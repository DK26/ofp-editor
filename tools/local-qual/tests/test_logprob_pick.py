#!/usr/bin/env python3
"""Tests for --pick-mode logprob (logprob_pick.py): its flags and refusals, the request bodies, and the letter
distribution read from llama-server's /completion (token variants, the five response shapes, missing and
escape letters, rotations and debiasing, the calibration file).

Runs run.py against mock_llama.py (a mock llama-server, in-process on 127.0.0.1) whose next-token lists are
scripted per test, so every probability is known by hand. No model runs.

Run the whole suite from the repository root with ``python -m unittest discover -s tools/local-qual/tests``;
the module docs of support.py explain the case functions and the environment switches.
"""

import json
import math
import os
import unittest

import logprob_support
import support
from logprob_support import *  # noqa: F401,F403 - the shared fixtures the cases use by name

URL = None  # the mock's base URL while this module runs (set by setUpModule)


def setUpModule():
    global URL
    URL = logprob_support.start("logprob-pick")


def tearDownModule():
    logprob_support.finish()


# ── Logprob mode: flags and refusals (l01-l02) ─────────────────────────────────

def l01_dry_run_prints_both_bodies_without_the_network():
    """--dry-run prints the /apply-template and /completion bodies of the first order and sends nothing.

    Why: the owner must be able to see exactly what a logprob run sends before a server is up.
    """
    p = run_py(lp_args("dry.jsonl", "--dry-run", "--n-probs", "40"))
    check(p.returncode == 0, f"exit {p.returncode}: {p.stderr[-300:]}")
    check(not STATE.requests, f"{len(STATE.requests)} requests during a dry run")
    text = p.stdout
    body = json.loads(text.split("POST /completion", 1)[1])
    tmpl = json.loads(text.split("POST /apply-template", 1)[1].split("POST /completion", 1)[0])
    check(body["n_predict"] == 1 and body["n_probs"] == 40 and body["temperature"] == 0.0
          and body["prompt"].endswith(PREFIX) and body["seed"] == sample_seed("PW01", 0),
          f"completion body {body}")
    check(tmpl["chat_template_kwargs"] == {"enable_thinking": False} and len(tmpl["messages"]) == 2
          and tmpl["response_format"]["json_schema"]["schema"]["properties"]["choice"]["enum"][-1] == "X"
          and "model" not in tmpl and "temperature" not in tmpl, f"template body {tmpl}")
    check(not os.path.exists(out("dry.jsonl")), "the dry run created its output file")
    return "0 requests; /completion: n_predict 1, n_probs 40, temperature 0, prompt ends with the answer prefix"


