# The no-code ladder: attributes, modules, rules and scripting

Research doc 31 for `ofp-editor`. Research date: 2026-09-27. Audience: contributors and LLM coding agents reading only this
file. Status: **proposal-only**; every design section is [I] unless a line says otherwise.

**Question answered.** The owner asked to "upgrade the entire experience" of scripting, to make camera and cinematic
scripting first-class, to let users achieve as much as possible without scripting, and to make everything the community
loves "easy, not hacky". This doc tests one answer: a **no-code ladder** of five rungs (attributes and presets, typed
modules, a rule builder, a cinematics timeline, the script editor). Every rung compiles to plain vanilla engine content for
the mission's target profile (`Cwa199`, `Cwr` 3.05, `Ce`), and code is always one click away.

**Legend.** **[V]** verified by static reading of the pinned source or a fetched page (nothing was built or run, so [V]
never means "observed at runtime"). **[I]** inferred or proposed by us. **[U]** unknown; needs a probe or a fetch.

**Citation aliases** (expand mechanically): `P:` = `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/`; `EVAL:` =
`BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/`; `GSE:` = `P:Game/Commands/GameStateExt.cpp` (the command
registration table); `CE:` = `ofpisnotdead-com/CWR-CE@b67bf3bd62:`. Unless a CE line is given, a `P:` citation also holds
for CE; in `GameStateExt.cpp`, CE lines are one lower up to L885 and two lower from L887 on, because CE has no `endGame`
row (3.05 L886) (corrected 2026-09-27; see Verification notes). Where a table repeats a file already
cited in full, the bare file name means that path; every full path is listed under Sources.

**Companions, not repeated here.** Doc 03 (dialog fields, Effects dialog), doc 04 (file formats, `description.ext`,
briefing, hooks), doc 08 (Preview, harness), doc 09 (community wishlist), doc 17 §6 (templates and compositions), docs 18/19
(campaign engine, CXL condition language, compiler), doc 21 (agent doctrine, step shapes), doc 22 (plugin tiers, T0 packs,
minijinja), doc 23 (catalog, checker, check modes), doc 24 (script risk policy), doc 25 (weak-model harness), doc 26
(campaign content), doc 27 (addons), doc 28 (fun), doc 30 (knowledge stack), doc 32 (cinematics), doc 33 (field manual).
Doc 32 is the detailed rung-4 design (tracks, hosts, compile pipeline, watchdog, preview, shot templates). §6 below only
summarises the engine limits and the contract the ladder relies on; where the two differ, doc 32 governs.

## TL;DR

- **Five rungs, one model, vanilla output.** (1) attributes and presets, (2) typed modules, (3) an event → condition →
  action rule builder, (4) a cinematics timeline, (5) the script editor. Each rung lowers to triggers, waypoints, sync,
  Effects fields, `description.ext`, `briefing.html` and SQS/SQF that the target profile accepts. No addon, no Fwatch, no
  runtime framework; the mission runs with our sidecar deleted (§1).
