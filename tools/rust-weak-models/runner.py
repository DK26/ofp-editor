#!/usr/bin/env python3
"""PLAIN vs GUIDED Rust API experiment: harness entry point.

Subcommands
  scaffold   generate the per-(task, variant) test crates and the workspace members
  listing    write both API listings and the system prompts; report the budget
  verify     reference solutions must pass visible + hidden tests in both variants
  run        run episodes: live (OpenAI-compatible endpoint), --mock, or --dry-run
  mutants    compile trap mutants in both variants (model-free static catch rate)
  conformance  both references must export byte-identical text on every test input
  summary    aggregate a results JSONL file

Examples
  python runner.py scaffold
  python runner.py verify
  python runner.py run --dry-run --tasks all
  python runner.py run --mock fail-first --tasks pilot --samples 1
  python runner.py run --base-url http://127.0.0.1:8080/v1 --model qwen3.5-4b \\
      --tasks scored --samples 6 --rounds 3 --top-p 0.8 --top-k 20 --min-p 0

Standard library only. Never builds or runs the product repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from rwm import cargo, listing, prompt, scan, tasks
from rwm.llm import MockClient, OpenAIClient, Sampler
from rwm.tasks import ROOT, VARIANTS, trap_category

RESULTS = ROOT / "results"


# ── Helpers ───────────────────────────────────────────────────────────────────


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def toolchain() -> dict:
    def ver(cmd: list[str]) -> str:
        try:
            return subprocess.run(cmd, capture_output=True, text=True, check=False).stdout.strip()
        except OSError:
            return "unavailable"

    return {"rustc": ver(["rustc", "--version"]), "cargo": ver(["cargo", "--version"]), "python": sys.version.split()[0]}


def seed_for(task_id: str, sample: int, round_no: int, base: int) -> int:
    """Same seed for PLAIN and GUIDED: hash(task, sample, round)."""
    h = hashlib.sha256(f"{base}|{task_id}|{sample}|{round_no}".encode()).hexdigest()
    return int(h[:8], 16) & 0x7FFFFFFF


class Jsonl:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.fh = path.open("a", encoding="utf-8")

    def write(self, rec: dict) -> None:
        self.fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self.fh.flush()


# ── Evaluation of one candidate file ──────────────────────────────────────────

_TEST_NAMES: dict[tuple[str, str, str], list[str]] = {}


def evaluate(task: tasks.Task, variant: str, code: str | None, args) -> tuple[dict, str | None]:
    """Compiles and tests one candidate. Returns (metrics, feedback-for-the-model).

    Feedback is None when the candidate compiles and passes every visible test
    (the loop stops); hidden-test results are never part of the feedback."""
    m: dict = {
        "format_ok": code is not None, "bypass": None, "compile_ok": False, "diag_codes": [],
        "n_errors": 0, "n_warnings": 0, "build_ms": 0, "test_ms": 0,
        "visible": None, "hidden": None, "trap": None, "visible_pass": False, "hidden_pass": False,
        "hidden_frac": 0.0, "accepted_but_wrong": False, "solution_panics": 0, "failure_mode": None,
        "infra_error": None,
    }
    if code is None:
        m["failure_mode"] = "format"
        return m, prompt.NO_CODE_FEEDBACK
    reason = scan.static_scan(code)
    if reason:
        m["bypass"] = reason
        m["failure_mode"] = "bypass"
        return m, f"The file was rejected before compiling: it {reason}. Use only `mb`, `mb_spec` and `std`."
    tasks.install_solution(task, variant, code)
    crate_dir = task.crate_dir(variant)
    b = cargo.build(task.package(variant), timeout=args.build_timeout)
    m["build_ms"] = b.ms
    m["diag_codes"] = b.codes
    m["n_errors"] = sum(1 for d in b.diags if d.level == "error")
    m["n_warnings"] = sum(1 for d in b.diags if d.level == "warning")
    if not b.ok:
        m["failure_mode"] = "timeout" if b.timed_out else "compile"
        if not b.diags and not b.timed_out:
            m["infra_error"] = b.tail[-800:]
        return m, cargo.compile_feedback(b, crate_dir)
    m["compile_ok"] = True
    vis_exe, hid_exe = b.exes.get("visible"), b.exes.get("hidden")
    if not vis_exe or not hid_exe:
        m["infra_error"] = f"test executables missing: {sorted(b.exes)}"
        m["failure_mode"] = "infra"
        return m, None
    key = (task.id, variant, "hidden")
    if key not in _TEST_NAMES:
        _TEST_NAMES[key] = cargo.list_tests(hid_exe)
    hidden_names = _TEST_NAMES[key]
    vis = cargo.run_tests(vis_exe, timeout=args.test_timeout)
    hid = cargo.run_tests(hid_exe, timeout=args.test_timeout)
    m["test_ms"] = vis.ms + hid.ms
    for name in hidden_names:
        hid.results.setdefault(name, "not_run")
    m["visible"] = {"passed": len(vis.passed), "total": len(vis.results), "failed": vis.failed}
    m["hidden"] = {"passed": len(hid.passed), "total": len(hidden_names), "failed": [n for n in hid.failed]}
    traps = [n for n in hidden_names if n.startswith("trap_")]
    trap_failed = [n for n in traps if hid.results.get(n) != "ok"]
    m["trap"] = {
        "passed": len(traps) - len(trap_failed),
        "total": len(traps),
        "failed": trap_failed,
        "categories_failed": sorted({trap_category(n) for n in trap_failed}),
        "categories": sorted({trap_category(n) for n in traps}),
    }
    panics = [n for n in list(vis.failed) + list(hid.failed) if cargo.solution_panicked(vis.output.get(n, "") + hid.output.get(n, ""))]
    m["solution_panics"] = len(panics)
    m["visible_pass"] = vis.all_pass
    m["hidden_pass"] = hid.all_pass and len(hid.passed) == len(hidden_names)
    m["hidden_frac"] = round(len(hid.passed) / len(hidden_names), 4) if hidden_names else 0.0
    m["accepted_but_wrong"] = m["visible_pass"] and not m["hidden_pass"]
    if vis.timed_out or hid.timed_out:
        m["failure_mode"] = "timeout"
    elif not m["visible_pass"]:
        m["failure_mode"] = "panic" if panics else "visible"
    elif not m["hidden_pass"]:
        m["failure_mode"] = "panic" if panics else ("hidden_trap" if trap_failed else "hidden_nominal")
    else:
        m["failure_mode"] = "none"
    feedback = None if m["visible_pass"] else cargo.test_feedback(vis, crate_dir)
    return m, feedback


# ── Subcommands ───────────────────────────────────────────────────────────────


def scaffold_hint(missing: list[str]) -> str | None:
    """The message for a checkout whose generated files are missing (None when complete).

    The per-task test crates and Cargo.lock are generated and git-ignored, so every fresh
    clone starts here; the message names the one command that fixes it."""
    if not missing:
        return None
    return (f"{len(missing)} generated file(s) missing, for example {missing[0]}: run `python runner.py scaffold` "
            "first (it writes the per-task test crates and Cargo.lock, which are git-ignored)")


# Subcommands that compile task crates, so they need the scaffold output. `run --dry-run`
# is excluded: it compiles nothing and reports missing crates in its own summary.
NEEDS_SCAFFOLD = ("verify", "mutants", "conformance", "run")


def cmd_scaffold(args) -> int:
    all_tasks = tasks.discover()
    members = tasks.scaffold(all_tasks)
    print(f"scaffolded {len(all_tasks)} tasks, {len(members)} crates; Cargo.lock regenerated offline")
    return 0


def _system_prompts(args, client=None):
    counter = None
    if client is not None and getattr(args, "server_tokens", False):
        probe = client.tokenize_count("fn main() {}")
        if probe:
            counter = lambda text: client.tokenize_count(text) or listing.estimate_tokens(text)  # noqa: E731
    return prompt.build_system_prompts(args.budget, counter)


def cmd_listing(args) -> int:
    sp = _system_prompts(args)
    RESULTS.mkdir(exist_ok=True)
    for v in VARIANTS:
        (RESULTS / f"listing_{v}.rs").write_text(prompt.api_listing(v), encoding="utf-8")
        (RESULTS / f"system_{v}.md").write_text(sp.text[v], encoding="utf-8")
    report = {
        "budget": args.budget, "counter": sp.counter, "listing_tokens": sp.listing_tokens,
        "pad_tokens": sp.pad_tokens, "system_tokens": sp.tokens,
        "ratio_guided_to_plain": round(sp.tokens["guided"] / max(1, sp.tokens["plain"]), 4),
        "listing_cap": args.listing_cap,
        "system_sha256": {v: sp.sha256(v) for v in VARIANTS},
    }
    print(json.dumps(report, indent=2))
    over = [v for v in VARIANTS if sp.listing_tokens[v] > args.listing_cap]
    if over:
        print(f"FAIL: listing over the {args.listing_cap}-token cap: {over}")
        return 1
    return 0


def cmd_verify(args) -> int:
    selected = tasks.select(tasks.discover(), args.tasks)
    failures = 0
    rows = []
    for t in selected:
        for v in args.variants.split(","):
            m, _fb = evaluate(t, v, t.reference(v), args)
            ok = m["compile_ok"] and m["visible_pass"] and m["hidden_pass"]
            failures += 0 if ok else 1
            vis = m["visible"] or {}
            hid = m["hidden"] or {}
            rows.append((t.id, v, "PASS" if ok else "FAIL", f"{vis.get('passed', 0)}/{vis.get('total', 0)}",
                         f"{hid.get('passed', 0)}/{hid.get('total', 0)}",
                         f"{(m['trap'] or {}).get('passed', 0)}/{(m['trap'] or {}).get('total', 0)}", m["failure_mode"]))
            if not ok and args.verbose:
                print(json.dumps(m, indent=1))
            print(f"{t.id:4} {v:7} {rows[-1][2]}  visible {rows[-1][3]:>5}  hidden {rows[-1][4]:>5}  traps {rows[-1][5]:>5}", flush=True)
    print(f"\n{len(rows) - failures}/{len(rows)} reference runs pass")
    return 1 if failures else 0


def catch_level(m: dict) -> str:
    """Where a mistake surfaces: `static` (compile error), `loop` (a visible test fails,
    so the feedback loop sees it), `silent` (visible tests pass, hidden tests fail:
    accepted but wrong) or `missed` (every test passes: the mutant is not a mistake)."""
    if not m["compile_ok"]:
        return "static"
    if not m["visible_pass"]:
        return "loop"
    return "silent" if not m["hidden_pass"] else "missed"


def cmd_mutants(args) -> int:
    """Model-free mutation check (design.json tasks.mutation_check): every PLAIN mutant
    must compile and fail a hidden trap test; for each GUIDED mutant record whether the
    compiler rejects it (static catch) and with which diagnostic codes."""
    selected = tasks.select(tasks.discover(), args.tasks)
    out = []
    for t in selected:
        for v in VARIANTS:
            for mut in t.mutants(v):
                m, fb = evaluate(t, v, mut["code"], args)
                rec = {"kind": "mutant", "task": t.id, "variant": v, "mutant": mut["name"], "category": mut["category"],
                       "catch": catch_level(m), "compile_ok": m["compile_ok"], "diag_codes": m["diag_codes"],
                       "visible_pass": m["visible_pass"], "hidden_pass": m["hidden_pass"],
                       "trap_failed": (m["trap"] or {}).get("failed", []),
                       "custom_diagnostic": bool(fb) and "fix:" in fb}
                out.append(rec)
                print(f"{t.id} {v:6} {mut['name']:34} {mut['category']:12} {rec['catch']:7} codes={','.join(m['diag_codes']) or '-'}"
                      f"{' (custom text)' if rec['custom_diagnostic'] else ''}", flush=True)
            tasks.restore_reference(t, v)
    RESULTS.mkdir(exist_ok=True)
    path = RESULTS / "mutants.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in out), encoding="utf-8")
    for v in VARIANTS:
        rows = [r for r in out if r["variant"] == v]
        if rows:
            counts = {lvl: sum(1 for r in rows if r["catch"] == lvl) for lvl in ("static", "loop", "silent", "missed")}
            print(f"{v:6}: " + ", ".join(f"{k} {n}/{len(rows)}" for k, n in counts.items()))
    guided = [r for r in out if r["variant"] == "guided"]
    if guided:
        caught = sum(1 for r in guided if r["catch"] == "static")
        print(f"static catch rate (GUIDED mutants rejected at compile time): {caught}/{len(guided)}")
    bad = [r for r in out if r["variant"] == "plain" and (not r["compile_ok"] or r["hidden_pass"])]
    if bad:
        print(f"FAIL: PLAIN mutant(s) that do not compile-and-fail as required: {[(r['task'], r['mutant']) for r in bad]}")
        return 1
    print(f"records -> {path.relative_to(ROOT)}")
    return 0


def cmd_conformance(args) -> int:
    """Cross-variant byte-identity check (design.json fairness control): run both
    reference solutions' visible and hidden tests with RWM_DUMP_DIR set, then compare
    every export text (or refusal) test by test. Equivalent missions must export
    byte-identical text in both variants."""
    import shutil

    selected = tasks.select(tasks.discover(), args.tasks)
    base = RESULTS / "conformance"
    shutil.rmtree(base, ignore_errors=True)
    mismatches, compared = [], 0
    for t in selected:
        dumps = {}
        for v in VARIANTS:
            tasks.restore_reference(t, v)
            b = cargo.build(t.package(v), timeout=args.build_timeout)
            if not b.ok:
                print(f"{t.id} {v}: reference does not build")
                return 1
            d = base / t.id / v
            d.mkdir(parents=True, exist_ok=True)
            for target in ("visible", "hidden"):
                cargo.run_tests(b.exes[target], timeout=args.test_timeout, extra_env={"RWM_DUMP_DIR": str(d)})
            dumps[v] = {p.name: p.read_bytes() for p in d.glob("*.txt")}
        names = sorted(set(dumps["plain"]) | set(dumps["guided"]))
        for n in names:
            a, b2 = dumps["plain"].get(n), dumps["guided"].get(n)
            compared += 1
            if a != b2:
                mismatches.append(f"{t.id}/{n}")
        runs = sum(x.count(b"----\n") for x in dumps["plain"].values())
        print(f"{t.id}: {len(names)} tests, {runs} solve() calls compared", flush=True)
    print(f"\n{compared} test outputs compared across variants, {len(mismatches)} mismatch(es)")
    for m in mismatches:
        print(f"  MISMATCH {m} (see {base.relative_to(ROOT)})")
    return 1 if mismatches else 0


def _template_kwargs(args) -> dict | None:
    """`--thinking off` sends chat_template_kwargs {"enable_thinking": false} (doc 49 section
    1.4); templates without a thinking switch ignore it. `default` sends nothing."""
    return {"enable_thinking": False} if getattr(args, "thinking", "default") == "off" else None


def _episode_order(selected, variants, samples, seed) -> list[tuple]:
    order = [(t, v, s) for t in selected for v in variants for s in range(samples)]
    random.Random(seed).shuffle(order)
    return order


# Run-header fields that must be identical before `--resume` may append to a results
# file: same model label, task set, sampler, rounds, seed, context, budget rule and
# byte-identical system prompts. Anything else would mix two experiments in one file.
RESUME_KEYS = ("mode", "model", "tasks", "variants", "samples", "rounds", "seed", "sampler", "ctx", "budget",
               "system_sha256")


def resume_state(path: Path, header: dict) -> tuple[set, list, str | None]:
    """Reads an existing results file for `--resume`.

    Returns (finished episode keys (task, variant, sample), prior run ids, mismatch).
    Episodes that ended in an infrastructure error are not counted as finished (the
    design re-runs them). `mismatch` names the differing header fields; the caller
    must abort when it is set. Episode seeds depend only on (task, sample, round), so
    a resumed episode gets exactly the seeds it would have had in one uninterrupted run."""
    if not path.exists():
        return set(), [], None
    done: set = set()
    run_ids: list = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        try:
            rec = json.loads(ln)
        except json.JSONDecodeError:
            continue  # a torn last line from a killed run carries no finished episode
        if rec.get("kind") == "run":
            diff = [k for k in RESUME_KEYS if rec.get(k) != header.get(k)]
            if diff:
                return set(), [], f"run {rec.get('run_id')} differs in {diff}"
            run_ids.append(rec.get("run_id"))
        elif rec.get("kind") == "episode" and not rec.get("infra_error"):
            done.add((rec.get("task"), rec.get("variant"), rec.get("sample")))
    return done, run_ids, None


def cmd_run(args) -> int:
    selected = tasks.select(tasks.discover(), args.tasks)
    variants = args.variants.split(",")
    mode = "dry-run" if args.dry_run else ("mock" if args.mock else "live")
    client = None
    if mode == "live":
        if not args.base_url or not args.model:
            print("live mode needs --base-url and --model (or use --mock / --dry-run)")
            return 2
        try:
            client = OpenAIClient(args.base_url, args.model, timeout=args.request_timeout,
                                  allow_remote=args.allow_remote_endpoint)
        except ValueError as e:  # the endpoint guard names the fix (rwm.llm.check_endpoint)
            print(e)
            return 2
    elif mode == "mock":
        client = MockClient(args.mock)
    sp = _system_prompts(args, client if mode == "live" else None)
    count = listing.estimate_tokens
    order = _episode_order(selected, variants, args.samples, args.seed)
    ratio = sp.tokens["guided"] / max(1, sp.tokens["plain"])
    budget_ok = args.budget == "natural" or abs(ratio - 1.0) <= args.budget_tolerance
    header = {
        "kind": "run", "ts": now(), "mode": mode, "mock": args.mock, "model": args.model or f"mock:{args.mock}",
        "base_url": args.base_url, "tasks": [t.id for t in selected], "variants": variants,
        "samples": args.samples, "rounds": args.rounds, "seed": args.seed,
        "sampler": {"temperature": args.temperature, "top_p": args.top_p, "top_k": args.top_k,
                    "min_p": args.min_p, "max_tokens": args.max_tokens, "llama_extras": not args.no_llama_extras,
                    "thinking": args.thinking, "chat_template_kwargs": _template_kwargs(args),
                    "penalties": "neutral (repeat 1.0, presence 0, frequency 0) sent per request"},
        "ctx": args.ctx, "budget": args.budget, "token_counter": sp.counter,
        "system_tokens": sp.tokens, "listing_tokens": sp.listing_tokens, "pad_tokens": sp.pad_tokens,
        "system_sha256": {v: sp.sha256(v) for v in VARIANTS}, "budget_ok": budget_ok,
        "toolchain": toolchain(), "episodes_planned": len(order),
    }
    if not budget_ok:
        print(f"prompt budget unequal: guided/plain = {ratio:.3f} (tolerance {args.budget_tolerance}); aborting")
        return 3
    if mode == "dry-run":
        out = RESULTS / "dryrun"
        out.mkdir(parents=True, exist_ok=True)
        for v in variants:
            (out / f"system_{v}.md").write_text(sp.text[v], encoding="utf-8")
        per_task = []
        for t in selected:
            up = prompt.user_prompt(t)
            (out / f"user_{t.id}.md").write_text(up, encoding="utf-8")
            missing = [v for v in variants if not (t.crate_dir(v) / "Cargo.toml").exists()]
            per_task.append({"task": t.id, "user_tokens_est": count(up), "missing_crates": missing})
        header["per_task"] = per_task
        print(json.dumps(header, indent=2))
        print(f"dry run: prompts written to {out.relative_to(ROOT)}; no model calls, no cargo")
        return 1 if any(p["missing_crates"] for p in per_task) else 0

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = Path(args.out) if args.out else RESULTS / f"{mode}-{stamp}.jsonl"
    if getattr(args, "resume", False):
        done, prior, mismatch = resume_state(out_path, header)
        if mismatch:
            print(f"--resume refused: {out_path} {mismatch}; use a new --out file")
            return 4
        order = [(t, v, s) for (t, v, s) in order if (t.id, v, s) not in done]
        header["resumed_from"] = prior
        header["episodes_skipped"] = len(done)
        if out_path.exists() and not out_path.read_bytes().endswith(b"\n"):
            out_path.open("a", encoding="utf-8").write("\n")  # never glue a record onto a torn line
    log = Jsonl(out_path)
    run_id = hashlib.sha256(f"{stamp}|{header['model']}".encode()).hexdigest()[:12]
    header["run_id"] = run_id
    log.write(header)
    sampler = Sampler(args.temperature, args.top_p, args.top_k, args.min_p, args.max_tokens, not args.no_llama_extras,
                      template_kwargs=_template_kwargs(args))
    print(f"{mode} run {run_id}: {len(order)} episodes -> {out_path}")
    t_start = time.monotonic()
    for n, (t, v, s) in enumerate(order, 1):
        if isinstance(client, MockClient):
            mut = t.mutants(v)
            client.bind(t.reference(v), mut[0]["code"] if mut else None)
        try:
            ep = run_episode(t, v, s, client, sp, sampler, args, log, run_id)
        finally:
            tasks.restore_reference(t, v)
        print(f"[{n}/{len(order)}] {t.id} {v:6} s{s} rounds={ep['rounds_used']} "
              f"R0={int(ep['per_R']['R0']['hidden_pass'])} final={int(ep['final']['hidden_pass'])} "
              f"mode={ep['final']['failure_mode']}", flush=True)
    print(f"done in {time.monotonic() - t_start:.0f}s -> {out_path}")
    summarize(out_path)
    return 0


def run_episode(t, v, s, client, sp, sampler, args, log, run_id) -> dict:
    messages = [{"role": "system", "content": sp.text[v]}, {"role": "user", "content": prompt.user_prompt(t)}]
    rounds = []
    last_code = None
    per_r = {}
    tokens = {"prompt": 0, "cached": 0, "completion": 0}
    gen_ms = cargo_ms = 0
    for r in range(args.rounds + 1):
        seed = seed_for(t.id, s, r, args.seed)
        msgs = prompt.fit_context(messages, args.ctx, args.max_tokens, listing.estimate_tokens)
        ctx_est = sum(listing.estimate_tokens(x["content"]) + 4 for x in msgs)
        reply = client.chat(msgs, sampler, seed)
        if reply.error:
            # Infrastructure failure: retried by the design's re-run rule, never scored.
            rec = {"kind": "round", "run_id": run_id, "task": t.id, "variant": v, "sample": s, "round": r,
                   "seed": seed, "infra_error": reply.error}
            log.write(rec)
            break
        code = scan.extract_code(reply.content)
        m, feedback = evaluate(t, v, code, args)
        if code is not None:
            last_code = code
        gen_ms += reply.gen_ms
        cargo_ms += m["build_ms"] + m["test_ms"]
        for k, val in (("prompt", reply.prompt_tokens), ("cached", reply.cached_tokens), ("completion", reply.completion_tokens)):
            tokens[k] += val or 0
        rec = {
            "kind": "round", "run_id": run_id, "ts": now(), "model": args.model or f"mock:{args.mock}",
            "task": t.id, "tier": t.meta.get("tier"), "scored": t.scored, "variant": v, "sample": s,
            "round": r, "seed": seed,
            "gen": {"prompt_tokens": reply.prompt_tokens, "cached_tokens": reply.cached_tokens,
                    "completion_tokens": reply.completion_tokens, "gen_ms": reply.gen_ms,
                    "finish_reason": reply.finish_reason, "timings": reply.timings,
                    "reasoning_chars": reply.reasoning_chars},
            **m,
            "context_est_tokens": ctx_est,
            "context_overflow": ctx_est + args.max_tokens > args.ctx,
            "code_sha256": hashlib.sha256(code.encode()).hexdigest() if code else None,
            "code_chars": len(code) if code else 0,
            "feedback_chars": len(feedback) if feedback else 0,
        }
        log.write(rec)
        if getattr(args, "save_dir", None):
            # Pilot diagnostics only: raw reply, extracted code and fed-back text per round.
            d = Path(args.save_dir) / run_id
            d.mkdir(parents=True, exist_ok=True)
            stem = f"{t.id}_{v}_s{s}_R{r}"
            (d / f"{stem}.reply.md").write_text(reply.content or "", encoding="utf-8")
            if code is not None:
                (d / f"{stem}.rs").write_text(code, encoding="utf-8")
            if feedback:
                (d / f"{stem}.feedback.txt").write_text(feedback, encoding="utf-8")
        rounds.append(rec)
        per_r[f"R{r}"] = {k: m[k] for k in ("compile_ok", "visible_pass", "hidden_pass", "hidden_frac", "accepted_but_wrong", "failure_mode")}
        if feedback is None:
            break
        assistant = f"```rust\n{code}```" if code else reply.content[:4000]
        messages.append({"role": "assistant", "content": assistant})
        messages.append({"role": "user", "content": prompt.feedback_message(feedback)})
    # Carry the last round forward so every episode reports R0..R{max}.
    last = None
    for r in range(args.rounds + 1):
        key = f"R{r}"
        if key in per_r:
            last = per_r[key]
        elif last is not None:
            per_r[key] = dict(last, carried=True)
    final = rounds[-1] if rounds else {"hidden_pass": False, "failure_mode": "infra", "compile_ok": False}
    diag_fix = []
    for a, b in zip(rounds, rounds[1:]):
        before, after = set(a["diag_codes"]), set(b["diag_codes"])
        diag_fix.append({"round": a["round"], "codes": sorted(before), "fixed": sorted(before - after), "remaining": sorted(before & after)})
    ep = {
        "kind": "episode", "run_id": run_id, "ts": now(), "model": args.model or f"mock:{args.mock}",
        "task": t.id, "tier": t.meta.get("tier"), "scored": t.scored, "friction": t.meta.get("friction"),
        "traps": t.meta.get("traps"), "variant": v, "sample": s,
        "rounds_used": max(0, len(rounds) - 1), "stopped_early": bool(rounds) and rounds[-1]["visible_pass"],
        "per_R": per_r if per_r else {"R0": {"hidden_pass": False, "failure_mode": "infra"}},
        "final": {k: final.get(k) for k in ("compile_ok", "visible_pass", "hidden_pass", "hidden_frac", "accepted_but_wrong", "failure_mode", "trap")},
        "tokens": dict(tokens, total=tokens["prompt"] + tokens["completion"]),
        "wall_ms": {"generation": gen_ms, "cargo": cargo_ms},
        "escape_hatches": scan.escape_hatches(last_code) if last_code else None,
        "diag_fix": diag_fix,
        "infra_error": any(r.get("infra_error") for r in rounds) or not rounds,
    }
    if "R0" not in ep["per_R"]:
        ep["per_R"]["R0"] = {"hidden_pass": False, "failure_mode": "infra"}
    log.write(ep)
    return ep


def summarize(path: Path) -> None:
    eps = [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if '"kind": "episode"' in ln]
    if not eps:
        print("no episodes")
        return
    rounds_max = max(int(k[1:]) for e in eps for k in e["per_R"])
    print(f"\n{'model':28} {'variant':7} {'n':>4} {'R0 pass':>8} {'R<=' + str(rounds_max) + ' pass':>10} {'acc-wrong':>9} {'R0 compile':>10} {'trap pass':>9} {'rounds':>6} {'tok/ep':>7}")
    groups: dict = {}
    for e in eps:
        groups.setdefault((e["model"], e["variant"]), []).append(e)
    for (model, v), es in sorted(groups.items()):
        n = len(es)
        r0 = sum(e["per_R"]["R0"].get("hidden_pass", False) for e in es) / n
        rl = sum(e["per_R"].get(f"R{rounds_max}", e["per_R"]["R0"]).get("hidden_pass", False) for e in es) / n
        abw = sum(e["per_R"].get(f"R{rounds_max}", {}).get("accepted_but_wrong", False) for e in es) / n
        c0 = sum(e["per_R"]["R0"].get("compile_ok", False) for e in es) / n
        tp = [e["final"].get("trap") for e in es if e["final"].get("trap")]
        trap = sum(x["passed"] for x in tp) / max(1, sum(x["total"] for x in tp))
        rounds = sum(e["rounds_used"] for e in es) / n
        tok = sum(e["tokens"]["total"] for e in es) / n
        print(f"{model[:28]:28} {v:7} {n:4} {r0:8.2f} {rl:10.2f} {abw:9.2f} {c0:10.2f} {trap:9.2f} {rounds:6.2f} {tok:7.0f}")


def cmd_summary(args) -> int:
    summarize(Path(args.file))
    return 0


# ── CLI ───────────────────────────────────────────────────────────────────────


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp, budget=True):
        sp.add_argument("--tasks", default="all", help="all | pilot | scored | T01,T02,...")
        sp.add_argument("--variants", default="plain,guided")
        sp.add_argument("--build-timeout", type=float, default=300.0, help="seconds per cargo build")
        sp.add_argument("--test-timeout", type=float, default=20.0, help="seconds per test binary")
        if budget:
            sp.add_argument("--budget", choices=["equal", "natural"], default="equal",
                            help="equal: pad the shorter variant's appendix to the same prompt tokens")
            sp.add_argument("--budget-tolerance", type=float, default=0.02)
            sp.add_argument("--listing-cap", type=int, default=7000)
            sp.add_argument("--server-tokens", action="store_true", help="count tokens with the server's /tokenize")

    sub.add_parser("scaffold")
    sp = sub.add_parser("listing")
    common(sp)
    sp = sub.add_parser("verify")
    common(sp, budget=False)
    sp.add_argument("--verbose", action="store_true")
    sp = sub.add_parser("mutants")
    common(sp, budget=False)
    sp = sub.add_parser("conformance")
    common(sp, budget=False)
    sp = sub.add_parser("run")
    common(sp)
    sp.add_argument("--dry-run", action="store_true", help="build prompts only; no model calls, no cargo")
    sp.add_argument("--mock", choices=["ref", "fail-first", "no-code-first", "mutant"], help="replay reference solutions")
    sp.add_argument("--base-url", help="OpenAI-compatible endpoint on this machine, e.g. http://127.0.0.1:8080/v1")
    sp.add_argument("--allow-remote-endpoint", action="store_true",
                    help="allow a non-loopback https --base-url (no spend cap here; cloud runs belong in "
                         "tools/local-qual's guarded backend, D058)")
    sp.add_argument("--model", help="model name sent to the endpoint and recorded")
    sp.add_argument("--samples", type=int, default=1)
    sp.add_argument("--rounds", type=int, default=3, help="repair rounds after the first attempt")
    sp.add_argument("--seed", type=int, default=20260928)
    sp.add_argument("--temperature", type=float, default=0.6)
    sp.add_argument("--top-p", type=float)
    sp.add_argument("--top-k", type=int)
    sp.add_argument("--min-p", type=float)
    sp.add_argument("--max-tokens", type=int, default=3072)
    sp.add_argument("--ctx", type=int, default=24576,
                    help="server context size (llama-server -c); the design's 16384 is too small for this prompt plus repair rounds")
    sp.add_argument("--no-llama-extras", action="store_true", help="do not send top_k/min_p/cache_prompt")
    sp.add_argument("--thinking", choices=["off", "default"], default="off",
                    help="off: send chat_template_kwargs enable_thinking=false (design: thinking off)")
    sp.add_argument("--request-timeout", type=float, default=600.0)
    sp.add_argument("--out", help="results JSONL path (default results/<mode>-<time>.jsonl)")
    sp.add_argument("--save-dir", help="pilot only: save each round's reply, code and feedback under <dir>/<run_id>/")
    sp.add_argument("--resume", action="store_true",
                    help="append to --out, skipping finished episodes; refused unless the run config is identical")
    sp = sub.add_parser("summary")
    sp.add_argument("file")
    args = p.parse_args(argv)
    if args.cmd in NEEDS_SCAFFOLD and not getattr(args, "dry_run", False):
        hint = scaffold_hint(tasks.scaffold_missing(tasks.discover(quiet=True)))
        if hint:
            print(hint, file=sys.stderr)
            return 2
    handlers = {"scaffold": cmd_scaffold, "listing": cmd_listing, "verify": cmd_verify, "mutants": cmd_mutants,
                "run": cmd_run, "summary": cmd_summary, "conformance": cmd_conformance}
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
