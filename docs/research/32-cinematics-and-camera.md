# Cinematics and camera: a first-class timeline

Research doc 32 for `ofp-editor`. Audience: contributors and LLM coding agents reading only this file. Status: **proposal-only**.
Question answered: how the editor makes intros, outros, in-mission cutscenes, dialogue scenes and camera work first-class. They are
authored on the 2D map and a timeline, previewed live where the engine allows it, and compiled per target profile to plain vanilla
SQS, triggers and `description.ext`, so nobody has to hand-write a camera script (and anybody still can).

**Epistemic legend.** **[V]** verified in pinned source or on a fetched page (cited). **[I]** inferred or proposed by us. **[U]**
unknown; needs a probe, a fetch or a playtest. Repository docs are cited as "doc NN §x".
**Citations.** `CWR:` = `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/`; `CE:` = `ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/`.
Line numbers are CWR's. The cinematic runtime files (`GameStateExtUi.cpp`, `CameraHold.cpp`, `CamEffects.cpp`, `TitEffects.cpp`,
`Scripts.cpp`, `WorldSetup.cpp`, `WorldInit.cpp`, `WorldImpl.cpp`, `DisplayUIMenus.cpp`, `Detector.cpp`, `DynSound.cpp`, `QStream.cpp`,
`express.cpp`) were SHA-256-identical in CE on 2026-09-27. `World.cpp`, `UIMapExtDisplay.cpp`, `GameStateExtTestAudio.cpp`,
`GameStateExtWorld.cpp`, `OptionsUI.cpp` and `Landscape.cpp` differ; the cited passages were re-checked in CE (same logic, shifted
lines). `GameStateExt.cpp` registrations sit about 2 lines earlier in CE (camera block CE `#L1339-L1354`). Re-read this session:
camera registrations and handlers, `CameraHold.cpp`, `QStream.cpp` `export_clip`, the SQS scheduler, the `WorldSetup.cpp` setters,
the `DisplayUIMenus.cpp` cutscene, end-gate and `StartAutoTest` code, `UIMapExtDisplay.cpp#L560-L611`, `WorldImpl.cpp#L492-L561`.
**Companions.** Docs 03 §4.7–§4.8 (trigger and Effects dialogs), 04 (sections, `description.ext` classes), 08 (Preview, harness),
18/19 (campaign Cutscene nodes; no campaign vars in chapter cutscenes, outros, awards), 21 (agent doctrine), 22 §2.1 (T0 packs;
minijinja with fuel), 23 (language service, catalog), 24 (risk caps), 25 (weak-model harness), 28 (fun), 33 (Field Manual C1).
Doc 31 (the no-code ladder) fixes rung 4's engine facts and compile contract in its §6; this doc refines rung 4 only.
**Hygiene.** No community script is copied. Patterns are described in our own words; quotes are short and attributed.

## TL;DR

