#!/usr/bin/env python3
"""Pre-registered analysis of the scaffold arms (run.py --scaffold): paired per-item tests with Holm, and the verdicts.

What it owns
------------
The decision rules of experiment-plan.json, as code, so they are fixed before any data exists:

* **Decision:** one (model, suite, item, condition, variant, sample). A decision with several records (an error record,
  then the one ``--resume`` re-ran; or a run repeated into the same file) counts once, as its last error-free record
  (its last record when every attempt failed: an unresolved error is a wrong decision), exactly as uplift.py's
  ``collapse``; the tokens and model calls of every attempt are summed into its cost.
* **Unit:** one (suite, item, condition). Each arm has k samples per unit; the unit's score is the mean correctness
  over its samples (Pick: the chosen key is the answer; Fill: schema-valid, every validator passing and every field
  right, exactly uplift.py's ``evaluate``). An arm is compared only with the baseline arm (default ``plain``) of the same
  model on the units both have with the same number of samples; a unit missing from either side is reported, not
  imputed. Every per-arm side figure (false escapes, wrong-but-valid, latency, tokens, model calls, truncated or
  thinking decisions) is computed over those shared units only, for the arm and for the baseline alike, so a
  cards-only arm (rule) is never held against the baseline's none-plus-cards pool.
* **Arms:** only variants starting with ``--arm-prefix`` (default ``scaffold-``) are compared, so a stray file of
  another variant (a logprob or --why run) in the input glob can neither join a Holm family nor get a verdict; the
  skipped variants are listed in the report.
* **Hint-only controls (SR3):** records of a suite named ``<suite>-hint-<mode>`` (control_suite.py) are never units of
  the primary test. Per arm, the hint-only accuracy (correct decisions over the arm's control decisions) is compared
  with chance (1 / menu size, X included) + 0.10 and with the baseline's hint-only accuracy on the same control units
  + 0.10; exceeding either fails SR3, which vetoes ``winner``. An arm with no control records reports ``sr3:
  not_run`` (no veto: the plan runs controls only for the arms that could choose by themselves).
* **Test:** the exact paired sign-flip permutation test of the summed per-unit difference. Differences are multiples of
  1/k, so the null distribution of the sum (each nonzero difference's sign flipped with probability 1/2) is computed
  exactly by dynamic programming over integer sums: no sampling, no approximation, any number of units. Two one-sided
  p-values: ``p_better`` (arm above baseline) and ``p_worse``.
* **Holm:** step-down over the arms of one family, a family being (model, step kind): all Pick arms of a model form one
  family, its Fill arms another. Separate Holm sets for ``p_better`` and ``p_worse``.
* **Verdict per arm:** ``winner`` when Holm-adjusted p_better < alpha AND the mean unit gain >= --min-gain AND the
  planted-escape recall is not lower AND the false-escape rate is not higher (doc 59 SR2) AND no category loses more
  than --max-category-loss units by majority (doc 55 PR4) AND SR3 did not fail; ``harmful`` when Holm-adjusted p_worse
  < alpha; otherwise ``no_effect``. The latency ratio (p50 per decision against the baseline's) is reported for doc 55
  PR6 and doc 59 SR5, never used to hide a result; the counts of truncated and thinking decisions are reported for
  PR1 (an arm that has any is invalid by the plan, a judgement left to the reader of the report).

How it fits
-----------
Reads run.py records (the same files score.py and uplift.py read) plus the suites (suites/ and --suite-file), and writes
one JSON report. Standard library only.
"""
import argparse
import json
import os
import statistics
import sys
from collections import defaultdict

from score import RESULTS_DIR, load_records, load_suites
from uplift import evaluate


# ── Exact paired sign-flip test ──────────────────────────────────────────────

