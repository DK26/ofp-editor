#!/usr/bin/env python3
"""Two rate-limit stops of cloud_backend's ``chat``: a daily-cap 429 with an absurd reset, and 429s inside an HTTP 200.

r09-r11 pin the daily-cap stop. OpenRouter's daily free counter resets at 00:00 UTC, and ``X-RateLimit-Reset`` is
untrusted server text. A reset that is not after now, is not a number, or lies more than a day past the next 00:00
UTC is replaced by the next 00:00 UTC (rate_gate.daily_wait), and the resume time is formatted without raising
(rate_gate.daily_resume_time). Before, a reset of "1" followed by 30 zeros made ``time.gmtime`` raise OverflowError
inside ``chat`` (OSError past the year 3000 on Windows): a traceback, the call never settled, no stop row, while a
reset in the past printed "resume after" the current time.

r12-r14 pin the 429 streak. A 429 reported inside an HTTP 200 counts toward the gate's streak like an HTTP 429, so
a free run stops as ``rate_limited`` after ``--max-consecutive-429`` (3) in a row. Before, every such 200 reset the
streak, so a storm of them spent each call's ``max_attempts`` and only the day's allowance ended the run. An answer
(or any other status) still resets the streak, and a paid gate, which has no streak limit, retries as before. r15:
a daily-cap 429 that completes a streak still stops as ``quota``, so the record says to resume after 00:00 UTC.

r09 calls rate_gate directly. r10 and r12-r15 call ``chat`` in-process; r11 and r12 also run run.py as a child
process. All of them talk to mock_server.py on 127.0.0.1, which cloud_support.py starts and whose files and console
transcripts it sweeps for the dummy keys at the end. Nothing is spent, no real endpoint is contacted and no real key
is used.

Run the whole suite from the repository root with ``python -m unittest discover -s tools/local-qual/tests``;
the module docs of support.py explain the case functions and the environment switches.
"""

import datetime as dt
import os
import random
import time
import unittest

import cloud_support
import support
from cloud_support import *  # noqa: F401,F403 - the shared fixtures the cases use by name

import cloud_backend  # after cloud_support: importing support put the tool folder on sys.path
import rate_gate as rg
from budget import Budget, read_ledger_rows

URL = None  # the mock's base URL while this module runs (set by setUpModule)

# A fixed "now" for the unit cases: 2026-09-21 14:13:20 UTC, so the next 00:00 UTC (MIDNIGHT) is S2M seconds away.
N = 1_790_000_000.0
S2M = 35_200.0
DAY = 86_400.0
MIDNIGHT = "2026-09-22T00:00:00Z"
# X-RateLimit-Reset values no daily cap can mean. HUGE reads as epoch milliseconds 10^27 seconds away, past what
# time.gmtime can format anywhere (OverflowError). YEAR_3500_MS is 3500-01-01 in epoch milliseconds, past the year
# 3000, where the Windows C runtime's gmtime gives up (OSError, errno 22).
HUGE = "1" + "0" * 30
YEAR_3500_MS = str(int(dt.datetime(3500, 1, 1, tzinfo=dt.timezone.utc).timestamp() * 1000))

# The request every in-process call sends: small, with an output cap, so a paid Budget can compute its worst case.
CHAT_BODY = {"model": FREE_MODEL, "messages": [{"role": "user", "content": "Pick A or B."}], "stream": False,
             "max_tokens": 16}
PAID_BODY = dict(CHAT_BODY, model="mock/model-1")
# mock_server answers the body "OK" with its normal completion: content "HOLD", and cost 0 after free_state().
OK = {"status": 200, "body": "OK"}


def setUpModule():
    global URL
    URL = cloud_support.start("rate-stops")


def tearDownModule():
    cloud_support.finish()


# ── Fixtures ─────────────────────────────────────────────────────────────────

