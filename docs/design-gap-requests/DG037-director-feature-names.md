# DG037: One word, six features: names for the "Director" features

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass (docs 39, 41 and 43 step).
> Status: **open**. **Decision by: the design round**: the owner delegated pending user-facing names on 2026-09-27 (OWQ-08 (a);
> [D034](../decisions/D034-descriptor-placement-and-names-delegation.md) item 3), so the names go into the one names table, each cleared
> through doc 02 §9, and the owner reviews the table before the first release. Blocks: UI strings, Standing Orders entries, Drill
> track titles and Wilco's wording for the features below; no design or code work waits on it.

## Context

"Director" names, or is proposed to name, six different things:

| Feature | Where | What it is |
| --- | --- | --- |
| Cutscene Director | Doc 39 (title, §1–§8) | Generator: intent and map picks → a checked, editable doc 32 cutscene |
| Atmosphere Director | Doc 41 §3 | Generator: mood → Intel fields, lights, soundscape and cue plan per mission section |
| Director's view | Doc 32 §3.3 | The cinematics workspace (map, timeline, screenplay, thumbnails) |
| Drill track "C. Director" | Doc 33 §5.4 | A Drill track: cutscenes, briefings, scripts, campaigns, multiplayer, later editors, workshop tools |
| Director panel and Director actions | Doc 34 ed18, ed22 | A Preview-time panel on Remastered and CE (capture back, route recording) and its undo lane |
| The "director's desk" flow | Doc 26 §8.2 | The campaign-making flow in which the user stays the director (pick, re-roll with pins, twist cards) |

Prior art adds a seventh meaning users may bring with them: Left 4 Dead's "AI Director" (docs 26 and 43). Doc 39's product review
("Still open", Names) asks to clear the UI names through doc 02 §9 (doc 33 principle 9) before any string ships. The owner
settled Plotroom's naming system (D002) and the names Standing Orders and Drill (D028); the features above have no settled name.
Owner question OWQ-08 (pending user-facing names) lists other placeholders from doc 39 (the realism levels) but not this collision.

## The gap

A user, a Standing Orders entry or Wilco saying "open the Director" could mean any of six things. Two of them (the Cutscene and
Atmosphere Directors) are generators that share one vocabulary (doc 39 §3, doc 41 §3), so they may belong under one name, while
the others are a workspace, a tutorial track, a Preview panel and a metaphor.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | "Director" only for the two generators, always qualified (Cutscene Director, Atmosphere Director); descriptive names for the rest (for example a "cinematics workspace", a Drill track "Cutscenes and story", a "live panel" in Preview); "director's desk" stays a design metaphor in docs, not a UI string | Plain words; one clearance search covers two qualified names | Two long names; "Director" still carries the L4D meaning |
| B | One "Director" surface with modes (Cutscene, Atmosphere), others renamed as in A | One entry point for both generators; they already share mood tags, vistas and light (doc 39 §3) | Merges two panels that live in different views (timeline versus section card) |
| C | Coined names in the style of Standing Orders and Drill, one per surface | Distinct and memorable; fits the owner's naming so far | Each coined name needs a clearance search (doc 02 §9) and a plain-language line beside it |

## Recommended resolution (proposal)

Option A as the working default, so docs and prototypes stop colliding, with option C open to the owner for the two generators.
Whichever is chosen, every name goes through doc 02 §9's clearance checklist before a string ships, and Standing Orders gets one
entry per surface that names the others it is not.

## What it would change

- Doc 32 §3.3 (workspace name), doc 33 §5.4 (track C title), doc 34 ed18 and ed22 (Preview panel), doc 39 and doc 41 (feature names
  in text and UI), doc 26 §8.2 (a note that the "director's desk" is a metaphor).
- Standing Orders entries and Drill lesson titles that name these surfaces.

## Affected docs

Docs 02 §9, 26, 32, 33, 34, 39, 41; D002 and D028 (naming decisions so far); OWQ-08.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 39's product review ("Still open", Names), doc 41 §3, doc 32 §3.3, doc 33 §5.4, doc 34 ed18 and ed22, doc 26
  §8.2 and doc 02 §9, re-read on 2026-09-27. The L4D prior art is cited in doc 26 §2.2 item 8 and doc 43 §1.1; no clearance search
  was run in this pass.
- Doc 43's owner-level questions (the challenge catalogue, the default play seed, memory across playthroughs and whether a re-roll
  may exist) were not filed as requests: owner questions OWQ-20 and OWQ-21 already carry them, and doc 43 points there (DG038 words
  only the SL11 rule that follows OWQ-21). The Director collision has no such entry, so it is filed here.

### Owner answers (2026-09-27)

- OWQ-08 was answered (a): pending user-facing names are delegated to the design round, recorded in one names table and reviewed by
  the owner before the first release (D034 item 3). The header's "Decision by" now says so; the options and the recommendation are
  unchanged, and the request stays open until the design round picks the names.
