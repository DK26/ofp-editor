# Cloud providers, cheap models and harness uplift

Research doc 48 for Plotroom (`ofp-editor`). Research date: 2026-09-27. Audience: contributors and LLM coding agents; it is meant to be
read alone.
Question answered (owner, paraphrased): once everything has been tested locally, which cheap and reliable providers, open-weight or not,
should we test? Do some models perform better on cloud hardware? And which cheap models strike the best balance between their cost and
how much our harness improves them?

**Status.** Research and a test plan. **Nothing has been run in the cloud**: no account was created, no keyed or paid API was called and
no money was spent. Quality statements are public evidence or hypotheses. Every dollar figure is price-sheet arithmetic **[I]**.
**Deferred (owner decision, 2026-09-27).** Round 1 (§6.1–§6.6) waits until the local results of doc 49 (the measured local shortlist)
are in. Nothing in §6.1–§6.6 runs before then, and prices, promotions and uptimes must be re-read before any run, because they move
weekly (§2.4). The plan gained an optional Bonsai 2 27B pair on 2026-09-27 (§6.6, runs O7 and O8), answering the owner's question of
doc 47 §2.7.
**Round 0 (§6.0, owner request, 2026-09-27)** tests OpenRouter's free models first: zero spend, synthetic suites only, a dedicated
account and a DPAPI-stored key. It needs only the tool patch; when it starts is the owner's call.
**Epistemic legend.** **[V]** verified on 2026-09-27 against the cited primary source (a provider's pricing, model, policy or docs page;
OpenRouter's or Hugging Face's public keyless APIs; a paper). **[V per doc N]** taken from a sibling doc. **[I]** our inference, proposal
or arithmetic. **[U]** unknown.
**Prices** are USD per million tokens (MTok), read on 2026-09-27 from the *pinned endpoint's* row, not the model's list price. They move
weekly, and several are promotions, marked **promo** with the list price. The editor reads prices from dated data (doc 40 R1), never from
this doc.
**Data.** [`data/cloud-candidates.csv`](data/cloud-candidates.csv): 73 rows, 2 of them added for §6.6 and 6 free-endpoint rows for §6.0
(`model, provider, kind, price_in_per_m, price_out_per_m, cached_in_per_m, batch, free_tier, precision, structured_output, context,
privacy, read_on, battery_cost_usd, role, sources`).
`battery_cost_usd` is the estimated cost of battery B (§1.2) at that row's price, with the tokenizer factor 1.3 and reasoning at the
row's lowest planned setting (§6.2); it is blank for aggregators and GPU rental.
**Tooling.** A cloud backend for `tools/local-qual` (any OpenAI-compatible endpoint, a hard budget cap, the harness-uplift variants of §5
and an `uplift.py` comparer, plus the `--free-only` mode, DPAPI key scripts and free-tier rate caps of §6.0) has been built and tested
against a local mock server only. It lands as one patch, with its `CODE-INDEX.md` entry, once doc 49's local measurement run has finished
with `tools/local-qual` [V for the mock tests; I for readiness].
**Relation to sibling docs.** Doc 14 (tiers, candidates), doc 21 and doc 25 (step shapes, evaluation), doc 40 (token economy, cost model,
instrument E12), doc 44 (first local measurement), doc 46 (llama.cpp, UD quants, `pick-hard`), doc 47 (small models, MoE offload
candidates); D021 (provider layer), D022 (Model Manager), D023 (model strategy), D026 (token economy). This doc changes no decision.
**Step-kind names** follow doc 47: PICK, FILL, COMPOSE, DRAFT (creative text and its translation) and EXPLAIN. DRAFT here is *not* the
ChangeSet shape of docs 21, 25 and 38 (doc 47 open question 1).
**Hygiene.** Public sources only. The planned runs send only the repository's synthetic suites: no user data, no mission files, no game
content.

## TL;DR

- **One account is enough to start: OpenRouter** (owner-created, never by an agent). One key reaches every core run below except one. Per
  request it can pin a single endpoint (`provider.only`, `allow_fallbacks: false`, `require_parameters: true`, `quantizations`), demand
  zero data retention (`zdr: true`) and exclude data-collecting hosts (`data_collection: "deny"`). It returns `usage.cost` on every
  response and supports a credit limit per key. It adds no markup on tokens; buying credits by card costs 5.5% (minimum $0.80) [V]. A free
  Hugging Face account is optional: its $0.10/month of routed credits covers Qwen3-4B-Instruct-2507 at nscale ($0.01/$0.03), which
  OpenRouter does not host [V]. Free tiers (Cerebras, Groq, Gemini, OpenRouter `:free`) are rate-limited or train on the data, so they
  suit smoke tests and round 0's zero-spend screening (§6.0) only.
- **Cheap, reliable, strict-schema and privacy-acceptable hosts** [V]: DeepInfra, CoreWeave, AkashML and Parasail (DeepInfra,
  CoreWeave and Parasail are US-headquartered; OpenRouter lists no headquarters for AkashML; all four are on OpenRouter's ZDR list, with
  1-day uptime 98.9–100% on the endpoints we plan to use); Mistral first-party (EU vendor, pinned to
  `mistral/zdr` or `mistral/eu`); Azure for GPT-6 and Google Vertex for Gemini and Claude (the ZDR routes on OpenRouter); Scaleway in
  Paris (ZDR by default). **Not defaults:** DeepSeek's own API (PRC storage, training unless the user opts out by email, no
  `json_schema`), the cheapest new networks (Darkbloom is not ZDR, and OpenRouter's price-weighted default routing sends unpinned traffic
  there), and every free or data-for-discount tier.
- **Cheap models to test with the harness** (USD/MTok in / out): gpt-6-luna 0.10/0.50; DeepSeek V4.1 Flash on DeepInfra 0.14/0.42
  (promo; list 0.20/0.60); gpt-oss-120b 0.037/0.17; Qwen3.5-9B 0.10/0.15; Gemma 4 26B-A4B 0.10/0.30 and 31B 0.14/0.40; Mistral Small 4
  0.15/0.60; Gemini 3.1 Flash-Lite 0.25/1.50. GLM-5.3-Flash (0.075/0.25 promo) has the highest AA index of the cheap models and leads
  EuroEval in Czech and Polish, but its thinking cannot be switched off and is verbose, so it is a COMPOSE and translation candidate.
  Writer candidates: GLM-5.3 on Morph (0.36/1.14 promo) and Qwen3.8-27B. **Dominated:** Claude Haiku 4.5 (retiring no sooner than
  2026-10-15, AA index 17 at $1/$5) and Gemini 3.5 Flash-Lite (costs more than 3.1 Flash-Lite).
- **"Better in the cloud" is two questions** [I]. (1) *The same weights at higher precision*: Ministral 3 3B (the only doc 44 model with
  a hosted copy), Qwen3-4B-Instruct-2507, gpt-oss-20b, and doc 47's MoE-offload candidates Gemma 4 26B-A4B and Qwen3.6-35B-A3B, at fp8 or
  bf16 against the local Q4. (2) *Bigger cheap models* that no 8 GB card can run. The evidence predicts little quantisation effect on
  PICK and large effects from serving defects, so a gap is not attributed to precision until two hosts agree (§4). Doc 44's own winners
  (Gemma 4 E4B QAT, Qwen3.5-4B, Granite 4.1 3B) have no cheap serverless copy; the exact files can run on a rented GPU [V].
- **The metric is cost per correct decision (CPCD), not price per token** [I]. A harness PICK call is 220–540 input tokens and 7 output
  tokens, so a full battery costs cents on any cheap model. What moves the bill is the admit rate, repairs, K samples and hidden reasoning.
  A 3-sample vote with cards on gpt-6-luna costs about $0.0002 per decision, against about $0.0055 for one bare open question to Sonnet 5
  at its default effort, about 30x more; accuracy decides whether the harness makes the cheap model a substitute.
- **The uplift instrument** (§5) removes one harness mechanism at a time: no menu, labels only, no schema, no cards, no repair, no
  constraints. It reports the gap closure *H* = (cheap_full − cheap_bare) / (frontier_bare − cheap_bare) and a non-inferiority test
  of the cheap model with the harness against a frontier model without it, split into engine vocabulary (which a bare model may know) and
  Plotroom's own catalogue ids (which it cannot), so the comparison is not rigged in the harness's favour.
- **Round 1 budget** [I]: 23 core runs and 17,648 calls, estimated at **$5.10** for the runs, $0.05 for preflights and $1.48 for a
  15% API double-grading sample, **$6.63 in all**. Hard caps per stage sum to $10.25; buy $15 of credits once (card fee $0.83) and set
  the key's own limit to $12. The two frontier comparators are 77% of the run cost; all 21 cheap arms together are about $1.15. Opus 5.5
  is optional (about $7.90 on its own).
- **Round 0 comes first and costs $0** (§6.0, owner request) [I]: OpenRouter `:free` models only, on a dedicated account with a
  DPAPI-stored key whose credit limit is $0, a free-only guard that stops on any charge, and client-side caps under the free limits
  (20 a minute; 50 a day account-wide). The core is 204 requests over 6 days: plumbing, the §5 ladder on Qwen3.8-27B (the only free
  general model on the ZDR list) and a same-weights Gemma 4 26B-A4B pair with the local build. It screens at k = 1 and qualifies nothing.
- **Product implications** [I]: D021's seam needs an aggregator adapter that pins (model, endpoint, precision, reasoning setting), sends
  ZDR and no-data-collection flags by default for user content, records and shows the serving host, and probes strict schemas per
  endpoint, because capability flags disagree with vendor docs in at least six cases. D023's cloud recommendations should name endpoints,
  not only models. Doc 40's cost model needs 3.1 Flash-Lite and hosted open-weight rows, a caching correction for 3.5 Flash-Lite, and
  promotion flags on prices.

## 1. What we buy from a provider

### 1.1 Per step kind [I]

| Step kind | The call | What the provider must deliver | What matters less | Latency budget |
| --- | --- | --- | --- | --- |
| PICK | One letter from a code-computed menu of up to 7 options plus escapes | Server-enforced enum schema; a reasoning-off switch that is honoured; stable serving | Output price, context size | Interactive: local p50 was 0.31–0.75 s (doc 44) |
| FILL | A small typed record (enums, quoted spans) | Strict `json_schema` with enums; no silent fallback to unconstrained output | Output price | About 1–2 s |
| COMPOSE | Several related fields or one radio exchange | Schema plus moderate reasoning; judgement | First-token time | Seconds |
| DRAFT | Briefings, dialogue, story beats; translation into the 8 engine languages | Writing quality, multilingual quality, output price; code still enforces length and codepage | Schema strictness (a thin JSON wrapper) | Batch is fine (doc 40 R12 Economy) |
| EXPLAIN | Two grounded sentences from a reference card | Faithfulness (low hallucination) with reasoning off | Output price | Interactive |

Latency favours local models for PICK. Hugging Face's router measured first-token times of 0.16–2.5 s for hosted models, typically
0.25–1.3 s before network overhead. For the §3 candidates, Artificial Analysis measures 0.73 s (gpt-6-luna, no reasoning) to 3.14 s
(GLM-5.3-Flash) to the first chunk [V]. Decode speed runs from about 20 to 1,000 tokens/s (Cerebras gpt-oss-120b about 1,007; Groq
gpt-oss-20b 776; Scaleway Gemma 4 26B 151; DeepInfra Gemma 4 26B 40), against 37–61 tokens/s locally [V; V per doc 44]. So the cloud
pays off for FILL whole records, COMPOSE, DRAFT and translation; a local 4B remains the best PICK path when it qualifies [I].

### 1.2 The token profile of our battery [V from the doc 44 and 46 records; I for new arms]

Per-call means with the local tokenizers (the chat template included). On the same model Ollama's `prompt_eval_count` equals
llama-server's `usage.prompt_tokens` exactly, so the two runtimes are comparable [V].

| Suite and arm | Calls per model (k) | Input tokens mean / p90 / max | Visible output mean / p90 / max | Local output cap |
| --- | --- | --- | --- | --- |
| pick, no card | 90 (3) | 220 / 248 / 286 | 7.1 / 7 / 10 | 64 |
| pick, cards | 90 (3) | 312 / 347 / 372 | 7.2 / 7 / 11 | 64 |
| pick-hard, no card (Qwen, llama.cpp; preliminary) | 90 (3) | 302 / 333 / 379 | 7 / 7 / 7 | 64 |
| pick-hard, cards | 90 (3) | 441 / 509 / 535 | 7 / 7 / 7 | 64 |
| fill | 36 (3) | 431 / 472 / 475 | 50 / 85 / 100 | 320 |
| explain, cards | 20 (2) | 305 / 336 / 353 | 84 / 107 / 136 | 320 |
| text, no card | 20 (2) | 162 / 183 / 192 | 19 / 28 / 39 | 120 |
| knowledge, no card | 24 (2) | 87 / 111 / 118 | 111 / 241 / 700 | 700 |
| knowledge, cards | 24 (2) | 222 / 259 / 276 | 82 / 156 / 348 | 700 |

Prompt parts, from a chars-to-tokens fit on 360 Qwen Pick records (tokens = 26.8 + 0.2311 × characters): the Fill schema text is about
137 tokens and its field glossary about 189; a Pick card 82 (135 on `pick-hard`); the lettered menu 91 (139), of which the one-line
descriptions are 66 (100) [V]. The new arms of §5 are estimated from the same fit [I]: an open question with no menu is about 129 input
tokens (159 on `pick-hard`), a labels-only menu 153 (195), and an open answer about 20 output tokens.

**Batteries** used in §6 [I]:

| Battery | What it is | Calls | Input tokens (local) | Visible output (local) |
| --- | --- | --- | --- | --- |
| B | Doc 44's 304-call battery plus `pick-hard` none and cards: the local↔cloud comparison | 484 | 147,022 | 11,039 |
| U | B plus the uplift rungs of §5 (open, labels and no-schema Pick on both menu suites; Fill without schema, with schema text only, and with repair; Explain without card; Text with style card and bare) | 1,201 | 308,077 | 28,989 |
| L | Precision ladder: `pick-hard` none and cards plus Fill | 216 | 82,386 | 3,060 |
| F | Frontier comparators: six bare arms at the provider's default effort, the same six at the lowest effort, six full-harness arms at the lowest effort | 849 | 193,997 | 28,764 |
| W | Writer probe: text without and with style card, explain with card | 60 | 12,900 | 2,440 |

### 1.3 Why cost per correct decision, not price per token [I]

**Cost per correct decision (CPCD)** is the billed USD of every call a decision policy used (all K samples, repair calls, failed but billed
calls) divided by the number of correct decisions. **CPAD**, doc 40's cost per *admitted* decision, divides by what the validators
admitted instead. The **false-admit rate** (admitted but wrong, over admitted) is the safety metric beside them.

The battery arithmetic shows why price per token is the wrong axis. With prices P in USD/MTok, a tokenizer factor τ (cloud tokens over
local tokens; planned at 1.3 until the preflight measures it) and θ reasoning tokens per call, billed as output:

```text
USD(B) = τ × (0.1470 × P_in + 0.0110 × P_out) + 0.000484 × θ × P_out
USD(U) = τ × (0.3081 × P_in + 0.0290 × P_out) + 0.001201 × θ × P_out
```

- At τ = 1.3, battery B costs $0.002 on Qwen3-4B-Instruct-2507 at nscale, $0.02–0.04 on the other cheap open models of §3 with
  reasoning off or low, $0.11 on GLM-5.3-Flash (whose thinking cannot be switched off), and $0.53 on Sonnet 5 with thinking off. A tenfold
  price difference between two cheap models moves the battery by cents.
