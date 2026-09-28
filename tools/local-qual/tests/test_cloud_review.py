#!/usr/bin/env python3
"""Review of the merged paid path (t63-t66): billing the cap cannot price, a thinking budget the worst case missed,
a key the record scrub could not find, and a sampler pin OpenRouter does not know by that name.

Each case encodes one gap found by the adversarial review after the cloud backend, the free-only mode, the logprob
mode, the scaffold arms and the presets were merged into one tool; each failed on the merged code and passes now:

* t63: ``--extra-body`` accepted ``service_tier``, ``modalities`` and ``audio``, which bill at rates the price flags
  do not name (a priority tier, audio or image output); on an endpoint that reports no cost the ledger would then
  count every call at the flags' lower rate, with no cost anomaly to stop the run.
* t64: ``--reasoning '{"max_tokens": 5000.0}'`` (or ``"5000"``, ``true``) went out as a thinking budget while the
  worst case added nothing for it, because budget.py counts only an integer ``reasoning.max_tokens``.
* t65: a key containing ``"`` or ``\\`` passed the key check, but records and ledgers are JSON lines, where those
  characters are written escaped; a key echoed inside a nested object (``usage``) reached the file in that escaped
  form, which the last scrub before every write (an exact-text replacement) cannot find.
* t66: ``--repeat-penalty`` goes out as ``repeat_penalty``, which OpenRouter's parameter list names
  ``repetition_penalty``, so on OpenRouter the pin was most likely dropped while the record said it was sent; the
  body stays as it was (existing command lines keep their bytes) and the run now says so at the start.

Every case runs run.py as a child process against mock_server.py (in-process on 127.0.0.1): nothing is spent and no
real endpoint is contacted. cloud_support.py holds the dummy keys and the final key sweep, which also looks for the
JSON-escaped forms of this module's dummy keys.

Run the whole suite from the repository root with ``python -m unittest discover -s tools/local-qual/tests``.
"""
import json
import secrets
import unittest

import cloud_support
import support
from cloud_support import *  # noqa: F401,F403 - the shared fixtures the cases use by name

URL = None  # the mock's base URL while this module runs (set by setUpModule)


def setUpModule():
    global URL
    URL = cloud_support.start("cloud-review")


def tearDownModule():
    cloud_support.finish()


# ── Helpers ──────────────────────────────────────────────────────────────────

def json_objects(text):
    """Every top-level JSON object printed in `text`, in order (a dry run prints the body, the scoring fields and
    the worst case one after another)."""
    found, dec, i = [], json.JSONDecoder(), 0
    while True:
        i = text.find("{", i)
        if i < 0:
            return found
        try:
            obj, end = dec.raw_decode(text, i)
        except ValueError:
            i += 1
            continue
        found.append(obj)
        i = end


def worst_case(p):
    """The worst case a dry run printed ({prompt_tokens_est, output_cap, usd}), or None."""
    return next((o["worst_case_per_attempt"] for o in json_objects(p.stdout) if "worst_case_per_attempt" in o), None)


# ── Security edge cases ──────────────────────────────────────────────────────

def t63_extra_body_refuses_fields_billed_at_rates_the_flags_do_not_name():
    """--extra-body may not set service_tier, modalities or audio; each is refused before any request.

    Why: the cap holds only while every token is priced at --price-in and --price-out. OpenAI's priority tier bills
    more per token than its list price, and audio or image output bills per audio token or per image; on an endpoint
    that reports no cost (OpenAI's own API) the ledger would count such a call at the flags' lower rate, and the cost
    anomaly check, which compares with that same computed figure, could not see it.

    How: one run per field (exit 2, the field named, the key never echoed, 0 requests); a field that bills nothing
    (``user``) still passes a dry run.
    """
    common = ["--suite", "pick", "--k", "1", "--limit", "1", "--max-usd", "1", "--out", out("billing.jsonl")]
    cases = [("service_tier", {"service_tier": "priority"}),
             ("modalities", {"modalities": ["text", "audio"]}),
             ("audio", {"audio": {"voice": "alloy", "format": "wav"}})]
    bad = []
    for field, extra in cases:
        q = run_tool(base(URL) + common + ["--extra-body", json.dumps(extra)])
        if not refused(q, field) or KEY in q.stdout + q.stderr:
            bad.append(f"{field}: exit {q.returncode}, stderr {q.stderr.strip()[-160:]!r}")
    check(not bad, "; ".join(bad))
    check(STATE.count() == 0, f"{STATE.count()} requests reached the server during the refusals")
    q = run_tool(base(URL) + ["--suite", "pick", "--items", "PW01", "--dry-run", "--extra-body", '{"user": "qual"}'])
    body = json_objects(q.stdout)[0] if q.returncode == 0 else {}
    check(body.get("user") == "qual", f"a field that bills nothing was refused: exit {q.returncode} {q.stderr[-200:]}")
    return f"{len(cases)} billing fields refused (exit 2, 0 requests, key never echoed); 'user' still passes"


