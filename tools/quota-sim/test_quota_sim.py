"""Unit tests for tools/quota-sim (run: python -m unittest discover -s tools/quota-sim, or python -m pytest).

What they prove: the data files are structurally sound, the decision expansion reproduces the research
profile's call counts exactly, the reference replay reproduces its day spans, pools/hosts/router enforce their
limits at both sides of every boundary, runs are deterministic, and no scenario can hang or overshoot the
interactive patience limit. Fixtures are built in memory from the tool's own data files; nothing touches the
network or a model.
"""
import copy
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import quota_pools as qp  # noqa: E402
import quota_report as qr  # noqa: E402
import quota_sim as qs  # noqa: E402

WORK, LIMITS = qs.load_data()


def one_block_day(workload, hours=1.0):
    """A synthetic day with one block at t = 0 (keeps end-to-end tests small and focused)."""
    return dict(planned_hours=hours, blocks=[dict(workload=workload, start_s=0)])


def run(day, strat, congestion="observed", seed=1, limits=None):
    """Run one synthetic day and return (sim, summary)."""
    sim = qs.Sim(WORK, limits or LIMITS, day, strat, congestion, seed, "test").run()
    return sim, sim.summary()


class FakeCall:
    """The two attributes choose() reads from a call, plus a decision-like stub."""

    def __init__(self, kind="PICK", tin=2000, tout=45, interactive=True, cached=0.6):
        self.tin, self.tout = tin, tout
        self.dec = type("D", (), dict(kind=kind, interactive=interactive, cached=cached))()


# ── Basic functionality: data integrity ──────────────────────────────────────────────────────────────────────
class DataIntegrity(unittest.TestCase):
    def test_every_strategy_and_level_builds_routes(self):
        """Every strategy x congestion level builds its pools and routing plans without error.

        Why: build_routes refuses a plan that sends a step kind to an endpoint not screened as plausible for it,
        so this also proves the shipped routing plans respect per-step-kind qualification."""
        for name in qs.STRATEGIES:
            for level in ("none", "moderate", "observed", "stress"):
                plans, _, _ = qs.build_routes(LIMITS, qs.STRATEGIES[name], level, 1)
                for kind, eps in plans.items():
                    self.assertTrue(eps, f"{name}/{kind} has no endpoint")
                    for ep in eps:
                        self.assertIn(kind, ep.kinds)

    def test_ineligible_plan_entry_is_refused(self):
        """A plan that sends COMPOSE to Granite Micro (screened 'no') raises ValueError naming the endpoint.

        Why: routing only to qualified (here: plausible) models per step kind is a product rule; the data must
        not be able to break it silently."""
        bad = copy.deepcopy(LIMITS)
        bad["routing_plans"]["multi"]["COMPOSE"].insert(0, "cf-granite-4.0-h-micro")
        with self.assertRaises(ValueError) as ctx:
            qs.build_routes(bad, qs.STRATEGIES["S3"], "observed", 1)
        self.assertIn("cf-granite-4.0-h-micro", str(ctx.exception))

    def test_plan_entry_excluded_by_a_product_rule_is_refused(self):
        """A plan that names an endpoint marked `excluded_by` (Gemma 4 :free, 55-day retention) raises ValueError.

        Why: D046 sends zdr: true by default and D045 item 7 never presets Google AI Studio's free tier, so a
        simulated route list that still reached that endpoint would overstate what the product may use. The data
        keeps the endpoint (it documents why it is out) but no plan may route to it."""
        self.assertTrue(LIMITS["endpoints"]["or-gemma-4-26b-a4b-free"].get("excluded_by"))
        for plan in ("single", "multi"):
            for kind, ids in LIMITS["routing_plans"][plan].items():
                self.assertNotIn("or-gemma-4-26b-a4b-free", ids, (plan, kind))
        bad = copy.deepcopy(LIMITS)
        bad["routing_plans"]["multi"]["TEXT"].append("or-gemma-4-26b-a4b-free")
        with self.assertRaises(ValueError) as ctx:
            qs.build_routes(bad, qs.STRATEGIES["S3"], "observed", 1)
        self.assertIn("or-gemma-4-26b-a4b-free", str(ctx.exception))

    def test_unknown_congestion_level_is_refused(self):
        """An unknown congestion level raises ValueError instead of silently using a default profile.

        Why: a typo on the command line must not produce a table that looks like a real scenario."""
        with self.assertRaises(ValueError):
            qs.build_routes(LIMITS, qs.STRATEGIES["S0"], "sunny", 1)

    def test_no_pool_is_shared_across_providers_or_duplicated_per_account(self):
        """Every endpoint's pool belongs to its own provider, and no provider has two accounts.

        Why: the scope rule (doc 50; D008) allows one account per provider, the user's own; pools are named per
        provider so a second account for the same provider would show up as a second pool family."""
        prefix = {"openrouter": "openrouter-", "groq": "groq-", "cloudflare": "cloudflare-", "huggingface": "hf-"}
        for eid, spec in LIMITS["endpoints"].items():
            if spec.get("local"):
                continue
            self.assertTrue(spec["pool"].startswith(prefix[spec["provider"]]), eid)
            self.assertIn(spec["pool"], LIMITS["pools"])


