# Synthetic reasoning: letting the harness think for small models

Research doc 59 for Plotroom (`ofp-editor`). Research date: 2026-09-28. Audience: the owner, contributors and LLM coding agents. This
file is meant to be read on its own.
Question answered (owner, 2026-09-28, lightly edited): "Is artificial or synthetic reasoning or thinking possible, to improve the
performance of the LLM?"

**Status: draft — experiments pending.** No model was loaded or run for this doc. Plotroom's own evidence is an offline re-count of
the stored call records of docs 44 and 46, plus preliminary doc 49 rows marked as such. No new calls were made. Only the tuning split
was used: today's suites, the six-item dispatch draft, and the tune halves of the expanded Pick and Fill pools staged with the run
tooling. Their held-out halves were not read. Every scaffold, knob, budget and decision rule below is a proposal [I].
**Epistemic legend** (doc 53's): **[V]** verified against the cited primary source, or re-derived from our stored records;
**[V-vendor]** a vendor's statement about its own model; **[V-3p]** a third-party report not confirmed at its source; **[V per doc
N]** taken from a sibling doc; **[anecdote]** a single practitioner's report; **[I]** our inference or proposal; **[U]** unknown. Web
sources are cited as [1]…[123] and listed under Sources, grouped by theme.
**Relation to sibling docs.** Doc 21 sets the doctrine: step shapes, §4.1's intent fill → dispatch, §8.2's admission rules ("a
reply cut off by the length limit is never executed"; "reasoning text is never stored"), §9's trust labels. Doc 25 adopted a leading
bounded `why` (§2.4, §4.3; hypothesis H5, untested). Doc 38 fixes the capsule (§3.3), doc 40 the token economy (R2–R4, R8), and docs
44 and 46 the measurements, all with thinking off. Doc 51 covers model-native reasoning switches (§2.6.2) and budget forcing (M9).
Doc 53 covers one-pass scoring, cascades, the letter-only question (T10, R7) and the Granite thinking test (S7, R8). Doc 55 (draft)
owns the knob catalogue, the preset file and the tuning protocol, and this doc feeds it. D048 governs: presets change how Wilco asks,
never what code owns. D027 item 6 (no fine-tuning) and D023 decision 3 (no silent cross-model escalation) stand. Doc 58 (in
progress) drafts the owner question on training small task models. This doc changes no decision.
**Names.** *Model reasoning* is text the model writes before its answer: native thinking, prompted chain of thought (CoT) or a `why`
field. *Harness reasoning* is reasoning that code authors or computes. *Synthetic reasoning* in this doc means harness reasoning
presented to the model or used in its place. A *code-written thought* is harness reasoning placed in the model's own think channel.
A *scaffold* is one such technique, selectable per model and DecisionKind. Step kinds follow doc 53: PICK, FILL, COMPOSE, creative
text and EXPLAIN.
**Hygiene.** Public sources only; no game content, no private projects, no local paths. Model answers appear only as short spans from
our own synthetic suites.

## TL;DR

- **Yes, and for Plotroom's 3–4B models the strongest form is harness reasoning, not longer model thinking** [I on V]. Code does the
  reasoning steps it can own: applying an engine rule, checking coverage against the module registry, working out each option's
  consequence, eliminating options by attribute. The model makes one small, closed judgement in the user's terms.
  - When a model decides from its own checklist, it looks consistent with it but seldom changes its answer when the checklist is
    edited: a gap of about 18–23 points on three of four benchmarks, across 12 models from 1.7B up (Qwen3 1.7B–235B among them).
    When a tool derives the decision from the same structure, the gap falls below 0.03 in most configurations; that arm ran on
    eight of the models, 1.7B–32B [34].
  - Typed rules plus a solver took Qwen3-4B-2507 to 0.983 in one call, against 0.700 for five-call self-consistency. The same
    pipeline was negative for Phi-4-mini-reasoning, so the gain is per model [35].
- **Model-written reasoning helps small models narrowly.**
  - Gains concentrate in math and logic; on non-math tasks CoT averaged 56.8 against 56.1 without [2].
  - At 4–8B, CoT lowered classification, extraction and instruction following in several studies, and weaker models lost more
    [4, 5, 6]. It is not uniformly negative: the same classification study found CoT lifted Gemma-3-4B and Qwen3-8B by 18.8–22.1
    points on subjective tasks [5], and at 3B few-shot CoT still lifts grade-school math from single digits to 59–71 [13].
  - Trained thinking lifts Qwen3-4B on logic (ZebraLogic 81.0 against 35.2) but not on IFEval (81.9 against 81.2), at thousands of
    tokens [7, V-vendor].
  - Reasoning fine-tuning lowered abstention by 24% on average [21], which threatens near-fit escapes.
  - Short budgets can help and long ones collapse: Qwen2.5-1.5B function routing went 44.0% → 64.0% at 32 tokens and fell to 25.0%
    at 256 [15].
- **Our failures are mostly systematic, not random** [V, offline re-count, tuning split].
  - Qwen3.5-4B: 162 Pick misses in 1,440 calls. 87 are counter-intuitive rules, 39 lures, 22 near-misses and 14 missed escapes. 118
    sit in majority-wrong cells, and a majority of three permuted samples would have fixed only 44.
  - HT03 ("same End number means AND") was 0 of 24, with or without the card that states the rule.
  - Gemma 4 E4B: 90 misses, 54 of them rules. Granite 4.1 3B: 18 misses on `pick`, 10 of them rules.
  - Sampling and self-critique fix random errors, not these. A scaffold must change what the model sees or who decides.
- **The ladder, cheapest and best supported first** [I]:
  1. Code decides from facets the model fills (extract-then-dispatch, the escape coverage check).
  2. Code states the facts that separate the options (option-diff lines, per-option consequences, the one decisive card sentence),
     without naming the answer.
  3. The model writes a bounded rationale before a constrained answer, only on DecisionKinds where it is measured to help.
  4. A small native thinking budget in two phases, triggered only on hard or disputed steps.

  Score-side helpers (letter-probability elimination, a re-ask on the top two) stack with any rung.
- **Literal synthetic thinking is possible on the pinned runtime.** By code reading, llama-server b11146 can prefill a code-written
  thought into Qwen3.5's `<think>` block or Gemma 4's thought channel (`continue_final_message`), then apply the answer schema after
  the block [V at source; U until a canary passes]. The thought adds about 100 prompt tokens (≈0.35 s uncached on the reference GPU)
  and no extra decode. It mirrors Thinking Intervention on 7B+ reasoning models [89]. At 3–4B it is untested [U].
- **Safety by construction** (§5). Code-written reasoning comes only from facts code owns. It uses templates authored per
  DecisionKind before tuning, is applied symmetrically to every option, and never reads the item's answer. Answer-swap and
  permutation tests prove the answer cannot reach it; a paired hint-only test checks that it does not choose on its own. Untrusted
  mission text never enters the thought channel.
- **Thinking stays off by default.** Reasoning becomes a D048 preset knob per (model, DecisionKind), switched on by code. This is
  the "classifier-selective" pattern, which beat both always-on and model-chosen reasoning [4]. The model never decides to reason.
- **Not recommended for local 1–9B models:**
  - self-critique turns [82, 84] and generative elimination [65];
  - Chain-of-Draft at 4B or less [13], filler or pause tokens [92, 93], and s1's "Wait" [19, 20];
  - voting beyond K = 3 against systematic errors;
  - model-written plans [47], and executing model-written programs [44];
  - lenient parsing of answers [123].
- **Experiments** (§6) [I]:
  - Scale: 16 Pick arms in three waves and 5 Fill arms, on the tuning split with sequential halving. About 5,000 calls and 2–2.5
    hours of GPU time per thinking-capable 4B model.
  - Sharpest test: the same facet questions, decided either by the model (checklist) or by code (dispatch).
  - Thinking arms wait for six canaries on the pinned build.
- **Eight design-gap candidates** (§7), listed, not filed. The main ones:
  - a registered scaffold slot per DecisionKind;
  - a capsule segment for code-written thought;
  - the two-phase call shape;
  - reconciling doc 21 §8.2 ("reasoning text is never stored") with the glass-box inspector.

## 1. Definitions

### 1.1 Who does the reasoning

| Form | Who writes the reasoning | Who draws the conclusion | Plotroom example |
| --- | --- | --- | --- |
| Model reasoning, native | The model, in its trained think channel | The model | Qwen3.5-4B with `enable_thinking` true |
| Model reasoning, prompted | The model, as visible text: a CoT instruction or a leading `why` field | The model | `run.py --why` (160 characters; not used in the records re-counted here) |
| Harness reasoning, structured | The model, in slots code authored: facet questions, checklist fields | The model (checklist) or code (dispatch) | HT03-D: "When should the mission end in victory?" |
| Harness reasoning, code-computed | Code: rules applied, consequences, exclusions, coverage | Code, or the model from code's facts | "End #1 and End #2: the mission ends as soon as either trigger is active" |
| Code-written thought | Code-computed reasoning placed in the model's think channel or assistant prefill | The model | §4.2 S4 |

The last three rows are the product-scoped reading of the owner's question. Code already owns the facts (AGENTS.md), so it can
also own the steps that only apply those facts. Literal "artificial thinking tokens" (filler dots, pause tokens) help only after a
model is trained to use them [92, 93]. D027 item 6 and D048 decision 3 rule that out [I].

### 1.2 Free, structured and code-computed reasoning

- **Free:** the model chooses length and content (native thinking, CoT). At 1–9B it gains in math and logic and often costs
  elsewhere (§2.1–§2.2).
- **Structured:** code fixes the form: a field bounded at both ends, a checklist, closed facet answers. Under constrained decoding,
  field order is generation order, so a reason placed after the answer cannot affect it [27, 28].
- **Code-computed:** each step is a deterministic function of facts code owns. Only these steps can be correct by construction, and
  only they give an explanation that is faithful by construction [38].

### 1.3 What "better" means here

The metrics are doc 55 §4.4's:

- Pick pass^3 in both card conditions, planted-escape recall and false `X`;
- Fill all-fields-right and per-field accuracy, and validator pass^3;
- p50 latency and tokens per decision (PR3, PR6).

This doc adds two:

- **Wrong-but-valid rate:** answers that pass the schema but are wrong. Hard constraints can raise it [30].
- **Hint-only accuracy:** accuracy when the request is blanked but the scaffold is kept (§5.3). It shows whether a scaffold chooses
  on its own.

## 2. Evidence

### 2.1 Model-written chain of thought at 1–9B

| Finding | Models and task | Effect | Source |
| --- | --- | --- | --- |
| CoT helped only large models in 2022 | LaMDA and PaLM families, math | "does not positively impact performance for small models"; about a 100B threshold; small models wrote "fluent but illogical" chains | [1] |
| The threshold moved for modern instruct models, on math | Qwen2.5-3B, Llama3.2-3B; GSM8K, few-shot | CoT 59.1 and 70.7, against 7.2 and 3.9 answering directly | [13] |
| Gains concentrate in math and symbolic steps | Meta-analysis of 100+ papers, plus 14 models incl. Llama 3.1 8B, Mistral 7B, Gemma 2 9B, Qwen 2 7B | Non-math 56.8 with CoT against 56.1 without; about 95% of MMLU's CoT gain comes from items with "="; a symbolic solver beats CoT where one exists | [2] |
| CoT can hurt objective classification, and help subjective | Qwen3-8B, Llama-3.1-8B, Gemma-3-4B (plus GPT-4o-mini and five large models); 5 datasets | CoT minus direct macro-F1 ranges from −11.35 to +22.05. TREC lost 5.9–11.4 points on all three open models; on the two subjective sets CoT gained 18.8–22.1 for Gemma-3-4B and Qwen3-8B and lost 8.2–9.9 for Llama-3.1-8B. SC-CoT and ToT cost 10–100× the tokens | [5] (2026 preprint) |
| CoT hurts extraction-like understanding, more for weaker models | 95 LLMs from about 1B to 671B, 87 clinical tasks | 86.3% of models degrade; the loss grows as baseline capability falls (R² 0.973) and as traces lengthen; the named error types are hallucination, omission and incompleteness | [6] |
| CoT hurts instruction following; selective reasoning wins | 15 models; Qwen2.5-7B-Instruct on IFEval | 63.6 without CoT, 57.7 with; an external classifier deciding when to reason 68.8; self-selected reasoning 59.7 | [4] |
| CoT hurts where deliberation hurts people | Frontier models; tasks including rule-based classification with exceptions | Drops of up to 36.3 points absolute (o1-preview against GPT-4o); mixed effects on the other tasks. Not small-model evidence | [3] |
| CoT explanations can rationalise a biased answer | GPT-3.5 and Claude 1.0; BBH with biasing contexts | Up to −36% accuracy; the stated reason hides the cause. Not small-model evidence | [24] |
| Terse drafts do not transfer down | Qwen2.5-1.5B and 3B, Llama3.2-3B; GSM8K | Chain of Draft against CoT: 24.2 vs 32.5, 43.1 vs 59.1, 52.5 vs 70.7 | [13] |
| Long-CoT distillation fails at 3B or less | Small students | The "learnability gap" | [14] |

### 2.2 Trained thinking modes and small budgets

| Finding | Models and task | Effect | Source |
| --- | --- | --- | --- |
| Thinking helps logic, not instruction following | Qwen3-4B, vendor table | MMLU-Redux 83.7 vs 77.3; GPQA-Diamond 55.9 vs 41.7; ZebraLogic 81.0 vs 35.2; BFCL v3 65.9 vs 57.6; IFEval 81.9 vs 81.2 | [7] V-vendor |
| Thinking helps small pairwise judges | Qwen3 0.6B, 1.7B, 4B | About +10 points at under 2× FLOPs; non-thinking judges with few-shot, rubrics or ensembles gained less at over 8× the cost | [8] (workshop) |
| Overthinking | Reasoning models | Accuracy rises, then falls with length; several short paths plus a vote beat one long chain by up to 20% at equal budget | [10] |
| Skipping thinking and sampling instead | DeepSeek-R1-Distill-Qwen (32B); math, proofs, code | 51.3 against 28.9 for thinking at a 700-token budget on AMC 23; matches thinking at up to 9× lower latency | [9] |
| Longer thinking is more distractible | Reasoning models | More distraction by irrelevant detail, more spurious correlation | [11] |
| The best length falls with capability and rises with difficulty | — | — | [12] |
| Short budgets can help, long ones collapse | Qwen2.5-1.5B on 200 BFCL v3 Multiple tasks; CoT capped, then a forced JSON pass | 0 tokens 44.0%; 32: 64.0%; 64: 58.0%; 128: 51.5%; 256: 25.0%; 512: 22.5%. Qwen2.5-7B 40.5 → 82.5 at 32, 36.0 at 128, 18.0 at 256; Phi-3-mini 29.5 → 86.0 at 32 and still 66.5 at 256, because it stopped by itself 68% of the time. The direct baselines are low, and this is the closest published task to a Pick (choosing one function from several) | [15] (2026 preprint) |
| A shared output cap punishes thinking | Qwen3-8B; GSM8K, MATH-500 | Non-thinking matches or beats thinking at every budget up to 2,048; 87.5 vs 18.0 at 256 (98.6% truncated), 93.1 vs 56.9 at 512; a separate answer pass recovers | [16] |
| Small models overthink easy items | Qwen3-1.7B | About 750 thinking tokens on simple queries in the scaling analysis (1,519 in the main table) for +2.2 to +4.7 points by answer type; +2.2 on multiple choice | [17] |
| Intermediate thinking after training buys little | Qwen3-4B, GPQA, after GRPO training in each mode | Tested without thinking: the No-Think-trained model 36.9% (1,560 tokens), the Mid-Think-trained model 38.2% (2,086); the untrained model thinking 53.2% (8,729). Post-training rows, not a training-free budget sweep (cell placement to recheck) | [18] |
| Budget forcing gives nothing at 4B | Gemma 3 4B IT; MMLU-Pro, SuperGPQA, math | Zero-shot 39.73, CoT 36.41, CoT plus forcing 39.33; "Wait" is not special | [19] |
| Reasoning lowers abstention | AbstentionBench | "reasoning fine-tuning degrades abstention (by 24% on average)" | [21] |
| More thinking, more hallucination on knowledge | Reasoning models | Test-time scaling not effective for knowledge-intensive tasks yet | [22] |
| Traces are not faithful | Reasoning models | A hint the model used is verbalised often less than 20% of the time | [23] |
| Think only when cheap drafts disagree | 0.6B–32B hybrid models | Two no-think drafts; answer directly when they agree; thinking tokens −32% to −73% | [25] |

### 2.3 Rationale fields and format constraints

| Finding | Models and task | Effect | Source |
| --- | --- | --- | --- |
| Format restrictions hurt reasoning and help classification | Llama-3-8B; GPT-3.5 | GSM8K 75.13 (text) → 64.67 (JSON requested in the prompt) → 48.90 (JSON plus a schema in the prompt); Last Letter 70.1 → 28.0; DDXPlus (classification) 44.1 → 55.5 for GPT-3.5 in JSON mode; GPT-3.5 put `answer` before `reason` in 100% of JSON replies | [27] |
| A bounded leading reason field removes the penalty | Llama-3-8B-Instruct, matched prompts, a 30–250-character regex-bounded reasoning field first | Structured against free: GSM8K 0.78 vs 0.77, Last Letter 0.77 vs 0.73, Shuffled Objects 0.44 vs 0.41 | [28] (vendor blog) |
| Reason free, constrain late | Qwen2.5-1.5B, GSM-Symbolic | CoT 26%, constrained 22%, alternating (CRANE) 31%; up to +10 points | [29] |
| Hard answer-only schemas raise wrong-but-valid answers at 3B or less | Qwen2.5 0.5B/1.5B/3B, SmolLM2-1.7B; synthetic deterministic reasoning, not multiple choice | Validity 61.5% → 100% while accuracy 19.7% → 11.0% and wrong-but-valid 49.5% → 88.9%. In the schema comparison, rationale + answer 36.5%, answer-only 26.8%, delayed constraint 40.7%. A calendar tool call: 91.5% prompt-only against 48.0% hard schema, both fully valid. Results varied by serving backend | [30] (2026 preprint) |
| Constrained decoding did not lower semantic accuracy in another setting | Qwen3-0.6B, Llama-3.2-1B and 3B, Phi-4-mini, Qwen3-4B; extraction and function-call tasks | Llama-3.2-1B 0.771 → 0.986 with XGrammar on receipt extraction (type coercion); Qwen3-4B 1.000 in every mode; a residual "semantic gap" for the smallest models, and "hollow rescues" (valid structure, empty content) | [31] (2026 preprint) |
| Format loss is a capacity effect | Small cloud models | "Think first, format later" recovers 80–87% of the loss | [32] |
| Grammars built per input beat free extraction | LLaMA-7B and 13B | Closed information extraction F1 11.9 → 23.5 and 12.9 → 30.6; entity disambiguation 42.0 → 73.4 (7B) | [33] |

**Reading** [I]: a constraint hurts when it forbids reasoning the task needs, or forces a value or field order the model would not
produce. One-token Picks and closed Fill fields need little reasoning. That fits Plotroom's 0 parse failures in 4,356 local calls
and 0.90–0.97 Pick pass^3 [V per docs 44, 46]. Rules that follow:

- any rationale field comes first, in both property order and `required` order;
- the field is bounded at both ends;
- the wrong-but-valid rate is tracked;
- a thinking arm answers in a second, constrained phase.

### 2.4 Harness-side reasoning: code decides, or code computes

| Finding | Models and task | Effect | Source |
| --- | --- | --- | --- |
| Code should draw the conclusion from the model's structure | 12 models incl. Qwen3 1.7B/4B/8B, Llama-3.2-3B, Falcon-3 3B/7B, Gemma-2 2B; 4 benchmarks | Models look consistent with their own rubrics or checklists but seldom update when the structure is edited (on AVeriTeC, mean 0.72 against 0.49; a gap of about 18–23 points on three of four datasets). With a tool deriving the decision, the gap is below 0.03 in most configurations (eight models, 1.7B–32B; Qwen3-4B not among them). The smallest models still slip on the tool step (Gemma-2 2B residual 0.26 on RiceChem) | [34] |
| Typed rules plus a solver, on the sizes we target | Qwen3-4B-2507; Gemma-3n-E4B; Phi-4-mini-reasoning | Qwen: 0.983 in 1 call against 0.700 for 5-call self-consistency (direct 0.675); BBH-derived 0.933 against 0.283. Gemma-3n-E4B 0.683 against 0.367, but 0.375 against 0.350 on BBH-derived (not significant). Phi-4-mini 0.042 against 0.183 direct (formalisation failures) | [35] |
| Program- and solver-aided reasoning (larger models) | Codex; StarCoder+ 15.5B; GPT-3.5 and GPT-4 | PAL +15 over PaLM-540B CoT on GSM8K [36]; PoT about +12% over CoT [37]; Faithful CoT beats CoT on 9 of 10 benchmarks and is faithful by construction [38]; Logic-LM +39.2% over standard prompting, +18.4% over CoT [39]; LINC beats GPT-3.5 CoT by 38 and GPT-4 CoT by 10 on ProofWriter [40]; SatLM +23% over PAL on a hard subset of GSM [41]; a 7B model in a code-driven select-and-infer loop beats a 280B baseline [42] | — |
| Applying the rule is the bottleneck | RuleArena | Models confuse similar rules and miscompute after choosing the right one; oracle tools help significantly | [43] |
| Code-guided scaffolds for small models, at a price | Gemma 4 E2B, Nemotron-3-Nano-4B, others up to 24B | Macro accuracy 38.1 → 66.2, but about 7× the solver tokens, 14.4% extraction failures, generated code that hard-codes answers, and regressions (Gemma 4 E2B −5.4 on Time-MQA). The authors call it an audit of retained runs, not a controlled study | [44] |
| Decompositions pay when someone good writes them | GPT-3-class models | Least-to-most: 99% against 16% for CoT on SCAN [45]; Plan-and-Solve [46]; high-quality external hints +9.7 for Llama2-70B-Chat, self-generated hints fail at 7B (to recheck) [47]; decomposition distils easily, solving does not [48] | — |
| A structured summary plus a deterministic compiler | Clinical forms | A 9-key model summary compiled with no model into a 134-item form, macro-F1 0.63–0.69 [49]; practitioner claims for schema-guided reasoning on a 4B model [50, anecdote] | — |
| Short retrieved instructions help above about 3B | 13 models, 1B–14B; procedures written offline by a teacher model | MedQA +9.4, MMLU-Law +7.9; concise beats verbose; model family dominates | [51] |
| Exemplar rationales: relevance beats validity | Few-shot CoT | Invalid rationales keep 80–90% of CoT's gain [52]; machine-built demonstrations can match hand-written ones [53] | — |

**Reading** [I]: no primary study found gains at 1–9B from *model-written* plans on multiple choice or extraction [U]. The
supported pattern is a decomposition authored by code, with the conclusion drawn by code. That is doc 21 §4.1's IntentFill →
Dispatch and doc 55 §4.2's extract-then-dispatch.

### 2.5 Changing what the model reads

- **Priors beat in-context rules.** Inverse-scaling tasks such as memo trap and redefine show models preferring memorised patterns
  over in-context definitions [54], and counterfactual task variants degrade [57].
- **Attribution framing and counterfactual demonstrations.** Framing the context as someone's statement, plus an instruction to
  follow it, cut text-davinci-003's share of answers that kept the memorised fact from 35.2% to 9.1% and lifted exact match from 6.2
  to 48.6, zero-shot; counterfactual demonstrations took exact match to 80–85. For LLaMA-2-7B, exact match went 3.5 → 13.7 from
  the instruction, and 39.2 → 49.6 with counterfactual demonstrations. All these rows were read from a rendering and are to be
  rechecked [55]. Context-aware decoding also helps in conflicts, but needs two passes and custom sampling [56].
- **Irrelevant details.** Adding "feel free to ignore irrelevant information" lifted code-davinci-002 CoT on GSM-IC from 72.4 to 77.8
  [58]. System 2 Attention (LLaMA-2-70B-chat rewrites the context without the irrelevant parts) took TriviaQA with opinions from
  62.8 to 80.3 and GSM-IC from 51.7 to 61.3 [59].
- **Prompt repetition.** With reasoning off, repeating the query won 47 of 70 model-benchmark tests with 0 losses (Gemini, GPT,
  Claude and DeepSeek models). Outputs did not lengthen and latency did not rise. Gains were larger when options came first, and a
  padding control gave nothing [60]. Re-reading: Llama-2-70B GSM8K CoT 49.73 → 56.71, while Llama-2-13B gained only 0.4–1.1 [61].
  Neither was measured on open 1–9B models [U].
- **Word overlap and negation.** Models over-use lexical overlap [62] and handle negation poorly [63].

### 2.6 Selection-side methods for menus

- **Score-based elimination works; generative elimination does not.** FLAN-T5-XL (3B) scored every option, masked the low ones and
  predicted again. It was best or second best on all 8 tasks, with large gains on logical deduction (+13.8) and conceptual
  combinations (+12 over the next method), and it was not consistent on commonsense and social tasks [64]. Asking the model to
  explain why each option is wrong always underperformed choosing the right answer, for GPT-3.5, LLaMA-2 and Falcon [65] (per-model
  gaps to recheck).
- **Pairwise comparison.** Pairwise ranking, scored in both orders to cancel position bias, let Flan-UL2 20B rival GPT-4's listwise
  ranking [66]. Knockout best-of-N with a trained pairwise judge gained 40–60% relative on the hardest half of MATH-500 [67]. No study
  of pairwise multiple-choice selection at 1–9B was found [U].
- **Order.**
  - Reordering options moves accuracy by 13–75%, and the sensitivity sits between the top two or three candidates [68]. PriDe
    removes the letter prior [69]; permutation self-consistency marginalises over orders [70].
  - A cyclic permutation improved 5 of 6 models on each of MMLU and ARC; the six include Llama 3.1 8B and Qwen 2.5 7B. "Answer
    freely, then match" hurt 11 of 12 model-benchmark pairs, and lower order sensitivity did not imply higher accuracy [71].
  - Text answers are more robust than first-token probabilities where the two disagree [72].
- **None of the above.** When "none of the above" is right, 28 LLMs drop 30–50% [74]. Aligned models often fail to reject every
  option; Llama 3.1 8B rejected none in any condition (as read from the HTML; to recheck). A warning that the answer may be missing
  changed some models' behaviour and not others', and CoT improved this "reflective judgement" ("improvements exceeding 85%", the
  paper's wording, over a pool that includes 7–8B models) [75]. An "I don't know" option that is never the answer lifted
  Llama-3-8B-Instruct by 2.0–8.4 points on three benchmarks, mainly by reducing selection bias [73]; it tests debiasing, not escape
  recall. Plotroom's `X` escape is a real answer, which makes it closer to [74, 75]. This is the one Pick class where the
  literature says some model reasoning helps small models.

### 2.7 Test-time compute: sampling, verifiers, self-critique

- **Self-consistency.**
  - PaLM-540B with CoT: GSM8K +17.9, ARC-Challenge only +3.9 [76].
  - Adaptive stopping used up to 7.9× fewer samples at under 0.1% loss [77]; soft self-consistency matched plain self-consistency with
    half the samples [78].
  - More calls help easy queries and hurt hard ones [79].
  - Ours: K = 3 bought +1.6 points for three times the calls [V per doc 53].
- **Verifiers.** Coverage grows log-linearly with samples, but without an automatic verifier voting plateaus [80]. With a process
  reward model and compute-optimal search, a 1B model beat a 405B model on MATH-500 [81]. Both need a trained or automatic verifier.
- **Self-critique.**
  - Intrinsic self-correction lowered accuracy: GPT-3.5 on CommonSenseQA fell from 75.8 to 38.1 after one round (41.8 after two)
    [82].
  - Locating the error is the bottleneck: GPT-4 found it 52.87% of the time, and correction given the location gained 18–44 points
    [83].
  - At 13B or less (LLaMA-2-13B, Gemma-7B), a trained self-verifier added little, while GPT-4 and oracle verifiers added several
    points each; the self-correction is bottlenecked by the verifier, not the refiner [84] (per-cell ranges to recheck).
  - Self-correction works only with reliable external feedback [85]. Independent verification questions reduce hallucination [86].
- **Contrast.** Contrastive CoT (valid and invalid demonstrations) took GPT-3.5 on GSM8K from 69.2 to 79.0 [87]. Contrastive decoding
  gave LLaMA-7B +3.6 on GSM8K but −2.7 on CommonsenseQA [88].
- **Mapping** [I]:
  - Plotroom's repair quotes one code finding with the recomputed allowed values (doc 25 §7.2). That is the "external feedback with
    location" regime the evidence supports, so keep it.
  - Fill has automatic verifiers (quote check, types, admission), so sampling until the first admitted answer is legitimate there.
  - Pick has no semantic verifier, and a 4B model is a weak judge of itself.

### 2.8 Injected thought

- **Thinking Intervention** inserts guidance text into a reasoning model's thinking. On the DeepSeek-R1 family (7B and larger, plus
  QwQ-32B) the abstract reports up to 6.7% on instruction following (the largest gain was R1-Qwen-32B's; R1-Qwen-7B went 55.08 →
  60.99 on IFEval), 15.4% on instruction hierarchy and a 40.0% rise in refusals of unsafe prompts. The authors attribute it to
  reasoning-phase attention staying mostly on the model's own reasoning tokens rather than on the prompt [89]. Every model had
  thinking on; nothing was tested with thinking off or below 7B.
- **Thought Manipulation** places an external chain of thought between the think tags. QwQ-32B produced about 30% fewer output tokens
  at equal accuracy. The named failure mode is "blindly following flawed external reasoning" [90].
- **Speculative Thinking:** a 32B model writes the reflective steps inside a 1.5B model's thinking; MATH500 83.2 → 89.4 [91]. It needs
  a second model, which D023 allows only by the user's binding.
- **NoThinking** shows that the think block can be closed by a prefill [9].
- **Filler dots and pause tokens** need training [92, 93].

### 2.9 Thinking control on the pinned runtime and the target models

- **Per-request budget** (llama-server b11146) [94, 95] [V at source]:
  - `reasoning_budget_tokens` (alias `thinking_budget_tokens`): −1 falls back to the server's `--reasoning-budget` (unlimited by
    default), 0 closes the block at once, and N caps it.
  - `reasoning_budget_message` is forced in before the end tag.
  - Also available: `chat_template_kwargs.enable_thinking`, and `--reasoning-format` (default `auto`).
