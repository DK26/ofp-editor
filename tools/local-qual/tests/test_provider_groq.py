#!/usr/bin/env python3
"""Tests for ``run.py --provider groq``: Groq's free plan through the openai backend (providers.py,
provider_gate.py, provider_backend.py).

What the provider must guarantee, and the case that proves each part:

* g01: the request goes to Groq's OpenAI-compatible base with the key in the Authorization header only, in Groq's
  shape (max_completion_tokens, reasoning_effort instead of OpenRouter's reasoning object, a strict-mode schema copy,
  no parameter Groq rejects or does not document); records and ledger rows name the provider, the model and the
  tokens counted; a dry run sends nothing and needs no key.
* g02: every refusal happens before anything is sent (exit 2): OpenRouter's flags, a spend, no ledger, a model
  outside the free-plan table, a reasoning setting the model does not take, undocumented samplers, another host,
  the text and knowledge suites (D047), caps above the free plan, a best-effort-only model on a strict arm, and a key
  that is not shaped like a Groq key.
* g03, g04: the client caps on both sides of each limit: requests and tokens per rolling minute (the gate waits),
  per rolling 24 hours (the run stops and names when to resume), and the server's own remaining counts from the
  x-ratelimit-* headers; ledger rows of another model do not count.
* g05: the header parsers (Go-style durations, integers) on known and hostile values, and the free-plan check.
* g06: Groq's 429s: a per-minute limit waits for retry-after and succeeds; a per-day limit ends the run (exit 10)
  with the resume time; the organisation id in the message never reaches a record or the console.
* g07: anything that means money could be spent stops the run with exit 9: limit headers above the free plan, a
  reported cost, another model answering.
* g08: separate runs share the ledger's count; one Groq run at a time per user (a lock beside the key store).

Every case runs run.py (or the gate in-process) against mock_server.py, in-process on 127.0.0.1, with random dummy
keys: nothing is spent and no real endpoint is contacted. The final sweep fails the module if a dummy key, the
dummy organisation id or the dummy account id reached a file or a console transcript.

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
T0 = _dt.datetime(2026, 9, 28, 12, 0, 0, tzinfo=_dt.timezone.utc).timestamp()
LIMITS = {"rpm": 30, "rpd": 1000, "tpm": 8000, "tpd": 200000}


def setUpModule():
    global URL
    URL = cloud_support.start("provider-groq")


def tearDownModule():
    cloud_support.finish()


# ── Helpers ──────────────────────────────────────────────────────────────────

def swap(args, flag, value):
    """A copy of `args` with the value after `flag` replaced."""
    out_args = list(args)
    out_args[out_args.index(flag) + 1] = value
    return out_args


def usage_body(prompt=100, completion=20):
    """A chat reply body that carries only usage (what the gate reads after an attempt)."""
    return json.dumps({"usage": {"prompt_tokens": prompt, "completion_tokens": completion,
                                 "total_tokens": prompt + completion}})


class Clock:
    """A fake clock whose sleep moves it forward and records each wait."""

    def __init__(self, t=T0):
        self.t, self.slept = t, []

    def now(self):
        return self.t

    def sleep(self, s):
        self.slept.append(s)
        self.t += s


def gate(caps, clock, rows=(), reserve=5):
    """A GroqGate for GROQ_MODEL with an estimate read from the body (``p`` prompt tokens, ``c`` output cap)."""
    import provider_gate as pg
    return pg.GroqGate(GROQ_MODEL, LIMITS, dict(LIMITS, **caps), rows=rows, reserve=reserve,
                       estimate=lambda b: (b["p"], b["c"]), clock=clock.now, sleep=clock.sleep)


def attempt(g, call_id, body=None, status=200, headers=None, raw=None):
    """One attempt through the gate: begin, check, and (when sent) settle; returns the check's stop or None."""
    g.begin_call(body or {"p": 200, "c": 50}, call_id)
    stop = g.before_attempt()
    if stop is None:
        g.after_attempt(status, headers or {}, usage_body() if raw is None else raw)
    return stop