- **Demand was high and never met natively [V].** Camera and cutscene tutorials are among OFPEC's most-downloaded OFP editing
  items; the best modern community tool (Faguss's Flashpoint Cutscene Maker) needs the Fwatch extender at runtime (§1).
- **The engine camera is a small keyframe machine, and we model exactly that [V].** `camCommit t` moves in a straight line at
  constant speed, the look-at is recomputed every frame, FOV is a fixed lens per commit. No roll, no independent pitch or heading
  (`camSetDir`/`Bank`/`Dive` do nothing on 3.05/CE), no auto-zoom (`camSetFovRange` is a stub), no preload (§2.3).
- **One timeline, eight track kinds** (shots, cut layer, title layer, music, sound, dialogue, actors, world) plus a script-clip lane
  as the escape hatch, compiled to one readable SQS driver per sequence whose `&t` cues share the game clock with camera commits
  (§3.2, §3.5).
- **Authored on the 2D map:** eye points, look lines, FOV wedges, height-above-surface labels, a terrain-profile strip. Templates
  generate keyframes; nobody types coordinates (§3.3, §5.1).
- **Safe by construction:** every exit path terminates the view *through the camera object*; input locks are balanced (the engine
  keeps a counter); fades live on the cut layer (subtitles overwrite the title layer, and a title-layer BLACK OUT blocks the mission
  end); actors are protected; a watchdog restores the view if the driver dies (§3.5).
- **Hosts:** Intro, OutroWin/OutroLoose, in-mission (rule, trigger, waypoint), campaign Cutscene nodes, the death camera, and
  zero-script Effects-dialog shots (§3.6).
- **Preview:** 2D is exact for the camera path; on Remastered/CE the harness gives exact shot thumbnails, quick framing and full-run
  filmstrips, with any cutscene section staged as the Intro of a group-less Mission so it plays in intro mode (§4). 1.99: export,
  then the stock editor's per-section Preview.
- **Capture and import:** the manual camera appends paste-ready blocks to `clipboard.txt`; the editor tails it and turns each block
  into a keyframe. Old camera scripts become shots where recognised, opaque script clips otherwise (§3.8, §4.4).
- **Weak models pick, code computes:** the model chooses templates, subjects, moods and words; code computes every coordinate,
  time and class name and validates every output (§5.3).
- **Headline acceptance test:** a newcomer authors a 30-second intro (4 shots, title card, music, radio chatter) without writing
  script, previews it live on Remastered, and it passes every lint on all three profiles (§7).

## 1. What the community did, and why it was hard

### 1.1 Evidence of demand [V counts, I interpretation]

| Resource (OFPEC Editors Depot unless noted) | Count | What it shows |
| --- | --- | --- |
| "Camera.sqs" tutorial (Messiah); "Intro to Camera Scripting" (snYpir) | 2,540 (4.6/5); 2,453 (5/5) | Camera scripting was learned from tutorials, not tools |
| Cutrsc/Titlersc tutorial; Font/Text tutorial | 1,388 (5/5); 781 | Title cards meant hand-written config |
| Sound Tutorial; OFP Sound Lab; Wav2Lip | 3,904; 5,303; 1,632 | Dialogue plumbing (classes, lip files) was the other half of every scene |
| Bullet Cam; Helmet Camera; LogicCam | 1,542; 1,151; 987 | Gadget cameras as gameplay |
| "On player killed" death-cam tutorial | 664 | Hidden hook conventions |
| Flashpoint Cutscene Maker v1.14 (ofp-faguss.com) | requires Fwatch 1.15 | The best tool needs a runtime extender |
| OFP.info "VideoMissions" category | 3 pages | Cinematic-only missions were a genre |

The counters mostly measure downloads after the 2007 site migration, so compare them with each other only [I]. Reviews and
tutorials add taste: "The ultimate goal for each scene should be emotion"; spinning editor cameras and slow zooms read as novice work;
long cutscenes were a named complaint (doc 28 §2.2, §3.4).

### 1.2 The classic workflow [V engine; I community practice]

Start the stock `camera.sqs` (game data, not in the repo) in a Preview and fly the engine's manual camera; each Fire **appends** a
timestamped `camSetTarget`/`camSetPos` (or `camSetRelPos` with Left Shift)/`camSetFOV`/`camCommit 0`/`@camCommitted _camera` block to
`clipboard.txt` (`CWR:World/Scene/Camera/CameraHold.cpp#L463-L536`; `IO/Streams/QStream.cpp#L361-L376`). Paste the blocks into an SQS
file, turn commits into moves, add `titleText`, `playMusic`, `say`, `~` delays and `cameraEffect ["terminate","back"]` by hand, time it
all by re-running the mission, and wire it from `initintro.sqs` or a trigger. Trivial shots use the Effects dialog presets (doc 03 §4.8).

### 1.3 Why it was hard, and what replaces it

| Pain | Evidence | Answer here |
| --- | --- | --- |
| Positions travel through a clipboard; no path is ever drawn | the workflow above | Keyframes on the 2D map, plus capture import (§3.3, §4.4) |
| Timing found by trial and full re-runs | aligrant: keep the first `camCommit` at 0 "otherwise you will have a camera floating around" | Timeline with absolute cues; live shot preview (§3.5, §4) |
| Every dialogue line touches 3–4 artefacts by name | Sound tutorials, Wav2Lip pain (doc 09 §6) | Screenplay track that generates classes, `.lip` and timing (§3.2) |
| Actors die or wander mid-scene | aligrant: troops "dead 20 seconds later" | Actor staging, protection and reset on cuts (§3.2) |
| Camera or input stuck after a script error | doc 23/24 error model; counter semantics (§2.7) | Safe wrapper plus watchdog (§3.5) |
| Dead commands waste effort | `camSetDir`/`Bank`/`Dive`/`FovRange` (§2.3) | Never emitted; linted in hand code (§3.7) |
| The good tool needs Fwatch | FCM docs | All authoring in the editor; output is vanilla (§3.5) |
| Novice look | doc 28 | Templates with restrained defaults; length and "spin" style notes (§3.7, §5) |
| Gadget cameras and film missions were hand-rolled | Bullet/Helmet Cam, LogicCam; VideoMissions (§1.1) | Gameplay-camera host and a film preset with style notes off (§3.6) [I] |

### 1.4 Prior art in other editors [V pages; I lessons]

| Tool | What we take | What CWA forbids |
| --- | --- | --- |
| Unreal Sequencer camera-cut track | The shot list as a lane of sections; adjacent sections cut | Blends between two cameras (CWA drives one camera) |
| Unity Timeline + Cinemachine | Shots record intent (subject, framing, move); editor playback is "only a simulation" | Runtime auto-framing (we compute FOV at authoring time) |
| Arma 3 Key Frame Animation; Splendid Camera; `BIS_fnc_establishingShot` | Splines drawn on the map with live preview; paste-able shot state; preset shots with a few knobs | Pitch/bank, focus, aperture fields |
| StarCraft II Cutscene Editor; Source Filmmaker | A separate studio started by gameplay triggers; a free "work camera" apart from authored shots | — |
| Creation Kit scenes | Phases × actors; a dialogue action completes when its line ends | Detecting end of speech (no command for it; §2.5) |
| Flashpoint Cutscene Maker (OFP) | A list of moves, two shown at once; actor freeze; import limited to simple scripts | Its Fwatch dependency |

## 2. The engine's cinematic toolbox

CWR 3.05 and CE share this runtime [V, file hashes above]. For legacy 1.99, BIKI tags the cam*, title, sound and move commands as
OFP 1.00 (`drop` as Resistance), but none has been probed on a 1.99 binary [U] (doc 23 §14.3). "All" below means registered in both
pinned trees and OFP-tagged; "Cwr/Ce" means Remastered-only or unknown on 1.99.

### 2.1 Where a sequence can run

| Host | Game mode | Started by | Lines per step | Campaign vars | Ends | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `Intro` section | GModeIntro | `initintro.sqs` (INT_MAX lines) | exec'd scripts: 100 | Yes, from `initintro.sqs` on, not in unit inits (doc 18 §8.2) | END/LOSE trigger (evaluated in intro mode) or Space/Esc | Needs ≥ 1 group (doc 04 §3) |
| `OutroWin` / `OutroLoose` | GModeIntro | Unit init or trigger; **no** `initintro.sqs` | 100 | No (doc 18) | Same | |
| `Mission` | GModeArcade | Trigger/waypoint activation, script | 100 | Yes | Mission end is **held** while a camera or title-layer effect is active, unless forced | Player suspended while a camera effect is active |
| Chapter cutscene | GModeIntro | `initintro.sqs` | 100 | No | Same as Intro | doc 18 §6.1 |
| `onPlayerKilled.sqs` | GModeArcade | Engine, respawn NONE only | default | — | Must call `enableEndDialog` | Single "camera script" slot |
| `exit.sqs` | GModeArcade | End already proceeding | INT_MAX | — | Simulated once, then the map is destroyed | Cannot host a sequence [I] |

Evidence: `CWR:UI/DisplayUIMenus.cpp#L1294-L1328` (intro init: campaign vars, `initintro.sqs` at INT_MAX), `#L1173-L1207`
(cutscene display: border on, Space/Esc via `BreakIntro` `#L710-L724`, exits on any end mode), `#L984-L995` (mission end gate, `exit.sqs`);
`World/WorldImpl.cpp#L541-L657` (END triggers counted in GModeIntro too); `World/Entities/Infantry/SoldierOldMove.cpp#L1068-L1086`;
`World/WorldSetup.cpp#L1409-L1428` [V]. Note that `forceEnd` only sets the "forced" flag (`Game/Commands/GameStateExtWorld.cpp#L781-L785`);
the end mode itself comes from an END/LOSE trigger, so a sequence ends a section through a generated END trigger [V].

### 2.2 Camera commands

| Command | Signature | Semantics and gotchas | Profiles |
| --- | --- | --- | --- |
| `camCreate` | `Object <- String camCreate Array` | Any non-AI vehicle at `[x,y(,hAGL)]`. Class `simulation` decides: `camera` → controllable camera; `seagull` → camSet*/commit do nothing and `camCommitted` is always true. Use `"camera"` only | All |
| `cameraEffect` | `Object cameraEffect [name, pos]` | `name` from `CfgCameraEffects >> Array` (mission → campaign → config); `pos` one of 14 (`TOP`, `LEFT`, `RIGHT`, `FRONT`, `BACK`, `LEFT FRONT`, `RIGHT FRONT`, `LEFT BACK`, `RIGHT BACK`, `LEFT TOP`, `RIGHT TOP`, `FRONT TOP`, `BACK TOP`, `BOTTOM`). An invalid `pos` is a **silent no-op, even for `"terminate"`**; a null object returns early. Infinite on a camera object or in intro mode | All |
| `camSetPos` / `camSetRelPos` | `Object camSetPos Array` / `[right, forward, up]` | Stored until commit. RelPos is resolved **once**, at the call, against the last *set* target (committed or not): an object's current heading with world up; a point target gives plain world-axis offsets; with no target ever set it is an absolute sea-level position. It does not follow | All |
| `camSetTarget` | `Object camSetTarget Object\|Array` | Look-at. An object target is tracked live; a point is fixed. Only Object and Array overloads exist | All |
| `camSetFov` | `Object camSetFov Scalar` | Sets min = max, so a fixed lens per commit; default 0.7; interpolated linearly | All |
| `camCommit` / `camCommitted` | `Object camCommit Scalar`; `Bool <- camCommitted Object` | Moves over *t* s of game time (≤ 0 = instant). `camCommitted` is true once game time passes the **latest** deadline so far. Returns Nothing on a non-camera | All |
| `camDestroy` | `camDestroy Object` | Deletes a camera object; does **not** end the view: the effect freezes on the last frame at FOV 0.7 and stays active (player suspended, mission end held) until a `terminate` is issued through some *other* live object | All |
| `camCommand` | `Object camCommand String` | `"manual on/off"`, `"inertia on/off"`; the capture tool (§4.4) | All |
| `camSetDive` / `camSetBank` / `camSetDir` | `Object … Scalar` | All three bound to the dive handler. The dive, bank and heading fields are stored and saved but read nowhere, so even a correct binding would do nothing: **no effect** on 3.05/CE; 1.99 [U] | Never emit |
| `camSetFovRange` | `Object camSetFovRange Array` | Empty handler: **no effect** (BIKI: non-functional) | Never emit |
| `switchCamera` / `cameraOn` | `Object switchCamera String`; `Object <- cameraOn` (nular getter) | Moves the normal view to that object in a mode (`INTERNAL`, `GUNNER`, `EXTERNAL`, `GROUP`, `CARGO`) for the return to play; unknown string is a silent no-op | All |
| `showCinemaBorder` / `disableUserInput` | `showCinemaBorder Bool` / `disableUserInput Bool` | Border drawn only while a camera effect is active; reset to on at every mission/cutscene display. Input lock is a **counter** (§2.7) | All |

Evidence: `CWR:Game/Commands/GameStateExt.cpp#L901, #L1037-L1038, #L1064-L1065, #L1341-L1356` (CE `#L1339-L1354`); `Game/Commands/GameStateExtUi.cpp#L1369-L1639`;
`World/Scene/Camera/CameraHold.hpp#L58-L81` (setters; dive/bank/heading only stored); `World/World.hpp#L81-L99`, `World/World.cpp#L873-L893` (effect on a deleted object);
`World/Scene/Camera/CamEffects.cpp#L32-L48`; `World/Entities/Vehicles/VehicleTypes.cpp#L749-L756` (dispatch on `simulation`) [V].

### 2.3 The motion model: what the camera can and cannot do [V unless marked]

- **Commit semantics.** Each `camCommit t` copies the pending position, target and FOV into "move to X by time T". Position then moves
  at speed = remaining offset / remaining time, re-planned every frame: a straight line at constant speed, no easing
  (`CameraHold.cpp#L288-L324`, `#L557-L591`). `camCommit 0` applies at once through an immediate `Simulate(0)`.
- **Aim.** When the target changes, aim interpolates direction and distance separately, from the *previously committed* target to the
  new one. Re-committing a target mid-transition can therefore jump [I from `#L210-L249`, `#L567-L574`]. Orientation is always
  "look at target, world up" (`#L251-L276`): pitch comes only from where the target sits, and roll is impossible.
- **FOV only with a target.** FOV and orientation are applied only once a target point exists; a camera never given a target keeps its
  old heading and renders at FOV 0.7 whatever `camSetFov` says (`#L251-L276`). The last target point is cached and never cleared, so
  once a camera has had a target it re-aims at that point forever. Points within about 0.7 m of the map origin count as "no target".
- **FOV re-timing.** Commit clears the "position set" and "target set" flags but never the FOV flag (`#L575-L580`), so after the first
  `camSetFov` every later commit re-times the FOV move to *its* deadline: a `camCommit 0` snaps an unfinished zoom, and a short
  segment finishes a long zoom early. Sampled segments must therefore each emit their own `camSetFov`.
- **Heights.** Positions are `[x, y]` or `[x, y, height above terrain or sea]` (`GameStateExtGrp.cpp#L885-L951`). The rendered camera
  is clamped to ≥ 0.1 m above the surface every frame, so a straight segment over a ridge skims the ground rather than clipping
  (`World/World.cpp#L1208-L1221`); the aim is still computed from the unclamped position.
- **FOV to angle.** The FOV value is the tangent of the half-angle before an aspect factor: tan(horizontal half) = FOV × `leftFOV`,
  tan(vertical half) = FOV × `topFOV` (`World/World.cpp#L1245-L1248`; `World/Scene/Camera/Camera.cpp#L27-L32`). Remastered defaults are
  4:3 = 1.0 × 0.75 and Hor+ above 4:3 (`topFOV` fixed at 0.75, `leftFOV` = 0.75 × aspect), unless the player set a custom FOV
  (`UI/Settings/AspectRatio.cpp#L12-L14, #L144-L165`; `UI/Settings/Presentation.cpp#L49-L73`). So FOV 0.7 is about 55° vertical at
  any aspect of 4:3 or wider, and 70° to 86° horizontal from 4:3 to 16:9. The 2D wedge draws the vertical angle exactly and the
  horizontal angle as a bracket over common aspects [I]; harness screenshots confirm it (§4.2). 1.99's factors are [U].
- **Clock.** Commits, script waits and title fades all run on game time, which `setAccTime` scales (`World/World.cpp#L213, #L334`).
- **Absent on every profile:** roll, independent pitch/heading, auto-zoom, camera shake, post-processing, NVG, preload/pre-stream, and
  a way to detect the end of speech (grep of both trees; §2.5). **Possible but probe-gated:** on a camera that has *never* had a
  target, the internal view copies the object's own transform every frame, so `setDir` (heading) and on Cwr/Ce `setVectorDir`,
  `setVectorUp` or `setVectorDirAndUp` (pitch and roll) should orient it. That is the mechanism [V]; the visual result is unprobed [U],
  and such shots are stuck at FOV 0.7 (`Game/Commands/GameStateExtGrp.cpp#L1849-L1861`; `GameStateExtWorldConfig.cpp#L1279-L1323`;
  `GameStateExt.cpp#L1436-L1438`; `World/Scene/Camera/CamEffects.cpp#L254-L297`).

### 2.4 Overlays: the cut layer and the title layer [V]

Two layers; the cut layer is drawn first and the title layer on top. Each holds **one** effect, and a new one replaces the old
(`World/World.cpp#L833-L854` simulation, `#L1646-L1652` draw order). `titleText`/`titleRsc`/`titleObj`, trigger and waypoint
effect titles, and `say` subtitles (as PLAIN DOWN) all use the **title** layer; `cutText`/`cutRsc`/`cutObj` and `titleCut` (bound to the cut handler) use the **cut** layer
(`World/WorldSetup.cpp#L1366-L1376`; `Audio/DynSound.cpp#L275-L301`; `Game/Commands/GameStateExt.cpp#L1000-L1008`).

| Effect | Behaviour (× speed; a larger speed is slower) |
| --- | --- |
| PLAIN, PLAIN DOWN | Text: 2 s fade in, 10 s hold, 1 s fade out |
| BLACK, BLACK OUT | 1 s fade to black, then held "forever" (hold 1e20 s) |
| BLACK FADED | Black overlay with the normal text timing |
| BLACK IN, WHITE IN | Fade from colour over 1 s |
| WHITE OUT | Like BLACK OUT in white: 1 s fade, then held "forever" |

Unknown effect names are silent no-ops. Speed 0 makes the effect end within a few frames (even a held BLACK OUT), and a negative
speed never ends; the compiler treats both as lint errors (`TitEffects.cpp#L137-L158`). `titleRsc`/`cutRsc` and `titleObj`/`cutObj`
ignore speed. An `RscTitles` `fadeOut` overwrites `fadeIn` and the fade-out is always 1 s. `titleObj`/`cutObj` read only the global
`CfgTitles`, never `description.ext` (`Game/TitEffects.cpp#L476-L625`). **End gate:** a mission does not end while a camera effect or
a *title*-layer effect is active, unless forced; cut-layer effects do not block (`UI/DisplayUIMenus.cpp#L984-L986`). A title-layer
BLACK OUT or WHITE OUT therefore blocks the ending until `forceEnd`, and each `say` subtitle holds the title layer for 13 s × its
speed, so the last subtitled line delays a mission end by up to 13 s. The gate exists only in the mission display: Intro and Outro
sections end on the first frame with an end mode, cutting off any running fade or subtitle (`UI/DisplayUIMenus.cpp#L1202`).

### 2.5 Sound, music, dialogue and radio [V unless marked]

| Command | Use | Gotchas | Profiles |
| --- | --- | --- | --- |
| `say` (`Object say String` / `[name, maxTitlesDist, speed]`) | Positional (3D) line from a `CfgSounds` class | Subtitles from `titles[]`, shown only if the player option is on or the class sets `forceTitles`; hidden beyond 100 m from the camera (array form: 0 = unlimited). A talking Person queues lines; dead speakers say nothing | All; array form Cwr/Ce, 1.99 [U] |
| `playSound` | 2D sound or voice-over | `titles[]` show under the same option/`forceTitles` gate, with no distance limit. A class with titles and no sound file shows only the subtitles, which is a vanilla path for text-only lines | All |
| `playMusic` / `fadeMusic` / `fadeSound` | `CfgMusic`; `t fadeMusic v` | `""` stops; `[name, start]` form | All; array form Cwr/Ce |
| `sideRadio` / `globalRadio` / `groupRadio` / `vehicleRadio`, `*Chat` | `CfgRadio` (single `title` shown in chat) | Outside MP **every** radio channel is off without a living real player; group/vehicle channels are always off in intro mode; radio audio is skipped while `setAccTime` > 1 (`AI/AIRadio.cpp#L1445`) | All |
| `soundLength` | Clip length in s (0 if unresolved) | Remastered addition (no BIKI page) | Cwr/Ce |
| `setMimic`, `playMove`, `switchMove` | Faces and animations (Man only) | Move names from the unit's `Moves >> States`; `switchMove` snaps and re-queues the previous external move at the front; unknown names only debug-log, and `switchMove` with an unknown name snaps the unit to its default move | All |

Evidence: `Game/Commands/GameStateExtUi.cpp#L878-L1156`; `Audio/DynSound.cpp#L125-L301`; `World/WorldSetup.cpp#L878-L932`;
`AI/AIRadio.cpp#L1429-L1442`; `World/Entities/Infantry/SoldierOldMove.cpp#L364-L411`; `World/Entities/Infantry/SoldierOld.cpp#L90-L98`.
Consequence: **`say` is the only dialogue path guaranteed audible in a cutscene**, and it is positional, so a speaker far from the
camera is quiet and loses subtitles [I on loudness]. A `say` by a Person waits while that unit is still speaking directly *or on the
radio* (`DynSound.cpp#L159-L234`), so an AI report can push a line past its cue; staged actors should have their radio quiet [I].

### 2.6 Actors, time and weather [V unless marked]

- **Staging:** `setPos`, `setDir`, `move` (group order), `stop`, `disableAI`, `setBehaviour`, `setSpeedMode`, `setUnitPos`,
  `setCaptive`, `allowDammage` are registered (`Game/Commands/GameStateExt.cpp#L1220, #L1236-L1243, #L1297-L1309`); per-profile availability
  comes from the doc 23 catalog. AI motion during a scene cannot be predicted by the editor.
- **Time:** `setAccTime` (unclamped; forced to 1 every frame in MP; scales cameras, fades and waits), `skipTime` hours (moves the
  clock of day only, not game time, so `&t` cues do not shift); `setDate` is Cwr/Ce only (BIKI tags it OFP: Elite, unverified)
  (`#L1054, #L1071, #L1178`; `World/World.cpp#L185-L213`; `GameStateExtUi.cpp#L1757-L1769`).
- **Weather:** `setOvercast` and `setFog` share one weather setter that passes "keep current" for the other value, so each cancels the
  other's pending transition (`World/WorldSetup.cpp#L1285-L1317`). An instant change schedules immediate random drift. **Rain is gated by overcast:** forced to 0
  unless actual overcast exceeds about 0.673, then re-randomised within `[0, overcast*1.5-1]` (`Game/Commands/GameStateExtUi.cpp#L1807-L1823`;
  `World/Terrain/Landscape.cpp#L459-L465, #L558-L652`).
- **Map shots:** `mapAnimAdd`/`mapAnimCommit`/`mapAnimDone` and `forceMap` are registered (`#L890-L892, #L1073-L1074`); intro displays
  create the main map (`UI/DisplayUIMenus.cpp#L1294-L1308`). A camera effect forces the player's map closed every frame, but
  `forceMap` is ORed in when the map is drawn (`World/World.cpp#L524-L527, #L1565`; `World.hpp#L606`), so `forceMap true` is the
  likely route [I]. How a map shot actually renders mid-intro is [U].

### 2.7 SQS runtime rules that shape the compiler [V]

- An exec'd script runs at most **100 internal lines per step**; `initintro.sqs`, `init.sqs` and `exit.sqs` are unlimited. Excess
  lines slip to the next frame; this is a timing slip, not a failure (`Game/Scripting/Scripts.cpp#L441-L479`).
- `&t` waits until the script's `_time` ≥ *t* (absolute since script start); `~t` is two internal lines built in a 256-byte buffer,
  so expressions over about 233 bytes are truncated; `@cond` is re-evaluated every step (`#L253-L289`). `_time` is game time
  (`#L512-L533`), the same clock as camera commits.
- A non-Boolean `@` condition silently counts as false (`BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/express.cpp#L2773-L2782`),
  so an `@` on an undefined flag probably waits forever [I]: initialise every flag before reading it.
- A runtime error abandons the rest of that line only; the script goes on with the next line (`Scripts.cpp#L458-L470`;
  `express.cpp#L2918-L2986`). Outside AutoTest and `--strict` the error is only logged (`Game/Scripting/ExpressExt.cpp#L146-L175`). A
  driver therefore stalls not by crashing but on an `@` that never turns true, for example `@camCommitted` on a deleted camera,
  which returns Nothing and so reads as false forever (`GameStateExtUi.cpp#L1458-L1467`).
- Inside a line, `;` separates statements (`express.cpp#L2968-L2979`); only a line that *starts* with `;` is a comment. Source-map
  comments must be whole lines, or the text after `;` runs as code and errors (fatal under AutoTest).
- `disableUserInput true` increments a counter (the first call also clears held keys) and `false` decrements it; input is enabled
  while the counter is ≤ 0. An extra `false` breaks a later lock (`World/WorldSetup.cpp#L1342-L1356`). The counter is reset only when
  the World object is constructed (`World/WorldInit.cpp#L167`), not per mission. It is fed to the global keyboard update and
  discards all mouse input (`Input/InputProcessingSdl.cpp#L192-L227`), so a leaked lock outlives the mission (how far menus are
  affected is [U]).
- Setting a camera effect suspends the player (`World/WorldSetup.cpp#L1358-L1364`), forces the map closed and ignores
  view/optics/map keys (`World/World.cpp#L413-L527`).
- Engine death/respawn hooks share one "camera script" slot and terminate only the previous hook script; an exec'd sequence keeps
  running, but a hook may take the view [I] (`#L1409-L1428`).
- Comment lines (`;`) are never stored, so provenance comments cost nothing at runtime (`Scripts.cpp#L242-L244`).

### 2.8 The Effects dialog: the zero-script rung [V]

Triggers and waypoints carry `cameraEffect`/`cameraPosition`, sound, voice, environment, trigger SFX, music and a title (text,
resource or object) (doc 03 §4.8). In missions a static camera effect lasts 10 s, internal 2 s, and an interpolated one its last
keyframe time; all are infinite in intros; `$TERMINATE$` ends the view (`World/Detection/Detector.cpp#L1331-L1529`;
`World/Scene/Camera/CamEffects.cpp#L153-L162, #L367-L450`). The script setters (`setCameraEffect`, `setTitleEffect`, …) store unknown enum
strings as −1, and firing such a trigger probably crashes [I] (`Game/Commands/GameStateExtWorldWaypoint.cpp#L569-L644`).

### 2.9 Engine defects the compiler routes around

`camSetBank`/`camSetDir` bound to the dive handler; the `camSetFovRange` stub; the `RscTitles` fadeOut overwrite; an unknown
`cameraEffect` name dereferenced after a suppressed warning (probable crash [I], `UI/OptionsUI.cpp#L492-L496, #L588-L625`); effect
setters storing −1; the capture tool writing `camSetTarget '<debugName>'`, which no overload accepts (single quotes are not string
delimiters); the manual camera's lock loop examining only the first collision result (`CameraHold.cpp#L426-L439`). Each becomes a
lint (§3.7) and a candidate upstream CE issue, filed through `docs/design-gap-requests/` [I].

## 3. The cinematics timeline

### 3.1 Place on the ladder [I]

Rung 4 of the no-code ladder. Rung 1 attributes (actor poses, identities) and rung 2 modules (a "death cam" or "ending sequence"
module) *use* sequences; rung 3 rules start them ("when objective 2 completes, play `seq_bridge`, then END2"). Rung 5, the script
editor, shows the generated driver read-only and supports "eject to script". A sequence is a typed model; SQS is its build output.

### 3.2 Tracks

| Track | Clips | Compiles to | Rules enforced by the model |
| --- | --- | --- | --- |
| **Shots** | Shot = entry (cut or move) + ≥ 1 camera key (eye, look-at, FOV, ease) | `camSetTarget`/`camSetPos`/`camSetRelPos`/`camSetFov`/`camCommit` segments | No overlaps; every key has a look-at; eye ≥ 0.5 m above surface; FOV in 0.01–2.0 [I range from the manual camera clamp] |
| **Cut layer** | Fade (8 effects), text, `RscTitles` card | `cutText`/`cutRsc` | One clip at a time; **default home of fades** |
| **Title layer** | Title card, caption | `titleText`/`titleRsc`/`titleObj` | Shared with `say` subtitles: overlaps with subtitled lines are errors |
| **Music** | Cue, fade | `playMusic`, `fadeMusic` | `CfgMusic` generated from the audio library |
| **Sound** | 2D SFX, positional voice | `playSound`, `say` | Classes generated |
| **Dialogue** | Screenplay line: speaker, text, channel, audio | `say` / radio / `*Chat`; `CfgSounds titles[]` or `CfgRadio title`; `.lip` | Channel legality per host (§2.5); duration from audio, or reading speed for a text-only line |
| **Actors** | Stage (place at mark), move order, pose, mimic, protect, freeze | `setPos`/`setDir`, `move`, `playMove`/`switchMove`, `setMimic`, `allowDammage`/`setCaptive` | Staging snaps happen only under a cut or fade [I] |
| **World** | Skip time, time scale, weather, date; any doc 31 §5.2 rule action (effect preset, destroy, marker, flag) in its rule-builder form | `skipTime`, `setAccTime`, `setOvercast`/`setFog`/`setRain`, `setDate`; the action's own lowering | Rain raises overcast ≥ 0.7 first; `setDate` Cwr/Ce only; `setAccTime` never 0 |

**Presentation** (per sequence, not a track): cinema border on/off (explicit, since the engine resets it), input lock (off by default
for camera-only scenes because the camera effect already suspends the player), skip policy (sections: engine Space/Esc; in-mission:
none until the probe in open question 6), actor protection (on by default).

**Product rules [I].** *Script clips:* a lane below the tracks holds SQS snippets at a cue (hand-written, or opaque lines from
import, §3.8), edited in the rung-5 language service with doc 23 lints and doc 24 caps, so the ceiling is one clip away, not a
whole-sequence eject; a clip that touches the sequence camera or input lock is warned. *Text-only lines* (most hobby authors record
no voice) compile to title-layer captions ("Speaker: text") timed by reading speed; attaching a WAV or a voice-plugin take (doc 22)
later switches the line to `say` and re-times it. *Live scenes:* a sequence with no shots emits no camera effect, border or input
lock, so dialogue, radio and actors can fill a transport leg while the player keeps control (doc 28 "dead air").

### 3.3 Authoring on the 2D map [I]

- **Eye and look-at.** Each key draws an eye dot, a look line to its target and a horizontal FOV wedge. The path between keys is
  drawn exactly as the engine will fly it: straight segments, or the sampled curve for eased keys. An object target draws a dashed
  "tracks live" line.
- **Height is a first-class number.** Keys carry labels such as "35 m AGL". A terrain-profile strip under the timeline plots the
  selected shot's path against ground height from the WRP heightmap the map renderer already loads (doc 05, doc 07). Clearance below
  2 m, where the engine clamp would skim the ground, is flagged. A side gauge shows pitch as `atan(Δh / distance)` to the target.
- **Direct manipulation.** Drag eye, target and wedge edges; Alt-drag to change height; "look at" snaps to units, objects and map
  features; "frame this" computes an FOV from subject size and distance.
- **Shot list lane and storyboard.** A lane of shot sections with names, durations and thumbnails (from the harness when available,
  otherwise an optional heightfield-silhouette sketch rendered from the heightmap). Reorder by drag; a cut is a hard edge, a move a ramp.
- **Director's view.** One workspace (map, timeline, screenplay, thumbnail), keyboard-first (J/K/L scrub, `,`/`.` step by cue). A
  "take" plays the harness filmstrip, "coverage" proposes an alternative angle for the selected shot, a tempo meter shows shot lengths
  against music bars when a cue has a BPM tag, and cutting on a dialogue line or a music accent is one click.

### 3.4 Typed model (proposal-only sketch)

```rust
// Proposal-only. Fields private, constructors enforce invariants; newtypes follow AGENTS.md (from_raw/to_raw/Display).
pub struct CineSequence {
    id: SequenceId, title: String, host: SequenceHost, tracks: Tracks, presentation: Presentation,
    origin: Provenance, // User | Template(TemplateId) | Ai { step: StepId, model: ModelTag } | Import { file, span }
    pin: PinState,      // Pinned | Free: regeneration never touches Pinned (AGENTS.md)
}
pub enum SequenceHost { Intro, OutroWin, OutroLoose,               // mission.sqm sections, intro mode
    InMission { start: StartRef }, CampaignCutscene(CampaignNodeId), DeathCam } // DeathCam: onPlayerKilled.sqs, respawn NONE only
pub struct Shot { id: ShotId, span: Span, entry: Entry, keys: NonEmpty<CamKey> }
pub enum Entry { Cut, MoveFromPrevious }  // Cut = camCommit 0 at span start
pub struct CamKey { at: Millis, eye: Eye, look: LookAt, fov: Fov, ease: Ease }
pub enum Eye { World { x: Metres, z: Metres, above_surface: Metres },
               Relative { to: ActorRef, right: Metres, forward: Metres, up: Metres, follow: Follow } }
pub enum Follow { SnapshotAtKey, Resample { every: Millis } } // camSetRelPos is a snapshot (§2.3)
pub enum LookAt { Point { x: Metres, z: Metres, above_surface: Metres }, Actor(ActorRef) } // no "none": FOV needs a target
pub enum Ease { Linear, In, Out, InOut }    // non-linear kinds compile by sampling
pub struct Fov(f32);                        // engine units, default 0.7
pub enum OverlayEffect { Plain, PlainDown, Black, BlackFaded, BlackOut, BlackIn, WhiteOut, WhiteIn } // closed set
pub enum Channel { Say, VoiceOver, Side, Global, Group, Vehicle, Caption }  // legality per host; Caption = text-only line
pub struct Tracks { shots: Vec<Shot>, cut_layer: Vec<OverlayClip>, title_layer: Vec<OverlayClip>, music: Vec<MusicCue>,
    sound: Vec<SoundCue>, lines: Vec<LineCue>, actors: Vec<ActorCue>, world: Vec<WorldCue>,
    script: Vec<ScriptClip> } // LineCue → ScreenplayLineId; ScriptClip = SQS text at a cue (escape hatch, §3.2)
```

Model invariants are checked at construction, not at compile time: overlaps per exclusive track, a target on every key, channel
legality per host, and the profile floor (computed from the commands a sequence will need, shown as a badge).

### 3.5 Compilation

**Pipeline (pure, deterministic) [I].** (1) Resolve actors to mission names (unnamed actors get generated `ofpe_a_<n>` names in
`mission.sqm`) and assets to classes. (2) Gate by profile through the doc 23 catalog. (3) Lower all tracks to one time-sorted cue
list. Eased keys and `Resample` follows are sampled into short linear segments (default 4 Hz, a quality setting). A segment's
target changes only at or after the previous deadline, so aim never jumps. (4) Emit the driver, a guard, host hooks,
`description.ext` classes (`CfgSounds`, `CfgMusic`, `CfgRadio`, `RscTitles`, `CfgIdentities`) in fenced regions, and an END trigger for
section hosts. (5) Verify: re-parse; doc 23 parity and lints; the ~233-byte `~` and 4095-byte line limits; ≤ 90 lines between waits;
source map. Output is byte-stable.

**Timing [V mechanics, I design].** Cues use absolute `&t` on the script's `_time`, and commits run on the same game clock, so drift
cannot accumulate. A cue may start up to one frame late, and the next commit re-plans from wherever the camera is. For Cwa199,
dialogue durations are measured from WAV/OGG/WSS at import (doc 07 §12). On Cwr/Ce the author may instead use `soundLength` pacing.

**Example output (abridged; the real file carries a source-map comment per cue).**

```sqf
; ofp-editor:generated seq=intro_dawn model=3f9a61c2 (edit the timeline, or eject to script)
ofpe_seq_intro_dawn_done = false
ofpe_cam = "camera" camCreate [4520, 10210, 60]
ofpe_cam cameraEffect ["internal", "back"]
showCinemaBorder true
cutText ["", "BLACK IN", 2]
playMusic "ofpe_m_dawn"
; shot 1 "Valley" 0.0-8.0 s: dolly with fixed look-at
ofpe_cam camSetTarget [4700, 10400, 5]
ofpe_cam camSetPos [4520, 10210, 60]
ofpe_cam camSetFov 0.7
ofpe_cam camCommit 0
ofpe_cam camSetPos [4610, 10300, 35]
ofpe_cam camCommit 8
titleText ["Everon, 1985", "PLAIN DOWN", 0.4]
&8
; shot 2 "Sergeant" 8.0-14.0 s: cut, relative framing (snapshot)
ofpe_a_sgt setDir 135
ofpe_cam camSetTarget ofpe_a_sgt
ofpe_cam camSetRelPos [1.5, 3, 1.7]
ofpe_cam camSetFov 0.45
ofpe_cam camCommit 0
ofpe_a_sgt say "ofpe_l_0001"
&14
cutText ["", "BLACK OUT", 1]
&15
ofpe_cam cameraEffect ["terminate", "back"]
camDestroy ofpe_cam
ofpe_seq_intro_dawn_done = true
```

The title card lasts 13 × 0.4 = 5.2 s, so it has left the title layer before the subtitled line at 8 s [V timing]. Terminating
through `ofpe_cam` rather than `player` matters: in a section without a player unit `player` is probably null, and `cameraEffect` on
a null object returns early (`GameStateExtUi.cpp#L1371-L1375`) [I].

**Safety [I design on V mechanics].**

- *Epilogue on every path:* terminate through the camera object with a valid position, then `camDestroy`; restore the border; issue one
  `disableUserInput false` per `true`; restore `enableRadio` and `setAccTime`; lift a held cut-layer blackout (`BLACK IN`) when
  returning to play; release frozen actors.
- *Watchdog:* `ofpe\cine\<seq>_guard.sqs` waits on `@(ofpe_seq_<id>_done || _time > <length + 5>)`. If the flag never came, it runs the
  same epilogue. On CWR/CE an SQS script survives runtime errors (§2.7), so the watchdog guards against *stalls*: an `@` that never
  fires, a deleted camera, a driver ended by `exit` or a bad `goto`, or a death-cam driver replaced by the next hook (§2.7). Because a deleted camera cannot carry the `terminate`, the
  epilogue terminates through the camera if it is alive and otherwise through the sequence's generated Game Logic (any live object
  works: `terminate` ignores its target, `GameStateExtUi.cpp#L1369-L1413`; `CamEffects.cpp#L653-L690`). The driver keeps its lock
  count in a variable so the epilogue can release exactly that many. 1.99 error behaviour is [U].
