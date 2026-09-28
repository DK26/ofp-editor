#!/usr/bin/env python3
"""Groq and Cloudflare Workers AI as zero-spend providers of the ``openai`` backend (``--provider``) (tools/local-qual).

What it owns
------------
* ``PRESETS``: per provider, the API base, the key variable, the key shape, whether its terms carry a violent-content
  clause (D047), and its dated data file: cloud/groq-free-limits.json (the free plan's limits per model) and
  cloud/cloudflare-neurons.json (each model's neuron rates and the daily free allocation). ``load_table`` reads and
  checks them.
* ``add_provider_args``: ``--provider``, ``--account-id-env``, ``--max-tokens-per-minute``, ``--max-tokens-per-day``
  and ``--max-neurons-per-day``. The request caps reuse free mode's ``--rpm``, ``--max-requests-per-day``,
  ``--daily-reserve`` and ``--max-consecutive-429`` with this provider's defaults.
* ``prepare`` (run.py, before any other check): ``--provider`` implies the openai backend, and D047 keeps the text and
  knowledge suites away from both hosts.
* ``apply_provider_flags`` (cloud_run.make_backend): every offline check of a provider run, and the values it sets: the
  base URL (the preset's, or a loopback test server; Cloudflare's carries the account id read from its variable), the
  key variable, a USD cap and prices of 0 (budget.py's zero-spend mode), the caps, the reasoning field the model takes,
  and Groq's max_completion_tokens and strict-mode schema copy. Nothing is sent; every refusal names the fix.
* ``start_provider`` (cloud_run.Session.start, on every start and resume): the gate (provider_gate.py) built from the
  ledger's quota rows, its record fields and start line, and a stop when the day's allowance is already used.
* ``key_refusal``, ``read_account_id``, ``resolve_root``, ``reasoning_wire``, ``schema_refusal`` and the per-user lock
  names, shared with provider_backend.py and provider_status.py (``--key-status``).

How it fits
-----------
``--provider openrouter`` (or no flag) leaves every OpenRouter path exactly as it was: ``active`` returns None and
nothing here runs. For Groq and Cloudflare the run is always held to the provider's free tier: there is no paid path.
The key reaches run.py only through an environment variable (cloud/run-cloud.ps1 decrypts it from the DPAPI store into
that one process); the Cloudflare account id likewise, since it identifies the owner's account and must stay out of
command lines, records and this public repository. Standard library only.

Sources (read 2026-09-28)
-------------------------
Groq: https://console.groq.com/docs/openai (base https://api.groq.com/openai/v1; logprobs, logit_bias, top_logprobs and
messages[].name return 400; n must be 1), /docs/reasoning (gpt-oss: reasoning_effort low, medium, high; Qwen3.8:
none, default, low, medium, high, and reasoning_format, whose raw value is refused in JSON mode), /docs/structured-
outputs (strict mode: every property required, additionalProperties false; gpt-oss-safeguard-20b best-effort only),
/docs/rate-limits (the table's figures). Cloudflare: https://developers.cloudflare.com/workers-ai/configuration/
open-ai-compatibility/ (base <root>/accounts/<account id>/ai/v1, bearer token), /workers-ai/platform/pricing/ (the
neuron table), /fundamentals/api/get-started/token-formats/ (cfat_, cfut_, cfk_). D047 item 3 and doc 50 section 5.9
for the suites kept away from hosts with a violent-content clause.
"""
import json
import math
import os
import re
import sys
import time
import urllib.parse

import provider_gate
from budget import Budget
from cloud_guard import is_loopback

HERE = os.path.dirname(os.path.abspath(__file__))
CLOUD_DIR = os.path.join(HERE, "cloud")

# ── Presets ──────────────────────────────────────────────────────────────────