- Hidden reasoning is the real multiplier. At 480 reasoning tokens per call, the Sonnet 5 bare arms at default effort cost $1.60 of
  R20's $2.22 (§6.2). gpt-oss's mandatory 300 reasoning tokens add $0.00004 per call at $0.13/MTok, while the same 300 tokens on Opus 5.5
  cost $0.006 per call.
- **Per decision** [I]: a 3-sample vote on a `pick-hard` menu with cards costs about $0.00019 on gpt-6-luna and $0.00018 on Gemma 4
  26B-A4B at CoreWeave. One bare open question to Sonnet 5 at its default effort (about 207 input, 26 visible and 480 reasoning tokens)
  costs about $0.0055. The cheap harness decision is about 30x cheaper; the open question is whether it is as often right.
- **What the battery cannot price.** Test prompts are 87–535 tokens, below every provider's prompt-cache minimum (1,024 or 4,096 tokens,
  doc 40 §2.3), while the product's capsules are about 2.3K (PICK) and 3.1K (text slot) tokens (doc 40 §5.1). So the battery measures the
  uncached cost of a minimal harness. The product's cost comes from feeding the *measured* quantities (first-pass admit rate, repair rate
  per shape, reasoning tokens per shape and effort, adaptive-K stop rate, τ) into `tools/cost-model/cost_model.py` in place of its [U]
  inputs: this is doc 40's instrument E12 on real endpoints [I].

## 2. Providers

### 2.1 Provider table (read 2026-09-27)

Uptime is OpenRouter's 1-day figure for the endpoints this plan would use: a point-in-time reading of OpenRouter traffic, not an SLA [V].

| Provider (how reached) | Serves, relevant here | 1-day uptime (OpenRouter) | Structured output | Cache / batch | Privacy, region | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| **OpenRouter** (aggregator) | Every core run except R02 | Per endpoint (5-min, 30-min, 1-day, status) | Per endpoint; `require_parameters: true` routes only to endpoints supporting every sent parameter | Passes provider caching through; `:batch` variants with a 24-hour window: 50% for OpenAI, Anthropic, Google and Mistral, 0.8x of DeepInfra's price for DeepInfra-served ones | No prompt logs by default (1% discount for opting in; do not); `zdr`, `data_collection` per request; 920 ZDR endpoints listed; 5.5% card fee (min $0.80), 5% crypto, BYOK 5% beyond a threshold | **The one account** |
| **Hugging Face Inference Providers** (router) | nscale, Featherless, Scaleway, Public AI, DeepInfra, Groq, Cerebras, … | None; `GET /v1/models` lists price, first-token time and throughput per provider without a key | Per-provider flag, not always enforced | Not exposed | Provider rates, "no markup"; $0.10/month free credits, $2 PRO; credits not used with a custom provider key | Optional second account (R02) |
| DeepInfra | gpt-oss, Gemma 4, Qwen3.5/3.6/3.8, DeepSeek V4.x, GLM-5.3 family, Muse-Glimmer, Nemotron 3.5 Lightning | 99.21–99.96% | Yes on most endpoints (not its gpt-oss-120b fp8) | Flex tier 0.8x (may queue up to 10 min or answer 429); cache on some rows | Inputs not stored to disk, outputs not stored, request content not logged (metadata only), no training (except proxied Google or Anthropic models); its bulk APIs may keep encrypted data on disk for "a short retention period"; ZDR list; US | Core host. Watch promotions and 16,384-token output caps on some rows |
| CoreWeave | gpt-oss-20b fp4, Gemma 4 26B bf16, Gemma 4 31B fp4, MiniMax-M3 fp4 | 97.88–100% | Yes (Gemma 26B without tools) | Cache on most rows | ZDR list; US | Core host |
| AkashML | Qwen3.6-35B-A3B fp8, gpt-oss-120b bf16 | 99.93–99.96% | Yes | Cache $0.05 (Qwen3.6) | ZDR list; HQ not stated | Core host |
| Parasail | Qwen3.5/3.6-35B fp8, Gemma 4 26B bf16, Gemma 4 31B fp8 | 98.99–99.95% | Yes | Cache | ZDR list; US | Replicate host |
| Crusoe | Gemma 4 31B bf16, gpt-oss-120b bf16 | 98.86%, 100% | Yes | Cache at the input price | ZDR list | bf16 rung |
| NextBit | Gemma 4 26B bf16 | 98.05% | Yes | Cache | ZDR list; Spain | Cheapest bf16 with schemas; weaker uptime |
| Nebius Token Factory | Qwen3-30B-A3B-Instruct-2507 fp8 | 95.74% | Yes | — | ZDR list. Without ZDR (the default; self-serve switch on the account page), inputs and outputs are stored in Finland for speculative decoding only, for a period the guide does not state; "not used to train any models" | Use with a fallback host |
| Mistral (first-party) | Ministral 3B/8B/14B, Mistral Small 4 | 99.13–99.98% | Flagged on every endpoint; Mistral's docs describe a schema injected into the prompt and state no guarantee | Cache 10% of input (needs `prompt_cache_key`, doc 40); Batch half price | Pin `mistral/zdr`, `mistral/eu` or `mistral/us`: the plain `mistral` endpoint is not ZDR. Direct API: training toggle in Admin (the paid default is not stated); ZDR only on request, approved case by case, pay-as-you-go only and for stateless calls (not batch); EU vendor | Core (EU vendor) |
| Azure (via OpenRouter) | gpt-6-luna, gpt-6-sol | 99.96–99.99% | Strict | Cache | The only ZDR route to GPT-6 on OpenRouter | Core for GPT-6 |
| Google Vertex (via OpenRouter) | Gemini 3.x, Claude, Gemma | 99.93–99.95% (3.1 Flash-Lite, Sonnet 5) | Gemini: JSON Schema subset, "always validate"; Claude: strict | Gemini cache plus storage; Batch and Flex 50% | The ZDR route for Gemini and Claude; `europe` endpoints +10% | Core for Gemini and Sonnet 5 |
| OpenAI, Anthropic, Google AI Studio (direct) | Their own models | 99.9%+ | Strict (Gemini: subset) | Batch 50% | No training on paid API traffic. OpenAI keeps abuse logs up to 30 days (ZDR by approval); Anthropic retains no conversation content by default, except 30 days for its Fable and Mythos models and up to 2 years for content its safety systems flag, and on Vertex or Bedrock the cloud provider, not Anthropic, is the data processor; Google keeps paid-tier logs "for a limited period" for abuse detection. On OpenRouter these first-party endpoints are **not** on the ZDR list | Fine direct; through OpenRouter prefer Azure or Vertex |
| Groq | gpt-oss-20b/120b, qwen3.8-27b | 96.29% (20b), 99.29% (120b) | `strict: true` constrained decoding on those three models; no streaming or tools with it | Batch 50% (Developer plan; not with ZDR) | No retention by default except up to 30 days for troubleshooting or abuse; self-serve ZDR; US | Free plan for smoke runs (30 RPM, 8K TPM) |
| Cerebras | gpt-oss-120b, qwen-3.8-27b | 99.97% | Strict constrained decoding; no `pattern`, `oneOf`, recursion; schema ≤ 5,000 characters | Cache without discount | Does not retain prompts or outputs | Free trial (1M tokens/day at 5 RPM); fastest host |
| Fireworks | DeepSeek V4.1 Flash, GLM, Kimi | 99.88% (V4.1 Flash) | GBNF grammar mode on all its models, the closest match to llama.cpp grammars | Batch 50% | No logging of open-model prompts without opt-in (metadata only); its Responses API stores conversations for 30 days unless `store=false` | Alternative; its direct price differs from its OpenRouter price |
| Together | GLM-5.3 family, MiniMax-M3, Kimi | 99.87–99.94% | Flagged on OpenRouter (the HF router disagrees for GLM-5.3-Flash) | — | Direct API stores prompts and responses by default and "may use them for product improvements" until an org admin enables ZDR; sharing for training other models is opt-in; its OpenRouter endpoints are on the ZDR list | Alternative |
| Scaleway (Paris; direct or HF) | Gemma 4 26B, Qwen3.6-35B, gpt-oss-120b, Mistral Small 3.2 | No OpenRouter history; HF: 127–151 tokens/s | Strict `json_schema` per its docs (HF reports false for Gemma) | Automatic prefix cache, no separate price; Batch −50% | ZDR by default; error or malicious traffic kept up to two weeks; Paris; GDPR | Best EU host; EUR prices; 1M tokens free |
| OVHcloud AI Endpoints (France; direct or HF) | Qwen3.5-9B ($0.12/$0.18 on HF), gpt-oss-20b, gpt-oss-120b, Qwen3.8-27B | No OpenRouter history; HF: 38–82 tokens/s | HF flag true for these models; enforcement [U] | — | "Zero data retention: we keep only the data required for billing purposes"; "never used to train"; French vendor, hosting region not stated on the product page [U] | Second EU host (added in review); not in round 1 |
| Tencent (via OpenRouter) | Hy-MT2 1.8B, 7B, 30B-A3B | 100% | 7B and 30B-A3B yes; 1.8B no | — | ZDR list; HQ CN, datacenter SG | Translation specialist |
| nscale (via HF) | Qwen3-4B-Instruct-2507 | No history; HF first token 650–771 ms | HF flag true; enforcement [U] (docs gated) | — | "does not log or train" (launch blog) | R02 |
| Featherless | Qwen3.5-4B (FP16), larger models at FP8 | HF "live" | Not documented | — | "Prompts stored: Never" | $25–50/month minimum: skip round 1 |
| DeepSeek (first-party) | V4.1 Flash, V4 Pro | 99.98% | `json_object` only; strict tool calls in a beta base URL | Cache 2–3% of input; off-peak half price | Stored in the PRC; used for training unless the user opts out by email (its general privacy policy; no separate API data terms were found); not ZDR | Synthetic suites only, never user content |
| Z.ai (first-party) | GLM-5.3, GLM-5.3-Flash | 99.43–99.96% | `json_object` only | Cache; storage free | Singapore; content not stored; ZDR list | Use a strict-schema host instead |
| Alibaba Model Studio | Qwen3.7/3.8 Flash, Qwen3.8 Max | 98.43–99.94% | `json_schema` "not supported yet" in the Singapore region | 1M free tokens for 90 days (Singapore) | "will never use your data for model training"; not ZDR | Not selected |
| New low-price networks (Darkbloom, InferenceNet, StreamLake, Sail Research, …) | The cheapest rows | Often good 1-day figures, no track record | Mixed | Promotions common | Several are not ZDR | Test arms at most |
| RunPod (GPU rental) | Any GGUF: the exact local artifact | Community availability varies | llama.cpp grammar, as local | — | Hosts may not inspect pod data (ToS); Secure Cloud for sensitive work | Exact doc 44 builds at higher precision |

### 2.2 Reliability [V]

- Most major hosts read 99.2–99.99% over one day. Red flags at read time: Alibaba's own Qwen3.5-35B-A3B endpoint (57.85% over one day),
  Google Vertex gpt-oss-120b (39.58%, status down), Amazon Bedrock's gpt-6-luna endpoint (0.04%), Groq gpt-oss-20b (96.29%), Nebius
  Qwen3-30B-2507 (95.74%), NextBit Gemma 4 26B (98.05%).
- These are snapshots of OpenRouter traffic. The runner must record uptime at the start and end of each run and must never fall back
  silently: with `allow_fallbacks: false` an outage pauses the run (retried, then stopped), and a named fallback host is a separate,
  labelled arm (D023 decision 3) [I].

### 2.3 Structured output belongs to the endpoint, not the model [V]

- The same Gemma 4 26B-A4B lacks the `structured_outputs` flag at Novita, Cloudflare, Makora, DekaLLM, Io Net and Google's `:free`
  endpoint. DeepSeek's and Z.ai's first-party APIs offer JSON mode but no `json_schema`. MiniMax-M3 first-party has no `response_format`
  at all; only 3 of its 13 OpenRouter endpoints flag schemas. Nova 2 Lite does not support Bedrock's structured outputs (model card).
- Flags and vendor docs disagree in at least six places: Moonshot (flag true, docs `json_object` only), Alibaba qwen3.8-flash (flag
  true, docs "Singapore region models are not supported yet"), GLM-5.3-Flash at Together (OpenRouter true, HF router false), Gemma at
  Scaleway (Scaleway docs strict, HF false), Claude on Bedrock (OpenRouter false, Bedrock docs true) and gpt-oss-20b on Bedrock
  (OpenRouter false, the Bedrock model card lists structured outputs as supported). Mistral's flag is true while its docs describe a
  schema injected into the prompt with no guarantee. So a capability probe must send a real strict-schema request and
  check conformance; it cannot read flags (D021 decision 4 already requires a probe per endpoint, model and version) [V; I].
- Schema dialects differ: Groq strict mode needs every property required and `additionalProperties: false`; Cerebras rejects `pattern`,
  `oneOf`/`allOf`/`not`, recursion and schemas over 5,000 characters; Anthropic rejects numeric and length limits; Gemini supports a
  keyword subset; Cohere rejects `minItems`/`maxItems` and length limits. A letter-enum PICK schema works everywhere; FILL needs a
  per-provider normaliser plus code validation of whatever was stripped (doc 40 §2.6) [V; I].
- Doc 44's "0 parse failures in 1,216 calls" came from local grammar enforcement. It does **not** carry over to the cloud automatically,
  so the D009 validator and repair loop stay on every cloud step [I on V].

### 2.4 Caching, batch and discounts [V]

- Cache reads cost 5–10% of input where listed (DeepSeek about 2%). Our test prompts never reach a cache minimum, so round 1 pays full
  input price everywhere (§1.3).
- OpenRouter `:batch` is not uniformly half price. OpenAI, Anthropic, Google and Mistral batches are 50%; batches served by DeepInfra
  (gpt-oss-120b, DeepSeek V4.1 Flash, GLM-5.3, GLM-5.3-Flash) are 0.8x of DeepInfra's price, and the GLM ones run at **fp4**, a different
  artifact from the pinned fp8 runs. Batch accepts one provider per batch. Some `:batch` prices exceed the cheapest synchronous host.
- Promotions are common on the cheapest rows: DeepInfra DeepSeek V4.1 Flash (30% off), GLM-5.3-Flash (50%), Qwen3.8-27B (25%), Morph
  GLM-5.3 (list $1.19/$3.74) and Kimi K3 (list $2.50/$14.00). Budgets in §6 use the billed price and leave room for the list price.
- Flex tiers appear as their own OpenRouter endpoints. Gemini 3.1 Flash-Lite's `google-vertex/global/flex` ($0.125/$0.75) is on the ZDR
  list, so R18 could run at half price if queueing is acceptable (about $0.11 instead of $0.21); gpt-6-luna's `openai/flex`
  ($0.05/$0.25) is not ZDR and has no Azure counterpart [V; I].

### 2.5 Privacy, ZDR and EU hosting [V]

- OpenRouter keeps no prompt logs by default, and per request `zdr: true` restricts routing to ZDR endpoints while `data_collection:
  "deny"` excludes providers that store data. The DeepSeek first-party, Alibaba, Darkbloom and `:free` Gemma endpoints are not ZDR.
  Three caveats from OpenRouter's ZDR page: a provider's in-memory prompt caching does not count as retention; ZDR enforcement covers
  provider routing only, "not plugins and tools" (another reason to keep Response Healing and other plugins off); and ZDR can also be
  enforced account-wide in the privacy settings, which is a second guard beside the per-request flag.
- Defaults differ sharply among the direct APIs: Together stores prompts (and may use them for product improvement) until an org admin
  enables ZDR; Nebius keeps data for speculative decoding unless ZDR is switched on; Groq keeps nothing by default except up to 30 days
  for abuse or troubleshooting; Fireworks and DeepInfra keep no prompts (Fireworks' Responses API and DeepInfra's bulk APIs are
  exceptions); Scaleway retains nothing by default except failing or malicious requests (up to two weeks); OVHcloud keeps only billing
  data; Featherless never stores; Mistral has an opt-out toggle plus ZDR on request (case by case, not for batch); DeepSeek trains
  unless the user opts out.
