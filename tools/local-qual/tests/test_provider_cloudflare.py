#!/usr/bin/env python3
"""Tests for ``run.py --provider cloudflare``: Workers AI's free daily neuron allocation through the openai backend
(providers.py, provider_gate.py, provider_backend.py, cloud/cloudflare-neurons.json).

What the provider must guarantee, and the case that proves each part:

* w01: the request goes to ``<API root>/accounts/<account id>/ai/v1/chat/completions`` with the token in the
  Authorization header only; the record and the ledger carry the neurons computed from the reply's usage and the
  dated table; the account id appears in no record, ledger row or console line.
* w02: every refusal happens before anything is sent (exit 2): a model outside the table, a missing or malformed
  account id, the Global API Key or a legacy token, a neuron cap above the free allocation, a reasoning setting the
  model does not take, the knowledge suite (D047), an undocumented sampler, another host, OpenRouter's flags.
* w03: the neuron arithmetic on known values (doc 52's worked examples), and the data file's checks.
* w04: the daily neuron budget on both sides of the cap (exactly at it goes; one call over stops before sending),
  per UTC day and per account (every model's rows count, yesterday's do not); a run stops with exit 10 and the reset.
* w05: Cloudflare's error codes in both body shapes: 3036 (the day's allocation is used up) ends the run with exit
  10, 3040 (capacity) is retried, 5035 (a paid-only model) is a configuration stop; an error body echoing the account
  id or the token is redacted.
* w06: a call that used more neurons than its worst case stops the run (CostAnomaly, exit 4): the table or the cap
  does not match what the endpoint applies, and on Workers Paid that would be billed.
* w07: the request body per provider and model: the reasoning field each takes, the seed range (0 maps to 1 on
  Cloudflare), and no OpenRouter reasoning object.
* w08: redaction: every provider's key shape on every path, and on the provider path the account id (in any letter
  case) and Groq's organisation id; a redirect naming the account id and the token stops unfollowed and unshown.

Every case runs run.py (or the gate and the client in-process) against mock_server.py, in-process on 127.0.0.1, with
random dummy tokens and a random dummy account id: nothing is spent and no real endpoint is contacted. The final
sweep fails the module if a dummy token, the dummy account id or the dummy organisation id reached a file or a
console transcript.

Run the whole suite from the repository root with ``python -m unittest discover -s tools/local-qual/tests``.
"""
import datetime as _dt
import json
import os
import unittest

import cloud_support
import support
from provider_support import *  # noqa: F401,F403 - the shared fixtures the cases use by name

URL = None  # the mock's base URL while this module runs (set by setUpModule)
UTC = _dt.timezone.utc
T0 = _dt.datetime(2026, 9, 28, 12, 0, 0, tzinfo=UTC).timestamp()
GEMMA = {"in": 9091, "out": 27273}


def setUpModule():
    global URL
    URL = cloud_support.start("provider-cloudflare")


def tearDownModule():
    cloud_support.finish()


# ── Helpers ──────────────────────────────────────────────────────────────────

def swap(args, flag, value):
    """A copy of `args` with the value after `flag` replaced."""
    out_args = list(args)
    out_args[out_args.index(flag) + 1] = value
    return out_args


def neuron_gate(cap, clock, rows=(), model=CF_MODEL):
    """A NeuronGate at one neuron per token (rates 1e6 per million), with an estimate read from the body (``p``
    prompt tokens, ``c`` output cap), so a reservation is simply p + c neurons."""
    import provider_gate as pg
    return pg.NeuronGate(model, {"in": 1e6, "out": 1e6}, cap=cap, rpm=300, rows=rows,
                         estimate=lambda b: (b["p"], b["c"]), clock=lambda: clock[0], sleep=lambda s: None)


def call(g, call_id, prompt, completion, settle=True):
    """One attempt of 30 + 10 neurons worst case; settled at prompt + completion neurons unless `settle` is False."""
    g.begin_call({"p": 30, "c": 10}, call_id)
    stop = g.before_attempt()
    if stop is None and settle:
        g.after_attempt(200, {}, json.dumps({"usage": {"prompt_tokens": prompt, "completion_tokens": completion,
                                                       "total_tokens": prompt + completion}}))
    return stop


