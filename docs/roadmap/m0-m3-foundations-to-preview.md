# Roadmap: M0 to M3 (foundations to the Preview beta)

> **Status:** proposal (roadmap baseline 2026-09-27). Part of the [roadmap](../roadmap.md). Crate names follow
> [`docs/architecture/crate-map.md`](../architecture/crate-map.md) and are final only when `CODE-INDEX.md` records them. Spike ids
> (`SP-nn`) are defined in [spikes-and-probes.md](spikes-and-probes.md); acceptance-test ids follow the roadmap's §2 conventions.

Each milestone lists: **goal**, **scope**, **out of scope**, **crates** (land = created here; grow = extended), **depends on**, **spikes
and probes first**, **gates** (DGs and owner questions that must be decided before the dependent code), **exit evidence**, **parallel
lanes** and the **integration items** that land here ([integration-owners.md](integration-owners.md)).

## M0 Foundations and spikes

**Goal.** A workspace that enforces `AGENTS.md` mechanically, plus go/no-go answers for the assumptions that would force a
re-architecture if they failed: the renderer composite, classic dialog input, Preview flags on shipping builds, the lossless CST patch,
snapshot cost, weak local models and provider wires. No user-facing release.

**Scope.**

- **Workspace.** Cargo workspace, edition 2024; release profile `lto = true`, `codegen-units = 1` (`AGENTS.md`, heap policy rule 7);
  workspace lints `unsafe_code = "forbid"` and the clippy deny set (crate-map §2.4), `arithmetic_side_effects` for format crates;
  per-crate `disallowed-methods` for `std::fs`, `std::process`, `std::net` and `std::env::var` outside the edge crates (crate-map §2.3).
- **`xtask`**: `layers` (the declared layer table checked against `cargo metadata`, crate-map §2.5), `codes` (generated from the DG005
  registry once decided), `catalog` skeleton (doc 23 §14), `skills` (SKILL.md index).
- **CI** on Windows, Ubuntu and macOS: `cargo fmt --all --check`, `cargo clippy --workspace --all-targets --locked -- -D warnings`,
  `cargo test --workspace --locked` (doctests included, never `no_run` or `ignore`); cargo-deny (GPL-3.0-compatible allowlist, GPL-2.0-only
  banned, per-layer feature bans); REUSE/SPDX; the public-hygiene grep (third-party marks and island names in crate, module, format,
  sidecar and generated-header names; private project names) (testing-strategy §14); a nightly `fuzz/` workspace skeleton.
- **`CODE-INDEX.md`** (required by `AGENTS.md`) with the crate table, landing milestones and the newtype table; **`docs/README.md`**, the
  design-authority entry point `AGENTS.md` names (NEW-README).
- **Spikes** SP-01–SP-07 and SP-09–SP-12, each with a short report and a go/no-go ([spikes-and-probes.md](spikes-and-probes.md) §2).
  Spike code lives in the crate that will own the result (`plotroom-draw2d`, `plotroom-gpu`, `plotroom-rsc`, `plotroom-ui-classic`,
  `plotroom-config`) or in a throwaway tool; code from a failed spike is deleted, not kept.
- **Design and docs lane.** File the architecture README §8 design-gap candidates (sidecar spelling and export; three `Origin` types;
  128-bit ids for campaign elements; live groups; lowering failure classes; no agent eval in Preview; out-of-process embedded
  inference; campaign layout; provenance granularity; two journals) and the DG index's "noticed but not filed" candidates
  (cutscene-section staging; workflow definitions replacing doc 25's `Stage` enum; generated file names). Fold the decided DGs (DG013,
  DG028, DG033 items 3–4) and the pure doc-fold integration items into the research docs (integration-owners.md, "M0 docs").
- **Owner answers to apply now** (all answered 2026-09-27): OWQ-02 (a) (docs are GPL-3.0-or-later, for the REUSE headers), OWQ-05 (a)
  (DCO, for the CI check; AI assistance allowed, `Assisted-by:` optional), OWQ-07 (descriptor placement per DG002 option A; the
  clearance search and repository rename gate M3's public release), OWQ-09 (a) (the owner's private security reports precede any
  public detail).

