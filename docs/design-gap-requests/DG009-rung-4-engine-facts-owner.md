# DG009: Which doc owns the cinematic engine facts: doc 31 §6 or doc 32 §2

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
> **Decision by: technical** (editorial, design round). Blocks: trimming docs 31 and 32 to their size targets; where later engine
> corrections about cameras, titles and cutscenes are written.

## Context

- **Doc 31**, verification notes, "Open" item 1: "§6 largely repeats doc 32 §2–§4. With these notes the file is about 830 lines,
  well over the ~650 target, so once doc 32 is accepted, cut §6 to the engine limits and the contract the other rungs rely on."
  (Item 3, the map-track drift, was reconciled in favour of doc 32 in the consolidation pass.)
- **Doc 32**, product review "Still open": "The doc is now ~640 lines; §2 could point to doc 31 §6.1 for the facts both docs
  repeat." Engine review "Still open or risky", Length: "these corrections push the doc to about 750 lines, well over the ~550
  target. §2 is the place to trim, by pointing to doc 31 §6.1 for the facts both docs repeat."
- **Doc 39** (still being written) §1.1 already reads: "Doc 32 owns the engine toolbox (§2), the typed model (§3.4), the compiler
  and safety wrapper (§3.5), hosts (§3.6), lints (§3.7), import (§3.8), preview (§4) …".
- Both docs carry engine reviews of the same camera facts (dive-bound `camSetDir`/`camSetBank`, the `camSetFovRange` stub, the commit
  model, title layers, the end gate).

## The gap

Each doc proposes to shrink by pointing at the other, so following both notes would delete the facts from both places. Neither doc
is declared the owner of the rung-4 engine facts, and both are over their line targets.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Doc 32 §2 owns the engine facts; doc 31 §6 keeps the rung's place on the ladder, the compile contract the other rungs rely on (§6.3) and pointers | Doc 32 is the specialist doc with the fuller engine review; doc 39 already assumes it; doc 31 reaches its target | Doc 32 cannot trim §2 that way and must trim elsewhere |
| B | Doc 31 §6.1 owns the facts; doc 32 §2 points to it | Doc 32 reaches its target | Moves the camera toolbox out of the camera doc; contradicts doc 39's assumption |
| C | Move the shared facts to a third place (Standing Orders entries or a data file) that both cite | Neither doc carries them | A new artefact to maintain; research docs lose self-contained reading |

## Recommended resolution (proposal)

Option A. Doc 32 §2 is the single owner of rung-4 engine facts (camera commands, motion model, overlays, sound, SQS runtime rules,
the Effects dialog, engine defects). Doc 31 §6 shrinks to: one paragraph on the rung, the §6.3 compile contract as the interface the
other rungs rely on, and "engine facts: doc 32 §2". Engine corrections found in either doc are written into doc 32 §2 and noted in
doc 31 only as pointers. Doc 32 reaches its size target instead by moving the §3.7 lint list into the code registry proposed in
DG005 (keeping one summary line per lint group) and by moving the engine-defect list to the engine-requests register (DG034).

## What it would change

- Doc 31 §6.1–§6.4: cut to summary, contract and pointers; verification "Open" item 1 closed with a pointer.
- Doc 32 product review "Still open" and engine review "Length": replaced by the DG005/DG034 trims.
- Doc 39 §1.1: already consistent.

## Affected docs

Docs 31, 32 (and 39 once final, no change expected).

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 31 verification notes ("Open" items 1 and 3 and the consolidation note on the map track), doc 32 product review
  "Still open" and engine review "Still open or risky", and doc 39 §1.1 (read only; doc 39 is still being written), re-read on
  2026-09-27.
- *Docs 39, 41 and 43 step (2026-09-27).* Doc 39 is final. Its §1.1 now reads "Doc 32 owns the engine toolbox, the typed model, the
  compiler and safety wrapper, hosts, lints, import, preview, templates and AI tools", without the section numbers quoted above, and
  its companions line still cites doc 31 §6; both fit option A, so no change to doc 39. Doc 39's own "Length" item (terrain facts to
  doc 07, AI facts to doc 31) raises the same question for other engine facts and is left to its product review.