# ── Known-value cross-validation ─────────────────────────────────────────────────────────────────────────────
class KnownValues(unittest.TestCase):
    CONFIGS = {
        "B": dict(cloud_k="standard", R=2, reduce=False, local=None),
        "B-quick": dict(cloud_k="k1", R=1, reduce=False, local=None),
        "F": dict(cloud_k="standard", R=2, reduce=False, local="gpu"),
        "F-cascade": dict(cloud_k="standard", R=2, reduce=False, local="cascade"),
    }

    def test_expected_calls_match_research_profile(self):
        """expected_calls() reproduces the profile's cloud and local calls for every workflow and 4 strategies.

        Why: the simulator must count calls exactly as the cost model does (calls = n x K x (1 + r + r^2)), or
        every quota conclusion drifts. Reference: data/workload.json crosscheck rows (e.g. campaign B 650.4)."""
        for name, rows in WORK["crosscheck"]["rows"].items():
            for label, cfg in self.CONFIGS.items():
                got = qs.expected_calls(WORK, name, cfg)
                self.assertAlmostEqual(got["cloud"], rows[label]["cloud"], delta=0.06, msg=f"{name} {label} cloud")
                self.assertAlmostEqual(got["local"], rows[label]["local"], delta=0.06, msg=f"{name} {label} local")

    def test_reference_replay_matches_research_day_spans(self):
        """REF (no limits, no congestion) ends each user day within 0.5% of the profile's unthrottled span.

        Why: the timing model (layers, phases, 8 concurrent calls, gates, block starts) must agree with the
        profile it was derived from before limits and congestion are layered on."""
        for day, span in WORK["crosscheck"]["unthrottled_day_span_s"].items():
            r = qs.run_one(WORK, LIMITS, day, "REF", "none", 1)
            self.assertAlmostEqual(r["wall_time_s"], span, delta=0.005 * span, msg=day)

    def test_cached_shares_match_the_cost_model_at_both_efforts(self):
        """Each workload's cached share equals the cost model's designed-cache read share, at Standard K and at K = 1.

        Why: Groq does not count cached prompt tokens, so this share decides how many calls fit Groq's token caps.
        With K = 1 there is no per-decision cache breakpoint shared by sibling samples (doc 40 section 4.1), so the
        share drops (a session from 0.673 to 0.577); using the Standard share for K = 1 strategies overstated Groq's
        headroom. Reference: tools/cost-model strategy C on deepseek-flash (automatic prefix caching, like Groq's).

        How: derived workloads (re-rolls, re-runs) reuse the share of the workflow they re-run."""
        sys.path.insert(0, os.path.join(HERE, "..", "cost-model"))
        import cost_model as cm  # noqa: E402  (read-only import; the cost model writes nothing on import)
        parent = {"briefing-reroll-3": "write-briefing", "cutscene-rerun": "cutscene-director",
                  "mission-text-reroll": "campaign-from-brief"}
        for name, w in WORK["workloads"].items():
            wf = parent.get(name, name)
            for field, over in (("designed_cached_share", {}),
                                ("designed_cached_share_k1", dict(K_pick=1, K_creative=1))):
                t = cm.strategy(wf, "C", "deepseek-flash", dict(cm.KNOBS, **over)).as_dict()
                self.assertAlmostEqual(w[field], t["rd"] / t["input_tokens"], delta=0.0015, msg=f"{name} {field}")

    def test_k1_strategies_use_the_k1_cached_share(self):
        """S1 (cloud K = 1) prices every call with the K = 1 share; REF and S0 (Standard K) keep the Standard share.

        Why: the cache credit must follow the effort the strategy actually runs, or token-capped pools look larger
        than they are for every multi-route strategy (all of S3-S6 run K = 1 on the cloud)."""
        day = one_block_day("session-30min")
        w = WORK["workloads"]["session-30min"]
        for strat, field in (("S1", "designed_cached_share_k1"), ("REF", "designed_cached_share"),
                             ("S0", "designed_cached_share")):
            shares = {d.cached for bl in qs.build_day(WORK, qs.STRATEGIES[strat], day, 1) for u in bl["units"]
                      for L in u["layers"] for d in L["decisions"]}
            self.assertEqual(shares, {w[field]}, strat)
        self.assertLess(w["designed_cached_share_k1"], w["designed_cached_share"])

    def test_sampled_calls_track_expected_calls(self):
        """Over 20 seeds the sampled campaign averages within 2% of the expected 650.4 cloud calls.

        Why: repairs are drawn per call from the seed; the draw must be unbiased so seeds vary only noise."""
        n = [run(one_block_day("campaign-from-brief"), "REF", "none", seed)[1]["calls"]["cloud_served"]
             for seed in range(1, 21)]
        self.assertAlmostEqual(sum(n) / len(n), 650.4, delta=0.02 * 650.4)


