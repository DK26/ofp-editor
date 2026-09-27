# D004: v1 scope: faithful editor, Preview, Wilco and the campaign flow

> **Status:** accepted; sizing open → sizing accepted (2026-09-27; see D036) · **Decided by:** owner · **Decided:** 2026-09-26 (the
> campaign flow was made first-class the same day) · **Recorded:** 2026-09-27 · **Related:** D005, D006, D009, D015, D018, D023, D024.
> **Open parts:** OWQ-13 (size of the v1 campaign flow), OWQ-14 (v1 modules, CLI, Standing Orders and Drill, locales), OWQ-15 (external
> agents over MCP); all three answered 2026-09-27 → D036.

## Context

- The original editor (top-down map, F1–F6 modes, its dialogs) is what the community knows; its pain points are listed in doc 09 and
  its behaviour in docs 03 and 05.
- The owner first scoped the campaign designer as "import and preserve in v1, full designer later", then made describe → generate →
  edit campaigns a primary purpose of the editor (`AGENTS.md`). Doc 34 OQ6 records v1 = editor + Preview + AI co-pilot + campaign flow.

## Decision

v1 contains four things:

1. **A faithful editor.** Visually and behaviourally true to the original (map, modes, dialogs, the Easy/Advanced switch per D029), with
   modern safety nets: undo, non-blocking validation, integrated script and briefing editing, and lossless load and save of existing
   missions (D017).
2. **Preview in the real game** (D018).
3. **Wilco, the optional AI co-pilot.** Off by default; bring your own model, cloud or local (D023); product-scoped (D006); Confirm
   autonomy by default (D024); everything it makes is glass-box (D010).
4. **The describe → generate → edit campaign flow, first-class.** A typed, verified, editable campaign model (doc 19) that a user can
   describe, generate and refine piece by piece. A run without any model produces a valid campaign with template text (D009).

Every v1 feature works with AI off; the no-model path is the baseline each AI feature must beat (doc 21 §1.1 rule 7).

## Alternatives considered

- Editor and Preview only, AI later: drops the product's differentiator and the owner's campaign goal.
- Campaign import/preserve in v1 and generation in v1.x (the owner's first scoping): replaced the same day by the first-class invariant.
- An AI-first product with a thin editor: contradicts "same path as the user" and the glass box (`AGENTS.md`).

## Consequences

- The roadmap shows the path from v1 to the north star (D005).
- Not v1 commitments until the owner answers: how large the v1 campaign flow is (classic patterns only, or the strategic layer too,
  OWQ-13); which doc 31 modules ship, whether the headless `plotroom` CLI ships, and Standing Orders/Drill content and locales (OWQ-14);
  whether the MCP server for external agents ships (OWQ-15).
- T1 WASM plugins, the pack registry and multiplayer Preview follow their own phase plans (doc 22 §7 MVP; doc 42 RG0–RG3; doc 08 P4)
  and are not implied by this record.
- The v1 campaign flow runs on the workflow runtime (D025), not on a bespoke stage enum (doc 38 §4.7).

## Sources

README; `AGENTS.md` (campaign invariant); doc 03; doc 05; doc 09; doc 19 TL;DR; doc 21 §1.1; doc 25 TL;DR; doc 34 OQ6 and its
verification notes; doc 38 §4.7.

## Amendment notes

### 2026-09-27: the owner's sizing answers (OWQ-13, OWQ-14, OWQ-15)

The "sizing open" parts of this record are answered in `OWNER-QUESTIONS.md`; the four things above are unchanged. Where a later
record restates these answers, that record governs.

- **Campaign flow (OWQ-13 (a)).** v1 ships the typed campaign model, Plotline, the Tote, Path Explorer, import and preserve, and
  describe → generate → edit for the classic patterns, with a no-model path. The strategic layer and "Operation Grey Heron" (D005) are
  the first milestone after v1 (roadmap v1.1).
- **Modules, CLI, Standing Orders and Drill (OWQ-14 (a)).** The doc 31 wave-1 modules whose probes pass on `Cwr`; a minimal headless
  `plotroom` CLI (lint, compile/export, round-trip check, golden-journal replay; no agent); Standing Orders seed entries and Drill
  track A in English first, other locales as native reviewers join.
- **Cinematics, rung 4 (OWQ-14 (a)).** v1 ships the Cutscene-node recipe with camera scripting through the script editor; the doc 32
  timeline and the doc 39 cutscene director ship in v1.2.
- **External agents (OWQ-15 (a)).** The opt-in, loopback-only MCP server ships in v1; decision points are answered only in the editor;
  `workflow.decide` for external agents comes after v1, journaled with an external origin and excluded from model qualification.

### 2026-09-27: pointer to D036

D036 states the answers above as a record and governs where the wording differs. The header gained pointers; nothing else above
changed.
