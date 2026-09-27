# Idioms from the shipped content

The 25 script and mission idioms that the game's own 1.99-era missions, campaigns and templates use most. For each: what it is for, a short example of our own, the profiles it works on with evidence, gotchas, and the typed replacement for users who do not script.

**Use this page to** recognise an idiom in an imported mission, explain it, repair it, and offer its typed replacement. When building, prefer the replacement. Write the raw idiom only when the user works at the script rung, then run `script.check` on it in its field context. Examples use generic names; class names in capitals (`MAG_CLASS`) are placeholders, so get real ones from `catalog.find`. Each `### Ixx` section stands alone: find the idiom in the index and load only its section.

## Evidence

- **Counts** are uses in the legacy official content: the `Missions`, `Campaigns`, `MPMissions`, `Templates` and `SPTemplates` folders that the 1.99 executable loads. They come from `docs/research/data/corpus-script-idioms.csv` (row names in backticks), `cwa199-observed-commands.csv` and `corpus-structure-stats.csv`, or from doc 35 where named. "Our count" means a local pass over the same corpus that is not in the data files. Regex counts are lower bounds.
- **`cwa199`:** every command in the examples appears in that content, so it is tier T1 (doc 35 §8.3). Commands that the gotchas name as absent, ineffective or unused say so where they appear. Seeing a command used proves that 1.99 had it, not how it behaved. Its 1.99 behaviour is assumed from the same code lineage **[I]** unless a line says otherwise.
- **`cwr` and `ce`:** every command used here is registered in both engines' command tables: `GSE` (CE's lines sit about 2 earlier) or `EVAL:express.cpp`, which is byte-identical in CE (`ofpisnotdead-com/CWR-CE@b67bf3bd62`). Semantics are read from CWR at the pin.
- **Legend.** Unmarked statements are verified by the count or the cited line. **[I]** marks an inference, **[U]** an open question that needs a Preview probe. "Read from source" means verified by reading the code, not by running it.
- **Aliases.** `CWR:` = `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/`; `GSE#L…` = `CWR:Game/Commands/GameStateExt.cpp#L…` (the command table); `EVAL:` = `BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/`; `doc NN` = `docs/research/NN-*.md`; "Field Manual `x`" = the field-manual skill's page `x`.
- **Replacements** are proposal-only designs from docs 19, 29, 31, 32 and 35 §9. Their names are provisional **[I]**.

## Index

| Id | Idiom | Legacy evidence | No-code replacement |
| --- | --- | --- | --- |
| I01 | Timed pause `~N` | 2,920 lines | Timeline cue; rule "after N s" |
| I02 | Wait until `@cond` | 2,835 lines | Rule WHEN/IF; module event |
| I03 | Branches and loops (`?`, `#label`, `goto`) | 1,427 `?`, 1,154 `goto` | Rule modes, "for each" |
| I04 | Every member, or how many (`forEach`, `count`) | 296 `forEach`, 487 `count` | Rule "for each", group strength |
| I05 | Flags and script launches | 4,298 custom trigger conditions | Rule builder flags |
| I06 | Timer triggers | 651 `true` conditions | Rule "after / held for N s"; Deadline |
| I07 | Hold a group until a trigger fires | median 8 syncs per SP mission | Rule "release group"; Reinforcements |
| I08 | Logic gates (AND/OR waypoints) | 408 gate waypoints | "Wait for all / any" gate |
| I09 | Ambient sound triggers | 38% of SP triggers | Ambient Soundscape |
| I10 | Radio calls with a live label | 60 triggers, 49 `setRadioMsg` | Player's Call |
| I11 | AI stance in init lines | 1,550 enum arguments | Behaviour preset attribute |
| I12 | Loadouts and crates | 1,496 `addMagazineCargo` | Loadout, Cargo contents |
| I13 | Start inside a vehicle | 182 `moveInCargo` | Special "In cargo"; start seat |
| I14 | Wrecks, damage, protected rides | 486 `setDammage` | Health slider; Destroyed at start |
| I15 | Stage an actor: hold, spare, turn | 477 `stop`, 118 `setCaptive` | Timeline actors; Hostage |
| I16 | Marker anchors | 1,049 `getMarkerPos` | Map placement; Random choice |
| I17 | Cutscene camera | 299 cutscene scripts | Cinematics timeline |
| I18 | Fades and title cards | 507 BLACK IN | Timeline titles; Opening |
| I19 | Scripted conversation | 114 conversation scripts | Conversation module |
| I20 | Music cues | 178 `playMusic` | Effects music; Timeline |
| I21 | Objective status | 525 `objStatus` | Objective module |
| I22 | Delayed checkpoint | 72 `saveGame` | Save point; Checkpoint |
| I23 | Ending socket: flag, outro, END trigger | 192 `forceEnd` | End state; Ending; sockets |
| I24 | Campaign state and "is it defined?" | 152 `saveVar`, 136 self-checks | Typed campaign state |
| I25 | MP server guard and broadcast | 532 `publicVariable` | Server guard; MP Game Rules |

