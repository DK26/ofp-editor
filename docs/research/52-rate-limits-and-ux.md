# Rate limits and UX: can free tiers carry Plotroom's workload?

Research doc 52 for Plotroom (`ofp-editor`). Research date: 2026-09-28 (UTC); provider limits re-read at the source on 2026-09-27
at about 21:50 UTC. Audience: the owner, contributors and LLM coding agents; meant to be read on its own.
Question answered (owner, 2026-09-27, lightly edited): "If we have rate-limit issues with the free providers, how do we overcome them?
If the limits are too restrictive, the UX may not be good enough for our standards."

**Status.** Research, simulation and proposals. **No model was run and no keyed API was called for this doc.** The evidence is (a) the
call and token counts of the cost model (`tools/cost-model/`, doc 40); (b) provider limits read at the source; (c) Plotroom's own run
records of 2026-09-27 (a free-endpoint probe and a paid screening run under D044; not in the repository, quoted as aggregates only);
and (d) a seeded simulator added with this doc, [`tools/quota-sim/`](../../tools/quota-sim/README.md). Every simulated number is a
model output [I]. The UX standard (§4) and the design (§5) are **proposals for the owner**; nothing here changes a decision record.
**Epistemic legend.** **[V]** verified against the cited primary source on the date given. **[V per doc N]** taken from a sibling doc
or its data file. **[V-obs]** observed in Plotroom's own run records (2026-09-27; not in the repository). **[I]** our inference,
arithmetic or simulation output. **[U]** unknown, or a placeholder value.
**Relation to sibling docs.** Doc 40 (token economy, the cost model), docs 25 and 38 (workflows, the concurrency cap, `BudgetLimited`),
docs 44 and 46 (local latency), doc 48 §6.0 (OpenRouter's free-tier rules), doc 50 (free services and the "connect a free model"
flow), doc 51 (rows Z15 and Z16: error taxonomy and retry policy), doc 53 (tiny models, latency classes, the confidence cascade;
draft), doc 55 (per-model presets; draft). Records: D004, D008, D021–D026, D044–D048.
**Rules this doc keeps.** Every cloud account is the user's own, **one account per provider**, created by the user; no Plotroom-owned
key, proxy, shared account or keyless default; no routing across several accounts of one provider (doc 50 §1.3; D045 item 2). Wilco
stays off by default (D004). Agents never create accounts or handle keys.
**Names.** "Strategy S0 … S6" are the simulator's routing strategies (§3.2), not doc 25's campaign stages; a campaign stage is always
written "stage S7". "Standard" is doc 25's effort preset (Pick K = 3, creative K = 2, repairs R ≤ 2). "Interactive" means a step the
user is waiting on; "background" means a run the user started and left (doc 53 latency class L4).
**Hygiene.** Public sources only. No local paths, user names, key material, call or generation ids, or private projects.

## TL;DR

- **The limit that bit in practice was shared upstream capacity, not the account quota** [V-obs]. On 2026-09-27 the only free
  zero-retention generalist on OpenRouter (`qwen/qwen3.8-27b:free`, one host) answered **1 of 13 attempts in 17.6 minutes**. The 12
  upstream 429s did not spend the 50-a-day counter, and their `retry_after` hints (0.12–0.77 s) said nothing about a throttle that
  lasted over 15 minutes. Retrying the same host cannot fix that; only a second route can.
- **Workload** [I on V per doc 40]: a 30-minute session makes 60 cloud calls at Standard (at most 10 in any minute); a mission-build day
  about 195; a campaign-from-brief day about 879 (310 in its busiest minute, 741 of them background); a heavy 8-hour day about 1,430.
  Creative text is 66% of a campaign's calls, and it is the load a small local model cannot take.
- **Which user days fit which free setup** (simulated, congestion as observed; §3) [I]:
  - **OpenRouter `:free` alone**, at 50 or 1,000 requests a day: no day completes. A light session gets 34–42% of its decisions
    answered, and interactive waits sit at the 60-s ceiling.
  - **Plus a local GPU model for Pick and Fill**: 72–85% answered; still no day completes.
  - **The user's own OpenRouter, Groq, Cloudflare and Hugging Face accounts** behind a quota- and congestion-aware router, with
    S1's call reductions, cloud K = 1 first (strategy S3): every day completes (the heavy day on 2 of 3 seeds).
  - **Plus a tiny local CPU cascade** for Pick and Fill (S4): all four days complete on 3 of 3 seeds, with interactive waits at
    p90 ≤ 1.7 s and at most 16 s. The tiny stage is unmeasured: 1.5 s a Pick and 23% escalated to the cloud are assumptions, and
    §3.5 varies both.
  - **When every free host is throttled** ("stress"), only S6 completes every day. S6 adds a paid pinned backstop with a hard cap
    of $0.25 a day, and it spent at most about $0.009 a day.
