#!/usr/bin/env python3
"""The structured cause of an OpenRouter 429 (``error.metadata.limit_source``) in rate_gate.classify_429.

r01-r08 pin one rule. A 429 whose metadata says ``limit_source: "upstream_provider_shared_pool"`` comes from the
provider's shared free pool, whatever its free text or headers say. It gets the upstream backoff and is never taken
for the account's daily cap, which stops a run until 00:00 UTC. Bodies without the field keep every classification
they had. Any other string value keeps those rules too, but the label a record carries shows it. A value of any
other JSON type is ignored. The evidence is doc 52's verification note of 2026-09-28 (re-check of the free shared
pools). The observed body is copied here synthetically: same keys and value types, no call id.

r01-r06 call rate_gate directly. r07 and r08 drive cloud_backend's ``chat`` against ``_Scripted``, a server in this
file on 127.0.0.1 with an ephemeral port. Nothing is spent, no real endpoint is contacted and no real key is used.

Run the whole suite from the repository root with ``python -m unittest discover -s tools/local-qual/tests``;
the module docs of support.py explain the case functions and the environment switches.
"""

import json
import random
import secrets
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import support  # first: it puts the tool folder on sys.path for the two imports after it
from support import check

import cloud_backend
import rate_gate as rg

# A fixed "now" for the unit cases: 2026-09-21 14:13:20 UTC, so the next 00:00 UTC is S2M seconds away.
N = 1_790_000_000.0
S2M = 35_200.0
FREE = "qwen/qwen3.8-27b:free"
SHARED = "upstream_provider_shared_pool"
# The prose of the observed body (doc 52, 2026-09-28), kept word for word: the old text rules read it.
RAW = ("qwen/qwen3.8-27b:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to "
       "accumulate your rate limits: https://openrouter.ai/settings/integrations")
HINT = ("Retry shortly, add your own provider key (https://openrouter.ai/settings/integrations), or route to another "
        "provider with provider routing: https://openrouter.ai/docs/features/provider-routing")
# A raw text that names a per-day quota: the provider's own, which the old rules read as the account's daily cap.
PER_DAY_RAW = "ModelRun: 1000 requests per day used for this shared pool; retry shortly"


# ── Fixtures ─────────────────────────────────────────────────────────────────

def observed_body(message="Provider returned error", **meta_over):
    """A synthetic copy of the shared-pool 429 body doc 52 recorded on 2026-09-28 (same keys and value types).

    ``meta_over`` replaces metadata fields (``raw=...``) so a case can change one thing and keep the rest real.
    """
    meta = {"raw": RAW, "provider_name": "ModelRun", "is_byok": False, "provider_error_code": "429",
            "limit_source": SHARED, "remedy_hint": HINT}
    meta.update(meta_over)
    return {"error": {"message": message, "code": 429, "metadata": meta}}


def body(message, meta=None):
    """A minimal OpenRouter error body with code 429, `message` and `meta` as ``error.metadata``."""
    return {"error": {"code": 429, "message": message, "metadata": dict(meta or {})}}


def with_source(data, value):
    """A copy of `data` whose ``error.metadata.limit_source`` is `value` (any JSON value)."""
    out = json.loads(json.dumps(data))
    out["error"]["metadata"]["limit_source"] = value
    return out


def without_source(data):
    """A copy of `data` with no ``error.metadata.limit_source``: what the old rules alone make of the body."""
    out = json.loads(json.dumps(data))
    out["error"]["metadata"].pop("limit_source", None)
    return out


def ms(seconds_ahead, now=N):
    """An X-RateLimit-Reset value `seconds_ahead` after `now`, in epoch milliseconds as OpenRouter sends it."""
    return str((now + seconds_ahead) * 1000)


def minute_headers():
    """OpenRouter's per-minute 429 headers (lower-case, as the backend passes them) with the reset 20 s after N."""
    return {"x-ratelimit-reset": ms(20), "x-ratelimit-limit": "20"}


