#!/usr/bin/env python3
"""``run.py --key-status --provider groq|cloudflare``: check a stored key or token without running a model
(tools/local-qual).

What it owns
------------
* ``run``: the whole command. It refuses what cannot be sent safely (exit 2, nothing sent: a key on the command line,
  --dry-run, no key variable, a key of the wrong shape, Cloudflare's Global API Key, a missing or malformed account
  id, a base URL that is neither the provider's nor on this machine), reads the provider's cheapest record with the
  key, prints the report and exits 0, or prints one line that names the next step. It sends no chat request, writes no
  ledger, record or other file and takes no lock.
* Groq: one ``GET <base>/models`` (no model runs and no tokens are used; whether Groq counts it as a request is not
  documented). The report: the key accepted, each model of the free-plan table listed or not (active, context window,
  output cap), the ``x-ratelimit-*`` headers of the reply, and whether they show the Free plan (limits above it name
  the exit 9 a run would take).
* Cloudflare: ``GET <root>/accounts/<id>/tokens/verify`` for an account token (cfat_), ``GET <root>/user/tokens/verify``
  for a user token (cfut_), then one ``GET <root>/accounts/<id>/ai/models/search?search=<name>`` per model of the
  neuron table (Workers AI Read is enough; no model runs, so no neurons are used; each counts toward Cloudflare's
  general limit of 1,200 API requests per five minutes). The report: the token's status and expiry, the account
  reachable, each table model listed or not, and the day's neuron allocation. The account id is never printed.

How it fits
-----------
run.main calls ``run`` instead of key_status.run (OpenRouter's GET /key) when ``--provider`` names Groq or Cloudflare.
The failure lines, the body display and the exit codes are key_status.py's: 0 the report printed; 2 refused before
sending; 3 no answer or HTTP 5xx; 5 the key, the token, its permission, the account id or the base URL is wrong (401,
403, 404, a redirect, a body that is not the record); 10 HTTP 429. Standard library only.

Sources (read 2026-09-28)
-------------------------
https://console.groq.com/docs/api-reference (GET /openai/v1/models: id, active, context_window, max_completion_tokens);
https://console.groq.com/docs/rate-limits (the headers); https://developers.cloudflare.com/api/resources/accounts/
subresources/tokens/methods/verify/ and /api/resources/user/subresources/tokens/methods/verify/ (result: id, status
active, disabled or expired, expires_on, not_before); /api/resources/ai/subresources/models/methods/list/ (the model
search, Workers AI Read or Write); /fundamentals/api/reference/limits/ (1,200 requests per five minutes).
"""
import os
import re
import sys
import time
import urllib.parse

import providers
from cloud_guard import MAX_BODY_BYTES, redirect_host
from cloud_reply import json_or_none
from key_status import EXIT_UNREACHABLE, printable, scrub, shown_body
from cloud_run import EXIT_CONFIG, EXIT_QUOTA
from provider_backend import ProviderBackend
from provider_gate import header_int
from rate_gate import next_utc_midnight

# The flags this command reads; any other flag set on the command line is named once as skipped.
USED_FLAGS = frozenset(("key_status", "provider", "backend", "base_url", "api_key_env", "account_id_env", "timeout",
                        "model", "max_neurons_per_day"))
# The headers of a Groq reply the report shows, and the values it shows as written (anything else is unreadable).
SHOWN_HEADERS = ("x-ratelimit-limit-requests", "x-ratelimit-remaining-requests", "x-ratelimit-reset-requests",
                 "x-ratelimit-limit-tokens", "x-ratelimit-remaining-tokens", "x-ratelimit-reset-tokens", "retry-after")
_HEADER_VALUE = re.compile(r"[0-9A-Za-z.:]{1,24}")
# A token's status and expiry are shown only when they look like one ("active"; an ISO time).
_STATUS = re.compile(r"[a-z_]{1,20}")
_WHEN = re.compile(r"[0-9T:.+\-Z ]{1,40}")


