# Agent runtime: Wilco, workflows and the harness

> **Status:** proposal (architecture baseline 2026-09-27). Nothing here is decided unless it restates `AGENTS.md`, a decision
> record (`Dnnn`), a decided DG or an owner answer (`OWQ-nn`, all answered 2026-09-27). Type sketches are not compiled and names are
> not final.
> **Part of:** [architecture overview](README.md). **Main sources:** docs 12, 13, 14, 16, 21, 25, 30, 38, 40, 44, 46, 47, 48; doc 33
> §6; doc 43 §2–§3; D006, D009, D010, D021–D027; DG006–DG008, DG010–DG013, DG015–DG027, DG031, DG032.

Wilco and every AI-off procedure (give-patrol, validate-and-fix, New Mission from template, Quick Op, the campaign flow) run on **one
runtime**. The runtime is a client of the core: it reads immutable snapshots and writes only by submitting proposals to the command
bus ([commands-undo-history.md](commands-undo-history.md)). Code owns facts, structure, limits and "done"; the model owns taste and
words, one bounded decision at a time (doc 21 §1.1; doc 25 §3; D009).

## 1. Position and crates

| Crate | Layer | Owns |
| --- | --- | --- |
| `plotroom-provider` | L6 | The provider seam types: `InferenceProvider`, requests, output constraints, events, capabilities, `CachePolicy`, model setups, role bindings, qualification records, dated price rows (doc 12 §3.1; doc 13 §9; doc 40 R1, R10) |
| `plotroom-workflow` | L6 | Definition types, TOML loader and the load-time definition compiler (doc 38 §3, §6.2) |
| `plotroom-decide` | L6 | The decision kernel: capsules, code-built menus, strict admission of model output, the check registry, one-finding repair, candidate selection, `IntentFill → Dispatch`, the selector seam (doc 16) |
| `plotroom-workflow-runtime` | L6 | Interpreter, decision journal, ledger, key-order scheduler, one-shot cards, resume and staleness, cancellation, `RunEvent` (doc 38 §4) |
| `plotroom-campaign-flow` | L6 | Code steps, fact providers, checks and gates of the describe → generate → edit flow (§10) |
| `plotroom-wilco` | L6 | Chat modes, the `AgentTool` set, turn reports, idea cards, persona, explain mode (doc 21 §4–§5, §11.7) |
| `plotroom-knowledge` | L5 | Standing Orders entries, cards, primer sections, skills, lessons and tips in one store (§8); used by the UI with AI off |
| `plotroom-evals` | L6 (shipped: `plotroom qualify` and the Model Manager's "Check this model on my machine", §13; cassette tooling dev-only) | Instruments E1–E12 and qualification suites, the Rust successor of `tools/local-qual` (§7) |
| `plotroom-provider-http`, `plotroom-model-manager`, `plotroom-net` | L7 | Wire adapters; the Model Manager and managed server; the single egress crate ([crate-map.md §10](crate-map.md)) |

- Harness crates (L6) have **no HTTP client, spawn no process and write no file**; their `tokio` use is limited to sync and
  cancellation types. `xtask layers`, cargo-deny and clippy `disallowed-methods` prove it in CI (doc 21 §1.3).
- The decision kernel is its own crate so that AI-off workflows and the MCP server never depend on the co-pilot crate, and the
  readiness coach is not a Wilco feature (doc 21 §11.1 lists it as `Forbidden`).
- **Default state (D004):** Wilco is off, no provider is configured and nothing touches the network. Every no-model path, including
  describe → generate → edit with template text, stays visible and runnable; Settings and the Model Manager offer setup.

## 2. Reach by construction

```rust
// plotroom-wilco. The agent's complete set of abilities (doc 21 §1.3); adding a variant is a design review.
pub enum AgentTool { Query(QueryOp), Lookup(LookupOp), Propose(ProposeOp), Check(CheckOp), Ask(QuestionSpec) }
pub enum AgentEffect { None, ReadDocument, ReadLocalReference, WriteDocumentUndoable, OfferPreviewButton }
// No Network, FileSystem or Process variant exists, so no tool can declare one.
```

- The callable set at any moment is `Reach::AgentCallable` commands (the registry) ∩ the chat mode's fixed tool set (DG023 option B,
  proposal) ∩ the current step's subset ∩ plugin grants ∩ the bound role. A call outside the step is refused with
  `ToolNotInStep { tool, step }` and the list of what the step allows.
- `ProposeOp` names a `CommandId` and typed arguments; the result is a `Proposal<CommandBatch>` on the same admission path as a
  user gesture.
