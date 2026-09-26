# Field Manual and live tutorials

Research doc 33 for `ofp-editor`. Audience: contributors and LLM coding agents reading only this file. Status: **proposal-only**.
Question answered: how the editor explains every concept, field and rule to the user *and* to its AI in the same verified words,
and how it teaches mission making by doing. "Field Manual" and "boot camp" are **working names**; both are also Arma 3 feature
names, so the shipped names are an open decision (§2 item 9, open question 1).

**Legend.** **[V]** verified in pinned source or on a fetched page (cited). **[I]** inferred or proposed by us. **[U]** unknown;
needs a probe, a fetch or a playtest. Repository docs are cited as "doc NN §x".
**Citations.** `CWR:` = `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/`; `CE:` = `ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/`.
Line numbers are CWR's. Of the cited files, `ArcadeTemplate.cpp`, `UIArcadeWaypoint.cpp`, `InGameUIDrawCursor.cpp`,
`UIMapExtDisplay.cpp` and `VehicleAI.cpp` differ in CE (same logic at shifted lines, e.g. `SetAdvancedMode` at CE
`UI/Map/UIMapExtDisplay.cpp#L352-L397`); the other cited engine files were SHA-256-identical on 2026-09-27. Re-read in this session:
`Detector.cpp#L1259-L1297`, `AIArcade.cpp#L398-L433`, `AIArcadeActions.inc#L1774-L1810`, `ArcadeTemplate.cpp#L446-L473, #L1040-L1055`,
`UIArcadeWaypoint.cpp#L72-L105`, `GameStateExt.cpp#L938, #L1236`.
**Companions.** Doc 03 (every dialog field), 04 (data model), 09 (pain points), 21 §10–§11 (grounded teaching, academy, persona), 22
(plugin tiers), 23 (language service), 30 §4.4 (knowledge tools and cards), 31 (no-code ladder, including the editor's own modules),
32 (cinematics) and 34 §3 (learning ideas le01–le11: tours, tip budget, Rosetta rows). Docs 30–32 were written after this doc's
first draft; §1.4, §5.4, §6.1 and open question 10 now point to them. This doc does not repeat doc 03's field tables.
**Hygiene:** every explanation here is our own, written from engine code; community pages are cited only as evidence of confusion, with at most a short attributed quote (doc 28 rules).

## TL;DR

- **The problem is invisible rules plus folk knowledge.** Game Logic, sync, Countdown vs Timeout, "Whole group / Not present", Switch,
  Guarded by and Info age follow rules nobody can see, and community answers mix in ArmA-era tutorials that spread myths (§1).
- **One registry feeds every surface:** tooltip and hover card, F1 page, manual, lint links, tutorial steps, the `explain_concept`
  reply and an Agent Skills `references/<id>.md`. User and model read the same words (§3).
- **Every engine claim carries evidence:** pinned lines plus a [V]/[I]/[U] tag. Only [V] facts are shown as rules; the rest read
  "likely, unconfirmed" until an in-game probe settles them (§3, §8).
- **Help explains this object, not only the concept.** Overlays (CYCLE loop arrow, SWITCH jump, 100 m auto-join ring, "who waits for
  whom" sync view, END-group counter) call the same ported rules as the validators (§4.3).
- **Demos show the mechanism:** map-renderer animations with scrubbing and "predict, then play", each behavioural one paired with a
  probe mission; "Show me in game" runs a throwaway sandbox through Preview (§4.6–§4.7).
- **Boot camp teaches by doing:** a sandbox, one new idea per step, introduce → develop → twist → master, steps that complete only
  when a validator predicate holds, a hint ladder, and skip / test-out / resume everywhere (§5).
- **The instructor sounds like 1985 but never states a fact itself;** code renders every fact. No streaks, no nagging, no "Great job!" (§5.3).
- **The AI picks entries; it never writes semantics.** `list_concepts`, `explain_concept` and `explain_instance` return registry
  content; later-game terms get "not in this engine" from a lookup; tutor mode hints and never does the step (§6).
- **Localised and accessible from the first release:** English, Czech, Polish, Russian and German (`en`, `cs`, `pl`, `ru`, `de`) with
  per-field staleness, WCAG 1.4.13 cards, keyboard entry, reduced motion, text alternatives for every demo (§7).
- **Headline acceptance test:** a newcomer builds a working patrol, a trigger and a named Game Logic anchor used by a script in 15
  minutes of active building (Track A runs about 55 minutes with demos and Previews). Also: 100% coverage of UI anchors, and zero invented engine claims from a small model on a trap benchmark (§9).

## 1. The problem: cryptic concepts and folk knowledge

### 1.1 Why the original editor felt cryptic

- **Labels without explanations.** Dialog labels are localised string ids from game data (e.g. `LocalizeString(IDS_AC_AND + …)`,
  `CWR:UI/Map/UIArcadeWaypoint.cpp#L83`) [V]. The engine can draw a per-control `tooltip` (`CWR:UI/Controls/UIControlsBase.cpp#L91-L135`)
  [V], but the editor's resource config is not in the repo, so whether any editor control used one is [U].
- **Invisible rules.** Auto-join within 100 m, formation snap, CYCLE choosing its target by position, where SWITCH jumps, the END AND
  rule, "no groups ⇒ no side brain": none of these was ever drawn on the map.
- **Overloaded words.** `this` means four things; "Countdown"/"Timeout" are near-synonyms; "Empty" means "no crew"; combat modes are
  colours.
- **Knowledge from later games.** Widely cited "OFP" tutorials are ArmA-era (OFPEC Triggers id=28, Units id=16, Waypoints id=17/221)
  [V, re-fetched], so later rules leak into CWA advice. The 2002 editor "comes with really lousy documentation" (COMBATSIM,
  Pawelek) [V]; doc 09 P8.
- **Errors arrive late and opaque:** a modal box after OK, a Preview button that silently vanishes, a hostile script-error box (doc 09 P2, P7) [V].

### 1.2 The top confusions, ranked

Ranked by the number of independent community sources and the years they span; the counts were not re-verified in the fact-check
pass [I]. Engine truth is [V] unless marked. Paths are relative to `CWR:`.

| # | Concept | What people expect | What the engine does | Engine cite | Community signal |
| --- | --- | --- | --- | --- | --- |
| 1 | Trigger won't fire | "I placed it; it should work" | New trigger: Activation None, Once, condition `this`. With None the area result stays false, so `this` never fires; a custom condition such as `true` can | `AI/ArcadeTemplate.cpp#L446-L473`; `World/Detection/Detector.cpp#L861-L868, #L1259-L1265` | COMBATSIM 2002; BI forums 2019; Steam 2016, 2024 |
| 2 | Synchronise (F5) | "The trigger starts the group" | A rendezvous barrier: the group walks to the waypoint, then waits there for trigger and partners. Several syncs = AND. Release a group with two waypoints | `AI/AIArcade.cpp#L811-L861`; `AI/AICenterImpl.cpp#L786-L807` | BI forums 2004, 2019; Steam 2017 |
| 3 | Game Logic | "What is it for?" | An invisible unit on side Logic: named anchor, init-code holder, owner of AND/OR gate waypoints. No sensors, no hidden powers | `World/Entities/Vehicles/InvisibleVeh.hpp#L20-L40`; `UI/Map/UIArcadeWaypoint.cpp#L74-L105`; `AI/AICenterImpl.cpp#L1596-L1600` | BI forums 2002; 2009 (Arma 2) |
| 4 | Whole group + Not present | "Fires when the group is gone" | Means "not all inside": fires once one member is outside. "Any group member + Not present" = none inside | `World/Detection/Detector.cpp#L1047-L1095, #L1179-L1217` | aligrant; PMC wiki |
| 5 | Endless waypoints | "Stuck at HOLD" | HOLD, GUARD, SUPPORT never complete. A SWITCH trigger jumps the group to the waypoint *after* the synced one, even backwards | `AI/AIArcadeActions.inc#L389-L508`; `World/Detection/Detector.cpp#L1339-L1383` | BI forums 2005 |
| 6 | Transport | "The helicopter left early" | LOAD does not wait. A GET IN synced over a link between exactly two groups makes the transport wait for boarding. GET OUT / UNLOAD / TR UNLOAD differ in whose soldiers leave | `AI/AIArcade.cpp#L1515-L1787`; `AI/AIArcadeActions.inc#L103-L256` | BI forums 2002 |
| 7 | Waypoint timing | "Combat settings apply at the waypoint" | Settings apply when the waypoint becomes current (on the way). On Activation runs after arrival, condition, syncs, timeout. Player-led groups still complete waypoints | `AI/AIArcade.cpp#L270-L306, #L579-L600, #L811-L909` | OFPEC 221 (ArmA-era) |
| 8 | CYCLE | "Loops to the first / never the previous" | Nearest earlier waypoint, including the start position and the previous one; ties go to the earliest | `AI/AIArcade.cpp#L400-L433` | OFPEC 17/221 myth; aligrant |
| 9 | Auto-join | "Why does my sniper follow them?" | A new unit joins the same-side group whose leader is nearest within 100 m | `AI/ArcadeTemplateFind.cpp#L412-L471` | aligrant; OFPEC 16 |
| 10 | Player / Playable / MP | "Playable = team switch in SP" | Playable skips presence; an unfilled AI-disabled slot is not created; MP creates every side centre [V]. Respawn and `description.ext` rules are community lore [I] | `AI/AICenterImpl.cpp#L1525-L1538`; `AI/AICenterStats.cpp#L1328-L1349` | aligrant; OFPEC MP list |
| 11 | `this` | "The thing I'm editing" | Unit init: the unit (crewed vehicle: the vehicle). Trigger condition: a Boolean. Waypoint: the leader's soldier. Trigger On Activation: stale | `World/WorldInit.cpp#L622-L627`; `World/Detection/Detector.cpp#L1331-L1337`; `AI/AIArcade.cpp#L311-L333` | COMBATSIM 2002; Steam 2016 |
| 12 | Presence | "The condition can read init variables" | Probability roll, then condition, once, before any init line; player and playable units skip both | `AI/AICenterImpl.cpp#L1525-L1538`; `World/WorldInit.cpp#L563-L632` | OFPEC 38, 16 |
| 13 | Countdown vs Timeout | "Three timers" | One random delay Gauss(min, mid, max); max < 0.1 s = instant; Timeout cancels if the condition drops. Label order [I] | `World/Detection/Detector.cpp#L1267-L1296`; `engine/Random/randomGen.cpp#L156-L171` | PMC wiki; OFPEC 28 |
| 14 | Guarded by / GUARD | "The trigger runs my code" | A pin only; no trigger object. The guard pool re-dispatches every 25–35 s. No "Seized by" in CWA | `AI/AICenterImpl.cpp#L1246-L1302, #L325-L516` | OFPEC 28; PMC wiki |
| 15 | Combat colours | Jargon | Two axes. Hold fire: Blue/Green/White; keep formation: Blue/Green/Yellow. Once the group is disclosed, Green → Yellow and White → Red | `AI/AIUnitImpl.cpp#L2108-L2143`; `AI/AIGroup.cpp#L759-L826` | OFPEC forum; aligrant |
| 16 | Empty side, In cargo | "In cargo boards the truck" | "Empty" = no crew, no group. In cargo boards only a crewed vehicle of the soldier's own group | `AI/ArcadeTemplateFind.cpp#L419-L426`; `AI/AICenterImpl.cpp#L1570-L1595` | OFPEC 38; COMBATSIM |
| 17 | Hidden waypoints | "Needs a description" | New waypoints default to Show: Never [V]; the in-world marker follows the HUD difficulty setting [I] | `AI/ArcadeTemplate.cpp#L1052`; `UI/Map/UIMapMain.cpp#L385-L458` | Steam 2018 |
| 18 | Show IDs | "The button is broken" | Advanced mode only; labels appear only past a zoom threshold | `UI/Map/UIMapExtDisplay.cpp#L455-L464`; `UI/Map/UIMap.cpp#L1696-L1718` | OFPEC 38 |
| 19 | Easy/Advanced, sections | "Easy missions differ" | Easy only hides things. CWR defaults to Advanced; retail default [U] | `UI/Map/UIMapExtDisplay.cpp#L63-L97, #L429-L501` | OFPEC 38; aligrant |
| 20 | Placement radius | "Even scatter" | Lowest terrain cost among ≤ 100 samples; marker starts give each spot 1/(n+1) odds | `AI/AICenterImpl.cpp#L628-L691, #L960-L984` | OFPEC 221; COMBATSIM |
| 21 | Info age | "Unknown = not known" | Seeds the player side's knowledge of other units; Unknown = a 2-hour-old report (= 120 min); no effect on triggers (computed in `CreateSensor`, then discarded) | `AI/AICenterImpl.cpp#L1163-L1199, #L1344-L1375`; `AI/AICenter.cpp#L82` | OFPEC 38, 16 |

**Also frequently hit [V]:** Health 0 spawns alive at 0.97 damage, not a wreck (`AI/AICenterImpl.cpp#L853`). Locked does not stop
enemy AI (`AI/AIUnitImpl.cpp#L223-L300`). Several END *k* triggers act as AND and any Lose beats every END (`World/WorldImpl.cpp#L541-L657`).
Radio triggers ignore timers and the text `null` hides them (`UI/Map/UIMapDisplayBriefing.cpp#L737-L767`). In SP, "Detected by East"
never fires when East has no placed groups (`World/Detection/Detector.cpp#L776-L790`). A named vehicle also creates `name`+`d`/`c`/`g`
crew variables (`AI/AICenterImpl.cpp#L1631-L1703`; retail 1.99 [U]). Merge renames clashing names but not the code using them
(`AI/ArcadeTemplateFind.cpp#L1086-L1310`). Trigger areas are 2D columns (`World/Detection/Detector.cpp#L792-L852`). Forecast weather
arrives within 30 minutes (`World/WorldSetup.cpp#L1254-L1283`). Markers are visible to every side (`UI/Map/UIMapMain.cpp#L299-L329`).

### 1.3 Myths the manual must correct

Each gets a "Folk wisdom vs engine" box citing §1.2's lines. "CYCLE skips the previous waypoint" (ArmA-era OFPEC; CWR excludes
nothing). "Switch jumps *to* the synced waypoint" (it goes to the one after). "Game Logic isn't needed" (a 2009 Arma 2 thread; AND/OR
logic waypoints appear to be the only no-code OR between triggers [I]). "A waypoint needs a description to show." "Guarded-by
triggers run their On Activation." "Seized by exists" (ArmA 1.05+, PMC wiki [V]). "Info age Unknown means unknown." "Placement radius
is an even scatter." "The player's waypoints are only guidance." "Health 0 places a wreck." "Locked stops the enemy." "The whole group
shares one combat mode" (members can differ, `AI/AIGroupCmd.cpp#L613-L636`). "Timeout is the default" (true from ArmA 1.05; in CWR a
new trigger is index 0, Countdown, `AI/ArcadeTemplate.cpp#L459`).

