# Power tools: first-class replacements for hand-edits and init-line workarounds

Research doc 37 for Plotroom (`ofp-editor`). Research date: 2026-09-27. Audience: contributors and LLM coding agents. This file is meant to be read on its own.
Question answered: for two decades OFP/CWA mission makers reached what the original editor could not give them by hand-editing `mission.sqm`, `description.ext`, `briefing.html` and `stringtable.csv`, or by typing init-line and script code. Which of those workarounds matter, what was each one really for, and how should Plotroom offer each as a direct, friendly, typed editor feature that still produces the same vanilla output?

**Status.** Proposal-only. Every type, name, code, threshold and UX in §2–§11 is **[I]** unless a cell or line says otherwise.
**Epistemic legend.** **[V]** verified by static reading of the pinned engine source, a fetched page or a corpus count; nothing was built or run, so [V] never means "observed at runtime". **[V-ext]** verified against an external artifact (the BIKI mirror's version tags, the 1.99 executable string scan of doc 35 §8.2, Faguss's 1.96→1.99 notes). **[I]** our inference or proposal. **[U]** unknown; needs a probe.
**Citation aliases.** `P:` = `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/`. `GSE` = `P:Game/Commands/GameStateExt.cpp` (the command registration table). `EVAL:` = `BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/`. `CE:` = `ofpisnotdead-com/CWR-CE@b67bf3bd62:`. Unless a CE line is given, a `P:` citation also holds for CE (the cited files are identical or differ only in wording, doc 03 §5). "1.99" means the legacy CWA 1.99 executable; its runtime is [U] unless the string scan or Faguss's notes say otherwise.
**Evidence bases.** Counts are "missions with at least one occurrence" unless they say fields, units or statements.

- **O**: 200 unique official missions (117 campaign, 24 SP, 30 MP, 29 templates), classified by an intent classifier over every code field in all four sections. A spot check of 65 statements found no misclassification.
- **F**: 276 unique missions (200 official, 31 Remastered templates, 45 CWE-modified) from a field-gap scan. 205 of them are binarized, so text-format hand-edit signatures could be checked on 71 only.
- **S**: 9 unique third-party missions, used for contrast only (too small to generalise).
- **C**: the repo CSVs under `docs/research/data/` (doc 35).
- **Forum**: OFPEC board-title regex counts and view counters. They are order-of-magnitude only: several top threads have 0–2 replies and probably inflated counters, and two draft title counts could not be reproduced.

All corpus inputs come from the owner's local install, read-only. Only aggregate numbers and command, key and field names appear here; no mission text, variable name or path is quoted.
**Relation to sibling docs.** Doc 31 defines the no-code ladder and the rung-1 contract (attributes and presets, generated init prefixes tracked by span and hash, lift offers). This doc is the detailed rung-1 design plus the inspector and tools around it. Doc 04 owns the lossless CST and patch rules, doc 27 dependency derivation, doc 33 concept explanations, doc 34 named zones, the retarget workbench (target profiles) and re-association after vanilla re-saves, and doc 35 the `Cwa199` evidence tiers. §10 says what lives where.
**Codes (provisional; the design round assigns final numbers).** Rows `WA01`–`WA47`, principles `G1`–`G8`, lints `PL01`–`PL14`, probes `PP1`–`PP12`, phases `PT0`–`PT4`, acceptance tests `PAT1`–`PAT16`. None collides with the codes listed in doc 36's header.
**Hygiene.** All text is our own words. Engine behaviour is cited by pinned path; community practice is described by command names only.

## TL;DR