- *Endings:* a sequence that ends a mission sets a flag read by a generated END*n* trigger. An END*n* fires only when **every** END*n*
  trigger of that number is active at once (`World/WorldImpl.cpp#L556-L651`), so the compiler must own that END number or route the
  author's END*n* triggers through the flag; adding a second END2 next to a hand-made one can stall the ending. In a mission the
  camera effect itself holds the end, so the driver terminates the view before raising the flag. Fades stay on the cut layer, so
  the gate cannot hang (a last subtitle can delay it by up to 13 s); if a title-layer effect must persist, the compiler emits
  `forceEnd`. In sections an END cuts at once (§2.4), so the flag goes up only after the last fade has finished.
- *Actors:* protection (`allowDammage false`, optional `setCaptive true`) for the scene, released in the epilogue.
- *Hooks:* host hooks are one fenced line each (`initintro.sqs`, a Game Logic init, a trigger activation).

**Per-profile lowering.**

| Feature | Cwa199 | Cwr305 / Ce |
| --- | --- | --- |
| Dialogue pacing | Measured durations baked into `&t` | Same by default; `soundLength` optional |
| Subtitles for distant speakers | Warn: 100 m limit (array `say` [U]) | `say [name, 0, 1]` |
| Music start offset | Not offered [U] | `playMusic [name, t]` |
| Date change | Not offered | `setDate` |
| Free heading/roll on a target-less shot | Not offered | Offered only after the §7 probe passes |
| Live preview | Export + stock editor section Preview | Harness (§4) |

