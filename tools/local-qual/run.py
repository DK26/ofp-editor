#!/usr/bin/env python3
"""Local-model qualification spike runner (tools/local-qual).

What it does
------------
Sends the spike suites (suites/*.json) to one model and writes one JSONL
record per decision. It measures whether a model can carry the co-pilot's
code-owned step shapes (doc 21 §3.1): a Pick from a code-computed menu, a small
typed Fill, a grounded two-sentence explanation, a short flavour line, and the
doc 30 knowledge tasks with and without a reference card.

Three runtimes are supported (``--backend``): ``ollama`` (the default, native
/api/chat, as measured in doc 44) and ``llamacpp`` (llama.cpp's llama-server
through its OpenAI-compatible /v1/chat/completions, the runtime doc 13 plans
as the managed sidecar), both in backends.py, and ``openai`` (any
OpenAI-compatible endpoint, for example OpenRouter or a provider's own API),
in cloud_backend.py. With llama-server any GGUF file works, including one
pulled straight from Hugging Face (``llama-server -hf <user>/<repo>:<quant>``).
The ``openai`` backend spends money, so it refuses to start without a hard
budget (``--max-usd`` with ``--price-in``/``--price-out``, enforced by
budget.py) and reads its key only from the environment variable named by
``--api-key-env`` (cloud_run.py holds its flags and run-time guards).
``--free-only`` runs OpenRouter's ``:free`` models with a cap of 0, rate caps
and a zero-spend check on every response (free_mode.py; runbook in
cloud/README.md). ``--key-status`` runs nothing but one ``GET <base>/key``
and prints what the key allows (key_status.py).

How it fits
-----------
run.py only collects raw evidence: prompts.py decides what each call asks,
a backend sends it, and run.py writes the records. Its command line and the
refusals checked before anything is sent live in run_cli.py; turning a reply
into a record (parsing, the repair call, --resume) lives in run_records.py.
score.py turns the JSONL
into summary tables; knowledge, explain and text quality are graded later by
LLM graders from the grading sheet score.py exports; the free-form answers of
the open Pick arms are mapped to option keys by grade_open.py; uplift.py
compares arms. Nothing here is product code: it is a research tool, standard
library only, so it runs on any machine with Python 3.

Design notes
------------
* Pick menus are permuted per (item id, sample) with a seeded RNG, so the
  correct option lands on different letters across samples, and every
  condition and variant sees the same permutation (paired comparison). The
  escape option is always last as X (doc 21 §3.2).
* Structured steps pass the item's JSON schema to the server (Ollama's
  ``format``, ``response_format`` json_schema elsewhere), which constrains
  decoding with a grammar, exactly as a product harness would.
* Harness-uplift variants (``--variant``) remove one harness mechanism at a
  time, with every other byte of the prompt unchanged: ``open`` hides the Pick
  menu, ``labels`` shows only the option names, ``noschema`` drops the
  response schema (and, for Fill, the schema text), ``schematext`` keeps the
  schema text but not the response schema, ``bare`` drops Text's constraint
  list; ``--repair`` adds at most one repair call when a code check fails. The
  default (``plain``) requests are byte-identical to earlier versions.
* Thinking is switched off (these steps are meant to be answered directly):
  ``think: false`` for Ollama, ``chat_template_kwargs.enable_thinking=false``
  for llama-server, and an explicit ``--reasoning`` setting (for example
  ``none``) for the ``openai`` backend. A local server that rejects its field
  gets the call again without it and the record says so (``think_sent``);
  ``thinking_chars`` shows whether any thinking text came back anyway.
* Each call is independent (no chat history), as in the harness design of a
  fresh capsule per decision; a repair call is the only exception (it shows
  the model its own rejected answer).
* Every record names the backend, the runtime version, the model file and the
  quantisation the server reports, so runs of two quants or two runtimes can be
  told apart and paired item by item.
* ``--pick-mode logprob`` (Pick suites on llama-server) reads the probability
  of every menu letter from one forward pass instead of sampling one letter,
  optionally averaged over rotated option orders (``--permute``) and
  temperature-scaled (``--calibration``); see logprob_pick.py. Its records are
  variant ``logprob`` and carry the whole distribution; cascade.py replays them
  offline as the first stage of a small-to-large cascade.
* ``--scaffold <arm>`` (doc 59) adds harness reasoning computed by code from
  the item's answer-blind view (scaffolds.py): one-call arms (why, diff, rule;
  Fill quote-first) change only the request; the multi-call arms (eliminate,
  pairwise, subq, prefill) run in scaffold_run.py. Records get variant
  ``scaffold-<arm>`` and a per-call ledger under ``scaffold``; without the flag
  (or with ``--scaffold none``) every request is byte-identical to before.
* ``--suite-file`` runs a suite kept outside suites/ (the staged pools), and
  ``--split`` keeps one half of a suite whose items carry a split; the held-out
  half needs ``--confirm-heldout``.
* ``--preset FILE`` (D048, doc 55 section 3) applies a data-only harness preset
  (presets/): run_preset.py turns its knobs for the suite's step kind into the
  flags above, refuses what run.py cannot honour, and every record carries the
  preset's id, version and SHA-256. Without the flag nothing changes.
"""
import datetime as _dt
import json
import os
import sys
import time
import urllib.parse
import uuid

