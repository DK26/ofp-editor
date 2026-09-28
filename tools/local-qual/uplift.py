#!/usr/bin/env python3
"""Harness-uplift and cost analysis over local-qual records (tools/local-qual).

What it does
------------
score.py summarises each arm (model, suite, condition, variant) on its own.
This script answers the questions that need several arms at once: how much
does each harness mechanism lift a model, what does a *correct decision*
cost, and can a cheap model with the full harness replace a frontier model
without it. It reads run.py's JSONL (and, for the open Pick arms, the grade
files of grade_open.py; for explain, knowledge and text quality, an optional
grader file) and writes one JSON report and two CSV tables.

Definitions
-----------
* **Decision.** One (item, sample) of an arm. Records written more than once
  for the same key (an error, then a --resume) collapse to the last successful
  one, but every record's ``cost_usd`` stays in the cost.
* **Correct** per step kind: Pick, the chosen key is the answer key; Fill, the
  record parses, matches the item's schema, passes every validator and has all
  fields right; Text, every code check passes (a graded pass is reported next
  to it when a grader file is given); Explain and Knowledge, a graded "pass"
  (ungraded otherwise).
* **Admitted**: what the product's validators would accept. Pick, a real
  option or the escape; Fill, parses, schema-valid and every validator passes;
  Text, every code check passes; Explain, schema-valid, within the sentence
  cap and free of forbidden patterns; Knowledge, a non-empty answer.
  **False-admit rate** = admitted but wrong / admitted (for example a quoted
  span that exists in the request but is the wrong one).
* **pass^k**: the unbiased estimator of tau-bench (arXiv 2406.12045), the mean
  over items of C(c_i, k) / C(n_i, k), with n_i samples and c_i correct ones.
* **Policies**: ``single`` (sample 0); Pick ``vote3`` (majority of samples
  0-2, ties wrong, three calls) and ``adaptive`` (stop when samples 0 and 1
  agree, else take sample 2; two or three calls); ``first_admitted_2`` (sample
  0 if admitted, else sample 1; the offline "generate until the code checks
  pass, at most two samples").
* **CPCD** (cost per correct decision) = billed USD of every call a policy
  used, failed and repaired ones included / correct decisions. **CPAD** is the
  same numerator over admitted decisions (doc 40 §7).
* **Intervals**: Wilson 95% for per-call rates; for everything computed per
  item, an item-cluster bootstrap (10,000 resamples, fixed seed), because the
  samples of one item are correlated.
* **Paired comparisons** (bare arm against fuller arm, same model and suite):
  the paired decision-accuracy difference with its bootstrap interval, the
  exact McNemar p-value on discordant item decisions, the error reduction
  ERR = (err_bare - err_full) / err_bare, and the prompt-token overhead.
  Pick results are also split into engine-vocabulary items (waypoint, trigger:
  a model may know these words from training) and code-owned items (catalogue
  ids no bare model can know), because uplift on the latter is trivially large.
* **Gap closure** (``--gap CHEAP_BARE CHEAP_FULL FRONTIER_BARE``):
  H = (acc_cheap_full - acc_cheap_bare) / (acc_frontier_bare - acc_cheap_bare);
  H >= 1 means the harness lifts the cheap model to the bare frontier model.
  With it, a non-inferiority test of cheap_full against frontier_bare: the
  one-sided 95% lower bound of the difference must exceed -delta. Pick items
  are restricted to the engine-vocabulary categories unless
  ``--gap-all-items`` is given.
* **Pareto** per suite, never pooled across step kinds: the (arm, policy)
  points not beaten on both CPCD and decision accuracy.

Arm specs on the command line are ``model|suite|condition|variant``.
Standard library only; it reuses score.py's checks, so both agree.
"""
import argparse
import csv
import json
import math
import os
import random
import re
import statistics
import sys
from collections import Counter, defaultdict

from score import (RESULTS_DIR, apply_open_grades, check_validator, load_records, load_suites, norm_span,
                   percentile, sentence_count, text_checks, validate_schema)

# Pick categories whose option names a model may know from the game itself (engine vocabulary); every other
# category uses Plotroom's own catalogue ids, which no bare model can know.
ENGINE_CATEGORIES = ("waypoint", "trigger")
BOOT_N = 10000
BOOT_SEED = 20260927
Z95 = 1.959963984540054


