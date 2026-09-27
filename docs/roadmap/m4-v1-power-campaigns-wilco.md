# Roadmap: M4 to v1.0 (modern power, campaigns, Wilco, release)

> **Status:** proposal (roadmap baseline 2026-09-27). Part of the [roadmap](../roadmap.md). Same section layout as
> [m0-m3-foundations-to-preview.md](m0-m3-foundations-to-preview.md). Every threshold quoted from a research doc is that doc's
> placeholder; moderated-session targets are set after the first study.

## M4 Modern power, knowledge and the no-model runtime (0.6)

**Goal.** The modern layers that make mission making faster without any model, and the harness infrastructure proven by AI-off
features before any real model call exists (architecture README §2 item 2): the Teller language service and text editors, attributes and
power tools, templates, Standing Orders and Drill track A, T0 packs, and the workflow runtime with its decision journal running on a
**faux model**.

**Scope.**

- **Teller in full** (`plotroom-teller`; doc 23; doc 31 §7): mission-aware symbol index with the reference kinds rename needs
  (`markers[]` links matched case-insensitively, `respawn_` prefixes, objective ids across HTML and `objStatus`, per-unit briefing
  sections; runtime-built names listed as "cannot prove"; I37-31IDX), rename with references, hover, completion, silent-failure lints
  (rc60, rc61), migration tips triggered by findings (le09), path-resolution hover and MC27 (I34-23-24). The top-100 command palette and
  SQS house style as Teller data (I35-PRIMER-FACTS rc13).
- **Text editors:** script editor panel; briefing, stringtable and screenplay views with per-language columns and staleness.
- **Attributes and power tools** (doc 37 PT0–PT3 without the MP and island parts): the editable inspector with exact values and
  multi-select; rung-1 attributes in `plotroom-modules` with lowering in `plotroom-lower` (attributes only), lift recognisers, the
  Attributes overlay, map verbs, drop chip and presets; the dependency doctor; rename with references; raw mode; bulk edit; class remap
  as **"Remap to an installed set"** (renamed from doc 35 rc84, I35-84), an AI-off workflow with doc 42 §2.9's tiers (I42-37); side swap;
  merge and split; normalise. Idiom constraints as construction rules (I37-IDIOMS). Route and accessibility overlays (ed08, ed21).
- **Templates and compositions:** `plotroom-template` (minijinja with fuel and marker escaping, D020); `plotroom-generate` first slice:
  typed templates with named anchors and derived entities, provenance "derived from anchor X", legacy template import as canonical with
  Remastered deltas as metadata (I35-TPL rc34, rc40); our own composition library per side by role tags (I35-MOD2 rc33). "New mission
  from template" is the **first workflow**.
- **Workflow runtime** (doc 38 W1–W3, W5): `plotroom-workflow` (TOML definitions, loader, definition compiler; `NonEmpty` gates and
  checks, I38-GATE; the whole-run `[budget].turns` semantics and its load lint, I38-BUDGET), `plotroom-decide` with the faux model
  (capsules, menus, admission, checks, repair), `plotroom-workflow-runtime` (journal, ledger, scheduler, resume, cancellation tree,
  staleness, `RunEvent`); the plan card, run panel, decision inspector and run graph. Built-in AI-off workflows: `core/give-patrol`,
  `core/validate-and-fix`, "New mission from template", "Remap to an installed set".
- **Readiness coach** as one dominant control in Problems: blocking versus advisory, snooze, audited "Preview anyway"; no finding lacks
  both a fix and a dismiss (I36-21).
- **Knowledge** (`plotroom-knowledge`; D027; D028): one store for Standing Orders entries, cards, primer anchors, skills, lessons and tips,
  every fact with an evidence mark that CI enforces (I33-SEED-B); the Standing Orders pane opening in front from the help action (F1
  stays the Units mode key in the Classic keymap, doc 34 le06; ui-shell §6), expert density,
  first-opening tips that speak about the instance or stay silent (I36-33); new entries for height, loadout, cargo, locks, callsigns and
  attributes (I37-SO); primer multiplayer section and new facts in `skills/mission-primer/references/` behind stable anchors (I35-PRIMER-MP,
  I35-PRIMER-FACTS, I37-IDIOMS); doc 33 phases 1–3 (registry and cards, instance help, demos with probes and "Show me in game").
