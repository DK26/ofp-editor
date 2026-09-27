# Script command risk audit: the engine's script surface and the Preview harness

> Research note 24 for `ofp-editor`, a standalone Rust re-implementation of the *Arma: Cold War Assault* /
> *Operation Flashpoint* mission editor with Preview, a campaign designer and an opt-in, product-scoped AI co-pilot.
> Written 2026-09-26. **Question:** which SQF/SQS commands and harness verbs reach beyond the running mission, and what
> may our linter, our AI co-pilot and our Preview harness allow? Companion data:
> [`data/script-command-risk.csv`](data/script-command-risk.csv) (111 rows, full citations). Fact-checked and corrected
> 2026-09-27; see [Verification notes](#verification-notes-2026-09-27). The consolidation pass the same day added doc
> 35's 1.99 evidence (§3.9) and finding F10.

**Epistemic legend.** **[V]** checked against the cited file by static reading (nothing was built or run, so "[V]"
never means "observed at runtime"). **[I]** our inference or recommendation. **[U]** unknown or unverified.

**Citation aliases** expand mechanically to `owner/repo@sha:`: `CWR:` = `BohemiaInteractive/CWR@ffc61838b7:`,
`CE:` = `ofpisnotdead-com/CWR-CE@b67bf3bd62:`, `DK:` = `DK26/CWR@6fd6ca3974:`. A `CWR:` citation also holds for CE
unless a CE citation is given: every audited file was compared between the two trees, and the differences are listed in
§3.9. In `GameStateExt.cpp`, CE line numbers are one lower from L399 and two lower after L886 (CE dropped the
`endGame` declaration and table row).

> **Disclosure note [I].** Findings F1, F3, F4, F9 and H2–H4 below can be used by a downloaded mission (or by anything
> that reaches a harness port) against players of the shipping game, not only against our Preview. Neither source
> snapshot has a `SECURITY.md` [V]. Before this note is merged into our public repository, the owner should report
> them privately to the CWR-CE maintainers and to Bohemia Interactive. This note deliberately contains no exploit
> strings. (Answered 2026-09-27 → [D035](../decisions/D035-outreach-and-security-disclosure.md) item 1, OWQ-09 (a): the
> owner reports privately through a private channel of each project and records the dates in OWQ-09; no new public
> detail is added until the reports are acknowledged. Nothing has been sent yet.)

---

## TL;DR

- **The engine has no script sandbox [V].** Commands run with the game process's full rights. Script file lookups are
  not confined: `loadFile`, `preprocessFile` and `exec` append the name to the mission folder with no `..` check,
  `loadFile` and `exec` open a name starting with `\` as given, and `#include` inside `preprocessFile` opens its name
  as given
  (`CWR:engine/Poseidon/Game/Scripting/Scripts.cpp#L126-L150`, `CWR:engine/Poseidon/UI/OptionsUI.cpp#L630-L655`).
  Any user-readable file can be loaded into a mission variable [I].
- **Any mission can make HTTP requests [V code; I linkage].** `triHttpGet` (GET of any URL, up to 64 KiB of the reply
  returned to the script) and 55 other test verbs are registered by two `INIT_MODULE`s **with no gate**
  (`CWR:engine/Poseidon/Game/Commands/GameStateExtTestGeneric.cpp#L416-L456`, `…GameStateExtTestGetters.cpp#L534-L588`).
  The upstream gate test (identical in both trees) guards only the gated module. Combined with the previous point this
  is a read-and-send channel in every run of the game. On non-Windows builds the libcurl call sets no protocol limit,
  so `file://` or `gopher://` URLs may also work (unverified).
- **Our Preview mode widens the surface [V].** `--test-mission` or `--harness` registers about 300 more `tri*` verbs,
  and the mission's own scripts can call them. They include a debug console that also runs SQF (`triConsoleRun`), file
  writes with unsanitised names (`triSaveGame`, `triScreenshot`), a recursive "make read-only" that takes an
  unvalidated directory name (`triMakeProfileReadOnly`), persistent settings changes (`triSetActiveProfile`), MP admin
  chat commands (`triNetCommand`) and synthetic input. CE adds `triDownloadFile` (any URL).
- **Arbitrary file write on servers [V].** `saveMission`/`loadMission` hand the script string straight to `fopen` on
  a server (`CWR:engine/Poseidon/Network/NetworkServerMission.cpp#L1123-L1136`). This matters for hosted MP and for
  our MP Preview (doc 08 option 5).
- **The mission sets who may `remoteExec`, and the name may be an engine command [V code; I impact] (F9, added
  2026-09-27).** A receiver runs `<name> _this` when no global function has that name, so any unary command is
  callable. A mission's `description.ext` `CfgRemoteExec` with `mode = 2` lets every client do this on the server and
  on other clients, for example `saveMission` on the server.
- **Process exit from a script [V].** In CWR, `endGame` quits the game. CE renamed it `triEndGame` and gated it, and
  the 1.99 executable does not contain the name (doc 35 §8.2), so the command is CWR-only.
- **Mission files are code sinks too [V code; I impact] (F10, added by the consolidation pass).** A non-literal numeric
  value in `mission.sqm`, `description.ext` or another config is evaluated as a script expression at load (doc 35
  §5.8), so the linter must check those fields as code.
- **The harness is "local code execution for whoever reaches the port" [V].** It binds loopback, has no
  authentication, serves one client at a time, has no line-length cap and skips non-JSON lines, so a JSON line inside
  an HTTP request body would be processed [I]. Besides `eval`/`exec` it offers `screenshot{path}` (any path),
  `query{what:"download"}` (any URL to any path), `query{what:"mp_join"}` and `http_fixture`, whose loopback check is
  a prefix match [V] that a `user@host` URL would pass [I].
- **Policy [I]:** (a) the linter denies test, debug, compiled-out and server file verbs and path escapes, and warns on
  code it cannot see into; (b) AI-proposed script text passes the same host-enforced policy, is never auto-executed,
  and may use only mission-scoped commands; (c) Preview sends only a fixed allowlist of harness verbs, `eval`/`exec`
  only from typed templates or user-typed console text that passed lint, and treats all output as untrusted data.
- **Catalog implication [V/I].** Our per-dialect command catalog needs a *registration gate* and *capability tags* per
  entry. The owner's fork `DK26/CWR` has an extracted catalog that skips `*Test*` and `*Tri*` files, so it misses
  `triHttpGet`, and lists the compiled-out `DBG_*` and `diag_*` commands
  (`DK:lsp/crates/poseidon-catalog/tests/completeness.rs#L24-L37`, `DK:lsp/crates/poseidon-catalog/data/commands.json#L1693-L1853`).
  Correction 2026-09-27: `diag_drawmode`/`diag_toggle`/`diag_enable` are compiled out, not always registered (§2).
- **Upstream hardening (§6):** nine small CE patches, with hook points and tests.

## 1. Scope and threat model

**In scope.** Every script command the game registers; the harness protocol (doc 08 §2.5); how both interact with our
Preview (doc 08 §4.2, §4.4), our linter, our AI co-pilot (AGENTS.md: "Untrusted content") and the target-profile
"Requires" badge.

| Actor | Capability | Why it matters to us |
| --- | --- | --- |
| A. Author of a downloaded community mission | Arbitrary SQS/SQF in `init.sqs`, triggers, waypoints, dialogs, scripts (entry points: doc 04 §8) | Preview runs it in the real game with the user's rights |
| B. Our AI co-pilot | Proposes script text; can be steered by text inside a mission (prompt injection) | Its output must be gated by the host, not by the model |
| C. Other local users, and web pages in the user's browser | Can open TCP connections to `127.0.0.1` | The harness has no authentication |
| D. MP peers | Send `publicVariable`/`remoteExec`/`publicExec` traffic | Only in MP Preview (doc 08 option 5) |

**Out of scope.** Malware already running as the same user (it can do anything the game can); memory-safety bugs in
file parsers (covered by fuzzing requirements in AGENTS.md); the legacy 1.99 executable's internals (no source).

## 2. Method and registration sites

1. Found every registration site in both trees by searching all `.cpp/.hpp/.h` files for
   `New(Functions|Operators|NularOps|Function|Operator|NularOp)(` and `Game(Nular|Function|Operator)(…, "name"`,
   excluding `tests/`. Registration happens through `INIT_MODULE` static registrars, which run for every translation
   unit that is linked (`CWR:engine/Poseidon/Foundation/Modules/Modules.hpp#L29-L39`).
2. Read the gate (if any) around each site, then the handler of every command whose name or handler suggests file,
   network, process, persistence, UI, debug or test behaviour, following helpers (`FindScript`, `OpenScript`,
   `QIFStreamB`, `SaveWorldState`, `DownloadFile`, `ProfileManager`, harness builtins).
3. Compared each audited file between CWR and CE (`fc`), and CE's `GameStateExtTestAudio.cpp` registrations line by
   line.
4. Reused doc 04 (script entry points), doc 08 (flags, harness), doc 14 (dialects) and doc 18 (campaign persistence).
   The BI community wiki returned HTTP 403 to every fetch, so 1.99 availability is inferred, not verified (§3.9).
   Consolidation pass 2026-09-27: doc 35 §8 has since supplied content observations and a 1.99 executable string scan
   for many of these commands (§3.9).

| Site | Lines matching the registration pattern (CWR / CE) | Registered into | Gate |
| --- | --- | --- | --- |
| `engine/Evaluator/express.cpp#L1098-L1219` (core operators, `call`, `if`/`while`/`for`) | 73 / 73 | game `GGameState` | always |
| `engine/Poseidon/Game/Commands/GameStateExt.cpp#L853-L1503` (`ExtNular`/`ExtUnary`/`ExtBinary`) | 473 / 472 (incl. 4 `TABLE_COMMAND` macro lines) | `GGameState` | always; `DBG_*` compiled out (`_ENABLE_CHEATS` is 0, `CWR:engine/Poseidon/Foundation/PoseidonPCH.hpp#L44`) |
| `engine/Poseidon/World/Scene/SceneDraw.cpp#L541-L553` (`diag_*`) | 3 / 3 | `GGameState` | **compiled out**: the whole block is inside `#if _ENABLE_CHEATS` (`CWR:…SceneDraw.cpp#L469-L555`, `CE:…#L596-L682`); corrected 2026-09-27, was "always" |
| `engine/Poseidon/Game/Commands/GameStateExtTestAudio.cpp` `INIT_MODULE(GameStateExtTest)` | 315 / 320 | `GGameState` | `--dev` or `--harness` or `--test-mission` (`CWR:…#L2960-L2964`, `CE:…#L2990-L2994`); `--dev` is rejected in release builds (`CWR:tests/unit/engine/Poseidon/Dev/Debug/test_dev_mode_gates.cpp#L105-L127`) |
| `engine/Poseidon/Game/Commands/GameStateExtTestGeneric.cpp#L437-L456` | 17 / 17 | `GGameState` | **none** |
| `engine/Poseidon/Game/Commands/GameStateExtTestGetters.cpp#L534-L588` | 39 / 39 | `GGameState` | **none** |
| `engine/Poseidon/Game/Commands/GameStateExtServerTest.cpp#L90-L98` | 6 / 6 | server `GGameState` | same three flags (`CWR:apps/cwr/Server/ServerApplication.cpp#L171-L174`) |
| `engine/Evaluator/EvalState.cpp#L186-L764` | 72 / 72 | a separate `EvalState` instance (the `PoseidonEvaluator` tool), not the game | n/a |

Not script commands, but reachable from scripts: the debug-console registry (`CWR:engine/Poseidon/Dev/Debug/DebugCheats.cpp#L735-L780`,
reached through `triConsoleRun`) and the harness command registry (§4). Not script commands, but mission content that
changes what scripts can reach: `description.ext` `CfgRemoteExec` (F9), `#include` in any config the engine
preprocesses (F3), and non-literal numeric values in configs and `mission.sqm`, which are evaluated at load (F10).

Re-check 2026-09-27 [V]: a search of both trees for `GameNular`/`GameFunction`/`GameOperator`,
`GGameState.New*` and `->New*` found no registration site outside the rows above (tests excluded); the only
conditionally compiled registrations are `DBG_*` and `diag_*`. The CWR/CE name diff is exactly `endGame` (CWR only) and
`triEndGame`, `triDownloadFile`, `triScenePreloadCount`, `triDetailTextureLoads`, `triMapWheel` (CE only).
The dedicated server's `GameStateExtServerTest.cpp` references `TriAssertEq`, which is defined in
`GameStateExtTestGeneric.cpp` (`CWR:…GameStateExtServerTest.cpp#L84-L98`), so the unconditional Generic module is
probably linked into the server too (unverified).

## 3. Findings

### 3.1 Cross-cutting findings

**F1. Unconditional test verbs, including network egress [V code; I linkage].** `INIT_MODULE(GameStateExtTestGeneric)`
and `INIT_MODULE(GameStateExtTestGetters)` register with no flag check
(`CWR:engine/Poseidon/Game/Commands/GameStateExtTestGeneric.cpp#L437-L456`, `…GameStateExtTestGetters.cpp#L534-L588`).
Both translation units are forced into the link by calls placed in the gated module's body
(`…GameStateExtTestAudio.cpp#L287-L288`, `#L3313-L3314`); a function call referenced anywhere links the unit even if
that code path never runs [I]. Among them, `triHttpGet` downloads any URL and returns up to 64 KiB to the script
(`…GameStateExtTestGeneric.cpp#L416-L430`). Non-Windows builds use libcurl with redirects on and no protocol
restriction (`CWR:engine/Poseidon/Network/XML/Xml.cpp#L80-L117`, `#L994-L1005`); Windows builds use WinINet
`InternetOpenUrlA` (`#L940-L990`, `#L291-L297`).
Whether WinINet attaches the user's stored cookies here is **[U]**; the call passes only
`INTERNET_FLAG_NO_UI | INTERNET_FLAG_RELOAD`, so WinINet's default cookie and redirect handling applies [V flags; U
effect]. On Windows a URL longer than 255 characters fails `InternetCanonicalizeUrlA` into a 256-byte buffer
(`CWR:engine/Poseidon/Network/XML/Xml.cpp#L266-L280`), which bounds how much one request can carry in its query string
[V]. The curl path sets no `CURLOPT_PROTOCOLS`, so `file://` (local read) or `gopher://` (raw bytes to any TCP port)
URLs may work if the linked libcurl enables those protocols; `vcpkg.json` asks for curl with `ssl` and default
features (unverified which protocols that enables). The gate test, identical in both trees, checks only the gated
module (`CWR:tests/unit/engine/Poseidon/Dev/Debug/test_dev_mode_gates.cpp#L43-L83`). A harmless runtime probe is
listed in §7.

