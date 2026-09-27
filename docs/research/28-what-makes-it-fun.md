# What makes it fun: the OFP formula and the craft of fun

Research doc 28 for `ofp-editor`. Audience: contributors and LLM coding agents reading only this file.
Question answered: what made the Operation Flashpoint / Cold War Assault campaigns and missions lovable, what the OFP mission
community learned about craft, what research says about fun, and how all of it becomes **generators, lints, prompt guidance
and UX** in the describe → generate → refine harness (docs 25 and 26), including the embedded design-sensibility prompt.

**Epistemic legend.** **[V]** verified against a fetched source (cited). **[I]** inferred or proposed by us. **[U]** unknown or
resting only on a search snippet; needs a fetch, a probe or a playtest. Repository docs are cited as "doc NN §x".
**Rules for this file.** Quotes are short and attributed to one named source. Mission titles appear only to cite structure;
Bohemia character names, mission titles and mission text never go into prompts, exemplars or generated content (§6.4).
One 2018 personal retrospective (Kai Wüest) supplies many reception quotes; it is always named, never generalised to "reviewers".

## TL;DR

- **The OFP formula** is a small soldier in a big, living war: goals without prescribed methods, one-bullet lethality, an enemy
  that reacts, radio that sells scale, a campaign that starts low and widens its lens, a survived defeat as the pivot, and
  quiet missions between the hard ones [V/I] (§1).
- **What people loved** was freedom of approach, combined arms, tension at long range and the editor itself. **What they hated**
  was losing 30 minutes to one unseen shot, triggers that never fire, empty walks and AI drivers [V] (§2).
- **The community's craft** converged on four separators between good and bad missions: it reliably ends, the enemy reacts, the
  briefing answers what/why/how, and presentation is short and emotional [I from ~16 OFPEC reviews] (§3).
- **Research on fun** that holds up: need satisfaction (competence, autonomy, relatedness), flow's clear goals and feedback,
  failure the player can own, peak-end memory. Pacing waves, interesting decisions and curation are strong practitioner wisdom
  (the "series of interesting decisions" line has an unverified origin [U]). Player types and "N kinds of fun" are vocabulary,
  not science [V]. Healthy pull is judged by need satisfaction, regret and consent, never by time played (§4, rows from doc 36).
- **LLM defaults are nearly the inverse of the OFP register**: positive, tidy, explanatory, ornate, verbose, generic, and
  homogeneous across runs [V]. A prompt alone cannot fix that, least of all on 3–9B models [I] (§5).
- **Most fun levers are spatial or countable** (sightlines, travel time, end conditions, counters, checkpoints, variety), so
  code owns them. The prompt carries only tone, intent and the reasons behind the design [I] (§6).
- **Principle map:** 69 principles, each with one owner: 29 code-generator, 21 code-lint, 7 prompt-guidance, 12 user-choice-ux
  (§6.2). It proposes 31 new lints: MC01–MC19 (mission), CF13–CF18 (campaign), TX01–TX06 (text), and lists doc 36's
  provisional MC30, MC31 and TX07 beside them (§6.3).
- **The embedded prompt is a set of slices**, not an essay: a ~150-word stance card written in the target register, a per-slot
  voice card, 2–3 rotated micro-exemplars and code-supplied seeds (§6.4).
- **A 9-dimension fun rubric** (1–5 with anchors) ranks candidates and scores evals. Lints admit; judges only rank. Anchor notes
  from doc 36 are queued for pack v0.2 evaluation, not adopted (§7).

## 1. The OFP/CWA campaign and mission formula

### 1.1 The 1985 campaign (Cold War Crisis)

- **Infantry is the spine; vehicles are punctuation.** The campaign has 41 numbered slots with a branch at slot 7. By mode, about
  28 are on foot, 6 in tanks and 7 in aircraft (our tally from the GameRevolution walkthrough) [I]. Critics praised "the feeling
  of being a small cog in a giant war machine" (Electric Playground, Metacritic) and a "large variety of gameplay" (Gamer's Pulse) [V].
- **The lens widens as the war grows.** Missions 1–12 are all on foot. The first vehicle seat is a tank training mission (#13, about
  32% in), squad command arrives at #20, "another learning mission" (about 49%), helicopter flying at #28 and the jet at #34.
  During #27–35 the mode changes almost every mission [V for titles and entries, I for the percentages].
- **Start low, earn command.** The infantry protagonist starts as a low-ranked soldier and ends a lieutenant (Wikipedia) [V].
- **New seats are taught just in time, at low stakes.** The first helicopter mission is a ferry run where "you will not be attacked
  by anyone"; tank and command missions open as training (GameRevolution) [V].
- **The plan meets the enemy.** At #6 the town falls easily, then a withdrawal is ordered, the truck is destroyed whatever you do and
  the transport helicopter is shot down [V]. Mid-mission reversals recur across the campaigns; the engine supports them by revealing
  hidden `OBJ_` lines (doc 26 §7.1) [I].
- **A survived defeat is the pivot.** The follow-up branches to a lone escape or a different mission, and both rejoin at a rescue
  (doc 26 §6) [V]. The walkthrough calls the escape "the first really tough mission" and says it shows "what is so special about
  OFP" [V]. Whether its patrols are randomised is [U] (snippet only).
- **Return to the scene of the defeat.** At #27 a tank platoon drives back to the town the infantry abandoned at #6 [V].
- **Deliberate valleys.** #19 has no enemies ("go there and back and do not get shot!"), #28 is uncontested, and the final mission
  flies comrades to the pub [V].
- **Escalation, a thread villain, a sober ending.** A rogue general's invasion escalates to a Scud and nuclear threat, he is captured
  in a pursuit mission, and both sides cover it up as a "foiled nuclear terrorist attack"; the epilogue reunites the cast (Wikipedia) [V].
