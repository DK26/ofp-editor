# CODE-INDEX

Source navigation index for **Plotroom — Mission & Campaign Editor for Arma: Cold War Assault / Operation Flashpoint**, required by
`AGENTS.md` ("Source Code Navigation Index"). It tells a human or an LLM agent where things are, and where they will be.

> **Status (2026-09-27): there is no Rust code yet.** The repository holds design documents, two skills, a prompt pack and two Python
> research tools. Every crate, module and newtype below is **planned**: it comes from the proposal in
> [`docs/architecture/crate-map.md`](docs/architecture/crate-map.md) and is not decided. Crate names become final only when the change
> set that creates the crate records it here (D002 item 4). That change set also fills the row's path and flips its status to
> **landed**.

## 1. Start here

| If you need to… | Go to |
| --- | --- |
| Know the rules for code, tests, docs and the product | [`AGENTS.md`](AGENTS.md) (read it first, always) |
| Find the design for a topic | [`docs/README.md`](docs/README.md) §4 (topic → canonical files) |
| Know which crate owns something, or may depend on what | §4 below, then [`crate-map.md`](docs/architecture/crate-map.md) |
| Know what the current milestone requires | [`docs/roadmap.md`](docs/roadmap.md) §4 and its milestone file |
| Check whether something is decided | [`docs/decisions/README.md`](docs/decisions/README.md) and the [DG index](docs/design-gap-requests/README.md) |
| Port upstream code or tests | [doc 20](docs/research/20-upstream-test-inventory.md), [`upstream-test-map.csv`](docs/porting/upstream-test-map.csv), [testing-strategy §4](docs/architecture/testing-strategy.md) |
| Record a gap in our own design | [`docs/design-gap-requests/README.md`](docs/design-gap-requests/README.md) (lifecycle and template) |
| Record a limitation of the game engine | [`docs/upstream/README.md`](docs/upstream/README.md) (engine-requests register) |
| Look up editor concepts and engine facts | [`skills/standing-orders/`](skills/standing-orders/SKILL.md), [`skills/mission-primer/`](skills/mission-primer/SKILL.md), docs 03, 04 and 18 |
| Measure a local or cloud model (free OpenRouter models included), the harness's uplift, reasoning scaffolds, a small-to-large cascade, or model cost | [`tools/local-qual/`](tools/local-qual/README.md), [`tools/cost-model/`](tools/cost-model/cost_model.py) |
| Simulate free-tier rate limits and upstream 429s over a user day | [`tools/quota-sim/`](tools/quota-sim/README.md) |

## 2. Repository layout (current)

```text
.
├── AGENTS.md              rules for contributors and coding agents; product invariants (read first)
├── CLAUDE.md              one-line include of AGENTS.md for an agent tool
├── CODE-INDEX.md          this file
├── README.md              what Plotroom is, what you need, licence, disclaimer
├── LICENSE                GPL-3.0-or-later
├── .gitignore             /private/, /target/, tool outputs, Python caches
├── docs/
│   ├── README.md          entry point: organisation, reading orders, topic index, research index
│   ├── research/          research docs 01–48 (final; designs proposal-only unless adopted); doc 49 in progress
│   │   └── data/          10 CSVs (corpus, catalog sizes, costs, command risk, local qualification, runtime and quant
│   │                      comparison, small-model and cloud candidates)
│   ├── design-gap-requests/  DG001–DG038 and the index README (lifecycle, template)
│   ├── decisions/         D001–D043, OWNER-QUESTIONS.md (OWQ-01–OWQ-23, all answered 2026-09-27), index README
│   ├── architecture/      README (thesis, layers, conflicts, Appendix A) + crate-map, core-document-model,
│   │                      commands-undo-history, validation-and-lints, agent-runtime, ui-shell, game-integration,
│   │                      extensibility, testing-strategy
│   ├── roadmap.md         milestones at a glance, lanes, definition of done, deferrals, risks
│   ├── roadmap/           m0-m3, m4-v1, v1x-and-v2, spikes-and-probes, integration-owners
│   ├── upstream/          engine-requests register: README, engine-requests.md, engine-requests.csv (ER-001–ER-109)
│   └── porting/           upstream-test-map.csv (636 upstream test rows)
├── skills/                product skills in the standard SKILL.md format (D019)
│   ├── mission-primer/    SKILL.md + references/ (idioms, file-skeletons, sources)
│   └── standing-orders/   SKILL.md + references/ (32 concept entries; formerly skills/field-manual/)
├── prompts/
│   └── design-sensibility/  v0.2 taste pack: core.md, lenses/ (8), rubric.md, code-owned-principles.md, EVALUATION.md
├── tools/                 Python research tools, standard library only; not product code
│   ├── local-qual/        README.md (usage, suites, metrics, tests, verification); run.py (runner) with run_cli.py (flags,
│   │                      refusals) and run_records.py; prompts.py; backends.py (Ollama and llama-server clients);
│   │                      cloud_backend.py, cloud_guard.py, cloud_run.py, budget.py (OpenAI-compatible endpoints under a
│   │                      hard budget); free_mode.py, free_key.py, rate_gate.py (--free-only: OpenRouter :free models at
│   │                      zero spend); logprob_pick.py, logprob_dist.py (--pick-mode logprob); scaffolds.py,
│   │                      scaffold_algos.py, scaffold_run.py, scaffold_stats.py, control_suite.py (reasoning scaffolds,
│   │                      doc 59); score.py, score_checks.py, grade_open.py, uplift.py, cascade.py, cascade_numbers.py;
│   │                      cloud/ (owner runbook, Windows DPAPI key scripts); suites/ (pick, pick-hard, fill, explain,
│   │                      text, knowledge .json + the open-arm sidecar); tests/ (unittest suite: mock servers, fixtures,
│   │                      goldens; run python -m unittest discover -s tools/local-qual/tests); results/ is git-ignored
│   ├── cost-model/        cost_model.py (its JSON output is git-ignored; feeds docs/research/data/cost-model.csv)
│   └── quota-sim/         README.md, quota_sim.py (day replay, strategies S0-S6, CLI), quota_pools.py (pools, congestion,
│                          endpoints), quota_report.py (metrics, grid, Markdown), test_quota_sim.py, data/ (workload.json,
│                          limits.json: inputs); results go to a path the caller names
└── private/               git-ignored local notes; never cite, link or copy from it
```

