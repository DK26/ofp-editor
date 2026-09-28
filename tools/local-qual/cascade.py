#!/usr/bin/env python3
"""Offline cascade simulator and confidence calibration over local-qual Pick records (tools/local-qual).

What it answers
---------------
"If the harness asked a small model first and escalated to a larger one only when the small one was unsure, how
accurate would the decisions be, how often would it escalate, and what would a decision cost and take?" No model
runs: it replays records that run.py already wrote for two or more models on the same Pick items and samples. Seeds
and option orders depend only on (item, sample), so records of different models pair exactly, and a confidence
threshold is swept over them.

Definitions (``simulate``)
--------------------------
* **Chain**: ``--chain ARM ARM [ARM ...]``, cheapest first, arms written ``model|suite|condition|variant`` as in
  uplift.py, all of one suite. Every stage but the last accepts its answer when the answer is valid and its
  confidence >= the threshold (one threshold for every stage); otherwise the next stage is asked. The last stage's
  answer is always accepted.
* **Signal** ``logprob`` (the unit is one (item, sample)): the confidence is the record's ``confidence``, the top
  option's probability from ``run.py --pick-mode logprob`` (after the temperature scaling of ``--calibration`` when
  the run used one); with ``--calibration ARM=FILE`` the record's raw ``p_by_key`` is rescaled here instead (a file
  fitted on another model is refused, as run.py does). ``--min-valid-mass V`` makes a decision whose menu letters
  held less than V of the model's next-token probability in some order (``valid_mass_min``) unconfident: a top
  probability renormalised from a sliver of mass is not a sure answer.
* **Signal** ``vote`` (the unit is one item; works on ordinary sampled records): a non-final stage spends ``--votes M``
  calls (samples 0..M-1; default: every sample the arm has for all items) and answers with their majority; the
  confidence is the majority's count / M, and a tie is never confident. The last stage is one call, scored as the
  mean over its samples (the expected accuracy of a single call).
* A failed call, an unparsed answer or an unusable confidence (missing, not a number, outside [0, 1]) is never
  accepted: it escalates at every threshold, and the last stage counts it wrong.
* **Cost per decision**: the calls actually made. A record's ``cost_usd`` (cloud; every record of a key counts,
  failed ones included) when present, else ``--price ARM=IN,OUT`` (USD per million prompt and output tokens) on the
  record's token counts, else ``--cost ARM=USD`` per call, else unknown (counted as 0 and listed under
  ``unpriced``). A logprob decision with ``--permute N`` is N calls (``completion_calls``: a decision that failed
  at order j made j + 1). **Latency** adds up along the chain, because the calls are sequential (``latency_ms`` of
  each record), and so do a vote stage's M calls (on a server with several slots they could run in parallel; the
  sum is then an upper bound).
* **Pairing**: a unit is kept only when every stage has it with the same seed, option order and answer key
  (``correct_key``); a suite edited between two runs can keep the order and change the answer.
* **Baselines** at each threshold: every model alone; random escalation at the same rate r, (1 - r) acc_first +
  r acc_last (two-stage chains); and the oracle, which escalates exactly the units the first stage gets wrong.
* **Signal quality** of the first stage: AUROC of its confidence for its own correctness (0.5 = chance), expected
  calibration error (10 equal-width bins) and Brier score.
* **Operating point**: among the thresholds whose accuracy is within ``--target-gap`` of the last stage alone, the
  one with the fewest escalations (then the higher accuracy, then the lower threshold), with an item-cluster
  bootstrap interval of (cascade - last stage alone). A threshold picked and scored on the same 30 items flatters
  the cascade, so a **two-fold cross-fit** also chooses it on one half of the items (split by a hash of the item
  id) and scores it on the other.

``calibrate`` fits the temperature T of a logprob arm by minimising the mean negative log-likelihood of the correct
option under p_T(k) ∝ p(k)^(1/T). The log-likelihood is concave in 1/T (a log-sum-exp of lines minus a line), so a
golden-section search over 1/T finds the optimum. Fit it on one set of records and apply it to another (another
suite, other samples, another condition): fitted and scored on the same records it looks better than it is.

Standard library only; it reads records with score.py's loader and reuses uplift.py's statistics. Its numeric
building blocks (safe numbers from records and flags, AUROC, ECE and Brier, the temperature fit) live in
cascade_numbers.py.
"""
import argparse
import csv
import json
import math
import os
import sys
from collections import Counter, defaultdict

