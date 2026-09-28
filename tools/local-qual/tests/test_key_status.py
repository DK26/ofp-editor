#!/usr/bin/env python3
"""Tests for ``run.py --key-status`` (key_status.py): the key's own record, read at no quota (t67-t73).

Why the command exists: before it, the only zero-quota way to see what a key allows (credit limit, usage, today's
free-model requests) was a hand-written script, since ``--dry-run`` sends nothing, not even the key check, and a real
free run spends one of the day's scarce requests. OpenRouter's ``GET <base>/key`` returns the key record at no cost,
so ``--key-status`` sends exactly that one request and prints the record's non-secret fields in plain words.

* t67: the report, field by field, against a known key record; the reset time; the per-key rate limit with -1 read as
  none; the free-only verdict; the pure report builder is deterministic; one GET /key and nothing else is sent.
* t68: the key and the record's ``label`` (a partly masked key, or any text the owner typed) never reach the console,
  on success or in an error body, whether the label holds ``sk-or-`` or not.
* t69: every way the read can fail (401, 403, 404, 429, 5xx, a redirect, a body that is not a key record, no
  connection) ends with one line that names the next step and a documented exit code; bodies are shown redacted and
  on one printable line.
* t70: refusals before anything is sent (a non-loopback http base, a key on the command line, --dry-run, no key
  variable, a key the guards reject, a non-OpenRouter key without --base-url).
* t71: ``--key-status`` added to a full free-run or paid-run command line runs only the key read: no catalogue, no
  chat, no ledger, no output file, no lock (it works even while a free run holds the free-run lock) and a note names
  the flags it skipped.
* t72: no other part of a hostile reply shows a secret either: a redirect's Location host, a record's date or period
  field, a JSON-escaped copy (``\\u0073k-or-...``, a non-ASCII or a quoted label).
* t73: the lines name the limit that applies: the per-account free-model limits beside the per-key ``rate_limit``,
  the daily counter shown as possibly lagging, a daily against a per-minute 429, a body over the cap, a 300 whose
  Location cannot be parsed.

The launcher path (cloud/run-cloud.ps1 with a throwaway DPAPI blob, ``--key-status`` accepted without ``--free-only``,
``sk-or-`` and ``--api-key`` still refused) is step 15 of dpapi_round_trip.ps1, run by t53 in
test_free_mode_review.py.

Every case runs run.py as a child process (or key_status.py's pure functions in-process) against mock_server.py,
in-process on 127.0.0.1: nothing is spent and no real endpoint is contacted. cloud_support.py holds the dummy keys and
the final key sweep, which fails the module if a key or a key label reached a file or a console transcript.

Run the whole suite from the repository root with ``python -m unittest discover -s tools/local-qual/tests``.
"""
import json
import os
import secrets
import socket
import time
import unittest

import cloud_support
import support
from cloud_support import *  # noqa: F401,F403 - the shared fixtures the cases use by name

URL = None  # the mock's base URL while this module runs (set by setUpModule)


def setUpModule():
    global URL
    URL = cloud_support.start("key-status")


def tearDownModule():
    cloud_support.finish()


# ── Helpers ──────────────────────────────────────────────────────────────────

def ks_args(url=None):
    """The shortest key-status command line against the mock (the launcher adds --api-key-env the same way)."""
    return ["--key-status", "--base-url", url or URL, "--api-key-env", ENV_NAME]


def key_gets():
    """The GET /key requests the mock received."""
    return [r for r in STATE.requests if r["path"].endswith("/key")]


def other_requests():
    """Every request that is not a GET /key: chat completions, catalogue reads, anything else."""
    return [r for r in STATE.requests if not r["path"].endswith("/key")]


def err_lines(p):
    """The non-empty lines a run printed on stderr."""
    return [ln for ln in p.stderr.splitlines() if ln.strip()]


# ── Basic functionality ──────────────────────────────────────────────────────

