# Crate map

> **Status:** proposal (architecture baseline 2026-09-27). Nothing here is decided unless it restates `AGENTS.md`, a decision
> record (`Dnnn`), a decided DG or an owner answer (`OWQ-nn`, all answered 2026-09-27). Crate names follow D002 item 4 and are final
> only when `CODE-INDEX.md` records them.
> **Part of:** [architecture overview](README.md). **Main sources:** doc 04 §12.1; doc 06 §4.1; doc 07 §15–§17; doc 08 §6; doc 12 §3;
> doc 13 §9; doc 20; doc 21 §1.3; doc 22 §7; doc 23 §13; doc 38 §4.7; doc 45 §2.9; doc 46 §4; D001, D002, D013, D016, D017, D021, D022,
> D025.

The workspace is layered. Edges point downward only; upward needs are met by traits defined low and implemented high, registered at
assembly (`CommitHook`, `Rule`, `FixProvider`, `FieldChecker`, `FactSource`, `CodeStep`, `ReadOnlySource`). Crates are created in
the milestone that first needs them, not as empty scaffolding; `CODE-INDEX.md` records each crate's landing milestone.

## 1. Reading this map

- **Layer:** L0 (foundation) to L8 (presentation). A crate may depend on lower layers and on the same-layer edges listed in §2.2.
- **Lands:** the milestone of the architecture's build order ([README](README.md) §6); the roadmap may rename milestones.
- **Tests:** the `target_area` of `docs/porting/upstream-test-map.csv` whose rows the crate ports (§13).
- **Licence:** every crate is GPL-3.0-or-later (D001); files translated from engine source carry `Derived-From:` headers (D017 item 2).
- **Blocked on:** open DGs whose decision the crate needs before its dependent part is coded (`AGENTS.md` Design Authority).

## 2. Layer rules and enforcement

### 2.1 Layers

| Layer | Purpose | May use |
| --- | --- | --- |
| L0 Foundation | Ids, bytes, encodings, profiles, diagnostic codes | `std` and tiny dependencies |
| L1 Formats | Pure `&[u8]` parsers and writers, one `Error` enum each | L0 |
| L2 World facts | VFS, installs, catalogs, terrain over an injected read-only source | L0–L1 |
| L3 Kernel and models | The document kernel and typed document models, with their command enums and planners | L0–L2 |
| L4 Core | Project store, command registry and admission, validation framework, view state | L0–L3 |
| L5 Domain engines and assembly | Compilers, generators, Teller, knowledge, Drill, packs, export; the session that assembles the core | L0–L4 |
| L6 Harness | Provider seam types, workflows, decision kernel, runtime, campaign flow, Wilco, evals: no I/O | L0–L5 except `plotroom-session` |
| L7 Edge | The only crates with file writes, processes, network or sandboxes | L0–L6 |
| L8 Presentation and binaries | Renderer, egui panels, the app and CLI binaries | Everything |

### 2.2 Same-layer edges allowed

- L0: `plotroom-profile` → `plotroom-ids`.
- L1: `plotroom-config` → `plotroom-preproc`; `plotroom-script` → `plotroom-script-catalog`; `plotroom-rsc` → `plotroom-config`.
- L2: `plotroom-catalog`, `plotroom-terrain`, `plotroom-install` → `plotroom-vfs`.
- L3: every model crate → `plotroom-doc`; `plotroom-campaign`, `plotroom-modules` → `plotroom-cxl`; `plotroom-sidecar` → `plotroom-doc`.
- L4: `plotroom-commands`, `plotroom-validate`, `plotroom-view` → `plotroom-project`; `plotroom-view` → `plotroom-commands`.
- L5: `plotroom-lower` → `plotroom-template`; `plotroom-campaign-compile` → `plotroom-lower`; `plotroom-generate` → `plotroom-lower`,
  `plotroom-campaign-compile`, `plotroom-template`; `plotroom-drill` → `plotroom-knowledge`; `plotroom-export` →
  `plotroom-campaign-compile`; `plotroom-session` → every other L5 crate.