- **Drill track A** (`plotroom-drill`): the lesson runner where code, not Wilco, validates each step; payoff-first order, test-out,
  hint ladder, resume (I34-21 le01, le05; I35-DRILL rc36, rc71, rc73–rc76; I34-33); lessons double as kittest scripts.
- **T0 packs and RG0** (`plotroom-packs`; doc 22 step 1): manifest v1 with `[activation] mods`, `ai`, `ai_usage`, SPDX per item and the
  licence split; Unicode and template-render lints; content kinds workflow, module, composition, preset, template, skill, card, overlay,
  tour, tip, lesson, identity, settings, script-library, lens, lint (I42-22, I34-22, I36-22-27, I42-17-30); contribution sets;
  vendoring into `modules.lock`; built-in packs verified against compiled-in hashes; sideloading with a badge (doc 42 RG0).
- **Mod-aware menus, offline:** the missing-mod card with its three routes and no network (MAT7); on `Cwr` and `Ce` targets its "get
  it" route offers the user-clicked "Launch the game to install mods" (owner, OWQ-17 item 1; it reuses M3's launcher, vanilla, no
  mission, without `--private`; placement in M4 is a proposal); the T0 overlay format with the vanilla pack (doc 42 MS1, first part).
- **Opt-in outbound MCP server** (`plotroom-mcp`; ships in v1, owner, OWQ-15 (a)): loopback, token, tools generated from the registry
  plus `workflow.list/start/status/cancel`; external runs wait for an editor click; decision points answered only in the editor.
- **Names table** that the design round keeps for pending user-facing names (OWQ-08 (a); the owner reviews it before the first
  release), including the rename of `DifficultyPreset::Veteran` before any code names it (I36-29).

**Out of scope.** Real model providers; campaigns; modules beyond attributes.

**Crates.** Land: `plotroom-template`, `plotroom-lower` (attributes), `plotroom-generate` (templates, compositions), `plotroom-knowledge`,
`plotroom-drill`, `plotroom-packs`, `plotroom-workflow`, `plotroom-decide` (faux), `plotroom-workflow-runtime`, `plotroom-provider` (seam
types and the faux provider only), `plotroom-mcp`, `plotroom-cxl` (the workflow `when` scope only, if DG008 picks one
condition language; the campaign scopes follow in M5). Grow: `plotroom-modules` (attributes), `plotroom-teller`,
`plotroom-validate` (readiness coach, craft rules), `plotroom-ui`.

**Depends on.** M2 (kernel, commands); M3 (Preview, for Drill demos, "Show me in game" and PAT4).

**Spikes and probes first.** Doc 33 phase 3's demo probes through the M3 probe runner; doc 37 PP1–PP5 on Remastered (1.99 later) for
attributes that need them; PAT4's harness run.

**Gates.** DG003 (attribute vocabulary), DG007 (one definition format), DG008 (the `when` vocabulary of definitions; D025 open part),
DG010 (resume and replay wording), DG015 (no schema on Pick; its load-refusal fixture is exit evidence below), DG016 (budget and repair
accounting), DG017 (journal storage), DG018, DG031 (concept ids), DG032 (one knowledge store and tool family), DG033 items 1–2 (entry
schema, demo fidelity). Owner answers applied (2026-09-27): OWQ-14 (a) (English content first; the minimal CLI), OWQ-15 (a) (MCP in
v1), OWQ-08 (a) (names table), OWQ-17 item 3 (CC-BY-SA only for editor-only content, for the licence split). DG014 is decided (option
B, OWQ-16): the pack loader refuses a third-party pack workflow that requires another publisher's plugin; chaining in first-party and
user-authored workflows needs T2 plugins, so it arrives with v1.4.

**Exit evidence.**

1. **Runtime:** AT-W1 (every definition-compiler refusal has a fixture with a field-labelled error; fuzzed TOML never panics), AT-W2
   (doc 21 §6.4's build-time test over every registered definition), AT-W3 (crash at every journal entry resumes to the same document,
   zero extra model calls for settled entries), AT-W4 (cancelling any step leaves no half-applied edit), AT-W5 (an undone commit is never
   re-applied), AT-W7 (the faux model as a state machine over every menu letter including `X` and `Q`, malformed, truncated and
   duplicate-key replies, timeouts); load-refusal fixtures for a `schema` key on a Pick step (DG015) and effort predicates on `ask`/`approve`
   (DG013).