from cascade_numbers import (EPS, calibration_report, fit_rows, fit_temperature, fold_of, mean, parse_assignments,
                             parse_cost, parse_price, parse_thresholds, probability, real, rnd, signal_quality)
from logprob_pick import apply_temperature, load_calibration
from score import RESULTS_DIR, load_records, load_suites, percentile
from uplift import bootstrap, spec


# ── Records to decisions ─────────────────────────────────────────────────────

def pick_records(recs, suites):
    """run.py call records of the Pick-shaped suites (budget rows, grading sheets and other shapes dropped)."""
    out = []
    for r in recs:
        if not isinstance(r, dict) or "budget_event" in r or "run_id" not in r or "seed" not in r:
            continue
        suite_def = suites.get(r.get("suite"), ({}, {}, None))[0]
        if suite_def.get("shape", r.get("suite")) == "pick" and "item_id" in r and "sample" in r:
            out.append(r)
    return out


def collapse(recs):
    """{arm: {(item, sample): {"rec": final record, "records": every record of that key}}}.

    A key written more than once (an error, then a --resume) keeps the last successful record as its answer, and
    every record of the key in its cost, as uplift.py does.
    """
    by = defaultdict(list)
    for r in recs:
        by[(r["model"], r["suite"], r["condition"], r.get("variant", "plain"))].append(r)
    arms = {}
    for arm, rs in by.items():
        keyed = defaultdict(list)
        for r in rs:
            keyed[(r["item_id"], r["sample"])].append(r)
        arms[arm] = {k: {"rec": ([r for r in v if not r.get("error")] or v)[-1], "records": v}
                     for k, v in keyed.items()}
    return arms


def calls_of(r):
    """Model calls behind one record: a logprob decision's /completion calls (the one that failed included; the
    option orders it kept when an older record has no count), plus a repair call when one was made."""
    lp = r.get("logprob") if isinstance(r.get("logprob"), dict) else {}
    orders = lp.get("orders")
    sent = lp.get("completion_calls")
    if isinstance(sent, int) and not isinstance(sent, bool) and sent >= 1:
        n = sent
    else:
        n = len(orders) if isinstance(orders, list) and orders else 1
    return n + (1 if r.get("repair_used") else 0)


def cost_of(records, price, flat):
    """USD of every record of one key: provider cost, else tokens x --price, else calls x --cost, else None."""
    costs = [real(r.get("cost_usd")) for r in records]
    if any(c is not None for c in costs):
        return sum(c for c in costs if c is not None)
    if price is not None:
        total = 0.0
        for r in records:
            pin, pout = real(r.get("prompt_eval_count")) or 0.0, real(r.get("eval_count")) or 0.0
            total += (pin * price[0] + pout * price[1]) / 1e6
        return total
    if flat is not None:
        return flat * sum(calls_of(r) for r in records)
    return None


def valid_answer(r):
    return not r.get("error") and bool(r.get("parse_ok")) and r.get("chosen_key") is not None


