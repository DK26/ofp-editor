#!/usr/bin/env python3
"""Tests for the harness-uplift arms and their analysis: the open and labels Pick arms and their grading
(grade_open.py), Fill's schema modes, the repair call, and uplift.py's statistics and comparisons.

The arms run through run.py's paid path against mock_server.py, which answers each request from a script,
so the grading and scoring see known answers; uplift.py is checked against hand-computed values.

Every case runs run.py (or another tool script) as a child process against mock_server.py, in-process on
127.0.0.1: nothing is spent and no real endpoint is contacted. cloud_support.py holds the dummy keys, the
helpers and the final key sweep that fails the module if any key or key label reached a file or a console
transcript.

Run the whole suite from the repository root with ``python -m unittest discover -s tools/local-qual/tests``;
the module docs of support.py explain the case functions and the environment switches.
"""

import csv
import json
import unittest

import cloud_support
import support
from cloud_support import *  # noqa: F401,F403 - the shared fixtures the cases use by name

URL = None  # the mock's base URL while this module runs (set by setUpModule)


def setUpModule():
    global URL
    URL = cloud_support.start("cloud-grading")


def tearDownModule():
    cloud_support.finish()


# ── Open arms, Fill schema modes, repair (t14-t17) ─────────────────────────────

def t14_open_arm_grading_and_scoring():
    """The open Pick arm sends no menu and no schema; grade_open.py maps its free-form answers to option keys
    (exact, substring, unmapped), and score.py reports accuracy only once every answer is graded.

    Why: the open arm measures what the menu adds, so its accuracy must rest on explicit, auditable mappings;
    the judge sheet must not carry the request (the judge maps the answer alone).
    """
    answers = {"PW01": "HOLD", "PW02": "Use a CYCLE waypoint", "PW03": "get in",
               "PW04": "Transport unload (TR UNLOAD)", "PW05": "seek & destroy",
               "PT01": "West present or East not present"}
    import run as runmod
    suite, _ = runmod.load_suite("pick")
    by_request = {it["request"]: it["id"] for it in suite["items"]}

    def answer(body):
        text = user_text(body)
        req = text.split("\n\n")[0][len("Request: "):]
        return answers[by_request[req]]
    STATE.answer_fn = answer
    o = out("open.jsonl")
    items = ",".join(answers)
    p = run_tool(base(URL) + ["--suite", "pick", "--condition", "open", "--items", items, "--k", "1",
                              "--max-usd", "1", "--out", o])
    check(p.returncode == 0, f"open run exit {p.returncode}: {p.stderr[-300:]}")
    bodies = chat_bodies()
    check(all("response_format" not in b and "Options:" not in user_text(b) and b["max_tokens"] == 48
              for b in bodies), "open request shape")
    check(all(r["variant"] == "open" and r["condition"] == "none" for r in calls(rows(o))), "variant")
    # The labels arm lists names without letters or descriptions.
    STATE.requests.clear()
    p_l = run_tool(base(URL) + ["--suite", "pick", "--variant", "labels", "--items", "PW01", "--k", "1",
                                "--max-usd", "1", "--out", out("labels.jsonl")])
    lb = chat_bodies()[0]
    check(p_l.returncode == 0 and "Valid names: " in user_text(lb) and "A)" not in user_text(lb), "labels shape")
    # Without grades: no accuracy.
    ps = run_py("score.py", [o, "--open-grades", "--csv", out("open_nog.csv"), "--json", out("open_nog.json")])
    s0 = load_json(out("open_nog.json"))[0]
    check(s0["accuracy"] is None and s0["open_ungraded"] == 6, f"ungraded: {s0.get('accuracy')}")
    # Grade, judge the unmapped one, score.
    g = out("grades/open-grades.jsonl")
    pg = run_py("grade_open.py", [o, "--out", g, "--judge-sheet", out("judge-sheet.jsonl")])
    check(pg.returncode == 0, pg.stderr)
    grades = {r["grade_of"]["item_id"]: r for r in rows(g)}
    modes = {k: (v["mapped_key"], v["map_mode"]) for k, v in grades.items()}
    check(modes["PW01"] == ("hold", "exact") and modes["PW02"] == ("cycle", "substring")
          and modes["PW03"] == ("getin", "exact") and modes["PW04"] == ("trunload", "substring")
          and modes["PW05"] == ("sad", "exact") and modes["PT01"] == (None, "unmapped"), str(modes))
    sheet = rows(out("judge-sheet.jsonl"))
    pt01_request = next(it["request"] for it in suite["items"] if it["id"] == "PT01")
    check(len(sheet) == 1 and pt01_request not in json.dumps(sheet[0], ensure_ascii=False)
          and "request" not in sheet[0], "judge sheet must not carry the request")
    judge = dict(grade_of=sheet[0]["grade_of"], answer_sha=sheet[0]["answer_sha"], mapped_key="east_not_present",
                 map_mode="judge", grader="judge:mock")
    with open(out("grades/judge.jsonl"), "w", encoding="utf-8") as f:
        f.write(json.dumps(judge) + "\n")
    ps2 = run_py("score.py", [o, "--open-grades", g, out("grades/judge.jsonl"), "--csv", out("open.csv"),
                              "--json", out("open.json")])
    check(ps2.returncode == 0, ps2.stderr)
    s = load_json(out("open.json"))[0]
    check(abs(s["accuracy"] - 4 / 6) < 1e-3 and abs(s["judge_mapped_accuracy"] - 5 / 6) < 1e-3, str(s["accuracy"]))
    check(s["map_exact"] == 3 and s["map_substring"] == 2 and s["map_unmapped"] == 1, "map counts")
    row = next(csv.DictReader(read_text(out("open.csv")).splitlines()))
    check(row["variant"] == "open" and row["judge_mapped_accuracy"] == "0.8333", "csv")
    return (f"6 open answers: exact 3, substring 2 (incl. 'TR UNLOAD' over 'unload'), unmapped 1; alias accuracy "
            f"{s['accuracy']}, judge-mapped {s['judge_mapped_accuracy']}; without grades accuracy None")


