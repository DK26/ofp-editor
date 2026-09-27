# D021: Provider layer: own the seam, rent the wires

> **Status:** baseline · **Decided by:** research (docs 10–12, 14, 40) · **Decided:** 2026-09-26 · **Recorded:** 2026-09-27
> **Scope:** how Plotroom talks to model providers and serves its tools to external agents. **Related:** D006, D022, D023, D024, D026.
> **Revisit if:** the adapter's upstream churn costs more than owning the wire code, or a provider feature we need cannot pass through it.

## Context

- `rig` is the most complete Rust LLM stack (MIT): many providers over a few wire grammars, typed tools with generated schemas, a tool
  loop with hooks that can approve, deny or rewrite each call, record/replay cassettes. Its cost is churn: a breaking 0.x release about
  every three weeks, and no provider-neutral effort setting (doc 12 TL;DR).
- `genai` (MIT OR Apache-2.0) has unified reasoning effort and cache control but no agent loop or MCP; no official Anthropic Rust SDK
  existed at research time (doc 12 TL;DR).
- Providers differ in reasoning knobs, forced tool choice and caching rules (doc 14 §7; doc 40 R5, R10).

## Decision

1. **Own the seam.** A Plotroom crate (working name `ofp-agent` in doc 12; a `plotroom-` name per D002) defines the provider-neutral
   types: messages, editor tools, `Effort`, context budget, usage and cost records. Domain crates (formats, mission, campaign) never
   import a provider library.
2. **Rent the wires.** One adapter crate implements the seam over `rig` with an **exact version pin**; hooks gate every editor mutation
   (approval, admission) and rewrite oversized tool results. `genai` is plan B.
3. **Serving tools to external agents** uses the official `rmcp` crate directly (D006, item 4). T2 plugin connectors go through the
   plugin host (D007), not through the provider adapter.
4. Provider rules the seam enforces: no forced tool choice (strict schemas plus validator and repair instead); a capability probe per
   (endpoint, model, version) at setup; pinned model ids in a `models.toml` that can change without a release; a `CachePolicy` per
   provider with wire tests; dated prices as data (doc 14 §7; doc 40 R1, R10; D026).
5. **Context budget without a tokenizer** in v1: a bytes-per-token estimate calibrated per model from provider-reported usage (doc 12).

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| Use `rig` types throughout the codebase | Its churn would ripple into every crate |
| Write every provider client ourselves | Large, repetitive wire work that `rig` already tests |
| `genai` as the primary | No agent loop, no MCP, beta line at research time |
| Depend on `headroom` for context compression | Not on crates.io, heavy native dependencies, panicking code; its ideas are ported instead (doc 12 TL;DR) |

## Consequences

- headroom's ideas become our own code: tools that query instead of dumping, reversible truncation with an `expand_ref` tool, must-keep
  sets, a byte-stable cacheable prefix, tool-call/result atomicity and a "never larger than the original" gate (doc 12 TL;DR).
- The pinned adapter version moves only with a cassette replay across providers.
- Local servers (Ollama, LM Studio, llama-server) are reached through the same seam as OpenAI-compatible endpoints (D022).
- Provider-specific code is documented as onboarding notes for maintainers new to each API (`AGENTS.md` comment rules).

## Sources

Doc 10; doc 11; doc 12 (TL;DR, §1, §3, §5); doc 14 §7; doc 38 §9; doc 40 (R1, R5, R10).

## Amendment notes

### 2026-09-27: cloud-provider consequences from doc 48 (proposals)

Doc 48 surveyed cloud providers and planned a measured round; **nothing has been run in the cloud**, and the owner deferred round 1
until the local results of doc 49 are in (owner decision, 2026-09-27). The consequences below are **proposals** from doc 48 §7.1; none
changes a decision above.

- **The OpenAI-compatible seam reaches every surveyed provider** (OpenRouter, the Hugging Face router, Mistral, Groq, Cerebras,
  Scaleway, DeepInfra and local servers). Through an aggregator a model id is not enough: a setup carries a **provider route**
  (endpoint tag, precision, `allow_fallbacks: false`, `require_parameters: true`), and its identity becomes (aggregator, model,
  endpoint, precision, reasoning setting, date) (doc 48 §4.2, §7.4 item 1).
- **Privacy flags by default for user content:** `zdr: true` and `data_collection: "deny"`; the host that served each call is recorded
  and shown in the run panel and the decision inspector (D010), because an aggregator forwards data to hosts the user did not name
  (doc 48 §2.5, §7.4 item 2). Whether aggregators ship as first-class providers is doc 48 OQ10, an owner question not yet filed.
- **Decision item 4's capability probe tests behaviour, not flags:** one real strict-schema request, a reasoning-off check and the
  served provider per (endpoint, model, route, precision, reasoning setting); flags disagreed with vendor docs in at least six cases
  (doc 48 §2.3). Reasoning is sent explicitly on every call and reasoning tokens go into the ledger (D026). Schemas need a per-provider
  normaliser with code validation of stripped keywords.
- **Compare setups by cost per correct decision** (CPCD), with doc 40's cost per admitted decision and the false-admit rate beside
  it, never by price per token: for harness-sized calls the bill is driven by admit rate, repairs, K and hidden reasoning (doc 48 §1.3,
  §5.3).
- **Usage accounting:** provider-reported cost and cached, cache-write and reasoning token counts feed the ledger; a key-limit HTTP 402
  maps to `BudgetLimited`; an error object inside an HTTP 200 is an error (doc 48 §7.1).

### 2026-09-28: refined by D045 and D046 (pointers)

A note under lifecycle item 5 (`docs/decisions/README.md`). Nothing above changes, and this record stays a research baseline for the
seam and the adapter choice; the header has no open part to mark.

- **Aggregators → [D046](D046-aggregators-as-first-class-providers.md)** (OWQ-25 (a), owner, 2026-09-28). Doc 48 OQ10, called "an owner
  question not yet filed" above, was filed as OWQ-25 and answered: aggregators are first-class providers. The note's proposals for
  them (a pinned provider route; `zdr: true` and `data_collection: "deny"` by default for user content; the serving host shown per
  call) are now owner rules, with a per-key host allow-list and periodic re-probes. How "the model provider the user configured"
  covers the downstream host is [DG039](../design-gap-requests/DG039-downstream-hosts-behind-aggregators.md), open.
- **Free-model presets → [D045](D045-free-model-offer-policy.md)** (OWQ-24 (b) and the owner's direction of 2026-09-27). The provider
  layer carries "connect a free model" presets on the user's own account as dated data, and a free model is offered for a step kind
  only if its provider's terms allow it and it passed Plotroom's qualification for that step kind.
- The deferral of round 1 above stands (OWQ-27; [D044](D044-cloud-first-model-screening.md)'s amendment note).
