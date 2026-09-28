#!/usr/bin/env python3
"""``run.py --key-status``: read the API key's own record once, at no quota, and say what it allows (tools/local-qual).

What it owns
------------
* ``run``: the whole command. It refuses what cannot be sent safely (exit 2, nothing sent), builds the ``openai``
  client only for its guards and its redaction (cloud_backend.OpenAICompatBackend runs cloud_guard.py's checks: an
  https base URL, or plain http to this machine only; no credentials or query in it; a key that is printable, long
  enough to redact and never inside the URL), sends one ``GET <base>/key`` [K] and prints the report, then exits 0.
  It sends no chat or completion request, reads no catalogue, writes no ledger, record or other file and takes no
  lock, so it spends none of the day's free requests and runs even while a free run holds the free-run lock.
* ``report_lines``: the record's non-secret fields in plain words: credit limit and what is left, usage in all and
  today, BYOK usage, free tier yes/no, management key yes/no, expiry, today's free-model requests with the UTC reset
  (as the account's counter reports them, which can lag [52]), the per-key rate limit (-1 read as none [52]) with the
  reminder that the free-model limits count per account, and whether a ``--free-only`` run would accept the key. The
  fields come from free_key.key_summary and free_key.rate_limit_summary and the verdict from free_key.key_refusal, so
  the parsing and the refusal wording are free mode's own.
* ``interpret``: every way the read can end without a key record (401, 403, 404, 429, 5xx, a redirect, a body that
  is not a key record, no answer at all) as one line that names the next step, with an exit code.
* The display rules for untrusted text (``scrub``, ``shown_body``, ``printable``): the record's ``label`` (a partly
  masked copy of the key, or whatever the owner named the key) and the key are never shown, whether they come in the
  body (JSON bodies are decoded first, so \\u-escaped copies are found), in a record field or in a redirect's
  Location header.

How it fits
-----------
run.main calls ``run`` right after parsing the command line, before a suite, a preset or any flag check of a run, so
nothing else happens. cloud/run-cloud.ps1 accepts ``--key-status`` without ``--free-only`` for that reason: the
command cannot send a prompt or spend. The client's own ``key_read`` (cloud_guard.get_capped) returns the status and
body of a failed read instead of raising, which ``key_info`` (used by the free and paid runs) does. Standard library
only.

Exit codes: 0 the report was printed; 2 refused before sending; 3 the endpoint did not answer or failed (5xx): try
again later; 5 the key or the base URL is wrong (401, 403, 404, a redirect, a body that is not a key record); 10 rate
limited (429): wait and try again.

Source (read 2026-09-27)
------------------------
[K] https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key : ``GET /api/v1/key`` returns the record
of the key sent (``limit``, ``limit_remaining``, ``limit_reset``, ``usage``, ``usage_daily``, ``byok_usage``,
``is_free_tier``, ``is_management_key``, ``expires_at``, ``free_model_daily_requests`` {used, limit, remaining},
reset at UTC midnight, ``rate_limit``, and the ``label``).
[52] docs/research/52-rate-limits-and-ux.md, re-check of 2026-09-28 (observed, not documented by OpenRouter):
``rate_limit`` read -1 requests per 10 s, no per-key limit; ``free_model_daily_requests.used`` read 0 before and
after an answered free call, so it is not a real-time count.
"""
import datetime as _dt
import json
import math
import os
import re
import sys
import time
import urllib.parse

from cloud_backend import OpenAICompatBackend
from cloud_guard import MAX_BODY_BYTES, redirect_host
from cloud_run import EXIT_CONFIG, EXIT_QUOTA
from free_key import key_refusal, key_summary, rate_limit_summary
from rate_gate import DAILY_RESERVE_DEFAULT, FREE_RPM_LIMIT, classify_429, next_utc_midnight

