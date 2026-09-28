# D054: A review stage for creative steps: advisory, opt-in by effort

> **Status:** accepted · **Decided by:** owner delegation (2026-09-28, lightly edited: "Go ahead without the GPG passphrase. I will not
> be near the PC for hours. We are working remote"; "Tiny models with no cloud availability should be tested directly on PC. Either
> way, except for GPG signing, we can do everything else"; for a choice between design options, "Figure out the best option for this
> use case"); decided under the owner's delegation; the owner may overrule it on return · **Decided:** 2026-09-28 · **Recorded:**
> 2026-09-28
> **Scope:** model review of already-admitted candidates in creative steps (briefings, dialogue, scenes): who reviews, when, what it
> may return and how it is shown (DG041 option B). **Refines:** D024 item 4 (a `reviewer` role joins the closed role list); D025 (no
> new step kind: the review is a key of `sample`); D026 (the cost preview includes the review). **Related:** D009, D010, D023, D049,
> D051; DG041; docs 21, 25, 38, 56 and 59.
> **Open parts:** which milestone implements it (the roadmap's call; this record does not put it in v1 scope); the closed list of
> concern codes; the review `DecisionKind` and its qualification bar; the `review` key's shape in doc 38 §3.3.

## Context

- Doc 25 §7.3 item 3: creative steps have no voting; code orders candidates by deterministic signals, "optionally by an advisory
  judge", and the user picks in interactive modes. §2.5: "A model judge may order candidates, labelled advisory; it never admits one";
  principle 4: "Acceptance is deterministic." Doc 38 §3.3's `rank` leaves that judge unspecified.
- Doc 21 §1.4 rejects a model judge as an acceptance gate; doc 56 §9 rejects voting across different models, and its tension 4
  accepts LLM grades only if they never gate admission or badges alone (D054 applies it strictly, rule 5); doc 59 §2.7 (evidence)
  and §4.2: never use a model as its own verifier.
- D024 item 1: effort is a budget and never changes the checks. D026 decision 3: no paid judge by default.
- DG041 records the shape discussed with the owner ("for strong models, opt-in by effort") and recommends B. Decided under the
  owner's delegation, as the decisions README's "owner delegation" kind (the practice that follows from D049) asks when one option
  is sound.

## Decision

1. **Option B of DG041: a review stage inside `sample`**, with no new step kind, under all five rules of DG041's recommended
   resolution:
   1. the review never admits, rejects, edits or repairs a candidate; admission stays with the verifiers (doc 25 principle 4);
   2. it is off by default and runs only at Thorough or Max, only for creative `DecisionKind`s, and only with a reviewer setup the
      user bound; the plan card shows its calls and cost before the run;
   3. one reviewer may reorder the admitted candidates, as doc 25 §7.3 allows an advisory judge to; with several reviewers the notes
      are shown side by side and code's deterministic order stays the default, so no vote across models arises (doc 56 §9);
   4. a reviewer returns typed concern notes from a closed list of codes, shown as a model's notes, never as findings or causes
      (doc 59 §7 item 5), and dismissible;
   5. a reviewer setup is qualified for its review `DecisionKind` like any other step, and LLM grades never gate admission or badges
      (doc 56 §9 tension 4, applied strictly).
2. **A `reviewer` role** joins D024 item 4's closed list, as D051 item 9 added `planner`. It is bound by the user and is never the
   writer's own setup: binding the setup that wrote the candidates as their reviewer is refused.
3. **Tests first** (DG041): a property test that no reviewer output changes which candidates are admitted; the review never runs
   below Thorough or without a bound reviewer; binding the writer's own setup as its reviewer is refused; with two reviewers the
   default order equals code's deterministic order.

## Alternatives considered

| Option (DG041) | Why not chosen |
| --- | --- |
| A: deterministic ranking and the user's pick, the advisory judge left unspecified | Strong setups add no review; the judge has no role, cost line or display |
| C: a thirteenth step kind, `panel`, with B's rules | Amends D025 decision 2 for behaviour B gets inside `sample` |
| D: reviewer concerns become repair findings sent to the writer | Repairs carry code-written findings (doc 25 §7.2); doc 25 §2.5 allows "a 'concerns' note only"; a model's opinion would become an acceptance lever |

## Consequences

- Advisory by construction, so effort may enable it without changing the checks (D024 item 1), and it is never a default cost (D026
  decision 3): a review adds calls only when the user binds a reviewer and picks Thorough or Max.
- Friction (D049): one optional binding and dismissible notes; no card or wait is added to a run.
- Folding steps, not done here: doc 25 §7.3 item 3; doc 38 §3.3 (`sample` gains `review`), §5.2 (plan card) and §5.3 (inspector).
  D024, D025 and D026 carry dated notes.

## Sources

DG041; doc 25 (§2.5, §7.2, §7.3); doc 38 (§3.3, §5.2, §5.3); doc 21 §1.4; doc 56 §9; doc 59 (§2.7, §4.2, §7 item 5); D024; D025;
D026; D051; the owner's delegation of 2026-09-28.
