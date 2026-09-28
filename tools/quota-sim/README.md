# quota-sim: free-tier rate limits over a Wilco user day

A small, deterministic simulator for the owner's question of 2026-09-27: *if free providers rate-limit us, how do we
overcome it, and is the experience still good enough?* It replays a **user day** (a sequence of Wilco workflow runs,
with their per-step calls and tokens) against a **provider set** (request, token, neuron and credit limits) under a
**routing strategy**, with a seeded model of **upstream 429 congestion**. It reports whether the day finished, the
wall time, per-call waits, user-visible stalls, fallbacks and the quota left.

Research tool, not product code: Python standard library only, no network, no model calls, no keys. Its results feed
the rate-limit research doc, [doc 52](../../docs/research/52-rate-limits-and-ux.md). Every number it prints is a model
output [I] built on inputs tagged in the data files ([V] verified, [V-obs] our own run records, [I] inference, [U]
placeholder).

## Run it

```text
python tools/quota-sim/quota_sim.py --day mission-build --strategy S4 --congestion observed --seed 1
python tools/quota-sim/quota_sim.py --all --seeds 1 2 3 --out <results.json> --md <results.md>
python -m unittest discover -s tools/quota-sim        (or: python -m pytest tools/quota-sim)
```

One run prints its summary as JSON. `--all` runs every strategy × congestion level × user day × seed (336 runs, about
15-25 s) and writes the per-run results and a Markdown table per user day to the paths you name. Nothing is written
inside the repository unless you point it there; results are not committed.

## Files

| File | What it holds |
| --- | --- |
| `quota_sim.py` | Strategies, the expansion of decisions into calls, the router, the event loop and the CLI |
| `quota_pools.py` | Quota pools (sliding 60-s windows, daily and monthly caps, interactive reserve), upstream hosts (congestion), endpoints (pricing a call in requests, tokens, neurons, USD) |
| `quota_report.py` | Run summary, the scenario grid, seed aggregation and the Markdown table |
| `test_quota_sim.py` | 31 unit tests (below) |
| `data/workload.json` | Workflows as layers of decision groups (step kind, K class, capsule tokens), four user days, and cross-check numbers |
| `data/limits.json` | Pools, endpoints, congestion profiles and levels, routing plans, with dated sources |

`data/workload.json` is a compact, sim-ready extract of the research workload profile for the rate-limit question
(2026-09-28): the decision groups, capsule sizes and repair rates of `tools/cost-model/cost_model.py`, arranged in the
layer order of doc 25 §4.1 and doc 38 §8 [I], plus that profile's per-workflow call counts and unthrottled day spans,
which the tests reproduce. `data/limits.json` takes its limits from `docs/research/data/free-llm-services.csv` and
docs 48 and 50 (read 2026-09-27, terms re-read 2026-09-28) and the one observed throttling window (2026-09-27).

## What it models

- **A day** is a list of blocks with planned start times (`user_days`). A block starts at its planned time or when the
  previous block ends, whichever is later. Sessions are 12 requests 150 s apart; a request starts only once the user
  has the previous answer. Campaign runs include the premise pick (120 s) and outline approval (300 s) user gates. The
  horizon is the planned hours plus one hour; work not done by then is "cut". No UTC reset falls inside a day.
- **A run** is layers of mutually independent decisions; layers run in sequence. Inside a layer, calls run in phases:
  the K samples, repair round 1, repair round 2, then the next cascade stage and its repairs. Each phase waits for the
  previous one (a barrier, as in the research profile). Repairs are drawn per call with the cost model's repair rates
  [U]; a repair is only sent if the call it repairs was answered.
- **Concurrency**: at most 8 cloud calls in flight (doc 38 §4.5 [I]); each local model serves one call at a time.
  Calls the user is waiting on are dispatched before background calls. A cloud call holds its slot from dispatch until
  it settles, including while it waits for a window, a cooldown or a backoff [I, conservative for single-route
  strategies]; a call still queued for a slot is timed out only once it gets one (at most 0.5 s late in the grid).
