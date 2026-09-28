#!/usr/bin/env python3
"""Tests for ``run.py --key-status --provider groq|cloudflare`` (provider_status.py): check a stored key or token
without running a model.

* k01: Groq: one ``GET <base>/models`` with the key; the report says the key was accepted, which models of the
  free-plan table are listed (active, context, output cap), which rate-limit headers the reply carried, and whether
  they show the Free plan (limits above it name the exit 9 a run would take).
* k02: every Groq failure (401, 403, 404, 429, 5xx, a redirect, a body that is not a model list, no connection)
  ends with one line naming the next step and the same exit codes as OpenRouter's key status (5, 10, 3); a body or a
  redirect target that echoes the key shows it redacted.
* k03: Cloudflare: token verify (the account path for an account token, the user path for a user token) and one
  model search per table model; the report gives the token's status and expiry, whether the account is reachable,
  which models are listed, and the day's neuron allocation; the account id is never printed.
* k04: every Cloudflare failure: a refused or expired token, a search the token may not run (Workers AI Read), a
  429, a 5xx; refusals before sending (no account id, the Global API Key, another host).
* k05: ``--key-status`` added to a full provider run line reads only: no chat, no ledger, no lock, and a note
  names the flags it skipped.

Every case runs run.py as a child process against mock_server.py, in-process on 127.0.0.1, with random dummy keys and
a random dummy account id: nothing is spent and no real endpoint is contacted. The final sweep fails the module if a
dummy secret reached a file or a console transcript.

Run the whole suite from the repository root with ``python -m unittest discover -s tools/local-qual/tests``.
"""
import os
import socket
import unittest

import cloud_support
import support
from provider_support import *  # noqa: F401,F403 - the shared fixtures the cases use by name

URL = None  # the mock's base URL while this module runs (set by setUpModule)
GROQ_LIST = {"object": "list", "data": [
    {"id": "openai/gpt-oss-20b", "object": "model", "active": True, "context_window": 131072,
     "max_completion_tokens": 65536, "owned_by": "OpenAI"},
    {"id": "qwen/qwen3.8-27b", "object": "model", "active": False, "context_window": 131072,
     "max_completion_tokens": 16384, "owned_by": "Alibaba Cloud"}]}
FREE_HEADERS = {"x-ratelimit-limit-requests": "1000", "x-ratelimit-remaining-requests": "998",
                "x-ratelimit-limit-tokens": "8000", "x-ratelimit-remaining-tokens": "8000"}


def setUpModule():
    global URL
    URL = cloud_support.start("provider-status")


def tearDownModule():
    cloud_support.finish()


# ── Helpers ──────────────────────────────────────────────────────────────────

def groq_ks(base=None):
    """The shortest Groq key-status line against the mock."""
    return ["--provider", "groq", "--key-status", "--base-url", base or cloud_support.URL, "--api-key-env", GROQ_ENV]


def cf_ks(base=None):
    """The shortest Cloudflare key-status line against the mock."""
    return ["--provider", "cloudflare", "--key-status", "--base-url", base or cf_root(), "--api-key-env", CF_ENV,
            "--account-id-env", ACCT_ENV]


def gets():
    """The GET requests the mock received."""
    return [r for r in STATE.requests if r["body"] is None]


def closed_port():
    """A loopback port with nothing listening (bound, then closed at once)."""
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


# ── Groq ─────────────────────────────────────────────────────────────────────

def k01_groq_key_status_reports_models_and_limit_headers():
    """One GET /models with the key; the report names each free-plan model as listed or not, the reply's limit
    headers, and whether they are the Free plan's; paid-tier headers are named with the exit 9 a run would take.

    Why: a model list costs no tokens, and its reply shows at once whether the key works and which of the table's
    models the organisation can call, before any run spends one of the day's requests.
    """
    STATE.get_queue = [{"status": 200, "body": GROQ_LIST, "headers": FREE_HEADERS}]
    p = run_groq(groq_ks())
    want = ["key: accepted", "openai/gpt-oss-20b: listed, active, context 131072, max completion 65536",
            "qwen/qwen3.8-27b: listed, not active", "openai/gpt-oss-120b: not listed",
            "x-ratelimit-limit-requests 1000", "within the Free plan"]
    missing = [w for w in want if w not in p.stdout]
    check(p.returncode == 0 and not missing, f"exit {p.returncode}; missing {missing}; {p.stdout!r} {p.stderr[-300:]!r}")
    g = gets()
    check(len(g) == 1 and g[0]["path"] == "/api/v1/models" and g[0]["headers"].get("Authorization") ==
          f"Bearer {GROQ_KEY}" and not chat_requests(), f"requests {[r['path'] for r in STATE.requests]}")
    check(provider_clean(p), "a dummy secret was printed")
    verdicts = {}
    for name, headers in (("paid", dict(FREE_HEADERS, **{"x-ratelimit-limit-requests": "14400"})), ("none", {})):
        STATE.reset()
        STATE.get_queue = [{"status": 200, "body": GROQ_LIST, "headers": headers}]
        q = run_groq(groq_ks())
        verdicts[name] = (q.returncode, "above the Free plan" in q.stdout and "exit 9" in q.stdout,
                          "no rate-limit headers" in q.stdout)
    check(verdicts == {"paid": (0, True, False), "none": (0, False, True)}, f"verdicts {verdicts}")
    return f"report lines {len(want)} present; paid-tier and missing headers named: {verdicts}"