# ── Basic functionality ──────────────────────────────────────────────────────

def g01_groq_request_shape_base_url_and_records():
    """A Groq run sends Groq's request shape to its base URL, records the provider and the tokens counted, and a dry
    run sends nothing without needing a key.

    Why: Groq returns 400 for fields it does not take (logprobs, n > 1, messages[].name) and documents
    max_completion_tokens and reasoning_effort, not OpenRouter's reasoning object; a strict schema needs every
    property required and additionalProperties false. The ledger rows are what later runs count against the free
    plan's per-model limits, so they must name the provider, the model and the tokens.
    """
    groq_state()
    o, led = out("g01.jsonl"), out("g01_ledger.jsonl")
    p = run_groq(groq_args("g01_ledger.jsonl") + ["--suite", "pick", "--items", "PW01", "--k", "1", "--out", o])
    check(p.returncode == 0, f"exit {p.returncode}: {p.stderr[-600:]}")
    reqs = chat_requests()
    check(len(reqs) == 1 and reqs[0]["path"] == "/api/v1/chat/completions"
          and reqs[0]["headers"].get("Authorization") == f"Bearer {GROQ_KEY}", f"{[r['path'] for r in reqs]}")
    body = reqs[0]["body"]
    check(body.get("max_completion_tokens") == 64 and "max_tokens" not in body and body.get("reasoning_effort") == "low"
          and "reasoning" not in body and "reasoning_format" not in body and isinstance(body.get("seed"), int),
          f"body fields {sorted(body)}")
    wire = body["response_format"]["json_schema"]
    check(wire["strict"] is True and wire["schema"].get("additionalProperties") is False, f"schema {wire}")
    check(not any(k in body for k in ("top_k", "min_p", "repeat_penalty", "logprobs", "top_logprobs", "n",
                                      "logit_bias", "provider")), f"a field Groq rejects was sent: {sorted(body)}")
    rec = calls(rows(o))[0]
    check(rec["provider"] == "groq" and rec["model"] == f"{GROQ_MODEL}@groq" and rec["cost_usd"] == 0
          and rec["error"] is None and rec["reasoning_sent"] == {"reasoning_effort": "low"}, f"record {rec}")
    used = rec["usage"]["prompt_tokens"] + rec["usage"]["completion_tokens"]
    rg = rec["rate_gate"]
    check(rg["requests_24h"] == 1 and rg["tokens_24h"] == used and rg["server_requests_left"] == 999,
          f"rate_gate {rg}")
    q, s = quota_rows(led), quota_rows(led, "quota_settle")
    check(len(q) == 1 and q[0]["provider"] == "groq" and q[0]["model"] == GROQ_MODEL and q[0]["unit"] == "tokens"
          and q[0]["reserved"] > used and len(s) == 1 and s[0]["used"] == used, f"quota rows {q} {s}")
    check(provider_clean(p, o, led), "a dummy secret reached the console or the files")
    # ── A dry run: the first body, nothing sent, no key and no ledger needed ──
    n = len(STATE.requests)
    d = run_groq(["--provider", "groq", "--model", GROQ_MODEL, "--reasoning", "low", "--suite", "pick", "--items",
                  "PW01", "--dry-run"], key="")
    check(d.returncode == 0 and len(STATE.requests) == n and '"reasoning_effort": "low"' in d.stdout
          and '"max_completion_tokens": 64' in d.stdout, f"dry run: exit {d.returncode}, {d.stderr[-300:]}")
    # The worst case in the provider's own unit (its USD worst case is always 0, which says nothing).
    check("reserves up to" in d.stderr and "tokens for this request" in d.stderr, f"dry run note: {d.stderr[-300:]!r}")
    return (f"1 call to /api/v1/chat/completions with max_completion_tokens and reasoning_effort low; record "
            f"provider groq, {used} tokens counted in the ledger; the dry run sent nothing")


