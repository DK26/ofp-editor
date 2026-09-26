# Iron Curtain Design Docs: AI-Editor and Creator-Tooling Ideas for the OFP/CWA Mission Editor

> Research note for the `ofp-editor` project (standalone Rust re-implementation of the
> *Arma: Cold War Assault* / *Operation Flashpoint* mission editor with a built-in AI "harness agent").
> Written 2026-09-26. This file is meant to be read on its own.

**Citation aliases** (mechanical prefix substitution; every alias expands to `owner/repo@sha:`):

| Alias | Expands to | What it is |
|---|---|---|
| `ICD:` | `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:` | Design docs (mdBook) of *Iron Curtain* (IC), the user's Red Alert-style RTS engine project |
| `IC:` | `iron-curtain-engine/iron-curtain@7b7fac7fa5:` | IC's Rust implementation repo |
| `CWR:` | `BohemiaInteractive/CWR@ffc61838b7:` | Bohemia's released CWA Remastered engine source ("Poseidon") |

**Epistemic tags:** **[V]** checked against the cited file or URL. **[IC-claim]** stated by the IC docs and not checked independently. **[I]** my inference or recommendation. **[U]** unknown or could not be verified.

---

## TL;DR

- **The IC material is design only.** IC's own index calls every LLM feature "design-stage only (no playable build yet)" and "experimental" [V: `ICD:src/LLM-MODES.md#L10`]. IC's code repo lists `ic-llm` and `ic-editor` under "Planned But Not Yet Implemented" [V: `IC:CODE-INDEX.md#L171-L184`]. What follows is untested design input, not proven practice.
- **Idea #1 to adopt: the agent is just another client of the editor's command registry.** IC's rule is "if the GUI can't do it, the LLM can't do it." Tool calls go through "the same validation and undo/redo pipeline as GUI actions — no special path." The tool manifest is generated from the command registry. The agent proposes, the editor shows a preview, and the user confirms. Autonomous mode is an opt-in toggle [V: `ICD:src/decisions/09f/D016/D016-factions-editor-tools.md#L160-L192`].
- **Reliability comes from constraining the output, not from the model.** Three pieces work together. (1) Templates and compositions whose parameters are checked against a schema make the LLM "a smart form-filler, not an unconstrained code generator" [V: `ICD:src/modding/tera-templating.md#L150-L158`]. (2) A validator runs in several stages. (3) Only the broken section is regenerated, at most 3 times, with the error text fed back to the model [V: `ICD:research/llm-generation-schemas.md#L1124-L1336`].
- **Provider model: bring-your-own-LLM ("BYOLLM") sets the ceiling and a local floor makes everything work.** Tasks are routed to different models. Prompt Strategy Profiles adapt prompts per model. Capability probes and a prompt test harness check a model before it is used. Exported configs never include keys [V: `ICD:src/decisions/09f/D047-llm-config.md`]. **Skip IC's "Cloud OAuth" tier.** Anthropic's published terms forbid third-party apps from offering Claude.ai login [V: https://code.claude.com/docs/en/legal-and-compliance]. OpenAI and Google were not checked [U].
- **Effort levels map to IC's Prompt Strategy Profiles plus repair budgets.** The profiles are `LocalCompact`, `LocalStepwise` (plan → validate → emit) and `CloudRich` [V: `D047#L245-L269`]. This is the closest IC analogue to the user's "effort level + workflows" idea [I].
- **Give the LLM its own metadata.** IC allows an optional `llm:` block (summary, role, strengths, weaknesses, tactical notes, counters) on any resource; its tag fields use a controlled vocabulary [V: `ICD:src/modding/llm-metadata.md#L21-L73`]. For OFP this becomes a per-class catalog. Class names come from the user's installed game at runtime. The descriptions are ours [I].
- **Dialogue and briefings.** Build characters from traits, flaw, desire, fear and speech style. Use story-style presets with explicit rules. Keep a compressed "campaign context" document as the model's memory. Always produce text first; voice (TTS) is an optional extra [V: `ICD:src/decisions/09f/D016/D016-characters-output.md`, `D016-cinematics-media.md#L239`].
- **Treat everything the LLM generates as untrusted mod content.** Validate it, scan scripts, apply cumulative budgets, and show a summary before the actual game is launched with it. Prompt logging is opt-in and can be stripped [V: `ICD:src/security/vulns-infrastructure.md#L333-L361`, `ICD:src/decisions/09d/D073-llm-exhibition-modes.md#L253-L262`].
- **Defer the "skill library" (a Voyager-style store of verified examples in SQLite FTS5) to v2.** In v1, just record the outputs the user accepted [V: `ICD:src/decisions/09f/D057-llm-skill-library.md`; I for the phasing].
- **Adopt IC's project-process tools:** decision records (`Dxxx`) with "Decision Capsules", a retrieval index for LLMs (`LLM-INDEX`), `CODE-INDEX.md`, a design-gap request folder (in use in IC's code repo), and Feature/Screen/Scenario specs [V: see §16].

---

## 1. What IC is and where its AI-editor ideas live

Iron Curtain is the user's Rust (Bevy) re-imagining of classic C&C. Its design docs are an mdBook: numbered chapters plus one file per decision under `src/decisions/09*/Dxxx-*.md`. The scenario editor (D038) is **explicitly modeled on the OFP mission editor and Arma 3's Eden editor** [V: `ICD:src/decisions/09f/D038/D038-core-architecture.md#L27-L39`]. That makes IC's non-AI editor ideas relevant to us as well.

| Topic | Canonical file(s) | Relevance to us |
|---|---|---|
| Human overview of all LLM "modes" | `src/LLM-MODES.md` | High: the framing and ground rules |
| Retrieval map for agents | `src/LLM-INDEX.md` | High: a process idea |
| LLM missions, BYOLLM, editor tool bindings | `src/decisions/09f/D016-llm-missions.md` + 7 sub-files under `D016/` | **Highest** |
| Scenario editor (OFP/Eden-inspired) | `src/decisions/09f/D038-scenario-editor.md` + 6 sub-files | High: editor UX and validation |
| Asset Studio (optional agentic layer) | `src/decisions/09f/D040-asset-studio.md` | Medium: provenance metadata |
| LLM-enhanced AI (orchestrator) | `src/decisions/09d/D044-llm-ai.md` | Low/medium: the "LLM advises, deterministic code executes" pattern |
| LLM config manager | `src/decisions/09f/D047-llm-config.md` | **Highest**: provider model |
| Skill library | `src/decisions/09f/D057-llm-skill-library.md` | Medium: v2 |
| External tool API / MCP | `src/decisions/09f/D071-external-tool-api.md` | Medium/high: editor as MCP server |
| LLM-readable metadata | `src/modding/llm-metadata.md` | High |
| Tera templating + LLM | `src/modding/tera-templating.md`, `tera-templating-advanced.md` | High |
| Setup guide (player-facing) | `src/player-flow/llm-setup-guide.md` | Medium: UX copy, troubleshooting table |
| Security | `src/security/vulns-infrastructure.md` (V40), `vulns-edge-cases-infra.md` (V57, V61) | High |
| Supporting research | `research/llm-generation-schemas.md`, `byollm-implementation-spec.md`, `cpu-llm-model-evaluation.md`, `pure-rust-inference-feasibility.md` | High: concrete schemas and prompts |

---

## 2. IC's ground rules and how they translate to our editor

IC applies six rules to every LLM feature; five are relevant here (the sixth, "No ranked assistance", concerns multiplayer) [V: `ICD:src/LLM-MODES.md#L18-L25`]:

