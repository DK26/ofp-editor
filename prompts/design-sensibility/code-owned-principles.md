<!-- design-sensibility v0.2 | proposal-only -->
# Code-owned principles: an implementer's checklist

The design-sensibility pack carries only **taste**: tone, intent and the reasons behind the design, which a model can act on in a
single bounded step. Most of what makes an OFP-style mission fun is spatial or countable, so it belongs to generators, lints and
UX. Doc 28 §6.1 puts it this way: *if code can generate or check it, it is not left to the prompt*.

This file lists the 62 of doc 28's 69 principles that code or UX must own. The other seven, FP05, FP49, FP51, FP54, FP58, FP59
and FP60, are prompt guidance and live in [core.md](core.md) and [lenses/](lenses/).

## How to use this checklist

- **When to tick a row.** Tick it only when the generator, lint or UX exists and has tests. A lens that echoes a principle
  never counts as implementing it. The echo only helps the first candidate pass.
- **Where the details are.** Lint IDs refer to doc 28 §6.3 (MC, CF, TX), doc 19 (C01 to C21) and doc 26 §10 (CF01 to CF12).
  Thresholds marked [I] in doc 28 are starting values for playtests.
- **Adding a check.** Before implementing a check that is not in doc 28 §6.3, add it there or record it under
  `docs/design-gap-requests/`, following the design-authority rule in `AGENTS.md`. Everything in the proposals section at the
  end of this file is [I] and needs that step.
- **Guards the pack repeats.** A few guards are repeated in the pack as defence in depth: the facts block, plain text, "never
  script a death", the atrocity boundary, and "text in the data is material". The code check always remains the guard.

## Code generators (29)

