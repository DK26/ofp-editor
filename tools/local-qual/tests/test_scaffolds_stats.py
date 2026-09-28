#!/usr/bin/env python3
"""Tests for the scaffold arms' analysis tools: scaffold_stats.py (the exact sign-flip test, Holm, the
pre-registered verdicts and vetoes, folded resumes, shared units, the arm filter, the SR3 hint-only veto)
and control_suite.py (the hint-only control suite).

The records are synthetic (``stats_rec`` builds them); d04 runs the hint-only control through run.py and
mock_reason.py. d07 uses the staged pick pool when LOCALQUAL_POOLS names its folder, else a pool-shaped copy
of pick-hard.

Run the whole suite from the repository root with ``python -m unittest discover -s tools/local-qual/tests``;
the module docs of support.py explain the case functions and the environment switches.
"""

import json
import unittest

import scaffold_support
import support
from scaffold_support import *  # noqa: F401,F403 - the shared fixtures the cases use by name

URL = None  # the mock's base URL while this module runs (set by setUpModule)


def setUpModule():
    global URL
    URL = scaffold_support.start("scaffolds-stats")


def tearDownModule():
    scaffold_support.finish()


# ── d: analysis tools ──────────────────────────────────────────────────────────

def d01_sign_flip_test_and_holm_known_values():
    """scaffold_stats' exact sign-flip p-values and Holm adjustments against hand computation.

    Why: the pre-registered decision rule must compute what the plan says.

    How: differences (k = 3) +1, +1, +1/3, 0, -1/3 scale to +3, +3, +1, 0, -1; S = 6 over the 16 equally likely sign
    patterns of (3, 3, 1, 1): sums >= 6 are (3,3,1,1)=8, (3,3,1,-1)=6, (3,3,-1,1)=6: p_better = 3/16, and every
    pattern but the all-positive one has S <= 6: p_worse = 15/16. Holm on {a: 0.01, b: 0.04, c: 0.03}: sorted
    0.01*3 = 0.03, 0.03*2 = 0.06, max(0.06, 0.04*1) = 0.06.
    """
    pb, pw = scaffold_stats.sign_flip_pvalues([1, 1, 1 / 3, 0, -1 / 3], 3)
    check(abs(pb - 3 / 16) < 1e-12 and abs(pw - 15 / 16) < 1e-12, f"{pb} {pw}")
    pb, pw = scaffold_stats.sign_flip_pvalues([1] * 10, 3)
    check(abs(pb - 1 / 1024) < 1e-15, f"ten wins {pb}")
    h = scaffold_stats.holm({"a": 0.01, "b": 0.04, "c": 0.03})
    check(abs(h["a"] - 0.03) < 1e-12 and abs(h["c"] - 0.06) < 1e-12 and abs(h["b"] - 0.06) < 1e-12, str(h))
    return "p_better 3/16 and 1/1024 exact; Holm 0.03 / 0.06 / 0.06"


def d02_stats_verdicts_end_to_end():
    """scaffold_stats reads run records, pairs units and gives winner / harmful / no_effect by the rules.

    Why: the plan's verdicts come from this code; a synthetic record set with a known structure must get them.

    How: 12 units, k = 3; plain is right only on the last two units (the last one a planted escape). Arm "good" is right
    everywhere: 10 units better, 2 tied, p_better = 1/1024, a winner. Arm "esc" is right everywhere except the escape:
    it gains on 10 units but loses the planted escape, so SR2 vetoes it (no_effect). Arm "bad" equals plain except one
    unit lost: p_worse = 1/2, no_effect. Then a separate set where plain is right everywhere and the arm wrong
    everywhere: p_worse = 1/2^12, harmful.
    """
    items = [it for it in SUITES["pick-hard"]["items"] if it["answer"] != it["escape"]["key"]][:11]
    items.append(next(it for it in SUITES["pick-hard"]["items"] if it["answer"] == it["escape"]["key"]))
    esc_item = items[-1]

    def rec(variant, it, s, right):
        wrong = it["options"][0]["key"] if it["answer"] != it["options"][0]["key"] else it["options"][1]["key"]
        return {"run_id": "t", "seed": 1, "model": "m", "suite": "pick-hard", "item_id": it["id"], "condition": "none",
                "variant": variant, "sample": s, "parse_ok": True, "correct_key": it["answer"],
                "chosen_key": it["answer"] if right else wrong, "latency_ms": 100.0, "prompt_eval_count": 10,
                "eval_count": 2}

    recs = []
    for i, it in enumerate(items):
        for s in range(3):
            recs.append(rec("plain", it, s, i >= 10))
            recs.append(rec("scaffold-good", it, s, True))
            recs.append(rec("scaffold-esc", it, s, it is not esc_item))
            recs.append(rec("scaffold-bad", it, s, i >= 11))
    suites = scaffold_stats.load_suites()
    rows_ = {r["arm"]: r for r in scaffold_stats.analyse(recs, suites)}
    good = rows_["scaffold-good"]
    check(good["verdict"] == "winner" and good["units_better"] == 10 and abs(good["p_better"] - 1 / 1024) < 1e-15
          and good["family_size"] == 3, str(good)[:300])
    check(rows_["scaffold-esc"]["verdict"] == "no_effect" and rows_["scaffold-esc"]["escape_recall_arm"] == 0
          and rows_["scaffold-esc"]["escape_recall_base"] == 1, str(rows_["scaffold-esc"])[:300])
    bad = rows_["scaffold-bad"]
    check(bad["units_worse"] == 1 and abs(bad["p_worse"] - 0.5) < 1e-12 and bad["verdict"] == "no_effect",
          str(bad)[:300])
    # A clearly harmful arm: plain right everywhere, arm wrong everywhere.
    recs2 = [rec("plain", it, s, True) for it in items for s in range(3)] + \
            [rec("scaffold-worse", it, s, False) for it in items for s in range(3)]
    r2 = scaffold_stats.analyse(recs2, suites)[0]
    check(r2["verdict"] == "harmful" and abs(r2["p_worse"] - 1 / 4096) < 1e-12, str(r2)[:200])
    return "winner, escape-loss veto (SR2) and harmful verdicts as the rules say; Holm family of 3"


