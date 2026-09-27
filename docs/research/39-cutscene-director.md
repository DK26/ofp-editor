# The cutscene director: easy, correct, tactical cutscenes

Research doc 39 for Plotroom (`ofp-editor`), 2026-09-27, for contributors and LLM coding agents reading only this file. Owner direction: "We
should definitely consider how to provide and enable easy cutscene creation and have them generated correctly, tactically, and effectively,
with ease." Question: how does a **Cutscene Director**, built on doc 32's cinematics timeline, turn an intent and a few map picks into a
finished, checked and fully editable cutscene (shots, unit staging, timing, titles, subtitles, music)?

**Status.** Proposal-only: every type, code, threshold and flow in §2–§10 is **[I]** unless marked; every number is a default to tune.
**Legend.** **[V]** verified in pinned source, a fetched page or paper, or a local corpus count re-run on 2026-09-27; **[V-search]** seen
only in a search snippet (fetch refused); **[I]** our inference or proposal; **[U]** unknown, needs a probe (§10) or a source.
**Citations.** `CWR:` = `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/` (line numbers are CWR's); `CE:` =
`ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/`, where the pillarbox, subdivision and forced-50 m-grid passages were re-checked identical.
**Hygiene.** The corpus is the owner's install, read locally by our own uncommitted scripts: aggregate numbers, command and class names and
our own descriptions only (doc 35 rules). No game or community script is quoted; papers, manuals and doctrine are paraphrased with a few
short attributed quotes; nothing refers to private or unpublished work.
**Companions.** Doc 32 (the timeline) and 31 §6; 25 (step shapes, menus, repair, pins); 38 (workflows); 26, 28 (content, fun); 33
(Standing Orders); 35 (corpus lessons); 07 §6–§7 (WRP, P3D); 08 (harness); 18/19 (hosts, campaign variables); 23 (catalog).
**Codes (provisional; unused elsewhere in `docs/`).** Archetypes CA01–CA12, checks DR01–DR22, tactical notes TP01–TP10, probes CP1–CP13,
phases DP0–DP4, acceptance tests DAT1–DAT13.

## TL;DR

- **What.** The user picks an intent (establish the AO, introduce a character, reveal a threat, insertion, extraction, aftermath, chapter
  transition, radio montage, …) and a few map subjects; code returns a complete doc 32 `CineSequence` of editable keys. No new runtime or format.
- **Architecture [V sources; I design].** Idiom state machines (Virtual Cinematographer, 1996) expand an archetype; a DCCL-style offline
  pipeline generates candidates (a Toric-space grid for two subjects), hard checks filter, a seeded score ranks, a pacing optimiser cuts.
- **The CWA camera shapes composition [V].** Object targets are always centred (a soldier's eye) with no offset, so composition needs
  computed point targets; a retarget pans 2/(1+cosθ) faster at mid-pan (2× at 90°) and collapses near 180°; distance is d = H/(1.5·FOV).
- **One safe frame [V].** In-mission scenes under Remastered's default Modern style are pillarboxed to a centred 4:3 band (unless a script
  sets `showCinemaBorder false`), sections render full width, and `titleObj`/`cutObj` always force the bars; subjects stay inside the 4:3
  band. The letterbox bar height is [U].
- **Terrain truth [V].** The visible ground is the 50 m WRP grid subdivided per the player's terrain setting (6.25 m on the owner's
  install); open cells deviate up to 5.4–7.6 m (p99). Keys are exact (AGL is resolved in-engine); segments use cache, emulation or margins.
- **Correct by construction.** Candidates pass whole-path clearance, object boxes (the engine clamp ignores objects), ≥ 80% nine-ray
  visibility, the object draw distance (2/3 of view distance), doc 32's layer rules and a skip-safe epilogue; the same checks lint hand work.
- **Engine-true tactical staging [V mechanisms].** Doctrinal wedge, road column, convoy, overwatch, helicopter drills, halts, orders groups; it
  knows SAFE/CARELESS units ignore slots and follow in ID order, one-group convoys close to ~15–25 m (computed), FORM units snap at start.
- **Robust to AI variance.** Teleports under cuts, `stop` freezes, short silent `doMove`s with budgets, event gates with timeouts and snap
  fallbacks; tight framing only for staged actors.
- **BI's defaults [V].** Official intros: median 72 s, 10 shots of 5 s; 85% fade in within 1 s, 91% end on a fade, 74% have music; 72% of
  lines start within 1 s of a cut. Eye height median 1.6 m; FOV 0.7 in 43% of settings; slow motion in 27% of camera scripts.
- **Glass box, pins win.** Each shot keeps its declared `ShotSpec`, residuals, check results, provenance and an evidence-badged thumbnail;
  editing a key pins the shot, and re-planning works around pins.
- **Weak models pick and write.** Intent, subjects, take, tempo/mood/emotion enums and text; never a coordinate, time, class or FOV.
  Qualified models may Compose custom idioms, which pass the same planner.
- **Sibling fixes (§1.2).** Doc 32's "eye below 2 m" warning would flag over half of BI's shots; doc 32 gains a pan template and gates; doc 31's
  convoy "spacing" has no engine knob; doc 28's intro cap becomes a warning; doc 35's shot counts need one population.

## 1. Relation to doc 32

### 1.1 What stays and what is new

Doc 32 owns the engine toolbox, the typed model, the compiler and safety wrapper, hosts, lints, import, preview, templates and AI tools.
The Director is a **producer** that writes into that model; the timeline stays the product and the only thing that compiles [I].

| Layer | Doc 32 has | This doc adds |
| --- | --- | --- |
| Intent | Templates and suggestions (§5.1–§5.2) | 12 archetypes: idiom, staging recipe, audio and title plan, length budget (§3) |
| Shots | `Shot`, `CamKey`, `Entry`, `Follow`, `LookAt` | `ShotSpec` beside the keys; a planner: scale and lens solver, composition, candidates, clearance, visibility, cut grammar, pacing, ranking (§4) |
| Actors | Actors track | A staging planner: doctrinal recipes, engine-true predictions, a robustness contract (§5) |
| Timing | Absolute `&t` cues | Event gates with timeouts joining absolute segments (§4.5) |
| Checks | Lints (§3.7) | DR checks (filters and lints), TP notes, harness detectors, a readiness report (§6) |
| AI | `cine.suggest`, `cine.fill`, `cine.critique` | The `core/make-cutscene` workflow; Compose for qualified models (§8) |

### 1.2 Changes asked of siblings (filed through `docs/design-gap-requests/`; this doc edits no other file)

| Sibling | Proposed change | Evidence |
| --- | --- | --- |
| Doc 32 §3.3, §3.7 | Replace the "eye below 2 m clearance" warning with DR01 (whole-path clearance on the best-known surface) | Official eye height median 1.60 m (n = 2,152) [V] |
| Doc 32 §3.2 | The "eye ≥ 0.5 m" invariant becomes a worm's-eye warning; reject only below 0.3 m | 33 of 614 intro and 83 of 941 cutscene-mission keys with explicit height are below 0.5 m [V]; the clamp is 0.1 m [V] |
| Doc 32 §5.1 | Add "Pan A→B" (≤ 45° segments), "Go-by" and "Orient on map" (probe-gated, shipped precedent) | Pans are the commonest moving commit [V] (§9) |
| Doc 32 §3.4–§3.5 | Add `Gate` (event-gated cue with a timeout) and gate-relative cues | 18% of official camera scripts wait on world events [V] |
| Doc 32 §3.5 | Restore radio only when returning to play; restore view distance only to a value the compiler knows | No view-distance getter exists (§4.3) |
| Doc 32 §3.6, §7 AT6 | The global death hook ships [V]: add a bounded "like the default" DeathCam preset; "`say` with radio styling" is defined in CA10 | §9.2 |
| Doc 32 §3.3, §4.2 | Terrain strip on the subdivided surface with a source badge; thumbnails after `triSimFrames`, in-mission look via `triSetAspectGameplayActive` | §4.3, §6.3 |
| Doc 28 FP43 | The intro cap "≤ 60–90 s" becomes a warning with per-archetype budgets | Intros median 72 s; 11 of 34 exceed 90 s [V] |
| Doc 31 §4.6 row 9, §2 row 37 | No engine spacing knob; SAFE makes vehicles follow in ID order whatever the formation; open column needs one group per vehicle or march unit | §5.2 |
| Doc 35 rc35, §3.2 | State population and shot definition; rc35 becomes 18–32 shots, 1.5–3.5 min | §9.3 |
| Docs 23, 07 | `moveTo`, `enableAI`, `animationState`, `forceSpeed`, `limitSpeed` are unregistered; `ofp-p3d` reads `pilot`/`zamerny`; a read-only subdivision-cache reader | §4, §5.3 |
| Doc 32 §3.4, §3.2 | `Shot` and actor cues carry their own `origin` and `pin`, not only `CineSequence`; the Actors rule "snaps only under a cut or fade" adds "or proven off-frame" (DR15) | Pins are per shot (§7); doc 25 §9.1 pins per element and field |

Engine limits met here (no look-at offset, no view-distance getter, no end-of-speech signal, no spacing command) also belong in the
engine-requests register under `docs/upstream/` (AGENTS.md); the Director works around each today and needs none of them.

## 2. Principles

1. **Intent in, editable timeline out:** doc 32 keys, cues and actor clips, never a blob; the user can stop at any stage and keep what exists.
2. **Code owns geometry and timing:** positions, heights, lenses, durations, gates, classes and spacing are computed; menus come first.
3. **Correct by construction:** the checks are the generator's filters; hand-made shots meet the same yardstick, with softer severities
   where a human choice may be intentional.
4. **Tactical by default, never a wall:** doctrine and engine behaviour under a visible realism setting; plausibility is dismissible advice.
5. **Story first:** orient the player (where, who, what next), establish before detail, cut on the line, end on a hand-off or a fade, keep it
   short (doc 28: "The ultimate goal for each scene should be emotion").
6. **Glass box:** every element shows its archetype, idiom step, model, seed, dependants, check results and evidence tier.
7. **Weak models pick and write only** (doc 25 §5.1); stronger models may Compose idioms, never bypass the planner.
8. **Profiles first:** everything lowers through doc 32 §3.5 and the doc 23 catalog; Cwr/Ce-only features never reach Cwa199 output.
9. **Deterministic:** the same request, seed and mission give byte-identical output; menus and seeds are recorded.

## 3. The cutscene archetype library

Archetypes are T0 data (doc 22 §2.1): parameter schema, taste bounds, shot idiom, staging recipe, audio plan, verifier list. Scales and
lenses are §4.2's (Wide 0.7, Normal 0.3–0.45, Tele 0.1–0.2, Extreme 0.05–0.08); "→" is a cut, "⇢" a move within a shot. Lengths assume the
Standard tempo; in-mission hosts default to ≤ 15 s. All ranges are [I], anchored to §9. Vista and reveal vantages start from doc 41
§4.3's vista finder (sun side, landmark in frame), light and weather from the section's Atmosphere card (doc 41 §3.1), and audio plans
use doc 41 §5.2's mood tags and cue budget, so the two Directors share one vocabulary.

- **CA01 Establish the AO and reveal the objective** (where, when, who, what; ends with the player facing his first bearing). *Subjects:* AO
  anchor (`island.places`/`island.sites`, doc 25 §6.1), objective, player's group. *Idiom:* vista or high orbit (Wide, 30–150 m AGL, arc ≤
  60°, 6–10 s, place/date card) → objective insert (Tele, 3–5 s) or pan A→B ≤ 60° → friendly MS/MLS at eye level → leader MCU on his first
  line → hand-off from behind the player, or a fade. *Staging:* group halted or in a SAFE road file; garrison AWARE with outward sectors;
  protected-actor bundle (§5.3). *Audio:* fade in ≤ 1 s, music at 0, card gone before the first subtitle, first line at 10–15 s.
  *Length:* 25–40 s, 5–7 shots; warning above 90 s. *Profiles:* all; unlike Arma 3's 500 m-high default orbit [V-search], ours stays low
  like BI's CWA shots (median pitch −9°) and always runs DR05.
