# Lessons from Civilization V (and Firaxis) for Plotroom

Research doc 36 for Plotroom (`ofp-editor`). Research date: 2026-09-27. Audience: contributors and LLM coding agents. This file is meant to be read on its own.
Question answered: *Sid Meier's Civilization V* (2010), with *Gods & Kings* (G&K, 2012) and *Brave New World* (BNW, 2013), was acclaimed and famously hard to put down. What made it good and "one more turn" addictive, what went wrong, what did the expansions fix, and which lessons should shape Plotroom, both for **mission makers** (our users) and for **the players of their missions and campaigns**?

**Status.** Proposal-only. Every Plotroom design here is **[I]**. Every number (threshold, cap, count) is a placeholder for the balance lab (doc 29 §5.2) or for playtests to tune.
**Epistemic legend.** **[V]** verified against a fetched source (cited). **[V-search]** seen only in a search-result snippet, because the page refused the fetch. **[V-secondary]** a fetched secondary page quoting a primary source we could not read (for example a review quoting the memoir). **[I]** our inference or design transfer. **[U]** unverified or unresolved. "As reported" marks a journalist's rendering of a talk, not a transcript. An adversarial pass on 2026-09-27 re-fetched the quotes and compared them word for word; §3.2 lists what it corrected.
**Rules for this file.** Quotes are short and attributed to one named source (doc 28 rules). Civ terms never enter prompts, exemplars or generated content; the design-sensibility pack never names a game. Nothing here refers to private or unpublished work.
**Companions.** Docs 21 (agent doctrine), 25 (weak-model harness), 26 (campaign content), 28 (fun) with the pack in `prompts/design-sensibility/`, 29 (XCOM-like strategic layer), 31 (no-code ladder), 32 (cinematics), 33 (Standing Orders and Drill: the concept manual and live tutorials), 22 (plugins), 27 (addons and mods) and 34 (Iron Curtain second pass). Doc 29 already carries the XCOM fairness evidence (Solomon); this doc adds the Firaxis 4X side and does not repeat it.
**Codes already in use (do not reuse):** doc 19 C01–C21; doc 26 CF01–CF12, P1–P8; doc 28 MC01–MC19, CF13–CF18, TX01–TX06; doc 29 SL01–SL20, PR01–PR23, P9, E7–E14; doc 27 D1–D8; doc 34 CF19–CF25, SL21–SL25, MC20–MC29, D9 (provisional); the L-series of docs 23–24. This doc's new codes (SL26–SL31, CF26–CF27, MC30–MC31, TX07) are **provisional**; the design round assigns the final numbers. Row IDs `cv01`–`cv44` are local to this doc.

## TL;DR

- **The pull is engineered.** Civ V runs four or five progress tracks at once that finish at different times, each shown as "N turns to X", so some payoff is always close (Sullla; Madigan) [V]. The *resumption* tendency behind "one more turn" survives a 2025 meta-analysis; the Zeigarnik *memory* effect does not [V-search]. → Doc 29: every counter reads "in N ops", and a horizon-mix check (SL26) keeps completions staggered between camps. Camps, act breaks and the finale are exempt, so threads can close together there and the player gets a natural place to stop (§4.5).
- **Interesting decisions have no dominant option, and the best one depends on the situation** (Meier, GDC 2012 [V]). "A game is a series of interesting decisions" is Meier's line by his own account, but its date and wording are unverified [U]; doc 28 §4 should stop dating it to 1989. → The balance lab checks every strategic menu for dominated or never-situational options (SL27).
- **Fairness is felt, not computed.** Players expect to win at 3:1, rage at streaks and credit wins to themselves (Meier, GDC 2010, as reported [V]); hidden help may only favour the player (Johnson; Solomon [V]). → Bad-luck protection in doc 29's stored rolls, risk bands on cards, deterministic payoffs (SL30) and telegraphed enemy advantages (MC31).
- **Civ V's launch problems were coupled-system problems.** One unit per tile (1UPT) jammed maps, slower production then caused waiting, and the AI could not play the rule, so difficulty fell back on handicaps. Global happiness walled off expansion, and the culture victory was passive (Shafer 2013; Beach 2013 [V]). → Every strategic-layer rule passes the balance lab for second-order effects, AI-executability and counterplay (SL31) before adoption.
- **The expansions rebuilt the back half** because players quit before the end (Beach [V]). The series still struggles: fewer than half of Civ VI games were finished (Beach 2024 [V]), and Civ VII's forced civ-switching at age transitions drew a backlash; a 2026 update made the switch optional [V as reported]. → Back-half novelty (CF26), decided-state detection with an early finale (SL29), and act breaks that never wipe what the player earned.
- **Several ways to win, none passive.** BNW made the culture victory interactive (Beach [V]). → Campaigns offer ≥ 2 ending routes, each with a visible progress track, each needing the player to act (CF27, MC30).
- **A legible opponent beats a clever one** ("a clear rhyme and reason behind their actions", Shafer [V]); opaque diplomacy read as random [V]. → Enemy commanders get typed personalities that drive behaviour, radio register and music. Every "why" in a debrief is computed by code.
- **One dominant control names the blocker** (the end-turn button [V]). → The readiness coach becomes the editor's single "Next issue" button that turns into "Preview", with blocking and advisory items kept apart, snooze and an audited override (doc 21 §11.1).
- **Help at the point of need, generated from rule data.** The Civilopedia opens on F1 and on right-click [V]; the Enhanced User Interface mod (EUI; 779,460 downloads shown on 2026-09-27) builds tooltips from "game XML data … rather than hardcoded blurbs" [V]. Definitional advisor pop-ups were ignored [V]. → Doc 33's registry is right. First-opening tips must speak about the instance, and an expert-density mode ships in v1 (Shafer wanted an "'expert' switch" and did not get it [V]).
- **Modding is a product.** Civ V's SDK mostly packaged files, hooks were missing, the API was undocumented, and modded play lost achievements and multiplayer [V/V-search]. Creators mostly made identities (civilizations, leaders, units) and maps, not scenarios [V counts; I reading]. → T0 packs for factions and compositions first, hook docs generated from the registry, and pack-built missions that compile to vanilla, so nothing is second-class.
- **Keep the expected third.** Meier's 33/33/33 rule, as told by producer Dennis Shirk [V]: the faithful 2001 editor is Plotroom's expected third and must be complete in v1.
- **Healthy pull, not compulsion.** Judge engagement by regret, consent and transparency, not by a blacklist (Deterding et al. [V]); optimise need satisfaction, never time played (Przybylski et al. [V-search]). → An engagement-ethics checklist (§4.5): clocks count ops, not hours; no streaks, dailies or grind; every op ends at a natural stopping point.

## 1. Why Civ V was addictive: the mechanisms

### 1.1 Overlapping tracks that finish at different times

- **Evidence.** Sullla's BNW review (Oct 2014): "The fun in the Civ5 gameplay comes from trying to juggle four or five different things at once, and get them all to line up at the same time without running into a bottleneck." [V]. Jamie Madigan (2013-03-06) ties "just one more turn" to unfinished goals: it is "almost always in the service of completing some structure, upgrade, technology, or conquest" [V]. He also notes that the Zeigarnik effect "isn't completely reliable" [V].
- **Mechanism.** An interrupted goal pulls the player back to finish it. A 2025 meta-analysis (Ghibellini & Meier; the second author is Beat Meier, a psychologist, not Sid) found no general memory advantage for unfinished tasks, but a general tendency to *resume* them, the Ovsiankina effect [V-search]. Effort also rises as a reward nears and drops right after it pays ("post-reward resetting", Kivetz, Urminsky & Zheng 2006, a coffee-card field study) [V-search]. With staggered completions, the moment when every track is done never comes [I].
- **Cost.** The same mechanism gives no natural stopping point [I]. Late in a game, when every track is long, the pull turns into tedium (§2).

### 1.2 Progress as a countdown, on the object and in one overview

- Progress reads as turns remaining. The F8 victory overview "provides some information to how close each civ is to a victory condition" (CivFanatics, 2016-10-15) [V]; "some" means full coverage of every civ and victory type is not verified.
- Players wanted more counters than vanilla gave. EUI's growth meter "turns red when city is starving, and shows turns to population decrease" [V]. The EUI page showed 779,460 downloads when checked on 2026-09-27; its last update is dated 2025-07-14 [V].
- **Mechanism [I].** A countdown turns accumulation into a near, dated promise, and a rival's visible progress gives the player a reason to interfere.

### 1.3 One dominant control drives the loop

- Shafer: "The size of each interface element reflects its relative importance, e.g. the end turn button is bigger than the button which shows toggleable map options." [V]. The button also carries the next required action, such as an orange "Choose Production" or a unit that needs orders [V-search].
- Ambiguity is costly. In launch week a player lost "5-10seconds" believing "Please wait" was still in progress, and another replied: "Next turn shouldn't be next turn if there are units still needing orders." (CivFanatics, 2010-10-03) [V]. A prompt that could not be cleared was also reported [V-search, title only].
- **Mechanism [I].** The label doubles as the most important notification, so the loop drives itself and no decision is forgotten.

### 1.4 Decisions with time horizons, made in calm

- Meier (GDC 2012, reported by Leigh Alexander): "Good decisions are situational." Interesting trade-offs include time horizons, such as an immediate chariot against a long-term wonder [V].
- Soren Johnson (2009): Meier first prototyped Civilization in real time, but "players were overwhelmed by the high number of new game systems they needed to juggle at once"; after the switch, "the phrase 'just one more turn' entered the gaming lexicon". His reason: "By removing time pressure, turn-based games allow players to adjust the learning curve to their own needs." [V].
- Ed Beach (2024, as embedded by Chris Kerr) contrasts "important, strategic decisions you don't have to make more than every five to 10 minutes" with "tiresome 'click here, click here, click, here' decisions" [V].