def d03_control_suite_swaps_and_blanks():
    """control_suite.py keeps menus, cards and answers, blanks or swaps every request (never its own, always another
    category), and renames the suite.

    Why: the hint-only control (SR3) is only meaningful if the request carries no information about the answer.
    """
    ph = SUITES["pick-hard"]
    swap = control_suite.control(ph, "swap")
    by_id = {it["id"]: it for it in ph["items"]}
    check(swap["suite"] == "pick-hard-hint-swap" and len(swap["items"]) == len(ph["items"]), "name/count")
    for it in swap["items"]:
        src = by_id[it["control_request_from"]]
        orig = by_id[it["id"]]
        check(it["request"] == src["request"] and src["id"] != it["id"] and src["category"] != it["category"],
              f"{it['id']} swap")
        check(it["options"] == orig["options"] and it["answer"] == orig["answer"] and it["card"] == orig["card"],
              f"{it['id']} menu changed")
    blank = control_suite.control(ph, "blank")
    check(all(it["request"] == control_suite.BLANK_REQUEST for it in blank["items"]), "blank")
    path = write_suite("d03-swap.json", swap)
    p = run_py(lc_args("d03.jsonl", "--suite-file", path, "--scaffold", "diff", suite=None, items="HW01"))
    check(p.returncode == 0 and rows(out("d03.jsonl"))[-1]["suite"] == "pick-hard-hint-swap", p.stderr[-200:])
    return f"{len(swap['items'])} swapped requests from other categories; blank mode; runs through --suite-file"


def d04_hint_only_mock_stays_near_chance():
    """With the request swapped, the prompt-only mock model scores near chance in every arm (the tool itself adds no
    answer signal).

    Why: a smoke version of doc 59 T-L6 for the tooling: the mock model reads only the prompt, so any arm clearly above
    chance here would mean the arm's requests carry the answer.

    How: pick-hard swap control, k = 3 (90 decisions per arm); chance is about 1/8 on 7 options plus X; the bound is
    chance + 0.15 because 90 hashed choices are noisy.
    """
    ph = control_suite.control(SUITES["pick-hard"], "swap")
    path = write_suite("d04-swap.json", ph)
    accs = {}
    for arm, cond in (("plain", "none"), ("diff", "none"), ("rule", "cards"), ("subq", "none"), ("eliminate", "none"),
                      ("pairwise", "none"), ("prefill", "none")):
        extra = [] if arm == "plain" else ["--scaffold", arm]
        name = f"d04-{arm}.jsonl"
        STATE.reset()
        STATE.chat_fn = model_chat
        STATE.dist_fn = model_dist
        STATE.complete_fn = lambda prompt, body: max(menu_of(prompt), key=lambda L: _h(menu_of(prompt)[L]))
        p = run_py(lc_args(name, "--suite-file", path, "--condition", cond, *extra, suite=None, items=None, k=3))
        check(p.returncode == 0, f"{arm}: {p.stderr[-300:]}")
        recs = rows(out(name))
        accs[arm] = sum(r["correct"] for r in recs) / len(recs)
    check(all(a <= 0.125 + 0.15 for a in accs.values()), str(accs))
    return "hint-only accuracy per arm " + ", ".join(f"{k} {v:.3f}" for k, v in accs.items())