PROVIDERS = ("openrouter", "groq", "cloudflare")
# The providers this module runs; "openrouter" (and no --provider) keeps the OpenRouter paths unchanged.
ACTIVE = ("groq", "cloudflare")
PRESETS = {
    "groq": {"title": "Groq", "base": "https://api.groq.com/openai/v1", "key_env": "GROQ_API_KEY",
             # gsk_ plus 32 to 80 letters and digits, the range cloud/set-groq-key.ps1 stores: secret scanners use gsk_
             # and 52 characters, and a proposal 48; Groq's own documentation states no format, so the range is wider.
             "key_shape": re.compile(r"gsk_[A-Za-z0-9]{32,80}"), "key_hint": "gsk_ followed by letters and digits",
             "table": "groq-free-limits.json", "table_name": "free-plan table", "scope": "model and organisation",
             "violent_content_clause": True, "keys_page": "https://console.groq.com/keys"},
    "cloudflare": {"title": "Cloudflare Workers AI", "base": "https://api.cloudflare.com/client/v4",
                   "key_env": "CLOUDFLARE_API_TOKEN",
                   # Account tokens cfat_ and user tokens cfut_: 40 characters and a checksum (the shape
                   # cloud/set-cloudflare-token.ps1 stores). The Global API Key (cfk_) and legacy tokens without a
                   # prefix are refused (key_refusal).
                   "key_shape": re.compile(r"cf(?:at|ut)_[A-Za-z0-9_-]{40,}"),
                   "key_hint": "an account token cfat_... or a user token cfut_...",
                   "table": "cloudflare-neurons.json", "table_name": "neuron table", "scope": "account",
                   "violent_content_clause": True,
                   "keys_page": "Manage account > Account API tokens in the Cloudflare dashboard"},
}
# The Cloudflare account id: 32 hexadecimal characters (stored lower case; the ids Cloudflare shows are lower case).
ACCOUNT_ENV = "CLOUDFLARE_ACCOUNT_ID"
ACCOUNT_ID = re.compile(r"[0-9a-fA-F]{32}")
# The account id a dry run builds its URL with when the variable is not set: a dry run sends nothing.
DRY_RUN_ACCOUNT = "0" * 32
# Suites D047 item 3 keeps away from hosts whose terms carry a violent-content clause, until items carry their own
# flag: doc 50 section 5.9 reads the text and knowledge suites as combat-flavoured (a cautious reading).
COMBAT_SHAPES = ("text", "knowledge")
# Sampler pins a provider does not document: sent anyway they may be refused (400) or silently ignored while the record
# says they were pinned. Groq documents neither top_k, min_p nor repeat_penalty; Cloudflare's OpenAI-compatible
# endpoint documents neither min_p nor repeat_penalty (its models name it repetition_penalty).
UNSUPPORTED_SAMPLERS = {"groq": ("top_k", "min_p", "repeat_penalty"), "cloudflare": ("min_p", "repeat_penalty")}
# Cloudflare's text-generation limit: 300 requests a minute (limits page, 2026-09-17); the client default stays far
# below it, since whether it counts per account or per model is not documented.
CF_RPM_LIMIT = 300
CF_RPM_DEFAULT = 60
# The share of the daily free allocation a run may count by default: the table's figures are our computation, and the
# account may carry other use, so 10% stays unused.
CF_NEURON_SHARE = 0.9
# Groq's defaults, as shares of the free plan's per-model limits: 28 of 30 a minute, 950 of 1,000 a day, 7,500 of
# 8,000 tokens a minute, 190,000 of 200,000 tokens a day (the organisation may carry other use).
GROQ_RPM_MARGIN = 2
GROQ_DAY_SHARE = 0.95
GROQ_TPM_SHARE = 0.9375
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def active(args):
    """The provider this run uses (groq or cloudflare), or None for OpenRouter and every other path."""
    p = getattr(args, "provider", None)
    return p if p in ACTIVE else None


def lock_name(provider):
    """The per-user lock's name (cloud_run.Session takes it as <free_lock_dir>/<name>.lock)."""
    return f"{provider}-run"


def lock_shown(provider):
    """How messages name the lock file: by the variable, never as an expanded path (that would carry the user name)."""
    if os.name == "nt":
        return rf"%LOCALAPPDATA%\plotroom-dev\{lock_name(provider)}.lock"
    return f"$XDG_STATE_HOME/plotroom-dev/{lock_name(provider)}.lock (default ~/.local/state/plotroom-dev)"


