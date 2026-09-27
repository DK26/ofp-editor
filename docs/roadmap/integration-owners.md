# Roadmap appendix: owners of the integration items

> **Status:** proposal (roadmap baseline 2026-09-27). Part of the [roadmap](../roadmap.md). The 65 **integration items** are proposals
> from later research docs aimed at earlier designs, collected in the first part of the consolidation pass (a working inventory that is
> not kept in the repository; this appendix and the architecture's Appendix A are its record). The architecture's Appendix A
> ([`docs/architecture/README.md`](../architecture/README.md#appendix-a-integration-items-owners)) names the design owner (an
> architecture section, a decision record, a doc fold or content); this appendix gives each item its **roadmap owner**: the milestone
> in which it lands, or "deferred: reason".

## 1. How to read the table

- **Owner** is the milestone where the item first lands as code, content or a completed doc fold. "M0 docs" means a fold into the
  research docs or `docs/` indexes done by lane F during M0, before the code that depends on it.
- **Also** names later milestones that finish the item. **Deferred** names what is left for v1.x or later, with the reason.
- **Lane** follows the roadmap's §6: A core and formats, B renderer and shell, C game integration, D AI harness, E knowledge and
  content, F design and docs, G campaign.
- A doc fold edits research docs only in the folding step of a decided DG or record, with a dated verification note in each edited doc
  (`docs/design-gap-requests/README.md`, lifecycle).

## 2. Items from doc 35 (lessons from real content)

| Item | Owner | Lane | What lands, where | Deferred part |
| --- | --- | --- | --- | --- |
| I35-PRIMER-MP | M4 | E | Multiplayer section in `skills/mission-primer/references/` with a pointer in SKILL.md, inside doc 30 §5.2's 1,200-word budget; stable anchor ids so capsules citing primer sections do not break (agent-runtime §8) | v1.3: facts re-checked against MP Preview probes |
| I35-PRIMER-FACTS | M4 | E | rc12 facts in the primer references; rc13's top-100 palette and SQS house style as Teller data. Also M5: `Cwa199` generators emit only `?`/`goto`/`@`/`~`; `if`/`while` only after an SP-08 probe | — |
| I35-MOD | M5 | E, F | One reconciled module catalogue as a data file (extensibility §3.5), merged with doc 31 §4.6 and doc 34 rows, never appended; the doc fold runs in lane F during M4. v1 ships the wave-1 rows whose probes pass on `Cwr` (owner, OWQ-14 (a)) | v1.3: MP rows rc23–rc26 (need MP Preview). v1.2: ambient soundscape rc14 (atmosphere). Later: candidate modules rc27 and the performance governor rc28 (need demand and probes) |
| I35-MOD2 | M4 | E, A | Composition library per side by role tags as a built-in T0 pack (rc33). Also M5: the module contract's variant group, counter/any/switch nodes and fault isolation (rc32) | — |
| I35-TPL | M4 | E | Template kind with named anchors and derived entities; provenance "derived from anchor X"; legacy template import with Remastered deltas as metadata and per-profile language files (rc34, rc40) | v1.3: CTI, Hub War, set-piece and co-op families (rc37–rc39), which depend on MP Preview |
| I35-CUT | M5 | B, A | Cutscene-node recipe and timing defaults in `plotroom-cine` (rc35, rc50), provisional until DG035 reconciles the shot counts with doc 39 §9.4 | v1.2: the timeline form of the recipe |
| I35-DRILL | M4 | E | Drill template for any mechanic (rc36); "Anatomy of an official mission" (rc71); "Missions and mods" (rc73); doc 33 §5 moves (rc74); the self-review checklist as the readiness lint summary (rc75); topic seeds (rc76) | v1.3: "How classic MP modes work" and the live CTF tutorial (rc72) |
| I35-GEN | M5 | G | Code-owned generator defaults rc07, rc41–rc49, rc53 (authority guard), rc54 (Quick Op), rc56, rc57 in `plotroom-generate`, `plotroom-lower` and `plotroom-export`. Earlier: rc55's folder-naming lint in M2 | v1.3: MP numbers rc52 |
| I35-PREV | M5 | C | Campaign-node Preview prologue with assumption chips, variables set in the staged init | — (a native row launch waits for ER-007, roadmap §8.3) |
| I35-LINT | M1 | A | Codes from the DG005 registry and owners per validation-and-lints §10: rc58 and rc67 in M1–M2; rc66 in M1/M3; rc68 and the first rc70 gate in M3; rc60, rc61, rc63, rc64, rc69 in M4; rc59, rc62 and rc70's Path Explorer part in M5 | v1.3: MP settings rc65 |
| I35-19 | M5 | G | Variant node attribute and output contracts (rc78); award defaults (rc80); the `Ignored` outcome (rc82); 6–12 mission defaults, story beats for loops, router nodes, forks with provenance (rc83). Also M6: the outcome-matrix builder, a v1 candidate inside OWQ-13 (a)'s classic-pattern scope, sized per the roadmap's §10 item 5 | v1.3: the SP-to-co-op pack workflow and MP series export as a rotation (need MP Preview and a 1.99 probe) |
| I35-26 | M5 | G, B | §9.3 archetype candidates and modifiers as data; the protagonist and mode lane in Plotline's Flow view; the "first sortie" beat. Also M6: model menus use them | — |
| I35-29 | deferred: v1.1 | G | — | Strategic-layer op kinds, roster seeds, ops-board cards, doom-clock modes and Reputation belong to the strategic layer, the first milestone after v1 (owner, OWQ-13 (a)) |
| I35-84 | M4 | C, D | "Remap to an installed set" as one typed AI-off workflow over the vanilla-safe swap and class remap, per-file fingerprints. M0 docs: the label rename in doc 35 rc84 | v1.4: vehicle remaps wait for the vehicle-role evaluation (doc 42 MS2) |
| I35-90 | M1 | A, F | Evidence tiers T1–T4 in `plotroom-profile` and the catalog; the `exe_199_string` column in the next data pass (before M2's catalog generation); the exe scan stays a local opt-in tool | — |
| I35-MOMENT | M5 | E, G | Moment cards as data; lint MC21 (`MomentSlot`). Also M6: model fills | v1.2: one music cue per mission, with the cue planner |

## 3. Items from docs 37, 42, 29, 38 and 40

| Item | Owner | Lane | What lands, where | Deferred part |
| --- | --- | --- | --- | --- |
| I37-IDIOMS | M4 | E, A | Gotchas I13, I14, I16 in `skills/mission-primer/references/idioms.md`; construction rules in the attribute planner and validators. Also M5: the 1.99 effect probes (PP6, PP12) through SP-08 | — |
| I37-SO | M4 | E | Standing Orders entries: height, loadout, cargo, locks, callsigns, attributes; greyed-out reasons routed through doc 33 §4.4 | — |
| I37-31IDX | M4 | A | Teller reference kinds for rename (`markers[]`, `respawn_` prefixes, objective ids, per-unit briefing sections; "cannot prove" for runtime names) | — |
| I42-08 | M3 | C | `--private` on every Preview launch (MAT12). Earlier: the side-effect question in SP-07 (M0) | — |
| I29-08 | M0 docs | F, C | The open items (campaign start at a chosen row; campaign `description.ext` under `--test-mission`) recorded in doc 08 and asked by SP-07. Also M5: campaign probes | — (engine support is ER-007) |
| I38-BUDGET | M4 | D | Whole-run `[budget].turns` semantics and the load lint in `plotroom-workflow`. M0 docs: the doc 21 §7.1 note | — |
| I38-STAGE | M5 | G | The campaign flow as workflow definitions plus code steps (D025). M0 docs: the doc 25 §4.2 supersession note and the DG filing the index lists as a candidate | — |
| I38-GATE | M4 | D | `NonEmpty<GateId>` and `NonEmpty<CheckId>` in definitions. M0 docs: the doc 21 §6.1 note | — |
| I40-14 | M6 | D | Dated `[[price]]` rows in `models.toml`, the 60-day chip, no prices in code, no fetching of pricing pages. M0 docs: the doc 14 §7 fold | — |
| I40-25 | M6 | D | Instrument E12 in `plotroom-evals`; its results settle doc 40 R6 and R7 (DG020, DG021) | — |
| I42-22 | M4 | D, F | Manifest fields `ai`, `ai_usage`, `[activation] mods`; the licence split; Unicode and template-render lints in the T0 loader; the `feed` kind is decided (D008) | v1.4: feed connectors and RG1; RG2–RG3 later |
| I42-25 | M5 | G | S0's no-model fields, the facet data and CfgGroups presets as one-pick squads. Also M6: `ModSetOption`, the mod-set picker, the four-level unit menu and variant chips in model menus | — |
| I42-17-30 | M4 | E | Knowledge overlays as T0 packs, shown only inside code-selected cards | — |
| I42-37 | M4 | C | Remap tiers (1 side + kind + role, 2 kind + role, 3 side + kind; up to 3 candidates; the model only ranks; the user confirms) | v1.4: vehicle remaps gated on the vehicle-role evaluation |

## 4. Repository structure items

| Item | Owner | Lane | What lands, where | Deferred part |
| --- | --- | --- | --- | --- |
| NEW-README | M0 docs | F | `docs/README.md`: rows for docs 01–45 (title, question answered, code families), data files, the porting CSV, skills, prompts, DGs, decisions, architecture, the upstream register and this roadmap; the renamed doc 33 file | — |
| NEW-DGDIR | M0 docs (done) | F | `docs/design-gap-requests/` exists (DG001–DG038). M0 files the architecture README §8 candidates and the index's "noticed but not filed" list | — |
| I17-DEC | M0 docs (done) | F | `docs/decisions/` exists (D001–D043). The retrieval index doc 17 also suggests goes into `docs/README.md` | — |
| I34-MERGE | M4 | F | The merge pass retiring doc 34 rows that doc 33 already covers (before Standing Orders and Drill content freezes). Also M5: the doc 31 and doc 34 module rows, before the catalogue data file freezes | — |

## 5. Items from doc 34 (second-pass ideas)

| Item | Owner | Lane | What lands, where | Deferred part |
| --- | --- | --- | --- | --- |
| I34-02 | M1 | F, A | `NOTICE` with Bohemia's §7 terms and `Derived-From:` headers (M1); the D9 guard in export (M3); SPDX per pack item (M4); the licence audit and the IC D051 comparison folded into doc 02 for the v1.0 legal review | Sharing extension overlays follows OWQ-06's answer (extension-only for Bohemia's campaigns; third-party parents by licence or recorded permission) and lands in v1.x |
| I34-04 | M2 | A | Intel `resistanceWest`/`East` as a campaign lever, weather and date fields as calendar targets, the voice-language sibling-file rule, sidecar-only zones, phases, named routes and the id map | — |
| I34-05-06 | M1 | B | Fallback fonts (M1); semantic action ids, keymap profiles and the preference-versus-project split (M2); route and accessibility overlays (M4) | — |
| I34-08 | M3 | C, B | Run records with assisted flags, `PreviewBattleReport`, the debrief card and the standalone outcome display. Also M4: tour completion events for Drill | v1.2: postcards (le13), test range and speed control (ed17), director, capture-back and route recording (ed18) |
| I34-09 | M0 docs | F | Doc 09 cross-references (S18 → le03, le07, le10; CO3 → le18; S4 → ed14; M1/M2 → le06, le16; S13/CO2 → ed18); the M2 parity scripts use them | — |
| I34-13 | M6 | D, B | Component presets and the storage panel in the Model Manager | — |
| I34-17 | M0 docs | F | Doc 17's pointer to doc 34 and the "designed" marks for named regions, the outliner, the complexity meter and play from cursor | — |
| I34-18 | M0 docs | F, C | Doc 18 note on the detour-and-return cost. Also M5: the cross-campaign save question as a probe | Reading another campaign's save as a feature (veteran import) waits for that probe (v1.x; OWQ-06 is answered) |
| I34-19 | M5 | G, B | Derived variables and counters, Victory/DefeatCondition, effect sentences, hub-card disclosure, thread lanes, consumers and teaching nodes in the explorer, priority column, standalone preview, outcome lints | v1.x: extension overlays (cw13, OWQ-06 answered) and the veteran-import build option (cw28, probe first) |
| I34-21 | M2 | A, B, D | Per-origin undo lanes as filtered history views (M2); Drill order payoff-first with test-out and a code-validated tour runner (M4); `/` dispatch in chat (M6) | Ribbons (le14) must pass the engagement-ethics rule, doc 36's cv43, a product rule since OWQ-20 (a) |
| I34-22 | M4 | D, E | Manifest fields, T0 kinds tour, tip, module, settings and script-library, the built-in packs rule, plugins shipping tips and tours only for their own tools; RG0 | v1.4: registry phases RG1 onward |
| I34-23-24 | M4 | A | Migration tips from findings, path-resolution hover, MC27, risk rows for the `saveGame` checkpoint and `setAccTime` | — |
| I34-25 | M6 | G, D | Thread lifecycle fields, the MoralComplexity chip, value tags and the ensemble check, one-slot fill rules, lock-based regeneration | v1.1: Mole clues and Nemesis taunts (strategic modules) |
| I34-26 | M5 | G, E | Classic-tier content: persistence modules (Fragments, alignment ladder), §9.3 knobs, §9.4 patterns, the TwistPattern catalogue, CF19–CF25. Also M6: model use | v1.1: strategic-tier rows (sectors cw21, support requests cw25, perk choice cw09, commendations le15, culmination cw06) |
| I34-27 | M1 | C | Lock family, path resolver, drift report (M1); requirement kinds, handoff bundle, server mod lists and D9 (M3) | — |
| I34-28 | M0 docs | F | Provisional MC20–MC29 registered in the DG005 registry with doc 28 §6.3's merges. Also M4 and M5: the rules implemented | — |
| I34-29 | deferred: v1.1 | G | — | The strategic layer, first after v1 (OWQ-13 (a)); its probes join the suite as they become relevant |
| I34-31 | M5 | A, F | Module reconciliation (ed01–ed08, ed10–ed12 module side, ed19; cw23, cw25, cw26, le21, le24), the lowering table and the Show/Eject/Lift contract | — |
| I34-32 | M5 | A | MC25 and MC26 with the Cutscene node; cw23 moments via MC21 | v1.2: ed09–ed12 with the timeline |
| I34-33 | M4 | E | Doc 33 reconciled with le01–le11, le17, le21, le25, cw12 and the tutorial content of mo05 and mo22; the Drill runner | — |

## 6. Items from doc 36 (Civilization V lessons), doc 29 and doc 33

| Item | Owner | Lane | What lands, where | Deferred part |
| --- | --- | --- | --- | --- |
| I36-19 | M5 | G, B | Classic tier default for imported campaigns; ending progress track and CF27; the readiness overlay in the Flow view; the "decided" query | — |
| I36-21 | M4 | A, B | The readiness coach as one dominant control; "no finding lacks both a fix and a dismiss" as a test. Also M6: explain mode with computed "why"s | v1.1: tuning proposals ×2/÷2 with the balance lab (cv30) |
| I36-22-27 | M4 | E, D | T0 identity blocks (faction, site, radio packs, overlays); generated hook and pack-kind references with one example pack each; the vanilla invariant; sharing as export and import with review; rule-override scenarios as T0 data | — |
| I36-25 | M5 | G | Horizon-mix and interesting-decision code gates after S3/S4; an early playable skeleton; few weighty Picks with safe defaults. Also M6: "Make a follow-up campaign" with the rule of 33s, a v1 candidate sized per the roadmap's §10 item 5 | v1.1: SL26's exemption for camps, act breaks and the finale |
| I36-26 | M5 | G, E | ≥ 2 non-passive approaches per archetype (MC30), faction personality records, ≤ 2 local factions, back-half escalation (CF26), discovery slots, off-screen war cues as data. Also M6: model use. The "ending routes" pattern number comes from DG005 | — |
| I36-29 | deferred: v1.1 | G | M4: the rename of `DifficultyPreset::Veteran` in the design round's names table (OWQ-08 (a)) before any code names the type | The strategic rules, status card, bands, bad-luck protection, difficulty rungs and balance-lab policies belong to the strategic layer |
| I36-31 | M5 | A, E | Rule-override presets, an AI-executability note per module, the reinforcements module's default announce cue (MC31) | — |
| I36-32 | deferred: v1.2 | E | — | Music cue pairs and the finale epilogue scene come with the timeline and atmosphere work; custom audio needs licensable assets |
| I36-33 | M4 | E, B | Standing Orders pane in front, instance-or-silent first-opening tips with a usability check, expert density in v1 | v1.1: entries for Plotroom's own strategic campaign rules |
| I29-26-19 | M0 docs | F, G | P9 registered in doc 26 §9.4 and the persistence rows mapped to doc 29's modules (D005). Also M5: P9 in the pattern data marked v1.1; the C and CF registries reference SL codes through DG005 | v1.1: the SL lints implemented |
| I33-SEED-B | M4 | E | Standing Orders entry format (verb-first "what" line; question, picture, example; "Folk wisdom vs engine"; Try-it split into action and observation; own cards and sub-anchors; evidence marks enforced in CI; the tiny-example notation in SKILL.md). Content work may start in M0 | — |

## 7. Summary

| Result | Count | Items |
| --- | --- | --- |
| Lands fully by v1.0 | 31 | I35-PRIMER-FACTS, I35-MOD2, I35-PREV, I35-26, I35-90, I37-IDIOMS, I37-SO, I37-31IDX, I42-08, I29-08, I38-BUDGET, I38-STAGE, I38-GATE, I40-14, I40-25, I42-25, I42-17-30, I34-MERGE, I34-04, I34-05-06, I34-13, I34-23-24, I34-27, I34-28, I34-31, I34-33, I36-19, I36-22-27, I36-26, I36-31, I33-SEED-B |
| Lands by v1.0 with a deferred remainder | 25 | I35-PRIMER-MP, I35-MOD, I35-TPL, I35-CUT, I35-DRILL, I35-GEN, I35-LINT, I35-19, I35-84, I35-MOMENT, I42-22, I42-37, I34-02, I34-08, I34-18, I34-19, I34-21, I34-22, I34-25, I34-26, I34-32, I36-21, I36-25, I36-33, I29-26-19 |
| Docs and indexes only (M0) | 5 | NEW-README, NEW-DGDIR (done), I17-DEC (done), I34-09, I34-17 |
| Deferred to v1.x | 4 | I35-29 (v1.1), I34-29 (v1.1), I36-29 (v1.1; rename in M4), I36-32 (v1.2) |

Each item appears in exactly one row: 31 + 25 + 5 + 4 = 65.

## 8. Differences from the architecture's Appendix A

The architecture gives the design owner and a landing point; this roadmap refines the landing point where the architecture left a "—"
or a range:

- **"—" items now have milestones:** NEW-README, I34-09, I34-17 and I29-26-19 in M0 docs; I34-MERGE in M4 and M5 (lane F); I34-18's
  probe in M5.
- **Earlier or split landings:** I35-GEN's folder-naming lint (rc55) in M2; I42-25's no-model part in M5; I36-26's data and lints in M5
  (architecture: M6), with model use in M6; I36-29's rename in M4 through the names table (OWQ-08 (a)). Four items start one or two
  milestones earlier than the architecture's first landing, because M1 builds their first part: I35-90's evidence tiers in
  `plotroom-profile` (architecture: M2), I35-LINT's read-only rc58, rc66 and rc67 (architecture: M2), I34-05-06's fallback fonts
  (architecture: M2) and I34-02's `NOTICE` and `Derived-From:` headers (architecture: M3).
- **Deferred parts made explicit:** MP rows of I35-MOD, I35-TPL, I35-DRILL, I35-GEN, I35-19 and I35-LINT to v1.3; the music cue of
  I35-MOMENT and the timeline rows of I34-08 and I34-32 to v1.2; vehicle remaps of I35-84 and I42-37 to v1.4; strategic parts of I34-25,
  I34-26, I36-21, I36-25, I36-33 and I29-26-19 to v1.1.

None of these changes contradicts the architecture's dependency order.

## Verification notes

### Roadmap baseline (2026-09-27)

- All 65 items were read from the part-1 inventory (id, source doc and section, target, change) and checked against the architecture's
  Appendix A. Milestone contents follow [m0-m3](m0-m3-foundations-to-preview.md), [m4-v1](m4-v1-power-campaigns-wilco.md) and
  [v1x-and-v2](v1x-and-v2.md).
- Links and hygiene review (2026-09-27): every link here resolves; the status banner now says that the part-1 inventory is a working
  list not kept in the repository, so this appendix and the architecture's Appendix A are the published record of the 65 items.
- Consistency review (2026-09-27): all 65 ids of the inventory appear in both appendices, and every item has an owner or a deferral
  with a reason. §8 now also lists the four M1 starts that differed from the architecture without being named here.
- Owner answers folded (2026-09-27): rows I35-MOD, I35-19, I35-29, I34-02, I34-18, I34-19, I34-21, I34-29, I36-25 and I36-29 now cite
  the owner's answers (OWQ-06, OWQ-08, OWQ-13, OWQ-14, OWQ-20). No item changed milestone.
