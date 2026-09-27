# D024: Effort, autonomy and role binding are three separate dials

> **Status:** accepted · **Decided by:** owner (DG013, what waits for a click) and research (doc 21 §7, the dials) · **Decided:**
> 2026-09-27 · **Recorded:** 2026-09-27 · **Scope:** every Wilco request and workflow run. **Related:** D006, D009, D023, D025, D026.
> **Open parts:** DG016 (budget and repair accounting), DG020 (reasoning-effort table), DG022 (same-model escalation), DG008 (whether
> `effort_at_least` survives in `when`).

## Context

Docs 25 §5.2 and 14 §8 let effort decide how often the user is consulted; doc 21 §7.3 gave that job to autonomy; doc 38 did both at once
(doc 38 OQ12). A user could not predict whether a Quick run would stop to ask about the premise (DG013).

## Decision

1. **Effort is a budget.** It sets the shape ceiling, candidates K, repairs R, verification depth, retrieval budget, provider reasoning
   and model turns (doc 21 §7.1). **Effort never changes the checks and never changes what waits for a click.**
2. **Autonomy alone governs every wait for a click** (DG013 option B):

   | Level | What happens (doc 21 §7.3) | Default creative check-ins |
   | --- | --- | --- |
   | Ask | Read-only: questions, explanations, lints, teaching | — |
   | Propose | Checked proposals appear as ghosts and a diff; the user applies them | Every stage |
   | **Confirm** (default) | An edit the user asked for lands as one highlighted undo group; plans are approved once; batches that delete, move or exceed a size threshold wait for one click | Premise, outline, end |
   | Auto | Opt-in per session; same caps and checks; one undo group per step; never launches Preview, applies idea cards or accepts a plugin's first egress | End only, with seeded defaults shown as assumption chips |

3. A **per-run "check-ins" choice** on the plan card (end only / premise and outline / every stage) overrides the autonomy default for
   that run. **Safety waits** (approving writes and deletions, launching Preview, plugin egress) always follow autonomy exactly.
4. **Role binding is explicit.** Roles are `router`, `writer`, `scripter`, `explainer`, `play-tester` and `translator`. The user binds
   each to a configured model; an unbound role shows "unassigned" and its steps follow their failure route. The run record stores each
   step's model setup, and a step never runs on a setup other than the one shown (doc 21 §7.2).

## Alternatives considered

| Option (DG013) | Why not chosen |
| --- | --- |
| A: effort decides consultation | Two dials would control waiting; Confirm + Quick would behave unlike Confirm + Thorough |
| C: `approve` gates follow effort, `ask` steps follow autonomy | Hard to explain; the contradiction doc 38 OQ12 records |

## Consequences

- A load-time lint refuses `when = { effort_at_least … }` on `ask` and `approve` workflow steps (DG013).
- Doc 25 §5.2's "User gates" row moves into the autonomy table; doc 14 §8's "Human gate" column points to doc 21 §7.3; doc 38's
  `s3-approve` drops its `when` (folding step).
- Effort presets show their cost on the plan card before a run (D026). Quick is not silent by default; users choose silence with the
  check-ins choice or Auto.

## Sources

DG013; doc 21 (§7.1–§7.3); doc 25 §5.2; doc 14 §8; doc 38 (§3.1, §5.2, §5.4, §8.1, OQ12).
