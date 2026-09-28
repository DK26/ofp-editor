#!/usr/bin/env python3
"""The Groq and Cloudflare Workers AI gates: free-tier caps asked before every attempt (tools/local-qual).

What it owns
------------
* ``GroqGate``: Groq's free plan, per model and organisation. Requests and tokens in any rolling minute (the gate
  waits for room) and in any 24 hours (the run stops and names when to resume), counted from the ledger's quota rows
  so every run on the ledger shares the count; the server's own remaining counts from the ``x-ratelimit-*`` headers
  (requests per day and tokens per minute); and the free-plan check: a limit header above the plan's figure means a
  paid tier, which stops the run (exit 9), as does a reported cost or another model answering.
* ``NeuronGate``: Cloudflare's daily free allocation, per account. Every attempt reserves its worst case in neurons
  (prompt estimate x the in-rate + output cap x the out-rate, per million tokens, from the dated table) and is sent
  only when today's neurons (UTC day, every model of the account) plus that reservation stay within the cap; after it
  the reply's usage is priced the same way. A reply beyond its worst case stops the run (CostAnomaly, exit 4): the
  table or the cap no longer holds, and on Workers Paid the excess would be billed.
* The ledger rows both write: ``quota`` before an attempt leaves (write-ahead), ``quota_settle`` after it.
* The parsers of what the providers send back live in provider_reply.py and are re-exported here: Go-style durations
  (``go_duration``), integer headers (``header_int``), output tokens and neurons from usage (``output_tokens``,
  ``neurons_for``), Cloudflare's error codes in both body shapes (``cloudflare_codes``), and the 429 classifiers
  (``groq_classify_429``, ``cloudflare_classify_429``).

How it fits
-----------
A gate has rate_gate.RateGate's interface, which cloud_backend.OpenAICompatBackend.chat calls around every attempt:
``before_attempt`` (may wait, or stop the call unsent: ``quota``, ``config``, ``rate_limited``), ``note_response``
(the 429 streak), ``streak_message`` and ``status`` (the record's ``rate_gate`` field). provider_backend.ProviderBackend
calls the rest: ``begin_call`` before a call, ``after_attempt`` after each HTTP exchange, and ``classify_429`` and
``response_stop`` through chat's hooks. providers.start_provider builds one gate per run and prints ``start_line``;
cloud_run.Session prints ``summary_line`` at the end. Standard library only.

Ledger rows
-----------
``{"budget_event": "quota", "provider", "model", "call_id", "attempt", "unit": "tokens"|"neurons", "reserved", "ts"}``
before an attempt leaves; ``{"budget_event": "quota_settle", ..., "used", "status", "ts"}`` after it. An attempt with
no settle row (the process died), or whose reply carried no usage, counts at its reservation, so a crash can only
over-count. Rejections before any model runs (400, 401, 402, 403, 404, 413, 422, 429, a refused redirect) count 0
tokens or neurons, but every attempt counts as a request. budget.py ignores these rows (they carry no cost_usd),
rate_gate.py counts only "reserve" rows, and score.py and --resume skip every budget_event row.

Sources (read 2026-09-28)
-------------------------
Groq: https://console.groq.com/docs/rate-limits : limits per model and organisation; x-ratelimit-limit-requests and
-remaining-requests always refer to requests per day, -limit-tokens and -remaining-tokens to tokens per minute; the
reset headers are durations such as "2m59.56s" and "7.66s"; retry-after (seconds) comes with a 429. How the daily
windows reset is not documented, so the day here is the last 24 hours, never looser than a calendar day. The 429 text
("... on tokens per day (TPD): Limit 200000 ...", with the organisation id) is quoted from third-party pages.
Cloudflare: https://developers.cloudflare.com/workers-ai/platform/pricing/ (10,000 neurons a day, reset at 00:00 UTC)
and /workers-ai/platform/errors/ (3036: the daily free allocation is used up; 3040: capacity, also a request
rejectIfBusy refused).
"""
import datetime as _dt
import time

from cloud_reply import is_redirect, json_or_none, num
from free_mode import exact_zero
# The parsers of what the providers send back live in provider_reply.py; re-exported here, where the gates, the
# key-status command and the tests use them.
from provider_reply import (CF_CAPACITY, CF_DAILY, _shown, cloudflare_classify_429, cloudflare_codes,  # noqa: F401
                            go_duration, groq_classify_429, header_int, iso_z, neurons_for, output_tokens)