- **Saves and difficulty.** Players get one save per mission; the stock campaign also placed scripted retry points ("After the
  retry-point is set…", GameRevolution #10) [V]. `saveGame` writes `autosave.fps` (doc 24; CWR source) [V]; its presence on 1.99
  is "likely" [U until probed]. Difficulty is two presets of twelve toggles: Cadet enables HUD, map position, auto-spotting,
  friendly tags, AT auto-guidance, a weapon cursor and an "Armor" toggle; enemy tags are off in both and nothing scales enemy
  numbers (CWR `DifficultyData.cpp`) [V]. What "Armor" does in code is [U].
- **Made with the shipped editor.** The developers shipped "exactly the same mission editor that we had used to design our missions",
  found scripting "much more powerful than we expected", and designed by playing (Španěl, Game Developer postmortem, 2001) [V].
  Kai Wüest credits this for rules that "stay consistent" and calls the pacing "incredibly varied without ever feeling like a theme
  park experience" [V].

### 1.2 Red Hammer (Codemasters, 2002)

The same war from the Soviet side. The protagonist, a demoted veteran, protests when sent to kill unarmed civilians, switches sides
and ends by arresting the general's loyalists (Wikipedia) [V]. A run of titles tracks his turn, and variety comes from vehicle
blocks with one protagonist (Cheatbook) [V]. Reception was mixed: praise for playing "the other side", split views on difficulty,
and "should have been released as a free addon" (Games.cz, per Wikipedia) [V]. Kai Wüest faults its "nonsensical lone-wolf suicide
missions" whose achievements "rarely lead to anything tangible" [V]. CWA omits it because Bohemia lacks the rights [I].

### 1.3 Resistance (2002, set in 1982)

- **Peacetime first.** The first mission opens with a choice between catching the bus and riding a motorbike, then the invasion
  arrives (SuperCheats) [V].
- **An early choice of conscience with a real price.** Betraying the rebel leads to the hero's execution as a traitor; fighting
  leads on (Wikipedia; SuperCheats) [V].
- **Persistence is the signature.** Weapons, ammo and soldiers carry over; the wounded and dead do not return; medics are precious;
  recruits improve; stockpiling pays (GamingExcellence; Old PC Gaming; SuperCheats) [V].
- **Yesterday changes today.** Succeeding at an intel mission removes two tanks from the next one [V]. But the cause of new recruits
  was so opaque that a walkthrough author could only guess it [V], a legibility failure [I].
- **Reception** (metascore 77): "some of the best gameplay scenarios yet seen in the genre" (PC Gamer), memorable moments such as
  "the rush of fleeing a successful ambush before the Soviets mobilize and send in their Hinds" (Old PC Gaming). Criticism: weak AI
  under conserve-your-men rules, saves, the command interface, less variety than the original, "lengthy cut scenes" [V].

### 1.4 The shared formula [I]

One world and one recurring antagonist across three campaigns; a closed set of task verbs (patrol, assault, defend with a setup
phase, ambush, escape and evade, rescue, infiltrate, sabotage, recon, escort, transport, air strike, capture equipment, pursue a
leader); night and NVG missions; defence missions with prep time and mines ("Plant your mines… get everyone a clear line of fire",
SuperCheats) [V for the quotes].

## 2. Why OFP was fun, and the frustrations to avoid

### 2.1 What critics and players praised

- **Recognition.** Metacritic PC 85; Computer Gaming World 2001 Game of the Year; Computer Games Magazine best action game and
  "Best AI"; over 1 million sold by 2002 and 2 million by 2010 (Wikipedia) [V].
- **Freedom of approach.** "How you go about doing them is completely up to you" (Kai Wüest); "a genuine sandbox" (Gamepressure) [V].
  Counterpoint: one Steam reviewer found stealth levels open-looking but with "only one arbitrary, 'correct' way" [V].
- **Scale and meaning.** Tactical objectives interwoven "with steady progress on the strategic level"; AI advances and "constant
  radio chatter" create "the illusion of a large-scale operation" (Kai Wüest) [V]. GameSpot (2001) found the world "much more alive
  and immersive than that of most shooters" [V, via text proxy].
- **Combined arms.** Any vehicle, "orders and mission conditions permitting"; the game simulates "the complex combined arms
  relationships" (Wikipedia) [V].
- **Lethality at range.** Fights at "around 250 meters" (Old PC Gaming) where "a single bullet could bring the campaign to an abrupt
  halt" (Kai Wüest) [V]. Hearing armour before seeing it rests on one reader comment and one review line [I].
- **An enemy that seemed smart and fair.** It used cover, retreated, called for help and flanked (Games Xtreme; 2002 forum posts) [V].
- **Squad attachment.** Completing a mission "while keeping everyone alive" feels "incredibly rewarding" (Kai Wüest) [V].
- **Authenticity, not exhaustive realism.** Marek Španěl: realism can be "a completely crazy, far-fetched simulation with a morbid
  emphasis on unimportant things", while an authentic game can "immerse and educate"; "I never wanted to glorify war" (Bohemia
  History #3) [V]. Radar was dropped because players would ignore "the game environment itself"; environments drew on real places [V].
- **Characters.** "Taken right out of a B-movie script, and I mean that in the best way possible" (Kai Wüest) [V]. Plot was the weak
  lever ("wafer-thin", Just Games Retro), character the strong one [I].
- **The editor and co-op culture.** User missions made the demo worth "more than many full versions" (Bohemia History #3); co-op
  sessions ran on "hunderends [sic] of user-created mission[s]" (Steam review); ofpisnotdead.com still runs a master server [V].
- **Audio.** Radio chatter, voices and gunfire "crisp and clear" (Games Xtreme); a soundtrack "quite tame for a shooter" that "works
  surprisingly well" (Kai Wüest) [V]. Instrumentation and iconic casualty calls are [U].

### 2.2 Frustrations, and the principle that answers each

| Frustration | Evidence [V unless marked] | Answered by |
| --- | --- | --- |
| Lost half-hours | "Losing 30 minutes of progress in an instant is not fun" (Kai Wüest); checkpoints "spread out" (Steam, 2014) | FP24 |
| Realism over playability | "at times it will bore less-than-hardcore war gamers" (Next Generation, via Wikipedia, re-fetched 2026-09-27); "fun suffers at realism's hands" (GameSpot) | FP05, FP32 |
| Triggers that never fire | "Hiccups in mission scripting prevent certain triggers from activating" (Kai Wüest); "and then… nothing" (Steam, 2018) | FP18, FP19 |
| Hunting the last straggler | "You have to hunt for those hiding enemy soldiers before the objective is completed" (Steam, 2018) | FP18 |
| Empty walks | "Run across that forest for 10 real life minutes with no speach [sic]" (AnandTech, 2002) | FP32 |
| Death from nowhere | "Pixaleted [sic] specs" killing from "insane distances" feels "frustratingly unfair" (Old PC Gaming) | FP15, FP16 |
| Needle in a haystack | A new player quit when the car to steal was not at the marked spot (Steam, 2021) | FP08 |
| Unreadable stealth | Unseen "within 20 meters", spotted prone "from over 200 meters" (Steam review) | FP22 |
| AI drivers | "Incapable of driving vehicles in a straight line" (Kai Wüest) | FP21 |
| Command interface | "Non-intuitive squad command system" (Gamers' Temple) | FP31, FP23 |
| Lone-wolf suicide runs | Red Hammer critique (Kai Wüest) | FP23 |
| Opaque consequences | Recruits whose cause a walkthrough author could only guess | FP45 |
| Long cutscenes | "A series of lengthy cut scenes" (GamingExcellence, Resistance) | FP44 |

## 3. The community's mission-making craft

### 3.1 The quality gate

OFPEC reviews scored four craft categories (Overview, Briefing, Camera, Scripting), a separate overall score out of 10 and a member
rating out of 5; beta boards returned "a list of bugs and comments" (OFPEC FAQ) [V]. No rubric defines the categories and the
overall is not their average: one campaign shows 8/10 overall over categories of 6, 7, 6, 5 [V/U]. Staff and members can disagree
sharply (6/10 staff against 5/5 members, and 8/10 against 1.5/5) [V]. Caveat: most OFPEC tutorials cited here are a later series
covering OFP:R 1.96, ArmA and ArmA 2; their craft advice transfers, but every mechanic must be checked against the OFP/CWA engine [V].

### 3.2 What the best-loved missions did [V, OFPEC depot reviews]

| Mission (score) | What reviewers praised | What they faulted |
| --- | --- | --- |
| *Abandoned Armies* (10/10 in all four categories, 4.9/5) | A "living island"; "don't feel you have to shoot everyone"; 15 state-dependent cutscenes, some "secret"; squadmates with "a unique personality"; randomisation "for the replay value" | Demanding: "the best part of a day", needing "skill, patience and guts" |
| *Operation Rattlesnake* (8/10) | "1 out of 4 possible insertion points", "4 different extracts"; AI reacting to "a neutralized enemy" | Repetitive briefing; markers not matching intel; stealth gear useless once loud |
| *The Black Gap* (9/10) | Friendly squads report contacts and casualties by radio; a concise briefing; "many random events" | Music during firefights; slow move orders |
| *The Last Months in Vietnam* (8/10) | A difficulty curve that "eases you in gently"; varied objectives; music never repeated | Lingering shots; spelling |
| *Grunt ONE* (8/10) | "Objectives can be accomplished in multiple ways"; civilians reveal caches | Flat side characters; players could not tell a design rule from a bug |
| *Too Young To Die* (8/10) | Voice acting for every message; "surprising twists mid-game"; three radio-menu quicksaves | A first mission of "about 2 hours"; unclear objectives; no ending scene |

### 3.3 What low-rated missions got wrong [V]

An enemy that "won't even react when you take out their bases"; missions that "might not end"; "not so informative briefings" and
"bad usage of titletext" (*Intrusion*, 4/10). Filler missions, no intro or outro, and absurd odds ("30+ BMPs/T80s/T72s" against an
M60 and 3 LAWs) (*ULOTC*, 4/10). "this isn't a campaign - it's a mission pack", with a hero who is pilot, black op, private and
tank gunner, and "static armour units are asleep" (*SharkEye II*, 6/10).

### 3.4 What the tutorials teach [V unless marked]

- **The last loon.** "An objective that won't tick off… caused by a trigger that waits for one side not present while there is one
  soldiers [sic] still hiding" (OFPEC Atmosphere tutorial); reviews cite "the infamous 1 km radius 'Not Present' trigger". OFP/CWA offers
  only Present, Not present and Detected-by activation: **"Seized by" arrived in ArmA 1.05** (PMC wiki; doc 03). Robust ends use
  `thisList` with `countSide`, `fleeing` and timeouts, all registered in the CWR source.
- **Dead air.** After a minute of silence players switch to 4x speed, and a death becomes "no problem as you can just reload";
  dialogue, radio or scenes should fill transport legs.
- **Atmosphere.** "Life is dynamic, so should a mission be"; empty towns and static bases ruin it; let the player choose the route;
  a broad armoury distracts from the story; "atmosphere alone is nothing without proper gameplay".
- **Cinematics.** "The ultimate goal for each scene should be emotion"; show, don't tell; spinning editor cameras and slow zooms are
  "instantly recognisable as novice"; keep scenes short and secure units first (OFPEC; PMC wiki; aligrant.com).
- **Craft levers.** Probability of presence, placement radius and min/mid/max timers add replay value; skill 100 made "Uber
  troopers" (COMBATSIM, 2002); keep AI groups to 6–8; music only where it fits, with fades; a named mission, a readme listing
  version and addons, no needless addons, no spelling mistakes.
- **Campaigns.** Two valid styles: story-driven (about 5–10 missions, characters, cutscenes) and content-driven (dozens of missions,
  slim story) (PMC wiki). Reviewers rewarded missions that felt like "a small leg in a bigger operation" (DVC review).
- **Makers.** "The best editors are players first" (OFPEC); testers watched battles from a civilian observer (COMBATSIM).

**Synthesis [I].** The four separators between 8+/10 and ≤6/10 missions: it reliably ends and progresses; the enemy reacts; the
briefing answers what, why and how with markers and an enemy estimate; presentation is short, purposeful and emotional. Unit count,
custom music and addons do not rescue a mission that fails these.

## 4. What research says about fun

| Idea | Source | Grade | What we take |
| --- | --- | --- | --- |
| Competence, autonomy and relatedness predict enjoyment and future play; intuitive controls work through competence | Ryan, Rigby & Przybylski, *Motivation and Emotion* 30(4):344–360, 2006 | Well-supported (4 studies) | Open methods, visible mastery, named people |
| SDT is often applied superficially in HCI | Tyack & Mekler, CHI 2020 | Well-supported | Heuristics, not formulas |
| Need *frustration* is distinct: constrained playstyle, stagnation, unfair situations, meaningless choices, disconnection | Ballou & Deterding, CHI PLAY 2023 (12 interviews); BANGS scale 2024 | Qualitative, then validated scale | The anti-pattern list in §6 |
| Only competence frustration predicted ill-being | Tyack & Wyeth, CHI PLAY 2021 (n=148) | Single study | Fairness lints are top priority |
| Competence-impeding play raised aggression independent of violent content | Przybylski et al., JPSP 2014 (7 experiments) | Well-supported | Grim themes are fine; thwarted competence sours play |
| Low need satisfaction went with obsessive passion, more play, tension after play and lower enjoyment; high need satisfaction with harmonious passion and energy | Przybylski, Weinstein, Ryan & Rigby, *CyberPsychology & Behavior* 12(5), 2009 | Correlational; abstract only [V-search] | Optimise need satisfaction, never time played |
| Interrupted tasks: no general memory advantage (Zeigarnik), but a general tendency to resume them (Ovsiankina) | Ghibellini & (Beat) Meier, meta-analysis, 2025 | Meta-analysis [V-search] | Open threads pull players back; close them at natural stopping points |
| Goal gradient: effort rises as a reward nears and resets after it pays | Kivetz, Urminsky & Zheng, *JMR* 2006 (coffee-card field study) | Field study [V-search] | Staggered tracks between camps; no illusory progress (doc 36 cv01, cv43) |
| Flow: challenge matched to skill, clear goals, immediate feedback; players' zones differ | Chen, CACM 2007; GameFlow 2005 | Established construct; game models are heuristics | Clear objectives, feedback, user-chosen difficulty |
| Difficulty alone showed no pooled effect on enjoyment; music did | Caroux & Pujol, IJHCI 2024 (meta-analysis, few studies) | Absence of evidence | "Harder = more fun" is folklore |
| Pacing waves: Build Up → Sustain Peak (3–5 s) → Peak Fade → Relax (30–45 s); "adjusts pacing, not difficulty"; "structured unpredictability" | Booth, *AI Systems of Left 4 Dead*, 2009 | Practitioner wisdom (co-op shooter) | Mission-scale use is analogy [I] |
| Storytellers pace one simulation for different tastes | RimWorld wiki | Practitioner | Pace presets |
| Value lives in the player's mental model; apophenia supplies story; unseen complexity is wasted | Sylvester, *The Simulation Dream*, 2013 | Design argument | Few, legible systems |
| Emergent material "will almost always lack story structure" without curation | J. Ryan, PhD 2018 | Well-argued thesis | Record and retell (FP14) |
| Fun is learning patterns; boredom when exhausted | Koster, 2004 book; 2012 talk | Designer's argument | Teach, then rotate |
| Interesting decisions: tradeoffs, situational, expressive, with enough information | Meier, GDC 2012 ("Good decisions are situational") [V]. The older "series of interesting decisions" line: a GDC talk Meier recalls, year and wording [U]; the 1997 Usenet version is Darren Reid's (doc 36 §3.2) | Practitioner | No dominated options |
| Removing time pressure lets players set their own learning curve; Meier's real-time Civilization prototype overwhelmed players | Johnson, "Turn-Based Versus Real-Time", 2009 | Practitioner [V] | Strategic picks never under fire (doc 36 cv22) |
| Interfaces have a teaching level and a reference level; players must be able to track their options at one time | Johnson, "Seven Deadly Sins", 2008 (reprinted 2013) | Practitioner [V] | Teaching and reference layers; few live options |
| "(total fun) = (meaningful decisions) / (time played)", offered as a heuristic, not a law | Johnson, "When choice is bad", 2013 | Practitioner heuristic [V] | Code does the chores; few weighty picks (FP32) |
| "Given the opportunity, players will optimize the fun out of a game" | Johnson, "Water Finds a Crack", 2011 | Practitioner [V] | Defaults discourage tedious exploits (doc 36 cv21) |
| Theme is not meaning: "meaning emerges from a game's rules", its decisions and consequences | Johnson, GDC 2010 "Theme is Not Meaning" (session description) | Design argument [V] | Told consequences need a typed effect (TX07) |
| Framing: a rest penalty recast as a bonus with "exactly the same" maths was loved | Rob Pardo, GDC 2010, via Shacknews | Practitioner anecdote [V as reported] | Bonus framing for optional modifiers; numbers stay visible (doc 36 cv13) |
| Meaningful play: outcomes "discernable and integrated" | Salen & Zimmerman, 2003 | Definition | Visible consequences |
| Acknowledging a choice preserved agency as well as real branching (short text stories) | Fendt et al., ICIDS 2012 | Narrow experiment | Acknowledge every choice |
| Meaningful choices are consequential, social, moral | Iten et al., CHI 2018 | Mixed-method | Few, weighty choices |
| Players prefer to feel responsible for failure; failing then succeeding rated highest | Juul, 2009 experiment; *The Art of Failure*, 2013 | Small experiment + theory | Fair, telegraphed lethality |
| Difficulty and death enabled meaningful experiences | Petralito et al., CHI 2017 (n=95) | Survey | Keep lethality |
| Peak and end shape remembered challenge | Gutwin et al., CHI 2016 (casual games) | Narrow experiment | End strong [I for long missions] |
| Curiosity comes from information gaps; uncertainty sources | Loewenstein 1994; Costikyan 2013; Schell lenses | Theory + wisdom | Anticipation cues |
| Variety must be perceived: "10,000 bowls of plain oatmeal" | Compton, blog (the Casual Creators paper says 1000, doc 26) | Practitioner | Perceptual differentiation |
| Choice overload: mean effect "virtually zero", large variance | Scheibehenne et al., JCR 2010 | Meta-analysis | Menu caps justified by weak models, not psychology |
| Dark pattern: used intentionally against players' best interests and "likely to happen without their consent" | Zagal, Björk & Lewis, FDG 2013 | Definition [V, via Deterding et al.] | No streaks, dailies, grind or nags (doc 36 §4.5) |
| The dark-pattern concept is "ontologically incoherent", but transparency and regret are fruitful starting points | Deterding, Stenros & Montola, DiGRA 2020 | Critique [V] | Judge pull by regret, consent and transparency |
| Eight aesthetics; Four Keys; Bartle types; 12 motivations | MDA 2004; Lazzaro 2004; Bartle; Quantic Foundry | Vocabulary | Use to name targets only |

The Johnson, Pardo, 2009 Przybylski, Ovsiankina, goal-gradient, Zagal and Deterding rows come from doc 36 (§1, §3.1, §4.5), which
holds their fetch status. Doc 36's **[V-search]** (seen only in search results or an abstract) counts as [U] under this file's legend.

**Folklore kept out of the harness [I].** "Fun = dopamine" (not actionable), Bartle types as the audience model for single-player
campaigns, the 8 aesthetics or 4 keys as validated science, "more branches = more agency", "harder = more fun", "realism = fun",
and "fewer options are always better".

## 5. Mil-sim tastes, and LLM narrative pitfalls

### 5.1 What mil-sim players love [V unless marked]

- **Selective authenticity.** War games stress material culture while perspectives stay "superficial, one-dimensional, if not
  entirely removed" (Salvati & Bullinger via Hammar & Woodcock). Španěl's answer: authentic, humane, not glorifying.
- **Plan, then lethal execution with permanent loss.** Rainbow Six's planning map and "deceased operatives are permanently lost";
  Ghost Recon's soldiers "not available for the rest of the campaign" (Wikipedia). Squad: "It makes moments matter" (Gamereactor).
- **Orders as ritual.** SMEAC, commander's intent, brevity ("the art of saying a lot with few words"), readback, structured contact
  reports; "keeping a briefing simple… will result in more people reading it" (ShackTac TTP2).
- **Radio with purpose.** A leading DCS campaign author finds random chatter unrealistic; his campaigns carry thousands of lines,
  "almost none of it idle" (Stormbirds Q&A, 2024).
- **Tone matters.** Red River (Codemasters, 2011) swapped understatement for macho profane banter; critics named the "overly macho
  voice acting" (PC Gamer, per Wikipedia) and a catchphrase "by turns hilarious and annoyingly repetitive" (Gaming Nexus). Metacritic
  67–69 against the original's 85; that tone caused the gap is [I].
- **Long walks, short fights** "is exactly the opposite of what most players look for… but it does have its charms" (Arma 3, MMOs.com).
- **Emergent stories need framing.** Player narratives depend on "structured, designer-produced settings" (Tom Cross, 2009).
- **Humane lens.** Arma 3 Laws of War (2017, with the ICRC) centred civilian harm and unexploded ordnance.

### 5.2 How LLMs fail at game narrative, and the countermeasure

| Pitfall | Evidence [V] | Countermeasure [I] | Owner |
| --- | --- | --- | --- |
| Positive, low-tension arcs; negative arcs nearly absent | Tian et al., EMNLP 2024 (explicit discourse structure: +40% diversity, suspense) | Code picks arc shape and beats; model writes inside a beat | code-generator |
| Far below professional craft | Chakrabarty et al., CHI 2024 (LLMs pass 9–30% of TTCW tests vs 85%) | Small slots, human accept/edit | user-choice-ux |
| Cliché, purple prose, needless exposition, vagueness | LAMP, CHI 2025 (1,057 paragraphs, all model families) | Stance card + TX04 phrase list + caps | code-lint |
| Over-explained themes, tidy single-track plots, little moral ambiguity | StoryScope, arXiv 2604.03136 (61,608 stories) | "Consequence, not lesson"; code-owned twists | prompt-guidance |
| Homogeneity across users and models | Doshi & Hauser 2024; Wenger & Kenett 2026 (22 LLMs) | Seeds from code menus; K candidates; TX05 similarity | code-generator |
| RLHF mode collapse | Kirk et al., ICLR 2024; Verbalized Sampling 2025 (weaker models gain less) | Ask for several candidates; code picks diversity | code-generator |
| Stock names ("Elara Voss", a 77% top-10 skew) | HF name experiment; Laforge 2025 | Names from nationality pools only | code-generator |
| Stock phrases 1,000x over-represented | Antislop, arXiv 2510.15061 | Backtracking banlist or reject + retry | code-lint |
| Villains flattened into shallow aggression | *Too Good to be Bad*, arXiv 2511.04962 | Villainy in few decision-makers; menu of motives | prompt-guidance |
| Hindsight leaks ("cannot forget") | Göttlich, Loibner & Voth, 2025 | Era and hindsight lexicon lint | code-lint |
| Length instructions broken; length bias | Yuan et al., arXiv 2406.17744 | Hard caps in code | code-lint |
| Negated instructions work poorly; examples get copied | Jang et al. 2022; Anthropic prompting guidance | Positive, reasoned, style-matched prompt; rotated exemplars | prompt-guidance |
| Specific prompts lower story quality on mid-size models | CS4, arXiv 2410.04197 | One small decision per slot | code-generator |
| Writers want drafts, not finals | Ubisoft Ghostwriter, GDC 2023 | Accept, edit, pin, re-roll | user-choice-ux |

**The gap [I].** An LLM's default register (positive, tidy, explanatory, moralising, ornate, verbose, generic) is nearly the
inverse of the OFP register (understated, uncertain, laconic, sudden, morally grey, specific). Plan-then-write, persona conditioning
and min-p sampling help (Yao et al. 2019; Persona Hub; Nguyen et al. 2025) [V], but for 3–9B models most of the register must be
enforced by code. No domain measurement of weak-model voice-card adherence exists [U].

## 6. The principle map

### 6.1 Owners and the ownership rule

- **code-generator**: deterministic, seeded generation (archetypes, skeletons, placements, templates, menus) builds it in.
- **code-lint**: a validator detects the violation in the typed model or the simulator (warn or error, with a witness).
- **prompt-guidance**: only taste the model can act on in one bounded text or ranking step (tone, register, character voice).
- **user-choice-ux**: the director decides; code offers computed options and shows consequences.

**Rule [I]: if code can generate or check it, it is not left to the prompt.** A prompt-guidance principle may also have a
heuristic lint, but never a hard dependency on the model obeying.

### 6.2 Principles FP01–FP65

| ID | Principle | Owner | How it applies (generator / lint / prompt / UX) | Evidence |
| --- | --- | --- | --- | --- |
| FP01 | Small cog in a big, living war | code-generator | Ambient friendly and enemy groups beyond the objective; HQ radio slots for other sectors; earlier outcomes echoed. Prompt writes one "why it matters" line | §1.1, §2.1 |
| FP02 | One operation, not a mission pack | code-lint | CF13: node unlinked to the operation goal or prior outcome; role change without story reason; untagged tonal outlier | §3.3, §1.2 |
| FP03 | Grounded, contained premise with escalation risk | user-choice-ux | Premise cards (doc 25 S1) default to contained crises; world-war premises offered, not defaulted | §1.1 |
| FP04 | The island is a character | code-generator | Objectives, rally points and lines anchored to named island features; routes follow landmarks | §2.1 |
| FP05 | Authentic, not exhaustive | prompt-guidance | Stance card: detail only when it changes a decision or is perceived. MC03 catches realism as tedium | §2.1, §4 |
| FP06 | Give the goal, not the path | code-generator | Compute ≥ 2 approach corridors or insertions and ≥ 1 extraction; outcome-based objectives. MC11 checks | §2.1, §3.2, §4 |
| FP07 | Brief the intent in few words | code-generator | SMEAC skeleton (doc 26 §7.1): task plus reason per `OBJ_`, enemy estimate, support, `marker:` links; model fills bounded colour | §3.4, §5.1 |
| FP08 | Hide the enemy, never the objective | code-lint | MC10: objective assets inside the marked or briefed area in every variant; briefing names only existing markers and places | §2.2 |
| FP09 | Options must trade something | code-lint | MC13: offered loadouts, supports and routes carry a cost (noise, pool, time); dominated or outcome-random options flagged | §4 |
| FP10 | Defenders get a setup phase | code-generator | Defend archetype: prep timer, mines, satchels, AT positions, a hint of the approach | §1.4 |
| FP11 | Systems, not rails: a reactive enemy | code-generator | Behaviour template per enemy group (patrol, guard → alarm, QRF, loss reaction, random reinforcement timer). MC04 checks | §3.2, §3.3 |
| FP12 | Controlled randomness with a floor | code-generator | Presence, radius, alternate routes and timers on non-critical elements; seeded; worst-case variant validated; critical path never random | §3.4, §4 |
| FP13 | Reward curiosity | code-generator | Optional discovery slots (cache, vantage, helpful civilian, state-dependent scene); visible in the glass-box view; never survival-critical | §3.2 |
| FP14 | Make emergent moments retellable | code-generator | Record engine-observable notable facts; debrief and next briefing retell 1–2 | §4, §5.1 |
| FP15 | Lethal but legible | code-lint | MC08: no enemy MG or sniper line of sight onto start, LZ or rally; no spawns in view; known threats named in the briefing | §2.2, §4 |
| FP16 | Telegraph before you punish | code-generator | ≥ 1 cue (sound, radio, sighting, intel line) before each lethal set piece; armour heard before seen [I]. MC08 checks the cue | §2.1, §3.2 |
| FP17 | Every threat has a counter; gear fits every phase | code-lint | MC05: armour needs AT, air needs AA or cover; stealth kit needs a loud-phase fallback; no armoury buffet | §3.2, §3.3 |
| FP18 | Every mission can always finish | code-generator | End templates from `thisList` thresholds, `fleeing`, named-target state, timeouts; never large "Not present". MC01 checks | §3.4 |
| FP19 | No single point of failure on the critical path | code-lint | MC09: critical NPC, vehicle or trigger has a fallback (backup unit, timeout, player takeover) | §2.2 |
| FP20 | No hidden rules | code-lint | MC02: every failure trigger's rule and consequence stated in `OBJ_`, Plan or a prior radio line | §3.2 |
| FP21 | Critical AI stays on terrain where it behaves | code-lint | MC14: critical convoys, drives and landings avoid dense towns, tight forest and unprobed bridges; Preview probes | §2.2 |
| FP22 | Legible stealth and alarms | code-generator | Detection has visible causes; alarm escalates (radio, flare) into a QRF from a known direction; no fine-margin stealth phases | §2.2 |
| FP23 | No lone wolf without means | code-lint | MC15: solo missions need a stealth route, tools, a planned extraction and a consequence | §1.2 |
| FP24 | Protect progress; the player picks the risk | user-choice-ux | Campaign save policy (ironman, one save, checkpoints); generator places `saveGame` at phase ends and briefed medic and ammo points. MC12 checks | §1.1, §2.2, §3.2 |
| FP25 | Failure moves the story forward | code-generator | Every node has a survivable failure outcome routed to a detour or harder variant (builds on doc 19 C03, doc 26 CF07) | §1.1, §1.3, §4 |
| FP26 | A survived defeat as the pivot, and a return | user-choice-ux | Pattern card: early reversal → escape or rescue node → rejoin; a later node revisits the site in a stronger seat | §1.1 |
| FP27 | Difficulty is visible dials; enemies stay honest | user-choice-ux | Separate help (markers, Cadet-only waypoints, intel detail, checkpoints, player armour) from challenge; no hidden rubber-banding | §1.1, §4 |
| FP28 | Sane skill bands and a gentle opener | code-generator | Skill from a band by node depth and preset (≈ 0.3–0.7 [I]); force ratio counted. MC16 and CF14 check | §3.4, §3.2 |
| FP29 | Persistence never punishes the AI's mistakes | code-lint | CF15: no critical-path capability held by one persistent specialist; replacements, wounded state, minimum loadout | §1.3 |
| FP30 | A tension curve inside every mission | code-generator | Phases insertion → approach → contact → objective → reaction → exfil with intensity tags; model picks the complication from a menu | §4, §1.3 |
| FP31 | Few commands under fire | code-generator | Set pieces must not require micromanaging many AI units; squad tasks default to simple orders | §2.2 |
| FP32 | No dead air | code-lint | MC03: movement legs over ~3 min [I] with no event slot; quiet missions short and labelled as breathers | §2.2, §3.4 |
| FP33 | Campaign rhythm is a sawtooth with valleys | code-lint | Existing CF01–CF02; Relax nodes are real missions or scenes, not gaps | §1.1, §4 |
| FP34 | Start low, earn command | code-generator | Skeleton grows rank, authority and seats; squad command near mid-campaign via a learning mission | §1.1 |
| FP35 | One spine role; guest seats as punctuation | code-generator | ~2/3 of nodes in the spine role; guest seats later and rotating faster as the war widens | §1.1, §1.2 |
| FP36 | Teach a new seat just in time, at low stakes | code-lint | CF16: the first node with a new seat or role must be Relax or Build | §1.1 |
| FP37 | Vary verb, seat, clock and weather | code-lint | CF17 (extends CF03): same verb, seat and time 3× in a row; no night or stealth mission in a campaign of 6+ (info) | §1.3, §2.1 |
| FP38 | Perceived variety, not oatmeal | code-generator | Variation axes chosen for perceptual difference; creative slots seeded (twist, mood, detail token, names); K candidates. TX05 checks | §4, §5.2 |
| FP39 | Name the fun each mission is for | code-generator | Each mission declares 1 primary and ≤ 2 secondary experiences from a closed set; knobs follow. CF18 checks coverage | §4 |
| FP40 | One fair surprise per mission | user-choice-ux | ≤ 5 legal twist cards; model ranks; user picks or rolls. MC17 requires a foreshadowing cue | §1.1, §3.2, §4 |
| FP41 | End strong, then breathe | code-generator | Climax near the end; debrief names what the player did; campaign finale then a short denouement. MC18 checks | §1.1, §4 |
| FP42 | Mood as punctuation; music with purpose | code-generator | Model picks mood from a menu; code places tracks at intro, outro, set-piece starts and quiet beats with fades, never under firefights | §3.2, §3.4 |
| FP43 | Short, emotional, well-shot scenes | code-generator | Shot grammar; caps (intro ≤ 60–90 s, in-mission ≤ 20 s [I]); squad secured; skippable; no orbit-and-zoom. MC19 checks | §3.4 |
| FP44 | Scarcity you can see, earn and lose | code-generator | Pools fed by capture or scavenge missions, shown on the gear screen, stakes briefed | §1.3 |
| FP45 | Yesterday's result changes today, and says why | code-lint | CF04 extension: each consequence variant or persistent effect (forces, recruits, losses, gear) differs visibly and carries a cause line in the next briefing or gear screen (C21 coverage) | §1.3 |
| FP46 | Losses persist and are remembered | code-generator | Roster and pool modules (doc 26 §5.2) carry casualties and gear; later lines are gated on alive-on-path (C18, C21); the debrief lists who fell | §1.3, §5.1 |
| FP47 | Acknowledge every choice; make a few real | code-lint | CF05 plus: a choice framed as momentous must change state; lines see prior choices in their fact scope | §4 |
| FP48 | Few, weighty choices of conscience | user-choice-ux | Loyalty or conscience choice nodes with hinted consequences; the archetype vocabulary has no atrocity objective; weight comes from refusing or protecting | §1.2, §1.3, §4 |
| FP49 | People worth keeping alive | prompt-guidance | Voice card: one trait, one want, one way of speaking; casualties audible. Code: CF06, C18; keep-alive rules stated (MC02) | §2.1, §3.2 |
| FP50 | A thread villain and a reunion | code-generator | Story bible antagonist row; beats for escalation and confrontation; survivor reunion built from roster state | §1.1, §1.4 |
| FP51 | Enemies are soldiers too | prompt-guidance | Villainy sits with a few decision-makers; conscripts competent and human; no mock accents | §5.2, §2.1 |
| FP52 | Show the other side, with a new idea | user-choice-ux | Perspective flip or prequel as a pattern parameter; must add a mechanic or situation, not a reskin | §1.2 |
| FP53 | Open in peacetime, let the war arrive | code-generator | Opening-beat menu offers a routine, training or civilian-life prologue first for story-driven campaigns | §1.3 |
| FP54 | Titles and beats trace the inner arc | prompt-guidance | Title slot sees the arc beat and protagonist state | §1.2 |
| FP55 | Story-driven or content-driven: the user chooses | user-choice-ux | A style slider sets budgets for scenes, dialogue slots and mission count | §3.4 |
| FP56 | Co-op versions with friends | user-choice-ux | MP target adds playable slots and co-op respawn and end rules; campaigns stay single-player (doc 18) | §2.1 |
| FP57 | Radio is the war's voice | code-generator | Code decides when (contact, casualty, objective change, reinforcement, phase) and who; line templates (doc 26 §7.3); model fills ≤ 1 colour clause | §2.1, §3.2, §5.1 |
| FP58 | Understate; suggest, don't explain | prompt-guidance | Stance card; feelings through action or omission; deaths reported, not eulogised. TX06 heuristic | §5.1, §5.2 |
| FP59 | Grim but humane; consequence, not lesson | prompt-guidance | No glory, no gore for kicks, no sermons; debriefs state what happened and what it cost | §2.1, §5.2 |
| FP60 | Vivid people, sober world | prompt-guidance | Characters may be larger than life; hardware, procedure and geography stay grounded and period-correct | §2.1 |
| FP61 | Specific beats generic; code supplies every fact | code-generator | Names from nationality pools, places from the island, gear from the catalog, numbers and grids from code. TX02 checks | §5.2 |
| FP62 | Era-true words, no hindsight | code-lint | CF11 lexicon plus TX03 hindsight list | §5.2 |
| FP63 | Short enough to read under fire | code-lint | TX01 hard caps per slot; over cap → reject and fall back to the skeleton line | §3.3, §5.1, §5.2 |
| FP64 | One voice per character; tics rationed | code-lint | TX05 per-speaker phrase repetition limit and cross-candidate similarity | §5.1, §5.2 |
| FP65 | Polish the text and the package | code-lint | MC07: spelling, consistent names, a named mission, no single-use addons, a readme | §3.2, §3.4 |
| FP66 | The user is the director | user-choice-ux | No blank canvas; three outlines; "surprise me" with pins; drafts with provenance; accept, edit, pin, re-roll; human edits never overwritten (AGENTS.md, doc 25 §9, doc 26 §8) | §2.1, §5.2 |
| FP67 | A craft report card, not a verdict | user-choice-ux | Overview, Briefing, Camera, Playability and Polish rolled up from lints and the simulator, each item linked to its element; no weighted total | §3.1 |
| FP68 | Playtesting is part of the editor | user-choice-ux | Preview from any phase; observer mode; campaign backbone run through every transition; beta pack export with version, addons and changelog | §3.4 |
| FP69 | Performance budget in view | code-lint | MC06: live meter of units, groups per side, crew seats per group and triggers against the target profile; offers staging or scaling down | §3.4 |

### 6.3 Proposed lints (complement doc 19 C01–C21 and doc 26 CF01–CF12) [I]

Thresholds marked [I] are starting values for playtesting. `Seized by` needs no lint: the typed trigger model for target `Cwa199`
cannot represent it, and C14 rejects raw commands outside the whitelist. MC30, MC31 and TX07 are **provisional** codes proposed by
doc 36 §4.6 and listed here so the mission and text series stay in one table; MC20–MC29 are doc 34's provisional codes. The design
round assigns final numbers.

| ID | Level | Fires when |
| --- | --- | --- |
| MC01 | error / warn | Objective or end trigger uses "Not present" over > 150 m [I] or over forest or buildings (warn); a clear-type objective lacks a timeout fallback (warn); the simulator finds no completion path (error) |
| MC02 | error | A failure trigger has no player-visible statement of both the rule and its consequence before it can fire |
| MC03 | warn | An on-foot leg estimated > 3 min [I] with no event slot; objective done then > N min of scripted travel with no event |
| MC04 | warn | More than half the enemy groups are static with no trigger, synchronisation or behaviour template |
| MC05 | warn | A scripted threat class (armour, air) with no reachable counter; kit unfit for a later phase; loadout breadth beyond the unit type |
| MC06 | warn | Units, groups per side (config MaxGroups), crew seats per group (cap 12; soft 6–8), or triggers exceed the target profile budget |
| MC07 | warn | Spelling, inconsistent names across briefing, radio and stringtable, unnamed mission, addon used by one object, missing readme fields |
| MC08 | error / warn | Enemy MG or sniper line of sight onto start, LZ or rally (error); spawn in player view; lethal set piece with no preceding cue (warn) |
| MC09 | warn | Critical-path NPC, vehicle or trigger with no fallback (backup unit, timeout, takeover) |
| MC10 | error | An objective asset can spawn outside its marked or briefed area; an `OBJ_` lacks text or marker; the briefing names a missing marker or place |
| MC11 | warn | Fewer than 2 viable approaches; a failure trigger fires on a reasonable route the mission did not declare off-limits |
| MC12 | warn | Simulated duration > 30 min [I] or a phase > 15 min [I] with no checkpoint, under the campaign's save policy |
| MC13 | info | An offered option is dominated on every cost axis, or its outcome is random whatever the pick |
| MC14 | warn | Critical AI convoy, drive or landing routed through dense town, tight forest or an unprobed bridge |
| MC15 | warn | Solo or special-forces mission with no stealth route, fitting tools or planned extraction |
| MC16 | warn | A whole side at skill ≥ 0.9 [I] |
| MC17 | warn | A twist card fires with no foreshadowing cue earlier in the mission |
| MC18 | warn | Missing debrief text for a reachable outcome; climax phase not in the last third [I] |
| MC19 | warn | Scene over its cap, player squad not secured, scene not skippable, or music scheduled under a sustained firefight |
| MC30 | info | *Provisional (doc 36).* Static analysis (or the simulator, where it models the mission) finds a win reachable with no player movement or action, for example an END trigger on a timer alone with no reachable loss condition; a timed defence the player can lose is fine |
| MC31 | warn | *Provisional (doc 36); extends MC08.* An enemy reinforcement or spawn has no earlier announce cue, or a script grants the enemy knowledge of the player without a declared sensor; which commands grant knowledge waits on doc 24's audit [U] |
| CF13 | warn | A node with no link to the operation goal or previous outcome; protagonist role change without a story reason; untagged tonal outlier |
| CF14 | warn | The opening mission is the hardest on its path |
| CF15 | warn | A critical-path capability is held by only one persistent specialist (extends CF07) |
| CF16 | warn | The first node with a new seat or role is Peak or Finale intensity |
| CF17 | warn / info | Same verb, seat and time of day 3× in a row (warn); campaign of 6+ nodes with no night or no stealth mission (info) |
| CF18 | info | A path covers fewer than 3 distinct declared primary experiences |
| TX01 | error | Text over its slot cap (no truncation: reject, then fall back to the skeleton line) |
| TX02 | error | A number, grid, callsign, name or place not in the slot's fact scope (extends CF11) |
| TX03 | warn | Era lexicon hit or hindsight about later events (extends CF11) |
| TX04 | warn | Stock-phrase or stock-name list hit (project-authored list) |
| TX05 | warn | A speaker's signature phrase over its rate; candidates or briefing openings too similar across a campaign |
| TX06 | info | Heuristic: debrief or epilogue states a moral, or text names emotions instead of showing them |
| TX07 | info | *Provisional (doc 36).* A generated line claims a consequence ("the villagers will remember") that no typed effect or guard implements (text-mechanic dissonance) |

### 6.4 The prompt-guidance slice: what the embedded prompt carries [I, proposal-only]

The prompt is layered, following doc 25 §4.4 (task → digest → constraints → slot spec → exemplars → schema) and its token budgets.
Mission text in the digest stays untrusted data and is never placed where instructions go (AGENTS.md).

1. **Stance card** (~150 words, identical for every text slot, written positively and in the target register, each rule with a
   short reason, because models mirror a prompt's register and handle negated instructions poorly, §5.2):

   ```text
   You write for soldiers in a Cold War campaign, 1980s. Keep it plain and short: players read this under fire.
   Use only the names, places, numbers and callsigns in the digest. They are checked.
   The player is one soldier in a bigger operation. Say why the task matters to it.
   Give the goal and the reason. The player chooses the method.
   Understate. Report a loss in one line. Let action and silence carry the feeling.
   Characters can be vivid. Kit, ranks and radio procedure stay real and period-correct.
   The enemy are soldiers too. Blame sits with the few who give the orders.
   On the radio: callsign first, one fact per line, then over or out.
   Before danger comes a sign: a sound, a sighting, a report.
   End on what happened and what it cost. The player draws the meaning.
   Write in the slot's voice and length. If the facts do not support the slot, leave text empty and say why.
   ```

2. **Voice card** per slot (code-built): speaker id, rank and role, one trait, one want, one speech habit (with its rate), channel,
   line kind, character cap, tone enum, fact scope (entity tokens), state facts (alive on this path, prior outcomes and choices),
   the declared mission experience (FP39) and the arc beat (FP54).
3. **Micro-exemplars**: 2–3 per call, rotated from a code-owned pool built from project-authored and user-approved lines, varied by
   line kind and tone so that no single example is copied (doc 25 §4.6). They use entity tokens, never real names. Two pool entries
   as an illustration: `{hq}, {me}. Contact, {size} trucks, infantry dismounting at {place}. Over.` and
   `{name} made it back. {name2} did not. The bridge at {place} is down; their armour takes the long road now.`
4. **Seeds instead of "be creative"**: code passes the twist card, mood, one concrete detail token and the names, so the model
   never has to invent them (FP38, FP61).
5. **Stays out of the prompt**: anything a lint enforces (length, facts, era words, stock phrases), Bohemia names and text, lists of
   "don'ts", ornate example prose, and more than one decision per call.
6. **Pick and rank steps** (twist cards, complications, moods) get the same stance card plus the step's menu; the fun rubric (§7)
   is never shown to the generating model, only to judges, so candidates are not written to the test [I].

## 7. Fun rubric

Use: ranking K candidates that already passed every error-level lint, offline evals per model tier (doc 25 §11), and the craft
report card. Judges never admit content (doc 25 §3, rule 4). Score each applicable dimension 1–5 with a one-line reason that cites
element IDs; anchors are given for 1, 3 and 5. A weak judge scores one dimension per call. **Composite [I]:** a 1 on R1 or R2
disqualifies; otherwise report the vector, rank by sum, and break ties by R1 + R2. Text-only slots use R8 (and R7 for choice
acknowledgement).

| Dim | Question | 1 | 3 | 5 | Fed by |
| --- | --- | --- | --- | --- | --- |
| R1 Completable and clear | Can it always finish, and does the player know what to do? | A win can hang; objective unfindable or unstated | Completable, but one rule or asset needs guessing | Simulator proves every objective and end; every rule, marker and success condition stated | MC01, MC02, MC09, MC10, C03 |
| R2 Fair lethality | Can the player blame themselves for every death? | Deaths from unseen or unanswerable threats | Mostly fair, one spike | Every threat telegraphed, counterable, avoidable; lethal and fair | MC05, MC08, MC14, MC15 |
| R3 Agency | Does the player choose the method? | One workable path; off-route failure | Two approaches, one dominant | ≥ 2 distinct viable approaches; real tradeoffs; choices acknowledged | MC11, MC13, CF05 |
| R4 Tension and pacing | Does intensity rise and fall? | Flat walk or constant peak; dead air | A curve with one slack stretch | Build → peak → reaction → release; quiet stretches carry anticipation; campaign sawtooth | MC03, MC18, CF01–CF02 |
| R5 A living war | Does the world act without the player? | Static enemy; empty world; unconnected mission | Reactive enemy, isolated operation | Reactive enemy, audible wider operation, outcomes echoed | MC04, CF13, FP01 |
| R6 Variety and surprise | Does it feel different from the last one? | Oatmeal: same verb, seat, clock, mood | Varied data, similar feel | Distinct verb, seat, time and mood; one fair, foreshadowed surprise | CF03, CF17, MC17, TX05 |
| R7 Consequence and people | Do choices and people matter? | Hollow choices; invisible state; nameless squad | Some echoes; thin characters | Few weighty choices; visible consequences with causes; named people whose fates show | CF04–CF06, C18, C21 |
| R8 Voice and authenticity | Does the text sound like this war? | Invented facts, anachronism, purple, moralising, stock names | Correct but generic | Plain, specific, era-true, understated, distinct voices, humane | TX01–TX06, CF11 |
| R9 Respect for time | Is the player's time protected? | 30+ min without a checkpoint; long unskippable scenes; walls of text | One long exposure | Checkpoints per policy; text within caps; short skippable scenes | MC12, MC19, TX01 |

**Queued for design-sensibility pack v0.2 [I, not adopted].** Doc 36 §4.4 proposes rubric notes: R3 at 5 adds "every offered
option is the best pick in some situation"; R9 at 5 adds "each op ends at a natural stopping point"; a calibration note scores a
timer or countdown that carries no decision R9 ≤ 3 (it may fit R4 better; doc 36 residual concern 8); the rubric never scores
session length or return rate. It also proposes lens candidates cv40 (`campaign-arc`: pay-offs in flight and a new back half), cv41
(`branching-and-consequence`: each option is the best pick in some named situation) and cv42 (`briefing`: the debrief names what was
settled and the player's pick, and leaves one thing open, nothing after the finale). None of these changes the table above or the
pack until it passes the evaluation round in `prompts/design-sensibility/EVALUATION.md`.

## Open questions

1. **Stock briefing register [U].** Diary notes or orders in the 1985 and Resistance `Main` sections? A local-only survey decides the
   default voice preset (doc 26 Open question 3).
2. **Engine probes [U].** `saveGame` on 1.99; what Cadet's "Armor" toggle changes; `countSide`/`fleeing` behaviour in thresholds;
   AI driving over bridges; detection margins that make stealth archetypes safe.
3. **Thresholds [I].** The 150 m "Not present" radius, 3-minute dead-air leg, 30-minute checkpoint, skill band 0.3–0.7 and scene caps
   are guesses; they need playtests with the simulator's duration estimates.
4. **Weak-model adherence [U].** Lint-failure rate per slot, name-pool conformance, era-word hits and cross-seed similarity per model
   tier, with and without the stance card; and whether the card helps T1 models at all.
5. **Rubric validity [U].** Do judge scores track playtester enjoyment? OFPEC's staff and member scores diverged sharply (§3.1).
6. **Unverified folklore [U].** Randomised patrols in the 1985 escape mission, iconic casualty radio calls, the soundtrack's
   instrumentation, and Red Hammer's voice acting rest on snippets.
7. **Community sample bias [U].** Reddit, the BI forums and the BI wiki were unreachable; community evidence comes from OFPEC, Steam,
   2002–2003 forums and reviews.
8. **Moral-choice boundaries [I].** Which conscience choices the archetype vocabulary offers, and how they are framed, may need an
   owner decision recorded in `docs/`.

## Sources

**Repository:** doc 03 (trigger presence options; unit dialog IDC 115–117; showWP), doc 04 §6 (briefing sections, presence and
placement fields), doc 09 (MAX_UNITS_PER_GROUP 12, MaxGroups, trigger timeouts, difficulty settings), doc 18 §6–§10 (one save slot,
saves deleted at mission start, `lives`, debriefing, no MP campaign flow), doc 19 (C01–C21), doc 24 and
`docs/research/data/script-command-risk.csv` (`saveGame`), doc 25 (step shapes, prompt contract, evaluation), doc 26 (archetypes,
CF01–CF12, radio templates, Casual Creators).
**Engine source:** CWR@ffc61838b7 `engine/Poseidon/Core/Profile/DifficultyTypes.hpp`, `DifficultyData.cpp`,
`engine/Poseidon/Game/Commands/GameStateExt.cpp`: <https://github.com/BohemiaInteractive/CWR>.

**OFP history and reception (fetched 2026-09-27 unless marked):**
<https://en.wikipedia.org/wiki/Operation_Flashpoint:_Cold_War_Crisis> (re-fetched for the Next Generation and sales quotes);
<https://en.wikipedia.org/wiki/Operation_Flashpoint:_Red_Hammer>; <https://en.wikipedia.org/wiki/Operation_Flashpoint:_Resistance>;
<https://www.metacritic.com/game/operation-flashpoint-cold-war-crisis/critic-reviews/?platform=pc>;
<https://www.metacritic.com/game/operation-flashpoint-resistance/critic-reviews/?platform=pc>;
Španěl postmortem (2001-12-19): <https://www.gamedeveloper.com/business/postmortem-bohemia-interactive-studios-operation-flashpoint>;
Bohemia History #3 (2022-05-10): <https://www.bohemia.net/blog/bohemia-interactive-history-3>; "From Flashpoint to Arma" (2011):
<https://www.bohemia.net/blog/from-flashpoint-to-arma>; Gamepressure (2022):
<https://www.gamepressure.com/editorials/history-of-bohemia-interactive-masters-of-combat-sims/zd580>; GameSpot (2001, via text
proxy): <https://www.gamespot.com/reviews/operation-flashpoint-cold-war-crisis-review/1900-2810242/>; GamesRadar (2007):
<https://www.gamesradar.com/operation-flashpoint-2/>; Kai Wüest (2018): <https://kaiwueest.com/reviews/operation-flashpoint-cold-war-crisis/>;
Breeden (2007): <https://www.gameindustry.com/reviews/game-review/operation-flashback/>; GamingExcellence (2002):
<http://www.gamingexcellence.com/pc/games/operation-flashpoint-resistance/review>; Old PC Gaming:
<https://oldpcgaming.net/operation-flashpoint-cold-war-crisis-review/>, <https://oldpcgaming.net/operation-flashpoint-resistance-review/>;
Just Games Retro (2014): <https://www.justgamesretro.com/win/operation-flashpoint>; Self Similar (2013):
<https://www.selfsimilar.org/tag/operation-flashpoint/>; Games Xtreme:
<https://www.gamesxtreme.com/article/2916/operation-flashpoint-cold-war-crisis-review>.
**Walkthroughs:** <https://www.gamerevolution.com/guides/29719-operation-flashpoint-walkthrough>;
<https://www.supercheats.com/pc/walkthroughs/operationflashpointresistance-walkthrough01.txt>;
<https://www.cheatbook.de/wfiles/operationflashpointredhammer.htm>.
**Players:** Steam app 65790 discussions `1693788384135887504`, `540742667828967187`, `3046104862461441958`, `350543389014333655`
and top reviews: <https://steamcommunity.com/app/65790/>; <https://forums.anandtech.com/threads/operation-flashpoint-the-new-gold-standard.706214/>;
<https://forums.civfanatics.com/threads/the-king-of-fps-games-operation-flashpoint.44894/>;
<https://forums.bohemia.net/forums/topic/10235-whats-the-the-difference-between-cadet-and-veteran/>; <https://ofpisnotdead.com/>.

**Community craft:** OFPEC depot lists and reviews, `index.php?action=details&id=` 1, 5, 7, 58, 87, 97, 121, 139, 188, 196, 258, 261,
262, 276, 285, 286, 293, 300: <https://www.ofpec.com/missions_depot/>; review thread <https://www.ofpec.com/forum/index.php?topic=28674.0>;
FAQ ids 49 and 57: <https://www.ofpec.com/faq/>; tutorials ids 14, 18, 24, 28, 36, 37, 38, 39, 41, 43, 274:
<https://www.ofpec.com/tutorials/>; PMC Editing Wiki `ofp:missions:` campaign_design, real_campaign, triggers, camera.sqs:
<https://pmc.editing.wiki/>; COMBATSIM (2002-09-10): <https://www.combatsim.com/memb123/htm/2002/09/opflash-me/>;
<https://www.aligrant.com/web/games/ofp/editing/cams>; Kronzky FAQ: <https://kronzky.info/theofpfaq/sp/multisave.htm>.

**Research on fun:** MDA (2004): <https://aaai.org/papers/ws04-04-001-mda-a-formal-approach-to-game-design-and-game-research/>;
Ryan, Rigby & Przybylski (2006), doi 10.1007/s11031-006-9051-8 (pages per Crossref); Tyack & Mekler (2020), doi 10.1145/3313831.3376723;
Ballou & Deterding (2023), doi 10.1145/3611028; BANGS (2024), doi 10.1016/j.ijhcs.2024.103289; Tyack & Wyeth (2021), doi 10.1145/3474709,
and (2017), doi 10.1145/3152771.3156149; Przybylski et al. (2014), doi 10.1037/a0034820; Chen (2007), doi 10.1145/1232743.1232769;
Sweetser & Wyeth (2005), doi 10.1145/1077246.1077253; Caroux & Pujol, doi 10.1080/10447318.2023.2210880; Booth (2009):
<https://steamcdn-a.akamaihd.net/apps/valve/2009/ai_systems_of_l4d_mike_booth.pdf>; <https://rimworldwiki.com/wiki/AI_Storytellers>;
Sylvester: <https://tynansylvester.com/2013/06/the-simulation-dream/>; J. Ryan: <https://escholarship.org/uc/item/1340j5h2>;
Koster (2012): <https://www.gamedeveloper.com/design/raph-koster-s-theory-of-fun-ten-years-on>; Lazzaro (2004):
<https://archive.org/stream/GDC2004Lazzaro/GDC2004-Lazzaro_djvu.txt>; <https://en.wikipedia.org/wiki/Bartle_taxonomy_of_player_types>;
Yee (GDC 2019): <https://www.gdcvault.com/play/1025742/a-deep-dive-into-the>; Meier (2012):
<https://www.gamedeveloper.com/design/gdc-2012-sid-meier-on-how-to-see-games-as-sets-of-interesting-decisions>;
<https://en.wikipedia.org/wiki/Meaningful_play>; Fendt et al. (2012): <https://ciigar.csc.ncsu.edu/files/bib/Fendt2012-IllusionOfAgency.pdf>;
Iten et al. (2018), doi 10.1145/3173574.3173915; Juul: <https://jesperjuul.net/text/fearoffailing/>; Petralito et al. (2017):
<http://www.mmi-basel.ch/extras/2017_Petralito.pdf>; Gutwin et al. (2016): <https://www.benlafreniere.ca/assets/papers/p5608-gutwin.pdf>;
Loewenstein (1994), doi 10.1037/0033-2909.116.1.75; To et al. (2016): <https://dl.digra.org/index.php/dl/article/view/793>;
<https://artificials.ch/lens-6-the-lens-of-curiosity/>; Compton: <https://www.tumblr.com/galaxykate0/139774965871/so-you-want-to-build-a-generator>;
Scheibehenne et al. (2010): <https://academic.oup.com/jcr/article-abstract/37/3/409/1827647>.
**Added from doc 36 (consolidation pass, 2026-09-27; fetch status per doc 36 Sources):** Goodfellow on the "interesting
decisions" quote (2008): <https://flashofsteel.com/index.php/2008/07/07/quote-misquote-cite/>; Johnson, "Turn-Based Versus
Real-Time" (2009): <https://www.gamedeveloper.com/game-platforms/analysis-turn-based-versus-real-time>, "Seven Deadly Sins":
<https://www.gamedeveloper.com/business/seven-deadly-sins-of-strategy-game-design>, "When choice is bad" (2013):
<https://www.gamedeveloper.com/design/when-choice-is-bad-finding-the-sweet-spot-for-player-agency>, "Water Finds a Crack" (2011):
<https://www.designer-notes.com/game-developer-column-17-water-finds-a-crack/>, "Theme is Not Meaning" (GDC 2010):
<https://gdcvault.com/play/1012750/Theme-is-Not>; Pardo via Leahy, Shacknews (2010): <https://www.shacknews.com/article/62807/sid-meier-and-rob-pardo>;
Przybylski et al. (2009), doi 10.1089/cpb.2009.0083; Ghibellini & Meier (2025): <https://www.nature.com/articles/s41599-025-05000-w>;
Kivetz, Urminsky & Zheng (2006), doi 10.1509/jmkr.43.1.39; Zagal, Björk & Lewis (2013):
<http://www.fdg2013.org/program/papers/paper06_zagal_etal.pdf>; Deterding, Stenros & Montola (2020): <https://eprints.whiterose.ac.uk/156460/>.

**Mil-sim and LLM narrative:** Hammar & Woodcock: <https://oro.open.ac.uk/68740/3/68740.pdf>;
<https://en.wikipedia.org/wiki/Tom_Clancy's_Rainbow_Six_(video_game)>; <https://en.wikipedia.org/wiki/Tom_Clancy%27s_Ghost_Recon_(2001_video_game)>;
<https://www.gamereactor.eu/squad-review/>; <https://ttp2.dslyecxi.com/leadership.html>; <https://ttp2.dslyecxi.com/communication.html>;
<https://stormbirds.blog/2024/05/09/community-qa-with-dcs-campaign-author-baltic-dragon/>;
<https://en.wikipedia.org/wiki/Operation_Flashpoint:_Red_River>; <https://www.gamingnexus.com/Article/3118/Operation-Flashpoint-Red-River/>;
<https://mmos.com/review/arma-3>; <https://gamedeveloper.com/pc/analysis-story-and-the-trouble-with-emergent-narratives>;
<https://arma3.com/news/arma-3-laws-of-war-dlc>; Tian et al.: <https://aclanthology.org/2024.emnlp-main.978/>; arXiv 2309.14556,
2409.14509, 2604.03136, 2402.01536, 2310.06452, 2510.01171, 2510.15061, 2511.04962, 2406.17744, 2209.12711, 2406.20094, 1904.09751,
2407.01082, 2410.04197, 2509.04239 (<https://arxiv.org/abs/ID>); Doshi & Hauser: <https://www.science.org/doi/10.1126/sciadv.adn5290>;
Wenger & Kenett: <https://academic.oup.com/pnasnexus/article/5/3/pgag042/8529001>;
<https://huggingface.co/blog/ChuckMcSneed/name-diversity-in-llms-experiment>;
<https://glaforge.dev/posts/2025/07/22/the-sci-fi-naming-problem-are-llms-less-creative-than-we-think/>;
<https://www.broadstreet.blog/p/history-llms-giving-the-past-a-voice>; Yao et al.: <https://ojs.aaai.org/index.php/AAAI/article/view/4726>;
<https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices>; Ghostwriter:
<https://www.gamedeveloper.com/marketing/here-are-more-details-on-ubisoft-s-narrative-ai-tools-from-gdc-2023>.

**Snippet-only, claims marked [U]:** BI community wiki (Main Characters, FAQ SinglePlayer), Operation Flashpoint Fandom, Armed Assault
Fandom (music), TV Tropes, a third-party repost of a mission readme. **Conflicts resolved:** the Ryan et al. page range is 344–360
per Crossref (one pass read 347–363 from a PDF); the full Next Generation sentence was re-fetched from Wikipedia on 2026-09-27
after one pass could not find its second clause.

## Verification notes

### Consolidation pass (2026-09-27)

Corrections from doc 36 (§3.2 Misattributions row 1; §5 "Doc 28 and the design-sensibility pack"), each checked against doc 36
before it was applied. No verified finding was deleted.

- **§4 interesting-decisions row (2026-09-27).** "Meier, GDC 1989 (revisited 2012)" replaced: the 2012 talk stays [V]; the
  origin of the "series of interesting decisions" line is now [U] (a GDC talk Meier recalls, year and wording unverified), and the
  1997 Usenet version is credited to Darren Reid. The TL;DR notes the unverified origin.
- **§4 research rows added (2026-09-27):** Johnson's turn-based calm, two levels, fun per time, "optimize the fun out" and "theme
  is not meaning"; Pardo's framing; Przybylski et al. 2009; Ovsiankina over Zeigarnik; the goal gradient; Zagal et al. 2013;
  Deterding et al. 2020. Tags follow doc 36; its [V-search] is read as [U] under this file's legend. Sources added.
- **§6.3 (2026-09-27):** MC30, MC31 and TX07 added as provisional doc 36 codes, with a note that MC20–MC29 belong to doc 34. The
  "31 new lints" count in the TL;DR is unchanged, because the three codes are doc 36's.
- **§7 (2026-09-27):** doc 36's rubric notes and lens candidates cv40–cv42 queued for pack v0.2 evaluation, not adopted.
- **Rename sweep (2026-09-27):** no "Field Manual", "Boot camp", "Bootcamp" or "Academy" references to our features, and no
  links to doc 33 or `skills/field-manual`, were found in this file; nothing to rename.