- L6: `plotroom-decide` → `plotroom-provider`; `plotroom-workflow-runtime` → `plotroom-workflow`, `plotroom-decide`;
  `plotroom-campaign-flow` → `plotroom-workflow`, `plotroom-decide`; `plotroom-wilco`, `plotroom-evals` → `plotroom-workflow-runtime`.
- L7: every networked crate → `plotroom-net`; `plotroom-model-manager`, `plotroom-preview` → `plotroom-io`; `plotroom-preview` →
  `plotroom-gamelink`.

This list is the starting table for `xtask layers`; adding a same-layer edge is a reviewed change to that table, never an incidental
`Cargo.toml` edit.

### 2.3 Capability confinement

| Capability | Only in | Why |
| --- | --- | --- |
| File writes (`std::fs` write APIs, temp files, renames) | `plotroom-io` | One place for atomic writes, `.bak` copies, installs and journals |
| File reads of game data and projects | `plotroom-io` (implements `ReadOnlySource`) | L2 crates stay pure and testable in memory |
| Child processes (`std::process`, `tokio::process`) | `plotroom-preview` (game executables of a discovered install); `plotroom-model-manager` (managed inference server and helper) | Every launch is a user action; nothing the agent can reach |
| Outbound network (HTTP clients, non-loopback sockets) | `plotroom-net` | One `EgressGrant` check, offline mode, allowlists on the final request path (D008) |
| Loopback sockets | `plotroom-gamelink` (client of the game's harness); `plotroom-mcp` (server); `plotroom-net` (local model servers) | The harness and MCP are loopback by design |
| OS keyring | `plotroom-io::secrets` | Secrets never in files or manifests |
| `tokio` runtime and I/O features | L7 and L8 | Harness crates use only sync and cancellation types |
| egui / eframe | `plotroom-ui`, `plotroom-app` | Everything below is headless |
| wgpu | `plotroom-gpu` (and egui-wgpu through the app) | One pinned wgpu version |
| wasmtime, rmcp | `plotroom-plugin-host`; rmcp also `plotroom-mcp` | Sandboxes and protocols stay at the edge |
| Environment variables | `plotroom-app`, `plotroom-cli`, test code | No hidden inputs in libraries |
| `UserIntent` minting | `plotroom-session::intent`, reachable only from the UI input adapter and the CLI parser | Consent cannot be forged ([commands-undo-history.md §4.4](commands-undo-history.md)) |

Model downloads from Hugging Face go through `plotroom-net`'s verified, resumable download API. `hf-hub` (D022's candidate) is used
only if its transport can be routed through `plotroom-net`; otherwise its URL scheme is re-implemented there (a spike decides). A pull
through the user's own Ollama is a loopback request that makes another process download; `plotroom-net` treats it as egress to the
source it names (enabled source, offline refusal, user-started; [agent-runtime.md §13](agent-runtime.md)).

### 2.4 Workspace lints (`AGENTS.md`, enforced mechanically)

```toml
[workspace.lints.rust]
unsafe_code = "forbid"

[workspace.lints.clippy]
indexing_slicing = "deny"
string_slice = "deny"
unwrap_used = "deny"
expect_used = "deny"
panic = "deny"
unreachable = "deny"
todo = "deny"
unimplemented = "deny"
```

- Every crate sets `lints.workspace = true`; format crates add `arithmetic_side_effects = "deny"` so untrusted-offset arithmetic uses
  `checked_*`/`saturating_*` (`AGENTS.md` integer overflow rule).
- Test code is exempt through clippy's test allowances where a configuration key exists (for example `allow-unwrap-in-tests`,
  `allow-expect-in-tests`) and `#[cfg_attr(test, allow(...))]` elsewhere. Whether `indexing_slicing` also catches `Index` on maps is
  [U]; if not, a review grep or small custom lint covers it ([testing-strategy.md §16](testing-strategy.md)).
- Per-crate `clippy.toml` `disallowed-methods` and `disallowed-types` implement §2.3.

### 2.5 `xtask layers` and cargo-deny

