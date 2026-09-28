#!/usr/bin/env python3
"""Free-model mode (``--free-only``): OpenRouter ``:free`` models with no way to spend (tools/local-qual).

What it owns
------------
The rules that let the ``openai`` backend run OpenRouter's free model variants at zero spend and inside the free
tier's limits:

* the command line (``add_free_args``, ``apply_free_flags``): one ``<author>/<slug>:free`` id outside the
  ``openrouter/`` router namespace, OpenRouter (or a loopback test server) as the host, a cap and prices of 0, a
  shared ``--ledger``, the rate-cap defaults, and a provider block that makes OpenRouter skip an endpoint lacking any
  parameter sent (``require_parameters: true``, so a strict schema is never silently dropped) and never fall back to
  another endpoint (``allow_fallbacks: false``);
* the start check against the live public catalogue (``model_entry``, ``check_catalogue``): the exact id listed,
  every price present exactly 0, text output only, every endpoint zero-priced, every body parameter supported;
* the key check (rules in free_key.py, re-exported here): never a management key, no paid-model headroom above a
  threshold, not expired, the account's daily free-request counter readable, and no rise in the key's spend since
  the ledger's last key reading; only non-secret fields are kept or printed;
* the per-response zero-spend check (``paid_signal``) and the no-route test for 404/503 bodies (``no_route``);
* ``start_free``, run by cloud_run.Session on every start and resume, which attaches the rate gate (rate_gate.py)
  with a key poll that stops the run if the key's usage moves and writes each reading to the ledger, and
  ``final_check``, which cloud_run.Session runs however a started run ends (done, a fatal result, the canary, a
  quota stop).

How it fits
-----------
cloud_run.py calls ``add_free_args`` and ``apply_free_flags`` while it parses the flags and ``start_free`` from
``Session.start``; cloud_backend.py calls ``paid_signal`` and ``no_route`` inside ``chat``. The paid path's budget
(budget.py) still runs with a cap and prices of 0, so any charged amount is a stop there too. This module imports
only cloud_guard.py, free_key.py, rate_gate.py and the standard library, so cloud_backend.py can import it without a
cycle.

Sources (read 2026-09-27)
-------------------------
[L] https://openrouter.ai/docs/api_reference/limits : the free-tier limits; a negative balance gives 402 even on free
models. [K] https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key : the ``GET /key`` fields.
[FV] https://openrouter.ai/docs/guides/routing/model-variants/free : a free variant is its own catalogue entry.
[HAUTO] https://openrouter.zendesk.com/hc/en-us/articles/51679572756123 : ``openrouter/auto:free`` can bill paid
models. [PS] https://openrouter.ai/docs/guides/routing/provider-selection : ``require_parameters``,
``allow_fallbacks``, ``max_price``. [UA] https://openrouter.ai/docs/guides/guides/usage-accounting : ``usage.cost``
is what the account is charged. Live public ``GET https://openrouter.ai/api/v1/models`` and
``/models/<id>/endpoints``: routers are priced ``"-1"``, no model has a ``request`` price key, and two zero-priced
music models without ``:free`` bill per clip.
"""
import datetime as _dt
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation

import rate_gate
from cloud_guard import is_loopback, opener, provider_matches, read_capped
# The key-record rules live in free_key.py; they are re-exported here for the modules and tests that import them from
# free_mode (cloud_backend.py takes key_summary from this module).
from free_key import (baseline_rise, describe_key, key_headroom, key_refusal, key_row, key_summary,  # noqa: F401
                      usage_rise)
from rate_gate import RateGate, utc_day

# ── Limits and defaults ──────────────────────────────────────────────────────

# A free variant's id [FV]: one author, one slug, the ":free" suffix and no other variant suffix (":online",
# ":nitro", ":batch" and the like change routing or billing). Lower case, as every id in the live catalogue is; the
# "~author/slug-latest" aliases do not match.
FREE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]*:free$")
# Router namespace: "openrouter/auto:free" ends in ":free" but may bill paid models [HAUTO]; "openrouter/free" picks a
# free model at random, so a run could not be attributed to one model.
ROUTER_PREFIXES = ("openrouter/",)
# Pricing keys that are not prices: endpoint rows carry a numeric "discount".
NOT_PRICES = frozenset(("discount",))
# The supported_parameters name each body field needs on the endpoint (other fields map to themselves). A strict
# json_schema needs "structured_outputs": an endpoint listing only "response_format" may offer JSON mode only.
PARAM_NAMES = {"max_completion_tokens": "max_tokens", "response_format": "structured_outputs",
               "repeat_penalty": "repetition_penalty"}