### 1.4 Dialect traps: later-game terms that do not exist here

The engine has 17 waypoint types plus AND/OR. There are no Dismiss, Get in nearest or Loiter waypoints and no Seized by or
Not-detected-by activations (`AI/Path/ArcadeWaypoint.hpp#L61-L86, #L206-L257`) [V]. There are no modules, no `thisTrigger` and no
per-unit description (`AI/ArcadeTemplate.hpp#L19-L61`) [V], and sides are WEST/EAST/GUER/CIV, not BLUFOR/OPFOR. Each such term gets a
`dialect.*` entry that answers "not in this engine" and points to the CWA equivalent, which is how §6 stops weak models improvising.
"Module" needs two answers, because doc 31 proposes modules *in this editor*: the game engine has none, and the editor's modules
compile to ordinary triggers, waypoints, markers, Game Logics and scripts (doc 31 §4.2 `Emit`; doc 34 §3.3 Rosetta row). The entry must say both, or a model will say either "no
modules" to a user looking at the module palette or "CWA has modules" [I].

## 2. Principles

1. **One source for human and model.** One entry feeds every surface, as Blender and Godot generate tooltips from the declaration
   [V]. Computable facts (hotkey, sqm key, legal values, limits such as the 12-seat cap `CWR:AI/Path/AITypes.hpp#L31`, defaults,
   minimum version) are appended by code, never typed by hand.
2. **Verified semantics, visible evidence.** Every engine claim cites pinned lines and carries a tag. [V] facts read as rules;
   [I]/[U] read "likely, unconfirmed" and name the probe that will settle them. Nothing rests on folklore alone.
3. **Explain the instance.** "This AND waypoint still waits on trigger `Alarm` (not fired)" beats a definition (Victor, *Learnable
   Programming*: "show the data" [V]). This is the AGENTS.md glass-box rule, applied to hand-made content too.
