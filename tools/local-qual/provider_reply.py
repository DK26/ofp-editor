#!/usr/bin/env python3
"""Reading what Groq and Cloudflare Workers AI send back (tools/local-qual).

What it owns
------------
The pure parsers the provider gates (provider_gate.py) and the key-status command use, each safe on untrusted input
(nothing here raises on a hostile header or body):

* ``go_duration`` and ``header_int``: Groq's ``x-ratelimit-*`` headers (Go-style durations such as "2m59.56s", and
  counts), with bounded lengths;
* ``output_tokens`` and ``neurons_for``: the tokens a reply used, and its neurons at a model's Cloudflare rates;
* ``cloudflare_codes``: the error codes of a Cloudflare body, in its v4 envelope or an OpenAI-style error object;
* ``groq_classify_429`` and ``cloudflare_classify_429``: which limit a 429 names (daily, minute, upstream) and how long
  to wait;
* ``_shown`` and ``iso_z``: an untrusted value and a time as printable text.

How it fits
-----------
Split out of provider_gate.py, which re-exports every name here, so that module stays readable in one pass. Standard
library only.

Sources (read 2026-09-28): https://console.groq.com/docs/rate-limits (the headers and their durations);
https://developers.cloudflare.com/workers-ai/platform/errors/ (3036, 3040); third-party quotes of Groq's 429 text
("... on tokens per day (TPD) ...").
"""
import datetime as _dt
import json
import math
import re

from cloud_reply import num
from rate_gate import daily_wait, seconds_to_midnight
# Cloudflare's error codes (errors page): the day's free allocation is used up, and capacity (or rejectIfBusy).
CF_DAILY = 3036
CF_CAPACITY = 3040
# Go-style durations as Groq's reset headers send them ("2m59.56s", "7.66s"); a bare number is read as seconds. At
# most 12 digits before and 9 after the point per part, so an absurd header can neither overflow nor be slow to read.
_UNITS = {"h": 3600.0, "m": 60.0, "s": 1.0, "ms": 1e-3, "us": 1e-6, "µs": 1e-6, "ns": 1e-9}
_PART = r"(\d{1,12}(?:\.\d{1,9})?)(h|ms|us|µs|ns|m|s)"
_DURATION = re.compile(f"(?:{_PART})+")
_DURATION_PART = re.compile(_PART)
_NUMBER = re.compile(r"\d{1,12}(?:\.\d{1,9})?")
_INT = re.compile(r"\d{1,12}")


# ── Parsers ──────────────────────────────────────────────────────────────────

def go_duration(value):
    """Seconds in a Go-style duration header ("2m59.56s", "500ms", "1h2m3s") or a bare number, else None."""
    if not isinstance(value, str):
        return None
    if _NUMBER.fullmatch(value):
        return float(value)
    if not _DURATION.fullmatch(value):
        return None
    total = sum(float(n) * _UNITS[u] for n, u in _DURATION_PART.findall(value))
    return total if math.isfinite(total) else None


def header_int(value):
    """A whole number from a header (at most 12 digits, surrounding spaces allowed), else None."""
    if not isinstance(value, str):
        return None
    v = value.strip()
    return int(v) if _INT.fullmatch(v) else None


def output_tokens(usage):
    """(prompt tokens, output tokens) of a usage object, or (None, None) when either is unreadable.

    Output is the largest of completion tokens, total minus prompt, and reasoning tokens: under OpenAI's convention
    the three agree, but a provider that reports reasoning beside the completion must not be under-counted.
    """
    u = usage if isinstance(usage, dict) else {}
    prompt, completion = num(u.get("prompt_tokens")), num(u.get("completion_tokens"))
    if prompt is None or completion is None:
        return None, None
    out = completion
    total = num(u.get("total_tokens"))
    if total is not None and total - prompt > out:
        out = total - prompt
    ctd = u.get("completion_tokens_details") if isinstance(u.get("completion_tokens_details"), dict) else {}
    reasoning = num(ctd.get("reasoning_tokens"))
    if reasoning is not None and reasoning > out:
        out = reasoning
    return prompt, out


