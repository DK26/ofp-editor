# rig and headroom: provider layer and context budgeting for the editor agent

Research date: 2026-09-26. Pinned sources: `0xPlaygrounds/rig@42f4e060ef` (main, 2026-09-26),
`headroomlabs-ai/headroom@7968122658` (main, 2026-09-26). Live registry data was fetched on the same date.

**Epistemic tags used below:** **[V]** verified against pinned code or a live source (citation given);
**[I]** inferred by the author from verified facts; **[U]** unknown or not verified. Any number without
[V] is an estimate.

**Context for readers of this file alone.** `ofp-editor` is a standalone Rust re-implementation of the
Mission Editor of *Arma: Cold War Assault* (the 2001 *Operation Flashpoint* editor). It will include a
built-in "harness agent": the user types a prompt and a model (cloud frontier model, local small model,
or a typed decision model) performs editor actions such as placing units and waypoints, creating triggers,
writing briefings, and generating dialogue. Users set an effort level and pick workflows. They can bring
their own model. This document answers two questions:

1. Which Rust crate(s) should talk to model providers ("provider layer")?
2. How do we keep prompts within a context budget when mission files, config class catalogs
   (`CfgVehicles`), world object lists (WRP files) and SQF scripts get large?

Glossary: **provider** = a model API (Anthropic, OpenAI, Gemini, a local Ollama server). **Tool** = a
function the model may call, described to it by name, description and JSON Schema. **Agent loop** =
calling the model, running the tools it requests, feeding results back, and repeating. **Structured
extraction** = forcing model output into a typed struct. **MCP** = Model Context Protocol, an open
protocol for exposing tools to any agent. **Prompt caching** = provider-side reuse of an unchanged prompt
prefix; cached input is cheaper and faster. **Effort** = a provider knob for how much hidden reasoning
("thinking") the model spends.

## TL;DR

- **rig** is the most complete Rust LLM stack **[V]**: MIT, v0.42.0 (2026-08-17), about 3.0M crates.io
  downloads. It has 26 provider modules over three wire grammars (OpenAI Chat/Responses, Anthropic
  Messages, Gemini) plus native Ollama. It also provides typed tools with `schemars` schemas, typed
  extraction, a multi-turn tool loop with hooks that can approve, deny or rewrite each tool call, a
  serializable sans-I/O run state machine, record/replay "cassettes", and optional in-process Candle
  inference. **Caveat [V]:** the pinned commit is *unreleased* `main` after 0.42.0. The published 0.42.0
  has the same core capabilities but a different crate layout and hook names (§1.0).
- **The cost is churn [V].** A breaking 0.x minor version ships about every three weeks (0.37→0.42 in 14 weeks).
  `MIGRATING.md` is 5,239 lines, and the README warns that breaking changes will keep coming. rig has no
  provider-neutral "effort" setting. `rig-rmcp` is built on `rmcp` 2.x, but `rmcp` itself is at 3.4.1.
- **Recommendation: own the seam, rent the wires.** Our crate `ofp-agent` defines the provider-neutral
  types (messages, editor tools, `Effort`, context budget). A single adapter crate, `ofp-agent-rig`, depends
  on `rig-core` + `rig-agent` (+ `rig-memory`) with an exact version pin. `rig-reqwest` exists on crates.io
  only as a 0.0.0 placeholder, so at 0.42.0 the HTTP transport is inside `rig-core`; adopt `rig-reqwest`
  when the next release publishes it (§1.0). Domain crates (mission, config and WRP parsers) never import rig.
- **Use rig's hook seams [V]:** `on_dispatch` for policy or human approval of every editor mutation,
  `on_outcome` to rewrite oversized tool results, and `RequestPatch` for per-turn effort params and
  `active_tools` allow-lists (our "workflows"). In published 0.42.0 the first two are named
  `on_tool_call` (`ToolCallAction::{Run, Rewrite, Skip, Stop}`) and `on_tool_result`
  (`ToolResultAction::{Keep, Rewrite, Stop}`).
- **Plan B is `genai` [V]** (MIT OR Apache-2.0). It has a unified `ReasoningEffort` and cache control, but no
  agent loop and no MCP, and its 0.7 line is still in beta (beta.15 on 2026-07-29, beta.24 on 2026-09-23). `async-openai` is OpenAI-only.
  `graniet/llm` releases more slowly. There is no official Anthropic Rust SDK (checked 2026-09-26).
- **MCP [V/I]:** depend on the official `rmcp` 3.x directly to *serve* editor tools to external agents. This
  is the cheapest bring-your-own-model path. Use rig's MCP client (rig-agent's `rmcp` feature in 0.42.0;
  the unpublished `rig-rmcp` crate on main) only if the in-app agent must *consume* external MCP servers,
  and accept a second `rmcp` major in the build tree if you do.
- **headroom [V]** is a Python-first local proxy/SDK (Apache-2.0, v0.39.0) with a partial Rust port of its
  core. It compresses tool outputs, logs, JSON arrays and prose before they reach the model. It keeps
  originals retrievable ("CCR": a hash marker plus a retrieve tool) and never touches cached prefixes.
  Its seeded proof table shows 21–57% input savings on agent-like payloads.
- **Do not depend on headroom [V/I].** `headroom-core` is not on crates.io and pulls ONNX Runtime,
  tree-sitter, SQLite and ICU. It uses `expect`/slicing that our lints forbid. Its ML text compressor
  (Kompress, a 150M-parameter ModernBERT; 274 MB weight-only int8 ONNX) targets prose, not our structured data.
- **Port headroom's ideas instead (about 1–2k lines of our own code) [I]:** tools that query instead of
  dumping; reversible truncation with an `expand_ref` tool; additive "must-keep" sets (errors, anomalies,
  IDs the user named, the current selection); a byte-stable cacheable prefix; tool-call/result atomicity;
  a "never larger than the original" gate; and effort routing that can only lower effort. On Anthropic,
  effort routing breaks the prompt cache unless the beta per-message effort is used (§5.7).
- **Budget in v1 without a tokenizer [V/I]:** use rig-memory's `TokenWindowMemory` with
  `HeuristicTokenCounter` (a bytes-per-token estimate), calibrated per model from the provider-reported
  `Usage.input_tokens`.

---

## 1. rig in detail

### 1.0 Published 0.42.0 vs the pinned `main` [V] (added by fact-check)

`42f4e060ef` is `main` about six weeks after the 0.42.0 release (the 0.42.0 crates were built from
`d5a34986a1`, per their `.cargo_vcs_info.json`). Line citations in §1 point at `main`. Checked against the
0.42.0 tarballs and the crates.io API on 2026-09-26:

- **Unpublished crates.** `rig-reqwest` and `rig-rmcp` are 0.0.0 name placeholders (created 2026-09-21),
  `rig-cassette` is a 0.0.1 "Placeholder crate", and `rig-typesafeai` is 0.0.0. Published at 0.42.0:
  `rig`, `rig-core`, `rig-agent`, `rig-memory`, `rig-candle`, `rig-derive`.
- **0.42.0 layout.** `rig-core` 0.42.0 depends on `reqwest` directly. MCP is `rig-agent`'s optional `rmcp`
  feature (`rmcp ^2`). The provider list has 27 modules, including `llamafile` (llama.cpp's OpenAI-compatible
  server) but no `registry`/`llamacpp`. Base URLs are set on the client builder
  (`rig-core-0.42.0/src/client/mod.rs#L829`). There are no Claude 5 model constants.