### 3.6 Hosts: where a sequence attaches [V engine, I compile]

| Host | Hook | Ending | Notes |
| --- | --- | --- | --- |
| Intro | Fenced `[] exec` line in `initintro.sqs` | Flag → generated END1 trigger in the Intro section | State variants allowed (campaign vars from `initintro.sqs` on) |
| OutroWin / OutroLoose | Init field of a generated Game Logic in that section | Same | No campaign vars: variant-by-state disabled (doc 19 §6.5, lint C16) |
| In-mission | Rule action, trigger or waypoint On Activation | Returns to play, or flag → END*n* | Player suspended by the camera; MP: runs on every client [U] |
| Campaign Cutscene node | Its Intro (group-less Mission, exits via `lost`) | As Intro | doc 18 §8.2, doc 19 §6.1 |
| Chapter cutscene | Its `initintro.sqs` | As Intro | No campaign vars |
| Death cam | Mission-local `onPlayerKilled.sqs` with `_this = [unit, killer]` | Must call `enableEndDialog` (the engine disables it first) | Respawn NONE only. The engine starts the hook only if the global `scripts\onPlayerKilled.sqs` exists, then resolves the name mission-first, so a mission copy overrides the default (`SoldierOldMove.cpp#L1068-L1084`; `UI/OptionsUI.cpp#L630-L655`); that the stock data ships the global file is [U] |
| Effects shot (rung 1) | Trigger/waypoint `class Effects` fields | Effect lifetime | One preset shot; no script; validated enums only |
| Gameplay camera (doc 31 row 41: bullet, helmet, overhead) | A module action, radio slot or event | Toggle off, subject lost or timeout, then the §3.5 epilogue | A live camera, not a timeline: a `Resample`-style follow of a runtime subject; reuses wrapper, watchdog and lints; never the hook slot (doc 31 §4.5); per-gadget lowering [U] |