- Free and data-for-discount tiers pay with data: the Gemini free tier is "used to improve our products" (users in the EEA, UK and
  Switzerland get paid-tier terms), Mistral's free Studio mode may train unless opted out, and Meta's Muse Spark Contributor tier grants
  training rights for its discount. Acceptable for our public synthetic suites; never a default for user content.
- EU options: Mistral (`mistral/eu`), Scaleway (Paris), OVHcloud (French vendor; region not stated), Google Vertex EU endpoints (+10%;
  tagged `google-vertex/europe` for Claude and `google-vertex/eu` for Gemini 3.x), NextBit (Spain), Alibaba Frankfurt (but qwen3.8-flash
  only with Global scope there). The first-party APIs of Anthropic (`global` or `us` only), xAI, DeepSeek, Moonshot, Z.ai
  and MiniMax offer no EU processing.

### 2.6 Aggregator economics and open price conflicts [V]

- OpenRouter's default routing weights providers by the inverse square of their price, so unpinned traffic mostly lands on the cheapest,
  often newest and quantisation-unknown host (for Qwen3.6-35B-A3B that is Darkbloom fp4, which is not ZDR). Its Auto Exacto re-ranking
  applies only to requests that include tools, which Plotroom's PICK and FILL calls do not send.
- Conflicts to settle from `usage.cost` on the first real calls: Fireworks' DeepSeek V4.1 Flash is $0.30/$1.20 on Fireworks' page and
  $0.22/$0.66 on its OpenRouter endpoint; Groq gpt-oss prices differ between the HF router ($0.10/$0.50) and Groq's docs ($0.075/$0.30);
  AWS lists Bedrock gpt-oss-20b at $0.07/$0.30 against $0.07/$0.15 on OpenRouter; a third-party aggregator lists nscale's Qwen3-4B-2507 at
  $0.20/$0.60 against HF's $0.01/$0.03; grok-4.7 is $2.00/$6.00 at xAI and $1.60/$4.80 on OpenRouter.

## 3. Models by role and price band

### 3.1 Cheap models to test with the harness

Public signals, for orientation only: the Artificial Analysis Intelligence Index v4.3.2 (AA II) is a general composite of agents,
coding, general knowledge and science and no longer includes IFBench or τ²-bench; EQ-Bench Creative v3 is English, judged by a Claude
model; EuroEval measures understanding and knowledge, not generation; Vectara's board measures summarisation faithfulness (lower is
better). Our suites decide [V for the numbers; I for the use].

| Model @ pinned endpoint | USD in / out | Precision | Reasoning control | Public signals | Role to test [I] | Run |
| --- | --- | --- | --- | --- | --- | --- |
| gpt-6-luna @ `azure` | 0.10 / 0.50 | n/a | `none` … `max` (default `medium`); no `temperature` | AA II 18 (no reasoning), 21 (low), 37 (max); abstains rarely (AA non-hallucination 0.15–0.23) | PICK, FILL, EXPLAIN; doc 40's cheap tier | R12 |
| DeepSeek V4.1 Flash @ `deepinfra/fp8` | 0.14 / 0.42 promo (list 0.20 / 0.60) | fp8 | off, low, high, max (default high) | AA II 25 (no reasoning), 39 (max); EQ 1540 | PICK, FILL | R13 |
| Mistral Small 4 @ `mistral/zdr` | 0.15 / 0.60 | undisclosed | `none` or `high` | AA II 9 (no reasoning), 11 | Weak cheap generalist: how far the harness lifts it | R14 |
| gpt-oss-120b @ `deepinfra/bf16` | 0.037 / 0.17 | bf16 (upcast of native MXFP4) | low, medium, high (mandatory) | AA II 10 (low); Vectara 14.2%; EQ 961 | Price floor for PICK, FILL | R15 |
| Qwen3.5-9B @ `deepinfra/bf16` | 0.10 / 0.15 | bf16 | hybrid, off | AA II 13; first chunk 0.78 s | PICK, FILL; cloud copy of doc 14's T2a | R16 |
| Gemma 4 31B @ `crusoe/bf16` | 0.14 / 0.40 | bf16 | off by default | AA II 14; Vectara 7.4%; EuroEval #6 in Czech and Polish; EQ 1368 | FILL, EXPLAIN, multilingual | R17 |
| Gemma 4 26B-A4B @ `coreweave/bf16` | 0.10 / 0.30 | bf16 | off by default | AA II 13; Vectara 5.2%; EQ 1305 | Cloud copy of doc 47's offload candidate | R05 |
| Qwen3.6-35B-A3B @ `akashml/fp8` | 0.10 / 0.90 | fp8 | hybrid, off | AA II 15 (no reasoning) | Cloud copy of doc 47's offload candidate | R07 |
| Qwen3-30B-A3B-Instruct-2507 @ `nebius/fp8` | 0.10 / 0.30 | fp8 | none (non-thinking model) | BFCL V4 41.39% [V per doc 47] | Screening before a 14–22 GB local download | R09 |
| Gemini 3.1 Flash-Lite @ `google-vertex/global` | 0.25 / 1.50 | n/a | `minimal` lowest (default) | EuroEval #5 in Czech and Polish (preview); Vectara 8.2% (preview) | PICK, FILL, translation | R18 |
| GLM-5.3-Flash @ `deepinfra/fp4` | 0.075 / 0.25 promo (list 0.15 / 0.50) | fp4 | forced thinking: low, high, max (default max) | AA II 42, the highest here, but AA's run of its own index cost $0.25 against $0.03 for gpt-6-luna at high effort (verbose thinking); EuroEval #1 in Czech and Polish; non-hallucination 0.72; 3.14 s to first chunk, 47.9 s end to end | COMPOSE, translation, batch; not PICK | R19 |

### 3.2 Writers and translators (DRAFT)

