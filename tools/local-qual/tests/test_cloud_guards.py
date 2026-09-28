#!/usr/bin/env python3
"""Adversarial checks of the paid path: each case encodes one break-in attempt found in review (a redirect
that would forward the key, a key or credential smuggled into the request, two processes on one ledger, a
stream or oversized body inside a 200, errors inside a 200, a cost reported as 0, an endpoint ignoring the
schema, reasoning text inside the answer, a ledger named in another letter case, a redirect whose target cannot be
parsed, an error body with an infinite code or nested past the JSON reader's depth). Each failed on the code as first
written and passes now.

Every case runs run.py (or another tool script) as a child process against mock_server.py, in-process on
127.0.0.1: nothing is spent and no real endpoint is contacted. cloud_support.py holds the dummy keys, the
helpers and the final key sweep that fails the module if any key or key label reached a file or a console
transcript.

Run the whole suite from the repository root with ``python -m unittest discover -s tools/local-qual/tests``;
the module docs of support.py explain the case functions and the environment switches.
"""

import json
import os
import subprocess
import sys
import unittest

import cloud_support
import support
from cloud_support import *  # noqa: F401,F403 - the shared fixtures the cases use by name

URL = None  # the mock's base URL while this module runs (set by setUpModule)


def setUpModule():
    global URL
    URL = cloud_support.start("cloud-guards")


def tearDownModule():
    cloud_support.finish()


# ── Adversarial review (t24-t37, t74, t76) ─────────────────────────────────────

def t24_redirects_are_refused_and_never_forward_the_key():
    """A 3xx from the endpoint (chat or GET /key) is never followed, so the bearer key cannot reach another URL.

    Python's urllib follows a POST 301/302/303 as a GET and every GET redirect, re-sending the Authorization header
    to the new location, which may be another host or plain http.
    """
    steal = root_url() + "/steal"
    STATE.queue = [{"status": 302, "body": {"error": {"code": 302, "message": "moved"}}, "headers": {"Location": steal}}]
    o = out("redirect.jsonl")
    p = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "2", "--max-usd", "1", "--out", o])
    stolen = [r for r in STATE.requests if r["path"].endswith("/steal")]
    check(not stolen, f"the client followed the redirect and sent {len(stolen)} request(s) to /steal "
                      f"(Authorization forwarded: {any('Authorization' in r['headers'] for r in stolen)})")
    check(p.returncode == 5 and STATE.count() == 1, f"chat redirect: exit {p.returncode}, {STATE.count()} calls")
    r = calls(rows(o))[0]
    check(r["cost_usd"] == 0.0 and "redirect" in r["error"], f"a refused redirect is unbilled: {r.get('cost_usd')}")
    STATE.reset()
    STATE.key_redirect = steal
    p2 = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "1", "--max-usd", "1", "--key-check",
                               "--out", out("redirect_key.jsonl")])
    stolen = [r for r in STATE.requests if r["path"].endswith("/steal")]
    check(not stolen and p2.returncode == 5 and STATE.count() == 0, f"key check redirect: exit {p2.returncode}, "
                                                                     f"{len(stolen)} to /steal")
    return "chat 302 and GET /key 302: 0 requests to the redirect target, exit 5, the refused attempt unbilled"


