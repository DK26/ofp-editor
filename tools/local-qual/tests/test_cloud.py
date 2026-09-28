#!/usr/bin/env python3
"""Tests for the paid path of the OpenAI-compatible backend (cloud_backend.py, cloud_run.py, budget.py):
start refusals, the hard budget cap and --resume, retries and what they cost, the stops (402, errors inside
a 200, provider pin, cost anomaly, reasoning leak), the key's hygiene, the shared ledger, the key check,
schema normalising and the canary.

Every case runs run.py (or another tool script) as a child process against mock_server.py, in-process on
127.0.0.1: nothing is spent and no real endpoint is contacted. cloud_support.py holds the dummy keys, the
helpers and the final key sweep that fails the module if any key or key label reached a file or a console
transcript.

Run the whole suite from the repository root with ``python -m unittest discover -s tools/local-qual/tests``;
the module docs of support.py explain the case functions and the environment switches.
"""

import json
import unittest

import cloud_support
import support
from cloud_support import *  # noqa: F401,F403 - the shared fixtures the cases use by name

URL = None  # the mock's base URL while this module runs (set by setUpModule)


def setUpModule():
    global URL
    URL = cloud_support.start("cloud")


def tearDownModule():
    cloud_support.finish()


# ── Refusals, the cap, retries and stops (t03-t13) ─────────────────────────────

def t03_refuses_to_start_without_budget_and_key_rules():
    """No --max-usd (or prices, key env, reasoning) means no start; the key is never accepted on argv."""
    url = URL
    common = ["--backend", "openai", "--model", "mock/m", "--base-url", url, "--suite", "pick", "--k", "1",
              "--limit", "1", "--out", out("refuse.jsonl")]
    p = run_tool(common + ["--api-key-env", ENV_NAME, "--reasoning", "none", "--price-in", "1", "--price-out", "1"])
    check(p.returncode == 2 and "refuses to start without --max-usd" in p.stderr, f"no-budget: {p.returncode}")
    p2 = run_tool(common + ["--api-key-env", ENV_NAME, "--reasoning", "none", "--max-usd", "1"])
    check(p2.returncode == 2 and "--price-in" in p2.stderr, "no prices")
    p3 = run_tool(common + ["--api-key", KEY, "--reasoning", "none", "--max-usd", "1", "--price-in", "1",
                            "--price-out", "1"])
    check(p3.returncode == 2 and "never takes a key on the command line" in p3.stderr, "argv key")
    p4 = run_tool(common + ["--api-key-env", "CLOUDQUAL_UNSET_VAR", "--reasoning", "none", "--max-usd", "1",
                            "--price-in", "1", "--price-out", "1"])
    check(p4.returncode == 2 and "not set or empty" in p4.stderr, "unset env")
    p5 = run_tool(common + ["--api-key-env", ENV_NAME, "--max-usd", "1", "--price-in", "1", "--price-out", "1"])
    check(p5.returncode == 2 and "--reasoning is required" in p5.stderr, "no reasoning")
    p6 = run_tool(["--backend", "openai", "--model", "m", "--base-url", "http://example.com/v1", "--suite", "pick",
                   "--api-key-env", ENV_NAME, "--reasoning", "none", "--max-usd", "1", "--price-in", "1",
                   "--price-out", "1"])
    check(p6.returncode == 2 and "plain http" in p6.stderr, "http to a remote host")
    p7 = run_tool(common + ["--api-key-env", ENV_NAME, "--reasoning", "none", "--max-usd", "1", "--price-in", "1",
                            "--price-out", "1", "--extra-body", '{"max_tokens": 5}'])
    check(p7.returncode == 2 and "may not set max_tokens" in p7.stderr, "extra-body max_tokens")
    p8 = run_tool(common + ["--api-key-env", ENV_NAME, "--reasoning", "none", "--max-usd", "1", "--price-in", "1",
                            "--price-out", "1", "--extra-body", '{"plugins": [{"id": "response-healing"}]}'])
    check(p8.returncode == 2 and "response-healing" in p8.stderr, "response healing")
    p9 = run_tool(common + ["--api-key-env", ENV_NAME, "--reasoning", "none", "--max-usd", "1", "--price-in", "1",
                            "--price-out", "1", "--warmup"])
    check(p9.returncode == 2 and "--warmup is not available" in p9.stderr, "warmup")
    check(STATE.count() == 0, f"{STATE.count()} requests reached the server")
    return "9 refusals (exit 2), 0 requests reached the server"


