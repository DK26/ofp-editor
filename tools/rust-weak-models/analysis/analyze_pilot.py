"""Descriptive per-arm summary of the live pilot (k = 1, R0 and R<=3 nested in one episode).

Usage: python analysis/analyze_pilot.py <out.json> <results1.jsonl> [<results2.jsonl> ...]
(live/drive_pilot.py runs it after every arm and writes pilot-summary.json and .txt.)

Exploratory only: k = 1 per (task, variant), no inference beyond counts and exact sign
tests on discordant task pairs. This is the script behind doc 64 §4.2 and §4.3's outcome
and paired tables. Standard library only.
"""
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path


def load(path):
    rows = [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]
    head = next(r for r in rows if r.get("kind") == "run")
    return head, [r for r in rows if r.get("kind") == "round"], [r for r in rows if r.get("kind") == "episode"]


def sign_test(b, c):
    """Two-sided exact binomial (sign) test on discordant pairs b vs c."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def frac(num, den):
    return round(num / den, 3) if den else None


def arm_stats(eps, rounds):
    n = len(eps)
    rmax = max(int(k[1:]) for e in eps for k in e["per_R"])

    def at(e, r, key):
        return bool(e["per_R"].get(f"R{r}", {}).get(key, False))

    out = {"n": n}
    for r in (0, rmax):
        out[f"R{r}_hidden_pass"] = frac(sum(at(e, r, "hidden_pass") for e in eps), n)
        out[f"R{r}_compile_ok"] = frac(sum(at(e, r, "compile_ok") for e in eps), n)
        out[f"R{r}_visible_pass"] = frac(sum(at(e, r, "visible_pass") for e in eps), n)
        out[f"R{r}_accepted_but_wrong"] = frac(sum(at(e, r, "accepted_but_wrong") for e in eps), n)
        out[f"R{r}_hidden_frac_mean"] = round(sum(e["per_R"].get(f"R{r}", {}).get("hidden_frac", 0) or 0 for e in eps) / n, 3)
    for r in range(1, rmax):
        out[f"R{r}_hidden_pass"] = frac(sum(at(e, r, "hidden_pass") for e in eps), n)
    out["final_failure_modes"] = dict(Counter(e["final"].get("failure_mode") for e in eps))
    r0_modes = Counter(e["per_R"]["R0"].get("failure_mode") for e in eps)
    out["R0_failure_modes"] = dict(r0_modes)
    tp = [e["final"].get("trap") for e in eps if e["final"].get("trap")]
    out["trap_pass_final_among_compiling"] = frac(sum(x["passed"] for x in tp), sum(x["total"] for x in tp))
    cat_fail = Counter(c for x in tp for c in x["categories_failed"])
    out["trap_categories_failed_final"] = dict(cat_fail)
    out["rounds_used_mean"] = round(sum(e["rounds_used"] for e in eps) / n, 2)
    out["tokens_per_episode_mean"] = round(sum(e["tokens"]["total"] for e in eps) / n)
    out["completion_tokens_per_episode_mean"] = round(sum(e["tokens"]["completion"] for e in eps) / n)
    out["gen_s_per_episode_mean"] = round(sum(e["wall_ms"]["generation"] for e in eps) / n / 1000, 1)
    out["cargo_s_per_episode_mean"] = round(sum(e["wall_ms"]["cargo"] for e in eps) / n / 1000, 1)
    passes = sum(at(e, rmax, "hidden_pass") for e in eps)
    out["tokens_per_success"] = round(sum(e["tokens"]["total"] for e in eps) / passes) if passes else None
    esc = Counter()
    for e in eps:
        for k, v in (e.get("escape_hatches") or {}).items():
            if isinstance(v, (int, float)):
                esc[k] += v
    out["escape_hatches_total"] = dict(esc)
    # Round-level facts.
    out["generations"] = len(rounds)
    out["reasoning_chars_total"] = sum((r.get("gen") or {}).get("reasoning_chars") or 0 for r in rounds)
    out["finish_length"] = sum(1 for r in rounds if (r.get("gen") or {}).get("finish_reason") == "length")
    out["format_failures"] = sum(1 for r in rounds if r.get("failure_mode") == "format")
    out["bypass"] = sum(1 for r in rounds if r.get("failure_mode") == "bypass")
    out["context_overflow_rounds"] = sum(1 for r in rounds if r.get("context_overflow"))
    out["infra_errors"] = sum(1 for r in rounds if r.get("infra_error"))
    r0codes = Counter(c for r in rounds if r.get("round") == 0 for c in set(r.get("diag_codes") or []))
    out["R0_diag_codes_by_episode"] = dict(r0codes.most_common(10))
    allcodes = Counter(c for r in rounds for c in (r.get("diag_codes") or []))
    out["diag_codes_all_rounds"] = dict(allcodes.most_common(10))
    # Fix rate per code: share of (round -> next round) transitions where the code disappeared.
    fixed, seen = Counter(), Counter()
    for e in eps:
        for d in e.get("diag_fix") or []:
            for c in d["codes"]:
                seen[c] += 1
                if c in d["fixed"]:
                    fixed[c] += 1
    out["fix_rate_by_code"] = {c: f"{fixed[c]}/{seen[c]}" for c, _ in seen.most_common(8)}
    # Repair stalls: a repair round whose code is byte-identical to the previous round's code.
    by_ep = defaultdict(list)
    for r in rounds:
        by_ep[(r["task"], r["variant"], r["sample"])].append(r)
    stalls = 0
    repair_rounds = 0
    for rs in by_ep.values():
        rs.sort(key=lambda x: x["round"])
        for a, b in zip(rs, rs[1:]):
            repair_rounds += 1
            if a.get("code_sha256") and a.get("code_sha256") == b.get("code_sha256"):
                stalls += 1
    out["repair_rounds"] = repair_rounds
    out["repair_rounds_identical_code"] = stalls
    return out


def paired(eps, rmax):
    """Per task: PLAIN vs GUIDED outcome at R0 and R<=max (k = 1)."""
    by = defaultdict(dict)
    for e in eps:
        by[e["task"]][e["variant"]] = e
    res = {}
    for r in (0, rmax):
        g_only = p_only = both = neither = 0
        for t, d in by.items():
            if "plain" not in d or "guided" not in d:
                continue
            gp = bool(d["guided"]["per_R"].get(f"R{r}", {}).get("hidden_pass"))
            pp = bool(d["plain"]["per_R"].get(f"R{r}", {}).get("hidden_pass"))
            g_only += gp and not pp
            p_only += pp and not gp
            both += gp and pp
            neither += not gp and not pp
        res[f"R{r}"] = {"guided_only": g_only, "plain_only": p_only, "both": both, "neither": neither,
                        "sign_test_p_two_sided": round(sign_test(g_only, p_only), 3)}
        # Hidden fraction difference (continuous), mean over tasks.
        diffs = [(d["guided"]["per_R"].get(f"R{r}", {}).get("hidden_frac") or 0) -
                 (d["plain"]["per_R"].get(f"R{r}", {}).get("hidden_frac") or 0)
                 for d in by.values() if "plain" in d and "guided" in d]
        res[f"R{r}"]["hidden_frac_diff_mean_guided_minus_plain"] = round(sum(diffs) / len(diffs), 3) if diffs else None
        res[f"R{r}"]["tasks_guided_higher_frac"] = sum(1 for x in diffs if x > 0)
        res[f"R{r}"]["tasks_plain_higher_frac"] = sum(1 for x in diffs if x < 0)
    return res


def per_task_table(eps, rmax):
    by = defaultdict(dict)
    for e in eps:
        by[e["task"]][e["variant"]] = e
    rows = []
    for t in sorted(by):
        row = {"task": t}
        for v in ("plain", "guided"):
            e = by[t].get(v)
            if not e:
                continue
            row[v] = {"R0": e["per_R"]["R0"].get("failure_mode"), f"R{rmax}": e["final"].get("failure_mode"),
                      "hidden_frac_final": e["final"].get("hidden_frac"), "rounds": e["rounds_used"]}
        rows.append(row)
    return rows


def main():
    out_path, files = sys.argv[1], sys.argv[2:]
    report = {"note": "k = 1 per (task, variant); descriptive pilot, not confirmatory", "runs": []}
    for f in files:
        head, rounds, eps = load(f)
        rmax = head["rounds"]
        run = {"file": Path(f).name, "model": head["model"], "run_id": head["run_id"], "sampler": head["sampler"],
               "system_tokens": head["system_tokens"], "toolchain": head["toolchain"],
               "episodes_planned": head["episodes_planned"], "episodes_done": len(eps), "arms": {}, "paired": {}}
        for scope, pred in (("scored", lambda e: e["scored"]), ("pilot", lambda e: not e["scored"]), ("all", lambda e: True)):
            sel = [e for e in eps if pred(e)]
            if not sel:
                continue
            for v in ("plain", "guided"):
                ev = [e for e in sel if e["variant"] == v]
                keys = {(e["task"], e["variant"], e["sample"]) for e in ev}
                rv = [r for r in rounds if (r["task"], r["variant"], r["sample"]) in keys]
                if ev:
                    run["arms"][f"{scope}/{v}"] = arm_stats(ev, rv)
            run["paired"][scope] = paired(sel, rmax)
        run["per_task"] = per_task_table(eps, rmax)
        report["runs"].append(run)
    Path(out_path).write_text(json.dumps(report, indent=1), encoding="utf-8")
    for run in report["runs"]:
        print(f"\n== {run['model']} ({run['episodes_done']}/{run['episodes_planned']} episodes)")
        print(f"{'arm':16} {'n':>3} {'R0 pass':>7} {'R3 pass':>7} {'R0 comp':>7} {'R3 comp':>7} {'R3 AbW':>6} "
              f"{'R0 hfrac':>8} {'R3 hfrac':>8} {'trap':>5} {'rounds':>6} {'tok/ep':>7} {'gen s':>6}")
        for k, a in run["arms"].items():
            print(f"{k:16} {a['n']:3} {a['R0_hidden_pass']:7} {a['R3_hidden_pass']:7} {a['R0_compile_ok']:7} "
                  f"{a['R3_compile_ok']:7} {a['R3_accepted_but_wrong']:6} {a['R0_hidden_frac_mean']:8} "
                  f"{a['R3_hidden_frac_mean']:8} {str(a['trap_pass_final_among_compiling']):>5} {a['rounds_used_mean']:6} "
                  f"{a['tokens_per_episode_mean']:7} {a['gen_s_per_episode_mean']:6}")
        for scope, p in run["paired"].items():
            print(f"paired {scope}: {json.dumps(p)}")


if __name__ == "__main__":
    main()