# ── Statistics ───────────────────────────────────────────────────────────────

def wilson(k, n, z=Z95):
    """Wilson score interval for k successes in n trials, or (None, None) when n is 0."""
    if n == 0:
        return None, None
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def pass_hat_k(pairs, k):
    """Unbiased pass^k: mean over items of C(c, k) / C(n, k); items with fewer than k samples are left out."""
    vals = [math.comb(c, k) / math.comb(n, k) for n, c in pairs if n >= k]
    return statistics.mean(vals) if vals else None


def mcnemar_exact(b, c):
    """Two-sided exact McNemar p-value from the discordant counts b and c."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(0, min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def bootstrap(items, stat, n=BOOT_N, seed=BOOT_SEED):
    """Percentile interval (2.5, 97.5) and the one-sided 5th percentile of `stat` over item resamples."""
    if not items:
        return None, None, None
    rng = random.Random(seed)
    vals = []
    for _ in range(n):
        sample = [items[rng.randrange(len(items))] for _ in items]
        v = stat(sample)
        if v is not None:
            vals.append(v)
    if not vals:
        return None, None, None
    return percentile(vals, 2.5), percentile(vals, 97.5), percentile(vals, 5.0)


def rnd(v, nd=4):
    return None if v is None else round(v, nd)


# ── Per-record evaluation (mirrors score.py) ─────────────────────────────────

def evaluate(r, shape, item, suite_def, graded):
    """(correct, admitted, graded_pass) for one record; None means "not known" (ungraded)."""
    gp = graded.get(grade_key(r))
    if r.get("error"):
        # A failed call is a wrong decision, except in graded step kinds, where collapse() decides once it knows
        # whether the arm was graded at all.
        return (None if shape in ("explain", "knowledge") else False), False, gp
    parsed = r.get("parsed") if r.get("parse_ok") else None
    if shape == "pick":
        if r.get("variant") in ("open", "labels") and not r.get("_graded"):
            return None, None, gp
        chosen = r.get("chosen_key")
        return bool(r.get("parse_ok")) and chosen == r.get("correct_key"), chosen is not None, gp
    if shape == "fill":
        if not isinstance(parsed, dict):
            return False, False, gp
        valid = not validate_schema(parsed, item["schema"])
        vals = all(check_validator(v, parsed.get(v["field"]), item["request"],
                                   suite_def.get("banned_words", [])) is not False for v in item["validators"])
        fields = True
        for field, spec in item["expected"].items():
            got = parsed.get(field)
            if "any_of" in spec:
                fields = fields and got in spec["any_of"]
            else:
                fields = fields and isinstance(got, str) and \
                    norm_span(got) in {norm_span(x) for x in spec["span_any_of"]}
        admitted = valid and vals
        return admitted and fields, admitted, gp
    if shape == "text":
        text = parsed.get("text") if isinstance(parsed, dict) else None
        if not isinstance(text, str):
            return False, False, gp
        ok = all(text_checks(item, text, suite_def)[0].values())
        return ok, ok, gp
    if shape == "explain":
        if not isinstance(parsed, dict):
            return gp, False, gp
        expl, fix = str(parsed.get("explanation", "")), str(parsed.get("fix", ""))
        admitted = (not validate_schema(parsed, item["schema"])
                    and sentence_count(expl) + sentence_count(fix) <= item["rubric"]["max_sentences"]
                    and not any(re.search(p, expl + " " + fix, re.I) for p in item["rubric"]["forbidden_patterns"]))
        return gp, admitted, gp
    return gp, bool(r.get("parse_ok")), gp  # knowledge


def grade_key(r):
    return (r.get("model"), r.get("suite"), r.get("item_id"), r.get("condition"), r.get("variant", "plain"),
            r.get("sample"))


def load_graded(paths):
    """{record key: True/False} from grader rows ({model, suite, item_id, condition, variant, sample, verdict})."""
    out = {}
    for row in load_records(paths or []):
        if "verdict" in row and "item_id" in row:
            out[grade_key(row)] = row["verdict"] == "pass"
    return out


# ── Arms ─────────────────────────────────────────────────────────────────────

def arm_of(r):
    return (r["model"], r["suite"], r["condition"], r.get("variant", "plain"))


def spec(text):
    parts = text.split("|")
    if len(parts) != 4:
        raise ValueError(f"arm spec must be model|suite|condition|variant, got {text!r}")
    return tuple(parts)


def collapse(recs, suites, graded):
    """{arm: {(item, sample): decision dict}} with the cost of every record of that key summed."""
    by = defaultdict(list)
    for r in recs:
        by[(arm_of(r), r["item_id"], r["sample"])].append(r)
    arms = defaultdict(dict)
    for (arm, item_id, sample), rs in by.items():
        ok = [r for r in rs if not r.get("error")]
        final = (ok or rs)[-1]
        suite_def, items, _ = suites.get(arm[1], ({}, {}, None))
        item = items.get(item_id)
        if item is None:
            continue
        shape = suite_def.get("shape", arm[1])
        correct, admitted, gp = evaluate(final, shape, item, suite_def, graded)
        costs = [r["cost_usd"] for r in rs if isinstance(r.get("cost_usd"), (int, float))]
        arms[arm][(item_id, sample)] = {
            "correct": correct, "admitted": admitted, "graded_pass": gp, "key": final.get("chosen_key"),
            "cost": sum(costs) if costs else None, "latency": final.get("latency_ms"),
            "prompt_tokens": final.get("prompt_eval_count"), "error": bool(final.get("error")),
            "attempts": sum(int(r.get("attempts") or 1) for r in rs), "records": len(rs),
            "status_429": sum((r.get("http_status_history") or []).count(429) for r in rs),
            "category": item.get("category"), "escape_item": "escape" in item and item["answer"] == item["escape"]["key"],
            "shape": shape,
        }
    # In a graded arm (explain, knowledge), a decision that never produced an answer is wrong, not ungraded.
    for dec in arms.values():
        if any(d["graded_pass"] is not None for d in dec.values()):
            for d in dec.values():
                if d["error"] and d["correct"] is None:
                    d["correct"] = False
    # An open Pick arm with any answer lacking a (current) grade gets no accuracy at all, as in score.py: scoring
    # only the graded subset would bias every open-arm figure, pair and gap closure toward the easy answers.
    for arm, dec in arms.items():
        ungraded = sum(1 for d in dec.values() if d["shape"] == "pick" and d["correct"] is None and not d["error"])
        if arm[3] in ("open", "labels") and ungraded:
            print(f"warning: {'|'.join(arm)}: {ungraded} open answers have no grade; no accuracy reported for this "
                  f"arm (run grade_open.py)", file=sys.stderr)
            for d in dec.values():
                d["correct"], d["admitted"] = None, None
    return arms


def decisions(dec, policy):
    """{item: (correct, admitted, cost, latency, calls)} under `policy`, or {} when it does not apply."""
    by_item = defaultdict(dict)
    for (item_id, sample), d in dec.items():
        by_item[item_id][sample] = d
    out = {}
    for item_id, s in by_item.items():
        if policy == "single":
            used = [s.get(0)]
            pick = s.get(0)
        elif policy == "first_admitted_2":
            used = [s.get(0)] if s.get(0) and s[0]["admitted"] else [s.get(0), s.get(1)]
            pick = used[-1]
        elif policy in ("vote3", "adaptive"):
            if not all(x in s for x in (0, 1, 2)) or s[0]["shape"] != "pick":
                return {}
            if policy == "adaptive" and s[0]["key"] is not None and s[0]["key"] == s[1]["key"]:
                used, pick = [s[0], s[1]], s[0]
            elif policy == "adaptive":
                used, pick = [s[0], s[1], s[2]], s[2]
            else:
                used = [s[0], s[1], s[2]]
                votes = Counter(x["key"] for x in used if x["key"] is not None).most_common()
                top = [k for k, c in votes if votes and c == votes[0][1]]
                if len(top) == 1:
                    winner = next(x for x in used if x["key"] == top[0])
                    pick = winner
                else:
                    pick = {"correct": False if all(x["correct"] is not None for x in used) else None,
                            "admitted": False}
        else:
            raise ValueError(policy)
        if any(u is None for u in used) or pick is None:
            continue
        costs = [u["cost"] for u in used]
        out[item_id] = (pick["correct"], pick["admitted"],
                        sum(costs) if all(c is not None for c in costs) else None,
                        sum(u["latency"] or 0.0 for u in used), len(used))
    return out


def arm_metrics(arm, dec, k):
    """Per-call and per-policy metrics for one arm."""
    vals = list(dec.values())
    known = [d for d in vals if d["correct"] is not None]
    n_ok = sum(1 for d in known if d["correct"])
    lo, hi = wilson(n_ok, len(known))
    per_item = defaultdict(lambda: [0, 0])
    for (item_id, _), d in dec.items():
        if d["correct"] is not None:
            per_item[item_id][0] += 1
            per_item[item_id][1] += bool(d["correct"])
    pairs = list(per_item.values())
    lat = [d["latency"] for d in vals if d["latency"] is not None]
    costs = [d["cost"] for d in vals if d["cost"] is not None]
    calls = len(vals)
    m = {
        "model": arm[0], "suite": arm[1], "condition": arm[2], "variant": arm[3], "calls": calls,
        "items": len(per_item), "graded_calls": len(known),
        "acc_call": rnd(n_ok / len(known)) if known else None, "acc_call_lo": rnd(lo), "acc_call_hi": rnd(hi),
        "pass1": rnd(pass_hat_k(pairs, 1)), "pass_k": rnd(pass_hat_k(pairs, k)), "k": k,
        "latency_p50_ms": rnd(percentile(lat, 50), 1) if lat else None,
        "latency_p90_ms": rnd(percentile(lat, 90), 1) if lat else None,
        "mean_prompt_tokens": rnd(statistics.mean([d["prompt_tokens"] for d in vals if d["prompt_tokens"]]), 1)
        if any(d["prompt_tokens"] for d in vals) else None,
        "cost_usd_total": rnd(sum(costs), 8) if costs else None,
        "errors_per_100": rnd(100 * sum(d["error"] for d in vals) / calls, 2) if calls else None,
        "retries_per_100": rnd(100 * sum(d["attempts"] - d["records"] for d in vals) / calls, 2) if calls else None,
        "http429_per_100": rnd(100 * sum(d["status_429"] for d in vals) / calls, 2) if calls else None,
    }
    lo_b, hi_b, _ = bootstrap(pairs, lambda s: pass_hat_k(s, k))
    m["pass_k_lo"], m["pass_k_hi"] = rnd(lo_b), rnd(hi_b)
    if vals and vals[0]["shape"] == "pick":
        for group, cats in (("engine", ENGINE_CATEGORIES), ("code_owned", None)):
            sel = [d for d in known if (d["category"] in ENGINE_CATEGORIES) == (cats is not None)]
            m[f"acc_call_{group}"] = rnd(sum(bool(d["correct"]) for d in sel) / len(sel)) if sel else None
    m["policies"] = {}
    for policy in ("single", "vote3", "adaptive", "first_admitted_2"):
        dd = decisions(dec, policy)
        dd = {i: v for i, v in dd.items() if v[0] is not None}
        if not dd:
            continue
        correct = sum(1 for v in dd.values() if v[0])
        admitted = sum(1 for v in dd.values() if v[1])
        false_admit = sum(1 for v in dd.values() if v[1] and not v[0])
        cost = sum(v[2] for v in dd.values()) if all(v[2] is not None for v in dd.values()) else None
        items = list(dd.values())
        lo_d, hi_d, _ = bootstrap(items, lambda s: sum(1 for v in s if v[0]) / len(s))
        escapes = [dec_item for dec_item in dd if any(d["escape_item"] for (i, _), d in dec.items() if i == dec_item)]
        m["policies"][policy] = {
            "decisions": len(dd), "decision_acc": rnd(correct / len(dd)), "decision_acc_lo": rnd(lo_d),
            "decision_acc_hi": rnd(hi_d), "calls_per_decision": rnd(statistics.mean(v[4] for v in items), 3),
            "cost_usd": rnd(cost, 8) if cost is not None else None,
            "cpcd_usd": rnd(cost / correct, 8) if cost is not None and correct else None,
            "cpad_usd": rnd(cost / admitted, 8) if cost is not None and admitted else None,
            "false_admit_rate": rnd(false_admit / admitted) if admitted else None,
            "latency_per_decision_p50_ms": rnd(percentile([v[3] for v in items], 50), 1),
            "escapes_all_correct": all(dd[i][0] for i in escapes) if escapes else None,
        }
    return m


def paired(bare_dec, full_dec, bare_arm, full_arm, policy="single", categories=None):
    """Paired decision-accuracy comparison of two arms on the items both have (see the module docs)."""
    b, f = decisions(bare_dec, policy), decisions(full_dec, policy)

    def cat_ok(item_id, dec):
        if categories is None:
            return True
        cat = next((d["category"] for (i, _), d in dec.items() if i == item_id), None)
        return cat in categories
    items = sorted(i for i in set(b) & set(f) if b[i][0] is not None and f[i][0] is not None and cat_ok(i, bare_dec))
    if not items:
        return None
    rows = [(int(bool(b[i][0])), int(bool(f[i][0]))) for i in items]
    acc_b = statistics.mean(x for x, _ in rows)
    acc_f = statistics.mean(y for _, y in rows)
    lo, hi, lo_one = bootstrap(rows, lambda s: statistics.mean(y - x for x, y in s))
    n_b = sum(1 for x, y in rows if x == 0 and y == 1)
    n_c = sum(1 for x, y in rows if x == 1 and y == 0)
    tok_b = [d["prompt_tokens"] for d in bare_dec.values() if d["prompt_tokens"]]
    tok_f = [d["prompt_tokens"] for d in full_dec.values() if d["prompt_tokens"]]
    return {
        "bare": "|".join(bare_arm), "full": "|".join(full_arm), "policy": policy,
        "items_group": "all" if categories is None else "+".join(categories), "items": len(items),
        "acc_bare": rnd(acc_b), "acc_full": rnd(acc_f), "delta": rnd(acc_f - acc_b), "delta_lo": rnd(lo),
        "delta_hi": rnd(hi), "delta_lo_one_sided_95": rnd(lo_one),
        "err_reduction": rnd((acc_f - acc_b) / (1 - acc_b)) if acc_b < 1 else None,
        "mcnemar_fixed": n_b, "mcnemar_broken": n_c, "mcnemar_p": rnd(mcnemar_exact(n_b, n_c), 5),
        "token_overhead": rnd(statistics.mean(tok_f) / statistics.mean(tok_b), 3) if tok_b and tok_f else None,
    }


def auto_pairs(arms):
    """(bare arm, full arm) pairs the run design implies: variant against plain, repair against its base,
    cards against none, and every scaffold arm (run.py --scaffold) against the plain request it adds to."""
    out = []
    for (model, suite, cond, var) in arms:
        if var in ("open", "labels", "noschema", "schematext", "bare"):
            full = (model, suite, cond, "plain")
            if full in arms:
                out.append(((model, suite, cond, var), full))
        if var.startswith("scaffold-") and (model, suite, cond, "plain") in arms:
            out.append(((model, suite, cond, "plain"), (model, suite, cond, var)))
        if var == "repair" or var.endswith("-repair"):
            base_var = "plain" if var == "repair" else var[: -len("-repair")]
            if (model, suite, cond, base_var) in arms:
                out.append(((model, suite, cond, base_var), (model, suite, cond, var)))
        if cond == "none" and (model, suite, "cards", var) in arms:
            out.append(((model, suite, "none", var), (model, suite, "cards", var)))
    return out


def gap(arms, cheap_bare, cheap_full, frontier_bare, policy, delta, all_items):
    """Gap closure H and the non-inferiority test (see the module docs)."""
    decs = [decisions(arms[a], policy) for a in (cheap_bare, cheap_full, frontier_bare)]
    shape_dec = arms[cheap_bare]
    engine_only = not all_items and next(iter(shape_dec.values()))["shape"] == "pick"

    def keep(item_id):
        if not engine_only:
            return True
        return next((d["category"] for (i, _), d in shape_dec.items() if i == item_id), None) in ENGINE_CATEGORIES
    items = sorted(i for i in set(decs[0]) & set(decs[1]) & set(decs[2])
                   if keep(i) and all(d[i][0] is not None for d in decs))
    if not items:
        return None
    rows = [tuple(int(bool(d[i][0])) for d in decs) for i in items]

    def h_of(s):
        a_b, a_f, a_x = (statistics.mean(r[j] for r in s) for j in range(3))
        return None if a_x == a_b else (a_f - a_b) / (a_x - a_b)
    acc = [statistics.mean(r[j] for r in rows) for j in range(3)]
    lo, hi, _ = bootstrap(rows, h_of)
    d_lo, d_hi, d_lo_one = bootstrap(rows, lambda s: statistics.mean(r[1] - r[2] for r in s))
    costs = []
    for d in decs:
        c = [d[i][2] for i in items]
        cor = sum(1 for i in items if d[i][0])
        costs.append(sum(c) / cor if all(x is not None for x in c) and cor else None)
    return {
        "cheap_bare": "|".join(cheap_bare), "cheap_full": "|".join(cheap_full), "frontier_bare": "|".join(frontier_bare),
        "policy": policy, "items": len(items), "items_group": "engine" if engine_only else "all",
        "acc_cheap_bare": rnd(acc[0]), "acc_cheap_full": rnd(acc[1]), "acc_frontier_bare": rnd(acc[2]),
        "H": rnd(h_of(rows)), "H_lo": rnd(lo), "H_hi": rnd(hi),
        "delta_full_vs_frontier": rnd(acc[1] - acc[2]), "delta_lo_one_sided_95": rnd(d_lo_one),
        "non_inferior": (d_lo_one is not None and d_lo_one > -delta), "margin": delta,
        "cpcd_cheap_full": rnd(costs[1], 8), "cpcd_frontier_bare": rnd(costs[2], 8),
        "cpcd_ratio_frontier_over_cheap": rnd(costs[2] / costs[1], 2) if costs[1] and costs[2] else None,
    }


def pareto(arm_rows):
    """Mark (arm, policy) points per suite that no other point beats on both CPCD (lower) and decision accuracy."""
    pts = [(m["suite"], m, p, v) for m in arm_rows for p, v in m["policies"].items()
           if v.get("cpcd_usd") is not None and v.get("decision_acc") is not None]
    out = []
    for suite, m, p, v in pts:
        dominated = any(s2 == suite and v2["cpcd_usd"] <= v["cpcd_usd"] and v2["decision_acc"] >= v["decision_acc"]
                        and (v2["cpcd_usd"] < v["cpcd_usd"] or v2["decision_acc"] > v["decision_acc"])
                        for s2, _, _, v2 in pts)
        out.append({"suite": suite, "arm": "|".join((m["model"], m["suite"], m["condition"], m["variant"])),
                    "policy": p, "cpcd_usd": v["cpcd_usd"], "decision_acc": v["decision_acc"],
                    "pass_k": m["pass_k"], "pareto": not dominated})
    return sorted(out, key=lambda r: (r["suite"], r["cpcd_usd"]))


# ── Main ─────────────────────────────────────────────────────────────────────

def main(argv=None):
    ap = argparse.ArgumentParser(description="Harness uplift, cost per correct decision and gap closure.")
    ap.add_argument("inputs", nargs="*", default=[os.path.join(RESULTS_DIR, "*.jsonl")])
    ap.add_argument("--open-grades", nargs="*", default=None, help="grade_open.py grade files")
    ap.add_argument("--graded", nargs="*", default=None,
                    help="grader rows for explain, knowledge and text ({model, suite, item_id, condition, variant, "
                         "sample, verdict: pass|partial|fail})")
    ap.add_argument("--k", type=int, default=3, help="k for pass^k (default 3)")
    ap.add_argument("--pair", nargs=2, action="append", default=[], metavar=("BARE", "FULL"),
                    help="an explicit paired comparison (arm specs model|suite|condition|variant)")
    ap.add_argument("--no-auto-pairs", action="store_true", help="skip the pairs implied by the variants")
    ap.add_argument("--gap", nargs=3, action="append", default=[], metavar=("CHEAP_BARE", "CHEAP_FULL", "FRONTIER_BARE"))
    ap.add_argument("--gap-all-items", action="store_true", help="gap closure on all Pick items, not engine-vocabulary")
    ap.add_argument("--policy", default="single", help="decision policy for pairs and gap (default single)")
    ap.add_argument("--delta", type=float, default=0.10, help="non-inferiority margin (default 0.10)")
    ap.add_argument("--json", default=os.path.join(RESULTS_DIR, "uplift.json"))
    ap.add_argument("--arms-csv", default=os.path.join(RESULTS_DIR, "uplift_arms.csv"))
    ap.add_argument("--pairs-csv", default=os.path.join(RESULTS_DIR, "uplift_pairs.csv"))
    ap.add_argument("--suite-file", action="append", default=[],
                    help="a suite file outside suites/ whose records are compared too (run.py --suite-file)")
    args = ap.parse_args(argv)

    suites = load_suites(args.suite_file)
    recs = [r for r in load_records(args.inputs) if "budget_event" not in r and "run_id" in r and "seed" in r]
    if not recs:
        print("no records found", file=sys.stderr)
        return 1
    if any(r.get("variant") in ("open", "labels") for r in recs):
        default = os.path.join(RESULTS_DIR, "grades", "open-grades.jsonl")
        paths = args.open_grades if args.open_grades is not None else ([default] if os.path.exists(default) else [])
        apply_open_grades(recs, paths, suites)
    arms = collapse(recs, suites, load_graded(args.graded))
    arm_rows = [arm_metrics(a, arms[a], args.k) for a in sorted(arms)]

    pair_specs = [] if args.no_auto_pairs else auto_pairs(set(arms))
    try:
        pair_specs += [(spec(b), spec(f)) for b, f in args.pair]
        gaps = [tuple(spec(x) for x in g) for g in args.gap]
    except ValueError as e:
        ap.error(str(e))
    pairs = []
    for b, f in pair_specs:
        if b not in arms or f not in arms:
            print(f"warning: pair {'|'.join(b)} / {'|'.join(f)}: arm missing", file=sys.stderr)
            continue
        for cats in (None, ENGINE_CATEGORIES, tuple(sorted({d['category'] for d in arms[b].values()
                                                            if d['category'] not in ENGINE_CATEGORIES}))):
            if cats is not None and next(iter(arms[b].values()))["shape"] != "pick":
                continue
            p = paired(arms[b], arms[f], b, f, args.policy, cats)
            if p:
                if cats is not None and cats != ENGINE_CATEGORIES:
                    p["items_group"] = "code_owned"
                elif cats == ENGINE_CATEGORIES:
                    p["items_group"] = "engine"
                pairs.append(p)
    gap_rows = []
    for g in gaps:
        if not all(a in arms for a in g):
            print(f"warning: gap {g}: arm missing", file=sys.stderr)
            continue
        row = gap(arms, *g, args.policy, args.delta, args.gap_all_items)
        if row:
            gap_rows.append(row)
    front = pareto(arm_rows)

    report = {"arms": arm_rows, "pairs": pairs, "gap": gap_rows, "pareto": front,
              "settings": {"k": args.k, "policy": args.policy, "delta": args.delta, "bootstrap": BOOT_N,
                           "seed": BOOT_SEED}}
    for path in (args.json, args.arms_csv, args.pairs_csv):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(args.json, "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
        f.write("\n")
    arm_cols = ["model", "suite", "condition", "variant", "policy", "calls", "items", "acc_call", "acc_call_lo",
                "acc_call_hi", "pass1", "pass_k", "pass_k_lo", "pass_k_hi", "decision_acc", "decision_acc_lo",
                "decision_acc_hi", "calls_per_decision", "cost_usd", "cpcd_usd", "cpad_usd", "false_admit_rate",
                "escapes_all_correct", "acc_call_engine", "acc_call_code_owned", "mean_prompt_tokens",
                "latency_p50_ms", "latency_per_decision_p50_ms", "errors_per_100", "retries_per_100",
                "http429_per_100"]
    with open(args.arms_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=arm_cols, extrasaction="ignore")
        w.writeheader()
        for m in arm_rows:
            for policy, v in (m["policies"] or {"-": {}}).items():
                w.writerow({**{k: m.get(k) for k in arm_cols}, **v, "policy": policy})
    pair_cols = ["bare", "full", "policy", "items_group", "items", "acc_bare", "acc_full", "delta", "delta_lo",
                 "delta_hi", "delta_lo_one_sided_95", "err_reduction", "mcnemar_fixed", "mcnemar_broken",
                 "mcnemar_p", "token_overhead"]
    with open(args.pairs_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=pair_cols, extrasaction="ignore")
        w.writeheader()
        for p in pairs:
            w.writerow(p)
    for p in pairs:
        print(f"{p['full']} vs {p['bare']} [{p['items_group']}]: {p['acc_bare']} -> {p['acc_full']} "
              f"(delta {p['delta']}, 95% {p['delta_lo']}..{p['delta_hi']}, McNemar p {p['mcnemar_p']})")
    for g in gap_rows:
        print(f"gap closure H {g['H']} ({g['H_lo']}..{g['H_hi']}), non-inferior at {g['margin']}: {g['non_inferior']}")
    print(f"wrote {args.json}, {args.arms_csv} and {args.pairs_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
