# Addons and mods

Research note 27 for **ofp-editor**, a standalone Rust re-implementation of the *Arma: Cold War Assault* (CWA; originally
*Operation Flashpoint*, 2001) mission editor. Question: how should the editor discover, load, show, depend on, launch
and reason about the game **addons** and **mods** a user has installed? Written 2026-09-27. It stands alone.

**Scope.** "Addons" and "mods" here are *game content*: PBO archives whose `config.cpp`/`config.bin` add or change
`CfgPatches`, units, weapons, islands and so on, grouped into mod folders. Our **editor plugins** (doc 22) are a
different thing: they extend the editor and its AI harness, never the game. §4.8 explains where the two meet.

**Pinned sources.** `BohemiaInteractive/CWR@ffc61838b7` (Remastered 3.05 engine source) and
`ofpisnotdead-com/CWR-CE@b67bf3bd62` (community continuation). Citation aliases expand mechanically:
`P:` = `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/`, `R:` = `BohemiaInteractive/CWR@ffc61838b7:` (repo root),
`CE:` = `ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/`, `CER:` = `ofpisnotdead-com/CWR-CE@b67bf3bd62:`.
Unless noted, the cited CWR files are byte-identical in CE (checked by file hash): `GameState.cpp`,
`ModCollection.{hpp,cpp}`, `ModSystem.cpp`, `ModId.cpp`, `WorldImpl.cpp`, `ParamFile.cpp`, `ParamFileCtx.cpp`,
`VehicleTypes.cpp`, `ModInstall.{hpp,cpp}`, `Configuration.cpp`, `NetworkClientOnMessage.cpp`. `AddonSystem.cpp`,
`ConfigParsers.cpp`, `QBStream.cpp`, `ArcadeTemplate.cpp` and `AppConfig.cpp` differ; the functions cited from them
match unless a `CE:` citation says otherwise.

**Epistemic tags.** **[V]** verified against the cited code, test or URL (retrieved 2026-09-27); **[I]** inferred from
verified facts, not run; **[U]** unknown. Nothing was executed against a game install. "Search snippet" marks a fact
seen only in a search-engine summary because the page itself refused the fetch.

## TL;DR

- **Engine layering [V].** Content roots are the base game, an auto-added `res` folder, and the `--mod`/`-mod=` list.
  They are searched **last-listed mod first, then `res`, base last**. A `dta\`/`addons\` PBO mounts under its file
  stem, and the first-mounted bank of a stem shadows every later one. The **last-listed** root with a `bin\config.*`
  **replaces the whole base config**. There is **no general loose-file overlay**: outside banks, `bin\` files, fonts
  and the mission/template scanners, loose files come from the game dir (§2.1). There are no signature checks, only
  product/format property filters, a `requiredVersion` gate and a silent drop of configs without `CfgPatches` (§2.2).
- **Config merge [V].** Every mounted addon config is ordered topologically by `requiredAddons` (preloaded addons
  first in each round) and merged field by field. The **owner** of a class is the first `CfgPatches` entry of the
  addon that *introduced* it; later patches keep the owner. A missing `requiredAddons` entry only warns. A cycle stops
  the merge of everything still unresolved (a critical error: logged in player builds, fatal under `--strict`).
- **Mission dependencies are narrower than people think [V].** The engine's `ScanRequiredAddons` counts only unit
  and empty-vehicle classes. Weapons, magazines, markers, effects, islands and script-created objects are not
  counted. At runtime, though, `NewVehicle`, `AddWeapon` and `AddMagazine` all check that the class's owner is
  activated; if it is not, CWR shows "addon missing" (the in-game editor silently registers the addon instead). A
  listed addon that is not installed fails the whole mission load (`LSNoAddOn`), and an MP client disconnects.
- **Classes from a replaced `bin\config` have no owner [V/I].** A total conversion that ships `bin\config.bin`
  (rather than addon PBOs) therefore leaves **no trace in `addOns[]`**. Our tracker must record mod-level requirements
  that `addOns[]` cannot express.
- **Ecosystem [V].** Big mods are still actively installed and updated: FDFMOD 1.35, CSLA, FFUR/SLX, ECP variants,
  WGL 5, Liberation (LIBMOD), OFrP, BAS, island packs. Game Schedule's 123 records range from **11 KB to 19.16 GB**
  (about 58 GB in all; doc 42 §3.1). Players install them through four channels: CWR's built-in MODS manager
  (papa-bear.cz), Fwatch/OFP Game Schedule (legacy 1.96/1.99 only), hand-made `-mod=` shortcuts, and mission packs
  shipped *inside* mod folders. Some mods are **launcher platforms** (CWE) that no `-mod=` line reproduces (§4.2).
- **Recommendation: model a "mod set" as a first-class, fingerprinted object** (ordered, named, tied to a target
  profile). Mirror the engine's mount and merge rules exactly in a pure `ofp-vfs` + `ofp-config` pipeline, with owner
  and access tracking and ported upstream tests. Give every catalog class **provenance** (layer, PBO, `CfgPatches`,
  "introduced by" / "modified by").
- **Recommendation: derive dependencies; never hand-edit them.** Write `addOnsAuto[]` with exact engine parity. Write
  `addOns[]` as the engine set ∪ the extended set (script literals, `description.ext` weapons, markers, effects) ∪
  user pins. Extended entries go only into `addOns[]`, which a re-save in a fresh in-game editor display never
  prunes. The stock editor can still drop an extra that matches a name it auto-listed at its previous save, even for
  another mission (§2.4), so our next open re-derives it. Export a manifest, and fold mod needs into the "Requires:"
  badge.
- **Preview uses the mission's resolved mod set** (`--mod "<abs>;<abs>"` on CWR/CE, `-mod=` names on 1.99). It also
  offers a **clean-room Preview** with only the required mods, and a **vanilla Preview**, so authors can prove their
  dependency list.
- **AI and campaigns [I].** The campaign-from-brief flow picks a mod set in step S0. Every class menu is computed from
  that set's catalog, so the model can never name an unloaded class. Knowledge overlays for mods ship as T0 content
  packs of our own text. A campaign has exactly one mod set (the game remounts only in the main menu).
- **Treat every PBO as hostile [I].** Enforce parse caps, confine `#include` to banks mounted in the same set, never
  execute config expressions or scripts, isolate failures per addon, and keep derived caches local only. We never
  redistribute addon content, and never download or install mods (open question 6).

## 1. Terms

| Term | Meaning here |
| --- | --- |
| **PBO / bank** | Bohemia archive (doc 07). Mounted under a *prefix*, the lower-case file stem for `dta\` and `addons\`. |
| **Addon** | One PBO whose root has `config.cpp`/`config.bin` with a `CfgPatches` class, loaded from an `addons\` root. |
| **`CfgPatches` name** | Identifier used in `requiredAddons[]` and in `mission.sqm` `addOns[]`. One PBO may declare several. |
| **Mod (folder)** | A directory mounted as a content root (`AddOns`, `Dta`, `Bin`, `Campaigns`, `Missions`, …); `@` is optional. |
| **Replacement mod** | Changes existing classes or data (FFUR, ECP, WGL); missions made with it usually still run without it. |
| **Total conversion** | Adds its own world (FDFMOD, CSLA, Liberation). It may replace the base `bin\config` outright. |
| **Launcher platform** | A mod that runs only through its own launcher (CWE: replaced main config, generated headers, folder renames). Doc 42 §2.8 `shape = "platform"`. |
| **Mod set** | *Ours:* an ordered, named list of mods for one target profile. It is the unit of loading, caching and Preview. |
| **Editor plugin** | *Ours (doc 22):* a T0/T1/T2 extension of the editor. It never enters the game's VFS or `addOns[]`. |

## 2. Engine mechanics (CWR 3.05 / CE source)

### 2.1 Where content comes from, and who wins

- **Mod list.** `--mod <a;b>` (the legacy `-mod`/`-mod=` spellings are normalized; `-nomap` is accepted but "currently no
  effect") [V: `P:Foundation/Platform/AppConfig.cpp#L86-L106`, `#L481-L489`, `#L517-L519`]. Relative entries resolve
  against `--mods-dir` if given, else cwd, then the `-C` game dir, then `<UserContent>/Mods`; failing that, the same
  roots are searched for a mod whose `mod.json` `modId` or `ModId` matches [V: `P:Core/ModCollection.cpp#L372-L391`].
  A candidate only counts if `LooksLikeMod` sees a content dir (`AddOns, Dta, Bin, Campaigns, Missions, MPMissions,
  Templates, SPTemplates, Anims, Fonts`) or a `mod.json`. An unresolved entry is a launch error, not a silent skip [V:
  `P:Core/ModCollection.cpp#L168-L194`, `#L331-L406`; `P:Foundation/Platform/AppConfig.cpp#L900-L926`]. (The header
  comment says Missions/MPMissions are *not* markers; the code disagrees, and the code wins [V:
  `P:Core/ModCollection.hpp#L37-L43`].)