**Out of scope.** Any product crate beyond spike code; any game data in the repository (doc 05; D016 item 3).

**Crates.** Land: `xtask`, `plotroom-testkit` (skeleton: fixture root, blob builder, seeded `IdSource`, virtual clock; doc 20 §3
"shared prerequisites"). Spike versions: `plotroom-draw2d`, `plotroom-gpu`, `plotroom-rsc`, `plotroom-ui-classic`, `plotroom-app` (shell),
`plotroom-config` (CST patch).

**Depends on.** Nothing.

**Spikes and probes first.** This milestone *is* the spike milestone. Order: SP-01 and SP-06/SP-07 first (the two go/no-go gates with
the widest blast radius), then SP-02–SP-05, SP-09, SP-10; lane D runs SP-11 and SP-12 independently.

**Gates (decided before the M1/M2 code that needs them).** DG005 (one code registry: `plotroom-diag` is generated from it; it also
registers MC20–MC29, the `Dnnn`, `OWQ-nn`, `SP-nn` and milestone families); DG011 (`Admitted<T>` or `Checked<T>`, and what a changed read
does; needed by `plotroom-doc`).

**Exit evidence.**

1. CI green on all three OSes for fmt, clippy, tests and doctests; the run link goes in the exit report.
2. `xtask layers` fails on a deliberately bad edge (an L6 crate depending on `plotroom-session`); cargo-deny rejects a planted
   GPL-2.0-only dev dependency; the hygiene grep rejects a planted mark in a crate name. Each is a committed negative test.
3. Spike reports SP-01–SP-05 against doc 06 §7's exit criteria: swatch bytes match in a screenshot; windowed ↔ borderless ↔ monitor
   switch works; 1-px lines stay crisp from 100 % to 150 % DPI; `DrawList` insta snapshots stable; headless goldens pass on WARP and
   lavapipe; map zoom and pan ≥ 60 fps on an integrated GPU and ≥ 10 fps on WARP with recorded frame times; Tab and focus stay in the
   classic view; a Japanese IME composes into a classic edit box (manual Windows note); Accessibility Insights lists classic controls with
   roles and names; a detached chat viewport keeps working. **Go/no-go:** if SP-01's colour check or SP-04's focus handling fails and
   cannot be fixed in two extra days, switch to raw winit + egui-winit before building more (doc 06 §7; D016 "Revisit if").
4. SP-06 and SP-07 answers recorded as verification notes in doc 08 and in `docs/architecture/game-integration.md` §14 open question 1,
   with the affected `ER-###` rows (ER-004 to ER-007) updated in the CSV and the rendered register in the same change set.
5. SP-09: `render(parse(b)) == b` property on synthetic configs with injected trivia; a patch test proving bytes outside the patched span
   are unchanged; a table of doc 04's writer rules with one passing test each.
6. SP-10: the commit-plus-snapshot-publish time on a 5,000-entity synthetic mission recorded against the < 2 ms target (ui-shell §11);
   the result decides whether the document-thread fallback is needed (doc 45 OQ5).
7. SP-11: the confirmation run's rows added to `docs/research/data/local-qualification.csv` with a dated note in doc 44; it feeds DG006
   (menu cap) and DG012 (requalification triggers).
8. SP-12: the provider-wire report states whether D021's baseline (an exact-pinned rig inside one adapter crate) stands.
9. `CODE-INDEX.md` and `docs/README.md` exist and link the architecture, decisions, DGs, upstream register and this roadmap.

**Parallel lanes.** A (workspace, SP-09, SP-10); B (SP-01–SP-05); C (SP-06, SP-07, run by the owner on real installs); D (SP-11,
SP-12); F (DG filing and folds, owner questions). Lanes E and G have no M0 work beyond the Standing Orders entry-format fixes
(I33-SEED-B) that the content lane can start at any time.

**Integration items.** NEW-README, NEW-DGDIR, I17-DEC, I34-09, I34-17, I34-18 (doc note), I29-26-19 (doc fold), I38-STAGE (doc note),
I38-BUDGET and I38-GATE (doc 21 notes), I40-14 (doc 14 fold), I35-84 (label rename), I34-28 (MC20–MC29 registered), I42-08 and I29-08
(as SP-07 questions).

## M1 Viewer (0.1)

