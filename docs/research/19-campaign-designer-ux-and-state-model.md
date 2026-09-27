# Campaign Designer: UX, Typed State Model, Condition Language and Vanilla Compiler

Research doc 19 for `ofp-editor`. Audience: contributors and LLM coding agents. This file is meant to be read on its own.
Question answered: how should our editor let designers build **campaigns, including RPG-like ones**? That covers global campaign state,
mission state that feeds back into it, and complex mission trees whose transitions depend on both. It must be intuitive and keep the
retro OFP look, and the output must still run on original CWA 1.99.

**Epistemic legend.** **[V]** = verified by reading source at a pinned commit or a fetched page (citation given). **[I]** = inferred, not run.
**[U]** = unknown, needs a test. **[W]** = web/community documentation (URL given; "search" = only a search-result extract was available).
**Engine source of truth:** `docs/research/18-campaign-system-in-engine.md` ("doc 18"); facts cited "doc 18 §n" were verified there by a fact-checker.
**Code-citation shorthands** (pinned): `CWR:` = `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/`,
`EVAL:` = `BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/`, `IC:` = `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/`.
**Glossary.** *SQS* = line-based OFP script (`? cond : stmt`, `#label`, `goto`). *End code* = one of the 7 routable mission endings (`lost`,
`end1`..`end6`). *Socket* = a generated condition-only END/LOOSE trigger that fires when global `cmpEnd` equals its number. *Router* = a
zero-gameplay mission that only decides the next node. *Book* = the in-game campaign history list. *Commit* = `saveVar` of every persistent
variable at mission end.

## TL;DR

- **Recommendation: the editor owns a typed `CampaignModel` (graph + declared state) and compiles it to vanilla 1.99 content; the engine is only the
  executor.** This mirrors DCS Liberation (an external program owns the persistent war and generates each mission), adapted to an engine whose
  state lives in its own `.sqc` (§2.2, doc 18).
- **State schema (§4):** only declared variables persist. Types are `Bool`, bounded `Int` (|x| ≤ 2^24 because engine scalars are `f32`), `Enum`,
  `Set<Enum>`, `Text` and `Real`, in two scopes (campaign, mission) plus typed **outcome payloads**, a typed **roster** with a per-character status
  ladder, and typed **pools**. Fixed-shape records use flat scalar `saveVar`s, which sidesteps array aliasing.
- **Condition language (§5):** a small, pure, statically typed expression DSL ("CXL"), with a **visual condition builder as a second view of the same
  AST**. Not raw SQF/SQS: the engine's `==` has **no boolean overload** (CWR has a separate `boolEq`/`boolNe`; 1.99 unverified), **case-insensitive
  string `==`**, `f32` scalars, and `?` lines that split at the first `:` **[V]**. Raw SQS survives only as a lint-gated escape hatch.
- **Graph semantics (§5.5, §6.1):** node kinds `Mission`, `Cutscene`, `Decision` (automatic), `Choice` (player picks), `Hub`, `Ending`; acts are
  cosmetic groups. Edge = trigger (outcome / choice / auto) + ordered guard + effects + target. First match wins, guards see pre-effect state, and
  every (node, trigger) must be provably covered.
- **UX (§6):** an OFP-styled **Flow view** plus a **Theatre view** (nodes on the island map); per-node **transition tables**; a Variables panel with
  "set in / read in" cross-references; a **7-socket budget meter**; a campaign-book-styled **what-if Playthrough**; an exhaustive **Path Explorer**;
  coverage heat; lints; Simple → Advanced tiers.
- **Compiler (§7):** allocates sockets per node over distinct (debrief narrative, successor) pairs and inserts routers only above 7. The
  socket/finisher design is BI's own ending idiom (doc 35 §3.3) **[V]**. Routing defaults follow BI's campaigns (§7.2): `lost` retries the mission,
  story-moving failures take END sockets with their own debriefs, cutscene nodes map every code forward, and a chapter's last mission uses the
  chapter fallback **[I]**. Finer debrief variation goes into `OBJ_` lines, which the debriefing's objectives pane also evaluates **[V CWR]**.
  Routers on one island share one folder and dispatch on a `cmp_route` token. The finisher runs select rule → effects → commit → **publish `cmpEnd`
  last**, because `exec`'d SQS runs at most **100 lines per step** **[V]**.
- **Vanilla expressibility (§7.4):** yes for arbitrary guards over campaign and mission state, merges, loops, hubs, side missions, failure branches
  (while the player is alive), persistent squads, pools, and state-aware briefings (hidden `OBJ_` sections **[V]**, intro variants, hints). No for
  routing on player death, invisible routers (every router is a book row), state-dependent chapter cutscenes/outros, more than 7 end-code debrief
  narratives per mission (objective lines can vary further), and MP campaigns. CWR-CE extensions E1/E3/E5/E6 (doc 18 §9) add polish, not expressiveness.
- **Round-trip (§7.6):** existing campaigns import losslessly; **Preserve** mode edits only the end-code map and an unedited re-save is
  byte-identical; **Adopt** is opt-in per node; discovered `saveVar` names become `Opaque` variables; **retrofit routers** add state-based branching
  without touching hand-written missions.
- **AI harness (§8):** typed, undoable campaign actions only (never glue code); branches arrive as ChangeSets; text variants are generated per state
  bundle with a coverage check; continuity checks are driven by simulator facts.
- **Blocker before freezing the lowering:** a 1.99 probe-mission suite covering `in`, `count`, `call`, `addAction`, hiding a radio item, `objStatus`
  before the briefing, `loadIdentity` in unit init, and trigger/script ordering (Open question 1).

## 1. Engine facts this design depends on

Relied on from doc 18 (re-read where cited): the 7-code static lookup `NextMission` (`CWR:UI/OptionsUI.cpp#L1894-L2022`) **[V]**; `END<n>` fires
only when every `END<n>` trigger is active, with LOOSE first (`CWR:World/WorldImpl.cpp#L541-L657`) **[V]**; `saveVar` lower-cases the name and
upserts the **current global value** (`CWR:Game/Commands/GameStateExtGrp.cpp#L412-L425`, `CWR:AI/AICenterStats.cpp#L69-L80`) **[V]**; re-injection
before unit creation, unit inits and `init.sqs` (`CWR:UI/OptionsUIApp.cpp#L883-L895` runs the `VarSet` loop before `InitVehicles`) **[V]**; per-row
snapshots taken **after** `init.sqs` and the briefing; array aliasing; no `isNil`; death is unroutable. The campaign classes hold no guards, but
`NextMission` has one global exit: if the top-level `exitScore` exists and the finished mission lacks `noAward`, a campaign score ≤ `exitScore`
ends the campaign (`CWR:UI/OptionsUI.cpp#L1905-L1923`) **[V]**. The compiler must treat `exitScore` as an implicit campaign end (C10).

New facts verified for this doc:

