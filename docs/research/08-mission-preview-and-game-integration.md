# Mission Preview and Game Integration

> Research report 08 for `ofp-editor`: a standalone Rust re-implementation of the
> *Arma: Cold War Assault* (CWA; originally *Operation Flashpoint: Cold War Crisis*, 2001) mission editor.
> Question: how can our editor's **Preview** button start the real game and play the mission being edited?
> Date: 2026-09-26. Sources: pinned source snapshots `BohemiaInteractive/CWR@ffc61838b7` and
> `ofpisnotdead-com/CWR-CE@b67bf3bd62`, the CWR-CE issue tracker, and Steam/GOG metadata APIs.

**Epistemic tags used below:** **[V]** means verified (a source or live metadata is cited). **[I]** means
inferred from verified facts but not tested at runtime. **[U]** means unknown or unverified. No part of this
report was checked against a running game: nothing was executed.

## TL;DR

- **Zero-patch auto-start exists today [V].** The Remastered client `PoseidonGame` accepts
  `--test-mission <folder-or-mission.sqm>`. It copies the mission to a temp stage, loads it and drops the player
  straight into gameplay, using the same steps as the in-game editor's **Preview** button. The engine's own
  test runner (Trident) uses this flag for every mission test. **Pass the folder, without a trailing
  separator:** the `mission.sqm`-file form stages only the file (as `…/Missions/mission.sqm`), losing the
  `<name>.<Island>` folder name, so by static reading nothing starts (§2.4 A) [I].
- **Side effect: "autotest" mode [V].** `--test-mission` sets the global `AutoTest` flag. Any SQF/SQS script
  error aborts the game (exit code 2), and mission end, player death or *Abort* quits the process. For a preview,
  "quit returns you to the editor" is fine. Aborting on script errors is harsh but is also useful diagnostics.
  The abort also covers errors in harness `eval`/`exec` text, so one bad debug-console line or watch expression ends
  the session; a console that survives its own errors needs a launch that is both non-`AutoTest` and `--no-strict`
  (design gap, §4.4) [V static].
- **Live link exists today [V].** `--harness <port|0>` opens a loopback-only TCP server that speaks
  newline-delimited JSON. It supports `eval`/`exec` of SQF, `screenshot`, `query`, key injection and `exit`, and
  emits `ready`/`display` events. The editor can drive a running preview with it: stop, teleport the player,
  a debug console, and screenshots for the AI agent. The option is only hidden from `--help`; it is not gated to
  dev builds. The schema's `click` and `wait_display` commands are **not** registered by `PoseidonGame` (§2.5).