- **0.42.0 hooks.** The same capabilities exist under different names in `rig-agent-0.42.0/src/agent/hook.rs`:
  `on_tool_call` → `ToolCallAction::{Run, Rewrite, Skip, Stop}` (#L1044-L1081, #L1280); `on_tool_result` →
  `ToolResultAction::{Keep, Rewrite, Stop}` (#L1086-L1120, #L1295); and `RequestPatch` with `active_tools`
  and `additional_params` (#L838-L855). `AgentRun` is `Serialize + Deserialize` and sans-I/O
  (`agent/run/mod.rs#L1-L13`, `#L388-L389`). There is no `on_dispatch`, `on_outcome` or `on_run_start`.
- **Unchanged in 0.42.0.** The OpenAI `ReasoningEffort` has the same variants. rig-candle's Qwen3-4B,
  4096-token and CPU-only statements are the same. `HeuristicTokenCounter::anthropic()` = 3.5 bytes/token,
  and `TokenWindowMemory` drops a leading orphan tool result.
- **[I] Consequence:** the next rig release will rename hooks and split crates, so it is a large migration.
  If coding starts before that release, write the adapter against 0.42.0 names and budget time for the
  migration. Otherwise start directly on the new release.

### 1.1 Crate layout [V]

The repo root is both the workspace and the `rig` facade crate. Workspace version 0.42.0, edition 2024,
MIT license (`0xPlaygrounds/rig@42f4e060ef:Cargo.toml#L1-L5`, `#L151-L153`). The README splits the
portable contracts (`rig-core`) from orchestration (`rig-agent`) (`README.md#L77-L89`).

| Crate | Role | Relevance to us |
|---|---|---|
| `rig-core` | Messages, `CompletionModel`, tools, streaming, 26 provider modules, memory and vector-store contracts. No default HTTP transport on `main`; 0.42.0 has reqwest built in. | **Yes.** Our adapter depends on it. |
| `rig-agent` | Agent builder, the tool loop ("runner"), hooks, tool registry, `Extractor`, sans-I/O `AgentRun`. | **Yes.** The loop and the approval hooks. |
| `rig-reqwest` (main only; unpublished) | Bundled reqwest transport. `rustls` by default; optional `reqwest-middleware` (retries). | **Yes**, once released. |
| `rig-derive` | `#[rig_tool]`, `#[derive(Embed)]`, `#[derive(ContextValue)]`. | Optional. |
| `rig-memory` | History-shaping policies: sliding window, token window. | **Yes.** For budgeting (see §5). |
| `rig-rmcp` (main only; unpublished) | MCP client: MCP tools become rig tools. Native targets only. | Maybe (§3.4). |
| `rig-candle` | In-process CPU inference over validated checkpoints. | Candidate for an embedded tier. |
| `rig-cassette` (main only; unpublished) | Effect logs, record/replay, HTTP cassettes. | Useful for deterministic tests. |
| `rig-typesafeai` (main only; unpublished) | Typed client for TypeSafe's hosted "Jev" judgment model. | Optional experiment (§1.9). |
| `rig-ecs` | The rig runtime inside a Bevy ECS `World`. | Only if the editor UI is Bevy. |
| `rig-bedrock`, `rig-vertexai`, `rig-gemini-grpc`, 12 vector stores | Cloud and storage integrations. | No. |

The facade's companion-crate dependencies are at `Cargo.toml#L312-L337` and its features at
`#L399-L483`. The facade's `default` features turn on `reqwest`, `agent`, `derive` and `rustls`
(`Cargo.toml#L401`), and it always depends on `rig-cassette`, which is not optional (`#L312-L316`). Both
points describe `main`: the published `rig` 0.42.0 has no `rig-cassette` or `rig-reqwest` dependency (§1.0).
**[I]** Depend on the published leaf crates with `default-features = false`, not on the facade.

### 1.2 Provider coverage [V]

`rig-core/src/providers/mod.rs#L11-L38` declares 28 modules. Two are helpers (`internal`, `registry`),
which leaves 26 providers. Serialized provider selection (`registry::ProviderRef`) recognizes three wire
**formats**, `OpenAi`, `Anthropic` and `Gemini` (`registry.rs#L60-L72`), plus 21 OpenAI-compatible
**dialects** (`registry.rs#L36-L58`).

| Needed provider | rig support | Evidence |
|---|---|---|
| Anthropic | Native Messages API. Prompt-cache helpers `with_prompt_caching()`, `with_automatic_caching()`, `with_automatic_caching_1h()`. Current model constants (for example `claude-opus-5`, `claude-sonnet-5`). | `providers/anthropic/wire.rs#L328-L399`, `anthropic/completion.rs#L20-L36` |
| OpenAI | Responses API by default; Chat Completions via `Route::Chat`. Typed `Reasoning { effort, ... }`. | `README.md#L138-L145`, `openai/responses_api/mod.rs#L1641-L1676` |
| Gemini | Native GenerateContent, interactions API, cached content. Thinking set through `AdditionalParameters { ThinkingConfig }`. | `providers/gemini/*`, `examples/gemini_stream_kill_token_count/src/main.rs#L326-L359` |
| DeepSeek | OpenAI dialect `DEEPSEEK`. Constants `deepseek-v4-flash` and `deepseek-v4-pro`. Reasoning content and cache-hit usage are parsed. | `providers/deepseek.rs#L1-L20` |
| Mistral, OpenRouter, Groq, Together, xAI, Moonshot, Z.ai, MiniMax, Perplexity, Azure, HF | OpenAI dialects. | `registry.rs#L36-L58` |
| Ollama | Native wire (NDJSON). `OLLAMA_API_BASE_URL` allows remote daemons. | `providers/ollama.rs#L1-L16` |
| llama.cpp server | OpenAI dialect `LLAMACPP`. Default `http://localhost:8080/v1`, optional bearer, raw `timings`. | `openai/wire/dialects.rs#L206-L246`, `providers/llamacpp/completion.rs#L13-L61` |
| Any OpenAI-compatible server (LM Studio, vLLM, …) | `OpenAI::with_base_url(...)` | `openai/wire.rs#L912` |
| In-process local model | `rig-candle` (see §1.8). There is no in-process llama.cpp binding in rig. | `crates/rig-candle/README.md#L1-L25` |
| ChatGPT / GitHub Copilot *subscriptions* | Login and token-exchange modules. | `providers/chatgpt/mod.rs#L1-L4`, `providers/copilot/mod.rs#L1-L5` |

The table describes `main`. In published 0.42.0, llama.cpp is reached through the `llamafile` module or a
client `base_url`, and the newest Anthropic constant is `claude-opus-4-8` (§1.0).

**[U]** Whether routing a third-party desktop app through a ChatGPT or Copilot subscription is permitted
by those services' terms. We do not recommend exposing these providers in our UI until that is checked.

### 1.3 Core contracts [V]

- `CompletionModel` (`rig-core/src/completion/request.rs#L411-L466`): `completion()`, `stream()`,
  `capabilities()`. `ProviderCapabilities` (`#L387-L409`) declares only whether native structured output
  composes with tool calls.
- `CompletionRequest` (`#L510-L541`) is `Serialize + Deserialize` (good for audit logs): `chat_history`,
  `documents`, `tools`, `temperature`, `max_tokens`, `tool_choice`, `additional_params:
  Option<serde_json::Value>` (the provider-specific escape hatch), `output_schema: Option<schemars::Schema>`.
- `Usage` reports input, output, cached-input, cache-creation and reasoning tokens (`#L321-L344`). The
  model listing has optional `context_length` and `max_output_tokens` (`model/listing.rs#L42-L49`).
- Reasoning blocks carry their issuer; `retain_replayable_reasoning` drops signatures another provider
  would reject (`completion/message.rs#L136-L208`), which matters when a user switches models
  mid-conversation. Agents erase the model type, so it can be swapped at runtime (`Agent::set_model`,
  `on_model_select`) (`MIGRATING.md#L2982-L2997`).

### 1.4 Tools and how their schemas are produced [V]

- `PortableTool` is context-free: `const NAME`, `type Args: Deserialize`, `type Output`,
  `type Error: std::error::Error`, `description()`, `parameters() -> serde_json::Value`, and
  `async fn call` (`rig-core/src/tool/portable.rs#L40-L67`).
- `Tool` adds a `&mut ToolContext`, which holds typed inbound values and **host-only result metadata the
  model never sees** (`tool/contextual.rs#L1-L76`). Argument parse failures come back to the model as
  failed tool results, not panics (`#L146-L191`). `DynamicTool` builds a tool at runtime from a name,
  description, schema and callback (`#L255-L318`).
- **Schemas:** the trait method returns hand-supplied JSON. The `#[rig_tool]` attribute macro generates
  an args struct with `#[derive(Deserialize, JsonSchema)]` and calls
  `schemars::schema_for!(Args).to_value()`, forcing an explicit `required` array
  (`rig-derive/src/tool/expand.rs#L315-L360`). It checks names and requiredness at compile time
  (`rig-derive/src/lib.rs#L50-L82`). rig uses schemars 1.x (`Cargo.toml#L266`).
  - **[I]** For our editor we should `impl Tool` by hand and call `schemars::schema_for!` on our own
    argument types. That keeps newtype IDs, enums and documentation under our control and keeps the macro
    out of our API.
- rig's workspace lints deny `unwrap_used`, `expect_used`, `indexing_slicing`, `panic` and more
  (`Cargo.toml#L123-L135`). These are the same rules as our project.

### 1.5 Structured extraction [V]

- `Extractor<T: JsonSchema + DeserializeOwned>` is a one-turn run. It exposes a synthetic `submit` tool
  whose schema is `T`, forces `ToolChoice::Required`, and supports retries
  (`rig-agent/src/extractor.rs#L1-L15`, `#L82-L89`, `#L130-L145`).
- `OutputMode` selects how structured output is obtained (`rig-agent/src/run/output.rs#L12-L30`): `Auto`
  (default), `Tool` (synthetic final-answer tool, best-effort), `Native` (provider structured output,
  where supported), `Prompted` (schema in the system prompt).
- **[I]** For dialogue and briefing generation, extraction into a typed `DialogueScript { lines:
  Vec<Line { speaker: UnitRef, text, ... }> }` is the right primitive. We still validate the result
  ourselves: rig itself documents non-native modes as best-effort.

### 1.6 Agent loop, streaming, hooks, durable runs [V]

- `AgentBuilder` (`rig-agent/src/agent/builder.rs#L152-L290`) sets the preamble, `tool_choice`,
  `default_max_turns`, `temperature`, `max_tokens`, `additional_params`, `output_schema`, `output_mode`
  and hooks. `AgentRunner::max_turns` sets the total model-call budget, including the initial call,
  retries and continuations (`agent/runner.rs#L132-L135`).
- Streaming emits `MultiTurnStreamItem`s. `run_channel` returns a future plus an event feed
  (`agent/streaming.rs#L466`, `lib.rs#L77`), which suits a UI thread.
- **`AgentHook`** (`agent/hook.rs#L959-L1111`) has these event methods: `on_run_start` (rewrite or stop),
  `on_model_select`, `on_completion_call` (returns a per-turn `RequestPatch`),
  `on_model_turn_finished` (retry with feedback), `on_invalid_tool_call` (repair, retry or skip),
  `on_dispatch` and `on_outcome`.
- `DispatchAction` (`hook.rs#L650-L729`) decides whether a tool call runs: `proceed`; `skip(reason)` (not
  run; the reason becomes the tool result the model sees); `rewrite_tool_args`; `stop`.
  `OutcomeAction::rewrite_tool_output` replaces what the model sees from a result (`hook.rs#L789-L834`).
- `RequestPatch` (`rig-agent/src/run/patch.rs#L13-L45`) changes one turn only: `additional_params`
  (shallow-merged), `active_tools` (allow-list, intersected across hooks), `history`, `max_tokens`.
- Worked human-in-the-loop examples ship in the repo: inline
  (`examples/agent_with_human_in_the_loop/src/main.rs#L1-L21`), policy-based and fail-closed
  (`examples/agent_with_approval_policy/src/main.rs#L1-L17`), and **durable** approval across a
  serialization boundary (`examples/agent_with_durable_approval/src/main.rs#L1-L28`). The last works
  because `AgentRun` is a "serializable, sans-I/O state machine for model turns, tool recovery, and
  history" (`rig-agent/src/run/mod.rs#L1-L12`).

**[I] Mapping to our editor:** every AI edit becomes an `EditorCommand` that goes through the same
validation and undo stack as a mouse edit. `on_dispatch` implements the user's approval policy (for
example: auto-approve reads, preview-then-approve writes, deny deletes above N objects).
`agent_with_durable_approval` is the pattern for "review a batch of proposed edits".

### 1.7 Reasoning, thinking, effort [V]

There is **no provider-neutral effort field** in `CompletionRequest`. A search for "effort" in
`rig-agent/src` finds only "best-effort" comments.

| Provider | How to set effort or thinking in rig |
|---|---|
| OpenAI Responses | Typed `Reasoning::with_effort(ReasoningEffort::{None, Minimal, Low, Medium, High, Xhigh, Max})` (`openai/responses_api/mod.rs#L1641-L1676`, `#L1754-L1766`) |
| Gemini | Typed `ThinkingConfig { thinking_budget, thinking_level }` serialized into `additional_params` (`examples/gemini_stream_kill_token_count/src/main.rs#L326-L359`) |
| Anthropic | No typed request field found in `anthropic/wire.rs` or `anthropic/completion.rs`. Only usage (`thinking_tokens`) and response `Thinking` blocks are typed (`anthropic/completion.rs#L82-L96`, `#L315-L320`). **[I]** Pass it raw via `additional_params`, which is `#[serde(flatten)]`ed into the body. rig already has a typed `output_config` field, used only for structured output (`anthropic/completion.rs#L1544-L1567`, `#L2094-L2104`), so a raw `output_config.effort` combined with `output_schema` would likely emit a duplicate key. Test this. |
| Ollama | `think` handling exists in `providers/ollama.rs` (not inspected in detail). |

headroom's README names the Anthropic knobs `thinking.budget_tokens` / `output_config.effort` and the
OpenAI knob `reasoning_effort` (`headroomlabs-ai/headroom@7968122658:README.md#L182-L186`).
**[V] Anthropic's docs** (<https://platform.claude.com/docs/en/build-with-claude/effort>, fetched 2026-09-26):
effort is `output_config.effort`, is GA, and needs no beta header. Its values are `low`, `medium`, `high`,
`xhigh` and `max`, and `xhigh`/`max` are available only on some models. The default is `high`
(`medium` on Claude Opus 5.5). There is no "off" level. `thinking: {"type": "disabled"}` returns 400 on
Opus 5.5 at every effort, and on Opus 5 at `xhigh`/`max`. `budget_tokens` applies only to extended-thinking
models such as Opus 4.5. **Changing top-level effort between requests invalidates the prompt cache.** A
per-message effort change keeps the cache, but it is beta (header `mid-conversation-output-config-2026-07-01`)
and only Fable 5.1, Mythos 5.1, Opus 5.5 and Opus 5 support it.
**[I]** We own a small mapping table `Effort → (provider, params)` in the adapter crate (§3.3).

### 1.8 MCP and local inference [V]

- **`rig-rmcp`** turns MCP server tools into `DynamicTool`s and resyncs them when the server's tool list
  changes (`crates/rig-rmcp/src/lib.rs#L1-L17`). It is client-only and emits a `compile_error!` on wasm
  (`#L31-L38`). It depends on `rmcp = "2"` (`Cargo.toml#L262`); the lockfile resolves it to 2.2.0
  (`Cargo.lock#L11086-L11087`). crates.io lists `rmcp` 3.4.1 (2026-09-23), Apache-2.0, from
  `modelcontextprotocol/rust-sdk` (live check). `rmcp` 3.0.0 shipped on 2026-07-28. `rig-rmcp` itself is
  only a 0.0.0 placeholder on crates.io. In published 0.42.0 the same client is `rig-agent`'s `rmcp` feature,
  also on `rmcp ^2` (crates.io dependency API).
- **`rig-candle`** (`crates/rig-candle/README.md`) takes byte buffers and does no filesystem or network
  access itself (`#L3-L5`). Validated profiles: Llama 3 instruct, SmolLM2-360M (Q4_K_M), and
  **Qwen3-4B Q4_K_M with tool calling** (`#L27-L52`). GGUF context is capped at **4096 tokens** (Candle
  0.11's quantized cache, `#L50-L52`). CPU only (`#L171-L172`). The pinned Qwen3-4B file is 2.33 GiB and
  loading needs more than twice that in RAM (`#L109-L132`). `output_schema` is not grammar-constrained;
  tool output mode is best-effort (`#L88-L92`).
- **[I]** An embedded tier is viable for small, well-scoped tasks (classifying a request, naming units,
  short dialogue lines). The 4096-token cap forces the aggressive budgeting in §5. Model selection is
  outside this document's scope.

### 1.9 TypeSafe "Jev" (`rig-typesafeai`) [V]

A typed client for `POST https://api.typesafe.ai/v1/systemone`, model `jev-latest`, token `JEV_TOKEN`
(`crates/rig-typesafeai/src/wire.rs#L39-L69`). Question primitives: `Choice` (2–255 options), `Score`
(2–10-level rubric), `Noul` (yes/no probability) (`README.md#L60-L72`). Answers are distributions;
"Confidence measures concentration, not correctness" (`#L91-L94`). Marked experimental. TypeSafe's API
page describes only a hosted API, with no pricing and no open weights (<https://docs.typesafe.ai/api>).
The crate is not published yet (a 0.0.0 placeholder on crates.io).
**[I]** Useful as an optional cheap judge or router ("is this a *place units* or a *write briefing*
request?", "does this briefing contradict the objectives?"), never as a requirement, because it is a
single-vendor hosted service.

### 1.10 Testing support [V]

`rig-cassette` provides effect logs, record/replay adapters and an HTTP cassette engine; its default
features pull no runtime (`crates/rig-cassette/README.md#L1-L30`). It is only on `main`; crates.io has
a 0.0.1 placeholder. **[I]** Once it is released, we can record agent runs
against *synthetic* missions and replay them in CI without network access or API keys. This fits our
rule of using only synthetic fixtures.

### 1.11 Maturity and churn [V]

| Signal | Value |
|---|---|
| Latest release | 0.42.0, 2026-08-17 (`CHANGELOG.md#L12`; crates.io). No release since, although `main` has more breaking changes (§1.0). |
| Cadence | 0.37.0 (05-13), 0.38.0 and 0.38.1 (06-02), 0.38.2 (06-09), 0.39.0 (06-19), 0.40.0 (07-10/11), 0.41.0 (07-28), 0.42.0 (08-17) (crates.io, `CHANGELOG.md#L12-L738`) |
| Breaking changes | Every minor release from 0.39.0 to 0.42.0 has `[**breaking**]` CHANGELOG entries. `MIGRATING.md` is 5,239 lines. The "0.41 → next" section spans `#L814-L4091`. It is the 0.42.0 guide (L797-L2780 in the published 0.42.0 tarball, which has 3,923 lines in total) plus changes added on `main` since the release. Examples: `OneOrMany` removed (0.42.0); the transport split into `rig-reqwest` and MCP moved to `rig-rmcp` (unreleased). |
| Warning | "future updates **will** contain **breaking changes**" (`README.md#L45-L46`) |
| Adoption | rig-core has 3,027,617 total downloads (crates.io, 2026-09-26). The README lists users including St Jude, Neon, VT Code and ilert (`README.md#L100-L116`). |
| Toolchain | Edition 2024, pinned rustc 1.95.0 (`rust-toolchain.toml`). No declared MSRV. |
| License | MIT (`LICENSE`, `Cargo.toml#L5`). Compatible with any license we choose, including GPL-3.0. |

---

## 2. Alternatives compared

Registry data is live from crates.io and GitHub, fetched 2026-09-26.

| Option | License | Latest | Providers | Tool loop / hooks | Unified effort | MCP | Fit |
|---|---|---|---|---|---|---|---|
| **rig** (rig-core/agent/memory) | MIT | 0.42.0 (2026-08-17) | 26 modules on `main` (27 in 0.42.0); native Anthropic, Gemini, OpenAI, Ollama | **Yes**, rich hooks, durable runs | No (per provider) | Client only: rig-agent `rmcp` feature in 0.42.0 / `rig-rmcp` on main (both rmcp 2.x) | **Best feature fit; highest churn** |
| **genai** (jeremychone/rust-genai) | MIT OR Apache-2.0 | 0.6.5 stable; 0.7.0-beta.24 (2026-09-23) | 27+ incl. Anthropic, Gemini, OpenAI Responses, Ollama, DeepSeek, Bedrock | No agent loop (chat + tools only) | **Yes**: `ChatOptions.reasoning_effort` = `None/Minimal/Low/Medium/High/XHigh/Max/Budget(u32)` | Not mentioned | Strong plan B for "wires only" |
| **async-openai** (64bit) | MIT | 0.42.0 (2026-09-09) | OpenAI plus compatible base URLs | No | OpenAI only | No | Too narrow (no native Anthropic or Gemini) |
| **llm** (graniet/llm) | MIT | 1.3.8 (2026-04-19) | About 12 incl. Anthropic, Ollama, DeepSeek, Google | Chains, basic agents | Claimed "reasoning" | Not verified | Slower cadence, 121K downloads |
| Community Anthropic crates (`anthropic-sdk-rust`, ThreatFlux, …) (unverified) | varies | varies | Anthropic only | No | Anthropic only | No | Not official. Anthropic's official SDKs are Python, TS, Java, Go, Ruby, C#, PHP and a CLI (<https://platform.claude.com/docs/en/api/client-sdks>). A Rust SDK request (issue #1559, opened 2026-05-17) is still open. |
| **rmcp** (official MCP SDK) | Apache-2.0 | 3.4.1 (2026-09-23) | n/a | n/a | n/a | **Server + client** | Use directly for our MCP server |
| **Own thin layer** (reqwest + serde) | ours | ours | Whatever we write | Whatever we write | Ours | via rmcp | Hidden cost (below) |

Sources: crates.io API for `rig-core`, `genai`, `async-openai`, `llm` and `rmcp`; the genai docs.rs pages
for `ChatOptions` and `ReasoningEffort`; the genai, async-openai and graniet/llm GitHub READMEs;
anthropics/anthropic-sdk-python#1559.

**What a "thin own layer" really costs [V/I].** Covering three wire grammars well means SSE parsing,
tool-call delta assembly, signature-preserving reasoning replay, cache markers, error mapping and usage
normalization. rig's Anthropic mapping alone is `anthropic/completion.rs` (2,181 lines) plus
`anthropic/streaming.rs` (768 lines). Gemini's `completion.rs` is 2,139 lines. The agent engine
(`rig-agent/src/agent/engine.rs`) is 2,346 lines, plus 10,170 lines of tests in `engine/tests.rs`. These
are total line counts on `main`. A minimal OpenAI-compatible
client (which also reaches Ollama, llama.cpp, LM Studio, OpenRouter, DeepSeek and Mistral) is small.
Native Anthropic and Gemini with streaming tool calls and thinking is weeks of work plus ongoing upkeep.
**[I]** Renting this layer is worth the churn, *if* the churn is contained to one crate.

---

## 3. Recommendation: provider layer

### 3.1 Architecture (own the seam, rent the wires) [I]

```text
ofp-mission / ofp-config / ofp-wrp / ofp-sqf   (pure parsers; never see LLM types)
            │
ofp-editor-core ── EditorCommand bus + undo stack + validation (human and AI edits use the same path)
            │
ofp-agent        (OUR types: AgentSession, EditorTool trait, Effort, ContextBudget, RefStore,
            │     ApprovalPolicy, Workflow; conformance tests over a fake backend)
            ├── ofp-agent-rig     (ONLY crate importing rig-core / rig-agent / rig-memory)
            ├── ofp-agent-genai   (optional plan B, same trait)
            └── ofp-mcp           (rmcp 3.x server exposing the same EditorTools to external agents)
```

- **Pin exactly:** `rig-core = { version = "=0.42.0", default-features = false }`, and the same for
  `rig-agent` and `rig-memory`. At 0.42.0, `rig-core` carries reqwest itself. `=0.42.0` of `rig-reqwest`
  cannot resolve because only a 0.0.0 placeholder exists (§1.0). Add `rig-reqwest` (feature `rustls`)
  with the first release that publishes it. Upgrade on purpose, one version at a time, reading that
  release's section of `MIGRATING.md`.
- **Our `EditorTool` trait** mirrors rig's `Tool`: name, description, a `schemars` schema, typed args, and
  a typed error enum from `thiserror`. The adapter wraps each `EditorTool` into a rig `Tool` or
  `DynamicTool`, and `ofp-mcp` wraps the same trait into an rmcp tool. One definition serves both the
  in-app agent and external agents.
- **Tool execution never mutates state directly.** The tool sends an `EditorCommand` over a channel to
  the UI/editor thread and awaits the result (applied, rejected, or pending approval).
- **Approval:** an `ApprovalHook: AgentHook` whose `on_dispatch` (0.42.0: `on_tool_call`) consults
  `ApprovalPolicy`. It is fail-closed. `skip(reason)` tells the model why a call was refused.
- **Workflows:** per-turn `RequestPatch.active_tools` restricts which tools the model sees. For example,
  a "Briefing writer" workflow sees only read tools plus `set_briefing`. This also saves prompt tokens on
  tool schemas.

### 3.2 Provider tiers to expose in the UI [I]

These follow the tiering the user already designed for Iron Curtain: `ProviderTier { IcBuiltIn,
CloudOAuth, CloudApiKey, LocalExternal }` and `PromptStrategyProfile { max_context_tokens, schema_mode,
retry_repair_passes, ... }`
(`iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D047-llm-config.md#L466-L518`).

| Tier | rig mechanism |
|---|---|
| Cloud API key: Anthropic, OpenAI, Gemini, DeepSeek, Mistral, OpenRouter | Native wires or OpenAI dialects |
| Local external: Ollama, llama.cpp server, LM Studio, vLLM | `ollama` wire, `LLAMACPP` dialect, `OpenAI::with_base_url` |
| Embedded (optional download) | `rig-candle` (Qwen3-4B Q4_K_M; 4096-token cap) or a sidecar server (another doc's decision) |
| External agent (Claude Code, Codex, opencode, …) | Our `ofp-mcp` server; no model runs in-app at all |

### 3.3 Effort mapping (owned by `ofp-agent-rig`) [I, provider params partly V]

| Our `Effort` | OpenAI Responses (V) | Gemini (V: `ThinkingConfig`) | Anthropic `output_config.effort` (V, docs; raw JSON in rig) | Local / candle |
|---|---|---|---|---|
| Off | `ReasoningEffort::None` | `thinking_budget: Some(0)` | no "off" level: use `low` (thinking cannot be disabled on Opus 5.5) | Qwen no-think (default in rig-candle, `README.md#L83-L86`) |
| Low | `Low` | small budget | `low` | same |
| Medium | `Medium` | medium | `medium` | same |
| High | `High` | large | `high` | same |
| Max | `Max` / `Xhigh` | largest allowed | `max` (or `xhigh`), where the model supports it | same |

Beyond this table, the "effort level" in our UI also sets: `max_turns`, the retry budget,
`ContextBudget` sizes, and whether a planner/critic pass runs. Those are harness decisions and work the
same with every provider.

### 3.4 MCP decision [V/I]

Expose editor tools through **`rmcp` 3.x as an MCP server** (`ofp-mcp`). This lets users drive the
editor from their existing agent subscriptions with zero model plumbing on our side. Pull in rig's MCP
client (rig-agent `rmcp` feature at 0.42.0; `rig-rmcp` once published; rmcp 2.x either way) only when the
in-app agent needs *external* MCP tools. Revisit when rig moves to rmcp 3.

### 3.5 What not to use [I]

- The `rig` facade crate with default features: on `main` it always brings in `rig-cassette` and, by
  default, `derive`. `reqwest-middleware` is *not* a default feature (`Cargo.toml#L401`, `#L481`).
- ChatGPT or Copilot subscription wires: terms unknown (§1.2).
- `rig-ecs`, unless our UI is Bevy.
- rig's vector stores: the design already favors SQLite FTS for retrieval
  (`iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D057-llm-skill-library.md#L176-L179`).

### 3.6 Exit strategy [I]

Keep a backend conformance suite in `ofp-agent`: scripted fake model, tool round-trips, approval
deny/skip, extraction retry, and budget trimming. Run it against `ofp-agent-rig` with cassettes. If rig's
churn exceeds our upgrade budget (for example, more than one day of work per release), switch to a
`genai`-backed adapter and our own loop. Since `AgentRun` is sans-I/O, this can happen one piece at a
time.

---

## 4. headroom in detail

### 4.1 What it is and how it works [V]

Headroom "compresses everything your AI agent reads — tool outputs, logs, RAG chunks, files, and
conversation history — before it reaches the LLM" and runs locally
(`headroomlabs-ai/headroom@7968122658:README.md#L35-L38`). The pipeline is `CacheAligner → ContentRouter
→ CCR` (`#L56-L81`):

- **ContentRouter** detects the content type and picks a compressor.
- **SmartCrusher** handles JSON arrays. It keeps "error items, values outside the normal statistical
  range, and first/last boundaries, selected from field-variance statistics rather than a keyword list"
  (`#L385`).
- **CodeCompressor** is tree-sitter AST-aware. Code mostly passes through by design
  (`docs/content/docs/limitations.mdx#L56-L70`).
- **Kompress-v2-base** is an ML compressor for prose (§4.3).
- **LogCompressor** handles build/test output. It classifies each line (error, fail, warn, …), keeps
  stack traces and summary lines, dedupes, and adapts the kept-line budget
  (`crates/headroom-core/src/transforms/log_compressor.rs#L1-L20`).
- **Adaptive K** sets how many array items survive. It finds the knee (Kneedle) of a
  unique-bigram-coverage curve, uses SimHash to detect near-duplicates, and runs a zlib diversity check
  (`transforms/adaptive_sizer.rs#L1-L17`). The kept budget is split 30% start, 15% end, 55% by
  importance. Errors, anomalies above 2σ and change points are kept *in addition* to that budget
  (`limitations.mdx#L113-L130`).
- **CCR (Compress-Cache-Retrieve)** makes compression lossy on the wire but lossless end to end.
  Originals are stored under a BLAKE3 hash prefix, a `<<ccr:HASH>>` marker goes into the prompt, and the
  model calls a `headroom_retrieve(hash)` tool to get the original back
  (`crates/headroom-core/src/ccr/mod.rs#L1-L8`, `#L59-L100`; `headroom/ccr/tool_injection.py#L37-L98`).
  The TTL is an idle window (default 30 min) with an absolute cap of 8× (`ccr/mod.rs#L62-L80`).
- **Cache safety:** only the "live zone" (the newest user message and its tool results) is compressed.
  Bytes outside rewritten blocks are copied verbatim ("byte-range surgery"), never re-serialized, so
  provider prompt caches stay valid (`transforms/live_zone.rs#L1-L86`). The Rust live-zone dispatcher
  currently handles only the Anthropic `/v1/messages` shape (`live_zone.rs#L12-L32`). Anthropic
  `cache_control` markers define a frozen floor (`crates/headroom-core/src/cache_control.rs#L1-L36`). A `tool_use` and its `tool_result` are compressed
  together or not at all (`transforms/safety.rs#L1-L21`). The project *retired* its message-dropping
  transforms (IntelligentContext, RollingWindow) in favor of live-zone-only compression
  (`README.md#L407`).
- **Tag protection:** custom XML-like tags (for example `<thinking>`) are swapped for placeholders before
  ML compression and restored afterwards (`transforms/tag_protector.rs#L1-L16`).
- **Output shaping (opt-in):** "verbosity steering" appends a terse-style note to the *end* of the
  system prompt, preserving the cache. "Effort routing" dials thinking effort down on turns that only
  resume after a tool result; new questions and errors keep full effort. It is clamp-only
  (`README.md#L170-L186`).

### 4.2 Implementation, integration modes, packaging [V]

- The product is Python (`pyproject.toml`: `headroom-ai` 0.39.0, Python ≥ 3.10, maturin build) with a
  TypeScript SDK. The pinned tree has 544 `.py` files under `headroom/` and 199 `.rs` files under
  `crates/`.
- Rust workspace crates: `headroom-core`, `headroom-proxy`, `headroom-py` (PyO3), `headroom-parity`
  and `headroom-simulators` (`Cargo.toml#L1-L20`). The Rust side is a parity port measured byte-for-byte
  against Python fixtures (`RUST_DEV.md#L1-L25`, `smart_crusher/mod.rs#L1-L11`).
- Integration modes (`README.md#L45-L54`): inline `compress(messages)` library (Python/TS); `headroom
  proxy` (OpenAI/Anthropic-compatible HTTP proxy); `headroom wrap <agent>`; an MCP server
  (`headroom_compress`, `headroom_retrieve`, `headroom_stats`).
- `headroom-core` is version 0.1.0, edition 2021 (`crates/headroom-core/Cargo.toml#L3`). crates.io
  returned 404 for `headroom-core` on 2026-09-26, so it is **not published**.
- Default feature `ml` pulls in `ort` (ONNX Runtime, `=2.0.0-rc.12`), `fastembed` and `magika`. Other
  dependencies include pinned tree-sitter grammars, `rusqlite` (bundled), `icu_segmenter`, `hf-hub`,
  `tiktoken-rs` and `tokenizers` (`Cargo.toml#L16-L25`, `#L55`, `#L86`, `#L121-L189`).
- Code style: 142 matches of `.expect(` or `[..24]` across 33 `headroom-core` source files (the count
  includes in-file test modules). For example, `ccr/mod.rs#L91` slices `hex.as_str()[..24]` and
  `smart_crusher/anchors.rs#L31-L58` uses `.expect` on regex compilation. Our lints forbid both.
- License: Apache-2.0 (`LICENSE`, `README.md#L672-L674`). The anonymous telemetry beacon is **on by
  default** in the product and can be disabled with `HEADROOM_BEACON=off` or `DO_NOT_TRACK=1`
  (`README.md#L596-L606`, `limitations.mdx#L161-L180`).

### 4.3 The Kompress model [V]

`chopratejas/kompress-v2-base` is a ModernBERT-base fine-tune with a per-token keep/discard head: a word is
kept when its score exceeds 0.5, over 350-word chunks of at most 512 tokens
(`transforms/kompress.rs#L1-L40`, `#L71-L106`). The model card
(<https://huggingface.co/chopratejas/kompress-v2-base>) states: Apache-2.0; 150M base parameters plus
4.4M LoRA parameters; ONNX weight-only int8 (`int8-wo`) 274 MB, fp32 601 MB; labels produced by DeepSeek-V4-Flash and judged by
DeepSeek-V4-Pro; test split F1 0.920, must-keep recall 0.989, keep rate 0.866 ("13% compression").
**[I]** For our content (SQF, config classes, mission trees, structured lists) a prose token-dropper is
the wrong tool: dropping words from SQF or class names breaks semantics, and a 274 MB ONNX Runtime
dependency is out of proportion for an editor.

### 4.4 Evidence of quality [V]

- **Seeded, offline proof table** (`README.md#L132-L152`, `benchmarks/index_proof_table.py --seed
  20260902`): input savings of 21% (code search), 57% (SRE incident), 42% (codebase exploration) and 30%
  (issue triage). The README adds that "prose and already-dense output compress very little".
- **Accuracy, tier-1 evals at N=100** (`README.md#L157-L168`): GSM8K unchanged (0.870 → 0.870);
  TruthfulQA "no detectable difference"; SQuAD v2 97% at 19% compression; BFCL (tool use) 97% at 32%.
- **Caveats the project states itself:** per-content-type ratios are "directional single-sample"
  measurements (`limitations.mdx#L10-L21`); the QA-accuracy comparison has no committed result artifact
  (`benchmarks.mdx#L56-L60`); the SmartCrusher accuracy test is a substring check that the injected error
  survives (`benchmarks.mdx#L43-L54`).
- **[I] Verdict:** credible for repetitive JSON/log payloads (the anomaly-preserving design is sound);
  thin for LLM-graded end-task quality. We must measure our own reducers on our own tasks (§5.7).

### 4.5 Verdict on headroom [I]

- **Do not** bundle headroom, its proxy, or `headroom-core`: the product is Python-first, the Rust core is
  unpublished and heavy, its code style conflicts with our lints, telemetry is on by default, and it
  targets coding-agent traffic.
- **Do** copy its *design rules*. If we port any code verbatim, Apache-2.0 requires keeping the license
  and NOTICE attribution. Apache-2.0 code may be combined into a GPL-3.0 project but not into a
  GPL-2.0-only one. Whether any of this matters depends on the project license, which another research
  doc decides.

---

## 5. Context budgeting for the OFP editor agent

### 5.1 Where the tokens will go [I]

These are estimates. Measure them locally on real game data, which must never be committed.

| Source | Why it is large | Dumping it verbatim would… |
|---|---|---|
| Config catalogs (`CfgVehicles`, `CfgWeapons`, …) | Hundreds to thousands of classes with inheritance **[U: count unmeasured]** | burn the whole budget on names the model will never use |
| Mission (`mission.sqm`) | Groups → units → waypoints, triggers, markers; tree-shaped class text | repeat near-identical unit blocks many times |
| WRP object lists | Potentially tens of thousands of placed objects (trees, buildings) **[U]** | be useless without spatial aggregation |
| SQF scripts, game logs | Long; errors are sparse | hide the one error line |
| Conversation history + tool schemas | Grows each turn | break prompt-cache hits if reordered |

### 5.2 Rule 1: design tools that query, not dump (largest lever) [I]

headroom compresses output that tools have already dumped. We write the tools ourselves, so we can avoid
the dump in the first place. Examples:

| Tool | Behavior |
|---|---|
| `catalog.search {query, kind, side, faction, limit≤25}` | Ranked class names + display names + 1-line stats; `total_matches` |
| `catalog.describe {class}` | One class with resolved inheritance |
| `mission.outline {}` | Counts per side/group, objectives, trigger names (no unit bodies) |
| `mission.get {entity_id}` | One entity in full |
| `world.objects_summary {bbox, grid}` | Counts per class per grid cell, plus notable landmarks |
| `sqf.read {file, lines}` / `sqf.find {pattern}` | Paged; never the whole file by default |

Every list tool returns `{items, returned, total, next_cursor}` so the model *knows* the output is partial.
This matches the paging discipline of the D047 `PromptStrategyProfile.max_context_tokens` idea (§3.2).

### 5.3 Rule 2: reversible truncation (headroom's CCR, simplified) [I, pattern V]

- Any tool result above `T_result` tokens (default about 1.5k; smaller for the embedded tier) is stored in
  an in-memory `RefStore`. The key is a BLAKE3 hex prefix, the same scheme as
  `ccr/mod.rs#L82-L100`, wrapped in a `RefId` newtype.
- The model receives a *reduced* view (§5.4), a header `{ref: "r:3f9a…", total_items, shown_items,
  omitted: "…"}`, and access to one extra tool `expand_ref {ref, cursor|filter|lines}`.
- The store is scoped to the session. The idle TTL is irrelevant in-process; we clear it when the
  session ends.
- Wiring: an `on_outcome` hook calls `OutcomeAction::rewrite_tool_output(...)`
  (`rig-agent/src/agent/hook.rs#L818-L834`). Alternatively, the tool itself returns the reduced view and
  puts the full payload in `ToolContext` host-only metadata (`rig-core/src/tool/contextual.rs#L1-L3`).

### 5.4 Rule 3: domain reducers with an additive must-keep set [I, pattern V]

Pattern from SmartCrusher and LogCompressor: select K items by importance, then **add** everything in
the must-keep set, even past K (`limitations.mdx#L113-L130`). Our must-keep set: IDs or names in the
user's prompt (headroom's "query anchors", `anchors.rs#L65-L70`); entities selected in the editor;
anything with a validation error; outliers (a unit far from its group, a waypoint on water); and the
first and last items of each list (schema and recency).

| Data | Reducer |
|---|---|
| Class list | Group by parent class / side / category and emit counts. Keep K representatives per group plus the must-keep set. |
| Mission tree | Collapse identical sibling units to `"6× SoldierWB (same loadout)"`. Keep leaders, named units and units referenced by triggers or scripts. |
| WRP objects | Grid histogram per class. List individually only named or landmark objects and those inside the query bbox. |
| SQF / logs | Keep error and warn lines plus ±N context lines. Dedupe repeats with a count. Keep the file header (params). |

Gate every reduction the same way headroom's PR-B4 does: if the reduced view is not smaller than the
original, send the original (`live_zone.rs#L57-L60`).

### 5.5 Rule 4: a byte-stable prefix and an append-only history [I, pattern V]

- **Order:** system prompt → tool schemas → static "game digest" (sides, factions, map name, a few
  catalog stats) → conversation history → *volatile* editor state (selection, camera, time of day) last.
  Anthropic caching in rig: `with_automatic_caching()` (`anthropic/wire.rs#L359-L399`). **[U]** Other
  providers' automatic prefix caching behavior must be verified per provider.
- **Never** re-serialize or reorder earlier turns. Compress only the newest tool results (the "live
  zone").
- **Never** drop a tool call without its result. `rig-memory`'s window policies cut at message
  boundaries and then drop any leading tool result whose call fell outside the window, so no orphaned
  result survives (`crates/rig-memory/README.md#L15-L21`).
- When history must shrink, first **summarize older turns into a mission-state digest** (the editor state
  is ground truth, so the digest can be regenerated from it), then window. Do not drop mid-exchange.

### 5.6 Rule 5: a budget ledger [I, API V]

For each request:

```text
available = model.context_tokens            (rig model listing `context_length` if reported, else user profile)
          - reserve_output                  (max_tokens for this turn)
          - safety_margin                   (5–10%)
fixed     = system + tool schemas (of active_tools only) + game digest
dynamic   = available - fixed  →  split: history (TokenWindowMemory) | live tool results | mission-state digest
```

- **Estimation:** `rig_memory::HeuristicTokenCounter` counts UTF-8 bytes ÷ bytes-per-token plus
  per-message and per-attachment overheads; `anthropic()` is 3.5 bytes/token
  (`crates/rig-memory/src/lib.rs#L252-L294`). `TokenWindowMemory` applies a token budget through the
  `TokenCounter` trait (`#L223-L226`, `#L373-L376`).
- **Calibration:** after each response, update a per-model EMA of `Usage.input_tokens / estimated_tokens`
  (`rig-core/src/completion/request.rs#L321-L344`). The next estimate uses that ratio. This avoids
  bundling tokenizers; headroom bundles `tiktoken-rs` and HF `tokenizers` to do the same job
  (`headroom-core/Cargo.toml#L16-L20`).
- The embedded tier (4096 tokens) needs its own profile: very small `T_result`, 5–10 active tools per
  workflow, and a digest-only history.

### 5.7 Rule 6: effort routing and measurement [I, pattern V]

- **Clamp-only effort routing**, as headroom does (`README.md#L180-L186`): the user's `Effort` is the
  ceiling. Turns that only continue after a successful read-only tool result may drop one level through
  `RequestPatch.additional_params` in `on_completion_call`. New user requests, tool errors and validation
  failures run at full effort.
  - **Conflict with Rule 4 [V]:** on Anthropic, changing top-level `output_config.effort` between requests
    invalidates cached prefixes (effort docs, §1.7). Per-turn effort routing is therefore cache-safe only
    through the beta per-message `output_config` on models that support it. Otherwise, keep effort
    constant within a conversation. **[U]** Whether changing OpenAI `reasoning.effort` or Gemini thinking
    settings affects their prompt caches is not verified.
- **Measure** each reducer on synthetic missions with a fixed task set, for example "add a squad to the
  selected group", "fix the trigger that never fires", "write a 5-line briefing". Compare task success
  with and without reduction, and record tokens. This is our equivalent of headroom's seeded proof table:
  a fixed, seeded task set with repeated trials per configuration, scored by our own evaluation
  instruments rather than by the model.

### 5.8 headroom idea → our implementation seam

| headroom idea | Our seam (rig, pinned) |
|---|---|
| ContentRouter + compressors | Our `Reducer` trait per tool output type (typed, not content-sniffed; we know what each tool returns) |
| CCR + `headroom_retrieve` | `RefStore` + `expand_ref` tool + `on_outcome` rewrite (`hook.rs#L818-L834`) |
| Live zone / frozen prefix | Prompt assembly order (§5.5) + Anthropic caching helpers (`anthropic/wire.rs#L328-L399`) |
| Tool-pair atomicity | `rig-memory` window policies; our digest summarizer respects pairs |
| Tokenizer validation gate | `if reduced_est >= original_est { original }` |
| Effort routing | `on_completion_call` → `RequestPatch.additional_params` (`run/patch.rs#L13-L45`) |
| Fewer tool schemas | `RequestPatch.active_tools` per workflow step |
| Tag protection | Not needed (we don't run ML token-droppers) |

Sketch, not compiled; rig API names verified at `@42f4e060ef` (unreleased). On published 0.42.0, implement
`on_tool_result` and return `ToolResultAction::rewrite_output(...)` / `ToolResultAction::keep()` instead (§1.0):

```rust
// ofp-agent-rig: rewrite oversized tool results into a reduced view + ref handle.
struct BudgetHook { store: Arc<RefStore>, limits: BudgetLimits }
impl rig_agent::AgentHook for BudgetHook {
    async fn on_outcome(&self, _cx: &HookContext, ev: OutcomeEvent<'_>) -> OutcomeAction {
        let Some(result) = ev.tool_result() else { return OutcomeAction::proceed() };
        match self.store.reduce_if_oversized(ev.tool_name(), result, &self.limits) {
            Ok(Some(view)) => OutcomeAction::rewrite_tool_output(&ev, view.into_tool_output()),
            Ok(None) => OutcomeAction::proceed(),                 // small enough or not smaller
            Err(e) => { tracing::warn!(%e, "reduce failed; sending original"); OutcomeAction::proceed() }
        }
    }
}
```

---

## 6. Risks [I]

| Risk | Mitigation |
|---|---|
| rig breaking changes every ~3 weeks | One adapter crate, exact pins, conformance suite, genai plan B |
| rmcp 2 (rig-rmcp) vs rmcp 3 (our server) duplication | Avoid `rig-rmcp` until needed, or until rig moves to rmcp 3 |
| Anthropic effort/thinking params only via raw JSON in rig, possibly colliding with rig's typed `output_config` | Our mapping table + a cassette test per provider (docs verified, §1.7) |
| Code written against `main` names does not compile on published 0.42.0 | Target one released version; see §1.0 |
| Heuristic token estimates are wrong for some model | Per-model calibration EMA; generous safety margin; provider errors on overflow trigger an automatic retry with a smaller budget |
| Reducers hide the one thing the model needed | Additive must-keep set, `expand_ref`, and the task-level evaluation in §5.7 |
| Embedded 4096-token tier is too small for real edits | Limit embedded to narrow workflows; route larger tasks to BYO cloud/local models |

## Open questions

1. **[Resolved, V]** Anthropic effort is `output_config.effort` (`low`…`max`). See §1.7. Still open
   **[U]**: whether rig serializes a raw `output_config.effort` correctly next to its typed
   `output_config` when `output_schema` is set.
2. **[U]** Is using ChatGPT/Copilot *subscription* auth from a third-party desktop app allowed by those
   services' terms? Until answered, those rig providers stay hidden.
3. **[U]** Real sizes of CWA config catalogs, typical `mission.sqm` files and WRP object counts. These
   must be measured locally on owned game data and never committed. They set `T_result` and the reducer
   defaults.
4. **[U]** When will the next rig release publish `rig-reqwest`/`rig-rmcp` and the renamed hooks
   (names reserved on crates.io 2026-09-21)? When will rig move to rmcp 3.x, and will it reach a stability
   promise (1.0 or an LTS branch)? Nothing in the pinned repo commits to any of these.
5. **[I→decide]** Should the in-app loop use rig-agent's `AgentRunner` (fast start) or our own driver over
   the sans-I/O `AgentRun` (more control over durable review of batches of edits)? Suggested: start with
   `AgentRunner` + hooks; revisit when durable batch approval is built.
6. **[U]** Does genai 0.7 stabilize soon, and does its `ReasoningEffort` map to Anthropic and Gemini
   correctly? Its docs.rs page does not document the mapping.

## Sources

Pinned code (repo-relative paths with line ranges are cited inline above):

- `0xPlaygrounds/rig@42f4e060ef`: workspace `Cargo.toml`/`Cargo.lock`/`README.md`/`CHANGELOG.md`/
  `MIGRATING.md`; `crates/rig-{core,agent,derive,rmcp,candle,typesafeai,cassette,memory,ecs}`; `examples/*`.
- `headroomlabs-ai/headroom@7968122658`: `README.md`, `Cargo.toml`, `RUST_DEV.md`, `pyproject.toml`,
  `LICENSE`, `NOTICE`, `crates/headroom-core/**`, `headroom/ccr/tool_injection.py`,
  `docs/content/docs/{limitations,benchmarks}.mdx`.
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9`: `src/decisions/09f/D047-llm-config.md#L466-L518`,
  `src/architecture/crate-graph.md#L26`, `src/decisions/09f/D057-llm-skill-library.md#L176-L179`.

Live web sources (fetched 2026-09-26):

- <https://crates.io/api/v1/crates/rig-core> (0.42.0; 3,027,617 downloads; version dates)
- <https://crates.io/api/v1/crates/genai> (0.6.5 stable; 0.7.0-beta.24 on 2026-09-23)
- <https://docs.rs/genai/latest/genai/chat/struct.ChatOptions.html>,
  <https://docs.rs/genai/latest/genai/chat/enum.ReasoningEffort.html>, <https://github.com/jeremychone/rust-genai>
- <https://crates.io/api/v1/crates/async-openai> (0.42.0, 2026-09-09), <https://github.com/64bit/async-openai>
- <https://crates.io/api/v1/crates/llm> (1.3.8, 2026-04-19), <https://github.com/graniet/llm>
- <https://crates.io/api/v1/crates/rmcp> (3.4.1, 2026-09-23)
- <https://crates.io/api/v1/crates/headroom-core> (HTTP 404: not published)
- <https://github.com/anthropics/anthropic-sdk-python/issues/1559> (official Rust SDK request, open)
- <https://huggingface.co/chopratejas/kompress-v2-base> (model card)
- <https://docs.typesafe.ai/api> (Jev API overview)
- <https://platform.claude.com/docs/en/build-with-claude/effort> (Anthropic effort parameter),
  <https://platform.claude.com/docs/en/api/client-sdks> (official SDK list: no Rust)
- <https://crates.io/api/v1/crates/rig-reqwest>, `/rig-rmcp`, `/rig-cassette`, `/rig-typesafeai` (placeholders);
  `https://crates.io/api/v1/crates/{rig,rig-core,rig-agent,rig-memory}/0.42.0/dependencies`; the published
  `.crate` tarballs of `rig`, `rig-core`, `rig-agent`, `rig-memory` and `rig-candle` 0.42.0 (built from `d5a34986a1`)

## Verification notes

Adversarial fact-check, 2026-09-26. Method: reread every cited line range in the local clones at the
pinned SHAs; queried the crates.io API directly (not through a summarizer); downloaded and inspected the
0.42.0 `.crate` tarballs; fetched the genai docs.rs pages, the genai and graniet/llm READMEs, issue #1559,
the Kompress model card, the TypeSafe API page, and Anthropic's effort and SDK pages.

- **Confirmed:** rig-core 0.42.0 (2026-08-17), MIT, 3,027,617 downloads; the release dates; MIGRATING.md
  has 5,239 lines and the "0.41 → next" section spans L814-L4091; the README warning; the 28 provider
  modules (26 providers), the 21 dialects and 3 formats; `LLAMACPP`; `with_base_url` at `wire.rs#L912`; no
  neutral effort field; OpenAI `ReasoningEffort` variants; Gemini `ThinkingConfig` via additional params;
  the hook, `DispatchAction`, `OutcomeAction` and `RequestPatch` semantics; `AgentRun`
  `Serialize + Deserialize`; `rmcp = "2"` → 2.2.0; rmcp 3.4.1; the rig-candle claims; the genai variants,
  license and 0.7 betas; the open issue #1559; all headroom claims (Apache-2.0, 0.39.0, `headroom-core`
  0.1.0 unpublished, `ort =2.0.0-rc.12`, 142 `expect`/`[..24]` matches in 33 files, beacon on by default);
  the Kompress numbers; rig-memory 3.5 bytes/token.
- **Corrected:** (1) the pinned rig commit is unreleased `main`, not 0.42.0. Added §1.0. Fixed the
  `=0.42.0` pin, which included `rig-reqwest`, a crate that has only a 0.0.0 placeholder on crates.io.
  Noted that the 0.42.0 hook names are `on_tool_call`/`on_tool_result`. (2) The Anthropic effort shape was
  marked [U]; it is now verified from Anthropic's docs, and the §3.3 table, §5.7 (effort changes break the
  Anthropic cache) and the risks were updated. (3) `max_turns` is a model-call budget, not a count of tool
  rounds. (4) The rig line counts were non-blank counts labeled as "lines"; they are now total line counts.
  (5) The facade defaults do not include middleware. (6) The `cache_control.rs` path was fixed. (7) The
  Kompress 274 MB file is weight-only int8. (8) The rig-memory wording now says it drops orphaned results.
  (9) The "0.41 → next" section is the 0.42.0 guide plus later `main` additions.
- **Added:** the rig typed `output_config` vs raw `output_config.effort` collision risk (inferred from code,
  not tested). The community Anthropic crate names were not checked and are marked (unverified).