Every section host also needs ≥ 1 group, which the compiler guarantees with its Game Logic (doc 04 §3). A **film preset** (the
VideoMissions genre) chains sequences with chapter markers and turns the length and spin style notes off; its host (Intro or
Mission) waits on the §4.3 staging results [I].

### 3.7 Lints (all visible on the map and the timeline)

Errors: `camSetDir`/`Bank`/`Dive`/`FovRange` anywhere (no effect); unknown `cameraEffect` names or positions (including `terminate`);
unknown title effects; an enum setter with a non-enum string; `camSetTarget '<name>'`; title-layer clips overlapping subtitled lines;
group/vehicle radio in a section; side/global radio in a section without a living player unit; `setAccTime 0`; speed ≤ 0; a
title-layer BLACK OUT or WHITE OUT before an END trigger without `forceEnd`; unbalanced input lock; a path without terminate + destroy,
or `camDestroy` before `terminate`; a generated END*n* sharing its number with another END*n* trigger; a trailing
`; comment` on a code line (it runs as code); `@camCommitted` on a camera the script may delete; a section without a group; `setDate`, `soundLength`
or array `say`/`playMusic` in Cwa199 output.
Warnings: eye below 2 m clearance; `camSetRelPos` with no target set yet (absolute sea-level position); a sampled FOV move whose
segments do not each set the FOV (§2.3); a `titleObj`/`cutObj` class missing from the global `CfgTitles`; target directly above/below the eye (degenerate look-at [I]); a relative shot on a moving actor
without `Resample`; a far cut with no fade or lead-in (no preload); a speaker far from the camera; `setRain` below overcast 0.7; separate
`setOvercast`/`setFog` transitions; subtitle reading speed above a configurable threshold; a whole sequence over a length threshold
without a skip path.
Style notes (advisory taste, never blocking, dismissible per sequence as "intentional"): shots over a length threshold; continuous
orbits over 90° or slow zooms (the doc 28 "novice" signs). They teach rather than nag; acceptance tests count only errors and warnings.

