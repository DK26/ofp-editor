# Original CWA Mission Editor ("Arcade" editor) — Code Map

Research note 03 for **ofp-editor** (a standalone Rust re-implementation of the in-game mission editor of
*Arma: Cold War Assault* / *Operation Flashpoint: Cold War Crisis*). This file maps every user-facing
feature of the original editor to the C++ that implements it in Bohemia's released engine source
(codename *Poseidon*), describes the architecture, and ends with a porting checklist.

**Pinned sources.** Primary: `BohemiaInteractive/CWR@ffc61838b7` (commit "3.05", 2026-08-18). Compared
against the community fork `ofpisnotdead-com/CWR-CE@b67bf3bd62` (2026-09-21).

**Citation shorthand (mechanically expandable).**
`P:<path>#Lx-Ly` ≡ `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/<path>#Lx-Ly`;
`CE:<path>#Lx-Ly` ≡ `ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/<path>#Lx-Ly`;
`R:<path>` ≡ `BohemiaInteractive/CWR@ffc61838b7:<path>` (repo root).

**Epistemic tags.** **[V]** verified by reading the cited code/test; **[I]** inferred from code but not
executed; **[U]** unknown / needs game data or a runtime check. Everything untagged in tables is [V]
against the citation in the same row.

## TL;DR

- The editor is `DisplayArcadeMap` (IDD 26) hosting one map control `CStaticMapArcade` (IDC 51); all
  editing dialogs are separate modal `Display` subclasses loaded by name from **Rsc config classes**
  (`RscDisplayArcadeUnit`, `…Waypoint`, `…Sensor`, `…Marker`, `…Group`, `…Effects`, `RscDisplayIntel`,
  `RscDisplayTemplateSave/Load`); Unit, Waypoint, Trigger, Marker, Effects and Intel also have an
  `…Simple` twin used in **Easy mode** (Group/Save/Load do not) [V]. The twins only drop expert and
  code fields and add none (§3.2; doc 35 §10) [V].
