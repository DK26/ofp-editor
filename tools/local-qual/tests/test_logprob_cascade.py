#!/usr/bin/env python3
"""Tests for the offline cascade simulator (cascade.py): two-stage logprob and vote cascades against
hand-computed accuracy, escalation, cost, latency, baselines and signal quality; pairing rules; unusable
answers; the temperature fit that --calibration reads; an end-to-end run through run.py and the mock
llama-server; and the simulator's refusals.

The records are synthetic (``rec`` below builds them as run.py writes them), except in c06.

Run the whole suite from the repository root with ``python -m unittest discover -s tools/local-qual/tests``;
the module docs of support.py explain the case functions and the environment switches.
"""

import contextlib
import io
import json
import os
import unittest

import logprob_support
import support
from logprob_support import *  # noqa: F401,F403 - the shared fixtures the cases use by name

URL = None  # the mock's base URL while this module runs (set by setUpModule)


def setUpModule():
    global URL
    URL = logprob_support.start("logprob-cascade")


def tearDownModule():
    logprob_support.finish()


# ── Synthetic records and the simulator in-process ─────────────────────────────

PICK_IDS = [it["id"] for it in SUITES["pick"]["items"]]


def rec(model, item, sample, variant="plain", chosen="answer", conf=None, error=None, cost=None, lat=100.0,
        order=None, p_by_key=None, parse_ok=True):
    """A synthetic run.py Pick record (seed and option order as run.py would write them)."""
    it = ITEMS[item]
    order = order or [o["key"] for o in permute_options(it, sample)]
    others = [o["key"] for o in it["options"] if o["key"] != it["answer"]]  # fixed across samples, so votes agree
    key = {"answer": it["answer"], "wrong": others[0], "wrong2": others[1], "wrong3": others[2]}.get(chosen, chosen)
    ok = parse_ok and not error
    r = {"run_id": "t", "seed": sample_seed(item, sample), "model": model, "suite": "pick", "condition": "none",
         "variant": variant, "item_id": item, "sample": sample, "error": error, "parse_ok": ok,
         "chosen_key": key if ok else None, "correct_key": it["answer"], "latency_ms": lat, "options_order": order,
         "prompt_eval_count": 200, "eval_count": 1}
    if cost is not None:
        r["cost_usd"] = cost
    if conf is not None:
        r["confidence"] = conf
    if p_by_key is not None:
        r["p_by_key"] = p_by_key
    return r