# ── Determinism ──────────────────────────────────────────────────────────────────────────────────────────────
class Determinism(unittest.TestCase):
    def test_same_inputs_give_identical_results(self):
        """Two runs of the same day, strategy, congestion and seed serialise to identical JSON.

        Why: doc 52's tables are reproduced by re-running the grid; any hidden state (dict order, wall clock,
        unseeded randomness) would make a replay disagree with the published numbers."""
        a = qs.run_one(WORK, LIMITS, "mission-build", "S4", "stress", 2)
        b = qs.run_one(WORK, LIMITS, "mission-build", "S4", "stress", 2)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_strategies_with_equal_effort_share_every_decision_draw(self):
        """S1 and S3 expand the same seed into the same decisions, skips and repair flags.

        Why: strategy comparisons must differ only by routing, not by different random workloads."""
        day = WORK["user_days"]["mission-build"]
        a = qs.build_day(WORK, qs.STRATEGIES["S1"], day, 3)
        b = qs.build_day(WORK, qs.STRATEGIES["S3"], day, 3)
        flat = lambda blocks: [(d.key, d.stages, d.flags) for bl in blocks for u in bl["units"]
                               for L in u["layers"] for d in L["decisions"]]
        self.assertEqual(flat(a), flat(b))


# ── Boundary tests: pools ────────────────────────────────────────────────────────────────────────────────────
class PoolBoundaries(unittest.TestCase):
    COST = dict(req=1, tok=1000.0, neurons=0.0, usd=0.0)

    def test_rpm_window_admits_exactly_rpm_then_waits_for_the_oldest(self):
        """With rpm 20, twenty attempts at t = 0..19 are admitted at once; the 21st waits until t = 60.

        Why: both sides of the per-minute request limit (OpenRouter's 20 a minute); an off-by-one here would add
        or remove a whole minute of wait per burst."""
        p = qp.Pool("p", dict(rpm=20))
        for i in range(20):
            self.assertEqual(p.ready_at(float(i), self.COST), float(i))
            p.admit(float(i), self.COST, ok=True)
        self.assertAlmostEqual(p.ready_at(19.5, self.COST), 60.0)
        self.assertEqual(p.ready_at(60.0, self.COST), 60.0)   # the t = 0 entry leaves exactly at 60 s

    def test_tpm_cap_at_and_one_past_the_limit(self):
        """A call of exactly tpm tokens fits an empty window; tpm + 1 can never run (None).

        Why: a call larger than Groq's 8,000 tokens a minute is refused whatever the wait, so the router must skip
        that endpoint instead of waiting for a window that can never open."""
        p = qp.Pool("p", dict(tpm=8000))
        self.assertEqual(p.ready_at(0.0, dict(self.COST, tok=8000.0)), 0.0)
        self.assertIsNone(p.ready_at(0.0, dict(self.COST, tok=8001.0)))

    def test_tpm_window_delays_until_enough_tokens_expire(self):
        """With 8,000 TPM and 3 x 2,500 tokens at t = 0, 10, 20, a 2,500-token call waits until t = 60.

        Why: the token window must release the oldest entries first, and only as many as the new call needs."""
        p = qp.Pool("p", dict(tpm=8000))
        for t in (0.0, 10.0, 20.0):
            p.admit(t, dict(self.COST, tok=2500.0), ok=True)
        self.assertAlmostEqual(p.ready_at(21.0, dict(self.COST, tok=2500.0)), 60.0)

    def test_daily_cap_exact_and_failed_attempts_are_free(self):
        """rpd 50: the 50th answered call fits, the 51st does not; 429 attempts never spend the daily cap.

        Why: OpenRouter's counter did not move on 12 upstream 429s [V-obs]; the model must not double-charge."""
        p = qp.Pool("p", dict(rpd={"free50": 50, "credits10": 1000}))
        for _ in range(100):
            p.admit(0.0, self.COST, ok=False)
        for _ in range(49):
            p.admit(0.0, self.COST, ok=True)
        self.assertTrue(p.has_daily(self.COST))
        p.admit(0.0, self.COST, ok=True)
        self.assertFalse(p.has_daily(self.COST))
        self.assertEqual(p.left(), {"req": 0})
        self.assertEqual(qp.Pool("p", dict(rpd={"free50": 50, "credits10": 1000}), tier="credits10").caps["req"], 1000)

    def test_background_reserve_leaves_headroom_for_interactive_steps(self):
        """reserve 0.3 on 50/day: background work stops after 35 calls, interactive work continues to 50.

        Why: doc 52's design keeps part of every daily allowance for steps the user waits on, so a campaign's
        background text cannot leave the next interactive Pick with nothing."""
        p = qp.Pool("p", dict(rpd=50), reserve=0.3)
        for _ in range(35):
            p.admit(0.0, self.COST, ok=True)
        self.assertFalse(p.has_daily(self.COST, background=True))
        self.assertTrue(p.has_daily(self.COST, background=False))


