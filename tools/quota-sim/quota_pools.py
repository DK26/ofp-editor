"""Quota pools, upstream hosts and endpoints for tools/quota-sim.

What it owns
    The three stateful pieces a model request meets on its way out: the quota pool that meters it (per account or
    per model, as the provider scopes its limits), the upstream host that may be congested, and the endpoint that
    ties a model to both and prices a call in the pool's units (requests, tokens, neurons, USD).

Where it fits
    quota_sim.py builds one set per simulated day from data/limits.json and asks the pools "can this call start,
    and when?" before every attempt. All queries arrive in non-decreasing simulated time (the event loop
    guarantees it), which is what lets the sliding windows prune from the left.
"""
import random
from collections import deque

WINDOW_S = 60.0   # per-minute limits (RPM, TPM) are modelled as sliding 60-s windows [I; providers do not say]


class Pool:
    """Request, token, neuron and credit allowances of one provider scope, with per-minute sliding windows.

    Daily and monthly caps refuse a call outright (it parks until the reset); per-minute caps delay it. With a
    reserve > 0, background calls may use only (1 - reserve) of each daily allowance, keeping the rest for steps
    the user is waiting on."""

    def __init__(self, pid, spec, tier="free50", reserve=0.0):
        rpd = spec.get("rpd")
        self.pid = pid
        self.rpm, self.tpm = spec.get("rpm"), spec.get("tpm")
        self.caps = dict(req=rpd.get(tier) if isinstance(rpd, dict) else rpd, tok=spec.get("tpd"),
                         neurons=spec.get("neurons_per_day"),
                         usd=spec.get("usd_per_month", spec.get("usd_cap_per_day")))
        self.used = dict(req=0, tok=0.0, neurons=0.0, usd=0.0)
        self.reserve = reserve
        self.win = deque()          # (time, counted tokens) per attempt inside the last 60 s
        self.win_tok = 0.0

    def has_daily(self, cost, background=False):
        """True when the call fits every daily or monthly cap (minus the interactive reserve for background work)."""
        share = (1.0 - self.reserve) if background else 1.0
        for field, cap in self.caps.items():
            if cap is not None and self.used[field] + cost[field] > cap * share + 1e-9:
                return False
        return True

    def _prune(self, t):
        # the 1e-9 s tolerance lets an entry leave exactly at ts + 60 despite floating-point rounding
        while self.win and self.win[0][0] <= t - WINDOW_S + 1e-9:
            self.win_tok -= self.win.popleft()[1]

    def ready_at(self, t, cost):
        """Earliest time >= t at which the per-minute windows admit this call; None if it can never fit."""
        self._prune(t)
        tok = cost["tok"]
        if self.tpm is not None and tok > self.tpm:
            return None
        start = t
        if self.rpm is not None and len(self.win) >= self.rpm:
            # the oldest entries must leave the window until one request slot is free
            start = max(start, self.win[len(self.win) - self.rpm][0] + WINDOW_S)
        if self.tpm is not None and self.win_tok + tok > self.tpm:
            left = self.win_tok
            for ts, k in self.win:
                left -= k
                if left + tok <= self.tpm:
                    start = max(start, ts + WINDOW_S)
                    break
        return start

    def admit(self, t, cost, ok):
        """Record an attempt: every attempt fills the request window; only an answered one spends tokens and quota."""
        self._prune(t)
        tok = cost["tok"] if ok else 0.0
        self.win.append((t, tok))
        self.win_tok += tok
        if ok:
            for field in self.used:
                self.used[field] += cost[field]

    def left(self):
        """Remaining allowance per capped field (rounded for the report)."""
        return {f: round(c - self.used[f], 4) for f, c in self.caps.items() if c is not None}