import cloud_run
import key_status
import logprob_pick
import run_cli
import run_preset
import scaffold_run
import scaffolds
# The local backend classes are looked up in this module's namespace when main() creates one, so a test harness can
# swap them (tests/dump_payloads.py and dump_bodies.py replace them with recording stand-ins).
from backends import LlamaServerBackend, OllamaBackend, SAMPLER_KEYS, normalize_host, quant_from_filename
# Re-exported: earlier scripts imported the prompt helpers (and strip_think) from run.py.
from prompts import (ESCAPE_LETTER, NUM_PREDICT, OPEN_VARIANTS, PICK_LETTERS, REPAIRABLE,  # noqa: F401
                     SCHEMA_MODE_VARIANT, SUITE_SHAPE, SUITES, SUITES_DIR, SYSTEM, SYSTEM_OPEN, TEMPERATURE,
                     VARIANTS, build_call, build_explain, build_fill, build_knowledge, build_pick, build_pick_open,
                     build_text, card_block, check_failure, compact, extract_json, load_sidecar, load_suite,
                     open_stem, permute_options, repair_message, sample_seed, strip_think)
# Re-exported too: these lived in run.py before the command line and the record helpers moved out.
from run_cli import load_suite_file, resolve_scaffold, resolve_variant, select_split  # noqa: F401
from run_records import FIRST_FIELDS, done_keys, interpret, merge_repair, slug  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(HERE, "results")


# ── Main ─────────────────────────────────────────────────────────────────────