def confidence_of(r, temperature=None, min_valid_mass=0.0):
    """The record's confidence, or None when it is missing or unusable (such an answer is never accepted).

    With `min_valid_mass` > 0, a logprob decision whose menu letters held less than that share of the model's
    next-token probability in some option order (``valid_mass_min``, missing counts as unusable) has no usable
    confidence: renormalised from a sliver, a high top probability says little.
    """
    if min_valid_mass > 0:
        vm = probability(r.get("valid_mass_min"))
        if vm is None or vm < min_valid_mass - EPS:
            return None
    if temperature is not None:
        p = r.get("p_by_key")
        if not isinstance(p, dict) or not p:
            return None
        vals = {k: probability(v) for k, v in p.items()}
        if any(v is None for v in vals.values()) or sum(vals.values()) <= 0:
            return None
        return max(apply_temperature(vals, temperature).values())
    return probability(r.get("confidence"))


def has_confidence(dec):
    return any("confidence" in d["rec"] or "p_by_key" in d["rec"] for d in dec.values())


def unit(correct, conf, cost, latency, calls, key):
    return {"correct": correct, "conf": conf, "cost": cost, "latency": latency, "calls": calls, "key": key}


def stage_units(dec, signal, final, votes, temperature, price, flat, min_valid_mass=0.0):
    """{unit id: unit} for one stage of the chain (see the module docs for each signal's semantics)."""
    out = {}
    if signal == "logprob":
        for (item, sample), d in dec.items():
            r = d["rec"]
            ok = valid_answer(r)
            conf = confidence_of(r, temperature, min_valid_mass) if ok and not final else None
            out[(item, sample)] = unit(1.0 if ok and r["chosen_key"] == r.get("correct_key") else 0.0, conf,
                                       cost_of(d["records"], price, flat), real(r.get("latency_ms")) or 0.0,
                                       sum(calls_of(x) for x in d["records"]), r.get("chosen_key"))
        return out
    by_item = defaultdict(dict)
    for (item, sample), d in dec.items():
        by_item[item][sample] = d
    for item, samples in by_item.items():
        if final:
            ds = list(samples.values())
            rs = [d["rec"] for d in ds]
            costs = [cost_of(d["records"], price, flat) for d in ds]
            out[item] = unit(mean(1.0 if valid_answer(r) and r["chosen_key"] == r.get("correct_key") else 0.0
                                  for r in rs),
                             None, mean(costs) if all(c is not None for c in costs) else None,
                             mean(real(r.get("latency_ms")) or 0.0 for r in rs),
                             mean(sum(calls_of(x) for x in d["records"]) for d in ds), None)
            continue
        if not all(s in samples for s in range(votes)):
            continue  # fewer samples than votes: the unit is left out (reported as unpaired)
        ds = [samples[s] for s in range(votes)]
        rs = [d["rec"] for d in ds]
        tally = Counter(r["chosen_key"] for r in rs if valid_answer(r)).most_common()
        top = [k for k, c in tally if c == tally[0][1]] if tally else []
        key = top[0] if len(top) == 1 else None
        costs = [cost_of(d["records"], price, flat) for d in ds]
        out[item] = unit(1.0 if key is not None and key == rs[0].get("correct_key") else 0.0,
                         tally[0][1] / votes if key is not None else None,
                         sum(costs) if all(c is not None for c in costs) else None,
                         sum(real(r.get("latency_ms")) or 0.0 for r in rs),
                         sum(sum(calls_of(x) for x in d["records"]) for d in ds), key)
    return out


def consistent(decs, signal):
    """Unit ids whose records disagree on seed, option order or answer key between stages (the pairing check).

    The answer key is compared too: a suite edited between two runs can keep the option order and change the
    answer, and each stage is scored against its own record's ``correct_key``.
    """
    bad = set()
    for key in set().union(*[set(d) for d in decs]):
        seen = [d[key]["rec"] for d in decs if key in d]
        seeds = {r.get("seed") for r in seen}
        orders = {json.dumps(r.get("options_order")) for r in seen if r.get("options_order") is not None}
        answers = {json.dumps(r.get("correct_key")) for r in seen}
        if len(seeds) > 1 or len(orders) > 1 or len(answers) > 1:
            bad.add(key if signal == "logprob" else key[0])
    return bad