2. **Packs:** AT-W12 (a Modified pack workflow does not run until re-approved), AT-W13 (a started run resumes after its pack changes),
   AT-W14 (a hostile pack gains nothing); 31-AT9 (a pack template emitting a `tri*` verb, a `..` path or unescaped text is refused with
   the doc 24 rule id); pack loader fuzz targets; MAT6 (every menu ≤ 7 plus escapes), MAT7, MAT13 (mod-set round trip byte-stable).
3. **AT-W15** (the MCP server ships in v1): an MCP-started run waits for the editor click; `ask`/`approve` are not answerable over MCP.
4. **Power tools:** PAT2 (attribute prefixes golden per profile; only T1 commands in `Cwa199` output; compiling twice is identical),
   PAT3 (lower then lift returns the attribute), PAT5 = MAT8 (remap updates or lists every reference; one undo restores identical
   bytes), PAT7 (dependency doctor), PAT8 (raw mode never locks the editor), PAT11, PAT12 (rename with `markers[]` and crew references),
   PAT13 (merge with colliding names, one undo), PAT14 (20 idioms imported, none lifted, byte-identical save), PAT16 (sidecar deleted,
   lifts offered, byte-identical); PAT4 as an opt-in local harness run; `power_tool_apply_is_one_undo_step`,
   `apply_template_is_one_undo_step`.
5. **Knowledge and Drill:** 33-AT1 (every doc 03 §4.4–§4.10 field has an entry), 33-AT2 (cold-start render for every id), 33-AT3 ("not
   in this engine" entries), 33-AT4 (overlay targets equal their rules' unit-test values on 20 synthetic missions), 33-AT5 (no tip fires
   twice after dismissal), 33-AT6 and 33-AT7 (demos have agreeing probes, reduced motion and transcripts), 33-AT12 (malicious lesson
   packs refused); CI fails on a missing evidence mark; every Drill lesson's reference solution replays in CI.
6. **Teller:** ported script-lang rows complete with the oracle; one failing and one passing fixture per diagnostic code (generated by
   `xtask codes`); rename tests across the reference kinds; the "Requires" badge equals the maximum availability actually used.
7. **Templates:** "New mission from template" goldens per mode family shipped in v1; provenance "derived from anchor X" visible in the
   inspector.

**Parallel lanes.** A (attributes, lowering, Teller); B (script, text, Standing Orders, Drill, plan card and run panels); C (demos and
probes for Drill and attributes); D (runtime, journal, faux model, packs); E (entries, primer, lessons, templates, compositions); F
(DGs above, the doc 33 merge pass of I34-MERGE, names table); G (design of the Grey Heron structural fixture from doc 29 §8, no code).

**Integration items.** I35-PRIMER-MP, I35-PRIMER-FACTS, I35-MOD2 (compositions), I35-TPL, I35-DRILL, I35-84, I37-IDIOMS, I37-SO,
I37-31IDX, I38-BUDGET, I38-GATE, I42-22, I42-17-30, I42-37, I34-02 (SPDX per item), I34-05-06 (overlays), I34-21 (Drill order, tours),
I34-22, I34-23-24, I34-33, I34-MERGE (doc 33 part), I36-21, I36-22-27, I36-33, I33-SEED-B, I36-29 (rename only).

## M5 Campaigns (0.7–0.8)

**Goal.** Campaigns become typed, verified, editable models, and describe → generate → edit runs end to end **without a model**: the
campaign model and condition language, the compiler and engine-faithful simulator, Plotline and the Tote, import in Preserve and Adopt
modes, modules and rules wave 1, the Cutscene node, the campaign Preview prologue and Quick Op (D004 item 4; D009; OWQ-13 (a)).

**Scope.**

- **Models:** `plotroom-cxl` (parser, scope typing, intervals, coverage, printer, engine-faithful evaluator; DG008), `plotroom-campaign`
  (campaign model, campaign `description.ext` lens, roster and pools as classic-tier data, campaign modules; derived variables and
  counters, `VictoryCondition`/`DefeatCondition`, a template sentence per effect (I34-19); variant nodes, declared output contracts,
  the `Ignored` outcome (I35-19)).
- **Compile and simulate:** `plotroom-campaign-compile` (sockets, routers, finisher, `saveVar` layout, campaign `description.ext`;
  import in Preserve and Adopt modes; campaign lints including rc59); `plotroom-campaign-sim` (interpreter with engine semantics, Path
  Explorer, what-if playthrough, the "states from which the ending is decided" query; rc62 state lints).