# OpenRouter's API base, the default of --key-status for an OpenRouter key (the launcher's key store holds one).
DEFAULT_BASE = "https://openrouter.ai/api/v1"
# Every OpenRouter key starts with this (set-openrouter-key.ps1 checks the same prefix). A key without it is never
# sent to DEFAULT_BASE by default: another provider's key must not reach OpenRouter because --base-url was left out.
OPENROUTER_KEY_PREFIX = "sk-or-"
# The endpoint did not answer, or answered 5xx: try again later (run.py's code for a server that is not ready).
EXIT_UNREACHABLE = 3
# The flags --key-status reads. Any other flag set on the command line is named once as skipped, so a free-run or
# paid-run command line with --key-status added still works and says what it did not do. (--api-key and --dry-run
# are refused before this list is consulted.)
USED_FLAGS = frozenset(("key_status", "backend", "base_url", "api_key_env", "timeout", "max_key_headroom_usd",
                        "allow_key_headroom", "daily_reserve", "provider"))
# The most characters of a response body a failure line shows, after redaction (the rest is cut, marked "...").
MAX_SHOWN = 200
# A "label" pair in a body that is not valid JSON; its value is scrubbed before anything is shown.
_LABEL_PAIR = re.compile(r'("label"\s*:\s*")((?:[^"\\]|\\.)*)')
_REDACTED = "[REDACTED]"


# ── Untrusted text ───────────────────────────────────────────────────────────

def printable(text):
    """``text`` as one line of printable ASCII: every other character is written as its escape (\\x1b, \\u202e, ...).

    Why: a response body or an error message is untrusted. A control character can rewrite the console line (an
    escape sequence) or start a new one, bidi, zero-width and tag characters make shown text read differently from
    what it is, and any non-ASCII character can fail to encode on a redirected Windows console.
    """
    return "".join(c if " " <= c <= "~" else c.encode("unicode_escape").decode("ascii") for c in str(text))


def _labels(node):
    """Every non-empty string held under a "label" key anywhere in a parsed JSON body (iterative: the body is
    untrusted, and its nesting depth must not decide whether this walk finishes)."""
    found, stack = [], [node]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for key, value in cur.items():
                if key == "label" and isinstance(value, str) and value:
                    found.append(value)
                else:
                    stack.append(value)
        elif isinstance(cur, list):
            stack.extend(cur)
    return sorted(set(found), key=len, reverse=True)  # a longer label first, in case one contains another


def _parse(raw):
    """The JSON value of a body, or None (not JSON, or nested past Python's recursion limit)."""
    try:
        return json.loads(raw) if raw and raw.strip() else None
    except (ValueError, RecursionError):
        return None


def scrub(text, labels, redact):
    """``text`` with every label, every ``"label": "..."`` pair, the key and anything shaped like an OpenRouter key
    replaced, as one line of printable ASCII (not cut: a caller cuts after this, so no cut can split a secret).

    ``labels`` are the "label" values of the reply's JSON (``_labels``); each is replaced as written and as json.dumps
    writes it inside a string (a quote or a backslash escaped), since the text shown may be JSON this module wrote.
    ``redact`` is the client's own (the key verbatim, then anything shaped like ``sk-or-...``).
    """
    for label in labels:
        for form in (label, json.dumps(label, ensure_ascii=False)[1:-1]):
            text = text.replace(form, _REDACTED)
    return printable(redact(_LABEL_PAIR.sub(r"\1" + _REDACTED, text)).strip())


def shown_body(raw, data, redact):
    """The part of a failed reply worth showing, scrubbed and printable on one line ("" for an empty body).

    A JSON error object shows its message and, briefly, its metadata (which names an upstream provider); any other
    JSON body is shown decoded (re-written by json.dumps), and a body that is not JSON shows its start. Decoding comes
    first because a JSON encoder may write a label or an echoed key with \\u escapes (``cl\\u00e9-...``,
    ``\\u0073k-or-...``), which no scrub of the raw text can find. Then ``scrub``, and cutting last, so no piece of a
    secret survives a cut through it. A key or label deliberately encoded some other way (base64, split, reversed)
    cannot be recognised; only the endpoint that already received the key can send one.
    """
    err = data.get("error") if isinstance(data, dict) and isinstance(data.get("error"), dict) else None
    if err is not None:
        text = str(err.get("message") or "")
        meta = err.get("metadata")
        if isinstance(meta, dict) and meta:
            try:
                text += " | metadata: " + json.dumps(meta, ensure_ascii=False)
            except (ValueError, RecursionError):
                text += " | metadata: (nested too deep to show)"
    elif data is not None:
        try:
            text = json.dumps(data, ensure_ascii=False)
        except (ValueError, RecursionError):  # nested deeper than the encoder goes: show the raw start instead
            text = raw or ""
    else:
        text = raw or ""
    text = scrub(text, _labels(data), redact)
    return text if len(text) <= MAX_SHOWN else text[:MAX_SHOWN] + "..."


