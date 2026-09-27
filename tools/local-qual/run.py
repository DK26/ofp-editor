#!/usr/bin/env python3
"""Local-model qualification spike runner (tools/local-qual).

What it does
------------
Sends the spike suites (suites/*.json) to one model served by a local runtime
and writes one JSONL record per call. It measures whether a small local model
can carry the co-pilot's code-owned step shapes (doc 21 §3.1): a Pick from a
code-computed menu, a small typed Fill, a grounded two-sentence explanation, a
short flavour line, and the doc 30 knowledge tasks with and without a
reference card.

Two runtimes are supported (``--backend``, clients in backends.py):
``ollama`` (the default, native /api/chat, as measured in doc 44) and
``llamacpp`` (llama.cpp's llama-server through its OpenAI-compatible
/v1/chat/completions, the runtime doc 13 plans as the managed sidecar). With
llama-server any GGUF file works, including one pulled straight from Hugging
Face (``llama-server -hf <user>/<repo>:<quant>``).

How it fits
-----------
run.py only collects raw evidence. score.py turns the JSONL into summary
tables; knowledge, explain and text quality are graded later by LLM graders
from the grading sheet score.py exports. Nothing here is product code: it is a
research tool, standard library only, so it runs on any machine with Python 3
and one of the two servers.

Design notes
------------
* Pick menus are permuted per (item id, sample) with a seeded RNG, so the
  correct option lands on different letters across samples, and the "none" and
  "cards" conditions see the same permutation (paired comparison). The escape
  option is always last as X (doc 21 §3.2).
* Structured steps pass the item's JSON schema to the server (Ollama's
  ``format``, llama-server's ``response_format`` json_schema), which constrains
  decoding with a grammar, exactly as a product harness would.
* Thinking is switched off (these steps are meant to be answered directly):
  ``think: false`` for Ollama, ``chat_template_kwargs.enable_thinking=false``
  for llama-server. If the server rejects the field, the call is retried once
  without it and the record says so (``think_sent``); ``thinking_chars`` shows
  whether any thinking text came back anyway.
* Each call is independent (no chat history), as in the harness design of a
  fresh capsule per decision.
* Every record names the backend, the runtime version, the model file and the
  quantisation the server reports, so runs of two quants or two runtimes can be
  told apart and paired item by item.
"""
import argparse
import datetime as _dt
import hashlib
import json
import os
import random
import re
import sys
import time

from backends import LlamaServerBackend, OllamaBackend, SAMPLER_KEYS, normalize_host, quant_from_filename

HERE = os.path.dirname(os.path.abspath(__file__))
SUITES_DIR = os.path.join(HERE, "suites")
RESULTS_DIR = os.path.join(HERE, "results")
# Suite name -> step shape. The shape picks the prompt builder, the schema, the temperature, the output cap
# and the system prompt, so several suites can share one shape: `pick-hard` (doc 44 §5.4 item 4) is a harder
# instrument for the same Pick step. Records and output files keep the suite's own name, so the two Pick
# suites score separately.
SUITE_SHAPE = {"knowledge": "knowledge", "pick": "pick", "pick-hard": "pick", "fill": "fill", "explain": "explain",
               "text": "text"}
SUITES = tuple(SUITE_SHAPE)

# Temperatures from the spike plan: sampled steps (pick/fill/text) run warmer
# because the harness draws K candidates and votes or validates; knowledge and
# explanations run cooler because they should be stable facts.
TEMPERATURE = {"pick": 0.6, "fill": 0.6, "text": 0.6, "knowledge": 0.2, "explain": 0.2}
# Output caps (tokens). Generous enough for each shape; a cap stops a small
# model that loops from burning minutes of GPU time. Override with --num-predict.
NUM_PREDICT = {"pick": 64, "pick_why": 200, "fill": 320, "text": 120, "knowledge": 700, "explain": 320}
PICK_LETTERS = "ABCDEFG"  # at most 7 real options per menu (doc 21 §3.2)
ESCAPE_LETTER = "X"

