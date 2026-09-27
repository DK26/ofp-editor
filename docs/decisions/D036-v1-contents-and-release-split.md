# D036: v1 contents: classic patterns, probe-cleared modules, a minimal CLI, English first, the MCP server

> **Status:** accepted · **Decided by:** owner (OWQ-13, OWQ-14, OWQ-15) · **Decided:** 2026-09-27 · **Recorded:** 2026-09-27
> **Scope:** what v1.0 ships inside D004's four things, and what moves to v1.1 and v1.2. **Refines:** D004 (its open parts OWQ-13 to
> OWQ-15; D004 stays as written), the OWQ-13 or OWQ-14 open parts of D005, D015 and D028, and the OWQ-15 open parts of D006 and
> D025. **Related:** D042, D043.
> **Open parts:** which wave-1 modules pass their probes on `Cwr` (probe results); which strategic modules join Grey Heron (doc 34 OQ6,
> with v1.1).

## Context

- D004 set v1 = faithful editor + Preview + Wilco + the describe → generate → edit campaign flow, and left its size to the owner.
- Doc 29's strategic layer needs its balance lab and about 20 probes on 1.99 before its rules are final.
- Doc 33 planned five locales from the first release, but no benchmark covers Czech, Polish or Russian creative text (doc 14 TL;DR)
  and every translation needs a native reviewer.
- The cinematics timeline needs the live link, exact terrain height and the CP probes first (architecture README §7 row 28).
- CI and the acceptance tests need a headless entry point anyway.

## Decision

1. **Campaign flow (OWQ-13 a).** v1 ships the typed campaign model, Plotline, the Tote, Path Explorer, import and Preserve, and
   describe → generate → edit for the classic patterns (doc 26 §9.4, P1–P8), with a no-model path. The strategic layer (pattern
   P9) and Operation Grey Heron (D005) are the first milestone after v1.
2. **Modules (OWQ-14 a).** The doc 31 §4.6 wave-1 modules whose probes pass on `Cwr` ship in v1; a module whose probe fails waits.
3. **Headless CLI (OWQ-14 a).** A minimal `plotroom` CLI ships in v1: lint, compile/export, round-trip check and golden-journal replay.
   It has no agent.
4. **Standing Orders and Drill (OWQ-14 a).** The seed entries and Drill track A ship in English first; Czech, Polish, Russian and German
   follow as native reviewers join.
5. **Cinematics, rung 4 (OWQ-14 rung-4 item a).** v1 ships the Cutscene-node recipe, with camera scripting through the script editor.
   The doc 32 timeline and the doc 39 cutscene director ship in v1.2.
6. **External agents (OWQ-15 a).** v1 ships the opt-in, loopback-only, authenticated MCP server: listing and starting workflows, the
   product tools, and the primer as a skill. Decision points are answered only in the editor. `workflow.decide` comes after v1; when it
   ships, external answers are journaled with an external origin and excluded from model qualification.

## Alternatives considered

- Grey Heron in v1 (OWQ-13 b): v1 would wait for the balance lab and the 1.99 probes. Import, Preserve and the graph editor only, with
  generation later (c): contradicts D009.
- A smaller top-ranked module set (OWQ-14 b): the probe gate already removes what cannot be shown to work.
- No CLI: CI and acceptance tests would have to drive the GUI.
- All five locales at release: the release would wait on reviewers, or ship unreviewed text.
- The timeline in v1 (rung-4 b), or timeline and director both (c): their engine prerequisites are not in place.
- `workflow.decide` in v1 (OWQ-15 b): its effect on qualification data is unmeasured; no MCP server (c): drops an exposure that
  `AGENTS.md` allows because it adds no capability.

## Consequences

- Roadmap: v1.0's definition of done follows items 1–6; v1.1 is the strategic layer and Grey Heron; v1.2 the timeline, the director
  and atmosphere (roadmap §4, §7, §8.1). The roadmap's reopen triggers for OWQ-13 and OWQ-14 no longer apply.
- D005's "v1 or the first milestone after it" is answered: the first milestone after v1 (v1.1). Commander and triage rules: D042.
- The CLI exposes product capabilities only (D006) and needs no provider key.
- MCP-started runs wait for the user's click in the editor, and `ask` and `approve` cards are never answerable over MCP (doc 38 §9).
  Workflows using T2 plugin tools, and cross-publisher chains (D043), are not exposed. The server's final name follows D002 item 4.
- Standing Orders entries in other locales fall back to English while a translation is missing or stale (doc 33 §7).

## Sources

D004; doc 14 TL;DR; doc 26 §9.4; doc 29 (TL;DR, §5); doc 31 §4.6; doc 32; doc 33 (TL;DR, §3.5, §5.4, §7, §9); doc 34 OQ6; doc 38
(§9, OQ8); doc 39; architecture README §7 row 28; roadmap §4, §7, §8.1; `OWNER-QUESTIONS.md` OWQ-13 to OWQ-15.

## Notes

- 2026-09-27 (consistency review): **Refines:** now also names D006 and D025, whose headers listed OWQ-15 as an open part and now
  point here (citation fix; no decision changed).