# ── The cascade at one threshold ─────────────────────────────────────────────

def run_at(stages, ids, tau):
    """Accuracy, escalation, cost and latency of the chain at threshold `tau` (math.inf: always escalate)."""
    n, last = len(ids), len(stages) - 1
    correct, costs, lats = [], [], []
    answered = [0] * len(stages)
    calls = [0.0] * len(stages)
    per_unit = {}
    for u in ids:
        cost = lat = 0.0
        for s, units in enumerate(stages):
            x = units[u]
            cost += x["cost"] or 0.0
            lat += x["latency"]
            calls[s] += x["calls"]
            if s == last or (x["conf"] is not None and x["conf"] >= tau - EPS):
                correct.append(x["correct"])
                per_unit[u] = x["correct"]
                answered[s] += 1
                break
        costs.append(cost)
        lats.append(lat)
    return {"threshold": "all" if tau == math.inf else rnd(tau, 10), "units": n,
            "accuracy": rnd(mean(correct)), "escalation_rate": rnd(1 - answered[0] / n) if n else None,
            "answered_by": [rnd(a / n) for a in answered], "calls_per_decision": [rnd(c / n) for c in calls],
            "cost_per_decision": rnd(mean(costs), 10), "latency_mean_ms": rnd(mean(lats), 1),
            "latency_p90_ms": rnd(percentile(lats, 90), 1) if lats else None, "_per_unit": per_unit}


def choose(rows, target):
    """The operating point: accuracy >= target, fewest escalations, then higher accuracy, then lower threshold."""
    ok = [r for r in rows if r["accuracy"] is not None and r["accuracy"] >= target - EPS]
    if not ok:
        return None
    return min(ok, key=lambda r: (r["escalation_rate"], -r["accuracy"],
                                  math.inf if r["threshold"] == "all" else r["threshold"]))


def as_tau(threshold):
    return math.inf if threshold == "all" else threshold


# ── Commands ─────────────────────────────────────────────────────────────────

