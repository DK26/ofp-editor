# Script Tooling: the DK26/CWR Poseidon LSP and Linter, and Our SQF/SQS Catalog and Checker

Research date: 2026-09-26; fact-checked and corrected 2026-09-27 (see "Verification notes" at the end). This document is for contributors and LLM coding agents, and it stands alone.

It evaluates the Rust "Poseidon" language server and linter in the project owner's public fork `DK26/CWR` for reuse. It then specifies what our own
script engine must do: a per-dialect command catalog, a syntax and type checker, check-only validation of editor fields, gating of AI-proposed
script text, and lowering of the campaign condition language (doc 19 §5).

## TL;DR

- **What it is.** One commit (`20e3334de0`, 2026-06-27) adds a standalone `lsp/` Cargo workspace (41 files, +13,905 lines) with four crates:
  - `poseidon-catalog`: a JSON command table plus type bitmasks;
  - `poseidon-syntax`: lexers, a type-only precedence checker and a reference oracle;
  - `poseidon-lsp`: a `tower-lsp` server;
  - `poseidon-cli`: the `poseidon-check` linter.

  The engine tree is untouched. It is about 4.75k lines of Rust (3.75k under `src/`, 1.0k under `tests/`) with 92 tests, GPL-3.0-or-later. [V, §1]
- **The core idea is right and worth keeping.** Model the engine's check-only evaluator as type algebra:
  - operand types are `GameType` bitmasks;
  - an overload matches when `arg & operand != 0`;
  - the result is the union of the matching return types, and an empty union is an error.

  This mirrors `VyhCast`. Surrounding it are an independent oracle, differential fuzzing, engine-verdict vectors and a source-completeness scan. [V, §2, §9]
- **The catalog is not a clean "extracted" table, and nothing in the repo regenerates it.** Against what CWR 3.05 actually registers (555 unique signatures, 524 names; the raw tables list 560/529, but 5 debug rows sit under `#if _ENABLE_CHEATS`, which `PoseidonPCH.hpp` hard-defines to 0):
  - it misses `voiceLanguage`, added in 3.03;
  - it contains 26 signatures the game never registers: two macro artifacts (`commandxxx`, `doxxx`), 19 rows from the **mock** `EvalState.cpp` host used by the standalone evaluator (`diag_log`, `str`, `toArray`, `toString`, `setVariable`, `getVariable`, `enableSimulation`, unary `createVehicle [...]`, …), and 5 compiled-out cheat commands (`DBG_switchLandscape`, `DBG_screenshot`, `diag_drawmode`, `diag_toggle`, `diag_enable`);
  - entries carry no dialect or version tag.

  The fork's own CI went red on the 3.05 merge (Test step). [V, §3]
- **It is not the 1.99 dialect.** The released source is the Remastered engine. It registers Arma-era commands (`for`, `exitWith`, `remoteExec`, `parseSimpleArray`) and accepts Arma 3 `private _x = …` syntax. Per the BI wiki, 38 of its command names were first introduced in OFP: *Elite* (Xbox). Only `find`, `setPosASL` and `getPosASL` of those are also tagged `ofp 1.99`. The fork's "classic 2001 dialect" claim therefore does not hold for `Cwa199`. [V wiki tags; I conclusion, §4]
- **Editor-field semantics are missing.** The original editor validates each field with one of three check modes:
  - `CheckExecute`: every statement must yield Nothing, and assigning Nothing is an error;
  - `CheckEvaluateBool`: the result must be Bool;
  - in both modes, a top-level `,` is an error and `{…}` bodies are not checked.

  The fork models none of this. It also skips `?cond : stmt` SQS lines entirely, accepts `//` comments in SQS (not preprocessed), ignores the 4095-byte SQS line cap, and does not resolve `goto` labels. [V, §5-§6]
- **ParamFile support is a token lexer plus a class outline.** It does not parse values, is not lossless and cannot round-trip. Doc 07's planned lossless `ofp-config` CST remains necessary. [V, §7]
- **AGENTS.md gap.** The code has no `unsafe`, but:
  - `expect`/`panic!` on embedded JSON, plus an `unreachable!()` in the shipped oracle;
  - about 60 direct-indexing expressions in production code;
  - stringly `kind`/`ret` fields;
  - no `Error` enum;
  - edition 2021;
  - CI runs no clippy or fmt;
  - tests lack doc comments. [V, §10]
- **Recommendation: port and restructure. Do not depend on it.**
  - Move the proven algorithms (type algebra, precedence table, checker, oracle and fuzz harness, engine vectors, doc corpus) into new crates in our workspace, rewritten to AGENTS.md. The owner wrote the code, and both projects are GPL-3.0-or-later.
  - Replace the hand-made JSON with a **generator**. It reads pinned CWR release snapshots and CE, joins BI-wiki `since` data (and optionally an owner-local scan of the 1.99 executable), and emits per-overload availability for `Cwa199` / `Cwr` / `Ce` profiles.
  - Add engine-parity field checking, a faithful SQS line model, and structured, LLM-oriented diagnostics.
  - Keep the LSP optional; the editor embeds the library. [I, §13-§15]

## 0. Scope, pins, legend

Pins:

- `DK26/CWR@6fd6ca3974` — the fork (`main`), a merge of BI 3.05 into the fork;
- `CWR@ffc61838b7` — `BohemiaInteractive/CWR` release "3.05";
- `CE@b67bf3bd62` — `ofpisnotdead-com/CWR-CE`.

Engine files in `DK26/CWR@6fd6ca3974` are byte-identical to `CWR@ffc61838b7`: `git diff --stat ffc61838b7 6fd6ca3974` lists only `lsp/**` and `.github/workflows/poseidon-lsp.yml`. Engine citations therefore use `CWR@ffc61838b7`. BI release snapshots are plain commits titled `3.01` (`fdc9596`), `3.03` (`a15f184`) and `3.05` (`ffc6183`). The upstream repo has no git tags. [V]

Legend: **[V]** verified against the cited code or a fetched source; **[I]** inferred; **[U]** unknown. Nothing was built or run. Behavioural statements about the fork come from reading its code and tests.

Numbers marked "scan" come from a PowerShell regex pass over the registration macros. It expanded `TABLE_COMMAND`/`TABLE_COMMAND_S`, normalised `MockGame*` to `Game*` and compared `(lowercase name, kind, argument types)` keys. Registration sites: `engine/Evaluator/express.cpp`, `engine/Poseidon/Game/Commands/GameStateExt.cpp` and `engine/Poseidon/World/Scene/SceneDraw.cpp`. `engine/Evaluator/EvalState.cpp` is kept separate as "host"; it is linked into the engine library but its `RegisterEvalCommands()` is called only by `EvaluatorHost` (`EvaluatorHost.cpp#L88`). The `GameStateExt*Test*.cpp`/`ServerTest` files register only `tri*` harness commands and are excluded. Rows inside `#if _ENABLE_CHEATS` (`GameStateExt.cpp#L1173-L1176`, all of `SceneDraw.cpp#L469-L555`) are compiled out: `PoseidonPCH.hpp#L44` defines `_ENABLE_CHEATS 0` unconditionally and is the target's precompiled header (`engine/Poseidon/CMakeLists.txt#L181`). Counts were independently recounted on 2026-09-27.

## 1. What the fork adds