- **Evidence says tools beat scripts.** The most-downloaded OFP-listed resources on OFPEC are tools that work around editor
  gaps (Eliteness 21,037, which includes lint checking; the Uber Editor Tutorial 10,418; Chris' Script Editor 6,264). The
  most-duplicated gameplay pattern is artillery: 8 separate scripts, 10,597 downloads combined. Counters are biased (post-2007,
  OFP and ArmA mixed), so they rank patterns against each other only [V counts; I interpretation] (§2).
- **Native first.** A rule or module compiles to engine primitives wherever one exists (radio, detected-by, guarded-by and
  switch triggers; END1–6/LOSE; synced held waypoints; Effects fields) and falls back to SQS only for sequencing. The output
  stays readable in the original in-game editor (§4.4, §5.3).
- **The compiler owns the engine's scarce singletons:** one global `onMapSingleClick` string, 10 radio slots, a
  two-element `addAction`, one engine camera-script slot used by the respawn and death hooks, the hook files themselves,
  the global namespace, and a server guard that also works in single player (`isServer` is false in SP) [V facts] (§4.5).
- **Profile-aware lowering.** `Cwa199` output emulates dynamic creation with pre-placed pools. `createGroup`,
  `createMarker`, `createTrigger`, `addWaypoint`, `createShell`, `soundLength`, `remoteExec`, `setDate` and `setVector*` appear
  only in `Cwr`/`Ce` output, and every module shows the resulting min-version badge [V registered in 3.05/CE; absence on
  1.99 rests on BI wiki tags (doc 23 §4) and is unverified on a 1.99 install; I policy].
- **Twenty first-party modules** cover the evidence-ranked patterns: objectives, end states, reinforcements, fire support,
  air transport, respawn, spawn zones and ambient population, patrols, convoys, randomiser, interactions, intel, hostages,
  garrisons, time and weather, effects, tracking markers, save points, conversations and spectator/death sequences. Each is
  grounded in registered commands; the open engine points (vanilla round spawning, marker hiding, hook override, the SP
  server guard) are listed as probes (§4.6, §10). Every module works when dropped, reads back as one plain sentence, is
  tuned by dragging its map footprint, and exposes events and verbs to rules, so a missing option is a rule, not an
  eject (§4.1).
- **Rules reuse the campaign condition language** (doc 19 CXL) extended with mission references, as WHEN/IF/THEN sentences
  with clickable typed slots and explicit ALL/ANY groups. Triggers are evaluated about every 0.5 s with a random phase
  [V static], and the engine has no `triggerActivated` command [V grep], so the compiler chains dependent rules with flags
  (§5).
- **The timeline must fit the real camera:** straight constant-speed moves, a fixed FOV per commit, no roll or independent
  pitch (`camSetBank`/`camSetDir` are bound to the `camSetDive` handler, which nothing reads; `camSetFovRange` is an empty
  stub), `camSetRelPos` resolved once at call time, and no preload command [V]. A safe wrapper restores camera, input and
  border on every path, and fades go on the cut layer, because a title-layer effect blocks the mission end [V]. Trigger
  and waypoint Effects titles, `say` subtitles and direct-channel chat lines all share that title layer [V static] (§6).
- **The script rung gets a mission-aware language service**, silent-failure lints first (the engine drops some errors
  without a log line), engine-exact rename, map links, function libraries, and Preview debugging on Remastered/CE through
  `jsonl` logs and the harness. A runtime error in console text ends a `--test-mission` Preview, which is a design gap
  (§7).
- **Import and lift never force.** Recognisers propose turning known patterns (engine camera captures first) into modules;
  "replace" is offered only when re-emission reproduces the normalised original, otherwise "wrap". Community code is never
  shipped: its licences are unknown (§8).
- **Weak models fill forms, never write glue.** They pick modules and fill typed slots from code-computed menus; raw SQS is
  allowed only in the Expression rung, behind the doc 23 checker and the doc 24 gate, and the agent never runs code (§9).
- **Headline acceptance test:** a newcomer builds an MP co-op mission with base respawn, a reinforcement wave, radio-called
  artillery and a four-shot intro without typing script. It passes every lint, contains nothing outside the target
  profile, and runs a CWR Preview with no script-error log line (§10).

## 1. Principles

| # | Principle | Consequence |
| --- | --- | --- |
| N1 | **No-code first, code always reachable** | Every rung has three escape sizes: an inline typed Expression slot, a per-element "Detach to script", and the script editor. Detaching keeps the model, so "return to form" works while the region is unedited |
| N2 | **Vanilla output per target profile** | Each element compiles for `Cwa199`, `Cwr` or `Ce` using only commands the doc 23 catalog marks available there. Nothing needs our tool, an addon or Fwatch at runtime (doc 09 M10, WN3) |
| N3 | **Native first** | Engine primitives before SQS. A rule that can be one trigger is one trigger |
| N4 | **Glass box** | Every element has a map footprint, a "why" card (rung, module, parameters, which workflow step and model made it), a read-only view of its generated lines, and a provenance header in the output (§8.3) |
| N5 | **Hand edits survive** | Generated regions are hashed. A hand-edited region is never regenerated over without an explicit choice (§8.3; doc 25 E9 requires zero clobbers) |
| N6 | **Code owns facts and wiring** | Class names, marker names, radio slots, handler registration, locality and ordering come from code. Models and users choose among valid options (doc 21 §2) |
| N7 | **Correct by construction** | Output passes the same parser, checker, risk policy and line limits as hand-written code (docs 23, 24) |
| N8 | **Honest about the engine** | No pretend features: `respawn = SIDE` is shown as "behaves like GROUP"; the timeline has no roll channel. Unavailable features are greyed out with a stated reason per profile |
| N9 | **Fun** | Presets, live previews and variations first; long silent generation never (doc 28) |

**The rungs.**

| Rung | The user… | Typical user | Lowers to | Escape |
| --- | --- | --- | --- | --- |
| 1 Attributes and presets | sets typed fields and named presets on existing entities | everyone | sqm fields, init-line prefixes, `description.ext`, briefing | edit the field text |
| 2 Modules | places a typed module on the map and fills its form | everyone | sqm objects plus namespaced SQS, ext entries, hook bodies | Detach to script |
| 3 Rules | writes WHEN/IF/THEN sentences from menus | intermediate | triggers, sync, Effects fields, small SQS | Expression slot; Detach |
| 4 Cinematics timeline | draws camera keys on the map and arranges tracks | storytellers | camera SQS with a safe wrapper, `description.ext` audio and titles | Detach; script |
| 5 Script editor | writes SQS/SQF with a mission-aware language service | scripters | itself | none needed |

## 2. The community pattern inventory → coverage plan

**Sources.** OFPEC's Editors Depot, the largest surviving OFP editing archive, lists 112 OFP scripts, 30 mission-editing
tutorials, 18 script tutorials, 8 cutscene/resource tutorials and 70 functions, each with a download counter [V,
re-scraped 2026-09-27]. Almost every legacy item shows "Added 01 Sep 2007", most likely the site migration, so counters
probably measure later downloads; `[OFPArmA]` items include ArmA users [I]. Other evidence: OFP.info categories, the BIKI
OFP editing FAQ, Faguss's 1.96-vs-1.99 scripting notes, and dated OFPEC forum threads.

**Rung codes.** A attribute/preset · M module · R rule builder · C cinematics · S snippet or script · K compiler-owned
infrastructure · T mission template · X out of scope. "W2" marks a second-wave module.

| # | Pattern | Signal (OFPEC downloads unless noted) | Rung | Lowering and dialect notes |
| --- | --- | --- | --- | --- |
| 1 | Objective chain + briefing | Briefing.html 1,922; Objectives 1,808 | M | `OBJ_n` sections plus `objStatus` (`GSE#L1321`) [V]; ids duplicated between HTML and scripts today |
| 2 | Event logic: ambush, reinforcement, alarm | Basic Trigger Tutorial 2,230; Intelligent Patrols 1,899; All About 'This' 3,076 | R, M | Native trigger synced to a held waypoint; SQS only for sequences |
| 3 | Intros, outros, in-mission cutscenes | Camera.sqs 2,540; Intro to Camera Scripting 2,453; OFP.info VideoMissions (3 pages) | C | `camSet*`/`camCommit` SQS with a safe wrapper (§6) |
| 4 | Conversations, radio, lip-sync, subtitles | Sound Tutorial 3,904; OFP Sound Lab 5,303; Wav2Lip 1,632 | M, C | `say` subtitles from CfgSounds `titles[]`; CfgRadio has one `title` string [V]; `.lip` via `PoseidonTools sound lip` |
| 5 | End states and debriefing | every mission | M | END1–6/LOSE, `Debriefing:EndN`; campaign-managed missions use doc 19 sockets |
| 6 | Respawn | Respawning Tutorial 2,265; Respawn With Weapons 1,391 | A, M | SIDE is not implemented and falls back to GROUP [V]; prefix-matched markers |
| 7 | Loadouts, crates, gear pool | Ammo Crate Contents 1,339; Weapons Buy Menu 1,220 | A | Init lines from the catalog; `class Weapons/Magazines` |
| 8 | MP locality, server-only logic | Triggers, Scripts & addAction in MP 4,376 (third most-downloaded OFP tutorial) | K | Declared locality; guard with a compiler-owned logic (§4.5) |
| 9 | Artillery and indirect fire | 8 scripts, 10,597 combined; snYpir support pack 1,720 | M | Shared click dispatcher; `createShell` on `Cwr`/`Ce` only [V]; vanilla shell spawn [I, probe] |
| 10 | Air strikes, CAS | Airstrike 1,954; Carpet Bomb 1,254 | M | Same "Fire support" family and call UI |
| 11 | Helicopter insertion and extraction | AI chopper transport 2,129 ("notoriously difficult … reliably"); 5 scripts 6,580 | M | LOAD / TR UNLOAD / GETOUT waypoints plus sync first |
| 12 | Spawning, dynamic population | Enemy Respawn & Random Patrol 1,705; spawn managers 2,741 | M | Pre-placed dormant groups on `Cwa199`; `createGroup` on `Cwr`/`Ce` |
| 13 | Patrols | Intelligent Patrols 1,899; Dynamic Waypoints 921 | A, M | CYCLE plus placement radius; runtime waypoints are `Cwr`/`Ce` only |
| 14 | Randomisation | editor fields; OFPWiz Dynamic Campaign 2,611 (Missions Depot) | A, M | Presence probability; server picks and publishes in MP |
| 15 | Particle effects | Drop Tutorial 3,470; Fire Effect 1,745; Vehicle Smoke & Burn 1,326 | M | Bounded `drop` loops, 19-element form |
| 16 | Titles, fades, credits | Cutrsc/Titlersc 1,388 | A, C | Effects title fields always write the **title** layer [V `P:World/Detection/Detector.cpp#L1489-L1509`], so fades and anything near an ending go to SQS `cutText`/`cutRsc` on the cut layer (§5.3, §6.1) |
| 17 | Action-menu interactions | Open & Close Gate 633; the 4,376 MP tutorial | M | `addAction` takes exactly `[title, script]` [V] |
| 18 | AI behaviour, surrender | AI Surrender 2,972 ([OFPArmA]); Improved AI 1,658 | A, M | `disableAI "ANIM"` is 1.99+ [V pdf] and irreversible: flags are OR-ed in and no `enableAI` is registered [V `P:Game/Commands/GameStateExtUi.cpp#L2378-L2403`; `P:AI/AIUnit.hpp#L110`; grep] |
| 19 | Paradrops, cargo drops, rappelling | Parachute Eject 2,237; Paradropping Objects 2,032 | M (W2) | Eject loops; attach loops cost CPU |
| 20 | Custom dialogs | Dialog Tutorial 2,440; OFP Dialog Maker 1,552 | S until L4 | Modules generate their own dialogs; a constrained designer arrives in L4 (§10). Until then this is the largest scripting-only demand in the table |
| 21 | Map-click interfaces | Multiple onMapSingleClick Handler 1,371; tutorial 1,063 | K | One global handler string [V]; generated dispatcher |
| 22 | Compositions, extra placeable objects | Editor103 5,630; Editor Upgrade 2,480; OFP.info EditorExtra ~51 entries | A | Compositions per doc 17 §6, vanilla-only badge |
| 23 | Music and ambient audio | Music, Sound & Radio 1,674 | A | Audio library generates CfgMusic/CfgSounds/CfgEnvSounds/CfgSFX |
| 24 | Save checkpoints | trigger `saveGame` | A, M | Preview deletes save files (doc 09 §2) |
| 25 | Identities, faces, voices | Custom Faces 1,870; Creating Identities 1,045 | A | Cast list → CfgIdentities + `setIdentity` |
| 26 | Revive and medics | Revive Respawn 1,220; First Aid Kit 1,094 | M (W2) | MP only; pairs with spectator |
| 27 | Spectator, death cam | On player killed 664; Faguss spectating script | M, C | Hook differs per respawn mode (§4.5) |
| 28 | Campaign persistence | Campedit 1,305; OfpCmaker 1,252 | docs 18/19 | Already designed |
| 29 | AI backup networks | Group Link II 1,449; Group Link 991 | M (W2) | `knowsAbout` polling |
| 30 | MP game modes | Capture & Hold 1,442 | T | Built from modules; naming convention generated |
| 31 | Explosives, IEDs | Pipebombs & Timebombs 1,302; Car Bomb 1,165 | M (W2) | Reuses effect presets |
| 32 | Animations and poses | Switchmove/Playmove Library 1,263 | A, C | Names from the unit's `Moves >> States` |
| 33 | Moving and tracking markers | Track Vehicles On Map 1,018 | A, M | Marker pool on `Cwa199`; `createMarker` on `Cwr`/`Ce` |
| 34 | Time and weather changes | Dynamic Weather 680 | M, R | Rain is gated by overcast (§4.6) |
| 35 | Vehicle respawn | Vehicle Respawn 1,228 | M (W2) | Editor names are read-only globals (§4.6) |
| 36 | Hostage rescue | Hostage Situation 985 | M | `setCaptive`, `join` |
| 37 | Convoys | OFPEC forum thread, Oct 2002 | M | Column + SAFE; 12-unit group cap [V] |
| 38 | Garrisons | buildingPosCount.sqf 439; guard.sqf 389 | M | `buildingPos`, waypoint `housePos`, GUARD |
| 39 | Commanding several groups | Become Leader 1,044; Multiple Group Control 1,035 | M (W2) | Dispatcher plus radio allocator |
| 40 | Minefields | Single Trigger AP Minefield 1,020 | M (W2) | One area trigger plus SQS, not one trigger per mine |
| 41 | Camera gadgets (bullet, helmet, satellite) | Bullet Cam 1,542; Helmet Camera 1,151 | M (W2) | Gameplay cameras, not cutscenes, so neither §6 nor doc 32 covers them: a wave-2 "Live camera" module (chained `camSetRelPos` commits, §6.1, with the §6.3 epilogue); how a script finds the fired projectile is [U, probe] |
| 42 | Attaching objects | Attach 1,247; TransBox 1,144 | K | No `attachTo` in 3.05 or CE [V grep]; shared per-frame helper |
| 43 | Event handlers | EventHandlers tutorial 2,217 | R | Typed event sources for rules |
| 44 | Timers and countdowns | trigger countdown/timeout | R | Countdown vs timeout semantics shown explicitly |
| 45 | Context variables (`this`, `thisList`, `_this`) | All About 'This' 3,076 | K | Hidden by forms; typed per field in the script rung (§7.1) |
| 46 | CTI / RTS frameworks | MFCTI; Kendo's template 680 | X | Templates or packs; strategic layer in doc 29 |
| 47 | Fwatch features | Fwatch 876; Flashpoint Cutscene Maker; ME3D | X | Provide the demand editor-side: timeline, script editor, harness placement |

**Folded in or deferred:** intel pickup (a composition of Interaction and Objective; no dedicated depot script, [I]),
flares (an effect preset and an artillery round), map objects by id (click-to-attribute, `object` at `GSE#L1142` [V]),
lobby parameters (exactly two, `titleParam1/2` [V doc 04 §5]), scoring (`addScore`, `minScore`), in-mission debug tools
(replaced by Preview debug controls, §7.4), keyboard hacks (out of scope; `AnimChanged` is 1.99+ [V pdf]). Ambient
civilians have no OFP-era depot script, so their popularity is [U].

**Why the old ways felt hacky [I, synthesised from the sources]:** magic strings typed by hand (classes, markers,
prefix-matched respawn markers), invisible coupling (sync lines, trigger-owned flags), timing guessed with `~` delays,
MP locality, configuration through global variables, and thin documentation. Each rung below removes one of these by
construction.

## 3. Rung 1: attributes and presets

An attribute is a typed field on an existing entity. A preset is a named bundle of attribute values (never code) that
ships as T0 data (doc 22 §2.1). Presets cover the "I just want a sleepy sentry" cases without any new object on the map.

| Entity | Attributes beyond the stock dialogs (doc 03 §4) | Lowering | Notes |
| --- | --- | --- | --- |
| Mission | Respawn mode and delay; lobby parameters; score thresholds; HUD items; loading texts; gear pool; cast; audio library; title resources | `description.ext` keys through the lossless patcher (doc 04 §12) | Respawn picker lists SIDE as "same as GROUP" and writes `GROUP` [V `P:World/Entities/Infantry/SoldierOldMove.cpp#L1118-L1120`]: SIDE also logs an ERROR-level line on every player death (`Fail()` is `LOG_ERROR` in release builds, `P:Foundation/Framework/DebugLog.hpp#L58`, `#L67`), which is fatal under `--strict`; no entry means BIRD in MP, and an out-of-range value means NONE [V `P:Network/NetworkServerMission.cpp#L341-L359`] |
| Unit | Loadout (catalog picker, magazine compatibility checked); behaviour preset (posture, alertness, fleeing, hold fire); pose; character (cast entry); captive | Generated prefix of the init field; `class CfgIdentities` | Magazines before weapons; moves listed from the unit's `Moves >> States` [V `P:World/Entities/Infantry/SoldierOldMove.cpp#L364-L411`] |
| Vehicle, crate | Cargo contents, refill period, lock | Init prefix; a tiny refill script | `clearWeaponCargo`/`addWeaponCargo`/`addMagazineCargo` [V `GSE#L1023`, `#L1332-L1333`] |
| Map object (by id) | Destroyed at start, objective target | `object <id>` references (`GSE#L1142`) [V] | Picked by clicking, never typed |
| Marker | Follows a unit; revealed when a rule fires | Tracking loop or a pool (§4.6 row 17) | Hiding technique on `Cwa199` [U, probe] |
| Trigger / waypoint Effects | Camera preset, sound, music, title | Stock Effects fields | Enum values come from pickers only: the script setters store unknown enum strings as −1, which probably crashes when the trigger fires [I from `P:Game/Commands/GameStateExtWorldWaypoint.cpp#L569-L644`]. Effects titles go to the title layer and Effects apply only on the machine whose player matches the Effects condition [V `Detector.cpp#L1392-L1509`; `P:AI/AIArcade.cpp#L794-L806`] |
| Objective | Autosave on completion | `saveGame` in the completing activation [V `GSE#L881`] | |
| Group | Patrol route drawing tool (loop, random order, radius) | Native waypoints with CYCLE | Random order needs rung 2 |

**Map badges.** Presence probability, condition of presence and placement radius (stock fields, doc 03 §4.4) are drawn
as percentage badges and radius rings, so randomisation is visible without opening a dialog [I].

**Where generated init code lives [I].** Map-object code in `mission.sqm` fields cannot carry `//` comments (the evaluator
has no comment syntax outside `preprocessFile`) [V `EVAL:express.cpp#L131-L137`]. The attribute layer therefore writes
a generated prefix into the field and records its span and hash in the sidecar; any hand-written text after the prefix is
user code and is never touched. Unit init fields run before `init.sqs`, so they must not call generated functions
(§7.3) [V `P:World/WorldInit.cpp#L622-L632`]. A script `exec`'d from an init field also gets its first step (up to 100
lines) before the first line of `init.sqs`, because `RunInitScript` adds `init.sqs` to the script list and then steps
every script once [V `P:UI/DisplayUI.cpp#L121-L129`; `P:World/WorldSetup.cpp#L1394-L1407`].

## 4. Rung 2: modules

### 4.1 What a module is

A module is a typed, versioned definition (parameter schema, map footprint, singleton needs, profile requirements,
lowering templates) plus placed instances. Placing one is a single undoable command; the form and its map handles are
its whole interface. The concept follows Eden modules and Reforger's Scenario Framework (attributes plus links, event
action lists), minus their two weaknesses: module code lived in addons and ran with no guaranteed initialisation order
[V: ACE3 framework docs "no guarantee when a module initializes"]. Ours emit mission-local code with one ordered init.

**Drop in, then refine [I].** Long forms are the usual failure of form-driven editors, so every module follows five rules:

- **It works when dropped.** Code fills every required slot with a context default (the nearest suitable group, the
  player's side, the nearest road or building) and shows each default as an editable chip. A freshly placed module
  passes every lint or says in one line what it still needs.
- **Short form first.** At most five basic fields; everything else sits under an "Advanced" fold. Each module ships named
  presets (for fire support, for example: mortar section, heavy battery, one air-strike pass), and "Shuffle" re-rolls its
  randomisable parameters for variety.
- **One-sentence summary.** Parameters render as a plain sentence ("When radio Alpha is called, 6 rounds of 81 mm fall
  within 50 m of the clicked point after 20 s; 3 uses"). It appears in the map tooltip and the "why" card, and it is
  what a model reads back to check intent.
- **Found by intent.** The palette searches plain goals ("artillery on call", "reinforcements arrive") and lists
  modules, presets and rule templates together.
- **Composed, not detached.** Each module exposes typed output events (arrived, rounds complete, freed) and input verbs
  (start, stop, reset) to the rule builder (§5.2). A missing option is usually one rule away, so "Detach to script" is
  the last resort, not the first.

"Module" here means a **mission** module. Doc 26 §5.2 uses "persistence module" for campaign-level bundles; the two share
the parameter vocabulary but live in different editors (open question 9).

### 4.2 Type sketch (crate `ofp-modules`; proposal-only)

```rust
/// Placed-instance id. Newtype per AGENTS.md (from_raw/to_raw, Display "mod#7"); add to the CODE-INDEX newtype table.
pub struct ModuleInstanceId(u32);
/// Definition key: "ofpe.fire_support" (first party) or "<pack>.<name>" (T0 pack).
pub struct ModuleDefKey(Box<str>);

pub struct ModuleDef {
    key: ModuleDefKey,
    version: SemVer,                 // instances pin it; upgrades show an output diff
    params: Vec<ParamSpec>,          // ordered form fields
    footprint: FootprintSpec,        // icon, areas, rings, routes, link kinds
    needs: Vec<SingletonNeed>,       // requested from the compiler, never taken directly
    locality: Locality,              // Server | Everywhere | Owner
    requires: ProfileReq,            // computed from emitted commands (doc 24 §5.5), never hand-declared
    lowering: BTreeMap<ProfileSet, TemplateRef>, // per-profile templates (minijinja, §4.8)
}

/// Closed parameter vocabulary (compare ZEN's ~10 control kinds). Every kind renders as a picker or a bounded editor.
pub enum ParamType {
    Unit, Group, Vehicle, MapObject, Marker, Area, Position, Route, Side, Bool,
    Int { min: i32, max: i32 }, Real { min: f32, max: f32, step: f32 }, Duration { min_s: f32, max_s: f32 },
    Enum(Vec<EnumCase>), LocalText { max_chars: u16 }, Class { root: CfgRoot }, // CfgVehicles, CfgAmmo, CfgMusic…
    RadioSlot, Condition,            // Condition = the §5.2 AST, edited with the rule builder
    Expression { mode: CheckMode },  // escape slot, checked with doc 23 check modes
    List { item: Box<ParamType>, max: u16 },
}

pub enum SingletonNeed {
    MapClick { priority: u8, consumes: bool }, RadioSlot, Action, RespawnHook(HookKind),
    CameraScriptSlot, ServerGuard, InitAfter(Vec<ModuleDefKey>),
}

pub enum Emit { // what lowering may produce; every variant is re-parsed and linted
    Trigger(TriggerSpec), Waypoint(WaypointSpec), Marker(MarkerSpec), GameLogic(LogicSpec),
    InitPrefix { entity: EntityRef, code: String }, Script { path: ScriptPath, text: String },
    ExtEntry(ExtPatch), BriefingSection(BriefingPatch), StringRow(StringRow), HookBody { hook: HookKind, code: String },
}

pub struct ModuleInstance {
    id: ModuleInstanceId, def: (ModuleDefKey, SemVer),
    params: BTreeMap<ParamKey, ParamValue>, links: Vec<Link>,
    origin: Origin,                  // User | Agent{run, step, model} | Lifted{recogniser, confidence}
    pinned: bool, regions: Vec<RegionRecord>, // §8.3 state machine
}
```

### 4.3 Map presence and synchronisation

- **Footprint.** Every instance draws its effect: range rings and dispersion ellipses (fire support), LZ circles and
  flight lines (air transport), respawn areas, patrol routes, convoy order numbers, garrison slots, alert-network links.
  Footprints are also handles: dragging a ring, an ellipse or a route point edits the parameter it draws, as one undo
  step, so most tuning never opens the form [I].
- **Links** are drawn like sync lines (dashed) from the module to the entities it uses, and are edited by dragging, as in
  Eden. A module can be "activated by" a rule or a trigger, like Eden's `isTriggerActivated` [V BIKI Modules page].
- **Init order** is one generated, dependency-ordered section at the top of `init.sqs`, before any `~` or `@` line: the
  engine starts `init.sqs`, runs it until its first wait, and only then executes `init.sqf` [V
  `P:World/WorldInit.cpp#L622-L632`; `P:UI/DisplayUI.cpp#L121-L145`]. `init.sqs` runs with no per-step line cap
  (`INT_MAX`), so the 100-line budget applies to `exec`'d scripts only; `init.sqf` is read raw (no preprocessor) and
  executed unscheduled, and its existence on 1.99 is (unverified) [I: the code comment reads like a CWR addition].

### 4.4 What a module compiles to (native first)

| Need | Preferred lowering | Fallback |
| --- | --- | --- |
| "Group X moves when condition C" | Trigger with condition C synced to X's held waypoint (no code) [V doc 03 §4.6-§4.7] | SQS `move`/`doMove` |
| Presentation (music, title, camera preset, sound) | Trigger or waypoint Effects fields | Timeline script |
| Area/side/radio activation | Trigger activation fields | SQS polling |
| Mission end | END/LOSE trigger type whose condition reads a compiler flag; scripts end the mission by setting that flag | None. `forceEnd` sets no ending: it only lets an END that already fired pass a blocking title or camera effect [V `P:Game/Commands/GameStateExtWorld.cpp#L781-L785`; `P:World/World.hpp#L445`; `P:UI/DisplayUIMenus.cpp#L984-L985`]. No `endMission` command is registered, and `endGame` (3.05 only, `GSE#L886`) closes the application [V `GameStateExtWorld.cpp#L787-L803`] |
| Sequenced actions | — | One namespaced SQS file per instance, `exec`'d from an activation |
| Configuration | `description.ext` via the CST patcher | — |

Generated files live under a per-instance name such as `ofpe\<tag>_fs1.sqs`: literal, mission-relative, with no `..` or
`:` (doc 24 L2). Every global a module creates carries the instance prefix (the OFPEC tag convention, done by the
compiler). The prefix and file name include a slug of the instance's user label where one exists (`ofpe\fs_north_battery.sqs`
rather than only `fs1`), so ejected code and Preview error lines stay readable [I].

### 4.5 Compiler-owned singletons

| Singleton | Engine fact | What the compiler does [I] |
| --- | --- | --- |
| Map clicks | `onMapSingleClick` stores **one** global code string; the handler sees `_pos`, `_units`, `_shift`, `_alt` and returns a Bool, where `true` suppresses the default move order [V `GSE#L1131`; `P:UI/Map/UIMapMain.cpp#L2139-L2173`]. `_pos` is `[x, z, height above surface]`; `_units` holds the selected units only when the player leads the group, else it is empty; `_shift`/`_alt` read only the left-hand keys; a non-Bool result counts as false, so the move order is issued [V same lines; `EVAL:express.cpp#L2784-L2793`] | One generated dispatcher. Modules register consumers with a priority, auto-removal (after N clicks, a time or a condition) and an explicit "consume click" flag |
| Radio | 10 slots, Alpha–Juliet, as trigger activation [V doc 03 §4.7]; `setRadioMsg` labels [V `GSE#L1278`]; hiding with `"NULL"` works in CWR, [U] on 1.99 (doc 19 §7.2) | Allocator; a conflict is a compile error listing the owners |
| Actions | `addAction` accepts exactly `[title, script]` (any other size is an error) and returns an id; no condition, distance, argument or priority parameter even in 3.05 [V `P:Game/Commands/GameStateExtGrp.cpp#L1413-L1438`]. The second element is a script **file**, started as a normal script with `_this = [object, caller, id]`; a null or non-entity object returns −1 [V `P:AI/VehicleAIPilot.cpp#L1064-L1073`; `GameStateExtGrp.cpp#L1415-L1419`] | Generated handler implements who, distance, one-shot and arguments; ids kept in namespaced globals |
| Respawn and death hooks | `onPlayerKilled.sqs` runs only with respawn NONE and disables the end dialog; `onPlayerRespawn.sqs` (INSTANT, BASE; 1.99 [U]); `onPlayerRespawnOtherUnit.sqs` (GROUP); `onPlayerRespawnAsSeagull.sqs` (BIRD, and GROUP with nobody left) [V `SoldierOldMove.cpp#L940`, `#L964`, `#L1064-L1200`]. Every hook is gated on `FileExist("scripts\<hook>")`, the **root** path only, before the mission → campaign → root lookup runs, so a mission-local hook runs only if a root copy also exists [V `SoldierOldMove.cpp#L880`, `#L1076`; `P:UI/OptionsUI.cpp#L630-L655`]; whether stock installs ship all four root files is (unverified). In SP the mode is always NONE (`KilledBy` reads the MP respawn mode only in network games) [V `#L1026-L1029`] | One generated file per hook that dispatches to module handlers; a mission that needs a hook the install lacks gets a trigger-based fallback (the row 20 pattern) |
| Camera-script slot | Each hook starts in the engine's single camera-script slot, and `StartCameraScript` itself first terminates whatever script holds it, so this holds for `onPlayerKilled.sqs` too [V `SoldierOldMove.cpp#L874-L891`; `P:World/WorldSetup.cpp#L1414-L1428`]. `exec` never uses the slot [V `P:Game/Scripting/Scripts.cpp#L574-L580`] | Only the spectator/death-sequence module may use the slot; cutscenes never rely on it |
| Server guard | `isServer` is false in single player and on clients: it returns `NetworkManager::IsServer()`, which is `_server != nullptr` [V `P:Game/Commands/GameStateExtWorldConfig.cpp#L890-L893`; `P:Network/NetworkImpl.hpp#L34`; Faguss pdf p.2] | A compiler-owned Game Logic; server-only code is guarded with `local <logic>`, the OFP-era idiom. Static reading supports SP: vehicles start with `_local = true` and `local` returns it [V `P:World/Simulation/Simul.cpp#L363`; `P:World/Entities/Vehicles/Vehicle.hpp#L346`]; runtime confirmation stays probe AT8 |
| Globals | Unit names from `mission.sqm` become read-only globals; assigning one is a runtime error the check mode misses [V `P:AI/AICenterImpl.cpp#L1016-L1017`] | Namespaced handles; never reassign an editor name |
| Group budget | 12 units per group [V `P:AI/Path/AITypes.hpp#L31`]; groups per side from config (63 in vanilla, doc 09 P7) | Live budget meter in every spawning module |

**Hand-written singleton use [I].** A mission often already sets `onMapSingleClick`, ships its own hook files or owns radio
triggers, and the compiler never overwrites them (N5). An existing hook file keeps its text; the compiler adds one fenced
dispatch line to it. An existing radio trigger keeps its slot, and the allocator works around it. A hand-written
`onMapSingleClick` assignment and the dispatcher would replace each other at runtime, so the pair is a compile error that
names the modules affected. Its one-click fix, previewed as a diff, turns the assignment into a registered consumer and
keeps the handler body verbatim.

### 4.6 First-party module catalogue (wave 1)

Each row names the commands it needs. All of them are registered in 3.05 and CE (`GSE` lines given); `Cwa199` availability
comes from the doc 23 catalog, and rows that need a probe say so.

| # | Module | Key parameters | Lowering on `Cwa199` | Extra on `Cwr`/`Ce` | Grounding |
| --- | --- | --- | --- | --- | --- |
| 1 | Objective | title, text, marker link, done-when and fail-when conditions, hidden at start, autosave | `OBJ_n` briefing section with `marker:` link, `objStatus` in activations, optional `saveGame` | `$STR_` tokens in HTML | [V] `GSE#L1321`, `#L881`; doc 04 §6 |
| 2 | End state | ending (END1–6, LOSE), debrief text, outro, condition | END/LOSE trigger (condition = compiler flag); `forceEnd` only as the unblocker for a live title or camera effect (§4.4); `Debriefing:EndN` section | — | [V] `P:AI/Path/ArcadeWaypoint.hpp#L249-L255`; in campaign-managed missions it becomes a doc 19 outcome (lint C13) |
| 3 | Reinforcements | groups, release condition, route, arrival behaviour | Pre-placed group whose first waypoint is held by a synced trigger | Optional spawn with `createGroup` + `createUnit` | [V] sync semantics (doc 03 §4.7); `GSE#L1182`, `#L1336` |
| 4 | Fire support (artillery, mortar, air strike, CAS) | round classes from CfgAmmo, rounds, delay, dispersion, call method (radio slot, action, map click), who may call, uses | Call UI → dispatcher → SQS that spawns rounds at random offsets after a delay | `createShell` | [V] `GSE#L1131`, `#L1208`; how a vanilla script makes a real explosion on 1.99 is [U, probe] |
| 5 | Air transport | heli group, pickup and drop LZs, call method, wait condition, return | LOAD / TR UNLOAD / GETOUT waypoints plus sync; helper SQS with `land`, `flyInHeight` | — | [V] waypoint types (doc 03 §4.6); `GSE#L1246`, `#L1264`; reliability with a player-led group [I] |
| 6 | Respawn point | side, unit or group; point or area; restore loadout | `respawn_<side>`-prefixed markers with collision-safe suffixes; loadout restore in the hook | `onPlayerRespawn.sqs` for INSTANT/BASE | [V] prefix match with random pick, then `respawn_<unit>`, `respawn_<leader>`, side markers, then any `respawn*` marker (so a side without its own marker can land on another side's) [V `SoldierOldMove.cpp#L723-L803`] → lint. Every step is a case-insensitive **prefix** match, so a unit named `w` matches `respawn_west…` markers; the resistance marker is spelled `respawn_guerrila`; with no marker at all, BASE respawns in place [V same lines; `#L1136-L1174`] |
| 7 | Spawn zone / ambient population | composition, side (incl. civilians), activation, cap, respawn budget | Pre-placed dormant groups moved in and given waypoints | `createGroup`, `createUnit`, `addWaypoint` | [V] `GSE#L1182`, `#L1419`; civilians consume group slots [V BIKI FAQ]; ambient-civilian demand [U] |
| 8 | Patrol area | group, area or route, loop or random, pace, reaction | CYCLE waypoints with placement radius; random order via an SQS `move` loop | `addWaypoint` | [V] `ArcadeWaypoint.hpp#L71`; runtime cycle waypoints were not possible in 2002 [V forum] |
| 9 | Convoy | vehicles in order, road route, spacing, speed, ambush reaction | One group in COLUMN, SAFE, LIMITED/NORMAL; for a fixed order, separate groups joined in order | — | [V as 2002 advice; I behaviour]; warns above 12 units |
| 10 | Random choice | N candidates (positions, objects, objective sites), weights | Server picks with `random` and publishes with `publicVariable`; `setPos` or presence | — | [V] `EVAL:express.cpp#L1166`, `GSE#L1042`; the engine RNG is not seedable (doc 19 §5.3). Publish a scalar index, not a position array: which value types 1.99 `publicVariable` carries is (unverified), and 3.05 registers separate `publicVariableArray`/`publicVariableString` names [V `GSE#L1044-L1045`] |
| 11 | Interaction | object, label, who, distance, one-shot, effect (rule actions) | `addAction` + generated filtering handler + `removeAction` | — | [V] arity above; the action runs on the machine where it is used [I] |
| 12 | Intel pickup | object, objective, markers revealed, hint | Interaction + Objective composition | — | [I] |
| 13 | Hostage | hostages, captors, rescue condition, extraction point | `setCaptive`, pose via `switchMove`, `join` on rescue, objective link | — | [V] `GSE#L1220`, `#L1277`, `#L1296` |
| 14 | Garrison | building (picked on the map), units, positions | `setPos` to `buildingPos` slots, or waypoint `housePos`; GUARD waypoint | — | [V] `GSE#L1230`; slot count per building from model data [U] |
| 15 | Time and weather director | keyframes: skip time, overcast, fog, rain | `skipTime`; **one gradual weather change at a time**: `setOvercast` re-targets fog to its current value and `setFog` does the same to overcast, so issuing both in sequence cancels the first one's pending transition. The director serialises them (change, wait, change) or makes the earlier one instant (`0 setOvercast x`). Rain only after overcast > ~0.67, because the engine forces rain to 0 below that and then drifts it randomly | `setDate` | [V] `P:World/WorldSetup.cpp#L1285-L1315`; `P:Game/Commands/GameStateExtUi.cpp#L1807-L1823`; `P:World/Terrain/Landscape.cpp#L459-L465`, `#L558-L652` (CE `Landscape.cpp` differs but keeps `maxRain` at L563) |
| 16 | Effect | preset (smoke, fire, wreck burn, dust, flare), duration, intensity | Bounded `drop` loop, always the 19-element form | — | [V] `GSE#L1124`; `P:Graphics/Rendering/Effects/Smokes.cpp#L2309-L2312` |
| 17 | Tracking marker | marker, unit, interval, reveal condition | `setMarkerPos` loop with `~`; pre-placed marker pool | `createMarker` | [V] `GSE#L1247`, `#L1185`; hiding technique [U] |
| 18 | Save point | condition or objective | `saveGame` | — | [V]; Preview deletes saves (doc 09 §2) |
| 19 | Conversation | cast, lines (speaker, text, channel, audio), pacing | CfgSounds/CfgRadio classes; SQS with `say`/`sideRadio`/`sideChat` and waits from durations measured at import | waits from `soundLength` | [V] `P:Audio/DynSound.cpp#L125-L157`, `P:AI/AIRadio.cpp#L1429-L1442`, `GSE#L1011`. `say` subtitles show only if the CfgSounds class sets `forceTitles` or the player enabled titles, and only near the camera; a `say` on a unit that is already speaking waits for it, so fixed waits can drift [V `DynSound.cpp#L132-L155`, `#L202-L234`, `#L281-L299`]. `soundLength` returns 0 without a sound system (e.g. `--nosound`) [V `GameStateExtUi.cpp#L952-L963`] |
| 20 | Spectator / death sequence | allowed sides or units, views | NONE: mission-local `onPlayerKilled.sqs` that re-enables the end dialog; GROUP/BIRD: `onPlayerRespawnAsSeagull.sqs`; INSTANT/BASE: a repeating `!alive player` trigger (the Faguss pattern) | — | [V] `SoldierOldMove.cpp#L1068-L1086`; lookup is mission → campaign → root (`P:UI/OptionsUI.cpp#L630-L655`; CE `#L636-L661`), but the hook starts only if the root `scripts\onPlayerKilled.sqs` exists [V `#L1076`], so the mission copy overrides only when the install ships a root copy (unverified; probe) |

**Wave 2:** alert network, minefield, vehicle respawn (the replacement cannot take the editor name: names are read-only
and `setVehicleVarName` is not registered [V grep], so references go through the module's handle), revive, air drop,
demolition, multi-group command, timer, live camera (follow, helmet and projectile views; row 41 of §2), MP game-mode
templates. **Not first party:** CTI frameworks (doc 29 territory) and
anything that needs an addon, such as CoC Unified Artillery (a 43.3 MB addon package, not a script) [V OFP.info].

### 4.7 Dependencies, versioning and profile badges

- `requires` is **computed** from the emitted commands against the catalog (doc 24 §5.5). A module whose `Cwa199`
  template exists is available everywhere; one without it is greyed out on `Cwa199` with the missing commands named.
- A module never adds to `addOns[]`. A class parameter drawn from an addon marks the mission's addon dependency through
  doc 27 §4.5, visibly.
- Instances pin a definition version. Upgrading shows the output diff first; lowering is deterministic for (definition
  version, parameters, profile), so golden tests can pin it.

### 4.8 Community modules as content packs

Community modules ship as **T0 data** (doc 22 §2.1): a parameter schema in the §4.2 vocabulary plus minijinja templates
(fuel limit, no file loader) [V doc 22]. Rules [I]:

1. Parameters are validated against the schema before rendering (the doc 17 §6.1 order); values reach templates only
   through pure per-format escaping filters (SQS string, SQF string, sqm string, `description.ext` string, briefing HTML,
   stringtable CSV). Our own template markers found in mission text are escaped, never expanded (doc 21 §9.3).
2. Rendered output is re-parsed with the lossless parsers and checked with the doc 23 checker and the doc 24 L1–L11 rules.
   A `deny` finding refuses the instance. `template-only` commands (`saveVar`, pool commands, `CfgRemoteExec`) are
   never allowed in pack output (doc 24 §5.3).
3. Packs request singletons through `needs`; they cannot write `onMapSingleClick`, hook files or radio triggers directly
   (a lint flags such text in pack output).
4. The instance shows a "community" badge with author, version and licence. Recognisers (§8) are data too and contain no
   code from the pack they recognise.

This lets community favourites (the eight artillery variants, spawn managers, Group Link) return as forms without
reintroducing their hacks.

## 5. Rung 3: the rule builder

### 5.1 Shape

A rule is a sentence: **WHEN** *event* **IF** *condition groups* **THEN** *actions*, with a mode (Once, Repeat, While true
with an "on end" branch, At start) and a declared locality. Every slot is a clickable typed picker, as in the Warcraft III
and StarCraft II editors and the community Better Triggers tool [V prior art]. Conditions use explicit **ALL of / ANY of**
containers, because flat condition lists with an OR flag bind in surprising ways (the Creation Kit evaluates `A AND B OR C
AND D` as `A AND (B OR C) AND D`) [V search summary].

**One condition language.** The condition AST is doc 19's CXL, extended with mission references: `unit.x`, `group.g`,
`marker.m`, `area.a`, `rule.r.fired`, `obj.n`, plus the functions below. The same projectional builder edits both, the
same pretty-printer keeps a canonical text form for diffs and models, and the doc 19 §5.4 lowering table extends to the
new atoms [I].

```rust
pub struct Rule { id: RuleId, when: EventSpec, guard: Option<CondAst>, then: Vec<ActionSpec>,
                  mode: RuleMode, locality: Locality, owner: Option<ModuleInstanceId> }
pub enum RuleMode { Once, Repeat, WhileTrue { on_end: Vec<ActionSpec> }, AtStart }
```

### 5.2 Vocabulary grounded in the engine

| Event or condition | Engine grounding | Lowers to | Profile |
| --- | --- | --- | --- |
| Side/anybody present or not present in an area; detected by a side | Trigger activation and presence fields [V doc 03 §4.7] | Trigger | all |
| Radio call Alpha–Juliet | Trigger activation [V] | Trigger via the radio allocator | all |
| Unit or vehicle destroyed; damage above x | `alive`, `getDammage` [V `GSE#L935`, `#L945`] | Trigger condition | all |
| Distance, knows about, in vehicle, group strength | `distance`, `knowsAbout`, `vehicle`, `count units` [V `GSE#L1235`, `#L1265`, `#L972`, `#L979`; unary `count` at `EVAL:express.cpp#L1187` (L1132 is the binary condition form); citation corrected 2026-09-27] | Trigger condition | all |
| Time elapsed; held for N s; after N s | `time` [V `GSE#L859`]; trigger timeout vs countdown (min/mid/max) [V fields; label mapping U, doc 03 §4.7]. The delay is drawn at random, `Gauss(min, mid, max)`, each time the condition turns true; an interruptible timer is cancelled when the condition drops, the other kind fires at expiry without re-checking [V `Detector.cpp#L1267-L1296`, `#L698-L704`] | Trigger timers with min = mid = max unless the rule asks for randomness | all |
| Another rule fired; waypoint reached; objective changed | No `triggerActivated` command [V grep]; waypoint On Activation field; `OBJ_n` globals [V doc 04 §6] | A generated flag set in the source's activation | all |
| Module event: reinforcements arrived, fire mission complete, convoy halted, hostage freed (declared per module, §4.1) | The same flag mechanism, set by the module's own trigger or script [I] | Flag | as the module |
| Unit events: killed, hit, damaged, get in/out, fired, engine, fuel, gear, incoming missile | `addEventHandler` [V `GSE#L1367`; `P:AI/EntityAIType.hpp#L399-L415`]; `AnimChanged` 1.99+ [V pdf] | EH in the ordered init, setting a flag or running an action script | all (`AnimChanged` not before 1.99) |
| Map click, action chosen | Dispatcher, Interaction module | Consumer registration | all |
| Player connected (MP) | `onPlayerConnected` [V `GSE#L1040`; wiki tag `ofpe`, doc 23 §4] | Handler | `Cwr`/`Ce` |

**Actions** (each a typed form): release a held group or order a move; set an objective; end the mission; play music;
show a title (cut layer by default, so it lowers to SQS, not to Effects; §5.3 step 3); play a conversation or a cutscene; set, clear or count a flag; enable or disable a
rule; reveal or move a marker; activate a spawn zone; call a support module or any module's input verb (start, stop,
reset); skip time or change weather; damage, destroy or repair; give or remove gear; join a group; make captive; save the
game; hint; **for each** unit of a group, of the units in an area, or of a picked list, apply nested actions (lowered with
`forEach`, which takes its body as a code string in the 3.05 evaluator [V `EVAL:express.cpp#L1133`]; `Cwa199` availability
from the doc 23 catalog); and "run script" (the Expression escape, doc 23 `CheckExecute`). Common sentences ship as
**rule templates** with the slots left open ("WHEN *side* enters *area* THEN release *group*"), which newcomers and weak
models fill instead of composing from scratch (§9).

### 5.3 How rules compile

1. **Single trigger when possible.** Area, radio and detected-by events with a pure condition become one trigger:
   activation fields, `expCond` built as `this && (…)` or a plain expression, statements in On Activation. Mode Once or
   Repeat maps to the repeat field; While-true uses On Deactivation for its end branch, which the engine runs **only on
   repeating triggers**, so While-true always emits a repeating trigger [V `Detector.cpp#L1280-L1288`, `#L1512-L1515`].
   Generated statements never read `this`: On Activation rebinds only `thisList`, On Deactivation rebinds nothing, and
   when the condition text is exactly `this` neither is bound before evaluation, so `this` can hold a value left by
   another trigger [V `Detector.cpp#L1259-L1265`, `#L1331-L1337`].
2. **No-code movement.** "THEN group X moves" becomes a sync from the trigger to X's held waypoint, the OFP idiom the
   community taught first.
3. **Presentation actions** go into the trigger's Effects fields when they fit (one music track, one text title, one
   camera preset); otherwise into the rule's SQS. Effects titles always go to the **title** layer (the same layer as
   `say` subtitles and direct-channel chat lines) [V `Detector.cpp#L1489-L1509`; `P:AI/AIArcade.cpp#L794-L806`], so a fade, a
   `BLACK OUT`, or any title that can still be alive when an END trigger fires is emitted as SQS `cutText`/`cutRsc`
   instead. An Effects camera preset is a live camera effect and blocks the ending the same way (§6.1).