- `xtask layers` reads a declared layer table (crate → layer, allowed same-layer edges, forbidden edges) and checks it against
  `cargo metadata`. It fails when: an edge points upward; an L6 crate, `plotroom-plugin-host` or `plotroom-mcp` depends on
  `plotroom-session`; anything below L8 depends on egui; anything outside §2.3 depends on an HTTP client, wasmtime or rmcp. Its evidence
  test is a deliberately bad edge that must fail (a first-milestone exit criterion).
- `cargo-deny` bans, per layer, the runtime and I/O features of tokio, HTTP clients, egui, wgpu, wasmtime and rmcp below the layers that
  may use them, with wrapper allowlists so a transitive helper crate cannot bypass the clippy bans (doc 21 §1.3). Its licence allowlist
  accepts GPL-3.0-compatible licences only and bans GPL-2.0-only crates (D001; doc 07).

## 3. L0 Foundation

| Crate | Owns | Implements | Tests | Lands | Blocked on |
| --- | --- | --- | --- | --- | --- |
| `plotroom-bytes` | Safe-read cursor (`read_u8`, `read_u16_le`, `read_u32_le` with checked offsets), the era's varint, BI LZSS encode/decode with both checksum kinds, `Caps` | doc 07 §16; D017 | formats-pbo (LZSS vectors) | M1 | — |
| `plotroom-ids` | The newtype macro (`from_raw`, `to_raw`, `Display`, the required derives); `EntityId`, `ElementId`, `LineId`, `DocumentId`, `CommitId`, `GroupId`, `Revision`, `RevisionSet`; `IdSource`, `Clock`, `Seed`, `RootSeed`, `RollScope`; `Digest`, `Fingerprint`, `NonEmpty`, `BoundedVec` | doc 45 §2.3; doc 38 §4.7; doc 43 §2.9 | — | M1 | doc 45 OQ4 (minting) |
| `plotroom-encoding` | Legacy code pages and UTF-8, `byte_len_in(TargetEncoding)`, the hidden-character scan | doc 04 §7; doc 21 §9.3; doc 45 §2.6 | — | M1 | — |
| `plotroom-profile` | `TargetProfile { Cwa199, Cwr { release }, Ce { rev, capabilities } }`, `ProfileSet`, availability and evidence tiers T1–T4, capability ids (`ER-###`), the "Requires" computation types | D003; doc 23 §13; doc 35 §8.3; `docs/upstream/` | — | M1 | — |
| `plotroom-diag` | The generated `DiagCode` enum and code metadata from the registry | DG005 | — | M1 | DG005 |

**Shared read helpers and `AGENTS.md`.** `AGENTS.md` asks for safe-read helpers in each format crate's `src/read.rs` and one `Error`
enum per crate. Each format crate keeps a thin `read.rs` that wraps `plotroom-bytes`' cursor and maps its read error into the crate's
own named-field variant (`Error::UnexpectedEof { needed, available, context }`). The rule holds literally; the implementation is shared.

## 4. L1 Formats

All are pure `&[u8]` (or `Read + Seek` for large archives) parsers and writers with caps from the engine's hardened limits, permissive
on unknown values and strict on structure, each with its own `Error` enum and fuzz targets (D017).

