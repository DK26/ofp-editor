#!/usr/bin/env python3
"""OpenAI-compatible client for the local-qual runner: cloud endpoints under a hard budget (tools/local-qual).

What it owns
------------
``OpenAICompatBackend``: any OpenAI-compatible ``POST <base>/chat/completions``
endpoint, local or cloud, for example OpenRouter (``https://openrouter.ai/api/v1``)
or a provider's own API; plus its helpers (usage parsing, provider matching,
error classification). The checks on the base URL, the key and
``--extra-body``, and the redirect-refusing opener, are in cloud_guard.py.
The key comes from an environment variable, is never written anywhere and
never follows a redirect;
every attempt is paid for out of a hard budget (budget.py) that refuses to send
a call it cannot afford; the schema goes in strict ``response_format`` and a
rejection stops the run instead of falling back to unconstrained output.

How it fits
-----------
It has the same interface as the local clients in backends.py (``probe``,
``payload``, ``chat``) and returns the same backend-neutral result, so score.py
reads its records unchanged; ``chat`` also takes the run's ``Budget`` and a call
id. cloud_run.py builds it from the command line. It lives in its own module so
that backends.py (the local runtimes doc 44 measured) stays as it was.

Standard library only.
"""
import http.client
import json
import math
import random
import re
import time
import urllib.error
import urllib.request

# Request hygiene lives in cloud_guard.py; check_base_url, normalise_schema, provider_matches, DROPPABLE_PARAMS and
# FORBIDDEN_EXTRA are re-exported here for callers that import them from this module. The free-only rules
# (--free-only: zero spend on OpenRouter's :free models) live in free_mode.py, the client-side rate caps in
# rate_gate.py.
from cloud_guard import (DROPPABLE_PARAMS, FORBIDDEN_EXTRA, STRIPPABLE_KEYWORDS, check_base_url,  # noqa: F401
                         check_extra_body, check_key, get_capped, normalise_schema, opener, provider_matches,
                         read_capped, redirect_host)
from free_mode import NO_ROUTE_HINT, key_summary, no_route, paid_signal
from rate_gate import classify_429

# ── OpenAI-compatible endpoints (cloud or local) ─────────────────────────────
#
# Status codes and billing rules follow https://openrouter.ai/docs/api-reference/errors (read 2026-09-27):
# 408, 429, 502, 503 and 504 are transient; 429 and 503 carry Retry-After; a non-streaming 200 can carry a
# provider error in its body; 402 means the account or the key is out of credits; and providers may bill
# prompt processing on a failed request even when no content came back.

# Rejections that happen before any model runs, so no tokens can have been billed (a refused 3xx redirect is
# unbilled too). Every other failure after the request left the machine (a 5xx, a timeout, a dropped connection,
# a provider error inside a 200 without usage) is charged its whole reservation: over-counting costs a little
# headroom, under-counting could break the cap.
UNBILLED_STATUS = frozenset((400, 401, 402, 403, 404, 413, 422, 429))
# Words that mark a 4xx as a structured-output rejection (the endpoint cannot honour the strict schema).
_SCHEMA_WORDS = ("response_format", "json_schema", "json schema", "structured output", "structured_output",
                 "structured-output", "schema")
# Marker for an attempt that failed while the request was being built or sent locally (see _post).
_LOCAL_FAILURE = "local-failure"
# Anything shaped like an OpenRouter key ("sk-or-v1-<hex>"), redacted wherever it appears: a provider may echo another
# key, and GET /key's "label" is a partly masked key. The key in use is also redacted verbatim (whatever its shape).
_OPENROUTER_KEY = re.compile(r"sk-or-[A-Za-z0-9_.-]{4,}")


def _num(value):
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
    completion, reasoning = _num(u.get("completion_tokens")), _num(ctd.get("reasoning_tokens"))
    return {
        "prompt_tokens": _num(u.get("prompt_tokens")), "completion_tokens": completion,
        "reasoning_tokens": reasoning,
        "visible_tokens": (completion - reasoning) if completion is not None and reasoning is not None else completion,
        "cached_tokens": _num(ptd.get("cached_tokens")), "cache_write_tokens": _num(ptd.get("cache_write_tokens")),
        "cost": _num(u.get("cost")), "upstream_cost": _num(cd.get("upstream_inference_cost")),
        "is_byok": u.get("is_byok") is True,
    }