def t15_open_alias_rules_unit():
    """grade_open's alias and escape rules map known phrasings to the expected keys (an option labelled None beats
    the escape phrase; ambiguous answers stay unmapped), and every Pick item has an open stem.

    Why: the mapping decides open-arm accuracy; each case is one a naive substring match gets wrong.
    """
    import grade_open as go
    import run as runmod
    sc, _ = runmod.load_sidecar()
    pick, _ = runmod.load_suite("pick")
    hard, _ = runmod.load_suite("pick-hard")
    items = {it["id"]: it for it in pick["items"] + hard["items"]}

    def m(item_id, ans):
        al, _ = go.item_aliases(items[item_id], sc)
        return go.map_answer(ans, al, items[item_id]["escape"]["key"], sc["escape_phrases"])[:2]
    cases = [
        ("PT01", "None", ("activation_none", "exact")),  # an option labelled None wins over the escape phrase
        ("PT01", "None of these fit", ("none_fit", "escape")),
        ("PT05", "None - the Type should be Lose", (None, "unmapped")),
        ("PR05", "Nothing fits: this is outside the editor", ("none_fit", "escape")),
        ("PA01", "AM07", ("am07", "exact")),
        ("PA01", "the dark night raid preset", ("am07", "substring")),
        ("PT03", "Countdown 60/90/120", ("countdown_60_90_120", "exact")),
        ("HK03", "Squad selection", ("squad_selection", "exact")),
        ("HM03", "spectator mode", ("spectator", "substring")),
        ("HW01", "UNLOAD", ("unload", "exact")),
        ("HW01", "unload or get out", (None, "unmapped")),
        ("PW05", "", (None, "unmapped")),
    ]
    bad = [(i, a, m(i, a), want) for i, a, want in cases if m(i, a) != want]
    check(not bad, str(bad))
    dropped = {i: go.item_aliases(items[i], sc)[1] for i in items}
    shared = {i: d for i, d in dropped.items() if d}
    for item_id, item in items.items():  # every stem resolves
        runmod.open_stem(item, sc)
    return f"{len(cases)} mapping rules hold; all {len(items)} items have a stem; shared aliases dropped: {shared}"


