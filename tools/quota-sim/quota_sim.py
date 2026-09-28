#!/usr/bin/env python3
"""Quota simulator: replays a Wilco "user day" against free-tier limits and upstream 429 congestion.

What it owns
    A small, deterministic, seeded discrete-event replay of one user day of Wilco workflow runs against model
    endpoints that have request, token and credit limits, plus a model of upstream (host-side) congestion. It
    answers the owner's question of 2026-09-27: if free providers rate-limit us, does the day still finish, how
    long does the user wait, and which routing strategy keeps the experience within our standards?

Where it fits
    tools/cost-model/cost_model.py counts calls and tokens per workflow. The research workload profile arranges
    those decisions into layers and user days (data/workload.json). This tool adds time: concurrency, per-minute
    windows, daily caps, retries, fallbacks and congestion. Endpoints, limits and routing plans come from
    data/limits.json. Results feed the rate-limit research doc (docs/research/52-rate-limits-and-ux.md). Stdlib
    only; no network; it never calls a model or reads a key.

The model in one paragraph
    A day is a sequence of blocks (workflow runs, or 30-minute sessions of 12 requests). A run is a list of layers of
    mutually independent decisions; layers run in sequence, and inside a layer calls run in phases (first samples,
    repair rounds, then any cascade stage), each phase waiting for the previous one, as in the research profile.
    The strategy routes each call to a local model or to cloud endpoints. A cloud endpoint belongs to a quota pool
    (one per account or per model, as the provider scopes it) and to an upstream host that flips between clear and
    congested (a two-state Markov chain); a congested host answers most attempts with a fast 429.

Determinism
    Each random draw is a keyed hash (urand) of the seed and a stable key (decision, sample, attempt), or comes
    from a per-host random.Random seeded with a string. The same (day, strategy, congestion, seed) always gives the
    same result, and every strategy sees the same decisions, repairs, escalations and host histories.

Allocation profile
    The whole day is expanded once at start (a few thousand small objects); the event heap holds one entry per
    pending event. Every scenario of the full grid runs in well under a minute.
"""
import argparse
import hashlib
import heapq
import json
import math
import os
import sys

from quota_pools import Endpoint, Host, Pool, ideal_endpoint

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")

# ── Harness constants ([I] unless marked; every one is a knob for a later measurement) ───────────────────────
STALL_S = 10.0           # doc 53 section 1.1: L3 budget, interactive creative steps within 10 s; longer is a stall
LONG_STALL_S = 60.0      # a second, harsher stall threshold for the report
PATIENCE_S = 60.0        # an interactive call waits at most this long, then keeps the code default (doc 25 10.1)
BACKOFF_BASE_S = 2.0     # doc 51 Z16: retries 2 s doubling to 60 s with jitter, 10 retries
BACKOFF_CAP_S = 60.0
BACKOFF_RETRIES = 10
DRIP_S = 180.0           # after 10 retries a background call probes every ~3 min, like the round-0 drip [V-obs]
COOLDOWN_BASE_S = 15.0   # S3+: an endpoint that returned an upstream 429 is skipped for 15 s, doubling to 600 s
COOLDOWN_CAP_S = 600.0
RANK_PENALTY_S = 1.0     # a lower-preference free endpoint must be able to start 1 s sooner per rank to be chosen
PAID_AFTER_S = {True: 10.0, False: 120.0}  # S6: paid only when no free endpoint can start within 10 s (the user is
                         # waiting; doc 53's L3 budget) or 2 min (background); compared on start times, no rank penalty
LAT_JITTER_LO, LAT_JITTER_SPAN = 0.8, 0.5  # [I] each answered call takes 0.8-1.3 x its step kind's placeholder
                         # latency (uniform, keyed per call), so calls of one phase do not all settle at one instant
RESERVE = 0.3            # S3+: background work leaves 30% of every daily allowance to interactive steps
PACK = 4                 # S1+ proposal: bulk independent text slots per request (needs an owner decision)
PACK_LATENCY_STEP = 0.25  # each extra slot in a packed call adds 25% to its latency
REUSE_EXPLAIN = 0.25     # S1+ [U]: explanations answered from the exact-hash memo (doc 40 R13)
SKIP_INTENT = 0.5        # S1+ [U]: intent Fills skipped because a gesture, menu or palette started the step (doc 53 DP-01)
SLACK_S = 3600.0         # the day's horizon is its planned hours plus one hour
EPS_S = 1e-6             # time tolerance: `ready + 60` recomputed later can differ in the last bit; without it a
                         # call rescheduled "at its deadline" can miss the deadline check and loop at one instant