- **No-code ladder, rungs 2–3** (doc 31 L1–L2): the wave-1 modules whose probes pass on `Cwr` (owner, OWQ-14 (a)): objective, end
  state, respawn point, save point and checkpoint, reinforcements, fire support, air transport, patrol, random, interaction, hostage,
  garrison, conversation; the rule
  builder with native-only lowering and then SQS lowering; the module contract extensions (variant group, counter/any/switch nodes,
  fault isolation; I35-MOD2 rc32); Show/Eject/Lift (I34-31); rule-override presets, an AI-executability note per module, the
  reinforcements announce cue (I36-31); the compiler-owned authority guard per profile (rc53). **One reconciled module catalogue data
  file** (I35-MOD, I34-31, I34-MERGE).
- **Cutscene node** (`plotroom-cine`, v1 subset): the Intro-only recipe with one director script, fade bracket and subtitle defaults
  (I35-CUT, provisional until DG035), lints MC25 and MC26 (I34-32), the skip-safe epilogue rule.
- **Campaign flow without a model** (`plotroom-campaign-flow`; doc 25 §4 as workflow definitions on the doc 38 runtime, I38-STAGE):
  S0 intake fields with defaults and the mod-set facets (I42-25, no-model part); S3 outline defaults with `campaign.fill_defaults`
  (draft-first); code gates after S3 and S4 (horizon mix, interesting decisions), an early playable skeleton, few weighty Picks with
  safe defaults (I36-25); S5 concepts from data: archetypes and modifiers (I35-26), patterns P1–P8 plus P9 registered for v1.1
  (I29-26-19), moment cards (I35-MOMENT), twist catalogue and persistence modules of the classic tier (I34-26), faction personality
  records and local factions (I36-26); S6 deterministic build; S7 template text; S8 verify. Code-owned generator defaults from doc 35
  (I35-GEN). Fan-out with `map` and key-order joins (doc 38 W4). **Quick Op** (rc54).
- **UI:** Plotline (Flow and Theatre views, transition tables with the visual condition builder beside CXL text (doc 19 §5), drag to
  rewire, socket and router meter, protagonist and mode lanes, thread lanes,
  hub-card disclosure, readiness overlay, "reads or sets variable" layer, Classic tier default for imports; I34-19, I35-26, I36-19) and
  the Tote (variables with "set in / read in", roster and pools, witness paths, the "decided" query, the what-if playthrough).
- **Preview and export:** the campaign-node Preview prologue with assumption chips, setting variables in the staged init because
  StartAutoTest clears them (I35-PREV); campaign export with campaign-level `CfgIdentities` and per-mission `CfgSounds`/`CfgRadio`
  (rc56); the completeness gate with Path Explorer coverage (rc70).
- **The 1.99 probe run** (SP-08) for doc 19 OQ1's lowering whitelist before `Cwa199` lowering is frozen; campaign probes (doc 20
  campaign rows; I29-08; the cross-campaign save question of I34-18).
- **Grey Heron structural fixture:** doc 29 §8's campaign built synthetically to stress the campaign model, compiler and runtime,
  with strategic modules stubbed (architecture agent-runtime §10).

**Out of scope.** The strategic layer and balance lab (v1.1); the cinematics timeline (v1.2); MP modules and MP Preview (v1.3);
extension overlays and veteran import (v1.x; OWQ-06 answered, a probe first); any real model.

**Crates.** Land: `plotroom-cxl` (campaign and mission scopes; it grows here instead if M4 created it for `when`), `plotroom-campaign`,
`plotroom-cine`, `plotroom-campaign-compile`, `plotroom-campaign-sim`,
`plotroom-campaign-flow`. Grow: `plotroom-modules` (modules, rules), `plotroom-lower`, `plotroom-generate`, `plotroom-validate`,
`plotroom-preview` (prologue), `plotroom-export`, `plotroom-ui`.

**Depends on.** M4 (runtime, templates, attribute lowering, packs); M3 (Preview and the probe runner).

**Spikes and probes first.** SP-08's lowering-whitelist run on a 1.99 install; the doc 31 §10 probe entries on Remastered (fire-support
rounds, `local` on a Game Logic in single player, marker hiding for pools, in-mission cutscene skip); doc 32 phase 0 probes that the
Cutscene node needs (title speed, `camDestroy` without terminate).