def t04_budget_cap_refuses_before_overspend_and_persists_across_resume():
    """The cap stops the run before an attempt could overspend; --resume keeps counting from the file."""
    o = out("budget.jsonl")
    args = base(URL) + ["--suite", "pick", "--k", "3", "--limit", "5", "--out", o]
    cap1 = 0.004
    p1 = run_tool(args + ["--max-usd", str(cap1)])
    check(p1.returncode == 4, f"first run exit {p1.returncode}: {p1.stderr[-300:]}")
    r1 = rows(o)
    c1 = calls(r1)
    sent1 = STATE.count()
    spent1 = sum(r["cost_usd"] for r in c1)
    check(sent1 == len(c1) and 0 < len(c1) < 15, f"sent {sent1}, records {len(c1)}")
    check(spent1 <= cap1, f"spent {spent1} > cap {cap1}")
    # Invariant at every send: total before + that attempt's worst case <= the cap in force.
    prev = 0.0
    for r in c1:
        check(prev + r["reserved_usd"] <= r["budget_usd"] + 1e-12, "a call was sent that could overspend")
        prev = r["spent_usd"]
    stop = [r for r in r1 if r.get("budget_event") == "stop"]
    check(stop and stop[-1]["stop"] == "BudgetLimited", "no stop row")
    next_w = c1[-1]["reserved_usd"]
    # Same cap, resumed: nothing more is sent.
    p2 = run_tool(args + ["--max-usd", str(cap1), "--resume"])
    check(p2.returncode == 4 and STATE.count() == sent1, f"resume same cap: exit {p2.returncode}, "
                                                          f"sent {STATE.count() - sent1} more")
    check("already spent" in p2.stdout and f"{spent1:.6f}" in p2.stdout, "resume did not report the carried spend")
    # Larger cap, resumed: finishes the 15 calls, no call sent twice, total within the new cap.
    cap3 = 0.05
    p3 = run_tool(args + ["--max-usd", str(cap3), "--resume"])
    check(p3.returncode == 0, f"resume larger cap exit {p3.returncode}: {p3.stderr[-300:]}")
    c3 = calls(rows(o))
    keys = [(r["item_id"], r["sample"]) for r in c3]
    check(len(c3) == 15 and len(set(keys)) == 15, f"{len(c3)} records, {len(set(keys))} unique")
    check(STATE.count() == 15, f"server saw {STATE.count()} calls")
    total = sum(r["cost_usd"] for r in c3)
    check(total <= cap3 and abs(c3[-1]["spent_usd"] - total) < 1e-9, "running total mismatch")
    from budget import Budget, read_ledger_rows
    reloaded = Budget(cap3, 1.0, 1.0, rows=read_ledger_rows(o)).spent()
    check(abs(reloaded - total) < 1e-9, f"reloaded {reloaded} != {total}")
    return (f"cap {cap1}: {len(c1)} calls sent, spent {spent1:.6f}, next worst case ~{next_w:.6f} refused (exit 4); "
            f"resume at the same cap sent 0 (exit 4); resume at cap {cap3}: 15 calls total, spent {total:.6f}, "
            f"ledger reload {reloaded:.6f}")


def t05_retry_on_429_with_retry_after_and_backoff():
    """429s are retried (Retry-After honoured, then full-jitter backoff) and are not charged."""
    o = out("r429.jsonl")
    err = {"error": {"code": 429, "message": "rate limited"}}
    STATE.queue = [{"status": 429, "body": err, "headers": {"Retry-After": "0"}}, {"status": 429, "body": err}]
    p = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "1", "--max-usd", "1", "--out", o])
    check(p.returncode == 0, f"exit {p.returncode} {p.stderr[-300:]}")
    r = calls(rows(o))[0]
    check(r["attempts"] == 3 and r["http_status_history"] == [429, 429, 200], str(r["http_status_history"]))
    check(r["attempt_costs_usd"][:2] == [0.0, 0.0] and r["cost_usd"] == r["attempt_costs_usd"][2], "429 charged")
    check(r["retry_after_s"][0] == 0.0 and 0 <= r["retry_after_s"][1] <= 0.05, str(r["retry_after_s"]))
    check(r["parse_ok"] and not r["error"] and r["cost_source"] == "provider", "not a clean record")
    return (f"history {r['http_status_history']}, delays {r['retry_after_s']} s, cost {r['cost_usd']:.8f} "
            f"(429s unbilled), {STATE.count()} requests")