| # | Fact | Evidence | Design consequence |
| --- | --- | --- | --- |
| F1 | Core binary operators: arithmetic, `==`/`!=` on **scalars and strings**, `&&`/`and`, `or` (plus its double-pipe alias), `select`, `set`, `count`, `in`, `+`/`-` on arrays. The game layer adds `==`/`!=` for objects, groups and sides only. There is **no `==` for booleans**; CWR instead registers `boolEq`/`boolNe` (its source comment says `==` is "improper" for bools) | **[V]** `EVAL:express.cpp#L1100-L1150`; `CWR:Game/Commands/GameStateExt.cpp#L1279-L1288` | The `Cwa199` lowering of `a == b` on booleans is `((a) and (b)) or (!(a) and !(b))`; `boolEq` only after a 1.99 probe **[U]** |
| F2 | Scalar comparison casts to `float` | **[V]** `EVAL:express.cpp#L405-L408` | `Int` range limited to ±2^24 for exactness |
| F3 | String `==` is `strcmpi` (case-insensitive) | **[V]** `EVAL:express.cpp#L435-L438` | Enums lower to ordinals, not strings; lint on `Text` equality |
| F4 | `in` compares elements with `IsEqualTo` | **[V]** `EVAL:express.cpp#L1067-L1079` | `Set<Enum>` = array of ordinals + `in`. Presence in 1.99 is **[U]** |
| F5 | CWR also registers `find`, `for`, `exitWith`, `resize` and `parseSimpleArray` | **[V]** `EVAL:express.cpp#L1131-L1147`, `#L1191-L1195` | Probably post-1.99. The lowering must not use them until the probe proves otherwise **[U]** |
| F6 | SQS `?` lines split at the **first `:`** (`strchr`) | **[V]** `CWR:Game/Scripting/Scripts.cpp#L292-L318` | No `:` inside a lowered guard (text literals are restricted) |
| F7 | Script lines are read into a 4096-byte buffer | **[V]** `CWR:Game/Scripting/Scripts.cpp#L165-L172` | Lowered lines must stay under 4 KB, because `ReadLine` silently truncates at 4095 bytes (`Scripts.cpp#L97-L123`) |
| F8 | `exec`'d scripts run **≤ 100 lines per simulation step** (default `maxLines = -1` → 100). `init.sqs`, `exit.sqs` and `initintro.sqs` run with `INT_MAX` | **[V]** `CWR:Game/Scripting/Scripts.hpp#L53`, `Scripts.cpp#L441-L478`, `#L577`; `CWR:UI/DisplayUI.cpp#L126`; `CWR:UI/DisplayUIMenus.cpp#L991-L993`, `#L1325` | A finisher may span frames, so publish `cmpEnd` in the **last** line. The 100 counts every stored line, including `?` lines whose condition is false (`~` stores two); comments and labels are not stored. A straight-line `exit.sqs` completes in its single call, which resolves doc 18 open question 5 for CWR **[V by reading]**. *Corrected:* an `exec` from `exit.sqs` is appended to the list that `SimulateScripts` is still iterating (`CWR:World/WorldSetup.cpp#L1378-L1407`), so it runs its first ≤ 100 lines up to its first wait, and nothing after that. Other live scripts also get one extra step **[V by reading]**. Keep the fallback commit inline |
| F9 | Briefing objectives: each `OBJ_*` section name is **evaluated as a variable**, and hidden (`OSHidden`) sections are skipped. `objStatus` sets `OBJ_<id>` and re-runs `UpdatePlan` if the map exists | **[V]** `CWR:UI/Map/UIMapDisplayBriefing.cpp#L427-L474`, `#L311-L316`; `CWR:Game/Commands/GameStateExtUi.cpp#L1825-L1859` | Vanilla state-aware briefing: variant lines as `OBJ_` sections, hidden by generated init code. They render as **objective entries** (status icon plus indent), not as free prose **[V]** |
| F10 | Debriefing narrative is selected by end code (`Debriefing:Loser`, `Debriefing:End1..6`). The debriefing's objectives pane re-evaluates the `OBJ_*` sections of `briefing.html` and skips hidden ones | **[V]** `CWR:UI/Map/UIMapDialogs.cpp#L1062-L1145`, `#L910-L912` | At most 7 debrief **narratives** per mission, and this drives socket allocation. Further state-dependent debrief lines can be `OBJ_` entries that stay hidden during play and are revealed by the finisher |
| F11 | Radio trigger channels `ALPHA`..`JULIET` (10), and `setRadioMsg` exists. The radio menu lists channel triggers **only when the player is group leader**, drops activated non-repeating triggers, and hides an item whose text is `null` (case-insensitive) | **[V]** `CWR:AI/ArcadeTemplate.cpp#L159-L168`; `CWR:Game/Commands/GameStateExt.cpp#L1278`; `CWR:Game/Commands/GameStateExtUi.cpp#L2213-L2268`; `CWR:UI/InGame/InGameUIMenu.cpp#L628-L683` | Choice and Hub nodes can offer ≤10 radio choices; the player must lead their group; `setRadioMsg "NULL"` hides options in CWR (1.99 **[U]**) |
| F12 | `presenceCondition` is evaluated at mission load when empty vehicles are created and when **non-playable** units are created; playable/player units skip it. Campaign vars are injected before `InitVehicles` | **[V]** `CWR:AI/AICenterImpl.cpp#L1403-L1410`, `#L1528-L1538`; `CWR:UI/OptionsUIApp.cpp#L883-L895` | Persistent squad members are pre-placed, **non-playable** units with generated presence conditions that can read campaign vars (on 1.99 **[U]**) |
| F13 | No `setRank`/`rank` script command is registered (grep of the command tables). `createUnit` accepts an optional 5th element, a rank name | **[V absence]** `CWR:Game/Commands/GameStateExt.cpp`; **[V]** `CWR:Game/Commands/GameStateExtWorld.cpp#L237-L310` | Rank persists through `saveIdentity`/`loadIdentity` (doc 18 §6.3), static `mission.sqm` ranks, or a rank var fed to `createUnit` for script-spawned squadmates (5-element form on 1.99 **[U]**) |
| F14 | Registered and useful: `format`, `hint`, `titleText`, `createDialog`, `addAction`/`removeAction`, `setDammage`, `getDammage`, `alive`, `addRating`, `setSkill`, `createUnit`, `deleteVehicle`, `saveStatus`/`loadStatus`, `saveIdentity`/`loadIdentity`, `exit`, `goto` | **[V]** `CWR:Game/Commands/GameStateExt.cpp#L882`, `#L935`, `#L945`, `#L1006`, `#L1026`, `#L1047`, `#L1051`, `#L1058`, `#L1078`, `#L1233`, `#L1241`, `#L1336`, `#L1363-L1364`, `#L1374-L1378`, `#L1383` | Presence of each in 1.99 is **[U]** until probed; `addAction` and `createDialog` are the riskiest |

## 2. Prior art

### 2.1 Narrative and quest tools

| Tool | State model | Conditions / effects | Lesson for us |
| --- | --- | --- | --- |
| **articy:draft** | Global variable **sets** (bool/int/string), addressed as `<variable-set>.<variable-name>` | Condition pins/nodes versus instruction pins/nodes; C-like "expresso" (`Inventory.key == true` / `Inventory.key = true;`); errors are underlined in red | Keep conditions and effects in **separate slots**. Namespaced vars. **Simulation mode** checks each condition "automatically" along a saved **journey**, with Analysis vs Player mode **[W]** |
| **Twine** (Harlowe/SugarCube) | `$story` vars are "globally accessible to all functionality everywhere"; `_temp` vars are passage-local | Macros | Undeclared global mutation does not scale. We require declarations **[W]** |
| **ink** | `VAR` (the initial value fixes the type), `CONST`, `LIST` = multi-valued set/state machine; knots carry implicit read counts | Inline conditional text in braces, with pipe-separated alternatives | Visit counts are free, useful state → `visited()`. Sets → `Set<Enum>` **[W]** |
| **Yarn Spinner** | `<<declare>>` with a default; "variables … can never change their type"; enums; **smart variables** (`<<declare $is_powerful = $strength > 50 && …>>`) computed on read | `<<if>>`, `<<set>>` | Static typing works for writers. Smart vars → our `Derived` variables **[W]** |
| **Arcweave** | Declared global variables | **Branch** items: `if` / `elseif` / `else`, each with its own output connection, evaluated top to bottom; `visits()` | This is exactly our ordered per-node transition table **[W]** |
| **Chat Mapper** | Lua tables | "Conditions are defined … typing a logical Lua expression"; scripts run when a node plays | A raw scripting language is powerful but unverifiable. We reject it as the primary surface **[W]** |
| **Unreal StateTree** | Hierarchical states, evaluators, parameters | Enter Conditions; transitions with trigger conditions, "evaluated starting from the leaf State and progressing upwards" | Node entry guards, and a clear evaluation order **[W]** |
| **RPG Maker MZ** | Switches, variables, self-switches | Page conditions: one of each type; the variable test is a fixed threshold; "the event with the highest ID value will be used" | A too-narrow condition UI spawned a plugin ecosystem. Ours must be compositional **[W]** |
| **Creation Kit** (Skyrim) | Quest **stages** (indices) | `GetStageDone MS01 30` is true once that stage has ever been set (per the wiki extract); stages carry conditioned journal entries | Stages ≈ our per-node `visited`/`last outcome` facts plus a journal **[W search]** |
| **BioWare Aurora** (NWN) | Journal categories with entry IDs; by default entry numbers must increase | "Text Appears When" `StartingConditional` scripts; the first starting node that is TRUE wins | First-match-wins ordering, and a monotonic journal **[W search]** |

### 2.2 Military and strategy campaign layers

| Game | Structure | Lesson |
| --- | --- | --- |
| **Arma 3 official campaign** | **Hub** missions (`isHub = 1`, `repeat = 1`); story missions (`isHubMission = 1`) return via `endDefault = A_hub01`; custom ending names **[W]** | Hub-and-spoke works for BI campaigns. These keys **do not exist** in the CWA engine (doc 18 §2), so we compile hubs to plain missions plus routers |
| **DCS Liberation / Retribution** | An "external program that generates full and complex DCS missions and manage a persistent combat environment". After a sortie a result window appears, you "Accept results", and `state.json` is read back. Squadrons have named pilots who can die, go on leave and gain skill **[W]** | Our architecture: the editor owns the model, the engine executes it. Difference: our results never leave the engine (the `.sqc` table is the store), so "accept results" becomes the in-mission **commit** |
| **XCOM 2** | The Avenger base between missions; permadeath and promotions; the Avatar Program "if completed is an automatic loss"; the Geoscape picks missions **[W]** | Hub + roster ladder + **doom-clock** counters |
| **BattleTech** | *Flashpoint*: self-contained chains in which "decisions must be made that will change the progress", plus "consecutive deployments" without repair **[W]** | Mini-campaign chains. "No repair between missions" is a carry-over rule |
| **Jagged Alliance 2** | Sector map; mercs level up; morale; "Mercenaries who dislike each other … one of the two mercenaries will quit" **[W]** | Relationships = bounded ints with threshold events |
| **Mount & Blade** | Renown from battles; offers of vassalage at high renown **[W]** | Reputation counters whose thresholds unlock nodes |
| **OFP community** | *OfpCmaker* ("Full campaign editor for Operation Flashpoint", Mikero) and *Campedit* (Amalfi) existed **[W]**; the Resistance roster/pool patterns are in doc 18 §10 | We have no published details of their models. Treat them as UX precedent only |