**Gates.** DG004 (module vocabulary), DG008 (one condition language), DG009 (owner of rung-4 cinematic facts), DG035 (Cutscene-director
sibling changes, for the node's defaults); the design-gap candidates on campaign ids (architecture README §8 items 3 and 8) and generated
file names. OWQ-13 (a) (the classic patterns) and OWQ-14 (a) (wave-1 modules) are answered; OWQ-22 (a) is answered too, so the short,
documented boundary list for generated suggestions (written in Standing Orders; the user's own content never filtered) ships with the
archetype vocabulary.

**Exit evidence.**

1. **CXL:** parser fuzzing; scope-typing, interval and coverage tests; the property `interp(ast) == mini_sqs_interp(lower(ast))` over
   random ASTs (doc 19 §9).
2. **Compile goldens** for sockets, routers and finishers per profile; every emitted SQS line passes `check_field` in its mode; the
   "Requires" badge equals the maximum availability emitted; compiling twice is byte-identical (31-AT10).
3. **Import:** Preserve-mode import of synthetic campaigns re-saves byte-identical; an opt-in corpus report; Adopt-mode goldens.
4. **Campaign rows:** the campaign area's `todo` row ported; its 10 probe rows run (Remastered through the harness, 1.99 by hand) with
   results recorded.
5. **Modules and rules:** 31-AT1 (single-player part: BASE respawn, a reinforcement wave, radio-called artillery and a four-shot intro
   with no typed script, every lint passing, no command outside `Cwa199` in its build, a CWR Preview with no script error), 31-AT2,
   31-AT3 (zero clobbers), 31-AT4 (ejected script identical until edited), 31-AT7, 31-AT8, 31-AT11, 31-AT12, 31-AT13, 31-AT14;
   `module_drop_is_one_undo_step`; lowering goldens `{input.sqm, rule.ron, seed, expected.sqm}`; region states (a hand edit makes
   `Customized` and is never overwritten silently).
6. **Campaign flow at T0:** AT-W9 (concurrency 1 and 8 give identical documents and canonical journals, also under a budget that runs
   out mid-`map`), AT-W10 (E9: zero clobbers with edits during a run), AT-W11 (E10: 100 % validity with no model over 20 briefs × 3
   seeds); Quick Op goldens.
7. **Grey Heron structural fixture** (synthetic, CI): compiles for `Cwr` and `Cwa199`; AC05 (Path Explorer reaches every ending with
   witness paths; no uncovered node, trigger and state); AC12 (every generated line source-mapped; every element opens its inspector);
   AC13 (the scoped refines change only their scope; zero clobbered human or pinned fields); AC03's folder, class and row counts reported
   (strategic parts marked pending v1.1).
8. **Lints:** fixtures for MC21, MC25, MC26, MC30, CF26, CF27 and the C lints; the "decided" query's tests.
9. **Preview:** prologue `StagePlan` goldens; a manual note starting a node with injected state on Remastered.
10. **1.99:** the lowering-whitelist probe report; `Cwa199` lowering frozen with "verified on 1.99" badges only for passed probes (D003).

**Parallel lanes.** G (campaign model, compiler, simulator, flow); A (modules, rules, lowering); B (Plotline, the Tote, Cutscene-node
editor); C (prologue, campaign export, SP-08 and Remastered probes); D (fan-out, journal at campaign scale); E (module catalogue data,
archetypes, moment cards, templates for text slots); F (DG004, DG008, DG009, DG035; the doc 31/34 merge pass).

**Integration items.** I35-MOD, I35-MOD2 (module contract), I35-CUT, I35-GEN, I35-PREV, I35-LINT (rc59, rc62, rc70), I35-19, I35-26,
I35-MOMENT, I38-STAGE, I42-25 (no-model part), I29-08 (campaign probes), I34-18 (probe), I34-19, I34-26, I34-31, I34-32, I34-MERGE
(doc 31/34 part), I36-19, I36-25, I36-26, I36-31, I29-26-19.

## M6 Wilco and the model-driven flow (0.9)

**Goal.** Models join as one more kind of recorded step: cloud and local providers, the Model Manager, Wilco's chat modes and the
campaign flow with models, with cost made visible and bounded. Everything stays off by default, on the same admission path as the user,
and glass-box (D004 item 3; D006; D010; D026).

**Scope.**

- **Providers:** `plotroom-provider` in full (requests, constraints, capabilities, `CachePolicy`, model setups, role bindings,
  qualification records, price-row types, `MicroUsd`); `plotroom-provider-http` (Anthropic, OpenAI, Gemini and OpenAI-compatible local
  servers; SSE; cache wiring) per SP-12's verdict; `plotroom-net` (the only HTTP client: `EgressGrant`, offline mode, final-path
  allowlists, no redirects off origin, caps, SSRF guards, resumable verified downloads).
- **Model Manager** (`plotroom-model-manager`; D022; doc 44 §5.3): hardware probe; recommendations from measured fit and qualification
  records, never file size; per-step badges ("spike-checked"); a pinned `models.toml` manifest with Hugging Face revisions and SHA-256;
  downloads started only by the user from an enabled source (D008); the model unloaded before Preview; the storage panel and component
  presets (I34-13). **Decided by the owner (2026-09-27):** the managed `llama-server` sidecar is the primary local runtime, on upstream
  Vulkan, Metal or CPU builds pinned by tag and SHA-256, with Ollama and LM Studio as bring-your-own endpoints and an upstream CUDA build
  as an optional user-started download if doc 49's bench supports offering it; Plotroom's own downloader fetches pinned files (never
  `-hf`); GGUFs the pinned runtime cannot run are refused; every sampler value is pinned per request (D022 amendment note; architecture
  agent-runtime §3, §13). The recommended list holds only qualified models under OSI licences with no field-of-use limit; everything
  else is "custom" with its licence and policy shown, explicit acceptance and an "unqualified" badge (OWQ-19 (a); D037).
- **Decision kernel with real models** (`plotroom-decide`): capsules in the cache-stable order, menus with the DG006 cap, K and R with
  adaptive K (DG021), repair, `OnFail::Split`, shape grants from qualification (Fill as a confirmed pre-fill; knowledge only from cards).
- **Wilco** (`plotroom-wilco`): Ask, Build, Teach and Review modes with fixed tool sets (DG023); `/` dispatch parsed by code (I34-21);
  typed tool-call cards; turn reports led by code-written facts; explain mode answering situational questions with computed "why"s
  (I36-21); the tutor mode (doc 33 phase 5); the persona per D002.
- **Campaign flow with models:** S0 with `ModSetOption`, the mod-set picker, the four-level unit menu and variant chips (I42-25); S1
  premise cards; S2 bible rows with thread lifecycle fields, the MoralComplexity chip and value tags (I34-25); S5 concept menus; S7 text
  slots with one-slot fill rules and lock-based regeneration (I34-25); `core/write-briefing`, `core/populate-town`,
  `core/campaign-refine`; the outcome-matrix builder and "Make a follow-up campaign" (rule of 33s), sized per the roadmap's §10 item 5
  (I35-19, I36-25).
- **Cost UX** (doc 40 §6; D026): plan-card estimates with the price date and the $0 alternative; the live meter with "cache saved";
  per-run, session and monthly caps ending in a resumable `BudgetLimited`; dated `[[price]]` rows and the "prices may be out of date"
  chip after 60 days (I40-14); the Economy mode for bulk text (its name from the names table, OWQ-08 (a)).
- **Evaluation:** `plotroom-evals` with E1–E11, E12 (I40-25) and the controls (no model, random-valid, always-ask); the `tools/local-qual`
  suites ported to Rust; `plotroom qualify` writing qualification records per (setup, decision kind, field).
- **Dials** (D024): autonomy (default Confirm), effort as budgets, explicit role binding in Settings.

**Out of scope.** Plugins beyond T0 (v1.4); `workflow.decide` for external agents (v1.4); in-process inference (v2).

**Crates.** Land: `plotroom-provider-http`, `plotroom-net`, `plotroom-model-manager`, `plotroom-wilco`, `plotroom-evals`. Grow:
`plotroom-provider`, `plotroom-decide`, `plotroom-campaign-flow`, `plotroom-workflow-runtime`, `plotroom-io` (keyring, model installs),
`plotroom-ui`.

**Depends on.** M5 (the flow at T0); M4 (runtime, journal); SP-12 verdict.

**Spikes and probes first.** SP-13 (doc 13 S1, S2, S4, S5 with their exit criteria; doc 46 met S1's parse criterion and part of S2),
SP-14 (can `hf-hub` route through `plotroom-net`; doc 46's plain pinned route is the fallback), and the qualification track (doc 44
§5.4 items 2–10: one grader, UD versus Q4_K_M, harder menus, `--why` and thinking on/off, bigger models, non-English, realistic cards,
other machines and llama-server parity, style-card text). Doc 46 ran UD versus Q4_K_M, the harder menus and llama-server parity on one
8 GB machine; doc 49 measures doc 47's shortlist; doc 48's cloud round follows doc 49 (owner decision, 2026-09-27).

**Gates.** DG006 (menu cap), DG012 (what voids a qualification), DG015 (no schema on Pick), DG019 (capsule order), DG020 (effort table,
from E12), DG021 (adaptive K), DG022 (same-model effort re-run), DG023 (fixed tool set per mode), DG024 (fixed cloud schemas), DG025
(cloud capsule budget and cache minimum), DG026 (candidate diversity without temperature), DG027 (warm-first fan-out); each decided or
explicitly defaulted with the default recorded. The architecture README §8 item 6 (no agent eval in Preview) filed and decided before
Wilco's tool set is frozen. OWQ-19 (a) (the recommended list), OWQ-08 (a) (Economy mode's name via the names table) and OWQ-22 (a)
are answered and applied.

**Exit evidence.**

1. **Workflows with models:** AT-W6 (CI cassette runs make no network call; a cassette miss fails CI), AT-W8 (every generated element
   opens an inspector with its journal record), AT-W10 and AT-W11 re-run with T1 and T3 cassettes; the end-to-end "put some guys near
   the town" test (IntentFill → plan card → `map` → one commit group → provenance → one Ctrl+Z removes everything).
2. **Instruments:** E1–E12 with the three controls, reported per (decision kind, model setup, effort, K policy), never pooled; E12's
   sweep settles doc 40 R6 and R7 and feeds DG020 and DG021.
3. **Token economy CI** (doc 40 §7): golden prefix bytes per decision kind; prefix stability across a namespace; each capsule within its
   shape budget + 5 %; a replayed campaign within ± 5 % of its recorded calls and tokens; zero model calls when resuming settled entries;
   cache fields on the wire per provider adapter; a prompt lint for cost-inflating phrases; price-table checks (no price in Rust code,
   every model dated, the 60-day chip).
4. **Safety:** injection fixtures (E11) with zero violations; hidden Unicode rendered visibly; the `AgentTool` × `AgentEffect` table;
   no agent tool can start a download or launch Preview; with no provider configured, the full suite passes and no network traffic occurs
   (MAT10's editor-side half); MAT1 (prompts naming absent mods admit zero classes outside the catalog).
5. **Weak-model proofs:** PAT9 ("the sniper on the church roof, prone, holding": only typed proposals, zero model-written init text),
   31-AT5 (an ambush with artillery from module and rule proposals only), 33-AT10 (a 3–9B tutor makes zero engine claims absent from
   entries, against the template-only baseline).
6. **Local inference:** SP-13's exit criteria met (S1 ≥ 99.5 % parse-and-validate; S2 50/50 cycles and 0 orphans after 10 forced kills;
   S4 resume 10/10, tamper rejected, atomic install; S5 byte-identical chat templates); download resume, hash and atomic-install tests;
   nothing labelled "runs on 8 GB" until the harness workload passes on the 8 GB reference machine (doc 13 §11).
7. **Qualification records** for the doc 44 models on at least three reference machines (an NVIDIA desktop, an AMD or Intel iGPU
   laptop, a CPU-only machine), shown as "spike-checked" badges with links to their evidence.
8. **Headline:** campaign-from-brief with a T1 local model on reference hardware yields a valid campaign (E10 = 100 %) with zero
   clobbers (E9); timings recorded as evidence for doc 29 AC18's later "≤ 30 min on T1" target.

**Parallel lanes.** D (providers, net, Model Manager, decide, evals); B (Wilco panel, plan card and run panel cost UX, Model Manager
UI); G (flow stages with models); E (cards for model steps, one per rule-bearing Fill field); F (the DG block above); C (model unload
before launch).

**Integration items.** I40-14, I40-25, I42-25 (model part), I34-13, I34-21 (`/` dispatch), I34-25, I36-21 (explain mode), I36-25
(model part; follow-up workflow), I35-19 (outcome-matrix builder, if in scope), I35-26 and I36-26 (model use).

## v1.0 Hardening and release

**Goal.** Harden M1–M6 into the release D004 describes, with nothing new in scope except what closes a v1 gap.

**Scope.** Bug fixing and performance against ui-shell §11; installers per OS; the accessibility pass (AccessKit on classic controls,
keyboard entry everywhere, reduced motion, text alternatives for demos); Standing Orders and Drill track A content complete in English
(OWQ-14 (a)); the minimal headless CLI (lint, compile/export, round-trip check, golden-journal replay; no agent; OWQ-14 (a)); the MCP
server (OWQ-15 (a)); security review of every edge crate; the legal review doc 02 asks for before 1.0.

**Gates.** OWQ-01 (b)'s wording (doc 02's draft plus the explicit coverage list) in `NOTICE`; OWQ-02 (a) applied; the OWQ-13 (a) and
OWQ-14 (a) scope met; DG002/OWQ-07 applied to every user-facing surface; OWQ-10's letter answered or a documented decision to proceed.

