#!/usr/bin/env python3
"""The ``openai`` backend's command line and its offline checks (tools/local-qual).

What it owns
------------
* ``add_cloud_args``: the flags of the ``openai`` backend, with free mode's (free_mode.add_free_args) and the Groq
  and Cloudflare provider flags (providers.add_provider_args);
* the parsers of ``--reasoning`` and ``--extra-body``;
* the OpenRouter routing advice and refusals: the pinned endpoint's tag, an unpinned run, a sampler pin OpenRouter
  lists under another name, a strict-schema run without ``require_parameters``;
* ``schema_conformant``, the canary's check that an endpoint really enforced the strict schema;
* ``_finite``, the number check the flag refusals share.

How it fits
-----------
Split out of cloud_run.py, which re-exports every name here (run.py, run_preset.py and the tests import them from
cloud_run), so that module keeps the backend construction, the run's record fields and the per-run Session.
Nothing here sends a request. Standard library only.
"""
import json
import math

import free_mode
import providers
from cloud_guard import DROPPABLE_PARAMS, STRIPPABLE_KEYWORDS, normalise_schema

REASONING_EFFORTS = ("none", "minimal", "low", "medium", "high", "xhigh", "max")


# ── Command line ─────────────────────────────────────────────────────────────
def add_cloud_args(ap):
    """The ``openai`` backend's flags (see the README's cloud section)."""
    cloud = ap.add_argument_group("openai backend (paid endpoints)")
    cloud.add_argument("--api-key-env", default=None,
                       help="name of the environment variable that holds the API key (required; the key is never "
                            "taken from the command line and never written to records or the console)")
    cloud.add_argument("--max-usd", type=float, default=None,
                       help="hard budget cap in USD (required): no attempt is sent whose worst case would push the "
                            "total spent in the ledger past it")
    cloud.add_argument("--price-in", type=float, default=None, help="input price, USD per 1M tokens (required)")
    cloud.add_argument("--price-out", type=float, default=None,
                       help="output price, USD per 1M tokens, reasoning included (required)")
    cloud.add_argument("--price-cache-read", type=float, default=None,
                       help="cached-input price, USD per 1M tokens (default: --price-in)")
    cloud.add_argument("--price-as-of", default=None, help="date the prices were read (recorded)")
    cloud.add_argument("--price-source", default=None, help="URL the prices were read from (recorded)")
    cloud.add_argument("--ledger", default=None,
                       help="JSONL ledger shared by several runs (default: the --out file itself); one run at a "
                            "time per ledger")
    cloud.add_argument("--reasoning", default=None,
                       help="required: 'none' (switch reasoning off on hybrid models), another effort (minimal, "
                            "low, medium, high, xhigh, max), a JSON object for OpenRouter's reasoning field, or "
                            "'omit' to send no reasoning field (the provider's default then applies)")
    cloud.add_argument("--extra-body", default=None,
                       help="JSON object (or @file) merged into every request, e.g. OpenRouter provider pinning: "
                            "'{\"provider\": {\"only\": [\"deepinfra/bf16\"], \"allow_fallbacks\": false, "
                            "\"require_parameters\": true, \"data_collection\": \"deny\"}}'")
    cloud.add_argument("--drop-params", default="",
                       help=f"comma-separated parameters not to send for models that reject them "
                            f"({', '.join(DROPPABLE_PARAMS)})")
    cloud.add_argument("--max-tokens-field", default="max_tokens", choices=("max_tokens", "max_completion_tokens"),
                       help="name of the output cap field (OpenAI's own API wants max_completion_tokens)")
    cloud.add_argument("--schema-normalise", action="store_true",
                       help="send a strict-mode copy of each schema (additionalProperties false, all properties "
                            "required); answers are still validated against the suite's own schema")
    cloud.add_argument("--schema-strip", default="",
                       help="comma-separated schema keywords to drop from the wire copy (e.g. maxLength,pattern for "
                            "endpoints that reject them); score.py still checks them in code")
    cloud.add_argument("--expect-provider", default=None,
                       help="stop the run if a response names another provider (e.g. deepinfra/bf16 or DeepInfra)")
    cloud.add_argument("--endpoint-tag", default=None,
                       help="endpoint label for records (default: the single entry of provider.only or order)")
    cloud.add_argument("--max-attempts", type=int, default=5, help="attempts per call on 408/429/5xx (default 5)")
    cloud.add_argument("--retry-base-s", type=float, default=2.0, help="backoff base in seconds (default 2)")
    cloud.add_argument("--retry-cap-s", type=float, default=60.0, help="longest single backoff in seconds (default 60)")
    cloud.add_argument("--est-tokens-per-byte", type=float, default=1.0,
                       help="prompt tokens assumed per UTF-8 byte for the worst-case reservation (default 1.0, an "
                            "upper bound; lower it only after the preflight measured the tokenizer)")
    cloud.add_argument("--est-extra-prompt-tokens", type=float, default=0.0,
                       help="hidden prompt tokens the endpoint adds (injected format or tool prompts) for the "
                            "reservation (default 0)")
    cloud.add_argument("--canary", type=int, default=20,
                       help="judge the run after this many calls: stop if parse failures (schema arms) exceed "
                            "--canary-max-parse-fail or errors exceed --canary-max-error (default 20; 0 = off)")
    cloud.add_argument("--canary-max-parse-fail", type=float, default=0.2)
    cloud.add_argument("--canary-max-error", type=float, default=0.1)
    cloud.add_argument("--key-check", action="store_true",
                       help="OpenRouter: before the run, read GET <base>/key and refuse unless the key has a credit "
                            "limit with at most --max-usd + --key-margin-usd left; after it, report the key's usage "
                            "change against the ledger")
    cloud.add_argument("--key-margin-usd", type=float, default=1.0)
    free_mode.add_free_args(ap)
    providers.add_provider_args(ap)