- **How the cap is enforced** [96, 97] [V at source]:
  - A sampler state machine finds the tags. At the cap it waits for a complete UTF-8 character, which matters for Czech, Polish and
    Russian text. It then forces the message and the end tag, setting every other logit to −∞.
  - The sampler also accepts prefilled tokens before sampling, so a prefilled seed presumably counts against the budget [I; canary
    C4].
  - The cut can land mid-sentence. Graceful termination is an open issue [104]. A draft PR's "soft" and "intro" messages disarmed the
    cut-off and lowered accuracy in its own tests [103]. Gemma 4 gained budget support on 2026-04-10 [102].
- **Schema only after the thought, by code reading** [98, 99, 100, 101] [V at source; U until canary C2]:
  - Qwen3.5 (the `qwen3-coder` parser) builds a grammar of optional free thinking up to `</think>`, then the schema, and is not lazy.
  - Gemma 4 allows an optional thought channel, then the schema inside a mandatory ```` ```json ```` fence.
  - Other Jinja templates use the auto parser, which works the same way. Without `--jinja`, the legacy path applies the schema from
    the first token.
  - **Trap:** `reasoning_format: none` empties the reasoning rule. With a schema, the JSON must then start at once, inside the open
    think block for templates that open one [98].
- **Counter-evidence.** Issue #20345, opened 2026-03-10, found the grammar inactive with thinking on: Qwen3.5-35B-A3B returned HTTP 500
  with fenced JSON, and Qwen3-VL-8B returned wrong fields [105]. Our two reads on 2026-09-28 disagree on whether it is now closed, and
  neither found a linked fix [V; status U]. LM Studio issue #1773 reports the schema applied to the reasoning stream for Qwen3.5 [106].
  A thinking-on plus schema canary must pass on the pinned build first.
- **Assistant prefill** [95, 98, 99, 108, 110] [V at source]:
  - `continue_final_message` takes `true`, `"reasoning_content"` or `"content"`, and `--prefill-assistant` is on by default.
  - Qwen3.5 renders `<|im_start|>assistant\n<think>\n{reasoning_content}`, adding `\n</think>\n\n{content}` for content continuation.
  - Gemma 4 renders `<|channel>thought\n{reasoning_content}`, adding `<channel|>{content}`.
  - Hugging Face transformers and vLLM have the same semantics. vLLM also constrains only after the reasoning unless told otherwise
    [109].
- **Model controls** [111, 112, 113, 114, 115] [V-vendor]:
  - **Qwen3.5-4B:** thinks by default; switching it off renders an empty think block, and there is no soft switch. The Qwen3 cards
    warn never to decode greedily in thinking mode. Qwen3 was trained to answer from a forced-closed block using a fixed early-stop
    sentence, and Qwen documents a two-pass budget recipe [7, 115]. Whether Qwen3.5 inherits that behaviour is [U].
  - **Gemma 4 E4B:** thinking is switched by `<|think|>` at the start of the system prompt, so thinking arms need their own cache
    namespace (doc 40 R4). E4B emits no empty block when thinking is off.
  - **Granite 4.2-3B:** `enable_thinking`, a `low_effort` switch, temperature 1.0.
  - **Granite 4.1 3B and Qwen3-4B-Instruct-2507:** no think channel.
- **Engines other than llama-server.** Ollama has thinking on or off only; its budget PR is open [107]. Budget arms are therefore
  llama.cpp-only locally.
- **Our records.** Every stored call re-counted here ran with thinking off (0 thinking characters in 4,356 records), and none used
  `--why` [V per doc 46; V, file listing]. Records written after this draft by a separate run are not used (Verification notes).
- **Cloud.**
  - OpenRouter takes `reasoning.max_tokens` or an effort level; Anthropic budgets have a 1,024-token floor; reasoning counts against
    `max_tokens` [116].
  - DashScope budgets run from 1 to 32,768 [115].
  - Prefix continuation exists on some endpoints only [117].
  - Consequence: 32–256-token budgets cannot be expressed on several routes [I].

### 2.10 How far this evidence transfers

1. Most CoT, decomposition, contrast and self-consistency gains were measured on math or symbolic tasks, with 70B+ or API models.
   Evidence at 1–9B on multiple choice and extraction is thinner and more often negative.
2. Many key sources are 2026 arXiv preprints [5, 15, 16, 18, 30, 31, 32, 34, 35, 44, 71], including the two harness-side results
   the TL;DR leans on [34, 35], and one is a workshop paper [8].
3. Some figures were read from HTML renderings and must be rechecked verbatim before they are cited further:
   - the LLaMA-2-7B rows of [55], and which text-davinci-003 column holds 35.2 and 9.1;
   - the 7B hint failure of [47];
   - the cell placement of [18]'s Qwen3-4B rows;
   - the per-model gaps of [65], the per-cell verifier ranges of [84], and the Llama 3.1 8B row of [75].

   The review of 2026-09-28 read the tables of [5], [15], [16] and [35] and the wording of [75] from the arXiv HTML; see the
   Verification notes.
4. The best prompt format does not transfer between models (doc 55 §1.2). Every arm below is measured per model on our own suites,
   and nothing is adopted from a published number alone.

## 3. Our failure types, and which scaffolds target them

### 3.1 Method

- **Records.** 3,348 stored plain calls on the tuning split [V, offline re-count, no new calls]:
  - Qwen3.5-4B in four arms: 720 `pick`, 720 `pick-hard` and 108 Fill records;
  - Gemma 4 E4B in four arms: 720, 720 and 144;
  - Granite 4.1 3B from doc 44 on Ollama: 180 `pick` and 36 Fill records. No Granite `pick-hard` record exists.

  Each suite has one hash across all records. There are 0 parse failures, 0 `why` records and 0 thinking characters.
- **Typing.** Each miss gets one primary type, by hand, per (item, chosen option). Precedence is escape > counter-intuitive rule >
  lure > near-miss, and secondary tags are kept. Two tests are computed:
  - **Word overlap:** does the chosen option share more stemmed request words than the answer?
  - **Order-conditional:** the model family answered the same menu right in at least 7 of 8 calls under another permutation, and
    wrong in at least 25% under the failing one.
- **Limits.** Arms of one family are near-copies of one model, so the counts describe and do not test. Qwen's 87 rule misses come
  from only 9 menus.

### 3.2 Pick

Order-conditional misses are in brackets.

| Primary type | Qwen3.5-4B (1,440 calls) | Gemma 4 E4B (1,440) | Granite 4.1 3B (180, `pick` only) |
| --- | --- | --- | --- |
| Counter-intuitive rule: the everyday word fits, the engine rule excludes it | 87 [26] | 54 [25] | 10 [0] |
| Lure: the option echoes the request in words or meaning | 39 [10] | 27 [2] | 1 [1] |
| Near-miss: a decisive detail missed (roles, numbers, one of several constraints) | 22 [11] | 6 [4] | 7 [2] |
| Escape under-use: a real option chosen where `X` was right | 14 [14] | 2 | 0 |
| Escape over-use: `X` where an option fits | 0 | 1 | 0 |
| Format | 0 | 0 | 0 |
| **Misses** | **162** | **90** | **18** |

**Items behind the types** [V]:

- **Qwen, rule:**
  - PW04 (UNLOAD against TR UNLOAD) 22;
  - HT03 24: End #1 + End #2 in 20, End #1 + None in 4;
  - HW04 (CYCLE placement) 12, HT04 8, HW03 (HOLD never finishes) 7, PW05 (SENTRY for GUARD) 7;
  - HT01 3, HT02 3, PT03 1.
- **Qwen, lure:**
  - HK01 Cutscene 17. This is a *meaning echo*: Cutscene shares no content word with the request, the answer shares one.
  - HV01 PerCampaign 7 and presence 3; PW02 MOVE 6 (the request says "MOVE" twice); HC01 4; HW03 SEEK AND DESTROY 2.
- **Qwen, escape under-use:**
  - HM04 12: Respawn point 4, every one lured by "come back", which the request negates; Interaction 4; Reinforcements 3; Random
    choice 1.
  - HA03 2.
- **Gemma, rule:** PW04 24, HT03 11, HW04 8, HT01 6, HW03 5.
- **Gemma, lure:** HV01 PerCampaign 16; HW03 SEEK AND DESTROY 8; HW05 GET IN 2; HR03 1, which obeyed an instruction quoted inside
  marker text.
- **Granite, rule:** PW04 6; PT04 (Countdown chosen where Timeout was needed) 4.
- **Granite, near-miss:** PK03 (an arc-shape sequence) 5.

Counting lures as secondary tags too, word overlap favoured the wrong option in 57 of Qwen's 162 misses, 55 of Gemma's 90 and 7 of
Granite's 18 [V]. The rule items are not a Qwen quirk: PW04 was wrong in every card call for all three models (Qwen 12, Gemma 12,
Granite 3), although the card states the rule [V].

### 3.3 Systematic, not random

| | Qwen3.5-4B | Gemma 4 E4B | Granite 4.1 3B |
| --- | --- | --- | --- |
| Misses | 162 | 90 | 18 |
| Order-conditional | 61 | 31 | 3 |
| Fixed by a majority of 3 permuted samples | 44 | 28 | 4 |
| In majority-wrong cells | 118 | 62 | 14 |
| … of which unanimous on the same wrong option | 48 | 36 | 9 |

Per menu, Qwen3.5-4B Q4_K_M on llama.cpp had these `pick-hard` results over 30 menus × 3 samples [V]:

- without cards: 21 unanimous-right, 2 unanimous-wrong (HT03, HK01) and 7 split;
- with cards: 23 unanimous-right, 1 unanimous-wrong (HT03) and 6 split.

Gemma 4 E4B QAT had no unanimous-wrong menu. HT03's wrong answer for Qwen was stable across every permutation, so it is
content-driven, not positional. HM04's escape misses were order-conditional: 7, 4 and 1 of 8 across its three orders.

**Consequence** [I]: voting, more samples and self-critique address at most the order-conditional share. The rest need a scaffold
that changes what the model sees (the rule, the consequences, the separating attribute) or takes the decision away from it.

### 3.4 Fill

| Field error type | Qwen3.5-4B (63 of 504 fields) | Gemma 4 E4B (31 of 672) | Granite 4.1 3B (35 of 168) |
| --- | --- | --- | --- |
| Over-inference: a value where "unspecified" was right | 22 | 7 | 15 |
| Catch-all "other" chosen for a recognisable value | 13 | 0 | 0 |
| Span paraphrase: target recomposed, reordered or language-mixed | 9 | 0 | 3 |
| Enum near-miss: squad → small, although the instruction glosses medium as "about one squad" | 9 | 11 | 5 |
| Decoy taken: a finding code filed as a place; "three uses" as a size; "dawn shot" as atmosphere | 6 | 11 | 4 |
| Span boundary: a verb phrase or whole clause instead of the target | 3 | 2 | 0 |
| Omission: place left empty where the request named one | 0 | 0 | 6 |
| First-value default | 1 | 0 | 2 |

Two position patterns appear [V]:

- All 9 over-inferred `side` values were `west`, the first listed value. The first listed task took 7 of Granite's 8 task errors.
- Qwen instead defaulted to the last task value, `other`, in 13 of its 18 task errors.

One Fill target hit the 60-character `maxLength` mid-word. A quote check should reject a span that stops exactly at the cap.

### 3.5 Cards can create lures

With cards, Gemma's lure misses rose from 7 to 20 [V]:

- HW03 SEEK AND DESTROY went 0 → 8: the card names it.
- HV01 PerCampaign went 6 → 10: the card's gloss ("the same across restarts, Retry and save loads") echoes the request's "restarts …
  retries".
- For Qwen, HW03 HOLD went 2 → 5.

A card that restates every option's rule adds request-echoing text to the distractors. This is one mechanism behind doc 55's
finding that the card effect changes sign by model and item. It argues for giving the model only the rule sentence that separates
the leading candidates (S2), not a whole paragraph [I].

### 3.6 From failure type to scaffold

| Failure type | What the literature predicts | First scaffolds (§4) | Not useful here |
| --- | --- | --- | --- |
| Counter-intuitive rule (context against prior) | Priors override in-context rules [54, 57]; CoT rationalises the prior [3, 24]; a solver beats CoT [2, 38]; counterfactual demonstrations move a 7B model more than instructions do [55] | S7 dispatch; S1 consequence lines; S4 code-written thought (experimental); S13 counterfactual exemplar; S12 attribution framing | Voting (HT03 0 of 24); self-critique [82] |
| Lure: lexical, negated cue, meaning echo | Overlap heuristics [62]; distraction [58, 59]; longer thinking distracts more [11]; negation is weak [63] | S1 option-diff contrast, mention resolution, negation flags; S2 instead of full cards; S12 "ignore details"; S11 repetition; S7 for meaning echoes | Long thinking budgets |
| Near-miss | Score-based elimination helps [64]; order sensitivity sits between the top two or three [68] | S5 elimination; S6 pairwise on the top two; S7 attribute questions; code numeric filters | Generative elimination [65] |
| Escape under-use | "None of the above" costs 30–50% [74]; some reasoning helps rejection [75]; reasoning lowers abstention [21] | S7 coverage check; `X`-mass threshold; S3 a bounded `why` on escape-bearing kinds only | Thinking without an escape gate |
| Order-conditional | Permutation methods [69, 70, 71] | Permuted samples, cyclic re-ask on a low margin, prior removal | — |
| Fill span paraphrase, boundary, omission | Grammars built per input help [33]; CoT raises omission [6] | S8 verbatim grammar or code candidates; place pre-fill from the island's place list | Any reasoning field on Fill |
| Fill over-inference and catch-all | Verification questions [86] | S8 cite-or-abstain; registry-token annotations; enum order permuted | — |
| Fill enum near-miss | — | A code lexicon (fireteam → small, squad → medium, platoon → large) as a *rule* with its own tests (§5.2) | — |

The tune half of the staged Pick pool (30 items; tune split only) will carry these arms. Its traits, as of the pool revision
rebuilt after this draft on 2026-09-28 [V, from the pool's metadata; tune half only]:

- 8 rule-bearing items, 12 lexical lures and 7 semantic lures (6 of them without a lexical tag); traits overlap;
- 6 escapes: 1 near-fit, 2 out of scope, 1 unsupported by the named target profile, 2 unsupported by the engine;
- 1 escape decoy, 1 injection item, and 5 items with dispatch sketches.

The draft's earlier tally (10 lexical and 4 semantic lures; 2 profile and 1 engine escape) matched the pre-review pool except for
the semantic lures, which were 7 there too. The pool is still staged, so these counts are re-read from its metadata before any run.

## 4. The scaffold catalogue

### 4.1 Overview

Costs use the reference GPU's stored rates [V, from `timings`]: Qwen3.5-4B Q4_K_M decodes at about 42 tokens/s and prefills at
280–310 tokens/s, and a pick is about 300 prompt tokens and 7 output tokens, with a p50 of 1,046 ms. So 100 extra prompt tokens in
the uncached dynamic tail cost about 0.35 s, and 40 extra decode tokens about 1 s [I, arithmetic].

| Id | Scaffold | Step kinds | Targets | Added cost per decision [I] | Main risk | D048 knob (§4.4) |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | Option-diff annotation and consequence lines | PICK | Rule, lure, near-miss | +40–120 prompt tokens (≈0.15–0.4 s); no decode | An asymmetric line leaks the answer; anchoring on code's framing | `layout.annotations` |
| S2 | Decisive-rule extraction: code selects the card sentence | PICK, EXPLAIN | Rule; card-induced lures | Replaces the card: −50 to −100 prompt tokens against `cards` | A wrongly selected rule gives a confident error | `layout.cards.mode = decisive_sentence` |
| S3 | Structured rationale before a constrained answer | PICK, escape- and rule-bearing kinds only | Escapes; maybe rules | +30–45 decode tokens (≈0.7–1.1 s, +70–100%) | Rationalises the prior; lost escapes; answer-first order | `answer.why`, `answer.rationale` |
| S4 | Code-written thought (reasoning prefill of a code-built skeleton) | PICK; closed FILL fields as a control | Rule | Closed: about +100 prompt tokens (≈0.35 s). Open with budget B: up to B/42 s more | Thinking plus schema breakage; an out-of-distribution block; anchoring | `reasoning.thought`, `reasoning.thought_id` |
| S5 | Elimination rounds, score-based | PICK | Near-miss, order | One prefill-only scoring call, plus one re-ask on the top 2–3 when the margin is low | Masking the answer; the letter prior | `scoring.elimination` |
| S6 | Pairwise tournament on the top two or three | PICK | Near-miss between two candidates | 2–6 short calls, only when triggered | Position bias (score both orders); cost | `scoring.pairwise` |
| S7 | Targeted sub-questions with code aggregation: dispatch, coverage check, attribute elimination | PICK, FILL | Rule, meaning-echo lure, escape, near-miss | One closed-field Fill (15–30 output tokens) instead of, or before, the Pick: 1–1.5× a pick | A facet the request does not answer (then ask); authoring cost; table bugs | `decomposition.mode` |
| S8 | Quote-then-fill and verbatim spans | FILL | Paraphrase, boundary, omission, over-inference | Verbatim grammar: no extra decode. Quote field: +10–20 tokens per span | Grammar build cost; diacritics | `fill.decomposition.spans` |
| S9 | Verifier-guided sampling: stop at the first admitted answer | FILL; PICK only where code can falsify | Random Fill errors | Expected 1 + failure-rate calls | No semantic verifier for Pick | `voting.stop = first_admitted` |
| S10 | Small thinking budget on hard steps only, triggered by the cascade | PICK, rule-bearing or disputed | Rule | Fires on disputed menus (13–27% for Qwen3.5-4B); B/42 s each: 64 → 1.5 s, 128 → 3.1 s | Coupling tax; lost escapes; loops | `reasoning.mode = budget`, `reasoning.trigger`, `cascade.route` |
| S11 | Request repeated after the menu | PICK | Lure, near-miss | +60–150 prompt tokens (≈0.2–0.5 s); more on CPU | Unmeasured on open small models | `layout.id` |
| S12 | Instruction and framing variants: "ignore details that do not change the decision"; attribution framing | PICK | Lure, rule | +15–30 prompt tokens, cache-stable | Small effect | `layout.instruction_variant` |
| S13 | One frozen contrastive or counterfactual exemplar with a code-templated rationale | PICK | Rule, lure | +80–150 prompt tokens, cache-stable | Copying the exemplar's answer; exemplar text acting as a lure | `layout.exemplars` |

### 4.2 Notes per scaffold

**S1 Option-diff annotation and consequence lines.** Code renders, for *every* option, the attribute values or the engine
consequence that its catalogue or engine model defines. For HT03 [I; rendered from the trigger-type rule, not from the answer]:

```text
What each option does (computed by the editor from the trigger rules):
A) Both End #1: the mission ends in victory when both triggers are active at the same time.
B) End #1 and End #2: the mission ends as soon as either trigger is active, with a different ending for each.
C) End #1 and None: only the radar trigger can end the mission; the village trigger runs only its own code.
…
```

- **HK01:** the same device becomes an attribute table from the node catalogue ("branches? decided by whom?"). It shows that
  Cutscene never branches and that Decision branches on campaign state.
- **Other line types:**
  - *mention resolution* from mission state: "SEEK AND DESTROY (already the squad's next waypoint)";
  - *negation flags* on options whose matched words fall inside a negated span of the request (HM04's "come back");
  - an *overlap contrast* when one option leads on shared words: "B and F share words with the request; they differ in …".
- **Why it helps:** the model is left with intent-to-consequence matching, the part small models do well, and code does the rule
  application [38, 43].
- **Risks:** a line written only for the leading options can leak which options code thinks matter. Rule: every line type is
  emitted for all options or for none.
- **Knob:** annotation ids in the prompt pack (`consequence.v1`, `option_diff.v1`, `overlap_contrast.v1`, `negation_flags.v1`,
  `mention_resolution.v1`).

**S2 Decisive-rule extraction.** Code sends the one card sentence that governs the attribute on which the menu's options differ,
instead of the whole card. For `trigger.end_type`, that is the End-number rule when the options differ in End numbers. The sentence
is selected by DecisionKind, by the option set and by code-extracted request features (for example "two objectives"), never by the
answer.

- **Targets:** Gemma's card-induced lures (§3.5), and prompt size.
- **Risks:**
  - The selector picks the wrong sentence: a confident error.
  - It can fail to find the separating attribute without a first-pass distribution. The fallback is the full card, and S5's top
    two can supply the pair.
- **Knob:** `layout.cards.mode = decisive_sentence`, with the selector id in the prompt pack.

**S3 Structured rationale before a constrained answer.** Two forms:

- **Bounded `why`:** 40–160 characters, with `minLength` and `maxLength`, both properties required and `why` first. Today's
  `run.py --why` sets only `maxLength` 160.
- **Checklist:** authored fields answered first, then the letter, in one reply. For example "requirement:", "an option covers every
  part: yes/no".

Evidence and risks:

- The evidence is mixed at this size (§2.1, §2.3). The strongest case is escape-bearing menus [75]. The main risks are rationalising
  the prior [24] and justifying a near fit, which lowers `X` recall.
- The checklist form is the control for S7. Same questions; only the decider changes [34].
- The `why` a model writes is not the cause of its choice. It is shown as a model's note (§5.4).

Knob: `answer.why{mode, min_chars, max_chars}` and `answer.rationale = checklist:<id>`. This is doc 53 R7's arm (g) and doc 55's
H-Q7, read per DecisionKind.

**S4 Code-written thought (reasoning prefill of a code-built skeleton).** Code renders a short thought from the prompt pack into the
model's think channel, using `continue_final_message`. The text is the DecisionKind's rule restated as a check, plus a checklist.

- **Closed** (`"content"`): the block is closed and the model answers at once under the schema; there is no thinking decode.
- **Open** (`"reasoning_content"`): the block stays open. The seed ends on a commitment slot ("Options whose effect matches every
  stated requirement:"), after the function-routing form in [15]. Budget B then applies, followed by a forced close.

For a module menu on Qwen3.5 [I; the text restates the module card, identical for every module menu]:

```text
<think>
Module menus: choose the most specific wave-1 module whose parameters cover the whole request; if none covers it, choose none fits.
Not available yet (wave 2): alert network, minefield, vehicle respawn, revive, air drop, demolition, multi-group command, timer.
Check: what must the module create or bring back, and do one option's parameters cover all of it?
</think>
```

- **Evidence:** text inside the thought outweighed prompt reminders for 7B+ reasoning models [89]. HT03's card failed in the user
  turn for Qwen (0 of 12 with it), so the thought channel is the natural next test [I].
- **Risks:**
  - The model follows the thought blindly [90].
  - A non-empty block while thinking is "off" may be out of distribution. Qwen3.5 is trained on an empty block; Gemma E4B emits none.
  - Thinking and the schema may interact badly on some builds (§2.9).
  - Gemma's continuation renders one newline where the model emits two.
- **Trust rule:** the thought holds only prompt-pack text and code-rendered facts, never mission text, user text or plugin output
  (§5.1).
- **Knob:** `reasoning.thought = none | code_closed | code_open`, `reasoning.thought_id`, plus `reasoning.budget_tokens` for the
  open form.

**S5 Elimination rounds, score-based.** One prefill-only call reads the letter probabilities (doc 53 instrument 1). Code masks
options below a threshold, then re-asks the top two or three under a fresh permutation. This is doc 55's top-two cascade route, and
the score-based elimination of [64]. The model is never asked why options are wrong [65].

- **Risks:** masking the right option when the margin is misleading. The rule: never mask `X`, and never mask more than the menu
  minus three.
- **Knob:** `scoring.elimination = off | keep_top{2..3}`.

**S6 Pairwise tournament.** Only over the top two or three after scoring. Each pair is asked in both orders, with S1's contrast line
for the pair. A knockout over a full seven-option menu would cost 6 calls (12 with both orders), so it is ruled out.

- **Evidence:** at 1–9B for multiple choice it is [U] [66, 67].
- **Knob:** `scoring.pairwise = off | top_k_both_orders{2..3}`.

**S7 Targeted sub-questions with code aggregation.** The model answers closed questions in the user's terms, one small Fill with at
most three facets (doc 53's facet cap). Code applies the rule table and decides. Three forms:

- **Extract-then-dispatch** for rule-bearing kinds (doc 55 §4.2):
  - HT03-D asks "When should the mission end in victory?" (only once every objective is done / as soon as any one is / each with its
    own ending), and code applies "same End number = AND".
  - The tune pool's QT01 asks "Where should the squad head once the call is made?", and code applies "a Switch is synced to the
    waypoint just before the destination".
- **Coverage check** for escapes. HM04-D asks "What must come back? players / an AI group / a vehicle / an object". Code checks the
  module registry's declared capabilities. If no listed option covers the answer, code decides `X` and says why ("vehicle respawn is
  wave 2").
- **Attribute elimination** for near-misses. HV02 asks "Must the host be able to choose?". Code removes the options that fail, and
  the model picks among the rest.

Cost, risks and knob:

- **Evidence:** [34, 35, 38]; the tuning-split draft has 6 items, plus the pool's 5 tune sketches.
- **Cost:** one closed-field Fill instead of the Pick.
- **Risks:** a facet the request does not answer is "unspecified", so code asks one computed question. A bug in a table is a code
  bug, tested like code (§5.3).
- **Knob:** `decomposition.mode = extract_dispatch | escape_precheck | attribute_elimination`, plus `checklist` as S3's control.

**S8 Quote-then-fill and verbatim spans.**

- **Span fields** get one of two forms:
  - a grammar built per request that admits only the request's own substrings at word boundaries [33];
  - or code-built candidates offered as a Pick (noun-phrase chunks, place names matched against the loaded island). Clauses are never
    candidates, and decoys such as a finding code stay in the list, so the list does not reveal the answer.
- **Closed fields** need a short quote copied from the request. Code checks the quote and falls back to "unspecified" when it is
  empty or has no word from the field's cue lexicon (cite or abstain).
- **Registry tokens** are annotated ("CF01 is a campaign-checker finding code"), and enum order is permuted, or "unspecified" listed
  first.
- **No reasoning field is added to Fill** [6].
- **Knob:** `fill.decomposition.spans = free_quote_check | quote_first | verbatim_grammar | code_candidates`,
  `fill.annotations`, `fill.enum_order`.

**S9 Verifier-guided sampling.** For Fill, draw up to K ≤ effort samples and keep the first one admitted by the quote check, types and
validators. This is legitimate because the verifier is automatic [80]. For Pick, sampling is verifier-guided only where code can
falsify an answer (a numeric range, coverage). Never use a model as its own verifier [84].

**S10 Small thinking budget on hard steps only, triggered by the cascade.** Triggers:

- `on_disagreement`: K = 3 was not unanimous. It reuses samples already drawn, after [25], and fires on 13–27% of Qwen3.5-4B menus.
- `on_low_margin`: from letter probabilities.
- `always`: for named DecisionKinds only.

Budgets are {64, 128}. The call is two-phase:

1. A think call with budget B, under the model's thinking sampler. That is never greedy, and for Qwen3.5 it matches the draft
   preset's Pick sampler: temperature 0.6, top_p 0.95, top_k 20, neutral penalties.
2. A second call closes the trace and reads the letter greedily with letter probabilities.

This decouples the budgets [16] and gives the cascade a margin. The close message is Qwen's own early-stop sentence, by id, for the
Qwen family only; other families get the bare end tag.

- **Limit:** `on_disagreement` cannot reach confident failures. HT03 in both conditions and HK01 without cards were unanimous-wrong,
  so only `always` on a named kind reaches them.
- **Rejected:** budgets of 256 and up locally (PR6, [15, 16]).
- **Knob:** `reasoning{mode = budget, budget_tokens, trigger, close_message_id, answer_pass = split_call}` and
  `cascade.route = same_model_think`.

**S11–S13 Cheap input arms.**

- **S11** repeats the request after the menu [60, 61]. Plotroom's layout is question-first, so a smaller gain is expected. The copy
  sits in the dynamic tail, and the static prefix stays cacheable (doc 40 R2–R3).
- **S12** adds "ignore details that do not change the decision" [58], or attribution framing ("The Standing Orders say … According to
  the Standing Orders, …") [55].
- **S13** is one frozen exemplar per rule-bearing DecisionKind. It applies the counter-intuitive rule to a *different* case and shows
  the lure losing, with a one-line rationale written from a code template [52, 55, 87]. It is frozen per prompt-pack version for
  cache stability.

### 4.3 Per step kind

| Step kind | Default preset | Candidate scaffolds | Excluded |
| --- | --- | --- | --- |
| PICK | Direct, letter, thinking off | S7 for rule- and escape-bearing kinds; S1 and S2; S5 and S6 on a low margin; S3 and S4 as measured arms; S10 only when triggered; S11–S13 | Self-critique, generative elimination, free CoT at 4B or less |
| FILL | Whole-record pre-fill plus quote check | S8, S9; closed fields as Picks (S7); registry annotations; S4 closed only as a do-no-harm check | Reasoning fields, thinking |
| COMPOSE | Authored split on budget | The split *is* a code-authored decomposition (S7); cloud reasoning at the provider floor (DG020) | Model-written plans |
| Creative text | Reasoning off | None; code checks, K candidates and the user's choice already do the work | Thinking: latency, and no verifier |
| EXPLAIN | Explanation plus fix | S2; a code-chosen fix (doc 55 H-G2); for the tiny tier, a card-sentence Pick | Thinking: more hallucination on knowledge [22] |

### 4.4 Proposed preset knobs

This extends doc 55 §3.3's outline. It is proposal-only, and the names are not final:

```text
step_kinds.pick:
  answer        { form, field, why{mode: off|before, min_chars, max_chars}, rationale: none|checklist:<id> }
  reasoning     { mode: off|budget, budget_tokens 0..512, trigger: always|on_disagreement|on_low_margin,
                  thought: none|code_closed|code_open, thought_id, close_message_id: none|<id>,
                  answer_pass: same_call|split_call, reasoning_format: auto (constant) }
  layout        { id, instruction_variant, cards{mode: declared|off|documents|decisive_sentence, format, selector_id},
                  annotations[ consequence.v1 | option_diff.v1 | overlap_contrast.v1 | negation_flags.v1 | mention_resolution.v1 ],
                  exemplars{count, set, rationale: none|code_templated} }
  decomposition { mode: direct|facets|checklist|extract_dispatch|escape_precheck|attribute_elimination, facet_cap }
  scoring       { mode, permutation, elimination: off|keep_top{2..3}, pairwise: off|top_k_both_orders{2..3} }
  cascade       { accept_margin, reask_margin, top2_margin, x_mass_threshold,
                  route: user_card|same_model_reask|same_model_think|code_default }
  output_cap_tokens = answer cap (+ why cap) (+ budget + close message, when reasoning.mode = budget)
