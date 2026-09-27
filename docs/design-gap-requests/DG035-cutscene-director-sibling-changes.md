# DG035: Cutscene Director changes asked of sibling docs

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass (docs 39, 41 and 43 step).
> Status: **open**. **Decision by: technical** (design round, from the corpus counts and engine readings doc 39 cites). Blocks: the
> Director's planner and checks (doc 39 phases DP1–DP3) stay `proposal-only` where they rely on group C below; doc 32's lints and
> templates stay as written until decided.

## Context

- **Doc 39 §1.2** ("Changes asked of siblings"; "this doc edits no other file") lists twelve changes to docs 07, 23, 28, 31, 32 and
  35, each with its evidence. Doc 39's product review ("Still open") and the index of this folder ("Candidates noticed but not
  filed") both said to file them once doc 39 was final.
- **Doc 39 §9.3** reconciles its corpus counts with doc 35: intro medians 115 s (Resistance) and 56.5 s (1985) against doc 35's
  125 s and 87 s; cutscene missions median 125 s with 21 shots against rc35's "25–35 shots, about 2.5 min". Doc 39 open question 7
  keeps the reconciliation open.
- **Doc 39 §1.2, closing paragraph**: four engine limits (no look-at offset, no view-distance getter, no end-of-speech signal, no
  formation-spacing command) belong in the engine-requests register, not here; they are ER-071, ER-074, ER-073 and ER-109 in
  `docs/upstream/engine-requests.csv` (DG034 records the routing).
- Doc 35 rc35 targets doc 32's templates and doc 19's Cutscene node, so a change to rc35 reaches those two docs too.

## The gap

Doc 39 builds its planner and checks on rules that its sibling docs do not state or that they contradict. Doc 32's "eye below
2 m clearance" warning would fire on more than half of BI's own shots; doc 28's intro cap would flag a typical official intro;
doc 35's cutscene recipe uses a population and shot definition that doc 39's counts do not reproduce; and doc 32's typed model has
no event-gated cue and no per-shot pin, which doc 39's gates and pins need. Until the siblings change, a reader of doc 32 gets lints
that the Director's own output would trip.

## The requested changes

Grouped by what they need. Evidence is doc 39's; section numbers are doc 39's unless another doc is named.

| # | Target | Change | Evidence | Group |
| --- | --- | --- | --- | --- |
| 1 | Doc 32 §3.6 death-cam row, §7 AT6 | The stock global `onPlayerKilled.sqs` ships (doc 32 has "[U]"); add a bounded "like the default" DeathCam preset; AT6's "`say` with radio styling" is defined by doc 39 CA10 | §9.2 (local corpus [V]); CA10 | A (fact) and C (preset) |
| 2 | Doc 31 §4.6 row 9, §2 row 37 | No script command sets formation spacing; SAFE or CARELESS vehicles follow in ID order whatever the formation; an open column needs one group per vehicle or march unit | §5.2 [V by reading] | A |
| 3 | Doc 35 rc35, §3.2 | State the population and the shot definition behind the recipe | §9.1, §9.3 | A |
| 4 | Doc 32 §3.3, §4.2 | Thumbnails settle a few `triSimFrames` after `triSceneReady` (which reads OK at once); in-mission look via `triSetAspectGameplayActive`; a terrain strip on the subdivided surface with a source badge | §4.3, §6.3 [V] | A (harness facts) and C (terrain strip) |
| 5 | Doc 23 dialect list | `moveTo`, `enableAI`, `animationState`, `forceSpeed` and `limitSpeed` are unregistered on every profile (doc 31 already records `enableAI`) | §5.3 [V grep] | A |
| 6 | Doc 32 §3.3, §3.7 | Replace the "eye below 2 m clearance" warning with DR01 (whole-path clearance on the best-known surface) | Official eye height median 1.60 m, n = 2,152 [V] | B |
| 7 | Doc 32 §3.2 | The "eye ≥ 0.5 m" invariant becomes a worm's-eye warning; reject only below 0.3 m | 33 of 614 intro and 83 of 941 cutscene-mission keys with explicit height are below 0.5 m; the clamp is 0.1 m [V] | B |
| 8 | Doc 28 FP43 | The intro cap "≤ 60–90 s" becomes a warning with per-archetype budgets | Intros median 72 s; 11 of 34 exceed 90 s [V] | B |
| 9 | Doc 35 rc35 | After row 3, the recipe becomes a band: 18–32 shots, 1.5–3.5 min; doc 32's templates and doc 19's Cutscene node take the band | §9.3 | B |
| 10 | Doc 32 §3.4–§3.5 | Add `Gate` (an event-gated cue with a timeout and a fallback) and gate-relative cues | 18% of official camera scripts wait on world events [V]; §4.5 | C |
| 11 | Doc 32 §3.4, §3.2 | `Shot` and actor cues carry their own `origin` and `pin`, not only `CineSequence`; the Actors rule "snaps only under a cut or fade" adds "or proven off-frame" (DR15) | §7; doc 25 §9.1 pins per element and field | C |
| 12 | Doc 32 §5.1 | Add templates "Pan A→B" (≤ 45° segments), "Go-by" and "Orient on map" (probe-gated) | Pans are the commonest moving commit [V]; §9.1 | C |
| 13 | Doc 32 §3.5 | The epilogue restores radio only when returning to play, and view distance only to a value the compiler knows | No view-distance getter exists (§4.3) | C |
| 14 | Docs 07, 39 §4.7 | `plotroom-p3d` reads the `pilot` and `zamerny` memory points; a read-only subdivision-cache reader and exact `SurfaceY` in `plotroom-terrain` (docs 07 and 39 use the working names `ofp-p3d` and a new `ofp-terrain`; [crate-map §15](../architecture/crate-map.md) maps them) | §4.2–§4.3; DP0 | D |

