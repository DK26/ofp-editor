# Plotroom roadmap

> **Status:** proposal (roadmap baseline 2026-09-27). Milestone names, contents, order, gates and exit evidence are proposals for the
> design round and the owner. Only what restates `AGENTS.md`, a decision record (`Dnnn`), a decided design-gap request (DG002,
> DG013, DG014, DG028, DG029, DG030, DG033 items 3–4) or an owner answer (OWQ-01 to OWQ-23, all answered 2026-09-27 in
> [`OWNER-QUESTIONS.md`](decisions/OWNER-QUESTIONS.md)) is settled. No calendar dates are committed: every milestone is **exit-gated,
> not date-gated**, and sizes are estimated only after the M0 spike reports exist.
> **Builds on:** [`docs/architecture/`](architecture/README.md) (§6 build order, crate "Lands" column), [`docs/decisions/`](decisions/README.md)
> (D001–D043, OWQ-01 to OWQ-23), [`docs/design-gap-requests/`](design-gap-requests/README.md) (DG001–DG038),
> [`docs/upstream/`](upstream/README.md) (ER-001 to ER-109) and research docs 01–48 (46–48: the local runtime, the small-model
> landscape and the cloud plan).

Plotroom is the Mission & Campaign Editor for Arma: Cold War Assault / Operation Flashpoint. This roadmap turns the architecture's
dependency order into milestones from **M0** (foundations and spikes) to **v1.0** (D004: faithful editor, Preview, the Wilco co-pilot
and the describe → generate → edit campaign flow) and on to **v1.x** (the north star, cinematics, replayability, plugins) and **v2**.

## 1. Files

| File | Answers |
| --- | --- |
| `roadmap.md` (this file) | Principles, milestones at a glance, lanes, gates, the v1 definition of done, what is deferred, risks |
| [`roadmap/m0-m3-foundations-to-preview.md`](roadmap/m0-m3-foundations-to-preview.md) | M0 Foundations and spikes, M1 Viewer, M2 Classic editor, M3 Preview beta: goal, scope, crates, dependencies, spikes first, gates, exit evidence, lanes |
| [`roadmap/m4-v1-power-campaigns-wilco.md`](roadmap/m4-v1-power-campaigns-wilco.md) | M4 Modern power and the no-model runtime, M5 Campaigns, M6 Wilco and the model-driven flow, v1.0 hardening |
| [`roadmap/v1x-and-v2.md`](roadmap/v1x-and-v2.md) | v1.1 North star (Operation Grey Heron), v1.2 Cinematics and atmosphere, v1.3 Replayability and multiplayer, v1.4 Extensions and community, v2 and "when the engine ships it" |
| [`roadmap/spikes-and-probes.md`](roadmap/spikes-and-probes.md) | The spike register (SP-01 to SP-16), the probe suites, the local-model qualification track and where results are recorded |
| [`roadmap/integration-owners.md`](roadmap/integration-owners.md) | Appendix: each of the 65 integration items → milestone, or "deferred: reason" |

## 2. Reading conventions

- **Milestones** are `M0`–`M6`, `v1.0`, `v1.1`–`v1.4` and `v2`. Two research families use similar labels: doc 27 §4.12's phases
  M0–M5 are cited here as "doc 27 phase M1"; doc 09 §8.1's parity items M1–M13 as "doc 09 M1". Doc 08 §6's Preview phases are
  "Preview P0"–"P4"; doc 19 §9's campaign phases P0–P4 are "doc 19 phase P1".
- **Acceptance tests** keep their source ids where they are unique: AT-W1–AT-W15 (doc 38 §10), AC01–AC18 (doc 29 §8), DAT1–DAT13
  (doc 39 §10), AMT1–AMT14 (doc 41 §9.2), RAT1–RAT18 (doc 43 §8.2), PAT1–PAT16 (doc 37 §11), MAT1–MAT16 (doc 42 §8.2), E1–E11 (doc 25
  §11.1) and E12 (doc 40 §7). Docs 31, 32 and 33 each number their tests AT1…, so this roadmap prefixes the doc: **31-AT1**, **32-AT6**,
  **33-AT8**.
- **Spikes** are `SP-01`…`SP-16` ([spikes-and-probes.md](roadmap/spikes-and-probes.md)); the prefix is unused elsewhere in `docs/`.
  DG005 (one code registry) should register the `SP-` and milestone families.