- **Groq and Cloudflare are both load-bearing** [I]. Without Cloudflare only the light session completes (a mission build keeps
  about 7 code defaults), and without Groq the campaign and heavy days complete on 1 of 3 seeds. With only OpenRouter and a local
  model, even a light session fails. So the written answers on fictional military content that D045 item 7 waits for (Groq's
  exception route; Cloudflare's violence clause) gate a free campaign default.
- **The call-reduction measure that matters is cloud K = 1** [I]. With Standard K on the cloud, S4 still completes the campaign
  day, but its campaign block takes 23–30 minutes instead of 11–12, and the heavy day completes on 1 of 3 seeds (about 11
  decisions parked). Packing text slots, the memo and skipped intent Fills were not load-bearing in the sensitivity runs. Capsule
  size decides whether token-capped tiers (Groq's 8K tokens a minute, Cloudflare's neurons) are usable at all.
- **Proposed UX standard** (§4, for the owner):
  - interactive waits caused by limits: p90 ≤ 2 s;
  - no interactive wait past 10 s without a visible card with choices;
  - a 60-s ceiling, after which the code default stands, labelled;
  - a light session and a mission build complete within one UTC day's free allowances;
  - a campaign completes that day, or the plan card says so before the run;
  - at least 99% of decisions answered;
  - never a silent switch, hang or loss.
- **Design** (§5): a quota-aware router over **user-authored route lists** (one per role and step kind). It keeps a quota ledger per
  account, fed by provider counters and headers, and sorts limit outcomes into their own types (a congested upstream host is not
  the account's daily quota). A circuit breaker per host trusts neither `Retry-After` nor catalogue uptime. Part of every allowance
  is kept for interactive steps. Background runs park at a spent quota and resume after the reset. The UX adds a plan card that
  prices calls against quota, a quota meter, a stall card and transparent fallbacks.
- **Not possible for free** [I]:
  - guaranteed interactive latency on a single shared free host;
  - a Standard-effort campaign in one day on one free provider (13–18 days of OpenRouter's 50 a day);
  - free cloud without an account;
  - one free route that has strict schemas, no retention, a permissive content policy and campaign capacity together;
  - any free cloud model offered today, because none is qualified per step kind yet (D045).
- **Honest upgrade paths** [I]:
  - A local model: no limits. A 3–4B session model on a GPU, or a tiny CPU model if doc 53's experiments pass.
  - A small paid pinned backstop with a hard daily cap. Buying 10 OpenRouter credits once (about $10.80) also lifts the free tier
    to 1,000 a day. The backstop cost under $0.01 a day at K = 1 and at most $0.06 a day at Standard K.
  - The user's own paid key (doc 40's presets).
  - The no-AI path, always.
- **Owner decisions needed** (§6, Open questions):
  - the UX standard;
  - whether a user-authored route list may move a call to another endpoint or model on a 429 without a click per switch (D023
    decision 3; doc 38 §4.6);
  - the release set of free presets: at least two free providers plus local;
  - whether the free flow offers the capped paid backstop.

## 1. The workload

### 1.1 How it is counted [I on V per doc 40]

- **Source.** `tools/cost-model/cost_model.py`: its workflows, knobs and repair rates, imported read-only. Calls per decision =
  K × (1 + r + r²) at R = 2, with the cost model's repair rates r [U] (Pick 0.03, enum Fill 0.08, extraction 0.10, text 0.12, Compose
  0.25, explain 0.05). All 35 workflow × strategy rows of the cost model (strategies B, C, C+eff, D, E, F and G over five workflows)
  are reproduced exactly; the simulator's tests check its own expansion against them.
- **Tokens** use the repository's 3.5 bytes per token. They are product-sized: a Pick capsule is about 2.3K tokens and a text-slot
  capsule about 3.1K, of which about 1.19K per Pick decision are uncached (doc 40 §1.1, §5.1). Lean prompts, like the batteries of
  docs 44, 46 and 48, are about 0.2–0.5K tokens.
- **Time.** Cloud latencies per step are placeholders [I] (Pick 1.0 s, enum Fill 1.4 s, text slot 2.0 s, Compose 4.0 s, explain
  2.5 s), from first-chunk times of 0.73–3.14 s in doc 48 §1.1. At most 8 cloud calls are in flight (doc 38 §4.5 [I]); a local
  model serves one call at a time. The layer order is our reading of doc 25 §4.1 and doc 38 §8 [I].
- **Strategies beyond the cost model's**, marked as such: **B-quick** (K 1/1, R 1), **B-adaptive** (DG021; Pick K averages 2.2),
  **B-thorough** (K 4/4, R 3), **F-cascade** (doc 53 §4.3: a local one-pass Pick with a 20% re-ask and 23% sent to the cloud at
  K = 1; needs an owner decision) and **L** (everything local).

### 1.2 Per workflow at Standard (strategy B) [I]

| Workflow | Decisions | Cloud calls (Pick / Fill / text / Compose / explain) | Ready at once | Busiest minute | Sequential rounds (first / expected / worst) | Input tokens per call | Model work, unthrottled | At 20 requests a minute |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| campaign-from-brief (8 missions) | 273 | **650.4** (204.1 / 18.6 / 427.7 / – / –) | 352 (stage S7) | 315 | 14 / 22.4 / 42, plus 2 user gates | 2,986 | 151 s (571 s with the gates) | 1,929 s |
| session-30min (12 requests) | 35 | **60.0** (34.0 / 15.5 / – / – / 10.5) | 8 | 10 | 3 / 3.3 / 9 per request | 2,172 | slowest request 6.6 s | no request slowed |
| write-briefing (11 slots) | 11 | 25.0 (text) | 22 | 25 | 1 / 2.2 / 3 | 3,358 | 8 s | 64 s |
| cutscene-director (30-s intro) | 13 | 26.9 (15.5 / 5.5 / 2.3 / 2.6 / 1.1) | 15 | 26 | 4 / 5.4 / 12 | 2,543 | 14 s | 70 s |
| populate-town | 2 | 4.2 (3.1 / 1.1 / – / – / –) | 3 | 4 | 2 / 2.2 / 6 | 2,578 | 2.6 s | 2.6 s |

- **The campaign burst.** Stage S7 releases 352 text calls at once. At doc 38's cap of 8 concurrent calls the model work takes 151 s.
  At 20 requests a minute it takes about 32 minutes. Finishing the cloud work within 10 minutes needs 65 requests a minute; within 30
  minutes, 21.7.
- **The chain.** At unlimited concurrency a campaign's critical path is about 32 s. Adaptive K (26.6 expected rounds), doc 40's D and
  G escalations (31.8 and 35.9) and the F-cascade (38.8) cut calls but lengthen the chain.
- **A naive chat agent** (doc 40 strategy A, the comparator) sends single requests of up to 118,180 tokens in a campaign and 37,780 in
  a session. That is above Groq Free's 8,000 tokens a minute, so it cannot run there at all. Every typed capsule is at most 4,510 tokens.

### 1.3 Strategies: cloud and local calls per run [I]

| Strategy | What changes | Campaign: cloud / local | Session: cloud / local | Expected campaign rounds |
| --- | --- | --- | --- | --- |
| B | Standard, all cloud | 650.4 / 0 | 60.0 / 0 | 22.4 |
| B-quick | K 1/1, R 1 | 299.2 / 0 | 37.2 / 0 | 18.8 |
| B-adaptive | Stop at decisive agreement (DG021) | 595.9 / 0 | 51.0 / 0 | 26.6 |
| B-thorough | K 4/4, R 3 | 1,144 / 0 | 71.4 / 0 | 24.3 |
| F | Pick and Fill on a local model (doc 40 R14) | 427.7 / 222.7 | 10.5 / 49.5 | 22.4 |
| F-cascade | Tiny local stage; 20% re-ask; 23% to the cloud (doc 53 §4.3) | 447.6 / 104.0 | 16.7 / 32.2 | 38.8 |
| G | Doc 40's cheapest cloud mix (escalations, re-runs) | 726.5 / 0 | 67.5 / 0 | 35.9 |
| L | Everything local | 0 / 650.4 | 0 / 60.0 | 22.4 |

Moving Pick and Fill local cuts a session's cloud calls 5.7 times (60 to 10.5). A campaign's roughly 428 text calls stay in the cloud
unless the text is written locally (L) or from templates.

### 1.4 Four user days against the free limits, with no congestion [I]

The days are illustrative [I]. **light-session**: 30 minutes, 12 requests (4 explain or teach, 5 small edits, 3 lint fixes).
**mission-build**: about 2.5 hours (2 sessions, 3 towns, a briefing plus 3 re-rolled slots, a cutscene plus a re-run). **campaign
day**: about 3 hours (a campaign from a brief, then 2 sessions, 2 missions' text re-rolled, 2 towns). **heavy-creator**: about 8
hours (a campaign, 2 mission builds, 8 sessions, 3 text re-rolls).

| Day | Strategy B cloud calls (interactive / background) | Busiest minute / hour | Strategy F cloud calls (local) | Share served by OpenRouter at 50 a day: B / F | at 1,000 a day: B | Groq, one model, product / lean capsules: B | Cloudflare days of neurons on Gemma 4 26B-A4B, product / lean: B |
| --- | --- | --- | --- | --- | --- | --- | --- |
| light-session | 60 (60 / 0) | 10 / 60 | 10.5 (49.5) | 83% (first refusal after 25 min) / 100% | 100% | 100% / 100% (worst response 125 s / 6.6 s) | 0.13 / 0.02 |
| mission-build | 195 (195 / 0) | 28 / 111 | 62.4 (132.6) | 26% / 80% | 100%; the briefing stretches from 8 s to 64 s | 43% / 100% | 0.47 / 0.09 |
| campaign day | 879 (137 / 741) | 310 / 752 | 548.5 (330.1) | 6% (17.6 days of quota) / 9% | 100%; the campaign block stretches from 571 s to 2,299 s | 9% / 94% | 2.46 / 0.23 |
| heavy-creator | 1,430 (639 / 791) | 310 / 752 | 744.4 (685.9) | 4% (28.6 days) / 7% | 70% | 6% / 59% | 3.79 / 0.46 |

What the workload says [I]:

1. **Interactive bursts are small**: 10 to 28 calls in a minute, one request's chain is 3 rounds. The heavy load is bulk text (stage
   S7, re-rolls): background work that can wait, queue and cross a quota reset.
2. **At 1,000 requests a day OpenRouter's quota is ample** for every day but the heavy one; 20 a minute never delays a session request
   and only stretches bulk blocks. **At 50 a day**, one session already exceeds the quota at Standard.
3. **Capsule size decides the token-capped tiers.** On Groq and Cloudflare, lean capsules make a campaign day fit (94% on one Groq
   model; 0.23 of a day's neurons), product-sized ones do not (9%; 2.46 days). A lean-capsule budget matters as much as call counts.
4. **None of this counts congestion.** §2.3 shows why that is the part that decides the experience.

## 2. The limits, and how the free endpoints behaved

### 2.1 Free limits on the user's own account [V, read 2026-09-27, re-read at about 21:50 UTC; no change]

Only services that doc 50 allows as a preset on the user's own account are listed. Doc 50 §2.1 records why the others are excluded:
OVHcloud's anonymous tier (screening only), Google AI Studio, Mistral, Z.ai, the NVIDIA trial, Cerebras and Cohere.

| Service | Requests | Tokens or units | Scope | Reset | What a limit looks like | Structured output |
| --- | --- | --- | --- | --- | --- | --- |
| **OpenRouter** `:free` | 20 a minute; 50 a day, or 1,000 a day once 10 credits have ever been bought (lifetime purchases, not the balance) | — | The account, shared by every `:free` model; more keys or accounts do not raise it | 00:00 UTC | `GET /api/v1/key` reports `free_model_daily_requests` (`used`, `limit`, `remaining`) without a prompt; upstream throttling returns 429 with `provider_name` and a short `retry_after` (§2.3) | Per endpoint: Qwen3.8-27B `:free` lists `structured_outputs`; Gemma `:free` offers `response_format` only |
| **Groq Free** | 30 a minute, 1,000 a day, per model | 8,000 tokens a minute, 200,000 a day, per model; cached tokens do not count (automatic caching on gpt-oss) | The organisation, per model | Mechanics [U] | 429 with `retry-after` and `x-ratelimit-*` headers | `strict: true` on gpt-oss-20b, gpt-oss-120b and Qwen3.8-27B |
| **Cloudflare Workers AI** | 300 a minute for text generation (20 for paid-only models) | 10,000 neurons a day; per MTok in / out: Gemma 4 26B-A4B 9,091 / 27,273, gpt-oss-20b 18,182 / 27,273, Qwen3.8-27B 40,909 / 290,909 | The account | 00:00 UTC | Past the allowance requests "fail with an error"; code [U] | JSON mode, which "can't guarantee" the schema |
| **Hugging Face** routed credits | Unpublished [U] | $0.10 a month | The user | Monthly | Status code at exhaustion [U] | Per provider flag |
| **Ollama Cloud** (watch only) | 1 concurrent request; extra requests queue | Token-metered; the starter allowance is unpublished [U] | One account per person | Monthly from sign-up | [U] | [U] |

Sources: OpenRouter's limits page and key API; Groq's rate-limit, prompt-caching and structured-output pages; Cloudflare's Workers AI
pricing (updated 2026-09-17) and limits pages; Hugging Face's Inference Providers pricing; Ollama's pricing and cloud pages (§Sources;
doc 50 §2.2; `data/free-llm-services.csv`). The per-minute figure for Cloudflare and the neuron rates for four more models are new
since doc 50.

### 2.2 Capacity in harness terms [I]

Arithmetic on §1's demand and §2.1's limits. It assumes product-sized capsules, no congestion, and 300 reasoning tokens a call on
gpt-oss (reasoning cannot be switched off there; lowest effort), none elsewhere.

| Route | 30-minute sessions a day: Standard / K = 1 / Pick and Fill local | Campaign (Standard) |
| --- | --- | --- |
| OpenRouter `:free`, 50 a day | 0.83 / 1.34 / 4.75 | 13 days (8.6 with Pick and Fill local) |
| OpenRouter `:free`, 1,000 a day | 16.7 / 26.8 / 95 | 0.65 days of quota; at least 33 minutes at 20 a minute |
| Groq, gpt-oss-20b or -120b (bound by tokens a day; cache credit assumed) | 3.1 / 4.2 / 13.1 | 4.5–10 days on one model; each of the three models has its own budget |
| Groq, Qwen3.8-27B (no cache credit assumed) | 1.5 / 2.5 / — | — |
| Cloudflare, Gemma 4 26B-A4B | 7.8 / 12.2 / — | 0.53 campaigns a day |
| Cloudflare, Granite 4.0-H-Micro | 40.8 / 62.1 / — | 2.85 campaigns a day (a Pick-class model; not a writer) |
| Hugging Face $0.10 a month, Qwen3-4B-Instruct-2507 | 71 a month / 111 a month / — | 4.9 campaigns a month; 0.66 on Gemma 4 26B-A4B |

### 2.3 The observed free endpoint [V-obs]

Plotroom's round-0 tooling (doc 48 §6.0) ran synthetic Pick menus against `qwen/qwen3.8-27b:free` on 2026-09-27. The call was pinned
to ModelRun (fp4), with `zdr` on and reasoning off. The key had a $0 limit, so no call could spend money. After three 429s in a row
the tool stopped, then retried about every three minutes until six cycles in a row made no progress.

| Measure | Value |
| --- | --- |
| Window | 20:17:50 to 20:35:26 UTC (17.6 minutes) |
| Calls / HTTP attempts | 9 / 13 |
| Answered | 1 (HTTP 200 in 804 ms; 239 prompt and 6 completion tokens; strict parse; correct; $0; no reasoning tokens) |
| Refused | 12 × HTTP 429 "temporarily rate-limited upstream", `provider_name: ModelRun`; none was the account's daily cap |
| Speed of a refusal | 0.35–0.56 s |
| `retry_after` on the refusals | 0.12–0.77 s, while the throttle lasted more than 15 minutes |
| Goodput | 0.057 requests a minute against 20 nominal (7.7% of attempts, 11% of calls) |
| Daily counter | `used` moved from 4 to 5 with the one answer and with nothing else: it stayed at 4 through the 3 refusals before the answer and at 5 through the 9 after it |
| Catalogue uptime at 20:30 UTC | Status 0, 30-minute uptime 100.0% (1-day 98.2%), in the middle of the throttle |

What it shows:

- **Upstream 429s did not count against the 50 a day** in this sample. That partly answers doc 50 OQ12; whether OpenRouter's own
  platform 429s count is still [U]. Doc 48 §6.0's tool counts every attempt anyway, which is the safe side.
- **Neither `retry_after` nor catalogue uptime is an availability signal** for a `:free` host. How OpenRouter computes uptime is not
  documented [U].
- A key with a $0 limit can call `:free` models, which answers one of the questions doc 48's run Z01 was planned to settle.
- **At this goodput** a light session would take 17.6 hours at Standard (3.1 hours with Pick and Fill local), a mission build 57
  hours, and a campaign day 257 hours [I].
- **One window, one host, one evening.** Time-of-day patterns are unknown [U]. The simulator's "observed" congestion profile is
  calibrated on this window alone (§3.1).

### 2.4 Paid pinned endpoints the same evening [V-obs]

The D044 screening run (battery S, doc 50 §5.2) went through OpenRouter between 22:18 and 23:30 UTC the same day. It used eleven
paid endpoints, one after another, each pinned with `only`, `allow_fallbacks: false` and `require_parameters: true`. The prompts were
battery-sized: about 270–490 tokens (p10–p90; median about 350). Only reliability is reported here; the screening results belong to
docs 49 and 50. Latencies are over every call, including those that gave up.

| Endpoint | Calls | Attempts | HTTP 429 | Calls that failed | Latency p50 / p90 / max |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 26B-A4B, CoreWeave bf16 | 238 | 305 | 69 (23% of attempts, over 7 minutes) | 2 gave up after 5 attempts | 0.71 / 2.73 / 14.5 s |
| Gemma 4 26B-A4B, DeepInfra fp8 | 256 | 257 | 1 | 0 | 0.91 / 1.89 / 4.6 s |
| Ministral 3 3B, Mistral (ZDR) | 417 | 417 | 0 | 1 (an error inside an HTTP 200) | 0.53 / 0.82 / 1.6 s |
| Qwen3-30B-A3B-2507, Nebius fp8 | 236 | 236 | 0 | 0 | 0.65 / 1.53 / 3.7 s |
| Qwen3-30B-A3B-2507, SiliconFlow fp8 | 236 | 236 | 0 | 0 | 1.49 / 4.43 / 8.8 s |
| Qwen3.5-35B-A3B, DeepInfra fp8 | 256 | 256 | 0 | 0 | 0.85 / 1.24 / 3.1 s |
| Qwen3.5-35B-A3B, Parasail fp8 | 256 | 257 | 1 | 0 | 0.84 / 1.27 / 3.2 s |
| Qwen3.6-35B-A3B, AkashML fp8 | 256 | 256 | 0 | 0 | 0.62 / 0.84 / 1.6 s |
| Qwen3.6-35B-A3B, Parasail fp8 | 256 | 256 | 0 | 0 | 0.86 / 1.49 / 3.2 s |
| gpt-oss-20b, AkashML fp4 | 124 | 125 | 1 | 0 | 1.30 / 2.63 / 10.6 s |
| gpt-oss-20b, DeepInfra bf16 | 220 | 316 | 100 (32% of attempts, over 10 minutes, to the end of its run) | 4 gave up after 5 attempts | 1.33 / 4.93 / 24.6 s |

**Paid pinned hosts throttle too.** Two hosts in eleven refused a quarter to a third of their attempts for 7–10 minutes; the other
nine refused 3 in 2,296. Throttling is per endpoint, not per provider: DeepInfra's fp8 Gemma and Qwen3.5 endpoints refused 1 attempt
in 513 while its bf16 gpt-oss-20b refused 100 in 316. A paid backstop therefore needs two hosts per model, as D044 P2 already plans
for screening. The simulator's "paid" congestion placeholder (§3.1) matches nine of the eleven hosts and is optimistic for two; S6's
one paid endpoint is the DeepInfra Gemma that stayed clear.

### 2.5 Local models: no limits, slower [V per docs 44, 46; V-obs for doc 49's preliminary rows; I for product-capsule estimates]

| Local option (reference box: GTX 1070 8 GB, 4-core AVX2 CPU) | Measured on battery prompts | Estimated with product capsules | Latency class (doc 53 §1.1) |
| --- | --- | --- | --- |
| 3–4B session model on the GPU (Gemma 4 E4B QAT, Qwen3.5-4B) | Pick p50 0.51 s (Ollama) to 1.09 s (llama.cpp Vulkan); Fill 1.47–2.22 s; explain 2.3–2.55 s; 40–49 tokens/s | Pick with a leading `why` 2.7–5.8 s; with a compact local profile 0.6–1.4 s; 3–5 minutes of model time a session; 37–67 minutes a campaign | L1–L2 with a compact profile |
| Granite 4.1 3B on the GPU | Pick 0.31 s; 49–56 tokens/s | — | L1 |
| MoE offload, Qwen3-30B-A3B-2507 (`--n-cpu-moe 39`) | Pick p50 6.5–7.5 s; Fill 11.3 s; explain 17.2 s (preliminary, doc 49 pending) | Pick 21–38 s; 4–7.5 hours a campaign | L4 only |
| 4B on the CPU only (Qwen3.5-4B smoke test, n = 2) | 15 prompt tokens/s; 7 generated tokens/s; an uncached Pick took 12 s | Pick 82–85 s; with a compact profile 20 s | Not interactive |
| Tiny CPU model, 0.4–1B (doc 53 §2.6, unmeasured) | — | One-pass letter Pick 0.7–1.3 s with ~200 uncached tokens; 4.4–8.2 s with 1.19K uncached | L1 only with a cached prefix |
| Tiny CPU model, 1–2B (unmeasured) | — | 2.0–3.6 s compact; 12–22 s product | L2–L3 |

A local model is the only AI path with no account, no rate limit, no data terms and no cost (doc 53 §4.10). Its limits are compute
and latency. It also loses the GPU to the game during Preview (D018).

## 3. Simulation

### 3.1 Method [I]

[`tools/quota-sim/`](../../tools/quota-sim/README.md) is a seeded, discrete-event replay of a user day. It uses the Python standard
library only and makes no network calls. Its README has the full definitions; in short:

- **A day** is a list of blocks with planned start times. Sessions are 12 requests 150 s apart, and each request waits for the previous
  answer. A campaign includes the premise-pick (120 s) and outline-approval (300 s) user gates. The horizon is the planned hours plus
  one; work not done by then is "cut". No UTC reset falls inside a day, and the user starts with full allowances.
- **A run** is a sequence of layers of independent decisions. Within a layer, the K samples, repair rounds and cascade stages run as
  phases, and each phase waits for the one before. Repairs are drawn per call at the cost model's rates [U].
- **Pools** meter what each provider meters:
  - OpenRouter per account, per minute and per day;
  - Groq per model, requests and tokens, with cached prompt tokens exempt on gpt-oss;
  - one Cloudflare neuron pool;
  - Hugging Face monthly credits;
  - S6's paid endpoint, under a daily hard cap.
  Every attempt fills the per-minute window; only answered calls spend the daily allowance (§2.3).
- **Congestion** is modelled per upstream host as a two-state Markov chain (clear or congested). A congested host refuses an attempt
  with a 429 in 0.35–0.56 s [V-obs].
  - **Profiles:** "observed" [V-obs] fails 0.91 of attempts, against 12 of 13 measured, with congested spells of about 20 minutes;
    "moderate" [U] is congested a quarter of the time in 10-minute spells; "low" [U] and "paid" [U] are near clear.
  - **Levels** say which hosts get which profile. "moderate" and "observed" throttle only OpenRouter `:free` hosts, the only ones
    measured. "stress" also puts Groq, Cloudflare and Hugging Face on "moderate".
- **Retries.** A single-route strategy retries the same endpoint with backoff: 2 s doubling to 60 s, 10 retries, then a probe every 3
  minutes (doc 51 Z16). A multi-route strategy puts a throttled endpoint on a shared cooldown (15 s doubling to 600 s) and re-routes the
  call at once. A call the user is waiting on gives up after 60 s and keeps the code default (doc 25 §10.1). A call that finds every
  eligible allowance spent parks until the reset (`BudgetLimited`, doc 38 §3.4).
- **Routing** (multi-route): among the endpoints listed for the call's step kind, it picks the one that can start soonest, plus 1 s per
  rank of preference. It skips a spent allowance, a per-minute token cap smaller than the call, and a cooldown. Background work may use
  only 70% of each daily allowance, so 30% stays for interactive steps. S6's paid endpoint comes last, and only when no free route can
  start within 10 s (interactive) or 2 minutes (background), compared on start times.
- **Held slots** [I]. A cloud call keeps its concurrency slot while it waits for a window, a cooldown or a backoff. That is conservative
  for the single-route strategies, whose calls back off on one host.
- **Tokens by effort** [I]. Groq's cache credit and the size of a packed text call use each workflow's cached share at the effort the
  strategy runs: at K = 1 no per-decision cache breakpoint is shared by sibling samples, so the share is lower (a session's 0.577
  against 0.673 at Standard; recomputed from the cost model by a unit test).
- **Grid:** 9 strategies × 3 congestion levels, plus the reference run, × 4 days × seeds 1, 2 and 3 = 336 runs in about 15–25 s. The
  results are kept outside the repository; the command is in the tool's README.
- **Evidence the tool is right:** 31 unit tests pass (`python -m unittest discover -s tools/quota-sim`, re-run for this doc). They cover:
  - known values: the research profile's call counts for 8 workflows × 4 strategies, each day's unthrottled span within 0.5%, and
    both cached shares against the cost model;
  - determinism;
  - both sides of every pool limit;
  - the congestion calibration;
  - the router's rules, including the paid backstop's 10-s threshold whatever the route list's length;
  - product rules in the data: every route entry screened plausible for its step kind, one account per provider, and no route to an
    endpoint a product rule excludes (Gemma 4 `:free`, §3.7);
  - degraded answers (a later sample, repair or escalation failed) reported apart from clean ones;
  - forward progress: every scenario ends, and no interactive wait exceeds the ceiling.

  One scenario was replayed for this doc and matched the stored grid: the campaign day under S4 at "observed", seed 1. Its campaign
  block took 737.7 s, with interactive waits at p90 1.8 s and 11.5 s at most.

### 3.2 Strategies simulated

| Id | What it adds | Machine |
| --- | --- | --- |
| REF | Reference: Standard on one unlimited, never-congested endpoint (not a product option) | any |
| S0 | One free provider: OpenRouter `qwen3.8-27b:free` at 50 a day, Standard, per-call backoff | any |
| S1 | S0 plus call reduction: cloud K = 1 (validators and repairs kept); bulk independent text packed 4 slots a request [I, a proposal]; 25% of explanations from the exact-hash memo (doc 40 R13) [U]; 50% of intent Fills skipped because a gesture or menu started the step (doc 53 DP-01) [U] | any |
| S2 | S1 plus a local 3–4B GPU model for Pick and Fill at Standard K | 8 GB GPU |
| S3 | S1 plus quota- and congestion-aware routing over the user's own OpenRouter, Groq, Cloudflare and Hugging Face accounts. Only endpoints screened plausible for a step kind are listed (§3.7) | any |
| S4 | S3 plus doc 53's tiny local cascade for Pick and Fill: one CPU pass, 20% re-ask, 23% escalated to S3's routing | CPU only |
| S4-noGroq | S4 without Groq (its answer on fictional military content is pending) | CPU only |
| S5-single | S1 at OpenRouter's 1,000-a-day tier: does buying 10 credits fix a single free provider? | any |
| S5 | S4 at the 1,000-a-day tier | CPU only |
| S6 | S5 plus a paid pinned endpoint (Gemma 4 26B-A4B at DeepInfra, $0.07 / $0.34 per MTok) as a last resort under a $0.25 daily hard cap | CPU only |

Routing preference [I] puts strict-schema, zero-retention endpoints first for Pick and Fill, and the largest plausible writers first
for text. Pick: gpt-oss-20b and Qwen3.8-27B on Groq, the OpenRouter Qwen, Qwen3-4B-2507 on Hugging Face, Granite 4.0-H-Micro and
Gemma 4 26B-A4B on Cloudflare, then gpt-oss-120b on Groq. Text: the OpenRouter Qwen, Qwen3.8-27B and gpt-oss-120b on Groq, then
Gemma 4 26B-A4B on Cloudflare. In the multi-route runs under observed congestion the calls actually landed on Cloudflare's Gemma for
text (81–84 a campaign day) and on Groq for Pick, Fill, Compose and explanations. Without the tiny stage (S3), Hugging Face and
Granite also took Pick overflow (Hugging Face 32–69 calls on campaign and heavy days). OpenRouter `:free` served 0–21 calls a day.

### 3.3 Results with congestion as observed [I; means over 3 seeds]

"Complete" counts the seeds on which every block finished and every decision was answered, either by a model or on purpose without
one. "Answered" is the share of decisions. "Wait" is the time an interactive call spent waiting for limits, slots, cooldowns or
backoff before its answered attempt started. It **excludes** the model's own latency, so p90 / max are given in seconds. For a local
call it includes queueing for the one local model. "Answered" includes **degraded** decisions, whose first answer stands although a
later sample, repair or cascade escalation failed: none for S3 to S6 under observed congestion, 1–7 a day for S4-noGroq, and 19–26 on
its heavy day.

| Strategy | light-session: Complete · Answered · Wait p90 / max | mission-build | campaign day | heavy-creator |
| --- | --- | --- | --- | --- |
| REF | 3/3 · 100% · 0 / 0 | 3/3 · 100% · 0.9 / 4.6 | 3/3 · 100% · 0 / 0 | 3/3 · 100% · 0 / 4.7 |
| S0 | 0/3 · 34.3% · 60 / 60 | 0/3 · 26.0% · 60 / 60 | 0/3 · 5.0% (364 decisions parked) | 0/3 · 3.0% (661 parked) |
| S1 | 0/3 · 41.9% · 60 / 60 | 0/3 · 38.1% · 60 / 60 | 0/3 · 16.5% (319 parked) | 0/3 · 17.4% (562 parked) |
| S2 | 0/3 · 84.8% · 60 / 60 | 0/3 · 75.9% · 60 / 60 | 0/3 · 76.4% (90 parked) | 0/3 · 72.0% (190 parked) |
| S3 | **3/3 · 100% · 0 / 0.5** | **3/3 · 100% · 0.4 / 57.9** | **3/3 · 100% · 0 / 1.4** | 2/3 · 100% · 0 / 60 |
| S4 | **3/3 · 100% · 0 / 1.9** | **3/3 · 100% · 1.7 / 16** | **3/3 · 100% · 1.2 / 13.7** | **3/3 · 100% · 1.6 / 13** |
| S4-noGroq | 3/3 · 100% · 1.6 / 60 | 3/3 · 100% · 2.8 / 60 | 1/3 · 90.4% (38 cut) · 7.3 / 60 | 1/3 · 99.3% (2.7 defaults kept, 2.3 cut) · 5.2 / 60 (26 waits over 10 s) |
| S5-single | 0/3 · 41.9% · 60 / 60 | 0/3 · 38.1% · 60 / 60 | 0/3 · 83.9% · 60 / 60 | 0/3 · 69.2% · 60 / 60.5 (1,715 upstream 429s) |
| S5 | as S4 | as S4 | as S4 | as S4 |
| S6 | as S4 (no paid call) | 3/3 · 100% · 1.5 / 10 (0.7 paid calls, $0.0005) | as S4 (no paid call) | as S4 (0.3 paid calls, $0.0003) |

Other figures from the same runs:

- **S4 splits the work** between the cloud and the tiny local model, per day: 12 cloud and 24 local calls (light), 35 and 65
  (mission), 150 and 165 (campaign), 265 and 336 (heavy). It left 36–50 of OpenRouter's 50 free requests unused, because the router
  kept away from the congested host (4–50 under moderate congestion).
- **The campaign block took 11–12 minutes under S4** (666–738 s), against 10 minutes (583–591 s) for REF.
- **Moderate congestion** changes the single-route picture only a little. S0 answers 78% of a light session, 31% of a mission build
  and 6% of a campaign day, because the quota runs out. S4, S5 and S6 complete every day. S3 completes the heavy day on 1 of 3 seeds,
  and S4-noGroq completes the campaign day on 2 of 3 and the heavy day on none.

### 3.4 Results when every free host is throttled ("stress") [I]

| Strategy | light-session | mission-build | campaign day | heavy-creator |
| --- | --- | --- | --- | --- |
| S3 | 2/3 · 97.1% · 0.4 / 60 | 0/3 · 93.3% · 1.4 / 60 | 1/3 · 99.0% · 0.4 / 60 | 0/3 · 97.7% · 0.9 / 60 |
| S4 | 3/3 · 100% · 0 / 60 | 1/3 · 95.5% · 1.9 / 60 | 2/3 · 99.7% · 1.5 / 60 | 1/3 · 99.7% · 1.7 / 60 |
| S4-noGroq | 2/3 · 99.0% · 1.9 / 60 | 0/3 · 89.2% · 9.0 / 60 | 0/3 · 90.9% · 13.7 / 60 | 0/3 · 96.5% · 7.0 / 60 |
| S5 | as S4 | as S4 | as S4 | as S4 |
| **S6** | **3/3 · 100% · 0 / 3** (0.7 paid calls, $0.0002) | **3/3 · 100% · 1.7 / 10** (2.3 paid calls, $0.0013) | **3/3 · 100% · 1.5 / 13.7** (5.7 paid calls, $0.0013) | **3/3 · 100% · 1.6 / 13** (14 paid calls, $0.0050) |

S0, S1, S2 and S5-single behave as in §3.3, since only OpenRouter's host changes between levels and it is already throttled there.
Across every S6 run the most any day spent on the paid endpoint was about $0.009, 0–25 paid calls against a $0.25 cap.

### 3.5 Sensitivity runs [I]

These runs used the tool's own functions with run-time overrides and changed no tracked file. Each cell gives the seeds that
completed, out of 3.

**Which call-reduction measures carry the result** (S4 unless named; "observed" and "stress"):

| Variant | mission-build | campaign day | heavy-creator | Notes |
| --- | --- | --- | --- | --- |
| S4 (K = 1, packing, memo, intent skip) | 3/3 · 1/3 | 3/3 · 2/3 | 3/3 · 1/3 | Cloud calls 35 / 150 / 265 |
| Without packing | 3/3 · 1/3 | 3/3 · 2/3 | 3/3 · 1/3 | Campaign cloud calls 311 |
| Without packing, memo or intent skip | 3/3 · 1/3 | 3/3 · 2/3 | 3/3 · 1/3 | — |
| **Standard K on the cloud** (packing kept) | 3/3 · 3/3 | 3/3 · 2/3 | **1/3 · 0/3** (11 parked) | Campaign block 23–34 minutes, against 11–12 |
| "Bare": Standard K, no packing, memo or skip | 3/3 · 1/3 (wait p90 55 s under stress) | 0/3 · 0/3 (82% answered) | 0/3 · 0/3 (84–90%) | — |
| Bare at 1,000 a day (S5) | 3/3 · 1/3 | 0/3 · 0/3 (77%; 88 cut) | 0/3 · 0/3 (49–50%; about 350 cut) | Worse than 50 a day, see below |
| **Bare with the paid backstop (S6)** | 3/3 · 3/3 | **3/3 · 3/3** | **3/3 · 3/3** | 149–229 paid calls on campaign and heavy days; at most $0.044–0.058 a day; campaign block 29–34 minutes |

**Which providers carry the result** (S4 at "observed"):

| Variant | light-session | mission-build | campaign day | heavy-creator |
| --- | --- | --- | --- | --- |
| S4 | 3/3 | 3/3 | 3/3 | 3/3 |
| Without Groq | 3/3 | 3/3 | **1/3** (90.4%; 38 cut) | **1/3** (99.3%; 26 waits over 10 s) |
| Without Cloudflare | 3/3 | **0/3** (93.3%; 7 defaults kept) | **0/3** (88.7%; 44 parked) | **0/3** (57.8%; 246 cut) |
| Without Groq and Cloudflare (OpenRouter, Hugging Face, local) | 0/3 (83.8%; wait p90 60 s) | 0/3 (70.5%) | 0/3 (39.9%) | 0/3 (62.0%) |
| OpenRouter `:free` and the tiny local model only | 0/3 (83.8%) | 0/3 (71.1%) | 0/3 (28.8%) | 0/3 (47.4%) |

Without Cloudflare, Groq carries the text alone, and its 8,000 tokens a minute per model is the bottleneck. A 4-slot packed text call
counts 8.3–8.6K tokens, more than Qwen3.8-27B's cap (it can still run on gpt-oss-120b, whose cached tokens do not count). Packing is
not the cause, though: without Cloudflare and without packing, the mission build completes on no seed (5 defaults kept on average).

**How fast the tiny CPU stage must be** (S4 at "observed"; the data assume 1.5 s per Pick; only the Pick latency varies, Fill stays at
3 s). Waits over 10 s per day, and the longest wait. Local calls have no 60-s ceiling in the tool:

| Tiny-stage Pick latency | light-session | mission-build | campaign day |
| --- | --- | --- | --- |
| 1.5 s (0.4–1B, one pass, cached prefix) | 0 · 1.9 s | 0.7 · 16 s | 1.3 · 13.7 s |
| 6 s (0.4–1B, product capsule) | 0 · 7.8 s | 1.7 · 25.5 s | 1.3 · 13.7 s |
| 15 s (1–2B, product capsule) | 3.0 · 19.5 s | 9.0 · 63.7 s | 7.7 · 19.2 s |

**How much the tiny stage may escalate** (the data assume 23%, the midpoint of doc 53's 13–33%, which was measured on 3–4B models;
a 0.4–1B model would likely escalate more [U]). S4 at "observed": seeds completed · longest wait; S6 under "stress" in the last
column:

| Escalated to the cloud | light-session | mission-build | campaign day | heavy-creator | S4 cloud calls a day | S6 under stress |
| --- | --- | --- | --- | --- | --- | --- |
| 23% | 3/3 · 1.9 s | 3/3 · 16 s | 3/3 · 13.7 s | 3/3 · 13 s | 12 / 35 / 150 / 265 | 3/3 on every day; at most $0.009 a day |
| 40% | 3/3 · 1.9 s | 3/3 · 41.7 s | 3/3 · 13.7 s | 3/3 · 42.8 s | 15 / 49 / 176 / 314 | 3/3 on every day; at most $0.009 |
| 60% | 3/3 · 1.9 s | 3/3 · 42.1 s | 3/3 · 13.7 s | 3/3 · 42.8 s | 18 / 60 / 199 / 366 | 3/3 on every day; at most $0.012 |

Completion survives up to 60% escalation; the price is a few longer interactive waits (still under the 60-s ceiling), which the stall
card (UX2) would show.

### 3.6 What the results mean [I]

1. **One free provider cannot meet any reasonable standard**, whatever the quota. Buying the 1,000-a-day tier (S5-single) removes
   parking but not congestion: 38–84% answered, with waits at the ceiling.
2. **Diversity of routes is the fix**: several providers the user signed up for, one account each, behind a router that routes
   around a congested host instead of retrying it. A multi-route S3 or S4 day spent more on each provider's own limits than on
   waiting.
3. **A local stage removes most interactive dependence on the cloud.** Under S4, an interactive Pick or Fill almost never waits for a
   cloud limit. It needs one of two things: a cached-prefix, compact capsule on a 0.4–1B CPU model, or a 3–4B model on a GPU. A 1–2B
   CPU model with product capsules would add 3–9 stalls a day. A higher escalation rate costs cloud calls and some long waits, not
   completion (§3.5).
4. **Keeping cloud K low matters most for capacity**, more than packing or memo reuse. K = 3 identical-prompt voting bought only 1.6
   points of Pick accuracy on average for three times the calls in Plotroom's records (doc 53 §3) [V per doc 53].
5. **More quota on a congested host can make things worse.** In the "bare" runs (Standard K) the 1,000-a-day tier did worse than 50
   a day. The router kept going back to OpenRouter's host, which stays first for text, after each cooldown. On the campaign day at
   observed congestion that meant 177 upstream 429s against 109 and 77% answered against 82%; on the heavy day, 364 against 152 and
   50% against 90%. With 50 a day that host drops out early. The router must lower the rank of a host it has observed to be unhealthy, not only cool it down
   (§5.2).
6. **A cheap paid backstop turns "usually" into "always".** It spent cents a day even at Standard K, and it is the only strategy that
   survives "stress". It is the user's own money on the user's own account, so it is an opt-in with a hard cap (D026), never a default.

### 3.7 Limits of the model

- **Congestion data.** One 18-minute window on one host calibrates "observed". Congestion on Groq, Cloudflare, Hugging Face and paid
  hosts is a placeholder [U]; "stress" exists because those hosts may throttle too, and §2.4 shows that paid ones do. S6 has one
  paid endpoint on the optimistic "paid" placeholder; two of the eleven paid hosts in §2.4 throttled for 7–10 minutes, so a real
  backstop needs its second host.
- **"Screened plausible" is not "qualified".** No cloud endpoint is qualified for any step kind today (D044, D045). The simulator
  measures time and quota, not quality. K = 1, packing, the tiny cascade and every route entry need quality evidence first (doc 53
  R6; D045 item 4).
- **The tiny stage is assumed.** Its latency (1.5 s a Pick) and its escalation rate (23%, measured on 3–4B models) are placeholders
  until doc 53's experiments run; §3.5 varies both.
- **Terms are modelled only as exclusions.** Content-policy bands (D047) and most data terms are not modelled; they can only shorten
  the route lists. One endpoint is excluded outright: Gemma 4 `:free` on Google AI Studio keeps prompts 55 days, so D046's
  zero-retention default and D045 item 7 rule it out. The data keeps it, marked `excluded_by`, and no route list may name it (a unit
  test checks both), so every table here runs without it. Its removal is not free: without Groq, S4's campaign day completes on 1 of
  3 seeds without it and on 2 of 3 with it.
- **Tokens are product-sized**, the conservative case for Groq and Cloudflare. Lean capsules would widen both (§1.4).
- **Phases are barriers**, and a real scheduler could overlap them, so waits are an upper bound on that account. Calls also hold a
  concurrency slot through backoff and cooldowns (§3.1). Wall time is set mostly by the planned schedule; read it together with
  Complete.
- **Every allowance starts full**, including Hugging Face's monthly $0.10, which S3 can spend in one day (up to 93 calls in the grid); on the
  next day that month it would be gone.
- **Doctrine is assumed changed.** The cascade's escalation to another model and the cross-model route lists of S3 to S6 are not
  allowed by today's doctrine without an owner decision (§6).
- **Not simulated:** single-concurrency services (Ollama Cloud), time-of-day patterns, a quota spent earlier the same UTC day, local
  EXPLAIN on a GPU model (which would remove a session's last cloud calls) and failures of the local runtime.

## 4. A proposed UX standard (proposal, for the owner)

The owner asked whether the experience would be "good enough for our standards". There is no written standard for rate-limited
operation yet. The standard below is written so that the simulator, the replay tests (doc 40 §7) and the run ledger can check it.
It builds on doc 53's latency classes (L1 ≤ 1–2 s for Picks the user waits on, L2 ≤ 2–3 s, L3 ≤ 10 s, L4 background) and on existing
rules: code defaults (doc 25 §10.1), soft deadlines (doc 38 §4.6), resumable `BudgetLimited` (doc 38 §3.4), and no silent model
switch (D023 decision 3; D026 item 3).

| Id | Criterion | Threshold (proposal) | Why |
| --- | --- | --- | --- |
| UX1 | Limit-induced wait on interactive steps | p90 ≤ 2 s per day; the step's total response stays in its doc 53 class at p50 | Rate limits must not turn an L1 Pick into an L3 wait |
| UX2 | Visible stall | Any interactive wait over 10 s shows a non-modal card with the reason and choices (use the default now, try the next route, keep waiting) | Never a silent hang; the 10-s limit is doc 53's L3 budget |
| UX3 | Hard ceiling | At 60 s the code default stands, labelled "default kept: model busy", and can be re-run in one click; on the recommended setup under observed congestion no decision reaches it | Doc 25 §10.1; fail closed, never an automatic yes |
| UX4 | Completion within a day | A light session and a mission build complete within one UTC day's free allowances on the recommended free setup, with nothing parked | A mission build is the everyday unit of work |
| UX5 | Campaign honesty | A campaign-from-brief at the default effort completes the same day on the recommended free setup, or the plan card says before the run how long it will take and why, with the alternatives | The owner's north-star workflow (D005) must not surprise the user |
| UX6 | Answered share | At least 99% of a day's decisions answered by a model or on purpose without one; defaults kept because of limits are at most 1%, each labelled | Degradation is visible and rare |
| UX7 | Plan accuracy | Forecast cloud calls within ±15% of actual; a run the card says "fits today" does not park for quota | Doc 40 §6's honest-numbers rule, applied to quota |
| UX8 | Nothing silent | Every reroute, fallback, park and default kept appears in the run panel and the decision inspector with its reason; no silent model switch; no lost work across a reset or restart | D010 glass box; D023 decision 3; doc 38 §4.1 |
| UX9 | Quota hygiene | At most 2 immediate retries of an interactive call on the same endpoint (doc 51 Z16); a congested host is not probed faster than its cooldown; the ledger never lets a background run spend the interactive reserve | Failed attempts must not burn allowances or minutes |

**Which strategies meet it** (simulated, §3; UX7 to UX9 are design properties the simulator does not test):

| Strategy | Congestion as observed | Stress |
| --- | --- | --- |
| S0, S1, S5-single | Fails UX1–UX6 on every day | Fails |
| S2 | Fails UX1, UX3, UX4 (waits hit the ceiling; campaign text parks) | Fails |
| S3 | Meets it except on the heavy day (a third of a default kept, one wait at the ceiling) | Fails UX4–UX6 on all four days |
| S4, S5 | **Meets UX1–UX6 on all four days** | Meets UX4–UX6 on the light day only (one wait at the ceiling); misses on mission, campaign and heavy days (1–5 defaults kept a day on average) |
| S6 | Meets it | **Meets it on all four days** (longest wait 13.7 s) |

What the standard implies [I]:

- A "recommended free setup" that meets the standard is, today:
  - the user's own OpenRouter, Groq and Cloudflare accounts;
  - a local model for Pick and Fill: the tiny cascade if doc 53 passes, or the GPU session model;
  - cloud K = 1.
- A user who has only OpenRouter's one-click preset gets a **taster**, and the product should say so.
- The only way to meet the standard when every free host is busy is a paid backstop or a local model for the text.

## 5. Design (proposal)

### 5.1 Principles

1. **Route around, do not retry into.** An upstream 429 on a free host is a signal to use another route. It is not a reason to wait
   (§2.3).
2. **Every route is the user's.** One account per provider, created and connected by the user through doc 50 §4's flow. There is no
   Plotroom key or proxy, and the router never creates accounts or keys.
3. **Every route is visible and authored.** The endpoints a call may reach form an ordered route list the user set up or accepted,
   shown on the plan card. Each call records the endpoint and host that served it (D046) and the reason it was chosen.
4. **Interactive first.** Steps the user waits on take precedence over background work, and part of each daily allowance is kept
   for them.
5. **Degrade downward, visibly.** The order is local, then the route list, then the paid backstop if the user enabled it, then the
   code default or template text. Background work parks at a spent quota and resumes after the reset. The fallback is never an
   unannounced bigger model (doc 25 principle 5).
6. **Spend fewer calls before routing more** (§5.3).

### 5.2 The quota-aware router

**Components** (a sketch; proposal-only, not compiled, names not final):

```rust
// Crate: the provider seam (D021). One QuotaPool per (user account, pool the provider meters); never more than one account per provider.
pub struct PoolId(u32);                       // newtype per AGENTS.md; joins CODE-INDEX.md's table when implemented
pub enum Meter { Requests, Tokens { cached_exempt: bool }, Neurons, Usd }
pub struct QuotaPool { id: PoolId, meter: Meter, per_minute: Option<u32>, per_day: Option<u64>,
                       used_today: u64, resets_at: UtcInstant, source: LedgerSource, reserve_interactive: Percent }
pub enum LedgerSource { ProviderCounter, ResponseHeaders, CountedLocally }    // OpenRouter key endpoint, Groq headers, estimate

// What a failed attempt means; each maps to one router action (doc 51 Z15).
pub enum LimitOutcome {
    UpstreamThrottled { host: HostId },                  // e.g. "temporarily rate-limited upstream": cool the host, reroute now
    AccountRateLimited { pool: PoolId, reset_at: UtcInstant },   // per-minute window: pace, then retry the same route
    QuotaExhausted { pool: PoolId, reset_at: UtcInstant },       // daily cap: skip the pool until the reset; never held against the model
    PaymentRequired,                                     // 402: stop; BudgetLimited
    NoEndpointForPolicy,                                 // guardrail 404 (privacy flags): a setup fault, shown to the user
    ModelGone,                                           // removed free id: D045 item 6's clean fallback
    ContentFiltered,                                     // its own outcome, never a wrong answer (D047)
}
pub enum HostHealth { Clear, Cooling { until: UtcInstant, strikes: u8 }, Probing, Demoted { until_session_end: bool } }
pub struct RouteList { role: Role, kind: StepKind, entries: NonEmpty<SetupId>, paid_backstop: Option<(SetupId, UsdCap)> }
```

**The quota ledger.** Each pool is metered the way its provider meters it (§2.1). The ledger:

- reads OpenRouter's `GET /api/v1/key` counter at session start, every few calls and at the end; that read sends no prompt (doc 50
  §4 step 4);
- reads Groq's `x-ratelimit-*` and `retry-after` headers on every response;
- counts Cloudflare neurons and Hugging Face credits locally from reported usage, since their counters are [U];
- persists the counts locally, so a restart the same UTC day does not forget the spend;
- keeps the limits themselves as dated data beside prices (`models.toml`, D026's R1 pattern), with `as_of` and a source, and shows a
  "limits may be out of date" chip. The data ships with releases; the editor never fetches providers' limits or pricing pages (D008
  item 5; doc 40 R1). At run time it learns only from the configured provider's own counters and response headers.

**Choosing a route.** For each call, the router walks the step kind's route list. It skips:

- an entry that is not qualified for this step kind, unless the user accepted it as custom and unqualified (D045 item 4; D048
  item 5);
- an entry that fails the privacy or content filters (D046; D047);
- a pool whose allowance is spent, or reserved for interactive work when the call is background;
- an endpoint whose per-minute token cap is smaller than the call;
- a cooling or demoted host.

Among the rest it takes the entry that can start soonest, with a small penalty per rank so that the user's order still wins when
starts are close (the simulator uses 1 s). Pacing is proactive: the router spaces calls within each known window instead of provoking
429s, because a refused attempt still fills a per-minute window (§3.1).

**Congestion: a circuit breaker per host.** "Host" means one serving endpoint (provider, model and precision), not the provider as a
whole: in §2.4 one provider served two models cleanly while a third endpoint of its own refused a third of its attempts.

- **Cooling.** An upstream 429 cools the host for 15 s. The cooldown doubles with each consecutive strike, to at most 10 minutes
  (the simulator's values [I]). The call reroutes at once.
- **Probing.** After the cooldown, one call probes the host, and only a success clears it.
- **Demoted.** A host whose recent success rate falls below a threshold (for example under 50% over its last 10 attempts [U]) is
  demoted to the bottom of every list for the session or for an hour. This is the fix for §3.6 item 5.
- **What it does not trust.** `retry_after` on an upstream 429 is a floor, never a promise (§2.3). Catalogue uptime is not used for
  routing. The account's own per-minute 429s (`AccountRateLimited`) follow `Retry-After` exactly.

**Interactive budget.** A call the user waits on gets at most 2 retries on one endpoint, or 10 s in all, before the stall card (UX2)
and the next route. At 60 s it takes the ceiling (UX3). A transport retry is never a repair turn and is journaled apart (doc 38 §4.6;
DG016).

**Fallback order per step kind** [I]:

| Step kind | 1 Local | 2 Route list (cloud) | 3 Paid backstop (opt-in) | 4 No-model path | Background at a spent quota |
| --- | --- | --- | --- | --- | --- |
| PICK | Session model if qualified, or the tiny cascade stage (if adopted) | Strict-schema endpoints first | Yes, under the cap | Code's best-scored default, shown as a chip (doc 25 §10.1) | Park; resume after the reset |
| FILL | As PICK, per field (doc 53 §4.4) | Strict-schema endpoints first | Yes | Code defaults; a question card | Park |
| Creative text | Local writer only if qualified (≥ 12B or MoE offload, L4) | Largest qualified writers first | Yes | Template text with seeded archetypes (doc 25 §10.1) | Park, or the user chooses template text |
| COMPOSE | Rarely (≥ 8B) | Qualified writers | Yes | Split into authored Fill and Pick steps (doc 21 §3.3) | Park |
| EXPLAIN | Session model where qualified (Qwen3.5-4B met the spike bar with a card, 20 of 20; not yet qualified) | Qualified explainers | Yes | The card or diagnostic text verbatim | — |

**Scheduling.** Interactive calls are dispatched before background ones, and a background run may use at most 70% of each daily
allowance by default. When a run's remaining work exceeds its remaining allowances, it enters a resumable **`QuotaLimited`** state:
`BudgetLimited` with a quota reason, the pool and its reset time (doc 38 §3.4). It resumes after the reset, automatically only if the
user ticked that on the plan card (it continues a plan already approved). Bulk text goes into a background queue that can wait for
the reset.

**What the router never does.** It never creates, rotates or pools accounts or keys; never sends a call to an endpoint outside the
user's route lists; never raises a cap; never uses OpenRouter's cross-host fallbacks, since routes stay pinned (D046); and never
changes a role binding silently.

### 5.3 Call-reduction measures in the harness

Ranked by what the simulation says they buy. Each keeps the typed, validated, one-decision harness (D009).

| Measure | What it cuts | Evidence | Status |
| --- | --- | --- | --- |
| **Cloud K per tier**: K = 1 on metered and free cloud setups, validators and repairs kept; Standard K only where the user sees the alternatives, or on local models | Pick calls 2–3 times; creative calls 2 times | Load-bearing in §3.5; K = 3 bought 1.6 points for three times the calls (doc 53 §3) [V per doc 53] | Proposal; extends DG021 and doc 40 R7; needs quality evidence on cloud |
| **Local first for Pick and Fill** (doc 40 R14), or the **tiny cascade** (doc 53 §4.3) | Session cloud calls 60 to 10.5 (F) or 16.7 (cascade) | §3.3: S2 and S4 | R14 in D026; the cascade needs the owner (doc 53 OQ2) and R6 evidence |
| **Lean capsules for token-capped providers**: a compact per-model profile, cache-stable prefixes (doc 40 R2–R5) | Tokens per call by 3–10 times; on Groq gpt-oss cached tokens do not count at all | §1.4: a campaign day on one Groq model 9% → 94% | Proposal; relates to DG019 and DG025 and to D048 presets |
| **Deferral of bulk text** to the background queue, across a reset if needed | Peak demand, not totals | The campaign burst is 352 calls at once (§1.2) | Proposal; doc 40 R12's Economy mode is the same idea for paid batch |
| **Exact memo reuse** (doc 40 R13) and **gesture-started steps** that skip IntentFill (doc 53 DP-01) | 25% of explanations, 50% of intent Fills [U] | Not load-bearing in §3.5 | R13 in D026; the skip is ours |
| **Packing** independent bulk text slots into one request | Text calls up to 4 times; tokens about 2–3 times | Not load-bearing in §3.5 | Departs from "one small decision per call"; low priority; owner decision |
| **Warm-first fan-out** (doc 40 R9) | Cache misses in a burst | — | DG027 |

**Effort presets on free tiers** (D024): the plan card should offer Quick (K 1/1, R 1) or a "free-tier Standard" (K = 1 on the cloud,
R ≤ 2) with the numbers. Effort stays a budget and never changes the checks (D024 item 1).

### 5.4 UX surfaces (glass box)

**Plan card: calls against today's allowances** (doc 38 §5.2; doc 40 §6; illustrative wording):

```text
Campaign from brief · 8 missions · Standard (cloud samples: 1)                 limits as of 2026-09-28 · resets 00:00 UTC (in 9 h 55 min)
  About 150 cloud calls and 165 on this PC (tiny model)
    Groq, your key          gpt-oss-120b: 972 requests, 152K tokens left    enough
    Cloudflare, your token  4,890 of 10,000 neurons left                    text needs about 2,600
    OpenRouter, your account 43 of 50 free requests left                    host busy now, cooling down
  Fits today. About 12 min of model work; background after the outline.
  If every route is busy: [keep defaults and continue] [pause until the reset] [allow up to $0.05 on your paid route]
  [ ] Resume automatically after the reset
  [Run] [Edit] [Cancel]
```

**Quota meter** in the status bar and run panel. It shows each connected account's allowance left, the reset time, and each host's
health (clear, cooling, demoted), with drill-in:

```text
Wilco · Groq 2% used · Cloudflare 51% · OpenRouter 7/50 (host busy, next try in 4 min) · local tiny: idle · resets in 9 h 55 min
```

**Stall card** after 10 s of waiting on an interactive step (UX2). It is non-modal. Under Auto autonomy the route list decides
without a card; under Confirm and Propose the card offers the choices and never times out into a yes (D024; doc 38 §4.1):

```text
Waiting for a model (12 s): OpenRouter's free host is busy (3 refusals in 20 s).
  [Use the default now]  [Try Groq gpt-oss-20b (next in your route list)]  [Keep waiting]
```

**Background queue.** Runs waiting for a reset or a busy host are listed with pause, resume, cancel and "run now on another route".
A parked run holds no model call and survives a restart (doc 38 §4.1).

**Transparent fallbacks.** The run panel counts reroutes, fallbacks and defaults kept. Each decision's inspector names:

- the setup, preset and host that answered (D046; D048);
- why the router chose it, for example "OpenRouter host congested (3 × 429 in 20 s); answered by Groq gpt-oss-20b, entry 2 of your
  route list";
- the attempts refused, with their outcome types.

The run report lists what ran on which route and what remains default.

**Disclosure card** (D045 item 3): the free-tier line becomes computed, not fixed. It gives today's allowance and what it buys in
sessions and campaigns on this setup, and says that free hosts "may be busy for long spells", citing the observed rate.

## 6. Implications (proposals) and design-gap candidates

### 6.1 For the decision records and doc 50

- **D021 (provider layer).**
  - The seam gains the quota ledger, the `LimitOutcome` taxonomy (vendor codes as profile data, doc 51 Z15), host health and route
    lists as data.
  - Limits become dated data next to prices.
  - The capability probe also records which rate-limit headers and counters an endpoint returns.
  - None of this puts a provider library into the domain crates (D021 item 1).
- **D022 (local inference and the Model Manager).**
  - The Model Manager is the rate-limit escape and should say so: "no limits, no account" beside each recommended model.
  - What it recommends depends on the machine: a GPU session model for Pick, Fill and, where qualified, EXPLAIN; on a CPU-only
    machine, a tiny model once doc 53's R1 and R3 pass; and the tiny CPU stage while the game holds the GPU during Preview.
  - It shows the expected model time per session (§2.5).
- **D024 (effort, autonomy, role binding).**
  - **Role binding** would bind a role to an ordered route list instead of one setup (item 4). That is an owner decision; see RG1.
  - **Autonomy** governs the stall card as it governs other waits.
  - **Effort presets** on free tiers are shown with their call counts; Quick or "free-tier Standard" is the suggested choice.
- **D026 (token economy).**
  - For a free user, **quota is the budget**. Caps and meters count requests, tokens and neurons with a reset time, not only
    dollars.
  - `BudgetLimited` gains a quota reason (`QuotaLimited`), and the plan card forecasts calls against allowances (UX7).
  - Item 3 ("no silent model switching") holds if route lists are visible and each switch is recorded.
  - The paid backstop is a capped, opt-in use of the user's own credits.
- **D045 and doc 50 (OWQ-24, answered (b) on 2026-09-28).**
  1. The **"connect a free model" flow should lead to a second provider**. OpenRouter's one-click preset alone is a taster that
     misses the UX standard even for a light session under the congestion observed. The recommended free setup is OpenRouter,
     Groq, Cloudflare and a local model (§4).
  2. The **written answers from Groq and Cloudflare are load-bearing** for the release preset list (D045 item 7), not optional.
  3. D045's **"about 13 days" capacity line** should be computed per setup from the ledger. It is one data point: Standard effort,
     OpenRouter at 50 a day, no congestion.
  4. D045 item 6's **clean fallback** is the route list's job; the stall card and the inspector are its visible form.
  5. **Only qualified entries** may appear in a preset route list (D045 item 4). No cloud setup is qualified yet, so the free
     cloud path stays "custom, unqualified" until qualification runs.
  6. **D046's zero-retention default** removes Gemma 4 `:free`. The simulation runs without it; with Groq connected that costs
     nothing, and without Groq it costs a campaign day on one seed in three (§3.7).
- **D023 decision 3 and doc 38 §4.6** ("transport retries … never switch models") conflict with S3 to S6 as simulated. Either
  route lists are an explicit, user-authored binding, so a switch within the list is the user's standing choice, or each switch needs
  a click, in which case a busy host produces a stall card every time. This is the main owner question (RG1).
- **D044 and D048.** The same qualification machinery serves both. A route list entry is a (preset, step kind) pair with its own
  badge. Qualifying Groq's and Cloudflare's candidate models for step kinds becomes a release prerequisite if the owner adopts §4.

### 6.2 Design-gap candidates (listed, not filed)

| Id | Candidate | Touches |
| --- | --- | --- |
| RG1 | **Route lists**: a user-authored, ordered list of setups per role and step kind, which the router may move along on a limit outcome without a click per switch, each switch recorded | D023 decision 3; D024 item 4; D026 item 3; doc 38 §4.6; doc 53 OQ2; D045 item 6 |
| RG2 | **Limit outcomes and retry accounting**: the `LimitOutcome` taxonomy; 429s are neither turns nor money; `Retry-After` is a floor on upstream 429s; the interactive retry budget | DG016; doc 51 Z15–Z16; doc 38 §4.6 |
| RG3 | **Quota ledger and `QuotaLimited`**: pools per account, persisted counts, the interactive reserve, resume after the reset (opt-in automatic resume) | doc 38 §3.4, §4.1; D026 |
| RG4 | **Adopt a UX standard for rate-limited operation** (§4) and its instruments (simulator, replay tests, ledger metrics) | D026; doc 53 §1.1; doc 40 §7 |
| RG5 | **Cloud K per tier**: K = 1 by default on metered and free cloud setups | DG021; doc 40 R7; doc 25 §5.2 |
| RG6 | **Lean capsule profile** for token-capped providers | DG019; DG025; D048 |
| RG7 | **Packing** independent text slots into one request (low priority) | D009; doc 25 §4.3; doc 38 §3.3 |
| RG8 | **Paid backstop** in the free flow: opt-in, hard daily cap, two hosts, shown on the plan card | D026; D045; D046 |
| RG9 | **Dated free-limit data**: who curates it and how it is refreshed, together with the preset data; refreshed through releases, never by the editor fetching providers' pages | doc 50 §6's candidate; D045 open parts; D008 item 5 |

### 6.3 Findings that affect sibling files (reported, not fixed)

1. D045's Consequences and doc 50 §4 step 8 give "about 13 days" per campaign at 50 a day as the capacity statement. That holds at
   Standard with no congestion. Under the congestion observed, even a session may not complete on that route (§3.3).
2. Doc 53's TL;DR and §4.10 say "about 12 cloud calls" remain in a session with Pick and Fill local. The cost model gives 10.5 (plus
   6.2 more with the cascade's escalations: 16.7). The difference comes from rounding intent and enum Fills.
3. Doc 50 OQ12 ("Do failed requests count against OpenRouter's free daily limit?") is partly answered: upstream 429s did not count
   in one 12-refusal sample (§2.3). Platform 429s remain [U].
4. `tools/quota-sim/README.md` called this doc "planned"; the 2026-09-28 review fixed the README and the tool's module docs.

## Open questions

1. **UX standard (owner).** Adopt §4's criteria and thresholds, change them, or keep rate-limited operation best-effort?
2. **Route lists (owner, RG1).** May a user-authored route list move a call to another endpoint or model on a limit outcome
   without a click per switch, provided each switch is shown and recorded? Or does D023 decision 3 require a click every time?
3. **Release free setup (owner).** Is asking users to connect two or three free providers acceptable as "free"? Should the flow
   recommend OpenRouter, Groq, Cloudflare and a local model together, and call OpenRouter alone a taster?
4. **Paid backstop (owner, RG8).** Should the free flow offer an opt-in "never stall" backstop on the user's own credits, with a hard
   daily cap (the simulation spent under $0.06 a day)?
5. **Outreach (owner).** The written answers from Groq (exception route) and Cloudflare (violence clause) on fictional military
   content now gate the free campaign path (D045 item 7).
6. **Congestion by time of day (measure).** Run a slow drip over 24 hours on several days, within the free quota and on synthetic
   suites only, against the `:free` hosts and Groq, to replace the "observed" and "stress" placeholders. Does OpenRouter's own platform
   429 count against the daily quota [U]?
7. **Groq mechanics (measure).** Do reasoning tokens count toward tokens per minute? How do the daily windows reset? How often does
   the free plan refuse under load? For Cloudflare: its error code at the allowance, its latency, and whether 300 a minute is per
   account [U].
8. **The tiny CPU stage (measure; doc 53 R1, R3, R6).** Does a 0.4–1B model hold PICK, and how fast is it with a cached prefix and a
   compact capsule? The simulation assumed 1.5 s per Pick, and at 6–15 s the stalls return (§3.5).
9. **K = 1 on cloud (measure).** What does one sample cost in quality on cloud Picks and creative text, compared with Standard?
   The 1.6-point figure is from local records.
10. **Automatic resume after the reset (design).** Opt-in per run, a global setting, or never automatic?
11. **Hugging Face's $0.10 a month (design).** Is it worth a preset? S3 used it on campaign and heavy days (32–69 calls a day under
    observed congestion, a month's credits in one day); with the local cascade (S4) it served at most 10 calls a day.

## Sources

**Repository.** Docs 21 (§3.3, §6.2, §7), 25 (§4.1, §5.2, §10.1–§10.2), 38 (§3.4, §4.1, §4.5–§4.6, §5.2–§5.3, §8), 40 (§1.1, §4.2
R2–R17, §5.1, §6, §7), 44, 46, 48 (§1.1, §6.0), 50 (§1.3, §2.1–§2.5, §4, §6, OQ12), 51 (Z15, Z16), 53 (§1.1–§1.3, §2.6, §3,
§4.1–§4.10, §5.5), 55; D004, D008, D009, D010, D021, D022, D023, D024, D026, D044, D045, D046, D047, D048; DG016, DG019, DG021,
DG025, DG027, DG039; `docs/research/data/free-llm-services.csv`, `docs/research/data/cost-model.csv`; `tools/cost-model/cost_model.py`;
`tools/quota-sim/` (README, `data/workload.json`, `data/limits.json`, 31 tests).

**Provider pages** (read 2026-09-27, limits re-read at about 21:50 UTC; terms re-read 2026-09-28 per doc 50):
OpenRouter: <https://openrouter.ai/docs/api/reference/limits> · <https://openrouter.ai/docs/api/api-reference/api-keys/get-current-key> ·
<https://openrouter.ai/docs/guides/routing/provider-selection> · <https://openrouter.ai/api/v1/models> (keyless catalogue and per-model
`/endpoints`). Groq: <https://console.groq.com/docs/rate-limits> · <https://console.groq.com/docs/prompt-caching> ·
<https://console.groq.com/docs/structured-outputs>. Cloudflare: <https://developers.cloudflare.com/workers-ai/platform/pricing/>
(updated 2026-09-17) · <https://developers.cloudflare.com/workers-ai/platform/limits/> ·
<https://developers.cloudflare.com/workers-ai/features/json-mode/>. Hugging Face: <https://huggingface.co/docs/inference-providers/pricing>.
Ollama: <https://ollama.com/pricing> · <https://docs.ollama.com/cloud>. OVHcloud:
<https://docs.ovhcloud.com/en/guides/public-cloud/ai-machine-learning/ai-endpoints-getting-started>. Doc 50's source list covers the
terms pages.

**Plotroom's own run records** [V-obs] (not in the repository; aggregates only): the round-0 free probe of 2026-09-27, 20:13–20:35
UTC (its call records, budget ledger and drip log), and the D044 screening run of 2026-09-27, 22:18–23:30 UTC (per-call HTTP status
history, latency and served provider). The OpenRouter catalogue read of 20:30 and about 21:55 UTC.

## Verification notes

### 2026-09-28, author checks at write-up

- **Cost-model rows.** The workload figures (§1) come from a research profile that imports `tools/cost-model/cost_model.py`
  read-only. Its 35 cross-check rows reproduce the cost model's `calls` and `local_calls` on gpt-6-luna exactly.
- **Simulator tests.** `tools/quota-sim`'s 26 unit tests were re-run for this doc with bytecode writing off: all pass, in about 8 s.
- **Replay.** One scenario was replayed and matched the stored grid: the campaign day, S4, "observed", seed 1. Its campaign block took
  737.7 s (stored 738 s), with interactive p90 1.8 s and 11.5 s at most.
- **Tables.** The §3.3 and §3.4 tables were copied from the grid's Markdown output and spot-checked against its per-run JSON (block
  durations; served-by counts per endpoint).
- **Sensitivity runs (§3.5)** used the tool's own `run_one` with run-time overrides of `PACK`, `REUSE_EXPLAIN`, `SKIP_INTENT`,
  `cloud_k`, provider exclusions and the tiny stage's latency. The scripts and their outputs stay outside the repository; no tracked
  file changed.
- **Run records.** The observed-endpoint figures (§2.3) were recounted from the round-0 call records and budget ledger: 9 calls, 13
  attempts, 1 × 200 and 12 × 429, and the `free_model_daily_requests` readings. The brief this doc was written from said "9+ 429s over
  about 25 minutes"; the records show 12 over 17.6 minutes. The paid-endpoint figures (§2.4) were counted from the screening records'
  HTTP status histories; quality results were not read into this doc.
- **Records and rules.** D021–D026, D044–D048, OWNER-QUESTIONS OWQ-24–OWQ-27 and DG016 were re-read on 2026-09-28. OWQ-24 is
  answered, (b) → D045, so §6 treats it as a decided flow with open parts.
- **Hygiene.** No local path, user name, key, call or generation id or private project appears in this file. No account was created
  and no keyed API was called.

### 2026-09-28, review of doc 52 and `tools/quota-sim`

- **Tests.** At the start of the review 30 tests passed; four had come with data fixes made after the write-up, so "26" was stale in
  this doc, the README and `docs/README.md`. One regression test was added (below); 31 pass, run with bytecode writing off.
- **Grid re-run** (336 runs, about 23 s) and compared cell by cell with §3.3 and §3.4. Most cells matched. These had drifted: S3 and S4
  on the mission build and S4-noGroq on the campaign and heavy days (observed); S3, S4, S4-noGroq and S6 under stress; and some
  §3.3 prose (OpenRouter requests left 36–50, not 44–50; under moderate congestion S3 misses the heavy day). **Cause**, isolated
  with run-time overrides: the tables predate two data fixes. One is the K = 1 cached share (a session's 0.577, not 0.673), which
  shrinks Groq's token headroom and enlarges packed text calls. The other removed Gemma 4 `:free` from the route lists. Undoing
  either restores the old cells (for example S4-noGroq's campaign day: 2/3, 92.8%, 28 cut). The TL;DR, §3.2–§3.7, §4's table, §6.1
  and the open questions now quote the current tool. §3.7's "removing it changes nothing" was wrong and was corrected.
- **Router fix, test first.** The paid backstop was charged the per-rank penalty on top of its 10-s threshold, so the real threshold
  was 10 s plus the length of the step kind's route list (14–17 s for a call the user waits on), not the rule stated in §3.1 and the
  README. `choose()` now compares the paid endpoint with the earliest free start. The new test failed before the fix and passes after
  it. Only S6 under "stress" changed: its longest interactive wait fell from 17.5–31.7 s to 3–13.7 s, and it used 0–25 paid calls
  and at most $0.0086 a day.
- **New sensitivity**: the tiny stage's escalation rate at 23%, 40% and 60% (§3.5), because the 23% was measured on 3–4B models.
  Also added: without Cloudflare and without packing (packing is not the cause of that failure).
- **Workload and capacity arithmetic.** From `data/workload.json` and the tool's own functions: decisions and calls per workflow and
  per day at B and F (§1.2–§1.4) and the whole §2.2 capacity table reproduce. §1.4's Groq and Cloudflare share columns were not
  recomputed.
- **Limits at the source**, re-read 2026-09-28: OpenRouter's limits page, Groq's rate-limits page, and Cloudflare's Workers AI pricing
  (updated 2026-09-17) and limits pages. Every figure in §2.1 and `data/limits.json` holds and agrees with
  `data/free-llm-services.csv`, including the four Cloudflare neuron rates. Whether Cloudflare's 300 a minute is per account is
  still [U].
- **Run records.** §2.3 was recounted from the round-0 call records, budget ledger and drip log, and every figure holds; the
  daily-counter row now says that 3 refusals came before the answer. §2.4 was recounted from the screening records. They now hold
  eleven paid endpoints up to 23:30 UTC, so the table gained six rows, including a second throttled host. DeepInfra's Gemma has 256
  calls (253 came from a partial read). SiliconFlow's p50 is 1.49 s at nearest rank, and prompts are 270–490 tokens (p10–p90).
- **Legal constraints.** The router and the UX keep one account per provider, no Plotroom key or proxy, pinned routes (D046) and
  per-step-kind qualification (D045 item 4). They also keep D045 item 1's Apache-2.0-only rule on Cloudflare: Gemma 4 and Granite are
  Apache-2.0 (doc 14). D008 item 5 (the editor never fetches providers' pages) was added to the ledger bullet and RG9.
- **Code comments.** Docstrings were added to the event-loop methods, the host helpers and the report helpers. The latency jitter is
  now a named, documented constant. The held-slot and queued-timeout assumptions are stated in code, README and §3.1. Test docstrings
  gained their "Why" paragraphs. The README and the module docs no longer call this doc "planned".
- **Hygiene.** Doc 52 and `tools/quota-sim/` were searched for local paths, user names, key prefixes, call or run ids and private
  project names; none found. No model was run and no keyed API was called; the public source pages were read without a key.