SYSTEM = {
    "knowledge": "Answer briefly; if unsure, say so.",
    "pick": ("You are the decision step of a mission editor for Arma: Cold War Assault (Operation Flashpoint). "
             "Code has already computed a menu of valid options. Choose the single best option for the request. "
             "If no option fits, choose X. Answer with JSON only."),
    "fill": ("You fill one small typed record for a mission editor for Arma: Cold War Assault. Use only what the "
             "request says; never invent. Answer with JSON only."),
    "explain": ("You explain one editor finding to a mission maker for Arma: Cold War Assault. Use only the finding, "
                "the mission facts and the reference card if one is given. Do not invent commands or behaviour. "
                "Answer with JSON only."),
    "text": ("You write one short line of in-world text for a Cold War military mission set in 1985. Follow every "
             "constraint exactly. Answer with JSON only."),
}


# ── Suite loading and seeding ────────────────────────────────────────────────

def load_suite(name):
    """Load suites/<name>.json and return (suite dict, sha256 of the file)."""
    path = os.path.join(SUITES_DIR, name + ".json")
    with open(path, "rb") as f:
        raw = f.read()
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()[:16]


def sample_seed(item_id, sample):
    """Stable 31-bit seed per (item, sample); identical across conditions so runs pair up."""
    digest = hashlib.sha256(f"{item_id}|{sample}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) & 0x7FFFFFFF


def permute_options(item, sample):
    """Return the item's real options in a seeded order (escape excluded).

    random.Random seeded with a str hashes it with SHA-512 (seed version 2), so
    the order is reproducible across machines and Python 3 versions.
    """
    opts = list(item["options"])
    random.Random(f"perm|{item['id']}|{sample}").shuffle(opts)
    return opts


# ── Prompt builders (one per suite) ──────────────────────────────────────────

def compact(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def card_block(item, condition):
    card = item.get("card")
    if condition == "cards" and card:
        return "\n\n[REFERENCE CARD]\n" + card
    return ""


def build_pick(item, condition, sample, why):
    opts = permute_options(item, sample)
    letters = PICK_LETTERS[: len(opts)]
    letter_to_key = {letter: opt["key"] for letter, opt in zip(letters, opts)}
    letter_to_key[ESCAPE_LETTER] = item["escape"]["key"]
    menu = "\n".join(f"{letter}) {opt['label']}: {opt['desc']}" for letter, opt in zip(letters, opts))
    menu += f"\n{ESCAPE_LETTER}) {item['escape']['label']}"
    enum = list(letters) + [ESCAPE_LETTER]
    if why:
        # Doc 21 §3.2: a short bounded reason comes before the answer.
        schema = {"type": "object",
                  "properties": {"why": {"type": "string", "maxLength": 160},
                                 "choice": {"type": "string", "enum": enum}},
                  "required": ["why", "choice"]}
        reply = 'Reply as {"why": "<one short reason>", "choice": "<letter>"}.'
    else:
        schema = {"type": "object", "properties": {"choice": {"type": "string", "enum": enum}},
                  "required": ["choice"]}
        reply = 'Reply as {"choice": "<letter>"}.'
    user = f"Request: {item['request']}{card_block(item, condition)}\n\nOptions:\n{menu}\n\n{reply}"
    answer = item["answer"]
    if answer == item["escape"]["key"]:
        correct_letter, correct_pos = ESCAPE_LETTER, len(opts)
    else:
        correct_pos = [o["key"] for o in opts].index(answer)
        correct_letter = letters[correct_pos]
    extra = {"letter_to_key": letter_to_key, "options_order": [o["key"] for o in opts],
             "n_options": len(opts), "correct_key": answer, "correct_letter": correct_letter,
             "correct_pos": correct_pos}
    return user, schema, extra


def build_fill(item, condition):
    user = (f"Request: \"{item['request']}\"{card_block(item, condition)}\n\n{item['instructions']}\n\n"
            f"JSON schema:\n{compact(item['schema'])}")
    return user, item["schema"], {}


def build_explain(item, condition):
    user = (f"Finding {item['code']} ({item['severity']}): {item['message']}\n"
            f"Mission facts: {item['context']}{card_block(item, condition)}\n\n"
            "Explain what is wrong and why in one sentence (explanation), and the fix in one sentence (fix). "
            "At most two sentences in total.\n\n"
            f"JSON schema:\n{compact(item['schema'])}")
    return user, item["schema"], {}


def build_text(item, condition):
    c = item["constraints"]
    lines = [f"- at most {c['max_words']} words"]
    if c.get("names_check", True):
        names = ", ".join(c["allowed_names"]) if c["allowed_names"] else "none"
        lines.append(f"- names, callsigns and places you may use: {names}; use no other names")
    if c.get("no_digits"):
        lines.append("- no digits")
    lines.append(f"- era: {c['era']}")
    lines.append(f"- tone: {c['tone']}")
    user = (f"Slot: {item['slot']}\nContext: {item['context']}{card_block(item, condition)}\n\nConstraints:\n"
            + "\n".join(lines) + f"\n\nJSON schema:\n{compact(item['schema'])}")
    return user, item["schema"], {}


def build_knowledge(item, condition):
    return item["prompt"] + card_block(item, condition), None, {}


def build_call(suite, item, condition, sample, why):
    if suite == "pick":
        return build_pick(item, condition, sample, why)
    if suite == "fill":
        return build_fill(item, condition)
    if suite == "explain":
        return build_explain(item, condition)
    if suite == "text":
        return build_text(item, condition)
    return build_knowledge(item, condition)


# ── Response parsing ─────────────────────────────────────────────────────────

def extract_json(text):
    """Parse a JSON object from model text.

    Returns (obj or None, mode). Grammar-constrained output is normally plain
    JSON ("strict"); the fallback finds the first balanced {...} span, for
    runtimes or models that wrap output in a code fence ("extracted").
    """
    s = (text or "").strip()
    try:
        obj = json.loads(s)
        return (obj, "strict") if isinstance(obj, dict) else (None, "not_object")
    except (ValueError, TypeError):
        pass
    start = s.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for pos, ch in enumerate(s[start:], start):
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            elif ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(s[start:pos + 1])
                        if isinstance(obj, dict):
                            return obj, "extracted"
                    except ValueError:
                        pass
                    break
        start = s.find("{", start + 1)
    return None, "failed"


# ── Main loop ────────────────────────────────────────────────────────────────

def slug(text):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-")


def done_keys(path):
    """Keys of successful records already in `path` (for --resume)."""
    keys = set()
    if not os.path.exists(path):
        return keys
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if not r.get("error"):
                keys.add((r["model"], r["suite"], r["item_id"], r["condition"], r["variant"], r["sample"]))
    return keys


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run a local-qual suite against a local model (Ollama or llama-server).")
    ap.add_argument("--backend", default="ollama", choices=("ollama", "llamacpp"),
                    help="'ollama' (default): native /api/chat; 'llamacpp': llama-server's /v1/chat/completions")
    ap.add_argument("--model", default=None,
                    help="ollama: the model name (required), e.g. qwen3.5:4b-q4_K_M or hf.co/<user>/<repo>:<quant>; "
                         "llamacpp: a label for records and file names (default: the served GGUF's file name "
                         "without .gguf), also sent as the request's model for router mode")
    ap.add_argument("--suite", required=True, choices=SUITES)
    ap.add_argument("--condition", default="none", choices=("none", "cards"),
                    help="'cards' appends the item's reference card when it has one")
    ap.add_argument("--k", type=int, default=3, help="samples per item (default 3)")
    ap.add_argument("--offset", type=int, default=0,
                    help="skip the first N items (after --items, before --limit); with --limit, runs a chunk")
    ap.add_argument("--limit", type=int, default=None, help="only the first N items (after --items and --offset)")
    ap.add_argument("--items", default=None, help="comma-separated item ids to run")
    ap.add_argument("--out", default=None, help="JSONL output (default results/<model>__<suite>__<condition>[__why].jsonl)")
    ap.add_argument("--base-url", default=None,
                    help="server URL (default: --host for ollama, http://127.0.0.1:8080 for llamacpp)")
    ap.add_argument("--host", default=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
                    help="ollama only, kept for older command lines: the Ollama server (default OLLAMA_HOST)")
    ap.add_argument("--api-key", default=os.environ.get("LLAMA_API_KEY"),
                    help="llamacpp only: bearer key if llama-server runs with --api-key (default LLAMA_API_KEY)")
    ap.add_argument("--quant", default=None,
                    help="quantisation label for the records when the server cannot report it")
    ap.add_argument("--why", action="store_true", help="pick only: ask for a short 'why' before the choice")
    ap.add_argument("--temperature", type=float, default=None, help="override the per-suite temperature")
    # Sampler pins. Unset means the server's or the build's default; set them to compare two runtimes
    # or two builds with the same sampler (doc 44 §1.6).
    ap.add_argument("--top-k", type=int, default=None)
    ap.add_argument("--top-p", type=float, default=None)
    ap.add_argument("--min-p", type=float, default=None)
    ap.add_argument("--presence-penalty", type=float, default=None)
    ap.add_argument("--repeat-penalty", type=float, default=None)
    ap.add_argument("--num-ctx", type=int, default=8192,
                    help="ollama: context per request; llamacpp: fixed by the server's -c, only checked")
    ap.add_argument("--num-predict", type=int, default=None, help="override the per-suite output token cap")
    ap.add_argument("--keep-alive", default="10m", help="ollama only")
    ap.add_argument("--think-mode", default="false", choices=("false", "omit"),
                    help="'false' (default) switches thinking off (ollama think=false; llamacpp "
                         "chat_template_kwargs.enable_thinking=false); 'omit' leaves the field out")
    ap.add_argument("--timeout", type=float, default=600.0, help="per-request timeout in seconds")
    ap.add_argument("--wait", type=float, default=180.0,
                    help="llamacpp only: seconds to wait for /health while the server loads the model")
    ap.add_argument("--warmup", action="store_true",
                    help="send the first selected call once, unrecorded, before the run (use on the first job "
                         "after a model load, so load and first-use costs stay out of the latency figures)")
    ap.add_argument("--resume", action="store_true", help="skip calls already recorded without error in --out")
    ap.add_argument("--dry-run", action="store_true", help="print the first request payload and exit")
    args = ap.parse_args(argv)
    shape = SUITE_SHAPE[args.suite]

    if args.why and shape != "pick":
        ap.error("--why applies to the Pick suites only (pick, pick-hard)")
    if args.backend == "ollama" and not args.model:
        ap.error("--model is required with --backend ollama")
    if args.backend == "ollama":
        base_url = normalize_host(args.base_url or args.host)
        backend = OllamaBackend(base_url, args.timeout, args.think_mode, args.keep_alive)
    else:
        base_url = normalize_host(args.base_url or "http://127.0.0.1:8080", default_port="8080")
        backend = LlamaServerBackend(base_url, args.timeout, args.think_mode, args.api_key)
    sampler = {k: getattr(args, k) for k in SAMPLER_KEYS}

    suite, suite_sha = load_suite(args.suite)
    # A suite file may name its shape ("shape": "pick" in pick-hard.json); it must agree with SUITE_SHAPE,
    # which score.py reads from the same field.
    if suite.get("shape", args.suite) != shape:
        ap.error(f"suites/{args.suite}.json declares shape {suite.get('shape')!r}; run.py expects {shape!r}")
    items = suite["items"]
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

    variant = "why" if args.why else "plain"
    temperature = args.temperature if args.temperature is not None else TEMPERATURE[shape]
    cap_key = "pick_why" if args.why else shape
    num_predict = args.num_predict if args.num_predict is not None else NUM_PREDICT[cap_key]

    def make_payload(item, sample, model):
        """Build the backend's request body for one (item, sample); returns (payload, seed, extra record fields)."""
        user, schema, extra = build_call(shape, item, args.condition, sample, args.why)
        seed = sample_seed(item["id"], sample)
        messages = [{"role": "system", "content": SYSTEM[shape]}, {"role": "user", "content": user}]
        # The schema name is the shape, so a pick-hard request differs from a pick request only in its content.
        payload = backend.payload(model, messages, schema, temperature, seed, num_predict, args.num_ctx, sampler,
                                  schema_name=shape)
        return payload, seed, extra

    if args.dry_run:
        # Print the first request without touching the network or the output file.
        if not items:
            ap.error("no items selected")
        payload, _, extra = make_payload(items[0], 0, args.model)
        print(json.dumps(payload, ensure_ascii=False, indent=1))
        if extra:
            print(json.dumps(extra, ensure_ascii=False, indent=1))
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
    print(f"backend {backend.name} at {base_url}: model {model}, file {run_info['model_file']}, quant {quant}, "
          f"runtime {run_info['runtime_version']}, context {num_ctx}"
          + (f", template reads enable_thinking: {info.get('thinking_kwarg_changes_prompt')}"
             if args.backend == "llamacpp" else ""), flush=True)

    out = args.out or os.path.join(
        RESULTS_DIR, f"{slug(model)}__{args.suite}__{args.condition}{'__why' if args.why else ''}.jsonl")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    skip = done_keys(out) if args.resume else set()
    run_id = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    if args.warmup and items:
        # The first request after a model load pays one-time costs: Ollama loads the weights, and
        # llama-server's GPU backend builds its compute pipelines on first use (12.9 s for a 239-token
        # prompt on a GTX 1070 under Vulkan the first time a build ran, 1.3-3.8 s on later starts,
        # against 0.8 s warm). Doc 44 excluded load time the same way, with one unrecorded call per model.
        t0 = time.perf_counter()
        res = backend.chat(make_payload(items[0], 0, model)[0])
        print(f"warm-up call: {(time.perf_counter() - t0) * 1000.0:.0f} ms"
              + (f" (error: {res['error']})" if res["error"] else ""), flush=True)

    n_done = n_err = 0
    # Samples form the outer loop so an interrupted run still covers every item evenly.
    with open(out, "a", encoding="utf-8", newline="\n") as fout:
        for sample in range(args.k):
            for item in items:
                key = (model, args.suite, item["id"], args.condition, variant, sample)
                if key in skip:
                    continue
                payload, seed, extra = make_payload(item, sample, model)

                t0 = time.perf_counter()
                res = backend.chat(payload)
                latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)

                error, content = res["error"], res["content"]
                # Field names and units follow Ollama's (durations in ns), so score.py reads both backends.
                rec = {
                    "run_id": run_id, "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
                    "model": model, "suite": args.suite, "suite_sha": suite_sha, "item_id": item["id"],
                    "condition": args.condition, "variant": variant, "sample": sample, "seed": seed,
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
                if shape == "knowledge":
                    rec["parse_ok"] = bool(content.strip()) and not error
                    rec["parse_mode"] = "text"
                    rec["parsed"] = content.strip() if rec["parse_ok"] else None
                else:
                    parsed, mode = extract_json(content) if not error else (None, "no_response")
                    rec["parse_ok"] = parsed is not None
                    rec["parse_mode"] = mode
                    rec["parsed"] = parsed
                rec.update(extra)
                if shape == "pick":
                    choice = rec["parsed"].get("choice") if rec["parse_ok"] else None
                    chosen_letter = choice.strip().upper() if isinstance(choice, str) else None
                    rec["chosen_letter"] = chosen_letter
                    rec["chosen_key"] = extra["letter_to_key"].get(chosen_letter) if chosen_letter else None
                    rec["correct"] = rec["chosen_key"] == extra["correct_key"]
                    if args.why and rec["parse_ok"]:
                        rec["why"] = rec["parsed"].get("why")

                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fout.flush()
                n_done += 1
                n_err += 1 if error else 0
                status = f"ERROR {error}" if error else (
                    f"{rec.get('chosen_letter')} ({'correct' if rec.get('correct') else 'wrong, want ' + extra['correct_letter']})"
                    if shape == "pick" else ("parsed" if rec["parse_ok"] else "PARSE FAIL"))
                print(f"[{args.suite}/{args.condition}/{variant}] {item['id']} s{sample} -> {status} "
                      f"{latency_ms:.0f} ms, {rec['eval_count']} tok", flush=True)

    print(f"done: {n_done} calls, {n_err} errors -> {out}")
    return 0 if n_err == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
