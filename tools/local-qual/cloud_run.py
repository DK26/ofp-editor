#!/usr/bin/env python3
"""Command line and run-time guards for the ``openai`` backend (tools/local-qual).

What it owns
------------
Everything run.py needs only when it talks to a paid endpoint:

* the ``openai`` argument group and its refusals: no start without
  ``--max-usd``, both prices, ``--api-key-env`` and an explicit
  ``--reasoning``; no key on the command line; no ``--warmup``;
* building ``OpenAICompatBackend`` (cloud_backend.py) from those flags and
  the record fields that describe the endpoint (host, pinned endpoint, prices,
  flags sent and dropped);
* ``Session``: the ledger (the output file, or a shared ``--ledger`` file)
  and its lock (one process per ledger, so two runs cannot each spend the
  cap), the ``Budget`` (budget.py) loaded from it, the optional key check
  (OpenRouter's ``GET /key``), the stop rows, and the canary that judges the
  first calls of a run, including whether the endpoint really enforced the
  strict schema;
* ``--free-only`` (free_mode.py holds its rules, free_key.py the key rules,
  rate_gate.py the rate caps): the flag checks, one free run per user at a
  time (a lock beside the key store), the start checks on every start and
  resume (live catalogue, key, the key's spend against the ledger's last
  reading, the day's request allowance), the rate gate, the key readings
  written to the ledger, and one more key check however a started run ends;
  ``--rpm``/``--max-requests-per-day`` on a paid run give it a plain rate
  gate;
* the exit codes of the stops.

How it fits
-----------
run.py stays one loop for every backend: for ``--backend openai`` it calls
``add_cloud_args``, ``make_backend``, ``run_info`` and one ``Session``, and
maps a result's ``fatal`` field to a stop row and an exit code from here.
Standard library only.
"""
import datetime as _dt
import json
import math
import os
import sys
import urllib.parse

import free_mode
from budget import Budget, read_ledger_rows
from cloud_backend import OpenAICompatBackend
from cloud_guard import DROPPABLE_PARAMS, STRIPPABLE_KEYWORDS, normalise_schema
from rate_gate import RateGate

REASONING_EFFORTS = ("none", "minimal", "low", "medium", "high", "xhigh", "max")

# Exit codes (0 ok, 2 some calls failed, 3 server not ready or model unknown, as for the local backends).
EXIT_BUDGET = 4  # the cap would be exceeded, HTTP 402, or a call cost more than its worst case
EXIT_CONFIG = 5  # a non-retryable 4xx (bad model id, bad parameter, auth) or a failed key check
EXIT_SCHEMA = 6  # the endpoint rejected the strict response schema
EXIT_CANARY = 7  # the canary window failed (parse failures, errors) or reasoning leaked on an effort-none call
EXIT_PROVIDER = 8  # the response names a provider other than the pinned one
EXIT_NOT_FREE = 9  # free-only: the model is not free now, a response was charged or came from another model, or the
#                    key's usage moved
EXIT_QUOTA = 10  # the day's request allowance is used up, or the rate limit held; resume later with --resume
FATAL_EXIT = {"budget": EXIT_BUDGET, "cost_anomaly": EXIT_BUDGET, "config": EXIT_CONFIG,
              "schema_rejected": EXIT_SCHEMA, "reasoning_leak": EXIT_CANARY, "provider_mismatch": EXIT_PROVIDER,
              "not_free": EXIT_NOT_FREE, "quota": EXIT_QUOTA, "rate_limited": EXIT_QUOTA}
FATAL_STOP = {"budget": "BudgetLimited", "cost_anomaly": "CostAnomaly", "config": "ConfigFault",
              "schema_rejected": "SchemaRejected", "reasoning_leak": "ReasoningLeak",
              "provider_mismatch": "ProviderMismatch", "not_free": "NotFree", "quota": "DailyQuota",
              "rate_limited": "RateLimited"}


