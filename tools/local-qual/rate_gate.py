#!/usr/bin/env python3
"""Client-side request caps for the ``openai`` backend: per minute, per UTC day, and the 429 rules (tools/local-qual).

What it owns
------------
* ``RateGate``, consulted before every attempt: at most ``rpm`` attempts in any rolling minute; at most ``per_day``
  attempts per UTC day counted from the ledger's write-ahead rows (so every run sharing the ledger counts, and a
  resume carries the count); the account's own remaining free requests less a reserve; a key poll every few
  attempts (free_mode.py supplies it: it stops the run if the key's usage moves); and a stop after several HTTP 429
  in a row.
* ``classify_429`` and ``reset_seconds``: which 429 is the daily quota (terminal), the per-minute window (wait for
  the reset) or a saturated upstream provider (bounded backoff honouring Retry-After).
* The UTC-day helpers (the free quota resets at 00:00 UTC).

How it fits
-----------
cloud_backend.py calls ``RateGate.before_attempt`` and ``note_response`` around every attempt and
``classify_429`` on every 429 when a gate is attached; free_mode.py builds the gate at the start of a free-only run;
cloud_run.py builds a plain one for a paid run given ``--rpm`` or ``--max-requests-per-day``. Standard library only.

Sources (read 2026-09-27)
-------------------------
https://openrouter.ai/docs/api_reference/limits : 20 requests per minute for ``:free`` variants; 50 per day while
fewer than 10 credits were ever bought, 1,000 with 10 or more; account-wide (more keys do not raise them).
https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key : ``free_model_daily_requests`` resets at
UTC midnight. The 429 body and headers (``X-RateLimit-Reset`` in epoch milliseconds, a daily reset exactly at 00:00
UTC) are as reported in litellm issue 9035; the daily-cap message ``free-models-per-day`` is quoted in public bug
reports; whether failed requests count toward the day is not documented, so every attempt counts here.
"""
import datetime as _dt
import json
import math
import time
from collections import deque

# OpenRouter's per-minute limit for ":free" variants, and the client cap kept two requests under it.
FREE_RPM_LIMIT = 20
FREE_RPM_DEFAULT = 18
# 50 free requests per UTC day while fewer than 10 credits were ever bought; the default keeps 5 in reserve.
FREE_DAILY_DEFAULT = 45
DAILY_RESERVE_DEFAULT = 5
# The key is read at least every this many attempts, so a charge is seen within a few requests.
KEY_POLL_EVERY_DEFAULT = 10
KEY_POLL_EVERY_MAX = 10
MAX_CONSECUTIVE_429_DEFAULT = 3
# An X-RateLimit-Reset further away than this is the daily cap, not the per-minute window.
DAILY_RESET_MIN_S = 300.0
# The rolling window of the per-minute cap, in seconds.
WINDOW_S = 60.0
# A header value above EPOCH_MS_MIN is epoch milliseconds (as OpenRouter sends X-RateLimit-Reset); above
# EPOCH_S_MIN, epoch seconds; below, a delay in seconds.
EPOCH_MS_MIN = 1e12
EPOCH_S_MIN = 1e9
# Ledger times are written in whole seconds (budget.py truncates them), so an attempt stamped S was sent in [S, S+1);
# the window seeded from the ledger places it at S + LEDGER_TS_RESOLUTION_S, its latest possible time, so a resumed run
# never drops it from the minute early.
LEDGER_TS_RESOLUTION_S = 1.0


# ── UTC days ─────────────────────────────────────────────────────────────────

def utc_day(epoch):
    return _dt.datetime.fromtimestamp(epoch, _dt.timezone.utc).date()


def _next_midnight(epoch):
    day = utc_day(epoch) + _dt.timedelta(days=1)
    return _dt.datetime(day.year, day.month, day.day, tzinfo=_dt.timezone.utc)


def next_utc_midnight(epoch):
    """The next 00:00 UTC after ``epoch``, as ISO text (when OpenRouter's daily free counter resets)."""
    return _next_midnight(epoch).isoformat().replace("+00:00", "Z")