- **CA02 Introduce a character** (name, role, one trait). *Subjects:* the character (story-bible identity), optional companion or setting.
  *Idiom:* go-by or walk-in at MLS with lead room ⇢ push-in to MCU (−10 to −20% distance, ≥ 5 s) with a name caption, or wide → medium →
  close; end on his first line or a reaction. *Staging:* exact (NONE) mark; a ≤ 20 m LIMITED `doMove` or a pose; listeners' `doWatch`
  eyelines; `setMimic` on the speaker. *Audio:* caption never overlaps his subtitle. *Length:* 12–25 s, 2–4 shots. *Profiles:* all.
- **CA03 Briefing at HQ (orders group)**, as BI staged orders for training and first-combat missions (doc 35 rc20). *Subjects:* speaker,
  listeners, setting. *Idiom:* establishing wide (5–8 s) → two-shot → speaker MCU or over-the-shoulder on line starts, a listener reaction
  after ~6 s on one speaker, re-establish after ~20 s of close coverage → optional map insert (CA11) → closing wide. *Staging:* semicircle
  2–4 m round the speaker, eyelines, catalog talk and gesture moves, SAFE. *Audio:* every line `say` with subtitles; no cut for a line
  under ~1.5 s; in-mission, a checkpoint after. *Length:* set by the lines; warning above 120 s. *Profiles:* all; Cwr/Ce may use `soundLength`.
- **CA04 Departure or insertion (truck, helicopter, boat)**; also fills a transport leg (doc 28 "dead air"). *Subjects:* vehicles, the
  carried group, the route, the destination. *Idiom:* truck: go-by at a road bend (4–8 s) → side tracking at 15–40 m, 2–6 m up →
  rear-quarter follow → arrival wide; helicopter: lift-off wide → tracking at similar altitude (`Resample`) → landing wide → dismount MS;
  boat: shore wide → low tracking (eye ≥ 0.8 m above the live water at keys, §4.3) → beaching wide. *Staging:* convoy recipe or one
  vehicle, SAFE, LIMITED; helicopters `special FLY`, `flyInHeight` 30 m (BI's mode); dismount drill; the player in cargo. *Audio:* live
  engine sound; chatter as CA10 lines, or a live scene without a camera. *Length:* 20–45 s, 4–6 shots. *Profiles:* all; beaching [U] (CP11).
- **CA05 Approach and contact** (build tension, hand control back at contact). *Subjects:* friendly elements, enemy position, contact event.
  *Idiom:* overwatch element (MS from behind, Tele insert) → bounding element (go-by or tracking) → lead scout MCU → gate on contact
  (detection flag, death, damage) with a timeout → reaction cut 0.2–0.5 s after the gate → hand-off. *Staging:* overwatch/bound recipe,
  AWARE or COMBAT, assigned sectors; the enemy SAFE until the gate. Captive or damage-proof actors cannot trip a detection, death or damage
  gate [I], so code stages the contact (the enemy's `doTarget`/`doFire` on a cue, or a flag at a mark) or the user marks one actor as the
  unprotected casualty; protection lifts at the gate for the hand-off. *Audio:* music drops, none under the firefight (doc 28 FP42);
  radio-framed lines. *Length:* 10–20 s with the elastic span at its timeout (the in-mission budget, DR12).
- **CA06 Reveal the threat.** *Subjects:* an observer, the threat. *Idiom:* over-the-shoulder of the observer → Tele insert → reaction CU;
  or a pan reveal ≤ 60°; or a crane over a ridge until the threat appears (visibility inverted: hidden at the start, ≥ 80% at the end).
  *Staging:* observer prone on a crest from the vantage menu (§4.3); threat NONE-placed or on a short patrol. *Audio:* a sting on the insert,
  one radio line. *Length:* 8–15 s in-mission, 2–4 shots. *Profiles:* all; distant Tele inserts fail DR05 first.
- **CA07 Extraction.** *Subjects:* pickup vehicle, extracted group, LZ. *Idiom:* arrival go-by → landing wide → boarding MS → lift-off
  tracking → cut-layer fade. *Staging:* smoke with the colour exchange (pilot names it, ground confirms); boarding from the front (TP05);
  GETIN waypoints or `moveInCargo` under a cut. *Length:* 20–40 s. *Profiles:* all; as an ending it follows BI's socket idiom (flag →
  short outro → END with `forceEnd`, doc 35 §3.3) and doc 32 §3.5.
- **CA08 Aftermath (win or lose).** *Subjects:* the result, survivors, the player. *Idiom:* short form (doc 35 rc20): 1–2 shots of 3–5 s,
  one optionally at slow motion 0.2–0.3, then fade and flag; long form: slow push-in or static wide on the result (8–12 s) → survivors MS
  → closing CU → fade. *Staging:* wrecks via `setDammage`, prisoners (`setCaptive`, a surrender pose), protected actors. *Audio:* music
  fade-out over 1–10 s (BI's range). *Length:* 5–10 s or 15–30 s. *Profiles:* all; lip sync under slow motion [U] (CP2).
- **CA09 Chapter transition.** *Idiom:* BLACK OUT on the cut layer → card on the title layer over the held black → time change under black
  (`skipTime`; `setDate` Cwr/Ce only) → fade in on CA01's first shot. *Staging:* the next scene pre-placed under black. *Length:* 15–30 s,
  card 4–6 s. *Profiles:* chapter cutscenes and outros have no campaign variables, so cards cannot vary by state there (doc 19 C16);
  `skipTime` moves only the time of day, so `&t` cues do not shift (doc 32 §2.6).
- **CA10 Radio montage.** *Subjects:* on-map speakers, an off-map HQ callsign, listeners, markers. *Idiom:* speakers within 100 m of the
  camera get speaker-visible shots cut on line starts; off-map lines play over a map insert or a listener's reaction. **"`say` with radio
  styling"** (fills doc 32 AT6): on-map lines are `say` from the unit, off-map lines `playSound`, each framed by a project-authored squelch
  and captioned "Callsign: text" through `titles[]`, so no radio channel is needed; sections never use group or vehicle radio, and side or
  global radio only with a living player unit (doc 32 §2.5) [V channels; I styling]. Code frames callsign, THIS IS and OVER/OUT; the model
  writes the body (TP08). *Length:* 20–60 s. *Profiles:* all; `say [name, 0, 1]` lifts the 100 m subtitle limit on Cwr/Ce; on 1.99 the
  array form is (unverified) (doc 32 §2.5).
- **CA11 Flyover and map orientation.** *Idiom:* map insert (notepad, compass, watch and radio hidden; animation steps zooming toward each
  objective marker; markers change colour or type on voice lines; `mapAnimDone` gate) → optional clearance-checked flyover ending behind
  the player, facing his first bearing. *Precedent [V, structure only]:* one official single-mission intro does this; two more official
  scripts use map animations. *Length:* 20–40 s. *Profiles:* the insert waits on CP6 (doc 32 open question 7); the flyover needs no probe.
- **CA12 Memorial.** *Idiom:* static wide of the site (8–12 s) → slow push-in on survivors in line → held CU → fade. *Staging:* survivors
  NONE-placed in a line from the slot table, facing the site, CARELESS. *Audio:* quiet music; a card per fallen name only where campaign
  variables exist (doc 18 §8.2), else an unnamed dedication. *Length:* 30–60 s. *Profiles:* all; how rested weapons look is [U] (CP3).

## 4. The shot planner

### 4.1 Shot vocabulary on the CWA camera

The engine offers straight constant-speed commits, a look-at recomputed every frame, one target FOV per commit (reached linearly over
the commit, so a FOV change inside a moving commit is a zoom) and no roll (doc 32 §2.3) [V].
DCCL's fragments (static, go-by, panning, tracking, point of view; Christianson et al. 1996 [V]) map onto it as follows [I on V mechanics].

| Kind | Realisation | Defaults and limits |
| --- | --- | --- |
| Static | One key, `camCommit 0` | 3–6 s; the dialogue default |
| Go-by | Fixed eye; fixed point target on the subject's path | Lead room for free; AI subjects validated over a ±30% speed band |
| Pan | Fixed eye; object target (centred) or point A → point B | Segments ≤ 45° (DR07) |
| Dolly, push-in, pull-out, crane | One straight commit with a fixed or object target; a crane changes height | 4–8 s; characters 0.3–1.5 m/s; push-ins ≥ 5 s; reveals end on a held frame |
| Track or follow | `Resample` loop of `camSetRelPos` snapshots, or a road dolly at convoy speed with an object target | Behind-quarter; eye outside the vehicle box |
| Orbit, zoom | Sampled positions round a fixed look-at; FOV re-set per segment | Arc ≤ 60°; zooms rare (doc 28 style note) |
| POV, map insert | Effects-dialog preset or relative eye at head height; `forceMap` + `mapAnim*` | Short; map insert gated on CP6 |

**Pan mechanics [V].** While the target changes, the aim point is rebuilt from the old and new directions, iDir = nDir·t + oDir·(1−t), with
distance interpolated separately; orientation is that normalised direction with world up, an nlerp (`CWR:World/Scene/Camera/CameraHold.cpp`
`#L210-L276`). Mid-pan angular speed over start speed is 2/(1+cosθ): 1.17 at 45°, 1.33 at 60°, 2 at 90°, 4 at 120°; at 180° the direction
collapses (our derivation, dφ/dt = sinθ/|v|² [I]). Pans ≤ 60° read as a mild ease-in/out; larger ones are split. Target ranges need not match.
θ is measured from the camera's current position every frame, so a dolly during a retarget changes it. A target committed before the
previous retarget's deadline blends from the previous *committed* target, not from the current aim, so the aim jumps (`#L567-L574`; doc 32
§2.3); chained pan segments therefore retarget exactly at the previous deadline. **Zoom mechanics [V].** FOV moves linearly in value
over the commit (`CameraHold.cpp#L309-L323`), so apparent magnification (∝ 1/FOV) speeds up as FOV shrinks: at the end of a 0.7 → 0.1
zoom it grows 7× faster than at the start. An even zoom is sampled in segments with geometric FOV steps [I].

### 4.2 Scale, lens, composition and the safe frame

**Lens [V].** tan(vertical half-angle) = FOV × topFOV; at 4:3 or wider topFOV = 0.75 and leftFOV = 0.75 × aspect (Hor+), narrower screens
use 1.0 and 1/aspect, and a player's custom FOV overrides both (`Camera.cpp#L20-L32`; `UI/Settings/AspectRatio.cpp#L12-L14, #L144-L221`;
`Presentation.cpp#L49-L73`). Visible height is H = 1.5·d·FOV, so d = H/(1.5·FOV); the 35 mm-equivalent focal length is 16/FOV mm (0.7 ≈ 23
mm, 0.3 ≈ 53, 0.2 ≈ 80, 0.1 ≈ 160) [I arithmetic]. The near plane is 0.067/FOV clamped to 0.07–0.2 m (`World.cpp#L1245-L1248`), so clipping
never limits close framing; actor geometry does, so CU and MCU prefer a longer lens from ≥ 1.5 m (FOV ≤ ~0.22–0.35) [I]. FOV is a newtype
limited to 0.01–2.0 (the manual camera's clamp, `CameraHold.cpp#L348`; `camSetFov` itself clamps nothing, and 0 divides by zero,
`Camera.cpp#L34-L41`).