def t06_5xx_retries_are_charged_and_exhaustion_is_an_error():
    """503s are retried and charged at their reservation; persistent 500s end in an error record, not a crash."""
    o = out("r503.jsonl")
    STATE.queue = [{"status": 503, "body": {"error": {"code": 503, "message": "unavailable"}}}] * 2
    p = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "1", "--max-usd", "1", "--out", o])
    r = calls(rows(o))[0]
    check(p.returncode == 0 and r["http_status_history"] == [503, 503, 200], str(r["http_status_history"]))
    w = r["reserved_usd"]
    check(abs(r["cost_usd"] - (2 * w + r["attempt_costs_usd"][2])) < 1e-12 and r["cost_source"] == "provider+reserved",
          "503 charge")
    STATE.reset()
    o2 = out("r500.jsonl")
    STATE.queue = [{"status": 500, "body": {"error": {"code": 500, "message": "boom"}}}] * 5
    p2 = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "1", "--max-usd", "1", "--max-attempts",
                               "3", "--out", o2])
    r2 = calls(rows(o2))[0]
    check(p2.returncode == 2 and r2["error"].startswith("gave up after 3 attempts"), r2.get("error"))
    check(STATE.count() == 3 and abs(r2["cost_usd"] - 3 * r2["reserved_usd"]) < 1e-12, "500 attempts/charge")
    return (f"503x2 then 200: cost {r['cost_usd']:.8f} = 2 x {w:.8f} + provider cost; 500x3: error "
            f"'{r2['error'][:40]}...', charged {r2['cost_usd']:.8f}")


def t07_schema_rejection_stops_without_unconstrained_fallback():
    """A 4xx naming the schema stops the run (exit 6); no request is ever sent without the schema."""
    o = out("schema_reject.jsonl")
    STATE.reject_schema = True
    p = run_tool(base(URL) + ["--suite", "fill", "--k", "2", "--limit", "3", "--max-usd", "1", "--out", o])
    check(p.returncode == 6, f"exit {p.returncode}")
    check("rejected the strict json_schema" in p.stderr, "message")
    bodies = chat_bodies()
    check(len(bodies) == 1 and all("response_format" in b for b in bodies), f"{len(bodies)} requests")
    rs = rows(o)
    check(calls(rs)[0]["error"] and not calls(rs)[0]["parse_ok"], "record")
    check(rs[-1].get("stop") == "SchemaRejected", "stop row")
    return f"exit 6 after 1 request (with response_format), stop row SchemaRejected, cost {calls(rs)[0]['cost_usd']}"


def t08_api_key_never_written_or_printed():
    """The key reaches the server only in the Authorization header; records, ledgers and console never hold it."""
    o = out("key.jsonl")
    STATE.queue = [{"status": 500, "body": "ECHO_AUTH"}]
    STATE.answer_fn = lambda body: json.dumps({"choice": "A", "note": "echo " + KEY}) \
        if "response_format" in body else "HOLD " + KEY
    p = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "2", "--max-usd", "1", "--out", o])
    check(p.returncode == 0, f"exit {p.returncode}")
    STATE.queue = [{"status": 400, "body": "ECHO_AUTH"}]
    p2 = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "1", "--max-usd", "1", "--out",
                               out("key2.jsonl")])
    check(p2.returncode == 5, f"config-fault exit {p2.returncode}")
    p3 = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "1", "--max-usd", "1", "--dry-run"])
    check(p3.returncode == 0, "dry run")
    seen = [r["headers"].get("Authorization") for r in STATE.requests]
    check(all(h == f"Bearer {KEY}" for h in seen) and seen, "the server did not get the key in the header")
    text = read_text(o) + read_text(out("key2.jsonl"))
    check(KEY not in text and "[REDACTED]" in text, "key in records")
    check(all(KEY not in s for s in LOGS), "key in console output")
    return (f"{len(seen)} requests carried 'Bearer <key>'; echoed key in a 500 body, a 400 body and the content was "
            f"written as [REDACTED]; 0 occurrences in records and console")


