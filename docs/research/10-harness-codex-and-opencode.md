# Harness Study: OpenAI Codex (codex-rs) and anomalyco/opencode

Research for the OFP/CWA Mission Editor rewrite (`DK26/ofp-editor`, Rust). This doc answers one question: **what can the
editor's built-in AI "harness agent" copy from Codex and opencode, or depend on?** Both are open-source coding-agent
harnesses. We studied their code, not just their READMEs.

**Epistemic markers** used throughout: **[V]** = verified in pinned code or a cited web source; **[I]** = inferred by
us from the code or from general engineering knowledge; **[U]** = unknown / not verified.

**Pinned sources** (code citations use `owner/repo@sha:path#Lx-Ly`):

- `openai/codex@e72da2b538`: commit of 2026-09-26. Rust workspace `codex-rs/` (153 workspace members, about 1.9M lines of `.rs`
  including tests).
- `anomalyco/opencode@b65de4d694`: commit of 2026-09-26. TypeScript/Bun monorepo (`packages/*`, about 675k lines of `.ts/.tsx`).

**Terms.** *Harness*: the program that wraps an LLM. It builds prompts, exposes tools, runs the model→tool→model loop,
enforces permissions and persists sessions. *Turn*: one user request processed until the model stops calling tools.
*Sampling request / step*: one model API call inside a turn. *Tool call*: the model asks for a named function with
JSON arguments, the harness runs it and feeds back the result. *Responses API*: OpenAI's newer `/v1/responses`
endpoint. *Chat Completions*: the older `/v1/chat/completions` endpoint, which most local servers support. *MCP*:
Model Context Protocol, a standard for connecting tools and servers to agents. *Compaction*: replacing old history with
a model-written summary when the context window fills. *Rollout*: Codex's name for a persisted session transcript.
*SQ/EQ*: submission queue / event queue.

---

## TL;DR

- **Recommendation: borrow patterns and selected code. Do not depend on Codex crates.** Codex is Apache-2.0 [V], so
  its code can be copied into our project if we keep the NOTICE and mark our changes. But its crates are `version 0.0.0`,
  they are not published by OpenAI on crates.io, and even `codex-protocol` pulls in heavy dependencies (exec policy,
  network proxy, ICU, Linux landlock/seccomp) [V]. opencode is MIT [V] but TypeScript, so it is a source of ideas only.
- **Codex's SQ/EQ core↔UI protocol is the model to copy for a GUI.** Typed `Op` submissions go in over a bounded
  channel. Typed `EventMsg` events come out over an unbounded channel, correlated by submission id (UUIDv7). Interrupts
  are just another `Op` [V]. This maps well onto an egui/iced frame loop that polls events [I].
- **Codex "dynamic tools" is the key pattern for us.** The host application declares tools with JSON Schema. When the
  model calls one, the core emits a request event and awaits the host's `Op::DynamicToolResponse` [V]. In our case the
  **editor owns the mission document**: the agent core never mutates the document itself, it asks the host to do it.
- **Tool errors are model feedback, not crashes.** Codex splits `RespondToModel` from `Fatal` [V]. opencode
  (a) auto-repairs mis-cased tool names, (b) routes unknown tools and bad arguments to a hidden `invalid` tool,
  (c) phrases schema-validation errors as "rewrite the input…", (d) asks the user after 3 identical calls in a row
  ("doom loop"; at this commit it only sees calls inside one model response, see §3.2) [V]. All four are essential for
  SLMs (small language models) [I].
- **Reasoning effort does not port across providers.** Codex models it as an enum plus per-model
  `supported_reasoning_levels`, resolved per model [V]. opencode calls it a "variant": a *named bundle of
  provider-specific options* chosen from a large hand-maintained per-provider table [V]. Our "effort level" should be
  a harness-level bundle that covers reasoning parameters and also step budget and self-check passes [I].
