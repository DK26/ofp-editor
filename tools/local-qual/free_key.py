#!/usr/bin/env python3
"""The OpenRouter key record in free-only mode: what is kept, what is refused, and what is compared (tools/local-qual).

What it owns
------------
* ``key_summary``: the non-secret fields of ``GET /api/v1/key`` [K]. The record's ``label`` is a partly masked copy of
  the key and its creator, organisation and workspace ids identify the account, so none of them is kept, recorded or
  printed.
* ``key_refusal`` and ``key_headroom``: which keys may run a free round (never a management key; no paid-model
  headroom above a threshold; not expired; the account's daily free-request counter and the usage figures readable).
* ``usage_rise``: whether the key's spend moved between two readings of one run (the key poll).
* ``key_row`` and ``baseline_rise``: the key's usage written to the run's ledger at every reading (a ``budget_event:
  "key"`` row) and compared at the next start. A charge the responses did not show (a stream or proxy page answered a
  call, a request timed out, the run was killed before its final key read) then still stops the next run on that
  ledger, instead of becoming that run's new baseline.

How it fits
-----------
free_mode.py re-exports these for its callers (cloud_backend.py builds ``key_summary`` from ``GET /key``;
free_mode.start_free runs the refusal, the baseline check and the poll; cloud_run.Session writes the rows). The rows
carry only numbers and a time: budget.py ignores them (no ``call_id``), rate_gate.py counts only ``reserve`` rows,
and score.py and run.py's ``--resume`` skip every ``budget_event`` row. Standard library only.

Source (read 2026-09-27)
------------------------
[K] https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key : ``limit``, ``limit_remaining``,
``limit_reset``, ``usage``, ``usage_daily``, ``byok_usage``, ``include_byok_in_limit``, ``is_free_tier``,
``is_management_key`` (``is_provisioning_key`` is its deprecated name), ``expires_at`` and
``free_model_daily_requests`` {used, limit, remaining} per UTC day.
"""
import datetime as _dt
import math
import re

# Key-record strings kept for printing only when they look like a date or a reset period.
_SAFE_TEXT = re.compile(r"^[A-Za-z0-9:.+\- ]{1,40}$")
# The all-time spend figures a key row keeps and the next start compares (``usage_daily`` resets at 00:00 UTC, so it
# is recorded but never compared across runs).
BASELINE_FIELDS = ("usage", "byok_usage")


def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


def _count(v):
    return v if isinstance(v, int) and not isinstance(v, bool) and v >= 0 else None


def key_summary(data):
    """The non-secret fields of a GET /key ``data`` object [K].

    Strings are kept only when they look like what the schema says (a date, a reset period), numbers only when
    finite; ``label`` and the account ids are dropped.
    """
    d = data if isinstance(data, dict) else {}
    out = {f: _num(d.get(f)) for f in ("limit", "limit_remaining", "usage", "usage_daily", "byok_usage")}
    out.update({f: d.get(f) if isinstance(d.get(f), bool) else None
                for f in ("is_free_tier", "is_management_key", "include_byok_in_limit")})
    for f in ("limit_reset", "expires_at"):
        v = d.get(f)
        out[f] = v if isinstance(v, str) and _SAFE_TEXT.match(v) else None
    fm = d.get("free_model_daily_requests")
    out["free_model_daily_requests"] = ({k: _count(fm.get(k)) for k in ("used", "limit", "remaining")}
                                        if isinstance(fm, dict) else None)
    return out


def key_headroom(k):
    """USD the key could still spend on paid models: its limit_remaining, or infinity when it has no limit."""
    if k.get("limit") is None or k.get("limit_remaining") is None:
        return math.inf
    return max(0.0, float(k["limit_remaining"]))


