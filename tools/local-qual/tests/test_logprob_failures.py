#!/usr/bin/env python3
"""Tests for --pick-mode logprob under failure and adversarial responses: server errors, the preflight and
--resume, hostile token entries, cut and invalid characters, truncated candidate lists, the answer-prefix
token boundary, the template render, failed orders, non-finite numbers and malformed replies.

Runs run.py against mock_llama.py (in-process on 127.0.0.1). No model runs.

Run the whole suite from the repository root with ``python -m unittest discover -s tools/local-qual/tests``;
the module docs of support.py explain the case functions and the environment switches.
"""

import json
import math
import unittest

import logprob_support
import support
from logprob_support import *  # noqa: F401,F403 - the shared fixtures the cases use by name

URL = None  # the mock's base URL while this module runs (set by setUpModule)


def setUpModule():
    global URL
    URL = logprob_support.start("logprob-failures")


def tearDownModule():
    logprob_support.finish()


# ── Logprob mode: failures and adversarial responses (l10-l19) ─────────────────

def l10_server_failures_preflight_resume_and_kwargs_fallback():
    """A build without n_probs stops at the preflight (exit 3); a 500 is an error record that --resume re-runs; a
    template that rejects chat_template_kwargs is retried without it; a response whose probabilities sum above 1 is
    an error.

    Why: a server fault must never turn into a recorded answer, and must not cost more than one request to detect.
    """
    STATE.no_probs = True
    p = run_py(lp_args("noprobs.jsonl"))
    check(p.returncode == 3 and "no token probabilities" in p.stderr and len(STATE.paths("/completion")) == 1
          and not rows(out("noprobs.jsonl")), f"no n_probs: exit {p.returncode}, {len(STATE.paths('/completion'))}")
    STATE.reset()
    STATE.raw_response = {"content": "x", "completion_probabilities": []}
    p = run_py(lp_args("empty.jsonl"))
    check(p.returncode == 3 and len(STATE.paths("/completion")) == 1, f"empty list: exit {p.returncode}")
    STATE.reset()
    STATE.dist_fn = weights_dist(lambda it, k: 5 if k == it["answer"] else 1)
    STATE.fail_completion = 1
    p = run_py(lp_args("fail.jsonl", items="PW01,PW02"))
    rs = rows(out("fail.jsonl"))
    check(p.returncode == 2 and len(rs) == 2 and "HTTP 500" in (rs[0]["error"] or "") and rs[0]["parse_ok"] is False
          and rs[0]["correct"] is False and rs[1]["error"] is None and rs[1]["correct"] is True,
          f"500: exit {p.returncode}, {[r['error'] for r in rs]}")
    n_before = len(completions())
    p = run_py(lp_args("fail.jsonl", "--resume", items="PW01,PW02"))
    rs = rows(out("fail.jsonl"))
    check(p.returncode == 0 and len(rs) == 3 and rs[2]["item_id"] == "PW01" and rs[2]["error"] is None
          and len(completions()) - n_before == 1, f"resume: exit {p.returncode}, {len(rs)} rows")
    STATE.reset()
    STATE.dist_fn = weights_dist(lambda it, k: 5 if k == it["answer"] else 1)
    STATE.reject_kwargs = True
    p = run_py(lp_args("kwargs.jsonl", items="PW01,PW02"))
    rs = rows(out("kwargs.jsonl"))
    menus = [q["body"] for q in STATE.paths("/apply-template") if "Options:" in json.dumps(q["body"])]
    # The boundary check renders first: rejected with the kwargs, retried without; the decisions never send them.
    check(p.returncode == 0 and [r["think_sent"] for r in rs] == [False, False] and all(r["correct"] for r in rs)
          and ["chat_template_kwargs" in b for b in menus] == [True, False, False, False],
          f"kwargs fallback: exit {p.returncode}, sent {['chat_template_kwargs' in b for b in menus]}")
    STATE.reset()
    # Padded to n_probs with probability-0 tokens, as a server lists them, so only the sum is wrong.
    STATE.raw_response = {"content": "A", "completion_probabilities": [{"token": "A", "top_logprobs": [
        {"id": 1, "token": "A", "logprob": math.log(.9)}, {"id": 2, "token": "B", "logprob": math.log(.9)}]
        + [{"id": 10 + i, "token": f"~{i}", "logprob": mock_llama.LOWEST} for i in range(30)]}]}
    p = run_py(lp_args("sum.jsonl"))
    r = rows(out("sum.jsonl"))[0]
    check(p.returncode == 2 and "sum to 1.8000" in (r["error"] or "") and r["chosen_key"] is None,
          f"sum > 1: exit {p.returncode}, {r['error']}")
    return ("no n_probs: exit 3 after 1 request; 500: error record, resume re-ran 1 call; kwargs rejected: retried "
            "without, think_sent false; listed mass 1.8: error record")