# ── Classification ───────────────────────────────────────────────────────────

def r01_observed_shared_pool_body_is_upstream():
    """The shared-pool 429 body observed on 2026-09-28 is an upstream 429, and its label names the limit_source.

    Why: every key got this body while ModelRun's free pool was full (doc 52). A run must back off and retry it,
    never stop until midnight as if the account's daily cap were used up.

    How: as observed, the body comes with no retry-after or x-ratelimit-* header; a Retry-After the caller passes is
    returned as the wait. provider_name already made this body upstream before limit_source was read; the
    label is new.
    """
    got = [rg.classify_429({}, observed_body(), N), rg.classify_429({}, observed_body(), N, retry_after=4.0),
           rg.classify_429(None, observed_body(), N)]
    check(got == [("upstream", None), ("upstream", 4.0), ("upstream", None)], str(got))
    check(rg.limit_source(observed_body()) == SHARED, f"limit_source {rg.limit_source(observed_body())!r}")
    label = rg.rate_limit_label("upstream", observed_body())
    check(label.startswith("upstream rate limit") and f'"{SHARED}"' in label and "not documented" not in label, label)
    return f"observed body -> {got[0]}, with Retry-After 4 -> {got[1]}; label {label!r}"


def r02_shared_pool_wins_over_per_day_text_and_a_far_reset():
    """limit_source "upstream_provider_shared_pool" is upstream even when the text says "per day" or an
    X-RateLimit-Reset hours away comes with it; either alone reads as the daily cap under the old rules.

    Why: free text belongs to the provider and can describe its own daily quota. Read as the account's daily cap,
    it would stop the run until 00:00 UTC although a retry in seconds may succeed (doc 52's consequence). The
    structured field is OpenRouter's own statement of the cause, so it decides.

    How: each body is checked twice, with the field (upstream) and without it (daily, the old rules), so the case
    also proves every variant really looks like the daily cap to the text and header checks.
    """
    far = {"x-ratelimit-reset": ms(3 * 3600), "x-ratelimit-limit": "50", "x-ratelimit-remaining": "0"}
    cases = [
        ("raw says requests per day", {}, observed_body(raw=PER_DAY_RAW)),
        ("raw per day and a reset 3 h away", far, observed_body(raw=PER_DAY_RAW)),
        ("message free-models-per-day and a reset 3 h away", far,
         observed_body(message="Rate limit exceeded: free-models-per-day")),
        ("a reset 3 h away alone", far, observed_body()),
        ("the field alone beside per-day text", {}, body("Rate limit exceeded: free-models-per-day",
                                                         {"limit_source": SHARED})),
    ]
    bad = []
    for name, headers, data in cases:
        got = (rg.classify_429(headers, data, N), rg.classify_429(headers, data, N, retry_after=6.0))
        old = rg.classify_429(headers, without_source(data), N)[0]
        if got != (("upstream", None), ("upstream", 6.0)) or old != "daily":
            bad.append(f"{name}: {got}, without the field {old}")
    check(not bad, "; ".join(bad))
    return f"{len(cases)} daily-looking shared-pool bodies -> upstream (Retry-After kept); without the field: daily"


