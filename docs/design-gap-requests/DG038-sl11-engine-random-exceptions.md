# DG038: Engine `random` and SL11: the play-seed bootstrap and opt-in re-roll on restart

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass (docs 39, 41 and 43 step).
> Status: **open**. **Decision by: technical** (design round). Its precondition is met: the owner answered OWQ-21 on 2026-09-27
> (Fresh play seed by default, memory opt-in, no re-roll exception in v1;
> [D040](../decisions/D040-play-seeds-and-memory.md)). This request covers only the rule text that follows.
> Blocks: doc 43's `PlaySeedPolicy::RolledAtStart` (§3.2) and its run-time New Adventure check (§1.4); the re-roll Campaign Condition
> (doc 43 §2.5).

## Context

- **Doc 29 §3.6, SL11** (error): "Engine `random` or a `presence` probability drives state that is committed or read by a guard."
  The §3.2 type sketch comments `RollSource`: "Engine `random` is allowed only for cosmetic variety (SL11)." Stored rolls use the
  LCG `cmp_seed = (cmp_seed * 75 + 74) mod 65537` (doc 29 §3.3).
- **Doc 43 §3.2**: the play seed is the initial `cmp_seed`. The proposed default `RolledAtStart` draws it once from engine `random`
  in the bootstrap prologue row, so playthroughs of one file differ; `Baked` fixes it from the build seed. "Using one engine draw as
  entropy for the first `cmp_seed` extends SL11's current wording … and needs a doc 29 change" (open question 3).
- **Doc 43 §2.5** and open question 2, and **doc 36 open question 2**: an opt-in "re-roll on restart" would mix engine `random` into
  the seed for players who choose it. It must not create reroll loops (doc 36 cv43 item 4), and the Exploiter policy (SL28) must gain
  nothing from it.
- **Doc 43 §2.1** (one draw carries at most 15 bits; the generator cannot be seeded or saved) and **§2.5** (the bootstrap runs only
  while the seed is unset, in a prologue row with no gameplay and no debriefing; probe P-R12). **VY01** is SL11's per-mission
  extension. The engine side is register entry ER-093 in `docs/upstream/engine-requests.csv`.
- **OWQ-21** asks the owner for the default play seed (recommended: Fresh each playthrough, Fixed for challenge entries and "beat my
  run" re-exports) and whether a re-roll exception exists (recommended: none in v1).

## The gap

Doc 43's proposed default commits a value drawn from engine `random`, which SL11 as written forbids, and two docs ask for a second,
player-chosen exception. Whatever the owner answers in OWQ-21, SL11, doc 29's `RollSource` and the lints need wording that says
exactly which engine draws may reach committed state.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | SL11 stays absolute (the answer if OWQ-21 picks Fixed by default) | No exception to explain | Every playthrough of one file is the same; doc 43 §1.4's run-time twin fails by design |
| B | One named exception: a single engine draw, once, in the bootstrap prologue row, only while the seed is unset, stored at once and never re-drawn; SL11 and VY01 allow that source and nothing else | Fits a Fresh default; anti-scum holds, because the stored seed replays on every restart path (doc 43 §2.5) | SL11 gains its first exception; the bootstrap placement still needs probe P-R12 |
| C | B, plus an opt-in re-roll that mixes one engine draw into the seed at a restart, disclosed on the campaign card and excluded from challenge entries | Player choice, as in Civ III (doc 36 §3.1 row 16) | Only if OWQ-21 allows it; cv43 item 4 and SL28 must be shown to hold |

## Recommended resolution (proposal)

Follow OWQ-21's recommended answers: option B, with a lint that the draw sits in the bootstrap row and runs only while the seed is
unset, and a named source in doc 29's `RollSource` (doc 43 §2.9 already extends that enum). Option C stays out of v1; revisit it
only if the owner allows a re-roll and the balance lab shows SL28's Exploiter policy gains nothing.

## What it would change

- Doc 29 SL11 wording and the `RollSource` comment; doc 43 §2.9's `RollSource` names the bootstrap source.
- Doc 43 §3.2, §2.5, VY01 and open questions 2–3; doc 36 open question 2: answered by pointer.

## Affected docs

Docs 29, 36, 43; OWQ-21; `docs/upstream/engine-requests.csv` ER-093 (engine side).

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 29 §3.2, §3.3 and §3.6 (SL11); doc 36 §3.1 row 16, cv43 and open question 2; doc 43 §1.4, §2.1, §2.5, §2.9,
  §3.2, VY01 and open questions 2–3; OWQ-21, re-read on 2026-09-27.
- The product questions (the default seed, whether a re-roll may exist) are OWQ-21's and are not repeated here. A first draft of this
  request also carried them; it was narrowed to the rule text before this note was written.

### Owner answers (2026-09-27)

- OWQ-21 was answered: seed (a), Fresh each playthrough by default and Fixed for challenge entries and "beat my run" re-exports;
  memory (a), opt-in; re-roll (a), no exception to SL11 in v1 (D040). So option A no longer fits the default, and option C stays out
  of v1. The header now records that the precondition is met; the options and the recommendation (option B) are unchanged, and the
  request stays open until the design round words the rule (D040 does not decide it).