**F2. Preview flags expose test verbs to the mission's own scripts [V].** Doc 08 recommends
`--test-mission` and optionally `--harness 0`. Either flag registers the whole gated `tri*` set into the same global
evaluator that runs mission scripts. Risky members (full list in the CSV):

- `triConsoleRun`: dispatches debug-console commands (`save`, `load`, `unlockcampaign`, `god`, `endmission`, …) or,
  failing that, evaluates the line as SQF (`CWR:…GameStateExtTestAudio.cpp#L1273-L1298`, `…DebugCheats.cpp#L735-L780`).
- Unsanitised names in file paths: `triSaveGame`/`triLoadGame` build `<tmp save dir>/<label>.fps` (`#L2797-L2830`);
  `triScreenshot` and `triShadowSceneDump` build `<TRI_OUTPUT_DIR>/…<label>` (default `/tmp/ofpr/tri-screenshots`,
  `CWR:engine/Poseidon/Game/Commands/GameStateExtTestRender.cpp#L225-L260`, `#L482-L497`).
- `triMakeProfileReadOnly` recursively clears write permission under `GetProfileDirPath(UserDir, name)`, which
  concatenates the name without validation (`…GameStateExtTestAudio.cpp#L1785-L1814`,
  `CWR:engine/Poseidon/Core/Profile/ProfileManager.cpp#L93-L96`; the validating `EnsureProfileDirectory` is not used).
- Persistence beyond the session: `triSetActiveProfile` rewrites the game settings file
  (`CWR:engine/Poseidon/UI/Settings/GameSettingsConfig.cpp#L311-L325`); `triCheatUnlockCampaign` writes a `.sqc` for
  every installed campaign (`…GameStateExtTestAudio.cpp#L1509-L1516`). Whether `triBindAction`, `triSetVolume`,
  `triSetLanguage` persist on exit is **[U]**.
- Network and MP: `triFetchWorkshopMods`; CE-only `triDownloadFile` (any URL, `CE:engine/Poseidon/Game/Commands/GameStateExtTest.cpp#L662-L682`);
  `triNetCommand` runs chat commands such as `#login`/`#kick` (`CWR:…GameStateExtServerTest.cpp#L43-L59`);
  `triMpAssignSelf*`, `triSideChat`, VoN verbs.
- Synthetic input (`triSendKey`, `triClick`, `triInvokeButton`, …) can drive any menu; process control (`triEndTest`,
  CE `triEndGame`, `triRemount`).