4. **Sequences** (waits, several steps, loops) become one namespaced SQS file `exec`'d from the activation.
5. **Timing is explicit.** Triggers are simulated with a 0.5 s precision and a random initial phase [V static reading,
   `P:World/Detection/Detector.cpp#L42-L46`, `#L696-L707`], so latency is up to about 0.5 s and firing order between
   triggers is not deterministic. A rule that depends on another reads the other's flag; the builder shows a latency and
   cost badge. Trigger timers are random between min and max (§5.2), so "after N s" sets min = mid = max. SQS `@` waits
   are re-evaluated on every script step, which appears costlier than a trigger [I].
6. **Parity checks.** Conditions are checked in `CheckEvaluateBool` mode, because a non-Bool condition counts as false
   silently at runtime [V `EVAL:express.cpp#L2773-L2782`]; text literals never contain `:` where they reach an SQS `?`
   line (doc 19 F6).
7. **Profiles.** Runtime triggers (`createTrigger`, `setTriggerStatements`) are `Cwr`/`Ce` additions [V registered at
   `GSE#L1191`, `#L1405`; 1.99 absence per wiki tags, doc 23 §4, unverified on an install]; rules are static, so
   `Cwa199` pre-places every trigger and loses nothing.

### 5.4 Debugging and visualisation