NOT_PARAMS = frozenset(("model", "messages", "stream", "provider"))
PARAM_HINTS = {"structured_outputs": "run this model's arms without a response schema (--schema-mode none)",
               "reasoning": "pass --reasoning omit"}
# Words in a 404 or 503 body meaning that no endpoint may serve the request (privacy settings, ZDR, a guardrail, or
# require_parameters with nothing left); retrying would only spend daily requests.
NO_ROUTE_WORDS = ("no endpoints", "no available model provider", "routing requirements", "data policy", "guardrail")
NO_ROUTE_HINT = ("the account's privacy settings for free endpoints (the training and publication toggles, ZDR), a "
                 "guardrail on the key, or require_parameters left no endpoint; see cloud/README.md")
# The one-free-run-at-a-time lock (cloud_run.Session takes it as <folder>/free-run.lock), and how messages name it:
# by the variable, never as an expanded path, which would carry the user name.
FREE_LOCK_NAME = "free-run"
FREE_LOCK_SHOWN = (r"%LOCALAPPDATA%\plotroom-dev\free-run.lock" if os.name == "nt"
                   else "$XDG_STATE_HOME/plotroom-dev/free-run.lock (default ~/.local/state/plotroom-dev)")


class FreeRefusal(Exception):
    """A start check failed. ``kind`` is ``not_free`` (the model is not free-only safe right now) or ``config`` (the
    run cannot start as asked); cloud_run.py turns it into a stop row and an exit code."""

    def __init__(self, kind, message):
        super().__init__(message)
        self.kind, self.message = kind, message


# ── Command line (offline: nothing is sent) ──────────────────────────────────

def add_free_args(ap):
    """The free-mode flags (see cloud/README.md for the runbook)."""
    free = ap.add_argument_group("free models (OpenRouter :free variants, zero spend; see cloud/README.md)")
    free.add_argument("--free-only", action="store_true",
                      help="spend nothing: the model id must be <author>/<slug>:free and zero-priced in the live "
                           "catalogue at every start; --max-usd and the prices are 0; every response must report "
                           "usage.cost 0 and the requested model (else exit 9); the key check, the rate caps and "
                           "the key poll are on; needs --ledger")
    free.add_argument("--rpm", type=int, default=None,
                      help=f"most attempts in any 60 s window (free default {rate_gate.FREE_RPM_DEFAULT}; OpenRouter "
                           f"allows {rate_gate.FREE_RPM_LIMIT} per minute on :free models)")
    free.add_argument("--max-requests-per-day", type=int, default=None,
                      help=f"most attempts per UTC day recorded in the ledger by every run sharing it (free default "
                           f"{rate_gate.FREE_DAILY_DEFAULT}: OpenRouter allows 50 a day per account under 10 "
                           f"purchased credits, 1,000 from 10); the account's own remaining count also applies")
    free.add_argument("--daily-reserve", type=int, default=rate_gate.DAILY_RESERVE_DEFAULT,
                      help="free requests of the account's daily quota left unused (default 5)")
    free.add_argument("--max-consecutive-429", type=int, default=rate_gate.MAX_CONSECUTIVE_429_DEFAULT,
                      help="stop (exit 10, resume later) after this many 429 in a row, as HTTP 429 or inside an "
                           "HTTP 200 (default 3)")
    free.add_argument("--key-poll-every", type=int, default=rate_gate.KEY_POLL_EVERY_DEFAULT,
                      help="read GET /key after at most this many attempts and stop if the key's usage moved "
                           "(1-10, default 10)")
    free.add_argument("--max-key-headroom-usd", type=float, default=None,
                      help="free-only: refuse a key that could spend more than this on paid models (default 0: "
                           "create the key with a credit limit of 0)")
    free.add_argument("--allow-key-headroom", action="store_true",
                      help="free-only: run even though the key could spend more than --max-key-headroom-usd")


