"""Monte Carlo power check for the PLAIN vs GUIDED primary contrast.

Generative model (logit scale), per task i, model j, variant v in {0: PLAIN, 1: GUIDED}:
    logit p = mu + a_i + m_j + c_ij + v * (beta + b_i)
    a_i  ~ N(0, sigma_task)   task difficulty (large: tasks run from trivial to near-impossible)
    m_j  fixed model offsets  (three small local models)
    c_ij ~ N(0, sigma_tm)     task x model interaction, shared by both variants (pairing)
    b_i  ~ N(0, tau)          task-specific variant effect (heterogeneity of the treatment)
Each (i, j, v) cell draws k Bernoulli episodes. The primary test statistic is the task-level
paired difference d_i = mean_{j, samples}(GUIDED) - mean_{j, samples}(PLAIN); a one-sample
t-test on d_i across tasks (task = unit of inference, models and samples averaged inside).
A sign-flip randomisation test gives nearly identical power at these N and is what the
pre-registration names; the t-test is used here for speed.

Pure standard library (no numpy on the host). Deterministic seeds.

Usage: python power_sim.py [reps]   (doc 64 quotes the 500-rep run; the default is 600)
Output: results/power_sim_results.json next to this script (git-ignored), whatever the
current directory.
"""
import json
import math
import random
import statistics
import sys
from pathlib import Path

T_CRIT = {19: 2.093, 23: 2.069, 29: 2.045, 35: 2.030}  # two-sided alpha 0.05
OUTPUT = Path(__file__).resolve().parent / "results" / "power_sim_results.json"


def logistic(x):
    return 1.0 / (1.0 + math.exp(-x))


def one_rep(rng, n_tasks, k, beta, tau, mu, sigma_task, sigma_tm, model_offsets):
    diffs = []
    pooled_p = [0.0, 0.0]
    for _ in range(n_tasks):
        a = rng.gauss(0.0, sigma_task)
        b = rng.gauss(0.0, tau)
        g_sum = 0
        p_sum = 0
        for m in model_offsets:
            c = rng.gauss(0.0, sigma_tm)
            base = mu + a + m + c
            pp = logistic(base)
            pg = logistic(base + beta + b)
            p_sum += sum(1 for _ in range(k) if rng.random() < pp)
            g_sum += sum(1 for _ in range(k) if rng.random() < pg)
        denom = k * len(model_offsets)
        diffs.append((g_sum - p_sum) / denom)
        pooled_p[0] += p_sum / denom
        pooled_p[1] += g_sum / denom
    mean_d = statistics.fmean(diffs)
    sd = statistics.stdev(diffs)
    se = sd / math.sqrt(n_tasks) if sd > 0 else 1e-9
    t = mean_d / se
    crit = T_CRIT[n_tasks - 1]
    return abs(t) > crit and mean_d > 0, mean_d, crit * se, pooled_p[0] / n_tasks, pooled_p[1] / n_tasks


def main():
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    mu = -0.6            # PLAIN pass rate around 0.35-0.40 for the small models after the loop
    sigma_task = 1.5     # wide task difficulty spread (doc 49: items ran from 0/6 to 6/6)
    sigma_tm = 0.5
    model_offsets = [0.0, -0.3, -0.6]
    results = []
    seed = 20260928
    for n_tasks in (20, 24, 30):
        for k in (3, 6, 10):
            for beta in (0.0, 0.4, 0.6, 0.8):
                for tau in (0.5, 1.0):
                    rng = random.Random(seed + n_tasks * 1000 + k * 100 + int(beta * 10) * 10 + int(tau * 10))
                    hits = 0
                    effs = []
                    halfw = []
                    bp = []
                    bg = []
                    for _ in range(reps):
                        sig, eff, hw, p_p, p_g = one_rep(rng, n_tasks, k, beta, tau, mu, sigma_task, sigma_tm, model_offsets)
                        hits += sig
                        effs.append(eff)
                        halfw.append(hw)
                        bp.append(p_p)
                        bg.append(p_g)
                    results.append({
                        "tasks": n_tasks, "k": k, "beta_logit": beta, "tau": tau,
                        "mean_plain": round(statistics.fmean(bp), 3),
                        "mean_guided": round(statistics.fmean(bg), 3),
                        "true_diff_pp": round(100 * statistics.fmean(effs), 1),
                        "ci95_halfwidth_pp": round(100 * statistics.fmean(halfw), 1),
                        "power": round(hits / reps, 3),
                    })
                    print(json.dumps(results[-1]), flush=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as fh:
        json.dump({"reps": reps, "mu": mu, "sigma_task": sigma_task, "sigma_tm": sigma_tm,
                   "model_offsets": model_offsets, "results": results}, fh, indent=1)


if __name__ == "__main__":
    main()