def g02_groq_offline_refusals_send_nothing():
    """Every flag a Groq run cannot honour is refused before anything is sent (exit 2, the fix named).

    Why: each of these would either spend (a price, OpenRouter's key check), lose the day's count (no ledger), send
    a request Groq answers with 400 or silently ignores (JSON reasoning, undocumented samplers, a strict schema on a
    best-effort model), exceed the free plan (caps above its limits), send the key to another host, or send
    combat-flavoured suites to a host whose terms carry a violent-content clause (D047 item 3).
    """
    groq_state()
    run_args = groq_args("g02_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "1", "--out",
                                                out("g02.jsonl")]
    no_ledger = run_args[:run_args.index("--ledger")] + run_args[run_args.index("--ledger") + 2:]
    cases = [
        (run_args + ["--free-only"], "drop --free-only"),
        (run_args + ["--max-usd", "1"], "spends nothing"),
        (run_args + ["--key-check"], "--key-check"),
        (no_ledger, "needs --ledger"),
        (swap(run_args, "--model", "meta-llama/llama-3.3-70b-versatile"), "not in the free-plan table"),
        (swap(run_args, "--reasoning", "none"), "--reasoning low"),
        (swap(run_args, "--reasoning", '{"effort": "low"}'), "effort word"),
        (run_args + ["--top-k", "20"], "top_k"),
        (swap(run_args, "--base-url", "https://example.com/openai/v1"), "sends its key only to"),
        (swap(run_args, "--suite", "text"), "D047"),
        (swap(run_args, "--suite", "knowledge"), "D047"),
        (run_args + ["--rpm", "31"], "--rpm must be 1-30"),
        (run_args + ["--max-requests-per-day", "1001"], "must be 1-1000"),
        (run_args + ["--max-tokens-per-minute", "8001"], "must be 1-8000"),
        (run_args + ["--max-tokens-per-day", "200001"], "must be 1-200000"),
        (run_args + ["--max-neurons-per-day", "5"], "applies to --provider cloudflare"),
        (swap(run_args, "--backend", "llamacpp"), "openai backend"),
        (swap(run_args, "--model", "openai/gpt-oss-safeguard-20b"), "--schema-mode none"),
    ]
    bad = []
    for args, needle in cases:
        p = run_groq(args)
        if not refused(p, needle):
            bad.append(f"{needle!r}: exit {p.returncode}, {p.stderr[-200:]!r}")
    for key, needle in (("sk-or-v1-" + "0" * 64, "does not look like a Groq key"), ("", "not set or empty")):
        p = run_groq(run_args, key=key)
        if not refused(p, needle):
            bad.append(f"key {needle!r}: exit {p.returncode}, {p.stderr[-200:]!r}")
    check(not bad, "; ".join(bad))
    check(not STATE.requests, f"{len(STATE.requests)} requests reached the server")
    return f"{len(cases) + 2} refusals, each exit 2 with the fix named; 0 requests reached the server"


# ── The client caps (boundary tests) ─────────────────────────────────────────