- **On the map:** area outlines, arrows from each rule to the entities it changes, and flag-flow arrows between rules. By
  default only the selection and its direct neighbours draw arrows; the full graph is a toggle, so a large mission does
  not turn the map into spaghetti [I]. A cross-reference panel lists, for every flag, who sets it and who reads it.
- **"Try it" on `Cwr`/`Ce` [I]:** from a rule, a module or a cutscene, start Preview with that element forced (run a rule's
  actions now, call this fire mission, play from shot 3) instead of replaying the mission up to it. The forced call is
  generated, checked code sent through the harness, so it waits for the non-aborting launch of §7.4. Short test loops are
  most of what makes building fun.
- **In Preview on `Cwr`/`Ce`:** a fire log from stage-only `logInfo` logpoints [V `GSE#L1062`], and "why didn't this
  fire?" evaluating each clause through the harness `eval` (read-only clauses only). A runtime error inside an `eval`
  ends a `--test-mission` session, so this needs the non-aborting launch of §7.4.
- **On 1.99:** a debug export variant with `hint` tracepoints, never part of normal export.

### 5.5 Avoiding spaghetti

Rules belong to a module or a named folder; the rule list groups by folder and by the entity they touch. Lints: rule
cycles with no state change; write-only and never-written flags; two rules writing one flag in the same instant;
constant conditions; unused radio slots; a rule touching more than N entities (suggest "Extract to module", which turns
a rule set plus its entities into a reusable module definition). Visual rungs stay domain-specific: no general node-graph
language, the lesson of Blueprint's per-node cost and binary diffs [V Epic docs].

## 6. Rung 4: the cinematics timeline

### 6.1 What the engine allows (both 3.05 and CE; cinematic files byte-identical at the pins [V])

Re-hashed 2026-09-27: `CameraHold.{cpp,hpp}`, `CamEffects.{cpp,hpp}`, `TitEffects.cpp`, `GameStateExtUi.cpp`,
`WorldSetup.cpp`, `DisplayUIMenus.cpp`, `Scripts.{cpp,hpp}`, `Detector.cpp`, `DynSound.cpp` and `SoldierOldMove.cpp` are
byte-identical in CE. `World.cpp` and `GameStateExtTestAudio.cpp` differ, so their CE lines are given separately [V].

| Area | Fact | Consequence |
| --- | --- | --- |
| Motion | `camCommit t` moves in a straight line at constant speed; look-at direction and distance and the FOV interpolate linearly; `t <= 0` applies at once [V `P:World/Scene/Camera/CameraHold.cpp#L288-L324`] | Curves and easing are sampled into short segments |
| Completion | `camCommitted` is true only after the **latest** deadline of all commits [V `CameraHold.cpp#L582-L597`] | Never start a segment before the previous deadline |
| Aim | A new target interpolates from the previously committed target, not from the aim on screen [V `#L567-L574`; jump I] | Let each segment finish before re-targeting |
| Relative position | `camSetRelPos [x, fwd, up]` is converted to an absolute point once, when called, against the target of the latest `camSetTarget` even if not yet committed, in that object's heading frame with up forced vertical (a position target just adds the offset) [V `GameStateExtUi.cpp#L1487-L1504`; `CameraHold.cpp#L81-L92`; `CameraHold.hpp#L69`] | Follow shots are chains of short commits; `camSetTarget` always precedes `camSetRelPos` |
| Orientation | `camSetDive`, `camSetBank`, `camSetDir` all bind to the `CamSetDive` handler, and commit never reads dive, bank or heading [V `GSE#L1348-L1350`; `CameraHold.cpp#L557-L591`] | No roll or free pitch channel; pitch comes from where the look-at point is |
| FOV | `camSetFovRange` is an empty stub [V `GameStateExtUi.cpp#L1517-L1520`]; `camSetFov` fixes the lens per commit by setting min = max. The engine's distance-based auto-zoom (`fov = 10 / distance`, clamped to [min, max]) therefore stays unreachable, and a new camera starts at 0.7 [V `CameraHold.cpp#L116-L135`, `#L251-L276`; `CameraHold.hpp#L59-L64`]. The FOV "set" flag is never cleared, so every later commit re-times a still-running zoom to its own duration [V `CameraHold.cpp#L575-L580`] | "Keep the subject framed" is computed at authoring time; `camSetFov` is emitted in every segment |
| Height | The rendered camera is clamped to 0.1 m above terrain or sea [V `P:World/World.cpp#L1208-L1221`; CE `#L1246-L1259`]; `triSetView` is applied after the clamp [V 3.05 `#L1218-L1221`] | Refuse keys below the surface |
| Streaming | No preload command in 3.05 or CE [V grep] | Lint far cuts without a lead-in |
| Effect switch | `cameraEffect` needs one of 14 position names, even for `"terminate"`, or it silently does nothing; an unknown effect name probably crashes (`FindCameraEffect` result is dereferenced after a `DoAssert`) [V/I `GameStateExtUi.cpp#L1369-L1413`; `CamEffects.cpp#L34-L48`, `#L653-L659`] | Both strings come from pickers |
| Lifetime | On a camera object (and in intro mode) the effect never times out; `camDestroy` does not end it, because the internal effect auto-terminates on a lost object only for a camera in manual mode [V `GameStateExtUi.cpp#L1406`; `CamEffects.cpp#L266-L297`; `CameraHold.hpp#L128`] | Always terminate before destroying |
| Overlays | Cut layer below, title layer on top [V `P:World/World.cpp#L1646-L1652` (3.05)]; `say` subtitles, trigger and waypoint Effects titles and direct-channel chat lines all use the title layer [V `DynSound.cpp#L297`; `Detector.cpp#L1489-L1509`; `P:AI/AIArcade.cpp#L794-L806`; `P:Game/Chat.cpp#L155-L161`]; a live **title-layer** effect or camera effect blocks the mission end unless it is forced; `BLACK OUT` holds for 1e20 s [V `P:UI/DisplayUIMenus.cpp#L984-L995`; `P:Game/TitEffects.cpp#L476-L488`] | Fades default to the cut track |
| Title quirks | `titleRsc`/`cutRsc` and `titleObj`/`cutObj` ignore speed, and `fadeOut` overwrites `fadeIn`; `titleObj` reads only global CfgTitles; an unknown effect-type string (`"PLAIN DOWNN"`) makes the command a silent no-op [V `TitEffects.cpp#L570-L625`; `GameStateExtUi.cpp#L1690-L1755`] | Lint and picker limits |
| Audio | In intro mode group and vehicle radio are inaudible; outside MP all radio needs a living player [V `P:World/WorldSetup.cpp#L878-L932`] | Cutscene dialogue uses `say` |
| Input and border | `disableUserInput` is an unclamped nesting counter; `showCinemaBorder` is reset to true at every mission or cutscene display [V `WorldSetup.cpp#L1342-L1356`; `DisplayUIMenus.cpp#L827`, `#L1177`] | Balanced pairs; border set explicitly |
| Sections | Intro, OutroWin, OutroLoose run in intro mode; Space or Esc skips; `initintro.sqs` runs for intros, never outros; a section with no groups is skipped [V `DisplayUIMenus.cpp#L1173-L1450`]. A section display exits as soon as the end mode leaves "continue", with no effect-blocking check (that check exists only in the mission display), so an intro ends through an END trigger or a skip; outros do not run `DisplayIntro::Init`, so they neither create the main map nor load campaign variables [V `#L1202-L1206`, `#L1294-L1329`, `#L1331-L1374`] | Outros start from a condition-true trigger; the Map track is greyed in outros (unverified whether the mission's map survives) |

### 6.2 Timeline model

Tracks: **Shots** (camera keys drawn on the 2D map: position absolute or relative to an actor, look-at point or unit,
FOV, duration, cut or move, easing), **Titles** (cut track by default; text track above it), **Music**, **Dialogue**
(screenplay lines from the Conversation module), **Actors** (moves from the unit's `Moves >> States`, orders, and
"freeze" as zero velocity plus captive, restored afterwards, the Flashpoint Cutscene Maker pattern [V FCM manual]),
**World** (time, weather, effects) and **Map** (`mapAnimAdd`, which works in intros because the intro display creates
the main map [V `DisplayUIMenus.cpp#L1294-L1308`]; outros skip that step, so the map in an outro is (unverified), §6.1
Sections). A cutscene targets a section (Intro, an Outro, or in-mission,
started by a rule). This is a summary: doc 32 §3.2 splits titles into separate cut-layer and title-layer tracks, adds a
Sound track, and treats the map pan as a template gated on a probe rather than a track.

### 6.3 Compile contract (every cutscene)

1. Prologue: an optional `disableUserInput true` (in-mission only; off by default, doc 32 §3.2), an explicit
   `showCinemaBorder`, `camCreate` of a `camera`-simulation class, `cameraEffect ["internal","back"]`.
2. Per segment: `camSetTarget`, then `camSetPos` or `camSetRelPos`, then `camSetFov`, then `camCommit dt` and
   `@camCommitted` or `~dt`. Never `camSetDir`, `camSetBank`, `camSetDive` or `camSetFovRange`.
3. Epilogue on every exit path (end, skip, abort): `cameraEffect ["terminate","back"]` issued **through the camera
   object**, not `player` (on a null object the command returns before doing anything [V
   `GameStateExtUi.cpp#L1371-L1375`], and `player` is probably null in a section without a player unit [I]),
   `camDestroy`, one `disableUserInput false` per `true`, border, radio and music restored; before an ending, no
   title-layer effect remains, or `forceEnd` is emitted. Scripts cannot catch errors (no `try`/`catch` is registered [V
   grep]), so the abort path is doc 32's watchdog
   script, which runs the same epilogue when the driver's done-flag never arrives.
4. Setup blocks between waits stay under the 100-lines-per-step budget of an `exec`'d script, and `~` expressions stay
   well under the 233-byte truncation [V `P:Game/Scripting/Scripts.cpp#L263-L281`; `Scripts.hpp#L53`].
5. In-mission skip: intros get the engine's Space/Esc skip; a vanilla skip for in-mission cutscenes is [U] (open
   question 3).

### 6.4 Shot capture, import and preview

- **Capture from the game.** The engine's free camera (`camCommand "manual on"`) appends a block per Fire press to
  `clipboard.txt`: a `;=== h:mm:ss` header, `camSetTarget` (variable name, a single-quoted debug name, or a position),
  `camSetPos` (or `camSetRelPos` with Left Shift), `camSetFOV`, `camCommit 0`, `@camCommitted _camera` [V
  `CameraHold.cpp#L463-L536`; `P:IO/Streams/QStream.cpp#L361-L376`]. Positions are written as `[x, z, height above
  surface]`, and a relative position only when a target object is locked; the lock itself is taken with the
  toggle-weapons action or keypad `/` [V same lines, `#L414-L449`, `#L504-L517`]. The importer splits on the headers and
  converts the single-quoted debug name, which cannot run, into a map point. `camera.sqs`-style and FCM scripts import through the §8
  recogniser.
- **2D preview** is exact only for the camera path, look-at to fixed points and the per-commit frustum. Moving actors,
  AI, animation and streaming need the game (Unity likewise calls its editor playback "only a simulation") [I; V quote].
- **Live preview on `Cwr`/`Ce`** through the harness (doc 08): *exact* mode evaluates the compiled shot with
  `setAccTime 0` and takes a screenshot; *quick framing* uses `triSetView`, which can show roll and below-surface views a
  compiled shot cannot, so it is labelled an approximation [V `GameStateExtTestAudio.cpp#L972-L999`, registration
  `#L3051-L3166`; CE `#L977-L1004`, `#L3085-L3200`]. `triSetView` takes raw engine order `[px, py(up), pz, dx, dy, dz(, up)]`,
  not the script `[x, z, height]` order, so the preview converts [V same lines]. With `setAccTime 0` game time stands
  still: a `camCommit dt` with `dt > 0` and every `~` wait never finish (motion speed is computed against a frozen clock),
  so exact mode re-expresses each sampled instant as `camCommit 0` [I from `CameraHold.cpp#L288-L324`;
  `Scripts.cpp#L512-L533`]. Never combine `setAccTime 0` with `manual on`: the manual camera divides its frame time by
  `accTime`, which has no lower clamp [V static `CameraHold.cpp#L333`; `P:World/World.hpp#L587`]. **1.99:** no live
  preview; export, play, capture.
- **Presets** with a few knobs, compiled to plain SQS: establishing orbit with a title, flyover along a road, two-shot
  dialogue, briefing-map pan, ending fade.

## 7. Rung 5: the script editor and language service

Doc 23 owns the catalog, the checker and the diagnostics schema; this section adds what makes scripting feel first
class.

