# Campaign Content Structures and Fun: Archetypes, Patterns and Generators for Describe → Generate → Edit

Research doc 26 for `ofp-editor`. Audience: contributors and LLM coding agents. This file is meant to be read on its own.
Question answered: what domain knowledge about **mission types, campaign structure, persistent state, pacing, dialogue and the
creation flow itself** should the editor encode as typed data and deterministic generators, so that even a weak (3–9B) local
model can help a user turn a campaign description into a campaign that is **playable, memorable, fun and correct** on CWA 1.99?

**Epistemic legend.** **[V]** verified against a fetched primary source (URL/arXiv id given). **[V-search]** only a search-result
extract or a secondary page was available. **[I]** inferred or proposed by us. **[U]** unknown; needs a test or more evidence.
Repository docs are cited as "doc NN §x"; engine facts come from doc 18 and doc 19, which cite the pinned engine source.
**Scope.** This doc supplies *content knowledge* (archetypes, patterns, persistence modules, pacing, text styles, creation-flow UX)
and plugs it into the typed campaign model, CXL, lints, simulator and compiler of doc 19. It does not redesign any of those.

## TL;DR

- **Encode the craft, not just the file format.** The difference between "an LLM wrote some files" and a good campaign is domain
  knowledge: which mission types exist, what terrain and forces they need, how they fail, how branches reconverge, how state stays
  visible and how intensity rises and falls. We put that knowledge into a **typed library** (mission archetypes, campaign
  patterns, persistence modules, text templates) that code instantiates deterministically. The model mostly **picks from computed
  menus** and **writes bounded flavour text** [I].
- **Mission archetypes come from doctrine, the "why" comes from quest research.** Doctrine provides a closed task vocabulary:
  patrol types, ambush and raid organisation (FM 7-8), tactical mission tasks (FM 3-90) and the five-paragraph order [V]. Doran
  & Parberry show that quests share a small structure of **9 NPC motivations → strategies → 20 atomic actions**, expanded by a
  grammar [V]. We map both onto 16 typed mission archetypes (§9.3), each with terrain needs, force roles, objectives, an outcome
  set that fits the engine's 7 end codes, failure modes, difficulty knobs and variation axes.
- **Default campaign shape: branch-and-bottleneck plus state tracking.** Ashwell's eight patterns [V] are rated against the
  engine (7 end codes per mission; campaign variables; routers, doc 19 §7). "Time cave" is rejected as too costly. Branch and
  bottleneck, sorting hat, hub/loop-and-grow, open map and floating modules all compile cheaply, because state-tracked variants
  (presence conditions, briefing `OBJ_` variants) add variety without new missions [I]. Resistance itself had 20 missions,
  of which one run plays 18, with two branch points: a moral choice and a success/failure split that changes the next mission's
  difficulty [V].
- **Persistent state is fun only when it is visible and consequential.** Named squadmates who can die, reputation with locals,
  scarce weapon pools (engine-native) and vehicle pools (saveVar-built; the engine has none), intel carried forward and delayed
  consequences are delivered as **persistence modules**. Each module declares its variables, effects and briefing/dialogue
  hooks, plus lints that forbid invisible state [I]. Failures route forward to a different or harder but playable mission (CWC: a
  failed Montignac assault → "Strange Meeting", rejoining at "Rescue"; Resistance: failing "Information" → "Occupation (1)") [V].
- **Pacing is a first-class, checkable property.** Use a sawtooth intensity curve across the campaign [V]. At mission level use
  Left 4 Dead's build-up / sustain / fade / relax cycle, which "adjusts pacing, not difficulty" [V]. Show a per-path intensity
  strip (the PaceMaker idea [V]) and lint for fatigue ("three peak missions in a row") [I].
- **The creation flow must itself be fun.** The Casual Creators patterns [V] (no blank canvas, mutant shopping, limited
  actions, instant and simulated feedback, the "chorus line", entertaining evaluations, avoiding "1000 bowls of oatmeal")
  become concrete UI: pick one of three outlines, "surprise me" dice with pins, twist cards, a consequence map, and 50
  simulated playthroughs rendered as a chorus line of endings and survivors [I].
- **Weak-model contract.** Every model step outputs an enum index, a ranked pick of at most 5 options, or one bounded text slot
  checked against code-owned facts. Code owns terrain, classes, numbers, grid references, variable names and all wiring. A
  stronger model may fill several steps in one typed `CampaignPlan`, which goes through the same validators (doc 19 §8) [I].

## 1. Division of labour: what code owns, what the model picks, what the user decides

| Concern | Code (deterministic, seeded) | Model (bounded) | User (director) |
| --- | --- | --- | --- |
| Campaign pattern | Computes the patterns that fit the requested length, islands and persistence; instantiates the skeleton | Ranks ≤ 3 computed options against the description | Picks, or rolls "surprise me" |
| Story arc / beats | Arc shapes and beat vocabulary; checks that the intensity curve matches | Picks an arc shape and one of ≤ 5 twist cards per act | Accepts, swaps or pins |
| Mission archetype per node | Filters archetypes by the node's role, intensity target, island terrain and variety rules | Picks from ≤ 5 feasible archetypes | Overrides any node |
| Location | Resolves candidate sites (towns, bridges, road segments, LZs) from the island index | Picks among named candidates | Drags the site on the map |
| Forces and classes | Role → class via the runtime catalog + overlay (doc 17 §7.2); budgets | None (it may name roles only) | Edits in the mission editor |
| Triggers, waypoints, sockets, `saveVar` glue | Archetype generator + campaign compiler (doc 19 §7) | None | Edits via the normal editor |
| Variables, guards, effects | Emitted by persistence modules and patterns | May propose one CXL guard, which is parsed and typed (doc 19 §5) | Edits the transition table |
| Text | Skeleton lines, keys, facts, numbers, grids, callsigns | Fills slots of ≤ N characters, with a tone enum and a fact scope | Accepts, edits or rejects each line (Ghostwriter pattern, doc 15 §3.1) |
| Verification | Lints C01–C21 (doc 19) + CF01–CF12 (§10), simulator, Path Explorer | Optional narration of a simulated run (doc 21 §D9) | Plays Preview |

Rule of thumb [I]: **if a wrong answer would break the engine or the fiction's facts, code owns it; if a wrong answer is only
less charming, the model may own it, and the user sees it before it is committed.**

## 2. Mission archetypes from doctrine

### 2.1 The closed task vocabulary [V]

- **Patrols (FM 7-8, 1992, ch. 3).** Reconnaissance patrols: *area* ("a specified location and the area around it"), *zone*
  ("enemy, terrain, and routes within a specified zone") and *route* ("one route and all the adjacent terrain"). Combat
  patrols: *raid* and *ambush*, to "destroy or capture enemy soldiers or equipment; destroy installations, facilities, or key
  points; or harass enemy forces". There are also tracking patrols. Ambushes vary along three axes: hasty/deliberate,
  point/area, and linear/L-shaped. The objective rally point (ORP) sits "out of sight, sound, and small-arms range of the
  objective area" (FM 7-8 via 550cord.com mirror). FM 7-8 (22 Apr 1992, change 1 of 2001) was later superseded by FM 3-21.8
  [V-search].
- **Tactical mission tasks (FM 3-90, App. B).** Actions by friendly forces: attack-by-fire, breach, bypass, clear, control,
  counterreconnaissance, disengage, exfiltrate, follow and assume, follow and support, occupy, reduce, retain, secure, seize,
  support-by-fire. Effects on the enemy: block, canalize, contain, defeat, destroy, disrupt, fix, interdict, isolate, neutralize,
  suppress, turn. Each has a one-line definition; for example *interdict* "prevents, disrupts, or delays the enemy's use of an
  area or route" (globalsecurity.org mirror).
- **Orders format.** The five-paragraph order (SMEAC): Situation (enemy, friendly, attachments), Mission (who, what, when, where,
  why), Execution (intent, concept, tasks, coordinating instructions), Service Support / Admin & Logistics, and Command & Signal
  (Wikipedia, "Five paragraph order"). FM 101-5 carried this format through the 1980s [V-search].

**Use [I].** The doctrine enums (`ReconKind`, `AmbushKind`, `TacticalTask`) become *typed tags* on archetypes. The model can only
choose among them, never invent a task. Their definitions double as teaching text for the academy (doc 21 §D7) and as
briefing-template vocabulary (§7).

### 2.2 What every archetype must specify [I]

1. **Terrain needs.** Queries over a code-computed island feature index: town with ≥ N buildings, road segment ≥ L m,
   bridge, crossroads, forest edge, high ground with ≥ H m relative height, coast, airfield, open LZ ≥ 50 × 50 m, plus distance
   constraints between features. An archetype that cannot be satisfied on the chosen island is **not offered** (menus are
   computed, not filtered after the fact).
2. **Force roles, not classes.** The player group, friendly support and enemy elements are given as roles (leader, rifleman,
   MG, AT, medic, sniper, crew, pilot, officer, civilian), with counts as ranges and a unit budget. Classes are resolved from
   the loaded catalog by side and era (doc 17 §7.2), so generated missions work with any addon set.
