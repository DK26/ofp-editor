# The language service as the model's instrument: lessons from coding agents

Research doc 61 for Plotroom (`ofp-editor`). Research date: 2026-09-28. Audience: contributors and LLM coding agents. This file is
meant to be read on its own.
Question answered (owner, 2026-09-28): "Learn from OpenCode (or better examples) about the usefulness of an LSP server to the LLM",
read together with the owner's direction of the same day to encode all knowledge and know-how in the harness, so that more powerful
models can "go even crazier and be granted more freedoms". In Plotroom's terms: which language-service mechanisms help a model edit
missions and scripts, which help only strong models, and how Teller should serve Wilco.

**Status: proposal.** Nothing was built, run or measured for this doc. Code was read in public shallow clones at the commits of §1.1;
papers were read as each citation in §2 says (abstract, or full text read by a research pass). Every design proposal is [I]. This
doc changes no decision.
**Epistemic legend.** **[V]** read in code at the cited commit, or on the cited public page, on 2026-09-28. **[V-author]** a number
measured and published by the cited authors, not reproduced by us. **[V-vendor]** a vendor's statement about its own product.
**[V per doc N]** taken from a sibling doc. **[I]** our inference or proposal. **[U]** unknown.
**Relation to sibling docs.** Doc 23 owns Teller's checker, catalog and model-shaped diagnostic schema (§13.4); doc 30 owns the
knowledge layers and the first tool list (§4.4), adopted by D027; doc 31 §7 owns the symbol index and editing features; docs 21 and
25 own the repair doctrine; doc 55 owns per-model knobs (D048); doc 57 owns the typed result envelope (its TM1); doc 10 studied
OpenCode's harness but not its language-server path. Two docs were written beside this one: doc 62 (type-driven guidance, the
study of the owner's `strict-path` crate; its §4 covers how rustc and rust-analyzer diagnostics reach coding agents) and doc 63 (the
capability ladder: knowledge in the harness, freedom by qualification; its §3.1 maps TS0–TS3 onto freedom levels FR0–FR8).
This doc supplies the language-service rows of doc 63's ladder.
**Names.** *Push channel*: findings the harness attaches to a result without the model asking. *Pull tool*: a lookup the model
chooses to call. *Card*: a short, typed, model-facing rendering of a result. *Handle*: an opaque id the harness issues for a result.
*Teller surface level* (TS0–TS3, this doc's term, §4.10): which Teller channels and tools a model setup gets. Gaps TG1–TG9 (§3) and
tests TT-01–TT-20 (§5) are this doc's labels; none collides with an existing family (checked 2026-09-28).
**Hygiene.** Public sources only; no game content; no local paths.

## TL;DR

- **Push beats pull.** The general coding agents that wire a language server to the model make post-edit diagnostics the default
  channel and keep model-called navigation behind a flag, a plugin or deferred loading. OpenCode appends errors to every edit, write
  and patch result, but registers its nine-operation `lsp` tool only under an experimental flag [V]; Qwen Code's twelve-operation
  tool is experimental and deferred [V]; Claude Code's arrives through plugins [V-vendor]. The exceptions are symbol-first tools:
  Zed's agent and Serena offer pull tools only, and Serena switched push off on purpose [V]. Codex, Gemini CLI, Kimi CLI and Goose
  give the model no language-server path at all [V].
- **Diagnostics in the loop pay; navigation tools mostly do not.** SWE-agent's lint guard is worth 3 points on SWE-bench Lite (18.0%
  against 15.0%) [V-author]; Kiro reports 29% fewer command runs [V-vendor]. A controlled token study found language-server navigation
  cost 6–118% more tokens on localization and saved tokens only for the weakest model; location-only references force extra reads,
  and semantic references miss names inside strings and comments [V-author].