- Added 2026-09-27: `triFontTune` accepts an optional TTF path of any kind that the font renderers then load
  (`CE:…GameStateExtTestAudio.cpp#L2150-L2186`, `CWR:engine/Poseidon/Graphics/Rendering/Draw/Font.cpp#L99-L133`; the
  load step is inferred); `triCheatStorePosition` (and the console's `storepos`) overwrites the user's system clipboard
  (`CWR:engine/Poseidon/Dev/Debug/DebugCheats.cpp#L557-L619`); synthetic Ctrl+V into a mission dialog's edit control
  would paste the user's clipboard where `ctrlText` can read it (`CWR:engine/Poseidon/UI/Controls/UIControls.cpp#L1729-L1750`)
  [I]. `triScreenshot` prefixes the label with `NNN_`, so a `..` escape needs lexical path normalisation (Windows) or
  an existing prefix directory [I]; `triSaveGame` and `triShadowSceneDump` append the label directly.

**F3. Script file lookups escape the mission folder [V].** `FindScript` tries `mission dir + name`, then
`BaseDirectory + "scripts\" + name`, then `"scripts\" + name`, with no normalisation
(`CWR:engine/Poseidon/UI/OptionsUI.cpp#L630-L655`, `CE:…#L636-L661`). `OpenScript` opens `name` minus its first
character when it starts with `\` (`CWR:engine/Poseidon/Game/Scripting/Scripts.cpp#L126-L150`). `QIFStreamB` falls
back to a plain filesystem open (`CWR:engine/Poseidon/IO/Streams/QBStream.cpp#L1501-L1541`). `loadFile`
(`CWR:engine/Poseidon/Game/Commands/GameStateExtWorldConfig.cpp#L1050-L1058`), `exec` (`Scripts.cpp#L574-L580`) and
`preprocessFile` (`#L1081-L1091`, whose `#include` handler opens the raw name, `#L1063-L1072`) all use this path.
Correction 2026-09-27 [V]: `preprocessFile` calls `FindScript` directly rather than `OpenScript`, so the leading-`\`
rule does not apply to its own name (a `..` still escapes); absolute paths come in through its `#include` lines.
Whether a drive-letter path survives the leading-`\` rule on Windows is **[U]** until probed; a name that starts with
three backslashes leaves a UNC path after the first is stripped, which on Windows would make the game open an SMB
connection to the named host (unverified). The config preprocessor that `ParamFile` uses by default (so
`loadConfig` files and, we infer, `description.ext`) also tries each `#include` name raw before trying it relative to
the including file (`CWR:engine/Poseidon/IO/PreprocC/PreprocC.cpp#L28-L49`,
`CWR:engine/Poseidon/IO/ParamFile/ParamFileUsePreprocC.cpp#L11-L21`) [V code; I reach]. By contrast,
`triReadWorkshopFile` shows the confinement pattern we want upstream: reject `..` components and absolute paths
(`CE:engine/Poseidon/Game/Commands/GameStateExtTest.cpp#L637-L660`). The pattern is incomplete on Windows: a
drive-relative component such as `D:x` is not `is_absolute()`, and `std::filesystem` `operator/` replaces the base
path when the drive differs (unverified; a canonical-prefix check would close it).

**F4. `saveMission`/`loadMission` take a raw path on servers [V].** Both check only `IsServer()` and pass the string
to `NetworkServer::SaveWorldState`/`LoadWorldState`, which call `fopen(filename, "wb"/"rb")`
(`CWR:…GameStateExtWorldConfig.cpp#L920-L938`, `CWR:engine/Poseidon/Network/NetworkServerMission.cpp#L1123-L1180`,
`CE:…#L1135-L1192`). A mission running on a hosted or dedicated server can create or truncate any file the server
process may write. Precision added 2026-09-27 [V]: `saveMission` always writes the same 20-byte `JIPS` header, so it
clobbers rather than plants content; `loadMission` reads only that 20-byte header and, on a match, shifts the mission
start time (`CWR:…NetworkServerMission.cpp#L1167-L1214`), so it is a logged existence/format probe, not a content
read. Whether `IsServer()` is true in single-player Preview is **[U]**, probably false [I].

**F5. `endGame` quits the process in CWR [V].** It sets `GApp->m_closeRequest`
(`CWR:…GameStateExtWorld.cpp#L787-L803`, registered at `CWR:…GameStateExt.cpp#L886`). CE renamed the handler
`triEndGame` and moved its registration into the gated module (`CE:…GameStateExtTestAudio.cpp#L2996`). Under
`--test-mission`, `forceEnd` and any mission end also quit (doc 08 §2.4). Consolidation pass 2026-09-27: the name is
absent from the 1.99 executable (doc 35 §8.2 [V strings; I availability]), so of our targets only CWR has it. Doc 35
§5.9 and §8.4 add a name hazard: shipped missions use a global variable named `EndGame`, and the evaluator reads a set
variable before a nular command of the same name, so on CWR a read before the variable is set would run this command
[V code; I runtime; doc 35 open question 11].

**F6. Log lines are mission-controlled [V].** `logInfo` writes arbitrary text at INFO level (`CWR:…GameStateExtWorld.cpp#L769-L773`);
`textLog`/`debugLog` log in simulate mode (`#L749-L767`). Doc 08 maps Preview results partly by parsing the log
(`Script error at`, `AUTO-TEST SUCCESS`, `HARNESS_PORT=` on stdout). A mission can print those markers itself [I].

**F7. Deferred and dynamic code defeats static certification [V/I].** Code is a string: `call`, `exec`, `publicExec`,
`onPlayerConnected`, `buttonSetAction`, `onMapSingleClick`, `addEventHandler`, `setTriggerStatements`,
`setWaypointStatements` store or run strings (doc 04 §8), and `format`, `+` and `loadFile` build them at runtime.
A token scan cannot see a verb name assembled from pieces [I]. The linter can prove the *absence* of risky commands
only when every code sink receives a literal.

**F8. The engine's own check-only mode is side-effect free [V].** `CheckEvaluate`/`CheckExecute` set `_checkOnly`
(`CWR:engine/Evaluator/express.cpp#L3067-L3092`), and operator dispatch is skipped in that mode (`#L1316`; rechecked
2026-09-27: unary functions at `#L1390` and nulars at `#L195-L208` are skipped too, nulars returning a typed nil). The
original editor validated fields this way (doc 03). Our Rust checker (doc 23) should do the same: parse and
type-check, never call handlers. The upstream `EvalState` tool is not safe for untrusted input: its `exec` reads host files
(`CWR:engine/Evaluator/EvalState.cpp#L709-L732`).

**F9. `remoteExec` reaches engine commands, under a policy the mission sets [V code; I impact] (added 2026-09-27).**
The receiver of a `remoteExec`/`remoteExecCall` runs the global variable's string if the name holds one, and otherwise
executes `<name> _this` (`CWR:engine/Poseidon/Network/NetworkServerMsgOnMessage.cpp#L113-L132`; the client has an
identical copy, `CE:engine/Poseidon/Network/NetworkClientOnMessage.cpp#L226-L245`, called at `#L2416-L2424`). `WireBounds::ValidIdentifier` checks
only identifier syntax, so a unary command name such as `saveMission`, `loadFile` or `triHttpGet` passes. Who may send
is decided by `RemoteExecClientAuthorized` (`CWR:engine/Poseidon/Network/NetworkServerAuth.hpp#L65-L109`,
`CWR:…NetworkServerMsgOnMessage.cpp#L684-L692`): the game master and the bot client always; other clients only when
the mission's own `description.ext` has `class CfgRemoteExec` with `mode = 1` (names listed as classes under
`Functions` or `Commands`) or `mode >= 2` (any name) (`CWR:engine/Poseidon/Network/NetworkServerMission.cpp#L77-L115`,
`#L384-L395`). A downloaded MP mission with `mode = 2` therefore lets any joined player run, for example,
`saveMission` on the server (F4) or `triHttpGet` on every client (F1). The default (no class) is safe. Linter,
agent and CSV rules: §5.2 L10, §5.3, CSV rows `remoteExec`, `remoteExecCall`, `description.ext CfgRemoteExec`.

**F10. Non-literal numeric values in config and SQM files run as script expressions at load [V code; I impact]
(added by the consolidation pass, 2026-09-27, from doc 35 §5.8).** When the config parser meets a numeric value that is
not a literal, it evaluates it as a script expression while the file loads
(`CWR:engine/Poseidon/IO/ParamFile/ParamFile.cpp#L815-L860`, `CWR:engine/Poseidon/IO/ParamFile/ParamFileEval.cpp#L107-L113`,
as cited by doc 35; not re-read in this pass). The template wizard depends on this: its positions, facings and trigger
sizes are arithmetic over `WIZVAR_*` anchors, and on finish it reloads `mission.sqm` so they evaluate, then saves the
mission (doc 35 §5.8; that the saved values are literals is our inference [I]). Any
text `mission.sqm` or `description.ext` can use the same path, so a downloaded mission can hold code in fields that
look like data, outside every code sink that F7 lists [I]. Which commands can run there is untested (doc 35 open
question 5) [U]. Linter, agent and CSV rules: §5.2 scope and L12, §5.3, CSV row `non-literal numeric in config or SQM`.

### 3.2 File reads

| Command | Effect | Tag |
| --- | --- | --- |
| `loadFile`, `preprocessFile`, `exec`, `#include`, `addAction`/`setWaypointScript` script names | Unconfined lookup (F3) | [V] |
| `loadConfig`, `listConfigNames` | Read/list `<UserDir>/Config/`; names with `/` or `\` are refused (`CWR:…GameStateExtWorldConfig.cpp#L84-L135`, `#L445-L483`) | [V] |
| `loadStatus`, `loadIdentity` | Read the campaign's `objects.sav` (`CWR:…GameStateExtWorld.cpp#L898-L945`, `#L1029-L1077`) | [V] |
| `setObjectTexture`, `setFlagTexture` | Load a texture by path (`CWR:…GameStateExtUi.cpp#L330-L400`); path handling not traced | [I] |
| `loadMission` | Raw path on servers; reads only a 20-byte header, so an existence/format probe (F4) | [V] |
| `#include` in `description.ext` and other preprocessed configs | Raw name tried first (F3) | [V code; I reach] |
| `triFontTune` (gated) | TTF from any path handed to the font loader (F2) | [V]/[I] |

### 3.3 File writes and persistence across missions or profiles

| Command | Effect | Tag |
| --- | --- | --- |
| `saveVar` | Campaign variable table, saved with campaign progress (`CWR:…GameStateExtGrp.cpp#L412-L425`; doc 18 §6.1) | [V] |
| `saveStatus`, `deleteStatus`, `saveIdentity`, `deleteIdentity` | Rewrite `<campaign save dir>/objects.sav`; keys are class names, not paths (`CWR:…GameStateExtWorld.cpp#L814-L1027`); never reverted (doc 18) | [V] |
| `fillWeaponsFromPool` and the pool commands | Campaign weapon pool (`CWR:…GameStateExtWorld.cpp#L1325`, `CWR:…OptionsUI.cpp#L1335-L1338`); per-command persistence inferred | [V]/[I] |
| `saveGame` | Overwrites `<save dir>/autosave.fps` (`CWR:…GameStateExtUi.cpp#L2123-L2135`) | [V] |
| `saveConfig` | Writes `<UserDir>/Config/<name>` (`CWR:…GameStateExtWorldConfig.cpp#L137-L167`); `:` and other Windows path forms not analysed | [V]/[U] |
| `VBS_addHeader/Event/Footer` | Text into the MP report, written only when report writing is on (`CWR:engine/Poseidon/AI/AICenterStats.cpp#L286-L288`) | [V] |
| `logInfo`, `textLog`, `debugLog` | Log lines (F6) | [V] |
| `saveMission` | Raw path on servers (F4) | [V] |
| gated `tri*` | F2 | [V] |

### 3.4 Network and multiplayer

| Command | Effect | Tag |
| --- | --- | --- |
| `triHttpGet` (always), `triFetchWorkshopMods`, CE `triDownloadFile` (gated) | Internet egress (F1, F2) | [V] |
| `publicVariable`, `publicVariableArray`, `publicVariableString` | Broadcast a variable (`CWR:…GameStateExtUi.cpp#L2309-L2313`) | [V] |
| `publicExec` | Every client `Execute`s the string; the server relays only from the game master or bot client (`CE:engine/Poseidon/Network/NetworkServerMsgOnMessage.cpp#L139-L142`, `#L589-L604`; `CE:engine/Poseidon/Network/NetworkClientOnMessage.cpp#L2407-L2414`) | [V] |
| `remoteExec`, `remoteExecCall`, `remoteExecRemove` | Run a named global function on peers, optional JIP queue (`CWR:…GameStateExtWorldConfig.cpp#L1104-L1233`; `CE:…NetworkClientOnMessage.cpp#L226-L245`). All are no-ops outside `GModeNetware`. Correction 2026-09-27: the identifier check is syntax only and the receiver falls back to `<name> _this`, so the name can be any unary engine command; non-privileged senders are gated by the mission's `CfgRemoteExec` (F9) | [V] |
| `description.ext` `CfgRemoteExec` | Mission-set policy: `mode = 2` lets every client `remoteExec` any name, commands included (F9) | [V code; I impact] |
| `onPlayerConnected`, `onPlayerDisconnected` | Store code run on (dis)connect (`#L940-L952`) | [V] |
| `serverPause`, `serverResume` | Freeze server simulation for everyone (`#L900-L918`) | [V] |
| `triNetCommand`, `triMp*`, chat/VoN `tri*` | F2 | [V] |

