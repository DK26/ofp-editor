# Token efficiency and compaction: lessons from agent harnesses

Research doc 57 for Plotroom (`ofp-editor`). Research date: 2026-09-28. Audience: contributors and LLM coding agents; it is meant to be
read alone.
Question answered (owner, 2026-09-28): "Learn from the following harnesses how to achieve perfect token efficiency. Feel free to extend
beyond these products, or directly inspect their source code: DeepSeek Harness, Pi Agent, ToFu, Strands Harness, and others. Including
also compaction and summary methods." In Plotroom's terms: which techniques cut the tokens, money and local seconds Wilco spends per call
and per workflow, and which compaction and summary method should Wilco use where a history does grow?

**Status.** Research and proposals. No model was called and no money was spent. Harness source code was read from public shallow clones
at the commits in §1.1 (23 harness and research repositories plus the llama.cpp server). One existing measurement was re-analysed with a
throwaway script: the stored llama-server records of `tools/local-qual` from the 2026-09-28 Qwen3.5-4B runs (§4.2). Those records live in
the git-ignored `tools/local-qual/results/`, so their figures are reproduced here with the method. Everything in §3.6, §4.3, §5 and §6 is
a proposal [I].
**Epistemic legend.** **[V]** verified at the source: code at the pinned commit, a vendor page, a paper, or a repo doc by section.
**[V-author]** a publisher's own figure about its own work, not reproduced by us. **[I]** our inference, arithmetic or proposal. **[U]**
unknown.
**Citation aliases.** `alias:path:lines` at the commits in §1.1. The aliases are lowercase on purpose: they point at newer commits than
doc 40's uppercase `CX:`, `OC:` and `PI:`, which stay valid for doc 40's own citations.
**Areas.** "Steps" are PICK, FILL, COMPOSE, text-slot and EXPLAIN capsules. "Conversations" are Wilco's assist and chat modes (doc 40's
"Ask chat"). "Long runs" are campaign-from-brief and other multi-stage workflows. "Journal" is the decision journal and ledger (doc 38).
"Local cache" is llama-server prefix and slot reuse; "cloud cache" is provider prompt caching.
**Relation to sibling docs.** Extends doc 40 (token economy: rules R1–R17, capsule layout §4.1, cost model) and doc 11 (earlier pi and
DeepSeek Harness study at older commits) without repeating them. Uses doc 10 (Codex, opencode), doc 12 §5 (query-don't-dump, RefStore,
reducers, ledger), doc 21 §8 (capsules; no model-written summaries of facts), doc 25, doc 38 (journal, fan-out, budgets), doc 51 (H23,
H24, V10, V11), doc 55 and [D048](../decisions/D048-per-model-harness-presets.md) (per-model presets), doc 56 and the open design gaps DG019–DG027 and DG039.
**Data.** [`docs/research/data/token-efficiency-techniques.csv`](data/token-efficiency-techniques.csv): 116 techniques with the columns
`technique, category, harnesses, evidence, measured_effect, plotroom_fit, plotroom_area, verdict, sources`. Verdicts by first word:
ADOPT 68, ADAPT 19, KEEP 13, REJECT 16.
**Hygiene.** All studied code is MIT or Apache-2.0 (§1.1). Ideas are re-implemented, never copied; summary prompts are quoted in a few
words at most.

## TL;DR

- **Most compaction code in the studied harnesses exists to manage one growing transcript.** Plotroom's fresh, code-built capsule per
  decision (doc 21 §8.1) gets that for free in steps and long runs: no summary calls to pay, no summary drift, no lost artifact trail,
  and a bounded prompt that can be counted before sending. Compaction is needed only in Wilco conversations, and there mostly on 8K local
  windows [I on V].