def l11_adversarial_entries_are_ignored():
    """Malformed entries (NaN, strings, booleans, probabilities outside [0, 1], positive logprobs, duplicate ids,
    bad bytes) are counted and ignored; an oversized list is cut at n_probs; a non-object response is an error.

    Why: token lists come from a server the tool does not control; a NaN or a negative probability must never reach a
    distribution, and a huge list must not grow the record without bound.
    """
    bad = [{"token": "A", "logprob": float("nan")}, {"token": "A", "prob": "0.5"}, {"token": "A", "prob": True},
           {"token": "A", "prob": -0.1}, {"token": "A", "prob": 1.5}, {"token": "A", "logprob": 0.5},
           {"token": "A"}, ["A", 0.5], None, {"token": 7, "prob": 0.1}, {"token": "", "bytes": [300], "prob": 0.1},
           {"token": "", "bytes": [65] * (lp.MAX_TOKEN_BYTES + 1), "prob": 0.01}]
    # A 128-byte token is real (the Qwen3 and Qwen3.5 vocabularies have over a hundred tokens above 64 bytes), and a
    # token exactly at the byte cap is kept too.
    good = [{"id": 1, "token": "B", "prob": 0.4}, {"id": 1, "token": "B", "prob": 0.4},
            {"id": 2, "token": "A", "logprob": -math.inf}, {"id": 3, "token": "C", "prob": 0.2},
            {"id": 4, "token": "", "bytes": [32] * 128, "prob": 0.01},
            {"id": 5, "token": "", "bytes": [45] * lp.MAX_TOKEN_BYTES, "prob": 0.01}]
    entries, shape, _, n_bad, beyond = lp.candidates({"completion_probabilities": [{"top_probs": bad + good}]}, 32)
    check(n_bad == len(bad) + 1 and [t for t, _ in entries] == ["B", "C", " " * 128, "-" * lp.MAX_TOKEN_BYTES, "A"]
          and entries[4][1] == 0.0 and beyond == 0 and shape == "native-post"
          and lp.listed_count(entries, n_bad, beyond) == len(bad) + len(good), f"{n_bad} bad, entries {entries}")
    big = [{"id": i, "token": f"t{i}", "prob": 0.0005} for i in range(1000)]
    entries, _, _, _, beyond = lp.candidates({"completion_probabilities": [{"top_probs": big}]}, 20)
    check(len(entries) == 20 and beyond == 980, f"oversized: {len(entries)} kept, {beyond} beyond")
    errors = 0
    for resp in ([], "x", {"choices": [{"logprobs": None}]}, {"completion_probabilities": [{"content": "A"}]}, {}):
        try:
            lp.candidates(resp, 20)
        except lp.LogprobError:
            errors += 1
    check(errors == 5, f"{errors} of 5 unusable responses raised LogprobError")
    return f"{len(bad) + 1} malformed entries ignored (incl. a duplicate id); 1,000 entries cut to 20; 5 unusable responses raise"