def free_model_refusal(model):
    """Why ``model`` cannot be a free-only target, or None. Offline: the live catalogue is read at run start."""
    m = (model or "").strip()
    if m.startswith(ROUTER_PREFIXES):
        return (f"--free-only refuses {m!r}: ids under openrouter/ are routers (openrouter/auto:free can bill paid "
                f"models; openrouter/free picks a model at random)")
    if not FREE_ID.match(m):
        return (f"--free-only needs one free model id <author>/<slug>:free (lower case, no other variant suffix), "
                f"not {m!r}")
    return None


def free_lock_dir():
    """The per-user folder of the one-free-run-at-a-time lock, outside every repository.

    OpenRouter's free limits (20 requests a minute, 50 or 1,000 a day) are per account, but a ledger lock only
    serialises runs that share a ledger, so two free runs on two ledgers could each keep their own minute window and
    day count. This lock makes free runs on any ledger go one at a time. Windows: %LOCALAPPDATA%\\plotroom-dev (next to
    the key store); elsewhere $XDG_STATE_HOME/plotroom-dev, by default ~/.local/state/plotroom-dev.
    """
    base = os.environ.get("LOCALAPPDATA") if os.name == "nt" else os.environ.get("XDG_STATE_HOME")
    return os.path.join(base or os.path.join(os.path.expanduser("~"), ".local", "state"), "plotroom-dev")


def free_host_ok(host):
    """Free mode reads OpenRouter's catalogue and key record, so it runs against OpenRouter (or a local test server)."""
    return host == "openrouter.ai" or is_loopback(host or "")


def free_extra_body(extra_body):
    """A copy of --extra-body with the routing free mode needs; ValueError when it asks for looser routing.

    ``require_parameters: true`` makes OpenRouter use only endpoints that support every parameter sent, so a strict
    ``response_format`` is never answered unconstrained, and ``allow_fallbacks: false`` keeps a request off any other
    endpoint [PS]. ``max_price`` is accepted only with every value 0 (a looser one would admit priced endpoints).
    """
    prov = extra_body.get("provider", {})
    if not isinstance(prov, dict):
        raise ValueError("--extra-body provider must be a JSON object")
    if prov.get("require_parameters", True) is not True:
        raise ValueError("--free-only sends provider.require_parameters true (an endpoint lacking a parameter, the "
                         "strict schema included, is skipped instead of answering unconstrained); do not set it false")
    if prov.get("allow_fallbacks", False) is not False:
        raise ValueError("--free-only sends provider.allow_fallbacks false (a fallback could be a paid endpoint); do "
                         "not set it true")
    max_price = prov.get("max_price")
    if max_price is not None and (not isinstance(max_price, dict) or not all(exact_zero(v) for v in max_price.values())):
        raise ValueError("--free-only accepts provider.max_price only with every value 0")
    out = dict(extra_body)
    out["provider"] = dict(prov, require_parameters=True, allow_fallbacks=False)
    return out


def apply_free_flags(args, extra_body):
    """--free-only: check the flags and set their free values; returns the extra body to send, or ValueError.

    The cap and the prices become 0 and the rate caps get their free defaults, so the records show what was in force.
    """
    why = free_model_refusal(args.model)
    if why:
        raise ValueError(why)
    if not free_host_ok(urllib.parse.urlsplit((args.base_url or "").strip()).hostname or ""):
        raise ValueError("--free-only runs against OpenRouter (--base-url https://openrouter.ai/api/v1): it reads "
                         "OpenRouter's public catalogue and key record")
    for flag, value in (("--max-usd", args.max_usd), ("--price-in", args.price_in), ("--price-out", args.price_out),
                        ("--price-cache-read", args.price_cache_read)):
        if value is not None and value != 0:
            raise ValueError(f"--free-only spends nothing: leave {flag} out (or set it to 0)")
    if not args.ledger and not args.dry_run:
        raise ValueError("--free-only needs --ledger: one file shared by every free run, which counts the day's "
                         "requests (OpenRouter's free quota is per account, not per run)")
    args.max_usd, args.price_in, args.price_out, args.price_cache_read = 0.0, 0.0, 0.0, None
    args.rpm = rate_gate.FREE_RPM_DEFAULT if args.rpm is None else args.rpm
    if args.max_requests_per_day is None:
        args.max_requests_per_day = rate_gate.FREE_DAILY_DEFAULT
    if args.max_key_headroom_usd is None:
        args.max_key_headroom_usd = 0.0
    if not 1 <= args.rpm <= rate_gate.FREE_RPM_LIMIT:
        raise ValueError(f"--rpm must be 1-{rate_gate.FREE_RPM_LIMIT} with --free-only (OpenRouter's per-minute limit)")
    if not 1 <= args.key_poll_every <= rate_gate.KEY_POLL_EVERY_MAX:
        raise ValueError(f"--key-poll-every must be 1-{rate_gate.KEY_POLL_EVERY_MAX}")
    if args.daily_reserve < 0 or args.max_consecutive_429 < 1:
        raise ValueError("--daily-reserve must be >= 0 and --max-consecutive-429 >= 1")
    h = args.max_key_headroom_usd
    if not (isinstance(h, (int, float)) and math.isfinite(h) and h >= 0):
        raise ValueError(f"--max-key-headroom-usd must be a finite number >= 0, got {h}")
    return free_extra_body(extra_body)