def stats_rec(variant, it, s, choice, condition="none", suite="pick-hard", **extra):
    """A minimal run.py Pick record for scaffold_stats: `choice` is "answer", "wrong" (a real option that is not the
    answer) or "escape" (X); extra fields (error, latency_ms, tokens, n_calls) override the defaults."""
    wrong = next(o["key"] for o in it["options"] if o["key"] != it["answer"])
    key = {"answer": it["answer"], "wrong": wrong, "escape": it["escape"]["key"]}[choice]
    letters = {L: o["key"] for L, o in zip("ABCDEFG", it["options"])}
    letters["X"] = it["escape"]["key"]
    r = {"run_id": "t", "seed": 1, "model": "m", "suite": suite, "item_id": it["id"], "condition": condition,
         "variant": variant, "sample": s, "parse_ok": True, "correct_key": it["answer"], "chosen_key": key,
         "letter_to_key": letters, "latency_ms": 100.0, "prompt_eval_count": 10, "eval_count": 2, "error": None}
    r.update(extra)
    return r


def stats_items():
    """d02's twelve pick-hard items: eleven with a real answer, then one planted escape."""
    items = [it for it in SUITES["pick-hard"]["items"] if it["answer"] != it["escape"]["key"]][:11]
    return items + [next(it for it in SUITES["pick-hard"]["items"] if it["answer"] == it["escape"]["key"])]


def d05_stats_fold_resumes_share_units_and_filter_arms():
    """scaffold_stats folds a resumed decision into one, computes every side figure over the paired units only, and
    compares only the scaffold arms.

    Why: (1) the plan chunks long runs with --resume, which appends the retry after the error record; counted as two
    samples, the unit no longer has k samples and silently leaves the paired test. (2) The SR2 veto compares false
    escapes; the rule arm runs on cards only while plain runs on none and cards, so a baseline rate pooled over both
    conditions is a different population and can wave a harmful arm through. (3) A stray non-scaffold variant in the
    input glob must neither join the Holm family nor get a verdict.

    How: (1) d02's "good" arm with an error record (3 model calls, 50 prompt tokens) before its HW01 sample-0 retry:
    still 12 units and p_better 1/1024, one folded record, and the failed attempt's cost counted in the decision's
    (model calls (35 x 2 + 2 + 3) / 36 = 2.08, prompt tokens (35 x 10 + 10 + 50) / 36 = 11.4). (2) plain chooses X on
    every real-answer item at none (false-escape rate 1) and a wrong real option at cards; the cards-only arm is right
    except on one item where it chooses X: against plain's cards units its false-escape rate 3/33 exceeds 0, so SR2
    vetoes it (a pooled baseline of 0.5 would have let it win); its latency ratio is 330 / 300 against the cards
    units, not against the pooled median 200. (3) A legacy "why" variant is skipped and the family has one arm.
    """
    items = stats_items()
    recs = []
    for i, it in enumerate(items):
        for s in range(3):
            recs.append(stats_rec("plain", it, s, "answer" if i >= 10 else "wrong"))
            if i == 0 and s == 0:
                recs.append(stats_rec("scaffold-good", it, s, "wrong", error="HTTP 500", parse_ok=False,
                                      chosen_key=None, prompt_eval_count=50, n_calls=3))
            recs.append(stats_rec("scaffold-good", it, s, "answer", n_calls=2))
    rep = {}
    good = scaffold_stats.analyse(recs, scaffold_stats.load_suites(), report=rep)[0]
    check(good["units"] == 12 and good["unequal_units"] == 0 and abs(good["p_better"] - 1 / 1024) < 1e-15
          and good["verdict"] == "winner" and rep["folded_records"] == 1, f"fold: {good} {rep}")
    check(good["mean_model_calls_arm"] == 2.08 and good["mean_prompt_tokens_arm"] == 11.4
          and good["mean_model_calls_base"] == 1.0, f"cost of the failed attempt: {good}")
    # (2) and (3)
    recs = []
    for i, it in enumerate(items):
        esc_item = it["answer"] == it["escape"]["key"]
        for s in range(3):
            recs.append(stats_rec("plain", it, s, "escape" if not esc_item else "answer", "none", latency_ms=100.0))
            recs.append(stats_rec("plain", it, s, "answer" if i >= 10 else "wrong", "cards", latency_ms=300.0))
            recs.append(stats_rec("scaffold-rule", it, s, "escape" if i == 3 else "answer", "cards", latency_ms=330.0))
            recs.append(stats_rec("why", it, s, "answer", "cards"))
    rep = {}
    rows_ = scaffold_stats.analyse(recs, scaffold_stats.load_suites(), report=rep)
    check([r["arm"] for r in rows_] == ["scaffold-rule"] and rep["skipped_variants"] == ["why"]
          and rows_[0]["family_size"] == 1, f"arm filter: {[r['arm'] for r in rows_]} {rep}")
    rule = rows_[0]
    check(rule["units"] == 12 and rule["units_better"] == 9 and rule["missing_units"] == 12
          and rule["holm_p_better"] < 0.05 and rule["mean_gain"] >= 0.05, f"rule arm test: {rule}")
    check(rule["false_escape_base"] == 0.0 and abs(rule["false_escape_arm"] - round(3 / 33, 4)) < 1e-12
          and rule["verdict"] == "no_effect", f"SR2 on shared units: {rule}")
    check(rule["latency_ratio"] == 1.1 and rule["latency_p50_base"] == 300.0, f"latency on shared units: {rule}")
    return ("resumed error folded (12 units, p 1/1024, its cost counted); SR2 and latency on the cards units only "
            "(false escapes 0.091 vs 0 -> no_effect; ratio 1.1); legacy why skipped, family of 1")


