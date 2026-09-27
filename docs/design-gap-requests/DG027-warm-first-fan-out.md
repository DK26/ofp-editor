# DG027: Warm-first fan-out and llama.cpp slots

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass (doc 40 gap G9).
> Status: **open**. **Decision by: technical**. Blocks: the scheduler in `ofp-workflow-runtime` (doc 38 phase W4); doc 40 R9 and R14 stay
> `proposal-only`.

## Context

- **Doc 38 §4.5**: fan-out items are seeded by stable keys, joined in key order, budget reserved in key order; `max_concurrency`
  defaults to 1 locally and more remotely; "Prefix reuse. Capsules put system text and tool schemas first, so a slot's K candidates
  share a prompt prefix; local reuse is [U]."
- **Doc 40 §2.3** [V]: on Anthropic a new cache entry becomes readable only once the first response starts streaming, so N parallel
  identical requests all pay full price; DeepSeek needs seconds to build a cache unit.
- **Doc 40 R9**: group parallel decisions that share a prefix; send one; release the siblings on its first streamed token, with
  bounded concurrency; admit in key order; K samples of one decision follow the same rule. **R14**: llama.cpp `cache_prompt` on, one
  slot per busy DecisionKind.

## The gap

Doc 38 fans out immediately, so parallel siblings miss a cache that the first request has not written yet; the local prefix-reuse
behaviour is left unknown.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Fan out immediately (doc 38 today) | Lowest latency on the first batch | Every sibling pays full input price on cloud |
| B | Warm first: send one request per shared prefix, release siblings on its first streamed token; on llama.cpp keep one slot per busy DecisionKind with `cache_prompt` | Cache hits for siblings; admission stays in key order, so results do not change | Adds one request's time-to-first-token of latency per group |

## Recommended resolution (proposal)

Option B for every backend: the scheduler groups ready items by cache namespace (stage × DecisionKind; doc 40 R4), sends one, and
releases the rest on its first streamed token within `max_concurrency`; on llama.cpp it assigns one server slot per busy
DecisionKind with `cache_prompt` on. Admission and joins stay in key order, so AT-W9 (concurrency 1 and 8 give identical documents)
still holds. Doc 38 §4.5's "local reuse is [U]" becomes a probe in the local test suite (a second request of the same namespace
reports reused prompt tokens).

## What it would change

- Doc 38 §4.5 "Prefix reuse" bullet: warm-first rule and the llama.cpp slot rule; the [U] becomes a probe.
- Doc 40 R9 and R14: rules; G9 closed.
- Doc 13 (local inference): the slot rule cross-referenced.

## Affected docs

Docs 13, 38, 40.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 38 §4.5 and phase W4, and doc 40 §2.3, R4, R9, R14 and §4.3 G9, re-read on 2026-09-27.