- **The gap is large and measurable.** In O, 78% of Mission-section init fields, 66% of cutscene init fields and 75% of Mission-section activation fields hold at least one intent that the vanilla UI cannot express; fields fully covered by an existing UI control are under 1% [V]. By missions in F, the biggest init-line intents are identity (140), starting behaviour (129), flags (116), attached scripts (111), loadouts (103), cargo (97), callsigns (92), group variables (89), courage (89) and seats (53) [V].
- **Three kinds of gap.** (1) Hidden sqm keys, plus stock dialogs that destroy hand edits on OK: the minute is rounded to 5, Resistance friendliness is forced to 0 or 1, skill is clamped to 0.2–1.0. (2) Side files with no UI at all. (3) Engine behaviours that only commands reach [V].
- **One contract (G2).** Every affordance compiles to what a careful hand edit or init line would produce for the target profile: native field first, then a hidden sqm key, then a generated init prefix, then a lossless `description.ext`/briefing patch, then a compiler-owned script. The mission still runs with our sidecar deleted, and the generated text is always shown beside the form (G3).
- **An engine-truthful property inspector** (§3) shows every sqm key, including hidden and dead ones, how the stock editor exposed it, and what the engine really does with it: "Y is ignored", "health floors at 3%", "presence is ignored for playable units". It edits exact numbers, supports multi-select, and never replays the stock dialogs' destructive round trips.
- **About 25 typed intent attributes** (§4), from "Starts in: truck1, cargo" to Height, Loadout, Cargo, Cast, Callsign and Start posture. They are found by goal search, right-click verbs and a drop chip, drawn as glyphs on the map, and bundled into presets and kits (§4.4). Engine facts are enforced by construction. Example: Height forces Special NONE on formation members, because the engine moves them to formation slots before init lines run, so a `getPos`-based `setPos` would lift the unit at its slot, not where it was placed [I from V].
- **Corrections found on the way** [V]: `setPos` and `setPosASL` take a mounted soldier out of his vehicle in CWR and CE, which refutes a community note; `lock false` gives DEFAULT, not UNLOCKED; marker setters are local to the machine that runs them; `addOnsAuto[]` is never read; without `allowFleeing`, courage is the leader's skill; unknown enum strings inside an `ItemN` half-load the item instead of failing the mission (only a log line); the runtime friend/enemy test is at 0.6, not the dialog's 0.5; while `allowDammage false` is set, `setDammage` cannot raise damage, so Protected and Starts destroyed exclude each other.
- **Power tools** (§5): class remap with an equivalence table, island move (a dry run, named apart from doc 34's profile "Retarget…"), SP↔MP wizard, side swap, bulk edit, rename with references, dependency doctor, normalisation, merge and split. Each shows a semantic and a byte diff first and applies as one undo group.
- **Map-object actions** (§6): click a building to make it destroyed at start, damaged, an objective or a garrison; IDs are never typed, and every reference stores an island fingerprint.
- **Safe raw mode** (§7): a text view of any mission file with live parsing, engine-strict validation, a typed diff and a lossless patch apply. It never locks the editor.
- **Lift on import** (§8): about 25 idiom recognisers plus hand-edit fingerprints. "Replace" is offered only when re-emission reproduces the normalised original; hand-edited values are protected, not "fixed"; import followed by save stays byte-identical.
- **Wilco** (§9): "put the sniper on the church roof" becomes four code-computed picks and one typed proposal. Weak models never write init code.
- **Honest per profile.** `Cwa199` output defaults to T1 commands (doc 35 §8.3). `setPosASL`, `buildingPos`, `setFuelCargo`, `setRepairCargo` (all T3) and `disableAI "ANIM"` wait on probes PP1–PP5; `allowDammage` is T1 (used in shipped official content), so only its 1.99 effect is checked by PP6. `Cwr`/`Ce`-only features (`setDate`, `setFriend`, `createGroup`, all absent from the 1.99 executable; Intel `viewDistance`) are greyed out with the reason.

## 1. The problem and principles

### 1.1 Three channels of workaround

| Channel | What the original editor offered | What makers did | Evidence |
| --- | --- | --- | --- |
| Hidden, gesture-only or clamped `mission.sqm` keys | Dialog fields per doc 03 §4. `markers[]`, trigger `idStatic`/`idVehicle`, waypoint `id`/`idStatic` and synchronisations only through map gestures. `year`, `leader`, `randomSeed`, `addOns[]`/`addOnsAuto[]`, unit and sync ids, and CWR's Intel `viewDistance` not at all | Opened the file in a text editor; lost some edits the next time anyone pressed OK in Intel or the unit dialog | Minute: `P:UI/Map/UIArcadeWaypoint.cpp#L664-L673`, `#L772-L775`; friendliness: `#L676-L693`, `#L777-L799`; skill: `P:UI/Map/UIArcade.cpp#L949-L956` with `P:UI/Controls/UIControlsWidgets.hpp#L238-L246` [V] |
| Side files with no UI | Nothing. Effects pickers list classes from `description.ext`, which is re-read only on editor Save or Load (`P:UI/OptionsUI.cpp#L855-L879`) [V] | Hand-wrote `description.ext`, `briefing.html`, `overview.html`, `stringtable.csv` and files with magic names (`init.sqs`, `exit.sqs`, `onPlayerKilled.sqs`) | doc 04 §5–§8; doc 09 P3 [V] |
| Engine behaviours with no field | Init, condition and activation fields: single-line, no comments outside `preprocessFile`, values over 2047 bytes truncated on parse, checked strictly (doc 23 §6; doc 04 §2.1) [V] | Seats, heights, loadouts, cargo, identities, stances, captive, callsigns and group names in init lines; anything longer pushed into `.sqs` files and `exec`'d | F: 3,516 init fields; O: 14.4% of objects carry an init line (S: 39.3%) [V] |

There is a fourth, quieter channel: **rules the editor never told you**. The engine re-snaps the file's Y coordinate to the surface, floors health at 3%, ignores presence on playable units and re-places formation members (§3.2). Makers learned these from forum threads and wrote init code to get around them.

**Why the old ways hurt [I, synthesised from docs 09, 31, 33 and the corpus].** Magic strings typed by hand (class names, marker names, callsigns, identity classes) that fail silently; unknown enum strings that are silent no-ops (`P:Game/Commands/GameStateExtGrp.cpp#L171-L261`) [V]; invisible cross-file coupling (identities, objective ids, sound classes); hand edits destroyed by a dialog round trip; and MP locality that nobody could see.

### 1.2 Principles

| # | Principle | Consequence |
| --- | --- | --- |
| G1 | **Intent over code** | The user states what should be true ("starts in truck1's cargo", "on the church roof, prone, holding"), not the command that makes it true |
| G2 | **Same vanilla output per profile** | Each affordance lowers, native first, to exactly what an expert would type for `Cwa199`, `Cwr` or `Ce`. No addon, no runtime framework; the sidecar can be deleted (doc 31 N2, N3) |
| G3 | **Glass box** | Every attribute row shows its generated text, a "why" card, the Field Manual entry and, for AI-made values, the workflow step and model (AGENTS.md). The text is editable, and editing it follows doc 31 §8.3 region states |
| G4 | **Lossless** | Import followed by save is byte-identical (doc 04 §12.3). Hand edits, unknown keys, legacy aliases and raw number lexemes are kept. No edit rewrites a field the user did not touch; "Normalize as engine" is an explicit command |
| G5 | **Lift is offered, never forced** | Recognisers propose; "replace" only when re-emission reproduces the normalised original; otherwise "wrap" or leave as code (doc 31 §8.2) |
| G6 | **Honest about the engine** | Engine truth is shown inline; unavailable features are greyed out with a reason per profile, answered through doc 33 §4.4 ("why is this greyed out?"); `Cwa199` generators use T1 commands until a probe promotes a T2/T3 command (doc 35 §8.3) |
| G7 | **Typed forms for people and models** | Every slot's valid values come from code: the catalog of the active mod set (doc 27), the world config, the mission's own names. Free text only for names, strings and user code |
| G8 | **Preview, then one undo group** | Every tool shows a semantic diff and a byte diff first; applying is one undo group in the origin's lane (user, Wilco, plugin; doc 34 ed22) |

## 2. The workaround → intent catalogue

Lift: **H** high (recogniser plus exact re-emission), **M** medium (semantics match, form differs: offer "wrap"), **—** nothing to lift (a tool or a preserved value). Profiles: "All" means `Cwa199`, `Cwr` and `Ce`.

| ID | What people did | Intent | Plotroom affordance | Compiles to | Profiles | Lift rule | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WA01 | Deleted (or added) names in `addOns[]`/`addOnsAuto[]` in every section by text editor | Declared dependencies that are true | Dependency doctor with a reason per name (§5) | `addOnsAuto[]` = engine-parity scan; `addOns[]` = parity ∪ reasoned extras ∪ pins, per section (doc 27 §4.5) | All | Existing names kept verbatim; unreasoned names flagged (D2), never auto-removed | F: 74 list addOns; 53 (47 official) carry 103 names absent from `addOnsAuto`; BIKI FAQ ×2; doc 09 P4 [V] |
| WA02 | Typed `year=` into Intel | Historical date, leap years, correct sky | Year in the Date field, with "apply to all four sections" | Intel `year` (read by `InitGeneral`, `P:World/WorldInit.cpp#L242-L268`) | All; `setDate` only for mid-mission jumps on `Cwr`/`Ce` | Shown as a protected hand edit | F: 0 missions [V] |
| WA03 | Typed an off-grid `minute=`; `skipTime` offsets | Exact start time | Minute 0–59, never rounded | Intel `minute` | All | Protected | F: 0; stock dialog rounds on OK [V] |
| WA04 | Typed fractional `resistanceWest/East` | Nuanced relations; civilians apart | Relations panel (§4.3) | Intel keys; `setFriend` block in generated `init.sqs` | Keys: all; `setFriend`: `Cwr`/`Ce` (absent from 1.99 exe) | Protected; never snapped to 0/1 | F: 1 fractional [V]; at runtime the side test is binary: friendly at 0.6 or more, enemy below (`P:AI/AICenterStats.cpp#L1371-L1410`) [V]; any graded effect elsewhere [U] |
| WA05 | Added Intel `viewDistance` (CWR) or `setViewDistance` in `init.sqs` | Per-mission view distance | View distance setting | `Cwr`/`Ce`: Intel `viewDistance` (clamped, `P:UI/Locale/MissionLanguageDetector.cpp#L300-L317`); `Cwa199`: generated `init.sqs` line | Key: `Cwr`/`Ce`; command: all | Top-level `init.sqs` line → H | F: key 0; command 55 [V] |
| WA06 | Wrote `show*` keys in `description.ext`; sqm keys of the same name do nothing | No map, GPS, compass, watch or notepad | HUD items checklist | `description.ext` keys (`P:UI/DisplayUIMenus.cpp#L850-L876`) | All | Ext keys → H; sqm keys flagged "no effect" (PL14), kept | F: sqm `showGPS` 2; ext `showGPS` 17, `showNotepad` 8, others 1–2 [V] |
| WA07 | Typed `position[]` numbers; offsets in init lines | Alignment, spacing, co-location | Numeric X/Z plus align, distribute, face and snap tools (§3.3) | `position[]` x/z, `azimut` | All | — | Undetectable in binarized files [U]; doc 09 S13 [V] |
| WA08 | Typed skill below 0.2, above 1 or exact; `setSkill` | Very weak or elite AI | Numeric skill; "derive from rank" toggle | `skill` key (omitted = rank-derived) | All | Protected; 0 is an error (PL05) | F: 0 out of range [V] |
| WA09 | Set `leader=1` by hand or raised a rank | A chosen unit leads | Leader picker with pin | `leader` key (honoured, `P:AI/AICenterImpl.cpp#L2059-L2070`) | All; `selectLeader` exists on no profile | Protected; PL06 | F: 0 [V] |
| WA10 | Groups-mode drags; edited `markers[]` | Random start among spots | "Start at one of…" (§4.3) | `markers[]`; unit moved onto a marker to exclude its own spot | All | Existing lists shown as the attribute | F: units 32, empties 5 [V] |
| WA11 | Edited `side=`/`vehicle=` in place; placed unlisted classes | Keep all wiring while changing who or what; reach hidden objects | Side swap and class swap (§5); catalog filter "unlisted classes" with a warning | `side`, `vehicle`, group side | All; hidden classes per mod set | — | OFPEC "sqm hacking" threads ~5.6k and ~3k views; doc 09 P5 [V] |
| WA12 | Find-and-replace of class names and addons for another mod | Play or port with another mod | Class remap (§5) | `vehicle`, script literals, cargo, loadouts, gear pool, addOns | All, mod-set aware | — | ~3 OFPEC titles; replacement-pack mods were the popular route [I] |
| WA13 | Renamed the folder suffix, stripped addons, re-placed units | Reuse on another island | Island move, dry run first (§5) | `<name>.<world>` folder; transformed positions; re-resolved object ids | All | — | BIKI FAQ recipe [V]; dry-run machinery shared with doc 34 ed15 |
| WA14 | Deleted `ItemN` blocks, fixed `items=` and ids, merged files | Bulk delete, repair, merge | Import linter, normalise, merge and split (§5) | CST patches; explicit Compact/CheckSynchro semantics | All | Anomalies shown "as the game loads it" | F: 43 of 71 text files hold non-`%f` floats, a sign of other writers [I] |
| WA15 | Unpacked PBOs and debinarized `mission.sqm` to study or fix | Learn from and repair missions | Open PBO and binarized sqm directly; save writes text | text `mission.sqm` | All | — | ~16 OFPEC depbo titles (~37k views); doc 09 P10 [V] |
| WA16 | `setPos [getPos… select 0, … select 1, h]` in init; external position-capture tools | Rooftops, towers, stacked props | Height (§4.3) | Init prefix: surface-relative `setPos` for every mission entity (all are `EntityAI`, T1); `setPosASL` only as an optional absolute form | All; `setPosASL` on `Cwr`/`Ce`, and on `Cwa199` after PP1 | Idiom → H | F: non-zero-height `setPos` 64; O: absolute-height form 10 uses in 6, keep-x/y form 8 in 4; ~36–39 OFPEC roof titles; doc 09 P6 [V] |
| WA17 | `setPos` onto `(object N) buildingPos i`; waypoint house positions | Garrisons inside buildings | Building-position picker (0-based stored, 1-based shown) | Waypoint `idStatic` + `housePos` (native), or init `buildingPos` | All; `buildingPos` on `Cwa199` after PP1 | H | `buildingPos` 0 in official; `housePos` 3 missions (F) [V] |
| WA18 | `this setDammage 1` | Wrecks, bodies, blown bridges | Starts destroyed | Init prefix, last statement | All | H | F: 23 missions (208 fields); O: 147 fields in 20 [V] |
| WA19 | `moveInDriver/Gunner/Commander/Cargo`; crew names `<veh>d/c/g` | Start in a given seat of any vehicle | Starts in: vehicle, seat; crew panel | Special CARGO when unambiguous, else init `moveIn*` | All; object form only | H | O: 151 fields in 42 (79 `moveInCargo`); F crew-name references 39 [V] |
| WA20 | `removeAllWeapons` + `addMagazine` + `addWeapon` chains | Custom kits | Loadout editor from the active catalog | Init prefix | All; classes per mod set | H when the chain is contiguous | O: 299 fields in 76 (709 statements); F 103 [V] |
| WA21 | `clear*Cargo` + `add*Cargo` chains; `set*Cargo` | Stocked crates and supply trucks | Cargo editor with capacity counters | Init prefix; spilled to a generated script over budget | All; `setFuelCargo`/`setRepairCargo` T3 on `Cwa199` (present in the exe, never observed), `setAmmoCargo` T1 | H | O: 385 fields in 67 (2,154 statements); Remastered templates 190 fields in 25; first technical item of the BIKI FAQ [V] |
| WA22 | `this setCaptive true` | Prisoners, undercover, safe actors | Captive | Init prefix | All; boolean form only | H | O: 73 fields in 19 (55 in cutscenes) [V] |
| WA23 | Damage-reset loops and handlers; `allowDammage false` | Protect key characters | Protected | `allowDammage false` on all profiles (T1 on `Cwa199`: used in shipped official content, doc 35 CSV); on `Cwa199` a yellow "1.99 effect unprobed" note until PP6; optional best-effort reset only as a fallback | `Cwr`/`Ce` effect [V]; `Cwa199` effect [U] | `allowDammage false` → H | F: 3 missions, handlers 1; ~21–23 OFPEC titles [V] |
| WA24 | `setUnitPos "UP"/"DOWN"/"AUTO"` | Stance of sentries and snipers | Stance | Init prefix | All; no "middle" in this engine | H | O: 229 fields in 32 [V] |
| WA25 | `setBehaviour`, `setCombatMode`, `setSpeedMode`, `setFormation`, `allowFleeing` in leader inits | Initial group posture without waypoints; never flee | Start posture and Courage | Waypoint-1 fields when a waypoint exists; else leader prefix. `allowFleeing` always init | All | H; M on a non-leader (same group-wide effect [V], but re-emission moves the text to the leader) | O: behaviour 748 fields in 103 (544 in cutscenes); `allowFleeing` 296 in 70 [V] |
| WA26 | `disableAI "MOVE"/"TARGET"/"AUTOTARGET"/"ANIM"`; `stop`/`doStop` | Static sentries, frozen actors | AI switches (irreversible, marked) and Hold | Init prefix | All; `"ANIM"` after PP5 on `Cwa199` | H | O: `disableAI` 92 fields in 2 missions; F `stop`/`doStop` 15 [V] |
| WA27 | Special Flying plus `flyInHeight` | Airborne start at a chosen altitude | Altitude (aircraft only) | Special FLY + init `flyInHeight` | All | H | F: 10 missions (42 fields); FLY 35 [V] |
| WA28 | `setFlagTexture`, `setFlagSide` | Nationality; CTF | Flag picker | Init prefix | All | H | O: 123 fields in 79; C: all 36 Remastered MP templates [V] |
| WA29 | `CfgIdentities` plus `setIdentity`, `setFace`, `setMimic` | A named cast | Cast list and assignment | `CfgIdentities` (mission or campaign) + init | All | H when the class resolves | O: 267 fields in 107 (235 `setIdentity`) [V] |
| WA30 | `switchMove`/`playMove` in init | Seated, wounded, kneeling actors | Pose picker from the unit's move states | Init prefix (+ ANIM switch where available) | All; ANIM as WA26 | H | F: 19 missions (65 fields) [V] |
| WA31 | `name = group this` | Refer to a group | Group name | Init of a member that always exists | All | H | O: 219 fields in 68; S: 164 in 6 [V] |
| WA32 | `group this setGroupId [...]` | Story callsigns | Callsign picker from `CfgWorlds >> GroupNames` and `GroupColors` | Init prefix | All (2-element form) | H | O: 98 fields in 61 [V] |
| WA33 | `inflame true`; `switchLight` | Lit fires; blackouts | Burning, Light | Init prefix | All | H | F: `inflame` 23 missions; `switchLight` 0 in mission fields, but 8 uses in 2 official script files, so T1 (doc 35 CSV) [V] |
| WA34 | `lock true/false`; the Lock combo | Keep players out | Lock with honest labels | `lock` key; runtime `lock true` | All | — | C: `lock` in 10 official folders [V] |
| WA35 | Far-parking plus `setPos`; empty-group placeholder (`x = group this` then `deleteVehicle this`); HOLD plus SWITCH trigger | Reinforcements; surprise | "Appears when…" (doc 31 Reinforcements) | Held synced waypoint (native); `createUnit` into a placeholder; `createGroup` on `Cwr`/`Ce` | All; `createGroup` `Cwr`/`Ce` | M | S: placeholder 117 fields in 5 of 9; ~44 OFPEC "appear" titles [V] |
| WA36 | Empty-type icon markers as named points; `setMarkerType`/`setMarkerPos` reveals | Invisible anchors; objectives that appear | Anchor points; "Revealed when…" | Empty markers; type swap in an activation that runs on every machine | All; `createMarker` `Cwr`/`Ce` | Anchors H; reveal chains M | O: 487 hidden markers in 77; F reveals 22 [V counts; I purpose] |
| WA37 | Show IDs plus `object N` in fields; `nearestObject` | Pre-destroyed towns, bridge objectives | Map-object actions (§6) | `object N` statements in a compiler-owned block; `idStatic` | All | H | F: ids in fields 2, scripts 4; waypoint `idStatic` 6 [V] |
| WA38 | `respawn` keys plus `respawn_*` marker names | MP respawn | Respawn attribute and spawn points (doc 31) | Ext keys plus generated markers | All; SIDE behaves as GROUP | H | F: 75 ext files; top OFPEC thread ~49k views [V] |
| WA39 | Hand-written lobby params, load texts, scores, `debriefing`, `disabledAI`, `aiKills`, gear pool | Mission settings | Mission settings panel; gear-pool editor | `description.ext` keys and classes | All; `joinInProgress`, `CfgRemoteExec`: `Cwr`/`Ce` | H | F: `onLoadMission` 218, scores 131, params 59, gear pool 41 [V] |
| WA40 | Hand-written `CfgSounds`, `CfgRadio`, `CfgSFX`, `CfgEnvSounds`, `CfgMusic` | Voices, music, ambience | Audio library (docs 31, 32; doc 34 ed20) | `description.ext` classes | All | H | F: `CfgSounds` 204, `CfgRadio` 187, `CfgSFX` 177, `CfgMusic` 2 [V] |
| WA41 | Hand-written `briefing.html`, `OBJ_n`, `objStatus` | Briefing and objectives | Briefing editor bound to Objective entities (doc 31) | `briefing.html` + `objStatus` | All; localized files `Cwr`/`Ce` | H | F: briefings 212; O: `objStatus` 368 fields in 96 [V] |
| WA42 | Hand-edited `stringtable.csv` and `$STR_` keys | Localisation | String-table grid with key refactoring | CSV bytes preserved | All; UTF-8 files `Cwr`/`Ce` | — | F: 268 missions [V] |
| WA43 | Files with magic names | Start, end, death and respawn logic | Mission events panel, compiler-merged (doc 31 §4.5) | `init.sqs`, `exit.sqs`, `onPlayerKilled.sqs`… | Per hook | — | F: `init.sqs` 186, `exit.sqs` 19 [V] |
| WA44 | `init.sqs` lines: `setViewDistance`, `enableRadio`, `setAccTime`, `showCinemaBorder`, `setTerrainGrid`, weather changes | Mission-wide presentation | Mission settings; weather timeline | Generated `init.sqs` block | All | Top-level lines → H | F: `enableRadio false` 171, `setAccTime` 146 [V] |
| WA45 | A Game Logic named `server` plus `local server`; manual SP↔MP rework | Run once on the server; reuse a mission | Compiler-owned server guard; SP↔MP wizard (§5) | Logic and guards; ext keys | All; `isServer` T3 on `Cwa199` | M | OFPEC MP tutorial 4,376 downloads; ~22 conversion titles [V] |
| WA46 | Zero-area triggers, flags and counters | Event logic | Rules and typed variables (doc 31 rung 3; doc 34 ed02) | Triggers and flags | All | M | F: zero-area triggers 201; O: flag fields 1,857 in 168 [V] |
| WA47 | `cadetMode`/`benchmark` in presence conditions | Scale by difficulty or performance | Difficulty chip (doc 34 ed05); performance tier [U] | `presenceCondition` | All; `benchmark` T2 (doc 35 §8.3 table; its rc28 row says T3, so doc 35 is inconsistent) | H | S: `benchmark` 87 fields in 2; O: `cadetMode` 3 fields, `benchmark` 0 [V] |

## 3. The advanced property inspector

### 3.1 What it is

A panel that lists **every** key of the selected entities, as the file and the engine see them: value (raw lexeme kept), state, exposure in the stock editor, what the engine does with it, and the profile. Attributes (§4) are the friendly layer on top; the inspector is the truthful layer underneath. Easy mode shows attributes only; Advanced shows both. So that "every key" does not become a wall of rows, Advanced opens filtered to keys with something to say (written, protected, generated or flagged), and "Show all keys" adds the defaulted and dead ones [I]. Engine notes are doc 33 registry facts, so the inspector, the card and the manual cannot disagree; the inspector keeps no note text of its own.

### 3.2 Exposure and engine truth

| Key | Stock exposure | What the engine does | Inspector behaviour |
| --- | --- | --- | --- |
| `position[1]` (Y) on units, empty vehicles, triggers | Written from the surface on insert and move | Ignored: re-snapped to the road or terrain surface at start (`P:AI/AICenterImpl.cpp#L985`, `#L1098-L1104`, `#L1248-L1249`; sound sources and mines too, `#L887`, `#L931`) [V]. The 2-D road-surface query has no height ceiling, so a soldier or trigger lands on the **highest** walkable (roadway) face of any object at that x/z, such as a bridge deck or a walkable roof, else on the terrain; vehicles and static objects land on the terrain (`P:World/Terrain/Landscape.cpp#L1655-L1773`) [V code path; which island models have roof roadways is U] | Read-only "surface", computed with the same rule where model roadway data is known; the Height attribute instead (PL01) |
| `position[0,2]` | Mouse only | Honoured, then marker choice, placement radius and formation (`P:AI/AICenterImpl.cpp#L965-L987`, `#L2142-L2186`) [V] | Numeric, with snapping tools |
| `azimut` | Float edit box; the compass click rounds to 5°; Shift-drag adds unbounded deltas (doc 03 §4.3–§4.4) [V] | Honoured | Kept as written: O has 1,616 units in 83 missions outside [0, 360) [V] |
| `health` | 0–1 slider | Damage = 1 − max(0.03, health), so 0 gives a live 97%-damaged object (`P:AI/AICenterImpl.cpp#L853`, `#L1021`) [V] | Note plus "Starts destroyed" (PL02) |
| `skill` | 0.2–1.0 slider that clamps on open and writes the clamped value on OK (`P:UI/Map/UIArcade.cpp#L949-L956`, `#L1178-L1182`) | Not clamped; stored with its inverse, so 0 gives an infinite inverse; a negative value, like an absent key, means rank-derived (`P:AI/ArcadeTemplate.cpp#L384`, `#L403-L406`); ignored for players and under Super AI; crews share the vehicle's value (`P:AI/AIUnit.cpp#L1366-L1380`; `P:AI/AICenterImpl.cpp#L1651`, `#L1689`, `#L1721`) [V] | Numeric; warning outside [0.2, 1], error at 0 (PL05); "derive from rank" omits the key |
| `presence`, `presenceCondition` | Slider, checked expression | Evaluated only for non-playable units and empties, while the world is built, before any init line (`P:AI/AICenterImpl.cpp#L1528-L1538`; empties `#L1402-L1407`; init lines run later, `P:World/WorldInit.cpp#L622-L627`) [V] | Greyed on playable units with the reason (PL03) |
| `special` | Combo | FORM re-places non-leaders (the leader stays); CARGO soldiers are created in a second pass, after the rest of the group, and seated in the first group vehicle, in unit order, with free cargo space, else left standing; in MP an unoccupied playable CARGO slot is not created; FLY for aircraft only (`P:AI/AICenterImpl.cpp#L2142-L2186`, `#L1936-L1964`, `#L1569-L1600`, `#L1115-L1133`) [V] | Explained inline; interacts with Height and Seat |
| `leader` | Computed: highest rank, on group edits only (`P:AI/ArcadeTemplate.cpp#L1542-L1561`) | Honoured even for a lower rank [V] | Leader attribute; PL06 |
| `markers[]` | Groups-mode drag only | Uniform over n + 1 options including the placed spot; names matched case-insensitively; only a FORM group's leader's links count (`P:AI/AICenterImpl.cpp#L965-L986`) [V] | Start-at attribute |
| `lock` (legacy `locked`) | Combo, three states | Scripts can only set LOCKED or DEFAULT (`P:Game/Commands/GameStateExtUi.cpp#L2330-L2345`) [V] | Honest labels (PL09) |
| Unit `id`, sync ids | Hidden | Renumbered on every engine load and save (Compact, CheckSynchro; doc 04 §3.9) [V] | "File id (unstable)"; identity lives in the sidecar (doc 34 ed16) |
| Intel `year` | None; the dialog only sizes the Day combo with it | Used for the calendar and the sky [V] | Date field |
| Intel `minute` | 5-minute combo opened at the nearest step; OK writes 5 × selection (`P:UI/Map/UIArcadeWaypoint.cpp#L664-L675`, `#L772-L776`) [V]; minutes 58–59 round to a 13th entry that does not exist (outcome unverified) | Honoured (plus 0.5 s, `P:World/WorldInit.cpp#L261`) [V] | 0–59, never rounded |
| Intel `resistanceWest/East` (legacy `resistance`) | Four-way toolbox that reads the value at a 0.5 threshold; OK forces 0 or 1 (`P:UI/Map/UIArcadeWaypoint.cpp#L676-L699`, `#L777-L799`) [V] | Friend if the value is 0.6 or more, enemy below (`P:AI/AICenterStats.cpp#L1371-L1410`), so 0.5–0.59 shows as friendly in the stock dialog but fights as an enemy; the civilian centre copies Resistance's values (`P:AI/AICenterImpl.cpp#L1745-L1768`) [V] | Relations panel; warns in the 0.5–0.6 band |
| Intel `viewDistance` (`Cwr`/`Ce`) | None | Read raw from the `Mission` section's Intel only (alias `missionViewDistance`), clamped to the user's range, and applied only while the player's "respect mission view distance" option is on (default on); dropped by a vanilla re-save (`P:UI/Locale/MissionLanguageDetector.cpp#L300-L317`; `P:UI/Settings/GameSettingsConfig.hpp#L22`) [V] | View distance setting; CST keeps the key |
| Section `addOns[]`, `addOnsAuto[]` | None | `addOns[]` checked per section, one unknown name fails the load; `addOnsAuto[]` never read (`P:AI/ArcadeTemplate.cpp#L1910-L1967`) [V]. On save, names in the *in-memory* auto list from the previous save that the new scan no longer finds are deleted from `addOns[]`; `Clear()` does not reset that list and loading does not read it, so after loading another mission in the same editor display it can hold that other mission's names (`P:AI/ArcadeTemplateFind.cpp#L184-L203`; `P:UI/Map/UIMapExtDisplay.cpp#L99-L133`) [V code; practical effect I] | Dependency doctor |
| Section `randomSeed` | None | Its only use is seeding licence plates, hashed with the vehicle id (`P:AI/ArcadeTemplate.cpp#L1567-L1580`; `P:AI/AICenterImpl.cpp#L1206-L1241`) [V] | Read-only, "reroll" action |
| Section `showHUD` … `showGPS` | None | No runtime reader (doc 04 §3.1) [V] | "No effect" (PL14) |
| Waypoint `idStatic`/`housePos`; trigger `idStatic`/`idVehicle` | Double-click and drag gestures; `housePos` only for buildings with positions | `idStatic` is not remapped by Compact [V] | Map-object and building-position pickers (§6) |
| Intro, OutroWin, OutroLoose | Section combo hidden in Easy mode | Full templates, each with its own Intel [V] | Always visible (doc 32) |
| Legacy tokens (`WIN`, `PLAY`, `locked`, `show`, `resistance`, `playerOnly`) | Read | Normalised by a vanilla re-save [V] | Raw token shown and kept |

### 3.3 Editing

- **Exact numbers** with units (m, °, s): X/Z, height (through the Height attribute), azimuth, placement radius, trigger axes, timers, date and time, skill, friendliness.
- **Permissive on values, strict on structure** (AGENTS.md parser rules): a value the engine accepts is accepted and annotated with its consequence; only structural errors block an apply.
- **Multi-select.** Shared keys show one value or "mixed". Operations: set; offset (+/−); scale around the selection's centroid; randomise within a range (the editor draws once, so the file gets literal values and the result is reproducible); distribute evenly along a line; align to a line; face a point; snap to grid or to road (road points from the WRP and model data, doc 07) [I]; copy attributes from one entity to many. One undo group per operation (G8).
- **No destructive round trips.** Plotroom's dialogs and inspector patch only the key the user changed; opening and closing a dialog writes nothing.

```rust
// ── Inspector model (proposal-only) ────────────────────────────────────
pub enum Exposure {
    Dialog { advanced_only: bool },            // a stock dialog field; some are hidden in Easy mode
    Gesture(StockGesture),                     // Groups-mode drag, double-click binding, Sync mode
    Computed,                                  // e.g. `leader`, recomputed by the stock editor
    Hidden,                                    // no stock UI at all (`year`, `randomSeed`, `addOns[]`)
    DeadKey,                                   // serialized but never read at runtime (`showGPS` in sqm)
    ProfileExtra(ProfileSet),                  // e.g. Intel `viewDistance`: `Cwr`/`Ce` only
}
pub enum DialogEffect { RoundsTo { step: u8 }, ClampsTo { min: f32, max: f32 }, SnapsAt { threshold: f32 } }
pub enum ValueState {
    Defaulted,                                 // key absent; the engine default applies
    Written,                                   // present; raw lexeme kept by the CST
    ProtectedHandEdit { stock_dialog: DialogEffect }, // the stock dialog would change it on OK
    Generated(RegionId),                       // owned by an attribute or module (doc 31 §8.3)
    UnknownToken(RawToken),                    // `Other(raw)`: the engine skips or rejects it
}
pub struct InspectorRow { pub key: FieldKey, pub state: ValueState, pub exposure: Exposure, pub notes: Vec<ConceptId> } // doc 33 entries; no second note store
```

## 4. Intent attributes

### 4.1 Contract

An attribute is a typed value on an existing entity with: applicability (entity kinds), availability per profile, a lowering, a recogniser for lift (§8), engine notes and a link to its Field Manual entry (doc 33). Placing, changing or removing one is a single undoable command.

- **Lowering order (G2).** (1) A native field the stock dialog already has (Special CARGO or FLY, waypoint-1 posture fields, `lock`, `markers[]`, `idStatic`/`housePos`, `health`). (2) A key the stock dialog hides (`year`, `leader`). (3) A generated init prefix: doc 31 §3 records its span and hash in the sidecar, and hand-written text after it stays user code. (4) A lossless `description.ext`, briefing or stringtable patch. (5) A compiler-owned `init.sqs` block or script file (doc 31 §4.5).
- **Fixed prefix order,** so output is deterministic: identity → loadout → cargo → state (captive, protection) → AI (stance, switches, hold, courage, posture, altitude) → seat → position → pose → destroyed. Destruction goes last so everything else applies before the object dies [I]. Two pairs are refused by construction because the order cannot rescue them: Protected with Starts destroyed (while `allowDammage false` is set, `setDammage` cannot raise damage on `Cwr`/`Ce`, `P:AI/VehicleAICombat.cpp#L365-L370` [V]), and Seat with Height on one soldier (`setPos`/`setPosASL` dismount him, §10 (d)). Cargo and Captive before Destroyed matter too: both commands do nothing on a destroyed object (`P:Game/Commands/GameStateExtObj.cpp#L297-L374`, `#L631-L641`) [V].
- **Field budget.** A text value over 2047 bytes is silently truncated on parse (doc 04 §2.1) [V]. When the prefix plus the user's text would pass a safety margin below that, long cargo and loadout lists spill into a generated script `exec`'d from the prefix. Its first step runs before `init.sqs` (doc 31 §3) [V]; the spill is shown in the diff (PL08).
- **Checker and policy.** The prefix passes the evaluator's check-only mode (statements that return nothing) and the doc 24 risk policy, per profile (doc 23 catalog).
- **Multiplayer.** Init lines probably run on every machine: the server sends them to clients (`P:World/WorldInit.cpp#L665-L671`) [V code; I effect]. Each attribute therefore declares a locality class from the doc 23 catalog: *owner-only* (e.g. `moveIn*`, a no-op unless the soldier is local [V]), *local effect needed everywhere* (identity, marker changes), or *global effect, maybe duplicated* (cargo, loadout: [U], PP7).
- **User code after a prefix wins.** If the user's own text later overrides an attribute (a `setPos` after Height), lint PL07 says so; nothing is rewritten.
- **Companion edits are visible and reversible [I].** When an attribute changes another field by construction (Special NONE for Height, a new vehicle name for Starts in, the unit moved onto a marker by Start at one of), the preview and the why card list that change. Removing the attribute restores the old value only if nobody has edited the field since; otherwise it asks.
- **No duplicates [I].** If the field's own code already does what a new attribute would (adding Captive where `setCaptive true` is typed), the §8 recogniser runs first and offers the lift instead of prepending a second statement.

### 4.2 Type sketch (crate `ofp-attributes`; proposal-only)

```rust
// ── ofp-attributes: typed intents that lower to vanilla fields and init prefixes ──
/// Building-position index as the engine stores it (0-based); the UI shows it 1-based,
/// matching the in-game "House position N" label. Out-of-range indices are refused at
/// construction, because the engine returns [0,0,0] for them and teleports the unit.
pub struct BuildingPosIndex(u16);
pub struct Metres(f32);                          // finite; validated on construction
pub enum Seat { Driver, Gunner, Commander, Cargo } // no cargo index: only the object form exists
pub enum HeightSpec {
    AboveSurface(Metres),                        // any mission entity (all are EntityAI): surface-relative `setPos`, T1
    AboveSeaLevel(Metres),                       // `setPosASL`: Cwr/Ce; Cwa199 after probe PP1
    OnRoof { building: MapObjectRef, offset: Metres }, // stores the pick, not the number: the
                                                 // absolute height is recomputed at lowering, so a
                                                 // drag or a re-resolved building never leaves a
                                                 // stale height [I]
    OnBuildingPosition { building: MapObjectRef, index: BuildingPosIndex },
}
pub enum Strip { Keep, AllWeapons, Listed(Vec<ClassName>) }
pub struct Loadout { pub strip: Strip, pub magazines: Vec<(ClassName, Count)>, pub weapons: Vec<ClassName>, pub select: Option<ClassName> }
pub struct CargoContents { pub clear: ClearMode, pub weapons: Vec<(ClassName, Count)>, pub magazines: Vec<(ClassName, Count)> }
pub enum Protection { Off, EngineFlag, BestEffortReset }
pub enum Stance { Up, Down, Auto }               // the engine's enum; no "middle"
pub enum AiSwitch { Move, Target, AutoTarget, Anim }
pub struct Courage(f32);                          // 0..=1; lowers to allowFleeing (1 - courage)
pub enum Attribute {
    Seat { vehicle: EntityRef, seat: Seat }, Height(HeightSpec), Destroyed,
    Loadout(Loadout), Cargo(CargoContents), Captive, Protection(Protection),
    Stance(Stance), Hold, AiSwitches(EnumSet<AiSwitch>), Altitude(Metres),
    StartPosture(Posture), Courage(Courage), Leader, StartAt(Vec<MarkerRef>),
    Flag(FlagSpec), Cast(CastId), Pose(MoveName), Burning, Light(LightState),
    GroupName(VarName), Callsign(CallsignPair), AppearsWhen(RuleRef),
}
/// Ordered slots keep the generated prefix deterministic (derive Ord).
pub enum PrefixSlot { Identity, Loadout, Cargo, State, Ai, Seat, Position, Pose, Destroyed }
pub enum Lowering {
    NativeField { key: FieldKey, value: FieldValue },
    InitPrefix { host: EntityRef, slot: PrefixSlot, text: Statement },
    ExtPatch(ExtEdit), InitSqsBlock(Statement), ScriptFile { path: MissionPath, text: Script },
}
pub enum Availability { Ready, Fallback { reason: &'static str }, NeedsProbe(ProbeId), Unavailable { reason: &'static str } }
pub trait IntentAttribute {
    fn availability(&self, target: Profile, entity: &EntityView<'_>) -> Availability;
    fn lower(&self, ctx: &LowerCtx<'_>) -> Result<Vec<Lowering>, Error>;
}
```

### 4.3 The attributes

| Attribute | Applies to | Lowers to | Rules enforced by construction | Profiles |
| --- | --- | --- | --- | --- |
| **Starts in** | Soldier | Special CARGO when the target is the only vehicle of his own group with cargo space; otherwise `this moveIn<Seat> <vehicle>` (on `Cwa199` also `assignAs<Seat>` until PP4 shows it is redundant) | An unnamed vehicle gets a name, shown in the diff. Seat capacity from the vehicle's config. A soldier already seated elsewhere is refused. No cargo index exists (`GSE#L1316-L1319`) [V]. `moveIn*` assigns and orders get-in itself in CWR (`P:Game/Commands/GameStateExtUi.cpp#L2624-L2851`) [V]. The 12-seat group check counts placed crew seats, not moved-in soldiers [I], so the real headcount is shown | All |
| **Crew panel** | Crewed vehicle | Read-only rows for the automatic crew: names `<vehicle>d`, `c`, `g`, class from the vehicle's config, ranks derived from the vehicle's, shared skill (`P:AI/AICenterImpl.cpp#L1631-L1722`) [V `Cwr`/`Ce`]. "Make crew explicit" turns the vehicle Empty and seats placed soldiers named `<vehicle>d/c/g` with Starts in | References keep working [I: no name collision, because an Empty vehicle has no automatic crew]. Renaming the vehicle renames the crew references (§5). Unnamed vehicles have no crew variables [V] | All (1.99 lineage [U]) |
| **Height** | Unit, vehicle, object | Every entity placed in `mission.sqm` is created as an `EntityAI` (`P:AI/AICenterImpl.cpp#L947-L997`; `P:World/World.hpp#L716-L718`), so one lowering serves units, vehicles and objects on all profiles: `this setPos [getPos this select 0, getPos this select 1, h]`, surface-relative, with the model offset applied by the engine's own place-on-surface step (`P:Game/Commands/GameStateExtGrp.cpp#L1696-L1730`; `P:World/Simulation/Simul.cpp#L1252-L1301`) [V]. `setPos` measures `h` from the highest walkable (roadway) face whose world height is at or below `h` itself (plus 0.5 m for soldiers) read as an *absolute* height, else from the terrain (`P:World/Entities/Infantry/SoldierOldSim.cpp#L215-L226`; `P:World/Terrain/Landscape.cpp#L1775-L1930`) [V code path], while `getPos` measures from the walkable face or terrain below the object's current position (`#L1532-L1550`), so the two are not inverses: on high ground the `setPos` reference is the terrain, but on low-lying ground a floor or roof below that level becomes the reference and the object ends up higher than asked, so the compiler corrects `h` where model roadway data is known and badges it otherwise (PP2). `setPosASL` (no surface term, origin placed at the given point) is an optional absolute form on `Cwr`/`Ce`, and on `Cwa199` after PP1 | Forces Special NONE on formation members (formation re-placement precedes init lines [V], so the `getPos` form would use the slot). Warns when an ASL height meets a placement radius or `markers[]`. Suggests Hold. The badge shows the absolute height. A roof or building-position pick is stored as the pick and recomputed when the entity is dragged, and flagged if the drag leaves the building's footprint; a typed ASL number is kept as typed and warns once the entity leaves the spot it was measured at [I]. A soldier placed over a model whose top walkable face is where he should stand (a bridge deck, a walkable roof) already starts there without any code (§3.2 `position[1]`), so the form offers "no code needed" first when model roadway data shows it [V code path]. Whether a soldier set above a face that is not walkable stays there is [U] (PP2). (The `setPos` branch that adds the model's lowest geometry point with no surface term applies only to non-`EntityAI` objects, which `mission.sqm` cannot place.) | All (`setPos` is T1); ASL form per PP1 |
| **Building position** | Soldier | "Go there": waypoint `idStatic` + `housePos` (native). "Start there": `this setPos ((object N) buildingPos i)` | The index is checked against the building's position count; beyond it the engine returns [0,0,0] (`P:Game/Commands/GameStateExtUi.cpp#L447-L473`) [V]. Positions come from model path data (§6) [I] | All; `buildingPos` T3 on `Cwa199` |
| **Starts destroyed** | Any | `this setDammage 1`, last slot | Health below 0.03 cannot make a wreck [V]. Refused together with Protected, which would silently cancel it on `Cwr`/`Ce` [V] (§4.1). Destroying a crewed vehicle kills its crew and trips `!alive` conditions at start [I]: shown in the note | All (`setDammage` spelling) |
| **Loadout** | Soldier | `removeAllWeapons this` or listed removes; magazines; weapons; `selectWeapon` | Magazines first: harmless everywhere, irrelevant on `Cwr`/`Ce` where each call reloads (`P:Game/Commands/GameStateExtObj.cpp#L1212-L1259`) [V], 1.99 [U] (PP3). A magazine with no free slot is refused silently [V], so slots are counted. On a soldier, `removeAllWeapons` removes every weapon and magazine, binoculars and night vision included, then re-adds only the built-in throw, put and fist weapons (`P:World/Entities/Infantry/SoldierOldSim.cpp#L943-L959`) [V], shown in the before/after; on a vehicle it removes only magazines (`P:AI/VehicleAI.cpp#L1972-L1975`) [V]. Classes come from the active mod set and feed doc 27's reasons | All |
| **Cargo** | Vehicle, crate | `clearWeaponCargo`/`clearMagazineCargo`, then `addWeaponCargo`/`addMagazineCargo [class, n]`; `set{Ammo,Fuel,Repair}Cargo` for service vehicles | Silent refusals (destroyed or non-supply container, bad argument shape, unknown class, `GameStateExtObj.cpp#L297-L374`) are impossible by construction [V]. Capacity counters [I]. Spill to a script over budget | All; on `Cwa199` `setFuelCargo`/`setRepairCargo` are T3 (probe first), the rest T1 |
| **Captive** | Unit | `this setCaptive true` | Boolean form only (`GSE#L1220`) [V]. Note: a captive still fires and is still watched [I] | All |
| **Protected** | Unit, vehicle, object | `this allowDammage false` on every profile. On `Cwr`/`Ce` the flag blocks hit damage and any `setDammage` that raises damage (`P:AI/VehicleAICombat.cpp#L74-L79`, `#L117-L122`, `#L365-L370`) [V]. On `Cwa199` the command is T1 (used in shipped official content), so it is offered with a yellow "1.99 effect unprobed" note until PP6; the opt-in best-effort reset handler is only a fallback if PP6 shows no effect | Refused together with Starts destroyed (§4.1). The fallback reset cannot stop one-shot kills and does not block scripted damage [I] | All; `Cwa199` effect [U] |
| **Stance** | Soldier | `this setUnitPos "UP"`, `"DOWN"` or `"AUTO"` | Enum only; unknown strings would be silent no-ops [V]. No effect on a human player [I] | All |
| **Hold** | Unit | `doStop this` | Reversible by later orders [I]. Paired with Special NONE, or FORM moves the unit first | All |
| **AI switches** | Unit | `this disableAI "<switch>"` per switch | Irreversible: flags are OR-ed and no `enableAI` exists (`GameStateExtUi.cpp#L2378-L2405`) [V]; the row says so. Applies to the vehicle's commander unit [V] | All; `"ANIM"` on `Cwa199` after PP5 |
| **Altitude** | Aircraft | Special FLY + `this flyInHeight h` | FLY is greyed for non-aircraft. The start altitude is the vehicle's own until the AI adjusts [I] | All |
| **Start posture** | Group | Waypoint-1 fields when the group has a waypoint (applied at start, `P:AI/AICenterImpl.cpp#L2110-L2140`) [V]; otherwise the leader's prefix with `setBehaviour`, `setCombatMode`, `setSpeedMode`, `setFormation` | The row says "applies at start, not on arrival" [V]. All four setters accept a unit or a group and act on the unit's group: `setBehaviour` sets the group's combat mode, `setCombatMode` the group semaphore (sent to every member), `setFormation` and `setSpeedMode` the main subgroup (`GSE#L1299-L1304`; `P:Game/Commands/GameStateExtGrp.cpp#L171-L191`, `#L228-L315`) [V `Cwr`/`Ce`; 1.99 U]. Unknown enum strings are silent no-ops [V] | All |
| **Courage** | Group | Leader prefix `this allowFleeing x`, x = 1 − courage | Without it, courage is the leader's skill, shown as the default; the command acts on the whole group; a group flees when its strength falls below (1 − courage) × its maximum while the leader lives (`P:AI/AIGroupImplHealth.cpp#L1566-L1578`; `P:AI/AIGroup.cpp#L1229-L1239`) [V] | All |
| **Leader** | Group | `leader=1` on the chosen unit | A vanilla re-edit of the group resets it (PL06); "also make highest rank" is offered | All |
| **Start at one of** | Unit, empty, sound source | `markers[]`; "exclude the placed spot" moves the unit onto the first chosen marker and links the rest | Each option has probability 1/(n + 1) [V], drawn as spokes with labels. Greyed on FORM non-leaders [V]. Marker renames update links (§5) | All |
| **Appears when** | Group | Doc 31 Reinforcements: a held synced waypoint (native), `createUnit` into a placeholder group, or `createGroup` on `Cwr`/`Ce` | Presence conditions cannot see init-line variables [V]. Far-parking is discouraged: the group still simulates and counts toward the 63-group cap [I] | All; `createGroup` `Cwr`/`Ce` |
| **Flag** | Flag pole | `this setFlagTexture "<path>"`; `this setFlagSide <side>` | Side only on flag carriers [V]. The picker lists stock flag textures and mission images; imports are normalised to a non-progressive 128×256 JPG (BIKI FAQ) [V-ext] | All |
| **Cast member** | Soldier | A `CfgIdentities` class (mission, or campaign for campaign missions) + `this setIdentity "<class>"` | Lookup is mission then campaign only, never global (`GameStateExtUi.cpp#L184-L235`) [V]; a mission copied out of its campaign loses its cast (PL13). The command reads `name`, `face`, `glasses`, `speaker` and `pitch` from the class, so the generated class writes all five (`GameStateExtUi.cpp#L218-L224`) [V]. The effect is local (no network message) [V], so it relies on init lines running everywhere [I]. In MP the joining player's own identity is applied when the unit is created (`P:AI/AICenterImpl.cpp#L1975-L2009`) [V]; an init-line `setIdentity` runs later and would replace it on each machine that runs it [I from V order], so Cast on playable units is warned | All |
| **Pose** | Soldier | `this switchMove "<state>"` (+ ANIM switch where available) | States listed from the unit's `Moves` config (doc 31 §3) [V]; the AI leaves the pose unless ANIM is disabled | All; ANIM as above |
| **Group name** | Group | `<name> = group this` on a member with presence 1 and no condition; if none exists, on every member (idempotent) | An absent unit never sets it [V]; renames refactor references | All |
| **Callsign** | Group | `group this setGroupId ["<letter>", "<colour>"]` | Values are class names from the global `CfgWorlds >> GroupNames` and `CfgWorlds >> GroupColors`; an unknown name is a silent no-op, and if another group already has the resulting callsign the two swap names (`P:Game/Commands/GameStateExtGrp.cpp#L979-L1022`; `P:AI/AIGroupImplHealth.cpp#L1398-L1435`) [V]; the picture form only on `Cwr`/`Ce` [I] | All |
| **Burning, Light** | Fireplace, lamp | `this inflame true`; `this switchLight "OFF"` | Offered only on classes that support them: `inflame` acts only on fireplace objects and `switchLight` only on street lamps; an unknown light state becomes AUTO, not a no-op (`GameStateExtUi.cpp#L627-L657`) [V] | All (both T1) |
| **Relations, Date, View distance, HUD items** | Mission | Intel keys, `description.ext` keys, generated `init.sqs` block (WA02–WA06) | Relations keep the stock four choices for Resistance ↔ West and ↔ East; an exact value per pair is one click away, marked with the engine's 0.6 friend/enemy threshold [V] and the stock dialog's 0.5 reading threshold, with a warning in the 0.5–0.6 band, and "any graded effect unverified" (PP11), so no control suggests graded hostility the engine does not have; civilians as a linked row; other pairs through `setFriend` on `Cwr`/`Ce` only | Per row |

