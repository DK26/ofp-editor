"""Detached driver for the live pilot (k = 1, thinking off, pinned sampler, R0..R3 nested).

Runs the arms of an arms file one after another on the local GPU, one llama-server at a time:
  start server (start-server.ps1) -> pre-run check (check_server.py) -> runner.py run
  -> stop server (always, in `finally`) -> refresh the pilot summary (analysis/analyze_pilot.py).
Launch it with Start-Process so it outlives the session that started it; a runner that dies
with its session leaves an idle server behind.

Inputs (nothing machine-specific lives in this file):
  --arms FILE        the arms (default: live/arms.local.json if it exists, else live/arms.json)
  --models-dir DIR   folder that relative `gguf` paths in the arms file are joined to
                     (default: the RWM_MODELS_DIR environment variable)
  --llama-server EXE llama.cpp's server binary (default: RWM_LLAMA_SERVER, else `llama-server`
                     on PATH); the pilot used release b11146
  --out-dir DIR      results, logs and status files (default: results/pilot-live)
  --dry-run          check the weights (existence and size) and print each arm's runner
                     command; start nothing

Control: create a file named STOP in the output folder to end the pilot after the arm that is
running (the server is still stopped). Progress: drive-status.json and drive_pilot.log there.

Windows only as written (tasklist, taskkill and PowerShell start the server). On another OS,
start llama-server yourself and run the command `--dry-run` prints. Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent  # live/
ROOT = HERE.parent  # the harness folder (runner.py)
START = HERE / "start-server.ps1"
CHECK = HERE / "check_server.py"
ANALYZE = ROOT / "analysis" / "analyze_pilot.py"
DEFAULT_OUT = ROOT / "results" / "pilot-live"
DEFAULT_ARMS = HERE / "arms.json"
LOCAL_ARMS = HERE / "arms.local.json"  # git-ignored copy with this machine's locations

# Every arm must carry these (see arms.json for their meaning).
ARM_FIELDS = ("tag", "label", "gguf", "size", "sha256", "top_p", "top_k", "min_p", "resume")

state: dict = {"driver_pid": None, "started": None, "arms": [], "current": None, "done": False}
OUT = DEFAULT_OUT  # set by main() from --out-dir


# ── Arms file ─────────────────────────────────────────────────────────────────


def load_arms(path: Path, models_dir: Path | None) -> list[dict]:
    """Reads an arms file and resolves each arm's weights to `gguf_path`.

    A relative `gguf` is joined to `models_dir`; an absolute one (allowed only in a local,
    git-ignored arms.local.json) is used as is. Raises ValueError naming the missing field,
    or naming `--models-dir` and RWM_MODELS_DIR when a relative path has no folder to join."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    arms = []
    for i, arm in enumerate(data.get("arms", [])):
        missing = [f for f in ARM_FIELDS if f not in arm]
        if missing:
            raise ValueError(f"{path}: arm {i} ({arm.get('tag', '?')}) lacks {', '.join(missing)}")
        gguf = Path(arm["gguf"])
        if not gguf.is_absolute():
            if models_dir is None:
                raise ValueError(f"arm {arm['tag']}: '{arm['gguf']}' is relative; pass --models-dir or set RWM_MODELS_DIR "
                                 "to the folder that holds it")
            gguf = Path(models_dir) / gguf
        arms.append(dict(arm, gguf_path=gguf))
    return arms


def runner_cmd(arm: dict, port: int, ctx: int, out: Path) -> list[str]:
    """The runner invocation for one arm (the design's pilot settings; sampler from the arm)."""
    cmd = [sys.executable, str(ROOT / "runner.py"), "run", "--base-url", f"http://127.0.0.1:{port}/v1",
           "--model", arm["label"], "--tasks", "all", "--samples", "1", "--rounds", "3",
           "--temperature", "0.6", "--top-p", arm["top_p"], "--top-k", arm["top_k"], "--min-p", arm["min_p"],
           "--server-tokens", "--thinking", "off", "--ctx", str(ctx),
           "--out", str(out), "--save-dir", str(out.parent / "code")]
    if arm["resume"]:
        cmd.append("--resume")
    return cmd


