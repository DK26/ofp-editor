# Upstream test inventory and porting plan

Research doc 20 for `ofp-editor`. Audience: contributors and LLM agents who port upstream code. This file is meant to be read on its own.
Question answered: which tests ship with the released engine source, which of them we must port (and in what order), which become
in-game probes, and how to keep the tracking map `docs/porting/upstream-test-map.csv` current.

**Pinned upstream.** `BohemiaInteractive/CWR@ffc61838b7` ("CWR") and its community continuation `ofpisnotdead-com/CWR-CE@b67bf3bd62`
("CE"). Both are GPL-3.0-or-later with Bohemia's section 7 additional terms. Paths in this doc and in the CSV are relative to the repo
root at those commits. Unless a row says otherwise, a line citation such as `express.cpp:1123` means `engine/Evaluator/express.cpp` in CWR.

**How this was produced.** Five partition reviewers read both clones (evaluator; editor and mission; core formats including the
`Asset/` and `Dev/` trees; harness and infrastructure; Rust crates and the remaining engine directories). An adversarial pass then
re-checked every row: file lists (SHA-256/MD5 comparisons between the clones), `TEST_CASE`/`#[test]`/`It` counts, and relevance
claims against the engine source. **Nothing was built or executed.** Every "1.99" statement below is inferred from source unless it
is marked as needing a probe.

**Epistemic tags.** **[V]** verified by reading pinned source. **[I]** inferred from verified facts. **[U]** unknown; needs a probe on
the original CWA 1.99 binary.

## TL;DR

- **The map has 636 rows covering 4,659 upstream test cases** (Catch2 `TEST_CASE`s, Rust tests, Pester `It` blocks, one per integration
  test and one per fuzz target; CE counts for files CE modified). Only a small part matters to an editor:

  | Relevance | Rows | Test cases | CSV status |
  | --- | ---: | ---: | --- |
  | port-now | 74 | 821 | `todo` |
  | port-with-module | 68 | 411 | `todo` |
  | adapt-as-probe | 20 | 22 | `probe` |
  | reference | 102 | 808 | `reference` |
  | not-applicable | 372 | 2,597 | `not-applicable` |