def t09_http_402_stops_as_budget_without_retry():
    """HTTP 402 (out of credits) stops the run as a budget stop (exit 4) after one request, never retried.

    Why: a 402 means the account cannot pay; a retry would only repeat the refusal, and the stop row tells
    --resume where to continue once credit is added.
    """
    o = out("r402.jsonl")
    STATE.queue = [{"status": 402, "body": {"error": {"code": 402, "message": "Insufficient credits"}}}]
    p = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "3", "--max-usd", "1", "--out", o])
    check(p.returncode == 4 and STATE.count() == 1, f"exit {p.returncode}, {STATE.count()} requests")
    check(rows(o)[-1]["stop"] == "BudgetLimited", "stop row")
    return "HTTP 402: exit 4 after 1 request, not retried"


def t10_error_inside_http_200_is_not_content():
    """A provider error reported inside an HTTP 200 (a top-level error, or finish_reason "error") is retried or
    recorded as an error, never scored as the answer.

    Why: OpenRouter can report an upstream failure with status 200; taking its text as content would score a
    failure as a model decision.
    """
    o = out("r200err.jsonl")
    STATE.queue = [{"status": 200, "body": {"error": {"code": 502, "message": "upstream overloaded"}}},
                   {"status": 200, "body": {"id": "x", "choices": [{"finish_reason": "error", "error": {
                       "code": 400, "message": "content filter"}, "message": {"content": "{\"choice\": \"A\"}"}}]}}]
    p = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "1", "--max-usd", "1", "--out", o])
    r = calls(rows(o))[0]
    check(p.returncode == 2 and r["attempts"] == 2 and "provider error inside HTTP 200" in r["error"], r.get("error"))
    check(not r["parse_ok"] and r["raw"] == "", "error content was treated as an answer")
    return f"502 inside a 200 retried, then a finish_reason error: error record, raw '' ({r['attempts']} attempts)"


def t11_provider_pin_mismatch_stops():
    """With --expect-provider, a response served by another provider stops the run (exit 8) after one call; the
    pinned provider is accepted.

    Why: a precision rung (bf16, fp8) means something only if the named host served it; a silent fallback
    would mix hosts within one arm.
    """
    o = out("prov.jsonl")
    STATE.provider = "OtherCloud"
    p = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "2", "--max-usd", "1", "--expect-provider",
                              "deepinfra/bf16", "--out", o])
    check(p.returncode == 8 and STATE.count() == 1, f"exit {p.returncode}")
    STATE.reset()
    STATE.provider = "DeepInfra"
    p2 = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "2", "--max-usd", "1", "--expect-provider",
                               "deepinfra/bf16", "--out", out("prov2.jsonl")])
    check(p2.returncode == 0, f"matching provider exit {p2.returncode}")
    return "served 'OtherCloud' for pin deepinfra/bf16: exit 8 after 1 call; 'DeepInfra' accepted"


def t12_cost_anomaly_and_reasoning_leak_stop():
    """A call costing more than its worst case stops the run (exit 4, CostAnomaly); reasoning tokens on an
    effort-none call stop it (exit 7); with effort low they are recorded.

    Why: a cost above the reservation means a price flag or output cap is not what the endpoint applies, so the
    cap no longer holds; hidden reasoning on a direct-answer arm changes what is being measured.
    """
    STATE.cost_multiplier = 1000.0
    p = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "3", "--max-usd", "5", "--out",
                              out("anom.jsonl")])
    check(p.returncode == 4 and "CostAnomaly" in p.stderr and STATE.count() == 1, f"anomaly exit {p.returncode}")
    STATE.reset()
    STATE.reasoning_tokens = 30
    p2 = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "3", "--max-usd", "1", "--out",
                               out("leak.jsonl")])
    check(p2.returncode == 7 and "ReasoningLeak" in p2.stderr, f"leak exit {p2.returncode}")
    STATE.reset()
    STATE.reasoning_tokens = 30
    args = base(URL)
    args[args.index("--reasoning") + 1] = "low"
    p3 = run_tool(args + ["--suite", "pick", "--k", "1", "--limit", "2", "--max-usd", "1", "--out", out("low.jsonl")])
    r = calls(rows(out("low.jsonl")))[0]
    check(p3.returncode == 0 and r["reasoning_tokens"] == 30 and r["reasoning_sent"] == {"effort": "low"}, "low")
    return ("cost 1000x the price: exit 4 CostAnomaly after 1 call; reasoning tokens on effort none: exit 7; "
            "effort low logs reasoning_tokens 30")