def main(argv=None):
    ap = run_cli.build_parser()
    args = ap.parse_args(argv)
    if args.key_status:
        # Read-only: one GET <base>/key, the key record's non-secret fields printed, and the exit code (key_status.py).
        # Nothing below runs: no suite, no preset, no model request, no ledger, no lock.
        return key_status.run(ap, args)
    file_suite = None
    if args.suite_file is not None:
        file_suite = load_suite_file(ap, args)
        shape = file_suite[0]["shape"]
    elif args.suite is None:
        ap.error("--suite is required (or --suite-file)")
    else:
        shape = SUITE_SHAPE[args.suite]
    # --preset: its knobs for this step kind become the flags that send them, before any check below reads a flag; a
    # knob run.py cannot honour, or a flag that contradicts one, stops the run here (exit 2, nothing sent).
    preset = run_preset.apply(ap, args, shape, sys.argv[1:] if argv is None else argv) if args.preset else None
    cloud = args.backend == "openai"
    if args.free_only and not cloud:
        ap.error("--free-only applies to --backend openai (OpenRouter's :free models)")
    condition, base_variant, variant = resolve_variant(ap, args, shape)
    arm = resolve_scaffold(ap, args, shape, condition, base_variant)
    keep = (args.scaffold_keep or 3) if arm in scaffolds.LOGPROB_ARMS else None
    channel = (args.prefill_channel or "content") if arm == "prefill" else None
    if arm is not None:
        variant = "scaffold-" + arm + (f"-k{keep}" if keep not in (None, 3) else "") + (
            f"-{channel}" if channel not in (None, "content") else "")
    variant, logprob_settings = logprob_pick.resolve(ap, args, shape, variant)
    sidecar, sidecar_sha = load_sidecar() if base_variant in OPEN_VARIANTS else (None, None)

    if args.backend == "ollama" and not args.model:
        ap.error("--model is required with --backend ollama")
    if args.backend == "ollama":
        base_url = normalize_host(args.base_url or args.host)
        backend = OllamaBackend(base_url, args.timeout, args.think_mode, args.keep_alive)
    elif args.backend == "llamacpp":
        base_url = normalize_host(args.base_url or "http://127.0.0.1:8080", default_port="8080")
        api_key = args.api_key if args.api_key is not None else os.environ.get("LLAMA_API_KEY")
        backend = LlamaServerBackend(base_url, args.timeout, args.think_mode, api_key)
    else:
        backend, cloud_settings = cloud_run.make_backend(ap, args)
        base_url = backend.base
    sampler = {k: getattr(args, k) for k in SAMPLER_KEYS}

    suite, suite_sha = file_suite if file_suite is not None else load_suite(args.suite)
    # A suite file may name its shape ("shape": "pick" in pick-hard.json); it must agree with SUITE_SHAPE,
    # which score.py reads from the same field.
    if suite.get("shape", args.suite) != shape:
        ap.error(f"suites/{args.suite}.json declares shape {suite.get('shape')!r}; run.py expects {shape!r}")
    items = select_split(ap, args, suite["items"])
    if args.items:
        wanted = [s.strip() for s in args.items.split(",") if s.strip()]
        by_id = {it["id"]: it for it in items}
        missing = [w for w in wanted if w not in by_id]
        if missing:
            ap.error(f"unknown item ids: {', '.join(missing)}")
        items = [by_id[w] for w in wanted]
    if args.offset < 0 or (args.limit is not None and args.limit < 0):
        ap.error("--offset and --limit must not be negative")
    # Chunking: --offset N --limit M selects items[N:N+M], so a long suite can be
    # split across several short commands that append to the same --out file.
    items = items[args.offset:]
    if args.limit is not None:
        items = items[: args.limit]

    temperature = args.temperature if args.temperature is not None else TEMPERATURE[shape]
    cap_key = "pick_why" if args.why or arm == "why" else ("pick_open" if base_variant in OPEN_VARIANTS else shape)
    num_predict = args.num_predict if args.num_predict is not None else NUM_PREDICT[cap_key]
    if arm == "quote-first" and args.num_predict is None:
        num_predict = scaffolds.QUOTE_CAP
    elif arm == "prefill" and args.num_predict is None:
        num_predict = scaffolds.PREFILL_CAP
    system = SYSTEM_OPEN if base_variant in OPEN_VARIANTS else SYSTEM[shape]
    picker = runner = None
    if logprob_settings is not None:
        # The logprob mode generates exactly one token at temperature 0; the records say what was sent.
        temperature, num_predict = 0.0, 1
        picker = logprob_pick.LogprobPicker(backend, system, **logprob_settings)
    if arm in scaffolds.PROCEDURE_ARMS:
        # Several calls per decision (scaffold_run.py); each call's cap is its phase's unless --num-predict is set.
        runner = scaffold_run.ScaffoldRunner(backend, system, arm, temperature, args.num_ctx, sampler,
                                             num_predict=args.num_predict, keep=keep or 3, channel=channel or "content")
    # The endpoint named in a one-call scaffold arm's ledger entry.
    runner_endpoint = "/api/chat" if backend.name == "ollama" else "/v1/chat/completions"

    def make_payload(item, sample, model):
        """Build the backend's request body for one (item, sample); returns (payload, seed, extra record fields)."""
        user, schema, extra = build_call(shape, item, condition, sample, args.why, base_variant, sidecar)
        if arm in scaffolds.PROMPT_ARMS:
            # One-call scaffold arm: the request text and schema come from the answer-blind builders; `extra` keeps the
            # plain request's scoring fields (same seeded menu), plus the scaffold's text, hash and details.
            opts = permute_options(item, sample) if shape == "pick" else None
            user, schema, info = scaffolds.build_prompt_arm(arm, item, condition, opts)
            extra = dict(extra, scaffold=info)
        seed = sample_seed(item["id"], sample)
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        # The schema name is the shape, so a pick-hard request differs from a pick request only in its content.
        payload = backend.payload(model, messages, schema, temperature, seed, num_predict, args.num_ctx, sampler,
                                  schema_name=shape)
        return payload, seed, extra

    # A strict-schema arm on OpenRouter must be routed only to endpoints that honour response_format; refused
    # here, before the dry run too, so nothing is ever sent unconstrained by mistake.
    if cloud:
        schema_sent = bool(items) and "response_format" in make_payload(items[0], 0, args.model)[0]
        refusal = cloud_run.routing_refusal(urllib.parse.urlsplit(backend.base).hostname or "",
                                            cloud_settings["extra_body"], schema_sent)
        if refusal:
            ap.error(refusal)

    if args.dry_run and picker is not None:
        # The logprob mode's two requests of the first order; the rendered prompt needs the server, so it is shown
        # as a placeholder.
        if not items:
            ap.error("no items selected")
        for what, body in picker.dry_run(items[0], condition, 0, sample_seed(items[0]["id"], 0), args.model):
            print(what)
            print(json.dumps(body, ensure_ascii=False, indent=1))
        return 0
    if args.dry_run and runner is not None:
        # A procedure arm's first request(s); later phases depend on the replies and are only named.
        if not items:
            ap.error("no items selected")
        for what, body in runner.dry_run(items[0], condition, 0, sample_seed(items[0]["id"], 0), args.model):
            print(what)
            if body:
                print(json.dumps(body, ensure_ascii=False, indent=1))
        return 0
    if args.dry_run:
        # Print the first request without touching the network or the output file.
        if not items:
            ap.error("no items selected")
        payload, _, extra = make_payload(items[0], 0, args.model)
        print(json.dumps(payload, ensure_ascii=False, indent=1))
        if extra:
            print(json.dumps(extra, ensure_ascii=False, indent=1))
        if cloud:
            cloud_run.print_estimate(args, payload)
        return 0

    # ── Ask the server what it is running (once per run) ─────────────────────
    if args.backend == "llamacpp":
        ready, why_not = backend.wait_ready(args.wait)
        if not ready:
            print(f"llama-server at {base_url} is not ready after {args.wait:.0f} s ({why_not})", file=sys.stderr)
            return 3
    info = backend.probe(args.model)
    model = info.get("model")
    if not model:
        print("could not determine the model label; pass --model", file=sys.stderr)
        return 3
    quant = args.quant or info.get("quant") or quant_from_filename(model)
    # The context is a server setting on llama-server: record the effective value and flag a mismatch.
    num_ctx = (info.get("n_ctx") or args.num_ctx) if args.backend == "llamacpp" else args.num_ctx
    if args.backend == "llamacpp" and info.get("n_ctx") and info["n_ctx"] != args.num_ctx:
        print(f"note: server context is {info['n_ctx']} tokens, not --num-ctx {args.num_ctx} "
              f"(start llama-server with -c {args.num_ctx} to match)", file=sys.stderr)
    run_info = {"backend": backend.name, "runtime_version": info.get("runtime_version"),
                "model_file": info.get("model_file"), "quant": quant,
                "sampler_sent": {k: v for k, v in sampler.items() if v is not None}}
    if args.backend == "llamacpp":
        run_info.update({k: info.get(k) for k in ("thinking_kwarg_changes_prompt", "total_slots",
                                                  "server_sampler_defaults")})
    label = args.label or model
    if cloud:
        label, fields = cloud_run.run_info(args, backend, model, cloud_settings, sampler)
        run_info.update(fields)
    if preset is not None:
        # Every record carries the preset (id, version, hashes, binding check); the label gains +<id>@<version>.
        label = run_preset.finish(args, preset, label, info, backend.name, model, run_info)
    if sidecar is not None:
        run_info["open_sidecar_sha"] = sidecar_sha
    print(f"backend {backend.name} at {run_info.get('base_host') or base_url}: model {model}"
          + (f" (label {label})" if label != model else "")
          + f", file {run_info['model_file']}, quant {quant}, runtime {run_info['runtime_version']}, context {num_ctx}"
          + (f", template reads enable_thinking: {info.get('thinking_kwarg_changes_prompt')}"
             if args.backend == "llamacpp" else ""), flush=True)
    if picker is not None:
        cal = picker.calibration
        if cal is not None and cal["model"] is not None and cal["model"] != label:
            print(f"the calibration file was fitted on {cal['model']!r}, not {label!r}; refit it with cascade.py "
                  f"calibrate on this model's records", file=sys.stderr)
            return 2
        # One tiny completion first: a build that ignores n_probs stops here, not once per item.
        why_not = picker.preflight(model)
        if why_not:
            print(f"--pick-mode logprob: {why_not}", file=sys.stderr)
            return 3
        if items:
            # Does the answer prefix end where this model's tokenizer would split? Recorded in every record; a
            # letter read across a merged token is warned about, not refused (see logprob_pick.boundary_check).
            boundary = picker.boundary_check(items[0], condition, model)
            run_info["logprob_boundary"] = boundary
            if not boundary.get("checked"):
                print(f"note: --pick-mode logprob could not check the answer-prefix token boundary "
                      f"({boundary.get('reason')})", file=sys.stderr)
            elif boundary["noncanonical"] or not boundary["junction_ok"]:
                print(f"warning: --pick-mode logprob: the answer prefix is not a token boundary of this model for "
                      f"letter(s) {', '.join(boundary['noncanonical']) or '-'} (pieces "
                      f"{ {k: boundary['letter_pieces'].get(k) for k in boundary['noncanonical']} }; prefix joins "
                      f"the template cleanly: {boundary['junction_ok']}); those letters are read after a split the "
                      f"model never saw, so their probabilities are biased", file=sys.stderr)
    if args.suite_file is not None:
        run_info.update(suite_file=os.path.basename(args.suite_file), split=args.split)
    if runner is not None and items:
        # One check before the first record: a build without n_probs (eliminate, pairwise) or a template the prefill
        # channel cannot use stops here, not once per item.
        why_not = runner.preflight(items[0], condition, model)
        if why_not:
            print(f"--scaffold {arm}: {why_not}", file=sys.stderr)
            return 3
        boundary = runner.boundary_check(items[0], condition, model)
        if boundary is not None:
            run_info["logprob_boundary"] = boundary

    out = args.out or os.path.join(
        RESULTS_DIR, f"{slug(label)}__{args.suite}__{condition}{'' if variant == 'plain' else '__' + variant}.jsonl")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    if args.resume:
        # With or without --preset: a file whose records of this label came from other preset bytes (or from a preset,
        # when this run has none) would get two harnesses under one label, because --resume skips by label.
        run_preset.check_resume(ap, out, label, preset["record"]["sha256"] if preset is not None else None)
    skip = done_keys(out) if args.resume else set()
    run_id = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    if args.warmup and items:
        # The first request after a model load pays one-time costs: Ollama loads the weights, and
        # llama-server's GPU backend builds its compute pipelines on first use (12.9 s for a 239-token
        # prompt on a GTX 1070 under Vulkan the first time a build ran, 1.3-3.8 s on later starts,
        # against 0.8 s warm). Doc 44 excluded load time the same way, with one unrecorded call per model.
        t0 = time.perf_counter()
        if picker is not None:
            res = picker.decide(items[0], condition, 0, sample_seed(items[0]["id"], 0), model)[0]
        elif runner is not None:
            res = runner.decide(items[0], condition, 0, sample_seed(items[0]["id"], 0), model)
        else:
            res = backend.chat(make_payload(items[0], 0, model)[0])
        print(f"warm-up call: {(time.perf_counter() - t0) * 1000.0:.0f} ms"
              + (f" (error: {res['error']})" if res["error"] else ""), flush=True)

    redact = backend.redact if cloud else (lambda s: s)
    stop_fields = {"run_id": run_id, "model": label, "suite": args.suite, "condition": condition, "variant": variant}
    n_done = n_err = 0
    # Samples form the outer loop so an interrupted run still covers every item evenly.
    with open(out, "a", encoding="utf-8", newline="\n") as fout:

        def write_row(row):
            """Append one JSON line (with the key redacted, belt and braces) and flush it at once."""
            fout.write(redact(json.dumps(row, ensure_ascii=False)) + "\n")
            fout.flush()

        def call_once(payload):
            """One backend call (under the budget for openai); returns (result, latency ms, call id)."""
            call_id = uuid.uuid4().hex[:16] if cloud else None
            t0 = time.perf_counter()
            res = backend.chat(payload, budget=session.budget, call_id=call_id) if cloud else backend.chat(payload)
            return res, round((time.perf_counter() - t0) * 1000.0, 1), call_id

        session = None
        # One try/finally from the session's creation on: finish() releases the ledger lock on every exit path
        # (a stop, an exception, Ctrl+C), so only a killed process can leave a lock behind.
        try:
            if cloud:
                try:
                    session = cloud_run.Session(args, backend, out, write_row)
                except cloud_run.LedgerLocked as e:
                    print(f"stop (LedgerLocked): {e}", file=sys.stderr)
                    return cloud_run.EXIT_CONFIG
                except ValueError as e:
                    print(f"budget: {e}", file=sys.stderr)
                    return cloud_run.EXIT_CONFIG
                # One request body lets the free start checks compare every parameter sent with the endpoint's list.
                code = session.start(stop_fields, run_info,
                                     payload=make_payload(items[0], 0, model)[0] if items else None)
                if code is not None:
                    return code
            for sample in range(args.k):
                for item in items:
                    key = (label, args.suite, item["id"], condition, variant, sample)
                    if key in skip:
                        continue
                    if picker is not None:
                        # One logprob decision: an /apply-template and a /completion per option order.
                        payload, seed, call_id = None, sample_seed(item["id"], sample), None
                        res, extra = picker.decide(item, condition, sample, seed, model)
                        latency_ms = res["latency_ms"]
                    elif runner is not None:
                        # One procedure-arm decision (several calls). The record's scoring fields are the plain
                        # request's for this (item, sample), computed here from the full item, after the decision.
                        payload, seed, call_id = None, sample_seed(item["id"], sample), None
                        res = runner.decide(item, condition, sample, seed, model)
                        extra = build_call(shape, item, condition, sample, False, "plain", None)[2]
                        latency_ms = res["latency_ms"]
                    else:
                        payload, seed, extra = make_payload(item, sample, model)
                        res, latency_ms, call_id = call_once(payload)
                    if cloud and res.get("fatal") and not res["extra"].get("attempts"):
                        # Nothing was sent (the cap, the day's request allowance or a key poll refused the first
                        # attempt): no call record, only the stop, which names the next item for --resume.
                        reason = cloud_run.FATAL_STOP.get(res["fatal"], "ConfigFault")
                        session.write_stop(reason, **stop_fields, next_item=item["id"], next_sample=sample,
                                           detail=res["error"])
                        print(f"stop ({reason}): {res['error']}", file=sys.stderr)
                        return session.end_check(stop_fields, cloud_run.FATAL_EXIT.get(res["fatal"],
                                                                                        cloud_run.EXIT_CONFIG))

                    error, content = res["error"], res["content"]
                    # Field names and units follow Ollama's (durations in ns), so score.py reads every backend.
                    rec = {
                        "run_id": run_id, "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
                        "model": label, "suite": args.suite, "suite_sha": suite_sha, "item_id": item["id"],
                        "condition": condition, "variant": variant, "sample": sample, "seed": seed,
                        "temperature": temperature, "num_ctx": num_ctx, "num_predict": num_predict,
                        "think_sent": res["think_sent"], "error": error, "raw": content,
                        "thinking_chars": res["thinking_chars"],
                        "latency_ms": latency_ms,
                        "prompt_eval_count": res["prompt_eval_count"],
                        "eval_count": res["eval_count"],
                        "eval_duration": res["eval_duration"],
                        "prompt_eval_duration": res["prompt_eval_duration"],
                        "load_duration": res["load_duration"],
                        "total_duration": res["total_duration"],
                        "done_reason": res["done_reason"],
                    }
                    rec.update(run_info)
                    rec.update({k: v for k, v in res["extra"].items() if v is not None})
                    if call_id is not None:
                        rec["call_id"] = call_id
                    if picker is not None:
                        logprob_pick.interpret(rec, res, extra)
                    elif runner is not None:
                        scaffold_run.interpret(rec, res, extra)
                    else:
                        interpret(rec, content, error, extra, shape, base_variant, args.why or arm == "why")
                    if arm in scaffolds.PROMPT_ARMS:
                        # One-call arm: the ledger has the one call; quote-first also gets code's verbatim check,
                        # and the scored record loses its "_quote" fields (score.py validates the item's own schema).
                        rec["scaffold"] = dict(rec["scaffold"], n_calls=1, model_calls=1,
                                               truncated_calls=int(res["done_reason"] == "length"),
                                               calls=[dict(scaffold_run.call_entry("answer", runner_endpoint, res,
                                                                                   latency_ms), cap=num_predict)])
                        rec["n_calls"] = 1
                        if arm == "quote-first" and rec.get("parse_ok"):
                            record, detail = scaffolds.quote_first_post(rec["parsed"], scaffolds.blind_fill(item))
                            rec["parsed_with_quotes"], rec["parsed"] = rec["parsed"], record
                            rec["scaffold"]["quote_first"] = detail
                    fatal = res.get("fatal")
                    if cloud and "response_format" in payload and not error:
                        # Did the endpoint really enforce the schema? (the canary counts the answers that were not)
                        rec["schema_conformant"] = cloud_run.schema_conformant(payload, rec)

                    # ── Optional repair: one more call when a code check fails ──
                    if args.repair and not error and not fatal:
                        failure = check_failure(shape, item, suite, rec["parsed"], extra)
                        rec["repair_used"] = failure is not None
                        rec["first_check_failed"] = failure
                        if failure is not None:
                            rep = dict(payload)
                            rep["messages"] = list(payload["messages"]) + [
                                {"role": "assistant", "content": content},
                                {"role": "user", "content": repair_message(shape, failure)}]
                            res2, lat2, call_id2 = call_once(rep)
                            fatal = res2.get("fatal")
                            merge_repair(rec, res2, lat2, call_id, call_id2)
                            rec["repair_message"] = repair_message(shape, failure)
                            interpret(rec, res2["content"], res2["error"], extra, shape, base_variant, args.why)
                            error = res2["error"]
                    if cloud:
                        rec["spent_usd"] = round(session.budget.spent(), 12)

                    write_row(rec)
                    n_done += 1
                    n_err += 1 if error else 0
                    if shape == "pick" and base_variant in OPEN_VARIANTS:
                        status = f"ERROR {error}" if error else f"\"{(rec.get('open_answer') or '')[:60]}\" (ungraded)"
                    else:
                        status = f"ERROR {error}" if error else (
                            f"{rec.get('chosen_letter')} ({'correct' if rec.get('correct') else 'wrong, want ' + extra['correct_letter']})"
                            if shape == "pick" else ("parsed" if rec["parse_ok"] else "PARSE FAIL"))
                    if rec.get("repair_used"):
                        status += " [after repair]"
                    if picker is not None and rec.get("confidence") is not None:
                        status += f" p {rec['confidence']:.3f}"
                    elif picker is not None and not error:
                        status += " (no menu letter among the listed tokens)"
                    if runner is not None and not error:
                        status += (f" [{rec.get('n_calls')} calls, "
                                   f"{(rec.get('scaffold') or {}).get('decided_by', '-')}]")
                    cost_note = f", {rec.get('cost_usd', 0.0):.6f} USD (spent {rec['spent_usd']:.6f})" if cloud else ""
                    print(f"[{args.suite}/{condition}/{variant}] {item['id']} s{sample} -> {redact(status)} "
                          f"{rec['latency_ms']:.0f} ms, {rec['eval_count']} tok{cost_note}", flush=True)

                    # ── Stops (paid endpoints only): fatal results, then the canary window. In free mode each one
                    #    reads the key once more first (session.end_check): a rise turns any stop into exit 9 ──
                    if fatal:
                        reason = cloud_run.FATAL_STOP.get(fatal, fatal)
                        session.write_stop(reason, **stop_fields, detail=error or fatal)
                        print(f"stop ({reason}): {redact(error or fatal)}", file=sys.stderr)
                        return session.end_check(stop_fields, cloud_run.FATAL_EXIT.get(fatal, cloud_run.EXIT_CONFIG))
                    if cloud:
                        detail = session.canary(rec, payload, error)
                        if detail:
                            session.write_stop("CanaryAbort", **stop_fields, detail=detail)
                            print(f"stop (CanaryAbort): {detail}", file=sys.stderr)
                            return session.end_check(stop_fields, cloud_run.EXIT_CANARY)
            if session is not None:
                # Free mode: one more key read after the last call; a usage rise is a stop (exit 9).
                code = session.end_check(stop_fields)
                if code is not None:
                    return code
        finally:
            if session is not None:
                session.finish()

    print(f"done: {n_done} calls, {n_err} errors -> {out}"
          + (f"; spent {session.budget.spent():.6f} of {session.budget.cap_usd:.6f} USD" if session else ""))
    return 0 if n_err == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
