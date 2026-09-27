# Owner questions

Open questions that only the owner can answer: product scope, user-facing names, security and network boundaries, licensing and legal
matters, and public outreach (the owner's areas in `docs/design-gap-requests/README.md`). They come from design-gap requests marked
**owner** that are not decided, and from research docs' open questions that are owner calls.

Each entry gives the question, where it comes from, the options, and a **recommended answer, which is a proposal** until the owner
decides. IDs are `OWQ-nn` (owner question), distinct from research docs' "OQn" open-question numbers. When the owner answers:

1. the entry gets a dated **Answer** line (never deleted, never renumbered);
2. a durable rule becomes a new decision record (`Dnnn`), or the answer is written into the DG's decision record when the question is a
   DG;
3. the affected docs are updated in the folding step, as for DGs.

*Last reviewed 2026-09-27. Not legal advice: licensing and trademark entries need the legal review doc 02 asks for before 1.0.*

## Summary

All 23 questions were answered by the owner on 2026-09-27; the "Answered" column gives the answer and the record that states the
rule (the dated Answer line under each entry is authoritative).

| ID | Question | Recommended (proposal) | Source | Answered (owner, 2026-09-27) |
| --- | --- | --- | --- | --- |
| OWQ-01 | Wording of the generated-content §7 permission | Doc 02 draft plus an explicit coverage list; legal review before 1.0 | doc 02 §6.2; D001 | (b) as recommended → [D031](D031-generated-content-permission-and-licence-scope.md) |
| OWQ-02 | Licence of `docs/` prose | GPL-3.0-or-later, like everything else | doc 02 OQ; D001 | (a) GPL-3.0-or-later → [D031](D031-generated-content-permission-and-licence-scope.md) |
| OWQ-03 | Licence of the plugin SDK, WIT files and test kit | GPL-3.0-or-later; revisit at plugin phase 3 | doc 22 TL;DR, §5 | (a); revisit at doc 22 MVP step 3 if asked → [D031](D031-generated-content-permission-and-licence-scope.md) |
| OWQ-04 | May GPL-3.0-only third-party code be ported? | No by default; re-implement ideas; case-by-case owner sign-off | doc 45 OQ10 | (a) by default; (b) when no reasonable re-implementation exists → [D031](D031-generated-content-permission-and-licence-scope.md) |
| OWQ-05 | Contribution terms: DCO or CLA; AI-assisted contributions | DCO; AI assistance allowed, human signs off; trailer optional | doc 02 §10.5, OQ | (a) → [D032](D032-contribution-terms-dco.md) |
| OWQ-06 | May campaign extension overlays for others' campaigns be shared? | Yes, extension-only, merged locally, with a redistribution guard | doc 34 cw13 | (a) for Bohemia's, (b) for third-party campaigns → [D033](D033-campaign-extension-overlays.md) |
| OWQ-07 | Descriptor placement, clearance search, repository rename | DG002 option A; clearance recorded; rename before first release | DG002 | DG002 A; `AGENTS.md` amended → [D034](D034-descriptor-placement-and-names-delegation.md) |
| OWQ-08 | Pending user-facing names | Delegate to the design round, each cleared through doc 02 §9 | docs 36, 39, 40, 42, 43; D019 | (a); one names table, owner review → [D034](D034-descriptor-placement-and-names-delegation.md) |
| OWQ-09 | Private disclosure of doc 24's engine security findings | Owner reports privately now; no new public detail until acknowledged | doc 24 note | (a); reports not yet sent → [D035](D035-outreach-and-security-disclosure.md) |
| OWQ-10 | Outreach to Bohemia Interactive | One letter after name clearance, before first release | doc 02 §11 step 8 | (a) → [D035](D035-outreach-and-security-disclosure.md) |
| OWQ-11 | Outreach to CWR-CE (patches, engine requests) | Start with CE #35 and a small tested PR; then the register | docs 01, 08, 18, 29 | (a) → [D035](D035-outreach-and-security-disclosure.md) |
| OWQ-12 | Outreach to the mod-channel maintainers | DG029 option A | DG029 | DG029 A with the 30-day non-objection rule → [D035](D035-outreach-and-security-disclosure.md) |
| OWQ-13 | Size of the v1 campaign flow | Classic patterns in v1; strategic layer (Grey Heron) next milestone | D004, D005 | (a) → [D036](D036-v1-contents-and-release-split.md) |
| OWQ-14 | v1 modules, headless CLI, Standing Orders/Drill and locales; the cinematics rung | Probe-cleared wave-1 modules; minimal CLI; Standing Orders and Drill track A in English first; Cutscene node in v1, timeline and director in v1.2 | doc 34 OQ6; doc 33; D015 | (a) for every item, rung 4 included → [D036](D036-v1-contents-and-release-split.md) |
| OWQ-15 | External agents: MCP server in v1, `workflow.decide` | MCP server in v1 (opt-in); `workflow.decide` after v1 | doc 38 OQ8 | (a) → [D036](D036-v1-contents-and-release-split.md) |
| OWQ-16 | Cross-plugin chaining in workflows | DG014 option B | DG014 | DG014 B → [D043](D043-cross-plugin-chaining-in-workflows.md) |
| OWQ-17 | Mod install hand-off, directory freshness, CC-BY-SA, registry operator | DG030's four proposals | DG030 | All four DG030 proposals → [D038](D038-mod-handling-owner-additions.md) |
| OWQ-18 | Write the extended addon set into `addOns[]` by default? | Yes by default; engine-parity-only mode kept | doc 27 OQ3 | (a) → [D038](D038-mod-handling-owner-additions.md) |
| OWQ-19 | Which models the Model Manager may recommend | OSI licences, no field-of-use limits, qualified; others as "custom" | docs 02, 14; D022 | (a) → [D037](D037-model-manager-recommended-list.md) |
| OWQ-20 | Engagement ethics as a product rule; challenge catalogue | Adopt doc 36 cv43; numbered catalogue without any calendar index | doc 36 cv43; doc 43 OQ1 | (a) → [D039](D039-engagement-ethics.md) |
| OWQ-21 | Default play seed, memory across playthroughs, re-roll on restart | Fresh seed; memory opt-in; no re-roll exception in v1 | doc 43 OQ8–9; doc 36 OQ2 | Seed (a), memory (a), re-roll (a) → [D040](D040-play-seeds-and-memory.md) |
| OWQ-22 | Boundaries for generated moral choices | A documented list for suggestions only; user intent still wins | doc 28 OQ8; D011 | (a) → [D041](D041-moral-choice-suggestion-boundaries.md) |
| OWQ-23 | Strategic layer: commander design, triage transparency | A campaign setting, plot armour by default; disclose triage in the debrief | doc 29 OQ5–6 | Commander (c), triage (a); to be reconfirmed after the first balance-lab runs → [D042](D042-strategic-layer-commander-and-triage.md) |

## Legal and licensing

### OWQ-01: Wording of the generated-content permission

- **Question.** What exact GPLv3 §7 additional permission goes into `NOTICE` so that missions and campaigns made with Plotroom are the
  user's, under terms of their choice?
- **Source.** D001 item 4; doc 02 §6.2 (draft text, constraints); README "License"; doc 42 §5.2 (licences of pack content that reaches
  missions).
- **Options.** (a) Adopt the doc 02 §6.2 draft as written. (b) The draft plus an explicit list of covered output: compiler and module
  lowerings, generated scripts and glue, finishers, AI-written text, and first-party pack content copied into missions; keep the
  exclusion of Bohemia-derived material. (c) No permission; rely on "plain program output is not covered by the GPL".
- **Recommended.** (b), with "Plotroom" filled in, CONTRIBUTING stating that contributions include the permission, and the legal review
  before 1.0. Option (c) leaves the doubt that scares mission makers who mix in APL-SA content (doc 02 §6.2).
- **Blocks.** `NOTICE`; CONTRIBUTING; the About box; template and module authoring rules.
- **Answer (owner, 2026-09-27).** (b): the doc 02 §6.2 draft plus the explicit coverage list, with legal review before 1.0.

### OWQ-02: Licence of `docs/` prose

- **Question.** Does "GPL-3.0-or-later everywhere" include the design docs, or do they take CC-BY-SA-4.0?
- **Source.** Doc 02 §6.4 and open question "Docs license"; D001.
- **Options.** (a) GPL-3.0-or-later for docs too. (b) CC-BY-SA-4.0 (one-way compatible into GPLv3).
- **Recommended.** (a): one licence, the simplest REUSE setup, and Standing Orders text moves between docs, skills and the shipped app
  without a licence boundary.
- **Blocks.** `LICENSES/`, REUSE headers for docs.
- **Answer (owner, 2026-09-27).** (a): GPL-3.0-or-later for `docs/` too.

### OWQ-03: Licence of the plugin SDK, WIT files and test kit

- **Question.** Doc 22 recommends `MIT OR Apache-2.0` for the plugin SDK, WIT interfaces and conformance kit; D001 says no permissive
  lane. Which wins?
- **Source.** Doc 22 TL;DR and §5; D001; D007.
- **Options.** (a) GPL-3.0-or-later like everything. (b) A single, narrow permissive exception for interface-only artefacts that contain
  no Plotroom or Bohemia logic.
- **Recommended.** (a) for now: T1 plugins distributed through the registry must be GPL-3.0-compatible anyway, so a GPL SDK costs plugin
  authors little. Revisit at doc 22's MVP phase 3 (T1), if plugin authors ask.
- **Blocks.** T1 SDK publication (not v1-critical).
- **Answer (owner, 2026-09-27).** (a): GPL-3.0-or-later for now; revisit at doc 22's MVP phase 3 if plugin authors ask.

### OWQ-04: GPL-3.0-only third-party code

- **Question.** May code licensed GPL-3.0-only (for example parts of Twine that doc 45 considered) be ported? It would make the combined
  work distributable under GPLv3 only, narrowing "or later".
- **Source.** Doc 45 OQ10; DG018 (port records).
- **Options.** (a) Never. (b) Case by case, with owner sign-off and a per-file licence marker. (c) Freely.
- **Recommended.** (a) by default, re-implementing ideas in our own code; (b) only when no reasonable re-implementation exists.
- **Blocks.** Nothing in v1.
- **Answer (owner, 2026-09-27).** As recommended: (a) by default; (b) only when no reasonable re-implementation exists.

### OWQ-05: Contribution terms

- **Question.** DCO or a CLA, and what is the policy for AI-assisted contributions?
- **Source.** Doc 02 §10.5 and open question "AI-contribution policy"; CWR-CE forbids AI trailers (doc 02 §10.5).
- **Options.** (a) DCO; AI assistance allowed; the human contributor signs off and answers for provenance and hygiene; an
  `Assisted-by:` trailer optional. (b) As (a) with the trailer required. (c) As (a) with AI trailers forbidden, like CWR-CE. (d) A CLA.
- **Recommended.** (a). A CLA buys relicensing flexibility that CWR-derived code cannot use (doc 02 §10.5). Agents never sign off for a
  human.
- **Blocks.** `CONTRIBUTING.md`; the DCO check in CI.
- **Answer (owner, 2026-09-27).** (a): DCO; AI assistance allowed; the human contributor signs off; `Assisted-by:` optional.

### OWQ-06: Sharing campaign extension overlays

- **Question.** May users share an extension overlay (new nodes, branches and missions) that attaches to someone else's campaign,
  including Bohemia's own campaigns?
- **Source.** Doc 34 row cw13 ("Only the extension ships [U licensing, doc 02]"); doc 34 §5.2 row 02; doc 19 §7.6 (Preserve mode).
- **Options.** (a) Yes: only the extension sidecar and the user's own new missions ship; the build merges locally from the user's
  installed parent by id and hash; the export guard (doc 34 mo10) blocks parent content. (b) Only for parents whose licence allows
  derivatives, or with the parent author's recorded permission. (c) Never.
- **Recommended.** (a) for Bohemia's campaigns, with the question added to the Bohemia letter (OWQ-10); (b) for third-party campaigns.
- **Blocks.** Doc 19 §7.6 extension overlays; the export guard's rules.
- **Answer (owner, 2026-09-27).** As recommended: (a) for Bohemia's campaigns (and asked in the OWQ-10 letter); (b) for third-party
  campaigns.

## Names

### OWQ-07: Descriptor placement, clearance search and repository rename (DG002)

- **Question.** Where may the descriptor "…for Arma: Cold War Assault / Operation Flashpoint" appear, and when do the clearance search
  and the repository rename happen?
- **Source.** DG002; doc 02 §9, §11; D002.
- **Options.** DG002 options A (Plotroom is the product name; the descriptor only in body-text places), B (the long form everywhere),
  C (Plotroom alone).
- **Recommended.** A, with DG002's placement table (no descriptor in the window title, installer name, binaries or directories); record
  the clearance search for Plotroom, Wilco, Plotline, the Tote and Teller in doc 02 before the first release; rename the repository
  before the first release.
- **Conflict to resolve.** `AGENTS.md` ("Naming and Trademarks") already says that the README, window title, splash, About box,
  installer and listings pair "Plotroom" with the descriptor. The recommendation above drops it from the window title and installer
  name, so adopting it means amending `AGENTS.md`; keeping `AGENTS.md` as written means DG002's table changes for those surfaces.
  Until the owner answers, `AGENTS.md` governs (found in the consistency review of 2026-09-27).
- **Blocks.** Window title and About box code; `NOTICE` and disclaimer text; the repository name.
- **Answer (owner, 2026-09-27).** A, with DG002's placement table (no descriptor in the window title, installer name, binaries or
  directories); `AGENTS.md` "Naming and Trademarks" is amended to match. Clearance search recorded in doc 02 and the repository renamed
  before the first release.

