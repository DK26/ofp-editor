# Upstream Repositories: BohemiaInteractive/CWR vs ofpisnotdead-com/CWR-CE

Research note 01 for **ofp-editor**, a standalone Rust re-implementation of the in-game Mission Editor of
*Arma: Cold War Assault* (CWA, originally *Operation Flashpoint: Cold War Crisis*, 2001).
Research date: 2026-09-26. Pinned snapshots analysed (full git history fetched for both):

- `BohemiaInteractive/CWR@ffc61838b7` (official "3.05" source snapshot, committed 2026-08-18)
- `ofpisnotdead-com/CWR-CE@b67bf3bd62` (community `main`, last commit 2026-09-21)

Epistemic tags used below: **[V]** verified against the cited code or page; **[I]** inferred from
verified facts; **[U]** unknown / not verified (treat as a hypothesis). Numbers from the GitHub or Steam
APIs are snapshots taken on 2026-09-26 and will change.

## TL;DR

- **Both repos contain the same engine**. CE's history branches from BI's first commit, and BI's later
  releases are squashed snapshots of work done in CE first. The ~28k lines of mission-editor code and
  the config/`mission.sqm` parser have changed very little in either repo since release [V].
- **BohemiaInteractive/CWR is locked**. It accepts no PRs. Issues are only for bugs in official Steam
  builds. It gets one squashed commit per Steam patch (3.01, 3.03, 3.05) and has no tags, releases or
  CI. Its README, CONTRIBUTING, CREDITS and its maintainer all point people to CWR-CE [V].