### 1.5 A generous opening, surprises and short side goals

- Early exploration pays: ancient ruins ("this game's version of the old goody huts"), natural wonders, and 15 or 30 gold for first meeting each city-state (Sullla) [V].
- City-states post short quests, some timed up to 30 turns, with Friend and Ally thresholds at 30 and 60 influence [V-search]. SpaceSector (2010-12-28): city-states give "more depth to diplomatic relations, more decisions to be made" [V].
- **Caveats (Sullla [V]).** Free stuff "undermines the rest of the gameplay and makes it less compelling"; many quests reward "things that he or she would have done anyway".

### 1.6 Personalities, presentation and closure

- Leaders are fully animated and speak their native languages; the AI carries "26 flavors" on a ten-point scale whose values vary slightly per game (Wikipedia) [V].
- Composer Michael Curran kept each leader's theme "recognizable to some extent" across its 'peace' and 'war' versions, and "each quadrant of the screen calls a soundscape" (VGMO interview; the page is undated but refers to the release "last month", so c. late 2010 [I]) [V]. Sullla credits "the beautiful map and the oustanding [sic] music" with reinforcing the 'One More Turn' feeling [V].
- The victory screen closes the story with Info, Demographics, Ranking ("your final score associated with a historical figure") and Replay: Messages, Graphs and a Map showing "the progress of the whole map" (CivFanatics) [V].
- Stories spread from readable quirks. Civ Battle Royale, an AI-only 42-civ game run on r/civ from 2015-02-20 [V-search], drew fans through "updates, maps, status reports and even gifs"; Kotaku (2015-03-19) reported that it took "twenty minutes just to load" and crashed at turn 239 [V]. Myths spread just as well (Nuclear Gandhi, §3.2).

### 1.7 Help is always one click away

- GameSpot (Kevin VanOrd, 9/10): "a friendly interface and expansive Civilopedia help newcomers get up to speed relatively quickly" [V-search]. F1 opens the Civilopedia (Steam, 2018) [V]. Right-clicking a tech opens its entry; a 2010 bug report says it "opens in the background" behind the tech tree [V].
- Shafer: "I'm particularly proud of what our team accomplished with the UI." [V].

### 1.8 Where the pull turns sour

- Critic Luke Plunkett (Aftermath Hours, 2025-02-14, on Civ VII): "It's like a slot machine." and "the point is, are you enjoying yourself while you're doing it?" [V; an opinion, not evidence].
- Przybylski, Weinstein, Ryan & Rigby (2009): low need satisfaction went with obsessive passion, more play, tension after play and lower enjoyment; high need satisfaction went with harmonious passion and energy after play [V-search, abstract; correlational]. Vuorre et al. (2022; about 39,000 players, publisher telemetry) found "little to no evidence for a causal connection between gameplay and well-being", while "motivations play a role" [V].
- **For us [I].** Civ's continuous turns never offer a natural place to stop. Plotroom's op and camp structure does, and we should keep it that way (§4.5).

## 2. What went wrong, and what the expansions fixed

| Problem at launch | Evidence | Root cause [I] | Later change | Lesson |
| --- | --- | --- | --- | --- |
| Map congestion, then waiting | Shafer: every unit "needed its own tile, and that meant the map filled up pretty quickly"; "I slowed the rate of production, which in turn led to more waiting around for buckets to fill up" (via QT3) [V] | One core-rule change cascaded into pacing | Beach defends 1UPT ("so much more tactical maneuvering and positioning") and says G&K eased naval congestion [V]; Civ VII's Commanders "pack nearby units into a single 'stack'" [V] | Simulate second-order effects; judge a rule by its typical case, not its best case |
| AI could not play its own rules | Shafer: in Panzer General "their AI didn't actually need to do anything" [V]. PC Gamer: the AI has "a bad habit of wheeling its long-range artillery directly up to my melee units" [V-search]. The AI drew the most common criticisms (Wikipedia) [V] | Tactical depth beyond the AI | No verified fix in this research [U] | Ship only mechanics the AI can execute |
| Difficulty through handicaps | CivFanatics lists 8 levels, Settler to Deity, with tables of handicaps only: free techs, extra units at King and above, work, growth and train modifiers [V]. Reading this as "bonuses instead of better play" is ours [I] | A weak AI compensated with stats | — | Label difficulty honestly; each rung changes what it says |
| Global happiness wall | Shafer: happiness "strongly encouraged you to stay small and the penalties for not obliging with this demand were quite harsh"; "Penalties should be challenges to overcome, not an insurmountable wall to be frustrated by." [V] | A global metric fought the genre's expansion fantasy | BNW games were "dominated by 'Tall' empires, civilizations comprised of 3-5 cities" (Sullla) [V] | Penalties need counterplay and must not scale with success |
| Opaque diplomacy | Shafer: "My original goal was for the AI leaders to act human." "Any attempt to do so just turns into random, unproductive noise." [V]. SpaceSector: "erratic, random or illogical" [V] | Simulated moods the player could not read | Sullla: BNW diplomacy is "VASTLY improved" [V] | Readable goals over simulated moodiness |
| No scarcity, no trade | Shafer: "easy access to a bit of every resource and there was almost no reason to trade" [V; one source] | Resources spread too evenly | — | Scarcity creates interaction |
| Passive, shape-forcing culture victory | Beach: "it was very passive"; it "pretty much required empires of four or fewer cities" [V] | A win path with no interaction and a hidden constraint | BNW tourism: "You not only have to build it, you have to spread it to the rest of the world." [V] | Every path to victory engages the opposition |
| Late-game tedium | Shirk: "If a player is going to run out of things to do, it will be in the second half." Sullla: the second half of the tech tree "has almost nothing interesting on it" [V] | Discovery ends while every track gets longer | BNW's goal was that players feel "this back half of the game was actually the best part of the game" (Beach); IGN credited tourism and ideologies with removing the tedium (via Wikipedia) [V] | Design the back half with new decisions |
| Expected features cut | Religion was cut because a converted civ "would be your ally forever" (Shafer 2010) [V] | Several core changes at once | G&K brought religion (EUI tooltips cover "active Pantheon/Religion beliefs" [V]); IGN: "I can't imagine playing Civilization V without it" [V] | Keep the expected third (§3.1 row 15) |
| Windfalls and randomness | Sullla: free stuff "undermines the rest of the gameplay"; "too much emphasis on randomness" [V] | Unearned power weakens trade-offs | — | Tie rewards to actions; cap random swings |
| Modding second-class | Sukritact: the SDK "existed purely as a means to package files together into a mod"; Tomatekh: "missing a lot of obvious Lua hooks" [V]. Mods disabled achievements; the multiplayer mods menu was commented out [V-search] | Hard-coded behaviour, no API guide | DLL source announced for the 2012 Fall Patch [V; release V-search]; MPPatch and mods packaged as DLC as workarounds [V-search] | Modding is a product (§4.3) |
| Experts wanted more information | Shafer: "we didn't end up with as many information overlays, screens or modes as I would have liked"; he had wanted "an alternate 'expert' switch that you could flip" [V] | A clean default with no expert layer | EUI filled the gap [V] | Ship the expert mode |

- **Reception [V].** Metacritic (per Wikipedia): base game 90 (70 reviews), G&K 80 (53), BNW 85. IGN (9.4) called BNW the "best Civilization expansion so far". GamesBeat (2016-02-18) reports "8 million for its latest, 2010's Civilization V and its expansions".
- **Fixes brought new problems [V].** Sullla on BNW: tall-empire dominance, ideologies as "simply filler material" (our paraphrase of his argument that policies and religion were already enough), and "pointless busywork, stuff that exists for the point of having stuff to do".
- **The designers disagree, and both are right [V].** Beach thought Shafer "was a little harsh on it" (QT3), and Shafer himself calls Civ V's combat "better in Civ 5 than in any other entry in the series". The upside and the cost of 1UPT were both real.
- **The series-level problem outlived the fix.** Beach (2024) put Civ VI's completion rate at "less than 50 percent" [V]. Civ VII's ages were meant to "reset the board a little bit and simplify things out" [V, as rendered by the outlet]. Pixelkin (2025-05-27) reported recent Steam reviews at "Mostly Negative", calling the era switch "jarring and annoying, resetting many accomplishments and situations" [V]. The 'Test of Time' update (2026-05-19) made civ-switching optional, and games.gg (2026-06-06) reports Take-Two's CEO Strauss Zelnick saying "we got it wrong with Civ VII, but it wasn't for want of trying." [V as reported]. Beach led the design of G&K and BNW [V], so the problem persisted across the series [I].

## 3. Sid Meier and Firaxis design principles

### 3.1 Principles, in verified wording

