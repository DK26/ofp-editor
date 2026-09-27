# Game integration: installs, mods, catalogs, Preview, probes and export

> **Status:** proposal (architecture baseline 2026-09-27). Nothing here is decided unless it restates `AGENTS.md`, a decision
> record (`Dnnn`), a decided DG or an owner answer (`OWQ-nn`, all answered 2026-09-27). Type sketches are not compiled and names are
> not final.
> **Part of:** [architecture overview](README.md). **Main sources:** doc 04 §9; doc 05 §7; doc 08; doc 20 §4; doc 23 §14; doc 24 §4–§6;
> doc 27 §2, §4; doc 32 §4; doc 34 (row 08, row 27); doc 42 §2, §6; D003, D012, D018, D030; DG001, DG034; `docs/upstream/`.

Preview is a client of the core: **staging is a pure function of a snapshot; only launching is an effect** (doc 08 §6). The same
holds for export. Game data is read from the user's install at runtime and never bundled (doc 05; D016 item 3). Every engine
limitation found here is recorded in the engine-requests register and never becomes a silent requirement (D012).

## 1. Crates

| Crate | Layer | Pure? | Owns |
| --- | --- | --- | --- |
| `plotroom-install` | L2 | Yes, over an injected read-only source | Install discovery (pure VDF/ACF parsers), profile folders, executable per target profile (doc 08 §5) |
| `plotroom-vfs` | L2 | Yes | Mount order, PBO-stem prefixes, case-insensitive lookup, `..` collapse, `#include` confinement, "who serves this file" (doc 27 §2.1, §4.3) |
| `plotroom-catalog` | L2 | Yes | Engine-parity config merge, class provenance, unit cards, facets, mod sets and their lock, drift reports, `addOns` derivation (doc 27 §4; doc 42 §2) |
| `plotroom-terrain` | L2 | Yes | WRP and P3D map info → heights, roads, objects, places with fallback clusters, candidate sites (doc 25 §6.1) |
| `plotroom-export` | L5 | Yes | Export plans, PBO building, export scans, requirement manifests |
| `plotroom-preview` | L7 | Staging pure; launch an effect | `StagePlan`, `LaunchSpec`, supervisor, run records, capability probe, probe runner (doc 08 §6) |
| `plotroom-gamelink` | L7 | No (loopback socket) | Typed JSON-lines client for the game's `--harness` link, restricted to an allowlisted verb set (doc 08 §2.5, §4.4) |

Reading game files goes through a `ReadOnlySource` trait implemented in `plotroom-io`; the L2 crates never touch `std::fs` directly,
so tests use in-memory trees and synthetic builders.

## 2. Installs and executables

- **Discovery** (doc 08 §5.2): user-configured installs first, then Steam (Remastered, app 65790; libraryfolders and appmanifest
  parsed purely), GOG, CE builds (chosen by the user), legacy 1.99, and the free Steam demo (data only; its executable has no editor
  module, doc 05). Discovery reads files; it **spawns nothing**.
- **Executable per target profile** (D003): `Cwr` and `Ce` use a Remastered or CE `PoseidonGame`; `Cwa199` uses the legacy
  executable through export-and-open only (it has no test harness, doc 08 §2.1; doc 20 §4.4).
- **Capability probe (resolution).** Whether a build honours `--test-mission`, `--harness`, `--check` and later CE flags is probed by
  running it (`--version`, a synthetic `--check --test-mission` expecting success; doc 08 §6). Because that spawns the game, the probe
  lives in `plotroom-preview`, runs only on a user action ("Check this install", or the first Preview), and is cached by executable
  path, size and modification time. An unknown build counts as lacking every optional capability.

## 3. VFS and mod sets (D030)

- **Mount order** mirrors the engine: base game, then `res`, then mods (last-listed first), with PBO-stem prefixes and
  case-insensitive lookup; `#include` is confined to the mounted set (doc 27 §2.1).