- **Preview and in-game validation are user buttons.** Wilco can offer them (`OfferPreviewButton`); only a click with `UserIntent`
  launches the game; an interrupted launch is never replayed; Auto autonomy never launches it (doc 21 §7.3).
- **No agent eval in Preview (resolution).** Doc 08 §6 P2 lists agent tools `validate_mission`, `preview_screenshot` and
  `eval_sqf_in_preview`; doc 21 §1.3 and doc 24 §5.4 treat the live harness as local code execution. Proposal: Wilco gets no eval
  tool and launches no process; it may read the typed run report, fire log and screenshots of a Preview the user launched; "Validate in
  game" (`--check`) is a button like Preview. The SQF console stays a user tool. Design-gap candidate ([README](README.md) §8 item 6).
- An effect-table test covers every `AgentTool` × `AgentEffect` pair (doc 21 §1.3).
- **Consent is typed.** Only `UserIntent` starts a model workflow, approves a plan card or accepts egress
  ([commands-undo-history.md §4.4](commands-undo-history.md)).

## 3. Provider seam and inference

```rust
pub trait InferenceProvider: Send + Sync {
    fn capabilities(&self) -> &Capabilities;                          // constraints, cache controls, reasoning knobs, limits
    fn generate(&self, req: InferenceRequest, cancel: CancellationToken) -> EventStream;
}
pub enum Backend { RemoteApi(ProviderId), LocalServer(Endpoint), ManagedServer(ManagedId) }
```

- "Own the seam, rent the wires" (D021; doc 12 §3.1): the seam types live in `plotroom-provider`; wire adapters live only in
  `plotroom-provider-http`, which may wrap an exact-pinned rig release. A spike on structured output, cache breakpoints and per-message
  effort decides between rig and thin clients of our own; the baseline stands unless that spike fails.
- Output constraints, strongest available first: grammar or JSON Schema at decode time, then JSON mode plus validation, then prompt
  plus validation (doc 13 §4). Every result is parsed and admitted like any other proposal (D022 item 3).
- Backends (D022): remote APIs; any local OpenAI-compatible server (llama-server, Ollama, LM Studio); a **managed llama-server**
  Plotroom downloads, verifies and supervises.
- **Primary local runtime (owner decision, 2026-09-27; D022 amendment note):** the managed `llama-server` sidecar, running upstream
  Vulkan, Metal or CPU builds pinned by build tag and asset SHA-256, with GGUF files pulled straight from Hugging Face by commit and
  SHA-256. Ollama and LM Studio are optional bring-your-own endpoints, auto-detected. An upstream CUDA build is an optional download
  the user starts (doc 13 §3), never bundled; whether it is offered on NVIDIA cards waits for doc 49's CUDA-versus-Vulkan measurement
  (doc 46 §2.6: Vulkan's prompt processing was 2–3× slower than Ollama's on the reference Pascal card, whose Ollama backend was not
  logged, with no detectable Pick quality difference and 859–1,281 MiB less GPU memory at peak than Ollama's library builds, which
  also carry vision parts).
- **Sidecar start-up (proposal, doc 46 §4.2):** `--jinja -ngl 99 -c <ctx> --host 127.0.0.1 --port <random> --api-key <random>`; wait
  for `/health`; read build, context, slots and default sampler from `/props`; check with `/apply-template` that the thinking switch
  changes the prompt; one warm-up call; record the effective values beside every result. `/props` and `/v1/models` report the model's
  full local path, which contains the user name: the sidecar records the file name only, and diagnostics exports strip paths.
- **Out of process, always (resolution).** D022 allows an in-process `llama-cpp-2` engine behind a feature after its safety spike.
  Because a native abort inside the editor process would lose unsaved work (doc 13 TL;DR), this architecture proposes that such an
  engine, if it lands, runs inside a small Plotroom-owned helper process supervised like the managed server, never inside the editor
  process. Design-gap candidate ([README](README.md) §8 item 7).
- Local hybrid models are sent "thinking off" explicitly, the sampler is pinned and the exact artifact recorded (doc 44 §5.1). **Every
  request pins every sampler value** (owner decision, D022 amendment note): temperature, top_k, top_p, min_p, the penalties (presence
  and frequency 0, repeat 1 for Pick and Fill), the seed and the thinking switch. GGUF, server and Ollama build defaults count as
  unknown until read: an Ollama build's hidden presence penalty of 1.5 lands on the end of the prompt, where the last menu letters are
  (doc 46 §2.2).