def sign_flip_pvalues(diffs, k):
    """(p_better, p_worse) of the exact paired sign-flip test for per-unit differences that are multiples of 1/k.

    Each difference d is scaled to the integer D = round(d * k). Under the null each nonzero D is +|D| or -|D| with
    probability 1/2 independently, so the distribution of S = sum(D) is built by convolution over integers. p_better
    is P(S >= S_obs), p_worse is P(S <= S_obs). Units with D = 0 contribute nothing (they are ties)."""
    scaled = [int(round(d * k)) for d in diffs]
    nonzero = [abs(x) for x in scaled if x != 0]
    s_obs = sum(scaled)
    dist = {0: 1.0}
    for a in nonzero:
        nxt = defaultdict(float)
        for s, p in dist.items():
            nxt[s + a] += p / 2
            nxt[s - a] += p / 2
        dist = nxt
    p_better = sum(p for s, p in dist.items() if s >= s_obs)
    p_worse = sum(p for s, p in dist.items() if s <= s_obs)
    return min(1.0, p_better), min(1.0, p_worse)


def holm(pvalues):
    """Holm step-down adjusted p-values for {name: p}, returned as {name: adjusted p} (monotone, capped at 1)."""
    order = sorted(pvalues, key=lambda n: (pvalues[n], n))
    m = len(order)
    out, running = {}, 0.0
    for i, name in enumerate(order):
        running = max(running, min(1.0, (m - i) * pvalues[name]))
        out[name] = running
    return out


# ── Decisions and units ──────────────────────────────────────────────────────

# control_suite.py names its suites "<suite>-hint-<mode>"; their records are controls, never units of the primary test.
HINT_MARK = "-hint-"
# SR3 (experiment-plan.json, doc 59 T-L6): hint-only accuracy may exceed neither chance nor the baseline's by more.
SR3_MARGIN = 0.10


def is_hint_suite(name):
    return HINT_MARK in (name or "")


def collapse(recs):
    """[(final record, every record)] per decision (model, suite, item, condition, variant, sample).

    The final record is the last error-free one, else the last one: a decision that failed and was re-run by --resume
    counts once, as its retry, and one that never succeeded stays a (wrong) error. Mirrors uplift.py's collapse, so the
    two tools score the same decisions."""
    by = defaultdict(list)
    for r in recs:
        by[(r.get("model"), r.get("suite"), r.get("item_id"), r.get("condition"), r.get("variant", "plain"),
            r.get("sample"))].append(r)
    out = []
    for rs in by.values():
        ok = [r for r in rs if not r.get("error")]
        out.append(((ok or rs)[-1], rs))
    return out


def _truncated(r):
    """True when the decision's answer, or any call of a multi-call decision, stopped at its output cap."""
    led = r.get("scaffold") or {}
    return r.get("done_reason") == "length" or bool(led.get("truncated_calls"))


def units_of(recs, suites):
    """(arms, side, hint, info).

    arms: {(model, shape, variant): {(suite, item, condition): [correct, ...]}} over collapsed decisions of the
    primary suites. side: {(model, shape, variant): {unit: [per-decision side data]}} (latency, tokens and model calls
    summed over every attempt, false escape, wrong-but-valid, truncated, thinking). hint: {(model, variant): {unit:
    [(correct, chance)]}} from the hint-only control suites. info: {unit: {"escape", "category"}} plus the counts of
    duplicate records folded away and of the decisions whose suite is unknown (a pool run analysed without its
    --suite-file would otherwise lose half of its units without a word)."""
    arms = defaultdict(lambda: defaultdict(list))
    side = defaultdict(lambda: defaultdict(list))
    hint = defaultdict(lambda: defaultdict(list))
    info = {"units": {}, "folded_records": 0, "unscored": defaultdict(int)}
    for r, attempts in collapse(recs):
        info["folded_records"] += len(attempts) - 1
        unit = (r.get("suite"), r.get("item_id"), r.get("condition"))
        if is_hint_suite(r.get("suite")):
            # A control decision: right when the chosen key is the item's answer (the record carries both), chance
            # 1 / menu size with X. Pick only: control_suite.py refuses other shapes.
            correct = not r.get("error") and bool(r.get("parse_ok")) and r.get("chosen_key") is not None \
                and r.get("chosen_key") == r.get("correct_key")
            size = len(r.get("letter_to_key") or {}) or None
            hint[(r["model"], r.get("variant", "plain"))][unit].append((correct, 1.0 / size if size else None))
            continue
        suite_def, items, _ = suites.get(r.get("suite"), ({}, {}, None))
        item = items.get(r.get("item_id"))
        if item is None:
            info["unscored"][str(r.get("suite"))] += 1
            continue
        shape = suite_def.get("shape", r["suite"])
        if shape not in ("pick", "fill"):
            continue
        correct, admitted, _ = evaluate(r, shape, item, suite_def, {})
        arm = (r["model"], shape, r.get("variant", "plain"))
        arms[arm][unit].append(bool(correct))
        escape_item = shape == "pick" and item["answer"] == item["escape"]["key"]
        info["units"][unit] = {"escape": escape_item,
                               "category": item.get("category") if shape == "pick" else item.get("kind")}
        side[arm][unit].append({
            "latency": r.get("latency_ms") if not r.get("error") else None,
            "prompt_tokens": sum(a.get("prompt_eval_count") or 0 for a in attempts),
            "eval_tokens": sum(a.get("eval_count") or 0 for a in attempts),
            "model_calls": sum(a.get("n_calls") or 1 for a in attempts),
            # A false escape: X chosen on an item whose answer is a real option (None on planted escapes).
            "false_escape": (r.get("chosen_key") == item["escape"]["key"]) if shape == "pick" and not escape_item
            else None,
            "wrong_valid": bool(admitted) and not correct,
            "truncated": _truncated(r),
            "thinking": bool(r.get("thinking_chars")),
        })
    return arms, side, hint, info