def l12_warmup_and_score_compatibility():
    """--warmup sends one unrecorded decision; the generate mode's default request bodies are untouched (checked by
    test_cloudqual.py t01 over 2,180 bodies), so this checks the warm-up only.

    Why: the first call after a server start is slow; it must stay out of the records here too.
    """
    STATE.dist_fn = weights_dist(lambda it, k: 5 if k == it["answer"] else 1)
    p = run_py(lp_args("warm.jsonl", "--warmup"))
    check(p.returncode == 0 and len(rows(out("warm.jsonl"))) == 1 and len(completions()) == 2
          and len(STATE.paths("/completion")) == 3 and "warm-up call" in p.stdout,
          f"exit {p.returncode}, {len(completions())} menu completions")
    return "1 preflight + 1 warm-up + 1 recorded decision; 1 record"


def l13_cut_characters_and_json_invalid_variants_are_not_letters():
    """A token whose text the server cut at a partial UTF-8 character is read from its bytes and is not a letter; a
    tab next to the letter (invalid inside a JSON string) does not count; one letter under two token ids adds up.

    Why: llama-server truncates the ``token`` text at the last whole character (``validate_utf8``) but sends every
    byte in ``bytes``, so 'D' + the first bytes of '…' arrives as the text "D": counting it credits a letter the model
    would continue into a longer string. A raw tab inside a string fails run.py's JSON parse, so a tab variant is not
    an answer the generate mode could have produced. A SentencePiece vocabulary with byte fallback has the letter
    both as a piece and as a byte token (<0x42>): two events, both "B".

    How: end to end, PW01 sample 0 has hold at D; the mock sends hold's letter only as the cut token (0.6) and sentry's
    letter as a plain token (0.3), so reading the bytes flips the answer to sentry.
    """
    resp = {"completion_probabilities": [{"top_logprobs": [
        {"id": 1, "token": "A", "bytes": [65], "logprob": math.log(.4)},
        {"id": 2, "token": "A", "bytes": [65, 0xE2, 0x80], "logprob": math.log(.2)},
        {"id": 3, "token": "B", "bytes": [66], "logprob": math.log(.15)},
        {"id": 4, "token": "B", "bytes": [66], "logprob": math.log(.1)},
        {"id": 5, "token": "\tC", "bytes": [9, 67], "logprob": math.log(.05)},
        {"id": 6, "token": "C\t", "bytes": [67, 9], "logprob": math.log(.05)},
        {"id": 7, "token": " C", "bytes": [32, 67], "logprob": math.log(.05)}]}]}
    entries = lp.candidates(resp, 32)[0]
    d = lp.letter_distribution(entries, ["A", "B", "C", "X"])
    check(close(d["letter_mass"]["A"], .4) and close(d["letter_mass"]["B"], .25) and close(d["letter_mass"]["C"], .05)
          and d["variants"]["B"] == ["B", "B"], f"mass {d['letter_mass']} variants {d['variants']}")
    check(lp.token_letter("A\t", ["A"]) is None and lp.token_letter("\tA", ["A"]) is None
          and lp.token_letter("A ", ["A"]) == "A", "tab variants")
    it = ITEMS["PW01"]
    menu0 = {letter: key for letter, key in zip("ABCDEFG", [o["key"] for o in permute_options(it, 0)])}
    hold = next(letter for letter, key in menu0.items() if key == "hold")
    sentry = next(letter for letter, key in menu0.items() if key == "sentry")
    cut = hold + "…"  # the letter followed by '…', whose bytes the mock sends whole and whose text it cuts
    STATE.token_bytes = {cut: cut.encode("utf-8")[:-1]}
    STATE.dist_fn = lambda menu, prompt: ([(cut, .6), (sentry, .3), ("\n", .1)] if item_for(prompt)
                                          else [("Hello", 1.0)])
    p = run_py(lp_args("cut.jsonl"))
    r = rows(out("cut.jsonl"))[0]
    o = r["logprob"]["orders"][0]
    check(p.returncode == 0 and r["chosen_key"] == "sentry" and close(r["confidence"], 1.0)
          and hold in o["missing"], f"exit {p.returncode}: chose {r.get('chosen_key')}, missing {o.get('missing')}")
    return (f"cut token '{hold}'+partial '…' not {hold} (sentry chosen, p 1.0); byte-fallback B + B = 0.25; "
            "tab variants rejected, trailing space kept")