# ── Congestion model ─────────────────────────────────────────────────────────────────────────────────────────
class Congestion(unittest.TestCase):
    def test_extreme_profiles(self):
        """p429 = 1 in both states always fails; p429 = 0 never does, at any time.

        Why: the Markov chain's state switching must not leak into the failure draw at the extremes."""
        always = dict(mean_congested_s=10, mean_clear_s=10, p429_congested=1.0, p429_clear=1.0)
        never = dict(always, p429_congested=0.0, p429_clear=0.0)
        a, n = qp.Host(always, "a"), qp.Host(never, "n")
        for t in range(0, 3600, 7):
            self.assertTrue(a.fails(float(t), 0.999))
            self.assertFalse(n.fails(float(t), 0.0))

    def test_observed_profile_reproduces_the_observed_failure_share(self):
        """The 'observed' profile fails about 12 of 13 attempts (0.92) when probed once a minute for hours.

        Why: it is calibrated to the only measured window (2026-09-27); a drift here would misstate S0-S2."""
        prof = LIMITS["congestion_profiles"]["observed"]
        fails = total = 0
        for seed in range(40):
            h = qp.Host(prof, f"{seed}|t")
            for i in range(600):
                fails += h.fails(i * 60.0, qs.urand(seed, i))
                total += 1
        self.assertAlmostEqual(fails / total, 12 / 13, delta=0.04)