def majority(values):
    return sum(values) * 2 > len(values)


def _over(side, units, field):
    """Every non-None value of `field` in the side data of `units`, in unit order."""
    return [d[field] for u in units for d in side.get(u, []) if d[field] is not None]


def _mean(values, nd=4):
    return round(statistics.mean(values), nd) if values else None


def sr3(hint, model, variant, baseline, margin=SR3_MARGIN):
    """SR3 for one arm: {"sr3": pass | fail | not_run, hint accuracies, chance} (see the module docs)."""
    arm_h = hint.get((model, variant)) or {}
    if not arm_h:
        return {"sr3": "not_run", "hint_units": 0, "hint_acc_arm": None, "hint_acc_base": None, "hint_chance": None}
    base_h = hint.get((model, baseline)) or {}
    dec = [d for u in sorted(arm_h) for d in arm_h[u]]
    acc_arm = statistics.mean(c for c, _ in dec)
    chances = [ch for _, ch in dec if ch is not None]
    chance = statistics.mean(chances) if chances else None
    shared = [u for u in sorted(arm_h) if u in base_h]
    acc_base = statistics.mean(c for u in shared for c, _ in base_h[u]) if shared else None
    fail = (chance is not None and acc_arm > chance + margin) or (acc_base is not None and acc_arm - acc_base > margin)
    return {"sr3": "fail" if fail else "pass", "hint_units": len(arm_h), "hint_acc_arm": round(acc_arm, 4),
            "hint_acc_base": None if acc_base is None else round(acc_base, 4),
            "hint_chance": None if chance is None else round(chance, 4)}