def simulate(args, arms, err):
    """The whole ``simulate`` report as a dict (err(message) reports a refusal and exits 2)."""
    chain = [spec(a) for a in args.chain]
    if len(chain) < 2:
        err("--chain needs at least two arms, cheapest first")
    if len({a[1] for a in chain}) != 1:
        err("every arm of a chain must be of one suite (the items must be the same)")
    missing = ["|".join(a) for a in chain if a not in arms]
    if missing:
        err(f"no records for arm(s): {'; '.join(missing)} (arms found: "
            f"{'; '.join('|'.join(a) for a in sorted(arms)) or 'none'})")
    temps = {}
    for arm, path in args.calibration.items():
        if arm not in chain[:-1]:
            err(f"--calibration names {'|'.join(arm)}, which is not a non-final stage of the chain")
        if args.signal != "logprob":
            err("--calibration applies to the logprob signal only")
        try:
            cal = load_calibration(path)
        except ValueError as e:
            err(str(e))
        if cal["model"] is not None and cal["model"] != arm[0]:
            # run.py refuses the same mismatch: a temperature fitted on one model means nothing for another.
            err(f"the calibration file {path!r} was fitted on {cal['model']!r}, not {arm[0]!r}")
        temps[arm] = cal["temperature"]
    if args.min_valid_mass > 0 and args.signal != "logprob":
        err("--min-valid-mass applies to the logprob signal only")
    decs = [arms[a] for a in chain]
    if args.signal == "logprob":
        for arm, dec in zip(chain[:-1], decs[:-1]):
            if not has_confidence(dec):
                err(f"{'|'.join(arm)} has no logprob confidence; run it with --pick-mode logprob, or use --signal vote")
    votes = args.votes
    if args.signal == "vote":
        available = min(min(Counter(item for item, _ in dec).values()) for dec in decs[:-1])
        votes = available if votes is None else votes
        if votes < 1 or votes > available:
            err(f"--votes must be 1-{available} (the fewest samples any non-final arm has for an item)")
    stages = [stage_units(dec, args.signal, s == len(chain) - 1, votes, temps.get(arm),
                          args.price.get(arm), args.cost.get(arm), args.min_valid_mass)
              for s, (arm, dec) in enumerate(zip(chain, decs))]
    bad = consistent(decs, args.signal)
    common = set.intersection(*[set(s) for s in stages])
    ids = sorted(u for u in common if u not in bad)
    everything = set().union(*[set(s) for s in stages])
    dropped = {"unpaired": len(everything - common), "mismatched": len(common & bad)}
    if not ids:
        err("no unit is present in every stage of the chain with the same seed and option order")

    thresholds = parse_thresholds(args.thresholds)
    rows = [run_at(stages, ids, t) for t in thresholds] + [run_at(stages, ids, math.inf)]
    alone = []
    for arm, st in zip(chain, stages):
        xs = [st[u] for u in ids]
        costs = [x["cost"] for x in xs]
        lats = [x["latency"] for x in xs]
        alone.append({"arm": "|".join(arm), "accuracy": rnd(mean(x["correct"] for x in xs)),
                      "cost_per_decision": rnd(mean(c or 0.0 for c in costs), 10),
                      "priced": all(c is not None for c in costs), "latency_mean_ms": rnd(mean(lats), 1),
                      "latency_p90_ms": rnd(percentile(lats, 90), 1),
                      "calls_per_decision": rnd(mean(x["calls"] for x in xs))})
    first, final = alone[0]["accuracy"], alone[-1]["accuracy"]
    two = len(chain) == 2
    for r in rows:
        r["random_same_rate"] = rnd((1 - r["escalation_rate"]) * first + r["escalation_rate"] * final) if two else None
    target = final - args.target_gap
    op = choose(rows, target)
    report = {
        "chain": ["|".join(a) for a in chain], "signal": args.signal, "votes": votes if args.signal == "vote" else None,
        "calibration": {"|".join(a): t for a, t in temps.items()}, "min_valid_mass": args.min_valid_mass,
        "units": len(ids), "dropped": dropped,
        "items": len({u[0] if isinstance(u, tuple) else u for u in ids}),
        "alone": alone, "signal_quality": signal_quality([stages[0][u] for u in ids]),
        "target_accuracy": rnd(target), "operating_point": None, "cross_fit": None,
        "unpriced": [a["arm"] for a in alone if not a["priced"]],
    }
    if two:
        s0, s1 = stages
        oracle = [1.0 if s0[u]["correct"] >= 1.0 else s1[u]["correct"] for u in ids]
        report["oracle"] = {"accuracy": rnd(mean(oracle)),
                            "escalation_rate": rnd(mean(1.0 if s0[u]["correct"] < 1.0 else 0.0 for u in ids))}
    if op is not None:
        report["operating_point"] = operating_point(op, rows, stages, ids)
    report["cross_fit"] = cross_fit(stages, ids, thresholds, args.target_gap)
    report["curve"] = [{k: v for k, v in r.items() if k != "_per_unit"} for r in rows]
    return report


def item_of(u):
    return u[0] if isinstance(u, tuple) else u


def operating_point(op, rows, stages, ids):
    """The chosen row with an item-cluster bootstrap interval of (cascade - last stage alone)."""
    last = stages[-1]
    groups = defaultdict(list)
    for u in ids:
        groups[item_of(u)].append((op["_per_unit"][u], last[u]["correct"]))
    items = list(groups.values())

    def diff(sample):
        flat = [x for g in sample for x in g]
        return mean(a - b for a, b in flat) if flat else None

    lo, hi, p5 = bootstrap(items, diff)
    out = {k: v for k, v in op.items() if k != "_per_unit"}
    out.update(diff_vs_last=rnd(diff(items)), diff_ci95=[rnd(lo), rnd(hi)], diff_one_sided_lower95=rnd(p5))
    return out