# ── Router ───────────────────────────────────────────────────────────────────────────────────────────────────
class Router(unittest.TestCase):
    def endpoints(self, specs):
        """Endpoints with private pools and no host, from (id, pool spec, extra endpoint fields)."""
        out = []
        for eid, pool, extra in specs:
            spec = dict(provider="x", pool=extra.pop("pool", "free"), kinds={"PICK": "plausible"}, **extra)
            out.append(qp.Endpoint(eid, spec, qp.Pool(eid, pool), None))
        return {"PICK": out}

    def test_first_preference_wins_a_tie_and_spent_pools_are_skipped(self):
        """Equal start times go to the first endpoint; an endpoint with no daily quota is never chosen.

        Why: the user's route order must win when routes are equally ready, and a spent allowance is never tried."""
        plans = self.endpoints([("a", dict(rpd=0), {}), ("b", dict(rpd=5), {}), ("c", dict(rpd=5), {})])
        ep, start = qs.choose(plans, FakeCall(), 0.0)
        self.assertEqual((ep.eid, start), ("b", 0.0))

    def test_cooldown_moves_traffic_and_all_spent_parks(self):
        """A cooling endpoint loses to a free one; with every pool spent choose() returns (None, None).

        Why: routing around a throttled host is the design's first principle, and (None, None) is what parks a
        run instead of spinning on spent allowances."""
        plans = self.endpoints([("a", dict(rpd=5), {}), ("b", dict(rpd=5), {})])
        plans["PICK"][0].cooldown_until = 30.0
        self.assertEqual(qs.choose(plans, FakeCall(), 0.0)[0].eid, "b")
        spent = self.endpoints([("a", dict(rpd=0), {}), ("b", dict(tpd=10), {})])
        self.assertEqual(qs.choose(spent, FakeCall(), 0.0), (None, None))

    def test_call_larger_than_tpm_is_never_sent_there(self):
        """A 9,000-token call skips an 8,000-TPM endpoint even when it is first and idle.

        Why: a naive long prompt can never run on Groq Free; the router must not wait for it there."""
        plans = self.endpoints([("groq", dict(tpm=8000), {}), ("other", dict(), {})])
        self.assertEqual(qs.choose(plans, FakeCall(tin=8955, tout=45), 0.0)[0].eid, "other")

    def test_paid_is_last_resort_and_respects_the_hard_cap(self):
        """Paid loses to a free endpoint that starts within 10 s; wins when free waits a minute; never past cap.

        Why: the paid backstop is the user's own money under a hard daily cap (D026); it must be a last resort
        and must stop at the cap."""
        spec = dict(usd_per_mtok=[100.0, 100.0], pool="openrouter-paid")   # 2,045 tokens -> 0.2045 USD a call
        plans = self.endpoints([("free", dict(rpm=1), {}), ("paid", dict(usd_cap_per_day=1.0), dict(spec))])
        free, paid = plans["PICK"]
        self.assertEqual(qs.choose(plans, FakeCall(), 0.0)[0].eid, "free")
        free.pool.admit(0.0, dict(req=1, tok=0.0, neurons=0.0, usd=0.0), ok=True)   # free now waits until t = 60
        self.assertEqual(qs.choose(plans, FakeCall(), 1.0)[0].eid, "paid")
        paid.pool.used["usd"] = 0.999                                              # one more call breaks the cap
        self.assertEqual(qs.choose(plans, FakeCall(), 1.0)[0].eid, "free")

    def test_paid_threshold_is_10_s_whatever_the_list_length(self):
        """Paid wins when the earliest free start is more than 10 s away, even behind five spent free entries.

        Why (regression): the README and doc 52 section 3.1 state the rule as "paid only when free routes cannot
        start within 10 s (interactive) or 2 min (background)". The paid entry is appended after every free entry,
        so charging it the per-rank penalty as well moved the real threshold to 10 s + its rank (up to 17 s for
        Pick), and interactive calls waited longer than the stated rule before the backstop took over.

        How: free entry 'a' (rank 0) has used its one request a minute at t = 0, so it can start again at t = 60;
        five spent entries fill ranks 1-5; paid is rank 6. At t = 45 free is 15 s away (paid wins), at t = 50 it is
        exactly 10 s away (free wins: it can start within 10 s), and a background call waits up to 120 s."""
        spec = dict(usd_per_mtok=[0.07, 0.34], pool="openrouter-paid")
        plans = self.endpoints([("a", dict(rpm=1), {})] + [(f"spent{i}", dict(rpd=0), {}) for i in range(5)]
                               + [("paid", dict(usd_cap_per_day=1.0), dict(spec))])
        plans["PICK"][0].pool.admit(0.0, dict(req=1, tok=0.0, neurons=0.0, usd=0.0), ok=True)
        self.assertEqual(qs.choose(plans, FakeCall(), 45.0)[0].eid, "paid")
        self.assertEqual(qs.choose(plans, FakeCall(), 50.0), (plans["PICK"][0], 60.0))
        self.assertEqual(qs.choose(plans, FakeCall(interactive=False), 45.0)[0].eid, "a")