- **Opening a mission straight into the in-game editor is not reliable [V]/[U].** In source, a positional
  `…/name.Island/mission.sqm` argument calls `OpenEditor()`. A CWR-CE organization member (her001) says instead
  that a positional mission file goes "straight into a mission" without `--test-mission`, and that there is
  "no way right now to open it in the editor" (issue #35). Both readings conflict; treat as unverified until tested.
- **Upstream:** `BohemiaInteractive/CWR` is locked and accepts no pull requests [V]. The community continuation
  is **CWR-CE**. Its launch code is byte-identical to CWR for everything relevant here [V]. It has an open
  request for editor-launch flags (#35) and no pull request implementing them [V].
- **Install discovery [V].** Steam app **65790** ("Arma: Cold War Assault Remastered") installs to
  `steamapps/common/ARMA Cold War Assault/`. Remastered runs as `Remastered/PoseidonGame(.exe)` and legacy 1.99
  as `ColdWarAssault.exe`. The free demo is app **4819000** and ships `PoseidonGameDemo`, which has **no editor
  module**. GOG product **1207658661** is Windows-only, version 3.0.5.
- **Profiles and missions [V] (from source, not checked on a shipping install).** User data is in `%APPDATA%\CWR` (profiles under `Users\<name>\`). Editor
  missions are in `Documents\Cold War Assault\missions\<name>.<Island>\mission.sqm`. The Linux and macOS
  equivalents and the `POSEIDON_*` environment overrides are listed in §2.8.
- **Recommendation:** ship Preview in phases:
  1. **P1:** stage a snapshot of the mission and launch `PoseidonGame --test-mission <stage> --window --no-splash --no-strict --harness 0`.
  2. **P2:** add live-link features over the harness.
  3. **P3:** upstream a small `--preview-mission` / `--edit-mission` patch to CWR-CE that plays without
     `AutoTest` and can show the briefing.
  4. **P4:** MP preview through a local `PoseidonServer --private` plus a client with `--connect 127.0.0.1`.
  5. **Always:** keep the zero-patch "export and open the game" fallback for legacy 1.99 and unknown builds.
- **Features that need no engine changes (built by editing a staged copy):** "Preview from camera position"
  (move the player unit in the staged `mission.sqm`), "Preview Intro/Outro" (stage the section as `class Intro`
  beside a group-less `Mission`, so `StartAutoTest` plays it in intro mode; §4.2, corrected from doc 32 §4.3),
  and "Validate mission" (`--check --test-mission`, exit 0 plus the log line `AUTO-TEST SUCCESS`).

---

## 1. Context and terms

| Term | Meaning |
|---|---|
| **CWR / Poseidon** | *Arma: Cold War Assault Remastered*. Bohemia released its engine and game source (codename Poseidon) under GPL-3.0-or-later plus GPLv3 §7 additional terms, which grant no trademark rights. |
| **CWR-CE** | `ofpisnotdead-com/CWR-CE`, the community continuation. It publishes CI "rwdi" builds (RelWithDebInfo) for Windows, Linux and macOS [V]. |
| **Legacy / 1.99** | The classic 32-bit CWA 1.99 executable `ColdWarAssault.exe`. It still ships in the same Steam app [V]. Remastered and classic multiplayer are mutually incompatible [V] ([BI blog](https://www.bohemia.net/en/blog/Arma-Cold-War-Assault-Remastered-Out-Now)). |
| **Mission folder** | `<missionName>.<WorldName>/` containing `mission.sqm` (plus optional `description.ext`, `init.sqs`, `briefing.html`, `stringtable.csv`, …). The `WorldName` is the island class, for example `Noe`, `Eden` or `Demo`. |
| **PBO** | A packed mission archive named `<missionName>.<WorldName>.pbo`. |
| **ArcadeTemplate** | The engine's in-memory mission model (`CurrentTemplate`). The in-game editor edits it. |
| **AutoTest** | A global engine flag (`bool AutoTest`) that switches mission flow into test mode (see §2.4). |
| **Trident / `tri`** | The Rust test orchestrator in `engine/Trident`. It spawns the game with `--harness` and drives it through JSON over TCP. |
| **Harness** | The in-engine TCP server (`engine/Poseidon/Dev/Harness`) that Trident connects to. |

All engine citations below point at CWR@ffc61838b7. Unless noted, the same files are identical in CE@b67bf3bd62:
`AppConfig.cpp` (differs only in one help string), `GameApplication.cpp`, `WorldImpl.cpp`, `DisplayUIMenus.cpp`,
`GamePaths.cpp`, `MissionPathLoader.hpp`, `HarnessServer.cpp` and `harness.schema.json`. This was checked by file
diff [V].

---

## 2. What the engine offers today

### 2.1 Executables and build flavours [V]

| Target | Role | Editor? | Evidence |
|---|---|---|---|
| `PoseidonGame` | Full client | **Yes**: `EditorModule::Register()` | `BohemiaInteractive/CWR@ffc61838b7:apps/cwr/Game/GameApplication.cpp#L1891-L1898` |
| `PoseidonGameDemo` | Demo client | **No**: the registration is commented out | `BohemiaInteractive/CWR@ffc61838b7:apps/cwr/GameDemo/GameDemoApplication.cpp#L5-L13` |
| `PoseidonServer` | Dedicated server, console | n/a | `BohemiaInteractive/CWR@ffc61838b7:apps/cwr/Server/ServerApplication.cpp#L143-L208` |
| `tri` (Trident) | Test orchestrator (Rust) | n/a | `BohemiaInteractive/CWR@ffc61838b7:tests/README.md#L43-L64` |

Without the Editor module, the `.sqm` branch in `World::StartIntro` is skipped, and that branch also covers
`--test-mission` (§2.4). **Preview therefore needs the full `PoseidonGame` binary.** CE docs say a full-game CE
build can run on the free demo data "to unlock usage of additional features (like the editor)" [V]
(`ofpisnotdead-com/CWR-CE@b67bf3bd62:docs/build/win.md`).

`--dev` is rejected in release builds, but **no other option is build-gated**. The `showOption(..., Dev)` wrapper
only hides an option from `--help`. The parser registers `--harness`, `--test-mission`, `--autotest` and
`--simulate` in every build [V] (`AppConfig.cpp#L287-L292`, `#L324-L337`, `#L602-L698`). Whether the *shipping
Steam 3.0x binary* matches this snapshot is **[U]** and must be tested (see Open questions). The pinned CWR and CE
sources both declare version `3.05` (`engine/Poseidon/Foundation/Platform/VersionNo.h`), the same as the GOG
installer (3.0.5), which makes a match plausible but does not prove it.

### 2.2 Command-line surface relevant to Preview [V]

The parser is CLI11 with `allow_windows_style_options()` and `allow_extras()`. Only four legacy single-dash
spellings are normalized: `-nosplash`, `-nomap`, `-oldpaths` and `-mod`/`-mod=`
(`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Foundation/Platform/AppConfig.cpp#L86-L106`).
**Always use the double-dash form** (`--name Foo`, not `-name=Foo`). Otherwise CLI11 splits single-dash tokens
as short options; `DescribeLaunchError` explains this pitfall at `#L246-L269`.

| Flag | Effect | Help level | Lines (`AppConfig.cpp`) |
|---|---|---|---|
| `--window` / `--fullscreen`, `--display-mode windowed\|borderless\|exclusive`, `-w/--width`, `-h/--height` | Window mode and size | Basic | L342-L354 |
| `--no-splash` (`-nosplash`) | Skip splash screens | Basic | L356-L357 |
| `--no-menu-scene` | **Skips `StartIntro()`, so a test or positional mission never starts.** Do not use it for Preview. | Basic | L358-L359; consequence at `GameApplication.cpp#L1731-L1734` |
| `--render dummy\|gl33\|auto` | Graphics backend | Full | L361-L364 |
| `--name <player>` | Profile/player name. Profile directory is `UserDir/Users/<name>/`. | Basic | L443-L445 |
| `--mod <a;b>`, `--mods-dir <dir>` | Mod mount list (semicolon-separated); base directory for relative names | Basic | L481-L489, L900-L926 |
| `--lang <Language>` | UI language | Basic | L498-L500 |
| `-C/--work-dir <dir>` | Game data directory (`DTA/`, `Worlds/`, …). Must exist. | Basic | L505-L508 |
| `--oldpaths` | Legacy layout: profiles, missions and mods live in the game folder | Basic | L513-L515 |
| `--check` | Init and exit. Combined with `--test-mission` it becomes the **mission smoke check**. | Dev | L524; `AppConfig.hpp#L239` |
| `--strict` / `--no-strict` | Any ERROR log becomes fatal. Member default is `false`. | Dev | L569-L573; `AppConfig.hpp#L419` |
| `--autotest` | Sets global `AutoTest` (§2.4) | Dev | L627, L1130 |
| `--harness <0..65535>` | Enables the TCP harness. `0` means auto port, announced as `HARNESS_PORT=N` on stdout. | Dev | L662-L666 |
| `--test-mission, --test <path>` | "Run mission folder or mission.sqm directly and exit" | Dev | L668-L670, L806-L808 |
| `--test-type autotest\|screenshot`, `-s/--screenshot <png>`, `--screenshot-delay N` | Capture a screenshot once gameplay starts, then exit | Dev/Full | L656-L658, L672-L676, L758-L759 |
| `--timeout <s>` | Auto-exit after N seconds | Dev | L638-L642 |
| `--log-file <path>`, `--log-format text\|jsonl`, `--log-level` | Structured logs for parsing | Basic/Full | L703-L727 |
| `--host`, `--connect <ip>`, `--port <n>`, `--connect-port`, `--password`, `--private/--lan`, `--config <cfg>` | Multiplayer; `--config` is the server config | Basic/Full | L391-L441 |
| `--mp-assign SIDE:SLOT`, `--mp-auto-start N`, `--force-jip` | MP automation used by Trident | Dev | L452-L462 |
| `--simulate <mission>`, `--duration <s>`, `--time-scale 1-16`, `--stats <s>` | Headless server-side mission run | Dev | L678-L698 |
| positional `mission` | "Mission file to load (.pbo or .sqm)". Copied into the global `LoadFile`. **The `.pbo` form is not handled by `StartIntro`**, which only accepts `.fps`, `.sqg` and `.sqm`. | Basic | L764-L765, L1132-L1137; `WorldImpl.cpp#L2222-L2258` |

There are **no** `-world=`, `-profiles=`, `-mission=` or `-init=` style options [V]: none appear in the parser.
The legacy 1.99 executable's own option list is documented on the BI wiki ("Operation Flashpoint: Startup
Parameters"), but that page returned HTTP 403 to this session **[U]**.

Useful environment variables [V] (`GamePaths.cpp#L54-L121`, `AppConfig.cpp#L205-L223`): `POSEIDON_USER_DIR`,
`POSEIDON_USER_CONTENT_DIR`, `POSEIDON_CACHE_DIR`, `POSEIDON_TEMP_DIR`, `POSEIDON_MODS_DIR` and
`POSEIDON_WORKSHOP_DIR`. When `POSEIDON_USER_DIR` is set, user content goes to `<USER_DIR>/content/`. This is how
Trident sandboxes runs (`GamePaths.cpp#L59-L66`; `engine/Trident/src/scenarios/integration.rs#L1154-L1157`).

### 2.3 How the in-game editor's Preview works (baseline to replicate) [V]

Source: `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapExtDisplay.cpp#L529-L614` (the same code
is at CE `#L452`).

1. `_currentTemplate->IsConsistent(this, _multiplayer)` must pass. The button is hidden while the template is
   inconsistent, and in MP it is also hidden until the mission has a filename (`#L410-L427`).
2. `ScanRequiredAddons()`.
3. **MP:** save to `GetMissionsDirectory()/<name>.<world>/mission.sqm`, then `Exit(IDC_OK)` hands off to the
   hosted-server flow. It is not played in place.
4. **SP:**
   1. `CurrentTemplate = *_currentTemplate`
   2. `SwitchLandscape(world)`, then `ActivateAddons(addOns)`, then `InitGeneral(intel)`, then
      `InitVehicles(GModeArcade, CurrentTemplate)`
   3. Delete `weapons.cfg`, `continue.fps`, `autosave.fps` and `save.fps` from the save directory.
   4. If **Shift** is held and a briefing exists, show `DisplayGetReady` (the briefing). Otherwise show
      `DisplayMission(this, true)`.
5. For the Intro and Outro sections, `InitVehicles(GModeIntro, …)` is followed by `DisplayIntro`.

Our standalone editor must reproduce step 1 (consistency checks) before launching, because the game will not
report the problem as nicely. Related: CE issue #185 reports that the in-game editor fails to open a
`mission.sqm` that lacks `class Intro/OutroWin/OutroLoose`. **Our writer should always emit those three
sections** [V] ([#185](https://github.com/ofpisnotdead-com/CWR-CE/issues/185)).

### 2.4 Direct-start paths already in the engine [V]

**A. `--test-mission <path>`**
(`BohemiaInteractive/CWR@ffc61838b7:apps/cwr/Game/GameApplication.cpp#L142-L187`, `#L1697-L1735`)

1. `StageTestMissionForGame` copies the folder (or file) to
   `<TempDir>/mission-smoke/<16 hex>/Missions/<name>.<Island>/`. `TempDir` defaults to `%TEMP%\cwr` on Windows
   and `/tmp/cwr` elsewhere (`GamePaths.cpp#L33-L46`, `#L97`). Per the code comment, the copy is removed on
   clean exit. The destination name is `srcPath.filename()`: for a `…/mission.sqm` input it is `mission.sqm`,
   and for a folder with a trailing separator it is empty, so the files land directly in `Missions/`. Either way
   `ProcessFullName` later finds a parent folder (`Missions`) with no `.<Island>` suffix and returns false, and
   `StartIntro` silently does nothing [I] (`GameApplication.cpp#L165-L187`; `MissionPathLoader.hpp#L56-L79`).
   The resolved path is copied into `LoadFile`, which `GameApplication.cpp` declares as `char[256]`, so keep the
   staged path under 255 bytes [I] (`#L1701`, `#L1715-L1716`).
2. `MissionPathLoader::ResolveMissionFile` accepts a directory (it appends `mission.sqm`) or a file literally
   named `mission.sqm` (case-insensitive). Anything else, **including `.pbo`**, logs an error and exits with
   **code 44** (`MissionPathLoader.hpp#L28-L54`; `GameApplication.cpp#L1706-L1713`).
3. It then sets `LoadFile = <staged>/mission.sqm` and `AutoTest = true`, and logs `Test mission: <in> -> <staged>`.
4. `World::StartIntro()` sees the `.sqm` and, if the Editor module is registered, calls `ProcessFullName()`.
   That splits the folder name at its **last** dot into mission and world and calls `SetMission(world, name,
   parentDir)` (`UIArcadeWaypoint.cpp#L904-L918`; `WorldImpl.cpp#L2217-L2258`). Because the split is at the last
   dot, mission names may contain dots; unit tests confirm `coop.training.v2.Noe`.
5. `AutoTest` leads to `StartAutoTest()`: `ParseMission`, with a fallback to the Intro section if there are no
   groups, then `SwitchLandscape`, `ActivateAddons`, `InitGeneral`, `InitVehicles(GModeArcade)`, save cleanup and
   `DisplayMission` (`DisplayUIMenus.cpp#L2012-L2066`). **Apart from the Shift-for-briefing option, this is the
   same sequence the in-game editor uses for Preview**, with one difference that matters to our writer:
   `StartAutoTest` re-parses `mission.sqm` from disk and never calls `ScanRequiredAddons()`, so the `addOns[]`
   array we write is exactly what `ActivateAddons` receives, and a listed addon that is not installed fails the
   parse (`LSNoAddOn`) [I] (`engine/Poseidon/AI/ArcadeTemplate.cpp#L1934-L1955`).
6. If `StartAutoTest` fails and `--check` is absent, the process does **not** exit: it logs
   `StartAutoTest could not boot '…'` and stays up with no mission (unless `--strict` turns the ERROR into exit 3)
   [I] (`WorldImpl.cpp#L2239-L2251`; `GameApplication.cpp#L921-L930`). The supervisor needs a log watch and a timeout.

**B. Positional `…/<name>.<Island>/mission.sqm`, without `AutoTest`.** In source this calls
`ProcessFullName` and then `OpenEditor()`. `OpenEditor()` switches landscape and creates `DisplayArcadeMap`,
whose constructor calls `LoadTemplates(GetMissionDirectory()+"mission.sqm")`
(`DisplayUIMenus.cpp#L1979-L1990`; `UIMapExt.cpp#L2883-L2910`). The mission runs in place: there is no staging
copy. **Conflict:** on CE #35, her001 (GitHub association `MEMBER` of the CE organization) wrote: "If you just
want to go straight into a mission, it is even simpler to just add the mission file as a parameter. It doesn't
need `--test-mission`, which has different behavior. Still, there is no way right now to open it in the editor."
([comment](https://github.com/ofpisnotdead-com/CWR-CE/issues/35#issuecomment-5081007160), 2026-07-25). The
static reading says the positional `.sqm` opens the editor and never plays it, so both halves contradict it.
Status is **[U]** until tested. If the positional path really plays the mission, it is a zero-patch preview
**without** `AutoTest`, which would beat Option 2 (see P0).

**C. Positional path plus `--autotest`.** Same as A, but the mission runs in place (no staging) and the
`testMissionActive` render-when-unfocused behaviour and tri command registration are absent (`GameLoop.cpp#L194-L196`).

**Side effects of `AutoTest` (A and C)** [V]:

| Event | Behaviour | Source |
|---|---|---|
| SQF/SQS script error | `LOG_ERROR "Script error at '…': … (test mode — aborting)"`, exit code 2, graceful close | `engine/Poseidon/Game/Scripting/ExpressExt.cpp#L146-L165` |
| Mission ends (win/lose/`endGame`) | Runs `exit.sqs`, then `Exit(IDC_MAIN_QUIT)`, which quits the game instead of showing the debriefing and menu | `DisplayUIMenus.cpp#L984-L1007`; `OptionsUIApp.cpp#L944-L969` |
| Player killed | Skips `DisplayMissionEnd` and quits | `DisplayUIMenus.cpp#L966-L981` |
| Briefing | Not shown: goes straight to `DisplayMission` | `DisplayUIMenus.cpp#L2057-L2064` |
| `--check` plus `--test-mission` | Logs `AUTO-TEST SUCCESS` and exits 0 on the first mission frame; exits 1 if boot failed | `DisplayUIMenus.cpp#L931-L941`; `WorldImpl.cpp#L2241-L2249` |
| `tri*` SQF commands | Registered whenever `--test-mission`, `--harness` or `--dev` is present | `engine/Poseidon/Game/Commands/GameStateExtTestAudio.cpp#L2960-L2964` |
| Unfocused window | Keeps rendering in windowed mode | `engine/Poseidon/Core/Game/GameLoop.cpp#L194-L196` |

With `--test-type screenshot --screenshot out.png`, the game waits for `GModeArcade`/`GModeIntro`, renders the
number of frames set by `--screenshot-delay`, captures, and exits (`GameApplication.cpp#L956-L985`,
`#L1102-L1116`). This gives us free mission thumbnails, and visual feedback for the AI agent.

### 2.5 The Trident harness (live link) [V]

- Enable it with `--harness 0`. The engine binds **`127.0.0.1` only**, prints `HARNESS_PORT=<n>` to stdout, and
  uses listen backlog 1. There is no authentication (`engine/Poseidon/Dev/Harness/HarnessServer.cpp#L73-L155`).
  The harness is compiled into all builds: `Dev/Harness/*.cpp` is in the engine glob
  (`engine/Poseidon/CMakeLists.txt#L14-L37`). It starts in `RunMainLoop` when the port is at least 0
  (`GameApplication.cpp#L552-L594`, `#L1020-L1025`).
- The protocol is newline-delimited JSON, version 1
  (`BohemiaInteractive/CWR@ffc61838b7:engine/Trident/protocol/harness.schema.json#L1-L141`):
  - **Commands in the schema:** `ping`, `describe`, `key` (SDL scancode), `key_up`, `click{idc}`, `query{what}`,
    `screenshot{path}`, `wait_display{idd}`, `eval{code}` (returns `result`), `exec{code}`, `http_fixture` and
    `exit`. **`PoseidonGame` registers only** `ping`, `describe`, `exit`, `screenshot`, `eval`, `exec`,
    `http_fixture`, `key`, `key_up` and a game-state `query` (`players`, `mission`, `ngs`, `world`,
    `master_server_*`; not `display`) (`GameApplication.cpp#L556-L594`; `HarnessServer.cpp#L60-L62`). A source
    comment says `click`, `query=display` and `wait_display` "live in PoseidonUITest" (`#L1020-L1022`), and
    `RegisterUIQuery`/`RegisterWaitDisplay` (`HarnessBuiltins.cpp#L917-L963`) have no call site in the tree.
    Workarounds: UI clicks via `exec` of the test SQF command `triClick <idc>`
    (`GameStateExtTestAudio.cpp#L3003`), display changes via `display` events. Probe with `describe` at runtime.
  - **Events:** `ready{idd}`, `display{idd,name}`, `player_joined`, `player_left`, `mission_state`, `von_*` and
    `exit{code}`. The schema also lists a `log` event, but no emitter was found in the client, so use
    `--log-file` or stdout for logs instead **[I]**.
  - **Shapes:** requests look like `{"cmd":"eval","code":"getPos player"}`, responses like
    `{"ok":true,"result":"[…]"}`, and events like `{"event":"display","idd":46}`
    (`engine/Trident/src/protocol/types.rs#L8-L112`).
- `eval`/`exec` run arbitrary SQF in a session-scoped variable space (`HarnessBuiltins.cpp#L73-L112`). Plain SQF
  such as `player setPos [x, y, 0]` works; Trident's own editor test uses it (`tests/integration/ui/editor/editor_preview_save_load.test.sqf#L14-L33`).
  Test-only helpers include `triTeleportPlayerTo [x,up,z]` (raw engine axis order) and `triSetView`
  (`GameStateExtTestAudio.cpp#L947-L975`).
- Useful IDD values (`engine/Poseidon/Core/resincl.hpp`): `IDD_MAIN 0`, `IDD_ARCADE_MAP 26` (editor),
  `IDD_INTEL_GETREADY 37` (briefing), `IDD_MISSION 46`, `IDD_INTERRUPT 49` (pause menu) and
  `IDD_SELECT_ISLAND 51`.
- Trident's own spawn logic is a ready reference for process handling:
  - pass `--harness 0` and pipe stdout to read the port
  - use `kill_on_drop(true)`
  - set `-C` when the data lives elsewhere
  - look up the binary as `PoseidonGame` or `OFPR`, also checking `bin/` and sibling directories

  See `engine/Trident/src/client/instance.rs#L52-L167`, `#L302-L410`. `tri` also has a live SQF REPL and an
  `exec` subcommand (`engine/Trident/src/main.rs#L147-L180`).
- **Licensing caution [I]:** Trident's licence is ambiguous. The top-level README says all source in the
  repository except `thirdparty/` is GPL-3.0-or-later with §7 terms (`README.md#L49-L60`), but
  `engine/Trident/Cargo.toml#L6` declares `license = "MIT"` (same in CE). Assume GPL until the CE maintainers
  clarify. If `ofp-editor` uses a permissive licence, **do not copy Trident code**. Instead, re-implement the small JSON-lines client from the documented
  protocol. Talking to a GPL program over a socket or the command line is the usual "separate programs" case in
  the FSF GPL FAQ ("aggregate" entry, <https://www.gnu.org/licenses/gpl-faq.html#MereAggregation>). That page
  could not be re-fetched this session (connection refused), and this is not legal advice.

### 2.6 Dedicated server and MP [V]

- `PoseidonServer` reads a `--config` file whose `class Missions { class X { template = "name.World";
  cadetMode = 0|1; param1 = …; param2 = …; }; };` entries it cycles through. Without such entries it holds a
  mission vote (`engine/Poseidon/Network/NetworkServerSimulate.cpp#L502-L547`). A template is resolved as a
  `.pbo` bank or a folder `MPMissions/<t>/mission.sqm` (`#L567-L590`). `GetMPMissionsDir()` is `MPMissions/`
  relative to the working directory, or a temp directory in simulate mode (`OptionsUI.cpp#L826-L841`). Trident's
  dedicated-server fixtures copy the `.pbo` into `<server USER_DIR>/content/MPMissions/`, which suggests
  user-content MPMissions are searched as well **[I]**
  (`tests/integration/multiplayer/von_dedicated.test/test.toml`).
- A non-simulate server waits for players. A client joins with `--connect 127.0.0.1 --port N --name X`
  (`GameApplication.cpp#L1681-L1695`). The dev flag `--mp-assign WEST:1` auto-picks a slot, and
  `--mp-auto-start N` auto-starts once N players are ready, fully only in `--simulate` mode
  (`NetworkServerSimulate.cpp#L636-L657`, `#L792-L812`). Trident's MP runner builds exactly these argument lists
  (`engine/Trident/src/scenarios/multi.rs#L2247-L2298`).
- `--simulate <mission>` (server) copies the mission into MPMissions under a random prefix and runs it headless.
  It can be combined with `--duration`, `--time-scale` and `--stats`, and `--check` turns it into a smoke check
  (`NetworkServerSimulate.cpp#L413-L461`; `AppConfig.hpp#L242`). This is a candidate for a headless
  "validate MP mission" action.
- `--private`/`--lan` disables master-server publishing (`AppConfig.cpp#L417-L418`, `#L858-L861`). **Every
  preview server must pass it.**

### 2.7 Mission discovery, naming and export [V]

- **Editor ("user") missions:** `<UserMissionsBase>/missions/<name>.<World>/mission.sqm`. `UserMissionsBase` is
  the user-content directory, or the profile directory under `--oldpaths` (`OptionsUI.cpp#L129-L141`;
  `OptionsUIApp.cpp#L815-L826`). MP editor missions use `…/MPMissions/…`.
- **In-game "Save as" export modes** (`UIMapExtDisplay.cpp#L2190-L2264`):
  - *User mission*: folder only.
  - *Single mission*: `Missions\<name>.<World>.pbo`, **relative to the working directory**, which is the game's
    `Remastered/` folder.
  - *Multiplayer*: `MPMissions\<name>.<World>.pbo`.
  - *E-mail*: a temporary `.pbo`.
- The Single-mission menu also finds unpacked missions under an active mod's `missions/`
  (`OptionsUI.cpp#L881-L915`). The briefing is resolved by `FindLocalizedMissionHtmlFile(dir, "briefing")`
  (`#L202-L205`). At mission start, `init.sqs` runs and then `init.sqf`; the latter is a Remastered addition
  (`engine/Poseidon/UI/DisplayUI.cpp#L121-L144`).
- **Naming rules for our writer:** the folder must be `<name>.<World>` with a non-empty name and world, and the
  world must be an installed island class. Avoid dots in mission names: the engine allows them, but CE #257
  reports that dotted mod-mission folders break the SP menu [V]
  ([#257](https://github.com/ofpisnotdead-com/CWR-CE/issues/257)).

### 2.8 User and profile folders [V]

Codename `CWR`, config `ColdWarAssault`, product folder `Cold War Assault` (`apps/cwr/GameBase/GameBase.cpp#L154-L156`).
Resolution code: `GamePaths.cpp#L68-L121`, `PlatformPaths_win.cpp#L30-L49` and `PlatformPaths_posix.cpp#L81-L119`.
The profile directory is `UserDir/Users/<name>/` (`ProfileManager.cpp#L23-L26`, `#L93-L96`).

| Item | Windows | Linux | macOS (CE builds only) |
|---|---|---|---|
| UserDir (profiles, cfg) | `%APPDATA%\CWR\` | `$XDG_CONFIG_HOME/CWR/` (default `~/.config/CWR/`) | `~/Library/Application Support/CWR/` |
| Profile | `UserDir\Users\<name>\UserInfo.cfg` | same | same |
| UserContentDir | `Documents\Cold War Assault\` (CSIDL_PERSONAL, so it follows OneDrive redirection) | `$XDG_DATA_HOME/Cold War Assault/` (default `~/.local/share/…`) | `~/Documents/Cold War Assault/` |
| Editor missions | `<Content>\missions\` (lowercase) | same | same |
| MP editor missions / Mods / Workshop | `<Content>\MPMissions\`, `\Mods\`, `\Workshop\` | same | same |
| Logs / crashes | `<Content>\logs\`, `\crashes\` (`GameBase.cpp#L159-L190`) | same | same |
| Cache / Temp | `%LOCALAPPDATA%\CWR\` / `%TEMP%\cwr\` | `~/.cache/CWR/` / `/tmp/cwr/` | `~/Library/Caches/CWR/` / `/tmp/cwr/` |
| `--oldpaths` | Everything under the game folder; editor missions go to `<game>\Users\<name>\missions\` | same | same |

Legacy 1.99 uses the classic in-game-folder layout (`<game>\Users\<name>\missions\`, `<game>\Missions\`,
`<game>\MPMissions\`). That is **[I]**: it comes from `--oldpaths`, which is documented as emulating it, not
from a test of the 1.99 executable.

---

## 3. Community status (CWR-CE) [V]

| Item | Status |
|---|---|
| Upstream CWR | "locked repository: pull requests are not accepted"; community work goes to CWR-CE (`BohemiaInteractive/CWR@ffc61838b7:README.md#L86-L92`, `CONTRIBUTING.md`) |
| [#35](https://github.com/ofpisnotdead-com/CWR-CE/issues/35) "Add command-line args for direct mission editor launch" | **Open** (opened 2026-06-27, 2 comments). It asks for `-profile`, `-mission`, `-island` and `-editor`. One reply suggests `--test-mission`; org member her001 says a positional mission file goes straight into a mission and editor opening is not possible (§2.4 B). No linked pull request. |
| [#166](https://github.com/ofpisnotdead-com/CWR-CE/issues/166) "Working with the Mission Editor and more" | Open. After using Preview, save and load don't work, AutoSave is broken, and launch options are undocumented. A CE contributor (FreezerOFP) replies: "feel free to explore `--help` … Docs will improve once things stabilize". |
| [#231](https://github.com/ofpisnotdead-com/CWR-CE/pull/231) "Fix profile and save paths" | Merged 2026-08-16 (port from the 3.05 release branch). |
| [#185](https://github.com/ofpisnotdead-com/CWR-CE/issues/185) | Open: `mission.sqm` without Intro/Outro classes fails in the editor. |
| CE code delta for preview-relevant files | None (see §1). CE has 124 `.test.sqf` integration tests against 115 in CWR [V]. |
| Repo activity | Last push 2026-09-21; 76 stars; 117 open issues and PRs (GitHub API, 2026-09-26) [V]. |

**Conclusion:** nobody has implemented or claimed preview-specific or editor-launch flags. A small, well-tested
pull request answering #35 would probably be welcome **[I]**.

---

## 4. Options evaluated

| # | Option | Engine change | UX (clicks after pressing Preview) | Works on | Effort | Verdict |
|---|---|---|---|---|---|---|
| 1 | Export to the user missions folder and launch the game; the user opens Editor, Load, Preview | None | ~5–7 | Remastered, CE, **legacy 1.99** | S | **Fallback** |
| 2 | `--test-mission <staged>` (plus optional `--harness 0`) | None | **0** | Remastered or CE full client (shipping binary still to be verified) | S–M | **Primary (P1)** |
| 3 | Contribute `--preview-mission` / `--edit-mission` to CWR-CE | Small pull request (~150–300 LoC plus tests) **[I]** | 0, with a briefing option and no abort on script errors | CE builds, and later official builds only if BI adopts them [U] | M | **P3** |
| 4 | Live link over the harness (stop, teleport, console, screenshots; later hot restart) | None for basics; a pull request for in-process restart | n/a | Same as 2 | M | **P2** |
| 5 | MP preview: local `PoseidonServer --private` plus client(s) with `--connect` | None | ~1–2 (slot pick) or 0 with `--mp-assign` | Needs a `PoseidonServer` binary (CE builds ship one; Steam [U]) | M–L | **P4** |

### 4.1 Option 1: zero-change export and launch

- Write `<Content>/missions/<name>.<World>/` (Remastered/CE) or `<game>/Users/<profile>/missions/…` (legacy).
  Then spawn the executable with `--name <profile> --no-splash` (Remastered) or `-nosplash -name=<profile>`
  (legacy, syntax **[U]**). Show a toast: "Open Editor → select island → Load → *name* → Preview".
- Pros: works everywhere, including 1.99, and needs no knowledge of hidden flags.
- Cons: clicks, and the user can end up with two diverging copies of the mission. Mitigate by making our project
  folder the single source of truth, overwriting the export on each Preview, and warning if the exported copy's
  timestamp is newer than our last write (the user saved from inside the game).

### 4.2 Option 2: `--test-mission` (recommended for P1)

Recommended invocation, with cwd set to the `Remastered/` folder or `-C <data dir>`:

```text
PoseidonGame --test-mission "<stage>/<name>.<World>" --window --no-splash --no-strict
             [--width 1600 --height 900] [--name "<profile>"] [--mod "<a;b>"] [--lang English]
             [--harness 0] [--log-format jsonl --log-file "<stage>/preview.log"]
```

- **Stage first.** Serialize the editor's in-memory model (unsaved edits included) to
  `<our temp>/preview/<session-id>/<name>.<World>/` and copy the mission's companion files. The engine then
  stages its own copy (§2.4 A). Pass an **absolute** path; the engine absolutizes before `-C`
  (`AppConfig.cpp#L806-L808`).
- **Result mapping:**

  | Exit code | Meaning |
  |---|---|
  | 0 | Mission ended or the user quit |
  | 2 | Script error; parse the log for `Script error at` |
  | 3 | `--strict` abort on any ERROR log (`GameApplication.cpp#L921-L930`) |
  | 44 | Bad path |
  | 1 | Boot failure, **only with `--check`**; without it a failed boot leaves the game running (§2.4 A.6) |
  | other | Crash; point the user to `<Content>/crashes` |

  Code 2 is also used for CLI exceptions and for `--dev` in release builds (`AppConfig.cpp#L287-L292`,
  `#L985-L987`), so read the log to tell them apart.
- **Staged-copy tricks, with no engine change [I]:**
  - *Preview from camera position:* set the player unit's `position[]` in the staged `mission.sqm`.
  - *Preview Intro / OutroWin / OutroLoose* [V static; runtime untested] (corrected 2026-09-27 from doc 32 §4.3):
    stage the section through `StartAutoTest`'s intro fallback, not through `class Mission`. With a `Mission`
    section that has no groups, `StartAutoTest` initialises `class Intro` in intro mode and opens `DisplayIntro`
    (`DisplayUIMenus.cpp#L2020-L2034`, `#L2057-L2060`, `#L1225-L1230`).
    - *Intro:* stage it as-is, next to a group-less `Mission`.
    - *OutroWin / OutroLoose:* copy the outro into the staged `class Intro` and remove `initintro.sqs` from the
      stage, because real outros never run it [I]. The stock editor's Preview does run it for outros
      (`UIMapExtDisplay.cpp#L566-L611`), so doc 32's lint warns when an outro depends on that file.
    - Empty the staged `OutroLoose` unless the Intro-then-outro chain is being previewed: when the staged Intro
      ends, the menu re-parses the group-less `Mission` and plays `OutroLoose` (`OptionsUIApp.cpp#L850-L875`).
    - `StartAutoTest` clears all campaign variables first (`DisplayUIMenus.cpp#L2039`;
      `engine/Poseidon/AI/AICenter.hpp#L555`), so a campaign-state variant previews only if the staged
      `initintro.sqs` sets those variables itself.
    - *Superseded:* the earlier recipe "copy that section's content into the staged `class Mission`". That path
      runs in arcade mode, where a section without a player unit either fails the single-player consistency check
      (doc 04 §3.9) or ends at once as "killed" (`engine/Poseidon/World/WorldImpl.cpp#L543-L551`), and radio and
      effect lifetimes differ [I]. Doc 32 §7 (phase 0) lists this refinement as a design-gap entry for
      `docs/design-gap-requests/`.
  - *Preview at time/weather X:* edit `class Intel` in the stage.
- **Validation action ("Check mission loads"):** `--check --test-mission <stage> --nosound [--render dummy]`
  should exit 0 after logging `AUTO-TEST SUCCESS`. Whether the dummy renderer can load a mission is **[I]**,
  not verified. This is the natural "tool" for the AI agent's verify loop.
- **Caveats:**
  - `AutoTest` aborts the preview on script errors. That is useful for authors, but surprising in a mission that
    tolerates errors. It also applies to errors in text sent over the harness (debug console, watches), see §4.4.
  - There is no briefing.
  - `tri*` commands are registered.
  - Never pass `--no-menu-scene`.
  - The engine's staging means edits to scripts during the session are not seen. Use the positional-plus-
    `--autotest` variant (§2.4 C) to run in place when "edit a script and re-exec it" is wanted. That variant
    also sets `AutoTest`, so it aborts on script errors just the same.

### 4.3 Option 3: upstream `--preview-mission` / `--edit-mission` patch to CWR-CE (exact hook points)

All paths are in CE@b67bf3bd62; line numbers match CWR@ffc61838b7 except where noted.

1. **`engine/Poseidon/Foundation/Platform/AppConfig.{hpp,cpp}`:** next to `--test-mission` (`AppConfig.cpp#L668-L670`),
   add:
   - `--preview-mission <path>`
   - `--preview-briefing` (show the briefing first, like Shift+Preview)
   - `--preview-on-end quit|menu` (default `quit`)
   - `--edit-mission <path>` (answers #35)

   Absolutize the paths before `-C`, as at `#L806-L808`. Add getters beside `GetTestMissionPath`
   (`AppConfig.hpp#L236-L239`).
2. **`apps/cwr/Game/GameApplication.cpp` `StartGameMode` (`#L1697-L1735`):** resolve with
   `MissionPathLoader::Loader::ResolveMissionFile` and set `LoadFile`. Run in place: do not call
   `StageTestMissionForGame` and do not set `AutoTest`. Set a new global or config flag `PreviewMission`.
3. **`engine/Poseidon/World/WorldImpl.cpp` `World::StartIntro` (`#L2235-L2256`):** extend the `.sqm` branch to
   `if (AutoTest) StartAutoTest(); else if (PreviewMission) StartPreviewMission(); else OpenEditor();`.
   `--edit-mission` reuses the existing `OpenEditor()` path; investigate why #35 reports it as not working.
4. **`engine/Poseidon/UI/DisplayUIMenus.cpp`:** add `StartPreviewMission()` modelled on `StartAutoTest()`
   (`#L2012-L2066`). Optionally create `DisplayGetReady` when the briefing is requested and
   `GetBriefingFile()` is non-empty (mirror `UIMapExtDisplay.cpp#L585-L593`; CE offset about −77 lines). In
   `DisplayMission::OnSimulate` (`#L966-L1007`) and `DisplayMain::OnChildDestroyed` `IDD_MISSION`
   (`engine/Poseidon/UI/OptionsUIApp.cpp#L944-L969`), treat `PreviewMission && on-end==quit` like `AutoTest`
   for **exit flow only**, not the script-error abort in `ExpressExt.cpp#L150-L165`.
5. **Optional harness command `preview_restart{path}`,** registered in `CreateGameHarness`
   (`GameApplication.cpp#L556-L594`). It would close the `DisplayMission` stack on the main thread and re-run
   `StartPreviewMission()`, giving hot restart without a process boot. Unwinding the display stack safely is the
   risky part **[I]**. `CanRemount()` shows the engine already reasons about "safe from menu only" states
   (`#L1743-L1751`).
6. **Tests:** a Catch2 CLI-parse test next to `tests/unit/apps/Server/test_simulate.cpp`, plus a Trident
   mission test. Trident sidecar TOML accepts `extra_args`; see `integration.rs#L11-L17`.

The pull request would be GPL code in CE's repository. Our editor only *invokes* the flag, so our own licence is
unaffected **[I]**.

### 4.4 Option 4: live link and IPC

| Feature | Mechanism today | Status |
|---|---|---|
| Know when the mission is running or has ended | `display` event (46 = mission, 49 = pause), process exit code, stdout `jsonl` logs | [V] building blocks |
| Stop preview | `{"cmd":"exit"}`, then kill after a timeout (Trident's `kill_after_failure` pattern, `instance.rs#L253-L274`) | [V] |
| Teleport to editor cursor / "play from here" mid-session | `exec` `player setPos [x, y, 0]` | [V] SQF used in engine tests |
| Debug console panel (watch expressions, run SQF) | `eval` / `exec` | [V] mechanism; **under `--test-mission` any runtime error in console or watch text aborts the game (exit code 2)**, see the caveat below |
| Screenshot for thumbnails or AI visual checks | `screenshot{path}` | [V] |
| Live tweaks (time, weather, spawn) | `exec` `skipTime`, `setOvercast`, `createUnit`, … These are ephemeral: warn that they are not saved to `mission.sqm`. | [I] |
| Hot reload of `mission.sqm` | Not possible in-process today. Relaunch instead (boot cost unmeasured), or the Option 3 `preview_restart`. | [V] absent |
| Script hot edit | Re-`exec` a script file edited in place; needs the in-place launch variant because `--test-mission` stages a copy | [I] |

**AutoTest caveat for everything sent over `eval`/`exec` [V static] (added 2026-09-27, from doc 31 §7.4).**
`--test-mission` sets `AutoTest = true` (`BohemiaInteractive/CWR@ffc61838b7:apps/cwr/Game/GameApplication.cpp#L1703-L1718`,
same in CE). Harness `eval` runs `EvaluateMultiple`, whose `ShowError` calls `DisplayErrorMessage`, which requests close
with exit code 2 under `AutoTest` (`engine/Evaluator/express.cpp#L2768`, `#L2988-L3011`;
`engine/Poseidon/Game/Scripting/ExpressExt.cpp#L146-L165`). So in the P1 launch one runtime error in a console line, a
watch expression, a teleport or live-tweak snippet, or an agent `eval` ends the whole preview; the positional-plus-
`--autotest` variant (§2.4 C) behaves the same. `--no-strict` alone does not help, because `--test-mission` itself sets
`AutoTest`, and `--strict` makes any script error fatal on its own. A tolerant debug session therefore needs a launch
that is **both** non-`AutoTest` and `--no-strict`: the P3 `--preview-mission` flag (§4.3), or a harness launch without
`--test-mission`, such as the positional path of §2.4 B plus `--harness 0 --no-strict`, whose playability is **[U]**
(open questions 2 and 10). Until one exists, the interim is the one doc 32 §4.2 already uses: pre-check generated
snippets before sending them, and present the session as a "strict preview" (§7). Recorded as a design gap in
[`docs/design-gap-requests/DG-preview-non-aborting-launch.md`](../design-gap-requests/DG-preview-non-aborting-launch.md);
doc 31 §5.4 ("Try it", "why didn't this fire?") and §7.4 (console, watches) and doc 32 §4.2 (live shot preview) depend on it.

**Security:** the harness has no authentication, so any local process could send SQF while a preview runs
[V]. Keep it opt-in, use port 0, and connect immediately, since the backlog is 1 (whether a second client is
refused is **[U]**). Never expose it beyond loopback; the engine already enforces that [V].

### 4.5 Option 5: MP preview

- **Hosted, zero automation:** export to `<Content>/MPMissions/` and launch the client with `--host`. The user
  picks the mission and slot in the server UI (the flag exists [V]; the exact UI flow was not traced [U]).
- **Dedicated and local (preferred):**

  ```text
  PoseidonServer --config <stage>/server.cfg --port <free> --private --nosound [--no-strict]
    # server.cfg:  class Missions { class Preview { template = "<name>.<World>"; cadetMode = 0; }; };
  PoseidonGame --connect 127.0.0.1 --port <same> --name "<profile>" --window --no-splash [--mp-assign WEST:1]
  ```

  Put the mission in the server's MPMissions. Most robust: sandbox the server with
  `POSEIDON_USER_DIR=<stage>/server` and copy it to `content/MPMissions/`, as Trident does (§2.6). Add extra
  clients (`--name P2 --mp-assign EAST:1`) to preview PvP or JIP (`--force-jip` on the server).
- **Headless MP validation:** `PoseidonServer --simulate <stage> --check`, or `--duration N --stats 10` for a
  soak run [V flags].
- **Blockers:** the Steam depot may not include `PoseidonServer` **[U]**. CE CI builds do [V]
  ([builds page](https://ofpisnotdead-com.github.io/CWR-CE-builds/)).

---

## 5. Locating installs and choosing the executable

### 5.1 Known identifiers [V]

| Product | ID | Install directory / executable | Source |
|---|---|---|---|
| Steam, CWA Remastered (includes legacy) | app **65790**, OS `windows,linux` | `installdir = "ARMA Cold War Assault"`. Launch configs: Windows `/Remastered/PoseidonGame.exe` (workingdir `/Remastered/`); Linux `Remastered/PoseidonGame` (workingdir `Remastered/`); legacy `ColdWarAssault.exe`; legacy prefs `ColdWarAssaultPreferences.exe` | [api.steamcmd.net/v1/info/65790](https://api.steamcmd.net/v1/info/65790) |
| Steam, Remastered Demo | app **4819000** | `installdir = "Arma Cold War Assault Demo"`, `PoseidonGameDemo(.exe)` at the top level (**no editor**) | [api.steamcmd.net/v1/info/4819000](https://api.steamcmd.net/v1/info/4819000) |
| GOG, "ARMA: Cold War Assault Remastered" | product **1207658661**, Windows only, installer 3.0.5 | CE docs say to use the game's `Remastered` folder | [api.gog.com/products/1207658661](https://api.gog.com/products/1207658661?expand=downloads); `CWR-CE@b67bf3bd62:docs/build/win.md` |
| CWR-CE builds | CI artifacts (rwdi): Windows x64, Linux x64/arm64, macOS x64/arm64 (Game, GameDemo, Server) | Copied by the user into `Remastered/` or the demo folder; CE binaries are "not drop-in compatible with original game folder" | [CE builds](https://ofpisnotdead-com.github.io/CWR-CE-builds/); CE `README.md` |

### 5.2 Discovery algorithm

1. **User-configured installs** always come first, stored in our settings as a list of `GameInstall` values
   with `kind`, `exe`, `data_dir` and `flavor`.
2. **Steam** (Windows, Linux):
   1. Find Steam roots: Windows registry `HKCU\Software\Valve\Steam\SteamPath` (or
      `HKLM\SOFTWARE\WOW6432Node\Valve\Steam\InstallPath`). On Linux try `~/.local/share/Steam`,
      `~/.steam/steam`, `~/.steam/root`, Flatpak `~/.var/app/com.valvesoftware.Steam/.local/share/Steam` and
      Snap `~/snap/steam/common/.local/share/Steam` **[I]**, a common convention.
   2. Parse `<root>/steamapps/libraryfolders.vdf`, which lists `path` and `apps{appid:size}` per library.
   3. For each library, read `steamapps/appmanifest_65790.acf` and its `installdir`.
   4. Candidates are then `…/steamapps/common/<installdir>/Remastered/PoseidonGame(.exe)` and the legacy
      `ColdWarAssault.exe`. The same applies to app 4819000 (demo; data only, not an editor-capable exe).
   5. Both files use the undocumented Valve KeyValues ("VDF") format **[I]**. The crates `steamlocate` 2.1.1
      (MIT) and `keyvalues-parser` 0.2.4 (MIT/Apache-2.0) implement it (crates.io, 2026-09-26) [V]. Per our
      AGENTS.md rules, a pure `&[u8]` parser with synthetic fixtures may be preferable to a dependency.
3. **GOG** (Windows): `HKLM\SOFTWARE\WOW6432Node\GOG.com\Games\1207658661`, value `PATH` (value names are
   case-insensitive). GameFinder advises opening `HKLM\Software\GOG.com\Games` through the 32-bit registry view
   rather than hard-coding `WOW6432Node`. This registry
   convention is documented by third-party game-finder libraries, not by GOG
   ([GameFinder wiki](https://github.com/erri120/GameFinder/wiki/GOG-Galaxy),
   [Vortex wiki](https://github.com/Nexus-Mods/Vortex/wiki/LEGACY-Tutorial-Game-detection)) **[I]**. Then use
   `<path>\Remastered\PoseidonGame.exe`. Verify the layout on a real install **[U]**.
4. **CE builds / macOS:** manual selection. Validate that `PoseidonGame[.exe]` exists and that the data
   directory contains `DTA/` and `Worlds/`, the directories the `-C` help names [V]
   (`AppConfig.cpp#L505-L508`).
5. **Capability probe** per executable, cached by path, size and mtime:
   - `--version` prints `Arma: Cold War Assault - Remastered v…` (`AppConfig.cpp#L941-L952`).
   - `--mp-version` prints the MP tuple.
   - A synthetic `--check --test-mission` run should end with exit 0 and the log line `AUTO-TEST SUCCESS`.
   - Help output cannot be used: Dev options are hidden in release help, and `--help --dev` is rejected there.

### 5.3 Which executable to run

| Situation | Executable | Preview mode |
|---|---|---|
| Steam or GOG owner (default) | `Remastered/PoseidonGame` | Option 2 (plus 4) |
| Enthusiast with a CE build (needed for P3 flags and macOS) | CE `PoseidonGame` in the `Remastered/` folder or the demo folder | Options 2, 3, 4 |
| Demo-only user | CE full `PoseidonGame` on demo data (per CE docs); never `PoseidonGameDemo` | Option 2; missions are limited to demo assets |
| Legacy 1.99 target (a mission meant for classic servers) | `ColdWarAssault.exe` | Option 1 only (positional-arg behaviour on 1.99 is **[U]**) |

Launching directly is better than going through Steam. The source contains no Steamworks or `SteamAPI_*`
calls [V], and CE docs say binaries "may be run directly, or you may press play in Steam/GOG Galaxy". Whether
the *official* Linux binary runs outside the Steam Runtime container is **[U]**; CE PRs #21 ("CI - steamrt4")
and #37 ("3.01: SteamRT4 targets + release debug symbols") mention SteamRT4 in their titles. Fallback:
`steam -applaunch 65790 <args>` ([ArchWiki: Steam](https://wiki.archlinux.org/title/Steam)) (unverified: the
page returned access-denied during the fact-check). How that interacts with the app's four launch
configs (a possible picker prompt) is **[U]**.

---

## 6. Recommendation and phased plan

**P0: spike on real installs (1–2 days).** Answer the **[U]** items with a throwaway script:

- Do the Steam 3.0x Windows and Linux binaries honour `--test-mission`, `--harness 0`, `--check` and
  `--render dummy`?
- Does a positional `…/name.Island/mission.sqm` open the in-game editor (static reading) or play the mission
  (CE #35 member)? If it plays without `AutoTest`, prefer it to `--test-mission` for P1. With `--harness 0
  --no-strict`, does it survive an `eval` error (the non-aborting console of §4.4, open question 10)?
- Boot-to-mission time on typical hardware.
- Does `PoseidonGame` start without Steam running?
- Does the Linux build run outside the Steam runtime?
- Does 1.99 accept a positional `mission.sqm`?
- Is `PoseidonServer` present in the Steam depot?

**P1: "Preview (SP)" MVP.**

- Crates, following our AGENTS.md rules (one `Error` enum per crate, no `unwrap`, pure parsers, newtypes such as
  `SteamAppId(u32)` and `HarnessPort(u16)`):
  - `ofpe-install`: discovery (§5.2), with pure VDF/ACF parsers and synthetic fixtures.
  - `ofpe-preview`: staging, a `LaunchSpec` builder that returns `Vec<OsString>`, and a process supervisor built
    on `tokio::process` with `kill_on_drop` (tokio 1.53.1, MIT).
- Behaviour:
  - Pre-flight validation that mirrors `IsConsistent`: a player exists, the island is installed, all three
    Intro/Outro sections are written, and `addOns[]` lists every addon used (the game does not re-scan).
  - Stage the mission, then launch with `--test-mission <stage folder>` (no trailing separator).
  - Stream `--log-format jsonl` stdout into a **Preview log** panel and map exit codes to messages.
  - Provide a "Validate" button (`--check`).
  - Preview-from-camera and Intro/Outro previews via stage edits (§4.2; Intro/Outro go through the intro
    fallback, not `class Mission`).
- Zero-change fallback: Option 1, including a legacy 1.99 profile.

**P2: live link.**

- `ofpe-harness-client`: a clean-room JSON-lines client for protocol v1 with typed commands and events, tested
  against a fake TCP server.
- UI: a Stop button, a "teleport player to cursor" command, an SQF console, and screenshot capture for
  thumbnails and for the AI agent's visual verification tool.
- The agent's tools (see reports on the harness agent) would get `validate_mission`, `preview_screenshot` and
  `eval_sqf_in_preview`, each gated by user approval.
- Under the P1 `--test-mission` launch, a runtime error in console, watch or agent `eval` text ends the preview
  (§4.4). A tolerant console, and features built on it, wait on a non-aborting launch (P3, or the [U] positional
  harness launch); see the design gap linked from §4.4.

**P3: upstream pull request to CWR-CE.**

- Scope: `--preview-mission`, `--preview-briefing`, `--preview-on-end` and `--edit-mission`, plus docs and
  tests (§4.3). Reference issue #35 and first discuss the design in the issue.
- After merge, capability-probe for the flags and prefer them over `--test-mission`. Later add
  `preview_restart` for hot restart.
- `--preview-mission` without `AutoTest`, launched with `--no-strict`, is also the fix for the debug-console abort
  (§4.4 caveat and its design gap).

**P4: MP preview.** Local dedicated server plus N clients (§4.5), with slot presets per side and a PvP/JIP
toggle. Use `--private` always and a sandboxed server `POSEIDON_USER_DIR`.

**Non-goals:** embedding the game's window inside our editor, and in-process hot reload of `mission.sqm`
before P3.

## 7. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| The official build strips or changes hidden dev flags in a future update | Medium [I] | Capability probe; Option 1 fallback; upstream the documented flags (P3) |
| AutoTest's abort on script errors frustrates users | Medium | Present it as "strict preview", show the error with its location, and add the tolerant mode after P3. The abort also hits debug-console, watch and agent `eval` text (§4.4 caveat; design gap filed) |
| Staging hides live script edits | Low | In-place variant (§2.4 C) behind a setting |
| The local harness can be abused by other local processes | Low | Opt-in, loopback only (already enforced), short-lived sessions |
| GPL contamination by copying Trident or engine code | Medium if careless | Clean-room protocol client, no copied fixtures, licence note in CODE-INDEX.md |
| Trademark: using "Arma" or "Operation Flashpoint" as our product name | High if careless | Descriptive nominative use only ("launches Arma: Cold War Assault"); CWR §7 terms forbid distributing modifications under BI marks (`LICENSE#L682-L692`) |

## Open questions

1. Does the **shipping Steam 3.0x** `PoseidonGame` (Windows and Linux) accept `--test-mission`, `--harness`,
   `--check` and `--render dummy` exactly as in CWR@ffc61838b7?
2. Why does a CE #35 comment report that a positional mission file plays the mission and does not open the
   editor, when the source says it opens the editor? Is it a path-shape issue, a timing issue (Options display),
   or a build difference?
3. How long is boot-to-mission for `--test-mission` (cold and warm cache)? This decides whether in-process
   restart (P3 `preview_restart`) is worth it.
4. Does the official Linux binary run outside Steam's runtime? Does `PoseidonGame` need the Steam client
   running at all?
5. Is `PoseidonServer` shipped on Steam or GOG? Which MPMissions roots does `ResolveMPMissionTemplateBase`
   search (game dir, user content, mods)?
6. Does legacy 1.99 accept a positional `mission.sqm`, and what is its exact `-name=`/profile syntax? The BI
   wiki returned 403 here.
7. What is the GOG install layout (`Remastered/` subfolder?) and registry `path` on a real install?
8. Does the harness refuse a second concurrent client (backlog 1), and can the `log` event in the schema be
   enabled?
9. Will CE maintainers accept preview flags, or prefer generalizing `--test-mission` (for example
   `--test-mission-mode play`)?
10. **Non-aborting debug launch (added 2026-09-27).** Does a harness launch without `--test-mission` (the positional
    `…/name.Island/mission.sqm` of §2.4 B plus `--harness 0 --no-strict`) play the mission and keep running after an
    `eval` error? If yes, it gives a tolerant debug console before P3; if not, the console waits for P3 (§4.4 caveat).
    The shipping default of `--strict` is also unconfirmed: the member default is `false`, but the flag help says it
    is on in Debug/RelWithDebInfo builds (doc 31 §7.4), so every launch passes `--strict` or `--no-strict` explicitly.

## Sources

**Code (pinned):**

- CLI parsing, legacy aliases, visibility, the `LoadFile` bridge:
  `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Foundation/Platform/AppConfig.cpp#L86-L106`, `#L273-L765`,
  `#L806-L808`, `#L985-L987`, `#L1027-L1137`
- Config getters and defaults: `…/AppConfig.hpp#L236-L242`, `#L419`, `#L445`
- Staging, harness setup, game-mode start, module registration:
  `BohemiaInteractive/CWR@ffc61838b7:apps/cwr/Game/GameApplication.cpp#L142-L187`, `#L552-L594`, `#L956-L985`,
  `#L1020-L1025`, `#L1664-L1736`, `#L1743-L1751`, `#L1891-L1898`
- Demo module registration: `…/apps/cwr/GameDemo/GameDemoApplication.cpp#L5-L13`
- Server stages: `…/apps/cwr/Server/ServerApplication.cpp#L143-L208`
- Game paths codename: `…/apps/cwr/GameBase/GameBase.cpp#L154-L190`
- `StartIntro` and the positional mission: `…/engine/Poseidon/World/WorldImpl.cpp#L2217-L2273`
- Mission flow, `OpenEditor`, `StartAutoTest`: `…/engine/Poseidon/UI/DisplayUIMenus.cpp#L911-L1012`,
  `#L1979-L2066`
- Main-menu mission flow and editor launch: `…/engine/Poseidon/UI/OptionsUIApp.cpp#L800-L827`, `#L944-L969`
- Intro/Outro staging (§4.2; cited from doc 32 §4.3, not re-read in this pass): `…/engine/Poseidon/UI/DisplayUIMenus.cpp#L1225-L1230`,
  `#L2020-L2034`, `#L2039`, `#L2057-L2060`; `…/engine/Poseidon/UI/OptionsUIApp.cpp#L850-L875`;
  `…/engine/Poseidon/AI/AICenter.hpp#L555`; `…/engine/Poseidon/World/WorldImpl.cpp#L543-L551`;
  `…/engine/Poseidon/UI/Map/UIMapExtDisplay.cpp#L566-L611`
- In-game editor Preview and save/export: `…/engine/Poseidon/UI/Map/UIMapExtDisplay.cpp#L410-L427`,
  `#L529-L614`, `#L2190-L2264` (CE Preview case at `ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/UI/Map/UIMapExtDisplay.cpp#L452`)
- Editor display constructor: `…/engine/Poseidon/UI/Map/UIMapExt.cpp#L2883-L2925`
- `ProcessFullName`: `…/engine/Poseidon/UI/Map/UIArcadeWaypoint.cpp#L904-L918`
- Mission path resolution: `…/engine/Poseidon/Game/Mission/MissionPathLoader.hpp#L28-L88`
- Directory and mission helpers: `…/engine/Poseidon/UI/OptionsUI.cpp#L121-L141`, `#L191-L205`, `#L826-L919`
- Init scripts: `…/engine/Poseidon/UI/DisplayUI.cpp#L121-L144`
- Script-error handling under AutoTest: `…/engine/Poseidon/Game/Scripting/ExpressExt.cpp#L146-L175`; harness `eval`
  error path (`EvaluateMultiple` → `ShowError` → `DisplayErrorMessage`): `…/engine/Evaluator/express.cpp#L2768`,
  `#L2988-L3011` (cited from doc 31 §7.4, not re-read in this pass)
- Unfocused rendering: `…/engine/Poseidon/Core/Game/GameLoop.cpp#L194-L196`
- Path resolution: `…/engine/Poseidon/Foundation/Common/GamePaths.cpp#L18-L153`,
  `PlatformPaths_win.cpp#L30-L49`, `PlatformPaths_posix.cpp#L81-L119`
- Profiles: `…/engine/Poseidon/Core/Profile/ProfileManager.cpp#L23-L96`
- Harness: `…/engine/Poseidon/Dev/Harness/HarnessServer.cpp#L60-L62`, `#L73-L155`, `HarnessBuiltins.cpp#L56-L112`,
  `#L183-L202`, `#L836-L963`
- Addon list on load: `…/engine/Poseidon/AI/ArcadeTemplate.cpp#L1910-L1955`; version: `…/engine/Poseidon/Foundation/Platform/VersionNo.h`;
  Trident licence metadata: `…/engine/Trident/Cargo.toml#L6`
- Test-only SQF commands: `…/engine/Poseidon/Game/Commands/GameStateExtTestAudio.cpp#L947-L975`, `#L2960-L2964`
- MP server mission flow: `…/engine/Poseidon/Network/NetworkServerSimulate.cpp#L413-L461`, `#L502-L590`,
  `#L636-L657`, `#L792-L812`
- Engine source glob: `…/engine/Poseidon/CMakeLists.txt#L14-L37`
- Trident: `…/engine/Trident/protocol/harness.schema.json#L1-L141`,
  `…/engine/Trident/src/protocol/types.rs#L8-L112`, `…/engine/Trident/src/client/instance.rs#L52-L410`,
  `…/engine/Trident/src/scenarios/integration.rs#L1-L17`, `#L1097-L1210`, `#L1386-L1438`,
  `…/engine/Trident/src/scenarios/multi.rs#L2247-L2298`, `…/engine/Trident/src/main.rs#L37-L180`
- Test fixtures: `…/tests/README.md#L43-L64`,
  `…/tests/integration/ui/editor/editor_unit_and_preview.test.sqf`, `editor_preview_save_load.test.sqf`,
  `…/tests/integration/multiplayer/von_dedicated.test/{test.toml,server.cfg}`,
  `…/tests/unit/engine/Poseidon/Dev/Debug/test_dev_mode_gates.cpp#L43-L83`
- Repository policy and licence: `…/README.md#L1-L92`, `…/CONTRIBUTING.md`, `…/LICENSE#L682-L721`
- CE docs and README: `ofpisnotdead-com/CWR-CE@b67bf3bd62:README.md`, `docs/build/win.md`, `docs/build/linux.md`

**Web (accessed 2026-09-26):**

- CWR-CE issues and pull requests:
  - Launch-flag request: <https://github.com/ofpisnotdead-com/CWR-CE/issues/35>
  - Editor workflow problems: <https://github.com/ofpisnotdead-com/CWR-CE/issues/166>
  - Intro/Outro parsing: <https://github.com/ofpisnotdead-com/CWR-CE/issues/185>
  - Profile and save paths: <https://github.com/ofpisnotdead-com/CWR-CE/pull/231>
  - Dotted mission names: <https://github.com/ofpisnotdead-com/CWR-CE/issues/257>
  - Original-assets question: <https://github.com/ofpisnotdead-com/CWR-CE/issues/8>
  - #35 member comment: <https://github.com/ofpisnotdead-com/CWR-CE/issues/35#issuecomment-5081007160>
  - SteamRT4 PRs: <https://github.com/ofpisnotdead-com/CWR-CE/pull/21>, <https://github.com/ofpisnotdead-com/CWR-CE/pull/37>
  - Repository API: <https://api.github.com/repos/ofpisnotdead-com/CWR-CE>
- CWR-CE CI builds: <https://ofpisnotdead-com.github.io/CWR-CE-builds/>
- Steam app metadata: <https://api.steamcmd.net/v1/info/65790>, <https://api.steamcmd.net/v1/info/4819000>
- Steam store page: <https://store.steampowered.com/app/65790/>
- BI release blog: <https://www.bohemia.net/en/blog/Arma-Cold-War-Assault-Remastered-Out-Now>
- GOG catalog and product: <https://catalog.gog.com/v1/catalog?query=like:cold%20war%20assault>,
  <https://api.gog.com/products/1207658661?expand=downloads>
- GOG registry convention: <https://github.com/erri120/GameFinder/wiki/GOG-Galaxy>,
  <https://github.com/Nexus-Mods/Vortex/wiki/LEGACY-Tutorial-Game-detection>
- Steam `-applaunch`: <https://wiki.archlinux.org/title/Steam>
- crates.io metadata: <https://crates.io/crates/steamlocate>, <https://crates.io/crates/keyvalues-parser>,
  <https://crates.io/crates/tokio>
- Not retrievable this session (HTTP 403 or connection refused), not relied on:
  <https://community.bistudio.com/wiki/Operation_Flashpoint:_Startup_Parameters>,
  <https://community.bistudio.com/wiki/Arma:_Cold_War_Assault_Remastered>,
  <https://www.gnu.org/licenses/gpl-faq.html#MereAggregation>

## Verification notes

Adversarial fact-check, 2026-09-26. Static source reading only; nothing was executed against a game.

- **Re-read at the pinned commits and confirmed:** the `AppConfig.cpp` flag registrations and line numbers in
  §2.2; the release gate on `--dev` only (#L287-L292, #L606-L612); `StartGameMode` staging, exit 44 and
  `--no-menu-scene` (#L1697-L1735); `StartIntro` (.fps/.sqg/.sqm only, Editor-module gate); `StartAutoTest`;
  AutoTest exit paths in `DisplayUIMenus.cpp` and `OptionsUIApp.cpp`; the script-error abort (exit 2) in
  `ExpressExt.cpp`; the harness binding to `INADDR_LOOPBACK` with backlog 1 and no authentication; the Demo module
  list; the path resolution in `GamePaths.cpp` and `PlatformPaths_*.cpp`; the in-editor Preview code; the MP
  server template flow; the IDD values; the §7 trademark terms; the "locked repository" README text. Hash
  comparison shows that `GameApplication.cpp`, `WorldImpl.cpp`, `DisplayUIMenus.cpp`, `GamePaths.cpp`,
  `MissionPathLoader.hpp`, `HarnessServer.cpp` and `harness.schema.json` are identical in CE, and that
  `AppConfig.cpp` differs by one help string.
- **Live metadata confirmed:** Steam 65790 and 4819000 installdirs and launch configs (api.steamcmd.net), GOG
  1207658661 (Windows only, 3.0.5), CE builds page (Game, GameDemo and Server for all five targets), CE repo
  stats (76 stars, 117 open, pushed 2026-09-21), #35 open with 2 comments and no PR, #231 merged 2026-08-16,
  crate versions, and the BI blog's MP-incompatibility sentence.
- **Corrected:**
  - The harness command list: `click`, `wait_display` and `query=display` are not registered in `PoseidonGame`.
  - The #35 commenter: an org MEMBER, who also says a positional mission file *plays* the mission.
  - The #166 replier: a CONTRIBUTOR, not "the maintainer".
  - The SteamRT4 PR titles.
- **Added:**
  - `--test-mission` with the file form or a trailing separator breaks staging.
  - `LoadFile` is 256 bytes.
  - `addOns[]` is not re-scanned on load.
  - Without `--check`, a boot failure does not exit.
  - Exit code 3 comes from `--strict`.
  - Trident's MIT-vs-GPL licence ambiguity.
  - The pinned source reports version 3.05.
  - The GOG registry-view caveat.
- **Could not verify:** Steam `-applaunch` (ArchWiki returned access-denied); anything about shipping binaries,
  Steam depots, or runtime behaviour.

### Consolidation pass (2026-09-27)

- **Corrected (from doc 31 §7.4, open question 7 and its engine-review item 8):** §4.4 listed the debug console and
  watch (`eval` / `exec` [V]) without the caveat that under `--test-mission` (`AutoTest`) any runtime script error,
  including one in console or watch text, aborts the game with exit code 2 [V static: `GameApplication.cpp#L1703-L1718`;
  `express.cpp#L2768`, `#L2988-L3011`; `ExpressExt.cpp#L146-L165`]. Added the caveat to the §4.4 table and a paragraph
  under it, and matching notes in the TL;DR (AutoTest bullet), §4.2 caveats (including the §2.4 C variant), §6 P0,
  P2 and P3, §7 risks, open question 10 and Sources. The `express.cpp` lines are taken from doc 31 and were not
  re-read here.
- **Filed the design gap:** `docs/design-gap-requests/DG-preview-non-aborting-launch.md`. A non-aborting launch must
  be both non-`AutoTest` and `--no-strict`: the P3 `--preview-mission` flag, or a harness launch without
  `--test-mission` whose playability is [U]. Doc 32 §4.2 and doc 31 §5.4 ("Try it") and §7.4 (console) depend on it.
- **Renames checked:** this doc has no references to the concept manual or the live tutorials, so nothing to rename.
- **Corrected (C32-08, from doc 32 §4.3 and §7 phase 0):** the §4.2 Intro/Outro recipe, "copy that section's content
  into the staged `class Mission`", is superseded. It now stages an Intro as-is beside a group-less `Mission` (the
  `StartAutoTest` intro fallback). It stages an outro by copying it into `class Intro` and stripping `initintro.sqs`,
  empties `OutroLoose` unless the chain is being previewed, and notes that `StartAutoTest` clears campaign variables
  first. The old recipe stays in §4.2 as a marked superseded item with the reason: the `class Mission` path runs in
  arcade mode, where a player-less section fails the SP consistency check or ends at once as killed
  (`WorldImpl.cpp#L543-L551`). The TL;DR "Features that need no engine changes" bullet and the §6 P1 behaviour
  bullet were updated to match, and the citations were added to Sources. Evidence is doc 32 §4.3 [V] and its
  engine review note "Staging clears campaign vars and plays OutroLoose after the staged Intro". The line numbers
  are CWR's and come from doc 32; they were not re-read here, and nothing was run. The design gap is listed in
  doc 32 §7 phase 0. No design-gap file for this staging refinement exists yet under `docs/design-gap-requests/`,
  so none is linked; filing one is left to the design-gap step.
- **Renames re-checked (2026-09-27):** there are no links to `docs/research/33-field-manual-and-live-tutorials.md` or
  `skills/field-manual`, and no "Field Manual", "Boot camp", "Bootcamp" or "Academy" mentions, so no link or
  name needed changing.
