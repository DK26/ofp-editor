# Plotroom architecture

> **Status:** proposal (architecture baseline 2026-09-27). This folder is the implementation architecture for Plotroom, Mission &
> Campaign Editor for Arma: Cold War Assault / Operation Flashpoint. Nothing in it is decided unless it restates `AGENTS.md`, a
> decision record (`docs/decisions/Dnnn`), a decided design-gap request (DG002, DG013, DG014, DG028, DG029, DG030, DG033 items
> 3–4) or an owner answer in [`OWNER-QUESTIONS.md`](../decisions/OWNER-QUESTIONS.md) (OWQ-01 to OWQ-23, all answered 2026-09-27 and
> stated as records D031–D043). Everything else is a proposal that the design round adopts, amends or rejects. Type sketches are not
> compiled and names are not final.

## 1. What this folder is

- **Precedence.** `AGENTS.md` wins over everything; accepted decision records win over this folder; this folder wins over the
  proposals in `docs/research/` where it resolves them, and says so. A contradiction this folder cannot resolve is listed as a
  design-gap candidate (§8) and the dependent work stays `proposal-only` (`AGENTS.md`, Design Authority).
- **Evidence.** Research docs 01–45 are the evidence (cited as "doc NN §x"), with docs 46–48 (local runtime, small-model landscape,
  cloud providers) for [agent-runtime.md](agent-runtime.md) §3 and §13; decision records D001–D043 and owner questions OWQ-01 to
  OWQ-23 (answered 2026-09-27) are in [`docs/decisions/`](../decisions/README.md); design-gap requests DG001–DG038 are in
  [`docs/design-gap-requests/`](../design-gap-requests/README.md); engine requests ER-001 to ER-109 are in
  [`docs/upstream/`](../upstream/README.md).
- **How it was made.** Three architecture proposals were written from different angles (core document model first, agent-native
  first, fidelity and delivery first) and scored by three judges (typed invariants and maintainability; the AI harness; delivery and
  community value). This baseline takes the **core-model-first** proposal as its spine (highest combined score) and grafts the best
  ideas of the other two; every conflict the judges raised is resolved in §7. The proposals and the judges' reports were working
  drafts and are not kept in the repository: this folder, §7 in particular, is their record.

## 2. Thesis

Plotroom is **a document engine with several clients.** The engine is a lossless, identity-stable, undoable, validated project model:
a concrete syntax tree with a typed lens, Plotroom ids in a sidecar, ops with inverses, pure validators and pure compilers, behind one
command registry. The egui shell, the classic renderer, Wilco, the AI-off workflows, plugins, the outbound MCP server, the headless
CLI, Drill lessons and Preview staging are all clients: they read immutable snapshots and write only by submitting typed commands.
"If the GUI can't do it, the LLM can't do it" (doc 17 §5; doc 21 §1.3) holds in its strict form: **nobody changes a document except
through an admitted `EditorCommand`.**

Three things are true at once, and the layering serves all three:

1. **Faithful first.** The first release that earns the community's trust is the original editor, standalone, with undo, non-blocking
   lints and one-click Preview (doc 09; D004 item 1). AI and campaigns arrive as layers over seams built on day one, never by
   re-architecture.
2. **The harness carries the weight.** The workflow runtime, decision journal, ledger and knowledge store are editor infrastructure
   proven by AI-off features before any model call exists; a model is one more kind of recorded step (D009; D025).
3. **Correct by construction.** Output lowers per target profile in the conservative subset, with a computed "Requires" badge (D003);
   engine gaps become engine requests, never silent requirements (D012).

## 3. Principles

| # | Principle | Where |
| --- | --- | --- |
| P1 | **One mutation path, enforced by the compiler**: trees in a `Guarded<T>` with no `DerefMut`; `LiveTx` exists only inside an open undo group; loading records nothing | [core §5](core-document-model.md) |
| P2 | **Lossless by default**: `render(parse(b)) == b`; edits are patches; normalisation only by an explicit command | [core §3–§4](core-document-model.md) |
| P3 | **Plan → admit → commit for every command**, the user's included; rejections never enter history; applied diff equals planned diff | [commands §4](commands-undo-history.md) |
| P4 | **Identity is ours** (128-bit ids in the sidecar); file ids and script names are never identity | [core §7](core-document-model.md) |
| P5 | **Code owns facts and validity**: validators, compilers and generators are pure functions of snapshots, fact packs and seeds | [validation](validation-and-lints.md); [agent §6](agent-runtime.md) |
| P6 | **Provenance everywhere; human work wins** by construction (automatic field ownership, consent tokens, one three-way merge) | [core §8](core-document-model.md) |
| P7 | **Determinism is injected**: `Clock`, `IdSource`, seeds; concurrency changes speed, never results | [ui-shell §10](ui-shell.md) |
| P8 | **Side effects live at the edge**: files, processes, network and sandboxes in a short allowlist of L7 crates | [crate-map §2.3](crate-map.md) |
| P9 | **One registry per vocabulary, many surfaces**: commands, codes, concepts, field descriptors, definitions | [commands §3](commands-undo-history.md); [validation §5](validation-and-lints.md) |
| P10 | **Honest about the engine, per profile**: conservative glue, computed badge, opt-in capabilities; realism is advice, never a wall | [validation §3, §8](validation-and-lints.md) |
| P11 | **`AGENTS.md` enforced mechanically**: `forbid(unsafe_code)`, deny-level clippy lints, `xtask layers`, cargo-deny, disallowed methods | [crate-map §2.4–§2.5](crate-map.md) |
| P12 | **A weak model can succeed** because the core does the hard parts; every AI-made element is an ordinary element with a decision record | [agent](agent-runtime.md) |
| P13 | **Consent is a type**: only `UserIntent` minted from real input starts model workflows, approves plans, accepts egress, launches Preview | [commands §4.4](commands-undo-history.md) |
| P14 | **Glass box**: every generated element is visible in its natural view, inspectable to the decision, editable natively (D010) | [ui-shell §7](ui-shell.md) |
| P15 | **Fun, and the user directs** (D009 item 5): interactive choices (premise cards, few weighty Picks with safe defaults, variant and assumption chips), a playable skeleton early and one-click Preview, instead of long silent runs; check-ins follow autonomy (D024) | [agent §10–§11](agent-runtime.md); [ui-shell §6](ui-shell.md) |