- **Port first, in this order:** PBO (including the CE `mserver/Archive` Rust crate's own tests and the LZSS vectors), config text,
  preprocessor, rapified config and stringtables, the SQF/SQS evaluator goldens, mission-folder and mission-text semantics, PAA,
  FXY fonts and WRP. These are the 74 port-now rows (up to 821 cases, including fixture and fuzz-target rows), almost all
  with inline or small synthetic fixtures.
- **Upstream assertions are uneven.** `test_paramfile_preprocessing.cpp` is 49/49 `REQUIRE(true)`, `test_paramfile_expressions.cpp`
  46/49, and roughly 60-70% of the evaluator assertions are tautological. The partition reviewers resolved most of these "no-oracle"
  cases from engine source. Port them as **source-derived goldens tagged `unverified-1.99`**, then confirm them in one batch of 1.99
  probes. This gives a much stronger suite than a verbatim port.
- **There are no behavioral unit tests of the Arcade editor, `ArcadeTemplate` serialization, trigger semantics or map drawing
  upstream** (`test_editor.cpp`, `test_detector.cpp` and `test_uiMap.cpp` are compile checks). Editor-core, mission-model and
  map-render tests must be written from the ported source, using the synthetic mission corpus as round-trip goldens.
- **The in-game runner (Trident, `tri`) is reusable against CE builds, including stock release builds**, which accept
  `--harness 0`, `--test-mission`, `--autotest` and `--check`. **Nothing runs on CWA 1.99**, which has no harness and no `tri*`
  commands. We need our own 1.99 probe backend (§4.4). One pitfall: in mission-dir mode every mission end exits 0, so an exit code
  never tells you *which* ending fired.
- **Fixtures:** most are synthetic and can be reused under GPL with attribution. **Never copy** `tests/fixtures/savegame/save.fps`,
  the photographic MP face textures, the unprovenanced `face.paa`/48 KB `.wav` files, anything under `packages/`, or the game-derived
  P3D goldens hard-coded in dead tests (§5).
- **Coverage fixes found during the review:** `tests/unit/engine/Poseidon/Asset/**` and `Dev/**` were missing from the original
  partition list. They hold the only WRP reader test, the PAA container test and `test_config_replace`. `mserver/Archive` is an
  existing Rust PBO reader/writer whose 5 tests nobody had claimed. 17 test files are compiled by no CMake target (dead).

## 1. What the upstream suites are and how they run

### 1.1 Unit tests (Catch2 v3, C++)

- **Framework:** Catch2 v3 (`catch2/catch_test_macros.hpp`, `Catch::Approx`, string matchers). Tests are registered through
  `ofpr_catch_discover_tests` (`cmake/CatchWindowsSafe.cmake`) and run with `ctest`.
- **Executables** (`tests/unit/engine/Poseidon/CMakeLists.txt`):
  - `PoseidonCoreTests`: the engine evaluator tests (`tests/unit/engine/Evaluator`), IO, ParamFile, PreprocC, Streams,
    `Asset/Addon/test_config_replace`, `Asset/Formats/Common/test_format_detector`, and the stringtable/codepage suite. It uses
    `Support/test_stubs.cpp`, `test_stubs.hpp` and `test_fixtures.hpp`.
  - `PoseidonTests`: Graphics, Core, Tools, TcPbo (Windows only), Platform, `Asset/Cache`, the BISFramework tests, `test_wrp`,
    `test_rtm`, `test_paa`, `test_pac`, `test_p3d_model_load`, `P3D/test_mlod_loader`, `test_poseidon_formats_capi`, `Asset/Probes`
    and `Dev`. It uses the **root-level** `test_main.cpp`, `test_stubs.cpp` and `test_fixtures.hpp`. These differ from the
    `Support/` copies but use the same lookup.
  - `PoseidonFoundationTests` (`Foundation/CMakeLists.txt`) and `PoseidonEvaluatorTests` (`tests/unit/apps/Evaluator`, custom
    Catch main).
- **Engine evaluator fixture.** `GGameState.Init()` is called once and registers only the core tables (`express.cpp:2361-2396`):
  nulars `nil true false pi`; unary math, `count call comment private parseSimpleArray if while for`; binary arithmetic, comparison,
  logic and `select set resize count forEach in find then else exitWith do from to step call`. Variables and custom operators
  persist across `TEST_CASE`s, so test order matters upstream. It must not matter in our port.
- **Apps evaluator host.** `EvaluatorHost` registers a **mock world** (`engine/Evaluator/EvalState.cpp:186-218, 341-763`) with
  shapes the engine does not have: unary array-form `createUnit`/`createVehicle`, `setVariable`/`getVariable`, `str`, `toArray`,
  `toString`, `diag_log` and unary `exitWith`. Every golden taken from this binary must record which command table it assumes.
- **Fixture lookup.** `GET_FIXTURE`/`REQUIRE_FIXTURE` look in `<exeDir>/fixtures/<name>`, then walk up to `tests/fixtures/<name>`.
  Post-build copy steps **remap paths**, so tests often open names that do not exist in the source tree:
  - `PoseidonCoreTests` flattens `config/`, `xml/`, `stringtable/` and `evaluator/`, so tests open `simple.txt` or
    `weapon_modes_lang.csv`.
  - `PoseidonTests` copies `paa/` and `pac/` to `texture/paa` and `texture/pac`.
- **Tags.** `[gamescan]`, `[GameData]` and `[external-data]` tests are excluded unless `packages/Remaster` exists. That directory is
  git-ignored, BI-licensed game data. `[.]`/`[.disabled]` hide tests: 3 in `test_preprocC`, 4 in `test_paramfile_binary`, 1 in
  `test_paramfile_inheritance`.
- **Dead tests.** 17 files are compiled by no CMake target in either repo: `BinaryFormats/test_p3d_mlod_to_odol_conversion.cpp`,
  `Asset/Formats/Common/test_csv_reader.cpp`, and 15 of the 16 `Asset/Formats/P3D/**` files (only `test_mlod_loader.cpp` is built).
  **Always check the CMake source lists before porting a file.**

### 1.2 Rust tests

- **Trident** (`engine/Trident`, crate `tri`): 102 tests in CE, 100 in CWR, as in-module `#[cfg(test)]` with `#[tokio::test]`
  for async. By file: `config.rs` 2, `protocol/types.rs` 19, `client/connection.rs` 10, `client/instance.rs` 7 (2 are
  `#[cfg(unix)]` and read `/proc`, so effectively Linux-only), `client/port_alloc.rs` 4 (dead code), `scenarios/integration.rs` 36
  (19 runner + 17 script-parsing), `scenarios/multi.rs` 20, `scenarios/stress.rs` 4.
- **mserver** (papa-bear crates): `Archive/src/pbo.rs` 5 (PBO reader/writer plus LZSS), `CLI/tests/cli_roundtrip.rs` 1, and
  `CLI/src/main.rs` 18. The `Client` (13) and `MasterService` (78) tests cover networking and a web backend.
- Both repos have a root Cargo workspace, so `cargo test` at the root runs everything; CE's `build.yml` does exactly that.
  Cargo metadata says `license = "MIT"`, but no MIT text or copyright holder ships. Treat these crates as GPL-3.0-or-later with the
  section 7 terms (§5).

### 1.3 Integration tests (Trident runner)

- **Invocation:** `tri test -j6 --retries 2 tests/integration` with `.trident.env` (`OFPR_GAME_DIR` = build/dist dir,
  `OFPR_DATA_DIR` = `packages/Demo`) (`tests/README.md`).
- **Discovery units:** `foo.test.sqf` with an optional `foo.test.toml` sidecar; `foo.test.<island>/` mission dirs (sidecar
  `foo.test.<island>.toml` in the parent); `foo.test/` multi-instance dirs with `test.toml`; `foo.seq/` ordered multi-boot phases.
- **Sidecar keys (`TestMeta`):** `type, mission, test_type, no_menu, no_player, extra_args, timeout, assert_timeout, binary,
  data_dir, no_autotest, language, tags` (`exclusive` reserves every slot). Some manifests use `package = "packages/Remaster"`.
  **The parser is lenient:** unknown keys are ignored and a TOML parse error only logs a warning, then uses defaults.
- **Directories:** `ai, flows, harness, helpers, ingame, missions, mods, mp, multiplayer, rendering, scripting, ui`. Nearly all
  tests need BI game data (`packages/Demo` or `packages/Remaster`) and CWR-only `tri*` script commands. **None runs on 1.99 as-is.**
- **Opt-in CTest bridge.** `cmake/{TridentCTest,RunTridentCTest}.cmake` registers one serial CTest per root (1800 s timeout) when
  `OFPR_REGISTER_TRIDENT_CTESTS=ON` and `packages/Remaster` exists. It is off by default and never enabled in CI.

### 1.4 Smoke, e2e, stress, perf, fuzzers, CI

- `tests/smoke/*.tests.ps1`: Pester v5, 34 `It` blocks. Every file imports `tests/cli/TestHelpers.psm1`, which is missing from both
  trees, so **none is runnable as shipped**.
- `tests/e2e`: 1 test whose orchestrator is missing. `tests/stress/mp`: 6 toxiproxy soak scenarios, 2 of which reference a
  nonexistent `jip_stress.eden`. `tests/perf/missions`: 5 `mission.sqm` files that no runner consumes.
- `apps/fuzzers/Fuzzer`: 16 libFuzzer targets, built only by the `*-clang-fuzz` presets. No corpus ships, and `run-weekend.ps1` is
  missing.
- **CI exists only in CE** (`.github/workflows/build.yml`, `rust.yml`):
  - `ctest` unit runs on Linux x64/arm64, macOS and Windows. Windows excludes PAAEncoder, `Image - Save to .paa`,
    `World state file format` and PreviewImage saves.
  - The whole Rust workspace is tested.
  - `tri test` runs over `tests/integration` in 4 shards under xvfb + openbox, with Demo assets downloaded at run time.
  - Smoke, e2e, stress, perf and the fuzzers never run in CI, which is why they have gone stale.

## 2. Totals by relevance and target area

Each cell is **rows / test cases**. Fixture and infrastructure rows count 0 cases. For a port-now file the case count is an upper
bound, because some files mix portable and engine-only cases; each row's rationale says which cases to take.

| Target area | port-now | port-with-module | adapt-as-probe | reference | not-applicable | **Total** |
| --- | --- | --- | --- | --- | --- | --- |
| formats-pbo | 11 / 99 | 0 / 0 | 0 / 0 | 3 / 47 | 0 / 0 | **14 / 146** |
| formats-config | 21 / 400 | 2 / 9 | 0 / 0 | 7 / 48 | 1 / 10 | **31 / 467** |
| script-lang | 17 / 164 | 3 / 10 | 3 / 3 | 11 / 179 | 0 / 0 | **34 / 356** |
| mission-model | 8 / 51 | 0 / 0 | 4 / 4 | 5 / 11 | 1 / 1 | **18 / 67** |
| formats-paa | 10 / 79 | 5 / 47 | 0 / 0 | 0 / 0 | 1 / 17 | **16 / 143** |
| formats-font | 3 / 19 | 1 / 3 | 0 / 0 | 2 / 20 | 1 / 10 | **7 / 52** |
| formats-wrp | 4 / 9 | 9 / 87 | 0 / 0 | 0 / 0 | 0 / 0 | **13 / 96** |
| formats-p3d | 0 / 0 | 10 / 32 | 0 / 0 | 17 / 96 | 3 / 9 | **30 / 137** |
| formats-audio | 0 / 0 | 5 / 16 | 0 / 0 | 3 / 11 | 2 / 2 | **10 / 29** |
| editor-core | 0 / 0 | 6 / 6 | 0 / 0 | 2 / 2 | 1 / 1 | **9 / 9** |
| editor-ui | 0 / 0 | 12 / 68 | 0 / 0 | 6 / 61 | 1 / 27 | **19 / 156** |
| map-render | 0 / 0 | 1 / 1 | 0 / 0 | 2 / 23 | 2 / 2 | **5 / 26** |
| campaign | 0 / 0 | 1 / 1 | 10 / 12 | 3 / 6 | 1 / 1 | **15 / 20** |
| platform-paths | 0 / 0 | 5 / 51 | 1 / 1 | 17 / 232 | 0 / 0 | **23 / 284** |
| preview-harness | 0 / 0 | 8 / 80 | 2 / 2 | 20 / 72 | 2 / 33 | **32 / 187** |
| none | 0 / 0 | 0 / 0 | 0 / 0 | 4 / 0 | 356 / 2,484 | **360 / 2,484** |
| **Total** | **74 / 821** | **68 / 411** | **20 / 22** | **102 / 808** | **372 / 2,597** | **636 / 4,659** |

By origin: 544 rows are identical in both repos, 69 are CE-modified, 22 are CE-only, and 1 is CWR-only (LFS rules for absent
fixtures). The `not-applicable` mass is renderer, audio mixer, input, netcode, VoN, workshop, options UI, C++ containers and math.
Each such row carries a one-line reason.

## 3. Porting plan by area, in dependency order

**Shared prerequisites** (build once, before the first port):

1. **A test-support module.** It needs a fixture root resolved from `CARGO_MANIFEST_DIR` (this replaces `GET_FIXTURE` and the
   flattened and `texture/paa` remaps), an opt-in game-data root read from an environment variable (a proposal; the name is not
   decided), and a little-endian blob builder modeled on `Asset/Formats/BISFramework/test_helpers.hpp`.
2. **A provenance convention.** Each ported test's doc comment cites repo, commit, path and `TEST_CASE`/`SECTION`, as AGENTS.md
   requires. Each copied fixture carries a provenance header or sidecar note plus the section 7 NOTICE, and adapted copies are
   marked as modified. Ported tests and fixtures are CWR-derived, so they must never go into the optional permissive-lane crate
   (docs/research/02 §6).
3. **Golden tables for inline-literal suites.** Keep one golden file per upstream file. Each case records the source (`TEST_CASE`/
   `SECTION`), the mode, the input, the expectation, and the **oracle kind**: `upstream`, `source-derived` (tagged
   `unverified-1.99`) or `probe-verified`. An illustrative shape:

```toml
# Adapted from BohemiaInteractive/CWR@ffc61838b7:tests/unit/engine/Evaluator/test_evaluator_complex.cpp (modified)
[[case]]
source  = "TEST_CASE(\"Error handling\") / SECTION(\"Unclosed paren\")"
dialect = "core-evaluator"   # core-evaluator | cwr-engine | cwr-mock | cwa199-verified
mode    = "Evaluate"         # Evaluate | EvaluateBool | EvaluateMultiple | Execute | CheckEvaluate | CheckEvaluateBool | CheckExecute | SqsParse
input   = "(2 + 3"
expect  = { error = "EvalCloseB" }
oracle  = "source-derived"   # express.cpp:1739-1780; confirm on 1.99
```

### 3.1 formats-pbo (first)

| Port | Golden inputs/outputs it gives us |
| --- | --- |
| `mserver/Archive/src/pbo.rs` (5, Rust) | Stored addon PBO without properties: 3 entries, `config.bin` 110 bytes. Every LZSS entry (`Cprs` = 0x43707273) decodes to its unpacked size and passes the checksum. A `pack_dir` round trip stores the `prefix` property in a `Vers` header entry, uses backslash wire paths and appends no SHA-1. Zip-slip rejection of `../x`, `/x` and `c:/x`. |
| `mserver/CLI/tests/cli_roundtrip.rs` (1) | Pack with `--prefix demo\addon`, then unpack gives byte-identical files and info prints `prefix = demo\addon`. Port as a library round trip. |
| `IO/Streams/test_qstream_pbo_roundtrip.cpp` (8) | Reads both fixture PBOs; `GetProperty`; the writer packs nested paths with backslash separators. |
| `IO/Streams/test_qstream_compression.cpp` (10) | SSCompress LZSS round trips (Okumura N=4096, F=18, THRESHOLD=2; the checksum sums **unsigned** bytes). Add golden vectors from `mission_fixture.Intro.pbo`. |
| `IO/Streams/test_qstream_path_resolution.cpp` (32) | Prefix compare that ignores case and slash direction; `SetPrefix` normalization; AutoBank rules (a drive letter matches nothing); case-insensitive and backslash lookups. |
| `IO/Streams/test_qstream_banks.cpp` (3 of 11) | Negative `headersEncodedSize` rejected; island-intro path `anims/../addons/triisl/intro.abel/mission.sqm` resolves case-insensitively; a deny-all policy blocks `../addons`. |
| `Game/test_game_state_ext.cpp` (PBO cases) | Raw header: the first entry has an empty name, `VersionMagic` and zero sizes, followed by zero-terminated property pairs. `config.cpp` is read back from a built bank. |
| `apps/Studio/...#preview/pbo_archive,vfs/*` (5) | `addon_fixture.pbo` has 3 files totalling 229 B; mounting `Addons/*.pbo` gives 10 VFS entries (3+2+3+2); the Configs category has exactly 2 entries. |
| `IO/Streams/test_qstream_pbo_game_scan.cpp` (4), `apps/fuzzers/Fuzzer/fuzz_pbo.cpp` | An opt-in corpus pass over the user's install (never committed); a cargo-fuzz target plus a never-panics property test. |

Gaps to fill with our own synthetic fixtures: none of the 28 committed PBOs has a `Vers` header entry or properties, and property
parsing is exercised only by an inline fuzz blob. Our writer's compressed path needs its own tests, because the Archive crate only
decodes. CWR treats entry names as UTF-8, whereas 1.99 uses ANSI bytes (`Core/test_mod_archive.cpp`, reference).

### 3.2 formats-config (text grammar, preprocessor, rapified config, class DB, stringtables)

- **Grammar and model:** `test_paramfile_parsing` (41; 20 vacuous error cases need differential oracles), `test_paramfile` (22),
  `test_paramfile_api` (30), `test_paramfile_inheritance` (25), `test_paramfile_access` (21) and `test_paramFile_defaults` (the 2
  fuzz cases). Goldens and facts:
  - `""` is the only string escape; there is no `\xNN`, so legacy bytes appear raw.
  - Bare empty values are legal (`end1 = ;` in real campaign fixtures).
  - The entry **owner** (the defining CfgPatches class) builds `mission.sqm` `addOns[]`/`addOnsAuto[]`.
  - Stock `CfgWorlds` classes are `access=3`, while `CfgWorlds` and `CfgWorldList` themselves are add-only.
- **Preprocessor:** `IO/PreprocC/test_preprocC.cpp` (25, 62 real assertions) is the real coverage. `test_paramfile_preprocessing`
  (45) contributes **inputs only**, because 1.99 probably lacks `#if expr`, `#elif`, `#`, `##` and `__FILE__` [U].
- **Rapified (`raP`):** `test_paramfile_binary` (26; mostly self round trips plus hardening), `apps/fuzzers/Fuzzer/fuzz_paramfile.cpp`,
  and an opt-in corpus pass over real `config.bin` files.
- **Expressions:** `test_paramfile_expressions` (30) supplies inputs only (46/49 assertions are `REQUIRE(true)`). Expected values come
  from the script-lang reference evaluator; `db+0` in `sound[]` is the common real-world case.
- **Stringtables and codepages:** `test_stringtable` (19), `test_stringtable_encoding` (21), `test_codepage_transcode` (36),
  `test_language_registry` (5), `test_localized_string` (5), `test_paramfile_localization` (11) and `fuzz_stringtable`. Goldens:
  - Columns are matched by LANGUAGE header name, not by position.
  - Each column is decoded with its own codepage (CP1250 Czech/Polish, CP1251 Russian, CP1252 Western).
  - COMMENT rows are ignored; `$STR_`/`@STR_` prefixes resolve.
  - Undefined codepage slots map to U+FFFD.
  - CWR-only behaviors stay reference: the `.utf8.csv` preference, shards, the autodetect heuristics and CE's empty-cell fallback
    to English.
- **Realworld configs:** `test_paramfile_realworld` (28) are **grammar tests only**. Their description.ext fixtures use Arma-era
  schema (`class Params`, `class Header`, `CfgBriefing`); CWA 1.99 uses `titleParam1`/`valuesParam1`.
- **Later:** `Asset/Addon/test_config_replace` (a mod's `bin/config.cpp` **replaces** the base config wholesale; confirm on 1.99)
  and the Studio `CfgVehicles >> Car >> speed` class-path lookups.

### 3.3 script-lang (SQF/SQS lexer, parser, type checker, reference evaluator)

- **Port now:** `tests/unit/engine/Evaluator/test_evaluator_{simple,complex,syntax,edge,state_vars,script_integration,integration}.cpp`
  and `tests/unit/apps/Evaluator/test_{expressions,errors,format,sqs_runner,sqs_integration}.cpp`; plus
  `AI/test_entity_event_handlers.cpp` (the 12 event names in legacy order), `Graphics/Rendering/test_smokes.cpp` (`drop` takes 18 or
  19 arguments, and script positions are `[x, north, height]`), the `tests/fixtures/evaluator/**` corpus, and `fuzz_sqf`/`fuzz_sqs`.
- **Parsing depends on the command table.** Whether a name is nular, unary or binary decides the parse, and an unregistered binary
  name is `EvalOper` (`express.cpp:1610-1647, 1797-1831`). Every golden and corpus file therefore needs a dialect tag. Against
  engine-faithful tables, 9 of the 16 fixture scripts parse. `error.sqf` fails at its dangling `+`. The other 6 use mock-only shapes
  and become negative `cwr-mock` tests.
- **Facts the goldens pin down** [V, confirm on 1.99]:
  - The precedence table, from loosest to tightest, is `|| < && < comparison < binary commands < else < + - < * / % mod atan2 <
    unary < ^` (`express.hpp:503-516`). So `-2 ^ 2` is -4 and `sqrt 16 + 9` is 13.
  - `&&` does not short-circuit, and `SetError` overwrites earlier errors.
  - Check mode is what the editor uses for trigger and waypoint fields (`UIArcade.cpp:1106-1111`). In check mode, unknown globals
    type as *any* and `{...}` bodies are opaque. The error text and caret offset are user-visible and should be matched.
  - Variables are case-insensitive: names are lowercased at `express.cpp:2406-2411`.
  - An undefined global is an untyped nil, and operators on nil return a typed nil without an error. A nil Bool reads as false, so
    a condition and its negation can both be false. The 1.99 sentinel `"scalar bool array string 0xfcffffef"` catches only an
    untyped nil.
  - Numbers are f32 rendered with `%g`: integers are exact up to 16,777,216, and only 6 significant digits survive `format`.
  - `format` inserts strings unquoted and silently drops `%0` and out-of-range `%N`.
  - SQS splits `? cond : stmt` at the first `:`. A `?` line without `:` is silently dropped, and `goto` is an ordinary unary command.
- **Hard limits for the linter and campaign compiler** (each needs a probe):
  - 256 operand slots per statement, so array literals with 256 or more elements fail with `EvalLineLong`.
  - A 4,096-byte SQS line buffer.
  - A 256-byte buffer for `~` delay expressions.
  - `format` output of 2,048 characters or more (a likely 1.99 crash).
  - A negative `resize` corrupted the heap in unfixed code.
- **Reference only:** the registration and `GameValue`/`GameData`/`GameVarSpace` tests. Keep their facts for the value model and
  the scope model. `test_mock_objects` is also reference: the mock's `createUnit`/`createVehicle`/`isNull` shapes must not leak
  into our command table. Doc 23 (`docs/research/23-script-tooling-lsp-and-linter.md`) owns the catalog and checker design.

### 3.4 mission-model

- `Game/Mission/test_mission_info.cpp` (21):
  - The `<name>.<world>` split happens at the last dot, backslashes are normalized, and `MISSION.SQM` in upper case is accepted.
  - Folders without a `mission.sqm` are rejected.
  - Trigger END1..END6 map to `end1`..`end6`. **Script-issued endings are invisible to this scan**, so the campaign coverage proof
    must also scan scripts.
- `UI/Locale/test_mission_language_detector.cpp` (21): briefing/overview file order (`briefing.<Lang>.html`, then the generic file),
  `$STR` expansion in HTML that keeps `marker:` links and `OBJ_n` anchors, `briefingName` resolution from the mission stringtable,
  and Templates listing. Rename the CWR-only `*.utf8.*` fixture files first.
- `World/Scene/test_camera_enums.cpp`: `Effects.cameraPosition` is a **named** enum written by `SerializeEnum` (TOP, LEFT, RIGHT,
  FRONT, BACK, LEFT FRONT, RIGHT FRONT, LEFT BACK, RIGHT BACK, LEFT TOP, RIGHT TOP, FRONT TOP, BACK TOP, BOTTOM; default BACK),
  whereas `cameraEffect` is a free `CfgCameraEffects` string.
- `Foundation/Time/test_clock_timeofday.cpp`: the default date is 1985-05-10 07:30 (day fraction 0.3125), and the editor watch
  shows `:01` if it uses only the coarse value.
- `IO/test_paramFileExt.cpp`: resource-path resolution for `CfgSounds`/`CfgMusic`, with a default dir, extension and `strlwr`. CWR's
  fix for the doubled prefix needs a 1.99-vs-CWR switch [U].
- `AI/test_ai.cpp`: legacy-byte user text in markers, waypoints and triggers. Keep the raw bytes and decode only for display.
- Corpora: `tests/integration/missions/*.Demo` (a version=11 corpus that covers sensors, effects, synchronizations and
  `CfgSounds` with `db+0`; four `joinInProgress` missions make negative 1.99 lint fixtures), `tests/fixtures/missions/*` and the
  `perf/missions` samples.

### 3.5 formats-paa, formats-font, formats-wrp

- **PAA:**
  - `Asset/Formats/test_paa.cpp`: type words AI88 0x8080, ARGB4444 0x4444, ARGB1555 0x1555, DXT1-5 0xFF01-0xFF05. Skip `GGAT` TAGG
    blocks and the palette, then read the mip-0 size.
  - `test_pac.cpp`; `Graphics/test_pixel_format.cpp`; `test_mipmap_layout.cpp` (4x4 block rounding, pitch).
  - `test_paa_decoder.cpp`, including the 3 fuzz regressions; `test_paa_decode_fixtures.cpp`; `test_image.cpp` (4444/1555/565/88
    expansion rules).
  - The CE case in `Graphics/Rendering/test_pactext.cpp`: a 16-bit PAA mip header is w16, h16, size24, and its LZSS checksum sums
    **signed** chars (worked example: -113). The shared LZSS decoder needs a signedness parameter.
  - Later: the encoder, the DXT compressor and JPG import (the power-of-two rule is a lint).
  - Gaps: no fixture has TAGGs or a palette, no PAC is really palettised, and none uses the legacy LZW marker. Add synthetic
    fixtures plus an opt-in corpus pass.
- **FXY fonts:** `Graphics/Rendering/test_font_data.cpp` (the file is 2,688 bytes = 224 glyphs x 12; space width = 3/4 of max
  width; texture name `<name>-01.paa`) and `Tools/test_font.cpp`. The fixtures check structure only, so add an opt-in corpus pass
  (`Tools/test_pbo_inspect_scan.cpp`).
- **WRP:** `Asset/Formats/test_wrp.cpp` (4WVR 4x4, 16 heights, 1 texture, objects 17/2/9, `Unknown file format` on bad magic) and
  `World/test_landscape_object_ids.cpp` (static IDs, which "Show IDs" displays). Port `generate_test_world.py` as a Rust builder.
  Later: BISFramework compressed arrays (the LZSS threshold rule for OPRW), `test_serializebin` hardening, and about 20 of the 72
  `World/test_terrain.cpp` cases (height conversion, triangle interpolation, normals) for placement and ASL/ATL.

### 3.6 editor-core and editor-ui (port with the module)

Upstream gives us fragments, not an editor suite:

- **Briefing and debriefing HTML:** `test_optionsUI.cpp` has the HTML-section case (sections split at `<hr>` and named by
  `<a name>`; an unknown section gives empty text), which is the mechanism behind `Debriefing:EndN`. Related:
  `test_html_body_text.cpp` (entities), `test_html_text_wrap.cpp` and the CE `test_html_table_row.cpp`.
- **Controls and layout:** `test_uiControls.cpp` (`idc`/`type`/`style` constants resolve without the evaluator) and the CE
  `test_cursor_layout.cpp` (800x600 layout; Arrow cursor 16x16 with hotspot 0,0; Track cursor 24x24 with hotspot 0.5).
- **Localization:** `test_titeffects_split.cpp` (only the two-byte `\n` splits titles), `test_localized_date.cpp` and
  `test_stringtable_switch.cpp`.
- **Editor behavior:** the `advancedEditor` UserInfo key from `test_game_state_ext.cpp` (Easy/Advanced is original behavior; probe
  the default [U]).
- **Integration flows, rebuilt as our own UI tests:** `arcade_map_language_switch` (an IDC-to-label golden, e.g. 101 Load, 102 Save,
  103 Clear, 106 Merge, 107 Preview, 108 Continue, 112 Show Textures), `editor_mission_save_load` (the name field auto-focuses and the
  Load list is built by folder scan), `editor_mission_save_unicode_name`, `editor_select_island_nordic_chars` and the wizard flows.

### 3.7 map-render, campaign, platform-paths, preview-harness, and the deferred formats

- **map-render:** only `World/test_io_types.cpp` (MapType values; the names come from the P3D LOD `map=` property, parsed in
  `ShapeLOD.cpp`). There are no upstream map-drawing tests. `Asset/Probes/test_asset_preview.cpp` (PreviewTerrain) and
  `UI/Map/test_map_legend_localized.cpp` are reference.
- **campaign:** almost everything is probes (§4.4). References: `World/test_world_serialization.cpp` (`enableRadio false` and
  `disableAI` were lost on save/load, so generated scripts should re-assert them) and `World/test_gamestate_vars_roundtrip.cpp`.
- **platform-paths:**
  - Port: `Foundation/Common/test_gamePaths.cpp` (CWR user-content layout vs the legacy `-oldpaths` layout),
    `Platform/test_gameDirs.cpp` (`Missions` vs lowercase `missions/`; the `MPMissions/__cur_mp.` prefix),
    `Core/test_profile_manager.cpp` (profile name rules), `Core/test_mod_collection.cpp` (`-mod=` parsing, order) and
    `Audio/test_voice_lang_path.cpp`.
  - Three mission-root layouts exist: CWR/CE default (`<UserContentDir>/missions`), CWR/CE `-oldpaths`, and 1.99 per-profile
    `Users/<name>/missions` [U].
- **preview-harness:** the Trident client tests (`config`, `protocol/types`, `client/connection`, `client/instance`,
  `scenarios/integration` runner and script parsing), `Core/test_user_config_serialization.cpp` and the `cfg/*` fixtures.
  `Foundation/Platform/test_launch_diagnostics.cpp` is reference, but it is why we need **separate 1.99 and CWR argument builders**.
  CWR bundles short options (`-abc` means `-a bc`) and normalizes only `-nosplash`, `-mod=`, `-nomap` and `-oldpaths`.
- **formats-p3d and formats-audio (deferred):** port `test_mlod_loader`, `test_format_detector`, the proxy-name case and the
  shape-loader fuzz regressions only if we read models. **Never port the dead P3D goldens** (19 LODs, 2,617 points, `velka vrtule`),
  which were taken from a real game model. Port the WAV/WSS loader tests only with a sound preview.

## 4. The integration runner and our preview/probe harness

### 4.1 How `tri` launches and judges a test [V]

1. **Binary discovery.** It looks for `PoseidonGame[.exe]` or `OFPR[.exe]` in the game dir, then in `bin/`, then in sibling dirs.
2. **Client arguments.** `--harness 0 [-C <data_dir>] --window --no-splash [--autotest] --lang English [--test-mission <abs>]
   [--test-type X] --strict <extra_args> <--game-arg ...>`.
3. **Isolation.** `POSEIDON_USER_DIR`, `POSEIDON_CACHE_DIR` and `POSEIDON_TEMP_DIR` point at a fresh tempdir (shared across the
   phases of a `.seq`). `kill_on_drop` is set, and stdin is null.
4. **Connection.** It reads stdout until `HARNESS_PORT=N`, then connects to `127.0.0.1:N`, retrying, and bails out if the process has
   exited.
5. **Wire protocol v1.** NDJSON over loopback (`engine/Trident/protocol/harness.schema.json`): `ping, describe, key, key_up, click,
   query, screenshot, wait_display, eval, exec, http_fixture, exit`, with events `ready, display, log, mission_state, ...`.
   docs/research/08 found that `click` and `wait_display` are not registered by `PoseidonGame`.
6. **Script execution.** The runner expands `#include` itself, splits statements (strings and `{}` blocks kept whole; parentheses and
   `/* */` are not tracked), waits for `ready` and the main menu, and polls `triMissionPlayerReady` when a mission is set. It sends
   one `eval` per statement. **Only `triAssert*` statements or results starting with `FAIL:` can fail a step**; a bare `false`
   passes.
7. **Pass rule.** The test passes when the game exits 0 within the timeout. Exit codes: 1 is a boot failure under `--check`,
   2 is a script error under `--autotest`, 3 is a logged error under `--strict`, and 44 means an unresolved `--test-mission`. On
   failure it sends `triEndTest`, waits 500 ms, then kills; retries go to `retry-N/`; sharding is LPT bin-packing by timeout.

### 4.2 Reuse verdict

- **CE (and CWR) builds: reuse.** `HarnessServer` is compiled into every build. `--harness`, `--test-mission`, `--autotest`,
  `--check` and `--test-type` are accepted by release builds (only `--dev` is rejected, `AppConfig.cpp:287`). The roughly 375 `tri*`
  commands register under `--harness` or `--test-mission` (`GameStateExtTestAudio.cpp:2993` in CE). Our Preview can launch
  `<CE exe> --harness 0 --window --no-splash -C <data> --test-mission <missionDir>`, read `HARNESS_PORT` and speak NDJSON. It can
  mirror the Trident client in Rust (porting its tests, §3.7) or shell out to an unmodified `tri`. **Keep the `.test.sqf` +
  `.toml` layout**, so our probes also run under upstream `tri`.
- **Useful CE modes to expose:**
  - `--check --test-mission <dir>`: a fast "does it load in the real game" check. It exits 0 once the mission runtime is entered.
  - `--test-type screenshot` / `--auto-screenshot`: mission thumbnails.
  - `triGetEndMode`, `triEndMission end1..end6`, `triCheatUnlockCampaign`, `triSaveGame`/`triLoadGame`, `triSetActiveProfile`:
    ending and campaign probes.
- **CWA 1.99: nothing carries over.** It has no harness, no `--test-mission`, no `tri*` commands and no `HARNESS_PORT`. One lead is
  unverified on the real binary: a positional `.sqm` argument opens that mission in the in-game editor, or auto-runs it under AutoTest
  (`WorldImpl.cpp:2222-2256`; docs/research/08 reports conflicting community evidence).

### 4.3 Pitfalls to fix in our runner

- **Mission-dir mode cannot tell endings apart.** Under AutoTest, *any* mission end (end1-6, lost, killed) quits with exit 0
  (`DisplayUIMenus.cpp:966-1006`). Ending probes must use a `.test.sqf` with a `mission=` sidecar and assert through the harness
  (`triGetEndMode`) before the end.
- **Manifests:** deserialize with `deny_unknown_fields` and make a parse error fail the test, because a typo in `mission=` silently
  runs a menu-only test upstream.
- **Assertions:** treat a `false` result of an assertion-shaped probe line as a failure, or require an explicit `OK`/`FAIL:`
  protocol.
- **Strict mode:** `tri` passes `--strict` (any logged error gives exit 3). User Previews must not; CE CI already passes
  `--no-strict`.
- **Port allocation:** always use `--harness 0` and port discovery. `tri exec` and `tri console` share the fixed port 9100.
- **Windows:** the Trident process tests are `#[cfg(unix)]` with `/proc`. Our launcher needs Windows liveness and kill-on-drop
  (for example a Job Object with `KILL_ON_JOB_CLOSE`).

### 4.4 The CWA 1.99 probe suite

The campaign compiler, the linter's hazard rules and the `unverified-1.99` goldens all rest on engine behavior that has only been
read in the remastered source. We therefore need a **probe suite** of small synthetic missions and campaigns, each with a machine-
or human-checkable expected outcome. It has two backends:

- **CE backend (automated):** the Trident protocol, with `tri*` assertions allowed.
- **1.99 backend:** plain SQF/SQS only. The observable channels are an open question (§Open questions). Candidates: the ending
  chosen, as seen by the next campaign mission; campaign `saveVar` state; screenshots plus a checklist.

**Probe backlog**, taken from the CSV `probe` rows and from source-derived oracles:

| Area | Probe | Upstream seed |
| --- | --- | --- |
| campaign | Variable-guarded END trigger fires; an unmet guard never ends; a mid-chain entry still resolves; player death vs ending guards | `flows/demo/demo_end_*` (re-author with neutral names) |
| campaign | Each `endN` shows only its `Debriefing:EndN` section | `ui/debriefing/campaign_result_current_section` + `tri_debrief.pbo` |
| campaign | Campaign-table title resolves from the **campaign** stringtable | `ui/campaign/campaign_table_mission_title` (CE) |
| campaign | `saveStatus`/`loadStatus` survive restarts, inside and outside a campaign | `multiplayer/crcti_status_persist.seq` |
| campaign | Campaign sounds resolve under `<campaign>/dtaExt/`, mission sounds under the mission dir | `Audio/test_campaign_sound_voice_suffix.cpp` |
| campaign | `enableRadio false` and `disableAI` after save/load | `World/test_world_serialization.cpp` |
| mission-model | Init order: object init fields before `init.sqs`; an `expCond="true"` trigger fires at simulation start | `multiplayer/dedicated_init_order_probe` (single-player rebuild) |
| mission-model | `objStatus` values of `OBJ_<name>` (ACTIVE, DONE, FAILED, HIDDEN) | `multiplayer/objective_status_dedicated` |
| mission-model | Trigger `timeoutMin/Mid/Max` and `interruptable` | `flows/demo/demo_end_tail_stay_in_uh_bum` |
| mission-model | Which briefing file and codepage is shown per language | `ui/briefing/briefing_encoding` |
| script-lang | One batch run of every `unverified-1.99` evaluator golden (error codes, nil, `%g`) | §3.3 |
| script-lang | `format` output of 2,048+ chars; negative `resize`; 256-element arrays; `~` expressions longer than 256 bytes | `scripting/format_long_no_overflow`, `test_evaluator_edge` |
| script-lang | Lower-case event names fire; `camCreate` of `Logic`/`Camera`; `setDamage`/`logInfo` exist; a global named like a command | `scripting/*`, `test_evaluator_nulars` |
| editor-core | The 1.99 editor Load list shows a mission our editor saved; non-ASCII folder names; `advancedEditor` default | `smoke/editor_mission_folder`, `editor_mission_save_unicode_name` |
| editor-core | A placeable `scope=2` class with `model=""` (our own synthetic addon) | `scripting/create_vehicle_empty_model` |
| preview-harness | A mission launched via Preview reaches gameplay and `briefingName` is localized | `flows/demo/mission_load` |

## 5. Fixtures: provenance, licensing and the synthetic-fixture strategy

- **License.** Both repos are GPL-3.0-or-later plus Bohemia's section 7 terms (`LICENSE:682-721`). The terms require carrying the
  notice, marking modified versions and using no BI/OFP trademarks. docs/research/02 adopts the same license with a NOTICE file, so
  reusing upstream tests and fixtures raises no license question. **Nothing CWR-derived may go into a permissive crate.**
- **Policy.** `tests/fixtures/ASSET_SOURCES.md` (identical in CE) requires fixtures to be repo-authored or trivially synthetic and
  not to preserve original asset identities. It is a policy, not a per-file record, and it **covers only `tests/fixtures`**. Media
  under `tests/integration/**` and `tests/unit/**/fixtures` must be judged file by file.
- **Copy with attribution** (small synthetic text or bytes): `pbo/*`, `config/*`, `stringtable/*`, `evaluator/**`, `font/legacy.fxy`,
  `paa/*` and `pac/*`, `mods-campaigns/*` PBOs, `mods-nordicnames` config, `missions/*`, `tests/integration/missions/*.Demo` text
  (except the `demo_end_*` chain), the MP mission text and stored synthetic PBOs, and `tests/fixtures/studio/*`.
- **Regenerate instead of copying:** `wrp/test_world.wrp` (port `generate_test_world.py`), the stringtable encoding fixtures
  (`generate_encoding_fixtures.py`), `p3d/animated_morph_odol.p3d`, and all PBO/PAA fixtures. For those, keep the upstream bytes as
  cross-implementation goldens and have our writers reproduce them.
- **Re-author with neutral names:** the `demo_end_*` missions. They reproduce the stock Demo mission's ending chain (trigger texts
  StartScenario, BUM, Vyskakali, StartOutro, `Konec E1`; variables Konec, Ukonci, uplkonec; Demo-island coordinates). Also retarget
  every `.Demo` mission to a 1.99 island (Noe, Eden, Abel, Cain, Intro) for probes, and rename CWR-only `*.utf8.html` and
  `stringtable.utf8.csv` files.
- **Do not copy:**
  - `tests/fixtures/savegame/save.fps` (a real Eden save with game identities, unreferenced).
  - The photographic `face.jpg` files in `multiplayer/custom_face_hosted_visual` and `custom_face_visual`.
  - `custom_face_restart_respawn/face.paa`, the 48 KB `tri_mp_ping.wav`/`tri_profile_ping.wav` and `ingame/custom_profile_media`
    media (no provenance).
  - `audio/voice-lang/*.lip` (a comment claims a demo origin).
  - The absent `s03r04.ogg`/`s07r01.ogg` (scrubbed campaign voice lines; never source them).
  - `mods-stress`/`mods-faguss` (LFS, absent, possibly third-party).
  - Everything under `packages/` (BI game data) and the Demo zip that CE CI downloads.
- **Game-derived values in source.** The dead `Asset/Formats/P3D/**` tests hard-code a real model's numbers, and the `test_rtm`
  titles name original animations. Do not port either.
- **Synthetic gaps to author ourselves:** a PBO with a `Vers` header and a `prefix` property; PAA files with TAGG blocks (AVGC,
  MAXC, FLAG, OFFS) and a palette; a truly palettised PAC; a legacy-codepage `stringtable.csv`; a minimal vanilla campaign (model:
  `tri_campname.pbo`: `MissionDefault` with empty `end1 = ;`..`lost = ;`, `Campaign > Test > CampName: MissionDefault`).
- **Opt-in corpus tests** (the `[gamescan]` equivalents) read the user's local CWA 1.99 or CWR install through an environment
  variable. They never commit or upload data, and they skip when the variable is unset.

## 6. CE vs CWR delta

- **Size.** Over `tests/`, `engine/Trident`, `mserver` and `apps/fuzzers`, CE has 132 changed files (62 added, 69 modified,
  1 removed). The fuzzers, e2e, smoke, stress and perf directories are identical.
  - Catch2: **+88 cases**, 47 of them in 13 new files and a net +41 in 41 modified files; 10 case names removed or renamed.
  - Rust: +13 tests.
  - Integration: +11 tests.
  - In the CSV: 22 `ce-only` rows (`upstream_repo` = CE) and 69 `both-modified` rows.
- **CE-only additions that matter to us:**
  - The signed PAA LZSS checksum (`test_pactext`).
  - UTF-8 PBO entry names (`test_mod_archive`).
  - Legacy folder-name decoding (`test_codepage_transcode`).
  - A missing `#include` logged at error level (`test_preprocC`).
  - A path longer than 512 bytes (`test_paramfile_parsing`).
  - A mod path escaping its prefix (`test_qstream_path_resolution`).
  - Empty stringtable cells falling back to English (`test_stringtable_encoding`).
  - Cursor layout and HTML table rows.
  - `endGame`/`triEndGame` not registered as nulars (`test_game_state_ext`).
  - The `campaign_table_mission_title` fixture, Unicode-named SP missions and MP mission folders.
- **Rule:** a CE-only test documents *CE* behavior, not 1.99 behavior. Where CE changed a rule (the empty-cell fallback, UTF-8
  names, cursor squareness), port the inputs, keep the rule behind a target switch, and let a 1.99 probe decide the default.
- **Counts:** `test_cases` holds the **CE** count for both-modified files; `subject` gives the CWR count where it differs. A ported
  test cites the repo and SHA it was translated from; prefer CE for both-modified files and cite CWR too when behavior is identical.
- **Only CE has CI**, and only its integration directory and cargo tests actually run. Treat the rest as design reference.

## 7. Keeping the CSV current

`docs/porting/upstream-test-map.csv` implements the AGENTS.md rule "Porting Upstream Code and Tests (Required)".

- **Format:** UTF-8 without BOM, LF, one physical line per row (no embedded newlines), RFC 4180 quoting only where a field contains a
  comma or quote. Header, exactly:
  `upstream_repo,upstream_path,exists_in,test_cases,subject,relevance,target_area,status,fixture_notes,rationale`.
  Rows are sorted by `target_area`, then `upstream_path`.
- **Keys:** `(upstream_repo, upstream_path)`. A row is a file, a glob of fixture or infrastructure files, or a `file#section` group
  when one file splits across relevance classes (Trident `integration.rs#runner`/`#script`, the Studio groups). Split a row further
  only when its parts get different statuses.
- **Allowed values:**
  - `exists_in`: `both`, `both-modified`, `ce-only` or `cwr-only`. `upstream_repo` is CE exactly when `exists_in` is `ce-only`.
  - `relevance` and `target_area`: the classes and tags used in this doc.
  - `status`: port-now and port-with-module rows start as `todo`; adapt-as-probe starts as `probe`; reference as `reference`;
    not-applicable as `not-applicable`.
- **Workflow:**
  - **When you port a file**, in the same change set: set `status` to `ported` (same inputs and outputs) or `adapted` (inputs kept,
    expectations re-derived or cases re-authored, e.g. the mistyped `call` case). Append the Rust test path to `rationale`
    (`ported as: <crate>/tests/<file>.rs`). Give every ported test a doc comment citing repo, SHA, path and `TEST_CASE` name.
  - **When a probe lands:** keep `status = probe` and append its probe path and the 1.99/CE verdict to `rationale`. If a probe
    contradicts a source-derived golden, fix the golden and record the difference.
  - **When relevance changes** (for example, we decide to read P3D): update `relevance`, `status` and the reason in the same PR.
- **Refreshing to a new upstream SHA:** diff `tests/`, `engine/Trident`, `mserver` and `apps/fuzzers` between the old and new pins.
  Add rows for new files, and recount modified files with PowerShell, e.g.
  `(Select-String -Path <file> -Pattern '^\s*TEST_CASE').Count` for Catch2, `'#\[(tokio::)?test\]'` for Rust and `'^\s*It '` for
  Pester. Integration tests and fuzz targets count as 1 each. Check the CMake source lists for newly dead or revived files, then
  update the pinned SHA in the `upstream_repo` column and in this doc.
- **Validation:** a small CI check can parse the CSV and enforce the value sets, the status mapping, the repo/`exists_in` rule,
  unique keys and the sort order. It should also check that every `ported`/`adapted` row names an existing test file.

## Open questions

1. **How do 1.99 probes report results?** CWA 1.99 has no file I/O or harness. Which observable channels are reliable (campaign
   `saveVar`/`.sqc` state, the ending seen by the next campaign mission, screenshots with a manual checklist) [U]? This decides
   whether the 1.99 suite can be automated at all.
2. **Which dialect table is canonical for script-lang?** CWR's engine table includes post-1.99 commands (docs/research/19 F5:
   `find`, `for`, `exitWith`, `resize`, `parseSimpleArray`). A `cwa199-verified` table can only be built by probing 1.99 [U].