def t67_key_status_reports_the_key_record_in_plain_words():
    """--key-status sends one GET /key and prints the record's non-secret fields in plain words, then exits 0.

    Why: the owner needs to see, at no quota, whether the key can spend (credit limit and what is left), what it has
    spent (in all, today, BYOK), whether it is a free-tier or a management key, how many of today's free-model
    requests are left and when the counter resets (00:00 UTC), and whether a free-only run would accept it. Any other
    request (a chat, a catalogue read) would spend quota or time the command promises not to spend.

    How: a known record (3 of 50 free requests used, usage 0.25 / 0.0125 / 0 USD, a 0 USD limit, rate limit
    requests -1) is checked line by line; a second record flips every yes/no, drops the credit limit and the daily
    counter and carries a positive rate limit; key_status.report_lines is called twice on one record to show it is a
    pure function of (record, time).
    """
    import rate_gate
    free_state(usage=0.25, usage_daily=0.0125, byok_usage=0, rate_limit={"requests": -1, "interval": "10s"})
    STATE.free_used_offset = 3
    before = time.time()
    p = run_free(ks_args())
    after = time.time()
    resets = {rate_gate.next_utc_midnight(before), rate_gate.next_utc_midnight(after)}
    want = ["credit limit: 0 USD, left: 0 USD (limit reset: none)",
            "usage: 0.25 USD in all, 0.0125 USD today (UTC), BYOK 0 USD", "free tier: yes", "management key: no",
            "expires: 2099-12-31T23:59:59Z", "free-model requests today: 3 used of 50, 47 left",
            "per-key rate limit: none (requests -1)",
            "free-only runs: accepted; with 5 kept in reserve, a free run may send at most 42 more today"]
    missing = [w for w in want if w not in p.stdout]
    check(p.returncode == 0 and not missing, f"exit {p.returncode}; missing {missing}; stdout {p.stdout!r} "
                                             f"stderr {p.stderr[-300:]!r}")
    check(any(f"the counter resets at {r} (00:00 UTC)" in p.stdout for r in resets), f"reset not in {p.stdout!r}")
    gets = key_gets()
    check(len(gets) == 1 and not other_requests() and gets[0]["headers"].get("Authorization") == f"Bearer {FREE_KEY}",
          f"{len(gets)} key reads, other requests {[r['path'] for r in other_requests()]}")
    check(no_secrets(p) and not err_lines(p), f"secrets shown or stderr not empty: {p.stderr[-300:]!r}")

    # ── The other value of every field ──
    STATE.reset()
    free_state(limit=None, limit_remaining=None, is_free_tier=False, is_management_key=True,
               rate_limit={"requests": 1000, "interval": "1h"}, expires_at=None)
    STATE.free_daily_limit = None  # no free_model_daily_requests in the record
    q = run_free(ks_args())
    want2 = ["credit limit: none (unlimited)", "free tier: no", "management key: yes",
             "expires: not set or not reported", "free-model requests today: not reported",
             "per-key rate limit: 1000 requests per 1h", "free-only runs: refused: the key record does not say "
                                                         "is_management_key false"]
    missing2 = [w for w in want2 if w not in q.stdout]
    check(q.returncode == 0 and not missing2 and no_secrets(q), f"exit {q.returncode}; missing {missing2}; "
                                                                f"{q.stdout!r}")

    # ── The pure report builder: deterministic, and untrusted shapes read as "not reported" ──
    import key_status
    rec = free_key(usage="0.1", byok_usage=True, rate_limit={"requests": True, "interval": "1h‮"},
                   free_model_daily_requests={"used": -1, "limit": 50, "remaining": 49})
    now = time.time()
    a = key_status.report_lines(rec, now, host="openrouter.ai", env_name=ENV_NAME)
    b = key_status.report_lines(rec, now, host="openrouter.ai", env_name=ENV_NAME)
    text = "\n".join(a)
    check(a == b, "report_lines gave two different reports for one record and one time")
    check("usage: not reported in all" in text and "BYOK not reported" in text and
          "per-key rate limit: not reported" in text and "free-model requests today: not reported" in text and
          LABEL not in text and "‮" not in text, f"untrusted shapes: {text!r}")
    odd = key_status.rate_limit_text({"requests": 5, "interval": "1h\x1b[2J"})
    check(odd == "5 requests (interval not reported)", f"unsafe interval shown: {odd!r}")
    return (f"8 fields in plain words (reset at {sorted(resets)[0]}); 1 GET /key, 0 other requests; the other value "
            f"of each field; report_lines deterministic; malformed fields read as not reported")


# ── Security edge cases ──────────────────────────────────────────────────────