class LedgerLocked(RuntimeError):
    """Another run holds the ledger (or the output file). Two processes on one ledger would each read the total
    once at start and could each spend up to the cap, so the second one refuses to start."""


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


def parse_reasoning(value):
    """--reasoning: 'omit' (the field is not sent), an effort word, or a JSON object such as {"effort":"low"}."""
    v = (value or "").strip()
    if v == "omit":
        return None
    if v.startswith("{"):
        obj = json.loads(v)
        if not isinstance(obj, dict):
            raise ValueError("--reasoning JSON must be an object")
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


def make_backend(ap, args):
    """Validate the openai flags and build the client; every refusal is ``ap.error`` (exit 2, nothing sent).

    Returns (backend, settings) where settings holds the parsed extra body, reasoning, dropped parameters and
    stripped schema keywords for the records.
    """
    if args.api_key is not None:
        ap.error("--backend openai never takes a key on the command line; put it in an environment variable "
                 "and pass its name with --api-key-env")
    if not args.model:
        ap.error("--model (the endpoint's model id) is required with --backend openai")
    if not args.base_url:
        ap.error("--base-url is required with --backend openai (e.g. https://openrouter.ai/api/v1)")
    if args.model.endswith(":online"):
        ap.error("--model ...:online adds OpenRouter's web search, billed per request outside the token prices the "
                 "budget cap reserves; use the model id without :online")
    if args.warmup:
        ap.error("--warmup is not available with --backend openai: every call is paid and recorded (drop each "
                 "schema's first call from latency figures instead)")
    if args.reasoning is None:
        ap.error("--reasoning is required with --backend openai (for example 'none'), so the effort is always "
                 "explicit; 'omit' sends no reasoning field")
    try:
        reasoning = parse_reasoning(args.reasoning)
        extra_body = parse_extra_body(args.extra_body)
    except (ValueError, OSError) as e:
        ap.error(str(e))
    if args.free_only:
        # Offline free-mode checks; the cap and the prices become 0 (free_mode.py).
        try:
            extra_body = free_mode.apply_free_flags(args, extra_body)
        except ValueError as e:
            ap.error(str(e))
    elif args.max_key_headroom_usd is not None or args.allow_key_headroom:
        ap.error("--max-key-headroom-usd and --allow-key-headroom apply to --free-only runs (paid runs: --key-check)")
    if (args.rpm is not None and args.rpm < 1) or (args.max_requests_per_day is not None
                                                   and args.max_requests_per_day < 1):
        ap.error("--rpm and --max-requests-per-day must be >= 1")
    drop = tuple(p.strip() for p in args.drop_params.split(",") if p.strip())
    unknown = [p for p in drop if p not in DROPPABLE_PARAMS]
    if unknown:
        ap.error(f"--drop-params: unknown parameter(s) {', '.join(unknown)}")
    strip = tuple(p.strip() for p in args.schema_strip.split(",") if p.strip())
    # ── Numbers that decide what a call may cost (checked even on --dry-run, which prints the worst case) ──
    try:
        if args.max_usd is not None and not args.free_only:
            _finite(args.max_usd, 0, "--max-usd", allow_equal=False)
        for flag, value in (("--price-in", args.price_in), ("--price-out", args.price_out),
                            ("--price-cache-read", args.price_cache_read)):
            if value is not None:
                _finite(value, 0, flag)
                if value == 0 and flag != "--price-cache-read" and not args.free_only:
                    raise ValueError(f"{flag} 0 makes every worst case free; zero prices are accepted only with "
                                     f"--free-only (OpenRouter :free models)")
        _finite(args.est_tokens_per_byte, 0.1, "--est-tokens-per-byte")
        _finite(args.est_extra_prompt_tokens, 0, "--est-extra-prompt-tokens")
        _finite(args.key_margin_usd, 0, "--key-margin-usd")
        for flag, value in (("--canary-max-parse-fail", args.canary_max_parse_fail),
                            ("--canary-max-error", args.canary_max_error)):
            _finite(value, 0, flag)
            if value > 1:
                raise ValueError(f"{flag} is a rate between 0 and 1, got {value}")
        if args.num_predict is not None and args.num_predict <= 0:
            raise ValueError("--num-predict must be > 0 with --backend openai: the output cap bounds every worst case")
        if args.max_attempts < 1:
            raise ValueError("--max-attempts must be >= 1")
    except ValueError as e:
        ap.error(str(e))
    api_key = None
    if not args.dry_run:
        # ── Refuse to start without a hard budget and a key from the environment ──
        missing = [flag for flag, value in (("--max-usd", args.max_usd), ("--price-in", args.price_in),
                                            ("--price-out", args.price_out), ("--api-key-env", args.api_key_env))
                   if value is None]
        if missing:
            ap.error(f"--backend openai refuses to start without {', '.join(missing)}: every call is paid, and "
                     "the budget cap needs the prices to reserve each call's worst case")
        # Read once, then removed from this process's environment: no process run.py might start later (a grader, a
        # helper in a future change) inherits the key. The backend keeps the only copy.
        api_key = os.environ.pop(args.api_key_env, None) or None
        if not api_key:
            ap.error(f"the environment variable {args.api_key_env} is not set or empty")
    try:
        backend = OpenAICompatBackend(
            args.base_url, args.timeout, api_key, extra_body=extra_body, reasoning=reasoning, drop_params=drop,
            schema_normalise=args.schema_normalise, schema_strip=strip, max_tokens_field=args.max_tokens_field,
            max_attempts=args.max_attempts, retry_base_s=args.retry_base_s, retry_cap_s=args.retry_cap_s,
            expect_provider=args.expect_provider)
    except ValueError as e:
        ap.error(str(e))
    return backend, {"extra_body": extra_body, "drop": drop, "strip": strip}