3. **Phases.** Insert → approach → action → consolidate/exfil. Each phase compiles to waypoints plus triggers.
4. **Objectives** with their trigger recipe (area-clear, `!alive`, reach-area, timer, "joined group") and their `OBJ_n` lines.
5. **Outcome set** of 2–4 named outcomes with polarity (doc 19 `Polarity`). Outcome triggers call the generated finisher; the
   generator never emits END/LOOSE triggers itself (doc 19 C13). Every archetype keeps **at least one failure that
   happens while the player is alive**, because player death is routed to Retry and cannot branch (doc 18 §5). Typical alive
   failures: squad below X %, objective destroyed, timer expired, "retreat ordered" by HQ.
6. **Failure modes** that the generator must make *legible* (for example "the patrol spotted you → the QRF leaves the
   garrison"). Each failure mode needs a player-visible cause.
7. **Difficulty knobs.** Typed ranges with a difficulty weight: enemy count and skill, reinforcement timer, time of day,
   fog/overcast, friendly support, pool ammo, time limit, intel quality (how many enemy positions are pre-marked).
8. **Variation axes (structured unpredictability).** Booth's AI Director populates "not purely random, nor deterministically
   uniform": designer-bounded random intervals and positions, boss events "shuffled and dealt out" with "successive repeats …
   not allowed". His warning: "Even multiple sets of manually placed triggers/scripts fails", because players memorise them [V].
   Archetypes therefore declare choices (which of 3 routes the convoy takes, which 2 of 5 houses hold the HVT) that compile to
   **static alternatives in `mission.sqm`**, never runtime spawning (BriefingRoom's rule, doc 15 §8.1). The engine picks: a
   `random` roll in `init.sqs` `deleteVehicle`s the unpicked ones (init runs after units exist, so presence conditions cannot
   read it), or presence conditions read a var committed earlier (doc 19 F12). `random` is unseeded, so Retry may re-roll;
   native random-start markers/`placement`/`presence` (doc 04 §3.3) cannot correlate choices across groups [I].
9. **Briefing skeleton and flavour slots** (§7).
10. **Engine-risk flags.** Behaviours that need a Preview probe before we trust them in generated content [U]: AI convoy driving
    over bridges, AI helicopter landing at a generated LZ, destructibility of specific map objects (bridges), `join` of a
    rescued unit, and night-vision availability in the era catalog.

## 3. Quest structure research mapped to military missions

### 3.1 Doran & Parberry: motivations → strategies → actions [V]

Doran and Parberry analysed human-authored quests from EverQuest, World of Warcraft, Vanguard and EVE Online (UNT tech report
LARC-2011-02, March 2011; published at PCG 2011). The tech report text says "almost 3000" quests, while its Table 2 counts sum to
753; the ACM abstract says "over 750". They found **9 NPC motivations**. Each motivation has **2–7 strategies** ("verb-noun
pairs") of **1–6 actions**, drawn from **20 atomic actions** with pre/postconditions (capture, damage, defend, escort, exchange,
experiment, explore, gather, give, goto, kill, listen, read, repair, report, spy, stealth, take, use, plus ε). A BNF grammar
expands `<goto>`, `<learn>`, `<get>`, `<steal>`, `<spy>`, `<capture>` and `<kill>` recursively, for example
`<learn> ::= <goto> <subquest> listen`. The prototype generator (Prolog) picks among rules "based on what the player is assumed
to know and what the state of the game is", so it "avoids having the player go on a quest for something they already have".
The authors conclude that motivations are "essential for ensuring that quests appear intentional and appropriate rather than
randomly generated".

| Motivation (observed share) | Paper's strategies (abridged) | Military/OFP reading [I] |
| --- | --- | --- |
| Conquest (20.2%) | Attack enemy; steal stuff | Assault, raid, capture enemy equipment |
| Equipment (18.5%) | Deliver / steal / trade for supplies | Convoy escort, depot raid, supply exchange with partisans |
| Knowledge (18.3%) | Deliver item for study; spy; interview NPC; use item in field | Recon, observe-and-report, informant meeting, document grab |
| Protection (18.2%) | Attack threatening entities; treat/repair; create diversion; assemble fortification; guard entity | Spoiling attack, MEDEVAC/repair bridge, feint, dig in, defend/escort |
| Serenity (13.7%) | Revenge/justice; capture criminal; check on NPC; recover item; rescue captured NPC | Punitive raid, HVT snatch, contact a lost patrol, recover codes, POW/CSAR rescue |
| Reputation (6.5%) | Obtain rare items; kill enemies; visit dangerous place | Prove yourself to partisans; deep patrol |
| Wealth (2.0%) | Gather raw materials; steal valuables | Scavenge fuel and ammo (Resistance-style) |
| Comfort (1.6%) | Obtain luxuries; kill pests | Supply a village (hearts and minds) |
| Ability (1.1%) | Practice, research, assemble tool | Training / qualification mission |

**Use [I].**
- **Mission level.** A motivation plus a strategy gives each generated mission an in-fiction *why*, which is also the seed of its
  briefing Situation paragraph. The strategy's action sequence becomes the mission's **phases**: `goto` → a movement leg with
  waypoints, `spy` → observe an area for T seconds, `damage`/`kill` → a destroy trigger, `escort` → `join` plus a
  protect-alive trigger, `report` → return to HQ or send a radio item, `use` → place a charge.
- **Campaign level.** Expanding the grammar *across* nodes explains why missions follow each other. When `<learn>` is not ε
  (the player lacks the depot's location), code inserts a preceding recon node whose success sets `camp.intel ∋ depot_location`.
  The raid node then has a guard or a briefing variant that depends on it. Depth is capped at 2 so that campaigns do not
  explode: the paper's generated example is a nested `goto`/`learn`/`listen` chain three levels deep, which we judge tedious [I].
- **Weak models** only choose `(motivation, strategy)` from a table filtered by side and pattern slot. Code expands the rest.

### 3.2 Propp and arc shapes: beats and curves, not generators [V/I]

- Propp's 31 functions (absentation, interdiction, violation, villainy/lack, departure, struggle, victory, return, recognition,
  punishment, wedding, …) are a *sequence* grammar for Russian folk tales [V-search]. Gervás rebuilt a generator faithful to
  that corpus and warned that efforts "to generalize Propp's account to types of stories beyond the corpus that it arose from"
  lose "a number of the valuable intuitions" (Gervás, CMN 2013) [V]. **We therefore use a small military beat vocabulary only
  as optional node tags** that feed the flavour writer and the pacing check: *Call to arms, Insertion, First blood, Setback,
  Captured/Cut off, Rescue, Betrayal revealed, Turning point, Final assault, Homecoming/Award* [I].
- **Arc shapes.** Reagan et al. (arXiv 1606.07772) found that the emotional arcs of Project Gutenberg fiction are "dominated by
  six basic shapes" [V]: rags to riches (rise), tragedy (fall), man in a hole (fall–rise), Icarus (rise–fall), Cinderella
  (rise–fall–rise) and Oedipus (fall–rise–fall) (names [V-search]). A 2026 generation pipeline keeps a narrative archetype as
  "soft Rise/Fall states" that condition "encounter composition, objectives, rewards, and runtime difficulty adaptation"
  (Wen et al., arXiv 2605.01245) [V]. **Adopt** an `ArcShape` enum per campaign. It sets the fortune target of each act
  (friendly territory, supplies, squad size) and so constrains which archetypes and outcomes the skeleton prefers. CWC's
  invasion → Montignac defeat → counter-offensive reads as "man in a hole"; Red Hammer's loyal soldier who deserts and turns on
  Guba reads as fall–rise [I].

## 4. Branching patterns versus the 7-ending engine

### 4.1 Ashwell's standard patterns [V], rated for this engine [I]

Sam Kabo Ashwell, "Standard Patterns in Choice-Based Games" (2015-01-26); quotes [V], ratings [I].

| Pattern | Ashwell's gist | Engine fit (doc 18/19) | Authoring cost | Verdict |
| --- | --- | --- | --- | --- |
| Time cave | "many, many endings", little re-merging | Legal, but every leaf is a full mission | Exponential | **Reject** (tiny "what if" epilogues only) |
| Gauntlet | "relatively linear central thread, pruned by branches which end in death, backtracking, or quick rejoining" | Natural; failure edges use `lost`; player death never branches | ~n | **Adopt** as P1, with failure-forward detours |
| Branch and bottleneck | branches "regularly rejoin"; "almost always rely on heavy use of state-tracking" | Ideal: sockets ≤ 7, rejoin nodes vary content by state | ~n·1.3–1.6 | **Default** (P2) |
| Quest | "distinct branches", "tightly-grouped clusters of nodes" by geography | Maps to islands/regions (Theatre view) | Medium | Folded into P5 |
| Open map | "static geography", "reversible" travel, extensive state-tracking | Hub + routers + sector vars | Medium | **Adopt** as P5 |
| Sorting hat | branches early, then "which major branch the player gets assigned to"; "write several different games" | Early Choice node; long parallel legs | High | **Adopt** as P3 (Resistance precedent), with a length cap |
| Floating modules | "no trunk"; encounters emerge "through state, or perhaps randomly" | Side-op pool behind Choice/Hub nodes with guards | Low per module | **Adopt** as P6 (side ops) |
| Loop and grow | thread "loops around, over and over", "new options may be unlocked" | Only a direct self-loop adds no book row (doc 18 §4); hub → spoke → hub adds a row per visit, plus router rows | Low–medium | **Adopt** inside P4 |

### 4.2 Foldback, state tracking and "defensive" text

- **Foldback** (branches that reconverge) cuts content but, in Crawford's critique, "robs choices of meaning" when overused
  (*Chris Crawford on Interactive Storytelling*, ch. "Simple Strategies That Don't Work") [V-search].
- **The cure is state that shows up later.** Quality-based narrative, per Emily Short, unlocks storylets by "numerical variables
  that can go up or down during play". It handles acquisition "in any sequence" with a single gated storylet instead of
  combinatorial branches (Short, 2016-04-12) [V]. Kreminski & Wardrip-Fruin map the storylet design space (ICIDS 2018) [V].
  In inkle's *Sorcery!*, content is "atomic": each narrative atom is guarded by preconditions, and "defensive logic" keeps the
  story coherent whatever order it happened in (Ingold, GDC 2017) [V-search].
- **Engine mapping [I].** A reconverged (bottleneck) mission differs by state at no router cost, through presence conditions
  (doc 19 F12), `OBJ_` briefing variants (F9), intro variants (`initintro.sqs`) and in-mission radio lines guarded in CXL. So
  **explicit branches are spent only on big forks** (allegiance, a lost battle, a captured hero); everything else is
  state-tracked variation. The C18/C21 lints (doc 19) make the "defensive logic" checkable: no line names a dead character, and
  every reachable state bundle has text.

### 4.3 Budget arithmetic [V/I]

- **Precedent.** Resistance has 20 authored missions; "due to branching paths you will only ever play 18 in one campaign". It
  has two branch points plus bad endings [V]. That is a ~1.1 authored/played ratio, and its replay value came from state
  (pool, squad), not from branch count [I].
- **Recommendation [I].** Target authored/played ≤ 1.5 by default, and at most 2–3 distinct successors per mission outside
  finales (engine limit 7, doc 18 §4). Each extra successor costs a mission. Each extra *debrief narrative* costs a socket
  (≤ 7, doc 19 F10), and finer variation goes to `OBJ_` lines. Show the counter "missions authored / missions per playthrough /
  endings" live in the pattern picker.

## 5. Persistent state that is fun

### 5.1 Precedents [V/V-search]

- **Resistance.** The player must "provide the weapons for the guerilla fighters (mostly from defeated Soviet forces)" and
  "minimize the losses of men and equipment as both are available in limited numbers". The squad has "up to 11 AI controlled
  members" (Wikipedia) [V]. Players attack "Soviet bases and convoys to obtain weapons, ammunition, and tanks" [V]. One
  walkthrough: "Having everyone wiped out makes things much harder for you in future missions"; "keep the two medics alive";
  new recruits "improve in intelligence and effectiveness" over time; replaying a mission loses the pool [V].
- **CWC (1985).** Early squad deaths did not persist (doc 18 §10). Its memorable persistence was narrative (Armstrong's
  capture and rescue by the FIA), not systemic.
- **Community.** OFPWiz's *Dynamic Campaign* (OFPEC entry dated 2007) carries, in its reviewer's words, "weapons, vehicles, men,
  and the status of all of the above between one mission to the next"; "Size of enemy force in the sector carries over" [V].
- **Beyond OFP.** XCOM-style permadeath makes losses hurt through attachment to named soldiers [V-search]. DCS Liberation keeps
  named pilots who can die (doc 19 §2.2).

### 5.2 Persistence modules [I]

A module is a reusable bundle: declared variables (doc 19 §4), effects on outcome edges, guards and presence conditions, text
hooks, and its own lints. Patterns recommend modules; the user toggles them.

| Module | State (doc 19 types) | Fun lever | Visibility hooks (mandatory) | Anti-frustration floor |
| --- | --- | --- | --- | --- |
| **Roster** | `CharacterDecl` × 3–8, status ladder, xp, rank. The engine has no roster: flat `saveVar` scalars plus versioned `saveIdentity`/`saveStatus` blobs, and pre-placed non-playable slots with presence conditions (doc 19 §4.3, F12) | Attachment; "who comes along" | Briefing roster line, debrief KIA line, the character's own radio lines | Replacements after N missions (recruit with low skill that improves); `MustSurvive` only for story-critical people |
| **Reputation** | `Int(-10..=10)` per faction (locals, partisans, HQ) | Doors open or close | Briefing tone variant; civilians' presence; partisan support in missions | A reputation repair side op always exists |
| **Weapon pool** | Native weapon/magazine pool (doc 18 §6.4); changes only in the finisher | Scarcity and scavenging | Briefing gear screen (`weaponPool = 1`) | Minimum loadout guaranteed per mission |
| **Vehicle pool** | No engine pool: `[classOrdinal, count]` rows via `saveVar`, copy-then-assign (doc 19 §4.3); pre-placed empty vehicles with presence conditions, not runtime spawning | "We have one T-72 left" | Presence of pooled vehicles at start | Never gate the critical path on a vehicle |
| **Intel** | `Set<Enum>` of intel items (`in` on 1.99 is [U], doc 19 F4) | Recon pays off | Pre-marked enemy positions, revealed routes, extra `OBJ_` hint | Missing intel raises difficulty, never blocks |
| **Supplies** | `Int` counters (ammo, fuel, medical) | Logistics choices | Ammo crates present; medic availability | Clamp at a playable minimum |
| **Doom clock** | `Int` turns left (doc 19 §6.8 Strategic tier) | Urgency, trade-offs | Briefing countdown line | Visible from turn 1; never hidden |
| **Consequence echoes** | Flags with a `surfaces_at` node set | "The bridge you blew stopped their armour" | A line or a changed force in a later mission | Must surface within ≤ 2 nodes on every path (CF04) |

**Design rules [I].**
- **No invisible state.** Every persistent variable must be *read* by at least one player-visible element (briefing line,
  presence, force size, dialogue) on every path where it could have changed (lint CF04). This goes beyond C07 (unused
  variables).
- **Failure forward.** Alive failures route to a harder or different mission, not to "game over". CWC: a failed assault on
  Montignac leads to "Strange Meeting" instead of "After Montignac", and both rejoin at "Rescue" [V]. Resistance:
  failing "Information" leads to the harder "Occupation (1)", with a T-72 and a T-80 to face [V].
- **Death spirals are bugs.** The simulator runs a pessimistic policy (always the worst outcome). If a path reaches a node
  whose knobs are infeasible (for example "requires ≥ 1 AT team" but the roster only has riflemen), it flags CF07.
- **Choices must differ.** If two options of a Choice node produce identical successor *and* identical state, the choice is fake
  (CF05), unless it is tagged `flavour_only`.

### 5.3 Pacing and difficulty across a campaign [V/I]

- **Sawtooth.** The Elimination analysis "corroborates that the level generator creates a sawtooth-shaped difficulty curve, as
  intended" (Khalifa, Gopstein, Togelius, arXiv 1905.06379; a puzzle game's level sequence) [V]. Our campaign reading [I]: the
  curve rises within an act, dips at the start of the next, and peaks higher.
- **Peaks need valleys.** Booth, *The AI Systems of Left 4 Dead* (Valve, 2009): "Constant, unchanging combat is fatiguing";
  "Long periods of inactivity are boring". The Director cycles **Build Up → Sustain Peak (3–5 s) → Peak Fade → Relax
  (30–45 s)**, and the "algorithm adjusts pacing, not difficulty" [V]. PaceMaker (Geheeb et al., arXiv 2408.15001) lets
  designers select paths on a directed graph and see "intensity and gameplay category" diagrams per path [V]. Flow needs
  challenge balanced against skill (Chen, CACM 50(4), 2007) [V-search].
- **Campaign mapping [I].** Every skeleton node carries `Intensity ∈ {Relax, Build, Peak, Finale}`. Relax nodes are cutscenes,
  hubs, recon or "scavenge" missions. Archetypes declare an intensity band. The intensity strip for each explored path (§8) is
  drawn from the simulator. Lints: CF01 (≥ 3 consecutive Peak nodes), CF02 (no Relax/Build after a Finale-class set piece
  before the next Peak), and CF03 (the same archetype 3× in a row on any path). Difficulty knobs scale with node depth plus the
  current fortune from the arc shape, never with hidden randomness.

## 6. What made the classic OFP campaigns memorable

| Campaign | Structure and persistence | Memorable devices | Lessons for templates [I] |
| --- | --- | --- | --- |
| **Cold War Crisis (1985)** | Four protagonists across roles: Armstrong (infantry), Hammer (tank commander), Nichols (helicopter then A-10 pilot), Gastovski (special forces, sabotage) (Wikipedia) [V]. Mostly linear (one walkthrough lists 41 missions). Branch after "Montignac Must Fall": seizing the town → "After Montignac" (a scripted, unwinnable withdrawal), a failed assault → "Strange Meeting"; both lead to "Rescue" [V] | A big combined-arms offensive that can fail; capture, then rescue by the FIA; the invasion-to-counter-invasion arc [V] | **Role rotation** (P7) gives variety cheaply; a **set-piece defeat as the pivot**; failure-forward instead of game over |
| **Resistance** | 20 missions, 18 per run. "Crossroad": turning the rebel in leads to "Contact", fighting leads to "No Turning Back" (Wikipedia lists three options: betray, negotiate, fight). "Information": success spares you a T-72 and T-80 in "Occupation (2)", failure leads to "Occupation (1)". Bad endings [V]. Weapon pool, squad of up to 11, captured equipment [V] | Guerrilla scarcity; scavenging; attachment to medics; a moral choice early | **Sorting hat with remerge** (P3); **success/failure → difficulty variant** (cheap, readable); pools as the core loop |
| **Red Hammer** | Soviet perspective on "the same conflict"; Lukin goes from loyal soldier to deserter who "joins the resistance" and finally arrests Guba's loyalists (Wikipedia) [V] | Playing the other side; a moral turn | **Perspective flip** as a pattern parameter; arc "fall–rise" |
| **Community (OFPEC sample)** | Of the 10 OFP campaigns on the depot's first page, none advertises branching or persistence. *Grunt ONE*: 16 linked missions, "multiple ways" to reach objectives, no traditional branching. *Too Young To Die*: 8 long missions with "surprising twists mid-game" [V]. OFPWiz *Dynamic Campaign*: full carry-over of weapons, vehicles and men [V] | Cutscenes (*SharkEye II*: "around 30 mins"), long set-piece missions, twists; voice acting (unverified) | Branching RPG-state campaigns were **rare** in the OFP community [I from a small sample, U overall]. That is the product's differentiator. Twists and set pieces matter more than branch count |
| **Arma 3 Combat Patrol (BI)** | Scenario generated "in every village based on a map's key points"; a chain of randomly selected objectives; enemy reinforcements triggered by alarm (Buchta, 2016-12-20) [V] | Replayable, location-agnostic missions | Precedent for **terrain-indexed archetype placement** and alarm → QRF as a failure mode |

## 7. Briefings, dialogue and radio in the era's style

### 7.1 Briefing = SMEAC poured into OFP's sections [I on the mapping, V on the sections]

The engine's `briefing.html` sections are `Main` (notes), `Plan`, `OBJ_<n>` (objectives with status) and
`Debriefing:End1..6/Loser`. Links `marker:<name>` pan the map (doc 04 §6) [V]. State variants use hidden `OBJ_` sections
(doc 19 F9/F10) [V].

| SMEAC paragraph | OFP section | Code-owned content | Model flavour slot |
| --- | --- | --- | --- |
| Situation | `Main` (1st paragraph) | Enemy/friendly facts from the mission (unit roles, counts as words, places) | ≤ 90 words, tone enum (doc 21 §D8) |
| Mission | `Plan` (1st line) | Who/what/where/when/why from archetype + motivation | None (template sentence) |
| Execution | `Plan` (numbered phases) | One line per phase with `marker:` links | ≤ 25 words per phase (optional colour) |
| Tasks | `OBJ_n` | Objective lines from the archetype | Optional ≤ 12-word rephrase |
| Service support | `Plan` tail | Pool gear, supplies, medic availability (modules) | None |
| Command & signal | `Plan` tail | Callsigns, radio items (Alpha…Juliet, doc 19 F11), HQ callsign | None |
| Debrief | `Debriefing:*` + revealed `OBJ_` lines | Outcome facts, KIA list, state deltas | ≤ 60 words per narrative |

Whether the shipped 1985 missions write `Main` as first-person diary notes or as orders is **[U]**. Survey the installed
missions locally (never commit their text) and encode the result as a style preset.

### 7.2 Radio procedure and callsigns

- **Prowords (ACP 125 via Wikipedia) [V].** OVER ("a response *is* necessary"), OUT ("no answer is required or expected"), with
  the rule that OVER and OUT are never used together; ROGER (received, not "yes"); WILCO ("… understand it, and will comply");
  SAY AGAIN / I SAY AGAIN; CORRECTION; BREAK; WAIT / WAIT OUT; THIS IS; RADIO CHECK. The US Army's current reference is
  ATP 6-02.53 [V-search].
- **Spot reports.** SALUTE: Size, Activity, Location, Unit/Uniform, Time, Equipment [V-search].
- **OFP conventions.** Group IDs are a letter word plus a colour (`setGroupId ["Delta","GroupColor4"]`, OFPEC COMREF)
  [V-search]. Abstract HQ speakers are `[side,"HQ"]` (aliases `"Base"`, `"PAPA_BEAR"`), shown as "PAPA_BEAR", and
  `[side,"airbase"]`, shown as "BASE FIREFLY"; a mission renames them only through the stringtable keys `STR_CFG_PAPABEAR`
  and `STR_CFG_FIREFLYBASE`, so at most two custom HQ callsigns exist per mission (toadlife.net tutorial) [V]. Behaviour on
  1.99 is **[U]** until probed; code reads the tokens from the loaded config.

### 7.3 Line templates [I]

Each `RadioLineKind` has a fixed skeleton. **Code** fills callsigns, grids, numbers, unit words and times. The **model** may
fill only the `{colour}` slot (≤ 8 words) and choose among ≤ 3 variants.

| Kind | Skeleton | Engine target |
| --- | --- | --- |
| Tasking (HQ) | `{to}, this is {hq}. {task_sentence}. {colour} Over.` | `sideRadio`/`sideChat` + stringtable |
| Contact (SALUTE) | `{hq}, this is {me}. Contact. {size} {unit}, {activity}, grid {grid}. Over.` | `groupChat`/`sideChat` |
| Acknowledge | `Roger, {me} out.` / `Wilco, out.` | same |
| SITREP | `{hq}, {me}. Objective {obj} {status}. {casualty_clause}. Over.` | same |
| Casualty | `{name} is down!` / `We lost {name}.` (roster-aware) | `groupChat` |
| Request extract | `{hq}, {me}, requesting extraction at {lz}. Over.` | radio item + trigger |
| Banter | `{speaker}: {colour}` (≤ 12 words; persona sheet) | `groupChat`/`titleText` |

- **Gates** (doc 21 §D8): speakers ⊆ roster (alive on this path, C18); entities ⊆ mission dossier; digits only from code;
  an era "forbid" list (GPS, drone, mobile phone, …); `sideChat`/`titleText` length caps; no `:` or `"` inside SQS-bound text
  (doc 19 F6).
- **Voice consistency.** A character sheet has traits, flaw, desire, fear and speech style (doc 17 §9). The model sees the
  sheet plus one line kind at a time, never the whole campaign.
- **State-variant lines** are narrative atoms with CXL preconditions (the *Sorcery!* approach, §4.2). For example
  `when alive(roster.dimitri): "Dimitri's team will cover the north road."`, else a variant without him. Coverage is lint C21.

## 8. Making the generation flow fun

### 8.1 Evidence: Casual Creators [V]

Compton & Mateas define a Casual Creator as "an interactive system that encourages the fast, confident, and pleasurable
exploration of a possibility space, resulting in the creation or discovery of surprising new artifacts that bring feelings of
pride, ownership, and creativity" (ICCC 2015). Their patterns:
- **Instant feedback.**
- **Chorus line.** Show many generated examples at once.
- **Simulation and approximating feedback.** "Only the perception of progress is necessary".
- **Entertaining evaluations.**
- **No blank canvas.** "The first move is the hardest", so reduce it to "accept the prompt, or discard it".
- **Limiting actions to encourage exploration.** The paper names "choice paralysis or hard failures" as flow breakers.
- **Mutant shopping.** Pick among suggested neighbours.
- **Modifying the meaningful.** Give the user high-level handles.
- **Saving and sharing; hosted communities; modding.**

They also name an anti-pattern, **"1000 bowls of oatmeal"**: artifacts that are "technically distinct to the computer, but
perceived by humans as uniform". Mixed-initiative co-creativity, where human and computer both contribute proactively, is the
framing of Yannakakis, Liapis & Alexopoulos (FDG 2014) [V-search].

### 8.2 The "director's desk" flow [I]

1. **No blank canvas.** The first screen is a pre-filled intent card: side, island, era, length, tone and persistence modules,
   with the "inferred" chips of doc 21 §D2. A random "prompt of the day" is available.
2. **Mutant shopping on outlines.** Code instantiates **3 skeletons** from different patterns or seeds. The model writes a
   ≤ 40-word pitch for each. The user picks one, or asks for "more like #2" (same pattern, new seed).
3. **Surprise-me dice with pins.** Any field (pattern, arc, an act's twist, a node's archetype, a location) can be re-rolled by
   code's seeded RNG. Pinned fields survive re-rolls. Dice never call the model, so they are instant and work offline.
4. **Twist cards.** For each act, code computes up to 5 legal twists from the beat vocabulary and the modules: "Captured", "The
   bridge is out", "The partisans want proof", "A squadmate deserts", "HQ orders a retreat". The model may only rank them.
5. **Consequence map (Theatre view, doc 19 §6.7).** Nodes sit on the island. Arrows are coloured by which variables they write.
   Hovering a variable lights up every place it surfaces (the CF04 view).
6. **Chorus line of playthroughs.** The simulator runs 50 seeded journeys under persona policies (cautious, reckless,
   completionist, random) and shows endings reached, survivors per character, pool at the finale and the intensity strip per
   path. That is instant, simulated feedback on a large artifact [V pattern, I application]. Persona narration by the model is
   optional flavour (doc 21 §D9).
7. **Entertaining evaluations that never gate.** An era "staff officer" persona comments ("Command notes: three night raids
   running; the men are tired"). Comments are derived from lint data and are never acceptance criteria (doc 21 §D3, §D5).
8. **Playable slice first.** Mission 1 is generated fully and is Preview-ready while the other nodes are still skeletons, so the
   user plays within minutes. Other missions are built on demand or in the background, and each is shown as it completes.
9. **Modifying the meaningful.** Per-node handles speak in fiction terms ("harder", "quieter", "more armour", "night",
   "civilians present") and map to typed knobs and modifiers. Raw fields stay available in the mission editor.
10. **Avoid tedium.** At most 3 questions before the first visible artifact; every question has a default; long operations show
    per-node progress; no step waits on a model call longer than its budget without offering "keep the default".

## 9. Proposal: the typed content library

### 9.1 Rust type sketches (crate `ofp-campaign-content`; proposal-only)

```rust
// ── Identifiers ─────────────────────────────────────────────────────────
// Newtypes per AGENTS.md: derive Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash,
// #[inline] from_raw/to_raw, Display ("arch#3"). NodeId/VarId/CharacterId come from doc 19.
pub struct ArchetypeId(u16);  pub struct PatternId(u16);  pub struct ModuleId(u16);
pub struct FlavorSlotId(u32); pub struct KnobKey(u16);    pub struct TwistId(u16);

// ── Vocabularies (closed enums: the only words a model may choose) ──────
pub enum Motivation { Knowledge, Comfort, Reputation, Serenity, Protection, Conquest, Wealth, Ability, Equipment }
pub enum TacticalTask { Recon(ReconKind), Ambush(AmbushKind), Raid, Seize, Secure, Clear, Retain, Delay, Destroy,
                        Interdict, Block, Exfiltrate, Escort, Rescue, Capture } // Delay (a retrograde form), Escort, Rescue
                        // and Capture are game-level additions, not FM 3-90 App. B tasks
pub enum ReconKind { Area, Zone, Route }
pub struct AmbushKind { deliberate: bool, area: bool, l_shaped: bool }
pub enum Intensity { Relax, Build, Peak, Finale }
pub enum ArcShape { RagsToRiches, Tragedy, ManInAHole, Icarus, Cinderella, Oedipus }
pub enum Beat { CallToArms, Insertion, FirstBlood, Setback, CutOff, Rescue, Betrayal, TurningPoint, FinalAssault, Homecoming }

// ── Mission archetype (data + one deterministic generator per archetype) ─
pub struct MissionArchetype {
    id: ArchetypeId, key: Ident,                 // "ambush", "town_assault", ...
    task: TacticalTask, motivations: Vec<(Motivation, StrategyKey)>, // Doran & Parberry rows this archetype realises
    intensity: RangeInclusive<Intensity>,
    terrain: Vec<TerrainNeed>,                   // ALL must resolve on the island or the archetype is not offered
    forces: ForceSpec,                           // roles and ranges; classes resolved from the runtime catalog
    phases: Vec<PhaseTemplate>,                  // insert → approach → action → exfil
    objectives: Vec<ObjectiveTemplate>,          // trigger recipe + OBJ_ line template
    outcomes: OutcomeSet,                        // invariant: 2..=4 outcomes, ≥1 alive-failure, fits 7 sockets
    failure_modes: Vec<FailureMode>,             // each with a player-visible cause
    knobs: Vec<KnobSpec>,                        // typed ranges with difficulty weights
    variation: Vec<VariationAxis>,               // seeded static alternatives (routes, HVT house, ambush sites)
    modifiers_allowed: EnumSet<Modifier>,        // Night, Fog, Stealth, Timed, Undermanned, CiviliansPresent
    briefing: BriefingSkeleton,                  // SMEAC → Main/Plan/OBJ_ (§7.1)
    flavor: Vec<FlavorSlotSpec>,
    probes: Vec<ProbeId>,                        // engine behaviours to confirm in Preview before "verified" status
    generator: GeneratorRef,                     // built-in Rust fn, or a T1 WASM plugin generator (doc 22)
}
pub enum TerrainNeed {
    Town { min_buildings: u16 }, RoadSegment { min_len_m: u32 }, Bridge, Crossroads, ForestEdge { min_len_m: u32 },
    HighGround { min_rel_height_m: u16 }, Coast, Airfield, OpenLz { min_side_m: u16 },
    Distance { a: FeatureRef, b: FeatureRef, range_m: RangeInclusive<u32> },
}
pub struct ForceSpec { player: GroupSpec, friendly: Vec<GroupSpec>, enemy: Vec<EnemyElement>, civilians: CivPresence,
                       unit_budget: u16 }
pub struct GroupSpec { roles: Vec<(Role, RangeInclusive<u8>)>, vehicle: Option<VehicleRole> }
pub enum Role { Leader, Rifleman, Autorifleman, AntiTank, Medic, Sniper, Crew, Pilot, Officer, Engineer, Civilian }
pub struct OutcomeTemplate { key: Ident, polarity: Polarity /* doc 19 */, raised_by: RaiseRule,
                             payload: Vec<PayloadTemplate>, debrief_facts: Vec<FactRef> }
pub enum RaiseRule { AllObjectives, ObjectiveFailed(ObjKey), SquadBelowPct(u8), TimerExpired, ReachedArea(AreaKey),
                     RetreatOrdered, TargetEscaped }
pub struct KnobSpec { key: KnobKey, ty: KnobType /* IntRange | EnumSet */, default: KnobValue, difficulty_weight: i8,
                      fiction_label: &'static str /* "more armour" */ }

// ── Flavour slots: the ONLY free text a model writes ──────────────────
pub struct FlavorSlotSpec { id: FlavorSlotId, kind: FlavorKind, max_chars: u16, tone: ToneRef,
                            facts: FactScope /* entities the text may mention */, forbid: ForbidListRef }
pub enum FlavorKind { MissionTitle, Pitch, Situation, PhaseColour, ObjectiveRephrase, Radio(RadioLineKind),
                      Debrief(OutcomeKeyRef), Bark(CharacterId) }

// ── Campaign patterns and persistence modules ────────────────────────
pub struct CampaignPattern { id: PatternId, key: Ident, family: AshwellFamily, params: Vec<PatternParam>,
                             recommended_modules: Vec<ModuleId>, builder: PatternBuilderRef }
pub struct Skeleton { arc: ArcShape, nodes: Vec<SkeletonNode>, edges: Vec<SkeletonEdge>, modules: Vec<ModuleInstance> }
pub struct SkeletonNode { role: NodeRole /* Opener|Spine|BranchLeg|Bottleneck|Pivot|SideOp|Hub|Choice|Finale|Ending */,
                          intensity: Intensity, beat: Option<Beat>,
                          archetype: ArchetypeSlot /* Fixed(ArchetypeId) | ChooseFrom(Vec<ArchetypeId>) */,
                          region: Option<RegionRef>, protagonist: Option<CharacterId> }
pub enum PersistenceModule { Roster { size: RangeInclusive<u8>, death: DeathPolicy, replacements: bool },
                             Reputation { factions: Vec<Ident> }, WeaponPool { scarcity: Scarcity },
                             VehiclePool { classes_from: CatalogFilter }, Intel { items: Vec<Ident> },
                             Supplies { kinds: Vec<Ident> }, DoomClock { turns: u8 }, Echoes { max_delay_nodes: u8 } }

// ── Provenance for partial regeneration (never clobber human work) ──
pub enum Origin { Generated { generator: GeneratorRef, seed: u64, inputs: InputsHash },
                  ModelFlavor { slot: FlavorSlotId, model: ModelRef, prompt: PromptHash }, Human }
pub struct Tracked<T> { value: T, origin: Origin, pinned: bool } // regeneration skips Human or pinned unless forced
```

All archetypes and patterns are **data plus a deterministic builder**. They ship as built-ins and can be extended through T0
content packs (patterns, text templates, twist cards) or T1 WASM generators (new archetypes) under doc 22's rules [I].

### 9.2 Deterministic generators versus model flavour slots [I]

| Artifact | Deterministic generator | Model slot (bounded) |
| --- | --- | --- |
| Skeleton graph, sockets, routers | `PatternBuilder` + doc 19 compiler | none |
| Archetype choice per node | Feasibility filter and variety rules | pick 1 of ≤ 5, or code dice |
| Site binding | Terrain index query → ranked candidates | pick 1 of ≤ 5 named sites |
| Units, waypoints, triggers, markers | Archetype generator (seeded) | none |
| Variables, guards, effects | Modules + pattern | optional single CXL guard (parsed, typed) |
| Names (operation, characters) | Era name lists per side | optional pick or ≤ 3-word codename |
| Briefing, radio, debrief | Skeleton sentences + facts | slots in §7 with caps and fact scopes |
| Twists, pitches | Legal twist set from beats and modules | rank twists; ≤ 40-word pitch |

### 9.3 Initial catalog: 16 mission archetypes [I, doctrine tags V]

Shared across all rows: player death means Retry (never an outcome); every row has ≥ 1 alive failure; "QRF" means an enemy
reaction force released by an alarm trigger (a Combat Patrol-style failure mode).

| # | Archetype (task; motivation) | Terrain needs | Forces (player / enemy) | Objectives → outcomes | Failure modes | Key knobs / variation |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | **Recon** (Recon area/route/zone; Knowledge·Spy) | OP on high ground/forest edge 300–800 m from target; covered route | 2–4-man team / garrison, patrols, QRF | Reach OP, observe N sites for T s, return → *Full intel*, *Partial intel*, *Compromised* (retreat) | Detected → QRF; team < 50 % | patrol density, enemy skill, time of day; which sites are live |
| 2 | **Combat patrol** (Secure; Protection) | 3–5 checkpoints on roads/villages | Squad / 1–3 random contacts | Visit checkpoints in order → *Cleared*, *Cleared with losses*, *Aborted* | Squad below threshold | contact count and strength; route choice |
| 3 | **Ambush** (Ambush point/area, linear/L; Conquest·Attack) | Road segment ≥ 300 m with cover on one or two sides | Squad + MG/AT / convoy or patrol with escort | Occupy kill zone before T, destroy ≥ x %, withdraw → *Annihilated*, *Partial* (survivors alert next node), *Failed* | Early detection; convoy reroutes | convoy size/armour, start window; which of 2 routes |
| 4 | **Raid** (Raid; Conquest/Equipment·Steal supplies) | Compound/depot with ORP 300–600 m | Assault + support + security / garrison, alarm QRF | Destroy targets, optionally load loot → *Success + loot* (pool Δ), *Success*, *Repulsed* | Alarm; QRF timer | garrison size, QRF delay, night; target positions |
| 5 | **Sabotage** (Destroy/Interdict; Protection·Create diversion) | Bridge/fuel dump/radar/launcher + infiltration route | 2–6 SF with charges / guards, patrols | Place charge, exfil, detonate → *Destroyed*, *Destroyed, compromised*, *Failed* | Guards alerted; target not destructible **[U probe]** | guard count, time window |
| 6 | **Defend** (Retain/Secure; Protection·Guard entity) | Defensible town edge/hill/bridge with 1–3 approach roads | Platoon + statics / 2–4 waves | Hold until T → *Held*, *Held, heavy losses*, *Ordered retreat*, *Overrun* | Position lost | wave count and mix, prep time, reinforcement ETA; which avenue attacks |
| 7 | **Delay / fighting withdrawal** (Delay/Disengage; Protection) | 2–3 phase lines along a road toward friendly lines | Squad/section + transport / superior advancing force | Hold PL1 until T1, fall back, reach lines → *Delayed*, *Partial*, *Cut off* (→ E&E node) | Encircled | enemy speed, PL spacing, transport |
| 8 | **Town assault** (Clear/Seize; Conquest·Attack enemy) | Town ≥ N buildings; 2 approach axes | Platoon + armour support / garrison + MG nests | Clear area, seize key building → *Seized*, *Seized, heavy losses*, *Repulsed* | Assault stalls; timer | garrison size, armour, civilians (reputation); garrison layout |
| 9 | **Convoy escort** (Escort; Equipment·Deliver supplies) | Road A→B 2–6 km with 1–3 chokepoints | Escort + trucks / ambush teams at k chokepoints | ≥ x trucks arrive → *All through*, *Partial* (supplies scaled), *Lost* | Trucks destroyed; AI driving **[U probe]** | ambush count/AT, truck count; which chokepoints |
| 10 | **Convoy interdiction** (Interdict; Conquest·Steal stuff) | 2–3 candidate enemy routes | Team + AT / convoy | Find and stop the convoy → *Captured cargo*, *Destroyed*, *Missed* | Wrong route; convoy escapes | intel reveals route (Intel module hook) |
| 11 | **Rescue / CSAR** (Rescue; Serenity·Rescue captured NPC) | Crash site or camp + extraction point | Squad (+ helo) / converging search teams | Reach survivor, survivor joins, extract → *Rescued*, *Rescued wounded*, *Survivor lost*, *Aborted* | Search teams arrive; `join` **[U probe]** | search timer, distance, survivor slowed |
| 12 | **HVT snatch** (Capture; Serenity·Capture criminal) | Village house/HQ + exit route | 3–6 team / officer + guards | Officer alive in the player group or area, then exfil → *Captured*, *Killed* (partial intel), *Escaped* | Alarm → target flees | guard count; which of k houses |
| 13 | **Exfiltration** (Exfiltrate; Protection) | Start deep; LZ/beach at D km | Team (maybe carrying wounded) / pursuers | Reach LZ within window → *Extracted*, *Extracted with losses*, *Missed extraction* (→ E&E) | Pursuit catches up | distance, pursuit timer, LZ window |
| 14 | **Escape & evade / breakout** (Exfiltrate/Breach; Serenity) | Camp/encirclement + route to friendlies or partisans | Player starts unarmed or cut off / search teams | Break out, arm from a cache, reach contact → *Friendlies*, *Partisans* (reputation +, may switch branch), *Recaptured* | Recapture | search density, cache presence; which contact point |
| 15 | **Armoured engagement** (Destroy/Block; Conquest) | Open rolling ground; hull-down ridges | Tank platoon / armour waves + AT infantry | Repel or destroy → *Victory*, *Pyrrhic* (vehicle pool −), *Withdraw* | Platoon destroyed | enemy mix, ammo, AT teams; wave axes |
| 16 | **Air assault** (Seize; Conquest) | Flat open LZ ≥ 50 × 50 m near an objective (hill/town) | Squad in transport helo + gunship / defenders, possible AA | Land, seize, hold for relief → *Seized*, *Hot LZ, seized late*, *Aborted* | LZ unusable; AI landing **[U probe]** | AA presence, relief ETA; which LZ |

**Modifiers** can be applied to any compatible archetype: *Night* (time and NVG availability from the era catalog **[U]**),
*Fog/Overcast*, *Stealth* (penalty on detection), *Timed*, *Undermanned* (roster losses), *Civilians present* (reputation
effects), *Captured gear only* (loadouts stripped, scavenge; never `clearWeaponPool`, which would destroy campaign state, and
how to suspend pool gear selection for one mission while `weaponPool` is campaign-wide is **[U]**, doc 18 §2). "Night assault on the town" = archetype 8 + Night. That is exactly the
kind of refinement the user asks for ("make mission 4 a night assault").

### 9.4 Initial catalog: 8 campaign structure patterns [I]

| # | Pattern (Ashwell family) | Parameters (defaults) | Skeleton sketch | Modules | Missions authored / played; endings | Engine cost |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | **Gauntlet with failure-forward** (Gauntlet) | `n` 6–12 (8); failure policy ∈ {RetryOnly, Detour, HarderNext}; detours 1–3 | A linear spine; alive failures go to a detour (rescue/E&E) or a hard variant, then rejoin | Roster (light), Intel | n + detours / n; 1–2 | Sockets only |
| P2 | **Branch and bottleneck** (default) | acts 2–4 (3); width per act 2–3; bottleneck per act 1 | Act = opener → 2–3 legs chosen by outcome or choice → bottleneck with state variants → next act | any | ≈ 1.3–1.6× played; 2–3 | Sockets; rare routers |
| P3 | **Sorting hat with remerge** (Sorting hat) | allegiances 2–3; leg length 2–4; remerge ∈ {none, betray-back, finale} | An early Choice (Resistance "Crossroad") → parallel legs → optional remerge | Reputation, Roster | 1.5–2×; 2–4 | One Choice mission; routers for the remerge |
| P4 | **Base camp: hub + loop and grow** (Loop and grow) | spokes 4–8; turns T 6–10; unlock rules; finale gate | Hub mission ↔ operation cards; state unlocks new cards; finale when gate holds or the clock runs out | Pool, Supplies, Doom clock, Roster | spokes + finale / T; 2–3 | Hub + routers (doc 19 §7.2) |
| P5 | **Theatre / sector control** (Open map, Quest) | sectors 3–6 per island; enemy strength per sector; win at k sectors | Sectors with ownership and strength vars; each turn picks an adjacent sector; the archetype comes from the sector's terrain | Pool, Vehicle pool, Intel | sectors × 1–2 / turns; 2–3 | Routers per turn; `.sqc` growth lint C20 |
| P6 | **Side-op pool** (Floating modules) | pool 3–8 side ops with guards; offered at Choice points | Mixed into P1/P2/P4: between spine missions, a Choice offers the ops whose preconditions hold | Reputation, Intel, Echoes | +pool / +k; 0 extra | ≤ 10 radio choices, listed only while the player leads the group (doc 19 F11) |
| P7 | **Multi-perspective rotation** (CWC) | threads 2–4 (by role: infantry, armour, air, SF; or other side); interleave | Threads interleave; cross-thread effects (the tank thread's result sets the infantry thread's support) | Echoes, Intel | ≈ played; 1–2 | Sockets; state only |
| P8 | **Countdown offensive** (Loop and grow + open map) | turns T 5–8; enemy offensive strength S; ops weaken S | Choose ops each turn (hub); the finale's difficulty is f(S) | Doom clock, Intel, Supplies | pool + finale / T; 2–3 by S | Hub + routers |

**Arc shape is orthogonal** to all patterns: `ArcShape` sets per-act fortune targets (§3.2). "Fall and rise" (man in a hole)
is the default for invasion stories, and P7 with a perspective flip reproduces the CWC + Red Hammer pairing [I]. Time cave is
deliberately absent (§4.1).

### 9.5 Plugging into the campaign designer (doc 19) and the harness

**The workflow is a typed state machine owned by code** (AGENTS.md invariant; doc 21 §D4 atoms). Each state stores its artifact
in the harness, not in the model's context. The model sees one menu or one slot at a time. **Proposal-only, to reconcile:**
doc 25 §4 already defines the flow (`CampaignFlow`, stages S0–S9, which build missions before writing text and cap menus at 7).
`ContentStage` below is this doc's content-side view; it should become doc 25's stage payloads, not a second state machine.

```rust
pub enum ContentStage {
    Intent(IntentDraft),            // S1  side, islands, era, length, tone, modules (chips; doc 21 §D2)
    Outline(Vec<SkeletonOption>),   // S2  code builds 3 skeletons; model pitches/ranks; user picks
    Arc(ArcDraft),                  // S3  ArcShape + per-act twist from ≤5 legal cards
    Cast(CastDraft),                // S4  roster from Roster module: names (era lists), roles, persona sheets
    Nodes(NodeAssignments),         // S5  per node: archetype (≤5 feasible) + site (≤5 candidates) + modifiers
    Wired(CampaignModel),           // S6  modules → vars/guards/effects; doc 19 model (no model call)
    Verified(VerifiedModel),        // S7  C01–C21 + CF01–CF12 + simulator chorus line (no model call)
    Flavored(FlavoredModel),        // S8  slots filled one at a time; gates §7.3
    Built(BuiltCampaign),           // S9  per-node archetype generators → missions; mission validators; compile
    Done(Summary),                  // S10 Preview mission 1 offered immediately (playable slice first)
}
```

| Step | Model output type | Menu or slot size | Validator | On failure (bounded) |
| --- | --- | --- | --- | --- |
| S1 | `IntentFill` (enums + literal spans) | closed vocab | span ⊆ request; values in vocab | Ask one computed question |
| S2 | `Rank([u8; 3])` + `Pitch(≤ 40 words)` ×3 | 3 | indices valid; pitch fact scope = skeleton | Pitches become code templates |
| S3 | `Pick(u8)` per act | ≤ 5 twists | legal for modules and beats | Code dice |
| S4 | `Pick(name index)`, persona colour ≤ 20 words | era list | name unique; forbid list | Code default |
| S5 | `Pick(u8)` archetype, `Pick(u8)` site | ≤ 5 each | feasibility, variety (CF03), intensity band | Code picks the top-ranked option |
| S6–S7 | none | — | doc 19 checker, lints, simulator | Fix-it list shown to the user; the model may explain lints |
| S8 | `Slot(text)` | 1 slot | length, fact scope, forbid list, SQS-safe chars | ≤ 2 repairs, then the skeleton sentence |
| S9 | none | — | mission validators (doc 15 §9), compile verify (doc 19 §7.1) | Re-seed that node's generator (≤ 3), then report |

- **Stronger models** may return a whole `CampaignPlan { pattern, arc, nodes: Vec<(ArchetypeId, SiteRef, Vec<Modifier>)> }`
  in one call. It is validated by exactly the same S2–S7 checks and applied as one doc 19 `propose_branch` ChangeSet [I].
- **Partial regeneration** is a re-entry into S5–S9 for one node or edge. For "Make mission 4 a night assault" the intent
  router maps the request to `node.retemplate(n4, TownAssault, +Night)`. S5 checks feasibility, S6–S7 re-verify downstream
  nodes, S8 regenerates only that node's `ModelFlavor` slots, and `Human` or pinned items are skipped (the `Tracked<T>` rule).
  "Add a branch if the pilot dies" becomes a Roster status guard on the next edge plus a new leg from the P2 builder; this
  works only for an NPC pilot, because player death cannot branch (doc 18 §5); for a player pilot code offers an alive-failure
  substitute (e.g. "aircraft crippled → forced landing" raised while the player lives).
  "Rewrite the sergeant's lines" regenerates S8 slots whose speaker is the sergeant. Every one of these is a single undoable
  transaction [I].
- **Effort levels** (doc 21 §D5) change the number of outline candidates (1/3/5), whether pitches are model-written or
  templated, and the repair budget. They never change the validators.

## 10. Content and fun lints (proposed; complement doc 19 C01–C21) [I]

| ID | Severity | Rule |
| --- | --- | --- |
| CF01 | warn | ≥ 3 consecutive `Peak`/`Finale` nodes on any explored path (fatigue) |
| CF02 | info | No `Relax`/`Build` node between two set-piece peaks (sawtooth broken) |
| CF03 | warn | The same archetype 3× in a row on a path, or one archetype > 40 % of a path (oatmeal) |
| CF04 | error (generated) / warn (hand-made) | A declared persistent variable written on a path is never surfaced to the player within ≤ 2 nodes (invisible state). Skips compiler housekeeping (`cmp_run`, …) and imported `Opaque` vars, so Preserve-mode imports (doc 19 §7.6) still compile |
| CF05 | warn | A Choice whose options give identical successor and state (fake choice) unless tagged `flavour_only` |
| CF06 | warn | A roster member with no lines, no briefing mention and no slot on some path (unused attachment) |
| CF07 | warn | Pessimistic-policy path reaches a node whose force or pool requirements are unmeetable (death spiral) |
| CF08 | info | An ending reached by < 2 % of the chorus-line runs across all personas (probably unreachable in practice) |
| CF09 | error | An archetype's terrain needs are unresolved or its site is unreachable on the island |
| CF10 | info | A multi-perspective campaign in which one thread has > 2× the missions of another |
| CF11 | warn | A text slot mentions an entity outside its fact scope, or a forbidden era word |
| CF12 | info | An archetype with an open `[U]` probe used in a campaign marked "verified" |

## Open questions

1. **Engine probes for archetypes [U].** AI convoy driving across bridges, AI helicopter landing at generated LZs, `join` of a
   rescued unit, destructibility of bridges and other map objects, and NVG availability in the 1985 catalog, all on 1.99. These
   gate archetypes 5, 9, 11 and 16 and the Night modifier. They extend doc 19 Open question 1.
2. **The island feature index [U].** Which data source (world config, road network, object lists) gives towns, roads, bridges,
   forest edges and flat LZs reliably for the stock islands and addon islands, and at what cost? Needs a design doc of its own.
3. **Shipped-mission style survey [U].** What register do the stock 1985 and Resistance briefings use (diary notes versus
   orders), and what are their typical lengths? This must be a local-only survey; no game text is committed.
4. **Grid reference format [U].** How the engine formats map grids in radio and briefing text, so that code, not the model,
   produces them.
5. **Community branching prevalence [U].** Our sample of OFPEC campaigns shows little branching. A broader survey (ofpisnotdead
   file mirrors, forum archives) would sharpen the differentiation claim.
6. **Weak-model menu sizes [U].** Are 3 or 5 options the right cap for the target local tiers (doc 14)? Doc 25 §5.1 allows
   ≤ 7; one number must win. This needs a small bench of pick-from-menu accuracy per step.
7. **Chorus-line cost [I/U].** 50 simulated journeys are cheap for the simulator, but model-narrated personas are not. Should
   narration be sampled (for example 3 of the 50)?
8. **Doran grammar depth [I].** Is a depth cap of 2 the right balance between purposeful campaign dependencies and tedious
   chains? This needs playtesting.

## Sources

**Repository docs:** doc 04 §6 (briefing sections); doc 14 (model tiers); doc 15 §3.1, §8.1, §8.4, §9 (Ghostwriter pattern,
BriefingRoom, text targets, evaluation); doc 17 §6, §7.2, §9 (scene templates, class overlay, character sheets); doc 18 §4–§6,
§10 (engine campaign facts, community precedents); doc 19 (typed model, CXL, lints C01–C21, simulator, compiler, AI actions);
doc 21 §D2–§D9 (intent fill, idea cards, workflow atoms, effort, wizard, dialogue gates, play-tester); doc 22 (plugin tiers);
doc 25 §4–§5 (workflow state machine, step shapes).

**Web (accessed 2026-09-26; fetched unless marked "search"):**

- Doran, J. & Parberry, I., *A Prototype Quest Generator Based on a Structural Analysis of Quests from Four MMORPGs*, UNT
  LARC-2011-02 (Mar 2011): <https://ianparberry.com/techreports/LARC-2011-02.pdf>; PCG 2011 record:
  <https://dl.acm.org/doi/10.1145/2000919.2000920> (search)
- Ashwell, S. K., "Standard Patterns in Choice-Based Games": <https://heterogenoustasks.wordpress.com/2015/01/26/standard-patterns-in-choice-based-games/>
- Short, E., "Beyond Branching: Quality-Based, Salience-Based, and Waypoint Narrative Structures" (2016-04-12):
  <https://emshort.blog/2016/04/12/beyond-branching-quality-based-and-salience-based-narrative-structures/>
- Kreminski, M. & Wardrip-Fruin, N., "Sketching a Map of the Storylets Design Space", ICIDS 2018, LNCS 11318 (search):
  <https://mkremins.github.io/publications/Storylets_SketchingAMap.pdf>
- Ingold, J., "Narrative Sorcery: Coherent Storytelling in an Open World", GDC 2017 (search):
  <https://www.gdcvault.com/play/1023989/Narrative-Sorcery-Coherent-Storytelling-in>
- Crawford, C., *Chris Crawford on Interactive Storytelling* (search):
  <https://books.google.com/books/about/Chris_Crawford_on_Interactive_Storytelli.html?id=68GCG4jVZ9EC>
- Gervás, P., "Propp's Morphology of the Folk Tale as a Grammar for Generation", CMN 2013, OASIcs 32:
  <https://drops.dagstuhl.de/entities/document/10.4230/OASIcs.CMN.2013.106>
- Reagan, A. J. et al., "The emotional arcs of stories are dominated by six basic shapes", arXiv 1606.07772:
  <https://arxiv.org/abs/1606.07772>; arc names (search): <https://nofilmschool.com/story-arcs>
- Wen, Y. et al., "The Garden of Forking Paths: Threading Narrative Archetype as a Semantic Signal Through Gameplay Planning",
  arXiv 2605.01245: <https://arxiv.org/abs/2605.01245>
- Booth, M., *The AI Systems of Left 4 Dead* (Valve, 2009): <https://steamcdn-a.akamaihd.net/apps/valve/2009/ai_systems_of_l4d_mike_booth.pdf>
- Khalifa, A., Gopstein, D., Togelius, J., "ELIMINATION from Design to Analysis", arXiv 1905.06379: <https://arxiv.org/abs/1905.06379>
- Geheeb, J., Dyrda, D., Geheeb, S., "PaceMaker: A Practical Tool for Pacing Video Games", arXiv 2408.15001:
  <https://arxiv.org/abs/2408.15001>
- Chen, J., "Flow in Games (and Everything Else)", CACM 50(4), 2007 (search): <https://dl.acm.org/doi/10.1145/1232743.1232769>
- Compton, K. & Mateas, M., "Casual Creators", ICCC 2015: <https://computationalcreativity.net/iccc2015/proceedings/10_2Compton.pdf>
- Yannakakis, G. N., Liapis, A., Alexopoulos, C., "Mixed-initiative co-creativity", FDG 2014 (search):
  <https://www.um.edu.mt/library/oar/bitstream/123456789/29459/1/Mixed-initiative_co-creativity.pdf>
- FM 7-8 *Infantry Rifle Platoon and Squad*, ch. 3 (mirror): <https://550cord.com/infantry-rifle-platoon-squad-fm-7-8/fm-7-8-chapter-3-patrolling/>;
  supersession note (search): <https://www.globalsecurity.org/military/library/policy/army/fm/3-21-8/>
- FM 3-90 App. B, *Tactical Mission Tasks* (mirror): <https://www.globalsecurity.org/military/library/policy/army/fm/3-90/appb.htm>
- Five paragraph order: <https://en.wikipedia.org/wiki/Five_paragraph_order>
- Procedure words (ACP 125): <https://en.wikipedia.org/wiki/Procedure_word>; ATP 6-02.53 (search):
  <https://armypubs.army.mil/ProductMaps/PubForm/Details.aspx?PUB_ID=1008613>; SALUTE (search):
  <https://www.globalsecurity.org/military/library/report/call/call_96-1_ct3-4art.htm>
- OFP group IDs (search): <https://www.ofpec.com/COMREF/index.php?action=details&game=All&id=304>; HQ callsigns (fetched
  2026-09-27): <http://ofp.toadlife.net/downloads/tutorials/Custom_HQ_Callsigns_in_your_missions.html>
- *Operation Flashpoint: Cold War Crisis*: <https://en.wikipedia.org/wiki/Operation_Flashpoint:_Cold_War_Crisis>; missions 7a/7b
  (2026-09-27): <https://www.gamerevolution.com/guides/29719-operation-flashpoint-walkthrough>,
  <https://forums.bohemia.net/forums/topic/50439-so-whats-up-with-this-strange-meeting-mission/>; StrategyWiki (search)
- *Operation Flashpoint: Resistance*: <https://en.wikipedia.org/wiki/Operation_Flashpoint:_Resistance>; walkthrough (mission list,
  branches, persistence advice): <https://www.supercheats.com/pc/walkthroughs/operationflashpointresistance-walkthrough01.txt>
- *Operation Flashpoint: Red Hammer*: <https://en.wikipedia.org/wiki/Operation_Flashpoint:_Red_Hammer>
- OFPEC Missions Depot, OFP campaigns list: <https://www.ofpec.com/missions_depot/index.php?action=list&cat=ca&game=OFP>; details
  pages `action=details&id=1` (*Grunt ONE*), `id=7` (*Too Young To Die*), `id=107` (OFPWiz *Dynamic Campaign*)
- ofpisnotdead.com (no curated campaign list found): <https://ofpisnotdead.com/>; Buchta, I., "OPREP – Combat Patrol"
  (2016-12-20): <https://dev.arma3.com/post/oprep-combat-patrol>
- XCOM/Darkest Dungeon permadeath attachment (search, low authority): <https://jonaspastoors.substack.com/p/xcom-2-vs-darkest-dungeon>

**Access notes.** The BI wiki, StrategyWiki, GameFAQs, GameSpot, neoseeker, the Fandom wikis and namu.wiki returned
403/402/429 or DNS errors on 2026-09-26/27; claims that depend on them are marked **[V-search]** or **[U]**.

## Verification notes

Adversarial review, 2026-09-27 (PDFs text-extracted locally). TL;DR, §1–§10, Open questions and Sources were complete.

- **Confirmed [V].** Doran & Parberry (LARC-2011-02; PCG 2011, Bordeaux): 9 motivations, Table 2 shares (counts sum to 753),
  2–7 strategies of 1–6 actions, 20 actions incl. ε, both quotes. Ashwell's 8 patterns; Compton & Mateas (incl. "1000 bowls
  of oatmeal"); Booth's quotes and timings; FM 7-8, FM 3-90, ACP 125 wording; Short, Gervás, Reagan, Wen et al., PaceMaker,
  Elimination, Combat Patrol; CWC's protagonists; Red Hammer; Resistance's 20/18 missions, branches and advice; OFPEC sample.
- **Corrected.** CWC: failing "Montignac Must Fall" leads to "Strange Meeting", not "Rescue"; both legs rejoin at "Rescue"
  (TL;DR, §5.2, §6). Doc 18 §10 repeats the old claim and needs the same fix. The HQ callsign override uses `STR_CFG_PAPABEAR`/
  `STR_CFG_FIREFLYBASE`, not same-name keys. Tightened WILCO, the Booth and Ashwell quotes, and the "tedious chain" claim ([I]).
- **Product fit.** Roster/vehicle pool: the engine has neither (saveVar, `saveIdentity`/`saveStatus`, presence slots); variation
  picks run in-engine; outcomes via the finisher (C13); book rows; radio leader rule; no player-death branch; no pool clearing;
  CF04 spares Preserve imports; non-doctrine tasks marked; §9.5 defers to doc 25 §4.
- **Residual.** Doc 21 (`21-agent-doctrine.md`) is not in the tree, so its §D2–§D9 citations are unchecked. The Crawford,
  Ingold, Chen, FM 101-5 and XCOM claims remain [V-search]. Menu caps (5 here, 7 in doc 25) are unresolved (Open question 6).