- **What a finding says matters more than how often you loop.** Admissible alternatives carry most of the repair gain (14/50 → 36/50
  for Qwen2.5-Coder-14B, in a text-game loop) [V-author]; more detail about the one root error helps; raw compiler text can do worse
  than minimal feedback; nearly all gain comes in 1–3 rounds; and 0.5–1.5B models do better resampling with the facts than re-reading
  their own broken code [V-author]. Plotroom's planned one-finding repair with recomputed allowed values (doc 25 §7.2) matches the
  arm that won those external measurements (not yet measured on Plotroom's steps); this doc adds a priority order, a delta rule, a
  sanitizer and a resample rule.
- **Earlier is better, and completeness is non-negotiable.** Type-level constraint at decode time cut compile errors by 56–75% on average
  across six models, and a language-server monitor let a 1.1B model beat a far larger one on compile rate [V-author]; checking during
  generation beat checking after it (13.1% against 20.7% compile errors in one study) [V-author]. An incomplete constrainer, however,
  cut functional correctness by up to 97% [V-author]. Teller may constrain or cut a stream only where it can prove a dead end.
- **By design, Teller already owns the stronger channel** (designed, not built). Wilco never edits files: each proposal is planned
  on a `Scratch` fork and admitted through Teller's `check_field` and lints, and a rejection never enters history
  (commands-undo-history §4). That is SWE-agent's
  reject-and-revert, enforced by types. None of the external-server timing tricks (150 ms debounce, 5–10 s waits, a 45 s initialize
  timeout) apply to an embedded library over an immutable snapshot.
- **Seven additions** (§4): repair quotes only findings the proposal introduced, with moved lines remapped (Hermes, Copilot); every
  echoed name passes a sanitizer, because identifiers are attacker-controlled text (Hermes); a fixed order for "which one finding";
  opaque, revision-bound, consumable handles for symbols, reference sets and fix menus (Qwen Code, Zed); name-addressed where-used
  queries that return the owning item, the line text and "cannot prove" rows; a "fixed by deletion" flag; quick fixes as a PICK menu
  that runs the same fix command a user clicks.
- **Weak models get facts pushed; strong models earn tools.** TS1 (any setup): push findings, code-picked cards, fix menus, no
  navigation tool. TS2 (qualified for script Compose): name-addressed lookups and checks during streaming. TS3 (qualified strong
  setups at higher effort): the full query family, multi-step drafts on a `Scratch` fork with one final admission, rename and
  safe-delete proposals, more repair rounds. Freedom means bigger steps and more tools, never weaker checks (doc 63; D024, D037,
  D045, D048).
- **The owner's `strict-path` idea has a runtime twin.** Qwen Code signs each call-hierarchy item with an HMAC over the document hash
  and rejects a stale or forged one with a message that says what to redo [V]. A handle the model can only copy is a witness that the
  lookup happened on the current mission. Doc 62 covers the compile-time side.
- **Budgets** [I]: every Teller call inside a model step sits in doc 53's L0 class (< 0.1 s); push costs 0 tokens on a clean result
  and about 50–200 tokens per finding; pull results are capped per preset with exact "N more" counts in doc 57's envelope.
- **Twenty tests to write first and fourteen design-gap candidates**, none filed (§5, §6). Nothing needs an engine change, no
  language-server process is spawned or downloaded, and Teller stays an embedded Rust library (doc 23 §13).

## 1. What coding agents do with language servers

### 1.1 Scope, pins and prefixes

| Prefix | Project | Commit read | What reaches the model |
| --- | --- | --- | --- |
| `oc:` | anomalyco/opencode (MIT); paths under `packages/opencode/src/` unless they start with `packages/` | `03e67171ab` (dev, 2026-09-28) | Push after edit; experimental pull tool |
| `qw:` | QwenLM/qwen-code (Apache-2.0); paths under `packages/core/src/` | `3f5ae3ffeb` | Experimental, deferred pull tool |
| `cr:` | charmbracelet/crush (FSL-1.1-MIT, source-available: ideas only) | `056387be7a` | Push after edit and view; small pull tools |
| `se:` | oraios/serena (GPL-3.0-or-later) | `7a2968335f` | Pull tools and symbolic edits; push switched off |
| `zed:` | zed-industries/zed, `crates/agent` only | `d3ccd57194` | Pull tools; no push |
| `cp:` | microsoft/vscode-copilot-chat (archived 2026-05-20) | `5863f5a708` | Push of new diagnostics, behind an experiment flag |
| `cl:` | cline/cline | `252082b9e9` | `@problems` mention |
| `co:` | continuedev/continue | `5522c6f44c` | Code-owned autocomplete context |
| `le:` | letta-ai/letta-code | `f378d20d90` | Errors appended on read, behind a flag |
| `he:` | NousResearch/hermes-agent (MIT) | `e98be8a328` | Push with a baseline delta and a sanitizer |
| `mls:` | isaacphi/mcp-language-server | `e4395849a5` | MCP bridge |
| `swe:` | SWE-agent/SWE-agent | `3ea751c087` | Lint guard that reverts |
| `ai:` | Aider-AI/aider | `5dc9490bb3` | Lint after edit; ranked repo map |
| — | Claude Code, Kiro | closed source | Documentation and vendor blog only |
| — | openai/codex `abc8f0c9a1`, google-gemini/gemini-cli `2fe7c2d3f0`, MoonshotAI/kimi-cli `9ab1286`, block/goose `04ed836c8c` | — | Nothing: no `textDocument/`, `publishDiagnostics` or language-server client [V] |

All transfer is design ideas; no code is copied, and all of it is TypeScript, Go or Python.

### 1.2 OpenCode: two channels, only one on by default

- **Push, always on.** `edit`, `write` and `apply_patch` notify the server after the write, wait for diagnostics and append them to
  the tool result: "LSP errors detected in this file, please fix:" (`oc:tool/edit.ts#L196-L201`, `oc:tool/apply_patch.ts#L265-L293`).
  `write` also reports up to `MAX_PROJECT_DIAGNOSTICS_FILES = 5` other files with errors, which surfaces cross-file breakage
  (`oc:tool/write.ts#L18`, `#L74-L90`) [V].
- **Format.** `Diagnostic.report` keeps severity 1 (errors) only, caps them at `MAX_PER_FILE = 20` with "... and N more", and prints
  `ERROR [line:col] message` with 1-based positions inside `<diagnostics file=…>` (`oc:lsp/diagnostic.ts#L3-L27`). A clean edit costs
  no tokens [V].
- **No baseline.** Errors that existed before the edit get the same "please fix" wording as new ones [V]. The model is told to fix code
  it did not touch.
- **Pull, experimental.** One `lsp` tool with nine operations (goToDefinition, findReferences, hover, documentSymbol, workspaceSymbol,
  goToImplementation, prepareCallHierarchy, incomingCalls, outgoingCalls) taking a file path and 1-based `line` and `character`
  (`oc:tool/lsp.ts#L11-L35`). It is registered only when `OPENCODE_EXPERIMENTAL_LSP_TOOL` or the umbrella `OPENCODE_EXPERIMENTAL` is
  set (`oc:tool/registry.ts#L247`; `oc:effect/runtime-flags.ts#L10-L14`, `#L45`) [V]. There is no rename, code-action or diagnostics
  operation. Each call asks the `lsp` permission, fails with "No LSP server available for this file type." when none matches, touches
  the file (so a query can wait up to 5 s for fresh diagnostics) and returns `JSON.stringify(result, null, 2)` of the raw payload:
  `file://` URIs, 0-based ranges and SymbolKind integers (`oc:tool/lsp.ts#L49-L109`) [V]. The only bound is the generic 2,000-line or
  50 KB truncation (`oc:tool/truncate.ts#L14-L15`). A pretty-printed location costs about 60–80 tokens and carries no source text [I].
- **Discovery and launch.** 38 built-in server definitions `{id, extensions, root(file), spawn(root)}`; the root is the nearest
  ancestor with a marker file; servers start lazily once per (root, server), in-flight spawns are de-duplicated and a failed pair is
  marked broken for the session (`oc:lsp/server.ts#L32-L86`; `oc:lsp/lsp.ts#L208-L297`). Many definitions install their binary with
  npm, `go install`, `gem install` or `dotnet tool install` unless `OPENCODE_DISABLE_LSP_DOWNLOAD` is set (`oc:lsp/server.ts#L358-L372`;
  `oc:effect/runtime-flags.ts#L22`) [V].
- **Timing.** 150 ms debounce, a 5 s wait in document mode, 10 s in full mode, 3 s per pull request, 45 s for `initialize`
  (`oc:lsp/client.ts#L13-L18`). Old diagnostics are kept on `didChange` because some servers republish only on real content change
  (`#L564-L567`); a publish counts only if it matches the new version or arrived after the edit (`#L464-L497`) [V]. PR #23771 reports warm
  C# edits falling from over 3 s, with no errors shown, to about 0.7 s [V-author].
- **Warm-up and code-owned uses.** `read` pre-opens the file in its server and ignores failure ("LSP warm-up is optional",
  `oc:tool/read.ts#L117-L120`). A user attachment with start = end is widened to the enclosing symbol through `documentSymbol`
  (`oc:session/prompt.ts#L830-L853`) [V].
- **Failure handling.** Every request swallows errors into `null` or `[]` (`oc:lsp/lsp.ts#L377-L441`), so "no result", "still
  indexing" and "unsupported" all read as `No results found for ${args.operation}` (`oc:tool/lsp.ts#L108`) [V]. Unknown looks like
  empty.

Verdict [I]: the push channel helps weak models (no tool choice, errors only, same turn). The pull tool is poorly shaped for them: it
asks for exact columns and returns raw JSON with locations but no text. OpenCode's two pitfalls to avoid are the missing baseline and
the silent "empty".

### 1.3 The others

| Agent | Push after edit | Pull tools | How the model names a symbol | Shape and caps | Idea worth taking |
| --- | --- | --- | --- | --- | --- |
| Claude Code | Yes; per-server `diagnostics` switch (default on) | Nine operations with OpenCode's names (per third-party write-ups; the version that added them is [U]) | Position | Plugin-configured servers (`lspServers` or `.lsp.json`), binary not installed by the plugin [V-vendor] | Push can be switched off per language without losing lookups |
| Qwen Code | No (only `tools/lsp.ts` uses the client) | Twelve: OpenCode's nine plus `diagnostics`, `workspaceDiagnostics`, `codeActions` (listed, never applied) (`qw:tools/lsp.ts#L34-L46`, `#L732-L807`) | Position | Numbered, relative-path, 1-based text lists; per-operation caps 20–50; a one-line refusal per missing parameter (`#L1163-L1222`); errors as text; retries an empty result 2 s after open (`qw:lsp/constants.ts#L34-L42`) | **Signed handles**: each call-hierarchy item carries an HMAC-SHA256 over the item plus the document hash and version, with a random per-connection key (`qw:lsp/native-lsp-service.ts#L1456-L1490`); a stale or forged item raises "stale or has unknown provenance; prepare call hierarchy again…" (`#L84-L92`, `#L1494-L1509`) [V] |
| Crush | Yes, after edit, multiedit, write, rename and replace; also on view after 300 ms | `lsp_definition`, `references`, `lsp_rename`, `lsp_replace_symbol`, `lsp_symbols`, `lsp_call_hierarchy`, `lsp_diagnostics`, `lsp_restart` | **Name**: grep `\bname\b` (≤ 100 hits), keep the first hit the server confirms, so hits in comments and strings drop out (`cr:internal/agent/tools/lsp_helpers.go#L24-L91`) | File and project sections, errors first, 10 per section with "N more", a summary count (`diagnostics.go#L130-L252`); returns after 1 s if nothing changed, else after 300 ms of stability, 5 s cap (`cr:internal/lsp/client.go#L620-L690`) [V] | Whole-symbol edits remove text-matching failures |
| Serena | Built, then **switched off** (`ENABLE_DIAGNOSTICS = False`: edits "often intentionally introduce diagnostics … resolved in subsequent edits", `se:src/serena/tools/tools_base.py#L425-L447`) | Symbol overview, find, referencing symbols (with a snippet each), implementations, per-file and per-symbol diagnostics, replace body, insert before/after, rename, `safe_delete_symbol` | **Name path** (`MyClass/my_method`, `[i]` for overloads) (`se:src/serena/tools/symbol_tools.py#L84-L151`) | Over 150,000 characters: "The answer is too long (N characters)…", never cut mid-content (`se:src/serena/util/text_utils.py#L949-L976`) [V] | Safe delete: delete only when unreferenced, else return the references (`symbol_tools.py#L352-L468`) |
| Zed agent | No | `go_to_definition`, `find_references` (path, line and a ≤ 200-character snippet per hit), `rename_symbol`, `diagnostics`, `get_code_actions`, `apply_code_action` | File, 1-based line and **name**; code finds the column, and on failure shows the line so the model can correct itself (`zed:crates/agent/src/tools/symbol_locator.rs#L12-L25`, `#L138-L217`) | Diagnostics pulled fresh or marked "Diagnostics may be stale."; errors and warnings only; the tool description says "make 1-2 attempts and then give up" and "Don't remove code you've generated just because you can't fix an error" (`diagnostics_tool.rs#L16`, `#L39-L40`, `#L83`); the system prompt repeats both as "Make 1-2 focused attempts … then defer to the user" and "Never simplify or discard meaningful code just to silence diagnostics" (`templates/system_prompt.hbs#L93-L96`) [V] | **Consumable fix menus**: `apply_code_action(index)` first `take()`s the stored list, then checks the index and refuses out-of-range with the count (`apply_code_action_tool.rs#L89-L108`) [V] |
| Copilot Chat | Yes, **new only**: waits 1 s, keeps errors and warnings absent before the edit, ≤ 20 per file, behind the `AutoFixDiagnostics` experiment (`cp:src/extension/tools/node/editFileToolResult.tsx#L79-L100`, `#L149-L174`) | `get_errors`: "first N of M", N = 50, related information dropped "to avoid blowing up the prompt" (`getErrorsTool.tsx#L313-L358`) | — | A repaired malformed patch comes back as `<correctedEdit>` (`#L125-L129`); retry advice only for models that need it (`modelNeedsStrongReplaceStringHint`, `#L135`); symbol hits pruned by priority under a token budget (`searchWorkspaceSymbolsTool.tsx#L81-L90`) [V] | Per-model harness text; new-only reporting |
| Hermes | Yes, **delta against a baseline** taken before each write (`he:agent/lsp/manager.py#L293-L317`); the baseline is moved to post-edit lines with a difflib line map, and errors in deleted lines drop out (`he:agent/lsp/range_shift.py#L1-L73`) | — | — | Errors only by default ("warnings/info/hints would flood the agent"), 20 per file, 4,000 characters total (`reporter.py#L14-L19`) [V] | **Sanitizer**: `message`, `code` and `source` are attacker-controlled ("a hostile repo can smuggle instruction-shaped text through identifier names"): CR/LF collapsed, control characters dropped, caps of 300/80/80 characters, `<>&` escaped (`reporter.py#L21-L72`) [V] |
| Cline, Continue, Letta Code | Letta appends ≤ 10 errors on read of files under 500 lines (`le:src/tools/impl/read-lsp.ts#L51-L98`); Cline keeps a new-problems helper with no caller outside tests (`cl:apps/vscode/src/integrations/diagnostics/index.ts#L7-L61`) | Cline: `@problems` mention (`cl:apps/vscode/src/core/mentions/index.ts#L390-L399`) | — | Continue builds autocomplete context in code: syntax-tree path to the cursor, definitions injected, a 100 ms race; its generic language-server snippets are off (`co:core/autocomplete/snippets/getAllSnippets.ts#L17`, `#L31-L36`) [V] | Code decides what context the model sees |
| mcp-language-server | — | `definition` by exact, qualified name through `workspace/symbol`, returning the full definition with line numbers; `diagnostics` with surrounding lines after a fixed 3 s sleep ("TODO: wait for notification") (`mls:internal/tools/definition.go#L12-L104`; `diagnostics.go#L29-L31`) [V] | Name | — | Return text, not locations |
| SWE-agent | Lint before and after; if the edit adds errors, **revert**, show the would-be and original windows, "DO NOT re-run the same failed edit command" (`swe:tools/windowed_edit_linting/bin/edit#L94-L119`) [V] | — | — | A narrow flake8 set (F821, F822, F831, E111–E113, E999, E902) | Reject instead of apply-and-ask |
| Aider | Tree-sitter syntax errors, compile, flake8 after each edit, shown inside their enclosing scopes with a marker; at most 3 reflections (`ai:aider/linter.py#L82-L116`; `ai:aider/coders/base_coder.py#L101`) [V] | — | — | Repo map: tags ranked by personalised PageRank, binary-searched into a token budget (1,024 by default, `ai:aider/repomap.py#L49`, `#L676-L698`) [V] | Budgeted, ranked outline |
| Kiro | Reads the IDE's diagnostics after generating code, "in under 35ms" per check; 29% fewer command runs; about 4× more checks in spec mode, one per task boundary (blog, 2026-01-14) [V-vendor] | Later: definition, references, hover, rename, diagnostics in the CLI [V-vendor] | — | — | Diagnostics instead of builds |

Two convergences stand out [I]. OpenCode and Claude Code expose the same nine pull operations, a de facto shape that Plotroom should
not copy, because it addresses symbols by column. And every product that measured or tuned the push channel filters it: errors first
or errors only, new only, capped with a count.

### 1.4 Eleven mechanisms and who they help

| # | Mechanism | Seen in | Weak models | Strong models | Plotroom (§) |
| --- | --- | --- | --- | --- | --- |
| A | Automatic post-edit diagnostics | OpenCode, Claude Code, Crush, Copilot, Letta, Hermes, SWE-agent, Aider, Kiro | Yes, strongly: no tool choice, same turn (§2.1) | Yes; Serena's counterpoint: intermediate edits break things on purpose | Admission findings as repair cards (§4.6); drafts for strong setups (§4.7) |
| B | Reject and revert vs apply and report | SWE-agent reverts; the rest apply | Reject: a broken edit never compounds | Apply-and-report suits multi-step work | Already reject (§4.6); drafts on a fork (§4.7) |
| C | How a symbol is named | Position (OpenCode, Claude Code, Qwen); line + name (Zed); name (Crush, mcp-language-server); name path (Serena); selectors (Lanser-CLI) | Names yes, columns no | Either | Typed addresses and handles only (§4.4) |
| D | Code actions as a menu | Zed (numbered, stored, consumed); Qwen (listed only) | Yes: it is a PICK | Yes | Fix menus (§4.3, §4.6) |
| E | Model-called navigation | All, gated or deferred | Little or negative (§2.5) | Modest precision gain | TS2–TS3 only (§4.10) |
| F | Code-owned context | Continue, OpenCode's symbol widening, Aider's map | Yes | Yes | Code-picked cards; the mission outline (§4.3) |
| G | Semantic edits (rename, replace body, safe delete) | Serena, Crush, Zed, mcp-language-server | Yes, as typed operations | Yes | Rename and safe delete as proposals (§4.3) |
| H | Result shape, caps, empty vs unknown | Every product differs | Numbered text, counts, explicit "unknown" | Tolerate more | The result card (§4.5) |
| I | Timing, debounce, warm-up | OpenCode, Crush, Copilot, mcp-language-server, Letta, Continue | — | — | Not needed in-process; index freshness only (§4.9) |
| J | Bounded repair; do not silence the checker | Zed (1–2 attempts; do not delete code), Aider (3), SWE-agent | Yes: weak models loop and delete | Need more rounds | Stop rules plus "fixed by deletion" (§4.6) |
| K | Per-model tool surfaces and hints | Copilot per-model hints; Qwen deferral; flags; Claude Code's per-server switch | Yes | Yes | TS levels under D048 presets (§4.10) |

## 2. Evidence

### 2.1 Diagnostics in the loop

- **SWE-agent** (NeurIPS 2024): GPT-4 Turbo on SWE-bench Lite resolved 18.0% with the linting editor, 15.0% without the lint guard and
  10.3% with shell-only editing [V-author]. The guard's stated aim is to stop loops of re-editing the same snippet.
- **Kiro**: diagnostics in place of builds, under 35 ms per check, 29% fewer command runs [V-vendor].
- **Static analysis as a feedback loop** (arXiv 2508.14419; GPT-4o, Bandit and Pylint, severity-weighted issue choice, 10 rounds):
  security issues from over 40% to 13%, readability from over 80% to 11% [V-author, abstract]. **CORE** (2309.12938): a proposer plus a
  ranker over 52 static checks; the ranker cut false positives by 25.8% [V-author, abstract].
- **Counterpoint**: Serena switched per-edit diagnostics off because multi-step edits pass through broken states (§1.3) [V].

### 2.2 What a diagnostic should say

- **Admissible alternatives carry the gain.** VeriHarness (Ray and Goyal, 2607.14167): under a four-call cap in 50 paired TextWorld
  games, feedback with location, observed value and admissible alternatives raised success from 14/50 to 36/50 for Qwen2.5-Coder-14B
  and 8/50 to 29/50 for Llama-3.1-8B; location and value alone stayed near the raw-diagnostic baseline; prose and keyed JSON did about
  equally well [V-author, abstract]. The loop is a text game, not code, so the transfer to scripts is [I].
- **Raw compiler text can hurt.** FeedbackEval (2504.06939): repair@1 of 49.2% with raw compiler feedback, 53.1% with minimal
  feedback, 57.9% with test feedback and 62.9–63.6% with expert or mixed feedback; gains plateau after 2–3 rounds [V-author].
- **More detail about the one error helps.** Krishnamurthi and Flatt (2606.01522): one deliberate type error per program, an agent
  repairing under four levels of message detail; "more detailed error messages generally improve an agent's ability to fix type
  errors" [V-author, abstract]. Per the paper body, as read by a research pass: qwen2.5-coder:14b via aider, 2,400 trials, success
  rising from 24.6/41.2% (untyped) to 40.7/63.4% (full unification context) in two bins, a median of one turn to success, and 97.9%
  of type-correct repairs passing the semantic tests. They propose a terse mode for humans and a detailed mode for agents.
- **Fewer, earlier, root-cause findings.** Generative Compilation (2607.13921, full text read by a research pass): reports held 5.5
  diagnostics on average against 13.8 after generation, and the median error was caught 3 lines after its source against 89
  [V-author]. Type mismatches were about 38% of detected errors.
- **Line numbers mislead.** Aider found models make off-by-one errors with line numbers and shows errors inside their enclosing
  function instead (aider.chat, 2024-05-22) [V-author].

### 2.3 How many repairs, and when to start fresh

- **One to three rounds.** Most gain arrives in the first two rounds for seven models including Llama 3.1 8B (2604.10508); the first
  3–4 iterations give most gains (2607.05197); most of 18 models lose 60–80% of debugging effectiveness within 2–3 attempts, and a
  fresh start at computed points restores it (Debugging Decay Index, 2506.18403) [V-author, abstracts].
- **Small models: facts, not their own broken code.** Iscan (2606.31511; frozen 0.5–1.5B models, 290 dead task-cell units): blind
  resampling beat bare-code retry by +18 net unlocks (p = 0.0021); code plus facts beat bare code by +18 and a generic placebo by +15;
  "falsification helped not as vocabulary or self-critique, but as comparison with external, executable counterexamples" [V-author].
  RLEF (2410.02089): models "struggle to improve code iteratively compared to independent sampling" until trained for it [V-author].
- **Strong models keep going.** Reasoning models keep improving over iterations; non-reasoning models do not (2606.17514) [V-author,
  abstract].
- **Weak models loop on the same prefix.** In Generative Compilation, Qwen3.5 9B needed more than 10 restarts in 40.9% of tasks (GPT
  5.3 Codex: 2.1%) and "often regenerate[s] the same erroneous prefix" [V-author].

### 2.4 Earlier feedback: in the stream and at decode time

- **Type-constrained decoding** (Mündler et al., PLDI 2025, 2504.09246; TypeScript HumanEval and MBPP; Gemma 2 2B–27B, DeepSeek Coder
  33B, CodeLlama 34B, Qwen2.5 32B): syntax causes only about 6% of compile errors; type constraining cut synthesis compile errors by
  74.8% and 56.0% on average (at least 54.8% and 27.3% for every model), against 9.0% and 4.8% for syntax-only; Gemma 2 2B repair
  pass@1 rose from 11.6 to 20.9 (HumanEval); median time +39–52% in an unoptimised implementation; 99.4% of tokens pass on the first
  sample [V-author, full text per a research pass]. It needs logit access.
- **Monitor-guided decoding** (Agrawal et al., NeurIPS 2023): a static-analysis monitor served through a language server raised
  compile rate by 19–25% at every scale from 350M to 175B, and SantaCoder-1.1B with the monitor beat text-davinci-003 on compile rate
  and next-identifier match [V-author].
- **Generative compilation** (2607.13921): a "sealor" completes a partial program so the compiler can check it during generation;
  works with black-box models. Mean compile-error rate 65.9% without feedback, 20.7% with post-generation feedback, 13.1% with
  generative compilation; better in 13 of 14 configurations; less runtime overhead (+170% against +283%) [V-author]. Caveat: Qwen3.5
  9B's functional correctness on one suite was lower (41.7% against 48.3%), and post-generation feedback gained more per restart for
  the first three restarts.
- **Counter-evidence: incompleteness.** Biagiola et al. (2606.21619; seven models, two languages, two constrainers): "when the
  constrainer is incomplete, unconstrained decoding significantly outperforms constrained decoding", with functional correctness cut
  by up to 97% through timeouts and low-probability text [V-author, abstract]. A schema-derived MLIR constrainer's heuristic layer
  falsely rejected valid output (−22.2 points) and reached 80% structural validity but about 20% functional correctness (2607.18254,
  single-author preprint) [V-author]. Structure is not intent.

### 2.5 Navigation tools, maps and code-picked cards

- **Xu** (2608.13568, preliminary; Claude Opus 4.8, Sonnet 4.6, Haiku 4.5): "On symbol-named localization the LSP costs tokens (+6% to
  +118%) and the agent ignores it when free"; on reference completeness "it buys precision but not token savings … it saves tokens only
  for the weakest model"; models "default to grep on localization (0-6% semantic use)"; on multi-file renames "a location-only LSP fails
  three-quarters of them by missing a call site", and a text-enriched one "recovers most of the gap but cannot close it, since a rename
  must touch comments and strings that semantic references exclude"; the recommendation is "an adaptive router keyed on task class,
  model capability, and lexical noise" [V-author, abstract]. Mandating semantic-first did not help (body, per a research pass).