def g03_groq_minute_caps_wait_on_both_sides():
    """Requests and tokens per rolling minute: exactly at a cap goes at once, one over waits until the window has
    room; the server's own remaining tokens (x-ratelimit-remaining-tokens) wait for their reset.

    Why: Groq's free plan allows 30 requests and 8,000 tokens a minute per model; a burst over them costs a 429 and a
    retry, and the tokens-per-minute header is the only live view of the organisation's window (other runs, other
    machines).

    How: a fake clock; each attempt reserves 250 tokens (200 prompt estimate + 50 cap) and settles 120.
    """
    # ── Requests: 3 a minute; the fourth waits for the oldest to leave the window ──
    c = Clock()
    g = gate({"rpm": 3}, c)
    for i in range(3):
        check(attempt(g, f"r{i}") is None, f"attempt {i}")
        c.t += 1
    check(c.slept == [], f"waited {c.slept} under the cap")
    check(attempt(g, "r3") is None and len(c.slept) == 1 and 56.9 < c.slept[0] < 57.2,
          f"fourth attempt waited {c.slept}")
    # ── Tokens: 3 x 120 settled + 250 reserved = 610 ──
    exact, over = Clock(), Clock()
    ga, gb = gate({"tpm": 610}, exact), gate({"tpm": 609}, over)
    for g2, ck in ((ga, exact), (gb, over)):
        for i in range(3):
            attempt(g2, f"t{i}")
            ck.t += 1
        attempt(g2, "t3")
    check(exact.slept == [] and len(over.slept) == 1 and over.slept[0] > 50,
          f"at the token cap waited {exact.slept}; one token over waited {over.slept}")
    # ── The server's remaining tokens: 100 left, 250 needed -> wait for the reset (7.66 s) ──
    s1, s2 = Clock(), Clock()
    g1, g2 = gate({}, s1), gate({}, s2)
    attempt(g1, "s0", headers={"x-ratelimit-remaining-tokens": "100", "x-ratelimit-reset-tokens": "7.66s"})
    attempt(g2, "s0", headers={"x-ratelimit-remaining-tokens": "250", "x-ratelimit-reset-tokens": "7.66s"})
    check(attempt(g1, "s1") is None and len(s1.slept) == 1 and 7.6 < s1.slept[0] < 7.8, f"server wait {s1.slept}")
    check(attempt(g2, "s1") is None and s2.slept == [], f"enough server tokens waited {s2.slept}")
    return (f"requests: 3 at once, the 4th waited {c.slept[0]:.2f} s; tokens: 610 of 610 went at once, 610 of 609 "
            f"waited {over.slept[0]:.2f} s; server tokens 100 < 250 waited {s1.slept[0]:.2f} s, 250 went at once")


