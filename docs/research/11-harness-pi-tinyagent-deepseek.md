# Harness Study: pi, tinyagent, DeepSeek Harness

Research note for the `ofp-editor` project, a standalone Rust rewrite of the Arma: Cold War Assault (OFP) mission editor with a built-in AI "harness agent". It covers three open-source agent harnesses and says which of their ideas fit an agent that edits a **typed mission document** inside a desktop GUI. Such an agent never needs a filesystem or a shell.

Pinned code studied (all citations below point at these commits):

| Short name | Repository @ commit | Commit date | Language |
|---|---|---|---|
| **pi** | `earendil-works/pi@2b0a123de9` | 2026-09-26 | TypeScript (Node/Bun) |
| **tinyagent** | `askbudi/tinyagent@1b85dc351f` | 2025-09-29 | Python |
| **dsh** | `deepseek-ai/deepseek-harness@477b4f4205` | 2026-09-24 | TypeScript (Node), Electron desktop |

Epistemic markers: **[V]** means verified in pinned code, docs or a cited web page. **[I]** means inferred by me from the evidence. **[U]** means unknown or not verified.

---

## TL;DR

- **All three harnesses are MIT-licensed at the pinned commits [V].** Any of them can be studied and ported, whatever license ofp-editor ends up with (MIT code can be incorporated into a GPL-3.0 or MIT/Apache project if its MIT notice is kept). None of them is Rust, so we **port ideas, not code** [I].
- **pi is the design to copy for the core loop.** It has a small loop with clear hooks (`beforeToolCall`, `afterToolCall`, `prepareRequest`, `finishTurn`, steering and follow-up queues) and one typed event stream that every UI consumes. Its default prompt is about 640 tokens by my reconstruction [I]; the author says prompt plus tool definitions come in under 1,000 tokens [V]. It has 4 default tools out of 8 built in [V]. A small surface like this is what small language models (SLMs) need [I].
- **pi-ai is the best reference for provider normalization.** It uses one `ThinkingLevel` ladder (`off…max`), a per-model `thinkingLevelMap`, and per-endpoint `compat` flags. Those flags cover Ollama, vLLM, llama.cpp, Qwen/DeepSeek-style thinking switches and strict/grammar-constrained tool schemas [V]. dsh's multi-provider adapter (`dsh-llm-pi-ai`) is built on pi-ai; its direct DeepSeek route uses a separate adapter (`dsh-llm-deepseek`) [V].
- **pi-ai already supports "decision models" as a separate model type.** `classify()` over TypeSafe's **Jev** ("System One" API): structured state in, typed choice/score/bool answers with confidences out [V]. This is a clean slot for the public decision models (Jev, Kev, Laya, CLM) compared in [16-decision-models.md](16-decision-models.md) [I].
- **dsh contributes the safety and typed-tool ideas.** Every tool declares a *validated output schema*. Every call goes through a guarded pipeline (`pre-execute` → approval, only when pre-execute says `ask` → monotonic guards → `execute` → `post-execute`). Approval is a closed, fail-closed outcome (`allowed-once | rejected | cancelled | unavailable`). Named permission presets bundle the two enforcement knobs (sandbox mode and approval policy) into one selector [V]. The last idea maps directly onto a user-facing "effort level" [I].
- **dsh's "PTC" (programmatic tool calling, which it also calls Code Mode) is worth copying later.** The model writes one small program against a generated, typed SDK, and every sub-call re-enters the guarded pipeline [V]. For an editor, this is how "place 40 units in a wedge along this road" becomes one reviewable script [I].
- **tinyagent is mostly a cautionary example.** Tool arguments are not validated. Malformed JSON silently becomes `{}`. `modified_args` is documented but never applied. Compaction is destructive. A 45 KB `memory_manager.py` is never imported [V]. Its last commit was 2025-09-29 [V]. Worth keeping: `final_answer`/`ask_question` exit tools, and sub-agents packaged as tools [V].
- **Recommendation: build a native Rust agent crate** that combines:
  - pi's loop and event model;
  - pi-ai's thinking-level and compat normalization;
  - dsh's typed input/output tools, guarded pipeline, approval and presets;
  - edits that go through **transactional change-sets on the mission document** (preview, then accept, then undo), not files.