### 4.4 Finding, seeing and reusing attributes [I]

A typed init line was at least visible in one place. Attributes must be quicker to find than typing the command and easier to see than reading the field, or users will keep typing.

- **Found where the intent starts.** The unit, vehicle and group dialogs and the side panel have an Attributes section whose "+ Add" searches by goal ("on the roof", "starts in the truck", "can't be killed"), the same intent search as doc 31 §4.1 and the doc 34 le18 command palette. Right-click on the map offers the common verbs (Put in vehicle…, Raise…, Garrison building…, Destroy at start, Make captive). Drops cover the most common intents without changing any stock gesture: a plain drag still moves (and Groups-mode drags still link) exactly as in doc 03 §4.3, but when soldiers are dropped on a vehicle or a building, a small chip offers a seat menu with free capacity or the building's positions. Ignoring the chip keeps the plain move; accepting replaces the move with the attribute in the same undo group. Attributes that do not fit the selection or profile stay listed but greyed, with their reason (G6), never hidden.
- **Same picks as Wilco.** Each form offers the menus code computes for §9. Height, for example, offers "roof", a known building position, "click on the map" or exact metres, and shows the resulting absolute height.
- **Seen on the map.** An Attributes overlay draws a small glyph on each icon (seat, height in metres, wreck, captive, protected, AI switches); hovering lists the attributes with their generated text (G3). Init-line state was invisible on the stock map; this is the "see" half of the glass-box rule.
- **Presets and kits.** Doc 31 §3 presets are named bundles of these attributes, never code: for example "roof sniper" (Height, Special NONE, Hold, Stance Down), "prisoner" (Captive, Hold, a seated Pose) or "wreck" (Starts destroyed). Kits are named loadouts and cargo lists, so thirty riflemen do not mean thirty loadout forms. Applying a preset or kit to a selection copies its values into ordinary attribute rows as one undo group, and each row remembers its preset as provenance. Later edits to a preset never propagate silently: "update from preset" shows a diff first. "Save as preset" works from any unit, and "Vary" picks among the kits of one family per selected unit, drawn once so the file holds literal values (§3.3). Presets ship as T0 data (doc 22 §2.1).
- **The sidecar is a convenience, not a dependency.** Every generated prefix is itself a High-confidence idiom (PAT3), so a mission whose sidecar was lost gets its attributes back as lift offers on the next open (§8); only provenance (origin, preset) is lost (PAT16).