**Goal.** Open any mission, from a folder or a PBO, from a real install (Remastered, GOG, CE, 1.99 data, or the free demo's data where
SP-06 shows it is enough), and show it on the classic map as the original editor would, read-only, with a per-profile lint report and a
headless `plotroom check`.

**Scope.**

- **L0:** `plotroom-bytes` (safe-read cursor, varint, BI LZSS with both checksum kinds, `Caps`), `plotroom-ids` (newtype macro and the
  id types; `IdSource`, `Clock`, `Seed`), `plotroom-encoding` (legacy code pages, UTF-8, hidden-character scan), `plotroom-profile`
  (`Cwa199`/`Cwr`/`Ce`, evidence tiers T1–T4, capability ids = `ER-###`; I35-90), `plotroom-diag` (generated from DG005).
- **L1 formats:** `plotroom-pbo`, `plotroom-preproc`, `plotroom-config` (CST, resolved view, raP read v2–4), `plotroom-stringtable`,
  `plotroom-wrp`, `plotroom-p3d` (map-info subset), `plotroom-paa`, `plotroom-fxy`, `plotroom-rsc` (read). Each with one `Error` enum,
  a thin `read.rs` over the shared cursor, caps from the engine's hardened limits, and fuzz targets (D017).
- **L2 world facts:** `plotroom-vfs` (mount order base → `res` → mods, PBO-stem prefixes, case-insensitive lookup, `#include`
  confinement, "who serves this file"), `plotroom-install` (pure VDF/ACF discovery for Steam app 65790, the demo app 4819000 marked as
  "data only, no editor executable", GOG, user-chosen CE builds and 1.99; spawns nothing), `plotroom-catalog` (engine-parity config
  merge in `requiredAddons` order, class provenance, unit cards with `basis`, facets, mod sets and the `*.modset.toml` lock format,
  drift report, `addOns` derivation), `plotroom-terrain` (heights, roads, objects, places with fallback clusters).
- **Read-only document path:** `plotroom-doc` types, `plotroom-mission` read lens and descriptor tables, `plotroom-project` read-only
  store and snapshots, `plotroom-validate` read-only runner with engine-structural and limit rules (rc58, rc67), `plotroom-io` read side
  (`ReadOnlySource`).
- **Shell and map:** `plotroom-draw2d`, `plotroom-gpu`, `plotroom-fonts` (FXY, OFL and TTF fallbacks; doc 34 mo23), `plotroom-map2d`,
  `plotroom-ui` (shell, docking, outliner read-only, problems panel read-only), `plotroom-app`, `plotroom-cli` (`plotroom check`: per-profile
  lint report, round-trip check).
- `NOTICE` with Bohemia's §7 terms when the first CWR-derived file lands (D001), and `Derived-From:` headers on ported files (D017).

**Out of scope.** Any write path; dialogs beyond read-only inspection; Preview.

**Crates.** Land: the L0, L1 (except `plotroom-briefing`, `-script`, `-script-catalog`, `-audio`) and L2 crates above; `plotroom-doc`
(types), `plotroom-mission` (read), `plotroom-project` (read-only), `plotroom-validate` (read-only), `plotroom-io` (read),
`plotroom-draw2d`, `plotroom-gpu`, `plotroom-fonts`, `plotroom-map2d`, `plotroom-ui`, `plotroom-app`, `plotroom-cli`.

**Depends on.** M0: SP-01–SP-03 go, SP-09 go; DG005 decided.

**Spikes and probes first.** SP-06's discovery answers (paths, demo data sufficiency, Linux runtime) before `plotroom-install` fixtures
are frozen.

**Gates.** DG005 (codes in `plotroom-diag`).

**Exit evidence.**

1. **Ported upstream rows**, in doc 20 §3's order, each updating `docs/porting/upstream-test-map.csv` in the same change set:
   formats-pbo (11), formats-config (23), formats-wrp (13), formats-p3d (10), formats-paa (15), formats-font (4), platform-paths (5; its
   probe row stays `probe`), map-render (1). Tautological upstream assertions become source-derived goldens tagged `unverified-1.99`.