- **CWR-CE is where development happens**:
  - 316 commits, 10 contributors, 216 PRs (151 merged) and CI on Windows, Linux x64/arm64 and macOS [V].
  - A `port` label marks candidates for the official Steam patches. For example, macOS support (CE
    PR #19, labelled `port`) was written in CE, and its source then appeared in the CWR 3.05 snapshot.
    Steam still ships only Windows and Linux builds [V].
  - Bus factor is 1: Josef Šimánek ("simi"/"retro") wrote 263 of the 316 commits. The 316 include the
    shared BI root commit, which he also authored. He also made the official releases and is listed
    as a developer on Steam [V].
- **Launching a mission from outside the game is already possible in the shipped code**:
  - The `PoseidonGame` binary accepts a positional path of the form `.../<name>.<island>/mission.sqm` [V].
  - Adding `--autotest` makes the game run nearly the same load and init steps as the editor's own
    Preview button. It is not identical: it re-reads the mission from disk, skips `ScanRequiredAddons`,
    and the mission does not return to an editor afterwards [V code].
  - `--test-mission` and `--check --test-mission` start a mission and exit (the second one is a load
    check) [V]. Pass the mission *folder*. Given a path to a `mission.sqm` file, the staging step
    copies only that file into `Missions/mission.sqm`, which loses the `<name>.<island>` folder the
    loader needs [I from code].
  - `--harness <port>` opens a localhost-only JSON-over-TCP control channel that can evaluate SQF [V].
  - None of these is gated to dev builds. In a release build they appear in no help output, because
    Dev-level options are listed only by `--help --dev` and release builds refuse `--dev`. None has
    been tested against the Steam binary [V code / U runtime].
- **The Demo executable cannot preview**. `PoseidonGameDemo` does not register the Editor module, so
  the `.sqm` launch path is skipped. Preview needs the full-game executable [V].
- **Recommendation**:
  - Port editor logic and formats from **CWR-CE `main` pinned to a SHA**, and cross-check against the
    **CWR release snapshots** for official behaviour.
  - For preview, launch the **user's installed official full game (≥ 3.05)** by default, and let the
    user point at a CE or self-built binary.
  - Send any upstream patches (for example `--editor` / `--preview` flags) **only to CWR-CE**, starting
    with issue #35.
- **Licensing caveat**: porting (translating) this GPL-3.0-or-later code with its Section 7 terms makes
  our code a derivative work [I]. The Rust crates in these repos declare `license = "MIT"` in their
  Cargo.toml files, while the repo LICENSE says GPL. That conflict is unresolved [V]. The licensing
  research doc will need to settle both points.
- **Visual layouts are not in either repo**. Dialogs such as `RscDisplayArcadeMap` are loaded from game
  data (under the APL-SA licence), not from GPL source [V]. See `05-visual-fidelity-and-ui-resources.md`.
- **Main risks**:
  - Most of the work depends on a single maintainer.
  - CE-only features could make missions that do not run on Steam builds.
  - The launch flags are undocumented test hooks and may change.
  - BI's squashed snapshots are hard to bisect.
  - The name "OFP" in our repo name and description may be a trademark problem.

## 1. Context and glossary

| Term | Meaning |
| --- | --- |
| **Poseidon** | Codename of the engine in both repos: the original OFP/CWA engine, modernised to C++20, CMake and Clang, with an OpenGL 3.3 renderer. |
| **CWR** | "Cold War Assault Remastered". Also the name of Bohemia Interactive's (BI) official source repo. |
| **CWR-CE / CE** | "Community Edition": `ofpisnotdead-com/CWR-CE`, the community continuation of that source. |
| **Arcade editor** | The in-game mission editor. Its code lives in `engine/Poseidon/UI/Map/UIArcade*.cpp`, `UIMap*.cpp` and `engine/Poseidon/AI/ArcadeTemplate*` (see `03-original-editor-code-map.md`). |
| **mission.sqm** | Mission file in "ParamFile" config syntax, either text or binarised. See `04-mission-data-model-and-formats.md`. |
| **PBO** | Archive format for packed missions and addons. |
| **SQF / SQS** | The engine's scripting languages. |
| **Trident (`tri`)** | Rust test orchestrator in `engine/Trident`. It drives game instances over the *harness* protocol. |
| **Harness** | A TCP control server built into the game, enabled with `--harness`. |
| **APL-SA** | Arma Public License Share Alike, the licence of the game data (models, textures, configs, missions). |
| **Section 7 terms** | Extra terms attached to the GPL under GPLv3 §7: no trademark rights, no misrepresentation, an indemnity clause, and a disclaimer. |

## 2. The source release

### 2.1 Timeline [V]

| Date (2026) | Event | Evidence |
| --- | --- | --- |
| 06-22 11:29Z | GitHub repo `ofpisnotdead-com/CWR-CE` created. This is about 1.5 h *before* BI's repo. | GitHub API `created_at` |
| 06-22 12:56Z | `BohemiaInteractive/CWR` created. First commit `ea77e57` "Public source code" by Josef Šimánek. | GitHub API; git history |
| 06-22 | Steam **demo** (app 4819000) released for Windows 64-bit and Linux 64-bit. | Steam appdetails |
| 06-23 | CWR "3.01" snapshot (64 files, +1661/−930). | `git show --stat fdc9596` |
| 07-15 22:26Z | CWR "3.03" snapshot `a15f184` (622 files, +27135/−2055). | git |
| 07-16 14:00Z | Steam news: "Arma: Cold War Assault Remastered Is Out Now!" (full game, app 65790). GamingOnLinux also gives 16 July 2026 as the release date. The bohemia.net blog copy of this post is dated 29/07/2026; the reason for the difference is unknown. | Steam news API (timestamp `1784210419`); GamingOnLinux; bohemia.net blog |
| 08-17 | Steam "Update 3.05" and a "SITREP" post by Josef Šimánek (retro). | Steam news API |
| 08-18 | CWR "3.05" snapshot `ffc6183` (567 files, +20885/−3039). This is the last push to CWR as of 09-26. | git; GitHub API `pushed_at` |
| 09-21 | Latest CE `main` commit `b67bf3b`. | git |

### 2.2 What was released, and what was not [V]

- **Included**:
  - The full engine and game source: `engine/Poseidon`, the GL33 and OpenAL backends and `PoseidonFormats`.
  - The apps: `PoseidonGame`, `PoseidonGameDemo`, `PoseidonServer`, `PoseidonTools`, `PoseidonEvaluator`
    (SQF), `PoseidonStudio` (an ImGui asset browser/previewer, not a mission editor) and a Blender P3D
    importer (`BohemiaInteractive/CWR@ffc61838b7:apps/README.md#L9-L36`).
  - Rust tooling: Trident, plus the "PAPA BEAR" master-server/workshop crates in `mserver/`. Among them
    is `papa-bear-archive`, described as "byte-compatible OFP/Poseidon pack & unpack" of PBOs.
  - Tests: Catch2 unit tests, Trident SQF-driven integration tests (including editor scenarios) and
    test fixtures (P3D, PAA, PBO, RTM, configs). `tests/README.md` does not say how the fixtures were
    made, so "synthetic" is unverified.
- **Excluded**:
  - Game data, which is licensed separately under APL-SA (`README.md#L14-L18`).
  - The trademarks "ARMA" and "OPERATION FLASHPOINT" (`README.md#L10-L12`).
  - The *original* 2001 source. The maintainer says releasing it "is not planned currently and it is not
    simply possible" (BI/CWR issue #17).
  - Changes from the community patch "2.03" (BI/CWR issue #5).
- **Licence**:
  - GPL-3.0-or-later with Section 7 additional terms (`BohemiaInteractive/CWR@ffc61838b7:LICENSE#L682-L721`).
  - The terms say: convey the notice and terms with every copy; no trademark rights; you may not
    "distribute any modification of this program using any Bohemia Interactive trademark or 'OPERATION
    FLASHPOINT' trademark"; you may not claim any affiliation or association with Bohemia Interactive;
    modified versions must be marked as modified; there is an indemnity clause if you assume
    contractual liability; plus an extra disclaimer.
  - The README says "OPERATION FLASHPOINT" is a registered trademark of **Electronic Arts Inc.**, while
    "ARMA" belongs to BI (`README.md#L62`).
  - `thirdparty/` is excluded from the GPL. The LICENSE files in the two repos are byte-identical.
- **Stated intent**:
  - BI says the code is released "to study it, build on it, fix it, and create from it" (`README.md#L4`).
  - Steam news calls it "a new way to study, preserve, experiment with, and better understand the technology".
  - The remaster was "developed in collaboration with members of our player community".

## 3. BohemiaInteractive/CWR: status [V]

- **Locked**:
  - "pull requests are not accepted here, and this repository will not be continuously updated"
    (`BohemiaInteractive/CWR@ffc61838b7:README.md#L86-L92`).
  - Issues are "only for bugs in official Bohemia Interactive builds distributed on Steam"
    (`CONTRIBUTING.md#L7-L17`).
  - Forks and ideas are directed to CWR-CE (`CONTRIBUTING.md#L34-L39`). CREDITS says: "The community
    release authors continue independently at <https://github.com/ofpisnotdead-com/CWR-CE>"
    (`CREDITS.md#L40-L41`).
  - The maintainer said in BI/CWR issue #5: "Development doesn't happen in here … Please join us at
    …/CWR-CE."
- **Not archived** (`archived: false`), so pushes still happen at Steam releases.
- **History**: 5 commits: the public release, issue templates, then 3.01, 3.03 and 3.05. There are no
  tags, releases, CI workflows (`.github/` holds only an issue template) or branches other than `main`.
- **Stats**: 1,197 stars, 173 forks, 14 open issues, 20 issues in total (0 PRs found by search). Topics
  so far are gameplay and rendering regressions, the Linux Steam launch (#11, 21 comments) and build help.
- **Meaning for us**: CWR is the best **"what official Steam builds contain"** baseline. Each commit
  corresponds to a Steam version. It is not a place to contribute to.

## 4. ofpisnotdead-com/CWR-CE: status [V]

- **Governance**:
  - Pull requests are welcome.
  - `main` is the primary development branch. Eight short-lived feature branches also exist (for
    example `sdl-ibus` and `issue-445-joystick`; branches API).
  - CONTRIBUTING describes an `official` branch as a "candidate base for a future official Bohemia
    Interactive Steam patch" that takes only bug/crash fixes and quality-of-life changes
    (`ofpisnotdead-com/CWR-CE@b67bf3bd62:CONTRIBUTING.md#L20-L32`). **As of 2026-09-26 no `official`
    branch exists** (branches API).
  - Instead, the maintainers apply the label `port` ("Candidate to port to 'official' version"). 96 PRs
    carry it.
- **People**:
  - 10 contributors: simi 263 commits, paavohuhtala 28, her001 9, Dahlgren 7, ayozetr 3, Psina909 2,
    and four others with 1 each.
  - "simi" is Josef Šimánek. BI's CREDITS thanks him for "development archaeology, codebase work, and
    preparation of this source release" (`BohemiaInteractive/CWR@ffc61838b7:CREDITS.md#L25`).
  - Steam lists the developers as "Bohemia Interactive, Josef Šimánek (retro)".
  - The only public org member is `her001`.
- **Activity**:
  - 316 commits on `main` by commit date: Jun 43, Jul 125, Aug 78, Sep 1–21 70.
  - 216 PRs (151 merged, 53 open); 93 issues (about 64 open).
  - Discussions are enabled, with categories Announcements, General, Ideas, papa-bear.cz, Polls and Q&A.
    Examples include "Roadmap / Vulkan Port" and "Difficulty selector".
  - There is no written roadmap beyond Steam SITREPs. The 3.05 SITREP says: "For the next patch, I
    plan to revisit multiplayer."
- **Builds**:
  - There are no GitHub releases.
  - CI publishes "Unofficial work-in-progress builds, straight from CI. No warranty" at
    <https://ofpisnotdead-com.github.io/CWR-CE-builds/>. Artifacts cover Game, GameDemo, Server,
    MasterService, Trident and Symbols for Windows x64, Linux x64/arm64 and macOS x64/arm64.
  - Artifacts are served through nightly.link and "expire and disappear automatically".
- **CI** (`.github/workflows/build.yml`): it builds and runs CTest on every platform, plus Linux
  sanitizer builds and a SteamRT4 build. It also runs **Trident integration tests (including the editor
  scenarios) under xvfb against Demo data in 4 shards** (`build.yml#L377-L396`). The Demo data comes
  from `files.ofpisnotdead.com/CWR-demo-assets-v2.zip` (`build.yml#L19`). Two editor scenarios
  (`editor_wizard_finish`, `mp_wizard_finish_demo`) are tagged `ci-host-blocked`, and CI skips that tag.
- **Compatibility warning**: CE binaries "are not drop-in compatible with original game folder", which
  means the classic, pre-remaster install. They need the Remastered config (CE README `#L69-L70`; CE
  issues #8 and #29). The maintainer's "use the Demo folder" advice in those comments dates from June,
  before the full game shipped. The CE README now says to copy the binaries into the Steam or GOG
  game's **Remastered** folder or the Steam demo folder (`#L65-L67`). A full-game exe run in the Demo
  folder unlocks the editor, but only with demo assets.
- **AI-contribution policy** (`CONTRIBUTING.md#L59-L72`). This affects any PR we send:
  - The human is the author.
  - Commits must have "no `Co-Authored-By` for a tool, no 'Generated with …' trailer, and no AI mention in
    the commit message".
  - Contributors must strip AI boilerplate and must not run AI review bots against the repo.
- **ofpisnotdead.com**:
  - A long-running OFP/CWA community hub: server list, master server, file hosting and the community
    Discord.
  - The `ofpisnotdead-com` GitHub org also hosts older community tools: PowerServer, OfpSpy,
    server-browser, a Rust `libofp` server-query prototype and an MIT `rust-pbo-wasm`.
  - The 3.05 SITREP names CWR-CE as the development venue and ofpisnotdead.com as the Discord entry
    point. It also mentions growing **Papa Bear** (papa-bear.cz, master server plus a mod catalogue) into
    a community portal.
- **Branding observation**: CE's binary still calls itself "Arma: Cold War Assault - Remastered CE"
  (`engine/Poseidon/Foundation/Platform/VersionNo.h#L9-L10`), even though the README says forks "must be
  renamed". BI appears to endorse CE [I], so this tells us nothing about what *we* may do with the marks.

## 5. How the two repos relate

```text
ea77e57 "Public source code" (2026-06-22)  <- shared root, the only common commit
   |\
   | \__ CWR-CE main: 316 commits (fixes, ports, CI, tests)  --(label "port")-->
   |                                                                          |
   \__ BI/CWR main: 3.01 -> 3.03 -> 3.05   <-- squashed snapshots of the ported work
                                   |
       CE "Bump to CWR 3.05" (93e7da0, 2026-08-19) re-syncs version numbers
```

- **[V]** The merge-base of CE `main` and CWR `main` is `ea77e57`. CWR 3.05 is *not* an ancestor of CE
  `main`: BI publishes squashed snapshots and never merges them back.
- **[V]** CE at `93e7da0` differs from CWR 3.05 in only 66 files (+2612/−367). Almost all of these are
  CE-only CI/docs, `mserver` workshop work, a JIP queue, crash-handler and stringtable tweaks. So nearly
  all CE work up to mid-August shipped in 3.05.
- **[V]** macOS support was added in CE commit `ea80764` (PR #19, labelled `port`; committed
  2026-07-25, authored 06-22, Björn Dahlgren). CWR's `cmake/presets/macos.json` first appears in the
  3.05 snapshot, although the CWR README still says "Windows x64 and Linux x64". This happened only in
  the source: the Steam full game lists Windows and Linux only, and the 3.05 SITREP points macOS users
  to the experimental CE CI build.

## 6. Divergence analysis (numbers from `git diff --shortstat`) [V]

| Scope | Public release → CWR 3.05 | Public release → CE HEAD | CWR 3.05 → CE HEAD |
| --- | --- | --- | --- |
| Whole tree | 992 files, +49040/−5351 | 1160 files, +60589/−7543 | 318 files, +11815/−2458 |
| Editor code (`UI/Map/*`, `AI/ArcadeTemplate*`, `IO/Serialization`; 27 files, ≈31.1k lines, of which `UI/Map` + `ArcadeTemplate*` ≈28.2k) | 10 files, +93/−40 | 11 files, +219/−174 | 7 files, +126/−134 |
| ParamFile parser (`IO/ParamFile*`, `IO/ParamFileExt*`) | 0 files | 3 files, +12/−4 | 3 files, +12/−4 |
| Launch path (AppConfig, GameApplication, WorldImpl, DisplayUIMenus, MissionPathLoader, GamePaths, Harness, Trident protocol) | — | — | 2 files, +11/−10 |
| Trident + mserver (Rust) | 28 files, +6704/−756 | 28 files, +7910/−889 | 13 files, +1194/−121 (mserver CLI/MasterService, Trident scenarios) |

### 6.1 What CE changed that matters to us

- **Editor and mission compatibility**. All of these are small:
  - Legacy-codepage (CP1252) island and world names are decoded in the editor and map (`80856fd`).
  - Mission descriptions and HTML entities are decoded to UTF-8 (`bc1952a`).
  - Mission names in legacy codepages are decoded (`f657230`).
  - A packed mission's own stringtable is read for its title (`e88327c`).
  - Missions whose island or addons are missing are refused, and the missing names are shown
    (`6c35ff7`, `0418966`). The latter factored `FindMissingAddons` / `MissingAddonMessage` out of
    `ArcadeTemplate.cpp`.
  - Terrain object IDs are preserved so that serialized mission objects cannot overwrite terrain entries
    (`03e57d5`, #157).
  - User mission saves are fixed (`8ed2d06`).
  - Map zoom and wheel bindings are rebindable, and the cursor scales on widescreen.
  - **No change to the `mission.sqm` / ParamArchive serialization format was found.**
  - **Lesson for our parsers**: mission and config text arrives both as legacy codepage and as UTF-8, so
    decoding must tolerate both (see doc 04).
- **CLI and launch**: none. The option set in `AppConfig.cpp` is identical apart from one changed help
  string (+1/−1).
- **Platforms**: CE adds Linux arm64 (`d7a8967`) and Linux sanitizer presets. macOS already reached CWR
  3.05.
- **Renderer**: large performance work (instanced terrain and water, GL33 state caching) that is only
  in CE after 3.05. It does not affect us, except that CE and Steam builds may render differently.
- **Rust**: Trident scenario changes, plus workshop publishing in the `papa` CLI and the MasterService
  (`mserver/CLI/src/main.rs` +483/−60).
- **Tests and CI**: 552 vs 524 integration test files. CI exists only in CE. Both repos already contain
  editor integration scenarios, for example `tests/integration/ui/editor/editor_unit_and_preview.test.sqf`,
  which places a unit, clicks Preview (IDC 107 → display 46) and checks the pause menu.
- **Open CE PRs that could fork mission semantics**: for example #208 "Add unit loadout scripting
  commands". A mission using such commands would fail on Steam builds.

## 7. What this means for ofp-editor

### 7.1 Reference for porting editor logic and formats

- **[V]** Editor code and the config parser are practically identical in both repos. CE adds a few
  robustness fixes (codepages, addon checks) and more tests and fixtures: 54 `mission.sqm` files and
  37 `.pbo` fixtures under `tests/` (CWR 3.05 has 52 and 28). They are covered by the repo's GPL
  licence. Whether all of them are synthetic is not stated (unverified).
- **[V]** The mission loader accepts **both binarised and text** `mission.sqm`. `ParseCutscene` tries
  `LoadBin` first, then `Load`, and still loads an `Intel` class when the archive version is below 7
  (`ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/UI/Map/UIArcadeWaypoint.cpp#L920-L965`).
- **[V]** The editor's dialog layout comes from game config: `Load("RscDisplayArcadeMap")`
  (`engine/Poseidon/UI/Map/UIMapExt.cpp#L2895`). The layout values themselves (positions, fonts, colours)
  are therefore not in the GPL repos.
- **Practice**:
  - Read CE at a pinned SHA.
  - Diff against the latest CWR snapshot before relying on behaviour ("does Steam 3.05 do this?").
  - Put the upstream path, SHA and line range in a provenance comment on every ported function.

### 7.2 Launching the game for Preview

Launch mechanisms found in the code (identical in CWR 3.05 and CE HEAD) [V code]:

| Mechanism | What the code does | Release build? |
| --- | --- | --- |
| Positional `<...>/<name>.<island>/mission.sqm` | The path is copied into the legacy global `LoadFile` (`AppConfig.cpp#L1130-L1137`). On boot, `World::StartIntro`, *only if the Editor module is registered and the extension is `.sqm`*, calls `ProcessFullName` and then **`OpenEditor()`**, which creates `DisplayArcadeMap` (`WorldImpl.cpp#L2217-L2258`, `DisplayUIMenus.cpp#L1979-L1990`). `.fps`/`.sqg` saves are also accepted. **`.pbo` has no branch there, although the help text says ".pbo or .sqm".** | Yes, shown in basic help (`#L764`). |
| `--autotest` + positional `.sqm` | `StartAutoTest()`: ParseMission (falls back to Intro), SwitchLandscape, ActivateAddons, InitGeneral, `InitVehicles(GModeArcade)`, deletes `weapons.cfg`/`continue.fps`/`autosave.fps`/`save.fps` in the save dir, then opens `DisplayMission` (`DisplayUIMenus.cpp#L2012-L2064`). **This closely mirrors the load/init steps of the editor's Preview button** (`UIMapExtDisplay.cpp#L452-L537`), but it is not identical. Preview uses the in-memory template and calls `ScanRequiredAddons`. Shift+Preview shows the briefing first. Preview opens `DisplayMission(this, true)` (the editor flag) as a child of the editor, whereas autotest opens `DisplayMission(options)` from the main menu, so the mission does not return to an editor. | Yes, hidden (`AppConfig.cpp#L627`). |
| `--test-mission <dir or mission.sqm>` | Copies the mission into `<TempDir>/mission-smoke/<random>/Missions/`, sets AutoTest, and "run[s] … directly and exit[s]" (`GameApplication.cpp#L150-L187`, `#L1697-L1735`). It also enables the `tri*` test SQF commands (`GameStateExtTestAudio.cpp#L2993`). **Pass the folder.** Given a `mission.sqm` file, only that file is copied, to `.../Missions/mission.sqm` (`#L177-L181`). `DescribeMissionFile` then finds no `<name>.<island>` folder, `ProcessFullName` fails, and nothing starts [I from code]. Trident passes the folder (`engine/Trident/src/scenarios/integration.rs#L1144`). | Yes, hidden (`#L668-L670`). |
| `--check --test-mission <path>` | Mission smoke check: boots, logs "AUTO-TEST SUCCESS", exits with 0 once the mission (or an intro-only mission) is running (`DisplayUIMenus.cpp#L931-L941`, `#L1213-L1222`). Exits 1 if `StartAutoTest` fails and 44 if the path does not resolve to a `mission.sqm`. No exit code is set if `ProcessFullName` rejects the path [I]. **This can act as a "does it load?" oracle for the AI agent loop.** | Yes, hidden. |
| `--harness <0-65535>` | TCP server bound to **127.0.0.1 only** (`HarnessServer.cpp#L98`), speaking newline-delimited JSON. Commands: ping, describe, key, key_up, click, query, screenshot, wait_display, **eval/exec (SQF)**, http_fixture, exit. Events: ready, display, log, mission_state, exit, … (`engine/Trident/protocol/harness.schema.json`). | Yes, hidden (`#L662-L666`). |
| Useful companions | `--window`, `--width`/`--height`, `--no-splash`, `--mod=` (legacy `-mod=`, `-nosplash`, `-nomap`, `-oldpaths` are normalised, `#L86-L106`), `--render dummy/gl33`, `--no-menu-scene`. | Yes. |

- **Gating [V]**:
  - The only option removed from release builds is `--dev` (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Foundation/Platform/AppConfig.cpp#L287-L292`, `#L606-L612`).
  - "Hidden" means Dev-level help visibility. Dev options are listed only for `--help --dev`
    (`AppConfig.cpp#L139-L179`), and a release build rejects `--dev` before parsing. So in a release
    build `--autotest`, `--test-mission`, `--check` and `--harness` appear in **no** help output,
    `--help-full` included. They still parse.
  - A build is a "release build" only when `OFPR_BUILD_VERSION_TAG=release` is set
    (`cmake/GenerateBuildInfo.cmake#L22-L39`). CE CI builds are therefore non-release builds.
  - **Whether the Steam 3.05 binary behaves this way at runtime has not been tested [U].**
- **Constraints [V]**:
  - The mission path must end in `<name>.<island>/mission.sqm` (`engine/Poseidon/Game/Mission/MissionPathLoader.hpp#L56-L88`).
    The parent directory can be anywhere, because `ProcessFullName` calls `SetBaseDirectory("")`.
  - **`PoseidonGameDemo` registers only the Missions module; `EditorModule::Register()` is commented out**
    (`apps/cwr/GameDemo/GameDemoApplication.cpp#L5-L12`). The full game registers it
    (`apps/cwr/Game/GameApplication.cpp#L1891-L1898`). Because the `.sqm` branch is gated on the Editor
    module, **neither the editor path nor the autotest path works with the Demo exe**.
  - `StartIntro` only runs when the menu scene is enabled (`GameApplication.cpp#L1731-L1734`). Do not pass
    `--no-menu-scene` together with a mission path.
  - `GameApplication.cpp#L1701` declares `extern char LoadFile[256]`, but the definition is
    `char LoadFile[512]` (`Shutdown.cpp#L101`). Test-mission paths are therefore truncated at 255 bytes.
    The path that gets truncated is the game's own re-staged path,
    `<TempDir>/mission-smoke/<16 hex>/Missions/<name>.<island>/mission.sqm`, so keep mission folder
    names short. `POSEIDON_TEMP_DIR` can shorten TempDir (`GamePaths.cpp#L97`). This is an upstream fix
    candidate.
  - Editor missions normally live under `UserContentDir/missions` and `MPMissions`: Documents on
    Windows, XDG data on Linux (`GamePaths.cpp#L96-L120`). This can be overridden with
    `POSEIDON_USER_CONTENT_DIR` or `POSEIDON_USER_DIR`, and `--oldpaths` switches to the legacy layout
    under the current directory.
- **Conflicting evidence [U]**:
  - CE issue #35 (open) asks for command-line flags that launch the editor directly.
  - A commenter there (her001, the only public CE org member) says passing the mission file "just"
    goes into the mission, and that "there is no way right now to open it in the editor". That
    contradicts the code above.
  - One possible cause [I]: `OpenEditor()` returns early if `GWorld->Options()` does not exist yet at
    that point in boot. That would explain "no editor" but not "starts the mission", so the report is
    still unexplained.
  - **The first spike should test each row of the table against Steam 3.05 and against a CE build.**

**Suggested Preview design**:

1. Write the mission to a short staging path `<stage>/<name>.<island>/mission.sqm`.
2. Launch `<exe> --window --no-splash [--mod=...] --autotest <path>`, or
   `--test-mission <stage>/<name>.<island>` (the folder, not the file) when the game should exit at the
   end.
3. Optionally add `--harness 0` and read `HARNESS_PORT=` from stdout
   (`HarnessServer.cpp#L129`) to observe display and mission_state events or push SQF.
4. Probe `--version` at runtime. `--help-full` cannot confirm the Dev-level flags, because they are
   never listed in release builds. Unknown flags do not cause an error either: the parser tolerates
   them (`allow_extras()`, `AppConfig.cpp#L322`) and only warns. Detect support by behaviour, for
   example a `HARNESS_PORT=` line on stdout, or `AUTO-TEST SUCCESS` and exit code 0 from a
   `--check --test-mission` dry run.

### 7.3 Contributing upstream (CE only)

Candidate patches, each to be opened as an issue or discussion first as `CONTRIBUTING.md#L74-L78`
asks:

1. Documented, basic-visible flags `--editor <mission>` and `--preview <mission>`. These implement CE
   #35 and close the "launch options not documented" gap raised in CE #166.
2. Fix the `LoadFile` array-size mismatch.
3. Handle a positional `.pbo`, or correct the help text.
4. Harness `load_mission` / `preview` commands and a `mission_end` event, for a live-preview link.
5. Clarify the licence metadata of the Rust crates (§7.4).

Target `main` and let the maintainers decide on `port`. Follow the AI-authorship rules, which means
turning off any agent-added trailers.

### 7.4 Reusable components and licence ambiguity

- **[V]** Every Rust crate declares `license = "MIT"` in its Cargo.toml:
  - `tri`: `engine/Trident/Cargo.toml#L6`.
  - `papa-bear-archive`/`-client`/`-cli`/`-master-service`: for example `mserver/Archive/Cargo.toml#L6`.
- **[V]** The repo LICENSE and README cover "the source in this repository" as GPL, and only
  `thirdparty/` is excluded. No licence file exists inside those crates.
- **[U]** Which licence applies is not settled. Until upstream clarifies, **treat these crates as GPL**.
- The following could be useful if the licences allow it:
  - **PBO pack/unpack**: `mserver/Archive/src/pbo.rs`, 473 lines.
  - **The harness protocol client**: `engine/Trident/src/client`.
  - The C ABI `PoseidonFormats` library for P3D, PAA, PBO and RTM (`engine/PoseidonFormats/PoseidonFormats.h`).

## 8. Other forks, derivatives and prior standalone editor tools

### 8.1 Forks and derivatives

| Project | What | Signal (2026-09-26) |
| --- | --- | --- |
| `koosoli/PoseidonVK` | Vulkan and modernisation derivative of CE (not a GitHub fork) that "tries to stay compatible with upstream CWR-CE" | 9 stars, about 207 commits [V web] |
| `McArdle-Systems/CWR-CE` (and `CWR-arm64`) | Apple Silicon, iOS and iPadOS port; CE PR #92 adds a Metal renderer | active to 09-12 |
| `CWR-Ports/CWR-Ports` | Android / arm64 port (fork of BI/CWR) | 6 stars |
| `MotionMark1111/Poseidon.wasm`, `dbeef/operation-wasmpoint` | WebAssembly / browser demo builds | small |
| `f0xeri/CWR-CE-Vulkan`, `belx-dev/OFF-1986`, `igiteam/openofpcwr` | Experimental forks. igiteam opened CE #35. | small |
| `DK26/CWR` (this project's owner) | Fork of BI/CWR adding a **Rust Poseidon LSP + linter** for SQF/SQS and ParamFile (`.sqm`/`.ext`). Its catalog of 612 command overloads is "extracted from engine source". Licensed GPL-3.0-or-later (commit `20e3334de0`). | Candidate validator for the AI agent loop |

- Most of BI/CWR's 173 forks are inactive mirrors.
- No fork was found that works on the mission editor itself or on a standalone editor. GitHub
  repository search for `"Cold War Assault"` created after 2026-06-21 finds only the projects above,
  plus translations and a PAA converter [V].

### 8.2 Prior standalone or external mission-editing tools (OFP/CWA era)

- **Faguss (ofp-faguss.com)**:
  - *MissionEditor3D v0.25*: "Real time mission editor". It edits `mission.sqm` while the mission runs
    and needs Fwatch 1.16.
  - *Set-Pos-In-Game*, *In-Game Script Editor* and *Flashpoint Cutscene Maker*.
  - Fwatch itself is the scripting extension `Faguss/fwatch`, still pushed in 2026-09.
  - This is the closest prior art for "edit and see it live".
- **OFPEC Editors Depot**:
  - *Mando_OFPClass*, which lists the unit classes used in a `mission.sqm`.
  - Mikero's *OfpCmaker* campaign maker.
  - *Campedit*.
  - *OFP Dialog Maker*.
  - Kegetys' launcher.
- **BI community wiki FAQ**: lists utilities such as Unpack-SQM and DeSQM for encrypted `mission.sqm`,
  and MakePBO and StuffPBO.
- **`kami-/mission-parser`**: a JavaScript `mission.sqm` parser/editor for Arma (MIT, 2015, inactive).
- **Conclusion [I]**: no standalone, visual, OFP-faithful mission editor appears to exist. Earlier tools
  are either in-game script add-ons (Fwatch-based) or text and format utilities.

## 9. Recommendation

| Need | Choice | Why |
| --- | --- | --- |
| (a) Reference for editor logic and formats | **CWR-CE `main`, pinned** (now `b67bf3bd62`). **CWR release commits** (`ffc61838b7` = 3.05) serve as the "official behaviour" baseline. | Same code in both, but CE has the fixes, the tests and the fixtures. The CWR snapshots map to Steam versions that players actually run. |
| (b) Game build to launch for Preview | **The user's installed official full game (Steam app 65790 / GOG), Remastered 3.05 or later**, using `--autotest` or `--test-mission` (pass the mission folder). Allow a configurable executable, for example a CE CI build or self-built `PoseidonGame` (needed on macOS and Linux arm64). **Never the Demo exe.** | Players' missions have to run on official builds. CE artifacts expire. Official Steam builds are compiled from the same launch code [I]. |
| (c) Upstream for patches | **CWR-CE only.** Start with issue #35 and a small, well-tested PR. | BI/CWR rejects PRs. CE's `port` label is the documented path into official Steam patches. |

- Default the editor's "target feature set" to **official 3.05**.
- Offer a "CE extensions" profile only once CE-only mission features (new SQF commands and similar)
  actually land.

## 10. Risks

1. **Bus factor**:
   - One person (simi) wrote about 83% of CE commits.
   - He also cuts the official releases and speaks for "Remastered Development".
   - If he steps back, both repos could stall.
2. **Semantic drift**:
   - CE `main` may gain gameplay or SQF features (for example PR #208) that Steam builds lack.
   - Missions using them will fail for most players.
3. **Undocumented test hooks**:
   - `--autotest`, `--test-mission` and `--harness` are hidden "Dev"-visibility options (see §7.2).
   - They could change or be gated to dev builds in the future, and they are untested on Steam builds.
4. **Opaque official history**: each CWR release is one squashed commit, with no tags and no changelog
   in the repo. The Steam news posts are the changelog.
5. **Licensing**:
   - Porting code carries GPL-3.0-or-later and the Section 7 terms into our project.
   - The MIT metadata on the Rust crates conflicts with the repo LICENSE.
   - The dialog layouts, icons and fonts belong to APL-SA game data and cannot be committed.
6. **Trademarks**:
   - Section 7 forbids distributing modifications that use BI trademarks or "OPERATION FLASHPOINT", and
     forbids claiming affiliation with BI. The README attributes "OPERATION FLASHPOINT" to Electronic
     Arts, so "OFP" involves a third-party mark.
   - Our public repo `DK26/ofp-editor` has the description "A Rust rewrite of OFP / ArmA: Cold War
     Assault Mission Editor". The branding needs a decision.
7. **Platform**:
   - The Linux Steam launch problem is still open (BI/CWR #11).
   - CE builds are not drop-in replacements for the original (pre-remaster) CWA 1.99 install [V].
   - Whether a 1.99-era exe supports launching a mission from the command line is unknown [U].

## 11. Monitoring plan

- **Pins**: keep the upstream SHAs (CE and CWR) in a single tracked file, for example an `UPSTREAM`
  section in `CODE-INDEX.md`. Include the SHA in every provenance comment.
- **Weekly CI job** (read-only):
  - Run `git ls-remote` on both repos.
  - If CWR `main` moved, treat it as a new official release: re-run the format and launch smoke tests.
  - For CE, run `git diff --stat <pin>..origin/main` over these watched paths:
    - `engine/Poseidon/UI/Map/`
    - `engine/Poseidon/AI/ArcadeTemplate*`
    - `engine/Poseidon/IO/ParamFile*`
    - `engine/Poseidon/IO/Serialization/`
    - `engine/Poseidon/Game/Mission/`
    - `engine/Poseidon/Foundation/Platform/AppConfig.*`
    - `engine/Poseidon/Foundation/Common/GamePaths.*`
    - `apps/cwr/Game/GameApplication.cpp`
    - `engine/Poseidon/Dev/Harness/`
    - `engine/Trident/protocol/`
    - `mserver/Archive/`
    - `LICENSE`, `CONTRIBUTING.md`
  - Open an issue in our repo whenever any of them changes.
- **Feeds**:
  - Steam news API for app 65790 (patch announcements).
  - CE issues #35, #166, #185 and #234, and PR #208.
  - PRs labelled `port`.
  - Creation of an `official` branch.
  - The CE-builds index.
- **Health signal**: each quarter, check the share of non-simi commits and the number of distinct
  contributors in CE.

## Open questions

1. At runtime on Steam 3.05, does positional `mission.sqm` open the editor (as the code says) or start
   the mission (as the CE #35 comment says)? Do `--autotest`, `--test-mission` and `--harness` work in
   the Steam binary?
2. What are the executable names and install paths per platform for the Steam and GOG builds? The CMake
   target is `PoseidonGame`; the Steam file naming is not verified. The Steam install holds the classic
   and Remastered versions side by side (Steam "Out Now" post), so the launcher must pick the
   Remastered exe. Is GOG at parity with 3.05?
3. Are the Rust crates in these repos MIT (per Cargo.toml) or GPL-3.0-or-later (per LICENSE)? Ask
   upstream.
4. Is a Rust *translation* of the editor logic a derivative work that forces GPL-3.0-or-later plus the
   Section 7 terms? Or should we write specs clean-room? This is for the licensing research doc.
5. Will CE create the `official` branch, and will BI keep pushing a snapshot to CWR for every Steam patch?
6. For missions staged outside the user content dir, where does the save dir that `--autotest` cleans
   resolve to?

## Sources

Code (pinned):

- `BohemiaInteractive/CWR@ffc61838b7`:
  - `README.md#L4-L18`, `#L62`, `#L86-L92`
  - `CONTRIBUTING.md#L7-L17`, `#L34-L39`
  - `CREDITS.md#L25`, `#L40-L41`
  - `LICENSE#L682-L721`
  - `engine/Poseidon/Foundation/Platform/AppConfig.cpp#L287-L292`, `#L606-L612`, `#L627`, `#L662-L670`, `#L764`
  - `engine/Trident/Cargo.toml#L6`
  - `mserver/Archive/Cargo.toml#L6`
  - `apps/README.md#L9-L36`
- `ofpisnotdead-com/CWR-CE@b67bf3bd62`:
  - `README.md#L5`, `#L32`, `#L65-L70`, `#L131-L139`
  - `CONTRIBUTING.md#L20-L32`, `#L59-L72`, `#L74-L78`
  - `engine/Poseidon/Foundation/Platform/VersionNo.h#L9-L10`
  - `engine/Poseidon/Foundation/Platform/AppConfig.cpp#L86-L106`, `#L139-L179`, `#L287-L292`, `#L322`, `#L343-L362`, `#L482`, `#L513`, `#L524`, `#L627`, `#L662-L670`, `#L764`, `#L1130-L1137`
  - `engine/Poseidon/World/WorldImpl.cpp#L2217-L2258`
  - `engine/Poseidon/UI/DisplayUIMenus.cpp#L784`, `#L931-L941`, `#L1213-L1222`, `#L1979-L1990`, `#L2012-L2064`
  - `engine/Poseidon/UI/Map/UIMapExtDisplay.cpp#L452-L537`
  - `engine/Poseidon/UI/Map/UIArcadeWaypoint.cpp#L904-L965`
  - `engine/Poseidon/UI/Map/UIMapExt.cpp#L2895`
  - `engine/Poseidon/Game/Mission/MissionPathLoader.hpp#L28-L88`
  - `apps/cwr/Game/GameApplication.cpp#L150-L187`, `#L552-L560`, `#L1697-L1735`, `#L1891-L1898`
  - `engine/Trident/src/scenarios/integration.rs#L1144`
  - `engine/Poseidon/Foundation/Platform/Shutdown.cpp#L101`
  - `apps/cwr/GameDemo/GameDemoApplication.cpp#L5-L12`
  - `engine/Poseidon/Foundation/Common/GamePaths.cpp#L96-L120`
  - `engine/Poseidon/Game/Mission/MissionPathLoader.hpp#L28-L54` (`ResolveMissionFile`)
  - `engine/Poseidon/Dev/Harness/HarnessServer.cpp#L98`, `#L129`
  - `engine/Poseidon/Game/Commands/GameStateExtTestAudio.cpp#L2993`
  - `engine/Trident/protocol/harness.schema.json`
  - `cmake/GenerateBuildInfo.cmake#L22-L39`
  - `.github/workflows/build.yml#L377-L396`
  - `tests/integration/ui/editor/editor_unit_and_preview.test.sqf#L33-L38`
  - `engine/PoseidonFormats/PoseidonFormats.h#L34-L115`
- CE commits cited: `93e7da0`, `ea80764`, `d7a8967`, `80856fd`, `bc1952a`, `f657230`, `e88327c`, `6c35ff7`, `0418966`, `03e57d5`, `8ed2d06`.

Web (accessed 2026-09-26):

- <https://github.com/BohemiaInteractive/CWR> and <https://api.github.com/repos/BohemiaInteractive/CWR>
- <https://github.com/ofpisnotdead-com/CWR-CE> and <https://api.github.com/repos/ofpisnotdead-com/CWR-CE> (plus `/branches`, `/releases`, `/contributors`, `/labels`, and the search API for PR/issue counts)
- <https://github.com/ofpisnotdead-com/CWR-CE/issues/35>, <https://github.com/ofpisnotdead-com/CWR-CE/issues/166>
- <https://github.com/ofpisnotdead-com/CWR-CE/issues/8#issuecomment-4772323490>, <https://github.com/ofpisnotdead-com/CWR-CE/issues/29#issuecomment-4803747960>
- <https://github.com/BohemiaInteractive/CWR/issues/5>, <https://github.com/BohemiaInteractive/CWR/issues/17>
- <https://github.com/ofpisnotdead-com/CWR-CE/discussions>
- <https://ofpisnotdead-com.github.io/CWR-CE-builds/>
- <https://ofpisnotdead.com/> ; <https://github.com/ofpisnotdead-com> ; <https://papa-bear.cz/>
- <https://store.steampowered.com/api/appdetails?appids=65790> ; <https://store.steampowered.com/api/appdetails?appids=4819000>
- <https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=65790> ("Out Now" 2026-07-16; "Update 3.05" and "SITREP" 2026-08-17)
- <https://www.gamingonlinux.com/2026/07/arma-cold-war-assault-remastered-is-now-out-in-full-and-open-source/> (release date 16 July 2026)
- <https://github.com/ofpisnotdead-com/CWR-CE/pull/19> (macOS, label `port`)
- <https://www.bohemia.net/en/blog/Arma-Cold-War-Assault-Remastered-Out-Now>
- <https://news.ycombinator.com/item?id=48636753>
- <https://www.bohemia.net/community/licenses/arma-public-license-share-alike>
- <https://api.github.com/repos/BohemiaInteractive/CWR/forks> ; <https://api.github.com/repos/ofpisnotdead-com/CWR-CE/forks>
- <https://github.com/koosoli/PoseidonVK> ; <https://github.com/McArdle-Systems/CWR-CE> ; <https://github.com/CWR-Ports/CWR-Ports> ; <https://github.com/igiteam/openofpcwr>
- <https://github.com/DK26/CWR/commit/20e3334de0>
- <https://github.com/Faguss/fwatch> ; <https://ofp-faguss.com/all> ; <https://ofp-faguss.com/files/missioneditor3d.pdf>
- <https://www.ofpec.com/editors-depot/index.php?action=list&game=OFP&cat=to&type=me>
- <https://community.bistudio.com/wiki/Operation_Flashpoint:_FAQ:_Mission_Editing>
- <https://github.com/kami-/mission-parser>

## Verification notes

Adversarial fact-check, 2026-09-26, against the same pinned clones plus the GitHub, Steam and web
sources above.

**Checked and confirmed**:

- BI/CWR repo model: README, CONTRIBUTING and CREDITS line ranges; 5 commits; no tags or releases;
  0 PRs; issue #5 and #17 quotes.
- The snapshot `VersionNo.h` values are 3.0 → 3.01 → 3.03 → 3.05.
- CE figures: 316 commits, including monthly counts by commit date; 10 contributors; 216/151/53 PRs;
  93/64 issues; `port` label on 96 PRs; no `official` branch; no releases.
- Merge-base `ea77e57`, and all whole-tree, editor, launch-path and Rust diff numbers.
- Editor code:
  - `StartIntro`, `OpenEditor`, `StartAutoTest`, `ParseCutscene` (LoadBin then Load), `DescribeMissionFile`.
  - The Demo module list, the `LoadFile[256]`/`[512]` mismatch, the smoke-check exit codes (0/1/44)
    and the `127.0.0.1` harness bind.
  - Harness schema v1 command and event names; `--dev` as the only release-gated flag.
- Cargo `license = "MIT"` on all five crates; LICENSE Section 7 text, byte-identical in both repos.
- `RscDisplayArcadeMap` appears only as a `Load()` call.
- Steam appdetails (both apps Windows and Linux only; demo released Jun 22, 2026; developers
  string) and the SITREP quotes.
- CE builds page quotes; DK26/CWR commit `20e3334de0` (612 overloads, GPL-3.0-or-later); fork
  metadata; Faguss tool list.

**Changed**:

- Steam "Out Now" date: 07-12 → **07-16**, per the Steam news API timestamp and GamingOnLinux.
- `--autotest` is no longer called "the same sequence" as Preview; the differences are now listed.
- "Hidden from basic help" is corrected to "hidden from all help in release builds". The Preview
  design no longer relies on probing `--help-full`, and it notes that unknown flags are tolerated.
- New code-derived finding [I]: `--test-mission` must be given the mission folder, not the
  `mission.sqm` file.
- Counts:
  - Editor-code lines: 28.2k covers only `UI/Map` + `ArcadeTemplate*`; ≈31.1k with `IO/Serialization`.
  - Fixtures: 54 `mission.sqm` / 37 `.pbo` (not 55/40); "synthetic" marked unverified.
  - `main.rs`: +483/−60 (not "+543").
  - ParamFile diff cells are now filled in.
- The CE drop-in guidance now reflects the current README (Remastered folder OK). The June Demo
  advice predates the full release.
- Smaller fixes:
  - macOS clarified as source-only, with PR #19 cited.
  - CE has 8 feature branches besides `main`.
  - The Section 7 affiliation clause and EA's ownership of the "OPERATION FLASHPOINT" mark were added.
  - PoseidonVK is not a GitHub fork.
  - The `PoseidonFormats.h` line range was corrected.
  - The Steam install ships classic and Remastered side by side (open question 2).

**Still unverified**:

- Runtime behaviour on the Steam 3.05 binary (all launch rows).
- Whether Steam builds set `OFPR_BUILD_VERSION_TAG=release`.
- The cause of the CE #35 report.
- The HN thread, the OFPEC and BI-wiki tool lists, and the Faguss PDF were not re-opened.