**Verification commands** (`AGENTS.md`, "Local Repo-Specific Rules"), once a Cargo workspace exists:
`cargo test --workspace --locked`, `cargo clippy --workspace --all-targets --locked -- -D warnings`, `cargo fmt --all --check`,
`cargo check`. Agents never run `cargo build` or `cargo run` unless the user asks. There is no `Cargo.toml` yet.

## 3. Planned workspace rules (from the architecture, proposal)

- **Layers L0–L8**, edges pointing downward only; allowed same-layer edges are listed in [crate-map §2.2](docs/architecture/crate-map.md)
  and checked by `xtask layers` against `cargo metadata`.
- **Side effects live at the edge** ([crate-map §2.3](docs/architecture/crate-map.md)): file writes only in `plotroom-io`; child
  processes only in `plotroom-preview` and `plotroom-model-manager`; outbound HTTP only in `plotroom-net`; loopback sockets in
  `plotroom-gamelink`, `plotroom-mcp` and `plotroom-net`; egui only in `plotroom-ui` and `plotroom-app`; wgpu only in `plotroom-gpu`;
  wasmtime and rmcp only in `plotroom-plugin-host` (rmcp also `plotroom-mcp`); environment variables only in the binaries and tests;
  `UserIntent` minted only in `plotroom-session::intent`.
- **Workspace lints** (`AGENTS.md`, enforced mechanically): `unsafe_code = "forbid"`; clippy `indexing_slicing`, `string_slice`,
  `unwrap_used`, `expect_used`, `panic`, `unreachable`, `todo`, `unimplemented` denied; format crates also deny
  `arithmetic_side_effects`. Release profile `lto = true`, `codegen-units = 1`.
- **One `Error` enum per crate** in `src/error.rs`; format crates keep a thin `src/read.rs` over `plotroom-bytes`' cursor.
- **Directory layout** of the workspace (for example whether crates live under `crates/`) is not decided; the M0 change that creates
  the workspace sets it and records it here.

## 4. Crate map (all planned)

"Lands" is the architecture's milestone ([crate-map "Lands"](docs/architecture/crate-map.md)); the
[roadmap](docs/roadmap.md) may refine it. "Blocked on" lists design-gap requests or owner questions the crate's dependent part waits
for. The path column is empty until the crate lands. The owner questions that used to appear in that column were answered on
2026-09-27 and DG014 and DG030 were decided the same day, so those cells now read "—", as in the crate map; the owner's answers
are stated in D031–D043 ([`OWNER-QUESTIONS.md`](docs/decisions/OWNER-QUESTIONS.md) names the record for each).

### 4.1 L0 foundation and L1 formats

