# Campaign System in the Poseidon Engine: Mechanics, Limits, and Patterns for Branching RPG Campaigns

Research doc 18 for `ofp-editor`. Audience: contributors and LLM coding agents. This file is meant to be read on its own.
Question answered: how do campaigns actually work in the CWA / OFP engine (Poseidon, as released in BohemiaInteractive/CWR), what can
persist between missions, what are the hard limits, and how can our editor express **arbitrary state-based transitions and mission trees**
while the output still runs on original CWA 1.99?

**Epistemic legend.** **[V]** = verified by reading source at the pinned commit (citation given). **[I]** = inferred from code or
docs but not run. **[U]** = unknown, needs a test. **[W]** = community or web documentation. Code citations use
`owner/repo@sha:path#Lx-Ly`. Pins: `BohemiaInteractive/CWR@ffc61838b7`, `ofpisnotdead-com/CWR-CE@b67bf3bd62`,
`iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9`. Unless a citation says otherwise, `CWR:` means `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/`.

## TL;DR

- **The transition model is a static lookup table.** A mission ends with one of 7 routable codes (`lost`, `end1`..`end6`). The engine then reads
  `Campaign/<chapter>/<mission>/<code>`. If that entry is empty, it falls back to `Campaign/<chapter>/<code>`, which names a *chapter* and always
  enters that chapter's `firstMission`. If that is empty too, the campaign ends. The campaign classes have no conditions or expressions **[V]**
  (`CWR:UI/OptionsUI.cpp#L1894-L2022`); CWR's config `__EVAL` cannot produce a usable target (§7) **[I]**.
- **Only triggers select the ending in 1.99-era script.** Trigger types `END1`..`END6` and `LOOSE` set the code. The engine has no `endMission`
  or `failMission` command. `forceEnd` only skips waiting for camera effects and *title-layer* effects (`titleText`/`titleRsc`/`titleObj`); in CWR
  `titleCut` is registered as an alias of `cutText` (cut layer), which never blocks the end. Every `END<n>` trigger of the same number must be active
  at once (AND). `LOOSE` wins over `END1`, which wins over `END2`, and so on **[V]** (`CWR:World/WorldImpl.cpp#L500-L665`,
  `CWR:UI/DisplayUIMenus.cpp#L984-L986`, `CWR:Game/Commands/GameStateExt.cpp#L1000-L1008`).
- **Player death cannot be routed.** A dead SP player produces `EMKilled`, which leads to the Retry/Load/Quit dialog, not a transition **[V]**.
  `exit.sqs` does not run on death either (§5) **[V]**. A mission file with no groups (a cutscene-only "mission") always takes the `lost`
  edge **[V]** (`CWR:UI/OptionsUIApp.cpp#L860-L875`).
- **`saveVar "name"` is the global campaign state.** It copies a *global* variable into an in-memory campaign table. That table is re-injected as
  globals at the start of every later mission (before unit inits and `init.sqs`) and in mission intros (there only *after* the intro's unit init
  lines, before `initintro.sqs`). Scalars, bools, strings, sides and nested arrays serialize well. Object and group
  values are saved as object-ID references and are unreliable across missions. You cannot save `nil`, so there is no "unsave" **[V]**.
  Arrays are stored **by reference** in memory: an in-place `set` on a saved (or re-injected) array silently changes the campaign table
  without `saveVar` **[V by reading, runtime U]** (§6.1 gotcha 4).
- **Reverting is built in for saveVar and the weapon pool, but not for `objects.sav`.** Each campaign-history row stores a snapshot of the
  saveVar table taken when that mission's gameplay starts (after its unit inits, `init.sqs` and briefing). "Restart from mission k" drops row k,
  restores that snapshot and re-copies the pool from row k−1, so both revert to their start-of-k state **[V]**.
  `saveStatus`/`saveIdentity` write one unversioned `objects.sav` per campaign. That file is never reverted, and it is not even cleared when a new
  campaign playthrough starts **[V]**.
