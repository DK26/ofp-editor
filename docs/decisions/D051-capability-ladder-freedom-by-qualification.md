# D051: Knowledge lives in the harness; models earn freedom by qualification

> **Status:** accepted · **Decided by:** owner (direction of 2026-09-28; go-ahead of 2026-09-28 for doc 63's draft record and its
> recommended options) · **Decided:** 2026-09-28 · **Recorded:** 2026-09-28 · **Scope:** how large a step each model setup may take,
> and how it reaches knowledge. **Refines:** D024 items 1 and 4, D025 decision 1 (after v1; see its note), D027 item 2 (see its
> note), D037 (badges), D045 item 4, D048 item 2. **Related:** D006, D009, D010, D023, D044, D050. **Open parts:** the level names (D034
> item 3), the effort ceiling row and the product ceilings above FR0 (doc 63 §4.2, §6), trial counts and budgets (doc 63 §4.3,
> §4.5; [OWQ-29](OWNER-QUESTIONS.md), open); design-gap candidates 1–12 (doc 63 §13), filed where this record leaves them open as
> DG042 (items 9–10, the `PlanDraft` mechanics), DG044 (item 3), DG053 (item 6), DG054 (item 2, stakes floors) and DG055 (item 7, the
> grant witness's name and crate; doc 62 §6.3), the rest mapped in the design-gap README's "Candidates not filed (2026-09-28)"; doc 63
> OQ6–OQ10 (OQ5, compile-fail tests, is answered by `AGENTS.md`'s "Negative Compile Tests").

## Context

- The owner's direction of 2026-09-28 (lightly edited): "Encode all knowledge and know-how into the harness; more powerful models
  could go even crazier and be granted more freedoms." Doc 63 answers it with a ladder of freedom levels and a draft record (§14).
- D009 already lets stronger models take larger steps while no workflow may require one; doc 21 §3.3 grants shapes by
  qualification. Missing were levels finer than Pick, Fill, Compose and Draft, ceilings no model can lift, pull rules and a view for
  the user (doc 63 TL;DR). Facts stay code-owned even for the strongest model (doc 30 §3.4; doc 53 DP-08, DP-16).
- The owner's go-ahead of 2026-09-28 (lightly edited): "Tiny models with no cloud availability should be tested directly on PC.
  Either way, except for GPG signing, we can do everything else." **Recommended option adopted under the owner's go-ahead; overrule
  on return.**

## Decision

1. **Knowledge and know-how live in the harness**, once, independent of the model: facts in catalogs and Teller, rules in cards and
   checkers, craft in lenses and lints, procedures in workflows and recipes, patterns in macros and modules. What a strong model
   teaches is absorbed as reviewed data, never as model memory or weights.
2. **Freedom levels FR0–FR8** (working codes; doc 63 §2.1): no model, one-pass Pick, guided Pick, field Fill, whole record, Compose,
   Draft, scene draft, plan. **Effective level = min(product ceiling, qualified level, effort ceiling, the user's per-role cap).**
   An unqualified setup runs FR2, with FR4 only as a pre-fill the user confirms.
3. **Product ceilings.** Each `DecisionKind` declares the highest level it allows; no preset, grant or setting raises it.
   Fact-bearing Picks and free-text engine knowledge stay at FR0.
4. **Earned per step kind.** A grant belongs to (setup, harness preset, `DecisionKind`, level, domain: profile, language, mod-set
   class); only qualification at that level's bar, beating the next-lower level on the same cases, sets it; DG012's triggers void it.
   A D044 cloud screen never sets a grant.
5. **Push always, pull by grant.** Code pushes the step's knowledge at every level. Read-only lookup, navigation and check tools come
   from FR5 by grant, and only at Thorough or Max effort (doc 30 §4.3). Weak models never fetch.
6. **Down automatically, up by the user.** A failed or over-budget step keeps its admitted parts and splits down along its authored
   decomposition. The level never rises mid-run; a larger step or a stronger model is a priced button.
7. **The floor holds at every level** (doc 63 §5): product scope, the command path, the same checks, code-owned facts and "done",
   pinned-field ownership, no silent switch, the glass box, untrusted text as data, typed consent, budgets that only tighten,
   draft-first, no self-grading, model-written memory or stored reasoning text.
8. **Visible, no new dial.** The plan card shows how each step is asked; Settings shows a grid of badges per level and
   `DecisionKind` family; a per-role "largest step" cap only lowers. No per-level approval prompts.
9. **Plans as data, after v1 (doc 63 §8.7 option B; OQ1–OQ3).** After v1, a `planner` role (added to D024's list, behind an FR8
   grant) may **propose** a workflow as data (`PlanDraft`) built only from registered units, reached only from
   `Dispatch::NotSupported`; the definition compiler checks it; it runs only after the user saves it as their own workflow, with a
   click that carries `UserIntent`, in Auto too. There is no "run once, don't keep". Wilco never saves a definition itself.

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| One shape per model tier | Ignores measured per-kind differences (doc 55) |
| Let strong models supply facts | The frontier model missed an engine rule (doc 30 §3.4); DP-08 and DP-16 have no model fix |
| A fourth "freedom" dial | D024 keeps three dials; the level lives in effort's shape ceiling and role binding |
| No FR8 (§8.7 A) | Leaves the owner's "go even crazier" unanswered where no workflow fits |
| FR8 for external agents only (§8.7 C) | No in-app capability; a weaker glass box for in-app users |
| Model-written scripts as plans | Rejected (doc 59 §4.5); a plan is typed data the loader validates |

## Consequences

- D023 decision 3 is unchanged: down-only mid-run, and a stronger model is a visible choice. D037 badges and D045 item 4 gain the
  level; a D048 preset may lower a level, never raise it or a product ceiling. Pointer notes on D024, D037, D045 and D048 are
  folding steps, not done here; D025 and D027 carry notes.
- A `PlanDraft` adds no step kind (doc 38's closed set stays); its `when` may test only inputs, `ask` answers and trusted code
  outputs; at most about 12 units; nested steps keep their own grants, with no transitivity.
- Friction (D049): no new dial or per-level prompt; saving a plan is one deliberate click, kept for consent.
- Folding steps: doc 21 §3.1 and §7.1, doc 25 §5, doc 30 §4.2–§4.3, doc 38 §2, the agent-runtime (§2, §7, §9), doc 63's status.

## Sources

Owner direction and go-ahead of 2026-09-28; doc 63 (TL;DR, §2, §4–§8, §13, §14, open questions); doc 62 §6.3; docs 21 (§3.3,
§12.3), 30 (§3.4, §4.3), 53, 55; D009; D023; D024; D025; D027; D037; D044; D045; D048.