def r03_bodies_without_limit_source_keep_their_classification():
    """Every branch of the old rules gives the same kind and wait as before for a body without limit_source.

    Why: the structured check runs first but must change nothing for the bodies the tool already met: the daily cap
    stays terminal, the per-minute window still waits for its reset, and the rest still backs off.

    How: known values computed by hand from the rules (N is 14:13:20 UTC, 35,200 s before midnight). A reset exactly
    DAILY_RESET_MIN_S (300 s) away is still the per-minute window; one second more is the daily cap.
    """
    check(rg.seconds_to_midnight(N) == S2M, f"seconds to midnight {rg.seconds_to_midnight(N)}")
    table = [
        ("free-models-per-day", {}, body("Rate limit exceeded: free-models-per-day"), None, ("daily", S2M)),
        ("per day", {}, body("100 requests per day"), None, ("daily", S2M)),
        ("PerDay", {}, body("PerDay quota"), None, ("daily", S2M)),
        ("reset 1 h away", {"x-ratelimit-reset": ms(3600)}, body("Rate limit exceeded"), None, ("daily", 3600.0)),
        ("reset 300 s away", {"x-ratelimit-reset": ms(300)}, body("Rate limit exceeded"), None, ("minute", 300.0)),
        ("reset 301 s away", {"x-ratelimit-reset": ms(301)}, body("Rate limit exceeded"), None, ("daily", 301.0)),
        ("per-minute headers", minute_headers(), body("Rate limit exceeded: free-models-per-min"), None,
         ("minute", 20.0)),
        ("limit header only", {"x-ratelimit-limit": "20"}, body("Rate limit exceeded"), 3.0, ("minute", 3.0)),
        ("provider_name", {}, body("busy", {"provider_name": "X"}), 4.0, ("upstream", 4.0)),
        ("provider_code", {}, body("busy", {"provider_code": "x"}), None, ("upstream", None)),
        ("upstream text", {}, body("temporarily rate-limited upstream"), None, ("upstream", None)),
        ("bare", {}, body("Rate limit exceeded"), None, ("upstream", None)),
        ("provider and a far reset", {"x-ratelimit-reset": ms(7200)}, body("busy", {"provider_name": "X"}), None,
         ("daily", 7200.0)),
        ("provider raw per day", {}, body("busy", {"provider_name": "X", "raw": "50 requests per day"}), None,
         ("daily", S2M)),
        ("observed body without the field", {}, without_source(observed_body()), None, ("upstream", None)),
        ("no body", {}, None, 2.0, ("upstream", 2.0)),
        ("text body", {}, "Too Many Requests", None, ("upstream", None)),
        ("error as text", {}, {"error": "free-models-per-min"}, None, ("upstream", None)),
        ("headers None", None, body("Rate limit exceeded"), None, ("upstream", None)),
    ]
    bad = []
    for name, headers, data, retry_after, want in table:
        got = rg.classify_429(headers, data, N, retry_after=retry_after)
        label = rg.rate_limit_label(got[0], data)
        if got != want or label != f"{want[0]} rate limit":
            bad.append(f"{name}: {got} {label!r}, want {want}")
    check(not bad, "; ".join(bad))
    return f"{len(table)} bodies without limit_source keep their kind and wait; labels unchanged ('<kind> rate limit')"


def r04_unknown_limit_source_keeps_the_old_rules_and_is_shown():
    """Any other string limit_source (unknown causes, near misses in case or spacing, "") is classified by the old
    rules, and the label shows the value, marked as not documented.

    Why: the parser rules are permissive on unknown values. An undocumented cause is not guessed at, so the old rules
    decide, but the value goes into the record so a new cause is visible instead of silently folded into a kind.
    Only the exact documented value counts, so a near miss cannot switch off the daily stop.
    """
    far = {"x-ratelimit-reset": ms(3600)}
    table = [
        ("account_daily_cap", {}, body("Rate limit exceeded: free-models-per-day"), ("daily", S2M)),
        # An undocumented value that sounds upstream, beside a provider_name, on the daily-cap message: still daily.
        ("upstream_provider_daily_cap", {}, body("Rate limit exceeded: free-models-per-day",
                                                 {"provider_name": "ModelRun"}), ("daily", S2M)),
        ("provider_minute", minute_headers(), body("Rate limit exceeded: free-models-per-min"), ("minute", 20.0)),
        ("new_cause", {}, body("Rate limit exceeded"), ("upstream", None)),
        ("UPSTREAM_PROVIDER_SHARED_POOL", {}, body("busy", {"raw": PER_DAY_RAW}), ("daily", S2M)),
        (" " + SHARED, {}, body("busy", {"raw": PER_DAY_RAW}), ("daily", S2M)),
        (SHARED + " ", far, body("busy"), ("daily", 3600.0)),
        ("", {}, body("Rate limit exceeded: free-models-per-day"), ("daily", S2M)),
    ]
    bad, labels = [], []
    for value, headers, base, want in table:
        data = with_source(base, value)
        got = rg.classify_429(headers, data, N)
        label = rg.rate_limit_label(got[0], data)
        labels.append(label)
        if got != want or rg.limit_source(data) != value or not label.startswith(f"{want[0]} rate limit") \
                or json.dumps(value) not in label or "not documented" not in label:
            bad.append(f"{value!r}: {got} {label!r}, want {want}")
    check(not bad, "; ".join(bad))
    return f"{len(table)} undocumented values keep the old kinds; e.g. {labels[0]!r}"