## Script flow

### I01 Timed pause (`~N`)

- **For:** spacing beats in a sequence: lines of dialogue, camera moves, staged events.
- **Example:**

  ```text
  hint "Charges set."
  ~5
  bridge1 setDammage 1
  ```

- **Profiles:** `cwa199`, `cwr`, `ce`. 2,920 lines (`sqs_delay_tilde`); the most common gaps are 2–4 s (977) and 1–2 s (755). `CWR:Game/Scripting/Scripts.cpp#L263-L281`.
- **Gotchas:** it counts game time, which `setAccTime` scales (doc 32 §2.7). The delay may be an expression (`~(2 + random 3)`), but the engine builds the line in a 256-byte buffer, so keep it short. `~` exists only in `.sqs` files, never in an editor field.
- **No-code:** a Timeline cue in a scene (doc 32). In gameplay, use a rule "after N s", which compiles to a trigger timer (doc 31 §5.2).

### I02 Wait until (`@cond`)

- **For:** blocking until an event: a flag, a death, a finished camera move, a boarding.
- **Example:**

  ```text
  @alarm_on
  @("alive _x" count units grpGuard) == 0
  @vehicle player != player
  ```

- **Profiles:** all three. 2,835 lines (`sqs_wait_at`): 2,553 on `camCommitted`, 89 on one global flag, 69 on `alive`, 22 on `unitReady`, 20 on `count`. `CWR:Game/Scripting/Scripts.cpp#L282-L291`, `#L454-L457`.
- **Gotchas:**
  - The condition is re-evaluated on every step of the script.
  - A non-Boolean result counts as false without an error (`EVAL:express.cpp#L2773-L2782`).
  - An unset global reads as nil, and nil counts as false, so the script waits until something sets the flag. Operators pass nil through, so `alarm_on && x` behaves the same way (read from source: `EVAL:express.cpp#L2432-L2439`, `#L1348-L1351`; `EVAL:express.hpp#L56`, `#L96`). Initialise flags anyway.
  - Give story-critical waits a way out: official missions add skip flags after 90–120 s (doc 35 §3.5).
  - `vehicle X != X` means "X is in a vehicle".
- **No-code:** a rule's WHEN and IF (doc 31 §5), compiled to a trigger, or a module's output event.

### I03 Branches and loops (`?`, `#label`, `goto`)

- **For:** choosing a path, skipping a block, repeating a check.
- **Example:**

  ```text
  #check
  ~2
  ? !(alive radioman) : goto "lost"
  ? radio_done : exit
  goto "check"
  #lost
  radio_lost = true
  ```

- **Profiles:** all three. 1,427 `?` lines, 1,154 `goto` (626 forward), 919 labels (`sqs_conditional_q`, `sqs_goto`, `sqs_labels`); 356 polling loops with a wait and 171 loops that iterate and exit without one. `CWR:Game/Scripting/Scripts.cpp#L245-L252`, `#L292-L318`, `#L552-L564`.
- **Gotchas:**
  - A `?` line splits at its first `:`, even inside a string.
  - Labels match without regard to case. A `goto` to a missing label silently ends the script (1 shipped case).
  - Give every backward loop a `~`, an `@` or an `exit`. An exec'd script yields after 100 lines per step, but `init.sqs` has no step limit (`Scripts.cpp#L442`, `#L471-L478`; doc 32 §2.7), so an endless loop there without a wait would freeze the mission **[I]**.
  - Official content has no `if`, `while` or `private`. On `cwa199` they are T2/T3 and need a probe first (doc 35 §8.3).
- **No-code:** the rule builder's Repeat and While-true modes and its "for each" action (doc 31 §5.1–§5.2), or a module when the loop is a known pattern (Patrol area, Tracking marker; doc 31 §4.6).

### I04 Every member, or how many (`forEach`, `count`)

- **For:** applying one command to each unit of a group or list, or counting the ones that match. The count is the classic "group wiped out" test.
- **Example:**

  ```text
  "_x moveInCargo truck1" forEach units grpSquad
  ? ("alive _x" count units grpGuard) == 0 : guards_dead = true
  ```

- **Profiles:** all three. `forEach` 296 uses in 134 files, `count` 487 in 179, `_x` 848. `EVAL:express.cpp#L1132-L1133`, `#L1187`; `units` `GSE#L979-L980`.
- **Gotchas:**
  - The body is a string, so inner quotes are doubled (`"_x setUnitPos ""DOWN"""`). Legacy content writes code strings in `{}` only 3 times (`code_in_braces`) and quotes almost everywhere else (278 quoted `forEach` lines, our count), so both forms were used in the 1.99 era.
  - `_x` exists only inside the body.
  - `setBehaviour`, `setCombatMode`, `setSpeedMode` and `allowFleeing` already act on the whole group, so a `forEach` over them is redundant (I11).
  - In a trigger, use `thisList` for the units the trigger found.