def parse_reasoning(value):
    """--reasoning: 'omit' (the field is not sent), an effort word, or a JSON object such as {"effort":"low"}.

    A JSON object's ``max_tokens`` (a thinking budget, which a provider may bill on top of the output cap) must be a
    whole number above 0: budget.py adds it to every worst case only as an integer, so 5000.0, "5000" or true would go
    out as a budget the reservation never counted.
    """
    v = (value or "").strip()
    if v == "omit":
        return None
    if v.startswith("{"):
        obj = json.loads(v)
        if not isinstance(obj, dict):
            raise ValueError("--reasoning JSON must be an object")
        if "max_tokens" in obj:
            budget = obj["max_tokens"]
            if isinstance(budget, bool) or not isinstance(budget, int) or budget <= 0:
                raise ValueError(f"--reasoning max_tokens must be a whole number of tokens above 0 (the worst case "
                                 f"counts it only then), got {json.dumps(budget)}")
        return obj
    if v in REASONING_EFFORTS:
        return {"effort": v}
    raise ValueError(f"--reasoning must be omit, one of {', '.join(REASONING_EFFORTS)}, or a JSON object")


def parse_extra_body(value):
    """--extra-body: a JSON object, or @path to a file holding one (easier to quote on Windows)."""
    if not value:
        return {}
    text = value
    if value.startswith("@"):
        with open(value[1:], encoding="utf-8") as f:
            text = f.read()
    obj = json.loads(text)
    if not isinstance(obj, dict):
        raise ValueError("--extra-body must be a JSON object")
    return obj


def endpoint_tag_from(extra_body):
    """The pinned endpoint named by an OpenRouter provider block (only/order with one entry), or None."""
    prov = extra_body.get("provider") if isinstance(extra_body.get("provider"), dict) else {}
    for field in ("only", "order"):
        vals = prov.get(field)
        if isinstance(vals, list) and len(vals) == 1 and isinstance(vals[0], str):
            return vals[0]
    return None