def t13_shared_ledger_caps_across_runs():
    """--ledger shares one cap across output files: a second run on the same ledger sees the first run's spend
    and sends nothing past the cap.

    Why: a screening stage runs many arms into separate files under one budget; per-file caps would multiply
    it.
    """
    led = out("ledger.jsonl")
    p1 = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "3", "--max-usd", "0.01", "--ledger", led,
                               "--out", out("ledA.jsonl")])
    check(p1.returncode == 0, f"A exit {p1.returncode}")
    spent = sum(r["cost_usd"] for r in calls(rows(out("ledA.jsonl"))))
    n = STATE.count()
    p2 = run_tool(base(URL) + ["--suite", "fill", "--k", "1", "--limit", "3", "--max-usd", f"{spent + 1e-6:.9f}",
                               "--ledger", led, "--out", out("ledB.jsonl")])
    check(p2.returncode == 4 and STATE.count() == n, f"B exit {p2.returncode}, {STATE.count() - n} sent")
    lr = rows(led)
    check(any(r.get("budget_event") == "settle" for r in lr) and not any(
        r.get("budget_event") == "reserve" for r in rows(out("ledA.jsonl"))), "ledger layout")
    return f"run A spent {spent:.6f} in the shared ledger; run B with cap spent+1e-6 sent 0 calls (exit 4)"


# ── Key check, schema normalising, budget units, canary (t18-t21) ──────────────

def t18_key_check_guard():
    """--key-check reads GET /key before any call and refuses a key without a credit limit, or with more left on
    its limit than the cap allows (exit 5, no chat call).

    Why: the tool's own cap cannot stop a key that could spend more elsewhere; the key's limit is the
    second wall.
    """
    STATE.key = {"limit": 2.0, "limit_remaining": 1.5, "usage": 0.5}
    p = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "1", "--max-usd", "1", "--key-check",
                              "--out", out("kc.jsonl")])
    check(p.returncode == 0 and "key check: the key's usage" in p.stdout, f"ok exit {p.returncode}")
    STATE.reset()
    STATE.key = {"limit": None, "limit_remaining": None, "usage": 0.0}
    p2 = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "1", "--max-usd", "1", "--key-check",
                               "--out", out("kc2.jsonl")])
    STATE.key = {"limit": 50.0, "limit_remaining": 10.0, "usage": 0.0}
    p3 = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "1", "--max-usd", "1", "--key-check",
                               "--out", out("kc3.jsonl")])
    check(p2.returncode == 5 and p3.returncode == 5 and STATE.count() == 0, f"{p2.returncode} {p3.returncode}")
    return "limit_remaining 1.5 <= 1 + 1 accepted; no limit and 10 left refused (exit 5) with 0 chat calls"


def t19_schema_normalise_and_strip_in_dry_run():
    """--schema-normalise and --schema-strip change only the wire schema (strict, additionalProperties false, all
    required, stripped keywords), never the suite's own schema; a property named like a keyword is kept.

    Why: some providers reject JSON Schema keywords, while the suite schema keeps the full constraints that
    score.py checks in code.
    """
    p = run_tool(base(URL) + ["--suite", "fill", "--items", "F09", "--dry-run", "--schema-normalise",
                              "--schema-strip", "maxLength"])
    body, _ = json.JSONDecoder().raw_decode(p.stdout)
    wire = body["response_format"]["json_schema"]["schema"]
    check(body["response_format"]["json_schema"]["strict"] is True, "strict")
    check("maxLength" not in json.dumps(wire) and wire["additionalProperties"] is False and
          wire["required"] == list(wire["properties"]), "normalised")
    import run as runmod
    suite, _ = runmod.load_suite("fill")
    orig = next(it for it in suite["items"] if it["id"] == "F09")["schema"]
    check("maxLength" in json.dumps(orig), "the suite schema must keep maxLength (validated in code)")
    from cloud_backend import normalise_schema
    s, removed = normalise_schema({"type": "object", "properties": {"pattern": {"type": "string", "pattern": "a"}}},
                                  True, ("pattern",))
    check("pattern" in s["properties"] and "pattern" not in s["properties"]["pattern"] and removed == ["pattern"],
          "a property named pattern was stripped")
    return "wire schema: strict, additionalProperties false, all required, maxLength stripped; suite schema intact"