- **No-code:** the rule builder's "for each" action and "group strength" condition (doc 31 §5.2), and the "wiped out" rule template.

## Trigger and waypoint glue

### I05 Flags and script launches

- **For:** connecting triggers, waypoints and scripts. One place sets a global, others wait for it, and a field starts a script.
- **Example:**

  ```text
  init.sqs:              alarm_on = false
  Trigger "alarm":       Condition: this       On Activation: alarm_on = true; [] exec "siren.sqs"
  Trigger "reinforce":   Condition: alarm_on   On Activation: hint "They are coming."
  ```

- **Profiles:** all three. 4,298 custom trigger conditions and 3,471 On Activation fields; 519 trigger fields `exec` a script; 132 missions ship `init.sqs`. `exec` `GSE#L1322`; `CWR:Game/Scripting/Scripts.cpp#L574-L580`; trigger `this`/`thisList` `CWR:World/Detection/Detector.cpp#L1259-L1265`.
- **Gotchas:**
  - Initialise every flag in `init.sqs`; there is no `isNil`.
  - Triggers are checked every 0.5 s with a random phase, so two triggers that read one flag fire in no fixed order (`Detector.cpp#L42-L46`; doc 31 §5.3).
  - In On Activation, read `thisList`, not `this` (doc 31 §5.3).
  - The script must exist in the mission folder or the global scripts folder: 18 shipped references do not (`script_reference_unresolved`).
  - Unit init lines run before `init.sqs` (doc 31 §3).
  - Never name a flag after a command (doc 35 §8.4).
- **No-code:** the rule builder, whose generated flags and cross-reference panel replace hand-named globals (doc 31 §5.2, §5.4).

### I06 Timer triggers

- **For:** "N seconds after the start" or "after the condition has held for N seconds", with no script.
- **Example:**

  ```text
  Trigger  Activation: None     Condition: true   Countdown 430/430/430   On Activation: convoy_go = true
  Trigger  West present (area)  Condition: this   Timeout 20/20/20        On Activation: area_held = true
  ```

- **Profiles:** all three. 651 triggers have the condition `true`; an official SP mission has a median of 19 timed triggers (`trig_timer`). `CWR:World/Detection/Detector.cpp#L1267-L1296`, `#L696-L705`.
- **Gotchas:**
  - The delay is one random draw between min and max, bunched around mid, taken each time the condition turns true. Set all three equal for a fixed time.
  - With max below 0.1 s the trigger fires at once, even if min and mid are set.
  - A Timeout is cancelled when the condition drops; a Countdown fires at expiry anyway. Which dialog label maps to which engine flag is unverified (Field Manual `countdown-vs-timeout`).
- **No-code:** a rule "after N s" or "held for N s" (doc 31 §5.2). A Deadline module announces long timers to the player (doc 35 rc19).

### I07 Hold a group until a trigger fires

- **For:** "the tanks wait until the alarm", with no script.
- **Example:**

  ```text
  Group Tanks:      WP1 MOVE at the start, WP2 MOVE to the village
  Trigger "alarm":  East detected by West, synced to Tanks WP1
  -> the tanks wait at WP1 until the alarm, then drive to WP2
  ```

- **Profiles:** all three. A median of 8 waypoint-to-trigger syncs per official SP mission (p90 21, `sync_wp_trig`); in the median mission, 18% of waypoints are synced (`share_wp_synced`). `CWR:AI/AIArcade.cpp#L309-L369`; `CWR:AI/AICenterImpl.cpp#L748-L804`; `CWR:World/Detection/Detector.cpp#L1384-L1390` (read from source; primer fact P2.10).
- **Gotchas:**
  - The group reaches the synced waypoint, then waits, so sync the waypoint *before* the move you want to release.
  - A waypoint with several syncs waits for all of them.
  - A SWITCH trigger does something else: it jumps the group past its synced waypoint, and backwards if the group already passed it (Field Manual `trigger-end-types`).