## 4. Layers

```text
 L8 presentation  plotroom-app (binary `plotroom`)   plotroom-cli   plotroom-ui (egui panels)
                  plotroom-ui-classic  plotroom-map2d  plotroom-draw2d  plotroom-fonts  plotroom-gpu (only wgpu user)
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 L7 edge          plotroom-io (only file writer)  plotroom-net (only HTTP client, EgressGrant)  plotroom-provider-http
                  plotroom-model-manager  plotroom-preview  plotroom-gamelink  plotroom-mcp  plotroom-plugin-host  -registry
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 L6 harness       plotroom-provider  plotroom-workflow  plotroom-decide  plotroom-workflow-runtime  plotroom-campaign-flow
 (no I/O)         plotroom-wilco  plotroom-evals                      → reach the document only through the command bus
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 L5 engines       plotroom-session (assembly: Session::step, CoreBuilder, UserIntent)
                  plotroom-lower  plotroom-template  plotroom-teller  plotroom-knowledge  plotroom-drill  plotroom-generate
                  plotroom-campaign-compile  plotroom-campaign-sim  plotroom-export  plotroom-packs
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 L4 core          plotroom-project (store, snapshots, identity)  plotroom-commands (registry, admission)
                  plotroom-validate (rules, readiness)  plotroom-view (selection, dialogs, map state machine)
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 L3 models        plotroom-doc (kernel: ops, groups, history, provenance)  plotroom-mission  plotroom-sidecar
                  plotroom-modules  plotroom-cxl  plotroom-campaign  plotroom-cine
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 L2 world facts   plotroom-vfs  plotroom-install  plotroom-catalog  plotroom-terrain       (pure over ReadOnlySource)
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 L1 formats       plotroom-pbo  -preproc  -config  -stringtable  -briefing  -script  -script-catalog  -wrp  -p3d  -paa
                  -fxy  -rsc  -audio                                   (pure &[u8] parsers, one Error enum each)
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 L0 foundation    plotroom-bytes  plotroom-ids  plotroom-encoding  plotroom-profile  plotroom-diag
```

Data flow of one edit, from any client:

```text
 gesture / dialog OK / Wilco turn / workflow step / plugin batch / MCP call
        │  Proposal<CommandBatch> { origin, reads, writes, trust, intent? }
        ▼
 command bus ──► Session::step (UI thread) ──► plan on Scratch ──► admit (check families) ──► commit hooks
                                                                                              │
        ┌─────────────────────────────────────────────────────────────────────────────────────┘
        ▼
 apply on LiveTx in one undo group ──► history + CommitId ──► publish Arc<Snapshot> ──► events
        │                                                          │
        ▼                                                          ▼
 crash op journal (app data)                     workers: validation, draw lists, Teller index, Path Explorer
                                                 runtime: next workflow step; Preview staging; saves (I/O thread)
```

## 5. How to read this folder

| File | Answers | Main research | Main decisions |
| --- | --- | --- | --- |
| [crate-map.md](crate-map.md) | Which crates exist, what each owns, who may depend on whom, which crates may touch files, processes and the network, which upstream tests each ports | 04, 06, 07, 08, 20, 21, 22, 23, 38, 45 | D001, D002, D013, D016, D017, D021 |
| [core-document-model.md](core-document-model.md) | What a project is: documents, CST and lens, ops, snapshots, identity, provenance, generated regions, authoring models, the `.plotroom/` sidecar, persistence and round-trip guarantees | 04, 07, 19, 25, 31, 37, 45 | D017 |
| [commands-undo-history.md](commands-undo-history.md) | How anything changes: command enums, the registry, plan → admit → commit, hooks and lowering timing, undo groups, gestures, history, dirty state, view state, `Session::step` | 17, 21, 31, 38, 45 | D006, D024 |
| [validation-and-lints.md](validation-and-lints.md) | Rules, severity, the code registry, quick fixes, acknowledgements, profiles and the "Requires" badge, Teller, lint owners, readiness | 19, 23, 24, 28, 31, 34, 35, 36, 45 | D003, D011, D012 |
| [agent-runtime.md](agent-runtime.md) | Wilco and the workflow runtime: reach, providers, definitions, journal, decision kernel, qualification, knowledge, the campaign flow, the three dials, cost, Model Manager, safety | 12, 13, 14, 16, 21, 25, 30, 38, 40, 44, 46–48 | D009, D021–D027 |
| [ui-shell.md](ui-shell.md) | The egui shell, classic renderer, map, dialogs, inspector, panels (Plotline, the Tote, Standing Orders, Drill), glass box, frame discipline, threading | 03, 05, 06, 19, 33, 38, 45 | D016, D028, D029 |
| [game-integration.md](game-integration.md) | Installs, VFS and mod sets, catalogs, Preview staging and launch, run records, live link, probes, export, security | 05, 08, 20, 24, 27, 32, 42 | D003, D012, D018, D030 |
| [extensibility.md](extensibility.md) | T0 packs, one definition format, skills, T1 WASM, T2 connectors and feeds, grants, registry, the outbound MCP server | 22, 38, 42, 45 | D007, D008, D019, D020 |
| [testing-strategy.md](testing-strategy.md) | Test layers, upstream porting, property and round-trip tests, the kernel harness, runtime and cost tests, UI tests, edge fakes, probes, CI gates | 04, 06, 20, 21, 25, 38, 40, 45 | D013, D016, D017 |

