# CODE-INDEX

Source navigation index for **Plotroom — Mission & Campaign Editor for Arma: Cold War Assault / Operation Flashpoint**, required by
`AGENTS.md` ("Source Code Navigation Index"). It tells a human or an LLM agent where things are, and where they will be.

> **Status (2026-09-29): the first product crate, `plotroom-config` (the SP-09 lossless config CST), has landed; the rest of the
> product is still planned.** The repository holds design documents, two skills, a prompt pack and
> research tools; since 2026-09-28 one of them, `tools/rust-weak-models`, is a standalone Cargo workspace of research crates (doc
> 64's experiment), not product code. The root Cargo workspace exists since 2026-09-28 (M0 skeleton, §2 and §3): the tooling crate
> `xtask` and the dev crate `plotroom-testkit` have landed, with CI and a `fuzz/` skeleton; since 2026-09-29 the L1 crate
> `plotroom-config` has too (§4.1, and the verification note "SP-09 `plotroom-config`"). Every other crate, and every module and
> newtype below, is **planned**: it comes from the proposal in
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
| Measure a local or cloud model (free OpenRouter, Groq and Cloudflare Workers AI models included), the harness's uplift, reasoning scaffolds, a harness preset, a small-to-large cascade, or model cost | [`tools/local-qual/`](tools/local-qual/README.md), [`tools/cost-model/`](tools/cost-model/cost_model.py) |
| Simulate free-tier rate limits and upstream 429s over a user day | [`tools/quota-sim/`](tools/quota-sim/README.md) |
| Re-run doc 64's experiment (PLAIN vs GUIDED Rust APIs for small models: harness, tasks, pilot driver, analyses) | [`tools/rust-weak-models/`](tools/rust-weak-models/README.md) |

## 2. Repository layout (current)

```text
.
├── AGENTS.md              rules for contributors and coding agents; product invariants (read first)
├── CLAUDE.md              one-line include of AGENTS.md for an agent tool
├── CODE-INDEX.md          this file
├── README.md              what Plotroom is, what you need, licence, disclaimer
├── LICENSE                GPL-3.0-or-later
├── NOTICE                 project copyright; Bohemia's section 7 notice and terms verbatim (they apply because files marked
│                          `Derived-From:` translate CWR/CWR-CE code); trademark disclaimer (doc 02 §10.1; D001 item 2)
├── .gitignore             /private/, /target/, tool outputs, Python caches
├── Cargo.toml             root Cargo workspace (M0): members crates/* and xtask; excludes tools/rust-weak-models, fuzz and
│                          xtask/fixtures; shared package fields, workspace lints (§3), release profile; Cargo.lock beside it
├── clippy.toml            test allowances; capability bans of crate-map §2.3 (files, processes, network, environment)
├── deny.toml              cargo-deny: advisories, GPL-3.0-compatible licence allowlist, bans, crates.io-only sources
├── .github/workflows/     ci.yml (fmt, clippy, tests on Windows, Ubuntu, macOS; trybuild UI job; xtask; cargo-deny),
│                          fuzz.yml (nightly)
├── crates/                product and dev crates, one folder per crate, named as in the crate map
│   ├── plotroom-config/   L1 (§4.1): lossless config CST (SP-09). src/: lib, error, limits, text (offset newtypes), scalar
│   │                      (engine typing), cst/{mod, kinds, green, builder, preproc (preprocessor view), stream, words,
│   │                      parser, cursor, entries (the game's view), issues (lint_syntax), lexeme, patch}, emit/{mod,
│   │                      float} (canonical writer); unit tests in cst/tests*.rs and emit/tests_writer_rules.rs; tests/
│   │                      (prop_identity, prop_patch, support/, upstream_{parsing,realworld,save,regressions,fixtures},
│   │                      fixtures/upstream-config/, ui.rs + ui/ trybuild cases behind the `ui-tests` feature)
│   └── plotroom-testkit/  dev (§4.4): fixture roots, BlobBuilder, VirtualClock, SeededIds; src/{lib,error,fixtures,blob,
│                          clock,ids}.rs
├── xtask/                 tooling (§4.4): layers.toml (the declared layer table); src/ (main, cli, error, metadata,
│                          layers/{table,check,tests,tests_table}.rs, hygiene/{mod,tests}.rs, sys.rs: its only I/O);
│                          tests/live_workspace.rs (both checks on the real workspace); fixtures/cargo-deny/ (licence gate)
├── fuzz/                  separate cargo-fuzz workspace: fuzz_targets/config_parse.rs (plotroom-config parse, round trip and
│                          patch checks), Cargo.lock
├── docs/
│   ├── README.md          entry point: organisation, reading orders, topic index, research index
│   ├── research/          research docs from 01 (status of each in docs/README.md §5; designs proposal-only unless adopted)
│   │   └── data/          10 CSVs (corpus, catalog sizes, costs, command risk, local qualification, runtime and quant
│   │                      comparison, small-model and cloud candidates)
│   ├── design-gap-requests/  DG001–DG060 and the index README (lifecycle, template)
│   ├── decisions/         D001–D043, OWNER-QUESTIONS.md (OWQ-01–OWQ-23, all answered 2026-09-27), index README
│   ├── architecture/      README (thesis, layers, conflicts, Appendix A) + crate-map, core-document-model,
│   │                      commands-undo-history, validation-and-lints, agent-runtime, ui-shell, game-integration,
│   │                      extensibility, testing-strategy
│   ├── roadmap.md         milestones at a glance, lanes, definition of done, deferrals, risks
│   ├── roadmap/           m0-m3, m4-v1, v1x-and-v2, spikes-and-probes, integration-owners
│   ├── upstream/          engine-requests register: README, engine-requests.md, engine-requests.csv (ER-001–ER-113)
│   └── porting/           upstream-test-map.csv (642 upstream test rows; `target_module` column since SP-09)
├── skills/                product skills in the standard SKILL.md format (D019)
│   ├── mission-primer/    SKILL.md + references/ (idioms, file-skeletons, sources)
│   └── standing-orders/   SKILL.md + references/ (32 concept entries; formerly skills/field-manual/)
├── prompts/
│   └── design-sensibility/  v0.2 taste pack: core.md, lenses/ (8), rubric.md, code-owned-principles.md, EVALUATION.md
├── tools/                 research tools, not product code: Python standard library, plus one standalone Cargo workspace
│   ├── local-qual/        README.md (usage, suites, metrics, tests, verification); run.py (runner) with run_cli.py (flags,
│   │                      refusals), run_records.py and run_preset.py (--preset: a harness preset's knobs to flags);
│   │                      presets/ (harness-preset schema, draft presets, lint.py checker; D048, doc 55 §3);
│   │                      prompts.py; backends.py (Ollama and llama-server clients);
│   │                      cloud_backend.py, cloud_reply.py, cloud_guard.py, cloud_run.py, cloud_flags.py, budget.py
│   │                      (OpenAI-compatible endpoints under a hard budget); free_mode.py, free_key.py, rate_gate.py
│   │                      (--free-only: OpenRouter :free models at zero spend); providers.py, provider_gate.py,
│   │                      provider_reply.py, provider_backend.py (--provider groq|cloudflare: their free tiers at zero
│   │                      spend); key_status.py,
│   │                      provider_status.py (--key-status: the key's record at no quota);
│   │                      logprob_pick.py, logprob_dist.py (--pick-mode logprob); scaffolds.py,
│   │                      scaffold_algos.py, scaffold_run.py, scaffold_stats.py, control_suite.py (reasoning scaffolds,
│   │                      doc 59); score.py, score_checks.py, grade_open.py, uplift.py, cascade.py, cascade_numbers.py;
│   │                      cloud/ (owner runbook, Windows DPAPI key scripts per provider, the dated Groq free-plan and
│   │                      Cloudflare neuron tables); suites/ (pick, pick-hard, fill, explain,
│   │                      text, knowledge .json + the open-arm sidecar); tests/ (unittest suite: mock servers, fixtures,
│   │                      goldens; run python -m unittest discover -s tools/local-qual/tests); results/ is git-ignored
│   ├── cost-model/        cost_model.py (its JSON output is git-ignored; feeds docs/research/data/cost-model.csv)
│   ├── quota-sim/         README.md, quota_sim.py (day replay, strategies S0-S6, CLI), quota_pools.py (pools, congestion,
│   │                      endpoints), quota_report.py (metrics, grid, Markdown), test_quota_sim.py, data/ (workload.json,
│   │                      limits.json: inputs); results go to a path the caller names
│   └── rust-weak-models/  doc 64's experiment, a standalone Cargo workspace (never a member of a root workspace, §3):
│                          README.md; crates/ (mb-spec, mb-core, mb-plain, mb-guided, mb-oracle); tasks/ (T01-T30) and
│                          pilot/ (P01-P04) sources; prompts/; design.json (pre-registration draft); runner.py with rwm/
│                          (harness, cargo runner, listing, static scan, loopback model client, hygiene checks);
│                          test_rwm.py and test_rwm_guards.py; clippy.toml (empty) and rustfmt.toml (formatting off), pinned
│                          so no root config reaches the stimuli; power_sim.py; diag-probe/;
│                          live/ (llama-server pilot driver, arms.json); analysis/ (pilot analyses); the generated task
│                          crates, Cargo.lock, target/ and results/ are git-ignored (python runner.py scaffold rebuilds them)
└── private/               git-ignored local notes; never cite, link or copy from it
```

**Verification commands** (`AGENTS.md`, "Local Repo-Specific Rules"), at the repository root:
`cargo test --workspace --locked`, `cargo clippy --workspace --all-targets --locked -- -D warnings`, `cargo fmt --all --check`,
`cargo check`. Agents never run `cargo build` or `cargo run` unless the user asks; `cargo test -p xtask` already runs the layer
and naming checks on the real workspace (`xtask/tests/live_workspace.rs`), and CI runs them as `cargo run -p xtask -- layers` and
`cargo run -p xtask -- hygiene`. `tools/rust-weak-models/Cargo.toml` is the research workspace's own manifest, verified with the
commands in its README; `fuzz/` builds only with `cargo +nightly fuzz` (nightly CI).

## 3. Workspace rules (from the architecture; enforced since the M0 skeleton, 2026-09-28)

- **Layers L0–L8**, edges pointing downward only; allowed same-layer edges are listed in [crate-map §2.2](docs/architecture/crate-map.md)
  and checked by `xtask layers` against `cargo metadata`. The table is `xtask/layers.toml`: it lists every planned crate (roles
  `L0`–`L8`, `dev`, `tooling`), the §2.2 edges crate by crate, the forbidden edges to `plotroom-session` and the confined third-party
  crates (egui, HTTP clients, WebAssembly runtimes, rmcp, wgpu). A workspace member missing from it fails; dev crates are
  dev-dependencies only; nothing depends on `xtask`.
- **Side effects live at the edge** ([crate-map §2.3](docs/architecture/crate-map.md)): file writes only in `plotroom-io`; child
  processes only in `plotroom-preview` and `plotroom-model-manager`; outbound HTTP only in `plotroom-net`; loopback sockets in
  `plotroom-gamelink`, `plotroom-mcp` and `plotroom-net`; egui only in `plotroom-ui` and `plotroom-app`; wgpu only in `plotroom-gpu`;
  wasmtime and rmcp only in `plotroom-plugin-host` (rmcp also `plotroom-mcp`); environment variables only in the binaries and tests;
  `UserIntent` minted only in `plotroom-session::intent`. The root `clippy.toml` bans `std::fs`, `Path` file-system queries,
  `std::process::Command`, `std::net` sockets and `std::env::var`/`var_os`/`vars` everywhere, each with an instruction as `reason`.
  A crate §2.3 allows a capability silences only the confining module or function with
  `#[expect(clippy::disallowed_methods, reason = "…")]` (today `xtask/src/sys.rs` and `plotroom_testkit::OptInRoot::read`),
  never with a crate-level `clippy.toml`: clippy does not merge those files, and one lint covers every ban.
- **Workspace lints** (`AGENTS.md`, enforced mechanically; root `Cargo.toml`): `unsafe_code = "forbid"`, `unused_must_use` and
  `deprecated` denied; clippy `indexing_slicing`, `string_slice`, `unwrap_used`, `expect_used`, `panic`, `unreachable`, `todo`,
  `unimplemented`, `let_underscore_must_use`, `allow_attributes_without_reason`, and `disallowed_methods`/`disallowed_types` (so the
  capability bans' reasons reach an errors-only feed, doc 62 §3.1) denied; tests get clippy's unwrap, expect, indexing and panic
  allowances. Format crates add `#![deny(clippy::arithmetic_side_effects)]` in `lib.rs` (Cargo cannot combine
  `lints.workspace = true` with per-crate lints). Release profile `lto = true`, `codegen-units = 1`.
- **One `Error` enum per crate** in `src/error.rs`; format crates keep a thin `src/read.rs` over `plotroom-bytes`' cursor.
- **Directory layout** (decided by the M0 skeleton): product and dev crates in `crates/<crate-name>/`; `xtask/` and `fuzz/` at the
  root (the usual places for both tools). Every crate inherits `version`, `edition`, `rust-version` and `license` from
  `[workspace.package]` and sets `[lints] workspace = true`.
- **Toolchain and formatting.** No root `rust-toolchain.toml`, `.cargo/config.toml` or `rustfmt.toml`. The first two would also
  reach `tools/rust-weak-models` (below); a root `clippy.toml` or `rustfmt.toml` no longer does, because that folder pins its own. `rust-version = "1.98.1"` in the root `Cargo.toml` and `RUST_TOOLCHAIN` in
  `.github/workflows/ci.yml` pin the compiler (bump both together); formatting is rustfmt's default style.
- **Research workspaces stay out.** `tools/rust-weak-models` is a standalone Cargo workspace (doc 64). The root `Cargo.toml` must
  carry `exclude = ["tools/rust-weak-models"]` and never name a path below it as a member: with cargo 1.98.1 a glob that matches the
  folder fails loudly, but a member path that reaches a crate inside it is adopted silently (root lock file, profiles and lints),
  and an explicit path wins over `exclude`. A root `rust-toolchain.toml` or `.cargo/config.toml` reaches it too.
  `tools/rust-weak-models/test_rwm.py` (`EnclosingWorkspace`) fails, naming the fix, when any of these appears, and its
  `python -m rwm.hygiene` also reports a `clippy.toml` or `rustfmt.toml` above it that its own pinned files would not shadow.

## 4. Crate map (planned unless the Path cell is filled)

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
| `plotroom-config` | L1 | Lossless green-tree CST, resolved view with inheritance, raP read (v2–4) and write (v4), `ConfigOrigin`. Landed (SP-09): the CST (`parse`, `render`), the game's view (`entries`, `find`), `lint_syntax`, span patches with checked lexemes, the canonical writer (`write_entries`, `WriterProfile`); resolved view, raP and `ConfigOrigin` still planned | M1 (CST spike in M0) | — | `crates/plotroom-config/` |
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
| `xtask` | tooling | `layers` and `hygiene` (landed); `codes`, `catalog`, `skills`, `provenance`, `defs` (planned) | M0 | DG005 (for `codes`) | `xtask/` |
| `plotroom-testkit` | dev | Landed: fixture roots (`fixture_root!`, `OptInRoot`), `BlobBuilder`, `VirtualClock`, `SeededIds`. Planned: `EditorHarness`, synthetic SQM, PBO, WRP and raP builders, synthetic island and catalog, faux model, cassettes | M0 skeleton | — | `crates/plotroom-testkit/` |
| `plotroom-script-oracle` | dev | Transliterated evaluator used only as a test oracle (doc 23 §13.2) | M2 (roadmap) | — | — |
| `fuzz/` | dev | Separate nightly cargo-fuzz workspace (`plotroom-fuzz`); target `config_parse` (the `plotroom-config` text parser: round trip, lint, patches; mirrors CWR's `fuzz_paramfile.cpp`) | M0 skeleton | — | `fuzz/` |

Later crates: `plotroom-plugin-sdk` and `plotroom-plugin-testkit` (v1.x; GPL-3.0-or-later for now, D031); the cutscene-director and
atmosphere crates (v1.x; names from the design round's names table, DG037 and D034).

## 5. Newtypes

`AGENTS.md` requires this table. Every newtype derives `Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash` where its inner type
allows, provides `from_raw` and `to_raw`, and implements `Display` in a human-readable form; `plotroom-ids` provides the macro. The rows
below are **planned** (named in `docs/architecture/`); "not set" means the architecture does not fix the inner type yet. A row flips to
**landed** with its real module path when the type is created.

**Landed newtypes** (moved here from the planned table, or added, by the change set that creates each type):

| Type | Inner | Crate / module | Purpose | Landed |
| --- | --- | --- | --- | --- |
| `TextOffset` | `u32` | `plotroom-config::text` | A byte position in a config text; computed by cursors from green-tree widths, never stored in the tree | 2026-09-29 (SP-09) |
| `TextWidth` | `u32` | `plotroom-config::text` | A byte length (token, node, inserted patch text); kept apart from `TextOffset` so a width is never used as a position | 2026-09-29 (SP-09) |

Not newtypes, but guard types of the same change set (private fields, checked constructors, trybuild cases in
`crates/plotroom-config/tests/ui/`): `TextSpan` (`start <= end`), `EntryValueLexeme` and `ElementValueLexeme` (bytes proven to
read back as one value), `EntryValueRef` and `ElementValueRef` (bound to one tree revision), `Patched` and `ByteEdit`. The M0
skeleton (`xtask`, `plotroom-testkit`) defines no newtype; `SeededIds` mints raw `u128` values until `plotroom-ids` (M1) brings
`EntityId` and its siblings.

**Planned newtypes:**

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
2. **One product crate so far.** The Rust in the repository is the M0 skeleton (`xtask/`, `crates/plotroom-testkit/`, `fuzz/`:
   tooling and test support), `crates/plotroom-config/` (the SP-09 config CST, the first product crate), and
   `tools/rust-weak-models/`, doc 64's research experiment, whose crates are stimuli, not product code. Questions about "how the
   product code does X" for anything else are answered by `docs/architecture/`, marked proposal.
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
   ids `Cwa199`, `Cwr`, `Ce` are data values, D003); no private project names anywhere; nothing from `/private/`. `xtask hygiene`
   enforces the names part from one list, `xtask::hygiene::MARKS`.
8. **Opt-in local tests** use `PLOTROOM_CORPUS_DIR` and `PLOTROOM_GAME_DIR` (planned; [testing-strategy §15](docs/architecture/testing-strategy.md));
   CI never depends on a game install or proprietary data.
9. **Tools** in `tools/` are research harnesses in Python's standard library; `tools/rust-weak-models` adds a standalone research
   Cargo workspace. Their raw outputs are git-ignored; only derived CSVs under `docs/research/data/` are committed.
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
  `backends.py` and the six suite files, including `pick-hard.json` (`results/` and Python caches are git-ignored).
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

- §1 and §2 list the tool's current files. The cloud backend of doc 48 (with its free-only mode and the Windows key scripts),
  `--pick-mode logprob` and `cascade.py` from doc 53, and the scaffold arms (doc 59) were merged into `tools/local-qual`. The
  five modules over the ~600-line ceiling (`run.py`, `score.py`, `logprob_pick.py`, `cascade.py`, `scaffolds.py`) were split
  into six new ones with every name re-exported (`run_cli.py`, `run_records.py`, `score_checks.py`, `logprob_dist.py`,
  `cascade_numbers.py`, `scaffold_algos.py`).
- The tool's tests live in `tools/local-qual/tests/` and run with the standard library's `unittest`; checks that compared the
  tool with a copy of an earlier version now compare with golden files frozen from that version (`tests/golden/`).
- Fixed while landing, test first: the budget booked OpenRouter's non-BYOK `upstream_inference_cost` on top of `cost` (doc 54
  §4.2), and `run.py` gained `--output`, an alias of `--out` that `cloud/run-cloud.ps1` can pass through `powershell -File`.
- No crate, module boundary of the planned workspace or newtype changed.

### `tools/local-qual`: harness presets (2026-09-28)

- `run.py --preset FILE` (D048 Consequences; doc 55 §3): `run_preset.py` turns a data-only harness preset into run.py's own
  flags, refuses what run.py cannot honour, and records the preset's id, version and hashes in every record. `presets/` holds
  the draft-2 schema, the 0.1.0 draft presets (untested hypotheses) and `lint.py`, the ported draft checker. Tests p01–p20 in
  `tests/test_presets.py`, `test_presets_plan.py` and `test_presets_run.py`. §2 lists the new files.
- No crate, module boundary of the planned workspace or newtype changed.

### `tools/local-qual`: review of the merged tool (2026-09-28)

- An adversarial review of the merged tool (paid and free-only cloud runs, logprob mode, scaffold arms, presets) fixed four gaps,
  each with a check written first: `--extra-body` fields billed at rates the price flags do not name (`service_tier`,
  `modalities`, `audio`); a JSON `--reasoning` thinking budget the worst case did not count (`5000.0`, `"5000"`, `true`); a key
  holding a character JSON escapes, which the record scrub could not find; and `--resume` without `--preset` into a preset run's
  records under one `--label`. `--repeat-penalty` on OpenRouter now warns at the start (friction register FR-C-032). New cases:
  t63–t66 in `tests/test_cloud_review.py` and p21 in `tests/test_presets_run.py`. The "pending patch" wording of the doc 46–48
  entry above is removed, since that patch has landed.
- No crate, module boundary of the planned workspace or newtype changed.

### `tools/local-qual`: `--key-status` (2026-09-28)

- `run.py --key-status` (new `key_status.py`) reads OpenRouter's `GET /key` once and prints the key's non-secret fields, at
  no quota: no model request, no ledger, no lock. `cloud/run-cloud.ps1` accepts it without `--free-only`. The runbook
  (`tools/local-qual/cloud/README.md`) gains step 5 for it (later steps renumbered 6–10) and an HTTP 429 section. Tests
  t67–t73 in `tests/test_key_status.py` (t72–t73 from the review: redirect targets, record fields and `\u`-escaped
  copies never show a secret; the limit that applies is named) and step 15 of `tests/dpapi_round_trip.ps1` (t53).
  §2 lists the new file. The same review fixed two older paths: a 300 with an unparsable Location crashed a run
  (`cloud_guard.redirect_host`, t74 in `tests/test_cloud_guards.py`), and a label planted in the key record's date
  fields reached a free run's console and records (`free_key.key_summary`, t75 in `tests/test_free_mode_review.py`).
- No crate, module boundary of the planned workspace or newtype changed.

### `tools/local-qual`: Groq and Cloudflare Workers AI (`--provider`, 2026-09-28)

- `run.py --provider groq|cloudflare` (D058 item 3) runs the suites on Groq's free plan or on Cloudflare Workers AI's daily free
  allocation, at zero spend: `providers.py` (presets, flags, offline checks, D047's suite rule), `provider_gate.py` (Groq's
  requests and tokens per minute and per 24 hours with its `x-ratelimit-*` headers and free-plan check; Cloudflare's neurons per
  UTC day from the dated `cloud/cloudflare-neurons.json`; its parsers in `provider_reply.py`), `provider_backend.py` (each
  provider's request shape and redaction, the account id included) and `provider_status.py` (`--key-status` for both). `cloud/run-cloud.ps1 --provider <name>` decrypts
  that provider's key (and Cloudflare's account id) into run.py's environment only; `cloud/set-provider-key.ps1` and
  `remove-provider-key.ps1` call the per-provider store and remove scripts. To stay under the ~600-line ceiling,
  `cloud_backend.py`'s reply helpers moved to `cloud_reply.py` and `cloud_run.py`'s flags to `cloud_flags.py`, every name
  re-exported. Tests g01–g08, w01–w08 and k01–k05 (`tests/test_provider_*.py`), steps 16–22 of `tests/dpapi_round_trip.ps1`
  (t53) and a third tracing mode in t58. §2 lists the new files.
- No crate, module boundary of the planned workspace or newtype changed.

### `tools/rust-weak-models` (2026-09-28)

- Doc 64's experiment harness moved into the repository from a scratch folder (friction register FR-C-013): the five research
  crates, the 34 tasks' hand-written sources, prompts, the pre-registration draft, the runner and its `rwm/` package, the tests,
  the power simulation, the diagnostic probes, the live pilot driver and the pilot analyses. Generated task crates, `Cargo.lock`,
  `target/` and `results/` are git-ignored. §1, §2, §3 and §6 now name it; the status line and tip 2 say "no product code" instead
  of "no code".
- It is a standalone Cargo workspace; §3 records the rule that keeps it out of the future root workspace, from a probe with cargo
  1.98.1 on a nested copy. Its crates are not planned product crates: §4 and §5 do not list them (the `GUIDED` ids are experiment
  stimuli, not project newtypes).
- Evidence and the changes made in the move are in its README. No crate, module boundary of the planned workspace or newtype changed.

### M0 workspace skeleton (2026-09-28)

- The root Cargo workspace landed (roadmap M0 "Workspace", D058 item 1): `Cargo.toml` (resolver 3, members `crates/*` and `xtask`,
  excludes `tools/rust-weak-models`, `fuzz` and `xtask/fixtures`), `Cargo.lock`, `clippy.toml`, `deny.toml`,
  `.github/workflows/ci.yml` and `fuzz.yml`, and the crates `xtask` (tooling) and `plotroom-testkit` (dev), plus the `fuzz/`
  skeleton. §2, §3, §4.4 (Path cells), §5 (an empty landed-newtype table) and tip 2 follow; the status line names them.
- Evidence: `cargo fmt --all --check`, `cargo clippy --workspace --all-targets --locked -- -D warnings` and
  `cargo test --workspace --locked` pass on Windows with rustc 1.98.1 (testkit 24 unit tests and 2 doctests; xtask 63 unit tests,
  2 live-workspace tests and 1 doctest), after a recorded red run against stub bodies. The committed negative tests of M0 exit
  evidence item 2 are `planted_l6_edge_to_session_fails` (xtask `layers/tests.rs`), `planted_mark_in_crate_name_fails`
  (`hygiene/tests.rs`) and the CI `deny` job's planted GPL-2.0-only fixture with its MIT control. A manual run that planted a
  dev-dependency on `xtask` and a fixture file named after an island made both live-workspace tests fail, then was reverted.
- `tools/rust-weak-models/test_rwm.py`'s `EnclosingWorkspace` still passes with the new root manifest, and `cargo metadata` from its
  crates still reports `tools/rust-weak-models` as their workspace root.
- Not verified locally: cargo-deny (the installed 0.14.3 predates the `[graph]` table and panics on cargo 1.98's metadata; CI runs the
  current release through the action; every locked dependency's declared licence was checked against the allowlist by hand), the
  workflow files (first CI run), and fuzzing itself (needs nightly and cargo-fuzz; the target passes `cargo check` on stable).
- Friction: adds FR-C-033 (root-level toolchain, cargo and rustfmt config is off-limits while the research workspace sits below the
  root) and FR-C-034 (an older local cargo-deny fails without naming the version it needs) to `docs/friction/register.csv`.

### SP-09 `plotroom-config` (2026-09-29)

- The first product crate landed: `crates/plotroom-config` (layer L1, std only; dev-dependencies proptest 1.11 and
  trybuild 1.0, both MIT OR Apache-2.0). §2, §4.1 (Path cell), §4.4 (`fuzz/`), §5 (landed newtypes `TextOffset` and
  `TextWidth`, and the guard types) and tip 2 follow; the status line names it. Design choices are in the crate's module docs:
  an in-house green tree over raw bytes (core-document-model §13 item 4), a port of the engine's reader over a preprocessed
  view, never failing on syntax (only the caps), issues derived by `lint_syntax`, patches verified by re-parsing.
- Files translated from CWR/CWR-CE carry `Derived-From:` headers; `NOTICE` (new, root) reproduces Bohemia's notice and
  section 7 terms verbatim; the generated-content permission waits for its wording (DG060). The patch API's witness surface
  is DG059. The porting CSV gained a `target_module` column and six `#fragment` rows (642 rows); `.github/workflows/ci.yml`
  gained the `ui` job; the engine-requests register gained ER-110 to ER-113; the friction register FR-C-035 and FR-C-036.
- Evidence: red then green with `cargo test -p plotroom-config` (key bodies stubbed for the red run), then
  `cargo fmt --all --check`, `cargo clippy --workspace --all-targets --locked -- -D warnings` and
  `cargo test --workspace --locked` pass on Windows with rustc 1.98.1; `cargo test -p plotroom-config --features ui-tests
  --test ui` passes (9 trybuild cases); `cargo check --manifest-path fuzz/Cargo.toml --locked` passes (fuzzing itself needs
  nightly and was not run).
