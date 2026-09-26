# Domain knowledge and guidance for LLMs

Research doc 30 for `ofp-editor`. Research date: 2026-09-27. Audience: contributors and LLM coding agents; it is meant to be read alone.
Question answered: most language models have seen little of this engine and a great deal of its successors. Should the editor teach
them with (a) an embedded knowledge skill, (b) deterministic actions that need no knowledge, or (c) guidance from our mission-aware
language service? Which mix is best and most practical?

**Epistemic legend.** **[V]** = verified against the pinned engine source or a fetched primary source (citation given). **[M]** =
measured by our own small experiment (§3); read it with the limitations in §3.6. **[I]** = inferred by us; every design in §4–§5 is
[I] and proposal-only. **[U]** = unknown.

**Pins.** `CWR@ffc61838b7` = `BohemiaInteractive/CWR` release 3.05; `CE@b67bf3bd62` = `ofpisnotdead-com/CWR-CE`. Engine citations
use `CWR:` for `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/` and `EVAL:` for `…@ffc61838b7:engine/Evaluator/`.

**Deliverable.** The primer skill `skills/mission-primer/` (`SKILL.md`, `references/file-skeletons.md`, `references/sources.md`).

**Relation to sibling docs** (not repeated here): doctrine, step shapes, capsules and knowledge packs are in doc 21; the command
catalog, checker, diagnostics schema and generator in doc 23; the weak-model harness in doc 25; model tiers in doc 14; licensing in
doc 02; plugins, skills and `ofp-mcp` in doc 22; mod sets in doc 27; campaign facts, CXL and lints in docs 18 and 19.

## TL;DR

- **Recommended knowledge stack, strongest lever first:**
  1. **Typed deterministic actions and code-written files (L1).** The model never writes structure: code renders `mission.sqm`,
     the `briefing.html` skeleton, `description.ext` settings, END-trigger wiring and common conditions. This removes whole classes
     of error rather than teaching them.
  2. **Facts from the language service (L2):** computed menus, short reference cards and command lookups, all generated from the
     pinned engine source and tagged per profile. For weak models, code picks the cards and injects them; strong and external agents
     may also call lookup tools. Measured on the weak model with one perfect, hand-written card per task placed directly in the
     prompt: passes rose from 1 to 16 of 24, answers with a hallucination fell from 10 to 2, and the result came within one pass of
     the frontier model working alone (17 of 24) [M]. This is an upper bound: choosing the right card was not tested (§3.6).
  3. **The language service as guard rail (L3).** `script.check` gives engine-parity verdicts with model-readable diagnostics and a
     repair loop that fixes one finding per turn; completions and dynamic enums come from the catalog. Of the 16 answers that fell short
     of a pass with cards, 8 contained a syntax or structure error that the checker or a typed action would catch, and 2 used a
     non-portable config value that a typed setting rules out (§3.4) [I]. This layer was not run in the experiment.
  4. **A compact primer skill (L4)**, `mission-primer`, of 1,200 words at most. It covers routing to tools, the mission model, the
     syntax rules and the traps. The numbers below are for the draft primer that was tested; the shipped primer was revised after
     the run and has not been re-run.
     - Alone, the draft lifted the weak model only from 1 to 4 passes (and 3 to 9 partials), and it halved hallucinations [M].
     - On top of cards it showed no measurable gain: 16 passes versus 16 [M].
     - It is still worth shipping. It is cheap, it is the only layer an external agent reads before choosing a tool, and it states
       rules a model does not know to look up.
  5. **Exemplars (L5), later:** verified, profile-tagged snippets from our own content.
  6. **Fine-tuning: not now.** The obstacles are training-data licensing (doc 02 §3.4, §8), upkeep per profile and per base model,
     poor transfer outside the training domain, and no benefit for cloud or external models. Retrieval beats unsupervised fine-tuning
     for injecting new facts [V, arXiv 2312.05934].
- **Answer to the owner's question.** Use all three, layered, over one source of truth: deterministic actions first, so most steps
  need no knowledge; the language service's generated data as the knowledge engine, reaching the model as cards, lookups and checks;
  and a small primer as the entry point. A primer is the weakest place to store knowledge: its coverage is capped by its length, it
  cannot follow the target profile, and in our run the model over-applied one true primer sentence into a hack.
- **Where the weak model still failed with cards** (§3.4): a correct command in the wrong form (binary commands used as prefixes);
  a whole file (`briefing.html` got 0 passes in all 8 weak-model answers, 6 of them with help); a misread question. The fix is L1
  and L3, not more knowledge.
- **Activation.** A weak model never decides to load knowledge. Each workflow step declares its primer sections and cards, and the
  harness injects them. Strong in-app models get the whole primer plus lookup tools. External agents get it as an Agent Skill through
  `ofp-mcp`.
- **Scope of knowledge.** Cards and catalog rows are tagged `cwa199` / `cwr` / `ce` and keyed to the mod-set fingerprint. The primer
  states conservative rules that hold in every profile, and names the profile when a rule does not.
- **Maintenance.** Every primer and card fact has an id, a pinned citation and a check kind (`catalog`, `const`, `vector`, `probe`,
  `review`), and tests fail on drift. The twelve experiment tasks become the first cases of a knowledge instrument.

## 1. The problem

### 1.1 A low-resource dialect in a high-resource shadow

- **No public benchmark measures SQF or SQS** (doc 14 §4.4) [V per doc 14]. SQS is barely identifiable in public code, and labelled
  SQF corpora are mostly from the later titles [I per doc 14]. Code models "struggle with low-resource languages" (MultiPL-T, arXiv
  2308.09895) [V per doc 14]. Models also "cannot generalize to using unseen functions and libraries, because these would never appear
  in the training data" (DocPrompting, arXiv 2207.05987) [V].
- **Contamination is worse than absence.** The successors share this engine's vocabulary, so a model fills gaps with confident
  near-misses: `sleep`, `isNil`, `spawn`, `findIf` and `setDamage` in scripts; `//` comments in SQS; `class Entities` and
  `version=53` in `mission.sqm`; the diary and task API instead of `briefing.html`; `thisTrigger` in conditions. None of these exist
  here (doc 14 §2, doc 23 §3–§4) [V], and our run observed most of them (§3.5).