- **Pools** meter what a provider meters: OpenRouter `:free` per account (20/min; 50/day, or 1,000/day after 10 credits
  bought once), Groq per model (30/min, 1,000/day, 8,000 tokens/min, 200,000 tokens/day; cached prompt tokens do not
  count on gpt-oss, at the workflow's cached share for the effort the strategy runs, lower at K = 1 than at Standard;
  300 reasoning tokens counted per call), Cloudflare one neuron pool (10,000/day, 300/min), Hugging
  Face monthly credits (0.10 USD), and the S6 paid endpoint's daily hard cap. Every attempt fills the per-minute window;
  only answered calls spend the daily allowance (OpenRouter's counter did not move on 12 upstream 429s [V-obs]).
- **Congestion** is per upstream host: a two-state (clear / congested) Markov chain with exponential dwell times. A
  congested host answers an attempt with a 429 in 0.35-0.56 s [V-obs] with probability `p429_congested`. Profiles:
  `observed` (calibrated on the one measured window: 12 of 13 attempts failed and the throttling outlasted 15 minutes),
  `moderate` [U], `low` [U] and `paid` [U]. **Levels** map endpoint classes to profiles: `moderate` and `observed` throttle
  only OpenRouter `:free` hosts (the only ones measured); `stress` also puts Groq, Cloudflare and HF on `moderate`.
- **Retries**: single-route strategies retry the same endpoint with backoff (2 s doubling to 60 s, equal jitter, 10
  retries, then a probe every 3 min; doc 51 Z16). Multi-route strategies put a throttled endpoint on a cooldown shared by
  every call (15 s doubling to 600 s) and re-route the call at once. A call the user waits on gives up after 60 s and
  keeps the code default (doc 25 §10.1). When every eligible allowance is spent the call parks until the reset (the
  run's `BudgetLimited` state, doc 38 §3.4).
- **Routing** (multi-route): among the endpoints listed for the call's step kind, pick the one that can start soonest,
  plus 1 s per rank of preference; skip endpoints whose daily allowance is spent, whose per-minute token cap is smaller
  than the call, or that are cooling down. Background work may use only 70% of each daily allowance, keeping 30% for
  steps the user waits on. The paid endpoint (S6) is last and only wins when no free route can start within 10 s (the
  user is waiting) or 2 min (background), compared on start times with no rank penalty, and never past its daily cap.
- **Product-rule exclusions**: an endpoint marked `excluded_by` in `data/limits.json` (Gemma 4 `:free`, whose host keeps
  prompts 55 days; D046, D045 item 7) stays in the data to document why it is out, and no routing plan may name it.

## Strategies

| Id | What changes | Machine |
| --- | --- | --- |
| REF | Reference only: Standard effort on one endpoint with no limits and no congestion | any |
| S0 | One free provider: OpenRouter `qwen3.8-27b:free` (50/day), Standard effort (Pick K = 3, creative K = 2, R = 2), backoff | any |
| S1 | S0 + call reduction: K = 1 with validators and repairs kept; bulk independent text packed 4 slots per request [I proposal]; 25% of explanations from the exact-hash memo [U]; 50% of intent Fills skipped because a gesture or menu started the step [U] | any |
| S2 | S1 + a local 3-4B GPU model for Pick and Fill at Standard K; text, Compose and Explain on S0's route | 8 GB GPU |
| S3 | S1 + quota- and congestion-aware routing over the user's own OpenRouter, Groq, Cloudflare and HF accounts, qualified (screened plausible) per step kind | any |
| S4 | S3 + doc 53's tiny local cascade for Pick and Fill: one CPU pass, 20% re-ask, 23% escalated to S3's routing | CPU only is enough |
| S4-noGroq | S4 without Groq (its answer on fictional military content is pending, doc 50) | CPU only |
| S5-single | S1 with OpenRouter's 1,000/day tier: does buying 10 credits alone fix a single free provider? | any |
| S5 | S4 with OpenRouter's 1,000/day tier (10 credits bought once, about 10.80 USD) | CPU only |
| S6 | S5 + a paid pinned endpoint (Gemma 4 26B-A4B, 0.07/0.34 USD per MTok) as last resort under a 0.25 USD daily hard cap [I] | CPU only |

Product rules the strategies assume and do not change: every account is the user's own, one per provider, created by
the user (doc 50; D008); no Plotroom-owned key, proxy or shared account; every endpoint a call may reach is a binding
the user set up and can see, and every fallback is recorded for the run record (doc 53 §4.1 rule 6; D023). Packing
several text slots into one request departs from "one small decision per call" and needs an owner decision; so does the
cascade's escalation to another model (doc 53 §4.3).

## Metrics

| Metric | Definition |
| --- | --- |
| Done | Every block of the day finished before the horizon |
| Complete | Done, and every decision was answered: by a model, or on purpose without one (memo, gesture-started step) |
| Answered | Share of the day's decisions answered by a model or on purpose without one |
| Defaults kept | Decisions whose every sample gave up after the 60-s patience limit (the code default stands) |
| Parked | Decisions refused because every eligible daily allowance was spent (resumable after the reset) |
| Cut | Decisions not reached or not finished by the horizon |
| Wall time | When the last block finished; mostly set by the planned schedule, so read it with Done |
| Wait | From the moment a call is ready (its phase started) to the start of its answered attempt, or to giving up. Includes queueing for a concurrency slot, per-minute windows, cooldowns and backoff; the table shows p50 / p90 / max for calls the user waits on |
| Stalls | Phases of a step the user waits on whose longest wait exceeded 10 s (doc 53's L3 budget) or 60 s |
| Off first choice / reroutes | Calls answered by a lower-preference endpoint of their step kind (spreading load counts too) / attempts moved after an upstream 429 |
| Quota left | Per pool at the end of the day: requests, counted tokens, neurons or USD remaining |

## Tests

`test_quota_sim.py` covers: data integrity (every routing plan names only endpoints screened plausible for that step
kind and none a product rule excludes; one account per provider; an unknown congestion level is refused); known values
(the expansion reproduces the research profile's calls for every workflow at B, B-quick, F and F-cascade, e.g.
campaign B 650.4; the REF replay reproduces each day's unthrottled span within 0.5%; both cached shares match the cost
model and K = 1 strategies use the K = 1 share; sampled repairs average to the expected count); determinism; pool
boundaries at and one past each limit (RPM, TPM, daily cap, interactive reserve; 429s never spend the daily cap); the
congestion model (extremes; the observed profile fails 0.91 of attempts against 12 of 13 observed); the router (ties,
spent pools, cooldowns, a call larger than the TPM cap, paid last resort and its cap, and the paid 10-s threshold
whatever the route list's length); end-to-end anchors (S0 cannot carry a Standard session; S4 finishes the observed
days; zero quota everywhere parks without hanging; a failed escalation is reported as degraded); and forward progress
(every scenario ends within the event budget, interactive waits never pass the patience limit, the budget guard
raises).

## Limits of the model

- One observed throttling window (18 minutes, one host, one evening) calibrates `observed`; Groq, Cloudflare, HF and
  paid congestion are placeholders [U]. The `stress` level exists because the free hosts we have not measured may
  throttle too. The `paid` placeholder is optimistic: 2 of 11 paid hosts screened on 2026-09-27 throttled for 7-10
  minutes (doc 52 section 2.4), and S6 has only one paid endpoint.
- Every allowance starts full on the simulated day, including Hugging Face's monthly credits, so a strategy can spend a
  month's HF credits in one day.
- The tiny cascade stage's latency (1.5 s a Pick) and escalation rate (23%, measured on 3-4B models, not on 0.4-1B)
  are placeholders; doc 52 section 3.5 varies both.
- "Qualified per step kind" means *screened plausible*; no cloud endpoint is qualified (doc 50 §5.1; D044). Quality
  differences between endpoints, K = 1 and the tiny cascade are not modelled: the simulator measures time and quota,
  not correctness. Doc 53 §5's evidence bar (R6) applies before the cascade is proposed as a default.
- Content-policy bands (D047) and data terms are not modelled; filtering endpoints by them first can only shrink the
  multi-route lists. Groq's pending answer is why S4-noGroq exists.
- Tokens are the cost model's product-sized capsules (3.5 bytes per token), the conservative case for token caps.
- Phases are barriers; a real scheduler could start a decision's repair before its siblings finish, so waits are an
  upper bound on that account.
- The cascade's re-ask and escalation are drawn independently of each other, as in the research profile.