def compare(base_units, arm_units, base_side, arm_side, unit_info, k_expected=None):
    """The paired comparison of one arm with the baseline (see the module docs)."""
    shared = sorted(u for u in arm_units if u in base_units and len(arm_units[u]) == len(base_units[u]))
    missing = sorted(set(arm_units) ^ set(base_units))
    unequal = sorted(u for u in arm_units if u in base_units and len(arm_units[u]) != len(base_units[u]))
    ks = {len(arm_units[u]) for u in shared}
    k = max(ks) if ks else (k_expected or 1)
    diffs = [statistics.mean(arm_units[u]) - statistics.mean(base_units[u]) for u in shared]
    p_better, p_worse = sign_flip_pvalues(diffs, k) if len(ks) == 1 else (None, None)
    esc = [u for u in shared if unit_info.get(u, {}).get("escape")]
    esc_base = sum(majority(base_units[u]) for u in esc)
    esc_arm = sum(majority(arm_units[u]) for u in esc)
    cat_loss = defaultdict(int)
    for u in shared:
        if majority(base_units[u]) and not majority(arm_units[u]):
            cat_loss[unit_info.get(u, {}).get("category")] += 1
    # Every side figure over the shared units only, for both arms (see the module docs).
    fx_b = _mean(_over(base_side, shared, "false_escape")) or 0.0
    fx_a = _mean(_over(arm_side, shared, "false_escape")) or 0.0
    lat_b, lat_a = _over(base_side, shared, "latency"), _over(arm_side, shared, "latency")
    lat_b = statistics.median(lat_b) if lat_b else None
    lat_a = statistics.median(lat_a) if lat_a else None
    passk = lambda units: statistics.mean(all(units[u]) for u in shared) if shared else None  # noqa: E731
    return {
        "units": len(shared), "k": k if len(ks) == 1 else sorted(ks), "missing_units": len(missing),
        "unequal_units": len(unequal),
        "mean_base": round(statistics.mean(statistics.mean(base_units[u]) for u in shared), 4) if shared else None,
        "mean_arm": round(statistics.mean(statistics.mean(arm_units[u]) for u in shared), 4) if shared else None,
        "mean_gain": round(statistics.mean(diffs), 4) if diffs else None,
        "units_better": sum(d > 0 for d in diffs), "units_worse": sum(d < 0 for d in diffs),
        "pass_k_base": passk(base_units), "pass_k_arm": passk(arm_units),
        "p_better": p_better, "p_worse": p_worse,
        "escape_units": len(esc), "escape_recall_base": esc_base, "escape_recall_arm": esc_arm,
        "false_escape_base": fx_b, "false_escape_arm": fx_a,
        "wrong_valid_base": _mean(_over(base_side, shared, "wrong_valid")),
        "wrong_valid_arm": _mean(_over(arm_side, shared, "wrong_valid")),
        "category_losses": dict(cat_loss),
        "latency_p50_base": lat_b, "latency_p50_arm": lat_a,
        "latency_ratio": round(lat_a / lat_b, 3) if lat_a and lat_b else None,
        "mean_prompt_tokens_base": _mean(_over(base_side, shared, "prompt_tokens"), 1),
        "mean_prompt_tokens_arm": _mean(_over(arm_side, shared, "prompt_tokens"), 1),
        "mean_eval_tokens_base": _mean(_over(base_side, shared, "eval_tokens"), 1),
        "mean_eval_tokens_arm": _mean(_over(arm_side, shared, "eval_tokens"), 1),
        "mean_model_calls_base": _mean(_over(base_side, shared, "model_calls"), 2),
        "mean_model_calls_arm": _mean(_over(arm_side, shared, "model_calls"), 2),
        "truncated_decisions_arm": sum(_over(arm_side, shared, "truncated")),
        "thinking_decisions_arm": sum(_over(arm_side, shared, "thinking")),
    }


def verdict(row, alpha, min_gain, max_category_loss):
    """winner / harmful / no_effect / incomplete by the rules in the module docs."""
    if row["p_better"] is None or row["units"] == 0:
        return "incomplete"
    if row["holm_p_worse"] < alpha:
        return "harmful"
    ok = (row["holm_p_better"] < alpha and row["mean_gain"] >= min_gain
          and row["escape_recall_arm"] >= row["escape_recall_base"]
          and row["false_escape_arm"] <= row["false_escape_base"]
          and all(v <= max_category_loss for v in row["category_losses"].values())
          and row.get("sr3") != "fail")
    return "winner" if ok else "no_effect"