step_kinds.fill:
  decomposition { spans: free_quote_check|quote_first|verbatim_grammar|code_candidates, closed_fields, enum_order }
  annotations   [ registry_tokens.v1 ]
  voting        { k_max, stop: first_admitted }
decision_overrides: [ { decision_kind, step_kind, settings, evidence } ]
```

**Rules** [I]:

- Every `*_id` resolves into the versioned prompt pack, and the preset carries no text (doc 55 §1.4).
- `reasoning_format` is never `none` when a schema is sent (§2.9).
- `finish_reason = length` in any phase counts as truncated and is never admitted (doc 21 §8.2).
- Thinking arms get their own cache namespace (doc 40 R4).
- PR1's "0 thinking characters" applies to thinking-off calls. Thinking arms have at most B reasoning tokens and a closed block.
- Local only: a budget knob is valid for llama.cpp setups. Cloud presets use the code-side scaffolds and keep reasoning off, or at
  the provider floor (doc 51).

### 4.5 Borrowed ideas and what is not adopted

- **Adopted as ideas** [I on V]; no code or prompt text is copied, and every licence is MIT or Apache-2.0:
  - DSPy's ChainOfThought is exactly a leading reasoning field [118]. Its BootstrapFewShot becomes S13's offline exemplars, with
    code-templated rationales.
  - GEPA- and MIPRO-style optimisers are dev-time tools that propose prompt-pack variants. A maintainer rewrites them, and they face
    the held-out gate [119, 120]. GEPA on Qwen3 8B: 45.23 → 54.85 aggregate, against 47.84 for MIPROv2 [119].
  - guidance and llguidance programs, which are code-owned segments over one KV cache [121], become S4 and S10's two-phase calls over
    a cached prefix.
  - SGLang's `select` with unconditional-likelihood normalisation [122] becomes a scoring mode that reuses doc 53's content-free
    prior call.
- **Not adopted:**
  - lenient schema-aligned parsing of answers [123], because only exact validated values are admitted (doc 51);
  - any runtime optimiser;
  - executing model-written programs [36, 37, 44];
  - a second model writing thoughts [91] without a user binding (D023 decision 3).

## 5. Generating the reasoning safely

### 5.1 The answer-blind contract

1. **Allowed inputs.**
   - The request's code-extracted features: numbers and ranges, negated spans, place-name matches, word overlap.
   - The code-built menu with typed option metadata.
   - Catalogue and engine facts, and mission state.
   - The versioned prompt pack.
2. **Forbidden inputs.** The item's answer, its rationale, anything written per item, and any preset data (presets carry ids only).
   Untrusted text never enters a code-written thought: mission text, briefings, stringtables, marker text, plugin output (doc 21 §9).
   Untrusted text stays quoted in the user turn, under its trust label. Text inside a thought weighs more than the prompt [89], so
   this rule is stricter there.
3. **Symmetry.** Every per-option template is applied to every option. A contrast is chosen by an answer-blind rule, such as
   information gain over the menu's metadata, or the top two by letter scoring.
4. **Authored before tuning.** Templates, facet schemas, decision tables and sentence selectors are written once per DecisionKind,
   before any tuning call, and shipped as prompt-pack ids with a hash. Their authors have read the tuning items and their failures
   (this doc's HT03 and HM04 examples are such), so the tuning split cannot show whether a template is over-fitted to it. Only the
   sealed held-out look can (doc 55 §4.1), and the template hash is frozen before that look.
5. **Never a verdict.** No scaffold text states which option to choose. General rules that apply to every menu of the kind are
   allowed; "choose none fits if nothing covers it" is a card rule, not a verdict.
6. **Exemplars stay out of the held-out neighbourhood.** An S13 exemplar is a different case, but it must not be a near-duplicate
   of a held-out item. Whoever keeps the held-out split checks this by script (word overlap and the same answer key), so the
   template authors never read held-out items.

A sketch of the type boundary (proposal-only; the crate and names are not final):

```rust
/// Everything a scaffold generator may read. There is deliberately no field for the gold answer,
/// so a generator cannot depend on it; test fixtures keep the answer in a separate struct.
pub struct ScaffoldInput<'capsule> {
    pub decision_kind: DecisionKindId,
    pub request_features: &'capsule RequestFeatures, // code-extracted: numbers, negated spans, place matches
    pub menu: &'capsule [OptionView],                 // typed option metadata from the catalogue
    pub facts: &'capsule FactView,                    // engine and catalogue facts, mission state
}
```

### 5.2 When a hint becomes a rule

A scaffold may make the answer easy, and that is the point, provided the ease comes from the request plus code's facts. If code
alone can decide without the request's meaning, the scaffold is not a hint but a code rule, and it moves into code with its own
tests. Examples:

- the size lexicon;
- a numeric-range filter;
- place pre-fill when exactly one place name matches;
- HT04's "this mission file has no East group", which is a lint fact.

Such rules are validated as code, not measured as model arms.

### 5.3 Leakage and trust tests

In the product, these are Rust `#[test]`s beside the DecisionKind registry, written first per AGENTS.md. In the tuning tooling, they
are script checks that must pass before an arm runs.