| Item | Evidence |
| --- | --- |
| One authored commit, "Add Poseidon LSP + linter for classic Arma: Cold War Assault resources", 2026-06-27; later only upstream merges | `git log` of the unshallowed clone [V] |
| 41 files, +13,905 lines; `commands.json` alone is 6,560 lines | `git show --stat 20e3334` [V] |
| Separate `lsp/` workspace (not a member of the root `Cargo.toml`), edition 2021, `rust-version = "1.80"`, `license = "GPL-3.0-or-later"`. `repository` points at CWR-CE, not the fork | `DK26/CWR@6fd6ca3974:lsp/Cargo.toml#L10-L24`, `Cargo.toml#L1-L9` [V] |
| README claims: "600 registered command overloads (525 unique names)", completion of "all 493 identifier-form commands", "92 tests" | `DK26/CWR@6fd6ca3974:lsp/README.md#L19,L28,L93` [V] |
| Actual data: 612 rows, 537 unique names (case-insensitive), 522 identifier-form names; 275 unary / 281 binary / 56 nular. The README counts are stale; the commit message says 612 | scan of `lsp/crates/poseidon-catalog/data/commands.json` [V] |
| VS Code client with TextMate grammars; a vendor-neutral agent skill (`skills/poseidon-scripting/SKILL.md`) | file list [V] |
| CI: ubuntu-only build + test + lint of one fixture mission + export of the doc corpus as `validate_ref` JSON; no clippy, no fmt | `DK26/CWR@6fd6ca3974:.github/workflows/poseidon-lsp.yml#L24-L58` [V] |

## 2. Architecture

### 2.1 Crates and dependencies

| Crate | Role | Runtime deps | Notes |
| --- | --- | --- | --- |
| `poseidon-catalog` | `Command {name, kind, ret, args, origin, prio, src}` (all string-typed: `String`, `Vec<String>`, `Option<String>`); type bitmasks; priority ordinals; authored docs | `serde`, `serde_json`, `once_cell` | JSON embedded with `include_str!`, parsed lazily with `.expect()` (`src/lib.rs#L195-L237`) [V] |
| `poseidon-syntax` | `sqf.rs` lexer, `check.rs` checker, `oracle.rs` reference evaluator, `config.rs` ParamFile lexer + class outline | catalog only | Byte-offset spans; `pub mod oracle` ships in the library, not test-only (`src/lib.rs#L10-L16`) [V] |
| `poseidon-lsp` | binary-only `tower-lsp` 0.20 server | `tower-lsp`, `tokio` (full), `dashmap` | `ropey` is declared in the workspace but unused [V] |
| `poseidon-cli` | lib + `poseidon-check` binary: files/dirs/stdin, `--json`, `--strict`, `sig`, `export-ref` | `serde_json` | Same checker as the server [V] |

`Cargo.lock` has 97 packages, most pulled in by the LSP binary. The two core crates depend only on serde/serde_json/once_cell. They are cheap to embed. [V]

### 2.2 Lexer

- Byte-based. Identifiers are `[A-Za-z_][A-Za-z0-9_]*` and case-insensitive. Strings use `""` doubling. Numbers are decimal/scientific, `0x` and `$` hex. An unterminated string is closed at end of line to aid recovery. [V: `DK26/CWR@6fd6ca3974:lsp/crates/poseidon-syntax/src/sqf.rs#L151-L174,L224-L264`]
- Token kinds are *classified* during lexing (`Command`, `Keyword`, `LocalVar`, `GlobalVar`, …) by catalog lookup (`sqf.rs#L310-L326`). Whitespace is not tokenised, and unknown bytes (including SQS `:`) are consumed without a token (`#L350-L365`). The stream is therefore **not lossless**. [V]
- Preprocessor directive lines become one opaque `Macro` token in **both** dialects (`#L123-L130`). `//` and `/* */` comments are accepted everywhere (`#L153-L154`). [V]

### 2.3 Checker and oracle

- **`check.rs`** is a recursive precedence climber. It computes a *type mask* per expression, never an AST (`src/check.rs#L221-L240,L268-L395`).
  - Overload resolution is `arg_bits & operand != 0`, with the union of return types; an empty union is an error (`#L397-L443`).
  - Variables get `VALUE_MASK`, i.e. "any value", so they never trigger a type error (`#L284-L309`).
  - A `{…}` block has type STRING, and the checker **recurses into it** (`#L337-L344`). [V]
- **Priorities** come from the `GamePriority` ordinals (`poseidon-catalog/src/lib.rs#L87-L115`). The fork takes the *minimum* over a name's overloads. The engine instead keeps the priority of the **first** registration of a name (`CWR@ffc61838b7:engine/Evaluator/express.cpp#L2243-L2258`), and likewise keeps only the first nular (`#L2217-L2226`). Both rules give the same result today because the core table in `express.cpp` registers first. [V code; I equivalence]
- **Assignments** are detected by any top-level `=`, and the left side is skipped unchecked (`check.rs#L177-L183`). [V]
- **`oracle.rs`** is a separate iterative priority-stack transliteration of `Vyhod`/`VyhCast`, used as an independent oracle (`src/oracle.rs#L1-L11`). It **shares the lexer and the catalog** with the checker (`#L13-L15`). Differential testing therefore catches parser disagreements, but not catalog or lexer errors (common mode). [V; I consequence]
- **Error recovery.** Every semantic finding is a `Warning` (`check.rs#L156-L158`). Parsing resynchronises at `;` or the closing delimiter and always makes progress (`#L161-L198`). The engine, by contrast, stops at the **first** error and reports a caret offset (`express.cpp#L2988-L3011`). [V]
- **No incremental parsing.** The LSP uses `TextDocumentSyncKind::FULL` (`poseidon-lsp/src/main.rs#L284-L286`) and re-lexes the whole document for every hover or semantic-token request (`#L354-L396`). [V] This is fine at SQS/SQF sizes. [I]

## 3. The command catalog: provenance and coverage

### 3.1 How it was produced

- The README and module docs say "mechanically extracted from the engine source" (`poseidon-catalog/src/lib.rs#L1-L6`). **No extractor script is committed** anywhere in `lsp/`. [V: file list] Regeneration after an upstream release is therefore manual. [I]
- The guard is `tests/completeness.rs`. It walks `engine/`, skips `*Test*`/`*Tri*` files, regex-matches `Game(Nular|Function|Operator)(…, "name"` and `TABLE_COMMAND(_S)`, and asserts that every **name** is known (`#L24-L86`). It checks names only, not arity, types or priority. It is skipped when `lsp/` is not inside a CWR checkout (`#L41-L45`). [V] It does not evaluate `#if` blocks, and its `TABLE_COMMAND` regex also matches the macro *definitions* (`#L48`, `#L69-L76`), so the guard itself demands the cheat-gated and `commandxxx`/`doxxx` rows (§3.2). [V code]

### 3.2 Coverage against the real registration tables (scan)

| Set | Unique signatures | Unique names |
| --- | --- | --- |
| CWR 3.05 game tables as registered (express + GameStateExt; `_ENABLE_CHEATS` rows excluded) | 555 | 524 |
| CWR 3.05 raw table rows incl. the 5 cheat-gated rows (2 in GameStateExt, 3 in SceneDraw) | 560 | 529 |
| CE@b67bf3bd62 game tables as registered (raw: 559 / 528) | 554 | 523 (no public `endGame`; CE renamed it `triEndGame`, harness-only: `CE@b67bf3bd62:engine/Poseidon/Game/Commands/GameStateExtTestAudio.cpp#L2996`; otherwise identical to 3.05) |
| Mock evaluator host (`EvalState.cpp`) | 72 rows | — |
| Fork catalog | 580 (612 rows; 32 host rows repeat a GameStateExt signature with different `src`/`origin`, none byte-identical) | 537 |

Catalog = 555 − 1 + 26:

- **Missing (1):** the `voiceLanguage` nular. It was added in release 3.03 (`a15f184`; `CWR@ffc61838b7:engine/Poseidon/Game/Commands/GameStateExt.cpp#L908`). The fork's extraction commit has parent `366f95f` (pre-3.01), whose command tables are identical to 3.01. [V: scan of each snapshot] The fork's CI failed at the merge commit `6fd6ca3974` in the Test step. [V: GitHub Actions API] `completeness.rs` must fail on `voiceLanguage` by construction [V code]; whether other tests failed too is unknown (the logs need auth).
- **Cheat-gated (5):** unary `DBG_switchLandscape`, `DBG_screenshot`, `diag_drawmode`, `diag_toggle` and binary `diag_enable`. They sit inside `#if _ENABLE_CHEATS` (`GameStateExt.cpp#L1173-L1176`, `SceneDraw.cpp#L469-L555`) and `_ENABLE_CHEATS` is 0 in every build (§0), so no build registers them. The catalog lists all five with `src` `GameStateExt.cpp`/`SceneDraw.cpp`. [V]
- **Macro artifacts (2):** unary `commandxxx` and `doxxx`. They come from the *definition* of `TABLE_COMMAND_S` (`GameStateExt.cpp#L365-L371`), not from a use of it. See `commands.json#L1309-L1317,L2019-L2027`. [V]
- **Mock-host signatures (19).** `EvalState.cpp` is the stub host behind the standalone `PoseidonEvaluator` tool (`CWR@ffc61838b7:apps/tools/Evaluator/Cli/main.cpp#L8,L59`), not the game. It registers:
  - 7 names the game does not have at all: `diag_log`, `str`, `toArray`, `toString`, `setVariable`, `getVariable`, `enableSimulation` (`CWR@ffc61838b7:engine/Evaluator/EvalState.cpp#L194-L200,L691-L692,L700`);
  - 11 wider or Arma-style overloads of real names:
    - unary `createVehicle [...]` and `createUnit [...]` (`#L494-L495`);
    - unary `countType` and `exitWith`;
    - `isNull ANY`;
    - `removeAction` with an ARRAY argument;
    - `join` OBJECT×GROUP;
    - `globalChat`, `sideChat`, `groupChat` and `vehicleChat` with an ANY left operand;
  - 1 harmless subset: `side OBJECT`.

  Because the checker unions all overloads, it **accepts** `diag_log "x"`, `str 5` and `createVehicle ["M1A1", …]`. The game rejects them. [V code; I behaviour]
- **Provenance errors.** Deduplication kept some host rows and dropped their game twins: 21 real game signatures (20 names) survive *only* as `EvalState.cpp`/`host` rows, including `player`, `west`, `east`, `time`, `hint`, `format`, `exit`, `exec` and `isServer`. Binary `call` carries the host return type VOID instead of `express.cpp`'s ANY (`express.cpp#L1149`). Hover shows these as "host" commands. [V]

### 3.3 What an entry carries

`name`, `kind` (string), `ret` and `args` (GameType strings such as `GameObjectOrArray`), `prio`, `origin` (`core`/`engine`/`host`) and `src` (a file name, no line). **Missing:**

- dialect or version availability;
- the source line;
- a per-overload `since`;
- deprecation, locality or side-effect notes.

Types are parsed from strings at every lookup (`type_bits`, `lib.rs#L68-L85`). An unknown type name maps to `u32::MAX`, i.e. "matches anything" (`#L77-L78`). That is safe against false positives but silently weakens checking. [V]

## 4. Dialect reality: the source is Remastered, not 1.99

Evidence from the BI Community Wiki MediaWiki API (`community.bistudio.com/wikidata/api.php`, `prop=revisions`, the `{{RV|type=command|gameN=|versionN=}}` header). All fetched 2026-09-26. [V]

| Command / syntax | Registered in CWR 3.05 | Wiki first-introduction tags |
| --- | --- | --- |
| `for … from … to … do` | yes (`express.cpp#L1195`) | `arma1 1.00` (no OFP tag) |
| `exitWith` | yes (`express.cpp#L1139`) | `arma1 1.00` |
| `parseSimpleArray` | yes (`express.cpp#L1191`) | `arma3 1.68` |
| `remoteExec`; `netId`/`objectFromNetId` | yes (`GameStateExt.cpp#L1228`, …) | `arma3 1.50`; `arma3 0.50` / `arma2oa 1.63` |
| `isJIP`, `publicExec`, `serverPause`, `boolEq`, `substr`, `sizeofstr`, `VBS_*` | yes | no wiki page [U: CWR additions, or undocumented OFP/VBS lineage] |
| `createGroup`, `createCenter`, `createTrigger`, `addWaypoint`, `setDate`, `setMarkerText`, `setVectorUp`, `onPlayerConnected`, … | yes | `ofpe 1.00`, then `arma1`; no `ofp` tag |
| `find`, `setPosASL`, `getPosASL` | yes | `ofpe 1.00` **and** `ofp 1.99` (for `getPosASL` as a trailing `game7=` entry; `acemod/arma3-wiki` `dist` agrees: `since.flashpoint` 1.99) |
| `getWorld` | yes (`GameStateExt.cpp#L907`) | `ofp 1.99` (OFP-only) |
| `while`, `if`/`then`/`else`, `call`, `comment`, `addEventHandler`, `preprocessFile` | yes | `ofp 1.85` |
| `in`, `count`, `select`, `forEach`, `format`, `goto`, `exec`, `private`, `mod`, `abs` | yes | `ofp 1.00` |
| `private _x = value` shorthand | accepted by `CheckAssignment`/`PerformAssignment`, whose code comment calls it "modern-SQF style" (`express.cpp#L2664-L2699,L2828-L2837`) | Arma 3 idiom [I: not 1.99] |

- **Category sizes** (2026-09-26): "Introduced with Operation Flashpoint version 1.00" has 258 pages, 1.75 has 62, 1.85 has 18, 1.99 has 2 (`getWorld`, `isServer`). The other twelve OFP version categories (1.04 to 1.90) total 43 pages, and the unversioned category holds 16. Categories can include non-command pages. "Introduced with Operation Flashpoint: Elite version 1.00" has 108. [V]
- **The Elite overlap** (scan against the Elite list): 38 of those 108 names are registered by CWR 3.05, and only `find`, `setPosASL` and `getPosASL` carry an extra `ofp 1.99` tag. The released engine therefore descends from a code line that includes Elite-era commands. A table taken straight from source would let about 35 non-1.99 commands into `Cwa199` output. A tag can sit anywhere in the `gameN` list, so the generator must read all of them, not just `game1`/`game2`. [V tags; I conclusion; must be confirmed on a 1.99 install, §14.3]
- **Overload granularity.** Wiki pages list syntaxes as `|sN=` with `|sNsince=` and per-syntax `|pN=`/`|rN=` types. For example, `in` has `s3since=arma3 0.50`, `s4since=arma3 1.96` and `s5since=arma3 2.02`. [V] Availability therefore has to be tracked **per overload**, not per name.
- **Answers for doc 19 §5.4.** The `[U]` for `in` and `count` in 1.99 now has wiki evidence (`ofp 1.00` for the base syntaxes). A 1.99 probe should still confirm it (§14.3). [V wiki; U runtime]

## 5. SQS and SQF: engine behaviour vs the fork

Engine facts are from `CWR@ffc61838b7:engine/Poseidon/Game/Scripting/Scripts.cpp` and `engine/Evaluator/express.cpp`. The 1.99 behaviour is assumed to be the same unless noted. [I]