def r05_non_string_limit_source_is_ignored():
    """A limit_source that is not a string (null, a number, a bool, a list or object, even one holding the documented
    value) is ignored: same kind and wait as the body without it, and no mention in the label.

    Why: only a JSON string is the documented shape. Unwrapping a list or reading a number would guess at a format
    no one has observed; worse, a list holding the documented value could switch off the daily stop.

    How: the old text rule reads the metadata's JSON, where a list or object holding the documented string contains
    the word "upstream"; those two values are left out of the per-minute base, where that text alone decides.
    """
    values = [None, 0, 1, -1.5, True, False, [], {}, [SHARED], {"value": SHARED}]
    bases = [("daily text", {}, body("Rate limit exceeded: free-models-per-day"), ("daily", S2M)),
             ("provider raw per day", {}, body("busy", {"provider_name": "ModelRun", "raw": PER_DAY_RAW}),
              ("daily", S2M)),
             ("far reset", {"x-ratelimit-reset": ms(3600)}, body("Rate limit exceeded"), ("daily", 3600.0)),
             ("minute", minute_headers(), body("Rate limit exceeded: free-models-per-min"), ("minute", 20.0)),
             ("provider", {}, body("busy", {"provider_name": "X"}), ("upstream", None)),
             ("bare", {}, body("Rate limit exceeded"), ("upstream", None))]
    bad, n = [], 0
    for value in values:
        for name, headers, base, want in bases:
            if name == "minute" and SHARED in json.dumps(value):
                continue
            data = with_source(base, value)
            got = rg.classify_429(headers, data, N)
            label = rg.rate_limit_label(got[0], data)
            n += 1
            if got != want or rg.limit_source(data) is not None or label != f"{want[0]} rate limit":
                bad.append(f"{value!r} on {name}: {got} {label!r}, want {want}")
    # The field is read only at error.metadata.limit_source; elsewhere, or under a metadata that is not an object,
    # it is not the structured cause.
    misplaced = [{"limit_source": SHARED, "error": {"message": "free-models-per-day"}},
                 {"error": {"limit_source": SHARED, "message": "free-models-per-day"}},
                 {"error": {"metadata": [SHARED], "message": "free-models-per-day"}},
                 {"error": {"metadata": SHARED, "message": "free-models-per-day"}}]
    for data in misplaced:
        n += 1
        if rg.limit_source(data) is not None or rg.classify_429({}, data, N) != ("daily", S2M):
            bad.append(f"misplaced {json.dumps(data)}: {rg.classify_429({}, data, N)}")
    check(not bad, "; ".join(bad))
    check(all(rg.limit_source(x) is None for x in (None, [], "text", 7, {"error": "x"})), "non-object bodies")
    return f"{n} bodies with a non-string or misplaced limit_source keep the old kinds and plain labels"


# ── Display safety ───────────────────────────────────────────────────────────

