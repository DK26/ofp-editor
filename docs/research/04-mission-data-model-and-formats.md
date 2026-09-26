# Mission Data Model and Mission File Formats (OFP / CWA / CWR)

Research note 04 for the `ofp-editor` project: a standalone Rust re-implementation of the
"Arma: Cold War Assault" (CWA, formerly "Operation Flashpoint: Cold War Crisis", OFP) in-game
Mission Editor. This file stands alone: it explains every file a mission consists of, the exact
`mission.sqm` schema as the engine reads and writes it, the side files the engine consumes, where
missions live, how they are exported, which game-config catalogs the editor lists, and a proposed
Rust data model with a byte-exact round-trip strategy.

## TL;DR

- **One schema, four sections.** `mission.sqm` is a config ("ParamFile") file: `version=11;` then
  `class Mission`, `class Intro`, `class OutroWin`, `class OutroLoose`. Each section is one
  `ArcadeTemplate` (Intel, Groups, empty Vehicles, Markers, Sensors = triggers). [V] CWR also
  reads an extra `Mission>>Intel>>viewDistance` key raw, which its own editor never writes and
  drops on re-save (§3.2). [V]
- **The engine omits keys whose value equals the default.** It always writes required keys and
  the `Intel` and `Effects` classes, and it drops empty arrays and lists. Floats are written with
  printf `%f`, ints with `%d`, bools as `0`/`1` and strings as `"..."` with `""` escaping. Lines
  end in CRLF and indentation uses tabs. [V]
- **Reading is strict at the top and lenient inside items.** An unknown enum token or a missing
  required key fails the key. Inside `ItemN` classes those failures are logged and swallowed, so
  the game silently keeps a half-default unit. Our validator must flag these as errors. [V]
- **Text vs binary.** The in-game editor saves only text and refuses binarized (`\0raP`)
  `mission.sqm`. The game tries binary first, then text. The OFP binary layout (string pool plus
  varints) is fully specified in source. [V]
- **Our IDs are not the file's IDs.** The engine renumbers unit `id`s and synchronization IDs
  densely on every load and save (`Compact`), and it drops dangling synchronizations
  (`CheckSynchro`). Do not treat `id` as stable identity. [V]
- **CWR and CWR-CE share the same mission serialization code.** CE differs only in the wording of
  missing-addon messages and in stringtable fallback. [V] CWR adds UTF-8 files
  (`stringtable.utf8.csv`, `briefing.<Lang>.utf8.html`), `init.sqf`, `initServer.sqs` and
  similar scripts, `joinInProgress` and `CfgRemoteExec`. OFP 1.96 and CWA 1.99 will ignore these
  or misrender them. [V for CWR; I for OFP]
- **Encoding hazard.** CWR's editor decodes marker text, trigger text and waypoint descriptions
  from legacy code pages to UTF-8 on load, so re-saving can silently change bytes. It also expands
  `$STR_…` values at read time. Our editor must treat strings as raw bytes. [V/I]
- **Recommendation: a three-layer design in pure-Rust crates.**
  1. A lossless concrete syntax tree (CST) of the config file, where render(parse(b)) == b.
  2. A typed mission "lens" with newtype IDs and `Other(RawToken)` enum arms that keep the
     original spelling.
  3. An engine-strict validator, plus an optional "normalize like the engine" writer profile.
- **Tests use synthetic fixtures only:** hand-authored `.sqm` files and generated
  `.sqm`/raP/PBO fixtures, property-based identity round trips and fuzzing. Tests against a real
  mission corpus run only as an opt-in local job gated by an environment variable, and nothing
  proprietary is ever committed.

## 0. Scope, pinned sources, legend

Code citations use these aliases:
- `CWR:` means `BohemiaInteractive/CWR@ffc61838b7:`
- `CE:` means `ofpisnotdead-com/CWR-CE@b67bf3bd62:`
- `IC:` means `iron-curtain-engine/iron-curtain@7b7fac7fa5:`

CWR is the GPL-3.0-or-later release of the CWA Remastered engine ("Poseidon"), version string
`3.05` (`CWR:engine/Poseidon/Foundation/Platform/VersionNo.h#L1-L3`). CE is its community
continuation.

**Epistemic legend:**

| Tag | Meaning |
|---|---|
| **[V]** | Verified in source at the pinned commit |
| **[V-ext]** | Verified against an external artifact (URL given) |
| **[I]** | Inferred (reasoning is given) |
| **[U]** | Unknown / unverified |

The BIKI wiki (community.bistudio.com) returned HTTP 403 to automated fetches during this
research, so no BIKI claim below is marked verified.

**Glossary:**
- **ParamFile / config:** BI's hierarchical `class X { key=value; arr[]={...}; };` format. The
  same parser reads `mission.sqm`, `description.ext` and `config.cpp`.
- **ParamArchive:** the reflection layer that maps C++ structs to config entries. It has a
  `minVersion` per key and an optional default.
- **ArcadeTemplate:** one mission section.
- **Sensor:** a trigger.
- **Sync:** a synchronization link, expressed as a shared integer.
- **raP / binarized:** the binary form of a config file.
- **PBO:** BI's archive format ("file bank").
- **Island / world:** a terrain, named by the key of its `CfgWorlds` class (e.g. `Eden`,
  `Abel`, `Cain`, `Noe`, `Intro`).

## 1. Mission folder anatomy

A mission is a directory named `<missionName>.<worldName>`. The world is found by splitting the
name at the first `.` (`CWR:engine/Poseidon/UI/Map/UIArcadeWaypoint.cpp#L870-L897`). A mission may
also be packed into a same-named `.pbo`.

| File | Read by | Purpose | Notes |
|---|---|---|---|
| `mission.sqm` | Editor (text only). Game: `LoadBin` first, then text (`CWR:engine/Poseidon/UI/Map/UIArcadeWaypoint.cpp#L920-L988`) | Placed entities, 4 sections | [V] Required. |
| `description.ext` | `SetMission` → `ExtParsMission.Parse` (`CWR:engine/Poseidon/UI/OptionsUI.cpp#L855-L879`) | Mission-level config: sounds, music, respawn, HUD flags, identities, dialogs | [V] Optional. Preprocessed like any config. |
| `stringtable.csv` | `LoadStringtable("Mission", …)` in `SetMission` | Localized strings (`STR_…` keys) | [V] Optional. CWR prefers `stringtable.utf8.csv` for HTML (`CWR:engine/Poseidon/UI/Locale/MissionHtmlLocalization.cpp#L244-L259`). |
| `briefing.html` | Map/briefing display (`GetBriefingFile`, `CWR:engine/Poseidon/UI/OptionsUI.cpp#L202-L205`) | Notes, plan, objectives, debriefing sections | [V] CWR probes `briefing.<Lang>.utf8.html`, `briefing.<Lang>.html`, `briefing.utf8.html` and `briefing.html`, in that order (`…/MissionHtmlLocalization.cpp#L261-L284`). |
| `overview.html` | Mission selection screen (`CWR:engine/Poseidon/UI/OptionsUIImpl.cpp#L485-L491`) | Mission list preview | [V] Same localized lookup as the briefing. |
| `init.sqs` / `init.sqf` | `RunInitScript` (`CWR:engine/Poseidon/UI/DisplayUI.cpp#L121-L145`) | Mission start | [V] The `.sqf` file is a CWR addition, executed unscheduled as one expression [I: absent from OFP]. |
| Other `*.sqs` / `*.sqf`, sounds (`.ogg`, `.wss`), images (`.paa`, `.jpg`) | Scripts / `CfgSounds` paths relative to the mission dir | Mission content | [V] path resolution in §6. |

## 2. The config text format (as implemented)

### 2.1 Reading rules
Sources: `CWR:engine/Poseidon/IO/ParamFile/ParamFile.cpp#L1571-L1872` and
`CWR:engine/Poseidon/IO/ParamFile/ParamFilePrivate.inc#L10-L107`.

- **Preprocessing.** The whole file first goes through the C-like preprocessor (`Preprocess`), so
  `//` comments, `/* */` comments, `#include` and `#define` are legal in both `mission.sqm` and
  `description.ext` (`CWR:engine/Poseidon/IO/ParamFile/ParamFileParse.cpp#L279-L323`). [V]
- **Grammar.** `class Name [: Base] { … };`, `name=value;` and `name[]={…};` (sub-arrays allowed).
  `enum {…}` and `__EXEC(...)` are also accepted. Values may end at `;` or at a newline. [V]
- **Scalar typing.** An unquoted token is tried as an int, then as a float, and otherwise kept as
  a string. `__EVAL(...)` and `(`-prefixed expressions are evaluated. Quoted values are always
  strings. Inside quotes, `""` stands for a literal `"`. A raw newline inside quotes raises an
  error message but is kept. [V]
- **Name lookup.** Names are **case-insensitive** (`strcmpi` in `ParamClass::FindIndex`,
  `ParamFile.cpp#L1213-L1227`). A duplicate member produces "Member already defined" and **the
  first occurrence wins** (`#L1849-L1866`). The keywords `class`, `enum` and `__EXEC` are,
  however, matched case-sensitively (`strcmp`, `#L1601`, `#L1646`, `#L1703`). [V]
