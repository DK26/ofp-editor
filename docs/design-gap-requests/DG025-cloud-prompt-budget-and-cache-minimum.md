# DG025: The cloud (T3) capsule budget and provider cache minimums

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass (doc 40 gap G7).
> Status: **open**. **Decision by: technical**. Blocks: capsule budgets for cloud setups; doc 40 R11 stays `proposal-only`.

## Context

- **Doc 25 §4.4**: budgets ≤ 2K tokens for T1 models, ≤ 4K for T2, "larger for T3 only when a Compose/Draft step needs it". No
  cloud (T3) budget is fixed for Pick and Fill.
- **Doc 40 §2.3** [V, 2026-09-27]: a prefix shorter than the model's cache minimum is never cached, and nothing reports it: 512
  tokens (Opus 5.5, Opus 5, Fable 5.1), 1,024 (Sonnet 5, GPT-5.6+), 4,096 (Haiku 4.5, Gemini 3.5–3.8 Flash, 3.1 Pro). "Doc 25 §4.4's
  ≤ 2K / ≤ 4K budgets are for local tiers, but a cloud capsule of that size never caches on Haiku 4.5 or Gemini 3.x [I]."
- **Doc 40 R11**: the ledger checks that each prefix clears the minimum; below it (Haiku 4.5 and Gemini 3.x at 4,096; Flash-Lite
  never) expect no saving; grow the shared pack only when the growth replaces per-capsule text. **R1**: each model's cache minimum
  lives in `models.toml`. §5.4: padding the stage prefix to 4,096 would cut campaign cost 1.26–1.36× on Haiku 4.5 and Gemini 3.8
  Flash [I, model].
- Doc 40 §5.1: a Pick capsule is about 2.3K tokens, a text-slot capsule about 3.1K.

## The gap

The capsule budget is defined only for local tiers. For cloud setups nobody states whether a small capsule is the goal (weak-model
discipline) or whether the static prefix should reach the cache minimum (cost), and nothing records when a model will not cache.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Cloud uses the T2 budget for Pick and Fill; ignore caching | One budget rule; small focused capsules | Pays full input price on every call for Haiku 4.5 and Gemini 3.x |
| B | Cloud budget = shape budget for the **per-decision** part, plus a **shared stage prefix** that may grow to the model's cache minimum only with text that replaces per-capsule text (doc 40 R11); record "uncached (below minimum)" per namespace | Keeps per-decision focus; honest cost estimates; no padding with filler | Needs the stage prefix to be designed per stage |
| C | Pad every prefix to the minimum | Maximum cache hits | Filler text in the model's context; contradicts R11 |

## Recommended resolution (proposal)

Option B. Doc 25 §4.4 gains a cloud line: the per-decision part (request, digest, menu or slot spec, schema restated) keeps the T2
budget for Pick and Fill; the static stage prefix (doctrine, core and lens, cards, frozen exemplars, shape rules; DG019) is shared
across the stage's decisions and is not counted per decision. The model's cache minimum (from `models.toml`) is an input to that
budget: when a stage prefix cannot reach it without filler, the plan card's estimate assumes no caching and the ledger marks the
namespace "uncached (below minimum)". Filler is never added.

## What it would change

- Doc 25 §4.4: the cloud line and the split between per-decision budget and shared stage prefix.
- Doc 40 R11: rule; G7 closed; §5.4's padding row stays an analysis, not a recommendation.
- Doc 14 §7 `models.toml`: the cache-minimum field (already asked by doc 40 R1).

## Affected docs

Docs 14, 25, 40; DG019.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 25 §4.4, doc 40 §2.3, R1, R11, §5.1, §5.4 and §4.3 G7, re-read on 2026-09-27. Cache minimums are doc 40's
  figures as of 2026-09-27 and were not re-fetched here.