def g04_groq_day_caps_stop_on_both_sides_and_count_per_model():
    """Requests and tokens per rolling 24 hours: exactly at a cap goes, one over stops (quota) and names when the
    oldest counted request leaves the window; the server's remaining requests less the reserve stop the run too;
    ledger rows of another model do not count, rows of this model do (a run exits 10 before sending).

    Why: Groq counts per model and per organisation, and how its daily windows reset is not documented, so the gate
    counts over the last 24 hours, which is never looser than a calendar day.
    """
    import provider_gate as pg
    c = Clock()
    g = gate({"rpd": 3}, c)
    for i in range(3):
        check(attempt(g, f"d{i}") is None, f"day attempt {i}")
        c.t += 61
    stop = attempt(g, "d3")
    resume = _dt.datetime.fromtimestamp(T0 + 86400 + 1, _dt.timezone.utc).strftime("%Y-%m-%dT%H:%M")
    check(stop is not None and stop[0] == "quota" and "resume after" in stop[1] and resume in stop[1],
          f"fourth request of the day: {stop}")
    c.t = T0 + 86400 + 1.5
    check(attempt(g, "d4") is None, "a request after the oldest left the 24-hour window was refused")
    # ── Tokens per 24 hours: 3 x 120 + 250 = 610 ──
    for cap, want in ((610, None), (609, "quota")):
        ck = Clock()
        gt = gate({"tpd": cap}, ck)
        for i in range(3):
            attempt(gt, f"k{i}")
            ck.t += 61
        got = attempt(gt, "k3")
        check((got is None) if want is None else (got is not None and got[0] == want), f"tpd {cap}: {got}")
    # ── The server's remaining requests (x-ratelimit-remaining-requests) less the reserve of 5 ──
    ck = Clock()
    gs = gate({}, ck)
    attempt(gs, "v0", headers={"x-ratelimit-remaining-requests": "6"})
    check(attempt(gs, "v1") is None, "6 left with 5 in reserve refused the next request")
    got = attempt(gs, "v2")
    check(got is not None and got[0] == "quota" and "Groq reports" in got[1], f"5 left: {got}")
    # ── End to end: a ledger with 950 of this model's requests in the last hour ──
    now = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(minutes=30)
    ts = now.isoformat(timespec="seconds")

    def seed(path, model):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            for i in range(950):
                f.write(json.dumps({"budget_event": "quota", "provider": "groq", "model": model, "call_id": f"s{i}",
                                    "attempt": 1, "unit": "tokens", "reserved": 50, "ts": ts}) + "\n")
                f.write(json.dumps({"budget_event": "quota_settle", "provider": "groq", "model": model,
                                    "call_id": f"s{i}", "attempt": 1, "unit": "tokens", "used": 10, "status": 200,
                                    "ts": ts}) + "\n")
    groq_state()
    seed(out("g04_full.jsonl"), GROQ_MODEL)
    seed(out("g04_other.jsonl"), "openai/gpt-oss-120b")
    full = run_groq(groq_args("g04_full.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "1", "--out",
                                                   out("g04a.jsonl")])
    check(full.returncode == 10 and not chat_requests() and "resume after" in full.stderr
          and stop_rows(out("g04a.jsonl"))[-1]["stop"] == "DailyQuota",
          f"950 of 950 used: exit {full.returncode}, {len(chat_requests())} calls, {full.stderr[-300:]!r}")
    other = run_groq(groq_args("g04_other.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "1", "--out",
                                                     out("g04b.jsonl")])
    check(other.returncode == 0 and len(chat_requests()) == 1, f"another model's rows: exit {other.returncode}")
    check(pg.DAY_S == 86400, "the window is 24 hours")
    return ("3 of 3 requests went, the 4th stopped naming the resume time; 610 of 610 tokens went, 610 of 609 "
            "stopped; the server's 6 left went once (reserve 5); 950 rows of this model: exit 10 with 0 calls; "
            "950 rows of another model: the run went")


# ── Parsers and the free-plan check ──────────────────────────────────────────

def g05_groq_header_parsers_known_and_hostile_values():
    """Go-style reset durations and integer headers parse to known values; anything else is unreadable (None), never
    an exception; limit headers above the free plan make the next response check stop the run.

    Why: the headers come from the network; a malformed or absurd value must neither crash a run nor stretch a wait
    past the minute window.
    """
    import provider_gate as pg
    known = {"2m59.56s": 179.56, "7.66s": 7.66, "1h2m3s": 3723.0, "500ms": 0.5, "0s": 0.0, "1.5h": 5400.0,
             "250us": 0.00025, "3": 3.0}
    got = {k: pg.go_duration(k) for k in known}
    check(all(got[k] is not None and abs(got[k] - v) < 1e-9 for k, v in known.items()), f"durations {got}")
    for bad in ("", "abc", "1x", "-1s", "s", "1s2", "1e3s", "NaNs", "infs", " 1s", None, 5, "9" * 400 + "h"):
        check(pg.go_duration(bad) is None, f"go_duration({bad!r}) = {pg.go_duration(bad)!r}")
    ints = {"1000": 1000, " 12 ": 12, "0": 0}
    check(all(pg.header_int(k) == v for k, v in ints.items()), "header_int known values")
    for bad in ("1,000", "-1", "1e3", "12.0", "", None, "x", "9" * 40):
        check(pg.header_int(bad) is None, f"header_int({bad!r}) = {pg.header_int(bad)!r}")
    # ── The free-plan check on limit headers ──
    ok = {"x-ratelimit-limit-requests": "1000", "x-ratelimit-limit-tokens": "8000"}
    verdicts = {}
    for name, headers in (("free", ok), ("project limit lower", dict(ok, **{"x-ratelimit-limit-requests": "500"})),
                          ("paid requests", dict(ok, **{"x-ratelimit-limit-requests": "14400"})),
                          ("paid tokens", dict(ok, **{"x-ratelimit-limit-tokens": "8001"})), ("no headers", {})):
        c = Clock()
        g = gate({}, c)
        attempt(g, "h0", headers=headers)
        stop = g.response_stop({"model": GROQ_MODEL, "usage": {"prompt_tokens": 1, "completion_tokens": 1}}, True)
        verdicts[name] = stop[0] if stop else None
    check(verdicts == {"free": None, "project limit lower": None, "paid requests": "not_free",
                       "paid tokens": "not_free", "no headers": None}, f"verdicts {verdicts}")
    # An absurd server reset never waits longer than one minute window.
    c = Clock()
    g = gate({}, c)
    attempt(g, "w0", headers={"x-ratelimit-remaining-tokens": "0", "x-ratelimit-reset-tokens": "99999h"})
    attempt(g, "w1")
    check(len(c.slept) == 1 and c.slept[0] <= 60.1, f"absurd reset waited {c.slept}")
    return f"{len(known)} durations and {len(ints)} integers parsed; 13 and 8 hostile values unreadable; verdicts {verdicts}"