def t25_key_extra_body_and_flag_hygiene_refusals():
    """Keys with whitespace, keys inside the URL or --extra-body, credential fields, billed extras, conflicting
    reasoning fields, schema-weakening strips and unsafe numeric flags are refused before any request."""
    common = ["--suite", "pick", "--k", "1", "--limit", "1", "--max-usd", "1", "--out", out("hyg.jsonl")]
    # A trailing newline (PowerShell Get-Content -Raw, a key file) is stripped; the run works.
    p = run_tool(base(URL) + common, env_extra={ENV_NAME: KEY + "\r\n"})
    check(p.returncode == 0 and KEY not in p.stdout + p.stderr, f"trailing newline: exit {p.returncode}")
    check(all(r["headers"].get("Authorization") == f"Bearer {KEY}" for r in STATE.requests), "key not stripped")
    n0 = STATE.count()
    cases = [
        ("CRLF inside the key", base(URL) + common, {ENV_NAME: KEY[:10] + "\r\n" + KEY[10:]}, "control"),
        ("short key", base(URL) + common, {ENV_NAME: "abc"}, "shorter than"),
        ("key in the base URL", [a if a != URL else URL + "/" + KEY for a in base(URL)] + common, None,
         "contains the API key"),
        ("credential field", base(URL) + common + ["--extra-body", '{"provider": {"api_key": "x-123456789"}}'], None,
         "looks like a credential"),
        ("key value in extra body", base(URL) + common + ["--extra-body", json.dumps({"user": KEY})], None,
         "contains the API key"),
        ("fallback models", base(URL) + common + ["--extra-body", '{"models": ["a/b", "c/d"]}'], None, "models"),
        ("web plugin", base(URL) + common + ["--extra-body", '{"plugins": [{"id": "web"}]}'], None, "plugins"),
        ("web search", base(URL) + common + ["--extra-body", '{"web_search_options": {}}'], None,
         "web_search_options"),
        ("prompt field", base(URL) + common + ["--extra-body", '{"prompt": "extra text"}'], None, "prompt"),
        (":online model", [a if a != "mock/model-1" else "mock/model-1:online" for a in base(URL)] + common, None,
         ":online"),
        ("reasoning_effort with --reasoning none", base(URL) + common + ["--extra-body", '{"reasoning_effort": "high"}'],
         None, "--reasoning omit"),
        ("strip enum", base(URL) + common + ["--schema-strip", "enum"], None, "--schema-strip"),
        ("zero prices", [a if a != "1.0" else "0" for a in base(URL)] + common, None, "--free-only"),
        ("negative backoff", base(URL) + common + ["--retry-base-s", "-1"], None, "--retry-base-s"),
        ("zero output cap", base(URL) + common + ["--num-predict", "0"], None, "--num-predict"),
        ("tokens per byte", base(URL) + common + ["--est-tokens-per-byte", "0.01"], None, "--est-tokens-per-byte"),
    ]
    bad = []
    for name, argv, env, needle in cases:
        q = run_tool(argv, env_extra=env)
        if not refused(q, needle) or KEY in q.stdout + q.stderr:
            bad.append(f"{name}: exit {q.returncode}, stderr {q.stderr.strip()[-160:]!r}")
    check(not bad, "; ".join(bad))
    check(STATE.count() == n0, f"{STATE.count() - n0} requests reached the server during the refusals")
    # --reasoning omit may carry a provider's own effort field (the README's escape hatch).
    omit = base(URL)
    omit[omit.index("--reasoning") + 1] = "omit"
    q = run_tool(omit + ["--suite", "pick", "--items", "PW01", "--dry-run", "--extra-body", '{"reasoning_effort": "none"}'])
    body, _ = json.JSONDecoder().raw_decode(q.stdout)
    check(q.returncode == 0 and body.get("reasoning_effort") == "none" and "reasoning" not in body, "omit escape hatch")
    return (f"trailing CRLF stripped (run ok); {len(cases)} refusals (exit 2, key never echoed), 0 requests; "
            f"--reasoning omit still passes reasoning_effort")


