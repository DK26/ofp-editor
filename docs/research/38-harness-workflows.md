# Workflows in the Plotroom harness

Research doc 38 for Plotroom (`ofp-editor`). Research date: 2026-09-27. Audience: contributors and LLM coding agents; it is meant to be read alone.
Question answered: how should Plotroom define, run, show, test and distribute **workflows**, the typed multi-step procedures through which
Wilco (the optional AI co-pilot) and the AI-off editor features do real work, and what may we learn from Claude Code, Codex and workflow engines?

**Status.** Proposal-only. **Epistemic legend.** **[V]** verified: Claude Code facts against its public docs, Codex facts against the pinned
source or its live docs, engine facts against the cited pages (all fetched or re-read 2026-09-27); repo docs by section. **[I]** our
inference; **every schema, type, name, number and UX in §2–§10 is [I] unless marked.** **[U]** unknown.
**Citation aliases.** `CX:` = `openai/codex@e72da2b538:` (committed 2026-09-26), as in doc 22. `CC:` = `https://code.claude.com/docs/en/`.
**Relation to sibling docs.** Doc 21 §6 defines the workflow shape (`WorkflowDef`, `StepKind`, `OnFail`, `Control`) and its rules; doc 25
the campaign stages S0–S9, step shapes, decision records, staleness and merge; doc 22 T0 packs (`workflows/*.toml`), plugin tool steps and
trust; doc 30 §4 the knowledge stack; doc 33 Standing Orders; `prompts/design-sensibility/` the lenses. This doc turns them into **one
definition format, one runtime and one UX**, and proposes answers to doc 21 open question 7 and doc 25 open questions 7 and 10.
**Hygiene.** All text is our own. Nothing is copied from Claude Code's prompts, documentation or scripts; Codex is cited by pinned path.

## TL;DR

- **Yes, borrow from Claude Code and Codex, as ideas.** Patterns are free to reuse. Claude Code is proprietary: we learn only from its
  public docs and never copy its prompts, doc text or scripts. Codex is Apache-2.0: code may be ported into our GPL-3.0-or-later tree with
  the license, its NOTICE, change notices and a provenance record, though most candidates need rewriting for our no-panic rules (§1.3).
- **Three answers to "who holds the plan".** Claude Code's dynamic workflows put orchestration in a JavaScript script Claude writes per
  task [V]; Codex keeps reliable flows as fixed Rust tasks and lets users extend only prose (skills) and guards (hooks) [V/I]. Plotroom:
  **workflows are typed data (TOML) interpreted by a Rust runtime**. The model never writes control flow; chat may start and parameterise
  a workflow, never redefine it (doc 21 §6.1).
- **One format for built-in and pack workflows** (§3): metadata with a model policy, typed inputs, budget ceilings, steps from a closed set
  of twelve kinds, outputs and a completion gate. A model step cannot exist without its check and fallback; repair is a bounded attribute.
- **A typed decision journal** (§4): pure steps are recomputed, recorded steps (model, user, plugin) settle once and are reused, effects
  commit as idempotent undo groups. Resume never re-executes a settled model call or a Preview; a changed catalog marks steps Stale.
- **The user directs mid-run.** `ask` and `approve` steps park the run behind a one-shot, validated card. Claude Code workflows take no
  input mid-run and Codex asks only from its root thread [V]; here "pick a premise" (S1) and "approve the outline" (S3) share one run.
- **Deterministic fan-out.** `map` steps iterate over stable element ids, seed items from their keys and admit in key order, so results do
  not depend on concurrency (answers doc 25 OQ7). Model-spawned sub-agents and agent teams are rejected.
- **Glass-box UX** (§5): palette actions (`/populate-town`), a plan card with steps and budgets, a run panel by phase, one-tap cards, a
  "why" inspector per step and a read-only run graph. The runtime writes the checklist; the model has no plan tool.
- **Policy hooks are built in and typed** (§7): admission, autonomy, provenance, budget, and a completion gate with "stop hook" semantics.
  Packs may only tighten, through declarative lints. No shell, HTTP, MCP-tool, prompt or agent hooks exist.
- **Trust follows provenance.** Only the user's own gesture or typed request starts a model workflow, approves a plan or accepts egress.
  Pack workflows are hash-pinned and re-reviewed on change; pack roles only narrow.
- **Tested like durable-execution code** (§6.4): golden journals replayed in CI, cassettes keyed by capsule hash, a faux model walking every
  menu escape, and a crash at every journal entry that must resume to the same document with zero extra model calls.
- **External agents use the same doors** (§9): `ofp-mcp` lists and starts workflows and, where a workflow opts in, lets an external agent
  answer decision points through the same admission. Plans and questions are still answered in the editor. (The MCP server in
  v1, `workflow.decide` after v1: answered 2026-09-27 → [D036](../decisions/D036-v1-contents-and-release-split.md) item 6.)
- **Build a small interpreter; depend on no workflow engine** (§4.7). duroxide (MIT, embeddable) is the reference design.

## 1. What we borrow, and from whom

### 1.1 Borrow table

Evidence for the Claude Code, Codex and engine cells is listed under Sources; the last two columns are [I].