| Crate | Layer | Owns | Lands | Blocked on | Path |
| --- | --- | --- | --- | --- | --- |
| `plotroom-bytes` | L0 | Safe-read cursor (`read_u8`, `read_u16_le`, `read_u32_le` with checked offsets), varint, BI LZSS, caps | M1 | — | — |
| `plotroom-ids` | L0 | The newtype macro; Plotroom ids; `IdSource`, `Clock`, seeds; `Digest`, `Fingerprint`, `NonEmpty`, `BoundedVec` | M1 | doc 45 OQ4 (minting) | — |
| `plotroom-encoding` | L0 | Legacy code pages and UTF-8, `byte_len_in(TargetEncoding)`, hidden-character scan | M1 | — | — |
| `plotroom-profile` | L0 | `TargetProfile` (`Cwa199`, `Cwr`, `Ce`), `ProfileSet`, evidence tiers T1–T4, capability ids `ER-###`, "Requires" types | M1 | — | — |
| `plotroom-diag` | L0 | The generated `DiagCode` enum and code metadata from the code registry | M1 | DG005 | — |
| `plotroom-pbo` | L1 | PBO reader (borrowed entries, streaming) and writer | M1 | — | — |
| `plotroom-preproc` | L1 | Preprocessor directives, `IncludeResolver`, source maps | M1 | — | — |
| `plotroom-config` | L1 | Lossless green-tree CST, resolved view with inheritance, raP read (v2–4) and write (v4), `ConfigOrigin` | M1 (CST spike in M0) | — | — |
| `plotroom-stringtable` | L1 | Stringtable CST, per-language columns, legacy and UTF-8 files | M1 | — | — |
| `plotroom-briefing` | L1 | CST of the engine's briefing HTML subset | M2 | — | — |
| `plotroom-script` | L1 | Lossless lexer, SQS line model, SQF AST, `check_field`, `lint` | M2 | — | — |
| `plotroom-script-catalog` | L1 | Generated per-profile command tables with availability, evidence tiers and risk tags; harness-verb table | M2 | — | — |
| `plotroom-wrp`, `-p3d`, `-paa`, `-fxy` | L1 | Terrain, the map-info subset of models, textures, bitmap fonts | M1 | — | — |
| `plotroom-rsc` | L1 | Dialog and control specs with inheritance; fallback look-alike theme data | M0 spike, M2 | — | — |
| `plotroom-audio` | L1 | WSS, OGG and WAV decoding; the lip-sync generator | v1.x | — | — |

### 4.2 L2 world facts, L3 models, L4 core

| Crate | Layer | Owns | Lands | Blocked on | Path |
| --- | --- | --- | --- | --- | --- |
| `plotroom-vfs` | L2 | Mount order, PBO prefixes, case-insensitive lookup, include confinement, "who serves this file" | M1 | — | — |
| `plotroom-install` | L2 | Install discovery (pure store-manifest parsers), profile folders, executables; spawns nothing | M1 | — | — |
| `plotroom-catalog` | L2 | Engine-parity config merge, class provenance, unit cards, facets, mod sets and locks, drift report, `addOns` derivation | M1 | — | — |
| `plotroom-terrain` | L2 | Heights, roads, objects, places, candidate sites, spatial index | M1 | — | — |
| `plotroom-doc` | L3 | `Guarded<T>`, ops, undo groups, history and lanes, `Origin`, `Provenance`, `merge_regenerated` | M1 types, M2 | DG011 | — |
| `plotroom-mission` | L3 | Typed lens, descriptor tables, writer profiles, `description.ext` lens, `MissionCmd` | M1 read, M2 write | — | — |
| `plotroom-sidecar` | L3 | Versioned sidecar records, migrations, identity, acknowledgements, regions | M2 | DG017 | — |
| `plotroom-modules` | L3 | Attributes, modules, rules, conversations; `ModuleCmd` | M4 attributes, M5 | DG003, DG004 | — |
| `plotroom-cxl` | L3 | The condition language: parser, scope typing, coverage, printer, engine-faithful evaluator | M4 `when` scope (if DG008 picks one language), M5 | DG008 | — |
| `plotroom-campaign` | L3 | `CampaignModel`, campaign `description.ext` lens, roster and pools, campaign modules, `CampaignCmd` | M5 | DG004 | — |
| `plotroom-cine` | L3 | The Cutscene-node model (v1 subset), later the timeline; `CineCmd` | M5 subset, v1.x | DG009, DG035 | — |
| `plotroom-project` | L4 | `ProjectStore`, snapshots, `LiveTx`/`Scratch`, identity map, reverse references, commit pipeline | M1 read-only, M2 | — | — |
| `plotroom-commands` | L4 | `EditorCommand`, `CommandSpec` registry, admission, queries, schema generation, command-bus types | M2 | DG011 | — |
| `plotroom-validate` | L4 | Rules, runner, fixes, acknowledgements, readiness; structural, limit, craft and MP rules | M1 read-only, grows | DG005 | — |
| `plotroom-view` | L4 | View state, selection, dialog sessions, the headless map interaction state machine | M2 | — | — |

### 4.3 L5 engines and assembly, L6 harness