## 5. Power tools

Every tool runs as a dry run first: it builds a `ChangeSet` of typed editor commands, shows a semantic diff ("12 units change class; 3 script literals updated; 2 references unresolved") and a byte diff per file, and applies as one undo group (G8). Nothing is written before the user accepts.

| Tool | Replaces | What it does | Report and guarantees | Profiles |
| --- | --- | --- | --- | --- |
| **Class remap** | Find-and-replace of class names; mod switches (WA12) | An equivalence table from → to, proposed by code from the catalog (side, `vehicleClass`, simulation, crew seats, cargo capacity; weapon and magazine families) and edited by the user. It covers unit and empty classes, script literals the language service resolves (doc 23), loadout and cargo attributes, the gear pool and `addOns[]`. Tables are shareable T0 data (doc 22) [I] | Unresolved classes listed; the 12-seat group limit and seat capacities rechecked [V limits, doc 04 §3.9]; dependencies recomputed (doc 27). Edits inside hand-written init text and scripts are grouped per file in the preview and can be excluded, because a literal there may be deliberate [I] | Mod-set aware |
| **Island move** | Folder-suffix renames and hand re-placement (WA13) | Transform: same coordinates (variant islands), a similarity transform from 2+ picked point pairs, or per-cluster moves. Each entity is checked for water, off-map and building footprints (WRP heights and objects, model boxes) [I]. Object ids and `idStatic` are re-resolved by model and nearby position, else marked invalid. Folder renamed to `<name>.<world>` | Fidelity report and rollback snapshot, reusing the machinery of doc 34 §2.4's "Retarget…"; that name stays reserved for changing the target profile, so the two commands are never confused [I]; nothing silently dropped | All |
| **SP ↔ MP wizard** | Manual conversion (WA45) | Steps: slots (SP needs one player, doc 04 §3.9 [V]); respawn and lobby settings; a locality audit of every init field and script (doc 23 catalog; init lines probably run everywhere [I]); `player` references in init lines; a compiler-owned server guard that also works in SP (doc 31 §4.5); target folder. The reverse picks the player slot and replaces `param1`/`param2` with their defaults | Each step previews; one undo group at Finish | All; `isServer` T3 on `Cwa199` |
| **Side swap** | Hand edits of `side=` (WA11) | Changes the side of selected groups while keeping waypoints, triggers and syncs (the stock unit dialog disables Side when editing, doc 03 §4.4 [V]); remaps classes through the class-remap table; updates group side | Lists side-dependent triggers (present, detected by, guarded by), relations and voices affected | All |
| **Bulk edit** | Repetitive dialog work | Inspector multi-select operations and "apply attribute to all" (§3.3) | One undo group per operation | All |
| **Rename with references** | Search-and-replace in files | Is doc 31 §7.3's engine-exact rename, not a second implementation, reachable from the map and the inspector as well as the script editor. It covers unit, group, trigger and marker names, automatic crew names `<vehicle>d/c/g` and stringtable keys (already in the doc 31 §7.1 index), plus the kinds this doc asks that index to add: `markers[]` links (matched case-insensitively [V]); `respawn_` marker prefixes (doc 31 §3); objective ids across HTML and `objStatus`; per-unit briefing sections (doc 35 §5) | Names built at runtime ("m" + str i) are listed as "cannot prove" | All |
| **Dependency doctor** | Addon-list edits (WA01) | Doc 27 §4.5 per section: reason chains, pins, D1–D8 lints. A missing addon opens the mission with ghost entities and offers the class remap instead of refusing to load (the stock editor aborts, doc 03 §4.11 [V]) | `addOnsAuto[]` parity plus reasoned `addOns[]`, so a vanilla re-save that starts from our file prunes nothing we added [V pruning rule]. Exception: the stock editor prunes against its *in-memory* auto list from its previous save, which loading neither reads nor clears, so a vanilla user who saved another mission in the same editor display and then opens ours can lose any of our extras that mission auto-listed (§3.2) [V code; I practical]; the doctor re-derives them on the next open (D1) | All |
| **Normalise and repair** | `ItemN`/`items=` and id surgery (WA14) | The import linter shows what the game will actually load: a missing `ItemK` becomes a blank default item, extra items past `items=` are ignored, and an unknown enum inside an item drops the item's remaining keys (`P:IO/Serialization/ParamArchive.hpp#L406-L411`; doc 04 §2.3) [V]. Offers "make the file match what loads" or "extend the count". "Normalize as engine" applies Compact and CheckSynchro semantics explicitly | Never implicit; ids stay stable otherwise (doc 04 §12.3 rule 5) | All |
| **Merge and split** | Stock Merge (zero offset only) and copy-paste between files (WA14) | Merge another mission, or one section, at an offset and rotation picked on the map; preview renames of colliding names with reference updates (the stock Merge suffixes `_N` and drops player status, doc 03 §4.11 [V]); keep or drop player slots. Split extracts a selection, with the markers, triggers and sidecar objects it references, into a composition (doc 17 §6) or a new mission | Dangling references listed; `addOns[]` union with reasons | All |
| **Open packed missions** | External unpack and debinarize tools (WA15) | Opens a PBO and a binarized `mission.sqm` through `ofp-pbo` and the raP reader (doc 04 §4); saving writes text into the project | The original archive is never modified | All |