def k02_groq_key_status_failures_name_the_next_step():
    """Each failure is one line on stderr naming the next step, with OpenRouter's exit codes: 5 for the key or the
    URL (401, 403, 404, a redirect, not a model list), 10 for 429, 3 for 5xx or no answer; echoed keys are redacted.
    """
    cases = [
        ({"status": 401, "body": {"error": {"message": "Invalid API Key", "type": "invalid_request_error"}}}, 5,
         "set-provider-key.ps1 -Provider groq -Force"),
        ({"status": 403, "body": {"error": {"message": "forbidden"}}}, 5, "HTTP 403"),
        ({"status": 404, "body": {"error": {"message": "not found"}}}, 5, "--base-url"),
        ({"status": 429, "body": {"error": {"message": "slow down"}}, "headers": {"retry-after": "3"}}, 10, "wait"),
        ({"status": 503, "body": {"error": {"message": "over capacity"}}}, 3, "try again"),
        ({"status": 500, "body": "ECHO_AUTH"}, 3, "try again"),
        ({"status": 302, "body": {"error": "moved"}, "headers": {"Location": f"https://relay.example/{GROQ_KEY}"}}, 5,
         "redirect"),
        ({"status": 200, "body": "<html>portal</html>"}, 5, "not a model list"),
    ]
    bad = []
    for scripted, code, needle in cases:
        STATE.reset()
        STATE.get_queue = [scripted]
        p = run_groq(groq_ks())
        lines = [ln for ln in p.stderr.splitlines() if ln.strip()]
        if p.returncode != code or needle not in p.stderr or len(lines) != 1 or not provider_clean(p):
            bad.append(f"{scripted['status']}: exit {p.returncode}, {p.stderr[-300:]!r}")
    q = run_groq(groq_ks(f"http://127.0.0.1:{closed_port()}/openai/v1"))
    if q.returncode != 3 or "could not reach" not in q.stderr:
        bad.append(f"no connection: exit {q.returncode}, {q.stderr[-200:]!r}")
    check(not bad, "; ".join(bad))
    return f"{len(cases) + 1} failures, each one line with the documented exit code and no key shown"


# ── Cloudflare ───────────────────────────────────────────────────────────────

def k03_cloudflare_key_status_verifies_the_token_and_searches_the_models():
    """An account token is verified at the account's path, a user token at the user path; every table model is
    searched once; the report gives the status, the expiry, the listed models and the neuron allocation, and never
    the account id.

    Why: token verify and model search run no model, so they use no neurons, and together they prove the token, its
    permission (Workers AI Read) and the account id before a run.
    """
    import providers
    table = providers.load_table("cloudflare")
    cf_state(models=[CF_MODEL, "@cf/openai/gpt-oss-20b"])
    STATE.cf_verify = {"id": "tok", "status": "active", "expires_on": "2026-10-31T00:00:00Z", "not_before": None}
    p = run_cf(cf_ks())
    want = ["token: active, account token (cfat_), expires 2026-10-31T00:00:00Z", "account: reachable",
            f"{CF_MODEL}: listed", "@cf/openai/gpt-oss-20b: listed", "@cf/qwen/qwen3.8-27b: not listed",
            "10,000 neurons a day", "00:00 UTC"]
    missing = [w for w in want if w not in p.stdout]
    check(p.returncode == 0 and not missing, f"exit {p.returncode}; missing {missing}; {p.stdout!r} {p.stderr[-300:]!r}")
    g = gets()
    verify = [r for r in g if r["path"].endswith("/tokens/verify")]
    search = [r for r in g if "/ai/models/search" in r["path"]]
    check(len(verify) == 1 and verify[0]["path"] == f"/client/v4/accounts/{ACCOUNT_ID}/tokens/verify"
          and len(search) == len(table["models"]) and all(r["path"].startswith(
              f"/client/v4/accounts/{ACCOUNT_ID}/ai/models/search?") for r in search)
          and all(r["headers"].get("Authorization") == f"Bearer {CF_TOKEN}" for r in g) and not chat_requests(),
          f"requests {[r['path'][:60] for r in STATE.requests]}")
    check(provider_clean(p), "the account id or the token was printed")
    STATE.reset()
    cf_state()
    u = run_cf(cf_ks(), key=CF_USER_TOKEN)
    uv = [r["path"] for r in gets() if r["path"].endswith("/tokens/verify")]
    check(u.returncode == 0 and uv == ["/client/v4/user/tokens/verify"] and "user token (cfut_)" in u.stdout
          and "expires never" in u.stdout and provider_clean(u), f"user token: exit {u.returncode}, {uv}")
    return f"account token verified at the account path, user token at the user path; {len(search)} searches"


