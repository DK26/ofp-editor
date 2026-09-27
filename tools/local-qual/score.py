#!/usr/bin/env python3
"""Score local-qual JSONL records (tools/local-qual).

What it does
------------
Reads the JSONL written by run.py and computes, per (model, suite, condition,
variant):

* pick (and pick-hard, whose suite file declares the Pick shape): accuracy
  per sample and overall, pass^k (every sample of an item correct),
  majority-vote accuracy, position-bias tables (accuracy by the
  correct option's letter, and how often each letter was chosen), escape use,
  and two baselines: random-valid (mean of 1/number of real options) and
  always-first-option (share of calls whose correct option landed on A);
* fill: schema-valid rate, exact-field accuracy (micro and per field), all
  fields correct, quote-check pass rate, all validators passing;
* text: pass rate per code check (word cap, digits, banned era words, names)
  and all checks passing;
* explain: schema validity, the two-sentence cap and forbidden-pattern flags;
  the grade itself stays "ungraded";
* knowledge: "ungraded" (answer length only);
* all suites: latency p50/p90, generation tokens per second, token counts.

It writes a flat summary CSV and a nested JSON, and optionally a grading sheet
(JSONL) for the LLM graders of knowledge, explain and text quality.

Scores are recomputed from raw fields against the current suite files; a
record whose suite_sha differs from the current file is counted and reported
(the suite changed after the run).
"""
import argparse
import csv
import glob
import hashlib
import json
import os
import re
import statistics
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SUITES_DIR = os.path.join(HERE, "suites")
RESULTS_DIR = os.path.join(HERE, "results")

WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'\-]*")
NAME_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")


# ── Loading ──────────────────────────────────────────────────────────────────

def load_suites():
    """Return {suite: (suite dict, {item id: item}, sha)} for every suite file present."""
    out = {}
    for path in sorted(glob.glob(os.path.join(SUITES_DIR, "*.json"))):
        with open(path, "rb") as f:
            raw = f.read()
        suite = json.loads(raw.decode("utf-8"))
        out[suite["suite"]] = (suite, {it["id"]: it for it in suite["items"]},
                               hashlib.sha256(raw).hexdigest()[:16])
    return out


def load_records(patterns):
    recs = []
    for pattern in patterns:
        paths = sorted(glob.glob(pattern)) or ([pattern] if os.path.exists(pattern) else [])
        for path in paths:
            with open(path, encoding="utf-8") as f:
                for n, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        recs.append(json.loads(line))
                    except ValueError:
                        print(f"warning: {path}:{n} is not JSON; skipped", file=sys.stderr)
    return recs


# ── Small helpers ────────────────────────────────────────────────────────────

def percentile(values, q):
    """Linear-interpolation percentile (q in 0..100) of a non-empty list."""
    vals = sorted(values)
    if not vals:
        return None
    if len(vals) == 1:
        return vals[0]
    pos = (len(vals) - 1) * q / 100.0
    lo = int(pos)
    hi = min(lo + 1, len(vals) - 1)
    return vals[lo] + (vals[hi] - vals[lo]) * (pos - lo)


def rate(num, den):
    return round(num / den, 4) if den else None


def norm_span(text):
    """Normalise a span for comparison: lower case, collapse spaces, trim punctuation and quotes."""
    s = re.sub(r"\s+", " ", str(text or "")).strip().lower()
    return s.strip(" .,;:!?\"'`")


def words(text):
    return WORD_RE.findall(text or "")