def analyse(recs, suites, baseline="plain", alpha=0.05, min_gain=0.05, max_category_loss=2, arm_prefix="scaffold-",
            report=None):
    """The rows: one per (model, step kind, arm) against the baseline, with Holm per (model, step kind).

    `report`, when given a dict, receives the skipped variants, the number of duplicate records folded away and the
    decisions per suite that could not be scored (no suite file for them)."""
    arms, side, hint, info = units_of(recs, suites)
    rows, skipped = [], set()
    families = defaultdict(list)
    for (model, shape, variant) in sorted(arms):
        if variant == baseline or (model, shape, baseline) not in arms:
            continue
        if not variant.startswith(arm_prefix):
            skipped.add(variant)
            continue
        row = {"model": model, "step_kind": shape, "arm": variant, "baseline": baseline}
        row.update(compare(arms[(model, shape, baseline)], arms[(model, shape, variant)],
                           side[(model, shape, baseline)], side[(model, shape, variant)], info["units"]))
        row.update(sr3(hint, model, variant, baseline) if shape == "pick" else
                   {"sr3": "not_applicable", "hint_units": 0, "hint_acc_arm": None, "hint_acc_base": None,
                    "hint_chance": None})
        rows.append(row)
        families[(model, shape)].append(row)
    for fam in families.values():
        usable = {r["arm"]: r for r in fam if r["p_better"] is not None}
        hb = holm({a: r["p_better"] for a, r in usable.items()})
        hw = holm({a: r["p_worse"] for a, r in usable.items()})
        for r in fam:
            r["family_size"] = len(usable)
            r["holm_p_better"] = hb.get(r["arm"])
            r["holm_p_worse"] = hw.get(r["arm"])
            r["verdict"] = verdict(r, alpha, min_gain, max_category_loss)
    if report is not None:
        report.update(skipped_variants=sorted(skipped), folded_records=info["folded_records"],
                      unscored_decisions=dict(sorted(info["unscored"].items())))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="Paired per-item tests with Holm for the scaffold arms (pre-registered).")
    ap.add_argument("inputs", nargs="*", default=[os.path.join(RESULTS_DIR, "*.jsonl")])
    ap.add_argument("--suite-file", action="append", default=[], help="suite files outside suites/ (the pools)")
    ap.add_argument("--baseline", default="plain", help="the baseline variant (default plain)")
    ap.add_argument("--arm-prefix", default="scaffold-",
                    help="compare only the variants starting with this (default scaffold-: the plan's arms)")
    ap.add_argument("--alpha", type=float, default=0.05, help="one-sided family-wise alpha (default 0.05)")
    ap.add_argument("--min-gain", type=float, default=0.05,
                    help="minimum mean per-unit gain for a winner on the tuning split (default 0.05)")
    ap.add_argument("--max-category-loss", type=int, default=2, help="doc 55 PR4 (default 2)")
    ap.add_argument("--json", default=os.path.join(RESULTS_DIR, "scaffold_stats.json"))
    args = ap.parse_args(argv)
    recs = [r for r in load_records(args.inputs) if "run_id" in r and "seed" in r and "budget_event" not in r]
    if not recs:
        print("no records found", file=sys.stderr)
        return 1
    extra = {}
    rows = analyse(recs, load_suites(args.suite_file), args.baseline, args.alpha, args.min_gain,
                   args.max_category_loss, args.arm_prefix, report=extra)
    os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
    with open(args.json, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"alpha": args.alpha, "min_gain": args.min_gain, "baseline": args.baseline,
                   "arm_prefix": args.arm_prefix, **extra, "rows": rows}, f, ensure_ascii=False, indent=1)
        f.write("\n")
    for r in rows:
        print(f"{r['model'][:28]:28} {r['step_kind']:5} {r['arm']:26} n={r['units']:>3} gain={r['mean_gain']} "
              f"p+={r['holm_p_better'] if r['holm_p_better'] is None else round(r['holm_p_better'], 4)} "
              f"p-={r['holm_p_worse'] if r['holm_p_worse'] is None else round(r['holm_p_worse'], 4)} "
              f"sr3={r['sr3']} -> {r['verdict']}")
    if extra.get("skipped_variants"):
        print(f"not compared (no '{args.arm_prefix}' prefix): {', '.join(extra['skipped_variants'])}")
    if extra.get("folded_records"):
        print(f"{extra['folded_records']} duplicate records folded into their decisions (a resumed error, a rerun)")
    for suite, n in (extra.get("unscored_decisions") or {}).items():
        print(f"warning: {n} decisions of suite {suite!r} were not scored (no such suite or item: pass its "
              f"--suite-file)", file=sys.stderr)
    print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