- **A, facts:** corrections backed by [V] evidence; no design choice.
- **B, severities and defaults:** evidence-backed, but they change what a lint reports or a recipe recommends.
- **C, model and template additions:** new types, fields or templates in doc 32's model.
- **D, code:** crate scope for doc 39's phase DP0.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Apply all fourteen as doc 39 §1.2 words them | One step; doc 39's planner works as designed | Rows 10–12 widen doc 32's typed model without a model review; where camera facts live is still open (DG009) |
| B | Apply groups A and B in the next cross-doc correction step; decide group C in the design round together with doc 32's model review; D lands with DP0 | Facts and severities stop drifting now; model changes get one review | The Director's gates and per-shot pins stay `proposal-only` until then |
| C | Leave doc 32, 28, 31 and 35 as they are; the Director keeps its own checks | No sibling edits | Two contradictory rule sets for one timeline; doc 32's lints would flag the Director's BI-like output |

## Recommended resolution (proposal)

Option B.

- Group A goes into the target docs with dated notes, as other factual corrections did in the consolidation pass.
- Group B adopts doc 39's severities, following `AGENTS.md` ("realism is a default, not a wall"): errors only for what the engine
  will not do, warnings for likely mistakes, style notes for taste. Row 9 waits for row 3.
- Group C is decided in the design round with DG009 (doc 32 as owner of the camera engine facts) and DG005 (DR checks share one
  finding with the doc 32 lints and doc 28 MC19 they restate).
- Group D is scoped when DP0 starts.
- The four engine limits stay in the engine-requests register (ER-071, ER-073, ER-074, ER-109; DG034).

## What it would change

- Doc 32 §3.2, §3.3, §3.4–§3.7, §4.2, §5.1, §7 AT6: rows 1, 4, 6, 7, 10–13.
- Doc 28 FP43: row 8. Doc 31 §2 row 37 and §4.6 row 9: row 2. Doc 35 rc35 and §3.2: rows 3 and 9; doc 19's Cutscene node recipe
  follows rc35.
- Doc 23's dialect list: row 5. Doc 07 §7 (`plotroom-p3d` output) and the `plotroom-terrain` scope in the
  architecture's crate map: row 14.
- Doc 39 §1.2, §9.3 and open question 7: answered by pointer once decided.

## Affected docs

Docs 07, 19, 23, 28, 31, 32, 35, 39; DG005, DG009, DG034.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 39 §1.1–§1.2, CA10, §4.2–§4.3, §4.5, §4.7, §5.2–§5.3, §6.1, §6.3, §7, §9.1–§9.3, §10 and open question 7, and the
  product review's "Still open", re-read on 2026-09-27. The targets were checked in their current text: doc 32 §3.2 (the "eye ≥ 0.5 m"
  invariant), §3.7 ("eye below 2 m clearance"), the §3.6 death-cam row ("that the stock data ships the global file is [U]") and §5.1;
  doc 28 FP43 ("intro ≤ 60–90 s"); doc 31 §2 row 37 and §4.6 row 9; doc 35 rc35. None had changed, so none of the rows is applied yet.
- Doc 23 has no dialect entry for the five commands; doc 31 §2 row 18 already says no `enableAI` is registered. Doc 07 §7's `MapInfo`
  has no memory points. The corpus counts and engine lines are doc 39's and were not re-run here.
- Links and naming review (2026-09-27): row 14 and "What it would change" now name the planned crates `plotroom-p3d` and
  `plotroom-terrain` (D002 item 4; `AGENTS.md`, "Naming and Trademarks") instead of the research working names, which row 14 keeps
  only as a pointer to docs 07 and 39.