def lock_message(name, held):
    """The refusal when another run holds a provider's lock `name`, or None when `name` is not one."""
    for p in ACTIVE:
        if name == lock_name(p):
            pre = PRESETS[p]
            return (f"another --provider {p} run is active for this user ({held or 'no details'}): {pre['title']}'s "
                    f"free limits count per {pre['scope']}, so its runs go one at a time; if no other run is active, "
                    f"delete {lock_shown(p)} and start again")
    return None


# ── Command line ─────────────────────────────────────────────────────────────

def add_provider_args(ap):
    """The provider flags (see cloud/README.md for the owner's runbook)."""
    g = ap.add_argument_group("Groq and Cloudflare Workers AI (--provider; free tiers only, zero spend)")
    g.add_argument("--provider", default=None, choices=PROVIDERS,
                   help="groq or cloudflare: run on that provider's free tier (implies --backend openai; the base URL, "
                        "the key variable and the caps come from its preset; nothing can be spent, and the request "
                        "and token caps, or the neuron budget, are kept per day in the shared --ledger); openrouter "
                        "(the default) changes nothing")
    g.add_argument("--account-id-env", default=None,
                   help=f"cloudflare: the environment variable that holds the account id (default {ACCOUNT_ENV}; "
                        f"cloud/run-cloud.ps1 sets it); the id goes into the URL and is kept out of every record")
    g.add_argument("--max-tokens-per-minute", type=int, default=None,
                   help="groq: most tokens in any 60 s per model (default 7,500 of the free plan's 8,000)")
    g.add_argument("--max-tokens-per-day", type=int, default=None,
                   help="groq: most tokens in any 24 hours per model (default 190,000 of the free plan's 200,000)")
    g.add_argument("--max-neurons-per-day", type=float, default=None,
                   help="cloudflare: most neurons per UTC day for the account, computed from usage and "
                        "cloud/cloudflare-neurons.json (default 9,000 of the free allocation's 10,000)")


def suite_refusal(provider, shape):
    """Why a suite of this shape may not go to `provider` (D047 item 3), or None."""
    if provider in ACTIVE and PRESETS[provider]["violent_content_clause"] and shape in COMBAT_SHAPES:
        return (f"--provider {provider}: the {shape} suite is not sent to {PRESETS[provider]['title']}: D047 item 3 keeps "
                f"combat-flavoured items away from hosts whose terms carry a violent-content clause, and until items "
                f"carry their own flag the text and knowledge suites count as combat-flavoured (doc 50 section 5.9); "
                f"run pick, pick-hard, fill or explain")
    return None


def prepare(ap, args, shape):
    """run.py, before any other check: --provider implies the openai backend; D047's suite rule (``ap.error``)."""
    p = active(args)
    if not p:
        return
    if args.backend == "llamacpp":
        ap.error(f"--provider {p} runs through the openai backend; drop --backend llamacpp")
    args.backend = "openai"
    why = suite_refusal(p, shape)
    if why:
        ap.error(why)


# ── Tables, keys, URLs ───────────────────────────────────────────────────────

def _positive(value, where, integer=False):
    """`value` when it is a finite number above 0 (a whole number when `integer`), else ValueError naming `where`."""
    ok = not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value > 0
    if not ok or (integer and not isinstance(value, int)):
        raise ValueError(f"{where} must be a {'whole ' if integer else ''}number above 0, got {json.dumps(value)}")
    return value