**Exit evidence (the definition of done in the roadmap's §7, in detail).**

1. **Faithful editor:** doc 09 M1–M13 parity scripts green; byte-identical save of unchanged missions on synthetic fixtures; an opt-in
   local corpus report with zero unexplained differences (hashes and counts only); PAT1, PAT14; kernel invariants and the one-action-one-
   undo family; Easy/Advanced with relabels (D029).
2. **Preview:** manual verification notes per supported OS for strict Preview from unsaved edits, Validate, from camera, Intro/Outro
   and the campaign prologue on Remastered and CE; export-and-open on 1.99; MAT12.
3. **Wilco:** off by default with no provider and no network (test); M6's weak-model proofs (PAT9, 31-AT5) and the headline campaign run
   re-run on the release build; cost UX present; E9 zero clobbers.
4. **Campaign flow:** E10 = 100 % with and without a model; Preserve import byte-identical; AT-W8 and AC12 on the Grey Heron fixture.
5. **Moderated sessions** (targets set after the first study; they gate usability claims, not CI): 33-AT8 (newcomers finish Drill
   A1–A6 in ≤ 15 min of active building; proposed bar ≥ 6 of 8), 33-AT9 (veterans test out of track A in ≤ 5 min), PAT15 (each
   attribute intent in ≤ 2 steps without code), 31-AT1's newcomer session, and doc 25 E10's human-panel columns.
6. **Housekeeping:** CI green on three OSes; fuzz nightly clean over the release window; `CODE-INDEX.md` current; no `todo` row left in an
   upstream-test area whose crate shipped without a recorded reason; the engine-requests register updated with every limitation met.

**Integration items.** I34-02 (legal review, the IC D051 comparison folded into doc 02).

## Verification notes

### Roadmap baseline (2026-09-27)

- Built from architecture README §6–§7 and Appendix A; agent-runtime §3–§13; extensibility §3–§10; validation-and-lints §10–§11;
  testing-strategy §6–§11; docs 13 §11, 19 §9, 22 §7.1, 25 §4 and §11, 29 §8, 31 §10, 33 §9, 37 §11, 38 §10, 40 §6–§7, 42 §8, 44 §5.
- The module list in M5 is doc 31 §10 L1–L2's list; which modules ship is OWQ-14's call.

### Owner answers folded (2026-09-27)

- The owner's answers of 2026-09-27 now stand in M4 (OWQ-08, OWQ-14, OWQ-15, OWQ-16/DG014, OWQ-17 items 1 and 3), M5 (OWQ-06, OWQ-13,
  OWQ-14, OWQ-22), M6 (OWQ-08, OWQ-19, OWQ-22, and the local-runtime decision in D022's amendment note) and v1.0 (OWQ-01, OWQ-02,
  OWQ-07, OWQ-10, OWQ-13, OWQ-14, OWQ-15). The M5 module list is the wave-1 modules whose probes pass on `Cwr` (OWQ-14 (a)). The only
  added item is the install hand-off button in M4's missing-mod card (a placement proposal); no other milestone content moved.

### Consistency review of the owner answers (2026-09-27)

- M6's Model Manager bullet now states OWQ-19 (a) in full (OSI licences with no field-of-use limit, and qualified) and cites D037.
  The v1 CLI of OWQ-14 (a) and M6's `plotroom qualify` are not yet reconciled: architecture README §8 item 11. No milestone content
  moved.