- Offline mode blocks every non-loopback backend (D008).

## 4. Workflow definitions

- **One format** (DG007 option C, proposal): UTF-8 TOML whose first key is `format = "plotroom-workflow/1"`, unknown keys refused,
  per-kind size caps, one pure loader family shared with modules, rule-sets, compositions and presets
  ([extensibility.md §4](extensibility.md)).
- **Twelve closed step kinds:** `code`, `tool`, `pick`, `fill`, `compose`, `draft`, `ask`, `approve`, `verify`, `map`, `call`,
  `commit`. No loop, goto, sleep or free choice (doc 38 §3.2; D025).
- **Types make the rules structural** (doc 38 §4.7): `DecisionSpec.verify: NonEmpty<CheckId>` and a non-empty completion gate
  (`NonEmpty<GateId>`; I38-GATE); `Binding` has no variant for raw model text; `OnFail` has no "bigger model" variant;
  `ModelShape::Pick { menu }` carries **no schema** (DG015 option B, proposal); `Map` inside `Each` is refused.
- `when` predicates parse into the CXL AST and share one evaluator (DG008 option A, proposal).
- **User gates follow autonomy** (DG013 decided; D024): the definition compiler **refuses effort predicates on `ask` and `approve`
  steps**, and doc 38 §8.1's `effort_at_least` gate on the campaign flow's approval step is removed.
- `[budget].turns` is a whole-run ceiling that replaces only the per-request "model turns" row; a load lint warns when a ceiling
  cannot cover one first pass (I38-BUDGET; D025; DG016 counts repairs and reservations).
- The load-time compiler refuses unknown kinds, types, checks, gates, lenses and roles; cycles; bad bindings; `map` without a stable
  key; tools outside registry ∩ grants ∩ role; and files or step counts over the caps (64 KiB and 128 steps are placeholders). Every
  refusal is a fixture (doc 38 AT-W1).
- Built-in workflows are authored in the same TOML, shipped as built-in packs and verified against compiled-in hashes; Rust registers
  vocabularies (code steps, checks, gates, providers, roles, lenses), not definitions. Pack workflows can add no step kind, code
  step, type, check, provider or wider tool set; pack roles only narrow (doc 38 §6.1). Runs are pinned to their definition snapshot.
- A build-time test asserts that every model step is immediately followed by its check and that no later step binds raw model text
  (doc 21 §6.4).

## 5. Runtime and decision journal

```rust
pub enum RunState { Planned(PlanCard), Running(Cursor), Parked(CardToken), Paused, BudgetLimited(LedgerSnapshot),
                    Interrupted, Done(TurnReport), Stopped(StopReason) }
pub struct JournalKey { run: RunId, step: StepId, item: Option<ItemKey>, attempt: Attempt }
pub enum JournalRecord {
    RunStarted(RunHeader /* embeds the definition snapshot */), StepScheduled { key: JournalKey, input: Digest },
    ModelRequested { key: JournalKey, capsule: Digest, setup: ModelSetupId, namespace: CacheNamespace, candidate: u8, repair: u8 },
    ModelSettled { key: JournalKey, outcome: Settlement /* admitted value, findings, raw reply as untrusted data; never reasoning */ },
    UserAsked { key: JournalKey, token: CardToken }, UserAnswered { key: JournalKey, token: CardToken, answer: AnswerValue },
    CommitIntent { key: JournalKey, idempotency: Digest, batch: Digest },     // flushed before the proposal is sent
    CommitApplied { key: JournalKey, group: GroupId, commit: CommitId, idempotency: Digest },
    Defaulted { key: JournalKey, why: FindingRef }, MarkedStale { keys: Vec<JournalKey>, why: StaleReason },
    Interrupted(JournalKey), Cancelled(JournalKey), RunFinished(FinalState),
}
```

- **Determinism classes** (doc 38 §4.2): pure steps (`code`, `verify`) are recomputed on resume; recorded steps (model, `tool`,
  `ask`, `approve`) settle once and are reused while their input digest matches (definition hash, bound inputs, fact-pack
  fingerprints, derived seed, lens and exemplar hashes, model setup); `commit` is idempotent by key.
- **Resume reuses settled entries and never re-executes a settled model call or a Preview** (DG010 wording, proposal). A digest
  mismatch parks the run ("catalog changed since this pick: re-run 3 steps / keep / stop"); dependents are marked Stale with a reason
  chip; nothing re-runs silently.