### OWQ-08: Pending user-facing names

- **Question.** Who names the user-facing terms that research left as placeholders, and how?
- **Source.** Examples: the realism setting's levels (doc 39 §5.1: Cinematic, Grounded, Doctrinal); "Styles" (D019); "Economy mode"
  (doc 40 R12); "Surprise me", "Seed Atlas", "Remix", "Event pacing" and campaign modifiers such as "Thin roster" (doc 43 §3); difficulty
  rungs and the rename of `DifficultyPreset::Veteran`, which clashes with the game's own Veteran mode (doc 36 OQ5; doc 43 §3.6);
  "Community catalog" (doc 42).
- **Options.** (a) Delegate to the design round, as the owner did for Standing Orders and Drill: pick the best names, clear each through
  doc 02 §9, refactor later if needed, and record them in one names table. (b) The owner names each one.
- **Recommended.** (a); the owner reviews the names table before the first release. The realism levels in doc 39 §5.1 are a sound start.
- **Blocks.** UI strings; Standing Orders entries for these features.
- **Answer (owner, 2026-09-27).** (a): delegated to the design round; one names table; the owner reviews it before the first release.

## Outreach

### OWQ-09: Private disclosure of doc 24's security findings

- **Question.** Doc 24's disclosure note says several findings can be used by a downloaded mission against players of the shipping game
  and should be reported privately to the CWR-CE maintainers and to Bohemia Interactive. Who reports them, and when?
