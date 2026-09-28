#!/usr/bin/env python3
"""Reading an OpenAI-compatible reply, and scrubbing secrets from text (tools/local-qual).

What it owns
------------
The pure helpers the ``openai`` backend (cloud_backend.py) uses on every attempt: the accounting numbers of a
``usage`` object (``usage_fields``), a body parsed without raising (``json_or_none``), the error hidden in a 200
(``embedded_error``) and an error's text and code (``code_and_message``, ``error_text``), which statuses are retried
(``retryable``, ``is_redirect``), thinking text in ``<think>`` tags (``think_blocks``), ``Retry-After``
(``retry_after_seconds``); and ``scrub_key_shapes``, which removes anything shaped like any provider's key.

How it fits
-----------
Split out of cloud_backend.py (which re-exports ``usage_fields`` for budget.py and keeps the other names as its own
private aliases), so that module stays readable in one pass. The Groq and Cloudflare client (provider_backend.py)
and the key-status commands use the same helpers. Every input here is untrusted server text: nothing raises on it.
Standard library only.
"""
import datetime
import json
import math
import re
from email.utils import parsedate_to_datetime

# Anything shaped like an OpenRouter key ("sk-or-v1-<hex>"), redacted wherever it appears: a provider may echo another
# key, and GET /key's "label" is a partly masked key. The key in use is also redacted verbatim (whatever its shape).
OPENROUTER_KEY = re.compile(r"sk-or-[A-Za-z0-9_.-]{4,}")
# The other providers' key shapes, redacted on every path the same way: Groq keys start with gsk_ (the prefix secret
# scanners use; Groq's documentation does not state it), Cloudflare account and user tokens with cfat_ and cfut_,
# and Cloudflare's Global API Key with cfk_ (https://developers.cloudflare.com/fundamentals/api/get-started/
# token-formats/, read 2026-09-28). Eight characters after the prefix keep ordinary words out.
PROVIDER_KEY = re.compile(r"(?:gsk|cfat|cfut|cfk)_[A-Za-z0-9_-]{8,}")
PROVIDER_PREFIXES = ("gsk_", "cfat_", "cfut_", "cfk_")
REDACTED = "[REDACTED]"


def scrub_key_shapes(text):
    """`text` with every OpenRouter, Groq and Cloudflare key shape replaced by [REDACTED] (non-strings unchanged)."""
    if not isinstance(text, str):
        return text
    if "sk-or-" in text:
        text = OPENROUTER_KEY.sub(REDACTED, text)
    if any(p in text for p in PROVIDER_PREFIXES):
        text = PROVIDER_KEY.sub(REDACTED, text)
    return text