def validate_schema(value, schema, path="$"):
    """Validate `value` against the JSON-schema subset the suites use.

    Supports type, enum, properties, required, additionalProperties (bool),
    minLength/maxLength, items, minItems/maxItems. Returns a list of errors.
    """
    errs = []
    typ = schema.get("type")
    types = typ if isinstance(typ, list) else ([typ] if typ else [])
    py = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}

    def is_type(t):
        if t == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if t == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        return isinstance(value, py.get(t, object))

    if types and not any(is_type(t) for t in types):
        return [f"{path}: expected {typ}, got {type(value).__name__}"]
    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{path}: {value!r} not in enum")
    if isinstance(value, str):
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errs.append(f"{path}: length {len(value)} > {schema['maxLength']}")
        if "minLength" in schema and len(value) < schema["minLength"]:
            errs.append(f"{path}: length {len(value)} < {schema['minLength']}")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for req in schema.get("required", []):
            if req not in value:
                errs.append(f"{path}: missing {req}")
        if schema.get("additionalProperties") is False:
            for extra in value:
                if extra not in props:
                    errs.append(f"{path}: unexpected {extra}")
        for k, sub in props.items():
            if k in value:
                errs.extend(validate_schema(value[k], sub, f"{path}.{k}"))
    if isinstance(value, list):
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errs.append(f"{path}: {len(value)} items > {schema['maxItems']}")
        if "minItems" in schema and len(value) < schema["minItems"]:
            errs.append(f"{path}: {len(value)} items < {schema['minItems']}")
        if "items" in schema:
            for i, v in enumerate(value):
                errs.extend(validate_schema(v, schema["items"], f"{path}[{i}]"))
    return errs


def banned_hits(text, banned):
    low = (text or "").lower()
    return [b for b in banned if re.search(r"(?<![a-z0-9])" + re.escape(b.lower()) + r"(?![a-z0-9])", low)]


def name_violations(text, allowed, allowlist):
    """Capitalised tokens that are not allowed names.

    Checked: every capitalised token that does not start a sentence; every
    all-caps token of two or more letters; and a sentence-initial token that is
    directly followed by a comma (an address such as "Ivan, move"). Other
    sentence-initial tokens are exempt, because ordinary words are capitalised
    there; this is a known blind spot (see README).
    """
    ok = {a.lower() for a in allowed} | {a.lower() for a in allowlist}
    bad = []
    s = text or ""
    for m in NAME_TOKEN_RE.finditer(s):
        tok = m.group(0)
        if not tok[0].isupper():
            continue
        before = s[: m.start()].rstrip(" \"'([")
        sentence_start = before == "" or before[-1] in ".!?:;\n" or before.endswith(("--", "—"))
        after = s[m.end():]
        address = after.startswith(",")
        all_caps = len(tok) >= 2 and tok.isupper()
        if sentence_start and not all_caps and not address:
            continue
        if tok.lower() not in ok:
            bad.append(tok)
    return bad


def sentence_count(text):
    """Count sentences: a break is [.!?] + whitespace + a capital letter or opening quote.

    Requiring the capital keeps SQS code such as "? !alive leader1 : exit" from
    counting as a sentence break.
    """
    t = (text or "").strip()
    if not t:
        return 0
    parts = [p for p in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(“])", t) if p.strip()]
    return len(parts)


# ── Per-suite scoring ────────────────────────────────────────────────────────