- **Knowledge is more than scripts.** It also covers file formats (`mission.sqm`, `briefing.html`, `description.ext`), editor rules
  (12 crew seats per group; auto-joining the nearest leader within 100 m), trigger semantics (`this`, `thisList`) and campaign
  mechanics (every trigger of an END type must be active at once; `saveVar` takes the variable's name). Most of this is visible only
  in the engine source, not in public documentation.
- **Dialects.** The released source is the Remastered engine, which registers commands that 1.99 lacks (doc 23 §4) [V]. So even
  knowledge that is correct "from source" must carry a profile tag.

### 1.2 What knowing has to mean here

| Kind | Examples | Checkable by code? |
| --- | --- | --- |
| **Facts** | Command names and operand types, class names, limits, file tokens (`OutroLoose`, `LIEUTNANT`) | Yes: catalogs, extracted constants |
| **Rules** | SQS line classes, field check modes, the `this` context, the END rule, `saveVar` semantics | Mostly: parity checker, lints, probes |
| **Craft** | How to structure an ambush, which trigger pattern suits a rescue, campaign variable conventions | No: templates, exemplars, the user |

**Requirements [I].** Knowledge must be correct for the mission's target profile, checkable before anything is committed, available
offline, usable by a weak local model, visible to the user (the glass-box rule in `AGENTS.md`), written in our own words with no
Bohemia wiki prose (doc 02 §3.5), and portable to external agents through `ofp-mcp` (doc 22 §4.3).

## 2. Options compared

### 2.1 Summary

| Option | Weak-model fit | Coverage | Build / upkeep | External agents | Main risk | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| **A. Typed actions, code-written files** | Best: nothing to know | Only what we built actions for | High build, low upkeep | Yes, the same tools via `ofp-mcp` | Escape hatches (raw script) still need B–C | **L1: first** |
| **B. Facts: menus, cards, lookups** | Very good when code picks what to inject [M] | As wide as the catalog and cards | Generated rows; cards authored once, pinned | Yes, as lookup tools | Retrieval misses; right fact, wrong form | **L2** |
| **C. Language service as guard rail** | Good: precise, one finding at a time | Syntax, types, profile, lints | Needed anyway for validation (doc 23) | Yes, `script.check` | Semantic errors that parse | **L3** |
| **D. Primer skill** | Weak alone [M]; orients and routes | ≤ 1,200 words | Low; pinned facts | Yes, the first thing read | Stale text, over-applied rules | **L4** |
| **E. Exemplar library** | Good for Compose steps (doc 25 §2.1) [V per doc 25] | Grows with use | Medium: every snippet re-checked per profile | Yes | Copied facts that do not exist in the mod set | **L5, v2** |
| **F. Fine-tuning** | Unclear; poor transfer outside its domain | Frozen at training time | High, per base model and per profile | No | Licensing and staleness | **No, for now** |

### 2.2 A. Typed deterministic actions and code-written files

- **What.** Every mission element, setting and campaign route is a typed editor command. Code computes the valid options and writes
  the files (doc 21 §1.1, §5.2; doc 19 §7). "End when group G is destroyed" writes activation `None` and the condition
  `"alive _x" count units G == 0`. The briefing tool renders `Main`, `Plan`, `OBJ_n` and `Debriefing:*` and leaves the model only
  text slots. The settings panel writes `debriefing = 0;`. The campaign compiler writes END triggers and `description.ext` keys.
- **Why it wins.** A fact the model never has to state cannot be misstated. This is doc 21's "remove-it test": if a result is the same
  without the model, ship the automation.
- **Precedent.** SPEAC gives the model an intermediate language it handles well and compiles that to a very low-resource target
  language. When the model strays outside the intermediate language, it uses "compiler techniques to repair the code" back into it.
  In a single case study (the UCLID5 verification language) it "produces syntactically correct programs more frequently" than
  retrieval or fine-tuning baselines (arXiv 2406.03636) [V]. Our CXL condition language, lowered to SQS by code (doc 19 §5), is the
  same move.
- **Limit.** Coverage is finite. A user's idea with no action falls back to script text, which needs B and C.

### 2.3 B. Fact providers: menus, cards and lookups over the user's own data

- **Menus.** Class, place and group menus are computed from the active mod set's catalog and the loaded island (doc 21 §10, doc 27).
  The model picks a letter and never types a class name.
- **Cards.** A card is a short (≤ 150 words [I]), profile-tagged note in our own words about one rule or format, for example
  `trigger.condition-context` or `briefing.html`. Cards carry pinned facts (§5.1).
- **Lookups.** `script.command` returns a command's rows: its form (`left command right`), operand types, availability per profile and
  a one-line meaning. For a missing command it returns `not registered` with `requires` and `did_you_mean` (doc 23 §13.4).
- **Evidence.** In our run, cards took the weak model from 1 to 16 passes of 24 [M]. Retrieved documentation helps code generation
  with unseen functions (arXiv 2207.05987) [V].
- **Limits.**
  - The right card must reach the model; our run injected a perfect card, so retrieval is unmeasured (§3.6).
  - A correct fact can still be composed wrongly (§3.4).

### 2.4 C. The language service as guard rail

- **Checks and repair.** `script.check(text, field, profile)` runs the engine-parity verdict for the field's check mode, plus lints
  (doc 23 §6, §13.3). Diagnostics use the machine-readable schema of doc 23 §13.4, including `expected`/`found` types, `candidates`,
  `requires` and `arma_ism`. The repair loop sends one finding per turn and is bounded (doc 21 §6.2). Self-correction without external
  feedback is unreliable (arXiv 2310.01798) [V per doc 25], so the finding must come from code.
- **Completions and signatures.** The in-app script editor and the agent use the same profile-filtered completion list with each
  command's form.
- **Constrained decoding.** Enum fields (classes, waypoint types, trigger types) become dynamic enums in the answer schema (doc 13 §4
  item 2). For script slots, see §4.5.
- **Limits.**
  - A constraint proves syntax, not intent (doc 13 §4 item 5).
  - Some errors parse cleanly. `"OBJ_1" objStatus "DONE"` is valid, but the engine prefixes `OBJ_` and so sets `OBJ_OBJ_1`
    (`CWR:Game/Commands/GameStateExtUi.cpp#L1825-L1851`) [V]. Only a cross-file lint that matches objective ids against briefing
    anchors catches it.

### 2.5 D. A compact primer skill

- **What.** An Agent Skills folder with a `SKILL.md` of at most 1,200 words (about 8 kB, roughly 2k tokens [I]). It holds routing
  rules, the mission model, syntax, traps and campaign essentials. Its references are loaded on demand.
- **For it.** It is cheap and follows an open format that the MCP Skills extension can also serve (doc 22 §2.1). It names the tools
  and the "empty result is an answer" rule. It states the unknown unknowns: rules a model will not think to look up, such as the
  operand order of binary commands, the missing `isNil`, and the requirement that every trigger of an END type be active at once.
- **Against it.** Coverage is capped by length; it cannot follow the target profile or the mod set; it goes stale unless pinned; and
  weak models over-apply its sentences. With the draft primer, the weak model used `goto "exit"` twice, because the draft said that a
  jump to a missing label ends the script (§3.5). That sentence was true (`CWR:Game/Scripting/Scripts.cpp#L552-L564`); the harm
  came from a true fact that the model over-applied.
- **Evidence.** The draft primer alone: 1 → 4 passes and 10 → 5 hallucinating answers; with cards, no measurable gain [M].

### 2.6 E. Exemplar library

- **What.** Verified snippets, each tagged with its profiles and field kind, are retrieved per step as one to three examples in the
  capsule (doc 21 §8.1). Bootstrapped demonstrations let small models compete with expert prompt chains (DSPy, arXiv 2310.03714)
  [V per doc 25].
- **Sources.** Our own templates; outputs the user accepted, kept only with consent through the normal save flow; CWR's GPL test
  fixtures, with attribution (doc 02 §3.4; doc 14 §4.4 item 2).
- **Rules** [I]. Every exemplar passes `script.check` for each profile it claims. Classes and names in an exemplar are placeholders
  that code re-binds to the active mod set. No exemplar is taken from wiki text.
- **Phase.** Doc 17 §10 defers the recipe library to v2. We agree.

### 2.7 F. Fine-tuning

- **Licensing.** Training on game texts, missions or stringtables should be avoided: the weights might become NonCommercial,
  Arma-only derived material (doc 02 §3.4) [I per doc 02]. A fine-tuned model inherits its base licence and needs a pinned
  data-provenance manifest (doc 02 §8 rule 5). Wiki prose has no known GPL-compatible licence, so it cannot be used (doc 02 §3.5).
  That leaves synthetic data we generate ourselves.
- **Transfer.** A fine-tuned 1.7B planner scored 82.9% in its domain and 0% on two unseen ones (arXiv 2601.14456) [V per doc 25].
  "LLMs struggle to learn new factual information through unsupervised fine-tuning", and retrieval "consistently outperforms it"
  (arXiv 2312.05934) [V].
- **Upkeep.** Each base model (doc 14 §6 lists several candidates) and each profile would need its own tuning, re-done at every
  engine pin bump. Nothing carries over to cloud (BYOK) or external agents.
- **Verdict.** No. Revisit only for a narrow local router trained on synthetic data, after L1–L4 are measured on T1 models.

## 3. The experiment

### 3.1 Method

- **Tasks.** Twelve tasks, each with a prompt, a ground truth, a PASS / PARTIAL / FAIL rubric with a separate hallucination flag,
  evidence at pinned lines in both clones, and a dialect note. All twelve ground truths were re-checked against both clones before
  grading, and the negative greps (for example, no `isNil`, `thisTrigger` or `createDiaryRecord` registration) were redone. Seven
  evidence or rubric refinements were made; none overturned a ground truth.
- **Conditions:**
  - `none`: the prompt alone;
  - `primer`: the draft primer that preceded `skills/mission-primer/SKILL.md`, prepended to the prompt;
  - `cards`: the task's reference card, written from source the way the language service would return it, placed in the prompt. This
    simulates a perfect code-side lookup, with no tool call;
  - `primer + cards`: both;
  - `frontier, none`: a frontier model with no help, as the control.
- **Models and samples.** The weak model is a small, fast hosted model standing in for our T1/T2 local tiers (doc 14 §6); the
  control is a frontier hosted model. Two samples per task and condition: 24 answers per condition, 120 in total.
- **Grading.** An LLM grader applied each rubric with the ground truth and the evidence, and wrote a note per answer.

### 3.2 Tasks

| Id | Topic | What a correct answer needs | Trap from the successor titles |
| --- | --- | --- | --- |
| T01 | SQS timing | `~5` before `hint "Go"` | `sleep 5` |
| T02 | SQS conditional exit | `? getDammage tank1 > 0.5 : exit` | `exitWith`, `terminate` |
| T03 | SQS comments | Only a leading `;` is a comment; `//` errors; mid-line `;` separates statements; `comment` is a no-op | `//` comments |
| T04 | Spelling and existence | `setDammage`, `getDammage`; no `isNil`, so initialise globals | `setDamage`, `isNil` |
| T05 | Trigger context | `this` is the activation Boolean, `thisList` the matches; activation None gives false | `this` as the trigger object, `thisTrigger` |
| T06 | "Group wiped out" condition | Activation None, `"alive _x" count units G == 0` | `findIf`, `isEqualTo` |
| T07 | `mission.sqm` top level | `version=11`; `Mission`, `Intro`, `OutroWin`, `OutroLoose`; triggers in `Sensors` | `class Entities`, version 53 |
| T08 | `description.ext` | `debriefing = 0;` in the mission folder's file; what happens instead | A control item: the successors use the same key |
| T09 | Campaign endings | END1–END6 and LOOSE; keys `end1`–`end6` and `lost`; every END1 trigger must be active | `endMission`, BIS functions |
| T10 | `saveVar` | Name as a string; which types persist; undefined stores nothing; objects need a workaround | `profileNamespace`, `setVariable` |
| T11 | Editor group rules | 12 crew seats; auto-join to the nearest same-side leader within 100 m; no check at insert | No cap; link by hand |
| T12 | `briefing.html` and objectives | `<html><body>`, `<hr>` sections, anchors inside `<p>`, `"1" objStatus "DONE"` | Diary and task API |

### 3.3 Results

| Condition | Pass | Partial | Fail | Pass rate (95% Wilson) | Score (partial = ½) | Answers with a hallucination |
| --- | --- | --- | --- | --- | --- | --- |
| Weak, none | 1 | 3 | 20 | 4% (1–20%) | 10% | 10 (42%) |
| Weak, primer | 4 | 9 | 11 | 17% (7–36%) | 35% | 5 (21%) |
| Weak, cards | 16 | 6 | 2 | 67% (47–82%) | 79% | 2 (8%) |
| Weak, primer + cards | 16 | 4 | 4 | 67% (47–82%) | 75% | 1 (4%) |
| Frontier, none | 17 | 5 | 2 | 71% (51–85%) | 81% | 2 (8%) |

The intervals treat answers as independent. The two samples per task are correlated, so the real uncertainty is wider [I].

Per task and sample (`P` pass, `a` partial, `f` fail), rebuilt from the graded answers:

| Task | Weak, none | Weak, primer | Weak, cards | Weak, primer + cards | Frontier, none |
| --- | --- | --- | --- | --- | --- |
| T01 | f f | P P | P P | P P | P P |
| T02 | f P | a a | P P | P P | P P |
| T03 | f f | a a | P P | P P | P P |
| T04 | f a | P P | a f | P P | P a |
| T05 | f f | a f | P P | P P | P a |
| T06 | f f | f f | P a | P f | P P |
| T07 | f f | f a | P P | P P | P P |
| T08 | f f | f f | P P | a a | P P |
| T09 | f f | f f | a P | f P | P f |
| T10 | f a | a a | a a | a a | a a |
| T11 | f a | f a | P P | P P | a f |
| T12 | f f | f f | f a | f f | P P |

### 3.4 Per-task observations

- **Cards fix lookups.** Every task that turns on a single fact or rule passed in both samples in the `cards` condition: T01–T03,
  T05, T07, T08 and T11 [M]. In `primer + cards`, T08 fell to two partials. The grouping into "single fact" tasks was made after
  grading, so this describes the run; it does not test a hypothesis.
- **The primer helps only where it speaks.** It covered T01 and T04 (both passed) and part of T02, T03 and T10 (partials). Where it was
  silent (T06, T08, T12), the weak model still failed all six answers [M].
- **Whole files fail.** T12 asks for a complete `briefing.html` plus one statement. The weak model got 0 passes in the 6 answers with
  help (1 partial) and 0 in the 2 without, while the frontier model passed both [M]. This is a Compose step and belongs to code (L1).
- **Right fact, wrong form.** These errors remained with cards [M]:
  - T04: `setDammage truck1 0.8`, a binary command written as a prefix, twice;
  - T12: `objStatus` written as a prefix command with an `OBJ_`-style id (`objStatus "OBJ_1" "DONE"` and variants), in all four
    card answers;
  - T06: `count {alive _x} units G`, with the code operand on the wrong side;
  - T06: `"{alive _x}"`, a brace literal nested inside a string.

  The final primer now states the command forms. The checker (L3) or a typed action (L1) should catch or prevent every one of them
  [I].
- **Engine-internal rules beat the frontier model too.** Without help, the frontier model missed the 100 m auto-join (T11, both
  samples short of a pass) and answered "yes" to T09(c) once; the weak model with cards passed T11 twice [M]. Rules that live only in
  source need cards even for strong models.
- **Advice is the last gap.** No answer in any condition passed T10: correct type lists kept omitting the workaround of saving counts
  or class names and recreating the units [M]. The final primer states the workaround, and the campaign designer's roster pattern
  (doc 19 §4) makes it automatic.
- **A config value.** T08 with primer + cards wrote `debriefing = false;` twice. The engine tests the key's value as an integer. In
  the CWR and CE source a word that is not a number falls back to script evaluation, and `false` then reads as 0, so these answers
  probably work on CWR and CE (`CWR:IO/ParamFile/ParamFile.cpp#L837-L860`, `#L1818-L1843`;
  `CWR:IO/ParamFile/ParamFileEval.cpp#L107-L113`). That comes from reading the code: it is not probed, and 1.99 is [U]. Grading
  them as partial is defensible for portability but strict. A typed setting removes the question.
- **Unguided behaviour is bimodal.** With no help, weak sample 1 declined all twelve tasks, while sample 2 answered all twelve and
  hallucinated in ten [M].
- **The residue is mostly mechanical.** Across the two card conditions, 16 answers fell short of a pass:
  - 8 contain a syntax or structure error that `script.check`, a lint or a typed action would catch or rule out [I]: T04 ×2,
    T06 ×2 and T12 ×4;
  - 2 use the T08 config value `false`, which is non-portable rather than clearly wrong (see above); a typed setting rules it out;
  - 6 are gaps in explanation: T10 ×4 and T09 ×2.

### 3.5 Hallucination patterns

| Pattern | Observed | Layer that removes it |
| --- | --- | --- |
| Commands and idioms from later titles | `sleep 5` (T01); `myVar == nil` as an existence test (T04: `nil` is registered, but any binary operation with a nil operand returns nil, so the test is never true; `EVAL:express.cpp#L1210`, `#L1348-L1351`); invented `objectiveDone` (T12) | L2 lookup; L3 `cmd.not-registered` with an `arma_ism` hint, plus a nil-comparison lint |
| Invented or later-title file formats | `version = 3` and `class Triggers` (T07); `class Extended { class Debriefing }` (T08); a `next =` key (T09) | L1 writes files; L2 schema cards |
| Wrong engine model | `this` is the trigger object (T05); one END1 ends the mission (T09); a unit joins the selected group; seats counted as units (T11) | L2 cards; L1 computed menus; lints |
| Right fact, wrong form | Binary commands written as prefixes (T04, T12); the operand on the wrong side of `count` (T06) | L3 parity check; a decode grammar with arity (§4.5) |
| Over-applied primer text | `goto "exit"` as an exit mechanism (T02, both primer answers; it does end the script at runtime, so this is fragile style rather than a broken answer) | The final primer states `exit`; the pitfall becomes the lint `sqs.goto-unknown-label` |
| False negatives | "`comment` is not a built-in" (T03); "iteration is absent" (T06) | The final primer names the real idioms; "empty result" applies only to lookups actually made |

### 3.6 Limitations

- **Models.** The weak model is a proxy, not a T1 candidate from doc 14 §6. The control is one frontier model.
- **Sample size.** 24 answers per condition, from 12 tasks sampled twice. The differences between `cards` and `primer + cards`
  (16/16 passes, 2/4 fails, 2/1 hallucinations) are within noise.
- **Grading.** One LLM grader, one pass, no human adjudication. Some calls are borderline, for example T08 `false`, whose engine
  behaviour is [U].
- **Perfect cards.** Each card was written for its task with the answer known, and injected directly. The `cards` condition is an
  upper bound on retrieval. Code-side card selection and model-invoked lookups are unmeasured.
- **Not run.** The check-and-repair loop (L3); end-to-end editor edits (the tasks are single-turn knowledge questions); anything on
  the 1.99 executable.
- **Authorship.** The same team wrote the tasks, cards and primer, so there is a risk of overfitting. The final primer was revised
  after these failures and has not been re-run.
- **Reproducibility.** The prompts, cards, raw answers and grader notes are not committed to this repository, and the models and
  sampling settings are not named. The tables cannot be re-derived from the repository alone. Committing the task set (in our own
  words) is part of §5.2 item 8.
- **Post-hoc grouping.** The task groupings in §3.4 ("single fact", "whole file", "mechanical residue") were made after grading.
  They explain this run and do not predict the next one.
- **Hallucination flag.** The flag is the grader's judgement. Two things show it is imperfect: a runtime-correct `goto "exit"`
  counted against the primer answers, and `debriefing = false;` probably works on CWR and CE (§3.4).

## 4. The recommended stack

### 4.1 Layers

| Layer | What | Who owns the fact | Present in |
| --- | --- | --- | --- |
| L1 | Typed actions; code-written files, skeletons and conditions; CXL lowered by code | Code | Every workflow; the no-AI path |
| L2 | Computed menus; reference cards; `script.command`, `reference.search`, `catalog.find`, `island.places` | Generated catalogs and pinned cards | Capsules (code-selected); tools for qualified models |
| L3 | `script.check`, lints, diagnostics shaped for models, one-finding repair; completions; dynamic enums; an optional decode grammar | The checker | After every model step that emits script or config |
| L4 | The `mission-primer` skill | Pinned text | Capsule system text (sections); Agent Skill for external agents |
| L5 | Exemplars (v2) | Checked snippets with placeholders | Compose and Draft capsules |

### 4.2 By step shape (doc 21 §3)

| Shape | Knowledge in the capsule | Tools the model may call | Checks |
| --- | --- | --- | --- |
| Deterministic | None | None | Validators |
| Pick | Option lines written by code from facts | None | Admission |
| Fill | Slot spec with dynamic enums; at most one card when a slot has a rule | None | Schema and lints |
| Compose (a condition, an init line, an `.sqs` snippet) | Primer §3–§4; the field-context card; a catalog row for each command code expects | `script.command` only if qualified | `script.check` in the field's mode; R repairs, one finding each |
| Draft (a multi-entity change set) | The whole primer; code-picked cards | All Lookup and Check tools | Per-command checks; full lints |

For weak models, **code selects and injects** the cards: this is what `cards` measured. Weak models are poor at multi-turn tool use
(BFCL multi-turn 22% for a 4B model, doc 14 §4.1) [V per doc 14], so they are not asked to fetch cards themselves. Code chooses from
four signals [I]: the field kind (a condition gets `trigger.condition-context`); the step (the briefing step gets `briefing.html`);
the tokens of the text being repaired (each command gets its catalog row); and the codes of the current diagnostics (each gets its
`diagnostic.explain` card).

### 4.3 By effort (doc 21 §7.1)

| Effort | Primer | Cards | Repairs | Model lookups |
| --- | --- | --- | --- | --- |
| Quick | None beyond the step spec | Rows for tokens in the draft only | 1 | No |
| Standard | Sections for the step | Code-selected | 2 | No |
| Thorough | Whole | Code-selected plus K candidates | 3 | If the model setup qualified |
| Max | Whole | As Thorough, plus an optional Preview smoke run | 3 | If qualified |

Effort never changes the checks (doc 21 §7.1).

### 4.4 Knowledge tools the language service exposes

The names are provisional. They extend doc 21 §10.2 (`script.command`, `reference.search`) and doc 23 §15 (`validate_script`), and
consolidating them is Open question 7. Every tool is a `Lookup` or `Check` variant of doc 21 §1.3's `AgentTool`, so it adds no new
effect.

| Tool | Framing name | Input | Output |
| --- | --- | --- | --- |
| `script.command` | lookup_command | name, profile | Rows as `left command right → result`, availability per profile, one-line meaning, card ids; or `not_registered` with `requires`, `did_you_mean` and `arma_ism` |
| `reference.search` | — | words or a type pattern (`Object → Scalar`), profile, limit | At most 8 rows, with shown/total counts |
| `reference.card` | schema_card | card id | A card of at most 150 words, with profile tags and fact ids |
| `diagnostic.explain` | explain_diagnostic | diagnostic code | What, why, fix pattern, one checked example |
| `script.check` | validate_script, check_field | text, field kind, profile | Diagnostics, schema v1 (doc 23 §13.4) |
| `script.complete` | — | text, cursor, field kind, profile | Ranked completions with forms |
| `catalog.find` | list_classes | side, role, era | Class ids from the active mod set |
| `island.places` | — | kind, near | Places |
| `next_step` | — | — | One readiness item (doc 21 §11.1) |

**First card set, taken from the experiment.** SQS: `sqs.line-classes`, `sqs.line-prefixes`, `sqs.conditional-line`. Scripts and
fields: `script.command-forms`, `field.check-modes`, `trigger.condition-context`. Editor and files: `editor.groups`, `mission.sqm`,
`briefing.html`, `description.ext:debriefing`. Campaigns: `campaign.endings`, `campaign.savevar`.

**Diagnostics taken from the failures in §3.5** [I]: `cmd.not-registered` (with `arma_ism`), `cmd.binary-used-as-prefix`,
`sqs.slash-comment`, `sqs.goto-unknown-label`, `objstatus.prefixed-id` (an id that starts with `OBJ_`),
`briefing.missing-html-wrapper`, `briefing.anchor-outside-paragraph`, `trigger.this-with-activation-none`, `end.same-type-and`
(info: the mission ends only when every trigger of that END type is active), `savevar.unquoted-name` and
`ext.debriefing-non-numeric`.

```toml
# Card sketch; proposal-only. Bodies are our own words.
id = "trigger.condition-context"
profiles = ["cwr", "ce"]            # "cwa199" only after a probe confirms it
body = """Unless the condition is exactly `this`, the engine sets `this` (Bool, the activation result) and `thisList` ..."""
[[facts]]
id = "P3.15"
source = "BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L839-L923"
check = "probe"
```

### 4.5 Constrained decoding from the catalog

- **Enums.** Classes, waypoint and trigger types, group handles and card ids are dynamic enums rebuilt per request (doc 13 §4). This
  is cheap and certain.
- **Script slots.** A grammar can be generated per profile from the catalog [I]. It limits identifiers to the profile's commands,
  mission variables and `_x`-style locals, and it encodes each command's **arity position**: nular names as operands, unary names
  before an operand, binary names only between operands. Such a grammar would have rejected `sleep`, `setDammage truck1 0.8`,
  `objStatus "OBJ_1" "DONE"` and `count {…} units G` at decode time.
- **Limits.** It cannot hold types, overloads or field check modes, so the checker stays the gate. Grammars can distort a model's
  output distribution (arXiv 2405.21047), and gains are small (doc 25 §2.4) [V per doc 25]. Keep the `why` field and the `none_fit`
  escape, make it experimental, and measure it (Open question 9). llguidance, a Rust library, accepts Lark-style grammars (doc 13 §4)
  [V per doc 13].

### 4.6 Activating the primer

- **Built-in agent, weak model, or any Pick / Fill / Compose step.** Activation is deterministic. A workflow step declares, for
  example, `knowledge = { primer = ["3", "4"], cards = ["trigger.condition-context"] }`. The harness splits the primer at its
  headings and places those sections in the capsule's system text (doc 21 §8.1). The model never decides whether to load knowledge.
- **Built-in agent, qualified model, Draft step.** The whole primer is in the system text, and the model may call the lookup tools.
- **External agents through `ofp-mcp`** (loopback and token, doc 22 §4.3). The primer is offered as an Agent Skill through the MCP
  Skills extension where the client supports it (doc 22 §2.1, SEP-2640), otherwise as an MCP prompt and resource. The server's
  instructions and each tool description carry one line: "load `mission-primer` before editing". Activation is by description: in
  Agent Skills' progressive disclosure, the name and description (about 100 tokens) are always loaded, the body when the skill
  activates, and `references/` only on demand [V: agentskills.io specification].
- **Portability.** The folder follows the open spec: `name` matches the folder, the description is at most 1,024 characters, and
  metadata values are strings under an `editor.` namespace. Any skills-aware agent can use it. Tool names in the body are marked
  provisional.

### 4.7 Per target profile and mod set

- **Profile.** Every catalog row, card and diagnostic carries availability for `cwa199`, `cwr` and `ce` (doc 23 §14).
  `script.command` answers for the mission's target profile and names other profiles in `requires`. The primer states only rules
  true in all three, names the profile (for example "only on CWR and CE"), or marks them "unconfirmed for 1.99".
- **Mod set.** Class menus and `catalog.find` read only the active mod set's catalog (doc 27). Cards that mention classes are
  generated at import time and never committed (doc 02 §3.4; doc 21 §10.1). Mod-specific craft knowledge arrives as T0 content-pack
  skills (doc 22 §2.1); they are hash-pinned, treated as untrusted text, and cannot grant tools.
- **Cache key.** Knowledge packs are keyed by (profile, mod-set fingerprint, generator version, card-set version).

## 5. Maintenance

### 5.1 One source of truth

- **Generated.** `ofp-script-catalog` is built from the pinned engine snapshots, a wiki facts snapshot and `overrides.toml` (doc 23
  §14). It feeds `catalog.json` for lookups, the catalog rows inside cards, completion lists, the decode grammar's identifier sets,
  and the "absent" and "unconfirmed" lists that the primer's §4 must match.
- **Authored.** Cards and the primer are in our own words, with no wiki prose (doc 02 §3.5). Each fact has an id, a claim, a pinned
  source and a check kind.
- **Fact table.** `skills/mission-primer/references/sources.md` is today's fact table for the primer (P1.1–P5.9 and R1–R4). It
  should later be generated from a machine-readable fact file shared with the cards.

### 5.2 Tests that pin the knowledge [I]

1. **Absence.** Every name in the primer's "Not in this engine" list is absent from every profile's catalog. Every name in "Remastered
   only, or unconfirmed" is present in `cwr` and not confirmed for `cwa199`.
2. **Presence and form.** Every command named in the primer, cards or exemplars exists in the profiles the text claims. Every code
   span parses and passes `script.check` in its declared field kind. This is the fork's doc-example gate (doc 23 §9), per profile.
3. **Constants.** 12 seats, 100 m, `version=11`, the 4,096-byte line buffer and file tokens (`OutroLoose`, `LIEUTNANT`, `LOOSE`) are
   compared with values the generator extracts from the pinned source.
4. **Citation drift.** The generator hashes each cited line range at the pin. On a pin bump, a changed hash marks the fact "needs
   review", and CI fails until someone reviews it.
5. **Probes.** Each `probe` fact gets a probe mission in the preview-harness suite (`AGENTS.md`; doc 08). Verdicts are recorded per
   profile; 1.99 probes are run by hand.
6. **Budget and format.** `SKILL.md` stays at or under 1,200 words; `name` equals the folder; the description is at most 1,024
   characters; metadata values are strings; cards are at most 150 words.
7. **Hygiene.** No names of private projects; no trademarks in skill names (doc 02 §9); no copied Bohemia text, checked by review.
   A similarity check against a locally kept wiki snapshot is possible, but the snapshot is never committed.
8. **Knowledge instrument.** T01–T12 become the first cases of a `knowledge` instrument in the evaluation suite (doc 21 §12), in our
   own words. Answers are graded by rubric plus `script.check` on any code they contain, run per model setup and condition, and
   reported per task, never pooled. The set should grow to at least 60 tasks with paraphrase twins and injection cases.

### 5.3 Update flow

Bump the engine pin → regenerate the catalog → read the drift report → review the changed facts → re-run the knowledge instrument
→ update the primer's `editor.engine-pins` and `editor.as-of` metadata.

### 5.4 What the failures changed in the primer

| Failure | Change in the final `SKILL.md` |
| --- | --- |
| T02 `goto "exit"` | Removed the "a missing label ends the script" sentence; stated `exit` |
| T03 (c), (d) | A mid-line `;` separates statements; `comment` is a no-op command |
| T04, T12 prefix forms | A command-forms paragraph with binary examples and one negative example |
| T05 activation None | `this` is false and `thisList` is empty |
| T06 | The wiped-out condition, with the code string on the left of `count` |
| T07 | `version=11;` and the section names; a skeleton in `references/` |
| T08 | `debriefing = 0;` in the mission folder's file, "not `false`" |
| T09 | Every `END<n>` trigger must be active at once; `LOOSE` ends at once; `forceEnd` only skips the wait for camera and title effects |
| T10 | The name as a string; undefined stores nothing; save counts or class names |
| T11 | Seat counting; the 100 m auto-join; the limit checked after placing |
| T12 | `"1" objStatus "DONE"` and the `OBJ_` prefix; the skeleton and parser rules in `references/` |
| Absent list | Added `findIf`, `isEqualTo`, `thisTrigger`, `createDiaryRecord`, `createSimpleTask` |

To stay under 1,200 words, the revision dropped the resistance-friendship setting, marker shapes, the "section without groups" rule
and the `goto` fallback detail. The tools and lints cover them.

## Open questions

1. **Transfer.** Do these results hold on the T1/T2 local candidates (doc 14 §6) and with real tool calls? Qualification needs at
   least 14 all-pass trials per task (doc 21 §12.3).
2. **Retrieval.** How often do code-selected cards include the right card, and how does that compare with model-invoked lookups on
   qualified models?
3. **Repair.** Does `script.check` with one-finding repair (R = 0, 1, 2) close the form errors of §3.4?
4. **The revised primer.** On top of cards, does it help, hurt or change nothing? It needs a re-run with more samples; the first run
   saw 2 versus 4 fails, within noise.
5. **1.99.** SQS sigils, the briefing parser, `saveVar`, the trigger context and the group rules are verified only on CWR 3.05 and CE
   source.
6. **`debriefing = false;`** Partly answered: the CWR and CE source reads it as 0 through the expression fallback (§3.4). A probe
   should confirm this on CWR and CE; 1.99 remains [U].
7. **Tool names.** Consolidate `script.command` / lookup_command and `script.check` / `validate_script` / `check_field` across docs 21,
   23 and 30.
8. **Card data.** May cards embed the dated wiki "since" facts (doc 23 open question 4)? Card bodies stay in our own words either way.
9. **Arity grammar.** Does encoding arity positions in the decode grammar (§4.5) help small models more than it distorts them?
10. **Mod knowledge.** Should mod authors ship cards and skills as T0 packs, and who reviews them (doc 22)?

## Sources

**This repository.** `AGENTS.md`; `skills/mission-primer/` (`SKILL.md`, `references/file-skeletons.md`,
`references/sources.md`); `docs/research/` doc 02 (§3.4, §3.5, §8, §9), doc 08, doc 13 (§4), doc 14 (TL;DR, §2, §4.1, §4.4, §6),
doc 17 (§10), docs 18 and 19 (§4, §5, §7, lints), doc 21 (§1–§3, §6–§8, §10–§12), doc 22 (§2.1, §4.3), doc 23 (§3–§6, §9,
§13–§15), doc 24, doc 25 (§2), doc 27.

**Engine (pinned).** `CWR:Game/Commands/GameStateExtUi.cpp#L1825-L1861` (`objStatus` prefixes `OBJ_`). Per-fact citations for the
primer are in `skills/mission-primer/references/sources.md`. Task evidence for T01–T12 is summarised in §3.2 and was re-checked
against both clones on 2026-09-27.

**Web** (fetched 2026-09-27):

- Agent Skills specification, <https://agentskills.io/specification>: frontmatter fields and limits, progressive disclosure,
  `references/`;
- Ovadia et al., "Fine-Tuning or Retrieval? Comparing Knowledge Injection in LLMs", [arXiv 2312.05934](https://arxiv.org/abs/2312.05934);
- Zhou et al., "DocPrompting: Generating Code by Retrieving the Docs", [arXiv 2207.05987](https://arxiv.org/abs/2207.05987);
- Mora et al., "Synthetic Programming Elicitation for Text-to-Code in Very Low-Resource Programming and Formal Languages",
  [arXiv 2406.03636](https://arxiv.org/abs/2406.03636).

**Cited through sibling docs:**

- MultiPL-T, [arXiv 2308.09895](https://arxiv.org/abs/2308.09895), and BFCL multi-turn figures (doc 14);
- [2601.14456](https://arxiv.org/abs/2601.14456), [2310.01798](https://arxiv.org/abs/2310.01798),
  [2405.21047](https://arxiv.org/abs/2405.21047) and [2310.03714](https://arxiv.org/abs/2310.03714) (doc 25);
- the MCP Skills extension, SEP-2640 (doc 22).

**Statistics.** Wilson score interval: E. B. Wilson, "Probable inference, the law of succession, and statistical inference", *JASA*
22 (1927) 209–212.

## Verification notes

- **Experiment counts.** Per-condition totals were recomputed from the 120 graded answers and match the run summary. The run's
  per-task summary strings merge pass and partial into one letter, so §3.3's matrix was rebuilt from the graded answers themselves.
- **Intervals and derived numbers.** Wilson intervals were computed by hand with z = 1.96 and n = 24. The partial-credit score is
  (pass + ½ partial) / 24.
- **Engine facts spot-checked for this doc** at `CWR@ffc61838b7`: the `objStatus` handler; the `==` overloads
  (`EVAL:express.cpp#L1113`, `#L1116`; `CWR:Game/Commands/GameStateExt.cpp#L1279-L1288`); the `distance`, `setDammage`, `saveVar`,
  `exit` and `exec` rows; `ArcadeTemplate::IsConsistent` for seat counting and the no-player rule; `WorldInit.cpp` (`this` is the
  unit); `DisplayUI.cpp` (`init.sqf`); and that every file path cited in `references/sources.md` exists.
- **Primer size.** Before the review below, `SKILL.md` measured 1,199 words and its description 591 characters. After it, the file
  measures 1,200 words (whitespace-separated tokens over the whole file, frontmatter included) and about 8,150 characters, and the
  description 564 characters. The token figure is an estimate [I].
- **Not verified:** anything on 1.99; retrieval quality; the effect of the revised primer; the diagnostic and tool names, which are
  proposals.

### Adversarial review (2026-09-27)

A second pass re-checked every engine claim in `skills/mission-primer/` against both pinned clones, recomputed §3, and checked the
skill against the Agent Skills specification.

- **Confirmed in both clones:**
  - SQS line classes and the 4,096-byte buffer; `exit`; `goto` exits on an unknown label.
  - Statement splitting and the field check modes: a top-level comma fails only in check mode, and acts as a separator at runtime.
  - Trigger `this`/`thisList` and activation None; `this` is the unit in init lines.
  - Seat counting, the 100 m auto-join and `version=11`.
  - Section order and the text-only editor.
  - The END/LOOSE evaluation (LOOSE is checked first); death as `EMKilled`.
  - `saveVar` and the chapter fallback; `objStatus` and its unknown-word default.
  - The briefing parser rules and section names.
  - The command registrations behind the "Not in this engine" list (quoted names and stringifying macros both searched) and the
    "Remastered only" list.
- **Corrected in the primer and its references:**
  1. **Test verbs and path escapes.** The line "No `tri*` test commands, and no paths …" read as engine absence. These are editor
     policy (doc 24): the verbs exist, and the engine does not confine paths. It is now phrased as a rule. It also names `endGame`,
     which is registered on CWR and closes the application (`CWR:Game/Commands/GameStateExt.cpp#L886`;
     `CWR:Game/Commands/GameStateExtWorld.cpp#L787-L803`; CE gated it as `triEndGame`).
  2. **`forceEnd`.** "No script command picks an ending (not even `forceEnd`)" became a statement of what `forceEnd` actually does:
     it lets an ending that is already set proceed without waiting for camera and title effects
     (`CWR:UI/DisplayUIMenus.cpp#L984-L985`). The gated test verb `triEndMission` can force an ending
     (`CWR:Game/Commands/GameStateExtTestAudio.cpp#L2075-L2092`); the `tri*` ban covers it.
  3. **Preprocessing.** "There is no preprocessor" became "SQS is not preprocessed". `preprocessFile` does run a C-style
     preprocessor (`CWR:Game/Commands/GameStateExtWorldConfig.cpp#L1081-L1091`), while `loadFile` and `init.sqf` are raw.
  4. **`init.sqf`.** "Only in the Remastered build" was ambiguous for CE. It now reads "raw, and only on CWR and CE"
     (`CE:UI/DisplayUI.cpp#L131-L132`).
  5. **IDs.** "IDs change on every load and save" overstated the behaviour. `Compact` closes gaps, so IDs *may* be renumbered
     (`CWR:AI/ArcadeTemplateFind.cpp#L882-L1045`).
  6. **`thisList`.** "The units that passed its test" was wrong for "not present" triggers, whose list holds the units found. It
     now reads "the matching units it found" (`CWR:World/Detection/Detector.cpp#L914-L921`).
  7. **Briefing file names.** "Per-language … names are Remastered features" was unverifiable for 1.99. It now names the CWR/CE
     lookup order and marks per-language `.html` as unconfirmed for 1.99.
  8. **The `debriefing` value.** The skeleton now explains how the value is read, including that a non-numeric word reads as 0 on
     CWR and CE.
  9. **Fact table.** `sources.md` rows P2.11, P3.2, P3.8, P3.11, P3.13, P4.8, P5.2, P5.4, R3 and R4 were updated to match. The
     P3.2 table row was also repaired: an unescaped `||` split the cell.
- **Corrected in this doc:**
  1. **T12 count.** "0 passes in 8 answers with any help" is 6 answers with help, 8 in total.
  2. **The "10 of 16" residue.** It is now split into 8 syntax or structure errors and 2 non-portable config values, because the
     CWR/CE source reads `debriefing = false;` as 0 (open question 6 is partly answered).
  3. **The `nil` row.** "`myVar == nil`" was listed as a later-title command, but `nil` is registered here. The real fault is that
     any comparison with nil returns nil.
  4. **TL;DR caveats.** The TL;DR now says that the cards result is an upper bound from perfect cards, and that the primer numbers
     are for the untested-since draft.
  5. **SPEAC.** The summary now says that its repair targets the intermediate language and that the result comes from one case
     study.
  6. **New limitations.** Reproducibility, post-hoc grouping and the hallucination flag were added to §3.6.
- **Recomputed and unchanged:**
  - Every per-condition total from the §3.3 matrix.
  - All five Wilson intervals (z = 1.96, n = 24).
  - All partial-credit scores and hallucination percentages.
- **Spec and hygiene:**
  - `name: mission-primer` is lowercase with hyphens, matches its folder, and uses no trademark.
  - The description is 564 of 1,024 allowed characters.
  - `metadata` values are all strings.
  - `license` is set.
  - The body is 82 lines, under the recommended 500.
  - A search of the doc and the skill folder found no private project names.
- **Still open:** everything on 1.99; the `saveVar` object loss (inferred from reference serialisation, not probed); the
  synchronisation semantics (read, not run); and the `false` reading (source only, not probed).