def num(value):
    """A finite, non-negative number from untrusted JSON, or None (bools, strings, NaN and negatives are rejected)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if math.isfinite(value) and value >= 0 else None


def usage_fields(usage):
    """Pick the accounting numbers out of an OpenAI-style ``usage`` object (untrusted: every field is checked).

    OpenRouter returns usage on every response, counted with the model's own tokenizer: ``cost`` (in credits,
    which are US dollars), prompt and completion tokens, ``prompt_tokens_details.cached_tokens`` and
    ``cache_write_tokens``, and ``completion_tokens_details.reasoning_tokens``, which are billed as output
    (https://openrouter.ai/docs/use-cases/usage-accounting and /docs/use-cases/reasoning-tokens, read
    2026-09-27). ``cost_details.upstream_inference_cost`` is the provider's own bill, and ``is_byok`` says whether the
    request ran on the user's own provider key (BYOK). Only then is the upstream cost money spent on top of ``cost``;
    on every other request OpenRouter reports the same amount in both fields (doc 54 §4.2: all 3,494 answered calls
    of the first screening round had ``is_byok`` false and ``upstream_inference_cost`` equal to ``cost``).
    ``is_byok`` counts only as the JSON value true: a string or a number from an untrusted body is not a BYOK flag.
    """
    u = usage if isinstance(usage, dict) else {}
    ptd = u.get("prompt_tokens_details") if isinstance(u.get("prompt_tokens_details"), dict) else {}
    ctd = u.get("completion_tokens_details") if isinstance(u.get("completion_tokens_details"), dict) else {}
    cd = u.get("cost_details") if isinstance(u.get("cost_details"), dict) else {}
    completion, reasoning = num(u.get("completion_tokens")), num(ctd.get("reasoning_tokens"))
    return {
        "prompt_tokens": num(u.get("prompt_tokens")), "completion_tokens": completion,
        "reasoning_tokens": reasoning,
        "visible_tokens": (completion - reasoning) if completion is not None and reasoning is not None else completion,
        "cached_tokens": num(ptd.get("cached_tokens")), "cache_write_tokens": num(ptd.get("cache_write_tokens")),
        "cost": num(u.get("cost")), "upstream_cost": num(cd.get("upstream_inference_cost")),
        "is_byok": u.get("is_byok") is True,
    }


def json_or_none(raw):
    """The JSON value of a body, or None (empty, not JSON, or nested past the reader's depth)."""
    try:
        return json.loads(raw) if raw and raw.strip() else None
    except (ValueError, RecursionError):  # RecursionError: nested deeper than the reader goes, a few KB suffice (t76)
        return None


def code_and_message(err):
    """(integer code or None, message cut to 600 characters) of an error object (or anything else, as text)."""
    if isinstance(err, dict):
        code = err.get("code")
        try:
            code = int(code) if code is not None and not isinstance(code, bool) else None
        except (TypeError, ValueError, OverflowError):  # OverflowError: json reads 1e999 and Infinity as inf (t76)
            code = None
        text = str(err.get("message") or "")
        meta = err.get("metadata")
        if isinstance(meta, dict) and meta:
            # OpenRouter puts the upstream provider's name and raw error here, which is what explains a
            # schema rejection; keep it short.
            text += " | metadata: " + json.dumps(meta, ensure_ascii=False)[:300]
        return code, text[:600]
    return None, str(err)[:600]


def embedded_error(data):
    """(code, message) when a 200 body is really an error, else None.

    A non-streaming response can report a provider failure with HTTP 200 (a top-level ``error``, or a choice
    with ``finish_reason: "error"``); it must never be scored as content.
    """
    if data.get("error"):
        return code_and_message(data["error"])
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        return None, "the response has no choices"
    first = choices[0]
    if first.get("error"):
        return code_and_message(first["error"])
    if first.get("finish_reason") == "error":
        return None, "finish_reason is error"
    return None


def error_text(data, raw):
    """The message of an error body's ``error`` object, else the start of the raw body."""
    if isinstance(data, dict) and data.get("error"):
        return code_and_message(data["error"])[1]
    return (raw or "").strip()[:600]


def retryable(status):
    """Timeout, rate limit and the 5xx family (a CDN in front of a provider also sends 52x codes)."""
    return status in (408, 429) or (isinstance(status, int) and 500 <= status <= 599)


def is_redirect(status):
    return isinstance(status, int) and 300 <= status <= 399


def think_blocks(content):
    """The reasoning text a model put inside ``<think>`` tags in its content (an unclosed leading block counts)."""
    blocks = re.findall(r"<think>(.*?)</think>", content, re.S)
    rest = re.sub(r"<think>.*?</think>", "", content, flags=re.S)
    if rest.lstrip().startswith("<think>"):
        blocks.append(rest.lstrip()[len("<think>"):])
    return blocks


def retry_after_seconds(headers):
    """Seconds from a Retry-After header (delta-seconds or an HTTP date), or None."""
    value = (headers or {}).get("retry-after")
    if value is None:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        when = parsedate_to_datetime(value)
        return max(0.0, (when - datetime.datetime.now(when.tzinfo)).total_seconds())
    except (TypeError, ValueError, IndexError, OverflowError):
        return None