def ignored_flags(ap, args):
    """The flags this command line sets (to other than their defaults) that the command does not use, as --names."""
    defaults = vars(ap.parse_args([]))
    return ["--" + dest.replace("_", "-") for dest, value in vars(args).items()
            if dest not in USED_FLAGS and dest in defaults and value != defaults[dest]]


def failure(p, what, status, headers, data, raw, exc, redact, record):
    """(exit code, one line naming the next step) for a read that brought no usable record, with the body shown
    scrubbed (key_status.shown_body: the key, every key shape, the account id; one printable line, cut last)."""
    title = providers.PRESETS[p]["title"]
    cf = p == "cloudflare"
    thing = "token" if cf else "key"
    if status is None:
        why = printable(redact(f"{type(exc).__name__}: {exc}"))[:200]
        return EXIT_UNREACHABLE, (f"key status: {what} could not reach {title} ({why}); check the network connection "
                                  f"and --base-url, then try again")
    if status == 200:
        body = (f"a body over {MAX_BODY_BYTES} bytes" if exc is not None else
                "a body that is not JSON" if data is None else "another JSON body")
        line = (f"{what} answered HTTP 200 with {body}, not {record}; check --base-url: it must be {title}'s API base "
                f"({providers.PRESETS[p]['base']}), not a web page")
        code = EXIT_CONFIG
    elif status == 401:
        code, line = EXIT_CONFIG, (f"HTTP 401: {title} does not accept this {thing} (revoked, expired, deleted or "
                                   f"mistyped); create a new one ({providers.PRESETS[p]['keys_page']}) and store it with "
                                   f"cloud/set-provider-key.ps1 -Provider {p} -Force")
    elif status == 403:
        code, line = EXIT_CONFIG, (
            "HTTP 403: the token may not do this on this account: it needs Account > Workers AI > Read, and the account "
            "id must be the token's own; store both again with cloud/set-provider-key.ps1 -Provider cloudflare -Force"
            if cf else "HTTP 403: the key may not list models (a project or organisation restriction); check it at "
                       "https://console.groq.com/keys")
    elif status == 404:
        code, line = EXIT_CONFIG, (
            "HTTP 404: check the account id (store it again with cloud/set-provider-key.ps1 -Provider cloudflare "
            "-Force) and --base-url" if cf else
            f"HTTP 404: {what} does not exist there; check --base-url ({providers.PRESETS[p]['base']})")
    elif status == 429:
        code, line = EXIT_QUOTA, (f"HTTP 429: too many requests just now; wait a minute, stop any other run on this "
                                  f"{'account' if cf else 'organisation'}, and run --key-status again")
    elif isinstance(status, int) and 300 <= status <= 399:
        target = scrub(redirect_host(headers), [], redact)[:200]
        code, line = EXIT_CONFIG, (f"HTTP {status}: the endpoint redirects (to host {target!r}); redirects are never "
                                   f"followed so the {thing} is never forwarded; pass the final URL as --base-url")
    elif isinstance(status, int) and 500 <= status <= 599:
        code, line = EXIT_UNREACHABLE, f"HTTP {status}: {title} failed or is overloaded; try again in a few minutes"
    else:
        code, line = EXIT_CONFIG, f"HTTP {status}: {title} refused {what}; check --base-url and the {thing}"
    shown = shown_body(raw, data, redact)
    return code, "key status: " + line + (f" (response: {shown})" if shown else "")


def _header_value(headers, name):
    value = (headers or {}).get(name)
    if value is None:
        return None
    return value if isinstance(value, str) and _HEADER_VALUE.fullmatch(value) else "(unreadable)"


def _count(value):
    return str(value) if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else "?"