### 2.3 Concepts extracted from the Iron Curtain design docs (the owner's own specs)

| IC concept | Citation | Adopt as |
| --- | --- | --- |
| Graph, not list; named outcomes; failure is an edge; continuous flow | `IC:decisions/09d/D021-branching-campaigns.md#L26-L34`, `IC:modding/campaigns.md#L9-L15` | Core graph semantics (§6) |
| Designer-controlled carry-over; "Automatic state carryover" rejected | `IC:decisions/09d/D021-branching-campaigns.md#L97-L104` | Only declared vars persist (§4) |
| Outcome `state_effects`; entry `conditions: require_flag` | `IC:modding/campaigns.md#L94-L167` | Edge effects; optional node entry guard |
| Edge = from outcome + condition + weight + roster filter; conditions evaluated before weights; mission pools | `IC:decisions/09f/D038/D038-campaign-editor.md#L48-L94` | Transition table; `roll` only in Decision nodes (§5.3) |
| `decision` choices with `requires_hero` and `unchosen_effects` | `IC:modding/campaigns.md#L619-L651` | `Choice` node with availability guards and unchosen effects |
| Persistent State Dashboard: every flag's "Set in / Read in"; scope conflict highlighting | `IC:decisions/09f/D038/D038-campaign-editor.md#L156-L190` | Variables panel cross-references and the C08 lint |
| Named characters (stable id, must-survive, death outcome); campaign inventory | `IC:decisions/09f/D038/D038-campaign-editor.md#L279-L330` | `CharacterDecl`, pools |
| Hero status ladder `ready → fatigued → wounded → captured → lost`; "no arcade lives" | `IC:modding/campaigns.md#L2012-L2039` | `CharacterStatus` enum |
| Bounded pending rescue with escalating compromise | `IC:modding/enhanced-campaign-plan.md#L323-L405` | Countdown `Int` vars decremented at commit; expiry lints |
| Expiring opportunities; mandatory `On Success / On Failure / If Skipped / Time Window` disclosures | `IC:modding/enhanced-campaign-plan.md#L59-L103` | Hub "operation cards" (§6.1) |
| Critical missions must be explicit and badged | `IC:modding/campaigns.md#L193-L219` | Lint C10: no implicit campaign end |
| Validation in three layers: graph, **state coverage**, presentation; validate by "asset bundle" instead of every flag permutation | `IC:modding/campaigns.md#L234-L262` | Lints + Path Explorer with abstract domains (§6.4) |
| Structured-state rule: do not bury canonical state in ad-hoc flags | `IC:modding/campaigns.md#L2842` | Typed roster and pools instead of stringly flags |
| Campaign journal from state diffs | `IC:modding/enhanced-campaign-plan.md#L1830-L1850` | Simulator journal; optional in-game hint log |
| Test tools: jump to mission with simulated state, path coverage colours, state inspector | `IC:decisions/09f/D038/D038-campaign-editor.md#L452-L462` | Debug campaign generator, coverage heat (§6.4) |
| Variables Panel (Switch/Counter/Timer/Text); Condition of Presence | `IC:decisions/09f/D038/D038-core-architecture.md#L133-L137`, `#L223-L241` | Mission-scope vars; `presenceCondition` in the CXL |
| Simple vs Advanced mode; hero features hidden in Simple mode | `IC:decisions/09f/D038/D038-campaign-editor.md#L445-L448` | Complexity tiers (§6.8) |
| Generated campaigns must converge and stay replayable without an LLM; LLM output is untrusted | `IC:decisions/09f/D016/D016-branching-world-campaigns.md#L71-L77`, `IC:modding/campaigns.md#L3124` | AI harness guardrails (§8) |

## 3. Design principles

1. **One model, one semantics, two executors.** The editor's simulator and the compiled SQS must agree bit for bit (with `f32` scalars and
   case-insensitive text). The lowering is property-tested against the interpreter (§9).
2. **Declared, typed, namespaced state only.** Nothing persists unless declared. Designers never type `cmp_` names.
3. **Designers think in outcomes, not end codes.** End codes, sockets, routers and chapters are compiler output, visible only in a "Compiled" overlay.
4. **Totality.** Every (node, trigger, reachable state) has exactly one successor, proven statically. No path may fall into the engine's
   "empty key ends the campaign" behaviour by accident (doc 18 §4).
5. **Vanilla first.** The `Cwa199` target is the default; CWR/CE features are opt-in target profiles.
6. **Lossless coexistence** with hand-written campaigns (Preserve/Adopt, §7.6).

## 4. Typed campaign-state schema

### 4.1 Concepts

| Concept | Scope / lifetime | Written by | Read by |
| --- | --- | --- | --- |
| Campaign variable | Whole campaign; **persistent** (committed by `saveVar`) | Edge effects, in-mission "Set campaign var" actions (buffered until commit) | Guards, in-mission conditions, presence conditions, text variants |
| Mission variable | One node; **transient** (plain global, never saved) | Mission triggers/scripts | That node's outgoing guards/effects and its own content |
| Outcome payload | One outcome of one node; a typed record | Bound to mission vars or probes when the outcome is raised | Effects/guards on edges triggered by that outcome |
| Derived variable | Macro (Yarn "smart variable"); never stored | — | Anywhere; inlined at lowering |
| Roster | Characters with status/rank/damage/custom fields | Commit (auto from unit facts) + effects | Guards, presence conditions, identity loading |
| Pools | Native weapon/magazine pool; vehicle pool; item counters | Commit + effects | Briefing gear (native), guards |
| Built-in facts | `visited(N)`, `visits(N)`, `last(N)` (last outcome of N) | Generated bookkeeping at commit | Guards |

### 4.2 Rust type sketches (crate `ofp-campaign-model`; proposal-only)

