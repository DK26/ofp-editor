# D031: Generated-content permission, docs and SDK licences, GPL-3.0-only code

> **Status:** accepted · **Decided by:** owner (OWQ-01 to OWQ-04) · **Decided:** 2026-09-27 · **Recorded:** 2026-09-27
> **Scope:** the GPLv3 §7 additional permission in `NOTICE`; the licence of `docs/`, of the plugin SDK, WIT files and test kit; porting
> third-party GPL-3.0-only code. **Refines:** D001 (its open parts OWQ-01 to OWQ-04) and D007 (its open part OWQ-03).
> **Related:** D014, D032, D033, D038.
> **Open parts:** the legal review before 1.0 (doc 02 §11 step 9); DG018 (port records and the per-file licence marker); the SDK
> licence is looked at again at doc 22's MVP step 3 only if plugin authors ask.

## Context

- D001 made the whole workspace `GPL-3.0-or-later` with no permissive lane and left four licence questions to the owner.
- Without an explicit permission, a mission that embeds Plotroom's template scripts could arguably be GPL-bound. That doubt scares
  mission makers, who often mix in APL-SA game content; "plain program output is not covered" does not remove it (doc 02 §6.2).
- Doc 02 §6.4 offered CC-BY-SA-4.0 for docs. Doc 22 (TL;DR, §5) recommended `MIT OR Apache-2.0` for the SDK, WIT and test kit. Doc 45
  found GPL-3.0-only projects worth studying (Twine; OpenRA's map server) and asked how a port would be marked (OQ10).

## Decision

1. **Generated-content permission (OWQ-01, option b).** `NOTICE` carries the doc 02 §6.2 draft with "Plotroom" filled in, plus an
   explicit list of covered output: compiler and module lowerings, generated scripts and glue, finishers, AI-written text, and
   first-party pack content copied into missions. The exclusion of material derived from Bohemia's CWR source stays. The wording passes
   a legal review before 1.0.
2. **Docs (OWQ-02, option a).** Prose under `docs/` is `GPL-3.0-or-later`, like everything else: one licence, the simplest REUSE setup,
   and Standing Orders text moves between docs, skills and the app without a licence boundary. Quoted third-party text keeps its own
   licence and is marked or kept short (doc 02 §6.4).
3. **Plugin SDK, WIT files and test kit (OWQ-03, option a).** `GPL-3.0-or-later` for now. Revisit at doc 22's MVP step 3 (T1 WASM with
   the SDK and conformance kit) only if plugin authors ask for a permissive interface.
4. **GPL-3.0-only third-party code (OWQ-04).** Not ported by default: Plotroom re-implements the ideas in its own code. Only when no
   reasonable re-implementation exists may a GPL-3.0-only file be ported, case by case, with the owner's sign-off, a port record and a
   per-file licence marker (DG018).

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| The doc 02 §6.2 draft without a coverage list (OWQ-01 a) | Leaves lowerings, finishers, AI-written text and pack content open to doubt |
| No permission; rely on "program output is not covered" (OWQ-01 c) | The doubt that deters mission makers remains (doc 02 §6.2) |
| CC-BY-SA-4.0 for docs (OWQ-02 b) | A second licence, and a boundary for Standing Orders text that also ships in skills and the app |
| A narrow permissive exception for interface-only artefacts (OWQ-03 b) | Registry T1 plugins must be GPL-3.0-compatible anyway (D007 item 5), so a GPL SDK costs their authors little now |
| Porting GPL-3.0-only code freely (OWQ-04 c) | The combined work would become distributable under GPLv3 only, ending "or later" (doc 02 §4.3) |

## Consequences

- `CONTRIBUTING.md` states that contributions are licensed `GPL-3.0-or-later` including the project's §7 additional permissions (D032);
  without that, the permission could not cover contributed templates (doc 02 §6.2 constraints).
- Templates, snippets and lowerings copied into user output stay original work, never translated from CWR or CWR-CE (D001 item 5).
  The coverage list doubles as the checklist for template and module authoring rules.
- REUSE headers for docs use `GPL-3.0-or-later`; `LICENSES/` needs no CC-BY-SA text for docs and no MIT or Apache text for an SDK
  (doc 02 §10.1 changes in the folding step). Third-party pack content keeps its own licence (D038 item 3).
- Adding any plugin exception later needs the consent of every affected contributor unless `CONTRIBUTING.md` grants it in advance
  (doc 22 §5 item 6).
- A ported GPL-3.0-only file keeps its own SPDX identifier; while one ships, the combined program is distributable under GPLv3 only,
  and its port record says so.
- The About box and `NOTICE` show the permission with the other legal notices (doc 02 §10.6). Not legal advice; doc 02 governs.

## Sources

Doc 02 (§4.3, §6.2, §6.4, §10.1, §10.5, §10.6, §11, open question "Docs license"); doc 22 (TL;DR, §5, §7.1); doc 45 (source table
rows 9 and 15, OQ10); `OWNER-QUESTIONS.md` OWQ-01 to OWQ-04; D001; D007.
