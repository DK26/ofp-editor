# D010: Nothing the AI makes is a black box

> **Status:** accepted (invariant) · **Decided by:** owner (`AGENTS.md`) · **Decided:** 2026-09-26 · **Recorded:** 2026-09-27
> **Scope:** every element a model, workflow, template or plugin generates. **Related:** D006, D009, D015, D025.
> **Open parts:** DG017 (journal storage, retention, export stripping); DG008 (condition language behind the visual builder).

## Context

`AGENTS.md`, "Nothing the AI makes is a black box", is authoritative. Generated missions and campaigns are only useful if the user can
understand and change them with the tools they already know; hidden generation also hides errors.

## Decision (summary; `AGENTS.md` governs)

1. Every generated element (units, groups, waypoints, triggers, markers, missions, branches, campaign variables, conditions, briefings,
   dialogue lines, scripts) is easy to:
   - **see** in its natural view: the map, Plotline (the campaign graph), the Tote (the state board), a screenplay or a text view;
   - **inspect**: why it exists, which step and which model setup produced it, what depends on it, and its validation status;
   - **edit** with the same native editors as hand-made content.
2. Visual, direct manipulation comes first (drag on the map, rewire in the graph, pick from menus, a visual condition builder); raw text
   is always available.
3. Generated content is ordinary editor objects, never an opaque blob or a hidden runtime framework.

## Alternatives considered

- Shipping generated logic as a hidden script framework inside missions: unreadable in the original editor and impossible to refine.
- Logs instead of inspectors: records what happened but gives the user no way to act on it.

## Consequences

- Provenance is kept per element and per field: origin (user, Wilco step, plugin, template), the model setup, and pinned or edited
  state (doc 25 §9; doc 21 §7.2 run record).
- An inspector per generated element opens its decision record: menu, pick, the model's `why`, verifiers, repairs and dependents
  (doc 25 §9.1). Workflow runs have a plan card, a run panel and a read-only run graph (doc 38 §5).
- Every "why" shown to the user is computed by code; the model only phrases it (doc 36 §5, recommendations for doc 21).
- Each rung of the no-code ladder shows the code it generates (D015; doc 31).
- Conditions have one AST with two views, text and a visual builder (doc 19 §5; DG008).
- Journals and provenance live in the sidecar, and what an export strips is DG017's decision.
- A generated element that cannot be shown in a natural view is a design gap, filed before the feature ships.

## Sources

`AGENTS.md`; doc 19 §5–§6; doc 21 (§5, §7.2); doc 25 §9; doc 31 TL;DR; doc 36 §5; doc 38 §5.