- **Several code paths do not see campaign state [V].** Chapter cutscenes, outros and award cutscenes wipe globals without reloading campaign
  vars (and CWR's award selection never picks an award at all, §2 and §4). The debriefing "Restart" path re-inits the mission without
  re-injecting campaign vars, which looks like a bug. Put state-dependent cinematics in mission `Intro` sections or in router missions.
- **MP campaigns do not exist in this engine.** The dedicated server only runs a flat rotation list **[V]**.
- **CWR-CE does not change campaign logic at the pinned SHAs.** The campaign files are byte-identical or differ only in unrelated UI/download
  code **[V]**.
- **Recommendation:** the editor should own a rich campaign graph (typed global vars, per-mission vars, guarded transitions) and compile it to
  vanilla output:
  - in-mission decision scripts that set one of 7 "outcome sockets" (Pattern A);
  - zero-gameplay **router missions** for fan-out above 7, for cross-chapter jumps, and for state-dependent routing. Each router costs about one
    world re-init and adds one campaign-book row; the other screens can be suppressed (Pattern B);
  - one generated SQS glue layer from the data model, with transactional commits, copy-then-assign array updates and versioned
    `objects.sav` keys (Pattern C).
  
  Treat any CWR-CE engine patch as optional progressive enhancement. The two worth upstreaming are small robustness fixes: re-inject vars on
  debriefing restart, and reset `objects.sav` on a new campaign.

## 1. On-disk layout and where state lives

| What | Path (CWR build) | Evidence |
| --- | --- | --- |
| Campaign root | `Campaigns/<name>/` (a folder), or a bank `Campaigns/<name>.pbo` with prefix `campaigns\<name>`. Mod folders are also enumerated. Language PBOs `<name>.<lang>` are remapped onto the base prefix | **[V]** `CWR:UI/OptionsUIImpl.cpp#L1587-L1653`, `CWR:Core/GameState.cpp#L201-L215`, `#L277` |
| Campaign config | `<root>/description.ext`, parsed into `ExtParsCampaign` whenever the base directory is set | **[V]** `CWR:UI/OptionsUI.cpp#L777-L794` |
| Campaign stringtable | `<root>/stringtable.csv` (loaded as the "Campaign" table) | **[V]** same |
| Campaign overview | `<root>/overview.html` (localized lookup) | **[V]** `CWR:UI/OptionsUIImpl.cpp#L483-L486`, `#L1134` |
| Missions | `<root>/missions/<mission>.<island>/` (mission.sqm, description.ext, briefing.html, overview.html, init.sqs, exit.sqs, ...). Named by the `template = "<mission>.<island>"` key | **[V]** `CWR:UI/OptionsUI.cpp#L148-L159`, `#L849-L853`; `CWR:UI/Map/UIArcadeWaypoint.cpp#L870-L902` |
| Shared scripts | `exec` lookup order: mission dir, then `<root>/scripts\`, then global `scripts\` | **[V]** `CWR:UI/OptionsUI.cpp#L630-L655` |
| Shared resources | `CfgIdentities`, `CfgSounds`, `CfgMusic`, `CfgRadio`, `CfgSFX`, `CfgEnvSounds`, `CfgCameraEffects`, `RscTitles`, dialogs: the mission's description.ext is searched first, then the campaign's | **[V]** `CWR:Game/Commands/GameStateExtUi.cpp#L184-L198`, `CWR:Game/Commands/GameStateExtWorldDialog.cpp#L24-L49`, `CWR:UI/OptionsUI.cpp#L310-L756` |
| Campaign progress ("book") | `<UserDir>/Saved/Tmp/<campaign>.sqc` (ParamArchive, `CampaignVersion = 3`) | **[V]** `CWR:UI/OptionsUIImpl.cpp#L1589-L1611`, `CWR:Core/SaveVersion.hpp#L14-L15` |
| Savegames | `<UserDir>/Saved/campaigns/<campaign>/{save,autosave,continue}.fps`, `weapons.cfg`. There is **one** save slot per campaign | **[V]** `CWR:UI/OptionsUI.cpp#L230-L258` |
| Unit/identity store | `<UserDir>/Saved/campaigns/<campaign>/objects.sav` | **[V]** `CWR:Game/Commands/GameStateExtWorld.cpp#L837` |

Whether the original 1.99 binary uses the same user paths is **[U]**. It does not matter to the editor, which only writes content.

## 2. `description.ext`: the keys the engine actually reads

The engine reads the keys below. Anything else is ignored, which is why extra keys are safe for forward compatibility **[I]**.

| Level | Key | Semantics as implemented | Evidence |
| --- | --- | --- | --- |
| root | `weaponPool` | Boolean at the **top level** (not inside `class Campaign`). It gates only briefing gear selection from the pool, `fillWeaponsFromPool`, and saving the leftover pool after gear selection. The pool itself is carried forward regardless | **[V]** `CWR:UI/Map/UIMapDisplay.cpp#L468-L477`, `#L532-L536`, `#L1132-L1144` |
| root | `exitScore` | If present and the campaign score is `<= exitScore` when a mission ends, the campaign ends. Skipped for missions with `noAward` | **[V]** `CWR:UI/OptionsUI.cpp#L1905-L1923` |
| root | `class Awards` / `class Penalties` | Children have `limit` plus one cutscene per island (`<worldname> = "<mission>.<island>"`). When the score falls, the unplayed qualifying penalty with the lowest `limit` plays. When it rises, every qualifying award is marked played but, as coded, **none is selected** (`best` starts at `INT_MAX` and the test is `limit > best`), so no award cutscene plays in CWR. Played ones are remembered | **[V by reading]** `CWR:UI/OptionsUI.cpp#L1756-L1892` (award loop `#L1843-L1888`); doc 35 §3.4 reads the same bug, so 1985's authored awards never play in CWR. Runtime and 1.99 parity **[U]** |
| `Campaign` | `name` | Title in the campaign menu | **[V]** `CWR:UI/OptionsUIImpl.cpp#L1041` |
| `Campaign` | `firstBattle` | Chapter class to start in. If it is empty, the campaign silently does not start | **[V]** `CWR:UI/OptionsUIApp.cpp#L350-L384` |
| chapter | `firstMission` | The **only** entry point of a chapter. It is used at campaign start and on every chapter transition | **[V]** `CWR:UI/OptionsUI.cpp#L1985`, `CWR:UI/OptionsUIApp.cpp#L559-L566` |
| chapter | `cutscene` | `"<mission>.<island>"` intro played when the chapter is entered (`RscDisplayCampaign`). It runs `initintro.sqs` and does **not** load campaign vars | **[V]** `CWR:UI/OptionsUI.cpp#L1728-L1732`, `CWR:UI/DisplayUIMenus.cpp#L1409-L1450` |
| chapter | `end1`..`end6`, `lost` | **Chapter** names used as the fallback when the mission-level key is empty. Empty here means the campaign ends | **[V]** `CWR:UI/OptionsUI.cpp#L1950-L1986` |
| mission | `template` | Mission folder `"<mission>.<island>"`. If it is invalid or has no mission.sqm, the engine shows the error "Error in campaign structure" and the campaign aborts | **[V]** `CWR:UI/OptionsUI.cpp#L1988-L2009` |
| mission | `end1`..`end6`, `lost` | Mission-class names **in the same chapter**. Empty means use the chapter fallback | **[V]** `CWR:UI/OptionsUI.cpp#L1925-L1948` |
| mission | `lives` | Read with no default. `-1` = unlimited retries. `>0` = a retry budget. `0` = no retry, and it also blocks the debriefing restart | **[V]** `CWR:UI/OptionsUIApp.cpp#L881`, `CWR:UI/DisplayUIMenus.cpp#L1037-L1053`, `CWR:UI/Map/UIMapDialogs.cpp#L673-L676` |
| mission | `noAward` | Disables `exitScore` and the award/penalty cutscenes after this mission | **[V]** `CWR:UI/OptionsUI.cpp#L1776`, `#L1905` |
| mission's own description.ext | `debriefing` | If it is present and false, the debriefing screen is skipped (stats are still updated) | **[V]** `CWR:UI/OptionsUIApp.cpp#L972-L983`. It is listed as an OFP parameter by PMC **[W]**. Presence in 1.99 is **[I]** and needs a test |
| mission's own description.ext | `minScore`, `avgScore`, `maxScore` | Converts the player's experience delta into campaign score points (-3..+4) | **[V]** `CWR:AI/AICenterStats.cpp#L94-L113` |

**Not read by this engine [V]** (checked by grep):
- `endDefault`, which is Arma 3+ **[W]**;
- `MissionDefault` and `NoEndings`, which are only config-inheritance conventions;
- a mission-level `cutscene`;
- `showHUD` in the campaign class (the code is commented out, `CWR:UI/OptionsUI.cpp#L1737-L1749`);
- `disableMP`, `enableHub`, `repeat`, `isHub` (Arma 2/3 **[W]**).

**Missing keys.** In CWR, `cls >> "key"` on a missing entry logs a debug line and returns an error entry (`CWR:IO/ParamFile/ParamFile.cpp#L1309-L1318`). Original
1.99 behavior (it may show an error box) is **[U]**. The generator should therefore emit **every** key for every class (`lives`, `noAward`,
all 7 end codes) and should not depend on inheritance across chapter scopes.

Illustrative vanilla-safe output (flattened, with every key explicit):

```cpp
weaponPool = 1;
class Campaign {
  name = "Operation Tannenberg";
  firstBattle = "Act1";
  class Act1 {
    name = "Act 1"; firstMission = "M01"; cutscene = "";
    end1 = ""; end2 = ""; end3 = ""; end4 = ""; end5 = ""; end6 = ""; lost = "";
    class M01 { template = "M01_Ambush.Eden"; lives = -1; noAward = 1;
      end1 = "R01"; end2 = "M02b"; end3 = ""; end4 = ""; end5 = ""; end6 = ""; lost = "M01x"; };
    class R01 { template = "Router.Eden";      lives = -1; noAward = 1;
      end1 = "M02a"; end2 = "M02b"; end3 = "M02c"; end4 = ""; end5 = ""; end6 = ""; lost = ""; };
  };
};
```

## 3. Runtime flow of one campaign step

State machine of `DisplayMain::OnChildDestroyed` in `CWR:UI/OptionsUIApp.cpp`:

```
StartCampaign ─► chapter cutscene (DisplayCampaignIntro) ─► IDD_CAMPAIGN ─► firstMission
NextMission ── same chapter ─► StartMission(newBattle=false)
            └─ chapter change ─► chapter cutscene ─► IDD_CAMPAIGN ─► firstMission
StartMission ─► DisplayIntro(mission Intro; loads campaign vars; initintro.sqs)
  ─► IDD_INTRO: ParseMission ── no groups ─► AddMission; _end=LOST ─► Outro ─► ...
                              └─ groups ─► SwitchLandscape; load campaign vars; InitVehicles (unit inits, init.sqs)
                                  ─► briefing.html? DisplayGetReady : DisplayMission (AddMission → history row + snapshot)
  ─► mission runs ─► end mode set (triggers) ─► exit.sqs(_this = code) ─► IDD_MISSION
     (player killed: EMKilled ─► onPlayerKilled.sqs? ─► RscDisplayMissionEnd; no exit.sqs, no transition, §5)
  ─► debriefing (unless description.ext debriefing=0) ─► Outro (OutroWin / OutroLoose)
  ─► IDD_OUTRO: CheckAward (unless noAward; in CWR only penalties are ever selected, §2) ─► NextMission(code)
```

| Step | Code |
| --- | --- |
| New campaign: clear stats and history, save `.sqc`, then play the `firstBattle` chapter cutscene | **[V]** `CWR:UI/OptionsUIApp.cpp#L350-L384` |
| Mission intro, cutscene-only missions, var injection, save deletion, briefing | **[V]** `CWR:UI/OptionsUIApp.cpp#L850-L943` |
| History row plus stats snapshot created when gameplay starts (`AddMission`, in the `DisplayMission` constructor). This is *after* unit inits, `init.sqs` and the briefing, so `saveVar`s made there are already in the snapshot | **[V]** `CWR:UI/DisplayUIMenus.cpp#L812-L821`, `CWR:UI/OptionsUI.cpp#L1693-L1712`, `#L1104-L1136`, `CWR:UI/OptionsUIApp.cpp#L893-L941` |
| End detection and `exit.sqs` | **[V]** `CWR:UI/DisplayUIMenus.cpp#L966-L1007` |
| Debriefing, outro, award, next mission | **[V]** `CWR:UI/OptionsUIApp.cpp#L944-L1049` |
| Island reload only if the island differs, but `World::CleanUp` always runs and `GGameState.Reset()` wipes **all** globals | **[V]** `CWR:World/WorldImpl.cpp#L1141-L1158`, `CWR:World/WorldInit.cpp#L1107-L1111` (`CleanUp` → `CleanUpDeinit`), `#L1001-L1026`, `BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/express.cpp#L2399-L2404` |

## 4. How the next mission is chosen (exact algorithm)

`NextMission(disp, mode)` at `CWR:UI/OptionsUI.cpp#L1894-L2022` **[V]**:

```
MissionCompleted(current) ; save .sqc
if !noAward && exitScore defined && score <= exitScore: end campaign
key = {EMLoser:"lost", EMEnd1:"end1", ... EMEnd6:"end6"}[mode]     // EMKilled/EMContinue: no case
next = Campaign/<battle>/<mission>/<key>        // mission class in SAME chapter
if next == "":
    battle = Campaign/<battle>/<key>            // chapter-level fallback
    if battle == "": end campaign (back to main menu)
    next = Campaign/<battle>/firstMission ; play chapter cutscene first
resolve template; missing mission.sqm => "Error in campaign structure", abort
StartMission(...)
```

Consequences:
- **Out-degree is at most 7** per mission class. Each code has exactly one target: either a mission in the same chapter, or a chapter entered at
  its `firstMission`.
- Loops are allowed. A self-loop does not add a new history row, because `AddMission` skips a row whose name equals the last row
  (`CWR:UI/OptionsUI.cpp#L1122-L1127`) **[V]**.
- If `EMKilled` ever reaches `NextMission` (possible only when `lives = 0`), the `switch` has no case for it. The same mission is re-selected and is
  marked "completed" **[V by reading, runtime U]**.
- Several mission classes may share one `template`. The engine only reads the string **[I]**. Field evidence now backs this: community dynamic
  campaigns point three classes at one template and use the graph as a router **[V in community content]** (doc 35 §6.3, §10). One physical
  router folder can therefore serve many campaign nodes, each with its own end mapping.
- **Awards never fire in CWR.** `CheckAward` runs after the outro, but the award loop starts `best` at `INT_MAX` and tests `limit > best`, so it
  never selects an award; only penalties play (§2; doc 35 §3.4 reads the same code) **[V by reading; runtime and 1.99 U]**. Generated
  campaigns must not depend on award cutscenes.
- **Recommendation: use one engine chapter for the whole graph by default.** That makes any-to-any mission edges legal. Editor "acts" can then be
  cosmetic; map them to real chapters only where a chapter cutscene is wanted and the act is entered at its first mission.

## 5. Producing an ending

- The `EndMode` enum is `EMContinue, EMKilled, EMLoser, EMEnd1..EMEnd6` **[V]** (`CWR:AI/AICenter.hpp#L151-L154`).
- Trigger types in mission.sqm are `END1`..`END6` and `LOOSE`. There is also a legacy alias `WIN`, which maps to END1 **[V]** (`CWR:AI/ArcadeTemplate.cpp#L191-L203`,
  `CWR:AI/Path/ArcadeWaypoint.hpp#L242-L257`).
- Evaluation happens every world tick while the mode is `EMContinue`. In SP, a dead or absent player gives `EMKilled` first. Then any single
  active `LOOSE` trigger gives `EMLoser`. Otherwise `END<n>` fires only when **all** `END<n>` triggers are active, checked in order 1..6 **[V]**
  (`CWR:World/WorldImpl.cpp#L541-L657`). The same logic runs in intros (`GModeIntro`), where any ending simply stops the cutscene
  (`CWR:UI/DisplayUIMenus.cpp#L1202-L1206`).
- The mission closes once the mode is not Continue/Killed **and** (no camera effect and no title effect, **or** `forceEnd` was called) **[V]**
  (`CWR:UI/DisplayUIMenus.cpp#L984-L1006`). `forceEnd` only sets that flag (`CWR:Game/Commands/GameStateExtWorld.cpp#L781-L785`).
  Only the *title* layer (`titleText`, `titleRsc`, `titleObj`) and camera effects are checked. The *cut* layer (`cutText`, `cutRsc`, `cutObj`, and
  `titleCut`, which CWR maps to the same `CutText` handler that calls `SetCutEffect`) does not block the end **[V]**
  (`CWR:Game/Commands/GameStateExt.cpp#L1000-L1008`, `CWR:Game/Commands/GameStateExtUi.cpp#L1729-L1735`, `CWR:World/World.hpp#L428-L448`).
  Biki calls `titleCut` obsolete in favor of `cutText` **[W]**; the layer used by the 1.99 binary is **[U]**.
- `exit.sqs` in the mission folder runs at close with `_this` = code (0 = lost, 1..6 = endN). It gets a single `SimulateScripts()` call **[V]**
  (`CWR:UI/DisplayUIMenus.cpp#L987-L994`) with no line limit, so several straight-line statements do complete (doc 35 §3.3) **[V by reading;
  runtime U]**. So it should be straight-line code with no delays **[I]**. It does **not** run when the player is killed: the `EMKilled`
  branch (`CWR:UI/DisplayUIMenus.cpp#L966-L981`) opens the mission-end dialog instead (doc 35 §3.3) **[V]**.
- **There is no script command that picks an ending.** `endMission` and `failMission` are not registered (Biki lists `endMission` as an Arma 2-era
  command **[W]**). CWR's `endGame` (renamed `triEndGame`
  in CWR-CE) is an automation "quit app" command, not a campaign ending **[V]** (`CWR:Game/Commands/GameStateExtWorld.cpp#L787-L803`,
  `ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/Game/Commands/GameStateExtTestAudio.cpp#L2996`).