2. **Parser categories** in every parser module (`AGENTS.md`): happy path; every `Error` variant with its structured fields; `Display`
   with numeric context; determinism; both sides of every cap; `u32::MAX` overflow inputs; adversarial inputs per safety guard.
3. **Round trips:** `render(parse(b)) == b` proptests for the config CST; write → read for every writer that exists (raP v4, PBO
   stored and compressed); an opt-in corpus report (`PLOTROOM_CORPUS_DIR`) printing only hashes and counts.
4. **Fuzzing:** cargo-fuzz targets mirroring CWR's 16 libFuzzer harnesses for the formats that exist, clean in the nightly run for the
   period set in the M0 exit report.
5. **Map goldens:** `DrawList` snapshots per map layer on a synthetic island; WARP and lavapipe golden images; frame times on the SP-03
   stress fixture re-recorded with real code.
6. **Catalog and mods:** MAT2 (`addOnsAuto[]` parity on fixtures; opt-in corpus with the doc 42 case-study floor), MAT3 (stub owner),
   MAT4 (card determinism and bases), MAT5 (infantry role rules against the opt-in corpus; vehicle roles stay "unvalidated"), MAT11
   (provenance levels on hostile fixtures), MAT16 (fingerprint cache); ported `test_mod_collection` (doc 27 phase M1).
7. **Install discovery** tests on synthetic Steam, GOG, CE, 1.99 and demo trees.
8. **`plotroom check`** golden output per profile on synthetic missions.
9. **Manual verification note:** three real missions (one on demo data if SP-06 supports it) opened and compared side by side with the
   original editor; screenshots stay local.

**Parallel lanes.** A (L0–L2, read lens); B (renderer, map, fonts, shell); C (installs, VFS, catalog); D (the Python suites in
`tools/local-qual` stay the evaluation tool until M6); F (DG005 live; the next data pass adds the `exe_199_string` column to
`docs/research/data/cwa199-observed-commands.csv`, I35-90).

**Integration items.** I35-90 (evidence tiers), I34-27 (lock family, path resolver, drift report), I34-05-06 (fallback fonts), I34-02
(`NOTICE` and headers), I35-LINT (rc58, rc66, rc67 read-only).

## M2 Classic editor (0.2–0.3)

**Goal.** Faithful editing: the original modes F1–F6, dialogs, keys and semantics (doc 09 M1–M13; docs 03, 05), with the modern safety
nets the community asks for most (doc 09 S1, S2, S4, S5, S7, S8, S11, S12): undo with visible history, a non-modal problems panel,
live engine-limit checks, integrated field checking, an outliner, autosave and backups, lossless save and PBO export.

**Scope.**

- **Kernel and commands:** `plotroom-doc` (guarded store, ops with inverses, undo groups and history, provenance, merge), writes in
  `plotroom-mission` (typed lens, writer profiles `Legacy196Text` and `RemasteredText`, "Normalize as engine" as an explicit command),
  `plotroom-sidecar` (`.plotroom/`, identity records, re-match after an external save), `plotroom-commands` (registry, admission,
  `resolve_targets`, schema generation), `plotroom-view` (selection, dialog sessions, the headless map interaction state machine),
  `plotroom-session` (`Session::step`, typestate `CoreBuilder`, `UserIntent` minting).
- **Script and briefing checks:** `plotroom-briefing` (CST of the engine's HTML subset), `plotroom-script` (lexer, SQS line model, SQF
  AST, `check_field` with engine-parity verdicts), `plotroom-script-catalog` (generated per-profile overload tables with availability,
  evidence tiers, registration gate and risk tags; `xtask catalog` with a drift check), `plotroom-teller` (field-checks adapter only).
- **Validation:** engine-structural and limit rules, the complexity meter (doc 34 ed14; rc67), per-profile results, quick fixes as one
  group, acknowledgements with fingerprints, a basic readiness model.
- **Persistence:** `plotroom-io` writes (atomic save with `.bak`, external-change check, crash op journal in app data, autosave and
  rotating backups); `plotroom-export` (PBO building; `a-b_X_Name.Island` folder naming with the `briefingName` lint, rc55).
