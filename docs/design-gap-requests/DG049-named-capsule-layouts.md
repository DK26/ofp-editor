# DG049: A small set of named capsule layouts that harness presets choose from

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-28 in the go-ahead pass (design-gap candidates of docs 51–63).
> Status: **open**.
> **Decision by: technical** (measurement: DG019's A/B run and doc 57 E13). Blocks: doc 55's `layout` knob, doc 57's message split
> (CL5), doc 60's `state_shared.v1` (P-06) and the lean capsule of doc 52 RG6; they stay `proposal-only`.

## Context

- **Doc 38 §3.3.** "The runtime fixes the capsule order …: authors declare contents, never layout." **DG019** (open) decides that
  order, measurement first; a layout change counts as major under DG012.
- **Doc 55 §7 item 5.** Presets need "a small, versioned set of layouts (static-first, menu-last, CPU-compact) to choose from".
- **Doc 51 §4.3, §6.1 item 11.** `layout_variant` is a preset choice; layout variants "must keep the static prefix byte-stable and be
  qualified before shipping".
- **Doc 57 §4.3, TE-G1, CL1–CL2, CL5.** Message boundaries (system prefix, a run-and-decision user message, a fixed acknowledgement,
  a sample tail) let hybrid and sliding-window local models reuse the digest; the split sits behind a preset field until E13
  decides; golden prefix tests through every dialect and template.
- **Doc 52 RG6; D050 open parts.** A lean capsule for token-capped providers (routed to DG019 and DG025 by D050).
- **Doc 60 P-06, §4 items 6–7.** A `state_shared.v1` layout beside `static_first.v1`, for several `DecisionKind`s asked over one
  item's state; the capsule builder refuses two items in one state for a per-item `DecisionKind`.
- **Doc 59 §7 item 2, OQ1.** Code-written thought as a named capsule segment, which the owner is asked about (glass box, D010).

## The gap

The runtime owns one layout, while four docs need presets to choose among several. Nothing says how many layouts exist, how they are
named and versioned, who qualifies them, or how their caching properties are tested.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | One runtime layout for every model (DG019 picks it) | One golden set | Measured per-family differences and token-capped providers cannot be served |
| B | A small, versioned, runtime-owned set of named layouts (for example `static_first.v1`, `state_shared.v1`, a menu-last and a CPU-compact form, a lean form for token-capped providers, with doc 57 §4.3's message boundaries as a field); a preset selects one by id; authors never choose; each layout has byte-stability goldens (doc 57 CL2) and is qualified before shipping; a layout change is major under DG012 | Presets fit models while caching stays testable | More goldens and qualification runs |

## Recommended resolution (proposal)

B (docs 51, 55, 57 and 60). DG019's measurement sets the default layout, and E13 decides the message split per model family. The
one-item-per-state rule of doc 60 P-06 applies to every layout. Code-written thought (doc 59 §7 item 2) waits for the owner's answer to
doc 59 OQ1 and is not decided here.

## What it would change

- Doc 38 §3.3 (a named layout per step, chosen by the preset); doc 40 §4.1 and R2–R4; doc 55 §3.3 (the `layout` field); doc 57 §4.3
  and CL1–CL5; agent-runtime §6 (capsule order); DG019 and DG025 (defaults and the lean form).
- Tests first (proposal; doc 57 CL2, doc 60 P-06): each layout's prefix bytes identical across decisions, runs and machines; a
  seeded regression (a timestamp above a breakpoint) fails; the builder refuses two items in one state for a per-item kind.

## Affected docs

Doc 38 §3.3; doc 40 (§4.1, R2–R4); doc 51 (§4.3, §6.1); doc 52 §6.2; doc 55 (§3.3, §7); doc 57 (§4.3, §5.1, §6.1); doc 59 (§7, OQ1);
doc 60 (P-06, §4); `docs/architecture/agent-runtime.md` §6; D050; DG012; DG019; DG025.

## Decision record

Open.

## Verification notes

### Filing (2026-09-28)

- Filed from doc 55 §7 item 5, doc 51 §6.1 item 11, doc 57 TE-G1, doc 52 RG6 and doc 60 §4 items 6–7 (deduplicated), re-read on
  2026-09-28 with DG019 and D050's open parts. Doc 59 §7 item 2 is cited but not filed here (owner question, doc 59 OQ1).