def load_table(provider, path=None):
    """The provider's dated data file, checked; ValueError names the file and the field that is wrong.

    Why so strict: the table decides every cap and every neuron count; a missing rate would price a call at 0 and a
    missing source or date would make a figure impossible to re-check.
    """
    path = path or os.path.join(CLOUD_DIR, PRESETS[provider]["table"])
    where = os.path.basename(path)
    try:
        with open(path, encoding="utf-8") as f:
            table = json.load(f)
    except (OSError, ValueError) as e:
        raise ValueError(f"{where} is not readable JSON ({type(e).__name__})") from None
    if not isinstance(table, dict) or table.get("provider") != provider:
        raise ValueError(f"{where}: 'provider' must be {provider!r}")
    if not (isinstance(table.get("source"), str) and table["source"].startswith("https://")):
        raise ValueError(f"{where}: 'source' must be the https URL the figures were read from")
    if not (isinstance(table.get("read"), str) and _DATE.fullmatch(table["read"])):
        raise ValueError(f"{where}: 'read' must be the date the figures were read (YYYY-MM-DD)")
    models = table.get("models")
    if not isinstance(models, dict) or not models:
        raise ValueError(f"{where}: 'models' must be a non-empty object of model id -> figures")
    for model, row in models.items():
        if not isinstance(row, dict):
            raise ValueError(f"{where}: models[{model!r}] must be an object")
        for field in (("rpm", "rpd", "tpm", "tpd") if provider == "groq" else ("in", "out")):
            _positive(row.get(field), f"{where}: models[{model!r}].{field}", integer=provider == "groq")
        efforts = row.get("reasoning_efforts")
        if efforts is not None and not (isinstance(efforts, list) and all(isinstance(e, str) for e in efforts)):
            raise ValueError(f"{where}: models[{model!r}].reasoning_efforts must be null or a list of words")
    if provider == "cloudflare":
        _positive(table.get("free_neurons_per_day"), f"{where}: free_neurons_per_day")
    return table


def key_refusal(provider, key):
    """Why `key` may not be sent to `provider`, or None. The message never contains the key.

    Why: a key of another provider (an OpenRouter key in the Groq slot) would reach the wrong host, and a key without a
    known prefix cannot be found again by the shape-based redaction. Cloudflare's Global API Key (cfk_) has full access
    to the whole account; a least-privilege token needs only Workers AI Read.
    """
    k = (key or "").strip()
    pre = PRESETS[provider]
    if provider == "cloudflare" and k.startswith("cfk_"):
        return ("this is Cloudflare's Global API Key (cfk_), which has full access to the account: create an account "
                "token with only Account > Workers AI > Read and store it with cloud/set-provider-key.ps1 -Provider "
                "cloudflare -Force")
    if not pre["key_shape"].fullmatch(k):
        return (f"the key in the variable does not look like a {pre['title']} key ({pre['key_hint']}); store the right "
                f"one with cloud/set-provider-key.ps1 -Provider {provider} -Force")
    return None


def read_account_id(name, needed=True):
    """The Cloudflare account id from the environment variable `name` (lower case), removed from this process's
    environment like the key; None when it is absent and not `needed`. ValueError never holds the value."""
    value = (os.environ.pop(name, None) or "").strip()
    if not value:
        if needed:
            raise ValueError(f"the environment variable {name} is not set or empty: it holds the Cloudflare account id "
                             f"(cloud/run-cloud.ps1 sets it from the file cloud/set-provider-key.ps1 -Provider "
                             f"cloudflare wrote)")
        return None
    if not ACCOUNT_ID.fullmatch(value):
        raise ValueError(f"{name} does not hold a Cloudflare account id (32 hexadecimal characters, from Account home "
                         f"> Copy account ID); store it again with cloud/set-provider-key.ps1 -Provider cloudflare "
                         f"-Force")
    return value.lower()


def resolve_root(provider, base_url):
    """The API root to use: the preset's, or --base-url when it is exactly that or a server on this machine (tests).

    Why: the key must never reach another host because a flag was mistyped or copied from another run.
    """
    pre = PRESETS[provider]
    if not base_url:
        return pre["base"]
    raw = base_url.strip().rstrip("/")
    try:
        host = urllib.parse.urlsplit(raw).hostname or ""
    except ValueError:
        host = ""
    if raw == pre["base"] or is_loopback(host):
        return raw
    raise ValueError(f"--provider {provider} sends its key only to {pre['base']}: leave --base-url out (a server on "
                     f"this machine is the only other base it accepts, for tests)")