## 6. Map-object actions

Island objects (houses, bridges, lamps, trees) carry ids from the island file. The stock editor reveals them only through Show IDs, which is hidden and forced off in Easy mode, and only when zoomed in (Field Manual `show-ids-and-object-ids`) [V].

- **Click, don't type.** Clicking an island object opens a card: id, class and model, building positions (if known), whether the mission already references it, and actions. Ids appear on hover at any zoom and in every mode, and a search box jumps to an id.
- **Actions.**
  - *Destroyed at start* and *damaged at start (x %)*: `(object N) setDammage x` statements in a compiler-owned block. The host is a compiler-owned Game Logic's init line, which runs like any init line, or the generated `init.sqs` block; the choice is Open question 1.
  - *Objective target*: a trigger bound to the object (Static activation, native `idStatic`), or a `damage`/`alive` condition, feeding an Objective module (doc 31).
  - *Garrison or house position*: a waypoint `idStatic` + `housePos` (native), or the Building-position attribute (§4.3).
  - *Lights off*: `switchLight` on street-lamp objects only (`GameStateExtUi.cpp#L627-L644`) [V]. It is unused in F's mission fields, but doc 35's CSV records 8 uses in 2 shipped official script files, so it is T1 on `Cwa199` [V].
  - *Reference in a script or rule*: inserts a typed map-object reference; the language service shows it on the map and in "where used".