- **Mod sets are first-class, fingerprinted objects** with a `*.modset.toml` lock; a mission's lock sits in its sidecar
  ([core-document-model.md §10](core-document-model.md)); presets are shareable (doc 42 §7.4).
- Folded from doc 34 row 27 (I34-27): the lock family (mo01), the path resolver that answers "who serves this file" (mo02), the drift
  report between a lock and the installed set (mo03), requirement kinds (mo08), the handoff bundle (mo15), server mod lists (mo19,
  mo20), and the D9 redistribution guard for user-supplied files ([validation-and-lints.md §10](validation-and-lints.md)).
- **Integrate, never host** (doc 42; D030): Plotroom never downloads, installs, re-hosts or runs mods, mod launchers or install scripts.
  "Use mod X" when X is missing produces a code-computed card with three routes: get it (link and instructions), build now with
  vanilla stand-ins marked for remap, or record X as a declared requirement (doc 42 §2.7). **Install hand-off (owner, OWQ-17 item 1 =
  DG030 item 1):** on `Cwr` and `Ce` targets the "get it" route offers a user-clicked **"Launch the game to install mods"** that starts
  the game vanilla, without `--private`, without a mission and without a mod set, so the user installs through the game's own MODS
  screen; Plotroom rescans on focus (doc 42 §3.3). It is never automatic and never a Preview (§12).
- **Remap to an installed set** (renamed from doc 35 rc84's "Retarget…", because "Retarget" is reserved for changing the target
  profile; I35-84) is one typed, AI-off workflow built on doc 27 §4.8's vanilla-safe swap and doc 37 §5's class remap, with doc 42
  §2.9's tiers: (1) side + kind + role, (2) kind + role on any side, (3) side + kind; up to three candidates each with tier and
  confidence; a model may only rank; the user confirms; vehicle remaps are gated on the vehicle-role evaluation (I42-37). Content is
  identified by per-file fingerprint (doc 27 §4.7).

## 4. Catalogs and terrain

- **Engine-parity config merge** in `requiredAddons` topological order, with the owner of every class recorded; unit cards carry a
  `basis` for each derived field (doc 42 §2.2); facet menus side → kind → role group → role keep weak-model menus within the cap
  (doc 42 §2.4).
- **Dependencies:** `addOns[]` is written from the engine set plus the extended set (script literals, `description.ext` weapons,
  markers, effects) plus user pins by default, with an engine-parity-only mode (owner, OWQ-18 (a); doc 27 TL;DR).
- The catalog, island places and per-profile script catalog are cached locally per fingerprint and never committed (doc 42 §2.10;
  doc 21 §10).
- Terrain: exact surface height and sight helpers grow with the cutscene director and atmosphere work in v1.x (doc 39; doc 41);
  `island.places` falls back to clusters when an island has few named places (I35-GEN rc57).

## 5. Preview staging

```rust
// plotroom-preview::stage (pure). Proposal-only.
pub fn stage(snap: &Snapshot, spec: &StageSpec) -> Result<StagePlan, Vec<Diagnostic>>;
pub enum StageSpec { Mission { section: SectionSel, from_camera: Option<CameraPose>, emit: EmitMode },
                     CampaignNode { node: ElementId, state: StateSource } }
pub enum StateSource { DesignerDefaults, PathExplorerScenario(ScenarioId), Explicit(StateBundle) }
pub enum StageTransform { StartAtCamera(CameraPose), Section(SectionKind /* Intro | OutroWin | OutroLoose */), Emit(EmitMode),
                          IntelOverride(IntelPatch), CampaignPrologue(StateSource), ProbeWrap(ProbeId) }
```

- **Pre-flight** is the readiness model's Preview view, mirroring the engine's `IsConsistent` (doc 08 §6 P1): a player exists, the
  island is installed, the Intro and Outro sections are written, `addOns[]` is complete; plus the doc 24 §5.2 Preview gate
  ([validation-and-lints.md §11](validation-and-lints.md)).