def r06_limit_source_in_the_label_is_escaped_bounded_and_never_cut():
    """The label shows limit_source in printable ASCII (control, DEL, bidi, zero-width and tag characters escaped),
    whole up to LIMIT_SOURCE_SHOWN_MAX characters and otherwise only by its length.

    Why: the value is untrusted server text that ends up in records and on the console. Escaping keeps a crafted
    value from reordering or hiding the text around it. Never cutting a value keeps any key inside it whole, so the
    backend's redaction (the key verbatim, anything shaped like an OpenRouter key) still finds it.

    How: the labels go through a real OpenAICompatBackend's ``redact`` built with a dummy key; nothing is sent. The
    hostile characters are written as escapes, never raw, so this source reads as it runs (test_source_text.py
    checks every source file for raw ones).
    """
    hostile = "a\u202eb\u200bc\U000e0041d\x00e\x7ff\ng\"h\\i"
    label = rg.rate_limit_label("upstream", with_source(body("x"), hostile))
    want = ("\\u202e", "\\u200b", "\\udb40\\udc41", "\\u0000", "\\u007f", "\\n", '\\"', "\\\\")
    check(all(" " <= ch <= "~" for ch in label) and all(w in label for w in want), f"escaped: {label!r}")
    cap = rg.LIMIT_SOURCE_SHOWN_MAX
    at_cap = rg.rate_limit_label("daily", with_source(body("x"), "x" * cap))
    over = rg.rate_limit_label("daily", with_source(body("x"), "x" * (cap + 1)))
    check(json.dumps("x" * cap) in at_cap and "x" * 8 not in over and f"{cap + 1} characters" in over,
          f"boundary: {at_cap!r} / {over!r}")
    # The longest label: LIMIT_SOURCE_SHOWN_MAX characters outside the Basic Multilingual Plane, each escaped as a
    # surrogate pair (12 characters), under the longest kind name. rate_gate documents the bound (1,100 characters).
    worst = rg.rate_limit_label("upstream", with_source(body("x"), chr(0xE0041) * cap))
    check(len(worst) < 1100 and all(" " <= ch <= "~" for ch in worst), f"worst case: {len(worst)} characters")
    huge = with_source(body("Rate limit exceeded: free-models-per-day"), "y" * 1_000_000)
    kind = rg.classify_429({}, huge, N)
    big = rg.rate_limit_label(kind[0], huge)
    check(kind == ("daily", S2M) and len(big) < 200 and "1000000 characters" in big, f"1 MB value: {kind} {big!r}")
    # ── Keys inside the value stay whole, so redaction removes them ──
    key = "sk-test-" + secrets.token_hex(16)
    backend = cloud_backend.OpenAICompatBackend("http://127.0.0.1:9/api/v1", 5.0, key)
    other = "sk-or-v1-" + "d" * 64
    shown = [backend.redact(rg.rate_limit_label("upstream", with_source(body("x"), v)))
             for v in ("quota:" + key, other)]
    hidden = rg.rate_limit_label("upstream", with_source(body("x"), "x" * 20 + other))
    check(all("[REDACTED]" in s and key not in s and "d" * 16 not in s for s in shown), f"redacted: {shown}")
    check("sk-or" not in hidden and "d" * 8 not in hidden, f"over the cap: {hidden!r}")
    return (f"hostile value escaped to printable ASCII ({label!r}); {cap} characters shown, {cap + 1} by length; a "
            f"1 MB value classified and labelled in {len(big)} characters; keys inside a shown value redacted whole")


# ── Through the backend ──────────────────────────────────────────────────────