- **Engine facts the card states** [V]: `object N` returns a null object unless N is a primary or network object (`P:Game/Commands/GameStateExtObj.cpp#L616-L629`); `setPos` and `setPosASL` do nothing on island objects (`P:Game/Commands/GameStateExtGrp.cpp#L1709-L1712`, `#L1627-L1630`); `nearestObject` searches 50 m by default (`GameStateExtUi.cpp#L477`); `idStatic` is not renumbered by Compact (doc 04 §3.9).
- **Island fingerprint.** Every stored id carries a fingerprint of the island file (world name plus a content hash) in the sidecar. If the loaded island differs, references turn yellow (PL12) and the island move tool (§5) offers re-resolution. Id stability across island versions and Remastered/CE terrain edits is [U] (PP10).
- **Building positions.** The engine's list comes from each model's path data. Doc 07's `ofp-p3d` extracts map info only, so building positions need either an extension that reads that data [I] or capture-back from a running Remastered/CE game (doc 34 ed18). Until then the picker offers only buildings whose positions are known.

## 7. Safe raw mode

A text view of `mission.sqm`, `description.ext`, `briefing.html`, `overview.html` and `stringtable.csv`, rendered from the CST (doc 04 §12).

- **Live checks while typing:** the config parser, the engine-strict validator (required keys, enum tokens, item counts, the 2047-byte limit, `CheckSynchro` validity, unknown `addOns[]`), and the typed-lens diff in plain words ("unit `alpha2`: skill 0.60 → 0.05, outside the stock slider").
- **Apply** re-parses the text, computes a structural diff against the current CST and applies it as minimal patches (doc 04 §12.3 rule 2), so untouched bytes stay identical. It is one undo group. Text that does not parse cannot be applied, but the draft is kept. The editor never locks (doc 09 P2). If the mission changed on the map while the draft was open, Apply shows a three-way diff against the draft's starting point instead of overwriting those map edits [I].
- **Generated regions.** A raw edit inside a generated prefix or block marks it Customized (doc 31 §8.3); a later parameter change offers a three-way merge.
- **Binarized files** show decoded text read-only, with "convert to text on save".
- **When to use it:** keys the lens does not model (mod-specific `description.ext` classes), pasting from a tutorial, experiments, and cases no tool covers yet. The raw view is also the teaching bridge: selecting an attribute highlights the bytes it produced.
- **Wilco has no raw-text tool** (§9); raw mode is a user capability only [I, Open question 6].

## 8. Lift on import

Opening a mission never changes it: import followed by save is byte-identical (G4). Analysis then offers lifts in a review list. Nothing is rewritten silently. The list is a non-modal badge ("23 init lines can become attributes"), never a dialog on open, because many opens are only to play or study a mission. It groups candidates by intent with counts, so a whole group can be accepted or dismissed at once, and dismissals are remembered per mission in the sidecar. It counts as a lint-driven tip, outside doc 33 §4.8's attention budget [I].

**Confidence rules [I].** *High*: the recognised statements form a leading run of the field, all arguments are literals that resolve (catalog classes, mission names, enum values), and re-emitting the attribute reproduces the normalised original (whitespace and command-name case only). Offer: **replace**. *Medium*: the meaning matches but the form differs (statements after unrecognised code, variables as arguments, `stop` instead of `doStop`, posture set on a non-leader). Offer: **wrap**: the attribute is shown read-only over the untouched text, with "replace" after a diff that shows any reordering. *Low*: not offered; shown as "recognised pattern, left as code".

| Idiom (command names) | Attribute | Confidence | Refused when |
| --- | --- | --- | --- |
| `moveInDriver/Gunner/Commander/Cargo <veh>` | Starts in | H | The vehicle name does not resolve, or the soldier also has Special CARGO |
| `removeAllWeapons` + `addMagazine`… + `addWeapon`… (+ `selectWeapon`) | Loadout | H if contiguous | A class is unknown to the active catalog (then M with a warning) |
| `clear*Cargo` + `add*Cargo [class, n]`… | Cargo | H | Counts are expressions |
| `setDammage 1` / `setDammage x` | Starts destroyed / damaged | H | Not the last effective statement (M) |
| `setCaptive true` | Captive | H | — |
| `allowDammage false` | Protected | H | — |
| `setUnitPos "<enum>"` | Stance | H | Value outside the enum (flagged as a silent no-op) |
| `disableAI "<switch>"` | AI switches | H | Unknown switch (flagged) |
| `stop true`, `doStop` | Hold | H / M | — |
| `setBehaviour`/`setCombatMode`/`setSpeedMode`/`setFormation` on the leader | Start posture | H | On a non-leader (M: the effect is the same group-wide one [V], but re-emission would move the text to the leader) |
| `allowFleeing x` | Courage | H | — |
| `flyInHeight h` with Special FLY | Altitude | H | Not an aircraft |
| `setFlagTexture`, `setFlagSide` | Flag | H | — |
| `setIdentity "<class>"` (+ `setFace`, `setMimic`) | Cast member | H | Class not found in mission or campaign scope (flagged, PL13) |
| `switchMove "<state>"` | Pose | H | State unknown for that unit |
| `<name> = group this` | Group name | H | Assigned in several members with different names |
| `group this setGroupId [...]` | Callsign | H | Values not class names in `CfgWorlds >> GroupNames`/`GroupColors` (a silent no-op, flagged) |
| `setPos [getPos… 0, getPos… 1, h]` | Height (above surface) | H | Unit is a FORM member without Special NONE (lifted as M with the fix shown) |
| `setPos ((object N) buildingPos i)` | Building position | H | Index beyond the building's count (PL11) |
| `inflame true`, `switchLight` | Burning, Light | H | — |
| `lock true` | Runtime lock | H | — |
| `x = group this` + `deleteVehicle this` | Appears when (placeholder group) | M | — |
| `setMarkerType` reveal chains in activations | Revealed when | M | Run from server-only or client-only code (PL10) |
| Camera captures, END/LOSE + debriefing, respawn keys, `OBJ_n` + `objStatus` | Doc 31 §8.2 recognisers | per doc 31 | per doc 31 |

**Hand-edit fingerprints are protected, not lifted.** On import the inspector marks values the stock dialogs could not produce: `year` ≠ 1985, a minute off the 5-minute grid, fractional friendliness, skill outside [0.2, 1], a leader below the group's highest rank, `addOns[]` names with no reason, sqm `show*` keys, Intel `viewDistance`, non-`%f` float lexemes, and template wizard expressions in numeric keys (O: Remastered and official templates) [V detection; I policy]. Each gets the *ProtectedHandEdit* state (§3.2): kept byte-for-byte, explained, and never passed through a clamping or rounding path. In F these fingerprints are rare (0 years, 0 minutes, 1 friendliness, 0 skills out of range) because the official data is editor-made; the protection matters for community missions [I].

**Batch lift.** "Lift all high-confidence" shows the full list with per-row checkboxes and applies as one undo group (G8). The lift log keeps one entry per entity, so a single entity can later be reverted alone as a new change (doc 34 ed22) [I]. Lift coverage on the local corpus is not measured yet [U]; PAT3 measures it.

## 9. The AI angle

Wilco maps a request to an intent and fills a typed form; code computes every menu (docs 21, 25, 31 §9).

**Example: "put the sniper on the church roof".**

1. *Intent* (Pick from ≤ 7 that code offers for the verb "put… on"): Height.
2. *Entity* (Pick): code lists candidates: the selection, then units whose loadout holds a sniper-class weapon in the catalog. With one candidate the step is skipped.
3. *Building* (Pick): code lists island objects in view whose class or model name matches the catalog category for churches, plus "click on the map". With none, Wilco asks the user to click [I: category data comes from the catalog, not the model].
4. *Spot* (Pick): roof top from the model's bounding box [I], a known building position, or "click". Code computes the absolute height and the badge. If the model's walkable (roadway) data puts the top face at the pick, the soldier already starts there with no code (§3.2), and code offers that first [V code path].
5. *Companions* (checkboxes code proposes from the Field Manual): Special NONE (required, not optional, for a formation member), Hold, Stance Down.
6. `attr.propose(entities, attributes)` → diff card → one undo group in Wilco's lane. On Remastered or CE, "Show me in game" (doc 33 §4.7) verifies the height; capture-back can adjust it (doc 34 ed18).

**Typed tools (product-scoped).** `attr.list(entity)`, `attr.describe(kind)`, `attr.propose(entities, attribute)`, `inspector.explain(key)` (engine notes and the doc 33 entry), `tool.preview(kind, params)` for the §5 tools, `lift.review(candidate)`, `mapobject.find(query)` over catalog categories. Each returns editor-command proposals shown as a diff; none touches files directly, and none runs code (AGENTS.md).

**Why weak models succeed.** Every slot has a finite, code-computed domain (seats with free capacity, compatible magazines, flag textures, config callsigns, move states), so a small model only picks. No model output reaches a file as raw text: there is no raw-mode tool, and init code is generated by code, never written by the model (doc 31 §9). Mission text is untrusted data (doc 21 §9.1). Every AI-made attribute carries its provenance in the inspector (G3).

## 10. Cross-references: what lives where

| Topic | Owner doc | What this doc adds |
| --- | --- | --- |
| Ladder, rung-1 contract, prefix span and hash, region states, eject, recogniser policy | Doc 31 §1, §3, §8 | The full attribute catalogue (§4), the inspector (§3), recognisers for init idioms (§8) |
| Modules: respawn, reinforcements, fire support, garrisons, objectives, weather, conversations | Doc 31 §4 | Pointers only (WA35, WA38, WA41, WA44) |
| Cinematics and poses in cutscenes | Doc 32 | Pose attribute for start states only |
| Concept pages, "why greyed out", myths | Doc 33 and `skills/field-manual/` (`init-line`, `special-placement`, `show-ids-and-object-ids`, `condition-of-presence`, `groups-and-leaders`, `sides-and-friendliness`, `empty-vehicles`) | Every attribute and engine note links to one entry; new entries needed: height, loadout, cargo, locks, callsigns, and one on attributes themselves (what the generated prefix is, why an init line gained one, lift and presets) |
| Named zones, phases, routes; retarget workbench; re-association after vanilla re-saves; difficulty chip; capture-back; undo lanes | Doc 34 ed01, ed05, ed06, ed08, ed15, ed16, ed18, ed22 | Island-move transforms and object-id re-resolution (§5, §6), reusing ed15's dry-run and fidelity-report machinery under its own name |
| Dependency derivation and write rule | Doc 27 §2.4, §4.5 | Dependency doctor UX (§5) |
| Lossless CST, patches, writer profiles | Doc 04 §2, §12 | Protected hand edits (§3.2, §8) |
| `Cwa199` evidence tiers | Doc 35 §8.3 | Per-attribute gating (§4.3) and probes (§11) |
| Checker, catalog, locality, risk | Docs 23, 24 | Locality classes per attribute (§4.1) |

**Design-gap candidates** (to file under `docs/design-gap-requests/`; this doc does not edit its siblings):

- (a) Doc 04 §12.3 rule 4 says the engine requires contiguous `Item0..N-1`; doc 04 §2.3 and `ParamArchive.hpp#L406-L411` show gaps and extra items load silently. Rule 4 should say "we keep lists contiguous", not "the engine requires it".
- (b) Doc 03 §3's description of unknown-enum loading vs doc 04 §2.3 (item-level leniency); the source supports doc 04.
- (c) Doc 31 §3 says "magazines before weapons" as a requirement; on `Cwr`/`Ce` the order is irrelevant [V], and it stays the safe default for 1.99 [U].
- (d) Community material says `setPos` does not take a soldier out of a vehicle; in CWR and CE both `setPos` and `setPosASL` call the vehicle's get-out handlers for a mounted soldier (`P:Game/Commands/GameStateExtGrp.cpp#L1758-L1802`, `#L1643-L1687`; CE `#L1770`, `#L1655`) [V]. 1.99 is [U] (PP12). The Height and Seat attributes must never be combined on one soldier.
- (e) `allowDammage` must not be tiered `Cwr`/`Ce`-only: it is present in the 1.99 executable and used in shipped official content (4 uses in 2 files), which makes it T1 under doc 35 §8.3; only its 1.99 effect is [U] (PP6).
- (h) Doc 27 §2.4 and §4.5 say manual `addOns[]` entries are never pruned. The pruning compares against the editor's in-memory auto list from its previous save, which `ArcadeTemplate::Clear()` does not reset and loading does not read (`P:AI/ArcadeTemplateFind.cpp#L184-L203`, `P:AI/ArcadeTemplate.cpp#L1910-L1932`; CE identical), so a manual entry can be pruned when it matches a name auto-listed at that previous save, including one made for another mission in the same editor display [V code; practical effect I].
- (i) Doc 35 §8.3 lists `benchmark` as T2 while its rc28 row calls it T3.
- (f) Doc 31 §8.2 rates init idioms (loadouts, cargo fills, `setPos` height lifts) "medium". This doc's §8 rates their exact, contiguous, literal forms High under the same rule (replace only when re-emission reproduces the original) and everything else Medium. Doc 31 §8.2 should point to §8's per-idiom table.
- (g) One idea has several names: doc 31 §3 says "behaviour preset" and "character"; the mission-primer idioms page (`skills/mission-primer/references/idioms.md`, I11–I15) says "Behaviour preset attribute", "start seat" and "Health slider"; this doc says Stance, Start posture, Courage, Hold, Starts in, Starts destroyed and Cast member. One attribute vocabulary should be canonical (doc 31 §3 or its design doc), with bundles always called presets, so users and Wilco see one word per idea.