def reasoning_wire(provider, model, entry, reasoning):
    """The body fields that carry --reasoning for this provider and model; ValueError when the model cannot take it.

    ``reasoning`` is cloud_flags.parse_reasoning's value: None for ``omit`` (nothing sent) or {"effort": word}. Groq
    and Cloudflare take ``reasoning_effort`` (OpenAI's name), not OpenRouter's ``reasoning`` object; Groq's Qwen3.8
    also gets ``reasoning_format: parsed``, since ``raw`` is refused in JSON mode and ``parsed`` keeps the thinking out
    of the answer. A model whose row lists no efforts has no setting: only ``none`` (sent as nothing, and a reply that
    reasons anyway still stops the run as ReasoningLeak) or ``omit``.
    """
    title = PRESETS[provider]["title"]
    if reasoning is None:
        return {}
    if not isinstance(reasoning, dict) or set(reasoning) != {"effort"} or not isinstance(reasoning["effort"], str):
        raise ValueError(f"--provider {provider} takes --reasoning as an effort word or omit, not a JSON object (that "
                         f"is OpenRouter's reasoning field)")
    effort = reasoning["effort"]
    efforts = entry.get("reasoning_efforts")
    if not efforts:
        if effort == "none":
            return {}
        raise ValueError(f"{model} has no reasoning setting on {title} (the table lists none): pass --reasoning none "
                         f"or omit")
    if effort not in efforts:
        hint = (f"; it always reasons: pass --reasoning {efforts[0]} and a larger --num-predict" if effort == "none"
                else "")
        raise ValueError(f"{model} on {title} takes --reasoning {', '.join(efforts)} or omit, not {effort}{hint}")
    wire = {"reasoning_effort": effort}
    if entry.get("reasoning_format") and effort != "none":
        wire["reasoning_format"] = entry["reasoning_format"]
    return wire


def schema_refusal(settings, schema_sent):
    """Why this run's strict schema cannot go to the model, or None (run.py, beside OpenRouter's routing refusal)."""
    if not settings or not schema_sent:
        return None
    if settings["provider"] == "groq" and settings["entry"].get("strict_schema") is False:
        return (f"{settings['model']} takes best-effort JSON only on Groq, not a strict schema (Groq's structured-"
                f"outputs page): run its arms with --schema-mode none")
    return None


# ── The run's flags (offline) ────────────────────────────────────────────────

def _cap(value, default, limit, flag, provider, what):
    """A whole-number cap from a flag, between 1 and the provider's `limit` (`default` when the flag is not set)."""
    v = default if value is None else value
    if isinstance(v, bool) or not isinstance(v, int) or not 1 <= v <= limit:
        raise ValueError(f"{flag} must be 1-{limit} for --provider {provider} ({what})")
    return v


def _caps(p, args, entry, table):
    """The run's caps: Groq's per model (requests and tokens a minute and a day), Cloudflare's per account."""
    if args.daily_reserve < 0 or args.max_consecutive_429 < 1:
        raise ValueError("--daily-reserve must be >= 0 and --max-consecutive-429 >= 1")
    if p == "groq":
        lim = {k: entry[k] for k in ("rpm", "rpd", "tpm", "tpd")}
        return {"rpm": _cap(args.rpm, max(1, lim["rpm"] - GROQ_RPM_MARGIN), lim["rpm"], "--rpm", p,
                            "the free plan's requests a minute"),
                "rpd": _cap(args.max_requests_per_day, max(1, int(lim["rpd"] * GROQ_DAY_SHARE)), lim["rpd"],
                            "--max-requests-per-day", p, "the free plan's requests a day"),
                "tpm": _cap(args.max_tokens_per_minute, max(1, int(lim["tpm"] * GROQ_TPM_SHARE)), lim["tpm"],
                            "--max-tokens-per-minute", p, "the free plan's tokens a minute"),
                "tpd": _cap(args.max_tokens_per_day, max(1, int(lim["tpd"] * GROQ_DAY_SHARE)), lim["tpd"],
                            "--max-tokens-per-day", p, "the free plan's tokens a day"),
                "reserve": args.daily_reserve, "max_429": args.max_consecutive_429}
    free = table["free_neurons_per_day"]
    neurons = free * CF_NEURON_SHARE if args.max_neurons_per_day is None else args.max_neurons_per_day
    if isinstance(neurons, bool) or not isinstance(neurons, (int, float)) or not math.isfinite(neurons) \
            or not 0 < neurons <= free:
        raise ValueError(f"--max-neurons-per-day must be above 0 and at most {free:g} (the free allocation a day; on "
                         f"Workers Paid every neuron past it is billed)")
    rpd = None if args.max_requests_per_day is None else _cap(args.max_requests_per_day, None, 10 ** 6,
                                                             "--max-requests-per-day", p, "requests a UTC day")
    return {"rpm": _cap(args.rpm, CF_RPM_DEFAULT, CF_RPM_LIMIT, "--rpm", p, "Workers AI's requests a minute"),
            "neurons": float(neurons), "rpd": rpd, "max_429": args.max_consecutive_429}