- **Durability order** (DG017 proposal): (1) the runtime writes `CommitIntent` and flushes; (2) sends the proposal; (3) the logic step
  commits one group with a `CommitId`; (4) the runtime writes `CommitApplied`. On load, `CommitApplied` records are reconciled by
  idempotency key against the commit ids saved in the sidecar project log, so a crash never applies a commit twice or loses one. A
  commit the user undid settles "reverted by user" and is never re-applied.
- **Storage** (DG017 option A, proposal): length-prefixed, checksummed JSONL segments per child run in `.plotroom/journal/`; a torn
  tail is truncated on load. The journal reader is a pure, size-capped parser with adversarial tests. Retention: admitted results and
  inspector records while the element exists; the last 3 superseded attempts per key [placeholder]; capsule bytes until a stage is
  compacted; a "Compact AI history" command. The crash op journal is a separate store in app data, linked by `CommitId`
  ([core-document-model.md §11](core-document-model.md)).
- **Export:** mission and campaign exports strip the sidecar. The "Share project" bundle includes AI history only when ticked, and
  capsules and raw replies only on a second tick. The **replay record** (doc 43 §3.4: seed code plus settled picks mapped to stable
  ids, admitted Fill text and human edits as ops; never raw replies) is a separate opt-in item; the export rule is DG017's open part.
- **Cards.** `ask` and `approve` park the run behind one-shot tokens: `hash(run, step, item, attempt, read-set revision, batch hash)`.
  A stale answer is refused and the card recomputed; a card never times out into a yes (doc 38 §4.1).
- **Fan-out.** `map` seeds each item from `hash(root seed, step id, item key)`, joins and admits in key order and reserves budget in
  key order, so concurrency changes speed, never results (doc 38 §4.5; AT-W9). Caps [placeholders]: ≤ 8 concurrent model calls,
  ≤ 512 items per map, ≤ 2,000 decisions per run, call depth ≤ 3.
- **Run lifecycle actions:** re-run this step (a new attempt; dependents Stale, not re-executed); rewind (fork the journal); revert this
  run (undo its groups where they commute, [commands-undo-history.md §8](commands-undo-history.md)).
- **Cancellation** uses a `CancellationToken` tree (a child never cancels its parent); streamed tokens are the timeout heartbeat;
  tests use a virtual clock (doc 38 §4.6).
- Only the runtime mints seeds and timestamps; a step never reads the clock or an RNG. Build seeds, seed codes and roll scopes follow
  doc 43 §2.2 and §3.3.

## 6. The decision kernel

**Step shapes.** Pick (a code-built menu), Fill (typed slots), Compose (a small structure, optionally split), Draft (text or code,
optionally split); "deterministic" is a `code` step (doc 21 §3.1; doc 38 §3.3).

**Capsules** (doc 21 §8; doc 40 §4.1): code builds each capsule fresh for one decision.

1. Frozen stage prefix: Wilco doctrine, the design-sensibility core and one lens (`prompts/design-sensibility/`, unevaluated),
   code-picked primer sections and cards, frozen exemplars, shape rules and schema text. Breakpoint.
2. The verbatim request, quoted as untrusted. Breakpoint.
3. A code-written digest, shrunk by relevance rank, never summarised by a model; untrusted segments fenced.
4. The menu in this sample's permutation, or the slot spec, with the answer schema restated.

Nothing volatile sits above a breakpoint; one cache namespace per (stage, `DecisionKind`); a golden test pins each kind's prefix bytes
(doc 40 R2–R4). Whether exemplars stay in the static prefix is measured (DG019).

**Menus** (doc 25 §6.2): generate from facts, filter by hard constraints, score, diversify, cap, shuffle per sample, label with
neutral letters, and add the escapes `X none_fit` and `Q ask`. Every option line is written from facts; an empty menu is a finding.

```rust
pub const MENU_MAX: usize = 7;                                   // DG006 option C (proposal): hard maximum, plus X and Q
pub struct Menu { options: BoundedVec<MenuOption, MENU_MAX>, cap: MenuCap /* per setup, from its qualification record */,
                  seed: Seed, escapes: Escapes }
pub enum PickAnswer { Option(OptionKey), NoneFit, AskMe }
```

- Catalog menus are **faceted** (side → kind → role group → role; CfgGroups presets as one-pick squads) rather than truncated
  (doc 42 §2.4; I42-25).
- **When code knows the deciding fact, it filters the menu instead of asking.** Doc 44 §2's helicopter menu (whose passengers are
  unloaded) was missed by every model even with a card; the fact belongs to code.

