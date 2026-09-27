# D040: Play seeds, memory across playthroughs, and no re-roll on restart

> **Status:** accepted · **Decided by:** owner (OWQ-21) · **Decided:** 2026-09-27 · **Recorded:** 2026-09-27
> **Scope:** the default play-seed policy of campaigns Plotroom generates, memory across playthroughs, and re-rolling stored rolls on
> restart. **Related:** D005, D039, D042. **Open parts:** DG038 (the exact SL11 and VY01 wording for the one bootstrap draw; a technical
> decision for the design round, which this record does not make); probes P-R10 and P-R12 (doc 43); the look of the reset.

## Context

- Campaign rolls come from a stored LCG seed, so restarting from a campaign-book row replays the same roll for the same outcome
  (doc 29 §3.3, SL11). The play seed is that LCG's initial value: "Fresh each playthrough" rolls it once at the start
  (`PlaySeedPolicy::RolledAtStart`); "Fixed (shareable)" bakes it from the build seed (`Baked`), so everyone gets the same rolls
  (doc 43 §3.2).
- `objects.sav` survives a new playthrough, so memory across playthroughs is possible in principle (doc 43 §5; probe P-R10).
- An opt-in "re-roll on restart" would mix engine `random` into the seed for players who choose it (doc 36 OQ2; doc 43 OQ2).

## Decision

1. **Default play seed: Fresh each playthrough** for campaigns. **Fixed (shareable)** is used for challenge entries (D039 item 3) and
   "beat my run" re-exports, and stays available to creators.
2. **Memory across playthroughs is opt-in per campaign**, with a reset the player can see and use.
3. **No re-roll exception in v1.** Restarting never re-rolls stored rolls.

## Alternatives considered

- Fixed by default (seed b): every playthrough of one file plays the same; the run-time variety doc 43 designs would not reach
  players unless creators changed a setting.
- Memory on by default (b): carries state into a new playthrough that players and creators did not ask for. Never (c): loses the
  callbacks to earlier playthroughs that some campaigns want (doc 43 source row 17).
- A documented opt-in re-roll (re-roll b): risks the reroll loops cv43 item 4 bans, and the Exploiter policy's gain from it (doc 29
  SL28) is unmeasured.

## Consequences

- The Fresh default needs one engine `random` draw in the bootstrap row, which SL11's current wording does not allow. DG038 settles
  the rule text; its recommended option (one named exception, drawn once while the seed is unset) fits this record, and its option C
  (an opt-in re-roll) stays out of v1 by item 3.
- Memory uses versioned `objects.sav` keys and ships after probe P-R10 passes (doc 43 RV4, v1.3 in the roadmap).
- Doc 43 OQ2, OQ8 and OQ9 and doc 36 OQ2 are answered by pointer in the folding step.

## Sources

Doc 43 (§3.2, §3.7, §5, RV4, OQ2, OQ8, OQ9, review notes); doc 29 (§3.3, SL11, SL28); doc 36 (cv43, OQ2); DG038; roadmap §4;
`OWNER-QUESTIONS.md` OWQ-21.