- **SemNav** (2609.31176): deterministic language-server navigation feeding compact, issue-conditioned "semantic cards" to a small
  model; File Hit@10 from 68.33% to 82.67% with Gemma 4B; cards cut working context by 48.2%; downstream resolution 44.00% → 52.33%
  [V-author, abstract].
- **Typed context wins**: typed holes with the expected type and typing context (ChatLSP, OOPSLA 2024), static-analysis type context
  (CatCoder, up to +14.44% compile@k), graph context (RepoGraph, +32.8% relative on SWE-bench), language-server-retrieved definitions
  for test generation (LSPRAG, ICSE 2026) [V-author, abstracts].

### 2.6 What the evidence does not show

Nothing here was measured on SQF, SQS or `mission.sqm`, or on Plotroom's step shapes. The languages are Python, TypeScript, Java, Rust
and ML-style; one strong result is a text game; four sources are single-author preprints (2608.13568, 2607.18254, 2606.31511,
2604.10508). Every number above is a direction for Plotroom's own instruments (§5), not a prediction [I].

## 3. Teller today: planned, and missing

Already planned, and backed by §2 [V per the cited docs]:

| Plan | Where | Backed by |
| --- | --- | --- |
| Check after every model step that emits script or config; one finding per turn; stop on a repeat; R = 1/2/3 by effort | Doc 25 §7.2; doc 30 §4.2–§4.3; agent-runtime §6 | §2.1, §2.3 |
| Findings with expected/found, candidates, `requires`, `did_you_mean`, `arma_ism`, `fix`; recomputed allowed values | Doc 23 §13.4; doc 25 §7.2 | §2.2 (admissible alternatives) |
| Engine parity reports the first error only; lints are a separate level | Doc 23 §13.3 item 2 | §2.2 (root cause, fewer cascades) |
| Code picks cards by field kind, step, tokens under repair and diagnostic codes; weak models never fetch | Doc 30 §4.2; agent-runtime §8 | §2.5 (SemNav, ChatLSP; models under-use tools) |
| Dynamic enums at decode time; an optional, experimental arity grammar | Doc 30 §4.5, OQ9 | §2.4, with §2.4's completeness warning |
| Symbol index, references, rename; runtime-built names "cannot prove" | Validation §9; doc 31 §7.1; I37-31IDX | §2.5 (renames must reach strings) |
| Embedded library; an LSP binary only for external editors, later | Validation §9; doc 23 §13.2 | §1.2 (no warm-up, no waits) |
| Oracle, differential fuzzing, engine vectors, doc-example gates | Doc 23 §9, §13–§14 | §2.4 (false rejects) |
| Repaired results counted apart from first-pass ones | Doc 25 §7.2; `Admitted<T>.repaired` | §2.3 |
| Revision-stamped results with a "stale" badge | Validation §4 | §1.3 (Zed "may be stale") |