**Strict admission of model output.** Exactly one answer; duplicate JSON keys, non-finite numbers and unknown tools refused; a reply cut
off by the length limit is never executed; IntentFill quotes must be substrings of the request; letters map to option keys; membership,
length and code page checked. The output is `Admitted<T>` (DG011), then the step's checks (V-schema, V-catalog, V-geo, V-mission,
V-cxl, V-campaign, V-text, V-compile; doc 25 §7.1) run through the validator, Teller and the campaign compiler.

**Repair** quotes one finding per turn (rule, field path, value, why, allowed values) and stops on a repeated finding, a repeated
answer or a spent budget, then takes `on_fail` (doc 25 §7.2).

**Candidates.** Vote (Pick over differently permuted menus), rank (deterministic signals; an advisory judge may order but never admit)
or user (top 2–3 cards). **K is adaptive on every setup** and the effort table's K is a maximum: Pick stops at the first agreement
of two samples, correctness-only Fills at the first admitted candidate, Economy and batch use K = 1 (DG021 option B, proposal).

**Clarification is computed** (doc 21 §4): free text → `IntentFill` (closed fields) → `Dispatch { Run, Ask, NotSupported }`; the
selector seam (doc 16) returns `Candidate | NoMatch | Clarify`.

## 7. Qualification and shape grants

- Qualification records are kept per (model setup, `DecisionKind`) and, for Fill, **per field** (doc 44 §4: no model qualified for
  whole-record Fill; closed fields such as archetype and time of day did).
- **Effective shape = min(effort ceiling, the shapes qualified for that decision).**
  - A setup with no record runs Pick with cards and offers Fill only as a **pre-fill the user confirms**; Compose and Draft need a
    record (doc 44 §5.1).
  - A failed Compose or Draft keeps its admitted parts; the rest re-plans as authored Pick and Fill steps (`OnFail::Split`).
  - **Free-text engine knowledge qualifies for no model** (doc 44 TL;DR): explanations are always shown next to the card and the
    computed finding, and an unknown term returns `NotInManual` with no model call (§8).
- Badges say "spike-checked" until doc 21 §12.3's product qualification (n consecutive passes against the next simpler decider)
  exists; each badge links to its evidence (suite hash, n, date, runtime, sampler) and applies to one exact artifact (doc 44 §4, §5.3).
- What voids a record is DG012.

## 8. Knowledge and reference tools

- **One store** (DG031 and DG032 option C, proposals): Standing Orders entries, model-facing cards (≤ 150 words), primer sections,
  SKILL.md skills (D019), Drill lessons, tips and diagnostic explanations share one id namespace (`standing-orders:<dotted-id>`).
- Every fact carries an id, an evidence mark ([V], [I] or [U]), a pinned citation and a check kind (catalog, constant, vector, probe,
  review). **CI fails on a missing mark**, because a forgotten mark silently upgrades a claim (I33-SEED-B); only [V] facts render as
  rules.
- **Weak models never fetch knowledge.** A step declares `knowledge = { primer, cards, skills }`; code selects cards from four signals:
  field kind, step, tokens in the text under repair, and the codes of current diagnostics (doc 30 §4.2, §4.6).
- Primer sections are addressed by **stable anchor ids**, not numbers, so adding the multiplayer section and new facts to
  `skills/mission-primer` (I35-PRIMER-MP, I35-PRIMER-FACTS, I37-IDIOMS) cannot break capsules. The primer body stays within doc 30
  §5.2's 1,200-word budget, with detail in `references/` behind pointers.
- Knowledge overlays from T0 packs appear **only inside code-selected cards** (I42-17-30; [extensibility.md §3](extensibility.md)).
- Knowledge packs built from the user's install (catalog, island places, per-profile script catalog) are local, dated, never
  committed, and keyed by (profile, mod-set fingerprint, generator version, card-set version) (doc 21 §10; doc 30 §4.7).
- Tool family (names provisional until the registry lands, DG032): reference search, card, explain-this-instance, explain-diagnostic;
  Teller's command, check and completion lookups; catalog and island-place lookups; readiness "next step".

## 9. Wilco chat

- **Modes with fixed, name-sorted tool sets** (DG023 option B, proposal): Ask (query, lookup, check), Build (adds propose and ask),
  Teach (lookup, check, explain-this-instance), Review (query, check, explain-diagnostic).
- `/command args` is parsed by code with no model call (I34-21; doc 34 le18); free text goes through `IntentFill → Dispatch` into a
  workflow (doc 38 §3.5).
- Free-text slots (turn report, idea cards, notes, dissent) cannot edit the document, hide a finding or state a number code did not
  supply (doc 21 §5). The turn report leads with code-written facts. Tool calls render as typed cards whose `ItemRef` links select
  on the map.