def t68_key_status_never_shows_the_key_or_the_label():
    """Neither the key nor the key record's label reaches stdout or stderr, on success or inside an error body.

    Why: the label is a partly masked copy of the key (or whatever the owner named the key), and an error body is
    untrusted text that may echo the Authorization header or the key record; the console is where a key is most
    easily copied into a chat or a screenshot.

    How: labels with and without ``sk-or-`` on a successful read; then a 500 that echoes the bearer header, a 500
    whose JSON error message quotes a plain label that its own ``data.label`` names, a 200 portal page quoting the
    masked label, and a 401 whose non-JSON body carries a ``"label": "..."`` pair. Every plain label is added to the
    module's final sweep too.
    """
    plain = "owner-named-" + secrets.token_hex(6)
    plain2 = "second-label-" + secrets.token_hex(6)
    SWEEP.extend([plain, plain2])
    shown = []
    for label in (LABEL, plain):
        STATE.reset()
        free_state(label=label)
        p = run_free(ks_args())
        check(p.returncode == 0 and label not in p.stdout + p.stderr and no_secrets(p),
              f"success with label {'sk-or-' if label == LABEL else 'plain'}: exit {p.returncode}")
    bodies = [(500, "ECHO_AUTH", "you sent Bearer [REDACTED]"),
              (500, {"error": {"code": 500, "message": f"lookup failed for {plain}"}, "data": {"label": plain}},
               "lookup failed for [REDACTED]"),
              (200, f"<html>portal for {LABEL}</html>", "portal for [REDACTED]"),
              (401, '{"label": "' + plain2 + '", broken', '"label": "[REDACTED]"')]
    bad = []
    for status, body, needle in bodies:
        STATE.reset()
        free_state()
        STATE.key_queue = [{"status": status, "body": body}]
        p = run_free(ks_args())
        text = p.stdout + p.stderr
        shown.append(needle)
        if (p.returncode == 0 or needle not in p.stderr or any(s in text for s in (FREE_KEY, LABEL, plain, plain2))
                or not no_secrets(p)):
            bad.append(f"HTTP {status}: exit {p.returncode}, stderr {p.stderr[-300:]!r}")
    check(not bad, "; ".join(bad))
    return (f"labels with and without sk-or- never shown on success; 4 error bodies shown only redacted: "
            f"{'; '.join(shown)}")


# ── Error paths ──────────────────────────────────────────────────────────────

def t69_key_status_failures_name_the_next_step():
    """Every failure of the read is one line on stderr that names the next step, with a documented exit code.

    Why: an owner who hit HTTP 429 elsewhere asked whether the setup still works; a bare traceback or "HTTP Error
    401: Unauthorized" does not say whether to wait, fix the base URL or replace the key.

    How: scripted GET /key responses. 401 and 403 (exit 5: store a new key), 404 and a body that is not a key record
    (exit 5: check --base-url), 429 (exit 10: wait), 500 and 503 (exit 3: try again later), a 302 (exit 5, never
    followed) and a closed port (exit 3). Each prints nothing on stdout and exactly one stderr line; a body with an
    escape sequence and a bidi override is shown escaped, still on one line. No chat request is ever sent.
    """
    steal = root_url() + "/steal"
    cases = [
        (401, {"error": {"code": 401, "message": "User not found."}}, None, 5, "set-openrouter-key.ps1 -Force",
         "User not found."),
        (403, {"error": {"code": 403, "message": "Forbidden"}}, None, 5, "Settings > API Keys", "Forbidden"),
        (404, {"error": {"code": 404, "message": "not found"}}, None, 5, "--base-url https://openrouter.ai/api/v1",
         "HTTP 404"),
        (429, {"error": {"code": 429, "message": "Rate limit exceeded"}}, None, 10, "wait", "Rate limit exceeded"),
        (500, "Internal Server Error", None, 3, "try again", "Internal Server Error"),
        (503, {"error": {"code": 503, "message": "overloaded"}}, None, 3, "try again", "overloaded"),
        (200, "<html>sign in</html>", None, 5, "--base-url", "not JSON"),
        (200, {"ok": True}, None, 5, "--base-url", "no key record"),
        (401, {"error": {"code": 401, "message": "bad \x1b[31mred\x1b[0m ‮drow"}}, None, 5,
         "set-openrouter-key.ps1 -Force", "\\x1b[31mred"),
        (302, {"error": {"code": 302, "message": "moved"}}, {"Location": steal}, 5, "redirect", "HTTP 302"),
    ]
    bad = []
    for status, body, headers, code, step, seen in cases:
        STATE.reset()
        free_state()
        STATE.key_queue = [{"status": status, "body": body, "headers": headers}]
        p = run_free(ks_args())
        lines = err_lines(p)
        if (p.returncode != code or p.stdout.strip() or len(lines) != 1 or step not in lines[0]
                or seen not in lines[0] or "\x1b" in p.stderr or "‮" in p.stderr or not no_secrets(p)):
            bad.append(f"HTTP {status}: exit {p.returncode} (want {code}), stdout {p.stdout!r}, stderr {lines!r}")
        if other_requests():  # a chat, a catalogue read, or the redirect target (/steal) would all land here
            bad.append(f"HTTP {status}: other requests {[r['path'] for r in other_requests()]}")
    check(not bad, "; ".join(bad))
    # ── No server at all: a closed loopback port ──
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    q = run_free(ks_args(f"http://127.0.0.1:{port}/api/v1"))
    lines = err_lines(q)
    check(q.returncode == 3 and len(lines) == 1 and "could not reach" in lines[0] and "try again" in lines[0],
          f"closed port: exit {q.returncode}, {lines!r}")
    return f"{len(cases)} scripted failures and a closed port: one line each, the next step named, exit 3, 5 or 10"