def print_estimate(args, payload):
    """--dry-run with the budget flags: the first request's worst case, without sending anything."""
    if args.max_usd is None or args.price_in is None or args.price_out is None:
        return
    try:
        est = Budget(args.max_usd, args.price_in, args.price_out, args.price_cache_read, args.est_tokens_per_byte,
                     args.est_extra_prompt_tokens, free_only=args.free_only).estimate(payload)
        print(json.dumps({"worst_case_per_attempt": est}, indent=1))
    except ValueError as e:
        print(f"budget: {e}", file=sys.stderr)
    if args.free_only:
        print("note: --free-only checks the live catalogue, the key and the day's request allowance at run start; a "
              "dry run sends nothing, and provider.only is filled from the live endpoint list then", file=sys.stderr)


def run_info(args, backend, model, settings, sampler):
    """(record label, record fields describing the endpoint); prints the pinning and price warnings."""
    extra_body = settings["extra_body"]
    endpoint_tag = args.endpoint_tag or endpoint_tag_from(extra_body)
    label = args.label or (f"{model}@{endpoint_tag}" if endpoint_tag else model)
    host = urllib.parse.urlsplit(backend.base).hostname or ""
    if args.free_only:
        # Free prices are read from the live catalogue at start (free_mode.start_free), not from flags.
        args.price_as_of = args.price_as_of or _dt.datetime.now(_dt.timezone.utc).date().isoformat()
        args.price_source = args.price_source or f"{backend.base}/models (checked at run start)"
    info = {
        "base_host": host, "model_requested": model, "endpoint_tag": endpoint_tag,
        "extra_body_sent": extra_body or None, "params_dropped": list(settings["drop"]),
        "sampler_sent": {k: v for k, v in sampler.items() if v is not None and k not in settings["drop"]},
        "schema_normalised": bool(args.schema_normalise), "schema_stripped": list(settings["strip"]),
        "price_row": {"in": args.price_in, "out": args.price_out, "cache_read": args.price_cache_read,
                      "as_of": args.price_as_of, "source": args.price_source},
        "budget_usd": args.max_usd,
    }
    for note in ([] if args.free_only else pinning_warnings(host, extra_body)):  # free mode pins at start
        print(f"warning: {note}", file=sys.stderr)
    if not (args.price_as_of and args.price_source):
        print("warning: record where and when the prices were read (--price-as-of, --price-source)", file=sys.stderr)
    return label, info


