<!-- design-sensibility v0.2 | proposal-only -->
# Evaluating the design-sensibility pack

This file covers how pack versions are compared, what round 1 found and what the next round must do. The rubric is in
[rubric.md](rubric.md). The wider evaluation plan for the harness is doc 25 §11.

**Status:** round 1 compared four candidate prompt drafts. Nobody has evaluated v0.1 itself yet. It merges the round-1 winner with
fixes for the failures the judges found, and those fixes are untested [I]. (The confirmation round below later ran v0.1 once,
informally.) v0.2 has not been run at all; see [v0.2 changes (unevaluated)](#v02-changes-unevaluated) at the end of this file.

## 1. Method (round 1)

| Item | Round 1 |
| --- | --- |
| Generator | A weak-model proxy: a small model standing in for the 3 to 9B tiers. Its exact identity, sampler and seeds are not recorded in this file [U]. |
| Conditions | 4 (see §2). Each draft condition sent that draft's core plus the lens for the task's step. |
| Tasks | 5 (see §3), all on one synthetic scenario |
| Samples | 1 output per condition per task (20 outputs in all) |
| Judges | 2 blind LLM judges per task. Each judge saw the four outputs relabelled A to D in its own order, together with the task input and the rubric dimensions R1 to R8. |
| Scoring | One holistic score from 1 to 10 per output, with reasons citing R1 to R8. The `format_ok` and `facts_ok` gates cap the score at 4 when they fail. |

**Scenario.** The scenario is a synthetic fixture authored for this project; it contains no game data. A coup has split the
army of a fictional island. The player leads a four-man squad with permanent death: a machine-gunner, a medic and a rifleman who
jokes, the rifleman wounded after mission 2. The cast also has an HQ callsign and a partisan contact who is a schoolteacher.

- **Places:** a port, a lighthouse, a village, a forest road bend, a hill crossroads, a mountain radar station and an airfield.
- **The coup army:** light patrol vehicles, BMP-1s, a T-72 section and one Mi-24 gunship at the airfield.
- **Persistent state:**
  - `partisan_trust`: an integer from -3 to 3
  - `squad_alive`: a set of names
  - `radar_destroyed` and `mortar_captured`: booleans

## 2. Conditions

| Condition | Idea |
| --- | --- |
| `baseline` | No pack: the step prompt only. |
| `compact-creed` | Short imperative rules with Yes/No example pairs and no persona. The core carries the register, a "when you choose, prefer" ranking list and a facts reminder. |
| `veteran-designer` | A persona: a seasoned mission designer and former staff officer. It gives craft wisdom with reasons, closes on silent self-check questions, and does not name the game. |
| `lens-questions` | The core states the player experience (tension, agency, consequence, variety, clarity, war stories) and the house voice. Each lens is a checklist of design questions ending in one good-versus-flat example and "borrow the difference, not the words". |

The three drafts are not stored in this repository. v0.1 ([core.md](core.md), [lenses/](lenses/)) is the merged result.

## 3. Tasks

The exact task prompts are not stored in this file. This table rebuilds them from the outputs and the judges' notes [I].

| Task | Step shape | What the step gave and asked for | Lens (presumed) |
| --- | --- | --- | --- |
| T1 pick-next | Pick | Choose mission 3 of 6 from a menu: a night raid on the radar, an ambush at the road bend, a downed-pilot rescue that brings in the gunship, and other options that are not visible in the outputs [U]. The history: a recon mission, then a village defence that earned partisan trust; the rifleman is wounded. Answer as JSON `{pick, why}`. | campaign-arc |
| T2 mission-concept | Compose | A concept for the road-bend convoy ambush, as JSON: title (capped at 6 words), hook, objective, complication, 4 beats, interesting failure, memorable moment. | mission-concept |
| T3 briefing | Fill (plain text) | Four plain-text sections (Situation, Mission, Execution, Notes) under a word cap. The facts given: two trucks and a BMP-1 escort due at a grid and time; the start grid 400 m away; mortar ammunition meant for an attack on the village; the contact reported the cargo; a secondary objective (the convoy commander's map case); the gunship at the airfield. | briefing |
| T4 radio | Fill | 6 to 8 lines of JSON `{speaker, channel: radio or voice, line}` for the moment of contact, each line capped at 14 words. | dialogue-and-radio |
| T5 skeleton | Compose | A 6-mission skeleton: archetypes from a list, places from a list, up to 7 outcomes per mission with effects on the declared variables, and 2 decision points. | campaign-arc |

Which lens each draft loaded for each task is not recorded here [U]. The last column is the natural routing from the README.

## 4. Results

### 4.1 Round-1 table, as reported

| Condition | Avg (1 to 10) | `format_ok` | `facts_ok` |
| --- | --- | --- | --- |
| `?` (T1 scores whose condition labels were lost) | 6.75 | 8/8 | 8/8 |
| `lens-questions` | **5.75** | 8/8 | 5/8 |
| `compact-creed` | 4.75 | 8/8 | 4/8 |
| `baseline` | 4.06 | 6/8 | 4/8 |
| `veteran-designer` | 3.31 | 6/8 | 2/8 |

The four named rows each average 8 scores: tasks T2 to T5, times 2 judges. All 8 T1 scores came back without their condition
labels, so they form the `?` row.

**Correction (2026-09-27).** The `?` row was a bookkeeping bug in the evaluation script: the T1 judges labelled candidates
"Candidate A" instead of "A", so the script could not map them back to conditions. The candidate order was deterministic
(a fixed rotation per task and judge), so all 40 round-1 scores were re-attributed mechanically from the run's journal. The
full, correct round-1 result is:

| Condition | Avg (1 to 10), n = 10 | `format_ok` | `facts_ok` |
| --- | --- | --- | --- |
| `lens-questions` | **6.10** | 10/10 | 7/10 |
| `compact-creed` | 5.20 | 10/10 | 6/10 |
| `baseline` | 4.60 | 8/10 | 6/10 |
| `veteran-designer` | 3.80 | 8/10 | 4/10 |

This matches the §4.2 "Avg T1 to T5" column, which was rebuilt independently from the judges' descriptions.

### 4.2 Per task (mean of the 2 judges)

The T1 column is rebuilt by matching each judge's description of a candidate to the outputs; the matches are unambiguous [I].

| Condition | T1 [I] | T2 | T3 | T4 | T5 | Avg T2 to T5 | Avg T1 to T5 [I] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `lens-questions` | 7.5 | **8.0** | **3.75** | 7.0 | **4.25** | **5.75** | **6.1** |
| `compact-creed` | 7.0 | 7.0 | 2.0 | **8.0** | 2.0 | 4.75 | 5.2 |
| `baseline` | 6.75 | 4.75 | 2.5 | 5.0 | 4.0 | 4.06 | 4.6 |
| `veteran-designer` | 5.75 | 4.0 | 3.5 | 2.5 | 3.25 | 3.31 | 3.8 |

- **The order holds.** It is the same with or without T1.
- **Where each draft led.** `lens-questions` scored highest on four of the five tasks. `compact-creed` won the radio task.
- **The hardest task.** T3, the briefing, was the hardest for every condition: every output failed at least one gate with at
  least one judge.

### 4.3 Gate failures

| Condition | `format_ok` fails | `facts_ok` fails (judge count) |
| --- | --- | --- |
| `lens-questions` | none | T3 ×2 (changed the secondary target's owner); T5 ×1 (invented partisan tanks) |
| `compact-creed` | none | T3 ×2 ("no air support expected" despite the listed gunship, plus several invented details); T5 ×2 (invented foreign forces) |
| `baseline` | T3 ×2 (Markdown bold) | T3 ×2 (said the coup controls the island, when the army is split; misattributed the report); T5 ×2 (invented foreign forces; the contact promoted to leader) |
| `veteran-designer` | T3 ×2 (Markdown bold) | T2 ×2 (foreign voices on the enemy radio; an invented direction); T3 ×1 (misattributed source, invented order); T4 ×2 (friendly air support and a SAM invented); T5 ×1 (invented details; a set variable used as a number) |

### 4.4 Judge agreement

- **Scores.** The mean absolute difference between the two judges on the same output was 0.6 points out of 10, over 20 pairs.
  The largest gap was 2 points (`compact-creed`, T1).
- **Rankings.** The two judges agreed on the top-ranked output for T2 and T4. They split on T1, T3 and T5, where the top two
  outputs were within 1 point of each other.
- **Gates.** The judges disagreed on `facts_ok` for 3 of 20 outputs (`veteran-designer` T3 and T5, `lens-questions` T5). They
  never disagreed on `format_ok`. The rubric now settles one of those splits: misusing a variable's type fails `format_ok`.

## 5. Notable judged examples (brief)

- **T1: grounded reasons win.** The top `why` ("…using M1 recon intel. Grounded ambush fits wounded squad.") tied the pick to
  earlier results and to the squad's state. Generic reasons ("plays to squad strength", "builds momentum") scored lower even when
  the pick was the same.
- **T2: agency and anticipation.** `lens-questions` scored 8 from both judges:
  - Its complication offered a real decision ("spring the trap early or wait for both").
  - Its beats built anticipation ("The road is quiet. Wait.").
  - It avoided nationality with "radio chatter you don't understand".
  - It lost points for a vague objective ("destroy what you can") and no named way out.

  `compact-creed` had the clearest objective, with a named exfil, a telegraphed armour timer and an understated moment. `baseline`
  scripted a permanent death ("One squad member falls here") and let allies rescue the squad. `veteran-designer` put "Russian
  voices" on the radio when the enemy is the island's own army, and paired a kill-all objective with a humane rescue scene that
  contradicts it.
- **T3: each draft failed a different way.** No draft passed both gates with both judges:
  - `lens-questions` handed the secondary map case to the wrong vehicle's commander.
  - `compact-creed` wrote "No air support expected" while a gunship was listed, and added armour ratings, distances and a new
    task.
  - `veteran-designer` wrote the tersest content ("Priority is the trucks") but used Markdown bold in a plain-text slot.
- **T4: procedure and consistency.** `compact-creed` won on procedure ("Viper One, Castle. Say status, over.") and on distinct
  voices. `baseline` had a medic report "All clear so far" in the middle of an ambush and a squad shout sent on the radio
  channel. `veteran-designer` promised friendly air support that did not exist.
- **T5: structure.** Most skeletons were linear: every outcome led to the next mission, so the decision points were hollow.
  - The richest branch wiring came from `baseline`: a captured contact leads to the rescue mission, and a withdrawal skips
    ahead. But `baseline` also invented foreign troops and treated "wounded" as dead.
  - `lens-questions` had the best arc shape, with a setback before the recovery, but it confirmed the radar destroyed even on the
    path where the raid failed.

## 6. What v0.1 changes in response

| Round-1 failure | v0.1 wording | Code backstop |
| --- | --- | --- |
| Added nationality, direction, support or task | core: "Add no nationality, direction, weapon, vehicle, support or task…" | TX02 extensions (see [code-owned-principles.md](code-owned-principles.md)) |
| Owner, role or source drift | core: "copied exactly: same owner, role and side"; "Keep who said what"; briefing lens | TX02 entity-attribute and source checks [I] |
| Listed threat softened | core: "Never call a listed threat absent or weak"; briefing lens: "Do not reassure." | Negated-threat check [I] |
| Markdown in a plain-text slot | core: "Plain text means no markdown"; briefing lens | Plain-slot format verifier |
| Scripted death | core: "Never script a death. Losses come from play."; mission-concept lens | C18 extension [I] |
| Vague or kill-all objective; no exit | mission-concept lens: a checkable end state, a named way out | MC01 |
| A threat the squad cannot answer | mission-concept and encounter lenses | MC05 |
| Allies winning the fight | encounter and branching lenses | none (taste) |
| Hollow decisions, overlapping outcomes, untyped effects, path contradictions | campaign-arc and branching lenses | CF05, C06, C21, an exclusivity check [I] |
| Radio procedure, unanswered questions, wrong channel | dialogue lens | Radio templates (doc 26 §7.3) |
| Generic `why` | core: "Fill any "why" field first, naming a fact from the step." | Judge check; no lint |
| Unforeshadowed surprise | variety lens | MC17 |

## 7. Limitations

- **The generator was a proxy.** It was not a qualified T1 or T2 model, and results may not transfer to the 3 to 4B and 8 to 9B
  tiers the harness targets (doc 25 §11.2).
- **The sample was tiny.** Round 1 had one sample per cell, five tasks and one scenario. A one-point gap between conditions
  (`lens-questions` 5.75 against `compact-creed` 4.75) is suggestive, not significant, and sampling noise alone could move a
  single output by that much [I].
- **The judges were LLMs.** They have not been validated against human playtesters (doc 28 open question 5). Doc 25 §11.2 treats
  LLM judges as a cheap pre-screen only. The judges also disagreed on 3 of 20 fact gates.
- **The score scale compresses differences.** The gates cap any failing output at 4, so the averages mostly track the gate
  rates. A version that fixes the facts could look much better without any change in taste.
- **Some data was lost.** T1's condition labels were lost, and the T1 column is a reconstruction [I]. The exact task prompts
  and which lens each task loaded are not recorded [U].
- **Several things went unmeasured.**
  - R9 (respect for time)
  - token counts
  - latency
  - whether the good-versus-flat examples were copied. One `lens-questions` output wrote "Diesel engines far off, then closer",
    which is close to the encounter lens example. Whether that lens was loaded for T2 is [U].
- **v0.1 is unevaluated.** It merges three drafts, and the grafts may interact: more rules may crowd out taste on small models.

## 8. Round 2 (required before v0.1 leaves proposal-only)

- **Conditions:**
  - `baseline`
  - the round-1 `lens-questions` draft, stored with the eval fixtures so that it can be rerun
  - v0.1
  - two ablations: v0.1 without the good-versus-flat pairs, and v0.1 core-only with no lens
- **Scenarios:** the round-1 scenario plus at least two new synthetic scenarios that were not used while writing v0.1. Vary
  the side, the year, the terrain and the squad size.
- **Models:** the proxy plus at least one real T1 model (3 to 4B) and one T2 model (8 to 9B). Record weights hash,
  quantisation, chat template, sampler and runtime (doc 25 §11.2).
- **Samples:** at least 5 seeds per cell. Report pass^k for the gates (doc 25 §11.2).
- **Judging:** two blind LLM judges using [rubric.md](rubric.md).
  - Record the R vector as well as the holistic score.
  - Have a human spot-check 10 to 20% of the items, including every gate disagreement.
- **Deterministic metrics,** as soon as the checks exist:
  - fact-scope violations per 100 words
  - Markdown in plain slots
  - `{placeholder}` leaks
  - verbatim copies of lens examples
  - TX04 stock-phrase hits
  - TX05 cross-sample similarity
  - `none fit` honesty on planted cases (doc 25 E4)
- **Adoption rule:** v0.1 becomes `evaluated` only if all of these hold on the held-out scenarios:
  - its `facts_ok` and `format_ok` rates are at least those of `lens-questions` (round 1)
  - its mean score is higher by more than the judges' disagreement on the same items
  - no task drops by 2 or more

## Confirmation round

This round compared the final pack with `baseline` on the same five tasks as round 1. It used a fresh run of the weak-model
proxy and one blind judge per task. The final pack is v0.1 as stored in this directory: every file carried the v0.1 header at
the time [I]. This is the first evaluation of v0.1 itself, so the status line at the top of this file and "v0.1 is unevaluated"
in §7 predate it. It is not the round 2 that §8 requires, and v0.1 stays `proposal-only`.

### Method

| Item | Confirmation round |
| --- | --- |
| Generator | A fresh run of the weak-model proxy. Its identity, sampler and seeds are not recorded, and neither is whether it was the round-1 proxy [U]. |
| Conditions | 2: `baseline` (the step prompt only) and `final` (v0.1). Which lens each `final` task loaded is not recorded [U]. |
| Tasks | The same 5 tasks on the same synthetic scenario as round 1 (§1, §3) |
| Samples | 1 output per condition per task (10 outputs in all) |
| Judges | 1 blind LLM judge per task. It saw the two outputs as A and B, together with the task input and R1 to R8. `final` was B on T1, T3 and T5 and A on T2 and T4, so the label did not track the condition. |
| Scoring | As in round 1: one holistic score from 1 to 10, capped at 4 when `format_ok` or `facts_ok` fails |

### Results

| Condition | Avg T1 to T5 (n = 5) | Avg T2 to T5 | `format_ok` | `facts_ok` | Both gates |
| --- | --- | --- | --- | --- | --- |
| `final` | **5.0** | 4.25 | 4/5 | 3/5 | 2/5 |
| `baseline` | 4.5 | **4.63** | 4/5 | 3/5 | 2/5 |

| Task | `baseline` | `final` | Final minus baseline | Gate failures |
| --- | --- | --- | --- | --- |
| T1 pick-next | 4 | **8** | +4 | `baseline` `format_ok`: the JSON was wrapped in a code fence |
| T2 mission-concept | **6** | 4 | -2 | `final` `format_ok`: two of the four beats ran over the 20-word cap |
| T3 briefing | **6** | 4 | -2 | `final` `facts_ok`: it invented the convoy's direction, "no air support available", a timescale, "limited sightlines" and a verdict on the contact's route |
| T4 radio | 3.5 | **5** | +1.5 | `baseline` `facts_ok`: HQ promised friendly close air support that the forces do not list |
| T5 skeleton | 3 | **4** | +1 | Both `facts_ok`. `baseline` added foreign forces and an enemy HQ. `final` added friendly assets (ships, a relief column, flights) and more helicopters than the one gunship. |

### Did the final pack beat the baseline?

- **Overall: narrowly, and not convincingly.** `final` averaged 5.0 against 4.5 and won three of the five tasks. The 0.5-point
  lead is smaller than the 0.6-point mean gap between two judges on the same output in round 1 (§4.4), and all of it comes from
  T1. On T2 to T5, the tasks behind the round-1 main table, `final` averaged 4.25 against 4.63 and lost.
- **T1: `final` won, 8 to 4.** The gap is the format cap. The judge found the baseline's reasoning stronger on persistence,
  because it weighed the wounded rifleman. The final `why` named facts from the step (the place and the partisan-trust gain), as
  core.md asks, and came as bare JSON.
- **T2: `baseline` won, 6 to 4.** `final` broke the word cap. On taste it had more agency (the partisans flank, and the player
  chooses to hold or extract), but its lethality was unfair: a BMP-1 against a rifle squad with no listed anti-tank weapon, and
  the gunship "one minute out". It also had no release beat, and two beats contradicted each other. The baseline paced better
  and telegraphed the gunship, but it offered only one path.
- **T3: `baseline` won, 6 to 4.** `final` had the better structure and voice: a clear primary and secondary objective, a terse
  period register, the HQ callsign and the contact used naturally, and a warning that the BMP-1 will fight. But its fact errors
  fall in exactly the categories core.md forbids ("Add no … direction, weapon, vehicle, support or task"). The baseline was
  accurate but flat and generic.
- **T4: `final` won, 5 to 3.5.** The baseline invented friendly air support, the same failure `veteran-designer` showed in
  round 1, and it set the ambush at the mountain radar station. `final` invented nothing but was generic: "return fire" three
  times, and the joker and the medic sounded like everyone else.
- **T5: `final` won, 4 to 3, with both capped.** The judge called `final` "clearly the more fun skeleton". It named the squad
  and the contact, gave deaths stated causes, brought the airfield's gunship back at the radar station in mission 4, and read
  the earlier state in the last mission. But it invented friendly assets, let `partisan_trust` reach -4 against the declared
  range of -3 to 3, let the machine-gunner die twice and put gating conditions in `effects` fields. The baseline left the
  casualties nameless, set variables that nothing read and sent every outcome to the next mission.

### What this round suggests

- **Gates decided every task.** On no task did both outputs pass both gates. In four tasks the winner was the output that did
  not trip a gate, and in T5 both tripped. Six of the ten outputs were capped at 4 or lower. The scores mostly record which
  single sample slipped, as §7 warned, and say little about taste [I].
- **Where the judge wrote about taste, the pack mostly helped.** `final` led on grounded reasons (T1), agency (T2), structure
  and voice (T3), and people and consequence (T5). `baseline` led on pacing and fair lethality (T2) and on weighing the wounded
  rifleman (T1). This rests on one judge's prose about one sample per cell [I].
- **The v0.1 fact rules did not hold on their own.** `final` failed `facts_ok` twice, on the same kinds of addition round 1
  found: a direction, a support statement, friendly assets and a changed unit count. core.md names each of them. The code
  backstops in §6 (the TX02 extensions and the negated-threat check) remain necessary [I].
- **Caps and bare JSON are cheap to check in code.** The only format failures were a code fence (`baseline` T1) and word counts
  (`final` T2). In the harness, a verifier and a bounded repair loop would catch these before the user sees them (doc 25). A
  fairer round would run those deterministic checks and one repair pass before judging, and report gate rates before and after
  the repair [I].
- **No sign that v0.1 improves on the round-1 winner.** `final` scored 4.25 on T2 to T5, below the 5.75 that `lens-questions`
  scored in round 1. The runs, judge counts and samples differ, so this comparison is weak, but it fits the §7 worry that more
  rules may crowd out taste on small models [I].

### Against the §8 adoption rule

The round cannot apply the rule: its scenario is not held out, it had one judge and one sample, and `lens-questions` was not
rerun. Read informally, it would fail all three conditions:

- **Gate rates.** `final` passed `format_ok` on 4/5 (80%) and `facts_ok` on 3/5 (60%). `lens-questions` passed 8/8 (100%) and
  5/8 (62.5%) in round 1.
- **Margin.** The lead over `baseline` was 0.5. That is below round 1's 0.6-point judge disagreement, and this round measured
  no disagreement of its own.
- **Drops.** T2 and T3 each fell 2 points against `baseline`.

### Limitations

- **A single run.** There was one sample per condition per task, 10 outputs and one scenario. The scenario is the round-1 one,
  which was in view while v0.1 was written, so it is not held out. One more sample could reverse any task [I].
- **LLM judges, one per task.** No agreement between judges was measured. The judges have not been validated against human
  players (doc 28 open question 5), and doc 25 §11.2 treats them as a cheap pre-screen only. Calls also varied between tasks:
  calling the coup's forces Soviet was docked but not capped on T2 (`baseline`), yet it helped cap `baseline` on T5.
- **A proxy model.** The generator was not a qualified T1 (3 to 4B) or T2 (8 to 9B) model, and results may not transfer to
  those tiers (doc 25 §11.2).
- **Two conditions only.** There was no `lens-questions` rerun and no ablation, so the round cannot say which part of v0.1
  helped or hurt.
- **Not recorded.**
  - the lens each `final` task loaded [U]
  - full R vectors; the reasons give only a few R scores in prose
  - R9 (respect for time), token counts and latency
  - whether any lens example was copied

## v0.2 changes (unevaluated)

**Status.** v0.2 is `proposal-only`, and nothing has been run on it: no generation, no judging and no deterministic checks. No
result in this file measures v0.2. The round-1 and confirmation results describe the drafts and v0.1, and do not transfer to
v0.2 [I]. **v0.2 needs its own evaluation run** before it can become `evaluated`.

The only measurement so far is size [V]: counted by the README rule, the core is 348 words and the eight lenses are 214 to 220
words each, all within their caps.

### What changed

The full list is the v0.2 entry in the [README changelog](README.md#changelog). The rows cite doc 35 §9.

| Change | Doc 35 | What the evaluation should watch |
| --- | --- | --- |
| New `multiplayer` lens | rc01 (§5, §7.2) | Features pulled in from later games that the target profile lacks, such as join-in-progress, revive or a third lobby parameter; rules that no longer fit in one sentence |
| Core framed for missions, campaigns and several players | rc01 | No change in the single-player scores on T1 to T5 |
| `briefing`: each threat comes with an answer from the step's gear or orders; the situation may speak in a listed person's voice | rc02 | `facts_ok` on T3, which was already the hardest task: invented counters, timings, people or events |
| `encounter-and-pacing`: responses in audible waves; the world's clock; deadlines announced more than once | rc03 | Invented timers, deadlines or reinforcements in Compose outputs such as T2 |
| `campaign-arc`: new seats and chapters start quietly; a small covert job shapes the next big fight | rc03, rc22, rc79 | T5: whether the shaping link is a state effect that a later mission reads, not just an assertion |
| `variety-and-surprise`, `dialogue-and-radio`, `branching-and-consequence` and `mission-concept` refinements | rc04, rc05, rc06, rc45 | T4: an HQ invented on the radio. T2 and T5: whether a survivable failure is present and wired to a distinct outcome |
| Wording compressed to fit the caps | none | Regressions on the round-1 patterns in §6, especially hollow decisions now that "If not, it is no decision." is gone |

### What its own run must include

- **Design.** The §8 round-2 design, with v0.2 as the candidate, v0.1 as the current version and `baseline`. Keep §8's
  models, seeds, judges and deterministic metrics.
- **Regression tasks.** The five round-1 tasks, plus the held-out scenarios §8 requires.
- **Multiplayer tasks.** At least two new tasks on a new synthetic scenario, written without reading the lens:
  - a co-op Pick, such as mode, respawn preset and limits from a menu
  - a competitive Compose, such as a rules sentence, limits, spawns and balance for two sides

  Judges use the multiplayer row in [rubric.md](rubric.md).
- **Ablation.** v0.2 core-only against v0.2 with the `multiplayer` lens on the multiplayer tasks, because the lens has no earlier
  version to beat.
- **Extra deterministic checks.** Verbatim copies of the new multiplayer example, and any mechanic in a multiplayer output that
  is not in the step's menu.
- **Adoption.**
  - On the shared tasks, apply the §8 rule to v0.2 against v0.1.
  - On the multiplayer tasks, the lens must beat both `baseline` and core-only by more than the judges' disagreement, with no
    gate regression.