```rust
// ── Identifiers ─────────────────────────────────────────────────────────
// Every newtype derives Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash,
// has #[inline] from_raw/to_raw, and Display ("node#12", "var#3", ...).
pub struct NodeId(u32);      pub struct EdgeId(u32);     pub struct VarId(u32);
pub struct OutcomeId(u32);   pub struct CharacterId(u32); pub struct EnumTypeId(u32);
pub struct ActId(u32);       pub struct ChoiceId(u32);   pub struct ItemId(u32);
/// 1..=6. Validated: `EndIndex::new(n) -> Option<Self>`; there is no public from_raw.
pub struct EndIndex(u8);

/// Engine-routable ending. Keys of the `Campaign` classes (doc 18 §2).
pub enum EndCode { Lost, End(EndIndex) }
/// Importer view of a key/token read from files: permissive by design.
pub enum ParsedEndKey { Known(EndCode), Other(RawToken) }

// ── Model root (fields private; mutated only through validated commands) ─
pub struct CampaignModel {
    meta: CampaignMeta, target: TargetProfile,
    types: TypeTable,                 // enum declarations (cases have stable ordinals)
    vars: VarTable,                   // all VarDecl, indexed by VarId and by name
    roster: RosterSchema, pools: PoolSchema,
    nodes: BTreeMap<NodeId, Node>, edges: BTreeMap<EdgeId, Transition>, acts: Vec<Act>, start: NodeId,
    engine_extras: EngineExtras,      // Awards/Penalties/exitScore, kept verbatim (CST)
    provenance: Provenance,           // Authored | Imported { mode, source_digest }
}
pub enum TargetProfile { Cwa199, Cwr, CwrCe { extensions: CeExtensionSet }, Other(RawToken) }

// ── Variables ───────────────────────────────────────────────────────────
pub struct VarDecl {
    id: VarId,
    name: Ident,                       // [a-z][a-z0-9_]{0,23}, unique ignoring case
    engine_name: EngineVarName,        // "cmp_" + short form; unique after lower-casing (saveVar lower-cases)
    ty: ValueType, default: Value,     // default is type-checked against `ty` at construction
    scope: VarScope, lifetime: Lifetime, doc: String,
}
pub enum VarScope { Campaign, Mission { node: NodeId } }
pub enum Lifetime { Persistent, Transient, Derived(Expr) }
pub enum ValueType {
    Bool,
    Int(IntRange),                     // invariant: min <= max, |min|,|max| <= 16_777_216 (f32-exact)
    Real(RealRange),                   // allowed; `==` on Real is a lint error
    Enum(EnumTypeId),                  // lowered to scalar ordinals (not strings: engine == is strcmpi)
    Set(EnumTypeId),                   // lowered to an array of ordinals; <= 64 cases
    Text(TextLimit),                   // byte cap; literals restricted (no ':' or '"')
    Opaque(ObservedShape),             // imported saveVar of unknown type: display-only, not usable in guards
}
pub enum Value { Bool(bool), Int(i32), Real(f32), Enum(EnumTypeId, u16), Set(EnumTypeId, u64), Text(String) }

// ── Roster ──────────────────────────────────────────────────────────────
pub struct CharacterDecl {
    id: CharacterId, key: IdentityStem, // key: objects.sav key stem, [a-z0-9_]
    display: LocalizedText,
    unit_class: ClassName,             // CfgVehicles class used when placing the slot
    identity_class: Option<ClassName>, // CfgIdentities class for setIdentity
    role: RosterRole, start: CharacterState,
    fields: Vec<FieldDecl>,            // custom typed fields: loyalty, relation, ...
}
/// The player cannot have a death policy: player death is EMKilled, the Retry dialog (doc 18 §5).
pub enum RosterRole { PlayerCharacter, Squadmate { death: DeathPolicy }, Npc { death: DeathPolicy } }
pub enum DeathPolicy { Permadeath, WoundedInstead { missions_out: NonZeroU8 }, MustSurvive { on_death: OutcomeId } }
/// Engine ordinals follow declaration order: Available=0, Fatigued=1, Wounded=2, Captured=3,
/// Missing=4, Dead=5, Dismissed=6. The data fields go in separate scalars (`cmp_r_<c>_out`).
pub enum CharacterStatus {
    Available, Fatigued, Wounded { missions_out: u8 }, Captured { missions_since: u8 },
    Missing, Dead, Dismissed,
}
pub struct CharacterState { status: CharacterStatus, damage: Damage01, rank: Rank, xp: i32 }
pub enum Rank { Private, Corporal, Sergeant, Lieutenant, Captain, Major, Colonel, Other(RawToken) }

// ── Pools ───────────────────────────────────────────────────────────────
pub struct PoolSchema {
    native_pool: Option<NativePoolDecl>,     // weapons/magazines; implies top-level weaponPool = 1
    vehicle_pool: Option<VehiclePoolDecl>,   // [class, count] rows committed via saveVar
    items: Vec<ItemDecl>,                    // counters: intel documents, keycards, supplies
}

// ── Graph ───────────────────────────────────────────────────────────────
pub struct Node { id: NodeId, name: Ident, act: Option<ActId>, kind: NodeKind, layout: CanvasPos, notes: String }
pub enum NodeKind {
    Mission(MissionNode),     // playable
    Cutscene(CutsceneNode),   // no groups, so it always ends `lost` (doc 18 §5); every code is mapped forward (§7.2)
    Decision(DecisionNode),   // automatic; compiles to a router
    Choice(ChoiceNode),       // player chooses; compiles to a tiny choice mission
    Hub(HubNode),             // repeatable base camp with spokes and return edges
    Ending(EndingNode),       // terminal; optional final cutscene; `kind: Victory|Defeat|Neutral`
}
pub struct MissionNode {
    mission: MissionRef,              // "<name>.<island>" folder inside the campaign
    outcomes: Vec<OutcomeId>,
    lives: Lives,
    entry_guard: Option<Expr>,        // lint-only precondition (IC `require_flag`)
    briefing_variants: Vec<ConditionalText>,
    management: Management,           // Managed | Preserved (see §7.6)
}
/// Engine `lives`: -1 / >0 / 0. No sentinel in the model.
pub enum Lives { Unlimited, Retries(NonZeroU8), NoRetry }
pub struct OutcomeDecl { id: OutcomeId, node: NodeId, name: Ident, polarity: Polarity,
                         debrief: Option<LocalizedHtml>, payload: Vec<PayloadField> }
pub enum Polarity { Success, Partial, Failure }   // presentation only; sockets follow the edge (§7.2): a Failure
                                                  // that retries uses `lost`, a story-moving Failure takes an END socket
pub struct PayloadField { name: Ident, ty: ValueType, source: PayloadSource }
pub enum PayloadSource { MissionVar(VarId), Probe(ProbeExpr) } // probe = typed raw engine expr, not simulatable

pub struct Transition {
    id: EdgeId, from: NodeId, on: EdgeTrigger,
    rank: u16,                        // order among edges with the same (from, on); first match wins
    guard: Guard, effects: Vec<Effect>, to: NodeId,
}
pub enum EdgeTrigger { Outcome(OutcomeId), AnyOutcome, Choice(ChoiceId), Auto }
pub enum Guard { Always, When(Expr) }
pub enum Effect {
    Assign { var: VarId, value: Expr }, Add { var: VarId, delta: Expr },
    Include { var: VarId, member: Expr }, Exclude { var: VarId, member: Expr },
    Roster(RosterEffect), Pool(PoolEffect), Journal(LocalizedText),
    RawSqs(RawSqs),                   // escape hatch; lint C14; excluded from the simulator
}
```

The crate has **one `Error` enum** with structured fields. Examples: `TypeMismatch { at: ExprSpan, expected: TypeTag, found: TypeTag }`,
`IntOutOfEngineRange { var: VarId, min: i64, max: i64, limit: u32 }`, `UncoveredCase { node: NodeId, trigger: TriggerTag, witness: StateDigest }`.

### 4.3 Engine encoding (lowering of state)

| Model | Engine representation | Why |
| --- | --- | --- |
| `Bool` | SQS bool global `cmp_<v>` | Native; never compared with `==` (F1) |
| `Int(range)` | Scalar | `f32`-exact within ±2^24 (F2) |
| `Enum` | Scalar ordinal; a generated comment table maps ordinals to names | Avoids case-insensitive string equality (F3). Stable across renames |
| `Set<Enum>` | Array of ordinals, **copy-then-assign only** | `in` (F4). Avoids in-place `set` aliasing (doc 18 §6.1 gotcha 4) |
| Roster record | **Flat scalars** `cmp_r_<char>_st`, `_dmg`, `_xp`, custom fields; identity/gear blobs through `saveIdentity`/`saveStatus` under `"<runId>_<producerNode>_<char>"` | No arrays means no aliasing. For pre-placed slots, rank persists via identity (F13). Versioned keys come from doc 18 §8.4 |
| Vehicle pool | Array of `[classOrdinal, count]` rows, rebuilt at commit | Variable length |
| Native pool | `addWeaponPool`/`addMagazinePool` in the finisher only | Pool commands are no-ops before `AddMission`; changes are lost on an aborted resume (doc 18 §6.4) |
| `visited`/`last` | `cmp_v_<node>` (count) and `cmp_o_<node>` (last outcome ordinal), updated at commit | Non-idempotent writes must not happen in init (doc 18 gotcha 5) |
| Housekeeping | `cmp_schema` (model hash), `cmp_run` (nonce), `cmp_route` (router token), `cmp_prod` (producer node for `objects.sav` keys) | Doc 18 §8.3/§8.4. `cmp_route` is new (§7.2) |

## 5. Transition-condition language ("CXL")

### 5.1 Options

| Option | Static checking | Simulatable | Engine-faithful | AI/diff friendly | Novice friendly | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| Reuse raw SQF/SQS expressions | Poor: dynamic types, and 1.99 vs CWR command sets differ (F5) | Needs a full SQF interpreter | Trivially, but it inherits every quirk (F1–F7) | Medium | Low | **Escape hatch only** |
| Visual builder only (RPG Maker style) | Good | Good | Good | **Poor** (no text form to diff or generate) | High, until complexity grows | **Second view** |
| **Small typed DSL + projectional visual builder** | **Full** (types, scopes, ranges, coverage) | Yes (tiny pure interpreter) | Yes, via a whitelisted lowering | **High** (canonical text) | High (the builder) | **Recommended** |

### 5.2 Grammar sketch (EBNF)

```text
guard     = expr ;
expr      = or ;
or        = and { "or" and } ;
and       = not { "and" not } ;
not       = "not" not | rel ;
rel       = sum [ relop sum ] | sum "in" sum ;            (* `in`: member in Set *)
relop     = "==" | "!=" | "<" | "<=" | ">" | ">=" ;
sum       = prod { ("+" | "-") prod } ;
prod      = unary { ("*" | "/" | "mod") unary } ;         (* "/" and "mod" only by a non-zero literal *)
unary     = "-" unary | atom ;
atom      = INT | "true" | "false" | TEXT | enumlit | ref | call | "(" expr ")" ;
enumlit   = TypeName "." Case ;                            (* Bridge.intact; Outcome literal: M03.victory *)
ref       = ("camp" | "mis" | "out") "." ident
          | "roster" "." ident "." field                   (* roster.dimitri.status *)
          | "pool" "." ident ;                             (* pool.vehicles.t72 *)
call      = ("visited" | "visits" | "last" | "count" | "has" | "alive"
             | "min" | "max" | "clamp" | "any" | "all") "(" [ expr { "," expr } ] ")" ;
effects   = effect { ";" effect } ;
effect    = target ("=" | "+=" | "-=") expr
          | "include" target expr | "exclude" target expr
          | "journal" TEXT | "roll" target INT ;           (* roll: Decision nodes only, result stored *)
TEXT      = '"' { char - ( '"' | ':' | newline ) } '"' ;   (* F6: no ':' may reach a `?` line *)
```

Examples:

- Guard: `out.hostages_saved >= 3 and camp.village_rep > 10 and not has(camp.intel, Intel.ambush_route)`
- Effects: `camp.village_rep += 5; include camp.intel Intel.radio_codes; roster.dimitri.status = Status.wounded`

### 5.3 Typing and static checks