- **Length limits.** A single token or value is copied into a `WordBuf` of 2048 bytes, so text
  values longer than 2047 bytes are **silently truncated** (`ParamFilePrivate.inc#L10,L52-L55`).
  The binary loader caps strings at 4095 bytes (`CWR:engine/Poseidon/IO/Streams/SerializeBin.cpp#L126-L153`). [V]
- **String localization at read time.** Reading a string whose value starts with `$STR` returns
  the **localized text**, not the raw key (`ParamRawValue::GetValue`, `ParamFile.cpp#L791-L802`).
  Engine code that reads and re-saves such a value (the in-game editor) therefore replaces
  `$STR_x` with the translation [I: follows from `ar.Serialize` using `operator RStringB()`,
  `CWR:engine/Poseidon/IO/Serialization/ParamArchive.cpp#L299-L321`; not tested].

### 2.2 Writing rules
Sources: `CWR:engine/Poseidon/IO/ParamFile/ParamFileParse.cpp#L325-L697` and `#L873-L891`.

- **Indentation and line endings.** Each nesting level is indented with one TAB, and every line
  ends in `\r\n`.
- **Classes** are written as `class Name` CRLF, `{` CRLF, the members, then `};` CRLF. An empty
  class is written the same way, with nothing between the braces.
- **Values** are written as `name=value;`.
- **Strings** are written as `"…"` with `"` doubled; no other escaping is done.
- **Ints** use `%d`.
- **Floats** use `%f`, e.g. `0.600000`. CWR adds a fallback: if `%f` does not round-trip the
  32-bit float, it writes `%.9g`, appending `.0` if needed (`#L371-L388`). The source comment
  says this deliberately changes the older plain-`%f` behaviour. [V] Real OFP-era files show
  `%f` values such as `skill=0.200000` and `resistanceWest=0.000000` (see [ofpkubi/OFP-CTI
  mission.sqm](https://raw.githubusercontent.com/ofpkubi/OFP-CTI/master/mission.sqm)). [V-ext]
  The same sample also shows `version=11;` first, a one-element-per-line `addOns[]` and `""`
  escaping inside `init`. Its tab and CRLF bytes, and whether it was last saved by 1.96 rather
  than a later tool, could not be checked (unverified).
- **Bools.** C++ `bool` goes through the `int` overload and is written as `0`/`1` [I: no bool
  overload exists in `ParamEntry::Add`, `ParamFile.hpp#L120-L122`].
- **Arrays.** An all-numeric array is written inline: `position[]={x,y,z};`. If any element is a
  sub-array or its value does not parse as a number, the array is written on several lines:
  CRLF, indent, `{` CRLF, then one element per line with `,` separators, then `}`
  (`#L531-L577`). [V] The test is `IsNumerical(GetValue())` (`#L333-L342`), not the element
  type, so a string array whose elements all look numeric (e.g. `markers[]={"1"}`) is written
  inline, still quoted. `GetValue()` also localizes `$STR…` strings before the test. [V]
- **Order and key naming.** The writer emits entries in insertion order. For `mission.sqm` that is
  the `Serialize` field order listed in §3. `version` is always the first entry
  (`ParamArchiveSave` constructor, `CWR:engine/Poseidon/IO/Serialization/ParamArchive.cpp#L625-L634`). [V]

### 2.3 Default omission (the most important rule for fidelity)
`ParamArchive::Serialize(name, value, minVersion, default)` works as follows
(`CWR:engine/Poseidon/IO/Serialization/ParamArchive.hpp#L49-L61`):

- **Saving:** if `value == default`, **nothing is written**.
- **Loading:** a missing key takes the default. When the file version is below `minVersion`, the
  key is not read at all.

Overloads *without* a default are **required**: a missing key returns `LSNoEntry`.

Lists and classes behave as follows:
- **Lists** of structs are written as `class X { items=N; class Item0{…}; … };` and are omitted
  entirely when empty (`#L371-L414`).
- **Plain arrays** (`addOns[]`, `markers[]`, `synchronizations[]`) are omitted when empty
  (`#L296-L325`).
- **`SerializeClass` members** (`Intel`, `Effects`, each section) are always opened and therefore
  always written, even when empty (`ParamArchive.cpp#L434-L447`). [V]

**Enums** are written as fixed strings. Loading compares them case-insensitively (`stricmp`), and
an unknown string causes `LSStructure` (`ParamArchive.cpp#L484-L531`). [V]

**Item-level leniency.** The list loader calls `SerializeArrayItem` and **ignores its return
value** (`ParamArchive.hpp#L406-L411`). A bad enum or a missing required key inside `ItemN` is
logged ("Error in statement") and the keys after it are never read. They keep the values set by
the struct's `Init()`, which are **not always the serialization defaults**: a waypoint keeps
`type=UNDEF` (serialization default `MOVE`) and `showWP=NEVER` (default `EASY`), and a unit
keeps `skill=0.6` instead of the rank-derived value (`ArcadeTemplate.cpp#L257-L284`,
`#L1033-L1056`). The mission still loads. A missing `ItemK` (with `K < items`) leaves a default
element; extra `ItemK` entries are ignored. A missing `items` key is not swallowed: it fails the
enclosing list. [V] (The runtime consequence, e.g. a unit with `vehicle=""`, is [I]. A unit that
fails before `id` keeps `id=0`, and one that fails after `id` skips the `nextVehId` update at
`ArcadeTemplate.cpp#L392-L407`. Either can give duplicate or out-of-range IDs going into `Compact()` [I].)

## 3. `mission.sqm` schema — every key

**Top level** (`CWR:engine/Poseidon/UI/Map/UIMapExtDisplay.cpp#L99-L133`):
- `version` (int; read by `ParamArchiveLoad::Load`, `ParamArchive.cpp#L583-L596`). It is
  required in effect, but how a missing key fails differs by reader. The game's `ParseCutscene`
  checks `Load`'s result and fails the mission (`UIArcadeWaypoint.cpp#L924-L929`). The editor
  constructs `ParamArchiveLoad(filename)`, which ignores `Load`'s result. The archive version
  then stays −1 (`ParamArchive.cpp#L32-L37`), and every `Serialize` call with `minVersion ≥ 1`
  returns `LSOK` without reading, so the editor silently loads nothing [V code path; I for the
  visible effect].
- `class Mission`, `class Intro`, `class OutroWin`, `class OutroLoose` (note the BI spelling
  "Loose").
- In files with version < 7, a single top-level `class Intel` is copied into all four sections.

The editor's `LoadTemplates` requires all four sections. The game's `ParseCutscene` reads only
the section it needs (`"Mission"` or `"Intro"`).

Current write version: `MissionsVersion = 11` (`CWR:engine/Poseidon/Core/SaveVersion.hpp#L9`),
identical in CE. There is no upper-bound check on load. `LSVersionTooNew` is declared but never
returned anywhere under `engine/`; a grep found only the enum and its name string [V]. The other
writer of `mission.sqm` is the MP wizard (`DisplayUIMultiplayerWizard.cpp#L790`, same version).

### 3.1 Section (`ArcadeTemplate::Serialize`)
Source: `CWR:engine/Poseidon/AI/ArcadeTemplate.cpp#L1934-L1992` and struct
`CWR:engine/Poseidon/AI/ArcadeTemplate.hpp#L157-L253`.

Keys are listed in write order. "min v" is the minimum file version at which the key is read;
"—" in the Default column means the key is required.

| Key | Type | Min v | Default (omitted when equal) | Notes |
|---|---|---|---|---|
| `addOns[]` | string[] | 1 | empty | Required CfgPatches names. The loader checks them against `CfgPatches` and **fails the whole load with `LSNoAddOn`** if any are missing. |
| `addOnsAuto[]` | string[] | 1 | empty | **Written only.** It is recomputed on save by `ScanRequiredAddons` and never read back. |
| `showHUD`, `showMap`, `showWatch`, `showCompass`, `showNotepad` | bool | 8 | 1 | Serialized, but runtime HUD flags come from **description.ext** (`CWR:engine/Poseidon/UI/DisplayUIMenus.cpp#L850-L876`). A grep of `engine/` for these names finds only the constructor, the serializer and `ArcadeTemplateFind.cpp#L191-L196` for the template flags. The only other `showHUD` read is commented out (`OptionsUI.cpp#L1737-L1749`), so the template flags have no runtime reader [V by grep]. |
| `showGPS` | bool | 8 | 0 | As above. |
| `randomSeed` | int | 1 | 1 | The constructor randomizes it (`#L1567-L1580`), so in practice it is always written. |
| `class Intel` | class | 7 | always written | §3.2 |
| `class Groups` | list of Group | 1 | empty → omitted | §3.3 |
| `class Vehicles` | list of Unit | 1 | empty | Empty (crewless) objects, same shape as a Unit with `side="EMPTY"` [I]. |
| `class Markers` | list of Marker | 1 | empty | §3.7 |
| `class Sensors` | list of Sensor | 1 | empty | Triggers not attached to a group. |

### 3.2 `class Intel`
Source: `ArcadeTemplate.cpp#L1474-L1539`.

| Key | Type | Min v | Default | Notes |
|---|---|---|---|---|
| `briefingName` | string | 2 | `""` | Mission title; `$STR_` / `@STR_` tokens are seen in the wild. |
| `briefingDescription` | string | 2 | `""` | |
| `resistanceWest` | float | 1 (only if v ≥ 10) | 1.0 | Friendship Guer↔West. |
| `resistanceEast` | float | 1 (only if v ≥ 10) | 0.0 | |
| `resistance` | float | used only if v < 10 | 1.0 | Legacy key; East = 1 − value. |
| `startWeather` / `forecastWeather` | float | 1 | 0.5 / 0.5 | Overcast 0..1. |
| `startFog` / `forecastFog` | float | 1 | 0 / 0 | |
| `year`, `month`, `day`, `hour`, `minute` | int | 1 | 1985, 5, 10, 7, 30 | |
| `viewDistance` (alias `missionViewDistance`) | float | — | absent | **CWR/CE-only extra, not in `ArcadeIntel::Serialize`.** It is read raw from `Mission>>Intel` by `MissionLanguageDetector.cpp#L300-L317` (identical in CE) and clamped. The engine editor never writes it and drops it on re-save (§12.3 item 11) [V]. |

Actual `Serialize` order (the table groups some keys): `briefingName`, `briefingDescription`,
`resistanceWest`, `resistanceEast` (or `resistance`), `startWeather`, `startFog`,
`forecastWeather`, `forecastFog`, `year`, `month`, `day`, `hour`, `minute` (`#L1501-L1539`) [V].

### 3.3 Group and Unit
- **Group** (`#L1460-L1467`) contains `side` (enum, **required**), then `class Vehicles` (its
  units), `class Waypoints` and `class Sensors` (triggers grouped with the group; these use
  activation `GROUP`, `LEADER` or `MEMBER`).
- **Unit** (`ArcadeUnitInfo::Serialize`, `#L354-L410`). Its first-pass defaults come from
  `Init()` (`#L257-L284`).

| Key | Type | Min v | Default | Notes |
|---|---|---|---|---|
| `presence` | float | 1 | 1.0 | Probability of presence. |
| `presenceCondition` | string (expression) | 1 | `"true"` | |
| `position[]` | float[3] | 1 | **required** | Order is `{x, y, z}` with **y = height** and z = north. The editor writes the terrain/road surface height (`RoadSurfaceYAboveWater`, `#L286-L290`). |
| `placement` | float | 1 | 0 | Random placement radius in metres. |
| `azimut` | float | 1 | 0 | Heading in degrees (BI spelling "azimut"). |
| `special` | enum | 1 | `FORM` | |
| `age` | enum | 1 | `UNKNOWN` | Age of intel. |
| `id` | int | 1 | **required** | Vehicle ID, see §3.8. |
| `side` | enum | 1 | **required** | |
| `vehicle` | string | 1 | **required** | `CfgVehicles` class name. |
| `player` | enum | 1 | `NONPLAY` | |
| `leader` | bool | 1 | 0 | |
| `lock` | enum | 1 (v ≥ 11) | `DEFAULT` | For v < 11, the legacy key `locked` (bool, min v 7) is read instead. |
| `rank` | enum | 1 | `PRIVATE` | |
| `skill` | float | 1 | −1 | In practice always written. If negative on load, it is derived from `rank`. |
| `health`, `fuel`, `ammo` | float | 1 | 1.0 | |
| `text` | string | 7 | `""` | The unit's **variable name**. |
| `markers[]` | string[] | 1 | empty | Alternative start positions (marker names). |
| `init` | string (SQS expression) | 7 | `""` | |

### 3.4 Waypoint
Source: `ArcadeWaypointInfo::Serialize`, `#L1092-L1149`; `Init` at `#L1033-L1056`.

| Key | Type | Min v | Default | Notes |
|---|---|---|---|---|
| `position[]` | float[3] | 1 | **required** | |
| `placement` | float | 1 | 0 | |
| `id` | int | 1 | −1 | Attached vehicle ID. |
| `idStatic` | int | 1 | −1 | Attached terrain object ID (from the island). |
| `housePos` | int | 2 | −1 | Building position index. |
| `type` | enum | 1 | `MOVE` | A missing key loads as MOVE. |
| `combatMode` | enum | 1 | `NO CHANGE` | Semaphore colours. |
| `formation` | enum | 1 | `NO CHANGE` | |
| `speed` | enum | 1 | `UNCHANGED` | |
| `combat` | enum | 4 | `UNCHANGED` | Behaviour. |
| `description` | string | 1 | `""` | |
| `expCond` | string | 7 | `"true"` | Condition. |
| `expActiv` | string | 7 | `""` | On-activation statement. |
| `script` | string | 7 | `""` | Script for SCRIPTED waypoints. |
| `synchronizations[]` | int[] | 1 | empty | |
| `class Effects` | class | 1 | always written | §3.6 |
| `timeoutMin`, `timeoutMid`, `timeoutMax` | float | 1 | 0 | |
| `showWP` | enum (v ≥ 10) | 1 | `EASY` | For v < 10, the legacy key `show` (bool) is read instead. |

### 3.5 Sensor (trigger)
Source: `ArcadeSensorInfo::Serialize`, `#L510-L562`; `Init` at `#L446-L473`.

| Key | Type | Min v | Default | Notes |
|---|---|---|---|---|
| `position[]` | float[3] | 1 | **required** | |
| `a`, `b` | float | 1 | 50, 50 | Axis half-sizes. |
| `angle` | float | 1 | 0 | |
| `rectangular` | bool | 7 | 0 | |
| `activationBy` | enum | 1 | `NONE` | |
| `activationType` | enum | 1 | `PRESENT` | |
| `repeating` | bool | 1 | 0 | |
| `timeoutMin`, `timeoutMid`, `timeoutMax` | float | 1 | 0 | |
| `interruptable` | bool | 1 | 0 | |
| `type` | enum | 1 | `NONE` | |
| `object` | string | 1 | `"EmptyDetector"` | |
| `age` | enum | 1 | **required** | Always written, e.g. `"UNKNOWN"`. |
| `idStatic`, `idVehicle` | int | 1 | −1 | |
| `text` | string | 3 | `""` | Trigger text. |
| `name` | string | 7 | `""` | Trigger variable name. |
| `expCond` | string | 1 | `"this"` | |
| `expActiv`, `expDesactiv` | string | 1 | `""` | |
| `class Effects` | class | 1 | always written | |
| `synchronizations[]` | int[] | 1 | empty | |

### 3.6 `class Effects` (waypoints and triggers)
Source: `#L820-L867`.

| Key | Type | Min v | Default | Notes |
|---|---|---|---|---|
| `condition` | string | 9 | `"true"` | For v < 9, the legacy bool `playerOnly` is read (1 → `"thisList"`). |
| `cameraEffect` | string | 1 | `""` | `CfgCameraEffects >> Array` class name, or `"$TERMINATE$"`. |
| `cameraPosition` | enum | 1 | `BACK` | |
| `sound` | string | 1 | `"$NONE$"` | `CfgSounds` class name. |
| `voice` | string | 5 | `""` | `CfgSounds` class name. |
| `soundEnv` | string | 5 | `""` | `CfgEnvSounds` class name. |
| `soundDet` | string | 5 | `""` | `CfgSFX` class name. |
| `track` | string | 1 | `"$NONE$"` | `CfgMusic` class name, or `"$STOP$"`. |
| `titleType` | enum | 1 | `NONE` | |
| `titleEffect` | enum | 1 | `PLAIN` | |
| `title` | string | 1 | `""` | Text, an `RscTitles` class, or a `CfgTitles` entry, depending on `titleType`. |

### 3.7 Marker
Source: `#L642-L663`; `Init` at `#L588-L605`.

| Key | Type | Default | Notes |
|---|---|---|---|
| `position[]` | float[3] | **required** | |
| `name` | string | **required** | Unique marker name. |
| `text` | string | `""` | |
| `markerType` | enum | `ICON` | |
| `type` | string | **required** | `CfgMarkers` class name; written even for rectangles and ellipses. |
| `colorName` | string | `"Default"` | `CfgMarkerColors` class name. |
| `fillName` | string | `"Solid"` | `CfgMarkerBrushes` class name. |
| `a`, `b` | float | 1, 1 | |
| `angle` | float | 0 | |

Icon size is **not** stored; it comes from `CfgMarkers >> type >> size`.

### 3.8 Enum tokens (exact on-disk strings)
Sources: `ArcadeTemplate.cpp#L38-L211`; sides in `CWR:engine/Poseidon/World/Scene/Object.cpp#L53-L62`;
semaphore, formation and rank in `CWR:engine/Poseidon/AI/AICenter.cpp#L146-L181`; title effects in
`CWR:engine/Poseidon/Game/TitEffects.cpp#L35-L48`; camera positions in
`CWR:engine/Poseidon/World/Scene/Camera/CamEffects.cpp#L32-L48`. All [V].

| Enum | Tokens |
|---|---|
| Side (`TargetSide`: EAST=0, WEST=1, GUER=2, CIV=3, …, LOGIC=7, EMPTY=8) | `WEST`, `EAST`, `GUER`, `CIV`, `UNKNOWN`, `ENEMY`, `FRIENDLY`, `LOGIC`, `EMPTY` |
| Waypoint `type` | `UNDEF`, `MOVE`, `DESTROY`, `GETIN`, `SAD`, `JOIN`, `LEADER`, `GETOUT`, `CYCLE`, `LOAD`, `UNLOAD`, `TR UNLOAD`, `HOLD`, `SENTRY`, `GUARD`, `TALK`, `SCRIPTED`, `SUPPORT`, `AND`, `OR` (AND/OR only for LOGIC groups; `CWR:engine/Poseidon/UI/Map/UIArcadeWaypoint.cpp#L78-L100`) |
| `combatMode` | `NO CHANGE`, `BLUE`, `GREEN`, `WHITE`, `YELLOW`, `RED` |
| `formation` | `NO CHANGE`, `COLUMN`, `STAG COLUMN`, `WEDGE`, `ECH LEFT`, `ECH RIGHT`, `VEE`, `LINE` |
| `speed` | `UNCHANGED`, `LIMITED`, `NORMAL`, `FULL` |
| `combat` | `UNCHANGED`, `CARELESS`, `SAFE`, `AWARE`, `COMBAT`, `STEALTH` |
| `showWP` | `NEVER`, `EASY`, `ALWAYS` |
| `special` | `NONE`, `CARGO`, `FLY`, `FORM` |
| `age` | `ACTUAL`, `5 MIN`, `10 MIN`, `15 MIN`, `30 MIN`, `60 MIN`, `120 MIN`, `UNKNOWN` |
| `player` | `NONPLAY`, `PLAYER COMMANDER`, `PLAYER DRIVER`, `PLAYER GUNNER`, `PLAY C`, `PLAY D`, `PLAY G`, `PLAY CD`, `PLAY CG`, `PLAY DG`, `PLAY CDG`. Legacy aliases on read: `PLAY`, `P1 …`, `P2 …`, `-1`, `0`, `1`, `2`, `-1.000000`, `0.000000`, … |
| `lock` | `UNLOCKED`, `DEFAULT`, `LOCKED` |
| `rank` | `UNDEFINED`, `PRIVATE`, `CORPORAL`, `SERGEANT`, `LIEUTNANT` (sic), `CAPTAIN`, `MAJOR`, `COLONEL` |
| `activationBy` | `NONE`, `EAST`, `WEST`, `GUER`, `CIV`, `LOGIC`, `ANY`, `ALPHA` … `JULIET`, `STATIC`, `VEHICLE`, `GROUP`, `LEADER`, `MEMBER` |
| `activationType` | `PRESENT`, `NOT PRESENT`, `WEST D`, `EAST D`, `GUER D`, `CIV D` |
| Sensor `type` | `NONE`, `EAST G`, `WEST G`, `GUER G`, `SWITCH`, `END1` … `END6`, `LOOSE`; alias `WIN` = END1 on read |
| `markerType` | `ICON`, `RECTANGLE`, `ELLIPSE` |
| `titleType` | `NONE`, `OBJECT`, `RES`, `TEXT` |
| `titleEffect` | `PLAIN`, `PLAIN DOWN`, `BLACK`, `BLACK FADED`, `BLACK OUT`, `BLACK IN`, `WHITE OUT`, `WHITE IN` |
| `cameraPosition` | `TOP`, `LEFT`, `RIGHT`, `FRONT`, `BACK`, `LEFT FRONT`, `RIGHT FRONT`, `LEFT BACK`, `RIGHT BACK`, `LEFT TOP`, `RIGHT TOP`, `FRONT TOP`, `BACK TOP`, `BOTTOM` |

**Aliases mean lossy normalization.** A file containing `type="WIN"` or `player="PLAY"` is
re-saved by the engine as `END1` / `PLAY CDG`. Our editor must keep the original token unless
the user changes the field.

### 3.9 IDs, synchronizations and consistency rules (all [V])
- **Vehicle IDs.** Unit `id`s (in groups and in empty vehicles) share one namespace. They are
  referenced by waypoint `id` and sensor `idVehicle`. On load and on save, `Compact()` remaps used
  IDs to 0..n−1 and rewrites the references (`CWR:engine/Poseidon/AI/ArcadeTemplateFind.cpp#L882-L960`).
- **Terrain object IDs.** `idStatic` is **not** remapped, because it is an object ID from the
  island file.
- **Sync semantics.** A sync is an integer shared by waypoints and triggers (`ArcadeTemplate.cpp#L1582-L1752`).
  `CheckSynchro` drops a waypoint's sync unless at least 2 participants share it. It drops a
  trigger's sync unless at least 1 **waypoint** shares it (so trigger-to-trigger syncs are
  invalid). Surviving syncs are then renumbered densely (`ArcadeTemplateFind.cpp#L962-L1045`).
- **Name uniqueness.** Marker `name`, unit `text` and trigger `name` are unique by convention.
  `Merge` renames duplicates as `name_N` (`ArcadeTemplateFind.cpp#L1086-L1310`).
- **`IsConsistent`** (`ArcadeTemplate.cpp#L1754-L1860`) enforces:
  - at most `MAX_UNITS_PER_GROUP = 12` crew seats per group, counting driver, commander and
    gunner of each vehicle type (`CWR:engine/Poseidon/AI/Path/AITypes.hpp#L31`);
  - per-side groups ≤ `MaxGroups`, where MaxGroups = `CfgWorlds>>GroupNameList>>letters` count ×
    `GroupColorList>>colors` count (`CWR:engine/Poseidon/Core/Config/Configuration.cpp#L339-L348`);
  - in single-player, **at least one** `PLAYER COMMANDER/DRIVER/GUNNER` unit. This is enforced
    only when `_ENABLE_CHEATS` is off. "At most one" is only an `AI_ERROR` log check, not a
    refusal (`#L1835-L1845`; `AI_ERROR` = `POSEIDON_LOG_CHECK`, `DebugLog.hpp#L93`).
- **The game refuses a section with no groups.** `ParseCutscene` fails when
  `groups.Size() == 0` or `IsConsistent` fails (`UIArcadeWaypoint.cpp#L966-L970`). A `Mission`
  or `Intro` with only empty vehicles, markers or triggers will not start. A section
  `Serialize` error, `LSNoAddOn` included, only produces a warning there (`#L933-L957`). The
  groups and `IsConsistent` check then decides whether the section starts.
- **Group presets** are `CfgGroups >> <side> >> <type> >> <group> >> UnitN { side (int); vehicle;
  rank; position[]={dx,dz,dy} }`. Note the axis order in `position[]`
  (`ArcadeTemplateFind.cpp#L841-L874`). The leader is the highest rank (`SelectLeader`,
  `ArcadeTemplate.cpp#L1542-L1561`).

## 4. Binarized `mission.sqm` (OFP "raP")

Implemented in `CWR:engine/Poseidon/IO/ParamFile/ParamFileParse.cpp#L43-L180` and `#L579-L1035`.
The layout is [V]. Compatibility with other toolchains is [I].

**Header and root:**
1. Magic bytes `00 72 61 50` (`"\0raP"`).
2. `int32 LE` context version. The writer uses 4; the reader rejects values below 2.
3. The root class body.

**Class body:**
- The class name, via the string pool.
- The base name as a plain NUL-terminated string.
- The entry count: a varint in v ≥ 4, otherwise `int32`.
- Each entry, prefixed by a kind byte (0 = class, 1 = value, 2 = array).

**Entries:**
- **Value:** a type byte (0 string, 1 float, 2 int), the name via the pool, then the payload.
  Strings go via the pool; float is `f32 LE`; int is `i32 LE`.
- **Array:** the name via the pool, a count, then elements, each with a type byte (3 =
  sub-array).

**String pool:** an index, varint-encoded in v ≥ 3 (7 bits per byte, low group first). A new
string must use exactly the next index and is followed by its NUL-terminated bytes (hardened in
`TransferString`, `#L70-L125`).

**Trailer:** `int32` count of "variables" (enum constants), each a NUL-terminated name plus
`int32` (`CWR:engine/Poseidon/IO/ParamFile/ParamFileEval.cpp#L70-L105`).

**Who reads and writes it:**
- The editor never writes binary missions. `SaveBin` is used only for configs, save games and
  CWR tools.
- `LoadTemplates` rejects a file whose first byte is 0 (`UIMapExtDisplay.cpp#L135-L143`).
- CWR ships a `config bin`/`debin` CLI that can serve as an external test oracle
  (`CWR:apps/tools/Tools/commands/ConfigCommand.cpp#L204-L271`).

This OFP layout (string pool, varints) is not Arma's offset-table rapify, so Arma-era binarizers
are probably incompatible [I; test with synthetic files].

## 5. `description.ext` — keys the engine actually reads

Each key below was found by grepping for `ExtParsMission` reads. [V] unless noted. "Campaign"
means a campaign's `description.ext`, loaded via `SetBaseDirectory`.

| Key / class | Type | Where read | Effect |
|---|---|---|---|
| `showMap`, `showWatch`, `showCompass`, `showNotepad`, `showHUD` | bool (default 1) | `DisplayUIMenus.cpp#L850-L876`, `UIMapDialogs.cpp#L347-L349` | Runtime HUD/map item visibility. |
| `showGPS` | bool (default 0) | same | |
| `onLoadMission`, `onLoadIntro` | string | `CWR:engine/Poseidon/World/WorldInit.cpp#L455-L503` | Loading-screen text. |
| `onLoadMissionTime` (default 1), `onLoadIntroTime` (default 0) | bool | same | Show the date/time on the loading screen. |
| `respawn` | int 0–5 or name | `CWR:engine/Poseidon/Network/NetworkServerMission.cpp#L281-L364` | `NONE`, `BIRD` (MP default), `INSTANT`, `BASE`, `GROUP`, `SIDE`. |
| `respawnDelay` | float | same | Seconds. |
| `disabledAI`, `aiKills` | bool | `#L316-L371` | |
| `joinInProgress` | bool | `#L373-L383` | CWR addition [I]. |
| `class CfgRemoteExec { Functions / Commands }` | class | `#L385-L393` | CWR addition (remoteExec policy) [I]. |
| `titleParam1/2`, `valuesParam1/2[]`, `textsParam1/2[]`, `defValueParam1/2` | mixed | `#L397-L460` | MP lobby parameters. |
| `debriefing` | bool | `UIMapExtDisplay.cpp#L2037-L2042` | 0 skips the debriefing. |
| `minScore`, `avgScore`, `maxScore` | float | `CWR:engine/Poseidon/AI/AICenterStats.cpp#L94-L99` | Score thresholds. |
| `class Weapons` / `class Magazines { class X { count=n; }; }` | class | `UIMapDisplay.cpp#L400-L452` | Briefing gear pool. |
| `CfgSounds`, `CfgRadio`, `CfgMusic`, `CfgEnvSounds`, `CfgSFX` | class | `CWR:engine/Poseidon/UI/OptionsUI.cpp#L283-L583` | Looked up **mission → campaign → global config**. `sound[]={file,vol,pitch}` is resolved relative to the mission dir (campaign: `dtaExt\`). `titles[]` holds subtitles (`CWR:engine/Poseidon/Audio/DynSound.cpp#L146`). CWR prefers `<file>.<voiceLang>.<ext>` if present. |
| `CfgCameraEffects { class Array {…} }`, `RscTitles` | class | `OptionsUI.cpp#L588-L773` | Same lookup order. |
| `CfgIdentities { class X { name; face; glasses; speaker; pitch; } }` | class | `CWR:engine/Poseidon/Game/Commands/GameStateExtUi.cpp#L184-L224` | Used by `setIdentity`. |
| Any class name used by `createDialog` | class | `GameStateExtWorldDialog.cpp#L27` | Mission-defined dialogs. |

Scripts are resolved **mission dir → `<campaign>\scripts\` → game `scripts\`**
(`OptionsUI.cpp#L630-L655`). Pictures and shapes use the mission dir, then `dtaExt\`, then banks.

## 6. `briefing.html` / `overview.html` — the engine's HTML subset

The parser is `CHTMLContainer::LoadBuffer` (`CWR:engine/Poseidon/UI/Controls/UIControlsExt.cpp#L1356-L1759`). [V]

**Structure:**
- `<html>` contains `<head>` (ignored) and `<body>`.
- **Each `<body>` and each `<hr>` starts a new section.**
- Body-level blocks: `<p>`, `<address>` (bottom-aligned), `<h1>`–`<h6>`, and
  `<table>`/`<tr>`/`<td>`. Blocks may carry `align`/`width` properties.
- Inline elements: `<a href=… name=…>`, `<b>`, `<br>`, and `<img src width height>`.
- **Text directly inside `<body>` (outside a block) is ignored.**
- Entities: `&#N;`, `&amp;`, `&quot;`, `&lt;`, `&gt;` and Latin-1 names (`#L574-L619`).

**Section names** come from `<a name="X">`; one section can carry several names. The meaningful
names are:
- `Main` (the briefing notes), with per-player variants `Main.<unitVar>`, `Main.<leaderVar>` and
  `Main.West|East|Guerrila|Civilian` (`CWR:engine/Poseidon/UI/Map/UIMapDisplayBriefing.cpp#L78-L136`).
- `Plan`, with the same variant scheme.
- Objectives `OBJ_<n>`, or side-filtered `OBJ_WEST_…`, `OBJ_EAST_…`, `OBJ_GUER_…`, `OBJ_CIVIL_…`
  (`#L427-L474`).
- Debriefing texts `Debriefing:End1` … `End6` and `Debriefing:Loser`
  (`CWR:engine/Poseidon/UI/Map/UIMapDialogs.cpp#L1062-L1091`).

The engine synthesizes the names `__PLAN`, `__BRIEFING`, `Group`, `__OBJECTIVES`, `__DEBRIEFING`
and `__STATISTICS`. Avoid these names.

**Objective state.** An objective's state is the global variable `OBJ_<n>`, set with
`"<n>" objStatus "DONE"` (`GameStateExtUi.cpp#L1825-L1827`). Valid values are `ACTIVE`, `DONE`,
`FAILED` and `HIDDEN`.

**Links:**
- `href="#Name"` switches section (`CWR:engine/Poseidon/UI/Controls/UIControlsHTML.cpp#L63-L67`).
- `href="marker:<name>"` pans the map to that marker (`UIMapDisplayBriefing.cpp#L978-L1028`).
- `%20` is decoded to a space.

**CWR additions:** `$STR_*` and `@KEY` tokens inside HTML are expanded
(`MissionHtmlLocalization.cpp#L286-L319`), and legacy code-page bytes are transcoded to UTF-8
before parsing.

## 7. `stringtable.csv` and localization

Loader: `StringTableDynamic::Load`, `CWR:engine/Poseidon/UI/Locale/Stringtable/Stringtable.cpp#L281-L363`. [V]

**File format:**
- The header row starts with `LANGUAGE`, followed by one column per language (e.g. `English`,
  `Czech`, …).
- Each data row is `KEY,"text",…`. Cells may be quoted, with `""` inside quotes, and rows end in
  CRLF or LF (`CWR:engine/Poseidon/Asset/Formats/Common/CsvReader.cpp#L65-L97`).
- Rows whose key is `COMMENT`, and rows with an empty key, are skipped.
- Duplicate keys log a message; the first one wins.

**Column choice and encoding:**
- If the current language column is missing, CWR uses column 0. CE also falls back to the English
  column per empty cell (CE diff of `Stringtable.cpp`).
- Legacy `.csv` cells are decoded with the language's code page (CP1252, CP1250 or CP1251; table
  in `CodepageTranscode.cpp#L74-L100`).
- `.utf8.csv` files are read as UTF-8.

**Resolution order** is **mission → campaign → global** (`#L567-L593`). `$STR…` and `@KEY` both
resolve (`#L643-L661`).

**Where lookups happen:**
- Config string values starting with `$STR` are localized **at read time** (§2.1).
- `briefingName` and similar strings are passed through `Localize()`.
- Scripts use `localize "STR_x"` [I: standard command; not traced].

## 8. Scripts: SQS vs SQF in this engine

- **SQS** scripts run through `Script`/`exec`, with `goto` labels (engine standard).
- **SQF-style code** exists only as **strings**: `call` takes a string
  (`CWR:engine/Evaluator/EvalState.cpp#L761`, `CWR:engine/Evaluator/express.cpp#L1149,L1188`), and
  `preprocessFile`/`loadFile` load files as strings (`CWR:engine/Poseidon/Game/Commands/GameStateExt.cpp#L1159-L1160`).
- A grep of `engine/` found no `spawn`, `execVM` or `compile` command registrations, so there is
  no scheduled SQF [V by absence of matches; I that none are registered elsewhere].
- `init.sqf` (CWR) is executed in one unscheduled `Execute` call.

**Event scripts** found in source:

| Script | Source location |
|---|---|
| `init.sqs` | `DisplayUI.cpp#L123` |
| `init.sqf` | `DisplayUI.cpp#L132` (CWR) |
| `initIntro.sqs` (lowercased in code) | `DisplayUIMenus.cpp#L1322` |
| `exit.sqs` (argument: end mode) | `DisplayUIMenus.cpp#L987-L991` |
| `onPlayerKilled.sqs` | `CWR:engine/Poseidon/World/Entities/Infantry/SoldierOldMove.cpp#L1075` |
| `onPlayerRespawnAsSeagull.sqs` | `#L964` |
| `onPlayerRespawnOtherUnit.sqs` | `#L940` |
| `onPlayerRespawn.sqs` | `#L1177` |
| `onPlayerResurrect.sqs` | `CWR:engine/Poseidon/Network/NetworkClientOnMessage.cpp#L319` |
| `onFlare.sqs` | `CWR:engine/Poseidon/World/Entities/Weapons/Shots.cpp#L1314` |
| `initServer.sqs`, `initPlayerLocal.sqs` | `DisplayUISetup.cpp#L1543-L1545` |
| `initPlayerServer.sqs` | `NetworkServerMsgOnMessage.cpp#L1922` |
| `initJIP.sqs` | `NetworkMissionTransfer.hpp#L1422-L1423` |

The `init*Server/Player/JIP` scripts and `onPlayerRespawn` mirror Arma 3 naming and are almost
certainly CWR additions [I].

## 9. Where missions live; campaigns; export to PBO

**Paths:**
- `GetMissionDirectory()` = BaseDirectory + subdir + `<name>.<world>/` (`CWR:engine/Poseidon/UI/OptionsUI.cpp#L191-L200`).
- **User (editor) missions:** base `GetUserMissionsBase()` (`#L129-L141`):
  - default CWR: the per-OS Documents/XDG *user-content* dir, with `missions/` and `MPMissions/`
    subfolders (`CWR:engine/Poseidon/Foundation/Common/GamePaths.cpp#L68-L121`). The product name
    is `"Cold War Assault"` (`CWR:apps/cwr/GameBase/GameBase.cpp#L155`), giving
    `Documents\Cold War Assault\` on Windows (`PlatformPaths_win.cpp#L45-L49`) and
    `$XDG_DATA_HOME` (default `~/.local/share`)`/Cold War Assault/` on Linux
    (`PlatformPaths_posix.cpp#L110-L119`). Both can be overridden with
    `POSEIDON_USER_CONTENT_DIR` or `POSEIDON_USER_DIR` (`GamePaths.cpp#L59-L66`) [V];
  - with *old paths* enabled: `<gameRoot>/Users/<playerName>/missions/<name>.<world>/` and
    `…/MPMissions/…` (`ProfileManager.cpp#L23-L26`), matching OFP 1.96 conventions [I].
- **Game-dir missions:** `Missions\<name>.<world>.pbo` (single), `MPMissions\<name>.<world>.pbo`
  or a folder (MP), and `Anims\<name>.<world>\` for intros (`OptionsUI.cpp#L843-L853`). CWR also
  scans mod folders' `missions/` and `mpmissions/` (`DisplayUIMultiplayer.cpp#L2718`).
- **Campaigns:** `campaigns/<c>/description.ext` plus `stringtable.csv`, and missions in
  `campaigns/<c>/missions/<name>.<world>/` (`OptionsUI.cpp#L148-L159`).

**Campaign `description.ext`** (`OptionsUI.cpp#L1721-L2009`, `OptionsUIApp.cpp#L361-L366,L881`):
- `class Campaign { firstBattle; class <Battle> { cutscene; firstMission; end1..end6; lost;
  class <Mission> { template="name.world"; end1..end6; lost; lives; noAward; }; }; }`.
- Top-level `exitScore` and `class Awards/Penalties { class X { limit; <world>=cutscene; }; }`.
- Campaign assets live in `dtaExt\`; campaign scripts in `scripts\`.

**Editor save/export** (`CWR:engine/Poseidon/UI/Map/UIMapExtDisplay.cpp#L2190-L2264`):
- **Save** writes the text `mission.sqm` into the user mission folder. The mode combo then
  offers:
  - 0: user mission only;
  - 1: `Missions\<name>.<world>.pbo`;
  - 2: `MPMissions\<name>.<world>.pbo`;
  - 3: e-mail.
- **PBO creation:** `FileBankManager::Create(target, folder, compress=true)` packs **the whole
  mission folder** (`CWR:engine/Poseidon/IO/PackFiles.cpp#L484-L589`).
- **Header entries:** `name\0` (backslash separators, max 255 chars on read), then `u32`
  packingMethod, `u32` originalSize, `u32` reserved/offset, `u32` timestamp and `u32` dataSize
  (`#L151-L184`). An empty-name entry terminates the header.
- **Properties:** an optional leading `"Vers"` entry plus key/value properties, written only if
  properties are given (none for missions) (`#L423-L439`).
- **Compression:** every file is compressed with BI LZSS (`'Cprs'`, with a 4-byte additive
  checksum; `SsCompress.cpp#L231-L325`), **except** `.pbo`, `.ogg`, `.wss` and `.jpg`
  (`#L467`). These are the `Create` defaults (`PackFiles.hpp#L57-L64`). No SHA-1 trailer is
  written. `'Cprs'` is an MSVC multi-char constant, i.e. u32 `0x43707273`, so the **on-disk bytes
  are `73 72 70 43` ("srpC")**. The GCC build spells it `StrToInt("srpC")`
  (`CWR:engine/Poseidon/IO/Streams/FileInfo.h#L8-L18`). `'Vers'` is likewise stored as the bytes
  "sreV" [V].
- **Entry order:** entries are sorted case-insensitively by name (all priorities are 0 without a
  log file; `PackFiles.cpp#L272-L320`). Sub-directories whose name starts with `.` are skipped.
  Dot-files are not skipped (`#L322-L403`) [V].
- Whether OFP 1.96 / CWA 1.99 exports were compressed is [U]. Uncompressed PBOs are community
  practice and are readable by the loader (`QBStream.cpp#L1051`) [I].

## 10. Catalogs the editor enumerates (from game data, never from source)

All of these come from the game's global config `Pars`: `bin\config.bin` plus addon `config.bin`
files in PBOs (`CWR:engine/Poseidon/World/World.cpp#L306-L307` shows the dump target), and
`Res` (`bin\resource.bin`). **They are game data, not code, and are not GPL.** The CWR README
says BI releases the CWR game data separately under the Arma Public License Share Alike (APL-SA),
a license distinct from the engine's GPL (`CWR:README.md#L14-L16`, `#L66-L72`) [V]. The terms
for OFP 1.96 / CWA 1.99 data are [U]. Our editor must extract the catalogs from the user's
install at runtime and must not ship them. [V/I]

| Catalog | Rule in the original editor | Source |
|---|---|---|
| Unit classes per side | `CfgVehicles` classes with `scope==2`, `side==chosen` and at least one of `hasDriver`/`hasGunner`/`hasCommander`, grouped by `vehicleClass`. Names are shown via `displayName`, the map icon via `icon`/`mapSize`. CWR localizes class labels via `STR_DISP_ARCUNIT_CLASS_<UPPER>`. | `CWR:engine/Poseidon/UI/Map/UIArcade.cpp#L242-L440` |
| Empty objects | Same, with `side != LOGIC` and not derived from `Man`. | same |
| Group presets | `CfgGroups` side → type → group, each level with a `name`. | `UIArcade.cpp#L1305-L1428` |
| Islands | Classes of `CfgWorldList` whose `.wrp` exists, labelled with `CfgWorlds >> X >> description`. Default map centre: `centerPosition`. | `UIArcadeWaypoint.cpp#L483-L517`, `UIMap.cpp#L250-L252` |
| Markers | `CfgMarkers`, `CfgMarkerColors`, `CfgMarkerBrushes`, each labelled with `name`. | `UIArcadeMarker.cpp#L53-L109` |
| Trigger objects | `CfgDetectors >> objects[]`, labelled with `CfgNonAIVehicles >> X >> displayName`. | `UIArcade.cpp#L1619-L1638` |
| Effects | Classes that have a `name` entry, **concatenated from config, then campaign, then mission**: `CfgSounds` (sound and voice), `CfgEnvSounds`, `CfgSFX`, `CfgMusic` (plus `$NONE$`/`$STOP$`), `CfgCameraEffects>>Array` (plus `$TERMINATE$`), `Res>>RscTitles`, and `CfgTitles>>titles[]`. | `UIArcadeMarker.cpp#L380-L1020` |
| Required addons | `CfgPatches >> X >> units[]`, plus the owner addon of each vehicle class. | `ArcadeTemplate.cpp#L321-L352` |

## 11. Compatibility matrix

| Aspect | OFP 1.96 | CWA 1.99 | CWR 3.05 | CWR-CE |
|---|---|---|---|---|
| `version` written | 11 [V-ext sample; I that 1.96 wrote it] | 11 [I] | 11 [V] | 11 [V] |
| Key set and defaults (§3) | same [I: shared lineage; sample consistent] | same [I] | [V] | identical files [V] |
| Float format | `%f` [V-ext] | `%f` [I] | `%f` plus `%.9g` fallback [V] | same [V] |
| Text encoding | ANSI code page [I] | ANSI [I] | Decodes legacy code pages to UTF-8 for marker/trigger text and waypoint descriptions (`ArcadeTemplate.cpp#L33-L36`); may re-save as UTF-8 [V] | same [V] |
| `*.utf8.csv/.html`, localized briefings | no [I] | no [I] | yes [V] | yes, plus campaign stringtable fallback for HTML [V] |
| `init.sqf`, `initServer.sqs` etc., `joinInProgress`, `CfgRemoteExec` | no [I] | no [I] | yes [V] | yes [V] |
| Default user mission root | `Users\<name>\` [I] | same [I] | Documents user-content dir, or old paths [V] | same [V] |

## 12. Proposed Rust data model

### 12.1 Layers and crates

The crates follow the IC rules: pure `&[u8]` parsers, permissive values, strict structure, one
`Error` enum per crate, and no `unsafe`/`unwrap`. The IC sources are `IC:AGENTS.md#L399-L408`
for the parser rules, `#L255-L260` for the shared `Error` enum (IC uses one per crate root),
`#L335-L341` for no `unwrap`/`expect` and `#L676` for no `unsafe`.

| Crate | Responsibility |
|---|---|
| `ofp-config` | Lossless CST for config text, plus a raP reader and writer. Pure `fn parse(&[u8]) -> Result<ConfigDoc, Error>`. |
| `ofp-mission` | Typed lens over `ConfigDoc`: `Mission`, `Section`, `Unit`, …; the engine-strict validator; writer profiles. |
| `ofp-pbo` | PBO read/write, BI LZSS `Cprs` with checksum, `Vers` properties, adversarial bounds. |
| `ofp-briefing` | HTML-subset parser and emitter that keeps source spans. |
| `ofp-stringtable` | CSV with raw-row preservation, per-language columns, code-page tags. |
| `ofp-catalog` | Builds a local catalog snapshot (CfgVehicles, CfgWorlds, …) from the user's config. It is never committed. |

### 12.2 Type sketches

```rust
// ── ofp-config: lossless CST ─────────────────────────────────────────────
pub struct ConfigDoc { pub root: Body, pub origin: Origin }          // Origin::Text | Origin::Rap{ctx_version: u32}
pub struct Body { pub items: Vec<Node> }                              // source order; duplicates kept
pub enum Node {
    Class { name: Ident, base: Option<Ident>, body: Body, trivia: Trivia },
    Value { name: Ident, value: Scalar, trivia: Trivia },
    Array { name: Ident, elems: Vec<Elem>, trivia: Trivia },
    Directive { raw: Vec<u8> },           // #include/#define line, kept verbatim
    Opaque { raw: Vec<u8> },              // recovery island for malformed text; re-emitted as-is
}
pub struct Scalar { pub kind: ScalarKind, pub raw: Vec<u8> }         // raw = exact lexeme incl. quotes
pub enum ScalarKind { Str, Int(i32), Float(f32), Bare }               // Bare: unquoted non-numeric
pub struct Trivia { pub leading: Vec<u8>, pub between: Vec<u8>, pub trailing: Vec<u8> } // ws/comments/EOL
pub struct Ident(Vec<u8>);                                            // compare ASCII-case-insensitively

// ── ofp-mission: typed lens ──────────────────────────────────────────────
pub struct VehicleId(u32); pub struct SyncId(u32); pub struct TerrainObjectId(i32);
pub struct VarName(Bytes); pub struct MarkerName(Bytes); pub struct ClassName(Bytes); pub struct AddonName(Bytes);
pub struct Bytes(Vec<u8>);                     // raw on-disk bytes; encoding is metadata, not a conversion
pub struct NodePath(Vec<u32>);                 // path into ConfigDoc (child indices)
pub struct RawToken(Bytes);                    // original enum spelling, e.g. b"WIN", b"play"

pub struct Field<T> { pub value: T, pub at: Option<NodePath> }   // None = defaulted (absent in file)
pub struct EnumField<E> { pub value: E, pub raw: Option<RawToken> }

pub enum Side { West, East, Guer, Civ, Unknown, Enemy, Friendly, Logic, Empty, Other(RawToken) }
pub enum WaypointType { Undef, Move, Destroy, GetIn, SeekAndDestroy, Join, Leader, GetOut, Cycle, Load,
    Unload, TransportUnload, Hold, Sentry, Guard, Talk, Scripted, Support, And, Or, Other(RawToken) }
pub enum TriggerType { None, EastGuarded, WestGuarded, GuerGuarded, Switch, End(u8 /*1..=6*/), Lose, Other(RawToken) }
// …same pattern for PlayerRole, Lock, Rank, Special, Age, Semaphore, Formation, Speed, Behaviour,
//    ShowWp, ActivationBy, ActivationType, MarkerShape, TitleType, TitleEffect, CamPosition.

pub struct Position { pub x: f32, pub y_up: f32, pub z: f32 }   // engine order {x, height, z}

pub struct Mission { pub version: Field<i32>, pub sections: [Section; 4], pub legacy_intel: Option<Intel>, pub doc: ConfigDoc }
pub struct Section { pub at: NodePath, pub addons: Vec<AddonName>, pub random_seed: Field<i32>, pub hud: HudFlags,
    pub intel: Intel, pub groups: Vec<Group>, pub empty_vehicles: Vec<Unit>, pub markers: Vec<Marker>, pub triggers: Vec<Trigger> }
pub struct Unit { pub at: NodePath, pub id: VehicleId, pub side: EnumField<Side>, pub vehicle: ClassName,
    pub position: Position, pub azimut: Field<f32>, pub var_name: Field<Option<VarName>>, pub init: Field<Bytes>,
    pub player: Field<EnumField<PlayerRole>>, /* … every §3.3 key as Field<…> … */ }
pub struct Trigger { pub at: NodePath, pub syncs: Vec<SyncId>, pub attached: Attachment, pub effects: Effects, /* … §3.5 */ }
pub enum Attachment { None, Vehicle(VehicleId), TerrainObject(TerrainObjectId), House { obj: TerrainObjectId, pos: i32 } }
```

**Unknown keys** are never modelled. They remain in the `ConfigDoc` untouched because the lens
only ever reads and writes known paths.

### 12.3 Byte-exact round-trip fidelity strategy

1. **Identity invariant.** For any input that parses, `render(parse(b)) == b`, including comments,
   directives, CRLF/LF mix, tabs vs spaces, duplicate keys, `Opaque` islands and trailing bytes.
   This is proven by property tests (§13).
2. **Edits are patches, not re-serialization.** Changing a value replaces only that `Scalar.raw`.
   A new key is inserted at the **engine canonical position**: after the nearest preceding
   sibling in the §3 order, using the parent's detected indent and EOL style.
3. **Keep defaults explicit.** Setting a key back to its default keeps it written, so the diff
   stays small. A separate command, "Normalize as engine", omits defaults.
4. **List edits.** Deleting or inserting an item renames the following `ItemK` classes and
   updates `items=` (the engine requires contiguous `Item0..N-1`).
5. **No renumbering on save.** New units get `max(id)+1` and new syncs `max+1`. Renumbering
   happens only on explicit normalize, which reuses the `Compact` and `CheckSynchro` semantics.
6. **Number formatting.** An unchanged value re-emits its raw lexeme. A changed float is emitted
   by a writer **profile**:
   - `Ofp196Text`: C `%f` of `f32 as f64`;
   - `CwrText`: `%f`, falling back to `%.9g` plus `.0` as in `ParamFileParse.cpp#L371-L388`.

   Test Rust `format!("{:.6}", v as f64)` against C `printf("%f")` semantics in a test before
   relying on it [U].
7. **Strings are bytes.** The editor never transcodes. Each file gets an encoding guess used
   only for display: UTF-8, or a legacy code page (1250/1251/1252) chosen by language.
   - Writing non-ASCII into a mission targeting 1.96 requires choosing a code page.
   - `$STR_…` tokens are stored and written verbatim; they are resolved only for display.
8. **Enum aliases.** An enum keeps its `RawToken` unless its value changes. `Other(raw)` round-trips
   verbatim, and the validator reports it as "the game will reject or skip this".
9. **Engine limit warnings:**
   - text values over 2047 bytes;
   - raw newlines in strings;
   - required keys missing;
   - `CheckSynchro`-invalid syncs;
   - more than 12 crew seats per group;
   - no player (single-player);
   - a `Mission`/`Intro` section with no groups (the game refuses to start it, §3.9);
   - unknown `addOns[]` (the whole load fails with `LSNoAddOn`).
10. **Safe writes.** Write to a temp file and rename atomically, keep `mission.sqm.bak`, and
    re-parse the output to assert typed-model equality before replacing the file.
11. **Editor metadata goes in a sidecar file** (e.g. `ofp-editor.meta.toml`), not in
    `mission.sqm`. The CWR editor drops unknown content on re-save, including CWR's own
    `Intel>>viewDistance`. [V: `SaveTemplates` builds a fresh `ParamArchiveSave` and serializes
    only `ArcadeTemplate` fields, `UIMapExtDisplay.cpp#L311-L331`.] Exclude the sidecar from our
    PBO export. The engine's own exporter packs every file in the folder (§9), so the sidecar
    would end up in engine-exported PBOs.

## 13. Round-trip test strategy (synthetic fixtures only)

These follow the IC fixture rules (`IC:AGENTS.md#L583-L604`): no game data in the repository, and
no CI dependency on a local install.

- **Hand-authored golden fixtures** under `crates/ofp-mission/tests/fixtures/`, owned by the
  project:
  - `minimal.sqm` (four empty sections plus Intel);
  - `all_keys_nondefault.sqm` (every key in §3 with a non-default value);
  - `defaults_explicit.sqm`;
  - `legacy_v6.sqm` (top-level Intel, `resistance`, `show`, `locked`, `playerOnly`);
  - `aliases.sqm` (`WIN`, `PLAY`, `P1 COMMANDER`, `1.000000`, lowercase tokens);
  - `unknown_keys.sqm`;
  - `comments_preproc.sqm`;
  - `crlf.sqm` / `lf.sqm` / `spaces_indent.sqm`;
  - `dup_keys.sqm`;
  - `items_mismatch.sqm` (missing and extra `ItemK`);
  - `long_init_2048.sqm`;
  - `cp1250_bytes.sqm` (non-ASCII bytes as `\x..` literals in the test source).
- **Generated fixtures:** an `SqmBuilder` test helper emits engine-canonical text. With
  `proptest`, random typed `Mission` → canonical render → parse must give an equal model. A random
  CST with injected trivia → render → parse → render must be byte-identical.
- **Engine-canonical writer checks:** expected bytes are derived by hand from the cited
  `Serialize` order and default rules. Include one test per writer rule in §2.2 (empty class,
  string array layout, `""` escaping, `%f` edge values: `-0.0`, `1e-5`, `16777217`, NaN
  rejection).
- **Binary:** our raP writer and reader round-trip; version-2/3/4 branch fixtures built
  byte-by-byte; adversarial cases mirroring CWR's hardening (varint over 32 bits, count larger
  than the remaining bytes, pool index gap, base on root).
