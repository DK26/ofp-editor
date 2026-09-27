# DG013: User gates: set by effort or by autonomy

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **decided** (owner, 2026-09-27): autonomy (Ask / Propose / Confirm / Auto) alone governs every wait-for-click, plus a per-run "check-ins" choice on the plan card; effort only changes budgets. The recommended resolution below is adopted.
> **Decision by: owner** (how often Wilco stops to consult the user is a product choice between speed and "the user stays the
> director"). Blocks: `approve` and `ask` step semantics in doc 38, the plan card's gate options, `core/campaign-from-brief`.

## Context

- **Doc 25 §5.2** effort table has a **User gates** row: Quick "End of run"; Standard "Premise, outline, end"; Thorough "Every
  stage"; Max "Every stage + candidate comparison". Its heading: "Effort changes how hard the harness tries and how often the user is
  consulted."
- **Doc 14 §8** also maps effort to a **Human gate** column (Quick: preview change-set … Max: side-by-side diff of alternatives).
- **Doc 21 §7** calls effort, role binding and autonomy "three separate dials". §7.1's effort table (extending doc 25 §5.2) has no
  gate row; §7.3 makes waiting an autonomy matter: Ask, Propose, Confirm (default; plans approved once, large or destructive batches
  wait for a click), Auto (opt-in; never launches Preview, applies idea cards or accepts a first plugin egress).
- **Doc 38 §5.4** maps autonomy to plan card, `ask`, `approve` and `commit`; **§8.1** uses `when = { effort_at_least = "standard" }`
  only on the `s3-approve` gate, while `s1-choose` (an `ask`) runs at every effort. OQ12 records the contradiction; §5.2 lets the plan
  card's typed Edit change "optional gates".
- Doc 25 §3 principle 7 and `AGENTS.md` ("Fun is a requirement … the user stays the director") favour short interactive loops.

## The gap

Three docs say effort decides how often the user is consulted; one says autonomy does; the workflow format does both at once. A user
cannot predict whether a Quick run will stop to ask about the premise.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | **Effort decides** consultation (doc 25 §5.2, doc 14 §8); autonomy only decides whether writes wait | "Quick" is really quick and silent | Two dials both control waiting; Confirm plus Quick behaves unlike Confirm plus Thorough, surprising users |
| B | **Autonomy decides** everything that waits for a click (doc 21 §7.3); effort never does. A per-run "check-ins" choice on the plan card (end only / premise and outline / every stage) overrides the autonomy default for that run | One rule; effort stays a pure budget as doc 21 §7 intends; the user sets consultation explicitly | Quick is no longer silent by default; one more choice on the plan card |
| C | **Split by kind** (doc 38 today): `approve` gates follow effort, `ask` steps follow autonomy | No doc text changes much | Hard to explain; the contradiction OQ12 records |

## Recommended resolution (proposal)

Option B. Safety waits (approving writes, deletions, Preview, plugin egress) follow autonomy exactly as doc 21 §7.3 and doc 38 §5.4
say. Creative check-ins (premise pick, outline review, candidate comparison) default from autonomy (Confirm: premise, outline, end;
Propose: every stage; Auto: end only, with seeded defaults shown as assumption chips) and can be changed per run on the plan card.
Effort never changes what waits. A load-time lint refuses `when = { effort_at_least }` on `ask` and `approve` steps. Doc 25 §5.2's
"User gates" row moves out of the effort table into the autonomy table.

## What it would change

- Doc 25 §5.2: the row and the heading sentence ("…and how often the user is consulted") move to an autonomy note.
- Doc 14 §8: the "Human gate" column points to doc 21 §7.3.
- Doc 21 §7.3: a check-in default per autonomy level; §7.1 unchanged.
- Doc 38 §3.1, §5.2, §5.4, §8.1 and OQ12: `s3-approve` drops `when`; the plan card lists the check-in choice; a lint refuses
  effort predicates on waiting steps.

## Affected docs

Docs 14, 21, 25, 38; DG008 (whether `effort_at_least` survives in `when`).

## Decision record

- **Decided:** 2026-09-27. **By:** the owner. **Chosen:** option B, as recommended above. The durable rule is recorded as
  [D024](../decisions/D024-effort-autonomy-role-binding.md) (items 1–3), which this section summarises.
- **Rule.**
  1. **Effort is a budget** (shape ceiling, candidates K, repairs R, verification depth, retrieval budget, provider reasoning, model
     turns; doc 21 §7.1). It never changes the checks and never changes what waits for a click.
  2. **Autonomy alone governs every wait for a click.** Default creative check-ins per level: Ask, none (read-only); Propose, every
     stage; **Confirm** (default), premise, outline and end; Auto, end only, with seeded defaults shown as assumption chips.
  3. A **per-run "check-ins" choice** on the plan card (end only / premise and outline / every stage) overrides the autonomy default for
     that run. **Safety waits** (approving writes and deletions, launching Preview, plugin egress) always follow autonomy exactly.
  4. A load-time lint refuses `when = { effort_at_least … }` on `ask` and `approve` workflow steps.
- **Reason.** One rule that users can predict; effort stays the pure budget doc 21 §7 intends; the user sets consultation explicitly.
  Option A would give two dials control over waiting (Confirm + Quick would behave unlike Confirm + Thorough); option C is the
  contradiction doc 38 OQ12 records. Consequence the owner accepted: Quick is not silent by default; users choose silence with the
  check-ins choice or Auto.
- **Still open.** Whether `effort_at_least` survives in `when` at all is DG008's call (D024 "Open parts").
- **Folding (what moves this request to `folded`).** The edits listed under "What it would change": doc 25 §5.2 (the "User gates" row
  and heading sentence move to an autonomy note), doc 14 §8 (the "Human gate" column points to doc 21 §7.3), doc 21 §7.3 (check-in
  defaults per level), doc 38 §3.1, §5.2, §5.4, §8.1 and OQ12 (`s3-approve` drops `when`; the plan card lists the check-in choice; the
  lint). Doc 39 §8 already states the decision (verification note below).

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 25 §3 and §5.2, doc 14 §8, doc 21 §7.1–§7.3, doc 38 §3.1, §5.2, §5.4, §8.1 and OQ12, re-read on 2026-09-27.
- *Docs 39, 41 and 43 step (2026-09-27).* Doc 39's `core/make-cutscene` workflow has an `approve` step for the take, and its §8 had
  "batch runs keep code's top-ranked take". §8 now states the decision: whether `approve` waits follows autonomy and the run's
  check-ins, never effort; when it does not wait, code's top-ranked take is kept. Docs 41 and 43 define no waiting steps. Doc 39 is
  not in this request's affected list and needed only that sentence.

### Owner answers (2026-09-27)

- The header said **decided** while the decision record still read "Open" (found by the consistency review). The record is now
  filled from D024, which was re-read for this step; no decision changed. Docs 14, 21, 25 and 38 were not edited.