Missing [I]:

| Gap | What is missing | Evidence | Addressed in |
| --- | --- | --- | --- |
| TG1 | A delta rule: repair quotes only what the proposal introduced; moved lines remapped | Copilot, Hermes, SWE-agent; OpenCode's pitfall | §4.6 |
| TG2 | A sanitizer for every echoed mission name in model-facing text | Hermes; doc 23 §13.4 states the rule without a mechanism | §4.5 |
| TG3 | Which "one finding", when several exist; advisories never repaired | Severity-weighted choice (2508.14419); D011 | §4.6 |
| TG4 | Revision-bound, consumable handles for symbols, reference sets and fix menus | Qwen Code, Zed; `reference.explain_instance(handle)` has no freshness rule | §4.4 |
| TG5 | Model-facing where-used, outline and call-graph queries with text inline and "cannot prove" rows | Xu; SemNav; agent-runtime §8's family has none | §4.3 |
| TG6 | A repair-versus-resample rule per setup | Iscan, RLEF, Debugging Decay Index | §4.6 |
| TG7 | Checks during streaming, and a completeness rule for any constraint | Generative Compilation; Biagiola; doc 30 §4.5 cites distortion but not incompleteness | §4.8 |
| TG8 | Latency targets for Teller inside loops | Kiro's 35 ms; doc 52's UX standard covers only rate-limit waits | §4.9 |
| TG9 | Finding deltas as a rank feature and a stop rule ("the repair did not reduce findings") | Lanser-CLI (2510.22907); CORE's ranker | §4.6 |

## 4. Teller as Wilco's instrument (proposal)

### 4.1 Principles [I]

1. **One checker, four channels.** The Teller that squiggles the script editor also admits Wilco's proposals, renders its repair
   cards and answers its lookups. There is no separate "agent linter".
2. **Pure over a snapshot.** Every answer is a function of (snapshot revision, target profile, mod-set fingerprint, catalog version),
   deterministic and cacheable, so qualification runs replay exactly (validation §4; testing-strategy §7).
3. **Typed addresses, never offsets.** The model names items, fields and symbols; code finds spans (§4.4).
4. **Never silent.** Every answer is found, none or cannot prove; a lookup against an index older than the snapshot waits or says
   "stale"; it never answers from an old index (§4.5).
5. **Menus over prose.** Wherever code can list the valid next moves (allowed values, fix options, candidate symbols), the model picks
   from a menu of at most 7 plus `X none_fit` and `Q ask` (agent-runtime §6).
6. **Same path as the user.** Fixes, renames and deletions are the editor's own commands through plan → admit → commit; no Teller
   answer changes the document by itself.
7. **Mission text is data.** Everything quoted from a mission passes the sanitizer before a model sees it (§4.5; D006; doc 21 §9).

### 4.2 Four channels

