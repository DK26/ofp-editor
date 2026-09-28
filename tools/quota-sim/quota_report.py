"""Run summaries, the scenario grid and the Markdown table for tools/quota-sim.

What it owns
    Turning a finished Sim into the metrics the owner asked for (completion, wall time, per-call waits,
    user-visible stalls, fallbacks, quota left), running every strategy x congestion x day x seed, and
    aggregating seeds into one Markdown table per user day.

Where it fits
    quota_sim.py runs the events; this module only reads the finished state. Definitions are repeated in
    README.md so a reader of the table does not need the code.
"""
import math
import statistics

SCENARIO_STRATEGIES = ("S0", "S1", "S2", "S3", "S4", "S4-noGroq", "S5-single", "S5", "S6")
CONGESTION_LEVELS = ("moderate", "observed", "stress")


def pct(values, q):
    """Nearest-rank percentile (q in [0, 1]); None for an empty list."""
    if not values:
        return None
    s = sorted(values)
    return s[min(len(s) - 1, max(0, math.ceil(q * len(s)) - 1))]


def _dist(values):
    """p50 / p90 / max of a list of seconds, rounded to 0.1 s (None entries for an empty list)."""
    return dict(p50=_r(pct(values, 0.5)), p90=_r(pct(values, 0.9)), max=_r(max(values) if values else None))


def _r(x, nd=1):
    """Round for the report, passing None through."""
    return None if x is None else round(x, nd)


def summarize(sim):
    """Metrics of one finished run.

    Decisions: 'answered' = at least one first-stage sample came back from a model; 'no_model' = answered by code
    or the memo by design (S1+); 'default_kept' = an interactive step gave up after the patience limit and kept the
    code default; 'parked' = every eligible allowance was spent (BudgetLimited until the reset); 'cut' = not done by
    the horizon (planned hours + 1 h). 'answered_degraded' is a subset of 'answered': the first stage answered but
    a later call of the same decision did not (a sibling sample, a repair, or the cascade's re-ask or cloud
    escalation), so the answer stands with less confirmation than planned. 'completed' does not exclude them; the
    report shows them in their own column. Waits: from the moment a call is ready to the start of its answered
    attempt (or to giving up); calls still waiting at the horizon count with their wait so far."""
    m = sim.m
    d = dict(total=0, answered=0, no_model=0, default_kept=0, parked=0, cut=0, answered_degraded=0)
    for b in sim.blocks:
        for u in b["units"]:
            for L in u["layers"]:
                d["no_model"] += L["skipped"]
                for dec in L["decisions"]:
                    d["total"] += dec.n
                    if dec.answered:
                        d["answered"] += dec.n
                        d["answered_degraded"] += dec.n if dec.outcomes else 0
                    elif "parked" in dec.outcomes:
                        d["parked"] += dec.n
                    elif "gave_up" in dec.outcomes:
                        d["default_kept"] += dec.n
                    else:
                        d["cut"] += dec.n
    d["total"] += d["no_model"]
    waits = list(m["waits"]) + [(sim.horizon - x.ready, x.dec.interactive) for x in sim.inflight if x.ready is not None]
    finished = m["day_end"] is not None
    served = m["served_by"]
    pools = {pid: p.left() for pid, p in sim.pools.items() if p.left()}
    spend = {pid: round(p.used["usd"], 4) for pid, p in sim.pools.items() if p.used["usd"] > 0}
    return dict(
        **sim.name,
        completed=finished and d["parked"] == d["default_kept"] == d["cut"] == 0,
        day_finished=finished,
        wall_time_s=_r(m["day_end"]) if finished else None,
        horizon_s=sim.horizon,
        blocks_done=m["blocks_done"], blocks_total=len(sim.blocks),
        decisions=d,
        answered_share=_r((d["answered"] + d["no_model"]) / d["total"], 3) if d["total"] else None,
        calls=dict(cloud_served=sum(v for k, v in served.items() if not k.startswith("local")),
                   local_served=sum(v for k, v in served.items() if k.startswith("local")),
                   attempts=m["attempts"], upstream_429=m["upstream_429"]),
        wait_s=dict(all=_dist([w for w, _ in waits]), interactive=_dist([w for w, i in waits if i])),
        stalls=dict(threshold_s=sim.stall_s, over_threshold=m["stalls"], over_60s=m["long_stalls"]),
        fallbacks=dict(calls=m["fallbacks"], reroutes_after_429=m["reroutes"],
                       paid_calls=sum(v for k, v in served.items() if k.startswith("or-paid"))),
        served_by=dict(sorted(served.items())),
        quota_left=pools,
        spend_usd=spend,
        blocks=[dict(workload=b["workload"], start_s=_r(b.get("t0")),
                     duration_s=_r(b["t_end"] - b["t0"]) if "t_end" in b else None) for b in sim.blocks],
    )


def run_grid(work, limits, seeds, stall_s):
    """Every strategy x congestion level x user day x seed, plus the REF baseline; returns runs and aggregates."""
    from quota_sim import STRATEGIES, run_one
    scenarios = [("REF", "none")] + [(s, c) for s in SCENARIO_STRATEGIES for c in CONGESTION_LEVELS]
    runs = []
    for day in work["user_days"]:
        for strat, cong in scenarios:
            for seed in seeds:
                runs.append(run_one(work, limits, day, strat, cong, seed, stall_s))
    agg = aggregate(runs)
    return dict(as_of=work["as_of"], stall_threshold_s=stall_s, seeds=list(seeds),
                strategies={k: v["desc"] for k, v in STRATEGIES.items()},
                congestion_profiles={k: v.get("tag") for k, v in limits["congestion_profiles"].items()
                                     if isinstance(v, dict)},
                aggregates=agg, runs=runs)


