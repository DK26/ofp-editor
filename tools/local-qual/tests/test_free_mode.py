#!/usr/bin/env python3
"""Tests for --free-only (free_mode.py, free_key.py, rate_gate.py): OpenRouter :free models at zero spend.

Covers the offline refusals, the live-catalogue traps, the request shape and records of a free run, the
zero-spend guard, model substitution, the key rules, the key poll, the daily cap and a resume across a day
boundary, the account quota and its reserve, the three kinds of 429, and the rate gate's units against known
values. The mock plays a free account (zero prices, a key record with a live daily counter, OpenRouter's
daily-cap 429, a public catalogue with a free model, a paid model and nine traps).

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
    URL = cloud_support.start("free-mode")


def tearDownModule():
    cloud_support.finish()


# ── Free-only mode (t40-t50) ───────────────────────────────────────────────────

def t40_free_only_offline_refusals():
    """Ids that are not one plain :free model, a non-OpenRouter host, any non-zero cap or price, no shared ledger,
    looser routing and out-of-range rate flags are refused before anything is sent (exit 2, 0 requests)."""
    common = ["--suite", "pick", "--k", "1", "--limit", "1", "--out", out("free_ref.jsonl")]

    def with_model(m):
        return free_args("fr_ledger.jsonl", m) + common
    no_ledger = free_args("x.jsonl")
    no_ledger = no_ledger[:no_ledger.index("--ledger")] + common
    cases = [
        ("paid id", with_model("mock/model-1"), "<author>/<slug>:free"),
        ("openrouter/auto:free", with_model("openrouter/auto:free"), "routers"),
        ("openrouter/free", with_model("openrouter/free"), "routers"),
        (":online suffix", with_model("mock/free-model:online"), ":online"),  # the paid path's own refusal
        (":nitro suffix", with_model("mock/free-model:nitro"), "<author>/<slug>:free"),
        ("two suffixes", with_model("mock/free-model:free:nitro"), "<author>/<slug>:free"),
        ("latest alias", with_model("~mock/free-latest:free"), ":free"),
        ("upper case", with_model("Mock/Free-Model:free"), ":free"),
        # A reserved name that never resolves (RFC 2606), so a mutant without the host check reaches no real server.
        ("remote host", free_args("fr_ledger.jsonl", url="https://api.example.invalid/v1") + common, "OpenRouter"),
        ("non-zero cap", with_model(FREE_MODEL) + ["--max-usd", "0.5"], "spends nothing"),
        ("non-zero price", with_model(FREE_MODEL) + ["--price-out", "0.1"], "spends nothing"),
        ("no ledger", no_ledger, "--ledger"),
        ("rpm above the limit", with_model(FREE_MODEL) + ["--rpm", "21"], "--rpm"),
        ("rpm 0", with_model(FREE_MODEL) + ["--rpm", "0"], "--rpm"),
        ("poll every 11", with_model(FREE_MODEL) + ["--key-poll-every", "11"], "--key-poll-every"),
        ("fallbacks on", with_model(FREE_MODEL) + ["--extra-body", '{"provider": {"allow_fallbacks": true}}'],
         "allow_fallbacks"),
        ("require_parameters off", with_model(FREE_MODEL) + ["--extra-body",
                                                              '{"provider": {"require_parameters": false}}'],
         "require_parameters"),
        ("max_price above 0", with_model(FREE_MODEL) + ["--extra-body", '{"provider": {"max_price": {"prompt": 1}}}'],
         "max_price"),
        ("fallback models", with_model(FREE_MODEL) + ["--extra-body", '{"models": ["mock/model-1"]}'], "models"),
        ("cap 0 without --free-only", base(URL) + common + ["--max-usd", "0"], "--max-usd"),
        ("headroom flag without --free-only", base(URL) + common + ["--max-usd", "1", "--allow-key-headroom"],
         "--free-only"),
        ("--free-only on a local backend", ["--backend", "ollama", "--model", "m", "--free-only"] + common,
         "--backend openai"),
    ]
    bad = []
    for name, argv, needle in cases:
        q = run_free(argv)
        if not refused(q, needle):
            bad.append(f"{name}: exit {q.returncode}, stderr {q.stderr.strip()[-200:]!r}")
    check(not bad, "; ".join(bad))
    check(not STATE.requests, f"{len(STATE.requests)} requests reached the server")
    return f"{len(cases)} refusals (exit 2) with 0 requests of any kind"


def t41_free_catalogue_checks_refuse_traps():
    """At start, the live catalogue must show the exact id, every price exactly 0, text output, zero-priced endpoints
    and support for every parameter sent; the catalogue is read without the key, before the key record."""
    free_state()
    traps = [("mock/negprice:free", "'-1' is not exactly 0"), ("mock/hidden-fee:free", "request price"),
             ("mock/web-fee:free", "web_search price"), ("mock/audio:free", "text only"),
             ("mock/overrides:free", "overrides[0].prompt"), ("mock/no-endpoints:free", "no endpoint"),
             ("mock/paid-endpoint:free", "endpoint 'mockprov/fp8': prompt price"),
             ("mock/expired:free", "expiration_date"), ("mock/absent:free", "not in OpenRouter's live model list")]
    bad = []
    for i, (model, needle) in enumerate(traps):
        o = out(f"trap{i}.jsonl")
        p = run_free(free_args(f"trap{i}_ledger.jsonl", model) + ["--suite", "pick", "--k", "1", "--limit", "1",
                                                                    "--out", o])
        stops = stop_rows(o)
        if p.returncode != 9 or needle not in p.stderr or not stops or stops[-1]["stop"] != "NotFree":
            bad.append(f"{model}: exit {p.returncode}, {p.stderr.strip()[-200:]!r}")
    check(not bad, "; ".join(bad))
    gets = [r for r in STATE.requests if r["body"] is None]
    check(STATE.count() == 0 and not any(r["path"].endswith("/key") for r in gets),
          f"{STATE.count()} chat calls, key read {sum(r['path'].endswith('/key') for r in gets)} times")
    check(gets and not any("Authorization" in r["headers"] for r in gets), "a catalogue request carried the key")
    n_traps = len(traps)
    # Parameters the endpoint lacks, and a pin naming no live endpoint: configuration refusals (exit 5), 0 chats.
    STATE.reset()
    free_state()
    ns = "mock/noschema:free"
    p1 = run_free(free_args("ns1.jsonl", ns) + ["--suite", "pick", "--items", "PW01", "--k", "1", "--out", out("ns1.jsonl")])
    p2 = run_free(free_args("ns2.jsonl", ns) + ["--suite", "pick", "--items", "PW01", "--k", "1", "--schema-mode",
                                                "none", "--out", out("ns2.jsonl")])
    p3 = run_free(free_args("ns3.jsonl") + ["--suite", "pick", "--items", "PW01", "--k", "1", "--extra-body",
                                            '{"provider": {"only": ["otherprov/bf16"]}}', "--out", out("ns3.jsonl")])
    check(p1.returncode == 5 and "--schema-mode none" in p1.stderr, f"strict arm: exit {p1.returncode}")
    check(p2.returncode == 5 and "--drop-params seed" in p2.stderr, f"seed: exit {p2.returncode}")
    check(p3.returncode == 5 and "provider.only names" in p3.stderr, f"pin: exit {p3.returncode}")
    check(STATE.count() == 0, f"{STATE.count()} chat calls during the configuration refusals")
    # The boundary: request and image prices of "0" and zero-priced tiers pass; so does the no-schema arm without seed.
    p4 = run_free(free_args("zo.jsonl", "mock/zero-overrides:free") + ["--suite", "pick", "--items", "PW01", "--k",
                                                                      "1", "--out", out("zo.jsonl")])
    p5 = run_free(free_args("ns4.jsonl", ns) + ["--suite", "pick", "--items", "PW01", "--k", "1", "--schema-mode",
                                                "none", "--drop-params", "seed", "--out", out("ns4.jsonl")])
    check(p4.returncode == 0 and p5.returncode == 0 and STATE.count() == 2, f"accepted: {p4.returncode} "
                                                                            f"{p5.returncode}")
    return (f"{n_traps} traps refused (exit 9, NotFree) with 0 chat calls and the key never read; catalogue GETs "
            f"carry no Authorization; missing structured_outputs, missing seed and a foreign pin refused (exit 5) with "
            f"the fix named; request/image prices of '0' with zero-priced tiers, and the no-schema arm with "
            f"--drop-params seed, run")


def t42_free_happy_path_request_shape_and_records():
    """A free run sends require_parameters true, no fallbacks and the live pin, records zero cost and the endpoint,
    reads the key at start and end, and shows only non-secret key fields."""
    free_state()
    o, led = out("free_ok.jsonl"), out("free_ok_ledger.jsonl")
    p = run_free(free_args("free_ok_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "3", "--out", o])
    check(p.returncode == 0, f"exit {p.returncode}: {p.stderr[-300:]}")
    bodies = chat_bodies()
    want = {"require_parameters": True, "allow_fallbacks": False, "only": ["mockprov/fp8"]}
    check(len(bodies) == 3 and all(b["provider"] == want for b in bodies), f"provider blocks {bodies[0]['provider']}")
    check(all(r["headers"].get("Authorization") == f"Bearer {FREE_KEY}" for r in STATE.requests
              if r["path"].endswith(("/chat/completions", "/key"))), "the key did not travel in the header")
    recs = calls(rows(o))
    check(all(r["cost_usd"] == 0.0 and r["free_only"] and r["endpoint_tag"] == "mockprov/fp8"
              and r["canonical_slug"] == "mock/free-model-20260901" for r in recs), "record fields")
    check([r["rate_gate"]["attempts_today"] for r in recs] == [1, 2, 3], str([r.get("rate_gate") for r in recs]))
    check("label" not in json.dumps(recs[0]["key_start"]) and recs[0]["free_daily_start"]["limit"] == 50, "key_start")
    from budget import Budget, read_ledger_rows
    spent = Budget(0, 0, 0, rows=read_ledger_rows(led), free_only=True).spent()
    key_reads = sum(1 for r in STATE.requests if r["path"].endswith("/key"))
    check(spent == 0 and key_reads == 2 and "usage unchanged" in p.stdout, f"spent {spent}, {key_reads} key reads")
    check(no_secrets(p, o, led), "a key, the key label or an account id was shown or written")
    d = run_free(free_args("dry.jsonl") + ["--suite", "pick", "--items", "PW01", "--dry-run"])
    body, _ = json.JSONDecoder().raw_decode(d.stdout)
    check(d.returncode == 0 and body["provider"] == {"require_parameters": True, "allow_fallbacks": False}
          and '"usd": 0.0' in d.stdout and len(STATE.requests) == 3 + key_reads + 2, "dry run")
    return ("3 calls: provider {require_parameters: true, allow_fallbacks: false, only: [live tag]}, cost 0, "
            "attempts_today 1-3, ledger spent 0, key read at start and end only, label and account ids never shown; "
            "dry run: routing shown, worst case 0 USD, nothing sent")


def t43_zero_spend_guard_stops_on_any_charge():
    """Any charge stops the run at once (exit 9): usage.cost above 0, no usage, BYOK upstream cost, or a cost on an
    error inside a 200 (no retry); a ledger that recorded spending refuses the next start."""
    free_state()
    STATE.price_in = STATE.price_out = 1.0  # the mock now reports usage.cost > 0
    o = out("charged.jsonl")
    p = run_free(free_args("charged_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "3", "--out", o])
    rec = calls(rows(o))[0]
    check(p.returncode == 9 and STATE.count() == 1 and "usage.cost" in rec["error"] and stop_rows(o)[-1]["stop"] ==
          "NotFree", f"charged: exit {p.returncode}, {STATE.count()} calls")
    n = len(STATE.requests)
    p2 = run_free(free_args("charged_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "3", "--resume",
                                                       "--out", o])
    check(p2.returncode == 9 and len(STATE.requests) == n and "must stay at 0" in p2.stderr,
          f"resume on a charged ledger: exit {p2.returncode}, {len(STATE.requests) - n} requests")
    results = [f"cost {rec['cost_usd']:.6f}: exit 9 after 1 call; resume on that ledger: exit 9, 0 requests"]
    ok_usage = {"prompt_tokens": 10, "completion_tokens": 2, "cost": 0}
    answer = {"id": "g", "model": FREE_MODEL, "provider": "MockProvider",
              "choices": [{"message": {"content": '{"choice": "A"}'}, "finish_reason": "stop"}]}
    for name, body in (("no usage", dict(answer)),
                       ("BYOK upstream cost", dict(answer, usage=dict(ok_usage, cost_details={
                           "upstream_inference_cost": 0.01}))),
                       ("cost on an error inside a 200", {"error": {"code": 502, "message": "upstream"},
                                                         "usage": {"cost": 0.001}})):
        STATE.reset()
        free_state()
        STATE.queue = [{"status": 200, "body": body}] * 3
        q = run_free(free_args(f"z_{len(results)}.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "3", "--out",
                                                             out(f"z_{len(results)}_o.jsonl")])
        check(q.returncode == 9 and STATE.count() == 1, f"{name}: exit {q.returncode}, {STATE.count()} calls")
        results.append(f"{name}: exit 9 after 1 call")
    return "; ".join(results)


def t44_model_substitution_and_unexpected_provider_stop():
    """A response from another model (the paid sibling) or another provider stops the run (exit 9); the model's
    canonical slug with :free is accepted."""
    free_state()
    STATE.served_model = "mock/free-model"
    p = run_free(free_args("sub1.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "3", "--out", out("sub1o.jsonl")])
    check(p.returncode == 9 and STATE.count() == 1 and "served by model 'mock/free-model'" in p.stderr,
          f"paid sibling: exit {p.returncode}")
    STATE.reset()
    free_state()
    STATE.served_model = "mock/free-model-20260901:free"
    p2 = run_free(free_args("sub2.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "2", "--out", out("sub2o.jsonl")])
    check(p2.returncode == 0, f"canonical slug: exit {p2.returncode}")
    STATE.reset()
    free_state()
    STATE.provider = "OtherCloud"
    p3 = run_free(free_args("sub3.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "3", "--out", out("sub3o.jsonl")])
    check(p3.returncode == 9 and STATE.count() == 1 and "OtherCloud" in p3.stderr, f"provider: exit {p3.returncode}")
    return ("served 'mock/free-model' for 'mock/free-model:free': exit 9 after 1 call; '<canonical>:free' accepted; "
            "served by 'OtherCloud' instead of the pinned endpoint: exit 9 after 1 call")


def t45_free_key_check_refusals():
    """The key must be a normal key that cannot spend (credit limit at most --max-key-headroom-usd, default 0), not
    expired, with the daily counter readable; refusals send no model request and show no secret field."""
    common = ["--suite", "pick", "--k", "1", "--limit", "1"]
    cases = [
        ("no credit limit", {"limit": None, "limit_remaining": None}, [], 5, "no credit limit"),
        ("0.5 USD headroom", {"limit": 5, "limit_remaining": 0.5}, [], 5, "0.5 USD left"),
        ("headroom just over the threshold", {"limit": 5, "limit_remaining": 0.5},
         ["--max-key-headroom-usd", "0.49"], 5, "0.5 USD left"),
        ("headroom at the threshold", {"limit": 5, "limit_remaining": 0.5}, ["--max-key-headroom-usd", "0.5"], 0, ""),
        ("--allow-key-headroom", {"limit": None, "limit_remaining": None}, ["--allow-key-headroom"], 0,
         "--allow-key-headroom"),
        ("management key", {"is_management_key": True}, ["--allow-key-headroom"], 5, "management key"),
        ("management flag missing", {"is_management_key": None}, [], 5, "management key"),
        ("expired key", {"expires_at": "2020-01-01T00:00:00Z"}, [], 5, "expired"),
    ]
    bad, detail = [], []
    for i, (name, over, extra, code, needle) in enumerate(cases):
        STATE.reset()
        free_state(**over)
        o = out(f"kc{i}.jsonl")
        p = run_free(free_args(f"kc{i}_ledger.jsonl") + common + extra + ["--out", o])
        sent = STATE.count()
        if p.returncode != code or (needle and needle not in p.stderr) or sent != (1 if code == 0 else 0) \
                or not no_secrets(p, o):
            bad.append(f"{name}: exit {p.returncode}, {sent} calls, {p.stderr.strip()[-160:]!r}")
        detail.append(f"{name} -> {p.returncode}")
    STATE.reset()
    free_state()
    STATE.free_daily_limit = None  # the key record has no free_model_daily_requests
    p = run_free(free_args("kc_nofm.jsonl") + common + ["--out", out("kc_nofm_o.jsonl")])
    if p.returncode != 5 or "free_model_daily_requests" not in p.stderr or STATE.count():
        bad.append(f"no daily counter: exit {p.returncode}")
    detail.append(f"no daily counter -> {p.returncode}")
    check(not bad, "; ".join(bad))
    return "; ".join(detail)


def t46_key_usage_rise_stops_the_run():
    """The key poll (every --key-poll-every attempts, and after the last call) stops the run with exit 9 as soon as
    the key's usage moves."""
    free_state()
    STATE.key_usage_per_chat = 0.0001
    o = out("rise.jsonl")
    p = run_free(free_args("rise_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "5", "--key-poll-every",
                                                   "2", "--out", o])
    check(p.returncode == 9 and STATE.count() == 2 and "usage rose" in p.stderr and stop_rows(o)[-1]["stop"] ==
          "NotFree", f"poll: exit {p.returncode}, {STATE.count()} calls")
    STATE.reset()
    free_state()
    STATE.key_usage_per_chat = 0.0001
    p2 = run_free(free_args("rise2_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "2", "--out",
                                                     out("rise2.jsonl")])
    check(p2.returncode == 9 and STATE.count() == 2 and "usage rose" in p2.stderr, f"end check: exit {p2.returncode}")
    return ("usage rising 0.0001 USD per call: with --key-poll-every 2 the run stopped before the 3rd call (exit 9); "
            "with 2 calls and the default poll, the check after the last call returned exit 9")