def ms(seconds_ahead, now=N):
    """An X-RateLimit-Reset value `seconds_ahead` after `now`, in epoch milliseconds as OpenRouter sends it."""
    return str((now + seconds_ahead) * 1000)


def provider_error(code=429):
    """An OpenRouter provider-error body with `code`. For 429 it is the upstream rate limit t49 uses (provider_name
    set, no per-day wording), so classify_429 calls it ``upstream``: retried, never the daily stop."""
    message = "mock/free-model:free is temporarily rate-limited upstream" if code == 429 else "Provider returned error"
    return {"error": {"code": code, "message": message,
                      "metadata": {"provider_name": "MockProvider", "raw": "busy"}}}


def http_429():
    """A scripted upstream rate limit as HTTP 429, with Retry-After 0 so the retry follows at once."""
    return {"status": 429, "body": provider_error(), "headers": {"Retry-After": "0"}}


def inside_200(code=429):
    """A scripted provider error with `code` reported inside an HTTP 200 body (OpenRouter documents both forms)."""
    return {"status": 200, "body": provider_error(code)}


def daily_429(reset):
    """OpenRouter's daily-cap 429 (message "free-models-per-day") with ``X-RateLimit-Reset`` set to the text `reset`."""
    cap = mock_server.daily_cap_429()
    cap["headers"]["X-RateLimit-Reset"] = reset
    return cap


def backend(gate, free=True, max_attempts=5, slept=None):
    """An OpenAICompatBackend at the mock with `gate` attached, as cloud_run.Session.start attaches one.

    With `free`, it also gets the zero-spend target free_mode.start_free sets (the requested :free model, the pinned
    endpoint). No key is sent (the mock does not ask for one). Back-off sleeps are appended to `slept`, not slept, so
    a case runs in milliseconds and can count them.
    """
    b = cloud_backend.OpenAICompatBackend(URL, 10.0, None, max_attempts=max_attempts,
                                          sleep=(slept if slept is not None else []).append, rng=random.Random(7))
    b.gate = gate
    if free:
        b.free_target = {"model": FREE_MODEL, "canonical_slug": None, "providers": ["mockprov/fp8"]}
    return b


def midnights():
    """The next 00:00 UTC as text, in a set: a case unites the sets taken before and after a call, so a call that
    straddles midnight still finds the time it printed."""
    return {rg.next_utc_midnight(time.time())}


def resumes_at(text, times):
    """Does `text` say "resume after <t> " for one of `times`?"""
    return any(f"resume after {t} " in (text or "") for t in times)


# ── Daily-cap stop with an absurd reset ──────────────────────────────────────

