# DG010: Resume reuses settled entries; one meaning for "replay"

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
> **Decision by: technical** (wording). Blocks: nothing in code; readers of docs 21, 25 and 40 currently get contradictory wording.

## Context

- **Doc 21 §6.2 rule 6**: "Model steps are never replayed from a log; a repair is a new, counted turn." **§8.2**: "Sessions resume
  from the document … resuming rebuilds the capsule and never replays a model call or a Preview launch." **§1.3**: "an interrupted
  launch is never replayed".
- **Doc 25 §4.2**: the `CampaignFlow` run is "persisted in the campaign sidecar so it can pause, resume and be replayed"; §6.2 step 7
  records the menu and seed "so the decision can be replayed and diffed".
- **Doc 38 §4.3** (last paragraph) and OQ3: the two "agree in substance but not in wording"; phase W0 files a note: resume **reuses**
  settled entries and never **re-executes** a settled model call. §4.2 defines reuse by determinism class; §6.4 "golden journals are
  replayed in CI".
- **Doc 40** R13: "Memoize exactly, replay from the journal"; R14: "replays from the journal (logits are not bit-identical across
  batch sizes)".

## The gap

"Replay" means two opposite things across the docs: re-executing a model call (forbidden by doc 21) and re-driving the runtime from
recorded results without any call (required by docs 25, 38 and 40). A reader cannot tell which is meant.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Keep "replay" in both senses; add a note in each doc | No edits beyond notes | The ambiguity stays in every future doc |
| B | Three defined terms: **reuse** (a settled, admitted result is used again with no model call), **re-run** (a new attempt, a new counted call), **replay** (re-driving the runtime from the journal or cassettes for resume, tests or inspection; never calls a model) | Each word has one meaning; matches doc 38 §4.2–§4.4 | Edits in docs 21, 25, 40 |

## Recommended resolution (proposal)

Option B, with this one-sentence rule used verbatim in docs 21, 25 and 38: **"Resume reuses settled entries and never re-executes a
settled model call; an unsettled request becomes a new, counted call (doc 38 §4.3 item 4)."** "Replay" is reserved for deterministic
re-driving from the journal or cassettes, which makes no model call and never relaunches Preview.

## What it would change

- Doc 21 §6.2 rule 6 and §8.2: "never re-executed" instead of "never replayed"; §1.3: "an interrupted launch is never relaunched
  automatically".
- Doc 25 §4.2 comment: "so it can pause, resume (reusing settled entries) and be replayed for inspection without model calls";
  §6.2 step 7 unchanged in meaning.
- Doc 38 §4.3 last paragraph and OQ3: answered by pointer.
- Doc 40 R13–R14: "reuse settled answers from the journal".
- A glossary entry once `docs/README.md` has a glossary.

## Affected docs

Docs 21, 25, 38, 40.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 21 §1.3, §6.2 and §8.2; doc 25 §4.2 and §6.2; doc 38 §4.2–§4.3, §6.4 and OQ3; doc 40 R13–R14, re-read on
  2026-09-27.
