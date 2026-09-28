# D055: A visible, user-authored second stage when the first is unsure

> **Status:** accepted · **Decided by:** owner delegation (2026-09-28, lightly edited: "Go ahead without the GPG passphrase. I will not
> be near the PC for hours. We are working remote"; "Tiny models with no cloud availability should be tested directly on PC. Either
> way, except for GPG signing, we can do everything else"; for a choice between design options, "Figure out the best option for this
> use case"); decided under the owner's delegation; the owner may overrule it on return · **Decided:** 2026-09-28 · **Recorded:**
> 2026-09-28
> **Scope:** moving a decision from a first stage (for example a tiny local model) to a second bound stage (the session model or a
> cloud setup) because the first is unsure (DG050 option B; doc 53 OQ2; doc 58 OQ4). **Refines:** D023 decision 3 and D024 item 4
> (dated notes); D026 (priced on the plan card, no learned router; dated note); D050's open part for cross-model confidence
> escalation (doc 53 OQ2); D051 item 6 (read with an authored second stage; dated note). **Related:** D010, D048, D049, D057; DG022;
> DG050; doc 21 §1.4; docs 40, 53, 55 and 56.
> **Open parts:** no pair has passed yet, so option A holds in practice (item 5); the calibration method and thresholds per pair (doc
> 53 §4.2, §5); DG022 (one visible same-model re-run); the CPU-only session plans of doc 52 §5.2 and doc 58 §5.2 wait for a pair that
> passes.

## Context

- D023 decision 3: "a failed step is split into smaller ones, never silently moved to another model; switching models is a visible
  user choice with its cost". Doc 21 §1.4 rejects "automatic escalation to a larger or remote model".
- D050 item 3: a user-authored route list may move a call on a limit outcome, each move recorded and shown, and never because a step
  failed its checks. An unsure first stage is neither a limit outcome nor a failed check, so neither rule covers it (DG050).
- Doc 53 §4.3 proposes a visible, user-authored two-stage role binding, priced on the plan card and recorded per step; its evidence
  bar R6 (§5.5): non-inferior to the session model alone on `pick-hard` pass^3, at least 50% fewer session-model calls, no loss of `X`
  recall and no rise in false `X`. Doc 56 §10 item 6: a computed margin routes only after held-out calibration; self-reported
  confidence never routes. Doc 55 §7 item 9: until decided, a preset's route is limited to same-model re-ask, the user card and
  code's default.
- D051 item 6: "The level never rises mid-run; a larger step or a stronger model is a priced button" (cited in DG050's Context).
- DG050 recommends B. Decided under the owner's delegation, as the decisions README's "owner delegation" kind (the practice that
  follows from D049) asks when one option is sound.

## Decision

1. **Option B of DG050: a user-authored two-stage binding per role** ("first stage; when unsure: second stage"), set up in the
   role-binding UI (D024), shown and priced on the plan card before the run.
2. **Only on a calibrated margin.** The call moves to the bound second stage only when the first stage's calibrated margin is below
   the pair's threshold; never on self-reported confidence (doc 56 §10 item 6).
3. **Only for a pair that passed.** A (first stage, second stage, `DecisionKind`) pair may escalate only after it passed doc 53's R6
   bar and its routing scores were calibrated on held-out data (doc 56 §10 item 6). An uncalibrated or unpassed pair never escalates.
4. **Recorded per step:** the run record and the decision inspector name the stage that answered and the margin (doc 53 §4.3:
   "answered by stage 2 after margin 0.08").
5. **Until a pair passes, option A holds** (doc 55 §7 item 9): a low margin goes to the user (`Q`, the top-2 card), to code's default,
   or to one visible same-model re-run if DG022 allows it; the staged checker keeps refusing `bound_second_stage` for such pairs.
6. **Reading of D023 decision 3, doc 21 §1.4 and D051 item 6.** An authored, visible second stage is the user's own choice made
   before the run, not the "automatic escalation" doc 21 §1.4 rejects, in the same way D050 item 3 treats authored route lists. A step
   that fails its checks is still split, never moved. D051 item 6 stands: the second stage answers the same `DecisionKind` at the
   step's effective level, never a higher one; the plan card prices it before the run in place of the button; a failed or
   over-budget step still splits down.
7. **Tests first** (DG050): an escalation happens only with a bound second stage and a calibrated score below its threshold; the run
   record names the stage and margin; an uncalibrated pair never escalates; the second stage never answers above the step's
   effective level (item 6).

## Alternatives considered

| Option (DG050) | Why not chosen |
| --- | --- |
| A: no second stage; a low margin goes to the user, code's default or a same-model re-run | Kept only until a pair passes: a tiny CPU stage cannot hand hard menus to the session model, and the user gets more cards |
| C: B, but each escalation asks with a card | A card on every unsure menu; doc 52 §5.4's stall-card argument applies |

## Consequences

- Cuts session-model and cloud calls where a pair passes (doc 53 R6 asks for at least 50% fewer); doc 40's cost rows D, E and G,
  which model a 15% escalation, can describe an authored binding once a pair passes R6 and is calibrated; until then they read as
  user re-runs.
- No router model is trained: the margin is computed by code from the first stage's own scores (doc 53 §4.2), so D026 decision 3's
  "no learned routers" holds (doc 40 §8).
- Friction (D049): one binding set up once; fewer cards on unsure menus once a pair passes; calibration work per pair for
  contributors.
- Folding steps, not done here: doc 53 §4.3; doc 55's route knob; doc 21 §1.4 (a note that an authored, visible second stage is not
  "automatic escalation"); the plan card and run record (doc 38 §5.2–§5.3). D023, D024, D026, D050 and D051 carry dated notes.

## Sources

DG050; D023; D024; D050; D051 (item 6); doc 21 §1.4; doc 40 (cost rows D, E, G; §8); doc 53 (§4.2, §4.3, §5.5 R6, OQ2); doc 55
§7 item 9; doc 56 §10 item 6; doc 58 OQ4; the owner's delegation of 2026-09-28.