# ── Boundary and refusal tests ───────────────────────────────────────────────

def t70_key_status_refusals_send_nothing():
    """Unsafe or contradictory key-status command lines are refused before any request (exit 2, 0 requests).

    Why: the key travels in a header, so the base-URL and key guards of the paid path (cloud_guard.py) apply
    unchanged; a key on the command line lands in shell history; --dry-run promises that nothing is sent; and a key
    of another provider must never go to OpenRouter just because --base-url was left out.

    How: plain http to a reserved non-loopback name (RFC 2606, so a mutant without the guard reaches no real server),
    credentials or a query in the URL, --api-key, --dry-run, no --api-key-env, an unset variable, a key with a space
    and the key inside the URL, each in a child process. The default base URL is checked in-process with
    ``key_status.DEFAULT_BASE`` pointed at the mock, so that a regression sends its request to the mock, never to
    openrouter.ai: a non-``sk-or-`` key without --base-url is refused with 0 requests, and an ``sk-or-`` key reads
    the (patched) default.
    """
    import contextlib
    import io
    import key_status
    import run as runmod
    cases = [
        ("non-loopback http", ks_args("http://api.example.invalid/api/v1"), {}, "plain http"),
        ("credentials in the URL", ks_args(URL.replace("http://", "http://u:p@")), {}, "credentials"),
        ("query in the URL", ks_args(URL + "?x=1"), {}, "query"),
        ("key on the command line", ks_args() + ["--api-key", "x-123456789"], {}, "command line"),
        ("dry run", ks_args() + ["--dry-run"], {}, "--dry-run"),
        ("no --api-key-env", ["--key-status", "--base-url", URL], {}, "--api-key-env"),
        ("variable not set", ks_args(), {ENV_NAME: ""}, "not set"),
        ("key with a space", ks_args(), {ENV_NAME: FREE_KEY[:12] + " " + FREE_KEY[12:]}, "spaces"),
        ("key in the URL", ks_args(URL + "/" + FREE_KEY), {}, "contains the API key"),
    ]
    bad = []
    for name, argv, env, needle in cases:
        q = run_free(argv, env_extra=dict({ENV_NAME: FREE_KEY}, **env))
        if not refused(q, needle) or not no_secrets(q) or KEY in q.stdout + q.stderr:
            bad.append(f"{name}: exit {q.returncode}, stderr {q.stderr.strip()[-200:]!r}")
    check(not bad, "; ".join(bad))
    check(not STATE.requests, f"{len(STATE.requests)} requests reached the server during the refusals")
    check(key_status.base_url_for(None, FREE_KEY) == "https://openrouter.ai/api/v1"
          and key_status.base_url_for(URL, KEY) == URL, "the default base URL")

    # ── No --base-url, in-process, with the default pointed at the mock ──
    def main_code(key):
        """run.main's exit code for --key-status without --base-url (an ap.error is SystemExit 2), and its output."""
        os.environ[ENV_NAME] = key
        sink = io.StringIO()
        try:
            with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
                try:
                    code = runmod.main(["--key-status", "--api-key-env", ENV_NAME])
                except SystemExit as e:
                    code = e.code
        finally:
            os.environ.pop(ENV_NAME, None)
        LOGS.append(sink.getvalue())
        return code, sink.getvalue()
    saved = key_status.DEFAULT_BASE
    key_status.DEFAULT_BASE = URL
    try:
        other_code, other_text = main_code(KEY)
        n_other = len(STATE.requests)
        or_code, or_text = main_code(FREE_KEY)
    finally:
        key_status.DEFAULT_BASE = saved
    gets = key_gets()
    check(other_code == 2 and "--base-url" in other_text and n_other == 0 and KEY not in other_text,
          f"another provider's key without --base-url: exit {other_code}, {n_other} requests, {other_text[-200:]!r}")
    check(or_code == 0 and "free tier:" in or_text and len(gets) == 1
          and gets[0]["headers"].get("Authorization") == f"Bearer {FREE_KEY}" and FREE_KEY not in or_text,
          f"an sk-or- key without --base-url: exit {or_code}, {len(gets)} key reads, {or_text[-200:]!r}")
    return (f"{len(cases)} refusals (exit 2) with 0 requests; without --base-url, another provider's key is refused "
            f"(0 requests) and an sk-or- key reads the default base")


