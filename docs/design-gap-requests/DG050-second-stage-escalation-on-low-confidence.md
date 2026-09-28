# DG050: Escalation to a second bound stage when the first is unsure

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-28 in the go-ahead pass (design-gap candidates of docs 51–63).
> Status: **open**.
> **Decision by: owner** (the reading of D023 decision 3 and D024 item 4; doc 53 OQ2; doc 58 OQ4). Blocks: doc 53 §4.3's two-stage
> role binding; doc 55's `bound_second_stage` route (its staged checker refuses it until decided); the CPU-only session plans of doc
> 52 §5.2 and doc 58 §5.2 that assume the tiny cascade.

## Context

- **D023 decision 3.** "A failed step is split into smaller ones, never silently moved to another model; switching models is a
  visible user choice with its cost." **Doc 21 §1.4** rejects "automatic escalation to a larger or remote model".
- **D050 item 3** (2026-09-28, under the owner's go-ahead): a user-authored route list may move a call on a **limit outcome** without
  a click per move, each move recorded, and "never moves because a step failed its checks". D050's open parts list "cross-model
  confidence escalation (doc 53 OQ2)". **D051 item 6**: "a larger step or a stronger model is a priced button"; the level never rises
  mid-run.
- **Doc 53 §4.3, R6, OQ2.** Proposal: "a visible, user-authored two-stage role binding ('router: tiny local model; when unsure: the
  bound session model or cloud setup'), set up once in the role-binding UI (D024), priced on the plan card, and recorded per step in
  the run record". Evidence bar R6: non-inferior to the session model alone, at least 50% fewer session-model calls, no loss of `X`
  recall. Doc 40's cost rows D, E and G already model a 15% router-to-bound-model escalation.
- **Doc 55 §7 item 9.** Until decided, a preset's route is limited to same-model re-ask, the user card and code's default.
- **Doc 56 §10 item 6.** A computed margin routes only after held-out calibration; self-reported confidence never routes.
- **Doc 58 OQ4, §4.11 item 1.** The same owner question, and component bindings (DG057). **DG022** (open): one visible same-model
  re-run.

## The gap

D050 settles moves on limit outcomes. A move because the first stage is unsure is neither a limit outcome nor a failed check, so
neither D050 item 3 nor D023 decision 3's split rule covers it; read strictly, D023 decision 3 treats it as a model switch that
needs a click each time.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | No second stage: a low margin goes to the user (`Q`, the top-2 card), to code's default, or to one visible same-model re-run (DG022) | D023 unchanged | A tiny CPU stage cannot hand hard menus to the session model; more cards for the user |
| B | A user-authored two-stage binding per role: on a low **calibrated** margin, the call goes to the bound second stage, priced on the plan card and recorded per step; allowed per (first stage, second stage, `DecisionKind`) only after R6 passes and the routing scores are calibrated on held-out data; never on self-reported confidence | Every move is authored and visible, as D050 does for limits; cuts session-model and cloud calls | Refines D023 decision 3 and D024 item 4; calibration per pair |
| C | B, but each escalation asks with a card | No standing automatic move | A card on every unsure menu; doc 52 §5.4's stall-card argument applies |

## Recommended resolution (proposal)

B, gated by R6 and calibrated routing: doc 53 §4.3 proposes the binding, doc 56 §10 item 6 adds the calibration rule, and D050 item 3
is the precedent for an authored, recorded move. Until the owner decides, A holds (doc 55 §7 item 9).

## What it would change

- D023 decision 3 and D024 item 4 (notes, as D050 added for route lists); doc 53 §4.3; doc 55's route knob; doc 21 §1.4 (a note that
  an authored, visible second stage is not "automatic escalation"); the plan card and run record (doc 38 §5.2–§5.3).
- Tests first (proposal): an escalation happens only with a bound second stage and a calibrated score below its threshold; the run
  record names the stage and margin; an uncalibrated pair never escalates.

## Affected docs

D023; D024; D050; D051; doc 21 §1.4; doc 40 (cost rows D, E, G); doc 52 §5.2; doc 53 (§4.2–§4.3, §5, OQ2); doc 55 §7; doc 56 §10;
doc 58 (§5.2, OQ4); DG022; DG057.

## Decision record

Open. Owner-level: needs an owner question (doc 53 OQ2 and doc 58 OQ4 ask it).

## Verification notes

### Filing (2026-09-28)

- Filed from doc 53 §4.3, doc 55 §7 item 9, doc 56 §10 item 6 and doc 58 OQ4 (one candidate across four docs), re-read on 2026-09-28
  with D023, D050 and D051. Written after D050 appeared the same day; route lists on limit outcomes are cited as decided there.