3. **Should Preview and probes depend on CE's harness long-term,** or treat CE as a development oracle only? The answer affects
   whether the Trident client tests are port-with-module or reference.
4. **Is the CE CI Demo-assets mirror** (`files.ofpisnotdead.com/CWR-demo-assets-v2.zip`) acceptable for our own CI? Its terms are
   unconfirmed, and it is BI data under APL-SA.
5. **Does `dummy.ttf` need separate font licensing?** It is FontForge output, Copyright 2026 Josef Šimánek, with no font license
   file. Otherwise we author our own.
6. **Protocol drift:** `types.rs` serializes `click` and `wait_display`, which docs/research/08 found unregistered in `PoseidonGame`.
   Confirm on a CE build before porting those cases as live commands.
7. **Where should "our test location" be recorded?** Should the CSV gain an `our_tests` column once the first crates exist, instead
   of appending paths to `rationale`?
8. **What should the opt-in game-data environment variable be called,** and should the corpus tests accept both 1.99 and CE
   installs?
9. **Is formats-p3d in scope at all** (map footprints, icons)? The answer decides 30 rows.
10. **Is the 1.99 editor mission root `Users/<profile>/missions`?** And what is the `advancedEditor` default there [U]?

## Sources

- Pinned upstream: `BohemiaInteractive/CWR@ffc61838b7`, `ofpisnotdead-com/CWR-CE@b67bf3bd62`. Row-level citations are in
  `docs/porting/upstream-test-map.csv`.