# ── Process helpers (Windows) ─────────────────────────────────────────────────


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def log(msg: str) -> None:
    with (OUT / "drive_pilot.log").open("a", encoding="utf-8") as f:
        f.write(f"{now()} {msg}\n")


def save() -> None:
    (OUT / "drive-status.json").write_text(json.dumps(state, indent=1, default=str), encoding="utf-8")


def llama_pids() -> list[int]:
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq llama-server.exe", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    pids = []
    for ln in out.splitlines():
        parts = [p.strip('"') for p in ln.split('","')]
        if len(parts) > 1 and parts[0].lower().startswith("llama-server"):
            try:
                pids.append(int(parts[1]))
            except ValueError:
                pass
    return pids


def stop_pid(pid: int) -> bool:
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
    for _ in range(60):
        if pid not in llama_pids():
            return True
        time.sleep(0.5)
    return False


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def start_server(tag: str, gguf: Path, ctx: int, llama_server: str) -> dict:
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
           f"& '{START}' -Gguf '{gguf}' -Ctx {ctx} -Name 'rwm-{tag}' -LlamaServer '{llama_server}' "
           f"-LogDir '{OUT / 'logs'}' -ExtraArgs @('-np','1','--cache-ram','4096') | ConvertTo-Json -Compress"]
    # Output goes to a file, not a pipe: Start-Process inside the helper makes llama-server
    # inherit the helper's stdout handle, so a pipe would never reach EOF while the server
    # lives and communicate() would hang. With a file we only wait for the helper to exit.
    out_file = OUT / f"start-{tag}.out.txt"
    with out_file.open("w", encoding="utf-8") as fh:
        subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, timeout=600)
    text = out_file.read_text(encoding="utf-8", errors="replace")
    for ln in reversed(text.splitlines()):
        if ln.strip().startswith("{"):
            return json.loads(ln)
    return {"ready": False, "error": text[-1500:]}


def summarize(arms: list[dict]) -> None:
    files = []
    for a in arms:
        for name in (f"{a['tag']}.full.jsonl", f"{a['tag']}.jsonl"):  # a refused resume writes .full
            if (OUT / name).exists():
                files.append(str(OUT / name))
                break
    if not files:
        return
    p = subprocess.run([sys.executable, str(ANALYZE), str(OUT / "pilot-summary.json")] + files,
                       capture_output=True, text=True, cwd=ROOT)
    (OUT / "pilot-summary.txt").write_text(p.stdout + p.stderr, encoding="utf-8")


# ── One arm ───────────────────────────────────────────────────────────────────