def score_pick(recs, items):
    by_item = defaultdict(list)
    per_sample = defaultdict(lambda: [0, 0])
    pos_stats = defaultdict(lambda: [0, 0])
    letter_counts = Counter()
    correct = parse_ok = escape_chosen = 0
    rand_base = []
    first_base = []
    escape_items = [0, 0]
    for r in recs:
        item = items.get(r["item_id"])
        ok = bool(r.get("parse_ok")) and r.get("chosen_key") == r.get("correct_key")
        correct += ok
        parse_ok += bool(r.get("parse_ok"))
        by_item[r["item_id"]].append(r)
        per_sample[r["sample"]][0] += ok
        per_sample[r["sample"]][1] += 1
        pos = r.get("correct_letter") or "?"
        pos_stats[pos][0] += ok
        pos_stats[pos][1] += 1
        letter_counts[r.get("chosen_letter") or "(none)"] += 1
        escape_chosen += r.get("chosen_letter") == "X"
        n_opts = r.get("n_options") or (len(item["options"]) if item else None)
        if n_opts:
            rand_base.append(1.0 / n_opts)
        first_base.append(1.0 if r.get("correct_pos") == 0 else 0.0)
        if item and item["answer"] == item["escape"]["key"]:
            escape_items[0] += ok
            escape_items[1] += 1
    n = len(recs)
    ks = [len(v) for v in by_item.values()]
    pass_k = sum(1 for v in by_item.values() if all(x.get("chosen_key") == x.get("correct_key") and x.get("parse_ok")
                                                   for x in v))
    maj_ok = ties = 0
    for v in by_item.values():
        votes = Counter(x.get("chosen_key") for x in v if x.get("parse_ok") and x.get("chosen_key"))
        top = votes.most_common()
        if not top:
            continue
        best = [k for k, c in top if c == top[0][1]]
        if len(best) > 1:
            ties += 1  # a tie counts as wrong: the harness would need another sample to decide
            continue
        maj_ok += best[0] == v[0].get("correct_key")
    cats = defaultdict(lambda: [0, 0])
    for r in recs:
        item = items.get(r["item_id"])
        cat = item["category"] if item else "?"
        cats[cat][0] += bool(r.get("parse_ok")) and r.get("chosen_key") == r.get("correct_key")
        cats[cat][1] += 1
    return {
        "calls": n, "items": len(by_item), "k": min(ks) if ks else 0,
        "parse_rate": rate(parse_ok, n),
        "accuracy": rate(correct, n),
        "accuracy_per_sample": {str(s): rate(c, t) for s, (c, t) in sorted(per_sample.items())},
        "pass_k": rate(pass_k, len(by_item)),
        "majority_accuracy": rate(maj_ok, len(by_item)),
        "majority_ties": ties,
        "accuracy_by_category": {c: rate(a, t) for c, (a, t) in sorted(cats.items())},
        "accuracy_by_correct_letter": {p: {"n": t, "accuracy": rate(c, t)} for p, (c, t) in sorted(pos_stats.items())},
        "chosen_letter_counts": dict(sorted(letter_counts.items())),
        "escape_rate": rate(escape_chosen, n),
        "escape_item_accuracy": rate(escape_items[0], escape_items[1]),
        "random_valid_baseline": round(statistics.mean(rand_base), 4) if rand_base else None,
        "first_option_baseline": round(statistics.mean(first_base), 4) if first_base else None,
    }


def check_validator(v, value, request, banned):
    """Apply one fill validator. Returns True/False, or None when it does not apply."""
    chk = v["check"]
    if chk == "enum":
        return None  # covered by the schema check; kept in the suite for readers
    if not isinstance(value, str):
        return False
    if chk == "quote_in_request":
        if value.strip() == "":
            return bool(v.get("allow_empty"))
        return norm_span(value) in norm_span(request)
    if chk == "max_chars":
        return len(value) <= v["value"]
    if chk == "max_words":
        return len(words(value)) <= v["value"]
    if chk == "non_empty":
        return value.strip() != ""
    if chk == "no_digits":
        return not re.search(r"\d", value)
    if chk == "banned_words":
        return not banned_hits(value, banned)
    if chk == "names_from_request":
        # Proper names in the text must come from the request (facts come from code or the user).
        req_tokens = {t.lower() for t in NAME_TOKEN_RE.findall(request)}
        return not name_violations(value, req_tokens, [])
    return None