def t16_fill_schema_modes_and_parse_failures():
    """--schema-mode none, text and strict send no schema, the schema as text only, and both; score.py counts the
    resulting parse failures per variant.

    Why: the harness-uplift comparison needs each rung to remove exactly one mechanism and leave the rest of
    the request unchanged.
    """
    def answer(body):
        text = user_text(body)
        if "response_format" in body:
            return json.dumps(mock_server.value_for(body["response_format"]["json_schema"]["schema"]))
        if "Lomovo" in text:
            return "Sure! The task is populate-area in Lomovo."
        return ('```json\n{"task": "other", "place": "", "side": "unspecified", "size": "unspecified", '
                '"time_of_day": "unspecified"}\n```')
    STATE.answer_fn = answer
    res = {}
    for mode in ("none", "text", "strict"):
        STATE.requests.clear()
        o = out(f"fill_{mode}.jsonl")
        p = run_tool(base(URL) + ["--suite", "fill", "--schema-mode", mode, "--items", "F01,F02", "--k", "1",
                                  "--max-usd", "1", "--out", o])
        check(p.returncode == 0, f"{mode}: exit {p.returncode} {p.stderr[-200:]}")
        b = chat_bodies()
        res[mode] = (("response_format" in b[0]), ("JSON schema:" in user_text(b[0])),
                     user_text(b[0]).endswith("Answer with JSON only."), calls(rows(o))[0]["variant"])
    check(res["none"] == (False, False, True, "noschema"), str(res["none"]))
    check(res["text"] == (False, True, False, "schematext"), str(res["text"]))
    check(res["strict"] == (True, True, False, "plain"), str(res["strict"]))
    ps = run_py("score.py", [out("fill_none.jsonl"), out("fill_text.jsonl"), out("fill_strict.jsonl"), "--csv",
                             out("fill.csv"), "--json", out("fill.json")])
    check(ps.returncode == 0, ps.stderr)
    by_var = {s["variant"]: s for s in load_json(out("fill.json"))}
    check(by_var["noschema"]["parse_rate"] == 0.5 and by_var["plain"]["parse_rate"] == 1.0, "parse rates")
    return (f"none: no response_format, no schema text; text: schema text only; strict: both. parse_rate "
            f"noschema {by_var['noschema']['parse_rate']}, schematext {by_var['schematext']['parse_rate']}, "
            f"strict {by_var['plain']['parse_rate']}; field accuracy noschema {by_var['noschema']['field_accuracy']}")


def t17_fill_repair_one_call_summed_cost():
    """--repair sends at most one repair call after a failed code check, shows the model its rejected answer and
    the check's message, and records both calls' costs under one decision.

    Why: a repair loop must stay bounded, and its cost must count against the budget exactly once per call,
    on --resume too.
    """
    good = {"task": "populate-area", "place": "Lomovo", "side": "east", "size": "large", "time_of_day": "unspecified"}
    bad = dict(good, place="Moscow")
    STATE.answer_fn = lambda body: json.dumps(good if len(body["messages"]) > 2 else bad)
    o = out("repair.jsonl")
    p = run_tool(base(URL) + ["--suite", "fill", "--repair", "--items", "F01", "--k", "1", "--max-usd", "1",
                              "--out", o])
    check(p.returncode == 0, f"exit {p.returncode} {p.stderr[-300:]}")
    r = calls(rows(o))[0]
    check(r["variant"] == "repair" and r["repair_used"] and
          r["first_check_failed"] == "place: quoted text not found in the request", str(r.get("first_check_failed")))
    b = chat_bodies()
    check(len(b) == 2 and b[1]["messages"][2]["role"] == "assistant" and
          "place: quoted text not found in the request" in b[1]["messages"][3]["content"], "repair request")
    check(len(r["call_costs"]) == 2 and abs(sum(r["call_costs"].values()) - r["cost_usd"]) < 1e-12, "cost sum")
    from budget import Budget, read_ledger_rows
    check(abs(Budget(1, 1, 1, rows=read_ledger_rows(o)).spent() - r["cost_usd"]) < 1e-12, "ledger")
    ps = run_py("score.py", [o, "--csv", out("rep.csv"), "--json", out("rep.json")])
    s = load_json(out("rep.json"))[0]
    check(s["repair_rate"] == 1.0 and s["all_fields_correct_rate"] == 1.0, str(s))
    # Pick noschema: a letter outside the menu is invalid; the repair asks for a menu letter.
    STATE.reset()
    STATE.answer_fn = lambda body: '{"choice": "A"}' if len(body["messages"]) > 2 else '{"choice": "Z"}'
    o2 = out("pick_noschema_repair.jsonl")
    p2 = run_tool(base(URL) + ["--suite", "pick", "--schema-mode", "none", "--repair", "--items", "PW01", "--k",
                               "1", "--max-usd", "1", "--out", o2])
    r2 = calls(rows(o2))[0]
    check(p2.returncode == 0 and r2["variant"] == "noschema-repair" and r2["first"]["chosen_key"] is None
          and r2["chosen_letter"] == "A" and r2["valid_choice"], "pick repair")
    check(all("response_format" not in b for b in chat_bodies()), "noschema sent a schema")
    return (f"fill: first answer failed '{r['first_check_failed']}', one repair call fixed it, cost "
            f"{r['cost_usd']:.8f} over 2 call ids, repair_rate 1.0; pick noschema: 'Z' repaired to 'A'")