- **Scope legality.** `mis.*` is valid only in the node's own content and on its outgoing edges; `out.*` only on edges triggered by that outcome;
  `camp.*` everywhere, but guards see the state **before** that edge's effects run.
- **No implicit coercions.** Enums are comparable only within their own type. `==` on `Real` is an error; use `<=`/`>=`.
- **Interval analysis.** Every `Int` expression gets an interval. It is an error if a result could exceed ±2^24 (F2) or an assignment could leave
  the declared range (wrap it in `clamp(…)`).
- **Purity and determinism.** Guards cannot mutate state and cannot call `random`. `roll` exists only as an effect on `Decision` nodes, and its result is
  stored. Randomness is therefore explicit, and restart-from-row behaviour is predictable. The engine has no seedable RNG **[I]**, so a restart
  re-rolls.
- **Coverage (totality).** For every (node, trigger) the guards, in rank order, must cover every state. A trailing unguarded edge ("otherwise")
  satisfies this trivially. Otherwise the checker enumerates the finite domains of the referenced variables, partitioning `Int` domains at the
  constants that appear in the guards. It reports a **witness state** for any gap (lint C03). An SMT solver is unnecessary at first.
- **Shadowing and constant guards.** The same enumeration flags edges that can never win (C04) and tautologies/contradictions (C05).
- **Name hygiene.** Engine names must be unique after lower-casing and must not collide with mission globals or reserved `cmp*` names (C08).

The visual builder edits the same AST: `ALL of` / `ANY of` groups, a variable picker tree (Campaign / This mission / Outcome payload / Roster /
Pools / Facts), operators filtered by type, and typed literal editors (enum dropdown, range-limited spinner). Arithmetic subtrees appear as
editable text chips. The canonical pretty-printer keeps the text form stable for diffs and for the AI.

### 5.4 Lowering table (target `Cwa199`, SQS expressions)

| CXL | SQS | Evidence / caveat |
| --- | --- | --- |
| `a and b`, `a or b`, `not a` | `(a) && (b)`, `(a) or (b)`, `!(a)` | **[V]** F1 (`or` is registered alongside the double-pipe form) |
| `a == b` (Bool) | `((a) && (b)) or (!(a) && !(b))` | No `bool ==` **[V]** F1. A `Cwr` profile may emit `(a) boolEq (b)` |
| `x < y` (Int / Real) | `(x) < (y)` | `f32` **[V]** F2 |
| `e == Bridge.intact` | `(cmp_e) == 0` | Ordinals (F3) |
| `has(S, K)` | `(k) in (cmp_S)` | `in` 1.99 **[U]**. The fallback lowering expands to a disjunction over `select` of a bounded-length array |
| `count(S)` | `count (cmp_S)` | 1.99 **[U]** |
| `visited(M)`, `last(M) == M.victory` | `cmp_v_m > 0`, `cmp_o_m == 1` | Generated facts |
| `min(a,b)` | `((a)+(b)-abs((a)-(b)))/2` | `abs` **[V]** `EVAL:express.cpp#L1180`. Exact when ranges stay ≤ 2^23 |
| `alive(roster.x)` | `alive u_x` (in-mission, the slot unit) or `cmp_r_x_st != 5` (between missions; Dead = 5) | `alive` **[V]** F14 |
| Text literal | `"txt"` inside `?` conditions | No `:` (F6); length < 4 KB (F7) |

The **probe whitelist** (Open question 1) lists the exact operator and command set allowed per target profile. The compiler refuses anything
outside it (C14).

### 5.5 Semantics of a node's transition table

1. The mission runs, and mission variables are written by triggers and scripts. A "Set campaign var" action inside a mission writes a
   **shadow** (`cmp_<v>` itself); it is not committed.
2. The designer raises an outcome ("Finish: *victory*") or the player makes a choice.
3. **Select.** Among edges whose trigger matches, in rank order, the first whose guard holds wins. Guards read campaign state (including uncommitted
   in-mission writes), mission vars and payload.
4. **Apply** that edge's effects, in order.
5. **Commit.** Update the built-in facts, then `saveVar` every persistent variable. Commit happens exactly once, and only at the end (doc 18 §8.4).
6. **Route** to the target. An edge whose target is an `Ending` ends the campaign.

## 6. Graph editor UX

### 6.1 Node types

| Node | Canvas glyph (OFP marker idiom) | Meaning | Lowering (§7) |
| --- | --- | --- | --- |
| Mission | Objective flag with a socket meter "4/7" | Playable mission with named outcomes | Managed mission + sockets |
| Cutscene | Film strip | Linear story beat; varies content by state via `initintro.sqs` | Group-less mission; exits via `lost`, with every code mapped to the successor (§7.2) |
| Decision | Diamond | Automatic branch on state; may `roll` | Router (shared folder) |
| Choice | Radio set | The player picks among options with availability guards; supports unchosen effects | Tiny choice mission: radio `ALPHA..JULIET` (F11) or actions |
| Hub | Base/camp flag | Repeatable base camp: spokes (operation cards with On Success / On Failure / If Skipped / Time Window), return edges, a turn counter, optional roster selection | Hub mission + routers |
| Ending | Chequered flag (Victory/Defeat/Neutral) | Terminal; explicit, never implicit | Empty end key (campaign ends) after an optional final cutscene |
| Act (group) | Coloured area marker behind nodes | Cosmetic grouping; optionally bound to an engine chapter | Single chapter by default (doc 18 §4) |

Edges are drawn as map arrows labelled `outcome · guard summary · Δeffects`. Failure edges are drawn red and dashed. Edges added by the compiler
(routers) appear only in the **Compiled overlay**.

### 6.2 Editing transitions

Selecting a node opens its **transition table**, an Arcweave-style `if / elseif / else` list for each trigger. Columns: `When` (outcome/choice),
`If` (CXL or builder), `Then` (effects), `Go to`, and `Debrief`. Rows can be dragged to reorder (rank). A red row means an uncovered witness
state, shown inline (C03). The socket meter shows the socket count the compiler will need; going above 7 shows "router inserted (+1 book row,
+1 short load)".

### 6.3 Panels

- **Variables:** declarations and types, plus IC-style **Set in / Read in** cross-references (nodes, edges, mission triggers, texts). The same panel
  shows scope conflicts, unused variables and the value range reachable at the selected node.
- **Roster:** each character with a status ladder and death policy. It lists the missions where the character has a slot and the paths on which the
  character can be dead.
- **Pools:** the native pool baseline, vehicle rows and item counters.
- **Text variants:** briefing, intro and debrief slots with `ConditionalText` rows; coverage is shown per reachable state bundle.
- **Compile preview:** generated `description.ext`, the file list, router count, book-row estimate, `.sqc` growth estimate and whitelist status.

### 6.4 What-if simulator, Path Explorer, coverage

- **Playthrough** is styled like the in-game campaign book. You step node by node and pick outcomes, choices and payload values (probes become
  inputs). A side pane shows state diffs (an articy-style journey with "Analysis vs Player" filtering). Journeys can be saved, replayed and diffed
  (IC journal).
- **Path Explorer** runs an exhaustive bounded search over `(node, state)`. Payload domains are abstracted by the guard constants, so it validates
  "bundles" rather than every permutation; revisited `(node, state)` pairs are deduplicated; a zero-gameplay cycle with no state progress is an
  error (C09). Output: reachable nodes and endings with **witness paths**, per-edge coverage, per-variable ranges at each node, and "book rows per
  path" (UX cost). Filters answer queries such as "paths reaching Ending B where Dimitri is dead".
- **Coverage heat:** green means covered by a saved journey, yellow means reachable but only explored, red means unreachable (colours after IC
  D038, where red means "untested").
- **Start at node X with state S** generates a throwaway debug campaign: a setup router saves S and routes to X (doc 18 §8.3). On CWR, Trident or
  the debug `endmission end1..end6` can drive traversal automatically (doc 18 §10).

### 6.5 Lints

| ID | Severity | Rule |
| --- | --- | --- |
| C01 | warn | Unreachable node (from `start` under any state) |
| C02 | error | A non-Ending node has a trigger with no outgoing edge |
| C03 | error | Uncovered case: a (node, trigger, state) where no guard holds. Reports a witness |
| C04 / C05 | warn | Shadowed edge (never first match) / constant guard |
| C06 | error | Undeclared reference, type error, or scope violation |
| C07 | warn / info | Unused, write-only, or never-written variable |
| C08 | error | Engine-name collision after lower-casing, or with mission globals / reserved `cmp*` |
| C09 | error | Zero-gameplay cycle without state progress (router livelock) |
| C10 | error | Implicit campaign end: an engine key would be empty without an `Ending` node, or a top-level `exitScore` can end the campaign after a mission without `noAward` (§1) |
| C11 | info | Edge crosses a chapter-bound act into a non-first node → router inserted |
| C12 | info | Socket demand above 7 → router inserted (UX cost shown) |
| C13 | error | A designer-authored END/LOOSE trigger (including the legacy `WIN` alias of END1, `CWR:AI/ArcadeTemplate.cpp#L201`) in a managed mission (AND semantics would break routing, §1) |
| C14 | error | A command or operator outside the target whitelist (raw SQS, probes, lowering) |
| C15 | error | A text literal or line that breaks the SQS limits (F6/F7) |
| C16 | error | State-dependent content in a chapter cutscene, outro or award cutscene (no vars there, doc 18 §6.1) |
| C17 | error | `Int` range or arithmetic beyond ±2^24 |
| C18 | warn | A character is referenced on a path where they may be dead or captured without a status check; a must-survive character lacks a death edge |
| C19 | warn | A pool or vehicle class is not in the local catalog |
| C20 | info | `.sqc` growth budget: rows × variables × size (doc 18 §6.1) |
| C21 | warn | A reachable state bundle has no matching briefing/intro/debrief variant |