def k04_cloudflare_key_status_failures_and_refusals():
    """A refused or expired token and a search the token may not run end with exit 5 and the fix; 429 exits 10, a
    5xx 3; no account id, the Global API Key and another host are refused before anything is sent (exit 2).
    """
    ok = {"status": 200, "body": {"success": True, "errors": [], "messages": [],
                                  "result": {"id": "t", "status": "active", "expires_on": None}}}
    cases = [
        ([cf_error(401, 10000, "Authentication error")], 5, "set-provider-key.ps1 -Provider cloudflare -Force"),
        ([dict(ok, body=dict(ok["body"], result={"id": "t", "status": "expired"}))], 5, "expired"),
        ([ok, cf_error(403, 10000, "Authentication error")], 5, "Workers AI"),
        ([ok, cf_error(404, 7003, f"Could not route to /accounts/{ACCOUNT_ID}")], 5, "account id"),
        ([cf_error(429, 971, "Please wait and consider throttling your request speed")], 10, "wait"),
        ([cf_error(502, 1000, "bad gateway")], 3, "try again"),
    ]
    bad = []
    for script, code, needle in cases:
        STATE.reset()
        cf_state()
        STATE.get_queue = list(script)
        p = run_cf(cf_ks())
        if p.returncode != code or needle not in p.stderr or not provider_clean(p):
            bad.append(f"{script[-1]['status']}: exit {p.returncode}, {p.stderr[-300:]!r}")
    STATE.reset()
    for kw, args, needle in (({"account": ""}, cf_ks(), "not set or empty"),
                             ({"key": "cfk_" + "a" * 40}, cf_ks(), "Global API Key"),
                             ({}, cf_ks("https://example.com/client/v4"), "sends its key only to")):
        p = run_cf(args, **kw)
        if not refused(p, needle):
            bad.append(f"refusal {needle!r}: exit {p.returncode}, {p.stderr[-200:]!r}")
    check(not bad, "; ".join(bad))
    check(not STATE.requests, f"the refusals sent {len(STATE.requests)} requests")
    return f"{len(cases)} failures with their exit codes and 3 refusals with none sent"


def k05_key_status_on_a_provider_run_line_reads_only():
    """--key-status on a full provider run line runs only the read: no chat, no ledger file, no lock, and one note
    names the skipped flags.
    """
    groq_state()
    STATE.groq_models = GROQ_LIST["data"]
    led = out("k05_ledger.jsonl")
    p = run_groq(groq_args("k05_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--key-status"])
    check(p.returncode == 0 and not chat_requests() and not os.path.exists(led) and "skipped:" in p.stderr
          and "--suite" in p.stderr and not os.path.exists(os.path.join(out("appdata"), "plotroom-dev",
                                                                         "groq-run.lock")),
          f"exit {p.returncode}, {len(chat_requests())} chats, {p.stderr[-300:]!r}")
    return "a Groq run line plus --key-status: one GET /models, no chat, no ledger, skipped flags named"


# ── unittest wiring ──────────────────────────────────────────────────────────

class ProviderKeyStatusTests(support.CaseTestCase):
    """--key-status for --provider groq and cloudflare (see the module docs)."""

    cases = (k01_groq_key_status_reports_models_and_limit_headers,
             k02_groq_key_status_failures_name_the_next_step,
             k03_cloudflare_key_status_verifies_the_token_and_searches_the_models,
             k04_cloudflare_key_status_failures_and_refusals,
             k05_key_status_on_a_provider_run_line_reads_only)

    def setUp(self):
        STATE.reset()


if __name__ == "__main__":
    unittest.main()