| Test | What it proves |
| --- | --- |
| T-L1 Type boundary | The generator's input type has no answer field (§5.1 sketch); it is a compile-time guarantee |
| T-L2 Answer swap | Changing a fixture's gold answer leaves every rendered scaffold byte-identical |
| T-L3 Permutation | Permuting the options permutes the per-option lines and changes nothing else |
| T-L4 Symmetry | Every per-option line type appears for all options or none; a lint refuses templates with a single-option slot |
| T-L5 No verdict | Rendered scaffolds contain no verdict pattern: "the answer is", "choose `<letter>`", "correct option", a lone letter |
| T-L6 Hint-only control | The scaffold is rendered from the real request, then the request is swapped with another item's of the same DecisionKind (or blanked). The scaffolded arm's accuracy is compared, per item and paired, with A0 under the same swap, not with nominal chance: a blank request invites `X`, which is right on escape items and wrong elsewhere, and the letter prior lifts A0 above 1/(n + 1). A gain of more than 10 points over A0's hint-only accuracy means the scaffold chooses by itself: promote it to a code rule (§5.2) or reject it. Escape and non-escape items are reported apart |
| T-L7 Trust | A fixture whose mission data carries an injected instruction never shows that text in the thought channel or the annotations |
| T-L8 Cache | The static prefix of every item of a DecisionKind is byte-identical, and scaffolds sit only in the dynamic tail (doc 40 R2) |
| T-L9 Determinism | The same input rendered twice gives identical text |
| T-L10 Decision tables | Every row is reachable; "unspecified" leads to ask; each tuning item's expected facets reproduce its answer. The draft suite and the pool's sketches already pass this last check [V, checked by script per doc 55]. The tables were written with those answers in view, so this check proves consistency, not generalisation; the held-out dispatch items do that |