- **Precedence** follows the architecture README §1: `AGENTS.md` > accepted decision records > `docs/architecture/` > research proposals.
  Where this roadmap and the architecture's §6 table differ, this roadmap refines milestone contents and the architecture keeps the
  dependency order; a real contradiction is a design-gap candidate (§10).

## 3. Principles (proposal)

1. **Faithful first, layers after.** The first release that earns the community's trust is the original editor, standalone, with undo,
   non-blocking lints and one-click Preview (doc 09 §8; D004 item 1). AI and campaigns arrive as layers over seams built from M2 on, never
   by re-architecture (architecture README §2).
2. **Evidence closes a milestone** (`AGENTS.md`, Evidence Rule). Each milestone lists named tests, round-trip captures, golden images,
   probe results, acceptance tests and manual verification notes. "Implemented" without them is not done. Each milestone ends with an
   **exit report**: a dated verification note in the milestone's section listing the CI run, test names, spike reports and manual notes.
3. **Spikes before the code they de-risk**, each with a go/no-go stated in advance (doc 06 §7; doc 08 §6 P0; doc 13 §11; doc 44 §5.4). A
   failed spike reopens the baseline record it names ("Revisit if", `docs/decisions/README.md`), not the milestone plan silently.
4. **Design gaps gate code per milestone, not all in M0** (architecture README §7 row 27). Work that depends on an open DG stays
   `proposal-only` or `blocked on DGnnn` (`AGENTS.md`, Design Authority).
5. **Ported upstream tests travel with the code** (D013): the crate that ports behaviour ports its tests and updates
   `docs/porting/upstream-test-map.csv` in the same change set; in-game-only tests become probes.
6. **AI-off first.** Every workflow runs on seeded defaults before any model call exists: a faux model in M4, the campaign flow without
   a model in M5, real models in M6 (D004; D009; doc 21 §1.1 rule 7). The no-model path is the baseline each AI feature must beat.
7. **Maximum within the engine** (D012). Every limitation met on the way becomes an `ER-###` row in the same change set; no milestone
   depends on an engine change. Community-engine features become opt-in `Ce` capabilities when shipped (§8.3).
8. **Public release gates.** The owner decided what each gate is (2026-09-27); the actions remain. Nothing public before the clearance
   search is recorded in doc 02 and the repository is renamed (OWQ-07; descriptor placement decided as DG002 option A), the Bohemia
   letter is answered or a documented decision to proceed exists (OWQ-10 (a): one letter after the clearance), and the private security
   reports are sent (OWQ-09 (a)) (architecture README §7 row 35).
9. **Tests and builds by the owner's rule.** Agents validate with `cargo clippy`, `cargo test`, `cargo check` and `cargo fmt --check`;
   running the app, the game or local models is done by the user, and results come back as verification notes (`AGENTS.md`).

## 4. Milestones at a glance