| Model @ endpoint | USD in / out | EQ-Bench Creative v3 Elo | Note | Run |
| --- | --- | --- | --- | --- |
| GLM-5.3 @ `morph/fp8` | 0.36 / 1.14 promo (list 1.19 / 3.74; Z.ai 1.40 / 4.40) | 2075.0 (#6, above Opus 5.5's 2050.1) | Forced thinking; licence "other" | R22 |
| Qwen3.8-27B @ `deepinfra/bf16` | 0.15 / 1.875 promo (list 0.20 / 2.50) | 1671.3 | Doc 14's T2b all-rounder; Apache-2.0 | R23 |
| Kimi K3 @ `morph/fp8` | 0.99 / 5.53 promo (list 2.50 / 14.00) | 2082.3 | Optional reference | O2 |
| Muse-Glimmer-30B @ `deepinfra/bf16` | 0.30 / 1.20 | 1798.3 | Blocked: its Usage Policy prohibits "Military, warfare … applications"; owner decision | O3 |
| claude-sonnet-5 | 2.00 / 10.00 | 1794.0 | Writer reference inside R20 | R20 |
| Hy-MT2-7B / 30B-A3B / 1.8B (Tencent) | 0.074 / 0.295 (1.8B: 0.044 / 0.177) | n/a | Translation specialist; 8K context; Apache-2.0 at the current revision; needs a translation suite | — |
| Bielik-11B-v3.0 (Public AI via HF) | 0.40 / 0.40 | n/a | Polish specialist; single host; host warns EU/UK users; needs a suite | — |

No public benchmark measures Czech, Polish or Russian creative quality (doc 14). Our `text` suite is 10 English flavour slots, so the
writer probes of round 1 show constraint-keeping and a grader's first impression, not DRAFT quality; a translation and non-English
DRAFT suite with native reviewers (doc 14 §9 item 4) is a precondition for choosing a writer or translator [I].

### 3.3 Frontier comparators (bare)

| Model @ endpoint | USD in / out | Reasoning | Note |
| --- | --- | --- | --- |
| claude-sonnet-5 @ `google-vertex/global` | 2.00 / 10.00 | Default `high`; can be disabled | Rejects `temperature` and `seed`: sample diversity comes from menu permutations only |
| gpt-6-sol @ `azure` | 2.00 / 10.00 | Default `medium`; `none` available | Rejects `temperature`; on Chat Completions, function calling works only at effort `none` (not used here) |
| claude-opus-5-5 @ `google-vertex/global` (optional) | 4.00 / 20.00 | Cannot be disabled; OpenRouter lists default `high`, Anthropic's docs `medium` | Run only if R20 and R21 disagree |

### 3.4 Local ↔ cloud pairs

| Local artifact (doc) | Cloud pair(s) | What a difference would isolate [I] |
| --- | --- | --- |
| Ministral 3 3B Q4_K_M (doc 44, Ollama) | `mistral/zdr` (precision undisclosed) | Runtime + precision + grammar engine together. The only doc 44 model with a hosted copy |
| Qwen3-4B-Instruct-2507 Q4_K_M (doc 47 plan) | nscale via HF | As above; nscale's precision is undisclosed |
| gpt-oss-20b MXFP4 GGUF (not yet run locally) | `coreweave/fp4` (native), `deepinfra/bf16` | Same numerics on CoreWeave: engine, template and grammar only. The cleanest test of the llama-server sidecar path |
| Gemma 4 26B-A4B QAT Q4 with `--n-cpu-moe` (doc 47 plan) | `coreweave/bf16`, `deepinfra/fp8` | Checkpoint (QAT vs original) + quant + engine: read as "is the local build good enough", not a pure quant effect. The two hosts differ in precision, so they satisfy §4.3's "two hosts agree" only on the evidence that fp8 is near-lossless; if they disagree, the same-precision replicate is `parasail/bf16` ($0.13/$0.40, ZDR, schemas; battery B about $0.031) |
| Qwen3.6-35B-A3B UD-Q4 with expert offload (doc 47 plan) | `akashml/fp8`, `parasail/fp8` | Quant + engine; fp8 matches Qwen's official FP8 checkpoint |
| Gemma 4 E4B QAT, Qwen3.5-4B, Granite 4.1 3B (docs 44, 46) | No cheap serverless host (Qwen3.5-4B only at Featherless, $25–50/month minimum) | Rent a GPU and run the identical GGUF at Q8 or bf16 with the same llama-server build: this isolates quantisation from everything else |

**Precision ladder inside the cloud** (R10, R11, R17): Gemma 4 31B at fp4 (`deepinfra/turbo`), fp8 (`parasail/fp8`) and bf16
(`crusoe/bf16`). It isolates precision from the local runtime, but server fp4 (NVFP4 or MXFP4) is not GGUF Q4_K_M, so the result
transfers only qualitatively [I].

### 3.5 Considered and not selected [V; I]

- **Claude Haiku 4.5**: $1/$5, AA II 15.4–16.9, EuroEval Czech #12, retirement no sooner than 2026-10-15 with no newer Haiku listed. Most
  of what it adds is abstention (non-hallucination 0.74), which MiniMax-M3 (0.82) and GLM-5.3-Flash (0.72) match for less.
- **Gemini 3.5 Flash-Lite**: $0.30/$2.50 against 3.1 Flash-Lite's $0.25/$1.50, and 9.87 s to the first chunk on AA.
- **Nova 2 Lite** (no structured outputs), **Qwen3.7/3.8 Flash** (no `json_schema` in the international region), **Kimi K2.6**
  (`json_object` only; its privacy documents conflict), **Grok 4.3/4.7** (mid price for AA II 25–46), **DeepSeek first-party**
  (privacy and schema, §2.5), **Muse Spark Contributor** (training rights), **Ling 3.0 Flash** ($0.021/$0.063, but no endpoint enforces a
  schema), **Ministral 14B** (weakest Mistral uptime; no Czech, Polish or Russian), **Hy3** (guesses often: non-hallucination 0.26).
- **Optional later**: MiniMax-M3 (O5), MiMo-V2.6-Flash (its only ZDR host was degraded at read time), Command A+ (Apache-2.0 weights,
  JSON Schema mode, Czech, Polish and Russian; first-party price not on Cohere's pricing page).
- **Added in review** [V for prices and flags; I for the roles]:
  - **Nemotron 3.5 Lightning 30B-A3B** (NVIDIA, 2026-08; OpenMDW-1.1, ungated; doc 14 lists it with EQ-Bench 1280): $0.07/$0.20 at
    `coreweave/bf16` and $0.08/$0.20 at `deepinfra/bf16`, both ZDR with structured outputs, 99.9–100% 1-day uptime. It is the cheapest
    3B-active MoE here with **two same-precision hosts**, so §4.3's attribution rule applies cleanly, and it is a further 30B-A3B
    offload-size model. Reasoning is optional. Its languages are English, Spanish, French, German, Italian and Japanese (no Czech,
    Polish or Russian), so it is a PICK/FILL candidate only; as a *download*, OpenMDW-1.1 stays "custom", never recommended, until
    OSI approves it (owner, OWQ-19 (a); D037), which does not affect hosted use. Optional run O6.
  - **Granite 4.2-8B** at `coreweave/bf16` ($0.10/$0.15, ZDR, structured outputs; the DeepInfra copy flags none): the only hosted Granite
    with an enforced schema, if doc 14's Granite line is carried to 8B.
  - **Seed 2.0 Mini** (ByteDance, proprietary; first-party `seed/fp8` only, $0.10/$0.40, ZDR, structured outputs; lowest effort
    `minimal`, not `none`): no public evidence was gathered for it; not selected.
  - **Cheaper hosts for planned weights**, not pinned because they are newer or report no precision: Reka serves Gemma 4 26B-A4B at
    $0.06/$0.20 and 31B at $0.08/$0.30 (both ZDR, schemas; no headquarters listed); inference-net serves DeepSeek V4.1 Flash at
    $0.035/$0.29 (ZDR, schemas, 98.76%); AkashML and CoreWeave serve gpt-oss-120b at $0.03/$0.17 (ZDR).

## 4. Cross-provider variance and how the test controls it

### 4.1 Evidence [V]

- **Serving defects dominate.** gpt-oss-120b on AIME25 (high effort, 32 runs, reported by Artificial Analysis): 93.3% on six hosts,
  90.0% Parasail, 86.7% Groq, 83.3% Amazon, 80.0% Azure ("old vLLM commits that didn't respect reasoning_effort"), 36.7% CompactifAI;
  Groq and Azure reached 93.3% within days. Artificial Analysis's Endpoint Accuracy Index (2026-08-04) found some gpt-oss-120b endpoints
  at 22% on BFCL-500 against the reference's 37%, and restrictive output caps halving some GLM-5.2 endpoints; its named causes are
  tool-schema parsing, context and output limits, reasoning-effort limits and precision.
- **Schema accuracy varies by host.** Moonshot's K2 Vendor Verifier (2025-11-15): Kimi K2-0905 tool-call schema accuracy 100% on
  Moonshot, Fireworks, DeepInfra, Groq and Novita; 84.47% on Nebius; 76.00% on vLLM; 73.13% on SGLang; 71.96% on Together. vLLM
  traced its failures to a dropped `add_generation_prompt` argument, empty content converted to a list and a strict tool-call-id parser
  (218 of 1,200+ calls parsed before the fixes); Moonshot's own API uses a constrained-decoding "Enforcer".
- **Quantisation alone is usually small.** OpenRouter: "We haven't seen a measurable impact on tool-call quality from quantization
  alone"; "Novita at FP4 beat FP8 providers"; Auto Exacto cut gpt-oss-120b tool-call errors from 5.6% to 3.5% by preferring better
  hosts. FP8 W8A8 is "lossless across all model scales" and INT4 weight-only recovers 99.36% (arXiv 2411.02355, Llama 3.1). llama.cpp
  Q4_K_M on Llama-3.1-8B moved IFEval +0.22, GSM8K −0.22 and MMLU −1.07 points (arXiv 2601.14277). **Small models are the exception**:
  Llama-3.2-1B at 4 bits lost 16 IFEval points (GPTQ family, arXiv 2409.11055), and a study of seven 1–4B models found losses of up to
  57% relative on multilingual maths and code with commonsense nearly intact (IJAI 13(1), June 2026). So quant effects matter most for
  the 3–4B tier and non-English DRAFT, least for PICK [I].
- **Our candidates specifically.** Gemma 4 26B-A4B's QAT Q4 agrees with the BF16 QAT checkpoint on the top token 85.63% of the time (KLD
  0.098; E4B 98.54%), the least faithful of the Gemma 4 QAT builds. Qwen3.6-35B-A3B at Q8_0 has KL 0.069 overall and 0.177 on tool
  calling. A q8_0 KV cache pushes Gemma 4 26B-A4B's KL to 0.377 while Qwen3.6 stays below 0.04, so the local arm runs with an f16 KV
  cache; hosted KV precision is undisclosed [V; U].
- **Templates and grammars are part of the artifact.** gpt-oss grammars reject Harmony control tokens in LM Studio (issue #1555, open
  since 2026-02-24); vLLM's guidance backend ignored the schema with the gpt-oss reasoning parser (vLLM #37359); Unsloth fixed a
  Qwen3.5 tool-calling template affecting "all quant uploaders and types" (2026-03-05); Gemma 4 GGUFs were re-issued with template
  fixes around 2026-04-11; llama.cpp #28509 misclassified the Gemma 4 26B template (fixed by PR #28511); a wrapper kept Qwen3.5-35B
  thinking despite `enable_thinking: false` (lemonade #1511).
- **Nothing is reproducible by seed.** At temperature 0, Qwen3-235B-A22B-Instruct-2507 gave 80 distinct completions in 1,000 because batch
  size varies with load (Thinking Machines, 2025-09-10). Model Equality Testing found 11 of 31 endpoints serving distributions that
  differ from the reference weights (arXiv 2410.20247). First-party serving drifts too: Anthropic's 2025-09-17 postmortem describes a
  routing bug that hit 16% of Sonnet 4 requests at peak and that "the evaluations we ran simply didn't capture".

### 4.2 Controls [I]

1. **Pin the endpoint:** `provider = {only: [<tag>], allow_fallbacks: false, require_parameters: true, quantizations: [<q>],
   data_collection: "deny", zdr: true}`. Never `:exacto`, `:floor` or `:nitro` in qualification runs. The runner warns on an unpinned
   OpenRouter run and refuses a strict-schema run without `require_parameters`.
2. **Record what served each call**: the endpoint tag, the quantisation tag, the served provider (when returned), `usage.cost`, reasoning
   tokens, finish reasons, the price row with its date and source. Spot-check generation ids.
3. **Same sampler on both arms**, sent explicitly; a parameter an endpoint rejects is dropped and logged (`params_dropped`), never
   silently omitted. Presence penalty 0 for PICK and FILL (doc 46 §2.2).
4. **Thinking off, verified per call.** A call sent with `reasoning: none` that reports reasoning tokens or returns thinking text stops
   the run (`ReasoningLeak`). Mandatory-reasoning models run at their lowest effort on both arms, with the effort recorded.
5. **One schema mode per comparison:** strict `json_schema` on the host against a GBNF grammar from the same schema locally. Where the
   local arm must run unconstrained (gpt-oss with Harmony), the host arm is also run unconstrained. Response Healing stays off (the
   runner refuses to enable it). Every strict-schema record carries `schema_conformant`, and the canary stops a run whose endpoint
   accepts the schema but ignores it.
6. **Same template:** pin the GGUF revision and diff its rendered prompt against the Hugging Face tokenizer template before blaming
   weights.
7. **Same local runtime as production:** llama-server build pinned, f16 KV cache, stated context, the `--n-cpu-moe` value logged. Expert
   offload changes where weights sit, not their precision, so it should change speed, not answers [I; unmeasured].

### 4.3 Attribution rule [I]

| Observation (item-paired, at least two same-precision hosts plus the local arm) | Reading | Next step |
| --- | --- | --- |
| The two hosts agree with each other and both beat local by ≥ 10 points | The local stack costs quality (quant, engine, template or grammar) | Run the same GGUF at Q8 or bf16 on a rented GPU with the same llama-server build: a gain there is quantisation, none is the engine |
| Only one host differs from the rest | A host defect | Exclude that host; report it |
| Hosts agree with local | No cloud advantage for this model and step at this n | Keep the local recommendation |
| The fp4 host matches the fp8 hosts, and all differ from local | Not "4-bit" as such: the local engine or template | Diff templates; check grammar behaviour |
| Any difference under about 10 points on 30 menus | Noise (doc 44 §6) | Use the 100-menu instrument (doc 44 §5.4 item 1) before claiming it |

### 4.4 Statistics [I on V]

- Pair by item; McNemar on per-item pass^3; item-cluster bootstrap intervals (10,000 resamples, fixed seed), because the samples of one
  item are correlated. With α 0.05 two-sided and power 0.8, a 5-point effect at 10% discordance needs about 311 paired items, 10 points
  at 15% about 115, and 30 points at 35% about 28.
- Preliminary `pick-hard` effect sizes from the doc 46 records (unreviewed at the time of reading): cards against none moved Qwen3.5-4B's
  per-call accuracy from 0.822 to 0.867 (Q4_K_M) and 0.811 to 0.900 (UD-Q4_K_XL). So the open-versus-menu rung, knowledge with and
  without cards (doc 44: 0 to 5–8 of 24) and the Fill schema rungs are testable with today's items, while cards-versus-none and
  model-versus-model differences under 10 points are not.
- Extra cheap-model calls cost about $0.00002 each, so the bottleneck is item authoring, not money.
- A 20-item canary per pinned endpoint, re-run monthly, catches drift: gpt-oss host spreads tightened within weeks in 2025.

## 5. The harness-uplift instrument

Proposed as doc 25's next evaluation instrument after doc 40's E12. Doc 29 already uses E13 for an engine extension (the E-number
collision is tracked in DG005), so this doc calls it **48-U** until codes are assigned.

### 5.1 Rungs [I; implemented as `--variant` and `--repair` in the pending tool patch]

Each rung removes one harness mechanism; every other byte of the prompt, the seeds and the menu permutations stay the same, so arms pair
item by item.

| Step | Bare | Rungs up to the full harness | Full harness |
| --- | --- | --- | --- |
| PICK (`pick`, `pick-hard`, k = 3) | **P0 `open`**: the request, a one-line stem ("Which waypoint type should this be?"), "answer in at most eight words", no menu, no schema | **P1 `labels`**: valid names only, no letters or descriptions · **P2 `noschema`**: the lettered menu with descriptions, no `response_format` (optional one repair call) · **P3**: strict schema, no card | **P4**: strict schema plus the reference card; **P5**: voting over P4's samples, computed offline (`vote3`, adaptive stop when two samples agree) |
| FILL (k = 3) | **F0 `noschema`**: field glossary and "JSON only", no schema | **F1 `schematext`**: schema text in the prompt, no `response_format` · **F2**: strict schema | **F3 `--repair`**: F2 plus at most one repair call naming the failed check ("place: quoted text not found in the request") |
| EXPLAIN (k = 2) | **E0**: no card | — | **E1**: with the card |
| Text (k = 2) | **T0 `bare`**: slot and context, no constraint list | **T1**: constraints · **T2**: constraints plus style card | **T3**: generate until every code check passes, at most 2 samples (offline) |
| Knowledge (k = 2) | **K0**: no card | — | **K1**: with the card (in the product, code shows the card itself) |

The open arms never take the reference card, because the PICK cards name the answer's option in 43 of 60 items; the tool refuses that
combination.

### 5.2 Grading the open arms [I]

- A sidecar of aliases per option (label, key with separators as spaces, codes, synonyms such as "transport unload" for TR UNLOAD) maps
  free answers to keys: exact alias, then escape phrase, then the longest whole-word match when exactly one option matches; anything else
  is `unmapped` and counts as wrong. A judge maps only the unmapped answers and never sees the request, so it cannot solve the task.
- Uplift is reported separately for **engine-vocabulary items** (waypoint and trigger: a bare model may know these words) and
  **code-owned items** (module, cutscene archetype, mood preset, routing, arc, campaign, replayability: no bare model can know Plotroom's
  catalogue ids). The headline cheap-versus-frontier comparison uses engine-vocabulary PICK items plus FILL, EXPLAIN, Text and Knowledge;
  otherwise it is rigged in the harness's favour.

### 5.3 Metrics [I]

- Per-call accuracy with a Wilson interval; the unbiased pass^k estimator (mean over items of C(c, k) / C(n, k), τ-bench, arXiv
  2406.12045); decision accuracy under the policies `single`, `vote3`, `adaptive` and `first_admitted_2`.
- CPCD, CPAD and the false-admit rate (§1.3). Gemma quoting the finding code CF01 as a place (doc 44 §2.2) is the kind of error the
  false-admit rate exists for.
- Uplift Δ = metric(full) − metric(bare), item-paired; the error reduction (err_bare − err_full) / err_bare; the token overhead
  input(full) / input(bare).
- Latency p50 and p90 per call and per decision; errors, 429s and retries per 100 calls; served-provider mismatches (must be 0).

### 5.4 The headline comparison [I]

A 2 × 2 per step kind, {cheap cloud model, frontier model} × {bare, full harness}, plus the local 4B with the full harness from docs 44
and 46 at $0 cash (time reported). Frontier-bare arms run at the provider's default effort (a user asking a chat model) and again at the
lowest effort; cheap-full arms run at `none`.

- **Gap closure** H = (acc_cheap_full − acc_cheap_bare) / (acc_frontier_bare − acc_cheap_bare). H ≥ 1 means the harness lifts the
  cheap model to or past the bare frontier model.
- **Substitution test:** non-inferiority of cheap_full against frontier_bare on decision accuracy and pass^3; the one-sided 95% lower
  bound of the difference must exceed −0.10 in this round (−0.05 in a confirmation round of at least 100 menus). The CPCD ratio is
  reported beside it.
- **"Best balance" per step kind:** the cheapest setup by CPCD whose pass^3 point estimate is at least 0.8 (doc 44's bar) and no more than
  10 points below the best, which passes every planted escape, whose endpoint shows at least 99% 1-day uptime, and which has structured
  outputs on at least two endpoints so the user has a second host. Present the Pareto frontier (CPCD against pass^3) per step kind; never
  pool across step kinds (doc 25 §11.2).

### 5.5 Why these rungs [V for the studies; I for the mapping]

- Voting and decomposition favour small non-reasoning models: MAKER (arXiv 2511.09030) ran over a million steps without error using
  maximal decomposition, first-to-ahead-by-k voting and "red-flagging" of long or misformatted answers, and found "relatively small
  non-reasoning models suffice". Large Language Monkeys (arXiv 2407.21787) got its cost win only with an automatic verifier; majority
  voting plateaued. Wilco's validators are exact verifiers, so K samples with code admission help PICK and FILL most and DRAFT least.
- Constrained output helps, with a caveat for tiny models: dottxt's re-run of "Let Me Speak Freely" found structured output at or above
  unstructured, while "The Constraint Tax" (arXiv 2605.26128, models of 1.7B and below) saw validity rise from 61.5% to 100% as accuracy
  fell from 19.7% to 11.0%. Hence the separate wrong-but-valid (false-admit) rate and flat letter enums.
- Thinking effort is often wasted on short steps: HAL (arXiv 2510.11977) found higher effort did not improve accuracy in 21 of 36 runs,
  and "When Thinking Fails" (arXiv 2505.11423) found chain-of-thought degrading instruction following. So PICK and FILL run at `none`.
- Retrieval cards close knowledge gaps for mid-size cloud models (doc 30: a small cloud model went from 1/24 to 16/24 with cards) but not
  for 3–4B local ones (doc 44: 0/24 to 5–8/24) [V per docs 30 and 44].

## 6. The test plan

### 6.0 Round 0: free models first (owner request, 2026-09-27)

The owner asked for a safe way to test models over OpenRouter, starting with free models. Round 0 uses only OpenRouter's `:free`
variants, sends only the repository's synthetic suites and has no path to spending money. It needs the tool patch and nothing else;
round 1 (§6.1–§6.6) stays deferred. Nothing below has been run.

**Free-tier rules** [V, read 2026-09-27; the catalogue figures at 20:06 UTC]:

- A free variant is its own catalogue entry, `<author>/<slug>:free`. `openrouter/auto:free` is a router that can bill paid models, so
  a suffix check alone is unsafe.
- 20 requests a minute. 50 a day while fewer than 10 credits have ever been bought, 1,000 a day from then on (lifetime purchases, not
  the balance). The limits belong to the account: more keys or accounts do not raise them. The day resets at 00:00 UTC. Whether failed
  requests count is undocumented [U], so the tool counts every attempt.
- A negative balance returns 402 even on free models. `GET /api/v1/key` sends no prompt and reports the key's `limit`,
  `limit_remaining`, `usage`, `byok_usage`, `is_management_key` and the account's `free_model_daily_requests` (`used`, `limit`,
  `remaining`).
- Two account toggles gate free endpoints: "Free endpoints that may train on request data" and "Free endpoints that may publish
  prompts". With one off, matching endpoints drop out and requests fail with 404 "No endpoints available matching your guardrail
  restrictions and data policy". Account, organisation and key settings stack, and the strictest wins. ZDR removes every free endpoint
  that retains prompts.
- A free call can still cost money through file or PDF input (a paid parser), fallback model lists, BYOK routing, models billed per
  item, or routers. Free variants come and go without notice; `expiration_date` was null on every one.
- The catalogue: 458 models, 17 of them free text models with one endpoint each. Only 3 free text endpoints are on the ZDR list:
  Qwen3.8-27B (ModelRun, fp4) and two Ling 3.0 Flash finance and health specialists. Four list `structured_outputs`: Qwen3.8-27B
  (without `response_format`), dots-3-note-preview, Nemotron 3 Super and LFM 2.5 2.6B. None of doc 44's models, gpt-oss, the Mistral
  models or Bonsai 2 has a free variant.

**Safety design** [V for the tool against its mock server: 59 tests pass and 66 injected faults, one per guard, are all caught; I for
real endpoints, which it has not met]:

| Goal | How |
| --- | --- |
| The key never appears in chat, argv, shell history, logs, records or plaintext on disk | The owner types it once at the hidden prompt of `set-openrouter-key.ps1`, which stores it DPAPI-encrypted for the Windows user at `%LOCALAPPDATA%\plotroom-dev\secrets\openrouter.key` (user-only ACL; any path inside a git working tree is refused). `run-cloud.ps1` decrypts it only into the environment of the one `run.py` process it starts, and refuses a run without `--free-only` or with `sk-or-` or `--api-key` in its arguments. Records and logs redact `sk-or-*`; the key's `label` is never printed. Residual: the plaintext sits in those two processes' memory during a run; DPAPI protects the file from other users and machines, not from programs running as the same user |
| Zero spend | A dedicated account with no payment method, Auto Top-Up off and no BYOK keys; one key with a $0 credit limit. `--free-only` refuses unless the id is `<author>/<slug>:free` outside `openrouter/` and, at every start and resume, the live keyless catalogue lists it with every price exactly 0 (a router's −1 fails; no model lists a `request` price today, so an absent price counts as 0), text output only and every endpoint at 0. The cap and all prices are 0; `require_parameters: true`, `allow_fallbacks: false` and `only` pinned to the endpoints read at start. A response whose `usage.cost` is anything but exactly 0, or that carries a BYOK cost, another model or an unlisted provider, stops the run at once (exit 9). `GET /api/v1/key` runs at the start, every 10 attempts or fewer and at the end: any rise in usage is exit 9, and the ledger keeps the last reading, so a charge no response showed stops the next start. The key check refuses a management key, a key without a limit and a key with more than `--max-key-headroom-usd` (default 0) left, unless the owner overrides it explicitly |
| Rate limits | At most 18 attempts in any 60 s and 45 per UTC day in the shared ledger, and never more than the account's remaining free requests minus 5. Every attempt counts. A daily-cap 429 ends the run (exit 10) with the time to resume; a per-minute 429 waits for its reset; three 429s in a row end the run. One free run at a time per Windows user; `--resume` continues after 00:00 UTC |
| Privacy | Only the synthetic suites are sent. The tier is an account setting (below) |

**Privacy tiers** [V: OpenRouter's provider table, read 20:13 UTC, which describes providers, not single endpoints; I for the tiers].
Input & Output Logging (Settings → Observability) and OpenRouter's use of inputs and outputs (Settings → Privacy, the 1% discount) stay
off. So does the publish toggle: no free text provider was flagged as publishing. Account-wide ZDR stays off on this account, because
tier 0 sends `zdr` per request.

| Tier | Toggles "may train" / "may publish" | Per request | Models added, and their hosts' policies |
| --- | --- | --- | --- |
| 0 | off / off | `zdr: true`, `data_collection: "deny"` | Qwen3.8-27B `:free` (ModelRun: on the ZDR list; no training, no retention) |
| 1 | off / off | none | Gemma 4 26B-A4B `:free` (Google AI Studio: no training, prompts kept 55 days); dots-3-note-preview `:free` (AtlasCloud: keeps prompts, no training) |
| 2 (Z13–Z15 only) | **on** / off | none | Nemotron 3 Ultra and 3 Super `:free` (NVIDIA API trial terms), LFM 2.5 2.6B `:free` (Liquid): they train on and keep prompts and receive a pseudonymous user id |

**Never turn either free-endpoint toggle on for an account whose keys carry real user content.** Round 0 therefore runs on a
dedicated account, and the product default stays `data_collection: "deny"` with `zdr` offered (§7.1).

**Runs** [I]. Every run is k = 1: sample 0, which pairs item by item with sample 0 of every local k = 3 record, because menu order is
seeded by item and sample. About 40 requests are planned per day under the tool's 45; every request costs $0. Rungs are §5.1's. Each
arm is one command (written on one line), for example Z04:

```text
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\run-cloud.ps1 --backend openai --free-only
  --base-url https://openrouter.ai/api/v1 --ledger tools/local-qual/results/free-ledger.jsonl --resume
  --model qwen/qwen3.8-27b:free --reasoning none --drop-params seed --extra-body @tools/local-qual/cloud/provider-zdr.json
  --suite pick-hard --condition cards --k 1
```

Gemma's model flags are `--model google/gemma-4-26b-a4b-it:free --reasoning none`. `--resume` makes every command safe to repeat: it
skips calls already recorded, so preflight items are not sent twice and a run stopped at the daily cap continues the next day.

| # | Model (tier) | Arms | Requests | Day | What it answers |
| --- | --- | --- | --- | --- | --- |
| Z00 | Qwen3.8-27B (0) | `pick` PW01 with `--dry-run` | 0 | D1 | The pinned request, and a worst case of $0 |
| Z01 | Qwen3.8-27B (0) | `pick` PW01: P3 | 1 | D1 | What OpenRouter does not document: whether a key with a $0 limit may call `:free` models; the `model` string of a free response; `usage.cost` present and 0; whether a strict schema routes to an endpoint that lists `structured_outputs` but not `response_format`; whether reasoning off is honoured |
| Z02 | Qwen3.8-27B (0) | `pick-hard` HW01: P4 and P2; `fill` F01: F2; `knowledge` T01: K0 | 4 | D1 | The §6.1 stage-1 preflight: served provider, finish reasons, reasoning tokens, schema conformance, τ |
| Z03 | Gemma 4 26B-A4B (1) | `pick-hard` HW01: P2; `fill` F01: F0 | 2 | D1 | Tier-1 routing with both toggles off; the no-schema path |
| Z04–Z07 | Qwen3.8-27B (0) | `pick-hard`: P4, P0, P3, P2, one a day | 29, 30, 30, 29 | D1–D4 | The Pick ladder on the harder suite |
| Z08 | Qwen3.8-27B (0) | `fill`: F0, F1, F3 (F2 is each F3 record's first answer) | 39 (≤ 48) | D5 | The Fill ladder: schema enforcement and repair |
| Z09 | Gemma 4 26B-A4B (1) | `pick-hard` P2; `fill` F0 | 40 | D6 | Same weights as doc 47's offload candidate and R05/R06, with no schema on either side (§4.2 item 5): the same two arms run on the local QAT build with the settings of its doc 49 run, at $0 and outside the quota |
| Z10–Z12 | Qwen3.8-27B (0) | `pick-hard` P1; `pick` P0 and P4; `explain` E0 and E1, `knowledge` K0 and K1, `text` T0 and T1 | 30, 60, 63 | D7–D10 | Optional: the rest of the ladder; with Z11, 20 engine-vocabulary items for §5.2's headline split |
| Z13 | Nemotron 3 Ultra 550B-A55B (2) | `pick-hard` P0; `fill` F0; `knowledge` K0 | 54 | D11–D12 | Optional: a large model's bare arms, for a proxy gap closure H′ = (Qwen full − Qwen bare) / (Ultra bare − Qwen bare). Not a frontier model |
| Z14 | LFM 2.5 2.6B (2) | `pick-hard` P0 and P4; `fill` F0 and F3, at effort low (its reasoning is mandatory) | 87 (≤ 96) | D12–D14 | Optional: the weak-model floor, the size of doc 44's small tier |
| Z15 | Nemotron 3 Super 120B-A12B (2) | `pick-hard` P0 and P4 | 60 | D14–D16 | Optional: whether the uplift carries to a second strict-schema model |

The core (Z00–Z09) is 204 requests (213 if every Fill item needs its repair call) over 6 days; all of round 0 is 558 (576) over about
16 days. Buying 10 credits once would raise the free limit to 1,000 a day for good and fit round 0 into one day at k = 1. That is a
spend decision for the owner, and it leaves the $0 key limit as the only barrier.
At 30 menus and k = 1 only effects of about 30 points are clear (§4.4); ten-point effects need round 1's k = 3 or the 100-menu
instrument. Each free model is one host at 4-bit or undisclosed precision and may serve differently from paid hosts, so round 0 screens
and qualifies nothing. It cannot stand in for the frontier comparators, the pinned precision rungs, doc 44's small models or Bonsai 2
(none of them has a free variant), or any cost per correct decision.

**Stop rules** [I]:

- **Exit 9 after a request** (a charge, a missing `usage` or a `usage.cost` other than 0, another model or provider, a rise in the key's
  usage): stop round 0, check the account's Activity page and revoke the key if anything was charged. That ledger never runs again.
  **Exit 9 at start**, with nothing sent, means the model left the catalogue or lost its zero price: drop its runs and never substitute.
- **Exit 4 (402) on Z01:** the $0 limit blocks free calls. Set the smallest limit the dashboard accepts ($0.01), add
  `--max-key-headroom-usd 0.01` and rerun Z01. Any later 402 stops the round.
- **Exit 5 on a Qwen strict arm:** never drop `require_parameters`. Qwen keeps its no-schema arms, and the strict arms move to
  dots-3-note-preview (tier 1) as a labelled different model. For exit 5 on privacy grounds, fix the tier; never widen it beyond the
  run's own tier.
- **Exit 7** (reasoning on an effort-none call): rerun that model at effort low with `--num-predict 1024` as a separate arm, never
  pooled with effort-none arms.
- **The canary** (the first 20 calls of a 30-item arm): more than 20% non-conformant answers in a strict arm, or more than 10% errors,
  stops that endpoint's strict arms.
- **Exit 10:** rerun the same command after 00:00 UTC. Drop an endpoint that stops on upstream 429s or errors two days running.
  Qwen3.8-27B's free endpoint read status −2 (not 0) with 98.17% 1-day uptime at 20:06 UTC.
- **Timebox:** if Z00–Z09 are not done 14 days after Z01, stop and report instead of extending round 0.

**What would justify the paid round** [I]:

- **Precondition:** Z01–Z03 pass. Every response shows $0, the pinned model and provider, flat key usage and no reasoning leak, and at
  least one free endpoint enforces a strict schema. The tool then works against a real endpoint, and round 1's remaining risk is money,
  which its caps bound.
- **A large uplift:** Qwen's P4 beats its P0 by at least 30 points on the 20 engine-vocabulary items (indicative at this n), or F3
  beats F0 by 30 points on whole-record Fill. The substitution question is then live, so stage 3b's frontier comparators (R20, R21:
  $3.94 of the $6.63) are worth running. With a gap under 10 points on engine vocabulary, shrink round 1 to stages 2 and 3a and keep 3b
  optional.
- **A usable hosted 27B:** Qwen3.8-27B with the full harness reaches 0.8 per-call accuracy on `pick-hard` P4 and on Fill F3. Then run
  R23 (the same weights at bf16 on a ZDR host, k = 3) and stage 3a to price its cost per correct decision.
- **Same weights that differ:** Z09 and the local Gemma build differ by at least 10 points on P2 or F0. Then run stage 2's R05 and R06
  (about $0.07) to find the cause (§4.3). Under 10 points, nothing follows at this resolution.
- **Friction:** if churn, upstream 429s or the 50-a-day limit break the timebox, move to round 1's pinned paid endpoints instead.

**Owner steps.** The account, privacy settings, key and key storage follow the runbook `tools/local-qual/cloud/README.md`, which lands
with the tool patch. Then Z00 and Z01, reading the exit code before anything else; Z02–Z04 the same day; Z05–Z09 on one day each. Tier 2
(Z13–Z15) turns "may train" on for its days only and back off afterwards. When round 0 ends, delete the key in the dashboard and run
`remove-openrouter-key.ps1`.

### 6.1 Stages and accounts

| Stage | Who | What | Cap (USD) |
| --- | --- | --- | --- |
| 0 | **Owner only** | Create the OpenRouter account and one key; set the key's credit limit to $12; buy $15 of credits once by card (fee $0.83; buying at least $10 also lifts `:free` limits to 1,000 requests a day); leave prompt-logging opt-in and plugins off, and turn on account-wide ZDR enforcement as a second guard beside the per-request flag. Optionally create a free Hugging Face account and a token allowed to call Inference Providers. Apply the tool patch after doc 49's local measurement run has finished with `tools/local-qual` | 0 |
| 1 | Runner | Preflight per endpoint: 4 calls at k = 1 (`pick-hard` with cards, `pick-hard` without schema, one Fill, one knowledge item). Check the served provider, finish reason, `usage.cost`, zero reasoning tokens on `none` arms, schema conformance, whether a precision-suffixed tag works in `provider.only` (fallback: the provider slug plus `quantizations`), and τ | 0.25 |
| 2 | Runner | Same weights, local vs cloud; precision ladder | 1.00 |
| 3a | Runner | Cheap models with and without the harness | 1.50 |
| 3b | Runner | Frontier comparators | 5.00 |
| 3c | Runner | Writer probes | 0.50 |
| 4 | Graders | Main grading as in docs 44 and 46 (LLM graders working from `score.py`'s grading sheet), kept outside this budget [I], but now with one grader model and one rubric for every arm, blind (names stripped, rows shuffled); a 15% double-grade sample through the API by a second model family for Cohen's kappa | 2.00 |

Every paid stage runs only when the owner starts it, or explicitly approves a session to start it, with the key in an environment
variable. One shared `--ledger` per stage enforces its cap across runs; a stop is `BudgetLimited` and resumable, never an error.

### 6.2 Runs, in order (prices read 2026-09-27; estimates at τ = 1.3)

Reasoning tokens per call are assumptions [U]: 0 at `none`; 30 at Gemini `minimal`; 300 for gpt-oss at `low`; 800 for the GLM models
at `low`; 480 for Sonnet 5 and 300 for GPT-6 Sol at their default efforts. The Fill repair rate is assumed at 25%.

| # | Model @ pin (route) | Precision | Reasoning | Battery | Calls | Est. USD | Purpose |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R01 | ministral-3b-2512 @ `mistral/zdr` | undisclosed | none (no mode) | B | 484 | 0.021 | Only doc 44 model with a first-party host; pairs with doc 44's local Q4_K_M (its `pick-hard` arm needs a local run first) |
| R02 | Qwen3-4B-Instruct-2507 @ `nscale` (HF router) | undisclosed | none (no mode) | B | 484 | 0.002 | Doc 47's best new T1 candidate; covered by free HF credits |
| R03 | gpt-oss-20b @ `coreweave/fp4` | fp4, native | low | B | 484 | 0.027 | Same numerics as a local MXFP4 GGUF: isolates engine, template, grammar |
| R04 | gpt-oss-20b @ `deepinfra/bf16` | bf16 | low | B | 484 | 0.028 | Same-weights second host |
| R05 | gemma-4-26b-a4b-it @ `coreweave/bf16` | bf16 | none | U | 1,201 | 0.051 | Upper bound for doc 47's offload candidate; uplift arm |
| R06 | gemma-4-26b-a4b-it @ `deepinfra/fp8` | fp8 | none | B | 484 | 0.018 | fp8 rung and second host |
| R07 | qwen3.6-35b-a3b @ `akashml/fp8` | fp8 | none | U | 1,201 | 0.074 | Upper bound for the second offload candidate; uplift arm |
| R08 | qwen3.6-35b-a3b @ `parasail/fp8` | fp8 | none | B | 484 | 0.043 | Same-precision replicate of R07 |
| R09 | qwen3-30b-a3b-instruct-2507 @ `nebius/fp8` | fp8 | none (no mode) | U | 1,201 | 0.051 | Screening before a local offload download |
| R10 | gemma-4-31b-it @ `deepinfra/turbo` | fp4 | none | L | 216 | 0.011 | Precision ladder, fp4 |
| R11 | gemma-4-31b-it @ `parasail/fp8` | fp8 | none | L | 216 | 0.018 | Precision ladder, fp8 |
| R12 | gpt-6-luna @ `azure` | n/a | none | U | 1,201 | 0.059 | Doc 40's cheap tier with the harness |
| R13 | deepseek-v4.1-flash @ `deepinfra/fp8` | fp8 | none | U | 1,201 | 0.072 | Budget MoE on a ZDR host with schemas (promo price) |
| R14 | mistral-small-2603 @ `mistral/zdr` | undisclosed | none | U | 1,201 | 0.083 | Weak cheap EU generalist |
| R15 | gpt-oss-120b @ `deepinfra/bf16` | bf16 | low | U | 1,201 | 0.083 | Price floor |
| R16 | qwen3.5-9b @ `deepinfra/bf16` | bf16 | none | U | 1,201 | 0.046 | Cloud copy of doc 14's T2a |
| R17 | gemma-4-31b-it @ `crusoe/bf16` | bf16 | none | U | 1,201 | 0.071 | Cheap dense model; bf16 rung of the ladder |
| R18 | gemini-3.1-flash-lite @ `google-vertex/global` | n/a | minimal | U | 1,201 | 0.211 | Google's cheapest stable model |
| R19 | glm-5.3-flash @ `deepinfra/fp4` | fp4 | low (forced) | B | 484 | 0.115 | COMPOSE and translation candidate (promo price) |
| R20 | claude-sonnet-5 @ `google-vertex/global` | n/a | bare: default, then none; full: none | F | 849 | 2.222 | Frontier-bare reference; writer reference |
| R21 | gpt-6-sol @ `azure` | n/a | bare: default, then none; full: none | F | 849 | 1.718 | Second frontier reference |
| R22 | glm-5.3 @ `morph/fp8` | fp8 | low (forced) | W | 60 | 0.064 | Writer probe (promo price) |
| R23 | qwen3.8-27b @ `deepinfra/bf16` | bf16 | none | W | 60 | 0.009 | Writer probe (promo price) |
| O1 | claude-opus-5.5 @ `google-vertex/global` | n/a | bare: default, then low; full: low | F | 849 | 7.859 | Optional third frontier reference |
| O2 | kimi-k3 @ `morph/fp8` | fp8 | low | W | 60 | 0.134 | Optional writer reference (promo price) |
| O3 | muse-glimmer-30b @ `deepinfra/bf16` | bf16 | low (mandatory) | W | 60 | 0.030 | Blocked on the owner's Usage Policy decision |
| O4 | granite-4.2-3b @ `deepinfra` (HF router) | undisclosed | none | B | 484 | 0.008 | Only if the preflight shows the schema is enforced |
| O5 | minimax-m3 @ `together` | undisclosed | none | B | 484 | 0.075 | Optional: best abstention among cheap models |
| O6 | nemotron-3.5-lightning @ `coreweave/bf16` | bf16 | none | B | 484 | 0.016 | Optional (added in review): cheapest 3B-active MoE with two same-precision ZDR hosts (replicate `deepinfra/bf16`, $0.018) |
| O7 | ternary-bonsai-2-27b @ `darkbloom/int4` | int4 (label; ternary weights [U]) | none (verified per call; default `xhigh`) | B | 484 | 0.021 | Optional (owner question, doc 47 §2.7; §6.6): hosted screening with thinking off; **not ZDR**, synthetic suites only |
| O8 | qwen3.8-27b @ `darkbloom/fp4` | fp4 | none | B | 484 | 0.045 | Optional, only with O7 (§6.6): same host and same base model, so an O7–O8 gap is not a host effect; **not ZDR** |

Batteries are defined in §1.2. R20 and R21 split into bare at the default effort ($1.60 and $1.10), bare at the lowest effort ($0.26 each)
and full at the lowest effort ($0.37 each).

### 6.3 Budget [I]

| Item | Estimate (USD) |
| --- | --- |
| Stage 2 (R01–R11) | 0.344 |
| Stage 3a (R12–R19) | 0.738 |
| Stage 3b (R20–R21) | 3.941 |
| Stage 3c (R22–R23) | 0.073 |
| Preflights (92 calls) | 0.054 |
| Grading: API double-grade sample (390 of 2,600 rows at about 900 input and 200 output tokens on Sonnet 5, thinking off) | 1.482 |
| **Core total** (17,648 run calls) | **6.632** |
| Sum of stage caps | 10.25 |
| Credits to buy once / key credit limit | 15.00 (+0.83 card fee) / 12.00 |
| Optional O1–O8 | 8.187 (O1 alone 7.859; O7 and O8 together 0.066, §6.6) |

- **The biggest uncertainty is hidden reasoning.** If Sonnet 5's default effort spends 1,500 reasoning tokens per call instead of 480, its
  bare-default arm costs about $4.46 and stage 3b would pass its $5 cap: the run stops `BudgetLimited` and resumes after the owner raises
  the cap. The cheap arms are insensitive: tripling GLM-5.3-Flash's reasoning (800 to 2,400 tokens a call) adds about $0.19 to R19, or
  $0.30 counting R22's GLM-5.3 as well.
- **The tool's own guards** (built, mock-tested): a worst-case reservation per attempt (every UTF-8 byte counted as a token, × 1.3,
  plus the output cap) must fit under the cap before the call leaves; costs settle at the higher of the provider's `usage.cost` and the
  cost at the flagged prices; failed attempts that may have been billed are charged their reservation; `--key-check` refuses a key
  whose remaining credit limit exceeds `--max-usd` + `--key-margin-usd` (default $1); a cost above its own worst case stops the run
  (`CostAnomaly`). OpenRouter's card fee is outside the cap. With the single $12 key limit of stage 0, `--key-check` refuses every stage
  (the largest cap is $5), so the command templates leave it off; to use it, edit the key's limit before each stage so that what
  remains is at most that stage's cap plus the margin.
- **Time** [I]: 17,648 sequential calls at about 1–3 s each is roughly 5–15 hours of wall time, split into resumable sessions; the frontier
  arms at default effort are the slowest.

### 6.4 Order and stop rules [I]

- Cheapest first, so pipeline bugs cost cents: preflight → R02 → the rest of stage 2 → 3a → 3c → 3b.
- The canary judges the first 20 calls of every (model, arm): it aborts on more than 20% non-conformant answers in a schema arm, more
  than 10% errors, a cost per call over twice the estimate, or any served-provider mismatch.
- Retry only 408, 429 and 5xx (exponential backoff with full jitter, honouring `Retry-After`); a 402 is out of budget; any other 4xx is a
  configuration fault and stops the arm.
- In round 1, `:free` endpoints serve only as plumbing smoke tests: precision unknown, schemas often missing, 20 requests a minute.
  Round 0 (§6.0) uses them for zero-spend screening, never for qualification.

### 6.5 What result would change a recommendation [I]

- **Local → cloud for a step kind**: a same-weights host pair beats the local build by at least 10 points on pass^3, the two hosts agree,
  and a Q8/bf16 GGUF on the same local engine closes the gap (so quantisation, not the engine, is the cause). Then the Model Manager's
  badge text for that build names the quant loss, and a larger quant becomes the recommended download where memory allows.
- **A cheap cloud model becomes a preset**: it passes the substitution test against both frontier references on a step kind, with a
  CPCD ratio of at least 10 and a false-admit rate no higher than the frontier-bare arm's.
- **An offload download is dropped**: its bf16/fp8 cloud copy misses whole-record Fill pass^3 ≥ 0.8 (doc 47 §6.3 item 3).
- **Precision matters**: the fp4 rung of the ladder trails the fp8 and bf16 rungs by at least 10 points on `pick-hard` or Fill with both
  of those agreeing; then precision tags become mandatory in cloud presets.

### 6.6 Optional: Bonsai 2 27B through OpenRouter (O7, O8)

Added 2026-09-27 for the owner's question "What about Bonsai 2 27B?" (doc 47 §2.7, whose verdict is "watch, not test-now" because
only PrismML's llama.cpp fork runs the model's packings, and on the reference GPU the fork processed prompts at about 16 tokens/s).
A hosted copy answers doc 47's cheapest "down to skip" questions in minutes and for cents, without the fork. **Like the rest of §6,
it is deferred until doc 49** (owner decision, 2026-09-27), and it is optional.

**What OpenRouter serves** [V, keyless reads of `GET /api/v1/models` at 18:06 UTC and of the model's `/endpoints` list at 18:06 and
18:23 UTC on 2026-09-27]:

| Fact | Value |
| --- | --- |
| Model id / canonical slug | `prism-ml/ternary-bonsai-2-27b` / `prism-ml/ternary-bonsai-2-27b-20260918` (listed 2026-09-18); `hugging_face_id` `prism-ml/Ternary-Bonsai-2-27B-gguf`; tokenizer "Qwen"; text and image in, text out |
| Endpoints | **One**: Darkbloom, tag `darkbloom/int4`, quantization `int4`; context 262,144; max output 32,768; status 0; 1-day uptime 99.97% |
| Price | $0.075 in / $0.50 out per MTok, discount 0 (no promotion); no cache price listed |
| Structured output | The endpoint lists `response_format` and `structured_outputs` (also `tools`, `tool_choice`, `seed`, `top_k`, the three penalties, `logprobs`). Enforcement is **[U]** until the preflight sends a real strict-schema request (§2.3: flags were wrong in at least six cases) |
| Reasoning | Optional (`mandatory: false`) but on by default (`default_enabled: true`); `supported_efforts` `xhigh` and `medium`, default `xhigh`. OpenRouter's listed defaults: temperature 1, top_p 0.95, top_k 20 |
| Privacy | **Not on the ZDR list** (0 Darkbloom entries among 920). `/api/v1/providers` lists no headquarters or datacenter. Darkbloom's privacy policy (Eigen Labs, updated 2026-08-28): its coordinator processes request payloads in plaintext transiently; content goes to the provider device selected to serve the request (the network's provider machines are attested Macs); the coordinator is designed not to log prompt content; the policy grants no right to train on content; content "may be retained for shorter operational periods" |
| Same-base comparator | `qwen/qwen3.8-27b` @ `darkbloom/fp4`: $0.069 / $2.20, discount 0, `structured_outputs` listed, max output 32,768, 1-day uptime 99.50%, not ZDR. The same model also runs at `deepinfra/bf16` (R23's pin, ZDR) |

**What is not known** [U]: which artifact `int4` names (the packings doc 47 §2.7 found are ternary GGUFs, an upstream-shaped Q2_0 and
an MLX 2-bit build, none labelled int4), and which runtime serves it. So O7 measures "Bonsai 2 as served by Darkbloom", not the
released GGUF, and cannot qualify anything. OpenRouter's supported efforts (`xhigh`, `medium`) differ from doc 47's reading of the
chat template (`xhigh`, `medium`, `low`); whether a reasoning-off request is honoured is exactly what the per-call leak check tests.

**Runs** (battery B at τ = 1.3, reasoning off; §6.2 rows):

- **O7** Bonsai 2 27B @ `darkbloom/int4`: $0.021. **O8** Qwen3.8-27B @ `darkbloom/fp4`: $0.045, run only with O7. Same host and the
  base model Bonsai 2 was derived from, both near 4 bits by label, so a gap between them is not a host or serving-stack effect (§4.3
  needs two hosts to blame precision; here the question is the model, not the precision). Together $0.066, charged to stage 3a's
  ledger (its cap of $1.50 covers 3a's $0.738 plus these), run after 3a.
- **Controls as in §4.2**, with two exceptions forced by the only endpoint: `zdr: false`, and `data_collection: "deny"` kept unless the
  preflight shows it excludes Darkbloom, in which case the owner decides whether to send `allow` for these synthetic suites. Account-wide
  ZDR enforcement (stage 0) blocks both runs, so the owner lifts it for this session only and restores it afterwards. Only the
  repository's synthetic suites are sent, as for DeepSeek's first-party API (§2.1); never user content.
- **Sampler and thinking pinned** as for every arm (presence penalty 0; doc 46 §2.2); the card's non-thinking values include a
  presence penalty of 1.5 (doc 47 §2.7), which this plan does not use. A call that returns reasoning tokens or thinking text stops the
  run (`ReasoningLeak`, §4.2 item 4); with the per-attempt reservation (§6.3), that bounds a leak's cost to a few calls.

**What would change doc 47's verdict** [I; doc 47 §2.7 items 1–3]:

- **Down to "skip"**: with thinking off O7 loops or runs to its cap, is non-conformant on the schema canary, leaks reasoning despite
  the off switch, or trails O8 by at least 10 points of pass^3 on `pick`, `pick-hard` or Fill.
- **Worth doc 47's local paired probe**: O7 is level with or ahead of O8 on every code-scored suite with thinking off and no leak.
  Even then nothing is recommended: the fork-only packings fail D022's rule that the Model Manager refuses GGUFs its pinned runtime
  cannot run (D022 amendment note, owner decision of 2026-09-27), so Bonsai 2 stays bring-your-own until mainline supports it.

## 7. Implications for the product

### 7.1 D021: the provider layer [I]

- **The OpenAI-compatible seam is enough to reach every provider in §2** (OpenRouter, the HF router, Mistral, Groq, Cerebras, Scaleway,
  DeepInfra direct and local servers), but an aggregator needs more than a model id. The adapter should carry a **provider route**
  (endpoint tag, precision, `allow_fallbacks: false`, `require_parameters: true`) and, for user content, send `zdr: true` and
  `data_collection: "deny"` by default. The run panel and each decision's inspector show which host served the call (the glass-box
  rule), because an aggregator forwards data beyond "the model provider the user configured" (AGENTS.md).
- **The capability probe tests behaviour, not flags**: one real strict-schema request per (endpoint, model, route, precision, reasoning
  setting), a reasoning-off check, and the served provider. Flags were wrong in at least six cases (§2.3).
- **Reasoning is always explicit.** Defaults vary from off to `max` (GLM-5.3-Flash `max`, Qwen3.8-27B `xhigh`, DeepSeek V4.1 Flash
  `high`, Sonnet 5 `high`, GPT-6 `medium`, Gemini 3.1 Flash-Lite `minimal`, Gemma off), mandatory models reject `none`, and reasoning
  tokens are billed as output. The adapter sends the setting on every call and the ledger records reasoning tokens (D026).
- **Schemas need a per-provider normaliser** (strict-mode rules, stripped keywords validated in code) and Pick keeps flat letter enums,
  which every dialect accepts (doc 40 R5).
- **GPT-6 on Chat Completions supports function calling only at effort `none`**; Plotroom's PICK and FILL use `response_format`, not
  tools, so this does not bite, but the pinned `rig` version's Responses API support should be checked for tool-using chat modes.
- **Usage accounting:** OpenRouter returns `usage.cost`, cached, cache-write and reasoning token counts on every response, which feeds
  the D026 ledger directly; HTTP 402 from a key limit maps to `BudgetLimited`; an error object inside an HTTP 200 is an error.

### 7.2 D023: recommended cloud setups per budget (candidates) [I]

These are hypotheses for round 1 to confirm or reject; D023 decision 2 keeps every named model a candidate until our instruments
qualify it.

| Budget | PICK / FILL | EXPLAIN | COMPOSE / DRAFT | Translation | Evidence today |
| --- | --- | --- | --- | --- | --- |
| $0 | Local T1 (doc 46's default) | Local, with the card | Cards and templates, or a visible cloud button | — | Docs 44 and 46 |
| Pennies (doc 40 models a whole campaign at $0.15 on gpt-6-luna) | gpt-6-luna at `none`, or an open model on a ZDR host (Gemma 4 26B/31B, Qwen3.5-9B, DeepSeek V4.1 Flash) | Same | Same model at `low` | Gemini 3.1 Flash-Lite or GLM-5.3-Flash in Economy | Round 1 (R05, R12–R18) |
| Cheap writer | As above | As above | GLM-5.3 on a pinned ZDR host, or Qwen3.8-27B | Hy-MT2 once a translation suite exists | Round 1 writer probes plus a DRAFT suite |
| Quality (doc 40 G rows: $2.3–3.5 per campaign) | Sonnet 5 thinking off, or gpt-6-sol `none` | Sonnet 5 | Sonnet 5 or gpt-6-sol at `low` | Same, plus native review | Doc 40 presets |
| EU processing preferred | Mistral Small 4 on `mistral/eu`; Gemma on Scaleway | Same | Sonnet 5 on Vertex `europe` (+10%) | — | §2.5 |

- Recommend **endpoints, not just models**: the same weights differ 3–10x in price across hosts (DeepSeek V4.1 Flash input $0.035–0.375
  across 27 OpenRouter endpoints from 26 providers on the review re-read) and differ in precision, schema support and retention.
- Never recommend free or data-for-discount tiers for user content; show a promotional price with its list price and date; show the
  host's country.

### 7.3 Doc 40: cost preview and the cost model [I on V]

- **Correct §2.1**: Gemini 3.5 Flash-Lite *does* cache on the paid tier ($0.03 per MTok plus $1.00 per MTok-hour storage; batch $0.02).
  "Not available" is the free tier's column (pricing page updated 2026-09-24, re-read while writing this doc). `cost_model.py` models it
  with no caching.
- **Add rows** to `cost_model.py` and `cost-model.csv`: gemini-3.1-flash-lite ($0.25/$1.50, cache $0.025), and hosted open-weight rows
  (gpt-oss-120b $0.037/$0.17; Gemma 4 26B-A4B $0.10/$0.30; Qwen3.5-9B $0.10/$0.15; DeepSeek V4.1 Flash on DeepInfra $0.14/$0.42 promo;
  GLM-5.3-Flash $0.075/$0.25 promo with forced thinking). In strategy D, replace the Haiku 4.5 router, which retires no sooner than
  2026-10-15 (doc 40 §6 already models Sonnet 5 with thinking off as slightly cheaper), and the Gemini 3.5 Flash-Lite router with the
  cheaper 3.1 Flash-Lite.
- **Price rows keyed by endpoint**: doc 40 R1's `[[price]]` table gains the route (aggregator, endpoint tag, precision), a `promo` flag
  with the list price, and the time of day for peak-priced providers (the DeepSeek rows on 2026-09-27 read off-peak because it was a
  Sunday).
- **Economy mode (R12)** must not assume "batch = 50% of the same artifact" on aggregators: DeepInfra-served `:batch` is 0.8x and GLM
  batches run at fp4.
- **The plan card** shows the serving host and, where a price is a promotion, its end date or "promotion, no end date".
- **E12's inputs** come partly from round 1: reasoning tokens per shape at each effort, first-pass admit and repair rates, τ per model.
- **Discrepancy to settle**: Opus 5.5's default effort (OpenRouter `high`, doc 40 `medium`), and OpenRouter listing `temperature` for
  Opus 5.5 where doc 40 says it returns 400.

### 7.4 Design-gap candidates (to be filed in `docs/design-gap-requests/`) [I]

1. **Cloud artifact identity.** D021, D023 and doc 40 R1 key prices and qualification by (provider, model); through an aggregator the
   identity is (aggregator, model, endpoint tag, precision, reasoning setting, date). Doc 14 §5's exact-artifact rule degrades to that
   tuple for cloud rows, and badges need periodic re-probing.
2. **Aggregators and the outbound-traffic invariant.** With OpenRouter configured, requests reach hosts the user did not name. Proposed:
   ZDR and no-data-collection by default, the host shown per call, and a per-key allow-list of hosts.
3. **Probe by behaviour.** D021 decision 4's capability probe must send a real strict-schema request, a reasoning-off request and
   check the served provider (§2.3).
4. **"Check this endpoint".** The Model Manager's "check this model on my machine" (doc 44 §5.3) has a cloud counterpart: the same suites
   against a user's endpoint under a cost cap shown in advance (round 1's battery B costs cents on cheap endpoints).
5. **Instrument numbering.** 48-U needs an E-number without colliding with doc 29's E7–E14 (DG005).

## Open questions

1. Does OpenRouter's `provider.only` accept precision-suffixed tags such as `deepinfra/bf16`? The docs say "use the full slug including
   the suffix" to target a variant or region (examples `google-vertex/us-east5`, `deepinfra/turbo`), and the endpoint lists give
   precision suffixes as tags of the same form, so it probably does; the preflight confirms it, and the fallback is the provider slug
   plus `quantizations` [U].
2. Does OpenRouter return the served provider in the response body? The runner reads an undocumented top-level `provider` field and marks
   records `provider_unverified` when it is missing [U].
3. Are schemas enforced by grammar at nscale, Scaleway and Featherless when reached through the HF router [U]?
4. How many reasoning tokens does each shape use at each effort on each model (doc 40 open question 1)? Frontier estimates swing 4–12x on it.
5. What is τ, the cloud-to-local token ratio, per model? Claude 4.7+ tokenizers produce about 30% more tokens than earlier ones (doc 40).
6. The owner's first question: does any hosted fp8/bf16 copy beat the local Q4 build by 10 points or more on any step kind (round 1)?
7. How much of the harness gain comes from menus (code-owned vocabulary), cards, schema enforcement and repair, per model (round 1)?
8. A translation and non-English DRAFT instrument with Czech, Polish and Russian items and native reviewers is missing (doc 14 §9 item 4);
   Hy-MT2, Bielik and the writer choice wait on it.
9. Owner decision: may Muse-Glimmer-30B be tested or recommended under its Usage Policy's "military, warfare" clause (doc 14 TL;DR
   and open questions)?
10. Should Plotroom ship aggregators (OpenRouter, the HF router) as first-class providers, given design-gap candidate 2 (§7.4)?
11. Re-run cadence: the cost of reaching a fixed benchmark level falls about 5–10x a year (arXiv 2511.23455) and several candidates are
    days old (gpt-6-luna 2026-09-22, MiMo-V2.6-Flash 2026-09-21). Proposed: a quarterly sweep plus a monthly 20-item canary per endpoint.

## Sources

All pages read on 2026-09-27 unless stated. Raw snapshots of the public APIs were kept with the research notes, outside the repository.

**Aggregators and their APIs (keyless).** <https://openrouter.ai/api/v1/models> (fetched 14:54 UTC) ·
`https://openrouter.ai/api/v1/models/<author>/<slug>/endpoints` for every model named in §3 and §6 (the Gemma 4 26B-A4B and gpt-oss-20b
lists were re-read while writing) · <https://openrouter.ai/api/v1/endpoints/zdr> · <https://openrouter.ai/api/v1/providers> ·
<https://openrouter.ai/docs/guides/routing/provider-selection> · <https://openrouter.ai/docs/features/provider-routing> ·
<https://openrouter.ai/docs/features/zdr> · <https://openrouter.ai/docs/features/privacy-and-logging> ·
<https://openrouter.ai/docs/features/structured-outputs> · <https://openrouter.ai/docs/use-cases/reasoning-tokens> ·
<https://openrouter.ai/docs/use-cases/usage-accounting> · <https://openrouter.ai/docs/api-reference/errors> ·
<https://openrouter.ai/docs/api-reference/limits> · <https://openrouter.ai/docs/faq> · <https://openrouter.ai/docs/batch-quickstart> ·
<https://openrouter.ai/blog/announcements/auto-exacto/> (2026-03-12) ·
<https://openrouter.ai/announcements/response-healing-reduce-json-defects-by-80percent> ·
<https://router.huggingface.co/v1/models> (the Qwen3-4B-Instruct-2507 entry re-read while writing) ·
<https://huggingface.co/docs/inference-providers/pricing> · `https://huggingface.co/api/models/<repo>?expand[]=inferenceProviderMapping`.
Added for §6.6 (read 2026-09-27, 18:06–18:23 UTC): <https://openrouter.ai/api/v1/models> (the `prism-ml/ternary-bonsai-2-27b` entry) ·
<https://openrouter.ai/api/v1/models/prism-ml/ternary-bonsai-2-27b/endpoints> · <https://openrouter.ai/api/v1/models/qwen/qwen3.8-27b/endpoints>
(the `darkbloom/fp4` row) · <https://openrouter.ai/api/v1/endpoints/zdr> and <https://openrouter.ai/api/v1/providers> (Darkbloom) ·
<https://www.darkbloom.dev/privacy> (updated 2026-08-28).
Added for §6.0 (read 2026-09-27): <https://openrouter.ai/api/v1/models> (20:06 UTC; the 17 `:free` text models) ·
`https://openrouter.ai/api/v1/models/<author>/<slug>:free/endpoints` for 13 of them (20:06 UTC) · <https://openrouter.ai/api/v1/endpoints/zdr>
(20:06 UTC) · `https://openrouter.ai/api/frontend/v1/all-providers` (undocumented; the data behind the provider-logging docs table;
20:13 UTC) · <https://openrouter.ai/docs/api-reference/limits> · <https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key> ·
<https://openrouter.ai/docs/guides/routing/model-variants/free> · <https://openrouter.ai/docs/guides/routing/provider-selection> ·
<https://openrouter.ai/docs/guides/features/zdr> · <https://openrouter.ai/docs/guides/privacy/provider-logging> ·
<https://openrouter.ai/docs/guides/features/guardrails> · OpenRouter help-centre articles, through the public Help Center API:
<https://openrouter.zendesk.com/hc/en-us/articles/51690904755227> (free endpoints and privacy toggles; updated 2026-09-23),
<https://openrouter.zendesk.com/hc/en-us/articles/51679572756123> (`openrouter/auto:free`),
<https://openrouter.zendesk.com/hc/en-us/articles/51678714631323> (file and PDF charges),
<https://openrouter.zendesk.com/hc/en-us/articles/51690568268059> (capping spend) · free-variant churn, a third-party tracker (not
OpenRouter): <https://github.com/cyclez2000/openrouter-free-models/issues/77>.

**Hosts.** DeepInfra: <https://api.deepinfra.com/models/list>, <https://deepinfra.com/pricing>, <https://docs.deepinfra.com/account/data-privacy>.
Mistral: <https://mistral.ai/pricing/api>, <https://mistral.ai/pricing>, <https://docs.mistral.ai/studio-api/conversations/structured-output/custom>,
<https://help.mistral.ai/en/articles/455207-can-i-opt-out-of-my-input-or-output-data-being-used-for-training>,
<https://help.mistral.ai/en/articles/347612-can-i-activate-zero-data-retention-zdr>. Groq: <https://console.groq.com/docs/models>,
<https://console.groq.com/docs/structured-outputs>, <https://console.groq.com/docs/your-data>, <https://console.groq.com/docs/rate-limits>,
<https://console.groq.com/docs/batch>. Cerebras: <https://inference-docs.cerebras.ai/models/openai-oss>,
<https://inference-docs.cerebras.ai/support/rate-limits>, <https://inference-docs.cerebras.ai/capabilities/structured-outputs>,
<https://support.cerebras.net/articles/1811589793-does-cerebras-retain-my-data>. Fireworks: <https://docs.fireworks.ai/serverless/pricing>,
<https://docs.fireworks.ai/guides/security_compliance/data_handling>, <https://docs.fireworks.ai/structured-responses/structured-output-grammar-based>.
Together: <https://www.together.ai/pricing>, <https://docs.together.ai/docs/privacy-and-security>. Nebius:
<https://docs.tokenfactory.nebius.com/legal/legal-quick-guide>. Scaleway: <https://www.scaleway.com/en/pricing/model-as-a-service/> and the
`scaleway/docs-content` pages on data privacy, supported models and structured outputs. Featherless: <https://featherless.ai/pricing>,
<https://featherless.ai/docs/plans>, <https://api.featherless.ai/v1/models>. nscale:
<https://www.nscale.com/blog/introducing-nscale-serverless-inference-scalable-ai-without-infrastructure-hassles>. Public AI:
<https://publicai.co/tc>. RunPod: <https://www.runpod.io/pricing> (updated 2026-09-13), <https://docs.runpod.io/references/security-and-compliance>.
OVHcloud (added in review): <https://www.ovhcloud.com/en/public-cloud/ai-endpoints/> and its models on <https://router.huggingface.co/v1/models>.

**First-party model vendors.** OpenAI: <https://developers.openai.com/api/docs/pricing>, `…/docs/models/gpt-6-luna`, `…/docs/models/gpt-6-sol`,
`…/docs/guides/your-data`, `…/docs/guides/flex-processing`. Anthropic: <https://platform.claude.com/docs/en/about-claude/pricing>,
`…/about-claude/models/overview`, `…/build-with-claude/structured-outputs`, `…/build-with-claude/prompt-caching`,
`…/manage-claude/api-and-data-retention`, `…/manage-claude/data-residency`. Google: <https://ai.google.dev/gemini-api/docs/pricing>
(updated 2026-09-24; re-read while writing), <https://ai.google.dev/gemini-api/terms>, <https://ai.google.dev/gemini-api/docs/structured-output>,
<https://ai.google.dev/gemini-api/docs/caching>, <https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api>. DeepSeek:
<https://api-docs.deepseek.com/quick_start/pricing>, <https://api-docs.deepseek.com/guides/json_mode>,
<https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html>. Z.ai: <https://docs.z.ai/guides/overview/pricing>,
<https://docs.z.ai/guides/capabilities/struct-output>, <https://docs.z.ai/guides/capabilities/thinking-mode>,
<https://docs.z.ai/legal-agreement/privacy-policy>. Moonshot: <https://platform.kimi.ai/docs/pricing/chat>. Alibaba:
<https://www.alibabacloud.com/help/en/model-studio/model-pricing>, `…/qwen-structured-output`, `…/context-cache`. xAI:
<https://docs.x.ai/developers/pricing>, <https://docs.x.ai/docs/guides/structured-outputs>. AWS:
<https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-2-lite.html>. Cohere: <https://docs.cohere.com/docs/structured-outputs>,
<https://cohere.com/data-usage-policy>. Meta: <https://dev.meta.ai/docs/pricing-rate-limits>. Model cards and licences on Hugging Face
(`openai/gpt-oss-20b`, `tencent/Hy-MT2-7B`, `meta-models/Muse-Glimmer-30B-GGUF` USAGE_POLICY.md, `zai-org/GLM-5.3`;
added in review: `https://huggingface.co/api/models/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16` for its licence and languages).

**Boards and evidence.** <https://artificialanalysis.ai/leaderboards/models> · <https://artificialanalysis.ai/methodology/intelligence-benchmarking> ·
<https://artificialanalysis.ai/articles/endpoint-accuracy-index> (2026-08-04) · <https://eqbench.com/creative_writing.js?v=1.0.91> ·
EuroEval leaderboard assets (Czech, Polish, European) · <https://raw.githubusercontent.com/vectara/hallucination-leaderboard/main/README.md>
(updated 2026-09-22) · <https://gorilla.cs.berkeley.edu/leaderboard.html> · <https://simonwillison.net/2025/Aug/15/inconsistent-performance/> ·
<https://raw.githubusercontent.com/MoonshotAI/K2-Vendor-Verifier/main/README.md> · <https://vllm.ai/blog/2025-10-28-kimi-k2-accuracy> ·
<https://www.kimi.ai/blog/kimi-vendor-verifier> · <https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues> ·
<https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/> · <https://unsloth.ai/docs/models/gemma-4/qat> ·
<https://unsloth.ai/docs/models/qwen3.5/gguf-benchmarks> · <https://localbench.substack.com/p/qwen-36-35b-a3b-gguf-quality-benchmark> ·
<https://localbench.substack.com/p/kv-cache-quantization-benchmark> · <https://github.com/lmstudio-ai/lmstudio-bug-tracker/issues/1555>.
Papers (arXiv): 2410.20247 (Model Equality Testing), 2411.02355 (quantisation recovery), 2601.14277 (llama.cpp quants), 2409.11055
(small-model quantisation), 2406.12045 (τ-bench, pass^k), 2511.09030 (MAKER), 2407.21787 (Large Language Monkeys), 2510.11977 (HAL),
2505.11423 (When Thinking Fails), 2605.26128 (The Constraint Tax), 2511.23455 (The Price of Progress). IJAI 13(1), June 2026 (quantised
1–4B models).

**Repository.** Docs 14 (§3, §5, §6, §9), 21 (§3, §12), 25 (§11), 29 (§7), 30 (§3), 40 (§2, §4, §5, §7), 44 (§2, §5, §6), 46 (§2),
47 (§1–§3, §2.7, §6); D021, D022, D023, D026; DG005; `tools/local-qual/README.md`; `tools/cost-model/cost_model.py`;
`docs/research/data/cost-model.csv`, `local-qualification.csv`, `runtime-quant-comparison.csv`, `slm-candidates.csv`.

## Verification notes

### 2026-09-27, author checks at write-up

- **Rows.** Every provider row in `cloud-candidates.csv` and §2–§3 comes from a fact-check pass that re-read each primary page or API
  on 2026-09-27 and recorded corrections (uptime drift, promotions, precision, retention wording). While writing, the OpenRouter
  endpoint lists for Gemma 4 26B-A4B and gpt-oss-20b, the HF router entry for Qwen3-4B-Instruct-2507 and the Gemini pricing page were
  re-read: prices and precisions matched; uptimes had drifted by up to 0.3 points (NextBit 98.04%, Parasail 99.69%), which the tables
  round over.
- **Arithmetic.** §1.2's battery totals were summed from §1.2's per-suite means; §1.3's closed forms, every estimate in §6.2 and §6.3 and
  every `battery_cost_usd` in the CSV come from one small script over those means, the stated τ, reasoning assumptions and the pinned
  prices; battery B at τ = 1.0 on gpt-6-luna reproduces an independent hand calculation's $0.020.
- **Tool claims.** The cloud backend's behaviour in §4.2 and §6.3 (refusals, caps, reservations, retries, canary, schema conformance,
  reasoning-leak stop, redaction) is taken from its README and its mock-server test evidence (40 tests, 26 injected faults all caught);
  it has not met a real endpoint.