### 3.5 Process and application lifecycle

`endGame` (CWR, F5); `forceEnd`/`enableEndDialog` (quit under AutoTest); `triEndTest` (`_exit(0)` when no application
object, `CWR:…GameStateExtServerTest.cpp#L21-L41`); CE `triEndGame`; `triRemount`. No command spawns a process: a
search of `engine/` and `apps/` C/C++ sources in both trees for `CreateProcess`, `ShellExecute`, `system(`, `popen(`,
`fork()`, `execvp`, `posix_spawn` and `SDL_OpenURL` found nothing [V by absence].

### 3.6 UI and input

`createDialog` opens a resource-defined dialog that can hold focus (`CWR:…GameStateExtWorldDialog.cpp#L136-L166`);
`buttonSetAction` stores code (`#L388-L414`); `disableUserInput` blocks all input until re-enabled
(`CWR:…GameStateExtUi.cpp#L2303-L2307`), which can leave a Preview window unusable; the gated synthetic-input verbs
(F2) and the harness `key`/`key_up` (§4) can drive any menu, including profile and save screens [I].

### 3.7 Debug, cheat and diagnostics

Correction 2026-09-27 [V]: `diag_drawmode`, `diag_toggle` and `diag_enable` are **not registered** in these builds.
Their handlers and the `INIT_MODULE(GameStateObj, 3)` that registers them sit inside `#if _ENABLE_CHEATS`
(`CWR:engine/Poseidon/World/Scene/SceneDraw.cpp#L469-L555`, `CE:…#L596-L682`), and `_ENABLE_CHEATS` is 0 (§2). They
belong with `DBG_*`: unknown commands for every current target. The earlier text (global diagnostic state from any
mission; possible MP cheat) applied only to cheat-enabled builds. Correction 2026-09-27 [V]: `showDebug ["text", ms]`
does not toggle evaluator debug output; it shows a global on-screen message through `GlobalShowMessage`
(`CWR:…GameStateExtObj.cpp#L1168-L1186`, `CWR:engine/Evaluator/express.cpp#L88-L91`,
`CWR:engine/Poseidon/Game/Scripting/ExpressExt.cpp#L180-L183`), which a mission could use to imitate engine messages
[I]. `cheatsEnabled` returns false but is registered with a `Nothing` return
type (`CWR:…GameStateExt.cpp#L897`, `CWR:…GameStateExtWorld.cpp#L1329-L1336`), a quirk our type checker must mirror.
`DBG_screenshot`/`DBG_switchLandscape` and the three `diag_*` commands are compiled out (§2) but appear in the owner's
extracted catalog (`DK:lsp/crates/poseidon-catalog/data/commands.json#L1693-L1853`). The gated `triCheat*` verbs call
the debug-cheat layer.

### 3.8 Resource exhaustion

`while … do` stops after 10,000 iterations and `for` after 100,000 (`CWR:engine/Evaluator/express.cpp#L788-L798`,
`#L944-L953`), but nesting multiplies the cost within one frame [I]. `resize` has no upper bound (`#L642-L655`).
`triWaitFrames`/`triSimFrames` pump up to 600 frames inside a single script call (gated). The harness waits up to 30 s
per command, configurable by `HARNESS_CMD_TIMEOUT_SEC` (`CWR:engine/Poseidon/Dev/Harness/HarnessServer.cpp#L411-L421`).

### 3.9 CWR and CE differences, and what 1.99 had

- **CE vs CWR [V].** The script-surface differences are: `endGame` → gated `triEndGame`
  (`CE:…GameStateExt.cpp` table and `CE:…GameStateExtWorld.cpp#L787-L803`); new gated verbs `triDownloadFile`,
  `triMapWheel`, `triScenePreloadCount`, `triDetailTextureLoads`; path-collapsing changes in `QBStream.cpp`; a
  download-result type change in `HarnessBuiltins.cpp`. `express.cpp`, `HarnessServer.cpp`, `HttpTestRewrite.cpp`,
  `Xml.cpp`, `GameStateExtWorldConfig.cpp`, `GameStateExtUi.cpp`, `GameStateExtObj.cpp`, `Scripts.cpp`,
  `PreprocC.cpp`, `DebugCommands.cpp`, `DebugCheats.cpp`, `ProfileManager.cpp`, `GameSettingsConfig.cpp`,
  `GamePaths.cpp`, `GameStateExtTestRender.cpp`, `GameStateExtTestGeneric.cpp`, `GameStateExtTestGetters.cpp`,
  `GameStateExtServerTest.cpp` and `GameApplication.cpp` are identical (`fc` text compare). `OptionsUI.cpp`,
  `NetworkServerMission.cpp`, `NetworkServerMsgOnMessage.cpp`, `ServerApplication.cpp` and `SceneDraw.cpp` differ;
  spot checks of the audited functions (`FindScript`, `SaveWorldState`, the `publicExec` relay gate, the server `tri`
  gate) found the same code at shifted line numbers.
- **1.99 [I/U].** Doc 14 already establishes that `remoteExec`/`remoteExecCall` are Remastered additions. Doc 18
  records community reports that Resistance 1.75 introduced `saveStatus`/`saveIdentity` and the weapon pool. A web
  search summary attributes `loadFile`/`preprocessFile` to 1.82, but the BI wiki page could not be read (HTTP 403), so
  that is **[U]**. A repeat search on 2026-09-27 gave the same 1.82 summary with one source placing `preprocessFile`
  in 1.85, and `/wiki/loadFile` again returned HTTP 403; still **[U]**. By naming and code comments we infer that
  `remoteExecRemove`, `isJIP`, `netId`, `saveMission`/`loadMission` and `serverPause`/`serverResume` are post-1.99
  (`diag_*` removed from this list on 2026-09-27: not registered in any current target). `publicExec`,
  `loadConfig`/`saveConfig` and `VBS_*` are **[U]**. The CSV marks each row `likely`, `absent` or `unknown`. A runtime check on the legacy
  executable would settle it (§7).
- **1.99, upgraded by the consolidation pass (2026-09-27) from doc 35 §8 [V content; V strings; I availability].**
  20 of the 30 CSV rows marked "1.99: likely" are observed in legacy official content: `exec`, `call`, `saveVar`,
  `saveStatus`, `loadStatus`, `deleteStatus`, `saveIdentity`, `loadIdentity`, `saveGame`, `fillWeaponsFromPool`,
  `addWeaponPool`, `addMagazinePool`, `putWeaponPool`, `pickWeaponPool`, `publicVariable`, `forceEnd`,
  `disableUserInput`, `addAction`, `addEventHandler` and `setFlagTexture` (doc 35 tier T1). `cheatsEnabled` and
  `debugLog`, marked "unknown", are observed too. `loadFile` is used only by CWE content and its name is in the 1.99
  executable (tier T2), which supersedes the "1.82" search summary above for the question "does 1.99 have it".
  `endGame` is absent from the 1.99 executable (F5). The CSV rows now say so, per
  [`data/cwa199-observed-commands.csv`](data/cwa199-observed-commands.csv). The other nine `likely` rows
  (`preprocessFile`, `deleteIdentity`, `clearWeaponPool`, `clearMagazinePool`, `createDialog`, `buttonSetAction`,
  `onMapSingleClick`, `setObjectTexture`, `while`) are not observed in content and stay `likely`. Not yet folded into
  the CSV: doc 35 §8.2's string scan also lists `preprocessFile`, `createDialog`, `buttonSetAction`, `onMapSingleClick`,
  `while` and `setObjectTexture` as present, and `for`, `publicExec`, `publicVariableArray`, `publicVariableString`,
  `onPlayerConnected`, `isJIP`, `netId`, the `setWaypoint*` family, `remoteExec` and `VBS_*` as absent; a present
  string does not prove registration. Those rows wait for the `exe_199_string` data column that doc 35 rc90 proposes.

## 4. Harness protocol risks

### 4.1 Transport and binding

| # | Behaviour | Evidence | Risk |
| --- | --- | --- | --- |
| H1 | Binds `INADDR_LOOPBACK`, backlog 1, prints `HARNESS_PORT=<n>` on stdout | `CWR:engine/Poseidon/Dev/Harness/HarnessServer.cpp#L95-L142` [V] | Other local users can connect; the port is findable by scanning [I] |
| H2 | No authentication or handshake | `#L303-L456` [V] | First client to connect owns the game |
| H3 | Serves one client at a time; the next `accept` happens only after the current client disconnects | `#L253-L301` [V] | A client that stays connected blocks others [I]; when our client drops, the next queued client gets full control |
| H4 | Lines that are not valid JSON get an error reply and the loop continues; no line-length cap on the receive buffer | `#L340-L367` [V] | An HTTP request whose body holds a JSON line would be processed, so a web page could drive the harness if it finds the port and the browser allows the request [I/U]; memory growth from a client that never sends a newline [I] |
| H5 | `SO_REUSEADDR` on the listening socket | `#L91-L93` [V] | On Windows, without `SO_EXCLUSIVEADDRUSE`, another process may bind the same explicit port [I]; port 0 reduces this |
| H6 | `ping`, `describe`, `exit` are handled on the network thread | `#L381-L402` [V] | Any connected client can quit the game |

### 4.2 Verbs registered by `PoseidonGame` and `PoseidonServer`

