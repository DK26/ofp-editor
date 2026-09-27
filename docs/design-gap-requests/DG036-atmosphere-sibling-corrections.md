# DG036: Atmosphere and audio corrections to docs 32, 34, 35 and the catalog

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass (docs 39, 41 and 43 step).
> Status: **open**. **Decision by: technical** (design round; items 1–3 are factual, items 4–6 change defaults). Blocks: nothing in
> doc 41's own design; doc 32's World-track rule and doc 34 ed12 stay as written until decided.

## Context

- **Doc 41 §2.5** ("Corrections for sibling docs") lists five corrections, each from doc 41's engine reading or corpus counts. Its
  engine review ("Still unverified") noted that none of DG002–DG018 covered them. A re-check against DG001–DG034 on 2026-09-27
  found none that does.
- **Doc 34 ed12** (music cues, mood playlist, ambient sound zones): "A cue is the trigger's `track`, or `playMusic` with a
  `fadeMusic` crossfade … The optional mood playlist (off by default) switches on the leader's `behaviour` … An ambient zone is an
  ed01 zone plus `soundEnv`/`soundDet`."
- **Doc 32** §2.5 and the §3.5 per-profile lowering rows "Subtitles for distant speakers: array `say` [U]" and "Music start
  offset: Not offered [U]" (both for Cwa199); the §3.2 World track row "Rain raises overcast ≥ 0.7 first" and a §3.7 lint "`setRain` below overcast 0.7".
- **Doc 35** rc08 ("one music cue per mission, no repeats") and rc43 ("Hour 7, overcast 0.3, fog 0 by default").
- **Doc 41 §5.2**: contact and firefight music is never scheduled by the planner; a hand-placed cue gets doc 28 MC19 (warn,
  dismissible). Doc 28 FP42 asks for no music under firefights.

## The gap

Docs 32, 34 and 35 state audio and weather rules that doc 41's engine reading contradicts or narrows, and doc 34's optional mood
playlist would schedule the very music doc 41 and doc 28 keep out of firefights. A module, lint or generator built from those
docs would model `soundEnv` as a zone, offer a music crossfade the engine cannot play, refuse array forms that 1.99's own content
uses, and hard-code defaults that doc 41's Atmosphere Director replaces with a light-first choice.

## The corrections

| # | Target | Correction | Evidence (doc 41) | Kind |
| --- | --- | --- | --- | --- |
| 1 | Doc 34 ed12 | `soundEnv` is a global bed switch that lasts until it is replaced, restored with `Default` or the section ends; it is not an ambient zone, and the switch is an instant cut. A music "crossfade" is a dip (fade out, switch, fade in): only one track plays | §2.2 [V]; engine review "Confirmed" | Fact |
| 2 | Doc 32 §2.5 and the §3.5 per-profile lowering table; doc 23 catalog | Official 1.99 content uses `playMusic [class, start]` (43 of 88 music scripts) and `say [class, 0]` (30 calls, 6 with a third element, which sets the subtitle speed); both forms very likely work on Cwa199 [I], pending probe AP3 | §1.2, §2.5 [V corpus] | Fact, pending a probe |
| 3 | Doc 32 §3.2 World track row and §3.7 lint | The engine's rain threshold is overcast ≈ 0.673 (rain needs 1.5·overcast − 1 > 0.01). Keep 0.7 as the compiler's margin and quote the real value in lint text. Doc 31 already quotes ≈ 0.67 (§4.6 module 15) | §2.1, §2.3 [V] | Fact |
| 4 | Doc 34 ed12 mood playlist | Found while filing: switching music on the leader's behaviour puts music under firefights. Either drop the playlist, or keep it opt-in with MC19 warning on every switch into combat | §5.2; doc 28 FP42, MC19 | Default |
| 5 | Doc 35 rc08 | "One music cue per mission, no repeats" is a default, not a rule: BI used about two `playMusic` calls per mission where it used music. Doc 41 §5.2's cue budget and AU17 (repeat within a campaign, info) carry it | §1.2, §5.2 | Default |
| 6 | Doc 35 rc43 | Its values (hour 7, overcast 0.3) stay valid, but the generator asks for the light first as a mood choice and never leaves the Intel defaults in place silently (AL01) | §3.1–§3.2, AL01 | Default |

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Apply all six as doc 41 words them | One step | Items 4–6 change what generators and modules do by default without a design-round look |
| B | Apply items 1–3 in the next cross-doc correction step; decide items 4–6 in the design round | Facts stop drifting now; defaults get one review | Doc 34 ed12's playlist and doc 35's defaults stay inconsistent with doc 41 until then |
| C | Leave the siblings; doc 41 overrides them where they meet | No edits | Docs 32, 34 and 35 keep teaching wrong facts; lints and modules built from them disagree with doc 41 |

## Recommended resolution (proposal)

Option B. Items 1–3 are applied with dated notes in docs 32, 34 and the doc 23 catalog (item 2 stays "very likely" until AP3
runs; the catalog marks the array forms "observed in official content", as doc 24's risk CSV already does for other commands). For items 4–6 this
request proposes doc 41's reading: drop ed12's behaviour-driven playlist, or keep it only as an opt-in with MC19 warnings; rc08
and rc43 become defaults that doc 41's cue planner and mood presets own.

## What it would change

- Doc 34 ed12: zone wording, crossfade → dip, playlist decision (items 1, 4).
- Doc 32 §2.5 and the §3.5 per-profile lowering table, the §3.2 World track row, §3.7 lint text (items 2–3).
- Doc 23 catalog: array-form notes for `playMusic` and `say` (item 2).
- Doc 35 rc08 and rc43: "default" wording with pointers to doc 41 §5.2 and §3 (items 5–6).
- Doc 41 §2.5 and its engine review: answered by pointer once decided. Doc 39 CA10 already cites item 2.

## Affected docs

Docs 23, 28 (MC19 reference only), 32, 34, 35, 39, 41.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 41 §1.2, §2.1–§2.3, §2.5, §3.1–§3.2, §5.2, §6 (AU17, AL01) and its engine review, re-read on 2026-09-27. The
  targets were read in their current text: doc 34 ed12, doc 32's §3.5 per-profile lowering rows for array `say` and music offsets,
  the §3.2 World track row and the §3.7 lint list, doc 35 rc08 and rc43, doc 31 §4.6 module 15. None had been changed by consolidation part 1.
- Doc 41 §2.5 item 3 first said "docs 31 and 32 use 0.7"; doc 31 already quotes ≈ 0.67, so doc 41 was corrected in the same step.
  Item 4 (the playlist) was found while filing; doc 41 §2.5 item 1 now mentions it. Corpus counts are doc 41's and were not re-run.