class _Scripted:
    """A loopback HTTP server for one case: each POST gets the next scripted (status, headers, body); the last one
    repeats. ``seen`` counts the POSTs that reached it.

    http.server runs a handler class per request; ThreadingHTTPServer gives each request its own thread and
    ``serve_forever`` runs in a daemon thread here, so ``chat`` can call it from the test's thread. Port 0 lets the
    system pick a free port. Used as a context manager: the server is shut down and its socket closed on exit.
    """

    def __init__(self, script):
        self.script, self.seen, self._lock = list(script), 0, threading.Lock()
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length") or 0))
                with outer._lock:
                    status, headers, payload = outer.script[min(outer.seen, len(outer.script) - 1)]
                    outer.seen += 1
                raw = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                for name, value in headers.items():
                    self.send_header(name, value)
                self.end_headers()
                self.wfile.write(raw)

            def log_message(self, *args):  # keep the test output clean
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/api/v1"
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


# An answered free call: zero cost, the requested :free model, served by the pinned provider (passes paid_signal).
COMPLETION = {"id": "gen-mock", "model": FREE, "provider": "ModelRun",
              "choices": [{"message": {"content": '{"choice": "A"}'}, "finish_reason": "stop"}],
              "usage": {"prompt_tokens": 12, "completion_tokens": 4, "cost": 0}}
CHAT_BODY = {"model": FREE, "messages": [{"role": "user", "content": "Pick A or B."}], "stream": False,
             "max_tokens": 16}


def _chat(script):
    """One ``chat`` call as a free run makes it (a rate gate stopping at 3 429s in a row, the zero-spend target)
    against a scripted server; returns (result, POSTs the server saw, back-off sleeps). The sleeps are recorded,
    not slept."""
    slept = []
    with _Scripted(script) as srv:
        backend = cloud_backend.OpenAICompatBackend(srv.url, 10.0, None, sleep=slept.append, rng=random.Random(7))
        backend.gate = rg.RateGate(max_429=3)
        backend.free_target = {"model": FREE, "canonical_slug": None, "providers": ["modelrun/fp4"]}
        result = backend.chat(dict(CHAT_BODY))
        seen = srv.seen
    return result, seen, slept


def r07_chat_backs_off_on_a_shared_pool_429_instead_of_stopping_as_quota():
    """Through cloud_backend.chat, a shared-pool 429 (as observed, or with per-day text and a far reset, or inside an
    HTTP 200) is retried and the next answer is kept; three in a row stop as rate_limited, never as quota. An
    undocumented limit_source beside the daily-cap message still stops as quota. The recorded error names the
    limit_source (rate_limit_label); a body without it keeps the text it had.

    Why: "quota" ends a free run until 00:00 UTC (exit 10) after one request. For a full shared pool the right
    reaction is a short back-off, and several in a row a rate_limited stop. The daily cap must stay terminal.

    How: _Scripted plays the bodies; the gate and the zero-spend target are set as free_mode.start_free sets them.
    Before limit_source was read, the per-day variants stopped as quota after one request.
    """
    reset = str(int((time.time() + 3 * 3600) * 1000))  # chat classifies with the real clock
    far = {"X-RateLimit-Reset": reset, "X-RateLimit-Limit": "50", "X-RateLimit-Remaining": "0"}
    ok = (200, {}, COMPLETION)
    runs = {
        "observed x2 then 200": [(429, {}, observed_body())] * 2 + [ok],
        "per-day raw + far reset x2 then 200": [(429, far, observed_body(raw=PER_DAY_RAW))] * 2 + [ok],
        "inside a 200, then 200": [(200, {}, observed_body(raw=PER_DAY_RAW)), ok],
    }
    bad, got = [], {}
    for name, script in runs.items():
        r, seen, slept = _chat(script)
        want_history = [s for s, _, _ in script]
        got[name] = r["extra"]["http_status_history"]
        if r["fatal"] is not None or r["error"] is not None or got[name] != want_history or seen != len(script) \
                or len(slept) != len(script) - 1 or r["content"] != '{"choice": "A"}':
            bad.append(f"{name}: fatal {r['fatal']}, error {r['error']!r}, history {got[name]}, {seen} POSTs")
    r3, seen3, _ = _chat([(429, {}, observed_body())])
    shared_label = f'HTTP 429 ({rg.rate_limit_label("upstream", observed_body())}): '
    if r3["fatal"] != "rate_limited" or seen3 != 3 or not (r3["error"] or "").startswith(shared_label):
        bad.append(f"3 in a row: fatal {r3['fatal']}, {seen3} POSTs, error {r3['error']!r}")
    daily = with_source(body("Rate limit exceeded: free-models-per-day"), "account_daily_cap")
    r4, seen4, _ = _chat([(429, {}, daily), ok])
    if r4["fatal"] != "quota" or seen4 != 1 or \
            not (r4["error"] or "").startswith('HTTP 429 (daily rate limit, limit_source "account_daily_cap" is not'):
        bad.append(f"undocumented source + daily message: fatal {r4['fatal']}, {seen4} POSTs, error {r4['error']!r}")
    # A body without limit_source keeps the record text it had: "HTTP 429 (<kind> rate limit): ...".
    r5, _, _ = _chat([(429, {}, without_source(observed_body()))])
    if not (r5["error"] or "").startswith("HTTP 429 (upstream rate limit): Provider returned error"):
        bad.append(f"no limit_source: error {r5['error']!r}")
    check(not bad, "; ".join(bad))
    return (f"retried and answered: {got}; observed x3: rate_limited after {seen3} POSTs; undocumented source with "
            f"the daily-cap message: quota after {seen4} POST")