- **`res` is an implicit first mod** when a `res` folder exists. This mirrors OFP:Resistance/CWA, which "baked
  `_MOD_PATH_DEFAULT "RES"`" into the engine; `--mod` entries take priority over it [V:
  `P:Foundation/Platform/AppConfig.cpp#L998-L1024`].
- **Search order is reversed [V].** `EnumDirectories` visits mods "last-listed … first, … matching the original strrchr
  tokenization", then the base dir [V: `P:Core/ModSystem.cpp#L49-L66`, `P:Core/GameState.cpp#L126-L148`]. Since `res`
  is prepended to the list, it is searched after every `--mod` entry and before the base.
- **Banks.** `Globals::Init` mounts `dta\*.pbo`, then `addons\*.pbo` (with config parsing), then `Campaigns\*.pbo`,
  each across all roots in that order [V: `P:Core/GameState.cpp#L262-L281`]. The prefix is the lower-cased file stem
  (`campaigns\<stem>` for campaigns). Language-suffixed PBOs replace their base in the same folder (`1985.cz` over
  `1985`). **A stem that is already mounted is skipped**, so the last-listed mod's `foo.pbo` shadows every other
  `foo.pbo` [V: `#L155-L234`, esp. `#L216-L220`; `P:IO/Streams/QBStream.cpp#L1478-L1497`]. A bank dropped by its
  after-open callback (a rejected addon config, §2.2) is removed, so a lower-priority `foo.pbo` then mounts; the product
  filter runs lazily at the first header read, so a product-refused bank probably keeps its stem [I, needs a probe:
  `P:IO/Streams/QBStream.cpp#L469-L490`, `#L642-L651`, `#L1332-L1370`]. No engine code reads a PBO `prefix` property [V by grep].
- **Loose files are not overlaid by relative path [V].** `AutoOpen` tries a mounted bank by prefix, then the loose file
  relative to the game dir, then a **mod-root alias** (first path component = a mod folder name, e.g. `@mod\sound\x`),
  then `anims\..\addons\<island>\…` normalization into a bank [V: `P:IO/Streams/QBStream.cpp#L64-L110`,
  `#L1501-L1564`]. `ResolveModOverride` (mod copy wins by relative path) is used only for fonts [V: `#L176-L189`,
  `P:Graphics/Rendering/Draw/Font.cpp#L191-L197`]. Mission, template and cutscene lists scan mod roots separately.
  CE adds `..` collapsing (no climb above the first component) and aliases after it, so `voice\..\@mod\voice\…`
  re-enters a mod root [V: `CE:IO/Streams/QBStream.cpp#L135-L196`, `#L1552-L1572`].

### 2.2 Acceptance filters (there are no signatures)

- **PBO properties** [V: `P:Core/GameState.cpp#L53-L102`]. A bank is refused when `product` is set and not one of
  "OFP: Cold War Crisis", "OFP: Resistance", "VBS", or when a `pboVersion` property is present (Arma-format PBOs).
  With `--encryption-required` (a server option), a missing `encryption` property also refuses it [V:
  `P:Foundation/Platform/AppConfig.cpp#L501-L503`].
- **`requiredVersion`** [V: `P:Asset/Addon/AddonSystem.cpp#L139-L171`]. The addon is rejected if any patch's value
  exceeds the running version. `VersionToInt("1.96")` = 1960 [V: `P:Core/Version.hpp#L7-L32`]. CWR and CE parse their
  version string "3.05 (…)" as 3050 [V: `P:UI/OptionsUIApp.cpp#L121-L136`, `P:Foundation/Platform/VersionNo.h#L3`]. A
  rejected addon's **bank is unmounted too**, since the after-open callback fails [V: `P:Asset/Addon/AddonSystem.cpp#L201-L227`,
  `P:IO/Streams/QBStream.cpp#L1365-L1369`]. So *the loadable catalog depends on the target version* [I].
- **No `CfgPatches`, no addon.** An addon `config.cpp`/`config.bin` with no (or an empty) `CfgPatches` fails the same
  check silently, so its config is never merged and its bank is unmounted. A PBO in `addons\` with no config at all
  stays mounted as plain data [V: `P:Asset/Addon/AddonSystem.cpp#L139-L143`, `#L173-L234`]. 1.99 behaviour is [U].
- **No `.bisign`/key system exists** (grep for `bisign|bikey|verifySignatures` finds nothing) [V]. CWR's MODS manager
  verifies downloads by size + SHA-256 (`VerifyModArtifact`) [V: `P:Core/ModInstall.hpp#L49-L50`]. The metadata
  filter is unit-tested upstream [V: `R:tests/unit/engine/Poseidon/Game/test_game_state_ext.cpp#L401-L417`].

### 2.3 How configs merge

1. **Base config** [V: `P:Asset/Addon/ConfigParsers.cpp#L179-L213`]. The first root (in search order) with
   `bin\config.cpp|bin` wins, and enumeration stops: a mod's `bin\config` **replaces** the base; it does not patch it.
   CWR then re-merges the base `config-extra.cpp` (CfgLanguages) [V: `#L125-L146`]. `resource.*` follows the same
   first-wins rule, with the base `resource-extra.cpp` merged back on top [V: `#L102-L123`, `#L233-L281`]. The
   stringtable does **not**: the base `bin\stringtable.csv` loads first and the first mod table found overlays its keys
   [V: `P:Core/Config/Configuration.cpp#L306-L311`]. Because `res` is a root, a classic layout's `res\bin\config.bin`
   would itself replace the base one [I]. Steam notes for 3.05: "Total-conversion mods can replace the base game
   configuration without unwanted vanilla classes appearing in the editor" [V: Steam news, 2026-08-17].
2. **Per-addon parse** [V: `P:Asset/Addon/AddonSystem.cpp#L131-L137`, `#L173-L234`]. The addon's config is parsed; the
   **owner** is the name of the *first* `CfgPatches` entry (`GetEntry(0)`, not filtered to classes), lower-cased and
   stamped recursively on every class [V: `P:IO/ParamFile/ParamFile.cpp#L1279-L1291`,
   `P:IO/ParamFile/ParamFile.hpp#L103`]. Each declared patch name is registered; a duplicate logs "Conflicting
   addon … previous definition in …" but the config is still merged [V: `P:Asset/Addon/AddonSystem.cpp#L162-L168`]. The PBO's root `stringtable.csv` joins the global stringtable.