4. **Learn by doing, one idea at a time.** One new concept per step (Portal commentary [V]); introduce → develop → twist → master
   (Hayashida's kishōtenketsu [V]); worked examples fade into free problems (Sweller; Renkl & Atkinson [V]).
5. **Pull, don't push; never patronise.** No start-up tour (NN/g [V]). Tips fire only on computed facts, never repeat once dismissed
   and never block (the Clippy lesson [V]). Everything is skippable and experts can test out (expertise reversal [V]). Feedback is
   about the task, never generic praise (Hattie & Timperley [V]).
6. **Fun that informs.** Twists, "predict, then play", Preview moments, achievements that describe competence. No streaks,
   loss-aversion nags or leaderboards: contingent rewards undermine free-choice motivation, while positive feedback enhanced it
   (Deci, Koestner & Ryan 1999 [V]), so achievements must read as information about competence, never as a prize; doc 21 §12.1
   forbids uploads.
7. **Localisable and accessible from day one** (§7).
8. **Product-scoped; untrusted content stays data.** Only product flows; community packs are T0 data (doc 22 §2.1); mission and
   pack text never instructs the agent (AGENTS.md).
9. **Original words and names.** Never paste Bohemia manual or wiki text or community tutorials. Doc 02 §9 records Bohemia's rule to
   "prefer original names", and "Field Manual" (CfgHints) and "Bootcamp" are Arma 3 names [V]; clear distinct era names through that
   checklist before any UI string is written.
10. **Anchor in the task, support recovery.** Minimalist instruction: action first, organised by the user's task, with error
    recognition and recovery built in, and every entry readable on its own in any order (van der Meij & Carroll 1995 [V]). Entries
    are also indexed by task ("I want a patrol / an alarm / a pickup / an ending"), and gotchas read as symptom → cause → fix.

## 3. The concept registry (proposal-only)

### 3.1 What an entry holds

| Field | Purpose | Surfaces |
| --- | --- | --- |
| `id` | Stable, dotted, lowercase (`waypoint.cycle`, `trigger.countdown-vs-timeout`) | All; also the lint and tutorial link key |
| `labels` | Original UI label (resolved at runtime from the user's game locale), plain names, later-game aliases; `asks`: 1–3 symptom questions in the user's words ("Why does my trigger never fire?") | Search, glossary, card title, page opener, symptom matching |
| `card` | `what` (one literal line, verb-first), `when` (one line), top `gotcha`. The analogy (`picture`, the seed entries' "In one sentence") is never the header: it opens the manual page, always followed by the literal rule | Tooltip header, hover card |
| `body` | Why, when not to, gotchas (symptom → cause → fix), a tiny worked example, a "folk wisdom vs engine" box | Manual page, `explain_concept(Full)` |
| `facts` | Engine semantics: text + grounding (citations, evidence, probe) + profiles | "Engine truth" section, AI replies |
| `dialect` | Notes for CWA 1.99 / CWR / CE / later Bohemia games | Badges, "not in this engine" answers |
| `related`, `anchors`, `lints` | Related ids; the UI it explains (dialog fields, modes, entity kinds, waypoint and trigger types, commands, overlays); lint ids that link here | "See also", F1 routing, coverage CI, findings panel, readiness coach (doc 21 §11.1) |
| `demo`, `exercise` | Map-animation scene and/or in-game demo mission plus its probe; tutorial step for "Try it", each step split into an action and an expected observation (hidden until the user predicts), with at least one step checkable in the editor without Preview | Manual, card mini-demo, card button |

### 3.2 Type sketch

Crate and placement are open (open question 3). The sketch follows AGENTS.md: newtypes, enums instead of flags, `Option` instead
of sentinels, private fields with checked constructors.

```rust
/// Stable concept id such as `waypoint.cycle`. A newtype, so a concept id cannot be passed where a lint id is expected.
pub struct ConceptId(Box<str>);
pub struct LintId(Box<str>);   // owned by the linter (doc 23 §13.4 `code`)
pub struct ProbeId(Box<str>);  // an in-game probe mission run through the Preview harness

/// Pinned upstream sources. Adding a pin adds a variant and forces CI to re-verify every citation.
pub enum Pin { Cwr /* ffc61838b7 */, CwrCe /* b67bf3bd62 */ }
pub struct Citation { pin: Pin, path: Box<str>, lines: LineRange } // LineRange::new rejects 0 and first > last

/// Evidence as types: a [V] fact cannot lack a citation, an [I]/[U] fact cannot lack a probe.
pub enum Grounding {
    Verified { cites: NonEmpty<Citation> },
    Inferred { cites: NonEmpty<Citation>, probe: ProbeId },
    Unverified { probe: ProbeId },
}
pub struct EngineFact { text: TextKey, grounding: Grounding, profiles: ProfileSet /* Cwa199 | Cwr | Ce */ }
pub struct DialectNote { dialect: Dialect /* Cwa199 | Cwr | Ce | LaterBohemia */, text: TextKey }

/// What an entry explains. Field ids are generated from the dialog definitions, so a stale anchor fails to parse.
pub enum UiAnchor {
    Field { dialog: DialogId, field: FieldId }, Mode(EditorMode), Entity(EntityKind), WaypointType(WaypointType),
    Activation(Activation), TriggerType(TriggerType), Lint(LintId), Command(CommandName), Overlay(OverlayKind),
}
/// A behavioural animation re-implements engine behaviour and can drift from it, so it must name its probe.
pub enum Demo {
    Static { scene: DemoSceneId },
    Behavioural { scene: DemoSceneId, probe: ProbeId },
    InGame { mission: DemoMissionId, probe: ProbeId },
}
pub struct ConceptEntry {
    id: ConceptId, kind: ConceptKind, labels: Labels, card: Card, body: Body,
    facts: Vec<EngineFact>, dialect: Vec<DialectNote>, related: Vec<ConceptId>, anchors: Vec<UiAnchor>,
    lints: Vec<LintId>, demo: Option<Demo>, exercise: Option<StepRef>,
    revision: FieldHashes, // source hash per field; drives translation staleness (§7)
}
```

### 3.3 Storage: a standard Agent Skills skill

- **Layout.** `skills/field-manual/SKILL.md` (index) plus `references/<id>.md` (one entry per file: YAML front matter and a Markdown
  body); translations in `locales/<lang>/<id>.md` (§7). The skill meets the Agent Skills spec: `name` matches the directory,
  `description` ≤ 1024 characters, SKILL.md under 500 lines and about 5000 tokens, references one level deep [V]. So it is portable.
- **One direction of generation.** The authored Markdown is the source. A build step (`xtask` or `build.rs`, open question 3)
  parses it into typed `ConceptEntry` values and fails on schema errors. SKILL.md's index table (id, title, `what`) is generated;
  CI checks the committed copy matches.
- **Parser rules.** The same parser reads community packs, so it follows AGENTS.md parser rules: pure, size-capped (entry ≤ 32 KiB,
  front matter ≤ 8 KiB [I: proposed]), permissive on unknown keys (kept and flagged), strict on structure, no links or includes.
- **The primer stays small.** `skills/mission-primer` keeps routing only; its `reference.card` lookup resolves into this registry,
  so primer and manual cannot disagree.

### 3.4 Example entry (abridged)

```markdown
---
id: entity.game-logic
kind: entity
labels: { original: ui:unit.side.logic, plain: ["invisible helper", "logic unit"], later: ["module"] }
card:
  what: "Places an invisible unit with a name, an init line and waypoints that never moves, sees or fights."
  when: "Use as a named point, a home for init code, or an AND/OR gate between triggers."
  gotcha: "No hidden powers. Put a gate's output sync on the NEXT logic waypoint."
anchors: [field:unit.side, entity:logic, waypoint:and, waypoint:or]
related: [waypoint.and-or, sync.rendezvous, trigger.activation.side]
lints: [logic.output-sync-on-gate]
demo: { behavioural: { scene: demo.logic-or-gate, probe: probe.logic-gate-release } }
exercise: bootcamp.a6#anchor
facts:
  - { text: fact.logic.only-and-or, verified: ["CWR:UI/Map/UIArcadeWaypoint.cpp#L74-L105"] }
  - { text: fact.logic.no-sensor, verified: ["CWR:AI/AICenterImpl.cpp#L1596-L1600"] }
  - { text: fact.logic.teleports-and-marks-sync, verified: ["CWR:AI/AIArcadeActions.inc#L1774-L1810"] }
  - { text: fact.logic.counted-by-anybody-present, inferred: ["CWR:World/WorldImpl.cpp#L495-L498"], probe: probe.logic-in-anybody-trigger }
---
## Folk wisdom vs engine
"Logics are useless" came from a later game. Here they appear to be the only no-code way to OR two triggers [I].
```

### 3.5 Seed set (about 70 entries, in priority order)

§1.2's rows and the "also frequently hit" list (`trigger.default-inert`, `sync.rendezvous`, `entity.game-logic`, `waypoint.and-or`,
`trigger.bound.group-vs-member`, `trigger.type.switch`, `waypoint.lifecycle`, `waypoint.cycle`, `group.auto-join`, `script.this`, …);
every field in doc 03 §4.4–§4.10 (including derived crew ranks, FORM/NONE/CARGO/FLY placement, lock, health/fuel/ammo, azimuth,
name and crew names); the 17 waypoint types, trigger activations and types; the mission-start timeline (`World/WorldInit.cpp#L539-L706`);
editor features (modes F1–F6, Easy/Advanced, Show IDs, Merge, Save/Export, the Preview gate `IsConsistent`
`UI/Map/UIMapExtDisplay.cpp#L411-L426`, sections, the `__cur_sp` mission name, doc 09 P11); briefing, endings, campaigns (docs 18/19)
and MP basics; and the `dialect.*` entries of §1.4.

## 4. UI surfaces

### 4.1 Two disclosure levels

Nielsen advises at most two levels [V], so the hover card *is* the tooltip, growing in place, and the manual page is the only second level.

| Level | Opens by | Content | Budget |
| --- | --- | --- | --- |
| Card header | Hover or keyboard focus | `what` plus code-appended facts (hotkey, sqm key, default) | 1 line, measured in rendered width (§7) |
| Card body | Dwell (~800 ms, tune in playtests [I]), Space on focus, or a click on the header | `when`, top gotcha, an **instance line**, a 3–6 s mini-demo shown as a still keyframe that plays once on request and never loops (WCAG 2.2.2 requires a pause or stop control for motion that starts by itself, lasts over 5 s and sits beside other content [V]), "More", "Try it" | ≤ 3 lines + demo |
| Manual page | F1, "More", Alt+click, right-click "What is this?" | Full entry: body, engine truth with tags, dialect notes, related, demo | Fixed section order, concrete before abstract: question, picture, tiny example, when (and when not), gotchas and myths, Try it, then engine truth (collapsed, with tags and citations), dialect notes, related |

Cards meet WCAG 2.1 SC 1.4.13: dismissible (Esc), hoverable, persistent [V]; they are non-modal. Essential constraints never live
*only* in a card: the 12-seat cap, per-side group slots and why Preview is hidden also appear inline and in validator messages (NN/g
tooltip guidelines [V]).

### 4.2 One "What is this?" gesture, and dialog references

F1 opens the entry for the focused field; Alt+click does it for any map object, waypoint, trigger, marker, sync line or finding;
right-click offers "What is this?" (Factoriopedia and Blender precedents [V]). Pages keep back/forward history. Each dialog also has
a "?" opening a **dialog reference**: every field with its one-line `what`, for scanning without hovering each control.

### 4.3 Instance explanations and map overlays

Overlays call the *same functions* as the validators and lints: Rust ports of cited engine rules, each unit-tested (§8), so the
teaching view and the checker cannot disagree.

- **Placement:** the 100 m auto-join ring and a "will join Alpha 1-1" ghost line (`AI/ArcadeTemplateFind.cpp#L412-L471`); FORM snap
  ghosts for non-leaders; radius and marker links greyed on FORM members.
- **Waypoints:** a dashed "loops back to →" arrow from CYCLE to its computed target; "SWITCH jumps to →" arrows, forward or back;
  resolved GET IN / JOIN targets, or "no target: completes without boarding / skips the merge".
- **Sync wiring:** each end shows ready or not; logic AND/OR waypoints drawn as gates; GET IN handshakes marked; a group's card says
  what holds it: its own Condition, a named partner, or an unfired Switch (`AI/AIArcade.cpp#L309-L369`).
- **Triggers:** Size greyed under Activation None and ignored fields greyed on Guarded-by; an END-group counter ("2 of 3 END1
  triggers"); a type badge for `this` in every code box ("this: Boolean", "this: leader's soldier").
- **Sides:** a start-existence badge per side (SP needs a placed group, `AI/AICenterStats.cpp#L1328-L1349`); a friendship grid with
  only its two editable cells enabled.
- **Randomness:** "show 10 random starts", drawn with the engine's lowest-terrain-cost pick when the island and reference vehicle
  are loaded (`AI/AICenterImpl.cpp#L628-L691`); otherwise a uniform disc labelled "approximate" [I].

### 4.4 "Why is this greyed out or invalid?"

Every disabled control and hidden button answers *why* on hover and F1 ("Rank is hidden for Logic units"; "Preview is hidden: group
Alpha 1-1 fills 14 of 12 crew seats"). Every finding links its entry and a 30-second "Try it", and the explanation sits next to the
object on the map, like Factorio's flying error text [V]. The readiness coach and troubleshooting playbooks (doc 21 §11.1–§11.2) cite
entries by id. Feedback states the cause in engine vocabulary: "Fired at mission start: Activation is WEST · NOT PRESENT and no WEST
unit was inside the area at t = 0" (`World/Detection/Detector.cpp#L914-L921`).

### 4.5 The manual browser and glossary

A searchable manual grouped as Units & groups, Waypoints, Triggers, Sync & logic, Randomness, Presentation, Mission & campaign,
Multiplayer, Dialect traps, plus a task-first index ("I want… a patrol, an ambush, an alarm, a pickup, a timed event, an ending")
that lists entries in the order a mission maker uses them (§2 item 10). Search matches ids, plain names, original labels in every installed locale and later-game aliases (which
land on their dialect entry). Pages open with a question in the user's words ("Why does my trigger fire the moment the mission
starts?") and a concrete case before the jargon (Nicky Case [V]). The glossary lists every term with its original label and dialect
notes; a "Coming from later editors?" page maps modules, Dismiss, Loiter, Seized by, `thisTrigger`, BLUFOR/OPFOR, per-unit
descriptions and Eden attributes to CWA equivalents or "not in this engine".

### 4.6 Animated map demos: how the 2D renderer plays them

- **Data and drawing.** A demo is a `DemoScene` (a tiny typed mission model on a canvas) plus a `Timeline` of keyframes: entity
  positions and overlay states (a sync end turning ready, a countdown bar filling, a trigger going idle → counting → active →
  spent). It is drawn by the editor's own map code (doc 06's `DrawList` batcher into an offscreen wgpu texture shown by egui), so it
  looks exactly like the user's editor, overlays included.
- **Two labelled layers.** The **computed layer** (CYCLE target, Switch target, sync partners, GET IN resolution, END grouping) comes
  from ported rules and is exact. The **illustrative layer** (walking units, AI behaviour) is a storyboard marked "illustration".
  Unlike Factorio's tips, which run the real game [V], we do not re-simulate the engine's AI, so every behavioural demo names a
  probe mission that asserts the same outcome in the real game (§8).
- **Controls.** Play, pause, step, scrub, speed; a **"predict, then play"** pause asks a one-tap question before the reveal (Case's
  "Place your bets"; the pretesting effect, Richland et al. [V]). Reduced motion swaps in a keyframe strip; every demo has a text
  transcript.
- **Canvas and tests.** Committed demos use a small synthetic procedural terrain, with no game assets (AGENTS.md fixture rules); with
  an install loaded, the same scene can be hosted on a real island at runtime, never committed. Timelines are seeded and
  deterministic; CI asserts semantic keyframes ("the CYCLE arrow targets waypoint 1") and golden images (doc 06 test stack).
- **First set (13).** Sync rope; Countdown vs Timeout with the mid-weighted delay; Whole group vs Any member; CYCLE nearest target;
  FORM snap; pickup handshake; TR UNLOAD drop-off; SWITCH releasing HOLD; SENTRY → SAD ambush; guard pool with Guarded-by pins;
  AND/OR gates; "roll presence 20 times"; the mission-start timeline.

### 4.7 "Show me in game"

Builds the entry's `DemoMissionSpec` into a product-owned scratch mission (e.g. `__fm_<id>.<world>`) and launches it through the
normal Preview flow (doc 08). It is labelled a demo, never touches the user's missions, and is removed on exit unless pinned to a
"Demo missions" list. The same spec builds the probe mission, adding only the assertion script, so the demo and its probe cannot
diverge [I]. Without an installed game and a stock island for the profile, the button is disabled and says why.

### 4.8 Contextual tips

Tips fire only on a computed fact: a lint, a failed check, a dialog's first opening, or a returning user opening a dialog after a
long gap (an optional 30-second refresher; spacing, Cepeda et al. [V]). They are non-modal, never shown while the user types, never
repeated once dismissed, silenced by one global "quiet" switch, and kept in a reopenable **tips inbox** (Factorio FFF #208 [V]). No
start-up tour; at most one dismissible welcome card offers the boot camp. Two limits come from doc 34 §3.2 (le03/le04): an attention
budget (at most one unprompted discovery tip per session; lint-driven tips are not counted) and **mastery suppression**: a tip about a
concept stops once the user's own edits show it used correctly (for example three real syncs), so an expert is never taught what they
just did [I].

## 5. Live tutorials ("boot camp")

Doc 21 §11.4's Academy and this boot camp should be **one system**: the Academy's ordered topics and validator-computed checks
become the curriculum (open question 4).

### 5.1 Tutorial model (proposal-only)

```rust
pub struct Tutorial {
    id: TutorialId, track: Track, requires: Vec<TutorialId>,
    sandbox: SandboxSpec,         // the starting mission plus the allowed palette
    steps: NonEmpty<Step>,
    reference: ReferenceSolution, // typed command list; CI and pack import replay it (§5.6)
}
pub struct Step {
    id: StepId, teaches: NonEmpty<ConceptId>, brief: TextKey, goal: Goal, hints: HintLadder, ghosts: Vec<Ghost>,
    palette: Palette,                     // e.g. only Units + Waypoints ("reduce the degrees of freedom")
    explain_back: Option<ChoiceQuestion>, // multiple choice, so code checks it without a model
}
/// Knowledge is checked on the mission model. Events only pace a lesson (open a dialog, run Preview); they never prove learning.
pub enum Goal { Holds(Predicate), Pacing(EditorEvent), All(Vec<Goal>), Any(Vec<Goal>) }
/// Closed vocabulary; each variant maps to a validator query, so a tutorial can never run a script.
pub enum Predicate {
    Exists { bind: RoleName, select: Selector },            // binds the first match for later steps
    Field { role: RoleName, field: FieldId, is: ValueMatch },
    Relation { a: RoleName, rel: Relation, b: RoleName },   // SyncedTo, BoundTo, MemberOf, CycleTargets, SwitchJumpsTo
    NoFinding { lint: LintId, on: Option<RoleName> },
    PreviewReady,                                           // readiness ladder empty (doc 21 §11.1)
}
```

Predicates check **values and relations**, not the mere existence of a type: MakeCode's `BlocksExistValidator` "does *not* validate
the parameters", so wrong solutions pass it [V]. Any valid solution passes (Gee's "multiple routes" [V]). VS Code's default, "checked
off when opened", proves nothing [V].

### 5.2 Sandbox, checking and fading

- **Sandbox.** Each lesson starts from a throwaway mission built from `SandboxSpec`: a stock island for the profile, or the synthetic
  canvas when no game is installed (then without Preview moments). Edits use the normal typed, undoable commands; each step pushes an
  undo checkpoint that "Reset step" rolls back to. Work leaves the boot camp only by explicit Save As (Gee's "psychosocial
  moratorium" [V]). Progress is a local record of passed step ids plus the sandbox state.
- **Checking and feedback.** Goals are re-evaluated on each model change (debounced). Feedback is task- or process-level, specific,
  next to the object, in engine vocabulary; never "Great job!" (Hattie & Timperley; step-based tutoring, VanLehn d = 0.76 [V]).
- **Fading.** Lesson 1 opens a finished mini-mission to inspect and poke (Unity Microgames [V]); later lessons blank one part, then
  two; each track's capstone is a blank page. Explain-back questions ("Why did Alpha wait here?") build understanding (Chi et al.
  [V]); a wrong answer shows why in one line and *offers* the demo replay, with no penalty; every question has "Skip".
- **Hint ladder.** (1) A one-line nudge; (2) a **ghost** on the map (pulsing ring, dashed arrow, translucent unit at the target); (3)
  the bottom-out answer as a worked step (Shih et al. [V]), then a near-transfer variant to practise. A short cooldown between rungs
  discourages click-through; help-seeking feedback changes behaviour more than learning (Aleven et al. 2016 [V]), so nothing is scored.
- **Preview moments.** Each lesson ends with the game running the learner's own work, followed by an explain-back question. Whether
  Preview can report in-game observations back depends on doc 08's return channel [U]; until then a Preview moment is watched, and
  passing rests on the validators.
- **Achievements** are computed by the same validators and purely informational. Placeholder era-style names: *Clockwork* (a CYCLE
  whose computed target is not waypoint 0, so the loop skips the start), *Tripwire*, *Rendezvous*, *Logician* (an OR gate opened by either input), *Taxi service* (the
  transport waited), *Fog of war* (randomised presence and starts). An optional offline comparison replaces pass/fail stamps ("yours
  used three triggers; the reference used one logic gate"): the Opus Magnum idea without a leaderboard [V].
- **Skip, test out, resume, expert mode.** Every lesson and step is skippable. "I already know this" runs the lesson's capstone check
  on a fresh sandbox and grants completion on a pass; a lesson whose capstone predicates already hold in one of the user's own
  missions is offered as done ("you already built this in your mission *Ambush*"), so veterans get credit without a quiz (doc 34 §3.1) [I]. Hint density fades as checks pass; an "experienced" setting collapses cards to
  their header. UI masking is off by default: tutorial freedom did not change player behaviour in a 45,000-player study (Andersen et
  al., CHI 2012 [V]), and Unity made masking optional in 0.5.0 [V]. No timed steps.

### 5.3 The instructor persona

Doc 21 §11.7's era staff officer, as a training instructor: dry, warm, brief (≤ ~3 sentences), never patronising, never blocking.
**Facts, statuses and numbers are rendered by code in a separate box**, so the persona cannot alter a fact. Plain voice is a toggle;
with AI off, human-written template lines keep the voice. Example (persona line, then the code-rendered fact line):

> *Instructor:* Your tripwire is armed, but it isn't watching anyone. Tell it who to watch.
> `Activation: None · Condition: this → can never fire` · entry `trigger.default-inert` · `CWR:World/Detection/Detector.cpp#L865-L868`

### 5.4 Curriculum

Ordered by §1.2's frustration ranking. Minutes are estimates to check in playtests [I]. Every lesson ends in Preview.

| Lesson | Teaches | Twist | Min |
| --- | --- | --- | --- |
| **A. First hour** | | | |
| A1 Boots on the ground | Player unit, map, modes F1–F6, Preview; pre-trains the words unit, group, waypoint, trigger | Remove the Player: Preview disappears, and hovering its place says why (§4.4) | 5 |
| A2 A squad | Auto-join ring, leader by rank, F2 links, FORM snap | A second squad placed 60 m away merges into the first | 8 |
| A3 A patrol | MOVE, CYCLE target, waypoint life-cycle strip, speed and formation, the combat-colour grid | Moving the CYCLE marker changes where the loop restarts | 10 |
| A4 A tripwire | Trigger area, side activation, Present, `this`/`thisList`, Once vs Repeatedly, END1 | A fresh trigger (None + `this`) never fires | 10 |
| A5 Wait for it | Sync as a rendezvous; the two-waypoint release pattern | Two syncs on one waypoint mean AND | 10 |
| A6 An invisible helper (capstone) | A Game Logic as named anchor and code holder, used from a script field | A second logic dropped within 100 m joins the first one's group and shares its waypoints (auto-join applies to logics too) | 12 |
| **B. Field craft** | | | |
| B1 Timing | Countdown vs Timeout, min/mid/max, radio Alpha–Juliet | Max 0 means no delay; radio ignores timers | 12 |
| B2 Stuck on purpose | HOLD, SWITCH, leaving a CYCLE | SWITCH jumps back if the group passed the synced waypoint | 10 |
| B3 Taxi | LOAD + GET IN on a two-group sync, TR UNLOAD, GET OUT vs UNLOAD, In cargo, Lock | A third group on the sync disables automatic targeting | 15 |
| B4 Logic gates | AND/OR waypoints with the output on the *next* logic waypoint; replays the 2019 forum case "alarm OR spotted → crew mounts" | A group synced to the gate waypoint itself is released early (probe-backed) | 15 |
| B5 Never the same twice | Presence probability and condition, placement radius, marker starts | Playable units ignore presence; a condition reading an init variable | 12 |
| B6 Reaction force | GUARD pool, Guarded-by pins, SENTRY → SAD | A Guarded-by trigger ignores its On Activation | 15 |
| B7 Watching things | Bound triggers (group, leader, member, vehicle, static object), "building destroyed" | Whole group + Not present = "not all inside" | 12 |
| B8 Who knows what | Detected by, Info age, friendship grid, side-existence rule | Detected by East never fires if East only spawns by script | 12 |
| **C. Director** | | | |
| C1 Cutscenes | Effects (camera, titles, music), Intro/Outro as storyboard slots, logic timelines (doc 32 §3) | Effects condition `thisList` = "only if the player caused it" | 20 |
| C2 Briefing and endings | Mission name (`__cur_sp`), briefing, `OBJ_` statuses, END AND rule, Lose precedence | Two END1 triggers must both be active | 15 |
| C3 Scripts | Init-order timeline, `this` per field, SQS basics, `script.check`, SCRIPTED waypoint arguments | A presence condition cannot see init-line variables | 20 |
| C4 Campaigns | Campaign graph, outcomes → next mission, `saveVar` state, branches (docs 18/19) | Objects don't survive between missions | 20 |
| C5 Multiplayer | Playable slots, `description.ext`, init lines on every machine, `isServer` (`GameStateExt.cpp#L909`) | `addWeapon` in an init line runs on every client [I] | 20 |
| C6 Coming from later editors | Modules, Dismiss, Loiter, Seized by, `thisTrigger` → CWA equivalents | The engine has no modules; open one of the editor's modules (doc 31 §4) and see the plain triggers, logics and script it compiles to | 10 |
| C7 Workshop tools | Merge, sections, Show IDs, map objects, the Easy/Advanced replacement | Merge renames names but not the code using them | 12 |

Track A totals about 55 minutes. Docs 31–32 (no-code ladder, cinematics) add C lessons for modules, the rule builder and the
timeline (open question 10).

### 5.5 Lesson file format

Tutorials are data (precedents: MakeCode Markdown tutorials, VS Code walkthroughs, Eden config tutorials [V]): one Markdown file per
lesson with YAML front matter, then one `##` heading per step holding a fenced `yaml` block of machine fields and the narration.

````markdown
---
id: bootcamp.a4
track: first-hour
requires: [bootcamp.a3]
sandbox: { from: sandbox.a4, palette: [units, triggers] }
---
## arm
```yaml
teaches: [trigger.area, trigger.default-inert]
goal: { holds: { exists: { bind: wire, select: { kind: trigger } } } }
ghosts: [{ ring: { at: marker:road_east, radius: 40 } }]
hints: [{ nudge: hint.a4.mode }, { ghost: { arrow: { to: marker:road_east } } }, { solution: a4.arm }]
```
Put a trigger across the road east of your patrol.
````

The next step, `watch`, uses `goal: { holds: { field: { role: wire, field: trigger.activation, is: WEST } } }`, which reuses the
role `wire` bound above, and `explain_back: q.a4.why-inert`.

### 5.6 Community tutorial packs

Community lessons ship as **T0 content packs** (doc 22 §2.1): lesson files, sandbox missions, a reference solution per lesson and
optional demo scenes. Import parses defensively (schema, size caps; an unknown predicate is a refusal, never a script); resolves
every concept id against the registry or the pack's own entries; **replays each reference solution** and refuses packs with an
unsolvable step (Roblox learners reported "pieces appear all of a sudden" [V]); runs doc 24's script-risk audit on sandbox missions,
whose scripts run only inside Preview; treats pack text as untrusted data, never agent instructions; and allows no URLs, network or
files outside the pack.

## 6. The AI

### 6.1 Tools

Names are provisional (doc 21 §10.2 style). All are read-only product capabilities.

| Tool | Input | Returns |
| --- | --- | --- |
| `list_concepts` | `text?`, `kind?`, `anchor?`, `limit ≤ 20` | `[{id, title, what}]` by alias match; a later-game alias ranks its `dialect.*` entry first |
| `explain_concept` | `id`, `depth: Card \| Full` | The entry in the user's locale if fresh, else English: card, body, facts with tags and code-attached citations, dialect notes, related ids |
| `explain_instance` | Entity handle | The concept ids that apply, **computed facts** ("waits for: trigger `Alarm`, not fired"; "CYCLE → waypoint 1"), open findings |

An unknown term returns `NotInManual { term }` with no model call; a later-game term returns its dialect entry ("not in this
engine") plus the nearest CWA concept. A weak model never has to guess.

These overlap doc 30 §4.4's `reference.search` and `reference.card`, which the seed `SKILL.md` already names. Two tool families with
the same job make a small model pick between near-synonyms, so one family should survive: concept cards served by `reference.card`,
or these three tools with the doc 30 names as aliases (doc 30 open question 7) [I].

### 6.2 How a weak model succeeds

Doc 21's "the model fills; code decides", applied to teaching: (1) code searches and computes a short menu of candidate ids, and the
model **picks** one or `none_fit`, and, when the user described a symptom, also picks the matching gotcha or `asks` line by index;
(2) code renders the entry, and the model may paraphrase in about 3 sentences at most (Kestin et al.'s brevity rule [V]), reusing the
entry's picture as written but never inventing a new analogy or stretching one into a mechanism; (3) code checks the paraphrase: every command and class it names exists in the profile catalog (doc 21
§10.2), every number appears in the entry, and no evidence tag is upgraded, so an [I] fact never becomes a rule; (4) on failure the
reply falls back to the entry verbatim. A 3B model's worst case is a correct, plain card.

### 6.3 Tutor mode (boot camp only)

The model sees the step goal, the validator state and the reference solution. It chooses one hint rung per turn and writes that
line. It has no mission-editing tools, and only validators mark a step complete. Why: plain GPT-4 as a crutch left students 17% worse
on an unassisted exam without their noticing, while a hints-only tutor fed teacher solutions removed the harm (Bastani et al., PNAS
2025 [V]; its published correction is unread [U]). A grounded, brief, one-step-at-a-time tutor more than doubled learning gains
(Kestin et al., Sci. Rep. 2025, n = 194, proctored [V]). Leaving tutor mode is allowed but visible; regular-agent work is labelled
and earns no achievement.

### 6.4 "Explain this mission"

Code builds a `MissionAnatomy` for any mission, downloaded ones included: sides present and whether each exists at start, group
waypoint timelines, triggers in plain words, the sync graph with gate semantics, endings with their AND groups, randomness, open
findings; each item carries concept ids. With no model it is a clickable structured view. With a model, the model writes a ≤ 150-word
walkthrough whose every sentence cites anatomy ids, and clicking a sentence highlights the map. Mission text is quoted, never obeyed.

### 6.5 Relationship to the primer

`skills/mission-primer` stays the always-loaded router; `skills/field-manual` loads on demand (its index enters context, entries are
fetched per id: progressive disclosure for the model). An external agent using the opt-in MCP server (AGENTS.md "outbound exposure")
gets the same three tools and gains no capability.

## 7. Localisation and accessibility

- **Locales and staleness.** English (canonical), Czech, Polish, Russian and German, the owner's target set; folders use BCP 47 tags
  (`en`, `cs`, `pl`, `ru`, `de`; `CZ` is a country code). Community sizes per language are unmeasured [U]. One file per entry per
  locale; each translated field records the source hash of its English field. A stale field falls back to English with an "out of
  date" badge; a stale engine fact is never shown. Citations and code tokens (`this`, `WEST`, `setPos`)
  are never translated.
- **Pictures are transcreated, rules are translated.** The analogy line ("a lit fuse", "a rope", "read the labels like a lawyer") is
  idiom and may be replaced by a local image that teaches the same rule; each carries a translator note naming that rule. `what`,
  gotchas and facts are translated literally. Their English source sentences stay short (about 20 words or fewer) and
  idiom-free, which also serves readers with dyslexia or English as a second language [I].
- **Original labels.** Aliases include the game's own localised editor labels, read at runtime from the user's install and never
  committed; this works because dialogs use string ids (`CWR:UI/Map/UIArcadeWaypoint.cpp#L83`) [V/I].
- **The AI in other locales.** `explain_concept` returns the reviewed translation when fresh; otherwise the model translates prose
  only and the UI marks it machine-translated. Persona template lines are translated by humans.
- **Layout and fonts.** Card budgets are measured in rendered width per locale and CI fails on overflow (German expands) [I]. Modern
  panels bundle an OFL font with Latin Extended and Cyrillic (e.g. Noto Sans) [I]; whether the game fonts used by the classic view
  cover Cyrillic depends on the install [U]. UI strings use Fluent-style plural messages; crate choice [U].
- **Accessibility.** WCAG 1.4.13 cards opened from the keyboard (F1, Space); manual, cards and boot-camp panels are egui widgets with
  AccessKit names (doc 06); the classic map, being a texture, gets a parallel accessible list of entities, overlays and instance
  explanations. Nothing relies on colour alone (combat modes are named; sync readiness uses shape and colour). Reduced motion follows
  the OS; every demo has a transcript; no timed steps.

## 8. Authoring and maintenance

- **Evidence chain: fact → pinned citation → test or probe.** A [V] rule the editor re-implements (CYCLE target, auto-join, sync
  partners, GET IN/JOIN target, Switch target, END groups, `this` typing) is one Rust function feeding the lint, the overlay and the
  demo's computed layer; its tests name the entry id and port the upstream behaviour (AGENTS.md porting rules). An [I]/[U] fact names
  a probe tracked in `docs/porting/upstream-test-map.csv` with status `probe`.
- **Initial probe queue** (code reads awaiting runtime proof): does `thisList` list crew or only their vehicle, including after
  runtime boarding; do Logic/Anybody triggers count Game Logics, and do empty vehicles count toward their config side; is a group
  synced to a logic gate waypoint released when the logic arrives; does a transport synced to GET IN wait for boarding; does an
  unbound, unsynced GET IN board without walking; is `local <logic>` server-only in MP; does retail 1.99 have the `d`/`c`/`g` crew
  names; the Countdown/Timeout label order; does JOIN AND LEAD run the absorbed group's On Activation; does the HUD marker ignore Show
  waypoint; does "Actual" Info age fire a player-side Detected-by trigger at start; what does an AI group do after its 600 s sync Wait
  lapses; does SWITCH jump backwards; are radius placements biased toward roads; do radio triggers ignore timeouts.
- **Required CI (offline, self-contained).** Schema and unique ids; `related`/`lints`/`exercise`/`demo` resolve. **Coverage:** every
  `UiAnchor` variant and lint id has an entry. Every tutorial's `teaches` ids exist and its reference solution replays to completion.
  **Every surface renders non-empty for every id after a cold start with caches cleared** (Godot had two empty-tooltip bugs, one
  only after a reload [V]). Card style lint: verb-first one-line `what`, no restating the label, no hand-typed defaults (Blender HIG
  [V]); the picture never stands in for `what`; at least one `asks` line; every Try-it step has an expected observation, and at least
  one step per entry is checkable in the editor (overlay or validator) [I]. Budgets: card width per locale; SKILL.md < 500 lines, ≈ 5000 tokens. Every command or class named exists in its profiles'
  catalog (doc 23 §14). Demo keyframe assertions and golden images. Citations well-formed and on an allowed pin.
- **Opt-in citation check** (env-gated or scheduled; needs the pinned clones): each cited file and range exists at its pin, and a
  recorded hash of the cited lines still matches, catching drift when a pin is bumped; the CE offset table is re-derived.
- **Review checklist.** Original words, quotes ≤ one sentence and attributed; an era tag on every web source; the AGENTS.md
  public-hygiene search; demos that show the mechanism, not decoration (Höffler & Leutner: animation helps most when it represents
  the mechanism or procedure [V]).
- **Ownership.** An entry changes in the same change set as the code implementing its rule, like `CODE-INDEX.md`.

## 9. Phased plan and acceptance tests

| Phase | Delivers | Acceptance tests |
| --- | --- | --- |
| 0. Decisions | Design-gap requests: names (doc 02 §9), entry schema and ownership, Academy = boot camp, demo fidelity policy, Easy/Advanced replacement, plain-language relabels | Recorded in `docs/`; no UI strings before names are cleared |
| 1. Registry + cards | Parser; ~25 top-confusion entries; hover cards, F1, dialog "?", glossary; `list_concepts`, `explain_concept` | **AT1** every doc 03 §4.4–§4.10 field has an entry. **AT2** cold-start render passes for every id. **AT3** "not in this engine" for Dismiss, Loiter, Get in nearest, Seized by, modules (plus the pointer to the editor's own modules, §1.4), `thisTrigger` |
| 2. Instance help | Overlays (§4.3), "why greyed", finding ↔ entry links, tips inbox, `explain_instance` | **AT4** each overlay's computed target equals its rule's unit-test value on 20 synthetic missions. **AT5** no tip fires twice after dismissal (scripted session) |
| 3. Demos | Demo player, the 13 scenes, probe missions, "Show me in game" | **AT6** every behavioural demo has a probe, and they agree. **AT7** reduced motion and a transcript for every demo |
| 4. Boot camp A+B | Runner, sandbox, hint ladder, persona, achievements, test-out | **AT8 (headline)** in moderated playtests newcomers finish A1–A6 in ≤ 15 min of active building (narration excluded), producing, as validators check: a group with ≥ 2 MOVE waypoints and a CYCLE whose computed target is a MOVE; a WEST-Present trigger with a non-default condition or END type that fires in Preview; a named Game Logic whose position a script field uses (e.g. `truck1 setPos getPos lz1`: both commands are registered in CWR, `GameStateExt.cpp#L938, #L1236`, and `script.check` gates the profile). Proposed bar: ≥ 6 of 8 participants [I]. **AT9** returning veterans clear Track A by test-out in ≤ 5 min |
| 5. AI tutor + explain mission | Tutor mode, `MissionAnatomy` | **AT10** on a 60-question benchmark (20 dialect traps), a 3–9B model through §6.2 makes zero engine claims absent from entries (claim matcher + human review), against a template-only baseline (doc 21 §12.1). **AT11** a delayed, unassisted transfer task a week later: tutor mode no worse than no-AI (the Bastani control) |
| 6. Community, locales, Track C | Pack import, `cs`/`pl`/`ru`/`de`, Track C | **AT12** malicious packs (oversized, unknown predicate, URL, unsolvable step, script outside Preview) refused with structured errors. **AT13** every card renders without overflow in each locale; stale fields fall back correctly |

## Open questions

1. **Names.** "Field Manual" and "Bootcamp" are Arma 3 feature names [V]; era-register candidates such as "Staff Handbook" and
   "Training Depot" (unchecked) need doc 02 §9 clearance.
2. Do plain-language relabels ("Countdown: fires after the delay no matter what", "Group: not all inside") replace the original labels
   or sit beside them? Needs a design-gap request; recommendation: beside them, so community tutorials still match.
3. Where does the registry live (a crate such as `fm-registry`, or the editor core), is the build step `build.rs` or `xtask`, and who
   owns the entry schema version?
4. Is doc 21's Academy (§11.4) exactly the boot camp? This doc proposes yes.
5. Can Preview report in-game observations back to the editor (doc 08)? That decides whether Preview moments can be checked.
6. Retail CWA 1.99 vs CWR differences affecting entries (Easy/Advanced default, crew-name variables, commands such as
   `createCenter`): each entry needs a profile badge.
7. Should the boot camp run on a stock island (needs an install) and also offer the synthetic canvas without Preview?
8. Should community packs be signed or hash-pinned like T2 plugins (doc 22), and may packs add *entries* or only lessons?
9. Which local, opt-in teaching metrics (completion, hint depth, skips), if any, may a user choose to export for playtest studies?
10. Docs 30–32 now exist: do doc 30's cards and this registry merge into one store and one tool family (§6.1), and which C lessons
    do doc 31's modules and rule builder and doc 32's timeline need?
11. The seed skill uses flat ids (`cycle-waypoint`) and fixed Markdown sections, while §3.1–§3.4 use dotted ids (`waypoint.cycle`) and
    typed front matter (`card`, `facts` with grounding). Which one is canonical, and when do the seed entries migrate? Until then,
    lint, tutorial and `explain_concept` links cannot resolve against the seed files.

## Sources

**Engine (pinned; `CWR:` per the header).** `World/Detection/Detector.cpp#L478-L1529`; `AI/AIArcade.cpp#L265-L2053`;
`AI/AIArcadeActions.inc#L1-L1810`; `AI/AICenterImpl.cpp#L295-L2220`; `AI/AICenter.cpp#L82`; `AI/AICenterStats.cpp#L1328-L1349`;
`AI/AIGroup.cpp#L759-L826`; `AI/AIGroupCmd.cpp#L613-L636`; `AI/AIUnitImpl.cpp#L223-L300, #L2108-L2143`; `AI/Path/AITypes.hpp#L31`;
`AI/Path/ArcadeWaypoint.hpp#L61-L257`; `AI/ArcadeTemplate.hpp#L19-L61`; `AI/ArcadeTemplate.cpp#L446-L473, #L1033-L1134`;
`AI/ArcadeTemplateFind.cpp#L412-L524, #L1086-L1310`; `World/WorldInit.cpp#L539-L706`; `World/WorldImpl.cpp#L495-L657`;
`World/WorldSetup.cpp#L1254-L1283`; `World/Entities/Vehicles/InvisibleVeh.hpp#L20-L40`; `UI/Controls/UIControlsBase.cpp#L91-L135`;
`UI/Map/UIArcadeWaypoint.cpp#L72-L105`; `UI/Map/UIMapExtDisplay.cpp#L63-L97, #L411-L501`; `UI/Map/UIMap.cpp#L1696-L1718`;
`UI/Map/UIMapMain.cpp#L299-L458`; `UI/Map/UIMapDisplayBriefing.cpp#L737-L767`; `Game/Commands/GameStateExt.cpp#L909, #L938, #L1236`;
`BohemiaInteractive/CWR@ffc61838b7:engine/Random/randomGen.cpp#L156-L171`. CE: `UI/Map/UIMapExtDisplay.cpp#L352-L397`.

**Repository.** Docs 02 §9; 03 §4; 06; 08; 09 §4 (P2, P7, P8, P11); 18; 19; 21 §9–§12; 22 §2.1; 23 §13.4, §14; 24; 28;
30 §4.4; 31 §4; 32 §3; 34 §3; `skills/mission-primer/SKILL.md`; `skills/field-manual/`; `AGENTS.md`.

**Community evidence (era-tagged).** COMBATSIM 2002 (Pawelek) <https://www.combatsim.com/memb123/htm/2002/09/opflash-me/> · BI forums
topics 10819 (2002), 15989 (2002), 38717 (2004), 43006 (2005), 73262 (2009, Arma 2), 226477 (2019) under
<https://forums.bohemia.net/forums/topic/> · Steam CWA (app 65790) discussions 360670708795153381 (2016), 2579854400753259902 (2017),
1709564118764995008 (2018), 4762081876734597538 (2024) · OFPEC tutorials id=38 (OFP) and id=16, 17, 28, 221 (ArmA-era)
<https://www.ofpec.com/tutorials/> · aligrant.com OFP editing pages · PMC Editing Wiki <https://pmc.editing.wiki/doku.php?id=ofp:missions:triggers>.

**Product precedents.** Arma 3 SITREP #00148 <https://dev.arma3.com/post/sitrep-00148>, BIKI Eden and CfgHints pages (via search
index), Arma 3 Bootcamp Update (2014-07-14); Arma Reforger Samples `SampleWorldEditorTool.c`; Blender tooltip HIG
<https://developer.blender.org/docs/features/interface/human_interface_guidelines/tooltips/>; Godot issues #59270, #98592; Unity Tutorial
Framework guide and changelog 0.5.0; VS Code walkthrough contribution points; JetBrains IDE Features Trainer (2016); MakeCode tutorial
docs <https://makecode.com/writing-docs/tutorials/basics>; Roblox DevForum onboarding thread (2021-03-12); Factorio Friday
Facts 208, 261, 361, 362 and 397 <https://www.factorio.com/blog/>; Portal developer commentary; Nutt, "The secret to Mario level design" (2012);
Zachtronics TIS-100 manual, Opus Magnum; Agent Skills specification <https://agentskills.io/specification>.

**Learning science and UX.** Sweller 1988; Sweller & Cooper 1985; Kalyuga et al. 2003; Kirschner, Sweller & Clark 2006; Wood, Bruner &
Ross 1976; Renkl & Atkinson 2003; Chi et al. 1989; Richland, Kornell & Kao 2009; Cepeda et al. 2006; Hattie & Timperley 2007; VanLehn
2011; Höffler & Leutner 2007; Gee 2003; Deci, Koestner & Ryan 1999; Andersen et al., CHI 2012
<https://grail.cs.washington.edu/projects/game-abtesting/chi2012/chi2012.pdf>; Victor 2011, 2012; Case 2017, 2018; NN/g (Laubheimer
2023 <https://www.nngroup.com/articles/onboarding-tutorials/>; tooltip guidelines 2019; Nielsen 2006); W3C WCAG 2.1 SC 1.4.13
<https://www.w3.org/WAI/WCAG21/Understanding/content-on-hover-or-focus.html> and SC 2.2.2
<https://www.w3.org/WAI/WCAG21/Understanding/pause-stop-hide.html>; Horvitz (Lumiere); Nass 2010; van der Meij & Carroll,
"Principles and heuristics for designing minimalist instruction", *Technical Communication* 42(2), 1995, pp. 243–258
<https://eric.ed.gov/?id=EJ504916>.

**AI tutoring.** Bastani et al., PNAS 2025 <https://www.pnas.org/doi/10.1073/pnas.2422633122> (correction pnas.2518204122 unread);
Kestin et al., Sci. Rep. 15:17458 (2025) <https://www.nature.com/articles/s41598-025-97652-6>; Aleven, Roll, McLaren & Koedinger,
IJAIED 2016; Shih, Koedinger & Scheines, EDM 2008.

## Verification notes

### Pedagogy review (2026-09-27)

**Scope.** This doc, `skills/field-manual/SKILL.md` and its 32 seed entries, read against §2's principles and docs 21 §11, 28, 30 §4.4,
31, 32 and 34 §3. The entries were read, not edited; engine facts were not re-checked in this pass.

**Verdict.** The design is sound teaching: pull not push, one idea per step, twists, predict-then-play, validator-checked steps, a
hints-only tutor and code-rendered facts. The seed entries are plain, concrete and never patronising; each has a tiny example, a Try it
and its "(unverified)" marks, so a weak model that follows `SKILL.md`'s recipe stays inside the facts. The main gaps sit between the
seed format and this doc's own card contract.

**Changed in this doc.** Stale "docs 30–32 do not exist" notes (header, C1, C6, Track C, open question 10); TL;DR 15 min = active
building; a two-part "module" answer (§1.4, AT3); Deci et al. stated precisely and a minimalist-instruction principle (§2 items 6, 10);
`asks`, literal `what` vs `picture`, and Try-it steps with expected observations (§3.1, §8); no looping card demos and a
concrete-first page order (§4.1); a task-first index (§4.5); tip budget and mastery suppression (§4.8); optional replay, a computable
*Clockwork* and credit from the user's own missions (§5.2); real twists for A1 and A6 (§5.4); tool-family overlap with doc 30 (§6.1);
symptom → gotcha picks and no invented analogies (§6.2); BCP 47 locale tags and transcreated pictures (§7); open question 11.

**Findings on the seed entries** (for the entry owners; suggestions, not edits):

1. **Card headers do not fit.** Every "In one sentence" line runs about 22–42 words, and most carry two or three ideas. The index's
   "In short" column is close to a card `what`; promote it into each entry as a literal, verb-first line and keep the analogy as the picture.
2. **Pictures that mislead.** `trigger-activation`: "not wired to anything yet" invites syncing the trigger; "watching nobody yet"
   matches the persona line. `cycle-waypoint`: a boomerang returns to the thrower, which is the "loops to the start" myth; a magnet
   pulling the group to the nearest earlier waypoint fits. `logic-gates` calls sync lines wires while `synchronisation` calls them a rope; use one image.
3. **Engine detail comes second.** Pages should lead with a question, the picture and the example (§4.1); the dense, citation-heavy
   "What it really does" bullets (some over 60 words, e.g. `guard-and-guarded-by`) belong in the collapsed engine-truth block.
4. **Myths are buried in gotchas.** Give `cycle-waypoint`, `trigger-end-types`, `show-waypoint`, `game-logic`, `guard-and-guarded-by`,
   `placement-radius`, `info-age`, `empty-vehicles`, `combat-mode` and `waypoint-lifecycle` a "Folk wisdom vs engine" section, and
   add one "When not to use it" line per entry.
5. **Try it gives the answer away, and mostly needs Preview.** Split each step into action and expected observation. Only 4 of 32
   (`groups-and-leaders`, `player-and-playable`, `not-in-this-engine`, `show-ids-and-object-ids`) show something without Preview; add an
   overlay step (CYCLE arrow, auto-join ring, END counter, "show 10 random starts", "roll presence 20 times") so the boot camp can check it.
6. **Try-it step bugs.** `trigger-end-types` step 3 needs "set Trigger 2 back to End #1" after step 2. `countdown-vs-timeout` step 2
   needs "then wait 20 s", or A seems broken. `waypoint-types` step 3 states no outcome. `logic-gates` step 3 omits its best twist:
   the "gate open" hint also fires at once, because on an OR gate the tanks are an input. `info-age` step 2 has no known outcome;
   label it a field experiment and keep it out of boot-camp checks. `mission-sections` step 3 has no path in this editor yet (doc 03 §4.12).
7. **Bundled concepts need their own cards.** The #1 and #5 confusions (the inert new trigger; Switch) live inside
   `trigger-activation` and `trigger-end-types`, yet §5.3 and lesson A4 link `trigger.default-inert`. Lock and Health (in
   `empty-vehicles`) and Behaviour and Speed (in `combat-mode`) need sub-anchors with their own `what` for field tooltips.
8. **Evidence marks.** "A plain statement is verified" means a forgotten mark silently upgrades a claim. Mark every engine bullet, or
   move facts into front matter, so §6.2's no-upgrade check can run.
9. **`not-in-this-engine`.** For "Seized by", the table says to combine West Present and East Not present, but the tiny example says
   either one; a model will copy the example. "Modules" needs the §1.4 two-part answer.
10. **Notation and tool names.** Document the tiny-example notation once in `SKILL.md`, so models read and write it the same way and
    code can turn it into a demo or sandbox. `SKILL.md` names doc 30's tools, not §6.1's (see open question 10).
11. **Localisation.** Idioms needing translator notes: lawyer (`bound-triggers`), fuse and breath (`countdown-vs-timeout`), gossip
    (`detected-by`), fire brigade (`guard-and-guarded-by`), stagehand (`game-logic`), boomerang (`cycle-waypoint`), bored (`seek-and-destroy`),
    sticky note (`init-line`), conveyor belt (`waypoint-lifecycle`), job card (`waypoint-types`).

**Residual concerns.** The 15-minute AT8 bar and the 55-minute Track A estimate are unmeasured. Explain-back questions may feel like
school; watch skip rates in playtests. Mastery suppression needs a per-concept definition of "used correctly", or it hides help from
people who got lucky. Achievements need an off switch (doc 34 le14 has one). Doc 34 still says docs 31–33 do not exist.