def score_fill(recs, items, suite):
    banned = suite.get("banned_words", [])
    schema_ok = field_ok = field_n = all_ok = quote_ok = quote_n = val_all = parse_ok = 0
    per_field = defaultdict(lambda: [0, 0])
    per_item = defaultdict(lambda: [0, 0])
    for r in recs:
        item = items.get(r["item_id"])
        if item is None:
            continue
        parsed = r.get("parsed") if r.get("parse_ok") else None
        parse_ok += parsed is not None
        valid = parsed is not None and not validate_schema(parsed, item["schema"])
        schema_ok += valid
        rec_all = parsed is not None
        for field, spec in item["expected"].items():
            got = parsed.get(field) if isinstance(parsed, dict) else None
            if "any_of" in spec:
                good = got in spec["any_of"]
            else:
                good = isinstance(got, str) and norm_span(got) in {norm_span(x) for x in spec["span_any_of"]}
            field_ok += good
            field_n += 1
            per_field[field][0] += good
            per_field[field][1] += 1
            rec_all = rec_all and good
        all_ok += rec_all
        per_item[r["item_id"]][0] += rec_all
        per_item[r["item_id"]][1] += 1
        vals_pass = parsed is not None
        for v in item["validators"]:
            res = check_validator(v, parsed.get(v["field"]) if isinstance(parsed, dict) else None,
                                  item["request"], banned) if parsed is not None else False
            if res is None:
                continue
            if v["check"] == "quote_in_request":
                quote_ok += res
                quote_n += 1
            vals_pass = vals_pass and res
        val_all += vals_pass
    n = len(recs)
    return {
        "calls": n, "items": len(per_item), "parse_rate": rate(parse_ok, n),
        "schema_valid_rate": rate(schema_ok, n),
        "field_accuracy": rate(field_ok, field_n),
        "field_accuracy_by_field": {f: rate(a, t) for f, (a, t) in sorted(per_field.items())},
        "all_fields_correct_rate": rate(all_ok, n),
        "all_fields_correct_by_item": {i: rate(a, t) for i, (a, t) in sorted(per_item.items())},
        "quote_check_pass_rate": rate(quote_ok, quote_n),
        "validators_all_pass_rate": rate(val_all, n),
    }


def text_checks(item, text, suite):
    c = item["constraints"]
    nw = len(words(text))
    checks = {
        "max_words": nw <= c["max_words"],
        "min_words": nw >= c.get("min_words", 1),
        "banned_words": not banned_hits(text, suite.get("banned_words", [])),
    }
    if c.get("no_digits"):
        checks["no_digits"] = not re.search(r"\d", text)
    if c.get("names_check", True):
        checks["names_subset"] = not name_violations(text, c["allowed_names"], suite.get("name_allowlist", []))
    return checks, nw


def score_text(recs, items, suite):
    per_check = defaultdict(lambda: [0, 0])
    all_ok = parse_ok = 0
    nwords = []
    for r in recs:
        item = items.get(r["item_id"])
        if item is None:
            continue
        parsed = r.get("parsed") if r.get("parse_ok") else None
        text = parsed.get("text") if isinstance(parsed, dict) else None
        if not isinstance(text, str):
            # Unparsed output fails every check that would have applied to this item.
            for name in text_checks(item, "", suite)[0]:
                per_check[name][1] += 1
            continue
        parse_ok += 1
        checks, nw = text_checks(item, text, suite)
        nwords.append(nw)
        for name, ok in checks.items():
            per_check[name][0] += ok
            per_check[name][1] += 1
        all_ok += all(checks.values())
    n = len(recs)
    return {
        "calls": n, "items": len({r["item_id"] for r in recs}), "parse_rate": rate(parse_ok, n),
        "constraint_pass_rate": rate(all_ok, n),
        "pass_rate_by_check": {k: rate(a, t) for k, (a, t) in sorted(per_check.items())},
        "mean_words": round(statistics.mean(nwords), 2) if nwords else None,
        "quality": "ungraded",
    }