3. **Ordering** [V: `P:Asset/Addon/AddonSystem.cpp#L304-L379`]. Configs are collected in mount order. Each
   `requiredAddons[]` name becomes an edge to the first config declaring it; **a missing requirement only warns and
   the addon still loads** (CE demotes CWR's `WarningMessage` to `LOG_WARN` [V: `CE:Asset/Addon/AddonSystem.cpp#L333`];
   CE issue #307 reports the same observation). Each outer round makes two greedy passes over the remaining configs
   in collection order, **preloaded first** (`CfgAddons >> PreloadAddons >> * >> list[]`, read from the base config
   before any addon merges), then the rest. A config with no unresolved edge is taken at once, and its edge is
   removed from all others, so a later config it unblocks can go in the same pass. When a round takes nothing, the
   engine raises "Circular addon dependency" and **stops; unresolved addons are never merged** (a self-requirement
   counts). The message is a critical `ErrorMessage`: logged in player builds, `exit(1)` under `--strict` (default
   in Debug/RelWithDebInfo) [V: `P:World/Simulation/Animation/FrameFunctions.cpp#L97-L127`,
   `P:Foundation/Platform/AppConfig.cpp#L569-L572`]. (Quirk: `preloaded` is overwritten per `CfgPatches` class, so
   the last class decides.)
4. **`Pars.Update` semantics** [V: `P:IO/ParamFile/ParamFile.cpp#L1874-L1999`]. Scalars and arrays override; missing
   classes are created *with the source owner*, while existing classes keep theirs; a class may be re-based. Access
   modes are honoured: read-only classes refuse updates, and add-only classes skip existing arrays and all scalars but keep
   merging (the code comment cites CSLA's `CfgVehicles`). A missing base class raises an error and abandons the rest
   of that class's update [V: `#L1908-L1916`]; a type-changing merge is unsupported (upstream "BUG-002", a disabled
   test in `R:tests/unit/engine/Poseidon/IO/ParamFile/test_paramfile_inheritance.cpp#L643-L677`).
5. **Consequence [I, needs a probe].** Two unrelated addons touching one class: the *later-merged* one wins. With the
   same preload flag and no edge between them, merge order is collection order: the last-listed mod's addons first,
   then earlier mods, `res`, base (within one folder, directory order). So the earlier-listed mod, or the base,
   wins over the later-listed mod; a non-preloaded mod addon still beats a preloaded vanilla one. Only a declared
   `requiredAddons` edge makes a patch reliably win. This is the reverse of bank shadowing (§2.1), so our model must
   implement both rules, not one.

### 2.4 Missions: `addOns[]`, activation and failure modes

- **Save** [V: `P:AI/ArcadeTemplate.cpp#L321-L352`, `#L1862-L1872`, `#L1910-L1941`]. For every unit and empty
  vehicle, `vehicle` is matched against `CfgPatches >> * >> units[]` (the *first* patch listing it) **and** the class
  owner. The result becomes `addOnsAuto[]`. Entries of the old auto list that are no longer found are deleted from
  `addOns[]`, and the new auto entries are added. Owner-less classes (base config, or a replacing `bin\config`) add
  nothing through the owner path; only a patch's `units[]` claim can name one. Both paths matter in practice: in
  vanilla, 40 of 71 public addon vehicles are missing from their own `units[]` and are named only through ownership,
  while CWE's `CWE_Standard` claims 168 vanilla classes in `units[]`, so every mission saved under CWE requires it
  (a live D3 case, §4.5) [V: doc 35 §6.1, §10].
  - **Pruning (corrected 2026-09-27; this line earlier said manual entries are never pruned).** The "old auto list"
    is the editor's *in-memory* list from its previous save. `ArcadeTemplate::Clear()` does not reset it and loading
    does not read `addOnsAuto[]` into it [V: `P:AI/ArcadeTemplateFind.cpp#L184-L203`,
    `P:AI/ArcadeTemplate.cpp#L1910-L1932`, `P:UI/Map/UIMapExtDisplay.cpp#L99-L133`; CE identical; doc 37 §10 (h)].
    A fresh editor display prunes nothing, but
    a manual entry can be pruned when it matches a name auto-listed at that previous save, including one made for
    another mission in the same editor display [V code; practical effect I].
- **Load** [V: `P:AI/ArcadeTemplate.cpp#L1875-L1906`, `#L1946-L1955`]. `addOns[]` is activated; any name absent from `CfgPatches` fails the
  section with `LSNoAddOn`. CE sorts and dedupes the message and blocks such missions in the SP list, together with
  a missing-world check [V: `CE:AI/ArcadeTemplate.cpp#L1892-L1971`, `CE:UI/OptionsUIImpl.cpp#L186-L218`]. An MP client
  disconnects with the missing list [V: `P:Network/NetworkClientOnMessage.cpp#L884-L908`].
- **Activation** [V: `P:World/WorldImpl.cpp#L1091-L1139`, `P:IO/ParamFile/ParamFileCtx.cpp#L94-L122`]. Active =
  preload lists + mission `addOns[]`. A class is "visible" if its owner is empty or active, checked up the parent
  chain. `NewVehicle`, `AddWeapon` and `AddMagazine` call `CheckAccessCreate` [V:
  `P:World/Entities/Vehicles/VehicleTypes.cpp#L461-L522`, `P:AI/VehicleAI.cpp#L1764-L1769`, `#L1983-L1988`].
  - In the in-game editor, `OnUnregisteredAddonUsed` just appends the owner to `addOns[]` [V:
    `P:UI/Map/UIMapExtDisplay.cpp#L2003-L2007`].
  - Elsewhere CWR warns "addon missing: `<owner>`" (first warning per mission only, §4.6) but still creates the
    object (the refusal branch is commented out).
    In an external `--test-mission` Preview, which has no editor display, this warning would fire [I]. 1.99's
    behaviour is [U].
- **Savegames** store the active addon list too [V: `P:World/WorldImpl.cpp#L1695-L1719`].
- **Editor lists ignore activation:** the unit, group and island dialogs list every `scope=2` class in `Pars` (doc 04
  §10); nothing in the editor code consults `CheckAddon` [V by grep].

### 2.5 Islands from addons

`CfgWorldList` names the islands. `CfgWorlds >> X >> worldName` gives the `.wrp` path (defaulting to `worlds\`,
`.wrp`), which for addon islands points into the island's PBO. The editor's island combo (`DisplayTemplateLoad`)
shows only worlds whose `.wrp` exists [V: `P:IO/ParamFileExt.cpp#L195-L205`,
`P:UI/Map/UIArcadeWaypoint.cpp#L483-L517`]. The island is **not** part of `ScanRequiredAddons` [V]; the mission
folder suffix `<name>.<World>` is the only link. CE open
issues ask for a loadable `Worlds` folder in mods (#260), report terrain animations outside PBOs (#261), and report
unpacked campaigns in mod folders not listed (#259) [V: CE issue list].

### 2.6 Remastered/CE mod management

- The **in-game MODS screen** scans `<UserContent>/Mods` (Local) and `<UserContent>/Workshop` (downloaded). A local
  mod shadows a downloaded one of the same id [V: `P:Core/ModCollection.hpp#L12-L35`, `#L118-L137`;
  `P:UI/OptionsUIApp.cpp#L1252-L1318`; `P:Foundation/Platform/AppConfig.cpp#L205-L223`, `#L491-L496`]. Changes
  apply by an in-process **remount, which is only allowed in the main menu** [V: `P:UI/OptionsUIApp.cpp#L1541-L1565`]. The
  catalog and downloads come from the master service, default `https://papa-bear.cz` [V:
  `P:Network/NetworkConfig.cpp#L7`], with staged, transactional installs [V: `P:Core/ModInstall.hpp#L52-L84`].
- **`mod.json`** fields read by the engine: `modId`, `name`, `version`, `packageRevision`, `sha256` [V:
  `P:Core/ModCollection.cpp#L25-L66`, `#L196-L231`]. Mod **identity** is the folder name verbatim; `ModId` normalizes
  it (basename, one leading `@` stripped, lower case) for matching server lists and catalog ids [V:
  `P:Core/ModId.cpp#L8-L43`]. A server advertises `modId`s, and joining can download and mount them [V:
  `P:Core/ModCollection.hpp#L77-L81`, `P:UI/DisplayUIMultiplayer.cpp#L1200-L1236`].
- **Update 3.05 (2026-08-17)** says mods "can provide their own single-player missions, multiplayer missions, editor
  templates, and intro cutscenes without files being copied into the player profile". The MODS manager "can now
  detect and install updated revisions" [V: Steam news API].
- The active mod collection is **not persisted** across restarts (CE #228 asks for it); CE #233 asks for mission
  dependency checks with per-file and per-mod hashes [V: CE issues].

### 2.7 Upstream tests to port, and gaps

All rows already exist in `docs/porting/upstream-test-map.csv`; porting updates their `status`.

| Upstream test | What it pins | Our target |
| --- | --- | --- |
| `R:tests/unit/engine/Poseidon/Core/test_mod_collection.cpp#L40-L385` (16) | `LooksLikeMod`, name verbatim, mount-path order, `ModLoader` dedupe, resolve order, catalog-id resolve, missing-mod errors (`ModId` only via one `MountPathForIds` check) | `ofp-install` (port) |
| `R:tests/unit/engine/Poseidon/Asset/Addon/test_config_replace.cpp` (+`CER:` `#L135` case) | mod `bin\config` replaces base; config-extra restored; bad resource falls back (CE) | `ofp-config` (port) |
| `R:tests/unit/engine/Poseidon/IO/ParamFile/test_paramfile_access.cpp#L281-L625` | access during update, locked arrays, owner set/query/filter/visibility | `ofp-config` (port) |
| `R:tests/unit/engine/Poseidon/IO/ParamFile/test_paramfile_inheritance.cpp#L410-L811` | merge keep/override/add/nested/arrays/idempotent; the access and owner cases assert only existence | `ofp-config` (port) |
| `R:tests/unit/engine/Poseidon/Game/test_game_state_ext.cpp#L401-L417`, `#L662-L852` | product/`pboVersion`/encryption acceptance, property header | `ofp-vfs` (port those cases) |
| `R:`/`CER:tests/unit/engine/Poseidon/IO/Streams/test_qstream_path_resolution.cpp` (`AutoBank` cases; CE `#L282`) | prefix matching; a mod path escaping its prefix (CE) | `ofp-vfs` (port) |
| `R:tests/unit/engine/Poseidon/UI/test_addon_content.cpp`, `CER:tests/integration/ui/main_menu/sp_mod_missions.test.*` | content-only mods; missing addons/world block a mission (CE-only asserts) | reference / probe |
| `R:tests/integration/scripting/{create_vehicle_empty_model,many_mag_slots_no_crash}.test.sqf` | `model=""` and >10 magazine slots are crash hazards in mod configs | reference (CSV); informs lint D8 |
| `R:tests/integration/mods/workshop_live_download.test`, `test_mod_install/selection/server_mod_resolve` | workshop, staging, MP negotiation | not-applicable |

**Gaps [V by grep of `tests/`]:** no upstream test covers `ParseAllAddonConfigs` ordering, preload priority, cycles,
`requiredVersion`, the no-`CfgPatches` drop, owner-from-first-`CfgPatches`, `Update` owner keeping,
`ScanRequiredAddons` pruning, or `CheckAddon`. We write these ourselves as known-value tests derived from the cited
code, each marked `oracle = "source-derived; confirm on 1.99"`, plus probe missions (§4.6). The synthetic mod
fixtures in `R:tests/fixtures/mods*/` are GPL and reusable (doc 20 §5).

## 3. The community ecosystem

| Mod | Kind | Verified facts |
| --- | --- | --- |
| FDFMOD ("finmod") | total conversion | "FDFMOD 1.35 is a new release after many years … a large pack of collected missions"; total conversion with its own islands and campaigns [V: Steam 3.05 notes]; `finmod` listed on Game Schedule [V]; FDFMod 1.3 for CWR: 4 campaigns, 51 SP and 1000+ MP missions, launched via a `.bat` [search snippet, Nexus]. |
| CSLA | total conversion | Named alongside FDFMOD as a total conversion [V: SITREP]; the engine carries a CSLA-driven merge fix [V: `P:IO/ParamFile/ParamFile.cpp#L1966-L1974`]; founded late 2001 (unverified). |
| FFUR / FFUR-SLX | replacement | "replacing and refreshing the original vanilla assets" [V: SITREP]; `@ffsx2007` 2.5 = 723 MB, `@ffsx85` 1.05 = 925 MB [V: Game Schedule API]; CE #306 is an FFUR-SLX animation bug [V]. |
| ECP | replacement | `@ECP (Original)` "Enhanced Configuration Project 1.085", 133 MB; `@ECP (REDUX)` 1.4 GB; `@ECP (TGS)` 31 MB [V: Game Schedule API]. |
| WGL | replacement | `@wgl5`, `@wgl5extra`, `@wgl_cti`, `@wgl_islandpack`, … listed [V: Game Schedule]; replaces infantry and tweaks AI (unverified). |
| Liberation 1941–45 | total conversion | `LIBMOD` listed [V: Game Schedule]; CWA launch option "-nosplash -mod=@LIBMOD" [search snippet, ModDB]. |
| OFrP, BAS, island packs, MFCTI | mixed | `@OFrP_Mod` 1.05, 217 MB, bundles Kegetys' editor addon, which replaced Mikero's "due to OFrP incompatibility" [V]; `@BAS` 213 MB, 148 MP missions; `@80+Islands1.3` 625 MB [V: Game Schedule]; MFCTI "is also available from the MODS storage" [V: Steam 3.05 notes]. |
| `@editorupdate` | editor addon | "Editor Update addon and 88 missions that use it", 31 MB [V: Game Schedule]: missions that *depend* on an editor addon are a real, shipped pattern (doc 09 P4/P5). |

- **Scale [V/I].** The Game Schedule home page listed about 128 mod names at first count (not re-checked). Its
  `mod=all` API returns **123 records (120 names)** whose sizes run from **11 KB to 19.16 GB**, about 58 GB in all;
  115 carry `req_version` "1.96" [V 2026-09-27: doc 42 §3.1; corrected from "77 records, 155 KB–3 GB"]. Large packs
  include `@FANB_MOD` (3 GB), `@ECP (REDUX)` (1.4 GB) and `@ffsx85` (925 MB) [V]. The game's own MODS storage (PB)
  holds 13 mods, 71 KB to 1.09 GB each (doc 42 §3.1). A play set is typically one base mod plus a few add-on packs [I].
- **Install and launch today [V].**
  - Remastered: the built-in MODS manager (papa-bear.cz storage).
  - Legacy 1.96/1.99: Fwatch's Mod Manager restarts the game "with a -mod parameter". It is "Not compatible with the
    remaster!" and identifies mods by an 8-character id in a `__gs_id` file.
  - OFP Game Schedule: installer scripts (`UNPACK`, `UNPBO`, `MAKEPBO`, `EDIT`, `IF_VERSION`, …) auto-download a
    server's mods.
  - By hand: `-mod=@a;@b` shortcuts (Kronzky's FAQ shows `-mod=@DynamicRange;@General`).
- **Mission distribution [V].** Missions travel inside mod folders (FDF, BAS, `@editorupdate`, `@cfogmissions`,
  `@vanilla_missions`), as loose PBOs, or via Game Schedule packages. CWR 3.05 made mod-supplied missions first-class.
- **Conflicts [V/I].** Examples: replacement mods patch the same vanilla classes; editor addons clash (OFrP); an
  island's post-mission cutscene "won't run if the island's anim folder is kept in a mod subdirectory" (Kronzky's
  FAQ, OFP-era); dotted mission folder names inside mods break the SP menu (CE #257).
- **Licensing [U/I].** Addon terms vary per author and are often absent or "ask first"; we could not verify a common
  licence. Policy: the editor only **reads** mods from the user's disk and never copies, re-packs, uploads or commits
  addon content. Derived caches (catalog DB, decoded icons) stay on the user's machine (doc 05 §7.1c). Test fixtures
  are synthetic addons we author, or GPL fixtures from upstream (doc 20 §5).

## 4. Design (proposal-only)

### 4.1 Principles

1. **Mirror the engine, then explain it.** Mount, shadow, merge, owner and activation rules are ported exactly and
   test-pinned. Every surprising rule (reversed priority, owner-less base classes, the missing-requirement warning)
   becomes a visible diagnostic, not hidden behaviour.
2. **The mod set is explicit state**, owned by the project and shown in the title bar. It is never implied by
   whatever happens to be installed.
3. **Dependencies are derived** from what the mission uses, with a reason chain per entry. Hand-edits are "pins",
   and never the source of truth (doc 17 §5).
4. **Vanilla-loadable by default** (doc 09 M10). Mods are opt-in per project, and the badge says what they cost.
5. **Game content is untrusted input**; plugins are a separate trust tier (doc 22).

### 4.2 Install probe, mod discovery and mod sets

- **Install probe (doc 05 §7.2, doc 08 §2.8).** Finds Remastered, legacy 1.99, CE builds and manual folders, and
  records `ExeKind`, version and roots.
- **Mod scan roots:** the game dir, `<UserContent>/Mods`, `<UserContent>/Workshop`, and user-added folders.
- **Game-folder addons [I].** Third-party PBOs dropped straight into the game's own addon folders are not a mod
  folder: they load with every launch, so "Vanilla" would silently include them. The scan compares the base roots'
  PBO stems with the stock list for the detected executable (names only) and shows extras as "Game-folder addons"
  with their own provenance chip; Vanilla-labelled AI menus leave them out unless the user opts in (doc 42 §4.1).
- **Mod identity:** `ModId` (engine normalization), folder name, `mod.json` fields and `__gs_id` when present. It
  also carries a content fingerprint (§4.7).
- **Mod sets** are named presets: an ordered list plus a target profile. "Vanilla" always exists. Importers read an
  existing `-mod=` line or a server's mod list. A mod set is valid for a target only if every mod resolves and
  `LooksLikeMod` holds.
- **Mod-set kind [V/I].** A *mod line* set is reproduced by `--mod`/`-mod=` alone. A **launcher platform** set (CWE,
  doc 35 §6.1) depends on launcher state: generated headers, launcher-selected PBOs, a declared stringtable. It
  records that `launcher_state`, which joins the fingerprint (§4.7) and the manifest (`shape = "platform"`, doc 42
  §2.8); lint D12 marks its provenance unverified (doc 42 §6.4). Plotroom never runs the launcher (doc 42 §6.2).

```rust
/// CfgPatches name (doc 04 `AddonName`): raw bytes, ASCII-case-insensitive Eq/Hash like the engine's stricmp.
pub struct AddonName(Bytes);
/// Engine-normalized mod id (P:Core/ModId.cpp): basename, one leading '@' stripped, lower case.
pub struct ModId(String);
/// Local handle for a stored mod-set preset. Newtype per AGENTS.md (from_raw/to_raw/Display).
pub struct ModSetId(u64);
/// BLAKE3 over a canonical manifest (§4.7); equal fingerprints ⇒ identical catalog.
pub struct Fingerprint([u8; 32]);

pub struct ModRef { id: ModId, folder: OsString, root: ModRoot, meta: Option<ModJson>, gs_id: Option<String> }
pub struct ModSet { id: ModSetId, name: String, target: TargetProfile /* doc 19 */, mods: Vec<ModRef> /* -mod order */,
                    kind: ModSetKind }
pub enum ModSetKind { ModLine, LauncherPlatform { launcher_state: Vec<LauncherInput> /* doc 42 §2.8 */ } }
pub enum ModRoot { GameDir, UserMods, Workshop, Custom(PathBuf) }
```

### 4.3 VFS layering and config merge (mirrors §2)

- **`MountPlan::from(mod_set, install)`** lists layers from lowest to highest priority: base, `res` (if present), then
  mods in `-mod` order. Bank mounting and `bin\` lookups walk it in reverse; bank stems dedupe first-mounted-wins, and
  each PBO records which layers it shadows. Path resolution follows §2.1 exactly (bank, game-dir loose file, mod-root
  alias, fonts override), not a generic overlay. `requiredVersion`, no-`CfgPatches` and product/format filters run
  per target, so a 1.99 plan can differ from a CWR plan over the same folders.
- **`AddonGraph`** holds per-addon state: `Merged { order }`, `RejectedVersion`, `RejectedNoPatches`,
  `RejectedMetadata`, `DroppedByCycle` or `ParseFailed`. It also holds the dependency edges (missing ones become
  diagnostics). Merge order follows §2.3 step 3 exactly, including the greedy in-pass unblocking.
- **`ConfigBase`** is `Vanilla` or `ReplacedBy(layer)`. `ofp-config` implements `update` with owner stamping and
  access modes, as the ported tests require.

```rust
pub enum LayerKind { Base, Res, Mod(ModRef) }
pub struct MountedPbo { layer: LayerIdx, root: BankRoot /* Dta|Addons|Campaigns */, stem: PboStem, shadows: Vec<LayerIdx> }
pub enum AddonState { Merged { order: u32 }, RejectedVersion { required: VersionInt }, RejectedNoPatches,
                      RejectedMetadata { key: &'static str }, DroppedByCycle, ParseFailed { diag: DiagId } }
pub struct AddonUnit { pbo: PboIdx, owner: AddonName /* first CfgPatches entry */, patches: Vec<PatchDecl>, state: AddonState }
```

### 4.4 Catalogs with provenance

- **One catalog per mod set.** It holds `CfgVehicles`, `CfgWeapons`, `CfgMagazines`, `CfgGroups`, `CfgMarkers`,
  effects, `CfgWorlds`/`CfgWorldList` and stringtables, built with doc 04 §10 rules.
- **Provenance per class:** `introduced_by` (base config layer or addon), `owner` (engine semantics), `modified_by`
  (every later addon or mod that patched it, with the fields it changed), and `patch_units_claim` (patches listing it
  in `units[]`).
- **`owner_from_stub` [V].** Set when the owner comes from an empty stub declaration in a helper addon that merged
  before the real definition: CWE's grenade pack declares an empty `Jeep`, so the engine stamps owner `bd_flashbang`
  on it, and exactly the CWE mission sections with Jeeps list that addon. Lint **D10** warns that every mission using
  the class will require that addon and shows the chain (doc 42 §2.1, §6.4).
- **UI.**
  - Mod filter chips and a "Mod" column in pickers, with search prefixes `mod:` / `class:` (doc 09 S8).
  - A coloured mod badge on map icons and entity rows. Mod folders rarely carry art, so the badge is a generated
    monogram unless the mod ships a picture [I].
  - Hovering a class shows "from `csla_units.pbo` (CfgPatches `CSLA_Units`) in `@CSLA`; patched by `@WGL5`".
  - A "Vanilla-safe" toggle hides owner-carrying and replaced-config classes. A "Diff mod sets" view lists classes
    added, removed or changed between two sets.

```rust
pub enum ClassSource { BaseConfig { layer: LayerIdx }, Addon { unit: AddonIdx } }
pub struct ClassProvenance { introduced_by: ClassSource, owner: Option<AddonName>,
                             modified_by: SmallVec<[(AddonIdx, FieldMask); 2]>, patch_units_claim: SmallVec<[AddonName; 1]>,
                             owner_from_stub: bool /* lint D10 */ }
```

### 4.5 Per-mission dependency tracking

**Collect uses** (typed model plus script lint, doc 23):

- unit and empty-vehicle classes;
- script string literals that resolve to a `CfgVehicles`/`CfgWeapons`/`CfgMagazines` class (in init fields,
  triggers, waypoints, `.sqs`/`.sqf`);
- `description.ext` gear pools, sounds, music and titles [I: which gear keys 1.99 reads is a doc 04 item];
- marker types, trigger effect classes, and the island;
- file paths into addon prefixes (`\csla_sounds\…`).

**Resolve each use** through the catalog to a `DependencyReason` → `AddonName` (owner, plus first `units[]` claimant
for parity) or → `ModNeed` (owner-less classes from a replaced `bin\config`; islands; path-only references). Take the
closure over `requiredAddons` for the *mod* list only. The engine does not need transitive names in `addOns[]` [I].

**Write rule (decision-critical).** It is grounded in the engine's pruning (§2.4; the default of writing the
extended set: answered 2026-09-27 → [D038](../decisions/D038-mod-handling-owner-additions.md) item 5):

| Array | Contents | Why |
| --- | --- | --- |
| `addOnsAuto[]` | exactly what `ScanRequiredAddons` would compute over this catalog | a later re-save in the in-game editor sees no change |
| `addOns[]` | `addOnsAuto` ∪ extended (weapons, magazines, script-created vehicles, markers, effects) ∪ user pins | extended entries prevent "addon missing" at runtime; the engine prunes only names in its in-memory auto list from its previous save (§2.4) |

Our editor prunes its own extended entries using the reason chains stored in the project sidecar, which is never
part of the mission. Missions keep byte-stable ordering and the original spelling of names already present
(doc 04 CST). The write rule stands after the §2.4 pruning correction: a re-save in a fresh stock editor display
prunes nothing we wrote, but a stock user who saved another mission in the same display first can lose extras that
mission auto-listed. The next open re-derives such entries from their reasons and shows the change (doc 37 §5
dependency doctor, PAT7) [V code; practical effect I].

**Lints** (problems panel, doc 09 S2):

- **D1** missing: the listed addon is absent from the active set. The mission still opens, with *ghost* entities.
- **D2** unused: a listed non-auto entry has no reason. Offer "remove" or "pin".
- **D3** replacement-only: the only reason is a `units[]` claim on a class the addon does not own, so the mission
  would run without it.
- **D4** owner-less mod class: `addOns[]` cannot express this need. It becomes a manifest-only requirement.
- **D5** `requiredVersion` above the target.
- **D6** an addon in a cycle, with a missing requirement, or with a config lacking `CfgPatches` (silently dropped).
- **D7** island from an addon.
- **D8** hazards from ported tests: `model=""`, more than 10 magazine slots.
- **D9–D12** are defined elsewhere: D9 redistribution guard (doc 34 mo10); D10 stub owner (§4.4), D11 master-server
  redirect and D12 platform launcher state (doc 42 §6.4).

**Never inject editor-only dependencies.** Entries come only from reasons. The active mod set, our plugins, T0
packs and preview helpers never add names. Opening and saving a mission without edits leaves its arrays unchanged,
except for exact-parity `addOnsAuto` recomputation, which the user can turn off.

**Dependency manifest (export).** A human `README` block plus JSON: mod ids, folder names, versions or
`packageRevision`, fingerprints, `CfgPatches` per mod, the island, the target and the reason summary. Per requirement
it also carries doc 42 §2.8's fields: `shape` (`mod` | `platform`), `need` (`required` | `recommended`, §4.9),
per-channel ids (`channels`: PB modId, GS 8-hex id, homepage) and, for platforms, `launcher_state`. Its fields
align with `mod.json` (`modId`, `name`, `version`) and Game Schedule names, so launchers can consume it (doc 09 CO9).
It is written next to the exported PBO by default, never into `mission.sqm`. Embedding it in the PBO is opt-in.

**Badge.** "Requires: CWR 3.05 · @CSLA (3 addons) · island `CSLA_Isle`". This takes the max of the target's script
requirements (doc 24 L8/L9) and the mods' `requiredVersion`s, and it opens the dependency panel.

```rust
pub enum DependencyReason { UnitVehicle { entity: EntityRef }, EmptyVehicle { entity: EntityRef },
    PatchUnitsClaim { class: ClassName }, ScriptLiteral { file: ScriptRef, span: Span, class: ClassName, kind: ClassKind },
    DescriptionExt { key: &'static str, class: ClassName }, Marker { marker: MarkerRef }, Effect { trigger: EntityRef },
    Island, AddonPath { file: ScriptRef, prefix: PboStem }, UserPinned }
pub struct DependencySet { addons: BTreeMap<AddonName, Vec<DependencyReason>>, mods: BTreeMap<ModId, ModNeed> }
pub struct AddonListPlan { addons: Vec<AddonName>, addons_auto: Vec<AddonName> } // write rule above
```

### 4.6 Preview and probe launches

- **Arguments.** `LaunchPlan` renders the mod arguments per executable:
  - CWR/CE: `--mod "<abs>;<abs>"` in mod-set order. Do not add `res`; the engine does.
  - 1.99: `-mod=<name>;<name>` relative to the game dir [I; whether absolute paths work on 1.99 is U].
  - Double-dash forms only (doc 08 §2.2).
- **Preflight** uses the same code as the lints: `LooksLikeMod` on every entry (CWR aborts on any unresolved one),
  D1/D5, D6 cycles (fatal if Preview passes `--strict`), and a mismatch between the mission's needs and the chosen set.
- **Three modes.**
  - Normal: the project mod set.
  - **Clean-room:** only the mods that provide reasons, plus their `requiredAddons` closure.
  - **Vanilla:** proves M10.

  A clean-room run that produces "addon missing" is a dependency bug that the harness log surfaces (doc 08 §2.5).
  CWR emits only the first warning per mission (`SINGLE_WARNING`, reset in `World::CleanUpInit`), so the log proves
  presence, never completeness [V: `P:World/Simulation/Animation/FrameFunctions.cpp#L30-L84`,
  `P:World/WorldInit.cpp#L1069`]; static lints stay the primary check.
- **Probes** (synthetic addons only):
  - reversed priority;
  - `bin\config` replacement;
  - the unrelated-patch merge winner (§2.3 step 5);
  - an unlisted weapon via `addWeapon`;
  - an addon with a missing requirement;
  - a cycle;
  - `requiredVersion` 2.0 on 1.99, and whether a lower-priority PBO of the same stem then mounts;
  - a product-refused PBO shadowing a same-stem PBO; a config without `CfgPatches`;
  - a loose mod file vs a base loose file of the same relative path.

  Each runs on 1.99 and CWR to settle the [U]/[I] rows.

### 4.7 Caching and invalidation

- **Mod-set fingerprint** = BLAKE3 over the canonical manifest:
  - target profile and exe version;
  - ordered layers;
  - for each mounted PBO: stem, size, mtime and a hash of its header plus config and stringtable entries;
  - loose `bin\*` hashes;
  - for a launcher platform set, its launcher-state inputs: the launcher-selected PBOs (such as the sound-system
    PBO), the generated headers (present or missing) and the declared stringtable (doc 42 §2.10, MAT16).

  At startup, a stat-only pass revalidates; any change re-hashes only the changed PBOs. The per-mod fingerprint is
  kept separately so it can align with CE #233's "sort per-file hashes, hash again" proposal if CE adopts it.
- **Cached per fingerprint** in the user cache dir, never in the project or the mission:
  - the merged catalog with provenance;
  - decoded icons and pictures;
  - island map tiles;
  - AI menus.

  Caches are LRU-bounded, and a mismatched schema version discards them.

### 4.8 The AI co-pilot and the campaign-from-brief flow

- **Mod set up front.** Step S0 (doc 25) gains a `mod_set` field. Its menu contains installed sets that are valid
  for the chosen target, plus "Vanilla". The model only *picks*; code resolves eras, sides and islands against that
  set's catalog.
- **Menus, not memory.** `catalog.units(side, era, role, kind)` gains a `mods` filter and returns only loaded class
  ids. V-catalog (doc 25 §7) rejects anything else and suggests the nearest match, so weak models cannot hallucinate
  classes.
- **Knowledge packs.** `llm:` overlays (doc 17 §7.2) are keyed by `(ModId, class)`. They are shipped as **T0 content
  packs** (doc 22), our own or community-written text, and never copied from the mod. Packs for unloaded mods stay
  inert. Addon `displayName`s and descriptions reach the model as quoted data (AGENTS.md "Untrusted content").
- **Swaps.** "Make this vanilla-safe" is a typed workflow. Code proposes role-equivalent vanilla classes; the model
  ranks at most 3 per entity; the user confirms. Human-edited entities are never swapped without asking.
- **Boundary.** Plugins may *describe* mods and propose edits. They never install mods, mount PBOs, or add runtime
  dependencies.

### 4.9 Campaigns that span mods

- A campaign runs inside one game launch. The engine remounts only from the main menu, so **a campaign has exactly
  one mod set** [V: §2.6]. Its dependency set is the union of its missions' sets. A lint flags missions whose needs
  exceed the campaign set.
- A campaign may be exported into a mod folder's `Campaigns\` (CWR 3.05). For 1.99 and CE #259, packed PBOs are the
  safe form [I].
- "Optional" replacement mods (D3-class) are recorded as *recommended*, not required.

### 4.10 Broken and malicious addons

- **Parsers** (AGENTS.md): pure `&[u8]`, caps on entry counts, name lengths, header size, LZSS output and ratio,
  config depth, class count, string length, `#include` depth and preprocessor output. Every guard is fuzzed, with
  adversarial tests per crate.
- **Filesystem.** Reject `..`, absolute and drive paths in PBO entries (the ported zip-slip cases). Resolve `#include`
  only inside the owning PBO or another bank mounted in the same mod set (by bank prefix, as CWE's version addon
  does), never through `..`, absolute paths or unmounted files (amended from "owning PBO or mod root", doc 42 §6.1);
  the engine resolves it against the cwd [V: `P:Asset/Addon/ConfigParsers.cpp#L61-L82`,
  `P:Asset/Addon/AddonSystem.cpp#L183-L194`], and we must not. A missing include is a per-addon diagnostic ("supplied
  by the platform launcher?"), not a failure. Do not follow symlinks out of a scan root.
- **Parser rules to mirror [V: doc 42 §6.1].** A scalar ends at `;` or at the end of the line; braces inside an
  unquoted value are ordinary characters, not balanced (`P:IO/ParamFile/ParamFile.cpp#L81-L103`, `#L1797-L1803`);
  `enum` constants; function-like macros (`##`, `#`, multi-line bodies, `#undef`/`#ifdef`/`#else`, a mid-line
  `#include` inside arrays); top-level classes outside `Cfg*`. Without the first two, CWE's `CfgVehicles` parse
  stopped at 13 public classes instead of 788. Each becomes a synthetic fixture with parser-security tests, including
  caps on macro passes, include depth and line joins.
- **No execution.** Config expressions (`db+0`, `EventHandlers`, `init` strings) are parsed as text only. Scripts in
  mods are linted, never run by the editor.
- **Isolation.** Parse each addon on a worker with a time budget. A failure marks *that* addon `ParseFailed` and
  carries a "the game would …" note where the engine would stop.
- **Display safety.** Strip control characters from names, and keep legacy code-page bytes raw (doc 04).

### 4.11 UX

- **Title-bar chip** "Mod set: CSLA + WGL5 (CWR 3.05)". It opens the **Mod Shelf**: drag to reorder, with live
  shadow/patch badges ("wins over @X for 12 classes"). Presets import from a `-mod=` line.
- **Dependency panel:** a tree of mods → addons → reasons. Clicking a reason focuses the entity or script span. It
  offers "Replace with vanilla…", "Pin" and "Remove", and a what-if ("drop @WGL5: 0 required, 41 cosmetic").
- **Opening a mission with missing mods never fails.** A banner lists what is missing. Ghost entities keep their raw
  classes and positions and stay editable, and the banner offers "Pick a mod set that has them".
- **Fun and trust:** "Preview as a player without mods" is one click. Exports show "Runs on: vanilla ✗ · with @CSLA ✓".

### 4.12 Phased plan

| Phase | Deliverable | Evidence |
| --- | --- | --- |
| M0 (with doc 07 crates) | `ofp-pbo`, `ofp-config` `update` + owner + access; synthetic addon builder | ported `test_paramfile_access/inheritance`, `test_config_replace`; fuzzers |
| M1 | install probe, mod scan, `ModSet`, `MountPlan`, `AddonGraph`, provenance catalog, fingerprint cache | ported `test_mod_collection`; own ordering/cycle/version tests; opt-in corpus test on the user's mods |
| M2 | dependency engine, write rule, lints D1–D8, manifest, badge, ghost entities | parity tests vs `ScanRequiredAddons` rules; round-trip byte tests |
| M3 | Preview modes + probe missions | probe results recorded for 1.99 and CWR |
| M4 | AI menus by mod set, S0 field, T0 overlay packs, vanilla-safe swap workflow | eval: zero unloaded classes admitted |
| M5 | campaign mod sets, launcher-compatible manifest, upstream proposals (CE #228/#233) | campaign lint tests; CE discussion links |

## Open questions

1. **1.99 behaviour (probes):** reversed `-mod` priority; `bin\config` replacement; merge winner for unrelated patches;
   `addWeapon` of an unlisted addon's weapon (warning, refusal or silent); absolute paths in `-mod=`; the effect of
   `requiredVersion` [U].
2. What the vanilla `CfgAddons >> PreloadAddons` lists contain, and which vanilla classes carry owners. This needs the
   user's install, and nothing may be committed [U]. **Partly answered (doc 35 §10) [V]:** the preload lists are
   `WeaponBIStudio` (9 addons), `MiscBIStudio` and `ResistanceBIStudio`; base-config classes have no owner; 40 of 71
   public addon vehicles are missing from their own `units[]` and are named through ownership (§2.4). The full
   per-class owner table stays a local, uncommitted artefact.
3. Should the extended set (§4.5) be written by default, or only offered as a lint? It is an owner decision. The
   engine-parity-only mode stays available. (answered 2026-09-27 →
   [D038](../decisions/D038-mod-handling-owner-additions.md) item 5: written by default, with the engine-parity-only
   mode kept.)
4. After a mod replaces `bin\config`, do base `AddOns\` classes still appear (the 3.05 note suggests not; the code
   still mounts them) [U].
5. Manifest location and schema: next to the PBO, inside it, or both; and whether to align with papa-bear catalog
   ids or with a CE #233 hash format if one lands.
6. Should the editor ever *install* mods (network)? This note assumes no: installing stays with the game's MODS
   manager, Fwatch or Game Schedule, and we deep-link at most. **Answered: never (doc 42 §3).** Plotroom never
   downloads, installs, unpacks or mirrors mods; it links out and hands installs to the channels' own tools. An
   opt-in, read-only metadata connector is proposal-only, blocked on the `feed` connector decision (doc 42 §3.3–§3.4).
   (The `feed` kind: decided 2026-09-27 → [D008](../decisions/D008-outbound-network-sources.md); the connector still
   waits for the channel maintainers' non-objection, answered 2026-09-27 →
   [D035](../decisions/D035-outreach-and-security-disclosure.md) item 4. The install hand-off, a user-clicked "Launch
   the game to install mods" for CWR and CE targets: answered 2026-09-27 →
   [D038](../decisions/D038-mod-handling-owner-additions.md) item 1.)
7. Policy for D3 replacement-only claims: drop them silently, warn, or keep for parity with in-game re-saves.
8. Language-suffixed PBO variants and `GFileBankPrefix` banks in the mount plan [U].
9. Where the CWR and 1.99 installs keep the stock config (`bin\` vs `res\bin\`), and hence whether vanilla itself is a
   "replaced" config in our model [U].

## Sources

**Engine source (pinned):** all `P:`/`CE:`/`R:`/`CER:` citations inline; key files:
`P:Asset/Addon/AddonSystem.cpp`, `P:Asset/Addon/ConfigParsers.cpp`, `P:Core/Config/Configuration.cpp`,
`P:World/Simulation/Animation/FrameFunctions.cpp`, `P:Graphics/Rendering/Draw/Font.cpp`, `P:Core/GameState.cpp`, `P:Core/ModSystem.cpp`,
`P:Core/ModCollection.{hpp,cpp}`, `P:Core/ModId.cpp`, `P:Core/ModInstall.hpp`, `P:Foundation/Platform/AppConfig.cpp`,
`P:IO/Streams/QBStream.cpp`, `P:IO/ParamFile/ParamFile.cpp`, `P:IO/ParamFile/ParamFileCtx.cpp`,
`P:AI/ArcadeTemplate.cpp`, `P:World/WorldImpl.cpp`, `P:World/Entities/Vehicles/VehicleTypes.cpp`, `P:AI/VehicleAI.cpp`,
`P:UI/Map/UIMapExtDisplay.cpp`, `P:UI/OptionsUIApp.cpp`, `P:Network/NetworkConfig.cpp`,
`P:Network/NetworkClientOnMessage.cpp`, `CE:AI/ArcadeTemplate.cpp`, `CE:UI/OptionsUIImpl.cpp`,
`CE:Asset/Addon/AddonSystem.cpp`; tests and fixtures under `R:tests/` and `CER:tests/`.

**Web (retrieved 2026-09-27):**

- Steam news API, app 65790: "Arma: Cold War Assault Remastered Update 3.05" and "SITREP … Update 3.05" (2026-08-17):
  <https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=65790>
- CWR-CE issues #228, #233, #307 and the issue list (#257, #259, #260, #261, #266, #306):
  <https://github.com/ofpisnotdead-com/CWR-CE/issues/228>, <https://github.com/ofpisnotdead-com/CWR-CE/issues/233>,
  <https://github.com/ofpisnotdead-com/CWR-CE/issues/307>, <https://github.com/ofpisnotdead-com/CWR-CE/issues?q=is%3Aissue+mod>
- OFP Game Schedule: <https://ofp-faguss.com/schedule/>, API <https://ofp-faguss.com/schedule/api?mod=all>,
  OFrP entry <https://ofp-faguss.com/schedule/show.php?mod=b7360a9f>, installer commands
  <https://ofp-faguss.com/schedule/install_scripts?lang=en>, repo <https://github.com/Faguss/OFP-Game-Schedule>
- Fwatch Mod Manager: <http://ofp-faguss.com/fwatch/modmanager/details>
- Kronzky's OFP FAQ, mod folders: <https://kronzky.info/theofpfaq/resistance/customize/modfolders.htm>
- ofpisnotdead.com hub (OFPMonitor, Game Schedule links): <https://ofpisnotdead.com/>; PAPA BEAR: <https://papa-bear.cz/>
- Search snippets only (pages refused fetch): Nexus FDFMod 1.3 <https://www.nexusmods.com/armacoldwarassault/mods/7>;
  ModDB Liberation <https://www.moddb.com/mods/liberation-1941-1945>; ModDB CSLA
  <https://www.moddb.com/mods/csla-mod-for-operation-flashpoint>; WGL/FDF/ECP summaries
  <https://www.twcenter.net/threads/operation-flashpoint-mods.32119/>. BIKI pages returned HTTP 403 and are not cited.

**Related notes:** docs/research/03, 04, 05, 07, 08, 09, 17, 19, 20, 22, 23, 24, 25, 26, 34, 35, 37, 42.

## Verification notes

Adversarial re-check, 2026-09-27, against the pinned clones and live URLs. Nothing was run against a game install.

- **Confirmed:** reversed search order and `res` placement (`res` searched after every `--mod`, before base);
  first-mounted-stem-wins bank shadowing; last-listed `bin\config` replaces the base; `requiredAddons` edges to the
  first declaring config; missing requirement = warning; cycle drops the unmerged remainder; owner stamped from the
  first `CfgPatches` entry and never rewritten by `Update`; `ScanRequiredAddons` counts only units and empty
  vehicles; `CheckAccessCreate` on `NewVehicle`/`AddWeapon`/`AddMagazine` warns and continues; the in-game editor's
  `OnUnregisteredAddonUsed`; `LSNoAddOn` and MP disconnect; product/`pboVersion`/encryption filters; the
  `requiredVersion` unmount; no signature system; `--mod`/`-mod=` normalization; `mod.json` fields; papa-bear.cz;
  the file-hash identity list (extended). The "earlier-listed wins for unrelated patches" inference follows from the
  code but stays [I] until probed.
- **Corrected:** loose files are *not* overlaid by relative path (`ResolveModOverride` serves fonts only; generic
  opens use bank → game-dir file → mod-root alias); `bin\stringtable.csv` is base-plus-overlay, not first-wins; the
  merge loop is greedy within a pass, and the preload list comes from the base config; the cycle error is fatal under
  `--strict`; only the first "addon missing" warning per mission is emitted (§4.6); an addon config without
  `CfgPatches` is dropped and unmounted (new `RejectedNoPatches`, lint D6); CWR's version integer is exactly 3050;
  "CE hardens" path handling → CE *adds* `..` collapsing and aliases; the base-config owner sentence; the `DisplayUIMultiplayer.cpp` and `AppConfig.cpp` line ranges; mod size range (155 KB–3 GB, not
  31 MB–1.4 GB) and the Game Schedule count (~128) (both superseded: see the consolidation pass below); the OFrP
  editor-addon detail; the LIBMOD launch string; the Kronzky quote (post-mission cutscene, not "intro").
- **Tests:** all named files exist at the stated paths and every one has a row in `docs/porting/upstream-test-map.csv`
  (statuses `todo`, `reference` or `not-applicable`, matching the table). Corrected ranges: `test_mod_collection`
  L40–L385 (16 cases, `ModId` only indirectly); `test_paramfile_inheritance` merge cases L410–L811, whose access and
  owner cases only assert existence. The missing-addon/world assertions of `sp_mod_missions` are CE-only. Added
  `test_game_state_ext.cpp` (metadata filters), which the table had missed.
- **Unverifiable here:** CSLA's founding date and WGL's scope (search summaries only); everything tagged [U] about
  1.99; whether a product-refused bank keeps its stem (lazy check, needs a probe); the classic `res\bin\config`
  layout.

### Consolidation pass (2026-09-27)

Corrections carried in from later research; each was checked against its source doc before it was applied.

- 2026-09-27, from doc 35 §10 (and §6.1): §2.4 confirmed; CWE's 168-class `units[]` claim added as a live D3 case;
  the 40-of-71 owner-path fact added to §2.4; open question 2 marked partly answered (preload lists, owner-less
  base config); "launcher platform" added to §1 and as a mod-set kind in §4.2 (`ModSetKind`), aligned with doc 42
  §2.8 `shape = "platform"`.
- 2026-09-27, from doc 37 §10 gap (h) and its engine review "Save-time pruning": §2.4's "manual `addOns[]` entries
  are never pruned" is corrected (the stock editor prunes against an in-memory auto list that survives loading
  another mission in the same display) [V code; practical effect I]. The TL;DR and the §4.5 write-rule table now say
  so; the write rule itself stands.
- 2026-09-27, from doc 42 §8.3 row 27 and its "Corrections carried" list: Game Schedule scale corrected in the TL;DR
  and §3 (123 records / 120 names, 11 KB–19.16 GB, about 58 GB, not 77 records and 155 KB–3 GB) [V 2026-09-27]; the
  home page's "~128" names was not re-checked and is labelled as a first count. Open question 6 answered ("never
  install", doc 42 §3). §4.10 amended (includes resolve only inside the owning PBO or a bank mounted in the same
  set; missing include = per-addon diagnostic) and given the doc 42 §6.1 parser rules. Launcher-state inputs added
  to §4.7; `owner_from_stub` (lint D10) to §4.4; the §2.8 fields (`shape`, `need`, `channels`, `launcher_state`) to
  the §4.5 manifest; game-folder addons (doc 42 §4.1) to §4.2. A pointer to lints D9–D12 was added to §4.5.
- No "Field Manual", "Boot camp"/"Bootcamp"/"Academy", doc 33 or `skills/field-manual` references exist in this
  doc, so the rename to Standing Orders / Drill needed no edits here.

### Owner answers folded (2026-09-27)

- 2026-09-27: folded by pointer, original words kept: open question 3 and the §4.5 write rule's default → D038 item 5
  (OWQ-18); open question 6's `feed` blocker → D008, its channel-maintainer wait → D035 item 4 (OWQ-12), and its install
  hand-off → D038 item 1 (OWQ-17). No recommendation here contradicts an answer.