### 3.8 Import and round-trip [I]

- **Capture blocks** (`;=== h:mm:ss` headers; fixed shape): high-confidence lift to keys. Quoted debug-name targets are flagged and
  resolved to the object nearest the captured point.
- **Camera scripts** of the classic shape (`camCreate`, `cameraEffect`, runs of `camSet*` + `camCommit` + `~t`/`@camCommitted`, plus
  `titleText`/`cutText`/`playMusic`/`say`/`*Radio` lines): lifted into a sequence. Unknown lines become **opaque script clips** pinned
  at their time; control flow (`goto`, `?`, loops) keeps the file as script with a read-only timeline *reading*.
- **Replace vs wrap:** "replace" only when re-emitting reproduces the normalised original tokens; otherwise "wrap" keeps the file and
  shows the timeline as an overlay (doc 19 §7.6 Preserve / Adopt / Eject). Import followed by save with no edits is byte-identical.
- **Dead commands** are shown struck through ("no effect on 3.05/CE; 1.99 unknown"), never silently removed. FCM exports need a
  recogniser written against its documented output [U].
- **Scripters keep the tools.** The same reading runs live in the rung-5 editor for hand-written camera scripts: path, wedges and
  lints appear on the map while typing, a position literal can be dragged on the map (only that literal is rewritten), and
  "insert capture" pastes the latest capture block at the cursor.

## 4. Preview

### 4.1 What each tier can show

The **2D map** is always available and exact for the camera path, look-at to fixed points, cue timing and layer occupancy, but not
for AI motion, animation, physics or streaming. The **shot preview** (Remastered/CE harness) frames each key exactly against a frozen
world with actors at their staged positions. The **full run** shows everything but cannot rewind [I].

### 4.2 Live shot preview on Remastered/CE [V building blocks, I design]

- **Launch** a staged copy as doc 08 P1 does (`--test-mission <stage> --window --no-splash --no-strict --harness 0`), with the
  driver *not* hooked, so the world stays still.
- **Exact mode:** `exec` `setAccTime 0` (game time stops, `World/World.cpp#L213, #L334`; a fully still world is [I]), then per key
  `eval` a generated snippet (reuse `ofpe_prev_cam`,
  `cameraEffect ["internal","back"]`, target, position, FOV, `camCommit 0`) and `screenshot{path}`: the PNG is the shot thumbnail.
  Scrubbing applies the editor-interpolated state at time *t* the same way (camera-exact, world-static). Never pair `setAccTime 0`
  with `"manual on"` (the manual camera divides by accTime, `CameraHold.cpp#L333`).
- **Quick framing:** `triSetView [px,py,pz,dx,dy,dz(,ux,uy,uz)]` pins the render transform in raw engine axes after the surface
  clamp; it can show roll and below-surface views that compiled shots cannot, and it leaves the FOV alone, so its thumbnails are
  badged "approximate" (`Game/Commands/GameStateExtTestAudio.cpp#L972-L999`, registered at `#L3051` (CE `#L981`, `#L3085`) with
  `--test-mission`, `--harness` or `--dev`, `#L2960-L2964`; `World/World.cpp#L1208-L1222`).
- **Filmstrip:** a full run with the driver hooked, screenshotting each cue; `triGetCameraEffectActive` (returns 1 or 0) at the end
  catches a stuck camera. `triSaveGame`/`triLoadGame` could give "play from shot N". The world save stores scripts (with `_time`) and
  the camera effect, but not the title or cut layers, the input-lock counter or the border flag, and the camera object does not
  save its committed move, target or deadlines (`World/WorldImpl.cpp#L1740-L1774`; `Scripts.cpp#L352-L403`; `CameraHold.cpp#L101-L114`;
  `GameStateExtTestAudio.cpp#L2797-L2830`). So a reload restores the driver but not an in-flight camera move or an overlay [I];
  "play from shot N" must re-issue each shot's full state and overlays, and whether saving works in intro mode is [U].
- **Calibration and risk:** screenshots at known distances fix the FOV-to-angle mapping (§2.3). Under `--test-mission` any script
  error aborts the process (doc 08 §2.4); snippets are pre-checked, but prefer doc 08's non-aborting launch when it exists.

### 4.3 Staging cutscene sections [V]

With a `Mission` section that has no groups, `StartAutoTest` falls back to the `Intro` section, initialises it in **intro mode** and
opens `DisplayIntro(noInit)`, which loads campaign vars and runs `initintro.sqs`
(`UI/DisplayUIMenus.cpp#L2020-L2034, #L2057-L2060, #L1225-L1230`). Two catches [V]: `StartAutoTest` first clears all campaign
vars (`UI/DisplayUIMenus.cpp#L2039`; `AI/AICenter.hpp#L555`), so a state variant previews only if the staged `initintro.sqs` sets
the variables itself; and when the staged Intro ends, the menu re-parses the group-less Mission and plays
**OutroLoose** (`UI/OptionsUIApp.cpp#L850-L875`), so the stage empties OutroLoose unless the chain is being previewed.
So: stage an Intro as-is with a group-less Mission; stage an Outro by copying it into `class Intro` and stripping `initintro.sqs`
from the stage, because real outros never run it [I]. This refines doc 08 §4.2's "copy the section into `class Mission`": that path runs in
arcade mode, where a section without a player unit either fails the single-player consistency check (doc 04 §3) or ends at once as
"killed" (`World/WorldImpl.cpp#L543-L551`), and radio and effect lifetimes differ [I]. The stock editor previews non-Mission sections the same way, and there too `initintro.sqs` runs for outros
(`UI/Map/UIMapExtDisplay.cpp#L566-L611`) [V]; our lint warns when an outro sequence depends on that file.

### 4.4 Capture from the game camera [V mechanics, I workflow]