def t47_daily_cap_and_resume_across_a_day_boundary():
    """--max-requests-per-day stops the run cleanly (exit 10) with the resume time; a same-day --resume sends nothing;
    after the day boundary --resume finishes the remaining items without repeating any."""
    free_state()
    o, led = out("day.jsonl"), out("day_ledger.jsonl")
    args = free_args("day_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "5", "--max-requests-per-day",
                                            "3", "--out", o]
    p1 = run_free(args)
    stops = stop_rows(o)
    stop = stops[-1] if stops else {}
    check(p1.returncode == 10 and STATE.count() == 3 and stop.get("stop") == "DailyQuota" and stop.get("next_item")
          and "resume after" in p1.stderr and "T00:00:00Z" in p1.stderr,
          f"day 1: exit {p1.returncode}, {STATE.count()} calls, stop {stop.get('stop')}")
    p2 = run_free(args + ["--resume"])
    check(p2.returncode == 10 and STATE.count() == 3, f"same-day resume: exit {p2.returncode}, {STATE.count()} calls")
    _age_reserve_rows(led)
    STATE.requests.clear()  # the account's counter reset at 00:00 UTC too
    p3 = run_free(args + ["--resume"])
    recs = calls(rows(o))
    ids = [r["item_id"] for r in recs]
    check(p3.returncode == 0 and STATE.count() == 2 and len(ids) == 5 and len(set(ids)) == 5,
          f"next day: exit {p3.returncode}, {STATE.count()} calls, {len(ids)} records")
    return (f"cap 3: 3 calls then exit 10 (DailyQuota, next item {stop['next_item']}, resume time printed); same-day "
            f"--resume: exit 10, 0 calls; after the day boundary: 2 calls, 5 unique records, exit 0")