## 11. Phased plan and acceptance tests

| Phase | Scope | Depends on |
| --- | --- | --- |
| PT0 | Read-only inspector over the CST: every key, exposure, engine notes, fingerprints; raw mode read-only; import linter | Doc 31 L0 (lossless emit, catalog, checker) |
| PT1 | Editable inspector (exact numbers, minute, year, skill, relations, leader), multi-select; attributes with no catalog need (seat, destroyed, captive, stance, hold, AI switches, altitude, start posture, courage, group name, callsign, flag, burning, light, lock, start-at); the Attributes overlay, map verbs, the drop chip and presets (§4.4); mission settings and HUD items; high-confidence lift; dependency doctor | PT0; doc 31 L1; doc 27 §4.5 |
| PT2 | Catalog attributes (loadout, cargo, cast, pose) and kits; Height with WRP and model boxes; map-object actions; rename with references; raw-mode apply; bulk edit | PT1; doc 07 `ofp-wrp`, `ofp-p3d` |
| PT3 | Class remap, side swap, merge and split, normalise; SP ↔ MP wizard; island move; building positions from model data or capture-back | PT2; doc 34 ed15, ed18 |
| PT4 | Locality-verified MP lowering; 1.99 promotions after PP1–PP12 | Doc 08 MP Preview; the probe suite |

| ID | Acceptance test | Pass criteria |
| --- | --- | --- |
| PAT1 | Open synthetic fixtures with `minute=7`, `year=1991`, `resistanceWest=0.37`, `skill=0.05`, a leader flag on a private, Intel `viewDistance`, sqm `showGPS`; edit an unrelated field; open and close every dialog; save | Only the edited bytes change; every protected value is byte-identical |
| PAT2 | Every attribute on a synthetic mission, compiled per profile | Prefix text equals the golden file; a catalog scan finds only T1 commands in `Cwa199` output unless a probe promoted one; compiling twice is byte-identical |
| PAT3 | Property test: lower an attribute, then run its recogniser | Returns the same attribute with High confidence; on the opt-in local corpus, report lift coverage per intent (counts only) |
| PAT4 | "Sniper on a roof" on CWR through the harness | The unit is within 0.5 m of the target height after 10 s and has not moved |
| PAT5 | Class remap on a fixture with units, script literals, cargo and loadouts | Every reference updated or listed as unresolved; `addOns[]` recomputed; one undo restores identical bytes |
| PAT6 | Island move (dry run) to a different island fixture | Report lists invalid object ids, units in water or off-map; nothing written until accepted |
| PAT7 | Dependency doctor on a fixture with a stale name, a script-only class and a user pin | Only the stale name is proposed for removal; simulating the engine's save-time pruning from a fresh editor display removes nothing we wrote, and a second run seeded with another mission's auto list reports exactly the extras it would prune |
| PAT8 | Raw mode: type an unknown enum, a missing required key and a 3,000-byte init value | Each is reported with its engine consequence; the editor never locks; valid edits apply as minimal patches |
| PAT9 | A weak local model asked for "the sniper on the church roof, prone, holding" | Only typed proposals; zero model-written init text; passes within the bounded repair loop (doc 25) |
| PAT10 | Seat, loadout and cargo attributes in a two-client MP Preview (doc 08 P4) | Seats correct, no duplicated cargo or weapons; locality classes match observations |
| PAT11 | Map object marked destroyed, then the island file fixture changed | Reference turns yellow (PL12); re-resolution offered |
| PAT12 | Rename a crewed vehicle and a marker linked from `markers[]` | `<vehicle>d/c/g` references and all links updated; a respawn-prefix collision is warned |
| PAT13 | Merge a mission at an offset with colliding names | Renames previewed with reference updates; one undo |
| PAT14 | Import a mission with 20 recognised idioms, lift none, save | Byte-identical output |
| PAT15 | Moderated newcomer test (doc 31 AT1 protocol): seat, height, loadout, cargo, captive, stance, starts destroyed, callsign, group name and flag on a fixture mission, without typing code or opening raw mode | Each intent is reached in at most two steps from the selection (right-click verb, drop chip or "+ Add" search); every result shows on the Attributes overlay; time targets come from the moderated sessions [I] |
| PAT16 | Delete the sidecar of a mission that uses every attribute and reopen it; then add Captive to a unit whose own init text already sets it | Every attribute returns as a High-confidence lift offer, and accepting all gives byte-identical output; the second step offers the lift and writes no second `setCaptive` |

**Probes (added to the in-game probe suite; AGENTS.md porting rules).** PP1 `setPosASL`, `buildingPos`, `setFuelCargo` and `setRepairCargo` semantics on 1.99 (all T3). PP2 the height reference of `setPos` for units and objects on low-lying ground where a walkable face lies below the requested height, and whether a soldier set above a non-walkable roof stays there, all profiles. PP3 `addWeapon`/`addMagazine` order on 1.99. PP4 whether `moveIn*` assigns the seat on 1.99. PP5 `disableAI "ANIM"` on 1.99. PP6 `allowDammage false` on 1.99. PP7 cargo and loadout init lines in MP (duplication). PP8 health 0 vs `setDammage 1` at start (`!alive` triggers, casualty counts). PP9 whether the vanilla editor keeps generated prefixes, and field length limits there (doc 31 open question 6). PP10 object-id stability across island versions and Remastered/CE terrain edits. PP11 confirm in game the 0.6 friend/enemy threshold read from the source (and look for any graded effect of fractional friendliness), and the meaning of skill above 1. PP12 whether `setPos` takes a mounted soldier out on 1.99.

**Provisional lints.** PL01 error: a unit's sqm height edited with no Height attribute ("Y is ignored"). PL02 warn: health below 0.03 used as if it made a wreck. PL03 warn: presence or presence condition on a playable unit. PL04 warn: imported `getPos`-based height on a FORM member. PL05 error at skill 0; warn outside [0.2, 1]. PL06 warn: leader flag below the highest rank. PL07 warn: user code after a prefix overrides an attribute. PL08 error: a field over 2047 bytes. PL09 warn: `lock false` used as if it unlocked. PL10 warn: marker changes in server-only or client-only code. PL11 error: a building-position index out of range. PL12 warn: an object id against a different island fingerprint. PL13 warn: an identity class found in neither mission nor campaign scope. PL14 info: sqm `show*` keys (no effect).

## Open questions

