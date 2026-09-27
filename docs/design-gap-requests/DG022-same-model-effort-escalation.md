# DG022: Same-model effort re-run versus "never upward"

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass (doc 40 gap G4).
> Status: **open**. **Decision by: technical**, as a doctrine wording change: it adds no capability and stays inside the effort preset the
> user chose. The owner needs to decide only if the cross-model part is ever reopened (it stays rejected here). Blocks: doc 40 R6's
> escalation rule; the fallback ladder in the runtime.

## Context

- **Doc 25 §3 principle 5**: "Degrade downward, never upward … never silently switch to a bigger or cloud model. Offering a stronger
  model is a user choice." **§10.2**: "Never: silently retry with a larger or cloud model"; a stronger model is a button with its cost.
- **Doc 21 §1.4** rejects "automatic escalation to a larger or remote model" until our own instruments justify it; **§6.2 rule 3**:
  "No silent escalation. A stronger model is offered as a visible button with its cost."
- **Doc 12 §5.7**: clamp-only effort routing; "new user requests, tool errors and validation failures run at full effort".
- **Doc 40 R6 and G4**: when a validator still rejects after R repairs, or the model answers `none_fit`, re-run that decision once
  at the effort preset's provider-reasoning ceiling, on the same model, never above the ceiling, shown in the run panel ("re-ran at
  `medium`: finding V-text/length"); a different model stays a button. Doc 40 §5.1's D, E and G cost rows model a 15% automatic
  router → bound-model escalation, which current doctrine rejects; doc 40 reads it as user re-runs.
- Doc 40 §2.5 [V]: in one published SWE-bench Pro run on Opus 5.5, running at `low` and re-running failures at `high` solved about
  97% at about $0.17 per solved task, against 92.8% at about $0.22 for `medium` alone (a coding benchmark, not our workload).

## The gap

"Never upward" does not say whether it means model size and locality only, or also reasoning effort on the same model. Doc 12 §5.7
already raises effort on validation failures; doc 25 and doc 21 can be read as forbidding it.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Forbid any automatic increase, including effort | Strictest reading; fully predictable cost | Wastes the cheapest fix; contradicts doc 12 §5.7 |
| B | Allow one visible same-model re-run at the preset's reasoning ceiling; cross-model stays a button | Cheap, measured benefit; no new model, no new data destination; bounded by the user's preset | One cache miss where per-message effort is unsupported; slightly less predictable cost (still inside caps) |
| C | Allow automatic escalation to a bound larger model (doc 40 D/E/G as modelled) | Lowest cost per admitted decision in doc 40's model | Rejected by doc 21 §1.4 and doc 25 principle 5; changes the data destination; needs owner review |

## Recommended resolution (proposal)

Option B. Principle 5 is clarified as "never upward in model size or locality; a single same-model re-run at the effort preset's
reasoning ceiling is allowed and shown". The re-run counts as a turn and is reserved (DG016). Doc 40's D, E and G rows keep their
"read as user re-runs" caveat; option C stays rejected under doc 21 §1.4.

## What it would change

- Doc 25 §3 principle 5 and §10.2 ladder (a step "re-run once at the preset's reasoning ceiling" before re-menu or decompose).
- Doc 21 §1.4 (clarifying sentence) and §6.2 rule 3 (unchanged meaning).
- Doc 12 §5.7: consistent; cross-reference.
- Doc 40 R6 and G4: rule instead of `proposal-only`.

## Affected docs

Docs 12, 21, 25, 40; DG016, DG020.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 25 §3 and §10.2, doc 21 §1.4 and §6.2, doc 12 §5.7, and doc 40 §2.5, §5.1, R6 and §4.3 G4, re-read on 2026-09-27.