| IC rule | IC wording (abridged) | Translation for `ofp-editor` [I] |
|---|---|---|
| Optional, never required | "game and SDK are designed to work fully without any LLM configured" | Every editor feature works with the agent off. The agent panel is an add-on, never on the critical path. |
| BYOLLM with a built-in floor | four provider tiers; "IC Built-in provides a functional baseline; BYOLLM provides the ceiling" | Same idea: a local or embedded option so nothing needs an account, plus BYO cloud or local for quality. See §3. |
| Determinism preserved | the sim "never performs LLM or network I/O" | Our equivalent: **the mission file is the only output**. The agent never talks to the running game. Preview launches the game with a normal mission folder. |
| Privacy and disclosure | prompt capture opt-in; built-in models never leave the device | Prompt and transcript logging is opt-in. Show clearly which provider receives the mission context. |
| Standard outputs | "Generated content is standard YAML/Lua/assets, not opaque engine-only blobs" | Output is a plain `mission.sqm`, SQS/SQF, `briefing.html`, `stringtable.csv`, byte-for-byte like hand-made content. Formats: see sibling doc `04-mission-data-model-and-formats.md`. |

D016 puts the last point as "**LLM is for creation, not for play**": a generated campaign stays playable after LLM access is lost, and hand-editing needs no LLM [V: `ICD:src/decisions/09f/D016/D016-world-assets-multiplayer.md#L134-L143`]. D016 also states "there is no 'generative campaign runtime'" [V: `D016-characters-output.md#L424`]. This fits our standalone design exactly [I].

IC also records a **positioning warning**: "The word 'AI' in gaming contexts attracts immediate hostility from a significant audience segment". It therefore treats LLM features as "a quiet power-user capability, not a project headline" [IC-claim: `ICD:src/decisions/09f/D016/D016-overview-generation.md#L21`]. The OFP community is an older modding community, so the same caution probably applies [I]. Lead with "faithful editor, standalone, undo, preview"; present the agent as an opt-in panel.

---

## 3. Provider and configuration model (D016 BYOLLM + D047 + setup guide)

### 3.1 What IC designed

**Four provider tiers, all behind one `LlmProvider` trait** [V: `ICD:src/decisions/09f/D047-llm-config.md#L24-L152`]:

| Tier | Name | Auth | IC design notes |
|---|---|---|---|
| 1 | IC Built-in | none | Embedded pure-Rust CPU runtime (`candle-core`, `candle-transformers`, `tokenizers`), in-process, no sidecar. **Weights are not in the base install**; they are downloaded as "model packs". GGUF Q4_K_M, target 8 GB RAM. IC picks and validates the checkpoint; users enable a *capability*, not a model (`#L28-L39`, `#L101-L102`). |
| 2 | Cloud OAuth | browser login | "Sign in with OpenAI/Anthropic/Google" (`#L107-L120`). |
| 3 | Cloud API key | pasted key | Any OpenAI-compatible endpoint plus Anthropic Messages API. Keys encrypted at rest and never exported (`#L122-L131`). |
| 4 | Local external | endpoint URL | Ollama, LM Studio, vLLM, etc. Auto-detects `localhost:11434` (Ollama) and `localhost:1234` (LM Studio) (`#L133-L141`). |

The other D047 building blocks:

- **Task routing.** Each task (mission generation, briefings, coaching, …) is assigned a provider. The default advice is local for high-frequency or latency-sensitive tasks and cloud for one-shot creative work [V: `D047#L199-L211`; `ICD:src/player-flow/llm-setup-guide.md#L225-L252`].
- **Prompt Strategy Profiles.** `EmbeddedCompact`, `CloudRich`, `CloudStructuredJson`, `LocalCompact`, `LocalStructured`, `LocalStepwise` ("task decomposition into multiple smaller calls (plan → validate → emit)"), and `Custom`. An `Auto` mode picks one from provider type, probe results and task type; the user can override per provider or per task [V: `D047#L245-L269`]. The design rule behind this: "Prompt behavior = provider transport + chat template + decoding settings + prompt strategy profile, not just 'the text of the prompt'". A bad local result may really be a template mismatch [V: `D016-overview-generation.md#L41-L47`].
- **Capability probe.** Runs only when the user asks, and results are cached per (endpoint, model, fingerprint). It checks chat-template compatibility, JSON reliability, effective context, latency, tool-call support and stop-token quirks. It never uses personal data, and its results are advisory [V: `D047#L271-L287`].
- **Prompt test harness.** Smoke test, structured-output test, task-sample test, and a latency and cost estimate. It shows the chosen profile, chat template and decoding settings, parser diagnostics, and a recommendation [V: `D047#L289-L306`].
- **Shareable configs without keys.** A YAML export carries providers, profiles, routing and performance notes. Endpoints can be left out, and on import everything is treated as advisory [V: `D047#L308-L372`].
- **Model-pack manifest.** `model_pack.toml` records id, roles, SPDX license, RAM requirements, format and quantization, context window, sha256, and the eval suite with its pass rate [V: `D047#L73-L99`].
- **Credential store.** API keys are AES-256-GCM blobs. The data key lives in the OS keyring (DPAPI, Keychain or Secret Service) or is derived with Argon2id from a vault passphrase. There is deliberately **no machine-derived key fallback**, which IC calls "security theater in an open-source project". Secrets use `zeroize`, are never exported, and a failed decryption asks the user to re-enter the key [V: `ICD:src/security/vulns-edge-cases-infra.md#L263-L306`].
- **Setup UX.** A four-option comparison table (cost, speed, privacy, difficulty), per-provider step-by-step guides, a troubleshooting table (connection refused, 401, 429, model not found, timeout), and a credential-recovery flow [V: `ICD:src/player-flow/llm-setup-guide.md#L11-L20`, `#L269-L308`].

The trait sketch in IC's implementation spec is **text in, text out**. It has `chat_complete`, `health_check`, `context_window`, and `ResponseFormat {Text, Json, Yaml}`, with no tool/function-calling, streaming or cancellation fields [V: `ICD:research/byollm-implementation-spec.md#L55-L138`]. IC also keeps its LLM crate from importing sim or AI crates: "`ic-llm` does NOT import `ic-sim` or `ic-ai`" [V: `#L53`].

### 3.2 Corrections and staleness to watch before reusing this

