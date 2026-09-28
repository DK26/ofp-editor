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
* all suites: latency p50/p90, generation tokens per second, token counts;
  for paid endpoints the summed cost, the cost per call and the mean
  reasoning tokens.

Harness-uplift variants (run.py ``--variant``) group separately, because the
variant is part of the group key. The open Pick arms (``open``, ``labels``)
answer with a name, not a letter: ``--open-grades`` reads the grade file
grade_open.py wrote and scores its mapped keys (``accuracy`` with the alias
mapping only, ``judge_mapped_accuracy`` with judge rows for the unmapped
answers). An open group with answers that have no grade gets no accuracy at
all, rather than a misleading one. ``--repair`` records add ``repair_rate``.

It writes a flat summary CSV and a nested JSON, and optionally a grading sheet
(JSONL) for the LLM graders of knowledge, explain and text quality.

Scores are recomputed from raw fields against the current suite files; a
record whose suite_sha differs from the current file is counted and reported
(the suite changed after the run). Budget rows written by the cloud backend
(``budget_event``) are skipped.
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

# The answer checks live in score_checks.py; they are re-exported here because uplift.py, prompts.py and cloud_run.py
# import them from score.py (one set of checks, so repair, scoring and the arm comparisons agree).
from score_checks import (NAME_TOKEN_RE, WORD_RE, banned_hits, check_validator, name_violations,  # noqa: F401
                          norm_span, sentence_count, text_checks, validate_schema, words)

HERE = os.path.dirname(os.path.abspath(__file__))
SUITES_DIR = os.path.join(HERE, "suites")
RESULTS_DIR = os.path.join(HERE, "results")

# run.py variants whose Pick answers are names, mapped to keys by grade_open.py.
OPEN_VARIANTS = ("open", "labels")


# ── Loading ──────────────────────────────────────────────────────────────────

def load_suites(extra_files=()):
    """Return {suite: (suite dict, {item id: item}, sha)} for every suite file present.

    `extra_files` adds suite files outside suites/ (run.py --suite-file, for example the staged pools), keyed by
    their own "suite" name like the others."""
    out = {}
    for path in sorted(glob.glob(os.path.join(SUITES_DIR, "*.json"))) + list(extra_files):
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


def apply_open_grades(recs, patterns, suites):
    """Put grade_open.py's mapped keys onto the open-arm Pick records (in place); see grade_open.apply_grades."""
    from grade_open import apply_grades  # sibling module; imported here so score.py loads without it otherwise
    return apply_grades(recs, patterns, {name: s[1] for name, s in suites.items()})


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
        # The escape by key, so a mapped open answer counts too (X always carries the escape key).
        escape_chosen += (r.get("chosen_key") == item["escape"]["key"]) if item else r.get("chosen_letter") == "X"
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
        # Share of calls that named a real option or the escape (a letter outside the menu, an unparsable
        # reply or an unmapped open answer does not).
        "valid_choice_rate": rate(sum(1 for r in recs if r.get("chosen_key") is not None), n),
    }


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


def answer_text(r):
    """A knowledge answer as graded: ``raw``, or the parsed answer when run.py removed a <think> block from it."""
    return (r.get("parsed") or "") if r.get("think_stripped") else (r.get("raw") or "")


