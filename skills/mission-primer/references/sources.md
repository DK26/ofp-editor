# Sources for the mission primer

Each fact in `SKILL.md` (P-ids, in reading order) and `file-skeletons.md` (R-ids) maps to its evidence and to the kind of check that pins it. For maintainers and tests; agents do not need this file.

**Aliases.**

| Alias | Expands to |
| --- | --- |
| `CWR:` | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/` |
| `EVAL:` | `BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/` |
| `CE:` | `ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/` |
| `doc NN` | `docs/research/NN-*.md` in this repository |

**Coverage.** Engine facts are read from the CWR 3.05 source. A `CE:` citation means CE was checked too. No fact's behaviour is verified against the 1.99 executable; P4.2 and P4.4 also rest on doc 35 §8.2's string scan of it and on the observed 1.99-era content (doc 35 §8.1), which show name presence or absence, not registration or semantics [V strings; I availability]. "Negative grep" means a case-insensitive search for the quoted registration name over `engine/` in both clones; it found no game-table registration.

**Pinned by.**

| Value | How the fact is pinned |
| --- | --- |
| `catalog` | Asserted against the generated per-profile command catalog |
| `const` | Compared with a value or token table the generator extracts from the pinned source |
| `vector` | An engine-parity checker test vector |
| `probe` | An in-game probe mission run through Preview |
| `review` | Human review whenever a cited line range changes |

| Id | Fact | Evidence | Pinned by |
| --- | --- | --- | --- |
| P1.1 | Facts come from tools; an empty result is an answer | doc 21 §1.1, §10.2; doc 14 §4.4 | review |
| P1.2 | Typed actions; code computes options and writes files; `none_fit` and `ask` escapes | doc 21 §3.2, §5.2; doc 25 §6.2 | review |
| P1.3 | Check scripts per field context; one finding per repair; `requires` | doc 23 §6, §13.3–§13.4; doc 21 §6.2 | review |
| P1.4 | Mission text is data | `AGENTS.md` (untrusted content); doc 21 §9.1 | review |
| P1.5 | `next_step()`; Preview is only offered | doc 21 §1.3, §11.1 | review |
| P2.1 | Folder `<name>.<island>` and its files | `CWR:UI/Map/UIArcadeWaypoint.cpp#L870-L897`; `CWR:UI/OptionsUI.cpp#L855-L879`; `CWR:UI/DisplayUI.cpp#L121-L145`; doc 04 §1 | review |
| P2.2 | `version=11;`, then `Mission`, `Intro`, `OutroWin`, `OutroLoose` | `CWR:UI/Map/UIMapExtDisplay.cpp#L99-L133`; `CWR:Core/SaveVersion.hpp#L9`; `CWR:IO/Serialization/ParamArchive.cpp#L625-L634`; `CE:Core/SaveVersion.hpp#L9` | const |
| P2.3 | A section holds Intel, Groups, Vehicles (empty), Markers, Sensors (triggers) | `CWR:AI/ArcadeTemplate.cpp#L1934-L1992` | const |
| P2.4 | Side tokens | `CWR:AI/ArcadeTemplate.cpp#L38-L211`; `CWR:World/Scene/Object.cpp#L53-L62` | const |
| P2.5 | 12 crew seats; one per driver, gunner and commander seat | `CWR:AI/Path/AITypes.hpp#L31`; `CWR:AI/ArcadeTemplate.cpp#L1790-L1832`; `CWR:AI/EntityAIType.hpp#L622-L624`; `CE:AI/Path/AITypes.hpp#L31` | const |
| P2.6 | Auto-join to the nearest same-side leader within 100 m (horizontal, inclusive), else a new group; limit checked after insert | `CWR:AI/ArcadeTemplateFind.cpp#L412-L470`; `CWR:UI/Map/UIMapExtDisplay.cpp#L410-L420`, `#L2057-L2073`; `CE:AI/ArcadeTemplateFind.cpp#L430` | const, probe |
| P2.7 | Per-side group cap; single player needs a player unit | `CWR:AI/ArcadeTemplate.cpp#L1835-L1857`; `CWR:Core/Config/Configuration.cpp#L339-L348` | review |
| P2.8 | Waypoint types, condition, on-activation | `CWR:AI/ArcadeTemplate.cpp#L1092-L1149`; `CWR:UI/Map/UIArcadeWaypoint.cpp#L78-L100` | const |
| P2.9 | Trigger fields, radio `ALPHA`–`JULIET`, types | `CWR:AI/ArcadeTemplate.cpp#L159-L168`, `#L191-L203`, `#L510-L562` | const |
| P2.10 | Sync holds a group at its waypoint | `CWR:AI/AIArcade.cpp#L309-L369`, `#L811-L827`; `CWR:AI/AICenterImpl.cpp#L748-L804`; `CWR:World/Detection/Detector.cpp#L1384-L1390` (read, not run) | probe |
| P2.11 | Load and save may renumber IDs: `Compact` closes gaps in unit IDs; invalid syncs are dropped | `CWR:AI/ArcadeTemplate.cpp#L1939-L1944`, `#L1983-L1990` (called on save and load); `CWR:AI/ArcadeTemplateFind.cpp#L882-L1045` (`Compact`); `CWR:AI/ArcadeTemplate.cpp#L1582-L1752` (`CheckSynchro`) | review |
| P3.1 | Nular, unary and binary forms; the examples' operand types | `CWR:Game/Commands/GameStateExt.cpp#L935`, `#L1241`, `#L1321`; `EVAL:express.cpp#L1132` | catalog |
| P3.2 | Unary > binary > comparison > `&&`/`\|\|` (`^` alone binds tighter than unary) | `EVAL:express.hpp#L503-L516`; `EVAL:express.cpp#L1847-L1859` | vector |
| P3.3 | `exec`; arguments in `_this` | `CWR:Game/Commands/GameStateExt.cpp#L1322`; `CWR:Game/Scripting/Scripts.cpp#L436` | catalog |
| P3.4 | SQS line classes: comment, label, statements | `CWR:Game/Scripting/Scripts.cpp#L97-L123`, `#L228-L244`, `#L319-L331` | vector |
| P3.5 | `~`, `@`, `&` waits | `CWR:Game/Scripting/Scripts.cpp#L253-L291`, `#L412-L488`; `CE:Game/Scripting/Scripts.cpp#L263` | vector |
| P3.6 | `?` splits at the first `:` | `CWR:Game/Scripting/Scripts.cpp#L292-L318`; `CE:Game/Scripting/Scripts.cpp#L292` | vector |
| P3.7 | `exit` ends the script | `CWR:Game/Commands/GameStateExt.cpp#L882`; `CWR:Game/Scripting/Scripts.cpp#L566-L569`, `#L585-L593` | catalog |
| P3.8 | SQS is not preprocessed; `//` errors; `#define` is a label; mid-line `;` separates statements | `CWR:Game/Scripting/Scripts.cpp#L148`, `#L165-L172`; `EVAL:express.cpp#L1610-L1651`, `#L2918-L2986` | vector |
| P3.9 | `comment` is a no-op | `EVAL:express.cpp#L1189` | catalog |
| P3.10 | 4096-byte line buffer, silent truncation | `CWR:Game/Scripting/Scripts.cpp#L97-L122` | const |
| P3.11 | SQF only as strings; `{…}` is a string; `call`; `preprocessFile` runs a C-style preprocessor (comments, `#define`, `#include`), `loadFile` returns the file raw | `EVAL:express.cpp#L257-L309`, `#L1149`, `#L1188`; `CWR:Game/Commands/GameStateExt.cpp#L1159-L1160`; `CWR:Game/Commands/GameStateExtWorldConfig.cpp#L1050-L1091`; `CWR:IO/PreprocC/Preproc.cpp#L26-L27`, `#L379-L386` | catalog |
| P3.12 | No scheduler | Negative grep: `spawn`, `execVM`, `sleep`, `uiSleep`, `waitUntil`; doc 14 §2 | catalog |
| P3.13 | `init.sqf` runs only on CWR and CE, executed raw (no preprocessor) after `init.sqs` is started | `CWR:UI/DisplayUI.cpp#L121-L145`; `CE:UI/DisplayUI.cpp#L131-L132` (1.99 absence inferred) | review |
| P3.14 | Field check modes; top-level comma | `CWR:UI/Map/UIArcade.cpp#L1103-L1125`, `#L1714-L1750`; `CWR:UI/Map/UIArcadeWaypoint.cpp#L331`, `#L343`; `EVAL:express.cpp#L2715-L2724`, `#L2773-L2782`, `#L2958-L2977`; doc 23 §6 | vector |
| P3.15 | `this` and `thisList` in trigger conditions; activation `None` | `CWR:World/Detection/Detector.cpp#L839-L923`, `#L1259-L1265`, `#L1331-L1337`; `CE:World/Detection/Detector.cpp#L1259` | probe |
| P3.16 | Wiped-out condition parses and works | `EVAL:express.cpp#L1019-L1043`, `#L1132`; `CWR:Game/Commands/GameStateExt.cpp#L935`, `#L979-L980`; `CWR:Game/Commands/GameStateExtUi.cpp#L802-L823` | vector |
| P3.17 | In a unit init, `this` is the unit | `CWR:World/WorldInit.cpp#L622-L627` | review |
| P4.1 | Commands absent from this engine | Negative grep of every listed name; `str`, `diag_log`, `setVariable`, `getVariable` only in the mock host `EVAL:EvalState.cpp#L194`, `#L198`, `#L691-L692`; `setRank` doc 19 F13; doc 23 §3.2 | catalog |
| P4.2 | Absent from 1.99: `for`, `exitWith`, `remoteExec`, `parseSimpleArray`, `createGroup`, `createTrigger`, `addWaypoint` (registered in CWR, missing from the 1.99 executable's strings: tier T4). Still unconfirmed for 1.99: the `private _x = …` form and `boolEq` | CWR registration: `EVAL:express.cpp#L1139`, `#L1191`, `#L1195`, `#L2664-L2699`; `CWR:Game/Commands/GameStateExt.cpp#L1228`, `#L1287`. 1.99 absence: doc 35 §8.2 (string scan, all seven in the absent list), §8.3 (T4), rc13; wiki tags per doc 23 §4 agree | catalog (T4 tier, doc 35 rc90) |
| P4.3 | `exitWith` does not end an SQS script | `EVAL:express.cpp#L877-L898`, `#L2988-L2991`; `CWR:Game/Scripting/Scripts.cpp#L454-L470` | vector |
| P4.4 | `setDammage`, `getDammage`, `allowDammage` take a double m; 1.99 has the single-m `setDamage` and `damage` (same handlers) but not `allowDamage` or `getDamage` | `CWR:Game/Commands/GameStateExt.cpp#L945-L947`, `#L1241-L1242`; `CE:Game/Commands/GameStateExt.cpp#L944`, `#L1239-L1240`; doc 35 §8.1 (`setDamage` and `damage` used in Resistance-era content, sharing the double-m handlers; `allowDammage` used in official content, per `docs/research/data/cwa199-observed-commands.csv`), §8.2 (`allowDamage` and `getDamage` absent from the 1.99 executable), §10, rc10; wiki tags (doc 23 §4) | catalog |
| P4.5 | Tokens `azimut`, `LIEUTNANT`, `OutroLoose`, `LOOSE` | `CWR:AI/ArcadeTemplate.cpp#L191-L203`, `#L354-L410`; `CWR:AI/AICenter.cpp#L146-L181`; `CWR:UI/Map/UIMapExtDisplay.cpp#L99-L133` | const |
| P4.6 | No Boolean `==`; string `==` ignores case; identifiers ignore case; `distance` Object × Object; a wrong enum string (for example `"CARELSS"`) is a silent no-op | `EVAL:express.cpp#L435-L438`, `#L1113`, `#L1116`; `CWR:Game/Commands/GameStateExt.cpp#L1235`, `#L1279-L1288`; identifiers: doc 23 §2.2 (the checker's lexer), doc 35 §8.4 (an unset `EndGame` reaches `endGame`); enums: `CWR:Game/Commands/GameStateExtGrp.cpp#L171-L261` via doc 35 §8.4, rc10 | catalog; vector (identifiers); probe (enums) |
| P4.7 | No `isNil`; an unset global reads as nil. Never name a global after a command of any profile: the evaluator reads a set variable before a nular of the same name, so an unset one runs the command (editor policy, doc 35 rc61) | Negative grep `isnil`; `EVAL:express.cpp#L72-L76`, `#L1210`, `#L2406-L2440`; `EVAL:express.cpp#L195-L208` via doc 35 §8.4, rc10 | catalog; review (naming) |
| P4.8 | Editor policy, not engine absence: never use `tri*` verbs (they exist, most gated to test and harness runs), `endGame` (registered on CWR, closes the application; CE gated it as `triEndGame`), or paths with `..` or a leading `\` (the engine does not confine them) | doc 24 TL;DR, §5.2 L1; `CWR:Game/Commands/GameStateExt.cpp#L886`; `CWR:Game/Commands/GameStateExtWorld.cpp#L787-L803`; `CWR:Game/Scripting/Scripts.cpp#L126-L150`; `CWR:UI/OptionsUI.cpp#L630-L655` | review |
| P5.1 | `objStatus` adds `OBJ_`; the four statuses | `CWR:Game/Commands/GameStateExt.cpp#L1321`; `CWR:Game/Commands/GameStateExtUi.cpp#L1825-L1861`; `CWR:UI/Map/UIMapDisplay.cpp#L268-L275`; `CE:Game/Commands/GameStateExtUi.cpp#L1827` | catalog, probe |
| P5.2 | `debriefing = 0;` skips the debriefing. The value is read as `GetInt() != 0`; a non-numeric word falls back to script evaluation, so on CWR and CE `false` also reads as 0 (source reading, not probed; 1.99 unknown). The primer still says `0` because it is portable | `CWR:UI/OptionsUI.cpp#L855-L879`; `CWR:UI/OptionsUIApp.cpp#L970-L983`; `CWR:UI/Map/UIMapExtDisplay.cpp#L2034-L2056`; `CWR:IO/ParamFile/ParamFile.cpp#L492`, `#L837-L860`, `#L1818-L1843`; `CWR:IO/ParamFile/ParamFileEval.cpp#L107-L113`; `EVAL:express.hpp#L223`, `#L390`; `CE:UI/OptionsUIApp.cpp#L973`; `CE:IO/ParamFile/ParamFile.cpp#L859` | probe |
| P5.3 | END/LOOSE types; every `END<n>` must be active; `LOOSE` is immediate. `END1`–`END6` are six distinct endings that also carry failures; `LOOSE` debriefs from a `Debriefing:Loser` section; campaigns conventionally route `lost` to a retry (corpus practice, not an engine rule) | `CWR:AI/AICenter.hpp#L151-L154`; `CWR:AI/ArcadeTemplate.cpp#L191-L203`; `CWR:World/WorldImpl.cpp#L541-L656`; `Debriefing:Loser` lookup `CWR:UI/Map/UIMapDialogs.cpp#L1064-L1087` via doc 35 §4; usage: doc 35 TL;DR, §3.1, §4, §10, rc09 | probe; review (usage) |
| P5.4 | Only triggers choose an ending; `forceEnd` only lets an ending that is already set proceed without waiting for camera and title effects. Exception outside normal missions: the gated test verb `triEndMission` forces an ending (covered by the P4.8 ban) | `CWR:Game/Commands/GameStateExt.cpp#L885`; `CWR:Game/Commands/GameStateExtWorld.cpp#L781-L785`; `CWR:World/World.hpp#L444-L445`; `CWR:UI/DisplayUIMenus.cpp#L984-L1007`; `CWR:World/WorldImpl.cpp#L541-L656` (the only ungated writer of the end mode); `CWR:Game/Commands/GameStateExtTestAudio.cpp#L2075-L2092`, `#L3039`; negative grep `endMission`, `failMission` | catalog |
| P5.5 | Player death is not routable | `CWR:UI/DisplayUIMenus.cpp#L966-L981`; `CWR:World/WorldImpl.cpp#L541-L656` | probe |
| P5.6 | Campaign keys `end1`–`end6`, `lost`; chapter fallback | `CWR:UI/OptionsUI.cpp#L1894-L2022`; `CE:UI/OptionsUI.cpp#L1934`; doc 18 §4 | probe |
| P5.7 | `saveVar` takes the name; stores at once; later missions get it; undefined stores nothing | `CWR:Game/Commands/GameStateExt.cpp#L1069`; `CWR:Game/Commands/GameStateExtGrp.cpp#L412-L425`; `CWR:AI/AICenterStats.cpp#L69-L80`; `CWR:UI/OptionsUIApp.cpp#L883-L895`; `CE:Game/Commands/GameStateExt.cpp#L1067` | probe |
| P5.8 | Which value types survive | `CWR:Game/Commands/GameStateExt.cpp#L77-L128`, `#L256-L267`; `EVAL:express.cpp#L1992-L2040`, `#L2096-L2112` (object loss inferred from reference serialisation) | probe |
| P5.9 | `cmp_` prefix, copy arrays, initialise in the first mission | doc 18 §6.1 gotchas 3–4 (`EVAL:express.cpp#L678-L708`); doc 19 §4 (practice, not engine fact) | review |
| R1 | `mission.sqm` order, version gates, text-only editor, all four sections required | `CWR:AI/ArcadeTemplate.cpp#L1934-L1992`; `CWR:UI/Map/UIMapExtDisplay.cpp#L99-L143`; `CWR:IO/Serialization/ParamArchive.cpp#L434-L447`, `#L583-L596` | const |
| R2 | `briefing.html` parser rules and section names | `CWR:UI/Controls/UIControlsExt.cpp#L163-L177`, `#L1392-L1419`, `#L1493-L1505`, `#L1649-L1747`; `CWR:UI/Map/UIMapDisplay.cpp#L609-L653`, `#L782-L840`; `CWR:UI/Map/UIMapDisplayBriefing.cpp#L311-L481`; `CWR:UI/Map/UIMapDialogs.cpp#L1062-L1091`; `CE:UI/Map/UIMapDialogs.cpp#L1070` | probe |
| R3 | Briefing file-name lookup order; UTF-8 names are Remastered additions; per-language `.html` names unconfirmed for 1.99 | `CWR:UI/OptionsUI.cpp#L202-L205`; `CWR:UI/Locale/MissionHtmlLocalization.cpp#L261-L284` (1.99 unknown) | review |
| R4 | `description.ext` scopes, debriefing flow and value reading, `template` and routing keys | As P5.2 and P5.6; `CWR:UI/OptionsUIApp.cpp#L1015-L1048`; `CWR:UI/OptionsUI.cpp#L1994` | probe |

## Verification notes

### Consolidation pass (2026-09-27)

- 2026-09-27: applied doc 35's primer corrections (§10 "Doc 31 and the primer", rc09, rc10) to `SKILL.md` and to rows P4.2, P4.4, P4.6, P4.7 and P5.3 above; the Coverage paragraph now names the 1.99 string-scan evidence. Each claim was checked against doc 35 §3.1, §4, §8.1–§8.4 and `cwa199-observed-commands.csv` before editing.
  - §4: the Remastered-only list now says "absent from 1.99" for `for`, `exitWith`, `remoteExec`, `parseSimpleArray`, `createGroup`, `createTrigger` and `addWaypoint` (T4); `private _x = …` and `boolEq` stay unconfirmed because doc 35 gives no 1.99 evidence for them. The superseded claim "single-m aliases are unconfirmed for 1.99" is replaced: `setDamage` and `damage` exist on 1.99, while `allowDamage` and `getDamage` are absent (`getDamage` added from doc 35 §8.2's absent list). rc10's other traps are added: wrong enum strings fail silently, identifiers ignore case, and no global may share a command's name in any profile.
  - §5: "`END1`–`END6` (wins) and `LOOSE` (loss)" is superseded by six distinct endings that also carry failures, with `LOOSE` as the loss ending (debrief `Debriefing:Loser`) that campaigns conventionally use for retry. The dependent line "route failure through `LOOSE` while the player lives" now reads "end a failure while the player lives".
  - Budget: `SKILL.md` stays at 1,200 words (whitespace tokens, frontmatter included; doc 30 §5.2 test 6). To make room, wording was tightened without dropping facts: the opening line, the description's release-name parenthetical, `for … from … to … do` shortened to `for`, and small phrasing cuts in §1–§3 and §5. Its own consolidation note is one line; details live here.
  - Renames: `SKILL.md` and this file had no references to the concept manual (now Standing Orders), the live tutorials (now Drill), doc 33's file or the concept manual's skill folder, so nothing was renamed.