| Crate | Owns | Implements | Tests | Lands |
| --- | --- | --- | --- | --- |
| `plotroom-pbo` | `Pbo<'input>` with borrowed entries, `PackingMethod`, properties, writer (stored and compressed), streaming reader | doc 07 | formats-pbo | M1 |
| `plotroom-preproc` | Directives, `IncludeResolver` trait (the VFS confines it), source maps | doc 04 §2; doc 07 | formats-config | M1 |
| `plotroom-config` | Lossless green-tree CST, resolved view with inheritance, raP read (v2–4) and write (v4), `ConfigOrigin` | doc 04 §2, §4, §12; doc 07 | formats-config | M1 |
| `plotroom-stringtable` | CSV CST, per-language columns, legacy and UTF-8 files | doc 04 §7 | formats-config (stringtables) | M1 |
| `plotroom-briefing` | CST of the engine's HTML subset with spans | doc 04 §6 | mission-model | M2 |
| `plotroom-script` | Lossless lexer, the faithful SQS line model, SQF AST with spans, `check_field` with engine-parity verdicts, `lint` | doc 23 §13 | script-lang | M2 |
| `plotroom-script-catalog` | Generated static per-profile overload tables with availability, evidence tiers, registration gate and risk tags; a separate harness-verb table | doc 23 §14; doc 24 §5.1; I35-90 | script-lang | M2 |
| `plotroom-wrp`, `plotroom-p3d`, `plotroom-paa`, `plotroom-fxy` | Terrain, map-info subset of models, textures, bitmap fonts | doc 07 | formats-wrp, formats-p3d, formats-paa, formats-font | M1 |
| `plotroom-rsc` | `DisplaySpec`/`ControlSpec` (IDD, IDC, control types, style bits, colours, fonts) with inheritance; the fallback look-alike theme data | doc 05 §2; doc 06 §4.1 | editor-ui | M0 spike, M2 |
| `plotroom-audio` | WSS, OGG and WAV decoding; the lip-sync generator ported with its upstream tests | doc 41 §5.6 | formats-audio | v1.x |

The command catalog is generated by `xtask catalog` from pinned CWR release snapshots and CE, BI-wiki `since` facts and optional
owner-local 1.99 evidence, with a CI drift check (doc 23 §14). The earlier SQF tooling fork is ported and restructured, not depended
on; its oracle becomes the dev-only `plotroom-script-oracle` (doc 23 §13.2).

## 5. L2 World facts

| Crate | Owns | Implements | Tests | Lands |
| --- | --- | --- | --- | --- |
| `plotroom-vfs` | Mount order (base → `res` → mods), PBO-stem prefixes, case-insensitive lookup, `..` collapse, `#include` confinement, "who serves this file" | doc 27 §2.1, §4.3; doc 34 mo02 | platform-paths | M1 |
| `plotroom-install` | Install discovery (pure VDF/ACF parsers), profile folders, executable per profile; spawns nothing | doc 08 §5 | platform-paths | M1 |
| `plotroom-catalog` | Engine-parity config merge, class provenance, unit cards with `basis`, facets, mod sets and locks, drift report, `addOns` derivation, catalog and mod lints | doc 27 §4; doc 42 §2; D030 | — | M1 |
| `plotroom-terrain` | Heights, road graph, objects, places with fallback clusters, candidate sites, spatial index; sun, sight and earshot helpers later | doc 25 §6.1; doc 39; doc 41 | formats-wrp (shared) | M1 |

## 6. L3 Kernel and document models

| Crate | Owns | Implements | Tests | Lands | Blocked on |
| --- | --- | --- | --- | --- | --- |
| `plotroom-doc` | `Guarded<T>`, `Op`/`OpKind`/`Recorded`, `ElementRef`, `FieldKey`/`FieldValue`, `OpenGroup`, `GroupKind`, `UndoGroup`, `History` and lanes, `MergeKey`, `Origin`, `Provenance`, `Rejection`, `merge_regenerated`, the planning service traits | doc 45 §2.1–§2.3, §2.7; doc 25 §9.3 | editor-core | M1 types, M2 | DG011 |
| `plotroom-mission` | The typed lens, descriptor tables, writer profiles, "Normalize as engine", the `description.ext` lens, `MissionCmd` and its planners | doc 04 §3, §5, §12; doc 37 §3 | mission-model | M1 read, M2 write | — |
| `plotroom-sidecar` | Versioned DTOs, typed migrations, identity records, planning layer, acknowledgements, regions, project-log records | doc 45 §2.7; doc 34 ed01, ed06, ed08, ed16 | — | M2 | DG017 (journal records) |
| `plotroom-modules` | Rung 1–3 authoring models: attributes, modules (mission and campaign), rules, conversations; `ModuleCmd` | doc 31 §3–§5; doc 37 §4; DG003, DG004 | — | M4 attributes, M5 modules and rules | DG003, DG004 |
| `plotroom-cxl` | The condition language: parser, scope typing, intervals, coverage, printer, engine-faithful evaluator | doc 19 §5; DG008 | campaign | M4 workflow `when` scope (if DG008 picks one language), M5 | DG008 |
| `plotroom-campaign` | `CampaignModel`, campaign `description.ext` lens, roster and pools, campaign modules, `CampaignCmd` | doc 19 §4; doc 26 §9; doc 29 §3 | campaign | M5 | DG004 |
| `plotroom-cine` | The Cutscene-node model (v1 subset) and, later, the timeline model; `CineCmd` | doc 32 §3; doc 35 rc35, rc50 | — | M5 subset, v1.x | DG009, DG035 |