def r09_absurd_daily_resets_wait_for_the_next_utc_midnight():
    """A daily-cap 429 whose X-RateLimit-Reset is absurd (huge, past the year 3000, not a finite number, negative,
    zero, in the past, or more than a day past the next 00:00 UTC) waits until the next 00:00 UTC; a sane reset is
    kept as sent. The resume time is formatted from a sane wait and never raises.

    Why: the daily free counter resets at 00:00 UTC, whatever an untrusted header says. A reset of 10^27 seconds was
    handed to chat() as the wait, and formatting the resume time crashed the run; a reset in the past gave a wait of 0
    and "resume after" the current time, which only burns another request. One day of slack past the next midnight
    keeps a server clock that is already past midnight (naming the midnight after) from being overruled.

    How: known values at N (14:13:20 UTC, 35,200 s before midnight). With the daily-cap message the text decides the
    kind and the header only the wait; the far-future values are also checked alone, where the header decides both.
    daily_wait is also called directly: a NaN or bool wait that slipped through it would still format as the next
    midnight (daily_resume_time falls back to it), so only a direct call shows that guard working.
    """
    per_day = {"error": {"code": 429, "message": "Rate limit exceeded: free-models-per-day", "metadata": {}}}
    bare = {"error": {"code": 429, "message": "Rate limit exceeded", "metadata": {}}}
    absurd = [("1 and 30 zeros", HUGE), ("3500-01-01", YEAR_3500_MS), ("1e400", "1e400"), ("inf", "inf"),
              ("-inf", "-inf"), ("nan", "nan"), ("negative", "-5"), ("zero", "0"), ("1 s ago", ms(-1)),
              ("a day ago", ms(-DAY)), ("1 s past the bound", ms(S2M + DAY + 1))]
    bad = []
    for name, value in absurd:
        got = rg.classify_429({"x-ratelimit-reset": value}, per_day, N)
        if got != ("daily", S2M):
            bad.append(f"{name}: {got}")
    for name, value in (("1 and 30 zeros", HUGE), ("3500-01-01", YEAR_3500_MS), ("1 s past", ms(S2M + DAY + 1))):
        got = rg.classify_429({"x-ratelimit-reset": value}, bare, N)
        if got != ("daily", S2M):
            bad.append(f"{name} without per-day text: {got}")
    sane = [("a 12 s delay", "12", 12.0), ("1 h", ms(3600), 3600.0), ("the next midnight", ms(S2M), S2M),
            ("the bound, a day past it", ms(S2M + DAY), S2M + DAY)]
    for name, value, want in sane:
        got = rg.classify_429({"x-ratelimit-reset": value}, per_day, N)
        if got != ("daily", want):
            bad.append(f"{name}: {got}, want kept")
    check(not bad, "; ".join(bad))
    # ── The resume time: a sane wait as sent, anything else the next 00:00 UTC, never an exception ──
    check(rg.next_utc_midnight(N) == MIDNIGHT, f"next midnight after N: {rg.next_utc_midnight(N)}")
    kept = [rg.daily_resume_time(N, w) for w in (S2M, 3600.0, S2M + DAY)]
    check(kept == [MIDNIGHT, "2026-09-21T15:13:20Z", "2026-09-23T00:00:00Z"], f"sane waits: {kept}")
    odd = [1e27, float("inf"), float("-inf"), float("nan"), -1.0, 0.0, None, S2M + DAY + 1]
    got = [rg.daily_resume_time(N, w) for w in odd]
    check(got == [MIDNIGHT] * len(odd), f"absurd waits: {list(zip(odd, got))}")
    # ── daily_wait itself: its NaN and bool guards are otherwise hidden behind daily_resume_time's fallback ──
    waits = [rg.daily_wait(w, N) for w in odd + [True, False]]
    check(waits == [S2M] * len(waits), f"daily_wait of absurd waits: {list(zip(odd + [True, False], waits))}")
    return (f"{len(absurd)} absurd resets -> wait {S2M:.0f} s (the next 00:00 UTC), 3 also without per-day text; "
            f"{len(sane)} sane ones kept up to the bound (S2M + 1 day); resume times {kept}; {len(odd)} absurd waits "
            f"-> {MIDNIGHT}")


