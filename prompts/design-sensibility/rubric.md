<!-- design-sensibility v0.2 | proposal-only -->
# Fun rubric

This rubric scores how well a piece of generated content delivers the player experience the pack aims at. The nine dimensions
and their anchors come from [doc 28 §7](../../docs/research/28-what-makes-it-fun.md#7-fun-rubric). The gates, the per-output
subsets and the calibration notes were added after round 1 (see [EVALUATION.md](EVALUATION.md)). Status: proposal-only [I].

## Where it is used, and where it is not

| Use | How |
| --- | --- |
| Offline evaluation of pack versions | Blind judges score every candidate (EVALUATION.md). |
| Advisory ranking of K candidates | Only among candidates that already passed every error-level lint. The rubric orders candidates; it never admits one (doc 25 §3 rule 4, §7.3). |
| Craft report card (FP67) | The same dimensions, rolled up from lints and the simulator and linked to elements, with no weighted total. |

The rubric is never:

- **shown to the generating model.** Candidates must not be written to the test (doc 28 §6.4 item 6). The lenses ask
  overlapping questions on purpose, but they are taste. They are not this scoring text.
- **used to admit content.** Verifiers admit. A judge score never overrides a lint, and a high score never excuses a failed
  gate.
- **scored with the pack in view.** Judges see the step input, this rubric and the candidates, and nothing else.

## Gates (check these before scoring)

| Gate | Passes when | Fails on (patterns seen in round 1) |
| --- | --- | --- |
| `format_ok` | The output parses as the step's format: schema, field names, section names, counts and caps. It is plain text when plain text is asked for. Effects use only declared variables, in their declared types. | Markdown bold in a plain-text briefing. A variable declared as a set of names was used as a number. |
| `facts_ok` | Every name, place, unit, gear item, number, grid, callsign, owner, role, side, source and threat matches the step's data. Nothing is added, and no listed threat is softened. | An added enemy nationality. A secondary target handed to a different owner. A report credited to the wrong person. "No air support expected" while an enemy gunship is listed. Friendly air support that was never listed. An invented direction, distance or armour rating. A soldier who is "wounded" removed from the living. |

- **In evals,** a failed gate caps the holistic score at 4 out of 10, and the judge's reason must name the failure.
- **In production ranking,** a candidate that fails a gate should never reach a judge. If one does, a lint is missing: add it
  to [code-owned-principles.md](code-owned-principles.md).
- **The judges split in round 1** on whether misusing a state variable's type fails a gate. This rubric settles it: it fails
  `format_ok`.

## Dimensions (score 1 to 5)

Score each dimension that applies, with a one-line reason that quotes the words or cites element IDs.

| Dim | Question | 1 | 3 | 5 | Fed by (lints) |
| --- | --- | --- | --- | --- | --- |
| R1 Completable and clear | Can it always finish, and does the player know what to do? | A win can hang; the objective is unfindable or unstated | Completable, but one rule or asset needs guessing | Every objective and end is provably reachable; every rule, marker and success condition is stated | MC01, MC02, MC09, MC10, C03 |
| R2 Fair lethality | Can the player blame themselves for every death? | Deaths come from unseen or unanswerable threats | Mostly fair, with one spike | Every threat is telegraphed, counterable and avoidable; lethal and fair | MC05, MC08, MC14, MC15 |
| R3 Agency | Does the player choose the method? | One workable path; going off-route means failure | Two approaches, one of them dominant | At least two distinct viable approaches; real tradeoffs; choices acknowledged | MC11, MC13, CF05 |
| R4 Tension and pacing | Does intensity rise and fall? | A flat walk or a constant peak; dead air | A curve with one slack stretch | Build, peak, reaction, release; quiet stretches carry anticipation; the campaign rises and falls | MC03, MC18, CF01, CF02 |
| R5 A living war | Does the world act without the player? | Static enemy; empty world; mission unconnected to the war | Reactive enemy, but the operation feels isolated | Reactive enemy, an audible wider operation, earlier outcomes echoed | MC04, CF13, FP01 |
| R6 Variety and surprise | Does it feel different from the last one? | Same verb, seat, time of day and mood | Varied data, similar feel | Distinct verb, seat, time and mood; one fair, foreshadowed surprise | CF03, CF17, MC17, TX05 |
| R7 Consequence and people | Do choices and people matter? | Hollow choices; invisible state; a nameless squad | Some echoes; thin characters | A few weighty choices; visible consequences with causes; named people whose fates show | CF04, CF05, CF06, C18, C21 |
| R8 Voice and authenticity | Does the text sound like this war? | Invented facts, anachronism, purple prose, moralising, stock names | Correct but generic | Plain, specific, era-true, understated, distinct voices, humane | TX01 to TX06, CF11 |
| R9 Respect for time | Is the player's time protected? | 30+ minutes without a checkpoint; long unskippable scenes; walls of text | One long stretch | Checkpoints follow the save policy; text within caps; short, skippable scenes | MC12, MC19, TX01 |

## Which dimensions apply

| Output kind | Dimensions | Notes |
| --- | --- | --- |
| Pick with a `why` field | R3 to R7 on the merits of the pick; R8 on the `why` | A `why` that cites the step's facts (an earlier result, a person's state, a place) beats a generic one. |
| Mission concept | R1 to R8 | |
| Briefing or debrief | R1, R2, R3, R5, R7, R8 | |
| Radio or dialogue lines | R8; also R1 and R2 when a line promises support or orders a move | |
| Campaign skeleton | R1 to R7; R8 on titles and effect wording | |
| Multiplayer mode, rules, limits, spawns or balance (v0.2) | R1 to R4 and R6; R5 for co-op; R8 on any text | Judge every side, and the smallest player count the step allows. There are no multiplayer calibration notes yet; add them after the first v0.2 run [I]. |
| Whole mission or campaign (simulator or Preview) | R1 to R9 | R9 needs the simulator's duration estimates or a playtest. |