### 7.1 Mission-aware symbol index and field contexts

One incremental index of every referable name: units and implicit crew names `<name>d/c/g`, groups, markers, triggers,
waypoints, script files (resolved mission → campaign `scripts\` → root `scripts\`), functions, globals with their set and
read sites, SQS labels (case-insensitive), `description.ext` classes, stringtable keys and campaign `saveVar` names
[V `P:AI/AICenterImpl.cpp#L1638-L1702`; `P:UI/OptionsUI.cpp#L630-L655`]. A reviewed **string-kind overlay** on the
catalog says what each string argument means (marker, script path, class, sound, label, code), which turns most OFP
mistakes into checked references. Each code site knows its context: `this` and `thisList` are read-only globals, bound
fresh in trigger conditions (except when the condition is exactly `this`), `thisList` only on activation, nothing on
deactivation (both then hold stale values), and `this` is the vehicle in init fields; every `then`, loop and `call` body is a child scope; all identifiers are lower-cased [V
`Detector.cpp#L1259-L1337`; `EVAL:express.cpp#L862-L875`, `#L2486-L2547`].

### 7.2 Lints, silent failures first

| Group | Findings |
| --- | --- |
| Silent (no log line) [V `Scripts.cpp#L97-L334`, `#L552-L564`; `DebugLog.hpp#L61`; `EVAL:express.cpp#L93-L129`, `#L2773-L2793`] | SQS `?` line without `:` (dropped; its "Only one field" report goes through `RptF`, a no-op); unknown label (logged at DEBUG only; the script exits); duplicate label (the first one wins, case-insensitive); lines over 4,095 bytes (truncated); non-Bool runtime conditions (the type error is recorded but never displayed, so the condition is silently false and an `@` waits forever); `exec`/`preprocessFile`/`loadFile` target not found (`WarningMessage` reports only the first warning of a severity per session, `SINGLE_WARNING` [V `P:World/Simulation/Animation/FrameFunctions.cpp#L55-L63`]); unknown `titleText`/`cutText` effect-type or `cameraEffect` position string (no-op, §6.1); `preprocessFile` returning "" after a preprocessor error; UTF-8 BOM [I] |
| Late (runtime error, no location) | `:` inside a `?` condition (the line splits at the first `:`, even inside a string, so the error points at a misleading fragment [V `Scripts.cpp#L292-L317`]); a `~` delay over 233 bytes (the fixed buffer drops the closing `)`, so a parse error follows [V `#L263-L281`]); `//` or `/* */` in raw-loaded code (`init.sqf`, `loadFile`, sqm fields); text after a mid-line `;` in SQS; top-level locals in `init.sqf` or init fields [I]; `while` loops that can pass 10,000 iterations [V `EVAL:express.cpp#L788-L798`; the "max iteration" text itself goes to the no-op `RptF`, only a generic error is shown]; assignment to a read-only unit name; `camSetTarget '<debugname>'` pasted from a capture; SQF-scheduler commands `sleep`, `spawn`, `execVM`, `waitUntil`, `isNil`, `compile`, `try`/`catch` pasted from later games (none is registered in 3.05 or CE [V grep]; the checker reports them as unknown) |
| Scope | A local first assigned inside a block and read after it; a function without `private` that overwrites the caller's locals |
| Camera and titles | §6.1 rules: invalid effect or position strings, no-op camera commands, unbalanced input lock, title-layer blackout before an ending |

### 7.3 Editing features

Completion and signature help filtered by the mission's profile (other profiles greyed with a "Requires CWR 3.03+" or
"CE" badge, doc 23 §13.3); hover with signature, availability, doc 24 risk caps and engine quirks; mechanical quick-fixes
previewed as diffs (`private _x = v` → `private ["_x"]; _x = v` for `Cwa199`, top-level locals wrapped in `call {}`,
nested quoted code turned into `{}` blocks, `sleep` moved to SQS `~`); **engine-exact rename** across files, sqm fields,
overlay-typed strings, briefing `marker:` links and campaign `saveVar` names, with collision checks after lower-casing,
as one undoable batch; **map links** (selecting a script draws edges to what it references; literal positions become
draggable ghost pins); **nested-code editing** that shows code inside strings unescaped and re-escapes per nesting level;
**function libraries** as `fn\<TAG>_<name>.sqf` files loaded by `preprocessFile` into tagged globals at the top of
`init.sqs`, since the engine reads no CfgFunctions (no hit for `CfgFunctions` in `engine/`; the only mission-config
function registry read is `CfgRemoteExec` at `P:Network/NetworkServerMission.cpp#L387`) [V grep]. Libraries are
`call`-only: there is no `spawn`/`execVM`/`sleep`, so anything that waits is SQS [V grep]; and clean-room snippets checked per profile in CI (doc 02 §6.2).

### 7.4 Preview debugging on Remastered and CE

- **Error surfacing.** Script errors are one log line, `Script error at '<before>|#|<after>': <text>`, with no file or
  line; the snippet starts at the failing statement of the innermost code string [V `EVAL:express.cpp#L2988-L3011`;
  `P:Game/Scripting/ExpressExt.cpp#L146-L178`]. Parse `--log-format jsonl` (category `Script`), strip the abort suffix,
  split on `|#|`, and map through our source maps. Pin `--lang English` (error texts are localised) and always pass
  `--strict` or `--no-strict` explicitly (the member default is `false`, but the flag's help says it defaults on in
  Debug/RelWithDebInfo builds, so the shipping default is unconfirmed) [V `P:Foundation/Platform/AppConfig.cpp#L569-L573`;
  U]. Under `--strict` every script error and every other ERROR-level log (including the `respawn = SIDE` `Fail()`) ends
  the process [V `ExpressExt.cpp#L166-L171`; `DebugLog.hpp#L58`, `#L67`].
- **Console, watch, logpoints, pause points.** `eval` and `exec` share one persistent, harness-owned local scope
  (`s_evalScope`) at global level, so a running script's locals are invisible [V
  `P:Dev/Harness/HarnessBuiltins.cpp#L73-L111`; CE same lines]. Watches batch read-only expressions at 1–4 Hz; logpoints are
  nonce-tagged `logInfo` lines injected into the stage copy only; SQS pause points are a snapshot line plus an `@` release
  flag, and they pause one script while the world keeps running.
- **Design gap.** Under `--test-mission`, any runtime script error, including one in console or watch text, aborts the
  game with exit code 2 [V static, upgraded from I on 2026-09-27: `--test-mission` sets `AutoTest = true`
  (`BohemiaInteractive/CWR@ffc61838b7:apps/cwr/Game/GameApplication.cpp#L1703-L1718`, same line in CE); harness `eval`
  runs `EvaluateMultiple`, whose `ShowError` calls `DisplayErrorMessage`, which requests close with exit code 2 under
  `AutoTest` (`EVAL:express.cpp#L2768`, `#L2988-L3011`; `ExpressExt.cpp#L146-L165`)]. Doc 08 §4.4 lists the console and
  watch without this caveat. Record it in `docs/design-gap-requests/`; resolve with a non-aborting launch, which must be
  **both** non-`AutoTest` and `--no-strict` (doc 08 P3 `--preview-mission`, or a harness launch without `--test-mission`
  whose playability is [U]).

### 7.5 What is impossible on 1.99

| Feature | `Cwa199` | `Cwr` | `Ce` |
| --- | --- | --- | --- |
| Static checking, lints, rename, map links, snippets | yes | yes | yes |
| One-click Preview, `jsonl` logs, exit codes | no: export and launch (doc 08 §5.3) | yes | yes |
| Console, watch, logpoints, rule fire log, live shot preview | no | yes (harness) | yes |
| `init.sqf`, `logInfo`, `soundLength` | no [I] / [U] / [U] | yes | yes |
| Debug export with `hint` tracepoints; "paste the error text" mapper | yes | yes | yes |

Every unavailable item is greyed out with its reason, never hidden [I].

## 8. Import and lift

### 8.1 Read-only analysis on open

Opening a mission parses every script losslessly (BOMs and line endings kept), classifies files (entry point, `exec`'d,
function, orphan), builds the symbol index and the call and exec graph, computes the Requires badge and runs the doc 24
risk lint and Preview gate. Nothing executes and nothing is rewritten; import followed by save is byte-identical (doc 04
§12.3, doc 19 §7.6).

### 8.2 Recognisers and lifting

| Recogniser | Confidence | Proposal |
| --- | --- | --- |
| Engine camera captures (`;=== h:mm:ss` blocks and the fixed `camSet*` shape) | high: the shape is emitted by the engine | Timeline shots |
| END/LOSE triggers plus `Debriefing:EndN` sections; `OBJ_n` anchors plus `objStatus` calls | high | End state and Objective modules |
| `respawn_*` markers plus the `respawn` key | high | Respawn attributes and points |
| Init idioms: loadouts, cargo fills, `setPos` height lifts | medium | Loadout and cargo attributes |
| Radio trigger → map click → shell loop | low | Fire support |
| Community packs, by file-set and normalised-token fingerprints, header metadata and OFPEC tag prefixes (2–8 letters plus `_`) [V OFPEC tags page] | varies | Pack-specific module |

**Offer, never force [I].** Each candidate shows its evidence and a diff. **Replace** is offered only when re-emitting
the proposed module reproduces the original's normalised tokens; otherwise the offer is **Wrap** (a module facade over
the untouched original files). The original stays until the user deletes it. Community scripts' licences are unknown,
so our modules are clean-room re-implementations and recognisers ship no pack code [U licences; I policy].

### 8.3 Provenance, hand edits and ejecting

- **Provenance syntax per format** [V comment rules]: `; ofp-editor:generated <hash>` in SQS (`;` lines are comments
  there and cost nothing at runtime, because comment lines are never stored [V `Scripts.cpp#L242-L244`]); `//` only in
  `preprocessFile`'d SQF and `description.ext`; `comment "…"` or sidecar-only in raw-loaded code and sqm fields. Fences
  carry a cog-style checksum [V cog docs]. Source maps live in the export-excluded sidecar.
- **Region states:** `Clean` (regenerate freely), `ParamEdited` (a parameter-bound literal changed; flows back into the
  form), `Customized` (other edits; regeneration offers a three-way merge or keep-and-detach), `Detached` (ejected; plain
  code), `Orphaned` (fences damaged; treated as user code). Customized and pinned regions are never overwritten silently.
- **Map edits count too [I].** Triggers, waypoints, markers and logics a module or rule emitted follow the same states.
  Moving an emitted entity whose position is bound to a parameter (a route point, an LZ) is `ParamEdited` and updates the
  form; any other change to an emitted entity (a moved trigger, an edited condition field) makes it `Customized`, and
  regeneration keeps it or offers the merge. Human edits on the map are never lost to a parameter change.
