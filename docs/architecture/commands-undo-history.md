# Commands, undo and history

> **Status:** proposal (architecture baseline 2026-09-27). Nothing here is decided unless it restates `AGENTS.md`, a decision
> record (`Dnnn`) or a decided DG. Type sketches are not compiled and names are not final.
> **Part of:** [architecture overview](README.md). **Main sources:** doc 17 §5; doc 21 §1.2–§1.3, §7.3, §8.2; doc 22 §4.3; doc 31
> §4.5, §8.3; doc 37 G8; doc 38 §4.3–§4.4, §7; doc 45 §2.1–§2.5, §2.8–§2.10, OQ6–OQ7; D006, D024; DG011, DG013, DG017.

Every change to a Plotroom project, from a mouse drag to a Wilco turn, a workflow step, a plugin batch or an MCP call, goes through one
path: **propose → plan → admit → commit** into one undo group tagged with its origin (doc 21 §1.2; doc 45 §2.2). This file owns that
path: the command representation, the registry, admission, commit hooks and lowering timing, undo groups, gestures, the project-wide
history, dirty tracking, the separation of view state, and the logic step that drives it all.

## 1. The rule

"If the GUI can't do it, the LLM can't do it" (doc 17 §5; doc 21 §1.3) is enforced here in its strict form: **nobody changes a
document except through an admitted `EditorCommand` batch.** The store's trees are unwritable outside an open group
([core-document-model.md §5](core-document-model.md)); every client submits a `Proposal<CommandBatch>` to one bus; only the logic
step commits.

## 2. Command representation

```rust
// Per-area data enums live next to the model they change (L3), so the outer enum can sit above every model with no upward edge.
// plotroom-mission::cmd
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
pub enum MissionCmd { AddUnit { .. }, SetFields { targets: NonEmpty<ElementRef>, key: FieldKey, value: FieldValue },
    MoveEntities { targets: NonEmpty<ElementRef>, delta: MapDelta }, AddWaypoint { .. }, Link { .. }, Sync { .. }, Delete { .. }, .. }

// plotroom-commands (L4): the one closed set of document commands.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
pub enum EditorCommand {
    Mission(MissionCmd), Ext(ExtCmd), Briefing(BriefingCmd), Stringtable(StringtableCmd), Script(ScriptCmd),
    Campaign(CampaignCmd), Module(ModuleCmd), Cine(CineCmd), Sidecar(SidecarCmd), Project(ProjectCmd),
    Fix(FixCmd), Power(PowerCmd),
}
pub struct CommandBatch { label: LabelKey, commands: NonEmpty<EditorCommand> }
```

**Why closed data enums (resolving the three proposals).** One proposal used a closed enum, one registered trait objects with untyped
arguments, one batched `Box<dyn EditorCommand>`. Commands must be **serialisable, hashable and comparable**: the workflow journal
digests the batch it intends to commit, the crash journal replays batches, MCP and plugins send them as JSON, cassettes key on them,
and property tests assert that the applied diff equals the planned one. Data enums also give exhaustive matching (`AGENTS.md`) and
`schemars` schemas for Wilco's tool manifest and the MCP server. Trait-object batches are rejected.

- **Planning next to the model.** Each area implements
  `fn plan(&self, doc: &AreaDoc, cx: &PlanCtx<'_>) -> Result<Vec<Op>, Rejection>` in its own crate. Commands that span documents
  (a rename used by a campaign and two missions, a campaign edit that updates mission stubs) are planned in `plotroom-commands` over
  the whole `Snapshot`, usually by expanding into per-area commands.