# ── Prices ───────────────────────────────────────────────────────────────────

def exact_zero(value):
    """Is ``value`` (a JSON number or numeric string) exactly 0?

    Decimal equality, never a float ``<= 0`` test: routers are priced "-1" and must not pass; NaN, infinities,
    booleans, None and non-numbers are not 0 either.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return False
    try:
        d = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return False
    return d.is_finite() and d == 0


def pricing_problems(pricing, where):
    """Every way ``pricing`` (a /models or /endpoints pricing object) is not free; [] when it is.

    ``prompt`` and ``completion`` must be present; every other key present (request, image, web_search,
    internal_reasoning, cache prices, audio, ...) must be exactly 0 too. A missing key is not a price: no model in the
    live catalogue has a ``request`` key, so requiring one would refuse every model. ``overrides`` (tiered prices)
    must be absent or zero-priced; keys named ``min_*``/``max_*`` in it are thresholds (``min_prompt_tokens``).
    """
    if not isinstance(pricing, dict):
        return [f"{where}: no pricing object"]
    problems = [f"{where}: no {k} price" for k in ("prompt", "completion") if k not in pricing]
    for key, value in pricing.items():
        if key in NOT_PRICES:
            continue
        if key == "overrides":
            if value in (None, [], {}):
                continue
            for i, entry in enumerate(value if isinstance(value, list) else [value]):
                if not isinstance(entry, dict):
                    problems.append(f"{where}: overrides[{i}] is not an object")
                    continue
                problems += [f"{where}: overrides[{i}].{k} {v!r} is not exactly 0" for k, v in entry.items()
                             if not str(k).startswith(("min_", "max_")) and not exact_zero(v)]
            continue
        if not exact_zero(value):
            problems.append(f"{where}: {key} price {value!r} is not exactly 0")
    return problems


# ── Catalogue (public, keyless) ──────────────────────────────────────────────

def get_public_json(base, path, timeout):
    """GET ``base + path`` from the public API: no Authorization header (the catalogue needs no key, so the key does
    not travel), redirects refused and the body capped (cloud_guard.py). Raises on any failure."""
    req = urllib.request.Request(base + path, headers={"Accept": "application/json"}, method="GET")
    with opener(base).open(req, timeout=timeout) as resp:
        text, too_big = read_capped(resp)
    if too_big is not None:
        raise too_big
    return json.loads(text)


def model_entry(models, model):
    """The /models entry whose id is exactly ``model``, or FreeRefusal."""
    data = models.get("data") if isinstance(models, dict) else None
    if not isinstance(data, list):
        raise FreeRefusal("config", "the public model list has an unexpected shape")
    entry = next((m for m in data if isinstance(m, dict) and m.get("id") == model), None)
    if entry is None:
        raise FreeRefusal("not_free", f"{model} is not in OpenRouter's live model list (free variants are added and "
                                      f"removed without notice); pick a listed :free model")
    return entry


def _parse_date(value):
    """A date from 'YYYY-MM-DD' or an ISO timestamp, else None."""
    if not isinstance(value, str):
        return None
    try:
        return _dt.date.fromisoformat(value[:10])
    except ValueError:
        return None


def _endpoint_row(ep):
    """The fields of one /endpoints row that the run records and routes by."""
    sp = ep.get("supported_parameters")
    return {"tag": ep.get("tag") if isinstance(ep.get("tag"), str) else None,
            "name": ep.get("name") if isinstance(ep.get("name"), str) else None,
            "provider_name": ep.get("provider_name") if isinstance(ep.get("provider_name"), str) else None,
            "quantization": ep.get("quantization") if isinstance(ep.get("quantization"), str) else None,
            "status": ep.get("status") if isinstance(ep.get("status"), (int, float)) else None,
            "uptime_last_1d": ep.get("uptime_last_1d") if isinstance(ep.get("uptime_last_1d"), (int, float)) else None,
            "supported_parameters": sorted(p for p in sp if isinstance(p, str)) if isinstance(sp, list) else []}


def _serves(pin, row):
    """Does a provider.only entry name this endpoint (its tag, or its provider)?"""
    return pin == row["tag"] or provider_matches(pin, row["provider_name"]) or provider_matches(pin, row["tag"])


def check_catalogue(entry, endpoints, model, payload, pinned, today):
    """Check a model's live catalogue entry and endpoints for a free-only run; return (target, pin, warnings).

    Raises FreeRefusal("not_free") when anything is priced, the output is not text only, the model is due for removal
    or no endpoint serves it; FreeRefusal("config") when the pin names no live endpoint or an endpoint lacks a
    parameter the run sends (with require_parameters, such a request would route nowhere and still use one of the
    day's scarce requests). ``payload`` is one request body of the run, ``pinned`` the provider.only list of
    --extra-body (None pins every live endpoint), ``today`` a date. ``target`` is what ``paid_signal`` compares each
    response with; ``pin`` the provider.only list to send.
    """
    problems = pricing_problems(entry.get("pricing"), "model pricing")
    arch = entry.get("architecture") if isinstance(entry.get("architecture"), dict) else {}
    if arch.get("output_modalities") != ["text"]:
        problems.append(f"output modalities {arch.get('output_modalities')!r}, not text only (non-text models can bill "
                        f"per image or clip at zero token prices)")
    warnings = []
    if entry.get("expiration_date") is not None:
        exp = _parse_date(entry.get("expiration_date"))
        if exp is None or exp <= today:
            problems.append(f"expiration_date {entry.get('expiration_date')!r}: the model is due for removal")
        else:
            warnings.append(f"{model} may be removed after {exp.isoformat()} (expiration_date)")
    data = endpoints.get("data") if isinstance(endpoints, dict) else None
    eps = data.get("endpoints") if isinstance(data, dict) else None
    if not isinstance(eps, list) or not eps:
        problems.append("no endpoint serves this free variant now")
        eps = []
    rows = []
    for ep in eps:
        if not isinstance(ep, dict):
            problems.append("an endpoint row is not an object")
            continue
        row = _endpoint_row(ep)
        problems += pricing_problems(ep.get("pricing"), f"endpoint {row['tag'] or row['name']!r}")
        if ep.get("model_id") not in (None, model):
            problems.append(f"endpoint {row['tag']!r} serves {ep.get('model_id')!r}, not {model}")
        if isinstance(row["status"], (int, float)) and row["status"] < 0:
            warnings.append(f"endpoint {row['tag']} reports status {row['status']} (uptime over one day "
                            f"{row['uptime_last_1d']}%): expect errors")
        rows.append(row)
    if problems:
        raise FreeRefusal("not_free", f"{model} is not free-only safe right now: " + "; ".join(problems))

    # ── Routing: the pin, then every parameter the run sends ──
    tags = [r["tag"] for r in rows if r["tag"]]
    if pinned:
        unknown = [p for p in pinned if not any(_serves(p, r) for r in rows)]
        if unknown:
            raise FreeRefusal("config", f"provider.only names {unknown}, but the live endpoints of {model} are {tags}")
        pin = list(pinned)
    elif tags:
        pin = tags
    else:
        raise FreeRefusal("config", f"the live endpoints of {model} carry no tag to pin; pin one with provider.only")
    served = [r for r in rows if any(_serves(p, r) for p in pin)]
    missing = []
    for key in payload or {}:
        if key in NOT_PARAMS:
            continue
        need = PARAM_NAMES.get(key, key)
        lacking = [r["tag"] for r in served if need not in r["supported_parameters"]]
        if lacking:
            hint = PARAM_HINTS.get(need) or f"pass --drop-params {key}"
            missing.append(f"the run sends {key} but endpoint {', '.join(map(str, lacking))} does not list {need} "
                           f"({hint})")
    if missing:
        raise FreeRefusal("config", "; ".join(missing))

    # ── Reasoning effort: advice only (the endpoint decides) ──
    reasoning = entry.get("reasoning") if isinstance(entry.get("reasoning"), dict) else None
    sent = (payload or {}).get("reasoning")
    effort = sent.get("effort") if isinstance(sent, dict) else None
    if reasoning and effort:
        efforts = reasoning.get("supported_efforts")
        if effort == "none" and reasoning.get("mandatory") is True:
            warnings.append(f"{model} reasons on every call; --reasoning none may be refused")
        elif effort != "none" and isinstance(efforts, list) and efforts and effort not in efforts:
            warnings.append(f"{model} lists reasoning efforts {efforts}, not {effort!r}")
    names = [r["provider_name"] for r in served if r["provider_name"]]
    canonical = entry.get("canonical_slug") if isinstance(entry.get("canonical_slug"), str) else None
    target = {"model": model, "canonical_slug": canonical, "providers": pin + names, "endpoints": served,
              "expiration_date": entry.get("expiration_date"), "reasoning": reasoning}
    return target, pin, warnings


# ── Per-response checks ──────────────────────────────────────────────────────

def no_route(text):
    """Does an error text say that no endpoint may serve the request (see NO_ROUTE_WORDS)?"""
    t = (text or "").lower()
    return any(w in t for w in NO_ROUTE_WORDS)


def paid_signal(data, target, answered):
    """Why a 200 response breaks the zero-spend rule, or None.

    Every response must carry ``usage.cost`` exactly 0 (usage accounting returns what the account was charged
    [UA]) and no BYOK upstream cost; an answered one must also name the requested free model (or its canonical slug
    with ":free") and, when it names a provider, one of the endpoints read at start. An error inside a 200 is
    checked for cost only (it may carry no usage).
    """
    usage = data.get("usage")
    if isinstance(usage, dict):
        cost = usage.get("cost")
        if (cost is not None or answered) and not exact_zero(cost):
            return f"usage.cost is {cost!r}, not 0"
        cd = usage.get("cost_details") if isinstance(usage.get("cost_details"), dict) else {}
        upstream = cd.get("upstream_inference_cost")
        if upstream is not None and not exact_zero(upstream):
            return f"cost_details.upstream_inference_cost is {upstream!r} (billed through a provider key)"
    elif answered:
        return "the response carries no usage, so its cost is unknown"
    if not answered:
        return None
    served = data.get("model")
    allowed = {target["model"]} | ({target["canonical_slug"] + ":free"} if target.get("canonical_slug") else set())
    if served not in allowed:
        return f"the response was served by model {served!r}, not the requested free model {target['model']!r}"
    prov = data.get("provider")
    if isinstance(prov, str) and target.get("providers") and not any(provider_matches(p, prov)
                                                                      for p in target["providers"]):
        return f"the response was served by provider {prov!r}, not a free endpoint read at start ({target['providers']})"
    return None


# ── Start and end of a free-only run ─────────────────────────────────────────

def start_free(args, backend, rows, payload, run_info, clock=time.time, record=None):
    """The start checks of a free-only run, then the gate; runs again on every --resume.

    Returns (None, gate) to go on, or ((kind, message), None) to stop before any model request; ``kind`` is
    ``not_free``, ``config`` or ``quota``. Order: the public catalogue first (the key is not sent), then the key
    record (its rules, then its spend against the ledger's last reading in ``rows``), then the day's allowance. On
    success the backend gets the gate, the zero-spend target and the pin. ``record(key_summary)`` writes a reading to
    the ledger (free_key.key_row); it is called for the start reading and for every poll that found no rise.
    """
    base, timeout = backend.base, min(float(args.timeout), 60.0)
    now = clock()
    # ── 1. Catalogue (public, without the key) ──
    prov = backend.extra_body.get("provider") if isinstance(backend.extra_body.get("provider"), dict) else {}
    pinned = prov.get("only") if isinstance(prov.get("only"), list) and prov.get("only") else None
    try:
        entry = model_entry(get_public_json(base, "/models", timeout), args.model)
        endpoints = get_public_json(base, f"/models/{args.model}/endpoints", timeout)
        target, pin, warnings = check_catalogue(entry, endpoints, args.model, payload, pinned, utc_day(now))
    except FreeRefusal as r:
        return (r.kind, r.message), None
    except Exception as e:  # noqa: BLE001 - an unreadable catalogue means the run cannot be shown to be free
        return ("config", f"the public catalogue could not be read ({type(e).__name__}: "
                          f"{backend.redact(str(e))[:300]})"), None
    # ── 2. Key record (sent with the key; only non-secret fields are kept) ──
    try:
        key = backend.key_info()
    except Exception as e:  # noqa: BLE001 - any failure means the key cannot be shown to be safe
        return ("config", f"key check failed: {backend.redact(str(e))[:300]}"), None
    print(f"key check: {describe_key(key)}", flush=True)
    why = key_refusal(key, args.max_key_headroom_usd, args.allow_key_headroom,
                      _dt.datetime.fromtimestamp(now, _dt.timezone.utc))
    if why:
        return ("config", f"key check: {why}"), None
    if key_headroom(key) > args.max_key_headroom_usd:
        print(f"warning: --allow-key-headroom: the key could spend {key_headroom(key)} USD on paid models; every "
              f"response and the key poll still stop the run on any charge", file=sys.stderr)
    if key.get("byok_usage"):
        print("warning: this key has BYOK usage; remove provider keys from a free-testing account", file=sys.stderr)
    # ── 2b. Spend since the ledger's last reading: a charge no run saw (free reservations are 0, so the ledger's
    #        spent total cannot show it) must not become this run's baseline ──
    since = baseline_rise(rows, key)
    if since:
        return ("not_free", f"{since}: something was billed that no run saw (a call whose charge its response did not "
                            f"show, a run stopped or killed before its final key check, or other use of this key); "
                            f"check the account's Activity page and revoke the key if the charge is not yours, then use "
                            f"a new key with a credit limit of 0 and a new --ledger"), None
    if record is not None:
        record(key)

    # ── 3. Gate: minute window, day allowance, key poll (rate_gate.py) ──
    start_key = dict(key)

    def poll():
        try:
            now_key = backend.key_info()
        except Exception as e:  # noqa: BLE001 - fail closed: without the poll a charge could go unseen
            return ("config", f"the key poll failed ({backend.redact(str(e))[:200]}); resume with --resume"), None
        rise = usage_rise(start_key, now_key)
        if rise:
            return ("not_free", f"{rise} during the run: something was billed; the run stopped (check the "
                                f"account's activity page before any further run)"), None
        if record is not None:
            record(now_key)  # the ledger's newest known-good reading, the next start's baseline
        return None, now_key.get("free_model_daily_requests")

    gate = RateGate(rpm=args.rpm, per_day=args.max_requests_per_day, reserve=args.daily_reserve, rows=rows,
                    server=key["free_model_daily_requests"], poll=poll, poll_every=args.key_poll_every,
                    max_429=args.max_consecutive_429, clock=clock)
    backend.gate, backend.free_target = gate, target
    backend.extra_body = dict(backend.extra_body, provider=dict(prov, only=pin, require_parameters=True,
                                                                allow_fallbacks=False))
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    ep = target["endpoints"][0] if target["endpoints"] else {}
    run_info.update({
        "free_only": True, "canonical_slug": target["canonical_slug"], "endpoint_tag": run_info.get("endpoint_tag")
        or (pin[0] if len(pin) == 1 else None), "provider_pin": pin, "endpoint_name": ep.get("name"),
        "quant": run_info.get("quant") or ep.get("quantization"), "endpoint_params": ep.get("supported_parameters"),
        "expiration_date": target["expiration_date"], "catalogue_read": utc_day(now).isoformat(),
        "key_start": {k: v for k, v in key.items() if k != "free_model_daily_requests"},
        "free_daily_start": key["free_model_daily_requests"], "rpm_cap": args.rpm,
        "day_cap": args.max_requests_per_day, "daily_reserve": args.daily_reserve})
    left = gate.remaining_today()
    print(f"free-only: {args.model} (canonical {target['canonical_slug']}) pinned to {pin}; every price is 0; "
          f"{gate.used_local} attempts in this ledger today; {left} requests allowed today; at most {args.rpm} per "
          f"minute", flush=True)
    if left is not None and left <= 0:
        return ("quota", gate.quota_message()), None
    return None, gate


def final_check(gate):
    """After the last call: one more key poll. Returns (stop or None, a console line)."""
    stop = gate.sync() if gate.poll is not None else None
    fm = gate.server or {}
    line = (f"key check at the end: usage unchanged; free requests today: {fm.get('used')} used of {fm.get('limit')} "
            f"({gate.used_local} attempts in this ledger)") if stop is None else f"key check at the end: {stop[1]}"
    return stop, line