- **Readable output, side by side [I].** Each generated SQS block opens with a one-line plain comment ("; North battery:
  wait 20 s, then drop 6 rounds near the clicked point"). A split view shows the form and its generated lines together;
  focusing a field highlights the lines it produces and updates them live. This is the bridge from forms to script
  (the MakeCode blocks-and-JavaScript pattern in Sources): reading their own generated code is how users of rungs 1–4
  learn rung 5.
- **Eject** turns any module, rule or cutscene into plain script with its provenance kept, and is undoable.

## 9. The AI angle

| Model capability (doc 21 §3.3) | Rungs it may use | Step shape |
| --- | --- | --- |
| Weak local | Pick a module, preset or rule template (§5.2) from a menu of ≤ 7; fill typed slots whose valid values code computed (units, markers, classes, radio slots) | Pick, Fill |
| Mid | Rule sentences composed from slot menus; shot lists from presets; screenplay lines (text only; code wires them) | Fill, Compose |
| Strong, qualified | One CXL condition or an Expression slot, behind the checker and a bounded repair loop | Compose, Draft |

- **Typed tools** (product-scoped, each returning `EditorCommand` proposals shown as a diff and applied as one undo
  group): `module.list`, `module.describe`, `module.propose(def, params)`, `rule.propose(slots)`,
  the rung-4 tools `cine.suggest`, `cine.fill(template_id, slots)` and `screenplay.write` (named as in doc 32 §5.3),
  `script.explain(span)`, `script.fix(diagnostic_id)` (chooses among code-computed fixes), `snippet.fill`,
  `lift.review(candidate)`.
- **Explaining generated code** uses the region's source map: which element, rung, parameters, workflow step and model
  produced each line. Concept explanations come from the doc 33 registry and command facts from the doc 23 catalog;
  an empty lookup answers "not in the local reference" (doc 21 §10.2).
- **Safety** (doc 24 §5.3): AI-proposed script text exists only inside typed edit commands, is parsed and capability-checked
  by the host for the target profile, and is never executed; only the user presses Run. Mission text, including
  briefings and comments, is untrusted data (doc 21 §9.1). Templates the agent selects are subject to the §4.8 rules.
- **Why this fits weak models:** in doc 30's experiment, typed actions and code-written files were the strongest lever,
  and the residual failures were wrong command forms and whole-file writing (measured in doc 30 §3). Modules and rules
  remove both.

## 10. Phased plan and acceptance tests

| Phase | Scope | Depends on |
| --- | --- | --- |
| L0 | Lossless emit and patchers (doc 04 §12); per-profile catalog and checker (doc 23); risk policy (doc 24); region hashing and sidecar provenance; singleton registry | — |
| L1 | Attributes and presets; Objective, End state, Respawn point, Save point modules; rule builder with native-only lowering; script editor core (symbol index, silent-failure lints, completion, rename) | L0 |
| L2 | Wave-1 modules (reinforcements, fire support, air transport, patrol, random, interaction, hostage, garrison, conversation); SQS lowering for rules; timeline v1 (shots, titles, music; capture import); Preview log mapping | L1; doc 08 P1 |
| L3 | Timeline live preview; screenplay audio and `.lip`; T0 community module packs; recognisers and lift; console, watch and rule debugger after the non-aborting launch | L2; doc 08 P2/P3; doc 22 T0 |
| L4 | Wave-2 modules; MP modules with MP Preview (doc 08 §4.5); constrained dialog designer | L3 |

| ID | Acceptance test | Pass criteria |
| --- | --- | --- |
| AT1 | Build an MP co-op mission with BASE respawn, a reinforcement wave when an area is lost, radio-called artillery and a four-shot intro, typing no script | Every lint passes; the `Cwa199` build contains no command outside that profile (catalog scan); a CWR Preview logs no `Script error` line; manual 1.99 checklist passes; in a moderated session a newcomer finishes within a target time [I, set after the first study] without opening the script editor. Gated at L2 in SP Preview; the MP behaviour is re-run on the L4 MP Preview |
| AT2 | Intro cutscene: four shots, a title, music, one `say` line; plus an in-mission cutscene before an ending | Static check proves balanced `disableUserInput`, terminate through the camera object before `camDestroy`, no title-layer effect at the ending; probe confirms the mission ends |
| AT3 | Hand-edit a generated region, and separately move a module-emitted trigger on the map; then change a module parameter | Both edits survive or a three-way merge is offered; zero clobbers (doc 25 E9) |
| AT4 | Eject every first-party module | Ejected script produces byte-identical game output until edited |
| AT5 | A weak model builds "ambush the convoy at the bridge, then call artillery" | Only module and rule proposals; zero hand-written SQS; all checks pass within the bounded repair loop |
| AT6 | Import a mission with pasted camera captures | Recogniser proposes shots; accept → re-emission equals the normalised original |
| AT7 | Two map-click modules plus fire support in one mission | Exactly one `onMapSingleClick` assignment in the output; all three work in Preview |
| AT8 | A server-guarded module in single-player Preview | It runs (probe of the `local <logic>` guard) |
| AT9 | A T0 pack template that emits a `tri*` verb, a `loadFile` whose path contains `..` or `:`, or unescaped parameter text | Refused at instance time with the doc 24 rule id (L1, L2); escaping filters neutralise quotes. A literal mission-relative `loadFile` is `approve`, not `deny`, under doc 24 §5.3, so refusing every pack `loadFile` needs a stricter pack policy (open question 13) |
| AT10 | Compile the same model twice per profile | Byte-identical output |
| AT11 | Switch a mission to `Cwa199` | Every `Cwr`/`Ce`-only feature is greyed out with its reason |
| AT12 | Drop every first-party module on a sample mission and change nothing | Each passes every lint on its context defaults, or names in one line the single thing it still needs |
| AT13 | Extend without ejecting: show a hint and release a group when a fire mission completes | Done with one rule on the module's output event; the module stays `Clean` and no script is typed |
| AT14 | A mission whose own `init.sqs` already sets `onMapSingleClick`, plus a fire-support module | The conflict is reported before export; after the previewed fix both handlers work in Preview and the original handler body is unchanged |

**Probe-suite entries** (run through Preview; AGENTS.md porting rules): vanilla round spawning for fire support; `local`
on a Game Logic in SP; marker hiding for pools; in-mission cutscene skip; `setDir`/`setVector*` on a never-targeted
camera; title speed 0 and negative; `camDestroy` without terminate; `onPlayerRespawn.sqs` and `soundLength` on 1.99; a
mission-local `onPlayerKilled.sqs` with and without a root `scripts\onPlayerKilled.sqs` (the root-only existence gate,
§4.5); `setFog` cancelling a pending `setOvercast` (statically confirmed, §4.6 row 15; the probe confirms the visible
effect); an Effects-field title alive when an END trigger fires (expected: the ending waits); the map in an outro; exact
live preview under `setAccTime 0`. The upstream tests
closest to this area (`camcreate_any_type`, the `demo_end_*` family, `demo_outro_titles_load`, `test_sqs_runner`,
`test_sqs_integration`) already have rows in `docs/porting/upstream-test-map.csv` [V].

**Upstream report candidates (CWR-CE):** the `camSetBank`/`camSetDir` binding, the `camSetFovRange` stub, the RscTitles
`fadeOut` overwrite, the unchecked unknown `cameraEffect` name, the −1 enum values stored by the effect setters, harness
`eval` errors that abort AutoTest, and script name and line in the error message. Added by the engine review: the
`camSetFov` "set" flag that is never cleared (`CameraHold.cpp#L575-L580`), `RptF` compiled to a no-op so the SQS "Only
one field" and "Max iteration count" reports never reach a log (`DebugLog.hpp#L61`), the root-only existence gate on
respawn hooks (`SoldierOldMove.cpp#L880`, `#L1076`), and `respawn = SIDE` logging through `Fail()` at ERROR level. The
compiler works around all of them for existing installs.

## Open questions

1. **Vanilla fire support.** Which method makes a real explosion from a script on 1.99 and 3.05 without `createShell`
   (spawning an ammo class with `camCreate` or `createVehicle`)? The community "fake artillery" wording could not be
   verified at its cited source [U].
2. **SP-safe server guard.** Is `local <game logic>` true in single player on every profile (AT8)? Static reading of
   3.05/CE says yes (§4.5); 1.99 and runtime remain open.
3. **In-mission skip.** Is any vanilla input path (radio menu, action) usable while a camera effect is active?
4. **Marker pools.** What hides a pre-placed marker on `Cwa199` (off-map parking, zero size, empty type)?
5. **Free camera heading.** Do `setDir` or `setVector*` orient a camera that never had a target? If yes, the timeline can
   offer heading (all profiles) and roll (`Cwr`/`Ce`) on no-target shots only.
6. **Init prefixes.** Does the original in-game editor preserve our generated init-field prefixes untouched on load and
   save, and how long may a field grow?
7. **Non-aborting debug launch.** A harness launch without `--test-mission` (so no `AutoTest`) and with `--no-strict`,
   versus the upstream `--preview-mission` (doc 08 P3); `--no-strict` alone does not help, because `--test-mission`
   itself sets `AutoTest` (§7.4). Record the design gap first.
8. **One format?** Should compositions (doc 17 §6), module definitions and rule sets share one on-disk format and schema
   language, and is it TOML?
9. **Vocabulary.** Mission modules here versus campaign "persistence modules" in doc 26 §5.2: one concept with two
   scopes, or two names?
10. **Condition language.** Extend CXL itself (one grammar, one checker) or define a sibling for mission scope?
11. **Ranking.** Validate the pattern order with a short community survey (doc 09 open questions), since counters mix eras
    and games.
12. **Generated-output licence.** Doc 02's Generated Content Exception covers our templates; what applies to output of
    community T0 templates?
13. **Pack policy for `approve` commands.** Doc 24 gives literal mission-relative `loadFile`/`preprocessFile`, `saveGame`
    and input locks `approve`. Should T0 pack output treat every `approve` command as refused (no user to ask at
    instance time), or ask once per pack install?

## Sources

**Engine, `BohemiaInteractive/CWR@ffc61838b7` (3.05) and `ofpisnotdead-com/CWR-CE@b67bf3bd62`:**
`engine/Poseidon/Game/Commands/GameStateExt.cpp#L853-L1466` (registration tables; CE#L852-L1464, corrected 2026-09-27;
only `DBG_*` rows at `#L1173-L1176` are cheat-gated); `GameStateExtUi.cpp#L878-L1823`; `GameStateExtGrp.cpp#L1413-L1438`, `#L1849-L1861`;
`GameStateExtWorld.cpp#L745-L803`, `#L1110-L1114`; `GameStateExtWorldConfig.cpp#L890-L893`, `#L1050-L1091`;
`GameStateExtWorldWaypoint.cpp#L540-L644`; `GameStateExtTestAudio.cpp#L2960-L2974`, `#L3051-L3166`;
`engine/Poseidon/World/Scene/Camera/CameraHold.cpp#L40-L597`, `CamEffects.cpp#L254-L297`, `CamEffects.hpp#L26-L39`;
`engine/Poseidon/Game/TitEffects.cpp#L476-L625`; `engine/Poseidon/Audio/DynSound.cpp#L125-L301`;
`engine/Poseidon/AI/AIRadio.cpp#L1429-L1442`; `engine/Poseidon/World/WorldSetup.cpp#L878-L932`, `#L1342-L1450`;
`engine/Poseidon/World/World.cpp#L1208-L1221`; `engine/Poseidon/World/WorldInit.cpp#L622-L632`;
`engine/Poseidon/World/Terrain/Landscape.cpp#L459-L465`, `#L558-L652`; `engine/Poseidon/World/Detection/Detector.cpp#L42-L46`,
`#L696-L707`, `#L1259-L1337`; `engine/Poseidon/World/Entities/Infantry/SoldierOldMove.cpp#L364-L411`, `#L723-L803`,
`#L874-L891`, `#L1064-L1200` (the CE file is byte-identical, so CE lines equal 3.05 lines); `engine/Poseidon/Network/NetworkServerMission.cpp#L281-L364`,
`#L387`; `engine/Poseidon/UI/OptionsUI.cpp#L630-L655`; `engine/Poseidon/UI/DisplayUIMenus.cpp#L827`, `#L984-L995`,
`#L1173-L1450`; `engine/Poseidon/UI/Map/UIMapMain.cpp#L2139-L2173`; `engine/Poseidon/AI/AICenterImpl.cpp#L1016-L1017`,
`#L1638-L1702`; `engine/Poseidon/AI/Path/ArcadeWaypoint.hpp#L61-L257`; `engine/Poseidon/AI/Path/AITypes.hpp#L31`;
`engine/Poseidon/AI/EntityAIType.hpp#L399-L415`; `engine/Poseidon/IO/Streams/QStream.cpp#L361-L376`;
`engine/Poseidon/Graphics/Rendering/Effects/Smokes.cpp#L2309-L2312`; `engine/Poseidon/Game/Scripting/Scripts.cpp#L97-L580`,
`Scripts.hpp#L53`; `engine/Poseidon/Game/Scripting/ExpressExt.cpp#L146-L178`; `engine/Poseidon/Dev/Harness/HarnessBuiltins.cpp#L73-L111`;
`engine/Poseidon/Foundation/Framework/DebugLog.hpp#L61`; `engine/Evaluator/express.cpp#L131-L137`, `#L788-L798`,
`#L862-L875`, `#L1132-L1133`, `#L1166`, `#L2486-L2547`, `#L2773-L2782`, `#L2988-L3011`; `apps/tools/Tools/commands/SoundCommand.cpp#L157`.
Absences checked by grep over `engine/`: `attachTo`, `triggerActivated`, `setVehicleVarName`, camera preload commands,
`try`/`catch`/`throw` as script commands.
Added by the engine review (2026-09-27): `engine/Poseidon/UI/DisplayUI.cpp#L121-L145`; `engine/Poseidon/World/WorldSetup.cpp#L1285-L1315`,
`#L1394-L1428`; `engine/Poseidon/World/World.cpp#L1646-L1652` (CE `#L1246-L1259` for the height clamp);
`engine/Poseidon/World/World.hpp#L445`, `#L587`; `engine/Poseidon/World/Detection/Detector.cpp#L1259-L1337`,
`#L1392-L1515`; `engine/Poseidon/AI/AIArcade.cpp#L794-L806`; `engine/Poseidon/Game/Chat.cpp#L155-L161`;
`engine/Poseidon/AI/VehicleAIPilot.cpp#L1064-L1073`; `engine/Poseidon/Game/Commands/GameStateExtWorld.cpp#L769-L803`;
`GameStateExtUi.cpp#L952-L963`, `#L1369-L1413`, `#L1641-L1755`, `#L1807-L1823`; `GameStateExtTestAudio.cpp#L972-L999`
(CE `#L977-L1004`, `#L2993`, `#L3085-L3200`); `engine/Poseidon/World/Scene/Camera/CameraHold.hpp#L24-L86`,
`CamEffects.cpp#L34-L48`, `#L653-L690`; `engine/Poseidon/World/Simulation/Simul.cpp#L363`;
`engine/Poseidon/World/Entities/Vehicles/Vehicle.hpp#L346`; `engine/Poseidon/Network/NetworkImpl.hpp#L34`;
`engine/Poseidon/World/Simulation/Animation/FrameFunctions.cpp#L55-L63`; `engine/Poseidon/Foundation/Framework/DebugLog.hpp#L51-L79`;
`engine/Poseidon/Foundation/Platform/AppConfig.cpp#L569-L573`, `#L627`, `#L1130`; `engine/Poseidon/UI/OptionsUI.cpp` CE `#L636-L661`;
`engine/Evaluator/express.cpp#L93-L129`, `#L1187`, `#L2702-L2793`; `apps/cwr/Game/GameApplication.cpp#L1703-L1718`
(same in CE). Further absences by grep: `CfgFunctions`, `endMission`, `enableAI`, `sleep`, `spawn`, `execVM`,
`waitUntil`, `isNil`, `compile` as registered script commands.

**Community (fetched or re-scraped 2026-09-27):** OFPEC Editors Depot lists and about 180 details pages
(<https://www.ofpec.com/editors-depot/index.php?action=list&game=OFP&cat=sc>, `cat=tu`, `cat=to|re|fu`); OFPEC forum topics
3021 (convoys, 2002) and 1905 (waypoints, 2002); <https://www.ofpec.com/tags/>; OFPEC Missions Depot id 107; OFP.info
EditorExtra, VideoMissions and CoC Unified Artillery 1.1 pages (<http://ofpr.info.paradoxstudio.uk/>); BIKI "Operation
Flashpoint: FAQ: Mission Editing" (MediaWiki API); aligrant.com OFP editing pages; Faguss: `cwa_scripting.pdf`,
`modified_spectating_script.pdf`, `flashpoint_cutscene_maker.pdf`, <https://ofp-faguss.com/scripts>;
<https://github.com/Faguss/fwatch>.

**Prior art (fetched unless noted):** Hive Workshop GUI leak guide; Better Triggers guide; StarCraft II editor guides
(GalaxyScript, Trigger Debugger, Action Definitions, Cutscene Editor); Hoggit DCS trigger pages and MOOSE UserFlag docs;
BIKI Modules, Key Frame Animation, Splendid Camera, `BIS_fnc_establishingShot`, Reforger Scenario Framework; ACE3
modules framework; ZEN dynamic dialog docs; Creation Kit conditions and scenes (search summaries); Lilac Soul's NWN
script generator; RPG Maker MZ event commands; Epic Blueprint/C++ balance and Diff Tool docs; Unity Cinemachine and
Timeline docs; MakeCode JavaScript blocks and Blockly connection checks; Weintrop & Wilensky (2015); cog checksum docs
(<https://cog.readthedocs.io/en/latest/running.html>).

**Repository docs:** 02 §6.2; 03 §4.4-§4.8; 04 §5, §6, §8, §12; 08 TL;DR, §4.2, §4.4, §4.5, §5.3; 09 §4, §6, §8; 17 §6;
19 §5, §6.5, §7; 21 §2, §3, §9, §10; 22 §2.1; 23 §4, §13; 24 §5; 25 E9; 26 §5.2; 30 TL;DR, §3; 32 §1.1, §3.2, §3.5, §5.3;
33 header; `docs/porting/upstream-test-map.csv`.

## Verification notes

### Product review notes

Product and fun review, 2026-09-27. It checked the doc against the owner direction (no-code first, scripting first-class,
community favourites made easy rather than hacky), the AGENTS.md invariants, and four prior-art pitfalls: visual
spaghetti, hitting the ceiling, opaque generated code and tedious forms. **Held:** native-first output that stays
readable in the stock editor; compiler-owned singletons; an honest camera with no pretend roll or auto-zoom; lifting
that offers and never forces; three escape sizes (N1); region states; weak models limited to Pick and Fill; no
general node graph. **Changed:**

- *Tedious forms.* §4.1 now says "drop in, then refine": a module works when dropped, shows at most five basic fields,
  ships presets and Shuffle, reads back as one sentence, and is found by intent. Footprints are handles (§4.3); AT12 added.
- *The ceiling.* Modules expose output events and input verbs to rules (§4.1, new §5.2 row). Rules gain a "for each"
  action (`forEach` [V `EVAL:express.cpp#L1133`]) and rule templates. AT13 added.
- *Opaque code.* Generated names carry the user's label (§4.4). Each generated block opens with a plain comment, and a
  form-and-code split view is the learning path to rung 5 (§8.3).
- *Spaghetti and iteration.* Rule arrows are scoped to the selection by default. "Try it" forces one element in Preview
  on `Cwr`/`Ce`, gated on the non-aborting launch (§5.4).
- *Human edits.* Map edits to emitted entities follow the region states (§8.3; AT3 extended). Hand-written hooks, radio
  triggers and click handlers are never overwritten. A clash with `onMapSingleClick` is a compile error with a previewed
  fix (§4.5); AT14 added.
- *Weak models.* The §9 weak tier now includes rule templates. AT5 had asked a weak model for rules that §9 reserved for
  the mid tier.
- *Cinematics.* Doc 32 exists and now governs rung 4 (header, §6.2). §6.3 terminates through the camera object:
  `cameraEffect` on a null object returns early [V `GameStateExtUi.cpp#L1371-L1375`], and `player` is probably null in a
  section with no player unit [I]. The input lock is optional, as in doc 32. With no `try`/`catch` [V grep], the abort
  path is doc 32's watchdog. §9 tool names now match doc 32 §5.3.
- *Coverage.* Camera gadgets (§2 row 41; 2,693 combined downloads) had no home in §6 or doc 32; they are now a wave-2
  "Live camera" module. The custom-dialog row now says it is script-only until L4. AT1 gains a moderated newcomer time
  target and phase gates (SP at L2, MP at L4).

### Engine review notes (2026-09-27)

Adversarial engine review against `BohemiaInteractive/CWR@ffc61838b7` and `ofpisnotdead-com/CWR-CE@b67bf3bd62`, docs 08,
23 and 24. Static reading only; nothing was built or run. Every command line cited in the doc's `GSE` column was
re-checked against the registration table, and CE parity was re-hashed file by file (§6.1 note).

**Held (re-verified):** one global `onMapSingleClick` string with a Bool result; 10 radio slots; `addAction` arity 2
with both elements strings; `camSetBank`/`camSetDir` bound to the dive handler and never read by commit;
`camSetFovRange` stub; linear constant-speed commits and the latest-deadline `camCommitted`; `camSetRelPos` resolved at
call time; 0.1 m camera clamp; 14 `cameraEffect` position names; title- or camera-effect blocking of the mission end;
`BLACK OUT` at 1e20 s; `titleRsc`/`cutRsc` speed and `fadeOut` quirks; `disableUserInput` as an unclamped counter;
`showCinemaBorder` reset per display; 0.5 s trigger precision with a random phase; no `triggerActivated`, `attachTo`,
`setVehicleVarName`, preload or `try`/`catch` command; read-only editor names and crew names; respawn SIDE falls back
to GROUP; prefix-matched respawn markers with a random pick; the hook-to-mode table; the single camera-script slot;
`isServer` false in SP; `init.sqs` before `init.sqf`; 100 lines per step for `exec`'d scripts; 4,095-byte lines;
233-byte `~` delays; `RptF` compiled to a no-op; the 10,000-iteration `while` cap; rain gated at overcast ≈ 0.67;
`AnimChanged` in the entity event list; the 12-unit group cap; 18- or 19-element `drop`; the capture format.

**Corrected in place:**

1. *Mission end (§4.4, §4.6 row 2).* `forceEnd` was listed as a fallback way to end a mission. It only sets the
   "end forced" flag that lets an END already triggered pass a blocking effect; no `endMission` is registered and
   `endGame` closes the application. Endings are END/LOSE triggers reading a compiler flag.
2. *Effects titles (§2 row 16, §3, §5.2, §5.3 step 3, §6.1).* Trigger and waypoint Effects titles always use the
   **title** layer, like `say` subtitles and direct-channel chat, so "a title in Effects" and "cut layer by default"
   were incompatible. Fades and titles that may be alive at an ending now lower to SQS `cutText`/`cutRsc`.
3. *Weather (§4.6 row 15).* The [I] "each resets the other's pending transition" is now [V static], and the proposed
   mitigation ("issued together") was wrong: the second call re-targets the first to its current value, so both in
   sequence cancel the first. One gradual transition at a time.
4. *Hook override (§4.5, §4.6 row 20).* Every respawn/death hook starts only if the **root** `scripts\<hook>` exists;
   the mission → campaign → root lookup runs after that gate. A mission copy therefore overrides only when a root copy
   exists (probe added).
5. *While-true rules (§5.3 step 1).* On Deactivation runs only on repeating triggers; `this` is not rebound in
   activation statements (stale when the condition is exactly `this`).
6. *Trigger timers (§5.2, §5.3 step 5).* Timeout/countdown delays are Gaussian-random over min/mid/max, so exact
   timing needs min = mid = max.
7. *Silent-failure lints (§7.2).* A `:` inside a `?` condition and a `~` delay over 233 bytes do produce a (misleading)
   runtime error, so they moved to "Late"; duplicate labels do not exit (the first wins); a missing script's warning is
   reported only once per severity per session (`SINGLE_WARNING`), no longer [I]; unknown title/effect strings added.
8. *Design gap (§7.4).* Upgraded from [I] to [V static] with the `--test-mission` → `AutoTest` link and the
   `eval` → `ShowError` → `DisplayErrorMessage` path. The non-aborting launch must avoid **both** `AutoTest` and
   `--strict`; `--no-strict` with `--test-mission` still aborts (open question 7 rewritten).
9. *Harness scope (§7.4).* `eval`/`exec` share one persistent harness-owned local scope, not "one global scope".
10. *Live preview (§6.4).* `setAccTime 0` freezes game time, so exact mode must commit samples with `camCommit 0`
    [I]; the manual-camera division by `accTime` is now [V static]; `triSetView` uses engine axis order; CE lines added.
11. *FOV (§6.1).* The engine has a distance-based auto-zoom that the stubbed `camSetFovRange` makes unreachable, and the
    FOV "set" flag is never cleared, so later commits re-time a running zoom; `camSetFov` is emitted per segment.
12. *Respawn (§3, §4.6 row 6).* SIDE logs at ERROR level through `Fail()` in release builds (fatal under `--strict`),
    so the picker writes `GROUP`; resistance markers are `respawn_guerrila`; unit-name prefixes can capture side markers;
    no marker means BASE respawns in place; invalid `respawn` values mean NONE.
13. *Init order (§3, §4.3).* Scripts `exec`'d from init fields step before `init.sqs`; `init.sqs` has no line cap;
    `init.sqf` on 1.99 marked (unverified).
14. *Citations.* CE offset in `GameStateExt.cpp` (one lower before L886, two after; CE has no `endGame`); CE range
    L852-L1464; `SoldierOldMove.cpp` is identical in CE (the old "CE lines" note was misleading); `count units` is the
    unary `count` at `express.cpp#L1187`; CE lines for `World.cpp`, `GameStateExtTestAudio.cpp`, `OptionsUI.cpp`.
15. *Profiles (TL;DR, §5.3 step 7).* 1.99 absence of the Elite/ArmA-era commands rests on wiki tags (doc 23 §4), not on
    a 1.99 install; marked so.
16. *AT9.* A literal mission-relative `loadFile` is `approve`, not `deny`, under doc 24; the test now uses a `..` path,
    and open question 13 asks for a pack policy on `approve` commands.

**Still unverified (need a probe, an install scan or a fetch):** everything about the 1.99 executable (command set,
`init.sqf`, `onPlayerRespawn.sqs`, `soundLength`, `logInfo`, `publicVariable` value types, `"NULL"` radio hiding);
whether stock installs ship root `scripts\onPlayer*.sqs`; `local <logic>` at runtime (AT8); the map in outros;
vanilla round spawning; marker hiding; `setDir`/`setVector*` on a never-targeted camera; the shipping default of
`--strict`; OFPEC download counts and the community quotes (not re-fetched by this review).

**Open:** (1) §6 largely repeats doc 32 §2–§4. With these notes the file is about 830 lines, well over the ~650 target,
so once doc 32 is accepted, cut §6 to the engine limits and the contract the other rungs rely on. (2) Stale cross-references outside this
file: the doc 32 header says doc 31 "is not written yet", and doc 33 says docs 30–32 do not exist. (3) The map track: §6.2
cites `mapAnimAdd` in intros as [V], while doc 32 §5.1 gates map pans on a probe [U]. The engine review should reconcile
them. (4) Custom dialogs (3,992 combined downloads) stay script-only until L4; consider module-generated menus or a
constrained designer in L3. (5) "Try it" is the strongest fun lever, and it is blocked on the unrecorded `--test-mission`
abort gap (§7.4); record the gap now. (6) Drop-in defaults can wire silently to the wrong thing (the "nearest group" may
be the player's), so defaults stay visible chips; test the risk in the AT1 study. (7) File names built from labels
change when a label changes. Either the rename follows every reference, or names freeze at first export; decide which.
(8) Rule locality (§5.1) is user-declared, but N6 says code owns locality. Compute it from the actions (spawns on the
server, presentation everywhere) and move the override under Advanced. (9) No UX claim here has user evidence yet. The
five-field cap, drop-in defaults, the split view and the pattern ranking (open question 11) all wait on the AT1 study.