- **UI:** classic dialogs for units, groups, waypoints (Cycle, attach to static objects), triggers, markers, effects and Intel;
  Easy/Advanced (default Advanced) with the original labels and plain-language relabels beside them (D029); the inspector (read/write),
  outliner, problems, history (filterable by origin and document); the command palette over the registry (commands only; locators grow
  in M4); semantic action ids and the "Classic" keymap profile (doc 34 le06); the split between user preferences and project settings
  (le16); accessibility nodes for classic controls (D016 item 6).
- **Sidecar-only objects** and levers from doc 34 row 04: Intel `resistanceWest`/`resistanceEast` and weather and date fields as typed
  levers, the voice-language sibling-file rule, zones, phases, named routes and the id map (I34-04).

**Out of scope.** Preview; modules, rules and campaigns; any AI.

**Crates.** Land: `plotroom-sidecar`, `plotroom-commands`, `plotroom-view`, `plotroom-session`, `plotroom-briefing`, `plotroom-script`,
`plotroom-script-catalog`, `plotroom-teller`, `plotroom-export`, `plotroom-ui-classic`; dev-only `plotroom-script-oracle`. Grow:
`plotroom-doc`, `plotroom-mission`, `plotroom-project`, `plotroom-validate`, `plotroom-io`, `plotroom-rsc`, `plotroom-ui`.

**Depends on.** M1; SP-04 and SP-05 go; SP-10's benchmark (and the document-thread fallback if it failed).

**Spikes and probes first.** SP-08's 1.99 exporter question (does the 1.99 exporter skip dot-directories?) before the `.plotroom/`
spelling is frozen (architecture README §8 item 1; doc 45 OQ1).

**Gates.** DG011 (admission wrapper) and DG017 (sidecar and journal records) decided; the architecture README §8 candidates on sidecar
spelling and export (1), `Origin` types (2), 128-bit ids (3), live groups (4), lowering failure classes (5), provenance granularity (9)
and two journals (10) filed and decided. DG018 (third-party port records) before the TrenchBroom-derived command tests land.

**Exit evidence.**

1. **Kernel invariants** checked after every `EditorHarness` step (id map complete and one-to-one; no dangling sync; `ItemN`
   contiguous; incremental lens equals re-derived lens; no open group at rest).
2. **Properties:** random op sequences → undo all → byte-identical CST and sidecar; redo all → pre-undo state; applied diff equals
   planned diff.
3. **"One action is one undo step"**: `drag_waypoint_is_one_undo_step`, `dialog_ok_is_one_undo_step`,
   `paste_group_with_waypoints_is_one_undo_step`, `fix_all_is_one_undo_step`, `migration_is_one_undo_step`.
4. **Command-processor event-log tests** (commit, rollback, nested, scopes, modification, collation), red first, with DG018 records.
5. **Dirty state and identity** tests from testing-strategy §6, including delete-then-undo of a unit with a synced trigger mid-group,
   and a simulated engine re-save re-matching ids.
6. **Lossless save:** an unchanged mission saves byte-identical; **PAT1** (protected values such as `minute=7`, `year=1991`,
   `resistanceWest=0.37`, `skill=0.05` survive an unrelated edit and every dialog open/close); one test per writer rule.
7. **Ported rows:** editor-core (6), editor-ui (12), mission-model (8; 4 probe rows wait for M3), script-lang (20; 3 probe rows wait).
8. **Parity scripts:** `egui_kittest` scripts for doc 09 M1–M13 (F1–F6 modes, double-click place and edit, Delete versus Shift+Del,
   100 m auto-join, marker hit-testing outside marker mode, keypad and wheel zoom, clipboard keys including paste-absolute); the per-OS
   shortcut-clash test; syncing a changed value into every control type emits zero commands.
9. **Performance** against ui-shell §11's targets (commit plus publish < 2 ms at 5,000 entities; overlay draw list < 4 ms at 1080p),
   with measured numbers in the exit report.
10. **Crash recovery:** a killed session recovers from the crash op journal; the journal reader survives a torn tail.
11. **Export:** PBO export read back by `plotroom-pbo`; folder-naming lint fixtures.
12. **Manual notes:** AccessKit listing of classic dialog controls on Windows; dialogs compared side by side with the original.