| Scale (standing soldier) | Visible height H | Camera distance, FOV 0.7 → 0.2 | Frame line [I, after the VC's cutting heights] |
| --- | --- | --- | --- |
| ECU / CU / MCU | 0.3 / 0.5 / 0.8 m | 0.3–1.0 / 0.5–1.7 / 0.8–2.7 m | Neck / under the chest or waist / waist |
| MS / MLS / FS | 1.1 / 1.6 / 2.4 m | 1.0–3.7 / 1.5–5.3 / 2.3–8.0 m | Crotch / under the knees / whole person |
| LS / ELS / Vista | 6 / 30 / 300 m | 5.7–20 / 29–100 m / 0.29–1.0 km | Person in setting / group and terrain / landscape |

**Object targets are always centred [V]; point targets compose [I].** The look-at is the target's `CameraPosition()`: for a soldier the
animated `pilot` memory point (the eye), else `zamerny`; for other objects `zamerny`, the geometry-box or bounding centre, re-read every frame
(`CameraHold.cpp#L53-L67`; `Object.cpp#L1651-L1664`; `SoldierOldActions.cpp#L2339-L2379`; `SoldierOldSimProxy.cpp#L1391, #L1425`). There is
no offset, unlike Cinemachine's Rotation Composer or Unreal's look-at Relative Offset [V docs]. So aiming atan(0.25·FOV) below the eyes puts
them on the upper-third line; lead room is a point target ~d·FOV/3 ahead of a moving subject, resampled; groups follow Cinemachine's Group
Framing [V concept] (radii 0.5–1 m per soldier, box half-diagonals for vehicles, leader weight 2, framing size 0.6–0.8, "dolly then zoom"
within FOV 0.2–0.9). Object targets stay for pans, tracking and wide scales, where head-aimed shots check that the feet stay in frame.

**Safe frame [V geometry; I margins].** While `showCinemaBorder` is on (the default, reset to on by every mission and cutscene display),
a camera effect draws the `CinemaBorder` letterbox model stretched to full width, so its bars take the same share of screen height at every
aspect (`World/WorldImpl.cpp#L2204-L2215`; `Object.cpp#L1190-L1209, #L1334-L1344`; `UI/DisplayUIMenus.cpp#L827, #L1177`). In mission mode it
then adds pillarbox bars outside a centred 4:3 band, but only under the Modern display style (default; Legacy turns them off) and while
"gameplay active" is on (`Object.cpp#L1289-L1332`; `Presentation.cpp#L14, #L24-L29`). `showCinemaBorder false` (registered on every
profile, 18 official uses) removes both the letterbox and these bars [V]. Sections render full width because gameplay is inactive in
intro mode (`World/WorldInit.cpp#L529-L533`), which covers every cutscene display: Intro and Outro sections and campaign chapter and award
cutscenes (`UI/DisplayUIMenus.cpp#L1232-L1440`); a cutscene built as a campaign mission's own Mission section plays in mission mode, and
loading a save turns gameplay on (`WorldImpl.cpp#L1585-L1586`). `titleObj` and `cutObj` force the bars everywhere, even under Legacy, and
flagged `RscTitles` overlays draw them in sections too (`Game/TitEffects.cpp#L360-L391`). Rule: primary subjects stay within
|x/z| ≤ FOV × 1.0 and |y/z| ≤ FOV × 0.75 with a 5% margin, shrunk by the letterbox bars (height from game data, CP1; inner ~70% until
measured) and by the subtitle band during lines. Each `ScreenAnchor` is a target position plus a tolerance box: Cinemachine's dead zone,
checked offline instead of damped at runtime.

### 4.3 Terrain, objects and visibility

- **Base grid [V].** All five stock islands (Malden, Kolgujev, Everon, the desert island, Nogova) are 256×256 cells of 50 m; the OPRW loader
  forces 50 m whatever `CfgWorlds` says (`World/Terrain/LandSave.cpp#L97, #L1300-L1322, #L1587-L1588`). Cells split into two triangles along
  the (1,0)–(0,1) diagonal; `SurfaceY` is −100 off the map; `SurfaceYAboveWater` = max(terrain, sea level), with sea level a 0–5 m tide
  plus a ±0.25 m wave of 12.5 s period (`Landscape.cpp#L727-L748, #L1536-L1653, #L1951-L1960`). An over-water key's h is measured from
  the live sea surface at the call (tide and wave included), and the clamp uses the same surface, so a key needs only the wave and the
  camera radius (0.5 m trough to crest plus 0.3 m, so ≥ 0.8 m above the water); the full 5.25 m tide-plus-wave allowance applies only
  where the planner judges a segment or sight line in absolute height without knowing the tide [I on V].
- **Runtime subdivision [V].** Every mission start subdivides to the player's terrain grid in halving steps (`WorldImpl.cpp#L1051-L1089`).
  Remastered maps terrain detail Low…Extreme to 50/25/12.5/6.25/3.125 m, defaults to Ultra and picks a first-boot preset from system RAM
  (`UI/Settings/GraphicsApply.cpp#L16-L33`; `GraphicsConfig.hpp#L26-L28, #L68`); MP forces 25 m; `setTerrainGrid` changes it. Steps smooth
  and add position-seeded noise (each term ≤ 0.05 × cell relief; both read the `Fractal` class, an engine slip), skip forest, water ≥ 1 m,
  building, near-flat and sub-zero cells, give roads no noise, and re-seat objects except forest blocks (`LandSave.cpp#L430-L494, #L577-L944`).
- **Measured [V].** Remastered and CE cache the result (`cwr_subdiv_<wrp>_L<n>.cache`, magic `SDCV`; `LandSave.cpp#L957-L1062`). Against the
  owner's caches (Malden and Everon at 6.25 m, the desert island), only 5.6–33.5% of land cells stay exact; per-vertex |Δ| has median
  0.1–0.4 m, p99 2.9–3.7 m, max 8.9–30.4 m. Forest cells are 100% exact; road cells' per-cell maximum has median 0.5–0.6 m (p99 2.7–3.1);
  other open cells 1.7–1.9 m (p99 5.4–7.6).
- **Consequences [I on V].** Key heights are exact by construction: `camSetPos`/`camSetTarget [x, y, h]` resolve h on the real surface at
  the call (`GameStateExtGrp.cpp#L885-L951`; `GameStateExtUi.cpp#L1469-L1485`, `#L1566-L1580`), so keys are stored AGL. A `camSetRelPos`
  key is not: it is an offset from the target's position (its heading, world up), resolved once at the call (`GameStateExtUi.cpp#L1487-L1504`),
  so it is checked at the target's predicted position like a segment point. Segment interiors (straight in absolute
  space), grazing sight lines and eye-to-subject heights across cells need the true surface, from a ladder shown as a badge: the player's
  cache (read-only) → emulation (heights, geography flags, object classes, the engine's positional seeds, texture roughness) → base
  triangles plus a margin (0 m forest, water, flat; ~3 m roads; ~6–8 m open relief). Short-margin segments are badged "estimated" with
  fixes: via-keys (each exact), raise, or cut instead of moving.
- **Paths, not keys [V].** Land rises across one 50 m edge reach p99 22–41 m (max 44–193 m), so a straight move between safe keys can pass
  under a ridge; segment–triangle tests walk every crossed cell (DDA). The camera is only clamped 0.1 m above the surface and objects are
  ignored (`World/World.cpp#L1208-L1217`; `CameraHold.cpp#L288-L324`).
- **Objects [V data; I model].** WRP records hold a model index and a 3×4 transform (`WrpReader.cpp#L358-L389`): 56,740–177,224 objects per
  populated island, p90 10–21 per occupied cell; each file lists 19–484 peaks for vantage menus (`#L282-L288`); P3D map info gives boxes and
  map types (doc 07 §7); geography flags mark roads on 4.7–9.5% and forest on 3.4–16.6% of land cells and the track flag nowhere
  (`AI/Path/AITypes.hpp#L39-L57`). The eye stays outside every box grown by a 0.3 m camera radius (covering the ≤ 0.2 m near plane).
  Occluders are hard (buildings, walls), soft (trees, bushes, forest cells; attenuated by path length) or ignored, plus mission units.
  *Visibility* [V method; I thresholds]: nine rays to each primary subject's box corners and centre (Ranon and Urli's sampling, used by Lino
  and Christie 2015) pass at ≥ 80%, tolerating ≤ 0.5 s of occlusion; the engine's own test likewise walks terrain cells, then objects in a
  ±1.5-cell band (`World/Simulation/Collisions.cpp#L1724-L1843`). Tree boxes include canopies, so the thumbnail is the final judge.
- **Draw distance [V].** `setViewDistance` clamps to 100–5000 m; objects draw only to min(2/3 × view, 3000 m) (never under 100 m), shadows
  to 5/18 (at most 500 m); fog sets the far plane (visibility = 1 − 0.95·fog; rain pulls it toward 350 m; night × 0.75–1)
  (`UI/Settings/ViewDistance.hpp#L8-L67`; `GameStateExtUi.cpp#L1774-L1805`; `Landscape.cpp#L654-L682`; `Scene.cpp#L122-L157`). Each mission
  or section load resets it to the preferred distance (900 m in MP) and no getter exists (`WorldImpl.cpp#L1075-L1089`; only `accTime` has one,
  `GameStateExt.cpp#L863`). On Cwr/Ce the preferred distance is the player's setting, or the Mission section's Intel `viewDistance` while
  the player's "respect mission view distance" option is on (default on); script `setViewDistance` has no such gate
  (`UI/OptionsUI.cpp#L167-L179`; `UI/Locale/MissionLanguageDetector.cpp#L300-L317`; `UI/Settings/GameSettingsConfig.hpp#L22`; doc 37 WA05).
  So the planner sets the distance itself for far shots (harmless in sections) or assumes 900 m (600 m objects), keeping subjects within
  0.9 × the object distance [I]; an in-mission restore can target the Intel value on Cwr/Ce, which is right unless the player turned the
  option off, and on Cwa199 still has no known value (DR21). CP8 thereby narrows to 1.99's behaviour and to mid-mission option changes.

### 4.4 Cut grammar and pacing

- **Action line.** Keep one side of the line between two subjects or along a movement axis; cross only through an on-axis shot or a move
  across it within one commit (Wikipedia "180-degree rule"; VC "don't cross the line") [V]. Cutaways as an excuse: house style [I].
- **Jump cuts.** Between shots of one subject, change vantage ≥ 30° or scale ≥ 1 step (30-degree rule; Galvane et al. 2015 require
  "sufficient change in either its apparent size or its profile angle") [V]; keep screen direction and left-to-right order [V].
- **Establish** early and again after ~20 s of close coverage or when a new subject enters (the VC's 100-tick exception at ~5 ticks/s [V
  text; I conversion]); official intros follow no rigid ladder (42% of cuts keep scale, 30% tighten, 28% widen; heuristic classes [I]).