# ── 429s and stops ───────────────────────────────────────────────────────────

def g06_groq_429s_minute_waits_day_stops_and_org_id_is_redacted():
    """A per-minute 429 waits retry-after and the call succeeds; a per-day 429 ends the run (exit 10, DailyQuota)
    with the resume time; the organisation id Groq's message carries appears in no record and on no console line.

    Why: retrying a daily limit only burns requests; and Groq's 429 text names the organisation (org_...), which
    identifies the owner's account and must stay out of the records like the key.
    """
    import provider_gate as pg
    groq_state()
    o1 = out("g06a.jsonl")
    STATE.queue = [groq_429("TPM", "0"), {"status": 200, "body": "OK"}]
    p1 = run_groq(groq_args("g06_ledger.jsonl") + ["--suite", "pick", "--items", "PW01", "--k", "1", "--out", o1])
    rec = calls(rows(o1))[0]
    check(p1.returncode == 0 and rec["error"] is None and rec["http_status_history"] == [429, 200]
          and rec["attempts"] == 2, f"minute 429: exit {p1.returncode}, {rec.get('http_status_history')}")
    o2 = out("g06b.jsonl")
    n = len(chat_requests())
    STATE.queue = [groq_429("RPD", "3600")]
    p2 = run_groq(groq_args("g06_ledger.jsonl") + ["--suite", "pick", "--items", "PW02", "--k", "1", "--out", o2])
    rec2 = calls(rows(o2))[0]
    check(p2.returncode == 10 and len(chat_requests()) == n + 1 and "resume after" in rec2["error"]
          and "daily rate limit" in rec2["error"] and stop_rows(o2)[-1]["stop"] == "DailyQuota",
          f"day 429: exit {p2.returncode}, {rec2.get('error')!r}")
    check(provider_clean(p1, o1) and provider_clean(p2, o2, out("g06_ledger.jsonl")) and "org_[REDACTED]"
          in rec2["error"], "the organisation id or a key reached a record or the console")
    # ── The classifier on known bodies ──
    now = T0
    kinds = {w: pg.groq_classify_429({}, groq_429(w)["body"], now, 7.0)[0] for w in ("RPM", "RPD", "TPM", "TPD")}
    other = pg.groq_classify_429({}, {"error": {"message": "over capacity"}}, now, 5.0)
    check(kinds == {"RPM": "minute", "RPD": "daily", "TPM": "minute", "TPD": "daily"} and other == ("upstream", 5.0),
          f"kinds {kinds}, other {other}")
    return f"TPM 429 then 200: one call, 2 attempts; RPD 429: exit 10 DailyQuota; kinds {kinds}"