## Composite

- **Production ranking and the report card** follow doc 28 §7. A 1 on R1 or R2 disqualifies a candidate. Otherwise, report
  the vector, rank by sum and break ties by R1 + R2.
- **Evals.** The round-1 protocol gave one holistic 1-to-10 score per candidate, informed by the applicable dimensions and capped
  at 4 on a failed gate. From round 2, also record the R vector per candidate, so that changes show up per dimension.

## Judge protocol

1. Relabel the candidates A, B, C and so on, and shuffle their order separately for each judge.
2. Give the judge the step input exactly as the model saw it (data, format, caps), this rubric and the candidates.
3. Check the gates first. Then score each applicable dimension, giving a one-line reason.
4. A weak judge scores one dimension per call (doc 28 §7).
5. Use at least two judges. When two judges differ by 2 or more on a candidate, or disagree on a gate, add a third judge or a
   human.
6. Report gate rates separately from scores. Never pool across tasks or model tiers without saying so.

## Calibration notes from round 1

Judges applied these anchors consistently in round 1. Reuse them so that scores stay comparable across rounds.

- **Scripted deaths.** A concept or line that decides a squad member dies ("one of them falls here") scores R3 ≤ 2 and R7 ≤ 2.
  Losses come from play.
- **Unanswerable threats.** A plan that sends the squad against a threat it cannot answer (armour with no anti-tank weapon
  listed, a gunship with no cover) scores R2 ≤ 2.
- **Allies winning for the player.** Allies who resolve the fight without the player acting score R3 ≤ 2.
- **Kill-all objectives.** "Kill all enemy personnel" as an objective scores R1 ≤ 2, because the end can hang (FP18).
- **Unclear success or exit.** A vague success condition ("destroy what you can") or no named way out scores R1 ≤ 3.
- **Hollow decisions.** When every outcome leads to the same next mission while the output claims decision points, score R3 ≤ 2
  and R7 ≤ 2.
- **Overlapping outcomes.** Outcomes of one mission that could all happen together, rather than being distinct endings, score
  R1 ≤ 3.
- **Path contradictions.** A later line that asserts a state false on some path reaching it (confirming a target destroyed on the
  path where the raid failed) scores R7 ≤ 2.
- **Radio procedure.** Radio that names the station called and the caller, carries one fact per line, ends with over or out and
  has voices you can tell apart scores about R8 = 4.
- **Staff-speak.** Stock phrasing ("critical opportunity", "secure objectives", "changes everything") scores R8 ≤ 2.
- **Framing drift.** A small drift that is not a fact (for example, calling a coup an "occupation") costs R8 but does not fail
  `facts_ok`.