def t26_ledger_lock_blocks_a_second_process():
    """Two processes on one ledger cannot both spend up to the cap: the second refuses while the first runs."""
    import time
    led = out("lock_ledger.jsonl")
    STATE.delay_s = 0.4
    env = dict(os.environ, PYTHONIOENCODING="utf-8", **{ENV_NAME: KEY})
    env.pop("LLAMA_API_KEY", None)
    a = subprocess.Popen([sys.executable, os.path.join(TOOL, "run.py")] + base(URL) +
                         ["--suite", "pick", "--k", "1", "--limit", "5", "--max-usd", "1", "--ledger", led,
                          "--out", out("lockA.jsonl")], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, encoding="utf-8")
    deadline = time.monotonic() + 30
    while STATE.count() == 0 and time.monotonic() < deadline:
        time.sleep(0.05)
    b = run_tool(base(URL) + ["--suite", "fill", "--k", "1", "--limit", "5", "--max-usd", "1", "--ledger", led,
                              "--out", out("lockB.jsonl")])
    sa, ea = a.communicate(timeout=120)
    LOGS.append(sa + ea)
    STATE.delay_s = 0.0
    fill_calls = sum(1 for r in STATE.requests if r["body"] and "Fill these fields" in json.dumps(r["body"]))
    check(fill_calls == 0 and b.returncode == 5 and "in use by another run" in b.stderr,
          f"second process: exit {b.returncode}, {fill_calls} fill calls sent")
    check(a.returncode == 0 and len(calls(rows(out("lockA.jsonl")))) == 5, f"first process exit {a.returncode}")
    check(not os.path.exists(led + ".lock"), "the lock outlived its run")
    # A lock left by a killed run blocks too (fail closed) and says how to clear it.
    write_text(led + ".lock", '{"pid": 1}')
    n = STATE.count()
    c = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "1", "--max-usd", "1", "--ledger", led,
                              "--out", out("lockC.jsonl")])
    check(c.returncode == 5 and "delete" in c.stderr and STATE.count() == n, f"stale lock: exit {c.returncode}")
    os.remove(led + ".lock")
    # A run that stops at start (cap used up) releases its lock.
    d = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "1", "--max-usd", "0.0000001", "--ledger", led,
                              "--out", out("lockD.jsonl")])
    check(d.returncode == 4 and not os.path.exists(led + ".lock"), f"used-up cap: exit {d.returncode}, lock left")
    return ("run B on A's ledger while A ran: exit 5, 0 calls; A finished its 5 calls and removed the lock; a stale "
            "lock blocks (exit 5); a run stopped at start releases its lock")


def t27_non_json_200_and_oversize_body_stop_without_retry():
    """A 200 that is not a JSON completion (a stream despite stream=false, a portal page, a huge body) stops the run
    after one attempt instead of being retried and charged again and again."""
    sse = 'data: {"choices": [{"delta": {"content": "{"}}]}\n\ndata: [DONE]\n\n'
    STATE.queue = [{"status": 200, "body": sse}] * 5
    p = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "3", "--max-usd", "1", "--out", out("sse.jsonl")])
    r = calls(rows(out("sse.jsonl")))[0]
    check(p.returncode == 5 and STATE.count() == 1, f"stream body: exit {p.returncode}, {STATE.count()} requests")
    check(abs(r["cost_usd"] - r["reserved_usd"]) < 1e-12, "a 200 of unknown content is charged its reservation")
    STATE.reset()
    STATE.queue = [{"status": 200, "body": '{"pad": "' + "x" * (9 * 1024 * 1024) + '"}'}] * 3
    p2 = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "2", "--max-usd", "1", "--out",
                               out("huge.jsonl")])
    check(p2.returncode == 5 and STATE.count() == 1, f"9 MiB body: exit {p2.returncode}, {STATE.count()} requests")
    return "SSE body inside a 200: exit 5 after 1 request, charged its reservation; 9 MiB body: exit 5 after 1 request"


def t28_embedded_402_and_401_in_http_200_stop():
    """Out of credits or a bad key reported inside a 200 stops the run like the HTTP status would."""
    STATE.queue = [{"status": 200, "body": {"error": {"code": 402, "message": "Insufficient credits"}}}] * 3
    p = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "3", "--max-usd", "1", "--out",
                              out("e402.jsonl")])
    check(p.returncode == 4 and STATE.count() == 1, f"402 in 200: exit {p.returncode}, {STATE.count()} requests")
    STATE.reset()
    STATE.queue = [{"status": 200, "body": {"error": {"code": 401, "message": "No auth credentials found"}}}] * 3
    p2 = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "3", "--max-usd", "1", "--out",
                               out("e401.jsonl")])
    check(p2.returncode == 5 and STATE.count() == 1, f"401 in 200: exit {p2.returncode}, {STATE.count()} requests")
    return "402 inside a 200: exit 4 after 1 request; 401 inside a 200: exit 5 after 1 request"


def t29_cost_anomaly_on_a_failed_attempt_stops_before_the_retry():
    """An attempt that costs more than its worst case stops the call at once, even when it failed and would retry."""
    STATE.queue = [{"status": 200, "body": {"error": {"code": 502, "message": "upstream"}, "usage": {"cost": 5.0}}}]
    o = out("anom_retry.jsonl")
    p = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "3", "--max-usd", "10", "--out", o])
    check(p.returncode == 4 and "CostAnomaly" in p.stderr and STATE.count() == 1,
          f"exit {p.returncode}, {STATE.count()} requests")
    from budget import Budget, read_ledger_rows
    spent = Budget(10, 1, 1, rows=read_ledger_rows(o)).spent()
    check(abs(spent - 5.0) < 1e-9, f"the ledger holds {spent}")
    return "5 USD reported on a 502-inside-200 attempt: exit 4 CostAnomaly after 1 request (no retry); ledger 5.0"