def t48_account_quota_reserve_and_resync():
    """The account's own remaining free requests less --daily-reserve cap the run, and the key poll re-reads them
    (another client using the quota mid-run lowers the allowance)."""
    free_state()
    STATE.free_used_offset = 43  # 7 left on the account, 5 kept in reserve -> 2 allowed
    p = run_free(free_args("aq1.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "5", "--out", out("aq1o.jsonl")])
    check(p.returncode == 10 and STATE.count() == 2, f"reserve: exit {p.returncode}, {STATE.count()} calls")
    STATE.reset()
    free_state()
    STATE.free_used_offset, STATE.external_use = 30, (2, 20)  # after 2 calls another client uses 20 more
    p2 = run_free(free_args("aq2.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "5", "--key-poll-every", "2",
                                            "--out", out("aq2o.jsonl")])
    check(p2.returncode == 10 and STATE.count() == 2, f"resync: exit {p2.returncode}, {STATE.count()} calls")
    STATE.reset()
    free_state()
    STATE.free_used_offset = 45  # 5 left, reserve 0 -> exactly 5 allowed
    p3 = run_free(free_args("aq3.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "5", "--daily-reserve", "0",
                                            "--out", out("aq3o.jsonl")])
    check(p3.returncode == 0 and STATE.count() == 5, f"boundary: exit {p3.returncode}, {STATE.count()} calls")
    return ("43 of 50 used, reserve 5: 2 calls then exit 10; 30 used and another client taking 20 mid-run: stopped at "
            "the next poll after 2 calls (exit 10); 45 used, reserve 0: exactly 5 calls, exit 0")


def t49_rate_limit_429s_daily_minute_upstream():
    """A daily-cap 429 is terminal (exit 10, never retried); a per-minute 429 waits for X-RateLimit-Reset; upstream
    429s honour Retry-After, count toward the day, and N in a row stop the run (exit 10)."""
    free_state()
    STATE.queue = [mock_server.daily_cap_429()] * 3
    o = out("q429.jsonl")
    p = run_free(free_args("q429_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "3", "--out", o])
    rec = calls(rows(o))[0]
    check(p.returncode == 10 and STATE.count() == 1 and "daily" in rec["error"] and stop_rows(o)[-1]["stop"] ==
          "DailyQuota" and "resume after" in p.stderr, f"daily 429: exit {p.returncode}, {STATE.count()} calls")
    STATE.reset()
    free_state()
    STATE.queue = [{"status": 200, "body": mock_server.daily_cap_429()["body"]}] * 3  # the same, inside an HTTP 200
    pe = run_free(free_args("q429e_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "3", "--out",
                                                     out("q429e.jsonl")])
    check(pe.returncode == 10 and STATE.count() == 1, f"daily 429 inside a 200: exit {pe.returncode}, "
                                                      f"{STATE.count()} calls")
    STATE.reset()
    free_state()
    minute = {"status": 429, "body": {"error": {"code": 429, "message": "Rate limit exceeded: free-models-per-min",
                                                "metadata": {"error_type": "rate_limit_exceeded"}}},
              "headers": {"X-RateLimit-Limit": "20", "X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "RESET_IN:1.0"}}
    STATE.queue = [minute]  # the mock sets the reset to 1 s after it sends the 429, in epoch milliseconds
    o2 = out("m429.jsonl")
    p2 = run_free(free_args("m429_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "1", "--retry-cap-s", "5",
                                                    "--out", o2])
    r2 = calls(rows(o2))[0]
    check(p2.returncode == 0 and r2["http_status_history"] == [429, 200] and 0.7 <= r2["retry_after_s"][0] <= 1.05,
          f"minute 429: exit {p2.returncode}, {r2['http_status_history']}, waited {r2['retry_after_s']}")
    STATE.reset()
    free_state()
    up = {"status": 429, "body": {"error": {"code": 429, "message": "mock/free-model:free is temporarily rate-limited "
                                            "upstream", "metadata": {"provider_name": "MockProvider", "raw": "busy"}}},
          "headers": {"Retry-After": "0"}}
    STATE.queue = [up, up]
    o3 = out("u429.jsonl")
    p3 = run_free(free_args("u429_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "1", "--out", o3])
    r3 = calls(rows(o3))[0]
    check(p3.returncode == 0 and r3["http_status_history"] == [429, 429, 200] and r3["rate_gate"]["attempts_today"]
          == 3 and r3["cost_usd"] == 0.0, f"upstream x2: exit {p3.returncode}, {r3['http_status_history']}")
    STATE.reset()
    free_state()
    STATE.queue = [up] * 5
    p4 = run_free(free_args("u429b_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "3", "--out",
                                                     out("u429b.jsonl")])
    check(p4.returncode == 10 and STATE.count() == 3 and "RateLimited" in p4.stderr,
          f"3 in a row: exit {p4.returncode}, {STATE.count()} calls")
    return (f"daily 429 (as HTTP 429, and inside a 200): exit 10 after 1 request, not retried; per-minute 429 with a "
            f"reset 1 s ahead: waited "
            f"{r2['retry_after_s'][0]} s, then 200; upstream 429 x2 then 200: 3 attempts counted today, cost 0; "
            f"upstream 429 x3: exit 10 RateLimited after 3 requests")


def t50_free_mode_units_known_values():
    """RateGate (minute window, day cap, day rollover, account counter, poll re-sync, ledger seeding, 429 streak),
    the reset and 429 parsers, exact-zero pricing, the zero-spend check and the key rules, against known values."""
    import datetime as dt
    import free_mode as fm
    import rate_gate as rg
    t = [dt.datetime(2026, 9, 27, 23, 58, 0, tzinfo=dt.timezone.utc).timestamp()]
    slept = []

    def sleep(s):
        slept.append(round(s, 2))
        t[0] += s
    g = rg.RateGate(rpm=3, per_day=5, clock=lambda: t[0], sleep=sleep)
    for _ in range(3):
        check(g.before_attempt() is None, "within the window")
        t[0] += 1
    check(g.before_attempt() is None and slept == [57.05], f"4th attempt waits for the window: {slept}")
    check(g.before_attempt() is None and g.used_local == 5, "5 attempts")
    stop = g.before_attempt()
    check(stop and stop[0] == "quota" and "2026-09-28T00:00:00Z" in stop[1], f"day cap: {stop}")
    t[0] += 120  # past 00:00 UTC
    check(g.before_attempt() is None and g.used_local == 1, "a new UTC day resets the count")
    # Account counter less the reserve, lowered per attempt and re-read at the poll (the lower figure wins).
    polls = []

    def poll():
        polls.append(1)
        return None, {"used": 48, "limit": 50, "remaining": 2}
    g2 = rg.RateGate(per_day=45, reserve=2, server={"used": 40, "limit": 50, "remaining": 10}, poll=poll,
                     poll_every=2, clock=lambda: t[0], sleep=sleep)
    check(g2.remaining_today() == 8, f"10 - 2 = {g2.remaining_today()}")
    got = [g2.before_attempt() is None for _ in range(3)]
    check(got == [True, True, False] and len(polls) == 1, f"poll re-sync to 2 left: {got}, {polls}")
    # Seeding from the ledger: today's reserve rows count; the last minute's fill the window.
    now = t[0]
    iso = lambda s: dt.datetime.fromtimestamp(s, dt.timezone.utc).isoformat(timespec="seconds")  # noqa: E731
    seed = [{"budget_event": "reserve", "ts": iso(now - 30)}, {"budget_event": "reserve", "ts": iso(now - 90)},
            {"budget_event": "reserve", "ts": iso(now - 86400)}, {"call_id": "x", "ts": iso(now)}]
    g3 = rg.RateGate(rpm=2, per_day=10, rows=seed, clock=lambda: t[0], sleep=sleep)
    check(g3.used_local == 1 and len(g3.window) == 1, f"seeded {g3.used_local} today, window {len(g3.window)}")
    g4 = rg.RateGate(max_429=3)
    check([g4.note_response(s) for s in (429, 429, 200, 429, 429, 429)] == [False, False, False, False, False, True],
          "429 streak")
    # Header and 429 parsing.
    n = 1_790_000_000.0
    check(rg.reset_seconds(str(int((n + 5) * 1000)), n) == 5.0 and rg.reset_seconds(str(n + 7), n) == 7.0
          and rg.reset_seconds("12", n) == 12.0 and rg.reset_seconds("soon", n) is None, "reset parsing")
    body = lambda m, meta=None: {"error": {"code": 429, "message": m, "metadata": meta or {}}}  # noqa: E731
    kinds = [rg.classify_429({}, body("Rate limit exceeded: free-models-per-day"), n)[0],
             rg.classify_429({"x-ratelimit-reset": str((n + 3600) * 1000)}, body("Rate limit exceeded"), n)[0],
             rg.classify_429({"x-ratelimit-reset": str((n + 20) * 1000), "x-ratelimit-limit": "20"},
                             body("Rate limit exceeded: free-models-per-min"), n),
             rg.classify_429({}, body("busy", {"provider_name": "X"}), n, retry_after=4.0),
             rg.classify_429({}, body("Rate limit exceeded"), n)[0]]
    check(kinds == ["daily", "daily", ("minute", 20.0), ("upstream", 4.0), "upstream"], str(kinds))
    # Exact zero: Decimal equality, nothing else.
    zeros = [fm.exact_zero(v) for v in ("0", "0.0", 0, 0.0, "-0", "0E-10")]
    others = [fm.exact_zero(v) for v in ("-1", "0.0000001", 1e-300, None, True, False, "NaN", "sNaN", "inf", "", [])]
    check(all(zeros) and not any(others), f"{zeros} {others}")
    check(fm.pricing_problems({"prompt": "0", "completion": "0", "discount": 0.25}, "p") == []
          and fm.pricing_problems({"prompt": "0"}, "p") == ["p: no completion price"]
          and len(fm.pricing_problems({"prompt": "0", "completion": "0", "internal_reasoning": "0.000001"}, "p")) == 1,
          "pricing problems")
    # Zero-spend check.
    tgt = {"model": "a/b:free", "canonical_slug": "a/b-2026", "providers": ["x/fp8", "X"]}
    ok = {"model": "a/b:free", "provider": "X", "usage": {"cost": 0}}
    sig = [fm.paid_signal(ok, tgt, True), fm.paid_signal(dict(ok, model="a/b-2026:free"), tgt, True),
           fm.paid_signal(dict(ok, usage={"cost": 1e-9}), tgt, True), fm.paid_signal(dict(ok, model="a/b"), tgt, True),
           fm.paid_signal({"error": {"code": 502}}, tgt, False), fm.paid_signal(dict(ok, provider="Y"), tgt, True)]
    check(sig[0] is None and sig[1] is None and "usage.cost" in sig[2] and "served by model" in sig[3]
          and sig[4] is None and "provider 'Y'" in sig[5], str(sig))
    # Key rules.
    summ = fm.key_summary(free_key())
    now_dt = dt.datetime(2026, 9, 27, tzinfo=dt.timezone.utc)
    check("label" not in summ and "creator_user_id" not in summ and summ["free_model_daily_requests"] is None
          and fm.key_refusal(summ, 0.0, False, now_dt).startswith("the key record has no free_model_daily"),
          "summary and refusal without the counter")
    summ["free_model_daily_requests"] = {"used": 0, "limit": 50, "remaining": 50}
    check(fm.key_refusal(summ, 0.0, False, now_dt) is None and "no credit limit" in fm.key_refusal(
        dict(summ, limit=None), 0.0, False, now_dt), "headroom rule")
    ids = [fm.free_model_refusal(m) is None for m in ("qwen/qwen3.8-27b:free", "openrouter/auto:free",
                                                      "qwen/qwen3.8-27b", "a/b:free:online", "A/b:free")]
    check(ids == [True, False, False, False, False], str(ids))
    return ("RateGate: 4th attempt in a minute waited 57.05 s, day cap 5 stopped with the 00:00 UTC resume time, a new "
            "day reset it; account 10 left - reserve 2, re-read 2 at the poll -> stop after 2; ledger seeding; 429 "
            "streak; reset in ms/s/delay; 429 kinds; Decimal zero (not -1, NaN, 1e-300); zero-spend and key rules")


# ── unittest wiring ──────────────────────────────────────────────────────────

class FreeOnlyTests(support.CaseTestCase):
    """The free-only mode's guards, caps and records (see the module docs)."""

    cases = (t40_free_only_offline_refusals,
             t41_free_catalogue_checks_refuse_traps,
             t42_free_happy_path_request_shape_and_records,
             t43_zero_spend_guard_stops_on_any_charge,
             t44_model_substitution_and_unexpected_provider_stop,
             t45_free_key_check_refusals,
             t46_key_usage_rise_stops_the_run,
             t47_daily_cap_and_resume_across_a_day_boundary,
             t48_account_quota_reserve_and_resync,
             t49_rate_limit_429s_daily_minute_upstream,
             t50_free_mode_units_known_values)

    def setUp(self):
        STATE.reset()


if __name__ == "__main__":
    unittest.main()