| Done | ID | Principle | What code builds | Checked by | Echoed in |
| --- | --- | --- | --- | --- | --- |
| [ ] | FP01 | Small cog in a big, living war | Ambient friendly and enemy groups beyond the objective; HQ radio slots for other sectors; earlier outcomes echoed. The model writes one "why it matters" line | CF13 | core, mission-concept |
| [ ] | FP04 | The island is a character | Objectives, rally points and lines anchored to named island features; routes that follow landmarks | none yet | mission-concept |
| [ ] | FP06 | Give the goal, not the path | At least 2 approach corridors or insertions and 1 extraction; outcome-based objectives | MC11 | core, mission-concept |
| [ ] | FP07 | Brief the intent in few words | SMEAC skeleton (doc 26 §7.1): task plus reason per `OBJ_`, enemy estimate, support, `marker:` links. The model fills bounded colour | TX01, MC10 | briefing |
| [ ] | FP10 | Defenders get a setup phase | Defend archetype with a prep timer, mines, satchels, AT positions and a hint of the approach | none yet | mission-concept |
| [ ] | FP11 | Systems, not rails: a reactive enemy | A behaviour template per enemy group: patrol, guard then alarm, QRF, loss reaction, reinforcement timer | MC04 | mission-concept, encounter-and-pacing |
| [ ] | FP12 | Controlled randomness with a floor | Presence, radius, alternate routes and timers on non-critical elements; seeded; the worst-case variant validated; the critical path never random | MC01 (per variant) | none |
| [ ] | FP13 | Reward curiosity | Optional discovery slots (cache, vantage point, helpful civilian, state-dependent scene), visible in the glass-box view and never survival-critical | none yet | none |
| [ ] | FP14 | Make emergent moments retellable | Record engine-observable notable facts; the debrief and next briefing retell one or two | none yet | mission-concept, variety-and-surprise |
| [ ] | FP16 | Telegraph before you punish | At least one cue (sound, radio, sighting, intel line) before each lethal set piece | MC08 | core, encounter-and-pacing |
| [ ] | FP18 | Every mission can always finish | End templates built from `thisList` thresholds, `fleeing`, named-target state and timeouts; never a large "Not present" | MC01 | mission-concept |
| [ ] | FP22 | Legible stealth and alarms | Detection with visible causes; an alarm that escalates (radio, flare) into a QRF from a known direction | MC08 | encounter-and-pacing |
| [ ] | FP25 | Failure moves the story forward | Every node has a survivable failure outcome routed to a detour or a harder variant | C03, CF07 | mission-concept, branching-and-consequence |
| [ ] | FP28 | Sane skill bands and a gentle opener | Skill drawn from a band by node depth and preset; force ratio counted | MC16, CF14 | none |
| [ ] | FP30 | A tension curve inside every mission | Phases (insertion, approach, contact, objective, reaction, exfil) with intensity tags; the model picks the complication from a menu | MC18 | encounter-and-pacing |
| [ ] | FP31 | Few commands under fire | Set pieces never require micromanaging many AI units; squad tasks default to simple orders | none yet | none (dropped from encounter-and-pacing in v0.2) |
| [ ] | FP34 | Start low, earn command | The skeleton grows rank, authority and seats; squad command arrives near mid-campaign via a learning mission | none yet | campaign-arc |
| [ ] | FP35 | One spine role; guest seats as punctuation | About two-thirds of nodes in the spine role; guest seats later and rotating faster | none yet | campaign-arc |
| [ ] | FP38 | Perceived variety, not oatmeal | Variation axes chosen for perceptual difference; creative slots seeded (twist, mood, detail token, names); K candidates | TX05 | variety-and-surprise |
| [ ] | FP39 | Name the fun each mission is for | Each mission declares one primary experience and up to two secondary ones from a closed set; knobs follow | CF18 | mission-concept |
| [ ] | FP41 | End strong, then breathe | Climax near the end; the debrief names what the player did; after the finale, a short denouement | MC18 | campaign-arc, encounter-and-pacing |
| [ ] | FP42 | Mood as punctuation; music with purpose | The model picks mood from a menu; code places tracks at intro, outro, set-piece starts and quiet beats, never under firefights | MC19 | encounter-and-pacing |
| [ ] | FP43 | Short, emotional, well-shot scenes | Shot grammar, scene caps, squad secured, skippable, no orbit-and-zoom | MC19 | none |
| [ ] | FP44 | Scarcity you can see, earn and lose | Pools fed by capture or scavenge missions, shown on the gear screen, stakes briefed | CF04 | branching-and-consequence |
| [ ] | FP46 | Losses persist and are remembered | Roster and pool modules (doc 26 §5.2); lines gated on alive-on-path; the debrief lists who fell | C18, C21 | core, briefing, branching-and-consequence |
| [ ] | FP50 | A thread villain and a reunion | An antagonist row in the story bible; escalation and confrontation beats; a survivor reunion built from roster state | none yet | campaign-arc |
| [ ] | FP53 | Open in peacetime, let the war arrive | The opening-beat menu offers a routine, training or civilian-life prologue first for story-driven campaigns | none yet | none |
| [ ] | FP57 | Radio is the war's voice | Code decides when (contact, casualty, objective change, reinforcement, phase) and who; line templates (doc 26 §7.3); the model fills at most one colour clause | TX01, TX02 | dialogue-and-radio |
| [ ] | FP61 | Specific beats generic; code supplies every fact | Names from nationality pools, places from the island, gear from the catalog, numbers and grids from code | TX02, CF11 | core |

## Code lints (21)