| Milestone | Version | Goal | Headline exit evidence | Needs first | Detail |
| --- | --- | --- | --- | --- | --- |
| **M0** Foundations and spikes | — | A workspace that enforces `AGENTS.md` mechanically, and go/no-go answers for the riskiest assumptions | 3-OS CI green; `xtask layers` fails on a planted bad edge; reports for SP-01–SP-07 and SP-09–SP-12 | DG005, DG011 decided before M1/M2 code | [m0–m3](roadmap/m0-m3-foundations-to-preview.md#m0-foundations-and-spikes) |
| **M1** Viewer | 0.1 (tester build) | Open any mission from a real install and show it faithfully, read-only, with a per-profile lint report | Ported format rows; `render(parse(b)) == b` properties; fuzz clean; map goldens; MAT2–MAT5, MAT11, MAT16 | Renderer spikes SP-01–SP-03 go; SP-09 (CST) go | [m0–m3](roadmap/m0-m3-foundations-to-preview.md#m1-viewer-01) |
| **M2** Classic editor | 0.2–0.3 (tester builds) | Faithful editing with undo, non-blocking checks, lossless save and PBO export | Kernel invariants; one-action-one-undo family; byte-identical unchanged save; PAT1; doc 09 M1–M13 parity scripts | SP-04, SP-05 go; SP-10 benchmark; SP-08's 1.99 exporter answer; DG017 and architecture §8 candidates 1–5, 9, 10 decided | [m0–m3](roadmap/m0-m3-foundations-to-preview.md#m2-classic-editor-0203) |
| **M3** Preview beta | 0.5 (first public) | One-click Preview in the real game from unsaved edits; export that proves its dependencies | StagePlan goldens; fake-binary and fake-harness tests; MAT12; probe results on Remastered and CE; export-scan goldens | SP-06, SP-07 answered; before public release: OWQ-07's clearance and rename, OWQ-10's letter, OWQ-09's reports (§3 item 8) | [m0–m3](roadmap/m0-m3-foundations-to-preview.md#m3-preview-beta-05) |
| **M4** Modern power, knowledge, no-model runtime | 0.6 | Teller, text editors, attributes and power tools, templates, Standing Orders and Drill track A, T0 packs, and the workflow runtime proven with a faux model | AT-W1–AT-W5, AT-W7, AT-W12–AT-W14; 33-AT1–33-AT5; PAT2, PAT3, PAT5, PAT7, PAT8, PAT12–PAT14, PAT16; crash at every journal entry | DG003, DG007, DG008 (`when`), DG010, DG015, DG016, DG017, DG018, DG031, DG032, DG033 items 1–2 (OWQ-14 (a) and OWQ-15 (a) answered) | [m4–v1](roadmap/m4-v1-power-campaigns-wilco.md#m4-modern-power-knowledge-and-the-no-model-runtime-06) |
| **M5** Campaigns | 0.7–0.8 | Typed, verified, editable campaigns (Plotline, the Tote, CXL, compiler, Path Explorer, import), modules wave 1, the Cutscene node, and the campaign flow **without a model** | CXL interpreter-vs-lowering property; compile goldens; Preserve import byte identity; AT-W9–AT-W11 at T0; 31-AT1 (SP), 31-AT2–AT4, AT7, AT8, AT10–AT14; Grey Heron structural fixture (AC05, AC12, AC13) | DG004, DG008, DG009, DG035 (OWQ-13 (a) answered: classic patterns); the 1.99 probe run (SP-08) before freezing `Cwa199` lowering | [m4–v1](roadmap/m4-v1-power-campaigns-wilco.md#m5-campaigns-0708) |
| **M6** Wilco and the model-driven flow | 0.9 | Providers, the Model Manager, Wilco, the campaign flow with models and cost UX, all off by default and on the same admission path | AT-W6, AT-W8, AT-W10, AT-W11 with models; E1–E12 with controls; prefix-stability and token-budget CI; doc 13 S1, S2, S4, S5; PAT9; 31-AT5; MAT1, MAT10 | SP-12–SP-14; the qualification track (doc 44 §5.4 items 2–10; doc 46 has run items 3, 4 and part of 9; doc 49 in preparation); DG006, DG012, DG015, DG019–DG027; OWQ-19 (a) and the owner's local-runtime decision (D022 amendment note) applied | [m4–v1](roadmap/m4-v1-power-campaigns-wilco.md#m6-wilco-and-the-model-driven-flow-09) |
| **v1.0** | 1.0 | M1–M6 hardened into D004's four things | §7's definition of done | OWQ-01 (b)'s wording in `NOTICE`; OWQ-02 (a) applied; OWQ-13 (a) and OWQ-14 (a) scope met; DG002/OWQ-07 applied; OWQ-10's letter answered or a decision to proceed; legal review (doc 02) | [m4–v1](roadmap/m4-v1-power-campaigns-wilco.md#v10-hardening-and-release) |
| **v1.1** North star | 1.1 | The strategic layer and "Operation Grey Heron" (D005) | AC01–AC15, AC17, AC18; AC16 human panel for the "north star achieved" claim | OWQ-13 (a), OWQ-20 (a), OWQ-23 (answered; re-confirmed after the first balance-lab runs); doc 29 probes PR01–PR22 | [v1.x](roadmap/v1x-and-v2.md#v11-north-star-the-strategic-layer-and-operation-grey-heron) |
| **v1.2** Cinematics and atmosphere | 1.2 | The cinematics timeline, the cutscene director, atmosphere and audio | 32-AT1–32-AT10; DAT1–DAT13 (DAT6 headline); AMT1–AMT14 | DG009, DG034–DG037; probes CP1–CP13, AP1–AP18 | [v1.x](roadmap/v1x-and-v2.md#v12-cinematics-and-atmosphere) |
| **v1.3** Replayability and multiplayer | 1.3 | Seeded variety at mission and campaign scale; multiplayer Preview and modules | RAT1–RAT18; PAT10; 31-AT1 re-run in MP Preview | DG038 (OWQ-20 (a) and OWQ-21 (a) answered); probes P-R1–P-R12 | [v1.x](roadmap/v1x-and-v2.md#v13-replayability-and-multiplayer) |
| **v1.4** Extensions and community | 1.4 | T2 connectors and feeds, T1 WASM plugins, the pack registry RG1, community mod directory and catalog | MAT9, MAT10 (connector on), MAT14, MAT15; T1 adversarial suite; doc 22 step 2–3 evidence | Decided by the owner: DG014 option B (OWQ-16), DG029 option A (OWQ-12), DG030's four proposals (OWQ-17), OWQ-03 (a); the channel maintainers' non-objection before the community sources ship | [v1.x](roadmap/v1x-and-v2.md#v14-extensions-and-community) |
| **v2** | — | Registry RG2–RG3, in-process inference, optional 3D view, gamepad, a decision model in front of the generator | — | Named per item | [v1.x](roadmap/v1x-and-v2.md#v2-and-later) |

The owner answered OWQ-13 with option (a) on 2026-09-27: the classic patterns ship in v1, and the strategic layer and Grey Heron are
the first milestone after v1 (v1.1).

## 5. Dependency order

```text
 M0 ──► M1 ──► M2 ──► M3 ──► M4 ──► M5 ──► M6 ──► v1.0 ──► v1.1 (north star)
 │ spikes │      │      │      │      │      │               v1.2 (cinematics, atmosphere)   needs M3 live link, M5 Cutscene node
 │        │      │      │      │      │      │               v1.3 (replayability, MP)        needs M5 campaign scale, Preview P4
 │        │      │      │      │      │      │               v1.4 (plugins, registry)        needs M4 T0 packs, M6 `plotroom-net`
 │        │      │      │      │      │      └─ real models, Model Manager, cost UX
 │        │      │      │      │      └─ campaign model, compiler, simulator, no-model flow (1.99 probe run gates Cwa199 lowering)
 │        │      │      │      └─ runtime + journal with a faux model, Teller, packs, Standing Orders, Drill
 │        │      │      └─ Preview staging, launch, live link, export gates (P0 answers first)
 │        │      └─ kernel, commands, sidecar, dialogs (renderer spikes 4–5, CST patch, snapshot benchmark first)
 │        └─ formats, VFS, catalog, terrain, renderer, map (renderer spikes 1–3 first)
 └─ lane D from day one: local-model confirmation run (SP-11), provider-wire spike (SP-12); doc 13 spikes before M6
```

v1.1–v1.4 are independent of each other except where noted; their order is a proposal and may interleave.

## 6. Lanes

Work proceeds in parallel lanes (architecture README §6 names A–D; this roadmap adds E–G). A lane owns its deliverables in every
milestone; a milestone closes when all lanes' exit evidence is in.

| Lane | Owns | M0 | M1 | M2 | M3 | M4 | M5 | M6 | v1.0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **A** Core and formats | Formats, kernel, models, commands, validation | Workspace, lints, `xtask`, SP-09, SP-10 | L0–L2 crates, read lens | Kernel, sidecar, commands, session, save | Export scans, manifests | Attributes, lowering (attributes) | CXL, modules, rules, lowering | — | Hardening, corpus |
| **B** Renderer and shell | `plotroom-draw2d`, `-gpu`, `-map2d`, `-ui-classic`, `-ui` | SP-01–SP-05 | Map, fonts, shell | Classic dialogs, inspector, panels | Preview log, run report | Script, text, Standing Orders, Drill panels; plan card, run panel, decision inspector | Plotline, the Tote | Wilco, cost UX on the plan card and run panel, Model Manager UI | Accessibility pass |
| **C** Game integration | Installs, VFS, catalog, Preview, probes | SP-06, SP-07 (P0) | Discovery, VFS, catalog | Harness spike prep | Staging, launch, live link, probe runner | "Show me in game" demos | Campaign prologue, SP-08 1.99 run | Model unload before launch | Manual runs per OS |
| **D** AI de-risking and harness | Provider seam, runtime, decision kernel, evals, Model Manager | SP-11, SP-12 | Python suites stay in `tools/local-qual` | Faux-model state machine in `plotroom-testkit` (optional) | `plotroom-workflow` started once DG007 is decided | Runtime + journal + faux model | Fan-out, campaign flow at T0 | Providers, net, Model Manager, Wilco, evals | Qualification records |
| **E** Knowledge and content | Primer, Standing Orders, Drill, templates, compositions, module catalogue | Entry format fixes | — | Relabels beside original labels (D029) | Standing Orders seed entries and Drill lesson scripts in draft | Primer MP and facts, entries, Drill track A, templates, compositions | Module catalogue data, archetypes, moment cards | Cards for model steps | English content complete (OWQ-14 (a)) |
| **F** Design and docs | DGs, decisions, doc folds, register, outreach prep | `docs/README.md`, file architecture §8 candidates, doc folds | DG005 registry live | DG017 | OWQ-07 clearance and rename; OWQ-09 reports; OWQ-10 letter | DG003/007/031–033 | DG004/008/035 | DG006, DG012, DG019–DG027 | OWQ-01 (b) wording, legal review |
| **G** Campaign | Campaign model, compiler, simulator, flow | — | — | — | — | Grey Heron fixture design | All of M5 | Flow with models | Import corpus |

## 7. What v1 is (definition of done, proposal)

v1.0 ships when each of D004's four things has its evidence (details in
[m4-v1](roadmap/m4-v1-power-campaigns-wilco.md#v10-hardening-and-release)):

| D004 item | v1 evidence |
| --- | --- |
| 1. Faithful editor | Doc 09 M1–M13 parity scripts green (kittest plus manual notes); byte-identical save of unchanged missions on synthetic fixtures and an opt-in local corpus report (hashes and counts only); PAT1, PAT14; kernel invariants and the one-action-one-undo family; Easy/Advanced with original labels and relabels beside them (D029) |
| 2. Preview in the real game | Strict Preview from unsaved edits on Remastered and CE, Validate, from camera, Intro/Outro, campaign-node prologue; export-and-open on 1.99; manual verification notes per supported OS; `--private` on every launch after its probe (MAT12) |
| 3. Wilco, optional co-pilot | Off by default with no provider and no network (test); a weak local model (T1, "spike-checked" badges) runs PAT9 and 31-AT5 and the campaign flow; cost UX (plan card, meter, caps, dated prices); zero clobbers (E9); AT-W6, AT-W8 |
| 4. Campaign flow, first-class | Describe → generate → edit for the classic patterns (OWQ-13 (a)); a campaign compiles for its profile with and without a model (E10 = 100 %; AT-W11); Preserve import re-saves byte-identical; every generated element inspectable (AT-W8; AC12 on the Grey Heron fixture) |

Plus: every v1 feature works with AI off; CI green on Windows, Ubuntu and macOS; `CODE-INDEX.md` current; no upstream-test-map row
left `todo` in an area whose crate shipped without a recorded reason; OWQ-01 (b)'s wording in `NOTICE`; legal review done (doc 02).

## 8. Deferred to v1.x and v2 (summary)

### 8.1 v1.x

| Deferred | To | Reason | Reopen trigger |
| --- | --- | --- | --- |
| Strategic layer, balance lab, Grey Heron acceptance (doc 29) | v1.1 | Owner, OWQ-13 (a); needs the balance lab and ~20 1.99 probes | An owner decision replacing OWQ-13 (a) |
| Cinematics timeline, live shot preview, capture-back (doc 32 phases 1–4) | v1.2 | Owner, OWQ-14 rung 4 (a): v1 ships the Cutscene-node recipe with camera scripting through the script editor (architecture README §7 row 28) | An owner decision replacing that answer |
| Cutscene director (doc 39) | v1.2 | Owner, OWQ-14 rung 4 (a); needs the timeline, exact terrain height and probes CP1–CP13 | As above |
| Atmosphere, sound and music; `plotroom-audio`; `.lip` port (doc 41) | v1.2 | Same timeline and probe dependencies; audio import needs licensable assets | — |
| Replayability variants, seeds, remix, Seed Atlas (doc 43 RV0–RV4) | v1.3 | Builds on the M5 campaign scale; MP parts need Preview P4 | — |
| Multiplayer Preview (Preview P4), MP modules (doc 31 L4), locality-verified lowering (doc 37 PT4) | v1.3 | D004 consequence: MP Preview follows its own phase plan | — |
| T2 connectors and feeds, T1 WASM and SDK, registry RG1 (docs 22, 42) | v1.4 | D004 consequence; DG014, DG030 and OWQ-03 are decided; the community sources wait for DG029's outreach (OWQ-12) | Non-objection recorded per channel |
| `workflow.decide` for external agents | v1.4 | Owner, OWQ-15 (a) | An owner decision replacing OWQ-15 (a) |
| Drill track B/C, community lessons, non-English content (doc 33 phase 6) | v1.4 | Owner, OWQ-14 (a): English first, locales as native reviewers join | Reviewers available |
| Extension overlays (doc 34 cw13), veteran import (cw28) | v1.x | OWQ-06 answered (extension-only for Bohemia's campaigns; third-party parents by licence or permission); a probe on reading another campaign's save | Probe passes |
| SP ↔ MP wizard and island move (doc 37 PT3's remainder) | v1.3 | The wizard needs MP Preview; island move (PAT6, a dry-run report) ships with it | — |

### 8.2 v2 and later

Registry RG2–RG3 (doc 42 §5.1); in-process embedded inference (doc 13 phase C, S3; out-of-process helper per architecture README §8
item 7); an optional 3D placement view (doc 09 CO1); gamepad and Steam Deck input (doc 09 CO14); a decision model in front of the
generator only if it beats both selectors (D023 item 5).

### 8.3 "When the engine ships it" (no milestone)

Tolerant Preview and the debug console (Preview P3; ER-001, ER-002, CE #35; DG001), campaign test launch at a chosen row (ER-007),
opt-in campaign keys (ER-027 and the filing plan's wave 5) and other `Ce` capabilities are adopted when the community engine ships them,
detected by the capability probe, opt-in and visible per mission (`docs/upstream/README.md`, "From a shipped change to a target-profile
capability"). They may land in any v1.x release and never gate one.

## 9. Risks and mitigations

| Risk | Signal | Mitigation |
| --- | --- | --- |
| The renderer composite or classic focus handling fails (SP-01, SP-04) | Spike exit criteria missed after 2 extra days | Switch to raw winit + egui-winit before building more (doc 06 §7 go/no-go); D016 reopens |
| Shipping builds drop or change the test flags Preview relies on | P0 answers; capability probe on each install | Export-and-open fallback always available; flags documented upstream (ER-002, ER-008) |
| 1.99 behaviour stays unverified | Probe backlog (doc 19 OQ1, doc 29 §9, doc 37 PP rows) | Conservative subset; degraded fallbacks; "verified on 1.99" badges only after probes (D003) |
| Weak local models do not reach pass^k on the shapes granted | SP-11 and M6 qualification | Pick with cards; Fill as a confirmed pre-fill; knowledge from cards only (doc 44 §4); the no-model path stays complete |
| The DG backlog stalls code | A milestone's gate list still open at its start | Per-milestone gating (§6 of the architecture); technical DGs decided from evidence in the design round; defaults recorded explicitly |
| v1 scope creep | Items outside the OWQ-13 (a) and OWQ-14 (a) answers proposed for M5 or v1.0 | Hold M5 and v1.0 to the answers; everything else goes to the v1.x list above |
| The local runtime is slow on older GPUs | Doc 46: Vulkan prompt processing 2–3× slower than Ollama on a Pascal card; warm Pick p50 about 1.1 s | Short, prefix-stable step prompts; the user-started upstream CUDA build if doc 49's bench supports it; bring-your-own Ollama or LM Studio; latency quoted as typical only after other GPUs are measured |
| Cloud cost surprises users | E12 and ledger data | Doc 40 rules R1–R17: dated prices, caps, adaptive K, cache-stable capsules, $0 path on every plan card (D026) |
| Legal or naming problems at first release | Clearance search, repository rename, OWQ-01 (b) wording or the OWQ-10 letter not done at M3 | Public release gated; letter to Bohemia; clearance search recorded in doc 02 |
| Upstream drift in CWR-CE | The read-only watch job (doc 01 §11) | Pinned SHAs; re-read hook points before filing (`docs/upstream/README.md`) |
| Three-OS CI grows too slow | CI time per push | Tiering (testing-strategy §14): unit and property per push, goldens per pull request, fuzz nightly |

## 10. Open questions and design-gap candidates

1. **Sizes and dates.** Set after the M0 exit report, from spike effort and the first two format crates' velocity.
2. **Where spike reports live.** Proposal: `docs/spikes/SP-nn-<slug>.md`, created with the first report ([spikes-and-probes.md](roadmap/spikes-and-probes.md) §1).
3. **Public cadence.** Whether M1 and M2 tester builds are public pre-releases is tied to OWQ-07's clearance and rename and OWQ-10's
   letter (both decided in kind, neither done yet).
4. **M4 size.** M4 is the widest milestone; it may split into M4a (Teller, text editors, power tools, packs) and M4b (runtime,
   Standing Orders, Drill) if the M2 exit report shows the kernel lane finishing late.
5. **The outcome-matrix builder and "Make a follow-up campaign"** (doc 35 rc82; doc 36 rule of 33s): OWQ-13 (a) does not name them.
   Proposal: treat them as v1 candidates inside the classic-pattern scope and size them after the M5 exit report (architecture
   agent-runtime §10).
6. **Design-gap candidates raised here:** none beyond the architecture README §8 list; the milestone-label collisions in §2 go to DG005.

## Verification notes

### Roadmap baseline (2026-09-27)

- Read for this baseline: `AGENTS.md`; `docs/architecture/` (README in full; crate-map, game-integration, testing-strategy in full;
  agent-runtime §3, §7–§16; ui-shell §6–§12; validation-and-lints §10–§11; extensibility §3–§10); `docs/decisions/README.md`, D003, D004,
  D005, D016, D022, D023, D024, `OWNER-QUESTIONS.md`; `docs/design-gap-requests/README.md`; `docs/upstream/README.md` and the summary and
  filing plan of `engine-requests.md`; the phased plans and acceptance tables of docs 06 §7, 08 §6, 13 §11, 19 §9, 20 §3, 22 §7.1, 25
  §11.1, 27 §4.12, 29 §8, 31 §10, 32 §7, 33 §9, 37 §11, 38 §10, 39 §10, 40 §6–§7, 41 §9, 42 §5.1 and §8, 43 §8, 44 TL;DR and §5.4;
  doc 09 §8; doc 45 TL;DR; the integration-item inventory of the part-1 pass (65 items).
- Thresholds quoted from research docs are their placeholders and proposals; this roadmap adds no new numeric target except where it
  cites one.
- No research doc, decision record, DG, register row or `AGENTS.md` was edited by this change.

### Consistency review (2026-09-27)

- Lane B now shows the plan card, run panel and decision inspector in M4 (as the M4 file says) and only their cost UX in M6. M4's
  gates add DG008 (`when` predicates), DG015 (its load-refusal fixture is M4 exit evidence) and DG017, matching the crate map's
  "Blocked on" column. The v1.0 row lists the same release gates as the v1.0 section of the M4–v1 file. The first 1.99 run (SP-08)
  moves before M2 freezes the `.plotroom/` spelling ([spikes-and-probes.md](roadmap/spikes-and-probes.md) §4.2).
- In the milestone files: `plotroom-cxl` may land in M4 for the workflow `when` scope (DG008); M5's Plotline names the visual
  condition builder (`AGENTS.md` glass box; doc 19 §5); M6 gates on the architecture README §8 item 6; the Standing Orders pane opens
  from the help action, since F1 is the Units mode key in the Classic keymap. The v1.2 deferral of the cinematics timeline and
  director now has a reopen trigger, OWQ-14's rung-4 item (D015 item 4).

### Owner answers folded (2026-09-27)

- The owner answered OWQ-01 to OWQ-23 on 2026-09-27 with the recommended options and decided the local runtime (the managed
  `llama-server` sidecar; D022 amendment note). This file now states them as decisions: §3 item 8 (the release gates are decided in
  kind; the actions remain), §4 (gates per milestone), §6 (lanes E and F), §8.1 (reasons and reopen triggers), §9 (scope-creep and
  legal rows; a new local-runtime latency row from doc 46), §10 items 3 and 5. Milestone contents and order are unchanged; the
  outcome-matrix sizing in §10 item 5 is a proposal. The cloud measurements of doc 48 are deferred by the owner until doc 49 exists.

### Consistency review of the owner answers (2026-09-27)

- The header now names the decided DGs of 2026-09-27 (DG002, DG014, DG029, DG030) and the records D031–D043 that state the owner's
  answers; the OWQ citations in this file stay valid, since each OWQ's Summary row in `OWNER-QUESTIONS.md` names its record. No
  milestone content changed.