def ledger_row(model, neurons, when, call_id):
    """A reserve and a settle row of the Cloudflare quota ledger at `when` (an aware datetime)."""
    ts = when.isoformat(timespec="seconds")
    return [{"budget_event": "quota", "provider": "cloudflare", "model": model, "call_id": call_id, "attempt": 1,
             "unit": "neurons", "reserved": neurons, "ts": ts},
            {"budget_event": "quota_settle", "provider": "cloudflare", "model": model, "call_id": call_id,
             "attempt": 1, "unit": "neurons", "used": neurons, "status": 200, "ts": ts}]


# ── Basic functionality ──────────────────────────────────────────────────────

def w01_cloudflare_request_path_neurons_and_no_account_id_in_records():
    """A Cloudflare run posts to the account's /ai/v1 path with the token as a bearer header; the record's neurons
    equal usage times the dated table's rates; nothing it writes or prints holds the account id.

    Why: Workers AI reports no cost or neuron figure, so the tool's own count from the table is the only guard of the
    daily free allocation; and the account id, which the URL must carry, identifies the owner's account.
    """
    cf_state()
    o, led = out("w01.jsonl"), out("w01_ledger.jsonl")
    p = run_cf(cf_args("w01_ledger.jsonl") + ["--suite", "pick", "--items", "PW01", "--k", "1", "--out", o])
    check(p.returncode == 0, f"exit {p.returncode}: {p.stderr[-600:]}")
    reqs = chat_requests()
    check(len(reqs) == 1 and reqs[0]["path"] == f"/client/v4/accounts/{ACCOUNT_ID}/ai/v1/chat/completions"
          and reqs[0]["headers"].get("Authorization") == f"Bearer {CF_TOKEN}", "path or header")
    body = reqs[0]["body"]
    check(body.get("max_tokens") == 64 and body.get("model") == CF_MODEL and "reasoning" not in body
          and "reasoning_effort" not in body and body.get("seed", 0) >= 1, f"body fields {sorted(body)}")
    rec = calls(rows(o))[0]
    u = rec["usage"]
    want = u["prompt_tokens"] * GEMMA["in"] / 1e6 + u["completion_tokens"] * GEMMA["out"] / 1e6
    rg = rec["rate_gate"]
    check(rec["provider"] == "cloudflare" and rec["model"] == f"{CF_MODEL}@cloudflare" and rec["cost_usd"] == 0
          and abs(rg["neurons_call"] - want) < 1e-6 and abs(rg["neurons_today"] - want) < 1e-6
          and rg["neuron_cap"] == 9000 and rec["base_host"] == "127.0.0.1", f"record {rec}")
    s = quota_rows(led, "quota_settle")
    check(len(s) == 1 and abs(s[0]["used"] - want) < 1e-6 and s[0]["unit"] == "neurons", f"settle rows {s}")
    check(provider_clean(p, o, led), "the account id or a token reached the console or the files")
    # ── A dry run: nothing sent, no account id or token needed, the worst case named in neurons ──
    n = len(STATE.requests)
    d = run_cf(["--provider", "cloudflare", "--model", CF_MODEL, "--reasoning", "none", "--account-id-env", ACCT_ENV,
                "--suite", "pick", "--items", "PW01", "--dry-run"], key="", account="")
    check(d.returncode == 0 and len(STATE.requests) == n and '"max_tokens": 64' in d.stdout
          and "neurons for this request" in d.stderr, f"dry run: exit {d.returncode}, {d.stderr[-300:]!r}")
    return (f"1 call to /client/v4/accounts/<id>/ai/v1/chat/completions; {want:.4f} neurons recorded and settled; the "
            f"dry run names its worst case in neurons")