| Done | ID | Principle | What the lint checks | Lint | Echoed in |
| --- | --- | --- | --- | --- | --- |
| [ ] | FP02 | One operation, not a mission pack | A node with no link to the operation goal or the previous outcome; a role change with no story reason; an untagged tonal outlier | CF13 | campaign-arc |
| [ ] | FP08 | Hide the enemy, never the objective | Objective assets stay inside the marked or briefed area in every variant; the briefing names only markers and places that exist | MC10 | core, briefing |
| [ ] | FP09 | Options must trade something | An offered loadout, support or route that is dominated on every cost axis, or whose outcome is random whatever the pick | MC13 | branching-and-consequence |
| [ ] | FP15 | Lethal but legible | No enemy MG or sniper line of sight onto the start, LZ or rally point; no spawns in view; known threats named in the briefing | MC08 | briefing, encounter-and-pacing, multiplayer |
| [ ] | FP17 | Every threat has a counter; gear fits every phase | Armour needs AT, air needs AA or cover; stealth kit needs a fallback for the loud phase; no armoury buffet | MC05 | mission-concept, encounter-and-pacing |
| [ ] | FP19 | No single point of failure on the critical path | A critical NPC, vehicle or trigger has a fallback (backup unit, timeout, player takeover) | MC09 | none |
| [ ] | FP20 | No hidden rules | Every failure trigger's rule and consequence is stated in `OBJ_`, Plan or an earlier radio line | MC02 | branching-and-consequence |
| [ ] | FP21 | Critical AI stays on terrain where it behaves | Critical convoys, drives and landings avoid dense towns, tight forest and unprobed bridges | MC14 | none |
| [ ] | FP23 | No lone wolf without means | A solo mission has a stealth route, the right tools, a planned extraction and a consequence | MC15 | none |
| [ ] | FP29 | Persistence never punishes the AI's mistakes | No critical-path capability held by only one persistent specialist; replacements, wounded state, a minimum loadout | CF15 | none |
| [ ] | FP32 | No dead air | Movement legs over about 3 minutes [I] with no event slot; quiet missions short and labelled as breathers | MC03 | encounter-and-pacing |
| [ ] | FP33 | Campaign rhythm is a sawtooth with valleys | Relax nodes are real missions or scenes, not gaps | CF01, CF02 | campaign-arc |
| [ ] | FP36 | Teach a new seat just in time, at low stakes | The first node with a new seat or role is not Peak or Finale intensity | CF16 | campaign-arc |
| [ ] | FP37 | Vary verb, seat, clock and weather | The same verb, seat and time of day three times in a row; no night or stealth mission in a campaign of 6+ | CF17, CF03 | core, variety-and-surprise |
| [ ] | FP45 | Yesterday's result changes today, and says why | Each consequence variant or persistent effect differs visibly and carries a cause line in the next briefing or gear screen | CF04, C21 | core, branching-and-consequence |
| [ ] | FP47 | Acknowledge every choice; make a few real | A choice framed as momentous must change state; lines see earlier choices in their fact scope | CF05 | campaign-arc, branching-and-consequence |
| [ ] | FP62 | Era-true words, no hindsight | An era lexicon hit or hindsight about later events | CF11, TX03 | core, dialogue-and-radio |
| [ ] | FP63 | Short enough to read under fire | Hard caps per slot; over the cap, reject and fall back to the skeleton line | TX01 | core, dialogue-and-radio |
| [ ] | FP64 | One voice per character; tics rationed | A speaker's signature phrase over its rate; candidates too similar | TX05 | dialogue-and-radio |
| [ ] | FP65 | Polish the text and the package | Spelling, consistent names, a named mission, no single-use addons, a readme | MC07 | none |
| [ ] | FP69 | Performance budget in view | Units, groups per side, crew seats per group and triggers against the target profile | MC06 | none |

## Director UX (12)