def l14_truncated_candidate_lists_are_refused():
    """A server that lists fewer tokens than n_probs (a truncated candidate set) stops at the preflight, and a decision
    that meets one is an error, not an answer.

    Why: llama-server computes the listed probabilities over every logit it holds; with backend sampling (-bs) it
    holds only the sampler's candidates, and at temperature 0 that can be the one greedy token, which would come
    back with probability 1 and make every decision look certain. A full vocabulary always has n_probs tokens.
    """
    STATE.truncate = 1
    STATE.dist_fn = weights_dist(lambda it, k: 5 if k == it["answer"] else 1)
    p = run_py(lp_args("trunc.jsonl"))
    check(p.returncode == 3 and "listed 1 of 32" in p.stderr and len(STATE.paths("/completion")) == 1
          and not rows(out("trunc.jsonl")), f"preflight: exit {p.returncode}, {p.stderr[-200:]}")
    STATE.reset()
    STATE.truncate, STATE.truncate_ping = 3, False
    STATE.dist_fn = weights_dist(lambda it, k: 5 if k == it["answer"] else 1)
    p = run_py(lp_args("trunc2.jsonl"))
    r = rows(out("trunc2.jsonl"))[0]
    check(p.returncode == 2 and "listed 3 of 32" in (r["error"] or "") and r["chosen_key"] is None
          and "confidence" not in r, f"decision: exit {p.returncode}, {r['error']}")
    # A response that generated two tokens (the first ended inside a UTF-8 character) lists another position.
    STATE.reset()
    top = [{"id": 1, "token": "A", "logprob": math.log(.6)}] + [
        {"id": 10 + i, "token": f"~{i}", "logprob": mock_llama.LOWEST} for i in range(31)]
    STATE.raw_response = {"content": "é", "tokens_predicted": 2, "tokens_evaluated": 100,
                          "completion_probabilities": [{"token": "A", "top_logprobs": top}]}
    p = run_py(lp_args("twotok.jsonl"))
    r = rows(out("twotok.jsonl"))[0]
    check(p.returncode == 2 and "generated 2 tokens" in (r["error"] or "") and r["prompt_eval_count"] == 100,
          f"two tokens: exit {p.returncode}, {r['error']}")
    return ("preflight listing 1 of 32 tokens: exit 3 after 1 request; a decision listing 3 of 32: error record; "
            "2 tokens generated: error record (its 100 prompt tokens still counted)")


def l15_answer_prefix_boundary_is_checked_through_tokenize():
    """Before the first item, the rendered prompt plus the answer prefix is tokenised with and without each letter;
    a vocabulary that merges the opening quote with a letter is reported, and a build without /tokenize is noted.

    Why: the mode reads the letter at the token boundary the prefix ends on. If the model's vocabulary has a single
    token for ' "A' the model never saw ' "' followed by 'A' in training, and the read is off-distribution for that
    letter; the owner must see that per model, not assume it (Qwen3, Qwen3.5 and Gemma 4 split there, doc check).

    How: the mock tokenises by greedy longest match; adding the piece ' "A' makes 'A' non-canonical.
    """
    STATE.dist_fn = weights_dist(lambda it, k: 5 if k == it["answer"] else 1)
    p = run_py(lp_args("bound.jsonl"))
    r = rows(out("bound.jsonl"))[0]
    b = r.get("logprob_boundary") or {}
    toks = [q["body"] for q in STATE.paths("/tokenize")]
    check(p.returncode == 0 and b.get("checked") is True and b.get("noncanonical") == [] and b.get("junction_ok")
          and b.get("prefix_tail") == ['":', ' "'] and len(toks) == 10
          and all(t["add_special"] is False and t["parse_special"] is True and t["with_pieces"] is True
                  and t["model"] == LABEL for t in toks), f"canonical: exit {p.returncode}, {b}, {len(toks)} calls")
    check(toks[1]["content"] == toks[0]["content"] + PREFIX and toks[2]["content"] == toks[1]["content"] + 'A"}',
          "tokenised texts")
    STATE.reset()
    STATE.extra_pieces = (' "A',)
    STATE.dist_fn = weights_dist(lambda it, k: 5 if k == it["answer"] else 1)
    p = run_py(lp_args("bound2.jsonl"))
    b2 = rows(out("bound2.jsonl"))[0].get("logprob_boundary") or {}
    check(p.returncode == 0 and b2.get("noncanonical") == ["A"] and "not a token boundary" in p.stderr
          and b2.get("letter_pieces", {}).get("A") == ' "A', f"merged: exit {p.returncode}, {b2}, {p.stderr[-300:]}")
    STATE.reset()
    STATE.no_tokenize = True
    STATE.dist_fn = weights_dist(lambda it, k: 5 if k == it["answer"] else 1)
    p = run_py(lp_args("bound3.jsonl"))
    b3 = rows(out("bound3.jsonl"))[0].get("logprob_boundary") or {}
    check(p.returncode == 0 and b3.get("checked") is False and "404" in (b3.get("reason") or ""),
          f"no /tokenize: exit {p.returncode}, {b3}")
    return "10 /tokenize calls; canonical: [] (tail '\":', ' \"'); vocabulary with ' \"A': ['A'] + warning; 404: unchecked"