def _json_or_none(raw):
    try:
        return json.loads(raw) if raw and raw.strip() else None
    except ValueError:
        return None


def _code_and_message(err):
    if isinstance(err, dict):
        code = err.get("code")
        try:
            code = int(code) if code is not None and not isinstance(code, bool) else None
        except (TypeError, ValueError):
            code = None
        text = str(err.get("message") or "")
        meta = err.get("metadata")
        if isinstance(meta, dict) and meta:
            # OpenRouter puts the upstream provider's name and raw error here, which is what explains a
            # schema rejection; keep it short.
            text += " | metadata: " + json.dumps(meta, ensure_ascii=False)[:300]
        return code, text[:600]
    return None, str(err)[:600]


def _embedded_error(data):
    """(code, message) when a 200 body is really an error, else None.

    A non-streaming response can report a provider failure with HTTP 200 (a top-level ``error``, or a choice
    with ``finish_reason: "error"``); it must never be scored as content.
    """
    if data.get("error"):
        return _code_and_message(data["error"])
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        return None, "the response has no choices"
    first = choices[0]
    if first.get("error"):
        return _code_and_message(first["error"])
    if first.get("finish_reason") == "error":
        return None, "finish_reason is error"
    return None


def _error_text(data, raw):
    if isinstance(data, dict) and data.get("error"):
        return _code_and_message(data["error"])[1]
    return (raw or "").strip()[:600]


def _retryable(status):
    """Timeout, rate limit and the 5xx family (a CDN in front of a provider also sends 52x codes)."""
    return status in (408, 429) or (isinstance(status, int) and 500 <= status <= 599)


def _is_redirect(status):
    return isinstance(status, int) and 300 <= status <= 399


def _think_blocks(content):
    """The reasoning text a model put inside ``<think>`` tags in its content (an unclosed leading block counts)."""
    blocks = re.findall(r"<think>(.*?)</think>", content, re.S)
    rest = re.sub(r"<think>.*?</think>", "", content, flags=re.S)
    if rest.lstrip().startswith("<think>"):
        blocks.append(rest.lstrip()[len("<think>"):])
    return blocks


def _retry_after_seconds(headers):
    """Seconds from a Retry-After header (delta-seconds or an HTTP date), or None."""
    value = (headers or {}).get("retry-after")
    if value is None:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        from email.utils import parsedate_to_datetime
        import datetime
        when = parsedate_to_datetime(value)
        return max(0.0, (when - datetime.datetime.now(when.tzinfo)).total_seconds())
    except (TypeError, ValueError, IndexError, OverflowError):
        return None


