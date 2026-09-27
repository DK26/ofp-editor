# Atmosphere, sound and music

Research doc 41 for Plotroom (`ofp-editor`). Research date: 2026-09-27. Audience: contributors and LLM coding agents. This file is meant to be read on its own.
Question answered (owner): "Research how to create beautiful scenarios and/or atmosphere, and how sound and music should be used correctly and effectively for that purpose. Offer the user friendly options and capabilities to achieve and/or edit those."

**Status.** Proposal-only. Every type, name, code, threshold, preset value and UX in §3–§9 is **[I]** unless a line says otherwise. Every number is a default, to be tuned against Preview probes (§9.3) and playtests.
**Epistemic legend.** **[V]** verified: a pinned engine line, the decoded base config, a fetched page, or a count over the local corpus (re-run 2026-09-27). **[V-search]** seen only in a search snippet, because the page refused the fetch. **[I]** our inference, derived arithmetic or proposal. **[U]** unknown; it needs a probe or a source. Engine facts are static readings of the source; nothing here was measured in a running game.
**Citation aliases.** `CWR:` = `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/`; `OAL:` = `BohemiaInteractive/CWR@ffc61838b7:engine/PoseidonOpenAL/`; `CE:` = `ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/` (as in docs 32 and 39). Line numbers are CWR's; CE was compared where a line says so.
**Profiles.** `Cwa199` (the CWA 1.99 executable), `Cwr` (Remastered, the CWR source) and `Ce` (the community continuation), as in doc 31. A *CWE mount* is the Cold War Enhanced mod set (docs 27, 42). 1.99 availability comes from a names-only string scan of the executable plus the forms that official content shipping with it uses; that scan cannot see overloads.
**Corpus and hygiene.** The corpus is the owner's install, read locally by uncommitted scripts: 24 SP missions, 118 campaign entries (the 1985 and Resistance campaigns, cutscenes and interludes included), 30 MP missions, the base config and the CWE mod. "Playable" means the 87 SP and campaign missions left after removing cutscenes and interludes. Counts from different scripts can differ by a few percent, so each number names its population. Only aggregate numbers, command and class names and our own descriptions appear here: no game or mod content is quoted, and no audio was extracted. Game audio is proprietary, so Plotroom references stock sounds and music by class name and never bundles, copies or redistributes them. Web sources are paraphrased. Nothing here refers to private or unpublished work.
**Codes (provisional; the design round assigns final numbers).** Heuristics `AH1`–`AH12`, mood presets `AM01`–`AM12`, soundscape layers `SX01`–`SX08`, cue plans `QP1`–`QP6`, audio lints `AU01`–`AU24`, atmosphere lints `AL01`–`AL17`, probes `AP1`–`AP18`, phases `AD0`–`AD4`, acceptance tests `AMT1`–`AMT14`. A grep of `docs/` finds none of these families, and none collides with the codes listed in the headers of docs 36, 37, 39 and 42.
**Companions.** Doc 03 (Intel and Effects dialogs), doc 04 (Intel keys, `description.ext` classes), doc 08 (Preview harness), doc 22 (plugins, Radio Voice), doc 25 (menus, Pick/Fill), docs 26 and 28 (fun; FP42, MC19), docs 27 and 42 (mods, CWE), doc 31 (modules 7, 15, 16, 19; the no-code ladder), doc 32 (timeline; §2.5–§2.6, §3.5), doc 34 (ed12, mo06, mo07, mo09, mo10, MC28, D9), doc 35 (rc08, rc14, rc33, rc43), doc 37 §6 (map-object actions), doc 39 (cutscene audio plans). This doc owns the atmosphere and audio *design*; the modules and the timeline it compiles into stay in their own docs.

## TL;DR

- **Atmosphere in CWA is a few dials plus authored life [V].** Intel date, time and a start→forecast weather arc, the view distance, lit fires, lamps and flares, trigger sound emitters, one music slot, dialogue and radio. The engine adds terrain ambience beds, rain, thunder and church bells on its own. It spawns no animals, birds or people (§1, §2).
- **Light depends only on sun height [V/I].** Every stock island sits at 40° N. Light is warm below 25°, and a night factor ramps in over the last 5° above the horizon; it gates every point light (fires, lamps, flares, headlights). Stars are full at −10°. The moon phase is cosmetic, so every night is equally dark (§2.3).
- **One dial makes the storm [V].** Above overcast ≈ 0.66 direct sunlight falls to 20–28 %; rain is possible only above ≈ 0.67 and thunder above ≈ 0.93. Fog is one scalar that cuts sight for the player and the AI alike (fog 0.5 ≈ 470 m). Scripts cannot read the weather. The Intel forecast was BI's weather-storytelling tool: 87 % of playable official missions change weather that way, and scripted weather appears twice (§1.2, §2.1).
- **Official content is restrained [V].** Half of the playable missions start between 04:00 and 07:59, and none starts with fog above ≈ 0.57. The median is one music cue per mission, 75 % of cues sit in intro and cutscene scripts, and only 2 of 184 are started by a detection trigger. About 900 distant-battle emitters carry the campaigns' sense of war (§1.2).
- **Sound mechanics that change designs [V].** `soundEnv` swaps the bed for the whole island, with an instant cut, until another `soundEnv` or the end of the section; it is not a zone, which corrects doc 34 ed12. Trigger emitters go silent beyond ≈ ⅔ of the view distance + 500 m from the player (or the cutscene camera). A positional volume sets how far a line carries, not how loud it is up close. `CfgRadio` volume is ignored. Music starts at 0.5 and cannot crossfade. `fadeSound` hushes the world but not voice-over, radio or music (§2.2–§2.3).
- **The Atmosphere Director [I].** Twelve mood presets (dawn fog patrol, still hot noon, storm at night, burning village aftermath, winter quiet, flare-lit night assault, …) compile per profile to ordinary Intel fields, init lines, objects and triggers. Each prints its consequences: sight range, rain and thunder, the enemy's night-vision share, earshot, lamp gaps, bell times (§3).
- **Previews make the invisible visible [I].** A sun bar with named light phases, sight and earshot rings on the 2D map, an engine-ambience overlay computed from the island, a weather-arc timeline, and live harness screenshots on Cwr and Ce (§3.4–§3.5).
- **Scene dressing from stock classes [V classes; I kits].** "What happened here" kits (ambushed convoy, abandoned camp, fresh graves, field hospital, village that fought back, …) use placeable wrecks, bodies, graves, tents, fires, barrels and wire, plus map-object destruction. Craters and ruins cannot be placed in the editor. Vista and landmark finders and a visible restraint budget round this out (§4).
- **Sound and music as lanes [I on V mechanics].** A phase-based cue planner with a silence budget; dips and ducking compiled to `fadeMusic` ramps; Bed/Scatter/Spot soundscapes placed inside earshot; a radio lane; forms that generate `CfgSounds`, `CfgMusic`, `CfgRadio`, `CfgSFX` and `CfgEnvSounds` in fenced regions (§5).
- **Import pipeline and ethics [V/I].** Vorbis output, mono for anything positional, loudness normalisation and a local radio filter. `.lip` files are generated from the audio by porting CWR's reference algorithm with its 8 tests. Size budgets, per-language siblings and licence metadata are enforced. TTS voices come from an allowlist, and there is no cloning (§5.6–§5.9).
- **Lints, never walls [I].** AU01–AU24 and AL01–AL17 cover music overuse and hard cuts; missing, oversized, clipped or misformatted files; licence gaps; inaudible radio; emitters out of earshot; weather changing too fast; dark objectives and hollow battles. Only what the engine cannot run is an error (§6).
- **Weak models pick; code computes [I].** The model picks a mood family, a preset, an intensity and a cue plan from menus of ≤ 7 items, and writes subtitles and radio lines. Code solves the hours, levels, positions, fades and files, and validates everything (§7).

## 1. What makes an OFP scene beautiful and atmospheric

### 1.1 Distilled heuristics

| # | Heuristic | Evidence | Plotroom lever |
| --- | --- | --- | --- |
| AH1 | Choose the light first: dawn, golden evening and night carry more mood than noon | Half of BI's playable missions start 04:00–07:59 [V corpus]. A retrospective remembers roaming Everon through the sun's whole daily arc and walking the woods at sundown for the birdsong (NME, Rick Lane, 2022) [V] | Time-of-day picker by named phase, solved per date (§3.2) |
| AH2 | One weather arc per mission, told by the forecast | 87 % of playable official missions have a forecast overcast that differs from the start value (52 worsen); scripts almost never touch weather [V] | Weather-arc editor; "forecast differs" is the default (§3.4) |
| AH3 | Fog hides what is near and builds suspense fairly; night does not | Fog sets one sight range for the renderer and the AI [V `CWR:World/Terrain/Landscape.cpp#L654-L683`]. Night multiplies AI visual accuracy by (1 − night): about 0.03 without NVG, 0.25 with [V `CWR:World/Detection/Target.cpp#L747-L765, #L872-L888`]. Silent Hill's fog, used to mask hardware limits, was credited with its atmosphere (Wikipedia, citing Edge) [V] | Sight read-out; night-vision share card; fog and night presets |
| AH4 | Hear it before you see it | Doc 28 FP16 and MC08 already ask for a cue before each lethal set piece; doc 35 rc14 proposes dog tripwires | Soundscape tells: dogs, engines and distant shots inside earshot (§5.4) |
| AH5 | Landmarks pull players, and reveals reward them | Disney's "weenies" (Level Design Book); Lynch's paths, edges, districts, nodes and landmarks; the triangle rule for gradual reveals in Breath of the Wild (Kotaku, 2017) [V] | Vista and landmark finder, reveal point (§4.3) |
| AH6 | Let the place tell what happened, and let it be missable | Smith and Worch, "What Happened Here?", GDC 2010; Smith: some things must be missable for finding them to mean something (Nieman Storyboard, 2011); Carson (2000): cause-and-effect vignettes, answer "where am I?" within 15 s, less is more [V] | Vignette kits and an opening checklist (§4.2–§4.3) |
| AH7 | Places feel alive through people and animals | The Level Design Book's Disneyland study: staff, not the architect, make spaces feel populated [V]. Only 13 of 118 campaign entries contain civilians [V corpus]. The tutorials in doc 28 §3.4 name empty towns as an atmosphere killer | Lived-in heuristic, AL14 (§4.4) |
| AH8 | Pacing needs valleys | Schell's interest curve; Left 4 Dead's 30–45 s relax phase after a peak; players switch to 4× time after a minute of dead air (all doc 28) [V] | Pacing strip and quiet beats (§5.2) |
| AH9 | Silence is a beat; music is punctuation | Omaha Beach in Saving Private Ryan plays without score (No Film School; Albrechtsen in A Sound Effect) [V]. BI's median is one cue per mission [V]. Doc 28 FP42 | Cue planner with a silence budget (§5.2) |
| AH10 | Density has a limit | Murch: beyond about two and a half layers of the same "colour" of sound, layers merge into one density; mixed colours allow about five (Transom, 2005) [V] | Dialogue and emitter density lints (AU22, AL15) |
| AH11 | Restraint | Ico's "subtracting design" (Wikipedia) [V]. BI dressed 14 % of its missions, with a median of 2.5 objects [V] | Atmosphere budget meter (§4.5) |
| AH12 | Consistency sells; pedantry does not | An owl at noon or a lark at midnight breaks the spell; AGENTS.md makes realism a default, never a wall | Day/night tags on classes; info-level lints only |

### 1.2 What the official content actually does [V aggregates]

| Aspect | Numbers (population) |
| --- | --- |
| Start hour (87 playable) | Night 21–03: 9 (10 %). Predawn 04–05: 19 (22 %). Dawn and early morning 06–07: 24 (28 %). Morning 08–10: 13. Midday 11–14: 8. Afternoon 15–17: 11. Evening 18–20: 3. Cutscenes and interludes keep 07:30 in 47 of 55. 19 of 30 MP missions keep every Intel default (07:30, 10 May 1985, overcast 0.5, fog 0) |
| Date (87 playable) | Always 1985. May 23, June 28, July 10, August 9, September 13, March 2, April 1, November 1; never October or December–February |
| Sky (87 playable) | Start overcast below 0.25: 37 (43 %). Fair 0.25–0.5: 14. Cloudy 0.5–0.67: 22. Rain-capable 0.67–0.93: 11. Storm-capable: 3. The forecast differs in 76 (52 worsen, 24 improve) |
| Fog | No fog in 61 % of playable missions. 38 of the 142 SP and campaign entries start foggy (median 0.28), and in 32 of those the forecast lifts it. The highest start fog is ≈ 0.57 |
| Scripted weather and time | `setOvercast` 2 calls (one cutscene); `setFog` and `setRain` 0; `skipTime` 8 calls in 5 campaign entries, 6 of them in cutscene scripts |
| Intel per section | Intro time differs from mission time in 21 of 24 SP and 102 of 118 campaign entries |
| View distance | `setViewDistance` in 44 script folders; 1200 m in 35 of 60 numeric calls; range 250–2000 |
| Light at night | Of 10 night-start missions, 6 add a light source (lit fire 5, flare classes 2, lamps 1). Fire objects appear in 26 of 142 missions and are lit anywhere in 13. `switchLight` has 9 calls in 2 campaign entries |
| Emitters (`soundDet`) | 206 SP, 1,299 campaign and 32 MP triggers. Distant battle (`CA_AK`, `CA_M16`, `CA_Expl1`): about 900 in 44 campaign entries, 69 % of campaign emitters, at a median 2.8 km from the player's start; 995 of 998 are flag-gated and 23 repeat. Nature: about 340 campaign emitters at a median 0.7 km. Placed Sound objects: 23 in 7 missions |
| Environment bed (`soundEnv`) | 1 SP mission; 14 uses in 12 campaign entries (11 with a mission-defined class); 1 MP mission |
| Music | Some cue in 15 of 24 SP, about 70 of 118 campaign entries and 1 of 30 MP missions; median 1 cue per mission. Of 184 SP and campaign cues: intro scripts 45 %, cutscene scripts 30 %, triggers and waypoints ≈ 18 %, `init.sqs` 5 %, outro scripts 0. Only 2 sit on detection triggers. Custom `CfgMusic` in 1 SP mission |
| Fades | About 400 literal `fadeMusic` calls (406–428 depending on the counting script): ≈ 92 % target 0.5 or less, 43 % target 0 and ≈ 2 % target 1 or more. 32 of 88 music scripts end on a fade to 0. `fadeSound`: 31 calls, targets 0, 0.1 and 1 only. `setAccTime 0.2` is the slow-motion outro beat (46 campaign calls) |
| Dialogue and radio | `say`: 90 SP calls and 1,088 campaign calls (110 of 118 entries). `CfgSounds` in 100 campaign entries (median 5 classes); 92 % of entries have subtitles; `forceTitles=1` appears 84 times. A `.lip` file sits beside 85 % of mission `CfgSounds` entries but only 1 of 765 radio lines. `CfgRadio` in 20 of 24 SP and 76 of 118 campaign entries. All 799 official radio classes carry a volume (the `sound[]` array requires one), which CWR ignores; 769 of them are `db-40` (1 % amplitude), which would be near-silent if 1.99 honoured it (§2.2, AP5) |
| Audio files | 1,971 mission audio files, 1,968 of them OGG; 99 % mono; 22.05 kHz 61 %, 44.1 kHz 36 %; median clip 4.2 s. Audio is ≈ 93 % of campaign bytes. MP missions: median 141 KB in total |
| Dressing and life | Wrecks, ruins, graves or pre-destroyed units in 20 of 142 missions (median 2.5 objects); civilians in 13 of 118 campaign and 2 of 24 SP entries; `drop` 11 calls in 3 campaign entries |