def apply_provider_flags(args, reasoning):
    """Check a provider run's flags and set what the preset decides; returns the provider settings, or ValueError.

    Nothing is sent. The settings dict holds the provider, the model and its table row, the table's source and date,
    the account id (Cloudflare), the API root, the reasoning fields to send and the caps; provider_backend.py and
    start_provider read it.
    """
    p = active(args)
    pre = PRESETS[p]
    title = pre["title"]
    # ── OpenRouter's paths and spending ──
    if args.free_only:
        raise ValueError(f"--free-only is OpenRouter's :free mode; a --provider {p} run is always held to {title}'s "
                         f"free tier: drop --free-only")
    if args.key_check or args.max_key_headroom_usd is not None or args.allow_key_headroom:
        raise ValueError(f"--key-check and the key-headroom flags read OpenRouter's key record; check a {title} key "
                         f"with --key-status --provider {p}")
    for flag, value in (("--max-usd", args.max_usd), ("--price-in", args.price_in), ("--price-out", args.price_out),
                        ("--price-cache-read", args.price_cache_read)):
        if value is not None and value != 0:
            raise ValueError(f"--provider {p} runs {title}'s free tier and spends nothing: leave {flag} out")
    # ── The other provider's flags ──
    other = ([("--max-neurons-per-day", args.max_neurons_per_day), ("--account-id-env", args.account_id_env)]
             if p == "groq" else
             [("--max-tokens-per-minute", args.max_tokens_per_minute), ("--max-tokens-per-day", args.max_tokens_per_day)])
    for flag, value in other:
        if value is not None:
            raise ValueError(f"{flag} applies to --provider {'cloudflare' if p == 'groq' else 'groq'}")
    if (args.reasoning or "").strip().startswith("{"):
        raise ValueError(f"--provider {p} takes --reasoning as an effort word or omit, not a JSON object (that is "
                         f"OpenRouter's reasoning field)")
    # ── The model's row, the ledger and the URL ──
    table = load_table(p)
    entry = table["models"].get(args.model)
    if entry is None:
        raise ValueError(f"{args.model} is not in the {pre['table_name']} (cloud/{pre['table']}, read {table['read']}): "
                         f"{', '.join(table['models'])}; add a row only after reading {table['source']} again")
    if not args.ledger and not args.dry_run:
        raise ValueError(f"--provider {p} needs --ledger: one file shared by every {title} run, which keeps the day's "
                         f"count (the free limits count per {pre['scope']}, not per run)")
    root = resolve_root(p, args.base_url)
    account = None
    if p == "cloudflare":
        account = read_account_id(args.account_id_env or ACCOUNT_ENV, needed=not args.dry_run) or DRY_RUN_ACCOUNT
        args.base_url = f"{root}/accounts/{account}/ai/v1"
    else:
        args.base_url = root
    args.api_key_env = args.api_key_env or pre["key_env"]
    # ── What the body carries ──
    wire = reasoning_wire(p, args.model, entry, reasoning)
    drop = {d.strip() for d in (args.drop_params or "").split(",") if d.strip()}
    for k in UNSUPPORTED_SAMPLERS[p]:
        if getattr(args, k, None) is not None and k not in drop:
            raise ValueError(f"{title} does not document {k}: drop --{k.replace('_', '-')} (the pin would be refused or "
                             f"silently ignored while the record lists it)")
    if p == "groq":
        # Groq documents max_completion_tokens (max_tokens is deprecated) and strict mode needs every property required
        # with additionalProperties false; answers are still validated against the suite's own schema (score.py).
        args.max_tokens_field = "max_completion_tokens"
        args.schema_normalise = True
        most = entry.get("max_completion_tokens")
        if isinstance(most, int) and args.num_predict is not None and args.num_predict > most:
            raise ValueError(f"--num-predict {args.num_predict} is above {args.model}'s output cap on Groq ({most})")
    caps = _caps(p, args, entry, table)
    # ── Zero spend, and the record's price row names the table ──
    args.max_usd, args.price_in, args.price_out, args.price_cache_read = 0.0, 0.0, 0.0, None
    args.price_as_of = args.price_as_of or table["read"]
    args.price_source = args.price_source or table["source"]
    args.endpoint_tag = args.endpoint_tag or p
    return {"provider": p, "title": title, "model": args.model, "entry": entry, "caps": caps,
            "table": {"file": f"cloud/{pre['table']}", "source": table["source"], "read": table["read"],
                      "free_neurons_per_day": table.get("free_neurons_per_day")},
            "account_id": account, "api_root": root, "reasoning_wire": wire, "reasoning_requested": args.reasoning}