def t20_budget_unit_boundaries():
    """Budget arithmetic at its edges: a reservation exactly at the cap is accepted and 1e-9 over is refused, an
    unsettled reservation counts in full, bad caps and a missing max_tokens are refused, and cost_from_usage
    and the base-URL check behave at their limits.

    Why: the cap is the one guarantee against overspending; an off-by-epsilon here would let a run pass it.
    """
    from budget import Budget
    b = Budget(1.0, 1.0, 1.0)
    ok1, _ = b.try_reserve("c1", 1, 1.0)
    b.settle("c1", 1.0, "provider")
    ok2, _ = b.try_reserve("c2", 1, 1e-9)
    check(ok1 and not ok2, "cap boundary")
    b2 = Budget(1.0, 1.0, 1.0, rows=[{"budget_event": "reserve", "call_id": "x", "attempt": 1, "reserved_usd": 0.3},
                                     {"budget_event": "reserve", "call_id": "y", "attempt": 1, "reserved_usd": 0.2},
                                     {"call_id": "y", "cost_usd": 0.01, "seed": 1}])
    check(abs(b2.spent() - 0.31) < 1e-12, f"crash-safety {b2.spent()}")
    errs = 0
    for bad in (0, -1, float("nan"), float("inf")):
        try:
            Budget(bad, 1, 1)
        except ValueError:
            errs += 1
    check(errs == 4, "bad caps accepted")
    try:
        b.estimate({"messages": [{"role": "user", "content": "x"}]})
        check(False, "no max_tokens accepted")
    except ValueError:
        pass
    # A BYOK request's upstream cost adds to OpenRouter's fee; without is_byok it is the same money as cost (t60).
    c, src = b.cost_from_usage({"cost": 0.002, "is_byok": True, "cost_details": {"upstream_inference_cost": 0.001}})
    c2, src2 = b.cost_from_usage({"cost": -5, "prompt_tokens": 1000, "completion_tokens": 1000})
    c3, _ = b.cost_from_usage(None)
    check(abs(c - 0.003) < 1e-12 and src == "provider" and abs(c2 - 0.002) < 1e-12 and src2 == "computed"
          and c3 is None, "cost_from_usage")
    est = b.estimate({"messages": [{"role": "user", "content": "é" * 10}], "max_tokens": 10,
                      "reasoning": {"max_tokens": 100}})
    check(est["prompt_tokens_est"] == 37 and est["output_cap"] == 110, str(est))
    from cloud_backend import check_base_url
    refused = 0
    for u in ("http://example.com/v1", "https://u:p@example.com/v1", "https://example.com/v1?key=1", "ftp://x"):
        try:
            check_base_url(u)
        except ValueError:
            refused += 1
    check(refused == 4 and check_base_url("http://127.0.0.1:9/v1/") == "http://127.0.0.1:9/v1", "base urls")
    return ("exactly-at-cap reserve accepted, 1e-9 over refused; an unsettled reservation counts in full; bad caps, "
            "missing max_tokens, negative provider cost and unsafe base URLs rejected")


def t21_canary_aborts_on_parse_failures():
    """The canary stops a run (exit 7) once its first --canary calls all fail to parse.

    Why: a misconfigured arm (a wrong schema mode, an endpoint that ignores the format) should cost a few
    calls, not a whole suite.
    """
    STATE.answer_fn = lambda body: "not json at all"
    p = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "10", "--max-usd", "1", "--canary", "5",
                              "--out", out("canary.jsonl")])
    check(p.returncode == 7 and "CanaryAbort" in p.stderr and STATE.count() == 5, f"exit {p.returncode}")
    return "5 schema calls with unparsable answers: exit 7 after the 5-call canary window"


# ── Regressions found in the first cloud screening round (doc 54) (t59-t62) ────