def t71_key_status_on_a_run_command_line_skips_the_run():
    """--key-status added to a free-run or paid-run command line reads the key only: no catalogue, no chat, no
    ledger, no output file, no lock, and one note names the flags it skipped.

    Why: the quickest way to check the key is to add --key-status to the command the owner already uses; the command
    must then do nothing else (the launcher lets it through without --free-only because it cannot spend), and it must
    work while a free run holds the per-user free-run lock, since it uses none of the account's free requests.
    """
    free_state()
    os.makedirs(os.path.dirname(free_lock_path()), exist_ok=True)
    write_text(free_lock_path(), '{"pid": 1}')
    try:
        argv = free_args("ks_ledger.jsonl") + ["--suite", "pick", "--k", "1", "--limit", "2", "--out",
                                               out("ks_run.jsonl"), "--key-status"]
        p = run_free(argv)
        lock = read_text(free_lock_path())
    finally:
        os.remove(free_lock_path())
    note = [ln for ln in err_lines(p) if ln.startswith("note: --key-status")]
    made = [f for f in ("ks_run.jsonl", "ks_ledger.jsonl", "ks_ledger.jsonl.lock", "ks_run.jsonl.lock")
            if os.path.exists(out(f))]
    check(p.returncode == 0 and "free-model requests today" in p.stdout and len(note) == 1
          and all(f in note[0] for f in ("--free-only", "--model", "--suite", "--ledger", "--out"))
          and "--base-url" not in note[0] and "--api-key-env" not in note[0],
          f"free line: exit {p.returncode}, note {note!r}, stderr {p.stderr[-300:]!r}")
    check(not made and lock == '{"pid": 1}' and len(key_gets()) == 1 and not other_requests(),
          f"files made {made}; lock {lock!r}; {len(key_gets())} key reads; other {[r['path'] for r in other_requests()]}")
    # ── A paid line with --key-check and a non-OpenRouter key: --base-url is given, so the key goes only there ──
    STATE.reset()
    q = run_tool(base(URL) + ["--suite", "pick", "--max-usd", "1", "--key-check", "--key-status"])
    check(q.returncode == 0 and "credit limit: 2 USD, left: 1.5 USD" in q.stdout and not other_requests()
          and KEY not in q.stdout + q.stderr, f"paid line: exit {q.returncode}, {q.stdout!r} {q.stderr[-300:]!r}")
    return ("free-run line plus --key-status: exit 0, 1 GET /key, 0 other requests, no ledger, output file or lock "
            "made, a held free-run lock untouched, one note naming the skipped flags; a paid line likewise")


# ── Security edge cases: hostile replies (review) ────────────────────────────