### 5.4 The glass box

- **Labels.** The decision inspector labels harness text "written by the editor" and model text "written by the model".
- **For a dispatched decision**, the reason shown is code's rule and the user's facet answer. It is faithful by construction [38].
  Illustrative: "You said: only once every objective is done → rule: trigger types → End #1 on both."
- **A model's `why` or thinking** is shown, if at all, as a note and never as the cause [23, 24, 34]. It is never replayed into a
  repair capsule, and it never bypasses validation.
- **Conflict with doc 21 §8.2.** Doc 21 §8.2 says reasoning text is never stored in the mission, sidecar or session log, while doc 25
  §9.1's inspector shows the `why`. Proposal:
  - the product stores the code-written thought's id and hash, the model's reasoning token count, and the `why` as an untrusted
    answer field;
  - the product never stores model thinking text;
  - research records may keep traces, git-ignored.

  This is design-gap candidate 4 (§7).

## 6. Experiment plan (summary)

### 6.1 Preconditions and canaries

- **Order and tooling.** Runs start after doc 49 frees the machine, one model at a time, on a scratch copy of the run tooling
  (`tools/local-qual` is in use).
- **Data.** Only the tuning split is used. Doc 55 §4.1's sealed held-out sets decide adoption. The staged pools' held-out halves are
  an interim held-out split, unread by the tuner.