def neurons_for(usage, rates):
    """Neurons of one reply: prompt tokens x rates["in"] + output tokens x rates["out"], per million; None when the
    usage is unreadable. Cached prompt tokens are priced as uncached (the conservative reading)."""
    prompt, out = output_tokens(usage)
    if prompt is None:
        return None
    return prompt * rates["in"] / 1e6 + out * rates["out"] / 1e6


def _shown(value):
    """An untrusted value as one JSON literal in printable ASCII, whole or by its length only (never cut, so a key
    inside it stays whole for the redaction)."""
    text = json.dumps(value, ensure_ascii=True)
    return text if len(text) <= 80 else f"a value of {len(text)} characters (not shown)"


def iso_z(epoch):
    """UTC ISO text of an epoch time, rounded up to the second ("2026-09-29T12:00:00Z"); never raises."""
    try:
        return _dt.datetime.fromtimestamp(math.ceil(epoch), _dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (OverflowError, OSError, ValueError):
        return "(an unreadable time)"


def _messages(data):
    """Every error message of a body, lower case: OpenAI's ``error`` object and Cloudflare's ``errors`` list."""
    out = []
    if isinstance(data, dict):
        err = data.get("error")
        if isinstance(err, dict):
            out.append(str(err.get("message") or ""))
        elif isinstance(err, str):
            out.append(err)
        errs = data.get("errors")
        for e in errs if isinstance(errs, list) else []:
            if isinstance(e, dict):
                out.append(str(e.get("message") or ""))
    return " ".join(out).lower()


def groq_classify_429(headers, data, now, retry_after=None):
    """(kind, wait) of a Groq 429: ``daily`` when the message names a per-day limit (RPD or TPD): terminal, the wait
    made sane by rate_gate.daily_wait; ``minute`` for RPM or TPM: wait retry-after, else the tokens' reset header;
    ``upstream`` otherwise (capacity), with retry-after."""
    text = _messages(data)
    if "(rpd)" in text or "(tpd)" in text or "per day" in text:
        return "daily", daily_wait(retry_after, now)
    if "(rpm)" in text or "(tpm)" in text or "per minute" in text:
        return "minute", retry_after if retry_after is not None else go_duration((headers or {}).get(
            "x-ratelimit-reset-tokens"))
    return "upstream", retry_after


def cloudflare_codes(data):
    """Every integer error code in a Cloudflare body: the v4 envelope's ``errors`` list, then an OpenAI-style
    ``error`` object (the shape of the /ai/v1 endpoint's errors is not documented, so both are read)."""
    codes = []
    if not isinstance(data, dict):
        return codes
    errs = data.get("errors")
    for e in errs if isinstance(errs, list) else []:
        code = e.get("code") if isinstance(e, dict) else None
        if isinstance(code, int) and not isinstance(code, bool):
            codes.append(code)
    err = data.get("error")
    code = err.get("code") if isinstance(err, dict) else None
    if isinstance(code, int) and not isinstance(code, bool):
        codes.append(code)
    elif isinstance(code, str) and _INT.fullmatch(code):
        codes.append(int(code))
    return codes


def cloudflare_classify_429(headers, data, now, retry_after=None):
    """(kind, wait) of a Cloudflare 429: ``daily`` for 3036 (the day's free allocation is used up; it resets at
    00:00 UTC, so the wait is the time to it), ``upstream`` for 3040 (capacity: back off), ``minute`` otherwise (the
    requests-a-minute limit), with retry-after."""
    codes = cloudflare_codes(data)
    text = _messages(data)
    if CF_DAILY in codes or "daily free allocation" in text:
        return "daily", seconds_to_midnight(now)
    if CF_CAPACITY in codes or "capacity" in text:
        return "upstream", retry_after
    return "minute", retry_after