def write(name, recs):
    """Write records to a JSONL file in the work folder; returns its path."""
    path = out(name)
    with open(path, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    return path


def cascade_main(argv):
    """cascade.main in-process: (exit code, console text). argparse refusals raise SystemExit, which the test runner
    (it catches Exception) would not see, so they come back as an exit code here."""
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        try:
            code = cascade.main(argv)
        except SystemExit as e:
            code = e.code
    return code, sink.getvalue()


def simulate(paths, chain, *extra):
    """cascade.main in-process; returns the JSON report (each call gets its own numbered report file)."""
    js = out("cascade-" + str(len(os.listdir(out(".")))) + ".json")
    code, text = cascade_main(["simulate"] + list(paths) + ["--chain"] + chain + ["--json", js, "--csv", js + ".csv"]
                              + list(extra))
    check(code == 0, f"cascade exit {code}: {text[-300:]}")
    return load_json(js)


def row(report, threshold):
    """The report's curve row at `threshold`."""
    return next(r for r in report["curve"] if r["threshold"] == threshold)


# c01's ten hand-made units: the small model's (confidence, right?) and the large model's right/wrong per unit.
C01_SMALL = [(0.95, True), (0.9, True), (0.85, False), (0.8, True), (0.7, True), (0.6, False), (0.5, True),
             (0.4, False), (0.3, False), (None, None)]
C01_LARGE = [True, True, True, True, False, True, True, True, False, True]


# ── Cascade simulator (c01-c08) ────────────────────────────────────────────────

def c01_logprob_cascade_known_values():
    """A two-stage logprob cascade over 10 hand-made units reproduces hand-computed accuracy, escalation, cost,
    latency, baselines and signal quality.

    Why: this is the arithmetic every cascade figure in the docs will rest on.

    How: small (0.001 USD, 100 ms) is right on 5 of 10 (the 10th is an error), large (0.01 USD, 1000 ms) on 8. At 0.75
    the small answers 4 (3 right), the large 6 (4 right): 0.7, escalation 0.6, cost 0.007, 700 ms; random escalation
    at 0.6 gives 0.4 x 0.5 + 0.6 x 0.8 = 0.68. At 0.65 the small answers 5 (4 right) and the large 4 of the other 5:
    0.8 at escalation 0.5, the fewest escalations that match the large model. AUROC 21/25, Brier 1.725/10, ECE 2.9/10.
    """
    small = [rec("small", PICK_IDS[i], 0, "logprob", "answer" if ok else "wrong", conf=c, cost=0.001, lat=100.0,
                 error=("HTTP 500" if c is None else None)) for i, (c, ok) in enumerate(C01_SMALL)]
    large = [rec("large", PICK_IDS[i], 0, "plain", "answer" if ok else "wrong", cost=0.01, lat=1000.0)
             for i, ok in enumerate(C01_LARGE)]
    paths = [write("c01-small.jsonl", small), write("c01-large.jsonl", large)]
    chain = ["small|pick|none|logprob", "large|pick|none|plain"]
    rep = simulate(paths, chain)
    expect = {0.0: (0.6, 0.1), 0.35: (0.6, 0.2), 0.45: (0.7, 0.3), 0.55: (0.7, 0.4), 0.65: (0.8, 0.5), 0.75: (0.7, 0.6),
              0.85: (0.7, 0.7), 0.9: (0.8, 0.8), 0.95: (0.8, 0.9), 1.0: (0.8, 1.0), "all": (0.8, 1.0)}
    for t, (acc, esc) in expect.items():
        r = row(rep, t)
        check(close(r["accuracy"], acc) and close(r["escalation_rate"], esc), f"threshold {t}: {r}")
    r = row(rep, 0.75)
    check(close(r["cost_per_decision"], 0.007) and close(r["latency_mean_ms"], 700.0)
          and close(r["random_same_rate"], 0.68) and r["answered_by"] == [0.4, 0.6], f"0.75 row {r}")
    a = rep["alone"]
    check(close(a[0]["accuracy"], 0.5) and close(a[1]["accuracy"], 0.8) and close(a[0]["cost_per_decision"], .001)
          and close(a[1]["latency_mean_ms"], 1000.0), f"alone {a}")
    q = rep["signal_quality"]
    check(close(q["auroc"], 0.84) and close(q["brier"], 0.1725) and close(q["ece"], 0.29), f"signal quality {q}")
    check(close(rep["oracle"]["accuracy"], 0.9) and close(rep["oracle"]["escalation_rate"], 0.5), f"{rep['oracle']}")
    op = rep["operating_point"]
    check(op["threshold"] == 0.65 and close(op["accuracy"], 0.8) and close(op["escalation_rate"], 0.5)
          and close(op["diff_vs_last"], 0.0), f"op {op}")
    rep2 = simulate(paths, chain, "--target-gap", "0.1")
    check(rep2["operating_point"]["threshold"] == 0.45, f"gap 0.1: {rep2['operating_point']['threshold']}")
    cf = rep["cross_fit"]
    check(cf is not None and sum(h["test_units"] for h in cf["halves"]) == 10, f"cross-fit {cf}")
    return ("thr 0.75: acc 0.7, esc 0.6, 0.007 USD, 700 ms (random 0.68); op 0.65 = 0.8 at esc 0.5 (gap 0) / 0.45 "
            "(gap 0.1); oracle 0.9; "
            "AUROC 0.84, Brier 0.1725, ECE 0.29")


def c02_vote_cascade_known_values():
    """A vote-signal cascade: majority of the small model's samples, ties always escalate, the large model scored as
    the mean over its samples.

    Why: most existing records are sampled (no logprobs); agreement between samples is the confidence available for
    them, and a tie must never be taken as an answer.
    """
    a, b, c, d = PICK_IDS[:4]
    votes = {a: ["answer"] * 3, b: ["wrong", "answer", "wrong"], c: ["wrong", "answer", "wrong2"],
             d: ["answer", "answer", None]}
    small = []
    for item, vs in votes.items():
        for s, v in enumerate(vs):
            small.append(rec("small", item, s, chosen=v or "answer", error=("HTTP 500" if v is None else None)))
    large_ok = {a: [True, True], b: [True, False], c: [True, True], d: [False, False]}
    large = [rec("large", item, s, chosen="answer" if ok else "wrong", lat=1000.0)
             for item, oks in large_ok.items() for s, ok in enumerate(oks)]
    paths = [write("c02-small.jsonl", small), write("c02-large.jsonl", large)]
    chain = ["small|pick|none|plain", "large|pick|none|plain"]
    rep = simulate(paths, chain, "--signal", "vote")
    check(rep["votes"] == 3 and close(rep["alone"][0]["accuracy"], 0.5) and close(rep["alone"][1]["accuracy"], 0.625),
          f"alone {rep['alone']}")
    for t, (acc, esc) in {0.9: (0.625, 0.75), 0.6: (0.75, 0.25), 0.0: (0.75, 0.25)}.items():
        r = row(rep, t)
        check(close(r["accuracy"], acc) and close(r["escalation_rate"], esc), f"threshold {t}: {r}")
    check(close(row(rep, 0.6)["latency_mean_ms"], 550.0) and row(rep, 0.6)["calls_per_decision"] == [3.0, 0.25],
          f"latency/calls {row(rep, 0.6)}")
    rep2 = simulate(paths, chain, "--signal", "vote", "--votes", "2")
    check(close(row(rep2, 0.9)["accuracy"], 0.875) and close(row(rep2, 0.9)["escalation_rate"], 0.5),
          f"2 votes: {row(rep2, 0.9)}")
    return "3 votes: alone 0.5 / 0.625; thr 0.6: 0.75, esc 0.25, 550 ms, calls [3, 0.25]; the tie always escalates; 2 votes at 0.9: 0.875"


def c03_pairing_duplicates_and_mismatches():
    """Units are paired on (item, sample) with equal seeds and option orders; a key written twice keeps its last
    successful answer and the cost of both records.

    Why: pairing records from another suite version (another option order) would compare different questions, and
    dropping the cost of a failed-then-retried call would understate a cascade's cost.
    """
    i1, i2, i3 = PICK_IDS[:3]
    small = [rec("small", i1, 0, "logprob", conf=0.9, error="HTTP 500", cost=0.002),
             rec("small", i1, 0, "logprob", conf=0.9, cost=0.001),
             rec("small", i2, 0, "logprob", conf=0.9, cost=0.001),
             rec("small", i3, 0, "logprob", conf=0.9, cost=0.001,
                 order=list(reversed([o["key"] for o in permute_options(ITEMS[i3], 0)])))]
    large = [rec("large", i1, 0, cost=0.01), rec("large", i3, 0, cost=0.01)]
    rep = simulate([write("c03-small.jsonl", small), write("c03-large.jsonl", large)],
                   ["small|pick|none|logprob", "large|pick|none|plain"])
    check(rep["units"] == 1 and rep["dropped"] == {"unpaired": 1, "mismatched": 1}, f"units {rep['units']} {rep['dropped']}")
    check(close(rep["alone"][0]["cost_per_decision"], 0.003) and rep["alone"][0]["calls_per_decision"] == 2.0
          and close(row(rep, 0.5)["accuracy"], 1.0) and close(row(rep, 0.5)["escalation_rate"], 0.0),
          f"small alone {rep['alone'][0]}")
    return "1 unit kept, 1 unpaired, 1 mismatched order; the retried key costs 0.003 USD over 2 calls"


def c04_unusable_answers_always_escalate():
    """Errors, unparsed answers and unusable confidences (NaN, string, bool, > 1, < 0, missing) escalate even at 0.

    Why: accepting a failed decision at a low threshold would make a cheap model look good for the wrong reason.
    """
    ids = PICK_IDS[:7]
    small = [rec("small", ids[0], 0, "logprob", conf=0.8),
             rec("small", ids[1], 0, "logprob", conf=0.8, error="boom"),
             rec("small", ids[2], 0, "logprob", conf=0.8, parse_ok=False),
             rec("small", ids[3], 0, "logprob", conf=float("nan")),
             rec("small", ids[4], 0, "logprob", conf="0.9"),
             rec("small", ids[5], 0, "logprob", conf=1.5),
             rec("small", ids[6], 0, "logprob", conf=True)]
    small[6]["confidence"] = True
    large = [rec("large", i, 0, chosen="wrong") for i in ids]
    rep = simulate([write("c04-small.jsonl", small), write("c04-large.jsonl", large)],
                   ["small|pick|none|logprob", "large|pick|none|plain"], "--thresholds", "0")
    r = row(rep, 0.0)
    check(close(r["escalation_rate"], 6 / 7) and close(r["accuracy"], 1 / 7)
          and rep["signal_quality"]["no_confidence"] == 6, f"threshold 0: {r} {rep['signal_quality']}")
    return "6 of 7 unusable small answers escalated at threshold 0 (only the valid 0.8 was accepted)"


def c05_calibrate_known_temperature():
    """cascade.py calibrate finds T = ln 9 / ln 1.5 = 5.41902 where it is known in closed form, and the file drives
    both simulate --calibration and run.py --calibration.

    Why: an over-confident model (0.9 on everything, right 60% of the time) must come out calibrated to 0.6.

    How: two-option distributions, correct at 0.9 on 6 items and at 0.1 on 4; with one confidence level the NLL
    optimum puts the calibrated 0.9 at the empirical 0.6: sigmoid(ln 9 / T) = 0.6.
    """
    recs = []
    for i, item in enumerate(PICK_IDS[:10]):
        it = ITEMS[item]
        other = next(o["key"] for o in it["options"] if o["key"] != it["answer"])
        p = {it["answer"]: 0.9, other: 0.1} if i < 6 else {it["answer"]: 0.1, other: 0.9}
        recs.append(rec("cal", item, 0, "logprob", chosen="answer" if i < 6 else other, conf=0.9, p_by_key=p))
    path = write("c05.jsonl", recs)
    cal_path = out("c05-cal.json")
    code, _ = cascade_main(["calibrate", path, "--arm", "cal|pick|none|logprob", "--out", cal_path])
    cal = load_json(cal_path)
    check(code == 0 and close(cal["temperature"], 5.419023, 1e-4) and cal["nll_after"] < cal["nll_before"]
          and close(cal["ece_before"], 0.3) and close(cal["ece_after"], 0.0, 1e-4) and cal["model"] == "cal",
          f"fit {cal}")
    check(lp.load_calibration(cal_path)["temperature"] == cal["temperature"], "run.py cannot read the file")
    large = [rec("large", item, 0) for item in PICK_IDS[:10]]
    rep = simulate([path, write("c05-large.jsonl", large)], ["cal|pick|none|logprob", "large|pick|none|plain"],
                   "--calibration", f"cal|pick|none|logprob={cal_path}", "--thresholds", "0.5,0.65")
    check(close(row(rep, 0.5)["escalation_rate"], 0.0) and close(row(rep, 0.65)["escalation_rate"], 1.0),
          f"calibrated confidences 0.6: {row(rep, 0.5)} {row(rep, 0.65)}")
    return f"T = {cal['temperature']} (closed form 5.419023); ECE 0.3 -> {cal['ece_after']}; calibrated confidence 0.6 accepted at 0.5, escalated at 0.65"


def c06_end_to_end_with_the_mock_server():
    """run.py writes a logprob arm and a sampled arm against the mock; cascade.py pairs them and finds the threshold
    that keeps the large model's accuracy at half the escalations.

    Why: the pieces must fit: record fields, labels, seeds and option orders written by run.py are what cascade.py
    pairs on.

    How: the small mock is 0.9 sure and right on the even items of pick, 0.55 sure and wrong on the odd ones; the
    large arm (the generate path, /v1/chat/completions) always answers the right letter.
    """
    order = {it["id"]: n for n, it in enumerate(SUITES["pick"]["items"])}

    def small_dist(menu, prompt):
        item = item_for(prompt)
        if item is None:
            return [("Hello", .5)]
        right = letter_of(menu, item, item["answer"])
        wrong = next(letter for letter in menu if letter not in (right, "X"))
        return [(right, .9), (wrong, .1)] if order[item["id"]] % 2 == 0 else [(right, .45), (wrong, .55)]

    def oracle(body):
        user = next(m["content"] for m in body["messages"] if m["role"] == "user")
        item = item_for(user)
        return letter_of(menu_of(user), item, item["answer"])

    STATE.dist_fn, STATE.chat_fn = small_dist, oracle
    ps = run_py(lp_args("e2e-small.jsonl", "--label", "small-mock", items=",".join(PICK_IDS)))
    pl = run_py(["--backend", "llamacpp", "--base-url", URL, "--suite", "pick", "--k", "1", "--wait", "5", "--label",
                 "large-mock", "--out", out("e2e-large.jsonl")])
    check(ps.returncode == 0 and pl.returncode == 0, f"exits {ps.returncode} {pl.returncode}: {pl.stderr[-300:]}")
    small = rows(out("e2e-small.jsonl"))
    small_cost = sum((r["prompt_eval_count"] * 0.1 + r["eval_count"] * 0.4) / 1e6 for r in small) / len(small)
    rep = simulate([out("e2e-small.jsonl"), out("e2e-large.jsonl")],
                   ["small-mock|pick|none|logprob", "large-mock|pick|none|plain"], "--thresholds", "0,0.6,1",
                   "--price", "small-mock|pick|none|logprob=0.1,0.4", "--cost", "large-mock|pick|none|plain=0.002")
    r0, r6 = row(rep, 0.0), row(rep, 0.6)
    check(rep["units"] == 30 and close(rep["alone"][0]["accuracy"], 0.5) and close(rep["alone"][1]["accuracy"], 1.0),
          f"alone {rep['alone']}")
    check(close(r0["accuracy"], 0.5) and close(r6["accuracy"], 1.0) and close(r6["escalation_rate"], 0.5)
          and close(r6["cost_per_decision"], small_cost + 0.5 * 0.002, 1e-9) and close(r6["random_same_rate"], 0.75),
          f"rows {r0} {r6}")
    check(rep["operating_point"]["threshold"] == 0.6 and close(rep["signal_quality"]["auroc"], 1.0)
          and rep["unpriced"] == [], f"op {rep['operating_point']} q {rep['signal_quality']}")
    code, _ = cascade_main(["calibrate", out("e2e-small.jsonl"), "--arm", "small-mock|pick|none|logprob", "--out",
                            out("e2e-cal.json")])
    cal = load_json(out("e2e-cal.json"))
    STATE.reset()
    STATE.dist_fn = small_dist
    pc = run_py(lp_args("e2e-cal.jsonl", "--label", "small-mock", "--calibration", out("e2e-cal.json")))
    rc = rows(out("e2e-cal.jsonl"))[0]
    check(code == 0 and pc.returncode == 0 and rc["logprob"]["calibration"]["temperature"] == cal["temperature"]
          and rc["chosen_key"] == rc["correct_key"], f"calibration round trip: {code} {pc.returncode} {pc.stderr[-200:]}")
    return (f"30 paired units: small 0.5, large 1.0; threshold 0.6: 1.0 at escalation 0.5 (random 0.75), AUROC 1.0; "
            f"fitted T {cal['temperature']} read back by run.py")


def c07_simulator_refusals():
    """Malformed chains, flags and inputs are refused with exit 2 (no input: exit 1), never simulated.

    Why: a chain across suites, a logprob signal on sampled records or a threshold outside [0, 1] would produce
    numbers that look valid and mean nothing.
    """
    small = write("c07-small.jsonl", [rec("small", PICK_IDS[0], s, "logprob", conf=0.9) for s in range(2)])
    large = write("c07-large.jsonl", [rec("large", PICK_IDS[0], s) for s in range(2)])
    other = write("c07-other.jsonl", [dict(rec("x", "HW01", 0), suite="pick-hard")])
    ok = ["small|pick|none|logprob", "large|pick|none|plain"]
    cases = [
        (["--chain", ok[0]], "at least two arms"),
        (["--chain", ok[0], "x|pick-hard|none|plain"], "one suite"),
        (["--chain", ok[0], "nobody|pick|none|plain"], "no records for arm"),
        (["--chain", ok[1], ok[1]], "no logprob confidence"),
        (["--chain"] + ok + ["--signal", "vote", "--calibration", f"{ok[0]}=x.json"], "logprob signal only"),
        (["--chain"] + ok + ["--calibration", f"{ok[1]}=x.json"], "not a non-final stage"),
        (["--chain"] + ok + ["--price", f"{ok[0]}=1"], "--price needs"),
        (["--chain"] + ok + ["--price", f"{ok[0]}=-1,2"], "--price needs"),
        (["--chain"] + ok + ["--price", f"{ok[0]}=nan,1"], "--price needs"),
        (["--chain"] + ok + ["--cost", f"{ok[0]}=x"], "--cost needs"),
        (["--chain"] + ok + ["--cost", "nobody"], "ARM=VALUE"),
        (["--chain"] + ok + ["--thresholds", "0:1:0"], "--thresholds"),
        (["--chain"] + ok + ["--thresholds", "a"], "--thresholds"),
        (["--chain"] + ok + ["--thresholds", "1.5"], "--thresholds"),
        (["--chain"] + ok + ["--thresholds", "0:1:0.0001"], "at most 1001"),
        (["--chain"] + ok + ["--signal", "vote", "--votes", "0"], "--votes must be"),
        (["--chain"] + ok + ["--signal", "vote", "--votes", "3"], "--votes must be"),
        (["--chain"] + ok + ["--target-gap", "2"], "--target-gap"),
        (["--chain", "a|b", ok[1]], "model|suite|condition|variant"),
    ]
    wrong = []
    for extra, needle in cases:
        p = run_py(["simulate", small, large, other] + extra + ["--json", out("c07.json"), "--csv", out("c07.csv")],
                   script="cascade.py")
        if p.returncode != 2 or needle not in p.stderr:
            wrong.append((extra, p.returncode, p.stderr[-160:]))
    p = run_py(["simulate", out("does-not-exist-*.jsonl"), "--chain"] + ok, script="cascade.py")
    check(p.returncode == 1, f"no input: exit {p.returncode}")
    p = run_py(["calibrate", large, "--arm", ok[1], "--out", out("c07-cal.json")], script="cascade.py")
    check(p.returncode == 2 and "no usable logprob" in p.stderr, f"calibrate on sampled records: {p.returncode}")
    check(not wrong, f"not refused as expected: {wrong[:3]}")
    check(not os.path.exists(out("c07.json")), "a refused simulation wrote its report")
    return f"{len(cases)} refusals (exit 2); no input: exit 1; calibrate on sampled records: exit 2"


def c08_answer_key_pairing_valid_mass_and_calibration_guards():
    """Units whose answer key differs between stages are dropped; --min-valid-mass escalates decisions whose letters
    held too little of the model's probability; a calibration file fitted on another model is refused; a file path
    with '=' is read whole.

    Why: two arms scored against different answer keys (a suite edited between runs) compare different questions
    even when the option order matches; a confidence renormalised from a sliver of probability is not a confident
    answer; a temperature fitted on one model means nothing for another (run.py refuses it too).

    How: 4 units; the small model is right and 0.9 sure on all; unit 2's large record has another answer key, unit 3's
    small record kept only 0.02 of the mass on the letters. With --min-valid-mass 0.05 unit 3 escalates to the large
    model (wrong), so at threshold 0.5: accuracy 2/3, escalation 1/3 over the 3 paired units.
    """
    ids = PICK_IDS[:4]
    small = [rec("small", i, 0, "logprob", conf=0.9) for i in ids]
    for r, vm in zip(small, (0.9, 0.9, 0.9, 0.02)):
        r["valid_mass_min"] = vm
    large = [rec("large", i, 0, chosen="wrong") for i in ids]
    large[2]["correct_key"] = next(o["key"] for o in ITEMS[ids[2]]["options"] if o["key"] != ITEMS[ids[2]]["answer"])
    paths = [write("c08-small.jsonl", small), write("c08-large.jsonl", large)]
    chain = ["small|pick|none|logprob", "large|pick|none|plain"]
    rep = simulate(paths, chain, "--thresholds", "0.5")
    check(rep["units"] == 3 and rep["dropped"] == {"unpaired": 0, "mismatched": 1}
          and close(row(rep, 0.5)["escalation_rate"], 0.0), f"answer-key pairing {rep['dropped']} {row(rep, 0.5)}")
    rep2 = simulate(paths, chain, "--thresholds", "0.5", "--min-valid-mass", "0.05")
    check(close(row(rep2, 0.5)["accuracy"], 2 / 3) and close(row(rep2, 0.5)["escalation_rate"], 1 / 3)
          and rep2["min_valid_mass"] == 0.05, f"min valid mass {row(rep2, 0.5)}")
    cal_dir = out("c08 dir=eq")
    os.makedirs(cal_dir, exist_ok=True)
    good, other = os.path.join(cal_dir, "good.json"), os.path.join(cal_dir, "other.json")
    with open(good, "w", encoding="utf-8") as f:
        json.dump({"temperature": 1.0, "model": "small"}, f)
    with open(other, "w", encoding="utf-8") as f:
        json.dump({"temperature": 1.0, "model": "another"}, f)
    for r in small:
        r["p_by_key"] = {r["correct_key"]: 0.9, "zzz": 0.1}
    paths[0] = write("c08-small.jsonl", small)
    rep3 = simulate(paths, chain, "--thresholds", "0.5", "--calibration", f"{chain[0]}={good}")
    check(rep3["calibration"] == {chain[0]: 1.0}, f"path with '=': {rep3['calibration']}")
    wrong = []
    for extra, needle in ((["--calibration", f"{chain[0]}={other}"], "fitted on 'another'"),
                          (["--min-valid-mass", "1.5"], "--min-valid-mass"),
                          (["--signal", "vote", "--min-valid-mass", "0.1"], "logprob signal only")):
        p = run_py(["simulate"] + paths + ["--chain"] + chain + extra + ["--json", out("c08.json"), "--csv",
                                                                         out("c08.csv")], script="cascade.py")
        if p.returncode != 2 or needle not in p.stderr:
            wrong.append((extra, p.returncode, p.stderr[-200:]))
    check(not wrong, f"not refused as expected: {wrong}")
    return ("answer-key mismatch dropped (3 of 4 units); valid mass 0.02 < 0.05 escalated (acc 0.667, esc 0.333); "
            "calibration for another model refused; a path with '=' read")


# ── unittest wiring ──────────────────────────────────────────────────────────

class CascadeTests(support.CaseTestCase):
    """The cascade simulator (see the module docs)."""

    cases = (c01_logprob_cascade_known_values,
             c02_vote_cascade_known_values,
             c03_pairing_duplicates_and_mismatches,
             c04_unusable_answers_always_escalate,
             c05_calibrate_known_temperature,
             c06_end_to_end_with_the_mock_server,
             c07_simulator_refusals,
             c08_answer_key_pairing_valid_mass_and_calibration_guards)

    def setUp(self):
        STATE.reset()


if __name__ == "__main__":
    unittest.main()