- **Dialogue coverage** (idioms after Leake et al. 2017 [V]; thresholds [I]): open on a two-shot; cut on line starts to the speaker or an
  over-the-shoulder; close-ups only for lines tagged emotional; no cut for lines under ~1.5 s; one scale step at a time; a reaction after ~6
  s on one speaker. **Hand-off** [I, after Nesky's GDC 2014 advice via a third-party summary]: the last shot before control returns looks
  along the player's heading or from behind him, or ends on a fade.
- **Tempo** is an enum. Standard fits official multi-shot sequences (linearly timed camera scripts with ≥ 4 cuts; 48 scripts, 509 shots):
  empirical median 5.0 s and ASL 6.8 s; the fitted log-normal μ = 1.67, σ = 0.70 has median e^μ ≈ 5.3 s and mean 6.8 s [V, re-run]; Brisk ~4.5 s
  (post-classical features 4.3–4.9 s, Bordwell via Wikipedia [V]); Slow ~9 s; Montage shrinks holds, as one official intro does from 1.5 s
  to 1.1 s, each opening with a 1 s cut-layer BLACK IN [V], down to ~0.8 s. Cost per shot (ln d − μ)²/2σ² + λ(ln dᵢ − ln dᵢ₋₁)², since
  neighbouring shot lengths correlate (Cutting, DeLong and Nothelfer 2010 [V]). Floor 2 s (4.3% of official shots are shorter), style note
  above 12 s (10.8%) [V]. Cut points come from line starts, BPM-tagged accents, gates + 0.2–0.5 s (ClearShot's "Activate After" [V
  concept]) and move ends; a small dynamic programme over 5–40 shots picks them (Galvane et al.'s semi-Markov solution [V method]).
- **Fades and slow motion.** BI fades in about once per 4.7 cuts, never on the title layer [V]; a per-cut dip from black is a Montage option
  (doc 32 §5.4's flash lint targets IN/OUT alternation, which it does not trigger). Slow motion 0.2–0.3 for 1–2 impact shots: commits,
  waits and fades run on game time [V], so the compiler converts durations; the driver saves `accTime`, forces 1, restores it at the end.

### 4.5 From intent to commits: sampling and gates

Curves become commits as in doc 32 §3.5: eased keys and follows sampled at 4 Hz, pans split into ≤ 45° segments, FOV re-set per segment,
targets changed only at a deadline. **Gates** join absolute segments (official scripts cut on deaths, damage, ammo, flags, `unitReady` and
`mapAnimDone` [V]); each has a closed-menu condition, a timeout and a fallback, and flags are initialised before any wait (a non-Boolean `@`
reads as false, doc 32 §2.7). Cues after a gate are relative to its opening; the map and timeline draw the span as elastic [I].

```sqf
; gate g1 (CA05): cut when the scout (the unprotected casualty) is hit or the staged contact flag rises, at the latest at 18 s
@((!alive ofpe_a_scout) || ofpe_f_contact || _time > 18)
_g = _time
; shot 6 "Reaction", 0.3 s after the gate: cut, eye level, normal lens
@(_time >= _g + 0.3)
ofpe_cam camSetTarget [5114.0, 9880.5, 1.2]
ofpe_cam camSetPos [5112.4, 9876.1, 1.6]
ofpe_cam camSetFov 0.35
ofpe_cam camCommit 0
```

### 4.6 Candidates, scoring and repair

Per idiom step [I]: resolve subjects and predicted positions (§5); solve scale into distance per lens; generate vantages (one subject: θ
every 15°, φ −5° to +40°, each lens, on the correct side of the line; two subjects: Toric (α, θ, φ), which cuts the search from 7D to 4D but
has no closed form, so its authors prune property intervals and sample, 60–380 samples in 5–40 ms [V], each solution becoming an eye plus a
point target on the solved axis; groups: group framing); run the hard checks (§6.1); score; keep the three best distinct candidates as takes.
Exhaustive generate-and-test suits offline planning (Bares et al. searched 50×50×50 positions, 15° steps and 10 FOVs, per the Christie,
Olivier and Normand survey [V]); sampling at keys and 10 Hz can miss very short violations [I]. The soft score sums visibility, anchor
error, distance from the scale's optimum (Cinemachine Shot Quality Evaluator [V concept]), continuity, novelty and pacing fit; ties break by
idiom priority (as ClearShot does after quality [V]), then seed; menus and seeds are recorded (doc 25 §6.2). When all candidates fail, code
computes fixes after Cinemachine's Deoccluder strategies [V concept]: pull forward, rise or orbit at the same distance, change lens, add a
via-key, cut instead of moving, switch variant; a weak model may pick one (doc 25 §7.2). **Cost [I]:** a 600 m sight line touches ~50 land
cells and 500–1,000 boxes at p90 density; a 30 s shot at 10 Hz, 5 subjects and 9 rays is 13,500 rays, cheap enough to run on every drag.

### 4.7 Type sketch (proposal-only; not compiled; names not final)

```rust
// Module `director` beside doc 32's model; exact terrain in a new `ofp-terrain` crate. Private fields, validating constructors, AGENTS.md
// newtypes; one crate `Error` enum with structured fields, e.g. `NoAdmissibleCandidate { shot: ShotId, generated: u32, rejected_by: CheckId }`.
pub struct DirectorRequest { archetype: ArchetypeId, variant: VariantId, host: SequenceHost, subjects: SubjectPicks,
    tempo: Tempo, mood: Mood, realism: Realism, take: TakeSeed }        // everything a model may touch is an id or an enum
pub enum Tempo { Slow, Standard, Brisk, Montage }                       // ASL ≈ 9 / 6.8 / 4.5 s; Montage holds ≥ 0.8 s
pub enum Realism { Cinematic, Grounded, Doctrinal }                     // visible per-mission setting; advisory only
pub struct ShotSpec { step: IdiomStepRef, subjects: NonEmpty<SubjectRef>, scale: Scale, lens: LensPreset, motion: Motion,
    side: LineSide, anchors: Vec<ScreenAnchor>, dur: DurBand }          // declared intent, kept beside the computed keys
pub enum Scale { Ecu, Cu, Mcu, Ms, Mls, Fs, Ls, Els, Vista }            // → visible height H; distance = H / (1.5 × FOV)
pub enum Motion { Static, GoBy, Pan { to: SubjectRef }, Dolly, Crane, PushIn, PullOut, Track(Follow), Orbit { arc: Deg }, Zoom, MapInsert }
pub struct ScreenAnchor { subject: SubjectRef, x: Frac, y: Frac, tol: Frac } // fractions of the 4:3 safe band
pub struct Fov(f32);                                                    // 0.01..=2.0, checked in from_raw
pub struct CellSize(f32);                                               // 50 m for OPRW (loader-forced); config value for 4WVR
pub enum TerrainSource { SubdivCache { level: u8 }, Emulated { level: u8 }, BaseWithMargin }
pub enum Evidence { ComputedExact, Estimated { spread: Metres }, GameVerified { run: RunId } }
pub struct Gate { cond: GateCond, timeout: Millis, react: Millis, fallback: GateFallback } // cond: UnitNear | Dead | Damaged | Flag | MapAnimDone
pub enum Prediction { Exact, Slot, FollowFile { gap: MetresBand }, Estimated { envelope: Metres } }
pub fn direct<'island>(req: &DirectorRequest, facts: &WorldFacts<'island>, mission: &MissionModel) -> Result<DirectorPlan, Error>;
```

## 5. The staging planner

### 5.1 Tactical recipes

Positions follow doctrinal spacing times a visible tightening factor; behaviour is checked against the movement it implies [I]. Doctrine is
from the manuals cited [V unless marked]; the engine column relies on §5.2.

| Recipe | Doctrine | Engine realisation |
| --- | --- | --- |
| Foot patrol | Fire-team wedge normally 10 m between soldiers; file when terrain rules it out; squad column most common (FM 7-8 §2-7, §2-8) | AWARE+ WEDGE, neighbours along an arm ~7.1 and ~8.3 m; file → COLUMN, staggered → STAG COLUMN; the doctrinal squad column (two wedges) needs two groups |
| Column on the road | Foot march 2–5 m by day, 1–3 m at night; 50 m between platoons (FM 21-18) | SAFE or CARELESS: units follow in ID order at ~3–4 m, preferring roads |
| Convoy | Close column 25–50 m below 25 mph, open ≥ 100 m above (FM 4-01.011 App. C); march unit ≤ 25 vehicles (FM 55-30 ch. 5) | One SAFE group settles at ~15–25 m; open column = one group per vehicle or march unit, timed starts; frame wider or track single vehicles |
| Overwatch and bound | Technique by chance of contact (FM 7-8 §2-10); lead team ideally ≥ 50 m ahead (ATP 3-21.8, 2024); bounds within 2/3 of the overwatch weapons' range (FM 3-21.71 §3-3) | Two groups, AWARE or COMBAT; overwatch prone with `doWatch` sectors; short `doMove` bounds; film overwatch first |
| Helicopter insertion | Approach from the front, never near the tail; crouched, downslope; 15–20 m out, prone, facing out until it leaves (FM 90-4 App. E) | `special FLY`, land, GETOUT; ring 15–20 m, `setUnitPos "DOWN"`, outward `doWatch`; AWARE wedge after lift-off; eye ~1 m |
| Helicopter extraction | Smoke: the aircrew reports the colour, the ground confirms (Wikipedia "Landing zone") | Smoke class, exchange template, boarding from the front, GETIN |
| Halt and perimeter | Short halt: off the route, prone, same sectors (cigar-shaped); long halt: perimeter, 360° (FM 7-8 §2-4; ATP 3-21.8) | Prone with `doWatch` sectors; full ring for long halts; duration is the user's |
| Orders group | BI's in-engine orders scenes (doc 35 rc20) [V]; shape [I] | Semicircle 2–4 m, eyelines, talk moves |
| East-side presets | Vehicles 15–50 m on roads, 50–100 m cross-country; dismount 300–400 m out (secondary source citing Isby 1981) [I] | Badged "secondary source" until FM 100-2-1 is read |

**Realism setting [I].** *Cinematic* tightens freely (BI's exactly placed intro infantry stand at a median 3.75 m, §9); *Grounded*, the
default, slides between doctrine and engine spacing; *Doctrinal* shows every TP note. No setting blocks a choice.

**Modules first [I].** Units already driven by a doc 31 module (convoy, patrol, air transport) are filmed as the module runs them: their
`Prediction` comes from the module's parameters, and any change is proposed as a module-parameter edit, never as a second staging.

### 5.2 Engine truths the planner encodes

- **Slots [V].** Seven formations, each a fixed slot table (base slot, x/z offset, watch angle); offsets scale by the mean of the two
  units' `formationX/Z` (Man 5×5 m, Car 20×20, Tank and Truck 20×30, Air 50×100, from the owner's config); slots follow the subgroup leader
  turned by `setFormDir`; new subgroups start in wedge (`AI/AISubgroup.cpp#L53-L159, #L494-L501, #L2113-L2209`; `AI/AIUnit.cpp#L1546-L1621`).
  The 0.1–1.5 "formation coefficient" only limits the leader's speed, and LIMITED caps it at 22% outside COMBAT (`#L2211-L2305`). No script
  command sets spacing.
- **Who holds a slot [V].** A non-"cautious" unit ignores its slot and follows the previous non-cautious unit of its subgroup in ID order
  (the subgroup leader heads the file), aiming 0.4 × the pair's mean `formationZ` behind it and closing to 0.6 × mean `formationZ` + 0.5 s ×
  the followed unit's speed; a vehicle waits when its successor falls over 3 × `formationZ` behind (`AI/VehicleAIPilot.cpp#L286-L310,
  #L618-L780`; `AI/AISubgroup.cpp#L2041-L2110`). Cautious means AWARE, COMBAT or STEALTH, but only COMBAT or STEALTH for
  cars and motorcycles (`AI/VehicleAI.cpp#L2358-L2367`; `Car.cpp#L2271-L2280`). Soldiers use the same pilot (`SoldierOldAI.cpp#L1730-L1738`);
  non-cautious units prefer roads (`AI/Path/PathPlanner.cpp#L343-L344`). Arithmetic [I until CP9]: cars ~12 m + 0.5 × speed (16–20 m at
  30–60 km/h), tanks and trucks ~18 m + 0.5 × speed, soldiers ~3–4 m at a walk.
- **Placement [V].** FORM units (the editor default) are moved into slots at mission start, facing the leader's heading; NONE and FLY keep
  their placement, CARGO starts inside (`AI/AICenterImpl.cpp#L1920-L1927, #L2142-L2185`). Map and thumbnails show post-snap positions.
- **Looks [V].** Without a watch order a unit looks along its slot angle; idle soldiers pick targets unless AUTOTARGET is disabled
  (`AISubgroup.cpp#L2191-L2201`; `AI/AIUnitImpl.cpp#L1279-L1300`). Crews turn out at SAFE/CARELESS, button up at COMBAT/STEALTH
  (`TransportCore.cpp#L874-L886`). Under fire a group rises to COMBAT and, unless its leader is CARELESS, unloads Car and Motorcycle cargo;
  CARELESS units ignore the raised mode (`AI/AIGroup.cpp#L783-L806`; `AI/AIUnit.cpp#L1290-L1312`).
- **Setters and orders [V].** `setBehaviour`, `setCombatMode` (group-wide) and `setUnitPos` silently ignore unknown strings, and official
  content ships such no-ops (`GameStateExtGrp.cpp#L171-L261`). `do*` orders are silent; `command*`, `setFormation` and `setCombatMode` (for
  non-leaders) go by radio; scripted moves drop when the leader is dead (`GameStateExtCommon.hpp#L15-L33`; `AI/AIGroupCmd.cpp#L37-L54`).
  `stop` is reversible; `disableAI` is one-way (`GameStateExtUi.cpp#L2362-L2405`).
- **Teleports [V].** `setDir` sets pure yaw. `setPos` seats units and vehicles on the highest roadway (road, bridge, building roadway) whose
  absolute height is ≤ the given h (+0.5 m for soldiers), else terrain or sea, adds h and aligns vehicles; so near sea level a mark above a
  bridge deck can land on it [I until CP13]. On crew it ejects; on island objects it does nothing; on non-AI entities (a `camCreate`d
  object, for example) h becomes an absolute height plus the model's lowest point, not a height above ground (`GameStateExtGrp.cpp#L1696-L1861`;
  `TransportCore.cpp#L58-L69`; `Landscape.cpp#L1775-L1885`).
- **Animation and `unitReady` [V].** `switchMove` snaps and re-queues the previous external move; a requested move is reached by a
  least-cost path; a state lasts 1/speed s; `CfgMovesMC` has 574 states (median 1 s, p90 4 s) (`SoldierOldMove.cpp#L364-L411`;
  `SoldierOld.cpp#L164-L223`), so chains are estimates. `unitReady` is false only while a listed subgroup leader holds a command: an actor
  given its own `doMove` leads its own subgroup, followers read true at once, and a path failing 3 times also ends it
  (`GameStateExtGrp.cpp#L1061-L1141`; `AI/AISubgroupFSM.cpp#L1402-L1439, #L2508-L2536`).
- **Variance [V sources; I effect].** Simulation steps by frame time × acceleration, fidelity drops with distance from the camera, and 133
  lines in 33 AI and entity files call the random generator (`World.cpp#L213, #L334`; `Simul.cpp#L1198-L1250`): AI timing is a distribution.

### 5.3 Commands per profile, robustness and synchronisation

| Tier | Commands | Use |
| --- | --- | --- |
| Registered, seen in official 1.99 content [V] | `setPos`, `setDir`, `doMove`, `commandMove`, `move`, `playMove`, `switchMove`, `stop`, `doStop`, `disableAI`, `setBehaviour`, `setSpeedMode`, `setCombatMode`, `setFormation`, `setFormDir`, `setUnitPos`, `doWatch`, `doTarget`, `doFire`, `doFollow`, `flyInHeight`, `moveInCargo`/`Driver`/`Gunner`, `setCaptive`, `allowDammage`, `setWPPos`, `unitReady`, `setVelocity` | All profiles |
| Registered, never seen on 1.99 [V] | `addWaypoint`, `setWaypointPosition`, `setWaypointTimeout`, `setVectorDir`, `setVectorUp`, `soundLength` | Cwr/Ce only; staging waypoints go into `mission.sqm` |
| Not registered [V grep] | `moveTo`, `enableAI`, `animationState`, `forceSpeed`, `limitSpeed` | Never emitted; linted |

Evidence: `CWR:Game/Commands/GameStateExt.cpp#L365-L372, #L1171, #L1220-L1437`; `docs/research/data/cwa199-observed-commands.csv`.

**Robustness contract [I on V].** (1) *Pre-place* every actor with placement radius 0 and presence 1, exact or at its true slot; BI's 1,754
Intro units have no placement radius [V]. This covers section units and actors the Director adds. An in-mission scene never rewrites the
presence, placement radius or start of the mission's own units (human craft, doc 28 §3.4): it films them where the mission puts them or
snaps them under a cut to marks the user approved, gates each on `alive` with the fallback shot, and offers any placement change as a
separate undoable suggestion. (2) *Protect and freeze* with the protected-actor bundle: CARELESS, `setCombatMode "BLUE"`,
`setCaptive true`, `allowDammage false`, `setUnitPos "UP"`, LIMITED, plus `stop true` (actors returning to play) or `disableAI` (intro-only,
labelled irreversible). Only the protection half (captive, `allowDammage false`, BLUE, quiet radio) is universal; behaviour, stance and speed
yield to the staging recipe, so an AWARE wedge stays AWARE (TP02), overwatch stays prone, and `stop` never freezes an actor with a planned
move. It mirrors official Intro inits (SAFE 221 and CARELESS 184 of 457 behaviours, BLUE 150 of 152, UP 139 of 157 [V])
and is safer than BI (1 camera script in 329 uses `allowDammage`). Radio-borne setup goes out before the camera starts; radio stays quiet,
which also stops AI chatter delaying `say` (doc 32 §2.5); the epilogue restores the values read when the scene started, falling back to
authored ones, so a group already in COMBAT is not reset to SAFE (the `behaviour`, `combatMode` and `captive` getters are registered,
`GameStateExt.cpp#L995-L1017`; the first two appear in 1.99 content, `captive` only in the CWE mod [V]). (3) *Short silent moves:*
`doMove` per actor, SAFE or CARELESS at LIMITED, budget = path length ÷ the LIMITED speed (at most 0.22 × the class's config maximum
outside COMBAT, `AI/AISubgroup.cpp#L2285-L2297`) × slack; BI teleports far more (`setPos` 823 lines
against 17 `doMove` [V]). (4) *Watchdog and snap:* each AI cue waits `@((unitReady u && u distance mark < r) || _time > budget)` with a
`setPos`/`switchMove` snap only under a cut, a fade or proven off-frame. (5) *Frame for uncertainty:* tight or off-centre framing only for
staged actors; AI subjects get wide go-bys, object-target pans or `Resample` follows validated over a ±30% speed band; cut before arrival.
(6) *Fallback shot:* each AI-dependent shot has a precomputed alternative that the gate's timeout cuts to.

**Synchronisation [I].** Staging cues sit on the Actors track, timed by the pacing pass as absolute or gate-relative cues: snaps under cuts,
move starts ahead of their shot, `switchMove` under cuts or `playMove` on screen with its estimate, `doWatch` eyelines to each speaker for
every listener (official cutscene missions: `doWatch` 249, `switchMove` 171 against 20 `playMove` [V]), releases in the epilogue. Shot
planning reads each actor's `Prediction`, and projection checks use predicted, not editor, positions.

## 6. Verification

### 6.1 Director checks

Each check filters generated candidates and lints hand-made shots. For hand work, errors are kept for what the engine will not do as shown
or what can stall or lose state (AGENTS.md); the rest are warnings or dismissible style notes. Doc 32 §3.7's lints still apply; where a DR
check restates one of them or doc 28 MC19 (DR11–DR13, DR16, DR18), both share one finding and message, so nobody sees a problem twice.

| Code | Check | Filter | Lint |
| --- | --- | --- | --- |
| DR01 | Camera underground or off map: eye clearance at keys and along segments on the best terrain source; an over-water key < 0.8 m above the live water, or a coastal segment that needs the unknown tide (up to 5.25 m, §4.3) | Reject < 0.3 m + margin | Error below surface or off map; warning < 0.3 m + margin (moving: < 1 m); worm's-eye badge 0.3–0.5 m |
| DR02 | Eye inside an object box + 0.3 m radius | Reject | Warning (interiors can be intended) |
| DR03 | Subject off frame: primary subject outside the safe frame at any 10 Hz sample | Reject | Warning |
| DR04 | Visibility < 80% on 9 rays for > 0.5 s | Reject hard, score soft | Warning |
| DR05 | Subject beyond 0.9 × object distance or fog range | Reject | Error beyond the object distance (not drawn) |
| DR06 | Projected size outside ±25% of the declared scale | Score | Style note |
| DR07 | Retarget per commit > 90° / ≥ 150° | Split ≤ 45° | Warning / error |
| DR08 | Pitch outside −75°…+45°; target < 1 m from the eye | Reject | Warning |
| DR09 | Action line crossed without an on-axis shot or crossing move | Reject | Style note |
| DR10 | Jump cut (same subject, < 30° and < 1 scale step); reversed screen direction or order | Reject / score | Style note |
| DR11 | Shot too short or long: < 2 s (montage 0.8 s) / > 12 s | Never / style | Warning / style note |
| DR12 | Sequence over budget, every gate at its timeout (per archetype; in-mission 20 s per doc 28; node 240 s per doc 35 rc64) | Never | Warning |
| DR13 | Cut-layer fades: a fade or card on the title layer where the cut layer belongs; title-layer BLACK OUT before an END; flashing | Never | Error / error / warning |
| DR14 | A gate without timeout or reading an uninitialised flag | Never | Error (stalls) |
| DR15 | A snap visible on screen | Never | Warning |
| DR16 | Speaker > 100 m from the camera with plain `say` (subtitles hidden); speaker off screen on his line | Reject / score | Warning / style note |
| DR17 | Skip path: state written after a section driver's first cue | Never | Error |
| DR18 | Input locks: any `disableUserInput` in a section; unbalanced locks in-mission | Never | Error |
| DR19 | Orders: `unitReady` without its own move; radio-borne orders in a sequence; a possibly dead leader; commands outside the profile catalog | Never | Warning / error |
| DR20 | `setPos` on crew, island objects or non-AI props; a mark over a roadway near sea level | Never | Warning |
| DR21 | Restores: slow motion over `say` while CP2 is open; in-mission `setViewDistance` with no known value to restore | Avoid | Warning |
| DR22 | Terrain source "estimated" on a segment or sight line that relies on less than its margin | Fix or badge | Warning until thumbnail-verified |

Skip facts behind DR17–DR18 [V]: Space or Esc (on Remastered also a gamepad Cancel, turned into Escape during any camera effect) closes a
cutscene display at once and runs no hook; `exit.sqs` runs only on the mission display's end path
(`UI/DisplayUIMenus.cpp#L710-L724, #L984-L991, #L1173-L1207`; `Input/InputProcessingSdl.cpp#L412-L425`). Time acceleration, camera effect,
radio, terrain grid and view distance reset at every mission init, but the input-lock counter only when the World object is built
(`World/WorldInit.cpp#L167, #L533-L537, #L1056-L1098`). So section drivers never own state: campaign variables go in `initintro.sqs` first.

### 6.2 Tactical plausibility notes (advisory; each with a fix and an "intentional" dismissal linked to Standing Orders, doc 33)

| Code | Note | Fix |
| --- | --- | --- |
| TP01 | Spacing outside the doctrinal band and not marked cinematic | Snap to band; mark cinematic |
| TP02 | A slot formation with SAFE or CARELESS: the group will follow in a file | Switch to AWARE; accept the file |
| TP03 | Open-column gaps requested inside one group | One group per vehicle or march unit, timed starts |
| TP04 | Ground vehicles off road cells while SAFE or CARELESS | Snap to the road polyline |
| TP05 | Dismount or boarding path behind a helicopter's tail; an LZ that is not flat and open | Re-route from the front; pick another site |
| TP06 | A long halt without 360° sectors | Assign sectors |
| TP07 | Behaviour inconsistent with the look (heads out needs SAFE or CARELESS) | Change behaviour or look |
| TP08 | "Over and out", "roger wilco", no closing proword (ACP 125 via Wikipedia "Procedure word"); REPEAT for SAY AGAIN only a style note with a "period-authentic" toggle, since BI's radio-style lines use "repeat" 20 times and "say again" 3 [V] | Code-framed prowords |
| TP09 | Actors unprotected while fire happens nearby | Apply the protected-actor bundle |
| TP10 | A behaviour change mid-scene that visibly re-forms the group | Move it under a cut |

### 6.3 In-game checks through the harness

- **Building blocks [V].** The JSON harness offers screenshot, eval and exec (`Dev/Harness/HarnessBuiltins.cpp#L58-L98`); `triScreenshot`
  writes sequence-prefixed PNG and BMP files to `$TRI_OUTPUT_DIR` (`GameStateExtTestRender.cpp#L225-L261`); `triSceneReady` accepts display
  46 or 47 once the engine's lifetime frame counter reaches 2, which it never resets, so it reads OK as soon as the display is up and the
  pipeline adds its own settle frames (`Graphics/Core/Engine.hpp#L310, #L328`); `triSimFrames n` runs full ticks (≤ 600) while
  `triWaitFrames` draws no scene; `triSetSimTime` pins game time
  (`GameStateExtTest.cpp#L1953-L2059`). `tri*` commands need `--dev`, `--harness` or `--test-mission`; `triGet*` getters register always
  (`GameStateExtTestAudio.cpp#L2960-L2965`; `GameStateExtTestGetters.cpp#L535-L573`).
- **Per-shot thumbnails [I].** Stage the section as the Intro of a group-less Mission (doc 08 §4.2, correcting doc 32 §4.3); wait for
  `triSceneReady`, then settle a few `triSimFrames`; freeze with `setAccTime 0` and `triSetSimTime`; per shot snap actors to planned marks
  and poses, set the camera with `camCommit 0`, run `triSimFrames 2`, `triScreenshot "shot_<id>"`. For in-mission hosts first
  `triSetAspectGameplayActive true` (`GameStateExtTestAudio.cpp#L1318-L1322`) so the bars appear; `triSetPillarboxBarsEnabled false`
  previews the Legacy look (`#L1306-L1310`). Badge "camera exact, staging planned"; the image shows real subdivided terrain and objects, so
  it judges DR01–DR04 and DR22.
- **Filmstrip and detectors** [V getters, `GameStateExtTestGetters.cpp#L64-L69, #L161-L218`; I use]: a full run screenshotting each cue,
  sampling `getPos` against marks, `triPerfStats`, and `triGetCameraEffectActive` after the end; `triGetBackBufferNonBlackCount` for black
  frames or stuck fades; `triGetPixelMaxChannel`/`triGetPixelMaxDiff` grids for uniform frames (inside geometry, sky only); an A/B occlusion
  probe (move the subject away, diff offline); a pop-in diff for far cuts. Repeated runs give each AI cue a stability score.
- **Risks [U].** Harness flags in shipped binaries; AutoTest ends the game on any script error; the `setAccTime 0` freeze and zero-step
  `switchMove` poses (doc 08 §6; doc 32 open question 3). Without a harness: 2D checks; on 1.99, export plus the stock Preview.

### 6.4 Cutscene readiness report

```text
seq_intro_dawn  CA01 Establish the AO   host Intro   36.5 s (default 25–40 s)   6 shots   profiles cwa199 cwr ce
Compile   doc 32 lints pass on all profiles; profile floor Cwa199
Terrain   subdivision cache L3 (6.25 m, player setting); 2 segments estimated on open relief → via-keys added
Framing   5 of 6 thumbnails game-verified (run 2); shot 4 estimated (AI convoy, envelope ±7 m); A/B residual max 3% of width
Staging   8 actors (6 exact, 2 slot-predicted), protected; 1 gate (worst case 39 s at its timeout, fallback shot 5b)
Timing    ASL 6.1 s (Standard); 4/4 lines cut-aligned; first line 11 s; fade in 0.5 s; fade out at 35.5 s
Skip/Access  Space/Esc; no state after the first cue; no input lock; subtitles on; reading speed OK; no flash
Tactics   TP01 spacing 5 m ("cinematic" suggested); TP08 missing OUT on line 3
```

## 7. UX

**Make a cutscene [I].** (1) Start from the palette (`/cutscene`), a context menu on a unit, marker, trigger or END state, or an accepted
doc 32 §5.2 suggestion. (2) Pick the intent from ≤ 7 cards valid for the host (the rest under "more"). (3) Pick subjects on the map: every
role arrives pre-filled with code's top candidate (doc 25 §10.1), so intent → takes can be one click; each role highlights code-computed
candidates (units, groups, markers, island sites, vantage points) and "use selection" fills roles. (4) Confirm defaults as editable chips
(host, variant, tempo, mood, realism, music; mood uses doc 41's music mood tags, and light and weather come from the section's Atmosphere
card, doc 41 §3.1). (5) Choose one of three takes that differ in kind (idiom variant, vantage side, tempo; doc 25 §6.2 step 4), shown at
once as storyboards with 2D frustum sketches (doc 32 §3.3's silhouette sketch on Cwa199) while harness thumbnails stream in. (6) Tweak on
timeline and map: dragging a key pins that shot (a template-backed shot first asks once to bake, doc 32 §5.1), "coverage" offers
alternatives, re-planning keeps pins (doc 25 §9), and "fly and capture" (doc 32 §4.4) replaces one shot's keys. When a subject or the
mission changes later, dependent shots turn Stale with the reason (doc 25 §9.2): free shots offer a one-click re-plan, pinned shots keep
their keys and show their DR findings. (7) Check readiness, play the filmstrip.

**Storyboard view.** Shot cards on doc 32 §3.3's shot lane: thumbnail and evidence badge, scale and lens (FOV and mm), duration, idiom step,
check chips, line text. Hovering lights frustum, look line and action line on the map; gated spans show as elastic; pinned shots carry a pin.
The inspector opens with one plain-language purpose line computed from the idiom step ("orients the player: objective 800 m north-east of
the start"), linked to Standing Orders C1 (doc 33), then archetype, step, model, seed and the `ShotSpec` residuals, after PACE's
field-by-field conformance measure (Duan et al. 2026).

**Fun touches.** *Director's cut:* Shuffle shows three seeded takes side by side. *"Like BI":* §9.1's official grammar as one preset.
*Suggestions:* "add a reaction", "re-establish here", "cut on this line", "make it a reveal", "pan to the objective". *Tactical overlay:*
slot sectors, spacing rings and predicted follow files, linked to Standing Orders. *Tempo meter* (doc 32 §3.3's): shot lengths against the
tempo band and music bars.

**Accessibility.** Subtitles on by default (`forceTitles` offered on story lines); length and skip policy visible on every sequence (players
asked how to skip long campaign cutscenes, §9.2); in-mission scenes ≤ 15 s by default, a walk-away "live scene" variant, a radio skip after
doc 32 open question 6; a "replay-friendly" option; doc 32 §5.4's reading-speed and flash lints; a "calm camera" preset.

## 8. The AI angle

| Decision (doc 25 shape) | Model decides | Code does |
| --- | --- | --- |
| Intent, variant (Pick) | One of ≤ 7 intents for the host; truck, helicopter or boat | Computes menus from host, mission state, story beat and available assets |
| Subjects (Pick per role) | A unit, group, marker or site from a menu | Builds role menus (doc 25 §6.2) described from facts only |
| Take (the user, via `approve`) | Nothing: takes are judged by eye, so batch runs keep code's top-ranked take (doc 25 §7.3) | Plans, checks, ranks and renders the takes |
| Style and text (Fill) | Tempo, mood, emotion tag per line; captions and line bodies through doc 32's `screenplay.write`; a callsign only where the story bible has none (admitted once as a bible row, then picked) | Maps enums to pacing, music and coverage; frames prowords, times lines, routes subtitles, runs V-text |
| Critique (Fill) | Phrases findings for the user through doc 32's `cine.critique` | Runs checks; computes and ranks fixes |

The model never types a coordinate, time, class name or FOV; out-of-menu answers are rejected and re-asked (doc 25 §7). PACE is the
cautionary measurement: framing driven by free text overshot the target head height 1.7–1.9×, against 0.96× with explicit geometry [V; the
transfer from image generation to engine cameras is I]. With AI off, Picks take seeded defaults and text stays as placeholder chips.
**Qualified models** (doc 25 §5.1) may **Compose** a custom idiom (a short shot list over §4.1's vocabulary with scales, anchors and
duration bands), validated as data, then planned and checked like a built-in archetype. The flow is a doc 38 workflow, `core/make-cutscene`
(`model_policy = "optional"`, all three profiles, scope mission): `pick` the intent from the `director.intents` menu (`on_fail` keeps the
suggested intent) → `map` over roles with a `pick` per subject → `code` `director.plan` (staging, shots, checks, three seeded takes) →
`approve` a take → `map` over text slots with `fill` → `verify` → `commit`, completion-gated on `cine.lints` and `director.checks`.

## 9. Corpus lessons and community craft

### 9.1 Populations and what BI did

Three populations from the owner's install, counted by our own local scripts [V as measurements; approximate]. **A**: official and
Remastered SQS files that commit a camera (329, only 255 content-distinct because MP template outros repeat up to 12 times); figures are
de-duplicated. **B**: 262 official camera scripts classified by host through exec chains (1985 113, Resistance 74, single missions 42, MP
33; 34 intros, 31 cutscene missions, 154 in-mission), not de-duplicated. **C**: official Intro sections (1,754 units). Timing is a linear
clock simulation that ignores control flow (present in 5 of 34 intros, 14 of 31 cutscene missions); a shot is a cut-to-cut span; scale
classes are heuristic.

| Measure | Official value | Director default |
| --- | --- | --- |
| Lengths (B) | Intros median 72 s (p25 50, p75 115; 1985 56.5, Resistance 115; 11 of 34 over 90 s); cutscene missions 125 s (18 of 31 over 120 s, 4 over 240 s); in-mission 6 s (114 of 154 under 15 s) | CA01 25–40 s; budgets warn; in-mission ≤ 15 s |
| Shots (A, B) | Intros 10 per scene, cutscene missions 21 (Resistance 27, p75 32.5); multi-shot sequences in A: 48, 509 shots, median 5.0 s, ASL 6.8 s, 4.3% < 2 s, 10.8% > 12 s | Standard tempo; 2 s floor |
| Kinds (B, intros) | Static 4 s, dolly 8.75 s, zoom 7.25 s, pan 8 s; 65% of commits are cuts; first shot a move in 65% (median 9.75 s) | Statics 3–6 s, moves 6–12 s; opening move |
| Eye and pitch (A, B) | `camSetPos` height median 1.60 m (p75 3.9, p90 11.8); in-mission 3.1 m; ±5° pitch in 271 of 427 intro shots; 1,789 of 1,928 point targets lie 90–110 km out (capture "infinity"); near targets median −8.9° | Eye level 1.5–1.8 m; high angles for establishing and threat |
| Lens (A) | FOV 0.7 in 43% of 2,434 settings; p25 0.39; 0.06 used dozens of times | Wide/Normal/Tele/Extreme presets |
| Moves (A) | Of 885 moving commits: pan 137, dolly+pan 106, hold 86, dolly+crane+pan 60, zoom 52, relpos+zoom 50; median 5 s; speed median 0.40 m/s; tilts unmeasured | Pan template; moves 4–8 s; zooms rare |
| Targets (A, B) | `camSetRelPos` in 29% of files (intro/outro median 6.2 m; front 155, behind 68, side 19); object targets in 47% of files; points outnumber objects ~4:1 in intro shots; `camSetDir`/`Bank`/`Dive`/`FovRange` never used | Front-quarter 3–8 m; §4.2 choice rule |
| Events (A) | 18% of files wait on deaths, damage, flags, `unitReady`, ammo or `mapAnimDone` | Gates |
| Grammar (B, intros) | Fade in ≤ 1 s 85%; end on a fade 91%; music 74%; a wide in the first three shots 24 of 34; last shot CU 18 of 34; first line median 14 s; every fade via `titleCut`; PLAIN cards in 4 of 34 | Intro recipe; cards optional |
| Dialogue (B) | `say` only, no radio commands, in intros and cutscene missions; 2.7 and 5.3 lines/min; 72% and 68% of lines start within 1 s of a cut | Cut on the line; CA10 |
| Housekeeping (A, B) | Slow motion in 27% of files (0.2 most common); `setAccTime 1` reset in 25 of 34 intros; `enableRadio false` in 49% of files; 115 in-mission scripts mute, 19 restore, 95 end on black; `setViewDistance` in 11 of 34 intros | Slow-motion option; radio quiet |
| Staging (A raw, C) | `setPos` 823 lines vs 17 `doMove`; waits 2,583 `@camCommitted` vs 8 `unitReady`; Intros 1,309 FORM men vs 129 NONE; NONE infantry nearest neighbour 3.75 m | Teleport-first; exact placement |
| Capture (B) | Capture-tool headers in 32 of 34 intros, 30 of 31 cutscene missions, 139 of 154 in-mission scripts | Capture is first-class |

### 9.2 Community craft and player memory

- **Tutorials** [V]: make the first commit instant or the camera floats in; secure units first; keep scenes short (aligrant). An ArmA-era
  PMC tutorial ends the intro with a script-set variable read by an END trigger, clears the title before the fade and fades music with the
  picture. Each is a compiler rule; no source here describes an in-mission skip.
- **Flashpoint Cutscene Maker v1.14** (needs Fwatch 1.15) [V manual]: two adjacent moves on screen, camera moved to a map point, "keep angle"
  height adjustment, actor freeze (zero velocity plus captive), per-move conditions, export with an `init.sqs` hook, import of capture-style
  scripts. The Director covers each natively, without an extender.
- **The stock death camera** [V, local corpus, paraphrased]: the shipped global `onPlayerKilled.sqs` waits ~2 s, fades to black on the cut
  layer and runs one of two scripts: a long-lens close-up of the body, a pull-back, a move to the killer and a slow zoom, then an endless
  loop; both call `enableEndDialog`. The DeathCam's first preset keeps the shape with a bounded ending.
- **Players** [V unless marked]: GameSpot's 2001 review credited "lengthy and generally well-directed in-engine cutscenes" [V-search]; a
  Resistance review called them lengthy (doc 28); a 2017 Steam thread asked how to skip long campaign cutscenes (answer: only Esc).
- **Machinima and later Arma** [V/V-search]: Wikipedia names puppetry, scripting (slow to perfect without WYSIWYG) and recamming recorded
  demos, and early Red vs. Blue actors had to estimate movements because a pistol pose kept them looking down: top-down blocking on our map,
  live preview and capture answer each. Arma 3's `BIS_fnc_establishingShot` and `BIS_fnc_infoText` became standard openers and BI's
  presentation guidance lists establishing and closing shots: precedent for CA01 and CA08 (a typewriter card needs `RscTitles` [U]).
- **The 1985 opener** [V local structure; I memory claims]: a barracks prologue cutscene mission, then training, then a first combat Intro
  with two helicopters: backing for "orders scene" and "helicopter ride-in" chapter openers (doc 35 rc08).

### 9.3 Reconciliation with doc 35

Doc 35 gives intro medians of 125 s (Resistance) against 87 s (1985) and a cutscene-node recipe of "25–35 shots, about 2.5 min"; this scan
gives 115 s and 56.5 s, and cutscene missions median 125 s with 21 shots (Resistance 27; p75 32.5). The gap is probably population or shot
definition [I]. Both docs should state them before feeding defaults; rc35 becomes a band (18–32 shots, 1.5–3.5 min).

## 10. Phased plan and acceptance tests

**Probes** (in-game missions with a vanilla observable; doc 32 phase 0): CP1 cinema-bar height per display style; CP2 `say` and lip sync
under `setAccTime 0.2`; CP3 weapon carry by behaviour; CP4 actor and prop intersection at close scales; CP5 the fog-range formula; CP6 map
inserts in CWR/CE intro mode; CP7 box tightness for trees and buildings (A/B); CP8 view distance on 1.99 and after a mid-mission options
change (the Cwr/Ce rule is read from source, §4.3); CP9 slot, follow-file and convoy spacing; CP10 subdivision emulation against the cache
(≤ 1 cm) and which grids players use; CP11 boat beaching; CP12 radio keys during an in-mission camera effect; CP13 `setPos` marks over
bridges and piers near sea level.

| Phase | Delivers | Acceptance tests |
| --- | --- | --- |
| DP0 Probes and terrain | CP1–CP13; `ofp-terrain` exact `SurfaceY`; subdivision-cache reader; WRP/P3D spatial index; §1.2 requests | **DAT1** known-value tests on synthetic grids (both triangles, diagonal, edges, −100 off the map, sea floor) plus overflow, NaN and truncated-cache adversarial inputs. **DAT2** a synthetic ridge between two clear keys trips DR01, and every computed fix passes |
| DP1 Offline planner | Vocabulary, scale solver, projection, composition, candidates, DR01–DR14, pacing; CA01, CA02, CA06, CA08, CA09; 2D storyboard; readiness report | **DAT3** no commit retargets ≥ 150°; a 120° pan splits into ≤ 45° segments; the aim model reproduces 2/(1+cosθ). **DAT4** identical request and seed give byte-identical sequences and SQS. **DAT5** a 30 s shot at 10 Hz, 5 subjects, 9 rays: checks under 16 ms p95 [U hardware] |
| DP2 Staging and live | Staging planner, gates, robustness contract; CA03–CA05, CA07, CA10–CA12; thumbnails, filmstrip, detectors | **DAT6 (headline)** from intent "establish the AO and the objective" plus 3 map picks, on each populated stock island at 10 seeds: a 25–40 s intro with 5–7 shots, zero clearance, framing and doc 32 errors or warnings on all three profiles; on Remastered every thumbnail passes the black and uniform-frame detectors and each primary subject's A/B diff lies inside its planned safe-frame box in ≥ 95% of shots (the rest flagged). **DAT7** `project()` matches calibration screenshots within 1% of frame width at 4:3 and 16:9. **DAT8** SAFE squad file, AWARE wedge and SAFE four-truck convoy fall inside predicted bands over 10 runs. **DAT9** AI-driven subjects over 10 filmstrips: no stalls or stuck cameras; ≥ 90% of AI shots framed, the rest on fallback |
| DP3 AI and fun | `core/make-cutscene`; Shuffle; "Like BI"; critique; Compose for qualified models | **DAT10** a 3–9B model, 30 seeds per archetype: 100% compiling, zero DR errors or warnings, zero model-typed coordinates, times, classes or FOVs. **DAT11** editing one key pins its shot; re-planning leaves pinned shots byte-identical, and an in-mission scene leaves every mission unit's presence, placement radius and start unchanged (doc 25 E9: clobbers = 0). **DAT12** skipping a generated section at every cue leaves campaign state equal to a full play, with no leaked input lock |
| DP4 Round-trip | Inferred ShotSpecs for captured and imported shots; DR parity on hand-made scenes; East presets from a primary source | **DAT13** a newcomer makes a CA01 intro and a CA08 ending without writing script and previews both on Remastered; moderated target ≤ 10 min [I] |

Tests are synthetic and redistributable (AGENTS.md): no official scene, island or cache bytes enter CI; island-based runs (DAT6, DAT8,
DAT9) are opt-in local tests behind an environment variable.

## Open questions

1. Rendering unknowns: the `CinemaBorder` bar height and so the vertical safe band (CP1); `say` and lip sync under slow motion (CP2);
   weapon carry of staged actors (CP3); close-scale intersection margins (CP4); map inserts in CWR/CE intro mode (CP6).
2. Checking unknowns: box tightness and soft-occluder factors (CP7); the fog-range formula in practice (CP5); view distance on 1.99
   and after a mid-mission options change (CP8; the Cwr/Ce rule is in source, §4.3); `setPos` seating on bridges near sea level (CP13);
   boat beaching (CP11).
3. Do predicted file, wedge and convoy spacings hold in game (CP9), and on 1.99, where CWR's drifted-Move re-arm may be missing?
4. Can emulation match the subdivision cache within 1 cm, and without either, should checks assume 6.25 m or the base grid (CP10)?
5. Harness flags in shipped binaries and the `setAccTime 0` freeze (doc 08; doc 32 open question 3); in-mission skip via radio keys (CP12).
6. House style: may a cutaway excuse an action-line crossing? Which taste bounds may a community archetype pack (doc 22) loosen?
7. East-side staging from a primary source (FM 100-2-1 located, not read); tilt usage in official scripts (unmeasured); the doc 35
   population reconciliation (§9.3).

## Verification notes

### Product review notes

Checked on 2026-09-27 against the owner direction (easy, correct, tactical, effective cutscenes), the AGENTS.md invariants (glass box,
weak models pick and write, human work kept, realism as defaults) and docs 25, 28, 31, 32, 33, 38 and 41. **Verdict [I]:** the flow is easy
and fun where it counts (intent cards, map picks, three takes at once, Shuffle, "Like BI", coverage, live thumbnails); every generated
element stays a doc 32 key, cue or clip with its `ShotSpec`, checks and provenance; no second runtime, compiler or timeline appears.

**Edits made in place.**

- *Tactics against protection (§5.3):* the bundle's CARELESS, UP and `stop` contradicted the AWARE wedge, prone overwatch and planned moves
  (TP02 by construction). Only protection is universal now; posture follows the recipe; the epilogue restores values read at scene start.
- *CA05 (§3, §4.5, §6.1, §6.4):* captive or invulnerable actors could never trip its contact gate, so every run would end on the timeout.
  Contact is staged by code or rides on a user-marked casualty; CA05 fits the 20 s in-mission budget; DR12 counts gates at their timeouts,
  and the §6.4 sample no longer overruns its own budget.
- *Human craft (§5.1, §5.3):* in-mission scenes no longer rewrite presence, placement radius or starts of the mission's own units, and
  units under a doc 31 module are filmed as the module runs them; DAT11 now tests the first.
- *Weak models (§8):* takes are judged by eye, so the user approves one and batch runs keep code's top take (doc 25 §7.3); callsigns come
  from the story bible; line text and critique go through doc 32's `screenplay.write` and `cine.critique` instead of new tools.
- *Doc 32 (§1.2, §6.1, §7):* per-shot `origin` and `pin` requested (doc 32 pins only sequences); dragging a template-backed key bakes first
  (doc 32 §5.1); the storyboard and tempo meter are doc 32 §3.3's; DR checks restating doc 32 lints or MC19 share one finding.
- *Ease and glass box (§7):* roles arrive pre-filled, so intent → takes is one click; takes differ in kind; a plain-language purpose line
  opens the inspector, linked to Standing Orders C1; later mission edits mark shots Stale instead of breaking them silently.
- *Doc 41 and AGENTS.md (§1.2, §3, §7):* mood tags, vistas, light, weather and the cue budget come from the Atmosphere Director; engine
  limits go to the engine-requests register.

**Still open.**

- *Names:* "Cutscene Director", doc 41's "Atmosphere Director", doc 33's Drill track "C. Director" and doc 32's "Director's view" crowd one
  word; clear the UI names through doc 02 §9 (doc 33 principle 9) before any string ships.
- *Drill:* doc 33's C1 lesson should become "intent → take → tweak → preview" on the Director once DP3 lands.
- *1.99-only authors* get sketches, never real frames, and DAT13 previews only on Remastered, so the headline test leaves them out.
- *§1.2 is not filed yet:* the design-gap index lists it as a candidate; file it once this doc is final.
- *Length:* about 700 lines against the ~550 target; the terrain facts of §4.3 and the AI facts of §5.2 could live in docs 07 and 31, with
  pointers here.

### Engine review notes (2026-09-27)

Camera model, projection and FOV, safe frame, choreography commands, timing and harness claims were re-read in `CWR@ffc61838b7` (the
camera files, `CameraHold.cpp/.hpp` and `Camera.cpp`, are byte-identical in `CE@b67bf3bd62`; the lens, clamp, near-plane, pillarbox and
`triSceneReady` logic match there at shifted lines) and against docs 07, 08 and 32. Corpus timing was re-run with our own local aggregate
scripts, de-duplicated by content.

**Confirmed [V].** Object targets aim at `CameraPosition()` with no offset: a soldier's animated `pilot` point, else `zamerny`; any other
object's `zamerny`, else its geometry-box centre, else its bounding centre, recomputed at load over the ODOL trailer value
(`Graphics/Rendering/Shape/ShapeLOD.cpp#L1477-L1494`). The retarget nlerp and its 2/(1+cosθ) profile. The 0.1 m clamp applies to camera
effects too (`World.cpp#L884-L899` then `#L1208-L1217`) and ignores objects. Lens factors, near plane, the Modern/Legacy/gameplay-active
pillarbox rules and forced `titleObj`/`cutObj` bars. Terrain tiers, the RAM-picked first-boot preset and per-mission subdivision with the
cache; the cache aggregates re-run to the same figures (exact land cells 5.6–33.5%, road p99 2.73–3.13 m, open p99 5.43–7.57 m, forest 0).
Heights resolved at the call; view-distance derivation, per-load reset and no getter. The follow-in-ID-order pilot, the 22% LIMITED cap,
FORM snapping and `unitReady`; `moveTo`, `enableAI`, `animationState`, `forceSpeed` and `limitSpeed` appear in neither the registration
tables nor the `do`/`command` macros. Space/Esc skip, `exit.sqs` only on the mission end path, the World-lifetime input-lock counter.
Harness `screenshot`/`eval`/`exec`, the `tri*` gate and the always-registered `triGet*` getters. Corpus: timed scripts with ≥ 4 cuts give
48 scripts and 509 shots, empirical median 5.00 s, mean 6.78 s, fit μ 1.672, σ 0.704, 4.3% under 2 s, 10.8% over 12 s; FOV 0.7 in 1,058
of 2,434 settings; `camSetPos` height median 1.60 m (n = 2,152); 885 moving commits with the §9.1 kind counts.

**Fixed in place.**

- §4.1: "one lens per commit" became one *target* FOV reached linearly; added zoom mechanics (magnification accelerates as FOV shrinks),
  the per-frame θ, and the jump when a target is committed before the previous retarget's deadline.
- §4.2: the manual camera's clamp is cited (`camSetFov` clamps nothing); the safe frame now states the `showCinemaBorder` gate (it
  removes letterbox and pillarbox together, and is reset to on by every mission and cutscene display), the full-width letterbox, which
  displays run in intro mode, and that `titleObj`/`cutObj` force bars even under Legacy. TL;DR synced.
- §4.3, CA04, DR01: "eyes keep ≥ 5.25 m AGL over water" contradicted the doc's own exact keys, since h is taken from the live sea surface;
  keys now need 0.8 m, and the 5.25 m tide-plus-wave allowance applies only to absolute-height segment and sight-line checks.
- §4.3: `camSetRelPos` keys are target-relative, not AGL; draw distance adds the Cwr/Ce Intel `viewDistance` and the player's "respect
  mission view distance" option (default on), the 100 m object floor and the 500 m shadow cap; CP8 (§10, open question 2) narrowed.
- §4.4: the fitted log-normal's median is e^1.67 ≈ 5.3 s; 5.0 s is the empirical median. The "multi-shot" population is now defined.
- §5.2: the follow chain runs per subgroup, skips cautious units and is headed by the subgroup leader; its 0.5 s term uses the followed
  unit's speed; `setPos` on non-AI entities takes h as an absolute height (`GameStateExtGrp.cpp#L1731-L1756`).
- §5.3: move budgets use the LIMITED cap (≤ 0.22 × the class's config maximum outside COMBAT), not the config speed.
- §6.3: `triSceneReady` counts frames over the process lifetime (`Engine.hpp#L310, #L328`), so it reads OK at once and thumbnails add
  settle frames; `triScreenshot` writes PNG and BMP; the staging recipe cites doc 08 §4.2; `triSetPillarboxBarsEnabled` previews Legacy.
- CA10: the array form of `say` on 1.99 is marked (unverified), as in doc 32 §2.5.

**Residual concerns.**

- CP1 stays open: the `CinemaBorder` model was not read, so the vertical safe band (inner ~70%) is a placeholder.
- That `pilot` is the eye is [I] from the selection name; head-aimed composition should be calibrated by DAT7 before it drives thirds.
- The 0.8 m water margin, geometric zoom sampling and the ≤ 45° split are [I] on [V] mechanics.
- Population B figures (intro lengths, fades, music, line timing, 18% event waits) and the montage example were not re-run in this pass.
- 1.99's camera, lens factors and view-distance behaviour remain (unverified) (doc 32 §2.3; CP8).
- Scripts are simulated before the camera effect each frame (`World.cpp#L871-L886`), so a cue on a deadline frame should continue a
  sampled move without a hold; frame-exact continuity is (unverified) until a filmstrip measures it.

## Sources

**Engine.** `CWR:` camera, display and title code (`World/Scene/Camera/`, `World/World*.cpp`, `World/Scene/`, `Game/TitEffects.cpp`,
`UI/Settings/`), terrain (`World/Terrain/`, `World/Simulation/`), AI and staging (`AI/`, `World/Entities/`), commands, UI and harness
(`Game/Commands/`, `Dev/Harness/`, `UI/DisplayUIMenus.cpp`, `Input/`), with files and line ranges cited inline; `CE:` re-checks as in the header.

**Repository.** Docs 07 §6–§7; 08 §2.4–§2.5, §6; 18 §8.2; 19 C16; 22 §2.1; 23; 25 §5.1, §6, §7, §9, E9; 26; 28 FP43; 31 §2, §4.6, §6;
32; 33; 35 §3.2–§3.5, rc08, rc20, rc35, rc64; 38 §3; `docs/research/data/cwa199-observed-commands.csv`; `AGENTS.md`.

**Local corpus (owner's install; read-only; aggregates and names only).** Official and Remastered camera scripts, Intro sections,
stringtables, `CfgVehicles`, `CfgWorlds` and `CfgMovesMC` values, the stock camera and death scripts, the five stock WRPs, Remastered
subdivision caches.

**Research.** He, Cohen, Salesin, "The Virtual Cinematographer", SIGGRAPH 1996 <https://grail.cs.washington.edu/wp-content/uploads/2015/08/he-1996-tvc.pdf>;
Christianson et al., "Declarative Camera Control for Automatic Cinematography", AAAI-96
<https://grail.cs.washington.edu/wp-content/uploads/2015/08/dccl-aaai96.pdf>; Lino, Christie, "Intuitive and Efficient Camera Control with
the Toric Space", ACM TOG 2015 <https://cinematography.inria.fr/files/2015/03/toric-space-tog-final.pdf>; Christie, Olivier, Normand, "Camera
Control in Computer Graphics", CGF 27(8), 2008 <https://people.irisa.fr/Marc.Christie/Publications/2008/CON08/870.pdf>; Galvane, Ronfard, Lino,
Christie, "Continuity Editing for 3D Animation", AAAI 2015 <https://ojs.aaai.org/index.php/AAAI/article/view/9288>; Leake, Davis, Truong,
Agrawala, "Computational Video Editing for Dialogue-Driven Scenes", ACM TOG 36(4), 2017
<https://graphics.stanford.edu/papers/roughcut/files/roughcut-small.pdf>; Cutting, DeLong, Nothelfer, "Attention and the Evolution of
Hollywood Film", 2010 <https://jordandelong.com/pubs/2010/AttentionEvolution.pdf>; Duan et al., "PACE", arXiv 2609.19853
<https://arxiv.org/abs/2609.19853>. Background: <https://arxiv.org/abs/1712.04216>, <https://arxiv.org/abs/2506.00974>.

**Tools.** Unity Cinemachine 3.1 manual (Rotation Composer, Deoccluder, Decollider, Shot Quality Evaluator, ClearShot, Target Group, Group
Framing, Spline Dolly, Sequencer Camera, transitions) <https://docs.unity3d.com/Packages/com.unity.cinemachine@3.1/manual/>; Unreal camera
rigs, cinematic cameras, Camera Cut track <https://dev.epicgames.com/documentation/en-us/unreal-engine/camera-jibs-and-dollies-in-unreal-engine>;
BIKI `BIS_fnc_establishingShot`, `BIS_fnc_infoText` (search snippets) and "Arma 3 Mission Presentation" (wikitext); Faguss, Cutscene Maker manual
<https://ofp-faguss.com/files/flashpoint_cutscene_maker.pdf>.

**Film grammar and games.** Wikipedia "180-degree rule", "30-degree rule", "Lead room", "Post-classical editing", "Machinima", "Red vs.
Blue", "Landing zone", "Procedure word" (fetched 2026-09-27); Halopedia "Machinima"; Nesky, GDC 2014 <https://gdcvault.com/play/1020460/50-Camera>
and a third-party summary <https://videohighlight.com/v/C7307qRmlMI>.

**Doctrine.** FM 7-8 ch. 2 <https://550cord.com/infantry-rifle-platoon-squad-fm-7-8/fm-7-8-chapter-2-operations/>; ATP 3-21.8 (2024)
<https://infantrydrills.com/manuals/fm-atp-3-21-8-infantry-rifle-platoon-squad-2024/>; FM 3-21.71 ch. 3, FM 4-01.011 App. C, FM 55-30 ch. 5,
FM 90-4 App. E <https://www.globalsecurity.org/military/library/policy/army/fm/>; FM 21-18
<https://archive.org/stream/milmanual-fm-21-18-foot-marches/fm_21-18_foot_marches_djvu.txt>; secondary Soviet doctrine
<https://balagan.info/soviet-order-of-battle-and-doctrine-in-the-cold-war>.

**Community and players.** aligrant <https://www.aligrant.com/web/games/ofp/editing/cams>; PMC Editing Wiki
<https://pmc.editing.wiki/doku.php?id=arma%3Amissions%3Acutscene_tutorial>; Steam CWA thread (2017-12-30)
<https://steamcommunity.com/app/65790/discussions/0/1621724915808106846/>; GameSpot review (search snippet)
<https://www.gamespot.com/reviews/operation-flashpoint-cold-war-crisis-review/1900-2810242/>.