def score_explain(recs, items):
    schema_ok = cap_ok = flagged = parse_ok = 0
    for r in recs:
        item = items.get(r["item_id"])
        if item is None:
            continue
        parsed = r.get("parsed") if r.get("parse_ok") else None
        if parsed is None:
            continue
        parse_ok += 1
        schema_ok += not validate_schema(parsed, item["schema"])
        expl, fix = str(parsed.get("explanation", "")), str(parsed.get("fix", ""))
        cap_ok += sentence_count(expl) + sentence_count(fix) <= item["rubric"]["max_sentences"]
        text = expl + " " + fix
        flagged += any(re.search(p, text, re.I) for p in item["rubric"]["forbidden_patterns"])
    n = len(recs)
    return {"calls": n, "items": len({r["item_id"] for r in recs}), "parse_rate": rate(parse_ok, n),
            "schema_valid_rate": rate(schema_ok, n), "sentence_cap_pass_rate": rate(cap_ok, n),
            "forbidden_pattern_rate": rate(flagged, n), "grade": "ungraded"}


def score_knowledge(recs):
    lens = [len(r.get("raw") or "") for r in recs if r.get("parse_ok")]
    n = len(recs)
    return {"calls": n, "items": len({r["item_id"] for r in recs}),
            "parse_rate": rate(sum(1 for r in recs if r.get("parse_ok")), n),
            "mean_answer_chars": round(statistics.mean(lens), 1) if lens else None, "grade": "ungraded"}


def perf(recs):
    lat = [r["latency_ms"] for r in recs if r.get("latency_ms") is not None and not r.get("error")]
    ev = [r for r in recs if r.get("eval_count") and r.get("eval_duration")]
    tok = sum(r["eval_count"] for r in ev)
    dur = sum(r["eval_duration"] for r in ev) / 1e9
    pe = [r["prompt_eval_count"] for r in recs if r.get("prompt_eval_count") is not None]
    ec = [r["eval_count"] for r in recs if r.get("eval_count") is not None]
    return {
        "latency_p50_ms": round(percentile(lat, 50), 1) if lat else None,
        "latency_p90_ms": round(percentile(lat, 90), 1) if lat else None,
        "tokens_per_s": round(tok / dur, 2) if dur > 0 else None,
        "mean_prompt_tokens": round(statistics.mean(pe), 1) if pe else None,
        "mean_eval_tokens": round(statistics.mean(ec), 1) if ec else None,
        "done_reason_length": sum(1 for r in recs if r.get("done_reason") == "length"),
    }


# ── Grading sheet ────────────────────────────────────────────────────────────

def grading_rows(recs, suites):
    """Rows for LLM graders: knowledge, explain and text quality, with the item's reference material."""
    for r in recs:
        suite = r["suite"]
        if suite not in ("knowledge", "explain", "text") or r.get("error"):
            continue
        item = suites.get(suite, (None, {}, None))[1].get(r["item_id"])
        if item is None:
            continue
        row = {"suite": suite, "item_id": r["item_id"], "model": r["model"], "condition": r["condition"],
               "sample": r["sample"], "answer": r.get("parsed") if suite != "knowledge" else r.get("raw")}
        if suite == "knowledge":
            row.update(prompt=item["prompt"], ground_truth=item["ground_truth"], grading=item["grading"])
        elif suite == "explain":
            row.update(finding=f"{item['code']}: {item['message']}", context=item["context"], card=item["card"],
                       rubric=item["rubric"])
        else:
            row.update(slot=item["slot"], context=item["context"], constraints=item["constraints"])
        yield row


# ── Main ─────────────────────────────────────────────────────────────────────