- **Canaries.** Before any thinking arm, about 5 calls each, per template, on the pinned build:
  - **C1:** with thinking on, `/apply-template` ends inside `<think>\n` (Qwen3.5), or the system prompt starts with `<|think|>`
    (Gemma 4).
  - **C2:** thinking on plus a strict schema gives non-empty reasoning and schema-valid content. A request that asks for markdown
    still gets bare schema JSON. This guards against a return of [105] or [106].
  - **C3:** budgets 0, 32 and 64 give at most B reasoning tokens plus the message, a closed block and an answer.
  - **C4:** a 40-token seed with `"reasoning_content"` and with `"content"`. The seed appears verbatim, and the run records whether it
    counts against B and whether a non-empty block is accepted while thinking is off.
  - **C5** (negative control): `reasoning_format: none` plus schema plus thinking on documents the trap.
  - **C6:** Gemma's prefill newline, and the ```` ```json ```` fence under `json_schema` against a compact `grammar`.

### 6.2 Arms

| Wave | Arm | What | Models |
| --- | --- | --- | --- |
| 1: who decides | A0 | Default preset | All |
| | A1 | Checklist: the model fills the same facets as A2, then picks the letter in the same reply | All |
| | A2 | Dispatch: same facets; code decides | All |
| | A3 | Coverage check plus `X`-mass threshold on escape-bearing kinds | All |
| 2: what the model reads | A4 | S1 consequence and option-diff lines | All |
| | A5 | S2 decisive sentence instead of the full card | All |
| | A6 | S11 request repetition | All |
| | A7 | S12 "ignore details" plus attribution framing | All |
| | A8 | S13 frozen contrastive exemplar | All |
| | A9 | S5 and S6: elimination, then the top two in both orders; needs doc 53's letter mode | All |
| 3: model reasoning | A10 | S3 bounded `why`, 40–160 characters (doc 53 R7, arm g) | All; Qwen3-4B-2507 if doc 49 keeps it |
| | A11 | `why`, then a one-pass letter read | All |
| | A12 | S4 code-written thought, closed | Qwen3.5-4B, Gemma 4 E4B |
| | A13 | S4 seeded thought, open, B = 64 | Qwen3.5-4B, Gemma 4 E4B |
| | A14 | S10 native budget, B = 64, split answer pass; `always` against `on_disagreement` | Qwen3.5-4B, Gemma 4 E4B; Granite 4.2-3B inside doc 53 S7 |
| | A15 | As A14 with B = 128. [15]'s curves peak at 32 and fall sharply by 128 for a 7B model, so a B = 32 arm is the stronger candidate if only one budget fits | As A14 |
| Fill | F0–F4 | Free plus quote check; quote-first; verbatim grammar; code candidates; cite-or-abstain with permuted enums. A12 as a do-no-harm check | All |

Granite 4.1 3B has no think channel. Its S4 counterpart is facts through its `documents` path (doc 55 H-R4).

### 6.3 Suites and metrics

- **Suites** (tuning split only): `pick-hard` 30 and `pick` 30, in both conditions; the tune half of the Pick pool (30); the
  six-item dispatch draft plus the pool's five tune sketches; `fill` 12 and the tune half of the Fill pool (18).
- **Dispatch gaps.** Sketches for the rule items PW04, HT01, HT02, HT04, PW05, PT04 and PT03 are still to be written, on the tuning
  split.
- **Metrics:**
  - pass^3; per-item flips against A0 (paired); planted-escape recall and false `X`; the wrong-but-valid rate;
  - per-facet accuracy for A1 and A2; hint-only accuracy (T-L6);
  - prompt, decode and thinking tokens; the rate at which the model closes its own thought within B; the truncation rate; p50 and
    p90 latency.

### 6.4 Pre-registered rules

Doc 55's PR1–PR9 govern adoption on held-out data. This doc adds [I]:

| Rule | Adopt only if… |
| --- | --- |
| SR1 Cheapest fix first | A model-reasoning arm (A10–A15) beats the best code-side arm for the same failure class (A2–A5) by at least 10 points pass^3 on that class's items, or matches it at a lower p50 |
| SR2 Escapes | No arm lowers planted-escape recall or raises false `X` against A0, in either condition (PR1; [21]) |
| SR3 Leakage | The scaffold passes T-L1–T-L9, and its hint-only accuracy is within 10 points of A0's under the same swap (T-L6) |
| SR4 Canaries | Thinking arms run only after C1–C4 pass for that template and build; a failure is recorded, not worked around |
| SR5 Latency | Triggered reasoning fits PR6 at its measured firing rate, or its added time is shown on the plan card; an always-on budget of 32 tokens or more needs a PR2 win |
| SR6 Checklist against dispatch | If A2 beats A1 by at least 10 points on rule-bearing items for all three models, checklist arms are dropped for those kinds [34] |
| SR7 The `why` | Doc 53 R7 decides per model, and the `why` is kept only on DecisionKinds where it wins |

**Power** [I]: a failure class has few items. With 8 rule-bearing tune items, 10 points of pass^3 is less than one item, and with
3 samples per cell a single flip moves an item's rate by 33 points. SR1 and SR6 are therefore read as paired item-level counts
(items flipped each way against the comparison arm), never as a bare percentage, and nothing passes on the tuning split alone.

### 6.5 Cost

[I, arithmetic from doc 46 p50s and stored decode rates]:

| Stage | Calls | Time |
| --- | --- | --- |
| Stage 1 screen | About 1,900: about 20 failure-bearing tune items × 3 samples × 2 conditions × 16 arms | About 60 minutes at a mean of about 1.8 s per call; thinking arms run 2.5–4 s |
| Stage 2 | About 2,700: survivors (about 4 arms plus A0) on 90 tune items × 3 × 2 | About 60–70 minutes |
| Fill | About 450 | About 10 minutes |
| Canaries | About 60 | — |
| **Total, thinking-capable 4B model** | **About 5,100** | **About 2–2.5 hours**, plus up to 30 minutes if budgets are exhausted and samples run one after another |
| Granite 4.1 3B, no thinking arms | — | About 1.2 hours |

The held-out look follows doc 55 §4.6.

### 6.6 Priors to falsify [I]

- A2 ≥ A1 on rule items [34, 35], and A2 moves HT03 for Qwen from 0 of 24.
- A10 ≈ A0 on HT03 for Qwen [3, 24]. This prior is weak: [3] and [24] measured frontier models, while the small-model results
  closest to a Pick ([15], [8]) found short reasoning helping. It may help near-fit escapes [75] or hurt them [21]; both directions
  are tested.
- A12 beats the user-turn card on HT03 for Qwen [89]. This is the least certain prior.
- A14 ≥ A15 (64 tokens at least as good as 128), and Qwen seldom closes its own thought within B [15, 16].
- A4 and A5 help Gemma's lure errors (HV01, HW03) most.
- A6 has a small effect, because the layout is question-first [60].
- Fill: F2 or F3 drives span errors toward 0 for Qwen and Granite, and F4 cuts over-inference.

## 7. Design-gap candidates (listed, not filed)

1. **Registered reasoning scaffolds per DecisionKind.** Facet schemas, decision tables, annotation generators and card-sentence
   selectors are authored and tested as code, with §5.3's tests. This extends doc 55 §7 item 2; doc 38 §3.3 allows `split` only for
   Compose and Draft.
2. **Code-written thought as a named capsule segment** (doc 38 §3.3, DG019). It is the last segment, holds only prompt-pack text and
   code-rendered facts, and needs a per-template probe (C4).