- **Codex now speaks only the OpenAI Responses API.** `wire_api = "chat"` and `ollama-chat` have been removed. The
  built-in local providers are Ollama ≥0.13.4 (per Codex's check) and LM Studio, both via `/v1/responses` [V]. Any other
  local server works only if it exposes `/v1/responses` and is added as a custom `model_providers` entry [V]. There is no native
  Anthropic path in the workspace provider list [V]. **We must own a multi-protocol provider layer.** opencode's split of
  `Protocol` (wire format) from `Route` (endpoint, auth, framing) is the design to copy [V].
- **Context management recipes to reuse:**
  - Auto-compact at about 90% of the context window.
  - Keep recent user messages (Codex keeps ≤20k tokens) plus a summary.
  - opencode uses a structured summary template with "prior summary" merging.
  - opencode prunes old tool outputs once more than 40k tokens of newer outputs sit on top of them.
  - Head/tail truncation of big tool outputs, with the full output spilled to a file [V].
- **Persistence:** Codex appends typed JSONL records (`rollout-<ts>-<id>.jsonl`) and supports resume/fork [V]. opencode
  uses SQLite, and its v2 is moving to event-sourced `session.next.*` events plus a projector [V]. For us: JSONL
  per session plus **one mission-state checkpoint per agent step**, so any agent action can be undone (opencode's
  snapshot/revert idea) [I].
- **Permissions:** we need a rule list (`allow/ask/deny` × tool × pattern, last match wins; `once/always/reject+feedback`)
  in the opencode style [V], not an OS sandbox. The editor agent gets **no shell tool**, so the sandboxing apparatus
  (Codex's `sandboxing`, `linux-sandbox`, `windows-sandbox-rs`, `execpolicy`) is irrelevant [I].
- **Cheap interoperability win:** both harnesses are MCP *clients* [V]. If the editor also exposes an **MCP server**
  ("ofp-editor tools"), Codex, opencode and others can drive it without any change on their side [I].

---

## 1. What the two repos are

| | openai/codex | anomalyco/opencode |
| --- | --- | --- |
| License | Apache-2.0 (`LICENSE`; workspace `license = "Apache-2.0"`). NOTICE credits Ratatui (MIT) [V] `openai/codex@e72da2b538:codex-rs/Cargo.toml#L159-L166` | MIT (`LICENSE`, "Copyright (c) 2025 opencode") [V] |
| Language | Rust 2024 edition, tokio. `clippy::unwrap_used`/`expect_used = "deny"` [V] `openai/codex@e72da2b538:codex-rs/Cargo.toml#L551-L590` | TypeScript on Bun, heavily built on Effect v4 beta [V] (`package.json` catalog) |
| Identity | OpenAI's coding agent. TUI, `exec` (headless), JSON-RPC `app-server` (used by IDE/desktop clients) [V] | Formerly `sst/opencode`, now under the **Anomaly** org: `github.com/sst/opencode` redirects to `anomalyco/opencode` [V], and a user comment on HN says "anomalyco now comprises of sst, opencode, etc." ([HN](https://news.ycombinator.com/item?id=46552218); not an official statement). Leftover CI guard: `if: github.repository == 'sst/opencode'` [V] `anomalyco/opencode@b65de4d694:.github/workflows/docs-update.yml#L13` |
| Version | crates are `0.0.0` path deps [V] | `packages/opencode` v1.18.32 [V] |
| State | Very active, very large; many features behind flags | Mid-migration: v1 runtime (`packages/opencode`, Vercel AI SDK) alongside v2 (`packages/core`, `llm`, `schema`, `server`, event-sourced) [V] |
| GUI story | TUI (ratatui). Desktop app is separate. Embeds the app-server **in-process** [V] | TUI (opentui/SolidJS), web app, Electron desktop (`electron 42.3.3`) spawning a local server [V] |

---

## 2. Codex (codex-rs) in depth

### 2.1 Crate map (what matters to us)

| Crate | Role | Lines (.rs, incl. tests) |
| --- | --- | --- |
| `protocol` | `Op`, `Event`, `EventMsg`, approvals, models/effort, token usage. Derives `serde`, `schemars`, `ts-rs` | 29.6k |
| `core` | Session, turn loop, tool router/registry/handlers, compaction, AGENTS.md | 397k |
| `tools` | `ToolExecutor` trait, `ToolSpec`, JSON-schema subset, truncation hooks | 7.4k |
| `codex-api`, `codex-client` | Responses API client (SSE + websocket), retry | 15.5k + 0.3k |
| `model-provider-info`, `model-provider`, `models-manager` | provider registry, auth, model catalog (`models.json`) | 1.7k + 7.5k + 3.2k |
| `rollout`, `history`, `thread-store`, `state` | JSONL persistence, resume/fork, SQLite index | 15k + … + 32k |
| `config` | TOML config, profiles, layered precedence, JSON schema | 27.6k |
| `codex-mcp`, `rmcp-client` | MCP client on `rmcp =3.2.0` [V] `openai/codex@e72da2b538:codex-rs/Cargo.toml#L444` | 23k + 33k |
| `ollama`, `lmstudio`, `utils/oss` | `--oss` local-model bootstrap | 1.0k + 0.4k |
| `app-server`, `app-server-protocol`, `app-server-client`, `core-api` | JSON-RPC surface and embedding facade | 33k (protocol) … |
| `hooks`, `skills`, `prompts`, `execpolicy`, `sandboxing`, `otel` | extensibility / safety / telemetry | — |

(Non-blank line counts measured by us over `*.rs` at the pinned commit. The ~1.9M figure in the header counts all lines;
non-blank is ~1.81M.)

### 2.2 Core↔UI protocol: SQ/EQ

- The protocol file opens: *"Uses a SQ (Submission Queue) / EQ (Event Queue) pattern to asynchronously communicate
  between user and agent"* [V] `openai/codex@e72da2b538:codex-rs/protocol/src/protocol.rs#L1-L4`.
- A `Submission { id, op, trace, parent_turn_id, root_turn_id, residency_guard }` [V]
  `openai/codex@e72da2b538:codex-rs/core/src/session/submission.rs#L7-L18`. The channel is created as
  `async_channel::bounded(SUBMISSION_CHANNEL_CAPACITY)` (512) for submissions and `unbounded()` for events [V]
  `openai/codex@e72da2b538:codex-rs/core/src/session/mod.rs#L502-L503,#L585-L586`. One spawned `submission_loop` task per session
  [V] `openai/codex@e72da2b538:codex-rs/core/src/session/mod.rs#L926-L932`. Submission ids are UUIDv7, so they sort by time and double as public turn ids [V]
  `openai/codex@e72da2b538:codex-rs/core/src/session/mod.rs#L1067-L1074`.
- `Op` (in-process only, `#[derive(Debug)]`, **not** serde) carries `oneshot::Sender` reply channels for ordered
  request/response operations. Examples: `TurnInput{request, mode, reply}`, `Interrupt`,
  `ExecApproval{id, turn_id, decision}`, `PatchApproval`, `UserInputAnswer`, `DynamicToolResponse{id, response}`,
  `Compact`, `ThreadSettings`, `Shutdown` [V] `openai/codex@e72da2b538:codex-rs/protocol/src/protocol.rs#L586-L766`.
- `Event { id /* correlated submission id */, msg: EventMsg }` [V] `openai/codex@e72da2b538:codex-rs/protocol/src/protocol.rs#L1338-L1345`. `EventMsg` is a serde-tagged enum
  with roughly 85 variants [V] `openai/codex@e72da2b538:codex-rs/protocol/src/protocol.rs#L1352-L1575`, including:
  - lifecycle: `TurnStarted`, `TurnComplete`, `TurnAborted`;
  - streaming: `AgentMessageContentDelta`, `ReasoningContentDelta`, `PlanDelta`;
  - item framing: `ItemStarted`, `ItemCompleted`;
  - approvals: `ExecApprovalRequest`, `ApplyPatchApprovalRequest`, `RequestUserInput`, `DynamicToolCallRequest`;
  - accounting: `TokenCount`, `ContextCompacted`;
  - other: `PlanUpdate`, `Error`, `Warning`, `StreamError`, `McpToolCallBegin/End`, and `Collab*` sub-agent events.
- **Two layers of protocol.** The in-process `Op`/`EventMsg` sits inside a *serializable* JSON-RPC v2 protocol for
  clients. That protocol has methods like `thread/start`, `turn/start`, `turn/steer`, `turn/interrupt`, server→client
  requests like `item/commandExecution/requestApproval` and `item/tool/call`, plus `thread/*` / `turn/*` notifications
  [V] `openai/codex@e72da2b538:codex-rs/app-server-protocol/src/protocol/common.rs#L551,#L1032-L1050,#L1765,#L1796`. The TUI now talks to an
  **in-process app-server**. Commands and the runtime stay bounded, but the consumer event queue is unbounded "so unread
  notifications cannot prevent request responses from being delivered" [V]
  `openai/codex@e72da2b538:codex-rs/app-server-client/src/lib.rs#L1-L17`.
- **Steering.** User input typed during a running turn is queued and drained at the top of each loop iteration, then
  recorded before the next sampling request [V] `openai/codex@e72da2b538:codex-rs/core/src/session/turn.rs#L424-L447`.

### 2.3 The agent loop

- `run_turn` doc comment: each sampling request yields function calls (execute, then feed outputs to the next request)
  or an assistant message (the turn ends) [V] `openai/codex@e72da2b538:codex-rs/core/src/session/turn.rs#L149-L170`. The main `loop` [V]
  `openai/codex@e72da2b538:codex-rs/core/src/session/turn.rs#L424-L645` does the following:
  - drains pending (steer) input;
  - captures a per-step context (tools advertised plus settings);
  - builds the prompt from history (`clone_history().for_prompt(...)`);
  - calls `run_sampling_request`;
  - then computes `needs_follow_up = model_needs_follow_up || has_pending_input`;
  - if the token limit is reached mid-turn, it **auto-compacts and continues**;
  - otherwise it runs stop hooks and ends.
- `run_sampling_request` wraps the request in a retry loop that uses provider `stream_max_retries`. It treats
  `ContextWindowExceeded` and `UsageLimitReached` as terminal [V] `openai/codex@e72da2b538:codex-rs/core/src/session/turn.rs#L1592-L1719`. Provider defaults are 5 stream retries,
  4 request retries and a 300 s stream idle timeout [V] `openai/codex@e72da2b538:codex-rs/model-provider-info/src/lib.rs#L63-L72`.
- `try_run_sampling_request` streams `ResponseEvent`s [V] `openai/codex@e72da2b538:codex-rs/codex-api/src/common.rs#L79-L131`:
  `Created`, `OutputItemAdded/Done`, `OutputTextDelta`, `ToolCallInputDelta`, `Reasoning*Delta`, `RateLimits`,
  `Completed{token_usage,end_turn}`. **Tool calls start executing as soon as their item is done**, pushed into a
  `FuturesOrdered` while the stream continues [V] `openai/codex@e72da2b538:codex-rs/core/src/session/turn.rs#L2748-L2762`. The results are drained in order after the
  stream completes [V] `openai/codex@e72da2b538:codex-rs/core/src/session/turn.rs#L2446-L2474,#L3122-L3140`.
- **Cancellation.** Every await is `.or_cancel(&preempt).or_cancel(&cancellation_token)`. A cancel yields
  `CodexErr::TurnAborted`. A "preempt" (new user input) instead ends the sampling early and marks the turn as needing
  follow-up [V] `openai/codex@e72da2b538:codex-rs/core/src/session/turn.rs#L2539-L2565,#L2611-L2632`. Running tool tasks are `AbortOnDropHandle`s. On cancel they are aborted and
  a synthetic "aborted" tool output is recorded [V] `openai/codex@e72da2b538:codex-rs/core/src/tools/parallel.rs#L244-L280`.

### 2.4 Tools: declaration, schema, validation, error feedback

- **Trait.** Each tool implements `ToolExecutor<Invocation>` with `tool_name()`, `spec()`, `exposure()`,
  `supports_parallel_tool_calls()` (default `false`), and `handle(invocation) -> BoxFuture<Result<Box<dyn ToolOutput>,
  FunctionCallError>>` [V] `openai/codex@e72da2b538:codex-rs/tools/src/tool_executor.rs#L101-L130`.
- **Exposure.** Tools can be `Direct`, `Deferred` (discoverable via a `tool_search` tool, which keeps the initial
  prompt small), `DirectModelOnly`, `DeferredModelOnly`, `CodeModeOnly`, or `Hidden` [V] `openai/codex@e72da2b538:codex-rs/tools/src/tool_executor.rs#L49-L80`. This matters for SLMs with small context windows [I].
- **Schema.** `ToolSpec` serializes directly to Responses-API tool JSON (`function`, `namespace`, `custom`/freeform
  grammar, `web_search`, `tool_search`) [V] `openai/codex@e72da2b538:codex-rs/tools/src/tool_spec.rs#L18-L56`. Parameters use a **hand-written
  JSON-Schema subset type** that mirrors OpenAI Structured Outputs (types plus `enum`, `anyOf/oneOf/allOf`, `$ref/$defs`)
  [V] `openai/codex@e72da2b538:codex-rs/tools/src/json_schema/types.rs#L8-L75`. Built-in tools build schemas by hand with constructors. Example:
  `update_plan` [V] `openai/codex@e72da2b538:codex-rs/core/src/tools/handlers/plan_spec.rs#L7-L58`. Arguments are then parsed with serde into a
  separate struct (`UpdatePlanArgs`, `deny_unknown_fields`) [V] `openai/codex@e72da2b538:codex-rs/protocol/src/plan_tool.rs#L7-L29`. **The schema and
  the Rust type are not generated from one source**, so they can drift [I]. `strict` is always `false`, and a TODO
  says strict validation is not implemented [V] `openai/codex@e72da2b538:codex-rs/tools/src/responses_api.rs#L32-L45,#L164-L173`.
- **External schemas** (MCP, dynamic tools) are sanitized: `const`→`enum`, missing `type` filled in, unreachable
  `$defs` pruned, large schemas compacted [V] `openai/codex@e72da2b538:codex-rs/tools/src/json_schema.rs#L25-L80`.
- **Error feedback.** `FunctionCallError::{RespondToModel(String), Fatal(String)}` [V]
  `openai/codex@e72da2b538:codex-rs/tools/src/function_call_error.rs#L3-L10`. A bad JSON argument becomes
  `RespondToModel("failed to parse function arguments: …")` [V] `openai/codex@e72da2b538:codex-rs/core/src/tools/handlers/plan.rs#L108-L112`. Mode violations also
  go back to the model ("update_plan … is not allowed in Plan mode") [V] `openai/codex@e72da2b538:codex-rs/core/src/tools/handlers/plan.rs#L87-L91`. Only `Fatal` aborts the turn
  [V] `openai/codex@e72da2b538:codex-rs/core/src/tools/parallel.rs#L99-L112`.
- **Parallelism gate.** A per-step `RwLock<()>`: tools that support parallel calls take a *read* guard, all others a
  *write* guard [V] `openai/codex@e72da2b538:codex-rs/core/src/tools/parallel.rs#L194-L225`. This is a simple and correct way to run queries concurrently and
  mutations serially.
- **Dynamic (host-executed) tools.** The client supplies `DynamicToolSpec::{Function, Namespace}` with a raw
  `input_schema` [V] `openai/codex@e72da2b538:codex-rs/protocol/src/dynamic_tools.rs#L10-L75`. On a call, the core registers a `oneshot` waiter keyed
  by `call_id` and emits `ItemStarted(DynamicToolCall{InProgress})`. It then awaits the host's
  `DynamicToolResponse{content_items, success}` and emits `ItemCompleted`. If the waiter is dropped, the model is told
  "cancelled before receiving a response" [V] `openai/codex@e72da2b538:codex-rs/core/src/tools/handlers/dynamic.rs#L116-L251`. Over JSON-RPC this
  appears as the server request `item/tool/call` [V] (`openai/codex@e72da2b538:codex-rs/app-server-protocol/src/protocol/common.rs#L1796`).

### 2.5 Approvals, permissions, sandboxing

- `AskForApproval = UnlessTrusted | OnRequest (default; "the model decides when to ask") | Granular{…} | Never` [V]
  `openai/codex@e72da2b538:codex-rs/protocol/src/protocol.rs#L968-L1026`. `Granular` toggles each prompt category (sandbox escalation, exec-policy
  rules, skill scripts, `request_permissions`, MCP elicitations). A `false` category is auto-rejected instead of shown
  to the user [V].
- Every approval reply is a `ReviewDecision`: `Approved | ApprovedForSession | ApprovedExecpolicyAmendment{…} |
  ApprovedMcpPolicyAmendment | NetworkPolicyAmendment{…} | Denied{rejection} | TimedOut | Abort` [V] `openai/codex@e72da2b538:codex-rs/protocol/src/protocol.rs#L4157-L4192`.
  `Denied` lets the agent continue and "try something else". `Abort` stops until the next user input [V].
- The tool orchestrator runs: approval → sandbox selection → attempt → retry with an escalated sandbox on denial, with
  approvals cached [V] `openai/codex@e72da2b538:codex-rs/core/src/tools/orchestrator.rs#L1-L8`. Sandbox modes: `read-only | workspace-write |
  danger-full-access` [V] `openai/codex@e72da2b538:codex-rs/protocol/src/config_types.rs#L104-L114`.
- `approvals_reviewer = user | auto_review` ("a carefully prompted subagent… risk-based decision framework") [V]
  `openai/codex@e72da2b538:codex-rs/protocol/src/config_types.rs#L183-L202`. **LLM-as-approver** is an interesting option for low-stakes editor edits [I].
- Hooks at `PreToolUse, PermissionRequest, PostToolUse, Pre/PostCompact, SessionStart/End, UserPromptSubmit,
  SubagentStart/Stop, Stop, Interrupt`, with handler types `Command | McpTool | Prompt | Agent` [V]
  `openai/codex@e72da2b538:codex-rs/protocol/src/protocol.rs#L1579-L1601`.

### 2.6 Reasoning effort

- `ReasoningEffort = None | Minimal | Low | Medium (default) | High | XHigh | Max | Ultra | Persistent | Custom(String)`.
  It serializes as a plain string, and unknown strings become `Custom` (forward compatible) [V]
  `openai/codex@e72da2b538:codex-rs/protocol/src/openai_models.rs#L56-L158`.
- **Per-model capability data.** `ModelInfo.supported_reasoning_levels: Vec<ReasoningEffortPreset{effort,
  description}>` and `default_reasoning_level`. The description is "Short human description shown next to the effort
  in UIs" [V] `openai/codex@e72da2b538:codex-rs/protocol/src/openai_models.rs#L194-L201,#L402-L415`. UI aliases are resolved per model: `Ultra` → the model's multi-agent effort or
  `Max` or its highest level; `Persistent` → wire value `"disabled"` [V]
  `openai/codex@e72da2b538:codex-rs/protocol/src/openai_models/reasoning_effort.rs#L8-L41`. On the wire: `reasoning: {effort, summary, context}`, and a numeric
  `Custom("8000")` becomes a JSON number [V] `openai/codex@e72da2b538:codex-rs/codex-api/src/common.rs#L156-L182`.
- **Config.** `model_reasoning_effort`, a separate `plan_mode_reasoning_effort`, `model_reasoning_summary`,
  `model_verbosity`, all settable globally or per profile [V] `openai/codex@e72da2b538:codex-rs/config/src/config_toml.rs#L391-L395`,
  `openai/codex@e72da2b538:codex-rs/config/src/profile_toml.rs#L36-L39`.
- **UI.** A "Select Reasoning Level for {model}" popup, plus a status-line item "model name with reasoning level" [V]
  `openai/codex@e72da2b538:codex-rs/tui/src/chatwidget/model_popups.rs#L639`, `openai/codex@e72da2b538:codex-rs/tui/src/bottom_pane/status_line_setup.rs#L61-L66`.
- Codex has **no step cap and no verification-pass setting**; user-facing "effort" is only the model parameter. It does
  have an experimental, feature-flagged **token budget** (`features.rollout_budget`: weighted `limit_tokens`,
  reminders with the remaining budget injected into context at `reminder_at_remaining_tokens` thresholds, and a
  `SessionBudgetExceeded` error once exhausted) [V] `openai/codex@e72da2b538:codex-rs/core/src/rollout_budget.rs#L11-L67`,
  `openai/codex@e72da2b538:codex-rs/core/src/agent/control/budget.rs#L11-L17`,
  `openai/codex@e72da2b538:codex-rs/core/src/session/rollout_budget.rs#L7-L31`, plus a per-goal `max_goal_token_budget`
  [V] `openai/codex@e72da2b538:codex-rs/config/src/config_toml.rs#L700-L705`. The "remaining budget" reminder is a
  pattern worth copying for our effort bundles [I].
  There are also "collaboration modes" `Plan | Default` [V] `openai/codex@e72da2b538:codex-rs/protocol/src/config_types.rs#L674-L684`.

### 2.7 Context management

- **Accounting.** `TokenUsage{input, cached_input, cache_write_input, output, reasoning_output, total}`, aggregated as
  `TokenUsageInfo{total, last, model_context_window}` and emitted via `TokenCount` events [V]
  `openai/codex@e72da2b538:codex-rs/protocol/src/protocol.rs#L2238-L2344`.
- **Window math.** `usable = context_window × effective_context_window_percent (default 95)/100`;
  `auto_compact_token_limit = min(configured, 90% of window)` [V] `openai/codex@e72da2b538:codex-rs/protocol/src/openai_models.rs#L513-L534`.
- **Compaction.** The prompt is a 9-line "CONTEXT CHECKPOINT COMPACTION… handoff summary for another LLM" [V]
  `openai/codex@e72da2b538:codex-rs/prompts/templates/compact/prompt.md#L1-L9`. The new history is: initial context, then the most recent user
  messages up to `COMPACT_USER_MESSAGE_MAX_TOKENS = 20_000` (the message that crosses the budget is truncated, older
  ones are dropped), then the summary [V]
  `openai/codex@e72da2b538:codex-rs/core/src/compact.rs#L55,#L662-L740`. There is also a server-side "remote compaction" path for OpenAI [V]
  (`openai/codex@e72da2b538:codex-rs/core/src/compact_remote_v2.rs`).
- **Truncation.** Tool output is cut in the middle to a byte or token budget, with the header
  `"Warning: truncated output (original token count: N)"` [V]
  `openai/codex@e72da2b538:codex-rs/utils/output-truncation/src/lib.rs#L20-L31`. Tokens are approximated as bytes/4 [V]
  `openai/codex@e72da2b538:codex-rs/utils/string/src/truncate.rs#L4,#L71-L74`. `tool_output_token_limit` is configurable [V]
  `openai/codex@e72da2b538:codex-rs/config/src/config_toml.rs#L336-L337`.

### 2.8 Session persistence / resume

- Transcripts are appended JSONL under `$CODEX_HOME/sessions/`, named
  `rollout-YYYY-MM-DDThh-mm-ss-<thread_id>[_<rollout_id>].jsonl` [V] `openai/codex@e72da2b538:codex-rs/rollout/src/lib.rs#L86-L87`,
  `openai/codex@e72da2b538:codex-rs/rollout/src/rollout_file_name.rs#L62-L74`.
- Each line is `RolloutLine{timestamp, ordinal?, #[flatten] item}`, where `RolloutItem = SessionMeta | ResponseItem |
  Compacted | TurnContext | TokenUsageRecord | EventMsg | …` [V] `openai/codex@e72da2b538:codex-rs/history/src/lib.rs#L199-L217,#L345-L356`.
- `InitialHistory = New | Cleared | Resumed | Forked` drives resume/fork [V]. A SQLite state DB indexes threads [V]
  (`openai/codex@e72da2b538:codex-rs/rollout/src/state_db.rs`). The dynamic-tool specs are persisted in `SessionMeta`, so resumed sessions re-advertise
  them [V] (`openai/codex@e72da2b538:codex-rs/history/src/lib.rs#L455-L459`).

### 2.9 Config

- `config.toml` in `$CODEX_HOME`, with `profile = "<name>"` and `[profiles.<name>]` bundles covering model, provider,
  approval, sandbox, efforts, instructions file, features and so on [V] `openai/codex@e72da2b538:codex-rs/config/src/profile_toml.rs#L20-L73`,
  `openai/codex@e72da2b538:codex-rs/config/src/config_toml.rs#L355-L360`.
- Layer precedence: packaged defaults (−10) < MDM (0) < system (10) < enterprise (15) < user (20) < user+profile (21)
  < project `.codex/` (25) < session flags (30) < legacy managed [V] `openai/codex@e72da2b538:codex-rs/config/src/config_layer_source.rs#L6-L51`.
- Per-model metadata comes from a model catalog (`models-manager/models.json`, 1,436 lines, or a remote `/models`)
  [V]. Users can override it with `model_catalog_json` [V].

### 2.10 Provider abstraction

- **Only one wire API.** `enum WireApi { Responses }`. Deserializing `"chat"` fails with "`wire_api = "chat"` is no
  longer supported", and `ollama-chat` is likewise removed [V] `openai/codex@e72da2b538:codex-rs/model-provider-info/src/lib.rs#L96-L130`.
- `ModelProviderInfo` fields: `base_url`, `env_key`, `http_headers`, `query_params`, retries/timeouts,
  `requires_openai_auth`, `supports_websockets`, AWS SigV4 [V] `openai/codex@e72da2b538:codex-rs/model-provider-info/src/lib.rs#L132-L200`. The comment on built-ins says: "We do not
  want to be in the business of adjucating [sic] which third-party providers are bundled with Codex CLI". Built-ins are `openai`,
  `amazon-bedrock`, `amazon-bedrock-runtime`, `ollama` (port 11434) and `lmstudio` (port 1234), all Responses [V]
  `openai/codex@e72da2b538:codex-rs/model-provider-info/src/lib.rs#L643-L682`.
- **`--oss`.** The default model is `gpt-oss:20b` (Ollama) or `openai/gpt-oss-20b` (LM Studio). Codex pulls or loads
  the model if missing and requires **Ollama ≥ 0.13.4** for the Responses API [V]
  `openai/codex@e72da2b538:codex-rs/ollama/src/lib.rs#L15-L70`, `openai/codex@e72da2b538:codex-rs/lmstudio/src/lib.rs#L6-L7`. Web sources say Ollama added a *stateless*
  `/v1/responses` in 0.13.3 [V] ([ollama#13595](https://github.com/ollama/ollama/issues/13595)), and LM Studio 0.3.29
  (2025-10-06) added `/v1/responses` with tools, streaming, `reasoning.effort` and `previous_response_id` [V]
  ([LM Studio blog](https://lmstudio.ai/blog/lmstudio-v0.3.29)). llama.cpp's `llama-server` README (master, fetched
  2026-09-26) documents `POST /v1/responses`, implemented "by converting Responses request into Chat Completions
  request" [V] ([llama.cpp server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)).
  The first llama.cpp release with it, and how well tool calls survive the conversion, are **[U]**.

### 2.11 MCP, AGENTS.md, skills, commands, sub-agents

- **MCP client**: stdio and streamable-HTTP transports, OAuth, resources, elicitations, on `rmcp =3.2.0` [V]. The CLI
  subcommand list at this commit has `mcp` (manage servers) and `app-server`, but **no `mcp-server` subcommand**, and
  there is no `mcp-server` workspace member [V] `openai/codex@e72da2b538:codex-rs/cli/src/main.rs#L142-L240`, `openai/codex@e72da2b538:codex-rs/Cargo.toml#L2-L156` (members). Codex
  therefore exposes itself to other programs through the JSON-RPC app-server, not through MCP. Internally it does use
  `rmcp`'s *server* side: the TUI runs an "approval-gated MCP transport for task tools" (streamable HTTP) to bridge
  host-owned dynamic tools [V] `openai/codex@e72da2b538:codex-rs/tui/src/dynamic_tools_mcp.rs#L1-L40`. That is a
  worked example of serving host-executed tools over MCP with `rmcp` [I].
- **AGENTS.md**: it concatenates every `AGENTS.md` from the project root (found by markers, default `.git`) down to the
  cwd. `AGENTS.override.md` takes precedence, and `project_doc_max_bytes` caps the total [V]
  `openai/codex@e72da2b538:codex-rs/core/src/agents_md.rs#L1-L49`. Skills (`SKILL.md`), plugins and hooks are separate subsystems [V] (`skills/`,
  `ext/skills`, `hooks/`).
- **Plans/todos**: the `update_plan` tool (steps with `pending|in_progress|completed`, at most one in progress) emits
  `EventMsg::PlanUpdate` [V] `openai/codex@e72da2b538:codex-rs/core/src/tools/handlers/plan.rs#L65-L99`, `openai/codex@e72da2b538:codex-rs/core/src/tools/handlers/plan_spec.rs#L44-L47`.
- **Sub-agents**: tools `spawn_agent`, `send_input`, `resume_agent`, `wait_agent`, `close_agent`, plus v2-style
  `send_message`, `followup_task`, `list_agents`, `interrupt_agent` [V]
  `openai/codex@e72da2b538:codex-rs/core/src/tools/handlers/multi_agents_spec.rs#L85-L351`, with `Collab*` events. There is also `request_user_input`
  (the agent asks the user a structured question) [V].

### 2.12 Embedding Codex in another Rust app (feasibility)

- `codex-core-api` is a "Public facade for thread management APIs built on `codex-core`". It re-exports
  `ThreadManager`, `CodexThread`, `Op`, `EventMsg`, `DynamicToolSpec`, `Config`… [V] `openai/codex@e72da2b538:codex-rs/core-api/src/lib.rs#L1-L145`.
- `thread-manager-sample` shows the minimum. It builds a `ThreadManager` from roughly 15 collaborators (auth manager,
  models manager, environment manager, extension registry, thread store, state DB…), then fills a large `Config`
  struct literal field by field [V] `openai/codex@e72da2b538:codex-rs/thread-manager-sample/src/main.rs#L149-L259`.
- **Verdict [I]:** feasible, but we would inherit `codex-core`'s full dependency graph (397k-line crate, exec-server,
  network proxy, sandbox crates, OpenAI auth/login). We would also be tied to the Responses API and to an unversioned
  (0.0.0) internal API that changes daily.

### 2.13 Telemetry and testing

- **Telemetry**: OpenTelemetry via `otel`. Log/trace exporters default to `None`, and prompt/response logging is
  opt-in, **but `metrics_exporter` defaults to `Statsig`** [V] `openai/codex@e72da2b538:codex-rs/config/src/types.rs#L633-L658`,
  `openai/codex@e72da2b538:codex-rs/core/src/config/otel.rs#L17-L21`. The Statsig exporter (an OTLP/HTTP endpoint at
  `ab.chatgpt.com`) is only used when `analytics_enabled` is on (the TUI passes default `true`; the standalone
  app-server binary passes `false`), and it is forced off in debug builds [V]
  `openai/codex@e72da2b538:codex-rs/core/src/otel_init.rs#L70-L77`, `openai/codex@e72da2b538:codex-rs/otel/src/config.rs#L9-L33`.
- **Testing** [V] (`openai/codex@e72da2b538:AGENTS.md#L114,#L182-L198,#L226-L242`):
  - integration tests use `core_test_support`: a wiremock mock Responses server with SSE builders such as
    `ev_response_created`, `ev_function_call(call_id,name,args)`, `ev_assistant_message`, `ev_completed`,
    `mount_sse_once` / `mount_sse_sequence` [V] `openai/codex@e72da2b538:codex-rs/core/tests/common/responses.rs#L740-L1497`;
  - tests assert on the captured outbound request bodies (for example the `function_call_output` returned to the
    model) [V] `openai/codex@e72da2b538:codex-rs/core/tests/common/test_codex.rs#L1384-L1411`;
  - UI tests use `insta` snapshots: 1,329 `.snap` files in `tui/` [V] (our count).

---

## 3. opencode in depth

### 3.1 Agent loop (v1, `SessionPrompt.run`)

- **The loop is DB-driven.** Each iteration re-reads the session's messages from storage, finds the last user and last
  assistant message, and exits if the last assistant finished with anything other than `tool-calls`/`unknown`
  and has no pending tool parts [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/session/prompt.ts#L1081-L1130`.
  Pending "tasks" (sub-agent calls, compaction) are handled first. An overflow check can insert an auto-compaction [V]
  `anomalyco/opencode@b65de4d694:packages/opencode/src/session/prompt.ts#L1142-L1168`.
- **Step budget.** Each agent has `steps` (default ∞). On the last step the harness appends an assistant message
  `MAX_STEPS_PROMPT` ("Tools are disabled… MUST provide a text response summarizing work done so far… remaining tasks")
  [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/session/prompt.ts#L1178-L1179,#L1279-L1282`, `anomalyco/opencode@b65de4d694:packages/core/src/session/runner/max-steps.ts#L1-L16`.
  In v1 this is **prompt-only**: the tool list is still sent on the last step and the loop is not hard-stopped
  (`isLastStep` is used only to append the prompt) [V] (same `prompt.ts` lines, `#L1226-L1286`). The v2 runner enforces
  it: on the last step it sends no tool definitions and `toolChoice: "none"` [V]
  `anomalyco/opencode@b65de4d694:packages/core/src/session/runner/llm.ts#L202-L220`.
- **Structured output.** When the user requests `format: json_schema`, the harness injects a `StructuredOutput` tool
  and sets `toolChoice: "required"` [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/session/prompt.ts#L1243-L1250,#L1285`.
- **Cancellation** uses Effect interruption. `finalizeInterruptedAssistant` marks the message with an `AbortError` [V]
  `anomalyco/opencode@b65de4d694:packages/opencode/src/session/prompt.ts#L1203-L1219`.
- **Retries** use exponential backoff (2 s × 2ⁿ, 25% jitter, cap 30 s without headers, max 5) and honour
  `retry-after(-ms)`. Retryable errors are classified with regexes [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/session/retry.ts#L26-L60`.

### 3.2 Tools

- **Definition.** `Tool.define(id, {description, parameters: EffectSchema, execute(args, ctx)})`. The single schema is
  the source for both the JSON Schema sent to the model (`Schema.toJsonSchemaDocument`) and runtime decoding [V]
  `anomalyco/opencode@b65de4d694:packages/opencode/src/tool/tool.ts#L55-L65,#L99-L149`, `anomalyco/opencode@b65de4d694:packages/opencode/src/tool/json-schema.ts#L12`. The wrapper decodes arguments, maps
  failures to `InvalidArgumentsError`, whose message is *"The X tool was called with invalid arguments: …Please rewrite
  the input so it satisfies the expected schema."*, and auto-truncates the output [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/tool/tool.ts#L18-L34,#L120-L145`.
  Tool context gives `abort`, `metadata()` (live progress) and `ask()` (permission) [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/tool/tool.ts#L36-L46`.
- **Per-provider schema transform** (`ProviderTransform.schema(model, schema)`) runs before a schema is sent [V]
  `anomalyco/opencode@b65de4d694:packages/opencode/src/session/tools.ts#L92-L101`.
- **Tool-call repair** (AI SDK `experimental_repairToolCall`). If the lowercased name exists, use it. Otherwise
  rewrite the call to the hidden `invalid` tool with `{tool, error}`, which answers "The arguments provided to the tool
  are invalid: …". `invalid` is excluded from `activeTools`, so the model never sees it [V]
  `anomalyco/opencode@b65de4d694:packages/opencode/src/session/llm.ts#L296-L317`, `anomalyco/opencode@b65de4d694:packages/opencode/src/tool/invalid.ts#L1-L21`.
- **Doom-loop guard.** If the last 3 parts are the same tool with identical JSON input, it runs
  `permission.ask({permission:"doom_loop"})` [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/session/processor.ts#L29,#L353-L380`.
  Caveat: it reads only the parts of the *current* assistant message (`MessageV2.parts(ctx.assistantMessage.id)`), and
  v1 creates a new assistant message for every loop step [V]
  `anomalyco/opencode@b65de4d694:packages/opencode/src/session/message-v2.ts#L496-L508`,
  `anomalyco/opencode@b65de4d694:packages/opencode/src/session/prompt.ts#L1186-L1219`. So it catches ≥3 identical
  calls inside one model response, not the same call repeated across consecutive steps [I, from code reading; not
  tested]. Our guard should look across steps.
- **Truncation.** Output above 2,000 lines or 50 KB is cut to a head (or tail) preview, and the full text is saved to a
  file with a hint to inspect it, with 7-day retention [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/tool/truncate.ts#L12-L39`.
- **Todo tool.** `todowrite` stores the list in a DB table, and its description is detailed "when to use / not use"
  guidance [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/tool/todo.ts#L6-L46`, `anomalyco/opencode@b65de4d694:packages/opencode/src/tool/todowrite.txt`.
- **v2 `@opencode-ai/llm`.** Tools have typed `parameters` *and* `success` schemas and a `toModelOutput` projection.
  `ToolFailure` becomes a model-visible error, while unmapped errors fail the stream [V]
  `anomalyco/opencode@b65de4d694:packages/llm/src/tool.ts#L36-L69`, `anomalyco/opencode@b65de4d694:packages/llm/src/tool-runtime.ts#L22-L61`.

### 3.3 Permissions and agents

- **Rules.** `{permission, pattern, action: allow|ask|deny}`, evaluated with **last match wins** and a default of `ask`
  [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/permission/index.ts#L28-L38`. The outcomes:
  - `deny` → `DeniedError` to the tool;
  - `ask` → publish an `Asked` event and await a `Deferred`;
  - the reply is `once | always | reject`;
  - `always` appends allow rules to an in-memory `approved` list held in per-instance state (not persisted, and not
    filtered by session when later asks are evaluated), then auto-resolves pending asks *in the same session* that now
    match;
  - `reject` with a message → `CorrectedError{feedback}`, i.e. the user's correction reaches the model; any reject
    also rejects every other pending ask in that session [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/permission/index.ts#L23-L26,#L67-L167`.
  Tools that are blanket-denied are **removed from the model's tool list** [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/permission/index.ts#L204-L219`.
- **Built-in agents.**
  - `build` (default; `"*": "allow"`, `doom_loop: ask`, `.env` reads ask);
  - `plan` (edits denied except plan files);
  - `general` and `explore` (sub-agents);
  - hidden `compaction`, `title` and `summary` agents with every tool denied [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/agent/agent.ts#L119-L265`.

  Agents carry `model`, `variant`, `temperature`, `topP`, `prompt`, `steps` and `permission`, and are user-definable in
  config or markdown [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/agent/agent.ts#L35-L55,#L267-L294`.
- **Sub-agents** are the `task` tool. It starts a child session with fresh context, returns a single final message
  and a `task_id` that can resume it [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/tool/task.txt`.

### 3.4 Effort = "variants"

- `variants(model)` returns `{variantName → providerOptions}`, and only for reasoning-capable models. Examples:
  - OpenAI: `reasoningEffort ∈ none/minimal/low/medium/high/xhigh`, gated by model and release date;
  - Anthropic: adaptive `thinking` with `effort`, or `budgetTokens` 16000/31999;
  - Gemini: `thinkingBudget` / `thinkingLevel`;
  - some chat-template models: `chat_template_kwargs.thinking_mode`;
  - many models (DeepSeek, Qwen, Kimi on some transports): `{}`, i.e. no variants [V]
    `anomalyco/opencode@b65de4d694:packages/opencode/src/provider/transform.ts#L576-L583,#L790-L1218`.
- Users can define custom variants per model, and a `variant_cycle` keybind (`ctrl+t`) cycles them [V]
  `anomalyco/opencode@b65de4d694:packages/web/src/content/docs/models.mdx#L138-L200`,
  `anomalyco/opencode@b65de4d694:packages/tui/src/config/keybind.ts#L132`.

### 3.5 Context management

- **Overflow.** `usable = limit.input − reserved(min(20k, maxOutput))`, or `context − maxOutput`. Compaction triggers
  when total tokens reach `usable` [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/session/overflow.ts#L8-L34`.
- **Prune** (opt-in `compaction.prune`). Walking backwards, it skips the last 2 turns, protects 40k tokens of recent
  tool output, and marks older outputs as compacted, shown as "[Old tool result content cleared]", when that frees more
  than 20k tokens [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/session/compaction.ts#L28-L33,#L76-L78,#L271-L317`.
- **Summary.** A fixed Markdown template (Objective / Important Details / Work State: Completed-Active-Blocked / Next
  Move / Relevant Files). A "prior-summary + conversation" merge prompt keeps summaries incremental [V]
  `anomalyco/opencode@b65de4d694:packages/core/src/session/compaction.ts#L12-L55`. The tail preserved by default is between 2k and 15k tokens [V]
  `anomalyco/opencode@b65de4d694:packages/opencode/src/session/compaction.ts#L32-L33,#L115-L120`.

### 3.6 Persistence, events, snapshots

- **Storage.** SQLite via Drizzle, with tables `session`, `message`, `part`, `todo`, `session_message`,
  `session_input`, `session_context_epoch` [V] `anomalyco/opencode@b65de4d694:packages/core/src/session/sql.ts#L22-L168`.
- **v2 events.** v2 defines durable typed events such as `session.next.step.started/ended/failed`,
  `…text.delta`, `…reasoning.delta`, `…tool.input.delta`, `…tool.called/progress/success/failed`, `…retried`,
  `…compaction.*` and `…revert.staged/committed` [V] `anomalyco/opencode@b65de4d694:packages/schema/src/session-event.ts#L55-L442`. A projector
  rebuilds state from them [V] (`anomalyco/opencode@b65de4d694:packages/core/src/session/projector.ts`). Clients consume events over SSE `/event`
  from a local HTTP server [V] (`anomalyco/opencode@b65de4d694:packages/opencode/src/server/routes/instance/httpapi/groups/event.ts`).
- **Snapshots.** File-state snapshots use a *shadow git repo* (separate `--git-dir`, same work-tree), with
  `track()`/`restore()` providing undo/revert of agent edits [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/snapshot/index.ts#L39-L41,#L71-L75`.

### 3.7 Providers, MCP, extensibility, testing, telemetry

- **Providers.** v1 uses the Vercel AI SDK (`streamText`) [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/session/llm.ts#L9`. The model catalog comes from
  models.dev (`https://models.opencode.ai`, overridable) [V] `anomalyco/opencode@b65de4d694:packages/core/src/models-dev.ts#L160`. Local models go
  through `@ai-sdk/openai-compatible` with `baseURL: http://localhost:11434/v1`. The docs add: "If tool calls aren't
  working, try increasing `num_ctx` in Ollama. Start around 16k - 32k." [V]
  `anomalyco/opencode@b65de4d694:packages/web/src/content/docs/providers.mdx#L1692-L1730`.
- **Native v2 LLM layer** (opt-in `experimentalNativeLlm`) [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/session/llm.ts#L224-L253`. It separates
  **`Protocol`** (request body schema plus a streaming state machine: `openai-chat`, `openai-responses`,
  `anthropic-messages`, `gemini`, `bedrock-converse`) from **`Route`** (URL, auth, framing), "so DeepSeek, TogetherAI,
  Cerebras… reuse `OpenAIChat.protocol`" [V] `anomalyco/opencode@b65de4d694:packages/llm/src/route/protocol.ts#L4-L43`.
- **Structured output.** `generateObject` forces a synthetic `generate_object` tool call. The code says "provider-native
  JSON modes are intentionally avoided so behaviour is uniform" [V] `anomalyco/opencode@b65de4d694:packages/llm/src/llm.ts#L80-L186`.
- **MCP client** (official TS SDK; stdio, streamable-HTTP and SSE) [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/mcp/index.ts#L6-L10`. **ACP agent**
  via `@agentclientprotocol/sdk` [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/acp/agent.ts#L18`. Instructions come from `AGENTS.md`, `CLAUDE.md`
  (unless disabled) and the deprecated `CONTEXT.md`, and the first project-level match wins [V]
  `anomalyco/opencode@b65de4d694:packages/opencode/src/session/instruction.ts#L61-L67,#L122`. Slash commands are markdown files with frontmatter (`description`,
  `model`) and `$ARGUMENTS` [V] `anomalyco/opencode@b65de4d694:.opencode/command/issues.md#L1-L8`. Skills load on demand through a `skill` tool [V]
  `anomalyco/opencode@b65de4d694:packages/opencode/src/tool/skill.txt`.
- **Testing.** `@opencode-ai/http-recorder` records real HTTP/WebSocket traffic once, then replays deterministic JSON
  cassettes with redaction [V] `anomalyco/opencode@b65de4d694:packages/http-recorder/README.md#L1-L6`. The llm package has recorded golden
  scenario tests [V] (`anomalyco/opencode@b65de4d694:packages/llm/test/recorded-*.ts`).
- **Telemetry.** OpenTelemetry only when `experimental.openTelemetry` is set [V] `anomalyco/opencode@b65de4d694:packages/opencode/src/session/llm.ts#L208-L222`.
  Session sharing is `manual | auto | disabled` [V] `anomalyco/opencode@b65de4d694:packages/core/src/v1/config/config.ts#L57-L60`.

---

## 4. Side-by-side

| Concern | Codex | opencode | Best fit for OFP editor [I] |
| --- | --- | --- | --- |
| Core↔UI | Typed in-process `Op`/`EventMsg` channels; JSON-RPC outside | HTTP server + SSE events + generated SDK | Codex style, in-process Rust channels |
| Loop state | In-memory history + rollout append | Re-read from DB each step | In-memory + append log (simpler, testable) |
| Tool schema | Hand-built subset; separate serde struct | One Effect Schema → JSON Schema + decoder | **Single source**: `schemars` from Rust types (see §6) |
| Bad tool calls | `RespondToModel` text | Repair names → `invalid` tool; "rewrite the input" message; doom-loop ask | opencode's full set |
| Parallel tools | RwLock read/write gate | AI SDK default | Codex gate |
| Approvals | Policy enum + sandbox + exec-policy + guardian | allow/ask/deny rules, once/always/reject+feedback | opencode rules + Codex `Denied{rejection}` semantics |
| Effort | Enum + per-model supported list | Named per-provider option bundles | Harness bundle (params + budgets), per-provider table |
| Providers | Responses only | Everything (AI SDK) / Protocol+Route (native) | Protocol+Route in Rust |
| Compaction | 90% auto; keep 20k user tokens + summary | Structured template; prune old tool output | Both |
| Persistence | JSONL rollout, resume/fork | SQLite; event-sourced v2; git snapshots | JSONL + per-step mission checkpoints |
| Step cap | none found: no `max_turns`/`max_steps`-style identifier in `codex-rs/core/src` (our grep) [V]; turns end on model stop, token/usage limits or interrupt; experimental token `rollout_budget` (§2.6) | `agent.steps` + MAX_STEPS_PROMPT (v1 prompt-only; v2 also strips tools) | opencode v2 (hard) + Codex-style budget reminders |
| Tests | wiremock SSE builders; insta | HTTP cassettes + redaction | Both |

---

## 5. Reuse assessment (Codex crates)

**Rules for reuse.**

- **License [V]:** Apache-2.0 code may be incorporated into a GPLv3 work, but not a GPLv2-only one
  ([FSF license list](https://www.gnu.org/licenses/license-list.html),
  [Apache License, Wikipedia](https://en.wikipedia.org/wiki/Apache_License)). It may also go into an MIT/Apache
  project. Obligations: keep the copyright and NOTICE, and state our changes.
- **Publication [V]:** crates.io has no `codex-core` (HTTP 404). `codex-protocol` on crates.io is a **third-party
  republish** (repository `namastexlabs/codex`, max 0.63.0), not OpenAI's
  ([crates.io API](https://crates.io/api/v1/crates/codex-protocol)).

| Crate | Depend? | Borrow? | Why |
| --- | --- | --- | --- |
| `codex-protocol` | No | **Yes, as a design** | Too heavy (depends on `codex-execpolicy`, `codex-network-proxy`, `codex-http-client`, ICU, landlock/seccomp on Linux [V] `openai/codex@e72da2b538:codex-rs/protocol/Cargo.toml`); coding-specific variants. Copy the SQ/EQ shape and approval/decision enums. |
| `codex-tools` | No | **Yes**: `ToolExecutor` trait shape, `ToolExposure`, `FunctionCallError`, JSON-schema sanitizer ideas | Depends on `codex-code-mode`, `codex-connectors`, `rmcp` [V] `openai/codex@e72da2b538:codex-rs/tools/Cargo.toml` |
| `utils/output-truncation`, `utils/string` truncate | No | **Yes** (small; middle-truncation with token budget) | Tiny, pure functions |
| `codex-api` SSE parser (`sse/responses.rs`) | No | Maybe, for our Responses protocol adapter | Responses-specific; about 1.8k lines |
| `rollout`/`history` | No | Ideas only (typed JSONL line enum, filename scheme, resume/fork) | Coupled to thread-store/state DB |
| `core`, `core-api`, `app-server*` | **No** | Loop structure only | Huge; Responses-only; OpenAI auth; unstable API |
| `ollama`, `lmstudio` | No | Ideas (reachability check, version gate, model pull with progress) | Depend on `codex_core::config::Config` [V] `openai/codex@e72da2b538:codex-rs/ollama/src/lib.rs#L8` |
| `rmcp` (external, official Rust MCP SDK) | **Yes** (if we do MCP) | — | What Codex itself uses; pinned `=3.2.0` [V] |

---

## 6. What we should adopt for the OFP editor agent

The items below are **[I] proposals** derived from the patterns above.

1. **An `ofp-agent-protocol` crate modelled on Codex SQ/EQ.** The GUI thread holds a `Sender<AgentOp>` (bounded) and
   drains a `Receiver<AgentEvent>` every frame with `try_recv`. The agent core runs on a tokio runtime in a background
   thread. Use newtype IDs (`SubmissionId(Uuid v7)`, `ToolCallId`, `ApprovalId`, `SessionId`), as our style rules
   require. Coalesce text deltas UI-side so an unbounded event queue cannot stall rendering.
   ```rust
   pub enum AgentOp {                       // in-process; reply channels allowed (Codex does this)
       UserTurn { text: String, effort: EffortLevel, workflow: Option<WorkflowId> },
       Steer { text: String },              // mid-turn input (Codex pending-input drain)
       Interrupt,
       ApprovalReply { id: ApprovalId, decision: ApprovalDecision }, // Approve|ApproveForSession|Deny{feedback}|Abort
       HostToolResult { call: ToolCallId, result: HostToolResult },  // editor-executed tools
       Compact, Shutdown,
   }
   pub enum AgentEvent {
       TurnStarted{..}, TextDelta{..}, ReasoningDelta{..}, PlanUpdated{..},
       HostToolCall { call: ToolCallId, tool: EditorTool, args: serde_json::Value },
       ApprovalRequested { id: ApprovalId, preview: MissionDiff },
       TokenUsage{..}, Compacted{..}, TurnComplete{..}, TurnAborted{ reason: AbortReason }, Error{..},
   }
   ```
2. **Every mission mutation is a host-executed tool (Codex dynamic tools).** Tools include `mission.query`,
   `mission.place_group`, `mission.add_waypoint`, `mission.add_trigger`, `mission.add_marker`,
   `mission.set_briefing`, `dialogue.draft`, `mission.validate` and so on. The core never touches the document. The
   editor applies each call through the **same command/undo stack a human uses**. Humans and the agent then share one
   code path, and undo works for agent edits automatically.
3. **One schema source.** Derive the JSON Schema with `schemars` from the same Rust arg struct that we
   `serde`-decode with `deny_unknown_fields`. That avoids Codex's hand-built-schema drift and matches opencode's
   single-source approach. Keep a sanitizer, as in Codex `json_schema.rs`, for provider quirks (for example Gemini) and
   external/MCP schemas.
4. **Error-as-feedback kit for SLMs:**
   - a `RespondToModel`/`Fatal` split;
   - "invalid arguments — rewrite the input" messages that include the schema-path error;
   - case/alias tool-name repair;
   - a hidden `invalid` fallback;
   - doom-loop detection (3 identical calls, counted across steps, not only within one response) → ask the user;
   - a hard `max_steps` with a final "summarize, no tools" message (opencode `MAX_STEPS_PROMPT`), enforced by sending no
     tools / `tool_choice: none` on that step as opencode's v2 runner does, not by the prompt alone.
5. **Run concurrently, mutate serially.** Use the Codex `RwLock` gate: read-only query tools share, mutating tools are
   exclusive.
6. **Permissions as rules, not sandboxes.** Use opencode's `allow/ask/deny` × tool × pattern with last match wins and
   `once/always/reject(+feedback)`. Defaults: reads → allow; in-memory mission edits → allow, with one undo checkpoint
   per agent step and a visible diff; **ask** for writing files to disk, exporting PBOs, launching the game preview,
   network fetches and anything that spends cloud budget. Hide blanket-denied tools from the model.
7. **Effort level = harness bundle.** Example (tunable, unverified):

   | Effort | model reasoning param | max steps | self-check pass | context target |
   |---|---|---|---|---|
   | Quick | none/low | 6 | none | small |
   | Standard | medium | 20 | `mission.validate` at end | medium |
   | Thorough | high | 50 | validate plus a reviewer sub-agent | large |

   Map the reasoning parameter through a per-provider table (opencode `variants` shows the real-world mess). Store
   supported levels as model metadata (Codex `supported_reasoning_levels`), and show a one-line description per level
   in the UI. "Workflows" = named agent profiles: system prompt, tool allowlist, effort default and steps, as in
   opencode agents / Codex profiles, plus skill-like markdown playbooks ("Create a convoy ambush", "Write a briefing").
8. **Own a provider layer with Protocol/Route separation** (opencode v2 design). Baseline is **Chat Completions**,
   because it has the widest reach (Ollama, LM Studio, llama.cpp, vLLM, OpenRouter). Add Responses and Anthropic
   Messages adapters. Implement structured output through a **forced tool call** (opencode `generateObject`) rather
   than provider JSON modes, for uniformity across SLMs. Evaluate `rig` (separate doc) before writing our own.
9. **Context policy.**
   - Auto-compact at about 90% of the usable window.
   - Use opencode's structured summary template, adapted to mission work (Objective / Mission state touched / Done /
     Active / Next).
   - Keep recent user messages (Codex's 20k-token rule, scaled to the model).
   - Prune old tool outputs.
   - Truncate large outputs (for example a full `mission.sqm` dump) head+tail and point the model at a paged
     `mission.query` tool instead.
   - Feed mission state as a compact, versioned "world state" block, not the raw SQM (Codex records a
     `WorldState` item [V] `openai/codex@e72da2b538:codex-rs/core/src/session/turn.rs#L505-L507`).
10. **Persistence.** One append-only JSONL log per agent session, with a typed `SessionLine` enum (meta, model item,
    tool call/result, approval, compaction, token usage), stored in app data and keyed by mission path. Support
    resume/fork. Never persist secrets; keep API keys in the OS keyring (Codex has a `keyring-store` crate [V]).
11. **Expose the editor as an MCP server** (via `rmcp`), in addition to the built-in agent. Codex/opencode/Claude
    Code users can then drive the editor from their own harness. That costs us nothing on the agent side, because the
    tool definitions are shared.
12. **Testing.**
    - A deterministic **scripted-model provider** (a queue of canned responses) for unit tests.
    - wiremock SSE builders à la `core_test_support::responses` for protocol adapters.
    - Recorded, redacted cassettes for real providers (opencode `http-recorder` idea).
    - `insta` snapshots of rendered prompts and tool schemas, so prompt changes show up as diffs.
    - All fixtures synthetic (no game data).

---

## 7. What we should avoid

- **Depending on `codex-core` / `codex-core-api`.** It is enormous, OpenAI-account-centric, Responses-only and
  unversioned (0.0.0), and the embedding setup already needs about 15 collaborators and a full `Config` literal [V].
- **Binding to one wire API.** Codex dropped Chat Completions [V]. For us that would lock out Anthropic's native
  Messages API and any OpenAI-compatible server that only has `/v1/chat/completions`. (llama.cpp now documents a
  `/v1/responses` shim that converts to Chat Completions [V], so it is less affected than we first assumed.)
- **A shell/exec tool and the sandbox stack that comes with it.** The editor agent needs none. Every capability should
  be a typed editor tool.
- **Hand-written schemas separated from the decoding types** (drift risk seen in Codex [I]). Also avoid "strict" modes
  we don't actually enforce (Codex leaves `strict: false` with a TODO [V]).
- **opencode's permissive defaults** (`"*": "allow"` for the build agent [V]) for anything irreversible outside the
  in-memory mission.
- **Telemetry on by default.** Codex's metrics exporter defaults to Statsig [V]. Ours should be off and local-only
  unless the user opts in.
- **A giant, ever-patched effort table keyed by model-id substrings** (opencode `transform.ts` [V]). Keep a
  data-driven capability file (as with models.dev / Codex `models.json`) plus a small adapter per protocol.
- **Two runtimes at once.** opencode's v1/v2 coexistence (AI SDK vs native, SQLite vs event-sourced) shows the cost
  [V]. Pick one core design early.
- **Loading the whole mission or long tool outputs into context verbatim.** Page and summarize instead.

---

## Open questions

1. GUI toolkit (egui vs iced vs other). It decides whether the event pump is per-frame polling or a subscription.
   This affects the `AgentEvent` channel bound and delta coalescing.
2. Do we build our provider layer on `rig` (MIT; see the rig study doc) or port opencode's Protocol/Route design? [U]
3. llama.cpp's `llama-server` documents `/v1/responses` (a conversion to Chat Completions) [V], but its minimum release
   and tool-call fidelity are [U]. Ollama's version floor differs: Codex code requires 0.13.4, while Ollama's docs and
   issue say 0.13.3 [V both]. That only matters if we ship a Responses adapter.
4. Structured output on SLMs: forced tool call (opencode) versus grammar-constrained decoding (GBNF/JSON-schema
   sampling in llama.cpp). Which is more reliable is a hypothesis to be measured with our own evaluation
   instruments. [U]
5. Which project license do we choose? Apache-2.0 borrowing works for GPLv3 or MIT/Apache, but not GPLv2-only [V].
6. Should mission diffs shown for approval be semantic (entity-level) or text (SQM)? The approval UX depends on the
   mission data model doc.
7. Will OpenAI publish Codex crates to crates.io under stable versions? [U] If so, revisit `codex-protocol` reuse.
8. Should the editor also speak ACP (opencode implements it as an agent) so ACP-capable IDEs can host it? Low
   priority. [I]

---

## Sources

**Pinned code** (all paths are repo-relative at the pins below; line ranges are cited inline above):

- `openai/codex@e72da2b538`. Key files:
  - protocol: `codex-rs/protocol/src/protocol.rs`, `codex-rs/protocol/src/dynamic_tools.rs`,
    `codex-rs/protocol/src/openai_models.rs`, `codex-rs/protocol/src/openai_models/reasoning_effort.rs`,
    `codex-rs/protocol/src/plan_tool.rs`, `codex-rs/protocol/src/config_types.rs`;
  - session and loop: `codex-rs/core/src/session/{mod,submission,turn}.rs`;
  - tools: `codex-rs/core/src/tools/{parallel,orchestrator}.rs`,
    `codex-rs/core/src/tools/handlers/{plan,plan_spec,dynamic,multi_agents_spec}.rs`,
    `codex-rs/tools/src/{tool_executor,tool_spec,responses_api,function_call_error,json_schema}.rs`,
    `codex-rs/tools/src/json_schema/types.rs`;
  - context and prompts: `codex-rs/core/src/{compact,agents_md}.rs`,
    `codex-rs/prompts/templates/compact/prompt.md`, `codex-rs/utils/output-truncation/src/lib.rs`,
    `codex-rs/utils/string/src/truncate.rs`;
  - persistence: `codex-rs/rollout/src/{lib,rollout_file_name}.rs`, `codex-rs/history/src/lib.rs`;
  - config: `codex-rs/config/src/{config_toml,profile_toml,config_layer_source,types}.rs`;
  - providers: `codex-rs/model-provider-info/src/lib.rs`, `codex-rs/ollama/src/lib.rs`,
    `codex-rs/lmstudio/src/lib.rs`, `codex-rs/codex-api/src/common.rs`;
  - embedding and CLI: `codex-rs/core-api/src/lib.rs`, `codex-rs/thread-manager-sample/src/main.rs`,
    `codex-rs/app-server-client/src/lib.rs`, `codex-rs/app-server-protocol/src/protocol/common.rs`,
    `codex-rs/cli/src/main.rs`;
  - TUI: `codex-rs/tui/src/chatwidget/model_popups.rs`, `codex-rs/tui/src/bottom_pane/status_line_setup.rs`;
  - tests and repo files: `codex-rs/core/tests/common/{responses,test_codex}.rs`, `codex-rs/Cargo.toml`,
    `codex-rs/protocol/Cargo.toml`, `codex-rs/tools/Cargo.toml`, `AGENTS.md`, `LICENSE`, `NOTICE`.
- `anomalyco/opencode@b65de4d694`. Key files:
  - session: `packages/opencode/src/session/{prompt,llm,tools,processor,compaction,overflow,retry,instruction}.ts`;
  - tools: `packages/opencode/src/tool/{tool,todo,invalid,truncate,json-schema}.ts`,
    `packages/opencode/src/tool/{task,skill,todowrite}.txt`;
  - permissions, agents, providers: `packages/opencode/src/permission/index.ts`,
    `packages/opencode/src/agent/agent.ts`, `packages/opencode/src/provider/transform.ts`;
  - other v1 modules: `packages/opencode/src/snapshot/index.ts`, `packages/opencode/src/mcp/index.ts`,
    `packages/opencode/src/acp/agent.ts`;
  - core/v2: `packages/core/src/session/{compaction,sql}.ts`, `packages/core/src/session/runner/max-steps.ts`,
    `packages/core/src/models-dev.ts`, `packages/core/src/v1/config/config.ts`,
    `packages/schema/src/session-event.ts`;
  - native LLM layer: `packages/llm/src/{llm,tool,tool-runtime}.ts`, `packages/llm/src/route/protocol.ts`;
  - docs, tests, repo files: `packages/http-recorder/README.md`,
    `packages/web/src/content/docs/{providers,models}.mdx`, `packages/desktop/package.json`,
    `.opencode/command/issues.md`, `.github/workflows/docs-update.yml`, `LICENSE`.

**Web:**

- opencode org move: https://news.ycombinator.com/item?id=46552218 ; https://github.com/anomalyco/opencode/issues/16440
- Ollama `/v1/responses` version: https://github.com/ollama/ollama/issues/13595 ; https://docs.ollama.com/api/openai-compatibility
- LM Studio `/v1/responses` (0.3.29): https://lmstudio.ai/blog/lmstudio-v0.3.29 ; https://lmstudio.ai/docs/developer/openai-compat/responses
- crates.io status: https://crates.io/api/v1/crates/codex-protocol (third-party republish) ; https://crates.io/api/v1/crates/codex-core (404 at time of check)
- License compatibility: https://www.gnu.org/licenses/license-list.html ; https://en.wikipedia.org/wiki/Apache_License ; https://www.apache.org/licenses/GPL-compatibility.html
- llama.cpp `/v1/responses`: https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md (master, fetched 2026-09-26)
- opencode repo redirect: https://github.com/sst/opencode (redirects to anomalyco/opencode)

---

## Verification notes

Adversarial fact-check, 2026-09-26, against the pinned clones and the web sources above.

**Confirmed in code or at source:**

- Codex license and packaging:
  - `LICENSE` is Apache-2.0, and `NOTICE` credits Ratatui (MIT).
  - The workspace sets `license = "Apache-2.0"` and `version = "0.0.0"`, and all 158 crate `Cargo.toml` files under
    `codex-rs/` (every one except the workspace root) use `license.workspace = true`.
  - The workspace has 153 members.
  - crates.io has no `codex-core` (HTTP 404). `codex-protocol` 0.63.0 was published 2025-12-11 by a third party
    from `namastexlabs/codex`. A crates.io search for "codex" shows no crate whose repository is `openai/codex`.
- Codex wire API and local providers:
  - `WireApi { Responses }` only. `"chat"` returns the "no longer supported" error, and `ollama-chat` is rejected in
    config (`config_toml.rs#L955`).
  - Built-in providers are openai, amazon-bedrock, amazon-bedrock-runtime, ollama (11434) and lmstudio (1234).
  - The Ollama minimum is 0.13.4 (0.0.0 dev builds are also accepted).
  - The `--oss` defaults are `gpt-oss:20b` and `openai/gpt-oss-20b`.
  - Ollama docs say `/v1/responses` was "Added in Ollama v0.13.3" and is non-stateful. The LM Studio 0.3.29 post is
    dated 2025-10-06.
- Codex protocol and tools:
  - `Op` is `#[derive(Debug)]` only and carries `oneshot::Sender`s. `Event`/`EventMsg` derive serde. `EventMsg` has 83
    variants.
  - Channel capacity is 512 (bounded) plus an unbounded event channel. Submission ids are UUIDv7.
  - Dynamic tools use a oneshot waiter, `ItemStarted`/`ItemCompleted` and the cancel message. The host's
    `Op::DynamicToolResponse` is routed in `core/src/session/handlers.rs#L589`. The app-server exposes it as
    `item/tool/call`.
  - Production tool specs use `strict: false` (`strict: true` appears only in tests). The parallel `RwLock` gate and
    the `RespondToModel`/`Fatal` split are as described.
- Codex config, context and persistence:
  - The reasoning-effort enum and its alias resolution. The auto-compact min(config, 90%) rule and the default 95%
    usable window. `COMPACT_USER_MESSAGE_MAX_TOKENS = 20_000`. Tokens estimated as bytes/4.
  - Rollout filenames and `RolloutLine`/`InitialHistory`. Config layer precedences.
  - `metrics_exporter` resolves to Statsig when unset. `rmcp = "=3.2.0"`. There is no `mcp-server` crate or
    subcommand.
  - Line counts, the 1,436-line `models.json` and 1,329 `.snap` files match.
- opencode:
  - MIT license, Effect 4.0.0-beta.83, v1.18.32, electron 42.3.3, and the `sst/opencode` CI guard.
  - `sst/opencode` redirects to `anomalyco/opencode`.
  - AI SDK `streamText` is the default path. `experimentalNativeLlm` defaults to false (see the runtime-flags test).
    The five protocols are as listed.
  - Tool-call repair (lowercase name, then the hidden `invalid` tool, excluded from `activeTools`) and the
    "Please rewrite the input…" text.
  - `DOOM_LOOP_THRESHOLD = 3`. Permission `findLast`, with `ask` as the default. The shared defaults start with
    `"*": "allow"`.
  - Retry constants, truncation limits (2,000 lines / 50 KB / 7 days), prune constants (20k/40k), the summary
    template and `generate_object`.
- Apache-2.0 can go into GPLv3 but not into GPLv2 work (ASF GPL-compatibility page; the FSF page was unreachable at
  check time).

**Corrected:**

1. §2.6 and §4: Codex does have an experimental harness-level *token* budget (`rollout_budget`, with reminders and
   `SessionBudgetExceeded`). It has no step cap.
2. §3.1 and §6.4: opencode v1's MAX_STEPS is prompt-only, with tools still sent. v2 removes the tools and sets
   `toolChoice: "none"`. Our recommendation now says to enforce the cap, not just prompt for it.
3. §3.2 and TL;DR: the doom-loop check only sees the current assistant message, which is one step in v1.
4. §3.3: `always` rules are instance-wide in memory, not session-scoped. A reject cascades to the other pending asks.
5. TL;DR, §2.10, §7 and Open question 3:
   - Codex local models are not limited to Ollama and LM Studio. Any `/v1/responses` server can be added as a custom
     provider.
   - llama.cpp now documents `/v1/responses`, so it is no longer [U].
6. §2.13: the Statsig default only takes effect when analytics are enabled, and never in debug builds.
7. Citation and detail fixes:
   - the compact prompt is 9 lines, not 7;
   - the CLI enum spans `#L142-L240`;
   - `variants()` spans `#L790-L1218`;
   - the hooks enum is at `#L1579-L1601`;
   - `ToolExposure` has 6 variants;
   - the sub-agent tool list is longer than first stated;
   - the HN "comprises" quote is a user comment, not an official statement;
   - the line-count basis (non-blank lines) is now stated.

**Not independently verified:** the Wikipedia and FSF license pages (FSF connection refused). Whether opencode's AI SDK
default of one step per `streamText` holds for every provider path. The release that added llama.cpp `/v1/responses`.