| Rule (engine) | Source | Fork | We need |
| --- | --- | --- | --- |
| An SQS file is read raw (`QIFStreamB::AutoOpen`), **no preprocessor**, so `//`, `/* */` and `#define` have no special meaning | `Scripts.cpp#L148,L165-L172` | Treats comments and `#define` as trivia in SQS (`sqf.rs#L123-L154`) [V] | Flag `//` in SQS. Treat `#anything` as a label |
| Physical lines go into a 4096-byte buffer, and the excess is **silently dropped** (4095 usable); leading spaces are skipped | `Scripts.cpp#L97-L122,L169` | Not modelled | Error at ≥4096 bytes (doc 19 F7) |
| Line sigils: empty or `;` = comment; `#` = label (trimmed); `&t` = absolute wait; `~t` = relative wait; `@c` = wait until; `?c : s` = conditional; anything else = statement | `Scripts.cpp#L228-L334` | Lexes `; # ~ @ & ?` at line start (`sqf.rs#L131-L150`) [V] | Faithful port of `ProcessLine` into a typed `SqsLine` enum |
| `~t` expands into a **256-byte** `snprintf` buffer, `"__waituntil = _time+(%s)"`, so long delay expressions are truncated | `Scripts.cpp#L263-L280` | Not modelled | Warn when `t` exceeds 233 bytes (256 minus 22 fixed characters and the NUL) |
| `?` splits at the **first** `:` (`strchr`), even inside a string. With no `:`, the line is dropped with a log "Only one field" | `Scripts.cpp#L292-L317` | **Skips `?` lines entirely**: neither the condition nor the statement is checked (`check.rs#L99-L101`) [V] | Split like the engine; error on `:` inside a condition string (doc 19 F6) |
| `@c` and `?c` are evaluated with `EvaluateBool`; `&t` with `Evaluate` into a number; `~t` becomes an `Execute`d statement `__waituntil = _time+(t)` plus an `Evaluate` of `__waituntil`; statements with `Execute` | `Scripts.cpp#L263-L280,L443-L470` | Checks `@`/`~`/`&` bodies as untyped expressions (`check.rs#L102-L104`) | Require Bool, Scalar or statement context per sigil |
| `goto` does a case-insensitive label search; an unknown label silently **exits** the script | `Scripts.cpp#L552-L564` | Not modelled | Resolve literal `goto "x"` targets; warn on dynamic ones |
| Statements separate on `;`. A top-level `,` is accepted at run time but rejected in check mode | `express.cpp#L2761-L2765,L2974-L2977,L1661-L1671` | Always warns `EvalSemicolon` and skips the rest of the statement unchecked (`check.rs#L184-L197`) [V code] | Error in editor fields; warning in scripts |
| Expression stack depth `SL = 256`, above which you get `EvalLineLong` | `express.hpp#L446`, `express.cpp#L1591-L1595` | Not modelled | Boundary test and lint |

For SQF, `.sqf` code runs only as strings, via `call` (and `preprocessFile`/`loadFile`) (doc 04 §8). `preprocessFile` preprocesses and `loadFile` does not. The fork always assumes a preprocessor. Our checker must take the *load path* as context. [V doc 04; I]

## 6. Editor fields: what the original editor checks

The original editor checks each field when its dialog closes. On error it shows the engine's message and moves the caret to the error offset. [V]

| Field | Check | Source |
| --- | --- | --- |
| Unit `init` | `CheckExecute` | `CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcade.cpp#L1103-L1113` |
| Unit presence condition | `CheckEvaluateBool` | `UIArcade.cpp#L1115-L1125` |
| Trigger condition / on activation / on deactivation | `CheckEvaluateBool` / `CheckExecute` / `CheckExecute` | `UIArcade.cpp#L1714-L1750` |
| Waypoint condition / on activation | `CheckEvaluateBool` / `CheckExecute` | `UIArcadeWaypoint.cpp#L331,L343` |
| Two further menu dialogs | `CheckExecute` / `CheckEvaluate` | `DisplayUIMenus.cpp#L1661,L1747` |

Check-mode semantics (`_checkOnly`). The fork implements none of the first five. [V code; I fork gaps]

1. **`CheckExecute` → `Execute`.** Each non-assignment statement must yield a type that includes Nothing, or the engine raises a TypeError (`express.cpp#L2958-L2966`). In an init field, `alive player` or `1+1` is therefore an error.
2. **`CheckEvaluateBool` → `EvaluateMultiple` + `EvaluateBool`.** Every statement except the last must yield Nothing, and the final value must include Bool (`#L2715-L2724,L2773-L2782`). A condition of `player` is an error.
3. **Assignments.** A right-hand side of type Nothing is an error, and a fake type (`if`/`while`/`for` values) is an error (`#L2889-L2900`). `x = hint "a"` fails.
4. **`{…}` code is an opaque STRING** (`Const`, `#L257`). The editor does **not** check the inside of `then {…}` bodies. The fork's recursion is *stricter* than the editor, which is useful, but it is a different verdict level.
5. **In check mode a global variable evaluates to `GameVoid`** (any value; `#L216-L219`), and **commands win over same-named variables** (`#L195`, `#L1624`, `#L1806`). The fork's "unary command without operand = variable" deviation (`check.rs#L376-L381`) matches run time (where a set variable hides the command) but not check mode. [V code; I verdict]

A local `_x` outside `{…}` needs a local variable space (`#L183-L193`); with none, `Const` raises `EvalNamespace` (`#L185-L190`). The game state's base context is created with a null space (`GameState::GameState` → `BeginContext(nullptr)`, `#L2304-L2309`), and the dialogs call `CheckExecute`/`CheckEvaluateBool` directly on `GWorld->GetGameState()` (`UIArcade.cpp#L1101-L1118`). So a bare `_x` in an editor field most likely fails with `EvalNamespace`. [V code; I: assumes no other context is active when the dialog closes; confirm with an upstream test or a probe] What an unset `_x` yields when a space *does* exist (scripts) is still **[U]**.

## 7. ParamFile (`.sqm`, `.ext`, `.cfg`)

- `config.rs` provides a lexer (strings, numbers, `#` directives, comments, brace balance) and a `symbols()` class-tree outline for document symbols (`src/config.rs#L19-L224,L239-L313`). [V]
- **No value parser:** there is no array, member or `enum` model. Output is not lossless and not round-trippable. Class keywords are found by byte scanning, so `"class"` inside a string or comment can create a phantom symbol (`#L246-L313`). [V code; I effect]
- **No semantic checks:** no inheritance, duplicate or schema checking; the roadmap lists these (`README.md#L155-L162`). There is no binarized raP support. Embedded SQF in `.sqm` fields (`init=`, `condition=`, `expActiv=`, …) is **not extracted or checked**. [V]
- **Verdict:** reuse nothing here. Doc 07 §17's clean-room lossless `ofp-config` CST is still the plan. Our script checker plugs into it per field, using the check mode from §6.

## 8. LSP and CLI features

| Feature | State |
| --- | --- |
| Diagnostics | Push on open/change; lexical *errors* + semantic *warnings*; config gets lexical only (`poseidon-lsp/src/main.rs#L262-L272`) [V] |
| Completion | A static list of every identifier-form catalog name plus signature, offered in any context. The list includes the spurious names (§3.2) (`#L155-L176`) [V] |
| Hover | Deduplicated overload signatures, "classic … {origin} command", authored docs for 65 names with 75 examples (`#L191-L230`; `data/docs.json`) [V] |
| Semantic tokens | Full only, from the lexer classification (`#L384-L396`) [V] |
| Document symbols | Config class tree (`#L398-L408`) [V] |
| Missing | Signature help, go-to-definition (labels, classes), code actions and fix-its, formatting, range tokens, incremental sync [V by capability list `#L277-L308`] |
| CLI | `path:line:col: severity[code]: message`; `--json` gives `{file, lang, ok, errors, warnings, diagnostics[{severity, code, message, start{line,col,offset}, end}]}`. Exit code 1 only on lexical errors unless `--strict` (`poseidon-cli/src/lib.rs#L159-L204`) [V] |

Diagnostic codes mix engine names (`EvalType`, `EvalOper`, `EvalOpenB`, …) with kebab-case (`unterminated-string`). Messages are free text. There are no expected/found types, candidate overloads, suggestions or fix-its. [V]

## 9. Tests