def seconds_to_midnight(epoch):
    return max(0.0, _next_midnight(epoch).timestamp() - epoch)


# ── 429s ─────────────────────────────────────────────────────────────────────

def reset_seconds(value, now):
    """Seconds until an X-RateLimit-Reset value: epoch milliseconds (as observed), epoch seconds, or a delay."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v) or v < 0:
        return None
    if v > EPOCH_MS_MIN:
        v /= 1000.0
    return max(0.0, v - now) if v > EPOCH_S_MIN else v


def classify_429(headers, data, now, retry_after=None):
    """(kind, seconds to wait or None) for an HTTP 429.

    ``daily``: the free daily quota (a message naming a per-day limit, such as "free-models-per-day", or a reset more
    than DAILY_RESET_MIN_S away): terminal, never retried, since a retry only burns the quota. ``minute``:
    OpenRouter's per-minute limit (X-RateLimit-* headers, reset soon): wait for the reset. ``upstream``: the
    provider donating the capacity is saturated (the metadata names it, or the text says upstream): bounded backoff
    that honours Retry-After.
    """
    err = data.get("error") if isinstance(data, dict) and isinstance(data.get("error"), dict) else {}
    meta = err.get("metadata") if isinstance(err.get("metadata"), dict) else {}
    text = (str(err.get("message") or "") + " " + json.dumps(meta, ensure_ascii=False)[:800]).lower()
    h = headers or {}
    reset = reset_seconds(h.get("x-ratelimit-reset"), now)
    if "per-day" in text or "per day" in text or "perday" in text or (reset is not None and reset > DAILY_RESET_MIN_S):
        return "daily", reset if reset is not None else seconds_to_midnight(now)
    if meta.get("provider_name") or meta.get("provider_code") or "upstream" in text:
        return "upstream", retry_after
    if reset is not None or "x-ratelimit-limit" in h:
        return "minute", reset if reset is not None else retry_after
    return "upstream", retry_after


# ── The gate ─────────────────────────────────────────────────────────────────

def _row_epoch(row):
    try:
        return _dt.datetime.fromisoformat(str(row.get("ts")).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


class RateGate:
    """Client-side request caps, asked before every attempt (cloud_backend.py ``chat``).

    * **Per minute.** At most ``rpm`` attempts in any rolling ``WINDOW_S`` seconds; the gate sleeps until the oldest
      one leaves the window. The window starts from the ledger's reserve rows of the last minute, so a quick resume
      cannot burst.
    * **Per UTC day.** Every attempt counts (429s and errors too: whether OpenRouter counts failed requests is not
      documented, so the count is conservative). ``per_day`` caps the attempts this ledger records today; the
      account's own ``free_model_daily_requests.remaining`` less ``reserve`` caps them too, lowered locally per
      attempt and re-read at each key poll (the lower figure wins: other tools may share the account). A new UTC day
      resets the local count and forces a poll.
    * **Key poll.** ``poll()`` returns (stop or None, the account's daily counter); it runs every ``poll_every``
      attempts and on a new day.
    * **429 streak.** ``note_response`` counts HTTP 429 in a row across calls; at ``max_429`` the run stops.

    ``before_attempt`` returns None to send, or (kind, message) to stop without sending: ``quota`` (nothing left
    today), or whatever the poll returns (``not_free``, ``config``). ``clock`` and ``sleep`` are injectable for tests.
    """

    def __init__(self, rpm=None, per_day=None, reserve=0, rows=(), server=None, poll=None,
                 poll_every=KEY_POLL_EVERY_DEFAULT, max_429=None, clock=time.time, sleep=time.sleep):
        self.rpm, self.per_day, self.reserve = rpm, per_day, reserve
        self.poll, self.poll_every, self.max_429 = poll, poll_every, max_429
        self.clock, self.sleep = clock, sleep
        now = clock()
        self.day = utc_day(now)
        times = [t for t in (_row_epoch(r) for r in rows if r.get("budget_event") == "reserve") if t is not None]
        # Attempts already written to the ledger today, and those of the last minute (write-ahead rows: one per send),
        # each at the latest time its whole-second stamp allows.
        self.used_local = sum(1 for t in times if utc_day(t) == self.day)
        late = [t + LEDGER_TS_RESOLUTION_S for t in times if t <= now]  # a stamp in the future is not an attempt yet
        self.window = deque(sorted(t for t in late if now - t < WINDOW_S))
        self.server_remaining = server.get("remaining") if isinstance(server, dict) else None
        self.server = dict(server) if isinstance(server, dict) else None
        self.since_poll = 0
        self.consecutive_429 = 0
        self.waited_s = 0.0
        self.last_wait_s = 0.0

    def remaining_today(self):
        """Attempts still allowed today (None when neither cap applies)."""
        caps = []
        if self.per_day is not None:
            caps.append(self.per_day - self.used_local)
        if self.server_remaining is not None:
            caps.append(self.server_remaining - self.reserve)
        return min(caps) if caps else None

    def quota_message(self):
        now = self.clock()
        return (f"the day's request allowance is used up: {self.used_local} attempts on {self.day.isoformat()} (UTC) "
                f"in this ledger (cap {self.per_day}), {self.server_remaining} free requests left on the account "
                f"({self.reserve} kept in reserve); resume after {next_utc_midnight(now)} with the same command plus "
                f"--resume")

    def sync(self):
        """Run the key poll now; returns a stop tuple or None (and keeps the lower remaining count)."""
        stop, server = self.poll()
        self.since_poll = 0
        if stop is not None:
            return stop
        if isinstance(server, dict) and isinstance(server.get("remaining"), int):
            self.server = dict(server)
            est = self.server_remaining
            self.server_remaining = server["remaining"] if est is None else min(est, server["remaining"])
        return None

    def _day_and_allowance(self, now):
        """Roll over to a new UTC day if ``now`` is in one, run a due key poll, and check the day's allowance.

        Returns a stop tuple or None. A new day (the quota reset at 00:00 UTC) resets the local count and forces a
        poll, so the account's own counter for the new day is read before anything is sent.
        """
        if utc_day(now) != self.day:
            self.day, self.used_local, self.server_remaining = utc_day(now), 0, None
            self.since_poll = self.poll_every
        if self.poll is not None and self.since_poll >= self.poll_every:
            stop = self.sync()
            if stop is not None:
                return stop
        left = self.remaining_today()
        if left is not None and left <= 0:
            return "quota", self.quota_message()
        return None

    def before_attempt(self):
        now = self.clock()
        self.last_wait_s = 0.0
        stop = self._day_and_allowance(now)
        if stop is not None:
            return stop
        # ── Per-minute window: wait until the oldest attempt leaves it ──
        if self.rpm:
            while self.window and now - self.window[0] >= WINDOW_S:
                self.window.popleft()
            if len(self.window) >= self.rpm:
                wait = self.window[0] + WINDOW_S - now + 0.05
                self.sleep(wait)
                self.waited_s += wait
                self.last_wait_s = wait
                now = self.clock()
                while self.window and now - self.window[0] >= WINDOW_S:
                    self.window.popleft()
                # The wait may have crossed 00:00 UTC: the attempt belongs to the new day, whose counter is read first.
                if utc_day(now) != self.day:
                    stop = self._day_and_allowance(now)
                    if stop is not None:
                        return stop
        # ── Count the attempt before it is sent (a crash after the send can only over-count) ──
        self.window.append(now)
        self.used_local += 1
        if self.server_remaining is not None:
            self.server_remaining -= 1
        self.since_poll += 1
        return None

    def note_response(self, status):
        """Count HTTP 429 in a row (any other answer resets the streak); True when the streak reached max_429."""
        self.consecutive_429 = self.consecutive_429 + 1 if status == 429 else 0
        return self.max_429 is not None and self.consecutive_429 >= self.max_429

    def status(self):
        """Fields for the call record."""
        return {"attempts_today": self.used_local, "requests_left_today": self.remaining_today(),
                "rate_wait_s": round(self.last_wait_s, 3)}