def groq_report(backend, table, root, env, model):
    """GET /models once; (exit code, lines for stdout or one line for stderr)."""
    status, headers, raw, exc = backend.get(root + "/models")
    data = json_or_none(raw)
    if not (status == 200 and exc is None and isinstance(data, dict) and isinstance(data.get("data"), list)):
        code, line = failure("groq", "GET /models", status, headers, data, raw, exc, backend.redact, "a model list")
        return code, [line]
    listed = {m["id"]: m for m in data["data"] if isinstance(m, dict) and isinstance(m.get("id"), str)}
    lines = [f"key status: the key in {printable(env)} at {printable(urllib.parse.urlsplit(root).hostname or '')} "
             f"(one GET /models: no model runs and no tokens are used; whether Groq counts it as a request is not "
             f"documented)",
             "  key: accepted (HTTP 200)",
             f"  models of the free-plan table (cloud/{providers.PRESETS['groq']['table']}, read {table['read']}):"]
    names = list(table["models"]) + ([model] if model and model not in table["models"] else [])
    for name in names:
        m = listed.get(name)
        row = table["models"].get(name)
        if m is None:
            text = "not listed"
        else:
            text = (f"listed, {'active' if m.get('active') is True else 'not active'}, context "
                    f"{_count(m.get('context_window'))}, max completion {_count(m.get('max_completion_tokens'))}")
        if row is None:
            text += "; not in the free-plan table, so a run refuses it"
        elif row.get("status") == "preview":
            text += "; a preview model (Groq may remove it at short notice)"
        lines.append(f"    {name}: {text}")
    shown = [f"{h} {_header_value(headers, h)}" for h in SHOWN_HEADERS if _header_value(headers, h) is not None]
    lines.append("  rate-limit headers on this reply: " + (", ".join(shown) if shown else "none"))
    rpd = max(r["rpd"] for r in table["models"].values())
    tpm = max(r["tpm"] for r in table["models"].values())
    lim_req = header_int((headers or {}).get("x-ratelimit-limit-requests"))
    lim_tok = header_int((headers or {}).get("x-ratelimit-limit-tokens"))
    if lim_req is None and lim_tok is None:
        verdict = ("not shown: the reply carried no rate-limit headers; a run reads them on every reply and stops "
                   "(exit 9) at limits higher than the plan's")
    elif (lim_req is not None and lim_req > rpd) or (lim_tok is not None and lim_tok > tpm):
        verdict = (f"above the Free plan ({lim_req} requests a day, {lim_tok} tokens a minute; the plan's are {rpd} and "
                   f"{tpm}): the organisation may be on a paid tier, where requests are billed; a run would stop at its "
                   f"first reply (exit 9)")
    else:
        verdict = f"the limits are within the Free plan ({lim_req} requests a day, {lim_tok} tokens a minute)"
    lines.append(f"  free plan: {verdict}")
    g = next(iter(table["models"].values()))
    lines.append(f"  limits per model and organisation: {g['rpm']} requests a minute, {g['rpd']:,} a day, {g['tpm']:,} "
                 f"tokens a minute, {g['tpd']:,} a day; a run keeps below them (--rpm, --max-requests-per-day, "
                 f"--max-tokens-per-minute, --max-tokens-per-day; see cloud/README.md)")
    return 0, lines