def t30_settles_at_the_higher_of_provider_and_computed_cost():
    """A provider that reports cost 0 for billed tokens is charged at the price flags instead (never under-count)."""
    STATE.cost_multiplier = 0.0
    o = out("zero_cost.jsonl")
    p = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "1", "--max-usd", "1", "--out", o])
    r = calls(rows(o))[0]
    u = r["usage"]
    want = (u["prompt_tokens"] + u["completion_tokens"]) / 1e6
    check(p.returncode == 0 and abs(r["cost_usd"] - want) < 1e-12 and r["cost_source"] == "computed>provider",
          f"cost {r['cost_usd']} ({r['cost_source']}), want {want}")
    return f"usage.cost 0 with {u['prompt_tokens']}+{u['completion_tokens']} tokens: charged {want:.8f} (computed>provider)"


def t31_estimate_counts_unknown_body_fields():
    """Text a provider may put into the prompt from an unknown body field is part of the worst case."""
    from budget import Budget
    b = Budget(1.0, 1.0, 1.0)
    base_body = {"messages": [{"role": "user", "content": "x"}], "max_tokens": 10,
                 "provider": {"only": ["a/b"]}, "temperature": 0.6, "seed": 1}
    e0 = b.estimate(base_body)["prompt_tokens_est"]
    e1 = b.estimate(dict(base_body, prompt="y" * 1000))["prompt_tokens_est"]
    check(e1 - e0 >= 1300, f"{e0} -> {e1}")
    return f"a 1,000-byte unknown field raises the prompt estimate from {e0} to {e1} tokens"


def t32_ignored_response_format_trips_the_canary():
    """An endpoint that silently ignores the strict schema (fenced or off-schema JSON) is caught by the canary."""
    STATE.answer_fn = lambda body: '```json\n{"choice": "A"}\n```'
    o = out("ignored_schema.jsonl")
    p = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "10", "--max-usd", "1", "--canary", "5",
                              "--out", o])
    rs = calls(rows(o))
    check(all(r["parse_ok"] for r in rs), "the fenced answers parse (the old canary saw no failure)")
    check(p.returncode == 7 and STATE.count() == 5 and all(r.get("schema_conformant") is False for r in rs),
          f"exit {p.returncode}, {STATE.count()} requests, conformant {[r.get('schema_conformant') for r in rs]}")
    STATE.reset()
    STATE.answer_fn = lambda body: '{"choice": "Z"}'
    p2 = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "10", "--max-usd", "1", "--canary", "5",
                               "--out", out("offschema.jsonl")])
    check(p2.returncode == 7 and STATE.count() == 5, f"off-enum answers: exit {p2.returncode}")
    STATE.reset()
    p3 = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "6", "--max-usd", "1", "--canary", "5",
                               "--out", out("conformant.jsonl")])
    check(p3.returncode == 0 and all(r["schema_conformant"] for r in calls(rows(out("conformant.jsonl")))),
          "conformant answers must pass")
    # An engine that enforces structure but ignores maxLength is still enforcing the schema: no false stop.
    STATE.reset()

    def long_strings(schema):
        v = mock_server.value_for(schema)
        return {k: ("x" * 400 if isinstance(x, str) and "enum" not in schema["properties"][k] else x)
                for k, x in v.items()}
    STATE.answer_fn = lambda body: json.dumps(long_strings(body["response_format"]["json_schema"]["schema"]))
    o4 = out("longfill.jsonl")
    p4 = run_tool(base(URL) + ["--suite", "explain", "--k", "1", "--limit", "5", "--max-usd", "1", "--canary", "5",
                               "--condition", "cards", "--out", o4])
    r4 = calls(rows(o4))
    check(p4.returncode == 0 and all(r["schema_conformant"] for r in r4), f"length-only violations: exit "
                                                                          f"{p4.returncode}")
    return ("fenced JSON and an off-enum letter on the strict arm: exit 7 after the 5-call canary; conformant arm "
            "passes; over-length strings in a well-formed record do not trip it")


