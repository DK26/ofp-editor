#!/usr/bin/env python3
"""Local-model qualification spike runner (tools/local-qual).

What it does
------------
Sends the spike suites (suites/*.json) to one model served by a local Ollama
server and writes one JSONL record per call. It measures whether a small local
model can carry the co-pilot's code-owned step shapes (doc 21 §3.1): a Pick
from a code-computed menu, a small typed Fill, a grounded two-sentence
explanation, a short flavour line, and the doc 30 knowledge tasks with and
without a reference card.

How it fits
-----------
run.py only collects raw evidence. score.py turns the JSONL into summary
tables; knowledge, explain and text quality are graded later by LLM graders
from the grading sheet score.py exports. Nothing here is product code: it is a
research tool, standard library only, so it runs on any machine with Python 3
and an Ollama server.

Design notes
------------
* Pick menus are permuted per (item id, sample) with a seeded RNG, so the
  correct option lands on different letters across samples, and the "none" and
  "cards" conditions see the same permutation (paired comparison). The escape
  option is always last as X (doc 21 §3.2).
* Structured steps pass the item's JSON schema as Ollama's `format`, which
  constrains decoding with a grammar, exactly as a product harness would.
* `think` is sent as false (these steps are meant to be answered directly). If
  the server rejects the field, the call is retried once without it and the
  record says so.
* Each call is independent (no chat history), as in the harness design of a
  fresh capsule per decision.
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
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SUITES_DIR = os.path.join(HERE, "suites")
RESULTS_DIR = os.path.join(HERE, "results")
SUITES = ("knowledge", "pick", "fill", "explain", "text")

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


# ── Ollama client ────────────────────────────────────────────────────────────

class Ollama:
    """Minimal /api/chat client (stream=false) with the think-field fallback."""

    def __init__(self, host, timeout, think_mode):
        self.url = host.rstrip("/") + "/api/chat"
        self.timeout = timeout
        # think_mode "false" sends think=false; "omit" never sends the field.
        self.send_think = think_mode == "false"

    def _post(self, payload):
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def chat(self, payload):
        """Return (response dict or None, error str or None, think_sent bool)."""
        body = dict(payload)
        if self.send_think:
            body["think"] = False
        for attempt in range(3):
            try:
                return self._post(body), None, "think" in body
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", "replace")[:500]
                if "think" in body and e.code in (400, 422, 500) and "think" in detail.lower():
                    # Older servers or non-thinking models may reject the field: retry once without it
                    # and stop sending it for the rest of the run.
                    body.pop("think", None)
                    self.send_think = False
                    continue
                return None, f"HTTP {e.code}: {detail}", "think" in body
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                if attempt < 2:
                    time.sleep(2.0)
                    continue
                return None, f"{type(e).__name__}: {e}", "think" in body
        return None, "retries exhausted", "think" in body


# ── Main loop ────────────────────────────────────────────────────────────────

def slug(text):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-")


def normalize_host(host):
    """Turn an OLLAMA_HOST value into a URL a client can connect to.

    OLLAMA_HOST is often set for the *server* as a bind address such as
    "0.0.0.0:11434". A client cannot connect to a wildcard address (Windows
    fails with WinError 10049), so, like the Ollama CLI, map 0.0.0.0 and :: to
    loopback, add the scheme and the default port 11434 when missing.
    """
    h = (host or "").strip() or "http://localhost:11434"
    if "://" not in h:
        h = "http://" + h
    scheme, rest = h.split("://", 1)
    hostport, _, path = rest.partition("/")
    if hostport.startswith("["):  # IPv6 literal, e.g. [::]:11434
        addr, _, port = hostport[1:].partition("]")
        port = port.lstrip(":")
    elif hostport.count(":") == 1:
        addr, port = hostport.split(":")
    else:
        addr, port = hostport, ""
    if addr in ("0.0.0.0", "::", ""):
        addr = "127.0.0.1"
    elif ":" in addr:
        addr = f"[{addr}]"
    return f"{scheme}://{addr}:{port or '11434'}" + (f"/{path}" if path else "")


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
    ap = argparse.ArgumentParser(description="Run a local-qual suite against an Ollama model.")
    ap.add_argument("--model", required=True, help="Ollama model name, e.g. qwen3.5:4b-q4_K_M or hf.co/<user>/<repo>:<quant>")
    ap.add_argument("--suite", required=True, choices=SUITES)
    ap.add_argument("--condition", default="none", choices=("none", "cards"),
                    help="'cards' appends the item's reference card when it has one")
    ap.add_argument("--k", type=int, default=3, help="samples per item (default 3)")
    ap.add_argument("--offset", type=int, default=0,
                    help="skip the first N items (after --items, before --limit); with --limit, runs a chunk")
    ap.add_argument("--limit", type=int, default=None, help="only the first N items (after --items and --offset)")
    ap.add_argument("--items", default=None, help="comma-separated item ids to run")
    ap.add_argument("--out", default=None, help="JSONL output (default results/<model>__<suite>__<condition>[__why].jsonl)")
    ap.add_argument("--host", default=os.environ.get("OLLAMA_HOST", "http://localhost:11434"))
    ap.add_argument("--why", action="store_true", help="pick only: ask for a short 'why' before the choice")
    ap.add_argument("--temperature", type=float, default=None, help="override the per-suite temperature")
    ap.add_argument("--num-ctx", type=int, default=8192)
    ap.add_argument("--num-predict", type=int, default=None, help="override the per-suite output token cap")
    ap.add_argument("--keep-alive", default="10m")
    ap.add_argument("--think-mode", default="false", choices=("false", "omit"),
                    help="'false' sends think=false (default); 'omit' leaves the field out")
    ap.add_argument("--timeout", type=float, default=600.0, help="per-request timeout in seconds")
    ap.add_argument("--resume", action="store_true", help="skip calls already recorded without error in --out")
    ap.add_argument("--dry-run", action="store_true", help="print the first request payload and exit")
    args = ap.parse_args(argv)

    if args.why and args.suite != "pick":
        ap.error("--why applies to --suite pick only")
    args.host = normalize_host(args.host)

    suite, suite_sha = load_suite(args.suite)
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
    temperature = args.temperature if args.temperature is not None else TEMPERATURE[args.suite]
    cap_key = "pick_why" if args.why else args.suite
    num_predict = args.num_predict if args.num_predict is not None else NUM_PREDICT[cap_key]

    def make_payload(item, sample):
        """Build the /api/chat body for one (item, sample); returns (payload, seed, extra record fields)."""
        user, schema, extra = build_call(args.suite, item, args.condition, sample, args.why)
        seed = sample_seed(item["id"], sample)
        payload = {
            "model": args.model,
            "messages": [{"role": "system", "content": SYSTEM[args.suite]},
                         {"role": "user", "content": user}],
            "stream": False,
            "keep_alive": args.keep_alive,
            "options": {"temperature": temperature, "num_ctx": args.num_ctx, "seed": seed,
                        "num_predict": num_predict},
        }
        if schema is not None:
            payload["format"] = schema  # grammar-constrained decoding against the item's schema
        return payload, seed, extra

    if args.dry_run:
        # Print the first request without touching the network or the output file.
        if not items:
            ap.error("no items selected")
        payload, _, extra = make_payload(items[0], 0)
        print(json.dumps(payload, ensure_ascii=False, indent=1))
        if extra:
            print(json.dumps(extra, ensure_ascii=False, indent=1))
        return 0

    out = args.out or os.path.join(
        RESULTS_DIR, f"{slug(args.model)}__{args.suite}__{args.condition}{'__why' if args.why else ''}.jsonl")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    skip = done_keys(out) if args.resume else set()
    client = Ollama(args.host, args.timeout, args.think_mode)
    run_id = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    n_done = n_err = 0
    # Samples form the outer loop so an interrupted run still covers every item evenly.
    with open(out, "a", encoding="utf-8", newline="\n") as fout:
        for sample in range(args.k):
            for item in items:
                key = (args.model, args.suite, item["id"], args.condition, variant, sample)
                if key in skip:
                    continue
                payload, seed, extra = make_payload(item, sample)

                t0 = time.perf_counter()
                resp, error, think_sent = client.chat(payload)
                latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)

                msg = (resp or {}).get("message") or {}
                content = msg.get("content", "") if resp else ""
                rec = {
                    "run_id": run_id, "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
                    "model": args.model, "suite": args.suite, "suite_sha": suite_sha, "item_id": item["id"],
                    "condition": args.condition, "variant": variant, "sample": sample, "seed": seed,
                    "temperature": temperature, "num_ctx": args.num_ctx, "num_predict": num_predict,
                    "think_sent": think_sent, "error": error, "raw": content,
                    "thinking_chars": len(msg.get("thinking") or ""),
                    "latency_ms": latency_ms,
                    "prompt_eval_count": (resp or {}).get("prompt_eval_count"),
                    "eval_count": (resp or {}).get("eval_count"),
                    "eval_duration": (resp or {}).get("eval_duration"),
                    "prompt_eval_duration": (resp or {}).get("prompt_eval_duration"),
                    "load_duration": (resp or {}).get("load_duration"),
                    "total_duration": (resp or {}).get("total_duration"),
                    "done_reason": (resp or {}).get("done_reason"),
                }
                if args.suite == "knowledge":
                    rec["parse_ok"] = bool(content.strip()) and not error
                    rec["parse_mode"] = "text"
                    rec["parsed"] = content.strip() if rec["parse_ok"] else None
                else:
                    parsed, mode = extract_json(content) if not error else (None, "no_response")
                    rec["parse_ok"] = parsed is not None
                    rec["parse_mode"] = mode
                    rec["parsed"] = parsed
                rec.update(extra)
                if args.suite == "pick":
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
                    if args.suite == "pick" else ("parsed" if rec["parse_ok"] else "PARSE FAIL"))
                print(f"[{args.suite}/{args.condition}/{variant}] {item['id']} s{sample} -> {status} "
                      f"{latency_ms:.0f} ms, {rec['eval_count']} tok", flush=True)

    print(f"done: {n_done} calls, {n_err} errors -> {out}")
    return 0 if n_err == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