def r10_chat_stops_as_quota_at_the_next_midnight_on_an_absurd_reset():
    """Through cloud_backend.chat, a daily-cap 429 with an absurd reset stops the call as ``quota`` after one
    request, unbilled, with the next 00:00 UTC as the resume time, on a paid run with a gate and on a free run.

    Why: the crash happened here, where chat() formats the resume time. The exception left chat() before the call
    settled, so on a paid run the attempt's whole reservation stayed booked as spent, and the run died with a
    traceback instead of a stop row naming when to resume.

    How: the mock replays each daily-cap 429 with its header; the paid backend carries a Budget (prices 1 USD per
    million tokens) and a gate from ``--max-requests-per-day`` (no 429 streak limit), the free one the gate and
    zero-spend target free_mode sets. An exception is caught and reported with the amount left reserved.
    """
    now = time.time()
    absurd = [("1 and 30 zeros", HUGE), ("3500-01-01", YEAR_3500_MS), ("nan", "nan"), ("negative", "-5"),
              ("a minute ago", str(int((now - 60) * 1000))),
              ("two days past midnight", str(int((now + rg.seconds_to_midnight(now) + 2 * DAY) * 1000)))]
    bad, runs = [], []
    for name, value in absurd:
        for free in (False, True):
            STATE.queue = [daily_429(value), OK]
            n0, budget = STATE.count(), (None if free else Budget(1.0, 1.0, 1.0))
            gate = rg.RateGate(max_429=3) if free else rg.RateGate(per_day=100)
            before = midnights()
            try:
                r = backend(gate, free=free).chat(dict(CHAT_BODY if free else PAID_BODY), budget, "c1")
            except (OverflowError, OSError, ValueError) as e:
                left = f"{budget.spent():.8f} USD left reserved" if budget else "no budget"
                bad.append(f"{name} ({'free' if free else 'paid'}): chat raised {type(e).__name__} ({e}); {left}")
                continue
            x, sent, times = r["extra"], STATE.count() - n0, before | midnights()
            runs.append(sent)
            if r["fatal"] != "quota" or not resumes_at(r["error"], times) or sent != 1 or x["cost_usd"] != 0.0 \
                    or x["cost_source"] != "unbilled" or (budget is not None and budget.spent() != 0.0):
                bad.append(f"{name} ({'free' if free else 'paid'}): fatal {r['fatal']}, {sent} POSTs, cost "
                           f"{x['cost_usd']} ({x['cost_source']}), error {r['error']!r}")
    check(not bad, "; ".join(bad))
    return (f"{len(absurd)} absurd resets on a paid and a free backend: {len(runs)} calls stopped as quota after "
            f"{sorted(set(runs))} POST, unbilled, resuming at the next 00:00 UTC")


def r11_free_run_with_an_absurd_daily_reset_exits_10_without_a_traceback():
    """A free run whose first request gets a daily-cap 429 with an absurd reset stops cleanly: exit 10, a
    DailyQuota stop row, the next 00:00 UTC printed as the resume time, one request sent, nothing billed.

    Why: this is what the owner sees. Before the fix run.py died with a traceback (exit 1) in chat(), so the output
    file had no record and no stop row, and the console did not say when to resume.

    How: run.py as a child process against the mock, which answers every chat with the daily-cap 429; each header
    value gets its own ledger. The ledger's spent total is read back with budget.py, as t42 does.
    """
    bad, seen = [], []
    for i, value in enumerate((HUGE, YEAR_3500_MS)):
        STATE.reset()
        free_state()
        STATE.queue = [daily_429(value)] * 3
        o, led = out(f"absurd{i}.jsonl"), out(f"absurd{i}_ledger.jsonl")
        before = midnights()
        p = run_free(free_args(f"absurd{i}_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "3",
                                                              "--out", o])
        times = before | midnights()
        recs = calls(rows(o)) if os.path.exists(o) else []
        stops = [r["stop"] for r in stop_rows(o)]
        spent = Budget(0, 0, 0, rows=read_ledger_rows(led), free_only=True).spent() if os.path.exists(led) else None
        seen.append(STATE.count())
        if p.returncode != 10 or "Traceback" in p.stderr or STATE.count() != 1 or stops[-1:] != ["DailyQuota"] \
                or not resumes_at(p.stderr, times) or not recs or recs[0]["cost_usd"] != 0.0 or spent != 0 \
                or not resumes_at(recs[0]["error"], times) or not no_secrets(p, o, led):
            bad.append(f"reset {value[:16]}...: exit {p.returncode}, {STATE.count()} requests, stops {stops}, "
                       f"{len(recs)} records, spent {spent}, stderr {p.stderr.strip()[-240:]!r}")
    check(not bad, "; ".join(bad))
    return (f"resets of 10^30 and 3500-01-01: exit 10, DailyQuota, {seen} requests, resume at the next 00:00 UTC, "
            f"ledger spent 0, no traceback")


