# DG024: No per-request dynamic enums in cloud schemas

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass (doc 40 gap G6).
> Status: **open**. **Decision by: technical**. Blocks: the constrained-decoding design (doc 30 §4.5); schema generation for cloud adapters.

## Context

- **Doc 30 §4.5**: "Classes, waypoint and trigger types, group handles and card ids are dynamic enums rebuilt per request (doc 13
  §4). This is cheap and certain." Doc 30 §4.2: Fill slot specs carry dynamic enums.
- **Doc 40 §2.3** [V]: changing the output schema (`output_config.format`, `text.format`) breaks the provider cache; **§8** "What we
  will not do": "Per-decision JSON-schema enums on cloud APIs: new schema per call: grammar compile and cache miss".
- **Doc 40 R5**: "Picks answer with a letter; the menu text lives in the capsule; code maps letters and checks membership, length
  and codepage. Per-decision enums of real ids appear only in local grammars (doc 13; doc 30 §4.5), never in cloud schemas." §4.1:
  one frozen schema per DecisionKind.
- Doc 25 §2.4: grammar-constrained decoding gains are small and can distort outputs.

## The gap

Doc 30 builds a new schema per request for every backend; on cloud providers that costs a grammar compile and a cache miss on every
call, which doc 40 rules out.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Dynamic enums everywhere | The decoder cannot emit an invalid id | Cache miss and compile cost per call on cloud APIs |
| B | Local grammars only; cloud schemas fixed per DecisionKind; enum-like fields answered as letters over a menu in the capsule, and code checks membership after decoding | Cache-stable; code still guarantees validity (admission refuses non-members) | Cloud models can emit an invalid letter (refused, then repaired) |

## Recommended resolution (proposal)

Option B. Cloud: Pick uses the frozen letter schema; Fill fields whose values come from a computed set become letter fields over a
menu printed in the capsule below the breakpoints; admission maps letters and checks membership, as for Pick. Local engines keep
per-request grammars (llguidance, doc 13 §4), which do not affect prompt caching there. The schema per DecisionKind is registered
once (DG015).

## What it would change

- Doc 30 §4.2 Fill row and §4.5 "Enums" bullet: "local grammars only; cloud schemas fixed per DecisionKind, enums as letters".
- Doc 40 R5: rule; G6 closed.
- Doc 25 §4.3 per-step schemas: enum fields shown as letter menus for cloud setups.

## Affected docs

Docs 25, 30, 40; DG015.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 30 §4.2 and §4.5, doc 40 §2.3, §4.1, R5, §8 and §4.3 G6, and doc 25 §2.4, re-read on 2026-09-27.