from rate_gate import next_utc_midnight, utc_day

# The rolling windows, in seconds.
WINDOW_S = 60.0
DAY_S = 86400.0
# Ledger times are whole seconds; a row stamped S was written in [S, S+1), so it is placed at its latest possible time
# and never leaves a window early (as rate_gate.LEDGER_TS_RESOLUTION_S).
LEDGER_TS_RESOLUTION_S = 1.0
# Parser-safety bound on waits: a gate that has not found room after this many waits stops the run instead of looping
# (only a clock that never advances could get here).
MAX_WAIT_ROUNDS = 50
# Rejections before any model runs: they use no tokens and no neurons (as cloud_backend.UNBILLED_STATUS).
UNBILLED = frozenset((400, 401, 402, 403, 404, 413, 422, 429))
# ── Ledger rows ──────────────────────────────────────────────────────────────

def _row_epoch(row):
    try:
        return _dt.datetime.fromisoformat(str(row.get("ts")).replace("Z", "+00:00")).timestamp()
    except (ValueError, OverflowError, OSError):
        return None


def load_entries(rows, provider):
    """({(call_id, attempt): entry}, unreadable rows) from a ledger's quota rows of `provider`.

    An entry is {"ts", "model", "reserved", "used"}; ``used`` stays None until a settle row gives it. A quota row
    without a readable time or reservation cannot be counted, so it is reported (the gate refuses to start) rather
    than skipped: skipping it would under-count.
    """
    entries, bad = {}, 0
    for r in rows:
        if not isinstance(r, dict) or r.get("provider") != provider:
            continue
        key = (str(r.get("call_id")), r.get("attempt"))
        if r.get("budget_event") == "quota":
            t, reserved = _row_epoch(r), num(r.get("reserved"))
            if t is None or reserved is None:
                bad += 1
                continue
            entries[key] = {"ts": t + LEDGER_TS_RESOLUTION_S, "model": r.get("model"), "reserved": float(reserved),
                            "used": None}
        elif r.get("budget_event") == "quota_settle" and key in entries:
            used = num(r.get("used"))
            if used is not None:
                entries[key]["used"] = float(used)
    return entries, bad


def _cost(e):
    """What an entry counts: its settled use, else its whole reservation."""
    return e["used"] if e["used"] is not None else e["reserved"]


class _Gate:
    """What both gates share: the ledger entries, the rows written, the call in flight, and the 429 streak."""

    provider = unit = None

    def __init__(self, model, rows, sink, max_429, estimate, clock, sleep):
        self.model, self.sink, self.max_429 = model, sink, max_429
        self.estimate, self.clock, self.sleep = estimate, clock, sleep
        self.entries, self.bad_rows = load_entries(rows, self.provider)
        self.body = self.call_id = self.current = None
        self.attempt = 0
        self.consecutive_429 = 0
        self.last_wait_s = self.waited_s = 0.0

    def begin_call(self, body, call_id):
        """The request the next attempts send (provider_backend.ProviderBackend.chat calls it before each call)."""
        self.body, self.call_id, self.attempt = body, call_id, 0

    def _bad_rows_stop(self):
        return ("config", f"the ledger holds {self.bad_rows} {self.provider} quota row(s) without a readable time or "
                          f"amount, so today's count cannot be trusted; restore the file or start a new --ledger")

    def _write(self, row):
        if self.sink is not None:
            self.sink(row)

    def _reserve(self, amount):
        """Count one attempt before it is sent: an entry, and a quota row written ahead of the request."""
        now = self.clock()
        self.attempt += 1
        self.current = {"ts": now, "model": self.model, "reserved": float(amount), "used": None}
        self.entries[(str(self.call_id), self.attempt)] = self.current
        self._write({"budget_event": "quota", "provider": self.provider, "model": self.model, "call_id": self.call_id,
                     "attempt": self.attempt, "unit": self.unit, "reserved": round(float(amount), 6),
                     "ts": _dt.datetime.fromtimestamp(now, _dt.timezone.utc).isoformat(timespec="seconds")})

    def _settle(self, used, status):
        """Settle the attempt in flight at `used` (None keeps its reservation) and write the settle row."""
        e = self.current
        if e is None:
            return
        if used is not None:
            e["used"] = float(used)
        self._write({"budget_event": "quota_settle", "provider": self.provider, "model": self.model,
                     "call_id": self.call_id, "attempt": self.attempt, "unit": self.unit,
                     "used": round(_cost(e), 6), "status": status if isinstance(status, int) else None,
                     "ts": _dt.datetime.fromtimestamp(self.clock(), _dt.timezone.utc).isoformat(timespec="seconds")})

    def note_response(self, status):
        """Count 429s in a row (any other status resets the count); True when the streak reached max_429."""
        self.consecutive_429 = self.consecutive_429 + 1 if status == 429 else 0
        return self.max_429 is not None and self.consecutive_429 >= self.max_429

    def streak_message(self):
        return (f"{self.consecutive_429} 429s in a row (as HTTP 429 or inside an HTTP 200): stopping to spare the "
                f"quota; resume later with --resume")

    def _wait(self, seconds):
        self.sleep(seconds)
        self.waited_s += seconds
        self.last_wait_s += seconds

    def _cost_stop(self, data):
        """A reported cost above 0 is money: neither provider's free tier reports one."""
        usage = data.get("usage") if isinstance(data, dict) else None
        cost = usage.get("cost") if isinstance(usage, dict) else None
        if cost is not None and not exact_zero(cost):
            return ("not_free", f"the response reports usage.cost {_shown(cost)}: the free tier charges nothing, so "
                                f"this account or organisation is not on it; check the provider's billing page")
        return None