def g07_groq_signs_of_spending_stop_the_run_with_exit_9():
    """Limit headers above the free plan, a reported cost above 0, or another model answering each stop the run at
    once with exit 9 (NotFree).

    Why: Groq has no key record or cost field to watch; the free plan's limit headers are the only live sign that
    the organisation is on it. A higher limit means a paid tier, where requests can be billed.
    """
    stops = {}
    for name, setup in (("paid-tier headers", lambda: groq_state(rpd=14400, tpm=30000)),
                        ("reported cost", lambda: (groq_state(), setattr(STATE, "cost_mode", "provider"))),
                        ("another model", lambda: (groq_state(), setattr(STATE, "served_model",
                                                                         "openai/gpt-oss-120b")))):
        STATE.reset()
        setup()
        o = out(f"g07_{len(stops)}.jsonl")
        p = run_groq(groq_args(f"g07_{len(stops)}_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "2",
                                                                     "--out", o])
        stops[name] = (p.returncode, len(chat_requests()), (stop_rows(o) or [{}])[-1].get("stop"))
    check(all(v == (9, 1, "NotFree") for v in stops.values()), f"stops {stops}")
    return f"each stops after its first call with exit 9 NotFree: {stops}"


def g08_groq_ledger_shared_across_runs_and_one_run_at_a_time():
    """A second run on the same ledger continues the first one's count; a Groq run left holding the per-user lock
    blocks the next one (exit 5, the file named) and does not block an OpenRouter free run's lock.

    Why: the free plan's limits are per organisation, so the count must survive between runs, and two runs on two
    ledgers would each keep their own count.
    """
    groq_state()
    led = "g08_ledger.jsonl"
    p1 = run_groq(groq_args(led) + ["--suite", "pick", "--k", "1", "--limit", "2", "--out", out("g08a.jsonl")])
    p2 = run_groq(groq_args(led) + ["--suite", "fill", "--k", "1", "--limit", "1", "--out", out("g08b.jsonl")])
    rec = calls(rows(out("g08b.jsonl")))[0]
    check(p1.returncode == 0 and p2.returncode == 0 and rec["rate_gate"]["requests_24h"] == 3,
          f"exit {p1.returncode}, {p2.returncode}; second run's count {rec['rate_gate']}")
    lock = os.path.join(out("appdata"), "plotroom-dev", "groq-run.lock")
    check(not os.path.exists(lock), "a finished run left its lock")
    os.makedirs(os.path.dirname(lock), exist_ok=True)
    write_text(lock, '{"pid": 1}')
    n = len(chat_requests())
    p3 = run_groq(groq_args(led) + ["--suite", "pick", "--k", "1", "--limit", "1", "--out", out("g08c.jsonl")])
    os.remove(lock)
    check(p3.returncode == 5 and "groq-run.lock" in p3.stderr and len(chat_requests()) == n,
          f"stale lock: exit {p3.returncode}, {p3.stderr[-300:]!r}")
    check(not os.path.exists(free_lock_path()), "the OpenRouter free-run lock was touched")
    return "second run counted 3 requests in the shared ledger; a stale groq-run.lock blocked the next run (exit 5)"


# ── unittest wiring ──────────────────────────────────────────────────────────

class GroqProviderTests(support.CaseTestCase):
    """--provider groq (see the module docs)."""

    cases = (g01_groq_request_shape_base_url_and_records,
             g02_groq_offline_refusals_send_nothing,
             g03_groq_minute_caps_wait_on_both_sides,
             g04_groq_day_caps_stop_on_both_sides_and_count_per_model,
             g05_groq_header_parsers_known_and_hostile_values,
             g06_groq_429s_minute_waits_day_stops_and_org_id_is_redacted,
             g07_groq_signs_of_spending_stop_the_run_with_exit_9,
             g08_groq_ledger_shared_across_runs_and_one_run_at_a_time)

    def setUp(self):
        STATE.reset()


if __name__ == "__main__":
    unittest.main()