The client registers `screenshot`, `eval`, `exec`, `http_fixture`, `key`, `key_up` and `query`
(`CWR:apps/cwr/Game/GameApplication.cpp#L556-L594`); the dedicated server registers `query`, `eval`, `exec` and
`http_fixture` (`CWR:apps/cwr/Server/ServerApplication.cpp#L418-L457`). Doc 08 §2.5 covers the schema.
Added 2026-09-27 [V]: the server's `query` handler also falls through to `AnswerServiceQuery`
(`CWR:apps/cwr/Server/ServerApplication.cpp#L434-L445`), so `download` (any URL to any path) and the master-server
queries work on the dedicated server too, even though its comment says it advertises only headless queries; both
builds also answer the read-only `connections` and `roles` targets (`CWR:…HarnessBuiltins.cpp#L266-L326`).
`RegisterUIQuery`/`RegisterWaitDisplay` (`query what=display`, `wait_display`) exist in `HarnessBuiltins.cpp` but
neither app registers them.

- **`eval`/`exec`** run any SQF in one process-wide local scope, `s_evalScope`
  (`CWR:engine/Poseidon/Dev/Harness/HarnessBuiltins.cpp#L73-L111`). Everything in §3, including gated `tri*` verbs,
  is one line away.
- **`screenshot{path}`** passes the raw path to `GEngine->Screenshot` (`#L56-L71`): an image file at any writable path.
- **`http_fixture{url,target}`** accepts a target that merely *starts with* `http://127.0.0.1:`, `http://localhost:`
  or `http://[::1]:` (`CWR:engine/Poseidon/Network/HttpTestRewrite.cpp#L21-L27`). A target containing userinfo, such
  as `http://localhost:1@example.org/`, passes the check, and libcurl treats the part before `@` as credentials [I].
  Rewritten requests are fetched with redirects on (`CWR:engine/Poseidon/Network/XML/Xml.cpp#L98-L101`;
  `CE:engine/Poseidon/Network/MasterServerServiceClient.cpp#L433-L437`).
- **`query`** answers read-only `players`, `mission`, `ngs`, `world`, `play_state`, `von_state`
  (`HarnessBuiltins.cpp#L132-L260`, `GameApplication.cpp#L427-L442`). It also answers `master_server_*` and
  `mp_resolve` (outbound queries), **`mp_join`** (arm a connect to any address with a password, optionally re-mount
  mods, `#L655-L682`) and **`download`** (any URL to any `dest` path, `#L753-L792`), all reached through
  `AnswerServiceQuery` (`#L795-L834`).
- **`key`/`key_up`** push synthetic SDL key events (`#L836-L872`).

### 4.3 Can a mission reach the harness?

Not directly [I]. A mission cannot read the game's stdout, so it does not learn the port. `triHttpGet` can send a GET
to loopback, but a GET carries no body and its request and header lines are not JSON, so H4 does not apply to
`http(s)` URLs. Caveat added 2026-09-27: on non-Windows builds the libcurl call has no protocol limit, and a
`gopher://127.0.0.1:<port>/_…` URL sends arbitrary bytes, which would include a JSON line; a mission could also
probe loopback ports this way (unverified: depends on the linked libcurl's protocols, and our client already holding
the only harness connection (H3) blocks it). With `--harness` the gated `tri*` verbs are registered anyway, so the
extra reach would be the harness-only verbs (`screenshot` to any path, `query` `download`/`mp_join`). The real
coupling is the other way round: whatever we send through `eval`/`exec` runs in the mission's global variable space,
so mission code can redefine globals our templates read. Our templates must therefore use only engine commands and
their own `_local` variables, and treat every returned string as mission-controlled data [I].

## 5. Recommended policy

### 5.1 Catalog metadata

Add two fields to each entry of our per-dialect catalog [I]:

- **`gate`**: `always` | `test-flags` (registered with `--dev`/`--harness`/`--test-mission`) | `unconditional-test`
  (F1) | `compiled-out` | `evaluator-tool-only` (`EvalState`) | `server-only`.
- **`caps`** (a set): `pure`, `mission-state`, `ui`, `input-lock`, `deferred-code`, `dynamic-code`, `fs-read`,
  `fs-write`, `persist-campaign`, `persist-profile`, `log-write`, `net-mp`, `net-internet`, `process`, `debug`,
  `test-only`, `resource`.

The CSV is the seed for the risky subset. Everything not in it is `pure` or `mission-state` by default and should be
confirmed when the full catalog is extracted. Extract from all registration sites in §2 (including test modules) and
drop only `EvalState` rows. Port the owner fork's source-scanning completeness test, minus its `*Test*` exclusion
(`DK:lsp/crates/poseidon-catalog/tests/completeness.rs#L24-L37`).

Policy vocabulary used in the CSV: **lint** `deny` (error; blocks one-click Preview), `warn`, `info`; **agent**
`allow`, `approve` (the user must accept it with the rationale shown), `template-only` (only our deterministic
generators, e.g. the campaign compiler, may emit it), `deny`; **harness** `allow`, `template`, `console`, `never`.

### 5.2 (a) Linting community missions

Scope: every code string the mission ships: `.sqs`/`.sqf` files, `mission.sqm` init, condition, activation and
waypoint statement fields, `description.ext` dialog and control code, any string literal that reaches a code sink
(F7), and every non-literal numeric value in `mission.sqm`, `description.ext` and other shipped configs (F10, added by
the consolidation pass). Rules [I]:

| Rule | Trigger | Severity |
| --- | --- | --- |
| L1 | `triHttpGet` or any gated `tri*` verb (CSV), `DBG_*`, `diag_*`, `saveMission`/`loadMission`, anywhere, including inside strings and as a `remoteExec`/`remoteExecCall` function name | deny |
| L2 | Script or file path containing `..` or `:`, a UNC path, or a path that is absolute after removing one leading `\`; an `#include` that does any of these | deny |
| L3 | Other leading-`\` paths (engine-root lookup); non-literal path argument | warn |
| L4 | Code sink (`call`, `exec`, `publicExec`, `onPlayerConnected`, `buttonSetAction`, `addEventHandler`, statements setters) with a non-literal argument | warn, and mark the mission "not statically checkable" |
| L5 | `endGame` (CWR only), `serverPause`, `publicExec`, `disableUserInput true` with no reachable `false`, `showDebug`, unconditional test verbs (`triAssert*`, `triGet*`), `loadConfig`/`saveConfig`/`listConfigNames`, `deleteStatus`/`deleteIdentity`, pool clears | warn |
| L6 | Log text that imitates engine markers (F6) | warn |
| L7 | Nested loops; `resize` with a non-literal size or a literal above 100,000 | warn |
| L8 | Command unknown in the mission's target profile (includes compiled-out and CE-only verbs) | error (type checker) |
| L9 | Campaign persistence (`saveVar`, `saveStatus`, …), MP commands (`remoteExec` → Requires CWR) | info, feeds the Requires badge |
| L10 | `description.ext` `CfgRemoteExec`: `mode >= 2`, or a listed `Functions`/`Commands` name that is an engine command whose own policy is `deny` (F9) → deny; any other `mode = 1` → warn | deny / warn |
| L11 | `#include` in `description.ext` or any shipped config whose name breaks L2 (F3) | deny |
| L12 (consolidation pass) | Non-literal numeric value in `mission.sqm`, `description.ext` or another shipped config (F10): its expression is checked as code under L1–L8, and any finding there keeps its own severity; arithmetic over `WIZVAR_*` anchors using only `pure` commands, in a template, is info | warn |

**Preview gate.** A mission with any `deny` finding, or with an L4 finding combined with any `fs-read` or
`net-internet` command, is not one-click Previewable. The user can override per mission with an explicit
confirmation that names the findings; the override is stored in project metadata, not in the mission. Until F1 is
fixed upstream, the dialog must say plainly that Preview runs the mission with the user's full rights [I].

### 5.3 (b) AI-proposed script text

The policy is enforced by the host; the model is never trusted to follow it (AGENTS.md: "Same path as the user",
"Untrusted content") [I].