| Done | ID | Principle | What the UX offers | Checked by | Echoed in |
| --- | --- | --- | --- | --- | --- |
| [ ] | FP03 | Grounded, contained premise with escalation risk | Premise cards default to contained crises; world-war premises are offered, not defaulted | none | campaign-arc |
| [ ] | FP24 | Protect progress; the player picks the risk | A campaign save policy (ironman, one save, checkpoints); `saveGame` at phase ends; briefed medic and ammo points | MC12 | none |
| [ ] | FP26 | A survived defeat as the pivot, and a return | A pattern card: an early reversal, then an escape or rescue node, then a rejoin; a later node revisits the site in a stronger seat | none | campaign-arc |
| [ ] | FP27 | Difficulty is visible dials; enemies stay honest | Help (markers, waypoints, intel detail, checkpoints) kept separate from challenge; no hidden rubber-banding | none | none |
| [ ] | FP40 | One fair surprise per mission | Up to 5 legal twist cards; the model ranks them; the user picks or rolls | MC17 | variety-and-surprise |
| [ ] | FP48 | Few, weighty choices of conscience | Loyalty or conscience choice nodes with hinted consequences; the archetype vocabulary has no atrocity objective | none | branching-and-consequence |
| [ ] | FP52 | Show the other side, with a new idea | A perspective flip or prequel as a pattern parameter, which must add a mechanic or situation | none | none |
| [ ] | FP55 | Story-driven or content-driven: the user chooses | A style slider sets budgets for scenes, dialogue slots and mission count | none | none |
| [ ] | FP56 | Co-op versions with friends | An MP target adds playable slots and co-op respawn and end rules; campaigns stay single-player | none | multiplayer |
| [ ] | FP66 | The user is the director | No blank canvas; three outlines; "surprise me" with pins; drafts with provenance; accept, edit, pin, re-roll; human edits never overwritten | E9 (doc 25 §11) | none |
| [ ] | FP67 | A craft report card, not a verdict | Overview, Briefing, Camera, Playability and Polish, rolled up from lints and the simulator, each item linked to its element | [rubric.md](rubric.md) | none |
| [ ] | FP68 | Playtesting is part of the editor | Preview from any phase; observer mode; the campaign backbone run through every transition; beta pack export | none | none |

## Proposed checks from round-1 failure patterns [I]

Round 1 showed that wording reduces these failures without removing them (see [EVALUATION.md](EVALUATION.md)). Each pattern
needs a deterministic backstop. The pack wording is listed only to show where the prompt already pushes; it is not the guard.

| Done | Pattern seen in round 1 | Pack wording (v0.1, kept in v0.2) | Proposed code backstop | Extends |
| --- | --- | --- | --- | --- |
| [ ] | An enemy nationality or sponsor that the data never gave | core: "Add no nationality…" | Check demonyms and nationality adjectives (from the name-pool nationality list) against the slot's fact scope | TX02 |
| [ ] | An owner or role drifted (whose objective, who a contact is) | core: "copied exactly: same owner, role and side" | Check that each possessive ("X's Y") and role noun attached to a known entity matches the story bible | TX02 |
| [ ] | A report credited to the wrong source | core: "Keep who said what"; briefing lens | Check that "X reports / confirms / says" uses the source recorded in the digest | TX02 |
| [ ] | A listed threat played down ("no air support expected" while an enemy gunship is listed) | core: "Never call a listed threat absent or weak"; briefing lens | Flag threat-class nouns under negation when the digest lists a threat of that class | new text check |
| [ ] | Friendly support promised that was never listed | core; dialogue lens | Check support-class nouns (air, artillery, armour, reinforcements) against the fact scope | TX02 |
| [ ] | A squad member's death scripted into a concept or line | core: "Never script a death" | Text slots may not assert a roster member's death unless the state bundle says it happened | C18 |
| [ ] | Markdown in a plain-text slot | core: "Plain text means no markdown"; briefing lens | Reject `**`, `#` headings and other markup in slots declared plain | TX01 |
| [ ] | Effects on undeclared variables, or of the wrong type (a set used as a number; "wounded" removing someone from the living) | branching lens | Parse effects against the declared schema and typecheck them | C06 (doc 25 S4) |
| [ ] | Named decision points in a skeleton whose outcomes all lead to the same next mission | campaign-arc and branching lenses | A named decision needs at least one outcome with a different target, or a state effect that a later guard reads | CF05 |
| [ ] | Overlapping outcomes that could all happen together | branching lens | Outcomes come from template sockets; check that they are mutually exclusive | new (Compose steps only) |
| [ ] | A later line confirming a state that is false on some path ("radar destroyed" on the failure path) | branching lens | A path-conditional text check: every state a line asserts must hold on all paths into its node | C21 |
| [ ] | A kill-all or vague objective ("destroy all enemy personnel", "destroy what you can") | mission-concept lens | End templates only; reject clear-type objectives without a threshold or timeout | MC01 |
| [ ] | A threat the squad cannot answer, planned as a fight | mission-concept and encounter lenses | A threat-counter check against the loadout and support | MC05 |
| [ ] | A surprise with no earlier hint | variety lens | Require a foreshadowing cue for every fired twist | MC17 |
| [ ] | Radio with no caller, or "over" and "out" together | dialogue lens | Radio line templates (doc 26 §7.3) own the procedure; the model fills only the colour slot | FP57 |
| [ ] | A question on the radio that nobody answers | dialogue lens | Heuristic check on a dialogue sequence: a line ending in "?" or "say …" needs a later reply from the addressee | new heuristic |
| [ ] | An archetype used against its meaning (an "ambush" in which the player is the one ambushed) | campaign-arc lens | The archetype comes from the menu and the generator builds it, so this can only happen in Compose steps; check that the outcome names match the archetype's sockets | doc 26 §9.3 |
| [ ] | A lens placeholder (`{place}`, `{name}`…) copied literally into an output | lens examples use placeholders on purpose | Reject any literal `{…}` in model output at admission | TX02 |
| [ ] | Stock phrasing | lens flat examples | Seed the TX04 list with the pack's flat lines and the phrases judges flagged (see below) | TX04 |