- **Not verified.** Anything a live call would show: served-provider fields, grammar enforcement on HF-routed hosts, reasoning-token
  counts, τ, and whether precision-suffixed tags work in `provider.only`. Artificial Analysis and EQ-Bench figures are the boards'
  own; they were parsed from the boards' published data, not re-derived.
- **Public rule.** No private or unpublished project, local path or user name appears in this doc or the CSV.

### 2026-09-27, independent review

Method: the keyless OpenRouter APIs (`/api/v1/models`, the `/endpoints` list of 33 models, `/endpoints/zdr` and `/providers`) and the
HF router's `/v1/models` were downloaded again and compared row by row with the CSV; policy and pricing pages were re-read; the budget
was recomputed from the per-suite means. No account was created and no keyed or paid API was called.

**Spot-checks against live pages** (all read 2026-09-27):

| Claim | Source | Result |
| --- | --- | --- |
| Pinned prices of R01–R23 and O1–O5 (for example gpt-oss-20b `coreweave/fp4` $0.03/$0.13, Gemma 26B `coreweave/bf16` $0.10/$0.30, Qwen3.6 `akashml/fp8` $0.10/$0.90, DeepSeek V4.1 Flash `deepinfra/fp8` $0.14/$0.42 with discount 0.30, GLM-5.3-Flash $0.075/$0.25 with 0.50, Morph GLM-5.3 $0.3622/$1.138 with 0.6956, Kimi K3 $0.9875/$5.53 with 0.605, Sonnet 5 on Vertex $2/$10) | `https://openrouter.ai/api/v1/models/<slug>/endpoints` | All match; the promotion list prices follow from the discount field |
| ZDR membership of every pinned endpoint; 920 ZDR entries; plain `mistral`, first-party OpenAI, Anthropic and DeepSeek, and Darkbloom not ZDR | `https://openrouter.ai/api/v1/endpoints/zdr` | Match, with one correction: Gemma 4 31B `deepinfra/turbo` **is** on the list (the CSV said "not checked"; R10's pin sent `zdr: false`) |
| Card fee 5.5% (minimum $0.80), crypto 5%, no inference markup, 1% discount for opting in to logging | <https://openrouter.ai/docs/faq> | Match |
| `:free` limits 20 RPM, 50 a day below $10 of credits bought, 1,000 at $10 or more; per-key limits | <https://openrouter.ai/docs/api-reference/limits> | Match |
| Inverse-square price weighting; `only` with full variant slugs; `zdr`, `data_collection` | <https://openrouter.ai/docs/guides/routing/provider-selection>, <https://openrouter.ai/docs/features/zdr> | Match; ZDR page adds three caveats now in §2.5 |
| Qwen3-4B-Instruct-2507 at nscale $0.01/$0.03, schema flag true; Granite 4.2-3B $0.03/$0.12, flag false; Bielik $0.40/$0.40; Scaleway Gemma $0.285/$0.57, flag false | <https://router.huggingface.co/v1/models> | Match; Qwen3-4B-2507 is still absent from OpenRouter, so the HF account remains the only route for R02 |
| HF credits $0.10/month ("subject to change"), PRO $2, no markup, credits not applied with a custom key | <https://huggingface.co/docs/inference-providers/pricing> | Match |
| DeepInfra: no disk storage, outputs not stored, no training except Google or Anthropic models | <https://docs.deepinfra.com/account/data-privacy> | Match; added its metadata-only logging and the bulk-API exception |
| Groq: nothing retained by default, up to 30 days for troubleshooting or abuse, self-serve ZDR disables batch; gpt-oss-20b $0.075/$0.30 | <https://console.groq.com/docs/your-data>, <https://console.groq.com/docs/models> | Match |
| Together stores prompts by default until an org admin enables ZDR | <https://docs.together.ai/docs/privacy-and-security> | Match; added "may use them for product improvements" and opt-in training sharing |
| Anthropic: no conversation content retained by default except Fable and Mythos | <https://platform.claude.com/docs/en/manage-claude/api-and-data-retention> | Match; added the 30-day figure, the 2-year retention of flagged content and that Google or AWS is the processor on Vertex or Bedrock (the plan's route) |
| Sonnet 5 default effort `high`, Opus 5.5 `medium`, Haiku 4.5 retires no sooner than 2026-10-15 | <https://platform.claude.com/docs/en/about-claude/models/overview> | Match |
| OpenAI: no training on API data, abuse logs up to 30 days, ZDR by prior approval; gpt-6-luna $0.10/$0.50, cache write $0.125 | <https://developers.openai.com/api/docs/guides/your-data>, <https://developers.openai.com/api/docs/pricing> | Match |
| Gemini paid tier not used to improve products, logs kept "for a limited period"; EEA, UK and Switzerland get paid terms on the free tier; 3.5 Flash-Lite paid caching $0.03 plus $1.00 per MTok-hour | <https://ai.google.dev/gemini-api/terms>, <https://ai.google.dev/gemini-api/docs/pricing> (updated 2026-09-24) | Match; confirms §7.3's correction of doc 40 |
| Scaleway ZDR by default, failing or malicious traffic up to two weeks, no training, Paris; Gemma €0.25/€0.50, Qwen3.6 €0.25/€1.50, batch −50%, first 1M tokens free | Scaleway data-privacy page on GitHub, <https://www.scaleway.com/en/pricing/model-as-a-service/> | Match; whether the free 1M is one-off stays [U] |
| Mistral: $0.10/$0.10 (3B), $0.15/$0.60 (Small 4), batch half price, Free plan $10/month with training opt-out; ZDR on request | <https://mistral.ai/pricing/api>, <https://mistral.ai/pricing>, the two help-centre articles | Match; added that ZDR is approved case by case, pay-as-you-go and stateless only |
| Cerebras: retains no prompts or outputs; $0.35/$0.75; trial 5 RPM, 30K uncached TPM, 1M TPD | Cerebras support article, <https://inference-docs.cerebras.ai/models/openai-oss>, rate-limits page | Match; the CSV's mixed-precision note was not re-found on the cited page and is now marked [U] |
| DeepSeek: stored in the PRC, trains unless opted out by email; $0.15/$0.60 off-peak, peak double (01–04 and 06–10 UTC on weekdays) | DeepSeek privacy policy, <https://api-docs.deepseek.com/quick_start/pricing> | Match; the rule comes from its general privacy policy, now stated |
| Nebius stores for speculative decoding without ZDR, in Finland, no training | <https://docs.tokenfactory.nebius.com/legal/legal-quick-guide> | Match; no retention period is stated, now said |
| Fireworks keeps no open-model prompts without opt-in | <https://docs.fireworks.ai/guides/security_compliance/data_handling> | Match; added the Responses API's 30-day default |
| Z.ai stores no API content; Singapore; policy of 2025-09-29 | <https://docs.z.ai/legal-agreement/privacy-policy> | Match |
| RunPod community RTX 4090 $0.34/h, RTX 3090 $0.22/h, L4 $0.44/h; per-second billing | <https://www.runpod.io/pricing> | Match |

**Arithmetic.** The per-suite means in §1.2 agree with the committed `local-qualification.csv` (for example Pick none 219.9, Fill 431.4,
Explain 304.9 input tokens) and, for `pick-hard`, with the Qwen rows of `runtime-quant-comparison.csv` (301.5 and 440.9; 7 output
tokens). Gemma 4 E4B on llama.cpp emits about 16.8 output tokens on `pick-hard`, which would add under $0.01 to any run. Battery B, U,
L and F totals, all 23 core estimates, the three-arm splits of R20, R21 and O1, the stage sums (0.344, 0.738, 3.941, 0.073), the
preflight total (0.054), the grading sample (390 of 2,600 rows, $1.482), the core total ($6.632), 17,648 calls, the 77% frontier share,
the $0.00019 against $0.0055 per-decision comparison, the $4.46 Sonnet sensitivity and all 58 original `battery_cost_usd` values in
the CSV (plus the 4 added rows) were recomputed and match. One figure was wrong: tripling GLM-5.3-Flash's reasoning adds $0.19 to R19 ($0.30 with R22), not $0.27; fixed.

**Nothing is claimed as measured.** Throughput, first-token and uptime figures are the providers', Hugging Face's, OpenRouter's or
Artificial Analysis's own; the tool's guards are mock-tested only, and the doc says so. One CSV phrase ("fastest measured") now names
whose measurement it is.

**Accounts.** OpenRouter alone reaches 22 of the 23 core runs (all but R02) and the stage 4 grading sample; the free Hugging Face
account is needed only for R02 (and optional O4), because Qwen3-4B-Instruct-2507 has no OpenRouter endpoint. That is the minimal set. One inconsistency
was fixed: with the single $12 key limit, the tool's `--key-check` refuses every stage, so §6.3 now says how to use it.

**Drift since write-up** (OpenRouter 1-day uptime, re-read): Groq gpt-oss-20b 96.45% (96.29%), Nebius Qwen3-30B-2507 96.64% (95.74%),
Alibaba Qwen3.5-35B 60.94% (57.85%), Vertex gpt-oss-120b 39.19%, Crusoe Gemma 31B 98.80% (98.86%), Parasail Gemma 31B 98.92%. So the
TL;DR range now reads 98.9–100%. DeepSeek V4.1 Flash now has 27 endpoints (§7.2 updated).

**Added for completeness.** Nemotron 3.5 Lightning 30B-A3B (optional O6 and two CSV rows), Parasail bf16 as the same-precision Gemma
26B replicate (CSV row and §3.4), OVHcloud as a second EU host (§2.1, §2.5, CSV row), the ZDR flex endpoint for Gemini 3.1 Flash-Lite
(§2.4), and cheaper unpinned hosts (§3.5). The CSV now has 65 rows. The core plan and its $6.63 estimate are unchanged; the optional
total is $8.121.

**Hygiene.** No private or unpublished project, local path, user name or e-mail address appears in this doc or the CSV (searched).

### 2026-09-27, owner deferral and the Bonsai 2 27B addendum

- **Deferral.** The owner deferred round 1 until doc 49's local results are in (owner decision, 2026-09-27); the note under Status
  says so. No account was created and no keyed or paid API was called for this addendum.
- **Bonsai 2 27B (§6.6, O7, O8, two CSV rows).** Read keyless from OpenRouter on 2026-09-27: `GET /api/v1/models` at 18:06 UTC (458
  models; the `prism-ml/ternary-bonsai-2-27b` entry with its pricing, supported parameters, default parameters and reasoning block),
  the model's `/endpoints` list at 18:06 and again at 18:23 UTC (one endpoint, `darkbloom/int4`, $0.075/$0.50, discount 0,
  `structured_outputs` listed, 1-day uptime 99.97% both times), Qwen3.8-27B's `/endpoints` list at 18:23 UTC (the `darkbloom/fp4`
  row: $0.069/$2.20, discount 0, `structured_outputs` listed, 99.50%), `/api/v1/endpoints/zdr` (920 entries, no Darkbloom endpoint)
  and `/api/v1/providers` (Darkbloom: no headquarters or datacenter listed). Darkbloom's privacy policy (updated 2026-08-28) was read
  for §6.6's privacy row. The listing date comes from the model's `created` timestamp (2026-09-18 UTC), which matches its canonical
  slug. This matches doc 47 §2.7's note of "one int4 provider, structured outputs".