- **How a script picks an ending:** use condition-only triggers such as `cmpEnd == 3` with type `END3`, and `forceEnd` in On Activation.
- **Player death:** the game shows the `RscDisplayMissionEnd` screen (Retry/Load/Quit). If `scripts\onPlayerKilled.sqs` exists, it runs first and
  must call `enableEndDialog` **[V]** (`CWR:UI/DisplayUIMenus.cpp#L966-L981`, `CWR:World/Entities/Infantry/SoldierOldMove.cpp#L1068-L1086`).
  `exit.sqs` does not run. A "death branch" is impossible. To branch on failure, route it through a `LOOSE` trigger while the player is still
  alive (for example "squad wiped", or "objective failed"). Respawn is not a way out in SP: outside `GModeNetware` the respawn mode is hard-wired to `RespawnNone`
  **[V]** (`CWR:World/Entities/Infantry/SoldierOldMove.cpp#L1026-L1029`).

## 6. Persistence mechanisms

### 6.1 `saveVar` (global campaign state)

- **Implementation [V].** The name is lower-cased and looked up in the **global** variable table. If the variable is undefined, the call does
  nothing; assigning `nil` to a global deletes it (`BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/express.cpp#L2504-L2505`), so `nil` cannot be saved.
  Otherwise it is upserted into `GStats._campaign._variables` (`CWR:Game/Commands/GameStateExtGrp.cpp#L412-L425`,
  `CWR:AI/AICenterStats.cpp#L69-L80`).
