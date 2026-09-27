# D038: Mods: install hand-off, directory freshness, CC-BY-SA, registry operator, extended addon set

> **Status:** accepted · **Decided by:** owner (OWQ-17 = DG030 items 1–4; OWQ-18) · **Decided:** 2026-09-27
> **Recorded:** 2026-09-27 · **Scope:** the "missing mod" card's install route, updates of the community mod directory, the pack licence allowlist, the pack
> registry's operator, and the default of the dependency writer. **Refines:** D030 (its open parts DG030 and OWQ-18; the rest of D030
> stays a research baseline), D007 (its open part DG030 item 4) and D008 (its open part DG030 item 2). **Related:** D003, D018, D031,
> D035.
> **Open parts:** namespace verification through OFPEC tags and third-party registries added by URL (doc 42 OQ9); `--private` on every
> Preview launch (doc 42 OQ10, MAT12).

## Context

- Doc 42 proposes `--private` on every Preview launch; it blanks the master server, so the game's MODS screen could not reach its mod
  storage from a Preview launch (DG030 item 1). Plotroom itself never installs mods (D030 item 5).
- Updating the offline directory through Plotroom's pack registry would put third-party metadata in it, against doc 42 MG8.
- Share-alike terms on content that reaches a mission would bind users' exported missions (DG030 item 3; doc 42 §5.2).
- The engine's own dependency scan misses weapons, magazines, markers and effects; a weapon whose addon is not activated fails at run
  time with "addon missing". Extended entries survive a re-save in a fresh stock-editor session (doc 27 TL;DR, OQ3).

## Decision

1. **"Launch the game to install mods"** (DG030 item 1 b). For CWR and CE targets only, a button reuses Preview's launcher to start
   the game vanilla: no `--private`, no staged mission, no mod set other than vanilla, only when the user clicks it, never
   automatically. Plotroom rescans installed mods when it regains focus (doc 42 §3.3).
2. **Directory freshness** (item 2 c). The built-in Community mod directory is regenerated at each release; users who enable the
   Community catalog connector (D008) also get its live refresh. Every row shows its snapshot date. Plotroom's pack registry never
   carries third-party mod metadata.
3. **CC-BY-SA-4.0** (item 3 b) is allowed for **editor-only** pack content, not for content that can reach a user's mission. Mission-
   reaching content stays under CC0-1.0, MIT, Apache-2.0 or CC-BY-4.0 (doc 42 §5.2), so exported missions stay the user's (D031).
4. **Registry operator** (item 4). No operator until the registry (doc 42 MS4) is scheduled; then the project's own GitHub
   organisation runs it with doc 42 §5.3's governance: two or three maintainers with FIDO 2FA, CODEOWNERS per namespace, a forkable
   index and a public succession plan.
5. **Extended addon set** (OWQ-18 a). The dependency writer puts the engine set, the extended set (script literals, `description.ext`
   weapons, markers, effects) and the user's pins into `addOns[]` **by default**; an engine-parity-only mode stays available.

## Alternatives considered

- Text instructions only for installs (item 1 a): a harder path for the common case, while a vanilla, user-started launch adds no
  capability.
- Release cadence only (item 2 a), or registry-delivered updates (b): stale rows for users who want live data, or third-party metadata
  in the registry.
- CC-BY-SA for mission-reaching content (item 3 a): binds users' missions and needs its own analysis next to the game data's APL-SA
  (doc 02 §3) [not legal advice].
- A community site as operator (item 4 b), or any operator before the registry exists: premature (doc 22 OQ1).
- The extended set as a lint only (OWQ-18 b): leaves a known run-time failure to users.

## Consequences

- D030 item 2's "whether the extended set is written by default is OWQ-18" and its CC-BY-SA consequence are answered here.
- The export licence audit and registry CI check the CC-BY-SA rule per item, from its manifest (doc 34 mo13; doc 42 §5.2; design
  detail: proposal).
- The directory pack (doc 42 MS2) also waits for D035 item 4's recorded non-objection; the registry and the connector are v1.4 work
  (roadmap §4).
- The folding step updates doc 42 (§3.3, §4.2, §5.2, §5.3, §7.2, §8.1, OQ8, OQ9), doc 27 OQ3, doc 34 OQ6 and doc 22 OQ1.

## Sources

DG030; doc 42 (§3.3, §4.2, §5.2–§5.3, §6.3, §7.2, §8.1, OQ8–OQ10); doc 27 (TL;DR, §4.5, OQ3); doc 34 (mo13, OQ6);
doc 22 OQ1; doc 02 §3; `OWNER-QUESTIONS.md` OWQ-17 and OWQ-18; D030.

## Notes

- 2026-09-27 (consistency review): **Refines:** now also names D008, whose open part (DG030 item 2) this record's item 2 settles
  (citation fix; no decision changed).