def d06_stats_sr3_hint_only_veto():
    """scaffold_stats applies SR3 from the hint-only control records and never pools them into the paired test.

    Why: the plan's winner rule includes SR3 (hint-only accuracy at most chance + 10 points and at most the baseline's
    + 10 points), and doc 59 T-L6 is the check that a scaffold does not choose by itself. Left to a manual step it can
    be skipped; pooled into the primary units it would dilute the test with answerless decisions.

    How: four arms right on every unit (winners by the paired test, Holm family of 4, p 4/1024). Control records on
    pick-hard-hint-swap (30 items, k = 1): plain right on 1; diff on 12 (0.4 > chance 0.125 + 0.1): SR3 fails;
    pairwise on 6 (0.2, under 0.225, but 0.167 above plain's 0.033): SR3 fails; subq on 3 (0.1): passes; eliminate has
    no control records: not_run, no veto. The control suite is passed to the analysis too, so a tool that pooled its
    records into the arms' units would show 42 units instead of 12.
    """
    items = stats_items()
    ctrl = control_suite.control(SUITES["pick-hard"], "swap")
    suites = scaffold_stats.load_suites()
    suites[ctrl["suite"]] = (ctrl, {it["id"]: it for it in ctrl["items"]}, "t")
    arms = ("scaffold-diff", "scaffold-pairwise", "scaffold-subq", "scaffold-eliminate")
    recs = []
    for i, it in enumerate(items):
        for s in range(3):
            recs.append(stats_rec("plain", it, s, "answer" if i >= 10 else "wrong"))
            recs += [stats_rec(a, it, s, "answer") for a in arms]
    right = {"plain": 1, "scaffold-diff": 12, "scaffold-pairwise": 6, "scaffold-subq": 3}
    for variant, n_right in right.items():
        for j, it in enumerate(ctrl["items"]):
            recs.append(stats_rec(variant, it, 0, "answer" if j < n_right else "wrong", suite=ctrl["suite"]))
    got = {r["arm"]: r for r in scaffold_stats.analyse(recs, suites)}
    check(all(got[a]["units"] == 12 for a in arms), f"control records pooled: {[got[a]['units'] for a in arms]}")
    check(got["scaffold-diff"]["sr3"] == "fail" and got["scaffold-diff"]["hint_acc_arm"] == 0.4
          and got["scaffold-diff"]["hint_chance"] == 0.125 and got["scaffold-diff"]["verdict"] == "no_effect",
          str(got["scaffold-diff"])[:400])
    check(got["scaffold-pairwise"]["sr3"] == "fail" and got["scaffold-pairwise"]["hint_acc_base"] == round(1 / 30, 4)
          and got["scaffold-pairwise"]["verdict"] == "no_effect", str(got["scaffold-pairwise"])[:400])
    check(got["scaffold-subq"]["sr3"] == "pass" and got["scaffold-subq"]["verdict"] == "winner",
          str(got["scaffold-subq"])[:400])
    check(got["scaffold-eliminate"]["sr3"] == "not_run" and got["scaffold-eliminate"]["verdict"] == "winner"
          and got["scaffold-eliminate"]["family_size"] == 4, str(got["scaffold-eliminate"])[:400])
    return ("SR3: diff 0.40 > chance + 0.1 and pairwise 0.20 > plain 0.03 + 0.1 vetoed; subq 0.10 passes; eliminate "
            "not run, no veto; control records never paired (12 units each)")