def t72_key_status_hostile_replies_show_no_secret():
    """No part of a hostile reply carries the key or a label to the console: not a redirect's Location, not a text
    field of the key record, not a JSON-escaped copy.

    Why: every piece of a reply is untrusted, not only its body. A redirect's target host is printed to say where the
    endpoint points, a record's date and period fields are printed in the report, and a JSON encoder may write a
    label (or a deliberately echoed key) with \\u escapes, which a scrub of the raw text cannot find.

    How: a 302 whose Location host is the key, the masked label or the plain label its own body names; a record that
    puts the plain and the masked label into ``limit_reset``, ``expires_at`` and ``rate_limit.interval`` (all shaped
    like dates or periods, so the parsers keep them), and one that puts another provider's 40-character key into
    ``limit_reset``; a 401 without an ``error`` object whose raw JSON writes a
    non-ASCII label with \\u escapes in a second field; a 200 that echoes the key as ``\\u0073k-or-...``; and a 500
    whose error metadata quotes a label holding double quotes (shown as JSON, so as ``\\"``). Secrets are matched by
    their random hex part, which no escaping changes, and failures name them, never print them.
    """
    plain = "owner-named-" + secrets.token_hex(6)
    accent = "clé-" + secrets.token_hex(6)
    quoted = 'my "free" key ' + secrets.token_hex(6)
    SWEEP.extend([plain, accent, quoted])
    tails = {"key": FREE_KEY[len("sk-or-"):], "masked label": LABEL[len("sk-or-"):], "plain label": plain,
             "non-ASCII label": accent[len("clé-"):], "quoted label": quoted[len('my "free" key '):]}

    def leaked(p):
        """The names (never the values) of the secrets a run printed."""
        return [name for name, tail in tails.items() if tail in p.stdout + p.stderr]
    bad = []
    # ── A redirect's target host ──
    # sftp: urllib refuses to follow any scheme but http, https and ftp before it connects, so even a regression that
    # followed redirects would send nothing (not even a name lookup); t69's loopback redirect covers following.
    for host, body in ((FREE_KEY, {"error": {"code": 302, "message": "moved"}}),
                       (LABEL, {"error": {"code": 302, "message": "moved"}}),
                       (plain, {"data": {"label": plain}})):
        STATE.reset()
        free_state()
        STATE.key_queue = [{"status": 302, "body": body, "headers": {"Location": f"sftp://{host}.example.invalid/x"}}]
        p = run_free(ks_args())
        if p.returncode != 5 or leaked(p) or "redirect" not in p.stderr:
            bad.append(f"302 to a host holding a secret: exit {p.returncode}, shown {leaked(p)}")
    # ── Text fields of the record ──
    for label in (plain, LABEL):
        STATE.reset()
        free_state(label=label, limit_reset=label, expires_at=label, rate_limit={"requests": 5, "interval": label})
        p = run_free(ks_args())
        if (p.returncode != 0 or leaked(p) or "limit reset: none" not in p.stdout
                or "expires: not set or not reported" not in p.stdout or "interval not reported" not in p.stdout):
            bad.append(f"label in the record's text fields: exit {p.returncode}, shown {leaked(p)}, "
                       f"{p.stdout.replace(label, '<label>')!r}")
    # Another provider's key has no sk-or- prefix, and at 40 characters of [a-z0-9-] it passes the date-shaped filter:
    # only the verbatim scrub of every printed line keeps it off the console.
    STATE.reset()
    free_state(limit_reset=KEY)
    p = run_tool(ks_args())
    if p.returncode != 0 or KEY in p.stdout + p.stderr or "limit reset: [REDACTED]" not in p.stdout:
        bad.append(f"another provider's key in limit_reset: exit {p.returncode}, shown {KEY in p.stdout + p.stderr}")
    # ── JSON-escaped copies ──
    escaped = [(401, json.dumps({"detail": "no such key: " + accent, "data": {"label": accent}})),
               (200, '{"echo": "\\u0073' + FREE_KEY[1:] + '"}'),
               # The shown metadata is JSON this module writes, where the label's quotes come out as \"
               (500, json.dumps({"error": {"code": 500, "message": "failed", "metadata": {"key_name": quoted}},
                                 "data": {"label": quoted}}))]
    for status, raw in escaped:
        STATE.reset()
        free_state()
        STATE.key_queue = [{"status": status, "body": raw}]
        p = run_free(ks_args())
        if p.returncode != (3 if status == 500 else 5) or leaked(p) or len(err_lines(p)) != 1:
            bad.append(f"HTTP {status} with an escaped secret: exit {p.returncode}, shown {leaked(p)}, "
                       f"{len(err_lines(p))} stderr lines")
    check(not bad, "; ".join(bad))
    return ("3 redirect targets, 2 records with the label in 3 text fields, another provider's key in a record field, "
            "3 JSON-escaped copies: no secret shown")