# ── The read and its failures ────────────────────────────────────────────────

def base_url_for(base_url, key):
    """The base URL to read: --base-url when given, else OpenRouter's API for an OpenRouter key; ValueError otherwise.

    Why the default: the launcher's key store holds an OpenRouter key, so ``run-cloud.ps1 --key-status`` needs nothing
    else. Why only for ``sk-or-`` keys: without --base-url, another provider's key would otherwise be sent to
    OpenRouter.
    """
    if base_url:
        return base_url
    if (key or "").strip().startswith(OPENROUTER_KEY_PREFIX):
        return DEFAULT_BASE
    raise ValueError(f"--key-status without --base-url reads OpenRouter's key record ({DEFAULT_BASE}) and sends it "
                     f"only an OpenRouter key; this key is not one, so pass its endpoint's --base-url")


def _failure(code, status, headers, data, exc, redact, now):
    """(exit code, one line naming the next step) for a read that brought no key record (see ``interpret``)."""
    if status is None:
        why = printable(redact(f"{type(exc).__name__}: {exc}"))[:MAX_SHOWN]
        return EXIT_UNREACHABLE, (f"GET /key could not reach the endpoint ({why}); check the network connection and "
                                  f"--base-url, then try again")
    if code == 200:
        if exc is not None:
            what = f"a body over {MAX_BODY_BYTES} bytes"
        elif data is None:
            what = "a body that is not JSON"
        else:
            what = "no key record (no data object)"
        return EXIT_CONFIG, (f"GET /key answered HTTP 200 with {what}; check --base-url: it must be the API base, "
                             f"such as {DEFAULT_BASE}, not a web page")
    if code == 401:
        return EXIT_CONFIG, ("HTTP 401: the endpoint does not accept this key (revoked, expired, deleted or mistyped); "
                             "create a new key, store it with cloud/set-openrouter-key.ps1 -Force, and run "
                             "--key-status again")
    if code == 403:
        return EXIT_CONFIG, ("HTTP 403: this key may not read its own record; check it in the dashboard (Settings > "
                             "API Keys), or create a new key and store it with cloud/set-openrouter-key.ps1 -Force")
    if code == 404:
        return EXIT_CONFIG, (f"HTTP 404: the endpoint has no /key; --key-status reads OpenRouter's key record, so pass "
                             f"--base-url {DEFAULT_BASE} (the API base, not the website)")
    if code == 429:
        kind, _ = classify_429(headers, data, now)
        if kind == "daily":
            return EXIT_QUOTA, (f"HTTP 429 naming a daily limit: wait until {next_utc_midnight(now)} (00:00 UTC), then "
                                f"run --key-status again")
        return EXIT_QUOTA, ("HTTP 429: too many requests just now; wait a minute, stop any other run on this account, "
                            "and run --key-status again (the kinds of 429: 'HTTP 429' in cloud/README.md)")
    if isinstance(code, int) and 300 <= code <= 399:
        # The Location header is the server's text like the body: its host may hold the key (it was just sent there)
        # or the label, so it is scrubbed as the body is. redirect_host never raises (a 300 keeps a malformed
        # Location such as "http://[x" intact, since urllib parses it only on the codes it would follow).
        target = scrub(redirect_host(headers), _labels(data), redact)[:MAX_SHOWN]
        return EXIT_CONFIG, (f"HTTP {code}: the endpoint redirects (to host {target!r}); redirects are never followed "
                             f"so the key is never forwarded; pass the final URL as --base-url")
    if isinstance(code, int) and 500 <= code <= 599:
        return EXIT_UNREACHABLE, f"HTTP {code}: the endpoint failed or is overloaded; try again in a few minutes"
    return EXIT_CONFIG, (f"HTTP {code}: the endpoint refused GET /key; check --base-url (for OpenRouter, "
                         f"{DEFAULT_BASE}) and the key")


