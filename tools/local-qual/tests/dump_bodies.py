#!/usr/bin/env python3
"""Dump every request body, dry-run print and record run.py produces over a grid of command lines, without a model.

Usage: python dump_bodies.py <tool dir> <output dir> [--scaffold-none]

What it does
------------
It imports run.py from <tool dir>, swaps the two local backend classes for subclasses whose ``chat`` records the JSON
body and answers from a canned script (their probes answer without the network), and calls the real ``run.main()``
over a grid: every suite, both conditions, --why, every harness variant (open, labels, noschema, schematext, bare),
--repair with a first answer that fails its code check (so the repair body is captured too), sampler pins,
--think-mode omit, --temperature and --num-predict overrides, both backends, the llama-server bearer key from the
environment and from --api-key, --dry-run prints, and --pick-mode logprob (with and without --permute) against the
in-process mock llama-server (its /apply-template, /completion and /tokenize bodies are captured from the mock).

Output, in <output dir>:

* ``grid.json``: the command lines in run order (the mock's URL shown as ``<mock>``; ``#fail-first`` marks the runs
  whose first answer fails its check);
* ``bodies.jsonl`` and ``records.jsonl``: ``<run index><TAB><JSON>`` per captured body and per record written, with
  the volatile fields run_id, ts and latency_ms (and a logprob order's cache_n) removed from the records;
* ``dryrun.json``: the console text of each dry run.

--scaffold-none appends "--scaffold none" to every command line, which must give the same files as the tool without
the flag. Test a01 compares per-run digests of these files with ``golden/scaffold-regress.json``, frozen from the tool
as it was before the scaffold arms, so no default request, record or dry run moved.
"""
import contextlib
import io
import json
import os
import shutil
import sys

tool_dir, out_dir = sys.argv[1], sys.argv[2]
SCAFFOLD_NONE = "--scaffold-none" in sys.argv[3:]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, tool_dir)
sys.path.insert(1, HERE)
sys.dont_write_bytecode = True
import backends  # noqa: E402
import mock_reason  # noqa: E402
import run  # noqa: E402

CAPTURED = []  # (run index, JSON line)
CURRENT = {"run": 0}
SCRIPT = {"n": 0}


def canned(content):
    """A backend result as the local clients return it, with fixed token counts and timings."""
    return {"error": None, "think_sent": True, "content": content, "thinking_chars": 0, "prompt_eval_count": 1,
            "eval_count": 1, "eval_duration": 1, "prompt_eval_duration": 1, "load_duration": None,
            "total_duration": 2, "done_reason": "stop", "extra": {}}


def reply_for(body):
    """A canned answer by prompt shape: the first repair-able answer of each run fails its check, later ones pass."""
    SCRIPT["n"] += 1
    msgs = body.get("messages") or []
    user = next((m["content"] for m in reversed(msgs) if m.get("role") == "user"), "")
    fail_first = SCRIPT.get("fail_next", False)
    SCRIPT["fail_next"] = False
    if "Options:" in user:
        return '{"choice": "Z"}' if fail_first else '{"choice": "A"}'
    if "JSON schema" in user or "Answer with JSON only" in user:
        return "{}" if fail_first else '{"task": "other", "place": "", "side": "west", "size": "small", ' \
                                        '"time_of_day": "day"}'
    return "A plain answer."


class RecOllama(backends.OllamaBackend):
    """The Ollama client with the network replaced by the canned script above."""

    def probe(self, model):
        return {"runtime_version": "test", "model_file": None, "quant": "Q4_K_M", "model": model}

    def chat(self, body):
        CAPTURED.append((CURRENT["run"], json.dumps({"backend": "ollama", "body": body}, ensure_ascii=False)))
        return canned(reply_for(body))


class RecLlama(backends.LlamaServerBackend):
    """The llama-server client with the network replaced; the Authorization header is captured with the body."""

    def wait_ready(self, max_wait_s=180.0):
        return True, None

    def probe(self, model):
        return {"runtime_version": "test", "model_file": "m.gguf", "quant": "Q4_K_M", "model": model or "m",
                "n_ctx": 8192, "total_slots": 1, "server_sampler_defaults": {},
                "thinking_kwarg_changes_prompt": True}

    def chat(self, body):
        CAPTURED.append((CURRENT["run"], json.dumps({"backend": "llamacpp", "auth": self.http.headers.get("Authorization"),
                                                     "body": body}, ensure_ascii=False)))
        return canned(reply_for(body))


run.OllamaBackend = RecOllama
run.LlamaServerBackend = RecLlama
server, URL = mock_reason.start()

# ── The grid (unchanged from the check that first froze these requests) ──────
grid = []
for suite in ("pick", "pick-hard", "fill", "explain", "text", "knowledge"):
    for condition in ("none", "cards"):
        whys = (False, True) if suite in ("pick", "pick-hard") else (False,)
        for why in whys:
            base = ["--suite", suite, "--condition", condition, "--k", "2"] + (["--why"] if why else [])
            grid.append(["--backend", "ollama", "--model", "qwen3.5:4b-q4_K_M"] + base)
            grid.append(["--backend", "llamacpp", "--base-url", "http://127.0.0.1:8080"] + base)