def worst_case_line(args, est):
    """--dry-run: the first request's worst case in the provider's own unit, as the gate would reserve it before
    sending (``est`` is budget.Budget.estimate's result). Why: the USD worst case of a provider run is always 0, which
    says nothing about how much of the day's tokens or neurons one call may take."""
    p = active(args)
    entry = load_table(p)["models"].get(args.model) or {}
    prompt, cap = est["prompt_tokens_est"], est["output_cap"]
    if p == "groq":
        return (f"note: --provider groq reserves up to {prompt + cap} tokens for this request (prompt estimate {prompt} "
                f"plus the output cap {cap}) against the per-minute and 24-hour token caps, counted from the --ledger "
                f"at run start; a dry run sends nothing")
    neurons = prompt * entry.get("in", 0) / 1e6 + cap * entry.get("out", 0) / 1e6
    return (f"note: --provider cloudflare reserves up to {neurons:.2f} neurons for this request (prompt estimate "
            f"{prompt} tokens x {entry.get('in', 0):g} + output cap {cap} x {entry.get('out', 0):g} per million) against "
            f"the day's neuron cap, counted from the --ledger at run start; a dry run sends nothing")


# ── Start of a run ───────────────────────────────────────────────────────────

def start_provider(args, backend, rows, run_info, sink, clock=time.time, sleep=time.sleep):
    """The start of a provider run, on every start and resume: the gate from the ledger's quota rows, the record
    fields, one start line; returns (None, gate) to go on or ((kind, message), None) to stop before any request."""
    s = backend.provider
    p, caps, entry = s["provider"], s["caps"], s["entry"]
    worst = Budget(0.0, 0.0, 0.0, None, args.est_tokens_per_byte, args.est_extra_prompt_tokens, free_only=True)

    def estimate(body):
        """(prompt tokens, output cap) of one attempt's worst case: budget.py's pessimistic estimate."""
        e = worst.estimate(body)
        return e["prompt_tokens_est"], e["output_cap"]

    if p == "groq":
        gate = provider_gate.GroqGate(s["model"], entry, caps, rows=rows, sink=sink, reserve=caps["reserve"],
                                      max_429=caps["max_429"], estimate=estimate, clock=clock, sleep=sleep)
    else:
        gate = provider_gate.NeuronGate(s["model"], entry, cap=caps["neurons"], rpm=caps["rpm"], per_day=caps["rpd"],
                                        rows=rows, sink=sink, max_429=caps["max_429"], estimate=estimate,
                                        source=s["table"]["source"], clock=clock, sleep=sleep)
    backend.gate = gate
    run_info.update({"provider": p, "provider_caps": gate.caps_record(), "provider_table": s["table"],
                     "reasoning_requested": s["reasoning_requested"]})
    print(gate.start_line(), flush=True)
    if p == "cloudflare":
        print("note: keep the account on Workers Free: there, calls past the free allocation fail; on Workers Paid "
              "they are billed, and this run's count is the only guard (see cloud/README.md)", file=sys.stderr)
    stop = gate.allowance_stop()
    return (stop, None) if stop else (None, gate)