def t59_non_byok_upstream_cost_is_not_counted_twice():
    """A response whose usage carries OpenRouter's upstream_inference_cost outside a BYOK request settles at usage.cost
    once: every record, the running total and the ledger equal what the provider billed.

    Why: doc 54 §4.2. OpenRouter reports cost_details.upstream_inference_cost on every call; outside a
    bring-your-own-key request it equals cost (is_byok false). The settle step added it to cost, so every call was
    booked twice (a ledger of 0.327 USD against 0.163 billed): every cap bound at half the real spend, run summaries
    doubled the cost, and the cost-anomaly guard fired once a call passed half its worst case.

    How: the mock answers in that shape (cost_details "mirror"); three calls at 1 USD per million tokens, the same
    prices as the flags. Each record's cost_usd must equal its usage.cost, and the ledger reloaded from the file, and
    the last record's running total, their sum.
    """
    STATE.cost_details = "mirror"
    o = out("non_byok.jsonl")
    p = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "3", "--max-usd", "1", "--out", o])
    check(p.returncode == 0, f"exit {p.returncode}: {p.stderr[-300:]}")
    recs = calls(rows(o))
    check(len(recs) == 3 and all(r["usage"]["is_byok"] is False and r["usage"]["cost_details"]["upstream_inference_cost"]
                                 == r["usage"]["cost"] for r in recs), "the mock did not answer in OpenRouter's shape")
    billed = sum(r["usage"]["cost"] for r in recs)
    check(all(abs(r["cost_usd"] - r["usage"]["cost"]) < 1e-15 for r in recs),
          f"cost_usd {[r['cost_usd'] for r in recs]} against billed {[r['usage']['cost'] for r in recs]}")
    from budget import Budget, read_ledger_rows
    ledger = Budget(1.0, 1.0, 1.0, rows=read_ledger_rows(o)).spent()
    check(abs(ledger - billed) < 1e-15 and abs(recs[-1]["spent_usd"] - billed) < 1e-15,
          f"ledger {ledger}, running total {recs[-1]['spent_usd']}, billed {billed}")
    return f"3 calls billed {billed:.8f} USD: records, running total and ledger all {ledger:.8f} (once, not twice)"


def t60_upstream_cost_counts_only_on_a_byok_request():
    """Budget.cost_from_usage adds cost_details.upstream_inference_cost to usage.cost only when usage.is_byok is true.

    Why: doc 54 §4.2. On a BYOK request OpenRouter's cost is its own fee and the provider bills the upstream cost to
    the user's provider account, so both are spent; on any other request the upstream figure is the same money as
    cost. A missing or malformed is_byok (the string "true", the number 1) is not a BYOK flag: the tool never adds
    money on the word of an untrusted field it cannot read, and the settle step still never goes below tokens x price.

    How: known values at the price flags of 1 USD per million tokens, where 10 + 2 tokens compute to 0.000012 USD.
    """
    from budget import Budget
    b = Budget(1.0, 1.0, 1.0)
    tok = {"prompt_tokens": 10, "completion_tokens": 2}
    up = {"upstream_inference_cost": 0.00002}
    cases = [
        ("non-BYOK, upstream equal to cost", dict(tok, cost=0.00002, is_byok=False, cost_details=up), 0.00002, "provider"),
        ("no is_byok field", dict(tok, cost=0.00002, cost_details=up), 0.00002, "provider"),
        ("is_byok the string 'true'", dict(tok, cost=0.00002, is_byok="true", cost_details=up), 0.00002, "provider"),
        ("is_byok the number 1", dict(tok, cost=0.00002, is_byok=1, cost_details=up), 0.00002, "provider"),
        ("BYOK: fee plus the provider's bill", dict(tok, cost=0.000001, is_byok=True,
                                                   cost_details={"upstream_inference_cost": 0.00003}), 0.000031, "provider"),
        ("BYOK below tokens x price", dict(tok, cost=0.000001, is_byok=True,
                                           cost_details={"upstream_inference_cost": 0.000005}), 0.000012,
         "computed>provider"),
        ("BYOK without an upstream figure", dict(tok, cost=0.00002, is_byok=True), 0.00002, "provider"),
        ("BYOK with a negative upstream figure", dict(tok, cost=0.00002, is_byok=True,
                                                      cost_details={"upstream_inference_cost": -1}), 0.00002, "provider"),
    ]
    bad = []
    for name, usage, want, source in cases:
        got = b.cost_from_usage(usage)
        if got[0] is None or abs(got[0] - want) > 1e-15 or got[1] != source:
            bad.append(f"{name}: {got}, want ({want}, {source!r})")
    check(not bad, "; ".join(bad))
    return f"{len(cases)} usage blocks: upstream added only with is_byok true; never below tokens x price"