| Crate | Layer | Owns | Lands | Blocked on | Path |
| --- | --- | --- | --- | --- | --- |
| `plotroom-template` | L5 | minijinja wrapper with fuel, marker escaping, render lints (D020) | M4 | — | — |
| `plotroom-lower` | L5 | The no-code compiler (attributes, modules, rules, cutscene nodes), owned regions, lift recognisers | M4 attributes, M5 | — | — |
| `plotroom-teller` | L5 | Teller: symbols, references, rename, hover, completion, field checks, model-shaped diagnostics | M2 field checks, M4 | — | — |
| `plotroom-knowledge` | L5 | The one knowledge store: Standing Orders entries, cards, primer anchors, skills index, lessons, tips | M4 | DG031, DG032, DG033 | — |
| `plotroom-drill` | L5 | Drill lesson and tour model and runner; goals are validator predicates | M4 | — | — |
| `plotroom-generate` | L5 | Fact providers, menus, templates, compositions, archetypes, patterns, code-owned defaults, Quick Op, seeds, remap tiers | M4 templates, M5, M6 | — | — |
| `plotroom-campaign-compile` | L5 | Sockets, routers, `saveVar` layout, campaign `description.ext`, import (Preserve, Adopt), campaign lints | M5 | — | — |
| `plotroom-campaign-sim` | L5 | Engine-faithful interpreter, Path Explorer, what-if playthrough, "decided" query; balance lab in v1.x | M5 | — | — |
| `plotroom-export` | L5 | Export plans, PBO building, `.plotroomignore`, export scans, requirement manifests | M2 PBO, M3 scans | — | — |
| `plotroom-packs` | L5 | T0 pack loader and lints, contribution sets, built-in pack verification | M4 | — | — |
| `plotroom-session` | L5 | `Session::step`, the typestate `CoreBuilder`, `UserIntent` minting, jobs, rule and hook registration | M2 | — | — |
| `plotroom-provider` | L6 | Provider seam types, capabilities, `CachePolicy`, model setups, role bindings, qualification records, price rows, `MicroUsd` | M4 (faux model), M6 | DG020, DG024, DG025 | — |
| `plotroom-workflow` | L6 | Workflow definitions, TOML loader, definition compiler | M4 | DG007, DG008, DG015 | — |
| `plotroom-decide` | L6 | Capsules, menus, admission of model output, checks, repair, candidates, the selector seam | M4 (faux model), M6 | DG006, DG011, DG019, DG021, DG026 | — |
| `plotroom-workflow-runtime` | L6 | Interpreter, decision journal, ledger, scheduler, cards, resume, staleness, cancellation | M4 | DG010, DG016, DG017 | — |
| `plotroom-campaign-flow` | L6 | Campaign-from-brief code steps, fact providers, checks and gates | M5 no model, M6 | — (v1 size: the classic patterns, D036) | — |
| `plotroom-wilco` | L6 | Wilco: chat modes, agent tools and effects, turn reports, idea cards, persona, explain mode | M6 | DG023 | — |
| `plotroom-evals` | L6 | Instruments E1–E12, qualification suites (shipped for `plotroom qualify` and the Model Manager's local check), cassette tooling (dev) | M6 (Python suites from M0) | DG012 | — |

### 4.4 L7 edge, L8 presentation, tooling

| Crate | Layer | Owns | Lands | Blocked on | Path |
| --- | --- | --- | --- | --- | --- |
| `plotroom-io` | L7 | The only file writer: atomic save, sidecar and journal I/O, app data, crash op journal, `ReadOnlySource`, watchers, OS keyring | M1 read, M2 | DG017 | — |
| `plotroom-net` | L7 | The only HTTP client: `EgressGrant`, offline mode, allowlists, verified resumable downloads (D008) | M6 | — | — |
| `plotroom-provider-http` | L7 | Wire adapters for cloud providers and OpenAI-compatible local servers, streaming, cache wiring (D021) | M6 | — | — |
| `plotroom-model-manager` | L7 | Hardware probe, recommendations from qualification records, pinned manifests, installs, inference-server supervision (D022; recommended list D037) | M6 | — | — |
| `plotroom-preview` | L7 | Staging, launch, supervisor, capability probe, run records, probe runner (D018) | M3 (P0 script in M0) | — | — |
| `plotroom-gamelink` | L7 | Typed loopback client for the game's harness, allowlisted verbs | M3 | — | — |
| `plotroom-mcp` | L7 | Opt-in, loopback, token-authenticated outbound MCP server generated from the command registry (ships in v1, D036) | M4–M6 | — | — |
| `plotroom-plugin-host` | L7 | T2 MCP client and `feed` connectors, then the T1 wasmtime host; grants, egress cards and log (cross-plugin chains: D043) | v1.x | — | — |
| `plotroom-registry` | L7 | Signed pack index client (registry phase RG1; operator: D038) | v1.x | — | — |
| `plotroom-draw2d` | L8 | GPU-free `DrawList` and batcher | M0 spike, M1 | — | — |
| `plotroom-gpu` | L8 | The one wgpu pipeline into an offscreen texture | M0 spike, M1 | — | — |
| `plotroom-fonts` | L8 | FXY fonts, open-licence fallback font, TTF fallback for CJK | M1 | — | — |
| `plotroom-ui-classic` | L8 | Retained control tree for the original dialogs | M0 spike, M2 | — | — |
| `plotroom-map2d` | L8 | The classic map as a pure function to draw lists | M1 | — | — |
| `plotroom-ui` | L8 | egui panels (Plotline, the Tote, Standing Orders, Drill, Wilco, inspector) | M1 | — | — |
| `plotroom-app` | L8 | The `plotroom` binary: GUI by default; forwards `check`, `export`, `stage`, `workflow test`, `pack check`, `qualify` | M1 | — | — |
| `plotroom-cli` | L8 | Headless subcommands over `Session` (v1 ships the minimal CLI: OWQ-14 (a), D036) | M1 | — | — |
| `xtask` | tooling | `layers`, `codes`, `catalog`, `skills`, `provenance`, `defs` | M0 | DG005 (for `codes`) | — |
| `plotroom-testkit` | dev | `EditorHarness`, synthetic SQM, PBO, WRP and raP builders, synthetic island and catalog, faux model, cassettes, virtual clock, seeded ids | M0 skeleton | — | — |
| `plotroom-script-oracle` | dev | Transliterated evaluator used only as a test oracle (doc 23 §13.2) | M2 (roadmap) | — | — |
| `fuzz/` | dev | Separate nightly cargo-fuzz workspace | M0 skeleton | — | — |

Later crates: `plotroom-plugin-sdk` and `plotroom-plugin-testkit` (v1.x; GPL-3.0-or-later for now, D031); the cutscene-director and
atmosphere crates (v1.x; names from the design round's names table, DG037 and D034).

## 5. Newtypes

`AGENTS.md` requires this table. Every newtype derives `Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash` where its inner type
allows, provides `from_raw` and `to_raw`, and implements `Display` in a human-readable form; `plotroom-ids` provides the macro. The rows
below are **planned** (named in `docs/architecture/`); "not set" means the architecture does not fix the inner type yet. A row flips to
**landed** with its real module path when the type is created.

| Type | Inner | Crate / module | Purpose | Status | Source |
| --- | --- | --- | --- | --- | --- |
| `EntityId` | `u128` | `plotroom-ids` | Identity of units, groups, waypoints, triggers and markers; `Display` with a typed prefix (`unit_…`, `grp_…`, `wp_…`, `trg_…`, `mkr_…`), a wrong prefix is a parse error | planned (M1) | [core §7.1](docs/architecture/core-document-model.md); doc 45 §2.3 |
| `ElementId` | `u128` | `plotroom-ids` | Identity of module instances, rules, campaign nodes, edges and variables, shots, conversations (`mod_…`, `rule_…`, `node_…`, `edge_…`, `var_…`, `shot_…`) | planned (M1); campaign use is architecture §8 candidate 3 | core §7.1 |
| `LineId` | `u128` | `plotroom-ids` | Every spoken or displayed line (`line_…`) | planned (M1) | core §7.1 |
| `DocumentId` | not set | `plotroom-ids` | One document of a project (mission, `description.ext`, script, briefing, stringtable) | planned (M1) | [crate-map §3](docs/architecture/crate-map.md); core §5 |
| `CommitId` | not set | `plotroom-ids` | One commit of the project history; links the crash op journal and the decision journal | planned (M1) | [commands §6](docs/architecture/commands-undo-history.md); [agent §5](docs/architecture/agent-runtime.md) |
| `GroupId` | not set | `plotroom-ids` | One undo group | planned (M1) | commands §6 |
| `Revision` | not set | `plotroom-ids` | Snapshot revision; `RevisionSet` is the read set checked at admission | planned (M1) | core §6; commands §4 |
| `Seed` | not set | `plotroom-ids` | Seed of a deterministic generator, recorded in provenance | planned (M1) | core §8.1 |
| `RootSeed` | `u64` | `plotroom-ids` | Build seed carried in a seed code | planned (M1) | crate-map §3; doc 43 §2.9 |
| `Digest` | not set (hash bytes) | `plotroom-ids` | Content hash for capsules, idempotency keys and owned regions | planned (M1) | crate-map §3; core §8.3 |
| `Fingerprint` | not set | `plotroom-ids` | Match key for re-matching identity and for acknowledgements | planned (M1) | core §7.2; [validation §7](docs/architecture/validation-and-lints.md) |
| `VehicleId` | `u32` | `plotroom-mission` | The engine's own file id of a unit or vehicle in `mission.sqm`; never Plotroom identity | planned (M1) | [core §3.2](docs/architecture/core-document-model.md); doc 04 §12.2 |
| `SyncId` | `u32` | `plotroom-mission` | Synchronisation id in `mission.sqm` | planned (M1) | core §3.2; doc 04 §12.2 |
| `MarkerName` | raw bytes | `plotroom-mission` | A marker name as stored, decoded only for display | planned (M1) | core §3.2; doc 04 §12.2 |
| `ClassName` | raw bytes | `plotroom-mission` | A config class name as stored | planned (M1) | core §3.2; doc 04 §12.2 |
| `VarName` | raw bytes | `plotroom-mission` | A unit's variable name (the `text` key): user-facing and renameable, never identity | planned (M1) | core §3.2; doc 45 §2.3 |
| `RegionId` | not set | `plotroom-doc` / `plotroom-sidecar` | A generated region owned by an element | planned (M2) | core §8.3 |
| `GestureId`, `DialogId`, `ToolId`, `MigrationId`, `ImportId`, `ClientId` | not set | `plotroom-doc` (beside `Origin`) | Each a separate newtype naming who or what started an undo group or a provenance record | planned (M2) | core §8.1; commands §6 |
| `CommandId` | string, `area.object.verb` | `plotroom-commands` | Stable id of a registered command; its stability promise to plugins and MCP clients is open | planned (M2) | commands §3, §12 |
| `FixId` | not set | `plotroom-validate` | A quick fix attached to a diagnostic code; Wilco proposes a fix by picking one | planned (M2) | validation §6 |
| `EngineRequestId` | not set (displays as `ER-###`) | `plotroom-profile` | An engine request and, once shipped, the capability id of a target profile | planned (M1) | validation §8; [`docs/upstream/README.md`](docs/upstream/README.md) |
| `ProbeId` | `Box<str>` (doc 33) | `plotroom-preview` | An in-game probe mission run through Preview | planned (M3) | [game §5, §10](docs/architecture/game-integration.md); doc 33 §3 |
| `ConceptId` | `Box<str>` (doc 33) | `plotroom-knowledge` | A Standing Orders entry; flat or dotted form is DG031 | planned (M4), blocked on DG031 | core §3.3; doc 33 §3 |
| `WorkflowId` | not set | `plotroom-workflow` | A workflow definition | planned (M4) | [extensibility §3](docs/architecture/extensibility.md); doc 38 §4.7 |
| `StepId` | not set | `plotroom-workflow` | A step of a workflow definition; also names Drill steps | planned (M4) | agent §4–§5; doc 38 §4.7 |
| `GateId`, `CheckId` | not set | `plotroom-workflow` / `plotroom-decide` | Completion gates and checks, always held as `NonEmpty` lists (I38-GATE) | planned (M4) | agent §4 |
| `RunId` | not set | `plotroom-workflow-runtime` | One workflow run | planned (M4) | agent §5 |
| `ItemKey`, `Attempt` | not set | `plotroom-workflow-runtime` | Item of a fanned-out step and attempt number, parts of `JournalKey` | planned (M4) | agent §5; doc 38 §4.7 |
| `CardToken` | not set | `plotroom-workflow-runtime` | Token of a question card waiting for the user | planned (M4) | agent §5; doc 38 §4.7 |
| `ModelSetupId` | not set | `plotroom-provider` | A configured model setup bound to a role | planned (M4 faux, M6) | agent §3; core §8.1 |
| `MicroUsd` | integer | `plotroom-provider` | Integer money (micro-dollars) for ledgers, caps and plan cards; never a float | planned (M4 faux, M6) | agent §12; crate-map §9 |
| `TurnId` | not set | `plotroom-wilco` | One Wilco chat turn | planned (M6) | commands §6; core §8.1 |
| `PluginId` | `Box<str>`, validated kebab-case (doc 22) | `plotroom-packs` / `plotroom-plugin-host` | A pack or plugin identity | planned (M4) | core §8.1; doc 22 |
| `DiagId` | not set | `plotroom-validate` | One diagnostic instance, an `ItemRef` target | planned (M1) | commands §10 |
| `HookId` | not set | `plotroom-project` | The commit hook named in a `Rejection` | planned (M2) | commands §4 |
| `GeneratorId`, `RecogniserId` | not set | `plotroom-doc` (beside `Source`) | The deterministic generator, or the lift recogniser, named in provenance | planned (M2) | core §8.1 |
| `ScenarioId` | not set | `plotroom-campaign-sim` | A named Path Explorer scenario used as campaign-node Preview state | planned (M5) | game §5 |
| `PackOrPluginId`, `GlyphId`, `TipId` | not set | `plotroom-packs` | Owner and contributed ids of a contribution set; `PackOrPluginId` may turn out to be `PluginId` | planned (M4) | extensibility §3.3 |
| `ProviderId`, `ManagedId` | not set | `plotroom-provider` | A remote provider, and a managed local server, behind the inference seam | planned (M4 faux, M6) | agent §3 |

Not newtypes: `DiagCode` is a generated enum (`plotroom-diag`, from the DG005 registry); `JournalKey` is a struct of `RunId`, `StepId`,
`ItemKey` and `Attempt`; `NonEmpty` and `BoundedVec` are container types.

**Candidates proposed only in research docs** (reconcile with the table above when the owning crate lands):

- Doc 04 §12.2: `TerrainObjectId(i32)`, `AddonName(Bytes)` (also doc 27).
- D017: `PackingMethod`, `StringPoolIndex`, `WrpObjectId` (format crates).
- Doc 19 §4.2: `NodeId`, `EdgeId`, `VarId`, `OutcomeId`, `CharacterId`, `EnumTypeId`, `ActId`, `ChoiceId`, `ItemId` as `u32`; the
  architecture proposes `ElementId` for nodes, edges and variables instead (architecture README §8 item 3).
- Doc 26: `ArchetypeId`, `PatternId`, `ModuleId`, `TwistId`, `KnobKey` (`u16`), `FlavorSlotId` (`u32`).
- Doc 27: `ModId(String)`, `ModSetId(u64)`.
- Doc 29 (strategic layer, v1.1): `CardId(u16)`, `FacilityId`, `ProjectId`, `RegionId`, `ResourceId`, `HangarSlotId`, `PerkId`,
  `OfferSlot` (`u8`). Doc 29's `RegionId` (a map region) and the architecture's `RegionId` (a generated text region) collide; one
  needs a new name before both exist (route to the design round's names table, D034).
- Doc 31: `ModuleInstanceId(u32)`; the architecture uses `ElementId` for module instances.
- Doc 33: `LintId(Box<str>)`; the architecture uses `DiagCode` from the DG005 registry.
- Doc 41: `MoodPresetId(u16)`. Doc 43: `PlaySeed(u16)`, `ItemSeed(u64)`.

## 6. Navigation tips for LLM agents

1. **Order:** `AGENTS.md` → this file → [`docs/README.md`](docs/README.md) §4 → one decision record, one architecture file, the cited
   research sections. Do not load whole research docs (30–127 KB each): read the header and TL;DR, list the `##` headings, read the
   cited sections.
2. **No code yet.** Searching for `.rs` files or `Cargo.toml` finds nothing. Questions about "how the code does X" are answered by
   `docs/architecture/`, marked proposal.
3. **Names in this file are the planned names.** Research docs use working names (`ofp-*`, `ofpe-*`, `.ofpeditor/`); the mapping to
   `plotroom-*` is [crate-map §15](docs/architecture/crate-map.md). Never invent a crate name; add or change one only through the
   crate map and this file.
4. **Before coding a crate,** read its "Blocked on" column: an `open` DG means the dependent part is `proposal-only` or
   `blocked on DGnnn` (`AGENTS.md`, Design Authority).
5. **Where things get recorded, in the same change set:** a new or renamed crate or module → §4 here and the `xtask layers` table; a
   new newtype → §5; a ported upstream test → its row in `docs/porting/upstream-test-map.csv`; an engine limitation → an `ER-###` row
   in `docs/upstream/` (CSV and rendered table); a design gap → a DG file and its index row; a new doc or data file →
   `docs/README.md`.
6. **Label collisions:** `D9` (lint) vs `D009` (decision); `T0`–`T4` (model, plugin or evidence tiers); `P0`–`P4` (Preview phases
   vs doc 19 phases); `AT1` in docs 31–33. See [`docs/README.md`](docs/README.md) §2.2.
7. **Naming and hygiene:** no third-party marks or island names in crate, module, format, sidecar or generated-header names (profile
   ids `Cwa199`, `Cwr`, `Ce` are data values, D003); no private project names anywhere; nothing from `/private/`.
8. **Opt-in local tests** use `PLOTROOM_CORPUS_DIR` and `PLOTROOM_GAME_DIR` (planned; [testing-strategy §15](docs/architecture/testing-strategy.md));
   CI never depends on a game install or proprietary data.
9. **Tools** in `tools/` are research harnesses in Python's standard library. Their raw outputs are git-ignored; only derived CSVs
   under `docs/research/data/` are committed.
10. **Skills and prompts** are product content for Wilco (the editor's own AI), loaded by the editor, not instructions for coding
    agents. Their tool names are provisional.

## 7. Maintaining this file

- Update it in the same change set as any change to the repository layout, a crate, a module boundary or a newtype (`AGENTS.md`).
- When a crate lands: fill its Path cell (a filled path means landed) and record any rename from the crate map. When a newtype lands:
  set its Status to landed and its real module path.
- Keep it at or under about 600 lines. When it grows, move per-crate detail into each crate's own module docs and keep the routing
  tables here.

## Verification notes

### Index creation (2026-09-27)

- Built from `AGENTS.md`, [`docs/architecture/crate-map.md`](docs/architecture/crate-map.md) (read in full), the architecture README
  (layers, §7 row 15, §8), `core-document-model.md` §3.2 and §7–§9, the `Origin`, journal and ledger sketches in
  `commands-undo-history.md` and `agent-runtime.md`, `docs/roadmap.md` and the M0 section of the M0–M3 roadmap file, and the newtype
  sketches of docs 04, 19, 22, 26, 27, 29, 31, 33, 38, 41, 43 and 45 and D017.
- The repository listing was taken from the working tree on 2026-09-27, excluding git-ignored outputs.
- Crate "Owns" cells shorten the crate map's cells; the crate map wins where they differ. "Blocked on" adds DG005 for
  `plotroom-validate` and `xtask codes`, DG011 for `plotroom-commands`, DG017 for `plotroom-io`, DG031–DG033 for `plotroom-knowledge`,
  OWQ-19 for the Model Manager, DG014 and OWQ-03 for the plugin host, DG030 for the registry and OWQ-14 for the CLI, each taken from
  the architecture text, the roadmap gates or the owner questions.
- No architecture, roadmap, decision or research file was edited by this change.

### Consistency review (2026-09-27)

- Every crate name in `docs/architecture/`, `docs/roadmap*`, `docs/decisions/` and `docs/upstream/` matches the crate map (the only
  other `plotroom-` names are the `plotroom-*/1` definition-format tags and `AGENTS.md`'s `plotroom-core` example). The ten id types
  named in architecture sketches but missing from §5 (`DiagId`, `HookId`, `GeneratorId`, `RecogniserId`, `ScenarioId`,
  `PackOrPluginId`, `GlyphId`, `TipId`, `ProviderId`, `ManagedId`) now have rows. `plotroom-script-oracle` lands in M2 (roadmap);
  `plotroom-evals` ships for in-app qualification (crate map §9).
- `docs/research/` now also holds a doc 47 and `data/slm-candidates.csv`, added after this index; §2's "01–45" and "7 CSVs" change
  when `docs/README.md` indexes them.

### Research docs 46–48 and `tools/local-qual` (2026-09-27)

- §2 now reads research docs 01–48 (doc 49 in progress, not linked) and 10 data CSVs, matching `docs/README.md` §5 and §6.1; this
  resolves the note above. The decisions line records that every owner question was answered on 2026-09-27.
- The `tools/local-qual` entry lists its current tracked files, taken from the working tree: `README.md`, `run.py`, `score.py`,
  `backends.py` and the six suite files, including `pick-hard.json` (`results/` and Python caches are git-ignored). Doc 48 describes a
  cloud backend with a budget cap and an uplift comparer, tested against a local mock server only, that lands as one patch; the change
  set that applies it updates this entry.
- §4's introduction notes that the OWQs in "Blocked on" (OWQ-03, OWQ-13, OWQ-14, OWQ-15, OWQ-19) are answered and that DG014 and
  DG030 are decided; the cells are left unchanged until the architecture folds the answers. The research-doc size range in §6 is now 30–127 KB (doc 47 is 126 KB).
- No crate, module or newtype changed; no architecture, decision, research or tool file was edited by this change.

### Consistency review of the owner answers (2026-09-27)

- The crate map now reads "—" in the "Blocked on" cells that named answered owner questions or DG014 and DG030, so §4 follows
  it: `plotroom-campaign-flow`, `plotroom-model-manager`, `plotroom-mcp`, `plotroom-plugin-host`, `plotroom-registry` and
  `plotroom-cli` name the record that settles them (D036, D037, D043, D038) in their "Owns" cells instead, and the later-crates line
  and the `RegionId` note point to D031 and D034. This resolves the note above. No crate, layer, landing milestone or newtype changed.

### `tools/quota-sim` (2026-09-28)

- A new research tool: a seeded replay of four user days against the free tiers of doc 50 and a congestion model calibrated on one
  observed upstream-throttling window, for the planned rate-limit doc (52). Its `data/` files are inputs (like `local-qual/suites/`);
  it writes results only where the caller points it. §1 and §2 list it. No crate, module boundary or newtype changed.

### `tools/local-qual`: cloud backend, logprob mode, cascade simulator and scaffold arms land (2026-09-28)

- §1 and §2 list the tool's current files. The pending cloud-backend patch (doc 48; free-only mode, the Windows key scripts,
  `--pick-mode logprob` and `cascade.py` from doc 53) and the scaffold arms (doc 59) were merged into `tools/local-qual`; this
  resolves the "pending" note of the doc 46–48 entry above. The five modules over the ~600-line ceiling (`run.py`, `score.py`,
  `logprob_pick.py`, `cascade.py`, `scaffolds.py`) were split into six new ones with every name re-exported (`run_cli.py`,
  `run_records.py`, `score_checks.py`, `logprob_dist.py`, `cascade_numbers.py`, `scaffold_algos.py`).
- The tool's tests live in `tools/local-qual/tests/` and run with the standard library's `unittest`; checks that compared the
  tool with a copy of an earlier version now compare with golden files frozen from that version (`tests/golden/`).
- Fixed while landing, test first: the budget booked OpenRouter's non-BYOK `upstream_inference_cost` on top of `cost` (doc 54
  §4.2), and `run.py` gained `--output`, an alias of `--out` that `cloud/run-cloud.ps1` can pass through `powershell -File`.
- No crate, module boundary of the planned workspace or newtype changed.