- **Re-injection [V]** happens as globals:
  - at mission start, after `SwitchLandscape` and before unit inits and `init.sqs` (`CWR:UI/OptionsUIApp.cpp#L883-L895`,
    `CWR:World/WorldInit.cpp#L622-L632`);
  - in mission intros (`CWR:UI/DisplayUIMenus.cpp#L1310-L1320`). This runs in `DisplayIntro::Init()`, *after* `InitVehicles(GModeIntro)` has
    already executed the intro's unit init lines, so only `initintro.sqs` and later scripts/triggers see the vars
    (`CWR:UI/DisplayUIMenus.cpp#L1257-L1292`, `CWR:World/WorldInit.cpp#L622-L627`);
  - on in-mission Retry without an autosave (`CWR:UI/DisplayUIMenus.cpp#L1058-L1068`).
- **Where it is not re-injected [V]:**
  - chapter cutscenes (`CWR:UI/DisplayUIMenus.cpp#L1409-L1450`);
  - outros (`#L1331-L1374`);
  - award cutscenes (`#L1376-L1407`);
  - the **debriefing "Restart"** path (`CWR:UI/Map/UIMapDialogs.cpp#L665-L695`).

  Each of these runs `SwitchLandscape`, which wipes globals, so campaign vars are simply absent in them.
- **Storage [V].** The table is in memory while playing, inside savegames (`AIGlobalSerialize` → `Stats`, `CWR:AI/AICenterImpl.cpp#L843-L851`),
  and inside the `.sqc` as a **snapshot per history row** taken at `AddMission` (`CWR:UI/OptionsUI.cpp#L1132`, `#L1073-L1095`). It is scoped to
  the campaign. It is also loaded for single missions, but there `GStats.ClearAll()` has emptied it.

| Value type | Persists? | Why |
| --- | --- | --- |
| Number, Boolean, String | Yes | Value serializers **[V]** `BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/express.cpp#L1992-L2040` |
| Array (nested, mixed) | Yes, recursively | **[V]** `BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/express.cpp#L2096-L2101` |
| Side | Yes (as an enum) | **[V]** `CWR:Game/Commands/GameStateExt.cpp#L123-L128` |
| Object, Group | Stored as an object/group **reference by ID**, resolved through `GLandscape->FindObject(id)` in the new world. Treat it as `objNull` or wrong | **[V]** `CWR:Game/Commands/GameStateExt.cpp#L77-L107`, `CWR:World/Scene/Object.cpp#L1547-L1561`. The Biki note says objects come back as objNull **[W]** |
| Config/file handle | Not serialized | **[V]** `CWR:Game/Commands/GameStateExt.cpp#L256-L267` |
| nil | Cannot be saved or deleted | **[V]** `CWR:Game/Commands/GameStateExtGrp.cpp#L417-L420` |

No count or size limit exists in code. Because each history row duplicates the whole table, `.sqc` size grows roughly with missions × vars **[I]**.
The engine has no `isNil`. The 1.99-era idiom `format ["%1",v] == "scalar bool array string 0xfcffffef"` matches the engine's nil text **[V]**
(`BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/express.cpp#L1908-L1913`). **Generated code should initialize every campaign variable in the first mission instead of testing
for nil.**

**Gotchas [V/I]:**
1. `saveVar` takes effect immediately. An in-mission Retry without an autosave re-injects the *already-modified* table. **Commit only at mission
   end.**
2. A debriefing Restart runs the mission with **no** campaign vars (see above). This is a latent bug. Either disable the restart with `lives = 0`
   (which also changes death handling, §4) or accept it and add a guard.
3. Every saved variable is re-injected into **every** later mission, which can shadow mission globals. **Namespace campaign vars** with a prefix
   such as `cmp_`.
4. **Arrays alias [V by reading, runtime U].** `GameValue` copies share their data
   (`BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/express.cpp#L2104-L2112`), `saveVar` stores the variable's value as-is
   (`CWR:AI/AICenterStats.cpp#L69-L80`), re-injection uses `VarSet` with the same value, the history row snapshot is a shallow copy
   (`CWR:UI/OptionsUI.cpp#L1132`), and `set` mutates an array in place (`BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/express.cpp#L678-L708`). So `cmp_roster set [0, x]` changes the campaign table
   and the current row's in-memory snapshot (re-saved to the `.sqc` at `NextMission`) without any `saveVar`, which breaks transactional commit and
   restart-from-k. **Generated code must never mutate a campaign array in place:** copy it first (`_a = [] + cmp_roster`; this copy is shallow,
   so rebuild any nested row it changes), edit the copy, and assign and `saveVar` it in the finisher.
5. **Init-time saves are baked into the row snapshot [V].** The snapshot is taken after unit inits, `init.sqs` and the briefing (§3), so a
   non-idempotent `saveVar` in init code (e.g. a visit counter) is applied twice after a restart-from-k. Keep init-time saves idempotent.

### 6.2 Campaign history, revert and replay

- The history is `CampaignHistory { battles[] { battleName, missions[] { missionName, displayName, completed, stats (score, kills, casualties,
  saveVar table), weapons[], magazines[], dead[] } } }` **[V]** (`CWR:UI/OptionsUICommon.hpp#L61-L105`).