### 6.6 Mission-editor integration

- **Trigger Type:** a managed mission's Type combo offers **"Campaign outcome: *name*"** instead of END1..6/LOOSE. On Activation then runs the
  generated finisher. Mission variables appear in trigger conditions through the CXL.
- **Presence and conditions:** unit **presence conditions** and trigger conditions accept CXL (`camp.bridge == Bridge.destroyed`), lowered into
  `presenceCondition`/`expCond` (F12).
- **Roster slots:** a unit can be marked "Roster slot: dimitri"; it must be non-playable (F12). The compiler then generates its presence condition, `loadIdentity`/`setDammage`
  init, and commit code.

### 6.7 Retro look

The designer is one more display in the same vector chrome as the rest of the editor: 1-px lines, flat fills, OFP fonts or the OFL fallback, and an
800×600-authored UI space (`docs/research/05-visual-fidelity-and-ui-resources.md` TL;DR). The **Flow view** background reuses the editor-map paper
palette and grid. The **Theatre view** places nodes at each mission's area on the real island map, one tab per island; OFP campaigns are
island-bound, so this reads as native **[I]**. The Playthrough uses the campaign-book layout.

### 6.8 Complexity tiers (one data model)

| Tier | Visible features |
| --- | --- |
| Classic | Missions, Won/Lost outcomes (Lost retries the mission by default, §7.2), automatic edges: OFP-equivalent |
| Branching | Named outcomes, flags, the condition builder, Choice nodes, Endings |
| RPG | Roster, pools, payloads, relationships, text variants |
| Strategic | Hubs, operation cards, countdowns/doom clocks, turn counters, `roll` |

## 7. Compiler to vanilla engine mechanics

### 7.1 Pipeline

1. **Check** (§5.3, §6.5); errors block compilation.
2. **Normalize:** bind acts to chapters (single chapter by default); expand Choice and Hub nodes; compute each node's socket demand; insert
   routers; add a **bootstrap router** as the first node unless `start` has no incoming edges. The bootstrap initialises every variable (there is
   no `isNil`), sets `cmp_run`/`cmp_schema`, and fills the native pool after gameplay starts (doc 18 §6.4).
3. **Lower** state (§4.3) and expressions (§5.4) under the target whitelist.
4. **Emit** through the lossless CST patchers of `docs/research/04-mission-data-model-and-formats.md` §12: the campaign `description.ext`
   (flattened, every key explicit, doc 18 §2); per mission a patched `mission.sqm` (7 sockets, rewritten outcome triggers, roster slots), `init.sqs`
   with an inlined generated prologue, `cmp_finish.sqs`, an `exit.sqs` fallback commit, `OBJ_` variant sections in `briefing.html`, and debrief
   sections; router folders; the `stringtable.csv` merge; source maps (each generated line ↔ model element).
5. **Verify:** re-parse all output, re-run the whitelist and line limits, recompute router and book-row counts, and compare with the simulator.

The model lives in the sidecar `ofp-editor.campaign.toml` at the campaign root, excluded from PBO export (the same policy as the mission sidecar in
doc 04 §12.3). Generated files carry `; ofp-editor:generated <model-hash>` headers and embed each guard's CXL source as a comment, so a campaign can
be reconstructed if the sidecar is lost.

### 7.2 Socket allocation and routers

- **Socket key.** For each managed Mission node, a socket key = (debrief variant, successor). A retry key (a Failure edge back to its own node)
  takes `lost`; every other key, including a Failure that moves the story, takes one of `end1..6` with its own debrief section. *Superseded in
  the 2026-09-27 consolidation pass:* the earlier default "Failure-polarity keys prefer `lost` (OutroLoose + `Debriefing:Loser`)" did not match
  the shipped campaigns; see the routing defaults below.