def key_refusal(k, max_headroom, allow_headroom, now):
    """Why this key may not run a free round, or None. ``k`` is a ``key_summary``; ``now`` an aware datetime.

    A management key can create keys and read the account balance, so it is never accepted. A key with no credit
    limit has unknown headroom: a normal key cannot read the account balance, and new accounts may hold a small
    allowance, so ``limit: null`` counts as unlimited. Headroom above ``max_headroom`` is refused unless
    ``allow_headroom`` accepts it knowingly (the per-response check and the key poll still stop the run on any charge).
    """
    if k.get("is_management_key") is not False:
        return ("the key record does not say is_management_key false; never give this tool a management key (it can "
                "create keys and read the balance): create a normal key")
    exp = k.get("expires_at")
    if exp:
        try:
            when = _dt.datetime.fromisoformat(exp.replace("Z", "+00:00"))
            if when.tzinfo is not None and when <= now:
                return f"the key expired at {exp}"
        except ValueError:
            pass  # an unreadable date is not a spend risk: an expired key gets HTTP 401, which stops the run
    fm = k.get("free_model_daily_requests")
    if not fm or any(fm.get(x) is None for x in ("used", "limit", "remaining")):
        return "the key record has no free_model_daily_requests counter, so the account's daily quota cannot be kept"
    if k.get("usage") is None or k.get("byok_usage") is None:
        return "the key record has no usage or byok_usage figure, so a charge during the run could not be seen"
    headroom = key_headroom(k)
    if headroom > max_headroom and not allow_headroom:
        where = ("no credit limit (unlimited)" if math.isinf(headroom)
                 else f"{k['limit_remaining']} USD left of its {k['limit']} USD credit limit")
        return (f"the key has {where}; --free-only needs a key that cannot spend: give it a credit limit of 0 (if "
                f"OpenRouter then refuses free calls, the smallest limit it accepts, with --max-key-headroom-usd set to "
                f"that value), or pass --allow-key-headroom to accept the headroom knowingly")
    return None


def describe_key(k):
    """One console line of non-secret key fields."""
    fm = k.get("free_model_daily_requests") or {}
    return (f"credit limit {k.get('limit')} USD ({k.get('limit_remaining')} left, reset {k.get('limit_reset')}), usage "
            f"{k.get('usage')} USD (today {k.get('usage_daily')}, BYOK {k.get('byok_usage')}), management key "
            f"{k.get('is_management_key')}, expires {k.get('expires_at')}; free requests today: {fm.get('used')} used "
            f"of {fm.get('limit')}, {fm.get('remaining')} left")


def usage_rise(start, now):
    """Why the key's spend moved between two summaries (all-time, today's and BYOK usage), or None."""
    for f in ("usage", "usage_daily", "byok_usage"):
        a, b = start.get(f), now.get(f)
        if a is None:
            continue
        if b is None:
            return f"{f} is missing from the key record"
        if b > a:
            return f"the key's {f} rose from {a} to {b} USD"
    return None


# ── Across runs: the ledger keeps the key's last reading ─────────────────────

def key_row(k):
    """The ledger row for one reading of the key: its usage figures, the daily counter and the time, nothing else."""
    return {"budget_event": "key", "usage": k.get("usage"), "byok_usage": k.get("byok_usage"),
            "usage_daily": k.get("usage_daily"), "free_model_daily_requests": k.get("free_model_daily_requests"),
            "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")}


def baseline_rise(rows, k):
    """Why the key's all-time spend is above the last reading this ledger recorded, or None.

    A key kept for free testing never spends, so any rise since the last run means something was billed that no run
    saw: a charge after that run's last key read, or other use of the key. A new key with lower figures is not a
    rise (the new reading simply becomes the baseline). Rows without a reading (older ledgers) give no baseline.
    """
    last = next((r for r in reversed(rows) if isinstance(r, dict) and r.get("budget_event") == "key"), None)
    if last is None:
        return None
    for f in BASELINE_FIELDS:
        a, b = _num(last.get(f)), _num(k.get(f))
        if a is not None and b is not None and b > a:
            return f"the key's {f} rose from {a} to {b} USD since this ledger's last key reading ({last.get('ts')})"
    return None