- **Restart from row k (campaign book) [V].** The game truncates history to the rows *before* k, sets `GStats._campaign = row.stats` (the saveVar
  table and score as snapshotted when k's gameplay started), deletes the saves, and restarts k. If k is the first row of its chapter, the chapter
  cutscene plays again (`CWR:UI/OptionsUIApp.cpp#L458-L501`). A row's `weapons`/`magazines` are *not* a frozen snapshot: they are the live pool
  while that mission runs and are saved at its end. Restart still reverts the pool, because the new row k copies the pool from row k−1
  (`CWR:UI/OptionsUI.cpp#L1704-L1711`). This gives us correct "time travel" for saveVar and pool state, subject to the array-aliasing and
  init-time-save caveats in §6.1.
- **Replay a completed row [V].** Replay runs as a non-campaign session (`CurrentCampaign = ""`). `objects.sav` is copied into Tmp, so writes are
  sandboxed. Replay never advances the campaign (`CWR:UI/OptionsUIApp.cpp#L503-L553`, `CWR:UI/OptionsUIImpl.cpp#L1193-L1197`).
- **Book display [V].** Rows with an empty `displayName` are hidden (`CWR:UI/OptionsUIImpl.cpp#L1069-L1083`). Vanilla, however, always fills
  `displayName` (briefingName, else `<file>.<island>`) (`CWR:UI/DisplayUIMenus.cpp#L814-L818`). **Every router or cutscene node therefore shows as
  a row** that the player can restart from.

### 6.3 `objects.sav`: saveStatus / loadStatus / deleteStatus / saveIdentity / loadIdentity / deleteIdentity

| Command | Behavior [V] |
| --- | --- |
| `obj saveStatus "key"` | Serializes `obj` in the "unit status" branch into `Objects/<key>`. For a Person this also marks the identity as used ("dead" list) (`CWR:Game/Commands/GameStateExtWorld.cpp#L814-L869`) |
| `obj loadStatus "key"` | Two-pass deserialize onto `obj` (`#L898-L945`) |
| `deleteStatus "key"` | Removes the entry (`#L871-L896`) |
| `unit saveIdentity "key"` / `loadIdentity` / `deleteIdentity` | Same, for `Identities/<key>`: name, face, glasses, speaker, pitch, experience, rank, and skill (`#L947-L1077`, `CWR:World/Entities/Infantry/Person.cpp#L414-L449`, `CWR:AI/AIUnit.cpp#L549-L560`) |

What "status" contains **[V]**:
- damage and destroyed state (`CWR:World/Entities/Weapons/Dammage.cpp#L626-L650`);
- the per-hitpoint `hit[]` array and `isDead`;
- weapons, magazines and magazine slots (`CWR:AI/VehicleAIDiag.cpp#L1254-L1441`);
- supply cargo: fuel, repair and ammo cargo plus weapon and magazine cargo (`CWR:World/Entities/Vehicles/Transport.cpp#L341-L361`);
- the identity, for persons (`CWR:World/Entities/Infantry/Person.cpp#L398-L412`);
- **not** position or transform (`CWR:World/Simulation/Simul.cpp#L1404-L1422`).

Other vehicle-class fields are **[U]**.

Constraints **[V]**:
- There is **one file per campaign**. It is not part of the history, so it is **never reverted** by restart-from-k.
- It is **not deleted** when a new campaign playthrough starts: the "Begin" path deletes only the `.fps` files
  (`CWR:UI/OptionsUIApp.cpp#L433-L447`).
- Outside a campaign, the commands write to `Saved/Tmp/objects.sav`.
- Biki says `loadIdentity` "does not work in Multiplayer" **[W]**.

### 6.4 Weapon and magazine pool

The pool is stored on the **current history row** (`MissionHistory.weapons/magazines`) **[V]**.
- At `AddMission`, the previous row's pool is copied into the new row (`CWR:UI/OptionsUI.cpp#L1704-L1711`).
- Commands **[V]** (`CWR:UI/OptionsUI.cpp#L1386-L1650`, registered at `CWR:Game/Commands/GameStateExt.cpp#L894-L895`, `#L1115-L1122`, `#L1133`):
  - `addWeaponPool` and `addMagazinePool ["name", n]`, where a negative `n` removes;
  - `clearWeaponPool`, `clearMagazinePool`;
  - `queryWeaponPool` and `queryMagazinePool "name"`;
  - `putWeaponPool obj`: pool into cargo, then empties the pool;
  - `pickWeaponPool obj`: cargo into the pool, then empties the cargo;
  - `fillWeaponsFromPool unit`: needs `weaponPool = 1`.
- With no history row the commands do nothing. In a new campaign the first row is only created by `AddMission` when the first mission's gameplay
  starts, so this covers the first chapter cutscene, the first mission's intro, **and the first mission's unit inits, straight-line `init.sqs`
  and briefing** (`CWR:UI/OptionsUIApp.cpp#L360-L384`, `#L893-L941`). This explains the community advice to fill the pool "in the first mission,
  not the first cutscene" **[V code, W advice]**; the generator should fill it from a trigger or a delayed script in the first mission **[I]**.
- Pool changes live on the in-memory history row until the next `SaveMission` (at mission end). Resuming an aborted mission from
  `continue.fps` reloads the history from the `.sqc`, so in-mission pool changes made before the abort are lost
  (`CWR:UI/OptionsUIApp.cpp#L448-L457`) **[V by reading, runtime U]**. Apply pool changes in the finisher, at mission end.
- Briefing gear draws from the pool when `weaponPool = 1`. Otherwise it uses the mission's own `Weapons`/`Magazines` classes
  (`CWR:UI/Map/UIMapDisplay.cpp#L1132-L1144`).
- There is **no vehicle pool and no unit roster** in the engine. Both have to be built from saveVar arrays, `saveStatus`, `createVehicle`,
  `createUnit` and `deleteVehicle` **[V absence; I pattern]**.

### 6.5 Savegames, score, lives, MP

- **Starting a mission deletes the saves [V].** Starting a mission, whether new or restarted, deletes `continue/autosave/save.fps` and
  `weapons.cfg` (`CWR:UI/OptionsUIApp.cpp#L897-L907`). Aborting a mission writes `continue.fps`, which is what "Resume" loads
  (`CWR:UI/DisplayUIMenus.cpp#L886-L895`, `#L1126-L1134`). Savegames carry `GStats` and therefore the saveVar table **[V]**.
- **Score [V].** Campaign score, casualties, kills and time are statistics only. They are shown in the book and drive `Awards`/`Penalties`/`exitScore`
  (`CWR:AI/AICenterStats.cpp#L82-L174`). They are not exposed to transitions except through `exitScore`.
- **MP [V].** There is no MP campaign flow. The server clears `CurrentCampaign`/`CurrentBattle`/`CurrentMission` and cycles a flat `class Missions` list from its server config (`template`, `cadetMode`,
  `param1`, `param2`) (`CWR:Network/NetworkServerSimulate.cpp#L528-L552`). Campaign vars are re-injected only in SP paths, so `saveVar` has no
  cross-mission effect in MP **[I]**.

## 7. Hard limits for complex designs

| Limit | Status | Workaround |
| --- | --- | --- |
| At most 7 outgoing edges per mission class (`lost`, `end1..6`) | [V] | Chain router missions (7^depth leaves) |
| Transition targets are static: no conditions or expressions in the campaign classes. The campaign description.ext is re-parsed at every `NextMission` (`CWR:UI/OptionsUI.cpp#L1896`, `#L777-L794`), and CWR's parser does support `__EVAL(...)`/`__EXEC(...)` against the global game state (`CWR:IO/ParamFile/ParamFile.cpp#L1703-L1733`, `#L1805-L1808`; `CWR:IO/ParamFile/ParamFileEval.cpp#L121-L129`). But a string result comes back via `GetText()` with embedded quotes, so it cannot name a mission class, and 1.99 support is unknown | [V] no conditions; [I] `__EVAL` unusable for targets | Decide in script, then pick one of the 7 codes |
| Mission-level edges must stay in the same chapter. Cross-chapter edges land on `firstMission` | [V] | A single engine chapter, or a router as each chapter's `firstMission` |
| Death (`EMKilled`) is not routable and runs no `exit.sqs` | [V] | A `LOOSE` trigger while the player is alive (SP respawn is hard-wired off, §5) |
| Award cutscenes are never selected in CWR (penalties are) | [V by reading; 1.99 U] | Never depend on `Awards` (doc 35 rc80); put reward beats in a mission `Intro` or a cutscene node |
| Campaign arrays alias in memory; in-place `set` bypasses `saveVar` and corrupts the row snapshot | [V by reading] | Copy-then-assign only (§6.1 gotcha 4) |
| `END<n>` needs **all** `END<n>` triggers active. Lower number wins on ties | [V] | Generate exactly one trigger per code, driven by `cmpEnd` |
| No script command to end with a specific code in 1.99-era script | [V] | Condition-only triggers plus `forceEnd` |
| Cutscene-only nodes always exit through `lost` | [V] | Map `lost` to the successor |
| Chapter cutscenes, outros, awards and debriefing-restart get no campaign vars; mission intros get them only after their unit init lines | [V] | State-dependent cinematics go in a mission `Intro` (driven from `initintro.sqs`) or a router |
| `objects.sav` is not versioned or reverted, and survives a new playthrough | [V] | Versioned keys plus a run nonce (§8.4) |
| Object/group values in `saveVar` are unreliable | [V] | Save strings (class names, `setIdentity` keys) and numbers |
| No MP campaigns | [V] | Out of scope, or an SP-only feature |
| One savegame slot per campaign | [V] | None (engine) |
| Template and path buffers are 256 chars | [V] `CWR:UI/Map/UIArcadeWaypoint.cpp#L872-L873` | Keep names short |
| The book shows every played node, including routers | [V] | Give routers a meaningful `briefingName`, or use CE extension E3 |

## 8. Patterns for arbitrary state-based transitions on vanilla

In the editor's model, a **transition** is `(fromNode, guard(globalVars, missionVars), toNode, effects)`, and the guards are evaluated in order.
The compiler lowers each guard into engine primitives.

### 8.1 Pattern A: in-mission decision via "outcome sockets" (default)

- Every compiled mission gets 7 generated condition-only triggers (`LOOSE`: `cmpEnd == 0`; `END1..6`: `cmpEnd == n`). Each has `forceEnd` in On
  Activation. Condition-only (activation `NONE`) triggers work because the condition replaces the area result
  (`CWR:World/Detection/Detector.cpp#L865-L868`, `#L1259-L1265`) **[V]**. `cmp_init` should set `cmpEnd = -1` first so no socket can match an
  unset value **[I]**.
- Designer triggers or scripts never pick an END type directly. They call the generated finisher, e.g. `[] exec "cmp_finish.sqs"`. The finisher:
  1. applies transition **effects** to the `cmp_*` globals;
  2. `saveVar`s every declared campaign variable (commit);
  3. evaluates the ordered guards and sets `cmpEnd`.
- The finisher is emitted in SQS with **reverse-priority assignment**, so it needs no `goto` or multi-statement lines:
  `cmpEnd = 1`, then `? cond3 : cmpEnd = 3`, then `? cond2 : cmpEnd = 2`. The last line is the highest priority.
- **Guards can read both global and mission state**, because campaign vars are ordinary globals inside the mission.
- Covers most designs when a mission has 7 or fewer distinct successors. It costs no UX.
- A commit-only fallback in `exit.sqs` catches endings not raised through the finisher. That is only for bookkeeping, e.g.
  `cmp_lastEnd = _this; saveVar "cmp_lastEnd"`. `exit.sqs` does not run on player death (§5), so this fallback commits nothing on a death.

### 8.2 Pattern B: zero-gameplay router missions

- **When to use:** fan-out above 7, cross-chapter jumps to a non-first mission, decisions shared by several predecessors, and "hub" logic. Another
  use is separating content missions from graph logic, so that a content mission always ends with a plain semantic code and the router maps state
  to the next node.
- **How to build a router [V for each engine rule used]:**
  - At least one group, with a player unit. With no groups the node is forced to `lost`.
  - No `briefing.html`, so the briefing is skipped.
  - Its description.ext sets `debriefing = 0`.
  - Empty `Intro`, `OutroWin` and `OutroLoose`.
  - `noAward = 1` and `lives = -1` in the campaign class.
  - `init.sqs` does `titleCut [" ","BLACK FADED",0]` (or `cutText`), then evaluates guards and sets `cmpEnd`.
  - The 7 socket triggers use `forceEnd`. In CWR `titleCut` draws on the cut layer, which does not block the end (§5), so `forceEnd` is
    strictly needed only if a title-layer effect (`titleText`/`titleRsc`) or camera is active. Keep it anyway: it is harmless and covers a
    possible 1.99 layer difference **[I]**.
  - Place the router on the **same island as its predecessor** to avoid a landscape reload.
  - Several router classes can share one folder (§4). The class names differ; the folder, and so its decision script, is shared.

| UX cost of a router | Suppressible in vanilla? |
| --- | --- |
| Chapter cutscene | Only on chapter change. Leave `cutscene` empty |
| Intro, briefing, debriefing, outro, award | Yes (see the build steps above) |
| `World::CleanUp` + `InitVehicles` (a short load; the island loads only if it differs) | No. Keep the router minimal and on the same island |
| One or more frames of the world | Hidden behind BLACK FADED |
| **A row in the campaign book**, which the player can restart from | No (see E3). Restart re-evaluates from the snapshot, so it is deterministic |

- **Cutscene nodes:** a node whose mission.sqm has no groups plays its `Intro` (which *does* get campaign vars, from `initintro.sqs` on, but not in
  its unit init lines) and always exits via `lost` [V]. That makes it a cheap linear "story beat" that can still vary its content by state.

### 8.3 Pattern C: generated glue from a data model

The editor owns a `CampaignModel`: nodes (Mission, Router, Cutscene), typed variables (bool, int, float, string, enum, list; with default, scope
"campaign" or "mission", and whether persisted), ordered guarded transitions with effects, and optional acts. It compiles to:
1. `description.ext`: one engine chapter by default, every key explicit (§2), end-code maps assigned by the compiler.
2. Per mission:
   - `cmp_init.sqs`, called first from `init.sqs`: namespacing and entry snapshot;
   - `cmp_finish.sqs`: effects, commit and decide;
   - the 7 socket triggers, merged into mission.sqm;
   - `exit.sqs` bookkeeping.
3. Router missions and trees, synthesized automatically wherever a node has more than 7 distinct successors or crosses a chapter.
4. A first-mission bootstrap that initializes every declared variable (there is no `isNil`) and saves `cmp_schema` and `cmp_runId` (a random
   nonce).
5. **Validation:** every end code resolves; templates exist; routers have groups; no CWR-only commands appear in the output when targeting 1.99.
   CWR registers commands that are likely absent from 1.99, e.g. `publicExec` and `remoteExecRemove` at `CWR:Game/Commands/GameStateExt.cpp#L1146-L1147`
   (their absence from 1.99 is unverified). CWR also runs a mission `init.sqf` (`CWR:UI/DisplayUI.cpp#L131-L144`), which 1.99 content must not
   rely on (unverified for 1.99). Also warn on unreachable nodes and cycles.
6. **An offline path simulator in the editor:** evaluate guards over var states to enumerate reachable paths, including "what if" state injection.
   For in-game testing, the compiler can emit a throwaway **debug campaign** whose `firstMission` is a setup router that `saveVar`s a chosen state
   and routes to node X. This uses only vanilla mechanics **[I]**.

### 8.4 Robust state rules the generator should enforce

- **Transactional commit:** `saveVar` only in `cmp_finish`/`exit.sqs`. This avoids the Retry pollution in §6.1.
- **Entry snapshot:** `cmp_init` copies the incoming values into `cmpIn_*` and saves them. On a detected re-entry it restores from `cmpIn_*`.
  This protects against partial commits. It does **not** fix the debriefing-restart bug, where the vars are absent altogether **[I]**.
- **Versioned `objects.sav` keys:** write `saveStatus`/`saveIdentity` under `"<runId>_<producerNode>_<slot>"`. Keep the pointer to the producing
  node in a saveVar (`cmp_lastNode`, which *does* revert). Readers load `"<runId>_<cmp_lastNode>_<slot>"`. Restart-from-k then stays consistent,
  and stale data from an old playthrough is never read **[I]**.
- **Squad or roster:**
  - Keep the authoritative roster in saveVar arrays, e.g. `[["dimitri", true, 0.2, "sergeant"], ...]`. Update it only by copy-then-assign,
    never with an in-place `set` (§6.1 gotcha 4).
  - Use `saveIdentity`/`saveStatus` only for gear, damage and experience blobs.
  - Pre-place the squad in every mission, `deleteVehicle` the units recorded as dead, and `loadStatus` the survivors. This mirrors how Resistance
    presented persistent team casualties **[W; exact script I]**.

### 8.5 Choosing between A, B and C

A and B are the compiler's lowering targets; C is the editor-side model plus compiler. Use A for ordinary missions. Let the compiler insert B only
when a limit in §7 forces it. Never make designers write END triggers by hand for campaign nodes.

## 9. Optional CWR-CE engine extension: hook points and verdict

The CWR and CWR-CE campaign code is the same at the pinned SHAs. In CWR-CE, `NextMission` is at
`ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/UI/OptionsUI.cpp#L1900`, and `DisplayUIMenus.cpp`, `WorldImpl.cpp`, `AICenterStats.cpp` and
`UIMapDialogs.cpp` are byte-identical **[V]** (hash compare). Every proposal below must keep vanilla behavior when its keys are absent. 1.99 will
simply ignore any unknown keys or classes.

| # | Change | Exact hook | Vanilla fallback | Verdict |
| --- | --- | --- | --- | --- |
| E1 | **Declarative router fast-path.** A router class may carry `class CEDecide { end1 = "<SQS expr>"; ... }`. At transition time CE evaluates the expressions against the saveVar table and hops directly to the target, skipping the router world. Hop depth is capped | `NextMission`: refactor `CWR:UI/OptionsUI.cpp#L1925-L1986` into `ResolveNext()` and loop before template resolution at `#L1988`. Evaluate as `Detector` does (`GameState::EvaluateBool`, `CWR:World/Detection/Detector.cpp#L1259-L1264`) on a scratch state filled by the `VarSet` loop of `CWR:UI/OptionsUIApp.cpp#L883-L892`. Skip `AddMission` for skipped routers; the pool stays on the previous row and is copied later **[I]** | 1.99 plays the router mission, whose generated SQS evaluates the **same expression text** | Nice-to-have; later |
| E2 | Cross-chapter direct targets, e.g. `end1 = "Act2/M05"` | `CWR:UI/OptionsUI.cpp#L1985` | Router as chapter `firstMission` | Low value if we use a single chapter |
| E3 | Hide router rows (`hideInHistory = 1`) | Pass an empty `displayName` in `AddMission` at `CWR:UI/DisplayUIMenus.cpp#L812-L821` and `CWR:UI/OptionsUIApp.cpp#L863-L871`. The book already skips empty names at `CWR:UI/OptionsUIImpl.cpp#L1075-L1078` | Row visible | Cheap; pairs with E1 |
| E5 | **Re-inject campaign vars on debriefing Restart**, and optionally restore `GStats._campaign` from the current row snapshot on Retry | `CWR:UI/Map/UIMapDialogs.cpp#L677-L694` (add the `VarSet` loop). Optionally `CWR:UI/DisplayUIMenus.cpp#L1058-L1068` | Unchanged (buggy edge) | **Worth upstreaming**: a bug fix with no content dependence |
| E6 | Reset `objects.sav` on "Begin campaign" (opt-in `resetObjectsOnStart = 1`) | `CWR:UI/OptionsUIApp.cpp#L433-L447`, `#L350-L384` | Stale file (the nonce keys already cope) | Worth upstreaming as opt-in |
| E4 | New script commands (`endMission`, `unsaveVar`, ...) | `CWR:Game/Commands/GameStateExt.cpp#L881-L895`, `#L1069` | **None**: missions using them break on 1.99 | **Reject** for generated content |

**Argument.** Everything designers need (arbitrary guards over global and mission state, arbitrary graphs, persistent rosters) is expressible on
vanilla through Patterns A to C. The cost is router load blips and book rows. The CE patches buy UX polish (E1, E3) and correctness (E5, E6), not
new expressiveness. Build vanilla-first. Propose E5 and E6 upstream early, because they are small and safe. Consider E1+E3 only once real campaigns
show that router UX hurts. Keep generated content 1.99-clean always.

## 10. How the community did it [W]

- **1985 (CWC)** used the 7-code table for branching. "Montignac Must Fall" ends in a scripted reversal whatever the player does, and
  its successor depends on how the player leaves the town (the exit route), not on whether the assault succeeded: END1 leads to a
  lone-escape mission and the other codes to a different one ("After Montignac" and "Strange Meeting"); both paths rejoin at "Rescue"
  (doc 35 §3.1, §3.5, §10, read from the shipped campaign files). This supersedes the success/failure reading applied here earlier on
  2026-09-27 from the doc 26 fact-check (a GameRevolution walkthrough and a Bohemia forum thread); see the consolidation pass below.
  Early squad deaths did not persist ("they just reappear").
- **Resistance (1.75)** introduced persistent team casualties, the weapon pool, `saveStatus`/`loadStatus`, and `saveIdentity`/`loadIdentity`.
  Known issues:
  - pool commands failed in some missions on 1.75 (fixed in 1.85+);
  - replaying a mission loses access to the pool. In CWR code, replay restores the history truncated before the replayed row, so pool
    commands should see the preceding row's pool (`CWR:UI/OptionsUIApp.cpp#L503-L553`) **[I]**; the report may be 1.75-era (unverified).
- The **PMC campaign guide** advises:
  - shared scripts in `<root>\Scripts\` (this matches `FindScript`);
  - campaign-level music in the root description.ext;
  - no mission.sqm in the campaign root;
  - testing every edge with the `ENDMISSION` cheat (engine: `CheatWinMission` → `END1` only, `CWR:World/WorldImpl.cpp#L502-L507`). Other codes
    need dev cheats, or CWR's debug `endmission end1..end6` (`CWR:Dev/Debug/DebugCheats.cpp#L656-L741`), which Trident integration tests also use
    (`BohemiaInteractive/CWR@ffc61838b7:tests/integration/ui/debriefing/campaign_result_current_section.test.sqf#L16`).
- **OFPWiz "Dynamic Campaign" (OFPEC, 2007)** carried captured weapons and vehicles, surviving teammates and the enemy force size between
  sectors. It is state carry-over rather than authored branching.
- **Design precedent for the editor model:** Iron Curtain's campaign spec ("Inspired by Operation Flashpoint: Cold War Crisis / Resistance")
  uses a graph with named outcomes, persistent
  roster and flags, and failure as an edge (`iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/modding/campaigns.md#L3-L15`, YAML at
  `#L57-L167`). That maps cleanly onto Patterns A to C.

## Open questions

1. **Parity of the 1.99 binary** with the CWR source for:
   - `debriefing = 0`;
   - missing-key behavior (for example `lives`);
   - empty-value syntax (`key = ;` vs `""`);
   - `forceEnd` with an active BLACK FADED title, and whether 1.99's `titleCut` uses the cut or the title layer;
   - the `WIN` alias;
   - whether award cutscenes ever play (the CWR award-selection loop never selects one, §2; doc 35 open question 6);
   - whether 1.99 parses `__EVAL` in a campaign description.ext;
   - the array-aliasing behavior of `saveVar` plus in-place `set` (§6.1 gotcha 4).

   Needs a Preview test on CWA 1.99 **[U]**.
2. Does 1.99's `RscDisplayDebriefing` show "Restart" in SP campaigns, and does 1.99 share the "no campaign vars after debriefing restart" behavior
   **[U]**?
3. Does 1.99 skip `AddMission` history rows or store them identically? Where does 1.99 keep `.sqc` and `objects.sav` **[U]**?
4. Which unit-status fields beyond those listed (fuel, ammo per vehicle class) round-trip through `saveStatus` **[U]**?
5. Does `exit.sqs` run to completion within one `SimulateScripts()` call when it has several statements **[I]**? Needs a test. Partly
   answered by reading: the call has no line limit (doc 35 §3.3); a runtime Preview check on 1.99 remains **[U]**.
6. Should editor "acts" become real engine chapters (chapter cutscene, book grouping) at the cost of edge restrictions, or stay cosmetic
   (recommended default)? This is a product decision.
7. Is CWR-CE open to upstreaming E5 and E6 (and later E1 and E3)? Maintainer contact needed.

## Sources

Code (pinned):
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/OptionsUI.cpp` (L148-L275, L630-L655, L777-L853, L1073-L1712, L1721-L2022)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/OptionsUIApp.cpp` (L350-L384, L420-L566, L850-L1049)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/OptionsUIImpl.cpp` (L483-L486, L1034-L1234, L1587-L1790)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/OptionsUICommon.hpp` (L41-L105)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/DisplayUIMenus.cpp` (L784-L1095, L1202-L1508)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapDialogs.cpp` (L542-L711, L891-L1091)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapDisplay.cpp` (L468-L539, L1132-L1144)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcadeWaypoint.cpp` (L870-L902)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/WorldImpl.cpp` (L500-L665, L1141-L1158)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/WorldInit.cpp` (L622-L632, L1001-L1026)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenter.hpp` (L151-L154, L506-L586)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterStats.cpp` (L69-L280, L618-L623)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp` (L843-L851)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.cpp` (L191-L203); `.../AI/Path/ArcadeWaypoint.hpp` (L242-L257)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Game/Commands/GameStateExt.cpp` (L77-L128, L256-L267, L881-L895, L1069, L1115-L1147, L1374-L1378)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Game/Commands/GameStateExtGrp.cpp` (L412-L425)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Game/Commands/GameStateExtWorld.cpp` (L775-L1077, L1206-L1327)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Game/Commands/GameStateExtUi.cpp` (L184-L198); `.../GameStateExtWorldDialog.cpp` (L24-L49)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/express.cpp` (L1908-L1913, L1992-L2101, L2399-L2404, L3095-L3101)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Scene/Object.cpp` (L1547-L1561); `.../World/Entities/Infantry/Person.cpp` (L398-L449); `.../AI/AIUnit.cpp` (L549-L560); `.../AI/VehicleAIDiag.cpp` (L1254-L1454); `.../World/Entities/Weapons/Dammage.cpp` (L626-L650); `.../World/Entities/Vehicles/Transport.cpp` (L341-L361); `.../World/Simulation/Simul.cpp` (L1404-L1422)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Core/SaveVersion.hpp` (L1-L30); `.../Core/GameState.cpp` (L201-L215, L277); `.../IO/ParamFile/ParamFile.cpp` (L1309-L1318)
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Entities/Infantry/SoldierOldMove.cpp` (L1068-L1086); `.../Network/NetworkServerSimulate.cpp` (L528-L552); `.../Dev/Debug/DebugCheats.cpp` (L656-L741); `.../World/Detection/Detector.cpp` (L696-L707, L1259-L1264)
- `BohemiaInteractive/CWR@ffc61838b7:tests/integration/ui/debriefing/campaign_result_current_section.test.sqf` (L1-L23)
- Added in verification: `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/World.hpp` (L428-L448); `.../Game/Commands/GameStateExtUi.cpp` (L1729-L1735); `.../Game/Commands/GameStateExt.cpp` (L1000-L1008); `.../World/WorldInit.cpp` (L1107-L1111); `.../IO/ParamFile/ParamFile.cpp` (L1703-L1733, L1805-L1808); `.../IO/ParamFile/ParamFileEval.cpp` (L121-L129); `.../UI/DisplayUI.cpp` (L121-L144); `BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/express.cpp` (L678-L708, L2104-L2112)
- `ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/UI/OptionsUI.cpp` (L1900); `.../Game/Commands/GameStateExt.cpp` (L1067, L883-L884); `.../Game/Commands/GameStateExtTestAudio.cpp` (L2996)
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/modding/campaigns.md` (L3-L167)

Web (accessed 2026-09-26; Biki pages returned HTTP 403 to the fetcher, so claims marked "search" come from search-result extracts):
- https://community.bistudio.com/wiki/Campaign_Description.ext (fetched; key list and version notes, `endDefault` = Arma 3)
- https://community.bistudio.com/wiki/saveVar (search; objects saved via saveVar return objNull)
- https://community.bistudio.com/wiki/loadIdentity and https://community.bistudio.com/wiki/saveIdentity (search; added 1.75, not MP)
- https://community.bistudio.com/wiki/Objects.sav (search listing)
- https://community.bistudio.com/wiki/Category:Command_Group:_Weapon_Pool (search; pool introduced with Resistance)
- https://community.bistudio.com/wiki/Operation_Flashpoint:_FAQ:_Campaigns:_Resistance (search; replay loses pool, 1.75 pool bug fixed in 1.85)
- https://community.bistudio.com/wiki/Operation_Flashpoint:_FAQ:_Campaigns:_1985_Cold_War_Crisis (search; Montignac branch)
- https://tvtropes.org/pmwiki/pmwiki.php/VideoGame/OperationFlashpoint (search; Resistance persistent team casualties; low-authority)
- https://pmc.editing.wiki/doku.php?id=ofp:missions:weaponpool (fetched)
- https://pmc.editing.wiki/doku.php?id=ofp:missions:campaign_design (fetched)
- https://pmc.editing.wiki/doku.php?id=ofp%3Afile_formats%3Adescription.ext (search; `debriefing` parameter listed for OFP)
- https://www.ofpec.com/missions_depot/index.php?action=details&id=107 (fetched; OFPWiz Dynamic Campaign)
- https://community.bistudio.com/wiki/endMission (search; Arma 2-era command)
- https://community.bistudio.com/wiki/isNil (search; not available in OFP/CWA)
- https://community.bistudio.com/wiki/titleCut (search; obsolete, use `cutText`)

## Verification notes

Adversarial re-check on 2026-09-26 against the pinned clones (`BohemiaInteractive/CWR@ffc61838b7`, `ofpisnotdead-com/CWR-CE@b67bf3bd62`) and
the cited web pages. Confirmed: the 7-code static lookup and chapter fallback (`NextMission`), END/LOOSE priority and AND semantics, `EMKilled`
handling and the `lives = 0` loop, no-groups → `lost`, `saveVar` upsert/lower-casing/no-delete, re-injection points, `debriefing = 0`, `noAward`,
empty Intro/Outro skipping, `objects.sav` location and non-reset, pool commands and `weaponPool` gating, book rows, MP rotation, and CWR-CE
parity (hash-identical `DisplayUIMenus.cpp`, `WorldImpl.cpp`, `AICenterStats.cpp`, `UIMapDialogs.cpp`, `WorldInit.cpp`, `UIMapDisplay.cpp`,
`GameStateExtGrp.cpp`, `express.cpp`; the other diffs are download/UI code and the `endGame` → `triEndGame` rename).

Corrected:
- `forceEnd` is needed only for title-layer or camera effects; CWR's `titleCut` is a cut-layer alias of `cutText` (router recipe reworded).
- Respawn is not a workaround for death routing in SP (respawn mode is forced to `RespawnNone` outside MP).
- Mission intros inject campaign vars only after the intro's unit init lines.
- The row snapshot is taken after unit inits, `init.sqs` and the briefing; the row pool is live, not a start-of-mission snapshot (revert still works).
- Pool commands are also no-ops in the first mission's init code and briefing, not just the first cutscene/intro.
- Award cutscenes are never selected by the CWR award loop (only penalties play).
- The campaign config is re-parsed at every transition and the parser supports `__EVAL`; still unusable for targets **[I]**.
- New gotcha: in-memory array aliasing between globals, the saveVar table and the row snapshot.
- Citation fixes: `World::CleanUp` at `WorldInit.cpp#L1107-L1111`; the Iron Curtain quote made exact.

The bottom line is unchanged. Transitions are a static 7-code table. Vanilla routers plus in-mission sockets can express arbitrary state-based
trees. A CE patch adds polish and fixes, not expressiveness.

### Consolidation pass (2026-09-27)

Cross-doc corrections from doc 35 §10 ("Doc 18"), with evidence checked in doc 35 §3.3, §3.4, §6.3 and its verification notes:

- §4: the shared-template consequence now cites field evidence (community dynamic campaigns point three classes at one template, doc 35 §6.3,
  §10; the count of three is stated only in §10, §6.3 says "several"). The engine-reading label stays **[I]**.
- §2 row, §4, §3 flow, §7 and the TL;DR: CWR's award selection never picks an award (already in §2; now surfaced where the flow and limits
  are read), with a new §7 row and the doc 35 rc80 advice not to depend on `Awards`.
- §5, §3 flow, §7, §8.1 and the TL;DR: `exit.sqs` does not run on player death.
- §5 and open question 5: doc 35 §3.3 reads the `exit.sqs` call as having no line limit; open question 5 is marked partly answered.
- §10, Montignac branch (doc 35 §10 "Doc 26", evidence in §3.1 and §3.5): the success → "After Montignac" / failure → "Strange
  Meeting" wording applied earlier today from the doc 26 fact-check is superseded. The mission ends in a scripted reversal and
  the branch keys on the exit route (END1 → a lone-escape mission, other codes → a different mission); both legs still rejoin at
  "Rescue". Doc 35 does not name the two successors, so which name belongs to which route is left unstated here.
- No Standing Orders / Drill renames or doc 33 / skill links were needed in this doc (re-checked 2026-09-27).