The editor `exec`s `ofpe_cap = "camera" camCreate getPos player; ofpe_cap cameraEffect ["internal","back"]; ofpe_cap camCommand "manual on"`
(in a stage with no player unit it uses a generated Game Logic's position instead, since `player` is probably null there [I]).
The user flies with the engine's controls: move keys translate, numpad 4/6 turn, 2/8 pitch, +/− zoom (0.01–2.0), numpad `/` locks,
5 unlocks, Delete toggles inertia, V deletes the camera, which ends the view (`CameraHold.cpp#L325-L462`; `CameraHold.hpp#L128`).
Each Fire appends a block to `clipboard.txt`, opened on Windows relative to the game's working directory (after any `-C`), which our
launcher sets, and also copies it to the system clipboard when a clipboard backend is registered; the game deletes the file at
startup (`IO/Streams/QStream.cpp#L361-L376`; `Core/GameState.cpp#L283`). The editor tails the file and drops each block onto the
timeline at the playhead. Any turn or pitch input resets the target, locked or not, to a point 100 km ahead, so turning unlocks
(`CameraHold.cpp#L280-L286, #L387-L407`); moving without turning keeps a lock, so the view stays on the subject. The captured
`camSetTarget [x,z,h]` therefore keeps the aim, pitch included, but its `h` is relative to the surface at a point that is usually
off the island, so pulling it in to 1 km along the same ray [I] needs the engine's off-map surface height (unverified). A
`camSetRelPos` line appears only with a locked *object* and Left Shift held. On 1.99 the stock `camera.sqs` produces the same blocks;
the user imports `clipboard.txt` from the game folder (location [U]).

### 4.5 Legacy 1.99 [I]

No live link. "Test on 1.99" exports the mission and the user opens it in the stock editor, selects the section and presses Preview.
The Cwa199 profile's catalog gate and lints are the correctness guarantee; the §7 probe missions are the manual checklist.

## 5. Fun, UX and AI

The director's view is part of §3.3. This section covers templates, suggestions and the AI.

### 5.1 Shot templates (T0 data: typed schema + minijinja template, output re-parsed and linted; doc 22 §2.1)

| Template | Parameters (typed) | Compiles to | Default taste |
| --- | --- | --- | --- |
| Establishing orbit | Target, radius, height, arc°, duration, caption | Sampled `camSetPos` around a fixed look-at | Arc ≤ 60°, ≥ 6 s, no 360° spins |
| Fly-over | Road or path, height, look-ahead | Samples along the path; target leads by N m | Height clearance checked on the profile strip |
| Push-in / pull-out | Subject, start/end distance, FOV | Position + FOV samples | Stops short of the "slow zoom" lint |
| Reveal | Occluder side or low→high rise, subject | Crane-style samples, fixed look-at | Ends on a held frame |
| Over-the-shoulder pair | Speaker A, B, side | Two relative snapshots alternating on screenplay lines | Cuts on line starts |
| Tracking vehicle | Vehicle, offset, rate | `Resample` follow loop | Offset kept outside the vehicle's bounding box |
| Tripod hold | Position, subject | One key | Default for dialogue |
| Dolly zoom | Subject, travel, FOV range | Position and FOV sampled together | Short; one per sequence |
| Map pan (intro) | Map points, zooms | `mapAnimAdd`/`mapAnimCommit` | Gated on the map-shot probe [U] |
| Ending card | Text or RscTitles class, fade | Cut-layer fade + card + END flag | Always on the cut layer |

A template instance stays parametric: its map handles edit the parameters. Dragging one sampled key asks once to **bake** the
instance into plain keys (undoable), so nobody fights a template to nudge one frame [I].

### 5.2 Auto-cinematic suggestions [I]

Code scans the mission model and proposes, never inserts: an intro on the player's start when there is a transport leg ("convoy
tracking"); a reveal on an objective when it completes; a fade-and-card ending per END state; a death cam when respawn is NONE; a
dialogue scene where the screenplay has lines with no host. Each suggestion is a filled template the user can preview and accept.
**Shuffle** re-rolls its free parameters (side, arc, height) within the taste bounds and shows three seeded variants side by side
as thumbnails, so choosing a shot feels like picking takes, not filling a form.

### 5.3 AI assistance: weak models pick, code computes [I, doc 21/25 doctrine]

| Tool (typed, same command bus as the UI, undoable) | Model decides | Code does |
| --- | --- | --- |
| `cine.suggest(scene_intent)` | Rank candidate templates by mood and story beat | Computes candidates from the mission, island sites (doc 25 `island.sites`) and actors |
| `cine.fill(template_id, slots)` | Subject id, mood enum, duration bucket, caption text | Coordinates, heights, sampling, classes; validates; bounded repair by choice among code-computed fixes |
| `screenplay.write(scene, cast, beats)` | Lines of text per speaker | Channels, classes, timing, subtitle routing, reading-speed check |
| `cine.critique(seq)` | Phrase the lint findings for the user | Runs the lints; picks fixes |

The model never types a coordinate, class name or time; out-of-menu answers are rejected and re-asked. Generated elements carry
provenance (step, model) and are pinned once the user edits them. Stronger models may chain several templates in one step, but no
workflow requires it.

### 5.4 Accessibility and localisation [I]

Subtitles default on for generated lines, with an author toggle for `forceTitles` on story-critical lines. There is a reading-speed
lint, a flash lint for rapid WHITE IN/OUT or BLACK IN/OUT alternation, and colour-blind-safe track colours; the timeline is fully
keyboard-operable and the editor honours reduced motion. Titles and subtitles go through the stringtable (`localize` is registered,
`GameStateExt.cpp#L1052`; `$STR_` in config per doc 04), so every card and line is translatable.

## 6. Glass box [I]

- **See:** every sequence is visible on the map (paths, wedges, look lines), in the shot lane and in the hosts panel ("plays from:
  Intro via initintro.sqs line 3").
- **Inspect:** each clip shows why it exists (template, AI step and model, or import span), what depends on it (rules, END triggers),
  its lint status and its exact generated lines, highlighted through the source map.
- **Edit:** natively on the map and timeline; or eject to script. Generated regions are hashed. If a parameter literal (a coordinate,
  a time) is edited in the file, the edit flows back into the model (ParamEdited); any other edit marks the region Customized, and
  regeneration then offers a 3-way merge or keep-and-detach, never an overwrite. Detached regions are plain script; damaged fences
  are treated as user code. The mission must run with the sidecar deleted.

## 7. Phased plan and acceptance tests

| Phase | Delivers | Acceptance tests |
| --- | --- | --- |
| 0. Probes | In-game probe missions for every [I]/[U] item below; FOV calibration; design-gap entries (doc 08 staging refinement; upstream candidates in §2.9) | **AT1** each probe reports a vanilla observable; results recorded per profile |
| 1. Core | Model, compiler, map authoring for shots, overlays, music, `say`; text-only captions, script clips, live scenes; Intro/Outro/in-mission hosts; lints; capture-block import; 1.99 export path | **AT2** compiled output of 50 generated sequences passes doc 23 parity and all lints on all three profiles, with no Cwr/Ce-only command in Cwa199 output. **AT3** capture-block import reproduces positions within 0.01 m and FOV within 0.001 |
| 2. Live | Harness shot preview, thumbnails, filmstrips, capture from the running game; screenplay track with measured durations and `.lip` via `PoseidonTools sound lip` (doc 09 §6) | **AT4** for fixed-target shots, `getPos ofpe_cam` sampled at cues matches the 2D path within 0.5 m. **AT5** a killed driver is recovered by the watchdog: view, input and border restored within 6 s |
| 3. Craft | Templates, suggestions, shuffle, AI tools, follow shots, death cam, gameplay cameras, film preset, Cutscene nodes, map shots (if probed) | **AT6 (headline)** a newcomer authors a 30-second intro with 4 shots, a title card, music and radio chatter (radio via a protected living player unit, or `say` with radio styling) without writing script, previews it live on Remastered, and it passes every error and warning lint on all three profiles; moderated target ≤ 20 min [I]. **AT7** a 3–9B model through §5.3 produces 100% compiling sequences over 30 seeds with zero model-typed coordinates |
| 4. Round-trip | Classic camera-script lifting, live map reading of hand-written camera scripts, wrap/replace, ParamEdited flow-back, T0 template packs, MP in-mission sequences | **AT8** import → save without edits is byte-identical on a synthetic corpus. **AT9** edited literals flow back; other edits are never clobbered (doc 25 E9: clobbers = 0). **AT10** an in-mission ending sequence followed by END2 reaches the END2 debriefing with no hang, also in a mission that already has a hand-made END2 trigger (§3.5) |

Tests are synthetic and redistributable (AGENTS.md). The upstream `demo_end_*` family and `camcreate_any_type` are already tracked in
`docs/porting/upstream-test-map.csv` as probes; this work adds our own probes, not upstream rows.

## Open questions

1. **1.99 probes:** `camSetDir`/`camSetBank` (dive binding inherited?), `camSetFovRange`, array `say`/`playMusic`, `localize`,
   `forceMap`, and the capture tool's output (doc 08 Option 1).
2. **Free orientation:** the mechanism exists on CWR/CE (§2.3); the probe confirms the rendered result of `setDir` and
   `setVectorDir`/`setVectorUp` on a never-targeted camera (heading, pitch, roll at FOV 0.7).
3. **Freeze and snapshots:** does `setAccTime 0` freeze an SP world cleanly (game time stops by construction; physics and animation
   are [U])? Does a `triSaveGame` in intro mode work, and does a reload replay the camera effect correctly (§4.2)?
4. **Error recovery:** answered for CWR/CE (the script continues, §2.7); still open on 1.99.
5. **Radio in intros:** the code makes side and global radio audible when a living real player exists (group and vehicle radio
   stay off). Open: does such a player unit cause side effects (end-on-death rules, AI reactions) in an Intro?
6. **In-mission skip:** do radio menu keys (0-0-x) work during a camera effect, so a "skip" radio trigger is possible?
7. **Map shots:** how is the main map shown during an intro (`forceMap`?), and does `mapAnim*` render there?
8. **Edge behaviour:** `say` loudness versus camera distance; the engine's surface height off the island (capture import, §4.4).
   `playSound` subtitles, title speed ≤ 0, `camDestroy` without terminate and `@camCommitted` on a destroyed camera are answered from
   source (§2.2, §2.4, §2.5, §2.7) and need only confirming probes.
9. **FCM output format** for the importer (and a courtesy check with its author).
10. **MP:** do Intro/Outro sections play in MP, and must in-mission sequences start per client? Out of scope until phase 4.
11. One global `ofpe_cam` per mission (simple; sequences cannot overlap) or one per sequence? Proposal: one, plus an overlap lint.

## Verification notes

### Product review notes

Checked on 2026-09-27 against the owner direction (no-code first, scripting first-class, community patterns easy rather than hacky),
the AGENTS.md invariants and the prior-art pitfalls (hitting the ceiling, tedious forms, opaque output, visual spaghetti). The
timeline is linear and domain-specific, so spaghetti is not a risk here.

**Edits made in place [I].** *Ceiling:* a script-clip lane (§3.2, §3.4) keeps custom lines one clip away; hand-written camera
scripts get the live map reading (§3.8). *Coverage:* gameplay cameras, which doc 31 row 41 assigns to this rung, and a film preset
for VideoMissions (§1.3, §3.6); text-only captions for authors without voice audio; shot-less live scenes against "dead air"; doc 31
rule actions on the World track, so set pieces reuse the rule-builder forms instead of a second form set. *Tedium and taste:*
template instances stay parametric with an explicit bake (§5.1); Shuffle variants (§5.2); taste checks demoted to dismissible style
notes (§3.7).

**Still open.** *Drift from doc 31 §6:* its epilogue terminates through `player` (here: through the camera object), its prologue
always locks input in-mission (here: off by default), and its Map track claims `mapAnimAdd` works in intros [V] where this doc gates
map shots on a probe [U]; reconcile doc 31 or file a design-gap request. AT6's "`say` with radio styling" is undefined. 1.99-only
authors get no framing preview beyond the silhouette sketch. In-mission skip (open question 6) and MP sequences are the largest gaps
against community use. The doc is now ~640 lines; §2 could point to doc 31 §6.1 for the facts both docs repeat.

### Engine review notes (2026-09-27)

An adversarial pass tried to refute every engine claim against both pinned trees. **Confirmed [V]:** the dive binding of
`camSetDir`/`camSetBank` and the empty `camSetFovRange`; the straight-line, constant-speed commit and the "latest deadline" rule for
`camCommitted`; `&t` on game time; the 100-line step, the 256-byte `~` buffer and the 4096-byte line buffer; the 14 camera
positions and the silent no-op on a bad position; the shared title layer and the end gate; the radio gates; the `StartAutoTest`
intro fallback; the `clipboard.txt` append and delete; the debug-name capture form (the evaluator knows only `"…"` and `{…}`
strings, `express.cpp#L222-L257`); `forceEnd` only setting a flag; the rain threshold.

**Corrected in place.**

- WHITE OUT is held forever like BLACK OUT, so it also blocks the end (§2.4).
- The end gate is mission-only: sections end at once. `say` subtitles hold the title layer for 13 s × speed (§2.4).
- An END*n* needs *all* END*n* triggers active, so a generated END2 beside a hand-made one can stall. This affects §3.5 and AT10.
- `camDestroy` without `terminate` leaves a frozen, still-active effect, and a destroyed camera cannot carry the `terminate`. The
  watchdog now falls back to a Game Logic (§2.2, §3.5).
- The FOV flag is never cleared on commit, so every commit re-times the zoom (§2.3).
- The FOV-to-angle mapping is traced, Hor+ plus the player's custom FOV, so it is no longer [U] (§2.3).
- `camSetRelPos` resolves against the last *set* target, and with no target it gives absolute sea-level coordinates (§2.2).
- Any turn or pitch input resets the manual camera's target, locked or not, so turning unlocks (§4.4).
- `playSound` subtitles show, so they are no longer [U] (§2.5).
- SQS survives runtime errors on CWR/CE, which changes what the watchdog is for. A mid-line `;` is a separator, not a comment (§2.7).
- The input-lock counter survives across missions (§2.7).
- Staging clears campaign vars and plays OutroLoose after the staged Intro (§4.3).
- Save games keep scripts and the camera effect, but not overlays or the camera's in-flight move (§4.2).
- Weather cancellation is verified.
- Citations fixed: map and keys under a camera effect (`World.cpp`), `triSetView` (`#L972-L999`), `camDestroy`/`camCommitted` (`#L1064-L1065`),
  and the list of files that differ in CE.

**Still open or risky.**

- All 1.99 behaviour. In this source the dive, bank and heading fields are read nowhere, so 1.99 could honour them only if its
  binary differs from this code [I].
- The rendered result of free-orientation shots.
- The off-map surface height needed to import captures.
- Whether the stock data ships `scripts\onPlayerKilled.sqs`.
- How far a leaked input lock reaches into menus.
- Save/load in intro mode.
- The map-shot route.
- In-mission skip.
- `tri*` getters such as `triGetCameraEffectActive` register without the dev gate (`GameStateExtTestGetters.cpp#L534-L572`), which
  doc 23's command count should note.
- The AutoTest abort still makes any harness snippet error fatal.
- Length: these corrections push the doc to about 750 lines, well over the ~550 target. §2 is the place to trim, by pointing to
  doc 31 §6.1 for the facts both docs repeat.

## Sources

**Engine (pinned; `CWR:` per the header).** `Game/Commands/GameStateExt.cpp#L853-L1466` (registration; camera `#L1341-L1356`,
titles/sound `#L1000-L1013`, border/input `#L1037-L1038`, `localize` `#L1052`, map `#L1073-L1074, #L890-L892`, `setDate` `#L1178`,
`say` `#L1266-L1267`, moves `#L1276-L1277`, weather `#L1324-L1326`, `forceEnd` `#L884-L885`); `Game/Commands/GameStateExtUi.cpp`
(`#L878-L1156`, `#L1369-L1606`, `#L1641-L1823`); `Game/Commands/GameStateExtGrp.cpp#L866-L951, #L1849-L1861`;
`Game/Commands/GameStateExtWorld.cpp#L781-L785`; `Game/Commands/GameStateExtWorldWaypoint.cpp#L569-L644`; `Game/Commands/GameStateExtTestAudio.cpp#L972-L999, #L2797-L2830, #L2960-L2974, #L3051`;
`Game/Commands/GameStateExtTestGetters.cpp#L520-L572`; `Game/Commands/GameStateExtWorldConfig.cpp#L1279-L1323`; `Game/Scripting/ExpressExt.cpp#L146-L175`;
`BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/express.cpp#L222-L257, #L2773-L2782, #L2918-L2986`; `World/Scene/Camera/Camera.cpp#L27-L32`;
`UI/Settings/AspectRatio.cpp#L12-L14, #L144-L165`; `UI/Settings/Presentation.cpp#L49-L73`; `UI/OptionsUIApp.cpp#L850-L875`; `World/WorldInit.cpp#L90-L167, #L1001-L1091`;
`Input/InputProcessingSdl.cpp#L192-L227`; `AI/AICenter.hpp#L555`; `World/World.hpp#L81-L99, #L606`; `World/Entities/Infantry/SoldierOld.cpp#L90-L98`; `World/Entities/Vehicles/SeaGull.cpp#L841-L845`;
`World/Scene/Camera/CameraHold.cpp#L40-L92, #L200-L597`; `World/Scene/Camera/CameraHold.hpp#L32-L74`; `World/Scene/Camera/CamEffects.hpp#L26-L40`;
`World/Scene/Camera/CamEffects.cpp#L32-L48, #L153-L162, #L254-L297, #L367-L450, #L653-L690`; `Game/TitEffects.cpp#L35-L625`;
`Audio/DynSound.cpp#L125-L307`; `AI/AIRadio.cpp#L1429-L1442`; `UI/OptionsUI.cpp#L434-L773`; `Game/Scripting/Scripts.cpp#L97-L176, #L228-L606`;
`World/World.cpp#L92-L115, #L185-L214, #L334, #L413-L527, #L833-L899, #L1208-L1248, #L1565, #L1646-L1652`; `World/WorldSetup.cpp#L878-L932, #L1254-L1450`;
`World/WorldImpl.cpp#L492-L657`; `World/Terrain/Landscape.cpp#L459-L465, #L558-L652`; `World/Detection/Detector.cpp#L1331-L1529`;
`AI/AIArcade.cpp#L682-L808`; `UI/DisplayUIMenus.cpp#L706-L724, #L940-L1007, #L1170-L1330, #L1409-L1450, #L2010-L2066`;
`UI/Map/UIMapExtDisplay.cpp#L560-L611`; `World/Entities/Infantry/SoldierOldMove.cpp#L364-L411, #L1068-L1086`;
`World/Entities/Vehicles/VehicleTypes.cpp#L749-L756`; `IO/Streams/QStream.cpp#L357-L376`; `Core/GameState.cpp#L283`.
CE: `Game/Commands/GameStateExt.cpp#L1339-L1354` (camera block), `#L1009` (`soundLength`); `Game/Commands/GameStateExtUi.cpp#L1517-L1553`.
Tests and fixtures: `BohemiaInteractive/CWR@ffc61838b7:tests/integration/scripting/camcreate_any_type.test.sqf`,
`tests/integration/missions/demo_end_chain.Demo/outro.sqs#L1-L8`, `tests/fixtures/mods-intro/@triintro/Anims/intro.Intro/intro.sqs`.

**Repository.** Docs 03 §4.7–§4.8; 04 §3, §5–§6, §12; 05; 07 §12; 08 §2.4–§2.5, §4.2–§4.4; 09 §6; 17; 18 §6.1, §8.2; 19 §6.1, §6.5,
§7.6; 21; 22 §2.1; 23 §4, §13–§14; 24; 25; 28 §2.2, §3.4; 33 §5.9; `docs/porting/upstream-test-map.csv`; `AGENTS.md`.

**Community evidence.** OFPEC Editors Depot OFP lists and details pages (scripts, tutorials, tools; re-scraped 2026-09-27)
<https://www.ofpec.com/editors-depot/>; aligrant.com OFP cut-scenes page <https://www.aligrant.com/web/games/ofp/editing/cams>;
PMC Editing Wiki `camera.sqs` <https://pmc.editing.wiki/doku.php?id=ofp%3Amissions%3Acamera.sqs>; Faguss, Flashpoint Cutscene Maker
manual <https://ofp-faguss.com/files/flashpoint_cutscene_maker.pdf> and scripts page <https://ofp-faguss.com/scripts>; OFP.info
VideoMissions <http://ofpr.info.paradoxstudio.uk/missions/videomissions.html>; BIKI pages `camSetFovRange`, `camSetDive`, `setDate`
(search snippets; direct fetch 403).

**Product precedents.** Unreal Engine camera cut track
<https://dev.epicgames.com/documentation/en-us/unreal-engine/cinematic-camera-cut-track-in-unreal-engine>; Unity Cinemachine 2.3/2.4 and
Timeline 1.8 manuals <https://docs.unity3d.com/Packages/>; BIKI `Arma_3:_Key_Frame_Animation`, `Arma_3:_Splendid_Camera`,
`BIS_fnc_establishingShot` (MediaWiki API); StarCraft II Cutscene Editor introduction
<https://s2editor-guides.readthedocs.io/New_Tutorials/06_Cutscene_Editor/079_Cutscene_Editor_Introduction/>; Creation Kit
`Bethesda_Tutorial_Scenes` (ck.uesp.net, search summary); Source Filmmaker <https://en.wikipedia.org/wiki/Source_Filmmaker>.