CSV_COLS = ["model", "suite", "condition", "variant", "calls", "items", "k", "errors", "stale_suite_records",
            "parse_rate", "accuracy", "pass_k", "majority_accuracy", "random_valid_baseline",
            "first_option_baseline", "escape_rate", "schema_valid_rate", "field_accuracy",
            "all_fields_correct_rate", "quote_check_pass_rate", "validators_all_pass_rate",
            "constraint_pass_rate", "sentence_cap_pass_rate", "forbidden_pattern_rate", "grade",
            "latency_p50_ms", "latency_p90_ms", "tokens_per_s", "mean_prompt_tokens", "mean_eval_tokens",
            "done_reason_length"]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Score local-qual JSONL records.")
    ap.add_argument("inputs", nargs="*", default=[os.path.join(RESULTS_DIR, "*.jsonl")],
                    help="JSONL files or globs (default results/*.jsonl)")
    ap.add_argument("--csv", default=os.path.join(RESULTS_DIR, "summary.csv"))
    ap.add_argument("--json", default=os.path.join(RESULTS_DIR, "summary.json"))
    ap.add_argument("--grading-out", default=None, help="write a JSONL grading sheet for LLM graders")
    args = ap.parse_args(argv)

    suites = load_suites()
    recs = load_records(args.inputs)
    # Keep only run.py call records. A grading sheet written by an earlier
    # `--grading-out results/grading.jsonl` matches the default results/*.jsonl
    # glob; its rows carry model/suite/item_id but no run_id or seed, and scoring
    # them would double the call counts and halve the parse rates of the
    # knowledge, explain and text groups on every re-score.
    n_rows = len(recs)
    recs = [r for r in recs if "run_id" in r and "seed" in r]
    if len(recs) < n_rows:
        print(f"note: skipped {n_rows - len(recs)} rows that are not run.py records (for example a grading sheet)",
              file=sys.stderr)
    if not recs:
        print("no records found", file=sys.stderr)
        return 1

    groups = defaultdict(list)
    for r in recs:
        groups[(r["model"], r["suite"], r["condition"], r.get("variant", "plain"))].append(r)

    summary = []
    for (model, suite, condition, variant), grp in sorted(groups.items()):
        suite_def, items, sha = suites.get(suite, ({}, {}, None))
        # A suite file may declare the step shape it measures ("shape": "pick" in pick-hard.json); the
        # scorer follows the shape, while the summary keeps the suite's own name.
        shape = suite_def.get("shape", suite)
        ok = [r for r in grp if not r.get("error")]
        if shape == "pick":
            m = score_pick(ok, items)
        elif shape == "fill":
            m = score_fill(ok, items, suite_def)
        elif shape == "text":
            m = score_text(ok, items, suite_def)
        elif shape == "explain":
            m = score_explain(ok, items)
        else:
            m = score_knowledge(ok)
        m.update(perf(grp))
        m.update(model=model, suite=suite, condition=condition, variant=variant,
                 errors=len(grp) - len(ok),
                 stale_suite_records=sum(1 for r in grp if sha and r.get("suite_sha") not in (None, sha)))
        if shape == "fill":
            m["accuracy"] = m["field_accuracy"]
        summary.append(m)

    for path in (args.csv, args.json):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(args.csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS, extrasaction="ignore")
        w.writeheader()
        for m in summary:
            w.writerow({c: m.get(c) for c in CSV_COLS})
    with open(args.json, "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
        f.write("\n")
    if args.grading_out:
        with open(args.grading_out, "w", encoding="utf-8", newline="\n") as f:
            for row in grading_rows(recs, suites):
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # Compact console table.
    print(f"{'model':32} {'suite':9} {'cond':5} {'var':5} {'calls':>5} {'acc':>6} {'pass^k':>6} "
          f"{'maj':>6} {'rand':>6} {'first':>6} {'p50ms':>7} {'tok/s':>6}")
    for m in summary:
        def fmt(v):
            return "-" if v is None else (f"{v:.3f}" if isinstance(v, float) else str(v))
        acc = m.get("accuracy", m.get("constraint_pass_rate", m.get("grade")))
        print(f"{m['model'][:32]:32} {m['suite']:9} {m['condition']:5} {m['variant']:5} {m['calls']:>5} "
              f"{fmt(acc):>6} {fmt(m.get('pass_k')):>6} {fmt(m.get('majority_accuracy')):>6} "
              f"{fmt(m.get('random_valid_baseline')):>6} {fmt(m.get('first_option_baseline')):>6} "
              f"{fmt(m.get('latency_p50_ms')):>7} {fmt(m.get('tokens_per_s')):>6}")
    print(f"wrote {args.csv} and {args.json}" + (f" and {args.grading_out}" if args.grading_out else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