# ── One paid run ─────────────────────────────────────────────────────────────

def _same_file(a, b):
    """Do two paths name one file? Compared after resolving links and, on Windows, ignoring letter case."""
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def _take_lock(path):
    """Create ``<path>.lock`` exclusively (atomic on every OS) and return its path, or raise LedgerLocked.

    A lock left behind by a killed run blocks the next run too (fail closed); the message says how to clear it.
    Only file names are printed, never a local directory.
    """
    lock = path + ".lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            with open(lock, encoding="utf-8") as f:
                held = f.read(200).strip()
        except OSError:
            held = ""
        if os.path.basename(path) == free_mode.FREE_LOCK_NAME:
            raise LedgerLocked(f"another free-only run is active for this user ({held or 'no details'}): OpenRouter's "
                               f"free limits are per account, so free runs go one at a time; if no other run is "
                               f"active, delete {free_mode.FREE_LOCK_SHOWN} and start again") from None
        raise LedgerLocked(f"{os.path.basename(path)} is in use by another run ({held or 'no details'}); if no "
                           f"other run is active, delete {os.path.basename(lock)} and start again") from None
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(json.dumps({"pid": os.getpid(),
                            "since": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")}))
    return lock


class Session:
    """The paid side of one run: ledger lock, budget, key check, stop rows and canary.

    ``write_row`` is run.py's writer for the output file (it redacts the key and flushes). The ledger is that
    file unless ``--ledger`` names another one, which this session opens for appending and closes in ``finish``.
    The ledger (and the output file, when separate) is locked for the whole run: a second process would read
    the spent total once at start and could spend the cap a second time. A free-only run also holds the per-user
    free lock (free_mode.free_lock_dir), since OpenRouter's free limits are per account, not per ledger. ``finish``
    must run (run.py calls it in a ``finally``), or the locks stay and the next run refuses to start until they are
    deleted.
    """

    def __init__(self, args, backend, out, write_row):
        self.args, self.backend, self.write_row = args, backend, write_row
        self.separate = bool(args.ledger) and not _same_file(args.ledger, out)
        self.ledger_path = os.path.abspath(args.ledger) if self.separate else out
        self.ledger_f, self.locks = None, []
        try:
            # ── Lock first, then read: the total read must be the one this process spends against ──
            if args.free_only:
                # One free run per user at a time, whatever its ledger (see free_mode.free_lock_dir).
                os.makedirs(free_mode.free_lock_dir(), exist_ok=True)
                self.locks.append(_take_lock(os.path.join(free_mode.free_lock_dir(), free_mode.FREE_LOCK_NAME)))
            os.makedirs(os.path.dirname(os.path.abspath(self.ledger_path)), exist_ok=True)
            for path in [self.ledger_path] + ([out] if self.separate else []):
                self.locks.append(_take_lock(path))
            rows = read_ledger_rows(self.ledger_path)
            if self.separate:
                self.ledger_f = open(self.ledger_path, "a", encoding="utf-8", newline="\n")
            # Reserve rows go to the ledger before a request leaves (write-ahead; see budget.py).
            sink = self._ledger_write if self.separate else write_row
            self.budget = Budget(args.max_usd, args.price_in, args.price_out, args.price_cache_read,
                                 args.est_tokens_per_byte, args.est_extra_prompt_tokens, sink=sink, rows=rows,
                                 separate_ledger=self.separate, free_only=args.free_only)
        except BaseException:
            self._release()
            raise
        self.rows = rows  # the rate gate counts today's attempts from the ledger's reserve rows
        self.gate = None
        self.end_checked = False
        self.key_usage_start = None
        self.canary_state = {"calls": 0, "errors": 0, "schema_calls": 0, "schema_parse_fail": 0, "judged": False}

    def _release(self):
        """Close a separate ledger and delete this run's locks (idempotent)."""
        if self.ledger_f is not None:
            self.ledger_f.close()
            self.ledger_f = None
        while self.locks:
            try:
                os.remove(self.locks.pop())
            except OSError:
                pass

    def _ledger_write(self, row):
        """Append one row to a separate ledger, with the key redacted like every line of the output file."""
        self.ledger_f.write(self.backend.redact(json.dumps(row, ensure_ascii=False)) + "\n")
        self.ledger_f.flush()

    def _record_key(self, key):
        """Free mode: write one reading of the key's usage to the ledger (free_key.key_row: numbers and a time only).
        The next start on this ledger compares the key with the newest one, so a charge no run saw is never lost."""
        row = free_mode.key_row(key)
        if self.ledger_f is not None:
            self._ledger_write(row)
        else:
            self.write_row(row)

    def write_stop(self, reason, **fields):
        """A stop row (budget_event 'stop'), in the output file and in a separate ledger."""
        row = self.budget.stop_row(reason, **fields)
        self.write_row(row)
        if self.ledger_f is not None:
            self._ledger_write(row)

    def _stop(self, kind, message, stop_fields):
        """Write the stop row for a start check that failed, print it, and return its exit code."""
        reason = FATAL_STOP.get(kind, "ConfigFault")
        self.write_stop(reason, **stop_fields, detail=message)
        print(f"stop ({reason}): {self.backend.redact(message)}", file=sys.stderr)
        return FATAL_EXIT.get(kind, EXIT_CONFIG)

    def start(self, stop_fields, run_info, payload=None):
        """Report the carried spend, refuse a used-up cap, run the key check (in free mode: the free start checks,
        on every start and resume). ``payload`` is one request body of the run. Returns an exit code to stop, or
        None."""
        spent = self.budget.spent()
        run_info["ledger"] = os.path.basename(self.ledger_path)
        print(f"budget: cap {self.budget.cap_usd:.6f} USD; {spent:.6f} USD already spent in "
              f"{os.path.basename(self.ledger_path)}", flush=True)
        if self.args.free_only:
            if spent > 0:
                return self._stop("not_free", f"the ledger records {spent:.6f} USD spent; a free-only ledger must "
                                              f"stay at 0 (find the charged call before any further run)", stop_fields)
            stop, self.gate = free_mode.start_free(self.args, self.backend, self.rows, payload, run_info,
                                                   record=self._record_key)
            return self._stop(stop[0], stop[1], stop_fields) if stop else None
        if not self.args.ledger:
            print("note: the cap covers only what this output file records; another output file starts again from "
                  "0, so pass one --ledger to every run of a stage to cap the stage", file=sys.stderr)
        if self.args.rpm or self.args.max_requests_per_day:
            # Paid runs may use the client-side caps too (no key poll, no account counter).
            self.gate = self.backend.gate = RateGate(self.args.rpm, self.args.max_requests_per_day, rows=self.rows)
            left = self.gate.remaining_today()
            if left is not None and left <= 0:
                return self._stop("quota", self.gate.quota_message(), stop_fields)
        if spent >= self.budget.cap_usd:
            self.write_stop("BudgetLimited", **stop_fields, detail="the cap is already used up")
            print("stop: the budget cap is already used up; raise --max-usd to continue", file=sys.stderr)
            return EXIT_BUDGET
        if self.args.key_check:
            # ── Second, independent guard: the key's own credit limit on OpenRouter ──
            try:
                key = self.backend.key_info()
            except Exception as e:  # noqa: BLE001 - any failure means the guard cannot be confirmed
                print(f"key check failed: {self.backend.redact(str(e))}", file=sys.stderr)
                return EXIT_CONFIG
            remaining = key.get("limit_remaining")
            if remaining is None or remaining > self.budget.cap_usd + self.args.key_margin_usd:
                print(f"key check: the key's remaining credit limit is {remaining}; set a limit of at most "
                      f"--max-usd + {self.args.key_margin_usd} USD on the key first", file=sys.stderr)
                return EXIT_CONFIG
            run_info["key_limit_remaining_start"] = remaining
            self.key_usage_start = key.get("usage")
        return None

    def canary(self, rec, payload, error):
        """Count one call; after ``--canary`` calls, return a stop reason if the window failed, else None.

        On strict-schema calls a failure is any first answer that is not bare, schema-valid JSON
        (``schema_conformant``): an endpoint that silently drops ``response_format`` often still returns
        parsable JSON (in a code fence, or with a value outside an enum), which ``parse_ok`` alone would pass.
        """
        st, a = self.canary_state, self.args
        if a.canary <= 0 or st["judged"]:
            return None
        st["calls"] += 1
        st["errors"] += 1 if error else 0
        if "response_format" in payload and not error:
            conformant = rec.get("schema_conformant")
            if conformant is None:
                conformant = schema_conformant(payload, rec)
            st["schema_calls"] += 1
            st["schema_parse_fail"] += 0 if conformant else 1
        if st["calls"] < a.canary:
            return None
        st["judged"] = True
        err_rate = st["errors"] / st["calls"]
        pf_rate = st["schema_parse_fail"] / st["schema_calls"] if st["schema_calls"] else 0.0
        if err_rate > a.canary_max_error or pf_rate > a.canary_max_parse_fail:
            return (f"canary after {st['calls']} calls: error rate {err_rate:.2f} (max {a.canary_max_error}), "
                    f"strict-schema non-conformance rate {pf_rate:.2f} (parse failures, fenced or off-schema JSON; "
                    f"max {a.canary_max_parse_fail})")
        return None

    def end_check(self, stop_fields, code=None):
        """Free mode: read the key once more however a started run ends, and return the exit code to use.

        run.py calls it after the last call (``code`` None) and on every stop after the start checks passed (a fatal
        result, the canary, a quota stop; ``code`` is that stop's exit code). A response may not show a charge (a
        stream or proxy page, a timeout), so a usage rise here is a NotFree stop, exit 9, whatever the other reason.
        A failed read keeps a stop's own code (the ledger's last reading still guards the next start); after the
        last call it is a configuration stop, as before. Runs once; a NotFree stop is not read twice.
        """
        if not (self.args.free_only and self.gate is not None) or self.end_checked or code == EXIT_NOT_FREE:
            return code
        self.end_checked = True
        stop, line = free_mode.final_check(self.gate)
        print(self.backend.redact(line), flush=True)
        if stop is None or (code is not None and stop[0] != "not_free"):
            return code
        return self._stop(stop[0], stop[1], stop_fields)

    def finish(self):
        """After the run: the key's usage change (with --key-check), then close a separate ledger and unlock."""
        try:
            self._report_key_usage()
        finally:
            self._release()

    def _report_key_usage(self):
        """With --key-check, and only when the start check passed: the key's usage change against the ledger."""
        if not (self.args.key_check and self.key_usage_start is not None):
            return
        try:
            key_end = self.backend.key_info()
            if isinstance(self.key_usage_start, (int, float)) and isinstance(key_end.get("usage"), (int, float)):
                print(f"key check: the key's usage rose by {key_end['usage'] - self.key_usage_start:.6f} USD; "
                      f"the ledger now holds {self.budget.spent():.6f} USD", flush=True)
        except Exception as e:  # noqa: BLE001 - the end-of-run check is informational
            print(f"key check at the end failed: {self.backend.redact(str(e))}", file=sys.stderr)
