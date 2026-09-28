# DG043: The repair turn: capsule shape, which finding goes in, and repair versus resample

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-28 in the go-ahead pass (design-gap candidates of docs 51–63).
> Status: **open**.
> **Decision by: technical** (measurement: doc 57 E13 and CL5; doc 61 TT-19). Blocks: the repair capsule builder (doc 25 §7.2;
> agent-runtime §6); doc 51 §4.6's repair bullet and doc 57 CL4–CL5 stay `proposal-only`.

## Context

- **Doc 25 §7.2.** A repair turn carries one finding written for a model reader with recomputed allowed values; repair stops on a
  recurring finding, a spent R, or a repeated (decision, answer digest).
- **Doc 51 §4.6, V10, §6.1 item 9.** "Every PICK and FILL repair is a fresh single-turn capsule (system, then one user message with
  the task, the offending value and one finding), safe under any template"; the finding sits at the tail after the restated schema;
  no reasoning replay; multi-turn repair only for COMPOSE and creative text. Three budgets are never shared: transport retries,
  resamples after an `InvalidAnswer`, and repairs R.
- **Doc 57 §3.6, §4.3, CL4–CL5, TE-G3, §6.3.** Every auxiliary call for a decision (K samples, repairs, EXPLAIN) appends to the
  decision's exact capsule bytes, with strict user/assistant alternation and a fixed acknowledgement. On hybrid and sliding-window
  local models a fresh capsule reuses only the system message; "the appended repair above is also a proposal to amend V10". E13
  measures whether the acknowledgement hurts small models' admit rates; CL5 tests that each qualified template renders it
  byte-stably; the split sits "behind a preset field until E13 decides".
- **Doc 61 TG1, TG3, TG6, TG9 (§6 items 1, 3, 7, 13).** A delta rule (repair quotes only what the proposal introduced); which finding
  when several exist (severity-weighted), with advisories never repaired (D011); a repair-versus-resample rule per setup; finding
  deltas as a rank feature and a stop rule.
- **Doc 62 §6.9, §10 item 8.** Evidence for grouping related errors: one *root* per turn with the findings that share its entity or
  field, against agent-runtime §6's "one finding per turn".
- **DG016** counts repairs and transport retries; **DG021** proposes adaptive K.

## The gap

Two proposals shape the same turn differently. Doc 51 makes every Pick and Fill repair a fresh single-turn capsule for template
safety; doc 57 appends it to the decision's bytes for prefix reuse, which matters most on hybrid and sliding-window local models.
Doc 57 names the conflict (§6.3) and doc 51 predates it. Separately, the content of the turn has four open proposals (delta rule,
which finding, one finding or one grouped root, repair or resample), all touching doc 25 §7.2's one repair protocol.

## Options

Capsule shape:

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Fresh single-turn capsule for every Pick and Fill repair (doc 51) | Safe under any chat template; no role-alternation dependency | On hybrid and SWA models a repair re-processes the digest (doc 57 §4.3) |
| B | Append to the decision's capsule bytes with strict alternation (doc 57 CL4) | Prefix reuse for samples, repairs and EXPLAIN on every model | Needs a byte-stable acknowledgement per template (CL5) and E13's evidence that it does not lower admit rates |
| C | A per-preset field: A by default, B for a model family only where CL5's template test passes and E13 shows no loss | Uses each model's safe option; doc 57 CL5 already puts the split behind a preset field, and doc 51 makes `role_alternation` a profile fact | Two paths to test |

Content (separate proposals, each adopted or rejected on its own evidence):

| # | Proposal | Source | Evidence named |
| --- | --- | --- | --- |
| C1 | Delta rule: quote only findings the proposal introduced | Doc 61 TG1 | Doc 61 §4.6 |
| C2 | Severity-weighted choice of the one finding; advisories never repaired | Doc 61 TG3; D011 | Doc 61 §4.6 |
| C3 | One root per turn with its grouped findings | Doc 62 §6.9 | Doc 61 TT-19's finding-field ablation; doc 62 §9.2 |
| C4 | Repair or resample, chosen per setup | Doc 61 TG6 | Doc 61 TT-19 (repair vs resample arm) |
| C5 | "The repair did not reduce findings" as a stop rule and rank feature | Doc 61 TG9 | Doc 61 §4.6 |

## Recommended resolution (proposal)

No source reconciles the two shapes. C is the combination both sources allow (doc 57 CL5's preset field; doc 51's profile fact),
decided per model family by E13 and CL5. For the content, C2's advisory exclusion follows from D011 (advisories are dismissible,
never errors), as doc 61 proposes; C1, C3, C4 and C5 are decided by doc 61 TT-19's pre-registered arms. Whatever wins, doc 51's three
separate budgets and DG016's accounting stay.

## What it would change

- Doc 25 §7.2 (the protocol); doc 51 §4.6 and V10; doc 57 §4.3 and CL4–CL5; agent-runtime §6 ("one finding per turn"); the harness
  preset schema (doc 55) gains the layout field if C wins (see DG049).
- Tests first (proposal): doc 57 CL4 (each auxiliary request starts with the base request's bytes) and CL5 (template renders);
  a repair capsule golden per layout; an advisory finding is never sent as a repair.

## Affected docs

Doc 25 §7.2; doc 51 (§4.6, V10, §6.1 item 9); doc 57 (§3.6, §4.3, §5.1, §6.1, §6.3); doc 61 (§4.6, §5, §6); doc 62 (§6.9, §10);
`docs/architecture/agent-runtime.md` §6; D011; DG016; DG021; DG049.

## Decision record

Open.

## Verification notes

### Filing (2026-09-28)

- Filed from doc 51 §6.1 item 9, doc 57 TE-G3, doc 61 §6 items 1, 3, 7 and 13, and doc 62 §10 item 8 (deduplicated into one request),
  re-reading doc 25 §7.2, doc 51 §4.5–§4.6 and V10, doc 57 §3.6, §4.3, §5.1 and §6.3, doc 61's TG table and doc 62 §6.9 on
  2026-09-28. No measurement was run.