| Issue | Status |
|---|---|
| **Tier 2 "Sign in with Anthropic" is not permitted.** Anthropic: "Anthropic does not permit third-party developers to offer Claude.ai login into their own applications, or to route requests through Free, Pro, or Max plan credentials on behalf of their users." Developers "should use API key authentication", and "may not collect, store, or intermediate Claude.ai credentials or session tokens". | [V: https://code.claude.com/docs/en/legal-and-compliance] |
| OAuth for OpenAI or Google API access by third-party desktop apps | [U]: not verified; do not design around it |
| IC's example cloud model IDs (`gpt-4o`, `gpt-4o-mini`, `o4-mini`, `claude-sonnet-4-20250514`, `claude-haiku-4-5-20251001`, `gemini-2.0-flash`, `gemini-2.5-pro`; local `llama3.2`) and prices | Dated: they come from 2025, the newest being `claude-haiku-4-5-20251001` [V: `ICD:src/decisions/09f/D047-llm-config.md#L174-L197`, `ICD:src/player-flow/llm-setup-guide.md#L103-L219`]. Only IC's CPU model evaluation carries an explicit date, "reflects models available as of mid-2025" [V: `ICD:research/cpu-llm-model-evaluation.md#L470-L484`]. **Never hardcode model IDs.** Query the provider's model list at runtime [I]. |
| IC's Tier 1 picks (Qwen2.5-1.5B for JSON, Phi-4-mini for generation) | Reasoning in `cpu-llm-model-evaluation.md#L457-L468` [IC-claim]. The benchmark figures are IC's and were not re-verified. Current model choice belongs to another research note. |
| `candle` can run quantized GGUF models of the Qwen and Phi families and is MIT/Apache-2.0 | [V: README says "Quantization support using the llama.cpp quantized types" and lists GGUF Qwen3 MoE; the model tree has `quantized_qwen2.rs`, `quantized_qwen3.rs`, `quantized_phi.rs`, `quantized_phi3.rs` (https://github.com/huggingface/candle/tree/main/candle-transformers/src/models, `main` as of 2026-09-26)]. Whether its CPU speed is good enough for our use is [U]. |
| A text-only provider trait is not enough for a harness agent | [I]: we need native tool calling, streaming, cancellation, and token/usage reporting. See sibling docs `10-harness-codex-and-opencode.md` and `11-harness-pi-tinyagent-deepseek.md` for harness designs. |

### 3.3 Recommended adaptation [I]

1. **Three tiers in v1:**
   - **Local external** (OpenAI-compatible HTTP: Ollama, LM Studio, llama.cpp server, vLLM).
   - **Cloud API key** (OpenAI-compatible + Anthropic Messages + others via a crate such as `rig`, researched separately).
   - **Built-in** (model pack downloaded on demand, never in the installer; an in-process or sidecar runtime decided later). Skip OAuth.
2. **Task routing from day one**, with at least three tasks: `agent` (tool-calling), `writer` (dialogue and briefings), `summarize/compress` (context compaction). Then a user can send dialogue to a strong cloud model while a small local model does the editing [I].
3. **Prompt Strategy Profiles ≈ effort levels** (see §4).
4. Copy the **probe and test harness** idea. It is the main tool for supporting "bring your own model" [I].
5. Copy the **credential store** rules: keyring via the `keyring` crate, no machine-derived fallback, `zeroize`, never exported, never written into mission folders [I].
6. Copy the **model-pack manifest** with license, sha256 and eval pass rate, if we ever ship weights [I].

---

## 4. The "LLM modes" concept → our agent modes, effort levels and workflows

`LLM-MODES.md` lists features **by audience** (players, spectators, creators, tool developers) and **by mode**. Each mode is an opt-in surface with explicit trust rules [V: `ICD:src/LLM-MODES.md#L29-L57`]. Only the creator modes matter to us:

- **(7) Replay-to-scenario narrative layer.** Mechanical extraction works with no LLM; an optional LLM adds briefings, objective wording and dialogue [V: `#L179-L195`; `ICD:src/decisions/09f/D038/D038-game-master-replay-multiplayer.md#L42-L71`].
- **(9) LLM-callable editor tool bindings** [V: `#L209-L219`].
- **(11) Configuration manager** and **(12) skill library** as infrastructure [V: `#L237-L272`].

IC has no user-facing **"effort level"**. The closest mechanisms are these (all [V]):

- the profile's `few_shot_examples`, `schema_mode` (`Relaxed`, `Simplified`, `Strict`) and `retry_repair_passes` [`D047#L509-L524`];
- `LocalStepwise` decomposition [`D047#L255`];
- the regeneration budget: 3 tries per section, then 1 full regeneration, then a user choice [`ICD:research/llm-generation-schemas.md#L1329-L1336`].

**Proposed mapping [I]:**

| Our effort level | Pipeline | Built from |
|---|---|---|
| Quick | 1 model call; template or form fill only; 1 repair pass; no self-review | `LocalCompact` + tera "form-filler" |
| Standard | plan → tool calls → validate → up to 2 repair passes → diff preview | `LocalStepwise` / `CloudStructuredJson` |
| Thorough | plan → critique plan → emit → validate → self-review against a checklist → up to 3 section repairs → optional alternatives | `CloudRich` + the IC regeneration policy |

**Workflows.** IC's nearest concepts are:

- MCP "Prompts (templated interactions)" [V: `ICD:src/decisions/09f/D071-external-tool-api.md#L273-L276`];
- mission and scene templates [§6];
- data-driven YAML "guided tours" for the SDK [V: `ICD:src/decisions/09f/D038/D038-onboarding-platform-export.md#L95-L124`].

We could define a workflow as a YAML file: named steps, each a prompt template plus the allowed tool subset, with gates and validator checkpoints. Examples: "Generate briefing from placed objectives" or "Add patrol to selected group" [I].

**Autonomy levels [I]**, following D016's "Not autonomous by default … Autonomous mode (accept-all) is an opt-in toggle" [V: `D016-factions-editor-tools.md#L184-L188`]:

| Level | Behavior |
|---|---|
| Ask | read-only tools only |
| Propose | produce a change set and show a diff; the user applies it |
| Apply with confirm | the default |
| Auto-apply | opt-in; still one undo group per turn |

---

## 5. Editor tool bindings: the central architectural idea

### 5.1 IC's design [V: `ICD:src/decisions/09f/D016/D016-factions-editor-tools.md#L160-L192`]

- "every GUI action has a programmatic equivalent — this is a D038 design principle."
- The tool layer (1) lists operations as a manifest (name, parameters, return type, description), (2) sends LLM calls "through the same validation and undo/redo pipeline as GUI actions — no special path, no privilege escalation", and (3) returns structured results (success or failure, created IDs, validation issues) so the model can plan multiple steps.
- "The manifest is auto-generated from the editor's command registry — no manual sync needed." It should be designed together with the command registry, before LLM work starts (`#L192`).
- "Not a new editor … If the GUI can't do it, the LLM can't do it."
- D038 repeats this: the command registry "should be designed with this future integration in mind" [V: `ICD:src/decisions/09f/D038/D038-onboarding-platform-export.md#L536`].
- IC cites UnrealAI, a UE5 plugin "announced February 2026" with 100+ tool bindings, as prior art [IC-claim at `D016-factions-editor-tools.md#L190`, **not verified**; web search was unavailable for this note and for its fact-check] (unverified).

### 5.2 Applied to OFP/CWA [I, plus V where cited]

The original editor's data model is small and well bounded. The editor has exactly six insert modes, `IMUnits`, `IMGroups`, `IMSensors` (triggers), `IMWaypoints`, `IMSynchronize`, `IMMarkers` [V: `CWR:engine/Poseidon/UI/Map/UIMap.hpp#L564-L573`]. `ArcadeTemplate` serializes each group as `side`, `Vehicles`, `Waypoints`, `Sensors` [V: `CWR:engine/Poseidon/AI/ArcadeTemplate.cpp#L1460-L1467`]. At template level it writes `addOns` and `addOnsAuto` (computed by `ScanRequiredAddons()`), the `showHUD`/`showMap`/`showWatch`/`showCompass`/`showNotepad`/`showGPS` flags and `randomSeed`, then `Intel`, `Groups`, `Vehicles` (empty vehicles), `Markers`, `Sensors`. `CheckSynchro(); // remove invalid synchronizations` runs on save and again on load [V: `CWR:engine/Poseidon/AI/ArcadeTemplate.cpp#L1934-L1990`]. A `mission.sqm` holds four such templates: `Mission`, `Intro`, `OutroWin`, `OutroLoose` [V: `CWR:engine/Poseidon/UI/Map/UIMapExtDisplay.cpp#L99-L121`]. Full key lists are in sibling doc `04-mission-data-model-and-formats.md`.

A closed command set therefore covers the whole editor:

| Editor mode (F-key, per IC's OFP mapping table [V: `D038-core-architecture.md#L88-L103`]) | Example typed commands |
|---|---|
| F1 Units | `PlaceUnit{class, side, pos, azimuth, rank, skill, probability, condition, init}`, `SetUnitAttr`, `Delete` |
| F2 Groups | `CreateGroup`, `JoinGroup`, `SetLeader` |
| F3 Triggers | `PlaceTrigger{area, activation, repeat, timeout_min/mid/max, condition, on_act, type}` |
| F4 Waypoints | `AddWaypoint{group, index, type, pos, behaviour, combat_mode, speed, formation, timeout}` |
| F5 Sync | `Synchronize{a, b}` (the engine itself prunes invalid synchronizations on save and load, so validate before emitting) |
| F6 Markers | `PlaceMarker{name, type, shape, text, color}` |
| Intel / mission | `SetIntel{weather, time, fog, ...}`, `SetMissionFlags{show_hud, show_map, ...}`, `SetBriefing`, `SetStringtableEntry`, `WriteScript{path, text}`; every mutating command names its target template (`Mission`/`Intro`/`OutroWin`/`OutroLoose`); the engine recomputes `addOnsAuto` on save, so the agent should not hand-edit add-on lists |
| Read-only | `ListClasses{filter}`, `DescribeSelection`, `Validate{preset}`, `FindObjects{query}` |

**Implementation sketch [I]:**

- One `EditorCommand` enum in a core crate. Each variant is a typed struct with newtype IDs (per our AGENTS rules).
- A JSON Schema is derived for the manifest, for example with `schemars`. This fulfils the "auto-generated manifest" idea and doubles as the "TypeSafe" path the user mentioned: the model can only emit schema-valid commands.
- `apply(&mut Mission, cmd) -> Result<Outcome, EditError>` is the **same function** the GUI calls.
- One agent turn becomes one undo group.
- The preview is a **semantic diff**. IC's `SemanticChange {AddObject, RemoveObject, ModifyField, RenameObject, MoveObject, RewireReference}` [V: `ICD:src/decisions/09f/D038/D038-core-architecture.md#L352-L363`] is exactly the right format for "here is what the agent wants to change", rendered in the diff pane and on the map.
- Stable content IDs plus canonical serialization make renames diff as edits rather than delete-and-add (`#L324-L327`). This matters for both Git and agent review.

### 5.3 "LLM advises, deterministic code executes"

D044 wraps a normal AI in an `LlmOrchestratorAi`. The LLM returns a `StrategicPlan`, which is translated into `set_parameter()` calls; the inner AI does the tick-level work, so there is "no LLM latency in the hot path" [V: `ICD:src/decisions/09d/D044-llm-ai.md#L18-L61`]. The Puppet Master layer generalizes this into a trait whose implementations can be an LLM, a human, or an algorithm [V: `ICD:src/decisions/09d/D043/commanders-and-puppet-masters.md#L134-L164`]. D044 also routes non-text custom models (WASM, local HTTP, native) through the same trait [V: `D044#L333-L349`].

**For us [I]:** define a `Planner`/`IntentSource` trait whose output is `Vec<EditorCommand>` or a template invocation. Then an LLM, a small local model, a rule-based macro, or a future "decision model" are interchangeable. The IC docs never mention the public decision models the user named (Jev, Kev, CLM, Laya) [U]. The trait just keeps that option open. Sibling doc `16-decision-models.md` covers those models and the evidence we require before putting one in front of the generative model.

---

## 6. Templates + LLM (Tera, scene templates, compositions)

### 6.1 IC's design [V]

- **Tera** is "a Rust-native Jinja2-compatible template engine", load-time only, with deterministic output [`ICD:src/modding/tera-templating.md#L3-L21`]. Upstream describes Tera as "a template engine for Rust based on Jinja2/Django", MIT license [V: https://github.com/Keats/tera]. Tera 2 is now current (crates.io newest 2.4.0, 2026-09-11, with a v1 migration guide), so IC's `Tera::new(...)` sketch may reflect the v1 API [V: https://crates.io/api/v1/crates/tera; API impact I].
- **Mission template** layout: `template.yaml` (Tera), `triggers.lua.tera`, `schema.yaml` (typed parameters with enum/range/default/description), preview image, README [`#L38-L94`]. Rendering merges defaults, checks types, ranges and enums, *then* renders [`#L123-L148`].
- **LLM + templates:** the LLM selects a template, fills the parameters against `schema.yaml`, the schema catches hallucinated values, and templates are chained for campaigns. "The LLM becomes a smart form-filler, not an unconstrained code generator" [`#L150-L158`].
- **Scene templates** are "inspired by Operation Flashpoint / ArmA's mission editor": sub-mission building blocks (ambush, patrol, convoy_escort, defend_position, reinforcements, extraction, timed_objective, …) with pre-tested logic [`#L162-L196`]. When composed, each scene's parameters are validated, its scripts rendered, and its functions namespaced into one mission script. "A 'convoy escort with two ambushes and a base-building finale' is 3 scene template references with ~15 parameters total, not 200 lines of handwritten Lua" [`#L484-L539`].
- **Compositions** (Eden-style saved clusters of entities, triggers, modules and connections) *are* scene templates in visual form: "a composition saved in the editor can be loaded as a scene template by Lua/LLM, and vice versa" [`ICD:src/decisions/09f/D038/D038-triggers-waypoints.md#L268-L305`].
- Prompt templates themselves are moddable data (`llm/prompts/mission_generation.yaml`, Jinja2-style) [`ICD:research/llm-generation-schemas.md#L1340-L1342`].

### 6.2 Applied to OFP [I]

- **This is the highest-leverage way to use small models.** Dialogue scripts, patrol loops, ambush triggers and reinforcement waves become **composition templates**: a `mission.sqm` fragment (groups, waypoints, triggers, markers) plus SQS/SQF snippets plus a typed parameter schema. The agent picks a template and fills parameters. Our validator and the template renderer do the rest.
- Keep one on-disk format for "composition" (user-saved from the GUI) and "template" (parameterized). This matches IC's rule and gives us a "save selection as composition" feature that doubles as agent knowledge.
- **Templating engine:** Tera (MIT, Jinja2-style) fits; `minijinja` is a smaller alternative [U: not evaluated here]. Keep rendering pure (`&str` in, `String` out) per our parser rules.
- **Prompts are data too.** Put system prompts and workflow prompts in versioned template files, not in Rust string literals.

---

## 7. LLM-facing metadata (`llm-metadata.md`)

### 7.1 IC's design [V: `ICD:src/modding/llm-metadata.md`]

- Every resource can carry an optional `llm:` block: `summary`, `role[]`, `strengths[]`, `weaknesses[]`, `tactical_notes`, `counters[]`, `countered_by[]`. Maps use `gameplay_tags` [`#L21-L48`].
- Design rules [`#L66-L73`]:
  - always optional;
  - human-written preferred, LLM-generated acceptable after review;
  - **tags use a controlled vocabulary** ("prevents tag drift");
  - free-text `tactical_notes` holds the nuance;
  - metadata lives *in the same file*, not in a sidecar.
- **`ai_usage` consent**, separate from the license: `allow` / `metadata_only` (default) / `deny`. Rationale: a license governs humans, `ai_usage` governs automated agents [`#L75-L91`]. Linting warns when `allow` has no metadata [`#L146`].
- Curated **composition sets**: pre-vetted bundles an LLM can start from [`#L190-L222`].
- IC's error messages are also written for LLMs. "An LLM reading a single error message should be able to pinpoint the root cause and suggest a fix," and there are tests on error text [V: `ICD:src/16-CODING-STANDARDS.md#L270-L272`, `#L598`].

### 7.2 Applied to OFP [I]

- **Class catalog.** At runtime we enumerate `CfgVehicles`, `CfgWeapons`, islands and so on from the user's installed game or addons. That data is never committed, per our "no proprietary game data" rule. We join it with a **hand-written `llm:` overlay** keyed by class name ("T72 — Soviet MBT; strong vs armor; weak vs AT infantry in towns"). The overlay is our own text and ships as `data/llm/classes/*.toml`.
- The agent's `ListClasses{filter: role=anti_armor, side=east}` tool reads this catalog. Stage 2 of the validator (§8) rejects unknown class names and suggests the nearest match.
- **Controlled vocabulary** for roles, tags and waypoint semantics. Put it in one file used by the prompts, the tools and the validator.
- `ai_usage` matters only if we ever add a community content hub. Until then it can be skipped [I].
- Adopt **LLM-readable validator messages** as a coding rule: object ID, field path, why, and a suggested fix. The repair loop needs these (§8).

---

## 8. Validating and securing generated content

### 8.1 IC's validator and repair loop [V: `ICD:research/llm-generation-schemas.md#L1124-L1336`]

Seven stages:

1. Parse, including required fields.
2. Game-module compatibility: unit and structure types against the registry, with Levenshtein "closest valid type" suggestions.
3. Reference integrity: zones, targets, outcome conditions.
4. Objective reachability, via a simplified path graph.
5. Script validation: syntax, **AST scan for disallowed calls**, referenced IDs, flag names.
6. Outcome coverage: a victory path exists, and every primary-objective failure is covered.
7. Non-blocking quality warnings: force balance, resources, unused characters, trigger count.

The result carries `SectionValidity` flags, so **only broken sections are regenerated**. The budget is at most 3 tries per section, then 1 full regeneration, then a user-facing fallback: "[Try Again] [Skip to Next Mission] [Edit Manually]". Warnings never trigger regeneration. The repair prompt lists each error and marks the valid sections "VALID — do not regenerate" (§12 of that file, headings at `#L2391-L2510`).

D016's faction generator follows the same pattern: automated checks with no LLM, "If validation fails → feedback to LLM for iteration (up to 3 retries per issue)" [V: `D016-factions-editor-tools.md#L67-L79`].

On the editor side, D038 defines **validation presets** (Quick < 2 s, Publish, Export, …) that share **one implementation between the GUI and the CLI**. The UX is non-blocking: async, cancelable, a "stale" badge instead of forced reruns, and severity levels Error, Warning and Advice, each issue with a location and a one-click focus [V: `ICD:src/decisions/09f/D038/D038-media-validation.md#L364-L442`].

### 8.2 IC's threat model for generated content [V: `ICD:src/security/vulns-infrastructure.md#L333-L361`]

V40 lists four risks:

- **prompt injection**, including via shared seeds;
- **no content filter** (for example "enter your password to unlock the bonus mission");
- **no cumulative limits**;
- **trust ambiguity**.

The mitigations:

- the same validator used for community submissions;
- campaign-level budgets on total spawns, total instructions and map size;
- a local, configurable text filter;
- a **sandboxed preview** that shows "This mission spawns N units, uses N Lua scripts, references N assets", with accept, regenerate or reject;
- LLM output tagged as untrusted mod content that "cannot request elevated capabilities".

### 8.3 Applied to OFP [I]

| Stage | OFP/CWA check |
|---|---|
| Parse | `mission.sqm` round-trips (sibling doc 04, §13 round-trip strategy) |
| Catalog | every `vehicle=` class exists in the runtime catalog, with nearest-match suggestion |
| References | sync IDs, waypoint and trigger links, marker names, `stringtable` keys, script paths all resolve |
| Scripts | SQS/SQF tokenize or parse; referenced global names exist; **flag risky commands** (which ones is [U] — needs an audit of the CWR script command table) |
| Briefing | `briefing.html` stays within the engine's HTML subset (the engine has `CWR:engine/Poseidon/UI/Locale/MissionHtmlLocalization.cpp`; subset described in doc 04 §6) |
| Outcomes | at least one end trigger reachable; lose conditions present (warning) |
| Budgets | units, triggers, script size vs. a "complexity meter" (IC's meter: `D038-core-architecture.md#L243-L261`) |

- Before **Preview launches the real game**, show IC-style summary cards (units, triggers, scripts, external files, anything new since the last preview). The real game runs untrusted scripts. The main realistic risk is probably denial of service (runaway loops or spawns), not system compromise [I]. Any CWR-CE script extensions that touch files or the network would change that [U].
- Treat **text inside the mission** (briefing, `stringtable`, marker text, existing scripts) as **untrusted input to the agent** too. A downloaded mission can carry prompt-injection text [I]. MCP's own spec says tool annotations from untrusted servers "should be considered untrusted" and that hosts must get consent before invoking tools [V: https://modelcontextprotocol.io/specification/latest].
- Pre-preview autosave (IC: "the editor automatically saves a snapshot before entering preview mode") [V: `D038-core-architecture.md#L315`].

---

## 9. Dialogue, briefing and narrative generation

### 9.1 IC's design [V]

- **Character sheet** fields: personality type, 3–5 core traits, **flaw**, **desire**, **fear**, **speech style** ("Concrete voice direction so dialogue sounds like a person, not a bot") [`ICD:src/decisions/09f/D016/D016-characters-output.md#L7-L16`].
- MBTI is used as a "consistency framework … not a horoscope" to keep a character's voice stable across 24 missions [`#L18-L23`].
- **Ensemble rules:** no duplicate personality types; deliberately complementary or opposed pairs [`#L27-L33`].
- **Story-style presets** set voice and structure (C&C Classic, Realistic Military, Political Thriller, …). Each preset carries **explicit numbered rules**, e.g. "Play everything straight", "Make it quotable", "Briefings sell the mission … should end with a question", "Debriefs acknowledge what happened" [`#L52-L95`]. IC requires "C&C Classic"-style system prompts to embed its narrative "pillars" [`ICD:src/13-PHILOSOPHY.md#L343-L348`].
- **Campaign context document** as the model's memory: skeleton, per-mission summaries, character states, flags, narrative threads, arc position. Older missions are compressed by the LLM itself to keep the context in roughly 8K–32K tokens [`#L172-L213`, `#L401`].
- **Intent Interpreter.** Free text ("Soviet campaign where you're a disgraced colonel…") becomes pre-filled structured parameters, each with a confidence, source and explanation, shown as "inferred" badges. A fixed override priority applies: explicit UI choice > explicit text > inference > preset default > global default. Narrative seeds carry what has no dropdown [`D016-overview-generation.md#L87-L161`].
- **Mid-mission radio events and branching dialogues** are ordinary editor data with trigger conditions and mechanical effects (set flag, add objective, reveal area) [`ICD:src/decisions/09f/D016/D016-cinematics-media.md#L7-L92`].
- **Media is a progressive enhancement:** "Text briefings work … Silent radar comms with text work". TTS voice is an optional per-type provider (`VoiceProvider`, with local Piper among the options), and a `VoiceProfile` keeps a character's voice consistent [`#L239`, `#L256-L316`, `#L371-L387`].
- A generated package keeps its **prompts as editable content** ("prompt as mod parameter"): others can adjust them and regenerate individual missions [`ICD:src/decisions/09f/D016/D016-branching-world-campaigns.md#L41-L51`].

### 9.2 Applied to OFP [I]

- A **Cast panel**: per-mission or per-campaign character sheets (name, side, rank, traits, flaw, desire, fear, speech style, optional archetype). The dialogue writer gets these, the selected **style preset** (e.g. "OFP 1985 Cold War realism: understated radio procedure, no heroics"), and a compact **mission context**: objectives, triggers already placed, outcomes. Make the personality typology optional. It is a writing aid, not a science.
- **Output targets:** text lines bound to OFP's radio and chat commands, or `titleText` inside generated SQS, trigger `On Act` fields, and `briefing.html` notes and plans (formats in doc 04). All strings go into `stringtable.csv` keys so missions stay localizable.
- Use the **Intent Interpreter pattern** for "describe your mission" → a pre-filled parameter form with "inferred" badges before any generation.
- **Voice is out of scope for v1.** Keep a provider seam so TTS could be added later.
- **Prompt provenance.** Store prompts in a *separate* sidecar (e.g. `.ofpeditor/`), excluded from PBO export by default. This keeps "prompt as editable content" without leaking private instructions into published missions (see §12).

---

## 10. Skill library (D057) → a "recipe library" later

**IC's design** [V: `ICD:src/decisions/09f/D057-llm-skill-library.md`]:

- A `Skill` is a *verified* reusable LLM output, stored with provenance (source, model, engine version), quality (verification count, success rate, rating, confidence `Tentative`/`Established`/`Proven`), tags and composability [`#L36-L125`].
- Storage is SQLite with an **FTS5** table as the always-available retrieval path and optional embedding BLOBs. "No external vector database" [`#L127-L179`].
- Skills enter prompts as few-shot examples. "The LLM is never forced to use retrieved skills" [`#L237-L301`].
- The lifecycle is discovery → execution → evaluation → candidacy → verification → promotion → retrieval → composition → sharing, plus decay and pruning [`#L346-L370`].
- It is "NOT fine-tuning" and "NOT required" [`#L405-L410`].
- The design is based on Voyager, whose abstract reports "3.3x more unique items, travels 2.3x longer distances, and unlocks key tech tree milestones up to 15.3x faster than prior SOTA" [V: https://arxiv.org/abs/2305.16291].

**Applied to OFP [I]:**

- Our verification signals are weaker than IC's. We do not run the game, so there are no win or loss outcomes. Usable proxies:
  - output passed validation;
  - the user applied it without edits, or with only small edits (measurable from the semantic diff);
  - an explicit thumbs up;
  - optionally, the mission was previewed.
- **v1:** log accepted (prompt, tool calls, diff) triples locally (opt-in) in SQLite with FTS5.
- **v2:** retrieve them as few-shot examples and allow export/import of "recipe packs".
- Design the recipe format together with this project's agent doctrine (sibling doc `21-agent-doctrine.md`), so recipes, workflows and evaluation share one vocabulary instead of growing a separate format [I].

---

## 11. Asset and media provenance (D040)

D040 records provenance mainly at *publish* time, not as blocking popups. It keeps `AssetProvenance` and `AiGenerationMeta {provider, model, generated_at, prompt_hash, human_edited}`, with checks that depend on the publish channel [V: `ICD:src/decisions/09f/D040-asset-studio.md#L138-L172`]. AI-enhanced media must be labelled, and originals are preserved [V: `#L174-L195`].

**For us [I]:**

- Record `AiGenerationMeta` per generated object or text block (in the sidecar).
- Add a "human edited" flag, set automatically when the user changes agent output.
- At export, optionally add a short "AI-assisted" note to the mission description. Communities tend to want disclosure [I].
- Skip IC's image, sprite, music, SFX and video generation. OFP assets are 3D models and textures and out of scope.

---

## 12. External agents: exposing the editor over MCP (D071)

**IC's design** [V: `ICD:src/decisions/09f/D071-external-tool-api.md`]:

- A local JSON-RPC 2.0 API with permission tiers (observer, admin, mod, debug) over WebSocket or HTTP, plus **stdio for MCP and LSP** [`#L10-L20`, `#L79-L85`].
- An MCP server exposing Resources, Tools and Prompts [`#L257-L278`].
- Rate limits and per-tier restrictions [`#L207-L216`].
- The threat model adds **Cross-Site WebSocket Hijacking** (V57): browsers can open `ws://localhost`, so the server must validate the `Origin` header and use a challenge secret [V: `ICD:src/security/vulns-edge-cases-infra.md#L120-L157`].

**Current MCP:** the latest revision is 2026-07-28. It is built on JSON-RPC 2.0 with "stateless, self-contained requests", defines Resources, Prompts and Tools on the server side and elicitation on the client side, and has optional extensions (Tasks, Skills over MCP, MCP Apps) [V: https://modelcontextprotocol.io/specification/latest].

**For us [I]:**

- Offer an **`ofp-editor mcp` stdio server** that exposes the same `EditorCommand` manifest (§5). The user's own agent (Claude Code, Codex, opencode, …) can then drive the editor without us embedding any model. It is cheap once the command registry exists, and it serves users who already pay for an agent.
- Do not open a network listener by default. If we add WebSocket later, copy the V57 defenses.
- Use the same permission split: read-only tools vs. mutating tools that need confirmation.

---

## 13. Privacy, logging and sharing [V + I]

- **IC defaults** [V]: prompt capture is opt-in; built-in models run on-device; cloud providers are "the user's choice and the user's responsibility" [`LLM-MODES.md#L24`]. Probes never touch personal data [`D047#L285`]. Replays have `strip-llm` and `redact-prompts` tools, and "a replay must remain fully playable if all LLM annotations are stripped" [`D073#L253-L262`]. Keys are never exported [`D047#L370`].
- **Our analogues** [I]:
  - A mission folder must stay valid with the agent sidecar deleted.
  - Add "Export without AI metadata" and "Redact prompts" actions.
  - Show which provider and endpoint will receive the context before the first cloud call in a session.
  - Never send file paths or usernames in context unless needed.

---

## 14. Evaluation

**IC's eval ideas** [V]:

- Every model pack ships "a minimal eval suite result" and records `eval_suite` and `eval_pass_rate` in its manifest [`D047#L69`, `#L94-L98`].
- Evals run against the **quantized** weights actually shipped [`ICD:research/cpu-llm-model-evaluation.md#L403-L409`].
- A task-specific JSON-parse suite targets "≥95% valid parses", with grammar-constrained decoding and a non-LLM fallback [`#L423-L435`].
- Only one model is loaded at a time on 8 GB machines [`#L396-L399`].
- The CPU throughput estimate is memory bandwidth ÷ model size, with a 0.55–0.70 real-world factor [IC-claim: `#L28-L61`].

**For us [I]:**

- Build a **golden-task suite** from synthetic missions (no game data), e.g.:
  - "place a 4-man squad patrolling between markers A and B";
  - "add a trigger ending the mission when all east units are dead";
  - "write a 3-line radio exchange for this ambush".
- Score each task on schema-valid tool calls, validator pass, semantic diff vs. the expected result, and number of repair passes.
- Run the suite from the in-app **Prompt Test** button (per provider and profile) and in CI against a local model.
- Use the same suite as evidence when choosing models. Sibling doc `16-decision-models.md` sets the bar a model must clear before we adopt it; any small-model quality claim stays a hypothesis until it is measured with our own evaluation instruments [I].

---

## 15. Editor UX ideas (AI and non-AI) worth borrowing

**AI UX** [V]:

- **"No dead-end buttons".** An AI action without a provider opens a guidance panel with "Configure provider" and "Use templates without AI" [`D016-overview-generation.md#L57`; `ICD:src/player-flow/single-player.md#L265-L276`].
- A **one-time, skippable discovery panel** [`ICD:src/player-flow/settings.md#L262-L335`].
- "**Great defaults, not hidden magic**": inferred values are always visible and can be overridden [`D016-overview-generation.md#L145`].
- Candidates come with in-context preview [`D040#L219-L226`].

**Editor UX from D038** [V: `ICD:src/decisions/09f/D038/*`], ideas the OFP community may like and our agent can also use:

- unlimited undo and redo; autosave in 3 rotating slots; crash recovery; pre-preview snapshot;
- search, favorites and recent items in the class palette;
- trigger folders and search, plus a read-only flow-graph view;
- a complexity meter;
- named regions reused across triggers;
- "play from cursor", preview at 2x/4x/8x, instant restart;
- Simple/Advanced modes on one data model;
- Git-friendly canonical serialization with stable IDs and a semantic diff.

Sources: `D038-core-architecture.md#L105-L115`, `#L243-L281`, `#L310-L366`; `D038-media-validation.md#L344-L362`.

IC credits OFP for Probability of Presence, Condition of Presence, placement radius, Guard/Guarded-By, sync lines and min/mid/max timers [V: `D038-core-architecture.md#L27-L37`, `#L137`; `D038-triggers-waypoints.md#L35`, `#L234-L255`]. These are native OFP features our editor must reproduce anyway.

---

## 16. Reusable project-process ideas

| Idea | What it is | Source | Adopt? |
|---|---|---|---|
| Decision records `Dxxx`, one per file | normative decisions with alternatives and revision notes; hub pages list only IDs and titles | `ICD:src/decisions/09f-tools.md`; `ICD:src/LLM-INDEX.md#L27-L37` | **Yes**: `docs/decisions/D001-*.md` [I] |
| Decision Capsule | a 10–16 bullet summary at the top of each decision (status, scope, decision, non-goals, invariants, defaults, interfaces, affected docs, keywords) | `ICD:src/decisions/DECISION-CAPSULE-TEMPLATE.md#L20-L60` | **Yes**: cheap and helps agents a lot [I] |
| `LLM-INDEX.md` | canonical-source priority, a topic → canonical file map, chunking rules (300–900 tokens), conflict rules ("prefer decision docs … state the conflict explicitly") | `ICD:src/LLM-INDEX.md#L27-L140` | **Yes**, once docs/ exceeds ~20 files [I] |
| `CODE-INDEX.md` | task routing ("start here for X"), repo map, per-subsystem entries, do-not-edit notes, proof paths | `ICD:src/tracking/source-code-index-template.md`; in use at `IC:CODE-INDEX.md` | **Yes** (already in our rules) |
| Design-gap requests | "Do not silently invent a new design": file `docs/design-gap-requests/DGxxx-*.md` with the conflict, options and impact, and label temporary work `implementation placeholder` | `ICD:src/tracking/external-code-project-bootstrap.md#L93-L130`; real examples `IC:docs/design-gap-requests/DG001-remastered-bk2-support-boundary.md` | **Yes** [I] |
| Feature/Screen/Scenario spec | YAML feature spec (guards, behavior, *non-goals*), typed widget tree, Given/When/Then scenarios, "so an agentic LLM has one correct interpretation" | `ICD:src/tracking/feature-scenario-spec-template.md#L1-L31` | **Yes, for the agent panel and the F1–F6 dialogs** [I] |
| Research rigor | "The human identifies the question"; claims verified at source level; "The LLM agent never commits"; "Mistakes to Never Repeat" list grows from real errors | `ICD:src/methodology/research-rigor.md#L184-L198`, `#L221-L273` | **Yes**: add a "Mistakes to never repeat" section to AGENTS.md [I] |
| Keep code small for retrieval | ≤500 lines per logic file, `//!` routing headers, one concept per module | `ICD:src/tracking/external-code-project-bootstrap.md#L153-L165` | Compatible with our ≤600-line rule [I] |

---

## 17. Ranked list of ideas to adopt or adapt

Ranked by value to the OFP editor divided by cost [I].

| # | Idea | IC source | How we adapt it | When |
|---|---|---|---|---|
| 1 | **Command registry as the single path.** GUI and agent share validation, undo and results; manifest generated from the enum | D016 tool bindings; D038 | `EditorCommand` enum + JSON Schema; one undo group per agent turn | Before any AI work (M-core) |
| 2 | **Semantic diff preview + confirm; autonomy is opt-in** | D038 `SemanticChange`; D016 "not autonomous by default" | Diff pane + map overlay; Ask/Propose/Confirm/Auto | With the agent MVP |
| 3 | **Multi-stage validator with LLM-readable errors + section-targeted repair (≤3)** | llm-generation-schemas §6/§12; 16-CODING-STANDARDS | Validator crate shared by GUI, CLI and agent; errors carry object ID, field path and suggestion | Validator early (useful without AI) |
| 4 | **Templates/compositions with typed schemas ("smart form-filler")** | tera-templating; D038 compositions | "Save selection as composition"; parameterized SQS/SQF + sqm fragments; Tera or minijinja | Agent MVP |
| 5 | **Provider abstraction + task routing + keyring credentials** | D047, V61 | Local-external + API-key tiers first; `agent`/`writer`/`compress` routes; no OAuth | Agent MVP |
| 6 | **Prompt Strategy Profiles as effort levels + capability probe + prompt test** | D047 | Quick/Standard/Thorough mapped to Compact/Stepwise/Rich + repair budgets; probe results cached | MVP (profiles), v1.x (probe UI) |
| 7 | **LLM class catalog with controlled vocabulary** | llm-metadata | Runtime catalog from the user's game config + our hand-written `llm:` overlay | MVP |
| 8 | **Untrusted-content posture** | V40, MCP spec | Script scan, budgets, summary before game preview, mission text treated as untrusted agent input | MVP |
| 9 | **Narrative kit: cast sheets, style-preset rules, context doc, Intent Interpreter** | D016 characters/overview | Cast panel; style presets as data; "describe mission" → pre-filled form with "inferred" badges | v1.x |
| 10 | **Editor as MCP server (stdio)** | D071 | `ofp-editor mcp` exposes the same manifest | v1.x (cheap after #1) |
| 11 | **Decision capsules, LLM-INDEX, design-gap requests, feature/scenario specs** | §16 | Adopt in `docs/` now | Now |
| 12 | **AI provenance metadata + human-edited flag + strippable sidecar** | D040, D073 | `.ofpeditor/` sidecar; export without AI metadata | v1.x |
| 13 | **Golden-task eval suite** | D047 eval packs | Synthetic missions; CI with a local model | v1.x |
| 14 | **Recipe/skill library (FTS5, verified by acceptance)** | D057 | Log accepted examples → retrieve as few-shot | v2 |
| 15 | **Built-in model pack (downloaded, pinned, eval'd, licensed)** | D047 Tier 1 | Only after BYO works; permissive licenses; pick the runtime then | v2 |

### Ideas to skip, and why [I unless marked]

| Skip | Why |
|---|---|
| **Cloud OAuth tier** | Anthropic forbids third-party Claude.ai login [V]; other vendors unverified; big security surface (V61 notes stolen refresh tokens) |
| Workshop-dependent features (`ai_usage` consent, community config marketplace, composition-set curation, LLM-config achievements) | We have no content hub. Keep only "import/export config file (no keys)" |
| Generative campaigns at runtime, "One More Prompt" loop, world-domination and multiplayer generative modes | We are an editor, not a game runtime. Campaign authoring aids belong with doc `18-campaign-system-in-engine.md` |
| In-game LLM AI (orchestrator, LLM player, exhibition and prompt duels) | The agent never talks to the running game (§2); this would need game-side hooks |
| Image, sprite (IST), music, SFX and video generation | OFP assets are 3D models and textures; out of scope, with legal and quality risk |
| Mandatory personality typology for characters | Keep flaw/desire/fear/speech style; make any typology optional |
| Win-rate-based skill auto-promotion | We have no gameplay outcome signal; use acceptance signals instead |
| Pure-Rust embedded inference as a v1 requirement | High effort; IC's own evidence is design-only. BYO local servers cover the need first |
| Hard-coded model IDs, prices and "recommended model" tables | They go stale (IC's did within about a year); fetch model lists at runtime |

---

## Open questions

1. **Command set closure.** Can every original F1–F6 dialog field and every `Intel` field be expressed as a typed command with no "raw text" escape hatch? Which fields need a free-text escape hatch (init lines, conditions, On Act)? Should those be tagged high-risk in previews? [U]
2. **Script risk.** Which SQS/SQF commands in CWA and CWR-CE deserve a denylist or warning (file access, `call` of runtime-built strings, anything added by CWR-CE)? This needs an audit of the CWR script-command registration code [U].
3. **Harness vs. provider layer.** Do we adopt an existing multi-provider Rust crate (e.g. `rig`) for tool-calling and streaming, or write a minimal trait? IC's trait lacks tool calls [V]. See sibling docs 10 and 11.
4. **OAuth for other vendors.** Do OpenAI or Google allow third-party desktop apps to use a consumer login for API calls? [U]
5. **Class-catalog overlay.** Who writes the `llm:` descriptions for vanilla CWA classes, and in what controlled vocabulary? Can a model draft them from config values, with human review, without copying proprietary text? [U]
6. **Effort-level UX.** One global effort selector, per-workflow defaults, or per-request? How is cost/latency shown (IC shows tokens and cost estimates in the probe) [I]?
7. **Shared formats.** Should the recipe library (§10) and the golden-task suite (§14) reuse the workflow and evaluation formats defined in sibling docs `21-agent-doctrine.md` and `16-decision-models.md`, or do they need their own? [U]
8. **UnrealAI prior art.** IC cites a UE5 "UnrealAI" plugin (Feb 2026, 100+ tool bindings, 8 providers). It is unverified here and worth checking as the closest editor-agent precedent [U].
9. **Disclosure norms.** Does the OFP/CWA community expect missions to disclose AI assistance, and would an "AI-assisted" tag help or hurt adoption? [U]

---

## Sources

**Iron Curtain design docs** (`iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9`, commit dated 2026-04-01):

- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/LLM-MODES.md#L10-L25`, `#L29-L57`, `#L179-L272`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/LLM-INDEX.md#L27-L140`, `#L223-L240`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f-tools.md`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D016-llm-missions.md`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D016/D016-overview-generation.md#L3-L47`, `#L57`, `#L87-L161`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D016/D016-characters-output.md#L7-L95`, `#L160-L213`, `#L401-L424`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D016/D016-cinematics-media.md#L7-L92`, `#L239-L396`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D016/D016-branching-world-campaigns.md#L33-L51`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D016/D016-world-assets-multiplayer.md#L120-L143`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D016/D016-factions-editor-tools.md#L67-L79`, `#L145-L192`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D016/D016-extensions-factions-tools.md#L197`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D038/D038-core-architecture.md#L7-L39`, `#L88-L137`, `#L243-L366`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D038/D038-triggers-waypoints.md#L1-L305`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D038/D038-media-validation.md#L344-L456`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D038/D038-game-master-replay-multiplayer.md#L42-L71`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D038/D038-onboarding-platform-export.md#L95-L124`, `#L534-L536`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D040-asset-studio.md#L3-L19`, `#L138-L233`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D047-llm-config.md#L7-L568`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D057-llm-skill-library.md#L11-L432`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D071-external-tool-api.md#L10-L85`, `#L207-L278`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09d/D044-llm-ai.md#L18-L61`, `#L333-L349`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09d/D043/commanders-and-puppet-masters.md#L134-L164`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09d/D073-llm-exhibition-modes.md#L14-L22`, `#L240-L262`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/modding/llm-metadata.md#L1-L222`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/modding/tera-templating.md#L3-L196`, `#L484-L539`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/player-flow/llm-setup-guide.md#L11-L20`, `#L103-L219`, `#L225-L308`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/player-flow/settings.md#L262-L335`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/player-flow/single-player.md#L265-L276`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/security/vulns-infrastructure.md#L333-L361`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/security/vulns-edge-cases-infra.md#L120-L157`, `#L263-L306`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/16-CODING-STANDARDS.md#L270-L272`, `#L598`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/13-PHILOSOPHY.md#L343-L348`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/DECISION-CAPSULE-TEMPLATE.md#L20-L60`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/tracking/external-code-project-bootstrap.md#L93-L165`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/tracking/source-code-index-template.md#L1-L70`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/tracking/feature-scenario-spec-template.md#L1-L31`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/methodology/research-rigor.md#L184-L273`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:research/llm-generation-schemas.md#L1124-L1342`, `#L2391-L2510`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:research/byollm-implementation-spec.md#L40-L138`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:research/cpu-llm-model-evaluation.md#L8-L61`, `#L354-L484`

**Iron Curtain code repo** (`iron-curtain-engine/iron-curtain@7b7fac7fa5`):

- `iron-curtain-engine/iron-curtain@7b7fac7fa5:CODE-INDEX.md` (`#L171-L184`: `ic-llm`, `ic-editor` planned, not implemented)
- `iron-curtain-engine/iron-curtain@7b7fac7fa5:docs/design-gap-requests/DG001-remastered-bk2-support-boundary.md`
- `iron-curtain-engine/iron-curtain@7b7fac7fa5:docs/design-gap-requests/DG002-media-container-and-localization-packaging-strategy.md`

**CWR engine source** (`BohemiaInteractive/CWR@ffc61838b7`):

- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.cpp#L1460-L1467` (group serialization: `side`, `Vehicles`, `Waypoints`, `Sensors`)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.cpp#L1934-L1990` (template: `addOns`, `addOnsAuto`, `show*` flags, `randomSeed`, `Intel`, `Groups`, `Vehicles`, `Markers`, `Sensors`; `CheckSynchro` on save and load)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMap.hpp#L564-L573` (`InsertMode`: the six editor modes)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapExtDisplay.cpp#L99-L121` (`Mission`/`Intro`/`OutroWin`/`OutroLoose` templates)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Locale/MissionHtmlLocalization.cpp` (HTML briefing localization exists)

**Web** (fetched 2026-09-26):

- Anthropic, Claude Code "Legal and compliance", Authentication and credential use: https://code.claude.com/docs/en/legal-and-compliance
- Model Context Protocol specification (latest = 2026-07-28): https://modelcontextprotocol.io/specification/latest
- Wang et al., "Voyager: An Open-Ended Embodied Agent with Large Language Models": https://arxiv.org/abs/2305.16291
- huggingface/candle README (quantized GGUF; Qwen/Phi families; MIT/Apache-2.0): https://github.com/huggingface/candle
- Keats/tera README (Jinja2/Django-based; MIT): https://github.com/Keats/tera
- tera crate metadata (newest 2.4.0, MIT): https://crates.io/api/v1/crates/tera
- candle quantized model sources: https://github.com/huggingface/candle/tree/main/candle-transformers/src/models

**Sibling notes in this repo** referenced for context (not re-verified here): `docs/research/04-mission-data-model-and-formats.md`, `10-harness-codex-and-opencode.md`, `11-harness-pi-tinyagent-deepseek.md`, `16-decision-models.md`, `18-campaign-system-in-engine.md`, `21-agent-doctrine.md`.

---

## Verification notes

Adversarial fact-check, 2026-09-26. Every IC and CWR pointer below was re-opened at the pinned commits. The web sources were re-fetched on the same day.

**Confirmed as written:**

- LLM-MODES "design-stage only" (L10) and the ground rules (L18-L25).
- D016 tool bindings (L160-L192): same validation and undo pipeline, manifest auto-generated from the command registry, not autonomous by default, "If the GUI can't do it, the LLM can't do it".
- The byollm `LlmProvider` sketch (L55-L138) has no tool-call, streaming or cancel fields; the only "stream" hit in the file is `"stream": false` at L899.
- D047 tiers, profiles, probe, test harness, export and manifest line ranges.
- V40, V57 and V61 security text.
- `llm-metadata` rules and `ai_usage`.
- Tera template and scene-template quotes, D038 compositions, `SemanticChange`, validation presets and autosave.
- The 7-stage validator and the 3/1/fallback regeneration policy; the §12 headings with "VALID — do not regenerate".
- D057 FTS5 and its "NOT fine-tuning" / "NOT required" statements; D044, D043, D071, D073 and D040 pointers.
- IC process files: `CODE-INDEX.md`, DG001 and DG002 exist.
- Anthropic's credential policy quote, the MCP spec (revision 2026-07-28, JSON-RPC 2.0, Resources/Prompts/Tools, elicitation, extensions, untrusted annotations, consent), the Voyager abstract numbers, candle's dual MIT/Apache-2.0 license and Tera's MIT license.
- No "effort level" concept exists anywhere in the IC docs (grep).

**Corrected:**

- The D016 sub-file count is 7, not 6.
- LLM-MODES has 6 ground rules, not 5.
- The TL;DR said the `llm:` block is on every asset; IC makes it optional.
- The cloud model IDs were attributed to `cpu-llm-model-evaluation.md`. They actually come from D047 and `llm-setup-guide.md`, and they include `claude-haiku-4-5-20251001`, so they are not all mid-2025. Only the CPU evaluation says "mid-2025".
- The narrative-pillar requirement applies to "C&C Classic" prompts only.
- The CWA data-model claim was incomplete. The template also serializes add-on lists, the `show*` flags and `randomSeed`. `CheckSynchro` runs on save as well as on load. A `mission.sqm` holds four templates. The editor's six insert modes were added (`UIMap.hpp#L564-L573`), and the command table was updated to match.
- The candle citation now points at the README text plus the `quantized_*` model sources. The README alone does not name quantized Phi.
- Tera 2 (2.4.0) is now current.
- Added evidence that IC has no `ic-llm` or `ic-editor` crate yet (`IC:CODE-INDEX.md#L171-L184`).

**Still unverified:** the UnrealAI prior art (web search was unavailable); whether OpenAI or Google allow OAuth for third-party apps; IC's CPU benchmark figures.