- **Keep the default tool set tiny and mission-specific** (roughly 8–12 tools such as `query_mission`, `apply_changes`, `validate_mission` and `write_text`), with skills-style progressive disclosure. Add **no shell or filesystem tools** [I].
- **Test like dsh and pi do.** Use a scripted fake provider (pi's `fauxProvider`), recorded-session replay snapshots (dsh), and "verify the world, not the self-report": assert the resulting mission, not what the model says it did [V for the practices, I for fit].

---

## 1. Terms used in this note

- **Harness**: the software around a model. It covers the prompt, tools, loop, context management, persistence, UI protocol and safety.
- **Turn / step**: in pi, a *turn* is one model response plus the tools it called [V]. In dsh, a *step* is one model request plus its tools, and a *turn* is zero or more steps until nothing is owed [V].
- **Tool call validation**: checking model-produced JSON arguments against the tool's schema before running it.
- **Thinking level / reasoning effort**: a provider knob that controls hidden reasoning tokens. Providers spell it differently (`reasoning_effort`, `thinking.budget_tokens`, `enable_thinking`, and so on).
- **Compaction**: replacing old conversation history with a model-written summary when the context window fills up.
- **Session tree**: storing the conversation as entries with `id`/`parentId`, so a user can branch from any point.
- **Constrained sampling**: the provider or inference server restricts decoding so the output always matches a JSON Schema or grammar. This matters most for small models.
- **PTC / Code Mode**: the model gets one `run_code` tool and calls the other tools from inside a small program.
- **SLM**: small language model, run locally (for example through Ollama or llama.cpp).
- **Classifier / "System One" model**: a non-generative model that answers typed questions about structured state, with probabilities.

---

## 2. Side-by-side snapshot

| Dimension | pi | tinyagent | dsh |
|---|---|---|---|
| License | MIT, © 2025 Mario Zechner [V] | MIT, © 2025 askbudi [V] | MIT, © 2026 DeepSeek; vendored Cordis MIT, © Shigma [V] |
| Status | Very active; moved to Earendil Works in 2026 [V] | Last commit 2025-09-29, v0.1.20 [V] | "Developer preview… compatibility-breaking changes" [V] |
| Scale (test files) | 627 `*.test.ts` [V, `git ls-files`, recounted] | 22 `test_*.py` [V, counted] | 1,861 `*.spec.ts`/`*.e2e.ts` (1,596 + 265), plus 261 `*.spec.tsx` [V, `git ls-files`, recounted] |
| Default system prompt | about 2.6 K chars, ≈640 tokens by reconstruction [I]; author claims < 1 K tokens including tools [V] | 3 sentences (generic agent); code agent uses a YAML prompt [V] | SDK text-turn: 2,475 bytes; session text-turn: 2,794 bytes; PTC session: 26,164 bytes, because the prompt embeds the tool SDK (non-PTC modes send tool schemas separately) [V] |
| Built-in tools | 8 implemented, 4 on by default (read, bash, edit, write) [V] | 3 control tools, plus TodoWrite; code agent adds run_python, bash and 5 file tools [V] | About 30 tool packages, about 65 model-visible names (my count; many opt-in) [I] |
| Tool schema | TypeBox; compiled validator; lenient coercion [V] | Generated from Python type hints; not validated at call time [V] | Own JSON-value DSL; hard-fail input validation (parameter root is an open object, so extra keys pass) **and** a mandatory validated output schema [V] |
| Provider layer | pi-ai: about 40 providers, `ThinkingLevel` ladder, compat flags, classifiers [V] | LiteLLM passthrough [V] | Adapter seam; reasoning effort is adapter-owned (opaque IDs); pi-ai-backed adapter [V] |
| Session model | JSONL tree (`id`/`parentId`), branch, fork, clone [V] | Flat message list plus storage backends [V] | Append-only event log, versioned formats with migrations, fork at turn boundary [V] |
| Compaction | Structured summary, non-destructive (entries kept) [V] | Replaces history with [system, summary] [V] | Pluggable seam; log-recorded lock; tool-result pruner and image-offload backends [V] |
| Extension model | In-process TS extensions with an event bus, plus skills, prompt templates and packages [V] | Callbacks/hooks list [V] | Everything is a Cordis plugin, with reversible effects and typed events [V] |
| UI modes | TUI, print, JSON events, RPC (JSONL stdio), in-process SDK [V] | Callback UIs (Rich, Gradio, Jupyter) [V] | Web, Electron desktop, SDK (JSON-RPC over NDJSON), ACP, headless [V] |
| Safety | None built in ("YOLO"); containerize; example gates [V] | AST checks plus OS sandboxes (Seatbelt, bubblewrap, Docker, Modal) [V] | Sandbox modes plus approval policy plus presets; fail-closed; SAFETY.md disclaimers [V] |

---

## 3. pi (`earendil-works/pi`)

### 3.1 Purpose and philosophy (measured)

pi describes itself as a "minimal, extensible AI agent for the terminal" [V: `earendil-works/pi@2b0a123de9:packages/coding-agent/README.md#L13-L17`]. The monorepo is layered as follows [V: `earendil-works/pi@2b0a123de9:README.md#L26-L36`]:
- `pi-ai`: the provider API;
- `pi-agent-core`: the loop and state;
- `pi-coding-agent`: the CLI;
- `pi-tui`, `chord`, `pi-durable`, `pi-protocol`, `pi-server`, `pi-client`, `evals`.

Minimalism measurements:

- **Built-in tools.** There are 8 tool implementations: `read`, `bash`, `powershell`, `edit`, `write`, `grep`, `find`, `ls` [V: `earendil-works/pi@2b0a123de9:packages/coding-agent/src/core/tools/index.ts#L95-L105`]. The default selection is `["read","bash","edit","write"]`, overridable by the `defaultTools` setting [V: `earendil-works/pi@2b0a123de9:packages/coding-agent/src/core/sdk.ts#L258-L265`; `…/src/core/system-prompt.ts#L58`].
- **System prompt.** The default prompt is assembled from:
  - a one-sentence preamble;
  - one-line tool snippets;
  - about 10 deduplicated rules;
  - a docs-pointer section;
  - the cwd.

  [V: `earendil-works/pi@2b0a123de9:packages/coding-agent/src/core/system-prompt.ts#L121-L180`; snippets and guidelines, for example `…/src/core/tools/edit.ts#L43-L51`]. I reconstructed the default text (no context files, no skills) and measured **2,567 characters / 356 words**, about 640 tokens at 4 chars/token [I]. The count depends on the install path (printed three times in the docs section) and the cwd; it was re-derived with `/usr/lib/node_modules/@earendil-works/pi-coding-agent` and `/home/user/project`. Tool JSON schemas are extra. The author's post says "pi's system prompt and tool definitions together come in below 1000 tokens" [V: https://mariozechner.at/posts/2025-11-30-pi-coding-agent/].
- **Deliberate omissions** (per the author) [V: same post]:
  - "does not and will not support MCP";
  - no built-in sub-agent tool;
  - no built-in plan mode;
  - "full YOLO mode" with no permission prompts.

  The repo README confirms there is no permission system [V: `earendil-works/pi@2b0a123de9:README.md#L40-L48`].
- **Minimal is not small.** The *agent surface* is minimal, but the repo is large. The durable harness spec alone (`packages/agent/docs/harness.md`) is about 210 KB [V, file size]. Minimalism here means "little in the context window", not "little code" [I].

### 3.2 Agent loop (`pi-agent-core`)

The core is `runLoop()` [V: `earendil-works/pi@2b0a123de9:packages/agent/src/agent-loop.ts#L162-L320`]:

- **Outer loop.** It keeps going while queued *follow-up* messages exist.
- **Inner loop.** It runs while there are tool calls or *steering* messages. Steering is user input injected mid-run, delivered after the current tool batch finishes.
- **Per turn:**
  1. optional `prepareNextTurn` (compaction runs here);
  2. declare tool-set changes to the model as a system-message delta (`declareToolChanges`, L332-L362);
  3. `prepareRequest` hook;
  4. stream the assistant response;
  5. execute tool calls;
  6. `finishTurn` hook, which can return `{action:"end"|"continue"}`;
  7. emit `turn_end`.
- **Truncated-output guard.** If `stopReason === "length"`, every tool call in that message is failed without executing, and the model is told to re-issue complete arguments [V: `…/agent-loop.ts#L263-L269`, `#L475-L500`]. This is a small but important detail for SLMs with short output limits [I].
- **Parallel vs sequential tools.** Tools run in parallel by default. Any tool marked `executionMode:"sequential"` forces the whole batch to run sequentially. Results are always appended in assistant source order [V: `…/agent-loop.ts#L505-L520`, `#L583-L657`; `packages/agent/README.md#L117-L130`].
- **Hooks.** `beforeToolCall` runs after argument validation and can `block` with a reason. `afterToolCall` can rewrite content, details or `isError`. Any tool result can carry `terminate: true`; the loop stops early only if **every** result in the batch agrees [V: `…/agent-loop.ts#L703-L771`, `#L816-L861`; `packages/agent/README.md#L126-L128`].
- **Events.** One typed event stream: `agent_start`, `turn_start`, `message_start/update/end`, `tool_execution_start/update/end`, `turn_end`, `agent_end` [V: `earendil-works/pi@2b0a123de9:packages/agent/README.md#L69-L115`, `#L193-L208`]. Every UI mode is a consumer of this stream.
- **Custom messages.** `AgentMessage` can be extended with app-specific roles. `convertToLlm` filters them before each call, and `transformContext` prunes or injects context [V: `…/packages/agent/README.md#L51-L67`, `#L432-L457`].

### 3.3 Tool schema and validation

- **Definition.** Tools are defined with TypeBox (a JSON-Schema builder with TS type inference) [V: `…/packages/agent/README.md#L459-L494`].
- **Validation.** `validateToolArguments()` works in five steps [V: `earendil-works/pi@2b0a123de9:packages/ai/src/utils/validation.ts#L317-L350`]:
  1. clones the args;
  2. drops `null` for optional fields;
  3. runs TypeBox `Value.Convert` (which already converts strings such as `"5"` to numbers);
  4. for plain JSON-Schema (non-TypeBox) tools only, applies its own lenient primitive coercion (`"5"`→5, `"true"`→true, `null`→`""`/0/false) [V: `#L59-L131`, gated at `#L323`];
  5. validates with a cached compiled validator and returns a path-annotated error listing the received arguments.

  The error goes back to the model as a tool error, so the model can self-correct [V: `…/agent-loop.ts#L764-L770`].
- **Constrained sampling.** A tool may opt in with `constrainedSampling: {type:"json_schema", strict:"prefer"|"require"}` or with grammar variants (`openai_lark`, `openai_regex`) [V: `…/packages/ai/src/types.ts#L670-L685`]. `makeStrictJsonSchema()` rewrites a schema into the strict subset providers accept, or explains why it cannot. With `strict:"require"`, an unsupported schema fails loudly instead of silently degrading [V: `…/packages/ai/src/api/constrained-sampling.ts#L116-L131`, `#L208-L228`].

### 3.4 Provider abstraction (`pi-ai`)

- **Models and providers.** A `Models` collection holds `Provider`s. `createProvider({id, auth, models, api|images|classifiers})` builds a custom provider; the README shows keyless Ollama and llama.cpp examples [V: `earendil-works/pi@2b0a123de9:packages/ai/README.md#L1175-L1212`, `#L1263-L1277`]. Wire APIs are a small closed set: `openai-completions`, `openai-responses`, `anthropic-messages`, `google-generative-ai`, `bedrock-converse-stream`, `mistral-conversations`, and a few more. About 40 named providers map onto those APIs [V: `…/packages/ai/src/types.ts#L17-L82`].
- **Thinking normalization.** There is one public ladder: `ThinkingLevel = "minimal"|"low"|"medium"|"high"|"xhigh"|"max"`, plus `"off"` [V: `…/types.ts#L85-L87`].
  - Each model declares `reasoning: boolean` and an optional `thinkingLevelMap`. The map sends a level to a provider string, or to `null` for "unsupported" [V: `…/types.ts#L1076-L1107`].
  - `getSupportedThinkingLevels` and `clampThinkingLevel` resolve an unsupported level by searching **upward** to the next supported level first and only then downward; `xhigh` and `max` count as supported only when the map has an explicit non-null entry [V: `…/packages/ai/src/models.ts#L1209-L1241`].
  - Token-budget providers get default budgets of minimal 1024, low 2048, medium 8192 and high 16384; `xhigh`/`max` clamp to `high` for budgets [V: `…/packages/ai/src/api/simple-options.ts#L54-L69`].
- **Local and odd endpoints.** `OpenAICompletionsCompat` flags describe how each server differs [V: `…/types.ts#L754-L831`]:
  - `supportsDeveloperRole`, `supportsReasoningEffort`, `maxTokensField`, `requiresToolResultName`;
  - `thinkingFormat` ∈ {openai, openrouter, deepseek, together, baseten, zai, qwen, chat-template, qwen-chat-template, string-thinking, ant-ling};
  - `thinkingTokenBudgetField` (vLLM/SGLang/llama.cpp names), `supportsStrictMode`, `supportsOpenAIGrammarTools`, `supportsMidConvoSystemMessages`, and so on.

  The mapping code is one `if/else` ladder [V: `…/packages/ai/src/api/openai-completions.ts#L875-L972`]. The README tells users to set `supportsDeveloperRole:false` (and `supportsReasoningEffort:false` if `reasoning_effort` is also unsupported) for servers that do not understand the `developer` role, adding that "this commonly applies to Ollama, vLLM, SGLang" [V: `…/packages/ai/README.md#L1287-L1313`]. The coding agent also ships a llama.cpp *router* integration that loads, unloads and downloads GGUF models [V: `…/packages/coding-agent/docs/llama-cpp.md#L1-L20`, `#L68-L87`].
- **Cross-provider handoff.** When a conversation switches provider, foreign thinking blocks become `<thinking>`-tagged text, and tool calls and results are preserved [V: `…/packages/ai/README.md#L1483-L1523`].
- **System messages as a transcript.** The prompt and tool set live in system messages that carry named `sections` and `toolsAdded`/`toolsRemoved` deltas. Models that cannot take mid-conversation system messages get them collapsed into one leading system message [V: `…/packages/ai/README.md#L1525-L1556`].
- **Classifier ("decision") models.** `type:"classifier"` models are called with `classify(model, {state, questions})`. Question types are `choice` (with criteria), `score` (ordered criteria) and `bool`. Answers carry `probabilities`, `confidence` or `probability` [V: `…/packages/ai/src/types.ts#L600-L654`]. The built-in implementation is TypeSafe System One, where `bool` maps to the wire type `noul` [V: `…/packages/ai/src/providers/typesafe.ts#L6-L18`; `…/src/api/system-one-shared.ts#L104-L132` (mapping), `#L149-L207` (call)]. The documented models are `jev-latest` (TypeSafe), `typesafe/jev-1.13` and `~typesafe/jev-latest` (OpenRouter), and `typesafe/jev` (Cloudflare Workers AI) [V: `…/packages/ai/README.md#L891-L933`]. The vendor post is dated 2026-09-15 and says Jev is "available today in early access", describing it as "unstructured state in, typed probabilistic decisions out" [V for date and wording: https://typesafe.ai/blog/introducing-system-one-models-and-jev; DataCamp also gives 2026-09-15: https://www.datacamp.com/blog/system-one-models-jev]. Capability and quality claims are vendor claims, not independently verified [U].
- **Test double.** `fauxProvider()` scripts assistant messages (text, thinking, tool calls), streams them, simulates token usage and caching, and returns an error once its queue is empty [V: `…/packages/ai/README.md#L1396-L1481`].

### 3.5 Context management and compaction

- **Trigger.** Compaction runs when `contextTokens > contextWindow − reserveTokens` (default reserve 16,384). It happens between turns inside `prepareNextTurn`, and also as a one-shot recovery after overflow or a `length` stop [V: `earendil-works/pi@2b0a123de9:packages/coding-agent/docs/compaction.md#L29-L41`].
- **Cut point.** Pi walks back until `keepRecentTokens` (default 20k) is reached. It never cuts between a tool call and its result. The summary is appended as a `CompactionEntry` with `firstKeptEntryId`, and **the original entries stay in the file** [V: `…/compaction.md#L43-L81`, `#L128-L137`].
- **Summary format.** The prompt is a fixed template: Goal / Constraints & Preferences / Progress (Done, In Progress, Blocked) / Key Decisions / Next Steps / Critical Context. Updates are iterative and include the previous summary [V: `…/packages/coding-agent/src/core/compaction/compaction.ts#L529-L601`].

### 3.6 Sessions, branching and durability

- **Session files.** Sessions are JSONL trees (`id`, `parentId`), and continuing from an earlier entry creates a branch in the same file. System messages persist the prompt and tool deltas, so a replay reconstructs exactly what the model saw [V: `…/packages/coding-agent/docs/session-format.md#L1-L3`, `#L49-L85`]. Moving between branches can generate a *branch summary* of the abandoned path [V: `…/compaction.md#L169-L198`].
- **Durable harness.** The newer `AgentHarness` spec models a session as four parts [V: `earendil-works/pi@2b0a123de9:packages/agent/docs/harness.md#L25-L33`]:
  - an immutable entry tree;
  - bound mutable values;
  - branches and lanes;
  - a usage ledger.

  Every provider request and tool call is wrapped as *intent → uncertain effect → settlement*. After a crash, a tool marked `replay:"never"` is **not** re-run (a synthetic "interrupted" result is written instead), while `replay:"safe"` tools are re-executed [V: `…/harness.md#L91-L114`].
- **Typed documents in `pi-durable`.** The design specifies typed, versioned JSON **documents** scoped to a session, a conversation or a task. Conversation documents can be `history:"rewindable"` with `fork:"asOf"|"current"|"initial"`, and they carry `migrate()` and `checkpointWhen()` [V: `earendil-works/pi@2b0a123de9:packages/durable/docs/pico-v5.md#L609-L650`]. Code and tests for documents and `asOf` forks exist (`packages/durable/src/documents.ts`, `src/session/forks.ts`, `test/session-documents.test.ts`, `test/session-forks.test.ts`) [V, files present], but the package README describes its current public API as durable record contracts plus memory/JSONL/SQLite storage [V: `…/packages/durable/README.md#L3-L5`], so completeness and stability are **[U]**. This is the closest existing design to "a conversation that owns a mission document that forks with it" [I].

### 3.7 Extension model

- **Extensions.** An extension is a TypeScript default-export factory that receives `ExtensionAPI` [V: `…/packages/coding-agent/docs/extensions.md#L71-L84`]. It can call `pi.on(event)`, `registerTool`, `registerCommand`, `registerShortcut`/`registerFlag`, `sendMessage`, `appendEntry` (non-context state), `setActiveTools`, `registerProvider`, and use the event bus.
  - Handlers run in load order.
  - `tool_call` handlers can mutate or block a call.
  - `tool_result` handlers compose.
  - `before_agent_start` can edit prompt sections [V: `…/extensions.md#L93-L115`].
  - The state-placement guide says which storage to use for each case [V: `…/extensions.md#L169-L182`]:
    - tool-result `details` for branch-following state;
    - `appendEntry` for durable non-context data;
    - `sendMessage` for model-visible custom content.
- **Skills** follow the Agent Skills spec. Only name, description and path go in the prompt; the full `SKILL.md` is read on demand [V: `…/docs/skills.md#L41-L45`].
- **Chord** is a standalone composition runtime [V: `earendil-works/pi@2b0a123de9:packages/chord/README.md#L17-L45`]. It provides plugin *facets* per environment, typed services, and **replicated state**: producers publish atomic `change(ctx, draft => …)` transactions, and consumers receive immutable values plus exact JSON op batches. The pico3 harness publishes the conversation view as Chord replicated state [V: `…/packages/agent/src/harness/pico3/chord.ts#L28-L43`].

### 3.8 UI decoupling (how a GUI embeds it)

- **Modes.** One agent and session core drives interactive TUI, print, JSON event stream, RPC and the in-process TS SDK [V: `…/packages/coding-agent/docs/how-pi-works.md#L33-L39`].
- **RPC mode.** It is JSONL over stdio with commands, `response` records (correlated by `id`), streamed session events, and an **extension-UI sub-protocol** [V: `…/docs/rpc.md#L3-L33`; `…/docs/rpc-extension-ui.md#L5-L10`]. That sub-protocol has blocking dialogs (`select`, `confirm`, `input`, `editor`, each with an optional timeout) and fire-and-forget calls (`notify`, `setStatus`, `setWidget`). It is exactly the shape a GUI host needs for approvals [I].
- **Experimental protocol and server.** `pi-protocol` uses CBOR-framed routed envelopes, and `pi-server` supports multiple presentation attachments per session [V: `…/packages/protocol/README.md`, `…/packages/server/README.md`].

### 3.9 Sub-agents and workflows

These are examples, not core:
- **Subagent extension.** It spawns separate `pi` processes with isolated context, in single, parallel (max 8, 4 concurrent) or chain (`{previous}` placeholder) mode. Agents are Markdown files with frontmatter (`tools`, `model`), and workflow presets are prompt templates such as `/implement` = scout → planner → worker [V: `…/examples/extensions/subagent/README.md#L91-L97`, `#L125-L163`].
- **Plan-mode extension.** It disables `edit`/`write` and allowlists bash commands [V: `…/examples/extensions/plan-mode/README.md#L1-L12`].
- **Structured-output tool.** A tool that returns `terminate:true` ends the run on a typed result without an extra model turn [V: `…/examples/extensions/structured-output.ts#L18-L44`].

### 3.10 Safety

There is no built-in permission system. The guidance is to containerize (Gondolin micro-VM, Docker, OpenShell) [V: `…/README.md#L40-L48`]. Project trust only controls which project resources load; it does not sandbox tool calls [V: `…/docs/how-pi-works.md#L47-L49`]. Permission gates are left to extensions, for example regex-matching dangerous bash commands and asking `ctx.ui.select`, or blocking by default without a UI [V: `…/examples/extensions/permission-gate.ts#L10-L34`].

### 3.11 Evals and tests

- 627 vitest `*.test.ts` files [V, recounted with `git ls-files`].
- `packages/evals` runs behavioural evals with `vitest-evals`, including **documentation-lift** evals. Each case runs in isolated `without_docs` and `with_docs` containers, and the report computes the lift [V: `…/packages/evals/README.md#L1-L17`, `#L54-L80`].

---

## 4. tinyagent (`askbudi/tinyagent`)

### 4.1 Purpose and philosophy

- **Positioning.** "Build your own AI coding assistant with any model" is the pitch. It was inspired by Hugging Face "Tiny Agents" and "12-factor-agents" [V: `askbudi/tinyagent@1b85dc351f:README.md#L13-L16`, `#L31-L48`].
- **Dependencies.** The package is `tinyagent-py` v0.1.20 and depends on `mcp`, `litellm`, `openai` and `tiktoken` [V: `askbudi/tinyagent@1b85dc351f:pyproject.toml#L13-L29`].
- **Activity.** The newest commit on `main` is from 2025-09-29, which is the pinned commit, so there have been about 12 months with no commits as of 2026-09-26 [V: https://github.com/askbudi/tinyagent/commits/main].

### 4.2 Agent loop

`_run_agent_loop()` [V: `askbudi/tinyagent@1b85dc351f:tinyagent/tiny_agent.py#L1295-L1608`]:
1. Deep-copy messages and let `llm_start` hooks rewrite the copy.
2. Call LiteLLM with `tool_choice="auto"`.
3. Append the assistant message.
4. Run all tool calls concurrently with `asyncio.gather`, each under a timeout (default 120 s, per the constructor) [V: `#L380-L407`, `#L1543-L1548`].
5. Stop in any of these cases:
   - the model answers with no tool call;
   - the model calls `final_answer` or `ask_question` [V: `#L1577-L1596`];
   - `max_turns` is reached (default 10) [V: `#L1598-L1602`].

`notify_user` is a non-exit progress tool [V: `#L577-L625`].

### 4.3 Tool schema and validation (weak)

- **Schema generation.** The `@tool` decorator builds a JSON Schema from Python type hints and docstrings [V: `#L64-L117`, `#L119-L349`]. Unknown or complex types fall back to `"string"` [V: `#L322-L332`].
- **Weaknesses:**
  - Arguments are **not** validated against the schema. The handler is called as `handler(**tool_args)` [V: `#L1138-L1204`].
  - Unparseable JSON arguments become `{}` [V: `#L1427-L1432`].
  - The built-in `final_answer` schema puts `"required"` outside `parameters`, so the requirement is never communicated to the model [V: `#L583-L588`].

### 4.4 Provider abstraction

- **LiteLLM.** Everything goes through LiteLLM with `drop_params=True`, so unsupported parameters are silently dropped [V: `#L474-L478`].
- **Hard-coded quirks.** Temperature is forced to 1.0 for `o1/o3/gpt-5*` [V: `#L484-L485`], and parallel tool calls are disabled for a hard-coded list of models [V: `#L1351-L1358`].
- **Local models.** `model="ollama/<name>"` with `model_kwargs` passthrough [V: `README.md#L1075-L1117`]. The recommended local list (llama2, codellama, mixtral…) is dated [V: `README.md#L1180-L1189`].
- **Gaps.** There is no reasoning-effort normalization in the core loop [V: grep finds no `reasoning_effort` handling in `tiny_agent.py`]. An optional OpenAI Responses adapter is enabled by an env var [V: `README.md#L114-L148`].

### 4.5 Context, sessions, extensions, UI, safety, tests

- **Compaction.** `compact()` summarizes the conversation and **replaces** history with `[system, user(summary)]` [V: `tiny_agent.py#L2337-L2381`].
- **Dead code.** `memory_manager.py` (message importance and strategies, about 45 KB) is referenced nowhere else in the repo [V: grep over the repo].
- **Storage.** JSON file, SQLite, Postgres and Redis backends save the flat message list. There is no branching [V: `tinyagent/storage/`].
- **Hooks.** Callbacks receive `(event_name, agent, **kwargs)` [V: `#L830-L916`]. Tool-control hooks return `{proceed, alternative_response, modified_args, modified_result}`, but only `proceed`/`alternative_response` (before) and `modified_result` (after) are applied. `modified_args` appears only in a docstring [V: `#L918-L953`, `#L1435-L1447`, `#L1533-L1536`].
- **UIs.** Rich, Gradio and Jupyter UIs are callbacks. There is no process protocol [V: `tinyagent/hooks/`].
- **Sub-agents.** They are exposed as ordinary tools (`prompt`, `working_directory`, `description`). Each spawns a fresh agent with its own context, `max_turns` and an optional timeout [V: `tinyagent/tools/subagent/subagent_tool.py#L250-L338`].
- **Safety (code agent).** Static AST blocking of dangerous modules and functions, runtime import hooks, and platform sandboxes: Seatbelt, bubblewrap, Docker, Modal [V: `docs/security_guide.md#L15-L24`; `tinyagent/code_agent/providers/`].
- **Tests.** 22 pytest files; no eval harness [V, counted].

---

## 5. DeepSeek Harness (`deepseek-ai/deepseek-harness`, "dsh")

### 5.1 Purpose and philosophy

- **Positioning.** "Everything-is-a-plugin" on **Cordis**, a plugin framework in which plugins contribute services, typed events and **reversible effects** to a shared context. Its paper (arXiv 2608.25512, submitted 2026-08-26) formalizes "revertible effects" and "reactive coeffects" [V: `deepseek-ai/deepseek-harness@477b4f4205:README.md#L5-L13`; https://arxiv.org/abs/2608.25512].
- **No privileged core.** The model adapter, tool registry, session log and the agent loop itself are all plugins [V: `…/docs/architecture.md#L9-L13`]. Cordis is vendored and MIT-licensed [V: `…/vendor/README.md` manifest].
- **Composition.** A running `dsh` is a plugin tree composed from **profiles** (`web`, `headless`, `sdk`, `sdk-minimal`, `acp`). Each profile stacks **bundles** plus YAML patches [V: `…/docs/architecture.md#L15-L27`].
- **Product modes.** Standard, Code Mode (PTC), Minimal (two tools: persistent bash plus `str_replace_editor`) and Creator [V: https://deepseek.com/harness/en/].

### 5.2 Agent loop

- **Turn flow.** `turn/start` → claim input → assemble prompt sections and tool schemas → `agent/pre-step` (waterfall; may reject or rewrite) → `step/start` → `agent/request` → stream → `tool/call`* through the tool pipeline → `step/end` → loop while tools are owed → `agent/turn-stopping` → `turn/end` [V: `…/docs/architecture.md#L84-L117`; code: `…/packages/core/agent-loop/src/agent.ts#L296-L369`].
- **Invariant: "Model-visible means logged".** A runtime check ensures every model request can be reconstructed from the session log [V: `…/docs/architecture.md#L119-L127`].
- **Cordis dispatch modes** (`emit`, `waterfall`, `parallel`, `serial`, `bail`) are part of each event's contract [V: `…/docs/cordis-primer.md#L15-L35`].

### 5.3 Tool schema, validation and the guarded pipeline

- **Definition.** A `ToolDefinition` = model-facing `ToolSchema` + mandatory `output` (a JSON Schema enforced on every successful value, plus a pure `render()` to model content) + `execute(args, exec)` + optional `timeoutMs`, `isConcurrencySafe(args)`, and pure `presentCall/presentResult` for UI cards, which are safe on log replay [V: `…/docs/subsystems/tools.md#L9-L106`].
- **Authoring.** `defineTool()` validates arguments strictly before `execute`, but validates softly in the presenters so that old logged arguments still render [V: `…/packages/core/tools/src/schema.ts#L554-L632`]. The schema DSL is small: string, number, integer, boolean, null, array, object with explicit `additionalProperties`, json and exact-one `oneOf` [V: `…/tools.md#L108-L126`]. "Strict" here means validation failure is a hard `ToolArgsError`; the parameter root itself is an implicit *open* object, so unknown top-level keys are not rejected [V: `…/tools.md#L110`; `…/packages/core/tools/src/schema.ts#L449-L458`].
- **Pipeline** [V: `…/docs/tool-execution-pipeline.md#L6-L63`]:
  - `tool/call` is logged **before** execution;
  - `tools/pre-execute` waterfall (allow, deny or **ask**) → on `ask` only, `ctx.approval` (`allowed-once` continues; anything else denies) → monotonic guards → `tools/execute` waterfall (timeouts, retry) → body → `projectContent` → `tools/post-execute` → `finalizeContent` → `tool/result`. The doc states explicitly that "`ctx.approval` resolves asks before monotonic guards" [V: `…/docs/tool-execution-pipeline.md#L33-L42`, `#L63`].
- **Approval.** An `ask` resolves through the approval service. The outcomes map one-to-one to allow or deny, with distinct reasons so the model can tell a human "no" from "no approval channel" [V: `…/packages/core/tools/src/index.ts#L1727-L1765`].

### 5.4 Safety and permissions

- **Approval.** The outcome type is closed: `'allowed-once'|'rejected'|'cancelled'|'unavailable'`, and a missing or throwing answerer yields `unavailable`, which means deny. The per-session policy is `ask|never` and is stored in the log. Every ask is audited as an `approval/asked` + `approval/decided` pair that the model does not see [V: `…/docs/subsystems/approval.md#L21-L46`, `#L84-L88`].
- **Permission presets.** Named bundles of `{sandbox mode, approval policy}`: `workspace-write`+`ask` and `danger-full-access`+`never` by default. A non-matching combination shows as a derived `custom` [V: `…/docs/subsystems/permission-presets.md#L9-L24`, `#L53-L55`].
- **SAFETY.md.** It is explicit: developer preview, not audited, sandboxing does not guarantee isolation, run in a disposable VM [V: `…/SAFETY.md#L5-L15`].

### 5.5 Provider abstraction

- **Adapter-owned effort.** Reasoning effort is deliberately **adapter-owned**. `ReasoningEffortId` is an opaque branded string. Each exact provider/model route exposes `{efforts:[{id,name,description}], defaultEffort?}`, and there is no normalized ladder [V: `…/docs/subsystems/llm-streaming.md#L522-L578`]. Contrast pi's fixed ladder in §3.4 [I].
- **Multi-provider via pi-ai.** `dsh-llm-pi-ai` routes requests "through pi-ai catalogs and hand-declared gateways", including self-hosted OpenAI-compatible servers. It is one adapter among several: the README points single-provider DeepSeek deployments at `dsh-llm-deepseek`, and both can be mounted together [V: `…/packages/llm/llm-pi-ai/README.md#L32-L34`]. Its config exposes pi-ai's `compat.thinkingFormat` and a per-model `reasoningEfforts` map [V: `…/packages/llm/llm-pi-ai/README.md#L10-L12`, `#L41-L73`].

### 5.6 Context, compaction and sessions

- **Compaction seam.** Compaction is a seam: a service definition plus backends (`compaction-basic`, `compaction-tool-result-pruner`, `compaction-image-offload`) [V: `…/packages/compaction/` listing].
- **Crash-detectable locking.** It is bracketed by log-recorded `compaction/start` … `compaction/end`, so a crash leaves a detectable orphaned lock. The summary replaces a surface range via a `user/message` with a `surfaceOp` [V: `…/docs/subsystems/compaction.md#L9-L19`].
- **Session formats.** They are versioned (v0–v4), with one migration package per version step and never-renamed generation files [V: `…/docs/architecture.md#L123`].

### 5.7 Workflows, sub-agents, plan, goals

- **Sub-agents.** Multiple named providers coexist: in-process spawn or fork, ACP, **Codex**, **Claude Code**, and the dsh SDK. Capability flags (`outputSchema`, `toolFilter`, `depthLimit`, `persona`, …) are checked **before** start, so an unsupported feature fails loudly [V: `…/docs/subsystems/subagent.md#L5-L36`].
- **Workflow.** The `workflow` tool runs a *model-written JS script* with `agent()`, `parallel()`, `pipeline()`, `phase()` and `log()` helpers, under caps. Misuse throws `WorkflowError{fatal:true}` instead of degrading to a `null` item [V: `…/docs/subsystems/workflow.md#L5-L37`, `#L114-L116`].
- **PTC (Code Mode).** `run_code` becomes the only directly callable tool. The prompt embeds a generated TypeScript SDK (`interface ToolArgsMap {…}`) with typed canonical return values. Calls run through `await tools.name(args)`, read-only calls may overlap, and mutating calls are serialized [V: `…/snapshots/session/ptc-node-read-only/system-prompt.expected.md#L8`, `#L34-L52`]. Every sub-call re-enters the full guarded pipeline [V: `…/docs/tool-execution-pipeline.md#L63`]. The PTC system prompt is 26,164 bytes versus 2,794 bytes for the non-PTC session text-turn snapshot [V, file sizes]. Much of that is relocation, not pure overhead: in non-PTC mode the same tools travel as separate JSON tool schemas outside the system prompt. Total request size per mode was not compared [U].
- **Plan mode** is *soft guidance* (a prompt section plus an `exit_plan_mode` tool). Enforcement is left to sandbox and approval [V: `…/docs/subsystems/plan.md#L5`].
- **Goals** are event-sourced objectives with phases `active|paused|blocked|complete` and compare-and-set revisions [V: `…/docs/subsystems/goal.md#L7-L30`].

### 5.8 UI decoupling

- **Web UI** is served by the harness. The **Electron desktop app** runs a private host that launches the same profile runner and web app [V: `…/docs/architecture.md#L51-L55`].
- **SDK protocol.** JSON-RPC 2.0 over newline-delimited streams with only 3 requests (`initialize`, `session/prompt`, `shutdown`) and 4 notifications (`session.event`, `session.status`, `subagent.started`, `subagent.finished`) [V: `…/packages/sdk/protocol/README.md#L36-L46`].
- **ACP** (Agent Client Protocol) is served for automation [V: `…/packages/acp/acp/README.md`, Summary].
- **Rendering rule.** "Add UI or editor integration: drive `ctx.agents` and render from `session/event`" [V: `…/docs/architecture.md#L155`].

### 5.9 Tests and evals

Test tiers [V: `…/docs/testing.md#L7-L15`, `#L23-L35`]:
- unit tests with a **per-file 100% coverage gate**;
- real-API e2e;
- benchmarks;
- **recorded-session snapshots** (record once, replay deterministically, compare persisted results and the workspace tree);
- browser snapshots.

Rules: "Prefer the real implementation over a mock" (mock only the LLM, network and clock) and "Verify the world, not the self-report" (re-read files and assert that untouched files are byte-identical).

---

## 6. Cross-harness comparison of key design choices

| Concern | pi | tinyagent | dsh | Best fit for ofp-editor [I] |
|---|---|---|---|---|
| Loop shape | Small, hookable, event stream | Simple while-loop | Log-driven turn/step machine | pi's loop, with dsh's "model-visible means logged" |
| Tool contract | TypeBox input, lenient coercion | Loose Python hints | Strict input **and output** schema, presenters | dsh contract; pi-style coercion as opt-in leniency for SLMs |
| Parallelism | Per-tool `sequential` override | All parallel | `isConcurrencySafe(args)` classifier | Reads parallel, mission mutations serialized |
| Effort / thinking | Fixed ladder plus per-model map | None | Adapter-owned opaque IDs | pi ladder in the UI, per-model map underneath |
| Permissions | None (extensions) | Hooks plus OS sandbox | Closed approval outcomes plus presets | dsh approval semantics (fail-closed), presets as "effort/permission" profiles |
| Compaction | Structured summary, non-destructive | Destructive | Seam plus locks plus pruners | pi template plus a mission digest; prune old tool results |
| Sessions | JSONL tree | Flat | Versioned event log | Tree (pi) that also branches the mission document (pi-durable idea) |
| Embedding | RPC JSONL, SDK | In-process Python | JSON-RPC SDK, ACP | In-process Rust channel; optional MCP/ACP server later |
| Bulk actions | — | Python code agent | PTC typed SDK | Later: sandboxed script (e.g. Rhai) over the editor API, same guarded pipeline |
| Testing | Faux provider, docs-lift evals | Unit tests | Snapshot replay, 100% gate, verify-the-world | Faux provider plus recorded-transcript replay plus mission-state assertions |

---

## 7. What to build: an agent embedded in a Rust mission editor

The editor's agent differs from all three harnesses in one fundamental way: **its world is a typed, in-memory mission document** (units, groups, waypoints, triggers, markers, briefing, dialogue), not a filesystem. Most coding-agent machinery goes away (bash, file reads, read-before-edit policies, sandboxes). What becomes central is **transactional, reviewable edits**, **domain validation** and **small-model reliability** [I].

### 7.1 Recommended architecture (all [I] unless marked)

1. **Rust `agent` crate with pi's loop semantics.**
   - `run_loop` covers turns, parallel read tools, serialized mutation tools, the truncated-output guard, and steering and follow-up queues.
   - Hooks: `before_tool`, `after_tool`, `prepare_request`, `finish_turn`.
   - Output is a single `AgentEvent` enum sent over a channel to the GUI thread, mirroring pi's event names [V pattern: §3.2].
   - Project rules apply: one `Error` enum per crate, no `unwrap`, newtype IDs.
2. **Typed tools over the mission.** Each tool is a Rust type with `Args: Deserialize + JsonSchema` and `Output: Serialize + JsonSchema`. It is validated at the boundary, and the error message the model sees lists the paths and received args (pi) [V pattern: §3.3].
   - Store both input and output schemas (dsh) [V pattern: §5.3].
   - Model-facing IDs are newtypes (`UnitId`, `GroupId`, `TriggerId`). Unknown IDs return a tool error listing the nearest valid IDs, which helps SLMs self-correct.
3. **Mutations as change-sets, not direct writes.**
   - Mutation tools return a `ChangeSet` (an ordered list of typed ops), similar to Chord's `change(ctx, draft)` → op batch [V pattern: §3.7].
   - The editor shows a diff overlay on the map and in the outliner. **Accept / Reject / Edit** maps onto dsh-style approval outcomes, with no approver meaning deny [V pattern: §5.4].
   - Accepted change-sets become ordinary undo-stack entries, so the agent never bypasses undo.
   - Tag every tool `replay: Safe|Never` (pi harness) so session replay never re-applies a mutation [V pattern: §3.6].
4. **Small default tool set.** Roughly: `query_mission` (filtered reads), `describe_area` (map context), `apply_changes` (typed op list), `validate_mission` (domain linter), `write_text` (briefing and dialogue fields), `ask_user`, `final_answer`.
   - Put heavier guidance in **skills** that are loaded on demand, for example "trigger syntax", "OFP waypoint types" and "radio protocol style" [V pattern: pi skills §3.7].
   - Keep the base prompt in the pi range (≈1 K tokens) so that 7–14 B local models keep headroom.
5. **Provider layer.**
   - Target the OpenAI-compatible Chat Completions API first; it covers Ollama, llama.cpp, LM Studio, vLLM and most clouds. Add Anthropic and Gemini next.
   - Copy pi-ai's `compat` flags table and `thinkingFormat` switch almost verbatim as a Rust enum [V source: §3.4].
   - Use strict JSON-schema or grammar decoding when the backend supports it (pi `constrainedSampling`) [V pattern: §3.3]. For llama.cpp this means its JSON-schema/grammar support [U: exact current flags not verified here].
   - Crate choice (for example `rig`) is covered in the separate rig study.
6. **Effort levels = named presets.** Following dsh's permission presets [V pattern: §5.4], one UI selector sets several knobs:
   - thinking level, clamped per model (pi) [V pattern: §3.4];
   - max turns;
   - "plan first" on or off;
   - an automatic `validate_mission` pass after changes;
   - whether sub-agents are allowed;
   - approval policy (ask each change-set vs. auto-accept into an undoable batch).

   Example presets: **Quick** (off/low thinking, 4 turns, no plan), **Standard**, **Thorough** (high thinking, plan plus validate plus self-review sub-agent).
7. **Workflows as data first.** Define workflows declaratively (TOML/YAML), similar to pi's prompt-template chains (scout → planner → worker) [V pattern: §3.9]. For example, "Draft briefing → Generate dialogue (writer sub-agent, no mutation tools, output schema = dialogue lines) → Validate → Propose".
   - Each step has its own tool subset and output schema, and fails loudly on capability mismatch (dsh sub-agent flags) [V pattern: §5.7].
   - Model-written orchestration scripts (dsh `workflow`/PTC) are a phase-2 feature: a sandboxed embedded script language over the same guarded tool pipeline [V pattern: §5.7].
8. **Context management.** Because the document *is* the state, each request can re-inject a compact **mission digest** via `prepare_request`, and old tool results can be pruned aggressively (dsh `compaction-tool-result-pruner`) [V package exists: §5.6]. Keep pi's structured summary template for long sessions, with one change: replace "file paths" with "entity IDs/names" [V template: §3.5].
9. **Session tree that forks the mission.** Store the conversation as a pi-style JSONL tree. Link each accepted change-set to its entry so that "branch from here" restores the mission state at that point, as in pi-durable's rewindable conversation documents [V design: §3.6; implementation status U].
10. **Decision models (optional).** Add a `classify()` capability separate from chat, shaped like pi-ai [V: §3.4]. It suits cheap typed checks, such as "does this briefing contradict the objectives?" or "which of these tool families is this request about?" (routing). Treat Jev as an optional cloud provider behind that trait, not a dependency.
11. **Interoperability.** Exposing the editor's tool registry as an MCP server or ACP endpoint would let external agents (Claude Code, Codex, pi via extension) drive the editor too. dsh already consumes Codex and Claude Code as sub-agent providers [V: §5.7]; the value for us is [I].
12. **Testing.**
    - A scripted fake provider (pi `fauxProvider`) for deterministic loop tests [V pattern: §3.4].
    - Recorded-transcript replay tests that assert the **final mission** equals a synthetic expected fixture (dsh "verify the world") [V pattern: §5.9].
    - Optional live-model evals with and without skills (pi docs-lift) [V pattern: §3.11].
    - Fixtures stay synthetic (project rule).

### 7.2 What not to copy

- **pi's "YOLO" default.** Acceptable for a terminal coding agent. In an editor, the mission file is the user's creative work, so change-sets must be reviewable and undoable [I].
- **tinyagent's patterns** [V defects: §4.3–4.5]:
  - unvalidated arguments;
  - silently coercing malformed JSON to `{}`;
  - schemas that default complex types to `"string"`;
  - destructive compaction;
  - hook fields that are documented but ignored.
- **dsh's size.** 54 top-level package groups under `packages/`, multi-megabyte persistence schemas (e.g. `docs/persistence-schema.json` is about 2.2 MB) and generated catalogs [V: directory listing and `docs/` sizes]. The *seams* (service definition / provider / consumer) are worth copying as Rust traits compiled in-tree. Dynamic plugin loading and hot reload are not needed early [I].
- **Model-written JS workflows as a first feature.** They add a script runtime, sandboxing and caps. Declarative workflows cover the stated needs (dialogue, briefings, placement) first [I].

---

## 8. Licenses

- **pi:** MIT, © 2025 Mario Zechner [V: `earendil-works/pi@2b0a123de9:LICENSE#L1-L3`]; every package with a `license` field at the pinned commit declares MIT [V]. Moved to Earendil Works in 2026 and "will stay MIT licensed" [V: https://mariozechner.at/posts/2026-04-08-ive-sold-out/]. The same post announces future Fair Source (delayed-open) features and proprietary enterprise offerings alongside the MIT core, so re-check the license of any file added after the pinned commit before porting it [V: same post].
- **tinyagent:** MIT, © 2025 askbudi [V: `askbudi/tinyagent@1b85dc351f:LICENSE#L1-L3`].
- **dsh:** MIT, © 2026 DeepSeek [V: `deepseek-ai/deepseek-harness@477b4f4205:LICENSE#L1-L3`]. All nine vendored Cordis-family packages are MIT, © 2021-present Shigma [V: `…/vendor/*/LICENSE`]. Third-party notices are in `THIRD_PARTY_NOTICES.md` [V].
- **Implication [I].** MIT is compatible with both MIT/Apache and GPL-3.0 project licenses. Ported *ideas* need no attribution; translated *code* (for example a direct port of pi-ai's compat table or the validation coercion logic) should keep an MIT notice in a `THIRD_PARTY_NOTICES` file.

---

## Open questions

1. **Native Rust vs. sidecar.** Is a native Rust agent crate clearly better than shipping pi as a sidecar binary driven over RPC? pi documents standalone binaries [V: `earendil-works/pi@2b0a123de9:README.md#L65-L76`], but custom *tools* are defined by in-process TypeScript extensions. Whether mission tools could be bridged over RPC without writing TS is **[U]**.
2. **pi-durable documents.** Source and tests for rewindable documents and `asOf` forks exist (see §3.6), but is that code complete and stable enough to study as code rather than spec? **[U]**
3. **Local model choice.** Which local model and quantization gives reliable tool calls with our tool count and ~1 K-token prompt? This is to be measured with our own evaluation instruments: scripted and recorded sessions scored on the resulting mission state (§7.1, item 12). **[U]**
4. **Constrained decoding.** Does constrained JSON-schema/grammar decoding on llama.cpp or Ollama materially raise tool-call validity for 3–8 B models on our schemas? **[U]**; measure it.
5. **Jev fit.** Do Jev-class decision models add value over a small LLM with a strict output schema for routing and consistency checks? Cost, latency and privacy (cloud-only) are unverified; [16-decision-models.md](16-decision-models.md) covers the candidates and the evidence we require. **[U]**
6. **Review UX.** Should change-set approval be per tool call (dsh style) or per turn (batch review)? This is a UX decision to prototype.
7. **Tool definitions.** Should the mission tool registry double as an MCP server from day one, so tool definitions are written once? **[I: likely cheap, unverified effort]**

---

## Sources

Code (pinned):
- `earendil-works/pi@2b0a123de9`: `README.md`, `LICENSE`, `packages/agent/{README.md,src/agent-loop.ts,src/harness/pico3/chord.ts,docs/harness.md}`, `packages/ai/{README.md,src/types.ts,src/models.ts,src/utils/validation.ts,src/api/simple-options.ts,src/api/constrained-sampling.ts,src/api/openai-completions.ts,src/api/system-one-shared.ts,src/providers/typesafe.ts}`, `packages/coding-agent/{README.md,src/core/sdk.ts,src/core/system-prompt.ts,src/core/tools/*.ts,src/core/compaction/compaction.ts,docs/*.md,examples/extensions/*}`, `packages/chord/README.md`, `packages/durable/{README.md,docs/pico-v5.md,src/documents.ts,src/session/forks.ts}`, `packages/{protocol,server,client}/README.md`, `packages/evals/README.md`
- `askbudi/tinyagent@1b85dc351f`: `README.md`, `LICENSE`, `pyproject.toml`, `tinyagent/tiny_agent.py`, `tinyagent/tools/subagent/subagent_tool.py`, `tinyagent/memory_manager.py`, `tinyagent/code_agent/*`, `docs/security_guide.md`
- `deepseek-ai/deepseek-harness@477b4f4205`: `README.md`, `LICENSE`, `SAFETY.md`, `vendor/README.md`, `docs/{architecture.md,cordis-primer.md,tool-execution-pipeline.md,tool-catalog.md,testing.md}`, `docs/subsystems/{tools,approval,permission-presets,llm-streaming,compaction,workflow,ptc-runtime,subagent,plan,goal,system-prompt}.md`, `packages/core/tools/src/{schema.ts,index.ts}`, `packages/core/agent-loop/src/agent.ts`, `packages/llm/llm-pi-ai/README.md`, `packages/sdk/protocol/README.md`, `packages/acp/acp/README.md`, `snapshots/sdk/text-turn/system-prompt.expected.md`, `snapshots/session/text-turn/system-prompt.expected.md`, `snapshots/session/ptc-node-read-only/system-prompt.expected.md`

Web:
- https://mariozechner.at/posts/2025-11-30-pi-coding-agent/ (pi design rationale; <1000-token claim; no MCP, sub-agents or plan mode; YOLO)
- https://mariozechner.at/posts/2026-04-08-ive-sold-out/ (move to Earendil, stays MIT, future Fair Source/proprietary tiers) and https://www.pi-map.org/news/pi-joins-earendil/ (now 301-redirects to https://piagent.fyi/news/pi-joins-earendil/, an unofficial community site)
- https://github.com/askbudi/tinyagent/commits/main (last commit 2025-09-29)
- https://deepseek.com/harness/en/ (developer preview, MIT, Standard/Code/Minimal/Creator modes)
- https://arxiv.org/abs/2608.25512 (Cordis paper, "A Programming Paradigm for Spatiotemporal Composability")
- https://typesafe.ai/blog/introducing-system-one-models-and-jev (post header dated 2026-09-15) and https://www.datacamp.com/blog/system-one-models-jev (Jev / System One; dates verified, capability claims are vendor and press claims)

---

## Verification notes

Adversarial fact-check on 2026-09-26 against the pinned clones and live web pages.

**Confirmed as written:**

- All LICENSE headers (pi © 2025 Mario Zechner; tinyagent © 2025 askbudi; dsh © 2026 DeepSeek; 9 vendored Cordis-family packages © 2021-present Shigma).
- pi's 8 tools and 4 defaults.
- The default-prompt reconstruction (re-derived: exactly 2,567 chars / 356 words; path-dependent).
- The author's "< 1000 tokens", "will not support MCP" and "full YOLO mode" quotes.
- The loop hooks and truncated-output guard (`agent-loop.ts#L263-L269`, `#L475-L500`).
- The `ThinkingLevel` ladder, the `thinkingLevelMap` null semantics, and the 11 `thinkingFormat` values.
- The classifier types and Jev model IDs.
- The README's "no built-in permission system" and its containerize guidance.
- The dsh closed `ApprovalOutcome` and fail-closed behavior (docs and `tools/src/index.ts#L1727-L1765`).
- dsh's mandatory output schema, `defineTool` validation before `execute`, adapter-owned `ReasoningEffortId`, and the `dsh-llm-pi-ai` README.
- The PTC and SDK snapshot sizes (26,164 and 2,475 bytes).
- dsh's developer-preview and not-audited statements.
- The tinyagent defects (no argument validation, `{}` fallback, unused `modified_args`, misplaced `required`, destructive `compact()`, unimported 44,916-byte `memory_manager.py`), v0.1.20, and the last commit on 2025-09-29.
- The pinned commit dates.

**Corrected:**

- The dsh pipeline order: approval runs **before** the monotonic guards, not after them. Fixed in the TL;DR and §5.3.
- `clampThinkingLevel` searches upward first rather than picking the "nearest" level.
- pi's own null→`""`/0/false coercion applies only to non-TypeBox schemas.
- The README's Ollama/vLLM/SGLang advice is conditional.
- The `noul` mapping citation line range.
- Test counts: pi 627, not 626; dsh 1,861, not 1,738.
- dsh package groups: 54, not "about 60".
- The pi-durable documents status: code and tests exist.
- The PTC prompt growth is mostly schema relocation.
- The `defineTool` parameter root is open, so extra keys pass.
- dsh also has a direct `dsh-llm-deepseek` adapter.
- The pi licensing note now covers the announced Fair Source and proprietary tiers.
- The pi-map.org link now redirects to an unofficial community site.
- The Jev launch date is now verified (2026-09-15).

**Not re-verified (spot checks only):** the dsh counts of about 30 tool packages and about 65 tool names; every line range in §3.7–§3.9, §4.5 and §5.7–§5.8. The ranges I sampled matched.

None of the corrections changes the bottom-line recommendation. The pipeline-order fix matters only if we copy dsh's ordering literally: the recommended order is pre-execute policy, then user approval, then invariant guards.