# Harness-uplift variants, on both backends.
for be in (["--backend", "ollama", "--model", "m"], ["--backend", "llamacpp", "--base-url", "http://127.0.0.1:8080"]):
    for suite, variant in (("pick", "open"), ("pick-hard", "labels"), ("pick", "noschema"), ("fill", "noschema"),
                           ("fill", "schematext"), ("text", "bare")):
        grid.append(be + ["--suite", suite, "--variant", variant, "--k", "1", "--limit", "4"])
    grid.append(be + ["--suite", "pick", "--condition", "open", "--k", "1", "--limit", "3"])
    grid.append(be + ["--suite", "pick", "--schema-mode", "none", "--k", "1", "--limit", "3"])
    grid.append(be + ["--suite", "fill", "--schema-mode", "text", "--k", "1", "--limit", "3"])
    # Repair: the first call of each of these runs fails its check (see reply_for), so the repair body goes out.
    for suite, extra in (("pick", []), ("pick", ["--variant", "noschema"]), ("fill", []),
                         ("fill", ["--variant", "schematext"])):
        grid.append(be + ["--suite", suite, "--repair", "--k", "1", "--limit", "2", "#fail-first"] + extra)
# Overrides and pins on a few suites.
for suite in ("pick", "fill", "text"):
    extra = ["--suite", suite, "--k", "2", "--top-k", "20", "--top-p", "0.95", "--min-p", "0.0",
             "--presence-penalty", "1.5", "--repeat-penalty", "1.1", "--temperature", "0.3", "--num-predict", "99"]
    grid.append(["--backend", "ollama", "--model", "hf.co/u/r:Q4", "--think-mode", "omit", "--num-ctx", "4096"]
                + extra)
    grid.append(["--backend", "llamacpp", "--model", "router-name", "--think-mode", "omit"] + extra)
# Logprob mode against the mock server (its /apply-template and /completion bodies are captured there).
for extra in ([], ["--permute", "3"], ["--condition", "cards", "--n-probs", "40"]):
    grid.append(["--backend", "llamacpp", "--base-url", URL, "--suite", "pick-hard", "--pick-mode", "logprob",
                 "--k", "1", "--limit", "3"] + extra)
DRY = [["--backend", "ollama", "--model", "m", "--suite", "pick-hard", "--condition", "cards", "--dry-run"],
       ["--backend", "llamacpp", "--suite", "fill", "--dry-run"],
       ["--backend", "llamacpp", "--base-url", URL, "--suite", "pick", "--pick-mode", "logprob", "--dry-run"]]

# llama-server bearer key: from the environment (default) and from --api-key. Both are dummies.
os.environ["LLAMA_API_KEY"] = "env-key-123"
grid.append(["--backend", "llamacpp", "--suite", "pick", "--k", "1", "--limit", "2"])
grid.append(["--backend", "llamacpp", "--suite", "pick", "--k", "1", "--limit", "2", "--api-key", "argv-key-456"])

shutil.rmtree(out_dir, ignore_errors=True)
os.makedirs(os.path.join(out_dir, "runs"))
records, dry_out = [], []
for n, argv in enumerate(grid):
    CURRENT["run"] = n
    fail_first = "#fail-first" in argv
    argv = [a for a in argv if a != "#fail-first"] + (["--scaffold", "none"] if SCAFFOLD_NONE else [])
    out = os.path.join(out_dir, "runs", f"run{n}.jsonl")
    mock_reason.STATE.reset()
    mock_reason.STATE.dist_fn = lambda menu, prompt: [("B", 0.5), (" C", 0.3), ("X", 0.2)]
    sink = io.StringIO()
    SCRIPT["fail_next"] = fail_first
    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        code = run.main(argv + ["--out", out])
    if code != 0:
        raise SystemExit(f"run.main exited {code} for {argv}: {sink.getvalue()[-800:]}")
    for r in mock_reason.STATE.requests:
        if r["path"] in ("/apply-template", "/completion", "/tokenize"):
            CAPTURED.append((n, json.dumps({"backend": "mock", "path": r["path"], "body": r["body"]},
                                           ensure_ascii=False)))
    with open(out, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            # Wall-clock fields differ on every run; everything else is a function of the command line.
            for volatile in ("run_id", "ts", "latency_ms"):
                rec.pop(volatile, None)
            if isinstance(rec.get("first"), dict):
                rec["first"].pop("latency_ms", None)  # a repaired record keeps its first call's wall time
            if isinstance(rec.get("logprob"), dict):
                for o in rec["logprob"].get("orders", []):
                    o.pop("cache_n", None)
            records.append((n, json.dumps(rec, ensure_ascii=False, sort_keys=True)))
for argv in DRY:
    argv = argv + (["--scaffold", "none"] if SCAFFOLD_NONE else [])
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        code = run.main(argv)
    dry_out.append(f"== {' '.join(a for a in argv if a != URL and a != '--scaffold' and a != 'none')} -> {code}\n"
                   + sink.getvalue().replace(URL, "<mock>"))


def shown(argv):
    """A command line as the goldens record it: the mock's per-run port hidden."""
    return [("<mock>" if a == URL else a) for a in argv]


with open(os.path.join(out_dir, "grid.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump([shown(a) for a in grid], f)
for name, lines in (("bodies.jsonl", CAPTURED), ("records.jsonl", records)):
    with open(os.path.join(out_dir, name), "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(f"{n}\t{line.replace(URL, '<mock>')}\n" for n, line in lines))
with open(os.path.join(out_dir, "dryrun.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(dry_out, f, ensure_ascii=False)
server.shutdown()
server.server_close()
print(f"{len(grid)} command lines, {len(CAPTURED)} request bodies, {len(records)} records, {len(DRY)} dry runs "
      f"-> {out_dir}")