def interpret(status, headers, raw, exc, redact, now):
    """(None, key record) when the reply holds one, else (exit code, one line for the console).

    ``status``, ``headers``, ``raw`` and ``exc`` are what OpenAICompatBackend.key_read returned; ``redact`` is the
    client's redaction. An error reported inside a 200 (a top-level ``error`` object with no record) is judged by its
    own code, as the chat path judges one.
    """
    data = _parse(raw)
    if status == 200 and exc is None and isinstance(data, dict) and isinstance(data.get("data"), dict):
        return None, data["data"]
    code = status
    if status == 200 and exc is None and isinstance(data, dict) and isinstance(data.get("error"), dict):
        inner = data["error"].get("code")
        code = inner if isinstance(inner, int) and not isinstance(inner, bool) else status
    exit_code, line = _failure(code, status, headers, data, exc, redact, now)
    body = shown_body(raw, data, redact) if status is not None else ""
    return exit_code, "key status: " + line + (f" (response: {body})" if body else "")


# ── The report ───────────────────────────────────────────────────────────────

def _usd(value):
    """A USD figure as written in the record (2.0 as 2), or "not reported"."""
    if value is None:
        return "not reported"
    if isinstance(value, float) and value.is_integer() and abs(value) < 1e15:
        return f"{int(value)} USD"
    return f"{value!r} USD"


def _yes_no(value):
    return "not reported" if value is None else ("yes" if value else "no")


def rate_limit_text(value):
    """The per-key ``rate_limit`` object in plain words: "none (requests -1)", "1000 requests per 1h", "not reported"."""
    rl = rate_limit_summary(value)
    req, interval = rl["requests"], rl["interval"]
    if req is None:
        return "not reported"
    if req < 0:
        return f"none (requests {req})"
    return f"{req} requests per {interval}" if interval else f"{req} requests (interval not reported)"


def report_lines(data, now, host, env_name, max_headroom=0.0, allow_headroom=False, reserve=DAILY_RESERVE_DEFAULT):
    """The report of one key record (the ``data`` object of GET /key) read at ``now`` (epoch seconds).

    A pure function of its arguments. The label is never read: the fields come from free_key's parsers, which keep
    numbers only when finite, flags only when booleans, and text only when it looks like a date or a period; a text
    field that nevertheless holds the label or an ``sk-or-`` string (a hostile server) is shown as not reported.
    ``max_headroom``, ``allow_headroom`` and ``reserve`` are the free-run flags the verdict uses.
    """
    k = key_summary(data)
    labels = _labels(data)
    rate_limit = data.get("rate_limit") if isinstance(data, dict) else None
    for field in ("limit_reset", "expires_at"):
        v = k.get(field)
        if v and (any(label in v for label in labels) or OPENROUTER_KEY_PREFIX in v):
            k[field] = None
    if isinstance(rate_limit, dict) and isinstance(rate_limit.get("interval"), str) and (
            OPENROUTER_KEY_PREFIX in rate_limit["interval"] or any(lb in rate_limit["interval"] for lb in labels)):
        rate_limit = dict(rate_limit, interval=None)
    fm = k.get("free_model_daily_requests") or {}
    counts = fm if fm and all(fm.get(x) is not None for x in ("used", "limit", "remaining")) else None
    credit = ("none (unlimited)" if k["limit"] is None else
              f"{_usd(k['limit'])}, left: {_usd(k['limit_remaining'])} (limit reset: {k['limit_reset'] or 'none'})")
    # The account's own counter, which is not a real-time count: doc 52's re-check of 2026-09-28 saw `used` read 0
    # before and after an answered free call. Shown as reported, with that caveat, never as an exact figure.
    free_today = (f"{counts['used']} used of {counts['limit']}, {counts['remaining']} left, as the account's counter "
                  f"reports it (it can lag behind recent calls); the counter resets at {next_utc_midnight(now)} "
                  f"(00:00 UTC)" if counts else "not reported")
    why = key_refusal(k, max_headroom, allow_headroom, _dt.datetime.fromtimestamp(now, _dt.timezone.utc))
    # The account's side of the day's allowance only: a free run also stops at its ledger's own daily cap
    # (--max-requests-per-day), which this read cannot see, hence "at most".
    verdict = (f"refused: {why}" if why else
               f"accepted; with {reserve} kept in reserve, a free run may send at most "
               f"{max(0, counts['remaining'] - reserve)} more today")
    # The per-key rate_limit is not the limit a free run meets: the free-model limits count per account, across every
    # key and machine (rate_gate.py's sources). Read alone, "none (requests -1)" would suggest no limit at all, so the
    # line says which limits apply, and repeats the record's own deprecation note (only the fact, never its text).
    note = rate_limit.get("note") if isinstance(rate_limit, dict) else None
    deprecated = ", a field the key record itself marks deprecated" if (
        isinstance(note, str) and "deprecated" in note.lower()) else ""
    rate_line = (f"{rate_limit_text(rate_limit)}{deprecated}; the free-model limits count per account (every key and "
                 f"machine): {FREE_RPM_LIMIT} a minute, and the day's allowance above")
    return [f"key status: the key in {printable(env_name)} at {printable(host)} (one GET /key: no model request, "
            f"none of the day's free requests used)",
            f"  credit limit: {credit}",
            f"  usage: {_usd(k['usage'])} in all, {_usd(k['usage_daily'])} today (UTC), BYOK {_usd(k['byok_usage'])}",
            f"  free tier: {_yes_no(k['is_free_tier'])}",
            f"  management key: {_yes_no(k['is_management_key'])}",
            f"  expires: {k['expires_at'] or 'not set or not reported'}",
            f"  free-model requests today: {free_today}",
            f"  per-key rate limit: {rate_line}",
            f"  free-only runs: {verdict}"]