| # | Principle | Verified wording and source | Tag |
| --- | --- | --- | --- |
| 1 | Interesting decisions | "Good decisions are situational."; "It's almost worth erring on the side of providing the player with too much information" (Meier, GDC 2012, Alexander, Game Developer 2012-03-07). He framed it by "what is not an interesting decision": players always picking the first option, or picking at random (paraphrase) | [V] |
| 2 | Acknowledge every decision | "The worst thing you can do is just move on. There's nothing more paranoia-inducing than having made a decision and the game just kind of goes on." (same talk) | [V] |
| 3 | The player is the star | "Players are very much inclined to accept anything you give them and gladly feel it was their own incredible play or strategy." (Graft, Game Developer 2010-03-12); Meier's "Winner's Paradox": "the threat of punishment is enough to keep it interesting, but in the end, the player should win the game." (Schramm, Engadget 2010-03-14) | [V as reported] |
| 4 | Felt odds are not odds | At 3:1, "about 25 percent of the time, the computer opponent would beat the odds", and testers hated it; losing twice in a row enraged players, so results began to account for earlier battles (Civ Revolution; AV Club 2010-03-13). Dyson's summary: "Players expect to win battles at rates far greater than the odds they face" | [V as reported] |
| 5 | Randomness with care | "Any kind of randomness needs to be treated with a lot of care. Whenever something random happens to the player, paranoia sets in." (Graft). On the tech path, players "didn't want it to appear randomly; they wanted it quickly... Players want to be in control." (Perry, VentureBeat 2010-03-12) | [V as reported] |
| 6 | The first 15 minutes | "You almost cannot reward the player enough in the first 15 minutes of a game" (Graft); Perry's report agrees. One attendee's notes say 50 minutes [U] | [V as reported] |
| 7 | Let imagination work | "We don't have to literally show players everything cool" (McWhertor, Kotaku 2010-03-12) | [V as reported] |
| 8 | Consistency and moral clarity | The player "promises to suspend his disbelief"; "For some games, it's important to remove the moral dilemma and provide moral clarity." (Tito, The Escapist 2010-03-12). Meier scopes it himself: "For some games" | [V as reported] |
| 9 | A ladder of difficulty rungs | Civ IV "features an impressive nine difficulty levels"; "Everyone wants to be above average" is Kotaku's framing | [V as reported] |
| 10 | Double it or cut it in half | "One of my big rules has always been, 'double it, or cut it in half.'" (memoir excerpt, PCGamesN 2020-09-01); "If a unit seems too weak, don't lower its cost by 5%; instead, double its strength." (Johnson, 'Sid's Rules', 2009) | [V] |
| 11 | Find the fun by playing | "I won't ponder for hours whether a feature would be a good idea, I just throw it in the game and find out for sure." (memoir, PCGamesN); "the primary job of a game designer is not to make something fun, but to find the fun" (memoir, Goodreads highlight) | [V]; [V-secondary] |
| 12 | One good game beats two great ones | Covert Action's action sequences were so intense that "by the time you got out, you had no idea of what was going on in the world." (Johnson 2009); "combining two great games had somehow left me with zero good ones." (memoir, AltChar 2020-10-13) | [V]; [V-secondary] |
| 13 | The player should have the fun | Failed designs were those where "either the designer or the computer was the one having the fun, not the player." (Johnson 2009) | [V] |
| 14 | Do the research after the game | "the player shouldn't have to read the same books the designer has read in order to be able to play." (Johnson 2009) | [V] |
| 15 | The rule of 33s | "one of Sid's cornerstones … It's 33 percent new, 33 percent improved, and 33 percent what everybody already expects to be there." (producer Dennis Shirk, Game Developer 2010-06-11) | [V] |
| 16 | Players optimise the fun out | "Given the opportunity, players will optimize the fun out of a game." Civ III's preserved random seed made some fans feel cheated, so it became an option at game start, and "the game, by default, discourages this work-intensive strategy." (Johnson, 'Water Finds a Crack', 2011) | [V] |
| 17 | Fun per unit of time | "a possible formula would be (total fun) = (meaningful decisions) / (time played)" (Johnson 2013); offered as a heuristic, not a law | [V] |
| 18 | Two levels, few things | "think of their interfaces as having two levels: a teaching level and a reference level"; "Players must be able to mentally track their in-game options at one time." (Johnson, 'Seven Deadly Sins', 2008, reprinted 2013) | [V] |
| 19 | Fairness belongs to the player | "When the question is one of fairness, the player is always right."; "single events based on hidden mechanics need to be handled with great care" (Johnson 2009) | [V] |
| 20 | Rules carry the meaning | "meaning emerges from a game's rules - the set of decisions and consequences unique to each one" (Johnson, GDC 2010 session description) | [V] |
| 21 | Legible AI | AI players "do need a clear rhyme and reason behind their actions"; "the only thing which matters in a game is the experience inside the player's head." (Shafer 2013) | [V] |
| 22 | Framing (Blizzard, same GDC session) | WoW's rest penalty was reframed as a bonus: "The math ended up being exactly the same, but players loved this new system." (Rob Pardo, via Leahy, Shacknews 2010-03-15) | [V as reported] |

### 3.2 Misattributions and corrections

| Often repeated | What the sources support | Tag |
| --- | --- | --- |
| "A game is a series of interesting decisions" (Meier, GDC 1989) | Meier: "I did say that once many, many years ago", in a GDC talk he recalls as "ten rules of game design" or similar (Civilization Chronicles interview, via Goodfellow 2008). Year and wording unverified. The 1997 Usenet version ("The decisions must be both frequent and meaningful.") was posted by Darren Reid, not written by Meier. A 2021 Game Developer community blog repeats the line; it is not a Meier source. **Doc 28 §4 cites "Meier, GDC 1989 (revisited 2012)"; downgrade the origin to [U].** | [U] origin |
| 33/33/33 as Jon Shafer's rule | Meier's rule, per Shirk. Firaxis still applies a "rule of thirds" in 2024 (Kerr's paraphrase) | [V] |
| The Nuclear Gandhi bug | A myth. Wikipedia: Meier's 2020 memoir contained "confirmation that the Gandhi software bug was fabricated" ("fabricated" is Wikipedia's word). The legend began with a 2012 TV Tropes edit and spread from 2014. In Civ V, Shafer did set Gandhi's nuke parameters to the maximum, 12, as a joke | [V] |
| "Players expect to win battles at rates far greater than the odds" as Meier's words | Jon-Paul Dyson's summary of the 2010 keynote | [V] |
| A random-seed option in Civ IV | Johnson places the preserved seed and its option in Civ III. Community threads show a Civ III setup option and a Civ IV reload option | [V]; [V-search] |
| "Infinite city sprawl" | Johnson wrote "infinite city sleaze" | [V] |
| "StarCraft II deliberately keeps about a dozen units" | "StarCraft, WarCraft 3, and StarCraft II all average 12 units per faction." | [V] |
| The Zeigarnik effect explains "one more turn" | Madigan argued it in 2013. The 2025 meta-analysis supports resumption, not the memory effect; its "Meier" is Beat Meier | [V]; [V-search] |
| "Any 3:1 battle became a guaranteed win" | Found only in Boris Smus's memoir review; not confirmed in the memoir text | [U] |
| "Our job is to impress you with yourself" | A memoir line as quoted in Brikman's 2026 review; not among the Goodreads highlights | [V-secondary] |
| Civ Battle Royale "ran 301 turns" | Kotaku reports a crash at turn 239; the 301-turn claim comes only from fan-wiki snippets. Fan art, mock newspapers and a stock market are unverified | [V]; [U] |
| "Reviewers" praised BNW for ending late-game tedium | IGN's review, as cited on Wikipedia | [V] |
| "Mixing and matching" policies | Jon Shafer, as quoted on Wikipedia | [V] |
| Shafer's specific wording is snippet-only | This pass fetched the full retrospective on Game Developer (2013-02-18, also on jonshaferondesign.com); earlier drafts had seen only PC Gamer snippets | [V] |

## 4. Mapping to Plotroom

Columns: **Applies to**: P = players of Plotroom-built campaigns, C = creators in the editor, W = Wilco and the harness, M = pack and plugin authors. Every change is **[I]**.

### 4.1 (a) The player experience, especially the strategic layer

| ID | Lesson | Applies to | Concrete change | Target doc |
| --- | --- | --- | --- | --- |
| cv01 | Overlapping tracks, staggered completion (§1.1) | P | The status card and camp terminal show 3–5 counters with different horizons: "Hale back in 2 ops", "Capture research 2/3", "Card B expires after this op", "Offensive 5/8", "Camp in 2–3 ops" (a range while the finisher may still defer the camp, doc 29 §4.3). The generator staggers wound lengths, research lengths and card TTLs so they rarely land together between camps; at a camp or act break they may close together, which is the campaign's natural place to stop (§4.5). SL26 checks the mix | 29 §3.3 step 8, §4.3 |
| cv02 | Always something about to pay off | P | The generator tunes durations so that most ops complete at least one track and advance another (a design-time target that SL26 checks; a lost op may complete nothing). After a camp reward, the next goal is shown at once. The debrief ends with what was settled plus **one** open thread, never five | 29 §3.3; 26 debrief slots |
| cv03 | A visible roadmap (the tech tree) | P | The Unlocks tree is visible to players, not only to creators: each node shows its one rule change, its requirement and "in N ops" when under way. It uses the camp terminal on `Cwr`, or grouped `OBJ_` lines with bucketed variants on `Cwa199`. At least a third of rule-changing nodes sit in the back half (CF26) | 29 §3.2 Unlocks, §4.2 |
| cv04 | Several ways to win, none passive (§2) | P | ≥ 2 ending routes (for example: sabotage the program, expose the order-giver, or hold the bridgehead until relief, where only turns in which the line held count), each with a progress track on the status card. The enemy offensive (K4) sits in the same overview. No route is won by waiting (CF27) | 19 Ending nodes; 26; 29 K4 |
| cv05 | Interesting decisions (§3.1 row 1) | P | The balance lab flags a card, perk, facility or project that is never the best pick in any seeded state, or that is best in almost every state (SL27). Card effects stay disclosed (SL05, doc 34 cw01) | 29 §5.2 |
| cv06 | Predict before committing (§1.3, §3.1 row 4) | P | Cards show risk and reward **bands** from the balance lab plus their factors ("night · no AT in squad · 2 wounded"). Bands are precomputed; factors are computed at commit (doc 29 §3.3 step 8) from committed state and code's recommended squad, so nothing estimates odds in-mission. A "Low" label requires a permanent-loss rate below a placeholder threshold under the Standard policy. No exact odds: OFP is real time | 29 §3.2 CardTemplate, §5.2 |
| cv07 | Felt odds; streaks enrage (§3.1 rows 3–5) | P | `RollSource::StoredLcg` gains bounded **bad-luck protection** for loss-side roll families only (triage, permanent injury): after a bad outcome, the next bad chance shrinks until a good outcome resets it, using one stored counter per family committed with the seed. Reward rolls never get it, because named rewards are deterministic (SL30) and a pity counter on payouts is a loot-box schedule (§4.5). It only ever favours the player, scales with the preset, and is zero on Ironman honour. In the first 3 ops, triage converts a second permanent named loss in consecutive ops into a grave wound. It is documented in the creator inspector, Standing Orders and the preset's player-facing description | 29 §3.2, §3.3 step 3 |
| cv08 | Enemy advantages must be legible (§3.1 row 19) | P | MC31: enemy reinforcements are announced (radio, engine sound, flare, sighting) before contact, and scripts may not give the enemy knowledge of the player without a declared sensor (dog, spotter, intercept). Doom and Pressure always show their reasons | 28 §6.3; 29 §4.3; 31 modules |
| cv09 | Randomness in the situation, not in the payoff (§3.1 row 5) | P | Research, promotions, unlocks and rewards named on a card are deterministic. Rolls vary offers, placement and tactical outcomes (SL30) | 29 §3; 26 |
| cv10 | Snowballs make a mop-up (§2) | P | The balance lab labels "decided" state bundles (SL29). The compiler turns them into ordinary guards, reviewed by the creator, that put a "force the finale" card on the board early. Enemies keep scaling by the clock, not by success (doc 29 rule 2) | 29 §1.5, §5.2; 19 CXL |
| cv11 | Design the back half (§2) | P | After the midpoint, generated campaigns add a new theatre or capability, tighten the clock and build to a real climax. A new island costs a landscape load and a camp copy (`CopyPerIsland`, doc 29 §4.3), shown on the SL14 meter. CF26 flags a flat second half. The length cap stays at 12–25 ops | 26; 29 §1.5 rule 4 |
| cv12 | Resets that erase work feel like theft (§2, Civ VII) | P | New doc 29 rule: an act break may change theatre, rules or the enemy, but never wipes the roster, its history, the memorial or earned unlocks | 29 §1.5 |
| cv13 | Penalties are challenges, not walls (§2) | P | Each penalty module (fatigue, upkeep, Pressure, Stress) needs a visible counterplay and must not scale with the player's success (SL31). Copy states each rule as a countdown the player can act on: wounds read "back in N ops", and doc 29's K5 fatigue (a rest requirement, not a skill penalty) reads "Hale rests 1 op". Where an optional module is a skill modifier with equal maths either way, prefer the bonus framing ("Rested: +skill for soldiers who sat out an op", §3.1 row 22), but the numbers stay visible in Standing Orders and the preset description: framing may never hide a rule | 29 K5, §3.5 |
| cv14 | Scarcity creates interaction (§2) | P | Captures and resources are regional and distinct (one captured BMP, a single fuel cache), scarce enough to force triage, within ≤ 3 currencies (SL03) | 29 Resources, Hangar |
| cv15 | City-states: small actors with short, expiring asks (§1.5) | P | Side cards come from ≤ 2 local factions (villagers, partisans, a defector), each with a standing meter and expiry. The enemy can court the same faction. Each card asks for something the player would not do anyway | 29 K3; 26 story bible |
| cv16 | Permanent identity, some reversible choices | P | Perks and doctrine picks are permanent; loadouts, squad and facility use change at camp. Every doctrine pick keeps ≥ 2 mission approaches viable | 29 Roster, Unlocks |
| cv17 | Early surprises, tied to actions (§1.5) | P | Ops 1–3 include discovery slots (cache, documents, a capturable vehicle; FP13) that pay only for an action, with a cap on random swing | 26; 28 FP13 |
| cv18 | Distinct, readable opponents (§1.6, §2) | P | An enemy commander or faction has a typed personality record (aggressive, cautious, deceptive…). Code maps it to force posture, reaction templates (FP11), radio register and a music pair; seeded jitter stays small enough to keep the identity | 26 story bible; 29 Nemesis |
| cv19 | Close with a replay (§1.6) | P | The finale gets an epilogue node: roll-call, memorial, a map of op sites marked by outcome (pre-placed markers whose type and colour are set at init, doc 29 §2 row 10), and per-op outcome lines. Simple text-bar charts only where the profile has dialogs [U]. Outros cannot read campaign vars (doc 18 §6.1), so the replay is a playable node | 29 K6; 32 |
| cv20 | A difficulty ladder (§3.1 row 9) | P | ≥ 5 named presets of cushion, timers, clock speed and reserves, layered over whichever Cadet or Veteran setting the player chose in the game (doc 28 §1.1: two player-side presets of twelve toggles; a mission can read it with `cadetMode`, which legacy official missions use per `data/cwa199-observed-commands.csv`, and no setter is known [I]). Each lists what it changes; players may change rung between ops in either direction, with no penalty and no shaming label. Names describe what changes, not the player's worth; the default rung is named for being the default ("Standard"), not "Easy". Harder is not more fun per se (doc 28 §4, Caroux & Pujol) | 29 `DifficultyPreset` |
| cv21 | Players optimise the fun out (§3.1 row 16) | P | Add an Exploiter policy to the balance lab (farms the cheapest side op, restarts on loss, hoards). SL28 flags a campaign where exploiting wins mainly through tedium. Payouts decay when an archetype repeats. The stored seed stays the default | 29 §5.2 |
| cv22 | Calm strategy, chaos in the op (§1.4) | P | No strategic decision under fire; picks wait for extraction with the auto-pick fallback (already doc 29 §1.1). Each op briefing restates the strategic stakes in one line, so the two layers read as one game (§3.1 row 12) | 29 §1.1; 26 briefing slots |

### 4.2 (b) The creator experience in the editor

| ID | Lesson | Applies to | Concrete change | Target doc |
| --- | --- | --- | --- | --- |
| cv23 | Civilopedia → Standing Orders (§1.7) | C | F1, right-click "What is this?" and Alt+click open the entry in a docked, non-modal pane **in front**, keeping the dialog open (the Civ V bug opened it behind). Numbers come from the ported rules, never from prose (EUI: "rather than hardcoded blurbs") | 33 §4.1–§4.2 |
| cv24 | Advisors → Wilco and tips (§1.7; Steam threads) | C, W | No definitional first-click pop-ups. Doc 33 §4.8's first-opening tip carries an instance line ("this trigger has no condition yet") or stays silent, and counts against the attention budget. Wilco's explain mode answers "what should I do here, and why?" with a computed fix and a link. The persona stays optional (doc 21 §11.7) | 33 §4.8; 21 §11 |
| cv25 | End-turn button → readiness coach (§1.3) | C, W | One dominant control whose label names the top blocker ("Next: END1 can never fire") and becomes "Preview" when nothing blocks. Blocking means the engine would fail or hide Preview (doc 33 §4.4); everything else is advisory and can be snoozed per mission. "Preview anyway" on advisories is logged in the Preview report. No finding may lack both a fix and a dismiss (a stuck prompt is a bug) | 21 §11.1, §12.4 |
| cv26 | Victory overview → campaign readiness (§1.2) | C | The campaign graph overlays each node's state: validated, previewed, pinned, human-edited, plus "N steps to Preview-ready" per mission and for the campaign | 19 §6; 21 §11.1 |
| cv27 | The expert switch Shafer wanted (§2) | C | Keep the original Easy/Advanced toggle for fidelity (doc 03; doc 05's `[Simple]` dialogs). Add an **expert density** mode (IDs, sqm keys, raw numbers, computed overlays on by default) and doc 19 §6.8's tiers. One registry feeds all of them, so they cannot disagree | 33 §4; 19 §6.8; 05 |
| cv28 | Watching a plan come together (§1.1) | C | Path Explorer witness paths, the chorus line, "predict, then play", and a Preview report that ties outcomes to the creator's own choices ("the dawn start you chose hid the approach"), naming only causes the checker computed, never flattery. The strategic turn journal plays the same role for campaigns | 21 §11.5–§11.6; 26 §8.2; 29 §5.1 |
| cv29 | Find the fun fast; the first 15 minutes (§3.1 rows 6, 11) | C, W | Time-to-first-Preview is the editor's headline usability measure, taken in moderated playtests and never by telemetry (doc 21 §12.1). Describe → generate yields a playable skeleton first, then refines. The first session ends with the user's own mission running (in the spirit of doc 33 §9's AT8 15-minute Drill test) | 25; 33 §9 |
| cv30 | Double it or cut it in half (§3.1 row 10) | C, W | "Harder / Easier" and Wilco's tuning proposals move one knob ×2 or ÷2 on a safe scale (skill band, reinforcement delay) and show a simulator diff before Preview. The balance lab sweeps ×2/÷2, then narrows. Pinned or human-set knobs are constraints, never moved (doc 29 §5.2) | 21; 29 §5.2 |
| cv31 | Never let a decision pass in silence (§3.1 row 2) | C, W | Every Wilco edit appears in the change list with its reason and undo (glass box). Every player pick is read back at extraction and shows in the next briefing (CF04, CF05) | 21 §1.2, §6.5; 29 |
| cv32 | Few weighty decisions, chores automated (§1.4, §3.1 row 17) | C, W | The editor does the chores (sync wiring, names, stringtable keys, `OBJ_` numbering, boilerplate). Wilco never asks what code can compute (doc 21 §4). Weak-model steps are a few weighty Picks with safe defaults | 21 §4; 25 |
| cv33 | The player should have the fun (§3.1 row 13) | C, W | Wilco offers choices, variations and previews, not finished blobs. Creative ideas nobody asked for arrive as Propose ghosts or idea cards (doc 21 §5.1, §7.3); pinned and human-edited content is preserved | 21 §7.3 |

### 4.3 (c) Modding and sharing

| ID | Lesson | Applies to | Concrete change | Target doc |
| --- | --- | --- | --- | --- |
| cv34 | Hooks and docs are part of the product (§2) | M | Every T0 pack kind and plugin hook has a typed schema, a generated reference page from the same registry as Standing Orders, and an example pack. Nobody should have to "assemble a Wiki through experimentation" (PCGamesN's paraphrase of Civ V modders [V]) | 22; 33 §8 |
| cv35 | Creators make identities and maps first | M | Steam Workshop tags (2026-09-27): Civilizations 4,189, Leaders 2,754, Units 2,248, Maps 2,203, but Scenario 738 [V counts; I reading; tags are self-chosen and "Other", 8,124, is the largest]. So T0 pack kinds start small: faction packs (name pools, identities, rank and voice cards, compositions, behaviour templates), site templates per island, radio template packs and overlays. A scenario is a combination of them | 22 §2.1; 26; 34 mo rows |
| cv36 | Modded play must never be second-class (§2) | M, P | Pack-built missions compile to vanilla output that runs with the sidecar deleted (doc 31), so they work wherever an equivalent hand-made mission works (single missions, campaigns and, when the content itself is MP-safe, multiplayer; doc 18 has no MP campaign flow) and carry no "modded" stamp. Game mods (doc 27) show Requires badges and export a mod set (doc 34 mo01) | 22; 27; 31 |
| cv37 | One-click sharing, without a hosted store | M | No hosted Workshop (doc 34 §6 skips it). One-click **export** of a pack, mod set or mission with credits and licence (doc 34 mo10, mo13); import shows the manifest for review; T0 content stays data | 22; 34 §4.4 |
| cv38 | Rule-bending scenarios (G&K's Fall of Rome, Smoky Skies) | C, M | Scenario-level rule overrides become a typed layer: doc 31 modules and doc 29 module presets (for example, a withdrawal campaign where the clock is the player's own retreat). Overrides pass the AI-executability check and are shown in the briefing and in Standing Orders | 31; 29 §3 |
| cv39 | Security differs from Civ V's DLL model | M | Civ V's answer was native DLL source. Ours stays WASM and remote MCP only (doc 22 rejects native plugins). Plotroom is GPL-3.0-or-later, so its source is open anyway; the lesson is hooks and docs, not native access | 22 |

### 4.4 (d) Design-sensibility prompt guidance

The pack carries taste only; nearly every Civ lesson is code-owned (SL/CF/MC checks above). The lenses are at their 220-word cap, so each addition replaces a line, and v0.2 must pass an evaluation round (`prompts/design-sensibility/EVALUATION.md`). Lens text never names a game.

| ID | Lesson | Proposed wording change (v0.2 candidate) | File |
| --- | --- | --- | --- |
| cv40 | Always something about to pay off; a back half that is new | Add to `campaign-arc`: "Does each mission pay something off while another thread is still on its way?" and "Does the second half bring something new, not more of the same?" | lenses/campaign-arc.md |
| cv41 | Interesting decisions | Sharpen `branching-and-consequence`'s "Does every option have a sound reason to pick it?" to "Would a good commander pick each option in some situation? Name that situation in the why." | lenses/branching-and-consequence.md |
| cv42 | Natural stopping point; readback | Add to `briefing` (which also serves debriefs): "Does the debrief say what was settled, name the pick the player made, and leave one thing open (nothing after the finale)?" | lenses/briefing.md |
| — | Telegraphed danger; moral clarity at the top, humanity in the ranks | No change: `core.md` already says "a sign comes first" and "Blame sits with the few who give orders", which matches Meier's scoped moral-clarity advice (§3.1 row 8) | core.md |
| — | Rubric anchors | R3 at 5 adds "every offered option is the best pick in some situation". R9 at 5 adds "each op ends at a natural stopping point". New calibration note: "a timer or countdown that carries no decision scores R9 ≤ 3". The rubric never scores session length or return rate | rubric.md |

### 4.5 (e) Ethics: healthy engagement, no dark patterns, respect for creators' time

Draw the line by effects (regret, consent, transparency), not by a blacklist. Zagal, Björk & Lewis (FDG 2013) define a dark pattern as one "used intentionally by a game creator to cause negative experiences for players which are against their best interests and likely to happen without their consent" [V]. Deterding, Stenros & Montola (DiGRA 2020) call the concept "ontologically incoherent" but keep transparency and regret as "fruitful analytic or empirical starting points" [V]. The checklist is code-owned **[I]**:

- **cv43 — Players.** (1) Clocks count deployments, never real time, and nothing decays while the game is closed (doc 29). (2) No streaks, dailies, login rewards or appointment mechanics in anything Plotroom's modules, presets, generators, Wilco or Standing Orders produce (doc 33 already bans streaks). A creator's own hand-written scripts stay the creator's call; a lint may inform, never block. (3) No grind: payouts decay when an archetype repeats (doc 29 rule 4, SL28). (4) No reroll or gacha loops for recruits or loot; candidates are shown before commitment. (5) Harsh modules are opt-in presets (doc 29 rule 11). (6) No illusory progress ("endowed progress", Kivetz et al.) used to lure play. (7) Every op ends at a natural stopping point: closure plus one open thread, with no "come back" nag. (8) Hidden help (cv07) is disclosed in Standing Orders, the creator inspector and the preset description the player reads. (9) No variable-ratio reward schedules: rolls vary situations, named rewards are deterministic (SL30), random bonuses (discovery slots, cv17) are capped and tied to an action, and bad-luck protection only softens losses (cv07). (10) Staggered tracks (cv01) stop at camps, act breaks and the finale, where threads may close together. (Answered 2026-09-27 → [D039](../decisions/D039-engagement-ethics.md): cv43 is a product rule for Plotroom's own output, and a challenge catalogue is allowed with no calendar, week index, streak, reward or reminder.)
- **cv44 — Creators and evaluation.** (1) No telemetry; doc 21 §12.1 forbids uploads. (2) Playtests ask "Was that time well spent?" and "Energised or drained afterwards?"; no metric scores session length or return rate (doc 28 §7). (3) Respect creators' time: tip budget and mastery suppression (doc 33 §4.8), no nagging, undo for everything, and Wilco asks only what code cannot compute. (4) No lock-in: output runs without Plotroom (doc 31). (5) The creator's fun is making missions; the editor adds no meta-rewards beyond achievements that describe competence (doc 33 principle 6), and those have an off switch (doc 33 verification notes; doc 34 le14).

### 4.6 Provisional lint codes

| Code | Level | Check | Rows |
| --- | --- | --- | --- |
| SL26 | warn | Horizon mix: at some simulated extraction between camps, no visible track completes within 2 ops, or ≥ 3 tracks complete on the same op turn in ≥ 2 turns of a run (bunching). Camp visits, act breaks and the finale are exempt, so closures may align there (§4.5) | cv01 |
| SL27 | warn | A card template, perk, facility or project is never the best pick in any seeded state of the balance lab (dominated), or the same option is best in ≥ 90 % of states (not situational); extends MC13, SL07, SL08 | cv05 |
| SL28 | warn | The Exploiter policy's win rate beats the Standard policy's by more than a placeholder margin while playing ≥ 25 % more ops | cv21 |
| SL29 | info | Decided state: from some turn with ≥ 3 ops left, ≥ 95 % of runs from that state reach the same ending and no remaining card changes it | cv10 |
| SL30 | error | A named reward, unlock, research completion or promotion depends on a roll | cv09 |
| SL31 | warn | A penalty module has no visible counterplay (card, facility, action or rotation), or its size scales with the player's success | cv13 |
| CF26 | warn | The second half of a path adds no new archetype, seat, decision type, unlock tier or theatre, or holds under a third of the rule-changing unlocks | cv03, cv11 |
| CF27 | warn | An ending route has no visible progress track, or is reachable by waiting alone | cv04 |
| MC30 | info | Static analysis (or the simulator, where it models the mission) finds a win reachable with no player movement or action, for example an END trigger on a timer alone with no reachable loss condition (a timed defence the player can lose is fine) | cv04 |
| MC31 | warn | An enemy reinforcement or spawn has no earlier announce cue, or a script grants the enemy knowledge of the player without a declared sensor; extends MC08. Which commands grant knowledge comes from doc 24's audit [U] | cv08 |
| TX07 | info | A generated line claims a consequence ("the villagers will remember") that no typed effect or guard implements (text-mechanic dissonance; §3.1 row 20) | cv31 |

## 5. Recommendations per target doc

**Doc 19 (campaign model and UX)**
- Keep the Classic tier (§6.8) complete and the default for imported campaigns: it is the expected third (cv27).
- Let Ending nodes declare an optional progress track (a declared `Int` with a visible surface) and add CF27 (cv04).
- Add a readiness overlay to the Flow view (cv26) and a Path Explorer query "states from which the ending is decided" (cv10). A decided-state guard is an ordinary CXL guard produced by the balance lab and shown for review; the language gains nothing.

**Doc 21 (agent doctrine)**
- §11.1: make the readiness coach the single dominant control, with blocking and advisory findings apart, snooze and an audited "Preview anyway" (cv25). Add to §12.4: "no finding lacks both a fix and a dismiss".
- §11.7 and explain mode: situational answers only, never definitions on first click (cv24).
- Tuning proposals move a knob ×2/÷2 with a simulator diff (cv30). Every "why" shown to a user (why a trigger fired, why the enemy acted) is computed; the model may only phrase it (cv18, cv31).

**Docs 22 and 27 (plugins, addons and mods), with doc 34's mo rows**
- Start the T0 catalogue with identity blocks: faction packs, site templates, radio packs and overlays (cv35).
- Generate hook and pack-kind references from the registry, each with an example pack (cv34).
- State the invariant that pack-built output is vanilla and never second-class, in multiplayer or campaigns (cv36). Sharing is export and import with review (cv37); rule-override scenarios are T0 data, not code (cv38).

**Doc 25 (weak-model harness)**
- Horizon-mix and interesting-decision checks run as code gates after S3/S4, never as prompt instructions (cv01, cv05).
- Order stages so that a playable skeleton exists early (cv29), and ask few, weighty Picks with safe defaults (cv32).
- "Make a follow-up campaign" defaults to the rule of 33s: keep the roster and theatre, fix the playtest pain points, add one new kernel or module (§3.1 row 15).

**Doc 26 (campaign content)**
- Every archetype supports ≥ 2 approaches, none of them passive (MC30, cv04). Add an "ending routes" pattern candidate; its number waits for the design round, because P10 already collides (doc 34).
- Add a typed faction personality record to the story bible (cv18) and ≤ 2 local factions with standing and expiring asks (cv15).
- Add the back-half escalation rule and CF26 (cv11), discovery slots tied to actions (cv17), and a library of off-screen war cues (radio, distant artillery, smoke) that sells scale without spawning fights (§3.1 row 7).

**Doc 28 and the design-sensibility pack**
- Fix §4's "Meier, GDC 1989 (revisited 2012)" row: the origin is [U] (§3.2).
- Add research rows: Johnson's two levels, "optimize the fun out", fun per time and "theme is not meaning"; Pardo's framing; the turn-based calm; Ovsiankina over Zeigarnik; the goal gradient; Przybylski 2009; Zagal 2013 and Deterding 2020.
- Add MC30, MC31 and TX07 to §6.3 as provisional. Queue cv40–cv42 and the rubric notes for pack v0.2, and evaluate before adoption (§4.4).

**Doc 29 (strategic layer)**
- New rules in §1.5: act breaks never wipe what was earned (cv12); every penalty has counterplay (cv13); randomness lives in situations, not payoffs (cv09).
- Status card: 3–5 horizons, each "in N ops" (cv01–cv03), and ending-route tracks beside the offensive (cv04).
- `CardTemplate`: risk and reward bands with factors (cv06). `RollSource`: bounded bad-luck protection by preset, for loss-side rolls only (cv07). `DifficultyPreset`: ≥ 5 honest rungs over the player's own Cadet/Veteran setting (cv20); its `Veteran` variant name collides with OFP's Veteran mode and should be renamed (decided 2026-09-27 → [D034](../decisions/D034-descriptor-placement-and-names-delegation.md); the new name comes from the names table).
- Balance lab: the Exploiter policy, ×2/÷2 sweeps, dominance and decided-state detection, and SL26–SL31 (cv05, cv10, cv21, cv30).
- K3 from local factions (cv15); K5 copy framed as "Rested" (cv13); a finale epilogue replay (cv19); the engagement-ethics checklist as a new subsection (cv43).

**Doc 31 (no-code ladder)**
- Scenario rule overrides as typed module presets (cv38). Tag each module with an AI-executability note (for example, convoy modules run MC14's route check).
- The reinforcements module emits an announce cue by default (MC31).

**Doc 32 (cinematics)**
- Music cue pairs (calm and tense) per faction or antagonist, chosen from stock tracks and keyed to mission state, following Curran's "recognizable" theme across peace and war (§1.6). Custom audio needs licensable assets, because the repository is public.
- The finale epilogue scene (cv19).

**Doc 33 (Standing Orders and Drill)**
- Manual pages open in front in a non-modal pane (cv23).
- First-opening tips speak about the instance or stay silent (cv24); run a usability check against the Civ V advisor evidence.
- Ship expert density in v1 (cv27). Add entries for Plotroom's own campaign rules (bad-luck protection, triage, decided-state finale), so the hidden help is not hidden from anyone who looks (cv43).

## Open questions

1. **Bad-luck protection strength.** How strong can it be before permadeath stops meaning anything, and which roll families get it? It needs the balance lab and playtests (cv07).
2. **Opt-in rerolls on restart.** Civ III let players choose. On vanilla, stored rolls revert with the book row, so an opt-in would need engine `random` mixed into the seed only for players who opt in. Does SL11 allow a documented exception? [U] (Answered 2026-09-27 → [D040](../decisions/D040-play-seeds-and-memory.md): no re-roll exception in v1. SL11's wording for the play-seed bootstrap draw is [DG038](../design-gap-requests/DG038-sl11-engine-random-exceptions.md), still open.)
3. **What counts as "decided"?** Should the early finale be offered as a card or taken automatically (cv10)?
4. **How many visible counters are too many?** "3–5" is a guess; SL03 caps cards and currencies but not counters (cv01).
5. **Difficulty rungs.** How many, what names, and how does each read alongside the Cadet or Veteran setting the player already chose, which a mission can read but not set (cv20)? (Who names them answered 2026-09-27 → [D034](../decisions/D034-descriptor-placement-and-names-delegation.md): the design round names the rungs in one names table, reviewed by the owner, and renames `DifficultyPreset::Veteran`. The number of rungs and the names themselves stay open.)
6. **Status surfaces on 1.99.** Do the horizon counters fit `hint format` and bucketed `OBJ_` lines within the §9 probes (PR series)?
7. **First-opening tips.** Keep them with instance lines, or remove them (cv24)? Needs a small usability test.
8. **Knowledge-granting commands.** Which engine commands give the AI knowledge of the player, for MC31? Needs doc 24's audit [U].
9. **Faction personality.** How many knobs, and can a weak model hold a radio register per personality within TX05's limits (cv18)?
10. **Civ facts still [V-search] or [U].** Advisor behaviour, city-state quest numbers (fandom returned 402), combat-preview thresholds (Steam guide returned 429), the GameSpot and PC Gamer quotes, and the Workshop-side MP mod workarounds. Settle them before citing them anywhere load-bearing.

## Sources

**Designers and developers**
- Jon Shafer, "Revisiting the Design of Civ 5", Game Developer, 2013-02-18 (also jonshaferondesign.com; first posted as At the Gates Kickstarter "Update 5"): <https://www.gamedeveloper.com/design/revisiting-the-design-of-civ-5> [fetched]; <https://jonshaferondesign.com/2013/02/18/revisiting-the-design-of-civ-5/> [search]; <https://www.kickstarter.com/projects/jonshafer/jon-shafers-at-the-gates/posts/404789> [title via search]
- Shafer, "Building Civilization V", Game Developer, 2010-08-11: <https://www.gamedeveloper.com/audio/building-i-civilization-v-i-> [fetched]
- Dennis Shirk, interviewed by Chris Remo, Game Developer, 2010-06-11: <https://www.gamedeveloper.com/business/historical-outlook-a-i-civilization-v-i-interview>; news item: <https://www.gamedeveloper.com/game-platforms/shirk-sid-meier-s-rule-of-33s-reigns-for-i-civilization-v-i-> [fetched]
- Ed Beach and Dennis Shirk, Shacknews (Steve Watts), 2013-03-29: <https://www.shacknews.com/article/78473/civilization-5-devs-on-forging-a-brave-new-world> [fetched]
- Ed Beach, PCGamesN (Rob Zacny), 2013-07-28: <https://www.pcgamesn.com/making-civilization-v-brave-new-world> [fetched]
- Ed Beach on Shafer, Quarter to Three (Nick Diamon), 2013-04-13: <https://www.quartertothree.com/fp/2013/04/13/brave-new-world-lead-disputes-jon-shafers-self-criticism/> [fetched]
- SpaceSector (Adam Solo) on Shafer's retrospective, 2013-02-14: <https://www.spacesector.com/blog/2013/02/jon-shafers-civ5-lessons-learned-mea-culpa-at-the-gates/> [fetched]; PC Gamer on the same: <https://www.pcgamer.com/jon-shafer-criticizes-every-decision-he-made-in-designing-civ-v-explains-how-at-the-gates-will-differ/> [snippets only]
- Ed Beach on completion rates, Game Developer (Chris Kerr), 2024-08-23: <https://www.gamedeveloper.com/design/firaxis-big-swing-with-civilization-vii-convincing-players-to-actually-finish-their-games> [fetched]
- Civ VII Dev Diary #5: Combat, 2024-12-18: <https://civilization.2k.com/civ-vii/archive/dev-diary/combat/> [fetched]
- Michael Curran, VGMO interview (undated, c. late 2010): <https://vgmonline.net/curranknorrinterview/> [fetched]
- Meier, GDC 2012 "Interesting Decisions", reported by Leigh Alexander, 2012-03-07: <https://www.gamedeveloper.com/design/gdc-2012-sid-meier-on-how-to-see-games-as-sets-of-interesting-decisions> [fetched]; session page: <https://gdcvault.com/play/1015756/Interesting> [fetched]
- Meier, GDC 2010 keynote "The Psychology of Game Design (Everything You Know Is Wrong)", as reported by: Kris Graft, <https://www.gamedeveloper.com/game-platforms/gdc-sid-meier-s-lessons-on-gamer-psychology>; Greg Tito, <https://www.escapistmagazine.com/liveblog-sid-meiers-gdc-2010-keynote-speech/>; Douglass C. Perry, <https://venturebeat.com/technology/quotes-from-sid-meiers-keynote-gdc-speech>; John Teti and David Wolinsky, <https://www.avclub.com/avc-at-gdc-10-day-four-spy-party-1798219468>; Michael McWhertor, <https://kotaku.com/civilization-creator-explains-why-everything-game-devs-5492078>; Mike Schramm, <https://www.engadget.com/2010-03-14-sid-meier-talks-player-psychology-and-the-year-of-civilization.html>; Brian Leahy (with Rob Pardo), <https://www.shacknews.com/article/62807/sid-meier-and-rob-pardo>; Jon-Paul Dyson, <https://www.museumofplay.org/blog/gdc-2010-game-psychology-101/> (all fetched, 2010-03-12 to 2010-03-31); Ada Chen Rekhi's attendee notes, <https://www.adachen.com/gdc10-notes-sid-meier-on-why-everything-you-know-is-wrong/> [U]
- Sid Meier with Jennifer Lee Noonan, *Sid Meier's Memoir!* (W. W. Norton, 2020): excerpt, <https://www.pcgamesn.com/sid-meiers-memoir-civilization> [fetched]; AltChar (Robert Edwards, 2020-10-13), <https://www.altchar.com/game-news/six-things-we-learned-from-sid-meiers-memoir-a7HB62n8SREW> [fetched]; Brikman review (2026-06-18), <https://www.ybrikman.com/blog/2026/06/18/sid-meier-memoir/> [fetched]; Smus review (Jan 2021), <https://smus.com/books/sid-meiers-memoir/> [fetched; secondary]; Goodreads highlights, <https://www.goodreads.com/author/quotes/5660350.Sid_Meier> [fetched]
- Troy Goodfellow on the "interesting decisions" quote, 2008-07-07: <https://flashofsteel.com/index.php/2008/07/07/quote-misquote-cite/> [fetched]; Darenn Keller community blog, 2021-10-14: <https://www.gamedeveloper.com/game-platforms/just-one-more-turn---game-development-tips-and-tricks-from-the-creator-of-civilization-sid-meier-> [fetched]
- Soren Johnson: "Sid's Rules" (2009), <http://www.designer-notes.com/game-developer-column-5-sids-rules/>; "Water Finds a Crack" (2011), <https://www.designer-notes.com/game-developer-column-17-water-finds-a-crack/>; "Our Cheatin' Hearts" (2009-09-14), <https://www.gamedeveloper.com/game-platforms/analysis-game-ai-our-cheatin-hearts>; "Turn-Based Versus Real-Time" (2009-11-06), <https://www.gamedeveloper.com/game-platforms/analysis-turn-based-versus-real-time>; "When choice is bad" (2013-07-29), <https://www.gamedeveloper.com/design/when-choice-is-bad-finding-the-sweet-spot-for-player-agency>; "Seven Deadly Sins" (2013-07-16, from 2008), <https://www.gamedeveloper.com/business/seven-deadly-sins-of-strategy-game-design>; "Theme is Not Meaning", <https://gdcvault.com/play/1012750/Theme-is-Not> and <http://www.designer-notes.com/theme-is-not-meaning-gdc-2010/> (all fetched)
- Jake Solomon on XCOM 2 randomness, 2016-03-01: <https://www.gamedeveloper.com/design/jake-solomon-explains-the-careful-use-of-randomness-in-i-xcom-2-i-> [fetched; already in doc 29]

**Reviews, critics and press**
- Sullla, BNW review (Oct 2014): <https://sullla.com/Civ5/bnwreview.html> [fetched]
- SpaceSector (Adam Solo), 2010-12-28: <https://www.spacesector.com/blog/2010/12/sid-meiers-civilization-5-review/> [fetched]
- GameSpot (Kevin VanOrd): <https://www.gamespot.com/reviews/sid-meiers-civilization-v-review/1900-6276683/> [snippet; 403]; PC Gamer: <https://www.pcgamer.com/civilisation-v-review/> [snippet]
- Wikipedia: <https://en.wikipedia.org/wiki/Civilization_V>, <https://en.wikipedia.org/wiki/Civilization_V:_Gods_%26_Kings>, <https://en.wikipedia.org/wiki/Civilization_V:_Brave_New_World>, <https://en.wikipedia.org/wiki/Nuclear_Gandhi>, <https://en.wikipedia.org/wiki/Jon_Shafer> [fetched]
- GamesBeat (2016-02-18): <https://gamesbeat.com/civilization-25-years-66-versions-33m-copies-sold-1-billion-hours-played/> [fetched]
- Kotaku on Civ Battle Royale (2015-03-19): <https://kotaku.com/giant-42-player-civilization-game-breaks-down-may-neve-1692488675> [fetched]; fan wiki: <https://civbattleroyale.fandom.com/wiki/Civ_Battle_Royale_Wikia> [snippet; 402]
- Pixelkin (2025-05-27): <https://pixelkin.org/2025/05/27/civ-7-has-a-serious-problem-as-steam-reviews-dip-to-mostly-negative/> [fetched]; games.gg (2026-06-06): <https://games.gg/news/civ-7-test-of-time-update/> [fetched]
- Aftermath Hours (2025-02-14): <https://aftermath.site/podcasts/aftermath-hours-podcast-civilization-vii-one-more-turn/> [fetched]
- PCGamesN on Civ modders (Richard Scott-Jones, updated 2016-11-29): <https://www.pcgamesn.com/civilization-vi/civilization-vi-best-modders-civ-6-toolkit> [fetched]
- Gamepressure on G&K scenarios: <https://www.gamepressure.com/civ5gk/scenarios/z43c95> [snippet]

**Community and forums**
- CivFanatics: next-turn button (2010-10-03) <https://forums.civfanatics.com/threads/the-next-turn-button-requires-change.387367/>; Civilopedia bug (2010-11-13) <https://forums.civfanatics.com/threads/fixed-right-click-tech-tree-does-not-bring-civilopedia-to-front.398106/>; victory overview (2016-10-15) <https://forums.civfanatics.com/threads/how-can-i-tell-who-is-closest-to-victory.599743/>; victory screen <https://forums.civfanatics.com/threads/how-to-find-your-score-after-the-victory.565693/>; Shafer mirror (2013-02-24) <https://forums.civfanatics.com/threads/jon-shafers-critique-of-civilization-5-my-thoughts.489360/>; EUI <https://forums.civfanatics.com/resources/civ5-enhanced-user-interface.24303/>; SDK (2010-09-28) <https://forums.civfanatics.com/threads/civ5-sdk-available-on-steam.385002/>; DLL source (2012-09-27) <https://forums.civfanatics.com/threads/civilization-v-dll-source-code-coming-with-fall-patch.476593/>; difficulty levels <https://civfanatics.com/civ5/info/difficulties/> (all fetched)
- Snippet only: <https://forums.civfanatics.com/threads/cant-clear-select-city-production-prompt.513828/>; <https://forums.civfanatics.com/threads/creating-ui-mods-with-lua-xml.399743/>; <https://forums.civfanatics.com/threads/mppatch-easy-modded-multiplayer.617806/>; <https://forums.civfanatics.com/threads/preserve-random-seed.136942/>; <https://forums.civfanatics.com/threads/new-random-seed-on-reload.287078/>; <https://steamcommunity.com/sharedfiles/filedetails/?id=749815003> (429); <https://civilization.fandom.com/wiki/City-state_(Civ5)> and <https://civilization.fandom.com/wiki/Advisor_(Civ5)> (402)
- Steam: advisors (2015-08-03) <https://steamcommunity.com/app/8930/discussions/0/541907867760291672/>; F1 and advisors (2018-03-15) <https://steamcommunity.com/app/8930/discussions/0/1698293703772771163/>; Workshop tag counts (2026-09-27) <https://steamcommunity.com/app/8930/workshop/> (all fetched)

**Research on motivation and ethics**
- Madigan, "The Zeigarnik Effect and Quest Logs", 2013-03-06: <https://www.psychologyofgames.com/2013/03/the-zeigarnik-effect-and-quest-logs/> [fetched]
- Ghibellini & Meier (2025), "Interruption, recall and resumption: a meta-analysis of the Zeigarnik and Ovsiankina effects", *Humanities and Social Sciences Communications* 12: <https://www.nature.com/articles/s41599-025-05000-w> [snippets; login redirect]
- Kivetz, Urminsky & Zheng (2006), *Journal of Marketing Research* 43(1):39–58: <https://journals.sagepub.com/doi/abs/10.1509/jmkr.43.1.39> [snippets; 403]
- Przybylski, Weinstein, Ryan & Rigby (2009), *CyberPsychology & Behavior* 12(5):485–492: <https://journals.sagepub.com/doi/abs/10.1089/cpb.2009.0083> [abstract via search; 403]
- Vuorre, Johannes, Magnusson & Przybylski (2022), *Royal Society Open Science* 9(7):220411, via the OII release (2022-07-27): <https://www.oii.ox.ac.uk/news-events/major-new-study-finds-little-evidence-for-causal-connection-between-well-being-and-video-game-playing/> [fetched]
- Zagal, Björk & Lewis (2013), "Dark Patterns in the Design of Games", FDG 2013, pp. 39–46: <http://www.fdg2013.org/program/papers/paper06_zagal_etal.pdf> (content confirmed via Deterding et al.)
- Deterding, Stenros & Montola (2020), "Against 'Dark Game Design Patterns'", DiGRA 2020: <https://eprints.whiterose.ac.uk/156460/> [PDF read in full]

**Repository documents (mapping targets)**
- `docs/research/19-…`, `21-agent-doctrine.md`, `22-plugin-system.md`, `25-…`, `26-…`, `27-addons-and-mods.md`, `28-what-makes-it-fun.md`, `29-north-star-xcom-like-strategic-layer.md`, `31-…`, `32-cinematics-and-camera.md`, `33-standing-orders-and-drill.md`, `34-iron-curtain-second-pass.md`; `prompts/design-sensibility/` (`core.md`, `rubric.md`, `lenses/`). Section references were read on 2026-09-27; this doc changes none of them.

## Verification notes

### Product-fit and ethics review (2026-09-27)

**Scope.** Every mapping row (cv01–cv44), the provisional lints (§4.6) and the per-doc recommendations (§5) were checked against the engine constraints recorded in doc 29 (§1.1 strategic turn, §2 feasibility matrix, §3.2–§3.3 types and commit pipeline, §4.3 status surfaces, §5.2 balance lab), doc 28 §1.1 (difficulty), doc 19 §6.8 (tiers), doc 21 §11–§12, doc 22 (plugin tiers), doc 31 (sidecar-free output), doc 33 §2, §4 and §9, and the design-sensibility pack (`core.md`, `rubric.md`, `README.md`, lenses). Three questions: is each change feasible on the engine and inside the AGENTS.md invariants; does any recommendation add a dark pattern for players or creators; are quotes tagged with the right status.

**Feasibility and invariant fixes made in place.**

- cv01: "Camp in 2 ops" became a range, because the finisher may defer a camp that offers no decision (doc 29 §4.3).
- cv02: "The finisher guarantees" a completion each op was not something a finisher can promise (a lost op may complete nothing); it is now a generator tuning target checked by SL26.
- cv04: the "hold until relief" example contradicted CF27 ("reachable by waiting alone"); relief now counts only turns in which the line held.
- cv06: stated where bands and factors are computed (precomputed bands; factors at commit step 8 from committed state and the recommended squad), since there is no in-mission odds engine.
- cv11: a new theatre costs a landscape load and a camp copy (doc 29 §4.3, SL14).
- cv13: the row described K5 as a "Tired: −skill" penalty; doc 29's fatigue is a rest requirement. Rewritten, and the Pardo-style framing is limited to optional skill modifiers whose numbers stay visible.
- cv19: "graphs" in dialogs became text-bar charts marked [U]; the outcome map uses markers whose type and colour are set at init (doc 29 §2 row 10).
- cv20: a campaign cannot set OFP's Cadet or Veteran mode; that is a player-side setting (doc 28 §1.1) the mission can only read (`cadetMode`; no setter known [I]). The presets now layer over it. §5 also notes that doc 29's `DifficultyPreset::Veteran` name collides with the engine's Veteran mode.
- cv21: SL28 is a warn-level lint, so "fails" became "flags".
- cv29: the headline measure is taken in moderated playtests, never through telemetry (doc 21 §12.1). The doc 33 reference now names AT8, which is a Drill test, not a first-session test.
- cv30: pinned and human-set knobs are constraints the ×2/÷2 sweep never moves (doc 29 §5.2; AGENTS.md "partial regeneration never clobbers human work").
- cv36: the multiplayer claim is scoped. Vanilla output works wherever an equivalent hand-made mission works; strategic campaigns are single-player (doc 18 has no MP campaign flow).
- MC30: "the simulator" became static analysis first, and timed defences the player can lose are excluded, so the lint does not flag ordinary hold-out missions.

**Dark-pattern fixes made in place.**

- **Engineered pull without a stopping point (TL;DR, cv01, SL26).** §1.1 names the cost: staggered completions remove natural stopping points. As first written, SL26 enforced staggering everywhere. Camps, act breaks and the finale are now exempt, so threads can close together there, and cv43 item 10 records the rule. Together with cv02's "one open thread", no real-time decay and no "come back" nag, this keeps the "one more op" pull in the healthy column.
- **A pity timer on rewards (cv07).** Bad-luck protection on "side-op payout" is the loot-box pattern: a variable-ratio reward with a pity counter. It also contradicted cv09 and SL30 (named rewards are deterministic). It is now limited to loss-side rolls (triage, permanent injury). cv43 item 9 bans variable-ratio reward schedules, and the hidden help is also disclosed in the player-facing preset description, not only in creator tools.
- **One-way difficulty (cv20).** "Players may step up" suggested that stepping down was barred. Rungs now change in either direction without penalty or shaming labels. Names describe what changes and do not flatter the player.
- **Scope of the no-streak rule (cv43 item 2).** It now binds what Plotroom's modules, generators, Wilco and Standing Orders produce, and it leaves a creator's own scripts to the creator: lints inform, never block.
- **Creators.** Preview-report attributions name computed causes only, never flattery (cv28). Achievements get an off switch (cv44 item 5). The first-session measure uses no telemetry (cv29). The debrief lens leaves no open thread after the finale (cv42).
- **No other dark pattern found.** No row adds dailies, appointment play, real-time decay, grind loops, rerolls or gacha, premium currency, social obligation, or nags. Card expiry and the doom clock count deployments, not wall time (doc 29 K0). The early-finale card (cv10) and payout decay on repeated side ops (cv21) work against grind.

**Quote and status checks.** Five sources were re-fetched on 2026-09-27 through a summarising fetch tool, so exact punctuation rests on that tool's extract:

- Aftermath Hours (2025-02-14): the two Plunkett lines appear in the episode text. [V]
- Johnson's "Our Cheatin' Hearts": it supports "hidden help may only favour the player" (fortunate drops "only happen for the human and never for the AI") and both quoted lines in §3.1 row 19. [V]
- PCGamesN: "assemble a Wiki through experimentation" is the journalist's paraphrase about Civ V's tools, now tagged; the Sukritact and Tomatekh quotes are the modders' own words. [V]
- Shafer's retrospective: "rhyme and reason" is confirmed, and so is the "'expert' switch" he wanted, now quoted in §2 and the TL;DR. [V]
- games.gg: the Test of Time update (May 19) made *civ-switching at age transitions* optional. The TL;DR had said "forced resets … were made optional", which overstated the change; it is fixed and tagged [V as reported]. The Zelnick quote starts lowercase, mid-sentence, and is now reproduced that way.

Every other status tag was left as the adversarial pass set it.

**Residual concerns (not fixed here).**

1. The pull stays deliberately engineered. Whether camps really work as stopping points is a playtest question: ask "Was that time well spent?" and "Energised or drained?" (cv44). The Ovsiankina evidence is [V-search] only.
2. Bad-luck protection and the early-ops loss rule are hidden help that can dilute permadeath (open question 1), and the disclosure works only if players read the preset description.
3. Auto-applying the early finale (open question 3) would take agency away; this review assumes it stays an offered card.
4. Five or more difficulty rungs, local factions with standing meters (cv15), a new "doctrine" concept (cv16, absent from doc 29's module kit) and 3–5 counters all add overhead against doc 29 rule 5. SL03 caps none of them.
5. cv06 factors computed for the recommended squad can go stale if the player overrides the squad at extraction. Either the hint recomputes them or it labels them "for the recommended squad".
6. MC31 depends on doc 24's audit of knowledge-granting commands [U]. The cv19 dialog charts and all 1.99 dialog surfaces depend on probes PR06–PR07.
7. The question line calls Civ V "addictive" in the colloquial sense. This doc makes no clinical claim, and Vuorre et al. (2022) found little causal evidence between play and well-being.
8. The proposed R9 anchor ("a timer or countdown that carries no decision scores R9 ≤ 3") may fit R4 better. Settle it in the pack v0.2 evaluation round.
9. The doc 29 `DifficultyPreset::Veteran` rename and the SL26 exemption belong in docs 29 and 25 when the design round adopts these codes. This review edited only this file.

### Consolidation pass (2026-09-27)

- RN-12 (owner rename decision): our concept manual, formerly "Field Manual", is now **Standing Orders**, and our live tutorials, formerly "boot camp", are now **Drill**. Renamed in the companions line (doc 33 is now "Standing Orders and Drill: the concept manual and live tutorials"), cv07, cv13, cv23 ("Civilopedia → Standing Orders"), cv34, cv38, cv43 items 2 and 8, the §5 heading for doc 33, and the product-fit note on cv43 item 2. "Boot-camp test" became "Drill test" in cv29 and in the product-fit note on cv29; AT8 is confirmed as the Drill-track (formerly "Boot camp A+B") headline test in doc 33 §9. The repository-documents link now points to `33-standing-orders-and-drill.md`; a later step of this pass renames doc 33's file, so the link resolves only after that step. No finding, code or row meaning changed; this doc never names Arma 3's own Field Manual or `skills/field-manual`, so nothing needed keeping or relinking there.
- Rename step done (2026-09-27; supersedes "resolves only after that step" above): doc 33's file was moved with `git mv` to `docs/research/33-standing-orders-and-drill.md`, so the repository-documents link now resolves.

### Owner answers (2026-09-27)

- **2026-09-27, folded by pointer:** cv43 points to [D039](../decisions/D039-engagement-ethics.md) (OWQ-20); open question 2 points to [D040](../decisions/D040-play-seeds-and-memory.md) (OWQ-21) and to DG038, which D040 does not decide; open question 5 and the §5 doc 29 `Veteran` rename point to [D034](../decisions/D034-descriptor-placement-and-names-delegation.md) (OWQ-08, naming delegated to the design round). Open question 1 (bad-luck protection strength) stays open, as D039 and D042 list it. No row, lint or recommendation changed.