def cross_fit(stages, ids, thresholds, gap):
    """Choose the threshold on one half of the items, score it on the other; pooled over both directions."""
    halves = {0: [u for u in ids if fold_of(item_of(u)) == 0], 1: [u for u in ids if fold_of(item_of(u)) == 1]}
    if not halves[0] or not halves[1]:
        return None
    detail, pooled = [], defaultdict(float)
    for fit, test in ((0, 1), (1, 0)):
        rows = [run_at(stages, halves[fit], t) for t in thresholds] + [run_at(stages, halves[fit], math.inf)]
        final_fit = mean(stages[-1][u]["correct"] for u in halves[fit])
        op = choose(rows, final_fit - gap) or rows[-1]
        tau = as_tau(op["threshold"])
        res = run_at(stages, halves[test], tau)
        final_test = mean(stages[-1][u]["correct"] for u in halves[test])
        detail.append({"fit_half": fit, "threshold": op["threshold"], "test_units": res["units"],
                       "test_accuracy": res["accuracy"], "test_last_alone": rnd(final_test),
                       "test_escalation_rate": res["escalation_rate"]})
        n = res["units"]
        pooled["n"] += n
        pooled["acc"] += res["accuracy"] * n
        pooled["esc"] += res["escalation_rate"] * n
        pooled["last"] += final_test * n
    n = pooled["n"]
    return {"halves": detail, "accuracy": rnd(pooled["acc"] / n), "escalation_rate": rnd(pooled["esc"] / n),
            "last_alone": rnd(pooled["last"] / n)}


