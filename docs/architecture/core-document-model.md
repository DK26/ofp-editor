# Core document model

> **Status:** proposal (architecture baseline 2026-09-27). Nothing here is decided unless it restates `AGENTS.md`, a decision
> record (`Dnnn`), a decided DG or an owner answer (`OWQ-nn`, all answered 2026-09-27). Type sketches are not compiled and names are
> not final.
> **Part of:** [architecture overview](README.md). **Main sources:** doc 04 §3, §9, §12–§13; doc 07; doc 19 §4, §7.6; doc 25 §8–§9;
> doc 31 §4.4–§4.5, §8.3; doc 37 §3, §7–§8; doc 45 §2.1–§2.7, OQ1–OQ9; D017; DG004, DG005, DG011, DG017.

This file owns what a Plotroom project *is* in memory and on disk: the documents, the three layers of every config file, the ops that
change them, the guarded store, snapshots, identity, provenance and generated regions, the authoring models, the sidecar and the
round-trip guarantees. How ops are grouped into commands, undo and history is in [commands-undo-history.md](commands-undo-history.md).

## 1. Principles for the model

1. **Lossless by default.** `render(parse(bytes)) == bytes`. An edit patches the concrete syntax tree (CST); it never re-serialises the
   file. Unknown keys, comments, directives, duplicate keys and raw number spellings round-trip (doc 04 §12.3; D017).
2. **One mutation path.** Document trees are only writable inside an open undo group; loading records nothing (doc 45 §2.1).
3. **Identity is ours.** Engine file ids (`id=`, sync ids, `ItemN`) are renumbered by the game's own editor on every save (doc 04 §3.9),
   so Plotroom keeps 128-bit ids in the sidecar and re-matches after an external save (doc 45 §2.3; D017 item 6).
4. **The mission runs with the sidecar deleted.** Engine files hold engine data only; everything Plotroom-specific lives in the sidecar
   (doc 37 G2; doc 45 §2.7).
5. **Provenance on every element.** Who made it, from what, and which fields a human owns; regeneration never clobbers human work
   (`AGENTS.md`; D010; doc 25 §9).
6. **Pure where possible.** Parsers, lenses, planners and compilers are pure functions of their inputs; ids, clocks and seeds are
   injected (`AGENTS.md` parser rules; doc 38 §4.2).

## 2. Project and documents

A **project** is one optional campaign plus N mission folders and their side files. Opening a single mission folder is a project of
one mission. The model is multi-document from the first milestone, because one Wilco turn or one workflow step can touch a campaign,
two missions and a stringtable in a single undo group (doc 45 §2.2).

```rust
// plotroom-project (L4). Proposal-only.
pub enum Document {                        // exhaustive: a new kind is a compile error at every site that must handle it
    Mission(MissionDoc),                   // mission.sqm: CST + typed lens
    DescriptionExt(ExtDoc),                // description.ext: CST + ext lens (doc 04 §5)
    Briefing(BriefingDoc),                 // one per language file (doc 04 §6)
    Stringtable(StringtableDoc),           // CSV CST + row lens, per-language columns (doc 04 §7)
    Script(ScriptDoc),                     // SQS/SQF text buffer + lexer spans (doc 23 §13.2)
    Campaign(CampaignDoc),                 // campaign description.ext CST + CampaignModel (doc 19 §4)
    Opaque(OpaqueFile),                    // any other file in the folder, kept byte for byte
}
pub enum DocSlot { Open(Document), Closed { path: ProjectPath, base: ContentHash } }
```

- `DocSlot::Closed` lets undo of a group that touched a closed mission load that mission headlessly (doc 45 §2.2 item 8).
- `Opaque` keeps unknown files byte for byte (permissive on unknown content, `AGENTS.md` parser rules).
- A binarized (raP) `mission.sqm` opens **read-only** with an explicit "Convert to text" command; the game's own editor refuses raP
  (doc 04 §4) and byte patching needs text.

## 3. The three layers of a config file

Every config-format file (`mission.sqm`, `description.ext`, the campaign `description.ext`) has three layers (doc 04 §12.1; D017
item 4): a lossless CST, a typed lens derived from it, and sidecar records keyed by Plotroom ids.

### 3.1 The CST: a relative-length green tree