- The plan is computed from an `Arc<Snapshot>`, **unsaved edits included**, and written by the I/O service to
  `<app temp>/preview/<session>/<name>.<World>/`. **The user's working folder is never launched.**
- **Intro and Outro previews** stage the section as the Intro of a group-less mission (the engine's intro fallback; doc 08 §4.2;
  doc 32 §4.3). Preview-from-camera moves the player unit in the staged copy.
- **Campaign-node Preview** ("start at node with state S", doc 19 §6.4): a Preview-only prologue sets undefined campaign variables to
  designer test values or a named Path Explorer scenario and shows each assumption as a chip. Because StartAutoTest clears campaign
  variables, the prologue sets them in the staged init (I35-PREV; doc 32 §4.3). Engine support for a campaign test launch at a chosen
  row is ER-007.
- Preview never touches history or dirty state (doc 09 S1).

## 6. Launch modes and phases

| Phase | Launch | Profiles | Notes |
| --- | --- | --- | --- |
| P0 (spike, on real installs) | A throwaway script the owner runs | Cwr, Ce, Cwa199 | Do shipping builds honour `--test-mission`, `--harness 0`, `--check`, `--render dummy`? What does a positional `mission.sqm` do (DG001 option B)? Does `--private` have side effects in single-player Preview (I42-08; doc 42 OQ10)? Does the 1.99 exporter skip dot-directories (doc 45 OQ1)? Can a whole campaign start at a chosen row, and does `--test-mission` read a campaign `description.ext` (I29-08; ER-007)? |
| P1 strict Preview | `--test-mission <stage folder, no trailing separator> --window --no-splash --no-strict --harness 0 --log-format jsonl`, plus `--mod` with the resolved mod set and, after the P0 probe, `--private` on **every** launch (I42-08) | Cwr, Ce | Labelled **strict**: a script error ends the run and shows where (doc 08 §4.4). A Validate button runs `--check` |
| Export and open | Export, then open the game (Option 1) | All; the only path for Cwa199 | Always available as the fallback |
| P2 live link | `plotroom-gamelink` over the loopback harness | Cwr, Ce | §8 |
| P3 tolerant Preview | CE `--preview-mission`, `--preview-briefing`, `--preview-on-end`, `--edit-mission` once shipped and probed (ER-001, ER-002; CE #35) | Ce (opt-in capability) | Also the fix for the debug-console abort (DG001) |
| P4 MP Preview (v1.x) | A local `PoseidonServer --private` with a sandboxed user directory, plus N clients | Cwr, Ce | doc 08 §4.5 |

- `LaunchSpec` is built by a closed builder from typed parts (executable, mission folder, mod list, flags); it is never assembled from
  free text, and the working directory and environment are fixed by the builder, not by callers.
- **Clean-room** (only the required mods) and **vanilla** (no mods) Preview variants prove a mission's dependency list (doc 27 §4.6).
- The local model is unloaded, or the managed server paused, before the game launches (doc 13; doc 44 §5.3).

## 7. Supervision, outcomes and run records

- The supervisor runs on the async runtime with `kill_on_drop` and a Windows Job Object; it streams jsonl logs into the Preview log
  panel.
- **Exit codes map to a typed outcome**, but in mission-directory mode every mission end exits 0, so **which ending fired is read from
  log markers or trace tokens, never from the exit code** (doc 20 TL;DR). Exit code 2 is overloaded (ER-006) and is disambiguated by
  the log.
- **Run records** (I34-08; doc 34 row 08) keep the launch spec, profile, mod set, staged-content hash, assisted flags (teleports,
  console use; le19), exit and ending, fire log and screenshots in app data, with a summary line in the sidecar project log. v1 adds
  the post-Preview debrief card that links findings back to elements (le12), the standalone outcome display (ed07) and a
  `PreviewBattleReport` that later calibrates the balance lab (cw22). Postcards (le13), test range and speed control (ed17), director,
  capture-back and route recording (ed18), and tour completion events (le05) follow in v1.x with cinematics and Drill tours.
- Camera capture for cinematics tails the game's clipboard output (doc 32 §4.4), v1.x.

## 8. Live link (`plotroom-gamelink`)

- A clean-room typed client for the harness protocol over loopback, connecting at once (the listen backlog is small), tested against a
  fake TCP server (doc 08 §6 P2).
- **Allowlisted verbs only:** stop, teleport to cursor, screenshot written only into the stage folder, safe read-only queries, time
  and weather tweaks labelled "not saved" from typed templates. The SQF console accepts only text the user typed, after Teller lint.
- Every reply is untrusted data (doc 24 §5.4). Under the P1 launch, any script error, including console text, ends the session; the
  tolerant console waits for a non-aborting launch (DG001; ER-001).
- **Wilco has no eval tool here** and never launches the game ([agent-runtime.md §2](agent-runtime.md)).
- The harness is "local code execution for whoever reaches the port": it is opened on an ephemeral port only while a Preview runs and
  closed on exit (doc 24 §4). Authentication and framing are ER-010 (private report first: OWQ-09 (a), the owner reports; not yet
  sent).

## 9. Trace mode and the fire log

- `EmitMode::PreviewTrace` injects trace lines keyed by `ElementId` (`logInfo` on `Cwr`/`Ce`; `hint` in the `Debug199` variant) and loop
  watchdogs; the parser turns them into a fire log drawn on rule cards and as a glow on the map; transcript lines carry their `LineId`
  (doc 45 §4.7; Blockly's per-block trace ids).
- `Export` output contains no trace tokens, proven by a golden test ([testing-strategy.md §7](testing-strategy.md)).

## 10. Probe suites

`AGENTS.md` turns upstream tests that are only observable in the running game into in-game probes; doc 20 §4 and the research docs
add probe lists of their own.

- **A probe is a generated synthetic mission with a declared expected outcome:** END1–6, LOSE, a script-asserted pass or fail, or
  timeout. Suites include **negative probes** that must fail, and a strict mode that fails on a new engine log warning (doc 45 §2.10;
  Wesnoth's schedule).
- **Remastered and CE** run probes through `--test-mission --check` plus the harness (`plotroom-preview::probe`).
- **1.99** has no harness and no test verbs: its backend is manual. Plotroom exports the probe, the user plays it, and the result is
  recorded with the probe's source and hash (doc 20 §4.4).
- Priority sets: doc 19 OQ1 (the lowering whitelist, which gates freezing the `Cwa199` lowering), doc 29 §9, doc 37 PP1–PP12, doc 43
  P-R1 and later rows, doc 34 OQ1, the P0 questions above, and I34-18's open question whether one campaign can read another campaign's
  save (doc 34 cw28).
- Probe results promote catalog entries between evidence tiers (doc 35 §8.3) and clear "unverified on …" badges; they become
  `probe` rows in `docs/porting/upstream-test-map.csv` where they replace an upstream test.

## 11. Export

- **Mission folders** named `a-b_X_Name.Island` with the `briefingName` lint (doc 35 rc55); mission PBOs through `plotroom-pbo`;
  campaign folders with campaign-level `CfgIdentities` and per-mission `CfgSounds`/`CfgRadio` (I35-GEN rc56).
- **The sidecar is always excluded**; a file-list preview and a `.plotroomignore` file let the user see and trim what ships (doc 45 §5).
- **Export scans:** no agent leftovers, no trace tokens, debug leftovers flagged (rc68), the D9 redistribution guard, no Bohemia or
  third-party parent content in shared extension overlays (OWQ-06: extension-only for Bohemia's campaigns; third-party parents only
  with a licence that allows derivatives or recorded permission).
- **Requirement manifest** keyed by the engine's mod id and the computed "Requires" badge (doc 42 §2.8;
  [validation-and-lints.md §8](validation-and-lints.md)).
- **Completeness gate:** blocking findings, `Todo` elements, Path Explorer coverage for campaigns and an optional smoke run (rc70).
- **Campaign compile** (sockets, routers, finisher, `saveVar` layout, campaign `description.ext`) runs here and at Preview, not on
  every commit ([commands-undo-history.md §5](commands-undo-history.md)).
- Install and regenerate never overwrite a version-controlled or author folder (doc 45 §5).

## 12. Security

- Only `plotroom-preview` (the game executables of a discovered install) and `plotroom-model-manager` (the managed inference server)
  may spawn processes; neither is ever started by the agent; every Preview launch and capability probe is a user action
  ([crate-map.md §2.3](crate-map.md)).
- `--private` on every launch after its probe, because a mod's `bin\remaster.cpp` can redirect the master server (doc 42 §6.3;
  ER-022; lint D11). The one exception is the mod-install hand-off the owner adopted (OWQ-17 item 1; §3): "Launch the game to install
  mods", vanilla, no mission, without `--private`, on `Cwr` and `Ce` targets; it is a separate, labelled user action, never a Preview.
- Downloaded missions get risk badges (doc 24 §5.2); the Preview gate blocks one-click Preview of `deny` findings; the dialog says
  plainly that Preview runs the mission with the user's full rights (doc 24 F1–F2).
- Hostile or huge mod content: parse caps and streaming readers (large PBOs are streamed through `Read + Seek`, never memory-mapped;
  D017), per-addon failure isolation, `#include` confinement, never executing mod code (doc 27 §4.10; doc 42 §6.1–§6.2).
- **Engine security findings stay private.** Hardening entries (ER-010, ER-014 to ER-018, ER-021 and others marked "private report
  first") enter any public discussion only after the owner's private reports are acknowledged (OWQ-09 (a); `docs/upstream/README.md`).

## 13. Engine requests

Every limitation met in this area already has, or gets, a row in `docs/upstream/engine-requests.csv`: the non-aborting Preview launch
(ER-001), editor-launch flags (ER-002; CE #35), in-process restart (ER-003), test-launch path handling and exit codes (ER-004 to
ER-006), a campaign test launch at a chosen row (ER-007), documented tooling flags and saves inside Preview (ER-008, ER-009), the
harness and test-verb entries (ER-010 to ER-013), the camera and effects defects routed by DG034, and the mod entries (ER-103 to
ER-108). When the community engine ships one, it becomes an **opt-in capability** of the `Ce` profile (and of `Cwr` if an official
release ports it), detected by the capability probe, with the `Cwa199` and `Cwr` fallbacks kept (`docs/upstream/README.md`).

## 14. Open questions

1. The P0 answers: flag support on shipping builds, positional launch behaviour, `--private` side effects, 1.99 dot-directory export,
   campaign test launch (I29-08).
2. Whether the free demo's data is enough to render classic dialogs faithfully when no full install exists (doc 05).
3. *Decided 2026-09-27:* the mod install hand-off route and directory freshness (OWQ-17 items 1–2; DG030; §3, §12).
4. Whether reading another campaign's save is possible or wanted (I34-18; doc 34 OQ3; a probe first).
5. Whether automatic capability probes at start-up would be acceptable if a user opts in.
6. The MP Preview slot presets and sandboxing details (doc 08 §4.5), v1.x.

## Verification notes

### Owner answers folded (2026-09-27)

- Folded from `OWNER-QUESTIONS.md` (answers of 2026-09-27) and DG030's proposals: §3 (OWQ-17 item 1, the install hand-off), §4
  (OWQ-18 (a)), §8 and §12 (OWQ-09 (a); reports not yet sent), §11 (OWQ-06), §12 (the hand-off as the one launch without
  `--private`), §14. The rescan on focus is doc 42 §3.3's design, unchanged.
