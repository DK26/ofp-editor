# DG011: `Admitted<T>` or `Checked<T>`, and what a changed read does

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
> **Decision by: technical** (design round). Blocks: the admission type in `ofp-workflow-runtime` and `ofp-campaign-flow`
> (doc 38 phase W2).

## Context

- **Doc 21 §1.2**: `pub struct Admitted<T> { value: T, reads: RevisionSet }`, built only by `check`. "`reads` binds a proposal to the
  revisions it looked at; a change to one of them refuses it, while unrelated edits do not (§8.2). Doc 25 §4.2 calls the same wrapper
  `Checked<T>` …; one name should win (Open question 1)." **§8.2**: "If an entity a proposal read or would write changed while the
  model was working, it is refused and recomputed. An approval binds the exact batch."
- **Doc 22 §4.3** cites `Admitted<T>`.
- **Doc 25 §4.2**: `pub struct Checked<T> { value: T, findings_resolved: u8, revision: CampaignRevision, read_set: ReadSet }`;
  `DecisionState::Admitted(Checked<Answer>)`. Invariant: if the user edited anything in the read set meanwhile, "it is re-verified
  against the current revision before admission, and dropped if it now fails or its target became human-edited or pinned."
- **Doc 38** OQ4 asks the name; its prose says "admitted" throughout (`StepStatus::Admitted { repaired }`); §4.4: "re-verified at
  commit: unrelated edits never block it, a changed read entity triggers a recompute".
- **Doc 40** measures "cost per *admitted* decision".

## The gap

Two names for one type, and a behavioural difference hidden behind them: on a changed read entity, docs 21 and 38 **refuse and
recompute**, while doc 25 **re-verifies** and keeps the value if it still passes.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | `Admitted<T>`; changed read → refuse and recompute (docs 21, 38) | Most docs already say "admitted"; the conservative rule | A campaign run wastes model calls whenever the user edits something the decision read |
| B | `Checked<T>`; changed read → re-verify (doc 25) | Cheaper; lets the user keep editing during long runs | "Checked" suggests any checked value, not one admitted for commit; fewer docs use it |
| C | `Admitted<T>` with doc 25's fields and a two-step rule: re-verify first (code only), recompute only if re-verification fails; approvals still bind the exact batch | Keeps the common name and doc 25's efficiency; checks, not the model, decide | Re-verification confirms validity, not that the model would still choose it |

## Recommended resolution (proposal)

Option C. The type is `Admitted<T> { value, reads: RevisionSet, revision, repaired: u8 }` (doc 25's `findings_resolved` becomes
`repaired`, matching doc 38's `Admitted { repaired }`). On a changed read entity: re-run the step's checks against the current
revision; admit if they pass and no target became human-edited or pinned; otherwise recompute (a new counted call, DG016). A user
approval still binds the exact batch (doc 21 §8.2): a changed batch needs a new approval. Menus whose options depended on the changed
entity are always recomputed, because the choice itself may no longer exist.

## What it would change

- Doc 21 §1.2 sketch and OQ1; §8.2 "refused and recomputed" → "re-verified; recomputed if it fails".
- Doc 25 §4.2: `Checked<T>` → `Admitted<T>`; field rename.
- Doc 38 OQ4 answered; §4.4 wording aligned.
- Doc 22 §4.3: no change.

## Affected docs

Docs 21, 22, 25, 38.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 21 §1.2, §8.2 and OQ1; doc 25 §4.2 (sketch and invariants); doc 38 §4.4, §4.7 and OQ4; doc 21's header note on
  doc 22 §4.3, re-read on 2026-09-27. The refuse-versus-re-verify difference was found while filing and is not recorded elsewhere.