**Reading.** BI built atmosphere from light, a forecast, a few emitters and one well-placed cue, and spent its audio budget on dialogue. A tool can fill the gaps BI left: life in towns, night lighting, deliberate composition, and emitters placed where the player can actually hear them (§2.2, §5.4).

## 2. The engine toolbox, per profile

**Availability at a glance [V].** All three profiles register the Intel fields, `skipTime`, `setOvercast`, `setFog`, `setRain`, `setViewDistance`, `setAccTime`, `daytime`, `playMusic`, `fadeMusic`, `musicVolume`, `fadeSound`, `soundVolume`, `playSound`, `say`, the `title*`/`cut*` families, the four radio and chat channels, `enableRadio`, `showRadio`, `drop`, `inflame`, `inflamed`, `switchLight`, `lightIsOn`, `camCreate` and `createVehicle`. **Cwr and Ce only:** `setDate`, `createShell`, `soundLength`, `voiceLanguage`, `setSoundEffect`, `setMusicEffect`, `setTitleEffect`, `setEffectCondition`, per-language voice files and the Intel `viewDistance` key. **No profile has** `fadeRadio`, getters for overcast, fog, rain or date, `setWind`, `say3D`, `playSound3D`, or any command that creates a light or sets its colour or brightness (`CWR:Game/Commands/GameStateExt.cpp#L855-L916, #L987-L1071, #L1124, #L1178, #L1208`; the same set in `CE:Game/Commands/GameStateExt.cpp`; names-only scan of the 1.99 executable). The agent's tool schema and the command catalog (doc 23) must never offer the missing ones.

### 2.1 World: time, light, weather, sight and effects

| Area | Controls | Cwa199 | Cwr / Ce | Key facts | Evidence |
| --- | --- | --- | --- | --- | --- |
| Date and time | Intel `year`, `month`, `day`, `hour`, `minute` per section; `skipTime`; `daytime`; `setAccTime` | ✓ | ✓, plus `setDate` | `skipTime` moves the clock and relights the scene; weather does not advance. Weather drift runs on scaled time, so `setAccTime` speeds it up | `CWR:Game/Commands/GameStateExtUi.cpp#L1757-L1769`; `CWR:World/WorldInit.cpp#L242-L268` [V] |
| Sun and moon | Date, time, island latitude | ✓ | ✓ | Latitude −40 in engine sign (40° N), inherited by every stock island and Noe. Longitude is read but unused. The moon is a fixed 28-day orbit | `CWR:Graphics/Rendering/Lighting/Lights.cpp#L80-L276`; `CWR:World/WorldInit.cpp#L963-L968` [V] |
| Intel weather | `startWeather`/`forecastWeather` (overcast), `startFog`/`forecastFog` | ✓ | ✓, plus Intel `viewDistance` (the stock editor drops it on re-save) | Start moves linearly to forecast over 30 game minutes. At 30 min, and then every 1 h 32 min to 13 h 32 min, the engine picks a new random target (overcast ±0.5, fog ±0.2) and ramps to it over that interval. The editor slider shows 1 − overcast | `CWR:World/WorldInit.cpp#L242-L251`; `CWR:World/WorldSetup.cpp#L1254-L1283` [V]; doc 03 L610 |
| Scripted weather | `t setOvercast v`, `t setFog v`, `t setRain v` | ✓ | ✓ | One shared setter: each call re-targets the *other* value to its current level, so two calls in a row cancel the first ramp. `t ≤ 0` snaps the value and schedules random drift for the next frame; `t > 0` postpones drift until t has passed | `CWR:World/WorldSetup.cpp#L1285-L1317`; `CWR:Game/Commands/GameStateExtUi.cpp#L1807-L1823` [V] |
| Rain and thunder | Overcast; `setRain` | ✓ | ✓ | Maximum rain is 1.5·overcast − 1. Rain is forced to 0 at overcast ≤ ≈ 0.673; above that natural rain wanders within [0, max] (at most 0.5). Thunder starts when max rain ≥ 0.4 (overcast ≥ ≈ 0.93): bolts land ≥ 300 m from the camera, with the far sound beyond 1 km. Rain above 0.1 cross-fades the ambience to the Rain bed | `CWR:World/Terrain/Landscape.cpp#L459-L465, #L558-L652`; `CWR:World/WorldImpl.cpp#L984-L994`; `CE:World/Terrain/Landscape.cpp#L563` [V] |
| Sky and wind | Overcast | ✓ | ✓ | Direct sun × (0.8·skyThrough + 0.2): 20–28 % from overcast ≈ 0.66. Wind random-walks within ±(4·overcast + 1) per axis, plus a fixed (4, 2)·overcast bias and gusts. No command sets wind or lightning, and there is no snow | `CWR:World/Terrain/Landscape.cpp#L425-L546, #L685-L758`; `CWR:World/Scene/Scene.cpp#L485-L492`; a grep of `CWR:World` and `CWR:Graphics` finds no snow code [V] |
| Sight | Fog, rain, night, view distance | ✓ | ✓ | One range sets both the rendered horizon and the AI's tactical fog (table in §2.3) | `CWR:World/Terrain/Landscape.cpp#L654-L683`; `CWR:World/Scene/Scene.cpp#L138-L145` [V] |
| View distance | `setViewDistance` | ✓ | ✓ | Clamped to 100–5000 m. Objects are drawn to ⅔ of it and shadows to 5/18 (at most 500 m). It also moves the sound earshot (§2.2) | `CWR:UI/Settings/ViewDistance.hpp#L20-L60`; `CWR:Game/Commands/GameStateExtUi.cpp#L1774-L1805` [V] |
| Fire | Placeable `Fire`; `inflame`, `inflamed` | ✓ | ✓ | Starts unlit. When lit: a flickering orange point light, smoke and a looping crackle. Soldiers within 5 m who face it get light and put-out actions. The state is networked | `CWR:World/Scene/Fireplace.cpp#L19-L286` [V] |
| Street lamps | Terrain objects; `switchLight` ON/OFF/AUTO; `lightIsOn` | ✓ | ✓ | AUTO turns lamps on before 07:12 and after 16:48 in every season. A lamp goes dark at total damage ≥ 0.3 or bulb damage ≥ 0.5 | `CWR:World/Scene/ObjectClasses.cpp#L243-L293` [V] |
| Headlights | AI behaviour; the `action` command's "LIGHT ON" for player-commanded vehicles | ✓ | ✓ | At night: CARELESS and SAFE → lights on; AWARE → cars and motorcycles lit, tracked and air vehicles dark; COMBAT and STEALTH → dark. A unit in danger always goes dark, and each AI vehicle switches on at its own night-factor threshold between 0.2 and 0.8 (sun ≈ 4° to 1°) | `CWR:World/Entities/Vehicles/TransportCore.cpp#L1623-L1638`; `CWR:AI/VehicleAI.cpp#L2358-L2381`; `CWR:World/Entities/Vehicles/Ground/Car.cpp#L2271-L2280` [V] |
| Flares and smoke | Illumination and smoke rounds (ammo classes `Flare`, `FlareGreen`, `FlareRed`, `FlareYellow`; `SmokeShell`, `SmokeShellRed`, `SmokeShellGreen`) fired from grenade launchers; scripted spawns | Weapon fire ✓. Scripted spawn [U]: no official mission `camCreate`s a flare | ✓, plus `createShell` | The stock night officer classes already carry flares | Base config (names); `CWR:Game/Commands/GameStateExtWorldConfig.cpp#L1636` [V/U] |
| Dynamic lights | — | ✗ | ✗ | Nothing creates a light or changes its colour or brightness | Registration grep of both clones and the 1.99 executable [V] |
| Particles | `drop` (19 elements, optional object) | ✓ | ✓ (18 or 19 elements) | Local only: in MP every machine must run its own loop | `CWR:Graphics/Rendering/Effects/Smokes.cpp#L2309-L2570` [V] |
| Ambient life | — | ✗ | ✗ | No animals, birds or civilians spawn on their own. The islands' `Sounds` lists are empty. Seagulls exist only through `camCreate "seagull"` | `CWR:World/Terrain/Geography.cpp#L647-L663`; `CWR:World/WorldInit.cpp#L289` [V] |
| Destroyed map objects | `object N` (primary and network objects only), `setDammage` | ✓ | ✓ | Doc 37 §6 owns map-object actions and their typed references | doc 37 §6 [V] |

### 2.2 Sound: beds, emitters, music, dialogue and radio

