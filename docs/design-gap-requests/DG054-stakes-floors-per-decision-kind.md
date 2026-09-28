# DG054: Stakes floors per `DecisionKind` that no preset can lower

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-28 in the go-ahead pass (design-gap candidates of docs 51–63).
> Status: **open**.
> **Decision by: technical** (design round); who sets the floors and whether Settings shows them is owner or technical (doc 60 OQ2).
> Blocks: the preset loader's threshold checks (doc 55 §3.3); doc 60 P-09 stays `proposal-only`.

## Context

- **D048 item 2.** A preset may set "the scoring mode and cascade thresholds" and never changes "the facts, the option computation,
  validation, repair limits or the product scope".
- **D051 item 3** (2026-09-28): each `DecisionKind` declares a product ceiling on step size that no preset, grant or setting raises;
  ceilings above FR0 are open parts.
- **Doc 53 §4.2.** Calibrated margins route a Pick: high margin → proceed; low → one permuted re-ask; still unstable → the top-2 card
  or `Q`. **Doc 60 §2.8, P-09, §4 item 2**: "A confidence threshold is not one number"; two tables: tuned per-preset routing values,
  and product-owned stakes floors per `DecisionKind`, "set by what a wrong pick costs to notice and undo (a reversible single-entity
  edit against a campaign-branch or multi-entity change)"; the preset loader refuses a routing value below the floor; a dead band
  maps to one permuted re-ask. "Reject … any per-model setting that lowers a stakes floor." OQ2: who sets the floors, and are they
  visible or editable in Settings?

## The gap

D051 caps how large a step a preset may ask for; nothing caps how low a preset may set the margin at which a decision is accepted
without a question. A preset tuned on average accuracy could accept a campaign-branch choice on a thin margin.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Thresholds live only in presets (D048 item 2 as written) | One table | A preset can route an expensive decision on a low margin |
| B | Two tables: tuned routing values per preset, and product-owned stakes floors in each `DecisionKind` registration, reviewed like code; the loader refuses a routing value below the floor; a dead band maps to one permuted re-ask | The threshold twin of D051's ceilings; presets keep tuning freedom above the floor | One more registry field per `DecisionKind` |

## Recommended resolution (proposal)

B (doc 60 P-09). Who sets the floors and whether Settings shows them stays open (doc 60 OQ2).

## What it would change

- D048 item 2 (a clarifying note, as doc 60 P-09 asks); the `DecisionKind` registry (a floors field beside D051's ceiling); doc 55
  §1.4 and §3.3 (the loader check); doc 53 §4.2 (the dead band).
- Tests first (doc 60 P-09): the loader refuses a preset whose accept margin is below the kind's floor; a decision in the dead band is
  re-asked once.

## Affected docs

D048; D051; doc 53 §4.2; doc 55 (§1.4, §3.3); doc 60 (§2.8, P-09, §4, OQ2); doc 63 §4.2.

## Decision record

Open.

## Verification notes

### Filing (2026-09-28)

- Filed from doc 60 §4 item 2 (with doc 63 §13 item 2, whose ceiling half D051 item 3 decided), re-read on 2026-09-28 with D048 and D051.