Read this README, then the file for the question at hand; each file lists its own open questions.

## 6. Build order (architecture view)

The roadmap owns dates and milestone names; this is the dependency order the architecture implies. Crates land in the milestone that
first needs them ([crate-map.md](crate-map.md) "Lands" column).

**Lanes after M0.** (A) formats → kernel → classic editor; (B) renderer proof of concept → map → classic dialogs, which needs VFS,
catalog and terrain in M1; (C) installs and Preview: the P0 script in M0, staging and launch proven on opened missions during M1–M2,
public in M3; (D) AI de-risking: the `tools/local-qual` confirmation run and the provider-wire spike from M0, a faux-model runtime by
M4, real models in M6.

| Milestone | Contents | Exit evidence | DG gates before its code |
| --- | --- | --- | --- |
| M0 Foundations and spikes | Workspace (edition 2024, LTO, `codegen-units = 1`), workspace lints, `xtask layers`, cargo-deny, REUSE, 3-OS CI, `CODE-INDEX.md`; spikes with go/no-go: doc 06 §7's five renderer spikes, doc 08 P0 on real installs, CST span patch plus writer parity, snapshot benchmark, doc 44 §5.4 confirmation run, provider wires | CI green; the layers test fails on a deliberate bad edge; spike reports | DG005, DG011 (before M1/M2 code) |
| M1 Viewer (0.1) | Formats, VFS, installs, catalog, terrain, read-only project, renderer and map, per-profile lint report, `plotroom check` | Round-trip properties; fuzz clean; map goldens; ported rows marked | — |
| M2 Classic editor (0.2–0.3) | Kernel, mission writes, sidecar and identity, commands, admission, history and lanes, dialogs with Easy/Advanced and relabels, field checks, limits meter, save, crash journal, PBO export | Kernel invariants; one-action-one-undo family; byte-identical unchanged save | DG017 (sidecar records) |
| M3 Preview beta (0.5) | Strict Preview including unsaved edits, Validate, Preview from camera, Intro/Outro, run records and debrief, live link, mod-set launches, `--private` after its probe, export gate | Probe results on Remastered; export-scan goldens; fake-binary supervisor tests | Before a public release: OWQ-07's clearance search and repository rename done (DG002 decided: option A), OWQ-09's private reports sent, OWQ-10's letter answered or a decision to proceed |
| M4 Modern power, knowledge, no-model runtime | Teller, briefing and stringtable editors, attributes and power tools, "New mission from template" as the first workflow, workflow runtime and decision kernel with a faux model, readiness coach, Standing Orders and Drill track A, T0 packs, the opt-in MCP server (in v1: OWQ-15 (a)) | AT-W1–W5, W7; crash at every journal entry; Drill scripts in kittest | DG003, DG007, DG008 (`when`), DG010, DG015, DG016, DG017, DG018, DG031, DG032, DG033 items 1–2 |
| M5 Campaigns | CXL, modules and rules wave 1, campaign model, compile, simulator and import, Plotline, the Tote, campaign Preview prologue, Cutscene node, no-model campaign flow and Quick Op, Grey Heron as a synthetic fixture | Compile goldens; Preserve import byte identity; CXL property; E10 no-model validity | DG004, DG008, DG009, DG035 (Cutscene node); the 1.99 probe suite before freezing `Cwa199` lowering |
| M6 Wilco and the model-driven flow | Providers, `plotroom-net`, Model Manager with the managed `llama-server` as the primary local runtime (owner, D022 amendment note), Wilco, evals, S0–S9 with models, cost UX | AT-W6, W8–W11; E1–E12 with controls; prefix-stability goldens; wire tests | DG006, DG012, DG015, DG019–DG027 decided or explicitly defaulted; §8 item 6 (no agent eval in Preview) |
| v1 | M1–M6 hardened (D004) | Byte-faithful save; Preview on Remastered; Wilco with a weak local model; a campaign that compiles for its profile with and without a model; every generated element inspectable; an imported campaign re-saves byte-identical | OWQ-01 (b)'s wording in `NOTICE` with the legal review; the OWQ-13 (a) and OWQ-14 (a) scope applied; DG002/OWQ-07's placement applied |
| v1.x | T2 connectors and feeds, T1 WASM and SDK, registry RG1, MP Preview, the strategic layer and Grey Heron acceptance (first after v1, OWQ-13 (a)), the cinematics timeline and director (v1.2, OWQ-14 rung 4 (a)), atmosphere, replayability variants, balance lab, audio | — | DG009, DG034–DG038; DG014, DG029 and DG030 as the owner decided them (OWQ-16, OWQ-12, OWQ-17) |

