# D009: Campaign creation is first-class; the harness carries the weight

> **Status:** accepted (invariant) · **Decided by:** owner (`AGENTS.md`) · **Decided:** 2026-09-26 · **Recorded:** 2026-09-27
> **Scope:** every AI workflow, above all describe → generate → edit for campaigns. **Related:** D004, D005, D010, D011, D024, D025.
> **Open parts:** DG006 (menu cap 5 or 7), DG008 (one condition language), DG015 (Pick answer schema), DG016 (budget accounting).

## Context

`AGENTS.md`, "Campaign Creation Is First-Class, and the Harness Carries the Weight", is authoritative. Doc 25 gives the reason: a
campaign draft needs roughly 200–300 small decisions, and at 95% success per decision 40 unguarded decisions all succeed only 13% of the
time; models plan and self-verify poorly but work well beside external verifiers (doc 25 TL;DR, with the cited papers).

## Decision (summary; `AGENTS.md` governs)

1. **Describe → generate → edit is a primary purpose.** The result is a typed campaign model (missions, state, transitions) that the
   editor understands, verifies and lets the user refine piece by piece, not a folder of loose files.
2. **Weak models must succeed.** Workflows are typed state machines owned by code. Each model step is one small, bounded decision with a
   typed output. Code owns every fact, computes the valid options, generates bulk content deterministically, validates every model output
   and drives bounded repair loops. The harness, not the context window, holds campaign and mission state.
3. Stronger models may take larger steps, but **no workflow may require one** to be correct.
4. **Correct by construction**: generated content passes the same validators, lints and compilers as hand-made content, so it runs on
   the targeted profile (D003).
5. **Fun is a requirement**: interactive choices, previews, variations and surprises over long silent runs; the user is the director.
6. **Partial regeneration never clobbers human work**: human-edited or pinned content is kept unless the user asks to regenerate it.

## Alternatives considered

- Free-form model plans with self-critique: without external feedback, models "struggle to self-correct" (doc 25 TL;DR).
- A fine-tuned planner: strong in-domain, near zero on unseen domains in the cited study (doc 25 TL;DR); also no help for cloud models.
- Generate files first, lint afterwards: leaves no typed model to refine, and invalid output reaches the user.

## Consequences

- **Step shapes** Pick, Fill, Compose and Draft; each model setup is qualified per shape, and a failed larger step is split into smaller
  ones, never handed silently to a bigger model (doc 21 §3; doc 25 §5).
- **Menus** are code-computed, short, shuffled and neutral-lettered, with `none fit` and `ask me` escapes; long catalog lists become facet
  steps (doc 25 §6.2; the cap is DG006).
- **Compilable from the first minute**: code builds a lint-clean default campaign and the model upgrades pieces one decision at a time;
  a failed decision leaves a flagged default, never a hole (doc 25 §10).
- Consistency lives in a typed story bible whose text stores entity tokens, so renames never need regeneration (doc 25 §8).
- Human edits: per-field provenance, pinning, and a field-level three-way merge keyed by stable ids (doc 25 §9).
- Every quality claim needs an instrument against no-model, random-valid and always-ask controls, and the harness must beat a
  single-prompt baseline (doc 21 §12; doc 25 §11.2).
- Runs execute on the workflow runtime (D025) under the effort, role and autonomy dials (D024).

## Sources

`AGENTS.md`; doc 25 (TL;DR, §3–§11); doc 21 (§1–§3, §12); doc 19 TL;DR; doc 26; doc 29 §6.