1. The agent returns script text only inside a typed edit command (e.g. set a trigger's activation field). The host
   parses and type-checks it for the mission's target profile with the check-only checker (F8). Nothing runs.
2. Capability policy: `allow` for `pure`, `mission-state`, `ui`, `resource` within L7 limits, and `deferred-code` whose
   code is a literal that passes this same policy recursively; `allow` also for `publicVariable*` in MP targets and for
   `exec`/`addAction`/`setWaypointScript` with a literal path to a script the project contains (that script passes the
   same policy). `approve` for `input-lock`, `remoteExec`/`remoteExecCall` with a literal name of a mission-defined
   function (MP targets only; never an engine command name, F9), `saveGame`, and literal mission-relative
   `loadFile`/`preprocessFile` of files the project contains (their result usually feeds `call`, which the checker
   cannot see into). Reconciled with the CSV on 2026-09-27: the CSV already said `allow` for `publicVariable*` and for
   project `exec`, while this list said `approve`. `template-only` for campaign
   persistence: only the campaign compiler emits `saveVar`/`saveStatus`/pool commands (docs 18/19); likewise only an
   MP generator may emit `CfgRemoteExec`, and only `mode = 1` listing mission-defined functions (F9); and our writers
   emit numeric fields as literals, with only a template generator emitting anchor arithmetic of `pure` commands
   (F10, added by the consolidation pass). `deny` for
   everything tagged `fs-write` (other than via templates), `net-internet`, `process`, `debug`, `test-only`,
   `compiled-out`, `dynamic-code` with a computed string, and any command outside the target profile or, for
   editor-generated glue, outside the conservative subset.
3. **Never auto-execute.** AI output is never sent to harness `eval`/`exec`. The agent reaches Preview only through
   product tools with fixed behaviour (doc 08 §6: `validate_mission`, `preview_screenshot`; an `eval_sqf_in_preview`
   tool, if kept, runs only after the user presses Run, and its text passes the §5.2 deny rules first).
4. Mission text is data: a briefing or comment that asks for `loadFile` or a URL changes nothing, because rule 2
   applies whatever the model was told. Log every denial with the rule id so evaluations can measure false positives.

### 5.4 (c) What our Preview and probe harness may send

**Launch profile [I].**

- Default Preview uses `--test-mission` **without** `--harness`; add `--harness 0` only when the user opens a
  live-link feature (debug console, teleport, screenshots).
- Set `POSEIDON_USER_DIR` to a per-session folder under the stage, seeded with a copy of the user's settings. The
  client honours it (`CE:engine/Poseidon/Foundation/Common/GamePaths.cpp#L56-L63`). This keeps saves, profiles,
  `objects.sav` and `Config/` writes out of the real profile. It does not stop F1 or F3.
- Parse stdout and logs strictly: accept `HARNESS_PORT=` only as the first matching line from the process we spawned,
  and never treat log text as proof of success (F6); prefer the exit code and harness events.

**Session rules [I].**

- Connect as soon as the port is announced and keep the connection for the whole session (H3). If our connection
  drops, kill the game rather than reconnect, because the next queued client could be someone else.
- Cap reply sizes, time out each request below the engine's 30 s, and treat every reply, event and `eval` result as
  untrusted data. Never pass replies to the agent as instructions.

| Harness verb | Allowed use |
| --- | --- |
| `ping`, `describe`, `exit`, `query` (`players`, `mission`, `ngs`, `world`, `play_state`) | allow |
| `screenshot` | allow, with a path we generate inside the stage folder |
| `eval`/`exec` | `template`: fixed SQF templates with typed, serializer-escaped parameters (teleport with `setPos`, `skipTime`, `setDate`, weather setters, `getPos` queries, `disableUserInput false` for recovery). `console`: text the user typed in the debug console, after §5.2 deny rules, with a confirmation for `warn` findings |
| `http_fixture`, `query` (`download`, `mp_join`, `mp_resolve`, `master_server_*`), `key`/`key_up` | never |
| `tri*` verbs inside `eval` | never, except the in-game probe suite (AGENTS.md "Porting Upstream Code and Tests"), which may use read-only probes (`triSceneReady`, `triFrameCount`, `triGet*`, `triAssert*`) and `triEndTest`; never `triConsoleRun`, cheats, file, profile, input or network verbs |

### 5.5 Target profiles and the Requires badge

The linter's Requires computation should treat `test-only`, `debug` and `compiled-out` commands as "not a valid
target" (error) rather than as a higher version. `remoteExec*`, `saveMission` and similar CWR additions raise the badge
to Remastered/CWR (`diag_*` removed from this list on 2026-09-27: compiled out, so "not a valid target" like `DBG_*`).
CE-only verbs raise it to CE [I]. Editor-generated glue uses only commands that are
`always`-gated, in the conservative subset, and carry no `fs-*`, `net-internet`, `process`, `debug` or `test-only`
cap. Consolidation pass 2026-09-27: doc 35 §8.3 proposes evidence tiers for the `Cwa199` profile (T1 observed in
official content, T2 used by community content and present in the 1.99 executable, T3 present only, T4 absent), and
the CSV's dialect column now carries T1, T2 and T4 evidence where §3.9 applied it.

## 6. Recommended CWR-CE hardening patches

All hook points are in CE@b67bf3bd62 and, unless noted, identical in CWR. Each patch needs a regression test and
adversarial tests in the same change set (AGENTS.md rule, and CE's own style of source-scanning gate tests).
(Order answered 2026-09-27 → [D035](../decisions/D035-outreach-and-security-disclosure.md) items 1 and 3: these
patches go upstream, and enter the engine-requests register, only after the Disclosure note's private reports are
acknowledged. Nothing has been sent yet.)

| # | Patch | Hook points | Tests |
| --- | --- | --- | --- |
| P1 | Gate the Generic and Getters modules like the Audio module; move `triHttpGet` into the gated set or delete it | `engine/Poseidon/Game/Commands/GameStateExtTestGeneric.cpp#L437-L456`, `GameStateExtTestGetters.cpp#L534` | Extend `tests/unit/engine/Poseidon/Dev/Debug/test_dev_mode_gates.cpp#L43-L83` to scan **every** `INIT_MODULE` body that registers a `"tri…"` name and require the gate before it |
| P2 | Decouple test verbs from `--test-mission`/`--harness`: register them only with an explicit `--test-verbs` flag that Trident passes | Gate at `GameStateExtTestAudio.cpp#L2990-L2994`; `apps/cwr/Server/ServerApplication.cpp#L171-L174`; flag in `AppConfig.cpp` next to `--test-mission`; Trident spawn in `engine/Trident/src/client/instance.rs` | Gate test updated; a Trident mission still passes; a `--test-mission` run without the flag reports `triVersion` as unknown |
| P3 | One `ResolveScriptPath()` for all script I/O: reject `..` components, drive letters, `:`, UNC; keep a leading `\` only for lookups that canonicalise under the game root or a mounted bank | `engine/Poseidon/UI/OptionsUI.cpp#L636-L661` (`FindScript`), `engine/Poseidon/Game/Scripting/Scripts.cpp#L126-L150` (`OpenScript`), `GameStateExtWorldConfig.cpp#L1060-L1091` (`preprocessFile` includes), `engine/Poseidon/IO/PreprocC/PreprocC.cpp#L28-L40` | Traversal, absolute and drive-relative names fail with a script error; existing mission/campaign/root lookups and bank paths still resolve (port BI fixtures where present) |
| P4 | Confine `saveMission`/`loadMission` to `<UserDir>/MPSaves/<basename>` with `ConfigFullName`-style validation plus a `:` check | `GameStateExtWorldConfig.cpp#L920-L938` or `engine/Poseidon/Network/NetworkServerMission.cpp#L1135`, `#L1179` | Path-escaping names rejected; round trip still works |
| P5 | Validate names in `triSaveGame`/`triLoadGame`, `triScreenshot`, `triShadowSceneDump`, `triMakeProfileReadOnly`, `triAssertProfileMissing`, `triSetActiveProfile` (reuse `IsValidProfileName` and the `triReadWorkshopFile` component check) | `GameStateExtTestAudio.cpp#L1783-L1833`, `#L2827-L2860`; `GameStateExtTestRender.cpp#L241-L260`, `#L484-L497` | Separator and `..` labels rejected |
| P6 | Harness hardening: a random token printed next to `HARNESS_PORT=` (only the parent sees stdout) and required as the first request; close the connection on the first non-JSON line or on HTTP-looking lines; cap line and buffer size; `SO_EXCLUSIVEADDRUSE` on Windows; stop accepting after the first authenticated client; `--harness-caps` so `download`, `mp_join`, `http_fixture` and `key` are off unless asked for; confine `screenshot` paths to an output folder | `engine/Poseidon/Dev/Harness/HarnessServer.cpp#L91-L155`, `#L303-L402`; `HarnessBuiltins.cpp#L56-L130`, `#L753-L835`; `apps/cwr/Game/GameApplication.cpp#L556-L594`; `apps/cwr/Server/ServerApplication.cpp#L418-L457`; Trident client handshake | Unit tests for token, framing, caps; an HTTP-shaped request is dropped without executing anything |
| P7 | Parse `http_fixture` targets properly (scheme `http`, host exactly loopback, no userinfo); disable redirects for rewritten URLs; restrict libcurl to `http`/`https` everywhere | `engine/Poseidon/Network/HttpTestRewrite.cpp#L21-L27`; `engine/Poseidon/Network/XML/Xml.cpp#L98-L115`; `engine/Poseidon/Network/MasterServerServiceClient.cpp#L433-L459` | Userinfo and non-loopback targets rejected; `file://` refused |
| P8 | Optional capability policy in the evaluator: tag registrations with capability bits and add `--script-policy untrusted`, which turns `fs-*`/`net-internet`/`process`/`debug`/`test-only` commands into script errors | `engine/Evaluator/express.cpp#L2217-L2260` (`NewFunction`/`NewOperator`/`NewNularOp`) and dispatch near `#L1316-L1330` | Each tagged command errors under the flag; vanilla missions unaffected |
| P9 (added 2026-09-27) | `remoteExec` executes only mission-defined functions: drop the `<name> _this` fallback for names that are registered engine commands, or require a server-config (not mission) opt-in for `CfgRemoteExec` `Commands` and `mode >= 2` | `ExecuteNamedRemoteExec` in `engine/Poseidon/Network/NetworkServerMsgOnMessage.cpp#L113-L132` and `NetworkClientOnMessage.cpp#L226-L245`; policy load at `NetworkServerMission.cpp#L398-L406` (CE) | A client `remoteExec` naming `saveMission`/`loadFile` is rejected on server and clients; a mission `mode = 2` without the server opt-in behaves as mode 0; mission functions still work |

P1, P3, P7 and P9 are the most valuable for players of the shipping game; P2 and P6 are what our Preview needs. CE already
did the `endGame` part of this work (F5), so BI could adopt it too [I].

## 7. Open questions

1. **Is `GameStateExtTestGeneric` linked into the shipping Remastered `PoseidonGame`?** Harmless probe: a mission,
   launched without any test flag, that shows `str (triAssert [true])` in a hint. `"OK"` confirms F1; a script error
   means the unconditional verbs are absent from that binary [U].
2. Does the Steam Remastered 3.05 binary match `CWR@ffc61838b7` (open in doc 08) [U]?
3. Runtime behaviour of F3 on Windows and Linux: do a leading-`\` drive path and a `..` path open outside the mission?
   Probe with a marker file inside our own stage folder [U].
4. Does WinINet attach stored cookies, or follow redirects across schemes, for `triHttpGet` on Windows [U]?
5. Which gated settings verbs (`triBindAction`, `triSetVolume`, `triSetLanguage`) persist to the profile on exit [U]?
6. Can a browser page reach a loopback harness port in current Chrome, Edge and Firefox, and are ephemeral-port scans
   practical [U]? P6 makes this moot.
7. Is `IsServer()` true in single-player Preview (F4) [U]?
8. Which of the §3.9 commands exist in CWA 1.99? Needs a probe on the legacy executable or wiki access [U].
   Partly answered by the consolidation pass (2026-09-27): doc 35 §8 settles existence for the observed commands and
   gives string-scan evidence for others (§3.9); semantics and the remaining rows still need a probe.
9. Will CE accept P2 given that Trident test missions call `tri*` verbs directly? Needs maintainer input [U].
10. Timing and channel for the private report (Disclosure note) [U]. (Answered 2026-09-27 →
    [D035](../decisions/D035-outreach-and-security-disclosure.md) item 1: the owner reports now, through a private
    channel of each project, and logs the dates in OWQ-09; not sent yet.)
11. Which `description.ext` dialog attributes hold executable code in this engine, so the linter extracts all code
    sinks [U]?
12. (Added 2026-09-27.) Which protocols does the shipped non-Windows libcurl enable (`file`, `gopher`, `dict`)? Probe:
    `triHttpGet` of a `file://` URL to a marker file inside our stage folder [U].
13. (Added 2026-09-27.) Is `GameStateExtTestGeneric` linked into the shipped dedicated server, so `triHttpGet` is
    registered there without flags [U]? Same probe as question 1, run on a server.
14. (Added 2026-09-27.) Does a real MP session honour a mission's `CfgRemoteExec` `mode = 2` for a plain client
    naming an engine command (F9)? Probe on our own loopback server with a harmless command such as `hint` [U].
15. (Added by the consolidation pass, 2026-09-27.) Which commands run inside a non-literal numeric field of
    `mission.sqm` or `description.ext` on 1.99 and on CWR (F10)? Same as doc 35 open question 5; probe with harmless
    commands only [U].

## 8. Sources

Source snapshots (static reading, 2026-09-26): `BohemiaInteractive/CWR@ffc61838b7`,
`ofpisnotdead-com/CWR-CE@b67bf3bd62`, `DK26/CWR@6fd6ca3974`.

- Registration: `CWR:engine/Evaluator/express.cpp#L1098-L1219`; `CWR:engine/Poseidon/Game/Commands/GameStateExt.cpp#L853-L1503`;
  `CE:engine/Poseidon/Game/Commands/GameStateExt.cpp#L852-L1501`; `CWR:engine/Poseidon/World/Scene/SceneDraw.cpp#L469-L555`;
  `CE:engine/Poseidon/World/Scene/SceneDraw.cpp#L596-L682`;
  `CWR:engine/Poseidon/Game/Commands/GameStateExtTestAudio.cpp#L287-L288`, `#L2960-L3315`;
  `CE:engine/Poseidon/Game/Commands/GameStateExtTestAudio.cpp#L2990-L3350`;
  `CWR:engine/Poseidon/Game/Commands/GameStateExtTestGeneric.cpp#L416-L456`;
  `CWR:engine/Poseidon/Game/Commands/GameStateExtTestGetters.cpp#L520-L588`;
  `CWR:engine/Poseidon/Game/Commands/GameStateExtServerTest.cpp#L14-L98`; `CWR:apps/cwr/Server/ServerApplication.cpp#L171-L174`;
  `CWR:engine/Evaluator/EvalState.cpp#L186-L764`; `CWR:engine/Poseidon/Foundation/Modules/Modules.hpp#L29-L39`;
  `CWR:engine/Poseidon/Foundation/PoseidonPCH.hpp#L44`; `CWR:engine/Poseidon/CMakeLists.txt#L14-L37`, `#L114-L147`.
- Gate tests: `CWR:tests/unit/engine/Poseidon/Dev/Debug/test_dev_mode_gates.cpp#L43-L127`.
- File I/O: `CWR:engine/Poseidon/Game/Scripting/Scripts.cpp#L126-L150`, `#L574-L580`; `CWR:engine/Poseidon/UI/OptionsUI.cpp#L630-L655`,
  `#L1335-L1338`, `#L1386-L1597`; `CE:engine/Poseidon/UI/OptionsUI.cpp#L636-L661`;
  `CWR:engine/Poseidon/IO/Streams/QBStream.cpp#L1501-L1616`; `CWR:engine/Poseidon/IO/PreprocC/PreprocC.cpp#L28-L40`;
  `CWR:engine/Poseidon/Game/Commands/GameStateExtWorldConfig.cpp#L84-L167`, `#L445-L501`, `#L602-L618`, `#L900-L952`,
  `#L1050-L1233`; `CWR:engine/Poseidon/Game/Commands/GameStateExtWorld.cpp#L745-L1077`, `#L1325`, `#L1329-L1336`;
  `CWR:engine/Poseidon/Game/Commands/GameStateExtUi.cpp#L330-L400`, `#L2123-L2135`, `#L2303-L2313`;
  `CWR:engine/Poseidon/Game/Commands/GameStateExtGrp.cpp#L412-L436`; `CWR:engine/Poseidon/Game/Commands/GameStateExtObj.cpp#L1168-L1186`;
  `CWR:engine/Poseidon/Game/Commands/GameStateExtWorldDialog.cpp#L136-L166`, `#L388-L414`;
  `CWR:engine/Poseidon/Network/NetworkServerMission.cpp#L1123-L1180`; `CE:engine/Poseidon/Network/NetworkServerMission.cpp#L1135-L1192`;
  `CWR:engine/Poseidon/AI/AICenterStats.cpp#L286-L288`.
- Test verbs: `CWR:engine/Poseidon/Game/Commands/GameStateExtTestAudio.cpp#L1113-L1127`, `#L1273-L1298`, `#L1509-L1516`,
  `#L1778-L1828`, `#L2797-L2830`; `CE:engine/Poseidon/Game/Commands/GameStateExtTestAudio.cpp#L337-L387`, `#L1538-L1564`,
  `#L2083-L2104`; `CE:engine/Poseidon/Game/Commands/GameStateExtTest.cpp#L625-L682`, `#L1923-L2054`;
  `CE:engine/Poseidon/Game/Commands/GameStateExtTestMap.cpp#L73-L105`; `CE:engine/Poseidon/Game/Commands/GameStateExtWorld.cpp#L787-L803`;
  `CWR:engine/Poseidon/Game/Commands/GameStateExtTestRender.cpp#L225-L260`, `#L482-L497`;
  `CWR:engine/Poseidon/Core/Profile/ProfileManager.cpp#L93-L102`; `CWR:engine/Poseidon/UI/Settings/GameSettingsConfig.cpp#L311-L325`;
  `CWR:engine/Poseidon/Dev/Debug/DebugCommands.cpp#L50-L84`; `CWR:engine/Poseidon/Dev/Debug/DebugCheats.cpp#L735-L780`.
- Network: `CWR:engine/Poseidon/Network/XML/Xml.cpp#L80-L117`, `#L291-L297`, `#L940-L1030`;
  `CWR:engine/Poseidon/Network/HttpTestRewrite.cpp#L21-L63`; `CE:engine/Poseidon/Network/MasterServerServiceClient.cpp#L433-L459`;
  `CE:engine/Poseidon/Network/NetworkServerMsgOnMessage.cpp#L113-L142`, `#L589-L630`;
  `CWR:engine/Poseidon/Network/NetworkServerMsgOnMessage.cpp#L139-L142`, `#L616-L640`;
  `CE:engine/Poseidon/Network/NetworkClientOnMessage.cpp#L226-L245`, `#L2407-L2424`.
- Harness: `CWR:engine/Poseidon/Dev/Harness/HarnessServer.cpp#L55-L456`; `CWR:engine/Poseidon/Dev/Harness/HarnessBuiltins.cpp#L56-L260`,
  `#L381-L872`; `CE:engine/Poseidon/Dev/Harness/HarnessBuiltins.cpp#L753-L836`; `CWR:apps/cwr/Game/GameApplication.cpp#L427-L442`,
  `#L556-L594`; `CWR:apps/cwr/Server/ServerApplication.cpp#L418-L457`.
- Evaluator check-only mode and limits: `CWR:engine/Evaluator/express.cpp#L642-L655`, `#L788-L798`, `#L944-L953`,
  `#L1316-L1330`, `#L2217-L2260`, `#L3067-L3092`; `CWR:engine/Evaluator/EvalState.cpp#L709-L732`.
- Sandboxed user dir: `CE:engine/Poseidon/Foundation/Common/GamePaths.cpp#L56-L63`.
- Added by the 2026-09-27 verification: `CWR:engine/Poseidon/Network/NetworkServerMsgOnMessage.cpp#L113-L132`, `#L684-L692`;
  `CWR:engine/Poseidon/Network/NetworkServerAuth.hpp#L65-L109`; `CWR:engine/Poseidon/Network/NetworkServerMission.cpp#L77-L115`,
  `#L384-L395`, `#L1167-L1214`; `CE:engine/Poseidon/Network/NetworkServerMission.cpp#L398-L406`;
  `CWR:engine/Poseidon/IO/PreprocC/PreprocC.cpp#L28-L72`; `CWR:engine/Poseidon/IO/ParamFile/ParamFileUsePreprocC.cpp#L11-L21`;
  `CWR:engine/Poseidon/Graphics/Rendering/Draw/Font.cpp#L99-L133`; `CE:engine/Poseidon/Game/Commands/GameStateExtTestAudio.cpp#L2150-L2186`;
  `CWR:engine/Poseidon/Dev/Debug/DebugCheats.cpp#L557-L619`; `CWR:engine/Poseidon/UI/Controls/UIControls.cpp#L1729-L1750`;
  `CWR:engine/Poseidon/Game/Scripting/ExpressExt.cpp#L180-L183`; `CWR:engine/Evaluator/express.cpp#L88-L91`;
  `CWR:engine/Poseidon/Network/XML/Xml.cpp#L266-L297`; `CWR:engine/Poseidon/Game/Commands/GameStateExtServerTest.cpp#L84-L98`;
  `CWR:engine/Poseidon/Game/Commands/GameStateExtTestGetters.cpp#L443-L459`; `CWR:apps/cwr/Server/ServerApplication.cpp#L434-L445`;
  `CWR:engine/Poseidon/Dev/Harness/HarnessBuiltins.cpp#L266-L326`, `#L917-L963`; `CWR:vcpkg.json#L7`;
  `CE:engine/Poseidon/UI/ModDownloadSupport.hpp#L40-L66`; `DK:lsp/crates/poseidon-catalog/data/commands.json#L1693-L1853`.
- Added by the consolidation pass (2026-09-27): doc 35 §5.8, §5.9, §8.1–§8.4 and §10, and
  [`data/cwa199-observed-commands.csv`](data/cwa199-observed-commands.csv); `CWR:engine/Poseidon/IO/ParamFile/ParamFile.cpp#L815-L860`
  and `CWR:engine/Poseidon/IO/ParamFile/ParamFileEval.cpp#L107-L113` as cited by doc 35 (not re-read in this pass).
- Owner fork catalog: `DK:lsp/crates/poseidon-catalog/src/lib.rs#L1-L33`; `DK:lsp/crates/poseidon-catalog/tests/completeness.rs#L1-L87`;
  `DK:lsp/crates/poseidon-catalog/data/commands.json#L1693`.
- Project docs: doc 04 §8 (script entry points), doc 08 §2.4–§2.5, §4.2–§4.4, §6 (Preview, harness), doc 14 §2
  (dialects, `remoteExec`), doc 18 §6, §10 (campaign persistence, 1.75 history), docs 19 and 22, `AGENTS.md`.
- Web: a WebSearch summary of BI's *Operation Flashpoint: Resistance Version History* page
  (<https://community.bistudio.com/wiki/Operation_Flashpoint:_Resistance_Version_History>) attributing
  `loadFile`/`preprocessFile` to 1.82; direct fetches of that page and of `/wiki/loadFile` and `/wiki/preprocessFile`
  returned HTTP 403, so the claim is **[U]**. Repeated 2026-09-27: `/wiki/loadFile` still HTTP 403, the web archive
  could not be fetched, and a new search summary again said 1.82 while noting one source that puts `preprocessFile`
  in 1.85; a second summary said `saveStatus`/`saveIdentity` arrived with the *Resistance* campaign (1.75), which
  agrees with doc 18. All remain **[U]** (search summaries, not primary pages). The same day, a fetch of
  <https://github.com/DK26/CWR> showed a public fork of `BohemiaInteractive/CWR` with an `lsp` directory, so citing it
  here is consistent with the public-repository rule.

## Verification notes (2026-09-27)

An adversarial re-check of this note and the CSV, by static reading of the same pinned trees (HEADs confirmed read-only
as `ffc61838b7`, `b67bf3bd62`, `6fd6ca3974`). Nothing was built or run.

**Method.** (1) Extracted every `GameNular`/`GameFunction`/`GameOperator` name with its line number from
`express.cpp`, `GameStateExt.cpp`, `SceneDraw.cpp` and the four `GameStateExtTest*`/`ServerTest` modules in both
trees, diffed the name sets, searched for any other `GGameState.New*`/`->New*` call, and checked every preprocessor
conditional around a registration. (2) Rechecked 40+ CSV rows (name, table, gate, handler lines, effect) against the
cited lines. (3) Read `HarnessServer.cpp`, `HarnessBuiltins.cpp`, `HttpTestRewrite.cpp`, both apps' harness setup and
the `--harness`/`--test-mission`/`--dev` option code. (4) Compared §5 with `AGENTS.md` and with the CSV. (5) Repeated
the web look-ups. File identity claims in §3.9 were rechecked with SHA-256 hashes and match.

**Confirmed [V].** Registration line counts (CWR / CE: 73 / 73, 473 / 472, 3 / 3, 315 / 320, 17 / 17, 39 / 39,
6 / 6, 72 / 72) and the CWR/CE name diff; the
`INIT_MODULE` gate lines (`CWR:…GameStateExtTestAudio.cpp#L2960-L2964`, `CE:…#L2990-L2994`); the unconditional
Generic and Getters modules and their link hooks; `triHttpGet` (64 KiB cap, curl with `CURLOPT_FOLLOWLOCATION`,
WinINet on Windows); every CSV registration line sampled (`loadFile` L1159, `saveMission` L1043, `remoteExec` L1228,
`showDebug` L1211, `triConsoleRun` L3069, `triMakeProfileReadOnly` L3108, `triScreenshot` L3135, and others);
`FindScript`/`OpenScript`/`QIFStreamB::AutoOpen` behaviour; `saveMission`/`loadMission` raw `fopen`; `endGame` vs CE
`triEndGame`; `ConfigFullName` slash check; check-only mode skipping nular, unary and binary handlers; loop caps; the
harness facts H1–H6 (loopback bind, backlog 1, no auth, one client at a time, no line cap, invalid-JSON lines skipped,
`SO_REUSEADDR`, `ping`/`describe`/`exit` on the network thread); the `http_fixture` prefix check; `query` `download`
and `mp_join`; no process-spawning call in `engine/` or `apps/` of either tree (and no mission-influenced
`LoadLibrary`/`dlopen`); no `SECURITY.md` in either tree; `DK26/CWR` is public.

**Refuted and corrected.**

- `diag_drawmode`, `diag_toggle`, `diag_enable` were listed as always registered. They are compiled out
  (`#if _ENABLE_CHEATS`, `CWR:…SceneDraw.cpp#L469-L555`). Fixed in §2, §3.7, §3.9, §5.2 (moved from L5 to L1), §5.5
  and the three CSV rows. Doc 23 already listed them as cheat-gated, so the two notes now agree.
- `showDebug` does not toggle evaluator debug output; it shows an on-screen message. Fixed in §3.7 and the CSV.
- `loadMission` "loads it as world state" overstated the effect: it reads a 20-byte header and shifts the mission
  start time. `saveMission` always writes the same 20 bytes. Fixed in F4, §3.2 and the CSV.
- `preprocessFile` "same lookup as loadFile": it calls `FindScript` directly, so the leading-`\` rule does not apply to
  its own name. Fixed in F3 and the CSV.
- `remoteExec` "named global function, identifier-checked": the check is syntax only and the receiver falls back to
  `<name> _this`, so engine commands are reachable. New finding F9.
- "CE's gate test" cited a CWR path; the test is identical in both trees. Wording fixed.
- §5.3 said `approve` for `publicVariable` and project `exec` while the CSV said `allow`. §5.3 now matches the CSV and
  gives the reason.

**Missed items added (5 CSV rows, 105 → 110).** `setFlagTexture` (named in §3.2 but had no row);
`triCheatStorePosition` (clipboard write); `triFontTune` (TTF from any path); `description.ext CfgRemoteExec`
(mission-set remoteExec policy, F9); `#include` in configs (raw include names in the default config preprocessor).
Existing rows were extended for: `triGet*` (chat lines, mod list: an information-leak source together with
`triHttpGet`); input-injection verbs (clipboard paste); `triReadWorkshopFile` (Windows drive-relative gap,
unverified); `triDownloadFile` and `triHttpGet` (no curl protocol limit, unverified; 255-character WinINet limit);
the harness `query` rows (`connections`, `roles`, and `download`/master-server queries on the dedicated server).
New lint rules L10 (`CfgRemoteExec`) and L11 (config `#include`), patch P9, and open questions 12–14.

**Consistency with `AGENTS.md` [I].** The policies fit the product rules: agent script text is only proposed inside
typed, undoable edits and checked by the host (§5.3 items 1, 2 and 4, "Same path as the user"); model-written script
is never sent to harness `eval`/`exec` automatically, and a kept `eval_sqf_in_preview` tool runs only after the user
presses Run (item 3); mission text and harness replies are treated as data ("Untrusted content"); no rule gives the
agent shell, filesystem or network reach, and every internet-egress command is `deny` for the agent. One tension to
watch: Preview of a downloaded mission can itself cause outbound traffic (`triHttpGet`), which the agent did not cause
but the user may not expect; the §5.2 Preview gate and its "full rights" warning cover this.

**Still unverified.** Runtime linkage of the unconditional modules into the shipped client and server; libcurl's
enabled protocols; WinINet cookie behaviour; UNC and drive-relative path handling on Windows; persistence of
`triBindAction`/`triSetVolume`/`triSetLanguage`; whether every mission config parse uses the preprocessing path; the
1.99 availability of the §3.9 commands (partly settled since; see the consolidation pass below). Most have a harmless
probe in §7; the Windows path cases belong in the F3 probe (question 3).

### Consolidation pass (2026-09-27)

Applied doc 35 §10's correction for this doc; evidence checked in doc 35 §5.8, §5.9, §8.1–§8.3, its verification
notes ("20 of the 30 names doc 24 marks '1.99: likely' are observed") and, row by row, in
`data/cwa199-observed-commands.csv`. Nothing was re-read in the engine source.

- **Dialect column upgraded.** CSV rows for the 20 observed `likely` commands, `cheatsEnabled` and `debugLog` now say
  "observed in official content per doc 35"; `loadFile` says "used only by CWE content; name in the 1.99 exe (T2)";
  `endGame` adds "absent from the 1.99 exe". Doc 35 names "the status and pool families" loosely: `deleteIdentity`,
  `clearWeaponPool` and `clearMagazinePool` are not observed, so they stay `likely`. Text: §3.9 (new bullet), F5,
  TL;DR, header note, §2 step 4, §5.5, open question 8 and "Still unverified" above.
- **New risk entry F10** (non-literal numerics in config and SQM files evaluated at load, [V code; I impact]): §3.1
  F10, TL;DR, §2, §5.2 scope and new rule L12, §5.3 item 2, open question 15, §8, and a new CSV row (110 → 111).
- **Also noted, from the same doc 35 sections:** the `EndGame` global-variable name hazard in F5.
- **Not applied (flagged in §3.9):** doc 35 §8.2's string-scan results for rows the correction did not name
  (`for`, `publicExec`, `publicVariableArray`/`String`, `onPlayerConnected`, the `setWaypoint*` family, `VBS_*`
  absent; `preprocessFile`, `createDialog`, `buttonSetAction`, `onMapSingleClick`, `while`, `setObjectTexture`
  present). They wait for the `exe_199_string` column (doc 35 rc90).
- No "Field Manual", "Boot camp" or "Academy" reference, and no link to doc 33 or `skills/field-manual`, exists in this
  doc or its CSV, so the feature rename needed no edit here. The working copy's CRLF line endings were normalised to
  LF, matching the index.

### Owner answers (2026-09-27)

- 2026-09-27: folded the owner's answers by pointer to [D035](../decisions/D035-outreach-and-security-disclosure.md)
  (OWQ-09 (a), OWQ-11 (a)) in the Disclosure note, §6's lead-in and open question 10; no finding, rule, patch or
  recommendation changed, and nothing has been sent yet.
