"""Recompute doc 64's time split and per-round compile rates from the pilot JSONL records.

Where the wall time of a live run goes (generation, split into prompt evaluation and
decoding; cargo build; test binaries) and how many rounds compiled. Reads round and
episode records only. Prints one block per file, then per file x arm, then per round
index, then all files pooled.

Usage: python analysis/time_split.py [results1.jsonl ...]
With no arguments it reads the three live pilot arms from results/pilot-live/ (not the
aborted first Qwen file). Standard library only.
"""
import json
import statistics as st
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PILOT = Path(__file__).resolve().parent.parent / "results" / "pilot-live"
PILOT_ARMS = ["qwen35-4b-q4km", "gemma4-e4b-qat", "granite41-3b-q4km"]


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def load(path):
    rounds, eps, runs = [], [], []
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        r = json.loads(ln)
        {"round": rounds, "episode": eps, "run": runs}[r["kind"]].append(r)
    return runs, rounds, eps


def block(name, rounds):
    n = len(rounds)
    gen = sum(r["gen"]["gen_ms"] for r in rounds)
    pr = sum(r["gen"]["timings"]["prompt_ms"] for r in rounds)
    dec = sum(r["gen"]["timings"]["predicted_ms"] for r in rounds)
    bld = sum(r["build_ms"] for r in rounds)
    tst = sum(r["test_ms"] for r in rounds)
    tot = gen + bld + tst
    b = [r["build_ms"] for r in rounds if r["format_ok"]]
    comp = sum(1 for r in rounds if r["compile_ok"])
    tested = sum(1 for r in rounds if r["test_ms"] > 0)
    vis = sum(1 for r in rounds if r["visible_pass"])
    fmt_bad = sum(1 for r in rounds if not r["format_ok"])
    ptok = [r["gen"]["prompt_tokens"] for r in rounds]
    ctok = [r["gen"]["completion_tokens"] for r in rounds]
    uncached = [r["gen"]["timings"]["prompt_n"] for r in rounds]
    dps = [r["gen"]["timings"]["predicted_per_second"] for r in rounds]
    pps = [r["gen"]["timings"]["prompt_per_second"] for r in rounds if r["gen"]["timings"]["prompt_n"] > 50]
    tms = [r["test_ms"] for r in rounds if r["test_ms"] > 0]
    print(f"== {name}: rounds {n}")
    print(f"  time s: gen {gen/1e3:.0f} (prompt {pr/1e3:.0f} + decode {dec/1e3:.0f}), build {bld/1e3:.1f}, tests {tst/1e3:.1f}, total {tot/1e3:.0f}")
    print(f"  shares: gen {gen/tot:.3%}  build {bld/tot:.3%}  tests {tst/tot:.3%}  | prompt-eval {pr/tot:.3%} decode {dec/tot:.3%} other-gen {(gen-pr-dec)/tot:.3%}")
    print(f"  minutes: prompt {pr/6e4:.1f} decode {dec/6e4:.1f} gen {gen/6e4:.1f} build {bld/6e4:.2f} tests {tst/6e4:.2f}")
    print(f"  build ms (format_ok rounds n={len(b)}): median {st.median(b):.0f} p90 {pct(b,0.9):.0f} max {max(b)}")
    print(f"  gen s per round median {st.median([r['gen']['gen_ms'] for r in rounds])/1e3:.1f}")
    print(f"  compiled {comp}/{n}  tests ran {tested}/{n}  visible pass {vis}/{n}  format fail {fmt_bad}/{n}")
    print(f"  test ms when run: {tms}")
    print(f"  prompt tok median {st.median(ptok):.0f}, uncached median {st.median(uncached):.0f}, completion median {st.median(ctok):.0f} p90 {pct(ctok,0.9):.0f}")
    print(f"  decode tok/s median {st.median(dps):.1f}; prompt tok/s median {st.median(pps):.0f}")
    return dict(n=n, gen=gen, pr=pr, dec=dec, bld=bld, tst=tst, comp=comp, tested=tested)


def overhead(rounds, eps):
    """Wall clock not in gen/build/test: gaps between consecutive records of one run."""
    recs = sorted(rounds + eps, key=lambda r: r["ts"])
    gaps, acc = 0.0, 0.0
    by_run = defaultdict(list)
    for r in recs:
        by_run[r["run_id"]].append(r)
    for rid, rs in by_run.items():
        rs = [r for r in rs if r["kind"] == "round"]
        for a, b in zip(rs, rs[1:]):
            dt = (datetime.fromisoformat(b["ts"]) - datetime.fromisoformat(a["ts"])).total_seconds()
            if dt > 600:
                continue  # an interruption, not overhead
            gaps += dt
            acc += (b["gen"]["gen_ms"] + b["build_ms"] + b["test_ms"]) / 1e3
    return gaps, acc


def main(argv=None):
    files = [Path(a) for a in (sys.argv[1:] if argv is None else argv)] or [PILOT / f"{t}.jsonl" for t in PILOT_ARMS]
    allr = []
    for path in files:
        f = path.stem
        runs, rounds, eps = load(path)
        allr += rounds
        print("#" * 70, f, "runs", len(runs), "episodes", len(eps))
        block(f, rounds)
        g, a = overhead(rounds, eps)
        print(f"  wall from ts gaps {g:.0f}s vs accounted {a:.0f}s -> unaccounted {g-a:.0f}s ({(g-a)/g:.1%})")
        # duplicates
        keys = defaultdict(int)
        for r in rounds:
            keys[(r["task"], r["variant"], r["sample"], r["round"])] += 1
        print("  duplicate round keys:", sum(1 for v in keys.values() if v > 1))
        for v in ("plain", "guided"):
            block(f"{f}/{v}", [r for r in rounds if r["variant"] == v])
        by_r = defaultdict(list)
        for r in rounds:
            by_r[r["round"]].append(r)
        print("  per round index: " + "; ".join(
            f"R{k}: {sum(1 for r in v if r['compile_ok'])}/{len(v)} compiled" for k, v in sorted(by_r.items())))
        ep_reach = sum(1 for e in eps if any(x.get("compile_ok") for x in e["per_R"].values()))
        ep_wall = [ (e["wall_ms"]["generation"] + e["wall_ms"]["cargo"]) / 1e3 for e in eps]
        print(f"  episodes that compiled at any round {ep_reach}/{len(eps)}; episode gen+cargo s median {st.median(ep_wall):.0f} mean {st.mean(ep_wall):.0f}")
        for v in ("plain", "guided"):
            es = [e for e in eps if e["variant"] == v]
            print(f"  {v}: episodes compiled any round {sum(1 for e in es if any(x.get('compile_ok') for x in e['per_R'].values()))}/{len(es)}, "
                  f"pass R0 {sum(1 for e in es if e['per_R'].get('R0',{}).get('hidden_pass'))}, final pass {sum(1 for e in es if e['final']['hidden_pass'])}, "
                  f"final compiles {sum(1 for e in es if e['final']['compile_ok'])}, abw {sum(1 for e in es if e['final']['accepted_but_wrong'])}, "
                  f"tok/ep {st.mean([e['tokens']['total'] for e in es])/1e3:.1f}k gen s/ep {st.mean([e['wall_ms']['generation'] for e in es])/1e3:.0f}")

    print("#" * 70, "pooled")
    block("all", allr)


if __name__ == "__main__":
    main()