| Channel | Who starts it | Carries | Surface level |
| --- | --- | --- | --- |
| Admission (push) | Code, on every proposal | The `Rejection`'s findings with allowed values, rendered as a repair card (§4.6) | TS1+ |
| Cards (push) | Code, per step | Catalog rows, field-context and diagnostic cards chosen by the four signals (doc 30 §4.2) | TS1+ |
| Menus (push) | Code, inside a repair or chat turn | Fix options, candidate symbols, allowed values, as PICK | TS1+ |
| Lookups (pull) | The model, where granted | The query family of §4.3 | TS2+ |

### 4.3 The tool family

Names are provisional until DG032 (option C, proposal) settles one family; every row is an existing `AgentTool` variant, so no tool
adds an effect (agent-runtime §2). "New" rows extend DG032's list.

| Job | Tool | Variant, effect | Input | Output card | Status |
| --- | --- | --- | --- | --- | --- |
| Diagnostics on demand | `script.check` | Check, None | text, `FieldKind`, profile | Findings (schema v1) as cards | Planned (doc 30 §4.4) |
| Explain a finding | `diagnostic.explain` | Lookup, ReadLocalReference | code | What, why, fix pattern, one checked example | Planned |
| Hover on a command | `script.command` | Lookup, ReadLocalReference | name, profile | Overload rows, availability per profile, risk class, card ids; or `not_registered` with `requires`, `did_you_mean`, `arma_ism` | Planned |
| Hover on a mission symbol | `reference.explain_instance` | Query, ReadDocument | handle | Kind, defining item and text, computed facts, open findings (doc 33 §6.1) | Planned; add freshness (TG4) |
| Completion candidates | `script.complete` | Lookup, ReadLocalReference | slot (field kind and position class: operand, operator, label, marker, class, script path), profile | A ranked menu of forms, never an unbounded list | Planned; reshape to a menu |
| Resolve a name | `mission.find` | Query, ReadDocument | name, kind (optional) | A handle; or a numbered candidate menu; or `not_found` with `did_you_mean` over profile-filtered names | New |
| Where used | `mission.where_used` | Query, ReadDocument | handle, scope (mission or campaign) | Rows with owning item, field, line text and reference kind; `cannot_prove` rows; shown and total | New (TG5) |
| Outline | `mission.outline` | Query, ReadDocument | scope, focus handle (optional) | A ranked mission map within the preset's budget | New |
| Script call graph | `script.calls` | Query, ReadDocument | script handle | `exec`, `call` and code-in-string edges both ways; unresolved paths as cannot prove | New |
| Quick fixes | `fix.options` | Query, ReadDocument | finding handle | A PICK menu of `FixId`s (validation §6) | New wrapper |
| Apply a fix | `fix.apply` | Propose, WriteDocumentUndoable | menu handle, option | `Proposal<FixCmd>` through admission | New wrapper |
| Rename | `mission.rename` | Propose, WriteDocumentUndoable | handle, new name | One undo group over every proven site; cannot-prove sites listed for the user to confirm | Command planned (validation §9); tool new |
| Safe delete | `mission.delete_unreferenced` | Propose, WriteDocumentUndoable | handle | A proposal, or a `Rejection` that lists the referencing sites (Serena's rule) | New |

Definition is not a separate tool: `mission.find` and `reference.explain_instance` return the defining item and its text, which is what
a model needs next (§2.5: location-only answers force follow-up reads). Reference kinds follow doc 31 §7.1 and I37-31IDX: identifiers
in code, string-typed arguments (marker, script path, class, sound, label, per the string-kind overlay), briefing `marker:` links,
`objStatus` and objective ids across HTML, stringtable keys, campaign `saveVar` names, `respawn_` prefixes and `description.ext` classes.
Stagnation in pull loops is caught by agent-runtime §9's (tool, args, result, revision) fingerprints.

### 4.4 Addressing: names and handles, never offsets

- **The model never supplies a column or a byte offset.** Positions are the weakest addressing mode (§1.4 row C). Mission content is
  addressed by `ItemRef` plus `FieldKind` (a trigger's condition, a unit's init line, a waypoint's activation, a briefing section);
  scripts by file handle plus an anchor code can resolve (an SQS label, a top-level function variable, or a quoted line the harness
  checks is a substring). Offsets and carets appear only inside code-owned diagnostics, for the UI.
- **Name-first resolution.** `mission.find("extract_lz")` resolves case-insensitively, as the engine does; several matches become a
  numbered menu with each candidate's kind and owner; none becomes `not_found` with `did_you_mean` (doc 23 §13.4).
- **Handles are witnesses.** A handle is an opaque id into a per-run table the harness owns, recording what it stands for and the
  `RevisionSet` of the entities read to produce it. It is valid only in its run and only while those entities are unchanged; per-entity
  revisions mean an unrelated edit does not stale it. A forged, foreign or stale handle is refused with a typed error whose text is the
  repair: "this answer is out of date: the mission changed since it was given; call `mission.find` again". In-process, a random id and
  a table lookup are unforgeable; Qwen Code needs an HMAC only because its handles cross a process boundary (§1.3). The same idea as
  agent-runtime §5's card tokens.
- **Menus are consumed.** A fix or candidate menu is stored with its handle and taken on use, Zed-style; a second `fix.apply` on the
  same menu is refused with "ask for options again". This prevents replaying a menu computed for an older state.
- This is the runtime counterpart of the witness and guard types studied in doc 62: holding the value proves the check ran [I].

### 4.5 The result card

Every Teller answer to a model is a typed card in doc 57's envelope (TM1: shown and total, exact omitted count, document revision,
evidence id, narrowing hint; "empty" distinct from "cut by budget"), rendered as numbered text lines, never raw JSON (Qwen, Copilot,
Hermes; §2.2 found JSON syntax brings no gain). Illustration, not a spec:

```text
WHERE USED  marker "extract_lz"  ·  rev 412 · profile cwr · 4 found, 1 cannot prove, all shown
1  marker "extract_lz"                    defined here (map marker)
2  trigger "Heli down" / On Activation    "extract_lz" setMarkerPos getPos heli1          [marker name in a string]
3  briefing / Plan section                <a href="marker:extract_lz">LZ</a>             [briefing marker link]
4  script extract.sqs, after #wait        "extract_lz" setMarkerPos getPos _lz            [marker name in a string]
?  script extract.sqs, after #loop        (format ["lz_%1", _i]) setMarkerPos _p          [cannot prove: name built at run time]
answer h7 · valid while these 4 items are unchanged
```

- **Tri-state.** `found`, `none` (the index proves no match) or `cannot_prove` (runtime-built names from `format` or concatenation,
  unknown mod content, a script path that resolves only at run time). "Unknown" never renders as "none" (OpenCode's pitfall).
- **Stamp.** Revision, profile and mod-set fingerprint on every card; a card built on a stale index says so.
- **Order and caps.** Stable order (definition first, then by item kind and id); caps come from the preset (§4.9) and always end with
  the exact omitted count and a narrowing hint ("add `scope = mission`").
- **Owner and text inline.** Each row names its owning item and quotes its line, clipped to 120 characters, so no follow-up read is
  needed (§2.5).
- **Sanitizer** (Hermes, adapted): CR and LF collapsed; control characters dropped; hidden characters (bidi, zero-width, tag, private
  use) rendered as visible markers by `plotroom-encoding` (validation §12); per-field caps (names 64 characters, quoted text 120); the
  card's own fence characters escaped so quoted text cannot close or open a section; every quote labelled as mission data (doc 21 §9).
  Names equal to our own template markers are escaped (agent-runtime §14).

### 4.6 Repair loops for scripts

For any step whose output is script text (a trigger condition or activation, an init line, a waypoint statement, an SQS or SQF file):

1. **Admit.** Strict admission of the model's output, then planning on the `Scratch` fork and the mandatory checks: `check_field` in
   the field's mode, plus lints at `error` severity for non-user origins (doc 23 §13.3 item 2; commands-undo-history §4.2).
2. **Baseline and delta (TG1).** Teller keeps each field's findings per revision. A finding is *introduced* when it is present after
   the proposal and absent from the baseline, keyed by (code, target, field path, typed facts). Multi-line fields and script files map
   the baseline through a line-shift map first (Hermes), so an old finding that moved is not new and one inside deleted lines drops out.
3. **Pre-existing parity errors are not the model's job.** A proposal that writes a field which already failed parity cannot be
   admitted unless it fixes that error; the harness does not ask the model to fix the user's code. It routes to an ask card ("this
   field already fails the engine check: fix it yourself, let Wilco try, or skip"), and a user choice is needed to let Wilco try.
4. **Choose one finding (TG3).** Only introduced findings qualify. Order: `EngineError`, then `ProfileError`, then `Warning`; parity
   before lint; earliest span first; code order last, for stability. `Advisory` findings are never repaired (D011: creative intent
   wins) and never block.
5. **Render one card.** Rule id, the typed address, the offending text (sanitized, clipped), why it fails (from the catalog), expected
   and found, and the recomputed allowed values or candidate forms as a menu when code can list them (doc 25 §7.2; §2.2). Mechanical
   fixes (quote a label, move a wait into SQS, swap in a profile overload) appear as fix options. At most one card, chosen by the
   finding's code (doc 30 §4.2). Model-shaped JSON (doc 23 §13.4) stays inside the harness.
6. **Repair or resample (TG6).** Per preset (D048), a failed attempt is followed either by a repair turn that shows the attempt and the
   finding, or by a fresh sample whose capsule omits the failed attempt and carries the finding as a fact ("`sleep` is not a command on
   this profile; waiting is done with `~` in SQS"). The default for setups without a measured preference: resample after the first
   failure on small local setups, repair on setups qualified for Compose [I; to measure, §5 TT-19].
7. **Stop.** The existing rules (a repeated finding, a repeated answer, R spent; agent-runtime §6) plus **no progress**: the attempt
   did not reduce the count of introduced blocking findings (TG9). Then `on_fail`.
8. **Fixed by deletion.** If a repair clears its finding by removing a statement, trigger, unit or file the step did not ask to remove,
   the admitted result carries a `ClearedByRemoval` note; under Confirm autonomy it waits for a click, and in every mode it is shown in
   the turn report. This turns Zed's prompt rule ("Don't remove code … just because you can't fix an error") into code.
9. **Record.** `Admitted<T>.repaired` counts turns; metrics keep repaired and first-pass results apart (doc 25 §7.2).

### 4.7 Repair loops for missions and campaigns

- Multi-entity proposals (Draft ChangeSets) are admitted as one batch; findings come from reference integrity, cardinality limits,
  profile policy, Teller's cross-entity rules (marker names used by triggers and scripts, SQS labels, objective ids, `exec` paths) and,
  for campaigns, the campaign compiler. Repair cards address items by `ItemRef` and offer the recomputed menu: "marker `lz_nort` does
  not exist; markers in this mission: A) `lz_north` B) `lz_east` … X) none fits".