## 7. L4 Core

| Crate | Owns | Implements | Tests | Lands |
| --- | --- | --- | --- | --- |
| `plotroom-project` | `ProjectStore`, `Document`, `DocSlot`, `Snapshot`, `LiveTx`/`Scratch`, identity map and re-match, reverse-reference index, the commit pipeline and hook traits, crash-journal record format (no I/O) | doc 45 §2.1–§2.3, §2.7 | editor-core | M1 read-only, M2 |
| `plotroom-commands` | `EditorCommand`, `CommandSpec` registry, admission and `Admitted<T>`, `resolve_targets`, `QueryOp`/`MissionQuery`, schema generation, the command bus types | doc 17 §5; doc 21 §1.2; doc 45 §2.8 | editor-core | M2 |
| `plotroom-validate` | `Rule`, `RuleOutcome`, runner, fixes, acknowledgements, readiness model, engine-structural and limit rules, craft (MC) and MP rules | doc 45 §2.6; [validation-and-lints.md](validation-and-lints.md) | mission-model | M1 read-only, grows |
| `plotroom-view` | `ViewState`, `Selection`, `ItemRef`, `DragPreview`, `PreviewEntity`, `DialogSession`, the headless map interaction state machine | doc 03; doc 45 §2.4 | editor-ui | M2 |

## 8. L5 Domain engines and assembly

| Crate | Owns | Implements | Tests | Lands |
| --- | --- | --- | --- | --- |
| `plotroom-template` | minijinja wrapper with fuel, marker escaping, render lints | D020; doc 22 §2.1 | — | M4 |
| `plotroom-lower` | The no-code compiler: attributes, modules, rules, cutscene nodes; compiler-owned singleton allocator; owned regions; `EmitMode`; lift recognisers; emitted-content checks | doc 31 §4.4–§4.5, §5.3, §8; doc 37; doc 32 §3.5 | — | M4 attributes, M5 |
| `plotroom-teller` | Teller: symbol index and references, rename, hover, completion, field checks adapter, silent-failure lints, model-shaped diagnostics | doc 23; doc 31 §7; D002 | script-lang | M2 field checks, M4 |
| `plotroom-knowledge` | The one knowledge store: Standing Orders entries, cards, primer anchors, skills index, lessons, tips; evidence marks | doc 30 §4; doc 33 §3; DG031, DG032, DG033 | — | M4 |
| `plotroom-drill` | Lesson and tour model and runner; goals are validator predicates | doc 33 §5 | — | M4 |
| `plotroom-generate` | Fact providers, the menu algorithm, templates with anchors, compositions, archetype and pattern libraries, code-owned defaults, Quick Op, seed scopes and codes, remap tiers | doc 25 §6; doc 26; doc 35 §9; doc 42 §2.9; doc 43 | — | M4 templates, M5, M6 |
| `plotroom-campaign-compile` | Sockets, routers, finisher, `saveVar` layout, campaign `description.ext`; import in Preserve and Adopt modes; campaign lints | doc 19 §7 | campaign | M5 |
| `plotroom-campaign-sim` | Engine-faithful interpreter, Path Explorer, what-if playthrough, "decided" query; balance lab in v1.x | doc 19 §6.4; doc 29 §5.2 | campaign | M5 |
| `plotroom-export` | Export plans, PBO building, `.plotroomignore`, export scans, requirement manifests | doc 04 §9; doc 42 §2.8 | — | M2 PBO, M3 scans |
| `plotroom-packs` | T0 loader and lints, contribution sets, vendoring, built-in pack verification | doc 22 §2.1, §7; doc 42 §5 | — | M4 |
| `plotroom-session` | `Session::step`, the typestate `CoreBuilder`, `UserIntent` minting, job scheduling, rule and hook registration | doc 45 §2.9; [commands-undo-history.md §11](commands-undo-history.md) | — | M2 |