- **Explain mode answers situational questions only**, and every "why" shown is computed; the model only phrases it (I36-21).
- Stagnation is detected with (tool, args, result, revision) fingerprints; session logs are append-only JSONL in app data and never
  contain reasoning; a session resumes from the document, not from memory.
- The persona is an era signals officer who never states an engine fact itself (doc 21 §11.7; D002).

## 10. The campaign flow: describe → generate → edit

The flow is first-class (D009; D004 item 4) and runs as `core/campaign-from-brief` definitions plus campaign code steps in
`plotroom-campaign-flow`; doc 25 §4.2's `Stage` enum is superseded (I38-STAGE; D025).

| Stage (doc 25 §4.1) | What runs |
| --- | --- |
| S0 intake | Quote-checked Fill of closed fields; `ModSetOption` and the mod-set picker, the four-level unit menu, variant chips, CfgGroups squads (I42-25); target profile; realism setting |
| S1 premise | Three premise cards via `map`, then an `ask` |
| S2 bible | Story-bible rows via `map` over roster slots (doc 25 §8), including thread lifecycle fields, the MoralComplexity chip and value tags (I34-25) |
| S3 outline | Outline Picks → `campaign.fill_defaults` (draft-first: the whole campaign compiles and lints clean before any further model step; code-owned generator defaults from doc 35, I35-GEN) → `approve` in the Plotline Flow view → `commit` |
| Gates after S3 and S4 | Horizon mix and interesting-decision checks as code gates; a playable skeleton early; few weighty Picks with safe defaults (I36-25) |
| S4 state | Campaign state schema |
| S5 concepts | `map` over nodes: archetypes, patterns, moment cards and twist catalogues from data (I35-26, I36-26, I34-26, I35-MOMENT) |
| S6 build | Deterministic mission build per node |
| S7 text | `map` over text slots with one-slot fill rules (I34-25); eligible for Economy mode |
| S8 verify | Campaign compile, Path Explorer, lints |
| S9 | Not a step: Preview is a user button; each refine request is a scoped `core/campaign-refine` run |

- **Draft-first invariant** (doc 25 §10.1): once the skeleton exists, code fills every node with a default mission and every slot with
  template text. A run with no model yields the same valid campaign with template text (E10; doc 38 AT-W11).
- **Human edits win.** Edits made during a run make fields human-owned; scoped regeneration uses the kernel's three-way merge and
  lock-based regeneration (I34-25); every element opens its decision record (doc 25 §9; D010).
- "Make a follow-up campaign" defaults to doc 36's rule of 33s (I36-25). The outcome-matrix builder of doc 35 rc82 and the
  follow-up workflow are v1 candidates inside OWQ-13 (a)'s classic-pattern scope; whether they make v1.0 is a roadmap sizing call
  (roadmap §10 item 5).
- **v1 ships the classic patterns** (owner, OWQ-13 (a)): the typed campaign model, Plotline, the Tote, Path Explorer, import and
  preserve, and describe → generate → edit with a no-model path. **The strategic layer is the first milestone after v1** (OWQ-13 (a);
  I35-29, I34-29, I36-29), but "Operation Grey Heron" (doc 29 §8; D005) is built early as a **synthetic structural fixture** to
  stress the campaign model, compiler and runtime.

## 11. The three dials (D024)

| Dial | Governs | Never governs |
| --- | --- | --- |
| **Autonomy** (Ask / Propose / Confirm, the default / Auto) | Every wait for a click; undo-group boundaries; a per-run "check-ins" choice on the plan card | Checks, budgets |
| **Effort** (Quick / Standard / Thorough / Max) | Budgets only: K maximum, R, shape ceiling, verification depth, retrieval, provider reasoning (doc 21 §7.1) | The checks; user gates (DG013) |
| **Role binding** (router, writer, scripter, explainer, play-tester, translator) | Which model setup does which job, set explicitly in Settings; the setup used equals the setup shown | Silent escalation (never) |

A stronger model is only ever a visible button with its cost (doc 21 §1.4; DG022 decides whether one same-model effort re-run is
allowed).

## 12. Budgets and cost as usability (D026; doc 40)

```rust
pub struct Ledger { scope: LedgerScope /* Run > Stage > Step > Attempt */, turns: u32,
                    tokens: TokenCounts /* in, cache read, cache write, out, thinking */, wall: Duration,
                    cost: Option<MicroUsd> /* integer money, never a float */, prices: PriceTableVersion }
pub struct Caps { run: Budget, session: Budget, month: Budget }      // the tightest wins; exceeding one → BudgetLimited
```