def score_knowledge(recs):
    lens = [len(answer_text(r)) for r in recs if r.get("parse_ok")]
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
    # Paid endpoints: every record's cost counts, failed ones included (they may have been billed).
    costs = [r["cost_usd"] for r in recs if isinstance(r.get("cost_usd"), (int, float))]
    reasoning = [r["reasoning_tokens"] for r in recs if isinstance(r.get("reasoning_tokens"), (int, float))]
    return {
        "latency_p50_ms": round(percentile(lat, 50), 1) if lat else None,
        "latency_p90_ms": round(percentile(lat, 90), 1) if lat else None,
        "tokens_per_s": round(tok / dur, 2) if dur > 0 else None,
        "mean_prompt_tokens": round(statistics.mean(pe), 1) if pe else None,
        "mean_eval_tokens": round(statistics.mean(ec), 1) if ec else None,
        "done_reason_length": sum(1 for r in recs if r.get("done_reason") == "length"),
        "cost_usd_total": round(sum(costs), 8) if costs else None,
        "cost_usd_per_call": round(sum(costs) / len(recs), 8) if costs else None,
        "reasoning_tokens_mean": round(statistics.mean(reasoning), 1) if reasoning else None,
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
               "variant": r.get("variant", "plain"), "sample": r["sample"],
               "answer": r.get("parsed") if suite != "knowledge" else answer_text(r)}
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
            "done_reason_length",
            # Added with the cloud backend and the harness-uplift variants (empty for older runs).
            "valid_choice_rate", "open_ungraded", "map_exact", "map_substring", "map_escape", "map_unmapped",
            "judge_mapped_accuracy", "repair_rate", "cost_usd_total", "cost_usd_per_call", "reasoning_tokens_mean"]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Score local-qual JSONL records.")
    ap.add_argument("inputs", nargs="*", default=[os.path.join(RESULTS_DIR, "*.jsonl")],
                    help="JSONL files or globs (default results/*.jsonl)")
    ap.add_argument("--csv", default=os.path.join(RESULTS_DIR, "summary.csv"))
    ap.add_argument("--json", default=os.path.join(RESULTS_DIR, "summary.json"))
    ap.add_argument("--grading-out", default=None, help="write a JSONL grading sheet for LLM graders")
    ap.add_argument("--open-grades", nargs="*", default=None,
                    help="grade files from grade_open.py for the open Pick arms (default "
                         "results/grades/open-grades.jsonl when it exists)")
    ap.add_argument("--suite-file", action="append", default=[],
                    help="a suite file outside suites/ whose records are scored too (run.py --suite-file); repeatable")
    args = ap.parse_args(argv)

    suites = load_suites(args.suite_file)
    recs = load_records(args.inputs)
    # Budget rows (reserve, settle, stop) written by the cloud backend are bookkeeping, not calls.
    recs = [r for r in recs if "budget_event" not in r]
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

    if any(r.get("variant") in OPEN_VARIANTS for r in recs):
        default_grades = os.path.join(RESULTS_DIR, "grades", "open-grades.jsonl")
        grade_paths = args.open_grades if args.open_grades is not None else (
            [default_grades] if os.path.exists(default_grades) else [])
        stats = apply_open_grades(recs, grade_paths, suites) if grade_paths else Counter()
        if not grade_paths:
            print("note: open-arm Pick records found but no grade file; run grade_open.py first", file=sys.stderr)
        elif stats:
            print("open-arm grades: " + ", ".join(f"{k} {v}" for k, v in sorted(stats.items())), file=sys.stderr)

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
        if shape == "pick" and variant in OPEN_VARIANTS:
            # Open answers score only through their grades; without a grade for every answer, no accuracy.
            ungraded = sum(1 for r in ok if not r.get("_graded"))
            m["open_ungraded"] = ungraded
            for mode in ("exact", "substring", "escape", "unmapped"):
                m[f"map_{mode}"] = sum(1 for r in ok if r.get("_graded") and r.get("map_mode") == mode)
            if ungraded:
                for field in ("accuracy", "accuracy_per_sample", "pass_k", "majority_accuracy",
                              "accuracy_by_category", "escape_rate", "escape_item_accuracy", "valid_choice_rate"):
                    m[field] = None
                print(f"warning: {model} {suite} {condition} {variant}: {ungraded} open answers have no grade; "
                      f"no accuracy reported (run grade_open.py)", file=sys.stderr)
            elif any("_judge_key" in r for r in ok):
                judged = [dict(r, chosen_key=r["_judge_key"]) if "_judge_key" in r else r for r in ok]
                m["judge_mapped_accuracy"] = score_pick(judged, items)["accuracy"]
        if variant == "repair" or variant.endswith("-repair"):
            m["repair_rate"] = rate(sum(1 for r in ok if r.get("repair_used")), len(ok))
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