- Test trees: `tests/unit/engine/Evaluator/*`, `tests/unit/apps/{Evaluator,Server,Studio,Tetris}/*`, `tests/unit/engine/Random/*`,
  `tests/unit/engine/Poseidon/{AI,Asset,Audio,BinaryFormats,Core,Dev,Foundation,Game,Graphics,Input,IO,Network,Platform,Support,
  TcPbo,Tools,UI,World}/**`, `tests/integration/**`, `tests/{e2e,smoke,stress,perf,fixtures}/**`, `tests/README.md`,
  `apps/fuzzers/Fuzzer/*`, `engine/Trident/src/**`, `engine/Trident/protocol/harness.schema.json` and `mserver/**`.
- Build and CI: `tests/unit/engine/Poseidon/CMakeLists.txt`, `tests/unit/apps/Evaluator/CMakeLists.txt`,
  `cmake/{CatchWindowsSafe,TridentCTest,RunTridentCTest}.cmake`, `cmake/presets/sanitizers.json`, and (CE only)
  `.github/workflows/{build,rust,lint,pch}.yml` and `.github/actions/*`.
- Engine sources cited for oracles:
  - `engine/Evaluator/{express.cpp,express.hpp,EvalState.cpp,SqsRunner.cpp}`
  - `engine/Poseidon/Game/Commands/{GameStateExt.cpp,GameStateExtWorld.cpp,GameStateExtUi.cpp}`
  - `engine/Poseidon/Game/Scripting/Scripts.cpp`
  - `engine/Poseidon/UI/Map/{UIArcade.cpp,UIArcadeWaypoint.cpp,UIMapExtDisplay.cpp}`
  - `engine/Poseidon/AI/ArcadeTemplate.cpp`
  - `engine/Poseidon/IO/Streams/SsCompress.cpp`
  - `engine/Poseidon/IO/ParamFile/ParamFileEval.cpp`
  - `engine/Poseidon/Foundation/Platform/AppConfig.cpp`
  - `engine/Poseidon/Foundation/Common/GamePaths.cpp`
  - `apps/cwr/Game/GameApplication.cpp`
  - CE `engine/Poseidon/Game/Commands/GameStateExtTestAudio.cpp`
- Policy and license: `tests/fixtures/ASSET_SOURCES.md` and `LICENSE` (section 7 terms at lines 682-721), in both repos.
- Project docs: `AGENTS.md` ("Porting Upstream Code and Tests"), `docs/research/02-licensing-and-trademarks.md`,
  `docs/research/07-file-formats-and-rust-crates.md`, `docs/research/08-mission-preview-and-game-integration.md`,
  `docs/research/18-campaign-system-in-engine.md`, `docs/research/19-campaign-designer-ux-and-state-model.md` and
  `docs/research/23-script-tooling-lsp-and-linter.md`.