| Concept | Claude Code [V] | Codex [V] | Workflow engines [V] | Plotroom adaptation | Verdict |
| --- | --- | --- | --- | --- | --- |
| Who owns control flow | A background runtime runs a JS script Claude writes for the task; it can be saved as a command (`CC:workflows.md`) | Fixed Rust tasks (`TaskKind` Regular, Review, Compact at `CX:codex-rs/core/src/state/turn.rs#L67-72`; the `SessionTask` trait at `CX:codex-rs/core/src/tasks/mod.rs#L170-202`); no user-definable step graph [I by absence] | ASL, BPMN, n8n, ComfyUI interpret declarative graphs; Temporal and Restate replay user code | TOML definitions interpreted by a Rust runtime; chat parameterises only | Adapt |
| Typed step output | `agent()` with a JSON schema; up to 5 validation attempts; a provably contradictory schema fails before start | `update_plan` and `request_user_input` specs are `strict: false`; review output parsed leniently | DSPy signatures; ChatAdapter falls back to JSONAdapter | Shape + answer schema + mandatory check; one-finding repair; strict admission (doc 21 §6.2, §8.2) | Adapt |
| Input mid-run | None; the docs advise one workflow per stage for sign-off | `request_user_input` only from the root thread, by default only in Plan mode | LangGraph `interrupt`, Temporal Update validators, Restate awakeables, Step Functions task tokens | `ask` and `approve` step kinds with one-shot validated tokens (§4.1) | Adopt the engines' model |
| Approve before running | Pre-launch card with phases and "view raw script"; "don't ask again" only for bundled, saved or plugin workflows | Plan mode ends with "Implement this plan?", including a clear-context option (`CX:codex-rs/tui/src/chatwidget/plan_implementation.rs#L9-21`) | — | Plan card (§5.2); "always" only for built-in or installed definitions; execution gets the typed plan, not the chat | Adopt |
| Visible checklist | `/workflows` view: per-phase agents, tokens, time; drill-in; pause, stop, restart | Model calls `update_plan`; UI shows "n/m complete"; "one step in progress" stated but not enforced (`CX:codex-rs/core/src/tools/handlers/plan.rs#L87-98`) | n8n and Houdini TOPs show per-node and per-item state | Runtime-written checklist with gate states; no model plan tool | Adopt UI, reject model authorship |
| Determinism and resume | `Date.now()`, `Math.random()` throw; resume replays in start order; the first changed or failed agent and every later one re-run | JSONL rollouts with resume and fork; `thread/revert` rewrites history but not local files | Temporal, Restate, duroxide journals; Inngest and Cloudflare key steps by name | Journal keyed by (run, step, item, attempt); settled entries reused; staleness by input digest | Adopt, finer-grained |
| Fan-out | `pipeline()`, `parallel()`; 16 concurrent agents by default, 4,096 items per call, 1,000 agents per run | `spawn_agent` family; 6 threads, depth 1 (v1) or 4 threads (v2) by default | Airflow `max_map_length` 1024; ASL `MaxConcurrency`; Temporal advises ≤ 1,000 children per parent | `map` over stable keys, key-order join, code-owned caps | Adapt; skip model-spawned agents |
| Budgets | Effort levels; the size guideline is advice, runtime caps are hard; advisory "Large workflow" warning | Goal token budgets end in a visible `BudgetLimited` status; reasoning effort per mode and per child | LangGraph `recursion_limit`; ASL timeouts and heartbeats | Effort is a budget bundle (doc 21 §7.1); nested ledger; caps only tighten | Adopt |
| Skills | `SKILL.md`; description always in context, body on use; `` !`cmd` `` shell injection | `SKILL.md`; catalog ≈ 2% of the window, shrunk evenly; shadow-mode lexical selectors (`CX:codex-rs/ext/skills/src/dynamic_skill_selector.rs#L1-58`) | — | Steps declare knowledge and code injects it; skills execute nothing (doc 22 §2.1) | Adopt format, adapt selection |
| Roles | Subagents with tools, model, `maxTurns`, permission mode | Roles may only narrow; hostile-role test (`CX:codex-rs/core/src/agent/role_tests.rs#L391-521`) | — | The user binds roles to models (doc 21 §7.2); pack roles narrow only | Adopt narrowing |
| Guards | 33 hook events, five handler types; exit 2 blocks on blocking events | Hooks run only when trusted by content hash; a blocking Stop hook's reason becomes a continuation prompt (`CX:codex-rs/hooks/src/events/stop.rs#L312-319`) | Temporal activity timeouts; BPMN boundary events | Built-in typed policy points (§7); hash-pinned pack trust (§6.2) | Adapt semantics, reject runnable hooks |
| Commands | `/name`, `/plugin:name`, structured `args`; project beats personal | `SlashCommand` enum in presentation order with availability predicates (`CX:codex-rs/tui/src/slash_command.rs#L7-86`) | — | Typed palette built from definitions; unavailable entries greyed with a fix | Adopt |
| Combining approvals | Permission modes | `AppToolApproval::restrict_to`, a conservative meet (`CX:codex-rs/config/src/mcp_types.rs#L36-50`) | — | Meet of autonomy dial, workflow effects and plugin grant | Adopt; port candidate |
| Provenance | `ultracode` starts a workflow only from a prompt the user typed; script-computed prompts are not user requests; agent messages cannot consent | A goal's objective is framed as user-provided data | — | Every capsule segment carries its origin; only user gestures reach Dispatch or approval | Adopt |
| Honest reporting | Claims verifiers could not check are listed as unverified, not refuted | Review falls back to plain text when JSON fails | — | "Not run" is never "pass" (doc 21 §6.5); prose is never shown as findings | Adapt |
| Versioning | Only edits to the saved script | — | Temporal pinned runs and replay tests; AWS immutable versions | Runs pinned to a definition snapshot; upgrade after a replay check (§6.3) | Adopt the engines' model |
| Recorded outputs | — | wiremock and insta (doc 10 §2.13) | Temporal mocks and time skipping; DSPy request-hash cache; n8n pinned data | Cassettes keyed by capsule hash; golden journals (§6.4) | Adopt |
| Left out [I] | Model-written orchestration; agent teams (a lead auto-approves a teammate's plan without review); auto memory; `opusplan`-style model switching; skill shell injection | Model-spawned sub-agents; model-managed context (`get_context_remaining`, `new_context`); model-judged completion (`update_goal`); `$ARGUMENTS` prompt templates (deprecated by Codex itself) | Durable-execution engines as dependencies (§4.7); bpmn-js; runtime prompt optimisation | — | Skip |

### 1.2 Licensing notes (not legal advice; doc 02 governs)

- **Claude Code** is proprietary. Its docs are public but not openly licensed, so we take concepts only: no prompts, doc wording, bundled
  scripts, schemas or UI text, and no reverse engineering. We cite pages by URL and use the name only to refer to the product.
- **Codex** is Apache-2.0 (`CX:LICENSE`; `CX:NOTICE#L1-6` credits OpenAI and Ratatui, whose derived TUI code is MIT and keeps its own
  copyright lines if ever ported). Apache-2.0 code may enter a GPL-3.0-or-later work in
  that direction only (doc 10 §5). A port ships the license and NOTICE contents in our third-party notices, marks modified files, keeps
  copyright lines, cites the `CX:` path in a comment and is recorded in a provenance list (Open question 9). No trademark rights: no
  "Codex" in our names. Code that breaks our rules is rewritten, not ported: direct slicing (`CX:codex-rs/skills/src/parser.rs#L125`,
  `CX:codex-rs/ext/skills/src/render.rs#L255`, `#L432-438`) and panics (`CX:codex-rs/core/src/tasks/review.rs#L113`). Candidates: the
  `restrict_to` meet, the role-authority test as a property-test model, the catalog budget algorithm, a BM25 selector.
- **Engines.** Ideas are free. The States Language spec carries an MIT-style notice; DSPy (MIT) may serve offline tooling only; duroxide
  code (MIT) needs attribution if taken; obelisk (AGPL-3.0-only) and the Restate server (BSL 1.1) never become dependencies.

## 2. Principles

1. **Workflows are data; the runtime owns control flow.** No model, pack or chat message can add a step kind, loop or branch the schema
   does not allow. Wilco has no tool that creates or edits a definition (doc 21 §1.3's `AgentTool` has no such variant); people author
   TOML, and the loader validates it as data (§6.2).
2. **Product tools only.** Steps call registered editor functions, typed `AgentTool`s (doc 21 §1.3) or plugin tools through their grant;
   no shell, file, web or process step exists, and no hook runs code (§7).
3. **One bounded decision per model step**: Pick, Fill, Compose or Draft (doc 21 §3), code-built menus with `X` none fit and `Q` ask me, a
   check right after, one-finding repairs and a fallback. A failed large step is split, never escalated.
4. **Code owns facts, state and "done".** The harness holds document, journal and story bible; capsules are rebuilt fresh (doc 21 §8.1);
   only the completion gate reports Done.
5. **Glass box and the user directs.** Every step is visible before, during and after a run; every generated element links to its
   decision; questions and approvals are steps; human edits and pins win.
6. **Deterministic, resumable, testable.** Seeds come from the runtime and stable keys; the journal makes runs resumable; path tests, crash
   tests and recorded model answers exercise every definition.
7. **AI off still works.** `optional` workflows complete with seeded defaults; the no-model run is the baseline (doc 21 §1.1 rule 7).
8. **Only the user's own gesture is consent.** Workflow text, plugin output, other agents' messages and mission text never start a model
   workflow, approve a plan or accept egress.

## 3. The workflow definition format (proposal-only)

### 3.1 File skeleton

One file per workflow, UTF-8 TOML, at most 64 KiB [I: parser-safety cap], filling doc 21 §6.1's `WorkflowDef` and doc 22 §4.2's step
syntax. The id reuses doc 22 §7.2's manifest example (`workflows = ["workflows/voice-radio-chatter.toml"]`).

```toml
format = "plotroom-workflow/1"            # schema major; unknown keys anywhere are refused (§6.2)
[workflow]
id = "radio-voice/voice-radio-chatter"    # "<pack>/<name>"; built-ins use "core"; never reused for other behaviour
version = "1.2.0"                         # semver; the loader also stores a content hash
title = "Write and voice radio chatter"
description = "Adds short radio lines to the selected triggers and voices them."   # ≤ 1,024 chars
model_policy = "required"                 # "forbidden" | "optional" | "required" (doc 21 §6.3)
profiles = ["cwa199", "cwr", "ce"]        # target profiles its output is valid for (doc 23 §14)
scope = "selection"                       # "selection" | "mission" | "campaign": what a run may read and write
entry = ["palette", "context-menu:trigger"]   # also "chat", "wizard:<id>"
external = "none"                         # "none" | "start" | "start-and-decide" (§9)
requires = ["radio-voice >= 1.2"]         # plugins whose tools steps use (doc 22 §4.2)
preflight = ["catalog"]                   # blocks only this workflow, with a one-click fix (doc 21 §6.2 rule 5)
completion_gate = ["text.lints", "radio.slots-filled"]   # registered gate ids; the only producer of Done
[inputs]                                  # host-registered types; JSON Schemas generated with schemars
triggers = { type = "trigger-set", required = true, from = ["selection"] }   # required inputs never default (doc 21 §4.2)
tone = { type = "tone-preset", default = "terse" }                            # defaults appear as editable assumption chips
[budget]                                  # ceilings only; the tightest limit wins (doc 22 §3.2)
turns = { quick = 4, standard = 12, thorough = 30, max = 30 }
[[step]]                                  # steps run in file order; `when` skips a step, it never jumps
id = "voice"                              # authored, unique, never templated: the journal key
kind = "tool"                             # one of twelve kinds (§3.2)
uses = "radio-voice/synthesize_lines"     # doc 22 §3.1 egress-card rules apply
optional = true                           # plugin disabled or offline: skipped with a reason
in = { lines = "step.lines" }             # workflow inputs or admitted outputs only
[outputs]
undo_group = "step.apply.undo_group"      # what the run reports (and returns over MCP, §9)
```

- **Bindings** name a workflow input or an **admitted** output of an earlier step. There is no syntax for raw model text, so doc 21 §6.2
  rule 1 ("no later step reads raw model text") holds by construction.
- **`when`** is a closed predicate vocabulary over inputs and admitted values, never code: `{ entry = "chat" }`, `{ set = "inputs.x" }`,
  `{ eq = ["step.a.kind", "night"] }`, `{ effort_at_least = "standard" }`, `all`, `any`, `not`. A skipped step settles as `Skipped` with
  its reason. Whether CXL (doc 19 §5) should replace this vocabulary is Open question 6.

### 3.2 Step kinds

A closed set that refines doc 21's `StepKind::Code | Model | User`. The determinism class drives the journal (§4.2).

| Kind | Class | What it does | Keys |
| --- | --- | --- | --- |
| `code` | Pure | Runs a registered deterministic editor function (provider, generator, macro, compiler); seeds come from the runtime | `run`, `in` |
| `tool` | Recorded | Calls a plugin tool through its grant; a missing plugin skips (`optional`) or blocks | `uses`, `optional`, `in` |
| `pick` | Recorded | One letter from a code-built menu of ≤ 7 options plus escapes | `menu` + model keys (§3.3) |
| `fill` | Recorded | A small flat typed record | model keys |
| `compose` | Recorded | One sub-structure, for qualified setups; `split` names the authored smaller decisions | model keys, `split` |
| `draft` | Recorded | A change set over several entities, for qualified setups (doc 21 §3.3) | model keys, `split`, `tools` |
| `ask` | Recorded | A computed question with computed options (doc 21 §4); always offers cancel and, where one exists, the default | `question`, `options` |
| `approve` | Recorded | Accept, edit or reject a plan, batch or candidate set; shown or skipped by autonomy (§5.4) | `show`, `batch` |
| `verify` | Pure | Runs checks on code output; findings route to `on_fail` | `checks`, `on`, `on_fail` |
| `map` | Structural | Runs one inline step (`each`) or a sub-workflow (`call`) per item of a collection, keyed by a stable id | `over`, `key`, `max_items`, `each` or `call` |
| `call` | Structural | Runs a sub-workflow as a child run with its own journal segment | `workflow`, `in` |
| `commit` | Effect | Applies admitted batches as one undo group tagged with `Origin` (doc 21 §1.2) | `batch`, `label` |

There is deliberately no loop, goto, sleep or free "choice" kind: bounded repair lives inside model steps, branching is `when` plus
`call`, and waiting happens only in `ask` and `approve`. An inline `each` holds exactly one step; anything longer is a sub-workflow.

### 3.3 Model steps: shape, capsule, candidates, repair, fallback

| Key | Contents | Rules |
| --- | --- | --- |
| `model` | `{ role, decision, schema }`: a role (`router`, `writer`, `scripter`, `explainer`, `play-tester`, `translator`), a `DecisionKind` id, an answer schema id | The user binds roles to setups; an unbound role follows `on_fail` (doc 21 §7.2). `decision` keys exemplars, qualification and instruments. Pick uses the menu's letter schema; Pick and Fill lead with a bounded `why` (doc 25 §4.3) |
| `menu` | Provider call that builds the options | Pick only; doc 25 §6.2's algorithm; an empty menu is a finding, not a prompt to improvise. `X` re-menus once with a new diversity seed, then follows `on_fail`; `Q` becomes an `ask`-style card (doc 25 §4.3, §10.2) |
| `capsule` | `{ lens, digest, knowledge, exemplars }` | One design-sensibility lens or `core-only`; digest as `provider:scope`, shrunk by relevance rank, never summarised; knowledge as doc 30 §4.6 (`primer`, `cards`, `skills`), injected by code; exemplars default to the library named by `decision` |
| `sample` | `{ candidates, select }` | `candidates = "effort"` or a number ≤ the effort level's K; `select` = `vote` (Pick, permuted menus), `rank` (deterministic signals, optional advisory judge) or `user` (top 2–3 cards) (doc 25 §7.3). Default: K from effort, `rank` |
| `verify` | Non-empty list of checks (`V-schema`, `V-catalog`, `V-geo`, `V-mission`, `V-cxl`, `V-campaign`, `V-text`, `V-compile`; doc 25 §7.1) | Missing or empty is a load error |
| `repair` | `"effort"` (default) or 0–3 | One finding per turn; stops on a repeated finding, a repeated answer or a spent budget |
| `on_fail` | `"ask-user"`, `"split"`, `"candidate-only"`, `"stop"`, or `{ keep-default = "<provider>" }` | Doc 21's `OnFail`; no "bigger model" value; defaults are in place before the model runs (doc 25 §10.1) |
| `split`, `tools` | Authored smaller decision kinds; Lookup and Check tools | Compose and Draft only; tools ⊆ registry ∩ plugin grants ∩ role, empty for Pick and Fill |

The runtime fixes the **capsule order** (system text and tool schemas → the verbatim request → digest → menu or slot spec → exemplars →
answer schema restated; doc 21 §8.1): authors declare contents, never layout. The design-sensibility core and lens and the declared
knowledge sections go in the system text (doc 30 §4.6; `prompts/design-sensibility/README.md` allows this position), which also keeps
the prefix shared across candidates (§4.5). Untrusted segments stay quoted data (doc 21 §9.1).

### 3.4 Budgets

- Doc 21 §7.1's effort table sets K, R, shape ceiling, verification depth, retrieval and provider reasoning. Definition numbers are
  **ceilings**: the effective value is the minimum of the effort table, the definition, the plugin's `[limits]` and the user's caps
  (Claude Code likewise lets caps beat skill and subagent effort overrides [V]). Budgets never change checks.
- Doc 21 §7.1's "model turns per request" caps one chat request, but a campaign run is hundreds of decisions (doc 25 §4.5), so long
  workflows declare whole-run ceilings that the plan card shows before launch (Open question 7). Read literally, the minimum rule above
  would cap every run at that per-request row, so proposed [I]: `[budget].turns` is a **whole-run** ceiling that replaces only that one
  row for the run (it never raises K, R, the shape ceiling or any other row); a definition without `[budget]` gets the per-request row
  for the whole run. A load-time lint warns when a ceiling cannot cover one first pass (K candidates per model step, times `max_items`
  inside a `map`) at that effort. Doc 21 §7.1 needs the matching note (phase W0).
- Near a ceiling, code shrinks the shape or keeps defaults. A spent budget ends the run as `BudgetLimited`, which is resumable, never an
  error (Codex's `BudgetLimited` goal status is the precedent [V]).

### 3.5 Skills, knowledge and lenses

- **Skills are knowledge, never procedures.** A step names what enters its capsule, e.g. `knowledge = { primer = ["3"], cards =
  ["trigger.condition-context"], skills = ["standing-orders:placement-radius"] }`; code injects it, as doc 30 §4.6 specifies. Pack skills
  (`<pack>:<skill>#<section>`; built-in skills use `<skill>:<entry>` as above, and built-in skill names are reserved as pack ids so
  the two forms cannot collide [I]) execute nothing and grant nothing (doc 22 §2.1); a skill may declare `metadata: { editor.decisions:
  "radio.line briefing.slot" }` to limit which decision kinds may cite it.
- **Lenses.** Creative steps name exactly one lens (extraction steps use `core-only`); only an `evaluated` or `default` pack version ships.
  The routing table in `prompts/design-sensibility/README.md` becomes a load-time lint; pack version and lens id go into the decision record.
- **Free chat differs.** Outside workflows, Wilco sees a skill catalog; reuse Codex's discipline of about 2% of the window with
  descriptions shrunk evenly before any entry is dropped (`CX:codex-rs/ext/skills/src/render.rs#L19-27`) [V], rewritten to our indexing
  rules. Free text reaches workflows only through IntentFill → Dispatch (doc 21 §4.1); a BM25 shortlist, run in shadow mode first as Codex
  does, may build the menu [I].

## 4. The engine

### 4.1 Run lifecycle

`Planned` (plan card) → `Running` → `Parked` (an `ask` or `approve` card is open) → `Running` … → `Done` or `Stopped { reason }`; side
states `Paused` (user), `BudgetLimited` (resumable) and `Interrupted` (found at start-up after a crash). A parked run holds no model call
and no lock and survives a restart.

- **One-shot card tokens**: `hash(run, step, item, attempt, read-set revision, proposed batch hash)`. An answer is validated before it is
  journaled (one of the computed options; the read set still holds), like a Temporal Update validator [V]. A stale card is refused and
  recomputed, which enforces doc 21 §8.2's "an approval binds the exact batch".
- **Fail closed.** Codex's `ReviewDecision` defaults to Denied and separates timed out, denied and abort
  (`CX:codex-rs/protocol/src/protocol.rs#L4154-L4199`) [V]. Here "no / keep default" routes to `on_fail`, "stop" ends the run, neither
  retries silently, and a card never times out into a yes.
- **Interrupts are their own steps**, never inside a model step, so LangGraph's pitfall (an interrupted node re-runs from its start, so
  earlier side effects must be idempotent [V]) cannot arise.

### 4.2 Determinism classes and the decision journal

| Class | Steps | On resume |
| --- | --- | --- |
| Pure | `code`, `verify` | Recomputed from the current document, fact packs and derived seeds |
| Recorded | `pick`, `fill`, `compose`, `draft`, `tool`, `ask`, `approve` | The settled, admitted result is reused if the input digest still matches |
| Effect | `commit` | Idempotent by key; applied at most once |

Durable engines split work the same way (Temporal activities, duroxide, Inngest `step.run`) [V]. Only the runtime mints seeds and
timestamps (duroxide's `ctx.*` rule; Claude Code makes `Date.now()` throw [V]); a step never reads the clock or an RNG.

The **journal** is an append-only typed log in the mission or campaign sidecar, excluded from export (doc 21 §9.3). Keys are
`(run, step, item, attempt)`: authored step ids and stable editor ids (node, slot, character), never list indices, because positional
matching breaks on reorder (Temporal compares command sequences; LangGraph matches interrupts by index; Inngest and Cloudflare key by step
name [V]). Records are listed in §4.7; model records hold the capsule hash, setup, admitted value, findings and the raw reply as
untrusted data, never reasoning text (doc 21 §8.2). They feed the inspector's `DecisionRecord` (doc 25 §9.1). Storage is Open question 2.

### 4.3 Resume, replay and staleness

1. Load the journal and the run's **own definition snapshot**; a pack update or uninstall never changes a started run (§6.3).
2. Recompute Pure steps. Reuse a settled Recorded step when its **input digest** matches: step-definition hash, bound inputs, fact-pack
   fingerprints (catalog and addon set, island, dialect pack; doc 21 §10.1), derived seed, lens and exemplar-pack hashes, model setup
   (Dagster's code-plus-input data versions and Prefect's cache keys are the precedent [V]; content digests avoid Houdini TOPs' documented
   blind spot for replaced result files [V]).
3. A mismatch **parks the run** ("catalog changed since this pick: re-run 3 steps / keep them / stop"); the step and its dependents are
   marked Stale with a reason chip. Nothing re-runs silently (doc 25 §9.2); a stale value is not called valid until re-checked (doc 21 §6.5).
4. An intent without a settlement becomes `Interrupted`; its retry is a new, budget-counted turn (doc 21 §6.2 rule 6). Preview launches and
   plugin egress are never retried automatically.
5. A `commit` whose idempotency key is already in the undo history settles as done; one the user undid settles "reverted by user".

Doc 21 §6.2/§8.2 ("never replayed from a log") and doc 25 §4.2 ("so it can pause, resume and be replayed") agree in substance but not in
wording; phase W0 files a design-gap note: resume **reuses** settled entries and never **re-executes** a settled model call.

### 4.4 Re-running one step, background runs and human edits

- **Re-run this step** appends attempt n + 1 for that key, reusing journaled inputs except what the user changed (reroll, effort, or
  another configured model setup offered as a button with its cost, doc 25 §10.2; the role binding itself changes only in Settings,
  doc 21 §7.2). The result goes through doc 25 §9.3's field-level merge; the previous attempt stays a one-click
  alternative. **Dependents are marked Stale, not re-executed** (LangGraph time travel re-runs later nodes including LLM calls [V]; weak
  models are slow and human edits must survive). A human edit makes a field human-owned (doc 25 §9.1): a constraint, not a trigger.
- **Run concurrently, mutate serially** (doc 10 §6 item 5): model calls and reads run off the UI thread; commits are queued and applied on
  the UI thread as undo groups; the user's own edits never wait for a run.
- **Revision-bound proposals.** Each admitted value carries its read set (doc 25 §4.2) and is re-verified at commit: unrelated edits never
  block it, a changed read entity triggers a recompute, a target that became human-edited or pinned is dropped with a note (doc 21 §8.2).
  Parallel branches declare write sets (doc 21 §1.2 `Proposal.writes`); overlapping ones are serialised.

### 4.5 Fan-out and parallelism

- **Item seed = hash(root seed, step id, item key).** A stable key rather than position (Unreal PCG seeds points from position [V]) keeps
  results stable when elements move. **Join** in canonical key order, never completion order (duroxide has its own deterministic join for
  this reason [V]). The policy is all-settled: one defaulted item never fails the stage (doc 25 §10.1). **Budget is reserved in key
  order** [I]: each item reserves its worst case (K candidates plus R repairs per decision, doc 21 §7.1) before dispatch; when the rest cannot cover a reservation, the
  scheduler waits for the earlier items to settle and decides from their actual spend. Whether an item runs or ends `BudgetLimited`
  then depends only on the items before it in key order, never on completion order.
- **Concurrency changes speed, never results.** `max_concurrency` defaults to 1 locally and more for remote backends [U: tune]. Caps
  [I: placeholders]: ≤ 8 concurrent model calls, ≤ 512 items per `map`, ≤ 2,000 decisions per run, call depth ≤ 3. Exceeding one is an
  error with numbers, never silent truncation (Claude Code rejects over-long lists for the same reason [V]).
- **Prefix reuse.** Capsules put system text and tool schemas first, so a slot's K candidates share a prompt prefix; local reuse is [U]
  (Claude Code briefly holds fan-out siblings so they share a cache prefix [V]).

### 4.6 Budgets, timeouts and cancellation

- **Ledger** nested run → stage → step → attempt (turns, tokens, wall time, K, R). Code reads it and shrinks shapes before exhaustion; the
  model never sees or manages it.
- **Timeouts.** Streamed tokens are the heartbeat, catching stalls before the step timeout (ASL keeps the heartbeat below the timeout [V]).
  A hard timeout interrupts and goes to `on_fail`; a soft deadline shows "use the default now / keep waiting" (BPMN's interrupting and
  non-interrupting boundary events [V]). Transport retries are bounded, journaled apart from repairs and never switch models.
- **Cancellation** uses a `tokio_util::sync::CancellationToken` tree: a stage cancels its steps, a child never cancels its parent [V]. A
  cancelled attempt settles `Cancelled`; admitted work stays, since commits are atomic undo groups. Tests use a virtual clock, like
  Temporal's time-skipping environment [V].

### 4.7 No workflow engine dependency; Rust sketch and UI events (proposal-only; not compiled; names not final)

`temporalio-sdk` needs a Temporal Service; `restate-sdk` needs the BSL-licensed Restate server; obelisk is an AGPL-3.0-only server;
flawless has had no stable release since 2024; underway needs Postgres [V: crates.io and repos, 2026-09-27]. All are code-as-workflow;
ours is data, so a small in-house interpreter suffices, with duroxide (MIT, embeddable, SQLite provider) as the reference design.

```rust
// Crate `ofp-workflow`: definition types, TOML loader, load-time validator. Pure: callers pass bytes; no I/O.
pub struct WorkflowDef { id: WorkflowId, version: Version, hash: DefHash, meta: Meta, policy: ModelPolicy, inputs: Vec<InputDef>,
                         budget: BudgetCaps, steps: NonEmpty<StepDef>, gate: NonEmpty<GateId> }
pub struct StepDef { id: StepId, when: Option<Predicate>, bind: Vec<(Name, Binding)>, kind: StepKind }
pub enum Binding { Input(Name), Admitted { step: StepId, field: FieldPath } }          // no variant for raw model text
pub enum StepKind { Code { run: CodeStepId }, Tool { uses: PluginToolRef, optional: bool }, Decide(DecisionSpec),
    Ask(QuestionSpec), Approve(ApproveSpec), Verify { checks: NonEmpty<CheckId>, on_fail: OnFail },
    Map { over: CollectionRef, key: KeyPath, limits: MapLimits, body: MapBody }, Call { workflow: WorkflowRef },
    Commit { batches: NonEmpty<Binding>, label: LabelKey } }
pub enum MapBody { Each(Box<StepKind>), Call(WorkflowRef) }                            // the loader forbids Map inside Each
pub struct DecisionSpec { shape: ModelShape, role: Role, decision: DecisionKind, schema: SchemaId, capsule: CapsuleSpec,
                          sample: SampleSpec, verify: NonEmpty<CheckId>, repair: Budgeted<u8>, on_fail: OnFail }
pub enum ModelShape { Pick { menu: MenuSpec }, Fill,                                   // "Deterministic" is StepKind::Code
    Compose { split: Option<NonEmpty<DecisionKind>> },                                 // split and tools exist only where §3.3
    Draft { split: Option<NonEmpty<DecisionKind>>, tools: ToolSubset } }               // allows them
pub enum OnFail { AskUser, KeepDefault(DefaultRef), Split, CandidateOnly, Stop }       // deliberately no "bigger model"

// Crate `ofp-workflow-runtime`: interpreter, journal, ledger, scheduler. Edits reach the document only via the command bus.
pub struct JournalKey { run: RunId, step: StepId, item: Option<ItemKey>, attempt: Attempt }
pub enum RunState { Planned(PlanCard), Running(Cursor), Parked(CardToken), Paused, BudgetLimited(LedgerSnapshot),
                    Interrupted, Done(TurnReport), Stopped(StopReason) }                // one cursor per branch
pub enum JournalRecord { RunStarted(RunHeader), StepScheduled { key: JournalKey, input: Digest },
    ModelRequested { key: JournalKey, capsule: Digest, setup: ModelSetupId, candidate: u8, repair: u8 },
    ModelSettled { key: JournalKey, outcome: Settlement }, UserAsked { key: JournalKey, token: CardToken },
    UserAnswered { key: JournalKey, token: CardToken, answer: AnswerValue },
    CommitApplied { key: JournalKey, undo_group: UndoGroupId, idempotency: Digest }, Defaulted { key: JournalKey, why: FindingRef },
    MarkedStale { keys: Vec<JournalKey>, why: StaleReason }, Interrupted(JournalKey), Cancelled(JournalKey), RunFinished(FinalState) }
pub enum RunEvent {                     // drained by egui each frame; extends doc 10 §6's AgentEvent (PlanUpdated)
    PlanReady { run: RunId, card: PlanCard }, PlanUpdated { run: RunId, steps: Vec<(StepId, StepStatus)> },
    StepStarted(JournalKey), CandidateReady { key: JournalKey, index: u8 }, NeedsInput { key: JournalKey, card: Card },
    StepSettled { key: JournalKey, status: StepStatus }, CommitApplied { key: JournalKey, undo_group: UndoGroupId },
    MarkedStale { keys: Vec<JournalKey>, why: StaleReason }, Budget { run: RunId, ledger: LedgerSnapshot },
    Finished { run: RunId, report: TurnReport } }                                       // doc 21 §5.1: code-written status first
pub enum StepStatus { Pending, Active, NeedsInput, Admitted { repaired: bool }, Defaulted, Skipped(SkipReason),
                      Blocked(FindingRef), Stale(StaleReason), Reopened, Cancelled }
```

`WorkflowId`, `RunId`, `StepId`, `ItemKey`, `Attempt` and `CardToken` are newtypes under AGENTS.md's rules and join `CODE-INDEX.md`'s table
when implemented. `NonEmpty<CheckId>` makes a model step without a check unrepresentable, and `Pick { menu }` a Pick without a menu.
`Reopened` is doc 21 §6.2 rule 4 (a finished step whose gate a later edit turns red), a state Codex's plan checklist lacks [V]. Doc 25's
`ofp-campaign-flow` (its typed `Stage` enum, doc 25 §4.2) becomes definitions plus campaign code steps on this runtime; that supersedes
a doc 25 sketch and is a W0 design-gap item. Crates: petgraph (cycles, topological order), tokio-util, serde and schemars, minijinja with fuel
(doc 22 §2.1); a plain enum likely makes `statig` or `rust-fsm` unnecessary.

## 5. UX

### 5.1 Entry points and the command palette

- **Doors, in doc 21 §2.1's order:** a gesture (context menu "Populate this town" chooses workflow and target), the palette, a wizard (doc
  21 §11.3), `/` in the Wilco chat, and free text through IntentFill → Dispatch (`Run`, `Ask`, `NotSupported`).
- **Palette.** A typed registry built from every enabled definition: `/populate-town` for `core/…`, `/radio-voice:voice-radio-chatter`
  for packs (namespaced as in Claude Code and doc 22 §4.1). Availability is computed with exhaustive matches, as Codex's `SlashCommand`
  does [V]: preflight, selection kind, another run's write set, model policy, role binding. Unlike Codex, which hides unavailable commands,
  entries stay **greyed with a one-click fix** ("load an island"; "no dead-end buttons", doc 17 §15).
- **Typed arguments.** `/populate-town Morton dense` is parsed by code against the input types with no model call (doc 34 le18); an
  ambiguous place becomes a computed question showing both candidates on the map (doc 21 §4.2).

### 5.2 The plan card

Before a run that can write, a non-modal card lists the steps (kind icon, title, role and bound model setup, K and R at the current
effort), declared effects (undoable writes, plugin egress, a Preview button offered at the end), required plugins, the budget estimate
(turns, time, cost for remote setups) and the assumption chips, with **Run**, **Edit** and **Cancel**.

- **Edit is typed:** effort, optional gates, scope (e.g. nodes m03–m05 only), pinned inputs. Role bindings are shown and changed only in
  Settings (doc 21 §7.2).
- **"Always run without the card in this project"** exists only for built-in and installed pack workflows whose effects are undoable
  writes, never for a run requested by an external agent (Claude Code never offers "don't ask again" for a freshly written script [V]).
- **Clear context after approval.** Execution steps receive the typed approved plan and code-built digests, never the planning chat
  (Codex's "clear context and implement" option [V]; doc 21 §8.1).

### 5.3 Run panel, notifications, inspection and undo

- **Run panel by phase:** decisions done/total, admitted, defaulted and repaired counts, tokens, time and model setup, with drill-in per
  step (the `/workflows` view is the template [V]); pause, resume, stop, cancel a stage, re-run a step; `BudgetLimited` offers "continue
  with N more turns". The campaign book and Flow view fill in live (doc 25 §10.3).
- **Notifications:** `NeedsInput` cards appear in chat and as a badge, never as modals; OS notifications while unfocused are opt-in. A
  finished run posts its `TurnReport`: what the AI wrote, what it could not do, which defaults remain.
- **Inspector** (doc 25 §9.1) per element and run-graph node: journal entries, the capsule as sent (untrusted segments marked), menu and
  seed, pick, the model's `why` as untrusted data, checks, repairs, lens and pack version, model setup, cost, dependents; rules that did
  not run show as not run (doc 21 §6.5). The **run graph** is a read-only egui view (code = rectangle, model = rounded with a role badge,
  user = person icon, `map` = diamond) with status overlays; authoring stays in validated TOML.
- **Three undo-like actions:** ordinary undo; **Rewind the run to here** (fork the journal, as LangGraph's `update_state` branches rather
  than rolls back [V]); **Revert this run** (undo its commits in reverse order where they commute with later edits, else "revert as a new
  change" with a conflict view; doc 34 ed22; Flowable compensates in reverse order [V]). Human-origin groups are never touched. Codex's
  `thread/revert` changes history but not files [V]; here journal and document move together.

### 5.4 Autonomy interplay (doc 21 §7.3)

| Autonomy | Plan card | `ask` steps | `approve` steps | `commit` |
| --- | --- | --- | --- | --- |
| Ask | Only read-only workflows run; writing ones show "switch to Propose" | Shown | — | None |
| Propose | Shown | Shown | Always, with map ghosts and a semantic diff | Only after the click |
| Confirm (default) | Once per run | Shown | When a batch deletes or moves existing entities or exceeds the size threshold | One highlighted undo group |
| Auto | Skipped only where "always" was granted | Required inputs still ask; optional ones take defaults | Skipped, except before irreversible effects | One undo group per step; never Preview, idea cards or a plugin's first egress (a send derived from another plugin's output shows the egress card every time: answered 2026-09-27 → [D043](../decisions/D043-cross-plugin-chaining-in-workflows.md) item 3) |

## 6. Authoring and distribution

### 6.1 First-party and community workflows

- **First-party.** Built-ins are written in the same TOML and compiled in by a build step that runs the same loader and fails the build on
  any error, so there is one format (doc 21 §6.1 says "Rust constants"; doc 34 mo22 ships first-party content as packs; Open question 1).
  Everything a definition names (code steps, types, checks, gates, providers, roles, lenses) is registered in Rust.
- **T0 packs.** `workflows/*.toml` listed under `[provides] workflows` in `plugin.toml` (doc 22 §2.1, §7.2). The install review shows per
  workflow: model policy, roles, step counts by kind, declared effects, required plugins, budgets and `external`. Pack workflows **cannot**
  add step kinds, code steps, types, checks, providers or wider tool sets, so a pack cannot add nondeterminism or effects.
  (Cross-publisher chains: a third-party pack workflow stays single-publisher; first-party and user-authored workflows may
  chain, with the egress card every time: answered 2026-09-27 → [D043](../decisions/D043-cross-plugin-chaining-in-workflows.md).)
- **Hash-pinned trust**, after Codex's hooks (Trusted when the stored hash matches, Modified when it differs, Untrusted when none is
  stored; `CX:codex-rs/hooks/src/engine/discovery.rs#L794-811`) [V]: an update that changes a workflow's hash marks it Modified, and it
  does not run until re-approved with a diff of its declared steps and effects. Started runs keep their snapshot.
- **No repository or mission scope.** Unlike Codex's repo-scoped skills [V], Plotroom never loads workflows or instructions from mission
  or campaign folders: downloaded content is untrusted data (AGENTS.md).

### 6.2 Load-time validation (the definition compiler)

Refuse, with field-labelled structured errors: unknown keys (`serde(deny_unknown_fields)`, as doc 22 §7.2 does for manifests; workflows
drive execution, so a misspelled `verify` must not pass); unknown kinds, types, checks, gates, providers, lenses or roles; duplicate,
templated or generated step ids; cycles (petgraph); bindings to anything but inputs or earlier admitted outputs, or of an incompatible type
(doc 21 §6.4's build-time test plus type checking); a model step without `verify` or `on_fail`; `on_fail = "split"` without `split`;
`required` with no model step, `forbidden` with one; tools outside registry ∩ grants ∩ role; a `map` without a stable key or above the
item cap; `requires` naming an unknown plugin (and, in a third-party pack workflow, a plugin of another publisher: answered
2026-09-27 → [D043](../decisions/D043-cross-plugin-chaining-in-workflows.md) item 1);
pack text failing minijinja under fuel; files over 64 KiB or 128 steps [I: caps]. Overlapping parallel write sets are serialised with a
warning. Every refusal is a CI fixture (AT-W1).

### 6.3 Versioning and migration

- A definition has id, semver and content hash. The run header embeds the full definition snapshot, so a run resumes on the definition it
  started with even after an update or uninstall (Temporal's pinned runs; AWS Step Functions' immutable versions [V]).
- **"Upgrade this run"** is offered only when a replay check passes: every settled step id exists with compatible I/O types and graph
  position. Otherwise the run finishes pinned, or the user restarts from a chosen stage carrying the admitted document state (Temporal's
  continue-as-new [V]). This is stricter than Temporal's Auto-Upgrade, which leaves replay safety to the author [V].
- Authors change behaviour by adding step ids, not patch branches, so definitions never accumulate version conditionals.

### 6.4 Testing and evaluation

- **Golden journals** (fixture island and catalog only, per AGENTS.md) for every built-in workflow are replayed in CI; incompatibility
  fails unless the version was bumped and old snapshots still resume (Temporal's replay testing [V]). Pack import runs the same check on
  pack-supplied journals, beside doc 33 §5.6's reference-solution replay.
- **Cassettes** keyed by a canonical capsule hash (template id and version, rendered capsule bytes, answer schema, grammar hash, sampler,
  model setup, candidate and repair index), in the spirit of DSPy's request-hash cache and Temporal's activity mocks [V]. CI is strict: a
  miss fails and never reaches a network. Cassettes hold raw replies, so admission, repair and checks run for real.
- **Path tests.** A scripted faux model (doc 11 §3.4) walks every menu letter including `X` and `Q`, plus malformed, truncated and
  duplicate-key replies, timeouts and cancellation at each step, via `proptest-state-machine` (XState's generated path tests are the
  precedent [V]). Invariants: the document stays valid; only the gate emits Done; no raw model text binds downstream; budgets hold;
  human-edited and pinned fields are unchanged. **Crash at every journal entry:** truncate after each record, resume, and assert the same
  document, a journal equal to an uninterrupted run's apart from `Interrupted` records, zero extra model calls for settled entries, and
  exactly one new, counted call per unsettled request (§4.3 item 4; cassettes make its answer identical) [I: our test; no cited engine
  documents it in these words].
- **Instruments.** Doc 25 §11 (E1–E11) and doc 21 §12 run through this runtime, with no-model, random-valid and always-ask controls.
- **Headless runner.** `plotroom workflow test <pack>` runs definitions on fixtures and writes a JSONL event log and a typed result (like
  `codex exec --json` [V] and doc 34's `plotroom check`): a product binary for authors and CI, never a Wilco tool. Its debug mode can pin
  a step's answer; pins apply only in debug runs, still pass admission and never ship (n8n's production runs ignore pinned data [V]).

## 7. Policy hooks on editor command events

Claude Code and Codex let users attach commands to lifecycle events [V]. Plotroom keeps the **semantics** and drops the **mechanism**:
every policy is a Rust function in the editor, extensions are data, and a model is never a gate (doc 21 §1.4).

| Event | Built-in policies | Outcomes | Extension |
| --- | --- | --- | --- |
| Run requested | Provenance (a user gesture, or an external request awaiting the click); preflight; model policy vs configured roles | Plan card; refuse with a fix | None |
| Model request | Budget ledger; capsule counted before sending; trust labels; setup used = setup shown (doc 21 §12.4 G5) | Send, shrink digest, split, stop | None |
| Model settled | Strict admission; the step's checks; one-finding repair (a pre-tool hook's "block with feedback") | Admit, repair, fall back | T0 lints and T1 checks add findings |
| Plugin tool request | Declared tools ∩ grant; egress cards (doc 22 §3.1); limits | Call, ask, refuse | The manifest only narrows |
| Before commit | Read-set revision; human-edited and pinned protection; autonomy; the card token binds the batch hash | Commit, recompute, ask | None |
| After commit | `Origin` with run, step and attempt; staleness propagation; reopen earlier gates that turned red | Stale, Reopened | None |
| Done requested | The completion gate: like a blocking stop hook, a red gate becomes one more repair turn with a code-written finding within budget, then an honest report (Codex feeds a Stop hook's reason back as a continuation [V]) | Done, repair, report | A pack may add lint ids to its own workflow's gate |
| User edit | Staleness triggers; human ownership | Stale; drop pending proposals | None |

Policies combine by a meet in which the most restrictive wins, unit-tested as a lattice (identity, commutativity, incomparable pairs)
after `AppToolApproval::restrict_to` [V]. **Staleness triggers**, a tested table after n8n's dirty-node rules [V]: a step definition,
bound input, fact-pack fingerprint, lens or exemplar pack changed; an upstream re-run admitted a different value; an answer was pinned,
unpinned or edited. **Never:** shell, HTTP, MCP-tool, prompt or agent handlers (Claude Code's five handler types [V]), user scripts,
or anything a mission file can declare.

## 8. Three example definitions

Each file starts with `format = "plotroom-workflow/1"`; `title`, `description` and `profiles` are omitted for space (§3.1 shows them).

### 8.1 `core/campaign-from-brief` (abbreviated)

```toml
[workflow]
id = "core/campaign-from-brief"
version = "0.1.0"
model_policy = "optional"                        # AI off: seeded picks and template text (doc 25 §10.1)
scope = "campaign"
entry = ["palette", "wizard:new-campaign", "chat"]
external = "start"
preflight = ["catalog", "islands-installed"]
completion_gate = ["campaign.compiles", "campaign.lints.errors", "campaign.endings-reachable"]
[inputs]
request = { type = "user-text" }                 # optional: the wizard may supply the brief instead
brief = { type = "campaign-brief" }              # doc 25 CampaignBrief, possibly partial
[budget]                                         # whole-run ceilings (§3.4); the plan card shows the estimate
turns = { quick = 400, standard = 900, thorough = 2000, max = 3000 }   # ≈ doc 25 §4.5's 200–300 decisions × K, plus repairs
[[step]]                                         # S0 Describe: quote-checked Fill, computed questions, chips
id = "s0-describe"
kind = "call"
workflow = "core/campaign-intake"
in = { request = "inputs.request", brief = "inputs.brief" }
[[step]]                                         # S1 Premise: three cards from three seeded archetypes
id = "s1-cards"
kind = "map"
over = { provider = "premise.archetypes", brief = "step.s0-describe.brief", count = 3 }
key = "archetype_id"
[step.each]
kind = "fill"
model = { role = "writer", decision = "campaign.premise", schema = "premise@1" }
capsule = { lens = "campaign-arc", digest = "brief.digest:premise" }
verify = ["V-schema", "V-text"]
on_fail = { keep-default = "premise.template" }
[[step]]
id = "s1-choose"
kind = "ask"
question = "premise.pick"                        # the three cards, "reroll", "keep the default"
options = "step.s1-cards"
# S2 Story bible: a `map` over roster slots calling core/bible-row (elided).
[[step]]                                         # S3 Outline: graph-shape Pick, beat Picks, node names
id = "s3-outline"
kind = "call"
workflow = "core/campaign-outline"
in = { brief = "step.s0-describe.brief", premise = "step.s1-choose" }   # plus the S2 bible (elided)
[[step]]
id = "s3-defaults"
kind = "code"
run = "campaign.fill_defaults"                   # a default mission per node, template text per slot: it compiles now
in = { outline = "step.s3-outline" }
[[step]]
id = "s3-approve"
kind = "approve"
show = "flow-view"
batch = ["step.s3-outline", "step.s3-defaults"]
when = { effort_at_least = "standard" }          # doc 25 §5.2 user gate; under Propose the commit still waits for a click (§5.4)
[[step]]
id = "s3-commit"
kind = "commit"
batch = ["step.s3-outline", "step.s3-defaults"]
label = "campaign-outline"
# S4 state schema (call core/campaign-state), S5 concepts (map over nodes, call core/mission-concept), S6 build
# (map over nodes, code missions.build), S7 text (map over slots, call core/text-slot), each with verify and commit (elided).
[[step]]                                         # S8 Verify
id = "s8-verify"
kind = "verify"
checks = ["V-campaign", "V-compile", "path-explorer"]
on = "campaign"
on_fail = "ask-user"
```

**Commentary.** Stage ids mirror doc 25 §4.1, and each stage is a child run, which keeps journals small and per-mission re-runs local
(part of doc 25 OQ10: code may compact a finished stage into admitted results plus the records the inspector needs; retention limits are
[U]). `s3-defaults` realises the draft-first invariant: after it commits the campaign compiles, and every later decision only upgrades a
default. Side and islands come from S0 intake. **S9 is not a step:** Preview is a button the user presses (doc 21 §7.3), and each refine
request starts a scoped `core/campaign-refine` run over this journal, which supplies staleness and merge bases (doc 25 §9.2–§9.3).
Doc 25 §5.2 shows no premise gate at Quick, yet `s1-choose` asks at every effort (only Auto takes its default, §5.4), because doc 21 §7
makes "what waits for a click" an autonomy question, not a budget; this contradiction is Open question 12.

### 8.2 `core/populate-town`

```toml
[workflow]
id = "core/populate-town"
version = "1.0.0"
model_policy = "optional"
scope = "mission"
entry = ["palette", "context-menu:place", "chat"]
external = "start-and-decide"
preflight = ["island-loaded", "catalog"]
completion_gate = ["mission.validators", "populate.within-town", "populate.caps"]
[inputs]
town = { type = "place-ref", required = true, from = ["selection", "intent.place"] }
side = { type = "side", required = true, from = ["selection", "intent.side"] }
density = { type = "density-band", default = "medium", from = ["intent.size"] }   # sparse | medium | dense, mapped from SizeBand
[budget]
turns = { quick = 2, standard = 5, thorough = 8, max = 8 }   # one Pick: K candidates plus R repairs (doc 25 §5.2); placeholders
[[step]]
id = "sites"
kind = "code"
run = "island.town_sites"                        # buildings, road entries, open squares inside the town radius
in = { town = "inputs.town" }
[[step]]
id = "composition"
kind = "pick"
model = { role = "router", decision = "populate.composition" }
menu = { provider = "compositions.compatible", side = "inputs.side", sites = "step.sites" }
capsule = { lens = "encounter-and-pacing", knowledge = { skills = ["standing-orders:probability-of-presence"] } }
sample = { candidates = "effort", select = "vote" }
verify = ["V-schema", "V-catalog"]
on_fail = { keep-default = "compositions.best-scored" }
[[step]]
id = "build"
kind = "code"
run = "compositions.instantiate"                 # seeded; ≤ 12 crew seats per group; per-side group caps
in = { sites = "step.sites", composition = "step.composition", density = "inputs.density" }
[[step]]
id = "check"
kind = "verify"
checks = ["V-catalog", "V-geo", "V-mission", "populate.caps"]
on = "step.build.batch"
on_fail = "stop"
[[step]]
id = "preview"
kind = "approve"
show = "map-ghosts"
batch = "step.build.batch"
[[step]]
id = "apply"
kind = "commit"
batch = "step.build.batch"
label = "populate-town"
```

**Commentary.** Doc 21 §6.4's "Give patrol" pattern at town scale, and doc 22 §1.2's town-population plugin as a built-in. Free text
is read once, before dispatch: IntentFill's quote-checked `place`, `side` and `size` fields (doc 21 §4.1) fill the inputs, so a chat
start and a context-menu start run the same steps, and a second intake Fill would only repeat that call. The model makes one taste Pick
among compositions that are all valid by construction; positions, classes, counts and caps belong to code. With AI off, `composition` keeps the best-scored default and the result is complete.
A T1 terrain-analysis plugin could replace `sites` with a `tool` step; `start-and-decide` lets an external agent answer the Pick (§9).

### 8.3 `core/write-briefing`

```toml
[workflow]
id = "core/write-briefing"
version = "1.0.0"
model_policy = "required"                        # AI off: the UI offers the template path (doc 21 §6.3)
scope = "mission"
entry = ["palette", "context-menu:briefing", "chat"]
external = "start"
preflight = ["mission-has-objectives"]
completion_gate = ["briefing.lints", "briefing.objectives-covered", "briefing.model-slot-admitted"]
[inputs]
tone = { type = "tone-preset", default = "terse" }
[budget]
turns = { quick = 24, standard = 48, thorough = 96, max = 132 }   # ≤ 12 slots × (K + R); placeholders
[[step]]
id = "skeleton"
kind = "code"
run = "briefing.render_skeleton"                 # Main, Plan, one OBJ_n per objective, Debriefing, marker links, facts
[[step]]
id = "slots"
kind = "map"
over = { provider = "briefing.slots", skeleton = "step.skeleton", tone = "inputs.tone" }   # situation, Plan colour, OBJ_ rephrases
key = "slot_id"
max_items = 12
[step.each]
kind = "fill"
model = { role = "writer", decision = "briefing.slot", schema = "slot-text@1" }   # {why, text}; caps from the slot spec
capsule = { lens = "briefing", digest = "mission.digest:slot", knowledge = { primer = ["5"], cards = ["briefing.html"] } }
sample = { candidates = "effort", select = "user" }   # batch mode: top-ranked, marked "AI draft, unreviewed"
verify = ["V-schema", "V-text"]
on_fail = { keep-default = "slot.template" }     # the template sentence stays in place
[[step]]
id = "review"
kind = "approve"
show = "text-diff"
batch = ["step.skeleton", "step.slots"]
[[step]]
id = "apply"
kind = "commit"
batch = ["step.skeleton", "step.slots"]
label = "write-briefing"
```

**Commentary.** Doc 21 §5.2's split made concrete: code writes structure, keys, grids, callsigns and numbers; the model writes bounded
slots checked for length, codepage, mentions ⊆ mission dossier, numbers ⊆ digest and the era word list. `briefing.model-slot-admitted`
enforces doc 21 §6.3 (a `Required` workflow refuses Done with zero model turns), tightened here to zero *admitted* slots [I]: a run in
which every slot fell back to its template reports "not done, templates kept" instead. Candidates arrive as cards that the user
accepts, edits or rejects; every line records its origin (doc 25 §9.1).

## 9. Exposure to external agents

AGENTS.md allows exposing the editor's own product tools through an opt-in, loopback-only, authenticated MCP server, because that adds no
capability; doc 12 §3.4 and doc 22 §4.3 call it `ofp-mcp`. Workflows join it as follows [I]:

- **Tools.** `workflow.list` (id, title, description, model policy, input schemas, availability); `workflow.start { id, args, effort }` →
  `{ run, plan }`; `workflow.status`; `workflow.cancel`; and, only for `external = "start-and-decide"`, `workflow.decide { run, key,
  answer }`: the external agent gets the menu or slot spec a model would get, and its answer goes through the same admission, checks and
  repair, recorded as `Origin::External { client }` (`workflow.decide` ships after v1, its answers excluded from model
  qualification: answered 2026-09-27 → [D036](../decisions/D036-v1-contents-and-release-split.md) item 6). Read-only `forbidden`
  workflows (validate, readiness coach, Path Explorer; doc 21 §6.3) run without a card; "explain a finding" is `Optional` there, so it
  spends the user's model budget and keeps the card.
  Definitions are readable as resources, and one MCP prompt per exposed workflow aids discovery; prompts carry no authority.
- **Approvals stay in the editor.** An MCP-started run waits in `Planned` for the user's click on a card badged "requested by an external
  agent"; `ask` and `approve` cards are never answerable over MCP. This is §2 item 8, and it mirrors Claude Code's rule that messages
  between agents cannot supply the user's consent [V].
- **No egress by proxy.** Workflows using T2 plugin tools are not exposed in v1, since plugin tools are not re-exported (doc 22 §4.3).
  (Cross-publisher chains are never exposed: answered 2026-09-27 → [D043](../decisions/D043-cross-plugin-chaining-in-workflows.md)
  item 4.)
- **Claude Code and Codex users** connect `ofp-mcp` like any MCP server. `mission-primer` is served as an Agent Skill or MCP prompt (doc 30
  §4.6), and its body should say "prefer `workflow.start` over composing edits yourself" [I]. Their own scripts may orchestrate our tools;
  every call is still admitted by our runtime. We ship no Claude Code workflow scripts or Codex-specific plugins in v1; a portable bundle of
  the skill plus MCP configuration is possible later, since both ecosystems package "skills + MCP servers" (doc 22 §6) [I].
- **Long runs.** MCP's Tasks extension could carry them; `rmcp` and client support is [U]; polling `workflow.status` works meanwhile.

## 10. Phased plan and acceptance tests

| Phase | Delivers | Acceptance tests |
| --- | --- | --- |
| W0 Decisions | Design-gap requests: one format and how recipes relate (doc 21 OQ7, doc 17 §10); resume wording (§4.3); `Admitted<T>` vs `Checked<T>` (doc 21 OQ1); whether prompt or exemplar changes void qualification (doc 21 §12.3 is silent); journal storage; whole-run budget semantics (§3.4); definitions replacing doc 25's `Stage` enum (§4.7); effort- versus autonomy-driven user gates (OQ12; decided 2026-09-27 → [D024](../decisions/D024-effort-autonomy-role-binding.md)) | Recorded under `docs/design-gap-requests/`; no runtime code before the format decision |
| W1 Definitions | `ofp-workflow`: schema, loader, validator, type checker; `core/give-patrol` and `core/validate-and-fix` running with no model | **AT-W1** every §6.2 refusal has a fixture and a structured, field-labelled error naming the offending value (including the cross-publisher `requires` refusal: answered 2026-09-27 → [D043](../decisions/D043-cross-plugin-chaining-in-workflows.md) item 1); fuzzed TOML never panics. **AT-W2** doc 21 §6.4's build-time test passes over every registered definition |
| W2 Runtime core | Journal, resume, idempotent commit, cancellation tree, ledger, virtual clock, plan card, run panel | **AT-W3** a crash at every journal entry resumes to the same document, and a journal equal to an uninterrupted run's apart from `Interrupted` records, with zero extra model calls for settled entries (§6.4). **AT-W4** cancelling any step leaves no half-applied edit. **AT-W5** a commit the user undid is never re-applied on resume |
| W3 Model steps | Capsules, K candidates, repair, cassettes, inspector, run graph, `core/write-briefing` | **AT-W6** CI cassette runs make no network call. **AT-W7** faux-model path tests over every menu escape and malformed reply hold the §6.4 invariants. **AT-W8** every generated element opens an inspector with its journal record |
| W4 Fan-out and campaigns | `map`, child runs, seeds, key-order join; `core/populate-town`; `core/campaign-from-brief` on seeded defaults, then with models | **AT-W9** concurrency 1 and 8 yield byte-identical documents and identical canonical journals (records in key order, timing fields excluded), including under a budget that runs out mid-`map` (§4.5). **AT-W10** doc 25 E9: zero clobbers with edits made during a run. **AT-W11** doc 25 E10: 100% validity at T0 |
| W5 Packs | T0 pack workflows, install review, hash trust, pinned snapshots, upgrade replay check, `plotroom workflow test` | **AT-W12** a Modified pack workflow does not run until re-approved. **AT-W13** a started run resumes after its pack is updated or uninstalled. **AT-W14** a hostile pack (asking for more tools, higher autonomy, egress, unknown kinds) gains nothing, modelled on Codex's role-authority test (a third-party pack workflow requiring another publisher's plugin is refused at load: answered 2026-09-27 → [D043](../decisions/D043-cross-plugin-chaining-in-workflows.md) item 1) |
| W6 External | `workflow.*` on `ofp-mcp` (the MCP server in v1, `workflow.decide` after v1: answered 2026-09-27 → [D036](../decisions/D036-v1-contents-and-release-split.md) item 6) | **AT-W15** an MCP-started run waits for the editor click; `ask`/`approve` are not answerable over MCP; external answers pass admission; no T2-plugin workflow is listed |

Evidence per phase is the listed tests plus doc 21 §12 reporting; nothing is "done" without them (AGENTS.md evidence rule).

## Open questions

1. **One format.** Built-ins as TOML compiled in (this doc) or Rust constants (doc 21 §6.1)? Do doc 17 §10's recipes become exemplar
   libraries rather than workflows (proposed)? Needs a design-gap request (W0). [I]
2. **Journal storage.** JSONL or SQLite in the sidecar, and can journal and document be saved atomically with autosave? [U]
3. **Wording.** Unify doc 21 §6.2/§8.2 and doc 25 §4.2 as "resume reuses settled entries and never re-executes a settled model call". [I]
4. **Wrapper name.** `Admitted<T>` (docs 21, 22) or `Checked<T>` (doc 25)? This doc says "admitted" in prose. [I]
5. **Requalification.** Does a lens, prompt-template or exemplar-pack change void a setup's qualification (doc 21 §12.3)? [I]
6. **`when` vocabulary.** Keep §3.1's closed predicates, or reuse CXL and its visual builder (doc 19 §5)? [I]
7. **Campaign-scale budgets.** Do long runs need their own effort table beside doc 21 §7.1's per-request one, and what defaults suit
   concurrency, soft deadlines and the §4.5 caps on local hardware? [U]
8. **External deciders.** Should `workflow.decide` ship in v1, and how are external answers counted in qualification and evaluation? [I]
   (answered 2026-09-27 → [D036](../decisions/D036-v1-contents-and-release-split.md) item 6: after v1; external answers are journaled
   with an external origin and excluded from model qualification.)
9. **Codex provenance list.** Where do Apache-2.0 port records live (for example a `docs/porting/` file beside `upstream-test-map.csv`)? [I]
10. **Retention and upgrades.** How many superseded attempts, candidates and capsules does the sidecar keep, what does export strip (doc 25
    OQ10), and what exactly counts as compatible for "Upgrade this run" (§6.3)? [U]
11. **MCP Tasks.** Does `rmcp` 3.x implement the Tasks extension, and do the main clients use it for long runs? [U]
12. **User gates: effort or autonomy?** Doc 25 §5.2 puts "user gates" in the effort table (Quick: end of run only); doc 21 §7.1 drops
    that row, and doc 21 §7.3 makes "what waits for a click" autonomy. This doc uses `when = { effort_at_least }` only on `approve`
    gates and leaves `ask` steps to autonomy (§5.4, §8.1). One rule should win. [I]
13. **Cross-plugin chaining.** May a pack workflow's `requires` name another publisher's plugin, so that one plugin's output feeds
    another plugin's egress? Doc 22 §3.2 forbids plugin-to-plugin calls but lets the agent chain tools under each grant. Proposed:
    allow it only for first-party and user-authored definitions, with the egress card shown every time. [I]
    (answered 2026-09-27 → [D043](../decisions/D043-cross-plugin-chaining-in-workflows.md): DG014 option B, as proposed; such chains
    are never exposed to external agents.)

## Sources

**This repository:** `AGENTS.md`; `docs/research/` 02, 10 (§2.6–§2.13, §5, §6), 11 (§3.4, §3.6, §7.1), 12 §3.4, 17 (§10, §15), 19 (§5,
§7.1), 21 (§1–§10, §12), 22 (§1.2, §2.1, §3, §4.1–§4.3, §6, §7), 23 §14, 25 (§3–§11, open questions 7 and 10), 30 §4, 33 (§3.3, §5.5–§5.6,
§6.5), 34 (ed22, le18, mo22); `skills/mission-primer`, `skills/standing-orders`; `prompts/design-sensibility/README.md`.

**Claude Code** (public docs; concepts only): `CC:workflows.md` (re-read 2026-09-27), `CC:skills.md`, `CC:sub-agents.md`,
`CC:agent-teams.md`, `CC:hooks.md`, `CC:hooks-guide.md`, `CC:model-config.md`, `CC:permission-modes.md`, `CC:plugins/overview.md`,
`CC:memory.md`, `CC:tools-reference.md`, `CC:agent-sdk/overview.md`, `CC:agent-sdk/typescript.md`, `CC:checkpointing`.

**Codex** (`CX:` = commit e72da2b53805894878023d01949a25a082e0a5cb), under `codex-rs/`: `core/src/tasks/{mod,review}.rs`;
`core/src/state/turn.rs#L67-72`;
`core/src/tools/handlers/{plan,plan_spec,request_user_input,request_user_input_spec,multi_agents_spec}.rs`; `tui/src/slash_command.rs`;
`tui/src/chatwidget/plan_implementation.rs`; `ext/skills/src/{render,catalog_prompt,dynamic_skill_selector}.rs`; `skills/src/parser.rs`;
`ext/goal/src/spec.rs`; `core/src/agent/{role,role_tests}.rs`; `config/src/mcp_types.rs` (re-read: #L36-50); `hooks/src/engine/discovery.rs`;
`hooks/src/events/stop.rs`; `protocol/src/protocol.rs#L4154-L4199`; `history/src/lib.rs#L366-L371`;
`app-server-protocol/src/protocol/v2/thread.rs#L1257-1267`; `exec/src/{cli,exec_events}.rs`; plus `LICENSE` and `NOTICE` at the root.
Live docs: <https://learn.chatgpt.com/docs/build-skills>, `/custom-prompts`, `/non-interactive-mode`, `/agent-configuration/subagents`,
`/hooks.md`, `/llms.txt`.

**Workflow engines and libraries:** <https://states-language.net/spec.html>; Temporal docs (<https://docs.temporal.io/>:
`workflow-definition`, `activity-definition`, `patching`, `develop/safe-deployments`, `production-deployment/worker-deployments/worker-versioning`,
`develop/python/{message-passing,testing-suite,cancellation}`, `workflow-execution/continue-as-new`, `child-workflows`); Restate
(<https://docs.restate.dev/concepts/durable_execution>, `develop/go/awakeables/`, server `LICENSE`); <https://github.com/microsoft/duroxide>;
<https://www.inngest.com/docs/learn/how-functions-are-executed>; <https://developers.cloudflare.com/workflows/build/rules-of-workflows/>;
AWS Step Functions developer guide (`connect-to-resource`, `concepts-state-machine-version`); LangGraph (<https://docs.langchain.com/oss/python/langgraph/>:
`checkpointers`, `interrupts`, `use-time-travel`, `graph-api`); DSPy docs (signatures, adapters, optimizers, cache, best-of-n-and-refine);
Prefect caching; Dagster asset versioning; Airflow dynamic task mapping; n8n executions and dirty nodes; ComfyUI README; SideFX Houdini
TOPs (`intro`, `cooking`); Unreal "Using PCG with GPU processing"; Flowable BPMN constructs; <https://bpmn.io/license/>; XState
(`persistence`, `graph`); <https://github.com/obeli-sk/obelisk>; crates.io pages for `temporalio-sdk`, `restate-sdk`, `duroxide`, `obelisk`,
`flawless`, `underway`, `graph-flow`, `statig`, `rust-fsm`, `petgraph`, `insta`, `proptest-state-machine`; docs.rs `tokio_util::sync::CancellationToken`.

## Verification notes

**2026-09-27, research pass.** Claude Code, Codex and engine facts come from fact-checked passes on 2026-09-27 that re-fetched every
page and re-opened the pinned lines; for this doc `CC:workflows.md`, `restrict_to` and the Codex role module header were re-read. No
number in §3–§10 is our measurement: caps, budgets and limits are placeholders for doc 21 §12 and doc 25 §11.

**2026-09-27, consistency review** against docs 21, 22, 25 and 30, `prompts/design-sensibility/README.md`, `skills/`, the pinned Codex
clone and the live Claude Code docs.

- **Re-verified [V].** `CC:workflows.md`: a script Claude writes; `agent()` schemas, five validation attempts and the contradiction
  check; 16 concurrent agents, 4,096 items per call, 1,000 agents per run; throwing `Date.now()`/`Math.random()`; no mid-run input;
  the launch card and when "don't ask again" is offered; `ultracode` only from typed prompts; script-computed prompts are not user
  requests; resume order; the prefix hold. `CC:agent-teams.md`: another agent's message can neither approve a permission prompt
  nor stand in for the user's consent, and teammate plan approvals are granted without review. `CC:hooks.md`: 33 events and five
  handler types (`command`, `http`, `mcp_tool`, `prompt`, `agent`). Codex: `LICENSE` is Apache-2.0; `NOTICE` is six lines crediting OpenAI and Ratatui (MIT); the
  slicing at `skills/src/parser.rs#L125` and `ext/skills/src/render.rs#L255`, `#L432-438`, the panic at `core/src/tasks/review.rs#L113`,
  `restrict_to`, `ReviewDecision`'s default and the 2% skill-catalog constant (`render.rs#L22`) all match.
- **Citations corrected.** `TaskKind` lives at `core/src/state/turn.rs#L67-72` (`tasks/mod.rs#L170-202` is the `SessionTask` trait);
  hook trust status is `hooks/src/engine/discovery.rs#L794-811` (the old `#L635-655` skips prompt and agent hooks); the Stop hook's
  continuation is set at `hooks/src/events/stop.rs#L312-319`.
- **Contradictions resolved here.** Budgets: taking the minimum with doc 21 §7.1's per-request row would cap a campaign run at 10
  turns, so `[budget].turns` is now a whole-run ceiling that replaces only that row (§3.4). §6.4's crash test now matches §4.3 item 4
  and AT-W3: an unsettled request costs one new call and adds an `Interrupted` record. AT-W9 no longer claims byte-identical journals,
  which append in completion order, and §4.5 reserves budget in key order so exhaustion cannot depend on scheduling. Write-briefing's
  commentary attributed "zero admitted slots" to doc 21 §6.3, which says "zero model turns"; the tightening is now marked [I].
  External `forbidden` runs no longer list "explain", which doc 21 §6.3 classes as `Optional`.
- **Example fixes (weak-model fitness).** `populate-town` had a Fill whose output no step bound; it is removed, since IntentFill already
  quote-checks place, side and size before dispatch (doc 21 §4.1), leaving one Pick. Its `quick = 1` budget could not fit the Fill and
  the Pick. `write-briefing` had no `[budget]`, so 12 slots × K would have hit the per-request cap; its `tone` input was never bound.
  `campaign-from-brief` passed nothing to `s3-outline` or `s3-defaults`, so the chosen premise was lost, and its turn ceilings were
  below doc 25 §4.5's 200–300 decisions × K. The `s3-approve` comment claimed Propose "always shows" a step that `when` skips.
  §3.3 now says what `X` and `Q` do; the Rust sketch puts `menu` inside `Pick` and `split`/`tools` inside Compose and Draft.
- **Recorded, not resolved.** Effort- versus autonomy-driven user gates (Open question 12); cross-plugin chaining (Open question 13;
  answered 2026-09-27 → [D043](../decisions/D043-cross-plugin-chaining-in-workflows.md));
  definitions superseding doc 25's `Stage` enum and whole-run budgets both need doc 21 and doc 25 notes (W0). Doc 21 §6.1's single
  `completion_gate: GateId` and single `check` became non-empty lists here; this refines doc 21 and does not conflict with it.
- **Invariants and hygiene.** Every step kind reaches only registered editor functions, typed tools or granted plugin tools; no
  shell, HTTP, MCP-tool, prompt or agent hook exists; Wilco has no tool that writes a definition (§2 item 1 now says so). Claude Code
  is used only for concepts cited by public URL; no prompt or doc text was copied. The doc names no private or unpublished project.

### Consolidation pass (2026-09-27)

- **Rename (owner decision).** The concept manual formerly called "Field Manual" is now **Standing Orders**: the header's doc 33
  pointer, the built-in skill ids in §3.5 (`standing-orders:placement-radius`) and §8.2 `populate-town`
  (`standing-orders:probability-of-presence`), and the Sources entry `skills/standing-orders` now use the new name. Both entries
  exist in the skill's reference table under the same ids; only the skill prefix changed. The folder and doc 33 file renames happen in
  a later step; until then the files still sit at `skills/field-manual` and `docs/research/33-field-manual-and-live-tutorials.md`.
  "drill-in" in §1.1 and §5.3 is a UI term (open a run's details), not the Drill tutorials, and is unchanged. No TL;DR or
  recommendation depended on the old name.
- **Moves done (2026-09-27; supersedes "a later step" above).** The skill folder is now `skills/standing-orders/` and doc 33 is now
  `docs/research/33-standing-orders-and-drill.md` (both moved with `git mv`), so the Sources path `skills/standing-orders` and the `standing-orders:` skill ids resolve.
- **Filing pointers (verification step).** The W0 row's design-gap requests and most open questions are now filed in
  `docs/design-gap-requests/` (checked against its index), all open: OQ1 → DG007, OQ2 and OQ10 → DG017, OQ3 → DG010, OQ4 → DG011,
  OQ5 → DG012, OQ6 → DG008, OQ9 → DG018, OQ12 → DG013 (decided 2026-09-27 →
  [D024](../decisions/D024-effort-autonomy-role-binding.md)), OQ13 → DG014 (decided 2026-09-27 →
  [D043](../decisions/D043-cross-plugin-chaining-in-workflows.md)); the whole-run budget semantics of §3.4 (with OQ7 in its
  context) → DG016; the Pick schema of §3.3 and §4.7 → DG015. Not filed: OQ8 (external deciders in v1; answered 2026-09-27 →
  [D036](../decisions/D036-v1-contents-and-release-split.md) item 6), OQ11 (a [U] fact about
  `rmcp`, not a design gap) and W0's "definitions replacing doc 25's `Stage` enum", which the folder index lists as noticed but not
  filed. No text above changed.

### Owner answers folded (2026-09-27)

- 2026-09-27: folded by pointer, original words kept: OQ8 (OWQ-15) → D036 item 6 in the TL;DR, §9 "Tools", the W6 row, OQ8 and
  the filing note; OQ13 (OWQ-16 = DG014 option B) → D043 in §5.4's Auto row, §6.1, §6.2's refusal list, §9 "No egress by proxy",
  AT-W1, AT-W14, OQ13 and the two notes above. No recommendation here contradicts an answer: OQ13's proposal is what the owner chose.