- **No-code:** a rule "THEN release group X", which compiles to exactly this sync (doc 31 §5.3 step 2); the Reinforcements module (doc 31 §4.6 #3); Alarm and Reaction Force (doc 35 rc18).

### I08 Logic gates (AND/OR waypoints on a game logic)

- **For:** "when both" or "when either" of two events happens, and timed sequences, with no script.
- **Example:**

  ```text
  Game Logic "gate":  WP1 AND, synced to triggers "radar_down" and "bridge_down"
                      WP2 AND, synced to Group Air WP1
  -> the air group leaves once both targets are destroyed
  ```

- **Profiles:** all three. 408 AND/OR waypoints in official content (402 in SP missions, 6 in co-op MP), all in logic groups. 45% of SP missions use them, and seven single missions plus the four training missions run whole timelines on them (doc 35 §2.2, §4). `CWR:UI/Map/UIArcadeWaypoint.cpp#L74-L105`; `CWR:AI/AIArcade.cpp#L309-L369`; `CWR:AI/AICenterImpl.cpp#L786-L807`.
- **Gotchas:**
  - The gate's output is the logic's *next* waypoint, so sync the held group there (Field Manual `logic-gates`; read from source, probe pending).
  - OR exists only on logic waypoints.
  - Several END triggers with the same number also act as AND.
- **No-code:** the "Wait for all / any" gate module (doc 35 rc15), or ALL OF / ANY OF in a rule (doc 31 §5.1).

### I09 Ambient sound triggers

- **For:** birds, dogs, wind or distant fire in one area, set up once.
- **Example:**

  ```text
  Trigger around the farm   Activation: None   Condition: true
  Effects: a trigger sound (CfgSFX) or environment sound (CfgEnvSounds) class from the catalog
  ```

- **Profiles:** all three. 1,426 of 3,725 official SP triggers (38%) exist only to play ambient sound, a median of 12.5 per mission (doc 35 §2.2). 136 legacy `description.ext` files declare `CfgSFX` and 135 declare `CfgEnvSounds`. `CWR:World/Detection/Detector.cpp#L1392-L1471`.
- **Gotchas:**
  - Effects run only when the Effects condition is true for the local player, which matters in MP (`Detector.cpp#L1392-L1439`).
  - A trigger sound is simulated with the trigger as its source (`Detector.cpp#L709-L712`, `#L1468-L1471`), so it is probably heard from the trigger's position **[I]**. How far it carries is unverified **[U]**.
  - Mission-made classes must be declared in the mission's `description.ext`.
- **No-code:** the Ambient Soundscape module: paint an area, pick a time-of-day preset, optionally go quiet on alarm (doc 35 rc14).

### I10 Radio calls with a live label

- **For:** letting the player choose the moment: start the attack, call support, call extraction.
- **Example:**

  ```text
  init.sqs:              1 setRadioMsg "null"
  Trigger "lz_clear":    On Activation: 1 setRadioMsg "Call extraction"
  Trigger "extract":     Activation: Radio Alpha, once   On Activation: heli_go = true
  ```

- **Profiles:** all three. 60 radio-activated triggers (`radio_trigger`). `setRadioMsg` has 49 uses in 24 files: 16 hide a slot with `"null"` and 22 set a localized label (our count). `GSE#L1278`; `CWR:Game/Commands/GameStateExtUi.cpp#L2213-L2268`.
- **Gotchas:**
  - Slots are numbered 1 (Alpha) to 10 (Juliet); any other number does nothing. The label applies to every trigger on that slot.
  - Hiding a slot with `"null"` is shipped 1.99-era practice, but the hiding itself is confirmed only by reading CWR (doc 31 §4.5) **[I for 1.99]**.
  - Radio triggers ignore timers (Field Manual `radio-triggers`).
- **No-code:** the Player's Call module, which shows the label only while the call is valid, with the compiler's radio allocator (doc 35 rc19; doc 31 §4.5).

## Unit setup

### I11 AI stance in init lines

- **For:** sleepy sentries, a careless convoy, a squad that never runs, prone snipers.
- **Example:**

  ```text
  this setBehaviour "SAFE"; this setCombatMode "BLUE"; this setUnitPos "DOWN"; this allowFleeing 0
  ```

- **Profiles:** all three. 1,550 enum-string arguments (`enum_string_argument`): `setBehaviour` SAFE 441, CARELESS 276, COMBAT 124; `setCombatMode` BLUE 172, RED 92; `setUnitPos` UP 246, DOWN 48. `allowFleeing` has 303 uses in 71 files. `GSE#L1299-L1305`, `#L1320`; handlers `CWR:Game/Commands/GameStateExtGrp.cpp#L171-L261`.
- **Gotchas:**
  - `setBehaviour`, `setCombatMode`, `setSpeedMode` and `allowFleeing` change the whole group, even from one unit's init line. `setUnitPos` changes one unit.
  - An unknown word does nothing and reports nothing; 10 shipped uses are wrong (`enum_string_not_recognised`).
  - The accepted words, in any case:
    - behaviour: CARELESS, SAFE, AWARE, COMBAT, STEALTH;
    - combat mode: BLUE, GREEN, WHITE, YELLOW, RED;
    - speed: LIMITED, NORMAL, FULL;
    - unit position: UP, DOWN, AUTO.

    Later titles' `MIDDLE` does not exist here (`CWR:AI/ArcadeTemplate.cpp#L76-L91`; `CWR:AI/AICenter.cpp#L146-L156`; `CWR:AI/AIRadioImpl.cpp#L1296-L1299`).
  - `allowFleeing 0` means "never flee": courage = 1 − value (`CWR:AI/AIGroup.hpp#L687`).
  - A later waypoint whose behaviour, combat or speed field is set changes the stance again **[I]**. In official missions, 82–89% of waypoints leave those fields unchanged (doc 35 §2.2).
- **No-code:** the unit and group behaviour-preset attribute (posture, alertness, fleeing, hold fire; doc 31 §3) and the waypoint's own fields.

### I12 Loadouts and crates

- **For:** giving a soldier chosen weapons, or filling a crate or vehicle with chosen gear.
- **Example:**

  ```text
  removeAllWeapons this; this addMagazine "MAG_CLASS"; this addMagazine "MAG_CLASS"; this addWeapon "RIFLE_CLASS"
  clearWeaponCargo this; clearMagazineCargo this; this addWeaponCargo ["RIFLE_CLASS", 4]; this addMagazineCargo ["MAG_CLASS", 24]
  ```

- **Profiles:** all three. `removeAllWeapons` 178, `addMagazine` 635, `addWeapon` 257, `addWeaponCargo` 759, `addMagazineCargo` 1,496, `clearWeaponCargo` 59, `clearMagazineCargo` 115. Custom crates appear in 21 of 30 official MP missions (doc 35 §5.7). `GSE#L1021-L1024`, `#L1255`, `#L1257`, `#L1332-L1333`.
- **Gotchas:**
  - Add magazines before the weapon so that it starts loaded (doc 31 §3) **[I]**.
  - Class names must come from the catalog. What an unknown class does is unverified **[U]**.
  - In MP every machine runs the init line. Whether cargo added there stacks once per machine is unverified **[U]**.
- **No-code:** the unit's Loadout attribute (catalog picker, magazine compatibility checked) and the vehicle or crate Cargo contents attribute (doc 31 §3). For gear that carries between missions, the campaign weapon pool (doc 29).

### I13 Start inside a vehicle

- **For:** a squad that begins in a truck, or a crew already seated in an empty tank.
- **Example:**

  ```text
  this moveInCargo truck1
  this moveInDriver tank1
  ```

- **Profiles:** all three. `moveInCargo` 182 uses (44 files), `moveInDriver` 89, `moveInGunner` 22, `moveInCommander` 15. `GSE#L1316-L1319`; handler `CWR:Game/Commands/GameStateExtUi.cpp#L2795-L2851`.
- **Gotchas:**
  - Nothing happens, and nothing is reported, when there is no free seat, the unit is not a soldier, or the soldier is not local to this machine.
  - For a vehicle of the unit's own group, the stock Special "In cargo" does this without code (Field Manual `special-placement`).
- **No-code:** Special "In cargo" for the unit's own group. For an empty vehicle or another group's, a start-seat picker on the unit (a proposal, not yet in doc 31 §3) **[I]**.

### I14 Wrecks, damage and protected rides

- **For:** a burnt-out vehicle or wrecked building at the start, a damaged vehicle, a scripted ride that must not fail.
- **Example:**

  ```text
  this setDammage 1
  this setDammage 0.6
  heli1 allowDammage false
  ```

- **Profiles:** all three. `setDammage` 486 uses in 159 files; `setDammage 1` appears 307 times in the init lines of 77 official missions (our count). `allowDammage` 4. `GSE#L1241-L1243`; handler `CWR:Game/Commands/GameStateExtUi.cpp#L102-L121`.
- **Gotchas:**
  - Spell `setDammage` and `allowDammage` with a double m. `setDamage` shares the handler and appears in 1.99-era content (3 uses). Single-m `allowDamage` is absent from the 1.99 executable (doc 35 §8.2).
  - `setDammage 0` also repairs an aircraft's landing gear.
  - Restore `allowDammage true` after the ride: official content protects only for the length of a scripted extraction (doc 35 §4).
- **No-code:** the stock Health slider on units and vehicles, and the "Destroyed at start" attribute for map objects (doc 31 §3). What a Health of 0 produces is unverified **[U]**. Protected rides become a timed option on the timeline (doc 35 rc48).

### I15 Stage an actor: hold, spare, turn

- **For:** a unit that must stay put for a scene or a post, a prisoner or witness nobody shoots, or a traitor everybody shoots.
- **Example:**

  ```text
  this stop true
  this disableAI "MOVE"
  prisoner1 setCaptive true
  traitor1 addRating -10000
  ```

- **Profiles:** all three. `stop` 477 uses (64 files), `disableAI` 197 (23 files), `setCaptive` 118 (28 files), `addRating` 343 (83 files). `GSE#L1220`, `#L1233`, `#L1308-L1309`; handlers `CWR:Game/Commands/GameStateExtObj.cpp#L631-L654`, `#L680-L704`.
- **Gotchas:**
  - `disableAI` cannot be undone, because no `enableAI` exists (doc 31 §2 row 18). Use `stop true` and `stop false` when the unit must move later.
  - On a vehicle, `setCaptive` applies to its commander; on a destroyed object it does nothing.
  - `addRating` adds to experience. Far below zero (−10,000 in official deathmatch, doc 35 §5.5) makes a renegade whom every side engages; positive values serve as rewards (doc 35 §3.4).
  - Captives change side-presence triggers: after CWE made wounded units captive, "not present" triggers stopped working (doc 35 §6.1).
- **No-code:** the Timeline actor track for scenes (doc 32), the unit's captive attribute and the Hostage module (doc 31 §3, §4.6 #13), and a hold-position behaviour preset.

### I16 Marker anchors

- **For:** placing a unit, object or camera at a spot chosen on the map rather than typed in code.
- **Example:**

  ```text
  officer1 setPos getMarkerPos "m_meeting"
  _p = getMarkerPos "m_cam1"
  _cam camSetPos [_p select 0, _p select 1, 12]
  ```

- **Profiles:** all three. `getMarkerPos` has 1,049 uses in 114 files and `setPos` 1,035 in 156. Official single missions keep 80 invisible Empty markers as script anchors (doc 35 §4). `GSE#L949`, `#L1236`; `CWR:Game/Commands/GameStateExtWorld.cpp#L429-L451`.
- **Gotchas:**
  - Marker names match without regard to case. A missing marker returns `[0,0,0]`, the map corner, with no error.
  - The height comes back as 0, so `setPos` puts the object on the ground. The third element of a position is height above the surface (doc 32 §2.3).
- **No-code:** drag the entity on the map. For "one of several places", use the unit's alternative start markers (`markers[]`, doc 04) or the Random choice module (doc 31 §4.6 #10). Scene positions are Timeline keys (doc 32).

## Presentation

### I17 Cutscene camera

- **For:** intros, outros and in-mission scenes: a scripted camera takes over the view and then hands it back.
- **Example:**

  ```text
  _cam = "camera" camCreate getPos hq_tent
  _cam cameraEffect ["internal", "back"]
  _cam camSetTarget hq_tent
  _cam camSetPos [2510, 3040, 6]
  _cam camCommit 0
  @camCommitted _cam
  _cam camSetPos [2530, 3050, 4]
  _cam camCommit 6
  @camCommitted _cam
  _cam cameraEffect ["terminate", "back"]
  camDestroy _cam
  ```

- **Profiles:** all three. 299 cutscene script files (`camera_script_files`); `camCommit` 2,694 uses; 2,553 `@camCommitted` lines; `cameraEffect` terminate 282; `camDestroy` 281. `GSE#L1064-L1065`, `#L1341-L1356`; handlers `CWR:Game/Commands/GameStateExtUi.cpp#L1369-L1639`; doc 32 §2.2–§2.3.
- **Gotchas:**
  - Terminate the view before `camDestroy`. Destroying first leaves a frozen view that holds the mission end, and `@camCommitted` on a deleted camera waits forever (doc 32 §2.2; `GameStateExtUi.cpp#L1458-L1467`). 21 shipped scripts never destroy their camera.
  - Moves run in straight lines at constant speed. `camSetDir`, `camSetBank`, `camSetDive` and `camSetFovRange` do nothing on CWR and CE, and official content never uses them (doc 32 §2.2).
  - Shipped scripts often call `enableRadio false` (175 lines) and `setAccTime 1` (189 lines, our count). Radio audio is skipped while time runs fast, and a unit that is talking on the radio delays its next `say` (doc 32 §2.5).
  - `[] exec "camera.sqs"` (58 references) starts the developer's free camera for finding shots; remove it before release. The 1,489 timestamp comments in shipped scripts are shots captured with it.
- **No-code:** the Cinematics timeline: shots drawn on the map, capture from the in-game camera, and a safe ending on every path (doc 32).

### I18 Fades and title cards

- **For:** opening from black, cutting to black between beats, showing place and time.
- **Example:**

  ```text
  titleCut ["", "BLACK IN", 2]
  titleText ["Northern ridge, 05:40", "PLAIN DOWN"]
  ~8
  titleCut ["", "BLACK OUT", 1]
  ```

- **Profiles:** all three. Effect types: BLACK IN 507, BLACK OUT 365, PLAIN 156, PLAIN DOWN 118, WHITE IN 26, BLACK FADED 21 (`title_effect_*`). `titleCut` has 914 uses, `titleText` 382, `cutText` 30. `GSE#L1000-L1008`; doc 32 §2.4.
- **Gotchas:**
  - There are two layers with one effect each. `titleCut` and `cutText` draw on the cut layer. `titleText`, trigger Effects titles and `say` subtitles share the title layer, so a subtitle replaces a title card.
  - A title-layer BLACK OUT blocks the mission end until `forceEnd`; the cut layer does not. Near an ending, fade with `titleCut` or `cutText`.
  - The third element is a speed factor: larger is slower, 0 ends within a few frames, and a negative value never ends.
  - Unknown effect names do nothing.
- **No-code:** the Timeline cut and title tracks (doc 32), and the Opening and Ending modules (doc 35 rc20).

### I19 Scripted conversation

- **For:** orders scenes, radio chatter and banter: voiced, subtitled lines paced by waits.
- **Example:**

  ```text
  ; init line of sgt1:  this setIdentity "LEAD_SERGEANT"
  sgt1 say "brief01"
  ~4
  player sideRadio "radio01"
  ~3
  ```

- **Profiles:** all three. 114 conversation scripts (3+ lines and 2+ waits, `conversation_script_files`). `say` has 1,142 uses in 185 files, `sideRadio` 691, `groupRadio` 86, `setIdentity` 269 in 120 files. The pause after a line has a median of 3 s (p90 8 s) (doc 35 §4). `GSE#L1221`, `#L1266-L1273`; doc 32 §2.5.
- **Gotchas:**
  - `say` needs a `CfgSounds` class, `*Radio` needs a `CfgRadio` class and `setIdentity` a `CfgIdentities` class. Recurring characters belong in the campaign's `description.ext` (doc 35 §2.2).
  - `say` subtitles appear only if the class sets `forceTitles` or the player turned titles on, and only within 100 m of the camera.
  - A unit that is still talking queues the next line, so fixed waits drift.
  - Outside MP, radio is silent without a living player, and radio audio is skipped while `setAccTime` is above 1 (doc 32 §2.5).
- **No-code:** the Conversation module and screenplay (speaker, line, channel, pacing; doc 31 §4.6 #19), the cast list (doc 31 §3), and the Timeline dialogue track (doc 32).

### I20 Music cues

- **For:** marking a moment: boarding, a target destroyed, armour sighted, the end.
- **Example:**

  ```text
  playMusic "TRACK_CLASS"
  ~30
  5 fadeMusic 0
  ```

- **Profiles:** all three. `playMusic` has 178 uses in 106 files and `fadeMusic` 404 in 115; the 1985 campaign has 89 `playMusic` calls in 50 missions (doc 35 §3.5). `GSE#L1012-L1013`, `#L1338`; the trigger Effects music field is handled at `CWR:World/Detection/Detector.cpp#L1473-L1487`.
- **Gotchas:**
  - `t fadeMusic v` fades to volume v over t seconds, and `playMusic ""` stops the music.
  - The `[name, start]` array form is documented only for Remastered; on 1.99 it is unverified (doc 32 §2.5) **[U]**.
  - In the Effects music field, `$STOP$` stops the music.
  - Well-loved campaigns used one cue per mission and never repeated it (doc 35 §6.3).
- **No-code:** the Effects music field on a trigger or waypoint, the Timeline music track, and moment cards such as the stinger (doc 35 rc08).

## Objectives, checkpoints, endings and state

### I21 Objective status

- **For:** ticking, failing, hiding or revealing a briefing objective at run time.
- **Example:**

  ```text
  "3" objStatus "HIDDEN"
  "1" objStatus "DONE"
  "2" objStatus "FAILED"
  "3" objStatus "ACTIVE"
  ```

- **Profiles:** all three. `objStatus` has 525 uses in 146 files; all 24 official single missions use it, and the 1985 campaign hides objectives 41 times and reveals them 33 times (doc 35 §3.5, §4). `GSE#L1321`; handler `CWR:Game/Commands/GameStateExtUi.cpp#L1825-L1861`.
- **Gotchas:**
  - The id is the part after `OBJ_` in `briefing.html`; the engine adds the prefix.
  - The status is stored in a global named `OBJ_<id>`, so never use that name for anything else. Setting the same status again does nothing.
  - An unknown status word counts as ACTIVE.
  - The "objective completed/updated" hint shows only when the easy (cadet) setting is on, and never for HIDDEN.
- **No-code:** the Objective module (title, text, marker link, done-when, fail-when, hidden at start, autosave; doc 31 §4.6 #1; doc 35 rc16).

### I22 Delayed checkpoint

- **For:** saving progress after a milestone, once the danger has passed.
- **Example:**

  ```text
  Trigger  Condition: obj1_done   Countdown 8/8/8   On Activation: saveGame
  ```

- **Profiles:** all three. `saveGame` has 72 uses in 62 files and appears in 32 of 42 playable 1985 missions. Single missions often save from a second trigger 5–11 s after a flag (doc 35 §3.5, §4). `GSE#L881`.
- **Gotchas:**
  - Save when no threat is near and no scene is running **[I]**.
  - Preview deletes save files (doc 09 §2).
  - CWE disables `saveGame` and replaces it (doc 35 §6.1).
- **No-code:** the Save point module (doc 31 §4.6 #18), the Objective module's autosave option, or a Checkpoint: a flag, then a save 6–10 s later (doc 35 rc16).

### I23 Ending socket: flag, outro, END trigger

- **For:** ending the mission with a chosen outcome after a short outro, from any script or event.
- **Example:**

  ```text
  Trigger "won":   Condition: obj1_done && obj2_done   On Activation: end_code = 1; [] exec "outro.sqs"
  outro.sqs:       camera and fades, then as its last line: outro_done = true
  Trigger END1:    Condition: outro_done && end_code == 1   On Activation: forceEnd
  Trigger END2:    Condition: outro_done && end_code == 2   On Activation: forceEnd
  ```

- **Profiles:** all three. `forceEnd` has 192 uses in 116 files. Trigger types: END1 244, END2 50, END3 26, LOSE 24 (`LOOSE` in the file). In 11 of 24 official single missions an outro script ends the mission this way. The Resistance campaign commits its state in `exit.sqs` (19 missions; doc 35 §3.3, §4). `GSE#L885`; `CWR:Game/Commands/GameStateExtWorld.cpp#L781-L785`; `CWR:World/WorldImpl.cpp#L541-L656`; `exit.sqs` `CWR:UI/DisplayUIMenus.cpp#L984-L994`.
- **Gotchas:**
  - Only END and LOSE triggers choose an ending. `forceEnd` only lets the chosen ending through a live camera or title effect.
  - Every trigger of one END number must be active at the same time.
  - END numbers are outcomes, not only wins (doc 35 rc09). Official single missions use them for failures the player survives, each with its own debriefing. Campaigns use LOSE to mean "retry this mission" (doc 35 §3.1, §4).
  - `exit.sqs` runs once, with the outcome in `_this` and no line limit, but not when the player is killed.
- **No-code:** the End state module (doc 31 §4.6 #2) with the Ending module's outro (doc 35 rc20). In campaign missions, use the campaign designer's outcome sockets (doc 19).

### I24 Campaign state and "is it defined?"

- **For:** carrying results into later missions while each mission stays playable on its own. The same check skips MP slots that may be empty.
- **Example:**

  ```text
  ; producer mission, when the radar falls
  cmp_radar = 1; saveVar "cmp_radar"
  ; consumer mission, init.sqs: keep the saved value, else use a default
  ? cmp_radar == cmp_radar : goto "known"
  cmp_radar = 0
  #known
  ```

- **Profiles:** all three. `saveVar` has 152 uses in 21 files; 1985 saves 10 names and Resistance about 112. There are 136 self-comparison checks (`self_equality_existence_check`), used for campaign variables (69 in 21 1985 missions) and for MP slots (doc 35 §3.4, §5.4). `GSE#L1069`; `CWR:Game/Commands/GameStateExtGrp.cpp#L412-L425`.
- **Gotchas:**
  - Only the positive form works. With the variable unset, `x == x` gives nil, which reads as false. `!(x == x)` is nil too, so a negated test never runs its default (read from source: `EVAL:express.cpp#L1348-L1351`, `#L1417-L1419`).
  - `==` exists only for numbers, strings, objects, groups and sides (`EVAL:express.cpp#L1113-L1117`; `GSE#L1279-L1283`). A defined Boolean or array fails the test, so save state as numbers, as the example does.
  - `saveVar` takes the name in quotes and stores the value at once. Which types survive is in the primer's §5.
  - Shipped campaigns contain write-only and misspelt variables (doc 35 §3.4). Use the `cmp_` prefix and give each name one owner.
- **No-code:** the campaign designer's typed state and outcome sockets (doc 19), the ShapingOperation module (doc 35 rc22), and a Preview prologue that fills unset campaign variables with test values (doc 35 rc51).

## Multiplayer

### I25 Server guard and broadcast

- **For:** running game rules once, on the server, and telling every client the result.
- **Example:**

  ```text
  ; rules.sqs, started from init.sqs on every machine; srv is a placed Game Logic
  ? !(local srv) : exit
  captures_w = captures_w + 1; publicVariable "captures_w"
  ; trigger END1 on every machine:  Condition: captures_w >= 5   On Activation: forceEnd
  ```

- **Profiles:** all three. `publicVariable` has 532 uses in 180 files and appears in 23 of 30 official MP missions. There are 73 `local` checks on a placed logic (`local_check_on_logic`), and 9 official MP missions place a logic as the server object (doc 35 §5.4). `GSE#L936`, `#L1042`. `isServer` (`GSE#L909`) never appears in official content; its name is in the 1.99 executable (T3, so probe first).
- **Gotchas:**
  - Triggers and init lines run on every machine. Guard server work, and initialise every broadcast global on every machine before anything reads it.
  - Official content broadcasts only numbers, Booleans and objects. Whether 1.99's `publicVariable` carries strings or arrays is unverified **[U]**.
  - `isServer` is false in single player (doc 31 §4.5). `local <logic>` should be true there, going by the source, but probe AT8 is pending **[I]**.
  - Empty playable slots leave their unit names undefined; test them with I24's self-comparison **[I]**.
- **No-code:** the compiler-owned server guard (doc 31 §4.5), each rule's locality, and the MP Game Rules module (limits, end detection on the server, broadcast mirrors; doc 35 rc23).

## Not in the official content

Official 1.99-era content is pure SQS, with 0 `.sqf` files. It never uses `if`/`then`/`else`, `while`, `private`, `isServer`, `onMapSingleClick`, dialogs or `loadFile`, and uses `addEventHandler` only 3 times (doc 35 §4, §5.7, §8). Community content used some of these (T2), and some exist only as strings in the 1.99 executable (T3). On `cwa199`, probe them in Preview before relying on them. Commands from later titles are listed in the primer's §4.