MAX_EVENTS = 5_000_000   # forward-progress guard: a full heavy day needs well under 1% of this

# ── Strategies ───────────────────────────────────────────────────────────────────────────────────────────────
# cloud_k: "standard" = doc 25 Standard K (Pick 3, creative 2); "k1" = one sample, validators and repairs kept.
# local: None, "gpu" (a 3-4B GPU model for Pick/Fill at Standard K) or "cascade" (doc 53 section 4.3 tiny stage).
# plan: routing plan in limits.json ("single": one endpoint and per-call backoff; "multi": quota- and
# congestion-aware routing over the user's own accounts). tier: OpenRouter :free daily tier.
STRATEGIES = {
    "REF": dict(desc="reference only: Standard effort on one unlimited, never-congested endpoint (not a product option)",
                cloud_k="standard", R=2, reduce=False, local=None, plan="ideal", tier="free50", paid=False, reserve=0.0),
    "S0": dict(desc="one free provider (OpenRouter :free, 50/day), Standard effort, retry with backoff",
               cloud_k="standard", R=2, reduce=False, local=None, plan="single", tier="free50", paid=False, reserve=0.0),
    "S1": dict(desc="S0 + call reduction: K = 1 with validators and repairs, packed bulk text, memo reuse, no-model path",
               cloud_k="k1", R=2, reduce=True, local=None, plan="single", tier="free50", paid=False, reserve=0.0),
    "S2": dict(desc="S1 + a local 3-4B GPU model for Pick/Fill (Standard K locally); text, Compose, Explain on S0's route",
               cloud_k="k1", R=2, reduce=True, local="gpu", plan="single", tier="free50", paid=False, reserve=0.0),
    "S3": dict(desc="S1 + quota- and congestion-aware routing across the user's own free accounts, qualified per step kind",
               cloud_k="k1", R=2, reduce=True, local=None, plan="multi", tier="free50", paid=False, reserve=RESERVE),
    "S4": dict(desc="S3 + tiny local cascade for Pick/Fill (CPU; 20% re-ask, 23% escalated to S3's routing)",
               cloud_k="k1", R=2, reduce=True, local="cascade", plan="multi", tier="free50", paid=False, reserve=RESERVE),
    "S4-noGroq": dict(desc="S4 without the Groq account (its fictional-military-content answer is pending, doc 50)",
                      cloud_k="k1", R=2, reduce=True, local="cascade", plan="multi", tier="free50", paid=False,
                      reserve=RESERVE, exclude=("groq",)),
    "S5-single": dict(desc="S1 with OpenRouter's 1,000/day tier: does buying 10 credits alone fix one free provider?",
                      cloud_k="k1", R=2, reduce=True, local=None, plan="single", tier="credits10", paid=False,
                      reserve=0.0),
    "S5": dict(desc="S4 with OpenRouter's 1,000/day tier (10 credits bought once, about 10.80 USD)",
               cloud_k="k1", R=2, reduce=True, local="cascade", plan="multi", tier="credits10", paid=False, reserve=RESERVE),
    "S6": dict(desc="S5 + a cheap paid pinned endpoint as last resort under a hard daily cap",
               cloud_k="k1", R=2, reduce=True, local="cascade", plan="multi", tier="credits10", paid=True, reserve=RESERVE),
}
KINDS = ("PICK", "FILL", "TEXT", "COMPOSE", "EXPLAIN")