# ── The 429 streak counts 429s inside an HTTP 200 ────────────────────────────

def r12_429s_inside_a_200_stop_a_free_run_as_rate_limited_after_three():
    """Three 429s inside HTTP 200 bodies in a row stop a free run as ``rate_limited`` (exit 10): within one call
    after 3 requests, across calls when a call gave up before the third, and through run.py.

    Why: the gate counted HTTP statuses only, and every 200 reset the streak, so a storm of 429s reported inside a
    200 spent each call's max_attempts (5) and went on call after call until the day's allowance ran out. Every
    attempt costs one of the day's 50 free requests.

    How: in-process calls against the mock with the free run's gate (max_429 3); the cross-call part uses
    max_attempts 2 so the first call gives up with a streak of 2. The run.py part is t49's "3 in a row" with the
    429s inside a 200.
    """
    free_state()
    slept, n0 = [], STATE.count()
    STATE.queue = [inside_200()] * 5 + [OK]
    r = backend(rg.RateGate(max_429=3), slept=slept).chat(dict(CHAT_BODY))
    one = (r["fatal"], STATE.count() - n0, r["extra"]["http_status_history"], len(slept), r["content"])
    check(one == ("rate_limited", 3, [200] * 3, 2, "") and "3 429s in a row" in (r["error"] or "")
          and (r["error"] or "").startswith("provider error inside HTTP 200 (code 429)"),
          f"one call: {one}, error {r['error']!r}")
    # ── Across calls: the streak carries from a call that gave up into the next one ──
    n0 = STATE.count()
    STATE.queue = [inside_200()] * 3 + [OK]
    b = backend(rg.RateGate(max_429=3), max_attempts=2)
    r1, r2 = b.chat(dict(CHAT_BODY)), b.chat(dict(CHAT_BODY))
    check(r1["fatal"] is None and (r1["error"] or "").startswith("gave up after 2 attempts")
          and r2["fatal"] == "rate_limited" and r2["extra"]["http_status_history"] == [200] and STATE.count() - n0 == 3,
          f"across calls: {r1['fatal']} {r1['error']!r}; {r2['fatal']} {r2['extra']['http_status_history']}")
    # ── A free run through run.py ──
    STATE.reset()
    free_state()
    STATE.queue = [inside_200()] * 6
    o, led = out("storm.jsonl"), out("storm_ledger.jsonl")
    p = run_free(free_args("storm_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "3", "--out", o])
    recs, stops = calls(rows(o)), [s["stop"] for s in stop_rows(o)]
    spent = Budget(0, 0, 0, rows=read_ledger_rows(led), free_only=True).spent()
    check(p.returncode == 10 and "RateLimited" in p.stderr and STATE.count() == 3 and stops[-1:] == ["RateLimited"]
          and recs and recs[0]["http_status_history"] == [200] * 3 and spent == 0 and no_secrets(p, o, led),
          f"run.py: exit {p.returncode}, {STATE.count()} requests, stops {stops}, spent {spent}, "
          f"{p.stderr.strip()[-240:]!r}")
    return ("3 in one call: rate_limited after 3 POSTs (2 back-offs); a call giving up at 2 then 1 more: rate_limited; "
            "run.py: exit 10 RateLimited after 3 requests, ledger spent 0")


def r13_an_answer_resets_the_streak_and_both_429_forms_share_it():
    """An answer resets the 429 streak, and so does any other error inside a 200 (as any other HTTP status does);
    HTTP 429s and 429s inside a 200 count in one streak, whichever form comes third.

    Why: the streak must measure "the endpoint keeps refusing", not how the refusal was wrapped: two 429s inside a
    200 and one HTTP 429 are three refusals. It must not stop a run that is getting answers, or whose refusals are
    broken by other failures (those retry under the call's own attempt limit, as before).

    How: in-process calls against the mock with the free run's gate (max_429 3); each part gets a fresh gate.
    """
    free_state()
    bad = []
    # ── Answers reset it: two calls of 429, 429, answer each ──
    gate, n0 = rg.RateGate(max_429=3), STATE.count()
    STATE.queue = [inside_200(), inside_200(), OK] * 2
    b = backend(gate)
    rs = [b.chat(dict(CHAT_BODY)) for _ in range(2)]
    if any(r["fatal"] or r["error"] or r["content"] != "HOLD" or r["extra"]["http_status_history"] != [200] * 3
           for r in rs) or gate.consecutive_429 != 0 or STATE.count() - n0 != 6:
        bad.append(f"answers: {[(r['fatal'], r['error']) for r in rs]}, streak {gate.consecutive_429}")
    # ── Another error inside a 200 (a 502) resets it: 429, 429, 502, 429, 429 run to the attempt limit ──
    gate, n0 = rg.RateGate(max_429=3), STATE.count()
    STATE.queue = [inside_200(), inside_200(), inside_200(502), inside_200(), inside_200(), OK]
    r = backend(gate).chat(dict(CHAT_BODY))
    if r["fatal"] is not None or not (r["error"] or "").startswith("gave up after 5 attempts") \
            or gate.consecutive_429 != 2 or STATE.count() - n0 != 5:
        bad.append(f"502 between: fatal {r['fatal']}, streak {gate.consecutive_429}, {STATE.count() - n0} POSTs")
    # ── Mixed forms share one streak: the third stops the call, whichever form it takes ──
    for name, script, lead in (("HTTP, inside, HTTP", [http_429(), inside_200(), http_429()], "HTTP 429 (upstream"),
                               ("inside, HTTP, inside", [inside_200(), http_429(), inside_200()],
                                "provider error inside HTTP 200 (code 429)")):
        n0 = STATE.count()
        STATE.queue = script + [OK]
        r = backend(rg.RateGate(max_429=3)).chat(dict(CHAT_BODY))
        err = r["error"] or ""
        if r["fatal"] != "rate_limited" or STATE.count() - n0 != 3 or not err.startswith(lead) \
                or "3 429s in a row" not in err:
            bad.append(f"{name}: fatal {r['fatal']}, {STATE.count() - n0} POSTs, error {err!r}")
    check(not bad, "; ".join(bad))
    return ("429, 429, answer twice: both answered, streak 0; a 502 inside a 200 between: 5 attempts, streak 2; "
            "HTTP/inside mixes: rate_limited on the third, either form")


def r14_paid_gates_keep_retrying_429s_to_the_attempt_limit():
    """A paid run's gate (``--rpm`` or ``--max-requests-per-day``, no streak limit) and a run without a gate retry
    429s, inside a 200 or as HTTP 429, up to max_attempts, with the same records and charges as before.

    Why: only free runs set ``--max-consecutive-429``; cloud_run.py builds a paid gate with max_429 None. Counting a
    429 inside a 200 must not stop a paid run, change what it is charged (a 200 without usage is charged its whole
    reservation, an HTTP 429 nothing) or change the recorded error.

    How: in-process calls with a Budget (1 USD per million tokens) against the mock; each call gets five 429s, then
    an answer it never reaches.
    """
    cases = [("paid gate, inside a 200", rg.RateGate(rpm=100), inside_200, "reserved"),
             ("no gate, inside a 200", None, inside_200, "reserved"),
             ("paid gate, HTTP 429", rg.RateGate(rpm=100), http_429, "unbilled")]
    bad, done = [], []
    for name, gate, make, source in cases:
        budget, slept, n0 = Budget(1.0, 1.0, 1.0), [], STATE.count()
        STATE.queue = [make() for _ in range(5)] + [OK]
        r = backend(gate, free=False, slept=slept).chat(dict(PAID_BODY), budget, "c1")
        x, err = r["extra"], r["error"] or ""
        each = round(budget.reservation_usd(PAID_BODY), 12) if source == "reserved" else 0.0
        labelled = err.endswith("; upstream rate limit") or err.startswith("gave up after 5 attempts; last: HTTP 429 (")
        if r["fatal"] is not None or STATE.count() - n0 != 5 or len(slept) != 4 or r["content"] != "" \
                or not err.startswith("gave up after 5 attempts; last: ") or x["attempt_costs_usd"] != [each] * 5 \
                or x["cost_source"] != source or labelled != (gate is not None):
            bad.append(f"{name}: fatal {r['fatal']}, {STATE.count() - n0} POSTs, costs {x['attempt_costs_usd']} "
                       f"({x['cost_source']}), error {err!r}")
        done.append(f"{name}: 5 attempts, {x['cost_source']}")
    check(not bad, "; ".join(bad))
    return "; ".join(done)


def r15_a_daily_cap_429_that_completes_the_streak_stops_as_quota():
    """A daily-cap 429 that arrives as the third 429 in a row stops the call as ``quota`` with the daily wording, not
    as ``rate_limited``, as HTTP 429 or inside an HTTP 200, after two 429s of either form.

    Why: both stops exit 10, but only the quota stop says to resume after 00:00 UTC; "resume later" invites a resume
    that meets the daily cap again and spends a request on it. Since a 429 inside a 200 counts toward the streak, the
    daily cap can complete a streak on either path, so each path must check the daily cap before the streak. Found
    in the adversarial review of r09-r14: moving the streak check first on either path passed every other test.

    How: in-process free-run calls (max_429 3) whose third response is the mock's daily-cap 429, as sent or with its
    body inside a 200, after two upstream 429s.
    """
    free_state()
    cap = mock_server.daily_cap_429()
    cap_inside = {"status": 200, "body": cap["body"]}
    bad = []
    for name, script in (("HTTP, HTTP, daily as HTTP 429", [http_429(), http_429(), cap]),
                         ("inside, inside, daily inside a 200", [inside_200(), inside_200(), cap_inside]),
                         ("inside, HTTP, daily as HTTP 429", [inside_200(), http_429(), cap]),
                         ("HTTP, inside, daily inside a 200", [http_429(), inside_200(), cap_inside])):
        gate, n0 = rg.RateGate(max_429=3), STATE.count()
        STATE.queue = script + [OK]
        r = backend(gate).chat(dict(CHAT_BODY))
        err = r["error"] or ""
        if r["fatal"] != "quota" or STATE.count() - n0 != 3 or gate.consecutive_429 != 3 or "in a row" in err \
                or "the daily quota is used up: resume after " not in err:
            bad.append(f"{name}: fatal {r['fatal']}, {STATE.count() - n0} POSTs, streak {gate.consecutive_429}, "
                       f"error {err!r}")
    check(not bad, "; ".join(bad))
    return "4 streaks completed by the daily cap (HTTP 429 or inside a 200): quota after 3 POSTs, never rate_limited"


# ── unittest wiring ──────────────────────────────────────────────────────────

class RateLimitStopTests(support.CaseTestCase):
    """The daily-cap stop with an absurd reset, and the 429 streak with 429s inside a 200 (see the module docs)."""

    cases = (r09_absurd_daily_resets_wait_for_the_next_utc_midnight,
             r10_chat_stops_as_quota_at_the_next_midnight_on_an_absurd_reset,
             r11_free_run_with_an_absurd_daily_reset_exits_10_without_a_traceback,
             r12_429s_inside_a_200_stop_a_free_run_as_rate_limited_after_three,
             r13_an_answer_resets_the_streak_and_both_429_forms_share_it,
             r14_paid_gates_keep_retrying_429s_to_the_attempt_limit,
             r15_a_daily_cap_429_that_completes_the_streak_stops_as_quota)

    def setUp(self):
        STATE.reset()


if __name__ == "__main__":
    unittest.main()