# ── The command ──────────────────────────────────────────────────────────────

def ignored_flags(ap, args):
    """The flags this command line sets (to other than their defaults) that --key-status does not use, as --names."""
    defaults = vars(ap.parse_args([]))
    return ["--" + dest.replace("_", "-") for dest, value in vars(args).items()
            if dest not in USED_FLAGS and dest in defaults and value != defaults[dest]]


def run(ap, args):
    """``run.py --key-status``: refuse what cannot be sent safely (``ap.error``, exit 2, nothing sent), read GET
    <base>/key once, and print the report (exit 0) or one failure line on stderr (exit 3, 5 or 10)."""
    # ── Refusals: nothing has been sent yet ──
    if args.api_key is not None:
        ap.error("--key-status never takes a key on the command line; put it in an environment variable and pass its "
                 "name with --api-key-env (cloud/run-cloud.ps1 does both)")
    if args.dry_run:
        ap.error("--key-status sends one GET /key and --dry-run sends nothing; pass one of them")
    if not args.api_key_env:
        ap.error("--key-status needs --api-key-env, the name of the variable that holds the key (cloud/run-cloud.ps1 "
                 "adds it)")
    h = args.max_key_headroom_usd if args.max_key_headroom_usd is not None else 0.0
    if not (isinstance(h, (int, float)) and math.isfinite(h) and h >= 0) or args.daily_reserve < 0:
        ap.error("--max-key-headroom-usd must be a finite number >= 0 and --daily-reserve >= 0")
    # Read once, then removed from this process's environment, as a run does (cloud_run.make_backend).
    key = os.environ.pop(args.api_key_env, None) or ""
    if not key.strip():
        ap.error(f"the environment variable {args.api_key_env} is not set or empty")
    try:
        backend = OpenAICompatBackend(base_url_for(args.base_url, key), args.timeout, key)
    except ValueError as e:
        ap.error(str(e))  # cloud_guard's messages never hold the key
    skipped = ignored_flags(ap, args)
    if skipped:
        print(f"note: --key-status only reads the key record; skipped: {', '.join(skipped)}", file=sys.stderr,
              flush=True)

    # ── One GET /key ──
    status, headers, raw, exc = backend.key_read()
    now = time.time()
    code, result = interpret(status, headers, raw, exc, backend.redact, now)
    if code is not None:
        print(result, file=sys.stderr, flush=True)
        return code
    host = urllib.parse.urlsplit(backend.base).hostname or ""
    for line in report_lines(result, now, host, args.api_key_env, h, args.allow_key_headroom, args.daily_reserve):
        print(backend.redact(line))  # belt and braces: no line can hold the key or an sk-or- string
    return 0