# ── End-to-end properties (research findings as regression anchors) ───────────────────────────────────────────
class EndToEnd(unittest.TestCase):
    def test_one_free_provider_cannot_carry_a_standard_session(self):
        """S0 on OpenRouter :free (50/day) serves at most 50 calls of a 60-call session and does not complete.

        Why: the research profile's headline (0.83 Standard sessions a day) must hold with no congestion at all."""
        _, r = run(WORK["user_days"]["light-session"], "S0", "none")
        self.assertLessEqual(r["calls"]["cloud_served"], 50)
        self.assertFalse(r["completed"])

    def test_multi_provider_cascade_finishes_the_measured_days(self):
        """S4 completes the light session and the mission build under the observed congestion for seeds 1-3.

        Why: this is doc 52's headline for the recommended free setup; a change that breaks it must be seen."""
        for day in ("light-session", "mission-build"):
            for seed in (1, 2, 3):
                self.assertTrue(qs.run_one(WORK, LIMITS, day, "S4", "observed", seed)["completed"], (day, seed))

    def test_everything_spent_parks_without_hanging(self):
        """With every cloud allowance at zero, S3 parks all cloud work at once and still finishes the day.

        Adversarial: zero quota everywhere is the degenerate input most likely to make a scheduler spin."""
        dry = copy.deepcopy(LIMITS)
        for spec in dry["pools"].values():
            for field in ("rpd", "tpd", "neurons_per_day", "usd_per_month", "usd_cap_per_day"):
                if field in spec:
                    spec[field] = {"free50": 0, "credits10": 0} if isinstance(spec[field], dict) else 0
        _, r = run(WORK["user_days"]["light-session"], "S3", "stress", limits=dry)
        self.assertTrue(r["day_finished"])
        self.assertEqual(r["calls"]["cloud_served"], 0)
        self.assertEqual(r["decisions"]["parked"] + r["decisions"]["no_model"], r["decisions"]["total"])

    def test_failed_escalation_keeps_the_tiny_answer_but_is_reported_as_degraded(self):
        """With every cloud allowance at zero, S4's escalated Picks keep the tiny stage's answer and count as degraded.

        Why: 'answered' means the first stage answered; a cascade escalation or repair that later fails leaves a
        low-confidence answer, not a model-confirmed one. The report must show those apart ('degraded') so a
        'Complete' cell cannot hide them, and the seed aggregate must carry the count into the Markdown table."""
        dry = copy.deepcopy(LIMITS)
        for spec in dry["pools"].values():
            for field in ("rpd", "tpd", "neurons_per_day", "usd_per_month", "usd_cap_per_day"):
                if field in spec:
                    spec[field] = {"free50": 0, "credits10": 0} if isinstance(spec[field], dict) else 0
        _, r = run(WORK["user_days"]["mission-build"], "S4", "observed", limits=dry)
        d = r["decisions"]
        self.assertGreater(d["answered_degraded"], 0)
        self.assertLessEqual(d["answered_degraded"], d["answered"])
        agg = qr.aggregate([r])[0]
        self.assertEqual(agg["degraded"], d["answered_degraded"])


# ── Security edge cases: forward progress and patience ───────────────────────────────────────────────────────
class ForwardProgress(unittest.TestCase):
    def test_every_scenario_terminates_and_respects_patience(self):
        """Every strategy x level x day (seed 1) ends within the event budget; interactive waits stay <= 61 s.

        Why (regression): a deadline recomputed as ready + 60 could miss the patience check by one float bit and
        reschedule itself at the same instant forever; and backoff could overshoot the 60-s patience."""
        for day in WORK["user_days"]:
            for strat in qs.STRATEGIES:
                for level in ("moderate", "observed", "stress"):
                    r = qs.run_one(WORK, LIMITS, day, strat, level, 1)
                    self.assertLessEqual(r["wait_s"]["interactive"]["max"] or 0, qs.PATIENCE_S + 1.0,
                                         (day, strat, level))

    def test_event_budget_raises_instead_of_hanging(self):
        """With the event budget cut to 100, a full day raises RuntimeError naming the run.

        Why: a scheduling bug must fail loudly with the scenario's name, never hang the grid."""
        saved = qs.MAX_EVENTS
        qs.MAX_EVENTS = 100
        try:
            with self.assertRaises(RuntimeError) as ctx:
                qs.run_one(WORK, LIMITS, "mission-build", "S0", "observed", 1)
            self.assertIn("forward progress", str(ctx.exception))
        finally:
            qs.MAX_EVENTS = saved

    def test_percentile_helper_edges(self):
        """Nearest-rank percentiles: empty -> None; one value -> itself; p50 of 1..4 -> 2; p90 of 1..10 -> 9.

        Why: the UX thresholds (p90 <= 2 s) are read off this helper; its boundary behaviour must be fixed."""
        self.assertIsNone(qr.pct([], 0.5))
        self.assertEqual(qr.pct([7.0], 0.9), 7.0)
        self.assertEqual(qr.pct([4, 1, 3, 2], 0.5), 2)
        self.assertEqual(qr.pct(list(range(1, 11)), 0.9), 9)


if __name__ == "__main__":
    unittest.main()
