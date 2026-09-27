# Replayability: every run a new adventure

Research doc 43 for Plotroom (`ofp-editor`). Research date: 2026-09-27. Audience: contributors and LLM coding agents. This file is meant to be read on its own.
Question answered (owner observation, paraphrased): in Sid Meier's games (XCOM, Civilization) every new game is a new adventure. How do we make that first-class for missions and campaigns made with Plotroom, both when a campaign is **built** (the same brief with a new seed gives a different campaign) and when it is **played** (each playthrough of one mission or campaign file differs)?

**Status.** Proposal-only. Every type, code, threshold, name and UX in §2–§8 is **[I]** unless a line says otherwise. Every number is a placeholder for the balance lab (doc 29 §5.2) or for playtests to tune.
**Epistemic legend.** **[V]** verified: engine facts by static reading of the pinned source ("by reading" means nothing was run in a game), web facts against a fetched page, corpus facts by a re-run count. **[V-search]** seen only in a search snippet, because the page refused the fetch. **[I]** our inference or proposal. **[U]** unknown; needs a probe (§8.3) or a source. Claims about the 1.99 executable rest on the derived CWR/CE source, string scans of the 1.99 binaries and corpus use, so they are [I] unless marked.
**Citation aliases.** `CWR:` = `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/`. `EVAL:` = `BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/`. `RND:` = `BohemiaInteractive/CWR@ffc61838b7:engine/Random/`. `CE:` = `ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/`. CE's `Random/` files hash identical to CWR's (SHA-256), so `RND:` facts hold for both. **Profiles** are doc 19's `TargetProfile` values, written here as Cwa199, Cwr and Ce.
**Codes (provisional; the design round assigns final numbers).** Principles `RP1`–`RP9`, variation axes `VX01`–`VX12`, lints `VY01`–`VY24`, probes `P-R1`–`P-R12`, phases `RV0`–`RV4`, acceptance tests `RAT1`–`RAT18`. A grep of `docs/` finds none of these families, and none collides with the codes listed in the headers of docs 34, 36, 37, 39, 41 and 42. DG005 proposes the registry that assigns final codes. **T0** here is doc 25's no-model tier (doc 14's T0), except in §3.7's "T0 pack data", which means doc 22's data-pack plugin tier; DG005 records that label collision.
**Relation to sibling docs.** Doc 18 owns the campaign engine facts (saveVar, history rows, restarts, `objects.sav`). Doc 19 owns the campaign model, simulator and Path Explorer; doc 25 the weak-model harness, seeds, decision records and T0 (the no-model tier); doc 26 the archetypes, variation axes (§2.2 items 7–8) and the director's desk (§8.2); doc 28 the fun lints; doc 29 the strategic layer (stored-LCG rolls, `RollSource`, `SideOpGenerator`, DoomClock, balance lab); doc 34 many small clocks, twists, Mole and Nemesis; doc 36 the Civilization lessons and the engagement-ethics checklist (cv43); doc 38 the workflow journal and item seeds; doc 40 token costs; doc 41 weather and time; doc 27 mod-set fingerprints. This doc adds the model that ties them together: roll scopes, per-profile lowerings, MP-safe rolling, seed codes, remix and variety metrics. It repeats sibling content only where a rule depends on it.
**Hygiene.** All text is our own. Quotes from public sources are short and attributed. The corpus is the owner's local install, read by uncommitted scratch scripts; only aggregate counts appear here, and no game or community mission text is quoted.

## TL;DR