- **The Rsc layouts, fonts, colors, icons, string table and all `Cfg*` classes are NOT in the repo** —
  they live in the (non-GPL, APL-SA) game data (`bin/resource.cpp|.bin`, `config.bin`, stringtable).
  Visual accuracy therefore requires reading the user's installed data at runtime [V: P:Asset/Addon/ConfigParsers.cpp#L242-L249, R:README.md#L14-L18].
  (Absence from the repo is [V]; that APL-SA — non-commercial, share-alike, "Arma-only" — covers
  `resource.*`/`config.bin`/stringtables specifically is [I] from the README's "models, textures, sounds,
  missions, etc." wording.)
- Data model = `ArcadeTemplate` (groups→units/waypoints/group-triggers, empty vehicles, free triggers,
  markers, intel, addons). One `mission.sqm` holds **four** templates: `Mission`, `Intro`, `OutroWin`,
  `OutroLoose` [V: P:UI/Map/UIMapExtDisplay.cpp#L99-L133].
- `mission.sqm` is written by `ParamArchive` (format version **11**): values equal to their declared
  default are **omitted** (only keys that declare a default, see §3.7), enums are written as **strings**
  (an unknown name on load fails its key; inside an `ItemN` that failure is only logged, so the item
  half-loads and the mission still loads, see §3.7 and doc 04 §2.3), arrays of classes as
  `items=N; class ItemK` [V].
- 6 editor modes on F1–F6: Units, Groups, Triggers("Sensors"), Waypoints, Synchronize, Markers [V].
  Interaction is double-click-to-insert/edit, click/Ctrl/Shift/rubber-band selection, drag-move,
  **Shift-drag rotate**, drag-to-link (Groups/Synchronize modes), Del, Ctrl+C/X/V clipboard [V].
- Every dialog follows one pattern: copy the struct in the ctor → fill controls in `OnCreateCtrl` →
  validate in `CanDestroy` (script syntax via the SQS/SQF evaluator in check-only mode, identifier
  rules, uniqueness) → write back in `Destroy` → parent merges in `OnChildDestroyed` [V].
- **Preview** is not a separate process: it copies the template into the global `CurrentTemplate`,
  calls `World::SwitchLandscape/ActivateAddons/InitGeneral/InitVehicles`, then opens `DisplayMission`
  (or `DisplayGetReady` if Shift is held and a briefing exists) [V: P:UI/Map/UIMapExtDisplay.cpp#L529-L614].
- A standalone app can reproduce Preview by saving the mission folder and launching the CWR binary with
  the positional `mission` argument (`…/<name>.<world>/mission.sqm` — file name and dotted folder name
  are mandatory) plus `--autotest`, which boots straight into the mission via `StartAutoTest()`
  [V for CWR/CWR-CE source; U for retail CWA 1.99 binaries]. That path re-reads the file from disk, skips
  the briefing and cannot preview Outro sections (see §4.12).
- CWR-CE differs only cosmetically in the editor (addon-missing message refactor, cursor aspect math,
  bindable mouse-wheel zoom); either repo is an equally valid reference for this code [V].
- **Recommendation:** port the data model + `mission.sqm` I/O + the map interaction state machine
  first (pure, testable), then the dialogs as data-driven forms fed by parsed `Cfg*`; treat Rsc
  layout replication and the landscape (WRP) map renderer as separate, later work streams.

## 1. Glossary

| Term | Meaning |
| --- | --- |
| Arcade / Arcade template | BI's internal name for the mission editor and its data (`ArcadeTemplate`). |
| Sensor | Internal name of a **trigger** (`ArcadeSensorInfo`, `IMSensors`, `IDC_ARCSENS_*`). |
| Synchronization | Integer link id shared by waypoints and/or triggers (`synchronizations[]`). |
| Section | One of 4 templates edited in one file: Mission, Intro, Outro (win), Outro (lose). |
| Display / IDD | A screen/dialog (`Display`, id = IDD). Controls inside have ids = IDC. |
| Rsc class | A config class in `Res` (resource config) describing a display's controls, e.g. `RscDisplayArcadeMap`. |
| `Pars` / `Res` | Global parsed game config (`config.bin`: `CfgVehicles`, …) and resource config (UI). |
| `ExtParsMission` / `ExtParsCampaign` | Parsed `description.ext` of the current mission / campaign. |
| ParamArchive | Engine serializer over the config-file syntax, used for `mission.sqm`. |
| Easy / Advanced mode | Editor difficulty toggle; Easy loads `…Simple` Rsc dialog variants. |
| Info age | Per-unit/trigger "how old is the intel" enum (`ArcadeUnitAge`); `UNKNOWN` hides non-player-side units from limited-rights map viewers (`P:UI/Map/UIMapExt.cpp#L705-L708`); runtime meaning [I]. |

## 2. Source inventory

| File (CWR) | Lines | Role | CWR-CE |
| --- | --- | --- | --- |
| `P:UI/Map/UIMap.hpp` | 1112 | Class decls: `DisplayNotebook`, `DisplayMapEditor`, `InsertMode`, `CStaticMapArcadeViewer`, `CStaticMapArcade`, `DisplayArcade*`, `DisplayIntel`, `DisplayTemplateSave/Load` | identical |
| `P:UI/Map/UIMapBase.hpp` | 392 | `SignType`/`SignInfo` (hit-test result), `CStaticMap` base map control | identical |
| `P:UI/Map/UIMap.cpp` | 2535 | `CStaticMap`: ctor (reads colors/fonts/icons), coordinate math, background layers, grid, zoom/scroll/pan | cursor + wheel-zoom changes |
| `P:UI/Map/UIMapExt.cpp` | 2933 | Editor map: draw overlays, hit-test, selection, drag/rotate/link, keyboard, clipboard, `DisplayArcadeMap` ctor | identical |
| `P:UI/Map/UIMapExtDisplay.cpp` | 2422 | `DisplayArcadeMap`: buttons, Load/Save/Merge/Clear/Export, Preview/Continue, child-dialog merge, easy/advanced, cheat SQF export | addon-message refactor |
| `P:UI/Map/UIArcade.cpp` | 1936 | Unit, Group, Trigger dialogs + azimuth widget | identical |
| `P:UI/Map/UIArcadeWaypoint.cpp` | 990 | Waypoint dialog, Save/Load dialogs, Intel dialog, mission-path parsing, `ParseCutscene` | addon-message refactor |
| `P:UI/Map/UIArcadeMarker.cpp` | 1172 | Marker dialog, Effects dialog | identical |
| `P:UI/Map/UIContainers.cpp` | 1929 | `ControlsContainer`: Rsc loading, control factory, mouse/keyboard dispatch | cursor-draw refactor |
| `P:UI/Map/UIMapDialogs.cpp`, `UIMapDisplay*.cpp`, `UIMapMain.cpp` | — | In-game map, briefing (`DisplayGetReady`), debriefing. Editor-relevant only via Preview | — |
| `P:UI/Map/UIMapExport.cpp` | — | Cheat-only map export to EMF (`ExportWMF`) | identical |
| `P:AI/ArcadeTemplate.hpp/.cpp` | 255 / 1994 | Data structs, enum↔string tables, defaults, serialization, consistency, addons | +`MissingAddonMessage` etc. |
| `P:AI/ArcadeTemplateFind.cpp` | 1404 | Template mutations: find/update/delete/regroup/sync/compact/merge | identical |
| `P:AI/Path/ArcadeWaypoint.hpp` | 309 | `ArcadeEffects`, `ArcadeWaypointInfo`, `ArcadeMarkerInfo`, all editor enums | identical |
| `P:AI/AIArcade.cpp` | — | **Runtime** waypoint FSM (how MOVE/SCRIPTED/… execute). Not needed by the editor; reference for semantics | — |
| `P:UI/DisplayUIMenus.cpp#L1791-L1990` | — | `DisplayNotebook`/`DisplayMapEditor` impl, `OpenEditor`, `StartAutoTest` | — |
| Tests | — | `R:tests/integration/ui/editor/*.test.sqf` (UI automation, IDCs), `R:tests/unit/engine/Poseidon/Game/test_editor.cpp` (compile-only stub) | same set |

## 3. Architecture

### 3.1 Class hierarchy [V: P:UI/Map/UIMap.hpp]

```text
ControlsContainer ─ Display
  ├─ DisplayNotebook (abstract: GetWeather/GetTime/GetPosition → notebook widgets IDC 52-55)   #L8-L24
  │    └─ DisplayMapEditor (map cursor shapes, routes keys to map first)                      #L34-L47
  │         └─ DisplayArcadeMap (IDD 26) — 4 ArcadeTemplates, _currentTemplate, _mode, _lastUnit,
  │                                        _multiplayer, _running, _advanced                   #L705-L764
  ├─ DisplayArcadeUnit(27) DisplayArcadeWaypoint(28) DisplayTemplateSave(29) DisplayTemplateLoad(30)
  ├─ DisplayIntel(32) DisplayArcadeGroup(40) DisplayArcadeSensor(41) DisplayArcadeEffects(44)
  └─ DisplayArcadeMarker(45)
CStatic ─ CStaticMap (map base)                                   P:UI/Map/UIMapBase.hpp#L125-L378
            └─ CStaticMapArcadeViewer (read-only draw + hit-test)  UIMap.hpp#L575-L617
                 └─ CStaticMapArcade (editing; EditRights)         UIMap.hpp#L619-L675
CStatic ─ CStaticAzimut (clickable azimuth compass bound to an edit box)  UIMap.hpp#L840-L852
```

IDD numbers: `P:Core/resincl.hpp#L286-L341` (also 202 = clear-confirm, 203 = exit-confirm msgbox).
`EditRights` has ERNone/ERGroupWP/ERSideWP/ERFull but the only construction uses **ERFull**
(`P:UI/Map/UIMapExtDisplay.cpp#L484`); the other rights are vestigial [V by grep].

### 3.2 Dialogs from Rsc config classes [V]

- `ControlsContainer::Load(name)` looks up `Res >> name`, reads `idd`, `movingEnable`, then iterates
  `controls`, `objects`, `controlsBackground` (class or name-array form); each control class needs
  `type` + `idc` (`P:UI/Map/UIContainers.cpp#L322-L442`).
- Each control is created via the virtual `OnCreateCtrl(type, idc, cls)`. Editor displays override it
  per IDC to construct and **pre-fill** combos/edits/sliders; unknown IDCs fall back to the generic
  factory keyed by `CT_*` type (`#L505-L599`; `CT_*` values `P:Core/resincl.hpp#L165-L191`;
  `CT_MAP=100` builds a `CStaticMap`, but the editor intercepts IDC 51 to build `CStaticMapArcade`
  with scaleMin/Max/Default = 0.001/1.0/0.1 — `P:UI/Map/UIMapExtDisplay.cpp#L482-L487`).
- **Commit protocol:** `Exit(idc)` sets `_exit`; `CanDestroy()` may veto (validation + message box);
  `Destroy()` copies control values into the display's own struct copy; the parent's
  `OnChildDestroyed(idd, exit)` reads `_child` and applies it to the template
  (`P:UI/Map/UIMapExtDisplay.cpp#L2021-L2362`). Cancel discards the copy.
- Because the code only touches controls that exist, the `…Simple` Rsc variants hide fields simply by
  omitting controls. Which fields they omit is in game data. It was read from the owner's install
  (doc 35 §10) [V]: the Simple variants drop exactly the expert and code fields and add none. The
  counts are Unit 9, Marker 5, Trigger 11, Effects 9, Waypoint 11 and Intel 2. Doc 35 names only
  the Unit fields (§4.4); the other dialogs' dropped field names still have to be listed from the
  same resource reading. (This was **[U]** before the consolidation pass.)

### 3.3 Entry points and lifecycle [V]

1. Main menu button IDC 115 → `CreateDisplayEditor` → `DisplaySelectIsland` (IDD 51) listing
   `CfgWorldList` entries whose `.wrp` exists (`P:UI/OptionsUIApp.cpp#L1232-L1237`,
   `P:UI/DisplayUI.cpp#L1193-L1238`). A "Wizard" button there opens the template wizard
   (`DisplayWizardTemplate`/`DisplayWizardMap`). This code map does not cover it, but it is the
   reference for our "New mission from template" (doc 35 §5.8).
2. OK → sets user-missions base dir, `SetMission(world,"")`, `SwitchLandscape(world)` (the **full
   landscape is loaded**), `CreateEditor(this)` → `new DisplayArcadeMap` (`P:UI/OptionsUIApp.cpp#L800-L827`,
   `P:UI/DisplayUIMultiplayer.cpp#L2418-L2421`).
3. MP host: server screen button IDC 103 → `CreateEditor(this, true)` (`…Multiplayer.cpp#L2427-L2440`).
4. Command line: positional `mission` arg ending in `.sqm` → `ProcessFullName` → `OpenEditor()`, or
   `StartAutoTest()` with `--autotest` (`P:World/WorldImpl.cpp#L2235-L2256`,
   `P:Foundation/Platform/AppConfig.cpp#L627`, `#L764`, `#L1132-L1137`). `ProcessFullName` only accepts
   a path whose file is `mission.sqm` inside a `<name>.<world>` folder
   (`P:Game/Mission/MissionPathLoader.hpp#L56-L88`). The help text says ".pbo or .sqm", but
   `World::StartIntro` dispatches only `.fps`, `.sqg` and `.sqm`, so a `.pbo` argument does nothing on this path [V].
5. `DisplayArcadeMap` ctor: `_mode=IMUnits`, `Load("RscDisplayArcadeMap")`, auto-load
   `<missionDir>/mission.sqm` if a mission name is set, center map on player, `LoadParams()`
   (easy/advanced), `ShowButtons()` (`P:UI/Map/UIMapExt.cpp#L2883-L2925`).
   `_enableSimulation=_enableDisplay=false`: the 3D world is loaded but neither simulated nor drawn.

### 3.4 Input model [V: P:UI/Map/UIContainers.cpp#L707-L982]

- Mouse is polled each frame in `ControlsContainer::OnSimulate`. LMB press → `OnLButtonDown`; a second
  press on the same control within **0.3 s** → `OnLButtonDblClick`. `OnLButtonClick` fires when the
  0.3 s window expires **or the mouse moves > 0.01 (screen fraction)** while captured — i.e. a drag
  starts from `OnLButtonClick` with the button still down. LMB release → `OnLButtonUp`. RMB → down/up.
  Movement → `OnMouseMove` if the cursor moved else `OnMouseHold`; wheel → `OnMouseZChanged`.
- Keys: `DisplayMapEditor::OnKeyDown` offers keys to the map first (`P:UI/DisplayUIMenus.cpp#L1930-L1941`);
  containers map Esc → `IDC_CANCEL`, Tab/Shift+Tab focus, Enter → default button (`#L984-L1052`).
- Screen coordinates are fractions 0..1 of the 2D canvas; the map converts with
  `WorldToScreen/ScreenToWorld` (`P:UI/Map/UIMap.cpp#L459-L474`): `x = X/L/scaleX + mapX + ctrlX`,
  `y = (1 − Z/L)/scaleY + mapY + ctrlY`, `L = LandGrid*LandRange` (island size), `scaleY = scaleX*h/w`.

### 3.5 Map draw pipeline in the editor [V]

`CStaticMap::OnDraw` (`P:UI/Map/UIMap.cpp#L2047-L2201`): poll zoom actions → keypad scroll or zoom
animation → `DrawBackground()` → `DrawGrid()` → virtual `DrawExt()` → cursor crosshair lines.

`DrawBackground` (`#L743-L1104`), layers in order. Density is measured as `ptsLand = 800/scale/LandRange`
(virtual points per land cell; contours use the analogous `ptsTerrain` over `TerrainRange`, `#L746-L751`);
thresholds at `#L613-L630` either coarsen the sampling stride (sea 6, textures 8, contours 8) or gate the layer entirely (forests 6, forest borders 6, roads 2, objects 10,
object stride coarsened by 15):
paper texture tiles → sea → **terrain textures only when "Show textures" is on** (`!_showScale`,
`#L804-L843`) → contour lines (interval auto-chosen from {2,5,10}×10ⁿ, `#L861-L878`) → forests →
forest borders → roads → objects by `MapType` (buildings as filled oriented boxes, trees/churches/…
as icons, **object IDs printed when Show IDs is on**, `#L1580-L1719`) → town names (`CfgWorlds >> world >> Names`)
→ mountain spot heights. Grid lines/labels come from `GWorld->GetGridInfo(scale)` (`#L1971-L2045`).

`CStaticMapArcadeViewer::DrawExt` (`P:UI/Map/UIMapExt.cpp#L426-L937`) overlays the template:

1. Waypoints attached to a unit (`id≥0`) snap to that unit's position.
2. Sync lines between all waypoints/triggers sharing a sync id (`_colorSync`, dimmed if neither end selected).
3. Per group: leader→waypoint polyline with arrowheads; waypoint icons (`_infoWaypoint`), placement
   circles, camera icon if the waypoint has effects (`HasEffect`); leader→group-trigger lines; group
   triggers (ellipse/rectangle outline + `_iconSensor`); leader→member lines; units: lines to their
   placement markers, icon (`CfgVehicles >> icon`, size from `mapSize`, rotated by azimuth, min 16 px),
   placement circle, player (`_colorMe`) / playable (`_colorPlayable`) badge.
4. Unit color: empty → `colorUnknown`; civilian/logic → `colorCivilian`; else friendly/enemy by
   `intel.friends[playerSide][side] ≥ 0.5`; unselected items at half alpha (`#L729-L753`).
5. Empty vehicles; free triggers (+ link line to the static object or vehicle they are bound to).
6. **Markers are drawn only in Markers mode** (`#L895-L934`) — but they remain hit-testable in all modes.
7. Hover label (`DrawLabel(_infoMove)`, `#L1708-L1940`): title + up to 6 detail lines (presence %,
   `? condition`, init, combat mode, behaviour, formation, speed, on-activation, trigger activation/type).

`CStaticMapArcade::DrawExt` (`#L939-L1056`) then draws the drag "link" line or the green rubber band.
Colors/icons come from the map control's Rsc class (`colorSea`, `fontLabel`, `Tree`, `Waypoint`, …) and
from `CfgInGameUI >> IslandMap` (`colorFriendly`, `iconSensor`, …) (`P:UI/Map/UIMap.cpp#L245-L386`).

### 3.6 Data model [V: P:AI/ArcadeTemplate.hpp, P:AI/Path/ArcadeWaypoint.hpp]

```text
ArcadeTemplate { groups[ArcadeGroupInfo], emptyVehicles[ArcadeUnitInfo], sensors[ArcadeSensorInfo],
  markers[ArcadeMarkerInfo], intel: ArcadeIntel, randomSeed, showHUD/Map/Watch/Compass/Notepad/GPS,
  nextSyncId, nextVehId, addOns[], addOnsAuto[], missingAddOns[] (runtime) }
ArcadeGroupInfo { side, units[ArcadeUnitInfo], waypoints[ArcadeWaypointInfo], sensors[ArcadeSensorInfo] }
```

Invariants maintained by `ArcadeTemplateFind.cpp`:

- Unit `id` = vehicle id, unique, dense after `Compact()` (renumbers ids, remaps waypoint `id` and
  trigger `idVehicle`; dangling refs become −1) (`#L882-L1046`). Waypoints/triggers reference units by id.
- Exactly one `leader` per group = highest rank (first wins); group side = leader side
  (`SelectLeader`, `P:AI/ArcadeTemplate.cpp#L1542-L1561`). Empty groups are deleted.
- Sync ids: `CheckSynchro` drops sync ids not used by ≥1 waypoint and ≥2 endpoints total
  (`P:AI/ArcadeTemplate.cpp#L1582-L1752`); triggers can sync only to waypoints.
- Only one *player* (`APPlayerCommander/Driver/Gunner`); setting a new player clears the old one
  (`UnitUpdate`, `P:AI/ArcadeTemplateFind.cpp#L412-L524`).
- A trigger lives in exactly one place: `template.sensors` (free) or `group.sensors` (activated by
  group, `activationBy=GROUP`); binding to a vehicle/static moves it to free triggers (`#L608-L690`).
- Positions are engine vectors **[X east, Y height, Z north]**; Y is recomputed from the terrain/road
  surface on every insert/move (`RoadSurfaceY`/`RoadSurfaceYAboveWater`) — the editor needs heights.

### 3.7 `mission.sqm` serialization rules [V]

- Root: `version=11` (`P:Core/SaveVersion.hpp#L9`), classes `Mission`, `Intro`, `OutroWin`,
  `OutroLoose`; pre-v7 files had one shared `Intel` (`P:UI/Map/UIMapExtDisplay.cpp#L99-L133`).
- Template body (`P:AI/ArcadeTemplate.cpp#L1934-L1992`): `addOns[]`, `addOnsAuto[]`, `showHUD…showGPS`
  (v8+), `randomSeed`, `class Intel`, `class Groups`, `class Vehicles` (empty), `class Markers`, `class Sensors`.
  Group: `side`, `class Vehicles`, `class Waypoints`, `class Sensors` (`#L1460-L1467`).
- Arrays of classes: `items=N; class Item0 {…}` (`P:IO/Serialization/ParamArchive.hpp#L403-L409`).
- **A key whose value equals its default is not written; a missing key loads as the default**
  (`ParamArchive.hpp#L49-L61`). This applies only to keys serialized *with* a default. Keys without one are
  always written and required on load: `position`, unit `id`/`side`/`vehicle`, group `side`, trigger `age`,
  marker `name`/`type` (`ArcadeTemplate.cpp#L363-L372`, `#L527`, `#L645-L648`, `#L1462`). Empty class
  arrays are omitted (`ParamArchive.hpp#L380-L381`). Enums are saved as the string names below
  (`ParamArchive.cpp#L484-L511`). Default-valued enums therefore never appear in CWR-written files
  (e.g. waypoint `type="MOVE"`, unit `special="FORM"`, trigger `activationBy="NONE"`), while
  `side="WEST"` always does. On load, enum names match case-insensitively, and an unknown enum
  string makes that key return `LSStructure` (`#L521-L529`). **Qualified in the consolidation pass
  (2026-09-27):** this text used to say the unknown string "fails the whole load". That holds only
  outside list items. The list loader ignores `SerializeArrayItem`'s return value, and `OnError`
  only records a context and writes an RPT line. So inside an `ItemN`, an unknown enum (or a
  missing required key) stops that item's remaining keys from being read. Those keys keep their
  `Init()` values, and the mission still loads with a half-default item (doc 04 §2.3,
  `ParamArchive.hpp#L406-L411`; doc 37 §10 design-gap candidate (b)) [V]. A missing root `version`
  key also fails the load (`ParamArchive.cpp#L590-L592`). Doc 04 §3 refines this: the result
  depends on the reader. The game's `ParseCutscene` fails the mission, while the editor ignores the
  result and silently loads nothing. Our validator must flag an in-item unknown enum or missing
  required key as an error, because the game swallows it (doc 04 §2.3). A Rust reader that is
  "permissive on unknown values" keeps the token as written instead of dropping the item's
  remaining keys.
  Defaults in the file format sometimes differ from in-memory `Init()` defaults (see §4 tables) — a
  round-trip-exact writer must use the *serialization* defaults.
- On save: `ScanRequiredAddons()` (units' `CfgPatches` owners → `addOnsAuto`, merged into `addOns`),
  `CheckSynchro()`, `Compact()`. On load: missing addons → `LSNoAddOn` and the load is aborted with a
  message; `nextVehId`/`nextSyncId` recomputed from max ids (`#L1910-L1932`, `#L1946-L1990`).
- User text (`description`, trigger `text`, marker `text`) is passed through legacy-codepage decoding
  on load (`DecodeMissionUserText`, `#L33-L36`).

## 4. Feature inventory

### 4.1 Main editor screen (`RscDisplayArcadeMap`, IDD 26) [V: P:Core/resincl.hpp#L678-L689, UIMapExtDisplay.cpp]

| IDC | Control | Behaviour |
| --- | --- | --- |
| 51 | Map | `CStaticMapArcade`, see §3.5/§4.3 |
| 104 | Mode toolbox | `_mode` = Units/Groups/Triggers/Waypoints/Synchronize/Markers (`#L712-L718`) |
| 101 / 106 | Load / Merge | `DisplayTemplateLoad(merge=false/true)`; Merge hidden in Easy (`#L511-L516`, `#L445-L449`) |
| 102 | Save | `DisplayTemplateSave` (name + export mode) |
| 103 | Clear | "Are you sure?" (IDD 202) → `_currentTemplate->Clear()`, mission name reset (`#L2329-L2350`) |
| 105 | Intel | `DisplayIntel` on current section's intel |
| 107 | Preview | visible iff `IsConsistent(nullptr, mp)` (MP: also needs a saved name) (`#L410-L427`) |
| 108 | Continue | visible iff SP and a preview world is running (`GWorld->GetMode()==GModeArcade`) |
| 109 | Section combo | Mission / Intro / Outro win / Outro lose; hidden in Easy (`#L450-L454`, `#L466-L473`); switching sections `#L675-L710` |
| 110 | Easy/Advanced active text | toggles, persisted as `advancedEditor` in `UserInfo.cfg`; CWR default **Advanced** (`#L63-L97`) |
| 111 | Show/Hide IDs | toggles static-object id labels; hidden (and forced off) in Easy |
| 112 | Show/Hide textures | toggles terrain texture layer (`_showScale` inverted; default textures hidden) |
| 2 | Exit | "Are you sure?" (IDD 203) → `Exit(IDC_CANCEL)` |
| 52–55 | Notebook | weather icon (overcast thresholds 0.2/0.4/0.6/0.8, `P:UI/Map/UIMapDisplay.cpp#L243-L265`), grid position of player, time, date (`P:UI/DisplayUIMenus.cpp#L1802-L1856`) |

English labels verified by test: Load, Save, Clear, Merge, Preview, Continue, Show Textures, Exit
(`R:tests/integration/ui/editor/arcade_map_language_switch.test.sqf#L51-L58`). Mode-toolbox strings come
from `$STR_DISP_ARCMAP_*` in Rsc (exact English text [U]). Layout positions: [U] (game data).

### 4.2 Modes [V: P:UI/Map/UIMap.hpp#L564-L573, P:UI/Map/UIMapExt.cpp#L1436-L1519]

| Key | `InsertMode` | Double-click on empty map inserts |
| --- | --- | --- |
| F1 | IMUnits | Unit dialog (pre-filled from last inserted unit) |
| F2 | IMGroups | Group dialog (`CfgGroups` preset); also enables drag-to-link |
| F3 | IMSensors | Trigger dialog |
| F4 | IMWaypoints | Waypoint for the group of the **last-clicked** unit/waypoint (nothing if none) |
| F5 | IMSynchronize | nothing; drag-to-sync only |
| F6 | IMMarkers | Marker dialog; markers only visible in this mode |

CWR added gamepad actions: previous/next tab cycles modes, a Preview action (`UIMapExtDisplay.cpp#L720-L772`).

### 4.3 Mouse & keyboard (editor map) [V: P:UI/Map/UIMapExt.cpp]

| Input | Effect | Code |
| --- | --- | --- |
| Hover | `_infoMove = FindSign()` → label drawn | `UIMap.cpp#L2333-L2339` |
| Hit-test | nearest item within `0.02·L·scale` (world m); strict `<` so search order only breaks ties: waypoints **first** (or **last** while Shift held — lets you pick a unit under its own waypoint), group units, group triggers, empty vehicles, free triggers, markers, buildings (`VehicleWithAI` of static type) | `#L1942-L2110` |
| Click | select item (clears others unless Ctrl); **Shift+click** on a group member/group trigger/waypoint selects the whole group | `#L2489-L2559` |
| Press on empty + drag | rubber-band; on release toggles selection of items inside (Ctrl keeps previous selection) | `#L2527-L2534`, `#L2414-L2486` |
| Drag (LMB held after click on an item) | move **all selected** items by the mouse delta, re-snapping Y to terrain | `#L2744-L2878` |
| **Shift+drag** | rotate selection around its centroid; units/triggers/markers also add the angle to azimuth/angle | `#L2777-L2791`, `ArcadeTemplate.cpp#L292-L308` |
| Drag in Groups mode | draws a link line; on release: unit→unit **join group**, unit→empty **leave group**, unit→trigger bind trigger to vehicle, unit↔marker add marker to unit's random-start list, trigger→static object bind to object, trigger→empty unbind/ungroup, static→trigger bind, marker→empty remove marker from all units | `#L2230-L2360` |
| Drag in Synchronize mode | waypoint→waypoint (different groups) **sync**; waypoint↔trigger sync; → empty clears that item's syncs | `#L2361-L2408` |
| Double-click | edit waypoint (any mode) > insert waypoint (Waypoints mode, on unit ⇒ `id`, on building ⇒ `idStatic`, else position) > edit trigger > edit marker > edit unit > mode-specific insert | `#L2561-L2742` |
| Del | delete the **hovered** item (unit delete re-selects leader / removes empty group) | `#L1520-L1587` |
| Shift+Del, Ctrl+X | cut selection | `#L1522-L1528`, `#L1606-L1615` |
| Ctrl+C, Ctrl+Ins | copy selection to a process-global clipboard template; remembers mouse world pos | `#L1168-L1247` |
| Ctrl+V, Shift+Ins | paste offset so the copy point lands under the mouse | `#L1249-L1262` |
| Ctrl+Shift+V | paste at original positions | `#L1264-L1268` |
| RMB drag | pan (`_moving`) | `UIMap.cpp#L2322-L2356` |
| Wheel | zoom `scale *= exp(0.1·dz)` around the cursor (CE: honours `MapZoomIn/Out` wheel bindings, `CE:UI/Map/UIMap.cpp#L2360`) | `UIMap.cpp#L2358-L2368`, `#L2496-L2523` |
| Numpad +/− | continuous zoom (actions `MapZoomIn/Out`, default KP+/KP−) | `UIMap.cpp#L2051-L2073`, `P:Input/InputSubsystem.cpp#L1270-L1271` |
| Numpad * | animate back to default zoom | `UIMap.cpp#L2244-L2259` |
| Numpad 1–4,6–9 | scroll | `UIMap.cpp#L2089-L2131`, `#L2224-L2243` |
| Numpad 5 | animated fly to the player (or island center) | `UIMapExt.cpp#L1405-L1435` |
| Esc | exit confirmation | `UIContainers.cpp#L1025-L1028` |
| Cursor | Track / Move (drag, rubber band) / Scroll (pan) / Arrow | `DisplayUIMenus.cpp#L1882-L1928` |

Not present in the original: undo/redo, snapping, zoom-to-selection, 3D placement [V by absence in these files].

### 4.4 Unit dialog (`RscDisplayArcadeUnit[Simple]`, IDD 27) [V: P:UI/Map/UIArcade.cpp]

Title "insert"/"edit" by `_index<0` (`#L809-L821`). Data: `ArcadeUnitInfo` (`P:AI/ArcadeTemplate.hpp#L19-L61`).

| IDC | Field → member | Values / range | Default (Init / file) | Code |
| --- | --- | --- | --- | --- |
| 102 | Side → `side` | West, East, Resistance, Civilian (+Logic, Empty only if non-playable); **disabled when editing** | WEST / required | `#L824-L874` |
| 107 | Class (vehicleClass) | distinct `CfgVehicles.vehicleClass` with `scope==2`, side match; empty side excludes Logic & `Man`-derived; types with no driver/gunner/commander seat are excluded for non-empty sides; "Men" first then A–Z; label `STR_DISP_ARCUNIT_CLASS_<NAME>` (CWR-added key [V]: the 9 `STR_DISP_ARCUNIT_CLASS_*` keys exist only in Remastered's editor stringtable, doc 35 §10) or raw name | — | `#L242-L355` |
| 103 | Unit → `vehicle` | `displayName` of matching classes, sorted | "" / required | `#L357-L453` |
| 104 | Rank → `rank` | Private…Colonel; hidden for Empty/Logic | PRIVATE / "PRIVATE" | `#L899-L914` |
| 105 | Control → `player` | Non-playable; Player (as commander/driver-or-pilot/gunner); Playable (C/D/G/CD/CG/DG/CDG, "pilot" wording for air); for men just Player/Playable; list depends on seats of the chosen type; the widest combination is stored as `PLAY CDG` | NONPLAY | `#L455-L803` |
| 112 | Special → `special` | None, In cargo, Flying, In formation | FORM / "FORM" | `#L923-L932` |
| 113 | Info age → `age` | Actual, 5, 10, 15, 30, 60, 120 min, Unknown | UNKNOWN | `#L939-L948` |
| 121 | Skill slider → `skill` | 0.2–1.0 | 0.6 / −1 ⇒ derive from rank (`RankToSkill`) | `#L949-L956`, `ArcadeTemplate.cpp#L213-L222`, `#L384`, `#L403-L406` |
| 108/109/110 | Health/Fuel/Ammo → `health/fuel/ammo` | 0–1 sliders | 1.0 | `#L957-L980` |
| 111 + 114 | Azimuth edit + compass picture → `azimut` | float degrees; clicking compass sets value rounded to 5° | 0 | `#L43-L107`, `#L915-L922` |
| 115 | Placement radius → `placement` | float metres (random start radius) | 0 | `#L995-L1002` |
| 116 | Probability of presence → `presence` | 0–1 slider | 1.0 | `#L981-L988` |
| 117 | Condition of presence → `presenceCondition` | boolean expression, validated | "true" | `#L989-L994`, `#L1115-L1125` |
| 118 | Name → `name` (file key `text`) | identifier (`IdtfGoodName`), unique vs units, triggers (case-insensitive) | "" | `#L1040-L1099` |
| 120 | Initialization → `init` | statement, validated with `CheckExecute` | "" | `#L1101-L1113` |
| 119 | Lock → `lock` | Unlocked, Default, Locked | DEFAULT | `#L1003-L1027` |

Behaviours: changing Side repopulates Class and Unit; changing Unit repopulates Control; choosing a
playable Control limits Side to the 4 real sides (`#L109-L221`). New-unit defaults: copy of the last
inserted unit, then position = click, name/init cleared, `player = PlayerCommander` if the mission has
no player yet else non-playable, health/fuel/ammo/presence = 1, placement 0 (`UIMapExt.cpp#L2703-L2740`).
On OK for a *new* unit: Empty ⇒ goes to `emptyVehicles`; otherwise joins the **nearest same-side group whose leader is
within 100 m**, else a new group (`ArcadeTemplateFind.cpp#L412-L471`). Non-editable fields also in the
struct: `markers[]` (random start markers, set via drag), `leader` (computed), `id`.
Easy mode (`RscDisplayArcadeUnitSimple`) drops 9 fields: rank, special, info age, placement,
presence, presence condition, name, lock and init. It adds none (doc 35 §10) [V].

### 4.5 Group dialog (`RscDisplayArcadeGroup`, IDD 40) [V: P:UI/Map/UIArcade.cpp#L1250-L1428]

Side → Type → Name cascading combos over `CfgGroups >> side >> type >> name` (display `name` key),
azimuth edit (104) + compass (105). Remembers last choice (`SetLastGroup`). On OK `AddGroup` creates one
unit per class entry: `side`, `vehicle`, `rank` (skill from rank), position = click + entry
`position[]` offset (index 0→X, 1→Z, 2→Y), then rotates the group by the azimuth
(`P:AI/ArcadeTemplateFind.cpp#L841-L874`, `P:UI/Map/UIMapExtDisplay.cpp#L2081-L2128`).

### 4.6 Waypoint dialog (`RscDisplayArcadeWaypoint[Simple]`, IDD 28) [V: P:UI/Map/UIArcadeWaypoint.cpp#L29-L445]

| IDC | Field → member | Values | Default (Init / file) |
| --- | --- | --- | --- |
| 102 | Type → `type` | MOVE, DESTROY, GETIN, SAD (seek & destroy), JOIN, LEADER (join & lead), GETOUT, CYCLE, LOAD, UNLOAD, TR UNLOAD, HOLD, SENTRY, GUARD, TALK, SCRIPTED, SUPPORT; Logic groups: AND, OR | in-memory UNDEF (dialog preselects first entry, MOVE) / file "MOVE" |
| 103 | Order (sequence) | "i: TYPE description" for existing + "n:" = append; re-inserts at chosen index | append |
| 104 | Description → `description` | text | "" |
| 105 | Combat mode → `combatMode` | No change, then 5 semaphores BLUE, GREEN, WHITE, YELLOW, RED | −1 / "NO CHANGE" |
| 106 | Formation → `formation` | No change, COLUMN, STAG COLUMN, WEDGE, ECH LEFT, ECH RIGHT, VEE, LINE | −1 |
| 107 | Speed → `speed` | UNCHANGED, LIMITED, NORMAL, FULL | UNCHANGED |
| 108 | Behaviour → `combat` | UNCHANGED, CARELESS, SAFE, AWARE, COMBAT, STEALTH | UNCHANGED |
| 109 | Placement radius → `placement` | float m | 0 |
| 111/113/112 | Timeout min / mid / max | float s | 0 |
| 114 (+115 label) | House position → `housePos` | only when bound to a building with path positions ("Position N") | −1 |
| 118 | Condition → `expCond` | bool expression, validated | "true" |
| 116 | On activation → `expActiv` | statement, validated | "" |
| 119 | Script → `script` | "file args" run by SCRIPTED waypoints (`P:AI/AIArcade.cpp#L996-L1035`) | "" |
| 117 | Show waypoint → `showWP` | NEVER, EASY (cadet only), ALWAYS | NEVER / file default **EASY** |
| 110 | Effects… button | opens Effects dialog (§4.8) | — |

Non-dialog members: `position`, `id` (bound unit), `idStatic` (bound building), `synchronizations[]`.
Enum names: `P:AI/ArcadeTemplate.cpp#L46-L100`, `P:AI/AICenter.cpp#L146-L171`.
Easy mode drops 11 fields, all expert or code fields, and adds none (doc 35 §10; the count only) [V].

### 4.7 Trigger dialog (`RscDisplayArcadeSensor[Simple]`, IDD 41) [V: P:UI/Map/UIArcade.cpp#L1430-L1934]

| IDC | Field → member | Values | Default |
| --- | --- | --- | --- |
| 102/103 | Axis a / b → `a`,`b` | float m | 50 / 50 |
| 104 | Angle → `angle` | float ° | 0 |
| 120 | Shape → `rectangular` | toolbox Ellipse(0) / Rectangle(1) | ellipse |
| 105 | Activation → `activationBy` | context-dependent: group-bound → "Group"; static-bound → "Static"; vehicle in group → Vehicle/Group/Leader/Member; empty vehicle → Vehicle; otherwise None, East, West, Resistance, Civilian, Logic, Anybody, Radio Alpha…Juliet | NONE |
| 106 | Presence → `activationType` | Present, Not present, Detected by West/East/Resistance/Civilians | PRESENT |
| 107 | Repeat → `repeating` | Once(0) / Repeatedly(1) | once |
| 108 | Countdown vs timeout → `interruptable` | toolbox 0/1 (label↔index mapping [U]; 1 ⇒ interruptable) | 0 |
| 109/111/110 | Timeout min / mid / max | float s | 0 |
| 112 | Type → `type` | None, Guarded by East/West/Resistance, Switch, End #1–#6, Lose (legacy "WIN" = END1) | NONE |
| 113 | Object → `object` | `CfgDetectors >> objects[]` (display names from `CfgNonAIVehicles`) | "EmptyDetector" |
| 114 | Text → `text` | label shown on map/radio | "" |
| 121 | Name → `name` | identifier, unique | "" |
| 117 | Condition → `expCond` | bool, validated | "this" |
| 118 / 119 | On activation / deactivation | statements, validated | "" |
| 115 | Info age → `age` | as units | UNKNOWN (file: always written) |
| 116 | Effects… | §4.8 | — |

Non-dialog: `idStatic`, `idVehicle` (set by drag-linking), `synchronizations[]`. Enum names
`P:AI/ArcadeTemplate.cpp#L149-L203`; defaults `#L446-L562`.
Easy mode drops 11 fields, all expert or code fields, and adds none (doc 35 §10; the count only) [V].

### 4.8 Effects dialog (`RscDisplayArcadeEffects[Simple]`, IDD 44) [V: P:UI/Map/UIArcadeMarker.cpp#L350-L1170]

Shared by waypoints and triggers (`ArcadeEffects`, `P:AI/Path/ArcadeWaypoint.hpp#L25-L59`).

| IDC | Field → member | Source list | Default |
| --- | --- | --- | --- |
| 113 | Condition → `condition` | expression (not validated) | "true" (pre-v9 `playerOnly` ⇒ "thisList") |
| 101 | Camera effect → `cameraEffect` | None(""), Terminate("$TERMINATE$"), `CfgCameraEffects >> Array` from config + campaign + mission `description.ext` | "" |
| 102 | Camera position → `cameraPosition` | 14 positions TOP…BACK TOP, BOTTOM (`P:World/Scene/Camera/CamEffects.hpp#L26-L39`) | BACK |
| 103 | Sound (2D) → `sound` | "$NONE$" + `CfgSounds` (3 sources) | "$NONE$" |
| 104 | Voice (3D) → `voice` | "" + `CfgSounds` | "" |
| 105 | Environment → `soundEnv` | "" + `CfgEnvSounds` | "" |
| 106 | Trigger sound → `soundDet` | "" + `CfgSFX` | "" |
| 107 | Music → `track` | "$NONE$", Silence "$STOP$", `CfgMusic` | "$NONE$" |
| 108 | Title type → `titleType` | NONE, OBJECT, RES, TEXT (Simple dialog forces TEXT) | NONE |
| 109 | Title effect → `titleEffect` | PLAIN, PLAIN DOWN, BLACK, BLACK FADED, BLACK OUT, BLACK IN, WHITE OUT, WHITE IN | PLAIN |
| 110/111/112 | Title text / `RscTitles` resource / `CfgTitles >> titles[]` object → `title` | shown by type; empty text ⇒ type NONE | "" |

Easy mode drops 9 fields, all expert or code fields, and adds none (doc 35 §10; the count only) [V].

### 4.9 Marker dialog (`RscDisplayArcadeMarker[Simple]`, IDD 45) [V: P:UI/Map/UIArcadeMarker.cpp#L18-L348]

| IDC | Field → member | Values | Default |
| --- | --- | --- | --- |
| 102 | Name → `name` | required, unique among markers | "" |
| 111 | Text → `text` | shown next to icon | "" |
| 103 | Shape → `markerType` | ICON, RECTANGLE, ELLIPSE | ICON |
| 104 (+109 label) | Icon → `type` | `CfgMarkers` (icon only) | "" |
| 105 | Color → `colorName` | `CfgMarkerColors`; "Default" = the icon's own `CfgMarkers.color` | "Default" |
| 110 | Fill → `fillName` | `CfgMarkerBrushes` (areas only; `texture` "" ⇒ 50 % alpha solid) | "Solid" |
| 106/107 | a / b | icon: scale factor; area: half-axes in m; switching shape ×/÷ 20 | 1 / 1 |
| 108 | Angle → `angle` | float ° | 0 |

Icon size in px = `CfgMarkers >> size` × a/b (`P:AI/ArcadeTemplate.cpp#L762-L798`, `UIMapExt.cpp#L909-L932`).
Easy mode drops 5 fields, all expert or code fields, and adds none (doc 35 §10; the count only) [V].

### 4.10 Intel dialog (`RscDisplayIntel[Simple]`, IDD 32) [V: P:UI/Map/UIArcadeWaypoint.cpp#L589-L830]

| IDC | Field → `ArcadeIntel` | Values | Default / file key |
| --- | --- | --- | --- |
| 102/103 | Month / Day | Jan–Dec; 1..days (leap-aware) | 5 / 10 (`month`, `day`) |
| 104/105 | Hour / Minute | 0–23; 00–55 step 5 | 7 / 30 |
| — | Year | **not editable in the dialog** | 1985 (`year`) |
| 108/110 | Weather now / forecast | slider shows `1 − overcast` | 0.5 (`startWeather`, `forecastWeather`) |
| 109/111 | Fog now / forecast | 0–1 | 0 (`startFog`, `forecastFog`) |
| 101 | Resistance friendly to | toolbox: nobody / West / East / both → `friends[GUER][WEST/EAST]` | West (`resistanceWest=1`, `resistanceEast=0`) |
| 106/107 | Mission name / description | text (`briefingName`, `briefingDescription`) | "" |

Serialization `P:AI/ArcadeTemplate.cpp#L1474-L1539`. Intel is per section; the notebook date/weather
widgets follow the current section (`UIMapExtDisplay.cpp#L334-L377`).
Easy mode drops 2 fields, all expert or code fields, and adds none (doc 35 §10; the count only) [V].

### 4.11 Load / Save / Merge / Clear / Export [V: P:UI/Map/UIMapExtDisplay.cpp, UIArcadeWaypoint.cpp#L447-L578]

- **Folder layout:** `<missionsBase>/missions/<name>.<world>/mission.sqm` (SP) or
  `…/mpmissions/…` (MP). CWR moved user missions to a non-roaming "user content" dir (Documents) unless
  old-paths mode (`P:UI/OptionsUI.cpp#L129-L141`, `#L191-L200`) — retail location differs [I].
- **Save dialog (IDD 29):** name (defaults to current), mode combo: *User mission* (folder only),
  *Export to single missions* (PBO → `Missions\<name>.<world>.pbo`), *Export to multiplayer*
  (PBO → MPMissions path), *Send by e-mail* (now a logged no-op) (`#L2190-L2264`, `#L2011-L2019`).
  PBO packing uses `FileBankManager::Create(file, dir, true)`.
- **Load dialog (IDD 30):** island combo (worlds with existing `.wrp`), name combo filled by scanning
  `<missionsDir>/*.<island>` directories; loading another island calls `SwitchLandscape` and rebuilds
  the static-object list (`#L2265-L2319`). Binary (rapified) `mission.sqm` is rejected
  (`#L137-L143`). Read-only files warn. Missing addons abort the load with a list of names.
- **Merge:** same dialog, merges all 4 sections at zero offset; conflicting marker/unit/trigger names
  get `_1`, `_2`… suffixes, merged units lose player/playable status, ids and sync ids are shifted
  (`P:AI/ArcadeTemplateFind.cpp#L1086-L1310`). Clipboard paste uses the same `Merge`.
- **Clear:** clears only the current section's template.
- **Exit with OK path** (MP editor) requires `IsConsistent` (`#L2364-L2379`).

### 4.12 Preview and Continue — internals [V: P:UI/Map/UIMapExtDisplay.cpp#L529-L622, #L2021-L2056]

1. Re-entrancy guard `_running`; `_currentTemplate->IsConsistent(this, mp)` (shows error box on failure);
   `ScanRequiredAddons()`.
2. **MP editor:** save to `<MPMissions>/<name>.<world>/mission.sqm`, `Exit(IDC_OK)` — the server flow
   launches the session.
3. **SP:** `CurrentTemplate = *_currentTemplate` (global used by the game), `_alwaysShow=false`, delete
   `weapons.cfg`, then `GWorld->SwitchLandscape(world)`, `ActivateAddons(addOns)`,
   `InitGeneral(intel)` (weather, fog, clock, sun — `P:World/WorldInit.cpp#L242-L268`).
4. Section *Mission*: `GStats.ClearAll()`, `InitVehicles(GModeArcade, CurrentTemplate)`; delete
   `continue.fps`/`autosave.fps`/`save.fps`; if **Shift held and a briefing HTML exists** →
   `DisplayGetReady` (briefing, then mission) else `DisplayMission(this, editor=true)` (IDD 46).
   Other sections: `InitVehicles(GModeIntro)` → `DisplayIntro(noInit)`.
5. `InitVehicles` (`P:World/WorldInit.cpp#L448-L764`): loading screen (`RscDisplayLoadMission`, texts from
   `description.ext onLoadMission*`), player side, `CreateCenter` for East/West/Resistance/Civilian/Logic,
   `center->Init(template)`, `InitNoCenters` (empty vehicles, free triggers, markers [I]), run every unit
   `init` with `this` bound, run `init.sqs` (arcade mode), `InitUnits`, sensors, preload.
6. On return: IDD_MISSION → debriefing unless `description.ext debriefing=0`; then `_alwaysShow=true`,
   `ShowButtons()` — editor reappears with the world still in `GModeArcade`, which enables **Continue**
   (`DisplayMission(this)` resumes the same simulation, `#L615-L622`).

- Automated test proof: Preview (IDC 107) → display 46 (`R:tests/integration/ui/editor/editor_unit_and_preview.test.sqf#L33-L38`).
- **The external `--autotest` path is not the same as in-editor Preview** [V: `P:UI/DisplayUIMenus.cpp#L2012-L2066`,
  `P:UI/Map/UIArcadeWaypoint.cpp#L920-L988`]:
  - `StartAutoTest` re-parses `mission.sqm` from disk through `ParseCutscene`, which tries the binary
    loader first, so rapified files work here.
  - It requires ≥1 group and `IsConsistent`, otherwise it falls back to the `Intro` section.
  - It never plays `OutroWin`/`OutroLoose` and never shows `DisplayGetReady` (no briefing).
  - It opens `DisplayMission(options)` without the editor flag.
  - Alternative: `--test-mission <folder|mission.sqm>` ("Run mission folder or mission.sqm directly
    and exit", Dev visibility) copies the mission into an isolated stage root and forces AutoTest
    (`P:Foundation/Platform/AppConfig.cpp#L668-L670`, `R:apps/cwr/Game/GameApplication.cpp#L165-L187`,
    `#L1702-L1719`). Runtime behaviour is [U].

### 4.13 Other features

- **Validation** [V]: group crew seats (driver+commander+gunner per unit type) ≤ `MAX_UNITS_PER_GROUP`=12
  (`P:AI/Path/AITypes.hpp#L31`); SP needs a player (0 ⇒ error box, check skipped in cheat builds;
  more than 1 is prevented by `UnitUpdate` and only asserted); groups per side ≤
  `MaxGroups` = `|GroupNameList.letters| × |GroupColorList.colors|` from `CfgWorlds`
  (`P:Core/Config/Configuration.cpp#L339-L348`, `P:AI/ArcadeTemplate.cpp#L1754-L1860`). Script checks use
  `GameState::CheckExecute/CheckEvaluateBool` = full evaluator in check-only mode, errors report caret
  position (`R:engine/Evaluator/express.cpp#L3067-L3092`); names use `IdtfGoodName`: first char
  `isalpha || '_'`, the rest `isalnum || '_'`. **There is no reserved-word or command-name check**, because
  `VarGoodName` returns `true` unconditionally (`#L152-L160`, `#L2795-L2814`). Uniqueness is case-insensitive
  across units, empty vehicles and triggers, not markers (`P:UI/Map/UIArcade.cpp#L1040-L1099`, `#L1752-L1809`).
- **Addons**: using a class from an unregistered addon adds it to `addOns` (`UIMapExtDisplay.cpp#L2003-L2007`).
- **Language switch at runtime** (CWR addition): `RefreshLanguage` (`#L2392-L2421`).
- **Cheat/dev-only** (`_ENABLE_CHEATS`): export template to an SQF script `mission.sqf` from
  `Editor\*.hpp` templates (`#L774-L1991`) — a useful blueprint for "mission → script" generation;
  copy cursor world position to `clipboard.txt`; export map as EMF (`P:UI/Map/UIMapExport.cpp`).
- **MP briefing editing**: `GetMode()` has an `IDD_INTEL_GETREADY` branch (waypoint-only mode), but no caller builds
  a limited-rights map [V by grep].

## 5. CWR vs CWR-CE (editor scope) [V: file hashes + `git diff --no-index`]

Identical: `UIArcade.cpp`, `UIArcadeMarker.cpp`, `UIMapExt.cpp`, `UIMap.hpp`, `UIMapBase.hpp`,
`ArcadeTemplateFind.cpp`, `ArcadeWaypoint.hpp`, `resincl.hpp`, `WorldInit.cpp`, `UIMapDialogs.cpp`,
`UIMapExport.cpp`. Different:

- `ArcadeTemplate.hpp/.cpp`, `UIMapExtDisplay.cpp`, `UIArcadeWaypoint.cpp`: missing-addon message
  deduplicated/sorted via new `MissingAddonMessage`, `FindMissingAddons`, `ReadMissionAddons`
  (`CE:AI/ArcadeTemplate.hpp#L255-L260`, `CE:AI/ArcadeTemplate.cpp#L1938`). Behaviour-equivalent otherwise.
- `UIMap.cpp`: crosshair sizing via `LayoutCanvas`/`CursorLayout`; wheel zoom only when the wheel is
  bound to `MapZoomIn/Out` (`CE:UI/Map/UIMap.cpp#L2360`).
- `UIContainers.cpp`: cursor rectangle computed by `CursorLayout` (aspect-correct).
- Editor-adjacent files outside that set, checked on 2026-09-26 [V by `git diff --no-index`]. Identical:
  `ParamArchive.*`, `SaveVersion.hpp`, `WorldImpl.cpp`, `DisplayUIMenus.cpp`, `express.cpp`,
  `Configuration.cpp`, `AITypes.hpp`, `AICenter.cpp`, `apps/cwr/Game/GameApplication.cpp`. Trivially
  different:
  - `AppConfig.cpp` changes one `--duration` help string.
  - `OptionsUIApp.cpp` changes only the mods-download UI.
  - `OptionsUI.cpp` `CreatePath` normalizes `\` to `/`.
  - `ConfigParsers.cpp` sets `resource-extra` base classes and fails on a bad `resource.cpp`.
  - `Input/InputSubsystem.cpp` binds the mouse wheel to `MapZoomIn/Out` by default
    (`CE:Input/InputSubsystem.cpp#L1286-L1289`).

Conclusion: for the editor, either repo is authoritative; prefer CWR for citations (upstream) and
watch CE for bug fixes [I].

## 6. Engine subsystems the editor depends on (standalone must re-implement or substitute)

| Subsystem | Used for | Where in engine | Standalone strategy |
| --- | --- | --- | --- |
| Config parser (text `config.cpp` + binarized/rapified `.bin`, class inheritance, `>>` lookup, arrays) | every combo list, icons, colors, groups | `P:IO/ParamFile/*`, `Pars`, `Res` | Pure Rust parser over `&[u8]` (both forms); inheritance resolution. |
| `CfgVehicles` (scope, side, vehicleClass, displayName, icon, mapSize, hasDriver/Gunner/Commander, simulation, crew, `Man`/`Air` ancestry) | unit dialog, icons, seat logic, validation | `UIArcade.cpp#L242-L803` | Build an index at load. |
| `CfgGroups`, `CfgMarkers`, `CfgMarkerColors`, `CfgMarkerBrushes`, `CfgDetectors`, `CfgNonAIVehicles`, `CfgSounds`, `CfgEnvSounds`, `CfgSFX`, `CfgMusic`, `CfgCameraEffects`, `CfgTitles`, `RscTitles`, `CfgPatches`, `CfgWorlds`/`CfgWorldList`, `CfgInGameUI>>IslandMap` | dialogs, map | §4 | Same parser; also parse mission/campaign `description.ext` for custom sounds/music/titles/camera effects. |
| Resource config `RscDisplay*` + fonts + control types | pixel layout of every screen | `UIContainers.cpp#L322-L599` | Either interpret the user's `resource.*` at runtime (max fidelity) or hand-author layouts; fonts need BI font decoding [U format]. |
| String table | all labels (`IDS_*`→`STR_*`, `P:IO/Serialization/StringIds.hpp`) | `LocalizeString` | Parse installed stringtable; ship English fallbacks we author ourselves. |
| PBO archive read/write | addons/data; Export | `FileBankManager` | Rust PBO reader/writer. |
| Textures (PAA/PAC) | unit/marker icons, fills, map paper, weather icons | `GlobLoadTexture` | Decoder crate/module. |
| Landscape (WRP) + object shapes (P3D map type, bounding box, ids, house path positions) | map layers, heights (`RoadSurfaceY`), building ids, waypoint house positions, Show IDs | `UIMap.cpp#L743-L1719`, `UIArcadeWaypoint.cpp#L236-L284` | WRP reader + minimal P3D reader (map type, min/max, paths LOD). Road-surface height ≈ terrain height + road model [I]. |
| Grid formatting (`GetGridInfo`, grid offsets, `PositionToAA11`) | grid labels, notebook position | `P:UI/Map/UIMap.cpp#L191-L228`, `#L1971-L2045` | Port formulas; config-driven per world. |
| SQS/SQF evaluator (check-only) + command table + `IdtfGoodName` | field validation, error caret | `R:engine/Evaluator/express.cpp` | Port a parser/type-checker with a command signature table; must accept everything the game accepts (permissive). |
| ParamArchive semantics | `mission.sqm` I/O | `P:IO/Serialization/ParamArchive.*` | Pure writer/reader honouring defaults-omission, enum strings, `items`/`ItemN`, version gates. |
| Game launch | Preview | `StartAutoTest` | Spawn game binary with `…/<name>.<world>/mission.sqm` (+ `--autotest` on CWR); no briefing/Outro preview, Continue has no equivalent [I]. |
| Addon registry (`CfgPatches` owner of classes) | `addOns`/`addOnsAuto` | `ArcadeTemplate.cpp#L321-L352`, `#L1875-L1932` | Track owning addon per class while merging configs. |

## 7. Porting checklist (dependency order)

1. **Primitives & enums**: newtypes for vehicle id / sync id / group & item indices; all enums with
   their exact file strings incl. legacy aliases (`P:AI/ArcadeTemplate.cpp#L38-L211`,
   `P:AI/AICenter.cpp#L146-L181`, `P:World/Scene/Object.cpp#L53-L62` (sides: WEST, EAST, GUER, CIV,
   LOGIC, EMPTY; the table also has UNKNOWN, ENEMY, FRIENDLY), `P:World/Scene/Camera/CamEffects.cpp#L31-L48`, `P:Game/TitEffects.cpp#L35-L48`).
2. **Config-syntax lexer/parser** (text) → generic tree; later rapified-binary reader.
3. **`mission.sqm` codec**: reader (versions ≤ 11, legacy keys `locked`, `playerOnly`, `show`,
   `resistance`, shared pre-v7 `Intel`) and writer (defaults omitted) + golden round-trip tests on
   synthetic fixtures.
4. **Template model + mutations**: port `ArcadeTemplateFind.cpp` semantics (UnitUpdate grouping rule,
   SelectLeader, Compact, CheckSynchro, Merge renaming, sensor re-parenting) as pure functions with tests.
5. **Consistency & name validation** (`IsConsistent`, uniqueness, `IdtfGoodName`).
6. **Game-data catalog**: `Cfg*` indexes (from user install, never committed), stringtable, `description.ext`.
7. **Map viewport math**: `WorldToScreen`, zoom around cursor, saturation, pan, keypad scroll, animations.
8. **Hit-testing & selection state machine**: `FindSign` priorities, click/double-click/drag timing
   (0.3 s, 0.01 move), rubber band, Ctrl/Shift modifiers, mode-dependent drag-link actions, clipboard.
9. **Overlay renderer** (template layer, §3.5 order, colors from `IslandMap`) on a blank/placeholder background.
10. **Dialogs** as data-driven forms (field tables in §4) with the cascade logic (side→class→unit→control).
11. **Script checker** for conditions/statements (initially syntax-only, then command signatures).
12. **Landscape background**: WRP heights/contours, sea, forests, roads, objects, names, grid; then
    "Show textures" and "Show IDs".
13. **Visual fidelity pass**: interpret `RscDisplay*` classes, BI fonts, PAA icons; Easy/Advanced variants.
14. **Save/Export**: folder layout, PBO writer, MP variants.
15. **Preview**: write mission, spawn game, detect binary/version, fallbacks.
16. **Community extras** (undo, snapping, search, …) and the AI harness on top of step 4's API.

## 8. Quirks worth preserving or deciding on deliberately

- Serialization defaults ≠ in-memory defaults: waypoint `type` (UNDEF vs file MOVE), `showWP` (NEVER vs
  file EASY), unit `skill` (0.6 vs file −1 ⇒ rank-derived) [V: `ArcadeTemplate.cpp#L1033-L1120`, `#L276`, `#L384`].
- Placing a unit within 100 m of a same-side leader silently joins that group [V].
- Del acts on the hovered item, not the selection; Shift+Del acts on the selection [V].
- Markers are invisible outside Markers mode yet still hit-testable (can be deleted/linked) [V].
- Side cannot be changed after insertion (combo disabled) [V].
- Year is not exposed in Intel; weather slider is inverted (`1 − overcast`) [V].
- The Order combo re-sorts waypoints; waypoint ids in the file are array positions [V].
- Text-only `mission.sqm` load: rapified files are rejected by the editor path (`LoadTemplates`) [V].

## Open questions

- Exact Rsc layouts (positions, sizes, fonts, colors) and toolbox label texts need a legally
  obtained `resource.*` from an install to inspect [U]. *Partly answered (consolidation pass,
  2026-09-27):* which fields each `…Simple` dialog omits is now [V] from doc 35 §10 (see §3.2).
  Only the Unit dialog's dropped field names are listed; the names for the other five dialogs
  are still open.
- Retail CWA 1.99 vs CWR differences in editor defaults (e.g. Easy vs Advanced default, user mission
  folder) — only CWR source was read [U].
- Does the retail/Steam CWR build accept `--autotest <mission.sqm>` for players (flag is tagged
  "Dev" visibility in help) and does it return to desktop when the preview ends? Source says it quits
  on abort (`P:UI/OptionsUIApp.cpp#L961-L964`) [I]; needs a runtime test.
- Label↔index mapping of the trigger Countdown/Timeout toolbox (IDC 108) [U].
- Exact `InitNoCenters` handling of empty vehicles/markers/free triggers (not read in full) [I].
- Font and texture container formats (BI `.fxy`/PAA variants) — out of this note's scope [U].

## Sources

Code (all at pinned commits; shorthand expanded):

- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMap.hpp#L1-L1112
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapBase.hpp#L1-L392
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMap.cpp#L200-L2530
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapExt.cpp#L1-L2933
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapExtDisplay.cpp#L1-L2422
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcade.cpp#L1-L1936
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcadeWaypoint.cpp#L1-L990
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcadeMarker.cpp#L1-L1172
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIContainers.cpp#L322-L1106
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapDisplay.cpp#L243-L265
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.hpp#L1-L255
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.cpp#L1-L1994
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplateFind.cpp#L180-L1329
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/Path/ArcadeWaypoint.hpp#L1-L309
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L996-L1035
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenter.cpp#L146-L181
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/Path/AITypes.hpp#L31
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Core/resincl.hpp#L165-L857
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Core/SaveVersion.hpp#L9-L12
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Core/Config/Configuration.cpp#L339-L348
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/IO/Serialization/ParamArchive.hpp#L49-L158
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/IO/Serialization/ParamArchive.cpp#L323-L353
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/IO/Serialization/ParamArchive.cpp#L484-L524
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Asset/Addon/ConfigParsers.cpp#L242-L261
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/DisplayUIMenus.cpp#L1791-L2066
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/DisplayUI.cpp#L1193-L1315
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/DisplayUIMultiplayer.cpp#L2418-L2440
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/OptionsUIApp.cpp#L800-L849
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/OptionsUIApp.cpp#L961-L964
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/OptionsUIApp.cpp#L1232-L1237
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/OptionsUI.cpp#L129-L200
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/WorldInit.cpp#L242-L764
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/WorldImpl.cpp#L2217-L2258
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Foundation/Platform/AppConfig.cpp#L627-L764
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Foundation/Platform/AppConfig.cpp#L1132-L1137
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Input/InputSubsystem.cpp#L1270-L1271
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Scene/Camera/CamEffects.hpp#L26-L39
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Game/TitEffects.hpp#L15-L21
- BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/express.cpp#L2800-L2814
- BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/express.cpp#L3067-L3092
- BohemiaInteractive/CWR@ffc61838b7:README.md#L1-L80
- BohemiaInteractive/CWR@ffc61838b7:tests/integration/ui/editor/arcade_map_language_switch.test.sqf#L1-L66
- BohemiaInteractive/CWR@ffc61838b7:tests/integration/ui/editor/editor_mission_save_load.test.sqf#L1-L80
- BohemiaInteractive/CWR@ffc61838b7:tests/integration/ui/editor/editor_unit_and_preview.test.sqf#L1-L84
- BohemiaInteractive/CWR@ffc61838b7:tests/unit/engine/Poseidon/Game/test_editor.cpp#L1-L10
- ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/AI/ArcadeTemplate.hpp#L255-L260
- ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/AI/ArcadeTemplate.cpp#L1879-L1970
- ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/UI/Map/UIMap.cpp#L2360-L2380
- ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/UI/Map/UIMapExtDisplay.cpp#L43-L220
- ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/Foundation/Platform/AppConfig.cpp#L627-L764
- ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/Input/InputSubsystem.cpp#L1286-L1289
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Game/Mission/MissionPathLoader.hpp#L28-L88
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcadeWaypoint.cpp#L904-L988
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Foundation/Platform/AppConfig.cpp#L668-L670
- BohemiaInteractive/CWR@ffc61838b7:apps/cwr/Game/GameApplication.cpp#L165-L187
- BohemiaInteractive/CWR@ffc61838b7:apps/cwr/Game/GameApplication.cpp#L1697-L1734
- BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/express.cpp#L152-L160
- BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/IO/Serialization/ParamArchive.cpp#L584-L634

Web:

- OFPEC, "Mission Editor Interface (OFP)" — layout of mode bar, Intel, Load/Save/Merge/Clear, Preview/Continue, Show IDs/Textures, Easy vs Advanced: <https://www.ofpec.com/tutorials/index.php?action=read&id=38>
- Bohemia Interactive Community, "Operation Flashpoint: Elite: Mission Editor": <https://community.bistudio.com/wiki/Operation_Flashpoint:_Elite:_Mission_Editor> (unverified: returned HTTP 403 on 2026-09-26)
- Arma Public License Share Alike (game data licence referenced by the CWR README): <https://www.bohemia.net/community/licenses/arma-public-license-share-alike>

## Verification notes

2026-09-26, adversarial fact-check against the local clones at the pinned SHAs. CWR-CE's commit is
authored 2026-07-27 and committed 2026-09-21. The CWR commit "3.05" is dated 2026-08-18.

**Checked and confirmed:**

- Rsc/Cfg/stringtable data absent from the repo: a grep for `RscDisplayArcadeMap` finds only the
  C++ `Load()` call, and `ParseResource` resolves `resource.cpp`/`.bin` from the bin dir.
- README game-data and APL-SA wording, and the APL-SA terms (fetched).
- `MissionsVersion = 11`, `SerializeAll`'s four sections, pre-v7 shared `Intel` and `Intel` minVersion 7.
- `PARS_4_TO_3` default omission, enum string tables (incl. "PLAYER COMMANDER", "FORM", "MOVE", "NONE"),
  and `items`/`ItemN`.
- Serialization vs `Init()` defaults (waypoint type, `showWP`, skill).
- Binary-mission rejection (`#L137-L143`).
- CLI flags `--autotest` (all builds, Dev help) and positional `mission`, `StartIntro` dispatch,
  `StartAutoTest`, and quit-on-abort.
- F1–F6 handlers, Del/clipboard keys, `FindSign` order and radius, and the double-click priority.
- Drag/rotate code, the 100 m auto-join (`<=`, XZ distance), `SelectLeader` (first max rank wins),
  crew-seat count vs 12, and `MaxGroups`.
- `CheckExecute`/`CheckEvaluateBool` in every dialog, `DefaultAdvancedEditorMode()==true`, and the
  Easy-mode hides.
- `RoadSurfaceY*` on insert/move/rotate, markers drawn only in `IMMarkers` but always hit-tested, and
  the side combo disabled on edit.
- `ERFull` as the only construction, IDD/IDC numbers, and the 0.3 s / 0.01 click timing.
- The 6-line label cap, Intel defaults and the inverted weather slider, and the CE diffs of the 17 listed
  files (hashes and diffs).

**Changed:**

- `IdtfGoodName` has no reserved-name check. The old text was wrong.
- The launch path must be `<name>.<world>/mission.sqm`, and `.pbo` is not dispatched.
- Added the `--autotest` vs in-editor Preview differences and the `--test-mission` alternative.
- Clarified which keys are always written, that empty arrays are omitted, and that enum loading is
  strict (unknown name ⇒ load fails). The consolidation pass below narrows the strictness to the
  top level, because items are lenient.
- Noted that the example default enums are never written by CWR.
- Corrected line counts (`UIMap.cpp`, `UIContainers.cpp`, `ArcadeTemplateFind.cpp`), the
  `CamEffects.cpp` range, the Easy-mode section-combo citation, and the contour density basis.
- Added the CE differences outside the 17 files.
- Scoped the APL-SA coverage of UI config to [I].
- Marked the BIKI source unverified.

**Not re-verified:** retail CWA 1.99 behaviour, runtime behaviour of `--autotest`/`--test-mission`,
and exact Rsc layouts. These still need game data or a runtime test.

### Consolidation pass (2026-09-27)

Cross-doc corrections applied. Each one was checked against its source doc before it was applied.

- **C35-03 (doc 35 §10, Doc 03 item; doc 35 §5.8).**
  - Easy-mode `…Simple` omissions went from [U] to [V] in §3.2.
  - Added per-dialog notes: the Unit field names in §4.4, and counts only in §4.6–§4.10.
  - The TL;DR now says the twins only drop fields.
  - The open question is marked partly answered.
  - `STR_DISP_ARCUNIT_CLASS_*` in §4.4 went from [I] to [V].
  - §3.3 now names the template wizard as the reference for "New mission from template".
  - Evidence: doc 35 §10 states the Simple counts [V], and its verification notes confirm that
    this doc marked the class-name key [I].
  - Doc 35 lists field names only for the Unit dialog, so the other names remain open (as doc 37
    open question 8 also notes).
- **C37-03 (doc 37 §10, design-gap candidate (b); doc 04 §2.3).**
  - §3.7 and the TL;DR no longer say an unknown enum fails the whole load. It fails its key; inside
    an `ItemN` the failure is only logged, and the item half-loads with `Init()` values.
  - Evidence: doc 04 §2.3 [V] and doc 37's engine review ("item-level leniency: return value
    ignored; `OnError` only records a context, plus an RPT line") [V].
  - The original sentence is kept, marked as qualified.
  - A pointer to doc 04 §3 was added for the adjacent missing-`version` sentence, which doc 04
    finds reader-dependent. This goes slightly beyond the correction as listed, so it is a pointer
    only and the sentence was not rewritten.
  - The design-gap request for (b) is still to be filed under `docs/design-gap-requests/` with
    doc 37's other candidates. That folder does not exist yet, and this pass did not create it.
  - *Supersedes the bullet above (verification step, 2026-09-27).* The folder now exists
    (`docs/design-gap-requests/README.md`). Its index treats (b) as a factual correction, already
    applied here, not as a request; only doc 37's candidate (g) was filed (DG003). Nothing in this
    doc waits on a design-gap request for (b).
- **Renames.** This doc has no mention of the concept manual, the live tutorials, doc 33's path
  or `skills/field-manual`, so it needed no Standing Orders / Drill edits.
- **Not re-verified here:** the engine source itself. No local clone at the pinned SHAs was
  available in this pass, so both corrections rest on the [V] findings of docs 04, 35 and 37.
