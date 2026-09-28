# D049: Friction review in every design and implementation change

> **Status:** accepted · **Decided by:** owner (direction of 2026-09-28) · **Decided:** 2026-09-28 · **Recorded:** 2026-09-28
> **Scope:** how Plotroom is designed and built; every audience of the product. **Related:** D009, D010, D024, D045, D048.
> **Open parts:** the friction register's format and first contents (`docs/friction/`, being prepared); how friction measurements
> (steps, waits, confirmations, error rates, tokens) are collected once code exists.

## Context

- The owner's direction of 2026-09-28, in the owner's words: "As we design and implement, we will have to actively notice and think
  about potential frictions and how to reduce or eliminate them."
- Plotroom serves three audiences with different frictions: people using the editor, models using its APIs and tools (Wilco and
  external agents), and contributors and coding agents building it.

## Decision

1. **Friction review is required** in every design and implementation change, for all three audiences. `AGENTS.md` ("Friction
   Review (Required)") states the rule.
2. **Remove before explaining.** Eliminating a step, choosing a safe default or making the wrong input impossible comes before
   documenting a workaround. Friction that cannot be removed is made visible, with the next action explained where it occurs.
3. **Measure where possible:** steps, clicks, waits, confirmations, error and repair rates, and tokens or calls for model-facing flows.
4. **Record it.** Friction found but not fixed goes into a register under `docs/friction/` (audience, severity, evidence, proposed
   removal); design documents note the frictions they introduce or remove.
5. **Invariants stay.** Reducing friction never weakens product scope, typed undoable commands, validation or the glass box.

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| Review friction only in usability testing after implementation | Friction found late is expensive to remove and often becomes a documented workaround |
| Leave it to each contributor's judgement | Friction for models and for contributors is easy to overlook without an explicit duty |

## Consequences

- A friction register is started under `docs/friction/` with an audit of the current design.
- Design reviews and change sets gain a friction check for the three audiences.

## Sources

Owner direction of 2026-09-28; `AGENTS.md` ("Friction Review (Required)"); D009; D010; D024; D045; D048.
