#!/usr/bin/env python3
"""Tests for what the scaffold arms compute and send (doc 59): the diff and rule texts against known values,
the bounded why, eliminate and pairwise over letter probabilities, subq's statements and rule table, the
prefill channels, quote-first's schema and verbatim check, refusals, records and per-call ledgers, --resume,
--suite-file with --split, a failed call, and the Ollama path.

Runs against mock_reason.py (in-process on 127.0.0.1). c12 uses the staged pick pool when LOCALQUAL_POOLS
names its folder, else a pool-shaped copy of pick-hard (scaffold_support.pick_pool).

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
    URL = scaffold_support.start("scaffolds-function")


def tearDownModule():
    scaffold_support.finish()


# ── c: function ────────────────────────────────────────────────────────────────

def c01_diff_known_values():
    """The diff algorithm on a hand-computed synthetic menu and on HT03.

    Why: the documented algorithm (nearest neighbour by SequenceMatcher ratio, one-token runs widened by one token of
    context) must produce exactly the lines a reader predicts.

    How: a = "moves at once; crew stays", b = "moves at once; crew leaves", c = "stays forever". a~b share 4 of 5
    tokens (ratio 0.8); c~a share "stays" (ratio 2/7), c~b nothing, so the pairs are {a, b} and {a, c}. a vs b: the
    runs "stays" / "leaves" widen to "crew stays" / "crew leaves"; a vs c: a has "moves at once; crew", c has
    "forever", widened to "stays forever".
    """
    v = {"id": "T", "request": "r", "options": [{"key": "a", "label": "Ay", "desc": "moves at once; crew stays"},
                                               {"key": "b", "label": "Bee", "desc": "moves at once; crew leaves"},
                                               {"key": "c", "label": "Cee", "desc": "stays forever"}],
         "escape": {"key": "none_fit", "label": "None of these fit"}}
    lines = sc.diff_lines(v, v["options"])
    want = ['- A) Ay vs B) Bee: only A has "crew stays"; only B has "crew leaves".',
            '- A) Ay vs C) Cee: only A has "moves at once; crew"; only C has "stays forever".']
    check(lines == want, f"synthetic lines {lines}")
    ht = ITEMS["HT03"]
    block = sc.diff_block(sc.blind(ht), permute_options(ht, 0))
    check('- A) End #1 and End #2 vs D) Both End #1: only A has "End #2"; only D has "End #1".' in block, block)
    return "synthetic menu lines exact; HT03's End #1 / End #2 contrast rendered"


def c02_rule_sentence_known_values():
    """The rule selector on a synthetic card (IDF arithmetic), on HT03 and on HM04's documented failure.

    Why: the selection must follow the documented score exactly, including the known case where it picks the lure's
    sentence (HM04), which the experiment is meant to measure rather than hide.

    How: card "Alpha beta gamma. Beta delta. Epsilon zeta." with request "beta zeta": df(beta) = 2, df(zeta) = 1, N = 3,
    so the scores are ln(1 + 3/2) = 0.916, 0.916 and ln(1 + 3) = 1.386: the third sentence wins.
    """
    import math
    v = {"id": "T", "request": "beta zeta", "card": "Alpha beta gamma. Beta delta. Epsilon zeta.",
         "options": [{"key": "a", "label": "Alpha", "desc": "x"}], "escape": {"key": "none_fit", "label": "n"}}
    s, d = sc.select_rule_sentence(v)
    check(s == "Epsilon zeta." and abs(d["scores"][0] - math.log(2.5)) < 1e-6 and abs(d["score"] - math.log(4)) < 1e-6,
          f"synthetic: {s} {d}")
    v2 = dict(v, request="nothing shared")
    s2, d2 = sc.select_rule_sentence(v2)
    check(d2.get("fallback") == "no_overlap" and s2 == "Alpha beta gamma.", f"no-overlap fallback: {s2} {d2}")
    s3, d3 = sc.select_rule_sentence(dict(v, card=None))
    check(s3 is None and d3["fallback"] == "no_card", "no card")
    s4, _ = sc.select_rule_sentence(sc.blind(ITEMS["HT03"]))
    check(s4.startswith("Standing Orders, trigger types: End #n ends the mission"), s4)
    s5, _ = sc.select_rule_sentence(sc.blind(ITEMS["HM04"]))
    check(s5.startswith("Key parameters: Respawn point"), s5)
    return "IDF arithmetic exact (0.916 / 0.916 / 1.386); HT03 picks the End #n rule; HM04 the documented lure sentence"


def c03_why_arm_bounds_both_ends():
    """--scaffold why asks for a 40-160 character reason first and records it; the output cap is the why cap.

    Why: doc 59 S3 and its finding 5: the legacy --why bounds only the upper end; a bounded arm needs both, with the
    reason first in property and required order so it can influence the letter.
    """
    STATE.chat_fn = lambda body: json.dumps({"why": "The group's own riflemen get out while the driver stays aboard.",
                                             "choice": "A"})
    p = run_py(lc_args("c03.jsonl", "--scaffold", "why"))
    check(p.returncode == 0, p.stderr[-400:])
    body = [b for path, b in posts("/v1/chat/completions")][-1]
    schema = body["response_format"]["json_schema"]["schema"]
    check(list(schema["properties"]) == ["why", "choice"] and schema["required"] == ["why", "choice"], str(schema))
    check(schema["properties"]["why"] == {"type": "string", "minLength": 40, "maxLength": 160}, str(schema))
    check(body["max_tokens"] == 200 and body["messages"][1]["content"].endswith(sc.REPLY_WHY), "cap or reply line")
    r = rows(out("c03.jsonl"))[-1]
    check(r["variant"] == "scaffold-why" and r["why"].startswith("The group's own") and r["n_calls"] == 1, str(r)[:300])
    return "schema why{40..160} then choice; max_tokens 200; why recorded; variant scaffold-why"


def c04_eliminate_keeps_top_k_and_never_masks_x():
    """eliminate keeps the top-k real options by letter probability, always keeps X, re-asks in a fresh seeded order,
    and maps the final letter back to the full menu.

    Why: doc 59 S5's rules (keep the top two or three; never mask X), and score.py must read the same lettering as the
    plain arm.

    How: the dist gives X the highest probability and the real options decreasing probabilities by menu letter
    (A 0.30, B 0.15, C 0.10, rest 0.02); the final call must show exactly A's, B's and C's labels plus X.
    """
    probs = {"X": 0.35, "A": 0.30, "B": 0.15, "C": 0.10, "D": 0.02, "E": 0.02, "F": 0.02, "G": 0.02}
    STATE.dist_fn = lambda menu, prompt: [(letter, probs[letter]) for letter in menu]
    it = ITEMS["HW01"]
    opts = permute_options(it, 0)
    want = {opts[0]["key"], opts[1]["key"], opts[2]["key"]}
    STATE.chat_fn = lambda body: json.dumps({"choice": "B"})
    p = run_py(lc_args("c04.jsonl", "--scaffold", "eliminate"))
    check(p.returncode == 0, p.stderr[-400:])
    final = [b for path, b in posts("/v1/chat/completions")][-1]
    menu = menu_of(final["messages"][1]["content"])
    labels = {o["label"]: o["key"] for o in it["options"]}
    shown = {labels[t.split(":")[0]] for letter, t in menu.items() if letter != "X"}
    check(shown == want and "X" in menu and len(menu) == 4, f"final menu {menu}")
    r = rows(out("c04.jsonl"))[-1]
    fo = sc.seeded_order(sc.blind(it), [k for k in [o["key"] for o in opts] if k in want], "elim", 0)
    check(r["chosen_key"] == fo[1]["key"], f"chosen {r['chosen_key']} want {fo[1]['key']}")
    check(r["chosen_letter"] == next(L for L, k in r["letter_to_key"].items() if k == r["chosen_key"]), "letter map")
    led = r["scaffold"]
    check([c["phase"] for c in led["calls"]] == ["score", "final"] and led["kept"] == [o["key"] for o in opts[:3]],
          str(led)[:300])
    check(r["prompt_eval_count"] == sum(c["prompt_tokens"] for c in led["calls"]) and
          r["eval_count"] == sum(c["completion_tokens"] for c in led["calls"]), "token sums")
    p2 = run_py(lc_args("c04b.jsonl", "--scaffold", "eliminate", "--scaffold-keep", "2"))
    r2 = rows(out("c04b.jsonl"))[-1]
    check(p2.returncode == 0 and r2["variant"] == "scaffold-eliminate-k2" and len(r2["scaffold"]["kept"]) == 2, "k2")
    return "top-3 real options kept with X although X led; fresh seeded order; letters mapped back; k=2 variant"


def c05_eliminate_fallback_without_letters():
    """A scoring pass with no menu letter among the listed tokens keeps the first k of the seeded order and says so.

    Why: an unusable distribution must not crash or silently drop the decision; the fallback is recorded.
    """
    STATE.dist_fn = lambda menu, prompt: [("Hello", 0.7), ("\n", 0.3)]
    p = run_py(lc_args("c05.jsonl", "--scaffold", "eliminate"))
    check(p.returncode == 0, p.stderr[-400:])
    r = rows(out("c05.jsonl"))[-1]
    opts = permute_options(ITEMS["HW01"], 0)
    check(r["scaffold"].get("fallback") == "no_valid_letter" and r["scaffold"]["kept"] == [o["key"] for o in opts[:3]],
          str(r["scaffold"])[:300])
    return "fallback no_valid_letter; kept the first 3 of the seeded order"


def c06_pairwise_round_robin_and_aggregation():
    """pairwise asks every pair of the top 3 in both orders (6 calls) and aggregates by code; unit cases by hand.

    Why: doc 59 S6: both orders cancel a first-position preference; the escape wins only by majority; ties go to the
    first-pass probability.
    """
    probs = {"A": 0.40, "B": 0.30, "C": 0.20, "D": 0.05, "E": 0.02, "F": 0.02, "G": 0.01, "X": 0.0}
    STATE.dist_fn = lambda menu, prompt: [(letter, probs[letter]) for letter in menu]
    it = ITEMS["HW01"]
    opts = permute_options(it, 0)
    fav = opts[2]["label"]  # the third-ranked option wins every pair it is in

    def chat(body):
        menu = menu_of(user_of(body))
        for letter, text in menu.items():
            if text.startswith(fav + ":"):
                return json.dumps({"choice": letter})
        return json.dumps({"choice": "A"})

    STATE.chat_fn = chat
    p = run_py(lc_args("c06.jsonl", "--scaffold", "pairwise"))
    check(p.returncode == 0, p.stderr[-400:])
    r = rows(out("c06.jsonl"))[-1]
    calls = [c for c in r["scaffold"]["calls"] if c["phase"] == "pair"]
    orders = [tuple(c["options_order"]) for c in calls]
    top = [o["key"] for o in opts[:3]]
    want = [(top[0], top[1]), (top[1], top[0]), (top[0], top[2]), (top[2], top[0]), (top[1], top[2]),
            (top[2], top[1])]
    check(orders == want, f"pair orders {orders}")
    check(r["chosen_key"] == top[2] and r["scaffold"]["pairwise"]["wins"][top[2]] == 4, str(r["scaffold"]["pairwise"]))
    # Unit cases of the aggregation rule.
    esc = "none_fit"
    k, d = sc.aggregate_pairwise(["a", "b"], [esc, esc, "a"], esc, {"a": 0.5, "b": 0.4})
    check(k == esc and d["rule"] == "escape_majority", "escape majority")
    k, d = sc.aggregate_pairwise(["a", "b"], ["a", "b"], esc, {"a": 0.4, "b": 0.5})
    check(k == "b", "tie to the first-pass probability")
    k, d = sc.aggregate_pairwise(["a", "b"], [None, None], esc, {"a": 0.4, "b": 0.5})
    check(k == "a" and d["rule"] == "fallback_first_pass", "all invalid")
    k, _ = sc.aggregate_pairwise(["a", "b"], [esc, "a"], esc, {"a": 0.4, "b": 0.5})
    check(k == "a", "an escape half is not a majority")
    return "6 pair calls in both orders; the third-ranked favourite won 4 of 4 of its calls; 4 rule cases by hand"


def c07_subq_statements_and_rule_table():
    """subq turns option clauses into shared statements and applies the rule table; one call when code decides,
    two when it ties.

    Why: the table (any "no" eliminates; a unique top decides; a tie asks one final Pick over the tied options only)
    must hold exactly, and the final menu must never show an eliminated option.
    """
    opts = permute_options(ITEMS["HW01"], 0)
    st, own = sc.subq_statements(opts)
    shared = [s for s, t in st if t == "moves on at once"]
    check(len(shared) == 1 and sorted(own[shared[0]]) == ["load", "unload"], f"shared clause {own}")
    ids = [s for s, _ in st]
    keys = [o["key"] for o in opts]
    ans = {s: "no" for s in ids}
    for s in ids:
        if "unload" in own[s]:
            ans[s] = "yes"
    for s in ids:
        if own[s] == ["load"]:
            ans[s] = "unclear"
    (kind, value), d = sc.aggregate_subq(ans, st, own, keys)
    check(kind == "key" and value == "unload" and d["rule"] == "unique_top", f"unique top {kind} {value} {d}")
    (kind, _), d = sc.aggregate_subq({s: "no" for s in ids}, st, own, keys)
    check(kind == "escape" and d["rule"] == "no_survivor", "no survivor")
    (kind, value), d = sc.aggregate_subq({s: "unclear" for s in ids}, st, own, keys)
    check(kind == "final" and sorted(value) == sorted(keys) and d["rule"] == "no_yes_final_pick", "no yes")
    (kind, _), d = sc.aggregate_subq(dict(ans, **{ids[0]: "maybe"}), st, own, keys)
    check(kind == "none" and d["rule"] == "unparsed", "unparsed")
    # End to end: a unique top decides in one call; a tie adds one final Pick over the tied options only.
    STATE.chat_fn = lambda body: (json.dumps(ans) if "s1:" in user_of(body) else json.dumps({"choice": "A"}))
    p = run_py(lc_args("c07a.jsonl", "--scaffold", "subq"))
    r = rows(out("c07a.jsonl"))[-1]
    check(p.returncode == 0 and r["n_calls"] == 1 and r["chosen_key"] == "unload" and r["correct"], str(r)[:300])
    # One "yes" each for HOLD ("stays at the spot and never finishes") and MOVE ("goes to the spot"), every other
    # statement "unclear": no option is eliminated and the top (one yes) is tied between HOLD and MOVE.
    text_of = dict(st)
    tie = {s: ("yes" if text_of[s] in ("stays at the spot and never finishes", "goes to the spot") else "unclear")
           for s in ids}
    STATE.chat_fn = lambda body: (json.dumps(tie) if "s1:" in user_of(body) else json.dumps({"choice": "B"}))
    p = run_py(lc_args("c07b.jsonl", "--scaffold", "subq"))
    r = rows(out("c07b.jsonl"))[-1]
    final = [b for path, b in posts("/v1/chat/completions")][-1]
    menu = menu_of(final["messages"][1]["content"])
    check(p.returncode == 0 and r["n_calls"] == 2 and r["scaffold"]["decided_by"] == "final_pick", str(r)[:300])
    check({t.split(":")[0] for letter, t in menu.items() if letter != "X"} == {"HOLD", "MOVE"} and "X" in menu,
          f"final menu {menu}")
    chats = [b for path, b in posts("/v1/chat/completions")]
    check(chats[-2]["messages"][0]["content"] == sc.SUBQ_SYSTEM and final["messages"][0]["content"] == SYSTEM["pick"],
          "system prompts: the statements call has its own, the final Pick the plain one")
    return ("shared clause dedup; 4 rule-table cases; unique top = 1 call; a tie = 2 calls over the tied options + X; "
            "statement call has its own system prompt")


def c08_prefill_content_and_think_channels():
    """prefill sends /apply-template then one /completion whose prompt is the rendered prompt plus the skeleton plus
    the answer prefix, under a menu-letter grammar; the think channel fills the empty think block; a template without
    one is refused before any completion.

    Why: the documented template handling, and no response_format on /completion (it would demand a fresh "{").
    """
    STATE.complete_fn = lambda prompt, body: "C"
    p = run_py(lc_args("c08a.jsonl", "--scaffold", "prefill", "--top-k", "20", "--min-p", "0"))
    check(p.returncode == 0, p.stderr[-400:])
    it = ITEMS["HW01"]
    opts = permute_options(it, 0)
    skel = sc.prefill_skeleton(sc.blind(it), opts)
    comp = [b for path, b in posts("/completion") if b.get("grammar")][-1]
    user = build_pick_order(it, "none", opts)[0]
    rendered = mock_reason.render([{"role": "system", "content": SYSTEM["pick"]}, {"role": "user", "content": user}],
                                  {"enable_thinking": False})
    check(comp["prompt"] == rendered + skel + "\n" + PREFIX, "content-channel prompt")
    check(comp["grammar"] == 'root ::= ("A" | "B" | "C" | "D" | "E" | "F" | "G" | "X") "\\"}"', comp["grammar"])
    check("response_format" not in comp and "json_schema" not in comp, "schema sent to /completion")
    check(comp["temperature"] == 0.6 and comp["seed"] == sample_seed("HW01", 0) and comp["top_k"] == 20
          and comp["min_p"] == 0 and comp["n_predict"] == sc.PREFILL_CAP, str({k: comp[k] for k in comp if k != "prompt"}))
    check(not posts("/v1/chat/completions"), "the chat endpoint was called")
    r = rows(out("c08a.jsonl"))[-1]
    check(r["chosen_key"] == opts[2]["key"] and r["scaffold"]["channel"] == "content" and r["n_calls"] == 1, str(r)[:300])
    p = run_py(lc_args("c08b.jsonl", "--scaffold", "prefill", "--prefill-channel", "think"))
    comp = [b for path, b in posts("/completion") if b.get("grammar")][-1]
    check(p.returncode == 0 and comp["prompt"] == rendered[: -len(sc.EMPTY_THINK)] + "<think>\n" + skel +
          "\n</think>\n\n" + PREFIX, "think-channel prompt")
    check(rows(out("c08b.jsonl"))[-1]["variant"] == "scaffold-prefill-think", "variant name")
    STATE.reset()
    STATE.template_style = "plain"
    p = run_py(lc_args("c08c.jsonl", "--scaffold", "prefill", "--prefill-channel", "think"))
    check(p.returncode == 3 and "empty think block" in p.stderr and not [b for path, b in posts("/completion")
                                                                        if b.get("grammar")], p.stderr[-300:])
    p = run_py(lc_args("c08d.jsonl", "--scaffold", "prefill"))
    check(p.returncode == 0 and rows(out("c08d.jsonl"))[-1]["parse_ok"], "content channel on a plain template")
    return "content prompt exact; think block filled; grammar exact; no schema on /completion; plain template refused (exit 3)"


def c09_quote_first_schema_post_and_scoring():
    """quote-first puts one "<field>_quote" per quote-checked field first, checks it is verbatim, replaces a paraphrased
    field with its verbatim quote, strips the quote keys, and score.py scores the result against the item's schema.

    Why: doc 59 S8; Qwen3.5-4B paraphrases Fill spans (doc 59 §3.4), and the check must be code's, not the model's.
    A field is a "paraphrase" only when the item's own quote_in_request validator rejects it: a byte-exact test would
    overwrite right spans that differ in case or punctuation, and a blank quote (a substring of any request with a
    space) would overwrite anything.
    """
    it = next(i for i in SUITES["fill"]["items"] if i["id"] == "F09")
    v = sc.blind_fill(it)
    schema = sc.quote_first_schema(v)
    check(list(schema["properties"])[0] == "target_quote" and schema["required"][0] == "target_quote"
          and schema["properties"]["target_quote"] == {"type": "string", "maxLength": 60}
          and schema["additionalProperties"] is False, str(schema)[:300])
    req = it["request"]
    rec, d = sc.quote_first_post({"target_quote": "the radar site on Hill 214", "target": "Hill 214 radar site",
                                  "title": "t"}, v)
    check(rec["target"] == "the radar site on Hill 214" and d["target"]["replaced"] and "target_quote" not in rec, str(d))
    rec, d = sc.quote_first_post({"target_quote": "the radar site", "target": "radar site on Hill 214"}, v)
    check(rec["target"] == "radar site on Hill 214" and not d["target"]["replaced"], "verbatim field kept")
    rec, d = sc.quote_first_post({"target_quote": "radar at hill", "target": "radar at hill"}, v)
    check(not d["target"]["quote_verbatim"] and rec["target"] == "radar at hill", "non-verbatim quote unused")
    rec, d = sc.quote_first_post({"target_quote": "", "target": "x"}, v)
    check(not d["target"]["quote_verbatim"], "empty quote not allowed where allow_empty is false")
    f01 = sc.blind_fill(next(i for i in SUITES["fill"]["items"] if i["id"] == "F01"))
    _, d = sc.quote_first_post({"place_quote": "", "place": ""}, f01)
    check(d["place"]["quote_verbatim"], "empty quote allowed where allow_empty is true")
    check("radar site on Hill 214" in req, "fixture")
    # A field the quote_in_request validator accepts is kept even when it is not byte-exact (case, a trailing full
    # stop), although the quote is verbatim: replacing it could turn a right span into a wrong one.
    rec, d = sc.quote_first_post({"target_quote": "the radar site on Hill 214", "target": "Radar site on Hill 214."}, v)
    check(rec["target"] == "Radar site on Hill 214." and not d["target"]["replaced"]
          and d["target"]["value_in_request"] and not d["target"]["value_verbatim"], f"validator-accepted field {d}")
    # A blank quote is a substring of almost any request, but it is no quote: it never replaces a field.
    for blank in (" ", "  "):
        for allow in (f01, v):
            fld = "place" if allow is f01 else "target"
            rec, d = sc.quote_first_post({fld + "_quote": blank, fld: "nowhere at all"}, allow)
            check(not d[fld]["quote_verbatim"] and rec[fld] == "nowhere at all", f"blank quote {blank!r} used on {fld}")
    # The mirrored check agrees with score.py's validator on every field of every Fill item and a set of variants.
    import score  # noqa: PLC0415 - the tool's scorer, imported here so the other tests do not depend on it
    variants = lambda s: [s, s.upper(), s.lower(), f" {s} ", s + ".", s + ",", '"' + s + '"', s.replace(" ", "  "),  # noqa: E731
                          s[:-1] if len(s) > 1 else s, s + " extra", "", " "]
    n = 0
    for it in SUITES["fill"]["items"]:
        for val in [vv for vv in it["validators"] if vv.get("check") == "quote_in_request"]:
            words_ = it["request"].split()
            for span in {" ".join(words_[i:i + 3]) for i in range(0, max(1, len(words_) - 2))}:
                for s in variants(span):
                    want = score.check_validator(val, s, it["request"], [])
                    check(sc.in_request(s, it["request"], val.get("allow_empty")) == want,
                          f"{it['id']} {val['field']}: in_request({s!r}) != score.check_validator ({want})")
                    n += 1
    check(n > 500, f"only {n} agreement cases")

    def chat(body):
        good = {"target_quote": "the radar site on Hill 214", "target": "Hill 214 radar", "title": "Night Raid",
                "side": "west", "archetype": "raid", "time_of_day": "night",
                "pitch": "West commandos strike the radar at night."}
        return json.dumps(good)

    STATE.chat_fn = chat
    p = run_py(lc_args("c09.jsonl", "--scaffold", "quote-first", suite="fill", items="F09"))
    check(p.returncode == 0, p.stderr[-400:])
    body = [b for path, b in posts("/v1/chat/completions")][-1]
    check(list(body["response_format"]["json_schema"]["schema"]["properties"])[0] == "target_quote"
          and "- target_quote: fill this first." in body["messages"][1]["content"] and body["max_tokens"] == 400,
          "request")
    r = rows(out("c09.jsonl"))[-1]
    check(r["parsed"]["target"] == "the radar site on Hill 214" and "target_quote" not in r["parsed"]
          and r["parsed_with_quotes"]["target"] == "Hill 214 radar" and r["scaffold"]["quote_first"]["target"]["replaced"],
          str(r)[:400])
    s = run_py(["--csv", out("c09.csv"), "--json", out("c09.json"), out("c09.jsonl")], script="score.py")
    summ = _load(out("c09.json"))
    grp = [m for m in summ if m["variant"] == "scaffold-quote-first"][0]
    check(s.returncode == 0 and grp["schema_valid_rate"] == 1.0 and grp["field_accuracy_by_field"]["target"] == 1.0,
          str(grp)[:300])
    return (f"quote fields first; verbatim quote replaces a paraphrase but never a validator-accepted field; blank "
            f"quotes ignored; in_request = score.check_validator on {n} cases; quote keys stripped; score.py: "
            f"schema-valid, span right")


def c10_refusals_before_any_request():
    """Every combination a scaffold arm cannot honour exits 2 before any request.

    Why: a silently ignored flag would make an arm look like something it is not.
    """
    base = ["--base-url", URL, "--k", "1", "--out", out("c10.jsonl")]
    cases = [
        (["--backend", "llamacpp", "--suite", "fill", "--scaffold", "diff"], "Pick suites only"),
        (["--backend", "llamacpp", "--suite", "pick", "--scaffold", "quote-first"], "Fill suites only"),
        (["--backend", "llamacpp", "--suite", "pick", "--scaffold", "diff", "--why"], "cannot be combined"),
        (["--backend", "llamacpp", "--suite", "pick", "--scaffold", "diff", "--repair"], "cannot be combined"),
        (["--backend", "llamacpp", "--suite", "pick", "--scaffold", "diff", "--variant", "noschema"],
         "cannot be combined"),
        (["--backend", "llamacpp", "--suite", "pick", "--scaffold", "diff", "--condition", "open"],
         "cannot be combined"),
        (["--backend", "llamacpp", "--suite", "fill", "--scaffold", "quote-first", "--schema-mode", "text"],
         "cannot be combined"),
        (["--backend", "llamacpp", "--suite", "pick", "--scaffold", "diff", "--pick-mode", "logprob"],
         "--pick-mode logprob"),
        (["--backend", "openai", "--model", "m", "--suite", "pick", "--scaffold", "diff"], "local-only"),
        (["--backend", "ollama", "--model", "m", "--suite", "pick", "--scaffold", "eliminate"], "needs --backend llamacpp"),
        (["--backend", "ollama", "--model", "m", "--suite", "pick", "--scaffold", "prefill"], "needs --backend llamacpp"),
        (["--backend", "llamacpp", "--suite", "pick", "--scaffold", "rule"], "--condition cards"),
        (["--backend", "llamacpp", "--suite", "pick", "--scaffold", "diff", "--scaffold-keep", "2"], "eliminate or pairwise"),
        (["--backend", "llamacpp", "--suite", "pick", "--scaffold", "eliminate", "--scaffold-keep", "4"], "must be 2 or 3"),
        (["--backend", "llamacpp", "--suite", "pick", "--scaffold", "eliminate", "--scaffold-keep", "1"], "must be 2 or 3"),
        (["--backend", "llamacpp", "--suite", "pick", "--scaffold", "diff", "--prefill-channel", "think"],
         "prefill only"),
        (["--backend", "llamacpp", "--suite", "pick", "--scaffold-keep", "2"], "--scaffold arm only"),
        (["--backend", "llamacpp", "--suite", "pick", "--scaffold", "prefill", "--think-mode", "omit"], "think-mode omit"),
        (["--backend", "llamacpp"], "--suite is required"),
    ]
    for argv, needle in cases:
        STATE.reset()
        p = run_py(argv + base)
        check(p.returncode == 2 and needle in p.stderr, f"{argv}: exit {p.returncode}, {p.stderr[-200:]}")
        check(not STATE.requests, f"{argv}: {len(STATE.requests)} requests before the refusal")
    return f"{len(cases)} refusals, each exit 2 with 0 requests"


def c11_records_ledger_totals_and_resume():
    """Every scaffold record carries its arm, version and per-call ledger (tokens, latency, timings); the record's
    totals are the ledger's sums; --resume re-sends nothing.

    Why: the plan compares arms on cost too, so each call's tokens and latency must be kept, not only a total; and PR1
    ("no finish_reason 'length' on an admitted answer") needs every call's own cap and finish, because the record's
    done_reason is only the last call's: a pair call cut at its cap inside a pairwise decision is invisible there.

    How: the caps are checked per phase (score 1, pair and final Pick the Pick cap, subq its own, prefill's answer
    PREFILL_CAP, a one-call arm the record's num_predict); then a pairwise run whose every pair call finishes "length"
    must count 6 truncated calls, and scaffold_stats must count that decision as truncated.
    """
    caps = {"score": 1, "pair": 64, "final": 64, "answer": None}
    for arm, extra in (("diff", []), ("subq", []), ("pairwise", []), ("prefill", [])):
        name = f"c11-{arm}.jsonl"
        p = run_py(lc_args(name, "--scaffold", arm, *extra, items="HW01,HT03", k=2))
        check(p.returncode == 0, p.stderr[-300:])
        for r in rows(out(name)):
            led = r["scaffold"]
            check(led["arm"] == arm and led["version"] == sc.SCAFFOLD_VERSION and r["variant"].startswith("scaffold-"),
                  "arm fields")
            for c in led["calls"]:
                check("latency_ms" in c and "phase" in c and "endpoint" in c, f"ledger entry {c}")
            forward = [c for c in led["calls"] if c["phase"] != "render"]
            check(all(isinstance(c["prompt_tokens"], int) for c in forward), "tokens per call")
            check(r["prompt_eval_count"] == sum(c["prompt_tokens"] or 0 for c in led["calls"]), "prompt sum")
            check(r["eval_count"] == sum(c["completion_tokens"] or 0 for c in led["calls"]), "eval sum")
            check(r["n_calls"] == led.get("model_calls", 1), "model calls")
            check(led.get("truncated_calls") == 0, f"{arm}: truncated_calls {led.get('truncated_calls')}")
            for c in forward:
                want = {"subq": sc.subq_cap(len(led.get("statements") or [])),
                        "answer": sc.PREFILL_CAP if arm == "prefill" else r["num_predict"]}.get(c["phase"],
                                                                                              caps.get(c["phase"]))
                check(c.get("cap") == want, f"{arm} {c['phase']}: cap {c.get('cap')}, want {want}")
        STATE.reset()
        STATE.chat_fn = model_chat
        STATE.dist_fn = model_dist
        p = run_py(lc_args(name, "--scaffold", arm, *extra, "--resume", items="HW01,HT03", k=2))
        # The run's one preflight ("ping" completion for the letter-reading arms, a render for prefill) still goes out;
        # no decision call may.
        sent = [b for path, b in posts("/v1/chat/completions", "/completion") if b.get("prompt") != "ping"]
        check(p.returncode == 0 and not sent and len(rows(out(name))) == 4, f"{arm}: resume re-sent {len(sent)} calls")
    # Every pair call cut at its cap: the decision stands, but its ledger counts 6 truncated calls and the stats see it.
    STATE.reset()
    STATE.chat_fn = model_chat
    STATE.dist_fn = model_dist
    STATE.finish_fn = lambda body: "length" if len(menu_of(user_of(body))) == 3 else "stop"
    p = run_py(lc_args("c11-trunc.jsonl", "--scaffold", "pairwise", items="HW01"))
    r = rows(out("c11-trunc.jsonl"))[-1]
    check(p.returncode == 0 and r["scaffold"]["truncated_calls"] == 6, f"truncated {r['scaffold'].get('truncated_calls')}")
    plain = dict(r, variant="plain", scaffold=None, done_reason="stop")
    row = scaffold_stats.analyse([plain, r], scaffold_stats.load_suites())[0]
    check(row["truncated_decisions_arm"] == 1, f"stats truncated {row['truncated_decisions_arm']}")
    return ("4 arms x 4 records: ledgers complete, totals = sums, model_calls counted, caps per call, resume sends no "
            "decision call; 6 truncated pair calls counted and seen by scaffold_stats")


def c12_suite_file_split_and_scoring():
    """--suite-file with --split runs only that half; a mixed-split file without --split, or the held-out half without
    --confirm-heldout, is refused; score.py and uplift.py read the records with --suite-file.

    Why: the plan tunes on the pools' tune halves only and looks at the held-out halves once, deliberately.

    How: the staged pick pool's tune half when LOCALQUAL_POOLS provides it, else its stand-in (pick_pool: pick-hard
    renamed pick-pool, every item split "tune"), plus one synthetic held-out item.
    """
    mixed = json.loads(json.dumps(pick_pool()))
    # A synthetic held-out item (a renamed copy of a tune item), so the refusals can be tested without the real half.
    fake = json.loads(json.dumps(mixed["items"][0]))
    fake.update(id="ZZ99", split="heldout")
    mixed["items"].append(fake)
    path = write_suite("c12-pool.json", mixed)
    p = run_py(lc_args("c12a.jsonl", "--suite-file", path, suite=None, items=None))
    check(p.returncode == 2 and "mixes splits" in p.stderr, p.stderr[-200:])
    p = run_py(lc_args("c12b.jsonl", "--suite-file", path, "--split", "heldout", suite=None, items=None))
    check(p.returncode == 2 and "--confirm-heldout" in p.stderr, p.stderr[-200:])
    p = run_py(lc_args("c12c.jsonl", "--suite-file", path, "--split", "tune", "--confirm-heldout", suite=None,
                       items=None))
    check(p.returncode == 2, "confirm without heldout")
    p = run_py(lc_args("c12d.jsonl", "--suite-file", path, "--split", "heldout", "--confirm-heldout", suite=None,
                       items=None))
    check(p.returncode == 0 and [r["item_id"] for r in rows(out("c12d.jsonl"))] == ["ZZ99"], "heldout confirm run")
    p = run_py(lc_args("c12e.jsonl", "--suite-file", path, "--split", "tune", suite=None, items=None))
    p2 = run_py(lc_args("c12e.jsonl", "--suite-file", path, "--split", "tune", "--scaffold", "diff", suite=None,
                        items=None))
    recs = rows(out("c12e.jsonl"))
    check(p.returncode == 0 and p2.returncode == 0 and len(recs) == 60 and all(r["split"] == "tune" and
          r["suite"] == "pick-pool" and r["suite_file"] == "c12-pool.json" for r in recs), "tune records")
    check("ZZ99" not in {r["item_id"] for r in recs}, "heldout item in a tune run")
    s = run_py(["--suite-file", path, "--csv", out("c12.csv"), "--json", out("c12.json"), out("c12e.jsonl")],
               script="score.py")
    summ = _load(out("c12.json"))
    check(s.returncode == 0 and {m["variant"] for m in summ} == {"plain", "scaffold-diff"} and
          all(m["accuracy"] is not None and m["stale_suite_records"] == 0 for m in summ), str(summ)[:300])
    u = run_py(["--suite-file", path, "--json", out("c12u.json"), "--arms-csv", out("c12a.csv"), "--pairs-csv",
                out("c12p.csv"), out("c12e.jsonl")], script="uplift.py")
    pairs = _load(out("c12u.json")).get("pairs", [])
    check(u.returncode == 0 and any("scaffold-diff" in json.dumps(pr) for pr in pairs), "uplift auto-pair")
    return "tune-only run of 30 items x 2 arms; 3 refusals; score.py and uplift.py (auto-pair plain vs scaffold-diff)"


def c13_failed_call_is_an_error_and_resumes():
    """A 500 on one pair call makes the decision an error record, and --resume re-runs exactly that decision.

    Why: a half-finished multi-call decision must never be scored as an answer.
    """
    STATE.fail_chat_nth = 3
    p = run_py(lc_args("c13.jsonl", "--scaffold", "pairwise", items="HW01,HT03"))
    check(p.returncode == 2, f"exit {p.returncode}")
    recs = rows(out("c13.jsonl"))
    check(recs[0]["error"] and recs[0]["parse_ok"] is False and recs[1]["error"] is None, str(recs[0])[:200])
    STATE.reset()
    STATE.chat_fn = model_chat
    STATE.dist_fn = model_dist
    p = run_py(lc_args("c13.jsonl", "--scaffold", "pairwise", "--resume", items="HW01,HT03"))
    recs = rows(out("c13.jsonl"))
    check(p.returncode == 0 and len(recs) == 3 and recs[2]["item_id"] == "HW01" and not recs[2]["error"], "resume")
    return "pair-call 500 -> error record (exit 2); --resume re-ran HW01 only"


def c14_ollama_one_and_two_call_arms():
    """The one-call arms and subq run on the Ollama backend (native /api/chat) with the same prompts.

    Why: the arms that need no letter probabilities stay runtime-neutral, so an Ollama-only machine can run them.
    """
    for arm, cond in (("diff", "none"), ("rule", "cards"), ("why", "none"), ("subq", "none")):
        STATE.reset()
        STATE.chat_fn = model_chat
        p = run_py(["--backend", "ollama", "--model", "mock:4b", "--base-url", URL, "--suite", "pick-hard", "--items",
                    "HW01", "--k", "1", "--condition", cond, "--scaffold", arm, "--out", out(f"c14-{arm}.jsonl")])
        check(p.returncode == 0, f"{arm}: {p.stderr[-300:]}")
        body = [b for path, b in posts("/api/chat")][0]
        check("format" in body and body.get("think") is False, f"{arm}: ollama body {list(body)}")
        check(rows(out(f"c14-{arm}.jsonl"))[-1]["scaffold"]["calls"][0]["endpoint"] == "/api/chat", arm)
    return "diff, rule, why and subq on /api/chat with think=false and the schema in format"


def c15_prefill_skeleton_adds_no_instruction():
    """The prefill skeleton's head and tail add no decision rule the plain prompt lacks: the tail restates the Pick
    system prompt, and the diff lines are the diff arm's, so prefill differs from diff only in the channel.

    Why: the plan reads prefill against diff as "the same lines, in the assistant turn instead of the user turn". A
    tail such as "pick the option that fits every part of the request; X if none does" is a stricter test than the
    system prompt's "choose the single best option; if no option fits, choose X": it leans towards X on near fits
    (HM04-type items), so a prefill gain or loss could come from that instruction, not from the channel.

    How: every word of the tail is a word of SYSTEM["pick"] except "now" and "pick" (the system prompt says
    "choose"); the head only announces the lines; and the skeleton minus head and tail is exactly the diff arm's lines.
    """
    extra = words(sc.PREFILL_TAIL) - words(SYSTEM["pick"])
    check(extra <= {"now", "pick"}, f"the prefill tail adds words the system prompt lacks: {sorted(extra)}")
    check(words(sc.PREFILL_HEAD) <= words(sc.DIFF_HEADING) | {"before", "answering", "lists"},
          f"the prefill head adds words: {sorted(words(sc.PREFILL_HEAD) - words(sc.DIFF_HEADING))}")
    n = 0
    for it in PICK_ITEMS:
        for sample in range(2):
            v, opts = sc.blind(it), permute_options(it, sample)
            skel = sc.prefill_skeleton(v, opts)
            check(skel == sc.PREFILL_HEAD + "\n" + "\n".join(sc.diff_lines(v, opts)) + "\n" + sc.PREFILL_TAIL,
                  f"{it['id']}: skeleton is not head + diff lines + tail")
            n += 1
    return f"tail words within the system prompt (+ now, pick); {n} skeletons = head + the diff arm's lines + tail"


# ── unittest wiring ──────────────────────────────────────────────────────────

class ScaffoldFunctionTests(support.CaseTestCase):
    """What the scaffold arms compute and send (see the module docs)."""

    cases = (c01_diff_known_values,
             c02_rule_sentence_known_values,
             c03_why_arm_bounds_both_ends,
             c04_eliminate_keeps_top_k_and_never_masks_x,
             c05_eliminate_fallback_without_letters,
             c06_pairwise_round_robin_and_aggregation,
             c07_subq_statements_and_rule_table,
             c08_prefill_content_and_think_channels,
             c09_quote_first_schema_post_and_scoring,
             c10_refusals_before_any_request,
             c11_records_ledger_totals_and_resume,
             c12_suite_file_split_and_scoring,
             c13_failed_call_is_an_error_and_resumes,
             c14_ollama_one_and_two_call_arms,
             c15_prefill_skeleton_adds_no_instruction)

    def setUp(self):
        reset_mock()


if __name__ == "__main__":
    unittest.main()