def r08_shared_pool_429s_inside_a_200_stop_within_the_call_attempt_limit():
    """A storm of shared-pool 429s reported inside HTTP 200 bodies (with per-day raw text) ends the call within the
    backend's max_attempts POSTs, without an answer and never as quota; the recorded error names the limit_source.

    Why: limit_source first means such a body is no longer the daily stop, so something else must bound the
    retries, and classify_429's docstring names it. The call's own attempt limit always does. Since a 429 inside a
    200 counts toward the gate's streak (r12, test_rate_limit_stops.py), the streak stops it first, as rate_limited
    after 3; the case accepts either bound, so it pins the limit_source record whichever stops the call.

    How: the scripted server answers every POST with the same 200 body; the backend keeps its default max_attempts,
    read from a backend built with the same defaults.
    """
    limit = cloud_backend.OpenAICompatBackend("http://127.0.0.1:9/api/v1", 5.0, None).max_attempts
    r, seen, slept = _chat([(200, {}, observed_body(raw=PER_DAY_RAW))])
    history = r["extra"]["http_status_history"]
    check(1 < seen <= limit and history == [200] * seen and r["fatal"] in (None, "rate_limited")
          and r["content"] == "" and "code 429" in (r["error"] or "") and len(slept) == seen - 1
          and 'limit_source "upstream_provider_shared_pool"' in (r["error"] or ""),
          f"fatal {r['fatal']}, {seen} POSTs (limit {limit}), history {history}, error {r['error']!r}")
    return f"{seen} POSTs (limit {limit}), fatal {r['fatal']}, no answer; error {r['error'][:60]!r}..."


# ── unittest wiring ──────────────────────────────────────────────────────────

class RateLimitSourceTests(support.CaseTestCase):
    """limit_source-first classification of OpenRouter 429s (see the module docs)."""

    cases = (r01_observed_shared_pool_body_is_upstream,
             r02_shared_pool_wins_over_per_day_text_and_a_far_reset,
             r03_bodies_without_limit_source_keep_their_classification,
             r04_unknown_limit_source_keeps_the_old_rules_and_is_shown,
             r05_non_string_limit_source_is_ignored,
             r06_limit_source_in_the_label_is_escaped_bounded_and_never_cut,
             r07_chat_backs_off_on_a_shared_pool_429_instead_of_stopping_as_quota,
             r08_shared_pool_429s_inside_a_200_stop_within_the_call_attempt_limit)


if __name__ == "__main__":
    unittest.main()