- **PBO:** uncompressed, `Cprs` with a bad checksum, `Vers` header, 255-character names,
  truncated header.
- **Fuzzing:** `cargo fuzz` targets for `ofp-config::parse`, `parse_rap`, `ofp-pbo::read` and the
  HTML parser. They must never panic and must respect allocation caps.
- **Opt-in local corpus:** an `#[ignore]` test driven by `OFP_MISSIONS_DIR` asserts identity
  round-trip and no validator crash for each mission. It prints only hashes and counts, and
  nothing from the corpus is ever committed.
- **Optional external oracle job:** run CWR's `tools lint mission`, `config debin` and `pbo list`
  on our outputs (`CWR:apps/tools/Tools/commands/LintCommand.cpp#L160-L222`). This invokes them as
  a separate process; licensing is handled in the license research note.

## Open questions

1. Is the OFP 1.96 / CWA 1.99 text writer byte-identical to CWR's in areas other than the `%.9g`
   fallback, e.g. `addOnsAuto` order or CRLF? Answering this needs a 1.99 install and a diff of a
   freshly saved mission [U].
2. Which raP context version (2, 3 or 4) did OFP-era binarizers and BI's shipped missions use?
   Were missions in official PBOs binarized? [U]
3. Did OFP 1.96 support any per-language briefing files (`briefing.<lang>.html`)? [U]
4. ~~What is the exact Documents folder name CWR uses for missions?~~ Resolved in verification:
   `Documents\Cold War Assault\missions\` (and `MPMissions\`) on Windows, and the XDG data dir on
   Linux (§9) [V].
5. What is the encoding policy for missions that mix UTF-8 (CWR-saved) and legacy bytes? Should
   we offer "target: 1.96/1.99 (ANSI)" vs "target: CWR (UTF-8)" at save time? This is a product
   decision.
6. How exactly does the game use `position[1]` (the height) at spawn: recomputed from terrain or
   honoured? This decides whether the standalone editor needs island heightmaps before its first
   save [U].
7. Should we emit the MP lobby parameters and other description.ext keys through a typed editor,
   or keep description.ext as a CST-only document with snippets?

## Sources

**Code at the pinned commits** (all aliases resolve as defined in §0):
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.hpp`, `…/ArcadeTemplate.cpp`, `…/ArcadeTemplateFind.cpp`, `…/AI/Path/ArcadeWaypoint.hpp`, `…/AI/Path/AITypes.hpp`, `…/AI/AICenter.cpp`, `…/AI/AICenterStats.cpp`
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/IO/Serialization/ParamArchive.hpp`, `…/ParamArchive.cpp`, `…/IO/ParamFile/ParamFile.cpp`, `…/ParamFileParse.cpp`, `…/ParamFilePrivate.inc`, `…/ParamFileEval.cpp`, `…/IO/Streams/SerializeBin.cpp`, `…/IO/Streams/FileInfo.h`, `…/IO/Streams/SsCompress.cpp`, `…/IO/PackFiles.cpp`, `…/Core/SaveVersion.hpp`, `…/Core/Config/Configuration.cpp`
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapExtDisplay.cpp`, `…/UIArcadeWaypoint.cpp`, `…/UIArcade.cpp`, `…/UIArcadeMarker.cpp`, `…/UIMapDisplay.cpp`, `…/UIMapDisplayBriefing.cpp`, `…/UIMapDialogs.cpp`, `…/UI/Controls/UIControlsExt.cpp`, `…/UI/Controls/UIControlsHTML.cpp`, `…/UI/OptionsUI.cpp`, `…/UI/DisplayUI.cpp`, `…/UI/DisplayUIMenus.cpp`, `…/UI/Locale/MissionHtmlLocalization.cpp`, `…/UI/Locale/Stringtable/Stringtable.cpp`, `…/UI/Locale/Stringtable/CodepageTranscode.cpp`
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Network/NetworkServerMission.cpp`, `…/World/WorldInit.cpp`, `…/World/Scene/Object.cpp`, `…/Game/Commands/GameStateExt.cpp`, `…/Game/Commands/GameStateExtUi.cpp`, `…/Foundation/Common/GamePaths.cpp`, `…/Core/Profile/ProfileManager.cpp`, `…/Foundation/Platform/VersionNo.h`, `engine/Evaluator/EvalState.cpp`, `engine/Evaluator/express.cpp`, `apps/tools/Tools/commands/{LintCommand,ConfigCommand,PboCommand}.cpp`
- `ofpisnotdead-com/CWR-CE@b67bf3bd62`: the same paths. Files identical to CWR (hash-checked): `ArcadeWaypoint.hpp`, `SaveVersion.hpp`, `ParamArchive.*`, `ParamFile.cpp`, `ParamFilePrivate.inc`, `PackFiles.cpp`, `SerializeBin.cpp`, `SsCompress.cpp`, `ArcadeTemplateFind.cpp`, `UIArcade.cpp`, `UIArcadeMarker.cpp`, `UIMapDisplayBriefing.cpp`, `DisplayUIMenus.cpp`, `GamePaths.cpp`. Files that differ:
  - addon-message refactor only: `ArcadeTemplate.cpp`, `ArcadeTemplate.hpp`, `UIMapExtDisplay.cpp`, `UIArcadeWaypoint.cpp`;
  - `ParamFileParse.cpp`: only the `realpath` log buffer, so writer behaviour is unchanged;
  - stringtable/HTML fallbacks: `Stringtable.cpp`, `MissionHtmlLocalization.cpp`;
  - unrelated to mission serialization: `OptionsUI.cpp`, `DisplayUI.cpp`, `NetworkServerMission.cpp`, `UIControlsExt.cpp`.
- Added during verification: `BohemiaInteractive/CWR@ffc61838b7:README.md` (licensing), `engine/Poseidon/UI/Locale/MissionLanguageDetector.cpp`, `apps/cwr/GameBase/GameBase.cpp`, `engine/Poseidon/Foundation/Common/PlatformPaths_{win,posix}.cpp`, `engine/Poseidon/IO/PackFiles.hpp`, `engine/Poseidon/UI/DisplayUIMultiplayerWizard.cpp`, `engine/Poseidon/Foundation/Framework/DebugLog.hpp`.
- `iron-curtain-engine/iron-curtain@7b7fac7fa5:AGENTS.md#L255-L260`, `#L335-L341`, `#L399-L408`, `#L583-L604`, `#L676`