# ── Groq ─────────────────────────────────────────────────────────────────────

class GroqGate(_Gate):
    """Groq's free plan for one model (see the module docs). ``limits`` are the plan's figures (rpm, rpd, tpm, tpd),
    ``caps`` the run's own (at most the limits); ``reserve`` requests of the server's daily count stay unused."""

    provider, unit = "groq", "tokens"

    def __init__(self, model, limits, caps, rows=(), sink=None, reserve=5, max_429=3, estimate=None,
                 clock=time.time, sleep=time.sleep):
        super().__init__(model, rows, sink, max_429, estimate, clock, sleep)
        self.limits = {k: int(limits[k]) for k in ("rpm", "rpd", "tpm", "tpd")}
        self.caps = {k: int(caps[k]) for k in ("rpm", "rpd", "tpm", "tpd")}
        self.reserve = reserve
        # The last reply's x-ratelimit-* view: requests left today (lowered locally per attempt) and tokens left in
        # the current minute, each with its reset time.
        self.server_requests_left = self.server_requests_reset_at = None
        self.server_tokens_left = self.server_tokens_reset_at = None
        self.tier_problem = None

    def _mine(self, now, window):
        return [e for e in self.entries.values() if e["model"] == self.model and now - e["ts"] < window]

    def need(self):
        """Tokens one attempt may use at most: the prompt estimate plus the output cap."""
        prompt, cap = self.estimate(self.body)
        return prompt + cap

    def _day_stop(self, now, day, need, what):
        """The stop when the 24-hour window is full: the time enough of it leaves for the next attempt to fit."""
        ordered = sorted(day, key=lambda e: e["ts"])
        used = sum(_cost(e) for e in day)
        if what == "requests":
            k = len(day) + 1 - self.caps["rpd"]
        else:
            k, left = 0, used
            while k < len(ordered) and left + need > self.caps["tpd"]:
                left -= _cost(ordered[k])
                k += 1
        free_at = ordered[max(0, min(k, len(ordered)) - 1)]["ts"] + DAY_S if ordered else now
        return ("quota", f"the day's allowance for {self.model} in this ledger is used: {len(day)} requests and "
                         f"{used:.0f} tokens in the last 24 hours (caps {self.caps['rpd']} and {self.caps['tpd']}; "
                         f"Groq's free plan allows {self.limits['rpd']} and {self.limits['tpd']}), and the next attempt "
                         f"needs up to {need:.0f} tokens; resume after {iso_z(free_at)} with the same command plus "
                         f"--resume")

    def allowance_stop(self):
        """At start: a stop when the ledger already holds the day's allowance, else None."""
        if self.bad_rows:
            return self._bad_rows_stop()
        now = self.clock()
        day = self._mine(now, DAY_S)
        if len(day) >= self.caps["rpd"]:
            return self._day_stop(now, day, 0, "requests")
        if sum(_cost(e) for e in day) >= self.caps["tpd"]:
            return self._day_stop(now, day, 0, "tokens")
        return None

    def before_attempt(self):
        """None to send (the attempt counted first), or (kind, message) to stop the call unsent."""
        self.last_wait_s = 0.0
        if self.bad_rows:
            return self._bad_rows_stop()
        need = self.need()
        if need > self.caps["tpm"]:
            return ("config", f"one attempt of this run may use up to {need:.0f} tokens (the prompt estimate plus the "
                              f"output cap), above the per-minute token cap of {self.caps['tpm']}: lower --num-predict, "
                              f"or --est-tokens-per-byte after a measured preflight")
        for _ in range(MAX_WAIT_ROUNDS):
            now = self.clock()
            day = self._mine(now, DAY_S)
            if len(day) + 1 > self.caps["rpd"]:
                return self._day_stop(now, day, need, "requests")
            if sum(_cost(e) for e in day) + need > self.caps["tpd"]:
                return self._day_stop(now, day, need, "tokens")
            if self.server_requests_left is not None and self.server_requests_left - self.reserve <= 0:
                when = self.server_requests_reset_at
                return ("quota", f"Groq reports {self.server_requests_left} requests left today for {self.model} "
                                 f"(x-ratelimit-remaining-requests; {self.reserve} kept in reserve for other use of the "
                                 f"organisation); resume after {iso_z(when) if when else next_utc_midnight(now)} with "
                                 f"the same command plus --resume")
            minute = self._mine(now, WINDOW_S)
            wait = 0.0
            if len(minute) + 1 > self.caps["rpm"] or sum(_cost(e) for e in minute) + need > self.caps["tpm"]:
                wait = min(e["ts"] for e in minute) + WINDOW_S - now + 0.05
            elif self.server_tokens_left is not None and self.server_tokens_left < need and \
                    self.server_tokens_reset_at is not None and now < self.server_tokens_reset_at:
                # The organisation's own minute (other runs, other machines): wait for its reset, at most one window;
                # after it the reply's view is stale.
                wait = min(self.server_tokens_reset_at - now, WINDOW_S) + 0.05
                self.server_tokens_left = None
            if wait <= 0:
                break
            self._wait(wait)
        else:
            return ("rate_limited", f"the per-minute caps found no room after {MAX_WAIT_ROUNDS} waits; resume later with "
                                    f"--resume")
        self._reserve(need)
        if self.server_requests_left is not None:
            self.server_requests_left -= 1
        return None

    def after_attempt(self, status, headers, raw):
        """Settle the attempt from the reply's usage, and read the x-ratelimit-* headers and the free-plan check."""
        now = self.clock()
        data = json_or_none(raw)
        used = None
        if status == 200 and isinstance(data, dict):
            prompt, out = output_tokens(data.get("usage"))
            used = None if prompt is None else prompt + out
        elif status in UNBILLED or is_redirect(status):
            used = 0
        self._settle(used, status)
        h = headers or {}
        limit_req, limit_tok = header_int(h.get("x-ratelimit-limit-requests")), header_int(h.get("x-ratelimit-limit-tokens"))
        if (limit_req is not None and limit_req > self.limits["rpd"]) or (
                limit_tok is not None and limit_tok > self.limits["tpm"]):
            self.tier_problem = (f"Groq reports limits above the Free plan for {self.model} ({limit_req} requests a day, "
                                 f"{limit_tok} tokens a minute; the plan's are {self.limits['rpd']} and "
                                 f"{self.limits['tpm']}): the organisation is on a paid tier or has raised limits, where "
                                 f"requests can be billed; check console.groq.com/settings/billing before any run")
        left = header_int(h.get("x-ratelimit-remaining-requests"))
        if left is not None:
            reset = go_duration(h.get("x-ratelimit-reset-requests"))
            self.server_requests_left = left
            self.server_requests_reset_at = now + reset if reset is not None else None
        left = header_int(h.get("x-ratelimit-remaining-tokens"))
        if left is not None:
            reset = go_duration(h.get("x-ratelimit-reset-tokens"))
            self.server_tokens_left = left
            self.server_tokens_reset_at = now + (reset if reset is not None else WINDOW_S)

    def classify_429(self, headers, data, now, retry_after=None):
        return groq_classify_429(headers, data, now, retry_after)

    def response_stop(self, data, answered):
        """(fatal kind, error) when an HTTP 200 shows that money could be spent, else None."""
        if self.tier_problem:
            return ("not_free", self.tier_problem)
        stop = self._cost_stop(data)
        if stop:
            return stop
        if answered and data.get("model") != self.model:
            return ("not_free", f"the response was served by model {_shown(data.get('model'))}, not {self.model}: "
                                f"another model has other limits and may be billed")
        return None

    def status(self):
        """Fields for the call record."""
        now = self.clock()
        minute, day = self._mine(now, WINDOW_S), self._mine(now, DAY_S)
        return {"requests_minute": len(minute), "requests_24h": len(day),
                "tokens_minute": round(sum(_cost(e) for e in minute), 1), "tokens_24h": round(sum(_cost(e) for e in day), 1),
                "server_requests_left": self.server_requests_left, "server_tokens_left": self.server_tokens_left,
                "rate_wait_s": round(self.last_wait_s, 3)}

    def caps_record(self):
        return {"limits": dict(self.limits), "caps": dict(self.caps), "daily_reserve": self.reserve}

    def start_line(self):
        now = self.clock()
        day = self._mine(now, DAY_S)
        return (f"groq: {self.model} on the free plan ({self.limits['rpm']} requests and {self.limits['tpm']} tokens a "
                f"minute, {self.limits['rpd']} requests and {self.limits['tpd']} tokens a day); this run keeps at most "
                f"{self.caps['rpm']} and {self.caps['tpm']} a minute, {self.caps['rpd']} and {self.caps['tpd']} in any "
                f"24 hours; this ledger holds {len(day)} requests and {sum(_cost(e) for e in day):.0f} tokens of the "
                f"last 24 hours")

    def summary_line(self):
        now = self.clock()
        day = self._mine(now, DAY_S)
        server = (f"; Groq's last reply: {self.server_requests_left} requests left today"
                  if self.server_requests_left is not None else "")
        return (f"groq: {len(day)} requests and {sum(_cost(e) for e in day):.0f} tokens for {self.model} in the last 24 "
                f"hours in this ledger (caps {self.caps['rpd']} and {self.caps['tpd']}){server}")