# ── uplift.py (t22, t23, t35) and the open arms without cards (t39) ────────────

def t22_uplift_statistics_known_values():
    """Wilson, unbiased pass^k and exact McNemar against hand-computed values."""
    import uplift
    lo, hi = uplift.wilson(8, 10)
    check(abs(lo - 0.4902) < 1e-4 and abs(hi - 0.9433) < 1e-4, f"wilson {lo} {hi}")
    check(uplift.wilson(0, 0) == (None, None), "wilson n=0")
    check(abs(uplift.pass_hat_k([(3, 2)], 1) - 2 / 3) < 1e-12 and uplift.pass_hat_k([(3, 2)], 3) == 0
          and uplift.pass_hat_k([(5, 4)], 3) == 0.4 and uplift.pass_hat_k([(2, 2)], 3) is None, "pass^k")
    check(abs(uplift.mcnemar_exact(8, 2) - 112 / 1024) < 1e-12 and uplift.mcnemar_exact(0, 0) == 1.0, "mcnemar")
    a = uplift.bootstrap([1, 0, 1, 1], lambda s: sum(s) / len(s))
    b = uplift.bootstrap([1, 0, 1, 1], lambda s: sum(s) / len(s))
    check(a == b, "bootstrap not deterministic")
    return (f"Wilson 8/10 = ({lo:.4f}, {hi:.4f}); pass^1(3,2) = 0.667, pass^3(5,4) = 0.4; McNemar(8,2) p = "
            f"{112 / 1024:.6f}; bootstrap repeatable with the fixed seed")