def l16_template_render_matches_the_generate_mode_request():
    """The /apply-template body carries the generate mode's messages, response_format, thinking switch and model, so
    the server renders exactly the prompt the generate mode's chat call gets.

    Why: llama-server renders /apply-template and /v1/chat/completions through the same parser; a chat handler that
    reads the schema, or router mode choosing the model by name, would otherwise give the two modes different prompts
    (or another model's template) and the comparison would not be like for like.
    """
    STATE.dist_fn = weights_dist(lambda it, k: 5 if k == it["answer"] else 1)
    p1 = run_py(lp_args("same-lp.jsonl"))
    p2 = run_py(["--backend", "llamacpp", "--base-url", URL, "--suite", "pick", "--items", "PW01", "--k", "1",
                 "--wait", "5", "--out", out("same-gen.jsonl")])
    check(p1.returncode == 0 and p2.returncode == 0, f"exits {p1.returncode} {p2.returncode}")
    tmpl = [q["body"] for q in STATE.paths("/apply-template") if "Options:" in json.dumps(q["body"])][-1]
    chat = STATE.paths("/v1/chat/completions")[-1]["body"]
    same = {k: (tmpl.get(k), chat.get(k)) for k in ("messages", "response_format", "chat_template_kwargs", "model")}
    check(all(a == b and a is not None for a, b in same.values()), f"differs: {[k for k, (a, b) in same.items() if a != b]}")
    check(set(tmpl) == {"messages", "response_format", "chat_template_kwargs", "model"}, f"template body keys {set(tmpl)}")
    return "messages, response_format, chat_template_kwargs and model identical to the chat body"


def l17_a_failed_order_counts_its_call():
    """A decision that fails at its second option order records two /completion calls, and cascade.py costs two.

    Why: the call that failed was sent (and on a paid or shared server it was spent); counting only the orders that
    succeeded would understate the cost of the logprob arm in the cascade figures.
    """
    STATE.dist_fn = weights_dist(lambda it, k: 5 if k == it["answer"] else 1)
    STATE.fail_nth = 2
    p = run_py(lp_args("failnth.jsonl", "--permute", "3"))
    r = rows(out("failnth.jsonl"))[0]
    d = r["logprob"]
    check(p.returncode == 2 and (r["error"] or "").startswith("order 1: POST /completion: HTTP 500")
          and d["completion_calls"] == 2 and len(d["orders"]) == 1 and cascade.calls_of(r) == 2,
          f"exit {p.returncode}, {r['error']}, calls {d.get('completion_calls')}, costed {cascade.calls_of(r)}")
    return "failure at order 1 of 3: 2 calls recorded and costed (1 order kept)"