# ── Cloudflare ───────────────────────────────────────────────────────────────

class NeuronGate(_Gate):
    """Cloudflare's daily neuron allocation for the account (see the module docs). ``rates`` are the model's neurons
    per million tokens ({"in", "out"}), ``cap`` the neurons a UTC day may count, ``rpm`` the requests a minute,
    ``per_day`` an optional cap on requests a UTC day."""

    provider, unit = "cloudflare", "neurons"

    def __init__(self, model, rates, cap, rpm, per_day=None, rows=(), sink=None, max_429=3, estimate=None,
                 source=None, clock=time.time, sleep=time.sleep):
        super().__init__(model, rows, sink, max_429, estimate, clock, sleep)
        self.rates = {"in": float(rates["in"]), "out": float(rates["out"])}
        self.cap, self.rpm, self.per_day, self.source = float(cap), int(rpm), per_day, source
        self.last_used = self.last_reserved = self.overrun = None

    def need(self):
        """Neurons one attempt may use at most: prompt estimate x in-rate + output cap x out-rate, per million."""
        prompt, cap = self.estimate(self.body)
        return prompt * self.rates["in"] / 1e6 + cap * self.rates["out"] / 1e6

    def _today(self, now):
        """Today's entries (UTC day) of every model: the free allocation is the account's."""
        day = utc_day(now)
        return [e for e in self.entries.values() if utc_day(e["ts"]) == day]

    def _day_stop(self, now, used, need):
        return ("quota", f"today's neuron budget is used: {used:.2f} of {self.cap:g} neurons on {utc_day(now).isoformat()}"
                         f" (UTC) in this ledger, every model of the account together, and the next call needs up to "
                         f"{need:.2f}; Cloudflare's free allocation resets at 00:00 UTC: resume after "
                         f"{next_utc_midnight(now)} with the same command plus --resume")

    def allowance_stop(self):
        if self.bad_rows:
            return self._bad_rows_stop()
        now = self.clock()
        used = sum(_cost(e) for e in self._today(now))
        return self._day_stop(now, used, 0.0) if used >= self.cap else None

    def before_attempt(self):
        self.last_wait_s = 0.0
        if self.bad_rows:
            return self._bad_rows_stop()
        need = self.need()
        if need > self.cap:
            return ("config", f"one call's worst case is {need:.2f} neurons ({self.model}: the prompt estimate x "
                              f"{self.rates['in']:g} + the output cap x {self.rates['out']:g} per million tokens), above "
                              f"the day's cap of {self.cap:g}: lower --num-predict, or raise --max-neurons-per-day "
                              f"(at most the free allocation)")
        for _ in range(MAX_WAIT_ROUNDS):
            now = self.clock()
            today = self._today(now)
            used = sum(_cost(e) for e in today)
            if used + need > self.cap + 1e-9:
                return self._day_stop(now, used, need)
            if self.per_day is not None and len(today) + 1 > self.per_day:
                return ("quota", f"{len(today)} requests today (UTC) in this ledger reach --max-requests-per-day "
                                 f"{self.per_day}; resume after {next_utc_midnight(now)} with --resume")
            minute = [e for e in self.entries.values() if now - e["ts"] < WINDOW_S]
            if len(minute) + 1 <= self.rpm:
                break
            self._wait(min(e["ts"] for e in minute) + WINDOW_S - now + 0.05)
        else:
            return ("rate_limited", f"the per-minute cap found no room after {MAX_WAIT_ROUNDS} waits; resume later with "
                                    f"--resume")
        self._reserve(need)
        self.last_reserved = need
        return None

    def after_attempt(self, status, headers, raw):
        """Settle the attempt at its usage priced by the table; a price above the worst case is kept for
        ``response_stop``."""
        data = json_or_none(raw)
        used = None
        if status == 200 and isinstance(data, dict):
            used = neurons_for(data.get("usage"), self.rates)
        elif status in UNBILLED or is_redirect(status):
            used = 0.0
        self._settle(used, status)
        self.last_used = used if used is not None else self.last_reserved
        if used is not None and self.last_reserved is not None and used > self.last_reserved * (1 + 1e-9) + 1e-9:
            self.overrun = (f"the call used {used:.2f} neurons by its usage and the table's rates, above its worst case "
                            f"of {self.last_reserved:.2f}: the table's rates ({self.source or 'the neuron table'}) or the "
                            f"output cap do not hold for {self.model} on this endpoint; check both before any further run")

    def classify_429(self, headers, data, now, retry_after=None):
        return cloudflare_classify_429(headers, data, now, retry_after)

    def response_stop(self, data, answered):
        if self.overrun:
            return ("cost_anomaly", self.overrun)
        return self._cost_stop(data)

    def status(self):
        now = self.clock()
        return {"neurons_call": None if self.last_used is None else round(self.last_used, 6),
                "neurons_today": round(sum(_cost(e) for e in self._today(now)), 6), "neuron_cap": self.cap,
                "requests_minute": sum(1 for e in self.entries.values() if now - e["ts"] < WINDOW_S),
                "rate_wait_s": round(self.last_wait_s, 3)}

    def caps_record(self):
        return {"neuron_rates": dict(self.rates), "neurons_per_day": self.cap, "rpm": self.rpm,
                "requests_per_day": self.per_day}

    def start_line(self):
        now = self.clock()
        used = sum(_cost(e) for e in self._today(now))
        return (f"cloudflare: {self.model} at {self.rates['in']:g} / {self.rates['out']:g} neurons per million tokens in "
                f"/ out; this ledger counts {used:.2f} of {self.cap:g} neurons today (UTC, the whole account); at most "
                f"{self.rpm} requests a minute")

    def summary_line(self):
        now = self.clock()
        used = sum(_cost(e) for e in self._today(now))
        return (f"cloudflare: {used:.2f} of {self.cap:g} neurons counted today (UTC) in this ledger; compare with the "
                f"Workers AI page of the dashboard")