- **Arithmetic.** O7 = 1.3 × (0.1470 × 0.075 + 0.0110 × 0.50) = $0.0215; O8 = 1.3 × (0.1470 × 0.069 + 0.0110 × 2.20) = $0.0446; both
  with reasoning off, as in §1.3's closed form. The optional total becomes 8.121 + 0.066 = $8.187. The core plan and its $6.63 estimate
  are unchanged; stage 3a's cap ($1.50) covers its core arms ($0.738) plus O7 and O8.
- **Not verified:** which weights or runtime serve `int4`; whether the reasoning-off request is honoured; whether the listed
  structured output is enforced; whether `data_collection: "deny"` still routes to Darkbloom.
- **Residual items for doc 48:** none.
- **Hygiene.** The addendum and the two CSV rows name no private project, local path, user name or e-mail address.
- **Wording (links-and-hygiene pass, 2026-09-27).** The Tooling line and stage 0 in §6.1 said the tool patch waits for "the GPU job";
  both now name what it waits for, doc 49's local measurement run in `tools/local-qual`. No plan, cap or number changed.
- **Owner answer folded (consistency review, 2026-09-27).** §3's Nemotron row said OpenMDW-1.1 as a download default "waits on doc
  47's owner ruling (OWQ-19)"; OWQ-19 is answered (a) and D037 lists not-yet-OSI licences such as OpenMDW as custom-only, so the row
  now says so. O3 stays blocked on this doc's own OQ9 (whether a model whose use policy bans military uses may be tested), which D037
  leaves open. No plan, cap or number changed.