class OpenAICompatBackend:
    """Any OpenAI-compatible ``POST <base>/chat/completions`` (stream=false): OpenRouter, a provider's own API,
    or a local vLLM or llama-server.

    What makes it different from the local backends:

    * **Key.** Passed in by run.py from the environment variable named by ``--api-key-env``; it is sent only
      in the Authorization header, never across a redirect, and removed from every string this class returns
      (``redact``).
    * **Budget.** ``chat`` asks the budget (budget.py) to reserve the worst-case cost of each attempt before
      sending it and refuses when the cap would be exceeded; afterwards it charges the provider-reported cost,
      the cost computed from usage and the price flags, or the whole reservation when neither is known.
    * **Schema.** Strict ``response_format`` json_schema. A 4xx that names the schema stops the run
      (``fatal: schema_rejected``); nothing is ever retried without the schema.
    * **Retries.** 408, 429 and 5xx get up to ``max_attempts`` attempts with exponential backoff and full jitter,
      honouring Retry-After; 402 stops the run as out of budget; other 4xx stop it as a configuration fault.
    * **Records.** usage, reasoning tokens, provider-reported cost, served model and provider, attempts and
      status history go into the backend-neutral result's ``extra``.
    * **Free mode** (set by cloud_run.py after free_mode.start_free passed): ``gate`` (a rate_gate.RateGate) is
      asked before every attempt and may wait or stop the call; ``free_target`` makes every 200 face the zero-spend
      check (usage.cost exactly 0, the requested :free model), whose failure stops the run as ``not_free``; a 429
      naming the daily quota stops it as ``quota`` (never retried), and several 429 in a row as ``rate_limited``.
    """

    name = "openai"

    def __init__(self, base_url, timeout, api_key, extra_body=None, reasoning=None, drop_params=(),
                 schema_normalise=False, schema_strip=(), max_tokens_field="max_tokens", max_attempts=5,
                 retry_base_s=2.0, retry_cap_s=60.0, expect_provider=None, sleep=time.sleep, rng=None):
        self.base = check_base_url(base_url)
        self._opener = opener(self.base)
        self.timeout = timeout
        self._key = check_key(api_key)
        if self._key and self._key in self.base:
            raise ValueError("--base-url contains the API key; the key goes only in --api-key-env")
        self._headers = {"Content-Type": "application/json"}
        if self._key:
            self._headers["Authorization"] = f"Bearer {self._key}"
        self.extra_body = dict(extra_body or {})
        check_extra_body(self.extra_body, self._key, reasoning)
        self.reasoning = reasoning  # None = field not sent (--reasoning omit)
        self.drop_params = tuple(drop_params)
        self.schema_normalise = bool(schema_normalise)
        self.schema_strip = tuple(schema_strip)
        unknown = [k for k in self.schema_strip if k not in STRIPPABLE_KEYWORDS]
        if unknown:
            raise ValueError(f"--schema-strip may drop only validation limits and annotations "
                             f"({', '.join(STRIPPABLE_KEYWORDS)}), not {', '.join(unknown)}: that would loosen the "
                             f"strict arm")
        if max_tokens_field not in ("max_tokens", "max_completion_tokens"):
            raise ValueError("max_tokens_field must be max_tokens or max_completion_tokens")
        self.max_tokens_field = max_tokens_field
        self.max_attempts = max(1, int(max_attempts))
        self.retry_base_s, self.retry_cap_s = float(retry_base_s), float(retry_cap_s)
        for flag, value in (("--retry-base-s", self.retry_base_s), ("--retry-cap-s", self.retry_cap_s),
                            ("--timeout", float(timeout))):
            # A negative backoff would crash time.sleep mid-call; a zero or negative timeout never completes.
            if not math.isfinite(value) or value < 0 or (flag == "--timeout" and value == 0):
                raise ValueError(f"{flag} must be a finite number of seconds >= 0 (> 0 for --timeout), got {value}")
        self.expect_provider = expect_provider
        self._sleep = sleep
        self._rng = rng or random.Random()
        # Free mode and the client-side rate caps; attached by cloud_run.Session.start (None: paid path as before).
        self.gate = None
        self.free_target = None

    # ── Secrets ──────────────────────────────────────────────────────────────

    def redact(self, text):
        """Remove the key (verbatim) and anything shaped like an OpenRouter key from a string that may reach a
        record, a log line or the console."""
        if not isinstance(text, str):
            return text
        if self._key:
            text = text.replace(self._key, "[REDACTED]")
        return _OPENROUTER_KEY.sub("[REDACTED]", text) if "sk-or-" in text else text

    # ── Request ──────────────────────────────────────────────────────────────

    def probe(self, model):
        """No network: a cloud endpoint reports nothing about its build; the pin in --extra-body names the quantisation."""
        prov = self.extra_body.get("provider") if isinstance(self.extra_body.get("provider"), dict) else {}
        quants = prov.get("quantizations") if isinstance(prov.get("quantizations"), list) else []
        return {"runtime_version": None, "model_file": None, "quant": quants[0] if len(quants) == 1 else None,
                "model": model}

    def payload(self, model, messages, schema, temperature, seed, num_predict, num_ctx, sampler, schema_name):
        """The /chat/completions body. ``num_ctx`` is not sent: the endpoint fixes the context."""
        body = {"model": model, "messages": messages, "stream": False, self.max_tokens_field: num_predict}
        if "temperature" not in self.drop_params:
            body["temperature"] = temperature
        if "seed" not in self.drop_params:
            body["seed"] = seed
        body.update({k: v for k, v in sampler.items() if v is not None and k not in self.drop_params})
        if schema is not None:
            wire = schema
            if self.schema_normalise or self.schema_strip:
                wire, _ = normalise_schema(schema, self.schema_normalise, self.schema_strip)
            body["response_format"] = {"type": "json_schema",
                                       "json_schema": {"name": schema_name, "strict": True, "schema": wire}}
        if self.reasoning is not None:
            body["reasoning"] = self.reasoning
        body.update(self.extra_body)
        return body

    def _post(self, body):
        """One HTTP attempt. Returns (status, lower-case headers, body text, exception or None).

        status is the HTTP code; None when the connection failed or timed out (the request may have been
        processed); ``_LOCAL_FAILURE`` when Python refused to build or send it (for example an invalid header).
        A body over MAX_BODY_BYTES comes back as "" with a ValueError.
        """
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(self.base + "/chat/completions", data=data, headers=self._headers,
                                     method="POST")
        try:
            with self._opener.open(req, timeout=self.timeout) as resp:
                raw, too_big = read_capped(resp)
                return resp.status, {k.lower(): v for k, v in resp.headers.items()}, raw, too_big
        except urllib.error.HTTPError as e:
            try:
                raw, _ = read_capped(e)
            except (OSError, http.client.HTTPException):
                raw = ""
            headers = {k.lower(): v for k, v in (e.headers.items() if e.headers else [])}
            return e.code, headers, raw, e
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError, http.client.HTTPException) as e:
            return None, {}, "", e
        except ValueError as e:
            # http.client raises ValueError for an invalid header or URL, with the offending value (possibly the
            # key) in the message; chat() redacts it and stops the run.
            return _LOCAL_FAILURE, {}, "", e

    def _delay(self, attempt, headers):
        """Retry-After when the server sends one (capped), else full jitter: uniform(0, min(cap, base * 2^(n-1)))."""
        after = _retry_after_seconds(headers)
        if after is not None:
            return min(after, self.retry_cap_s)
        return self._rng.uniform(0.0, min(self.retry_cap_s, self.retry_base_s * (2 ** (attempt - 1))))

    def key_info(self):
        """OpenRouter's GET <base>/key (sends no prompt): the non-secret fields of the key record
        (free_mode.key_summary): credit limit, what is left of it, usage, BYOK usage, the management flag, expiry and
        the account's daily free-request counter. The ``label`` (a partly masked key) and account ids are dropped."""
        req = urllib.request.Request(self.base + "/key", headers=self._headers, method="GET")
        with self._opener.open(req, timeout=min(self.timeout, 30.0)) as resp:
            data = _json_or_none(read_capped(resp)[0])
        d = data.get("data") if isinstance(data, dict) else None
        if not isinstance(d, dict):
            raise ValueError("unexpected /key response")
        return key_summary(d)

    def key_read(self):
        """GET <base>/key once, never raising (``run.py --key-status``, key_status.py): (HTTP status or None,
        lower-case headers, body text, exception or None), from cloud_guard.get_capped. Unlike ``key_info`` it hands
        back a 4xx or 5xx with its body, so the caller can name the next step; the body is untrusted and may echo the
        key or the record's ``label``, so pass anything shown through ``redact`` first."""
        return get_capped(self._opener, self.base + "/key", self._headers, min(self.timeout, 30.0))

    # ── One call ─────────────────────────────────────────────────────────────

    def chat(self, body, budget=None, call_id=None):
        """Send one call with retries under the budget; return a backend-neutral result dict.

        ``fatal`` is None, or why the run must stop now: ``budget`` (the cap, or HTTP 402 as a status or inside a
        200), ``schema_rejected``, ``config`` (another 4xx, a refused redirect, a 200 that is not a JSON completion,
        a request Python could not send), ``provider_mismatch``, ``cost_anomaly`` (an attempt cost more than its
        worst case, so a price flag or max_tokens is not what the endpoint applies; checked on every attempt, and
        the call stops at once) or ``reasoning_leak`` (reasoning tokens billed, or thinking text returned, on a
        call sent with effort none); with a rate gate or in free mode also ``quota`` (the day's request allowance
        is used up, or a 429 names the daily cap), ``rate_limited`` (several 429 in a row) and ``not_free`` (a
        response was charged or served by another model, or the key's usage moved).
        """
        reservation = budget.reservation_usd(body) if budget is not None else 0.0
        history, slept, costs, sources = [], [], [], []
        resp, error, fatal, exhausted = None, None, None, True
        schema_sent = "response_format" in body
        for attempt in range(1, self.max_attempts + 1):
            # ── Rate gate: the day's allowance, the key poll, the per-minute window (may wait, or stop unsent) ──
            if self.gate is not None:
                stop = self.gate.before_attempt()
                if stop is not None:
                    fatal, error = stop
                    exhausted = False
                    break
            # ── Budget gate: nothing is sent unless its worst case still fits under the cap ──
            if budget is not None:
                ok, spent = budget.try_reserve(call_id, attempt, reservation)
                if not ok:
                    error = (f"BudgetLimited: spent {spent:.6f} USD + worst case {reservation:.6f} USD for the next "
                             f"attempt would exceed the cap of {budget.cap_usd:.6f} USD")
                    fatal, exhausted = "budget", False
                    break
            status, headers, raw, exc = self._post(body)
            history.append(status if status is not None else type(exc).__name__)
            data = _json_or_none(raw)
            too_many_429 = self.gate.note_response(status) if self.gate is not None else False
            wait_override = None
            if status == 200 and isinstance(data, dict):
                embedded = _embedded_error(data)
                cost, source = (budget.cost_from_usage(data.get("usage")) if budget is not None else (None, None))
                if cost is None:
                    cost, source = reservation, "reserved"
                costs.append(cost)
                sources.append(source)
                if embedded is not None:
                    error = f"provider error inside HTTP 200 (code {embedded[0]}): {embedded[1]}"
                if self.free_target is not None:
                    # ── Zero-spend check (free mode): charged, or another model, stops the run before any retry ──
                    why = paid_signal(data, self.free_target, answered=embedded is None)
                    if why:
                        error = f"zero-spend guard: {why}"
                        resp = data if embedded is None else None
                        fatal, exhausted = "not_free", False
                        break
                if budget is not None and cost > reservation * (1 + 1e-9) + 1e-12:
                    # ── Cost anomaly: stop now, before any retry can spend again at the wrong price ──
                    resp = data if embedded is None else None
                    fatal, exhausted = "cost_anomaly", False
                    break
                if embedded is None:
                    resp, error, exhausted = data, None, False
                    break
                code, text = embedded
                if code == 402:
                    fatal, exhausted = "budget", False  # out of credits, reported inside a 200
                    break
                if code in (401, 403):
                    fatal, exhausted = "config", False  # a bad or unauthorised key, reported inside a 200
                    break
                if code == 429 and self.gate is not None and classify_429(headers, data, time.time())[0] == "daily":
                    # The daily quota reported inside a 200 is as terminal as the HTTP status: a retry only burns it.
                    error += "; the daily quota is used up: resume after 00:00 UTC with the same command plus --resume"
                    fatal, exhausted = "quota", False
                    break
                if schema_sent and code is not None and 400 <= code <= 499 and \
                        any(w in text.lower() for w in _SCHEMA_WORDS):
                    fatal, exhausted = "schema_rejected", False
                    break
                if not (code is not None and _retryable(code)):
                    exhausted = False
                    break
            elif status == _LOCAL_FAILURE:
                # Python refused to build or send the request. Charged in full in case some bytes left anyway;
                # never retried (it would fail the same way).
                costs.append(reservation)
                sources.append("reserved")
                error = f"the request could not be sent ({type(exc).__name__}: {exc})"
                fatal, exhausted = "config", False
                break
            elif status is None:
                # Timeout or dropped connection: the provider may have processed (and billed) the prompt.
                costs.append(reservation)
                sources.append("reserved")
                error = f"{type(exc).__name__}: {exc}"
            elif status == 200:
                # A stream despite stream=false, a portal or proxy page, a truncated or oversized body: the model may
                # have run, so it is charged; the next attempt would most likely get the same, so the run stops.
                costs.append(reservation)
                sources.append("reserved")
                error = ("HTTP 200 with a body that is not a JSON completion" + (f" ({exc})" if exc else "")
                         + "; check --base-url and that the endpoint honours stream=false")
                fatal, exhausted = "config", False
                break
            elif _is_redirect(status):
                costs.append(0.0)
                sources.append("unbilled")
                target = redirect_host(headers) or None  # never raises: a 300 keeps a malformed Location intact
                error = (f"HTTP {status}: the endpoint redirects (to host {target!r}); redirects are never followed so "
                         f"the key is never forwarded; pass the final URL as --base-url")
                fatal, exhausted = "config", False
                break
            elif status == 402:
                costs.append(0.0)
                sources.append("unbilled")
                error = f"HTTP 402, out of credits or over the key's limit (never retried): {_error_text(data, raw)}"
                if self.free_target is not None:
                    error += ("; on a :free model this means a negative account balance, or a key credit limit that "
                              "blocks free calls (see cloud/README.md)")
                fatal, exhausted = "budget", False
                break
            elif status == 429 and self.gate is not None:
                # ── Rate limits with a gate: the daily cap is terminal; the minute window and upstream are retried ──
                costs.append(0.0)
                sources.append("unbilled")
                kind, wait = classify_429(headers, data, time.time(), _retry_after_seconds(headers))
                error = f"HTTP 429 ({kind} rate limit): {_error_text(data, raw)}"
                if kind == "daily":
                    resume = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + (wait or 0.0)))
                    error += f"; the daily quota is used up: resume after {resume} with the same command plus --resume"
                    fatal, exhausted = "quota", False
                    break
                if too_many_429:
                    error += (f"; {self.gate.consecutive_429} HTTP 429 in a row: stopping to spare the quota; resume "
                              f"later with --resume")
                    fatal, exhausted = "rate_limited", False
                    break
                wait_override = wait
            elif self.free_target is not None and status in (404, 503) and no_route(_error_text(data, raw)):
                # No endpoint may serve the request (privacy settings, ZDR, a guardrail): a retry cannot help and would
                # spend another of the day's requests.
                costs.append(0.0)
                sources.append("unbilled")
                error = f"HTTP {status}, no endpoint may serve this request ({NO_ROUTE_HINT}): {_error_text(data, raw)}"
                fatal, exhausted = "config", False
                break
            elif _retryable(status):
                billed = status not in UNBILLED_STATUS
                costs.append(reservation if billed else 0.0)
                sources.append("reserved" if billed else "unbilled")
                error = f"HTTP {status}: {_error_text(data, raw)}"
            else:
                billed = status not in UNBILLED_STATUS
                costs.append(reservation if billed else 0.0)
                sources.append("reserved" if billed else "unbilled")
                text = _error_text(data, raw)
                if schema_sent and any(w in text.lower() for w in _SCHEMA_WORDS):
                    error = (f"HTTP {status}: the endpoint rejected the strict json_schema response_format; pin an "
                             f"endpoint that supports structured outputs (never retried without the schema): {text}")
                    fatal = "schema_rejected"
                else:
                    error = f"HTTP {status}, a configuration fault (never retried): {text}"
                    fatal = "config"
                exhausted = False
                break
            # ── Back off before the next attempt (a 429's own reset or Retry-After first, capped) ──
            if attempt < self.max_attempts:
                delay = (min(max(0.0, wait_override), self.retry_cap_s) if wait_override is not None
                         else self._delay(attempt, headers))
                slept.append(round(delay, 3))
                self._sleep(delay)
        if exhausted and error:
            error = f"gave up after {len(history)} attempts; last: {error}"

        # ── Charge the call ──
        total = round(sum(costs), 12)
        billed_sources = sorted({s for s in sources if s != "unbilled"})
        cost_source = "+".join(billed_sources) or ("unbilled" if sources else "not-sent")
        if budget is not None:
            budget.settle(call_id, total, cost_source)

        r = resp or {}
        choices = r.get("choices") if isinstance(r.get("choices"), list) else []
        choice = choices[0] if choices and isinstance(choices[0], dict) else {}
        msg = choice.get("message") if isinstance(choice.get("message"), dict) else {}
        content = msg.get("content") if isinstance(msg.get("content"), str) else ""
        reasoning_text = msg.get("reasoning") or msg.get("reasoning_content") or ""
        reasoning_text = reasoning_text if isinstance(reasoning_text, str) else ""
        in_content = sum(len(t) for t in re.findall(r"<think>(.*?)</think>", content, re.S))
        usage = r.get("usage") if isinstance(r.get("usage"), dict) else {}
        u = usage_fields(usage)
        served_provider = r.get("provider") if isinstance(r.get("provider"), str) else None

        # ── Checks that stop the run after this record is written ──
        if resp is not None and fatal is None:
            # Thinking that came back as text counts too: some providers do not report reasoning tokens, and a
            # template's empty "<think>\n\n</think>" is not thinking, so only non-blank text counts.
            thought = len(reasoning_text.strip()) + sum(len(t.strip()) for t in _think_blocks(content))
            if self.expect_provider and served_provider is not None and \
                    not provider_matches(self.expect_provider, served_provider):
                error = f"provider mismatch: served by {served_provider!r}, pinned {self.expect_provider!r}"
                fatal = "provider_mismatch"
            elif isinstance(self.reasoning, dict) and self.reasoning.get("effort") == "none" and \
                    ((u["reasoning_tokens"] or 0) > 0 or thought > 0):
                # The answer is not a direct-mode answer, so it is an error: neither scored nor skipped on --resume.
                error = (f"reasoning on an effort-none call ({u['reasoning_tokens'] or 0} reasoning tokens, "
                         f"{thought} characters of thinking text)")
                fatal = "reasoning_leak"

        extra = {
            "usage": usage or None,
            "model_served": r.get("model") if isinstance(r.get("model"), str) else None,
            "provider_served": served_provider,
            "provider_unverified": bool(self.expect_provider) and resp is not None and served_provider is None,
            "generation_id": r.get("id") if isinstance(r.get("id"), str) else None,
            "native_finish_reason": choice.get("native_finish_reason"),
            "reasoning_sent": body.get("reasoning", "omit"),
            "reasoning_tokens": u["reasoning_tokens"], "visible_tokens": u["visible_tokens"],
            "cached_tokens": u["cached_tokens"], "cache_write_tokens": u["cache_write_tokens"],
            "params_sent": [k for k in body if k not in ("model", "messages", "stream")],
            "seed_sent": "seed" in body,
            "attempts": len(history), "http_status_history": history, "retry_after_s": slept,
            "reserved_usd": round(reservation, 12), "attempt_costs_usd": [round(c, 12) for c in costs],
            "cost_usd": total, "cost_source": cost_source,
            "cost_anomaly": fatal == "cost_anomaly",
            "system_fingerprint": r.get("system_fingerprint"),
            "rate_gate": self.gate.status() if self.gate is not None else None,
        }
        extra = {k: self.redact(v) if isinstance(v, str) else v for k, v in extra.items()}
        return {
            "error": self.redact(error) if error else None, "fatal": fatal,
            "think_sent": "reasoning" in body,
            "content": self.redact(content),
            "thinking_chars": (len(reasoning_text) if isinstance(reasoning_text, str) else 0) + in_content,
            "prompt_eval_count": u["prompt_tokens"], "eval_count": u["completion_tokens"],
            # A cloud endpoint reports no generation time; score.py skips None when it computes tokens/s.
            "eval_duration": None, "prompt_eval_duration": None, "load_duration": None, "total_duration": None,
            "done_reason": choice.get("finish_reason"),
            "extra": extra,
        }