- **92 `#[test]` functions** across 18 files (grep). [V] Nothing was run here.
- **`engine_vectors.json`:** 89 expressions (80 valid, 9 error), taken from 14 upstream test and reference files (`poseidon-syntax/tests/engine_vectors.json`). No harvester is committed. [V]
  - Upstream `tests/unit/{engine,apps}/Evaluator/*.cpp` has 26 files (25 contain test cases; `test_stubs.cpp` has none), with 847 `TEST`/`SECTION` hits and 420 literal-string `Evaluate`/`Execute`/`Check*` call sites (grep). The vectors cover roughly a fifth of those call sites. [V counts; I ratio]
- **Differential fuzzing:** 8,000 expressions from 14 atoms, 10 unary and 16 binary operators; **no code blocks, no SQS, no assignments** (`tests/differential.rs#L56-L136`). [V]
- **"Live-engine parity"** runs vectors through `PoseidonEvaluator --eval`. That is **runtime** evaluation in the **mock host**, not `CheckEvaluate` against the game table. It is gated off when no binary is present, which includes CI (`tests/evaluator_parity.rs#L1-L17,L31-L35`). [V]
- **Corpus:** every shipped fixture must be clean except names containing `error`/`invalid`/`bad`, and one allow-listed placeholder (`tests/corpus.rs#L66-L82`). At 3.05 the fixture set is 10 `.sqf`, 17 `.sqs`, 13 `.sqm`, 11 `.ext` and 7 `.cfg`. [V] It skips silently outside a CWR checkout (`#L40-L44`). [V]
- **Doc gates:** every documented name must exist, and every example must lex and check clean (`docs_grounded.rs`, `doc_examples.rs`). [V]
- **Relation to AGENTS.md porting rules:** upstream tests are harvested as verdict data, not ported one-to-one with origin doc comments, and there is no test map. [V]

## 10. Code quality against our AGENTS.md

| Rule | Fork state |
| --- | --- |
| No `unsafe` | Compliant; no occurrences [V: grep] |
| No `unwrap`/`expect`/panic in production | `poseidon-catalog/src/lib.rs#L200,L228,L233` (embedded JSON); `poseidon-cli/src/lib.rs#L244`; `poseidon-cli/src/main.rs#L125`; `poseidon-syntax/src/oracle.rs#L331` (`unreachable!()` in the `pub mod oracle` library code). The rest are in tests [V] |
| No direct indexing | About 60 index/slice expressions in production code: 27 in `oracle.rs` (`#L100-L121,L262-L342`, its stack machine) and about 35 elsewhere, e.g. `sqf.rs#L59,L91,L315`, `check.rs#L43,L77,L93-L103`, `config.rs#L32,L187,L264,L277,L320,L324,L345`, `poseidon-lsp/src/main.rs#L99,L207,L370`, `line_index.rs#L28-L29,L39,L46`, `poseidon-cli/src/lib.rs#L120-L121,L284-L285`, `poseidon-cli/src/main.rs#L70-L86`, `poseidon-catalog/src/lib.rs#L75,L215` [V: regex scan of code before each `#[cfg(test)]`] |
| One `Error` enum per crate, structured fields | None. `Diagnostic { code: &'static str, message: String }` [V] |
| Type safety (enums/newtypes) | `kind`, `ret`, `args` and `origin` are `String`; priorities are `u8` ordinals [V] |
| Edition 2024, clippy `-D warnings`, fmt | Edition 2021; CI runs neither clippy nor fmt [V] |
| Module/test docs | Module `//!` docs are good. Most `#[test]` functions lack `///` what/why comments [V] |
| ~600-line files | All files are under 600 lines (largest `check.rs` 585) [V] |
| Cite upstream lines | Many comments cite `express.cpp` lines, but not pinned SHAs [V] |

## 11. Dependencies, licence, maturity