- **For growing histories, deterministic masking plus exact recovery beats LLM summaries on the evidence.** Masking old tool output
  halves cost at an equal solve rate (Complexity Trap, 2508.21433) [V]. Hermes Agent's lean policy (short tail, verbatim user messages, a
  code-harvested identifier index, a recovery pointer) recalled 68.3% at ~49K retained tokens against 45.8% at ~162K for its fatter
  summary policy [V-author]. Summaries score worst on the artifact trail (2.19–2.45 of 5 in Factory's probes) and lengthen agent runs by
  13–15% [V].
- **Summary method for Plotroom: a typed Session Digest rendered by code from the journal** (verbatim user asks, pinned constraints,
  decisions and entity tokens with journal ids, open findings, workflow position, lookup handles). A model may add only labelled narrative
  fields, written as a warm-prefix fork, applied as a validated delta patch, and confirmed by the user as chips before anything becomes a
  constraint. Workflows never read it as facts (§3.6).
- **Every auxiliary call must extend the exact cached prefix, never start a new prompt.** Qwen Code's compaction request was 92.8% cached
  this way on a live provider, where its old cold summariser matched zero cached tokens in a mock exact-prefix comparison; DeepSeek
  Harness, Codex, kimi-cli's `/btw`, OpenHands' `ask_agent` and Hermes' forks do the same [V-author].
  Repairs, K samples and EXPLAIN-this-decision append at the capsule's tail. Calls whose prefix nobody re-reads go uncached (pi, Strands).
- **New local finding: on hybrid and sliding-window models, llama-server reuses a prefix only at message boundaries.** Qwen3.5 is hybrid
  (doc 14). In our own local-qual records, identical Fill prompts reused all but 4 tokens (prefill 1.6–2.3 s cold, 0.1–0.4 s warm), while
  Pick samples reused only the 58-token system message on 731 of 734 calls [V data; I cause]. Capsule messages should split at the
  breakpoints: system = stage pack; user = request and digest; a fixed assistant acknowledgement; user = sample tail (to be tested, §4.3).
- **Cache discipline is testable, so test it.** Render every capsule through the production serializer and the llama.cpp chat template,
  assert byte identity up to each breakpoint, and include seeded regressions (a timestamp above BP1, a moved tail) that the test must
  catch (goose, ToFu, Codex, OpenHands). The ledger records a named cause for every cache miss (ToFu) [V].
- **In conversations, rewrite already-sent bytes only in batches at cache-cold moments, and express every threshold as a fraction of the
  served per-slot window.** ToFu waits for three cold rounds, OpenHands condenses to half, Cline batches 64 KB, Hermes needs 4,096
  tokens of gain [V]. The absolute defaults of pi, kimi-cli, Qwen Code, DeepSeek Harness and Hermes disable or break compaction at 8K
  [I on V].
- **Tool results in conversations become typed envelopes**: shown and total counts, a cursor derived from the rendered rows, the
  document revision, an evidence id, exact omission counts and a narrowing hint. Add "unchanged since revision N" receipts (ToFu measured
  −51% on 47 repeats, counterfactual), superseded-view stubs and a split between model text and display detail. Handles point into the
  journal, never at files (product scope).
- **Money needs better accounting, not more cleverness.** Keep disjoint usage buckets, provider-reported versus estimated costs and a
  harness-overhead bucket. Show a cold-cache chip on resume (opencode: 12 cold resumes were 51% of one session's cost). Choose the TTL by
  pacing (Hermes: 63% of interactive cache writes were cold re-writes). Model the in-batch hit rate per provider: DashScope reports zero
  cached tokens inside a batch, so its batch discount loses above a 62.5% realtime hit rate [V-author].
- **Reject**: model-managed context tools, opaque provider compaction items, programmatic tool calling, LLM or embedding selection of
  history, token-dropping compression, per-turn sliding windows, per-turn tool-list changes, fixed keep-alive pings and mid-history
  stepping-stone breakpoints (§6.2 F13).

## 1. What each studied harness does

### 1.1 Code studied

| Alias | Repository @ commit (date) | Licence | What it is |
| --- | --- | --- | --- |
| `tofu:` | NiuTrans/ToFu @ `2bf26ed` (2026-09-06), v0.17.x | MIT | Python research harness built for token efficiency; paper arXiv 2607.11423 |
| `strands:` | strands-agents/harness-sdk @ `c56b7de` (2026-09-26) | Apache-2.0 | Strands Agents SDK (Python, TS) and the assembled "Strands Harness" (renamed from sdk-python) |
| `dsh:` | deepseek-ai/deepseek-harness @ `21638c5` (2026-09-27) | MIT | TypeScript harness built from plugins; doc 11 studied `477b4f4` |
| `pi:` | earendil-works/pi @ `6f75515` (2026-09-28) | MIT | Pi coding agent, pi-ai and the experimental pico3 harness; docs 11 and 40 studied `2b0a123` |
| `codex:` | openai/codex @ `abc8f0c` (2026-09-27) | Apache-2.0 | codex-rs; docs 10 and 40 studied `e72da2b` |
| `oc:` | anomalyco/opencode @ `b471c2b` (2026-09-26, `dev`) | MIT | v1 runtime and v2 runtime (`packages/core`, `packages/llm`) |
| `qwen:` | QwenLM/qwen-code @ `3f5ae3f` (2026-09-27) | Apache-2.0 | Qwen Code CLI (a Gemini CLI fork) |
| `gem:` | google-gemini/gemini-cli @ `2fe7c2d` (2026-09-25) | Apache-2.0 | Gemini CLI, including an experimental graph context manager |
| `kcode:` | MoonshotAI/kimi-code @ `be7d5f5` (2026-09-24) | MIT | Kimi Code, successor of kimi-cli |
| `kcli:` | MoonshotAI/kimi-cli @ `9ab1286` (2026-09-22; archived 2026-09-23) | Apache-2.0 | kimi-cli 1.52 with the kosong LLM layer |
| `oh:` | OpenHands/software-agent-sdk @ `3311ba9` (2026-09-27) | MIT | Current home of the OpenHands condensers |
| `oh0:` | OpenHands/OpenHands tag 0.62.0 @ `7fbb48c` (2025-11-11), sparse | MIT (`enterprise/` not checked out) | Legacy V0 condenser zoo |
| `swe:` | SWE-agent/SWE-agent @ `3ea751c` (2026-07-16) | MIT | History processors, windowed tools |
| `mini:` | SWE-agent/mini-swe-agent @ `04d809c` (2026-09-03); draft PR #948 @ `2aaed7f` | MIT | Linear-history baseline |
| `ctrap:` | JetBrains-Research/the-complexity-trap @ `bf15b5f` (2025-11-18) | MIT | Companion code for arXiv 2508.21433 |
| `acon:` | microsoft/acon @ `d63f9ae` (2025-10-14) | MIT | Companion code for arXiv 2510.00615 |
| `aider:` | Aider-AI/aider @ `5dc9490` (2026-05-22) | Apache-2.0 | Repo map, chat summary, cache keep-alive |
| `goose:` | block/goose @ `04ed836` (2026-09-25) | Apache-2.0 | Rust agent with cache-semantics tests |
| `cline:` | cline/cline @ `252082b` (2026-09-26) | Apache-2.0 | Cline SDK and apps |
| `letta:` | letta-ai/letta-code @ `f378d20` (2026-09-27) | Apache-2.0 | Current Letta (the `letta-ai/letta` main branch is now a stub) |
| `letta0:` | letta-ai/letta, `archive` branch @ `56ba9c2` (2026-08-13), sparse | Apache-2.0 | MemGPT-lineage server summariser |
| `da:` | langchain-ai/deepagents @ `b5f22b0` (2026-09-27) | MIT | Deep Agents SDK and CLI |
| `hermes:` | NousResearch/hermes-agent @ `e98be8a` (2026-09-27) | MIT | General agent with a committed compaction recall eval; doc 51 §3.1 studied `04ea129` |
| `lcpp:` | ggml-org/llama.cpp @ `4da6337` (2026-09-27), sparse (`tools/server`, `common`) | MIT | The local runtime, not a harness |

The GitHub commits API does not resolve three of these 7-character prefixes; their full hashes are hermes-agent
`e98be8a328050f1fc978fa4f0f27614801183c56`, gemini-cli `2fe7c2d3f065dc40ad573d50b2091116f8a4aa18` and deepagents
`b5f22b01aff7cfe328d632de086c31247c2b1081`.

Also used but not re-studied: headroom (doc 12), Mistral Vibe (doc 51 §3.5), and Claude Code, which is closed source and cited only from
its public docs and blog.

### 1.2 Mechanisms at a glance

"W" is the context window, "O" the reserved output. Details and line numbers are in §1.3, §2 and the CSV.

| Harness | Compaction trigger | Method | Kept verbatim | Cache handling | Tool output | Local KV |
| --- | --- | --- | --- | --- | --- | --- |
| ToFu | min(0.9 × usable, 128K working set) plus a payback gate | L1: cold results become placeholders, only once the cache is cold; L2: "state receipt" 800–1,600 tokens (cap 2,200), rejected when evidence ids are missing | objective anchor; ≤ 8 user messages or 4,096 tokens; in-flight turn; newest tool round | 4 markers (tail and tools reserved), 1 h prefix / 5 min tail, settle gate, miss classifier | per-tool caps, full result persisted, 2,000-char preview, typed envelope, unchanged receipts | none |
| Strands | proactive 0.7 before every call in the conversation managers; the `auto` context manager summarises at 0.85; overflow retry ≤ 3, only on progress | results > 1,500 tokens → 750-token preview plus stash reference; summarise the oldest 30% | pinned, first user, last 4–10 | one rolling point on the last user message; `prompt_cache_key` per session; one-shots uncached | offloader at production; `retrieve_context` ≤ 10K | `cache_prompt` on; `/tokenize`; no `n_ctx` read (assumes 200K) |
| DeepSeek Harness | ⌊min(0.8W, W − O − 65,536)⌋; overflow retry only if the surface changed | summary call replays the warm prompt plus a trailing instruction; 8-section checkpoint; fail-closed; shrink guard | system head; newest 16% of W − O; tool pairs | in-history system and tool updates; request series; live cache test | pruner under pressure (8,192 → 4,096 head + 1,024 tail chars); spill > 12,500 tokens | none |
| pi | context > W − 16,384; keep 20,000; one overflow retry | serialized-transcript summary, 6 sections, iterative; pico3 appends the request to the cached transcript | token tail; cumulative file lists by code | 3 rolling breakpoints; prompt section patches; deferred-tool placeholder; cost-aware keep-warm | 2,000 lines / 50 KB with continuation hints; model text vs `details` | reads server `n_ctx`; no `id_slot` |
| Codex | 90% of W (95% usable); counts body after prefix | local 9-line handoff prompt; server v2 opaque item; experimental `new_context` reset without summary | user messages ≤ 20,000 tokens (v2: 64,000) | WorldState diffs appended; key per session; incremental-continuation check | middle truncation, 10,000 tokens × 1.2 per tool | none |
| opencode | v1 after each step; v2 pre-send estimate plus one overflow retry | prune when > 20K reclaimable beyond a 40K protected tail; anchored template summary | tail 25% of usable, clamped 2K–15K | v2 context epochs with deltas; cache policy on last tool, system, latest user | 2,000 lines / 50 KB, full text to a file | none |
| Qwen Code | min(0.85W, W − 20K − 13K); warn / auto / hard tiers; breaker after 3 failures | microcompact to placeholders (keep 5 per kind, clear to half); `state_snapshot` XML; compaction reuses the main prefix | plan, tasks, 5 recent files, images re-attached by code | typed prompt layers; name-sorted tools; tool-search bridge | 25K chars / 1,000 lines → file plus preview; batch water-fill | none |
| Gemini CLI | 0.5 × W; masking protects 50K and waits for 30K prunable | `state_snapshot` plus a self-check call; experimental JSON delta snapshot | newest 30%; retrieval tool outputs | implicit only; model sticky per prompt | 40K chars or 4 × remaining, 20/80 head/tail | LiteRT router; no reuse |
| Kimi Code | ≥ 0.85W or used + 50K; learned window | handoff summary through the same prefix | user messages by typed origin (18K tail + 2K head); TODO re-rendered | frozen system prompt in the event log; change-keyed reminders; miss detector; "cache expired" dialog | 50K chars → file, 4,096 + 1,024 preview | none |
| kimi-cli | ≥ 0.85W or tokens + 50K ≥ W | separate summariser prompt, no tools (cold) | last 2 messages plus later tool messages | persisted system prompt; `/btw` fork with refused tools | 50,000 chars; output vs display | none |
| OpenHands SDK / V0 | tokens > max or 80–240 events; condense to half; min progress 10% | rolling LLM summary (from 500-char previews); V0: masking, amortized, attention, structured | first 2–6 events | static and dynamic system blocks with snapshot tests; `ask_agent` fork | head/tail 30K chars; file on clip | none |
| SWE-agent / mini / Complexity Trap | none (exit on overflow); masking every turn | last-n observations with `polling`; summary every 21 turns; hybrid | first observation, demos | rolling 2 markers; state diff stripped from older turns | 100K chars; 100-line viewer; search refuses > 100 hits | vLLM prefix cache |
| ACON | history > 4,096; observation > 1,024 tokens | optimised guideline LLM compressor; distilled small compressors | system, first prompt, last k | none designed | LLM observation compressor | vLLM LoRA |
| aider | history > W/16 (clamp 1K–8K), in the background | recursive head/tail summary by the weak model | tail half; files re-read from disk | 3 breakpoints; repo map frozen while caching | lint windows; `/tokens` ledger | Ollama `num_ctx` per request |
| goose | 0.8; reactive ≤ 2 per turn | JSON-structured summary with raw fallback; middle-out tool removal | last user message; dual visibility | `CacheSemantics` per model; prefix-invariance tests; lookback anchor | > 200K chars → file | in-process llama.cpp, no reuse |
| Cline | 0.9 of input budget; target 0.7 / 0.5 | deterministic "basic" or agentic summary | typed user prompts; last answers; code-built action ledger | rolling marker; Bedrock `cachePoint`; sticky session | 8,000 chars per result at render; outdated reads batched at 64 KB | Ollama `num_ctx` fixed |
| Letta Code / archive | W − min(16,384, 0.2W); server 0.9W | sliding summary (30%); server self-compact reuses the cache | kept tail; nothing deleted | prompt compiled once; memory delta at the tail | caps, overflow file, 32K backstop | `n_ctx` from `/props`; no `id_slot` |
| Deep Agents | 0.85W, keep 10%; budget 95% minus output | 4-section summary; history archived with a pointer | goal re-appended | memory frozen per thread; cold-cache advisor | > 20K tokens → file plus 5 + 5 lines | none |
| Hermes | 50% of (W − O), floor 75% under 512K; breaker | lean summary, anchor index, verbatim user messages, recovery pointer; opt-in micro | tail 2.5% of W, clamped, ≤ 20% of W | 4-marker planner on a copy; TTL by pacing; scope keys; cache-parity forks | spill at 15% / 30% of W | managed llama.cpp; budgets from the served window; no `id_slot` |

### 1.3 Per-harness notes

- **ToFu** (`tofu:`). The most complete token engineering found. Three layers: size-aware budgeting (large results externalised as a
  preview plus a reference), cache-aware micro-compaction, and a query-aware state receipt near the limit (target 800–1,600 tokens, hard
  2,200; `tofu:docs/CONTEXT_COMPACTION.md:61-78`). L1 never edits the warm prefix and opens only after three consecutive verifiably cold
  rounds, because one transient miss had caused "a self-feeding re-bill loop" (`tofu:lib/tasks_pkg/cache_tracking/_prefix.py:37-143`).
  A summary is bought only if it pays back within the observed prefix lifetime (`tofu:docs/CONTEXT_COMPACTION.md:90-98, 125-141`). A
  model summary that misses evidence ids is replaced by `TaskStateSnapshotV1`, rebuilt from events, where completion comes from tool
  status and never from prose (`tofu:lib/tasks_pkg/context_composer/task_state.py:80-186`). Lesson: prune only when the cache is already
  lost; state comes from events.
- **Strands** (`strands:`). The "auto" default truncates tool results over 1,500 tokens to a 750-token preview with stash references and
  a paginated `retrieve_context` capped at 10,000 tokens (`strands:strands-py/src/strands/_context_manager/context_manager.py:31-34,
  83-89`; `.../retrieval_tool.py:24-26`). The date and cwd are injected at the tail of the user turn because a per-turn value "would bust
  the cached system-prompt prefix" (`strands:harness-py/src/strands_harness/plugins/environment.py:1-12`). An experimental "agentic" mode
  lets the model manage its own context through meta-tools. Lesson: gate size at production; retrieve by handle.
- **DeepSeek Harness** (`dsh:`). The summary call replays the last request's system prompt, tools and messages and appends the
  instruction as the final user message "so the provider's KV cache is reused"
  (`dsh:packages/compaction/compaction-basic/src/summarizer.ts:25-31`). A summary that is not smaller than what it replaces is refused
  (`.../region.ts:410-422`). Every reduction is a
  logged bracket citing the entries it shadows, and each package README states its "Token effect" and "KV Cache effect". Since doc 11,
  headroom and the summary cap default to 65,536 tokens (`.../config.ts:75-76`), which gives small windows a negative budget. Lesson:
  auxiliary calls are prefix extensions; reductions are logged events.
- **pi** (`pi:`). New since doc 11: cost-aware keep-warm ($0.05 minimum expected saving, 0.15 idle continuation probability;
  `pi:packages/coding-agent/src/core/cache-warmer.ts:15-32`), prompt changes sent as section patches, and a pico3 "collapse" that
  appends the summary request to the cached transcript. A placeholder deferred tool is declared from the first request because otherwise
  Anthropic's hidden scaffolding causes a "full miss" (`pi:packages/ai/src/api/anthropic-messages.ts:186-196`). Its absolute defaults
  (reserve 16,384, keep 20,000; `pi:packages/coding-agent/src/core/compaction/compaction.ts:148-152`) leave compaction with nothing to
  reclaim at 8K (§3.2).
- **Codex** (`codex:`). Settings are typed WorldState sections sent in full once, then only as appended diffs
  (`codex:codex-rs/core/src/context/world_state/mod.rs:207-260`). An effort change is appended as a ConfigurationUpdate so request fields
  keep the cache (`codex:codex-rs/core/src/session/reasoning_effort.rs:1-157`). After local compaction it keeps real user messages up to
  20,000 tokens verbatim (`codex:codex-rs/core/src/compact.rs:55`). The experimental `new_context` resets the window without a summary
  and recovers state through notes and read-only history tools. Lesson: reset from state rather than summarise.
- **opencode** (`oc:`). v2 "context epochs" freeze a typed baseline and append changes as system-update messages
  (`oc:packages/core/src/system-context/index.ts:198-291`). Pruning clears old tool output once more than 20K is reclaimable beyond a 40K
  protected tail (`oc:packages/opencode/src/session/compaction.ts:28-33`). Its issue tracker is the best field record of cache failures
  (§3.5).
- **Qwen Code** (`qwen:`). Compaction re-sends the main prefix and appends the directive: 92.82% of the compaction request cached in a
  one-off live DashScope check; in a deterministic mock the old cold summariser matched zero cached tokens
  (`qwen:docs/design/chat-compression-cache-sharing.md:69-83`). Microcompaction clears old results
  down to half its trigger. A measured "idle cost" of 46,734 tokens before the first message (98.7% of the first request) drove a
  resident-context diet. Batch loses to realtime on DashScope above a 62.5% hit rate (`qwen:docs/users/features/batch.md:48-67`).
- **Gemini CLI** (`gem:`). Compression fires at 50% of the window (`gem:packages/core/src/context/chatCompressionService.ts:45`) and
  runs a second self-check call. Masking protects 50K tokens of tool output and waits until 30K are prunable. The experimental context
  manager has content-derived node ids, 5K hysteresis and a JSON delta-patch snapshot applied by code under a 4,000-token budget
  (`gem:packages/core/src/context/utils/snapshotGenerator.ts:44-371`).
- **Kimi Code** (`kcode:`). The system prompt is frozen in the event log; reminders are re-announced only when their inputs change; a
  miss detector fires below 95% of the previous cache read; a dialog warns when the cache has expired on resume. Issue #2720: background
  compaction was cancelled 21 of 24 times at ~160K tokens each.
- **kimi-cli** (`kcli:`). `/btw` side questions reuse the exact prompt and tools (advertised, all refused) and never enter history
  (`kcli:src/kimi_cli/soul/btw.py:1-9`). Its compaction call uses a separate prompt without tools, so it reads nothing from the cache [I].
  The dual trigger fires on every step for windows of 50K or less (`kcli:src/kimi_cli/soul/compaction.py:60-76`).
- **OpenHands SDK and V0** (`oh:`, `oh0:`). Static and dynamic system blocks, with tests forbidding timestamps, cwd, home directory and
  hostname in the static one (`oh:tests/sdk/context/prompts/test_prompt_snapshot.py:223-232`). The condenser halves the view and
  refuses to act below 10% progress (`oh:openhands-sdk/openhands/sdk/context/condenser/llm_summarizing_condenser.py:72-80`). The
  summariser is fed 500-char display previews (§3.5). V0 records that its summarising condenser cost $40 more on SWE-bench Verified
  "due to the lower prompt cache utilization" (PR #6597).
- **SWE-agent, the Complexity Trap and mini-swe-agent** (`swe:`, `ctrap:`, `mini:`). Last-n observation masking, with `polling` so
  the prefix changes only every P steps (`swe:sweagent/agent/history_processors.py:104-122`). The Complexity Trap measured masking at
  equal solve rates and half the cost. mini-swe-agent's unprocessed linear history is the baseline: median $0.355 and 39.8 calls per
  instance on the SWE-bench Verified bash-only leaderboard.
- **ACON** (`acon:`). Optimises compressor guidelines from failed-versus-succeeded trajectory pairs and distils small compressors: 26–54%
  lower peak tokens, though its cost table excludes caching and latency rises. An in-code note: giving the observation compressor the
  history summary "rather makes observation optimization worse" (`acon:src/productive_agents/agents/memory.py:341-344`).
- **aider** (`aider:`). A repo map of tree-sitter tags ranked by personalised PageRank and fitted to a token budget by binary search
  (`aider:aider/repomap.py:365-706`); three cache breakpoints; the map frozen while caching is on (`aider:aider/main.py:954-955`); fixed
  keep-alive pings. Warnings: the date sits in the system prompt, and the DeepSeek cost fallback bills cache hits at full price
  (`aider:aider/coders/base_coder.py:2092`).
- **goose** (`goose:`). A `CacheSemantics` enum per (provider, model), unknown pairs defaulting to strict prefix matching
  (`goose:crates/goose-provider-types/src/cache_semantics.rs:8-51`), and a prefix-invariance test run through the real projection and
  every provider formatter, with seeded regressions that must fail (`goose:crates/goose-provider-types/tests/prefix_invariance.rs:1-8`).
- **Cline** (`cline:`). Deterministic per-result caps at render time keep request N a byte prefix of request N+1; outdated reads are
  replaced only in 64 KB batches (`cline:sdk/packages/core/src/session/services/message-builder.ts:28-51`). The deterministic "basic"
  compaction keeps typed user prompts and builds an action ledger in code. Its docs say summarisation reuses the prompt cache
  (`cline:docs/features/auto-compact.mdx:41-45`); the code sends a new system prompt.
- **Letta Code and the Letta archive** (`letta:`, `letta0:`). The system prompt is compiled once per conversation and reused while the
  memory is unchanged; a mid-conversation memory change goes to a tail block. The server's self-compaction appended its request to the
  cached history "for cache compatibility" (`letta0:letta/services/summarizer/self_summarizer.py:23-138`). A fallback silently replaced
  a user's custom summary prompt (letta-code #3954).
- **Deep Agents** (`da:`). Non-destructive summarisation events, evicted history archived with a pointer, and a cold-cache advisor that
  prices re-warming after a TTL lapse (`da:libs/code/deepagents_code/cold_cache.py:801-1137`).
- **Hermes Agent** (`hermes:`). The only harness with a committed compaction recall eval. Lean compaction with recovery beat its larger
  summary policy by 22.5 points at 0.30x the retained tokens (`hermes:evals/compaction/results/SCORECARD-2026-08-15.md:15-52`). Also TTL
  by pacing, slot-keyed cache scopes, cache-parity forks (~26% cost cut) and spill budgets scaled to the window.
- **llama.cpp server** (`lcpp:`). The local runtime. Its prefix, slot and checkpoint rules decide local latency (§4.2).

## 2. Techniques by category, with evidence

Each bullet names the harnesses, the evidence and what Plotroom should do. The CSV holds all 116 rows.

### 2.1 Prompt layout for caching

- **Static first, volatile last, one renderer owns the order.** Qwen Code's typed `SystemPromptLayers` put auto-memory last so a memory
  save invalidates the shortest prefix (`qwen:packages/core/src/core/prompts.ts:813-861`). OpenHands tags every section STATIC or
  DYNAMIC and renders the date last (`oh:openhands-sdk/openhands/sdk/context/prompts/section.py:24-30`). Hermes orders stable → context
  → volatile (`hermes:agent/system_prompt.py:731-803`). Plotroom already has R2/R3; make the tier a type so a volatile field cannot
  compile above BP1 (CL1).
- **Append changes; never edit them in.** Codex WorldState diffs, opencode epochs, ToFu's content-addressed tail blocks with
  "supersedes" versions and tombstones (`tofu:docs/modules/context_engineering.md:38-54`), DeepSeek Harness's in-history system updates,
  pi's section patches (`pi:packages/coding-agent/src/core/system-prompt.ts:199-216`), Kimi Code's change-keyed reminders and Letta's
  memory-update tail all do this. Codex's test states the invariant: request 2 equals request 1 plus the diff items plus the new message
  (`codex:codex-rs/core/tests/suite/prompt_caching.rs:479-602`). Plotroom: conversations and long runs (WC2, LR2).
- **Rebuild the prefix only when the cache is already cold.** Hermes rebuilds at the compaction boundary and defers slash-command
  changes to it (`hermes:AGENTS.md:20-25`); DeepSeek Harness folds appended updates back into the head only when a new request series
  starts; Letta refreshes metadata only after compaction. Plotroom: pack, preset and tool-set edits take effect at the next stage or
  namespace boundary (F2).
- **Golden tests through the real serializer.** goose runs persisted session states through the production projection and five provider
  formats, with a strict relation for implicit caches and a marker-stripped one for explicit caches, and two seeded regressions the
  checker must catch (`goose:crates/goose-provider-types/tests/prefix_invariance.rs:388-428`). ToFu asserts byte identity of the
  translated wire prefix and "representation invariance": a string-to-block flip when a breakpoint attached had "re-billed the cached
  prefix EVERY round" (`tofu:lib/llm/cache.py:274-331`). Plotroom: CL2 and CL3.
- **Breakpoint allocation.** ToFu strips every marker on each request and reserves one for the tools and one for the rolling tail. A
  mid-history "stepping stone" was net negative in a live A/B: dropping it cut floor collapses from ~34% to ~8% of rounds and re-written
  tokens 3.1x over 50 rounds (`tofu:lib/llm/cache.py:97-112`) [V-author]. goose adds a lookback anchor about 20 blocks back for long tool
  loops (`goose:crates/goose-provider-types/src/cache_semantics.rs:53-103`). Steps keep doc 40 §4.1's BP1–BP3; conversations use a
  frozen-prefix marker, a rolling tail marker and, where needed, a lookback anchor.
- **Latch cache-key inputs.** ToFu latches the extended-TTL decision per task so a retry cannot flip it
  (`tofu:lib/tasks_pkg/cache_tracking/_ttl.py:55-95`); Codex pins request effort per context window. Plotroom: add the TTL to doc 40 R4's
  namespace freeze.
- **TTL by pacing.** Hermes' `cache_ttl: auto` gives 1 h to human-paced sessions and 5 min to machine-paced ones. On one install, 63% of
  interactive cache-write tokens were cold re-writes after a 5–60 min gap; 1 h saves ~42% of write cost there but would cost ~49% more on
  subagent and cron traffic (`hermes:agent/prompt_caching.py:114-122`) [V-author]. Plotroom: 1 h for conversations and open proposal
  cards, 5 min for runs scheduled back to back (F5).
- **Uncached one-shots.** pi sends summary calls with caching off and a fresh routing id
  (`pi:packages/coding-agent/src/core/compaction/compaction.ts:641-661`); Strands' page summariser is "deliberately" uncached
  (`strands:harness-py/src/strands_harness/models.py:500-517`); OpenHands V0 turns caching off for condensers. Plotroom: a lone EXPLAIN or
  single text slot carries no breakpoint on write-premium providers (F5).
- **Volatile facts.** pi removed the date from its prompt after it broke the cache every day (CHANGELOG #6621); aider and opencode v1
  still carry it (`aider:aider/coders/base_coder.py:1143-1144`; `oc:packages/opencode/src/session/system.ts:74-85`). Hermes canonicalises
  replayed tool-call JSON and whitespace on the send path so the same row never changes bytes
  (`hermes:agent/turn_request_assembly.py:105-113`).

### 2.2 KV and prefix-cache reuse

- **Keys.** A cache routing key per session or run namespace: Codex, Strands, pi, opencode, kimi-cli, Qwen Code. In opencode issue #51580
  a reporter counted 3.36% misses (23 of 685 requests) for a client without `prompt_cache_key` against 0.30% (2 of 657) for another
  client with it on the same endpoint; two different clients, so the key is the likely but not the only difference [V-author].
  xAI-style caches are slot-keyed: two divergent streams under one key evict each other, so Hermes gives a fork its own key once its stream has diverged
  (`hermes:agent/prompt_cache_scope.py:182-196`). llama-server slots behave the same way (§4.2).
- **Auxiliary calls as prefix extensions.** DeepSeek Harness (summary), Qwen Code (compaction 92.8% cached live; its old cold path
  matched nothing in a mock), Codex remote v2 (the
  normal request plus one trailing trigger item), kimi-cli `/btw`, OpenHands `ask_agent`, Hermes background review (~26% cost cut on
  Sonnet 4.5, `hermes:agent/background_review.py:1001-1012`) and the Letta archive's self-compaction all send the same system prompt,
  tools and history and append one instruction. The Claude Code team's published rule for compaction is the same "cache-safe fork".
  Counter-examples pay uncached input for the whole history: Cline, goose, kimi-cli compaction, Gemini CLI (two cold calls per
  compaction) and OpenHands (+$40 on a benchmark, PR #6597).
- **Forks and siblings.** DeepSeek Harness fork children keep the parent's byte-identical prefix and model; Qwen Code forks must inherit
  the parent model to keep its cache. Qwen's review fan-out read 93.3% of 12.87M input tokens from cache; 8 of 11 first requests raced
  the first cache write, costing ~2% of input (`qwen:docs/design/review-cpu-for-tokens.md:115-134`) [V-author]. Its agents make about 15
  calls each; Plotroom's capsules are mostly single calls, so every fan-out sibling is a first request and doc 40 R9 (warm first) matters
  more for us.
- **Write visibility.** ToFu cites an Anthropic SDK reproducer (anthropic-sdk-python issue #1451, not re-read by us): ~40% misses on
  back-to-back identical prefixes and 0/20 with a 2 s gap. ToFu's own live floor-miss pattern matched that race, so it holds the next
  same-prefix request up to 4 s once the prefix is 30K tokens or more (`tofu:lib/llm_dispatch/cache_settle.py:1-86`) [V-author].
  Doc 40 R9 releases siblings on the first streamed token; make the release point a measured per-provider field (F4).
- **Keep-warm.** pi warms by expected value; aider sends a fixed number of pings every 295 s. Doc 40 R11 already follows pi.
- **Batch.** Qwen Code measured zero cached tokens inside a DashScope batch; at a realtime cached price of 20% of list, batch (50% off)
  loses once the realtime hit rate exceeds 0.625 [V-author]. Doc 40's cost model uses one in-batch hit rate of 0.60 for every provider
  (F10, CM3).
- **Local.** None of the studied harnesses manages llama-server slots or checkpoints: Strands, pi and Letta pass `cache_prompt` or read
  `n_ctx` at most; goose re-prefills every request in its in-process engine. §4.2 covers what Plotroom must own.

### 2.3 Tool schemas and tool lists

- **No tools in Pick and Fill; a fixed, name-sorted set per chat mode** (doc 40 R5): confirmed by opencode, goose, Gemini CLI, Qwen Code
  and DeepSeek Harness ("the tool catalog stays the same across modes for request-cache stability",
  `dsh:packages/bundle/base/cordis.patch.yml:322-336`).
- **Large catalogs are deferred.** ToFu measured 240 MCP schemas at ~55K tokens, a third of a request (`tofu:docs/LLM_COST_OPTIMIZATION.md:11`);
  Anthropic's tool search cut definitions from 77K to 8.7K tokens [V-author]. Bridges exist in Qwen Code (`tool_search` then `tool_call`,
  ~4.2K tokens per request), Codex (BM25), Kimi Code (`select_tools`) and Hermes, whose manifest budget is min(4,000 tokens, 5% of the
  window). Plotroom: plugin catalogs in strong-model chat only; weak models get code-chosen plugin tools per mode.
- **Schema hygiene.** OpenHands minimises schemas to an allowlist of keys and inlines references
  (`oh:openhands-sdk/openhands/sdk/tool/schema.py:71-244`); Codex runs lossy passes above 5,000 bytes; Qwen Code gates prompt text on the
  declared tools: ~276 or ~1,082 tokens per request for trimmed tool sets, zero for a default session, and its design names
  correctness as the part worth paying for (`qwen:docs/design/2026-09-18-resident-tool-prompt-assembly.md:15-18, 123`).
  Rejected: OpenHands' injected `summary` and
  `security_risk` parameters, which cost tokens on every call.
- **Programmatic tool calling and code mode** (Strands, DeepSeek Harness, Codex, goose −31% in one run, opencode, Deep Agents) are outside
  product scope: the agent may not execute code, and weak models must not orchestrate.

### 2.4 Tool output: truncation, elision and receipts

- **Query, don't dump, honestly.** DeepSeek Harness's retention library keeps the first items, counts exactly what it omitted and adds
  guidance supplied by the tool (`dsh:packages/util/output-retention/README.md:28-120`). SWE-agent's search refuses more than 100 hits
  and asks for a narrower query. Deep Agents derives the resume offset from the rows actually rendered after the budget cut, so a re-read
  never skips lines (`da:libs/deepagents/deepagents/middleware/filesystem.py:994-1075`). The SWE-agent paper measured summarised search at
  18.0% resolved against 12.0% for iterative search (2405.15793) [V].
- **A typed result envelope.** ToFu's `ToolResultEnvelopeV2` carries status, summary, up to 64 items, a cursor or recovery handle,
  raw and visible sizes, observation time, world version and an evidence id (`tofu:lib/tasks_pkg/compaction/_budget.py:38-51,
  239-555`). This is the contract Plotroom's query tools and plugin results should follow (TM1).
- **Gate size at production.** Strands' offloader, DeepSeek Harness's spill policy, opencode, Deep Agents, Kimi Code and Letta store
  large results and show a preview plus a reference. Hermes scales the limits to the window: 15% of the window per result and 30% per
  turn (`hermes:tools/budget_config.py:9-114`). Plotroom: the handle points into the journal (doc 12 §5.3 RefStore), never at a file.
- **Fair sharing.** Qwen Code water-fills one budget across a batch of results, keeping small ones whole
  (`qwen:packages/core/src/tools/tool-response-finalizer.ts:157-187`); ToFu shares preview space max-min fairly and drops previews, never
  identities. Plotroom: the same allocator for digest sections.
- **Cuts.** Head plus tail with exact counts, tail-weighted for logs (Gemini CLI 20/80); never cut JSON mid-structure (Strands TS); drop
  whole list elements (OpenHands). Hermes uses one counted marker that says it is not original content, because a bare "...[truncated]"
  was copied by the model into new tool calls and written to disk (`hermes:agent/compression_marker.py:14-75`).
- **Model text separate from display detail.** Qwen Code, kimi-cli (`kcli:src/kimi_cli/soul/message.py:35-77`) and pi return a
  one-line receipt to the model and keep diffs for the UI. Plotroom's typed commands already fit: the model gets ids and counts; the
  glass-box panels read the journal.
- **Unchanged-since receipts.** ToFu replaces a byte-identical re-read with a short receipt while the earlier copy is still visible; in a
  counterfactual replay, 47 repeats fell from 13,553 to 6,619 tokens (−51.16%; `tofu:docs/LLM_COST_OPTIMIZATION.md:73`) [V-author]. Qwen
  Code's read cache had to learn the same lesson: idle masking blanked earlier reads (issue #4239, reported as edits falsely blocked
  as "not read"), and the fix tracks whether a read is still resident and disarms the unchanged fast path for blanked reads
  (`qwen:packages/core/src/tools/read-file.ts:184-193`; `.../microcompaction/microcompact.ts:53-58, 165-171`). The receipt needs the
  same "still resident" flag.
- **Superseded views in batches.** Cline replaces outdated file reads only when 64 KB is reclaimable, "to avoid breaking provider prefix
  caches on every re-read" (`cline:sdk/packages/core/src/session/services/message-builder.ts:37-39`); SWE-agent closes older windows of
  the same file. Plotroom: key on (entity id, revision).

### 2.5 Retrieval instead of stuffing

- **Recovery pointers.** Hermes adds a footer telling the model the compacted messages are searchable and how; the pointer added 20–43
  points of recall in its eval [V-author]. DeepSeek Harness's proposed "recallable compaction" replaces stale history with frozen,
  code-built index stubs plus `history_read` and `history_search`
  (`dsh:.agents/notes/proposed/feature/2026-07-06-recallable-compaction.md:9-108`). Kimi Code, Codex and Strands have similar recovery
  paths. Plotroom's journal is the event store these designs assume; recall is a typed, paginated product query, never a free-text log
  search.
- **Paginated retrieval that cannot recreate the overflow.** Strands caps retrieval at 10,000 tokens and never re-offloads retrieved
  content; its design note warns that "retrieving offloaded content re-creates the overflow", citing another team that disabled its
  retrieval tool for that reason (`strands:team/designs/0015-context-manager.md:28`) [V-author].
- **Code-ranked maps.** aider fits a ranked repo map to a token budget by binary search. Plotroom analogue: a "mission map" digest ranked
  by an entity graph (units, groups, triggers, markers, script globals) personalised by the selection and the request (TM5).
- **Rejected:** embedding retrieval over past turns was ACON's worst baseline on AppWorld (27.4 against 56.0 uncompressed) [V].

### 2.6 History pruning

- **Observation masking** (SWE-agent, Complexity Trap, Gemini CLI, Qwen Code, opencode, OpenHands V0, Strands, ToFu L1) replaces old tool
  results with a one-line stub and keeps actions and reasoning. Measured numbers are in §2.11.
- **Hysteresis.** Prune in batches: `polling` (SWE-agent), condense to half (OpenHands), 64 KB (Cline), 4,096 tokens minimum reclaim plus
  a regrowth runway (Hermes, `hermes:agent/context_compressor.py:3230-3379`), 20K reclaimable beyond 40K (opencode), 5K coalescing
  (Gemini CLI). Anthropic's own `clear_at_least` exists for the same reason: clear only when enough is freed to justify breaking the cache.
- **Cold moments.** ToFu edits nothing cached while the cache is warm; Qwen Code and Hermes also prune after an idle gap. Plotroom:
  prune at a stage boundary or after the provider TTL has lapsed.
- **Legal cut points.** OpenHands derives the indices where events may be removed from pairing, batch and tool-loop properties
  (`oh:openhands-sdk/openhands/sdk/context/view/manipulation_indices.py:6-52`); DeepSeek Harness snaps cuts to balanced tool pairs.
- **Non-destructive views.** OpenHands, DeepSeek Harness, Cline, Deep Agents, pi and goose keep the full log and derive the model's view
  from recorded prune events. Plotroom's journal already works this way.
- **Rejected:** per-turn sliding windows (OpenHands V0 RecentEvents, Strands' 40-message window) move the rewrite point on every turn,
  and model-initiated rollback (kimi-cli D-Mail) hides facts in a model-written note.

### 2.7 Reasoning and output budgets

- **Clamp output to what the window has left, keeping an answer floor**: ToFu (input × 1.10 + 512 + completion ≤ window, floor 1,024),
  Qwen Code, kimi-cli, Cline, OpenHands, pi (`MIN_ANSWER_TOKENS` 1,024) and goose. kimi-cli has a test proving that the summary cap plus
  the next request fits an 8,192-token window.
- **A reply cut by the limit is never executed** (Strands, pi, DeepSeek Harness), as doc 21 §8.2 and doc 40 R8 already say.
- **Auxiliary calls with thinking off** (DeepSeek Harness, Strands, Qwen Code), but with a floor: Cline's hard-coded thinking-off returned
  HTTP 400 where reasoning is mandatory (#14551), and Hermes steps up to its route's lowest level and remembers it
  (`hermes:agent/auxiliary_reasoning_floor.py:1-15`).
- **Reasoning replay is per model.** DeepSeek V4 in thinking mode returns HTTP 400 when its reasoning is emptied
  (`tofu:lib/tasks_pkg/compaction/_builtin_steps/_thinking.py:18-66`). This belongs in doc 55's preset data; capsules never replay
  reasoning.

### 2.8 Cost accounting

- **Buckets.** Uncached input, cache read, cache write and output, with reasoning inside output and failed attempts billed (DeepSeek
  Harness `dsh:packages/llm/token-meter/src/usage-projection.ts:14-150`, goose, Codex). aider's Gemini benchmark was reported at $6.32 and
  re-run at ~$37 because reasoning tokens were not counted (~6x) [V-author].
- **Overhead is its own bucket** (pi's "Tools/summaries", goose's `is_compaction`, OpenHands' per-role usage ids, Gemini CLI's
  `LlmRole`). In the Complexity Trap, summary calls were 2.86–7.2% of instance cost [V].
- **Name the miss.** ToFu compares cache reads and writes round to round and names the cause in order of precedence: client change (system
  prompt, tool, model), prefix-byte mutation with the field list, TTL expiry, namespace or routing switch, upstream eviction
  (`tofu:lib/tasks_pkg/cache_tracking/_detect.py:45-300`). pi adds a 1,024-token noise floor and counts misses only once a provider has
  ever reported cache activity (`pi:packages/coding-agent/src/core/cache-stats.ts:4-174`). ToFu saw two adjacent rounds with nearly
  equal input differ 5.95x in price at 19% versus 97% cache read [V-author].
- **Tell the user before paying.** Deep Agents prices re-warming after a TTL lapse and opens a modal above $0.50; Kimi Code shows a
  "cache expired" dialog. opencode #51109: 12 cold resumes of a ~440K context were 51% of one session's cost [V-author].
- **Honest estimates.** Mark estimates as estimates and unknown prices as unknown (goose `CostSource`, ToFu, mini-swe-agent). chars/4
  undercounted CJK tool output by 39–54% (Qwen Code), tiktoken counted Claude input at 0.66x (ToFu), and Cline overestimated base64 images
  ~25x (#14512) [V-author]. Codex issue #45074 reports a 235K gap between estimated and server counts (user report).
- **Manifests.** ToFu records each request's blocks, tokens, hashes and suppression reasons
  (`tofu:lib/tasks_pkg/context_composer/_render.py:59-249`); Qwen Code measures "idle cost" (input tokens of a session that asks one question) because a percentage of window
  means nothing across 8K and 1M windows. DeepSeek Harness requires every package README to state what the model sees and its token and
  cache effect, checked by CI.

### 2.9 Sub-agents and forks

Every harness with sub-agents gives the child a fresh context and returns only its final answer; Anthropic reports multi-agent systems at
~15x chat tokens [V-author]. Two details matter for Plotroom: Hermes budgets a child's result from the parent's last measured prompt,
after budgeting from the session sum collapsed 1,393 summaries to the floor (`hermes:tools/delegate_tool_results.py:158-285`), and forks
that must share a cache keep the model and prefix identical (§2.2). Model-chosen delegation and LLM routers (Strands' classifier router,
OpenHands' `ask_oracle`) stay rejected (doc 40 §8).

### 2.10 What the wider literature adds

- **Small, focused contexts are also more accurate.** Input length alone lowered accuracy by 13.9–85% even with perfect retrieval
  (2510.05381); in NoLiMa, 11 of 13 models claiming at least 128K fell below half their short-context score at 32K (2502.05167); RULER
  found about half of 17 models holding up at 32K (2404.06654) [V]. Capsules of 1–4K tokens sit on the right side of every curve, which
  matters most for small local models [I].
- **Fewer tools for small models.** LongFuncEval measured −7% to −85% as the tool catalog grows (2505.10570); a quantised Llama 3.1 8B
  failed with 46 tools and succeeded with 19 (Less is More, 2411.15399) [V]. This supports doc 40 R5's fixed small tool set per mode.
- **Recaps beat long chats.** The same information spread over turns cost 39% on average; restating it in a final turn recovered about
  half of the loss (GPT-4o-mini 50.4 → 66.5 against 86.8 fully specified; GPT-4o 59.1 → 76.6 against 93.0), and the authors call the
  recap an unrealistic setting because the last turn is not known in advance (2505.06120, Table 2) [V]. This is outside support for
  a fresh capsule per decision and a code-built recap when a conversation resets.
- **Memory is context management.** A file-backed agent scored 74.0% on LoCoMo against 68.5% for a dedicated memory layer, and Letta
  concludes that how the agent manages context matters more than the retrieval mechanism [V-author]; MemGPT (2310.08560) and Mem0
  (2504.19413) are the reference designs. Plotroom's typed document and journal play this role exactly.
- **Idle time is cheap locally.** Sleep-time compute needed about 5x less test-time compute for equal accuracy by precomputing while idle
  (2504.13171) [V]. On the local tier, code can precompute menus, digests and next-stage capsules during the user's think time and splice
  them only if the journal revision is unchanged (the pattern of Gemini CLI's background snapshot inbox) [I].
- **Caching done right is the biggest single cloud lever.** Strategic cache blocks cut API cost 41–80% in "Don't Break the Cache"
  (2601.06007), already cited by doc 40 [V].

### 2.11 Measured effects

Everything here is the publisher's own measurement unless marked. None was measured on Plotroom-sized capsules.

| Effect | Number | Source | Caveat |
| --- | --- | --- | --- |
| ToFu vs Claude Code, SWE-bench Verified | −28.4% tokens (mean of −20.8%, −43.6%, −20.8%); on Opus 4.6 ToFu cost +3.2% per instance | arXiv 2607.11423 Table 1 | no Claude Code version, no layer ablation, "tokens" undefined for cached input; read from HTML |
| Strands Harness vs other harnesses | ~28% lower token cost; `auto` context manager −55% cost, 68% → 98% accuracy | Strands blogs 2026-09-21, 2026-06-18 | no benchmark names, n or model |
| Observation masking vs raw agent (Gemini 2.5 Flash) | $0.415 → $0.177 (−57%), 32.8% → 35.6% solved; LLM summary $0.242, 36.0% | 2508.21433; `ctrap:auxiliary-data/bootstrapped_cis.csv` | SWE-agent scaffold; OpenHands needed a window of 58, not 10; with thinking on, masking solved 36.4% against 40.4% raw (same CSV) |
| Masking + summary hybrid | 7% cheaper than masking, 11% cheaper than summary | 2508.21433 §5.3 | one model, Verified-50 |
| Summary lengthens runs | +13–15% turns | 2508.21433 §4.4 | — |
| Hermes lean + recovery | 68.3% recall at ~49K vs 45.8% at ~162K; pointer +20–43 points; anchor index 23.3% → 60.0% | `hermes:evals/compaction/results/SCORECARD-2026-08-15.md:15-52` | 4 transcripts, 15 questions each, ±3.3 points noise; two of the four "current" scores come from earlier question banks |
| Compaction via the main prefix | 92.82% cached; the old cold path matched 0 in a mock | `qwen:docs/design/chat-compression-cache-sharing.md:69-83` | one-off live validation on DashScope; the 0 is from a deterministic mock, not the live run |
| Cache-parity forks | ~26% end-to-end cost cut | `hermes:agent/background_review.py:1001-1010` | code comment citing an issue |
| Unchanged receipts | −51.16% on 47 repeats | `tofu:docs/LLM_COST_OPTIMIZATION.md:73` | counterfactual replay |
| No stepping-stone breakpoint | re-written tokens 943K → 306K over 50 rounds | `tofu:lib/llm/cache.py:97-112` | 3 conversations |
| Summarising condenser | +$40 on a SWE-bench Verified run through lower cache use; 200 vs 203 solved | OpenHands PR #6597 | 2025 |
| Summary quality | artifact trail 2.19–2.45 of 5 for every method; overall 3.35–3.70 | Factory probe evaluation (36,611 messages) | vendor's own method wins |
| Context collapse on rewrite | 18,282 → 122 tokens; accuracy 66.7 → 57.1 (no adaptation: 63.7) | ACE, 2510.04618 | AppWorld |
| Constraint retention by compactors | 17% on average; constraint-aware extractor > 90% | COMPINT, 2608.11242 | — |
| Multi-turn degradation | −39% average; a final recap turn 50.4% → 66.5% (fully specified 86.8%) | 2505.06120 Table 2 | recap figures for GPT-4o-mini on four tasks; GPT-4o 59.1 → 76.6 (93.0) |
| Context editing (Anthropic) | +29% (editing), +39% (with memory); −84% tokens on a 100-turn eval | Anthropic, 2025-09-29 | internal evals |
| ACON | −26% to −54% peak tokens; latency 73 s → 88–102 s per task | 2510.00615 | cost table excludes caching |
| Code mode (goose) | 23,339 vs 33,648 tokens (−31%) | goose blog | one run |
| Cold resumes | 12 resumes = 51% of a session's cost | opencode #51109 | reporter figure |
| Compaction thrash | 21 of 24 compactions cancelled, ~160K tokens each | Kimi Code #2720 | — |
| Prune-reread loop | ~23.4M tokens, zero edits | Cline #14328 | stale credentials caused it |
| Local prefix reuse (ours) | identical prompts: all but 4 tokens reused; permuted Pick samples: 58 of ~300 | `tools/local-qual` records, §4.2 | one model, one GPU, not committed |

## 3. Compaction and summaries

### 3.1 Where Plotroom needs compaction, and where it does not [I]

| Area | Does history grow? | What Plotroom does instead | What remains to design |
| --- | --- | --- | --- |
| Steps | No: one fresh capsule per decision (doc 21 §8.1) | Count before sending; shrink the digest by relevance rank or refuse; never drop the verbatim request | Nothing new; overflow is a capsule-budget bug (CL6) |
| Long runs | The journal grows; prompts do not | Stage prefixes shared; each decision rebuilt from the document and journal; children fresh | Code-built stage-handoff digests (LR1); recall by journal query (LR3) |
| Journal | Yes, on disk | Folded record per attempt; never sent whole | Context receipts for prunes (JL2) |
| Conversations | Yes | Append-only, fixed tool set, masking at phase boundaries (doc 40 R16) | The policy in §3.6: triggers, masking pipeline, Session Digest, optional narrative |

What the studied harnesses spend compaction code on, and what Plotroom gets for free: history growth (a fresh capsule instead);
summary drift and summaries of summaries (no summaries of facts); a lost artifact trail (typed commands in the journal); estimator error
on growing histories (exact counts of small capsules, `/tokenize` locally); tool-schema overhead in decisions (no tools in Pick and
Fill); and resume costs (sessions resume from the document, doc 21 §8.2).

### 3.2 Triggers, and what breaks at 8K

Numbers at an 8,192-token served window are our arithmetic from each harness's constants [I on V].

| Harness | Trigger | At W = 8,192 |
| --- | --- | --- |
| ToFu | min(0.9 × usable, working set); usable = W − 128K − 8K, floored at 70% of W | usable 5,734; trigger ~5,161 |
| Strands | 0.7 × window before every call (conversation managers); 0.85 in the `auto` context manager | its llama.cpp model has no window table and assumes 200,000, so proactive compression never fires |
| DeepSeek Harness | ⌊min(0.8W, W − O − 65,536)⌋ | negative: a per-target error; the automatic listener warns and skips |
| pi | context > W − 16,384; keep 20,000 | threshold −8,192, so every turn qualifies, but the 20,000-token keep exceeds the window and the cut finds little or nothing to summarise (`pi:packages/agent/src/harness/compaction/compaction.ts:370-398`); pico3's collapse threshold is a separate setting whose default 0 means off at any window (`pi:packages/agent/src/harness/pico3/kinds/collapse.ts:56`, `.../generation.ts:598`) |
| Codex | 90% of W; user messages kept up to 20,000 tokens | trigger 7,373, but the retention budget exceeds the window |
| opencode | usable = input − min(20K, maxOutput); v2 buffer max(maxOutput, 20K) | ≤ 0 when maxOutput ≥ 8,192 |
| Qwen Code | min(0.85W, W − 20K − 13K) with a proportional fallback | auto ~6,963; warn 0; hard 8,192; a few hundred tokens left for the summary |
| Gemini CLI | 0.5 × W | 4,096 |
| Kimi Code | ≥ 0.85W or used + 50K (reserve ignored when ≥ W) | 6,963 |
| kimi-cli | ≥ 0.85W or tokens + 50,000 ≥ W | fires on every step |
| Letta Code | W − min(16,384, 0.2W) | 6,554 |
| goose | 0.8 × W | 6,554; skips its turn-context block below 32K |
| Cline | 0.9 × input budget (budget 0.9W when only W is known) | ~6,636; target ~4,645 |
| Deep Agents | 0.85 × W, keep 10% | 6,963 |
| Hermes | 50% of (W − O), floor 75% under 512K; 10K lean-tail floor | the tail floor was 122% of W until capped at 20% (`hermes:agent/context_compressor.py:959-965`); tool use refused under 64K |
| OpenHands SDK | tokens or events | refuses windows under 16,384 unless an environment flag is set |
| aider | history > W/16, clamped to 1K–8K | 1,024 |

Rules we draw [I]: (1) express every threshold as a fraction of the **served per-slot** window, with an absolute output-plus-thinking
reserve subtracted first; (2) keep the values in the model preset (D048), not in code; (3) have the definition compiler reject a step or
chat mode whose fixed part cannot fit the smallest qualified window (doc 51 V11); (4) anchor the size on the last provider-reported usage
plus an estimate of what was appended since (pi, ToFu, kimi-cli, Codex, goose, DeepSeek Harness), and count exactly where possible; (5)
retry an overflow once, only if the request shrank (DeepSeek Harness, Strands, Cline); (6) stop after two ineffective prunes, judged by
real usage (Hermes, Qwen Code); (7) prune only if it pays back within the observed prefix lifetime (ToFu).

### 3.3 Methods compared

| Method | Who | Evidence | Cost | Verdict for Plotroom |
| --- | --- | --- | --- | --- |
| Observation masking (stub per old tool result) | SWE-agent, Complexity Trap, Gemini CLI, Qwen Code, opencode, OpenHands V0, Strands, ToFu L1 | halves cost at an equal solve rate (2508.21433) | no model call; one cache miss per prune | ADOPT for conversations, batched |
| Reversible offload with handles | Manus, Strands, DeepSeek Harness, Deep Agents, Hermes; DTOC paper | DTOC: input −10–13%, 3–3.5x cheaper per solved task for the models that benefited; "reversibility is critical" (2609.26121); Hermes pointer +20–43 points | handle plus query tool | ADOPT with journal handles |
| Structured state from code | ToFu `TaskStateSnapshotV1`, Gemini CLI recap, Hermes anchor index and fallback, Cline basic, kimi-cli task snapshot | Hermes anchor index 23.3% → 60.0%; Context Compaction Theory: sets survive only outside summaries | none | ADOPT as the primary method |
| LLM summary, fixed sections | DeepSeek Harness, pi, opencode, Codex, OpenHands, Qwen Code, goose, Letta, Deep Agents, aider, Gemini CLI | artifact trail 2.19–2.45/5; +13–15% turns; 2.86–7.2% of cost; collapse on rewrite (ACE); output and retained information "fluctuate substantially from run to run" (2605.23296) | one call; cold unless forked | Narrative fields only, forked and validated |
| Provider-native compaction | Anthropic, OpenAI, xAI; Codex v2, Hermes | Factory: 3.44 and 3.35 of 5 | provider-specific, opaque or signed | REJECT (glass box, local) |
| Model-managed context | Strands agentic mode, kimi-cli D-Mail, OpenHands `request_condensation`, Codex notes, SelfCompact (2606.23525) | gains reported for strong models | model spends tokens deciding | REJECT (weak-model invariant) |
| LLM ranking or distillation of history | OpenHands attention condenser, ACON, Gemini CLI distillation | ACON retrieval 27.4 and LLMLingua 39.3 vs 56.0 | extra call per step | REJECT |

### 3.4 What must survive verbatim

The union across harnesses, mapped to Plotroom's records [I on V]:

- **The system prefix and tool set**, never compacted (all).
- **The first request as an objective anchor**, re-inserted verbatim at a fixed position (ToFu `_anchor.py:32-87`, OpenHands
  `keep_first`, Strands' first user message).
- **Every user message within a budget, newest first** (Codex 20,000 tokens, ToFu 4,096 tokens or 8 messages, Hermes 24,000 chars, Kimi
  Code 18K tail plus 2K head chosen by typed origin). COMPINT found that compactors keep 17% of session constraints; a constraint-aware
  extractor kept over 90% (2608.11242) [V].
- **The in-flight turn and the newest complete tool round**, with call and result pairs together (ToFu, DeepSeek Harness, OpenHands).
- **Exact identifiers harvested by code** (Hermes anchor index; pi's cumulative read and modified file lists; ToFu evidence ids).
- **Pinned items with their tool-pair partners** (Strands `pin_message.py:22-107`).
- **Live state re-rendered by code after the prune**, never trusted to the summary: plan and todos (Kimi Code, Qwen Code, Hermes, Strands),
  background tasks (kimi-cli), recently touched files re-read fresh (Qwen Code).
- **The latest assistant answer** (Cline, Hermes).

Plotroom mapping: user messages and pinned or human-edited constraints from the session log; entity tokens and journal ids from typed
records; plan card and workflow position from the state machine; last validation from the validator; lookup handles for everything
else.

### 3.5 Failure modes seen in the field

- **Summaries of summaries lose detail.** OpenHands feeds its summariser `str(event)`, clipped to 500 chars, so a prior summary longer
  than that is cut before it is summarised again (`oh:openhands-sdk/openhands/sdk/event/base.py:17, 82-105`) [V code reading]. ACE
  measured collapse on rewrite. In the Complexity Trap code, static checkpointing appears to fall back to all accumulated summaries on
  non-trigger steps [I, code reading].
- **The summary call misses the cache.** Cline's docs promise cache reuse that its code does not do; goose, kimi-cli and Gemini CLI send
  new system prompts; OpenHands paid $40 more on a benchmark run.
- **Thrash.** Kimi Code #2720 (21 of 24 compactions cancelled); Cline #14328 (a 401 made every agentic compaction fall back to basic,
  the model re-read files, the threshold was hit again: ~23.4M tokens, no edits); opencode #47485 (each compaction was a 45–85K-token
  summary call that left a 22–42K context, and the agent then re-read the files it had lost, one of them 66 times).
- **Wrong counts.** Base64 images counted as text (~25x high, Cline #14512); CJK undercounted 39–54% (Qwen Code); a 235K estimate gap
  (Codex #45074); reasoning tokens missing from cost (aider, ~6x).
- **Small-window breakage.** The absolute defaults in §3.2.
- **Imitation.** After compaction a small model wrote `[Assistant tool call]: ...` lines as text instead of calling tools (opencode
  #50814); a model copied a bare truncation marker into tool arguments (Hermes).
- **Silent fallbacks.** A sliding-window mode wiped the whole context and a custom prompt was replaced by the default one (Letta #3270,
  letta-code #3954).
- **Thinking eats the summary.** Reasoning models used the 4,096-token cap and returned no summary (Cline raised it to 8,192); forcing
  thinking off returned HTTP 400 on mandatory-reasoning routes (Cline #14551).
- **Stale read records.** Idle masking blanked earlier file reads while the read cache still counted them; the fix added a residency
  flag that also disarms "unchanged" placeholders for blanked reads (Qwen Code #4239, §2.4).
- **Goal and todo loss.** opencode keeps todos in a table and never re-injects them; Hermes and Kimi Code re-render them by code.
- **Reasoning replay.** DeepSeek V4 thinking mode rejects emptied reasoning (ToFu).

### 3.6 Recommendation: Plotroom's context policy (proposal) [I]

**Steps.** No change: a fresh capsule, counted before sending, shrunk by relevance rank or refused; the verbatim request is never
dropped. Every auxiliary call for the same decision (K samples, repairs, EXPLAIN) extends the capsule's exact bytes at the tail (CL4).

**Long runs.** Never compact. Stage handoffs use a code-built digest from the journal and document; children are fresh capsules that
return typed results; recall is a journal query. Rebuild prefixes only at stage boundaries.

**Conversations.** A ladder, cheapest first; each rung is code-owned and records a journal receipt:

1. **Render deterministically.** Append-only history; fixed tool set per mode; per-result caps at render time from the window fraction;
   typed result envelopes; state changes (selection, mode, enabled plugins) appended as deltas; "unchanged since revision N" receipts.
2. **Mask in batches at cold moments.** When the ledger shows the prefix is already cold (TTL lapsed, stage boundary, model change) or
   the conversation reaches its fraction threshold, and the reclaimable tokens pay back one cold miss (§3.2 rule 7): replace old tool
   results by retention class (keep validator findings and pinned items; mask listings; supersede older entity views) with one-line
   typed stubs carrying entity tokens, shown/total and a journal handle. Drop whole turns only at legal cut points.
3. **Reset to a Session Digest.** If still over budget, start a new window from a code-built digest plus the newest turns verbatim plus
   every user message within its budget, newest first. The old window stays in the journal, reachable by handles.
4. **Optional narrative fields.** Only with a qualified preset and never on the 8K local tier by default. A cheap-role call, forked from
   the conversation's own cached prefix with one trailing instruction, returns a JSON delta patch (Gemini CLI's snapshot-generator shape)
   for two fields only: the conversation's goal in one sentence and open questions. Code applies the patch, enforces a budget and shows
   the result as editable chips; a stated preference becomes a pinned constraint only when the user confirms it (the editable chips of
   doc 21 §4.2 and §11.3). Admission fails closed on a cap stop, empty output or a tool call, and when the result is not smaller than
   what it replaces
   (DeepSeek Harness's shrink guard).

The Session Digest has fixed headings, in a fixed order, with "(none)" kept so its byte shape is stable (DeepSeek Harness's rule). Code
fills every field except those marked:

```text
Session digest (code-built; journal rev <r>)
Goal            first request, verbatim; latest request, verbatim; [narrative: one-sentence goal]
User constraints verbatim quotes with journal ids; pinned and human-edited items
Decisions       accepted and rejected proposals: journal id, entity tokens, one line each
Entities touched entity token @ revision, newest first, within budget (+N more: handle)
Open findings   validator codes and entity tokens
Where we are    workflow and step, or "free chat"; plan card state
Open questions  [narrative]; unanswered questions the user asked
Lookup          handles: journal.find, mission.get, catalog.search
```

Validators: every must-keep item (user messages within budget, pinned items, open findings) appears; every entity token resolves; the
digest fits its budget; nothing call-shaped appears (opencode #50814); markers are non-imitable (Hermes). Internal notes are English with
exact literals; user-facing mission text keeps its language and codepage (DeepSeek Harness). This extends doc 21 §8.1 and doc 40 R16;
TE-G2 records the one doctrinal question (the narrative fields).

## 4. Caching

### 4.1 Cloud prompt caches: rules learned

Doc 40 §2 and R2–R17 stay the base. New or sharper rules [I on V]:

- **C1. Auxiliary calls fork the cache.** Same system prompt, tools, model, effort and schema, plus a trailing item (§2.2). A different
  summariser prompt pays the whole history uncached.
- **C2. One-shot prefixes go uncached** on write-premium providers (pi, Strands, OpenHands V0).
- **C3. Strip and re-place markers on every request; reserve slots for the tools and the tail; no mid-history stepping stones** (ToFu).
  For long tool loops in conversations, add a lookback anchor about 20 blocks back (goose).
- **C4. A marker never changes a message's representation** (ToFu), and the golden test runs through the production serializer (goose).
- **C5. Latch cache-key inputs per namespace, including the TTL** (ToFu, Codex).
- **C6. TTL by pacing:** 1 h for human-paced conversations and open cards, 5 min for runs (Hermes' measurements).
- **C7. The sibling release point is a measured per-provider field** (first token or stream end plus a settle window; ToFu).
- **C8. Cache semantics are data per (provider, model):** explicit breakpoints, implicit tolerant, implicit strict (the default for
  unknowns), uncached (goose). Explicit markers can disable implicit caching on some models (OpenHands' unsourced Gemini note). Proxy
  routes and SDKs can drop markers silently: Claude over an OpenAI-compatible route got no markers in opencode v2 (#51557), and the AI
  SDK drops `cache_control` on Bedrock, so Cline sends Bedrock's own `cachePoint` block
  (`cline:sdk/packages/llms/src/providers/routing/bedrock-cache-point.ts:9-27`; CLI changelog 3.0.50, "Bedrock prompt caching works
  again").
- **C9. Slot-keyed caches need a fork key after divergence** (Hermes, xAI).
- **C10. Declare a placeholder deferred tool from the first request** when plugin tools may be deferred (pi).
- **C11. Every miss gets a named cause in the ledger** (ToFu, pi, Kimi Code).
- **C12. Batch discounts are compared with the realtime hit rate per provider** (Qwen Code's DashScope measurement).

### 4.2 llama-server: how reuse works, and what our records show

**Mechanics** (`lcpp:` at `4da6337`) [V]:

- `cache_prompt` defaults to on; the reused part is the longest common prefix of tokens
  (`lcpp:tools/server/server-context.cpp:3228-3230`). The README warns logits are not bit-identical across batch sizes (`lcpp:tools/server/README.md:587`), so replays come
  from the journal.
- A request goes to the idle slot with the highest LCP fraction above `--slot-prompt-similarity` (default 0.10), unless `id_slot` pins
  it (`lcpp:tools/server/server-context.cpp:1571-1615`).
- `--cache-ram` (default 8,192 MiB) keeps prompt states in host RAM, and `--cache-idle-slots` (default on) saves idle slots into it; a
  new request can restore the best-matching saved prompt (`lcpp:common/common.h:629-633`; `lcpp:tools/server/README.md:167-169`).
- A prompt at or above the slot's context is rejected ("exceeds the available context size"), never truncated
  (`lcpp:tools/server/server-context.cpp:3218-3225`). Context shift is off by default; `--cache-reuse` (KV shifting of chunks) is off
  by default and only approximates a fresh prefill [I].
- **Checkpoints.** When the model's memory cannot be partially rolled back (recurrent or hybrid layers) or uses sliding-window attention
  without `--swa-full`, the server keeps up to 32 "context checkpoints" per slot (`lcpp:tools/server/server-context.cpp:3471-3484`;
  `lcpp:common/common.h:630`). Prompt processing breaks, and checkpoints are made, at the start of the last user message, at a user
  message when the slot has no checkpoint yet, at user messages more than `--checkpoint-min-step` (8,192) tokens past the previous
  checkpoint, and 4 and 4 + n_ubatch tokens before the prompt end (`:3531-3600`). When a common prefix ends between checkpoints, the
  server restores the nearest earlier one or re-processes the whole prompt ("likely due to SWA or hybrid/recurrent memory", `:3360-3395`),
  and drops the checkpoints past the restore point (`:3402-3408`). The list therefore stays short, and the oldest checkpoint (the end of
  the system message) survives a sequence of decisions on one slot unless the list fills (`:2325-2350`) [I on V].

**What our records show** [V data; I interpretation]. The 2026-09-28 `tools/local-qual` runs of Qwen3.5-4B Q4_K_M (a hybrid of Gated
DeltaNet and gated attention, doc 14 §3.2) on llama.cpp b11146 with Vulkan, 4 slots and an 8,192-token context store `timings.cache_n` per
call. A throwaway script aggregated them:

| Suite (condition) | Calls | Mean prompt tokens | Cached share | Most common `cache_n` | Reading |
| --- | --- | --- | --- | --- | --- |
| fill (none) | 72 | 433 | 83% | prompt − 4 (60 calls) | identical prompts repeat across sample rounds; restored from the checkpoint 4 tokens before the end |
| pick-hard (none) | 452 | 302 | 20% | 58 (449 calls) | only the system message is reused; request and permuted menu share one user message |
| pick-hard (cards) | 282 | 442 | 13% | 58 (282 calls) | the ~140-token card sits in the user message and is re-processed on every call |

Fill prefill time fell from 1.55–2.31 s cold to 0.11–0.41 s warm for ~466-token prompts. In one pick-hard run of 90 calls (median prompt
298 tokens) the median prompt time was 1.19 s and the median latency 1.8 s. The runner loops samples outside items (`tools/local-qual/run.py:440-441`), so the same item's earlier sample could only
come back from the host-RAM cache; the Fill rows show that path works. On a full-attention model the restored state would have been
reused up to the end of the shared request text; on this hybrid model reuse stopped at the only user-message boundary [I]. A paired run
with the split layout below, or with a full-attention model, would confirm it (E13, §5.8).

**What it costs** [I]. At the 215–337 tokens/s measured for uncached prompt parts on the test GPU (`tools/local-qual/README.md:240-243`),
re-processing a ~900-token request-plus-digest part costs 2.7–4.2 s per extra sample, so a K = 3 Pick loses 5–8 s. Losing a 1,230-token
stage prefix (doc 40 §1.1) between decisions would cost 3.7–5.7 s per decision.

**Memory** [I]. KV bytes per token = 2 × attention layers × KV heads × head dimension × bytes per element. For a dense Qwen3-4B-class
model (36 layers, 8 KV heads, head dimension 128, f16) that is 144 KiB per token: a 3,000-token prefix is ~420 MiB, and the default 8 GiB
`--cache-ram` holds about 19 of them; q8_0 KV halves this. Hybrid models store KV only for their attention layers but add recurrent state
to each checkpoint [U per model].

### 4.3 The capsule layout that maximises hits (fold into doc 40 §4.1) [I]

Doc 40 §4.1 fixes the order. This adds message boundaries, so the same layout works for cloud breakpoints and for llama-server
checkpoints on hybrid and sliding-window models:

```text
tools        none for Pick, Fill and text slots; a fixed, name-sorted set per chat mode
system msg   frozen stage prefix per (stage x DecisionKind x pack version x model setup)
             doctrine -> core + lens -> code-picked cards -> frozen exemplars -> shape rules -> schema text
  == BP1     cloud: cache_control / prompt_cache_breakpoint | local: checkpoint at the first user-message start
user msg 1   run and decision part: verbatim request -> code-built digest (quoted, untrusted) -> "+N more" handles
  == BP2/BP3 cloud: only when K >= 2, a repair or an EXPLAIN is likely
assistant    fixed acknowledgement, byte-stable per pack version ("Ready.")
user msg 2   sample tail: permuted menu or slot spec -> variant note -> schema restated
             repair: this sample's answer as an assistant message, then a user message with the finding (appended, never rebuilt)
             EXPLAIN of an admitted decision: its answer, then the explain instruction (appended)
  == local   checkpoint at the last user-message start: user msg 1 is reused by every sample, repair and EXPLAIN of the decision
format       one frozen schema per DecisionKind
```

On a full-attention model (and on cloud providers) the extra messages change nothing: the longest common prefix is reused either way. On
hybrid or SWA models they are what lets samples, repairs and EXPLAIN reuse the digest [I]. Two things need measuring before adoption (E13,
TE-G1): whether the fixed acknowledgement changes small models' admit rates, and whether each qualified chat template renders it byte-stably
with thinking off. Doc 51 V10 currently makes every repair a fresh single-turn capsule; on hybrid models that reuses only the system
message, so the appended repair above is also a proposal to amend V10 (§6.3). V10's reason, templates that reject adjacent user
messages, does not arise here: the layout alternates user and assistant strictly, which the template test in CL5 should also assert.
Fallbacks where the acknowledgement hurts: `--swa-full` for
SWA models when VRAM allows, or accept the re-prefill and rely on adaptive K (doc 40 R7).

## 5. Concrete changes for Plotroom

All proposals [I]. Each change is test-first (AGENTS.md): the test named in the third column is written before the change and must fail
on the old behaviour.

### 5.1 Capsule layout and rendering

| # | Change | Proof (write first) | From |
| --- | --- | --- | --- |
| CL1 | Capsule sections carry a type-level volatility tier (stage, run, decision, sample) and the renderer returns breakpoint offsets | the stage-prefix builder's API accepts only stage-tier section types (enforced by the type system, not by a `compile_fail` doctest, which AGENTS.md bans); a unit test and a snapshot of breakpoint offsets per DecisionKind | OpenHands, Hermes, ToFu |
| CL2 | Golden prefix test through every provider dialect's serializer and through the llama.cpp chat template (llama-server's `POST /apply-template` in an opt-in local test, or the GGUF template rendered offline) | synthetic fixtures; bytes up to each breakpoint identical across decisions, runs and machines; seeded regressions (timestamp in the system message, digest moved above BP1) must make the test fail | goose, ToFu, Codex |
| CL3 | Representation invariance: a marker adds or removes only its key | serialize each capsule with and without markers, strip markers, compare bytes | ToFu |
| CL4 | Auxiliary calls (K samples, repairs, EXPLAIN) append to the decision's exact capsule bytes | test that each auxiliary request starts with the base request's bytes; cassette test that the provider reports cached tokens | DeepSeek Harness, Qwen Code |
| CL5 | Message split of §4.3 behind a preset field until E13 decides | template test: each qualified GGUF template renders the acknowledgement identically across calls and accepts the strict user/assistant alternation (including an appended repair); E13 local run | llama.cpp checkpoints |
| CL6 | Capsule manifest: block ids, tokens, hashes, suppression reasons (closed enum) | manifest token sum equals the counted capsule; suppression reasons round-trip | ToFu, Deep Agents |
| CL7 | Prompt lints: no action, tool or card named that the step does not offer; no call-shaped digest lines; no uncounted elision markers | lint fixtures with one violation each | Qwen Code, opencode, Hermes |

### 5.2 Tool and menu rendering

| # | Change | Proof (write first) | From |
| --- | --- | --- | --- |
| TM1 | Typed result envelope for every Wilco query tool and plugin result: shown/total, cursor from rendered rows, document revision, evidence id (journal ref), exact omitted count, narrowing hint named by the tool; "empty" distinct from "cut by budget" | property tests: shown + omitted = total; the cursor resumes at the first unrendered row; empty and cut produce different statuses | ToFu, DeepSeek Harness, Deep Agents |
| TM2 | Result caps from the served window (a fraction per tier, about 1–1.5K tokens at 8K) and max-min fair sharing across results | a fixture with one large and three small results: small ones intact, large one previewed, no entity token dropped | Hermes, Qwen Code, ToFu |
| TM3 | Cuts never split JSON or a row; one counted, non-imitable marker; a validator rejects answers that echo it | truncation fixtures; a scripted model echoing the marker is refused | Strands, Hermes |
| TM4 | "Unchanged since revision N" receipt keyed on (tool, arguments, revision), only while the earlier copy is unmasked; block after two repeats | masking the earlier copy re-enables the full result (the Qwen Code #4239 case) | ToFu, Qwen Code, Hermes |
| TM5 | Mission map digest: entity graph ranked by selection and request, fitted to the budget by binary search with deterministic tie-breaks | golden digest bytes for a synthetic mission; fitting stays within 15% under budget | aider |

### 5.3 Journal and ledger

| # | Change | Proof (write first) | From |
| --- | --- | --- | --- |
| JL1 | Ledger per attempt: four disjoint buckets, reasoning inside output, `cost_source` (provider, estimated, unknown), cache namespace, prefix hash, schema hash, role (decision, repair, mask, digest, title, warm ping) | cassettes from each adapter map to the buckets; an unpriced model shows "unknown", never $0 | DeepSeek Harness, goose, Kimi Code |
| JL2 | Context receipt for every prune, mask, digest regeneration and window reset: what was shadowed (journal ids), tokens before and after, cache cost, reason | replay rebuilds the exact request bytes from receipts; receipts never enter model context | ToFu, DeepSeek Harness, OpenHands |
| JL3 | Miss classifier: client byte change, TTL expired, below minimum, host or routing change, provider; 1,024-token noise floor; counted only after a provider has reported cache activity | synthetic usage sequences classify to the expected cause | ToFu, pi |
| JL4 | One folded record per attempt; stream deltas stay in memory | a streamed attempt stores one record | Qwen Code |

### 5.4 Wilco conversations

| # | Change | Proof (write first) | From |
| --- | --- | --- | --- |
| WC1 | The ladder of §3.6: render, mask, reset to Session Digest, optional narrative | an 8K synthetic session crosses each rung in order; each rung writes a JL2 receipt | §3.6 |
| WC2 | State changes (selection, mode, enabled plugins, pack reload) appended as change-keyed deltas; one-shot notices re-armed after a reset | two consecutive turns with no change send no state block; a change sends one delta; prefix bytes unchanged | Codex, Kimi Code, opencode |
| WC3 | Retention class per product tool (keep, mask, supersede) as a typed enum | fixture history: findings and pinned items survive masking; listings become stubs; older entity views collapse | SWE-agent, Gemini CLI, Cline |
| WC4 | Thresholds as preset fractions of the served per-slot window; masking only at cold moments with a minimum gain from the price table | at 8K no threshold is ≤ 0 or ≥ W; a warm cache blocks masking unless the hard limit is near | §3.2 |
| WC5 | Breaker: two ineffective prunes (judged by the next reported usage) stop with a plain report; prune-reread cycles join the stagnation fingerprint (doc 21 §8.2) | scripted re-read loop stops after two cycles | Hermes, Cline #14328 |
| WC6 | "Tidy context" button: shows what would be dropped and the next-request cost, then runs rung 2 or 3 with no model call | UI state test; undo restores the previous window | DeepSeek Harness, Deep Agents |
| WC7 | Cold-cache chip on resume after the TTL: "re-reading ~N tokens is about $X" | TTL, minimum and price from `models.toml`; no chip below the minimum | Deep Agents, Kimi Code |

### 5.5 Long runs

| # | Change | Proof (write first) | From |
| --- | --- | --- | --- |
| LR1 | Stage handoff digest built by code from the journal (Session Digest schema, stage variant) | handoff digests are byte-identical on replay; no model call | ToFu, Cline |
| LR2 | Pack, preset or catalog changes during a run apply at the next stage boundary; a visible "applies at next stage" note | a change mid-stage leaves prefix bytes unchanged until the boundary | Hermes, DeepSeek Harness |
| LR3 | Typed journal queries (`journal.find`, `journal.get`) for child capsules and conversations; results paginated and never re-offloaded | pagination and cap tests | DeepSeek Harness, Strands |
| LR4 | Fan-out child results sized from the last measured prompt, not session totals | fixture: a large session total does not shrink child budgets | Hermes |
| LR5 | Economy mode (doc 40 R12) checks the provider's in-batch hit rate against the realtime hit rate before it is offered | DashScope-like data (in-batch 0, cached price 20%) hides Economy above a 62.5% realtime hit rate | Qwen Code |

### 5.6 Local runtime (llama-server)

| # | Change | Proof (write first) | From |
| --- | --- | --- | --- |
| LO1 | Launch profile: `--cache-prompt` (default on), `--cache-ram` sized from the KV formula (§4.2) and free RAM, `--cache-idle-slots` on, `-np` = number of busy namespaces the VRAM allows, `--ctx-checkpoints` 32, context shift off, `--cache-reuse 0`; `--swa-full` for SWA models only when E13 shows it pays | a launch-argument snapshot per preset; the launch record lists every flag (doc 56 MM2) | llama.cpp |
| LO2 | Per request: `cache_prompt: true`, `id_slot` pinned per cache namespace, `n_predict` = min(shape cap, slot `n_ctx` − counted prompt − margin), refusal before sending when below the shape minimum | request-builder unit tests; an over-budget capsule never reaches the server | ToFu, Qwen Code, kimi-cli |
| LO3 | Read `n_ctx` per slot and `total_slots` from `/props` at connect time; never assume a window; exact counts through `/tokenize` | fake server fixtures; an unknown window fails closed with a typed error | Strands gap, Letta, pi |
| LO4 | Never send more concurrent requests than there are slots | a scheduler test with 4 slots and 8 ready decisions | pi split-turn 429s |
| LO5 | Record `timings.cache_n`, `prompt_n`, `prompt_ms` in the ledger for every local attempt | ledger fields present for llama-server cassettes | local-qual |

### 5.7 Cost model additions (`tools/cost-model`)

- **CM1. Strategy W: a Wilco conversation.** Append-only prefix, capped tool results, masking every P turns at cold moments, a Session
  Digest reset at the fraction threshold; compare it with strategy A on `session-30min`.
- **CM2. Knob `a_compact_cold`.** `run_chat` prices the naive agent's compaction call as reading the cache (`request(static + H, static +
  H_prev)`, `tools/cost-model/cost_model.py:532-537`), which is the cache-safe-fork case. Most studied harnesses pay it cold (§2.2), so A
  is optimistic here; the knob prices both.
- **CM3. `h_batch` per provider** (DashScope 0; Anthropic's 30–98% range), replacing the single 0.60.
- **CM4. `ttl_policy = pacing`**: 1 h for session workflows, 5 min for runs.
- **CM5. Local seconds.** `local_pp_tps` (215–337 tokens/s measured on the test GPU, `tools/local-qual/README.md:240-243`) and
  layout (`single` or `split`) to report prefill seconds per workflow for hybrid models (§4.2).
- **CM6. Shadow cost** of local runs at a chosen cloud card (ToFu).
- **CM7. Prune payback function** for W (§3.2 rule 7).
- **Tests.** Add `tools/cost-model/test_cost_model.py` with known values: W ≤ A on `session-30min` for every model; `a_compact_cold` never
  lowers A; `h_batch = 0` makes E ≥ D when the realtime hit rate exceeds 0.625 at a 0.2 read ratio.

### 5.8 Instrument E13: tokens per workflow (proposal)

Doc 40 E12 measures effort and K per step shape. E13 (number proposed; doc 25 §11.1 owns the list) measures what a whole workflow sends.

- **Where.** `tools/local-qual/trace.py` for local runs; `tools/cost-model/cost_model.py --trace` to price the same traces for cloud models.
- **Input.** `suites/traces/<workflow>.json`, generated from synthetic fixtures (no game data): an ordered list of capsule requests, each
  with its namespace, sections tagged by tier, K and the expected answer shape. First traces: `populate-town`, `write-briefing` and a
  short `campaign-from-brief` stage.
- **Arms.** Layout `single` (system plus one user message) vs `split` (§4.3); `id_slot` pinned vs free; `-np` 1, 2, 4; a hybrid model
  (Qwen3.5-4B), an SWA model (Gemma 4) and a full-attention control.
- **Records per call.** Prompt tokens, `cache_n`, `prompt_n`, `prompt_ms`, `predicted_n`, section token counts from `/tokenize`, slot,
  namespace, layout; answer and parse status.
- **Report per workflow.** Prompt tokens, re-processed tokens, cached share per tier, prefill seconds, output tokens, and cost per admitted
  decision when priced by the cost model.
- **Decision rules (pre-registered).** Adopt `split` for a model family if it reuses at least 90% of the run-and-decision part across
  samples and repairs, and Pick accuracy stays non-inferior within 5 points (paired by item, as in doc 55 §4.4); otherwise keep `single`
  for that family and record it in the preset.

## 6. Design-gap candidates and doc 40 folds

### 6.1 Design-gap candidates (listed, not filed)

AGENTS.md routes these to `docs/design-gap-requests/` (the next free number is DG040). Until each is decided, the proposals that depend on
it are `proposal-only`.

| # | Gap | Current text | Proposed resolution |
| --- | --- | --- | --- |
| TE-G1 | Message layout for hybrid and SWA local models | Doc 40 §4.1 and doc 21 §8.1 fix the order, not the message boundaries | §4.3's split behind a preset field, decided per model family by E13 |
| TE-G2 | Conversation context policy and narrative fields | Doc 21 §8.1: no model-written summaries of facts; doc 40 R16: masking at phase boundaries | §3.6's ladder; narrative limited to goal and open questions, chips confirmed by the user, never read by workflows |
| TE-G3 | Auxiliary calls as prefix extensions | Doc 51 V10: each repair is a fresh single-turn capsule | Repairs, K samples and EXPLAIN append to the decision's capsule bytes; a fresh capsule only when the model or schema changes |
| TE-G4 | Context receipts and capsule manifests in the journal | Doc 38 journal classes do not name them | JL2 and CL6 records, visible in the inspector, never sent to the model |
| TE-G5 | Miss classifier and cost source in the ledger | Doc 40 §7 lists fields, no causes | JL1 and JL3 |
| TE-G6 | Owner of the llama-server launch profile and slot map | Docs 13, 46 and 55 each touch flags | One launch profile per preset (LO1), recorded per run |
| TE-G7 | Thresholds as fractions of the served per-slot window | Absolute numbers in several docs (doc 12 §5.3 `T_result` 1.5K) | Preset fractions plus absolute reserves; compiler check |
| TE-G8 | TTL by pacing | Doc 40 R11: 5 min default, 1 h when measured | 1 h for conversations and open cards, 5 min for runs, both measured by E13 and the ledger |
| TE-G9 | Tool result envelope contract for plugins | Doc 22 does not define result shapes for token budgets | TM1's envelope in the plugin manifest |
| TE-G10 | "Unchanged since" receipts | None | TM4 |
| TE-G11 | Uncached one-shot calls | Doc 40 R11 on minimums and clocks only | A breakpoint only where a later call is expected to re-read it |
| TE-G12 | Journal query tools for Wilco | Doc 12 §5.3 `expand_ref` per session only | LR3's typed, paginated journal queries |

### 6.2 Doc 40 folds (listed, not applied)

- **F1 (R2).** The golden test runs through the production serializer and the llama.cpp chat template, and includes seeded regressions and
  the representation-invariance check (CL2, CL3).
- **F2 (R4).** The namespace freeze includes the TTL; pack, preset and catalog edits apply at the next boundary.
- **F3 (§4.1).** Add §4.3's message boundaries and the appended repair and EXPLAIN tail.
- **F4 (R9).** The sibling release point (first token or stream end plus a settle window) is a measured CachePolicy field; single-call
  capsules make warm-first worth more than the ~2% Qwen Code measured for multi-call agents.
- **F5 (R11).** TTL by pacing; one-shot calls uncached.
- **F6 (R10).** `CacheSemantics` per (provider, model) as data with strict as the default; a DashScope/Qwen adapter; slot-keyed caches
  (xAI) fork their key after divergence; wire tests that markers survive proxy routes.
- **F7 (R13).** "Unchanged since" receipts in conversations.
- **F8 (R14).** Replace "one slot per busy DecisionKind" with slot pinning per namespace, `--cache-ram`, the checkpoint rule for hybrid
  and SWA models and the local-qual evidence (§4.2).
- **F9 (R16).** The conversation ladder of §3.6, with thresholds as window fractions.
- **F10 (R12, §5.1).** In-batch hit rate per provider.
- **F11 (§2.3).** Add: hybrid and SWA local models reuse only at message boundaries; summary calls with their own prompt miss the cache;
  proxies can drop markers; a client without a key saw ~10x more misses than another client with one (opencode #51580, a
  reporter's comparison).
- **F12 (§3).** New rows: auxiliary calls as prefix extensions; masking with recovery handles; unchanged receipts; typed result envelopes.
- **F13 (§8).** New rows: model-managed context tools; opaque provider compaction items; programmatic tool calling; embedding or LLM
  selection of history; mid-history stepping-stone breakpoints; per-request `num_ctx` changes (a reload drops the KV cache [I]);
  `--cache-reuse` KV shifting and context shift.
- **F14 (§5, §7).** Cost-model additions CM1–CM7; the E13 instrument; the miss classifier.

### 6.3 Findings for other sibling docs (reported, not fixed)

- **Doc 51 V10** (fresh single-turn repair capsule) conflicts with TE-G3 on hybrid local models, where it reuses only the system message.
- **Doc 11 §5.6** describes DeepSeek Harness at `477b4f4`; at `21638c5` the summary cap and headroom default to 65,536 tokens (an archived
  note said 8,192) and the summary call replays the warm prefix.
- **Doc 12 §5.3** sets `T_result` near 1.5K tokens "smaller for the embedded tier"; a window fraction is safer (TE-G7).
- **Doc 55** presets need fields for the message layout, `swa_full`, reasoning replay, mid-conversation system messages and cache TTL
  policy.
- **`tools/local-qual`** already records `cache_n`; its README could state that samples loop outside items (`run.py:440-441`) and that
  hybrid models reuse only at message boundaries, since both shape its latency figures.
- **`tools/cost-model`**: the naive agent's compaction is priced as a cache-safe fork (CM2).

## Open questions

1. **Does the fixed acknowledgement hurt small models?** E13's paired Pick accuracy per family; the answer decides TE-G1.
2. **Gemma 4 and Granite 4.x memory types.** Which qualified GGUFs report `n_swa` > 0 or recurrent layers, and what does `--swa-full` cost
   at 8K on an 8 GB GPU [U]?
3. **Checkpoint memory.** How much RAM do 32 checkpoints per slot take for Qwen3.5-4B at 8K [U]?
4. **Narrative fields at all?** Do the goal and open-question fields improve conversation outcomes enough to justify one call per reset,
   or is the code-only digest enough (TE-G2)?
5. **Masking cadence P and minimum gain** for Wilco conversations, per provider TTL and price table.
6. **Settle window per provider.** Does Anthropic's first-token release still miss for Plotroom-sized prefixes, and what do OpenAI,
   DeepSeek and Mistral need?
7. **TTL by pacing for our editors.** The pause distribution of real editing sessions (the ledger will have it).
8. **Retention classes.** Which Wilco tools belong to keep, mask or supersede, and does superseding by revision ever hide a fact the user
   still refers to?
9. **Recall eval.** A Hermes-style probe eval for conversation prunes on synthetic sessions: closed-book vs typed recovery, per tier.
10. **Estimator calibration** for Czech, Polish and Russian stringtables and SQF (doc 40 open question 10), now with `/tokenize` ground
    truth locally.
11. **ToFu's headline figure** was read from the arXiv HTML; re-check against the PDF before quoting outside this doc.
12. **DeepSeek's 64-token cache granularity** comes from a code comment only (doc 40 open question 6).

## Sources

**Harness code** at the commits in §1.1: <https://github.com/NiuTrans/ToFu> · <https://github.com/strands-agents/harness-sdk> ·
<https://github.com/deepseek-ai/deepseek-harness> · <https://github.com/earendil-works/pi> · <https://github.com/openai/codex> ·
<https://github.com/anomalyco/opencode> · <https://github.com/QwenLM/qwen-code> · <https://github.com/google-gemini/gemini-cli> ·
<https://github.com/MoonshotAI/kimi-code> · <https://github.com/MoonshotAI/kimi-cli> · <https://github.com/OpenHands/software-agent-sdk> ·
<https://github.com/OpenHands/OpenHands/tree/0.62.0> · <https://github.com/SWE-agent/SWE-agent> · <https://github.com/SWE-agent/mini-swe-agent>
(and PR #948) · <https://github.com/JetBrains-Research/the-complexity-trap> · <https://github.com/microsoft/acon> ·
<https://github.com/Aider-AI/aider> · <https://github.com/block/goose> · <https://github.com/cline/cline> ·
<https://github.com/letta-ai/letta-code> · <https://github.com/letta-ai/letta/tree/archive> · <https://github.com/langchain-ai/deepagents> ·
<https://github.com/NousResearch/hermes-agent> · <https://github.com/ggml-org/llama.cpp/tree/master/tools/server>.

**Issues and pull requests.** opencode issues 51580, 47485, 51109, 51557 and 50814 (<https://github.com/anomalyco/opencode/issues>) ·
Cline issues 14512, 14328 and 14551 (<https://github.com/cline/cline/issues>) · Kimi Code issue 2720
(<https://github.com/MoonshotAI/kimi-code/issues/2720>) · Codex issue 45074 (<https://github.com/openai/codex/issues/45074>) · OpenHands
PR 6597 (<https://github.com/OpenHands/OpenHands/pull/6597>) · Letta issue 3270 (<https://github.com/letta-ai/letta/issues/3270>) and
letta-code issue 3954 (<https://github.com/letta-ai/letta-code/issues/3954>) · Qwen Code issue 4239
(<https://github.com/QwenLM/qwen-code/issues/4239>) · mini-swe-agent draft PR 948 (<https://github.com/SWE-agent/mini-swe-agent/pull/948>) ·
anthropic-sdk-python issue 1451 (cited by ToFu; not re-read).

**Papers.** ToFu (arXiv 2607.11423) · The Complexity Trap (2508.21433) · ACON (2510.00615) · SWE-agent (2405.15793) · ACE (2510.04618) ·
Context Compaction Theory (2608.01326) · COMPINT, "Lost in Compaction" (2608.11242) · Parallel Context Compaction (2605.23296) · LLMs
Get Lost in Multi-Turn Conversation (2505.06120) · DTOC (2609.26121) · SelfCompact (2606.23525) · Context Length Alone Hurts (2510.05381) ·
NoLiMa (2502.05167) · RULER (2404.06654) · LongFuncEval (2505.10570) · Less is More (2411.15399) · MemGPT (2310.08560) · Mem0 (2504.19413) ·
Sleep-time Compute (2504.13171) · Don't Break the Cache (2601.06007) · ContextBench (2602.05892; the benchmark the Strands design
note ran, whose offloading figures in the CSV are the Strands team's own runs, `strands:team/designs/0015-context-manager.md:24`).

**Vendor pages and posts.** Anthropic: compaction overview (re-read 2026-09-28)
<https://platform.claude.com/docs/en/build-with-claude/compaction>, context editing
<https://platform.claude.com/docs/en/build-with-claude/context-editing>, <https://claude.com/blog/context-management>,
<https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>,
<https://www.anthropic.com/engineering/writing-tools-for-agents>, <https://www.anthropic.com/engineering/advanced-tool-use>,
<https://www.anthropic.com/engineering/multi-agent-research-system>,
<https://claude.dev/blog/lessons-from-building-claude-code-prompt-caching-is-everything/>. OpenAI:
<https://developers.openai.com/api/docs/guides/compaction>, <https://developers.openai.com/cookbook/examples/agents_sdk/session_memory>,
<https://openai.com/index/gpt-5-1-codex-max/>. xAI: <https://docs.x.ai/developers/advanced-api-usage/context-compaction>. Google ADK:
<https://developers.googleblog.com/architecting-efficient-context-aware-multi-agent-framework-for-production/>. Factory:
<https://factory.com/news/evaluating-compression>. Strands: <https://strandsagents.com/blog/introducing-strands-harness/>,
<https://strandsagents.com/blog/reduced-cost-better-isolation-more-resilience/>. OpenHands:
<https://www.openhands.dev/blog/openhands-context-condensensation-for-more-efficient-ai-agents>. Manus:
<https://rlancemartin.github.io/2025/10/15/manus/>. Chroma: <https://www.trychroma.com/research/context-rot>. Letta:
<https://www.letta.com/blog/benchmarking-ai-agent-memory/>. SWE-bench leaderboards:
<https://raw.githubusercontent.com/SWE-bench/swe-bench.github.io/master/data/leaderboards.json>.

**Repo.** Docs 10, 11, 12 (§5.2–§5.6), 14 (§3.2), 21 (§4, §8), 22, 25 (§11), 38 (§4.2–§4.6), 40 (§2–§8), 46, 49, 51 (H23, H24, V10, V11), 55,
56 · `tools/local-qual/README.md`, `run.py` · `tools/cost-model/cost_model.py` · DG019–DG027, DG039.

## Verification notes

### 2026-09-28, author checks at write-up

- The harness mechanisms come from per-harness code studies at the pinned commits. At write-up about 40 anchors were re-read against the
  clones, among them: ToFu `CONTEXT_COMPACTION.md:56-100, 125-149`, `cache.py:95-114`, `_unchanged.py:1-12`,
  `LLM_COST_OPTIMIZATION.md:9-14, 73`, `context_engineering.md:36-56`; Strands `environment.py:1-14`; DeepSeek Harness `summarizer.ts:20-35`,
  `region.ts:408-424`, `config.ts:68-80`; pi `cache-warmer.ts:14-40`, `compaction.ts:142-153`, `anthropic-messages.ts:186-196`; Codex
  `compact.rs:53-58`; opencode `compaction.ts:26-34`; Qwen Code `chatCompressionService.ts:100-142`, `chat-compression-cache-sharing.md:66-84`,
  `review-cpu-for-tokens.md:115-136`; Gemini CLI `chatCompressionService.ts:44-51`; kimi-cli `compaction.py:58-77`; Kimi Code
  `fullCompactionService.ts:74-82`; OpenHands `llm_summarizing_condenser.py:70-82`; SWE-agent and the Complexity Trap
  `history_processors.py` (polling); goose `cache_semantics.rs:8-30`, `prefix_invariance.rs:1-10`; Cline `message-builder.ts:28-52`,
  `auto-compact.mdx:38-46`; Letta Code `compaction.ts:20-60`; aider `base_coder.py:2088-2098`; ACON `memory.py:338-346`; Deep Agents
  `summarization.py:155-170`; Hermes `prompt_cache_scope.py:174-200`, `context_compressor.py:956-983`, `SCORECARD-2026-08-15.md:15-52`,
  `prompt_caching.py:110-122`, `background_review.py:998-1012`; llama.cpp `server-context.cpp:1568-1615, 3218-3230, 3360-3395, 3468-3490,
  3531-3600`, `common.h:626-634`, and the server README flag table. All matched the studies' claims.
- The llama.cpp checkpoint rule was read in code, not only in the README; the first-user-message checkpoint applies when a slot has no
  checkpoint yet (`server-context.cpp:3565`).
- §4.2's table was computed at write-up from 808 local-qual records with a throwaway script (grouped by suite, condition and model file;
  cached share = sum of `cache_n` / sum of prompt tokens); the table shows the 806 Q4_K_M records, and the two single-call UD-quant groups
  are left out. The runner's loop order was read in `run.py:440-441`; checkpoint invalidation and thinning in
  `server-context.cpp:2325-2350, 3402-3408`.
- The Anthropic compaction overview page was re-fetched and confirms the `compact-2026-09-04` on-demand mode and the separate threshold
  mode.
- §3.2's 8K figures are our arithmetic from the cited constants.
- The ToFu paper's table, the Strands blog figures and the Factory scores were read by fetch during the studies and are marked
  [V-author]; they were not re-fetched at write-up.
- Public rule: no private or unpublished project, local path or user name appears in this doc or the CSV.

### 2026-09-28, independent review

- **Mechanical check of every code anchor.** A throwaway script extracted all 414 `alias:path:lines` citations from this doc and the
  CSV and resolved each against its repository at the §1.1 commit with `git show` (opencode at `b471c2b`, although the local clone had
  moved on; the OpenHands 0.62.0 tree from its sparse checkout). Every file exists and every line range lies inside the file. The only
  unmatched hit was the script's own parsing of `=` in `ctrap:config/default_no_demo_checkpoint_same_model_N=21_critic.yaml`, which exists.
- **Content spot-checks at the pinned commits (51 files or ranges), all matching unless noted:** ToFu `cache.py:97-112` (34% → 8%, 943K →
  306K, 3 conversations), `cache.py:316`, `cache_settle.py:1-86`, `_prefix.py:87-99`, `LLM_COST_OPTIMIZATION.md:11, 13, 73`,
  `CONTEXT_COMPACTION.md:77-78, 90-98`; DeepSeek Harness `summarizer.ts:25-31`, `region.ts:410-422`, `config.ts:75-76, 172-194`,
  `cordis.patch.yml:330`; pi `cache-warmer.ts:15-26`, `compaction.ts:148-152, 289-291`, `anthropic-messages.ts:188-196`, and the pico3
  collapse default; Codex `compact.rs:55`; opencode `compaction.ts:28-33`; Qwen Code `chat-compression-cache-sharing.md:69-83`,
  `batch.md:48-55`, `review-cpu-for-tokens.md:115-134`, `resident-tool-prompt-assembly.md:15-18, 123`, `read-file.ts:184-193`; Gemini
  CLI `chatCompressionService.ts:45`, `snapshotGenerator.ts:176`; kimi-cli `compaction.py:60-76`, `btw.py:1-9`; OpenHands
  `test_prompt_snapshot.py:223-232`, `llm_summarizing_condenser.py:72-80, 248-249`, `event/base.py:17, 82-105`; SWE-agent
  `history_processors.py:106-122`; ACON `memory.py:342`; aider `base_coder.py:2089-2092`, `main.py:954-955`; goose
  `cache_semantics.rs:8-51`; Cline `message-builder.ts:28-51`, `auto-compact.mdx:41-45`, `compaction-shared.ts:15-30`; Letta archive
  `self_summarizer.py:37, 100, 111`; Hermes `SCORECARD-2026-08-15.md:1-52, 351`, `prompt_caching.py:114-120`,
  `background_review.py:1001-1010`, `context_compressor.py:959-967`, `budget_config.py:85-89`, `compression_marker.py:14-18`;
  Strands `context_manager.py:31-34, 83-89`, `retrieval_tool.py:26`, `environment.py:1-12`, `team/designs/0015-context-manager.md:24,
  28`; llama.cpp `server-context.cpp:3218-3230, 3471-3484, 3560-3576`, `common.h:626-633`, `README.md:165-170`; Complexity Trap
  `auxiliary-data/bootstrapped_cis.csv`.
- **Literature and vendor figures re-read (15):** NoLiMa 11 of 13 below half at 32K; 2510.05381 13.9–85%; LongFuncEval 7–85%;
  Less-is-More 46 vs 19 tools (paper body, Table II); sleep-time compute ~5x; 2505.06120 −39% and Table 2 recap figures; ACE 18,282 →
  122 tokens, 66.7 → 57.1 (63.7); COMPINT 17% and over 90%; DTOC 10.3% and 12.7%, 3x and 3.5x; the Complexity Trap costs and solve
  rates from its repository CSV; ToFu Table 1 (−20.8%, −43.6%, −20.8%; Opus cost +3.2%; no Claude Code version); Factory 3.70, 3.44,
  3.35 and artifact trail 2.19–2.45; Anthropic context editing +29%, +39%, −84%; ContextBench is 2602.05892. All matched.
- **Issues and PRs re-read through the GitHub API:** opencode 51580, 51109, 47485, 51557, 50814; Cline 14512, 14328, 14551; Kimi Code
  2720; Codex 45074; OpenHands PR 6597 (200 vs 203 solved, "$40 more"); Letta 3270; letta-code 3954; Qwen Code 4239; mini-swe-agent PR
  948. All exist and support the claims, after the corrections below. Every vendor, blog and arXiv URL in the doc returned HTTP 200. The
  CSV parses: 116 rows × 9 fields, no empty cells, verdicts ADOPT 68, ADAPT 19, KEEP 13, REJECT 16; every `measured_effect` cell is
  tagged or says "none". Relative links resolve.
- **Corrected in place:** Qwen Code's "0 → 92.8%" compaction figure (the 92.82% is live, the 0 comes from a mock; TL;DR, §1.3, §2.2,
  §2.11, CSV); the ~40% and 0/20 settle-window figures come from an Anthropic SDK issue that ToFu cites, not from ToFu's own
  measurements (§2.2, CSV); Strands' `auto` context manager summarises at 0.85 in code, not only in the harness docs (§1.2, §3.2);
  opencode 51580 compares two different clients (§2.2, F11, CSV); opencode 47485's 22–42K is the context left after compaction, not
  tokens recovered (§3.5); Qwen Code 4239 was reported as edits falsely blocked after idle masking, and its fix adds a residency flag
  (§2.4, §3.5, CSV); at 8K pi's threshold is −8,192 and the problem is the 20,000-token keep, while pico3's collapse is off by default at
  any window (§1.3, §3.2, CSV); the recap turn in 2505.06120 recovered about half of the loss, not most, for two models (§2.10, §2.11);
  DTOC's quotation reads "reversibility is critical" (§3.3); the Hermes and Complexity Trap caveats gained the question-bank and
  thinking-mode notes (§2.11); CM5's range now matches the local-qual README (215–337 tokens/s); two quotations were made verbatim (ToFu
  "cached prefix EVERY round", the Strands design note) and a paraphrase lost its quotation marks (Qwen Code's resident-tool design);
  the doc 21 chip reference now names §4.2 and §11.3; §4.3 and CL5 now state that the split layout keeps strict role alternation, which
  answers doc 51 V10's template concern; full hashes were added for the three commits whose short prefix the GitHub API does not resolve;
  the Sources list now links each issue and PR directly.
- **Scope and fit.** Every recommendation in §3.6 and §5 stays inside the product: handles point into the journal, recall is a typed
  product query, plugins enter only through the plugin system, model-managed context and code execution stay rejected, and each change
  is a code-owned step or panel that a weak model can follow. The local runtime flags in §5.6 are set by the product's runtime profile,
  never by the agent. No copied code; quotations stay within a sentence.