# ── Deterministic randomness ─────────────────────────────────────────────────────────────────────────────────
def urand(*key):
    """Uniform [0, 1) from a keyed hash: a counter-based draw that no other draw can shift (see module docs)."""
    h = hashlib.blake2b("|".join(map(str, key)).encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(h, "big") / 2.0 ** 64


def load_data(data_dir=DATA_DIR):
    """Load the two data files; returns (workload, limits) as plain dicts."""
    with open(os.path.join(data_dir, "workload.json"), encoding="utf-8") as fh:
        work = json.load(fh)
    with open(os.path.join(data_dir, "limits.json"), encoding="utf-8") as fh:
        limits = json.load(fh)
    return work, limits


# ── Expanding decisions into calls ───────────────────────────────────────────────────────────────────────────
def stages_for(strat, kind, Kc, consts):
    """Where one decision's calls go: a list of (target, K, fraction of decisions that reach this stage).

    Pick and Fill may run locally (S2's GPU model at Standard K, or doc 53's cascade: tiny model once, a 20% re-ask,
    23% escalated to the cloud at K = 1). Everything else, and everything in S0/S1/S3, goes to the cloud router."""
    std = consts["presets"]["standard"]
    k_std = std["K_pick"] if Kc == "pick" else std["K_creative"] if Kc == "creative" else 1
    k_cloud = k_std if strat["cloud_k"] == "standard" else 1
    if kind in ("PICK", "FILL"):
        if strat["local"] == "gpu":
            return [("local-gpu-4b", k_std, 1.0)]
        if strat["local"] == "cascade":
            return [("local-cpu-tiny", 1, 1.0), ("local-cpu-tiny", 1, consts["P_REASK"]),
                    ("cloud", 1, consts["P_CASCADE"])]
    return [("cloud", k_cloud, 1.0)]


def no_model_share(strat, item):
    """Share of an item's decisions answered without a model call (S1+ reductions; zero otherwise)."""
    if not strat["reduce"]:
        return 0.0
    if item["decision_kind"] == "intent":
        return SKIP_INTENT
    if item["shape"] == "explain":
        return REUSE_EXPLAIN
    return 0.0


def pack_size(strat, item):
    """Bulk independent text slots share one request under S1+ (1 = no packing)."""
    return PACK if (strat["reduce"] and item["bulk"] and item["shape"] == "fill_text") else 1


def packed_tokens(item, pack, cached_share):
    """Tokens of one call carrying `pack` slots: the frozen prefix is sent once, the rest once per slot [I]."""
    tin = item["tin"] * (1 + (pack - 1) * (1 - cached_share))
    return tin, item["tout"] * pack


def expected_calls(work, name, strat):
    """Expected cloud and local calls of one run of workload `name` (the analytic twin of the sampled plan).

    calls = decisions x reach x K x (1 + r + ... + r^R), the cost model's arithmetic; the unit tests check it
    against the research profile's cross-check rows."""
    consts, kinds = work["constants"], work["step_kind_map"]
    w = work["workloads"][name]
    layer_lists = [req["layers"] for req in w["requests"]] if w["kind"] == "session" else [w["layers"]]
    out = {"cloud": 0.0, "local": 0.0}
    for layers in layer_lists:
        for L in layers:
            for it in L["items"]:
                n = it["n"] * (1 - no_model_share(strat, it))
                pack = pack_size(strat, it)
                r = consts["repair_rate"][it["shape"]]
                if pack > 1:
                    n = math.ceil(it["n"] / pack)
                    r = 1 - (1 - r) ** pack
                rep = sum(r ** i for i in range(1, strat["R"] + 1))
                for target, K, frac in stages_for(strat, kinds[it["shape"]], it["Kc"], consts):
                    out["cloud" if target == "cloud" else "local"] += n * frac * K * (1 + rep)
    return out


class Decision:
    """One decision (or one pack of bulk text slots) with its pre-drawn stages and repair needs."""
    __slots__ = ("key", "kind", "shape", "n", "interactive", "tin", "tout", "cached", "stages", "flags", "alive",
                 "answered", "outcomes")

    def __init__(self, key, kind, shape, n, interactive, tin, tout, cached, stages, flags):
        self.key, self.kind, self.shape, self.n, self.interactive = key, kind, shape, n, interactive
        self.tin, self.tout, self.cached = tin, tout, cached
        self.stages = stages      # [(target, K)] for the stages this decision reaches
        self.flags = flags        # flags[stage][sample][round - 1]: that repair round is needed
        self.alive = [[False] * K for _, K in stages]
        self.answered = False     # at least one first-stage sample was served
        self.outcomes = set()     # reasons of unserved calls ("parked", "gave_up", "cut")

    def calls_for_phase(self, p, R, finding, variant):
        """Calls of phase p: stage p // (R + 1); round 0 = the K samples, round j = repairs still alive."""
        si, j = divmod(p, R + 1)
        if si >= len(self.stages):
            return []
        target, K = self.stages[si]
        if j == 0:
            tin = self.tin + (variant if K > 1 else 0)
            return [Call(self, si, s, 0, target, tin, self.tout) for s in range(K)]
        return [Call(self, si, s, j, target, self.tin + finding + self.tout, self.tout)
                for s in range(K) if self.alive[si][s] and self.flags[si][s][j - 1]]


class Call:
    """One model request: a sample or a repair of one decision stage."""
    __slots__ = ("dec", "stage", "sample", "round", "target", "tin", "tout", "ready", "start", "n429", "attempts",
                 "layer")

    def __init__(self, dec, stage, sample, rnd, target, tin, tout):
        self.dec, self.stage, self.sample, self.round, self.target = dec, stage, sample, rnd, target
        self.tin, self.tout = tin, tout
        self.ready = self.start = None
        self.n429 = self.attempts = 0
        self.layer = None

    @property
    def key(self):
        return f"{self.dec.key}|{self.stage}|{self.sample}|{self.round}"


def build_decisions(work, strat, item, key, interactive, cached, seed):
    """Expand one layer item into Decision objects, drawing no-model skips, cascade reach and repairs by hash."""
    consts, kinds = work["constants"], work["step_kind_map"]
    kind, R = kinds[item["shape"]], strat["R"]
    pack = pack_size(strat, item)
    r = consts["repair_rate"][item["shape"]]
    tin, tout = packed_tokens(item, pack, cached)
    if pack > 1:
        r = 1 - (1 - r) ** pack
    out, skipped = [], 0
    stage_defs = stages_for(strat, kind, item["Kc"], consts)
    groups = ([min(pack, item["n"] - i) for i in range(0, item["n"], pack)] if pack > 1 else [1] * item["n"])
    for d, size in enumerate(groups):
        dkey = f"{key}|{d}"
        if pack == 1 and urand(seed, dkey, "nomodel") < no_model_share(strat, item):
            skipped += 1
            continue
        stages, flags = [], []
        for si, (target, K, frac) in enumerate(stage_defs):
            if frac < 1.0 and urand(seed, dkey, "reach", si) >= frac:
                continue
            stages.append((target, K))
            fl = []
            for s in range(K):
                need, rounds = True, []
                for j in range(R):
                    need = need and urand(seed, dkey, "repair", si, s, j) < r
                    rounds.append(need)
                fl.append(rounds)
            flags.append(fl)
        out.append(Decision(dkey, kind, item["shape"], size, interactive, tin, tout, cached, stages, flags))
    return out, skipped


def build_day(work, strat, day, seed, day_name="day"):
    """Expand every block of a day into units -> layers -> decisions (the whole plan, before any call runs)."""
    blocks = []
    for bi, b in enumerate(day["blocks"]):
        w = work["workloads"][b["workload"]]
        # The cached share prices Groq's cache credit and packed calls. It depends on the effort: at K = 1 there is no
        # per-decision breakpoint shared by sibling samples, so less of each prompt is a cache hit (cost model,
        # doc 40 section 4.1). Using the Standard share for K = 1 strategies overstated Groq's token headroom.
        cached = w["designed_cached_share_k1"] if strat["cloud_k"] == "k1" else w["designed_cached_share"]
        units = []
        reqs = w["requests"] if w["kind"] == "session" else [dict(label=b["workload"], layers=w["layers"])]
        for ui, req in enumerate(reqs):
            layers = []
            for li, L in enumerate(req["layers"]):
                inter = w["interactive"] or L["phase"] == "foreground"
                decs, skipped = [], 0
                for ii, it in enumerate(L["items"]):
                    d, s = build_decisions(work, strat, it, f"{day_name}|{bi}|{ui}|{li}|{ii}", inter, cached, seed)
                    decs += d
                    skipped += s
                layers.append(dict(decisions=decs, skipped=skipped, interactive=inter, gate_s=L["gate_s"]))
            units.append(dict(label=req["label"], layers=layers))
        blocks.append(dict(workload=b["workload"], planned=b["start_s"], units=units,
                           spacing=w.get("spacing_s", 0), session=w["kind"] == "session"))
    return blocks


# ── Endpoints, pools and routing plans ───────────────────────────────────────────────────────────────────────
def build_routes(limits, strat, congestion, seed):
    """Create pools, hosts and endpoints for one run and resolve the strategy's routing plan per step kind."""
    locals_ = {eid: Endpoint(eid, spec, None, None) for eid, spec in limits["endpoints"].items() if spec.get("local")}
    if strat["plan"] == "ideal":
        ep = ideal_endpoint()
        return {k: [ep] for k in KINDS}, locals_, {"ideal": ep.pool}
    pools = {pid: Pool(pid, spec, strat["tier"], strat["reserve"]) for pid, spec in limits["pools"].items()}
    profiles, hosts, eps = limits["congestion_profiles"], {}, {}
    if congestion not in limits["congestion_levels"]:
        raise ValueError(f"unknown congestion level {congestion!r}")
    level = limits["congestion_levels"][congestion]
    for eid, spec in limits["endpoints"].items():
        if spec.get("local"):
            continue
        prof = profiles[level[spec["congestion"]]]   # the level maps the endpoint's congestion class to a profile
        if spec["host"] not in hosts:
            hosts[spec["host"]] = Host(prof, f"{seed}|host|{spec['host']}", profiles["fail_latency_s"])
        eps[eid] = Endpoint(eid, spec, pools[spec["pool"]], hosts[spec["host"]])
    plans = {}
    for kind in KINDS:
        ids = [i for i in limits["routing_plans"][strat["plan"]][kind]
               if eps[i].provider not in strat.get("exclude", ())]
        if strat["paid"]:
            ids.append(limits["routing_plans"]["paid_fallback"])
        # strict on structure: a plan may only name endpoints screened as plausible for that step kind, and never
        # one a product rule takes out of every route list (for example D046's zero-retention default)
        bad = [i for i in ids if kind not in eps[i].kinds or eps[i].excluded_by]
        if bad:
            raise ValueError(f"routing plan {strat['plan']!r} sends {kind} to ineligible or excluded endpoints {bad}")
        plans[kind] = [eps[i] for i in ids]
    for target in ("local-gpu-4b", "local-cpu-tiny"):
        if target in locals_ and not {"PICK", "FILL"} <= locals_[target].kinds:
            raise ValueError(f"local endpoint {target} is not eligible for PICK and FILL")
    return plans, locals_, pools


def choose(plans, call, now):
    """Pick the endpoint that can start this call soonest (plus a small rank penalty); None when all are spent.

    'Header-driven' in practice: pools know their exact remaining allowance and window state, as the providers'
    rate-limit headers and OpenRouter's key endpoint report them. Returns (endpoint, earliest start) or (None, None).

    Free endpoints compete on start time plus RANK_PENALTY_S per rank, so the user's order wins when starts are
    close. The paid endpoint (S6) stays outside that contest: it is taken only when the earliest free start is more
    than PAID_AFTER_S away from its own start. Charging it the rank penalty too would move the threshold by the
    length of the route list (a regression test covers it)."""
    best = paid = earliest_free = None
    for rank, ep in enumerate(plans[call.dec.kind]):
        cost = ep.cost(call.tin, call.tout, call.dec.cached)
        if not ep.pool.has_daily(cost, background=not call.dec.interactive):
            continue
        s = ep.pool.ready_at(now, cost)
        if s is None:        # a single call larger than the per-minute token cap can never run there
            continue
        s = max(s, ep.cooldown_until)
        if ep.paid:
            if paid is None or s < paid[0]:
                paid = (s, ep)
            continue
        earliest_free = s if earliest_free is None else min(earliest_free, s)
        score = s + rank * RANK_PENALTY_S
        if best is None or score < best[0]:
            best = (score, s, ep)
    # the last resort: no free route can start soon enough (or none has allowance left) and the cap still allows it
    if paid is not None and (earliest_free is None or earliest_free > paid[0] + PAID_AFTER_S[call.dec.interactive]):
        return paid[1], paid[0]
    return (best[2], best[1]) if best else (None, None)


# ── The discrete-event simulation ────────────────────────────────────────────────────────────────────────────
class Sim:
    """One day x strategy x congestion x seed. Call run() once, then read summary()."""

    def __init__(self, work, limits, day, strat_name, congestion, seed, day_name="day", stall_s=STALL_S):
        self.work, self.strat, self.seed = work, STRATEGIES[strat_name], seed
        self.name = dict(day=day_name, strategy=strat_name, congestion=congestion, seed=seed)
        self.consts = work["constants"]
        self.stall_s = stall_s
        self.blocks = build_day(work, self.strat, day, seed, day_name)
        self.horizon = day["planned_hours"] * 3600.0 + SLACK_S
        self.plans, self.locals, self.pools = build_routes(limits, self.strat, congestion, seed)
        self.heap, self.seq, self.t = [], 0, 0.0
        self.cloud_free = self.consts["cloud_concurrency"]
        self.queue = {True: [], False: []}      # interactive first, FIFO within each class
        self.local_queue = {k: [] for k in self.locals}
        self.local_busy = {k: False for k in self.locals}
        self.inflight = set()
        self.kicked = False
        self.m = dict(waits=[], stalls=0, long_stalls=0, served_by={}, fallbacks=0, reroutes=0, upstream_429=0,
                      attempts=0, blocks_done=0, day_end=None)

    # event plumbing
    def at(self, t, fn, *args):
        """Schedule fn(*args) at simulated time t; the sequence number keeps same-time events in FIFO order."""
        heapq.heappush(self.heap, (t, self.seq, fn, args))
        self.seq += 1

    def kick(self):
        """Ask for one dispatch pass at the current time (avoids deep recursion when many calls settle at once)."""
        if not self.kicked:
            self.kicked = True
            self.at(self.t, self.pump)

    def run(self):
        """Pop events in time order until the heap is empty or the horizon passes; MAX_EVENTS guards progress.

        Events past the horizon are left unrun: their calls count as 'cut' and their waits so far are reported."""
        self.at(0.0, self.start_block, 0)
        events = 0
        while self.heap:
            t, _, fn, args = heapq.heappop(self.heap)
            if t > self.horizon:
                break
            events += 1
            if events > MAX_EVENTS:
                raise RuntimeError(f"no forward progress: {events} events by t = {t:.1f} s ({self.name})")
            self.t = t
            fn(*args)
        self.m["events"] = events
        return self

    # blocks, units, layers, phases
    def start_block(self, bi):
        """Start block bi (its planned time has come or the previous block ended); past the last block, end the day."""
        if bi >= len(self.blocks):
            self.m["day_end"] = self.t
            return
        b = self.blocks[bi]
        b["t0"] = self.t
        self.start_unit(bi, 0)

    def start_unit(self, bi, ui):
        """Start unit ui of block bi (a session request, or the whole run); after the last, schedule the next block."""
        b = self.blocks[bi]
        if ui >= len(b["units"]):
            self.m["blocks_done"] += 1
            b["t_end"] = self.t
            nxt = bi + 1
            start = max(self.blocks[nxt]["planned"], self.t) if nxt < len(self.blocks) else self.t
            self.at(start, self.start_block, nxt)
            return
        # a session request starts on its slot or when the user has the previous answer, whichever is later
        start = max(self.t, b["t0"] + ui * b["spacing"]) if b["session"] else self.t
        self.at(start, self.start_layer, bi, ui, 0)

    def start_layer(self, bi, ui, li):
        """Start layer li of a unit: reset its phase bookkeeping and release its first phase of calls."""
        layers = self.blocks[bi]["units"][ui]["layers"]
        if li >= len(layers):
            self.start_unit(bi, ui + 1)
            return
        L = layers[li]
        L.update(pos=(bi, ui, li), phase=-1, pending=0, wait=0.0)
        L["max_phase"] = max((len(d.stages) * (self.strat["R"] + 1) for d in L["decisions"]), default=0)
        self.next_phase(L)

    def next_phase(self, L):
        """Advance layer L to its next phase that has calls (a barrier: every call of the previous phase settled).

        Phases with no calls (no repair needed, no decision reaching that cascade stage) are skipped. After the last
        phase the layer's user gate (premise pick, outline approval) runs, then the next layer starts."""
        R, c = self.strat["R"], self.consts
        while True:
            L["phase"] += 1
            if L["phase"] >= L["max_phase"]:
                bi, ui, li = L["pos"]
                self.at(self.t + L["gate_s"], self.start_layer, bi, ui, li + 1)
                return
            calls = [x for d in L["decisions"]
                     for x in d.calls_for_phase(L["phase"], R, c["finding_tokens"], c["variant_note_tokens"])]
            if calls:
                break
        L["pending"], L["wait"] = len(calls), 0.0
        for x in calls:
            x.layer, x.ready = L, self.t
            self.inflight.add(x)
            if x.target == "cloud":
                self.queue[x.dec.interactive].append(x)
            else:
                self.local_queue[x.target].append(x)
        self.kick()

    # dispatch
    def pump(self):
        """One dispatch pass: start one call on each idle local model, then fill free cloud concurrency slots.

        Calls the user waits on leave the queue first. A cloud call keeps its slot from here until it settles,
        including while it waits for a per-minute window, a cooldown or a backoff [I, conservative: a real
        scheduler could release the slot while a call backs off]. A call still queued for a slot is not timed
        out until it gets one, so an interactive wait can pass PATIENCE_S by the time a slot frees (at most 0.5 s
        in the shipped grid; the forward-progress test bounds it at 1 s)."""
        self.kicked = False
        for k, q in self.local_queue.items():
            if q and not self.local_busy[k]:
                x = q.pop(0)
                self.local_busy[k] = True
                x.start = self.t
                lat = self.locals[k].latency_s[x.dec.shape] * (LAT_JITTER_LO + LAT_JITTER_SPAN
                                                               * urand(self.seed, x.key, "lat"))
                self.at(self.t + lat, self.local_done, x, k)
        while self.cloud_free > 0 and (self.queue[True] or self.queue[False]):
            x = (self.queue[True] or self.queue[False]).pop(0)
            self.cloud_free -= 1
            self.route(x)

    def local_done(self, x, k):
        """A local model finished call x: free the model and record the answer (local models never refuse)."""
        self.local_busy[k] = False
        self.settle(x, True, self.locals[k])

    def route(self, x):
        """Send, wait for, or give up on one cloud call that holds a concurrency slot."""
        deadline = x.ready + PATIENCE_S
        if x.dec.interactive and self.t >= deadline - EPS_S:
            return self.settle(x, False, reason="gave_up")
        ep, start = choose(self.plans, x, self.t)
        if ep is None:            # every eligible allowance is spent: the run parks until the reset (BudgetLimited)
            return self.settle(x, False, reason="parked")
        if start > self.t + EPS_S:
            if x.dec.interactive and start > deadline:
                return self.at(deadline, self.route, x)
            return self.at(start, self.route, x)
        cost = ep.cost(x.tin, x.tout, x.dec.cached)
        x.attempts += 1
        self.m["attempts"] += 1
        if ep.host is not None and ep.host.fails(self.t, urand(self.seed, x.key, "attempt", x.attempts)):
            ep.pool.admit(self.t, cost, ok=False)   # counts toward the per-minute window, not the daily cap [V-obs]
            self.m["upstream_429"] += 1
            return self.at(self.t + ep.host.fail_latency(urand(self.seed, x.key, "fail", x.attempts)),
                           self.on_429, x, ep)
        ep.pool.admit(self.t, cost, ok=True)
        x.start = self.t
        pack_mult = 1 + PACK_LATENCY_STEP * (x.dec.n - 1)
        lat = (self.consts["latency_cloud_s"][x.dec.shape] * pack_mult
               * (LAT_JITTER_LO + LAT_JITTER_SPAN * urand(self.seed, x.key, "lat")))
        self.at(self.t + lat, self.on_ok, x, ep)

    def on_ok(self, x, ep):
        """An answered attempt: clear the endpoint's strike count (its next 429 starts a fresh 15-s cooldown)."""
        ep.consecutive_429 = 0
        self.settle(x, True, ep)

    def on_429(self, x, ep):
        """An upstream 429 came back: multi-route cools the endpoint and re-routes; single-route backs off and retries.

        The backoff follows doc 51 Z16 (2 s doubling to 60 s, equal jitter, 10 retries, then a probe every 3 min);
        a call the user waits on never backs off past its patience limit."""
        x.n429 += 1
        if self.strat["plan"] == "multi":
            # congestion-aware: the endpoint cools down for every call, and this call is re-routed at once
            ep.consecutive_429 += 1
            ep.cooldown_until = self.t + min(COOLDOWN_CAP_S, COOLDOWN_BASE_S * 2 ** (ep.consecutive_429 - 1))
            self.m["reroutes"] += 1
            return self.route(x)
        base = DRIP_S if x.n429 > BACKOFF_RETRIES else min(BACKOFF_CAP_S, BACKOFF_BASE_S * 2 ** (x.n429 - 1))
        delay = base / 2 + urand(self.seed, x.key, "backoff", x.n429) * base / 2   # "equal jitter"
        if x.dec.interactive:     # the user's patience ends the wait; route() then keeps the default
            delay = min(delay, max(0.0, x.ready + PATIENCE_S - self.t))
        self.at(self.t + delay, self.route, x)

    def settle(self, x, served, ep=None, reason=None):
        """Record one finished call and advance its layer when the phase is complete."""
        self.inflight.discard(x)
        if x.target == "cloud":
            self.cloud_free += 1
        dec, L = x.dec, x.layer
        wait = (x.start if served else self.t) - x.ready
        self.m["waits"].append((wait, dec.interactive))
        if served:
            dec.alive[x.stage][x.sample] = True
            if x.stage == 0:
                dec.answered = True
            self.m["served_by"][ep.eid] = self.m["served_by"].get(ep.eid, 0) + 1
            plan = self.plans.get(dec.kind, [])
            if x.target == "cloud" and plan and ep is not plan[0]:
                self.m["fallbacks"] += 1
        else:
            dec.alive[x.stage][x.sample] = False
            dec.outcomes.add(reason)
        if dec.interactive:
            L["wait"] = max(L["wait"], wait)
        L["pending"] -= 1
        if L["pending"] == 0:
            if dec.interactive and L["wait"] > self.stall_s:
                self.m["stalls"] += 1
            if dec.interactive and L["wait"] > LONG_STALL_S:
                self.m["long_stalls"] += 1
            self.next_phase(L)
        self.kick()

    # ── Reporting ────────────────────────────────────────────────────────────────────────────────────────────
    def summary(self):
        """Metrics of the finished run (see README for definitions)."""
        from quota_report import summarize
        return summarize(self)


def run_one(work, limits, day_name, strat_name, congestion, seed, stall_s=STALL_S):
    """Run one named user day under one strategy, congestion level and seed; returns the summary dict."""
    day = work["user_days"][day_name]
    return Sim(work, limits, day, strat_name, congestion, seed, day_name, stall_s).run().summary()


def main(argv=None):
    """CLI: one run printed as JSON, or --all for the whole grid written to the paths given (never the repository)."""
    from quota_report import run_grid, write_markdown
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--day", help="one user day (see data/workload.json user_days)")
    ap.add_argument("--strategy", default="S4", choices=sorted(STRATEGIES))
    ap.add_argument("--congestion", default="observed", help="profile for OpenRouter :free hosts")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--all", action="store_true", help="run every strategy x congestion x day x seed")
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--stall-s", type=float, default=STALL_S)
    ap.add_argument("--out", help="write the grid results as JSON here")
    ap.add_argument("--md", help="write the grid summary table as Markdown here")
    a = ap.parse_args(argv)
    work, limits = load_data()
    if not a.all:
        res = run_one(work, limits, a.day or "light-session", a.strategy, a.congestion, a.seed, a.stall_s)
        json.dump(res, sys.stdout, indent=1)
        print()
        return 0
    grid = run_grid(work, limits, a.seeds, a.stall_s)
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(grid, fh, indent=1)
    if a.md:
        write_markdown(grid, a.md)
    print(f"{len(grid['runs'])} runs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