def t33_openrouter_schema_arm_requires_require_parameters():
    """On OpenRouter a strict-schema arm must set provider.require_parameters, or it could be routed to an endpoint
    that ignores response_format (checked with --dry-run: nothing is sent either way)."""
    orr = ["--backend", "openai", "--model", "a/b", "--base-url", "https://openrouter.ai/api/v1", "--reasoning", "none",
           "--suite", "pick", "--items", "PW01", "--dry-run"]
    pin = {"provider": {"only": ["x/bf16"], "allow_fallbacks": False}}
    p = run_tool(orr + ["--extra-body", json.dumps(pin)])
    check(refused(p, "require_parameters"), f"unpinned schema arm: exit {p.returncode}")
    pin["provider"]["require_parameters"] = True
    p2 = run_tool(orr + ["--extra-body", json.dumps(pin)])
    del pin["provider"]["require_parameters"]
    p3 = run_tool(orr + ["--extra-body", json.dumps(pin), "--schema-mode", "none"])
    check(p2.returncode == 0 and p3.returncode == 0, f"{p2.returncode} {p3.returncode}")
    return "strict arm without require_parameters: exit 2; with it: ok; the no-schema arm does not need it"


def t34_think_blocks_are_stripped_before_parsing():
    """A reasoning block in the content never supplies the answer, and on an effort-none call it stops the run."""
    STATE.answer_fn = lambda body: '<think>maybe {"choice": "B"}</think>\n{"choice": "A"}'
    args = base(URL)
    args[args.index("--reasoning") + 1] = "low"
    o = out("think.jsonl")
    p = run_tool(args + ["--suite", "pick", "--items", "PW01", "--k", "1", "--max-usd", "1", "--out", o])
    r = calls(rows(o))[0]
    check(p.returncode == 0 and r["chosen_letter"] == "A" and r.get("think_stripped") is True,
          f"exit {p.returncode}, chose {r.get('chosen_letter')}")
    STATE.requests.clear()
    o2 = out("think_none.jsonl")
    p2 = run_tool(base(URL) + ["--suite", "pick", "--items", "PW01,PW02", "--k", "1", "--max-usd", "1", "--out", o2])
    r2 = calls(rows(o2))[0]
    check(p2.returncode == 7 and "ReasoningLeak" in p2.stderr and r2["error"] and STATE.count() == 1,
          f"effort none: exit {p2.returncode}, error {r2.get('error')!r}")
    # Knowledge graders see the answer, not the thinking.
    STATE.answer_fn = lambda body: "<think>a private draft</think>\nFinal answer."
    o3 = out("think_knowledge.jsonl")
    p3 = run_tool(args + ["--suite", "knowledge", "--items", "T01", "--k", "1", "--max-usd", "1", "--out", o3])
    ps = run_py("score.py", [o3, "--csv", out("tk.csv"), "--json", out("tk.json"), "--grading-out", out("tk_sheet.jsonl")])
    sheet = rows(out("tk_sheet.jsonl"))
    check(p3.returncode == 0 and ps.returncode == 0 and sheet and sheet[0]["answer"] == "Final answer.",
          f"grading sheet answer {sheet[0]['answer'] if sheet else None!r}")
    return ("'<think>{B}</think>{A}' scored A (was B); on effort none: ReasoningLeak exit 7 after 1 call, the record "
            "is an error so it is neither scored nor skipped by --resume; the knowledge grading sheet gets the answer "
            "without the thinking")


def t36_ledger_path_compared_case_insensitively_on_windows():
    """On Windows, --ledger naming the output file in another letter case is the same file, not a second ledger."""
    if os.name != "nt":
        return "skipped (not Windows)"
    o = out("case.jsonl")
    p = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "2", "--max-usd", "1", "--ledger",
                              o.upper(), "--out", o])
    rs = rows(o)
    check(p.returncode == 0 and not any(r.get("budget_event") == "settle" for r in rs),
          f"exit {p.returncode}; settle rows written: the file was opened as a second ledger")
    return "--ledger in upper case of --out: one ledger (no duplicate settle rows)"


def t37_no_ledger_note_and_warning_free_pinned_run():
    """A run without --ledger says the cap covers only its own output file."""
    p = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "1", "--max-usd", "1", "--out",
                              out("note.jsonl")])
    check(p.returncode == 0 and "--ledger" in p.stderr, "no note about the per-file cap")
    return "note printed: the cap covers only this output file unless --ledger is given"