def t23_uplift_end_to_end_synthetic():
    """Paired deltas, CPCD, policies, gap closure H, non-inferiority and Pareto on a hand-built scenario."""
    import run as runmod
    suite, _ = runmod.load_suite("pick")
    items = suite["items"][:15]  # PW01-05, PT01-05 (engine vocabulary), PM01-05 (code-owned)
    engine = [it for it in items if it["category"] in ("waypoint", "trigger")]
    code = [it for it in items if it not in engine]
    check(len(engine) == 10 and len(code) == 5, "item split")

    def pattern(arm, it):
        e = it in engine
        idx = (engine.index(it) if e else code.index(it))
        if arm == "A":  # cheap bare
            return (1, 1, 1) if e and idx < 5 else (0, 0, 0)
        if arm == "B":  # cheap full
            return (1, 1, 0) if e and idx == 9 else (1, 1, 1)
        return (1, 1, 1) if (e and idx < 8) or (not e and idx == 0) else (0, 0, 0)  # C frontier bare
    arms = {"A": ("cheap", "noschema", 0.0001), "B": ("cheap", "plain", 0.0001), "C": ("frontier", "noschema", 0.005)}
    path = out("uplift_in.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for arm, (model, variant, cost) in arms.items():
            for it in items:
                wrong = next(o["key"] for o in it["options"] if o["key"] != it["answer"])
                for s, ok in enumerate(pattern(arm, it)):
                    f.write(json.dumps({"run_id": "r", "seed": s, "model": model, "suite": "pick", "item_id": it["id"],
                                        "condition": "none", "variant": variant, "sample": s, "parse_ok": True,
                                        "chosen_key": it["answer"] if ok else wrong, "correct_key": it["answer"],
                                        "cost_usd": cost, "latency_ms": 100.0,
                                        "prompt_eval_count": 200 if variant == "plain" else 150}) + "\n")
    p = run_py("uplift.py", [path, "--gap", "cheap|pick|none|noschema", "cheap|pick|none|plain",
                             "frontier|pick|none|noschema", "--json", out("uplift.json"), "--arms-csv",
                             out("uplift_arms.csv"), "--pairs-csv", out("uplift_pairs.csv")])
    check(p.returncode == 0, p.stderr[-500:])
    rep = load_json(out("uplift.json"))
    arm = {(a["model"], a["variant"]): a for a in rep["arms"]}
    b = arm[("cheap", "plain")]
    check(abs(b["pass_k"] - 14 / 15) < 1e-4 and abs(b["pass1"] - (14 + 2 / 3) / 15) < 1e-4, f"pass {b['pass_k']}")
    pol = b["policies"]
    check(pol["single"]["cpcd_usd"] == 0.0001 and pol["vote3"]["decision_acc"] == 1.0 and
          abs(pol["vote3"]["cpcd_usd"] - 0.0003) < 1e-12 and abs(pol["adaptive"]["cpcd_usd"] - 0.0002) < 1e-12,
          str(pol))
    a = arm[("cheap", "noschema")]["policies"]["single"]
    check(abs(a["false_admit_rate"] - 2 / 3) < 1e-4 and abs(a["decision_acc"] - 1 / 3) < 1e-4, str(a))
    c = arm[("frontier", "noschema")]["policies"]["single"]
    check(abs(c["cpcd_usd"] - 0.075 / 9) < 1e-8, str(c))
    pairs = {(x["bare"], x["items_group"]): x for x in rep["pairs"]}
    pa = pairs[("cheap|pick|none|noschema", "all")]
    check(abs(pa["delta"] - 10 / 15) < 1e-4 and pa["mcnemar_fixed"] == 10 and pa["mcnemar_broken"] == 0 and
          abs(pa["mcnemar_p"] - 2 / 1024) < 1e-5 and pa["token_overhead"] == round(200 / 150, 3), str(pa))
    pe = pairs[("cheap|pick|none|noschema", "engine")]
    check(pe["items"] == 10 and pe["delta"] == 0.5 and abs(pe["mcnemar_p"] - 0.0625) < 1e-9, str(pe))
    pc = pairs[("cheap|pick|none|noschema", "code_owned")]
    check(pc["items"] == 5 and pc["delta"] == 1.0, str(pc))
    g = rep["gap"][0]
    check(g["items_group"] == "engine" and g["items"] == 10 and abs(g["H"] - 5 / 3) < 1e-4 and g["non_inferior"]
          and g["cpcd_ratio_frontier_over_cheap"] == 62.5, str(g))
    front = {(x["arm"], x["policy"]): x["pareto"] for x in rep["pareto"]}
    check(front[("cheap|pick|none|plain", "single")] and not front[("cheap|pick|none|noschema", "single")]
          and not front[("frontier|pick|none|noschema", "single")], str(front))
    return (f"cheap+harness vs cheap bare: delta {pa['delta']} (McNemar p {pa['mcnemar_p']}), engine items "
            f"{pe['delta']}, code-owned {pc['delta']}; H {g['H']} on engine items, non-inferior to the frontier arm; "
            f"CPCD single/adaptive/vote3 {pol['single']['cpcd_usd']}/{pol['adaptive']['cpcd_usd']}/"
            f"{pol['vote3']['cpcd_usd']}; frontier/cheap CPCD ratio {g['cpcd_ratio_frontier_over_cheap']}")


def t35_uplift_refuses_partially_graded_open_arm():
    """uplift.py, like score.py, reports no accuracy for an open arm with ungraded answers (no silent subset)."""
    import run as runmod
    suite, _ = runmod.load_suite("pick")
    items = suite["items"][:4]
    path = out("uplift_open.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for variant in ("open", "plain"):
            for it in items:
                f.write(json.dumps({"run_id": "r", "seed": 1, "model": "m", "suite": "pick", "item_id": it["id"],
                                    "condition": "none", "variant": variant, "sample": 0, "parse_ok": True,
                                    "open_answer": it["answer"] if variant == "open" else None,
                                    "chosen_key": it["answer"], "correct_key": it["answer"]}) + "\n")
    g = out("grades/partial.jsonl")
    import grade_open as go
    with open(g, "w", encoding="utf-8") as f:
        it = items[0]
        f.write(json.dumps({"grade_of": {"run_id": "r", "model": "m", "suite": "pick", "item_id": it["id"],
                                         "condition": "none", "variant": "open", "sample": 0},
                            "answer_sha": go.answer_sha(it["answer"]), "mapped_key": it["answer"],
                            "map_mode": "exact"}) + "\n")
    p = run_py("uplift.py", [path, "--open-grades", g, "--json", out("uplift_open.json"), "--arms-csv",
                             out("uplift_open_arms.csv"), "--pairs-csv", out("uplift_open_pairs.csv")])
    rep = load_json(out("uplift_open.json"))
    arm = {a["variant"]: a for a in rep["arms"]}
    check(p.returncode == 0 and arm["open"]["acc_call"] is None and not rep["pairs"] and "no grade" in p.stderr,
          f"open acc {arm['open']['acc_call']}, {len(rep['pairs'])} pairs")
    return "1 of 4 open answers graded: open arm accuracy None, no open-vs-menu pair, warning printed"


def t39_open_arms_refuse_reference_cards():
    """An open or labels arm never carries the reference card: the cards name the answer's option in most items
    (43 of 60 when this test was written), so "open + cards" would be a menu by the back door."""
    import grade_open as go
    import prompts
    sc, _ = prompts.load_sidecar()
    named = 0
    for suite in ("pick", "pick-hard"):
        for it in prompts.load_suite(suite)[0]["items"]:
            al, _ = go.item_aliases(it, sc)
            named += any(f" {a} " in f" {go.normalise(it.get('card') or '')} " for a in al.get(it["answer"], ()))
    common = ["--backend", "ollama", "--model", "m", "--suite", "pick", "--items", "PW01", "--dry-run"]
    p1 = run_tool(common + ["--variant", "open", "--condition", "cards"])
    p2 = run_tool(common + ["--variant", "labels", "--condition", "cards"])
    p3 = run_tool(common + ["--condition", "open"])
    check(refused(p1, "card") and refused(p2, "card") and p3.returncode == 0,
          f"open+cards exit {p1.returncode}, labels+cards exit {p2.returncode}, open exit {p3.returncode}")
    check("[REFERENCE CARD]" not in p3.stdout, "the open arm carried a card")
    return f"cards name the answer in {named} of 60 Pick items; open and labels with cards refused (exit 2)"


# ── unittest wiring ──────────────────────────────────────────────────────────

class UpliftArmTests(support.CaseTestCase):
    """The uplift arms, their grading and uplift.py (see the module docs)."""

    cases = (t14_open_arm_grading_and_scoring,
             t15_open_alias_rules_unit,
             t16_fill_schema_modes_and_parse_failures,
             t17_fill_repair_one_call_summed_cost,
             t22_uplift_statistics_known_values,
             t23_uplift_end_to_end_synthetic,
             t35_uplift_refuses_partially_graded_open_arm,
             t39_open_arms_refuse_reference_cards)

    def setUp(self):
        STATE.reset()


if __name__ == "__main__":
    unittest.main()