## 7. Conflicts resolved

| # | Conflict (judges) | Resolution | Where |
| --- | --- | --- | --- |
| 1 | Command representation: closed enum vs trait objects vs `Box<dyn>` batches | Closed serde/schemars data enums per area next to each model; one outer `EditorCommand` above all models; services via traits in `PlanCtx`; `Box<dyn>` batches rejected | [commands §2](commands-undo-history.md) |
| 2 | Core granularity and broken edge tables | Kernel `plotroom-doc` below the models (L3), `project`/`commands`/`validate`/`view` above them (L4); explicit same-layer edge list checked by `xtask layers` | [crate-map §2, §6–§7](crate-map.md) |
| 3 | Permissive licence lane for format crates and the SDK | GPL-3.0-or-later everywhere (D001); the SDK too, for now (OWQ-03 (a); revisit at doc 22's phase 3 if plugin authors ask) | [crate-map §14](crate-map.md) |
| 4 | Shared `plotroom-bytes` vs "helpers in each format crate's `read.rs`" | Thin per-crate `read.rs` wrapping the shared cursor and mapping errors into the crate's own named-field variant; no `AGENTS.md` amendment | [crate-map §3](crate-map.md) |
| 5 | Provenance per field (`Tracked<T>`) vs per element | Element record plus a sparse per-field map; `Pin` enum; automatic human ownership | [core §8.1](core-document-model.md) |
| 6 | Eager vs lazy lowering | Eager and incremental for document content (doc 31 §8.3 needs real emitted entities); campaign compile on demand; invariant violations refuse, compiler errors keep last good output as Stale | [commands §5](commands-undo-history.md) |
| 7 | Boolean flags vs enums | `CommandEffect`, `Reach`, `Destructiveness`, `Pin`, `RuleKind`, `AckReason` enums | [commands §3](commands-undo-history.md) |
| 8 | Three severity lattices | `EngineError`, `ProfileError`, `Warning`, `Advisory`, `Info`; plausibility is a rule kind emitting `Advisory` | [validation §3](validation-and-lints.md) |
| 9 | Op shape; absolute byte spans | One serialisable `Op` on `ElementRef`, `SetSidecar { value: Option<_> }`, `ReplaceText`; CST ops anchored on paths, offsets computed from a relative-length green tree | [core §3.1, §5.2](core-document-model.md) |
| 10 | Egress and I/O confinement | One HTTP crate with `EgressGrant`; one file writer; processes only in `plotroom-preview` and `plotroom-model-manager` | [crate-map §2.3](crate-map.md) |
| 11 | Journal location (DG017) | `.plotroom/journal/` per DG017 option A (proposal); crash op journal in app data; linked by `CommitId`; replay record a separate opt-in | [agent §5](agent-runtime.md) |
| 12 | Capability probes spawning the game at discovery | Discovery is pure; the probe runs in `plotroom-preview` on a user action and is cached | [game §2](game-integration.md) |
| 13 | In-process embedded inference | Always out of process (a supervised helper). The owner's runtime decision (2026-09-27; D022 amendment note) makes the managed `llama-server` sidecar the primary local runtime, with Ollama and LM Studio as bring-your-own endpoints | [agent §3](agent-runtime.md); §8 |
| 14 | Milestone order (runtime before shell, shell before runtime, kernel before all) | Four lanes; faithful editor and Preview first for users, AI de-risking in parallel from M0, no-model runtime by M4 | §6 |
| 15 | Stale M0 items | `docs/decisions/` and `docs/upstream/` exist; crate and sidecar names follow D002 item 4 and are fixed in `CODE-INDEX.md`; no rename DG | §6 |
| 16 | Type names embedding a third-party mark | Neutral identifiers (`Legacy196Text`, `RemasteredText`); the naming rule's spirit applies to types too | [crate-map §15](crate-map.md) |
| 17 | Consent typing | `UserIntent`, minted only by the session; agent, runtime, plugin and MCP crates cannot depend on the minting crate | [commands §4.4](commands-undo-history.md) |
| 18 | Agent eval in Preview (doc 08 §6 P2 vs docs 21, 24) | No agent eval; Validate-in-game is a user button; Wilco reads typed run reports | [agent §2](agent-runtime.md); §8 |
| 19 | MCP semantics and timing | Loopback, token, opt-in; external runs wait for an editor click; external proposals never auto-apply; ships in v1 (OWQ-15 (a)), not before the plan card and inspector; `workflow.decide` after v1 | [extensibility §10](extensibility.md) |
| 20 | Where the decision kernel lives | Separate `plotroom-decide`, so AI-off workflows and MCP never depend on Wilco | [agent §1](agent-runtime.md) |
| 21 | Crate-name collisions (`models`, `harness`, `Effect`) | `plotroom-provider` / `plotroom-model-manager`; `plotroom-workflow-runtime` / `plotroom-gamelink`; `CommandEffect` / `AgentEffect` | [crate-map §15](crate-map.md) |
| 22 | Readiness coach ownership | Readiness model in `plotroom-validate`, UI in Problems, Wilco only phrases (doc 21 §11.1 `Forbidden`) | [validation §11](validation-and-lints.md) |
| 23 | DG006, DG015, DG021 option choices | Follow each DG's recommendation (C: hard max 7 plus per-setup caps; B: no schema on Pick; B: adaptive K everywhere) as proposals | [agent §6](agent-runtime.md) |
| 24 | Qualification granularity vs doc 44 | Fill qualifies per field and is a confirmed pre-fill; knowledge qualifies for no model; badges say "spike-checked" | [agent §7](agent-runtime.md) |
| 25 | AI default vs first-class campaign flow | D004: Wilco off by default, no provider and no network; the flow stays visible and runs without a model | [agent §1](agent-runtime.md) |
| 26 | DG013 follow-through | Load lint refusing effort predicates on `ask`/`approve`; doc 38 §8.1's `effort_at_least` removed | [agent §4](agent-runtime.md) |
| 27 | DG gating: all in M0 vs per milestone | Per milestone | §6 |
| 28 | v1 scope: timeline, attributes, locales | The owner decided rung 4 (OWQ-14 (a)): the Cutscene-node recipe with camera scripting through the script editor in v1, the cinematics timeline and director in v1.2; atmosphere and replayability variants in v1.x; attributes and power tools in M4; locales supported by the shell, Standing Orders and Drill content in English first (OWQ-14 (a)) | §6; [ui-shell §12](ui-shell.md) |
| 29 | Live-link console before Teller | Teller's field checks land in M2, before the M3 live link | §6 |
| 30 | Security hardening entries | Private reports first (OWQ-09 (a): the owner reports; not yet sent); no new public detail before acknowledgement | [game §12](game-integration.md) |
| 31 | Provider wires: rig vs own clients | D021 baseline (exact-pinned rig inside one adapter crate) until the wire spike says otherwise | [agent §3](agent-runtime.md) |
| 32 | Renderer proof-of-concept timing | M0, with go/no-go before dialogs are built (D016 item 6) | §6 |
| 33 | Corpus environment variable names | `PLOTROOM_CORPUS_DIR`, `PLOTROOM_GAME_DIR` | [testing §15](testing-strategy.md) |
| 34 | Lanes of undo | Filtered views over one project history; out-of-order revert only when ops commute | [commands §8](commands-undo-history.md) |
| 35 | First public release gating | M3's public release waits for OWQ-07's clearance search and repository rename (placement decided: DG002 option A), OWQ-09's private security reports sent, and OWQ-10's letter answered (or a documented decision to proceed) (D034 item 2; D035) | §6 |

## 8. Design-gap candidates raised here

These contradict a research doc or a baseline record and should be filed in `docs/design-gap-requests/` in the next change (this
change files none):

1. **Sidecar spelling and export**: `.plotroom/` dot-directory instead of doc 04 §12.3(11)'s file; the 1.99 exporter probe (doc 45 OQ1).
2. **Three `Origin` types** split into `ConfigOrigin`, `Origin`, `Provenance` (doc 45 OQ2; docs 04, 21, 22, 26, 38).
3. **128-bit ids for campaign nodes, edges and variables** instead of doc 19 §4.2's `u32` (doc 45 OQ4).
4. **Live groups apply with observability flags** (doc 45 OQ6).
5. **Lowering timing and failure classes** versus doc 45 §2.2 item 4's "any hook failure refuses the group".
6. **No agent eval in Preview**; `validate_mission` and `eval_sqf_in_preview` of doc 08 §6 P2 become user buttons or are dropped
   (docs 08, 21 §1.3, 24 §5.4).
7. **Embedded inference always out of process**, refining D022 item 1(3) (needs the owner or D022's revisit evidence). The owner's
   runtime decision of 2026-09-27 makes the managed sidecar primary but does not decide the in-process backend, so this stands.
8. **Campaign layout `Option<CanvasPos>`** (doc 45 OQ8; doc 19 §4.2).
9. **Provenance granularity**: element record plus sparse field map instead of doc 26's `Tracked<T>` on every field.
10. **Two journals linked by `CommitId`** (doc 45 OQ3): a note on DG017 rather than a new request.
11. **The v1 CLI's subcommands** (added 2026-09-27): OWQ-14 (a) and D036 item 3 give the v1 CLI as lint, compile/export, round-trip
    check and golden-journal replay, with no agent, while `plotroom-app` forwards `stage`, `workflow test`, `pack check` and `qualify`
    (`CODE-INDEX.md` §4; testing-strategy §10). Whether `qualify` (it calls models, though not Wilco) and `stage` ship in the v1 CLI
    needs a decision; until then they are proposal-only.

Already listed as candidates in the DG index: cutscene-section staging, the doc 25 `Stage` enum superseded by workflows (I38-STAGE),
generated file names built from labels.

## 9. Cross-cutting open questions

1. *Answered 2026-09-27:* v1 campaign-flow size (OWQ-13 (a)), v1 modules, CLI, Standing Orders content and locales (OWQ-14 (a)), MCP in
   v1 (OWQ-15 (a)). What remains is sizing inside those answers (roadmap §10).
2. Snapshot cost with structural sharing, and whether the document thread fallback is needed (doc 45 OQ5; M0/M2 benchmark).
3. Re-match thresholds after external saves (doc 45 OQ9).
4. Whether shipping builds keep honouring the test flags Preview relies on (doc 08 §7; P0).
5. The 1.99 behaviours that gate `Cwa199` lowering (doc 19 OQ1; doc 29 §9; doc 37 PP rows; doc 43 probes).
6. Whether a 3–4B local model reaches useful pass^k on the shapes the harness grants it beyond doc 44's spike (confirmation run).
7. The generated-content §7 permission's final wording and legal review (OWQ-01 (b)); the SDK licence is GPL-3.0-or-later for now
   (OWQ-03 (a)).
8. Descriptor placement is decided (DG002 option A; `AGENTS.md` "Naming and Trademarks" amended); the clearance search and the
   repository rename remain to be done before the first release (OWQ-07).

## Appendix A. Integration items: owners

The 65 integration items collected in the first part of the consolidation pass (proposals from later docs aimed at earlier designs).
That working inventory is not kept in the repository; this table and the roadmap's
[integration owners](../roadmap/integration-owners.md) are its record. **Architecture** means a section
of this folder owns the design; **Decision** means a record already owns it; **Doc fold** means the change is an edit of research docs in
the consolidation step, not architecture; **Content** means skill or knowledge content; **v1.x** means explicitly deferred. The
milestone is the architecture's landing point (§6).

| Item | Owner | Where | Lands |
| --- | --- | --- | --- |
| I35-PRIMER-MP | Content + Architecture | `skills/mission-primer` (MP section in `references/`, pointer in SKILL.md); stable primer anchors in [agent §8](agent-runtime.md) | M4 |
| I35-PRIMER-FACTS | Content + Architecture | Same; the top-100 palette and house style as Teller data ([validation §9](validation-and-lints.md)) | M4 |
| I35-MOD | Doc fold + Architecture | Doc 31 §4.6 reconciliation; one module catalogue data file ([extensibility §3.5](extensibility.md)); v1 list: the wave-1 modules whose probes pass on `Cwr` (OWQ-14 (a)) | M5 |
| I35-MOD2 | Architecture | Module contract extensions ([core §9](core-document-model.md)); composition library ([extensibility §3.1](extensibility.md)) | M4–M5 |
| I35-TPL | Architecture; families v1.x | Template kind and legacy import ([extensibility §3.1](extensibility.md)); `plotroom-generate` ([crate-map §8](crate-map.md)) | M4 |
| I35-CUT | Architecture (provisional) | Cutscene-node recipe in `plotroom-cine` ([core §9](core-document-model.md)); reconcile via DG035 | M5 |
| I35-DRILL | Content + Architecture | Doc 33 §5 and `skills/standing-orders`; Drill runner ([ui-shell §6](ui-shell.md)) | M4 |
| I35-GEN | Architecture | Code-owned defaults in `plotroom-generate` ([agent §10](agent-runtime.md)); rc55–rc57 in [game §4, §11](game-integration.md); rc53 guard as a compiler-owned singleton ([core §8.3](core-document-model.md)) | M5 |
| I35-PREV | Architecture | Campaign-node Preview prologue ([game §5](game-integration.md)) | M5 |
| I35-LINT | Architecture | Lint owners table ([validation §10](validation-and-lints.md)); codes via DG005 | M2–M5 |
| I35-19 | Architecture | Variant nodes, output contracts, `Ignored` ([core §9](core-document-model.md)); outcome-matrix builder and follow-up ([agent §10](agent-runtime.md)); rc80/rc83 as generator defaults; MP series export v1.x | M5 |
| I35-26 | Architecture | Archetype data ([agent §10](agent-runtime.md)); protagonist lane in Plotline ([ui-shell §6](ui-shell.md)) | M5–M6 |
| I35-29 | v1.x | Strategic layer, the first milestone after v1 (OWQ-13 (a)); campaign modules ([core §9](core-document-model.md)) | v1.x |
| I35-84 | Architecture + Doc fold | "Remap to an installed set" workflow ([game §3](game-integration.md)); label rename in doc 35 | M4 |
| I35-90 | Architecture + data pass | Evidence tiers in `plotroom-profile` and the catalog ([validation §8](validation-and-lints.md)); CSV column in the next data pass | M2 |
| I35-MOMENT | Architecture | Moment cards as data ([agent §10](agent-runtime.md)); MC21 ([validation §10](validation-and-lints.md)) | M5–M6 |
| I37-IDIOMS | Content + Architecture | Primer `references/idioms.md`; construction rules ([validation §10](validation-and-lints.md)) | M4 |
| I37-SO | Content | Standing Orders entries; concept ids ([agent §8](agent-runtime.md)) | M4 |
| I37-31IDX | Architecture | Teller reference kinds ([validation §9](validation-and-lints.md)) | M4 |
| I42-08 | Architecture | `--private` on every launch after the P0 probe ([game §6](game-integration.md)) | M0/M3 |
| I29-08 | Architecture | P0 questions and campaign probes ([game §6, §10](game-integration.md)); ER-007 | M0/M5 |
| I38-BUDGET | Decision + Architecture | D025; load lint ([agent §4](agent-runtime.md)); doc 21 note is a doc fold | M4 |
| I38-STAGE | Decision + Architecture | D025; [agent §10](agent-runtime.md); doc 25 note is a doc fold | M5 |
| I38-GATE | Architecture + Doc fold | `NonEmpty` gates and checks ([agent §4](agent-runtime.md)); doc 21 §6.1 note | M4 |
| I40-14 | Decision + Architecture | D026; dated `[[price]]` rows ([agent §12](agent-runtime.md)); doc 14 §7 fold | M6 |
| I40-25 | Architecture | E12 ([testing §10](testing-strategy.md)) | M6 |
| I42-22 | Decision + Architecture | D008 (feeds); manifest fields and lints ([extensibility §3.2, §7, §9](extensibility.md)); feeds and RG1 v1.x | M4 |
| I42-25 | Architecture | S0 mod-set picker and facets ([agent §6, §10](agent-runtime.md)) | M5–M6 |
| I42-17-30 | Architecture | Overlays as T0 packs, only in code-selected cards ([extensibility §3.1](extensibility.md); [agent §8](agent-runtime.md)) | M4 |
| I42-37 | Architecture | Remap tiers ([game §3](game-integration.md)) | M4 |
| NEW-README | Docs index (not this folder) | `docs/README.md`, a separate change; it should link this folder | — |
| NEW-DGDIR | Done | `docs/design-gap-requests/` exists (DG001–DG038); new candidates in §8 | — |
| I17-DEC | Done | `docs/decisions/` D001–D043 | — |
| I34-MERGE | Doc fold | Merge pass of docs 31, 33, 34; single data catalogues prevent duplicates ([extensibility §3.5](extensibility.md)) | — |
| I34-02 | Decision + Architecture | D001, OWQ-06 (answered; [D033](../decisions/D033-campaign-extension-overlays.md)); D9 lint ([validation §10](validation-and-lints.md)); SPDX per item ([extensibility §3.2](extensibility.md)); the IC D051 comparison is a doc 02 fold for the legal review | M3–M4 |
| I34-04 | Architecture | Intel levers, voice-language rule, sidecar-only objects ([core §3.2, §3.4, §10](core-document-model.md)) | M2 |
| I34-05-06 | Architecture | Overlays, fonts, action ids, keymaps, preference split ([ui-shell §1, §3, §6, §8](ui-shell.md)) | M2–M4 |
| I34-08 | Architecture; rest v1.x | Run records, debrief, battle report, outcome display ([game §7](game-integration.md)) | M3 |
| I34-09 | Doc fold | Doc 09 cross-references | — |
| I34-13 | Architecture | Component presets and storage panel ([agent §13](agent-runtime.md)) | M6 |
| I34-17 | Doc fold | Doc 17 pointer and "designed" marks | — |
| I34-18 | Doc fold + probe | Doc 18 note; reading another campaign's save is a probe question ([game §10, §14](game-integration.md)) | — |
| I34-19 | Architecture | Derived variables, conditions, effect sentences ([core §9](core-document-model.md)); hub cards and thread lanes ([ui-shell §6](ui-shell.md)); outcome lints | M5 |
| I34-21 | Architecture; ribbons to owner | Per-origin undo lanes ([commands §8](commands-undo-history.md)); `/` dispatch ([agent §9](agent-runtime.md)); Drill order, test-out, code-validated tours ([ui-shell §6](ui-shell.md)); ribbons must clear doc 36's cv43 rule, a product rule since OWQ-20 (a) | M2–M6 |
| I34-22 | Architecture | Manifest fields and T0 kinds ([extensibility §3](extensibility.md)) | M4 |
| I34-23-24 | Architecture | Migration tips, path hover, MC27, risk rows ([validation §9](validation-and-lints.md)) | M4 |
| I34-25 | Architecture; Mole and Nemesis v1.x | Thread lifecycle, one-slot fills, lock-based regeneration ([agent §10](agent-runtime.md)) | M6 |
| I34-26 | Architecture; strategic rows v1.x | Content libraries and persistence modules ([agent §10](agent-runtime.md); [core §9](core-document-model.md)) | M5–M6 |
| I34-27 | Architecture | Lock, resolver, drift, handoff, server lists, D9 ([game §3](game-integration.md)) | M1–M3 |
| I34-28 | Architecture | MC20–MC29 registered provisional ([validation §5, §10](validation-and-lints.md)) | M0 registry |
| I34-29 | v1.x | Strategic layer; its probes join the suite ([game §10](game-integration.md)) | v1.x |
| I34-31 | Doc fold + Architecture | Module reconciliation; Show/Eject/Lift ([core §8.3](core-document-model.md)) | M5 |
| I34-32 | Architecture (MC25, MC26); rest v1.x | [validation §10](validation-and-lints.md); timeline items with cinematics | M5 |
| I34-33 | Content + Architecture | Doc 33 lesson content; Drill runner ([ui-shell §6](ui-shell.md)) | M4 |
| I36-19 | Architecture | Classic tier default, progress tracks, readiness overlay, "decided" query ([core §9](core-document-model.md); [ui-shell §6](ui-shell.md)); CF27 | M5 |
| I36-21 | Architecture; tuning v1.x | Readiness coach ([validation §11](validation-and-lints.md)); explain mode ([agent §9](agent-runtime.md)) | M4 |
| I36-22-27 | Architecture | Identity blocks, generated references, vanilla invariant, sharing, rule overrides ([extensibility §3](extensibility.md)) | M4 |
| I36-25 | Architecture | Code gates after S3/S4, early skeleton, rule of 33s ([agent §10](agent-runtime.md)) | M5–M6 |
| I36-26 | Architecture | Content data ([agent §10](agent-runtime.md)); MC30, CF26 ([validation §10](validation-and-lints.md)) | M6 |
| I36-29 | v1.x; one rename now | Strategic rules v1.x; the `DifficultyPreset::Veteran` rename goes to the names table the design round keeps (OWQ-08 (a)) | v1.x |
| I36-31 | Architecture | Rule-override presets, AI-executability note, announce cue ([core §9](core-document-model.md); [extensibility §3.1](extensibility.md)) | M5 |
| I36-32 | v1.x | Music cue pairs and the finale epilogue with the timeline and atmosphere work | v1.x |
| I36-33 | Content + Architecture | Standing Orders pane ([ui-shell §6](ui-shell.md)); new entries | M4 |
| I29-26-19 | Decision + Doc fold | D005; SL cross-references via DG005 ([validation §5](validation-and-lints.md)) | — |
| I33-SEED-B | Content + Architecture | `skills/standing-orders` entry format; evidence marks enforced in CI ([agent §8](agent-runtime.md)) | M4 |

## Verification notes

### Architecture baseline (2026-09-27)

- Read for this baseline: `AGENTS.md`; `docs/decisions/README.md`, `OWNER-QUESTIONS.md`, D002, D003, D004, D007, D008, D016, D017,
  D022, D025; `docs/design-gap-requests/README.md`, DG017 and the recommended resolutions of DG004–DG008, DG011, DG015, DG021, DG023,
  DG031–DG034; `docs/upstream/README.md` and the register's ids by area; the counts of `docs/porting/upstream-test-map.csv`;
  the section structure of research docs 04, 06, 08, 12, 13, 14, 19–25, 27, 29–33, 37, 38, 40, 42–45; doc 45 §2 and its open
  questions; doc 44 §4–§5; doc 38 §4; doc 23 §13; the three architecture proposals and the three judges' reports.
- Many section citations were carried over from the proposals and were checked against section headings, not re-read line by line.
  Numbers marked as targets or placeholders (budgets, caps, thresholds) are proposals to be measured.
- No research doc, decision record, DG or `AGENTS.md` was edited by this change; the design-gap candidates in §8 are not yet filed.

### Links and hygiene review (2026-09-27)

- Every relative link in this folder resolves, and every "§n" in a link's text names a heading of the linked file. No private or
  unpublished project, local path or third-party mark in a crate, module, format, sidecar or header name was found.
- §1 and Appendix A now say that the three proposals, the judges' reports and the integration inventory were working drafts not kept
  in the repository, so that no citation points at a file a reader cannot find.

### Consistency review (2026-09-27)

- Checked this folder against `AGENTS.md`, D001–D030, the decided DGs, the roadmap and the crate "Blocked on" columns. §3 gains P15
  (fun, D009 item 5). §6's DG gates now match the crate map and the roadmap: DG008, DG010, DG015 and DG016 in M4 (the workflow crates
  land there), DG009 and DG035 in M5 (the Cutscene node), §8 item 6 in M6 (Wilco's tool set), OWQ-09 before the first public release,
  and the release gates of the roadmap's v1.0. "Design-gap candidate" pointers in the other files now name §8, not §7.
- Other fixes: `plotroom-evals` ships (in-app qualification); the sidecar holds the mod-set lock once (`modset.toml`); Model Manager
  downloads, manifest updates and Ollama pulls follow D008; the conservative subset follows D003 item 5's wording; F1 stays a mode
  key in the Classic keymap (doc 34 le06); the descriptor-placement conflict between `AGENTS.md` and DG002's recommendation is
  flagged in ui-shell §12 and OWQ-07; §7 row 28's deferral of the cinematics timeline now points at OWQ-14's new rung-4 item, because
  v1 scope is the owner's call; `plotroom-cxl` may land in M4 for the workflow `when` scope (agent §4 uses its AST); Plotline names the
  visual condition builder that `AGENTS.md` asks for (ui-shell §6).

### Owner answers folded (2026-09-27)

- The owner answered OWQ-01 to OWQ-23 on 2026-09-27 (`OWNER-QUESTIONS.md`), each with the recommended option, and decided the local
  runtime (D022 amendment note). This folder now states: OWQ-13, OWQ-14 (including rung 4) and OWQ-15 as decided scope (§6, §7 rows
  19 and 28, §9, Appendix A; agent-runtime §10, §15; crate-map; extensibility §10); OWQ-07's placement in ui-shell §12, matching the
  amended `AGENTS.md`; OWQ-19 and the runtime decision in agent-runtime §3 and §13; OWQ-16, OWQ-17 and OWQ-18 in extensibility §3.2,
  §7, §9 and game-integration §3, §4, §12. Remaining owner actions (clearance search, repository rename, OWQ-09 reports, OWQ-10
  letter) stay as release gates. Doc 48's cloud round is deferred by the owner until doc 49's local results exist.
- Everything else in this folder keeps its proposal status.

### Consistency review of the owner answers (2026-09-27)

- The header now lists every decided DG and names D031–D043 as the records of the owner's answers; agent-runtime §13 cites D037
  instead of the placeholder "the OWQ-19 record", and §3's doc 46 figures carry doc 46's qualifiers. Checked against `AGENTS.md`
  (the amended "Naming and Trademarks" matches ui-shell §12 and D034), D031–D043 and the roadmap; no design changed. §7 row 35 now
  lists OWQ-09's private reports among the release gates, as §6's M3 row, roadmap §3 item 8 and D035 already did.
- Open, not decided here: whether `plotroom qualify` (testing-strategy §10; agent-runtime §13) and the `stage`, `workflow test` and
  `pack check` subcommands that `plotroom-app` forwards (`CODE-INDEX.md` §4) belong to the v1 CLI, which OWQ-14 (a) and D036 item 3
  list as lint, compile/export, round-trip check and golden-journal replay. It is a design-gap candidate for §8.