def l18_non_finite_counts_neither_crash_nor_reach_the_record():
    """NaN and Infinity in a response's token counts and timings are counted as 0 / left out; the run finishes and
    every record line is strict JSON.

    Why: Python's json.loads accepts NaN and Infinity, int() of either raises (the run would stop mid-suite on one
    odd response), and json.dumps would write NaN into the JSONL, which strict readers (and other tools) reject.
    """
    top = [{"id": 1, "token": "A", "logprob": math.log(.6)}, {"id": 2, "token": "B", "logprob": math.log(.3)}]
    top += [{"id": 10 + i, "token": f"~{i}", "logprob": mock_llama.LOWEST} for i in range(30)]
    STATE.raw_response = {"content": "A", "tokens_evaluated": float("nan"), "tokens_predicted": float("inf"),
                          "timings": {"prompt_ms": float("inf"), "predicted_ms": -5.0, "cache_n": float("nan")},
                          "completion_probabilities": [{"token": "A", "top_logprobs": top}]}
    p = run_py(lp_args("nan.jsonl"))

    def strict(text):
        raise ValueError(f"non-finite constant {text} in a record")

    with open(out("nan.jsonl"), encoding="utf-8") as f:
        recs = [json.loads(line, parse_constant=strict) for line in f if line.strip()]
    r = recs[0]
    check(p.returncode == 0 and r["prompt_eval_count"] == 0 and r["eval_count"] == 0 and r["error"] is None
          and r["logprob"]["orders"][0]["cache_n"] is None and r["total_duration"] == 0,
          f"exit {p.returncode}: {p.stderr[-300:]} {r.get('prompt_eval_count')}")
    return "NaN/Infinity counts and timings: run finished, counts 0, cache_n null, strict-JSON record"


def l19_non_object_template_and_tokenize_replies():
    """A /tokenize reply that is not a token list leaves the boundary unchecked; an /apply-template reply that is not
    an object is an error record per decision, never a crash.

    Why: both endpoints belong to a server the tool does not control; a list or a string where an object belongs must
    not stop a long run halfway (the records say what went wrong, and --resume re-runs the errors).
    """
    STATE.dist_fn = weights_dist(lambda it, k: 5 if k == it["answer"] else 1)
    STATE.tokenize_reply = ["not", "an", "object"]
    p = run_py(lp_args("tokreply.jsonl"))
    r = rows(out("tokreply.jsonl"))[0]
    b = r.get("logprob_boundary") or {}
    check(p.returncode == 0 and b.get("checked") is False and "no tokens" in (b.get("reason") or "")
          and r["correct"] is True, f"tokenize list: exit {p.returncode}, {b}")
    STATE.reset()
    STATE.dist_fn = weights_dist(lambda it, k: 5 if k == it["answer"] else 1)
    STATE.template_reply = ["a", "list"]
    p = run_py(lp_args("tmplreply.jsonl", items="PW01,PW02"))
    rs = rows(out("tmplreply.jsonl"))
    check(p.returncode == 2 and len(rs) == 2 and all("returned no prompt" in (x["error"] or "") for x in rs)
          and not completions(), f"template list: exit {p.returncode}, {[x.get('error') for x in rs]} "
                                 f"{p.stderr[-300:]}")
    return "tokenize list: boundary unchecked, run fine; template list: 2 error records, 0 completions, no crash"


# ── unittest wiring ──────────────────────────────────────────────────────────

class LogprobFailureTests(support.CaseTestCase):
    """The logprob Pick mode under failures (see the module docs)."""

    cases = (l10_server_failures_preflight_resume_and_kwargs_fallback,
             l11_adversarial_entries_are_ignored,
             l12_warmup_and_score_compatibility,
             l13_cut_characters_and_json_invalid_variants_are_not_letters,
             l14_truncated_candidate_lists_are_refused,
             l15_answer_prefix_boundary_is_checked_through_tokenize,
             l16_template_render_matches_the_generate_mode_request,
             l17_a_failed_order_counts_its_call,
             l18_non_finite_counts_neither_crash_nor_reach_the_record,
             l19_non_object_template_and_tokenize_replies)

    def setUp(self):
        STATE.reset()


if __name__ == "__main__":
    unittest.main()