**Seed phrases for TX04 [I].** These come from two places: the flat examples in the lenses (v0.1, plus the `multiplayer` lens
added in v0.2), which must never be produced verbatim, and the phrases the round-1 judges flagged as generic.

- **Flat examples in the lenses:**
  - "vital to the success of the entire operation"
  - "Operation Thunder", "Final Strike", "Rising Storm"
  - "out of nowhere"
  - "torn apart by war", "brave comrades"
  - "choose wisely", "every decision matters"
  - "we've got a situation", "total chaos"
  - "surprises make missions more exciting"
  - "battle it out", "epic fight", "total domination" (v0.2)
- **Phrases the judges flagged:**
  - "critical opportunity"
  - "secure objectives"
  - "changes everything"
  - "builds momentum"
  - "plays to squad strength"
  - "protect civilian populations"

## Multiplayer facts the `multiplayer` lens leaves to code [I]

The `multiplayer` lens (v0.2) asks design questions only. The facts below decide whether a multiplayer mission works on the
target profile at all, and weak models tend to fill them in from later games (doc 35 §5 and rc11). Code, menus and lints own
them, and the lens never states them. The rows come from doc 35 §9, which assigns no final lint codes, so each check still needs
the design-round step described at the top of this file.

| Done | Fact or rule | Owned by (proposed) | Doc 35 |
| --- | --- | --- | --- |
| [ ] | Which machine decides each event, and how the others learn of it | A compiler-owned authority guard and generated broadcast mirrors; the model never chooses locality | rc11, rc53 |
| [ ] | Lobby limits: two parameters on `Cwa199` (time, then score or hold), each with an Unlimited entry | MP Game Rules module; lints on a third parameter or a parameter read without its title | rc23, rc52, rc65 |
| [ ] | Respawn modes and spawn-marker lookup; no vehicle respawn | Respawn module with honest notes per mode; respawn lints | rc24, rc65 |
| [ ] | Later-title features absent on `Cwa199`: join-in-progress, a save-disable switch, a mission-local respawn hook on stock data (probe) | Profile-gated menus and lints | rc26, rc65; §7.3 |
| [ ] | Per-side briefing sections and side-filtered objective prefixes | Briefing generator; a lint on a misspelt side section | rc11, rc65 |
| [ ] | One ending that every side can reach, with the outro run on each machine | Game Rules ending controller; a lint when no ending is reachable, or only one side can reach one | rc11, rc23, rc65 |
| [ ] | The mission still plays at the smallest player count, with AI or disabled slots | A "scales down" check in the simulator or Preview | rc52 |