class Host:
    """Upstream host congestion: a two-state (clear / congested) continuous-time Markov chain.

    Sojourn times are exponential with the profile's means, so the chain is memoryless and a fresh start is drawn
    from the stationary distribution. A congested host answers an attempt with a 429 with probability
    p429_congested (p429_clear otherwise), after a short fail-fast latency. Queries must come in time order."""

    def __init__(self, profile, rng_key, fail_latency_s=(0.35, 0.56)):
        self.p = profile
        self.rng = random.Random(rng_key)     # str seeds are hashed with SHA-512: stable across processes
        mc, ml = profile["mean_congested_s"], profile["mean_clear_s"]
        self.congested = self.rng.random() < mc / (mc + ml)
        self.until = self._dwell()
        self.lo, self.hi = fail_latency_s

    def _dwell(self):
        """How long the current state lasts: exponential with that state's mean (memoryless)."""
        return self.rng.expovariate(1.0 / (self.p["mean_congested_s"] if self.congested else self.p["mean_clear_s"]))

    def state(self, t):
        """True while congested at time t (advances the chain lazily)."""
        while t >= self.until:
            self.congested = not self.congested
            self.until += self._dwell()
        return self.congested

    def fails(self, t, u):
        """Whether an attempt at time t gets an upstream 429, given a uniform draw u in [0, 1)."""
        return u < (self.p["p429_congested"] if self.state(t) else self.p["p429_clear"])

    def fail_latency(self, u):
        """How long a refused attempt takes to come back: uniform over the observed 0.35-0.56 s [V-obs]."""
        return self.lo + (self.hi - self.lo) * u


class Endpoint:
    """One model at one provider: its pool, host, eligible step kinds and how a call is priced there."""

    ELIGIBLE = ("plausible", "measured-pass")   # screening readings accepted as 'qualified' for routing [I]

    def __init__(self, eid, spec, pool, host):
        self.eid, self.pool, self.host = eid, pool, host
        self.provider = spec.get("provider", "")
        self.kinds = {k for k, v in spec.get("kinds", {}).items() if v in self.ELIGIBLE}
        self.reasoning = spec.get("reasoning_tokens", 0)
        self.cache_credit = spec.get("cache_credit", False)
        self.neurons = spec.get("neurons_per_mtok")
        self.price = spec.get("usd_per_mtok")
        self.latency_s = spec.get("latency_s", {})
        self.paid = spec.get("pool") == "openrouter-paid"
        # A product rule that keeps this endpoint out of every route list (kept in the data to document why);
        # quota_sim.build_routes refuses a plan that names it.
        self.excluded_by = spec.get("excluded_by")
        # Cooldowns are per endpoint, not per host: when several of one provider's models share a congested host,
        # the router learns it once per model. Doc 52 section 5.2 proposes a per-host breaker; this is the more
        # conservative stand-in.
        self.cooldown_until = 0.0
        self.consecutive_429 = 0

    def cost(self, tin, tout, cached_share):
        """A call's cost in every unit a pool may meter.

        Groq does not count cached prompt tokens (automatic on gpt-oss), so its counted input drops by the run's
        cached share (the workflow's Standard-K or K = 1 share, chosen per strategy in quota_sim.build_day);
        mandatory reasoning tokens are counted as output [I, conservative]."""
        counted_in = tin * (1.0 - cached_share) if self.cache_credit else tin
        out = tout + self.reasoning
        neurons = (tin * self.neurons[0] + out * self.neurons[1]) / 1e6 if self.neurons else 0.0
        usd = (tin * self.price[0] + out * self.price[1]) / 1e6 if self.price else 0.0
        return dict(req=1, tok=counted_in + out, neurons=neurons, usd=usd)


def ideal_endpoint():
    """The REF baseline: one endpoint with no limits and no congestion (not a product option)."""
    spec = dict(provider="ideal", kinds={k: "plausible" for k in ("PICK", "FILL", "TEXT", "COMPOSE", "EXPLAIN")})
    return Endpoint("ideal", spec, Pool("ideal", {}), None)