**Parallel lanes.** A (kernel, commands, sidecar, session, save); B (classic dialogs, panels, keymaps, accessibility); C (the harness
spike prep for M3: SP-07's link questions on a real install); D (idle for product code; may pre-build `plotroom-testkit`'s faux-model
state machine); E (relabel text per D029; Standing Orders entry format); F (DG017, DG018, architecture §8 candidates).

**Integration items.** I34-04, I34-05-06 (action ids, keymaps, preference split), I34-21 (per-origin undo lanes as filtered history
views), I35-LINT (structural and limit rows).

## M3 Preview beta (0.5)

**Goal.** One-click Preview in the user's real game from unsaved edits, with honest results, and an export that proves its
dependencies. This is the **first public release**, subject to the release gates below: the faithful editor plus Preview is already the
product the community asked for (doc 09 M8; D018).

**Scope.**

- **`plotroom-preview`:** pure staging (`stage(snapshot, spec) → StagePlan`, unsaved edits included, staged to app temp, never the
  working folder); the closed `LaunchSpec` builder; the supervisor (`kill_on_drop`, Windows Job Object, jsonl log streaming); the
  capability probe on a user action, cached by executable path, size and time; run records; the probe runner.
- **Launch modes** (game-integration §6): strict Preview P1 (`--test-mission … --harness 0 --log-format jsonl`, `--mod` from the mod
  set, `--private` on every launch once SP-07 shows no side effects; I42-08, MAT12); Validate (`--check`); Preview from camera;
  Intro/Outro through the intro fallback; clean-room and vanilla variants; export-and-open for every profile and as the only path for
  `Cwa199`.
- **`plotroom-gamelink` (Preview P2 live link):** typed loopback client with allowlisted verbs only (stop, teleport to cursor,
  screenshot into the stage folder, read-only queries, time and weather tweaks labelled "not saved"); a console that accepts only
  user-typed text after Teller's check. The console stays **strict** while DG001 is open: any script error ends the session.
- **Results:** the Preview log panel with jump-to-element; run records with assisted flags (doc 34 le19); the post-Preview debrief card
  (le12); the standalone outcome display (ed07); a stored `PreviewBattleReport` (cw22) for later balance calibration; trace mode for
  triggers and waypoints with a fire log on the map (`EmitMode::PreviewTrace`; export stays trace-free).
- **Safety:** the Preview gate (doc 24 §5.2) and risk badges for downloaded missions; the dialog states that Preview runs the mission
  with the user's full rights.
- **Export and dependencies:** the dependency engine and write rule (engine set ∪ extended set ∪ user pins by default, with an
  engine-parity-only mode: owner, OWQ-18 (a)), lints D1–D8, the requirement manifest keyed by mod id and the "Requires" badge (doc
  27 phase M2; doc 42 §2.8); export scans (no trace tokens, no agent leftovers, debug leftovers rc68, the D9 redistribution guard); `.plotroomignore` and a
  file-list preview; a first completeness gate (blocking findings; Path Explorer coverage joins in M5).
- **Mod sets:** requirement kinds (mo08), the handoff bundle (mo15), server mod lists (mo19, mo20) (I34-27); lint D11 for a mod that
  redirects the master server.
- **Release packaging** per OS, the About box and disclaimer per D002 and DG002's placement rule (decided, OWQ-07; `AGENTS.md`
  "Naming and Trademarks"): "Plotroom" alone in the window title, installer name and file name; the descriptor with the disclaimer on
  the splash and About box (architecture ui-shell §12).

**Out of scope.** Tolerant Preview and a non-aborting console (Preview P3, waits for ER-001/ER-002; roadmap §8.3); MP Preview (v1.3);
any agent access to Preview (Wilco has no eval tool; architecture README §7 row 18).

**Crates.** Land: `plotroom-preview`, `plotroom-gamelink`. Grow: `plotroom-export` (scans, manifests), `plotroom-catalog` (dependency
engine, D-lints), `plotroom-validate` (readiness: Preview pre-flight mirroring `IsConsistent`), `plotroom-io`, `plotroom-ui`.

**Depends on.** M2; SP-06 and SP-07 answered; the harness link questions of SP-07 checked on Remastered and CE.