- **Services through traits, not edges.** `PlanCtx` carries trait objects defined in the kernel and implemented higher up:
  `FieldChecker` (Teller's `check_field`), `FactSource` (catalog, terrain), `IdSource`, `Clock`. The session injects them.
- **Heavy plans off the UI thread.** A command flagged `CostClass::Heavy` (large paste, power tool over hundreds of units, a
  generator's change set) plans on a worker against the published snapshot and is applied only if its read set is still fresh.
- Area modules stay under ~600 lines each (units, groups, waypoints, triggers, markers, intel, sync, ext, briefing, stringtable,
  script, campaign, module, rule, cine, power, project); doc 45 §2.9 item 5.
- View changes (selection, camera, folds, hover) are `ViewCmd`s. They never enter history and never dirty a document (§10).

## 3. The registry

```rust
pub struct CommandSpec {
    id: CommandId,                      // stable "area.object.verb", e.g. "mission.waypoint.add"
    label: LabelKey, relabel: Option<LabelKey>, area: Area, tier: Tier, concept: Option<ConceptId>,
    keys: PerOs<Vec<Shortcut>>, effect: CommandEffect, reach: Reach, destructiveness: Destructiveness,
    since: ApiVersion, schema: SchemaRef, profiles: ProfileSet, cost: CostClass,
}
pub enum CommandEffect { None, ReadDocument, WriteDocumentUndoable, OfferPreviewButton, UserFileDialog, ViewOnly }
pub enum Reach { AgentCallable, UserOnly(UserOnlyReason) }         // e.g. UserOnly(OpensFileDialog), UserOnly(LaunchesGame)
pub enum Destructiveness { Safe, Destructive { confirm: ConfirmKind } }
```

- Enums, not bit flags, for effect, reach and destructiveness (`AGENTS.md` "enum state machines over boolean flags").
- `CommandEffect` is the command's own effect class. It is distinct from doc 21 §1.3's agent effect table, which this architecture
  names `AgentEffect` ([agent-runtime.md §2](agent-runtime.md)); two enums called `Effect` would collide.
- **One registry, many surfaces.** Menus, the command palette, map hotkeys, semantic action ids and keymap profiles (I34-05-06; doc 34
  le06), Drill step palettes, Wilco's tool manifest, the outbound MCP server's tools and the vocabulary plugins may `propose` are all
  generated from it (doc 45 §2.8). Tool schemas and descriptions come from `///` docs via `schemars`, with a hidden list and a depth
  cap. Errors tell the caller how to repair the call ("call `list_commands` for valid ids").
- **Tests:** a per-OS shortcut-clash test; a schema snapshot of every `CommandSpec`; every `Reach::AgentCallable` command belongs to a
  workflow or to the read-only query set (doc 21 §6.4).

## 4. Plan → admit → commit

### 4.1 The pipeline

```rust
pub struct Proposal<T> { value: T, reads: RevisionSet, writes: WriteSet, trust: TrustLabel, origin: Origin,
                         intent: Option<UserIntent> }
pub struct Admitted<T> { value: T, reads: RevisionSet, revision: Revision, repaired: u8 }  // constructor private (DG011 option C)
pub struct Rejection { findings: NonEmpty<Finding>, allowed: Option<AllowedValues>, repair: RepairHint, hook: Option<HookId> }
```

1. **Submit.** A client puts `Queued { source, proposal, location }` on the bounded command bus (§11).
2. **Plan** on a `Scratch` fork of the current snapshot (pure). The plan records ops, read set, write set and a semantic diff.
3. **Admit.** The mandatory check families run (§4.2). Success yields `Admitted<PlannedBatch>`; only the admission module can build it.
   A rejection never enters history; it returns typed findings and, where code can compute them, the allowed values, so a repair turn
   or a user question needs no prose (doc 21 §1.2).
4. **Resolve pending previews.** If a proposal preview (ghosts, a diff card) is open, it is accepted as one group or discarded
   before any save, export, Preview launch or other command (doc 45 §3).
5. **Commit hooks** run at the outermost commit, in a fixed order (§5).
6. **Apply** the same recorded op list on `LiveTx` inside the open group. Debug builds and property tests assert that the applied diff
   equals the planned diff (OpenTTD's test-run idea, doc 45 §2.2 item 6).
7. **Publish.** Push the group to history, `rev += 1`, publish `Arc<Snapshot>`, append the crash op journal, then fire change events
   (events after the history update, doc 45 §2.2 item 3), and reply to the requester with the `GroupId` or the rejection.

### 4.2 Mandatory admission checks and the core builder

| Family | What it checks | Implemented by |
| --- | --- | --- |
| Field check modes | Every script-bearing field passes engine-parity `check_field` in its mode (doc 23 §13.3 item 3) | Teller |
| Cardinality and engine limits | 12 units per group, groups per side, radio slots and other compiler-owned singletons (doc 31 §4.5) | `plotroom-validate` limits |
| Reference integrity | No new dangling reference; syncs, `idVehicle`, marker links | `plotroom-project` reverse index |
| Profile and capability policy | Everything used is available on the target profile, or an opted-in capability; editor glue stays in the conservative subset (D003) | `plotroom-profile`, `plotroom-validate` |
| Script-risk policy | Non-user origins may not introduce `deny` or risky commands under doc 24 §5.3 | `plotroom-validate` risk rules |
| Ownership | Non-user writes to human-owned or pinned fields need `UserIntent` ([core-document-model.md §8.1](core-document-model.md)) | `plotroom-project` |
| Read-set freshness | A changed read entity re-runs the checks; admit if they pass and no target became human-owned or pinned, else recompute or drop with a note (DG011 option C, proposal) | `plotroom-commands` |

The session assembles the core through a **typestate `CoreBuilder`** that cannot `build()` until every family above is supplied, so no
assembly path (GUI, CLI, test harness) can skip a check family:

```rust
let core = CoreBuilder::new(store)
    .field_checks(teller.checker())          // CoreBuilder<NoChecks> → CoreBuilder<FieldChecks> → …
    .reference_integrity(project.ref_index())
    .profile_policy(profile_policy)
    .ownership(ownership_rules)
    .build();                                // only callable on CoreBuilder<AllChecks>
```

### 4.3 Origins and group boundaries

The origin of a group follows its source (`Origin`, [core-document-model.md §8.1](core-document-model.md)). Where one run ends and
the next group begins follows **autonomy**, not effort (DG013 decided; D024): Confirm autonomy gives one group per Wilco turn; Auto
gives one per workflow step; a plugin batch is one `Origin::Plugin` group; "fix all N" is one labelled group (doc 21 §7.3; doc 45
§2.2 item 2).

### 4.4 `UserIntent`: consent as a type

```rust
pub struct UserIntent(GestureToken);   // minted only by plotroom-session from real UI input or an explicit CLI invocation
```

- Required to: overwrite a human-owned or pinned field; start a model workflow; approve a plan card; accept an egress card; launch
  Preview or an in-game validation; switch on an engine capability that narrows who can play the content (docs/upstream README,
  "From a shipped change…", item 5).
- **Unforgeable by construction.** The minting API lives in `plotroom-session::intent` behind a sealed input-source type that only
  the UI input adapter and the CLI argument parser construct. The agent, workflow runtime, plugin host and MCP crates may not depend on
  `plotroom-session` at all; `xtask layers` fails the build if they do ([crate-map.md §2.5](crate-map.md)). External MCP requests can
  therefore never carry intent; an externally started run waits for an editor click (doc 38 §9).

### 4.5 Proposals from long-running work

Workflow steps, Wilco turns and plugin runs compute on snapshots off the UI thread and submit proposals stamped with their read set.
"Run concurrently, mutate serially" (doc 38 §4.4): the user's own edits never wait for a run; a proposal whose reads changed is
re-verified at commit (§4.2, freshness). A run that fails, is cancelled or exhausts its budget leaves the document and history
untouched; its output survives only as an inspectable proposal (doc 45 §2.2 item 7).

## 5. Commit hooks and when lowering runs

**Decision (proposal), resolving the judges' "eager versus lazy lowering" conflict.** Lowering is **eager and incremental for
document content, on demand for whole-campaign compilation, and a lowering bug never refuses an unrelated edit.**

Doc 31 §8.3 needs emitted map entities to be real, editable document entities with region states, and the split view to update
live as a form field changes. That rules out purely lazy lowering at save time. But running every compiler inside every user edit
couples plain edits to compiler bugs and grows latency. So:

| Hook (in order, at the outermost commit) | Scope | On failure |
| --- | --- | --- |
| 1. Template and linked-set propagation | Only into fields that are neither overridden nor human-owned | Invariant violation → refuse the group |
| 2. Incremental lowering (`plotroom-lower`): attributes, modules, rules, cutscene nodes, compiler-owned singleton allocation, region-state updates | Only elements whose **declared input set** the group touched | See the two failure classes below |
| 3. Reference integrity | Reverse index updated; a dangling reference stays byte for byte and becomes a diagnostic, never a silent tidy | Invariant violation → refuse |
| 4. Identity bookkeeping | New ids, reserved ids, locators | Never fails on valid ops |

- **Failure class 1: invariant violation.** The output would corrupt the document or break an engine hard limit (13 units in a group,
  a radio slot clash, a dangling reference). The whole group is refused with a typed `Rejection` naming the hook and the element, but
  only when the group touched that element's inputs.
- **Failure class 2: lowering error.** The element cannot be lowered for the target profile, or the compiler fails. Its owned regions
  keep their last good content, marked `Stale`, and a diagnostic is raised. Plain edits elsewhere are never refused.
- **Not in commits:** campaign compilation (sockets, routers, finisher, `saveVar` layout; doc 19 §7) runs on demand at verify,
  export and Preview; validation runs on workers (§11); Teller's index rebuilds on a worker.
- In-commit lowering always uses `EmitMode::Export`. `PreviewTrace` and `Debug199` exist only in Preview staging
  ([game-integration.md §9](game-integration.md)).
- A per-hook latency budget test keeps commits cheap; the budget numbers are set by the M2 benchmark.

This is a design-gap candidate because doc 45 §2.2 item 4 refuses the whole group on any hook failure ([README](README.md) §8 item 5).

## 6. Undo groups

```rust
pub enum OpenGroup {                                        // one slot per project; an enum state machine (doc 45 §2.2)
    Idle,
    Started  { token: GroupToken, kind: GroupKind, scope: TxScope },
    Modified { token: GroupToken, kind: GroupKind, scope: TxScope, ops: Vec<Recorded>, merge: Option<MergeKey> },
}
pub enum GroupKind { Gesture(GestureId), Dialog(DialogId), Paste, AgentTurn(TurnId), WorkflowStep { run: RunId, step: StepId },
    PluginBatch(PluginId), QuickFix(FixId), PowerTool(ToolId), Migration(MigrationId), Import(ImportId), DrillStep(StepId),
    External(ClientId) }
pub enum TxScope { Atomic, Live }
pub struct UndoGroup { id: GroupId, commit: CommitId, origin: Origin, label: LabelKey, ops: Vec<Recorded>,
    touched: BTreeSet<DocumentId>, selection_before: Vec<ItemRef>, selection_after: Vec<ItemRef> }
```

- **Open, join, end.** A pointer-down, a dialog OK, a turn start or a workflow step opens the slot. A begin while a group is open
  joins it, so sub-steps fold into their parent (TrenchBroom, Graphite; doc 45 §2.2 item 1). Ending a `Started` group leaves no
  history entry. Abort (Esc, a failed or cancelled run) applies the inverses in reverse order.
- A scoped Rust guard is only sugar for synchronous work such as one quick fix; dropping it uncommitted rolls back. Gestures and
  streamed Wilco turns span frames, so the slot is state, not a lexical guard.
- `CommitId` is a 128-bit id written into the sidecar project log at save, so the workflow journal can reconcile `CommitApplied`
  records after a restart even though history itself is session-only (doc 45 §2.2 item 9; DG017).

## 7. Gestures, live edits and merging

- **Map drags** keep a `DragPreview { ids, delta }` in view state and emit no ops until release; release commits one `MoveEntities`
  (Twine, doc 45 §3). The renderer draws the preview over a cached static layer.
- **Slider scrubs, rotation and similar continuous edits** open a `TxScope::Live` group: ops apply to the store and snapshots are
  published with `live: true`, which only the renderer and inspector read. Commit hooks, validation, Wilco reads, Plotline relayout
  and journal appends happen at gesture end. This answers doc 45 OQ6 with "apply with observability flags" (proposal; design-gap
  candidate), because an overlay the renderer reads would duplicate every read path.
- **Merging.** Only adjacent groups with the same `MergeKey { gesture, targets, field }` and the same origin merge; a merged change
  that returns to the original value is dropped as obsolete; a time window applies to typing only, through the injected `Clock`
  (Tiled, Atlas, Blockly; doc 45 §2.2 item 5).
- **Undo-spam detector.** Debug builds warn when more than 10 undo points appear within 20 frames, catching widgets that open a group
  per frame (rerun, doc 45 §2.2 item 9).

## 8. One project-wide history

- **One history per project.** Groups record every document they touched; undoing a group that touched a closed mission opens it
  headlessly (`DocSlot::Closed`, [core-document-model.md §2](core-document-model.md)).
- **Lanes are filtered views**, never separate stacks: by origin (user, Wilco turn, workflow run, plugin, migration) and by document.
  "Undo last Wilco change" (doc 34 ed22; I34-21) is revert-in-a-lane.
- **Out-of-order revert.** Reverting a group that is not on top requires its ops to commute with every later group: disjoint targets
  and fields for CST ops, non-overlapping ranges for text ops after transforming them through later `ReplaceText` ops, and no later
  `SetList` over the same list. If they commute, the revert is a new group. If not, the user gets a no-clobber conflict card ("revert as
  a new change" with a field-level view); later human groups are never touched (doc 45 §2.2 item 8, OQ7).
- **Hygiene.** History is session-only; the history type does not implement `Serialize`, checked statically (rerun). It survives
  Preview (doc 09 S1) and survives catalog, mod-set, target-profile and schema changes, because those are commands too. It is trimmed
  by whole groups under a memory budget, with a visible "older history trimmed" row.
- **History UI** ([ui-shell.md §6](ui-shell.md)): clickable entries with localised labels; click to rewind or replay; filter by
  origin and document; after undo or redo the map pans to the affected area and pulses it (doc 45 §2.2 item 11).

## 9. Dirty tracking

- `dirty(doc) = saved[doc] != current_revision(doc)`, per document, **sidecar-only edits included**; undoing back to the save point
  makes the document clean again (Graphite, TrenchBroom, Tiled; doc 45 §2.2 item 10).
- Saves run on the I/O thread from a snapshot and report `Saved { doc, rev }`; dirty state stays correct when the user keeps editing
  during a save ([core-document-model.md §11](core-document-model.md)).
- A pending proposal is resolved before a save (§4.1 step 4); a test asserts that saving with a pending proposal writes the
  pre-proposal bytes.

## 10. Selection and view state

```rust
pub enum ItemRef { Unit(EntityId), Group(EntityId), Waypoint(EntityId), Trigger(EntityId), Marker(EntityId),
    Module(ElementId), Rule(ElementId), CampaignNode(ElementId), CampaignEdge(ElementId), StateVar(ElementId), Shot(ElementId),
    Line(LineId), BriefingSpan(DocSpan), ScriptSpan(DocSpan), Diagnostic(DiagId), Journal(JournalKey) }
pub struct ViewState {                         // plotroom-view; never serialised into documents, never dirty
    selection: Selection /* private; changed only by ViewCmd */, hover: DoubleBuffered<Option<ItemRef>>, camera: MapCamera,
    mode: MapMode /* F1–F6 */, drag: Option<DragPreview>, ghosts: Vec<PreviewEntity>, seen: SeenSet, nav: SelectionHistory,
    detail: Detail /* Easy | Advanced, default Advanced (D029) */, folds: FoldState }
```

- One `ItemRef` is shared by the map, outliner, inspector, Problems list, Plotline, the Tote, history and Wilco's citations (doc 45
  §2.4). Stale refs are purged at the start of each step; back/forward navigates selections.
- `resolve_targets(&Selection, CommandKind) -> Targets` holds the engine's rules in one place (a waypoint acts on its group; per-unit
  attributes act on a group's units; linked-instance members conflict). **Commands carry explicit targets**, so fixes, Wilco and
  plugins never rewrite the user's selection; Wilco may only propose a highlight.
- Each undo group stores the selection before and after it, so undoing a delete reselects the restored units.
- Camera, folds, per-user hide and lock, the "new since you looked" set and dock layout live in app data.

**Dialogs are Scratch sessions.** The original editor copies the edited struct when a dialog opens, validates in `CanDestroy` and
writes back in `Destroy` (doc 03). Plotroom maps that lifecycle exactly:

```rust
pub struct DialogSession<'doc> { display: &'doc DisplaySpec, scratch: Scratch, targets: Targets, detail: Detail }
```

- Opening forks a `Scratch`; controls are filled through descriptor bindings (IDC → `FieldKey`); **syncing values into controls
  emits no commands** (doc 45 §2.5; tested for every control type).
- OK builds a batch of **only the fields the user changed**, runs admission (whose plan step hosts the original `CanDestroy` parity
  checks: `check_field`, identifier rules, uniqueness) and commits one `GroupKind::Dialog` group. Cancel drops the scratch. The
  stock dialogs' destructive round trips (for example a time rounded to five minutes) are documented as `StockQuirk`s and never
  replayed (doc 37 §3).
- Wilco and plugin proposals for the same fields pass exactly the checks a user's OK click passes.

The **map interaction state machine** (F1–F6 modes, hit-test priorities, insert, rubber band, rotate, drag-to-link, the 100 m
auto-join into groups, Del versus Shift+Del; doc 03) lives headless in `plotroom-view`, turning abstract input events into `ViewCmd`s
and `EditorCommand`s; its behaviours are ported as documented tests ([testing-strategy.md §6](testing-strategy.md)).

## 11. The logic step: `Session::step`

`plotroom-session` is a library. `Session::step(inputs) -> outputs` is the single place where documents change, and the same function
drives the egui app (`eframe::App::logic`), the headless `plotroom` CLI and the `EditorHarness` tests (doc 45 §2.9).

```rust
pub enum CommandSource { Ui(GestureId), View, Dialog(DialogId), Workflow { run: RunId }, Wilco { turn: TurnId },
                         Plugin(PluginId), External(ClientId), Cli }
pub struct Queued { source: CommandSource, proposal: Proposal<CommandBatch>, location: &'static Location<'static> /* debug */ }
```

One step, in order:

1. Repair view state (purge stale refs, swap hover buffers).
2. Drain the bounded command bus; plan, admit and commit each batch (§4).
3. Publish the new `Arc<Snapshot>`.
4. Drain worker, runtime, Preview, download and I/O results; drop or re-verify results stamped with a stale revision.
5. Coalesce `Revalidate`, `RebuildDrawList` and `RelayoutPlotline` to at most once per step and schedule them on workers.
6. Emit effect requests (save, stage, launch, download) for the edge services; the session itself performs no I/O.

Threading, channels and budgets are in [ui-shell.md §10](ui-shell.md).

## 12. Open questions

1. Live groups: confirm "apply with observability flags" against crash and journal semantics (doc 45 OQ6).
2. The conflict view for a non-commuting revert, and the exact commute rules for `SetList` (doc 45 OQ7).
3. The history memory budget and trimming thresholds.
4. Which commands are `CostClass::Heavy`; per-hook latency budgets (set by the M2 benchmark).
5. Whether the lowering failure classes need a third class ("refuse only if the user asked for this module's output now").
6. The `CommandId` naming scheme's stability promise for plugins and MCP clients (`since` and deprecation).