| Area | Controls | Cwa199 | Cwr / Ce | Key facts | Evidence |
| --- | --- | --- | --- | --- | --- |
| Terrain beds | Automatic, from the island | ✓ | ✓ | Each 50 m cell is Sea, Trees, Hills (above 170 m) or Meadows; the listener blends 4 cells. The night set is used when the night factor exceeds 0.5. Beds are silent 200 m above the ground. Only Malden overrides the global beds | `CWR:World/Terrain/Geography.cpp#L557-L640`; `CWR:World/WorldImpl.cpp#L879-L1023` [V] |
| Environment bed | Effects Environment (`soundEnv`); `setSoundEffect` (Cwr/Ce) | ✓ | ✓ | Replaces the four terrain cells with one bed, everywhere, until another `soundEnv`; trigger deactivation does not undo it. Every section (intro, mission, outro) and every MP client start on the terrain mix again. The switch is an instant cut, and the override plays at half the weight of a uniform terrain bed (≈ −6 dB). Rain above 0.1 still cross-fades to the Rain bed on top. Selecting the base-config `Default` restores the terrain mix. A mission or campaign `CfgEnvSounds` class named `Default` shadows it: its path gets a directory prefix, never matches the engine's sentinel, and leaves the bed silent. A custom class without `soundNight` presumably leaves nights silent [I]. The override is not saved in savegames [I]. Global classes: Default, Rain, Sea, Meadows, Trees, Hills, Combat | `CWR:World/WorldImpl.cpp#L953-L1021`; `CWR:World/Detection/Detector.cpp#L1463-L1466, #L1512-L1529`; `CWR:World/WorldInit.cpp#L740-L741, #L792-L793`; `CWR:UI/OptionsUI.cpp#L283-L338`; `CWR:Audio/SoundScene.cpp#L598-L653`; `CE:World/WorldImpl.cpp#L953` [V] |
| Point emitters | Trigger sound (`soundDet`, a `CfgSFX` class); placed Sound objects | ✓ | ✓ | Picks by probability, then waits a Gauss(min, mid, max) gap plus the clip length; ±2.5 % volume jitter, no pitch variation. Silent beyond the object distance + 500 m from the viewer (≈ 1.1 km at view distance 900, 1.3 km at 1200). The viewer is the player's unit or vehicle in SP, the camera while a camera effect runs, and every player in MP. While culled, an intermittent emitter's gap timer pauses. A non-repeating trigger never stops its emitter. Sound objects cannot be named or stopped. A seamless loop (one sound, no delays) does not restart after a distance cull: the cull ends the loop and its restart timer is set to 10¹⁰ s [V static; AP8 confirms in game] | `CWR:Audio/DynSound.cpp#L42-L80, #L317-L384`; `CWR:World/Simulation/Simul.cpp#L1211-L1235`; `CWR:World/WorldSetup.cpp#L378-L431`; `CWR:AI/AICenterImpl.cpp#L855-L895`; `CE:World/Simulation/Simul.cpp#L1224` [V] |
| Landmark sounds | `Church001`–`003` (bells), `Fountain` (loop) | ✓ | ✓ | Bells strike the hour at about hh:00 (up to a minute early) and the quarters at about :15, :30 and :44. A slip in the case labels repeats the three-quarter strike about 2 minutes later | `CWR:World/Entities/Vehicles/House.cpp#L949-L1110` [V code; I timing] |
| Music | `playMusic`, `fadeMusic`, `musicVolume`; Effects Music; `setMusicEffect` (Cwr/Ce) | ✓; array form likely [I] | ✓, including `[class, start]` | One 2D slot. A track plays once, and a new track cuts the old one. Volume starts at **0.5** in every mission, and `t fadeMusic v` ramps linearly. No crossfade. Stock tracks have class volume 1 and the 2D gain clamps at 1, so `fadeMusic` values above 1 add nothing | `CWR:Game/Commands/GameStateExtUi.cpp#L972-L1032`; `CWR:Audio/SoundScene.cpp#L238-L271, #L537, #L579-L596`; `CWR:Audio/Shared/AudioMath.hpp#L25-L36`; base config `CfgMusic` [V] |
| World hush | `fadeSound`, `soundVolume` | ✓ | ✓ | Scales only accommodated sounds (weapons, vehicles, 3D `say`, emitters, beds). It does not reach `playSound`, Effects Sound, radio or music. Beds scale linearly, but a 3D sound only has its full-level radius shrunk by √v, so a loud sound heard from inside the reduced radius is not quieter at all. `fadeSound 0` stops 3D sounds | `CWR:Audio/SoundScene.cpp#L254-L267, #L569-L640`; `CWR:Audio/Core/VoiceBudget.cpp#L87-L149`; `OAL:WaveOAL.cpp#L822-L880` [V] |
| Dialogue | `say` (3D), `playSound` (2D), Effects Voice (3D) and Effects Sound (2D) | ✓; array `say` likely [I] | ✓, plus `soundLength` | Subtitles come from `titles[]` when the player enabled them or the class sets `forceTitles=1`. They are hidden beyond 100 m from the camera (array form: 0 = any distance). A unit that is still speaking queues its next line | `CWR:Audio/DynSound.cpp#L82-L301`; `CWR:Game/Commands/GameStateExtUi.cpp#L878-L945` [V] |
| Radio | `sideRadio`, `globalRadio`, `groupRadio`, `vehicleRadio` and the `*Chat` forms; `enableRadio`; `showRadio` | ✓ | ✓ | 2D speech. The **config volume is ignored** on Cwr and Ce (Cwa199 after AP5; BI's `db-40` on 96 % of its radio classes suggests 1.99 ignores it too). Lines queue per channel, and the engine plays radio noise under side, group and global lines. Radio audio is skipped while `setAccTime` > 1 (the chat line still appears), group and vehicle channels are off in intros, and outside MP it needs a living player | `CWR:AI/AIRadio.cpp#L1407-L1495`; `CWR:World/WorldSetup.cpp#L878-L932` [V] |
| Effects fields | Camera effect (12 `CfgCameraEffects` classes plus terminate), Sound, Voice, Environment, Trigger sound (triggers only), Music, Title (text, resource or object: `Sphere`, `BISLogo`, `TVSet`) | ✓ | ✓, plus the `set*Effect` commands | Effects run only where the Effects condition holds. Titles always use the title layer | `CWR:AI/AIArcade.cpp#L735-L808`; `CWR:World/Detection/Detector.cpp#L1392-L1510` [V] |
| Titles | Effects title; `title*` and `cut*` commands | ✓ | ✓ | Effects titles, subtitles and `titleText` share the title layer and replace each other | `CWR:Game/Commands/GameStateExtUi.cpp#L1701-L1727` [V] |
| `description.ext` classes | `CfgSounds`, `CfgMusic`, `CfgRadio`, `CfgSFX`, `CfgEnvSounds` | ✓ | ✓ | `sound[] = {file, volume, pitch}`; volumes may be written `dbN`; `CfgSounds` adds `titles[]`, `forceTitles`, `titlesFont`, `titlesSize`; `CfgRadio` adds `title`; `CfgSFX` entries add probability and min/mid/max delay plus an `empty[]` entry; `CfgEnvSounds` has day and night sounds. Lookup order: mission, campaign `dtaExt\`, base config | `CWR:IO/ParamFileExt.cpp#L70-L181`; `CWR:UI/OptionsUI.cpp#L283-L583` [V] |
| Audio formats | Chosen by the last extension | ✓ | ✓ | `.wav` must be RIFF PCM; `.ogg` is Vorbis; anything else loads as WSS. The OpenAL backend makes only mono or stereo, 8 or 16 bit buffers, and presumably does not spatialise stereo [I]; the 1.99 DirectSound path is [U] | `CWR:Audio/Streaming/WaveStream.cpp#L146-L164`; `OAL:WaveOAL.cpp#L21-L26` [V] |
| Lip sync | Sibling `.lip` text file | ✓ | ✓, with language fallback | Frame line plus `time, phase` rows (phase 0–7, −1 closed); pitch-scaled. With no file the mouth does not move. Radio has no lip path | `CWR:World/Entities/Infantry/Head.cpp#L29-L177` [V] |
| Volume channels | The player's Effects, Speech and Music sliders | ✓ | ✓ | `say`, `playSound`, trigger sounds, emitters and beds follow Effects; only radio follows Speech | `OAL:WaveOAL.hpp#L117`; `CWR:AI/AIRadio.cpp#L1447-L1451` [V] |
| Voice budget | — | [U] | ✓ | Only the N loudest 3D sounds play (config default 6, floored at 16 in CWR); the rest resume later | `CWR:Audio/Core/VoiceBudget.cpp#L78-L157`; `CE:Audio/Core/VoiceBudget.hpp#L23` [V] |
| Ear accommodation | — | [I: ported code] | ✓ | An automatic gain on world sounds (×1/256 to ×4, starting at 0.5). It drops fast after loud events and recovers at ≈ +0.4 dB/s for 3D sounds | `CWR:Audio/SoundScene.cpp#L272-L330` [V; I rates] |
| Per-language voice | Sibling `<base>.<voiceLang>.<ext>` | ✗ (base file only) | ✓; `voiceLanguage` | Applies to mission and campaign `CfgSounds`, `CfgRadio` and `CfgSFX`, not to music or beds | `CWR:UI/OptionsUI.cpp#L434-L442`; `CWR:Audio/VoiceLangPath.hpp#L12-L54` [V] |

### 2.3 Reference numbers [I unless marked]

**Sun at 40° N.** A port of `LightSun::Recalculate`, re-run on 2026-09-27; not yet probed in game.

| On the 15th of | Jan | Mar | May | Jun | Aug | Oct | Dec |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Sunrise – sunset | 07:26–16:45 | 06:29–17:43 | 04:58–18:45 | 04:36–19:14 | 05:12–19:07 | 06:14–17:38 | 07:14–16:36 |
| Noon elevation | 28° | 43° | 65° | 72° | 67° | 45° | 28° |

On the default date (10 May) the sun rises at ≈ 05:04, clears 5° at ≈ 05:31, leaves the warm band (25°) at ≈ 07:16, re-enters it at ≈ 16:27, drops below 5° at ≈ 18:12 and sets at ≈ 18:39; stars are full after ≈ 19:36. The default 07:30 is therefore a neutral morning just past the warm light. The engine's seasons run about ten days late (equinox noon peaks of 45.5° and 53.9°).

**Light phases** [V thresholds `CWR:Graphics/Rendering/Lighting/Lights.cpp#L80-L88, #L158-L256`]:

- *Day*: sun above 25°.
- *Warm*: 0–25°. Light and sky take a sunset tint, and the disc reddens below 20°.
- *Night factor*: ramps in from 5° down to 0° (0.5 at ≈ 2.5°). Point lights and their glows appear, AI vehicles switch their lights, and beds switch to night sounds.
- *Afterglow*: 0 to −10°. Direct light fades from red to black while the stars fade in; it is not blue.
- *Night*: below −10°.

Ambient light never falls below 5 %, and the moon adds none. Visible full moons fall around the last day of a month or the first of the next; new moons fall mid-month. Photographers put golden hour at about +6° to −4° and blue hour at −4° to −6° (PhotoPills, PetaPixel; Wikipedia gives 4–8° below for blue hour) [V]. The engine's warm band is wider and its twilight is red, so presets name the engine's own phases: "Golden" targets 3°–15° and "Afterglow" 0° to −8° [I].

**Sight range** at view distance 1200 m, in daylight, with no rain and overcast below 0.65:

| Fog | 0 | 0.1 | 0.2 | 0.3 | 0.4 | 0.5 | 0.6 | 0.75 | 0.9 | 1.0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sight (m) | 1200 | 1022 | 857 | 705 | 567 | 472 | 387 | 259 | 131 | 45 |

Rain 0.5 gives ≈ 775 m. Night, or overcast ≥ ≈ 0.91, caps sight at ≈ 900 m.

**Weather marks.** 0.66: flat grey light. 0.673: rain possible. 0.93: thunder. At overcast 0.95 there is a bolt about once a minute on average; at 1.0, about every 15 s.

**Positional carry.** The full-level radius is 30·√(volume · accommodation · soundVolume). Beyond it the level falls 6 dB per doubling of distance, down to a −40 dB floor at 100× the radius. At accommodation 0.5: `db-40` ≈ 2 m, `db-10` ≈ 12 m, `db+20` ≈ 67 m, `db+40` ≈ 212 m [V formula `CWR:Audio/Shared/AudioMath.hpp#L8-L47`; `OAL:WaveOAL.cpp#L822-L887`]. BI's distant-gunfire classes (volume 0.1) have a ≈ 7 m radius and reach their floor at ≈ 670 m. In a quiet scene accommodation can climb to 4, which widens that radius to ≈ 19 m and moves the floor out to ≈ 1.9 km; either way, beyond ≈ 0.7 km the simulation cut-off, not the level, decides whether an emitter is heard. The floor belongs to software mixing: the 100× maximum distance is the software DirectSound path that CWR reproduces, while the old hardware path used an effectively unlimited maximum distance [V `CWR:Audio/Shared/DX8Reference.hpp#L74-L94`]; which path 1.99 takes on a given machine is (unverified).

**Music level.** 0.5 is the default (0 dB); 0.35 ≈ −3 dB; 0.25 ≈ −6 dB; 0.16 ≈ −10 dB; 1.0 = +6 dB, which is also the ceiling for stock tracks (§2.2).

### 2.4 Mods

CWE replaces stock weather with a scripted system that scripts can read back (start and forecast values, rain, fog, transition times). Its readmes ask mission makers not to call `setRain`, `setFog`, `setOvercast` or `fadeSound` directly, but to use its own functions. Its Dynamic Sound System is an external helper program, driven through Fwatch, that plays gun sounds chosen by distance tier and surroundings (forest, hill, town, indoors, …). It is forced on with `-dss`, off with `-nodss`, and always on in MP [V local readmes and folder names]. Earlier community packs (ECP, FlashFX) mostly added effects: fire, smoke, dust, random weather and snow, radio chatter [V/V-search]. Plotroom treats all of this as optional mount data (doc 27): missions must sound right on vanilla, and CWE targets get CWE-aware lowering and lints (AU13, AL17).

### 2.5 Corrections for sibling docs (to file as design-gap requests)

1. **Doc 34 ed12.** `soundEnv` is a global bed switch that lasts until it is replaced, restored with `Default` or the section ends; it is not an ambient zone, and switching it is an instant cut. A music "crossfade" is a dip (fade out, switch, fade in), because only one track can play.
2. **Doc 32 §2.5 and the doc 23 catalog.** Official content that ships with 1.99 uses `playMusic [class, start]` (43 of 88 music scripts) and `say [class, 0]`, some calls with a third element (30 calls, Resistance). Both forms therefore very likely work on Cwa199 [I]; probe AP3 confirms. The third `say` element sets the subtitle speed, not the audio.
3. **Rain threshold in docs 31 and 32.** Both use 0.7, while the engine's threshold is ≈ 0.673. Keep 0.7 as the compiler's safety margin, and quote the real value in lints.
4. **Doc 35 rc08, "one cue per mission, no repeats".** The rule comes from community campaigns; BI used about two `playMusic` calls per mission where it used music at all. Keep it as a default, not a rule.
5. **Doc 35 rc43.** Its defaults (hour 7, overcast 0.3) work as *values*, but the Director instead asks for the light as the first mood choice and never leaves the engine default in place silently (AL01).

## 3. The Atmosphere Director

### 3.1 Principles

- One **Atmosphere card** per mission section (Intro, Mission, OutroWin, OutroLoose). Each is linked to the Mission card by default, and a time jump is shown explicitly ("intro 04:30 → mission 05:10").
- The user or the model chooses a **mood**. Code solves every number for the island, date and profile, and prints the consequences before anything is applied.
- The output is ordinary content: Intel fields, compiler-owned init lines, objects, triggers, `description.ext` classes and timeline cues. Each is tagged with the preset and the step that made it (glass box). Editing any of them marks the card *customized*, and regeneration never overwrites customized or pinned values.
- **Profile honesty.** A control no profile offers (wind direction, valley fog, light colour, snow) is shown locked with its reason and is never faked. These gaps, and the others in §2 (no light creation, weather getters, music crossfade or `fadeRadio`; the ignored `CfgRadio` volume), are candidates for the engine-requests register under `docs/upstream/` that AGENTS.md requires; once filed, a locked control links to its entry. The panel layout follows later Armas' environment attributes (paired start and forecast values, a "time of changes") and named weather states [V: BIKI Eden Scenario Attributes; Reforger `TimeAndWeatherManagerEntity`], lowered to what CWA can do.

### 3.2 Mood presets

The first menu offers seven families: Dawn, Day, Dusk, Night, Storm, Aftermath and Season. Each preset has three intensities (subtle, standard, strong) that scale fog, overcast, emitter counts and cue levels.

| ID | Preset | Light (solved) | Weather start → forecast | View distance (m) | Lights, effects, dressing | Soundscape (§5.4) | Cue plan (§5.2) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AM01 | Dawn fog patrol | First light: sun −4° to +5° at start; May–September | Overcast 0.2–0.4 → 0.2; fog 0.3–0.5 → 0 (lifts over 30 min) | 1200 | — | SX03 dawn chorus; cock and dogs near villages | QP1 |
| AM02 | Golden evening | Sun 3°–15°, setting behind the objective | Overcast ≤ 0.4 (kept below 0.66); fog 0–0.1 | 1500–2000 | Church bells timed to arrival (§3.5) | SX03 birds, SX05 village | QP1, soft outro |
| AM03 | Still hot noon | 11:00–14:00, June–August | Overcast 0–0.1 → 0–0.2; fog 0 | 1600–2000 | — | Terrain bed (field crickets) only; dogs as tells | QP6 (silent until contact) |
| AM04 | Grey occupation | Mid-morning or afternoon | Overcast 0.66–0.8 (flat light; above 0.673 light rain up to 0.2 can fall); fog 0.1–0.2 | 1000–1200 | Lamps OFF in the occupied town | SX05, sparse (crows, a mournful dog) | QP2 |
| AM05 | Storm rolling in | Afternoon or dusk | Overcast 0.4 → 0.8 (rain possible ≈ 20 min in); fog 0.1 → 0.2 | 1200 | — | Terrain bed; the rain bed arrives by itself | QP1, with nothing after the rain starts |
| AM06 | Storm at night | 22:00–03:00 | Overcast ≥ 0.95, held; fog 0.1 | 900–1200 | Lightning (≈ 1 bolt a minute); lit fires under cover | Engine rain and thunder only | QP6 |
| AM07 | Dark night raid | 00:00 until the sun reaches −10° (afterglow gone): ≈ 03:30 on 15 June, ≈ 04:00 on 15 May, ≈ 06:15 in December (ported sun model) | Overcast 0.2, held; fog 0–0.1 | 900 | Town lamps OFF (blackout) or AUTO; lit sentry fires | SX04 night field; dogs as tells | QP3 |
| AM08 | Flare-lit night assault | 22:00–02:00 | Overcast 0.3; fog 0 | 900–1200 | Flare magazines for the squad; scripted flare beats (Cwr/Ce; Cwa199 only after AP9) | SX06 distant battle in the earshot band | QP4, with a tension cue at H-hour |
| AM09 | Burning village aftermath | Late afternoon to dusk | Overcast 0.5–0.7; fog 0.1–0.2 | 1000 | Lit fires, `drop` smoke columns, wrecks, bodies, graves, destroyed map buildings (§4.2) | SX05 crows and a mournful dog; no birdsong | QP2, elegy at −6 dB |
| AM10 | Winter quiet | A December–February date: low sun (≤ 28°), short day | Overcast 0.5–0.7; fog 0.2 | 1000 | AUTO-lamp gap fixed (AL09) | Sparse: crows, wind on hills | QP1, very sparse |
| AM11 | Front line | Day, any phase | Overcast 0.3–0.5 → +0.1 | 1200 | A real skirmish within reach (AL12) | SX06 distant battle; optional Combat bed; SX08 radio chatter | QP4 |
| AM12 | Clear long-range day | 09:00–16:00 | Overcast 0–0.2; fog 0 | 2000–3000 (performance note on Cwa199) | Vista start (§4.3) | SX03 birds | QP1, with the intro cue on the reveal |

In stock CWA, "winter" is light and sky only: vegetation stays green and there is no snow [V], and the card says so. The thunder in AM06 and the flares in AM08 carry a photosensitivity note (§8.2). The moods that retrospectives remember (dawn over the island and a walk at sundown, NME 2022 [V]; constant radio chatter and enemies as specks on the horizon, GameSpot 2001 [V-search]; plus fire at night) map onto AM01, AM02, AM11, AM12 and AM07, which form the default gallery for new users.

### 3.3 Consequence card

For every preset, and for every manual edit in the panel, code computes and shows: the sight range at start and after the 30-minute ramp; the sun phase at the start and at the estimated end; whether rain is possible, whether thunder occurs, and the wind band; the time point lights become visible; the enemy's night-vision share and the resulting AI sight factor at night; the earshot ring for trigger sounds; lamp twilight gaps (AUTO switching against the night factor); church-bell times near the route; the music budget used; and performance notes (view distance on Cwa199, particle rate, emitter count). A consequence that conflicts with the mission, such as a 600 m sniper objective in fog 0.5, becomes a lint (§6), never a block. So that the card informs without overwhelming, it leads with three chips (sight, light phase, sky) and folds the rest under *Details*; Easy mode shows only the chips (doc 09 M2) [I].

### 3.4 Weather and time timeline

The mission timeline (doc 32) gains an **Environment** band:

- **Sun track.** The elevation curve, coloured by phase, with sunrise, sunset and the 5° line marked. `skipTime` keyframes show as jumps.
- **Overcast and fog tracks.** The Intel ramp from start to forecast over the first 30 minutes, then a shaded band for possible random drift. The first random re-target fires as the Intel ramp ends at 30 min; each re-target moves up to ±0.5 overcast and ±0.2 fog, linearly over 1 h 32 min to 13 h 32 min, so drift is at most ≈ 0.33 overcast and ≈ 0.13 fog per hour [V `CWR:World/WorldSetup.cpp#L1265-L1279`]. Horizontal guides mark 0.66, 0.673 and 0.93.
- **Director keyframes** (doc 31 module 15). `Ramp` (one gradual change at a time, serialised), `Hold` and `Skip`. A *hold* lowers to an instant set followed by the same value with a long time, for example `36000 setOvercast v`. Wanted then equals actual, the ramp speed is zero, the other value stays at its current level, and the next random change is 10 hours away [I from `CWR:World/WorldSetup.cpp#L1285-L1317`; AP2]. The target does not need to be re-issued periodically, with three limits. Both calls must run in the same statement or frame. Every later `Ramp` ends the hold, because when its time is up the engine picks a new random target, so the compiler appends a fresh hold pair at each ramp's end [V `CWR:World/WorldSetup.cpp#L1266-L1279, #L1309-L1316`]. And the 10 hours are weather time, which `setAccTime` speeds up and `skipTime` does not advance. Rain is not held: above overcast 0.673 it still wanders within its band.
- **Rain.** A "possible" band derived from overcast. `setRain` keys are allowed only inside it, and the card says that rain above 0.5 will not last.
- **MP.** Each machine runs its own drift from the same Intel values [V: no weather sync in `CWR:Network`]. The Director's "deterministic weather for MP" option therefore holds the weather on every machine and runs every change from triggers or init lines, never from server-only scripts. What join-in-progress clients see is [U] (AP16).

### 3.5 Previews

| Preview | What it shows | Source of truth |
| --- | --- | --- |
| Sun bar | Sunrise to sunset for the chosen date and island, phase colours, the chosen minute, and a moon chip labelled "visual only" | Ported sun model (AD0) |
| Sight ring | A circle at the sight range around the player start, route points and objectives, updated live from fog, rain, night, overcast and view distance | §2.3 formula |
| Earshot rings | ⅔·view distance + 500 m around the planned route; emitters outside every ring are greyed as "never heard" | §2.2 |
| Ambience overlay | Sea, trees, meadow and hills cells from the island's WRP and objects, with day and night beds. An active `soundEnv` override appears as a global banner on the timeline | Engine rules (§2.2), computed when the island is indexed |
| Lights layer | Fires (lit or cold), lamps (ON, OFF, AUTO) and flare beats, each with "visible from HH:MM" | §2.1 |
| Bells | Churches on the map with their next strikes on the mission clock | §2.2 |
| Live screenshots | On Cwr and Ce builds that carry the Preview harness (doc 08: loopback `eval` and `screenshot`), the preset is rendered from chosen camera points at the start and at +30 min. The images stay in the user's cache | doc 08 [V]. Cwa199 has no harness, so its previews are static and labelled as such |

### 3.6 Types (proposal-only sketch)

```rust
/// Proposal-only. The atmosphere of one mission section. Code owns it; every field is editable in native panels.
pub struct SectionAtmosphere {
    date: GameDate,                // Intel year/month/day
    start: StartTime,              // a clock time or a solved sun phase
    weather_start: Weather,        // Intel startWeather / startFog
    weather_forecast: Weather,     // Intel forecastWeather / forecastFog
    view_distance: Option<Metres>, // lowered to an init line, which every profile reads
    linked_to_mission: bool,
    provenance: Provenance,        // preset, intensity, workflow step and model that produced it
    pins: PinSet,                  // user-edited fields that regeneration must keep
}
pub enum StartTime { Clock(HourMinute), Phase { phase: SunPhase, edge: PhaseEdge, offset: Minutes } }
pub enum SunPhase { Night, Afterglow, FirstLight, Warm, Day }
/// The newtypes clamp to 0..=1 at construction, so an out-of-range weather value cannot be represented.
pub struct Overcast(f32);
pub struct Fog(f32);
pub struct Weather { overcast: Overcast, fog: Fog }
pub enum WeatherKey {
    Ramp { at: MissionTime, target: WeatherTarget, over: Seconds },
    Hold { at: MissionTime, duration: Seconds },
    Skip { at: MissionTime, hours: Hours },
}
pub enum WeatherTarget { Overcast(Overcast), Fog(Fog), Rain(RainDensity) }
pub struct MoodPresetId(u16);
pub enum Intensity { Subtle, Standard, Strong }
/// Derived, never stored as truth: recomputed whenever an input changes.
pub struct Consequences {
    sight_at_start: Metres,
    sight_after_ramp: Metres,
    rain: RainOutlook,
    thunder: bool,
    point_lights_visible_from: Option<HourMinute>,
    enemy_nvg_share: Option<Fraction>,
    earshot: Metres,
    lamp_gap: Option<Minutes>,
    notes: Vec<ConsequenceNote>,
}
```

### 3.7 Compiling per profile

| Element | Cwa199 | Cwr / Ce | CWE mount |
| --- | --- | --- | --- |
| Date, start time, weather arc | Intel fields per section; days advance only through `skipTime` | Same, plus `setDate` for mid-mission date changes | Same, plus CWE's own weather data |
| View distance | A compiler-owned `setViewDistance` init line | Same; the Intel key is avoided because the stock editor drops it | Same |
| Weather keys and holds | `setOvercast` and `setFog` serialised; `setRain` only inside the rain band | Same | CWE's functions; stock commands are linted (AL17) |
| Fires, lamps, headlights | `Fire` with the init line `this inflame true`; `switchLight` on typed map-object references (doc 37 §6); group behaviour for headlights | Same | Same |
| Flares | As gear; scripted beats only after AP9 | `createShell` beats | As Cwr/Ce, or as the mount allows |
| Smoke columns | Doc 31 module 16 effects (seen and edited as effect markers with preset, duration and intensity), lowered to bounded 19-element `drop` loops run on every machine | Same | Same |
| Soundscape | `soundDet` triggers, Sound objects, `soundEnv` and `Default` | Same, plus `setSoundEffect` | Same; the DSS stays outside Plotroom |
| Music, fades, ducking | `playMusic` and `fadeMusic`; start offsets after AP3; waits from lengths measured at import | Same, plus `soundLength` | `fadeSound` through CWE's function (AU13) |
| Voices | Base files only | Language siblings | As the base game |

A test compiles every preset for all three profiles and runs the lints on the result (AMT1).

## 4. Scene dressing and composition

### 4.1 Stock palette [V: base config, scope 2 unless noted; names only]

| Role | Classes |
| --- | --- |
| Wrecks | `JeepWreck1`–`3`, `M113Wreck`, `UralWreck` |
| Human cost | `Body`, `Grave`, `GraveCross1`, `GraveCross2`, `GraveCrossHelmet` |
| Camps and aid | `Camp`, `CampEmpty`, `CampEast`, `CampEastC`, `ACamp`, `MASH`, `Fire`, `Table`, `Tablemap`, `Barrels`, `Barrel1`–`4`, `Paleta1`, `Paleta2` |
| Checkpoints and defences | `Fence`, `Wire`, `WireFence`, `Fortress1`, `FlagCarrier`, `HeliH` |
| Sound landmarks | `Church001`–`003` (bells), `Chapel`, `Fountain` (looping) |
| Sound objects | `Owl`, `Stream`, `Frog`, `Frogs`, `Alarm`, `BirdSinging`, `Crickets1`–`4`, `Chicken`, `Cock`, `Cow`, `Crow`, `Wolf`, `Dog`, `BadDog`, `SorrowDog`, `LittleDog`, `Music` (a barrel organ) |
| Not placeable | Ruined houses (`Housedumruina*`, scope 1); `Crater` (an internal class with no model); street lamps (terrain objects). The editor lists only scope 2, but on Cwr and Ce a script can still `camCreate` a scope-1 class such as a ruin [V `CWR:World/Entities/Vehicles/VehicleTypes.cpp#L270-L277`; `CWR:Game/Commands/GameStateExtUi.cpp#L1425-L1431`]; on Cwa199 (unverified). Whether a script can spawn a usable crater is (unverified). Otherwise craters come from explosions, and ruins from destroying map buildings |
| Effects | `drop` smoke and fire (§2.1). Smoke from a destroyed vehicle's engine lasts only ≈ 10–16 s [V `CWR:World/Entities/Weapons/Dammage.cpp#L588-L613`]; how long wrecks burn is [U] (AP10) |

### 4.2 "What happened here" kits

The model supplies a story tag and one detail token (for example "ambush, dawn, the lead truck"). Code composes the objects on valid terrain, off the critical path, links them to a briefing line or objective, and records a "why it exists" note.

| Kit | Story question | Objects (range) | Sound | Notes |
| --- | --- | --- | --- | --- |
| Ambushed convoy | Who hit them, and are they still here? | 2–3 wrecks on a road, 1–3 bodies, scattered barrels | Crows; distant shots if the ambushers remain | Wrecks follow the road's heading; one wreck doubles as a map-visible landmark |
| Abandoned camp | Where did they go, and when? | Tents, a cold `Fire`, table and map, barrels | Silence, or a mournful dog | The cold fire is a deliberate prop, not an AL08 finding |
| Fresh graves | Who paid for this ground? | 2–5 graves by a church or chapel | Church bells timed to the player's arrival | Links to a name in the briefing |
| Field hospital | How bad is the front? | `MASH`, tents, bodies, a flag | Radio chatter lane, distant battle | Pairs with AM11 |
| Checkpoint | Who controls this road? | Wire, fence, flag, barrels, a manned or empty post | Dogs, radio | The manned version uses doc 31's garrison module |
| Village that fought back | What happened to the people? | 1–3 destroyed map buildings (doc 37 §6), wrecks, bodies, lit fires, a smoke column | Crows, a mournful dog, no birdsong | The core of AM09 |
| Evacuated village | Why is nobody here? | Parked civilian cars, a barking dog, lamps OFF at night | Dog, wind | The explained absence that satisfies AL14 |
| Burning farm | A warning or a mistake? | Lit fires, a smoke column, cow and chicken emitters | Animal emitters | The smoke `drop` runs locally in MP |

Kits are optional finds and never gate progress. The default budget is 1–3 kits of 2–6 objects each per mission (§4.5).

### 4.3 Composition helpers

- **Vista finder.** Using the island heightfield and object heights, code scores viewpoints near the planned start and route for openness, a landmark in frame (named places from the island's names list, church towers, hilltops, the coast), water or valley depth, and the sun's direction at the chosen hour (side light for warm presets, backlight for silhouettes). It proposes the start facing, a postcard spot for the intro (doc 39's establishing shot), and a reveal point where the objective first comes into view.
- **Landmark sightlines.** Line of sight from route points to the objective within the current sight range. Info lints fire when the objective is visible the whole way (no reveal) or is never seen before the last 200 m (no anticipation).
- **Opening checklist.** Within the first 15 s the player should know where, when and why: a title card, a landmark in frame, and the light and weather mood (Carson).

### 4.4 Life

Every settlement on the player's route gets at least one sign of life or an explained absence (the evacuated-village kit). Signs of life include a civilian group from doc 31's ambient-population module, a dog or cockerel emitter, and a lit fire or lamp at night. Seagulls over the coast can be `camCreate`d locally. The UI says plainly that the game adds none of this by itself.

### 4.5 Restraint budget

Each mission shows a visible meter: 1 weather arc; 1–3 vignette kits; 1–2 music cues plus an optional stinger; up to ≈ 20 distant-battle emitters and ≈ 15 nature emitters; and no more than ≈ 6–8 emitters overlapping at any one spot (the voice budget, §2.2). Going over the budget produces an info note ("consider cutting"), never a block, and human choices win.

## 5. Sound and music

### 5.1 Mental model

Every audio cue carries a typed diegesis: **World** (in-fiction sounds and speech), **Score** (music), **Radio** (in the fiction, but it informs the player the way UI does; applying Jørgensen's "transdiegetic" sound (2007) to radio is our own reading [I]) or **Caption** (text only). Game-audio practice builds ambience from **beds** (looping tone), **scatter** (randomised one-shots) and **spots** (story sounds) (Game Audio Learning Portal) [V]. CWA maps onto this directly: terrain beds and `soundEnv` are beds, `CfgSFX` emitters are scatter, and `say`, `playSound` and Effects sounds are spots. The editor uses the same lanes, so users learn one model. Score cues must never carry objective information (AU24).

### 5.2 Music cue planner

| Phase | Default | Allowed | Transition rule | Level |
| --- | --- | --- | --- | --- |
| Intro / establishing | One cue from the first shot or the cut from black | A start offset ("come in at the swell") | Fade in over 2–4 s from a pre-muted level; fade out over 6–8 s when control starts | 0 dB (0.5) |
| Calm / approach | Silence | A low cue for long transport legs (QP5) | — | −8 dB |
| Tension | Silence, or one stinger on a reveal | A tension cue in stealth plans | Dip if something is already playing | −3 to −6 dB |
| Contact / firefight | **Never scheduled** by the planner; a hand-placed cue gets MC19 (warn, dismissible as "intentional") | — | Fade to 0 over 2–3 s at first contact | — |
| Victory | Outro cue | — | Fade in over 2 s | 0 dB |
| Defeat | Silence, one line, cut | A low cue in cutscenes | — | −6 dB |
| Aftermath | Silence | An elegy (QP2) | Slow fade in over 4–6 s | −6 dB |

**Silence budget.** By default at least 70 % of the estimated play time has no score, and the planner leaves the first contact unscored [I]. **Cue budget.** One opening or outro cue and at most one stinger. By default a track is not reused within a campaign, and AU17 notes a repeat. Cutscene cues follow doc 39's archetype audio plans.

| Plan | Shape |
| --- | --- |
| QP1 Classic OFP | Opening cue; silence in play; an optional stinger of ≤ 40 s at an objective; an outro cue on a win; silence on a loss |
| QP2 War film | QP1 without the stinger, plus a shell-shock beat at the first big explosion and an elegy only in the aftermath |
| QP3 Night stealth | Night bed and tells; no music until detection; on alarm, a tension cue at −6 dB, released on escape |
| QP4 Big battle | An opening march cue, then nothing until the ending; distant battle and radio carry the middle |
| QP5 Transport leg | A long, low cue at −8 dB during travel, ducked under intercom lines spaced 20–40 s apart |
| QP6 Silent | No score at all; world sound and radio only |

Official stock tracks are picked by class name from the base catalog (21 classes, plus 13 in the Resistance addon). Their names carry almost no mood information, so Plotroom supplies its own mood, tempo and length tags, with facets for stingers (≤ 40 s) and beds (> 2 min). Lengths are measured from the user's own install at index time and kept in the user's cache. The picker auditions stock tracks and sounds by decoding them from the user's install at play time; decoded audio never leaves the machine and is never written into a mission, an export or a shared preset (doc 02 §3.4) [I].

### 5.3 Fades, dips and ducking (compile rules)

- **Levels in dB.** Levels are edited in dB relative to the default, where 0 dB = `fadeMusic 0.5`. Values above 0 dB are allowed but flagged (AU06); `fadeMusic 1` is +6 dB.
- **Dips.** A change of track compiles to a dip: fade out (0.5–3 s), `playMusic`, fade in. A new track starts at the current music volume, so after a fade to 0 the compiler always adds the fade back up.
- **Soft fades.** A soft fade is 2–3 piecewise-linear `fadeMusic` segments, because a single linear amplitude ramp sounds abrupt at the tail.
- **Intensity variants.** Adaptive scores either switch between pieces (horizontal re-sequencing) or add and remove layers (vertical layering) (Wikipedia, "Adaptive music"; Phillips 2021) [V]. With one slot CWA can only switch, but `playMusic [class, offset]` can jump between pre-mixed intensity variants of the same piece at the matching offset. The jump is an instant cut, so it is seamless only for phase-aligned variants; otherwise the compiler wraps it in a 0.3–0.5 s dip [I]. Cwr/Ce; Cwa199 after AP3.
- **Ducking.** The engine never ducks music under speech. A per-line toggle, on by default for Radio and Say lines while a Score cue plays, compiles to `0.3 fadeMusic <duck>` before the line and `1.5 fadeMusic <restore>` after its measured length (`soundLength` on Cwr and Ce). Presets: Light −4 dB, Clear −8 dB, Hard −12 dB. The −4 dB, 0.3 s example comes from a practitioner Wwise tutorial [V example; I depths].
- **Hush the world** (`fadeSound`). To really drop the world, target ≈ 0.01–0.03, because 0.1 lowers distant 3D sounds by only ≈ 10 dB and leaves a loud sound within ≈ ⅓ of its full-level radius untouched (0.01 still spares the inner tenth). Hold 4–6 s and restore over 6–8 s. Voice-over, radio and music keep playing. Only `fadeSound 0` silences every 3D sound, by stopping it.
- **Effects Music.** An Effects Music field on a trigger is fine for a single cue. Its fade lines go into the same trigger's On Activation, which runs before the Effects [V `CWR:World/Detection/Detector.cpp#L1335-L1487`].
- **Visibility.** Every fade is a visible ramp on the timeline.

### 5.4 Soundscapes

| ID | Layer | Built from (stock class names) | Placement rule |
| --- | --- | --- | --- |
| SX01 | Terrain bed | The engine, automatically | Shown as an overlay. Plotroom never adds generic nature beds on top |
| SX02 | Global bed override | `soundEnv` (for example `Combat`, `Hills`) and `Default` | Drawn on the timeline, not the map; always paired with a restore unless the user opts out (AU07). In SP an enter/exit pair keyed to the player can stand in for a zone, but each crossing is an audible hard switch; MP is open question 5 |
| SX03 | Dawn and day birds | `skylark`, `forestlark`, `hedgesparrow`, `jay`, `BirdSingingSfx`; `SeagullSfx` on coasts | 3–8 emitters inside earshot, off the route; optional quiet-on-alarm |
| SX04 | Night field | `CricketSfx`, `Cricket1Sfx`–`Cricket3Sfx`, `OwlSfx`, `owl`, `nightingale`; `FrogSfx` and `FrogsSfx` near water | 3–8 emitters; day and night tags checked (AL13) |
| SX05 | Village and farm | `DogSfx`, `LittleDogSfx`, `BadDogSfx`, `SorrowDogSfx`, `CockSfx`, `ChickenSfx`, `CowSfx`, `crow2`, `CrowSfx` | One or two per settlement; dogs double as stealth tells |
| SX06 | Distant battle | `CA_AK`, `CA_M16`, `CA_Expl1`; optionally the `Combat` bed as a far layer | 8–20 emitters in the band between the reachable area and the earshot ring, gated by a phase flag and repeating so that the war can stop; timers staggered; drawn as a translucent "front" |
| SX07 | Alarm | `AlarmSfx` (a seamless siren loop) on a trigger | Starts on an alarm flag; keep it inside earshot, because it will not restart after a cull. SX03 bird emitters stop on the same flag, which needs repeating triggers (only deactivation stops a trigger emitter). A placed `Alarm` object sounds from mission start (only its presence condition, checked once, can drop it) and cannot be stopped; a script-created one is silent on Cwr/Ce [V `CWR:AI/AICenterImpl.cpp#L855-L895, #L1403-L1415`; `CWR:World/Entities/Vehicles/VehicleTypes.cpp#L757-L760`] |
| SX08 | Radio chatter | `CfgRadio` lines on side radio at 20–60 s intervals | Radio lane (§5.5); no static baked into files, because the engine adds its own noise |

**Distance rules.** Emitters are audible only inside the earshot ring (§2.2). Loudness inside the ring follows §2.3: at normal accommodation BI's gunfire classes fall to their faint floor by ≈ 670 m and stay there until the cut-off. The default distant-battle band is therefore ≈ 0.4–1.0 km from the route and outside reach [I]. Probe AP7 measures real loudness at 0.5, 1.0 and 1.3 km before these defaults ship. BI's median placement of 2.8 km put most of its war noise out of earshot until the player came close. AL12 ("hollow battle") flags emitters the player can walk up to and find nobody there. Prefer intermittent classes for emitters the player may leave and revisit, because a seamless loop does not restart after a cull [V static; AP8]. Among stock classes, `AlarmSfx` and the barrel organ's `FunMusicSfx` are seamless loops; `StreamSfx` and the cricket classes carry delays and resume [V base config]. Use placed Sound objects only for sources that never stop, such as a stream.

### 5.5 Dialogue and radio mixing

- **Channel choice.** Radio follows the Speech slider, plays in 2D under the engine's radio noise, queues per channel, and shows its `title` in the chat. `say` follows the Effects slider and fades with distance. Story-critical lines default to radio or to forced subtitles.
- **Carry radius.** Positional lines get a "full-level radius" slider (whisper 3 m, talk 15 m, shout 60 m, loudspeaker 250 m) that compiles to volume = 2·(R/30)² [I, nominal]. The map draws the full-level ring and a −20 dB ring at 10·R. 2D cues use volume 1, with their loudness baked into the file: a 2D volume above 1 saturates and partly bypasses the player's slider (AU19).
- **Radio.** `CfgRadio` classes are generated with volume 1, since the value is ignored (Cwr and Ce; Cwa199 pending AP5, and if 1.99 did honour it, 1 would be 40 dB above BI's usual `db-40`). A radio line may not fall inside an `enableRadio false` span, play while `setAccTime` > 1, use group or vehicle radio in an intro, or play outside MP when no living player exists (AU20). HQ senders come from a picker of the four stock identities: Base, HQ, PAPA_BEAR and AirBase. Radio-styled `say` and `playSound` lines (doc 39 CA10) get no engine noise, so they are framed by a squelch that Plotroom synthesises itself, never one taken from the game [I].
- **Density.** Generated plans keep at most two voices at once and stagger extra voices by their measured lengths; on hand-placed lines AU22 offers the same stagger as a fix, never silently. A generated positional line within ≈ 8 s of a scripted explosion is moved or switched to radio (AU12 offers this for hand-placed lines), because ear accommodation has just turned the world down. In a firefight a quiet `say` can lose its voice-budget slot, so the fix offers radio or a closer speaker.
- **Subtitles.** Story-critical lines get `forceTitles=1`. Long lines are split into timed `titles[]` chunks. Reading speed above 17 characters per second gets an info note, and above 20 cps a warning (AU14). Netflix's adult limit is 20 cps, and BI's own lines run at a median 15.8 cps. No Effects title may overlap a subtitled line (AU15). A speaker more than 100 m from the camera uses the array form with distance 0 (on Cwa199, after AP3).

### 5.6 Custom audio import pipeline

`decode → optional mono downmix → resample → trim and click-free fades → optional radio filter → loudness normalisation → Vorbis encode → .lip → class generation`. Each step is a typed, undoable command, and the original file always stays beside the processed variant (doc 34 mo09).

| Use | Channels | Rate | Vorbis quality | Loudness target | Notes |
| --- | --- | --- | --- | --- | --- |
| Positional voice and SFX (`say`, Voice, `CfgSFX`) | Mono (forced) | 44.1 kHz | q3 | −20 LUFS-I; peak-based for clips under 3 s | Stereo is presumably not spatialised (AU01; AP6) |
| 2D voice-over, stingers | Mono or stereo | 44.1 kHz | q3 | −20 LUFS-I | |
| Radio | Mono | 22.05 kHz | q2 | −20 LUFS-I | Local radio filter: high-pass ≈ 300–500 Hz, low-pass ≈ 2.5–3.4 kHz, light saturation, limiter; "clean", "field" and "distant" variants; edge fades ≤ 50 ms so the engine's squelch lands on silence [I; V-search practitioner advice] |
| Music | Stereo | 44.1 kHz | q4 (q3 for MP) | −23 LUFS-I | True peak ≤ −1 dBTP for everything (ASWG-R001) |

- **Formats.** Only `.ogg` (Vorbis), `.wav` (RIFF PCM) and WSS load. MP3, Opus and FLAC are read as WSS and fail, so import transcodes everything to Vorbis (AU08). Files never have more than two channels. Vorbis I was frozen in 2000, but whether files from a modern encoder play on 1.99 is still probed (AP14).
- **Loudness.** House targets are calibrated when the catalog is indexed, by measuring stock voice and music locally (aggregates only, never stored in the repo). The values above are starting points [I]. The ASWG recommendation for home platforms is −24 LKFS ± 2 with true peak ≤ −1 dBTP [V].
- **Size budget.** For MP, the target is ≤ 1 MB of audio per mission, with a warning above 2 MB (BI's MP missions have a median total size of 141 KB). SP and campaign totals are shown against the official medians (AU10).
- **`.lip` generation.** A Rust port of CWR's reference WAV-to-lip algorithm runs on every imported or synthesised `say` line and on each language variant. The algorithm uses 40 ms frames and a deviation energy, normalises it, buckets it into phases 0–7, and writes only changes. The port brings `BohemiaInteractive/CWR@ffc61838b7:tests/unit/engine/Poseidon/Asset/Probes/test_wave_to_lip.cpp` (8 cases) in the same change set, with synthetic fixtures, and moves its row in `docs/porting/upstream-test-map.csv` (row 50, counting the header as row 1; rows are keyed by upstream path, so the number can shift) from `reference` to `ported`. Radio lines get no `.lip`, because radio has no lip path [V `CWR:World/Entities/Infantry/Head.cpp#L29-L113`; `CWR:Asset/Probes/WaveToLip.cpp#L31-L126`].
- **Rust building blocks** [V crates.io, 2026-09-27]: decoders per doc 07 §12 (`lewton` or `symphonia`); `vorbis_rs` 0.5.6 (BSD-3-Clause); `ebur128` 0.1.10 (MIT); `rubato` 5.0.0 (MIT OR Apache-2.0); `biquad` 0.6.0 (MIT OR Apache-2.0). All are GPL-compatible; versions are pinned in `Cargo.lock`.
- **Mixer math.** The distance, carry and level read-outs port CWR's audio-math formulas. The change set that adds them moves `test_audio_math.cpp` (4 cases) and `test_dx8_reference.cpp` (37 cases) from `not-applicable` to `adapted` (rows 269 and 272).

### 5.7 Audio classes authored through forms

The audio library panel edits five class types: `CfgSounds` (name, file, volume in dB, pitch, subtitles, `forceTitles`), `CfgMusic`, `CfgRadio` (name, file, title), `CfgSFX` (entries with probability and min/mid/max delay sliders plus a silence share, with an audition that simulates the Gauss spacing) and `CfgEnvSounds` (day and night files). The compiler writes them into fenced, compiler-owned regions of `description.ext` (doc 32 §3.5). Hand-written classes outside the fences are preserved and shown read-only, and hovering a path shows how it resolves.

Paths follow the engine's rules [V `CWR:IO/ParamFileExt.cpp#L124-L181`]. A name without a leading `\` gets `sound\` prepended, and gets `.wss` appended if it has no dot. A leading `\` makes the path relative to the mission root (the usual form for music). Paths longer than 255 characters are truncated. Lookup runs mission, then campaign `dtaExt\`, then the base config. Plotroom never writes a redundant `sound\` prefix, because only CWR and CE fix the resulting double prefix (AP15). Only classes with a `name` appear in the stock editor's Effects lists.

### 5.8 Per-language voice

A line × language matrix (doc 34 mo07). Each cell holds a sibling file `<base>.<voiceLang>.<ext>` with its own loudness pass and `.lip`. Missing cells fall back to the base file and to text. This needs Cwr or Ce; Cwa199 always plays the base file.

### 5.9 Licensing guard and synthetic voices

- **Game audio is never copied.** Stock sounds and music are referenced by class name. An exported file that is byte-identical to a stock or mod file triggers D9 (AU16). Import also hashes the source file against the same local index, so a stock or mod file brought in by hand is marked "derived from game or mod audio"; the mark follows every processed variant, because a trimmed or re-encoded copy is no longer byte-identical, and AU16 fires on the variant too. Like D9, this warns and never blocks private use (doc 34 §4.4) [I].
- **Per-asset metadata.** Each asset records its source URL, author, licence (SPDX) and modification notes. The import writes the steps it ran (trim, fades, filter, loudness) into those notes by itself, because CC BY 4.0 asks whoever shares the material to credit the author, say whether it was modified and link the licence. Export compiles them into the credits block of doc 34 §4.4 (`overview.html`, an optional outro roll, the readme). Under the CC 4.0 licences a pure format change (transcode, resample) never makes an adaptation, while syncing music in timed relation with moving pictures always does; ND licences allow producing an adaptation but not sharing it. ND files therefore default to format-only processing, and an ND track on a cutscene cue works in private builds while AU04 warns at once and again at export, unless the user records a separate permission. NC music gets a warning too (AU04) [V CC BY 4.0 and CC BY-ND 4.0 legal codes; I application].
- **Synthetic voices** (doc 22 Radio Voice plugin). An allowlist shows each voice's licence: Piper voice licences differ per voice (LJSpeech is public domain, LibriTTS voices are CC BY 4.0), and research-only and NC voices are excluded by default [V/V-search]. Output gets an "AI voice" tag in the project, and synthesised audio enters the same local pipeline as a human take, as a variant beside the text and any human recording (doc 34 mo09). The voice's own licence credit is always written when that licence requires one; the "AI voice" disclosure line is offered at export, on by default and removable (doc 09 §7.3). There is no cloning feature, whether for real people or the original cast, and no voice is described as sounding like a named performer (doc 09 WN2, doc 15); the 2025 SAG-AFTRA video game agreement requires written consent for digital replicas [V, from a law firm's summary].

## 6. Lints

Severity follows AGENTS.md: realism and taste are info or warn, and only what the engine or profile cannot run is an error. Every lint offers one-click fixes computed by code, applied through the same undoable commands as manual edits. Every info or warn finding can be dismissed per mission as "intentional" (as in docs 32 and 39); taste notes such as AL13, AL14 and AU17 follow the mission's visible realism setting (doc 39 §5.1); and info findings wait in a quiet list instead of interrupting [I].

### 6.1 Audio (AU)

| Code | Severity | Rule | Fix offered |
| --- | --- | --- | --- |
| AU01 | warn / info | Stereo file bound to a positional use (warn: it will probably not be positioned) or used in 2D (info) | Downmixed variant |
| AU02 | warn | Integrated loudness more than 3 LU from the house target | Normalised variant |
| AU03 | warn | True peak above −1 dBTP, or clipped samples | Limited variant |
| AU04 | warn | Missing licence or author; an NC licence; ND music synced to a cutscene or edited beyond a format change (fires on assignment and again at export; never blocks private use) | Replace, pick another cue, or record a separate permission |
| AU05 | warn | A track switch or Effects Music while a cue plays, with no fade before it (hard cut) | Insert a dip |
| AU06 | info | `fadeMusic` above 0.5 (louder than the default); above 1 it has no further effect on stock tracks | Clamp to 0 dB |
| AU07 | warn | `soundEnv` override with no restore, two triggers setting different beds, or a mission or campaign `CfgEnvSounds` class named `Default` (it breaks the restore) | Add a paired `Default`; rename the class |
| AU08 | error | Unsupported format or extension (MP3, Opus, FLAC, non-PCM WAV, more than 2 channels): the engine cannot play it | Transcode |
| AU09 | warn | Missing file, or a case mismatch on the target host (extends MC28) | Relink |
| AU10 | warn | Audio over the size budget (MP: 1 MB target, warning at 2 MB) | Re-encode at a lower quality |
| AU11 | info | `CfgRadio` volume other than 1 (it has no effect) | Set it to 1 |
| AU12 | warn | Positional line within ≈ 8 s after a scripted explosion | Delay it, or switch to radio |
| AU13 | warn | `fadeSound` on a CWE mount | Use CWE's function |
| AU14 | info / warn | Reading speed above 17 cps (info) or above 20 cps (warn) | Split or shorten |
| AU15 | warn | Title-layer effect overlapping a subtitled line | Move the title to the cut layer |
| AU16 | warn | File byte-identical to a stock or mod file (D9) | Reference it by class |
| AU17 | info | The same track used in two missions of one campaign | Suggest another track with the same tags |
| AU18 | info | `CfgSFX` emitter outside every earshot ring on the route | Move it into the band |
| AU19 | warn | 2D cue with a volume above 1 | Bake the gain into the file |
| AU20 | warn | A radio line nobody can hear: inside an `enableRadio false` span, while `setAccTime` > 1, on group or vehicle radio in an intro, or with no living player outside MP | Switch to `say` or `playSound`, or move the line |
| AU21 | info | More music cues than the plan allows, or the silence budget missed (music overuse) | Drop the weakest cue |
| AU22 | warn | More than two dialogue sources at once | Auto-stagger |
| AU23 | info | `say` line on a visible person with no `.lip` | Generate one |
| AU24 | warn | Objective or warning information carried only by a Score cue | Add a radio or caption line |

### 6.2 Atmosphere (AL)

| Code | Severity | Rule |
| --- | --- | --- |
| AL01 | info | Intel left at every engine default (07:30, 10 May, overcast 0.5, fog 0): "choose the light" |
| AL02 | warn | `setRain` while overcast is below ≈ 0.673, or rain above 0.5 expected to last |
| AL03 | warn | Two weather ramps overlap, so the second cancels the first |
| AL04 | warn | Weather changing too fast: overcast change ≥ 0.3 or fog change ≥ 0.2 in under 60 s, outside a cut or time skip [I thresholds] |
| AL05 | info | Scripted weather that the Intel forecast would do on its own |
| AL06 | info | Start fog above 0.6 (sight ≤ ≈ 390 m; BI never went above ≈ 0.57) |
| AL07 | warn | Sight range shorter than a required engagement distance (objective, sniper position, ambush) |
| AL08 | info | Night objective with no light source nearby; an unlit fire at night (which may be intended) |
| AL09 | info | AUTO lamps dark in twilight on a winter date: the lights could show earlier, but the lamps switch on only at 16:48 |
| AL10 | info | Night stealth objective where more than half the enemy have night vision |
| AL11 | info | Warm-light preset with overcast ≥ 0.66, which leaves no direct sun |
| AL12 | warn | Hollow battle: a distant-battle emitter within reach of the route, with no units near it, while its flag can be true |
| AL13 | info | A day animal at night, or a night animal by day |
| AL14 | info | A settlement on the route with no life and no explanation |
| AL15 | info | Atmosphere budget exceeded, or more than ≈ 8 emitters overlapping one spot |
| AL16 | warn | MP: weather, music, particle or sound actions run only on the server |
| AL17 | warn | Stock `setRain`, `setFog` or `setOvercast` on a CWE mount |

## 7. The AI angle

The agent works only through the product's typed tools (AGENTS.md). The atmosphere workflow is a code-owned state machine (docs 25 and 38):

1. **Pick** a mood family (≤ 7), then a preset within it (≤ 7), then an intensity (3). Code computes the menus for the island, date and profile, and shows locked options with their reasons.
2. **Pick** a cue plan (QP1–QP6) and, for each phase, a music mood from Plotroom's own tags (tense, somber, triumphant, ambient, …).
3. **Fill** only text: subtitles, radio lines and captions within the reading-speed limit, plus one story tag and detail token per vignette kit.
4. **Code computes** the solved hour, Intel values, holds, lamp and fire states, flare beats, emitter positions and gates, cue times, fade ramps, duck levels, file placement and class definitions, then runs every lint.
5. **Repair is bounded.** An over-long subtitle goes back to the model once with the measured limit; after that, code splits it. A kit that cannot be placed is dropped with a note.
6. **Critique** (optional). The model compares two consequence cards and picks one. Comparing harness screenshots needs a vision-capable model, and the screenshots render game data (doc 02 §3.4), so they go only to a local model unless the user explicitly opts in to sending them to a cloud provider [I].

Apart from the lines of text it writes, the model never supplies a number, a time, a class name, a file path or a command. Existing mission text and imported file names are data, never instructions. Stronger models may compose a custom preset, which passes through the same compiler and lints. Suggested tools: `atmo.suggest`, `atmo.apply`, `atmo.explain` (why a value is what it is), `audio.plan_cues`, `audio.lint`.

## 8. Fun, UX and accessibility

### 8.1 Fun and UX

- **Mood board.** A gallery of presets, shown as screenshots taken locally from the user's install through the Cwr/Ce harness, or as labelled illustrations on Cwa199. The gallery Plotroom ships, and any preset shared through a pack or registry, uses Plotroom's own illustrations; local screenshots stay in the user's cache (doc 02 §3.4).
- **Variations.** "Make it moodier / lighter / stormier / quieter" and "surprise me" produce seeded variants within the preset's bounds, each with its own consequence card, so the user stays the director.
- **A/B.** Two presets side by side (screenshots and consequence cards); the raw and processed versions of any imported line; a line with and without ducking or the radio filter.
- **Direct manipulation.** Drag the start-time marker along the sun bar, drag the forecast handle on the weather arc, paint soundscape emitters, click lamps to cycle ON/OFF/AUTO, and nudge the start time to catch the church bells.
- **"Listen from here".** A map tool that lists what the player would hear at a given point and time: the bed, emitters in earshot and their rhythm, bells, and the music state.

### 8.2 Accessibility

- **Text paths.** Every sound has a text path (doc 34 mo06, MC28), and story-critical lines force subtitles. A speaker-name prefix is optional house style [I]. The Game Accessibility Guidelines rank "subtitles for all important speech" as basic [V].
- **Volume sliders.** The player's three sliders (Effects, Speech, Music; §2.2) are explained wherever lines are authored.
- **Not audio-only.** No information lives only in audio or only in the score (AU24). Dog tells and distant shots can also appear as optional hints for players who cannot hear them [I].
- **Visual safety.** Overlays use pattern as well as colour. The thunder and flare presets carry a photosensitivity note, and the Director can avoid lightning entirely by keeping overcast below 0.93 [I].

## 9. Phased plan, probes and acceptance tests

### 9.1 Phases

| Phase | Content | Proof |
| --- | --- | --- |
| AD0 | Sun model port with its own known-value tests; sight formula; weather rules; audio math (upstream rows 269 and 272 adapted); catalogs of stock sound and music classes read from the user's install | Unit tests against the §2.3 tables; ported upstream cases |
| AD1 | Atmosphere panel per section: Intel editing, sun bar, sight read-out, consequence card, AL lints | Synthetic mission fixtures, one per lint |
| AD2 | Presets AM01–AM12, weather timeline and director, lights (fires, lamps, flares), dressing kits, vista finder, compilation per profile | AMT1–AMT6 |
| AD3 | Sound: cue planner and plans, fades and ducking, soundscape painter, class forms, import pipeline, `.lip` port (upstream row 50 ported), language matrix, licence guard, AU lints | AMT7–AMT12 |
| AD4 | AI workflow, harness previews and mood board, A/B, probe runs | AMT13–AMT14 |

### 9.2 Acceptance tests

| ID | Scenario | Expected |
| --- | --- | --- |
| AMT1 | Apply every preset at each intensity to a fixture mission, and compile for Cwa199, Cwr and Ce | Valid output for each profile; no errors; no Cwr/Ce-only command in the Cwa199 output |
| AMT2 | Apply "dawn fog patrol" with QP1 to a mission on Everon dated 15 June | Start time solved to first light (between about 04:10 and 05:05); the fog lifts within 30 minutes; the sight read-out matches §2.3 for the chosen fog; no audio lints. On Cwr, a live screenshot at the start matches the phase within the tolerance agreed in AD4 |
| AMT3 | Edit the solved start time by hand, then regenerate the preset | The edited time is kept and marked customized |
| AMT4 | Weather hold on a 2-hour mission | The compiled pair is present; probe AP2 shows no drift in Preview |
| AMT5 | Add a `setRain` key while the arc sits at overcast 0.5 | AL02 fires; the fix raises overcast first |
| AMT6 | Place the village-that-fought-back kit on a fixture island | Objects sit off the critical path and are linked to a briefing line; map buildings are referenced by typed ids |
| AMT7 | Import a stereo 48 kHz WAV as a `say` line | Mono Vorbis at 44.1 kHz, loudness within 1 LU of the target, a generated `.lip`, the original kept, and a `CfgSounds` class in the fenced region |
| AMT8 | Import an MP3 and a 6-channel WAV | Both are transcoded; AU08 would fire on the untranscoded originals |
| AMT9 | Two music cues back to back with no fade | AU05 fires; the fix inserts a dip that compiles to `fadeMusic`, `playMusic`, `fadeMusic` |
| AMT10 | A radio line placed in an intro on group radio | AU20 fires; the fix moves it to side radio or `playSound` |
| AMT11 | Export a mission that contains a copied stock sound file and a trimmed re-encode of another | AU16 (D9) fires on both and does not block the export; applying its fix rewrites each reference to the stock class, after which the export contains no game file |
| AMT12 | `.lip` port | The 8 upstream cases pass on synthetic fixtures |
| AMT13 | A 3–9B local model runs the atmosphere workflow on 20 briefs | Every run yields a valid preset, a cue plan and lint-clean output; outside its text lines the model emits no number, class name or path |
| AMT14 | The same model and seed, twice | Byte-identical compiled output |

### 9.3 Probes (Preview missions)

| ID | Question |
| --- | --- |
| AP1 | Do sunrise and sunset match the ported model on three dates (screenshots at the solved minutes)? |
| AP2 | Does the instant-then-long-hold pair keep overcast and fog fixed for the whole mission? |
| AP3 | Do `playMusic [class, t]` and `say [class, 0]` work on Cwa199? |
| AP4 | Does `soundEnv` `Default` restore the terrain bed on Cwa199, does the override reset between sections, and does it survive loading a savegame? |
| AP5 | Is `CfgRadio` volume ignored on Cwa199 too? |
| AP6 | Is a stereo `say` line positioned, on Cwa199 and on Cwr? |
| AP7 | How loud are stock gunfire emitters at 0.5, 1.0 and 1.3 km, at view distances 900 and 1200? |
| AP8 | Confirm that a seamless looping `CfgSFX` class (for example `AlarmSfx`) does not restart after the player leaves and returns, as the source reads |
| AP9 | Does a `camCreate`d flare fall and illuminate on Cwa199? |
| AP10 | How long do destroyed vehicles burn and smoke? |
| AP11 | Is the church-bell timing as derived, and do terrain (island) churches ring? |
| AP12 | Does `fadeSound` leave `playSound`, Effects Sound, radio and music untouched? |
| AP13 | What is the 3D voice budget on Cwa199? |
| AP14 | Do files from a modern Vorbis encoder play on Cwa199? |
| AP15 | How does Cwa199 resolve a `sound[]` path that already starts with `sound\`? |
| AP16 | How far does MP weather drift between clients, and what do join-in-progress clients see? |
| AP17 | Do AUTO lamps in winter twilight look as predicted? |
| AP18 | How intense and how frequent is the lightning flash at overcast 0.95 and 1.0 (for the photosensitivity note)? |

## Open questions

1. Where do the tuning values for each preset come from: probe screenshots graded by the owner, or a small player survey? [U]
2. Should "hold weather" be on by default for MP missions, given that clients drift apart? [I] (depends on AP16)
3. Should Plotroom's mood tags for stock tracks ship as data (our own opinions about each class name) or be built per user by listening locally? Either way, measurements such as lengths stay in the user's cache. [I]
4. Should loudness house targets be calibrated against stock voice measured on the user's machine, or fixed at −20/−23 LUFS? [U]
5. Should `soundEnv` "zones" (enter and exit pairs keyed to the player) be offered at all in MP, where each machine's trigger decides? [U]
6. Should the accessibility fallback for sound tells (AU24) be a hint track in the UI, or captions only? [U]
7. Does the 1.99 renderer match CWR's sun, moon and night-factor code (AP1, AP17)? [U]
8. Should the Director script flare beats on Cwa199 before AP9 passes, or only hand out flares as gear? [I]
9. Which Plotroom content pack owns the presets and kits (T0 data per doc 22), and how are community presets reviewed (doc 42's registry)? [U]
10. How does CWE's scripted weather treat Intel values? Should CWE targets author weather only through CWE's data? [U]

## Sources

**Engine source (static reading at the pinned commits).**

- `CWR:Graphics/Rendering/Lighting/Lights.cpp#L22-L276`, `TransLight.cpp#L439-L451`; `CWR:Graphics/Rendering/Effects/Smokes.cpp#L2309-L2570`
- `CWR:World/WorldInit.cpp#L190-L309, #L740-L793, #L883-L968`; `WorldSetup.cpp#L333-L449, #L878-L932, #L1201-L1317`; `WorldImpl.cpp#L831-L1049`; `World/Entities/Vehicles/VehicleTypes.cpp#L41-L59, #L270-L277, #L757-L760`; `World/Terrain/Landscape.cpp#L423-L758`, `Geography.cpp#L557-L666`, `LandSave.cpp#L1885-L1900`; `World/Scene/Scene.cpp#L138-L145, #L485-L503`, `Fireplace.cpp#L19-L286`, `ObjectClasses.cpp#L33-L39, #L236-L293`; `World/Detection/Detector.cpp#L696-L724, #L1259-L1529`, `Target.cpp#L747-L888`; `World/Simulation/Simul.cpp#L1200-L1240`
- `CWR:World/Entities/Vehicles/House.cpp#L949-L1110`, `TransportCore.cpp#L1623-L1649`, `Ground/Car.cpp#L2271-L2280`, `Ground/Motorcycle.cpp#L2298-L2307`; `World/Entities/Weapons/Dammage.cpp#L588-L613`, `Shots.cpp#L1292-L1340`; `World/Entities/Infantry/Head.cpp#L29-L177`
- `CWR:AI/AIArcade.cpp#L735-L808`, `AIRadio.cpp#L1375-L1495`, `AICenterImpl.cpp#L855-L895, #L1305-L1342, #L1403-L1415`, `AIUnitImpl.cpp#L1986-L2004`, `VehicleAI.cpp#L2358-L2381`, `ArcadeTemplate.cpp#L1474-L1539`
- `CWR:Audio/DynSound.cpp#L42-L430`, `SoundScene.cpp#L192-L653`, `Speaker.cpp#L23-L199`, `Core/VoiceBudget.cpp#L78-L203`, `Shared/AudioMath.hpp#L8-L47`, `Shared/DX8Reference.hpp`, `Streaming/WaveStream.cpp#L146-L248`, `Streaming/WaveStreamOGG.cpp#L63-L91`, `VoiceLangPath.hpp#L12-L54`; `CWR:Asset/Probes/WaveToLip.cpp`, `WaveToLip.hpp`
- `CWR:IO/ParamFileExt.cpp#L70-L181`, `IO/ParamFile/ParamFile.cpp#L718-L733`; `CWR:UI/OptionsUI.cpp#L283-L583`, `UI/Settings/ViewDistance.hpp#L1-L72`, `UI/Locale/MissionLanguageDetector.cpp#L300-L317`
- `CWR:Game/Commands/GameStateExt.cpp#L853-L916, #L987-L1071, #L1124-L1415`, `GameStateExtUi.cpp#L627-L690, #L878-L1110, #L1415-L1445, #L1690-L1823`, `GameStateExtGrp.cpp#L1366-L1411`, `GameStateExtWorldConfig.cpp#L1636`; `CWR:Core/Config/EngineConfig.hpp#L74`, `Core/EngineState.hpp#L12`; `CWR:Network/NetworkClientActions.cpp#L125-L137`, `NetworkServerSimulate.cpp#L745`
- `OAL:WaveOAL.cpp#L21-L26, #L803-L887, #L1614-L1639`, `WaveOAL.hpp#L105, #L117`, `SoundSystemOAL.cpp#L153, #L553-L566`
- `BohemiaInteractive/CWR@ffc61838b7:tests/unit/engine/Poseidon/Asset/Probes/test_wave_to_lip.cpp`, `…/Audio/test_audio_math.cpp`, `…/Audio/test_dx8_reference.cpp`
- `CE:Game/Commands/GameStateExt.cpp`, `World/WorldSetup.cpp#L1271`, `World/Terrain/Landscape.cpp#L563-L672`, `World/WorldImpl.cpp#L953`, `World/Simulation/Simul.cpp#L1224`, `AI/AIRadio.cpp#L1447`, `Audio/SoundScene.cpp#L537`, `Audio/Core/VoiceBudget.hpp#L23`, `UI/OptionsUI.cpp#L346-L573`, `IO/ParamFileExt.cpp#L146`

**Owner's install and corpus** (read-only; aggregates, class and command names only; scripts not committed): the decoded base config (1.99 and Remastered), the Resistance addon and Noe configs, and the stringtable (display names); official SP, campaign and MP missions (decoded `mission.sqm`, scripts, `description.ext`); OGG headers and a header-only scan of the music bank (no audio extracted); a names-only string scan of the 1.99 executable; CWE readmes (weather system, commands not to use, executables, launch parameters, BASS licence) and CWE sound folder names.

**Repo.** Docs 03, 04, 07 §12, 08, 09 (WN2), 22, 23, 25, 26, 27, 28, 31, 32, 34, 35, 37, 38, 39, 42; `docs/porting/upstream-test-map.csv` rows 50, 269 and 272.

**Web** (fetched 2026-09-27 unless marked).

- *Storytelling and level design:* Smith and Worch, GDC 2010 <https://gdcvault.com/play/1012647/What-Happened-Here-Environmental>, summary <https://www.worch.com/2010/03/11/gdc-2010/>; Nieman Storyboard, 2011 <https://niemanstoryboard.org/2011/01/14/harvey-smith-on-environmental-storytelling-and-embedding-narrative/>; Carson, 2000 <https://www.gamedeveloper.com/design/environmental-storytelling-creating-immersive-3d-worlds-using-lessons-learned-from-the-theme-park-industry>; Level Design Book <https://book.leveldesignbook.com/studies/irl/disneyland>; Lynch <https://en.wikipedia.org/wiki/The_Image_of_the_City>; Kotaku, 2017 <https://kotaku.com/breath-of-the-wilds-biggest-design-secret-lots-of-tria-1819113140>; Ico <https://en.wikipedia.org/wiki/Ico>; Silent Hill <https://en.wikipedia.org/wiki/Silent_Hill_(video_game)>; interest curve <https://game-studies.fandom.com/wiki/Interest_Curve> [V-search].
- *Light:* PhotoPills <https://www.photopills.com/articles/golden-hour-photography-guide>; PetaPixel <https://petapixel.com/2014/06/11/understanding-golden-hour-blue-hour-twilights/>; <https://en.wikipedia.org/wiki/Blue_hour>.
- *OFP memories and mods:* NME, 2022 <https://www.nme.com/features/returning-to-operation-flashpoints-island-of-everon-in-arma-reforger-3238129>; GameSpot, 2001 <https://www.gamespot.com/reviews/operation-flashpoint-cold-war-crisis-review/1900-2810242/> [V-search]; ECP 1.085 <https://www.ghostrecon.net/forums/index.php?/topic/27029-ecp-v1085-released/>; FlashFX <https://www.gamefront.com/games/operation-flashpoint/file/flashfx> [V-search].
- *Later Armas:* <https://community.bistudio.com/wiki/Eden_Editor:_Scenario_Attributes>; <https://community.bistudio.com/wikidata/external-data/arma-reforger/ArmaReforgerScriptAPIPublic/interfaceTimeAndWeatherManagerEntity.html>.
- *Game audio and film sound:* Jørgensen 2007, Northern Lights 5(1): 105–117, DOI 10.1386/NL.5.1.105_1; adaptive music <https://en.wikipedia.org/wiki/Adaptive_music>, Phillips 2021 <https://www.gamedeveloper.com/audio/horizontal-resequencing-and-dynamic-transitions-for-game-music-composers>; Murch 2005 <https://transom.org/2005/walter-murch/>; Saving Private Ryan <https://www.asoundeffect.com/saving-private-ryan-sound-design/>, <https://nofilmschool.com/saving-private-ryan-sound-design>; ambiences <https://www.gameaudiolearning.com/knowledgebase/how-to-make-ambiences-for-games>; ASWG-R001 v1.10 <http://gameaudiopodcast.com/ASWG-R001.pdf>; Wwise ducking example <https://gameaudioresource.com/2019/08/24/chapter-15-a-adviser-map-intro/>; radio voice processing <https://vi-control.net/community/threads/telephone-speaker-radio-voice-fx-suggestions-plugins.65816/> [V-search]; Vorbis <https://en.wikipedia.org/wiki/Vorbis>.
- *Subtitles and accessibility:* Netflix <https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide>; Game Accessibility Guidelines <https://gameaccessibilityguidelines.com/provide-subtitles-for-all-important-speech/>.
- *Licensing and voices:* CC BY 4.0 <https://creativecommons.org/licenses/by/4.0/legalcode.en>; CC BY-ND 4.0 <https://creativecommons.org/licenses/by-nd/4.0/legalcode.en>; Piper <https://github.com/rhasspy/piper/discussions/271>, <https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_US/ljspeech/high/MODEL_CARD>, <https://github.com/OHF-Voice/piper1-gpl> [V-search]; SAG-AFTRA 2025 summary <https://www.dglaw.com/sag-aftras-new-video-game-agreement/>.
- *Crates (API):* <https://crates.io/api/v1/crates/vorbis_rs>; <https://crates.io/api/v1/crates/ebur128>; <https://crates.io/api/v1/crates/rubato>; <https://crates.io/api/v1/crates/biquad>.

## Verification notes

### Product and legal review notes

A product, fun and legal review on 2026-09-27 checked the doc against AGENTS.md and docs 02, 09, 15, 22, 31, 32, 34 and 39, and re-fetched the CC BY 4.0 and CC BY-ND 4.0 legal codes. Engine claims were not re-checked in this pass, and nothing was run. Edits made in place:

- **ND music (§5.9, AU04).** The draft refused ND tracks on cutscene cues. The CC 4.0 ND licences allow producing an adaptation and forbid only sharing it, a format change never counts as an adaptation, and doc 34's D9 never blocks private use. ND files now default to format-only processing. AU04 warns when the track is assigned and again at export, and it accepts a recorded separate permission [V legal codes §1(a), §2(a)(1)(B), §2(a)(4)].
- **Attribution (§5.9).** The import writes its own processing steps into the modification notes, because CC BY 4.0 §3(a)(1) asks whoever shares the work to say whether it was modified and to link the licence. The credits block is the one doc 34 §4.4 already specifies.
- **Game-audio guard (§5.9, AMT11).** A byte-identical check misses a trimmed or re-encoded stock file. Import now hashes the source and carries a "derived from game or mod audio" mark to every variant. AMT11 had said nothing from the game is written, which contradicted "warn, never blocks"; it now expects a warning and a fix.
- **Game data stays local (§5.2, §7, §8.1).** Stock tracks are auditioned by decoding them from the user's install at play time, and they never enter missions, exports or shared presets. The shipped gallery and shared presets use Plotroom's own illustrations. The critique step compares consequence cards by default. Harness screenshots, which render APL-SA data, go to a cloud model only on explicit opt-in, and this default also suits weak local models, which rarely have vision.
- **Voices (§5.9, §5.5).** A voice's licence credit is mandatory when its licence requires one. The "AI voice" disclosure line is offered, on by default and removable (doc 09 §7.3, doc 34 mo09). No voice is described as sounding like a named performer (doc 15). The SAG-AFTRA sentence now states what the agreement requires instead of calling it an industry norm. Radio-styled `say` and `playSound` lines (doc 39 CA10) use a squelch that Plotroom synthesises.
- **Paraphrase (AH1).** The NME line was a direct quote, although the header promises paraphrase.
- **Defaults, never walls (§5.2, §5.5, §6).** The planner never schedules music under a firefight, and a hand-placed cue gets MC19 (warn, dismissible). Staggering and explosion moves apply to generated plans; on hand-placed lines AU22 and AU12 offer them as fixes. Every info or warn finding is dismissible as "intentional", and taste notes follow the visible realism setting (doc 39 §5.1).
- **Tedium and glass box (§3.3, §3.7).** The consequence card leads with three chips (Easy mode shows only those). Smoke columns are doc 31 module 16 effects, edited as map markers rather than as generated script.
- **Maximum within the engine (§3.1).** The engine gaps found here are named as candidates for the engine-requests register. `docs/upstream/` does not exist yet.

Checked and kept: the scope (atmosphere and audio for missions and campaigns only; TTS only through a doc 22 plugin with its egress card; the agent picks from menus and writes only text); restraint as the default (AH9, AH11, the silence budget, QP6, the restraint meter as info); and consistency with doc 31 modules 7, 15, 16 and 19, doc 32's timeline and fenced regions, and doc 39's audio plans.

Left for the design round:

1. There are 41 lint codes. Even with dismissal, group them into a few user-facing families in the UI.
2. Free CWA missions are non-commercial in practice, so an NC warning (here and in doc 34 mo13) may nag. Consider info on assignment and a warning only for commercial channels.
3. Whether in-mission (non-cutscene) music counts as "synched with a moving image" is [U]. Only cutscene cues are treated as certain.
4. The voice allowlist policy (doc 22 open question 6) should decide whether a single-speaker dataset voice needs a consent statement from its provider.
5. A "record a take" button in the line matrix would be the friendly, human alternative to synthetic voices. It needs a microphone-permission design.
6. No acceptance test yet proves the credits block (author, licence link, modification notes, AI line). The default preset intensity is also unspecified; Standard is suggested, with every intensity inside the §4.5 budget.

### Engine review notes (2026-09-27)

An adversarial engine review on 2026-09-27 re-read the pinned CWR source (CE where a line says so), the decoded base config and the corpus scripts for the command, config, format and profile claims in §1.2, §2, §3.2–§3.4, §4.1, §5.3–§5.6 and §6. Nothing was run in a game, so every [V] here is a static reading.

**Confirmed as written.**

- *`soundEnv` is global, not a zone.* The bed switch compares one global slot with a sentinel (`CWR:World/WorldImpl.cpp#L953-L963`). Only Effects write that slot (`Detector.cpp#L1463-L1466`, `CWR:AI/AIArcade.cpp#L765-L768`). The base `Default` class resolves to the sentinel through the default-name rules (`CWR:IO/ParamFileExt.cpp#L124-L181`; base config `CfgEnvSounds`). The doc 34 ed12 correction stands.
- *Emitter cut-off.* `CWR:World/Simulation/Simul.cpp#L1224-L1227` and `CWR:Audio/DynSound.cpp#L319-L326`, with objects at ⅔ of the view distance (`CWR:UI/Settings/ViewDistance.hpp`), give 1.1 km at view distance 900 and 1.3 km at 1200. In the corpus, campaign distant-battle emitters sit at p10/p50/p90 = 1.5/2.8/5.2 km from the player's start, so at least 90 % start outside the cut-off even at 1200.
- *Music and hush.* One `_musicTrack`, reset to 0.5, a linear ramp, and a new track replaces the old. `fadeSound` reaches only waves opened with accommodation on; `playSound`, Effects Sound, radio and music are opened with it off (`CWR:Audio/SoundScene.cpp#L507-L526, #L579-L591`; `DynSound.cpp#L112-L121`; `CWR:AI/AIRadio.cpp#L1447`). Radio plays at volume 1 whatever the class says, and CE has the same line.
- *Weather.* Rain needs 1.5·overcast − 1 > 0.01 (overcast > 0.6733). Thunder needs max rain ≥ 0.4 (overcast ≥ 0.9333), with mean bolt gaps of 58.6 s at 0.95 and 14.9 s at 1.0. Direct sun is 0.28 at 0.66 and 0.20 at 1.0. The fog table re-derives (fog 0.5 → 472.5 m). Night, or overcast ≥ 0.9126, caps sight at 900 m, from the sun colour's red channel of 0.85. The Intel ramp takes 30 minutes. Neither clone registers a weather, date or wind getter. The CWR-name scan of 1.99 cannot see a command that CWR lacks, so the 1.99 executable was also searched for these names as standalone strings: `overcast`, `fog` and `wind` do not occur, and the single `rain` and `date` hits are consistent with the config class `Rain` and a savegame key `date` that CWR also uses (`CWR:AI/AICenterStats.cpp#L230`).
- *Weather hold.* With wanted equal to actual, a timed `SetWeather` sets both speeds to 0 and moves the next change t seconds out. The derivation is right; AP2 is still required.
- *Light.* Only sun elevation matters (`Lights.cpp#L80-L276`). The moon colour is black. Point lights are multiplied by the night factor (`CWR:Graphics/Rendering/Lighting/TransLight.cpp#L439-L451`). The base config has a single `latitude=-40`.
- *Array forms.* 43 of the 88 SP and campaign scripts that call `playMusic` use `[class, start]`, and 2 mission files do too. There are 30 array `say` calls, all in Resistance, 6 of them with a third element, which `ObjSay` reads as the subtitle speed.
- *Upstream tests.* The files hold 8, 4 and 37 cases. In the CSV, file lines 50, 269 and 272 carry `reference`, `not-applicable` and `not-applicable`.
- *Placeability and corpus numbers.* The editor lists scope 2 only (`VehicleTypes.cpp#L41-L59`; `CWR:UI/Map/UIArcade.cpp#L263-L267`). Both ruin classes are scope 1, `Crater` has an empty model, and the kit classes are scope 2. Other counts re-run: 43 of 87 playable missions start 04–07; the forecast differs in 76 of 87; there are 184 cues; 769 of 799 radio volumes are `db-40`.

**Corrected in place.**

1. *Environment bed (§2.2, TL;DR, §2.5, SX02, AU07, AP4).* The override resets at every section start and on MP client init (`WorldInit.cpp#L740-L741, #L792-L793`), and deactivation does not undo it. The switch is an instant cut, plays at about −6 dB against a uniform terrain bed, and still has rain layered on top. A mission-level `Default` class breaks the restore. Two further points are [I]: nights are silent without `soundNight`, and the override is not saved in savegames.
2. *Emitter viewer (§2.2, TL;DR).* Distance is measured from the player's unit or vehicle, the camera-effect position, or every MP player (`WorldSetup.cpp#L378-L431`), not from a free camera. "A seamless loop does not restart after a cull" moves from [I] to [V static]. `AlarmSfx` and `FunMusicSfx` are the stock seamless loops. SX07 now uses a gated trigger, and bird emitters that go quiet on the alarm need repeating triggers. A placed `Alarm` object cannot be flag-gated, and a script-created Sound object is silent on Cwr/Ce (`VehicleTypes.cpp#L757-L760`).
3. *Music ceiling (§2.2, §2.3, AU06).* Stock tracks have class volume 1, and the 2D gain clamps at 1 (`AudioMath.hpp#L25-L36`), so `fadeMusic` above 1 adds nothing.
4. *`fadeSound` on 3D sounds (§2.2, §5.3).* It only shrinks the full-level radius, so nearby loud sounds keep their level. Only `fadeSound 0` silences them.
5. *Radio volume (§1.2, §2.2, §5.5).* "Ignored" is now scoped to Cwr and Ce, with the `db-40` evidence for Cwa199. The earlier "769 of 799 set a volume" was wrong: all 799 carry one.
6. *Random weather (§2.1, §3.4).* The first random re-target fires at 30 min, not after at least 1 h 32 min. Drift is bounded at about 0.33 overcast and 0.13 fog per hour.
7. *Hold limits (§3.4).* Both calls must run in the same frame. Every later ramp ends the hold. The 10 hours are weather time. Rain is not held.
8. *Ruins (§4.1, TL;DR).* On Cwr/Ce a script can `camCreate` a scope-1 class (`VehicleTypes.cpp#L270-L277`; `GameStateExtUi.cpp#L1425-L1431`). On Cwa199 this is (unverified), and so is a scripted crater.
9. *Firefights (TL;DR).* "None plays under a firefight" became "2 of 184 cues start on a detection trigger"; whether those play over combat is [U].
10. *Smaller fixes.* Lamps also go dark at bulb damage ≥ 0.5. AI headlights stay off in danger and switch on at a per-vehicle night factor of 0.2–0.8 (`TransportCore.cpp#L1630-L1636`). AM07's window is solved per date (−10° at ≈ 03:33 on 15 June), and AM04 notes possible light rain. The carry paragraph now covers accommodation up to 4 (floor at ≈ 1.9 km) and the old DirectSound hardware path, which had no floor. The `.lip` row numbering is clarified.

**Still unverified, or out of this doc's reach.**

- On Cwa199: CfgRadio volume (AP5), `soundEnv` restore and reset (AP4), the array forms (AP3), the voice budget (AP13), scripted ruins, and whether 1.99 mixes in software (the −40 dB floor) or through a hardware path.
- The object distance is clamped to 100–3000 m (`ViewDistance.hpp#L24-L25`), so the cut-off stops growing at 3.5 km (view distance 4500 m and above); the earshot ring must use the clamped value. Without a mission `setViewDistance`, earshot follows the player's own setting, and the compiler-owned init line in §3.7 removes that variance.
- In MP a remote entity keeps the importance it was sent (`Simul.cpp#L1200-L1203`). How that affects client-side emitters is [U] (AP16 could cover it).
- The §2.5 corrections are not yet filed: none of DG002–DG018 in `docs/design-gap-requests/` covers them.