- `plotroom-config` parses text into a CST whose nodes store **widths, not offsets** (the "green tree" shape of rowan and cstree):
  immutable, `Arc`-shared nodes, with byte offsets computed on demand by a cursor. This is what makes the two requirements compatible:
  span patching needs exact bytes, and cheap snapshots need structural sharing (§6). A patch rebuilds only the path from the edited
  leaf to the root.
- Trivia (whitespace, comments, preprocessor lines), duplicate keys and item-count mismatches are kept. Unparseable spans become
  `Opaque` islands that render verbatim.
- `ConfigOrigin { Text, Rap { version } }` records the source form (renamed from doc 04's `Origin`; doc 45 OQ2).
- Whether to depend on an existing green-tree crate or write a small one is decided by the CST spike in the first milestone; the
  candidates are MIT/Apache-licensed and GPL-compatible [I].
- raP is read (versions 2–4) and written (version 4) by the same crate (doc 07; D017).

### 3.2 The typed lens

- `plotroom-mission` derives a typed view of the four sections (Mission, Intro, OutroWin, OutroLoose), Intel, groups, units,
  waypoints, triggers, markers and effects (doc 04 §3). Fields are `Field<T> { value, at: Option<NodePath> }`; enums are
  `EnumField<E> { value, raw: Option<RawToken> }` with `Other(RawToken)` arms that keep the original spelling.
- **Unknown keys are never modelled.** They stay in the CST untouched and appear in the inspector as raw rows (doc 45 §2.5).
- **Strings are bytes** plus an encoding tag; code-page decoding happens only for display (D017 item 5). Every engine limit is
  measured in bytes of the target encoding by one function, `byte_len_in(TargetEncoding)` in `plotroom-encoding` (doc 45 §2.6).
- **Engine file ids get their own newtypes**, distinct from Plotroom identity: `VehicleId`, `SyncId`, `MarkerName`, `ClassName`,
  `VarName` (doc 04 §12.2). The type system then refuses to treat a file id as identity.
- The lens is **maintained incrementally** from each patch and indexed by `EntityId`. Invariant, checked after every test step:
  the incrementally maintained lens equals a lens re-derived from the CST.
- The campaign `description.ext` gets its own lens in `plotroom-campaign`; the mission `description.ext` lens lives in
  `plotroom-mission::ext`.
- Intel fields carry the campaign-lever and calendar roles doc 34 names (`resistanceWest/East` as a lever, cw05; weather and date as
  calendar targets, cw24), expressed as descriptor metadata rather than new keys (integration I34-04).

### 3.3 Descriptor tables

One `FieldDescriptor` table per entity kind is the single source of field facts (doc 45 §2.5; doc 37 §3):

```rust
// plotroom-mission::descriptor (and the matching tables in plotroom-campaign and plotroom-modules). Proposal-only.
pub struct FieldDescriptor {
    key: FieldKey, ty: FieldType, engine_default: Option<FieldValue>, limits: Limits,
    options: OptionSource,              // enum, catalog query (active mod set), mission names, markers
    check: Option<CheckMode>,           // CheckExecute / CheckEvaluateBool field modes (doc 23 §6)
    glyph: MapGlyph, tier: Tier, concept: ConceptId, profiles: ProfileSet,
    label: LabelKey,                    // the original label, from the user's game stringtable (D029)
    relabel: Option<LabelKey>,          // the plain-language line shown beside it (D029)
    rsc: Option<RscBinding>,            // IDD/IDC of the classic dialog control, and its Easy ("…Simple") twin
    stock_quirk: Option<StockQuirk>,    // e.g. a stock dialog rounding a value: documented, never replayed (doc 37 §3)
}
pub enum ValueSource { Explicit, Template(TemplateRef), ModuleDefault(ElementId), EngineDefault, Catalog }
```

The same table drives the classic dialogs (Easy and Advanced), the modern inspector, Wilco's Fill slot specs and Pick menus, plugin
forms, rule-builder slots, map glyphs and the live byte counters. Adding a field once updates every surface.

### 3.4 Text documents

| Document | Model | Notes |
| --- | --- | --- |
| Script (SQS/SQF) | Text buffer (rope) + lossless lexer spans from `plotroom-script` | SQS is line-oriented; the faithful line model is doc 23 §13.2's `SqsFile` |
| Briefing HTML | CST of the engine's HTML subset with spans (doc 04 §6) | Per-side and per-unit sections are symbols in Teller's index (I37-31IDX) |
| Stringtable | CSV CST + row lens with one column per language | Legacy code pages for `.csv`, UTF-8 for Remastered `.utf8.*` files (doc 04 §7); the voice-language sibling-file rule of doc 34 mo07 lives in this lens (I34-04) |

Text ops are `ReplaceText` over a range (§5.2); the lexer re-tokenises only the damaged region.

## 4. Writer rules

Taken from doc 04 §12.3, with the corrections recorded there:

1. An unchanged document saves byte-identical (text origin).
2. An edit changes only the scalar's raw lexeme. A new key goes in at the engine's canonical position, with the parent's indent and
   line ending.
3. A key reset to its default **stays written**. Only the explicit "Normalize as engine" command omits defaults, renumbers ids and
   drops what the engine would drop (it ports the engine's `Compact`/`CheckSynchro` behaviour, doc 04 §3.9).
4. `ItemN` lists stay contiguous and `items=` is updated with them; unit and sync ids are never renumbered except by Normalize.
5. Enums keep their raw token until the value changes; numbers keep their lexeme until the value changes.
6. Float formatting comes from a **writer profile**: `Legacy196Text` and `RemasteredText` (neutral names replacing the working names
   in docs 04 and 07, which embedded a third-party mark). Parity with the engine's C formatting is [U] until the writer spike compares
   against real output.
7. A safe write re-parses the output and asserts lens equality before it replaces the file (doc 04 §12.3(10)).
8. Writers default to output every profile accepts; profile-only file features (UTF-8 stringtables, `init.sqf`) sit behind the
   mission's profile (D003).

## 5. Ops and the guarded store

### 5.1 One guarded store

```rust
// plotroom-doc (L3 kernel) and plotroom-project (L4). Proposal-only.
pub struct Guarded<T>(T);                 // field private to the store module; impl Deref, never DerefMut
pub struct ProjectStore {
    docs: Guarded<BTreeMap<DocumentId, DocSlot>>, sidecars: Guarded<SidecarSet>,
    history: History, open: OpenGroup, rev: Revision, saved: BTreeMap<DocumentId, Revision>,
    ids: Box<dyn IdSource + Send>, clock: Box<dyn Clock + Send>,
}
pub trait DocMut { fn apply(&mut self, op: Op) -> Result<Recorded, Error>; }
pub struct LiveTx<'store> { store: &'store mut ProjectStore, token: GroupToken }   // exists only inside an open group
pub struct Scratch { base: Arc<Snapshot>, overlay: Vec<Recorded> }                // a fork for proposals, dialogs, import
```

- Module privacy, not a doctest, enforces the single path (`AGENTS.md` bans `compile_fail` doctests; doc 45 §2.1), plus a `trybuild`
  UI test per misuse (building `LiveTx` outside its module, mutating through a `Guarded<T>`), which proves the path is closed and pins
  the compiler's guidance text (`AGENTS.md` "Negative Compile Tests"; doc 62 §5.5–§5.6).
- `LiveTx` applies ops to the live store inside the open group. `Scratch` forks an `Arc<Snapshot>`; dialogs, importers, generators
  and Wilco ghosts build on it, and applying replays **the same op list** on the live store in one group, so what the user previewed
  is exactly what lands (doc 45 §2.1, Tiled's pattern).
- Read access comes in three tiers named after what they borrow: `AppCtx<'app>` (catalogs, settings), `DocCtx<'doc>` (snapshot,
  selection, diagnostics) and `EditCtx<'doc>` (plus the open group). Wilco and plugins only ever see `MissionQuery` scopes derived from
  `DocCtx` (doc 22 §4.3).

### 5.2 The op enum

```rust
// plotroom-doc. Serializable (serde) and hashable (a digest), so journal intents, crash journals, cassettes and the
// "applied diff equals planned diff" property can compare ops. Proposal-only.
pub struct Op { doc: DocumentId, kind: OpKind }
pub enum ElementRef { Entity(EntityId), Element(ElementId), Line(LineId) }
pub enum OpKind {
    SetField    { target: ElementRef, key: FieldKey, value: FieldValue },
    SetList     { owner: ElementRef, list: ListKey, items: Vec<ElementRef> },   // ItemN order and `items=`
    Create      { snapshot: ElementSnapshot, at: ListSlot },
    Delete      { target: ElementRef },                                         // inverse = Create at the same slot
    SetSidecar  { key: SidecarKey, value: Option<SidecarValue> },               // None = remove, so an insert has an inverse
    ReplaceText { range: TextRange, bytes: Bytes },                             // scripts, briefing and stringtable text
}
pub struct Recorded { op: Op, inverse: Op }                                     // inverse computed from live state at apply
```

- **Anchors.** CST ops address `ElementRef` plus `FieldKey`/`ListKey`, never byte offsets; offsets are computed at render time from
  the green tree. `ReplaceText` ranges are relative to the revision they were applied at (ordinary stack undo); out-of-order revert
  transforms them through later text ops ([commands-undo-history.md §8](commands-undo-history.md)).
- **"Change unit class" is `SetField(vehicle)`**, never delete-plus-create, on every path, so attributes, name and syncs survive
  (doc 45 §2.2).
- `Delete` records the element snapshot, its `ItemN` index and parent list, so undo restores identical bytes, numbering, syncs and
  selection.
- Every public mutator emits at least one op; loading emits none (tested, doc 45 §2.10).

## 6. Snapshots and structural sharing

```rust
pub struct Snapshot { rev: Revision, docs: PersistentMap<DocumentId, Arc<DocState>>, sidecars: Arc<SidecarSet>, live: bool }
```

- After each commit the logic step publishes an `Arc<Snapshot>` through an atomic swap; readers (renderer, validators, workers,
  Wilco, Preview staging, saves) never block the writer (doc 45 §2.9).
- Structural sharing: green-tree CST subtrees plus a persistent map (`imbl` or `rpds`, chosen by benchmark). Cost per commit is [U]
  (doc 45 OQ5). Targets to validate on a 5,000-entity synthetic mission: under 2 ms for a typical commit plus publish, and a stated
  p99 (doc 06 §4.10 lists the frame budgets).
- **Fallback:** if commits stall frames, the store moves to a dedicated document thread with typed request and response messages
  (0 A.D. Atlas, doc 45 §2.9 item 4). The `Session` API is already message-shaped, so only the app crate changes.
- `live: true` marks intermediate revisions of a `Live` group (drag, scrub); only the renderer and inspector read those
  ([commands-undo-history.md §7](commands-undo-history.md)).

## 7. Identity

### 7.1 Plotroom ids

- `EntityId` (units, groups, waypoints, triggers, markers), `ElementId` (module instances, rules, campaign nodes, edges and variables,
  shots, conversations) and `LineId` (every spoken or displayed line) are `u128` newtypes from an injected `IdSource`: time-ordered
  plus random in production (the ULID shape doc 34 ed16 proposes), a seeded counter in tests (doc 45 §2.3).
- Display is a typed prefix plus the id (`unit_…`, `grp_…`, `wp_…`, `trg_…`, `mkr_…`, `mod_…`, `rule_…`, `node_…`, `edge_…`,
  `var_…`, `shot_…`, `line_…`); a wrong prefix is a parse error. Each id type follows `AGENTS.md`'s newtype rules and joins the
  `CODE-INDEX.md` table.
- **Campaign ids are 128-bit too.** Doc 19 §4.2 sketches `NodeId(u32)`; two branches of a shared campaign would collide on merge
  the same way as a unit counter (doc 45 OQ4). Proposal: `ElementId` everywhere (design-gap candidate, [README](README.md) §8 item 3).
- Ids are never reused. `Delete` reserves the id and list slot until the group leaves history (Fyrox's pool rule, doc 45 §2.3).

### 7.2 Re-matching after an external save

```rust
pub struct IdentityEntry { id: ElementRef, at: NodePath, fingerprint: Fingerprint /* class, side, group, position bucket, name */ }
pub enum Rematch { Exact, Confident { score: u8 }, Ambiguous(NonEmpty<ElementRef>), New }
```

- After the game's editor re-saves a mission, the sidecar's entries are re-matched by locator and fingerprint. `Ambiguous` matches
  are asked about, never guessed; unmatched items get fresh ids and an "identity re-assigned" diagnostic. Provenance of a re-matched
  element below `Exact` is downgraded to "reviewable". Thresholds are [U] (doc 45 OQ9) and are measured on the opt-in corpus before
  any match becomes automatic.
- A mission opened without a sidecar mints ids and says so (doc 37 G2 allows deleting the sidecar).
- Duplicate ids on load are a typed diagnostic with a repair offer.

### 7.3 Paste, rename and references

- **Paste** remaps references inside the pasted set (waypoint → group, syncs, trigger `idVehicle`, marker names used by triggers and
  scripts), keeps references that point outside it, suffixes clashing names and reports them. Cut-and-paste within one document keeps
  ids (doc 45 §2.3).
- **`VarName` is a renameable label, never identity.** A rename is checked against the target profile's commands, keywords and engine
  globals and rewrites every reference through Teller in one group ([validation-and-lints.md §9](validation-and-lints.md)).
- A **reverse-reference index** (in `plotroom-project`, extended by Teller into scripts, briefings and stringtables) powers "what
  depends on this", safe delete ("N references will break") and rename. A dangling reference stays in the file byte for byte and
  becomes a diagnostic with fixes (retarget, remove, restore); only derived caches are rebuilt silently.
- **Transient entities** (Wilco ghosts, drag previews, paste and template placement previews) are a separate `PreviewEntity` type the
  serializer does not accept (doc 45 §2.3).

## 8. Provenance, ownership and generated regions

### 8.1 Three types, three meanings

| Type | Meaning | Where |
| --- | --- | --- |
| `ConfigOrigin` | Source form of a config file: text or raP | `plotroom-config` |
| `Origin` | Who committed an undo group | `plotroom-doc` |
| `Provenance` | Where an element or value came from | `plotroom-doc`, persisted in the sidecar |

This splits the three `Origin` types of docs 04, 21/22/38 and 26 (doc 45 OQ2; design-gap candidate).

```rust
pub enum Origin { User { gesture: GestureId }, Wilco { turn: TurnId, setup: ModelSetupId },
    Workflow { run: RunId, step: StepId, item: Option<ItemKey> }, Plugin { id: PluginId, version: Version, tool: ToolName },
    External { client: ClientId }, QuickFix(FixId), Migration(MigrationId), Import(ImportId) }
pub enum Source { Human, Deterministic { generator: GeneratorId, seed: Seed },
    Model { journal: JournalKey, setup: ModelSetupId, capsule: Digest }, ModelChosenByHuman { journal: JournalKey },
    ModelEditedByHuman { journal: JournalKey }, Template(TemplateRef), Lifted { recogniser: RecogniserId, confidence: u8 },
    Imported(ImportId), Derived { anchor: ElementRef } }
pub enum Pin { Unpinned, Pinned { by: GestureId } }                     // an enum, not a bool (AGENTS.md type safety)
pub struct Provenance { source: Source, pin: Pin, fields: BTreeMap<FieldKey, FieldSource>, overrides: BTreeSet<FieldPath> }
pub struct FieldSource { source: Source, pin: Pin }
```

- **Granularity (resolved here):** one record per element plus a **sparse** per-field map that holds only fields whose source differs
  from the element's (typically a human edit on a generated element, or a pinned value). Lens fields stay plain `Field<T>`; wrapping
  every lens field in `Tracked<T>` (doc 26) would cost memory and churn everywhere for information that is almost always uniform per
  element. The sidecar DTO may still serialise it as `Tracked<T>` rows.
- **Automatic human ownership.** A `User`-origin `SetField` on a generated or templated element records `FieldSource::Human` for that
  field. Admission refuses writes from any other origin to a human-owned or pinned field unless the proposal carries the user's
  `UserIntent` ([commands-undo-history.md §4.4](commands-undo-history.md)). "Partial regeneration never clobbers human work" is thus
  enforced once, in the core, not per workflow (`AGENTS.md`).
- **One merge.** `merge_regenerated(base, ours, theirs, provenance)` in `plotroom-doc` implements doc 25 §9.3's field-level three-way
  merge; every generator, workflow and plugin commit uses it.
- The inspector's value-source badge ("engine default", "from template Ambush-2", "picked by you from Wilco's menu", "written by
  model, turn 12") reads `ValueSource` plus provenance. Provenance points into the journal by `JournalKey`; DG017's retention keeps
  inspector records while the element exists.

### 8.2 Templates and linked sets

- Template instances store `overrides: BTreeSet<FieldPath>`; sync flows only into fields that are neither overridden nor
  human-owned. "Reset to template" and "Detach" are ordinary commands (doc 45 §3, Tiled).
- A linked set lives only in the sidecar; `mission.sqm` gets plain duplicates, so the mission runs without Plotroom (doc 37 G2).

### 8.3 Generated regions

```rust
pub struct OwnedRegion { id: RegionId, doc: DocumentId, anchor: RegionAnchor, hash: Digest, owner: ElementRef, state: RegionState }
pub enum RegionState { Clean, ParamEdited, Customized, Detached, Orphaned }     // doc 31 §8.3
```

- Compiler output (module and rule lowering, attribute prefixes, compiler-owned singletons, fenced `description.ext` classes,
  generated briefing sections) is tracked as owned regions with content hashes. **Emitted map entities** (triggers, waypoints,
  markers, logics) are real document entities with the same states (doc 31 §8.3 "Map edits count too").
- Regeneration replaces only `Clean` regions; `ParamEdited` flows back into the form; `Customized` offers a three-way merge or
  keep-and-detach; `Orphaned` (damaged fences) is treated as user code. Customized and pinned regions are never overwritten silently.
- **Show / Eject / Lift** (doc 31 §8.3, §8.2; I34-31): generated text is shown side by side with the form that produced it; Eject
  turns a module, rule or cutscene into plain content with provenance kept (undoable); Lift recognises hand-written patterns on import.
- Provenance markers per format (doc 31 §8.3), renamed per D002: `; plotroom:gen <hash>` in SQS, `//` fences in `description.ext` and
  preprocessed SQF, sidecar-only for `mission.sqm` fields. Generated files live under the mission's `plotroom\` folder with
  per-instance names; whether names follow later label renames is an open candidate in the DG index ("Generated file names").
- `Todo` elements keep a draft runnable in Preview; export refuses them (doc 45 §4.6).

When lowering runs, and what happens when it fails, is decided in [commands-undo-history.md §5](commands-undo-history.md).

## 9. Authoring models

These are typed values in their own crates (L3), with no store and no I/O. Their command enums and planners live next to them
([commands-undo-history.md §2](commands-undo-history.md)); their compilers live in L5 ([crate-map.md §8](crate-map.md)).

| Model | Crate | Content | Sources |
| --- | --- | --- | --- |
| Conditions (CXL) | `plotroom-cxl` | Lexer, parser, scope-typed checker (campaign, mission, workflow, lesson scopes), intervals, coverage, canonical printer, engine-faithful evaluator (f32, case-insensitive strings) | doc 19 §5; DG008 option A (proposal) |
| Modules | `plotroom-modules` | `ModuleDef` and instances; mission modules and campaign modules as one family (DG004 option C, proposal); variant groups, counter/any/switch logic nodes and fault isolation (failed module falls back to its default outcome) (I35-MOD2); AI-executability note per module and a default announce cue on reinforcements (I36-31); rule-override scenarios as typed module presets (I36-31) | doc 31 §4; doc 26 §5; DG004 |
| Rules and conversations | `plotroom-modules::rule`, `::conversation` | WHEN/IF/THEN rules with modes; conversations of `Line`, `Choice`, `Gather`, `Branch`, `Todo`; sentence templates with named, typed slots (doc 45 §4.2) | doc 31 §5; doc 45 §4 |
| Planning layer | `plotroom-sidecar::planning` | Zones, phases, named routes, notes: sidecar-only objects (I34-04; doc 34 ed01, ed06, ed08) | doc 34 |
| Cinematics | `plotroom-cine` | v1: the Cutscene-node recipe subset (doc 35 rc35, rc50 timing defaults, provisional until reconciled with doc 39 §9.3 through DG035; I35-CUT); the full timeline is v1.x | doc 32 §3; doc 39 |
| Campaign | `plotroom-campaign` | See below | doc 19 §4–§7 |

**The campaign document** (`CampaignDoc { model: Guarded<CampaignModel>, cst: Guarded<ConfigDoc> }`):

- Node kinds (mission, cutscene, decision, choice, hub, ending), per-node transition tables, declared state (Bool, bounded Int,
  Enum, Set, Text, Real), roster and pools; guards and effects in CXL (doc 19 §4–§5).
- Additions folded from later docs: `variant` nodes (state-gated presence inside one mission) and declared output contracts for
  sibling branches, an `Ignored` objective outcome distinct from `Failed` (I35-19); derived variables and counters,
  `VictoryCondition`/`DefeatCondition`, one template sentence per effect (I34-19); optional ending progress tracks; the Classic
  complexity tier complete and default for imported campaigns (I36-19; doc 19 §6.8).
- Node, edge and variable ids are `ElementId`s (§7.1). Layout is `Option<CanvasPos>`, `None` meaning automatic layout (doc 45 OQ8;
  design-gap candidate).
- A canonical sorted text form in the sidecar keeps ids across export and import (doc 45 §2.7).
- Import has Preserve mode first (an unedited re-save is byte-identical) and opt-in Adopt per node (doc 19 §7.6).
- Campaign modules (persistence and, in v1.x, strategic: roster, loadout, ops board, doom clock; doc 26 §9, doc 29 §3) attach
  declared state and effects; the strategic tier is the first milestone after v1 (owner, OWQ-13 (a); I35-29, I34-29, I36-29
  deferred).
- Rolls declare a scope `RollScope { Build, PerCampaign, PerTurn, PerAttempt }` (doc 43 §2.2); build seeds are generator inputs,
  never ambient randomness.

## 10. The sidecar (`.plotroom/`)

The shared sidecar is a **dot-directory** inside each mission or campaign folder. CWR's exporter skips dot-directories (doc 04 §9
[V]); whether the 1.99 exporter does is [U] and needs a probe (doc 45 OQ1). Plotroom's own export always excludes it. The name
replaces the research working names (`ofp-editor.meta.toml`, `.ofpeditor/`) per D002 item 4.

```text
<name>.<Island>/                      engine files only (mission.sqm, description.ext, scripts, briefing, stringtable)
  plotroom/                           generated scripts, fenced with `; plotroom:gen <hash>`
  .plotroom/
    project.toml                      format_version, target profile, opted-in capabilities, realism setting, mod-set reference
    identity.toml                     id → locator + fingerprint (§7.2)
    provenance.toml                   element provenance, field sources, pins (§8.1)
    regions.toml                      owned regions and hashes (§8.3)
    templates.toml                    template instances, overrides, linked sets (§8.2)
    acks.toml                         acknowledgements and suppressions (validation-and-lints.md §7)
    planning.toml                     zones, phases, named routes, notes
    authoring/                        typed sources of modules, rules, conversations, sequences
    modules.lock                      vendored, content-hashed ModuleDefs with licence (extensibility.md §3.4)
    modset.toml                       the mission's mod-set lock, its only copy (doc 27 §4.2; game-integration.md §3)
    campaign.toml, bible.toml         campaign folders: canonical campaign model; story bible (doc 25 §8)
    log.jsonl                         append-only project log (versions, profile and mod-set changes, migrations, runs, commit ids)
    journal/<run>.jsonl               workflow decision journal (DG017 option A, proposal; agent-runtime.md §5)
```

- **Persisted types are versioned DTOs** in `plotroom-sidecar::dto::vN`, separate from in-memory types, so an internal refactor
  cannot silently change an on-disk format, and every `migrate_vN_to_vN1` has a stable source type.
- Shared files are canonical: `BTreeMap` order, no timestamps or auto-layout coordinates outside `log.jsonl`, so diffs stay small.
- Unknown records, and modules or rules whose definition is missing, load as `Opaque { def_key, version, raw }`: they keep their
  bytes, show "needs pack X vN", block export and write back unchanged (doc 45 §2.7).

| Tier | Holds | Travels |
| --- | --- | --- |
| Mission folder | Engine data and fenced generated scripts | Yes, and in exports |
| `.plotroom/` | Everything above | With the folder and the "Share project" bundle; never in our export; AI history and replay records only by opt-in (DG017; doc 43 §3.4) |
| App data (per user) | Camera, folds, dock layout, recents, "seen" set, crash op journal, Wilco session logs, model store, plugin grants; secrets in the OS keyring | Never |

## 11. Persistence

- **Save.** Before a save, any pending proposal is resolved (accepted as one group or discarded), so a save with a pending proposal
  writes the pre-proposal bytes. The I/O service serialises from an `Arc<Snapshot>` at revision *r*, writes to a temporary file,
  re-parses and asserts lens equality, keeps a `.bak`, renames atomically, and reports `Saved { doc, rev: r }`; the logic step then
  sets `saved[doc] = r`, so dirty state stays right even if the user kept editing (doc 04 §12.3(10); doc 45 §2.7).
- **External change.** Before every save the on-disk hash is compared with the hash recorded at open; a mismatch offers reload,
  overwrite, or save-a-copy-and-diff (doc 45 §2.7, OpenRA). A file watcher surfaces changes early.
- **Crash op journal** (app data): the base file hash plus committed op batches, appended per group and flushed on group close and
  idle. On reopen after a crash it verifies the base hash and offers replay, or a diff if the file changed meanwhile.
- **Migrations.** Every Plotroom format carries `format_version` from the first release; each bump adds a typed
  `migrate_vN_to_vN1` with golden synthetic fixtures. Migrations dry-run by default, apply as one undo group and are recorded in the
  project log. `mission.sqm` is never migrated.
- **Repairs.** Load-time anomalies become `RepairNote`s, applied as ordinary commands only when accepted (doc 45 §2.7).
- The save path, the crash journal and the workflow journal commit ids connect as described in
  [agent-runtime.md §5](agent-runtime.md) (durability order).

## 12. Round-trip guarantees

| # | Guarantee | Evidence ([testing-strategy.md](testing-strategy.md)) |
| --- | --- | --- |
| R1 | An unchanged text document saves byte-identical | Property test `render(parse(b)) == b`; opt-in corpus run |
| R2 | An edit changes bytes only inside the patched spans | `verify_round_trip_each_commit`, always on in tests and CI |
| R3 | Unknown keys, comments, directives, duplicates and raw lexemes survive any edit | Golden fixtures (doc 04 §13) |
| R4 | Undo of all ops gives a byte-identical CST and sidecar; redo of all gives the pre-undo state | Random op-sequence property tests |
| R5 | The incrementally maintained lens equals the re-derived lens | `validate_invariants()` after every harness step |
| R6 | Ids survive load → save → load; a simulated engine re-save re-matches | Identity tests |
| R7 | The mission runs with `.plotroom/` deleted | Export and staging tests; probe |
| R8 | A Preserve-mode campaign import re-saves byte-identical | Campaign import tests (doc 19 §7.6) |
| R9 | No view state (selection, camera, folds) ever reaches a saved file | Serialisation tests; `PreviewEntity` has no serializer |
| R10 | raP opens read-only; conversion is explicit | Command tests |

## 13. Open questions

1. Does the 1.99 exporter skip dot-directories (doc 45 OQ1)? Probe in the first Preview spike; until then Plotroom's own export is
   the recommended path for `Cwa199` missions with a sidecar.
2. Re-match fingerprint fields and confidence thresholds (doc 45 OQ9) [U]; measured on the opt-in corpus.
3. Float formatting parity of each writer profile with the engine's C formatting [U].
4. Green-tree crate or in-house CST; persistent map crate; the measured commit cost (doc 45 OQ5).
5. Whether generated file names follow label renames or freeze at first export (DG index candidate).
6. Journal retention numbers and the replay-record export rule (DG017; doc 43 §3.4).
7. The exact voice-language sibling-file rule and per-language staleness fields of the stringtable lens (I34-04; doc 33 §7).
8. Whether provenance of re-matched elements below `Exact` should also mark their journal records stale.

## Verification notes

### Owner answers folded (2026-09-27)

- §9 now states OWQ-13 (a) (the strategic tier is the first milestone after v1), from `OWNER-QUESTIONS.md` as answered on 2026-09-27.
  Nothing else in this file depended on an owner question.