def t74_unreadable_redirect_target_is_a_config_stop_not_a_crash():
    """A 3xx whose Location cannot be parsed stops the run as a refused redirect (exit 5, unbilled), not a traceback.

    Why: urllib parses Location only on the codes it would follow (301, 302, 303, 307, 308), so a 300 reaches the
    redirect branch with a Location such as ``http://[bad`` intact, and reading its host raised ValueError out of
    chat(): exit 1 with a traceback, the call never settled and no record naming the fix. Found in the review of
    ``--key-status``, whose failure line reads the same header.
    """
    STATE.queue = [{"status": 300, "body": {"error": {"code": 300, "message": "choices"}},
                    "headers": {"Location": "http://[bad/x"}}]
    o = out("redirect_300.jsonl")
    p = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "1", "--max-usd", "1", "--out", o])
    rs = calls(rows(o)) if os.path.exists(o) else []
    check(p.returncode == 5 and "Traceback" not in p.stderr and STATE.count() == 1,
          f"exit {p.returncode}, {STATE.count()} calls, stderr {p.stderr[-300:]!r}")
    check(rs and rs[0]["cost_usd"] == 0.0 and "redirect" in rs[0]["error"], f"record {rs[:1]!r}")
    return "HTTP 300 with an unparsable Location: exit 5, 1 call, the record names the redirect, unbilled"


# Hostile error bodies (t76). JSON text, sent by the mock exactly as written: Python's json module reads 1e999,
# Infinity and -Infinity as float infinity. DEEP nests 5,000 levels (10 KB), past the depth the JSON reader handles
# (about 3,000 on Python 3.12), yet far under the 8 MiB body cap.
INF_CODE = '{"error": {"code": 1e999, "message": "busy"}}'
NEG_INF_CODE = '{"error": {"code": -Infinity, "message": "busy"}}'
INF_IN_CHOICE = '{"choices": [{"error": {"code": Infinity, "message": "busy"}}]}'
DEEP = "[" * 5000 + "]" * 5000
DEEP_META = '{"error": {"code": 429, "message": "busy", "metadata": ' + '{"a": ' * 5000 + "1" + "}" * 5000 + "}}"