def run_arm(arm: dict, ctx: int, llama_server: str) -> dict:
    rec = {"tag": arm["tag"], "label": arm["label"], "gguf": arm["gguf_path"].name, "state": "starting", "t0": now()}
    state["arms"].append(rec)
    state["current"] = arm["tag"]
    save()
    # ── Weights: size always; SHA-256 recorded, and checked against the pin ─────────
    gp = arm["gguf_path"]
    if not gp.exists() or gp.stat().st_size != arm["size"]:
        rec["state"] = f"skipped: weights missing or wrong size ({gp.stat().st_size if gp.exists() else 'missing'})"
        return rec
    rec["sha256"] = sha256(gp)
    if arm["sha256"] and rec["sha256"] != arm["sha256"]:
        rec["state"] = "skipped: SHA-256 mismatch against the pin"
        return rec
    rec["sha256_pinned_ok"] = bool(arm["sha256"])
    # ── One server at a time: refuse if any llama-server is running ────────────────
    others = llama_pids()
    if others:
        rec["state"] = f"blocked: llama-server already running {others}"
        return rec
    info = start_server(arm["tag"], gp, ctx, llama_server)
    rec["server"] = info
    save()
    if not info.get("ready"):
        rec["state"] = "server failed to start"
        if info.get("pid"):
            stop_pid(int(info["pid"]))
        return rec
    pid, port = int(info["pid"]), int(info["port"])
    try:
        # ── Pre-run check: template thinking switch, sampler defaults, one probe ─────
        chk = subprocess.run([sys.executable, str(CHECK), str(port), str(OUT / f"check-{arm['tag']}.json")],
                             capture_output=True, text=True, timeout=600, cwd=ROOT)
        rec["check_rc"] = chk.returncode
        rec["state"] = "running"
        save()
        out = OUT / f"{arm['tag']}.jsonl"
        cmd = runner_cmd(arm, port, ctx, out)
        rec["cmd"] = " ".join(cmd[1:])
        with (OUT / f"{arm['tag']}.log").open("a", encoding="utf-8") as lf:
            rc = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT, cwd=ROOT).returncode
        if rc == 4 and arm["resume"]:
            # Resume refused (config differs): run the arm in full into a fresh file instead.
            log(f"{arm['tag']}: resume refused, running the full arm into a new file")
            out2 = OUT / f"{arm['tag']}.full.jsonl"
            cmd2 = [c for c in cmd if c != "--resume"]
            cmd2[cmd2.index(str(out))] = str(out2)
            with (OUT / f"{arm['tag']}.log").open("a", encoding="utf-8") as lf:
                rc = subprocess.run(cmd2, stdout=lf, stderr=subprocess.STDOUT, cwd=ROOT).returncode
            rec["out_file"] = out2.name
        rec["runner_rc"] = rc
        rec["state"] = "finished" if rc == 0 else f"runner exit {rc}"
    finally:
        rec["server_stopped"] = stop_pid(pid)
        rec["t1"] = now()
        save()
    return rec


def main(argv: list[str] | None = None) -> int:
    global OUT
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--arms", type=Path, default=LOCAL_ARMS if LOCAL_ARMS.exists() else DEFAULT_ARMS)
    p.add_argument("--models-dir", type=Path, default=os.environ.get("RWM_MODELS_DIR") or None)
    p.add_argument("--llama-server", default=os.environ.get("RWM_LLAMA_SERVER") or "llama-server")
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)
    try:
        arms = load_arms(args.arms, args.models_dir)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    ctx = int(json.loads(args.arms.read_text(encoding="utf-8")).get("ctx", 24576))
    OUT = args.out_dir.resolve()
    if args.dry_run:
        for arm in arms:
            gp = arm["gguf_path"]
            size = gp.stat().st_size if gp.exists() else None
            status = "ok" if size == arm["size"] else ("missing" if size is None else f"size {size} != {arm['size']}")
            print(f"{arm['tag']}: weights {status}: {gp}")
            print("  " + " ".join(runner_cmd(arm, 8080, ctx, OUT / f"{arm['tag']}.jsonl")[1:]))
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    state["driver_pid"] = os.getpid()
    state["started"] = now()
    state["arms_file"] = args.arms.name
    save()
    log(f"driver start pid {os.getpid()}")
    for arm in arms:
        if (OUT / "STOP").exists():
            log("STOP file found; ending before " + arm["tag"])
            state["arms"].append({"tag": arm["tag"], "state": "not started (STOP)"})
            break
        try:
            rec = run_arm(arm, ctx, args.llama_server)
        except Exception as e:  # noqa: BLE001 - record and continue with the next arm
            rec = {"tag": arm["tag"], "state": f"driver error: {type(e).__name__}: {e}"}
            state["arms"].append(rec)
            # run_arm refuses to start while any llama-server runs, so one alive now is ours.
            rec["stopped_after_error"] = [pid for pid in llama_pids() if stop_pid(pid)]
        log(f"{arm['tag']}: {rec.get('state')}")
        save()
        summarize(arms)
    # ── Leave the GPU free: no llama-server may remain that this driver started ─────
    left = llama_pids()
    state["llama_left_running"] = left
    state["current"] = None
    state["done"] = True
    state["finished"] = now()
    save()
    summarize(arms)
    log(f"driver done; llama-server still running: {left}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