**Spikes and probes first.** SP-07 (flags on shipping builds, positional launch, `--private` side effects, the harness link); the
Remastered/CE probe suite infrastructure (probe = generated synthetic mission with a declared outcome; negative probes; strict mode)
built on the probe runner; SP-08's manual 1.99 runs for any P0 1.99 question not already answered before M2 (the exporter question
must be answered before M2 freezes the `.plotroom/` spelling; spikes-and-probes §4.2).

**Gates.** OWQ-18 is answered (a), so the write rule ships as above. **Public release** (each decided by the owner on 2026-09-27; the
actions remain): OWQ-07 (placement decided; clearance search recorded in doc 02 and the repository renamed), OWQ-10 (a) (the Bohemia
letter answered, or a documented decision to proceed), OWQ-09 (a) (private reports sent; no new public detail before acknowledgement),
OWQ-05 (a) (the DCO check live) before outside contributions are accepted. DG001 stays open and only limits the console.

**Exit evidence.**

1. **Staging goldens:** `StagePlan` golden folders for missions, Intro, Outro-Win and Outro-Lose via the intro fallback, and Preview
   from camera; staging never touches history or dirty state (test).
2. **Launch and supervision:** `LaunchSpec` argument tests per executable flavour; a fake game binary (exit codes, jsonl output, a hang
   followed by a kill); exit-code mapping that reads the ending from log markers, never from the exit code (doc 20 TL;DR; ER-006).
3. **Live link:** a fake loopback harness server (verb allowlist, malformed lines, oversize replies); every reply parsed as untrusted.
4. **MAT12:** a synthetic mod with `bin\remaster.cpp` redirecting the master server fires D11, and every Preview launch line contains
   `--private`.
5. **Ported rows:** preview-harness (8) and its 2 probe rows run on Remastered; the platform-paths probe row; the mission-model and
   script-lang probe rows from M2 run through the probe runner, results recorded per profile.
6. **Probe results** on Remastered and CE for SP-07's questions and doc 27 phase M3's mod probes, recorded as evidence tiers in the
   catalog and as dated notes; `ER-###` rows updated where a probe changes the evidence.
7. **Export:** export-scan goldens (no trace tokens, no agent leftovers, D9 on a copied stock file); requirement-manifest goldens;
   parity tests against the engine's `ScanRequiredAddons` rules (doc 27 phase M2); round-trip byte tests of re-saved `addOns[]`.
8. **Security:** the Preview gate blocks a `deny` fixture; the override is stored in project metadata, not in the mission.
9. **Manual verification notes:** Preview from unsaved edits, Validate, from camera and Intro/Outro on a real Remastered install on
   each supported OS; export-and-open on 1.99; a Preview on CE.
10. **Release checklist:** disclaimer and descriptor per DG002; `NOTICE`; licence files; the OWQ actions above done and dated.

**Parallel lanes.** C (all of Preview, probes, export); A (export scans, readiness); B (Preview log, debrief card, run report); D
(may start `plotroom-workflow` and the runtime on synthetic fixtures once DG007 is decided, since M4 needs it); E (Standing Orders seed
entries in draft; Drill lesson scripts in draft); F (release gates; outreach letters prepared for the owner).

**Integration items.** I42-08 (`--private` everywhere), I34-08 (run records, battle report, debrief card, outcome display), I34-27
(requirement kinds, handoff, server lists, D9), I34-02 (D9 guard), I35-LINT (rc68, rc70 first part).

## Verification notes

### Roadmap baseline (2026-09-27)

- Built from architecture README §6 and §7, crate-map §3–§11 ("Lands" column), game-integration §2–§12, testing-strategy §2–§14, doc 06
  §7, doc 08 §6, doc 09 §8, doc 20 §3, doc 27 §4.12 and doc 42 §8. Upstream row counts are the `todo` counts of crate-map §13.
- Where this file moves an item relative to the architecture's §6 table (trace mode for triggers in M3; dependency engine and D-lints
  in M3), the architecture left the milestone open; no conflict is intended.

### Owner answers folded (2026-09-27)

- M0's owner-question bullet, M3's dependency write rule, release packaging and gates now state the owner's answers of 2026-09-27
  (OWQ-02, OWQ-05, OWQ-07, OWQ-09, OWQ-10, OWQ-18). The release gates stay: the answers decide what each gate is, not that it is done.