- **Routing defaults** (doc 35 §3.1 and its rc77; the socket/finisher shape itself is BI's ending idiom, doc 35 §3.3 **[V]**). In every official
  campaign `lost` means "retry this mission" (the one exception is 1985's closing coda, whose `lost` ends the campaign), failures that move the
  story use END codes, and no shipped briefing defines `Debriefing:Loser` **[V, doc 35]**. The compiler therefore defaults to **[I]**:
  1. **Retry on LOOSE.** A Mission node's Failure outcome gets a default self-loop edge through `lost`; a self-loop adds no book row (doc 18 §4).
  2. **Story-moving failures on END sockets**, each with its own `Debriefing:End<n>` section.
  3. **`lost`-forward** (OutroLoose plus a `Debriefing:Loser` section) stays available as an explicit per-outcome option, never the default.
  4. **Cutscene nodes** map `lost` and `end1..6` all to the successor, as every official cutscene node does.
  5. **Chapter-bound acts:** a chapter's last mission leaves its forward mission-level keys empty (still written out as `""`, doc 18 §2) and
     relies on the chapter-level keys, so the next chapter's cutscene plays before its `firstMission`; its `lost` still names the mission
     itself when it retries. An edge into a non-first node of another chapter still needs a router (C11).
- **Direct routing.** With ≤ 7 keys, the finisher's selected rule maps straight to its key's socket (Pattern A, doc 18 §8.1).
- **Router routing.** Otherwise the mission ends with one socket per **debrief narrative** (at most 7). Beyond 7, the compiler moves the finer
  variation into hidden `OBJ_` debrief lines that the finisher reveals (F10); if that is not possible it is a compile error asking the designer
  to merge narratives. It commits `cmp_o_<node>`, sets `cmp_route = <routerId>`, and jumps to a router class that finishes the selection.
- **Router folders.** All routers on one island share **one folder**, `cmpRouter.<Island>` (several classes can share a template, doc 18 §4). Its
  single decision script dispatches on `cmp_route`; each router class has its own end-code map in `description.ext`. A predecessor always sets
  `cmp_route` in its commit and routers never `saveVar` it, so restart-from-router-row is deterministic (the snapshot holds the token) **[I]**.
- **Effect-free routers** decide in `init.sqs`, read-only; the snapshot is taken after init (doc 18 §3). **Routers with effects** decide in a script
  started by a condition-`true` trigger, i.e. after `AddMission`; a commit in init would be baked into the row snapshot and re-applied on restart
  (doc 18 gotcha 5) **[I]**.
- **Router build:** one player group, no `briefing.html`, `debriefing = 0`, empty Intro/Outros, `noAward = 1`, `lives = -1`, a BLACK FADED cut,
  `forceEnd` in the sockets, same island as the predecessor, and a neutral stringtable book name such as "…" (doc 18 §8.2). Fan-out above 7 after a
  router uses a tree of router classes (7^depth leaves). **Cutscene nodes** always exit `lost` (every code is mapped to the same successor, see the
  routing defaults above), so a state-dependent successor goes through a router.
- **Choice/Hub:** radio triggers (≤ 10) or actions set `_choice` and the finisher routes it. The player must be the group leader, or the radio
  items are not listed (F11). Generated code hides unavailable options: `setRadioMsg "NULL"` in CWR **[V]**, or action removal. The hiding
  mechanism is **[U]** on 1.99. Hub roster selection uses actions on squad units ("Take along" / "Leave
  behind") that write selection flags **[I]**.

### 7.3 Generated finisher (sketch, SQS)

```sqs
; cmp_finish.sqs, GENERATED for node m03 "Bridge at Olsha". Called as: [outcomeOrdinal] exec "cmp_finish.sqs"
? cmpFinishing : exit
cmpFinishing = true
_o = _this select 0
; 1) select a rule: reverse-priority assignment, so the LAST matching line wins (no goto needed)
_r = 5
? (_o == 2) : _r = 4
? (_o == 1) : _r = 3
? (_o == 1) && (cmp_rep >= 10) : _r = 2
? (_o == 1) && (cmp_bridge == 0) && (mBridgeIntact) : _r = 1
; 2) effects of the selected rule (arrays: copy, edit the copy, assign)
? _r == 1 : cmp_rep = cmp_rep + 5
? _r == 4 : cmp_r_dimitri_st = 2
? _r == 4 : cmp_r_dimitri_out = 2
; 3) facts, roster capture, pool deltas, then commit every persistent var
cmp_o_m03 = _o
cmp_v_m03 = cmp_v_m03 + 1
cmp_prod = "m03"
? alive u_dimitri : cmp_r_dimitri_dmg = getDammage u_dimitri
saveVar "cmp_rep"
saveVar "cmp_o_m03"
; ... one saveVar per declared persistent variable ...
; 4) publish LAST: an exec'd script runs at most 100 lines per step (F8), so sockets must never see a half-finished state
; rules 4 and 5 are Failure-polarity: rule 4 moves the story on its own END socket (own debrief);
; rule 5 is the retry and uses the `lost` socket (0), which description.ext maps back to m03
_e = 0
? _r == 1 : _e = 1
? _r == 2 : _e = 2
? _r == 3 : _e = 3
? _r == 4 : _e = 4
cmpEnd = _e
```

- **Sockets.** The 7 socket triggers in `mission.sqm` are condition-only: `expCond = "cmpEnd == 3"`, `type = "END3"`, `expActiv = "forceEnd"`.
  The generated prologue (the first lines of `init.sqs`) sets `cmpEnd = -1` and `cmpFinishing = false`. `-1` is an engine-side encoding, not a
  model value.
- **Fallback commit.** `exit.sqs` holds an inlined, straight-line fallback commit for endings that bypassed the finisher, such as the `ENDMISSION`
  cheat (END1). It is guarded by `cmpFinishing`, because `exit.sqs` also runs after every normal non-death ending. Each ending gets its code's
  default rule. It completes within its single call (F8).
- **Roster slots.** The unit's `presenceCondition` is `cmp_r_dimitri_st < 2`; its init line is
  `this loadIdentity (cmp_run + "_" + cmp_prod + "_dimitri"); this setDammage cmp_r_dimitri_dmg` (key scheme from doc 18 §8.4; `loadIdentity` in
  unit init on 1.99 is **[U]**).
- **State-aware briefing.** Each variant paragraph is an `OBJ_cmpN` section; the prologue runs `"cmpN" objStatus "HIDDEN"` for variants whose guard
  fails, before the briefing is built. In CWR, `init.sqs` runs inside `InitVehicles` (`CWR:World/WorldInit.cpp#L629-L632`), and the plan reads
  `OBJ_` vars whenever it is built (F9) **[V by reading]**; ordering on 1.99 is **[U]**. The lines appear as objective entries. **Intros** vary through `initintro.sqs`, where the vars are present;
  **in-mission lines** use `hint format [...]`.

### 7.4 Expressibility: vanilla CWA 1.99 vs engine extension

| Design feature | Vanilla 1.99 | Mechanism | Needs an extension for |
| --- | --- | --- | --- |
| Guards over campaign + mission state + payloads | **Yes** | Finisher (Pattern A) | — |
| More than 7 successors; shared decision logic; any-to-any edges | **Yes** | Router trees; single chapter | No-world routing (E1) |
| Merges, loops, repeatable missions | **Yes** | A self-loop adds no book row (doc 18 §4) | — |
| Optional side missions, hub-and-spoke base camp, operation cards, turn counter, doom clock | **Yes** (coarse UI) | Hub mission + counters decremented at commit | — |
| Failure branches instead of game over | **Partial**: only while the player is alive | END sockets with their own debriefs (LOOSE retries by default, §7.2); "captured" and "squad wiped" patterns | Routing player death: engine change; **not proposed** |
| Persistent squad (identity, wounds, rank, xp) | **Yes** | Flat vars + identity/status blobs + presence conditions | `objects.sav` reset on a new game (E6) |
| Weapon pool / vehicle pool / items | **Yes** | Native pool / saveVar rows | — |
| State-aware briefings | **Partial** | Hidden `OBJ_` variants, intro variants, hints | — |
| Debrief text per path | **≤ 7 narratives per mission**, plus state-dependent objective lines | End-code sections + revealed `OBJ_` entries (F10) | — |
| State-aware chapter cutscene / outro / award | **No** | Use Cutscene nodes instead | Var re-injection there (not in doc 18's list) |
| Hide technical rows in the book; zero-load routing | **No** | Neutral naming | E3, E1 |
| Debriefing "Restart" keeps campaign vars | **No** (engine bug) | `lives = 0`, or accept the risk | E5 |
| Rich intermission UI (armory, dialogs) | **Partial / [U]** | Hub mission with actions; `createDialog` if present in 1.99 | — |
| Weighted random edges | **Yes**, re-rolled on restart | `roll` in a router | — |
| Multiplayer campaigns | **No** | — | Out of scope (doc 18 §6.5) |

### 7.5 Targets beyond 1.99

- `Cwr`/`CwrCe` profiles may widen the whitelist, for example to `if … then` via `call`, pending probes.
- An E1 extension could consume a generated declarative `class CEDecide`, whose expression text is identical to the router script (doc 18 §9).
- Output for the `Cwa199` profile always stays valid on 1.99. Profiles only remove routers or rows; they never change semantics.

### 7.6 Round-trip import of hand-written campaigns

1. **Parse** `description.ext` with the lossless CST (text or raP). Resolve inheritance (`MissionDefault`/`NoEndings`) for the model, but **edit
   through patches** of the original nodes.
2. **Map:** chapters → acts bound to chapters; mission classes → Mission nodes with `Management::Preserved`; each non-empty `endN`/`lost` → an
   edge `on: Outcome(legacy_endN)`; chapter fallbacks → edges marked "via chapter entry" (C11); empty keys → explicit `Ending` nodes (pre-satisfies
   C10).
3. **Scan missions without executing anything:** END/LOOSE triggers → legacy outcomes; `saveVar "x"` string literals in scripts and inits →
   `Opaque` variables with their observed assignments; `saveStatus`/`saveIdentity` keys → roster hints.
4. **Preserve mode** (default): mission content untouched; edits change only the `Campaign` classes. **Invariant:** import → no edits → save is
   byte-identical (the doc 04 identity invariant).
5. **Retrofit routers:** once the designer types an `Opaque` variable, a Preserved node's edge can target a Decision node that reads the
   hand-written mission's own `saveVar`s, so state-based branching needs no mission edits **[I]**.
6. **Adopt** (per node, explicit, shown as a diff first): END/LOOSE triggers become outcome triggers and the glue is injected.
7. **Eject:** drop the sidecar and keep the generated files as a plain campaign. Never commit imported game campaigns as fixtures; opt-in corpus
   tests stay local-only (`AGENTS.md`).

## 8. How the AI harness helps

| Typed action (same command bus as the UI, undoable) | Purpose | Guardrail |
| --- | --- | --- |
| `campaign.inspect(scope)` | Compact JSON of nodes, variables, lints and coverage | Read-only |
| `campaign.declare_var(name, type, default, scope)` | Add state | Type/range checks |
| `campaign.add_node` / `connect(from, on, guard_cxl, effects_cxl, to, rank)` | Build the graph | Parse + typecheck; diagnostics return to the model so it can self-correct |
| `campaign.lint()` / `simulate(policy)` / `explore(query)` | Ground truth for the agent | Deterministic |
| `campaign.propose_branch(spec)` | Sub-graph plus mission skeletons as a **ChangeSet** | Not applied until the user approves; must lint-clean |
| `text.generate_variants(slot, partition)` | State-aware briefing/debrief/dialogue lines per reachable state bundle | C21 coverage; the ≤ 7 debrief budget |
| `campaign.compile_preview(target)` | Router, row and whitelist cost | No writes |

- **Consistency checks** combine simulator facts with text: dead or captured characters named in later texts on some path (C18); briefing promises
  ("if skipped…") that no path honours; items referenced before they can be obtained; branch explosion without convergence (IC D016 heuristic).
- **Effort levels:** low = explain lints and fix type errors; medium = write guards and text variants; high = draft whole branches plus missions via
  mission-editor actions, then iterate `explore → fix` until the lints are clean.
- **BYO/local models:** the CXL grammar plus the variable table fits in a small prompt.
- **Untrusted output** (IC V40 precedent): the agent never emits SQS; raw-SQS effects require a human toggle.

## 9. Implementation and test plan (proposal-only)

- **Crates:** `ofp-campaign-model` (types, command validation); `ofp-campaign-lang` (lexer, parser, typechecker, intervals, coverage,
  pretty-printer); `ofp-campaign-sim` (interpreter with engine-faithful `f32`/`strcmpi` semantics, explorer); `ofp-campaign-compile` (lowering and
  emitters over `ofp-config`/`ofp-mission`); `ofp-campaign-import`.
- **Proof artifacts:** golden emission fixtures (synthetic campaigns only); `proptest` over random ASTs asserting
  `interp(ast) == mini_sqs_interp(lower(ast))` with a tiny SQS-subset interpreter; byte-identity import round-trips; fuzzing of the CXL parser and
  importer; an opt-in local Trident/CWR harness that plays every edge; the manual 1.99 probe-mission suite (Open question 1).
- **Phases:** P0 import/Preserve + graph view → P1 managed missions, CXL, sockets, routers, simulator → P2 roster, pools, text variants → P3 hubs,
  strategic tier, AI actions → P4 optional CE profiles.

## Open questions

1. **1.99 whitelist probe [U]:** `in`, `count`, `select`, `call`, `if/then`, `boolEq`; `addAction`, `createDialog`, and `setRadioMsg "NULL"` used to
   hide a radio item; `getDammage`; the 5-element `createUnit` with a rank; `objStatus "HIDDEN"` in `init.sqs` before the briefing, and revealed
   `OBJ_` lines in the debriefing; `loadIdentity` in unit init; `presenceCondition` reading campaign vars; the `exec` line cap (is it 100 in 1.99?);
   trigger vs script order within a frame. Plus the doc 18 parity items (`debriefing = 0`, `forceEnd`/`titleCut`,
   array aliasing).
2. Should `Real` exist at all, or should all quantities be bounded `Int` to remove float lints? (Product.)
3. Is a raw-SQS escape hatch acceptable in shared campaigns, or should it be `Cwr`-profile only? (Product/security.)
4. Should Choice/Hub UI prefer radio (10 slots, vanilla since 1.0 **[I]**) or actions? Depends on probe 1 and UX testing.
5. Is `.sqc` size or load time a practical limit for large RPG state (hundreds of vars × dozens of rows) on 1.99? Doc 18 flags growth; no limit is
   known **[U]**.
6. Is there an identifier length limit for globals or `saveVar` names in 1.99 **[U]**? The generator assumes ≤ 24 characters.
7. Should restart-from-row re-roll random Decision nodes, or should `roll` pre-roll in the predecessor's commit for reproducibility? (Design.)
8. Will CWR-CE accept E1/E3 (invisible routers) and E5/E6 (robustness) (doc 18 §9)?

## Sources

**Code (pinned):**

- `BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/express.cpp` (L405-L438, L1067-L1079, L1100-L1196)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Game/Scripting/Scripts.cpp` (L154-L172, L228-L334, L412-L510, L577) and `Scripts.hpp` (L53-L54)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Game/Commands/GameStateExt.cpp` (L882-L885, L935-L947, L1000-L1078, L1221-L1393);
  `GameStateExtUi.cpp` (L1825-L1860, L2213-L2268); `GameStateExtGrp.cpp` (L412-L425); `GameStateExtWorld.cpp` (L237-L310)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/WorldSetup.cpp` (L1378-L1407); `World/WorldInit.cpp` (L618-L632);
  `UI/OptionsUIApp.cpp` (L877-L895); `UI/InGame/InGameUIMenu.cpp` (L628-L683)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterStats.cpp` (L69-L80); `AI/AICenterImpl.cpp` (L1396-L1410, L1534);
  `AI/ArcadeTemplate.cpp` (L159-L168, L191-L203, L232-L362)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/OptionsUI.cpp` (L1894-L2022); `World/WorldImpl.cpp` (L541-L657); `UI/DisplayUI.cpp` (L126);
  `UI/DisplayUIMenus.cpp` (L984-L997, L1325)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapDialogs.cpp` (L910-L912, L1062-L1145); `UI/Map/UIMapDisplayBriefing.cpp` (L311-L332,
  L427-L481); `UI/Map/UIMapExtDisplay.cpp` (L1400-L1409)
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09d/D021-branching-campaigns.md` (L26-L104)
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D038/D038-campaign-editor.md` (L35-L94, L156-L190, L279-L330, L445-L462);
  `D038-core-architecture.md` (L133-L137, L223-L241); `decisions/09f/D016/D016-branching-world-campaigns.md` (L53-L77)
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/modding/campaigns.md` (L9-L15, L94-L262, L619-L651, L1201-L1369, L1718-L1742,
  L2012-L2039, L2842, L3105-L3124); `modding/enhanced-campaign-plan.md` (L59-L103, L323-L405, L1830-L1850)

**Repository docs:** `docs/research/18-campaign-system-in-engine.md` (engine truth); `docs/research/04-mission-data-model-and-formats.md` §3, §12;
`docs/research/05-visual-fidelity-and-ui-resources.md` TL;DR; `docs/research/35-lessons-from-real-content-and-later-armas.md` §3.1, §3.3, §9
(rc77), §10 (routing defaults).

**Web (accessed 2026-09-26; "fetched" unless marked "search"):**

- Narrative tools: <https://www.articy.com/help/adx/Scripting_in_articy.html>, <https://www.articy.com/help/adx/Presentation_Simulation.html>,
  <https://twinery.org/cookbook/terms/terms_variables.html>, <https://github.com/inkle/ink/blob/master/Documentation/WritingWithInk.md>
- Yarn Spinner: <https://docs.yarnspinner.dev/write-yarn-scripts/scripting-fundamentals/logic-and-variables>,
  <https://docs.yarnspinner.dev/write-yarn-scripts/scripting-fundamentals/smart-variables>,
  <https://docs.yarnspinner.dev/write-yarn-scripts/scripting-fundamentals/enums> (search)
- Arcweave / Chat Mapper / StateTree / RPG Maker: <https://docs.arcweave.com/project-items/branches>,
  <https://docs.arcweave.com/project-items/variables/overview> (search), <https://www.chatmapper.com/docs/topics/idh-topic160.html>,
  <https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-state-tree-in-unreal-engine>,
  <https://rpgmakerofficial.com/product/MZ_help-en/01_09_03.html>
- Creation Kit / Aurora (search; 403 to the fetcher): <https://ck.uesp.net/wiki/GetStageDone>,
  <https://nwnlexicon.com/index.php/Conversation_Conditional_Script>, <https://nwnlexicon.com/index.php?title=AddJournalQuestEntry>
- Arma 3 campaigns: <https://community.bistudio.com/wiki/Campaign_Description.ext>,
  <https://pmc.editing.wiki/doku.php?id=arma3:missions:east-wind-campaign-description.ext>
- DCS Liberation: <https://github.com/dcs-liberation/dcs_liberation>, <https://github.com/dcs-liberation/dcs_liberation/wiki/First-operation>,
  <https://github.com/dcs-liberation/dcs_liberation/wiki/Squadrons-and-pilots>
- Strategy games: <https://en.wikipedia.org/wiki/XCOM_2>, <https://en.wikipedia.org/wiki/BattleTech_(video_game)>,
  <https://en.wikipedia.org/wiki/Jagged_Alliance_2>, <https://en.wikipedia.org/wiki/Mount_%26_Blade>
- OFP tools: <https://www.ofpec.com/editors-depot/index.php?action=list&game=OFP&cat=to&type=me> (OfpCmaker, Campedit)

## Verification notes

Adversarial fact-check, 2026-09-26. Every CWR and IC code pointer above was re-read at the pinned commits. The web pages re-fetched were
Campaign_Description.ext, East Wind, Arcweave branches, Yarn Spinner, DCS Liberation (README and First-operation), RPG Maker MZ and Twine;
their quotes match. BIKI command pages returned 403, so 1.99 command presence stays **[U]**.

- **Confirmed:** the 7-code `NextMission` lookup with its chapter/`firstMission` fallback; END AND-semantics with LOOSE first; `f32` scalar
  compares; `strcmpi` string `==`; the `?`-line split at the first `:`; the 4096-byte line buffer (longer lines are silently truncated); the
  100-line `exec` cap and `INT_MAX` for init/exit/initintro; `OBJ_` evaluation and hidden-skip; `objStatus` → `OBJ_<id>`; end-code debrief
  sections; `ALPHA`..`JULIET`; `setRadioMsg`; no `setRank`/`rank`/`isNil`; the `saveVar` lower-case upsert; the snapshot at `AddMission`
  (`OptionsUI.cpp#L1132`); and all IC citations.
- **Corrected:**
  1. `==` is also registered for objects, groups and sides. CWR has `boolEq`/`boolNe` for booleans.
  2. `exitScore` is a global campaign-exit condition.
  3. An `exec` from `exit.sqs` does run, but only for one step.
  4. The debriefing also evaluates `OBJ_` sections, so "≤ 7 debrief variants" applies only to the narrative sections.
  5. Presence conditions apply only to non-playable units and empty vehicles. Campaign-var visibility there is now verified by reading.
  6. `createUnit` takes a rank.
  7. The radio menu requires the player to be group leader, and in CWR `null` text hides an item.
  8. The finisher now uses `getDammage` (listed in F14) instead of `damage`; both are registered in CWR.
- **Caveat:** all engine facts come from CWR, the remastered engine, and are not from 1.99 binaries. Open question 1 remains the gate.

### Consolidation pass (2026-09-27)

- **Routing defaults revised (doc 35 §10 "Doc 19" and rc77).** Evidence checked in doc 35 §3.1 (every official playable node except 1985's
  closing coda maps `lost` to itself; every cutscene node maps all codes forward; a chapter's last mission relies on the chapter fallback;
  story-moving failures use END codes), §3.3 (BI's socket idiom) and §4 / its verification notes (no shipped briefing defines
  `Debriefing:Loser`). Edited: the TL;DR compiler bullet; the `Polarity` and `Cutscene` comments in §4.2; the Cutscene row in §6.1; the Classic
  tier in §6.8; the §7.2 socket-key bullet (old default kept as a superseded note) plus a new routing-defaults bullet; the §7.3 finisher example
  (rule 4 now takes END4, rule 5 retries on `lost`); the failure-branch row in §7.4; Sources. The new defaults are a proposal **[I]**; the
  underlying corpus facts are **[V]** in doc 35.
- **Renames checked:** this doc has no references to the concept manual, the live tutorials or doc 33, so nothing was renamed.