**External:**
- Real OFP-era mission sample (format evidence only; not to be copied into the repository):
  https://raw.githubusercontent.com/ofpkubi/OFP-CTI/master/mission.sqm
- BIKI pages attempted but blocked (HTTP 403): https://community.bistudio.com/wiki/Mission.sqm,
  https://community.bistudio.com/wiki/Event_Scripts

## Verification notes

Adversarial fact-check performed 2026-09-26 against the local pinned clones and the one external
URL.

**Confirmed against primary source.** All 20 flagged claims hold in substance.
- Claims 1–13 and 15–20 were checked line by line at the cited ranges.
- The sections, the default-omission macro, the enum tables and aliases, the %f/%.9g writer,
  CRLF/TAB output, the raP layout and 2047/4095-byte truncation all match the source.
- So do `Compact`/`CheckSynchro`, `$STR` read-time localization, legacy text decoding,
  description.ext readers, briefing section names, PBO export, `MAX_UNITS_PER_GROUP`/`MaxGroups`
  and user mission paths.
- CWR↔CE identity was re-checked by file hash and `git diff --no-index`.
- The ofpkubi sample confirmed `version=11`, `%f` floats, multi-line string arrays and `""`
  escaping (the fetched copy was truncated).

**Corrected or refined:**
- **Missing `version`:** now described as reader-dependent (the game fails; the editor silently
  loads nothing). "No upper-bound check" upgraded from [I] to [V].
- **Item-level leniency:** keys after a failing key keep `Init()` values, which differ from the
  serialization defaults in places. A missing `items` key fails the whole list. Possible
  ID-table hazard noted [I].
- **Array layout:** the rule is `IsNumerical(GetValue())`, so numeric-looking strings are written
  inline.
- **IsConsistent:** it enforces *at least one* player, not "exactly one". Added the game's
  refusal of sections with zero groups.
- **Intel:** added the CWR-only `Intel>>viewDistance`/`missionViewDistance` key.
- **§12.3 item 11:** "editor drops unknown content" upgraded from [I] to [V].
- **PBO:** clarified the on-disk bytes of `'Cprs'`/`'Vers'` and the entry order.
- **Game data license:** changed "proprietary" to APL-SA per the CWR README.
- **Open question 4:** answered (`Documents\Cold War Assault\`).
- **Citations:** fixed the IC `AGENTS.md` citations and the list of files that differ in CE.

**Not independently verifiable here:** OFP 1.96 / CWA 1.99 behaviour (all [I] rows in §11),
BIKI content (HTTP 403), and the sample file's byte-level whitespace and provenance.