### 2026-09-27, round 0 (free models) addendum

- **Request.** The owner asked for a safe way to test models over OpenRouter, free models first (2026-09-27). §6.0 answers it; round 1
  stays deferred. No account was created, no key was used and no keyed or inference endpoint was called.
- **Reads.** Keyless, on 2026-09-27: `GET /api/v1/models` at 20:06 UTC (458 models, 17 `:free` text models), the `/endpoints` lists
  of 13 of them and `/api/v1/endpoints/zdr` (920 entries; 3 free text endpoints) at 20:06 UTC, and the provider table at 20:13 UTC.
  The limits page and the help-centre article on free endpoints (updated 2026-09-23) were re-read the same evening and match the rules
  in §6.0. An earlier read the same day, through the public Help Center API, supplied the other articles cited.
- **Correction to a CSV row.** The Gemma 4 26B-A4B `:free` row called the route "plumbing smoke tests only" and gave only Google's
  own free-tier terms. OpenRouter's provider table lists Google AI Studio with no training and 55-day retention under Google Cloud
  terms; which policy governs this one endpoint is [U]. The row now says both and names its round-0 runs (Z03, Z09).
- **Arithmetic.** Requests per run are suite sizes at k = 1 (pick 30, `pick-hard` 30, fill 12, explain 10, text 10, knowledge 12),
  minus preflight items reused through `--resume`, plus Fill repairs at §6.2's 25% (ceiling). Core 204 (213 at one repair per item);
  all runs 558 (576). Days assume 40 planned requests a day, one run a day in phases A–C.
- **Tool claims.** The safety design in §6.0 is the scratch patch's free-only layer: its README, its mock-server tests (59 passing)
  and its mutation check (66 injected faults, all caught), with the DPAPI scripts tested on a random dummy key. It has not met
  OpenRouter.
- **Not verified:** everything Z01–Z03 exists to settle (a $0 key limit with free calls, the `model` string of free responses,
  `usage.cost` on free responses, strict-schema routing on Qwen3.8-27B's endpoint, reasoning off on it, `data_collection: "deny"` on
  retain-only endpoints), per-endpoint data policies (the provider table describes providers), and whether failed requests count
  against the daily quota.
- **Hygiene.** §6.0 and the six new CSV rows name no private project, local path, user name or e-mail address. The key path is given
  by its environment variable only.