def w02_cloudflare_offline_refusals_send_nothing():
    """Every flag or setting a Cloudflare run cannot honour is refused before anything is sent (exit 2, the fix
    named).

    Why: an unknown model has no neuron rate, so no worst case; the Global API Key has full access to the account and
    a legacy token cannot be told from other text by the redaction; a cap above 10,000 neurons could reach billing on
    Workers Paid; the knowledge suite is combat-flavoured under D047.
    """
    cf_state()
    run_args = cf_args("w02_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "1", "--out", out("w02.jsonl")]
    cases = [
        (swap(run_args, "--model", "@cf/meta/llama-4-scout-17b-16e-instruct"), "not in the neuron table"),
        (run_args + ["--max-neurons-per-day", "10001"], "--max-neurons-per-day must be above 0 and at most 10000"),
        (run_args + ["--max-neurons-per-day", "0"], "--max-neurons-per-day must be above 0 and at most 10000"),
        (swap(run_args, "--reasoning", "low"), "no reasoning setting"),
        (swap(swap(run_args, "--model", "@cf/openai/gpt-oss-20b"), "--reasoning", "none"), "--reasoning low"),
        (swap(run_args, "--suite", "knowledge"), "D047"),
        (run_args + ["--min-p", "0.1"], "min_p"),
        (swap(run_args, "--base-url", "https://example.com/client/v4"), "sends its key only to"),
        (run_args + ["--free-only"], "drop --free-only"),
        (run_args + ["--max-tokens-per-minute", "100"], "applies to --provider groq"),
        (run_args + ["--rpm", "301"], "--rpm must be 1-300"),
    ]
    bad = []
    for args, needle in cases:
        p = run_cf(args)
        if not refused(p, needle):
            bad.append(f"{needle!r}: exit {p.returncode}, {p.stderr[-200:]!r}")
    for kw, needle in (({"account": ""}, "not set or empty"), ({"account": "xyz"}, "32"),
                       ({"key": "cfk_" + "a" * 40}, "Global API Key"), ({"key": "b" * 40}, "cfat_"),
                       ({"key": GROQ_KEY}, "cfat_")):
        p = run_cf(run_args, **kw)
        if not refused(p, needle):
            bad.append(f"{kw}: exit {p.returncode}, {p.stderr[-200:]!r}")
        elif ACCOUNT_ID in p.stderr + p.stdout:
            bad.append(f"{kw}: the account id was printed")
    check(not bad, "; ".join(bad))
    check(not STATE.requests, f"{len(STATE.requests)} requests reached the server")
    return f"{len(cases) + 5} refusals, each exit 2 with the fix named; 0 requests reached the server"


# ── Known values and the data file ───────────────────────────────────────────

def w03_neuron_arithmetic_and_table_checks():
    """Neurons per call: prompt tokens x in-rate + output tokens x out-rate, per million (doc 52's worked examples:
    Gemma 4 at 2,300 in and 300 out is about 29.1 neurons, Qwen3.8 at 2,000 and 2,000 about 664); output counts the
    larger of completion tokens, total minus prompt, and reasoning tokens; unreadable usage gives None. The shipped
    tables load; malformed ones are refused with the field named.

    Why: the count is the only guard of the free allocation, so a reply that reports reasoning apart from the
    completion must not be under-counted, and a broken table must never price calls at zero.
    """
    import provider_gate as pg
    import providers
    gemma = pg.neurons_for({"prompt_tokens": 2300, "completion_tokens": 300}, GEMMA)
    qwen = pg.neurons_for({"prompt_tokens": 2000, "completion_tokens": 2000}, {"in": 40909, "out": 290909})
    check(abs(gemma - (2300 * 9091 + 300 * 27273) / 1e6) < 1e-9 and 29.0 < gemma < 29.2, f"gemma {gemma}")
    check(abs(qwen - 663.636) < 0.001, f"qwen {qwen}")
    total = pg.neurons_for({"prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 150}, {"in": 0, "out": 1e6})
    reason = pg.neurons_for({"prompt_tokens": 100, "completion_tokens": 10,
                             "completion_tokens_details": {"reasoning_tokens": 40}}, {"in": 0, "out": 1e6})
    check(total == 50 and reason == 40, f"output counted as {total} and {reason}")
    for bad in ({}, {"prompt_tokens": 1}, {"prompt_tokens": -1, "completion_tokens": 1},
                {"prompt_tokens": True, "completion_tokens": 1}, {"prompt_tokens": "5", "completion_tokens": 1}, None):
        check(pg.neurons_for(bad, GEMMA) is None, f"neurons_for({bad!r}) = {pg.neurons_for(bad, GEMMA)!r}")
    cf = providers.load_table("cloudflare")
    groq = providers.load_table("groq")
    check(len(cf["models"]) == 8 and cf["free_neurons_per_day"] == 10000 and cf["read"] == "2026-09-28"
          and cf["models"][CF_MODEL] == dict(GEMMA, reasoning_efforts=None), f"cloudflare table {cf['models'].get(CF_MODEL)}")
    check(len(groq["models"]) == 4 and all(m["rpd"] == 1000 and m["tpm"] == 8000 for m in groq["models"].values()),
          "groq table")
    good = support.load_json(os.path.join(support.TOOL, "cloud", "cloudflare-neurons.json"))
    broken = {"no models": dict(good, models={}), "negative rate": dict(good, models={CF_MODEL: {"in": -1, "out": 5}}),
              "no source": {k: v for k, v in good.items() if k != "source"}, "bad date": dict(good, read="yesterday"),
              "other provider": dict(good, provider="groq"), "bool rate": dict(good, models={CF_MODEL: {"in": True,
                                                                                                         "out": 5}})}
    refused_fields = {}
    for name, table in broken.items():
        path = out(f"table_{len(refused_fields)}.json")
        write_text(path, json.dumps(table))
        try:
            providers.load_table("cloudflare", path)
            refused_fields[name] = None
        except ValueError as e:
            refused_fields[name] = str(e)[:60]
    check(all(refused_fields.values()), f"a malformed table loaded: {refused_fields}")
    return f"gemma {gemma:.4f}, qwen {qwen:.3f} neurons; {len(broken)} malformed tables refused"


# ── The daily budget (boundary tests) ────────────────────────────────────────

def w04_neuron_budget_both_sides_per_utc_day_and_per_account():
    """A call whose worst case lands exactly on the cap goes; the next one, one neuron over, stops (quota) before
    sending and names the next 00:00 UTC; yesterday's rows do not count; today's rows of another model do (the
    allocation is per account); a run whose cap is already used stops with exit 10 and 0 calls.

    How: one neuron per token; each attempt reserves 30 + 10 = 40 neurons. Settled 25, 25 and 10, then an unsettled
    reservation of 40: 25 + 25 + 10 + 40 = 100 = the cap.
    """
    t = [T0]
    g = neuron_gate(100.0, t)
    stops = [call(g, "a", 20, 5), call(g, "b", 20, 5), call(g, "c", 5, 5), call(g, "d", 0, 0, settle=False)]
    over = call(g, "e", 0, 0)
    check(stops == [None] * 4, f"calls up to the cap: {stops}")
    check(over is not None and over[0] == "quota" and "2026-09-29T00:00:00Z" in over[1] and "00:00 UTC" in over[1],
          f"one over: {over}")
    yesterday = ledger_row(CF_MODEL, 90.0, _dt.datetime(2026, 9, 27, 12, 0, tzinfo=UTC), "y")
    other = ledger_row("@cf/openai/gpt-oss-20b", 90.0, _dt.datetime(2026, 9, 28, 9, 0, tzinfo=UTC), "o")
    check(call(neuron_gate(100.0, [T0], rows=yesterday), "f", 1, 1) is None, "yesterday's neurons counted today")
    got = call(neuron_gate(100.0, [T0], rows=other), "g", 1, 1)
    check(got is not None and got[0] == "quota", f"another model's neurons today were not counted: {got}")
    # A cap below one call's worst case can never send anything: a configuration stop, not a wait for tomorrow.
    small = call(neuron_gate(30.0, [T0]), "h", 1, 1)
    check(small is not None and small[0] == "config" and "--num-predict" in small[1], f"cap below one call: {small}")
    # ── End to end: today's ledger already holds 8,999.99 of the default 9,000 neurons ──
    cf_state()
    led = out("w04_ledger.jsonl")
    write_text(led, "".join(json.dumps(r) + "\n" for r in ledger_row(CF_MODEL, 8999.99, _dt.datetime.now(UTC), "s")))
    o = out("w04.jsonl")
    p = run_cf(cf_args("w04_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "1", "--out", o])
    check(p.returncode == 10 and not chat_requests() and "00:00 UTC" in p.stderr
          and stop_rows(o)[-1]["stop"] == "DailyQuota", f"exit {p.returncode}, {p.stderr[-300:]!r}")
    return ("100 of 100 neurons went, 140 of 100 stopped naming 2026-09-29T00:00:00Z; per account, per UTC day; a cap "
            "below one call is a configuration stop; 8,999.99 of 9,000 used: exit 10 with 0 calls")


# ── Errors and stops ─────────────────────────────────────────────────────────

def w05_cloudflare_error_codes_in_both_body_shapes():
    """3036 (the day's free allocation is used up) ends the run with exit 10 and no retry, in the v4 envelope and in
    an OpenAI-style error; 3040 (capacity) is retried; 5035 (a paid-only model) stops with exit 5; an error body that
    echoes the account id and the token shows neither.

    Why: Cloudflare documents the codes but not the body shape of its OpenAI-compatible endpoint, and a retry of 3036
    only repeats the refusal (community reports say it can persist after the reset).
    """
    import provider_gate as pg
    results = {}
    scripts = {
        "3036 envelope": [cf_error(429, 3036, "You have used up your daily free allocation of 10,000 neurons. "
                                              "Please upgrade to Cloudflare's Workers Paid plan.")],
        "3036 openai": [{"status": 429, "body": {"error": {"code": 3036, "message": "daily free allocation used"}}}],
        "3040 then answer": [cf_error(429, 3040, "Capacity temporarily exceeded, please try again."),
                             {"status": 200, "body": "OK"}],
        "5035": [cf_error(403, 5035, "This model requires the Workers Paid plan.")],
        "echo": [cf_error(400, 7003, f"Could not route to /client/v4/accounts/{ACCOUNT_ID}/ai/v1 with {CF_TOKEN}")],
    }
    for name, script in scripts.items():
        STATE.reset()
        cf_state()
        STATE.queue = list(script)
        o = out(f"w05_{len(results)}.jsonl")
        p = run_cf(cf_args(f"w05_{len(results)}_ledger.jsonl") + ["--suite", "pick", "--items", "PW01", "--k", "1",
                                                                   "--out", o])
        results[name] = (p.returncode, len(chat_requests()), provider_clean(p, o))
    want = {"3036 envelope": (10, 1, True), "3036 openai": (10, 1, True), "3040 then answer": (0, 2, True),
            "5035": (5, 1, True), "echo": (5, 1, True)}
    check(results == want, f"got {results}")
    now = T0
    kinds = {c: pg.cloudflare_classify_429({}, cf_error(429, c, "x")["body"], now, 3.0)[0] for c in (3036, 3040, 999)}
    check(kinds == {3036: "daily", 3040: "upstream", 999: "minute"}, f"kinds {kinds}")
    check(pg.cloudflare_codes({"errors": [{"code": 3036}, {"code": "x"}], "error": {"code": 5035}}) == [3036, 5035],
          "codes from both shapes")
    return f"{results}; kinds {kinds}"


def w06_neurons_above_the_worst_case_stop_as_cost_anomaly():
    """A reply whose usage prices above the call's worst case stops the run (CostAnomaly, exit 4).

    Why: the worst case rests on the table's rates and the request's output cap; a reply beyond it means one of them
    does not hold for this endpoint, so the day's count can no longer be trusted, and on Workers Paid every neuron
    past the allocation is billed.
    """
    cf_state()
    STATE.reasoning_tokens = 5000  # completion tokens far above max_tokens 64
    o = out("w06.jsonl")
    p = run_cf(cf_args("w06_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "2", "--out", o])
    check(p.returncode == 4 and len(chat_requests()) == 1 and stop_rows(o)[-1]["stop"] == "CostAnomaly"
          and "worst case" in p.stderr, f"exit {p.returncode}, {p.stderr[-300:]!r}")
    return "5,064 output tokens on a 64-token cap: exit 4 CostAnomaly after 1 call"


def w07_request_body_per_provider_and_model():
    """Each provider gets its own reasoning field: Groq's gpt-oss reasoning_effort, Groq's Qwen3.8 reasoning_effort
    with reasoning_format parsed (never raw: refused in JSON mode), Cloudflare's efforts as listed, nothing for a
    model without a setting, and never OpenRouter's reasoning object; seed 0 goes to Cloudflare as 1 (its range starts
    at 1) and to Groq as 0.
    """
    import provider_backend
    import providers
    groq_t, cf_t = providers.load_table("groq"), providers.load_table("cloudflare")
    wires = {
        "groq gpt-oss low": providers.reasoning_wire("groq", GROQ_MODEL, groq_t["models"][GROQ_MODEL], {"effort": "low"}),
        "groq qwen none": providers.reasoning_wire("groq", "qwen/qwen3.8-27b", groq_t["models"]["qwen/qwen3.8-27b"],
                                                   {"effort": "none"}),
        "groq qwen medium": providers.reasoning_wire("groq", "qwen/qwen3.8-27b", groq_t["models"]["qwen/qwen3.8-27b"],
                                                     {"effort": "medium"}),
        "groq omit": providers.reasoning_wire("groq", GROQ_MODEL, groq_t["models"][GROQ_MODEL], None),
        "cf qwen xhigh": providers.reasoning_wire("cloudflare", "@cf/qwen/qwen3.8-27b",
                                                  cf_t["models"]["@cf/qwen/qwen3.8-27b"], {"effort": "xhigh"}),
        "cf gemma none": providers.reasoning_wire("cloudflare", CF_MODEL, cf_t["models"][CF_MODEL], {"effort": "none"}),
    }
    check(wires == {"groq gpt-oss low": {"reasoning_effort": "low"}, "groq qwen none": {"reasoning_effort": "none"},
                    "groq qwen medium": {"reasoning_effort": "medium", "reasoning_format": "parsed"},
                    "groq omit": {}, "cf qwen xhigh": {"reasoning_effort": "xhigh"}, "cf gemma none": {}},
          f"wires {wires}")
    for prov, model, table, value in (("groq", GROQ_MODEL, groq_t, {"effort": "none"}),
                                      ("groq", GROQ_MODEL, groq_t, {"effort": "low", "max_tokens": 5}),
                                      ("cloudflare", CF_MODEL, cf_t, {"effort": "low"})):
        try:
            providers.reasoning_wire(prov, model, table["models"][model], value)
            check(False, f"{prov} {model} {value} was accepted")
        except ValueError:
            pass
    msgs = [{"role": "user", "content": "x"}]
    cf = provider_backend.ProviderBackend(
        f"http://127.0.0.1:9/client/v4/accounts/{ACCOUNT_ID}/ai/v1", 5.0, CF_TOKEN, reasoning={"effort": "none"},
        provider={"provider": "cloudflare", "model": CF_MODEL, "account_id": ACCOUNT_ID, "reasoning_wire": {}})
    gq = provider_backend.ProviderBackend(
        "http://127.0.0.1:9/openai/v1", 5.0, GROQ_KEY, reasoning={"effort": "low"},
        provider={"provider": "groq", "model": GROQ_MODEL, "account_id": None,
                  "reasoning_wire": {"reasoning_effort": "low"}}, max_tokens_field="max_completion_tokens")
    b0, b5 = (cf.payload(CF_MODEL, msgs, None, 0.6, s, 64, 8192, {}, "pick") for s in (0, 5))
    g0 = gq.payload(GROQ_MODEL, msgs, None, 0.6, 0, 64, 8192, {}, "pick")
    check(b0["seed"] == 1 and b5["seed"] == 5 and g0["seed"] == 0 and "reasoning" not in b0 and "reasoning" not in g0
          and g0.get("reasoning_effort") == "low" and g0.get("max_completion_tokens") == 64 and b0.get("max_tokens") == 64,
          f"cloudflare {b0}, groq {g0}")
    return f"{len(wires)} reasoning mappings and 3 refusals; seed 0 -> 1 on Cloudflare only"


def w08_redaction_of_every_provider_secret():
    """Every string the client returns loses any provider's key shape (on every path, OpenRouter's included), and on
    the provider path also the account id in any letter case and Groq's organisation id; a redirect whose Location
    names the account id and the token stops the run unfollowed (exit 5) and shows neither.

    Why: a server may echo a key or the account id in an error body, a header or a redirect target, and every such
    string can end up in a record, a ledger row or the console.
    """
    import cloud_backend
    import provider_backend
    others = ["gsk_" + "a" * 52, "cfat_" + "b" * 48, "cfut_" + "c" * 48, "cfk_" + "d" * 40, "sk-or-v1-" + "e" * 64]
    plain = cloud_backend.OpenAICompatBackend("http://127.0.0.1:9/api/v1", 5.0, None)
    shown = plain.redact("keys: " + " ".join(others))
    check(not any(k in shown for k in others) and shown.count("[REDACTED]") == len(others), f"base path: {shown}")
    cf = provider_backend.ProviderBackend(
        f"http://127.0.0.1:9/client/v4/accounts/{ACCOUNT_ID}/ai/v1", 5.0, CF_TOKEN, reasoning=None,
        provider={"provider": "cloudflare", "model": CF_MODEL, "account_id": ACCOUNT_ID, "reasoning_wire": {}})
    text = f"acct {ACCOUNT_ID} ACCT {ACCOUNT_ID.upper()} tok {CF_TOKEN} org {ORG_ID} " + " ".join(others)
    got = cf.redact(text)
    check(not any(s in got or s.upper() in got for s in (ACCOUNT_ID, CF_TOKEN, ORG_ID)) and "[ACCOUNT]" in got
          and not any(k in got for k in others), f"provider path: {got}")
    cf_state()
    STATE.queue = [{"status": 302, "body": {"error": "moved"},
                    "headers": {"Location": f"https://relay.example/{ACCOUNT_ID}/v1?token={CF_TOKEN}"}}]
    o = out("w08.jsonl")
    p = run_cf(cf_args("w08_ledger.jsonl") + ["--suite", "pick", "--items", "PW01", "--k", "1", "--out", o])
    check(p.returncode == 5 and len(chat_requests()) == 1 and provider_clean(p, o, out("w08_ledger.jsonl")),
          f"redirect: exit {p.returncode}, {p.stderr[-300:]!r}")
    return "5 key shapes redacted on the base path; account id (both cases), token and org id on the provider path"


# ── unittest wiring ──────────────────────────────────────────────────────────

class CloudflareProviderTests(support.CaseTestCase):
    """--provider cloudflare (see the module docs)."""

    cases = (w01_cloudflare_request_path_neurons_and_no_account_id_in_records,
             w02_cloudflare_offline_refusals_send_nothing,
             w03_neuron_arithmetic_and_table_checks,
             w04_neuron_budget_both_sides_per_utc_day_and_per_account,
             w05_cloudflare_error_codes_in_both_body_shapes,
             w06_neurons_above_the_worst_case_stop_as_cost_anomaly,
             w07_request_body_per_provider_and_model,
             w08_redaction_of_every_provider_secret)

    def setUp(self):
        STATE.reset()


if __name__ == "__main__":
    unittest.main()