## 9. L6 Harness (no I/O)

| Crate | Owns | Implements | Lands | Blocked on |
| --- | --- | --- | --- | --- |
| `plotroom-provider` | `InferenceProvider`, requests, constraints, events, capabilities, `CachePolicy`, model setups, role bindings, qualification records, price-row types, `MicroUsd` | doc 12 §3; doc 13 §9; doc 40 R1, R10; D021 | M4 (faux model), M6 | DG020, DG024, DG025 |
| `plotroom-workflow` | Definitions, TOML loader, definition compiler | doc 38 §3, §6.2; D025 | M4 | DG007, DG008, DG015 |
| `plotroom-decide` | Capsules, menus, admission of model output, checks, repair, candidates, selector seam | doc 21 §3–§4, §8; doc 25 §6–§7; doc 16 | M4 (faux model), M6 | DG006, DG011, DG019, DG021, DG026 |
| `plotroom-workflow-runtime` | Interpreter, journal, ledger, scheduler, cards, resume, staleness, cancellation, `RunEvent` | doc 38 §4 | M4 | DG010, DG016, DG017 |
| `plotroom-campaign-flow` | Campaign-from-brief code steps, fact providers, checks and gates | doc 25 §4; doc 38 §8.1 | M5 no model, M6 | — (size decided: the classic patterns in v1, OWQ-13 (a)) |
| `plotroom-wilco` | Chat modes, `AgentTool`/`AgentEffect`, turn reports, idea cards, persona, explain mode | doc 21 §4–§5, §11.7 | M6 | DG023 |
| `plotroom-evals` | Instruments E1–E12, qualification suites (shipped: `plotroom qualify` and the Model Manager's "Check this model on my machine"), cassette tooling (dev only) | doc 25 §11; doc 40 §7; doc 44; `tools/local-qual` | M6 (Python suites from M0) | DG012 |

## 10. L7 Edge crates

| Crate | Owns | Implements | Tests | Lands |
| --- | --- | --- | --- | --- |
| `plotroom-io` | The only file writer: atomic save with `.bak`, external-change check, sidecar and journal segment I/O, app-data stores, crash op journal, `ReadOnlySource` implementation, file watchers, OS keyring | doc 04 §12.3(10); doc 45 §2.7; DG017 | platform-paths (shared) | M1 read, M2 |
| `plotroom-net` | The only HTTP client: `EgressGrant` checks, offline mode, final-path allowlists, no redirects off origin, caps, SSRF guards, resumable verified downloads | D008; doc 22 §3.2 | — | M6 |
| `plotroom-provider-http` | Wire adapters (Anthropic, OpenAI, Gemini, OpenAI-compatible local servers), SSE streaming, cache-policy wiring; any rig dependency exact-pinned here only | D021; doc 12 | — | M6 |
| `plotroom-model-manager` | Hardware probe, recommendation from qualification records, pinned manifests, pinned Hugging Face downloads via `plotroom-net`, atomic installs via `plotroom-io`, refusal of GGUFs the pinned runtime cannot run, supervision of the managed `llama-server` sidecar, the primary local runtime by the owner's decision of 2026-09-27 (and a helper process for any embedded engine) | D022 and its amendment note; doc 13 §6, §9; doc 44 §5.3; doc 46 §4 | — | M6 |
| `plotroom-preview` | Pure staging plus launch, supervisor, capability probe, run records, probe runner | doc 08 §6; D018 | preview-harness | M3 (P0 script in M0) |
| `plotroom-gamelink` | Typed loopback client for the game's harness, allowlisted verbs | doc 08 §4.4; doc 24 §5.4 | preview-harness | M3 |
| `plotroom-mcp` | Opt-in, loopback, token-authenticated outbound MCP server generated from the registry | doc 38 §9; D006 | — | M4–M6 (ships in v1: OWQ-15 (a)) |
| `plotroom-plugin-host` | T2 MCP client and `feed` connectors, then T1 wasmtime host; grants, egress cards and log | doc 22; D007, D008 | — | v1.x |
| `plotroom-registry` | Signed pack index client (RG1) | doc 42 §5 | — | v1.x |

## 11. L8 Presentation and binaries

| Crate | Owns | Implements | Tests | Lands |
| --- | --- | --- | --- | --- |
| `plotroom-draw2d` | GPU-free `DrawList` and batcher | doc 06 §4.2–§4.3 | map-render | M0 spike, M1 |
| `plotroom-gpu` | The one wgpu pipeline into an offscreen texture | doc 06 §4.3–§4.4 | — | M0 spike, M1 |
| `plotroom-fonts` | FXY fonts, OFL fallback, TTF fallback for CJK | doc 06 §2.4; doc 34 mo23 | formats-font (shared) | M1 |
| `plotroom-ui-classic` | Retained control tree for the original dialogs | doc 06 §4.1; doc 05 | editor-ui | M0 spike, M2 |
| `plotroom-map2d` | The classic map as a pure function to draw lists | doc 06 §2.5 | map-render | M1 |
| `plotroom-ui` | egui panels | [ui-shell.md](ui-shell.md) | — | M1 |
| `plotroom-app` | The `plotroom` binary: GUI by default; forwards `check`, `export`, `stage`, `workflow test`, `pack check`, `qualify` to the CLI code | D016 | — | M1 |
| `plotroom-cli` | Headless subcommands over `Session`; v1 ships the minimal CLI (owner, OWQ-14 (a)): lint, compile/export, round-trip check, golden-journal replay; no agent | doc 34 ed15 | — | M1 |

## 12. Tooling and dev crates

- `xtask` (not shipped): `catalog` (script catalog generator and drift check), `codes` (registry → `plotroom-diag`, fixtures, tests,
  Standing Orders links), `skills` (the SKILL.md index), `layers` (§2.5), `provenance` (DG018 records), `defs` (compiles built-in
  definitions with the same loader).
- `plotroom-testkit` (dev-dependency): `EditorHarness`, `SqmBuilder`, synthetic PBO, WRP and raP builders, a synthetic island and
  catalog, faux model, cassettes, virtual clock, seeded `IdSource`.
- `plotroom-script-oracle` (dev-only): the transliterated evaluator used as a test oracle (doc 23 §13.2).
- `fuzz/`: a separate nightly workspace with cargo-fuzz targets (D017).
- v1.x: `plotroom-plugin-sdk` and `plotroom-plugin-testkit` (GPL-3.0-or-later for now, OWQ-03 (a)); crates for the cutscene director
  and atmosphere (names from the design round's names table: DG037; OWQ-08 (a)).

## 13. Upstream test areas and their crates

| `target_area` | Crates | `todo` / `probe` rows |
| --- | --- | --- |
| formats-pbo | `plotroom-pbo`, `plotroom-bytes` | 11 / 0 |
| formats-config | `plotroom-config`, `plotroom-preproc`, `plotroom-stringtable` | 23 / 0 |
| script-lang | `plotroom-script`, `plotroom-script-catalog`, `plotroom-teller`, `plotroom-script-oracle` | 20 / 3 |
| mission-model | `plotroom-mission`, `plotroom-briefing`, `plotroom-validate` | 8 / 4 |
| formats-paa, formats-font, formats-wrp, formats-p3d, formats-audio | `plotroom-paa`, `plotroom-fxy`, `plotroom-wrp`, `plotroom-p3d`, `plotroom-audio` | 15, 4, 13, 10, 5 / 0 |
| editor-core | `plotroom-doc`, `plotroom-project`, `plotroom-commands` | 6 / 0 |
| editor-ui | `plotroom-view`, `plotroom-rsc`, `plotroom-ui-classic` | 12 / 0 |
| map-render | `plotroom-map2d`, `plotroom-draw2d` | 1 / 0 |
| campaign | `plotroom-campaign`, `plotroom-cxl`, `plotroom-campaign-compile`, `plotroom-campaign-sim` | 1 / 10 |
| platform-paths | `plotroom-install`, `plotroom-vfs`, `plotroom-io` | 5 / 1 |
| preview-harness | `plotroom-preview`, `plotroom-gamelink` | 8 / 2 |

Ported rows change their CSV status and target crate in the same change set (D013; [testing-strategy.md §4](testing-strategy.md)).

## 14. Licences and provenance

- **GPL-3.0-or-later everywhere** (D001); there is no permissive lane for format crates. Bohemia's §7 terms go into `NOTICE` when the
  first CWR-derived file lands; the generated-content permission is doc 02's draft plus an explicit coverage list, with legal review
  before 1.0 (OWQ-01 (b)).
- Files translated from CWR or CE carry `Derived-From:` headers citing repo, commit and path (D017 item 2).
- Third-party ports (for example TrenchBroom tests, GPL-3.0-or-later) carry DG018 records; GPL-3.0-only code is not ported by default,
  only when no reasonable re-implementation exists and the owner signs off (OWQ-04).
- The plugin SDK, WIT and test kit are GPL-3.0-or-later for now (OWQ-03 (a)).
- Dependencies must be GPL-3.0-compatible; cargo-deny enforces the allowlist (§2.5). CUDA runtimes are never bundled (D022).

## 15. Naming (D002 item 4)

| Research working name | Plotroom name |
| --- | --- |
| `ofp-*`, `ofpe-*` crates (docs 04, 06, 07, 08, 12, 13, 19, 22, 23, 25, 26, 29, 31, 37, 38) | `plotroom-*` as listed here |
| `ofp-workflow-runtime`, `ofp-agent`, `ofpe-harness-client` | `plotroom-workflow-runtime`, `plotroom-wilco`, `plotroom-gamelink` |
| `ofp-mcp` | `plotroom-mcp` |
| `.ofpeditor/`, `ofp-editor.meta.toml` | `.plotroom/` ([core-document-model.md §10](core-document-model.md)) |
| WIT `ofp:plugin@1` | `plotroom:plugin@1` |
| Generated folder `ofpe\`, header `; ofp-editor:generated <hash>` | `plotroom\`, `; plotroom:gen <hash>` |
| Module keys `ofpe.*` | `core.*` |
| Writer profile names with a third-party mark (docs 04, 07) | `Legacy196Text`, `RemasteredText` |
| `Effect` (two meanings) | `CommandEffect` and `AgentEffect` |
| "harness" (both the workflow runtime and the game's `--harness` link) | `plotroom-workflow-runtime` and `plotroom-gamelink` |

Profile ids `Cwa199`, `Cwr` and `Ce` are owner-decided data values (D003), not product or crate names. A CI grep refuses third-party
marks and island names in crate, module, format, sidecar and generated-header names ([testing-strategy.md §14](testing-strategy.md)).

## 16. Open questions

1. Whether the kernel split (`plotroom-doc` below the models, `plotroom-project` above them) holds once cross-document commands grow;
   the alternative is a single core crate with internal modules.
2. The final landing milestones, set by the roadmap.
3. Whether `hf-hub` can route through `plotroom-net` (SP-14). Doc 46 §1.3 downloaded pinned files with three plain HTTPS calls (the
   model API for the commit, the file tree for size and SHA-256, `resolve/<commit>/<file>` with range resume), so `plotroom-net` can
   implement the owner's pinned-download rule without `hf-hub` if the spike fails (proposal).
4. Whether `plotroom-briefing`'s CST should share `plotroom-config`'s green-tree implementation.
5. The crate names of the v1.x director and atmosphere work (DG037; the design round's names table, OWQ-08 (a)).

## Verification notes

### Owner answers folded (2026-09-27)

- Folded from `OWNER-QUESTIONS.md` (answers of 2026-09-27) and the owner's runtime decision (D022 amendment note): §9
  (`plotroom-campaign-flow`, OWQ-13), §10 (`plotroom-model-manager`, `plotroom-mcp`), §11 (`plotroom-cli`, OWQ-14), §12, §14
  (OWQ-01, OWQ-03, OWQ-04), §16. No crate, layer or landing milestone changed.