- **A new adventure is a new situation inside rules the player trusts** (§1). XCOM, Left 4 Dead, Slay the Spire, Spelunky, Into the Breach, RimWorld and Hades agree: keep the rules, the arc shape and the anchors fixed; vary the situation, the people, the enemy's plan and the forced choices; make every roll visible. Randomising building blocks alone gave maps that "still mostly played the same" (Firaxis, GDC 2018) [V].
- **Only perceptible, play-changing variety counts** (the oatmeal trap, §1.3). Every procedural template varies at least 2 gameplay axes, decoration is budgeted separately, and an axis the player never sees does not count (VY13, VY14).
- **The engine's `random` cannot be seeded, saved or shared** [V by reading]. It walks a fixed 32,768-entry table from a clock-seeded index shared with AI, weather and timers, so one roll carries at most 15 bits, several consecutive draws carry no more between them, and draws after a save load are not the ones the original run saw (§2.1). A roll that must survive a restart, be shared or resist save-scumming runs on doc 29's stored LCG in campaign variables.
- **Every roll declares a scope**: `Build` (baked by the generator), `PerCampaign`, `PerTurn` (at a commit) or `PerAttempt` (by the engine, at every load). The scope decides the lowering and the restart behaviour (§2.2). Run-time scopes multiply compiled content. Build scope costs nothing at run time, but everyone who plays that file gets the same result.
- **Correlated one-of-N variants have four lowerings** (§2.4): a stored campaign roll read by `presenceCondition` (every mission after the bootstrap row), a "roller" object whose presence condition rolls once at load (standalone and MP; probe P-R1), `init.sqs` pruning (SP fallback) and lobby parameters (MP). Every pool also has a default variant for the paths that run without campaign variables (debriefing Restart, intros) [V by reading].
- **Anti-scum by construction** (§2.5). The next mission's variants are pre-rolled in the predecessor's finisher, so restart-from-row, Retry and Replay replay the same variant; this answers doc 19 open question 7. In-mission events read stored slots, never `random`, so save-look-reload cannot re-deal a card. The one hole is the debriefing Restart, which runs the whole mission without campaign variables: it shows the default variant and must not commit (doc 29 row 13's guard) [V by reading].
- **Multiplayer: the server rolls, numbers are broadcast, and every machine applies them locally** (§2.6). Only the server creates mission objects, so presence and placement are already consistent. `random` in `init.sqs`, unit init lines or triggers diverges per machine, and marker commands change only the local map [V by reading on Cwr and Ce; I on Cwa199]. On Cwa199, broadcast numbers only.
- **Budgets come from the corpus** (§2.7): ≤ 63 groups per side summed over every variant (the load path refuses a file over it, and a campaign then books the mission as lost [V by reading]), a worst-case variant no larger than the largest shipped official mission, and pool overhead ≤ 35 %. Over half of the official campaign missions already randomise (presence, placement, start markers), but always per attempt, unseeded and uncorrelated [V].
- **Three reproducibility guarantees, stated honestly** (§3.1). A seed code reproduces a no-model campaign exactly; a replay record (seed code plus journaled picks) reproduces a model-assisted one; the same seed with fresh model calls does **not**, because no cloud model API promises deterministic sampling [V].
- **Seed codes carry a generator epoch and fingerprints** (§3.3). Remix re-rolls only unpinned, unedited fields at a chosen scope and level (§3.5). Modifiers are typed, labelled and split into build and run layers (§3.6). Doc 36 cv43 bans dailies, so challenges become a never-expiring numbered catalogue, which the owner allowed on 2026-09-27 with no calendar, week index, streak, reward or reminder (§3.7; OWQ-20 (a), D039).
- **Variety is measured, not asserted** (§4): expressive-range analysis over N seeds (archetype sequences, sites, branch shapes, cast and twists, text), a Variety Budget meter, and the balance lab run across seeds so that no seed is unfair.
- **Code owns every die** (§7). The model picks among code-computed variation recipes, names things and writes flavour. Seeds, pools, weights, decks and checks are deterministic code, so a no-model run has the same variety.

## 1. What creates the "new adventure" feeling

### 1.1 Evidence

| # | Source | What it shows | Plotroom rule |
| --- | --- | --- | --- |
| 1 | Hess, "Plot and Parcel", GDC 2018 (Firaxis) [V] | XCOM: EU had about 80 hand-made maps and EW about 30 more, "mostly custom art", judged "super expensive" and "not enough". XCOM 2 shipped 80 plots (hand-made master layouts) with 200+ parcels in three footprint classes (12×12, 12×24, 24×24) placed with random facing, and 450 road pieces (PCPs) whose variants are picked at random on load | **Site Kits**: per island, an authored skeleton of roads, LZs, approach lanes and sockets with footprint classes, filled with compositions (compound, checkpoint, depot, camp) that each allow 2–4 facings. The seed fills sockets at build time; at run time the mission only selects compiled layers (doc 26 §2.2, doc 29 `SideOpGenerator`, doc 34 cw07) |
| 2 | Same slides [V]; Foertsch via GameRant 2015 [V; referent I] | The first plot evaluation: "Maps still mostly played the same". Later passes varied facings, driveways, zones and random starts; late feedback still wanted visual variety and got a new plot type. "Random's not fun" (art director Foertsch); the "Enemy Unknown" he contrasts most likely means the 1994 game, since the 2012 one used hand-built maps | The oatmeal rule (RP3, VY13): shuffled parts are not variety unless play changes |
| 3 | Hess [V]; Booth, "The AI Systems of Left 4 Dead", 2009 [V] | XCOM 2 added less-procedural "Golden Path" missions with fixed narrative elements, and lists the storytelling costs of procedural levels; the slides end on "How procedural does it need to be?". L4D exempts boss encounters from adaptive pacing | Story ops, the finale and landmark ops are authored and pinned with a frozen seed (RP1). Cinematics anchor to objects present in every variant (VY21) |
| 4 | Booth [V] | Static placement gets memorised, and "Even multiple sets of manually placed triggers/scripts fails". The remedy is "structured unpredictability": several bounded random functions stacked (mob spawns every 90–180 s) | Mission variety comes from several independent, bounded axes (§2.3), each a typed range knob (doc 26 §2.2 item 7) |
| 5 | Booth [V] | Designers place several candidate weapon caches and the Director picks which exist. Boss events (Tank, Witch, Nothing) are shuffled and dealt, with no repeat in a row | Static alternatives: pre-place and validate every variant, select by presence, never spawn at run time (doc 26 §2.2 item 8). Decks are shuffle bags with a no-repeat field and relief ("nothing happens") cards (VX08) |
| 6 | Booth [V] | Adaptive pacing changes frequency, not amplitude, so peaks come at different times and places on every run; a crude intensity estimate is enough | An optional reinforcement pacer (VX07) moves timing only; the difficulty preset owns strength [U: probe P-R11] |
| 7 | UFOpaedia, Dark Events (XCOM 2) [V] | About 3 enemy programs per month (2 at the start), one usually hidden unless the player pays intel; one can be prevented by a Guerrilla Op, the rest take effect. 15 in the base game; the War of the Chosen count is unconfirmed, and recurrence within a campaign is snippet-level only | Enemy Programs deck (doc 34 §1.2), §5. Sizing the deck above the number of draws, or allowing repeats with a cooldown, is our own rule, not an XCOM precedent |
| 8 | UFOpaedia, abductions (EU 2012) and Avatar Project (XCOM 2) [V] | Abductions offer 2 or 3 countries with different rewards; ignored ones panic. The Avatar bar has 12 blocks, facilities add blocks, story actions remove them, and a full bar starts a countdown to defeat | Doc 29's 2–3-card triage is the cheapest divergence engine; the DoomClock's feeding regions are seeded (§5) |
| 9 | UFOpaedia, War of the Chosen [V]; Solomon, GamesBeat 2017 [V] | Each campaign generates its Chosen with random strengths and weaknesses; they grow, gather intel on XCOM and return until their stronghold falls. "We wanted to give XCOM a personality. That's what the Chosen bring." | Nemesis traits per campaign (VX09, §5) |
| 10 | UFOpaedia, Second Wave (EU/EW) [V]; Vigaroe (WotC) [V] | Player-chosen campaign modifiers; several randomise the economy, rookie stats or rewards; some unlock only after a victory. EW's "Save Scum" re-rolls the shot seed on save, which implies the default keeps it across reloads | Typed modifiers (§3.6). Stored rolls replay on restart by default; re-rolling is opt-in (§2.5) |
| 11 | Johnson 2011, via doc 36 §3.1 row 16 [V] | Civ III's preserved random seed "made some fans feel cheated", so it became a start-of-game option | Same default and same opt-in as row 10 |
| 12 | Steam and CivFanatics threads on Civ V and VI [V] | Civ V places starts by a switchable start bias; Civ VI has one seed for the map and another for civilisations and city-states; a seed reproduces a map only with the same world settings | A visible, switchable Start Bias rule; split seeds (§3.2) |
| 13 | Minecraft Wiki [V]; Factorio wiki [V] | A generator update changes what a seed makes. Factorio's map exchange string packs game version, all settings, the seed and a CRC32 | Seed codes carry an epoch, settings and fingerprints (§3.3) |
| 14 | Rose, Game Developer 2013 [V] | Spelunky's Daily Challenge: everyone plays the same levels once; single-player turned into shared competition and stories | Shareable operation codes, without dailies (§3.7) |
| 15 | RimWorld wiki, AI Storytellers [V] | Storytellers are pacing and variance presets; "The difficulty is adjusted separately from the storyteller". Commitment mode (one save, no reload) is a separate switch | An Event pacing preset (Classic / Calm / Chaotic) separate from difficulty and from Ironman (§3.6) |
| 16 | Sylvester, "The Simulation Dream", 2013 [V] | Players co-author stories from random outcomes, but "For apophenia to work, players have to see and understand interesting things happening"; unseen complexity "degraded into noise" | Every roll surfaces as a readable cause (RP6, VY14) |
| 17 | Kasavin, Game Developer 2020 (Hades) [V] | Reactivity: conditions over the run state select weighted pre-written events, and death moves the story on | State-variant lines over rolled facts and run history (doc 26 §7); optional memory across playthroughs (§5) |
| 18 | Ma, Game Developer 2018 (Into the Breach) [V]; Wikipedia [V] | "less randomness than FTL", telegraphed enemy attacks, procedural scenarios on preset maps | Randomness lives in the situation and is disclosed before the player commits (doc 36 cv09, SL30) |
| 19 | slaythespire.wiki.gg, Map Generation [V]; Wikipedia, FTL [V] | Weighted room types, fixed anchor floors, Unknown rooms resolved on entry. FTL was tuned to about a 10 % win rate | Weighted node types with fixed anchors in the campaign graph, branching ≤ 3; "?" intel nodes resolved from a stored roll at commit; an explicit success band per preset |
| 20 | Kazemi, "Spelunky Generator Lessons" [V]; Yu via GameDiscoverCo 2021 [V] | The level generator guarantees a solution path through a 4×4 room grid first, then fills the rest. Yu: randomness gives "free value", but only systems and rules lift it above "a glorified slot machine" | Generator order: the critical path first (RP7) |
| 21 | Compton via Vice 2016 [V]; Short 2016 [V] | "10,000 bowls of plain oatmeal" are unique and still the same; "Perceptual uniqueness is the real metric". Oatmeal-avoidance depends on whether generation "is connected to anything mechanical" | RP3; the metrics of §4 |
| 22 | Solomon, Game Developer 2016 [V]; Tetris wiki [V] | Displayed odds feel lower than true odds ("We're human beings--we see patterns."); "If you shave off the lows, a lot of the time you're shaving off the highs". A bag randomiser bounds droughts | Shuffle bags; bad-luck protection only on loss-side rolls (doc 36 cv07); displayed numbers never lie; hidden help is disclosed (cv43 item 8) |

### 1.2 Principles

| # | Principle | Consequence |
| --- | --- | --- |
| RP1 | **Authored structure, procedural situation** | Rules, arc shape, anchors and site kits stay fixed; situation, cast, enemy plan and micro-placement vary. Every template and module declares Fixed and Varied fields, and human edits and pins become Fixed automatically |
| RP2 | **Spend variety from the top of the perception ranking** | (1) story situation and stakes; (2) people (cast, nemesis); (3) objective verb and site; (4) approach geometry; (5) conditions (weather, time); (6) micro-placement. Two seeds of one brief should differ on ≥ 3 of dimensions 1–4 |
| RP3 | **No oatmeal** | An axis counts only if the player can perceive it and it changes play. Each procedural template varies ≥ 2 of: player start or ingress, objective location, enemy posture zone, QRF origin (VY13) |
| RP4 | **Fair surprises** | Foreseeable or discoverable (foreshadowing or intel), worst case validated, counterable, explained afterwards (VY15, VY16) |
| RP5 | **Every roll has a scope and a source** | Rolls that feed state, guards or commits are stored, never engine `random` (doc 29 SL11, VY01) |
| RP6 | **Every roll is readable** | It surfaces as a radio line, briefing variant, debrief line or marker (doc 28 FP45, doc 19 C21, VY14) |
| RP7 | **The critical path is never random** | Generators guarantee ingress, objective, exfil, a stealth and a loud route, and evac after the alarm first (doc 34 cw07, doc 28 FP12), then add optional content |
| RP8 | **Cost is shown next to what it buys** | The Variety Budget meter (§4.4) sets layers, lines and Preview runs against the number of meaningfully different runs |
| RP9 | **Code owns the dice** | The model names and writes; it never picks probabilities, seeds or weights (§7) |

### 1.3 The oatmeal trap

A generator can produce thousands of mathematically distinct missions that play the same: a patrol shifted 30 m, the same objective under a different cloud. Firaxis's first plot evaluation found exactly this, and Compton's and Short's critiques explain why: novelty counts only when the player perceives it and it is tied to mechanics [V]. Plotroom therefore budgets variety by axis: gameplay axes (start, objective location, posture zone, QRF origin, route) are counted; visual axes (site class, time of day, weather) are budgeted separately; micro jitter is free but earns no credit. "Show me 3 options" uses farthest-point selection across seeds over typed features, and doc 28 TX05 extends from text to structural similarity (§4.2) [I].

### 1.4 "A new adventure" as a testable property

In the Sid Meier and roguelite sense, a new adventure means a new starting situation, new people, a new enemy plan, forced choices that fork the story, and a world that visibly remembers, all inside rules the player trusts [I, synthesis of §1.1]. The balance lab gets a campaign-level **New Adventure check** (RAT17): across seeds of one brief it expects a different opening situation, ≥ 50 % different roster identities, different nemesis traits or programs deck, a different first triage offer, and ≥ 1 memory callback line per act; the rule set and difficulty band stay constant. It feeds doc 28's R6 rubric row. Its **run-time twin** covers the case players meet most: one compiled campaign file under N play seeds, walked in the simulator (every run-time roll is stored-LCG code, so it can be). It drops the build-only dimensions (skeleton, and cast while VX11 is Build) and expects a different first triage offer, different nemesis traits or program-card order, and a different selected variant on ≥ 50 % of the ops that carry a pool [I; placeholder]. A file that passes the build check but fails the twin is a "new campaign per seed, same run per file" and the Variety panel says so.

## 2. Run-time variety

### 2.1 Engine facts that shape every design

| Fact | Evidence | Status | Consequence |
| --- | --- | --- | --- |
| `random x` returns a table value × x. The table has 32,768 entries, built once by ISAAC (seed 120) and masked to 15 bits; an index advances on every draw. Our port reproduces the ISAAC reference vector and finds no zero in the table (min 1, max 32767, 20,794 distinct values), so `random x` lies in [x/32768, 32767x/32768]. The draw is `table[index++]`, so the whole generator state is the 15-bit index: a second draw in the same script is the next table entry and adds no entropy. The table is a fixed sample, not an ideal uniform: over it, `presence` 0.4 passes 39.6 % of start indices, 0.5 passes 49.7 % and 0.7 passes 70.2 % | `EVAL:express.cpp#L535-L539`, `#L1166`; `RND:randomGen.cpp#L15-L23`, `#L141-L154`; `RND:randomGen.hpp#L6-L26` | V by reading and port; Cwa199 table P-R3 | Probabilities are quantised to 1/32768; `random n` never returns n and is not an integer (VY06); the simulator uses the ported table, not an ideal uniform |
| One process-wide generator, seeded from the tick count at construction and re-seeded in `World::World` with tick count + wall-clock seconds. The World is created once, so the stream runs on across missions. No script command sets the seed (the test-harness `tri*Seed*` commands are unrelated) | `CWR:World/WorldInit.cpp#L90`, `#L129-L135`; `RND:randomGen.cpp#L154`; `CWR:Foundation/Platform/GraphicsInitBridge.cpp#L84`; `CWR:Game/Commands/GameStateExtTestAudio.cpp#L3006-L3009` | V | No Plotroom seed can reach `random` |
| The stream is shared: AI radio pauses, explosion delays, weather targets, trigger countdowns and waypoint timeouts draw from it. Mission load also consumes it: one draw per presence check (even at presence 1), 200 per unit or vehicle with a placement radius, and up to 200 per randomised waypoint (it stops at the first valid sample) | `CWR:AI/AIRadio.cpp#L1612`; `CWR:World/Entities/Vehicles/Ground/Tank.cpp#L828`; `CWR:World/WorldSetup.cpp#L1270-L1276`; `CWR:World/Detection/Detector.cpp#L1276`; `CWR:AI/AIArcade.cpp#L871`; `CWR:AI/AICenterImpl.cpp#L641-L644`, `#L700-L703`, `#L1530` | V | A script roll depends on everything else that consumed values before it |
| `mission.sqm`'s `randomSeed` only seeds licence plates, through a lookup that does not advance the stream; loading overwrites the constructor's random default (stored value, default 1) | `CWR:AI/ArcadeTemplate.cpp#L1567-L1579`, `#L1975`; `CWR:AI/AICenterImpl.cpp#L1211-L1216` | V | Never present it as "the mission seed" |
| Savegames store globals, the clock, weather and active countdowns, not the generator index | `CWR:World/WorldImpl.cpp#L1740-L1748`; `CWR:World/Detection/Detector.cpp#L158-L160` | V | After a load, later draws differ; values already stored survive |
| Presence: an object is skipped when the draw exceeds `presence`, then `presenceCondition` is evaluated. Both apply only to non-playable units and to empty vehicles (and sounds, mines); every unit rolls on its own | `CWR:AI/AICenterImpl.cpp#L1400-L1410`, `#L1525-L1538`; CE identical | V | VY02, VY10 |
| Load order (`InitVehicles`): centres East, West, Resistance, Civilian, Logic; groups in file order; non-cargo units, then cargo; named objects become globals as they are created; then empty vehicles, mission triggers and markers; then unit init lines; then `init.sqs` (SP). SP injects campaign vars before `InitVehicles`; the MP server sets `param1`/`param2` before it; intros inject vars after it | `CWR:World/WorldInit.cpp#L559-L632`; `CWR:AI/AICenterImpl.cpp#L1770-L1790`, `#L1936-L1941`, `#L1014-L1018`, `#L1396-L1446`; `CWR:UI/OptionsUIApp.cpp#L883-L895`; `CWR:UI/DisplayUIMenus.cpp#L1282-L1320`; `CWR:UI/DisplayUISetup.cpp#L1505-L1519` | V | A presence condition can read campaign vars (SP), params (MP), globals from earlier-created objects and fixed engine state (`daytime`), never vars set in `init.sqs` or init lines (VY03) |
| `presenceCondition` is a multi-statement expression: assignments are allowed and only the last value must be Bool. An undefined variable is nil, any operator with a nil operand returns nil, and nil evaluates false | `EVAL:express.cpp#L2702-L2782`, `#L72-L76`, `#L2432-L2439`, `#L1348-L1351`, `#L1417-L1420`; `EVAL:express.hpp#L55-L57`, `#L119-L131` | V by reading; runtime P-R1, P-R2 | The roller lowering (§2.4); a default variant for nil (VY04). No official presence condition assigns, rolls or reads a param [V corpus] |
| A group whose units are all absent is removed before its waypoints and group triggers exist; mission-level triggers are always created; group IDs are assigned max+1 as groups are created, so callsigns shift between runs. A waypoint synchronisation skips partners that were never created, so a sync line to an absent layer stops holding (runtime unverified). A cargo entry whose transport is absent finds no seat and stands at its own editor position | `CWR:AI/AICenterImpl.cpp#L1781-L1782`, `#L2052-L2056`, `#L2072-L2108`, `#L1432-L1438`, `#L786-L807`, `#L1572-L1595`, `#L1938-L1968`; `CWR:AI/AICenterImplPreview.cpp#L202-L221` | V by reading | VY09, VY17, VY18 |
| Placement radius: a unit or vehicle keeps the first sample in the lowest-cost landscape cell among about 78 in-disc samples, so it is biased only where the disc spans cells of different cost; the leader carries the group through formation slots. Waypoints take the first valid uniform sample; sounds and mines are uniform | `CWR:AI/AICenterImpl.cpp#L628-L739`, `#L855-L939`, `#L2143-L2185` | V; "roads and open ground win" is I (P-R4) | The simulator models "best cell, then uniform" |
| Start markers: with n linked markers, the editor position plus each marker are n+1 equally likely starts (within about 0.5 percentage points over the ported table) | `CWR:AI/AICenterImpl.cpp#L966-L984` | V | Show equal odds; weights need duplicate markers or a stored roll |
| `select` rounds half to even; an index equal to the count returns nil, others out of range error. So `arr select random count arr` gives element 0 half weight and nil about 1/(2n) of the time. No `floor`, `round` or `ceil` command exists (the `floor` and `ceil` strings in the 1.99 executables sit in the C runtime's math-function name table, not the script table); `mod` and `%` are both `fmod` | `EVAL:express.cpp#L626-L640`, `#L391-L399`, `#L1104-L1105`, `#L1128-L1129` | V (CWR/CE); 1.99 `mod` is doc 29 PR20 | VY05; generated code floors with `r - (r mod 1)`, which gives 0..n−1 for `r = random n`. On 1.99 the evaluator's string block shows `%` beside `atan2` and `^` but no separate `mod` (it may be pooled with an identical literal elsewhere), so PR20 tests both spellings and the compiler emits the one that passes [I] |
| Countdowns and waypoint timeouts are Gauss(min, mid, max): the mean of 4 draws mapped piecewise through mid. About 90 % of values fall in [min + 0.52(mid−min), mid + 0.48(max−mid)] | `RND:randomGen.cpp#L156-L171`; `CWR:World/Detection/Detector.cpp#L1267-L1296` | V | Show the bell, not "random between min and max" |
| Weather ramps from Intel start to forecast over 30 minutes, then drifts to random targets (overcast ±0.5, fog ±0.2) over ≥ about 92 minutes. Timed `setOvercast` and `setFog` share one transition; an instant set starts drift on the next frame. No weather or clock message crosses the network | `CWR:World/WorldInit.cpp#L242-L268`; `CWR:World/WorldSetup.cpp#L1254-L1317`; grep of CWR and CE `Network/` | V | One instant weather step per machine; doc 41's hold keyframe (§2.3 VX06) |

**Per-profile runtime creation** [V by reading for Cwr/Ce; I for Cwa199 from the 1.99 string scan and corpus use]:

| Capability | Cwa199 | Cwr | Ce |
| --- | --- | --- | --- |
| `createVehicle`, `createUnit` (into an existing group; refuses at 12 units), `deleteVehicle`, `camCreate`, `setPos`, `setWPPos`, `skipTime`, `setOvercast`/`setFog`/`setRain` | yes | yes | yes |
| `createCenter`, `createGroup`, `createMarker`, `createTrigger`, `addWaypoint`, `setWaypointPosition`, `setDate` | no | yes | yes |
| Join in progress (the `description.ext` key `joinInProgress`), `initJIP.sqs`, `initServer.sqs`, `initPlayerLocal.sqs`, `remoteExec`, `isJIP` | no (none of these strings is in either 1.99 executable) | yes | yes |
| `isServer` | name present among the script nulars in both 1.99 executables, unused by the corpus; P-R5 | yes | yes |
| `publicVariable` of strings and arrays | assume numbers, bools, objects and groups only; P-R6 | yes | yes |
| Lobby `titleParam1`/`titleParam2` | yes | yes | yes |

Evidence: `CWR:Game/Commands/GameStateExtWorld.cpp#L83-L310` (cap at `#L157`); `CWR:AI/Path/AITypes.hpp#L31`; `CWR:Game/Commands/GameStateExt.cpp#L909`, `#L1178-L1191`, `#L1228`, `#L1251`, `#L1335-L1342`, `#L1419-L1420`; `CE:Poseidon/Game/Commands/GameStateExt.cpp#L1176-L1189`; `docs/research/data/cwa199-observed-commands.csv`.

### 2.2 Roll scopes and restart paths

| Scope | Rolled | Stored in | Same across | Differs across | Content cost |
| --- | --- | --- | --- | --- | --- |
| `Build` | by the generator, at build time | the mission files | every playthrough of this file | seeds and remixes | one variant compiled |
| `PerCampaign` | once, at the campaign bootstrap | `cmp_seed` and derived vars | restarts, Retry, save loads | new playthroughs (unless the play seed is baked, §3.2) | every option compiled |
| `PerTurn` | in a finisher commit, for the next op(s) | campaign vars | restart-from-row, Retry, save loads, Replay of the row | different outcomes and choices; the debriefing Restart shows the default layer instead (§2.5) | every option compiled |
| `PerAttempt` | by the engine, at mission load | nowhere | nothing | every path that re-runs `InitVehicles` | native fields; near zero |

What each path does [V by reading unless marked]:

| Path | Re-runs `InitVehicles` | Campaign vars at load | Engine rolls | Stored rolls | Evidence |
| --- | --- | --- | --- | --- | --- |
| New playthrough ("Begin") | yes | none; `objects.sav` survives (only `.fps` saves are deleted) | re-roll | bootstrap rolls again (or uses a baked seed) | `CWR:UI/OptionsUIApp.cpp#L433-L447` |
| Restart from row k | yes | row k's snapshot | re-roll | replayed | doc 18 §6.2 |
| Retry without autosave | yes | current table re-injected; the campaign guard is commented out, so standalone missions too | re-roll | replayed (commits happen only at mission end) | `CWR:UI/DisplayUIMenus.cpp#L1037-L1085` |
| Retry with autosave, or loading a save | no | from the save | not re-rolled; later draws differ | kept | `CWR:World/WorldImpl.cpp#L1740-L1748` |
| Debriefing Restart | yes | **none**, for the whole attempt: `SwitchLandscape` resets the game state and nothing re-injects the table, although `GStats` keeps it as it stood when the debriefing opened (so it includes whatever the failed attempt already committed) | re-roll | **nil**: gated pools vanish unless defaulted. A finisher on this path reads nil: assigning a nil result deletes the global and `saveVar` of a missing variable does nothing, so its derived commits (seed advance, next pre-roll) silently do not happen, while constant writes (flags set to true) still do | `CWR:UI/Map/UIMapDialogs.cpp#L665-L695`, `#L898`; `CWR:World/WorldImpl.cpp#L1141-L1148`; `CWR:World/WorldInit.cpp#L1026`; `EVAL:express.cpp#L2505`; `CWR:Game/Commands/GameStateExtGrp.cpp#L412-L425`; doc 18 gotcha 2, E5 |
| Intro | yes | injected after `InitVehicles` | re-roll | nil at presence time | `CWR:UI/DisplayUIMenus.cpp#L1282-L1320` |
| Standalone mission from the menu | yes | cleared | re-roll | none | `CWR:UI/OptionsUIApp.cpp#L631`, `#L757` |
| Replay of a completed row | yes | row k's snapshot: Replay sets `GStats._campaign` to it, and the common load path injects it before `InitVehicles` (non-campaign session, so writes are not kept) | re-roll | replayed: the row snapshot carries the pre-roll, so Replay shows the variant originally played | `CWR:UI/OptionsUIApp.cpp#L503-L553`, `#L850-L895`; doc 18 §6.2 |

### 2.3 The toolkit

| Code | Axis | Default scope | SP campaign lowering | Standalone and MP lowering | Notes and lints |
| --- | --- | --- | --- | --- | --- |
| VX01 | **Variant pool**: one of N layers (garrison posture, which checkpoint exists, which patrol set runs) | PerTurn | Stored roll, pre-rolled in the predecessor's finisher, read by `presenceCondition`; each layer's mission triggers guarded by the selector; hidden markers and an `OBJ_` block per layer (doc 29 `SideOpGenerator`) | Roller (P-R1) or lobby param; SP fallback: `init.sqs` pruning | VY03, VY04, VY11, VY17, VY18 |
| VX02 | **Strength jitter**: per-unit presence | PerAttempt | `presence` 0.4–0.7 on members, never on leaders or the critical path | Same; in MP the server rolls once for everyone | VY02, VY10 |
| VX03 | **Objective candidate set**: which of 5 houses holds the officer, which of 3 depots is live | PerTurn or PerCampaign | Stored roll → presence of the objective asset, its marker and `OBJ_` lines | Roller or param; MP moves markers on every machine | FP08/MC10, VY14, VY15 |
| VX04 | **Start or ingress set** | PerAttempt (native) or PerTurn | `markers[]` on the leader (n+1 equal starts), or a stored roll → presence of insertion assets plus `setPos` of the player group in the synchronous prefix of `init.sqs` (playable units ignore presence) | `markers[]` resolved on the server | Corpus: 1 marker, leaders only; VY15 checks every start |
| VX05 | **Route and patrol variants** | PerAttempt or PerTurn | Waypoint placement 50–150 m, or alternative patrol groups as pool layers; QRF route sets | Same | Each route validated for reachability (doc 34 cw07) |
| VX06 | **Weather and time** | Build, or PerCampaign/PerTurn | One instant step from the stored roll: `0 setOvercast v; 0 setFog f; skipTime h`, then doc 41's hold keyframe in the same frame so drift waits (doc 41 §3.4) | Server rolls → numeric broadcast → every machine applies; `setDate` on Cwr/Ce only | VY19; P-R8; doc 41 AP2 |
| VX07 | **Reinforcement timing and QRF origin** | PerAttempt | Countdown min/mid/max ranges; QRF origin as a pool; optional reinforcement pacer module (holds waves while a crude intensity proxy is high, releases after a relax window) | Countdowns run per machine in MP, so only server-side effects may hang on them | VY07; pacer P-R11 [U] |
| VX08 | **Event cards at extraction** (enemy programs, complications, intel reveals; a complication card fills the next op's single doc 34 cw07 `Complication` slot, never a second one, MC20) | PerTurn | Stored-LCG shuffle bag with slot-keyed draws, a no-repeat field and relief cards; effects lower to `saveVar` flags plus presence conditions | MP: a per-session deck rolled by the server | VY16, VY22; doc 29 SL30 (named rewards never roll) |
| VX09 | **Nemesis and adaptive elements** | PerCampaign (traits) plus state (adaptation) | Traits from the stored roll at bootstrap; adaptation from bounded tactic counters (doc 34 cw17) | none (no MP campaign flow) | SL31 counterplay; PR21 for kill handlers |
| VX10 | **Run modifiers** (second-wave style) | PerCampaign | A prologue Choice writes declared flags (§3.6) | MP: lobby-param bitmask | cv43 item 4: no reroll loops |
| VX11 | **Cast**: identities and starting traits | Build (default) or PerCampaign | Generator bakes identities, or a stored roll picks among compiled ones | — | Name pools per nationality (doc 28) |
| VX12 | **Cosmetic micro-variety** | PerAttempt | Placement radius on props, ambient sounds, cosmetic scripts | Allowed per machine when nothing global depends on it | SL11, VY01 |

### 2.4 Lowering a correlated one-of-N choice

Native presence is per object, so it cannot express "garrison A **or** garrison B". Four lowerings can:

| Lowering | How it compiles | Valid for | Survives restart | Status |
| --- | --- | --- | --- | --- |
| A. Stored roll → `presenceCondition` | Mission k−1's finisher derives `cmp_v<k>` from the stored LCG and `saveVar`s it; mission k's layer units carry `cmp_v<k> == 2` | SP campaign missions after the bootstrap | yes (replayed from the row snapshot) | V by reading (doc 19 F12); 1.99 runtime U |
| B. Roller | A dedicated non-playable, non-cargo unit with presence 1 whose condition assigns the pick and returns false, so it never exists; later layers compare the global. "First-created" means the first unit of the first group of the first side, in load order (East, West, Resistance, Civilian, Logic), that the mission already uses: a group on an otherwise unused side would make the engine create that side's centre (`CWR:AI/AICenterStats.cpp#L1328-L1346`). Presence 1 always passes, because the table never reaches 1. In MP it runs only on the server, which then `publicVariable`s the pick for markers and briefing | Standalone SP, first missions, MP | no, unless the pick derives from a saved seed | I; P-R1, P-R2; the floor idiom needs PR20 on 1.99 |
| C. `init.sqs` pruning | The synchronous prefix of `init.sqs` computes the pick and `deleteVehicle`s the rest (crews included) before the first frame | SP only | per the pick's source | V by reading |
| D. Lobby parameter | `presenceCondition` reads `param1`/`param2` (set before objects are created); "Random" resolves through B on the server | MP | per session | V by reading |

**Default variant rule (VY04).** Every gated pool compiles layer 0 as the default, chosen when its selector is nil, so the debriefing Restart, intros and an MP mission previewed in SP always show a complete, validated mission. Because any operator with a nil operand yields nil (false), the default layer cannot use `isNil || v == 0`; it compares `format ["%1", v]` strings (doc 18's nil idiom) against the other layers' values, so selectors are small integers [I; the exact emitted form is probe P-R2].

A roller in generated form (our own sketch, not engine or game text):

```text
; presenceCondition of the roller unit (evaluated once at load, on the SP machine or MP server)
rv_p1 = random 3; rv_p1 = rv_p1 - (rv_p1 mod 1); false
; presenceCondition of every unit in layer 2 of the same pool
rv_p1 == 2
```

Budget cost: absent objects are never constructed, so they cost no simulation or network traffic, only one draw and one condition evaluation at load; pruned objects cost load time, and in MP a network create plus delete for every client [V by reading] (§2.7). Absent objects still count toward the file-level group and seat limits that the load path checks (§2.7).

### 2.5 Anti-scum and restart policy

- **Pre-roll in the predecessor's finisher.** A PerTurn choice for mission k is derived and saved when mission k−1 commits, so the row snapshot of k carries it; restart-from-row, Retry and Replay of the row then show the same variant [V by reading; PR18 at run time]. This answers doc 19 open question 7.
- **The debriefing Restart is the one hole** [V by reading; 1.99 behaviour is doc 18 open question 2]. It reloads the mission with no campaign variables for the whole attempt, so a gated pool shows its default layer instead of the rolled one, and the finisher reads nil. A player who fails can therefore trade the rolled variant for layer 0 once, but cannot bank it [I, design]: every mission with stored rolls carries doc 29 row 13's guard, which detects the missing variables and blocks the commit and the endings, and the book's restart-from-row brings the rolled variant back. Two stronger closures exist: `lives = 0` for that mission, which also removes the restart and changes death handling (doc 18 §4), or CE patch E5, which re-injects the table.
- **Bootstrap once.** The campaign seed is rolled only when unset (doc 18's nil idiom) and `saveVar`d. Init-time saves are baked into the row snapshot (doc 18 gotcha 5), so restart-from-row keeps the seed. A debriefing Restart has no vars, so an "only when unset" guard would see nil, re-roll, and `saveVar` the new value over the stored seed, which `GStats` still holds [V by reading]. Plotroom therefore puts the bootstrap in a **prologue row with no gameplay and no debriefing**, which mission 1 follows; mission 1 then sees the seed at load on every path [I; P-R12]. The fallback is doc 29 row 13's guard.
- **Slot-keyed events.** Event k of a mission reads the seed advanced k times (doc 29 §3.3), so the order in which the player triggers events cannot change which card an event deals, and save-look-reload cannot re-deal it (VY01).
- **Loss-side bad-luck protection** only, per preset, disclosed (doc 36 cv07, cv43 item 8).
- **Standalone missions** are PerAttempt by nature and are labelled "re-rolls on restart". An optional "keep roll across Retry" saves the pick with `saveVar`, since Retry without an autosave re-injects saved values even outside a campaign [V by reading].
- **Opt-in re-roll on restart** is a possible Campaign Condition that the owner kept out of v1 on 2026-09-27 (doc 36 open question 2; OWQ-21 re-roll (a), D040: no exception to SL11 in v1; DG038 words the rule). It must not create reroll loops (cv43 item 4), and the Exploiter policy (cv21, SL28) must gain nothing from it.
- **Ironman** stays detection-only on vanilla (doc 29 E8, PR19).

### 2.6 Multiplayer

There is no MP campaign flow (doc 18 §6.5) [V], so MP replayability is per session: lobby parameters plus server rolls. Where rolls happen [V by reading]:

| Class | Mechanisms | Why |
| --- | --- | --- |
| **Safe** | `presence`, `presenceCondition` (params, roller), placement, `markers[]`, waypoint placement, server-side create and delete | Only the server runs `InitVehicles` and replicates objects to clients (`CWR:UI/DisplayUISetup.cpp#L1501-L1549`, `#L1633-L1652`; `CWR:Network/NetworkServerSimulate.cpp#L725-L771`) |
| **Unsafe unless server-rolled and broadcast** | `random` in `init.sqs`, unit init lines, trigger statements or `createUnit` init strings; marker moves; weather and time; countdowns with global effects | `init.sqs` runs on every machine (`CWR:UI/DisplayUISetup.cpp#L1538`, `#L1649`); the server sends every unit init line to the clients, which re-run it (`CWR:World/WorldInit.cpp#L665-L671`; `CWR:Network/NetworkClientOnMessage.cpp#L1372-L1379`), and a `createUnit` init string runs on the creating machine and is then sent the same way (`CWR:Game/Commands/GameStateExtWorld.cpp#L193-L209`); every machine simulates its copy of each trigger (`CWR:World/Detection/Detector.cpp#L696-L729`); marker commands, `createMarker` included, change only the local map (`CWR:Game/Commands/GameStateExtWorld.cpp#L453-L506`; `CE:Poseidon/Game/Commands/GameStateExtWorldConfig.cpp#L724-L757`); `createVehicle` in a script every machine runs makes N copies (`CWR:Game/Commands/GameStateExtWorld.cpp#L124-L150`), and `createUnit` into a remote group asks the group's owner to create it (`#L300-L307`) |

**Roll protocol** (generated code follows one pattern). The server rolls, writes numeric globals, `publicVariable`s each, then sets and broadcasts a ready flag last; clients wait on the flag (nil reads as false) and apply local effects: markers, weather step, time, briefing lines. "Flag last" assumes guaranteed messages arrive in send order; the server's own JIP object sync relies on that too (`CWR:Network/NetworkServerMission.cpp#L987-L988`), but the transport's ordering itself is unverified. So clients wait until the flag **and** every rolled number read as defined (a nil-safe test), and no client code ever initialises a broadcast global, because a broadcast can arrive before that client's `init.sqs` runs and an initialisation would overwrite it [I]. The server gate is `isServer` on Cwr/Ce, and on Cwa199 once P-R5 passes; until then the compiler inserts a Game Logic named `server` and tests `local server` (editor logics are local to the host) [I]. On Cwa199, choices are encoded as numbers only (P-R6). `publicVariable` relays through the server to every player (`CWR:Network/NetworkServerMsgOnMessage.cpp#L556-L615`) [V by reading].

- **Lobby parameters.** `param1`/`param2` are set and broadcast before objects are created, so presence conditions can read them; they are never set in SP, so Preview injects defaults when an MP mission is tested in SP (`CWR:UI/DisplayUISetup.cpp#L1507-L1519`) [V by reading]. With only two slots, host-picked modifiers pack as bitmasks (exact below 2^24).
- **Join in progress (Cwr/Ce only).** Only when the mission's `description.ext` sets `joinInProgress` does the server store `publicVariable` messages (deduplicated by name, capped at 10,000 entries) and replay them to a joining client after the world objects; unit init lines are not stored for replay (`CWR:Network/NetworkServerMission.cpp#L373-L383`, `#L978-L1121`; `CWR:Network/NetworkServerMsgOnMessage.cpp#L570-L614`) [V by reading]. A JIP client runs `initPlayerLocal.sqs` and `initJIP.sqs` when it enters play (`CWR:Network/NetworkClientOnMessage.cpp#L2148-L2154`), so local effects are re-applied in `initJIP.sqs`. `init.sqs` stays free of `random` because every regular client runs it; whether a JIP client also runs it was not found by reading (unverified). Time and weather sync for JIP clients, and whether replayed vars arrive before the JIP scripts, are P-R7 and P-R9.
- **Slot scaling.** Empty playable slots with AI disabled are not created, so the playable force already scales with player count; presence never applies to those slots (`CWR:AI/AICenterImpl.cpp#L1795-L1822`, `#L1003-L1007`) [V by reading].
- **Corpus [V].** 79 of 398 mission folders (all types, SP included) define `titleParam1`; `publicVariable` appears in 23 of 30 official MP missions and 26 of 31 templates. No official file uses `isServer` or `local server`; they gate on unit locality. No shipped mission has a server-rolled, broadcast or persisted variant.

### 2.7 Budgets and corpus baselines

| Budget | Value | Basis | Status |
| --- | --- | --- | --- |
| Groups per side, summed over every variant including absent ones | ≤ 63 | 9 letters × 7 colours (`MaxGroups`, from `CfgWorlds`). `IsConsistent` counts every group in the file, and it runs on the **load path** as well as in the editor: `ParseMission` calls it and fails when it fails, so an over-limit file never loads (doc 04 already records this refusal). The same check applies to the `Intro` and outro sections, which load through the same parser. In a campaign the engine then treats the mission like a cutscene-only entry, adds its book row and plays the loser outro, so the campaign silently moves on as if the mission were lost (`CWR:AI/ArcadeTemplate.cpp#L1754-L1860`; `CWR:UI/Map/UIArcadeWaypoint.cpp#L920-L988`, check at `#L966-L970`; `CWR:UI/OptionsUIApp.cpp#L860-L875`; CE identical at `CE:Poseidon/UI/Map/UIArcadeWaypoint.cpp#L953`) | V by reading (Cwr, Ce); Cwa199 I |
| Crew seats per group, summed over every variant | ≤ 12 | `MAX_UNITS_PER_GROUP`; the same check counts each entry's driver, commander and gunner seats, so one tank entry uses 3 | V by reading |
| Entries in `mission.sqm` (a crewed vehicle is one entry; gated entries included) | about 115 units, 170 objects | official campaign p90 (p50 74 units, 98 objects) | V corpus |
| Worst-case variant combination | about 180 units, 260 objects | official SP maxima (177 units, 260 objects) | V corpus |
| Pool overhead (gated share of mission objects) | ≤ 35 % | official campaign max 34.5 % (p90 7.8 objects); official SP max 30.8 % | V corpus |
| Load time with 8–20 layers | — | doc 29 PR17 | U |
| Frame-rate cost of large variants | — | not measured | U |

**How official content randomises** [V corpus, unique missions per group]. Of 63 official campaign missions, 35 (55.6 %) use at least one explicit mechanism: presence < 1 in 25.4 % (common values 0.5, 0.4, 0.2, 0.7, 0.3; mean 0.50), waypoint placement 22.2 % (p50 50 m, p90 150 m), start markers 22.2 % (one marker each but one, always on leaders), script `random` 14.3 %, unit placement 9.5 % (p50 25 m), `presenceCondition` 3.2 % (3 units). 92.1 % have a trigger countdown spread (p50 2 s, p90 5 s) and 74.6 % a waypoint timeout spread (p50 9 s, p90 180 s). Of 18 official SP missions, 50 % use presence. MP: coop 75 %, deathmatch 80 %, team 31 %. **Presence is used for strength jitter, never for one-of-N**: of 105 gated campaign groups, 51 thin members, 32 are single units, 16 put the same p on every unit (a squad of 4 at p = 0.5 appears whole only 1/16 of the time), 4 gate only the leader and 2 use different p on every unit. CWE re-releases count once (31 of 63 campaign and 27 of 28 MP missions are identical to official ones); original CWE missions lean on `random` in `init.sqs` (4 of 5 large missions). A broader heuristic count over all 398 folders, cutscenes included, finds about 40 % with presence, placement or `random` [I, heuristic parser].

Corpus-grounded defaults: presence slider 0.4–0.7, unit placement about 25 m, waypoint placement 50–150 m, one alternative marker on the leader. Plotroom's addition is the layer shipped content never had: seeds, correlation, storage, anti-scum and MP broadcast. On import, existing randomness surfaces as variation chips labelled "per attempt, uncorrelated, worst case not validated".

### 2.8 Lints

| Code | Severity | Rule |
| --- | --- | --- |
| VY01 | error | Engine `random`, `presence`, placement or a countdown feeds a committed var, a guard, an outcome or a card (per-mission extension of SL11) |
| VY02 | warn | `presence` < 1 or a `presenceCondition` on a playable unit (no effect) |
| VY03 | error | A presence condition reads a variable not definitely assigned before it is evaluated (vars from `init.sqs` or init lines, objects created later, a roller in a cargo slot) and is not nil-safe |
| VY04 | error | A pool gated on campaign vars, a roller or params has no default variant for nil |
| VY05 | warn | `select random count` or any `select` on an unfloored `random` index |
| VY06 | warn | A probability below 1/32768 treated as non-zero, or code that assumes `random n` returns an integer or can reach n |
| VY07 | error (MP) | `random` in `init.sqs`, unit init lines, trigger statements or `createUnit` init strings feeds shared state or a global effect |
| VY08 | error (MP) | `createVehicle`/`createUnit` outside a server-gated block, or a marker, weather or time change that runs only on the server |
| VY09 | warn | A vehicle pruned without its crew, a gated transport whose cargo entries do not share its gate (the cargo then stands at its own editor position, §2.1), or `init.sqs` pruning in an MP mission |
| VY10 | info | Every unit of a group shares one `presence` < 1 (partial squads); offer "whole-group chance" as a pool |
| VY11 | error | More than 63 groups on a side summed over all variants, or more than 12 crew seats in a group (the load path refuses the file, §2.7) |
| VY12 | warn | The worst-case variant combination exceeds the unit or object cap, or pool overhead exceeds 35 % |
| VY13 | warn | A procedural template varies fewer than 2 gameplay axes (oatmeal) |
| VY14 | warn | A rolled axis has no player-visible surface |
| VY15 | error | Some variant breaks the critical path: objective outside the briefed area (FP08/MC10), exfil unreachable, or an enemy within the no-spawn radius or line of sight of a player start |
| VY16 | warn | A twist or surprise card lacks a foreshadowing or intel slot, a counterplay tag or a debrief cause line |
| VY17 | error | Radio, briefing or debrief text hard-codes the callsign of a pool group |
| VY18 | warn | A mission-level trigger that belongs to a variant is not guarded by its selector, or a waypoint or trigger synchronisation line crosses layers (it stops holding when the partner layer is absent, §2.1) |
| VY19 | warn | A timed `setOvercast`/`setFog` pair that ramps to new values (the second cancels the first ramp; doc 41's hold pair, which repeats the current values, is exempt); in MP, a weather or time roll not applied on every machine; `setDate` on Cwa199 |
| VY20 | info | Estimated distinct runs stopped growing while cost kept growing (§4.4) |
| VY21 | warn | A cinematic's anchor object or camera path is missing in some variant (docs 32, 39) |
| VY22 | warn | A deck smaller than its expected draws without a repeat cooldown, or an immediate repeat where the template forbids it |
| VY23 | error | A stored seed or slot value outside 0..=65535, or not an integer |
| VY24 | warn | A string or array `publicVariable`, or `isServer`, on a Cwa199 target before P-R6 / P-R5 pass |

VY19's first clause is doc 41's AL03, and VY08's weather clause is part of doc 41's AL16; each pair shares one finding and message (as doc 39's DR checks do with doc 32's lints) until the code registry (DG005) assigns one id.

### 2.9 Type sketch (Rust, proposal-only)

```rust
// Proposal-only; names are placeholders for the design round.
/// When a roll is made and how long its result holds (§2.2).
pub enum RollScope { Build, PerCampaign, PerTurn, PerAttempt }

/// Where the randomness comes from. Extends doc 29's `RollSource`.
pub enum RollSource {
    BuildSeed { item: ItemSeed },                    // generator; result baked into files
    StoredLcg { seed: VarId, slot: RollSlot },       // doc 29 §3.3, read at a fixed slot
    EngineLoad,                                      // presence, placement, markers[], min/mid/max
    Roller { roller: EntityId, var: VarId },         // §2.4 B; P-R1
    ServerBroadcast { var: VarId, ready: VarId },    // MP roll protocol, numbers only on Cwa199
    LobbyParam { slot: ParamSlot, bits: BitRange },  // host choice, packed bits
    CosmeticEngineRandom,                            // never feeds state (SL11, VY01)
}

/// One thing that differs between runs, as the Variety panel shows it.
/// This is the type doc 26 §9.1's `MissionArchetype::variation` names, not a second one;
/// doc 29's `SideOpGeneratorModule::caps` (`VarietyCaps`) carries the §2.7 budgets.
pub struct VariationAxis {
    id: AxisId, kind: AxisKind /* VX01..VX12 */, scope: RollScope, source: RollSource,
    options: Vec<VariantOption>,       // 2..=7, so menus and ghost overlays stay legible
    default: VariantId,                // chosen when the selector is nil (VY04)
    surfaces: Vec<Surface>,            // radio, briefing block, debrief line, marker (VY14)
    gameplay: EnumSet<GameplayAxis>,   // start, objective, posture, QRF origin, route (VY13)
    lowering: PoolLowering, origin: Origin, pinned: bool,
}
pub struct VariantOption { id: VariantId, weight: Chance32k, layer: LayerId, label: TextKey }
/// Probability quantised like the engine table (1/32768 steps).
pub struct Chance32k(u16);
pub enum PoolLowering { StoredRollPresence, Roller, InitPrune, LobbyParam, ServerRollDelete }

/// A deck dealt from stored rolls (VX08).
pub struct ShuffleBag { cards: Vec<CardId>, no_immediate_repeat: bool, relief_cards: u8, repeat_cooldown: u8 }

/// Seed of doc 29's LCG. u16 is exactly its cycle 0..=65535; 65536 (a fixed point) is rejected on parse.
pub struct PlaySeed(u16);
pub enum PlaySeedPolicy { RolledAtStart, Baked(PlaySeed) }
pub struct RootSeed(u64);        // build seed carried in a seed code
pub struct ItemSeed(u64);        // BLAKE3(root, step id, item key), doc 38 §4.5
pub struct GeneratorEpoch(u16);  // bumped whenever golden seeds change
```

Newtypes follow AGENTS.md (`from_raw`/`to_raw`, `Display`) and go into the CODE-INDEX newtype table when implemented.

## 3. Build-time variety

### 3.1 What "same brief + seed" guarantees

| How the campaign was made | Guarantee | Why |
| --- | --- | --- |
| T0, no model | **Exact**: seed + typed brief + generator epoch + fact-pack fingerprints reproduce the campaign byte for byte | Pure code, subject to the rules in §3.2 [I] |
| Any model tier, replayed from the journal | **Exact** while each step's input digest matches; settled Recorded steps are reused and never re-executed; a mismatch parks the run as Stale | Doc 38 §4.2–§4.3 [V, repo] |
| Any model tier, sampled fresh with the same seed | **Not reproducible**: the menus match, the model's picks may not, and one different pick changes everything downstream | See below [V] |

No cloud backend offers deterministic sampling. Anthropic's Messages API has no seed parameter, says temperature 0.0 is "not fully deterministic", and rejects temperatures other than 1.0 for models released after Claude Opus 4.6 [V]. OpenAI's seed is "best effort" [V]. Thinking Machines got 80 distinct completions from 1,000 identical temperature-0 requests, traced to batch-variant kernels [V]; Atil et al. measured accuracy swings up to 15 % under "deterministic" settings [V]. A local CPU build with a fixed sampler seed may replay on one machine (a llama.cpp PR author states CPU "is already deterministic") [V], but not across builds, hardware or users. Doc 40 §2.5 lists the current Claude models that refuse `temperature`, `top_p` and `top_k` with an error; whether a request that sets exactly 1.0 is accepted was not re-checked here, and DG026 (open) proposes where candidate diversity comes from instead. So sharing a model-assisted campaign means sharing its journaled picks (§3.4). The UI never offers a "model seed" knob as if it made output reproducible; the journal records backend, build, thread count and sampler seed so a local mismatch can be explained.

### 3.2 Seeds and portability

- **Seed parts** [I]. A `RootSeed` derives domain seeds by hashing: **Theatre** (sites, routes, compositions), **Story** (skeleton, twists, cast) and **Lab** (balance sampling). "Swap seed part" keeps the theatre and re-rolls the story, or the reverse, as in Civ VI's separate map and game seeds [V]. Item seeds follow doc 38 §4.5 (hash of root, step id and item key), so moving elements does not reseed them.
- **Play seed** [V arithmetic; I design]. The run-time seed is the initial `cmp_seed` of doc 29's LCG, `(x·75 + 74) mod 65537`. Its largest intermediate (4,915,274) is below 2^24, so it is exact in the engine's 32-bit floats; its cycle from 0 covers 0..=65535, and 65536 maps to itself. `PlaySeedPolicy::RolledAtStart` (the default) rolls it once from engine `random`, so playthroughs almost always differ. One bootstrap draw carries at most 15 bits: the table holds 20,794 distinct values, and drawn as `random 65536` and floored they are all even, so the roll reaches under a third of the 65,536 seeds. Because the table repeats values (up to 7 times), two playthroughs share a play seed about once per 16,500 pairs, assuming a uniform start index [V arithmetic over the ported table]. A second draw in the same script adds nothing (§2.1). `Baked` fixes it from the build seed, so everyone gets the same rolls: the "Fixed (shareable)" versus "Fresh each playthrough" choice. Using one engine draw as entropy for the first `cmp_seed` extends SL11's current wording ("cosmetic variety only") and needs a doc 29 change (DG038; OWQ-21 chose Fresh each playthrough as the default on 2026-09-27, D040).
- **Portability rules for generator crates** [V sources; I rules]. `rand`'s `StdRng` and `SmallRng` are explicitly non-portable, `rand` allows value-breaking changes in minor versions, and its docs warn never to sample `usize` when portability matters; std's `DefaultHasher` may change between releases, `HashMap` iterates in arbitrary order, and `f64` transcendental functions vary by platform. Therefore: a named, pinned ChaCha implementation behind a newtype, with our own integer sampling covered by test vectors; `BTreeMap` or sorted vectors on every output path; integer or fixed-point scoring for picks; golden-seed outputs byte-identical across the Windows, Linux and macOS CI matrix (RAT3).

### 3.3 Seed codes ("operation codes")

| Field | Size | Notes |
| --- | --- | --- |
| Format version, generator epoch | 2 B | An epoch mismatch opens an honest card: "made with generator epoch 3, you have 4; the campaign will differ", offering "generate anyway" or "open the replay record" |
| `RootSeed` | 8 B | — |
| `PlaySeedPolicy` | 3 B | tag plus `u16` |
| Typed `CampaignBrief` after S0 | ≈ 6–10 B | enums only, never free text (doc 25 §4.3) |
| Build modifiers with parameters | ≈ 3–5 B | only `ModifierLayer::Build` (§3.6) |
| Fingerprint prefixes | 12 B | 32-bit prefixes of the mod set (doc 27 BLAKE3), island catalogue and content packs |

Total ≈ 34–40 B, about 55–64 Crockford base32 symbols plus a check value and hyphens [I arithmetic]. Crockford base32 drops I, L, O and U, decodes case-insensitively, reads i/l as 1 and o as 0, and ignores hyphens [V]. Its optional mod-37 check symbol uses `*`, `~`, `$`, `=` and `U`, which chat and Markdown renderers mangle, so the check value should come from the 32-symbol alphabet (for example two CRC symbols) [I]. A numbered-catalogue code (§3.7) needs no 64-bit seed and fits in 8–10 symbols. `SeedCode` has a pure parser with length cap, checksum, unknown-epoch and overflow errors in the crate's single `Error` enum; unknown future enum values parse as-is and are refused at generation with a finding. It is untrusted input with an adversarial test suite (RAT6). The code is shown on the campaign card, in the export readme and in the Share dialog.

### 3.4 Replay records

A replay record reproduces a model-assisted campaign with no model call: the seed code, the journal's settled answers (Pick letters mapped to stable ids, admitted Fill text) and human edits as ops; never raw replies or reasoning [I]. Imported records re-run every verifier, carry origin `ImportedReplay { from_code }`, keep model provenance in the AI content report (doc 25 §9.1), obey size caps, and park as Stale on any epoch or fingerprint mismatch. Their text is untrusted data and never enters a capsule as instructions (AGENTS.md). Two design gaps: "recipe" already names doc 17 §10's recipe library, so the artifact's name and format belong to doc 38's W0 "one format" decision (doc 21 open question 7); and exporting it is an exception to "journal excluded from export" (doc 21 §9.3). Both are now tracked in `docs/design-gap-requests/`: DG007 proposes that recipes become exemplar libraries, DG010 reserves "replay" for re-driving from the journal with no model call (the sense "replay record" uses), and DG017 decides journal storage and what leaves the machine, including this record.

### 3.5 Remix with pins

Remix re-runs a chosen scope with a new seed salt, feeds pinned and human-owned fields in as constraints, and merges with doc 25 §9.3's field-level three-way merge (keep ours on conflict; deleted stays deleted; pinned values never recomputed) [V, repo]. Levels [I]:

| Level | Re-rolls | Keeps |
| --- | --- | --- |
| **Reshuffle** | sites, time, weather, micro-placement | skeleton, archetypes, twists, cast |
| **Rearrange** | archetypes and twists within the same skeleton | skeleton, cast, pins |
| **Rebuild** | the skeleton | cast and pinned nodes |
| **Nudge** | one dimension through a sub-seed | everything else |

- Scope: campaign, act, node or aspect. The result lands as one undo group with a "what changed" card per view, and the previous version stays a one-click alternative; the journal keeps every seed, so any earlier variant can be restored and diffed.
- A pinned node the new skeleton cannot host produces a finding and a question, never a silent drop. Downstream nodes whose menus changed (menus depend on earlier picks, doc 25 §6.2 step 3) are marked Stale with reason "upstream remix".
- **T0 caveat** [I]: seeded picks must be journaled as Recorded or frozen on adoption; as Pure steps they would be silently recomputed from the current document (doc 38 §4.2).
- **Cost is asymmetric.** A code-side remix is instant, free and offline; regenerating text costs money on cloud keys (doc 40 models a full campaign at $8.88 on Sonnet 5 at Standard budgets, $3.52 with every lever; text slots are about 70 % of spend) [I, doc 40's model]. Invalidated text slots are marked Stale and the user chooses: cycle stored alternatives ($0), template text ($0), or regenerate N lines at a shown price.

### 3.6 Modifiers and presets

- **Two layers** [I]. `ModifierLayer::Build` changes what Plotroom generates and goes into the seed code. `ModifierLayer::Run` is chosen per playthrough; the game's campaign UI has no such screen, so run modifiers compile to a prologue Choice (radio, ≤ 10 items, only while the player leads the group; doc 19 F11) that writes declared flags, and they pass the doc 19 lints. In MP they are lobby-param bits.
- **Precedents share one shape**: a labelled toggle chosen at run start, sometimes ranked, sometimes excluded from achievements. XCOM's Second Wave [V]; Slay the Spire's Custom Mode (seed plus any number of modifiers, achievements and leaderboards off) [V]; Hades' ranked Pact conditions [V-search].
- **Families** (our classification): Variety, Pressure, Assist, Realism. Each modifier declares its layer, preconditions, effect as knob deltas or module presets, required lints, exclusion groups and a one-line player disclosure.
- **Weights.** The balance lab can measure a difficulty weight only for strategic modifiers; tactical ones act through the lab's uncalibrated combat-outcome table (doc 29 §5.2, open question 1), so their weights are labelled assumptions until Preview playtests.
- **Not modifiers.** Campaign patterns (perspective flip P7, long march P10) belong in the brief's pattern field; Nemesis and Mole are module toggles whose picks roll at run time (doc 34 cw16–cw17). Per-node modifiers (Night, Fog/Overcast, Stealth, Timed, Undermanned, Civilians present, Captured gear only, plus the three candidates from doc 35 rc81 that doc 26 §9.3 now lists) stay doc 26 §9.3's `Modifier`; the campaign modifiers here only change how often the generator applies those, or set run-time knobs, so the type is named `CampaignModifier` to keep the two apart [I].
- **Event pacing preset** (Classic, Calm, Chaotic): event-deck pacing and variance, set separately from difficulty and from Ironman honour, after RimWorld's storytellers [V precedent; I design]. It is not called "tempo", which already names doc 34 §1.2's operational-tempo counter and doc 39's shot `Tempo`.
- **Unlock after victory** [V by reading; runtime P-R10]: `objects.sav` is per campaign and survives "Begin", and `loadStatus` returns a Bool (`CWR:Game/Commands/GameStateExtWorld.cpp#L898-L945`), so a finale can save a marker that the next playthrough's prologue reads to offer harder modifiers. Separate campaigns cannot see each other, so cross-campaign unlocks stay editor-side suggestions.

| Modifier | Layer | Effect | Weight |
| --- | --- | --- | --- |
| Night-heavy | Build | time-of-day weights shift toward night (doc 26's Night modifier applied more often) | assumed |
| Foul weather | Build or Run | weather band for VX06 | assumed |
| Scarce pool | Build or Run | pool income and starting stock down | measured |
| Short fuse | Run | doom clock +1 per turn | measured |
| Lengthy scheme | Run | doom clock max doubled | measured |
| Thin roster | Build | roster size down (not doc 26's per-node Undermanned) | measured |
| Hidden programs | Run | one more face-down program card | measured |
| Seasoned enemy | Build | enemy skill band up (not "Veteran", which is the game's own difficulty mode; doc 36 notes the same clash) | assumed |

### 3.7 Challenges without dailies

Daily and weekly challenges conflict with doc 36 cv43 item 2 (no streaks, dailies, login rewards or appointment mechanics in anything Plotroom's generators produce); a calendar-rotated preset is at least adjacent to an appointment mechanic [V, repo]. Server-bound challenges also die: XCOM 2's Challenge Mode left Steam on 2022-03-28 and was shut down on all platforms on 2022-08-22 [V-search]. The rule-compliant design, **allowed by the owner on 2026-09-27** (OWQ-20 (a) in `docs/decisions/OWNER-QUESTIONS.md`; D039 item 3), is a numbered, never-expiring **challenge catalogue** in the style of Brogue's seed catalogue: "Operation #37", shipped as T0 pack data (doc 22). Entries are T0 only with a baked play seed, vetted by the balance gates, playable at any time with no calendar, streak, reward or reminder; Ironman is honour-only (doc 29 E8); an optional plain-text after-action code can be shared; communities may publish their own catalogues. Deterministic rejection sampling (attempt 0, 1, 2…) lets every client converge on the same vetted seed with no server.

### 3.8 Surprise me, Seed Atlas and the novelty archive

- **Surprise me** extends doc 26 §8.2's dice: code samples 64 T0 skeletons for the current brief and offers the one farthest from the user's archive. Dice never call the model [V, repo].
- **Seed Atlas** [I]: background T0 sampling (100–500 skeletons; throughput unmeasured [U]) plotted on two user-chosen metric axes; hover shows a skeleton card, clicking adopts the seed and the normal S1–S9 flow runs. It follows Danesh's expressive-range plots with click-to-load (Cook, Gow, Smith & Colton 2022) [V] and Brogue's seed catalogue of seeds 1–1000 [V-search], which Brogue CE can regenerate [V]. A MAP-Elites-style archive (Mouret & Clune [V-search]; Gravina et al. 2019 [V]) keeps the admitted seed with the best fun-lint and balance score per cell. Empty regions are shown honestly as generator holes.
- **Novelty archive** [I]: local only, opt-out, never uploaded (doc 21 §12.1). It biases which seed is *suggested*, never what a seed *generates*, so codes stay portable. Novelty search scores distance to the k nearest archived items (Lehman & Stanley 2011) [V-search]; a 2026 study found agent output growing less diverse over weeks unless users supplied distinctive material (Lai et al.) [V].

## 4. Variety budgets and diversity metrics

### 4.1 Three levels of sameness

(1) **Within one campaign** (oatmeal): doc 26 CF03, doc 28 CF17 and TX05. (2) **Across seeds of one brief**: the metrics below, in doc 25 E2/E10 and the Atlas. (3) **Across users and briefs**: offline evaluation only, since there is no telemetry. LLM-assisted content tends to converge: intra-model repetition and inter-model homogeneity (Artificial Hivemind, NeurIPS 2025) [V]; AI-assisted stories rated more creative but more alike (Doshi & Hauser 2024) [V-search]; lower diversity when writing with an instruction-tuned model (Padmakumar & He, ICLR 2024) [V]. Azad & Baten's human-relative ratio ρ (parity at ρ ≥ 1) is a usable per-metric report [V].

### 4.2 The metric vector

Expressive range analysis (Smith & Whitehead 2010) is the established instrument: "a generator that can create tens of thousands of levels in a matter of minutes is useless if many of those levels are effectively identical" [V]. Later work adds kernel density, e-distance with bootstrap tests and self-plagiarism checks (Summerville 2018) [V], criteria for choosing metric pairs (Withington & Tokarchuk 2023) [V], constraint-based generation that covers the metric grid systematically (Bazzaz & Cooper 2025) [V], and overlays of users' own artifacts on a tool's range (ERaCA 2022) [V-search]. Plotroom reports a **vector**, never one "variety score" [I]:

| Dimension | Metrics | Computed over |
| --- | --- | --- |
| Archetype sequence | Hill number exp(H) of archetypes and of (verb, seat, time) tuples; longest same-value run; bigram coverage; normalised edit distance between spines; distinct classes under a code-defined equivalence (NoveltyBench-style distinct_k, but exact) | per explored path; across N seeds |
| Sites and islands | sites per grid cell or named region; union coverage; hot-spot index (largest share of seeds using one site); mean pairwise site distance | across N seeds |
| Branch structure | distinct shape classes by Weisfeiler-Lehman hash of the typed skeleton graph (Shervashidze et al. 2011 [V-search]); endings, reconvergences, Choice nodes, routers | per campaign; across seeds |
| Cast and twists | twist-id collision rate per act position; name reuse; nemesis-motive distribution; "pool pressure" when pool size < slots × target distinct campaigns | across N seeds |
| Text | per-slot-kind 3-gram Jaccard against earlier seeds; repeated 4-word openings; compression ratio (Shaib et al. 2025: compression, long-n-gram repetition, Self-BLEU and BERTScore have low mutual correlation) [V] | per campaign; across seeds |
| Run-time layouts | distinct variant tuples over N simulated loads; worst-case and median layout validity | per mission |
| Whole-set spread | Vendi score over a typed similarity kernel, never raw text embeddings by default (Friedman & Dieng) [V] | across N seeds |

Text metrics only order candidates; they never admit or reject content. Computational metrics are not perceived variety ("current computational metrics should not be used in lieu of user studies", Mariño et al. 2015 [V]); only some metrics (element counts, block diversity, material presence) tracked human scores in Hervé & Salge 2021 [V]. So thresholds are calibrated with a blind panel judging "same or different?" pairs across seeds (doc 25 §11.2), and only metrics that predict those judgements are kept.

### 4.3 Baselines from human-made campaigns

Corpus aggregates (owner's 1.99 install; re-run on 2026-09-27) [V]. The main 1985 campaign: 42 playable nodes, 12 player roles (entropy 3.16 bits, longest same-role run 5, 66 % of adjacent pairs change role), islands 1.50 bits with a longest same-island run of 9, time of day day/dawn-dusk/night 20/12/10 (1.52 of a possible 1.58 bits; longest run 3, folder order as play order [I]). Resistance: 20 playable nodes, 3 roles (16 as the guerrilla leader, 0.92 bits, longest run 16), one island, time of day 14/4/2 (1.16 bits, longest run 5). Briefing text: 1985 distinct-2 0.664, zlib ratio 3.03, pairwise 3-gram Jaccard mean 0.0025; Resistance 0.718, 2.85, 0.0058 (distinct-n depends on corpus size, so the two are not directly comparable); neither repeats a 4-word opening. **Consequence:** targets depend on the pattern. Single-protagonist campaigns legitimately have low seat and island entropy; multi-perspective ones should vary seat. CF17 must be run over the official campaigns' joint (verb, seat, time) sequence before it ships at warn severity [U].

### 4.4 The Variety Budget meter

Per mission and per campaign [I]: layer count against the probe-derived cap (PR17), estimated distinct runs over the top four dimensions of RP2, extra book rows and routers (expected 0), compiled lines added by runtime scopes, and the Preview smoke runs needed. It warns when distinct runs stop growing while cost does (VY20). XCOM's history frames the trade: about 110 hand-made maps against 80 plots, 200+ parcels and 450 road pieces [V].

### 4.5 Fairness across seeds

The balance lab (doc 29 §5.2) runs N seeds × M runs (defaults 20 × 50 [I]) [I]. Each seed must pass AC06 (500 seeded runs per policy; every run reaches an ending; the Pessimistic policy reaches the last stand or finale with ≥ 4 deployable) and the AC09 band (Standard win rate 40–75 %) [V, repo]. The panel shows per-seed pass/fail chips, p10/p50/p90 bands of win rate, early-loss rate and clock reach, a cross-seed "systematic bias" finding, auto-tune per seed with pinned numbers as constraints, and the Exploiter check (SL28) and dominance check (SL27) per seed. Challenge entries use tighter bands. The lab covers only the strategic layer; tactical fairness (for example AI squadmates dying from AI mistakes) needs Preview playtests (doc 29 AC16) [U], and every variant layout must pass VY15 before it can be dealt. Until playtests exist, the one code-side check on **sibling variants of one pool** reuses doc 28 FP28's force-ratio count: each variant's ratio along its critical-path corridor stays within a placeholder band of the pool median, or the outlier is tagged a hard variant that intel foreshadows and the debrief explains (RP4, VY16), so the dealt layout never decides the mission on its own [I].

### 4.6 Weak-model pick collapse

Aligned models collapse onto "typical" choices: they over-pick 7 among "random" numbers (West & Potts), RLHF "significantly reduces output diversity" (Kirk et al., ICLR 2024), and raising temperature costs quality, while sampling a stratum first does better (SimpleStrat) [V]. Verbalized sampling raised creative-writing diversity 1.6–2.1× [V], but code-owned strata need no prompt trick. So code owns every random choice and never asks a model to "pick randomly" [I]. The harness measures pick entropy across seeds with permuted menus against a random-valid-pick control. If picks collapse, **the model proposes and the seed disposes**: among admitted options within the ranking margin, the item seed breaks ties. For text, code picks the stratum (tone, detail token, speaker) and the model writes inside it. There are no temperature knobs.

## 5. The XCOM-like layer and the Civilization lessons, applied

Docs 29, 34 and 36 own these mechanisms; this table lists only what replayability adds.

| Mechanism | Owner | What this doc adds |
| --- | --- | --- |
| Ops board triage (2–3 cards, "if ignored" shown) | doc 29 K3, OpsBoard | Card mix from the stored LCG; consecutive turns never offer the same archetype pair; the first triage offer differs across seeds (RAT17) |
| Enemy Programs deck (Dark-Event-style) | doc 34 §1.2 (Programs module, cw02), doc 29 K3 | Shuffle bag (VX08): 2–3 cards per turn, one face-down unless the player spends intel; the extraction choice counters one and the rest fire; each card has one visible rule, lowered to flags plus presence conditions. A program card deals *which* of doc 34's programs moves this turn: firing shifts its timing one phase (SL25 already demands a variant per shift), countering applies doc 34's delay or deny verb, so the deck adds no second clock [I] |
| DoomClock | doc 29 K4 | Per-campaign seeding of which regions host the facilities that feed it and which side-op archetype attacks each; length as a Campaign Condition |
| Nemesis | doc 34 cw17 | 2 strengths and 2 weaknesses drawn from a typed catalogue at bootstrap, each lowered to an engine lever (skill, gear, QRF size, a favoured reaction, radio register) and passing SL31; weaknesses revealed by intel ops; the reckoning op authored |
| Mole | doc 34 cw16 | Suspect drawn per campaign; clue coverage for every value (C21) |
| Roster | doc 29 `SoldierDecl` | Seeded era-correct identities and 1–2 starting traits mapped to engine levers; acquired traits from events; a Character Pool import (Mixed, PoolOnly, RandomOnly) of the user's own names as Human-pinned entries |
| Side ops | doc 29 `SideOpGenerator`, doc 34 cw07 | Site-kit sockets filled per seed; ≥ 2 gameplay axes per archetype (VY13); worst-case layer validated |
| Campaign graph | doc 19, doc 26 §9.4 | Weighted node types with fixed anchors, branching ≤ 3 within the 7-socket budget; "?" intel nodes resolved from a stored roll at commit |
| Start bias | doc 36 (Civ) | A visible, switchable rule that biases insertion and opening sites toward terrain the brief implies |
| Fair odds | doc 36 cv07, cv09, SL30 | Randomness in situations, deterministic named rewards, loss-side bad-luck protection, disclosed |
| Reactivity and memory | doc 26 §7, doc 28 FP45 | State-variant lines over rolled facts; optional callbacks to earlier playthroughs through versioned `objects.sav` keys with a player-visible reset [runtime P-R10] |

## 6. UX

- **Variety panel.** One dial per mission and per campaign, "How different is each run?": **Fixed** (build-time only, plus cosmetic jitter), **Varied** (PerTurn pools, weather and time, event decks, plus the bounded PerAttempt jitter shipped missions already use: VX02 strength, VX05 waypoint placement, VX07 countdown spreads) and **Wild** (plus PerAttempt layouts and start sets, whose chips read "re-rolls on Retry"). The dial states its promise in one line: at Varied, a Retry keeps the situation and shifts the details, so a failed attempt is neither a re-deal nor a memorised replay (§1.1 row 4, §2.5) [I]. The dial only sets per-axis defaults; each axis stays editable as a chip showing its scope badge (Build / Campaign / Turn / Attempt) and its source (build seed, stored roll, engine per attempt, MP server, lobby).
- **Make it vary** (hand authoring on the map). Select objects or groups and choose **Alternatives**: the selection becomes option 1 and a ghost copy follows the cursor to be dropped as option 2 (up to 7, the `VariationAxis` limit); **One of these** turns several selected groups into one pool; **Maybe** gives a whole group one chance (the VY10 fix). Code picks the lowering from the profile and the mission's place in the campaign (§2.4), adds the default variant, guards triggers and markers, and runs VY15 on every option, so the author never writes a selector [I].
- **Preview N rolls.** "Roll 10" draws ten layouts in the simulator (ported engine table, random start indices) and shows them as ghost overlays on the map: variant positions, a heat layer of spawn frequency, start-marker odds, placement circles drawn as "prefers cheaper ground". Clicking a ghost forces that variant in the next Preview run; a roll strip under the Preview button records which option each run took.
- **Variation Inspector** (glass box). Every roll lists its name, scope, source, options with weights, what each option changes, the player-facing surface, which step and model (if any) produced it, and its validation status. Weights edit in the normal visual editors; pinning an axis freezes it.
- **Variety map view.** Per campaign node: what is authored, what is seeded at build time and what rolls at run time, coloured consistently with the chips.
- **Seed codes and Share.** The code sits on the campaign card with a copy button that wraps it in a code span; the Share dialog offers "operation code (reproduces the no-model campaign)" and "replay record (reproduces this campaign exactly)", each labelled with what it guarantees, plus the Fixed/Fresh play-seed choice. Players see their run's play seed once, as a one-line `hint` in the prologue (where run modifiers are chosen, §3.6), and again on doc 36 cv19's epilogue node ("Operation 41207"). It is kept in its own var because `cmp_seed` advances. Preview can start a campaign from any reported play seed, so a player's bug report is reproducible without the player owning Plotroom, and the author can re-export that run as a Fixed file for a "beat my run" share; the game has no seed-entry screen, so players cannot type one in (`hint` and `format` are observed on 1.99, `docs/research/data/cwa199-observed-commands.csv`; design [I]).
- **Remix button.** Scope and level pickers, a cost line for invalidated text, one undo group, a "what changed" card and a history of seeds with diff and restore.
- **Surprise me and Seed Atlas** (§3.8), both instant and offline.
- **Import.** Existing randomness in imported missions appears as chips with the honest label of §2.7, and a one-click "convert to a variant pool" where VY10 fires.
- **Player-facing disclosure.** Modifiers and presets show one-line rules in the briefing (for players) and in Standing Orders (for authors, doc 33); hidden help is disclosed (cv43 item 8); rolled facts appear as intel, radio or debrief lines (RP6).

## 7. The AI angle

- **Code owns every die** [I, from doc 25 principles and AGENTS.md]. Seeds, decks, pools, weights, lowerings, validation and the balance lab are deterministic code. The model never picks probabilities, seeds or weights, and a T0 run produces the same variety (RAT18).
- **The model picks recipes.** At S0 or on request, code computes ≤ 7 feasible variation recipes (the menu cap; DG006) for a node ("three garrison postures, two insertion points, weather band", "objective in one of four houses"), each with its Variety Budget line; the model ranks or picks a letter, as in doc 25's Pick steps.
- **The model writes flavour** for each variant slot: briefing blocks, radio lines, debrief cause lines, nemesis taunts. Code picks the stratum and the model writes inside it; 2–3 authored variants per event text keep repeats fresh.
- **Diversity comes from code**, not temperature: the model proposes, the seed disposes (§4.6).
- **Cost.** Seeded variety tokens sit after the prompt-cache breakpoint (doc 40 R2–R5), and remix defaults to code-only changes.
- **Untrusted inputs.** Imported replay records, seed codes and mission randomness are data, never instructions.

## 8. Plan, acceptance tests and probes

### 8.1 Phases

| Phase | Scope | Exit evidence |
| --- | --- | --- |
| RV0 | Engine truth: probes P-R1–P-R12 plus doc 29 PR17–PR20 in the in-game probe suite (our own probes, so not rows in `docs/porting/upstream-test-map.csv`, which tracks upstream tests; doc 32 §7); a ported random-table model checked against the ISAAC reference vector (license per doc 02); import chips; lints VY01–VY12 | Probe results per profile; lint tests |
| RV1 | Mission run-time core: `VariationAxis`, lowerings A–C, default variants, budgets, sibling-variant parity (§4.5), the Variety panel, Make it vary gestures, Preview N rolls and force-variant | RAT8–RAT10, RAT14, RAT16 |
| RV2 | Build-time seeds: `RootSeed`/`ItemSeed`, portable PRNG, golden seeds, `SeedCode`, remix levels, Surprise me | RAT1–RAT7, RAT15, RAT18 |
| RV3 | Campaign scale: bootstrap prologue row, PerCampaign and PerTurn axes, shuffle-bag decks, nemesis traits, Event pacing presets, campaign modifiers, balance across seeds, Seed Atlas | RAT13, RAT17 |
| RV4 | MP and extras: roll protocol, param-bitmask modifiers, JIP on Cwr/Ce, reinforcement pacer (after P-R11), cross-playthrough memory (after P-R10), challenge catalogue (the owner decision is made: OWQ-20 (a), D039) | RAT11, RAT12 |

### 8.2 Acceptance tests (thresholds are placeholders)

| # | Test |
| --- | --- |
| RAT1 | 20 T0 seeds of one brief: ≥ 15 distinct archetype sequences; median pairwise normalised edit distance ≥ 0.4; every pair differs on ≥ 3 of RP2's dimensions 1–4; zero lint errors; 100 % compile |
| RAT2 | Same 20 seeds: union site coverage ≥ 60 % of eligible site cells, and no single site used by > 30 % of seeds (hot-spot index) |
| RAT3 | Golden seeds generate byte-identical campaigns on Windows, Linux and macOS CI |
| RAT4 | A replay record round-trips byte-stable, replays with zero model calls, and parks as Stale on a digest mismatch |
| RAT5 | Remix: doc 25 E9 scripts show zero clobbers; a T0 remix of node k leaves every non-Stale node byte-identical |
| RAT6 | The seed-code parser passes an adversarial suite (bad check, over-long, unknown epoch, overflow, mixed case, hyphens, confusable letters) without panicking |
| RAT7 | The Rust LCG reproduces the full 65,536-state cycle; stored-seed parsing rejects 65536 and non-integers; PR20 passes on 1.99 |
| RAT8 | One mission, 10 Preview loads plus 1,000 simulator loads: ≥ 4 distinct enemy layouts, every layout passes VY15 (no unfair spawns), and the worst case stays within §2.7 budgets |
| RAT9 | Each path in §2.2 behaves as the axis's scope declares in the Preview harness (PR18, P-R12) |
| RAT10 | Debriefing Restart and intro loads always produce exactly the default variant, never an empty pool |
| RAT11 | Hosted server plus 2 clients, and a dedicated server: every machine shows the same variant, markers and initial weather step; VY07/VY08 clean |
| RAT12 | Cwr/Ce JIP: a late joiner sees the rolled markers, weather and time (P-R7, P-R9) |
| RAT13 | 20 seeds × 50 lab runs: every seed inside AC06 and AC09; win-rate p10–p90 spread within the placeholder; SL28 clean per seed |
| RAT14 | 100 % of procedural templates pass VY13 and 100 % of rolled axes pass VY14 |
| RAT15 | CI expressive-range non-regression: grid coverage does not drop and e-distance stays within bootstrap bounds unless the generator epoch is bumped |
| RAT16 | Every roll in a generated campaign appears in the Variation Inspector with scope, source, options and weights, and Preview can force each option |
| RAT17 | New Adventure check (§1.4) across 10 seeds of one brief, and its run-time twin across 10 play seeds of one compiled campaign |
| RAT18 | T0 parity: structural variety metrics of a T0 run match a model-assisted run within tolerance; only text metrics may differ |

### 8.3 Probes

| # | Question | Profiles |
| --- | --- | --- |
| P-R1 | Does an assignment inside `presenceCondition` (the roller) set a global that later conditions read? | all; 1.99 first |
| P-R2 | Does nil evaluate false in `presenceCondition`, and which default-layer comparison form works? | all |
| P-R3 | Presence 0 never spawns and 1 always does (the table has no zero) | Cwa199 |
| P-R4 | Does placement prefer cheaper cells or roads? | all |
| P-R5 | Does `isServer` work on 1.99? | Cwa199 |
| P-R6 | `publicVariable` of a string or array on 1.99 (expected to fail) | Cwa199 |
| P-R7 | Do JIP clients get synced time and weather? (One run with doc 41 AP16) | Cwr, Ce |
| P-R8 | Weather drift right after an instant set, and its divergence across MP machines; with doc 41 AP2 (hold) and AP16 (MP drift) | all |
| P-R9 | Do replayed `publicVariable`s reach a JIP client before its `init.sqs`? | Cwr, Ce |
| P-R10 | Does an `objects.sav` marker survive "Begin" and read back with `loadStatus`? | all |
| P-R11 | Cost and responsiveness of an SQS reinforcement pacer loop | Cwa199 first |
| P-R12 | A gameplay-free prologue row with no debriefing: no Restart path re-runs the bootstrap, and restart-from-row of mission 1 keeps the seed | all |

Until the relevant probes pass, profile badges mark the roller and `isServer` targets "Cwr/Ce verified by reading, Cwa199 pending".

## Open questions

1. **Challenge catalogue vs cv43 item 2** (owner decision; OWQ-20): is a numbered, never-expiring catalogue acceptable, and may a "week" index exist at all? *Answered 2026-09-27 (OWQ-20 (a); D039): yes, as T0 data with a baked seed; no week index.*
2. **Opt-in re-roll on restart** (doc 36 open question 2; OWQ-21, then DG038): does SL11 allow a documented exception? *Answered 2026-09-27 (OWQ-21 re-roll (a); D040): not in v1.*
3. **SL11 wording** (DG038, after OWQ-21's seed answer): may one engine `random` draw seed the first `cmp_seed` (`RolledAtStart`)? Needs a doc 29 change. *OWQ-21 chose Fresh (D040); the wording is still DG038's, open.*
4. **Epoch policy**: ship old generator epochs so old codes keep working, or only show the honest mismatch card?
5. **Replay record** name, format and export exception (doc 38 W0, doc 21 open question 7, doc 21 §9.3; DG007, DG010, DG017).
6. **Seed-code details**: final size, check alphabet, how islands from mod sets are encoded.
7. **Bootstrap placement**: prologue row (P-R12) or mission 1 with doc 29's guard. (Replay of a completed row injects that row's snapshot before `InitVehicles` by reading, §2.2; only its runtime check remains.)
8. **Defaults** (owner decision; the play seed is OWQ-21): the Variety dial per campaign pattern, and whether "Fixed (shareable)" or "Fresh each playthrough" is the default play seed. *Play seed answered 2026-09-27 (OWQ-21 seed (a); D040): Fresh by default, Fixed for challenge entries and "beat my run" re-exports. The Variety dial default per pattern stays with the design round.*
9. **Memory across playthroughs** (OWQ-21): is it welcome, and what does the player-visible reset look like? *Answered 2026-09-27 (OWQ-21 memory (a); D040): opt-in per campaign with a visible reset; the reset's look stays open.*
10. **Calibration**: perceptual panel data, CF17 thresholds per pattern, lab combat-model calibration (doc 29 open question 1) for tactical modifier weights, and T0 throughput for the Atlas.
11. **MP "Random" UX** with only two parameter slots, and string payloads on 1.99 (P-R6).

## Sources

**Design talks and articles.** Hess, "Plot and Parcel", GDC 2018 (<https://media.gdcvault.com/gdc2018/presentations/Hess_Brian_PlotAndParcel.pdf>; text extracted locally). Booth, "The AI Systems of Left 4 Dead", 2009 (<https://steamcdn-a.akamaihd.net/apps/valve/2009/ai_systems_of_l4d_mike_booth.pdf>). GameRant on XCOM 2 levels (<https://gamerant.com/xcom-2-procedural-level-detail/>). Game Developer: Solomon on randomness (<https://www.gamedeveloper.com/design/jake-solomon-explains-the-careful-use-of-randomness-in-i-xcom-2-i->), GDC 2018 preview (<https://www.gamedeveloper.com/design/attend-gdc-2018-and-learn-how-i-xcom-2-i-s-procedural-level-design-works>), Hades (<https://www.gamedeveloper.com/design/how-supergiant-weaves-narrative-rewards-into-i-hades-i-cycle-of-perpetual-death>), Into the Breach (<https://www.gamedeveloper.com/game-platforms/road-to-the-igf-subset-games-i-into-the-breach-i->), Spelunky daily (<https://www.gamedeveloper.com/design/the-understated-genius-of-the-i-spelunky-i-daily-challenge>). GamesBeat, War of the Chosen (<https://gamesbeat.com/xcom-2-war-of-the-chosen-upgrades-design-enemies-and-cinematic-story/>). PCGamesN, Solomon interview (<https://www.pcgamesn.com/xcom-2/xcom-jake-solomon-interview>). Sylvester, "The Simulation Dream" (<https://tynansylvester.com/2013/06/the-simulation-dream/>). Kazemi, Spelunky generator (<https://tinysubversions.com/spelunkyGen/>). Yu via GameDiscoverCo (<https://newsletter.gamediscover.co/p/how-spelunky-got-its-procedural-hook>). Vice, Compton on oatmeal (<https://www.vice.com/en/article/nz7d8q/no-mans-sky-review>). Short, "Bowls of oatmeal" (<https://emshort.blog/2016/09/21/bowls-of-oatmeal-and-text-generation/>). Compton, "So you want to build a generator" (search summaries only).

**Wikis and community pages.** UFOpaedia: Second Wave (EU2012), Dark Events, Avatar Project, War of the Chosen, Alien Abductions (<https://www.ufopaedia.org/>). Vigaroe, WotC Second Wave (<https://vigaroe.com/Analyses/XCOM2/SecondWave>). GosuNoob, Character Pool (<https://www.gosunoob.com/xcom-2/character-pool/>). XCOM wiki and PC Gamer on Challenge Mode [V-search]. RimWorld wiki, AI Storytellers (<https://rimworldwiki.com/wiki/AI_Storytellers>). slaythespire.wiki.gg: Map Generation, Custom Mode; Daily Climb [V-search]. Wikipedia: FTL, Into the Breach. Tetris wiki, Random Generator. Minecraft Wiki: World seed, Seed (level generation). Factorio wiki, Map exchange string format. Steam threads on Civ V start bias (<https://steamcommunity.com/app/8930/discussions/0/312265327166600555/>) and Civ VI seeds (<https://steamcommunity.com/app/289070/discussions/0/1813170373218165266/>); CivFanatics on map seeds. Crockford base32 (<https://www.crockford.com/base32.html>). Brogue seed catalogue [V-search] and BrogueCE changelog. Hades Pact conditions [V-search].

**Papers.** Smith & Whitehead, PCG 2010. Summerville, AIIDE 2018. Withington & Tokarchuk, FDG 2023 (arXiv 2304.02366). Bazzaz & Cooper, FDG 2025 (arXiv 2504.05334). Kreminski et al., ERaCA 2022 [V-search]. Cook, Gow, Smith & Colton, Danesh, IEEE ToG 2022. Mariño, Reis & Lelis, AIIDE 2015. Hervé & Salge 2021 (arXiv 2107.02457). Mouret & Clune (arXiv 1504.04909) [V-search]; Gravina et al., CoG 2019 (arXiv 1907.04053). Lehman & Stanley 2011 [V-search]. Shervashidze et al., JMLR 2011 [V-search]. Jiang et al., Artificial Hivemind (arXiv 2510.22954). Doshi & Hauser 2024 [V-search]. Padmakumar & He (arXiv 2309.05196). Azad & Baten (arXiv 2605.06540). Lai et al. (arXiv 2609.16051). Kirk et al. (arXiv 2310.06452). Zhang et al., Verbalized Sampling (arXiv 2510.01171). West & Potts (arXiv 2505.00047). Wong et al., SimpleStrat (arXiv 2410.09038). Zhang et al., NoveltyBench (arXiv 2504.05228). Friedman & Dieng, Vendi Score (arXiv 2210.02410). Shaib et al., AACL 2025 (arXiv 2403.00553). Atil et al. (arXiv 2408.04667).

**Engineering references.** Anthropic Messages API reference; OpenAI cookbook on reproducible outputs; Thinking Machines, "Defeating Nondeterminism in LLM Inference" (2025-09-10); llama.cpp PR #16016; `rand` `StdRng` docs and the Rust Rand Book (crate reproducibility); Rust std `DefaultHasher`, `HashMap`, `f64`.

**Engine source** (static reading at the pinned commits). `EVAL:express.cpp`, `express.hpp`; `RND:randomGen.cpp`, `randomGen.hpp`, `isaac.hpp`; `CWR:AI/AICenterImpl.cpp`, `AICenterImplPreview.cpp`, `ArcadeTemplate.cpp`, `AIArcade.cpp`, `AIRadio.cpp`, `Path/AITypes.hpp`; `CWR:World/WorldInit.cpp`, `WorldSetup.cpp`, `WorldImpl.cpp`, `Detection/Detector.cpp`, `Terrain/Landscape.cpp`, `Entities/Vehicles/Ground/Car.cpp`, `Tank.cpp`; `CWR:Game/Commands/GameStateExt.cpp`, `GameStateExtWorld.cpp`, `GameStateExtUi.cpp`, `GameStateExtGrp.cpp`, `GameStateExtTestAudio.cpp`; `CWR:UI/DisplayUI.cpp`, `DisplayUISetup.cpp`, `DisplayUIMenus.cpp`, `OptionsUI.cpp`, `OptionsUIApp.cpp`, `Map/UIMapDialogs.cpp`; `CWR:Network/NetworkMisc.cpp`, `NetworkClientActions.cpp`, `NetworkClientOnMessage.cpp`, `NetworkClient.cpp`, `NetworkServerMsgOnMessage.cpp`, `NetworkServerMission.cpp`, `NetworkServerSimulate.cpp`, `NetworkScriptValueCodec.cpp`; `CWR:Foundation/Common/FltOpts.hpp`, `Foundation/Platform/InitBridge.cpp`, `GraphicsInitBridge.cpp`. CE counterparts as cited inline. 1.99 executables: string scans only.

**Local corpus** (owner's install, read-only; aggregates only; scripts and outputs outside the repo): random-mechanism statistics per group, group-level presence patterns, duplicate detection, `select` idiom shapes, MP parameter and `publicVariable` counts, campaign variety and text-diversity baselines, max-group config scan. All re-run on 2026-09-27.

**Repo docs.** 04 (§3.3), 13 (sampler), 17 (§10), 18 (§3, §6.1–§6.5, E5), 19 (F11, F12, C21, §5.3, §6.4, open question 7), 21 (§9.3, §12.1, open question 7), 22, 25 (§2.9, §3, §4.3, §6.2, §9.1–§9.3, §10–§11, E2, E9, E10), 26 (§2.2, §7, §8, §9.1, §9.3 modifiers, §9.4, CF03), 27 (fingerprints), 28 (FP08, FP12, FP28, FP38, FP45, CF17, TX05, R6), 29 (K3, K4, §3.2–§3.3, §5.2, SL11, PR17–PR21, E8, AC06, AC09, AC16, row 13, `VarietyCaps`), 31, 32, 34 (§1.2–§1.4, cw02, cw07, cw14–cw19, SL25, MC20), 36 (§3.1 rows 4, 5, 16; cv07, cv09, cv19, cv21, cv43; SL27, SL28, SL30, SL31; `DifficultyPreset` naming note; open question 2), 38 (§4.2–§4.5, W0), 39 (`Tempo`), 40 (TL;DR, R2–R5), 41 (weather, AP2); `docs/research/data/cwa199-observed-commands.csv`. Added in the consolidation pass: 14 (tiers), 22 (T0 packs), 33 (Standing Orders), 40 §2.5, 41 (§3.4, AL03, AL16, AP16); `docs/design-gap-requests/` DG005–DG007, DG010, DG017, DG026, DG033, DG038; `docs/decisions/` D028, D029 and `OWNER-QUESTIONS.md` (OWQ-20, OWQ-21); `docs/upstream/engine-requests.csv`.

## Verification notes

An adversarial pass on 2026-09-27 re-fetched quotes, re-read every engine citation at the cited lines, validated the random-table port against the ISAAC reference vector and re-ran the corpus scripts. Corrections carried into this doc:

- Foertsch's "Enemy Unknown" most likely refers to the 1994 game; the RimWorld page never says "completely independent"; Solomon's line is "give XCOM a personality", not "the enemy".
- No source supports a "seeded" Dark Events pool "larger than any campaign draws"; that sizing is our own rule.
- `objects.sav` survives a new playthrough ("Begin" deletes only `.fps` saves), so victory unlocks and cross-playthrough memory are possible in principle (runtime P-R10).
- The generator is seeded in `World::World`, once per process, not per mission; `randomSeed` in `mission.sqm` is overwritten on load and feeds only licence plates.
- `arr select random count arr` under-weights only element 0 and returns nil at the top, not "both ends".
- An instant weather set starts drift on the next frame, not after 30 minutes.
- ~~`IsConsistent` (63 groups, 12 seats) is an editor check; the load path does not enforce it.~~ Reversed by the engine review below: `ParseMission` runs `IsConsistent` and refuses the file.
- The seed-code size is 34–40 B, not about 30. A draft's `Baked(u16 in 0..65537)` was wrong twice: `u16` cannot hold 65536, and 65536 is the LCG's fixed point anyway.
- Doc 25 already seeds menu diversification; the gap is deriving that seed from the item seed.
- "Weekly and daily challenges" conflict with doc 36 cv43 item 2 and are now a blocked, calendar-free catalogue.
- Still [U]: every probe in §8.3, T0 throughput, perceptual calibration, and whether CF17's run limits match human practice.

### Product review notes

A product and fun pass on 2026-09-27 read the doc against the owner's goal ("every run a new adventure"), the AGENTS.md invariants (weak models succeed, correct by construction, fun, glass box, human edits preserved) and docs 26, 29, 34 and 36 for duplicate concepts. **Verdict:** the design delivers the goal where it matters. Variety sits in the situation, not in shuffled parts (RP1–RP3, VY13–VY14). Surprises are fair and explained (RP4, VY15–VY16). Anti-scum is built into restart paths. Code owns every die, so a weak or absent model gives the same variety (§7, RAT18). Every roll is inspectable and forceable (§6, RAT16). Edits made in place:

- **Run-time twin of the New Adventure check** (§1.4, RAT17). The build-side check alone could pass a campaign whose shipped file plays the same every time. That per-file replay is the case the owner named.
- **Retry promise on the Variety dial** (§6). Varied now includes the bounded per-attempt jitter shipped missions already use, so a Retry keeps the situation and shifts the details. Wild's per-attempt layouts are labelled "re-rolls on Retry".
- **Make it vary** (§6). Hand authors had no direct-manipulation path to a pool, only an import conversion. Alternatives, One of these and Maybe put it on the map, and code picks the lowering.
- **Sibling-variant parity** (§4.5). Nothing stopped one dealt layout from being far harsher than its siblings. It reuses doc 28 FP28's force-ratio count instead of a new metric.
- **Play seed shown to players** (§6). A one-line hint in the prologue and on the epilogue makes a player's bug report reproducible in Preview and gives players a number to compare.
- **No duplicate concepts.**
  - `VariationAxis` is doc 26 §9.1's type, and the budgets fill doc 29's `VarietyCaps` (§2.9).
  - The Programs deck deals doc 34's existing programs instead of adding a second clock (§5). Complication cards fill cw07's single slot (VX08).
  - Campaign modifiers are `CampaignModifier`, apart from doc 26's per-node `Modifier`.
  - Renames: Undermanned → Thin roster, Veteran enemy → Seasoned enemy (the game's own difficulty mode), Tempo preset → Event pacing preset (doc 34's tempo counter, doc 39's `Tempo`). All names remain placeholders for the design round.

Residual product concerns, not edited:

- **Default play seed** (open question 8). The product recommendation is Fresh each playthrough for campaigns. Fixed is for challenge entries and "beat my run" re-exports. The owner adopted this on 2026-09-27 (OWQ-21 (a); D040).
- **Knob count.** The dial, per-axis chips, campaign modifiers, event pacing, the play-seed policy, four remix levels, Surprise me and the Atlas are a lot at once. A newcomer should see only the dial and Roll 10, with the rest one step away. This should be mapped onto doc 31's ladder and the Easy view (DG033 item 3, decided, D029: the Easy/Advanced switch stays as a view preset, default Advanced).
- **Cast is fixed per file.** People rank second in RP2, but VX11 defaults to Build, so two playthroughs of one file share every name. Consider PerCampaign cast as the Varied default when the roster module is on.
- **Seed codes are long.** At 55–64 symbols they are copy-paste only. A short form for vanilla fingerprints would help (open question 6).
- **Wild in campaigns allows re-rolling a layout by restarting.** This is acceptable only because every layout passes VY15 and the parity band. The Exploiter policy (SL28) does not model tactical restarts.
- **Tactical fairness stays [U]** until Preview playtests. The parity band is a heuristic, not a measurement.
- **Reading order.** Engine facts come before the author experience. A reader who wants the author's view should go from the TL;DR straight to §6. A short author walkthrough would help the design round.
- **Sibling back-references.** Doc 34 §1.2 and doc 26 §9.3 do not yet point back to the mappings above. They should when they are next revised.

### Engine review notes (2026-09-27)

An adversarial engine pass on 2026-09-27 re-read the randomisation, presence, load-order, restart, multiplayer and budget claims against `BohemiaInteractive/CWR@ffc61838b7` and `ofpisnotdead-com/CWR-CE@b67bf3bd62` (the relevant `Random/`, `AICenterImpl.cpp`, `WorldInit.cpp`, `UIMapDialogs.cpp`, `DisplayUIMenus.cpp` and `express.cpp` files hash identical), against docs 04, 18, 19, 26 and 29, and against string scans of the two 1.99 executables. It recomputed the seed-collision figure over the ported table. Corrections made in place:

- **The group and seat limits are enforced at load, not only in the editor** (§2.7, VY11, TL;DR). `ParseMission` → `ParseCutscene` runs `IsConsistent` and refuses the section (`CWR:UI/Map/UIArcadeWaypoint.cpp#L966-L970`, CE identical), as doc 04 already recorded. In a campaign the refused mission is booked like a cutscene-only entry and the loser outro plays, so the campaign moves on down the lost branch (`CWR:UI/OptionsUIApp.cpp#L860-L875`, `#L1015-L1048`). The earlier note saying the opposite is struck through above. The 12-unit cap counts crew seats over every entry, gated ones included.
- **The debriefing Restart is an anti-scum hole, and its finisher is unsafe** (§2.2, §2.5, TL;DR). The whole attempt runs without campaign variables, not only the load. `GStats` is restored as it stood when the debriefing opened (`UIMapDialogs.cpp#L677`, `#L898`), so it keeps the failed attempt's commits. A nil assignment deletes the global (`EVAL:express.cpp#L2505`) and `saveVar` of a missing variable is a no-op (`CWR:Game/Commands/GameStateExtGrp.cpp#L417-L420`), so derived commits vanish while constant flags still commit. A bootstrap guard on that path would overwrite the stored seed, because `AddVariable` replaces by name (`CWR:AI/AICenterStats.cpp#L69-L80`). Doc 29 row 13's guard must therefore sit in every mission with stored rolls, not only the bootstrap fallback.
- **Replay of a completed row injects the row snapshot before `InitVehicles`** (§2.2, open question 7). It was [U]. Replay sets `GStats._campaign` to the row's stats (`OptionsUIApp.cpp#L532-L533`), and the shared `IDD_INTRO` load path injects them (`#L850-L895`), so Replay shows the originally played variant.
- **Entropy and odds** (§2.1, §3.2, TL;DR). The generator state is only the 15-bit index, so a second consecutive draw adds nothing. The table is a fixed sample: presence 0.4, 0.5 and 0.7 pass 39.6 %, 49.7 % and 70.2 % of start indices. A one-draw play seed repeats about once per 16,500 pairs (Σp² over the table, up to 7 repeats per value), not once per 20K, and `random 65536` reaches only even seeds.
- **Load-time stream consumption** (§2.1). One draw per presence check even at presence 1, 200 per placement radius, and up to 200 per randomised waypoint (`AICenterImpl.cpp#L641-L644`, `#L700-L703`, `#L1530`).
- **Cross-layer hazards** (§2.1, VY09, VY18). Cargo whose transport is absent stands at its own editor position (`#L1572-L1595`). `SynchronizedItem::IsActive` skips partners that were never created (`#L786-L807`), so a sync line into an absent layer stops holding; the runtime effect is unverified.
- **Roller placement** (§2.4). "First-created" is pinned to load order, and a group on an otherwise unused side creates that side's centre (`CWR:AI/AICenterStats.cpp#L1328-L1346`).
- **Floor idiom on 1.99** (§2.1). `mod` and `%` are both `fmod` in CWR. The 1.99 evaluator's string block shows `%` but no separate `mod`, and string pooling makes that inconclusive, so doc 29 PR20 should test both. The `floor`/`ceil` strings in the 1.99 executables are the C runtime's math names, not script commands.
- **Multiplayer** (§2.6, TL;DR). Marker locality is V by reading only for Cwr and Ce (`createMarker` included); Cwa199 is inferred. JIP replay of `publicVariable` happens only when `description.ext` sets `joinInProgress`, and is capped at 10,000 stored messages. JIP clients run `initPlayerLocal.sqs` and `initJIP.sqs`; whether they also run `init.sqs` was not found by reading (unverified). None of the JIP strings is present in either 1.99 executable. The "ready flag last" protocol now waits for every rolled number as well, since the transport's ordering of guaranteed messages was not verified. `createUnit` into a remote group asks the owner to create the unit (`GameStateExtWorld.cpp#L300-L307`).
- **VY19** exempts doc 41's hold pair, which repeats the current values and cancels no ramp.

Confirmed unchanged by reading: no script path seeds `random` or saves its index; presence and `presenceCondition` apply only to non-playable units and to empty vehicles, sounds and mines, and run before unit init lines and `init.sqs`; nil propagates through operators and reads false, without a type error; the intro path injects variables after `InitVehicles`; restart-from-row and Retry without an autosave replay stored rolls; only the server runs `InitVehicles` in MP; the server sets and broadcasts `param1`/`param2` before it; string scans find no `createGroup`, `createMarker`, `createTrigger`, `addWaypoint`, `setDate`, `remoteExec` or `isJIP` in either 1.99 executable, and do find `isServer`, `setFog`, `setRain`, `titleParam1` and `presenceCondition` (string evidence, so [I] for runtime); and the LCG cycle from 0 covers 0..=65535 with 65536 fixed. Still unverified: all of §8.3, doc 29 PR17 and PR20 on 1.99, the runtime effect of cross-layer synchronisation, JIP `init.sqs`, and in-order delivery of guaranteed messages.

### Consolidation pass (2026-09-27)

This doc was left out of consolidation part 1 while it was being written. This step checked it against the owner's renames and decisions (`docs/decisions/`), the design-gap index (DG001–DG034), the owner questions (OWQ-01–OWQ-23) and the corrections other docs made in part 1. No engine fact, lowering, lint rule, budget or acceptance test changed meaning.

- **Renames (D028).** The doc's one Standing Orders mention (§6, player-facing disclosure) now says who reads what: the briefing is for players, Standing Orders (doc 33) for authors. The doc never named the live tutorials and had no links to doc 33's file or `skills/standing-orders`.
- **Design-gap and owner-question filing.** §3.7's challenge catalogue, which the doc said was "to be filed", is already owner question OWQ-20 in `docs/decisions/OWNER-QUESTIONS.md` (TL;DR and open question 1 point there). The default play seed, memory across playthroughs and the opt-in re-roll (§2.5, §3.2, open questions 2, 8–9, the product review, and doc 36 open question 2) are OWQ-21. No design-gap request duplicates them; DG038 (technical) only words the SL11 rule that follows OWQ-21's answer (if Fresh is chosen, SL11 names the single bootstrap draw as its one exception; open questions 2–3 and §2.5, §3.2 point to it). The Variety dial default per pattern and PerCampaign cast stay in open question 8 and the review notes for the design round. §3.4's "two design gaps" were already covered: DG007 (recipes become exemplar libraries), DG010 ("replay" means re-driving from the journal with no model call, the sense "replay record" uses; the game's own campaign-book Replay stays a game term) and DG017 (journal storage and what leaves the machine); open question 5 points to all three, and DG010 and DG017 now list this doc. Other pointers: DG005 (codes header, and the new note that "T0" means two things across docs 14, 22 and 25), DG006 (§7's ≤ 7 recipes), DG026 (§3.1's temperature facts), DG033 item 3 (decided, recorded as D029; the Easy view for the knob-count concern).
- **Corrections carried in.**
  - §3.1: doc 40 §2.5 records the per-model refusal of `temperature`, `top_p` and `top_k`; this doc's "rejects temperatures other than 1.0" is kept as fetched, and the gap between the two wordings is flagged, not resolved.
  - §3.6: doc 26 §9.3 gained doc 35 rc81's three candidate modifiers in part 1; the per-node list now mentions them.
  - §8.1 RV0: our own probes are not rows in `docs/porting/upstream-test-map.csv`, which tracks upstream tests only (AGENTS.md; doc 32 §7 says the same). Doc 33 §8 has the same slip and is left to its own pass.
  - VX06: doc 41 §3.4 requires the hold pair in the same frame as the instant set; the row says so.
  - §2.8, §8.3: doc 41, written in parallel, already has AL03 and AL16 (VY19's first clause, VY08's weather clause) and AP16 (MP weather drift, overlapping P-R7 and P-R8); each pair now shares one finding or one probe run.
- **Engine requests.** The gaps met here are entries in the engine-requests register (AGENTS.md), `docs/upstream/engine-requests.csv`, created in the same pass: ER-093 (no script command sets or saves the generator's seed or index), ER-026 (the debriefing Restart runs without campaign variables; doc 18's CE patch E5), and ER-043, ER-044, ER-094 to ER-096 and ER-101 for the other limits of §2.1, §2.6, §2.7 and §3.6. DG034 records how engine limits are routed there.
- **Checked, unchanged.** Doc 40's campaign costs ($8.88 at Standard budgets, $3.52 with every lever, text slots ≈ 70 %) match §3.5; doc 26 §8.2, doc 29 SL11 and row 13, doc 36 cv43 and doc 19 open question 7 read as cited; the doc 25 section numbers cited here all exist.
- **Length.** The file is about 615 lines, just over the ~600-line ceiling; splitting it was out of scope for this step.

### Owner answers (2026-09-27)

- The owner answered OWQ-20 (a) and OWQ-21 (seed (a), memory (a), re-roll (a)); the rules are D039 and D040. The TL;DR, §2.5, §3.2, §3.7, §6 (review notes), §8.1 RV4 and open questions 1–3, 8 and 9 now state the answers by pointer; the Variety dial default per pattern, the look of the memory reset and DG038's SL11 wording stay open. No design, lint, budget or acceptance test changed.