def pinning_warnings(host, extra_body):
    """Advice when an OpenRouter run is not pinned to one endpoint (the served model could change mid-run)."""
    if not host.endswith("openrouter.ai"):
        return []
    prov = extra_body.get("provider") if isinstance(extra_body.get("provider"), dict) else {}
    notes = []
    if not (prov.get("only") or prov.get("order")) or prov.get("allow_fallbacks", True) is not False:
        notes.append("the run is not pinned: set provider.only (or order) with allow_fallbacks false in --extra-body, "
                     "or calls may be served by different providers and precisions")
    return notes


# Sampler pins whose run.py name (llama-server's) is not OpenRouter's: the backend sends the flag's own name, while
# OpenRouter's endpoints list the parameter under the second name in their supported_parameters (free_mode.PARAM_NAMES
# maps the same pair when it checks an endpoint's list).
OPENROUTER_NAMES = {"repeat_penalty": "repetition_penalty"}


def sampler_warnings(host, sampler_sent):
    """Advice when an OpenRouter run pins a sampler value under a name OpenRouter does not list.

    The request is left as it is (existing command lines keep their exact bodies), so the run says it at the start:
    the pin is most likely dropped while the record's ``sampler_sent`` names it. The fix is the same value under
    OpenRouter's name in --extra-body, instead of the flag.
    """
    if not host.endswith("openrouter.ai"):
        return []
    return [f"--{name.replace('_', '-')} is sent as '{name}', which OpenRouter lists as '{theirs}', so the pin is "
            f"most likely ignored although the records list it; drop the flag and pass "
            f"'{{\"{theirs}\": {sampler_sent[name]}}}' in --extra-body instead"
            for name, theirs in OPENROUTER_NAMES.items() if sampler_sent.get(name) is not None]


def routing_refusal(host, extra_body, schema_sent):
    """Why an OpenRouter strict-schema run may not start, or None.

    Without ``provider.require_parameters: true`` OpenRouter may route to an endpoint that does not support
    ``response_format`` and silently ignores it (provider routing docs, read 2026-09-27), so the strict arm would
    measure unconstrained output. The canary would catch it after --canary calls; this refuses it before any.
    """
    if not (schema_sent and host.endswith("openrouter.ai")):
        return None
    prov = extra_body.get("provider") if isinstance(extra_body.get("provider"), dict) else {}
    if prov.get("require_parameters") is not True:
        return ("a strict-schema run on OpenRouter needs provider.require_parameters: true in --extra-body, or it may "
                "be routed to an endpoint that ignores response_format")
    return None


def schema_conformant(payload, rec):
    """Did the first answer of a strict-schema call come back as bare JSON valid against the schema sent?

    A grammar-constrained endpoint returns exactly that; fenced JSON, prose around it or an off-schema value
    (a letter outside the enum) means the endpoint did not enforce the schema, whatever parse_ok says. None for a
    call sent without a schema. Only structure is judged (types, enums, required and extra keys) against the
    wire schema: several grammar engines enforce structure but ignore length and pattern limits, and score.py
    checks those limits anyway, so they must not make the canary stop a run whose schema is enforced.
    """
    rf = payload.get("response_format")
    if not isinstance(rf, dict):
        return None
    from score import validate_schema  # sibling module with no side effects
    first = rec.get("first") or rec
    parsed = first.get("parsed")
    wire = (rf.get("json_schema") or {}).get("schema") or {}
    structure, _ = normalise_schema(wire, strict_objects=False, strip=STRIPPABLE_KEYWORDS)
    return first.get("parse_mode") == "strict" and isinstance(parsed, dict) and not validate_schema(parsed, structure)


def _finite(value, low, flag, allow_equal=True):
    ok = isinstance(value, (int, float)) and math.isfinite(value) and (value >= low if allow_equal else value > low)
    if not ok:
        raise ValueError(f"{flag} must be a finite number {'>=' if allow_equal else '>'} {low}, got {value}")
