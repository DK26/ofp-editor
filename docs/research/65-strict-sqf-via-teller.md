# A Rust-like experience for mission scripts: strict SQF through Teller

Research doc 65 for Plotroom (`ofp-editor`). Research date: 2026-09-28. Audience: contributors and LLM coding agents. This file is
meant to be read on its own.
Questions answered (owner, 2026-09-28, verbatim): "I wonder if LSP servers could provide the same experience as in Rust, to some
point", and the follow-up: "Well the language won't compile if things are not correct, and the entire language is built to detect
issues at compile time." In Plotroom's terms: can Teller give the people and models who write mission scripts (SQF, SQS, the code
fields of `mission.sqm`) tools that lead into correct usage, make bad states impossible where possible and make logical errors easy
to spot; and can that be **enforced**, not only advised, without taking away the user's creative freedom (D011)?

**Status: proposal.** Nothing in the repository was coded or changed except this file. Engine and tool sources were read at the pins
of §7.1 and the Sources; web pages and papers as the Sources say; corpus shares come from a local estimator (legend [M-local]). Every
design proposal is [I]. This doc changes no decision.
**Epistemic legend** (doc 16's, extended). **[V]** read at the cited commit or page on 2026-09-28. **[V-author]** a number published
by the cited authors, not reproduced by us. **[V per doc N]** taken from a sibling doc. **[M-local]** measured for this doc by a
scratch estimator over the owner's own install, run outside the repository; only aggregate counts leave the machine; it is a Python
re-implementation, not the ported checker, so every such number is to be re-measured when Teller exists. **[I]** our inference or
proposal. **[U]** unknown.
**Relation to sibling docs.** Doc 23 owns Teller's catalog, the parity checker, the check modes and the model-shaped diagnostic schema
(§13.4); doc 24 the command risk policy and its finding F7 ("dynamic code cannot be certified"); doc 19 §5 the campaign condition
language (CXL); doc 30 the knowledge stack (D027); doc 31 §7 the script rung, the symbol index and the silent-failure lints, §8 import
and lift, §9 the AI angle; doc 35 the corpus and its idiom counts; validation-and-lints §1, §3, §7 and §9 set severity and place
Teller; commands-undo-history §4 owns admission. Written the same day: doc 61 (Teller as the model's instrument, surface levels
TS0–TS3), doc 62 (type-driven guidance for Rust APIs; its governing principle quotes the owner's follow-up and names this doc as its
application to mission scripts) and doc 63 (freedom levels FR0–FR8). Doc 64 (Rust and weak models, an experiment design) was not in
`docs/research/` when this was written; §6 mirrors the design its draft pre-registers and must be re-aligned when doc 64 is published.
**Names** (working terms; user-facing names go through the names table, D034). A **gate** is a check whose failure stops an artifact
from being built (admitted, staged for Preview, exported), not merely reported. The **floor** is what blocks at every level today:
engine parity, the target profile and doc 24's risk policy (validation-and-lints §3, §11). **Strict SQF/SQS**, "the dialect", is plain
SQF/SQS plus erasable declarations; every plain script is a valid dialect file at the lowest level. **Levels** Off / Advisory / Strict
are set per file, per field and as a mission default (§4.10). A **raw block** is a marked, user-authored region of a Strict file whose
findings are advisory, the analogue of Rust's `unsafe`. An **ascription** is a declared type for a value the checker cannot prove: a
trusted claim, never a checked cast. **Lifting** raises a file or region to a higher level. A **contract error** is a Strict violation.
Labels SG1–SG14 (§7.3), ST-01–ST-23 (§9), H-SQ1–H-SQ4 and DR-SQ1–DR-SQ8 (§6) are this doc's; none collides with an existing
family (checked 2026-09-28). "Strict" collides with the "strict Preview" launch (game-integration §6), the engine's `--strict` flag
and the envelope rules called "strict admission of model output" (agent-runtime §6; doc 21; doc 61 §4.6 item 1); §7.3 SG4.
**Hygiene.** Public sources only. The corpus is the owner's own install, read locally and never committed (as in doc 35): this doc
holds only aggregate counts and command or class names; no script, mission or campaign text is reproduced. The estimator and its
outputs stay outside the repository. No local paths, user names or keys.

## TL;DR

- **Yes, to a large extent; but the enforcement is not in the language server.** A language server can carry the guiding half of
  Rust's experience: completion filtered by the slot's expected type, signature help with the active overload, inlay hints for
  inferred types, diagnostics that name the fix, quick fixes, semantic tokens and safe rename [I]. What makes Rust feel like "it won't
  compile unless it's right" is that the build refuses to produce output. Diagnostics alone are advice: across 9,655 Python projects,
  78.3% of commits went in despite type errors their annotations exposed (Di Grazia and Pradel, FSE 2022) [V-author], and TypeScript
  emits JavaScript on type errors unless `noEmitOnError` is set, which "defaults to `false`" [V]. So the proposal (§4.3) makes Teller's
  verdict the only way to build what admission, Preview staging and export accept [I].
- **SQF is unusually well suited to a gate.** On official content [M-local]: 98.4% of code units (script files and code fields) pass a
  level provable from text and the command catalog; 96.6% pass once mission names resolve; 95.6% pass a sound level (no dynamic code,
  no names shadowing commands, one type per global) on `Cwr` (96.3% on `Cwa199`); 95.4% with no implicit "any". Official content holds
  almost no string-built code (doc 35 counts one computed `exec` path in all of it) [V per doc 35]. What blocks is names, not types:
  dead developer cheat triggers, undefined or misspelt globals, campaign variables, names that shadow commands.
- **Whole missions pass far less often:** 44% at the sound level, 55% after four previewed auto-migrations, because one bad field fails a
  mission [M-local]. A gate on all existing content would be a wall. Hence the split: **mandatory for code Plotroom and models produce,
  opt-in for code people write.**
- **Recommendation (§4.2): one typed core, three front-ends, one gate.** (1) The no-code IR and CXL, correct by construction: the main
  path for generators and weak models. (2) Strict SQF/SQS: the same language with erasable declarations (the TypeScript, Teal and Luau
  model); every new-syntax language compiled to SQF stayed niche. (3) Raw SQF/SQS as a marked, user-only escape hatch with advisory
  diagnostics. Proposed: all Wilco output, generated modules, plugin and external-agent proposals, quick fixes and migrations pass
  Strict, so nothing unchecked from those origins reaches a mission; this adds to doc 24's capability policy and replaces none of it.
- **Freedom stays with the user (§4.4).** Raw is always available; a Strict region is downgraded in one visible, undoable click; imported
  and community missions keep working as they are; outside Strict the floor blocks only what it blocks today. A contract error exists
  only in regions the user opted into and in generated code. Letting it block a user's own region needs a new severity and an owner
  ruling on D011 item 3 and validation-and-lints §1 principle 2 and §3; the alternative that keeps Strict advisory for user code is
  listed beside it (SG1; open question 2).
- **What Strict adds (§4.8):** declared globals with one type each; comment-borne types and function contracts where the load path keeps
  comments (SQS `;` lines, `//` in `preprocessFile`d SQF), the sidecar elsewhere; a `Code` type, so no code is built from strings (the
  condition doc 24 F7 names for certification); references (markers, classes, sounds, script paths, labels) resolved against the
  mission; enum strings from the engine's own name tables; nullability for `objNull`, `grpNull` and maybe-undefined globals; locality
  markers for multiplayer.
- **The engine forces an erased design.** Neither CWR 3.05 nor CE registers `params`, `isNil`, `typeName`, `compile` or `str` [V grep],
  so no runtime check can guard a boundary. Declarations erase, hand-written Strict code ships byte for byte as written, and a checker
  change can never break a mission already shipped (§4.3).
- **Limits.** Types catch a real but bounded share of bugs: about 15% of fixed public JavaScript bugs and 15% of corrective Python defects
  [V-author]. Timing, AI behaviour, locality and world state stay runtime concerns for Preview probes, and `Cwa199` has no Preview. A
  "compiles" badge is never shown as "correct" (§4.14).
- **The LLM side (§5).** Wilco writes, Teller checks, one root finding per repair with a typed fix menu. Weak models fill IR slots and
  write no script text; qualified models write the dialect; no model writes raw or trusted ascriptions (coding agents used `any` 9× as
  often as humans in TypeScript PRs) [V-author]. Per D048, a preset may change the authoring surface, never the gate. On doc 63's
  ladder the dialect is the FR5–FR7 surface; raw is at no level.
- **An experiment plan (§6)** mirrors doc 64's: plain SQF with floor diagnostics against the Strict dialect with Strict diagnostics,
  three small local models and a larger comparator, R0 against up to three repairs, hidden checks by a static oracle and CWR Preview
  probes. Fourteen design-gap candidates, four engine-request candidates and 23 tests to write first are listed, none filed (§7, §9).

## 1. What makes Rust's experience guiding, and what an LSP can reproduce

### 1.1 Seven mechanisms

| # | Mechanism | In Rust | Carried by LSP? | Teller for mission scripts [I] |
| --- | --- | --- | --- | --- |
| 1 | Types that make bad states unrepresentable | Newtypes, enums, `Option`, private constructors | No: the checker decides; LSP only shows it | Branded strings, enum literals, `Code`, `Object?` (§4.8); in the no-code IR, real Rust types (ids, enums) |
| 2 | Exhaustiveness | `match` | No | CXL totality with a witness state (doc 19 C03); SQS label resolution |
| 3 | Diagnostics that name the fix | Primary message, notes, `help` with a suggestion, stable codes, `--explain` | Yes: `publishDiagnostics` (message, code, code description, related information, data) | Doc 23 §13.4's schema, the DG005 code registry, the wording rules of §4.9 |
| 4 | Quick fixes | Machine-applicable suggestions; rust-analyzer assists | Yes: `codeAction` | `FixId` commands, previewed and undoable (validation-and-lints §6) |
| 5 | Guidance while typing | Completion, signature help, inlay hints, hover, semantic highlighting | Yes | Completion filtered by expected type (bitmask algebra plus refinements), profile-greyed rows (doc 31 §7.3) |
| 6 | The compiler in the loop: nothing ships that fails | `cargo build` refuses to emit | **No**: the protocol has no build | Admission, Preview staging and export accept only Teller-built witnesses (§4.3) |
| 7 | Explicit, audited escapes; lint levels; editions | `unsafe`, `forbid`, `#[expect]`, editions | Only as tags | Raw blocks, levels, a "forbid raw" policy, checker editions (§4.5, §4.10, §4.13) |

Rows 3–5 are what a language server transports, for any checker. Rows 1, 2, 6 and 7 are properties of the language and the build. So
the answer to "to some point" is: the protocol gives the guiding surface; the "won't compile" property must live in Teller the library
and in Plotroom's pipeline [I]. Wilco reaches Teller in process, never through the protocol (doc 61 §4.2), and the optional LSP binary
for external editors (validation-and-lints §9) should put the rule and the fix in `message` at error severity, since many clients
forward nothing else (doc 62 §4.4).

### 1.2 Where today's tools stop

- **The owner's fork** (`DK26/CWR@6fd6ca3974`, `lsp/`) is the only surveyed tool that targets this dialect and parses SQS. Its own
  agent skill states the gap: "Only *lexical* breakage (unterminated string, unbalanced brackets) is reported as an `error`. Everything
  semantic — an unknown command, a type mismatch, a missing operand — is a **`warning`**, because the checker treats a variable as
  unknown ("any") type and never raises a false red" (`lsp/skills/poseidon-scripting/SKILL.md#L56-L61`) [V]. Its `--strict` flag
  fails on warnings, but local and global variables get the "any value" mask (`crates/poseidon-syntax/src/check.rs#L284-L308`) and
  `?cond : stmt` SQS lines are skipped (`#L99-L101`) [V], so even `--strict` cannot see undefined names, enum strings or SQS conditions.
  Doc 23 §13.1 recommends porting and restructuring it; this doc says what it should grow into.
- **Arma 3 tools** (HEMTT, armalint, sqflint, sqf-analyzer, the SQF-VM language server) infer types and warn, but keep undefined-variable
  checks advisory because SQF scopes are dynamic: HEMTT's `L-S13 undefined` defaults to "help" and skips code blocks it cannot place
  (`libs/sqf/src/analyze/lints/s13_undefined.rs`, `default_config` → `LintConfig::help()`) [V]. All of them follow the Arma 3 dialect,
  none parses SQS except the fork, and none checks class-name strings against a loaded config (§7.1) [V per research pass].
- **The original editor had a field-level gate.** Its unit dialog runs `CheckExecute` on the init line and `CheckEvaluateBool` on the
  presence condition, and on failure focuses the control, shows the engine's message, moves the caret and returns `false`, so the
  dialog does not close (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcade.cpp#L1103-L1125`) [V]. Plotroom's
  planned admission reproduces it (`check_field`; commands-undo-history §4.2). Script files and `{…}` bodies were never checked (doc
  23 §6 rule 4).

## 2. Evidence

### 2.1 A checker without a gate is advice

| Source | Finding | For Plotroom [I] |
| --- | --- | --- |
| Di Grazia, Pradel, FSE 2022 (Distinguished Paper) | 1,414,936 annotation changes in 9,655 projects; "more type annotations help find more type errors (0.704 correlation)"; "many commits (78.3%) are committed despite having such errors" [V] | Unenforced checks are ignored; the gate is the point |
| TypeScript handbook, `noEmitOnError` | "Do not emit … if any errors were reported"; "This defaults to `false`" [V] | The owner's "won't compile" is TypeScript with `strict` plus `noEmitOnError`, not TypeScript's default |
| TypeScript design goals | Types fully erasable, no runtime type information; a sound type system is a non-goal [V] | Our targets force erasure too (§4.3) |
| Gao, Bird, Barr, ICSE 2017 | 400 fixed public JavaScript bugs: Flow and TypeScript each detect 60, "mean 15%" (95% interval 11.5–18.5%); 1.7 and 2.4 annotation tokens per detected bug; "StringError" (wrong string contents) ranks second among undetectable bugs, since "the string type is opaque to most static type systems" [V-author] | Types catch a bounded share; SQF hides most of its types in strings, so typed strings matter most |
| Khan, Chen, Varró, McIntosh, TSE 2022 | mypy could have prevented 15% of corrective defects (11% of all defects) in 210 Python projects; most common causes: redefined references, dynamic attribute initialisation, mishandled null objects [V-author] | SQF analogues: reused globals, runtime-built names, `objNull`/`grpNull`/undefined reads |
| Bogner, Merkel, MSR 2022 | TypeScript apps: better code quality and understandability, but not lower bug proneness; their mean bug-fix commit ratio was higher (0.206 against JavaScript's 0.126) [V-author] | Never promise fewer bugs from types alone |
| Berger et al., TOPLAS 2019 | Language-level effects on defects are "exceedingly small" when the classic study is reproduced [V-author] | Claims stay mechanism-specific |

### 2.2 How typed layers over dynamic languages were adopted

| System | Levels | Escape hatch | Where it ended |
| --- | --- | --- | --- |
| Sorbet (Ruby) | Per-file sigils `ignore` < `false` < `true` < `strict` < `strong` | `T.untyped`, `T.unsafe`; no documented comment that silences one error, so suppression stays in code and is traceable [per research pass] | Stripe: "85% of all non-test files opt into `# typed: strict`" and "over 95% of all files are `# typed: true`"; "only a couple dozen `# typed: strong` files" in over 150,000; metrics are files per sigil and `T.untyped` uses; spoom's `bump` promotes a file only when that adds no errors [V-vendor] |
| TypeScript over JavaScript | `// @ts-check`, `checkJs`, JSDoc types on plain `.js` | `@ts-expect-error`, itself an error when nothing follows it; typescript-eslint's `ban-ts-comment` demands a description [V] | Checked plain files with no change to the emitted code |
| Pyright, mypy (Python) | `off`, `basic`, `standard`, `strict`, per file | Rule-scoped ignores; a report for stale ignores (off by default) [V] | Dropbox: mandatory annotations for new files, weekly coverage reports; `Any` leaking in "caused a major loss of typing precision" [V-vendor] |
| Hack (PHP) | `partial`, `strict`, `decl` | `HH_FIXME[code]`, allowed only for codes listed in the project config [V] | Moving to strict only: HHVM 4.48 added an opt-in `disable_partial` flag (default off), 4.62 expected support for `// partial` to be removed, and 4.135 (2021) was "actively working towards removing support for 'partial' mode" [V] |
| Luau (Roblox) | `--!nocheck`, `--!nonstrict`, `--!strict` | `any` suppresses errors without cascades | Two contracts: non-strict "aimed at non-professionals, focused on minimizing false positives (that is, in non-strict mode, any program with a type error has a defect)"; strict "aimed at professionals, focused on minimizing false negatives" (HATRA 2023) [V]. Non-strict became the default on 2025-11-20, "reporting only definite runtime errors" [V] |
| Elixir 1.20 (2026-06-03) | Gradual typing with no annotations | `dynamic()` | Reports "verified bugs: typing violations that are guaranteed to fail at runtime if executed", only for disjoint types [V] |
| Dart | Mixed sound and unsound code | Legacy libraries | Dart 3 removed unsound mode [V per research pass] |
| Elm 0.19 | One strict mode | User native code removed | Users left over the missing escape [V per research pass] |
| Enforce Script (Bohemia's typed successor to SQF) | Statically typed | — | Compiles at game start, so one broken mod stops the game; in Reforger 1.1 "the Enforce Script Compiler now throws errors on incorrect usage of the `ref` keyword", and the post mentions no warning or deprecation period [V, reforger.armaplatform.com; search summaries for the start-up failures] |

Reading [I]: every ecosystem that got the most from types ended in a **ratchet** (opt-in per file, then a default, then more strict),
kept its escape hatch **marked, scoped, reasoned and counted**, and **enforced at authoring time, never at the player's load time**.
Luau needed years to reach a default mode with near-zero false positives, so Advisory (§4.10) is measured on the corpus before it is on
by default. Elm and Dart show that removing the hatch or forcing migration costs users; Plotroom does neither.

### 2.3 Typed layers over game scripting languages, and over SQF

- **Outside Arma.** Teal ("a typed dialect of Lua"; `tl gen` strips annotations to plain Lua; OpenMW ships Teal declarations for its
  API). TypeScriptToLua with generated engine typings (typed-factorio, Dota2Declarations, w3ts), whose caveats page lists the semantic
  mismatches of compiling one language's semantics into another's (`0` and `""` truthy, `==` as `===`, `nil` deleting table keys, 200
  locals per scope). GDScript's optional typing with `UNSAFE_*` warnings and green "safe lines" in the editor [V].
- **Over SQF (all for the Arma 3 dialect).** ASL (MIT; C-style syntax; no program type checking in its README, which since 1.2.0 reads
  an Arma 3 `supportInfo` command-signature file to lower command calls; last commit 2018), TypeSqf's SQX (typed object-oriented
  dialect; the analyzer ships only as a binary, `Dependencies/TypeSqf.Analyzer.dll`; last commit 2020-11), OOS (archived 2022), SQF++
  (typed parameters) and SQC inside SQF-VM (typed parameters lowered to Arma 3's runtime `params` checks,
  `src/sqc/sqc_parser.cpp#L824-L872`) [V repository pages and clones at the §7.1 pins].
  None reached wide use; the tool the community adopted is HEMTT, which checks plain SQF [I]. The pattern matches CoffeeScript giving way
  to TypeScript, and Dropbox's CoffeeScript-to-TypeScript migration [V-vendor].
- **Why it matters here.** A new syntax has no training data, while models already know SQF's shadow dialect (doc 30 §1.1); a
  same-semantics dialect avoids TypeScriptToLua's mismatch class entirely; and SQC's approach is impossible on our targets, which have no
  `params` (§4.3) [I].

### 2.4 Types and language models

| Source | Finding [V-author unless marked] | For Plotroom [I] |
| --- | --- | --- |
| Mündler et al., PLDI 2025 | Syntax causes only about 6% of compile errors in LLM-written TypeScript, the rest being type-checker errors; type-constrained decoding "reduces compilation errors by more than half", for open models of 2–34B; needs sampler access (doc 61 §2.4 has the per-model figures) [abstract V-author; the 6% per doc 61, from a research pass] | Type checks, not syntax checks, carry the gain; decode-time types only for local models |
| MultiPL-E (Cassano et al.) | "Static type-checking neither helps nor hinders code generation model performance" (typed against untyped target languages); replacing TypeScript signature types with `any` cost 2.5% (p < 0.001) | Shown types help a little; the larger gains reported above come when types are enforced in the loop or the decoder |
| Monitor-guided decoding (Agrawal et al., NeurIPS 2023) | A static-analysis monitor served through a language server let SantaCoder-1.1B beat text-davinci-003 on compile rate | A language service can lift small models at generation time |
| TypeChat | Types as the schema; the compiler validates; its diagnostics drive repair [V] | Plotroom's "code proposes, model selects, code validates" |
| Tambon et al., EMSE 2025 | 333 LLM bugs: hallucinated objects 9.57%, wrong attributes 8.55%, wrong input types 5.91%, syntax 6.11% (catalog- or type-detectable); misinterpretation 20.77% and missing corner cases 15.27% (not) | About 30% is gate-catchable; the rest needs specs, previews and tests |
| CloudAPIBench (Jain et al.) | GPT-4o made only 38.58% valid calls to low-frequency APIs; documentation in context raised it to 47.94% | CWA 1.99's command set is extremely low-frequency; a profile-filtered catalog the checker enforces is the defence |
| Static-analysis feedback loops (arXiv 2508.14419; 2508.00422) | Checker findings fed back over rounds cut issues sharply with no logit access | Works with cloud models |
| Lee, Hassan, Hindle (arXiv 2602.17955) | "AI agents are 9x more prone to use the 'any' keyword" than humans in TypeScript PRs [V] | Models use escape hatches to pass gates (§5.5) |
| Doc 30's own run | Of 16 answers that fell short with cards, 8 had a syntax or structure error a checker or typed action would catch [counts per doc 30; the classification is doc 30's own inference] | The residue is gate-shaped |

### 2.5 What the evidence does not show

Nothing above was measured on SQF, SQS or a mission's code fields. The model results come from TypeScript and Python benchmarks; the
bug-share studies are about public bugs, which the authors say understate private-development benefits. The corpus shares of §3 come
from a Python estimator with known false positives (§3.2). Adoption of SQX, ASL and OOS was never measured. Every number here is a
direction for the instruments of §6 and §9, not a prediction [I].

## 3. How much of SQF can be checked

### 3.1 What the engine's types give, and what they hide

All at `BohemiaInteractive/CWR@ffc61838b7` (`EVAL:` = `engine/Evaluator/`, `GSE:` = `engine/Poseidon/Game/Commands/GameStateExt.cpp`).

- **The type universe is a bitmask.** Scalar 1, Array 2, Bool 4, String 8, Nothing 16, the fake control types `if`, `while`, `for`, and
  `GameVoid` = any value (`EVAL:express.hpp#L44-L57`); Object 0x100 through File 0x4000 (`GameStateExt.hpp#L12-L18`); scalars are
  32-bit floats (`express.hpp#L67`) [V]. Overloads therefore already form a set-theoretic type system, as in Luau and Elixir [I].
- **There is no Code type.** A `{…}` block lexes to a String constant (`EVAL:express.cpp#L257-L270`), and `then`, `exitWith`, `else`,
  `do`, `forEach`, `count` and `call` take String (`#L1132-L1149`) [V]. Code, class names, marker names, enum words and script paths
  are all String.
- **Arrays carry no element types.** `select` returns `GameVoid` (`#L1128-L1129`); `units` returns a bare Array (`GSE#L979-L980`) [V].
  A research pass counted 724 argument slots in 534 registration rows: Object 204, String 171, Array 137, Scalar 104, Bool 37; about 43%
  are String or Array [V per research pass, regex scan].
- **Shapes and enum domains live in handler bodies.** `GetRelPos` accepts an Object or an Array of 2–3 Scalars
  (`GameStateExtGrp.cpp#L885-L938`) [V]. `setBehaviour` is Object-or-Group × String (`GSE#L1299`), and its handler
  looks the word up case-insensitively in the `CombatMode` name table (`engine/Poseidon/AI/ArcadeTemplate.cpp#L82-L92`: `UNCHANGED`,
  `CARELESS`, `SAFE`, `AWARE`, `COMBAT`, `STEALTH`) and returns Nothing, with no error, when nothing matches
  (`GameStateExtGrp.cpp#L171-L191`) [V]. The engine has 66 explicit `GetEnumNames` specialisations by our regex (a research pass counted
  68 with another pattern), plus macro-built tables [V].
- **Failures are silent by default.** A command with a nil operand returns a typed nil without calling its handler (binary
  `EVAL:express.cpp#L1348-L1351`, unary `#L1417-L1419`); "nil is never equal to anything" (`#L1958-L1963`); a non-Bool condition records a
  type error and returns `false` (`EvaluateBool`, `#L2773-L2782`) [V]. A misspelt global therefore turns a whole statement into a no-op
  with no log line (doc 31 §7.2).
- **The engine's own check is shallow.** In check mode a global evaluates to `GameVoid` and a nular command wins over a same-named
  variable (`#L195-L219`); `{…}` bodies are never entered [V]. At run time the opposite holds: a set variable hides an operator of the same
  name (`#L1320`), so one line parses differently in check mode and at run time [V]. The engine does this on purpose: "A user-defined
  variable hides a function or operator of the same name, so a script keeps working even when a new command later collides with one of
  its variable names" (`#L1287-L1289`) [V]. Forbidding such names is therefore a Strict choice, not an engine rule; outside Strict it
  stays a Warning (validation-and-lints rc61) [I].
- **`this` depends on the field.** In a trigger condition it is the activation Bool
  (`engine/Poseidon/World/Detection/Detector.cpp#L1259-L1263`); On Activation does not rebind it: `DoActivate` sets it to `true` and
  re-evaluates the condition, then `OnActivate` rebinds only `thisList` (`#L1299-L1337`), so it is still that Bool, or a stale value
  when the condition text is exactly `this` (doc 31 §5.3, §7.1); in a unit or object init line it is the vehicle
  (`engine/Poseidon/World/WorldInit.cpp#L624`); in a waypoint field it is the leader's vehicle, with `thisList`
  (`engine/Poseidon/AI/AIArcade.cpp#L331-L332`) [V]. Named vehicles also get implicit crew globals `<name>d`, `<name>c`, `<name>g`
  (`engine/Poseidon/AI/AICenterImpl.cpp#L1638-L1640` and following) [V].
- **There is no runtime type introspection.** Neither CWR 3.05 nor `ofpisnotdead-com/CWR-CE@b67bf3bd62` registers `params`, `isNil`,
  `typeName`, `isEqualType`, `compile`, `compileScript`, `spawn`, `sleep`, `waitUntil`, `setVariable`, `getVariable` or `str`; the only
  introspection is `typeOf OBJECT`, which returns a class name (`GSE#L1197`), and `isNull` (`GSE#L933`) [V grep of the registration
  rows, excluding the mock `EvalState.cpp` host, doc 23 §3.2].

Consequence [I]: the dialect's value is in **refinements the engine erases**: `Code` with its context, element and tuple types, branded
strings and literal unions. The engine can never check them at run time, so Teller must check them before anything ships.

### 3.2 The checkability map

Shares are code units of official content (legacy campaigns, single and multiplayer missions, editor templates: 208 mission and template
folders, 686 SQS files and 12,640 code fields in `mission.sqm`) that pass each class **cumulatively** and unchanged [M-local].

| Class | What it covers | Needs | Units passing |
| --- | --- | --- | --- |
| **A. Provable from text and catalog** | The SQS line model (`?` without `:`, `:` inside a condition string, 4,095-byte lines, `~` over 233 bytes, labels, code after `exit`); command fixity, arity and priority; overload algebra, including literal code in known code positions with `_x` and `_this` bound; check-mode statement kinds; enum strings; Nothing-returning commands used as values (`cheatsEnabled`, `GSE#L897`); `Bool == Bool`, which has no overload (only Scalar, String, Object, Group, Side: `EVAL:express.cpp#L1113-L1117`, `GSE#L1279-L1284`; `boolEq` is the CWR form); profile availability (131 names absent from the 1.99 executable, doc 35 §8.2); locals never assigned; literal class names against the config catalog | The generated catalog | **98.4%** |
| **B. With mission context** | Globals from unit, vehicle and trigger names and the implicit crew names; markers; sound, radio and music classes; script paths in the engine's search order; the mod set's classes; `this` per field kind | Teller's symbol index (doc 31 §7.1) | **96.6%** |
| **C. Sound** | No dynamic code; no name equal to a command of the profile; one type per global (only 2 globals in all official content hold two concrete types); array element types from the catalog | Inference plus declarations | **95.6%** on `Cwr`, **96.3%** on `Cwa199` |
| **C_full** | No implicit "any": function contracts at the `_this` boundary of `exec` and `call`; typed `call` results | Signatures | **95.4%** |
| **D. Not statically checkable** | String-built code, computed paths and names; runtime locality; timing (`@` re-evaluation, `~` delays, the 0.5 s trigger period with a random phase, the 10,000-iteration `while` cap); world state (`alive`, `damage`, `random`); semantics of 1.99 names nobody probed (doc 35 tier T3) | Preview probes and advisories (§4.14) | — |

**Missions**, where one failing unit fails the mission [M-local]: A 61%, B 47%, C 44%, C_full 43%; C after auto-migration (§4.12) 55%.
Per group at C: 1985 campaign 33 of 79 missions, Resistance 4 of 39, official multiplayer 20 of 30, templates 25 of 36, single missions 7
of 18. **A mod framework** (the CWE library, 552 files) looks different: 62 files (11%) hold truly dynamic code (computed paths 38,
`format`-built code 10, code from variables 12, other 6); 219 more load functions with `call loadFile` or `preprocessFile` of literal
paths, which project and addon file context resolves; `_this` parameters leave implicit "any" in 418 files, and files pass C_full at
10.7% against 46% at C [M-local]. Libraries need function contracts; missions need names.
**Caveats.** The estimator mirrors the engine's parser (`Vyhod`/`VyhCast`, `EVAL:express.cpp#L1558-L1864`, `#L1290-L1468`) but is not the
ported checker; the mod's replacement main config is missing from its class catalog (59 known false positives); blocker counts are
approximate; `cheatsEnabled`'s Nothing return and the missing `Bool ==` are CWR facts, unprobed on 1.99. Doc 35 counts one `exec` with a
computed path in official content (`data/corpus-script-idioms.csv` row `exec_non_literal_path`), while the estimator classed no official
unit as dynamic; either way the dynamic tail of official content is at most one statement [V/M-local; the difference is U].

### 3.3 What blocks a sound level today

Official content, units failing C and missions affected [M-local]:

| Blocker | Units | Missions | Remedy (§4.12) |
| --- | --- | --- | --- |
| Developer cheat triggers reading `cheat0`–`cheat9` (never set in retail; doc 35 counts 260 references in 75 official missions, 271 with the mod library) | 189 fields | 74 (the only blocker in 15) | Quarantine, previewed |
| Reads of undefined globals: typos, stale object names, markers used as variables | 150 | 63 | Real defects: a human decides |
| Globals defined only in another mission of the campaign (path-sensitive: some only on some branches) | 57 | 39 | Declare in the Tote (doc 19 §4) |
| The `X == X` existence idiom (252 lines corpus-wide, doc 35 row `self_equality_existence_check`) | 28 SQS files | 26 | Declare the name maybe-undefined; Strict reads the idiom as a typed existence test (§4.8 rule 2) |
| Names equal to a command: a global named like CWR's `endGame` (84 units on `Cwr`); objects or variables named `weapons`, `player`, `to`, `saveGame`, `fire`, `call`, `removeAllWeapons` (34 units) | 118 | — | Engine-exact rename, previewed |
| `? CheatsEnabled` (a Nothing-valued condition) | 14 SQS files | — | Quarantine |
| Unresolved scripts, markers and sounds; unrecognised enum strings (10 in official content, doc 35) | about 60 | — | Pick from candidates |
| Globals holding two types | 17 | — | Split the name |
| Genuine type errors, for example an Object-left `orderGetIn` inside a `forEach` string (it needs an Array, `GSE#L1294-L1295`) and `this setDammage 1` in a trigger activation, where `this` is the condition's Bool (§3.1) | 3 | — | Real defects |

### 3.4 Profiles change verdicts

The same file can be Strict-clean on one profile and not on another [M-local; V lines]. CWR 3.05 registers a public `endGame` nular that
closes the application (`GSE#L886`; doc 24 F5), so a mission global of that name blocks 70 official SQS files on `Cwr` and none on `Cwa199`
(SQS files passing C: 72.4% on `Cwr`, 82.7% on `Cwa199`); CE renamed it to a harness-only `triEndGame` (doc 23 §3.2). CWR accepts the
Arma 3 shorthand `private _x = v` (`EVAL:express.cpp#L2826-L2837`), which is not 1.99 syntax. Official 1.99 content uses no command absent
from the 1.99 executable, so class A passes equally on both. The gate therefore runs per profile; generated code keeps to the conservative
subset (D003 item 5; validation-and-lints §8), and on `Cwa199` generators emit only `?`, `goto`, `@` and `~` until the `if`/`while` probe
clears them (integration-owners I35-PRIMER-FACTS).

## 4. Enforcement, not advice

### 4.1 Options for a compile gate

| Option | What it is | For | Against | Verdict [I] |
| --- | --- | --- | --- | --- |
| (a1) A new-syntax typed language compiled to SQF (the ASL, SQX, OOS, SQF++ or TypeScriptToLua model) | Its own grammar and types; SQF as output | Full control over types | No training data for models; every SQF precedent stayed niche; a mismatch class between two semantics; users read output they did not write | **Rejected** |
| (a2) **A typed dialect that is SQF/SQS itself plus erasable declarations** (the TypeScript-over-JavaScript, Teal and Luau model) | Strict SQF/SQS: declarations in comments or the sidecar; the checker refuses to admit, stage or export code that fails | Models and users keep what they know; every plain file is already valid; erasure equality proves nothing changed | Declarations only where the load path keeps comments; some facts only inferable | **Recommended as the text form** |
| (b) **The no-code IR and CXL as the typed path** | Modules, rules, cinematics (doc 31) and campaign conditions (doc 19 §5), lowered by code | Rust types make bad states unrepresentable; the weak-model path; already designed | Covers what modules, rules and CXL express, not every script | **Recommended as the primary path** |
| (c) A strict gate on all raw SQF at export and Preview | One rule for everything | Simple to state | 44% of official missions pass (55% after migration); community content blocked; contradicts validation-and-lints §1 principle 2 and D011 | **Rejected as a default**; kept as a per-mission opt-in and a project "forbid raw" policy |

### 4.2 Recommendation: one typed core, three front-ends, one gate

```text
no-code IR (attributes, modules, rules, cinematics)  ─┐
CXL (campaign conditions and effects)                ─┤
strict SQF/SQS text (Expression slots,                ├──► Teller typed core ──► lower (IR, CXL) or erase (text) ──► plain SQF/SQS
  script editor, Wilco Compose)                       │    catalog + refinements              │
raw SQF/SQS blocks (user-only, marked)               ─┘    + mission symbol index             └──► engine-parity re-check per field mode
                                                           raw: parsed, indexed, advisory       (translation validation)
```

- **One core.** All front-ends parse into one typed syntax tree whose overloads come from the generated catalog (doc 23 §14). Doc 23
  §13.3's two verdict levels (parity, lint) gain a third: the **contract** of Strict (§4.8).
- **Two invariants, tested differentially** against the ported oracle and the engine vectors (doc 23 §9, §13.1): the gate never accepts
  what engine check mode rejects (ST-01); the lowering of every Strict program passes engine parity on its profile (ST-02; doc 23 §13.3
  item 4; doc 31 N7).
- **Hand-written Strict code compiles to itself.** Declarations erase and nothing else changes: the exported bytes are what the user wrote
  (D017's lossless round trip). Profile-specific forms are **fix-its that rewrite the source visibly**, not hidden lowering: `private _x
  = v` becomes `private ["_x"]; _x = v` for `Cwa199`, and an Arma 3 `sleep` (registered on no profile, §3.1) becomes an SQS `~` line
  (doc 31 §7.3). TypeScript-style downlevel
  compilation of hand-written text was considered and rejected: the user should read what ships (doc 31 N4). Only the IR and CXL
  front-ends lower [I].

### 4.3 Where the gate sits

- **Erased, so shipped missions never depend on Plotroom.** With no runtime introspection (§3.1), no boundary check can be emitted; sound
  gradual typing with runtime checks would also be slow (over 100× in some Typed Racket configurations, Takikawa et al., POPL 2016)
  [V-author]. A checker change therefore alters only what the next export accepts, never a mission already shipped, unlike Enforce
  Script's load-time compile (§2.2) [I].
- **The gate is a witness type** (proposal-only; not compiled; names not final), in the style of `Admitted<PlannedBatch>` and the
  typestate `CoreBuilder` (commands-undo-history §4.1–§4.2):

```rust
// plotroom-teller::gate (sketch). Only this module can build these values; all fields are private.
pub struct Checked<S> { site: S, profile: TargetProfile, edition: CheckerEdition, level: Level,
                        content: ContentHash, raw: Vec<RawAck> }          // raw blocks inside the site, if any
pub struct RawAck { span: RawSpan, fingerprint: Fingerprint, reason: AckReason, by: GestureId }
pub struct GatedSnapshot { snap: Arc<Snapshot>, sites: Vec<Checked<CodeSiteRef>> }
pub fn gate(snap: Arc<Snapshot>, profile: TargetProfile) -> Result<GatedSnapshot, GateRefusal>;

// plotroom-preview and plotroom-export take the witness instead of a bare snapshot.
pub fn stage(snap: &GatedSnapshot, spec: &StageSpec) -> Result<StagePlan, Vec<Diagnostic>>;
```

- A `GatedSnapshot` exists only if every code site passed the floor and, at Strict, its contract (for regions a user made Strict, as
  SG1 decides); raw blocks appear only with a `RawAck` that carries a user gesture. Today `stage` takes `&Snapshot`
  (game-integration §5), so this is a signature change (SG7).
- **Gate points.** (1) **Admission**, on every edit: floor for all origins; the contract for non-user origins; no raw from non-user
  origins (§4.4). A user's own edit is never refused for a contract error, even inside a Strict region: it lands and is reported, as
  typing in a Rust file is never refused before the build. (2) **Compile**, at Preview staging and export: cross-file checks (the
  reference graph, `_this` contracts, labels, campaign variables) and the re-check of every lowered line. (3) The existing Preview risk
  gate (doc 24 §5.2) and export gate (validation-and-lints §11). (4) `plotroom check`, whose exit code serves the CLI and registry CI
  (validation-and-lints §13).
- **Refusing to emit.** A generated region that fails its own check is a lowering error (commands-undo-history §5, failure class 2): the
  region keeps its last good content, marked `Stale`, with a diagnostic; unchecked output is never emitted.

### 4.4 Which code must pass, and how users keep their freedom

| Origin (core-document-model §8.1) | Level required | Raw blocks | Notes |
| --- | --- | --- | --- |
| `Wilco`, `Workflow`, `Plugin`, `External` | **Strict** at admission, on top of doc 24 §5.3's capability policy (allow, approve, template-only, deny), which is unchanged; a contract error rejects the proposal with allowed values | May not create, widen or edit inside one; may propose lifting one to Strict | Would replace doc 23 §13.3 item 2's "parity plus lint at `error` severity" for the AI gate with one named contract |
| Generators and lowering (`Source::Deterministic`: modules, rules, cinematics, CXL, editor glue) | **Strict by construction**, re-checked (§4.11) | Never | A failure is a compiler bug, never shipped |
| `QuickFix`, `Migration` | Must not add a finding at the target's level; Strict-clean where the target is Strict | Never | A fix never makes code worse (ST-14) |
| `Import` | Kept as it is; opens at Advisory (§4.12) | — | Nothing forced; bytes round-trip |
| `User` | The level the user chose; the floor always | Creates, edits and reasons them | The only origin that can |

- **A new severity, only where opted into.** Validation-and-lints §1 principle 2 and §3, and D011 item 3 ("Only what the engine or the
  target profile cannot run is an error"), say only `EngineError` and `ProfileError` block. For non-user origins the gate is admission,
  which already rejects beyond export severity; for a region the user made Strict, blocking export on a contract error is new, because
  the engine can run that code. Options for the owner (SG1; open question 2): **(a)** a `ContractError` severity that blocks only inside
  regions the user made Strict, with the readiness coach's audited "Preview anyway" (validation-and-lints §11) for Preview and no export
  until fixed or downgraded; **(b)** as (a) for Preview, with export offering "downgrade these regions to Advisory and export" in the
  refusal itself; **(c)** no new blocking: in user regions a contract error is a Warning that withholds the "Strict-checked" badge, and
  only non-user origins are gated. (c) matches D011 and today's severity rule exactly; (a) and (b) read a user's explicit opt-in (a
  `UserIntent` click, never a default, generator, preset or pack) as the user's own creative intent, which D011 says always wins. In
  every option the downgrade is one click away from the refusal, and nothing blocks code the user never opted in. This must be decided,
  not implemented silently.
- **How users keep full creative freedom** [I]:
  1. Raw is always available to the user; no feature requires Strict.
  2. Downgrading a region (Strict → Advisory → Off) is one undoable command, visible in the file badge and the mission badge.
  3. No migration is forced; an imported mission runs, previews and exports as it is, subject only to today's floor.
  4. Strict checks well-formedness of code, never taste: realism and plausibility stay advisory and dismissible (D011).
  5. "Forbid raw" is a policy a project, campaign or registry may choose (Rust's `forbid`), never a default. In a project or campaign
     only the user sets it, by a visible setting; a registry's requirement would apply only to submission to that registry, never to
     editing, Preview or local export (open question 3).
  6. If the user asks Wilco for a construct Strict cannot express (code built at run time), Wilco does not write that text: doc 24 §5.3
     rule 2 already denies AI-proposed `dynamic-code` with a computed string. Wilco says in plain words why Strict cannot certify it and
     points to the editor's "write this part as raw" action; the user creates the block (`UserIntent`) and writes the dynamic part, and
     Wilco may still write the Strict code around it. Letting a user-accepted Wilco suggestion fill a raw block would change doc 24's
     policy and is not proposed here (SG12). Wilco never offers raw as a way to fix a Strict finding.

### 4.5 The escape hatch

Form (illustrative; syntax is SG3): in SQS, `; @raw begin reason: "…"` … `; @raw end`; in `preprocessFile`d SQF, the same with `//`;
for a `mission.sqm` code field, a sidecar mark on the whole field.

- **Scoped and reasoned.** A raw block covers named lines and needs a reason (TypeScript's `@ts-expect-error` description rule;
  armalint's W229 "An inline suppression is missing a justification" [V]).
- **Typed at its boundary.** Values leaving a raw block are `unknown` until the user ascribes a type; each ascription is listed as a
  trusted claim. Globals the block writes are declared as its effects, so Strict code reading them stays checked.
- **Still parsed, indexed and linted.** Where-used reports "cannot prove" rows for names built inside it (doc 61 §4.5); findings inside
  are Advisory; the floor still applies (parity in editor fields, profile availability, doc 24 `deny`, which blocks one-click Preview
  with its named override).
- **Only the user touches it.** Admission rejects a raw block, a widened one or an edit inside one from any non-user origin; this extends
  the "Script-risk policy" family of commands-undo-history §4.2. Non-user origins may only replace a whole raw block with Strict code
  (a lift) as a proposal.
- **Stale escapes are reported.** A raw block whose contents would pass Strict gets an info-level "can be lifted", the analogue of
  TypeScript's unused `@ts-expect-error` [V].
- **No line-level ignore for contract errors.** As in Sorbet, a contract error is fixed, wrapped in raw, or its region is downgraded;
  fingerprinted acknowledgements (validation-and-lints §7) stay available for Warning and Advisory findings.
- **Counted.** A per-mission audit lists raw blocks, raw lines and ascriptions, like counting `unsafe`; the "fully checked" badge
  appears only when there are none (Dart's honest claim, §2.2). In a mission whose code is all Strict, dynamic code lives only in raw,
  so doc 24 F7's "not statically checkable" mark (rule L4) names exactly those blocks; in Advisory and Off regions L4 keeps marking the
  mission as today. The audit also counts doc 24 F10's other code sites: non-literal numeric values in `mission.sqm`,
  `description.ext` and other shipped configs, which the engine evaluates as script at load. They get the "fully checked" badge only
  when they are literals or pass Strict as expressions (doc 24 rule L12), and otherwise count like raw [I].

### 4.6 Engine-signature typing per target profile

- **Base signatures** come from the generated catalog: bitmask overloads per snapshot (CWR 3.01, 3.03, 3.05; CE at a pin), per-overload
  availability, `Cwa199` narrowed by the wiki `since` data, the 1.99 executable tiers T1–T4 and probes (doc 23 §14; doc 35 §8.3). Types
  always come from the CWR tables: the wiki's parameter types describe the latest Arma 3 syntax (`acemod/arma3-wiki` dist: 118
  parameters "Unknown", locality unspecified for 182 of 401 commands) [V per research pass], so the wiki supports availability only.
- **A refinement overlay**, generated where the source allows and reviewed where it does not, each row with a file:line citation:
  - branded strings from doc 31 §7.1's string-kind overlay: `MarkerName`, `ClassName<CfgVehicles | CfgWeapons | …>`, `SoundClass`,
    `MusicClass`, `RadioClass`, `ScriptPath`, `Label`, `ObjectiveId`, `VarName` (for `publicVariable`, `saveVar`);
  - literal unions from the engine's `GetEnumNames` tables: behaviour, combat mode, speed mode, formation, unit position; title-effect
    and camera-effect words (doc 31 §7.2);
  - shapes mined from handler bodies (`GetRelPos` → `Pos2 | Pos3`; pairs), and element types for array-returning commands (`units`,
    `crew`, `list`, `thisList` → `Array<Object>`; `getPos`, `position`, `getMarkerPos`, `velocity` → `Pos3`; `weapons`, `magazines` →
    `Array<ClassName>`);
  - `Code<Ctx>` for every code position (`then`, `else`, `exitWith`, `do`, `forEach`, `count`, `call`, `while`, `addEventHandler`,
    `onMapSingleClick`, `buttonSetAction`, `setTriggerStatements`, `setWaypointStatements`, the `createUnit` init string, and doc 24
    F7's `publicExec` and `onPlayerConnected` where the profile has them), with `_x` and `_this` bound;
  - locality rows curated from handler bodies (18 `IsLocal()` and 60 `GetNetworkManager()` call sites in the non-test command files,
    `engine/Poseidon/Game/Commands/` without `*Test*`) [V], since no signature carries locality.
- **Unknown is never "anything" in Strict.** Doc 23 §3.3 found that the fork maps an unknown type name to "matches anything"; in the
  generator that becomes an error, and in Strict an untyped value is `unknown`, which permits no operation until narrowed [I].
- **Evidence tiers bind.** Generated code uses only "verified by reading" or "probe-confirmed" overloads (validation-and-lints §8); in a
  user's Strict file an "unverified on `Cwa199`" overload is a Warning with the tier shown, never a silent pass (open question 6).

### 4.7 Mission-aware checks

- **Symbols** from Teller's index (doc 31 §7.1; validation-and-lints §9): unit and vehicle names, implicit crew globals only when the
  vehicle class has that seat, groups, markers, triggers, waypoints, script files in the engine's search order (mission, campaign
  `scripts\`, root `scripts\`), `description.ext` classes, stringtable keys, campaign `saveVar` names, module-owned globals.
- **Field contexts.** `this` and `thisList` typed per field kind (§3.1), so `this setDammage 1` in a trigger activation is a contract
  error; check-mode statement kinds; no bare `_x` in editor fields (`EvalNamespace`, doc 23 §6).
- **Campaign variables** typed by the Tote (doc 19 §4): definitely or maybe defined at each mission, computed over the campaign graph, so
  a variable written only on one branch reads as maybe-undefined downstream.
- **Mods.** Class catalogs per mod-set fingerprint (D030); a mod's replacement configs are loaded, or its class checks stay Advisory.
- **Cross-file.** The `exec` and `call` graph with `_this` contracts checked at every call site; labels per file; `publicVariable` names
  declared once.

### 4.8 The Strict contract

| # | Rule | Evidence | Erased or lowered as | Fix offered |
| --- | --- | --- | --- | --- |
| 1 | Globals are declared (mission model, Tote, module or script declaration), one type each; no global named like a command of any enabled profile; near-miss names rejected | 150 units with undefined reads; runtime shadowing (`EVAL:express.cpp#L1320`) | Erased | Declare; engine-exact rename; pick a candidate |
| 2 | A maybe-undefined global is read only through an existence test that narrows it: the corpus idiom `X == X` for types with an equality overload, or after a definite write | Nil propagation (§3.1); 252 idiom lines | Nothing to lower: the idiom is SQF | Wrap the read; a Bool campaign variable gets a definite initial write (Bool has no `==`) |
| 3 | Code is a type: code sinks accept `Code<Ctx>` only; `format`, `+` or `loadFile` results never reach a sink outside raw; literal `loadFile`/`preprocessFile` paths resolve to project files with contracts | Doc 24 F7; no engine Code type | `{…}` or quoted strings, re-escaped per nesting level (doc 31 §7.3) | Turn a string into a block; move the dynamic part into a user raw block |
| 4 | References resolve: markers, classes, sounds, script paths, labels, objective ids; a computed name is `Text` unless a declared **name family** (for example `lz_%1` over declared markers) proves every value | 18 unresolved script references in official content, 19 with the mod library (doc 35) | Erased | Pick from resolved candidates; declare the family |
| 5 | Enum words come from the engine's tables, exactly | `GrpSetBehaviour` ignores unknown words; 10 unrecognised in official content | Erased | Pick |
| 6 | `Object?` and `Group?` from commands that can yield null, narrowed by `isNull` or `alive` before commands that would silently no-op | With `--strictNullChecks`, "22 bugs, an increase of 58%, are detectable under TypeScript 2.0 but not under TypeScript 1.8" (Gao et al.) [V-author] | Erased | Insert the guard |
| 7 | Function contracts at the `_this` boundary of `exec`, `call` and `fn\TAG_*.sqf` libraries (doc 31 §7.3): parameter and result types | `_this` parameters cause most implicit "any" in the mod library (§3.2) | Comment header or sidecar | A signature skeleton inferred from the call sites |
| 8 | Field and file context: statement kinds per check mode; no top-level `,` in fields; locals only where a local space exists | Doc 23 §6 | — | Wrap in `call {…}` |
| 9 | SQS line model: lines ≤ 4,095 bytes, `~` expression ≤ 233 bytes, no `:` inside a `?` condition string, labels resolved and unique | Doc 23 §5 | — | Mechanical |
| 10 | Locality markers on multiplayer targets: a script or function declares where it runs (server, every machine, the owner of an object); commands with curated locality rows are checked against it; generated code gets the compiler-owned server guard (doc 31 §4.5) | Locality is in no signature (§4.6) | Erased | Add the marker; move the call into the guard |
| 11 | Every overload and syntax feature is available on the target profile | Doc 23 §13.3 item 1 | — | A fix-it rewrites to the profile's form (§4.2) |
| 12 | No condition reads a Nothing-valued command or a developer cheat variable | 14 files; 189 fields (§3.3) | — | Quarantine |

Illustration (not a spec; the syntax is SG3). SQS keeps `;` lines as comments that the engine never stores
(`engine/Poseidon/Game/Scripting/Scripts.cpp#L240-L244`) [V], so declarations cost nothing at run time:

```text
; @strict
; @param _grp: Group
; @param _lz: MarkerName
; @reads extract_ready: Bool
_grp = _this select 0
_lz = _this select 1
@ extract_ready
_grp move getMarkerPos _lz
_grp setBehaviour "AWARE "
exit
```

The last statement fails the contract (rule 5); the finding a person sees (§4.9):

```text
error[strict.enum.unknown]  extract.sqs, line 9   setBehaviour: "AWARE " is not a behaviour
  The engine ignores an unknown behaviour without an error, so the group keeps its old behaviour.
  expected: one of CARELESS, SAFE, AWARE, COMBAT, STEALTH, UNCHANGED (case does not matter)
  fix A: use "AWARE"     fix B: choose another behaviour     (each is one undoable edit)
```

A function library file loaded by `preprocessFile` carries its contract in `//` lines, which only preprocessed SQF allows (doc 31 §8.3):
`// @fn TAG_fnc_nearestEnemy (_unit: Object, _radius: Scalar) -> Object?`. Code fields in `mission.sqm` and raw-loaded code have no
comment syntax the engine skips, so their declarations live in the export-excluded sidecar and show in the editor's gutter [I].

### 4.9 Diagnostics that name the fix

1. **First line:** what is wrong in product words, and its consequence at run time ("would be shown, not run"; "the engine ignores it
   silently").
2. **Name the class of guarantee** it protects (§3.2), so the reader learns why Strict exists.
3. **Expected and found** as types the user knows (marker name, group, code), never bitmasks.
4. **Every fix is a `FixId`** with a preview; the mechanical fix first. The escapes (raw, downgrade) come last and are offered only to
   the user, never in a model's repair menu (doc 62 §3.3: guidance never widens a guard).
5. **`requires`** explains the profile ("`for` needs CWR; on `Cwa199` use a label loop").
6. **Stable codes** with a failing and a passing fixture each (DG005): the equivalent of `--explain`.
7. **Mission text is data:** names are quoted through the sanitizer and never phrased as instructions (doc 61 §4.5).
8. **One set of fields, two renderings:** terse for people, detailed for models (doc 61 §2.2); one root finding per model turn, related
   findings grouped (doc 62 §6.9).
9. **In Advisory regions** the same finding reads as advice, with "Make this file Strict" offered when it would pass.

### 4.10 Levels

| Level | Contract | Blocks | Proposed default for | Promotion |
| --- | --- | --- | --- | --- |
| **Off** | Floor only; Teller's lints hidden for this file (still counted by the readiness model) | The floor | Nothing by default; a user's choice for a library they do not want flagged | — |
| **Advisory** | Luau's non-strict contract: only findings that are certain (a definite no-op, a type error, an unresolved literal reference) and the silent-failure lints of doc 31 §7.2; unknown values are `dynamic` | The floor | Imported files and files people write | "Make Strict" offered when the file would pass, and applied only on a click (spoom's `bump`) |
| **Strict** | §4.8 | Floor plus contract errors | Every region generated or proposed by a non-user origin; any file, field or mission a user opts in | — |

- **Where it is set:** a header line (`; @strict`, `// @strict`) or the sidecar per file; the sidecar per field; a mission and campaign
  default in settings. A project or campaign may add "forbid raw".
- **What is visible:** a level badge per file; gutter marks on lines the gate proved (GDScript's "safe lines"); a mission badge beside
  "Requires", such as "92% of code Strict-checked · 2 raw blocks"; the audit of §4.5.
- **Measurement first.** Advisory's false-positive rate is measured on the corpus before it is on by default (ST-21), because a warning
  people learn to ignore is the Luau lesson.
- **The ratchet is the owner's call** (open question 1): stay opt-in (recommended); or make new files Strict by default once Advisory
  and Strict are measured, which fits D011 only if a contract error in a user region blocks nothing (SG1 option (c)), since a default
  the user never chose must not become a wall; a Hack-style "Strict only" is ruled out by D011.

### 4.11 No-code modules emit Strict-clean code by construction

- **References are ids** (`MarkerId`, `UnitId`) resolved to names only at lowering, so a rename cannot leave a dangling string (doc 31
  §7.1); enums are Rust enums; counts and ranges are typed.
- **Code is built through a typed emitter**, generated from the catalog so that each command builder takes typed operands and an
  ill-typed call cannot be written (sketch, not compiled):

```rust
fn set_behaviour(target: Expr<GroupOrObject>, mode: Behaviour) -> Stmt;   // Behaviour: the engine's CombatMode table
fn exec_script(args: Expr<Array>, script: ScriptRef) -> Stmt;             // ScriptRef resolves through the project, never a string
fn when(cond: Expr<Bool>, body: Code<Stmt>) -> Stmt;                      // `?` plus goto on Cwa199; `if … then {…}` where allowed
```

- **Translation validation.** Every emitted line is re-checked in Strict and in its field mode (doc 23 §13.3 item 4; doc 31 N7);
  property tests sweep module parameters on every profile (ST-02).
- **Detach to script** (doc 31 N1) yields a file that is already Strict-clean, so a user's first edit starts from a checked file; region
  states (doc 31 §8.3) keep human edits.

### 4.12 Import, lift and auto-migration

- Imported scripts open at Advisory with inference (a set of possible types per variable, like HEMTT's inspector) [I].
- **Lift** is offered per file or field when inference closes with no unknowns. Doc 31 §8.2's rule applies: rewriting is offered only
  when re-emission reproduces the normalised original; otherwise only declarations are added, which erase.
- **Auto-migrations** are previewed, undoable `Migration` commands, never silent: declare `X == X` names as maybe-undefined (§4.8 rule
  2); engine-exact rename of names that shadow commands (doc 31 §7.3); quarantine developer cheat triggers (disabled and kept, visibly);
  the `private _x =` rewrite for `Cwa199`. On official content they raise units passing C from 95.6% to 97.9% (SQS files 72.4% to 86.6%,
  fields 96.9% to 98.6%) and missions from 44% to 55% [M-local; the estimator modelled the `X == X` case as a rewrite].
- What remains needs a person or context: undefined globals are mostly real defects; campaign variables need the Tote; libraries need
  signatures.

### 4.13 Editions

- Teller's rule set is pinned per project as an edition. New Strict rules arrive as warnings; they become contract errors only when the
  user opts into the next edition, with a migration assist (a batch of `FixCmd`s), like Rust editions and unlike Reforger 1.1 (§2.2) [I].
- A catalog regeneration after an engine release (doc 23 §14.3) raises new `ProfileError`s only on the profiles it changed.
- Because output is erased, an edition or checker change never breaks an exported mission; it changes only what the next export accepts.

### 4.14 What stays a runtime concern

| Concern | Why it cannot be proved statically | Where it is handled |
| --- | --- | --- |
| Trigger ordering and latency | 0.5 s simulation step with a random phase (doc 31 §5.3) | Rule flags; Preview's "why didn't this fire?" (doc 31 §5.4) |
| AI behaviour and pathing | World state | Preview probes and smoke runs (validation-and-lints §11) |
| World-dependent nulls | Run-time values | Nullability rules (§4.8 rule 6) plus Preview |
| Iteration caps, SQS step budget | Run-time counts | Lints where static; Preview otherwise |
| Multiplayer locality | Who owns an object is decided at run time | Locality markers, MP Preview (doc 08) |
| 1.99 semantics of names never probed (T2, T3) | No source for 1.99 | Probes; on `Cwa199` a debug export with `hint` tracepoints (doc 31 §7.5) |
| Anything inside raw | Not certifiable (doc 24 F7) | Advisory findings; the risk gate |

The P1 strict Preview launch, where a script error ends the run (game-integration §6), is the runtime backstop on `Cwr` and `Ce`. The
badge says "Strict-checked", never "correct": a gate removes classes of error; specification and logic errors remain (§2.4, Tambon et
al.).

## 5. The LLM side

### 5.1 Wilco writes, Teller checks, one root per repair

A proposal is planned on a `Scratch` fork and admitted through the floor plus the Strict contract (commands-undo-history §4.1–§4.2). A
rejection returns one root finding with the recomputed allowed values and a fix menu (doc 25 §7.2; doc 61 §4.6), then the preset decides
repair or resample. Doc 61's rules carry over unchanged: only findings the proposal introduced are quoted; pre-existing user code is not
the model's to fix; the loop stops on a repeat, on no progress or when R is spent; a repair that clears a finding by deleting code is
flagged. A clean admission costs no tokens (D026).

### 5.2 Quick fixes as typed commands

Every Strict finding offers `FixId`s (validation-and-lints §6), which the model picks from a consumable menu (doc 61 `fix.options`,
`fix.apply`); the chosen fix runs the same command a user's click runs. A fix's output must pass at the target's level (ST-14). Picking a
fix is a bounded decision a weak model can make (doc 25).

### 5.3 Who writes what on the ladder

| Freedom level (doc 63) | Script surface | Gate | Teller surface (doc 61) |
| --- | --- | --- | --- |
| FR0–FR4 | **No script text.** Typed IR slots: modules, rule templates, CXL slots, enum and reference ids from code-built menus (at FR0 code fills them with no model) | Strict by construction plus the re-check | TS0 at FR0; TS1 (push only) at FR1–FR4 |
| FR5 | One Strict snippet in one field or file (a condition, an init line, a short SQS sequence) | Strict at admission; `script.check` before submitting at Thorough or Max effort | TS2 |
| FR6–FR7 | Several Strict files and fields as a draft on a `Scratch` fork, one dry-run admission | Strict | TS3 |
| FR8 | No script text of its own: a plan over registered workflows, whose nested steps follow the rows above | Per nested step | TS3 for nested steps only (doc 63 §3.1) |
| Any | **Raw** | Not available to any model | — |

This matches doc 31 §9 (weak models fill forms and never write glue) and doc 30's measurement that weak models fail on command forms and
whole files, which the IR removes. The dialect is the text a model writes once it qualifies for script Compose (doc 53 DP-19).

### 5.4 Strict in the presets: the surface is a knob, the gate is not

D048 item 2 says a preset changes how Wilco asks, never what code owns, and doc 55 §2.3 lists "admission and every validator" among the
settings that are not knobs. So if adopted, the Strict gate on model output would be fixed for every preset. What a preset may choose
per `DecisionKind` [I]:

- **The authoring surface:** IR slots, the dialect with inferred types only, or the dialect with required signatures;
- **the typed context card:** declared globals, markers and enums for the step's symbols (the typed-context evidence of doc 61 §2.5);
  MultiPL-E suggests it helps only together with the checker (§2.4);
- **diagnostic rendering:** terse or detailed, repair or resample, R within effort;
- **local decode constraints:** a grammar over catalog arity (doc 30 §4.5) and, experimentally, a type-level monitor, under doc 61 §4.8's
  completeness rule (a constraint may reject only what the checker would reject). Doc 61 §4.8 states that rule against `check_field`
  (parity) and doc 62 §6.9 against "everything the engine can run for the target profile"; a Strict-level monitor would reject more,
  which is sound only for output that must pass Strict anyway. The two statements must be reconciled if the owner adopts Strict for
  model output (Findings for sibling docs); until then a monitor stays at parity completeness [I];
- **cloud decode help:** code enumerates the typed options per slot into JSON enums; grammars there are syntax-only.

No preset may lower the level for model output, allow raw, or allow trusted ascriptions. SG11 asks doc 55 to add the surface knob.

### 5.5 Closing the escape routes

- **No widening.** A model's Strict output has no `dynamic` or `unknown` escape: an unknown must be resolved (declared, narrowed, picked),
  never widened. This answers the 9× `any` finding (§2.4).
- **No raw, no ascription over unknown values, no edits inside raw blocks, no acknowledgements** of contract errors (validation-and-lints
  §6 already says Wilco may propose, never apply, an acknowledgement).
- **Qualification counts attempts.** Output containing raw markers, string-built code or declarations that contradict inference is a
  must-pass failure in qualification (doc 63 §4.3 item 3), and the count is reported per setup.
- **No model reaches the checker's inputs:** catalog, overlay, editions and levels are code and user settings (doc 62 §6.3, the
  ImpossibleBench lesson).
- **Advisory is never repaired.** Doc 61 §4.6 item 4's rule that `Advisory`-severity findings never enter a repair turn and never block
  holds (D011). Note the two senses: the Advisory *level* of §4.10 names a file or region setting whose findings may have any
  non-blocking severity, while `Advisory` is also a severity (validation-and-lints §3); SG4 should give the level another name.

## 6. Experiment: plain versus Strict for weak models (plan only)

Nothing here has run. The design mirrors doc 64's draft pre-registration for Rust (a synthetic domain, PLAIN against GUIDED, a nested
repair loop, task-level analysis) and must be re-aligned with it when doc 64 is published. Research tooling goes under `tools/`; it
evaluates Wilco's harness, and no product feature executes code.

### 6.1 Questions and hypotheses

- **RQ1.** Do small local models write more correct mission scripts in the Strict dialect with Strict diagnostics than in plain SQF/SQS
  with floor diagnostics?
- **RQ2.** Does Strict reduce *accepted but wrong* scripts, which pass every check shown to the model and fail a hidden one?
- **RQ3.** Is the repair loop worth more under Strict?
- **RQ4.** Does a small model with Strict reach a larger model's plain level?
- **RQ5** (exploratory). Which ingredient carries the effect: rejection (contract errors), forced handling (nullability, existence), the
  typed context card or the fix menus? At what token cost? How far is the IR-slot ceiling?

Fixed-sequence confirmatory tests as in doc 64: **H-SQ1** hidden pass at R ≤ 3 is higher for STRICT than PLAIN, small models pooled;
**H-SQ2** (only if H-SQ1 holds) accepted-but-wrong is lower; **H-SQ3** the loop's gain (R ≤ 3 minus R0) is larger for STRICT; **H-SQ4**
per small model, STRICT at R ≤ 3 is non-inferior to the comparator's PLAIN within −10 points. Two-sided; a harmful result is
informative (annotations are rare in training data).

### 6.2 Tasks, arms and traps

- **Tasks.** 30 scored and 4 pilot tasks over missions authored for the experiment: trigger conditions and activations, unit init
  lines, SQS sequences with waits and labels, an SQF function with a contract, a server-guarded multiplayer script. Each task gives a
  spec, a mission context (declared symbols) and visible checks; hidden checks are never shown. Profile `Cwr`; a `Cwa199` subset is
  checked statically only and reported apart.
- **Arms.** PLAIN: catalog cards for the task's commands and the mission's symbol list; the model writes plain SQF/SQS; feedback is the
  floor plus Advisory findings in doc 61's repair-card form. STRICT: the same cards plus a dialect card (at most 150 words) and the typed
  context card; output must pass Strict; feedback is Strict findings with fix menus. Exploratory: IR (fill a module or rule template's
  typed slots), STRICT with a local decode monitor, and STRICT without the typed context card.
- **Trap classes** (doc 64's S/F/R): **S**, rejected statically by Strict and accepted by the floor (an enum word with a trailing space,
  a misspelt global or marker, text where code is expected, `this` used as an object in a trigger activation, a `goto` to a missing
  label, a name that shadows a command on `Cwr`); **F**, handling Strict forces (a unit that may be dead or absent, a campaign variable
  that may be undefined); **R**, runtime-only controls (trigger ordering, AI completion timing). Predicted: the gain is largest for S,
  smaller for F, near zero for R; if R improves too, the gain is more likely the cards than the types.

### 6.3 Oracle and hidden checks

1. **A static oracle independent of Teller:** the ported transliteration of the engine's evaluator, test-only (doc 23 §13.2), plus a
   reference symbol table per task, so a Teller bug cannot grade itself.
2. **Behavioural checks in CWR Preview** through the harness: after a scripted timeline, fixed read-only expressions read the state
   ("the group's behaviour is AWARE", "the marker moved"). A runtime script error ends a `--test-mission` run (doc 31 §7.4), which the
   oracle records as a failure. This part needs the owner's install and stays local and opt-in (AGENTS.md fixture rules).
3. **Never fed back:** hidden checks, their names, oracle findings and trap labels.

### 6.4 Models, loop, metrics and analysis

- **Models** as doc 64's draft: three small local models and a larger comparator, pinned when frozen; cloud hosts chosen under D047
  (mission tasks are combat-flavoured).
- **Loop** (doc 64's nesting): R0 is the first attempt of the same episode; up to three repair rounds; outcomes at R0, R ≤ 1, R ≤ 2,
  R ≤ 3, last code carried forward.
- **Metrics per round:** floor_ok, strict_ok (STRICT arm), visible_pass, **hidden_pass** (primary), accepted_but_wrong, trap_fail per
  class. **Per episode:** rounds used, tokens (prompt, cached, completion), tokens per success, escape attempts (raw markers, string-built
  code, contradicted declarations), fix rate per diagnostic code, generation and Preview time.
- **Analysis:** task-level paired differences, sign-flip test, task-cluster bootstrap. If doc 64's power simulation carries over (its
  draft: 30 tasks, 6 samples per cell, about +10 points detectable at 74–91% power), the same size applies: 30 × 6 × 2 arms × 3 models =
  1,080 small-model episodes [I].
- **Cost:** Preview adds roughly one to two minutes per distinct code version checked, so about 30–40 hours of unattended game time for
  the small models, unless several tasks share one launch (a harness question) [I; U].

### 6.5 Decision rules

| Rule | If | Then [I] |
| --- | --- | --- |
| DR-SQ1 | H-SQ1 holds at ≥ +10 points and H-SQ2 is not worse | The dialect with required signatures becomes the default surface for script Compose (FR5+) in the default preset; the typed context card ships |
| DR-SQ2 | The gain appears only with the loop (STRICT R0 ≤ PLAIN R0) | The loop is mandatory for every script step (already doctrine); presets carry R |
| DR-SQ3 | STRICT is worse (95% interval below 0) | Keep the gate on model output; ask models for plain SQF checked by inference-only Strict; move small models to IR slots only |
| DR-SQ4 | Equivalent within ±5 points | The dialect's value is for people and for the gate; stop citing it as a weak-model lever |
| DR-SQ5 | Inconclusive | A new pre-registration with more tasks, not more samples |
| DR-SQ6 | H-SQ4 holds for a model | "Punches above its weight" may be stated for that model, this domain and this loop |
| DR-SQ7 | STRICT tokens per success above 1.5× PLAIN | Trim cards before dropping types |
| DR-SQ8 | Per-model estimates disagree in sign | Per-model knobs in the presets |

No outcome turns the gate off for model output: the experiment decides the authoring surface and the knowledge given, not whether
generated code is checked.

### 6.6 Threats and prerequisites

- **Threats:** allegiance (the authors expect STRICT to win; neutral task text, reviews and frozen hashes as in doc 64); a prototype
  checker; Preview nondeterminism (random trigger phase); synthetic missions; few tasks.
- **Prerequisites:** Teller's parity checker (doc 23 P1) and a Strict prototype; the ported oracle; a Preview launch that the oracle's
  own reads cannot abort (DG001); doc 64's harness reused under `tools/`.

## 7. Reuse, licences and requests

### 7.1 What to port, borrow or avoid

Upstream pins re-checked on 2026-09-28: `BohemiaInteractive/CWR@ffc61838b7`, `ofpisnotdead-com/CWR-CE@b67bf3bd62` (the command tables
differ only in the `endGame` row, doc 23 §3.2), `DK26/CWR@6fd6ca3974` [V].

| Source | Licence | Use [I, consistent with doc 23 §11–§13] |
| --- | --- | --- |
| DK26/CWR `lsp/` (the owner's fork) | GPL-3.0-or-later; engine-derived parts carry CWR's §7 terms | **Port and restructure** (doc 23 §13.1): type algebra, precedence, oracle (test-only), vectors; no trademark-bearing hover text |
| CWR and CE engine source | GPL-3.0-or-later with §7 terms | **Generator input**: tables, enum-name tables, handler shapes, locality rows, each with file:line |
| HEMTT `libs/sqf` (`885c4acaaf`) | `GPL-2.0` in `libs/sqf/Cargo.toml`, the deprecated SPDX id for GPL-2.0-only; the root `LICENSE` is the plain GPLv2 text [V; no legal review] | **Design reference only**; cannot be linked into GPL-3.0 code. Ideas: type-set inference, orphan-scope handling, non-reducible critical lints |
| armalint (`83a2582828`) | MIT | Ideas: suppression with a justification (W229), remote-execution and public-variable contracts (W220, W221) [V README] |
| sqflint, vscode-sqflint | MIT | Arma 3 semantics; would reject legal OFP code such as `then "string"` (per research pass). Ideas only |
| sqf-analyzer (`f01addc5b7`) | No licence file | Reference only |
| SQF-VM runtime and language server | LGPL-3.0 | Ideas: unused and unassigned variable lints, scripted analyzers |
| TypeSqf (SQX) | Editor MIT; analyzer a closed binary | Reference only |
| ASL | MIT | Reference only (untyped) |
| `acemod/arma3-wiki` data; BI wiki | Data licence not stated (GitHub licence field null; wiki rights info empty) [V per research pass] | Dated facts only (names, versions, syntax skeletons), as doc 23 §14.1 says |
| Armitxes/VSCode_SQF | CC-BY-NC-SA-4.0; commits `node_modules`, including `flatmap-stream` (the 2018 event-stream incident package), which the host's antivirus flagged | **Avoid**; do not clone |
| Teal, TypeScript docs, Luau papers | MIT and public docs | Design references |

### 7.2 Engine-request candidates (for `docs/upstream/`, not filed)

Each is an opt-in capability of the `Ce` profile, never a requirement (D012):

1. **A command-table dump**, like Arma 3's `supportInfo`, from the real `GameState` tables (`EVAL:express.hpp#L698-L700`) after the game
   module registers them: our generated catalog is then checked against each built release, not only against parsed source.
2. **An opt-in warning for unknown enum words** in setters such as `setBehaviour` (`GameStateExtGrp.cpp#L171-L191`).
3. **Runtime type introspection** (`typeName`- or `isNil`-like), so raw-to-typed boundaries become checked casts on `Ce`.
4. **A warning when a set variable shadows a command** (the `#L1320` behaviour). Doc 24's P8 (`--script-policy untrusted`) is related.

### 7.3 Design-gap candidates (listed, not filed)

1. **SG1 Contract severity.** Options (a)–(c) of §4.4: `ContractError` blocking only inside regions the user made Strict, blocking
   with an in-refusal downgrade, or no new blocking for user regions; its Preview and export behaviour; D011 item 3,
   validation-and-lints §1 principle 2 and §3; DG005.
2. **SG2 Levels.** Off / Advisory / Strict per file, field and mission; where they are stored (sidecar); the "forbid raw" policy.
3. **SG3 Declaration syntax per load path:** `;` in SQS, `//` in `preprocessFile`d SQF, sidecar for `mission.sqm` fields and raw-loaded
   code; a probe that each path ignores them as expected.
4. **SG4 Names:** the dialect, its levels and any file marker, through the names table (D034) and the trademark rule; no clash with the
   strict Preview launch, the engine's `--strict`, "strict admission of model output" (agent-runtime §6), the `Advisory` severity
   (validation-and-lints §3) or TypeSqf's `.sqx`.
5. **SG5 The raw block:** form, user-only creation, reason, fingerprint (reusing validation-and-lints §7), stale detection, audit counts.
6. **SG6 Existence and nullability:** the `X == X` narrowing rule, Bool campaign variables, how strict `Object?` is (open question 5).
7. **SG7 The gate witness:** `Checked<S>`, `GatedSnapshot`, and the `stage` and export signatures (game-integration §5).
8. **SG8 Refinement catalog:** the string-kind overlay, enum tables, shapes, element types and locality rows as generated data with
   citations (extends doc 23 §14).
9. **SG9 Campaign-variable typing** over the campaign graph, path-sensitive, owned by the Tote (doc 19 §4).
10. **SG10 Editions** and migration assists.
11. **SG11 Authoring-surface knob** in the preset catalogue (doc 55 §2.1), with the gate listed among the non-knobs.
12. **SG12 Anti-escape rules for non-user origins:** no raw, no trusted ascription, no widening, as admission checks
    (commands-undo-history §4.2); Wilco writes no dynamic code even on request (doc 24 §5.3 rule 2; §4.4 item 6).
13. **SG13 Auto-migrations at import** as previewed `Migration` commands (§4.12).
14. **SG14 Advisory false-positive gate:** the corpus measurement that must pass before Advisory is on by default (ST-21).

## 8. Friction review (D049)

| Audience | Friction Strict introduces | How it is removed or made visible [I] |
| --- | --- | --- |
| People writing scripts | Declarations to write; contract errors on opted-in files | Inference first (declarations only at boundaries); signature skeletons as fixes; one-click downgrade; no user file Strict by default in v1 (open question 1) |
| People importing missions | Many findings on old content | Advisory, certain findings only; previewed auto-migrations; per-mission counts instead of a wall |
| Models | Rejections they must repair | One root finding with a fix menu; typed context card; IR slots for small models; no prose to parse |
| Contributors | A third verdict level, an overlay to maintain | Generated from pinned source with citations; drift tests (doc 23 §14.3) |

Friction removed: silent failures (no-op enum words, typo'd globals, labels that exit a script) surface while writing, not in a Preview
run or after release; models stop spending repair rounds on command forms.

## 9. Tests to write first

Each fails before its feature exists (AGENTS.md "Test-First / Proof-First") and follows AGENTS.md's documentation and section rules.
Crates follow crate-map (`plotroom-teller`, `plotroom-lower`, `plotroom-commands`, `plotroom-preview`, `plotroom-export`).

| Id | Test | Crate |
| --- | --- | --- |
| ST-01 | `strict_gate_never_accepts_what_engine_check_mode_rejects` (differential against the ported oracle and engine vectors, per profile) | `plotroom-teller` |
| ST-02 | `every_module_lowering_passes_strict_and_parity_on_its_profile` (property test over module parameters) | `plotroom-lower` |
| ST-03 | `erasing_declarations_reproduces_the_plain_bytes` | `plotroom-teller` |
| ST-04 | `stage_and_export_accept_only_a_gated_snapshot` (API plus a layering check; trybuild if doc 62 §8 is approved) | `plotroom-preview`, `plotroom-export` |
| ST-05 | `non_user_origin_cannot_create_widen_or_edit_inside_a_raw_block` (Wilco, workflow, plugin, external) | `plotroom-commands` |
| ST-06 | `wilco_proposal_with_contract_error_is_rejected_with_allowed_values` | `plotroom-commands` |
| ST-07 | `downgrading_a_strict_region_is_one_undoable_group_and_updates_the_badge` | `plotroom-commands` |
| ST-08 | `advisory_level_never_blocks_beyond_the_floor` | `plotroom-teller` |
| ST-09 | `unknown_enum_word_is_a_contract_error_in_strict_and_a_warning_in_advisory` (`"AWARE "`) | `plotroom-teller` |
| ST-10 | `object_command_on_this_in_trigger_activation_is_rejected` | `plotroom-teller` |
| ST-11 | `global_named_like_a_command_is_an_error_only_on_profiles_that_register_it` (`endGame` on `Cwr`, not `Cwa199` or `Ce`) | `plotroom-teller` |
| ST-12 | `format_built_code_reaching_a_sink_is_rejected_outside_raw` | `plotroom-teller` |
| ST-13 | `self_equality_narrows_maybe_undefined_global_and_bool_self_equality_is_rejected` | `plotroom-teller` |
| ST-14 | `quick_fix_and_migration_never_add_a_finding_at_the_target_level` | `plotroom-teller` |
| ST-15 | `raw_block_whose_contents_pass_strict_reports_can_be_lifted` | `plotroom-teller` |
| ST-16 | `raw_block_without_a_reason_is_refused` | `plotroom-commands` |
| ST-17 | `strict_check_twice_on_one_snapshot_is_byte_equal` (determinism) | `plotroom-teller` |
| ST-18 | Boundaries: SQS lines of 4,095 and 4,096 bytes; `~` expressions of 233 and 234 bytes; a `:` inside a `?` condition string | `plotroom-teller` |
| ST-19 | Adversarial: declaration comments with hidden characters, 10 KB names, `@raw` markers inside string literals (not honoured), unbalanced raw markers; no panic, no verdict change | `plotroom-teller` |
| ST-20 | `edition_bump_turns_new_rules_into_errors_only_after_opt_in` | `plotroom-teller` |
| ST-21 | Advisory false-positive report on the owner's corpus (opt-in, environment-gated, local only; aggregate output) | `plotroom-teller` |
| ST-22 | `lowering_for_cwa199_emits_only_the_primer_subset` (`?`, `goto`, `@`, `~`; I35-PRIMER-FACTS) | `plotroom-lower` |
| ST-23 | `only_user_intent_raises_a_user_region_to_strict` (no workflow, preset, plugin, pack, import or migration changes a user file's, field's or mission's level; D011 opt-in) | `plotroom-commands` |

## Open questions

1. **Owner:** the ratchet (§4.10): Strict opt-in only; or new user files Strict by default after measurement (non-blocking for user
   regions, SG1 option (c))? [I; recommended: opt-in in v1, revisit with ST-21 and §6's results]
2. **Owner:** in a region the user made Strict, does a contract error (a) block export and gate Preview behind the audited "Preview
   anyway", (b) do the same with "downgrade and export" offered in the refusal, or (c) block nothing and only withhold the
   "Strict-checked" badge, as D011 item 3 reads today (§4.4; SG1)? Non-user origins are gated in every option. [I]
3. **Owner:** does "forbid raw" ship in v1, and may a registry require it for packs? [I]
4. **Technical:** do `;` SQS comment lines and `//` lines in `preprocessFile`d SQF behave identically on 1.99, and is there any path that
   stores or evaluates them? (SG3; a probe) [U]
5. **Design:** nullability strictness: is a command on a maybe-null `Object` an error or a warning, given most such commands silently do
   nothing on `objNull`? [I]
6. **Design:** in a user's Strict file, is an "unverified on `Cwa199`" overload a warning with the tier (proposed) or an error? [I]
7. **Technical:** did 1.99's check mode apply the same Execute and Bool rules as CWR (doc 23 open question 3)? It decides class A on
   `Cwa199`. [U]
8. **Technical:** can the Advisory contract reach near-zero false positives on the corpus without the mod's replacement config? [U]
9. **Measurement:** §6's H-SQ1–H-SQ4. [U]
10. **Design:** how far can definite initialisation reach across triggers when the compiler does not own init order? [I]
11. **Design:** are name families (§4.8 rule 4) enough for the computed marker and unit names real missions use, or do they need raw? [U]

## Findings for sibling docs (reported, not fixed)

- **Validation-and-lints §3** ("Nothing else blocks export or Preview") needs SG1 if the owner adopts Strict regions; §9's Teller table
  gains a "Strict contract and levels" row.
- **Doc 23 §13.3 item 2** ("The AI gate … parity plus lint at `error` severity") becomes "parity plus the Strict contract"; §13.4's schema
  gains a `level` (parity, lint, contract) and a `guarantee` field.
- **Doc 23 §3.3**: the fork's unknown-type-as-anything mapping must be a generator error, not only a weakness.
- **Game-integration §5**: `stage(snap: &Snapshot, …)` would take a gated snapshot (SG7).
- **Doc 55 §2.1 and §2.3**: add the authoring-surface knob; the gate stays among the non-knobs (SG11).
- **Doc 31 §9**: "raw SQS allowed only in the Expression rung" reads as "the Strict dialect in the Expression rung; raw is user-only".
- **Doc 62** (its governing principle) names this doc as its application to mission scripts; §4 here is that application.
- **Doc 63 §4.2**: the "Script snippets" product ceiling (FR5, behind `check_field`) becomes "FR5, behind the Strict contract".
- **Naming:** "strict" is already used by game-integration §6's P1 launch, by the engine's `--strict` flag and by "strict admission of
  model output" (agent-runtime §6; doc 21; doc 61 §4.6 item 1); "Advisory" is also a severity (SG4).
- **Doc 61 §4.8 and doc 62 §6.9**: the completeness rule for decode-time constraints is stated against parity and against "everything
  the engine can run"; if Strict applies to model output, both would read "a superset of what admission accepts for that origin" (§5.4).
- **Doc 24 §5.2 L4 and F10**: nothing changes; §4.5 only states that the "fully checked" badge counts L4 sinks and F10 config
  expressions like raw unless they pass Strict. §4.4 item 6 follows doc 24 §5.3 rule 2 (no AI-proposed dynamic code).
- **D011 and validation-and-lints §1 principle 2 and §3** (SG1 decided 2026-09-28 → D052: option (b), refined with a "Preview once" exception and an export-time downgrade): only SG1 options (a) and (b) would need an owner ruling; option (c) needs
  none.

## Sources

All read on 2026-09-28 unless stated.

### Engine and tools (commit pins; file:line citations are in the text)

- <https://github.com/BohemiaInteractive/CWR> at `ffc61838b7e756bec56aafafbf390396e639ac8f`: `engine/Evaluator/express.hpp`,
  `engine/Evaluator/express.cpp`, `engine/Poseidon/Game/Commands/GameStateExt.hpp`, `GameStateExt.cpp`, `GameStateExtGrp.cpp`,
  `engine/Poseidon/AI/ArcadeTemplate.cpp`, `AIArcade.cpp`, `AICenterImpl.cpp`, `engine/Poseidon/World/Detection/Detector.cpp`,
  `engine/Poseidon/World/WorldInit.cpp`, `engine/Poseidon/Game/Scripting/Scripts.cpp`, `engine/Poseidon/UI/Map/UIArcade.cpp`
- <https://github.com/ofpisnotdead-com/CWR-CE> at `b67bf3bd623a52d62456c3ef65f7e0e0163dcd9b` (registration grep)
- <https://github.com/DK26/CWR> at `6fd6ca39748f3ab2e086f79122d7e256453151d2`: `lsp/crates/poseidon-syntax/src/check.rs`,
  `lsp/skills/poseidon-scripting/SKILL.md`
- <https://github.com/BrettMayson/HEMTT> at `885c4acaaf12d34d2a258ac87c71a6986c14bf45`: `libs/sqf/Cargo.toml`,
  `libs/sqf/src/analyze/lints/s13_undefined.rs`; <https://hemtt.dev/lints/sqf.html>
- <https://github.com/armachisel/armalint> at `83a258282a63dea230703395da9820863bf34812` (`README.md` rule table)
- <https://github.com/SkaceKamen/sqflint> at `bfc89b5c21d3651907f1208e3c208f60c6b13f60`; <https://github.com/SkaceKamen/vscode-sqflint>
- <https://github.com/sqf-analyzer/sqf-analyzer> at `f01addc5b75c8e9dc4b03b367c77ed24ff7e0f0a`
- <https://github.com/SQFvm/runtime> at `ed9f5f58a991ed00ff59858e68e01ffcaab89e04` (`src/sqc/ReadMe.md`, `src/sqc/sqc_parser.cpp`); <https://github.com/SQFvm/language-server>
- <https://github.com/XEngima/Apps-TypeSqfEdit> at `f7f8de7ee3f9c807d8dc553ed8aefe88a49628bd`; <https://github.com/Kugelschieber/asl> at
  `5fe69dc3d485ba1857744f125cdba875c435e02b`; <https://github.com/X39/ObjectOrientedScripting>; <https://github.com/DavisBrown723/SQF_plusplus_Transpiler>
- <https://github.com/acemod/arma3-wiki> (dist branch); <https://community.bistudio.com/wikidata/api.php> (the `params`, `typeName` and
  `SQF_Bytecode` pages; site rights info)
- <https://github.com/Armitxes/VSCode_SQF> (licence only; not cloned again)

### Typed layers, gates and escape hatches

- <https://www.typescriptlang.org/tsconfig/noEmitOnError.html>; <https://github.com/microsoft/TypeScript/wiki/TypeScript-Design-Goals>;
  <https://www.typescriptlang.org/docs/handbook/type-checking-javascript-files.html>; <https://typescript-eslint.io/rules/ban-ts-comment/>
- <https://stripe.dev/blog/sorbet-stripes-type-checker-for-ruby>; <https://sorbet.org/docs/static>; <https://sorbet.org/docs/gradual>;
  <https://sorbet.org/docs/metrics>; <https://github.com/Shopify/spoom>
- <https://raw.githubusercontent.com/microsoft/pyright/main/docs/configuration.md>; <https://raw.githubusercontent.com/microsoft/pyright/main/docs/comments.md>;
  <https://dropbox.tech/application/our-journey-to-type-checking-4-million-lines-of-python>
- <https://hhvm.com/blog/2020/03/09/hhvm-4.48.html>; <https://hhvm.com/blog/2020/06/16/hhvm-4.62.html>;
  <https://hhvm.com/blog/2021/11/08/hhvm-4.135.html>; <https://docs.hhvm.com/hack/silencing-errors/introduction>
- <https://luau.org/news/2020-11-19-luau-type-checking-release/>; <https://research.luau-lang.org/hatra23/hatra23.pdf> (Brown, Friesen,
  Jeffrey, "Goals of the Luau Type System, Two Years On"); <https://devforum.roblox.com/t/general-release-luau%E2%80%99s-new-type-solver/4084991>
- <https://elixir-lang.org/blog/2026/06/03/elixir-v1-20-0-released/>
- <https://github.com/dart-community/migrate-to-null-safety/blob/main/docs/unsound.md>; <https://lukeplant.me.uk/blog/posts/why-im-leaving-elm/>
- <https://reforger.armaplatform.com/news/modding-update-scripting-1-1>
- <https://teal-language.org/>; <https://openmw.readthedocs.io/en/latest/reference/lua-scripting/teal.html>; <https://typescripttolua.github.io/docs/caveats>;
  <https://github.com/GlassBricks/typed-factorio>; <https://github.com/TypeScriptToLua/Dota2Declarations>; <https://github.com/cipherxof/w3ts>;
  <https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/static_typing.html>
- <https://dropbox.tech/frontend/the-great-coffeescript-to-typescript-migration-of-2017>
- <https://doc.rust-lang.org/nomicon/meet-safe-and-unsafe.html>; <https://doc.rust-lang.org/rustc/lints/levels.html>;
  <https://doc.rust-lang.org/edition-guide/editions/index.html>

### Studies

- Gao, Bird, Barr, ICSE 2017: <https://www.microsoft.com/en-us/research/wp-content/uploads/2017/09/gao2017javascript.pdf>;
  <https://earlbarr.com/publications/typestudy.pdf>;
  <https://blog.acolyer.org/2017/09/19/to-type-or-not-to-type-quantifying-detectable-bugs-in-javascript/>
- Khan et al., TSE 2022: <https://rebels.cs.uwaterloo.ca/papers/tse2021_khan.pdf>
- Di Grazia, Pradel, FSE 2022: <https://2022.esec-fse.org/details/fse-2022-research-papers/36/The-Evolution-of-Type-Annotations-in-Python-An-Empirical-Study>
- Bogner, Merkel, MSR 2022: <https://arxiv.org/abs/2203.11115>; Berger et al., TOPLAS 2019: <https://arxiv.org/abs/1901.10220>
- Takikawa et al., POPL 2016: <https://www2.ccs.neu.edu/racket/pubs/popl16-tfgnvf.pdf>
- Type-constrained decoding (PLDI 2025): <https://arxiv.org/abs/2504.09246>; MultiPL-E: <https://arxiv.org/pdf/2208.08227>; monitor-guided
  decoding: <https://arxiv.org/abs/2306.10763>; TypeChat: <https://microsoft.github.io/TypeChat/docs/introduction/>
- Tambon et al. (EMSE 30(3), 2025, doi 10.1007/s10664-025-10614-4): <https://arxiv.org/abs/2403.08937>; CloudAPIBench:
  <https://arxiv.org/abs/2407.09726>; feedback loops: <https://arxiv.org/abs/2508.14419>, <https://arxiv.org/abs/2508.00422>; agents
  and `any`: <https://arxiv.org/abs/2602.17955>

### This repository

- `AGENTS.md`; docs 08, 16, 19 (§4, §5), 21, 23 (§3, §5, §6, §9, §11–§14), 24 (F5, F7, F10, §5.2 L4 and L12, §5.3), 25 (§7.2), 30 (§1.1,
  §3.4, §4.5), 31 (N1, N4, N7, §4.5, §5.3–§5.4, §7, §8.2–§8.3, §9), 35 (§8, `data/corpus-script-idioms.csv`), 53 (DP-19), 55 (§2), 61
  (§4.6, §4.8, §4.10), 62 (§3.3, §4.4, §6.3, §6.9), 63 (§3.1, §4.2, §4.3)
- `docs/architecture/`: validation-and-lints (§1, §3, §6–§9, §11, §13), commands-undo-history (§4, §5), core-document-model (§8.1),
  game-integration (§5, §6), agent-runtime (§6); `docs/roadmap/integration-owners.md` (I35-PRIMER-FACTS)
- Decisions D003, D011, D012, D017, D026, D027, D030, D034, D047, D048, D049; DG001, DG005

## Verification notes

### 2026-09-28, author checks at write-up

- **Pins.** The local clones' `HEAD`s match the pins above for CWR, CWR-CE, DK26/CWR, HEMTT, armalint, ASL, TypeSqfEdit, sqf-analyzer,
  SQF-VM runtime and sqflint.
- **Re-read in code by the author at the pins:** `express.hpp#L44-L57`, `#L67`, `#L696-L700`; `express.cpp#L195-L219`, `#L257-L270`,
  `#L1110-L1117`, `#L1128-L1149`, `#L1316-L1356`, `#L1415-L1420`, `#L1955-L1963`, `#L2770-L2782`, `#L2826-L2837`; `GameStateExt.hpp#L12-L18`;
  `GameStateExt.cpp` rows at `#L886`, `#L897`, `#L979-L980`, `#L1197`, `#L1278-L1288`, `#L1294-L1299`; `GameStateExtGrp.cpp#L171-L191`;
  `ArcadeTemplate.cpp#L72-L93`; `UIArcade.cpp#L1101-L1125`; `Detector.cpp#L1258-L1264`; `WorldInit.cpp#L622-L625`; `AIArcade.cpp#L330-L333`;
  `AICenterImpl.cpp#L1636-L1640`; `Scripts.cpp#L240-L245`; the fork's `SKILL.md#L19-L24`, `#L56-L61` and `check.rs#L99-L101`, `#L284-L290`;
  HEMTT's `s13_undefined.rs` (default `help`, `check_orphan_code` off) and `libs/sqf/Cargo.toml` (`GPL-2.0`); armalint's README rows
  W101, W203, W220, W221, W229.
- **Registration grep by the author:** no `params`, `isNil`, `typeName`, `isEqualType`, `compile`, `compileScript`, `spawn`, `sleep`,
  `waitUntil`, `setVariable`, `getVariable` or `str` registration in either engine (the mock `EvalState.cpp` excluded); the same pattern
  finds `typeOf`, `isNull`, `format`, `call`, `setBehaviour`, `loadFile`, `preprocessFile` and `exec`, so the method works.
- **Web pages confirmed by the author:** `noEmitOnError` (definition, default `false`); the Luau general-release post (2025-11-20,
  non-strict on by default, definite runtime errors); the FSE 2022 abstract (9,655 projects, 0.704, 78.3%); the Elixir 1.20 post
  (2026-06-03; "verified bugs"; no annotations); the summary of Gao et al. (400 bugs, 60 each, mean 15%, 1.7 and 2.4 tokens); the abstract
  of arXiv 2602.17955 ("9x more prone to use the 'any' keyword"); HATRA 2023's two-contract sentence (from a text extract of the PDF).
- **Corrected or narrowed at write-up:** (1) Gao et al.'s annotation times differ between a research pass (mean 231 s and 307 s) and the
  summary read here (133 s and 262 s); neither is used. (2) The `GetEnumNames` count is 66 explicit definitions by the author's regex,
  against a research pass's 68; both are given. (3) The estimator found no dynamic official unit, while doc 35 counts one computed `exec`
  path; both are stated (§3.2). (4) Detector's `this` binding is cited only for trigger conditions; On Activation's binding follows doc
  31 §5.3 item 1. (5) A research pass proposed a new `defined(X)` intrinsic lowered to `X == X`; this doc instead types the existing
  idiom, so hand-written Strict code stays erasable (§4.2). (6) The auto-migration shares of §4.12 were measured with the `X == X` case
  modelled as a rewrite, not as a declaration; the effect on the shares is expected to be the same but is unmeasured.
- **Taken from research passes, not re-read by the author:** the 724-slot type scan; the `GetRelPos` and handler-body counts; locality
  call-site counts; the wiki data counts; Tambon, CloudAPIBench, MultiPL-E, monitor-guided decoding and the feedback-loop figures; Dart,
  Elm, Sorbet, Pyright, Dropbox, Hack, Teal, TypeScriptToLua, GDScript and the SQF-language repository facts; the Armitxes licence and
  antivirus event. They are marked by source class and should be re-read before any is used as a decision input.
- **[M-local] numbers** come from one estimator run over the owner's install (208 official folders, 52 mod mission folders, the mod's
  552-file library), reusing doc 35's tokenizer and executable name scan. Only the aggregate counts above left the machine; no corpus
  text is reproduced. The misspellings doc 35 already published are not repeated here.
- **Not done:** no Teller code; no model run; no Preview run; no probe of comment handling on 1.99; no legal review of the licence
  readings.
- **Folding steps, not done here:** a row for this doc in `docs/README.md`; the sibling-doc findings above; re-alignment of §6 with doc 64
  once it is published.
- **Hygiene:** public sources only; the owner's fork and crates are public; no private or unpublished project is named, and no local
  path, user name or key appears.

### 2026-09-28, review

Scope: citations re-opened, consistency with docs 23, 24, 30, 31, 61, 62 and 63 and with D011, D048 and D049, the "nothing decided"
and "opt-in, never a wall" rules, and hygiene. Doc 64 is still not in `docs/research/`, so §6 was not re-aligned.

- **Pins re-checked.** The `HEAD`s of the local clones of CWR, CWR-CE, DK26/CWR, HEMTT, armalint, ASL, TypeSqfEdit, sqf-analyzer,
  SQF-VM runtime and sqflint equal the full hashes in Sources.
- **Engine and tool lines re-opened by the reviewer [V]:** `express.hpp#L44-L57`, `#L67`, `#L698-L700`; `express.cpp#L162` (`{` is
  `OPEN_STRING`), `#L195-L219`, `#L257-L300`, `#L1108-L1150`, `#L1287-L1356`, `#L1412-L1422`, `#L1956-L1963`, `#L2773-L2782`,
  `#L2826-L2837`; `GameStateExt.hpp#L12-L18`; `GameStateExt.cpp#L886`, `#L897`, `#L933-L934`, `#L979-L980`, `#L1197`, `#L1279-L1299`
  and the registrations of `onPlayerConnected`, `buttonSetAction`, `onMapSingleClick`, `publicExec`, `setTriggerStatements` and
  `setWaypointStatements`; `GameStateExtGrp.cpp#L171-L191`, `#L885-L938`; `ArcadeTemplate.cpp#L73-L92`; `Scripts.cpp#L228-L330`
  (`;` lines break before any `_lines.Add`; the `~` buffer is 256 bytes); `UIArcade.cpp#L1101-L1125`; `Detector.cpp#L1259-L1263`,
  `#L1299-L1337`; `WorldInit.cpp#L622-L627`; `AIArcade.cpp#L331-L333`; `AICenterImpl.cpp#L1635-L1640`; the fork's `SKILL.md#L19-L24`,
  `#L56-L61` and `check.rs#L95-L103`, `#L280-L309`; HEMTT `s13_undefined.rs#L15-L57` and `libs/sqf/Cargo.toml`; armalint README rows
  W101, W203, W220, W221, W229 and its MIT `LICENSE`; ASL `README.md#L1-L50` and last commit (2018-09-03); TypeSqfEdit last commit
  (2020-11-27) and `Dependencies/TypeSqf.Analyzer.dll`; SQF-VM `src/sqc/ReadMe.md#L140-L165` and `src/sqc/sqc_parser.cpp#L824-L872`.
- **Registration grep repeated:** zero registration rows for `params`, `isNil`, `typeName`, `isEqualType`, `compile`, `compileScript`,
  `spawn`, `sleep`, `waitUntil`, `setVariable`, `getVariable` and `str` in either engine outside `EvalState.cpp`; `endGame` only in CWR
  and `triEndGame` only in CE; `typeOf`, `isNull`, `format`, `exec`, `loadFile` and `preprocessFile` found in both.
- **Counts reproduced [V]:** 66 `GetEnumNames` definitions (69 matching lines minus 3 declarations in `AIUnit.hpp`); 18 `IsLocal()`
  and 60 `GetNetworkManager()` call sites in the non-test command files (20 and 69 with the `*Test*` files). Both upgraded from
  "research pass" in §3.1 and §4.6.
- **Web and paper sources re-opened [V]:** `noEmitOnError` (definition, default `false`); TypeScript Design Goals ("fully erasable";
  soundness a non-goal); typescript-eslint `ban-ts-comment` (`allow-with-description`, minimum length 3, 10 in strict); Stripe's Sorbet
  post and sorbet.org metrics and static pages; HHVM 4.48, 4.62 and 4.135 posts and the HH_FIXME page; the HATRA 2023 PDF (two-contract
  sentences, from a text extract) and the Luau general-release post (2025-11-20); Elixir 1.20 post; the Reforger 1.1 post; TypeScriptToLua
  caveats; Godot static typing page (safe lines, `UNSAFE_*` warnings off by default); Teal home page; Pyright configuration
  (`reportUnnecessaryTypeIgnoreComment` "none" in every mode); Dropbox's Python post; the FSE 2022 abstract and Distinguished Paper
  award; Gao et al. full text (400, 59/58 then 60 each, [11.5%, 18.5%], tokens 1.7 and 2.4, the `strictNullChecks` 22 bugs, StringError);
  Khan et al. full text (15% of corrective, 11% of all, the three causes); Bogner and Merkel abstract; Takikawa et al. ("slowdowns of up
  to 105x" in one benchmark); Mündler et al. abstract; MultiPL-E full text (finding 5 and the `any` ablation); monitor-guided decoding
  abstract; Tambon et al. Table 2 and the EMSE 2025 record; CloudAPIBench abstract; arXiv 2508.14419 abstract; arXiv 2602.17955 abstract.
- **Corrected by the reviewer:**
  1. The fork's global-variable mask runs to `check.rs#L308`, so the citation is `#L284-L308`, not `#L284-L290`.
  2. `Vyhod` spans `express.cpp#L1558-L1864` and `VyhCast` `#L1290-L1468` (were `#L1575-L1864` and `#L1300-L1456`).
  3. The engine's own comment at `express.cpp#L1287-L1289` says shadowing a command is deliberate; §3.1 now says forbidding it is a
     Strict choice, a Warning elsewhere (rc61).
  4. On Activation's `this`: `DoActivate` and `OnActivate` (`Detector.cpp#L1299-L1337`) now cite the author's note (4); §3.3 no longer
     states "`this` is Bool" without the stale case.
  5. Gao et al.'s annotation times are resolved: 231.4 s and 306.8 s are means, 133 s and 262 s medians (Table II); neither is used.
  6. Bogner and Merkel: TypeScript's bug-fix ratio was higher, not merely "no lower"; Khan's causes quoted as published; MultiPL-E's
     reading narrowed (shown types help a little, −2.5% with `any`); the Mündler 94/6 split marked as doc 61's research-pass figure;
     Tambon's gate-catchable share given as about 30% (30.1%), not "a third"; doc 30's 8-of-16 marked as doc 30's inference.
  7. Hack did not end "strict only": 4.48 added an opt-in flag, 4.62 and 4.135 announced the removal of partial mode. Sorbet's Stripe
     figures completed (85% of non-test files at `strict`); its "no fixme comments" is kept as a research-pass reading, since no page
     read documents a suppression comment either way. Reforger 1.1's "no deprecation period" narrowed to "the post mentions none".
  8. ASL does read a `supportInfo` signature file (README L39-L50), so "no type checking in its README" became "no program type
     checking"; TypeSqf's "closed binary" names the file; SQC's `params` lowering is cited in code.
  9. `sleep` is registered on no profile, so §4.2 calls it an Arma 3 form rather than a profile-specific one.
  10. HEMTT's licence field is `GPL-2.0` (the deprecated SPDX id for GPL-2.0-only); the table says so instead of asserting `-only`.
  11. Doc 35 publishes 18 unresolved script references in official content (19 with the mod library) and 260 cheat references in
      75 official missions (271 with the mod library); both now say so. The hygiene note named a misspelling while saying it did not.
- **Consistency fixes:**
  1. **Doc 24 §5.3 rule 2** denies AI-proposed `dynamic-code` with a computed string; §4.4 item 6 had Wilco suggest such text for a raw
     block. It now has Wilco explain and leave the dynamic part to the user; changing that is left to SG12 and doc 24.
  2. **Doc 24 F10 and L4**: §4.5 claimed raw blocks are the only uncertifiable code; non-literal numeric config values evaluated at
     load (F10, L12) and L4 marks in non-Strict regions are now counted.
  3. **Doc 24 F7's sinks** `publicExec`, `onPlayerConnected` and `setWaypointStatements`, and `exitWith`, were missing from §4.6's
     `Code<Ctx>` list; all are registered in CWR (checked above).
  4. **Doc 63 §3.1**: FR0 is TS0, not TS1, and FR8 had no row; both added to §5.3.
  5. **Doc 61 §4.8 and doc 62 §6.9** state the decode-constraint completeness rule against parity and against what the engine can run;
     §5.4 had silently restated it against "the checker". The tension is now stated and reported for the sibling docs.
  6. **Naming**: "strict admission of model output" (agent-runtime §6; doc 61 §4.6) and the `Advisory` severity collide with this
     doc's Strict dialect and Advisory level; added to the header, SG4, §5.5 and the sibling findings.
  7. **Doc 23 §13.1** recommends porting the fork; §1.2 said "already decided".
- **Decided-status and D011 fixes:** TL;DR bullets that read as decisions now say "proposed"; §4.4 separates the owner's three options
  for contract errors in user regions, including (c), which blocks nothing beyond today's floor and needs no amendment of D011 item 3
  or validation-and-lints §3; §4.3 states that a user's own edit is never refused for a contract error; "forbid raw" is user-set per
  project and, for a registry, applies only to submission; §4.10 and open question 1 tie any Strict-by-default for user files to
  option (c); ST-23 (`only_user_intent_raises_a_user_region_to_strict`) was added so opt-in is tested, and the counts in the header and
  TL;DR were updated.
- **Checked and consistent, no change:** doc 23 §5 (SQS reads raw, `;` comments, `//` not a comment in SQS) against §4.8's declaration
  forms; doc 23 §13.3 items 2 and 4 against the sibling findings; doc 31 §7.1, §7.3, §8.2, §8.3 and §9 against §3.1, §4.2, §4.12 and
  §5.3; doc 30 §4.5 against §5.4; doc 62's governing principle names this doc; D048 item 2 and doc 55 §2.3 against §5.4;
  core-document-model §8.1's `Origin` and `Source::Deterministic` against §4.4; commands-undo-history §4.2's "Script-risk policy"
  family and `CoreBuilder`, and game-integration §5's `stage(&Snapshot, …)` and §6's P1 launch, as cited; D049's friction review is
  present (§8).
- **Hygiene:** no local path, user name, key or private project name in the file (searched for drive letters, user folders and known
  private names); game and expansion names appear only nominatively.
- **Not re-read:** the 724-slot type scan; the wiki data counts; the Dart and Elm readings; the second feedback-loop paper
  (arXiv 2508.00422); CloudAPIBench's body; every [M-local] number (owner-local, not reproducible here).

### 2026-09-28, SG1 decided

- SG1 (what a contract error in a user's Strict region does) is decided in D052 under the owner's delegation: option (b), with a one-run "Preview once without strict checks" exception at Preview and a visible, recorded "Downgrade this region to Advisory" at export; model and tool output get no exception.