- **Prices are dated data** in `models.toml` `[[price]]` rows keyed by (provider, model, mode, effective_from) with `as_of`, source,
  cache minimum, read and write multipliers and TTL; no price in Rust; a "prices may be out of date" chip after 60 days; the editor
  never fetches pricing pages (I40-14; D026).
- The **plan card** prices a run before it starts, with the $0 AI-off alternative beside it; the **run panel** shows a live meter and
  "cache saved"; caps end in a resumable `BudgetLimited` state.
- Levers (doc 40 R-rules): effort floors per shape (DG020), adaptive K (DG021), output caps per shape and effort (R8), cache
  namespaces (R4), a `CachePolicy` per provider with wire tests (R10), warm-first fan-out (DG027), exact memoisation by capsule hash
  (R13), local-first Pick and Fill when a qualified local setup is bound (R14), an explicit Economy mode on batch APIs for bulk text
  (R12; its user-facing name comes from the design round's names table, OWQ-08 (a)).
- **Cloud setups (proposal, doc 48 §7.1; D021 amendment note):** an aggregator setup carries its provider route (endpoint tag,
  precision, no fallbacks, required parameters) and, for user content, zero-data-retention and no-data-collection flags; the serving
  host is recorded per call and shown in the run panel; setups are compared by cost per correct decision, not price per token. No cloud
  measurement exists yet: the owner deferred doc 48's round 1 until doc 49's local results are in (owner decision, 2026-09-27).
- The plugin manager shows each plugin's tool-schema token cost (doc 40 R5).
- Not done (doc 40 §8): semantic caching, prompt compression, model-written summaries, learned routers, silent model switches.

## 13. Model Manager (D022, D037; doc 44 §5.3)

- A **Settings feature, never an agent tool**: the user browses, downloads, deletes and selects models; every download is started
  by the user; Wilco does not suggest downloads on its own (D008; doc 44 §5.3).
- **Hardware first:** GPU name, total and currently free VRAM, system RAM and the available backend (the user's server, the managed
  server, CPU).
- **Fit from measurements, never file size:** manifest rows carry the measured memory increase at a stated context size and
  tokens/s on reference GPUs; badges Fits / Tight / Partial offload / CPU only.
- **Per-step badges, not a score** (Pick, Fill fields, explanation, text candidates, knowledge "No; cards are shown instead").
- The recommended list is a pinned `models.toml` manifest (repository, revision, file, bytes, SHA-256, licence, chat template id),
  updatable without a release. **Which models it may hold is decided (owner, OWQ-19 (a);
  [D037](../decisions/D037-model-manager-recommended-list.md)):** OSI licences with no
  field-of-use limits, and only models that passed Plotroom's qualification. Every other model, including any Hugging Face file the
  user picks, installs as **"custom"**: its licence and use policy are shown, the user accepts them explicitly, and it carries an
  "unqualified" badge until qualified. **Proposal:** an update between releases is itself a download from a user-enabled source under
  D008 (off by default, blocked offline, signed or hash-checked, fetched only when the user asks); without that source the manifest,
  and the `[[price]]` rows it carries (§12), change only with releases.
- **Manifest fields doc 46 §4.1 shows are needed (proposal):** the quant label from the file name (UD-Q4_K_XL and Q4_K_M report the
  same GGUF file type); the measured tensor-type mix; **both licence fields**, the model card's and the GGUF's `general.license`, read
  at the pinned revision, where a mismatch blocks a recommendation until resolved (Gemma 4 E4B QAT: `gemma` in the file, Apache-2.0 on
  the card); `general.sampling.*` defaults; a chat-template hash; the thinking default and its switch; whether a vision projector is
  needed; measured fit per backend and context.
- **Provisional defaults for 8 GB GPUs (research, doc 46 §4.1; not decided):** Gemma 4 E4B QAT (Unsloth's uniform Q4_0 file, despite
  its "UD" name) once its licence mismatch is resolved and Google's QAT file is measured, or Qwen3.5-4B Q4_K_M as the equal
  alternative; not the 4-bit UD dynamic files; one model per session. Doc 49's measured shortlist may change them (D023 amendment note).
- **Download routes (owner decision, 2026-09-27; D022 amendment note):** the primary route is the managed server with pinned GGUF files
  that **Plotroom's own downloader** fetches from Hugging Face: commit, size and SHA-256 resolved through the Hugging Face API, range
  resume from `resolve/<commit>/<file>`, hash check and an atomic install through `plotroom-io`; the sidecar then starts with
  `-m <file>`, never `-hf`, which cannot pin a revision. The managed server's own binary is a pinned, hash-checked download under the
  same rules. The user's own Ollama or LM Studio remains a bring-your-own route. "Check this model on my machine" runs the
  `plotroom-evals` port of the local suites on any installed model. **Proposal (D008 applied):** a pull through the user's Ollama
  (`/api/pull`, including `hf.co/` names) is a loopback call that makes a third-party process download, so it counts as a download
  from the source it names: that source must be enabled, the call is refused in offline mode, and only a user click starts it.
- **Refuse what the pinned runtime cannot run (owner decision, D022 amendment note; doc 47 §2.7):** a GGUF with a tensor type or
  metadata (for example a fork's rotation keys) that the pinned runtime does not declare support for is refused before loading,
  because a stock build may load it and generate nonsense. Fork runtimes are never downloaded or supervised; the user may point
  Plotroom at one as a bring-your-own endpoint, and its model stays "unqualified" until `plotroom qualify` passes on that runtime.
- Storage panel and component presets (I34-13; doc 34 mo05, mo18); the model is unloaded before Preview launches the game; one
  model per session on an 8 GB GPU by default; no CUDA runtime bundled (D022 item 2).

## 14. Safety

- **Trust labels** (doc 21 §9): mission, addon, plugin and feed text is untrusted and reaches a model only as quoted data; hidden
  characters render as markers; our own template markers are escaped; every capsule is counted before sending.
- **Egress** exists only in `plotroom-net`, and every request needs an `EgressGrant` issued by Settings, the plugin manager or the Model
  Manager after a user gesture ([extensibility.md §8](extensibility.md)).
- AI-written script passes doc 24 §5.3's policy at admission and is never run automatically.
- Injection fixtures (mission text addressing the assistant) must change nothing ([testing-strategy.md §9](testing-strategy.md)).

## 15. External agents

The opt-in, loopback-only, token-authenticated MCP server exposes the registry's product tools and `workflow.list/start/status/cancel`;
externally started runs wait for an editor click, decision points are answered only in the editor, and plugin tools are never
re-exported ([extensibility.md §10](extensibility.md); doc 38 §9). **It ships in v1** (owner, OWQ-15 (a)); `workflow.decide` for
external deciders comes after v1, journaled with an `External` origin and excluded from model qualification.

## 16. Open questions

1. Whether rig or thin clients carry the wires (the provider spike; D021 "Revisit if").
2. Menu cap per tier and whether facets cost more than they save (DG006; bench E4).
3. Journal storage, retention and the replay-record export rule (DG017).
4. What voids a qualification record (DG012); product qualification counts (doc 21 §12.3).
5. *Answered 2026-09-27:* the v1 campaign flow is the classic patterns (OWQ-13 (a)); external agents answer no decision points in v1
   (OWQ-15 (a)). Still open: whether the outcome-matrix builder and the follow-up workflow make v1.0 (roadmap §10 item 5).
6. Capsule order (DG019), effort table (DG020), same-model re-run (DG022), fixed cloud schemas (DG024), cloud budget and cache
   minimum (DG025), candidate diversity without temperature (DG026).
7. Out-of-process embedded inference as a refinement of D022 (design-gap candidate).
8. Whether the user-started upstream CUDA build is offered on NVIDIA cards (doc 49's CUDA-versus-Vulkan measurement), and whether a
   compact JSON grammar recovers Gemma's pretty-printing cost (doc 46 OQ5).

## Verification notes

### Owner answers folded (2026-09-27)

- Folded from `OWNER-QUESTIONS.md` (answers of 2026-09-27) and the owner's runtime decision of the same day (D022 amendment note):
  §3 (primary runtime, CUDA option, sampler pins), §10 (OWQ-13 (a)), §12 (OWQ-08 (a)), §13 (OWQ-19 (a), download route, refusal
  rule), §15 (OWQ-15 (a)), §16. Numbers in §3 and §13 are doc 46's measurements on one 8 GB Pascal GPU; the sidecar start-up
  sequence, manifest fields, provisional defaults and cloud-setup notes remain proposals.

### Consistency review of the owner answers (2026-09-27)

- §13 now cites D037 (the OWQ-19 record) where it had a placeholder, and §3's doc 46 figures carry doc 46's own qualifiers (Ollama's
  backend not logged; the memory saving is measured against Ollama's library builds, which include vision parts). No design changed.