- **Draft mode for qualified setups** [I]. A TS3 setup may run several steps on one `Scratch` fork with findings reported as
  information, not rejections, and one admission of the whole batch at the end. This is Serena's reason for switching per-edit
  diagnostics off, applied safely: nothing reaches history, the journal's commit records or disk until the batch admits. Which
  freedom level grants it, and under which autonomy, is doc 63's question (D024 item 2: autonomy governs waits; effort never changes
  checks); doc 63 §3.1 proposes FR6, with a dry-run admission of the draft.
- `mission.delete_unreferenced` and `mission.rename` let a strong setup restructure without text surgery; both land as one undo group.

### 4.8 Checks during generation (experimental)

- **Prefix verdicts (TG7).** A Teller function `prefix_verdict(FieldKind, prefix, profile) -> Viable | DeadEnd(finding)` checks a
  streamed script at natural boundaries: each complete SQS line (the engine's own unit, doc 23 §5) and each top-level `;` in SQF. On
  `DeadEnd` the harness cancels the stream (agent-runtime §5's cancellation tree) and resamples with the finding as a fact. It works on
  every backend that streams, including cloud ones. The script text sits inside a JSON string field, so the harness needs an
  incremental extractor for that one field. Restarts are capped (Qwen3.5 9B's same-prefix loops, §2.3), after which the post-hoc
  repair path of §4.6 takes over.
- **Completeness rule.** `DeadEnd` only on proof that no completion passes `check_field` in that mode: an unknown identifier may be a
  mission variable, an unfinished string may close later. The same rule binds any decode-time grammar or type monitor: it must accept
  a superset of the profile-valid programs for that field (mission variables, `_x` locals, string contents, every catalog overload,
  unknown or harness names handled exactly as the checker handles them). Timeouts, out-of-token results and forced low-probability
  text are typed outcomes that fall back to unconstrained generation plus the checker (§2.4).
- **Type-level monitors** need sampler access. The managed llama-server takes grammars but not a custom type check; a monitor would
  need the Plotroom-owned helper process that agent-runtime §3 proposes for any in-process engine. Measure against prefix verdicts
  first (doc 30 OQ9).

### 4.9 Token and latency budgets

Targets are proposals to confirm with the M2 benchmark that validation §14 item 5 and commands-undo-history §12 item 4 already plan.

| Item | Budget [I] | Why |
| --- | --- | --- |
| `check_field` on one field | p95 ≤ 5 ms | Runs inside every admission; doc 53's L0 class is < 0.1 s for all code steps |
| Lints on one script file, cross-entity rules for one proposal | p95 ≤ 25 ms | Kiro checks in under 35 ms [V-vendor]; an in-process check must not be slower |
| `mission.find`, `where_used`, `script.calls` on a warm index | p95 ≤ 10 ms | Index reads over `Arc<Snapshot>` |
| `mission.outline` | p95 ≤ 50 ms | Ranking plus a budget fit |
| Index rebuild after a commit | p95 ≤ 100 ms for a mission of p90 size (doc 35 corpus statistics) | Runs on a worker; readers of a newer snapshot wait or get "stale" |
| `prefix_verdict` per line or statement | p95 ≤ 1 ms | Must keep pace with streaming |
| Repair card | ≤ 200 tokens with its menu; about 50 without | One finding, one menu (agent-runtime §6: 7 options plus escapes) |
| Code-picked cards | ≤ 150 words each (doc 30 §4.4) | Already specified |
| Where-used rows | about 25–40 tokens per row; cap 5 (TS2) or 20 (TS3) | Text inline instead of 60–80-token bare locations (§1.2) |
| Outline | 400 (TS2) or 1,500 (TS3) tokens, binary-searched to fit (Aider) | A ranked map, not the whole mission |

Push content changes every turn, so it sits after the capsule's last cache breakpoint and never in the frozen prefix (doc 40 R2–R4;
agent-runtime §6). A clean admission adds nothing. Tool descriptions for TS2–TS3 are part of the frozen prefix and are counted in the
plugin-manager style cost display (doc 40 R5).

### 4.10 Weak and strong models: Teller surface levels

The owner's direction, read for Teller: the harness holds the knowledge (catalog facts, cards, menus, checks, the index), and a
stronger model earns more reach into it, never a weaker gate. The level is part of the setup's preset (D048) and is granted only where
qualification for the step kind allows (D037, D045); effort sets the budgets inside it (D024), and doc 30 §4.3 already allows model
lookups only at Thorough and Max, which this doc keeps. Doc 63 owns the ladder these rows join.

| Level | Who | Push | Pull | Steps and repair | Evidence |
| --- | --- | --- | --- | --- | --- |
| TS0 | No model (AI off) | — | — | The user sees the same findings, fixes and where-used in the editor | Validation §13 |
| TS1 | Every setup, including unqualified ones | Repair cards, code-picked cards, fix menus | None | Per-field steps; one finding per turn; resample-first on small setups; R by effort | §2.3; SemNav; Xu (weak models gain little from tools) |
| TS2 | Setups qualified for script Compose | As TS1 | `script.command`, `script.complete` as menus, `mission.find`, `reference.explain_instance`, `mission.where_used` (cap 5) | Prefix verdicts while streaming; repair-first if qualified | §2.2, §2.4 |
| TS3 | Strong setups qualified for multi-entity work | As TS1; findings informational inside drafts | The whole family of §4.3 with larger caps; the model chooses when to use it (no semantic-first mandate) | Drafts on a `Scratch` fork with one final admission; rename and safe-delete proposals; up to R = 3 repairs | §2.3 (reasoning models keep improving); Xu (route, do not mandate) |

- **Invariants at every level:** the same admission and checks; product scope; `UserIntent` for consent; the glass box (every
  finding, fix and handle visible in the decision inspector); no silent model switch (D023). The callable set stays registry ∩ chat
  mode ∩ step ∩ plugin grants ∩ role (agent-runtime §2), with the setup's surface level as one more intersection.
- **External agents** reach Teller only through Plotroom's opt-in, loopback MCP server (agent-runtime §15), which exposes the product
  tools of §4.3 at TS3 scope; qualification does not apply to a model Plotroom does not run, and their proposals pass the same
  admission. The primer skill (D027 L4) routes them to these tools.

### 4.11 Scope, safety and licences

- **No external servers, no downloads.** Every agent studied spawns language-server binaries, and several download them (§1.2). Wilco
  and the harness crates spawn no process and have no network (AGENTS.md; agent-runtime §1). Teller is a Rust library in the editor;
  the optional LSP binary of doc 23 §13.2 serves external editors and is never on Wilco's path.
- **Untrusted content.** Missions are downloads. The sanitizer (§4.5), the labelled quoting of doc 21 §9 and the injection fixtures of
  testing-strategy §9 cover Teller's model-facing text; a marker named like an instruction must change nothing (TT-05).
- **Licences.** Ideas only: OpenCode (MIT), Qwen Code (Apache-2.0), Hermes (MIT), Serena (GPL-3.0-or-later), Crush (FSL-1.1-MIT,
  source-available). No engine change is needed, so there is no engine-request entry.

## 5. Tests to write first

Each test is written and seen failing before its feature (AGENTS.md, "Test-First / Proof-First"), with the doc-comment and section
standards of AGENTS.md. Crates follow crate-map: `plotroom-teller` (L5), `plotroom-decide` and `plotroom-wilco` (L6), `plotroom-evals`.

| Id | Test | Crate | Proves |
| --- | --- | --- | --- |
| TT-01 | `repair_quotes_only_findings_the_proposal_introduced` | `plotroom-decide` | TG1 delta |
| TT-02 | `moved_preexisting_finding_is_not_reported_as_new` (insert lines above an old warning in an SQS file) | `plotroom-teller` | Line-shift remap |
| TT-03 | `finding_inside_deleted_lines_drops_out_of_the_delta` | `plotroom-teller` | Line-shift remap |
| TT-04 | `proposal_into_field_failing_parity_routes_to_ask_card` | `plotroom-decide` | §4.6 step 3 |
| TT-05 | `instruction_shaped_marker_name_is_neutralised_in_every_card` (newlines, fence characters, bidi and zero-width characters, 10 KB name) | `plotroom-wilco` | Sanitizer; adversarial |
| TT-06 | `repair_picks_engine_error_before_warning_then_earliest_span` | `plotroom-decide` | TG3 order |
| TT-07 | `advisory_findings_never_enter_a_repair_turn` | `plotroom-decide` | D011 |
| TT-08 | `stale_handle_is_refused_with_the_redo_instruction` (edit a read entity between issue and use) | `plotroom-wilco` | TG4 freshness |
| TT-09 | `forged_or_foreign_run_handle_is_refused` | `plotroom-wilco` | TG4 unforgeability |
| TT-10 | `unrelated_edit_does_not_stale_a_handle` | `plotroom-wilco` | Per-entity revisions |
| TT-11 | `fix_menu_is_consumed_by_first_apply` | `plotroom-wilco` | Zed-style menus |
| TT-12 | `where_used_reports_cannot_prove_for_format_built_marker_name` | `plotroom-teller` | Tri-state |
| TT-13 | `where_used_covers_string_args_briefing_links_stringtable_and_saveVar` | `plotroom-teller` | §4.3 reference kinds |
| TT-14 | `card_shown_plus_omitted_equals_total_and_empty_differs_from_cut` | `plotroom-wilco` | Doc 57 TM1 |
| TT-15 | `lookup_on_index_behind_snapshot_waits_or_says_stale_never_answers_old` | `plotroom-teller` | Principle 4 |
| TT-16 | `repair_that_deletes_unrequested_statement_is_flagged_cleared_by_removal` | `plotroom-decide` | §4.6 step 8 |
| TT-17 | `prefix_verdict_never_rejects_a_prefix_of_a_valid_program` (property test over the engine vectors, the fixture corpus and fuzzed completions, per profile) | `plotroom-teller` | Completeness |
| TT-18 | `surface_level_cannot_exceed_the_setups_qualification` (a TS1 setup cannot call `mission.where_used`; the refusal lists the step's tools) | `plotroom-wilco` | §4.10; D048 item 2 |
| TT-19 | Instrument arms in `plotroom-evals`: finding fields (location only; plus expected/found; plus allowed values; plus card), terse vs detailed rendering, R = 0–3, repair vs resample, push-only vs TS2 lookups; first-pass and repaired reported apart | `plotroom-evals` | §2.2–§2.5 on our steps |
| TT-20 | Benchmarks for §4.9's rows, reported per field kind (not a CI gate until M2 sets the numbers) | `plotroom-teller` | TG8 |

Determinism (every Teller answer computed twice on one snapshot is byte-equal) and the golden bytes of each card kind follow the
existing rules (validation §4; agent-runtime §6).

## 6. Design-gap candidates (listed, not filed)

1. **Delta rule for model-facing findings** (TG1), including the pre-existing-parity route of §4.6 step 3. Touches doc 25 §7.2,
   agent-runtime §6, commands-undo-history §4.2.
2. **Sanitizer contract for Teller text** (TG2): which fields, which caps, which escaping; shared with plugin results (doc 57 TE-G9).
3. **Repair priority and advisory exclusion** (TG3). Touches doc 25 §7.2.
4. **Freshness-bound, consumable handles** for `reference.explain_instance`, where-used sets and fix menus (TG4). Touches DG032.
5. **Name-addressed query tools** (`mission.find`, `mission.where_used`, `mission.outline`, `script.calls`, `fix.options`,
   `fix.apply`, `mission.rename`, `mission.delete_unreferenced`) as an extension of DG032 option C (TG5).
6. **Teller surface levels TS0–TS3 in the preset schema** (doc 55 §3.3) and as an intersection of the callable set (agent-runtime §2);
   depends on doc 63.
7. **Repair-versus-resample policy per setup** (TG6); relates to DG021 (adaptive K) and DG016 (repair accounting).
8. **"Fixed by deletion" admission note** and its autonomy behaviour (D024).
9. **Draft mode** on a `Scratch` fork with one final admission for TS3 setups; which freedom level and which autonomy (doc 63 §3.1
   and §6 propose FR6 under the existing autonomy dial; D024).
10. **Prefix verdicts during streaming** (TG7), experimental, with a restart cap.
11. **Completeness rule and false-reject gate for any decode constraint**; amends doc 30 §4.5 (TG7).
12. **Latency targets for Teller in loops** (TG8), set by the M2 benchmark and tied to doc 52's UX standard and doc 53's classes.
13. **Finding deltas as a rank feature and stop rule** (TG9); touches doc 25 §7.3.
14. **Reference kinds for where-used and rename**: confirm that I37-31IDX covers stringtable keys, campaign description text and
    `mission.sqm` trigger texts, not only the kinds validation §9 lists.

## Open questions

1. **Measurement:** does the push-only TS1 surface beat TS2 lookups for a 4B local setup on script Compose, on first-pass and repaired
   rates and tokens? (TT-19) [U]
2. **Measurement:** which finding fields carry the repair gain on SQF and SQS (TT-19's ablation)? The strongest external result is
   from a text game (§2.2) [U].
3. **Measurement:** for 3–4B setups, is resampling with the finding better than repair after one failure, as for 0.5–1.5B models? [U]
4. **Design:** does a user-started "fix the script errors" workflow count as the click for every pre-existing parity error it
   touches (§4.6 step 3), or does it ask per field? [I]
5. **Design:** do TS3 drafts need their own undo granularity (one group per draft, or per step as under Auto)? [I]
6. **Technical:** can `prefix_verdict` be complete for SQF without a full partial-program sealor, given top-level `;` boundaries and
   nested code strings (doc 31 §7.2)? [U]
7. **Technical:** how large may a where-used answer get on a big campaign before the cap and narrowing hint hurt more than help? [U]
8. **Owner:** should external agents over MCP get the TS3 query family by default, or only the TS2 subset until the user widens it in
   Settings? [I]

## Findings for sibling docs (reported, not fixed)

- **Doc 30 §4.5** says a grammar "cannot hold types" and that gains are small (doc 25 §2.4). §2.4 here shows large gains once the
  constraint is type-level and complete, and a large loss when it is incomplete; the section should cite both.
- **Agent-runtime §8** lists no where-used, outline or call-graph lookup in the tool family; doc 10 §6 proposed a generic
  `mission.query`.
- **Validation §9**'s "Model-shaped diagnostics" row has no delta, priority or sanitizer rule.
- **Doc 23 §13.2** names crates `ofp-script*`; crate-map already uses `plotroom-script`, `plotroom-script-catalog` and `plotroom-teller`,
  and AGENTS.md forbids the game's marks in crate names. Doc 23 §15 P3 still names `validate_script`, which DG032 would retire.
  DG032 itself repeats the old name ("`check_field` stays the internal Rust function in `ofp-script`", Context and Recommended
  resolution); crate-map places `check_field` in `plotroom-script` (added in review).
- **DG032** option C's `reference.explain_instance(handle)` has no freshness or forgery rule for its handle.

## Sources

All read on 2026-09-28. **Code** at the commits of §1.1, each as `https://github.com/<repo>/tree/<full commit>`:
anomalyco/opencode `03e67171ab2dc1e7f16e8cebfbc7f778f61b89f0` (plus PR <https://github.com/anomalyco/opencode/pull/23771>);
QwenLM/qwen-code `3f5ae3ffeb7264f236038eef91256a3310361d3c`; charmbracelet/crush `056387be7ac39e5e6f47be046d4390413daae2ee`;
oraios/serena `7a2968335f2198b966864de1ce3655c8e485a653`; zed-industries/zed `d3ccd5719486b39b6c18cf37a06233ef9833d6d8`;
microsoft/vscode-copilot-chat `5863f5a7088958050792b5dccbe8b46c6e13eccc`; cline/cline `252082b9e93b4f91253876391e35b4c13326f5e6`;
continuedev/continue `5522c6f44ca0ac3528b37244818fbfa39b5af470`; letta-ai/letta-code `f378d20d90505aad6c99c290f62326b18397d7b5`;
NousResearch/hermes-agent `e98be8a328050f1fc978fa4f0f27614801183c56`; isaacphi/mcp-language-server
`e4395849a52e18555361abab60a060802c06bf50`; SWE-agent/SWE-agent `3ea751c087f32b16e039a2233dd6eefecef325d5`; Aider-AI/aider
`5dc9490bb35f9729ef2c95d00a19ccd30c26339c`; negative results: openai/codex `abc8f0c9a1ba5754f4bf71343f50283a7a72dcff`,
google-gemini/gemini-cli `2fe7c2d3f065dc40ad573d50b2091116f8a4aa18`, MoonshotAI/kimi-cli `9ab1286`, block/goose
`04ed836c8cde23e540cc77d256992e00be99298b`.

**Vendor pages:** <https://code.claude.com/docs/en/plugins-reference> (`lspServers`);
<https://kiro.dev/blog/empowering-kiro-with-ide-diagnostics/>; <https://kiro.dev/docs/tools/code-intelligence/>;
<https://aider.chat/2024/05/22/linting.html>; <https://aider.chat/docs/repomap.html>; `strict-path`, the owner's public crate:
<https://crates.io/crates/strict-path>.

**Papers** (arXiv abstract pages unless stated): SWE-agent 2405.15793 and its NeurIPS 2024 paper,
<https://proceedings.neurips.cc/paper_files/paper/2024/file/5a7c947568c1b1328ccc5230172e1e7c-Paper-Conference.pdf>; type-constrained
code generation (PLDI 2025) 2504.09246; monitor-guided decoding (NeurIPS 2023) 2306.10763 and <https://github.com/microsoft/monitors4codegen>;
Generative Compilation 2607.13921; The Alignment Problem in Constrained Code Generation 2606.21619; schema-derived constrained decoding
for MLIR 2607.18254; VeriHarness 2607.14167; FeedbackEval 2504.06939; Type-Error Ablation and AI Coding Agents 2606.01522;
Falsification, Not Exposure 2606.31511; RLEF 2410.02089; How Many Tries Does It Take? 2604.10508; Is Three the Magic Number?
2607.05197; Debugging Decay Index 2506.18403; iterative feedback loops (Zhang and Kothari) 2606.17514; static analysis as a feedback
loop 2508.14419; CORE 2309.12938; Does a Language Server Save Tokens for Coding Agents? (Xu) 2608.13568; SemNav 2609.31176;
RepoGraph 2410.14684; CatCoder 2406.03283; LSPRAG 2510.22210; typed holes (ChatLSP) 2409.00921; Lanser-CLI 2510.22907. Each at
`https://arxiv.org/abs/<id>`.

**This repository:** `AGENTS.md`; docs 10 (§6), 21 (§9), 23 (§5, §9, §13–§15), 25 (§7.1–§7.3), 30 (§4.1–§4.6, OQ9), 31 (§7), 33 (§6.1),
35, 40 (R2–R5), 52 (UX1–UX9), 53 (latency classes), 55 (§2.1, §3.3), 57 (TM1, TE-G9); `docs/architecture/` agent-runtime (§1–§9, §11,
§14–§15), commands-undo-history (§4, §11, §12), validation-and-lints (§2–§6, §9, §12–§14), crate-map; D011, D023, D024, D027, D037, D045,
D048; DG016, DG021, DG032; I37-31IDX.

## Verification notes

### 2026-09-28, author checks at write-up

- **Re-read in code by the author at the pinned commits:** OpenCode `lsp/diagnostic.ts#L3-L27`, `tool/write.ts#L18`, `#L74-L90`,
  `tool/edit.ts#L196-L201`, `tool/lsp.ts#L11-L35`, `#L49-L109`, `tool/registry.ts#L247`, `effect/runtime-flags.ts#L10-L14`, `#L22`, `#L45`,
  `lsp/client.ts#L13-L18`; Qwen Code `native-lsp-service.ts#L84-L92`, `#L1494-L1509`; Hermes `reporter.py#L14-L40`,
  `range_shift.py#L1-L20`; Zed `apply_code_action_tool.rs#L89-L108` (the list is taken before the index is checked, so any call
  consumes it); Serena `tools_base.py#L425-L447`; Crush `lsp_helpers.go#L24-L46`; SWE-agent `edit#L94-L119`; Copilot
  `editFileToolResult.tsx#L79-L100`. The clones' `HEAD`s match §1.1.
- **Re-read on the page by the author:** the abstracts of 2608.13568, 2607.14167, 2606.01522, 2609.31176, 2607.13921, 2606.21619 and
  2606.31511, and the Kiro blog post (date, 35 ms, 29%, about 4×).
- **Resolved conflicts:** a research pass reported per-arm rename figures for Xu (location-only 0.67, text-enriched 0.83 pass@1); the
  abstract says a location-only server "fails three-quarters" of multi-file renames. This doc quotes the abstract and leaves the body
  figures unused. VeriHarness measures TextWorld games, not code; §2.2 says so. Biagiola et al.'s abstract gives seven models and two
  languages, used here.
- **Corrected at write-up:** the first TL;DR bullet now names the exceptions to "push by default" (Zed's agent and Serena offer pull
  tools only); the type-constrained decoding figures are averages, with each model's minimum given (§2.4); doc 10's `mission.query`
  proposal is in its §6, not §7; `reference.search` searches knowledge, not missions, so TS3 no longer cites it as mission text search.
- **Taken from research passes, not re-read by the author:** other file:line citations in §1.2–§1.3 (only the clones' commits were
  confirmed); the full-text numbers of 2504.09246, 2607.13921, 2606.01522 and 2607.18254; the abstracts of the remaining
  papers; Claude Code's documentation. They are marked by source class and should be re-read before any is used as a decision input.
- **Not verified:** any Plotroom effect of any proposal; every budget in §4.9.
- **Folding steps, not done here:** a row for this doc in `docs/README.md`; the sibling-doc findings above; cross-links with docs 62
  and 63 once they exist.
- **Hygiene:** public sources only; the owner's `strict-path` crate is public; no private or unpublished project is named, and no
  local path, user name or key appears.

### 2026-09-28, review of docs 61–63

- **Clones:** every `HEAD` matches §1.1; a fresh fetch of OpenCode's `dev` branch is still `03e67171ab`.
- **Spot-checked and confirmed at the pinned commits:** OpenCode `tool/edit.ts#L196-L201`, `tool/write.ts#L18`, `#L74-L90`,
  `lsp/diagnostic.ts#L3-L27`, `tool/lsp.ts#L11-L35`, `#L108`, `tool/registry.ts#L247`, `effect/runtime-flags.ts#L10-L14`, `#L22`,
  `#L45`, `lsp/client.ts#L13-L18` (150 ms, 5 s, 10 s, 3 s, 45 s), `tool/truncate.ts#L14-L15`, `tool/read.ts#L117-L120`,
  `lsp/lsp.ts#L377-L441` (every request `.catch`es to `null` or `[]`); Qwen Code `native-lsp-service.ts#L84-L92`, `#L1456-L1509`
  (random 32-byte key per connection, HMAC-SHA256 over name, item, digest and version); Hermes `reporter.py#L14-L40`; Zed
  `apply_code_action_tool.rs#L89-L108`; Serena `tools_base.py#L425-L447`; Crush `lsp_helpers.go#L24-L46`; Copilot
  `editFileToolResult.tsx` (`AutoFixDiagnostics` at `#L81`, 1 s wait at `#L150`, 20 per file at `#L98`, `modelNeedsStrongReplaceStringHint`
  at `#L135`); SWE-agent `edit#L94-L119`.
- **Confirmed on the page:** the abstracts of 2608.13568 (all six quoted phrases, the three models), 2607.14167 (all figures),
  2609.31176 (all figures), 2504.09246 ("more than half"); the Kiro post (2026-01-14; 35 ms, 29%, about 4×); Claude Code's plugins
  reference (`lspServers`, `.lsp.json`, per-server `diagnostics` defaulting to `true`).
- **Corrected in this review:** (1) Zed row, §1.3: the two quoted guidelines are in `diagnostics_tool.rs#L39-L40` (the tool
  description), not in `system_prompt.hbs#L93-L96`, which says "Make 1-2 focused attempts … then defer to the user" and "Never
  simplify or discard meaningful code just to silence diagnostics"; both are now cited for what each says. (2) TL;DR: the
  one-finding repair is planned, and it matches the arm that won external measurements; "is the measured winner" overstated it.
  (3) TL;DR: "Teller already owns the stronger channel" now says it is designed, not built. (4) §1.2: `<op>` rendered as an HTML
  tag and vanished; the source expression is quoted instead. (5) §4.7 and §6 item 9: "rung" became "freedom level", doc 63's term
  (doc 63 avoids "rung", which five other docs already use), with doc 63's FR6 answer. (6) The sibling paragraph now says docs 62
  and 63 exist and where each connects. (7) Sibling findings: DG032 repeats the `ofp-script` crate name.
- **Not re-verified:** the full-text numbers of 2607.13921 (no HTML version is published), 2606.01522, 2606.31511 and 2607.18254;
  Serena `symbol_tools.py` and `text_utils.py`, Crush `diagnostics.go` and `client.go`, Letta, Cline, Continue and
  mcp-language-server line ranges.
- **Consistency with docs 62 and 63:** doc 63 §3.1 grants TS2 lookups from FR5; this doc keeps doc 30 §4.3's rule that model lookups
  run only at Thorough and Max effort. Doc 63 now states that the effort gate still applies (its §3.1).