def t61_cost_below_the_worst_case_never_trips_the_anomaly_guard():
    """A call billed at 60% of its worst case, in OpenRouter's non-BYOK usage shape, settles at that cost and does not
    stop the run.

    Why: doc 54 §4.3. The screening round's only guard stop was a call billed at 65% of its reservation that the
    double count booked at 131%, so the cost-anomaly guard fired although the price flags were right.

    How: the OpenAI-compatible backend and a budget in-process against the mock, with one scripted answer whose
    usage.cost is 0.6 x the reservation of the very body sent (its tokens cost far less at the price flags, so the
    provider's figure is the one settled).
    """
    from budget import Budget
    from cloud_backend import OpenAICompatBackend
    backend = OpenAICompatBackend(URL, 30.0, KEY, reasoning={"effort": "none"}, retry_base_s=0.01, retry_cap_s=0.05)
    budget = Budget(1.0, 1.0, 1.0)
    messages = [{"role": "system", "content": "Choose one."}, {"role": "user", "content": "Request: hold here."}]
    body = backend.payload("mock/model-1", messages, None, 0.6, 1, 64, 8192, {}, "pick")
    reserved = budget.reservation_usd(body)
    cost = 0.6 * reserved
    STATE.queue = [{"status": 200, "body": {
        "id": "gen-60", "model": "mock/model-1", "provider": "MockProvider",
        "choices": [{"message": {"role": "assistant", "content": "HOLD"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 1, "cost": cost, "is_byok": False,
                  "cost_details": {"upstream_inference_cost": cost}}}}]
    r = backend.chat(body, budget=budget, call_id="c60")
    check(r["fatal"] is None and r["error"] is None and not r["extra"]["cost_anomaly"],
          f"fatal {r['fatal']!r}: {r['error']}")
    check(abs(r["extra"]["cost_usd"] - cost) < 1e-15 and abs(budget.spent() - cost) < 1e-15,
          f"settled {r['extra']['cost_usd']} / spent {budget.spent()}, billed {cost}")
    return f"billed {cost:.9f} of a {reserved:.9f} USD worst case (60%): settled once, no CostAnomaly"


def t62_output_is_an_alias_of_out():
    """--output names the records file exactly as --out does, and the requests do not change.

    Why: cloud/run-cloud.ps1 passes run.py's arguments through ``powershell -File``, whose parameter binder takes
    "--out" for an abbreviation of its own common parameters -OutVariable and -OutBuffer and stops before the script
    starts ("the parameter name 'out' is ambiguous"), so a free run launched that way could not name its output file.
    "--output" matches no PowerShell parameter; dpapi_round_trip.ps1 checks it passes through the launcher (t53).
    """
    o1, o2 = out("alias_out.jsonl"), out("alias_output.jsonl")
    common = base(URL) + ["--suite", "pick", "--items", "PW01", "--k", "1", "--max-usd", "1"]
    p1 = run_tool(common + ["--out", o1])
    p2 = run_tool(common + ["--output", o2])
    check(p1.returncode == 0 and p2.returncode == 0, f"--out exit {p1.returncode}; --output exit {p2.returncode}: "
                                                     f"{p2.stderr[-300:]}")
    r1, r2 = calls(rows(o1)), calls(rows(o2))
    check(len(r1) == 1 and len(r2) == 1 and r1[0]["item_id"] == r2[0]["item_id"] == "PW01"
          and r1[0]["seed"] == r2[0]["seed"], "the two runs wrote different records")
    bodies = chat_bodies()
    check(len(bodies) == 2 and bodies[0] == bodies[1], "--output changed the request")
    check(f"-> {o2}" in p2.stdout, "the run did not report the --output path")
    return "--out and --output each wrote one PW01 record; identical request bodies"


# ── unittest wiring ──────────────────────────────────────────────────────────

class PaidEndpointTests(support.CaseTestCase):
    """The paid path's refusals, cap, retries, stops and guards (see the module docs)."""

    cases = (t03_refuses_to_start_without_budget_and_key_rules,
             t04_budget_cap_refuses_before_overspend_and_persists_across_resume,
             t05_retry_on_429_with_retry_after_and_backoff,
             t06_5xx_retries_are_charged_and_exhaustion_is_an_error,
             t07_schema_rejection_stops_without_unconstrained_fallback,
             t08_api_key_never_written_or_printed,
             t09_http_402_stops_as_budget_without_retry,
             t10_error_inside_http_200_is_not_content,
             t11_provider_pin_mismatch_stops,
             t12_cost_anomaly_and_reasoning_leak_stop,
             t13_shared_ledger_caps_across_runs,
             t18_key_check_guard,
             t19_schema_normalise_and_strip_in_dry_run,
             t20_budget_unit_boundaries,
             t21_canary_aborts_on_parse_failures,
             t59_non_byok_upstream_cost_is_not_counted_twice,
             t60_upstream_cost_counts_only_on_a_byok_request,
             t61_cost_below_the_worst_case_never_trips_the_anomaly_guard,
             t62_output_is_an_alias_of_out)

    def setUp(self):
        STATE.reset()


if __name__ == "__main__":
    unittest.main()