- **Source.** Doc 24 disclosure note (findings F1, F3, F4, F9, H2–H4) and §6 (hardening patches); D012.
- **Options.** (a) The owner reports privately now, through a private channel of each project, and records the date here. (b) Open public
  issues. (c) Wait until Plotroom ships.
- **Recommended.** (a). Until the reports are acknowledged, no new public detail is added (doc 24 already contains no exploit strings),
  and the doc 24 §6 hardening patches enter the engine-requests register only after that.
- **Blocks.** Hardening entries in `docs/upstream/`; any public discussion of the findings.
- **Answer (owner, 2026-09-27).** (a): the owner reports privately to CWR-CE and Bohemia and records the dates here; no new public detail
  until acknowledged. Reports sent: *not yet*.

### OWQ-10: Outreach to Bohemia Interactive

- **Question.** Should the project write to Bohemia, what should it ask, and when?
- **Source.** Doc 02 §11 step 8 and open questions (loading APL-SA data including the demo's, the demo EULA, pre-remaster 1.99 data);
  doc 01 OQ3 and doc 07 OQ5 (MIT metadata in CWR's Cargo manifests versus the GPL LICENSE); OWQ-06.
- **Options.** (a) One letter after the name clearance and before the first public release: the name, the disclaimer and the data
  policy, asking for comfort on nominative use, on loading APL-SA data (Remastered, demo and 1.99) in a GPL editor, on the MIT
  metadata, and on extension overlays for Bohemia's campaigns. (b) No outreach; rely on doc 02's reading.
- **Recommended.** (a), sent by the owner; answers recorded in doc 02.
- **Blocks.** Nothing in development; the first public release should wait for either an answer or a documented decision to proceed.
- **Answer (owner, 2026-09-27).** (a): one letter from the owner after the name clearance and before the first public release.

### OWQ-11: Outreach to CWR-CE

- **Question.** Who represents Plotroom with CWR-CE, and in what order are patches and engine requests proposed?
- **Source.** Doc 01 §9 (c) (start with CE issue #35 and a small, well-tested PR) and OQ5 (an `official` branch); doc 08 P3; doc 18 §9
  (E1–E6); doc 29 OQ9 (E13, E7, E8; E5 and E6 as cheap first asks); doc 42 OQ1 (CE issues #233 and #228); D012.
- **Options.** (a) The owner, or a maintainer the owner names, starts with #35 plus a small tested PR, then opens one tracking discussion
  that links the engine-requests register once it exists. (b) File all requests at once. (c) No outreach until v1.
- **Recommended.** (a); security items only after OWQ-09's private reports.
- **Blocks.** Preview phase P3; every "proposed" status in `docs/upstream/`.
- **Answer (owner, 2026-09-27).** (a): the owner (or a maintainer the owner names) starts with CE #35 and a small tested PR, then one
  tracking discussion linking the register; security items only after OWQ-09's private reports.

### OWQ-12: Outreach to the mod-channel maintainers (DG029)

- **Question.** Who asks the maintainers of the game's MODS storage and of the Game Schedule for their terms, and what counts as
  non-objection?
- **Source.** DG029; doc 42 OQ1–OQ2, §4.2.
- **Options.** DG029 A (one message per channel from the owner or a named maintainer), B (ship with a notice and wait for objections),
  C (wait until the channels publish terms).
- **Recommended.** A. The owner sets the non-objection rule (DG029's placeholder: a written reply that does not object, or no
  objection 30 days after an acknowledging reply).
- **Blocks.** The Community mod directory pack (doc 42 MS2) and the Community catalog connector (MS3).
- **Answer (owner, 2026-09-27).** A, with the non-objection rule: a written reply that does not object, or no objection 30 days after an
  acknowledging reply.

## Scope

### OWQ-13: Size of the v1 campaign flow

- **Question.** How much of the describe → generate → edit flow must v1 ship?
- **Source.** D004 (v1 includes the campaign flow; the owner's first scoping was import/preserve first); D005; doc 26 §9.4 (patterns
  P1–P8); doc 29 (P9 Strategic layer, Grey Heron).
- **Options.** (a) v1: the typed campaign model, Plotline, the Tote, Path Explorer, import and preserve, and describe → generate → edit
  for the classic patterns with a no-model path; the strategic layer and Grey Heron are the first milestone after v1. (b) Grey Heron in
  v1. (c) Import, preserve and the graph editor in v1; generation after v1.
- **Recommended.** (a). It makes the flow first-class in v1 while the strategic layer waits for its balance lab and 1.99 probes;
  (c) contradicts D009.
- **Blocks.** Roadmap milestones.
- **Answer (owner, 2026-09-27).** (a): the classic patterns in v1; the strategic layer and Grey Heron are the first milestone after v1.

### OWQ-14: v1 modules, headless CLI, Standing Orders and Drill, locales

- **Question.** Which doc 31 modules ship in v1; is the headless `plotroom` CLI in v1; which Standing Orders and Drill content ships,
  in which languages?
- **Source.** Doc 34 OQ6 (modules, strategic modules, CLI, registry operator); doc 31 §4.6 (twenty wave-1 modules); doc 33 TL;DR
  (five locales from the first release) and §9; doc 14 TL;DR (no benchmark for Czech, Polish or Russian text).
- **Options.** Modules: (a) the wave-1 modules whose probes pass on `Cwr`, or (b) a smaller top-ranked set. CLI: (a) a minimal CLI
  (lint, compile/export, round-trip check, golden-journal replay; no agent), or (b) none. Standing Orders and Drill: (a) the seed entries
  and Drill track A in English, other locales as native reviewers join, or (b) all five locales at release.
- **Recommended.** Modules (a); CLI (a), because CI and the acceptance tests need it anyway; Standing Orders and Drill (a). The strategic
  modules follow OWQ-13.
- **Also: rung 4 (cinematics) in v1?** D015 item 4 makes camera and cinematics first-class but sets no release. The architecture
  (README §7 row 28) and the roadmap ship only the Cutscene-node recipe in v1, with camera scripting through the script editor, and
  move the timeline (doc 32) and the cutscene director (doc 39) to v1.2. Options: (a) that split; (b) the doc 32 timeline in v1, the
  director in v1.2; (c) both in v1. **Recommended:** (a), because the timeline needs the live link, exact terrain height and the
  CP probes first; the owner confirms, since v1 scope is an owner call (added in the consistency review of 2026-09-27).
- **Blocks.** v1 milestone contents.
- **Answer (owner, 2026-09-27), rung 4 only.** (a): v1 ships the Cutscene-node recipe with camera scripting through the script editor;
  the doc 32 timeline and the doc 39 cutscene director ship in v1.2.
- **Answer (owner, 2026-09-27), the rest.** Modules (a): the wave-1 modules whose probes pass on `Cwr`; CLI (a): the minimal CLI;
  Standing Orders and Drill (a): seed entries and Drill track A in English first, other locales as native reviewers join.

### OWQ-15: External agents in v1

- **Question.** Does v1 ship the opt-in MCP server for external agents, and may external agents answer workflow decision points
  (`workflow.decide`)?
- **Source.** Doc 38 OQ8 and §9; D006 item 4.
- **Options.** (a) The MCP server in v1 (list and start workflows, product tools, the primer as a skill); decision points answered only
  in the editor; `workflow.decide` after v1, journaled with an "external" origin and excluded from model qualification. (b) Both in v1.
  (c) Neither in v1.
- **Recommended.** (a).
- **Blocks.** Doc 38 §9 scope; evaluation accounting.
- **Answer (owner, 2026-09-27).** (a): the opt-in MCP server in v1; `workflow.decide` after v1.

## Plugins, network, mods and models

### OWQ-16: Cross-plugin chaining in workflows (DG014)

- **Question.** May a pack workflow chain plugins from different publishers, so that one plugin's output reaches another plugin's service?
- **Source.** DG014; doc 38 OQ13; doc 22 §3.1–§3.2.
- **Options.** DG014 A (forbid), B (first-party and user-authored workflows only, with the egress card every time), C (any pack).
- **Recommended.** B, as DG014 proposes; such workflows are never exposed to external agents.
- **Blocks.** The `requires` rule for pack workflows; the T0 install review.
- **Answer (owner, 2026-09-27).** DG014 option B: first-party and user-authored workflows only, the egress card every time, never exposed
  to external agents.

### OWQ-17: Mod install hand-off, directory freshness, CC-BY-SA and registry operator (DG030)

- **Question.** DG030's four items.
- **Source.** DG030; doc 42 (§3.3, §4.2, §5.2–§5.3, OQ8–OQ9); doc 34 OQ6; doc 22 OQ1.
- **Options and recommended (DG030's proposals).** (1) A user-clicked "Launch the game to install mods" that starts the game vanilla,
  without `--private` and without a mission, for CWR and CE targets. (2) Directory refreshed at each release plus the opt-in connector's
  live refresh; no third-party metadata in Plotroom's registry. (3) CC-BY-SA-4.0 allowed only for editor-only content, not for content
  that reaches missions. (4) No registry operator until the registry is scheduled; then the project's own organisation with doc 42
  §5.3's governance.
- **Blocks.** The "missing mod" card's install route; directory updates; the registry licence allowlist and RG1.
- **Answer (owner, 2026-09-27).** All four DG030 proposals as written.

### OWQ-18: The extended addon set

- **Question.** Should Plotroom write the extended dependency set (script literals, `description.ext` weapons, markers, effects) into
  `addOns[]` by default, or only offer it as a lint?
- **Source.** Doc 27 OQ3 and TL;DR (recommendation: engine set ∪ extended set ∪ user pins); D030.
- **Options.** (a) Written by default, with an engine-parity-only mode. (b) Lint only.
- **Recommended.** (a): weapons and magazines whose addon is not activated fail at run time with "addon missing", which the engine's
  own scan does not prevent; extended entries survive a re-save in a fresh stock-editor session, and Plotroom re-derives any the stock
  editor drops (doc 27 TL;DR).
- **Blocks.** The dependency writer's default.
- **Answer (owner, 2026-09-27).** (a): written by default, with an engine-parity-only mode.

### OWQ-19: Which models the Model Manager may recommend

- **Question.** Which licences and use policies may a model have to appear in the Model Manager's recommended list, and how are other
  models, including arbitrary Hugging Face files, treated?
- **Source.** D022; D023; doc 02 TL;DR (offer OSI-licensed weights by default; models with pass-through restrictions are brought by the
  user); doc 14 TL;DR and §6 (one candidate's usage policy bans military or warfare uses).
- **Options.** (a) Recommended list: OSI licences with no field-of-use restriction, and only models that passed Plotroom's
  qualification; everything else installable as "custom" with its licence and policy shown and an explicit acceptance, and an
  "unqualified" badge until qualified. (b) Any licence in the recommended list, with warnings. (c) Recommended list only; no custom
  installs.
- **Recommended.** (a). It honours the owner's "even directly from Hugging Face" while keeping licence risk visible.
- **Blocks.** The Model Manager's catalogue data.
- **Answer (owner, 2026-09-27).** (a): OSI licences without field-of-use limits and qualified, for the recommended list; everything else
  as "custom" with licence and policy shown, explicit acceptance, and an "unqualified" badge until qualified.

## Player-facing product rules

### OWQ-20: Engagement ethics and the challenge catalogue

- **Question.** Is doc 36's cv43 list a product rule for everything Plotroom's modules, generators, Wilco and Standing Orders produce,
  and, under it, may a numbered, never-expiring challenge catalogue exist, with or without a "week" index?
- **Source.** Doc 36 cv43 (no real-time decay, no streaks, dailies, login rewards or appointment mechanics, no grind, no gacha loops,
  harsh modules opt-in, natural stopping points, disclosed hidden help, no variable-ratio rewards); doc 43 §3.7 and OQ1.
- **Options.** (a) Adopt cv43 as a product rule (creators' own scripts get informative lints only), and allow the challenge catalogue as
  T0 data with a baked seed and no calendar, week index, streak, reward or reminder. (b) As (a) with a week index. (c) No challenges.
- **Recommended.** (a). A week index is an appointment mechanic in disguise.
- **Blocks.** Doc 43 RV4; generator presets; Standing Orders entries on Plotroom's own campaign rules.
- **Answer (owner, 2026-09-27).** (a): cv43 is a product rule for Plotroom's own output; the challenge catalogue is allowed as T0 data
  with a baked seed and no calendar, week index, streak, reward or reminder.

### OWQ-21: Default play seed, memory across playthroughs, re-roll on restart

- **Question.** Which play seed does a campaign use by default; is memory across playthroughs welcome; may a player opt in to re-rolling
  stored rolls on restart?
- **Source.** Doc 43 OQ8, OQ9 and the product review notes; doc 36 OQ2; doc 29 SL11.
- **Options.** Seed: (a) Fresh each playthrough, Fixed for challenge entries and "beat my run" re-exports, or (b) Fixed by default.
  Memory: (a) opt-in per campaign with a visible reset, or (b) on by default, or (c) never. Re-roll: (a) no exception to SL11 in v1, or
  (b) a documented opt-in.
- **Recommended.** Seed (a); memory (a); re-roll (a).
- **Blocks.** Doc 43 defaults; doc 29 SL11 wording.
- **Answer (owner, 2026-09-27).** Seed (a), memory (a), re-roll (a).

### OWQ-22: Boundaries for generated moral choices

- **Question.** Which conscience choices may the archetype vocabulary and Wilco *suggest*, and how are they framed?
- **Source.** Doc 28 OQ8; D011 (the user's explicit intent always wins; no refusals or nagging).
- **Options.** (a) A short, documented boundary list for generated suggestions only (for example: dilemmas carry consequences and are
  never rewarded as atrocity; civilians and prisoners are framed as dilemmas, not loot); the user's own content is never filtered.
  (b) No boundaries. (c) A content filter on user content, which conflicts with D011.
- **Recommended.** (a), written in Standing Orders so users can see it.
- **Blocks.** Doc 26 archetype vocabulary; lens wording.
- **Answer (owner, 2026-09-27).** (a): a short documented boundary list for generated suggestions only, written in Standing Orders; the
  user's own content is never filtered.

### OWQ-23: Strategic layer: commander design and triage transparency

- **Question.** Is the player an invulnerable commander (plot armour) or an embodied roster soldier with Retry, on `Cwa199` and `Cwr`;
  and does the debrief disclose triage ("survived: gravely wounded")?
- **Source.** Doc 29 OQ5–OQ6 (both marked "product"); doc 36 cv07 and cv43 item 8 (hidden help is disclosed).
- **Options.** Commander: (a) plot armour, (b) embodied with Retry, (c) a campaign setting. Triage: (a) disclose, (b) hide.
- **Recommended.** Commander (c) with (a) as the default; triage (a), consistent with cv43 item 8. Confirm after the first balance-lab
  runs and playtests.
- **Blocks.** Grey Heron's final rules.
- **Answer (owner, 2026-09-27).** Commander (c), a campaign setting with plot armour as the default; triage (a), disclosed in the debrief.
  Both confirmed again after the first balance-lab runs and playtests.

## Verification notes

### Consolidation pass (2026-09-27)

- Built from the DG index (DG002, DG014, DG029, DG030 open and owner-marked) and the open questions of docs 02, 14, 22, 24, 27, 28,
  29, 33, 34, 36, 38, 42, 43 and 45, re-read on 2026-09-27. DG013, DG028 and DG033 items 3–4 are decided and appear as D024, D008 and
  D029. No outreach was made and no legal advice is given.

### Owner answers (2026-09-27)

- The owner answered all 23 questions on 2026-09-27, each with its recommended option (OWQ-04: (a) by default, (b) only when no
  reasonable re-implementation exists; OWQ-06: (a) for Bohemia's campaigns, (b) for third-party ones; OWQ-14 answered in two dated
  lines, rung 4 and the rest). The Answer lines were written before this step and were not changed by it.
- The Summary table gained the "Answered" column, and each durable rule became a decision record: D031 (OWQ-01–04), D032 (OWQ-05),
  D033 (OWQ-06), D034 (OWQ-07–08), D035 (OWQ-09–12), D036 (OWQ-13–15), D037 (OWQ-19), D038 (OWQ-17–18), D039 (OWQ-20), D040
  (OWQ-21), D041 (OWQ-22), D042 (OWQ-23) and D043 (OWQ-16). Four DGs are decided through these answers: DG002 (OWQ-07), DG014
  (OWQ-16), DG029 (OWQ-12) and DG030 (OWQ-17).
- Still to do after the answers, and tracked in the records' **Open parts**: OWQ-09's private reports (not yet sent; their dates go in
  OWQ-09's entry), the OWQ-10 letter and the other outreach (D035), the clearance search and the names table (D034), the legal review
  of the §7 wording before 1.0 (D031), the reconfirmation of OWQ-23 after the first balance-lab runs (D042), and DG038's SL11 wording,
  which OWQ-21's answer unblocks (D040).
- Recorded the same day, outside this list: the owner's choice of the managed `llama-server` sidecar as the primary local runtime (D022's
  amendment note, which D037 builds on), and the deferral of doc 48's cloud test round 1 until doc 49's local results are in (D021's
  amendment note). Neither was an owner question here.

### Consistency review of the owner answers (2026-09-27)

- Each answer was checked against its record (D031–D043), the decided DGs (DG002 → D034, DG014 → D043, DG029 → D035, DG030 → D038),
  the amended `AGENTS.md` "Naming and Trademarks", the architecture, the roadmap, D004, D021–D023, D030 and docs 43, 44, 47 and 48.
  No answer is contradicted. The earlier records that listed these questions as open parts now point to the records that settle them.
- Open owner-level items that are **not** in this file: doc 48 OQ9 (may a model whose use policy bans military uses be tested; D037
  only rules that it is never recommended) and doc 48 OQ10 (should aggregators ship as first-class providers; D021's note). If the
  owner is to answer them, they become OWQ-24 and OWQ-25 in a later change.
