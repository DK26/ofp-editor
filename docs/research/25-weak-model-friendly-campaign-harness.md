# Weak-Model-Friendly Campaign Harness: Describe → Generate → Refine

Research doc 25 for `ofp-editor`. Research date: 2026-09-26; adversarial review 2026-09-27. Audience: contributors and LLM coding agents. This file is meant to be read on its own.
Question answered: how can **weak (small, local) language models** reliably finish a long, structured, creative job such as a whole branching
campaign, and how should our harness and workflows be designed so that this works, is fun, and is always correct?

**Epistemic legend.** **[V]** = verified against a primary source (arXiv id, paper, official page, or a repo doc whose own citation was verified;
given inline). **[I]** = inferred by us; every design proposal in §4–§11 is [I] unless marked. **[U]** = unknown, needs measurement.
**Relation to sibling docs.** The typed campaign model, the CXL condition language, lints C01–C21, the simulator and the vanilla compiler are in
`19-campaign-designer-ux-and-state-model.md` (doc 19); engine campaign facts are in doc 18; model tiers and effort presets are in doc 14; local
inference and constrained decoding are in doc 13; prior art (BriefingRoom, academic PCG) is in doc 15; Iron Curtain's generation ideas are in
doc 17; plugins are in doc 22. This doc does not repeat them. It designs the **workflow layer** that drives a model through them.

**Glossary.** *Decision point*: one model call that returns one typed answer. *Menu*: a code-computed list of options that are all valid.
*Fact provider*: a deterministic editor function that answers a question about the catalog, island, engine limits, campaign or story.
*Digest*: the small, code-built slice of state that a prompt carries. *K*: candidates sampled per decision. *R*: repair turns per decision.
*Bundle*: a class of reachable campaign states that the explorer treats as one (doc 19 §6.4). *Story bible*: the typed tables of characters,
factions, places, items, events and threads. *T1/T2/T3*: local small / local medium / cloud frontier model tiers (doc 14 §6).

## TL;DR

- **Validity must be a property of the harness, not of the model.** A campaign draft needs roughly 200–300 small decisions [I, §4.5]. At a
  95% per-decision success rate, 40 unguarded decisions all succeed only 13% of the time (0.95^40) [I, arithmetic]; a 2026 synthesis of 27
  agent benchmark, taxonomy and audit papers finds that "failures compound nonlinearly with task length" [V, arXiv 2607.05775]. So code
  guarantees that every admitted step is valid, and the model can only change *quality*. The same synthesis finds that "additional scaffolding
  does not consistently improve reliability" [V], so the harness must beat a single-prompt baseline in our own evaluation (§11.2).
- **The literature agrees on the architecture.** Autoregressive LLMs "cannot, by themselves, do planning or self-verification", but work well
  when paired with external verifiers (LLM-Modulo, arXiv 2402.01817) [V]. On TravelPlanner GPT-4 alone reached 0.6% [V, 2402.01622]; the same
  task reached 93.9% when the LLM translates constraints for a formal solver [V, 2404.11891]. A fine-tuned 1.7B planner scored 82.9% in-domain and
  **0% on two unseen domains** [V, 2601.14456]. Our campaign graph, state and missions are therefore planned and checked by code, and the model fills
  bounded slots.
- **Menus beat free generation for weak models.** When every option is valid by construction, a wrong pick is merely *suboptimal*, never
  broken [I]. Offering fewer tools "significantly improves" small-model function calling [V, 2411.15399]; LLMs show position "selection bias" in
  multiple choice [V, 2309.03882], so menus are short, shuffled, and labelled with neutral letters mapped to real IDs by code. More than half
  of the vanilla Unit dialog's lists are longer than 7, so catalog menus are split into facet steps (side → kind → role group → role) rather than truncated (§6.2).
