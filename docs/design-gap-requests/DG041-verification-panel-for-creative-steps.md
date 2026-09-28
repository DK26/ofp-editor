# DG041: A verification panel for strong models on creative work, opt-in by effort

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-28 under the owner's go-ahead of 2026-09-28 ("Either way,
> except for GPG Signing, we can do everything else"), as one of three dynamic-workflow additions discussed with the owner (DG040,
> DG041, DG042). Status: **decided** (owner's delegation, 2026-09-28): option B → D054. An advisory review stage inside `sample`, off
> by default, only at Thorough or Max with a user-bound `reviewer` setup that is never the writer's own. Not yet folded.
> **Decision by: technical** (design round); **owner** for adding a reviewer role to D024 item 4's closed role list, as D051 item 9
> did for `planner`. Blocks: any model review of creative candidates beyond doc 25 §7.3's optional advisory judge; doc 38 §3.3's
> `rank` keeps its unspecified "optional advisory judge" until decided.

## Context

- **Doc 25 §7.3 item 3.** Creative steps have no voting: code orders candidates by deterministic signals, "optionally by an advisory
  judge whose position/self-preference biases are known", then shows the top 2–3 to the user in interactive modes or takes the top
  one in batch modes, marked "AI draft, unreviewed". **§2.5**: LLM judges show "position, verbosity, and self-enhancement biases" and
  favour their own generations; "A model judge may order candidates, labelled advisory; it never admits one". Its adoption table:
  model self-critique and model judges are "advisory ordering or a 'concerns' note only; never acceptance". Principle 4: "Acceptance
  is deterministic."
- **Doc 38 §3.3.** `sample.select = "rank"` means "deterministic signals, optional advisory judge".
- **Doc 21 §1.4** rejects a model grading or accepting its own output and "a model judge as an acceptance gate (it may only order
  checked candidates)". **Doc 56 §9** lists "voting across different models" among rejected designs, and its tension 4 accepts LLM
  grades only if they never gate admission or badges alone. **Doc 59 §2.7**: never use a model as its own verifier.
- **D024 item 1.** Effort is a budget (K, R, verification depth, provider reasoning) and "never changes the checks". **D026
  decision 3**: no "paid judge by default". **D023 decision 3, D024 item 4**: every model a step uses is bound by the user and shown.
- **D051; doc 63 §4.2.** Prose, dialogue and briefings are asked at FR4 alone or FR7 inside a scene draft; strong setups earn larger
  steps, and "bigger steps buy coherence, fewer calls, lower latency and delight, not correctness" (doc 63 TL;DR).

## The gap

Strong models writing briefings, dialogue or scenes produce candidates that pass every deterministic check but differ in craft:
tone, continuity with the story bible, era voice. The only model-side review the format allows is an unspecified advisory judge
inside `rank`. Nothing defines which role reviews, which setup, at which effort, what it may return, how its notes are shown, what it
costs, or how a review by several models (a "panel") avoids the rejected vote across models.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Today: deterministic ranking plus the user's pick, with the advisory judge left unspecified | Nothing new | Strong setups add no review; the judge has no role, cost line or display |
| B | A review stage inside `sample` (no new step kind): at Thorough and Max only, and only when the user has bound a reviewer setup, reviewers read the already-admitted candidates and return typed concern notes from a closed list of codes, and at most one reviewer may reorder; several reviewers' notes are shown side by side, never merged into a vote; a reviewer is never the setup that wrote the candidates; the plan card prices it; off by default | Advisory by construction, so effort may enable it without changing the checks (D024 item 1); never a default cost (D026); fits doc 25 §7.3 and doc 38's `rank` | Needs a reviewer role (owner) and a qualified review `DecisionKind` |
| C | A thirteenth step kind, `panel`, placed after a creative step, with B's rules | Its own row in the plan card and run graph | Amends D025 decision 2 for behaviour B gets inside `sample` |
| D | Reviewer concerns become repair findings sent back to the writer | Turns review into better text | Repairs carry code-written findings (doc 25 §7.2); doc 25 §2.5 allows "a 'concerns' note only"; a model's opinion becomes an acceptance lever |

## Recommended resolution (proposal)

B, the shape discussed with the owner ("for strong models, opt-in by effort"), with these rules:

- The review never admits, rejects, edits or repairs a candidate; admission stays with the verifiers (doc 25 principle 4).
- It runs only at Thorough or Max, only for creative `DecisionKind`s, and only with a reviewer setup the user bound; the plan card
  shows its calls and cost before the run.
- One reviewer may reorder the admitted candidates, as doc 25 §7.3 allows an advisory judge to; with several reviewers the notes are
  shown side by side and code's deterministic order stays the default, so no vote across models arises (doc 56 §9).
- A reviewer's notes are shown as a model's notes, never as findings or causes (doc 59 §7 item 5), and are dismissible.
- A reviewer setup is qualified for its review `DecisionKind` like any other step, and LLM grades never gate admission or badges
  (doc 56 tension 4).

C is the alternative if the design round wants the review as its own row badly enough to amend D025 decision 2; D is not
recommended because it contradicts doc 25 §2.5 and §7.2.

## What it would change

- Doc 25 §7.3 item 3 and doc 38 §3.3 (`sample` gains a `review` key); D024 item 4 (a reviewer role, owner); the plan card (doc 38
  §5.2) and inspector (§5.3) show the review; D026's cost preview includes it.
- Tests first (proposal): a property test that no reviewer output changes which candidates are admitted; the review never runs below
  Thorough or without a bound reviewer; binding the writer's own setup as its reviewer is refused; with two reviewers the default
  order equals code's deterministic order.

## Affected docs

Doc 25 (§2.5, §7.3); doc 38 (§3.3, §5.2, §5.3); doc 21 §1.4; doc 56 §9; doc 59 §2.7; D024; D025; D026; D051.

## Decision record

- **Decided 2026-09-28 under the owner's delegation: option B → [D054](../decisions/D054-review-stage-for-creative-steps.md).** A
  review stage inside `sample` with all five rules of the recommended resolution above; a `reviewer` role joins D024 item 4's closed
  list (the owner-level part), bound by the user and never the writer's own setup; off by default. Which milestone implements it is
  the roadmap's call, not v1 scope by this decision. The owner may overrule it on return.
- **Reason.** Advisory by construction, so effort may enable it without changing the checks (D024 item 1) and it is never a default
  cost (D026). C amends D025 decision 2 for what B does inside `sample`; D contradicts doc 25 §2.5 and §7.2.
- **Folding (what moves this request to `folded`).** Doc 25 §7.3 item 3; doc 38 §3.3 (`review` key), §5.2 and §5.3. The notes on
  D024, D025 and D026 are done (2026-09-28).

## Verification notes

### Filing (2026-09-28)

- Filed from the owner's dynamic-workflow additions, as the go-ahead of 2026-09-28 allowed. Doc 25 (§2.5, §7.2, §7.3), doc 38 §3.3,
  doc 21 §1.4, doc 56 §9, doc 59 §2.7, D024, D026, D051 and doc 63 §4.2 were re-read on 2026-09-28.
- No research doc proposes a panel. Options B–D are this request's reading of the doctrine above; nothing here is decided.

### Owner delegation, design-gap pass (2026-09-28)

- Decided with the recommended option B under the owner's delegation of 2026-09-28 (quoted in D054), which also covers the reviewer
  role that the header names as the owner's part. D054 was written from this request, doc 25 (§2.5, §7.2, §7.3), doc 38 §3.3, doc 56
  §9, D024, D025, D026 and D051 item 9, re-read on 2026-09-28. Docs 25 and 38 were not edited.