def t76_hostile_error_bodies_never_crash_the_call():
    """An error body whose ``code`` is not a finite number (1e999, Infinity) or that nests deeper than the JSON reader
    goes ends its attempt like any other unreadable error, never with a traceback: as HTTP 200, 400, 429 or 503,
    in-process with a budget and a rate gate, and through run.py on a paid and a free run.

    Why: ``int()`` of an infinite code raised OverflowError out of ``_code_and_message``, and a deep body raised
    RecursionError out of ``_json_or_none`` (both caught only ValueError). Either left ``chat()`` before the call
    settled: the attempt's reservation stayed booked as spent, and run.py died with exit 1, no record and no stop
    row. Found in the adversarial review of the 429 fixes (r09-r14): the streak reads every 200's error code before
    counting it, and a gated 429 records its body's text. key_status.py already catches RecursionError.

    How: in-process calls use max_attempts 3, a Budget (1 USD per million tokens) and a paid gate (``--rpm``); the
    call must have settled exactly what it recorded. The child runs read the exit code, the stop rows and the ledger.
    """
    import random
    import cloud_backend
    import rate_gate
    from budget import Budget, read_ledger_rows
    chat_body = {"model": "mock/model-1", "messages": [{"role": "user", "content": "Pick A or B."}], "stream": False,
                 "max_tokens": 16}
    # (name, HTTP status, body, attempts, fatal): unreadable errors retry on 429 and 5xx, stop on a 4xx or a 200.
    table = [("200, code 1e999", 200, INF_CODE, 1, None), ("200, Infinity in a choice", 200, INF_IN_CHOICE, 1, None),
             ("400, code 1e999", 400, INF_CODE, 1, "config"), ("429, code 1e999", 429, INF_CODE, 3, None),
             ("503, code -Infinity", 503, NEG_INF_CODE, 3, None), ("200, nested", 200, DEEP, 1, "config"),
             ("429, nested metadata", 429, DEEP_META, 3, None), ("503, nested", 503, DEEP, 3, None)]
    bad = []
    for name, status, raw, attempts, fatal in table:
        STATE.reset()
        STATE.queue = [{"status": status, "body": raw}] * attempts
        budget = Budget(1.0, 1.0, 1.0)
        backend = cloud_backend.OpenAICompatBackend(URL, 10.0, None, max_attempts=3, sleep=lambda s: None,
                                                    rng=random.Random(7))
        backend.gate = rate_gate.RateGate(rpm=100)
        try:
            r = backend.chat(dict(chat_body), budget, "c1")
        except (OverflowError, RecursionError, ValueError) as e:
            bad.append(f"{name}: chat raised {type(e).__name__}, {budget.spent():.8f} USD left reserved")
            continue
        x = r["extra"]
        if x["attempts"] != attempts or r["fatal"] != fatal or not r["error"] or budget.spent() != x["cost_usd"]:
            bad.append(f"{name}: {x['attempts']} attempts, fatal {r['fatal']}, spent {budget.spent()} for a record of "
                       f"{x['cost_usd']}, error {str(r['error'])[:80]!r}")
    check(not bad, "; ".join(bad))
    # ── Through run.py: a paid run gets an infinite code inside a 200, a free run nested 429s (its streak stops it) ──
    STATE.reset()
    STATE.queue = [{"status": 200, "body": INF_CODE}] * 2
    o = out("hostile_paid.jsonl")
    p = run_tool(base(URL) + ["--suite", "pick", "--k", "1", "--limit", "2", "--max-usd", "1", "--out", o])
    recs = calls(rows(o)) if os.path.exists(o) else []
    spent = Budget(1, 1, 1, rows=read_ledger_rows(o)).spent() if os.path.exists(o) else None
    check(p.returncode == 2 and "Traceback" not in p.stderr and len(recs) == 2 and STATE.count() == 2
          and all("code None" in (r["error"] or "") for r in recs)
          and spent is not None and abs(spent - sum(r["cost_usd"] for r in recs)) < 1e-12,
          f"paid: exit {p.returncode}, {len(recs)} records, spent {spent}, stderr {p.stderr.strip()[-240:]!r}")
    STATE.reset()
    free_state()
    STATE.queue = [{"status": 429, "body": DEEP_META}] * 3
    o2, led = out("hostile_free.jsonl"), out("hostile_free_ledger.jsonl")
    p2 = run_free(free_args("hostile_free_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "2", "--out", o2])
    check(p2.returncode == 10 and "Traceback" not in p2.stderr and STATE.count() == 3
          and [s["stop"] for s in stop_rows(o2)][-1:] == ["RateLimited"] and no_secrets(p2, o2, led),
          f"free: exit {p2.returncode}, {STATE.count()} requests, stderr {p2.stderr.strip()[-240:]!r}")
    return (f"{len(table)} hostile bodies in-process: no exception, each call settled what it recorded; paid run.py: "
            f"exit 2, 2 records; free run.py with nested 429s: exit 10 RateLimited after 3 requests")


# ── unittest wiring ──────────────────────────────────────────────────────────

class AdversarialGuardTests(support.CaseTestCase):
    """Break-in attempts against the paid path (see the module docs)."""

    cases = (t24_redirects_are_refused_and_never_forward_the_key,
             t25_key_extra_body_and_flag_hygiene_refusals,
             t26_ledger_lock_blocks_a_second_process,
             t27_non_json_200_and_oversize_body_stop_without_retry,
             t28_embedded_402_and_401_in_http_200_stop,
             t29_cost_anomaly_on_a_failed_attempt_stops_before_the_retry,
             t30_settles_at_the_higher_of_provider_and_computed_cost,
             t31_estimate_counts_unknown_body_fields,
             t32_ignored_response_format_trips_the_canary,
             t33_openrouter_schema_arm_requires_require_parameters,
             t34_think_blocks_are_stripped_before_parsing,
             t36_ledger_path_compared_case_insensitively_on_windows,
             t37_no_ledger_note_and_warning_free_pinned_run,
             t74_unreadable_redirect_target_is_a_config_stop_not_a_crash,
             t76_hostile_error_bodies_never_crash_the_call)

    def setUp(self):
        STATE.reset()


if __name__ == "__main__":
    unittest.main()