3. **The two-phase call shape.** The output cap becomes budget + close message + answer (doc 21 §8.2, doc 40 R8's table), and
   "same-model re-ask with thinking" becomes a cascade route. D023 decision 3 holds because no other model is involved.
4. **Reasoning records against doc 21 §8.2.** What the product stores and shows: the thought id and hash, the reasoning token count,
   and the `why` as an untrusted note, but never model thinking text (§5.4).
5. **The `why` in the glass box.** It is labelled as a model's note, never as the cause. Dispatched decisions show code's rule.
6. **The leading `why` becomes a knob, not doctrine** (doc 25 §2.4 and §4.3, doc 38 §3.3). This reinforces doc 53 R7 and doc 55
   §7 item 8, with this doc's per-class evidence.
7. **Scaffold leakage tests as part of the DecisionKind contract** (§5.3).
8. **A dev-time prompt-pack optimiser**, GEPA- or MIPRO-style: synthetic suites only, a maintainer rewrite of every proposed text,
   the held-out gate, and never at runtime. It is not fine-tuning (D027 item 6 stands).

## Findings for sibling docs (reported, not fixed)

1. **Doc 53 §5.3 item 7 and stage S7.** "The grammar starting after `</think>`" is what b11146's parsers do by code reading
   [98, 100], but [105] reported otherwise on an earlier build, so canary C2 comes first. S7's 512-token cap must use
   `reasoning_budget_tokens`, with n_predict of at least 512 plus the answer cap. With `max_tokens` alone it measures the coupling tax
   [16], not thinking.
2. **Docs 46 §2.6 and 55 §1.1, §2.2 and H-G1.** Part of Gemma's +9 tokens per pick is a mandatory ```` ```json ```` fence in Gemma
   4's response-format grammar at b11146 [99], not only pretty-printing. H-G1's compact `grammar` should test both (C6) [V at source;
   U until canary].
3. **Doc 25 §2.4** ("Adopt … a leading bounded `why`") and H5 rest on math and letter tasks at 8B and up. The evidence here makes it a
   per-(model, DecisionKind) knob.
4. **Doc 51 §3.4 M9** describes budget forcing through Mellea as Ollama-only. llama-server b11146 has native per-request budgets and
   a forced close [94, 96]; Ollama has only on and off [107].
5. **`tools/local-qual/run.py --why`** bounds `why` with `maxLength` 160 and no `minLength`. A bounded arm sets both. The change
   belongs in the scratch copy used for tuning, not in the tree while jobs run.

## Open questions

1. **Code-written thought (owner):** is text the editor writes into the model's thinking acceptable under the glass-box invariant,
   if it is labelled "written by the editor" and holds only code's facts? [I]
2. **Dispatch as doctrine (owner):** if dispatch wins for all first targets, do rule-bearing DecisionKinds drop the direct Pick
   (doc 55 OQ8)? [I]
3. **Training small helpers (owner; doc 58):** an error-locating classifier [83] or a reasoning-selection classifier [4] would need
   training, which revisits D027 item 6. It is deferred to doc 58's owner question. [I]
4. **Qwen3.5 and forced closes (technical):** does Qwen3.5 answer well from a forced-closed block, and has it inherited Qwen3's
   early-stop training? [U]
5. **Prefill in the think channel (technical):** do prefilled thought tokens count against the budget, and is a non-empty block
   with thinking off in distribution for Qwen3.5 and Gemma 4 (C4)? [U]
6. **Cloud (technical):** which endpoints support assistant-prefix continuation, and should cloud presets use code-side scaffolds
   only? [U]
7. **Sentence selection (technical):** can the decisive card sentence be selected answer-blind for every rule-bearing DecisionKind,
   or do some kinds need S5's first-pass distribution to find the leading pair? [I]
8. **Tiny tier (technical):** is any model-side reasoning arm worth testing below 2B [14, 30], or only code-side scaffolds? [I]

## Sources

Arxiv abstracts, repository files at tag b11146, issues, PRs and vendor pages were read on 2026-09-27 and 2026-09-28. Items marked
"to recheck" in §2.10 were read from HTML renderings.

### Model-written reasoning at small scale

- [1] Wei et al., Chain-of-Thought Prompting Elicits Reasoning in LLMs, <https://arxiv.org/abs/2201.11903>
- [2] Sprague et al., To CoT or not to CoT?, <https://arxiv.org/abs/2409.12183>
- [3] Liu et al., Mind Your Step (by Step), <https://arxiv.org/abs/2410.21333>
- [4] Li et al., When Thinking Fails: pitfalls of reasoning for instruction following, <https://arxiv.org/abs/2505.11423>
- [5] TextReasoningBench: Does Reasoning Really Improve Text Classification? (2026 preprint), <https://arxiv.org/abs/2603.19558>
- [6] Why Chain of Thought Fails in Clinical Text Understanding, <https://arxiv.org/abs/2509.21933>
- [7] Qwen3 Technical Report (thinking tables; thinking budget and early-stop sentence), <https://arxiv.org/abs/2505.09388>
- [8] Explicit Reasoning Makes Better Judges (NeurIPS 2025 workshop), <https://arxiv.org/abs/2509.13332>
- [9] Ma et al., Reasoning Models Can Be Effective Without Thinking, <https://arxiv.org/abs/2504.09858>
- [10] Does Thinking More Always Help?, <https://arxiv.org/abs/2506.04210>
- [11] Inverse Scaling in Test-Time Compute, <https://arxiv.org/abs/2507.14417>
- [12] When More is Less: Understanding Chain-of-Thought Length in LLMs, <https://arxiv.org/abs/2502.07266>
- [13] Xu et al., Chain of Draft, <https://arxiv.org/abs/2502.18600>
- [14] Li et al., Small Models Struggle to Learn from Strong Reasoners, <https://arxiv.org/abs/2502.12143>

### Thinking budgets, abstention and faithfulness

- [15] Qi, Brief Is Better: Non-Monotonic CoT Budget Effects in Function-Calling Agents (2026 preprint),
  <https://arxiv.org/abs/2604.02155>
- [16] Nie et al., The Coupling Tax: Shared Token Budgets Undermine Visible CoT, <https://arxiv.org/abs/2605.07686>
- [17] Aggarwal et al., OptimalThinkingBench, <https://arxiv.org/abs/2508.13141>
- [18] Mid-Think: Training-Free Intermediate-Budget Reasoning, <https://arxiv.org/abs/2601.07036>
- [19] ICLR Blogposts 2026, Wait, Do We Need to Wait? Revisiting Budget Forcing,
  <https://iclr-blogposts.github.io/2026/blog/2026/wait-do-we-need-to-wait/>
- [20] Muennighoff et al., s1: Simple test-time scaling, <https://arxiv.org/abs/2501.19393>
- [21] Kirichenko et al., AbstentionBench, <https://arxiv.org/abs/2506.09038>
- [22] Zhao, Hooi, Ng, Test-Time Scaling Is Not Effective for Knowledge-Intensive Tasks Yet, <https://arxiv.org/abs/2509.06861>
- [23] Chen et al., Reasoning Models Don't Always Say What They Think, <https://arxiv.org/abs/2505.05410>
- [24] Turpin et al., Language Models Don't Always Say What They Think, <https://arxiv.org/abs/2305.04388>
- [25] Lee et al., DART: Draft-Agreement Routing for Adaptive Thinking Budgets, <https://arxiv.org/abs/2606.23181>
- [26] Dong, Qin, Shah, When Does Learning to Stop Help? Early exits in reasoning models, <https://arxiv.org/abs/2606.30852>

### Rationale fields and format constraints

- [27] Tam et al., Let Me Speak Freely?, <https://arxiv.org/abs/2408.02442>
- [28] .txt (dottxt), Say What You Mean: A Response to "Let Me Speak Freely", <https://blog.dottxt.ai/say-what-you-mean.html>
- [29] Banerjee et al., CRANE: Reasoning with Constrained LLM Generation, <https://arxiv.org/abs/2502.09061>
- [30] Ray, The Constraint Tax (2026 preprint), <https://arxiv.org/abs/2605.26128>
- [31] Constrained Decoding Eliminates Structural Failures in Small LLMs but Reveals a Semantic Gap (2026 preprint),
  <https://arxiv.org/abs/2609.23742>
- [32] Fan, Capacity, Not Format, <https://arxiv.org/abs/2606.09410>
- [33] Geng et al., Grammar-Constrained Decoding for Structured NLP Tasks without Finetuning, <https://arxiv.org/abs/2305.13971>

### Harness-side and neurosymbolic reasoning, decomposition

- [34] Somov et al., Breaking the Chain: faithfulness to intermediate structures, <https://arxiv.org/abs/2603.16475>
- [35] Ramírez Ovalle, Alvarez, Resource-Aware Neuro-Symbolic Reasoning for Local SLMs, <https://arxiv.org/abs/2606.27281>
- [36] Gao et al., PAL: Program-aided Language Models, <https://arxiv.org/abs/2211.10435>
- [37] Chen et al., Program of Thoughts, <https://arxiv.org/abs/2211.12588>
- [38] Lyu et al., Faithful Chain-of-Thought Reasoning, <https://arxiv.org/abs/2301.13379>
- [39] Pan et al., Logic-LM, <https://arxiv.org/abs/2305.12295>
- [40] Olausson et al., LINC, <https://arxiv.org/abs/2310.15164>
- [41] Ye et al., SatLM, <https://arxiv.org/abs/2305.09656>
- [42] Creswell et al., Selection-Inference, <https://arxiv.org/abs/2205.09712>
- [43] RuleArena, <https://arxiv.org/abs/2412.08972>
- [44] Biswas et al., Code-Guided Reasoning for SLMs, <https://arxiv.org/abs/2605.18827>
- [45] Zhou et al., Least-to-Most Prompting, <https://arxiv.org/abs/2205.10625>
- [46] Wang et al., Plan-and-Solve Prompting, <https://arxiv.org/abs/2305.04091>
- [47] Fu et al., Hint-before-Solving Prompting, <https://arxiv.org/abs/2402.14310>
- [48] Divide-or-Conquer? Which Part Should You Distill Your LLM?, <https://arxiv.org/abs/2402.15000>
- [49] Zabolotnii, LLM StructCore, <https://arxiv.org/abs/2604.20560>
- [50] Abdullin, Schema-Guided Reasoning (practitioner write-up) [anecdote], <https://abdullin.com/schema-guided-reasoning/>
- [51] Alkiek et al., Instruction Retrieval at Inference Time, <https://arxiv.org/abs/2510.13935>
- [52] Wang et al., Towards Understanding Chain-of-Thought Prompting, <https://arxiv.org/abs/2212.10001>
- [53] Zhang et al., Auto-CoT, <https://arxiv.org/abs/2210.03493>

### Priors, context and input restructuring

- [54] McKenzie et al., Inverse Scaling: When Bigger Isn't Better, <https://arxiv.org/abs/2306.09479>
- [55] Zhou et al., Context-faithful Prompting, <https://arxiv.org/abs/2303.11315> (tables via <https://ar5iv.labs.arxiv.org/html/2303.11315>)
- [56] Shi et al., Trusting Your Evidence: Context-Aware Decoding, <https://arxiv.org/abs/2305.14739>
- [57] Wu et al., Reasoning or Reciting?, <https://arxiv.org/abs/2307.02477>
- [58] Shi et al., LLMs Can Be Easily Distracted by Irrelevant Context (GSM-IC), <https://arxiv.org/abs/2302.00093>
- [59] Weston, Sukhbaatar, System 2 Attention, <https://arxiv.org/abs/2311.11829>
- [60] Leviathan, Kalman, Matias, Prompt Repetition Improves Non-Reasoning LLMs, <https://arxiv.org/abs/2512.14982>
- [61] Xu et al., Re-Reading Improves Reasoning in LLMs, <https://arxiv.org/abs/2309.06275>
- [62] McCoy, Pavlick, Linzen, Right for the Wrong Reasons, <https://arxiv.org/abs/1902.01007>
- [63] Truong et al., Language models are not naysayers, <https://arxiv.org/abs/2306.08189>

### Multiple-choice selection

- [64] Ma, Du, POE: Process of Elimination for Multiple Choice Reasoning, <https://arxiv.org/abs/2310.15575>
- [65] Balepur et al., It's Not Easy Being Wrong, <https://arxiv.org/abs/2311.07532>
- [66] Qin et al., Pairwise Ranking Prompting, <https://arxiv.org/abs/2306.17563>
- [67] PairJudge RM: Best-of-N with a Knockout Tournament, <https://arxiv.org/abs/2501.13007>
- [68] Pezeshkpour, Hruschka, Sensitivity to the Order of Options in MCQ, <https://arxiv.org/abs/2308.11483>
- [69] Zheng et al., LLMs Are Not Robust Multiple Choice Selectors (PriDe), <https://arxiv.org/abs/2309.03882>
- [70] Tang et al., Found in the Middle: Permutation Self-Consistency, <https://arxiv.org/abs/2310.07712>
- [71] Accuracy and Order Sensitivity Diverge Under Label-Free Strategies (2026 preprint), <https://arxiv.org/abs/2608.11947>
- [72] Wang et al., Look at the Text, <https://arxiv.org/abs/2404.08382>
- [73] Mitigating Selection Bias with Node Pruning and Auxiliary Options, <https://arxiv.org/abs/2409.18857>
- [74] None of the Above, Less of the Right, <https://arxiv.org/abs/2503.01550>
- [75] Wait, that's not an option: LLMs Robustness with Incorrect Multiple-Choice Options, <https://arxiv.org/abs/2409.00113>

### Sampling, verification and self-critique

- [76] Wang et al., Self-Consistency, <https://arxiv.org/abs/2203.11171>
- [77] Aggarwal et al., Adaptive-Consistency, <https://arxiv.org/abs/2305.11860>
- [78] Wang et al., Soft Self-Consistency, <https://arxiv.org/abs/2402.13212>
- [79] Chen et al., Are More LLM Calls All You Need?, <https://arxiv.org/abs/2403.02419>
- [80] Brown et al., Large Language Monkeys, <https://arxiv.org/abs/2407.21787>
- [81] Liu et al., Can 1B LLM Surpass 405B LLM?, <https://arxiv.org/abs/2502.06703>
- [82] Huang et al., LLMs Cannot Self-Correct Reasoning Yet, <https://arxiv.org/abs/2310.01798>
- [83] Tyen et al., LLMs cannot find reasoning errors, but can correct them given the location, <https://arxiv.org/abs/2311.08516>
- [84] Zhang et al., Small Language Models Need Strong Verifiers to Self-Correct, <https://arxiv.org/abs/2404.17140>
- [85] Kamoi et al., When Can LLMs Actually Correct Their Own Mistakes?, <https://arxiv.org/abs/2406.01297>
- [86] Dhuliawala et al., Chain-of-Verification, <https://arxiv.org/abs/2309.11495>
- [87] Chia et al., Contrastive Chain-of-Thought Prompting, <https://arxiv.org/abs/2311.09277>
- [88] O'Brien, Lewis, Contrastive Decoding Improves Reasoning, <https://arxiv.org/abs/2309.09117>

### Injected thought and thinking tokens

- [89] Wu et al., Thinking Intervention, <https://arxiv.org/abs/2503.24370>
- [90] Liu et al., Thought Manipulation, <https://arxiv.org/abs/2504.13626>
- [91] Speculative Thinking, <https://arxiv.org/abs/2504.12329>
- [92] Goyal et al., Think before you speak: pause tokens, <https://arxiv.org/abs/2310.02226>
- [93] Pfau, Merrill, Bowman, Let's Think Dot by Dot, <https://arxiv.org/abs/2404.15758>

### Runtimes, engines and model cards

- [94] llama.cpp `tools/server/README.md` at b11146, <https://github.com/ggml-org/llama.cpp/blob/b11146/tools/server/README.md>
- [95] llama.cpp `tools/server/server-common.cpp` at b11146,
  <https://github.com/ggml-org/llama.cpp/blob/b11146/tools/server/server-common.cpp>
- [96] llama.cpp `common/reasoning-budget.cpp` at b11146,
  <https://github.com/ggml-org/llama.cpp/blob/b11146/common/reasoning-budget.cpp>
- [97] llama.cpp `common/sampling.cpp` at b11146, <https://github.com/ggml-org/llama.cpp/blob/b11146/common/sampling.cpp>
- [98] llama.cpp `common/parsers/qwen3-coder.cpp` at b11146,
  <https://github.com/ggml-org/llama.cpp/blob/b11146/common/parsers/qwen3-coder.cpp>
- [99] llama.cpp `common/parsers/gemma4.cpp` at b11146, <https://github.com/ggml-org/llama.cpp/blob/b11146/common/parsers/gemma4.cpp>
- [100] llama.cpp `common/chat-auto-parser-generator.cpp` at b11146,
  <https://github.com/ggml-org/llama.cpp/blob/b11146/common/chat-auto-parser-generator.cpp>
- [101] llama.cpp `common/chat.cpp` at b11146, <https://github.com/ggml-org/llama.cpp/blob/b11146/common/chat.cpp>
- [102] llama.cpp PR #21697, reasoning budget for Gemma 4, <https://github.com/ggml-org/llama.cpp/pull/21697>
- [103] llama.cpp PR #25961 (draft), intro and soft budget messages, <https://github.com/ggml-org/llama.cpp/pull/25961>
- [104] llama.cpp issue #20632, graceful reasoning-budget termination, <https://github.com/ggml-org/llama.cpp/issues/20632>
- [105] llama.cpp issue #20345, grammar not applied with thinking enabled, <https://github.com/ggml-org/llama.cpp/issues/20345>
- [106] LM Studio bug tracker #1773, schema applied to the reasoning stream,
  <https://github.com/lmstudio-ai/lmstudio-bug-tracker/issues/1773>
- [107] Ollama PR #17566, thinking token budget, <https://github.com/ollama/ollama/pull/17566>
- [108] vLLM docs, reasoning outputs, <https://docs.vllm.ai/en/latest/features/reasoning_outputs.html>
- [109] vLLM docs, structured outputs, <https://docs.vllm.ai/en/latest/features/structured_outputs.html>
- [110] Hugging Face transformers docs, chat templating (`continue_final_message`),
  <https://huggingface.co/docs/transformers/main/en/chat_templating>
- [111] Qwen3.5-4B model card, <https://huggingface.co/Qwen/Qwen3.5-4B>
- [112] Qwen3-4B model card (no greedy decoding in thinking mode), <https://huggingface.co/Qwen/Qwen3-4B>
- [113] Gemma 4 E4B model card, <https://huggingface.co/google/gemma-4-E4B-it>
- [114] Granite 4.2 3B model card, <https://huggingface.co/ibm-granite/granite-4.2-3b>
- [115] Qwen thinking-budget guide,
  <https://github.com/QwenLM/Qwen3/blob/main/docs/source/getting_started/thinking_budget.md>; Alibaba Model Studio, deep thinking,
  <https://www.alibabacloud.com/help/en/model-studio/deep-thinking>
- [116] OpenRouter, reasoning tokens, <https://openrouter.ai/docs/use-cases/reasoning-tokens>
- [117] DeepSeek, Chat Prefix Completion (beta), <https://api-docs.deepseek.com/guides/chat_prefix_completion/>; Mistral, prefix
  guide, <https://docs.mistral.ai/guides/prefix>

### Frameworks whose ideas are re-implemented or rejected

- [118] Khattab et al., DSPy, <https://arxiv.org/abs/2310.03714>; ChainOfThought source,
  <https://raw.githubusercontent.com/stanfordnlp/dspy/main/dspy/predict/chain_of_thought.py>
- [119] Agrawal et al., GEPA, <https://arxiv.org/abs/2507.19457>
- [120] Tan et al., LangProBe, <https://arxiv.org/abs/2502.20315>
- [121] guidance, <https://github.com/guidance-ai/guidance>; llguidance, <https://github.com/guidance-ai/llguidance>
- [122] SGLang, choices methods, <https://docs.sglang.io/docs/references/frontend/choices_methods>
- [123] BoundaryML, Schema-Aligned Parsing [V-vendor], <https://boundaryml.com/blog/schema-aligned-parsing>

**Repository docs.**

- `AGENTS.md`.
- `docs/research/21-agent-doctrine.md` §3.2, §4.1, §8.2, §9.
- `25-weak-model-friendly-campaign-harness.md` §2.4, §4.3, §7.2, §9.1, H5.
- `38-harness-workflows.md` §3.3.
- `40-token-economy.md` R2–R4, R8.
- `44-local-model-qualification-spike.md`; `46-llamacpp-huggingface-and-ud-quant-spike.md` §2.6.
- `51-model-native-harnesses.md` §2.6.2, §3.4 M9.
- `53-how-small-can-we-go.md` T1, T10, §4.2–§4.3, §5.3–§5.5 (R7, R8, S7).
- `55-per-model-harness-presets.md` §1.1–§1.4, §2, §3.3, §4, §6, §7.
- Decisions D023 (decision 3), D027 (item 6) and D048.
- `tools/local-qual/run.py` (`build_pick`, `--why`, `--think-mode`, `NUM_PREDICT`), and `suites/pick.json`, `pick-hard.json`,
  `fill.json`.

**Our records, re-analysed offline.** The stored call records of docs 44 and 46, plus preliminary doc 49 rows (git-ignored). They
were re-scored without new model calls:

- the per-miss failure typing and order-conditional flag;
- majority and unanimity per menu;
- Fill field errors by kind;
- decode and prefill rates from `timings`.

The staged tuning-split material, outside the tree: the six-item dispatch draft, and the tune halves and metadata of the expanded Pick
and Fill pools.

## Verification notes

### 2026-09-28, author checks at write-up

- **Re-derived from stored records** (no model calls):
  - every count in §3 and the TL;DR;
  - the item tallies for HT03, HK01 and HM04, which match doc 55 §1.1's pooled figures (HT03 0 of 24; HK01 7 of 24 right for Qwen and
    24 of 24 for Gemma; HM04 12 of 24 for Qwen and 22 of 24 for Gemma);
  - unanimity per menu; the decode and prefill rates behind §4.1's costs.