def l02_refusals_before_any_request():
    """Every flag combination the mode cannot honour is refused with exit 2 before any request.

    Why: a silently ignored flag (a sampler pin, --why, a calibration fitted on another model) would make a run look
    like something it is not; a malformed calibration file must never reach the confidence fields.
    """
    cal_dir = out("cal")
    os.makedirs(cal_dir, exist_ok=True)

    def cal(name, text):
        path = os.path.join(cal_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    base = ["--base-url", URL, "--items", "PW01", "--k", "1", "--out", out("refused.jsonl")]
    cases = [
        (["--backend", "ollama", "--model", "m", "--pick-mode", "logprob"], "needs --backend llamacpp"),
        (["--backend", "openai", "--model", "m", "--pick-mode", "logprob"], "needs --backend llamacpp"),
        (["--backend", "llamacpp", "--pick-mode", "logprob", "--suite", "fill"], "Pick suites only"),
        (["--backend", "llamacpp", "--pick-mode", "logprob", "--variant", "open"], "cannot be combined"),
        (["--backend", "llamacpp", "--pick-mode", "logprob", "--variant", "labels"], "cannot be combined"),
        (["--backend", "llamacpp", "--pick-mode", "logprob", "--variant", "noschema"], "cannot be combined"),
        (["--backend", "llamacpp", "--pick-mode", "logprob", "--schema-mode", "none"], "cannot be combined"),
        (["--backend", "llamacpp", "--pick-mode", "logprob", "--why"], "cannot be combined"),
        (["--backend", "llamacpp", "--pick-mode", "logprob", "--repair"], "cannot be combined"),
        (["--backend", "llamacpp", "--permute", "2"], "--permute applies to --pick-mode logprob only"),
        (["--backend", "llamacpp", "--n-probs", "30"], "--n-probs applies to --pick-mode logprob only"),
        (["--backend", "llamacpp", "--calibration", "x.json"], "--calibration applies to --pick-mode logprob only"),
        (["--backend", "llamacpp", "--pick-mode", "logprob", "--permute", "0"], "--permute must be 1-7"),
        (["--backend", "llamacpp", "--pick-mode", "logprob", "--permute", "8"], "--permute must be 1-7"),
        (["--backend", "llamacpp", "--pick-mode", "logprob", "--n-probs", "19"], "--n-probs must be 20-200"),
        (["--backend", "llamacpp", "--pick-mode", "logprob", "--n-probs", "201"], "--n-probs must be 20-200"),
        (["--backend", "llamacpp", "--pick-mode", "logprob", "--temperature", "0.5"], "do(es) not apply"),
        (["--backend", "llamacpp", "--pick-mode", "logprob", "--num-predict", "5"], "do(es) not apply"),
        (["--backend", "llamacpp", "--pick-mode", "logprob", "--top-k", "20"], "do(es) not apply"),
    ]
    bad_files = {"zero": '{"temperature": 0}', "negative": '{"temperature": -1}', "huge": '{"temperature": 25}',
                 "string": '{"temperature": "2"}', "bool": '{"temperature": true}', "nan": '{"temperature": NaN}',
                 "inf": '{"temperature": Infinity}', "missing": '{"model": "m"}', "list": '[2.0]',
                 "not-json": 'temperature=2', "method": '{"method": "platt", "temperature": 2}',
                 "model-type": '{"temperature": 2, "model": 7}'}
    for name, text in bad_files.items():
        cases.append((["--backend", "llamacpp", "--pick-mode", "logprob", "--calibration",
                       cal(name + ".json", text)], "calibration"))
    wrong = []
    for extra, needle in cases:
        p = run_py(base + ([] if "--suite" in extra else ["--suite", "pick"]) + extra)
        if p.returncode != 2 or needle not in p.stderr:
            wrong.append((extra, p.returncode, p.stderr[-200:]))
    check(not wrong, f"not refused as expected: {wrong[:3]}")
    check(not STATE.requests, f"{len(STATE.requests)} requests reached the mock")
    check(not os.path.exists(out("refused.jsonl")), "a refused run created its output file")
    return f"{len(cases)} refusals (exit 2, message names the problem), 0 requests"


# ── Logprob mode: the distribution (l03-l09) ───────────────────────────────────

def l03_happy_path_request_shape_and_known_distribution():
    """PW01 with a known next-token list: the requests, the renormalised distribution and the record fields.

    Why: the core claim of the mode is p(option) = mass(letter) / valid mass; every number here is computed by hand.

    How: the mock gives hold 0.45, sentry 0.18, none_fit/move/guard 0.09 each (spread 70/20/10 over "L", " L" and
    'L"') plus 0.10 of non-letter tokens; cycle and sad get nothing. Renormalised: hold 0.5, sentry 0.2, the rest 0.1.
    """
    STATE.dist_fn = weights_dist(lambda it, k: PW01_W.get(k, 0))
    p = run_py(lp_args("happy.jsonl", k=2))
    check(p.returncode == 0, f"exit {p.returncode}: {p.stderr[-400:]}")
    rs = rows(out("happy.jsonl"))
    check(len(rs) == 2, f"{len(rs)} records")
    r = rs[0]
    order = [o["key"] for o in permute_options(ITEMS["PW01"], 0)]  # sentry move sad hold guard cycle
    check(r["variant"] == "logprob" and r["pick_mode"] == "logprob" and r["parse_mode"] == "logprob"
          and r["chosen_key"] == "hold" and r["correct"] is True and r["chosen_letter"] == "D"
          and r["options_order"] == order and r["seed"] == sample_seed("PW01", 0) and r["temperature"] == 0.0
          and r["num_predict"] == 1 and r["think_sent"] is True and r["raw"] == "D", f"record fields {r}")
    check(all(close(r["p_by_key"][k], v) for k, v in PW01_P.items()), f"p_by_key {r['p_by_key']}")
    check(close(r["confidence"], 0.5) and close(r["p_margin"], 0.3) and close(r["p_entropy"], 1.3592367)
          and close(r["valid_mass_min"], 0.9), "confidence, margin, entropy or valid mass")
    o = r["logprob"]["orders"][0]
    check(o["missing"] == ["C", "F"] and o["variants"]["D"] == ["D", " D", 'D"'] and close(o["total_mass"], 1.0)
          and o["shape"] == "native" and o["n_returned"] == 32 and o["listed"] == 32 and o["bad_entries"] == 0
          and o["floor"] == 0.0 and o["missing_mass_max"] == 0.0 and r["logprob"]["completion_calls"] == 1,
          f"order detail {o}")
    # The first render is the run's boundary check (item 0, order 0), then one per decision.
    tmpl = [q["body"] for q in STATE.paths("/apply-template") if "Options:" in json.dumps(q["body"])]
    comp = completions()
    check(len(comp) == 2 and len(tmpl) == 3 and tmpl[0] == tmpl[1], f"{len(comp)} completions, {len(tmpl)} renders")
    for t, c in zip(tmpl[1:], comp):
        check(t["chat_template_kwargs"] == {"enable_thinking": False}, "enable_thinking not sent")
        check(c["prompt"] == render(t["messages"], t["chat_template_kwargs"]) + PREFIX,
              "the completion prompt is not the rendered template plus the answer prefix")
        check(c["n_predict"] == 1 and c["n_probs"] == 32 and c["temperature"] == 0.0 and c["cache_prompt"] is True
              and not ({"top_k", "top_p", "min_p", "grammar", "json_schema"} & set(c)), f"completion body {c}")
    check(t["messages"][0]["content"] == SYSTEM["pick"], "the system prompt differs from the generate mode's")
    check(rs[1]["options_order"] != order and rs[1]["chosen_key"] == "hold", "sample 1 did not reorder or changed")
    s = run_py([out("happy.jsonl"), "--csv", out("happy.csv"), "--json", out("happy.json")], script="score.py")
    summ = load_json(out("happy.json"))
    check(s.returncode == 0 and len(summ) == 1 and summ[0]["variant"] == "logprob" and summ[0]["accuracy"] == 1.0
          and summ[0]["parse_rate"] == 1.0, f"score.py: {summ}")
    return ("hold 0.5, sentry 0.2, others 0.1, cycle/sad missing (C, F); prompt = template + prefix; score.py "
            "accuracy 1.0 on variant logprob")


def l04_tokenisation_variants_known_values():
    """Letter variants add up; continuations, letters outside the menu and a quote inside the string do not count.

    Why: tokenisers spell one letter several ways; dropping a variant understates that letter, and counting "AB" or
    '"A' as A would credit an answer the model did not give.
    """
    entries = [("A", .30), (" A", .10), ('A"', .05), ('A"}', .05), ("▁B", .10), ("ĠC", .05), ("b", .05),
               ("AB", .10), ("A1", .05), ('"A', .05), ("X", .02), (' x"', .01), ("Al", .03), ("", .01), ("\n", .03)]
    d = lp.letter_distribution(entries, ["A", "B", "C", "X"])
    want = {"A": .50, "B": .15, "C": .05, "X": .03}
    check(all(close(d["letter_mass"][k], v) for k, v in want.items()) and close(d["valid_mass"], .73),
          f"mass {d['letter_mass']} valid {d['valid_mass']}")
    check(close(d["dist"]["A"], .50 / .73) and close(d["dist"]["X"], .03 / .73), f"dist {d['dist']}")
    check(d["variants"]["A"] == ["A", " A", 'A"', 'A"}'] and d["missing"] == [], f"variants {d['variants']}")
    # A prefix that stops before the opening quote: the token must bring the quote itself.
    d2 = lp.letter_distribution(entries, ["A", "B", "C", "X"], opens_string=False)
    check(close(d2["letter_mass"]["A"], .05) and close(d2["valid_mass"], .05), f"quote-less prefix {d2}")
    # A tab next to the letter is not a letter (a raw tab inside a JSON string fails run.py's parse; see l13).
    cases = {("D", "ABC"): None, ("  B", "ABX"): "B", ('B "', "AB"): "B", ("B.", "AB"): None, ("Ａ", "A"): None,
             ("x", "AX"): "X", ("\t▁A", "A"): None, (" ▁A", "A"): "A"}
    got = {t: lp.token_letter(t, list(v)) for (t, v) in cases}
    check(all(lp.token_letter(t, list(v)) == want_ for (t, v), want_ in cases.items()), f"token_letter {got}")
    return "A = 0.30+0.10+0.05+0.05, B = ▁B + b, X = X + ' x\"'; AB, A1, Al, '\"A', D and a full-width A rejected"


def l05_response_shapes_read_alike():
    """The five response shapes (native, post-sampling, pre-2025, OpenAI, OpenAI legacy) give the same distribution.

    Why: llama-server has changed the field names across builds; a parser that reads only one shape would record
    'no probabilities' against a working server.
    """
    STATE.dist_fn = weights_dist(lambda it, k: PW01_W.get(k, 0))
    seen = {}
    for shape in ("native", "native-post", "native-old", "openai", "openai-legacy"):
        STATE.shape = shape
        p = run_py(lp_args(f"shape-{shape}.jsonl"))
        check(p.returncode == 0, f"{shape}: exit {p.returncode}: {p.stderr[-300:]}")
        r = rows(out(f"shape-{shape}.jsonl"))[0]
        check(r["logprob"]["orders"][0]["shape"] == shape, f"{shape} read as {r['logprob']['orders'][0]['shape']}")
        check(all(close(r["p_by_key"][k], v, 1e-9) for k, v in PW01_P.items()), f"{shape}: {r['p_by_key']}")
        seen[shape] = r["chosen_key"]
    # A token sent only as bytes (an empty or cut text) is rebuilt from them.
    entries = lp.candidates({"completion_probabilities": [{"top_logprobs": [
        {"id": 1, "token": "", "bytes": [65], "logprob": math.log(0.4)},
        {"id": 2, "token": "�", "bytes": [66, 34], "logprob": math.log(0.3)}]}]}, 32)[0]
    check([t for t, _ in entries] == ["A", 'B"'], f"bytes fallback {entries}")
    return f"all five shapes -> hold 0.5 ({', '.join(seen)}); bytes-only tokens rebuilt"


def l06_missing_letters_and_no_valid_letter():
    """Letters outside the top N get 0 and are listed; a reply with no menu letter at all is a wrong answer, not an
    error.

    Why: renormalising over what was listed must be visible (missing letters, floor, valid mass), and a model that
    puts no mass on the menu must neither crash the run nor count as a server error.

    How: 25 filler tokens of 0.03 push move (0.005) and X out of the top 20; hold 0.2 and sentry 0.04 remain.
    """
    def dist(menu, prompt):
        item = item_for(prompt)
        if item is None:
            return [("Hello", .5)]
        return ([(letter_of(menu, item, "hold"), .2), (letter_of(menu, item, "sentry"), .04),
                 (letter_of(menu, item, "move"), .005)] + [(f"w{i}", .03) for i in range(25)])

    STATE.dist_fn = dist
    p = run_py(lp_args("missing.jsonl", "--n-probs", "20"))
    check(p.returncode == 0, f"exit {p.returncode}: {p.stderr[-300:]}")
    r = rows(out("missing.jsonl"))[0]
    o = r["logprob"]["orders"][0]
    check(close(r["p_by_key"]["hold"], .2 / .24) and close(r["p_by_key"]["sentry"], .04 / .24)
          and r["p_by_key"]["move"] == 0.0 and r["p_by_key"]["none_fit"] == 0.0, f"p_by_key {r['p_by_key']}")
    check(o["n_returned"] == 20 and close(o["valid_mass"], .24) and close(o["floor"], .03)
          and sorted(o["missing"]) == ["B", "C", "E", "F", "X"], f"order {o['missing']} {o['valid_mass']}")
    STATE.reset()
    STATE.dist_fn = lambda menu, prompt: [("Hello", .5), (" world", .3)]
    p = run_py(lp_args("novalid.jsonl"))
    r = rows(out("novalid.jsonl"))[0]
    check(p.returncode == 0 and r["error"] is None and r["parse_ok"] is False and r["parse_mode"] == "no_valid_letter"
          and r["chosen_key"] is None and r["correct"] is False and "confidence" not in r
          and "no menu letter" in p.stdout, f"exit {p.returncode}, record {r}")
    s = run_py([out("novalid.jsonl"), "--csv", out("nv.csv"), "--json", out("nv.json")], script="score.py")
    summ = load_json(out("nv.json"))[0]
    check(s.returncode == 0 and summ["accuracy"] == 0.0 and summ["errors"] == 0, f"score {summ}")
    return ("top 20: hold 0.8333, sentry 0.1667, B C E F X missing, floor 0.03, valid mass 0.24; no menu letter: "
            "parse_mode no_valid_letter, wrong, not an error")


def l07_escape_and_letters_outside_the_menu():
    """X always maps to the escape key; letters beyond the menu (F, G on a 5-option menu, Y) are never counted.

    Why: the escape is a real answer (doc 21 §3.2) and must be readable at X whatever the menu length; mass on a
    letter the menu does not have is not an answer.
    """
    STATE.dist_fn = weights_dist(lambda it, k: 8 if k == "none_fit" else 1)
    p = run_py(lp_args("escape.jsonl", items="PR05"))
    r = rows(out("escape.jsonl"))[0]
    check(p.returncode == 0 and r["chosen_letter"] == "X" and r["chosen_key"] == "none_fit" and r["correct"] is True,
          f"escape item: {r.get('chosen_letter')} {r.get('chosen_key')}")
    it = ITEMS["PW02"]
    other = next(o["key"] for o in permute_options(it, 0) if o["key"] != it["answer"])

    def dist(menu, prompt):
        item = item_for(prompt)
        if item is None:
            return [("Hello", .5)]
        return [("F", .3), ("G", .2), ("Y", .1), (letter_of(menu, item, item["answer"]), .2),
                (letter_of(menu, item, other), .1)]

    STATE.reset()
    STATE.dist_fn = dist
    p = run_py(lp_args("outside.jsonl", items="PW02"))
    r = rows(out("outside.jsonl"))[0]
    o = r["logprob"]["orders"][0]
    check(p.returncode == 0 and r["chosen_key"] == it["answer"] and close(r["confidence"], .2 / .3)
          and list(o["letter_mass"]) == ["A", "B", "C", "D", "E", "X"] and close(o["valid_mass"], .3),
          f"5-option menu: {r['chosen_key']} p {r.get('confidence')} letters {list(o['letter_mass'])}")
    return "escape item -> X = none_fit (correct); F 0.3, G 0.2, Y 0.1 ignored on a 5-option menu (p answer 0.6667)"


def l08_permutation_bookkeeping_and_debiasing():
    """--permute N sends N cyclic rotations (escape fixed at X), averages per key, and cancels a pure position bias.

    Why: averaging per letter instead of per key, or rotating the escape, would silently corrupt the distribution;
    the known values prove the bookkeeping.

    How: the mock's letter weight is w(key) + 3 on letter A, with w = 2 for the answer, 1 for the six others and 0.5
    for the escape (Z = 11.5). One order picks whatever sits at A (4 > 2). Over the 7 rotations each key sits at A
    once: p(answer) = (2 + 3/7) / 11.5 = 0.21118, p(other) = (1 + 3/7) / 11.5 = 0.12422, p(X) = 0.5 / 11.5.
    """
    dist = weights_dist(lambda it, k: 2 if k == it["answer"] else (0.5 if k == it["escape"]["key"] else 1),
                        letter_share=1.0, variants=(("{L}", 1.0),), filler=[], bias={"A": 3})
    STATE.dist_fn = dist
    p1 = run_py(lp_args("perm1.jsonl", suite="pick-hard", items="HW01", k=3))
    r1 = rows(out("perm1.jsonl"))
    STATE.reset()
    STATE.dist_fn = dist
    p7 = run_py(lp_args("perm7.jsonl", "--permute", "7", suite="pick-hard", items="HW01", k=3))
    r7 = rows(out("perm7.jsonl"))
    check(p1.returncode == 0 and p7.returncode == 0, f"exits {p1.returncode} {p7.returncode}: {p7.stderr[-300:]}")
    check([r["correct"] for r in r1] == [True, False, False], f"permute 1: {[r['chosen_key'] for r in r1]}")
    it = ITEMS["HW01"]
    for s, r in enumerate(r7):
        base = [o["key"] for o in permute_options(it, s)]
        check(r["variant"] == "logprob-perm7" and r["options_order"] == base and r["correct"] is True
              and r["logprob"]["orders_used"] == 7, f"sample {s}: {r['variant']} {r['chosen_key']}")
        for j, o in enumerate(r["logprob"]["orders"]):
            check(o["options_order"] == base[j:] + base[:j] and o["letter_to_key"]["X"] == "none_fit"
                  and [o["letter_to_key"][c] for c in "ABCDEFG"] == o["options_order"], f"order {j} bookkeeping")
        want = {k: ((2 + 3 / 7) if k == it["answer"] else (1 + 3 / 7)) / 11.5 for k in base}
        want["none_fit"] = 0.5 / 11.5
        check(all(close(r["p_by_key"][k], v) for k, v in want.items()), f"sample {s} p_by_key {r['p_by_key']}")
        check(r["chosen_letter"] == "ABCDEFG"[base.index(it["answer"])], "chosen letter not in order-0 lettering")
    # What the mock saw: 7 menus per decision, each a rotation of the base order, the escape last.
    comp = completions()
    check(len(comp) == 21, f"{len(comp)} completion calls for 3 decisions x 7 orders")
    keys = key_by_line(it)
    for n, c in enumerate(comp[:7]):
        menu = menu_of(c["prompt"])
        base = [o["key"] for o in permute_options(it, 0)]
        check([keys[menu[x]] for x in "ABCDEFG"] == base[n:] + base[:n] and keys[menu["X"]] == "none_fit",
              f"mock menu {n}")
    STATE.reset()
    STATE.dist_fn = dist
    p5 = run_py(lp_args("perm5.jsonl", "--permute", "7", items="PW02"))
    r5 = rows(out("perm5.jsonl"))[0]
    check(p5.returncode == 0 and r5["logprob"]["orders_used"] == 5 and len(completions()) == 5,
          f"5-option item with --permute 7: {r5['logprob']['orders_used']} orders, {len(completions())} calls")
    return ("permute 1 correct on samples [T, F, F] (bias to A); permute 7: 7 rotations each, X fixed, p(answer) "
            "0.21118, others 0.12422, X 0.04348, all correct; a 5-option item uses 5 orders")


def l09_calibration_file_applied():
    """--calibration T=2 rescales the confidence as p^(1/T) and leaves the chosen option alone; a file fitted on
    another model is refused.

    Why: calibration must only change how sure the record says the model was, never what it chose, and a temperature
    fitted on one model is meaningless for another.

    How: from hold 0.5, sentry 0.2, three at 0.1: sqrt weights 0.70711, 0.44721, 0.31623 x 3 (sum 2.10300) give
    hold 0.33624, sentry 0.21265, the rest 0.15037.
    """
    path = out("cal-t2.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"method": "temperature", "temperature": 2.0, "model": LABEL}, f)
    STATE.dist_fn = weights_dist(lambda it, k: PW01_W.get(k, 0))
    p = run_py(lp_args("cal.jsonl", "--calibration", path))
    check(p.returncode == 0, f"exit {p.returncode}: {p.stderr[-300:]}")
    r = rows(out("cal.jsonl"))[0]
    want = {"hold": .336237, "sentry": .212655, "none_fit": .15037, "move": .15037, "guard": .15037}
    check(all(close(r["p_by_key_cal"][k], v, 2e-6) for k, v in want.items()) and close(r["confidence"], .336237, 2e-6)
          and close(r["confidence_raw"], .5) and r["chosen_key"] == "hold", f"calibrated {r['p_by_key_cal']}")
    c = r["logprob"]["calibration"]
    check(c["temperature"] == 2.0 and c["file"] == "cal-t2.json" and len(c["sha"]) == 16, f"calibration detail {c}")
    with open(out("cal-other.json"), "w", encoding="utf-8") as f:
        json.dump({"temperature": 2.0, "model": "another-model"}, f)
    STATE.reset()
    p = run_py(lp_args("cal-other.jsonl", "--calibration", out("cal-other.json")))
    check(p.returncode == 2 and "fitted on 'another-model'" in p.stderr and not STATE.paths("/completion"),
          f"model mismatch: exit {p.returncode}, {len(STATE.paths('/completion'))} completions")
    return "T 2: hold 0.5 -> 0.33624, choice unchanged, file and sha recorded; a file for another model: exit 2, 0 calls"


# ── unittest wiring ──────────────────────────────────────────────────────────

class LogprobPickTests(support.CaseTestCase):
    """The logprob Pick mode's requests and distributions (see the module docs)."""

    cases = (l01_dry_run_prints_both_bodies_without_the_network,
             l02_refusals_before_any_request,
             l03_happy_path_request_shape_and_known_distribution,
             l04_tokenisation_variants_known_values,
             l05_response_shapes_read_alike,
             l06_missing_letters_and_no_valid_letter,
             l07_escape_and_letters_outside_the_menu,
             l08_permutation_bookkeeping_and_debiasing,
             l09_calibration_file_applied)

    def setUp(self):
        STATE.reset()


if __name__ == "__main__":
    unittest.main()