- **Constrain the answer, not the thinking.** Constrained decoding raised Llama-3.1-8B task accuracy (GSM8K 80.1% → 81.6–83.8% across four
  engines) in JSONSchemaBench [V, 2501.10868], but strict format constraints can hurt reasoning [V, 2408.02442] and grammars can distort the model's
  distribution [V, 2405.21047]. Remedy: a short free `why` field *before* the answer, small flat schemas, dynamic enums, and an explicit
  `none_fit` / `ask` escape (CRANE, 2502.09061; dottxt's rebuttal) [V/I].
- **Sample-then-verify is the strongest lever for weak models; self-critique is not.** With an automatic verifier, repeated sampling lifted
  SWE-bench Lite from 15.9% to 56% [V, 2407.21787], and compute-optimal test-time scaling (with a process reward model as the verifier) let a
  1B model beat a 405B one on MATH-500 [V, 2502.06703]. Sampling only helps where the model is sometimes right, so steps stay small (§5).
  Without external feedback, LLMs "struggle to self-correct" [V, 2310.01798; 2406.01297]. So acceptance comes only from deterministic
  verifiers; repairs quote one precise finding and are bounded.
- **The harness holds the state; each call is fresh and small.** When a task arrives piecemeal over several turns, LLMs lose 39% on average
  versus one fully specified turn [V, 2505.06120], and accuracy drops with context length [V, 2502.05167; Chroma "Context Rot"]. Every
  decision point gets a new prompt of ~1–4K tokens [I] built from typed tables, never from a model-written summary.
- **Step shape adapts to the model; budgets adapt to effort.** Four step shapes: *Pick* (one letter from a menu), *Fill* (a small typed
  record), *Compose* (a sub-structure such as one mission plan), *Draft* (a whole branch as a ChangeSet). Each model is **qualified per step**;
  a failed bigger step is automatically decomposed into smaller ones, ADaPT-style (arXiv 2311.05772) [V/I]. Effort sets K, R, verification
  passes and user gates (§5).
- **The draft is compilable from the first minute.** Code builds a default campaign (skeleton + template missions + template text) that
  already passes all lints; the model upgrades pieces one decision at a time. A failed decision leaves a valid default, flagged, never a
  hole (§10).
- **Consistency lives in a typed story bible**, not in the context window: characters, places and events carry path conditions, text stores
  entity *tokens* (so renames never need regeneration), and mention lints use simulator facts ("Dimitri may be dead here") (§8).
- **Human edits are sacred by construction:** per-field provenance, pinning, and a field-level three-way merge keyed by stable IDs, where a
  field the human changed, pinned or explicitly chose always wins unless the user explicitly asks otherwise (§9). Every generated element opens
  an inspector with its decision record: menu, pick, the model's `why`, verifiers, repairs and dependents (§9.1).
- **Fun is designed in**, not hoped for: premise cards, idea rerolls, seeded variety from code (LLM outputs are homogeneous across and within
  models [V, 2510.22954]), a campaign book that fills as you watch, and a what-if playthrough at every stage (§4, §10).
- **Evaluation must prove the weak-model claim** with per-step and end-to-end instruments scored on typed diffs and lints, run at 3–4B,
  8–9B, 27B+ and frontier, against no-model, random-menu and always-ask controls, reporting pass^k (τ-bench, arXiv 2406.12045) (§11).

## 1. What "a weak model succeeds" has to mean

| Property | Owner | Target | Why |
| --- | --- | --- | --- |
| **Valid**: compiles for the target profile; lints C01–C21 clean at error level; missions pass the mission validators (doc 19 §6.5, §7) | Harness | 100% at every model tier, including no model | AGENTS.md "Correct by construction" |
| **Faithful**: the typed brief (side, islands, length, features, tone) is honoured | Harness + model | Checkable expectations per brief (§11) | Users judge the tool by whether it listened |
| **Coherent**: no contradictions across paths (dead characters, timeline, places) | Harness lints + model | Zero error-level consistency lints | Long-form generation drifts without structure (§2.9) |
| **Fun / good**: premise, variety, voice, pacing | Model + user | Human panel preference over the no-model baseline | Quality is where model size shows |
| **Editable**: every element is a normal editor object with provenance | Harness | 100% | AGENTS.md "Partial regeneration never clobbers human work" |

The first and last rows are never delegated to a model. The harness is judged by rows 1 and 5 (binary), models by rows 2–4 (graded) [I].

## 2. Evidence survey (2023–2026, plus a few foundational papers)

### 2.1 Decomposition, plan-then-fill and hierarchical generation

| Work | Finding | Consequence for us |
| --- | --- | --- |
| Least-to-Most prompting (Zhou et al., arXiv 2205.10625) | Solving subproblems in order: SCAN "at least 99%" with 14 exemplars vs 16% for chain-of-thought [V] | Order steps so each depends only on already-admitted answers |
| Plan-and-Solve (Wang et al., 2305.04091) | Plan first, then execute: beats zero-shot CoT on all tested datasets [V] | Plan (skeleton) before content |
| Decomposed Prompting (Khot et al., 2210.02406) | Specialised sub-prompts per sub-task beat monolithic few-shot prompting [V] | One prompt template per decision type |
| Skeleton-of-Thought (Ning et al., 2307.15337) | Skeleton first, then expand points in parallel: "considerable speed-ups across 12 LLMs" [V] | Once the skeleton is fixed, missions and text slots expand independently and in parallel |
| ADaPT (Prasad et al., 2311.05772) | Decompose only "when the LLM is unable to execute" a sub-task; adapts "to both task complexity and LLM capability"; up to +28.3% ALFWorld, +27% WebShop, +33% TextCraft [V] | **As-needed decomposition** is our capability adaptation (§5.1) |
| DSPy (Khattab et al., 2310.03714) | Compiled pipelines with bootstrapped demonstrations: small models "competitive with approaches that rely on expert-written prompt chains for proprietary GPT-3.5" [V] | Optimise exemplars offline per step and per model tier (§4.6) |

### 2.2 Planning with external solvers and verifiers

| Work | Finding | Consequence |
| --- | --- | --- |
| LLM+P (Liu et al., 2304.11477) | LLM translates to PDDL, a classical planner solves: "optimal solutions for most problems, while LLMs fail to provide even feasible plans for most problems" [V] | Structure (graph shape, reachability, coverage) is computed, not generated |
| Guan et al. (2305.14909) | GPT-4 builds PDDL models "for over 40 actions"; the *corrected* models then solve 48 tasks with a planner [V] | Frontier models may *author* structure (Draft shape), always behind the solver/linter |
| LLM-Modulo (Kambhampati et al., 2402.01817) | LLMs are "approximate knowledge sources" in a generate-test loop with "external model-based verifiers" [V] | Our whole loop: propose → verify → critique with precise errors → re-propose |
| LLM-Modulo on TravelPlanner (Gundawar et al., 2405.20625) | 4.6× over baseline for GPT-4-Turbo; GPT-3.5-Turbo from 0% to 5% [V] | Verifiers multiply a strong model's success but cannot rescue a weak model given big steps; **weak models also need small steps** [I] |
| Hao et al. (2404.11891) | LLM + formal verification tools: 93.9% on TravelPlanner vs 10% for o1-preview [V] | Hard constraints belong in solvers and checkers |
| ChatHTN (Muñoz-Avila et al., 2505.11814) | Interleaves symbolic HTN decomposition with LLM decompositions and is "provably sound" [V] | Campaign → acts → nodes → mission plan is an HTN whose methods are code; the model chooses among methods |
| Generalization gap (Belcamino et al., 2601.14456) | Fine-tuned 1.7B planner: 82.9% valid plans in-domain, 0% on two unseen domains; sensitive to surface form [V] | Do not rely on a small model's planning, even if fine-tuned |
| PDDLCoder (Laule et al., 2608.16637) | Agentic PDDL generation: 89.6% vs 45.3% (prior) and 74.5% (direct LLM) [V] | Tool-assisted formalisation keeps improving; still verifier-gated |

### 2.3 Choosing from a menu versus generating freely

- Presenting question and options jointly helps models with good "multiple choice symbol binding" (Robinson, Rytting & Wingate, 2210.12353)
  [V], and models suffer "selection bias" toward particular option IDs; the authors' PriDe fix estimates that prior by permuting options
  (Zheng et al., 2309.03882) [V]. → Shuffle options per sample; aggregate across permutations when voting [I].
- "Selectively reducing the number of tools available to LLMs significantly improves their function-calling performance" on edge devices
  (Paramanayakam et al., 2411.15399) [V]. Gorilla documents hallucinated API usage and wrong arguments (2305.15334) [V]. → Menus are short
  (default ≤ 7 options plus escapes [I]); the model never types a class name, coordinate or ID.
- Verification is not free either: GPT-4 is generator-validator consistent "only 76% of the time" (2310.01846) [V]; models can generate
  better than they understand (West et al., 2311.00059) [V]; and "a variant of the generation-verification gap scales monotonically with the
  model pre-training flops" (Song et al., 2412.02674) [V]. → A small model is a poor *judge*. It should pick among options whose validity code
  already proved, so its pick expresses fit and taste, not correctness [I].

### 2.4 Grammar and JSON-schema constrained decoding

| Evidence | Direction |
| --- | --- |
| Grammar-constrained decoding lets LMs "substantially outperform unconstrained LMs" on structured NLP tasks (Geng et al., 2305.13971) [V] | Gain |
| JSONSchemaBench, Llama-3.1-8B-Instruct: GSM8K 80.1% unconstrained vs 81.6–83.8% across Guidance, llama.cpp, Outlines, XGrammar; Last Letters 50.7 → 51.2–54.0; Shuffle Objects 52.6 → 52.6–55.9 (llama.cpp no gain; Guidance best) [V, 2501.10868 HTML v3, Table 8] | Small gain (≤ 3.7 points) |
| Same paper: coverage of real schemas differs (GlaiveAI 0.93–0.96; "GitHub Hard" Guidance 0.41, Outlines 0.03); XGrammar had the most under-constrained failures [V] | Keep schemas simple; test the engine's coverage |
| "Let Me Speak Freely?": "significant decline in LLMs reasoning abilities under format restrictions"; stricter formats degrade more (Tam et al., 2408.02442) [V] | Loss |
| dottxt rebuttal (Kurt, 2024): with aligned prompts and a reasoning field, Llama-3-8B structured ≥ unstructured (GSM8K 0.78 vs 0.77, Last Letter 0.77 vs 0.73, Shuffle 0.44 vs 0.41) [V, blog.dottxt.ai] | Gain if done right |
| CRANE (Banerjee et al., 2502.09061): strict grammars can diminish reasoning; alternating free reasoning and constrained output gives up to +10 points [V] | Constrain the answer, free the thinking |
| Grammar-Aligned Decoding (Park et al., 2405.21047): constrained decoding "can distort the LLM's distribution", producing grammatical but low-quality outputs [V] | Forcing a model into options it finds implausible produces junk: offer `none_fit` |
| llama.cpp's built-in schema converter puts required properties first and silently ignores unsupported keywords; llguidance errors instead [V per doc 13 §4] | Mark every property required so declared key order (`why` before `pick`) survives, or use llguidance |
| NPC-dialogue scaffolding effects were "role-dependent": tight constraints stabilised a quest-giver but made suspects less believable (arXiv 2510.25820, doc 15 §9) [V] | Strict for facts, loose for voice |

### 2.5 Sampling, voting, verifiers and repair

| Work | Finding | Consequence |
| --- | --- | --- |
| Self-consistency (Wang et al., 2203.11171) | Majority vote over sampled reasoning paths: GSM8K +17.9%, SVAMP +11.0%, AQuA +12.2% [V] | Voting helps when answers are discrete (Pick steps) |
| Soft Self-Consistency (Wang et al., 2402.13212) | "When tasks have many distinct and valid answers, selection by voting requires a large number of samples"; likelihood-based scores need half the samples [V] | Do not vote on creative text; for local models, use option log-probabilities (doc 13 §4 item 6) as a soft score |
| Large Language Monkeys (Brown et al., 2407.21787) | Coverage "scales with the number of samples over four orders of magnitude"; with automatic verification SWE-bench Lite 15.9% → 56% at 250 samples; without verifiers, voting and reward models "plateau beyond several hundred samples" [V] | K candidates + deterministic verifiers is the main lever; our verifiers are exact |
| Snell et al. (2408.03314); Liu et al. (2502.06703) | Test-time compute can "outperform a 14x larger model" on problems where the small model already has moderate success; "a 1B LLM can exceed a 405B LLM on MATH-500" with a process reward model [V] | Spend local compute on K and verification rather than demanding a larger model, but only on steps small enough that the model is sometimes right |
| Huang et al. (2310.01798); Kamoi et al. (2406.01297) | No reliable self-correction "without external feedback"; it works with "reliable external feedback" [V] | Self-review is never an acceptance gate |
| Self-Debugging (Chen et al., 2304.05128); Olausson et al. (2306.09896) | Feedback from execution helps (up to +12%); self-repair gains are "often modest" once cost counts, bottlenecked by feedback quality [V] | Repairs quote one precise, machine-produced finding; budgets are small |
| LLM judges (Zheng et al., 2306.05685; Panickssery et al., 2404.13076) | "position, verbosity, and self-enhancement biases"; judges favour their own generations [V] | A model judge may order candidates, labelled advisory; it never admits one |

### 2.6 Externalised state and context budgets

- "LLMs Get Lost in Multi-Turn Conversation": "average drop of 39% across six generation tasks" when an underspecified task is revealed over
  several turns, versus one fully specified turn; models "get lost and do not recover" (Laban et al., 2505.06120) [V].
- "Lost in the Middle": accuracy is highest when relevant information is at the beginning or end (Liu et al., 2307.03172) [V]. NoLiMa: at 32K
  tokens "11 models drop below 50% of their strong short-length baselines", of 13 tested (2502.05167) [V]. Chroma's "Context Rot" (18 models, 2025-07-14):
  performance "grows increasingly unreliable as input length grows" [V].
- MemGPT treats the context window as managed memory over external storage (Packer et al., 2310.08560) [V]; Iron Curtain keeps a campaign context
  document that the LLM itself compresses (doc 17 §9.1) [V].
- **Consequence [I]:** one fresh single-turn prompt per decision; the digest is computed from typed tables (never model-written summaries, which
  would launder errors into state); the task and the answer schema go at the start and end of the prompt.

### 2.7 Exemplars and retrieval

Similar in-context examples help strongly (Liu et al., 2101.06804: +41.9% ToTTo, +45.5% NQ) [V]; exemplar order alone moves results (Lu et al.,
2104.08786) [V]; DSPy bootstraps demonstrations per module (2310.03714) [V]. **Consequence [I]:** each decision type has an exemplar library of
admitted, human-approved answers (from our synthetic fixtures and, opt-in, the user's own accepted choices), retrieved by beat, side, era and tone,
with 1–3 exemplars for small models and a fixed order per model qualified offline.

### 2.8 Small-model tool calling and its failure modes

- Official BFCL V4 (last updated 2026-04-12; `data_overall.csv` re-read 2026-09-27, 109 rows): multi-turn accuracy 22.12% for
  Qwen3-4B-Instruct-2507 (FC), 41.75% for Qwen3-8B (FC), 68.38% for Claude-Opus-4-5 (FC) [V]. τ-bench: agents "succeed on <50% of the
  tasks", pass^8 < 25% in retail (2406.12045) [V].
- A 12-category taxonomy over 1,980 deterministic tests found tool-*initialisation* failures the main bottleneck for smaller models; qwen2.5:14b
  reached 96.6% on commodity hardware (Huang et al., 2601.16280) [V]. Small agents make "structural errors such as missing required observations,
  performing premature writes, repeating failed calls" (Li et al., 2609.28003) [V]. When2Call evaluates when to call, ask, or decline
  (2504.18851) [V]; ToolBeHonest scored 2024's Gemini-1.5-Pro and GPT-4o at 45.3 and 37.0 of 100 on tool-hallucination diagnosis
  (2406.20015) [V].
- A position paper argues that small models are "sufficiently powerful" for many agentic sub-tasks (Belcak et al., 2506.02153) [V]. It is an
  argument for narrow, well-scoped calls, not a measurement, and it matches the design below [I].

| Failure mode | Harness countermeasure [I] |
| --- | --- |
| Hallucinated IDs, classes, coordinates | The model sees letters mapped to code IDs; dynamic enums in the grammar; unknown values cannot be emitted |
| Wrong or missing arguments | Fill schemas are small, flat and typed; ranges come from code; admission rejects and re-asks with one finding |
| Format drift, malformed JSON | Constrained decoding; else JSON mode + parse + one repair (doc 13 §4); truncated output is never executed |
| Omission (answers in prose instead of acting) | There is no tool choice to make: each decision point has exactly one answer schema |
| Loops and repeated failed calls | The harness owns the loop: fixed K and R, stop when the same finding recurs, cycle fingerprinting |
| Premature stopping | Completion is a code gate (every node admitted + lints clean), not a model claim |
| Failing to ask | Code computes when to ask (missing required field, `none_fit`, low option margin, budget exhausted); the model's own `ask` option is a bonus |
| Lost state across turns | No multi-turn dialogue: each decision is single-turn over a fresh digest |

### 2.9 Long-form, branching and procedural narrative

| Work | Finding | Consequence |
| --- | --- | --- |
| Hierarchical story generation (Fan et al., 1805.04833) | Premise → story preferred 2:1 over non-hierarchical [V] | Premise first |
| Re3 (2210.06774); DOC (2212.10077) | Plans and detailed outlines: +14% and +22.5% absolute plot coherence [V] | Outline-conditioned slot filling |
| Dramatron (2209.14958); Agents' Room (2410.02603) | Hierarchical co-writing with 15 professionals; specialised sub-agents for narrative [V] | Per-role prompts: premise, character, beat, briefing, radio |
| DOME (2412.13575) | A temporal-knowledge-graph memory reduces contextual conflicts; a "Temporal Conflict Analyzer" on the same graph evaluates consistency [V] | Story bible with timeline and path conditions (§8) |
| PLOTTER (Gu et al., 2604.21253) | Evaluate-Plan-Revise on event and character **graphs**, not text [V] | Plan the campaign as a typed graph; text last |
| GENEVA (Leandro et al., 2311.09213) | GPT-4 generates "branching and reconverging storylines", writing the narrative and then rendering it as a graph (two steps) [V] | We invert the order: code owns the graph shape, content comes second; model-written graphs only as a qualified Draft shape |
| WHAT-IF (Huang et al., 2412.10582) | Meta-prompting explores branches of a linear plot; graph storage [V] | "What if" branch proposals on an existing campaign (refine stage) |
| ASP-guided stories (Wang & Kreminski, 2406.00554); StoryVerse (2405.13042) | Answer set programming outlines give "more diverse stories than an unguided LLM"; narrative planning mediates author intent [V] | Seeded symbolic outline generator as the source of variety |
| Narrative planning benchmark (Wang & Kreminski, 2506.10161) | GPT-4-tier models are causally sound at small scale; intentionality and conflict remain hard [V] | Causality from code (preconditions/effects); the model supplies motives and voice |
| SLM game content (Munk et al., 2601.23206) | "more difficult tasks require narrower scope and higher specialization to the training corpus"; retry-until-success reaches adequate quality with predictable latency [V] | Narrow slots + retries for 3–4B models; their SLMs were specialised, so general instruct models must be measured (§11) [I] |
| Word2World; Värtinen et al. (doc 15 §9) | Decomposition matters; one in five GPT quest descriptions acceptable to a critic [V] | Humans choose among candidates |
| Artificial Hivemind (Jiang et al., 2510.22954); Luminate (Suh et al., 2310.12953) | "intra-model repetition" and "inter-model homogeneity"; chat UIs push "rapid convergence on a limited set of ideas" [V] | Variety comes from code (seeds, archetype menus, farthest-point selection) and from showing the user alternatives |
| BriefingRoom (doc 15 §8.1) | Deterministic staged generator with per-stage retries and fallbacks, no LLM [V] | The no-model baseline must already produce a playable campaign |

### 2.10 Verdicts

| Technique | Verdict | Where |
| --- | --- | --- |
| Code-owned hierarchical state machine (HTN-like) with model slot filling | **Adopt** | §4 |
| Menus of code-validated options; letters mapped to IDs; shuffle; `none_fit`/`ask` escapes | **Adopt** | §6 |
| Grammar/JSON-schema constrained answers with a leading bounded `why` field | **Adopt** | §4.4 |
| K candidates → deterministic verifiers → deterministic/advisory ranking → user pick | **Adopt** | §7 |
| Majority voting | **Adapt**: Pick steps only, across permuted menus; never for text | §7.3 |
| Bounded repair with one precise finding per turn | **Adopt** | §7.2 |
| Model self-critique, model judge | **Adapt**: advisory ordering or a "concerns" note only; never acceptance | §7.3 |
| Long agent conversation that carries campaign state | **Avoid** | §2.6 |
| Model-written summaries as memory | **Avoid**; code-built digests from typed tables | §8 |
| Small model planning a whole campaign graph | **Avoid** as a requirement; allowed as a qualified Draft shape for strong models | §5 |

## 3. Design principles

1. **Always valid.** Every stage leaves a campaign that compiles and passes error-level lints; generation *upgrades* defaults (§10).
2. **Code owns facts, structure and limits; the model owns taste and words.** In Pick/Fill steps the model never produces a class name,
   coordinate, ID, count, guard operator or engine key; it chooses among them or fills a typed slot whose range code computed. Compose/Draft
   steps (qualified models only, §5.1) may write CXL or typed actions, but every identifier must resolve against declared tables and every
   command passes the same verifiers; a weak model is never routed to them.
3. **One decision, one schema, one fresh prompt.** Single-turn calls over a digest; no conversational state in the model.
4. **Acceptance is deterministic.** Verifiers admit; models, judges and votes only order candidates.
5. **Degrade downward, never upward.** When a step fails, shrink the step (Compose → Fill → Pick → ask the user or keep the default); never silently
   switch to a bigger or cloud model. Offering a stronger model is a user choice.
6. **Human work wins.** Human-edited or pinned fields are inputs to regeneration, never outputs of it.
7. **The user directs.** Short loops that show something new (a premise card, a graph, a mission on the map, a playthrough) beat long silent runs.
8. **Same path as the user.** Every admitted answer becomes a typed, undoable editor command (doc 19 §8; AGENTS.md).

## 4. The campaign workflow state machine

### 4.1 Stages

`describe → outline → missions → text → verify → preview → refine` maps onto ten code-owned stages. Each stage is a sub-machine of decision
points; each ends with a completion gate and an optional user gate.

| # | Stage (user-facing name) | Input | Output (typed) | Model's job (weak default shape) | Code's job | Completion gate |
| --- | --- | --- | --- | --- | --- | --- |
| S0 | **Describe**: intake | Free text, installed islands and catalog | `CampaignBrief` | Fill brief fields that the text states, each with a literal quote (Fill) | Check quotes are substrings; resolve islands/sides/eras against the catalog; apply code defaults as visible "assumption" chips; compute questions for missing required fields; flag engine-impossible wishes (e.g. "branch when the player dies", doc 18) with alternatives | All required fields set by user, text or default |
| S1 | Premise | Brief | `Premise` (logline, protagonist unit, antagonist faction, inciting incident, stakes, tone preset) | Pitch 3 premise cards by filling a premise template; the user picks or rerolls (Fill ×3) | Archetype menus by side/era; lints (length, codepage, anachronism) | User pick, or seeded default |
| S2 | Story bible | Premise, brief | `StoryBible` rows (§8) | One character/faction/place row per call: name, traits, speech style (Fill); pick a home town from a menu (Pick) | Roster slots from the brief's tier; unit class and rank from faceted catalog menus (§6.2); places bound to island `Names`, or to fallback clusters where an island has none (§6.1); uniqueness | Bible lints clean |
| S3 | **Outline**: skeleton | Brief, bible | Campaign graph: nodes, outcomes, edges, endings (doc 19 §4.2) | Pick a graph shape from a menu; pick a beat per node from a beat menu; name nodes (Pick/Fill) | Shape library parameterised by length and complexity tier (doc 19 §6.8); instantiate; enforce totality (C02/C03), endings (C10), no livelock (C09); prefer shapes with ≤ 7 sockets per mission and show each router the compiler must add (C11/C12: +1 book row, +1 short load, doc 19 §6.2) on the shape card | Lints clean; user approves the Flow view |
| S4 | State schema | Skeleton, brief features | Declared variables, roster, pools, guards, effects | Pick consequence archetypes (reputation counter, intel flags, squad roster, weapon pool, doom clock) from a menu; fill guard constants inside computed ranges (Pick/Fill) | Declare typed vars (doc 19 §4): guards use `Bool`/`Int`/`Enum`/`Set` only (string `==` is case-insensitive, F3); object/group values are never persisted (doc 18 §7); instantiate guard/effect CXL templates; typecheck (C06), intervals (C17), coverage (C03), `.sqc` growth (C20) | CXL clean; explorer finds every ending reachable |
| S5 | **Missions**: concept | Node beat, bible digest | `MissionConcept`: site, scene template, conditions | Pick site from the fact-provider menu; pick a compatible scene template; fill enums (time, weather, enemy strength band) (Pick/Fill) | Site menus (§6); template compatibility; map each template outcome to the node's outcomes (menu) | Every node outcome has a template outcome |
| S6 | Missions: build | `MissionConcept` | Real `mission.sqm` content + sidecar | None (Deterministic) | Seeded generator instantiates groups, waypoints, triggers, markers, outcome sockets and roster slots (docs 15 §8.3, 17 §6, 19 §6.6) | Mission validators clean |
| S7 | **Text** | Mission, bible digest, reachable bundles | Briefing sections, `OBJ_` variant lines, ≤ 7 debrief narratives per mission, dialogue and radio rows, stringtable entries | One slot per call, K candidates; variant lines per state bundle (Fill) | Slot specs (length, codepage, channel, tone); speaker menus; entity tokens; keys; SQS glue | Text lints clean; C21 variant coverage |
| S8 | **Verify** | Whole model | Findings, compile preview | None | Full compile for the target, whitelist, line limits, simulator vs lowering, round-trip, Path Explorer (doc 19 §7.1) | Zero errors |
| S9 | **Preview** and **Refine** | Compiled campaign; user requests | Played missions; scoped regeneration | Interpret a typed-in request as a `RefineRequest` (Fill; scope picked from a menu of existing elements), then rerun the affected stages. The same request can be built from context menus with no model | Scope, staleness, merge (§9) | Same gates as the stages it reran |

### 4.2 Rust sketch (crate `ofp-campaign-flow`; proposal-only)

```rust
/// A code-owned workflow run. Persisted in the campaign sidecar so it can pause, resume and be replayed; the model never sees it whole.
pub struct CampaignFlow { run: FlowRunId, stage: Stage, base: CampaignRevision, log: Vec<DecisionRecord> }
pub enum Stage { Intake(IntakeState), Premise(PremiseState), Bible(BibleState), Skeleton(SkeletonState), Schema(SchemaState),
                 Concepts(PerNode<ConceptState>), Build(PerNode<BuildState>), Text(PerSlot<TextState>), Verify(VerifyState), Refine(RefineState) }

/// One bounded question to a model. Everything except the model's answer is computed by code before the call.
pub struct DecisionPoint { id: DecisionId, kind: DecisionKind, shape: StepShape, menu: Option<Menu>, schema: SchemaId,
                           digest: DigestSpec, exemplars: ExemplarQuery, verifiers: Vec<VerifierId>, budget: StepBudget, fallback: Fallback }
pub enum StepShape { Deterministic, Pick, Fill, Compose, Draft }
pub struct StepBudget { candidates: NonZeroU8, repairs: u8, verify: VerifyDepth }
/// What happens when the budget is spent. There is deliberately no "call a bigger model" variant.
pub enum Fallback { Decompose(Vec<DecisionKind>), KeepDefault, AskUser(QuestionSpec) }
pub enum DecisionState { Pending, Sampled(Vec<Candidate>), Admitted(Checked<Answer>), NeedsInput(Question), Defaulted(Answer), Stale }
/// Only verifiers construct `Checked<T>` (private constructor), so unchecked model output cannot reach the command bus.
pub struct Checked<T> { value: T, findings_resolved: u8, revision: CampaignRevision, read_set: ReadSet }
```

Invariants [I]: a `Checked<T>` records the revision and the elements its digest and verifiers read (`read_set`). If the user edited any of
them meanwhile, it is re-verified against the current revision before admission, and dropped if it now fails or its target became human-edited
or pinned. Unrelated edits never block it, so the user can keep editing while a run fills the campaign. Every model decision is immediately
followed by its verifiers; nothing downstream reads a raw model string.

### 4.3 Per-step schemas (examples)

**S0 intake (Fill).** Every field is optional, and every filled field carries the quoted words that justify it:

```json
{ "side":      {"value": "EAST", "quote": "as a Soviet paratrooper"},
  "islands":   [{"value": "island#2", "quote": "on Kolgujev"}],
  "length":    {"value": "medium_6_9", "quote": "about eight missions"},
  "tier":      {"value": "rpg", "quote": "my squad should carry over"},
  "features":  [{"value": "roster", "quote": "my squad should carry over"}],
  "tone":      null, "branching": null }
```

Code rejects a field whose `quote` is not a substring of the request (after case, whitespace and Unicode normalisation, so CZ/PL/RU briefs
work), turns `null` required fields into a question card with computed options (installed islands, sides present on them), and shows
defaults for optional ones as editable assumption chips [I].

**S5 site pick (Pick).** Prompt digest, then a menu whose options are all valid (synthetic fixture names):

```text
TASK  Choose where the ambush in node m04 "Night Road" takes place.
STORY The convoy carries the defector (char#3 Major Orlov). Player side: EAST, 1985, night.
OPTIONS (all valid for this beat)
  A  Road bend in forest, 1.1 km NE of Novy Dvor; cover on both sides; convoy speed low
  B  Bridge over the Sava stream, S of Dolina; open ground to the west
  C  Hill road near Hill 243; overwatch from the crest; exposed descent
  X  None of these fit the story (explain)
Answer as JSON: {"why": "<= 25 words", "pick": "A" | "B" | "C" | "X"}
```

The grammar allows exactly `A|B|C|X`; `why` comes first so the model reasons before committing (§2.4), and it is bounded. Code maps `A` to the
site record. `X` triggers a re-menu with different diversity seeds, then a user question [I].

**S7 text slot (Fill).** Code supplies the speaker (`sgt_kovac`, side channel), length cap, tone and required facts; the model writes only the line:

```json
{ "why": "terse, tense; the defector must survive", "text": "Two trucks, no escort. Nobody fires until I do. Orlov comes out alive." }
```

Admission converts known names to entity tokens (`Orlov` → `{char:orlov}`), then checks length, codepage (doc 14 §2), the anachronism list,
mentions ⊆ bible, grid references and numbers ⊆ digest, and alive-on-path for every mentioned character (§8.3).

### 4.4 Prompt contract for every decision point [I]

- Order: task line → story digest → constraints → menu or slot spec → exemplars → answer schema (restated at the end).
- Budget: ≤ 2K tokens for T1 models, ≤ 4K for T2, larger for T3 only when a Compose/Draft step needs it (§2.6); refuse to build a prompt over
  budget and shrink the digest by relevance rank, never by summarising.
- Reasoning: the leading `why` field (≤ 25–40 words) for Pick/Fill; provider "thinking" only where measured to help that step and model (§11).
- All mission text inside digests is untrusted data (AGENTS.md): quoted, control characters neutralised, never placed where instructions go.

### 4.5 How many decisions a campaign needs [I]

For 8 missions: intake ~5, premise 3, bible 10–20, skeleton ~10, schema 5–10, per mission 5–10 concept decisions and 15–25 text slots, plus
variants. That is roughly 200–300 decisions. At a few seconds each on a local model [U: hardware-dependent], a full draft takes minutes, not
seconds. Therefore: deterministic stages run instantly and show results first; independent decisions (per node, per slot) run in parallel where
the backend allows (§2.1 Skeleton-of-Thought); the UI shows the campaign book filling in; the user can steer at any gate.

### 4.6 Exemplar libraries

Each `DecisionKind` has a library of admitted answers with metadata (beat, side, era, tone, model tier that produced it, human-approved flag).
Retrieval picks 1–3 by metadata match, plus embedding similarity only when an embedding model is configured (metadata alone must work) [I].
Libraries ship built from synthetic fixtures and project-authored examples only (AGENTS.md fixture rules); a user may opt in to adding their
own approved answers locally. Exemplar count and order per model tier are
fixed by offline qualification (§11), following DSPy's compile-then-freeze idea (§2.7).

## 5. Step granularity: capability shapes and effort budgets

### 5.1 Capability: step shapes, qualified per model

| Shape | What the model returns | Example | Minimum qualified tier [I, to be measured] |
| --- | --- | --- | --- |
| Deterministic | Nothing | Build a mission from a concept | None |
| Pick | One label from ≤ 7 options + escapes | Site, graph shape, beat, template, consequence archetype | T1 (3–4B) |
| Fill | A small flat record: enums, bounded ints, ≤ 1–3 short text fields | Intake, character row, a briefing paragraph, a guard constant | T1 for enums; T1/T2 for prose |
| Compose | One sub-structure: a full mission concept, one node's transition table in CXL, all lines of one dialogue | "Plan mission m04" | T2 (8–9B) or T3 |
| Draft | A sub-graph or whole branch as a ChangeSet of typed campaign actions (doc 19 §8 `propose_branch`) | "Add a rescue branch if the pilot is captured" | T3; local 27B+ experimental |

- **Qualification, not parameter count, grants a shape.** A model profile records, per `DecisionKind`, the largest shape the model passed
  (§11) [I]. Unqualified models run the smallest shape.
- **As-needed decomposition (ADaPT, §2.1).** The effective shape is `min(effort ceiling, qualified shape)`. If a Compose/Draft step exhausts its
  budget, the harness keeps the admitted parts and re-runs the rest as Fill/Pick decision points, without asking the model to plan the split:
  the decomposition is authored per `DecisionKind` [I].
- **Stronger models never bypass verifiers.** A Draft is admitted as one ChangeSet only if every contained command passes the same checks.

### 5.2 Effort: budgets, not correctness

Effort changes how hard the harness tries and how often the user is consulted. The role→model binding (doc 14 §6–§8) is a separate setting that a
preset may also set. Placeholders [I]:

| Budget | Quick | Standard | Thorough | Max |
| --- | --- | --- | --- | --- |
| Shape ceiling | Pick/Fill | Fill (Compose if qualified) | Compose (Draft if qualified) | Draft if qualified |
| K candidates per creative decision | 1 | 2 | 3–5 | 5–8 |
| K for Pick steps (permuted menus, §7.3) | 1 | 3 | 3–5 | 5 |
| R repairs per decision (one finding each) | 1 | 2 | 3 | 3 |
| Verification depth | Step verifiers + error lints | + full lints + explorer | + compile + round-trip | + optional scripted preview smoke run (doc 08) |
| User gates | End of run | Premise, outline, end | Every stage | Every stage + candidate comparison |
| Exemplars | 1 | 2 | 3 | 3 |

Weak local models benefit *more* from larger K (§2.5), and K costs only local time, so "Thorough on a 4B model" is a sensible preset [I].

## 6. Fact providers and menu computation

### 6.1 Providers

| Provider | Answers | Source | Used in |
| --- | --- | --- | --- |
| `catalog.units(side, era, role, kind)` | Class IDs, display names, crew seats, side | User's installed config (doc 04 `ofp-catalog`) + our own `llm` overlay text (doc 17 §7.2) | S2, S5, S6 |
| `island.places(kind, near, radius)` | Towns and named locations with positions | `CfgWorlds >> world >> Names` (doc 05 §5.2). Returns **nothing** for Kolgujev and the desert island, which have 0 named places in config [V, doc 35 §2.2; `data/catalog-sizes.csv`]; there it falls back to settlement clusters from building density, labelled by grid and terrain, plus user-named places (doc 35 rc57) [I] | S0, S2, S5 |
| `island.sites(purpose, near, constraints)` | Candidate sites: road bends, road–water crossings, forest edges, crests from spot heights, flat open LZs, shorelines | WRP heightmap, road objects, forests (doc 05 §5.2) + deterministic terrain analysis; richer analysers may come from plugins (doc 22 §1.2 #5, #7) | S5 |
| `island.route(a, b)` | Road distance and travel-time estimate | Road graph [U: road connectivity extraction untested] | S3 timeline, S5 |
| `limits.*` | 7 end codes per mission (more successors cost routers, each a book row and a load); ≤ 7 debrief narratives per mission; player death is unroutable; no campaign vars in chapter cutscenes/outros/awards; `Int` within ±2^24; ≤ 12 crew seats per group; per-side `MaxGroups`; ≤ 10 radio choices, player must lead; text codepage and SQS line limits | Doc 04 (`IsConsistent`), doc 18 §5, §7, doc 19 F2, F6–F11 | All |
| `campaign.reachable(node)`, `campaign.alive(char, node)` | State bundles at a node; `Always` / `Sometimes(witness path)` / `Never` | Simulator and Path Explorer (doc 19 §6.4) | S4, S7, S9 |
| `campaign.vars_in_scope(node)` | Declared variables usable in this node's guards | CXL scope rules (doc 19 §5.3) | S4 |
| `templates.compatible(beat, site, side, era)` | Scene templates with typed parameter schemas and declared outcomes | Template registry (doc 17 §6) | S5 |
| `bible.digest(scope, budget)` | Relevant bible rows under a token budget | §8 | Every model step |
| `text.slots(node)` | Slot specs: channel, length cap, codepage, tone, required facts, and whether the slot may vary by state (C16) | Doc 19 F9/F10, C16, doc 15 §8.4 | S7 |

### 6.2 Menu algorithm [I]

1. **Generate** candidates from the provider (e.g. all road bends within 3 km of the node's area).
2. **Filter by hard constraints**: legality (engine limits, catalog, geography), story constraints from pinned/human content, reachability.
3. **Score by soft heuristics** code can compute: fit to the beat (cover for an ambush, open ground for an LZ), distance from previous nodes'
   sites, novelty against sites already used.
4. **Diversify**: farthest-point selection over a feature vector, so options differ in kind, not only in position (counters homogeneity, §2.9).
5. **Cap** at k ≤ 7 and **shuffle** per sample; label with neutral letters; append `X none_fit` and, where the user can answer, `Q ask_user`.
6. **Describe** each option in one line from facts only (no model text), so the menu itself cannot mislead.
7. **Record** the menu with its seed, so the decision can be replayed and diffed.

**Catalog menus need a facet step.** Step 5's cap cannot be met by truncating a catalog list: 15 of the 27 Side × Class lists in the vanilla
Unit dialog exceed k ≤ 7 (median 8, max 60 for Empty > Objects) [V, doc 35 §2.2; `data/catalog-sizes.csv`]. `catalog.units` menus are
therefore split into facet steps, side → kind → role group → role, each ≤ 7 options plus escapes on both the vanilla and CWE catalogs, with
variants resolved by the brief's era chip or a separate variant Pick (doc 42 §2.4; doc 35 rc33) [V/I]. Farthest-point diversification (step 4)
stays for sites and other open-ended candidates, where dropping near-duplicates is harmless.

An empty filtered menu is itself a finding: the node's beat cannot be realised here, so the harness offers a different beat or island area
rather than asking the model to improvise [I]. An island with no named places is not an empty menu: the `island.places` fallback (§6.1)
supplies the options.

## 7. Verifiers, candidate selection and repair

### 7.1 Verifiers per step

| Verifier | Checks | Steps | Source of truth |
| --- | --- | --- | --- |
| V-schema | Parse, JSON Schema, dynamic enum membership, quote-is-substring (S0), length bounds | All model steps | Rust types + `schemars` (doc 13 §4) |
| V-catalog | Class exists and matches side/era; crew seats ≤ 12 per group; groups ≤ `MaxGroups` | S2, S5, S6 | Installed catalog, doc 04 |
| V-geo | Positions on land/water as the class needs; inside the island; site constraints; route exists | S5, S6 | Island data |
| V-mission | Round-trip parse; `IsConsistent`; ≥ 1 group; every outcome socket wired; no designer END/LOOSE triggers in managed missions (C13) | S6 | Docs 04, 19 |
| V-cxl | Parse, typecheck, scope, interval bounds (C06, C17) | S4, S9 | Doc 19 §5 |
| V-campaign | C01–C21 at the configured severity | S3, S4, S7, S8 | Doc 19 §6.5 |
| V-text | Length, codepage, anachronism list, speakers ⊆ roster, mentions ⊆ bible, numbers/grids ⊆ digest, no `:` or `"` in SQS-bound literals (F6), alive-on-path (C18), variant coverage (C21), no state variants in state-invariant slots (C16) | S1, S2, S7 | Docs 14 §2, 19 |
| V-compile | Whitelist, line limits, simulator = lowering, re-parse of emitted files | S8 | Doc 19 §7.1 |

### 7.2 Repair protocol [I]

- A repair turn carries **one** finding, written for a model reader: rule ID, field path, the offending value, why it fails, and the
  **recomputed** allowed values (a fresh menu or range), not a generic "invalid".
- Stop when the same finding recurs, when the budget R is spent, or when a (decision, answer digest) pair repeats. Then take the fallback.
- A repaired answer is recorded as repaired; metrics never count it as a first-pass success (§11).
- Iron Curtain's policy of regenerating only broken sections, then offering "Try Again / Skip / Edit Manually" (doc 17 §8.1) and BriefingRoom's
  per-stage retries with stage fallbacks (doc 15 §8.1) are the precedents [V].

### 7.3 Choosing among K candidates [I]

1. Drop every candidate a verifier rejects (after its repairs).
2. **Pick steps:** vote across K samples that saw differently permuted menus (self-consistency plus position debiasing, §2.3, §2.5). With an
   in-process engine, add the option probabilities as a soft score (§2.5, doc 13 §4). A low margin between the top two options is a signal to
   show both to the user.
3. **Creative steps:** no voting. Order by deterministic signals (lint warnings, length fit, novelty against the bible), optionally by an
   advisory judge whose position/self-preference biases are known (§2.5); then show the top 2–3 to the user in interactive modes, or take the
   top one in batch modes, marked "AI draft, unreviewed".
4. The chosen candidate is admitted; the others are kept as one-click alternatives until the user moves on.

## 8. Consistency memory: the story bible

### 8.1 Tables (typed, in the campaign sidecar; proposal-only)

| Table | Key fields | Links |
| --- | --- | --- |
| `Character` | `CharacterId`, display name, rank, side, role, `RosterRole` and death policy (doc 19 §4.2), traits, speech style, voice notes | Roster slots, dialogue speakers |
| `Faction` | Side, unit-set tags from the catalog overlay, attitude to player | Catalog |
| `Place` | Island + `Names` entry or coordinates, kind, story role | Island data, node sites |
| `Item` / `Intel` | Declared campaign variable or pool item | Doc 19 `ItemDecl`, vars |
| `Event` | Node, outcome, effect on the world ("bridge destroyed"), **path condition** as a CXL guard | Skeleton edges |
| `Thread` | Setup (node, slot) → payoff (node, slot), both with path conditions | Text slots |

Every row carries provenance (§9.1). Model output only ever *proposes* rows through Fill decisions; code admits them.

### 8.2 Digests

`bible.digest(scope, budget)` selects rows referenced by the node or slot, then graph neighbours (previous and next nodes on reachable paths),
then threads open at this node, ranked and cut at the budget. Rows are rendered as terse fact lines, with conditional facts shown with their
condition ("if m03 ended `bridge_blown`: the bridge at Dolina is destroyed") [I].

### 8.3 Consistency checks [I]

- **Entity tokens, not names.** Admitted text stores `{char:orlov}` and `{place:dolina}`; display names render at compile time. A rename is a
  deterministic refactor that never needs regeneration (the user's "renaming updates every reference" requirement).
- **Alive on path.** For a line shown at node N under bundle B, every mentioned character must be `Always` alive for B, or the line must sit in a
  variant guarded by the character's status. The explorer supplies witnesses (doc 19 C18); the repair finding quotes the witness path.
- **Timeline and place.** Events referenced in text must precede the node on every path where the text is shown; a destroyed place cannot host
  a later mission on that path unless its template allows ruins.
- **Setup/payoff.** A `Thread` payoff must have its setup on every path that reaches it (explorer query), or it becomes a variant.
- **Variant budgets** come from the engine: briefing variants are hidden `OBJ_` objective lines, not free prose (doc 19 F9); debrief narratives
  are ≤ 7 per mission (F10); chapter cutscenes, outros and award cutscenes see no campaign vars, so their slots are state-invariant and may only
  mention `Always`-true facts (C16; state-dependent scenes go in a Cutscene node or a mission Intro). The slot spec says so, so the model is
  never asked for something the engine cannot show.

## 9. Keeping human edits

### 9.1 Provenance and pinning [I]

- Each element **and each field** records `origin` (`Human`, `Deterministic`, `Model { run, decision, model_id, prompt_hash }`,
  `ModelChosenByHuman` (the user picked or approved it among candidates), `ModelEditedByHuman`), the generation base it came from, and a
  `pinned` flag. Doc 15 §11 principle 6 and the disclosure needs in doc 15 §10 (Steam, Nexus tags) motivate the same record.
- **Inspect.** Every element opens an inspector card in its native view (map, Flow graph, state panel, text view) showing why it exists: its
  `DecisionRecord` (stage, menu offered with its seed, the pick, the model's `why` rendered as untrusted data, verifiers run, repairs), its
  dependents (the staleness graph) and its current lint status. Edits happen in the normal editors, never in a generated blob.
- **Pin** locks an element or field. Pinned and human-origin values become *constraints* in later digests ("keep: the sergeant is called
  Kovac").
- An **AI content report** and an export warning for unreviewed model text reuse this data (doc 15 §10).

### 9.2 Scoped regeneration [I]

A refine request becomes a typed `RefineRequest { scope, aspect, intent }` (Fill), then a plan of stages to rerun:

| User says | Scope | What reruns | What stays |
| --- | --- | --- | --- |
| "Make mission 4 a night assault" | Node m04 | Deterministic: time of day; Pick: a night-compatible template if the current one is day-only; Text: slots that mention time become stale | Graph, other nodes, human-edited lines |
| "Add a branch if the pilot dies" | New guarded edge (status check on the pilot) from nodes where `alive(pilot)` is `Sometimes`; a Decision node (a router: +1 book row, +1 load) only when socket demand would exceed 7 | Code checks the pilot is a squadmate or NPC with a death policy, never the player character (player death is unroutable, doc 18 §5); S3–S7 for the new sub-graph only | Everything else |
| "Rewrite the sergeant's lines to be more cynical" | Text slots with speaker `sgt_kovac` | S7 for those slots with a tone override | Human-edited and pinned lines unless explicitly included |

**Staleness:** when an upstream element changes, dependents are marked `Stale` with the reason; they are not regenerated automatically. The user
sees "3 lines mention dawn; regenerate?".

### 9.3 Three-way merge on regeneration [I]

Base = the generated version the current content descends from (stored); ours = current content; theirs = the new generation. Merge per stable
ID and per field:

| ours vs base | theirs vs base | Result |
| --- | --- | --- |
| unchanged, not human-chosen | changed | take theirs |
| changed (human) | unchanged | keep ours |
| changed | changed | **keep ours**; show a conflict card with theirs as an alternative |
| unchanged but `ModelChosenByHuman` | changed | keep ours; theirs becomes a one-click alternative (a user's pick is a human decision) |
| deleted by human | any | stays deleted |
| pinned | any | keep ours; theirs is never computed for pinned fields |

Long prose fields may use a line-level diff3 inside the field. The formal analysis of diff3 (Khanna, Kunal & Pierce, FSTTCS 2007) examines
the intuition that edits to "well-separated" regions never conflict and finds several natural intuitions about diff3 false in general [V];
we therefore show any conflicting prose to the user rather than auto-resolving it [I]. The merged result is re-verified and applied as one undo group.

## 10. Failure UX: degrade gracefully, never break

### 10.1 The draft-first, always-compilable invariant [I]

- As soon as the skeleton exists, code fills every node with a **default mission** from the beat's default template and default site, and
  every text slot with template text. The campaign compiles, lints clean and is playable in the what-if simulator and in Preview.
- Model decisions replace defaults one at a time. An admitted answer upgrades a piece; a failed decision leaves the default in place, marked
  `Defaulted` with the reason.
- The no-model mode (doc 14 T0) runs the same pipeline with seeded picks: it is both the baseline in §11 and a real product mode.

### 10.2 Fallback ladder per decision [I]

1. Repair (≤ R turns, one finding each).
2. Re-menu with a different diversity seed (Pick steps).
3. Decompose into smaller shapes (Compose/Draft steps, §5.1).
4. In interactive modes, ask the user a computed question whose options include "keep the default".
5. In batch modes, or when the user skips, keep the deterministic default (it is already in place, §10.1).
6. Report "not done, default kept" in the run summary.

Never: silently retry with a larger or cloud model, hide a failing lint, or claim a step succeeded. A stronger model is offered as a button
("try this step with the configured writer model") with its cost shown (doc 14 §8).

### 10.3 Keeping it fun [I]

- **Choices, not waiting.** Premise cards, graph-shape cards, 2–3 site options on the map, 2–3 candidate lines: the user picks, rerolls or edits.
- **Something to look at every minute.** The Flow and Theatre views (doc 19 §6) fill in live; each built mission can be opened on the map.
- **Surprise on request.** "Twist" and "reroll" buttons re-seed menus or ask for a new premise; variety comes from code seeds and archetype
  menus, since models alone converge (§2.9).
- **Play it early.** The what-if playthrough (doc 19 §6.4) works from S3 onwards; Preview works per mission from S6.
- **Honest reporting.** The run summary lists what the AI wrote, what it could not do, and which defaults remain, in the retro campaign-book
  style.

## 11. Evaluation plan

### 11.1 Instruments (synthetic island and catalog fixtures only, per AGENTS.md)

| ID | Instrument | Cases | Oracle (typed diff + lints) | Primary metrics |
| --- | --- | --- | --- | --- |
| E1 | Intake fill | 60 briefs incl. ambiguous, contradictory, engine-impossible, non-English | Expected `CampaignBrief`; quote check | Field accuracy; **wrong fills** (worst); unnecessary questions (annoyance) |
| E2 | Premise and bible rows | 30 briefs × 3 | Lints; uniqueness; human rating | First-pass admit; diversity across seeds |
| E3 | Skeleton picks | 30 briefs | Brief checklist (length, branching, endings, features) | Fidelity vs random-pick baseline |
| E4 | Site and template picks | 100 node menus, 20 with a planted "no option fits" | Panel labels; `X` expected on planted cases | Agreement vs random; `none_fit` honesty |
| E5 | Mission concept fill / compose | 60 nodes | V-catalog, V-geo, V-mission | First-pass admit; repairs; decomposition rate |
| E6 | Guard constants and CXL compose | 40 nodes | Typecheck, coverage; AST diff against intent | Admit; semantic match |
| E7 | Text slots | 200 slots, 4 tones | V-text; blind human rating | Lint-free first pass; rating vs no-model templates |
| E8 | Consistency traps | 20 campaigns with deaths/destruction on some paths | C18, timeline, thread lints before repair | Violations per 100 lines before repair; after repair (must be 0) |
| E9 | Refine and merge | 30 edit-then-regenerate scripts, incl. edits made while a run is in flight | Typed diff: human-edited, human-chosen and pinned fields unchanged | **Clobbers (must be 0)**; stale marks correct |
| E10 | End to end | 20 briefs × 3 seeds × each tier | Compile + lints; brief checklist; human panel | Validity (**must be 100%**), fidelity, fun, time, cost, questions asked, routers/book rows added |
| E11 | Adversarial text | Injections in imported mission text, briefs asking for out-of-scope actions | No effect outside the plan; byte-identical campaign when the run should stop | Zero violations |

### 11.2 Matrix, controls and statistics [I]

- **Tiers:** no model (T0 seeded defaults), 3–4B (e.g. Qwen3.5-4B), 8–9B (Qwen3.5-9B), 27B+ (Qwen3.8-27B), frontier (doc 14 §6). Record exact
  artifacts: weights hash, quantisation, chat template, sampler, runtime, thinking on/off.
- **Controls** on every instrument: random valid pick, always-first option, always-ask, and no-model defaults. A model that cannot beat the
  random-valid-pick control on a step is not qualified for that step's creative role. On E10, also a *single-prompt* control (the same model
  asked for a whole campaign as one typed ChangeSet, admitted through the same verifiers), because added scaffolding does not reliably help
  by itself (TL;DR; 2607.05775); the staged flow must beat it on validity-before-fallback, fidelity and fun at T1–T2.
- **Reliability:** report pass^k over repeated runs (τ-bench's metric, §2.8), per step, never pooled across steps or models. For zero observed
  failures in n trials, the 95% upper bound on the failure rate is about 3/n (the "rule of three", Hanley & Lippman-Hand, JAMA 1983) [V];
  claiming ≥ 80% per-step success at 95% confidence needs ≥ 14 all-pass trials (ln 0.05 / ln 0.8) [I, arithmetic].
- **Human panel:** blind pairwise comparisons across tiers *and against the no-model baseline*, rating coherence, fidelity and fun. LLM judges
  only as a cheap pre-screen, reported separately (§2.5).
- **CI:** deterministic stages and recorded model answers (replayed cassettes) run in CI; live-model runs are opt-in local jobs.

### 11.3 Hypotheses to confirm or kill [I]

- **H1** Validity is 100% at every tier, including T0 (a failure is a harness bug, not a model result).
- **H2** A 3–4B model beats the random-valid-pick control on E3/E4 fidelity and on E10 human preference.
- **H3** On Pick/Fill steps, the 8–9B vs frontier gap is small; it widens on Compose/Draft.
- **H4** K > 1 with verifiers narrows the weak-vs-strong gap more than extra exemplars do.
- **H5** A leading `why` field helps 3–4B models on Pick steps; provider "thinking" does not pay for its latency there.
- **Kill rule:** if H2 fails, the campaign flow for T1 defaults to T0 picks plus model-written text only.

## Open questions

1. **Menu size:** is k ≤ 7 right for 3–4B models, and does position debiasing by permutation cost more than it gains at K = 3? (E4) [U]
   Keeping the cap already costs extra facet steps for unit menus (§6.2); E4/E5 should measure whether the added steps lose more than a longer menu would.
2. **Shape qualification thresholds:** what pass^k per step grants Fill → Compose? Proposal: pass^3 ≥ 0.8 on the step's instrument [U].
3. **Site analysis quality:** can road-bend, crossing and crest finders be built reliably from WRP data, and which belong in core rather than a
   plugin (doc 22)? Road connectivity for `island.route` is untested [U].
4. **Scene-template coverage:** how many templates (with night/day, side and era variants) does a satisfying 8-mission campaign need? Without
   enough templates, menus shrink and campaigns feel repetitive [U].
5. **Text quality floor:** is 3–4B prose acceptable for briefings once lints pass, or should T1 default to template text plus model-picked
   variants from a curated phrase bank? Doc 14 §4.2 found 4B-class creative quality unmeasured on EQ-Bench [U].
6. **Non-English briefs and output:** intake quotes and codepage lints must work for CZ/PL/RU; small-model quality there is unmeasured (doc 14) [U].
7. **Parallelism vs determinism:** parallel decisions must stay replayable; seeds and admission order need a canonical schedule [I].
8. **Local soft scores:** do option probabilities from an in-process engine calibrate well enough to decide "ask the user" (doc 13 §4 item 6) [U]?
9. **Merge UX:** how are conflict cards shown for dozens of lines without overwhelming the user?
10. **Sidecar size:** the decision log, alternatives and provenance for 300 decisions: prune policy and export exclusion (doc 19 §7.1) [U].

## Sources

**Repository docs:** `docs/research/04-mission-data-model-and-formats.md` (IsConsistent, `MaxGroups`); `05-visual-fidelity-and-ui-resources.md`
§5.2 (island map layers, `Names`); `13-local-inference-in-rust.md` §4; `14-model-selection.md` §2, §4.1, §6, §8; `15-prior-art-ai-content-creation.md`
§8–§11; `17-iron-curtain-ai-editor-ideas.md` §6–§9; `18-campaign-system-in-engine.md` TL;DR, §5, §7, §8; `19-campaign-designer-ux-and-state-model.md`
§1 (F2–F11), §4–§8; `22-plugin-system.md` §1.2, §4.2; `35-lessons-from-real-content-and-later-armas.md` §2.2, §9 (rc33, rc57), §10;
`42-mods-in-generation-and-distribution.md` §2.4; `data/catalog-sizes.csv` (`CfgWorlds.*.named_places`, `editor.unit_dialog.*`).

**Papers (arXiv abstracts fetched 2026-09-26 via arxiv.org / export.arxiv.org; most re-fetched 2026-09-27, see Verification notes):**

- Decomposition: Zhou et al., Least-to-Most, [2205.10625](https://arxiv.org/abs/2205.10625); Wang et al., Plan-and-Solve, [2305.04091](https://arxiv.org/abs/2305.04091);
  Khot et al., Decomposed Prompting, [2210.02406](https://arxiv.org/abs/2210.02406); Ning et al., Skeleton-of-Thought, [2307.15337](https://arxiv.org/abs/2307.15337);
  Prasad et al., ADaPT, [2311.05772](https://arxiv.org/abs/2311.05772); Khattab et al., DSPy, [2310.03714](https://arxiv.org/abs/2310.03714).
- Planning and verifiers: Liu et al., LLM+P, [2304.11477](https://arxiv.org/abs/2304.11477); Guan et al., [2305.14909](https://arxiv.org/abs/2305.14909);
  Kambhampati et al., LLM-Modulo, [2402.01817](https://arxiv.org/abs/2402.01817); Xie et al., TravelPlanner, [2402.01622](https://arxiv.org/abs/2402.01622);
  Gundawar et al., [2405.20625](https://arxiv.org/abs/2405.20625); Hao et al., [2404.11891](https://arxiv.org/abs/2404.11891); Muñoz-Avila et al., ChatHTN,
  [2505.11814](https://arxiv.org/abs/2505.11814); Belcamino et al., [2601.14456](https://arxiv.org/abs/2601.14456); Laule et al., PDDLCoder,
  [2608.16637](https://arxiv.org/abs/2608.16637).
- Menus and selection: Robinson, Rytting & Wingate, [2210.12353](https://arxiv.org/abs/2210.12353); Zheng et al., [2309.03882](https://arxiv.org/abs/2309.03882);
  Paramanayakam et al., [2411.15399](https://arxiv.org/abs/2411.15399); Patil et al., Gorilla, [2305.15334](https://arxiv.org/abs/2305.15334); Li et al.,
  [2310.01846](https://arxiv.org/abs/2310.01846); West et al., [2311.00059](https://arxiv.org/abs/2311.00059); Song et al., [2412.02674](https://arxiv.org/abs/2412.02674).
- Constrained decoding: Geng et al., [2305.13971](https://arxiv.org/abs/2305.13971); Geng et al., JSONSchemaBench, [2501.10868](https://arxiv.org/abs/2501.10868)
  (results from [HTML v3](https://arxiv.org/html/2501.10868v3)); Tam et al., [2408.02442](https://arxiv.org/abs/2408.02442); Banerjee et al., CRANE,
  [2502.09061](https://arxiv.org/abs/2502.09061); Park et al., Grammar-Aligned Decoding, [2405.21047](https://arxiv.org/abs/2405.21047); Willard & Louf, Outlines,
  [2307.09702](https://arxiv.org/abs/2307.09702); Dong et al., XGrammar, [2411.15100](https://arxiv.org/abs/2411.15100); Kurt, "Say What You Mean",
  <https://blog.dottxt.ai/say-what-you-mean.html>.
- Sampling, repair, judges: Wang et al., Self-Consistency, [2203.11171](https://arxiv.org/abs/2203.11171); Wang et al., Soft Self-Consistency,
  [2402.13212](https://arxiv.org/abs/2402.13212); Brown et al., Large Language Monkeys, [2407.21787](https://arxiv.org/abs/2407.21787); Snell et al.,
  [2408.03314](https://arxiv.org/abs/2408.03314); Liu et al., [2502.06703](https://arxiv.org/abs/2502.06703); Huang et al., [2310.01798](https://arxiv.org/abs/2310.01798);
  Kamoi et al., [2406.01297](https://arxiv.org/abs/2406.01297); Chen et al., Self-Debugging, [2304.05128](https://arxiv.org/abs/2304.05128); Olausson et al.,
  [2306.09896](https://arxiv.org/abs/2306.09896); Zheng et al., MT-Bench judges, [2306.05685](https://arxiv.org/abs/2306.05685); Panickssery et al.,
  [2404.13076](https://arxiv.org/abs/2404.13076).
- Context and state: Laban et al., [2505.06120](https://arxiv.org/abs/2505.06120); Liu et al., Lost in the Middle, [2307.03172](https://arxiv.org/abs/2307.03172);
  Modarressi et al., NoLiMa, [2502.05167](https://arxiv.org/abs/2502.05167); Packer et al., MemGPT, [2310.08560](https://arxiv.org/abs/2310.08560); Hong, Troynikov &
  Huber, "Context Rot", <https://www.trychroma.com/research/context-rot>; Liu et al., [2101.06804](https://arxiv.org/abs/2101.06804); Lu et al.,
  [2104.08786](https://arxiv.org/abs/2104.08786).
- Tool use: BFCL V4 leaderboard, <https://gorilla.cs.berkeley.edu/leaderboard.html> and its data file
  <https://gorilla.cs.berkeley.edu/data_overall.csv> (last updated 2026-04-12); Yao et al., τ-bench,
  [2406.12045](https://arxiv.org/abs/2406.12045); Huang et al., [2601.16280](https://arxiv.org/abs/2601.16280); Li et al., [2609.28003](https://arxiv.org/abs/2609.28003);
  Albayaydh et al., [2607.05775](https://arxiv.org/abs/2607.05775); Ross et al., When2Call, [2504.18851](https://arxiv.org/abs/2504.18851); Zhang et al., ToolBeHonest,
  [2406.20015](https://arxiv.org/abs/2406.20015); Belcak et al., [2506.02153](https://arxiv.org/abs/2506.02153).
- Narrative: Fan et al., [1805.04833](https://arxiv.org/abs/1805.04833); Yang et al., Re3, [2210.06774](https://arxiv.org/abs/2210.06774); Yang et al., DOC,
  [2212.10077](https://arxiv.org/abs/2212.10077); Mirowski et al., Dramatron, [2209.14958](https://arxiv.org/abs/2209.14958); Huot et al., Agents' Room,
  [2410.02603](https://arxiv.org/abs/2410.02603); Wang et al., DOME, [2412.13575](https://arxiv.org/abs/2412.13575); Gu et al., PLOTTER,
  [2604.21253](https://arxiv.org/abs/2604.21253); Leandro et al., GENEVA, [2311.09213](https://arxiv.org/abs/2311.09213); Huang et al., WHAT-IF,
  [2412.10582](https://arxiv.org/abs/2412.10582); Wang & Kreminski, [2406.00554](https://arxiv.org/abs/2406.00554) and [2506.10161](https://arxiv.org/abs/2506.10161);
  Wang et al., StoryVerse, [2405.13042](https://arxiv.org/abs/2405.13042); Munk et al., [2601.23206](https://arxiv.org/abs/2601.23206); Jiang et al., Artificial
  Hivemind, [2510.22954](https://arxiv.org/abs/2510.22954); Suh et al., Luminate, [2310.12953](https://arxiv.org/abs/2310.12953).
- Other: Khanna, Kunal & Pierce, "A Formal Investigation of Diff3", FSTTCS 2007, <https://www.cis.upenn.edu/~sanjeev/papers/fsttcs07_diff3.pdf>;
  Hanley & Lippman-Hand, "If Nothing Goes Wrong, Is Everything All Right?", JAMA 249:1743–1745 (1983), <https://pubmed.ncbi.nlm.nih.gov/6827763/>.

## Verification notes

- **2026-09-27 adversarial review** (after a 2026-09-26 first pass from abstracts). Re-fetched every arXiv abstract cited here except those under
  "Still unverified" (all 2026 ids included), JSONSchemaBench HTML v3 Table 8 and its coverage table, Chroma "Context Rot" (authors, 2025-07-14,
  18 models), the dottxt post (Will Kurt, Llama-3-8B-Instruct, six numbers), BFCL `data_overall.csv` (109 rows; Overall/Multi-turn
  77.47/68.38, 42.57/41.75, 35.68/22.12) and the diff3 abstract. Ids, titles, authors and numbers match; nothing refuted; no wrong ids.
- **Corrected or narrowed:** Laban's 39% is for underspecified tasks revealed over turns; JSONSchemaBench Last Letters/Shuffle are now ranges
  over four engines; Snell's 14× needs moderate small-model success and Liu's 1B > 405B uses a reward model; Guan's 48 tasks use *corrected*
  PDDL; Song's claim is about "a variant of" the gap; DOME's analyzer evaluates conflicts; GENEVA writes narrative before graph; Munk's SLMs
  are specialised; Robinson et al. has three authors; NoLiMa is 11 of 13 models; BFCL is now [V] directly. Added 2607.05775's scaffolding
  counter-finding and a single-prompt control (§11.2).
- **Product-fit fixes (AGENTS.md; docs 18/19):** S3 no longer treats C12 as a hard ≤ 7 budget (it is info; routers are legal but each costs a
  book row and a load, so shape cards show and rank by router cost); the §9.2 pilot branch prefers a guarded edge over a Decision node (a
  router) and excludes the player character; S4 limits guard types (F3), never persists object/group values and checks C20; text slots carry a
  state-invariant flag for chapter cutscenes, outros and awards (C16, §6.1, §7.1, §8.3); principle 2 no longer contradicts Compose-shape CXL;
  `Checked<T>` re-verifies against its read set instead of failing on any user edit; a `ModelChosenByHuman` origin and merge row keep a user's
  pick from being silently replaced (E9 tests it); an inspector card makes every element's decision record visible (§9.1); refine requests can
  be built without a model; embedding retrieval is optional; intake quote checks are normalised for non-English briefs.
- **Still unverified on 2026-09-27** (first-pass check only): 2210.02406, 2305.15334, 2311.00059, 2306.05685, 2307.03172, 2310.08560,
  2104.08786, 2307.09702, 2411.15100 and the JAMA "rule of three" paper. The dottxt post shows no date ("2024" unconfirmed).
- **Public rule:** this file names no private or unpublished project, benchmark or coined term (searched 2026-09-27). All design content in
  §3–§11 is [I] and proposal-only; step counts, budgets, menu sizes and token budgets are placeholders for E1–E11.

### Consolidation pass (2026-09-27)

- **2026-09-27, from doc 35 §10 (Doc 25).** §6.1: `island.places` returns nothing for Kolgujev and the desert island (config has 0 named
  places, `data/catalog-sizes.csv` rows `CfgWorlds.Cain.named_places` and `CfgWorlds.Intro.named_places`) [V]; the provider now names the
  doc 35 rc57 fallback, and S2 binds places to it. §6.2: 15 of 27 Side × Class unit lists exceed k ≤ 7 (median 8, max 60; rows
  `editor.unit_dialog.lists`, `lists_over_7`, `list_median`, `list_max`) [V], so a "Catalog menus need a facet step" paragraph adds the
  side → kind → role group → role facet of doc 42 §2.4 (doc 35 rc33). The TL;DR menu bullet, open question 1 and Sources were updated to match.
  No earlier finding was removed. No Standing Orders / Drill renames or doc 33 / skill links occur in this file, so none were needed.