- **Tallied from the pool metadata:** the tune-pool trait counts in §3.6. Only the tune half was read; the held-out half's hash is
  recorded in the split file.
- **Re-read at the source for this write-up:**
  - the abstracts of [15], [16], [21], [25], [30], [34], [35] and [60];
  - issue #20345's page [105]. It showed no closure, while an earlier read in this research reported it closed with no linked fix, so
    its status is [U].
- **Read at the source during the research for this doc:** the llama.cpp b11146 files [94]–[101], the PRs and issues [102]–[107], and
  the model cards [111]–[115].
- **To recheck verbatim before citing further:** see §2.10 item 3. The per-budget rows of [15] beyond Qwen2.5-1.5B come from the paper
  body, not the abstract.
- **Not verified:**
  - any arm, and any latency or call count in §4 and §6 (arithmetic from doc 46 p50s and stored rates);
  - whether b11146 enforces the schema after thinking in practice (canary C2);
  - whether a code-written thought is accepted with thinking off (C4);
  - Qwen3.5's behaviour after a forced close.
- **Limits:**
  - arms of one family are near-copies; n is small; misses were typed by hand with a fixed precedence;
  - the word-overlap test is crude and cannot see meaning echoes such as HK01;
  - the doc 49 rows may change.
- **Folding steps, not done here:** a row for this doc in `docs/README.md`; the knob additions (§4.4) in doc 55's catalogue once
  arms are measured; D048's open parts.

### 2026-09-28, independent review

Scope: literature numbers against their sources, the honesty of the small-model caveats, the leakage safeguards, the line between
measured and proposed, and public hygiene. No model was run. Papers were re-read at their arXiv abstract pages and, for tables,
through the arXiv HTML renderings via a page-summarising fetch tool. Where that tool's output was internally inconsistent or could
not place a figure, the figure stays "to recheck".

- **Confirmed at the source:**
  - [2] 56.8 against 56.1 and the 95% "=" share; [4] Qwen2.5-7B IFEval 63.6 / 57.7 / 68.8 / 59.7; [7] every Qwen3-4B thinking
    and non-thinking figure in §2.2, and the fixed early-stop sentence; [13] the Chain of Draft table; [15] every budget cell for all three models, and Phi-3-mini's 68% early
    stops; [16] 87.5 against 18.0 at 256 (98.6% truncated) and 93.1 against 56.9 at 512; [21] "by 24% on average";
  - [27] 75.13, 64.67, 48.90, 70.1 → 28.0, 44.1 → 55.5, and GPT-3.5's answer-first order in 100% of JSON replies; [28] 0.78 / 0.77,
    0.77 / 0.73, 0.44 / 0.41 with a 30–250-character reasoning regex placed first; [29] 26 / 22 / 31; [30] every figure in §2.3;
  - [34] the 18–23-point gap, the below-0.03 tool result and Gemma-2 2B's 0.26; [35] every Qwen3-4B-2507, Gemma-3n-E4B and
    Phi-4-mini figure; [8], [9], [10], [14], [23], [25], [44], [51], [58], [59], [60] (47 of 70, 0 losses, larger with options
    first, padding control null), [61] 70B, [68], [74], [83], [87] 69.2 → 79.0, [88] +3.6 / −2.7, [89] (as reworded), [90], [91],
    [119];
  - llama.cpp b11146: `reasoning_budget_tokens` with its `thinking_budget_tokens` alias, −1 falling back to the server default,
    the budget applied only when the template declares end tags, and `continue_final_message` accepting `true`,
    `"reasoning_content"` and `"content"` (server-common.cpp and chat.cpp at the tag).
- **Corrected in place:**
  - [5]: the sign (the range is CoT minus direct), the subjective-task gains of CoT for Gemma-3-4B and Qwen3-8B, and the TL;DR
    caveat that CoT is not uniformly negative at 4–8B; the per-cell tally is now read, so it left the recheck list;
  - [6]: the named error types are hallucination, omission and incompleteness (not "units");
  - [3] and [24]: marked as frontier-model evidence; [13]: the direct baselines (7.2 and 3.9) added;
  - [17]: about 750 thinking tokens (not 753) for +2.2 to +4.7 by answer type;
  - [18]: the three figures are post-training rows (No-Think-trained, Mid-Think-trained, untrained with thinking), not a
    training-free budget sweep;
  - [27]: 64.67 is JSON requested in the prompt and 48.90 adds a schema in the prompt (not "JSON mode" and "format instructions");
  - [31]: the 1B figure is receipt extraction, and the paper's point is a residual semantic gap;
  - [34]: the gap holds on three of four datasets, and the tool arm ran on eight models (1.7B–32B, without Qwen3-4B);
  - [41]: a hard subset of GSM, not GSM-hard; [44]: an audit, not a controlled study;
  - [64]: +12 on conceptual combinations too, and inconsistent on commonsense and social tasks ("under 3 points elsewhere" was
    wrong); [65]: the LLaMA-2-7B range could not be confirmed, so only the direction is kept;
  - [71]: 5 of 6 models on each benchmark; [73]: the "I don't know" option lifted Llama-3-8B-Instruct by 2.0–8.4 (not 0.7–1.4), and
    it is never a correct answer there, so it is not escape evidence; [75]: the warning's effect was mixed, the 85% wording is
    quoted, and Llama 3.1 8B's row is flagged; [82]: 38.1 is after one round;
  - [84]: the per-cell ranges could not be confirmed, so only the direction is kept; [89]: the 6.7% was R1-Qwen-32B's, the
    attention finding reworded, and "thinking on, 7B and up" stated;
  - §3.3: without cards, Qwen3.5-4B Q4_K_M had 2 unanimous-wrong menus (HT03 and HK01) and 7 split, not 1 and 8; §4.2 S10's limit
    follows. Re-derived from the stored records: 30 menus, 3 samples each;
  - §3.6: the tune-pool traits were re-tallied from the pool revision rebuilt minutes after the draft (tune half only);
  - §1.1 and §2.9: "never run" became "not used in the records re-counted here" (next bullet).
- **Re-derived from stored records by the reviewer:** 1,440 / 1,440 / 180 Pick calls and 162 / 90 / 18 misses; 118 / 62 / 14
  misses in majority-wrong cells and 48 / 36 / 9 unanimous on one wrong option; HT03, HK01, HM04 and PW04 item tallies; 0 thinking
  characters, 0 parse failures and 0 `why` records in the re-counted set; the tune pool's 30 items and the Fill pool's 18 tune items.
- **Records written after this draft.** A separate ranking run has since written git-ignored records for Qwen3.5-4B (a `why` arm,
  a 256-token thinking arm, two temperatures, a drift re-run) and a partial Gemma 4 E4B `why` arm on `pick-hard`. This doc uses none
  of them, and they are not held-out evidence. A read-only look shows HT03 answered correctly in some `why` and thinking calls, where
  the stored plain arm of the same build had none, at 3 samples per cell. That is not a measurement at this n, but it is why the §6.6
  prior "A10 ≈ A0 on HT03" is now marked weak. Their write-up belongs to that run's own doc.
- **Leakage safeguards, tightened:** T-L6 and SR3 now compare against A0 under the same request swap, not against nominal chance
  (a blank request invites `X`, and letter priors lift A0 above 1/(n + 1)), and report escape items apart; §5.1 gains the
  author-exposure caveat and a held-out near-duplicate check for S13 exemplars; T-L10 is marked as a consistency check; §6.4 gains a
  power note, because one flip on 8 rule items outweighs a 10-point threshold. The TL;DR no longer says the hint-only test "proves"
  anything.
- **Measured against proposed:** every scaffold, arm, budget, cost and rule stays [I]; the only [V] counts are offline re-counts of
  stored records and pool metadata. §6.2 now notes that [15]'s curve favours a 32-token arm.
- **Hygiene:** no local paths, user names, private project names or island names; `ofp-editor` is the repository name used by the
  sibling docs; engine terms are used nominatively; model answers appear only as option keys from our own synthetic suites. The ten
  source-group labels became headings, and `<letter>` sits in code, for the Markdown linter.
- **Still to recheck:** §2.10 item 3's list; [2]'s exact 14-model roster; [47]'s 7B finding; the llama.cpp files [96]–[100] (only
  [95] and [101] were re-read here); the model cards [111]–[115]; the cloud pages [116]–[117]. The older citations not named above
  ([1], [11], [12], [20], [22], [36]–[40], [42], [43], [45], [46], [48], [50], [52]–[54], [56], [57], [62], [63], [66], [67],
  [69], [70], [72], [76]–[81], [85], [86], [92], [93]) were not re-read in this review; [19] and [49] were, and match, and [41]
  was corrected above.