def t64_reasoning_budget_must_be_a_whole_positive_token_count():
    """--reasoning '{"max_tokens": N}' is refused unless N is a whole number of tokens above 0.

    Why: the worst case adds reasoning.max_tokens to the output cap only when it is an integer, because only then is
    it a token count; 5000.0, "5000" or true went out to the provider as a thinking budget that the reservation never
    counted, so a call could cost up to that many output tokens more than the cap allowed for (the cost-anomaly stop
    then comes one paid call late).

    How: six malformed budgets are refused (exit 2, 0 requests); a valid one (64) raises the dry run's worst-case
    output cap by exactly 64 over the same request with --reasoning none.
    """
    dry = ["--suite", "pick", "--items", "PW01", "--dry-run", "--max-usd", "1"]
    bad = []
    for value in ("5000.0", '"5000"', "true", "0", "-8", "null"):
        args = base(URL)
        args[args.index("--reasoning") + 1] = '{"max_tokens": ' + value + "}"
        q = run_tool(args + ["--suite", "pick", "--k", "1", "--limit", "1", "--max-usd", "1",
                             "--out", out("budget_reasoning.jsonl")])
        if not refused(q, "max_tokens"):
            bad.append(f"max_tokens {value}: exit {q.returncode}, stderr {q.stderr.strip()[-160:]!r}")
    check(not bad, "; ".join(bad))
    check(STATE.count() == 0, f"{STATE.count()} requests reached the server during the refusals")
    plain = worst_case(run_tool(base(URL) + dry))
    args = base(URL)
    args[args.index("--reasoning") + 1] = '{"max_tokens": 64}'
    budgeted = worst_case(run_tool(args + dry))
    check(plain and budgeted and budgeted["output_cap"] - plain["output_cap"] == 64,
          f"worst cases: none {plain}, max_tokens 64 {budgeted}")
    return (f"6 malformed thinking budgets refused (exit 2, 0 requests); max_tokens 64 raises the worst-case output "
            f"cap from {plain['output_cap']} to {budgeted['output_cap']}")


def t65_key_with_a_character_json_escapes_is_refused():
    """A key containing a double quote or a backslash is refused before any request, and never printed.

    Why: records and ledgers are JSON lines, and the last scrub before a line is written replaces the key's exact
    text. JSON writes '"' as '\\"' and '\\' as '\\\\', so a key with either character, echoed by an endpoint inside
    a nested object such as ``usage``, reached the file in an escaped form the scrub could not find (every other
    printable ASCII character is written as itself). Real API keys never contain them.

    How: two random dummy keys, one per character (added, with their escaped forms, to the final sweep): exit 2
    naming the characters, neither form on the console, 0 requests.
    """
    common = ["--suite", "pick", "--k", "1", "--limit", "1", "--max-usd", "1", "--out", out("quote_key.jsonl")]
    bad = []
    for ch in ('"', "\\"):
        key = "sk-mock-" + secrets.token_hex(6) + ch + secrets.token_hex(6)
        SWEEP.extend([key, json.dumps(key)[1:-1]])
        q = run_tool(base(URL) + common, env_extra={ENV_NAME: key})
        shown = q.stdout + q.stderr
        if not refused(q, "quote or backslash") or key in shown or json.dumps(key)[1:-1] in shown:
            bad.append(f"key with {ch!r}: exit {q.returncode}, stderr {q.stderr.strip()[-160:]!r}")
    check(not bad, "; ".join(bad))
    check(STATE.count() == 0, f"{STATE.count()} requests reached the server during the refusals")
    return "keys with a quote or a backslash refused (exit 2, 0 requests, neither form printed)"


def t66_repeat_penalty_on_openrouter_is_warned_about():
    """A run that sends --repeat-penalty to OpenRouter is warned that OpenRouter names the parameter
    repetition_penalty, with the --extra-body form to use; other hosts and other sampler pins get no warning.

    Why: the openai backend sends the pin as ``repeat_penalty`` (llama-server's name), which is not in OpenRouter's
    parameter list, so OpenRouter most likely drops it while the record's ``sampler_sent`` says it was sent: a
    silent change of the measured sampler. The request itself must not change (existing command lines keep their
    exact bodies), so the fix is to say so at the start of the run, where the flag can still be swapped.

    How: ``cloud_run.sampler_warnings`` directly, then ``cloud_run.run_info`` with an OpenRouter base and the pin,
    capturing stderr (nothing is sent: run_info only describes the endpoint).
    """
    import contextlib
    import io
    import types
    import cloud_run
    warn = cloud_run.sampler_warnings("openrouter.ai", {"repeat_penalty": 1.1, "top_k": 20})
    check(len(warn) == 1 and "repetition_penalty" in warn[0] and "--extra-body" in warn[0], f"warnings {warn}")
    check(cloud_run.sampler_warnings("127.0.0.1", {"repeat_penalty": 1.1}) == [], "a non-OpenRouter host was warned")
    check(cloud_run.sampler_warnings("openrouter.ai", {"top_k": 20}) == [], "another pin was warned about")
    args = types.SimpleNamespace(endpoint_tag=None, label=None, free_only=False, schema_normalise=False,
                                 price_in=1.0, price_out=1.0, price_cache_read=None, price_as_of="x",
                                 price_source="y", max_usd=1.0)
    backend = types.SimpleNamespace(base="https://openrouter.ai/api/v1")
    settings = {"extra_body": {"provider": {"only": ["a/b"], "allow_fallbacks": False}}, "drop": (), "strip": ()}
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        cloud_run.run_info(args, backend, "m/x", settings, {"repeat_penalty": 1.1})
    check("repetition_penalty" in err.getvalue(), f"run_info printed no warning: {err.getvalue()!r}")
    return "OpenRouter + --repeat-penalty: one warning naming repetition_penalty and --extra-body; none elsewhere"


# ── unittest wiring ──────────────────────────────────────────────────────────

class MergedReviewTests(support.CaseTestCase):
    """Gaps found reviewing the merged paid path (see the module docs)."""

    cases = (t63_extra_body_refuses_fields_billed_at_rates_the_flags_do_not_name,
             t64_reasoning_budget_must_be_a_whole_positive_token_count,
             t65_key_with_a_character_json_escapes_is_refused,
             t66_repeat_penalty_on_openrouter_is_warned_about)

    def setUp(self):
        STATE.reset()


if __name__ == "__main__":
    unittest.main()