def calibrate(args, arms, err):
    arm = spec(args.arm)
    if arm not in arms:
        err(f"no records for arm {args.arm}")
    rows = fit_rows(arms[arm])
    if not rows:
        err(f"{args.arm} has no usable logprob distributions (p_by_key); run it with --pick-mode logprob")
    t = fit_temperature(rows)
    out = {"method": "temperature", "temperature": round(t, 6), "model": arm[0], "suite": arm[1],
           "condition": arm[2], "variant": arm[3], "n": len(rows)}
    out.update(calibration_report(rows, t))
    out["note"] = "fitted on these records; apply it to other records (another suite, sample set or condition)"
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Offline cascade simulator and confidence calibration for Pick records.")
    sub = ap.add_subparsers(dest="command", required=True)
    sim = sub.add_parser("simulate", help="sweep a confidence threshold over a small-to-large chain of arms")
    sim.add_argument("inputs", nargs="*", default=[os.path.join(RESULTS_DIR, "*.jsonl")])
    sim.add_argument("--chain", nargs="+", required=True, help="arms model|suite|condition|variant, cheapest first")
    sim.add_argument("--signal", default="logprob", choices=("logprob", "vote"))
    sim.add_argument("--votes", type=int, default=None, help="vote: samples per non-final decision (default all)")
    sim.add_argument("--calibration", action="append", default=[], help="ARM=FILE: temperature for a logprob arm")
    sim.add_argument("--price", action="append", default=[], help="ARM=IN,OUT: USD per million tokens")
    sim.add_argument("--cost", action="append", default=[], help="ARM=USD: flat cost per call")
    sim.add_argument("--thresholds", default="0:1:0.05", help="start:stop:step (inclusive) or a comma list")
    sim.add_argument("--target-gap", type=float, default=0.0,
                     help="operating point: accuracy at least (last stage alone - this); default 0")
    sim.add_argument("--min-valid-mass", type=float, default=0.0,
                     help="logprob: a decision whose menu letters held less of the model's probability than this "
                          "(valid_mass_min) always escalates; default 0 (off)")
    sim.add_argument("--json", default=os.path.join(RESULTS_DIR, "cascade.json"))
    sim.add_argument("--csv", default=os.path.join(RESULTS_DIR, "cascade_curve.csv"))
    cal = sub.add_parser("calibrate", help="fit a temperature for a logprob arm")
    cal.add_argument("inputs", nargs="*", default=[os.path.join(RESULTS_DIR, "*.jsonl")])
    cal.add_argument("--arm", required=True, help="model|suite|condition|variant of a logprob arm")
    cal.add_argument("--out", required=True, help="calibration JSON to write (read by run.py --calibration)")
    args = ap.parse_args(argv)

    def err(msg):
        ap.error(msg)

    try:
        if args.command == "simulate":
            for arm in args.chain:
                spec(arm)  # a malformed arm spec is refused before any record is read
            args.calibration = parse_assignments(args.calibration, "--calibration", str)
            args.price = parse_assignments(args.price, "--price", parse_price)
            args.cost = parse_assignments(args.cost, "--cost", parse_cost)
            parse_thresholds(args.thresholds)
            if real(args.target_gap) is None or not 0.0 <= args.target_gap <= 1.0:
                raise ValueError("--target-gap must be in [0, 1]")
            if real(args.min_valid_mass) is None or not 0.0 <= args.min_valid_mass <= 1.0:
                raise ValueError("--min-valid-mass must be in [0, 1]")
        else:
            spec(args.arm)
    except ValueError as e:
        err(str(e))
    suites = load_suites()
    arms = collapse(pick_records(load_records(args.inputs), suites))
    if not arms:
        print("no Pick records found", file=sys.stderr)
        return 1

    if args.command == "calibrate":
        out = calibrate(args, arms, err)
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(out, f, indent=1)
            f.write("\n")
        print(f"T = {out['temperature']:.4f} on {out['n']} decisions: NLL {out['nll_before']} -> {out['nll_after']}, "
              f"ECE {out['ece_before']} -> {out['ece_after']}; wrote {args.out}")
        return 0

    report = simulate(args, arms, err)
    for path in (args.json, args.csv):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(args.json, "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
        f.write("\n")
    cols = ["threshold", "units", "accuracy", "escalation_rate", "random_same_rate", "cost_per_decision",
            "latency_mean_ms", "latency_p90_ms", "answered_by", "calls_per_decision"]
    with open(args.csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in report["curve"]:
            w.writerow({c: (json.dumps(r[c]) if isinstance(r.get(c), list) else r.get(c)) for c in cols})

    print(f"chain {' -> '.join(report['chain'])}; signal {report['signal']}; {report['units']} units over "
          f"{report['items']} items (dropped: {report['dropped']})")
    for a in report["alone"]:
        print(f"  alone {a['arm']}: accuracy {a['accuracy']}, {a['calls_per_decision']} calls, "
              f"{a['latency_mean_ms']} ms mean, cost {a['cost_per_decision']}" + ("" if a["priced"] else " (unpriced)"))
    q = report["signal_quality"]
    print(f"  first-stage confidence: AUROC {q['auroc']}, ECE {q['ece']}, Brier {q['brier']}")
    print(f"  {'thr':>5} {'acc':>7} {'esc':>7} {'random':>7} {'cost':>12} {'ms':>9}")
    for r in report["curve"]:
        print(f"  {str(r['threshold']):>5} {str(r['accuracy']):>7} {str(r['escalation_rate']):>7} "
              f"{str(r['random_same_rate']):>7} {str(r['cost_per_decision']):>12} {str(r['latency_mean_ms']):>9}")
    op = report["operating_point"]
    if op:
        print(f"  operating point (accuracy >= {report['target_accuracy']}): threshold {op['threshold']}, accuracy "
              f"{op['accuracy']}, escalation {op['escalation_rate']}, cascade - last {op['diff_vs_last']} "
              f"(95% {op['diff_ci95']})")
    cf = report["cross_fit"]
    if cf:
        print(f"  two-fold cross-fit: accuracy {cf['accuracy']} (last alone {cf['last_alone']}), escalation "
              f"{cf['escalation_rate']}")
    print(f"wrote {args.json} and {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