def aggregate(runs):
    """Seeds folded per (day, strategy, congestion): counts as k/n, rates as means, wait maxima as the max."""
    groups = {}
    for r in runs:
        groups.setdefault((r["day"], r["strategy"], r["congestion"]), []).append(r)
    out = []
    for (day, strat, cong), rs in groups.items():
        n = len(rs)
        mean = lambda f: _r(statistics.fmean(f(r) for r in rs), 2)
        walls = [r["wall_time_s"] for r in rs if r["wall_time_s"] is not None]
        iw = [r["wait_s"]["interactive"] for r in rs]
        or_left = [r["quota_left"].get("openrouter-free", {}).get("req") for r in rs]
        out.append(dict(
            day=day, strategy=strat, congestion=cong, seeds=n,
            completed=f"{sum(r['completed'] for r in rs)}/{n}",
            day_finished=f"{sum(r['day_finished'] for r in rs)}/{n}",
            answered_share=_r(statistics.fmean(r["answered_share"] for r in rs), 3),
            default_kept=mean(lambda r: r["decisions"]["default_kept"]),
            degraded=mean(lambda r: r["decisions"]["answered_degraded"]),
            parked=mean(lambda r: r["decisions"]["parked"]), cut=mean(lambda r: r["decisions"]["cut"]),
            wall_time_s_median=_r(statistics.median(walls)) if walls else None,
            interactive_wait_s=dict(p50=_r(statistics.median([w["p50"] or 0 for w in iw])),
                                    p90=_r(statistics.median([w["p90"] or 0 for w in iw])),
                                    max=_r(max(w["max"] or 0 for w in iw))),
            all_wait_s_p90=_r(statistics.median([r["wait_s"]["all"]["p90"] or 0 for r in rs])),
            stalls=mean(lambda r: r["stalls"]["over_threshold"]), stalls_60s=mean(lambda r: r["stalls"]["over_60s"]),
            fallback_calls=mean(lambda r: r["fallbacks"]["calls"]),
            reroutes_after_429=mean(lambda r: r["fallbacks"]["reroutes_after_429"]),
            upstream_429=mean(lambda r: r["calls"]["upstream_429"]),
            cloud_calls=mean(lambda r: r["calls"]["cloud_served"]), local_calls=mean(lambda r: r["calls"]["local_served"]),
            openrouter_free_left=_r(statistics.fmean(x for x in or_left if x is not None)) if any(
                x is not None for x in or_left) else None,
            paid_calls=mean(lambda r: r["fallbacks"]["paid_calls"]),
            paid_usd=_r(statistics.fmean(r["spend_usd"].get("openrouter-paid", 0.0) for r in rs), 4),
        ))
    return out


def hm(s):
    """Seconds as h:mm (None as a dash)."""
    if s is None:
        return "-"
    s = int(round(s))
    return f"{s // 3600}:{(s % 3600) // 60:02d}"


def write_markdown(grid, path):
    """One table per user day: rows are scenarios, columns the owner's metrics (definitions in README.md)."""
    lines = [f"# Quota simulation results (as of {grid['as_of']})", "",
             f"Seeds {grid['seeds']}; stall threshold {grid['stall_threshold_s']:g} s. Congestion levels: 'moderate' "
             "and 'observed' throttle OpenRouter :free hosts only (other free hosts use the 'low' placeholder); "
             "'stress' also throttles Groq, Cloudflare and HF ('moderate'). Counts are means over seeds; 'Done' "
             "(every block finished by the horizon) and 'Complete' (done, and every decision answered by a model or "
             "by design without one) are runs out of seeds; waits are medians over seeds except the max. 'Off first "
             "choice' = calls answered by a lower-preference endpoint; 'reroutes' = attempts moved after an upstream "
             "429; 'Degraded' = answered decisions whose later sample, repair or cascade escalation failed (counted "
             "in Answered and Complete). Definitions: tools/quota-sim/README.md.", ""]
    head = ("| Strategy | Congestion | Done | Complete | Answered | Defaults kept | Degraded | Parked | Cut | Wall time "
            "| Interactive wait p50 / p90 / max (s) | Stalls > {t:g} s / > 60 s | Off first choice / reroutes "
            "| Upstream 429s | Cloud / local calls | OR :free left | Paid calls / USD |").format(t=grid["stall_threshold_s"])
    for day in dict.fromkeys(a["day"] for a in grid["aggregates"]):
        lines += [f"## {day}", "", head, "|" + " --- |" * 17]
        for a in (x for x in grid["aggregates"] if x["day"] == day):
            w = a["interactive_wait_s"]
            lines.append(
                f"| {a['strategy']} | {a['congestion']} | {a['day_finished']} | {a['completed']} "
                f"| {a['answered_share'] * 100:.1f}% | {a['default_kept']:g} | {a['degraded']:g} "
                f"| {a['parked']:g} | {a['cut']:g} "
                f"| {hm(a['wall_time_s_median'])} | {w['p50']:g} / {w['p90']:g} / {w['max']:g} "
                f"| {a['stalls']:g} / {a['stalls_60s']:g} | {a['fallback_calls']:g} / {a['reroutes_after_429']:g} "
                f"| {a['upstream_429']:g} "
                f"| {a['cloud_calls']:g} / {a['local_calls']:g} "
                f"| {'-' if a['openrouter_free_left'] is None else format(a['openrouter_free_left'], 'g')} "
                f"| {a['paid_calls']:g} / {a['paid_usd']:.4f} |")
        lines.append("")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