1. **Map-object host.** Should destroyed-at-start objects lower to a compiler-owned Game Logic's init line (runs like other init lines) or to the generated `init.sqs` block, given that `init.sqs` timing in MP was not traced (Field Manual `init-line`) [U]?
2. **View distance.** On `Cwr`/`Ce`, write only the Intel key (clamped to the user's range, dropped by a vanilla re-save), or also an `init.sqs` line that survives that re-save?
3. **Building positions.** Extend `ofp-p3d` to read model path data, or rely on capture-back from a running game? Which is legally and technically cheaper (doc 07)?
4. **Remap tables.** Ship community equivalence tables as T0 packs? Their licences and accuracy are unknown.
5. **Unlisted classes.** Allow placing classes the stock lists hide (scope below 2) with a warning, or only through raw mode?
6. **Raw mode for Wilco.** Never, or a strong-model-only "propose raw patch" behind the same validation (doc 21 §3.3)?
7. **Posture setters.** Answered for `Cwr`/`Ce` [V]: all four accept a unit or a group and act on the unit's group (§4.3 Start posture). Open only for 1.99, where the same group-wide behaviour is expected but unprobed [U]; the catalog records it before the leader-prefix lowering is final for `Cwa199`.
8. **Easy mode.** Which fields each Easy (Simple) dialog omits needs game data [U]; the inspector's `advanced_only` flag depends on it.
9. **Explicit crew.** Is naming placed crew `<vehicle>d/c/g` safe on 1.99, where the automatic-name convention is unverified?
10. **Fingerprint ranking.** Community missions are where hand edits live, but the S sample is 9 missions. A larger, licence-clean community sample is needed before ranking fingerprint handling.
11. **Linked presets.** §4.4 copies preset values and updates only on request. Should a mission-local kit optionally stay linked, so one edit re-equips thirty riflemen, given that a link is exactly the invisible coupling §1.1 criticises? If linked, the link must be drawn on the Attributes overlay and listed in "where used".

## Sources

### Engine source

BohemiaInteractive/CWR@ffc61838b7, and ofpisnotdead-com/CWR-CE@b67bf3bd62 where a CE line is given.

- `engine/Poseidon/AI/ArcadeTemplate.cpp#L213-L410` (unit keys, skill default), `#L1474-L1580` (Intel, leader, randomSeed), `#L1754-L1860` (IsConsistent), `#L1862-L1992` (required addons, section serialize)
- `engine/Poseidon/AI/AICenterImpl.cpp#L853` (MinHealth), `#L955-L1133` (placement, marker choice, surface snap, health), `#L1206-L1241` (licence plates), `#L1525-L1600` (presence, CARGO), `#L1631-L1722` (crews), `#L1745-L1768` (civilian relations), `#L1915-L2186` (leader, inits, waypoint-1 posture, formation)
- `engine/Poseidon/AI/AIUnit.cpp#L1366-L1380`; `engine/Poseidon/AI/AIGroupImplHealth.cpp#L1566-L1578`; `engine/Poseidon/AI/AIGroup.cpp#L1229-L1239`; `engine/Poseidon/AI/VehicleAICombat.cpp#L76-L367`
- `engine/Poseidon/Game/Commands/GameStateExt.cpp#L1220`, `#L1316-L1319` (registrations)
- `engine/Poseidon/Game/Commands/GameStateExtGrp.cpp#L171-L261` (enum no-ops), `#L885-L935` (position arguments), `#L979-L1018` (setGroupId), `#L1614-L1690` (setPosASL), `#L1696-L1810` (setPos, including get-out); CE `engine/Poseidon/Game/Commands/GameStateExtGrp.cpp#L1655`, `#L1696`, `#L1770`
- `engine/Poseidon/Game/Commands/GameStateExtUi.cpp#L123-L139`, `#L184-L235`, `#L447-L477`, `#L2330-L2345`, `#L2378-L2405`, `#L2624-L2863`
- `engine/Poseidon/Game/Commands/GameStateExtObj.cpp#L297-L374`, `#L616-L646`, `#L1212-L1259`
- `engine/Poseidon/UI/Map/UIArcadeWaypoint.cpp#L584-L799` (Intel dialog); `engine/Poseidon/UI/Map/UIArcade.cpp#L915-L1113` (unit dialog); `engine/Poseidon/UI/Controls/UIControlsWidgets.hpp#L238-L246`
- `engine/Poseidon/UI/OptionsUI.cpp#L855-L879`; `engine/Poseidon/UI/Locale/MissionLanguageDetector.cpp#L300-L317`; `engine/Poseidon/UI/DisplayUIMenus.cpp#L850-L876`
- `engine/Poseidon/World/WorldInit.cpp#L242-L268`, `#L570-L680`; `engine/Poseidon/IO/Serialization/ParamArchive.hpp#L372-L413`
- Added by the engine review: `engine/Poseidon/AI/AICenterStats.cpp#L1371-L1410` (friend/enemy threshold); `engine/Poseidon/AI/AIGroupImplHealth.cpp#L1398-L1435` (callsign lookup); `engine/Poseidon/AI/ArcadeTemplateFind.cpp#L184-L203` (`Clear`); `engine/Poseidon/UI/Map/UIMapExtDisplay.cpp#L99-L214` (editor load); `engine/Poseidon/UI/Map/UIArcade.cpp#L1178-L1182` (skill write-back); `engine/Poseidon/AI/VehicleAICombat.cpp#L365-L370` (`SetDammage` guard); `engine/Poseidon/AI/VehicleAI.cpp#L1972-L1975` and `engine/Poseidon/World/Entities/Infantry/SoldierOldSim.cpp#L215-L226`, `#L943-L959` (strip weapons, soldier surface); `engine/Poseidon/World/Simulation/Simul.cpp#L1252-L1301` (place on surface); `engine/Poseidon/World/Terrain/Landscape.cpp#L1655-L1930` (road-surface queries); `engine/Poseidon/Game/Commands/GameStateExtGrp.cpp#L1532-L1560` (`getPos`), `#L263-L315` (formation, speed mode); `engine/Poseidon/Game/Commands/GameStateExtWorld.cpp#L453-L506` (marker setters); `engine/Poseidon/Game/Commands/GameStateExtUi.cpp#L627-L657` (lights, fires); `engine/Poseidon/UI/Settings/GameSettingsConfig.hpp#L22`

### Repo docs and skills

`docs/research/03-original-editor-code-map.md` (§3, §4.1–§4.13); `04-mission-data-model-and-formats.md` (§2–§5, §12); `07-file-formats-and-rust-crates.md` (§7, WRP and P3D); `09-community-wishlist.md` (P2–P10, S13, CO2); `23-script-tooling-lsp-and-linter.md` (§4–§6); `24-script-command-risk-audit.md`; `27-addons-and-mods.md` (§2.4, §4.5); `31-no-code-ladder-modules-rules-and-scripting.md` (§1–§4, §8–§10); `32-cinematics-and-camera.md`; `33-field-manual-and-live-tutorials.md`; `34-iron-curtain-second-pass.md` (ed01–ed22, §2.4, le18); `35-lessons-from-real-content-and-later-armas.md` (§4, §5, §8); `docs/research/data/corpus-script-idioms.csv`, `cwa199-observed-commands.csv`; `skills/field-manual/references/init-line.md`, `special-placement.md`, `show-ids-and-object-ids.md`, `condition-of-presence.md`; `skills/mission-primer/references/idioms.md` (I11–I15, naming only).

### Community and external

All paraphrased; nothing copied.

- BIKI, "Operation Flashpoint: FAQ: Mission Editing": <https://community.bistudio.com/wiki/Operation_Flashpoint:_FAQ:_Mission_Editing> (read through the Wayback Machine; the live API returned 403).
- acemod/arma3-wiki, `dist` branch (machine-readable BIKI mirror; version tags): <https://github.com/acemod/arma3-wiki/tree/dist>, fetched 2026-09-27.
- Faguss, OFP 1.96 vs CWA 1.99 scripting differences: <http://ofp-faguss.com/files/cwa_scripting.pdf>.
- OFPEC COMREF and forum boards, e.g. <https://www.ofpec.com/forum/index.php?topic=91.0> (respawning); topics 419, 847, 3364, 3834, 18905, 22323, 22956, 25946 and 28634 on the same site; OFPEC Editors Depot counters (doc 31 §2).
- A 2014 Steam CWA discussion: <https://steamcommunity.com/app/65790/discussions/0/35220315784764335/>.

### Local analysis (not in the repo; aggregates only)

An init-intent classifier over the O corpus (intents, commands, idioms, fingerprints and UI-coverage tables); a field-gap scan over the F corpus (hidden keys, description.ext keys, command use by field); a registration-row and version-tag comparison; OFPEC and BI-forum title scrapes, recounted. Scripts and outputs stay in the session scratch area and contain no mission text.

## Verification notes

### Product review notes

Product and UX review, 2026-09-27. It asked of every affordance: is it easier than the hand edit it replaces, can a user find it, does it stay short for thirty units, can the result be seen, inspected and edited, is an existing mission safe (lossless, lift never forced), and does it reuse the concepts of docs 31, 33 and 34 instead of adding parallel ones. **Held:** the G2 lowering order with a deletable sidecar; protected hand edits and no destructive dialog round trips; "replace" only on exact re-emission; one-undo-group dry runs; engine truth inline; weak models limited to picks. **Changed:**

- *Discoverable and visible.* The attributes had no stated entry point and left no mark on the map. New §4.4: goal search shared with doc 31 §4.1 and the doc 34 le18 palette, right-click verbs, a drop chip for seats and building positions that leaves the stock drags unchanged, an Attributes overlay with glyphs, and human forms that offer the same code-computed picks as Wilco. TL;DR and PT1 updated; PAT15 added.
- *Tedium.* Doc 31 §3 defines rung 1 as "attributes and presets", but this doc never mentioned presets. §4.4 adds presets and kits (copied values with provenance, explicit "update from preset", "Vary" drawn once), and open question 11 asks whether kits may stay linked. §8's lift list now groups by intent with group accept and dismiss, and the Advanced inspector opens filtered to keys with something to say (§3.1).
- *Hidden side effects.* Height forced Special NONE and Starts in named vehicles, with no stated way to see or undo either. §4.1 now makes companion edits visible in the preview and why card, and reversible only when untouched. Adding an attribute over code that already does the same thing offers the lift instead of a duplicate statement (PAT16).
- *Safety of existing missions.* The lift list is a non-modal badge, never a dialog on open. A raw-mode draft applied after map edits shows a three-way diff instead of overwriting them (§7). Class-remap edits inside hand-written text are grouped per file and can be excluded (§5). Height stores the roof or building pick, not a stale absolute number (§4.2 `OnRoof`, §4.3). A lost sidecar costs only provenance, because every prefix lifts back at High confidence (§4.4, PAT16).
- *Honest controls.* Relation sliders implied graded hostility whose runtime meaning is [U] (PP11). The stock four choices stay the default, with exact values one click away and labelled (§4.3).
- *No duplicated concepts.* "Island retarget" collided with doc 34 ed15's "Retarget…", which changes the target profile; it is now "Island move" and reuses the ed15 machinery (TL;DR, WA13, §5, §6, §10, PT3, PAT6). "Rename with references" is now stated to be doc 31 §7.3's rename, not a second one. Inspector engine notes are doc 33 registry facts (`Vec<ConceptId>`), greyed-out reasons route through doc 33 §4.4, and §10 asks the Field Manual for an entry on attributes themselves.
- *Cross-doc gaps recorded, not edited.* §10 (f): doc 31 §8.2 rates init idioms "medium", while §8 here rates exact forms High. §10 (g): the same attribute has different names in doc 31 §3, the mission-primer idioms page and this doc.

**Residual concerns.** The inspector's "every key" remains an expert surface even when filtered, and whether Easy mode users ever need it is untested. The count of about 25 attributes may itself become a long "+ Add" list; ranking by the F corpus frequencies is the proposed default [I]. PAT15's time targets wait on moderated sessions. §4.4's drop chip keeps the stock drag-to-move and Groups-mode link drag intact (doc 03 §4.3); a modifier key was rejected because Shift rotates and doc 33 §4.2 gives Alt+click to "What is this?". Whether the chip is noticed without being a nuisance needs the same sessions [U].

### Engine review notes

Adversarial engine review, 2026-09-27. Every compile-to claim was re-read against `BohemiaInteractive/CWR@ffc61838b7` (CE lines checked where the doc gives them, at `ofpisnotdead-com/CWR-CE@b67bf3bd62`), docs 03, 04, 23, 24, 27 and 35, the `cwa199-observed-commands.csv` tiers and the local 1.99 string-scan output; corpus counts were recomputed from the local scratch scripts. Static reading only; nothing was built or run.

**Confirmed as written [V].** Y is ignored and re-snapped for units, empties and triggers (also sound sources and mines). The Intel minute rounding, the 0/1 friendliness snap and the 0.2–1.0 skill clamp, now with the OK write-back lines. `addOns[]` is checked per section and one unknown name fails the load; `addOnsAuto[]` is never read (CE identical). `setPos` and `setPosASL` dismount a mounted soldier in CWR and CE. Formation re-placement of non-leaders runs inside the centre's `BeginArcade`, before `WorldInit` executes the collected init lines, so Height must force Special NONE on formation members. The 0.03 health floor; presence ignored for playable units and evaluated before init lines; Special CARGO's first-vehicle rule. Local-only marker setters; `lock false` giving DEFAULT; `moveIn*` a no-op for a non-local soldier and refused for a soldier already in a vehicle; courage defaulting to the leader's ability; the mission-then-campaign identity lookup. Item-level leniency (return value ignored; `OnError` only records a context, plus an RPT line). The O and F corpus figures: 78% / 66% / 75% "no UI" fields and 19 of 7,089 action fields fully covered; identity 140, starting behaviour 129, flags 116, attached scripts 111, loadouts 103, cargo 97 missions in F (the "courage 89" figure counts `allowFleeing 0` only). The `Cwr`/`Ce`-only status of `setDate`, `setFriend`, `createGroup` and `createMarker` (absent from the 1.99 executable) and the T3 status of `setPosASL`, `buildingPos` and `isServer`.

**Fixed in place.**

- *Height lowering (decision-critical).* The "AI entity vs other object" split was wrong: `mission.sqm` creates every entity through `NewVehicle`, which returns an `EntityAI`, so `setPos` is surface-relative for units, vehicles and objects alike, and the engine applies the model offset itself. The model-box `setPos` branch applies only to non-`EntityAI` objects, which a mission cannot place. `Cwa199` objects therefore get the same T1 `setPos` as units; `setPosASL` is an optional absolute form. New [V code path] caveats: `setPos` measures from the highest walkable face at or below `h` read as an absolute height (so on low-lying ground a floor or roof can become the reference), `getPos` measures from the face below the object, so the two are not inverses; and soldiers already start on the highest walkable face at their x/z. PP2 was re-aimed at these.
- *Friendliness.* The runtime side test is 0.6, not "a map colour at 0.5"; 0.5 is only the stock dialog's reading threshold, so 0.5–0.59 looks friendly in the dialog and fights as an enemy. WA04, §3.2, the Relations row and PP11 updated.
- *Protected.* `allowDammage` is T1 on `Cwa199` (4 uses in 2 shipped official files), so it is offered with an "effect unprobed" note instead of greyed out; on `Cwr`/`Ce` the flag also blocks any `setDammage` that raises damage, so Protected and Starts destroyed are now mutually exclusive by construction (the fixed prefix order would otherwise cancel the wreck silently). "Scripted damage still applies" was true only for the fallback reset handler.
- *Callsigns* come from the global `CfgWorlds >> GroupNames` and `GroupColors` classes, not a world's name lists; unknown names are silent no-ops, and a duplicate callsign swaps names with the other group.
- *Posture setters* (open question 7): all four act on the unit's group in `Cwr`/`Ce`, so the lowering from the leader is safe; a non-leader lift stays M only because re-emission moves the text.
- *Loadout*: `removeAllWeapons` on a soldier strips binoculars and night vision and re-adds only the built-in throw, put and fist weapons [V, was I]; on a vehicle it strips magazines only.
- *Cargo*: `setFuelCargo` and `setRepairCargo` are T3 on `Cwa199`; `setAmmoCargo` and the rest are T1. `switchLight` is T1 (official script use), not "present in the executable but unused", and acts only on street lamps, with an unknown state becoming AUTO.
- *Intel `viewDistance`*: Mission section only, alias `missionViewDistance`, and honoured only while the player's "respect mission view distance" option is on.
- *Cast member*: the class must define the five keys the command reads; in MP an init-line `setIdentity` runs after the player's own identity is applied.
- *Save-time pruning* (decision-critical nuance). "Removes only names auto-added in the same session" holds, but the list it prunes against survives loading another mission in the same editor display, so extras can be lost after a vanilla user edits two missions in one sitting. The Dependency doctor row, PAT7 and design gap (h) were updated; the write rule itself (parity `addOnsAuto[]`, reasoned extras and pins in `addOns[]`) stands.
- *Smaller corrections*: `randomSeed`'s only use is licence plates; a negative skill means rank-derived; minutes 58–59 overflow the stock combo (outcome unverified); WA47's "O: 3 fields" were `cadetMode`; doc 35's T2/T3 disagreement on `benchmark` recorded as gap (i).

**Residual concerns.**

- The roadway-ceiling behaviour of `setPos`, the "soldiers start on the top walkable face" rule and the stale in-memory auto list are read from code paths, not observed; which island models have roof roadways, and whether a soldier stays above a non-walkable roof, are [U] until PP2. The Height compiler needs model roadway data (doc 07 `ofp-p3d` does not read it yet) to correct `h` near sea level.
- Every 1.99 statement rests on the string scan and shipped-content tiers; the CWR source is the Remastered engine, so behaviour such as the `setPos` dismount, the 0.6 threshold and the group-wide posture setters is [U] on 1.99 even where the command is T1.
- The doc 04 §12.3 rule 4 correction (gap (a)) and the doc 27 pruning nuance (gap (h)) are still only candidates; neither sibling doc was edited here.