- **Licences.** The fork's workspace is GPL-3.0-or-later, matching ours (doc 02).
  - `check.rs` and `oracle.rs` are described as ports of `express.cpp`. They therefore carry upstream GPL-3.0 obligations and the Bohemia §7 additional terms that apply to translated engine code (doc 02; doc 07 TL;DR). [I]
  - The authored `docs.json` and the non-derived code belong to the owner. [I]
  - The CWR §7 terms forbid distributing modifications "using any Bohemia Interactive trademark or 'OPERATION FLASHPOINT' trademark" (`CWR@ffc61838b7:LICENSE`, "ADDITIONAL TERMS"). User-facing strings such as the hover's "classic Operation Flashpoint / Cold War Assault … command" (`poseidon-lsp/src/main.rs#L208-L211`) should not be ported verbatim; follow doc 02 for descriptive naming. [I]
  - Dependencies are permissive. `tower-lsp` is `MIT OR Apache-2.0` (its `Cargo.toml` and crates.io; GitHub's licence detector shows only Apache-2.0). Its repo was last pushed 2024-08-15, and the newest crates.io release is 0.20.0. [V: GitHub and crates.io APIs]
- **Maturity.** One authored commit and two CI runs (success at `20e3334de0`, failure at `6fd6ca3974`). The GitHub releases list is empty. [V: GitHub API] Not published on crates.io: `poseidon-catalog`, `poseidon-syntax`, `poseidon-lsp` and `poseidon-cli` all return 404 (2026-09-27). The install instructions (`lsp/skills/README.md#L28`, `SKILL.md#L36`) only give `cargo install --path`. [V]

## 12. Alternatives

| Option | Licence | Fit |
| --- | --- | --- |
| HEMTT `hemtt-sqf` (chumsky parser, lints) | `GPL-2.0` (SPDX "only"); depends on `arma3-wiki` | Arma 3 semantics; cannot link into GPL-3.0 (doc 02, doc 07). Useful as a design reference for lint UX [V: `libs/sqf/Cargo.toml`] |
| `SkaceKamen/sqflint` | MIT, Java, last push 2023-03-07 | Arma 3 syntax checking; not the OFP dialect [V: GitHub API] |
| `LordGolias/sqf` | BSD-3-Clause, Python, archived (last push 2022-04-10) | Arma 3 parser/analyser/interpreter; reference only [V] |
| `PoseidonEvaluator` (`CWR@ffc61838b7:apps/tools/Evaluator`) | GPL-3.0-or-later + §7 terms (CWR) | Real `express.cpp` over a **mock** command host (`--eval`, `--validate-ref`, SQS runner). A good opt-in local oracle for the *parser*; wrong command table for the game [V] |
| `PoseidonTools lint mission` | GPL-3.0-or-later + §7 terms (CWR) | Structural counts and "bootable" only; no script checks (`apps/tools/Tools/commands/LintCommand.cpp#L100-L141`) [V] |
| `acemod/arma3-wiki` | client crate MIT (`clients/rust/Cargo.toml`); licence of the data branch [U] | Parsed wiki data in the `dist` branch, one YAML file per command with `since: {flashpoint: {major, minor}, flashpoint_elite: …}` (e.g. `commands/setPosASL.yml`, `commands/getWorld.yml`). A cross-check for our own wiki scrape [V] |

## 13. Recommendation: how to reuse

### 13.1 Decision

- **Do not take a git dependency on `DK26/CWR`.** It would pull the whole engine repo into our build. The crates are not a stable library API (stringly types, public fields, panicking statics, no profile parameter). Their grounding tests assume they sit inside a CWR checkout and skip silently otherwise. [I]
- **Do not vendor unchanged.** The catalog is wrong for every profile (§3-§4), and the checker lacks the check-mode semantics that editor fields need (§6). [I]
- **Port and restructure (recommended).** Move the ideas and selected code into our workspace, rewritten to AGENTS.md. Keep the fork pinned as a *reference oracle* until our crates pass its tests plus the new ones. [I]

| Keep (port) | Rewrite | Drop |
| --- | --- | --- |
| Type bitmask algebra and constants; `VyhCast` overload rule; priority table; `oracle.rs` as a **test-only** crate; differential fuzz harness; engine-vector format; doc-corpus gates; CLI JSON idea | Lexer (lossless, trivia-preserving); SQS line model; typed AST with spans; check modes; catalog as generated Rust; diagnostics | JSON-at-runtime catalog; `config.rs` (superseded by `ofp-config`); LSP binary in the core path (optional later) |

### 13.2 Target layout

Crate names follow doc 07 and remain subject to its crate-prefix question.

| Crate | Owns |
| --- | --- |
| `ofp-script-catalog` | Generated `static` tables: `Overload { name, kind: Kind, ret: TypeSet, args: [TypeSet; 2], prio: Priority, availability: Availability, src: SourceRef }`. `TypeSet` is a bitflags newtype; `Profile` is `Cwa199` / `Cwr { release }` / `Ce { sha }`. Lookups are allocation-free by lowercase name. No runtime parsing, no panics |
| `ofp-script` | Lossless lexer; `SqsFile` (a faithful `ProcessLine` port); SQF statement/expression parser into an AST with spans; `check_field(FieldKind, &str, Profile) -> ParityVerdict`; `lint(Source, Context, Profile) -> Vec<Diagnostic>`; label resolution; one `Error` enum |
| `ofp-script-oracle` (dev-only) | The transliterated `Vyhod`/`VyhCast` stack machine, used only by tests |
| `xtask catalog` (not shipped) | The generator in §14, plus drift checks |
| `ofp-script-lsp` (optional, later) | A thin server over `ofp-script` for external editors. Re-evaluate `tower-lsp` against alternatives at that point [I] |

### 13.3 What must change

1. **Profiles everywhere.**
   - Availability is per overload *and* per syntax feature: `private _x =`, top-level `,` in fields, comments in SQS, `for`, `exitWith`.
   - Anything with unconfirmed 1.99 status is `Remastered-only` for `Cwa199` (conservative).
   - The linter computes the mission's "Requires: `<min version>`" badge from the highest availability actually used.
2. **Two verdict levels.**
   - **Engine parity:** what the original editor would accept. The first error only, with `EvalError` kind and caret offset, following §6 rules 1-5 exactly.
   - **Lint:** everything else, as warnings: recursion into `{…}` strings, label resolution, Arma-isms, 4 KB lines, and so on.
   - Save-time validation of fields uses parity. The AI gate and the glue generator use parity plus lint at `error` severity.
3. **Field contexts.** Map `.sqm` keys to check modes following the dialog code (§6). Every `ofp-config` field edit command runs `check_field` before commit. This is the "typed, validated, undoable command" path of AGENTS.md.
4. **Typed signatures for lowering.** The CXL compiler (doc 19 §5.4) selects overloads from `ofp-script-catalog` by `TypeSet`. It refuses anything outside `Cwa199 ∩ Cwr ∩ Ce ∩ whitelist` (C14). It re-checks every emitted SQS line with `check_field` in the right mode, and emitted text never contains a `:` inside a `?` condition string.
5. **Catalog correctness.**
   - Exclude `EvalState.cpp`; record `tri*` harness commands in a separate `harness` table for Preview (doc 08).
   - Evaluate preprocessor conditionals with the engine's own defines, so `#if _ENABLE_CHEATS` rows (`DBG_*`, `diag_drawmode`/`diag_toggle`/`diag_enable`) are dropped.
   - Expand macros only at use sites; add `voiceLanguage`; fix provenance; key priority by first registration.
6. **AGENTS.md compliance.**
   - Edition 2024, `get()`-based indexing, no `expect`, an `Error` enum, newtypes (`ByteOffset`, `LineNo`).
   - Documented tests, clippy and fmt in CI, a Windows/Linux/macOS matrix.
   - Ported upstream tests tracked in `docs/porting/upstream-test-map.csv`.

### 13.4 LLM-friendly diagnostics

The AI repair loop (doc 14 §4.4) needs machine-actionable fields, not prose. Proposed shape, versioned as `schema: 1`:

```json
{ "code": "type.binary_mismatch", "level": "parity", "severity": "error",
  "span": {"start": 7, "end": 16, "line": 1, "col": 8, "col_utf16": 8},
  "message": "`setDamage` cannot take STRING on the right",
  "expected": {"left": ["OBJECT"], "right": ["SCALAR"]}, "found": {"left": "OBJECT", "right": "STRING"},
  "candidates": ["<OBJECT> setDamage <SCALAR> -> NOTHING"],
  "profile": "cwa199", "requires": null, "did_you_mean": [],
  "arma_ism": null, "fix": null, "engine_error": "EvalType" }
```

- `requires` is set when a command exists in another profile, e.g. `"cwr-3.05"` for `for` under `Cwa199`.
- `did_you_mean` is edit distance over *profile-filtered* names.
- `arma_ism` holds curated hints such as "`distance` to a position is Arma 2+" (unverified; CWR 3.05 registers only OBJECT `distance` OBJECT, `GameStateExt.cpp#L1235`) or "`private _x = …` is not 1.99".
- `fix` is present only when mechanical, for example quoting a label.
- Codes are a Rust enum with stable string forms. Messages must never echo mission text as instructions (AGENTS.md "untrusted content").

## 14. Generating and maintaining the per-dialect catalog

### 14.1 Inputs, all pinned

1. **Engine tables at each release snapshot:** BI `3.01` `fdc9596`, `3.03` `a15f184`, `3.05` `ffc6183`, and CE at a pinned SHA. The generator parses `GameNular`/`GameFunction`/`GameOperator` rows (including multi-line rows), expands `TABLE_COMMAND`/`TABLE_COMMAND_S` at their use sites (`GameStateExt.cpp#L1171,L1358-L1360`), drops rows in inactive `#if` blocks (`_ENABLE_CHEATS` is 0, `PoseidonPCH.hpp#L44`), and resolves `|` unions. It records file and line, and applies the first-registration-wins rules for priority and nulars (`express.cpp#L2217-L2258`). It emits `present_in: {cwr_3_01, cwr_3_03, cwr_3_05, ce_<sha>}`. Our scan shows this is tractable with regexes; a real generator should use a small tokenizer over the C++ initializer lists. [V/I]
2. **BI wiki facts via the MediaWiki API:**
   - the `gameN`/`versionN` header;
   - per syntax: `sN`, `sNsince`, `pN`, `rN`;
   - category lists "Introduced with Operation Flashpoint version X" and ": Elite version 1.00".

   Store only facts (names, versions, syntax skeletons) as a dated JSON snapshot. Wiki prose licensing is **[U]**, so descriptions stay authored. Cross-check against `acemod/arma3-wiki` `dist` YAML (`since.flashpoint`).
3. **Owner-local 1.99 evidence (opt-in, gated by environment variable, never in CI).** Scan the installed CWA 1.99 executable for the command-name string literals, because registration tables are string literals in the binary. [I] Only the resulting *name list and its hash* is committed. Doc 02 should confirm that this is acceptable. [U]
4. **Probe missions** for disputed overloads. A tiny mission per candidate is run by hand on 1.99. Record the verdict with the probe's source. The CWR harness cannot drive 1.99 (doc 08). [I]
5. **`overrides.toml`:** a manual verdict per `(name, overload)` with an evidence citation. It wins over heuristics and is reviewed like code.

### 14.2 Output and rules

- A generated `catalog.rs` (static arrays), a `catalog.json` for AI retrieval (doc 14 §4.4 step 2), and a Markdown report of all conflicts.
- `Cwa199` includes an overload only if the wiki gives `ofp ≤ 1.99` for that syntax (or `ofp 1.99` explicitly) **and** it is not contradicted by the binary scan or a probe.
- Elite-only (`ofpe` without `ofp`) and Arma-tagged overloads are `Cwr`+.
- Names that are in the engine but have no wiki page stay unknown, which counts as `Cwr` until confirmed.
- The editor glue whitelist is a hand-curated subset of the intersection (doc 19 C14, "probe whitelist").

### 14.3 Maintenance

- **CI drift test:** regenerate from the pinned inputs, and fail if `catalog.rs` differs. A separate test asserts that every registration name is covered, the same idea as the fork's `completeness.rs`, but over pinned snapshots vendored as small extracted text rather than a sibling checkout.
- **Release bump:** a new BI release commit or CE bump means updating the pins, regenerating and reviewing the diff report. The fork's red CI after 3.05 is exactly the failure this process turns into a reviewed change.
- **Vector harvest:** script the extraction of all literal `Evaluate`/`Execute`/`Check*` calls with their asserted outcome from upstream Evaluator tests, from about 89 today to all 420 sites. Re-run it on each bump, and port the SQS runner tests (`test_sqs_runner.cpp`, `test_sqs_integration.cpp`) as known-value Rust tests.
- **Our own tests on top:**
  - boundaries at 4095/4096-byte SQS lines, the 256-byte `~` expansion and stack depth 256;
  - adversarial `cargo-fuzz` on the lexer and parser, since missions are untrusted input;
  - differential fuzzing that now includes `{…}`, assignments and SQS lines.

## 15. Phasing

1. **P0, catalog:** `xtask catalog` over the CWR snapshots and CE; fix the §3.2 defects; provenance report. Evidence: drift test green, completeness equal to the scan (555/524 registered for 3.05; 554/523 for CE@b67bf3bd62).
2. **P1, parity checker:** port the lexer and checker into `ofp-script` with an AST, check modes and the `SqsFile` model; port the fork's 92 tests where they still apply plus upstream vectors. Evidence: parity tests per §6 rules 1-5, SQS boundary tests.
3. **P2, dialects:** wiki snapshot, overrides and the optional 1.99 name scan; `Requires:` badge; glue whitelist wired into the CXL compiler.
4. **P3, AI and UX:** diagnostic schema v1 in the agent's `validate_script` tool, hover and completion in the in-app script editor, optional `ofp-script-lsp`.

## Open questions

1. **1.99 command set.** Does the CWA 1.99 executable contain `createGroup`, `createTrigger`, `setDate` or other Elite-tagged names? The wiki says no for 35 of the 38 (§4; it tags `find`, `setPosASL` and `getPosASL` as 1.99), and only an install scan or probe can settle it.
2. **Check-mode locals.** Code reading says a bare `_x` in an editor field raises `EvalNamespace`, because the base context has no local space (§6). A probe should confirm this. What an unset `_x` yields when a space exists (`express.cpp#L183-L193`) is still open.
3. **1.99 check semantics.** Did 1.99's `CheckExecute` already require Nothing-typed statements and reject top-level `,`, or are these CWR changes? The released source has no 1.99 history.
4. **Wiki data licence.** Can we commit a factual snapshot (names, versions, syntax skeletons) from the BI wiki or `acemod/arma3-wiki`'s data branch?
5. **Undocumented commands.** Are `boolEq`, `substr`, `sizeofstr`, `isJIP`, `serverPause`, `publicExec` and `VBS_*` CWR-era additions or older undocumented commands? This affects the `Cwr` minimum version.
6. **Harness commands.** Should the `tri*` commands (registered only with `--dev`, `--harness` or `--test-mission`; `GameStateExtTestAudio.cpp#L2960-L2966`) appear in a Preview-only profile?
7. **Fork disposition.** After P1, should the owner fix or archive `DK26/CWR/lsp` (stale README counts, red CI)? Should the vendor-neutral agent skill be re-pointed at our checker?

## Sources

Pinned code (aliases in §0):

- **Fork:**
  - `DK26/CWR@6fd6ca3974:lsp/{README.md#L10-L29,L93-L119,L155-L162, Cargo.toml#L10-L24}`;
  - `…/lsp/crates/poseidon-catalog/{src/lib.rs#L1-L115,L195-L237, data/commands.json#L1309-L1317,L2019-L2027, data/docs.json, tests/completeness.rs#L24-L86}`;
  - `…/lsp/crates/poseidon-syntax/src/{sqf.rs#L56-L70,L120-L186,L224-L264,L310-L365, check.rs#L60-L118,L156-L240,L268-L443, oracle.rs#L1-L140,L262-L342, config.rs#L19-L366, lib.rs#L10-L16}`;
  - `…/lsp/crates/poseidon-syntax/tests/{engine_vectors.json, engine_oracle.rs#L25-L89, differential.rs#L56-L136, evaluator_parity.rs#L1-L60, corpus.rs#L39-L83}`;
  - `…/lsp/crates/poseidon-lsp/src/main.rs#L99,L155-L230,L262-L408`;
  - `…/lsp/crates/poseidon-cli/{src/lib.rs#L133-L204,L240-L318, src/main.rs#L70-L86,L125}`;
  - `…/lsp/skills/{README.md#L28, poseidon-scripting/SKILL.md#L19-L36}`;
  - `DK26/CWR@6fd6ca3974:.github/workflows/poseidon-lsp.yml#L24-L58`;
  - commits `20e3334de0` and `6fd6ca3974`.
- **Evaluator:** `CWR@ffc61838b7:engine/Evaluator/express.cpp#L165-L221,L257,L1101-L1212,L1591-L1595,L1624-L1628,L1661-L1671,L1806-L1809,L2217-L2258,L2304-L2309,L2361-L2397,L2664-L2699,L2702-L2782,L2826-L2916,L2918-L3011,L3067-L3092`; `…/express.hpp#L18-L35,L446,L503`; `…/EvalState.cpp#L186-L217,L341-L355,L488-L503,L611-L624,L691-L701,L760-L763`; `…/EvaluatorHost.cpp#L88`.
- **Build configuration:** `CWR@ffc61838b7:engine/Poseidon/Foundation/PoseidonPCH.hpp#L44`; `…/engine/Poseidon/CMakeLists.txt#L115-L121,L181`; `…/engine/Poseidon/World/Scene/SceneDraw.cpp#L469-L555`.
- **Commands and scripts:** `CWR@ffc61838b7:engine/Poseidon/Game/Commands/GameStateExt.cpp#L365-L371,L853,L886,L907-L910,L930,L1171,L1173-L1176,L1217,L1228,L1235,L1237,L1287,L1358-L1360,L1470-L1503`; `…/GameStateExtTestAudio.cpp#L2960-L2966`; `…/Game/Scripting/Scripts.cpp#L97-L122,L148,L165-L172,L228-L334,L443-L470,L552-L564`; `…/Game/Commands/GameStateExtWorldConfig.cpp#L1050-L1091` (`loadFile` raw, `preprocessFile` preprocessed).
- **Editor dialogs:** `CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcade.cpp#L1103-L1125,L1714-L1750`; `…/UI/Map/UIArcadeWaypoint.cpp#L331,L343`; `…/UI/DisplayUIMenus.cpp#L1661,L1747`.
- **Tools:** `CWR@ffc61838b7:apps/tools/Evaluator/Cli/main.cpp#L8,L38-L59`; `CWR@ffc61838b7:apps/tools/Tools/commands/LintCommand.cpp#L100-L141`; upstream tests `CWR@ffc61838b7:tests/unit/{engine,apps}/Evaluator/*.cpp` and `tests/fixtures/**`.
- **Releases and CE:** release commits `fdc9596` (3.01), `a15f184` (3.03, adds `voiceLanguage`), `ffc6183` (3.05), and the 3.01→3.05 diff of `GameStateExt.cpp`/`GameStateExtUi.cpp`; `CE@b67bf3bd62:engine/Poseidon/Game/Commands/{GameStateExt.cpp#L906, GameStateExtTestAudio.cpp#L2996}`.
- **Related research:** docs 02, 03, 04 §8, 07 §11/§17, 08, 14 §4.4, 18, 19 §5.

Web sources, fetched 2026-09-26:

- **BI Community Wiki API:**
  - pages (`action=query&prop=revisions&rvprop=content&rvslots=main`): `for`, `while`, `exitWith`, `private`, `find`, `parseSimpleArray`, `forEach`, `call`, `setVariable`, `str`, `diag_log`, `toArray`, `resize`, `set`, `comment`, `getWorld`, `isJIP`, `missionStart`, `format`, `else`, `count`, `remoteExec`, `publicExec`, `netId`, `objectFromNetId`, `setVectorDir`, `getPosASL`, `onPlayerConnected`, `requiredVersion`, `loadFile`, `preprocessFile`, `playersNumber`, `VBS_addHeader`, `publicVariable`, `createVehicle`, `createUnit`, `addEventHandler`, `saveStatus`, `nearestBuilding`, `setVelocity`, `serverPause`, the 20 Elite-tagged pages checked in §4, `in`, `mod`, `abs`, `saveVar`, `boolEq`, `select`, `objStatus`, `localize`, `goto`, `exec`, `random`, `substr`, `sizeofstr`, `and`, `or`, `not`, `if`, `then`, `echo`;
  - `list=allcategories&acprefix=Introduced with Operation Flashpoint`;
  - `list=categorymembers&cmtitle=Category:Introduced_with_Operation_Flashpoint:_Elite_version_1.00`.

  Base URL: <https://community.bistudio.com/wikidata/api.php>. The plain `wiki?action=raw` endpoint returned HTTP 403.
- **GitHub API:**
  - <https://api.github.com/repos/DK26/CWR/actions/runs>, `…/runs/36251596801/jobs`;
  - <https://api.github.com/repos/SkaceKamen/sqflint>, <https://api.github.com/repos/LordGolias/sqf>, <https://api.github.com/repos/ebkalderon/tower-lsp>, <https://api.github.com/repos/acemod/arma3-wiki>, `…/contents/?ref=dist`.
- **Raw files:** <https://raw.githubusercontent.com/BrettMayson/HEMTT/main/libs/sqf/Cargo.toml>; <https://raw.githubusercontent.com/acemod/arma3-wiki/main/{Cargo.toml,README.md,clients/rust/Cargo.toml}>; <https://raw.githubusercontent.com/acemod/arma3-wiki/dist/commands/{setPosASL.yml,getWorld.yml}>.
- **Unreachable on 2026-09-26:** crates.io API (DNS failure). Reached on 2026-09-27: <https://crates.io/api/v1/crates/tower-lsp> and `…/crates/poseidon-{catalog,syntax,lsp,cli}` (404).
- **Added 2026-09-27:** wiki `list=categorymembers` for `Category:Introduced_with_Operation_Flashpoint_version_1.99`; the full `getPosASL` page header; <https://raw.githubusercontent.com/acemod/arma3-wiki/dist/commands/getPosASL.yml>; <https://raw.githubusercontent.com/ebkalderon/tower-lsp/master/Cargo.toml>; <https://api.github.com/repos/DK26/CWR/releases>.

## Verification notes

Adversarial fact-check, 2026-09-27, against the same pinned clones (`CWR@ffc61838b7`, `CE@b67bf3bd62`, `DK26/CWR@6fd6ca3974`) and live web APIs. Nothing was built or run.

**Recounted and confirmed.**

- Fork commit `20e3334de0`: 2026-06-27, 41 files, +13,905 lines, `commands.json` 6,560 lines. Parent `366f95f`; the only later commit is the merge. Engine files are identical to 3.05 and neither repo has tags.
- Catalog: 612 rows, 580 signatures, 537 names, 522 identifier-form names, 275/281/56 by kind. README counts (600/525/493/92) are stale as described.
- Registration sites: a whole-tree search for `GameNular(`/`GameFunction(`/`GameOperator(` finds no site besides express.cpp, GameStateExt.cpp, SceneDraw.cpp, EvalState.cpp and the `tri*` test files. Raw table counts 560/529 (CE 559/528, differing only by `endGame`) match the original scan.
- Catalog defects: exactly 1 missing signature (`voiceLanguage`) and the 21 listed extras (2 macro artifacts, 7 host-only names, 11 wider host overloads, 1 subset).
- `EvalState.cpp` is mock-only: `RegisterEvalCommands()` has a single caller, `EvaluatorHost.cpp#L88`.
- SQS: 4096-byte buffer with 4095 usable bytes and silent truncation; `~` 256-byte `snprintf` with 233 usable bytes; `?` split with `strchr` and the "Only one field" drop; case-insensitive `goto` that exits on an unknown label; raw `AutoOpen` with no preprocessor. `loadFile` is raw and `preprocessFile` preprocesses.
- Check modes: `CheckExecute`/`CheckEvaluateBool`/`CheckEvaluate` at the cited `UIArcade.cpp`, `UIArcadeWaypoint.cpp` and `DisplayUIMenus.cpp` lines, and the rule-1 to rule-5 semantics in `express.cpp`.
- Priority: the engine keeps the first registration and the fork takes the minimum. They coincide because `==`/`!=` are registered as comparison in express.cpp before GameStateExt re-registers them as function.
- Fork code at the cited lines: lexer, checker, oracle, LSP capabilities, CLI, 92 tests in 18 files, 89 vectors (80/9) from 14 files, fuzz parameters, corpus rules, fixture counts, 65 documented names with 75 examples, 97 lockfile packages, unused `ropey`, edition 2021, no `unsafe`, largest file 585 lines.
- Upstream Evaluator tests: 847 `TEST`/`SECTION` hits and 420 literal call sites.
- Web: CI runs (success, then failure in Test), empty releases, `sqflint`/`LordGolias/sqf`/HEMTT licences and dates, the wiki tags in the §4 table, the category sizes, and the `in` `sNsince` values. All 38 Elite-overlap pages were checked through API summaries.

**Corrected.**

- 5 table rows are compiled out by `_ENABLE_CHEATS 0`. The game therefore registers 555/524 (CE 554/523), and the catalog carries 26 bogus signatures, not 21.
- `voiceLanguage` arrived in 3.03, not 3.05.
- The 32 "exact duplicates" are host rows that repeat a GameStateExt signature. None is byte-identical.
- Host-only provenance affects 21 signatures (20 names), not only the seven listed.
- `getPosASL` is tagged `ofp 1.99` on the wiki (in `game7`) and in `acemod/arma3-wiki`. That makes 3 of the 38 Elite names, not 2, and the §4 table and open question 1 now say so.
- Rust size: 4,750 lines, not about 4.4k.
- Direct indexing: about 60 expressions, not about 30, and `oracle.rs#L331` adds an `unreachable!()`.
- CI also exports the doc corpus.
- `tower-lsp` is `MIT OR Apache-2.0`.
- crates.io was reachable: the fork's crates are unpublished.
- The fork's handling of top-level `,` is known: an `EvalSemicolon` warning.
- The `_x` check-mode question is narrowed by code reading (§6).
- There are 26 upstream Evaluator test files, not 25.
- `~t` is executed as an assignment, not evaluated directly.

**Still unverified.** Whether other CI tests failed (the logs need auth). The runtime behaviour of `_x` in editor fields. Anything about the 1.99 executable. Wiki and `acemod` data licensing. The "Arma 2+" `distance` hint. That no Elite-overlap page other than `getPosASL` carries a trailing `ofp` tag, which rests on model-summarised API output and deserves a scripted re-check when the generator is built.