def d07_stats_command_line_end_to_end():
    """scaffold_stats.py as the plan runs it: one glob of a model's records (tuning arms, a stray variant, hint-only
    controls, a pool run) and --suite-file, written to --json.

    Why: the plan's analysis is this command line, and its input glob holds more than the paired arms: the hint-only
    files and possibly other variants. A pool run analysed without its suite file must be reported, not silently
    dropped (half of the Pick units would vanish from the test).

    How: pick-hard records as in d02 (plain right on 2 of 12 items, scaffold-diff right everywhere, one error record
    before a retry), a logprob variant, 30 hint-only control records where diff is right on 12, and 3 pool items for
    plain and diff. Without the pool's --suite-file: 12 units, a warning naming pick-pool (18 decisions), the logprob
    variant listed as skipped, one folded record, SR3 failed, verdict no_effect. With it: 15 units. The pool is the
    staged pick pool's tune half when LOCALQUAL_POOLS provides it, else its stand-in (pick_pool).
    """
    pool = pick_pool()
    items = stats_items()
    ctrl = control_suite.control(SUITES["pick-hard"], "swap")
    pool_items = pool["items"][:3]
    recs = []
    for i, it in enumerate(items):
        for s in range(3):
            recs.append(stats_rec("plain", it, s, "answer" if i >= 10 else "wrong"))
            if i == 1 and s == 2:
                recs.append(stats_rec("scaffold-diff", it, s, "wrong", error="HTTP 500", parse_ok=False, chosen_key=None))
            recs.append(stats_rec("scaffold-diff", it, s, "answer"))
            recs.append(stats_rec("logprob", it, s, "answer"))
    for j, it in enumerate(ctrl["items"]):
        recs.append(stats_rec("plain", it, 0, "answer" if j < 1 else "wrong", suite=ctrl["suite"]))
        recs.append(stats_rec("scaffold-diff", it, 0, "answer" if j < 12 else "wrong", suite=ctrl["suite"]))
    for it in pool_items:
        for s in range(3):
            recs.append(stats_rec("plain", it, s, "wrong", suite="pick-pool"))
            recs.append(stats_rec("scaffold-diff", it, s, "answer", suite="pick-pool"))
    path = out("d07.jsonl")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(json.dumps(r) + "\n" for r in recs))
    p = run_py([path, "--json", out("d07.json")], script="scaffold_stats.py")
    rep = _load(out("d07.json"))
    row = rep["rows"][0]
    check(p.returncode == 0 and len(rep["rows"]) == 1 and row["arm"] == "scaffold-diff", p.stderr[-300:])
    check(rep["skipped_variants"] == ["logprob"] and rep["folded_records"] == 1
          and rep["unscored_decisions"] == {"pick-pool": 18} and "pick-pool" in p.stderr, str(rep)[:400])
    check(row["units"] == 12 and row["sr3"] == "fail" and row["hint_acc_arm"] == 0.4 and row["verdict"] == "no_effect"
          and "sr3=fail" in p.stdout, str(row)[:400])
    pool_file = write_suite("d07-pool.json", pool)
    p = run_py([path, "--suite-file", pool_file, "--json", out("d07b.json")], script="scaffold_stats.py")
    rep = _load(out("d07b.json"))
    check(p.returncode == 0 and rep["rows"][0]["units"] == 15 and rep["unscored_decisions"] == {}, str(rep)[:300])
    return ("CLI: 12 units, logprob skipped, 1 folded record, pick-pool's 18 decisions reported unscored, SR3 failed "
            "(0.40) -> no_effect; with the pool's --suite-file 15 units")


# ── unittest wiring ──────────────────────────────────────────────────────────

class ScaffoldStatsTests(support.CaseTestCase):
    """The scaffold analysis tools (see the module docs)."""

    cases = (d01_sign_flip_test_and_holm_known_values,
             d02_stats_verdicts_end_to_end,
             d03_control_suite_swaps_and_blanks,
             d04_hint_only_mock_stays_near_chance,
             d05_stats_fold_resumes_share_units_and_filter_arms,
             d06_stats_sr3_hint_only_veto,
             d07_stats_command_line_end_to_end)

    def setUp(self):
        reset_mock()


if __name__ == "__main__":
    unittest.main()