def cloudflare_report(backend, table, root, env, account_env, account, key, cap):
    """Token verify, then one model search per table model; (exit code, lines)."""
    account_token = key.startswith("cfat_")
    url = f"{root}/accounts/{account}/tokens/verify" if account_token else f"{root}/user/tokens/verify"
    status, headers, raw, exc = backend.get(url)
    data = json_or_none(raw)
    res = data.get("result") if isinstance(data, dict) else None
    if not (status == 200 and exc is None and isinstance(data, dict) and data.get("success") is True
            and isinstance(res, dict)):
        code, line = failure("cloudflare", "GET tokens/verify", status, headers, data, raw, exc, backend.redact,
                             "a token record")
        return code, [line]
    state = res.get("status") if isinstance(res.get("status"), str) and _STATUS.fullmatch(res["status"]) else None
    expires = res.get("expires_on") if isinstance(res.get("expires_on"), str) and _WHEN.fullmatch(res["expires_on"]) \
        else None
    if state != "active":
        return EXIT_CONFIG, [f"key status: the token is {state or 'not reported as active'} (Cloudflare's token verify); "
                             f"create a new token ({providers.PRESETS['cloudflare']['keys_page']}) and store it with "
                             f"cloud/set-provider-key.ps1 -Provider cloudflare -Force"]
    found = []
    for model in table["models"]:
        query = urllib.parse.urlencode({"search": model.rsplit("/", 1)[-1]})
        status, headers, raw, exc = backend.get(f"{root}/accounts/{account}/ai/models/search?{query}")
        data = json_or_none(raw)
        if not (status == 200 and exc is None and isinstance(data, dict) and isinstance(data.get("result"), list)):
            code, line = failure("cloudflare", "GET ai/models/search", status, headers, data, raw, exc,
                                 backend.redact, "a model list")
            return code, [line]
        names = {r.get("name") for r in data["result"] if isinstance(r, dict)}
        found.append((model, model in names))
    kind = "account token (cfat_)" if account_token else "user token (cfut_)"
    free = table["free_neurons_per_day"]
    lines = [f"key status: the token in {printable(env)} for the account in {printable(account_env)} at "
             f"{printable(urllib.parse.urlsplit(root).hostname or '')} (token verify and a model search: no model "
             f"runs, no neurons used)",
             f"  token: active, {kind}, expires {expires or 'never'}",
             "  account: reachable; the token may search its Workers AI models",
             f"  models of the neuron table (cloud/{providers.PRESETS['cloudflare']['table']}, read {table['read']}):"]
    for model, listed in found:
        rates = table["models"][model]
        lines.append(f"    {model}: {'listed' if listed else 'not listed'}; {rates['in']:g} / {rates['out']:g} neurons "
                     f"per million tokens in / out")
    lines.append(f"  free allocation: {free:,.0f} neurons a day, reset at 00:00 UTC (next: "
                 f"{next_utc_midnight(time.time())}); a run keeps at most {cap:,.0f} (--max-neurons-per-day)")
    lines.append("  runs: the token and the account check out; keep the account on Workers Free (cloud/README.md): "
                 "on Workers Paid every neuron past the allocation is billed")
    return 0, lines


def run(ap, args):
    """``run.py --key-status --provider groq|cloudflare`` (see the module docs); returns the exit code."""
    p = providers.active(args)
    pre = providers.PRESETS[p]
    # ── Refusals: nothing has been sent yet ──
    if args.api_key is not None:
        ap.error("--key-status never takes a key on the command line; put it in an environment variable (cloud/run-cloud.ps1 "
                 "does)")
    if args.dry_run:
        ap.error("--key-status sends a read and --dry-run sends nothing; pass one of them")
    env = args.api_key_env or pre["key_env"]
    account_env = args.account_id_env or providers.ACCOUNT_ENV
    try:
        if p == "groq" and args.account_id_env:
            raise ValueError("--account-id-env applies to --provider cloudflare")
        root = providers.resolve_root(p, args.base_url)
        table = providers.load_table(p)
        cap = table["free_neurons_per_day"] * providers.CF_NEURON_SHARE if p == "cloudflare" else None
        if p == "cloudflare" and args.max_neurons_per_day is not None:
            cap = args.max_neurons_per_day
        account = providers.read_account_id(account_env) if p == "cloudflare" else None
    except ValueError as e:
        ap.error(str(e))
    key = os.environ.pop(env, None) or ""
    if not key.strip():
        ap.error(f"the environment variable {env} is not set or empty")
    why = providers.key_refusal(p, key)
    if why:
        ap.error(why)
    key = key.strip()
    base = root if p == "groq" else f"{root}/accounts/{account}/ai/v1"
    try:
        backend = ProviderBackend(base, args.timeout, key, provider={"provider": p, "model": args.model,
                                                                     "account_id": account, "api_root": root})
    except ValueError as e:
        ap.error(str(e))
    skipped = ignored_flags(ap, args)
    if skipped:
        print(f"note: --key-status only reads; skipped: {', '.join(skipped)}", file=sys.stderr, flush=True)
    # ── The reads ──
    if p == "groq":
        code, lines = groq_report(backend, table, root, env, args.model)
    else:
        code, lines = cloudflare_report(backend, table, root, env, account_env, account, key, cap)
    for line in lines:
        print(backend.redact(line), file=sys.stdout if code == 0 else sys.stderr, flush=True)
    return code