def t73_key_status_names_the_limit_that_applies():
    """The report and the failure lines name the limit that actually applies: a daily 429 gives the reset time, a
    per-minute 429 says wait a minute, a body over the cap is named as such, and the per-key ``rate_limit`` line says
    that the free-model limits are per account (and that the record marks the field deprecated, when it does).

    Why: the command exists for an owner who hit HTTP 429 elsewhere. A per-key line reading "none" with nothing else
    suggests that no limit applies, while the free-model limits are counted per account, across every key and machine;
    the account's daily counter was seen to read 0 before and after an answered free call (doc 52's re-check of
    2026-09-28), so it must not read as an exact count; and "wait a minute" for a daily cap, or "not JSON" for an
    oversized body, names the wrong next step.

    How: the mock's documented key record (its ``rate_limit`` carries OpenRouter's deprecation note) and one without
    the note; scripted 429s with the daily and the per-minute wording; a 200 of MAX_BODY_BYTES + 1 bytes; a 300 whose
    Location cannot be parsed (a traceback instead of the one line would hide the next step).
    """
    import cloud_guard
    bad = []
    STATE.reset()
    free_state()  # rate_limit {"requests": 1000, "interval": "1h", "note": "This field is deprecated ..."}
    p = run_free(ks_args())
    line = next((ln for ln in p.stdout.splitlines() if "per-key rate limit:" in ln), "")
    if p.returncode != 0 or "deprecated" not in line or "per account" not in line or "20 a minute" not in line:
        bad.append(f"rate-limit line with the deprecation note: exit {p.returncode}, {line!r}")
    # The account's daily counter was seen to lag (doc 52, 2026-09-28 re-check): the line must not read as exact.
    free_line = next((ln for ln in p.stdout.splitlines() if "free-model requests today:" in ln), "")
    if "can lag" not in free_line:
        bad.append(f"free-model line presents the account counter as exact: {free_line!r}")
    STATE.reset()
    free_state(rate_limit={"requests": -1, "interval": "10s"})
    p = run_free(ks_args())
    line = next((ln for ln in p.stdout.splitlines() if "per-key rate limit:" in ln), "")
    if p.returncode != 0 or "deprecated" in line or "per account" not in line or "none (requests -1)" not in line:
        bad.append(f"rate-limit line without the note: exit {p.returncode}, {line!r}")
    cases = [(429, {"error": {"code": 429, "message": "Rate limit exceeded: free-models-per-day"}}, None, 10,
              "00:00 UTC"),
             (429, {"error": {"code": 429, "message": "Rate limit exceeded: free-models-per-min"}}, None, 10,
              "wait a minute"),
             (200, "x" * (cloud_guard.MAX_BODY_BYTES + 1), None, 5, f"over {cloud_guard.MAX_BODY_BYTES} bytes"),
             # A 300 is a redirect urllib does not parse; its malformed Location must not crash the report.
             (300, {"error": {"code": 300, "message": "choices"}}, {"Location": "http://[bad/x"}, 5, "redirects")]
    for status, body, headers, code, needle in cases:
        STATE.reset()
        free_state()
        STATE.key_queue = [{"status": status, "body": body, "headers": headers}]
        p = run_free(ks_args())
        lines = err_lines(p)
        if p.returncode != code or len(lines) != 1 or needle not in lines[0]:
            bad.append(f"HTTP {status} ({needle}): exit {p.returncode}, {[ln[:200] for ln in lines]!r}")
    check(not bad, "; ".join(bad))
    return ("rate-limit line names the per-account limits (and the deprecation when the record says so); daily and "
            "per-minute 429, an oversized body and an unreadable redirect each name their own next step")


# ── unittest wiring ──────────────────────────────────────────────────────────

class KeyStatusTests(support.CaseTestCase):
    """run.py --key-status (see the module docs)."""

    cases = (t67_key_status_reports_the_key_record_in_plain_words,
             t68_key_status_never_shows_the_key_or_the_label,
             t69_key_status_failures_name_the_next_step,
             t70_key_status_refusals_send_nothing,
             t71_key_status_on_a_run_command_line_skips_the_run,
             t72_key_status_hostile_replies_show_no_secret,
             t73_key_status_names_the_limit_that_applies)

    def setUp(self):
        STATE.reset()


if __name__ == "__main__":
    unittest.main()
