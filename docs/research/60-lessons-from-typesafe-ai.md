# Lessons from TypeSafe AI's design for Plotroom's harness

Research doc 60 for Plotroom (`ofp-editor`). Research date: 2026-09-28. Audience: contributors and LLM coding agents. This file is
meant to be read on its own.
Question answered (owner, 2026-09-28): "Anything we can learn from TypeSafe AI's design, to further improve our harness?"

**Status: proposal. Nothing was run, measured or coded for this doc, and no TypeSafe API call was made.** Every design proposal is
[I]. Numbers about Jev come from TypeSafe's own pages or from third parties, never from Plotroom measurements.
**Epistemic legend** (doc 16's): **[V]** read on the cited public page on 2026-09-28; for a TypeSafe page this is the vendor's own
statement about its own product. **[V-author]** a number published by a vendor or third-party author, quoted as published and not
reproduced by anyone we know of or by us. **[V per doc N]** taken from a sibling doc. **[I]** our inference or proposal. **[U]**
unknown, needs measurement.
**Relation to sibling docs.** Doc 16 introduced decision models (Jev, Kev, Laya, CLM), the `Selector` seam and the evidence bar; doc
11 (§3.4, §7.1 item 10) and doc 12 §1.9 cover pi-ai's `classify()` slot and rig's `rig-typesafeai` client. This doc does not repeat them. It asks
a different question: which of TypeSafe's *design* ideas, rather than its model, should shape Plotroom's own harness. Doc 21 sets the
doctrine, docs 25 and 38 the step shapes and workflows, doc 40 the token economy, doc 53 (draft) one-pass letter scoring and cascades,
doc 55 (draft) the per-model harness presets that D048 accepted, doc 56 (proposal) the implementation patterns, doc 59 (draft,
experiments pending) the synthetic reasoning scaffolds; its S3 (structured rationale) and S7 (targeted sub-questions with code
aggregation) are the scaffolds this doc's arms meet. Doc 58 (draft, proposals only) covers purpose-specific ML components; this doc
does not repeat it. §3 names the arms this doc hands them. D023 (decision 5: no decision model in front of the generative model in v1), D047 and D048
govern. This doc changes no decision.
**Names.** *Jev* is TypeSafe's hosted decision model; *Choice*, *Score* and *Noul* are its question types (one of N options; a level
on an ordered scale; a yes/no probability). *Harness preset* keeps doc 55's meaning. *Existence gate* (this doc's term) is a separate
yes/no question asking whether the state answers the question at all. *DecisionKind* keeps doc 38's meaning.
**Hygiene.** Public sources only; no game content; no local paths; no API keys.

## TL;DR

- **Borrow the design, not the model.** TypeSafe's core is "keep code in control and give the model narrow, structured decisions",
  with answer types that map onto `match`, `if` and sorting [V]. That is Plotroom's doctrine already (docs 16, 21, 25). Independent
  tests show a plain generative model read by label-token probabilities comes close to Jev (Gemma 4 26B: 75.3% against 77.3% overall,
  level on yes/no) [V-author]. So D023 decision 5 stands and doc 53's one-pass scoring gets outside support [I].
- **The question text is the program.** Wrong option descriptions pushed Jev below chance (16.7% against a 25% floor), and renaming
  options from 0/1 to no/yes "changes 70.4 more answers per hundred" with the rubric unchanged [V-author]. Proposal: a question and
  menu style guide with a load-time lint, and the wording hash in every run record and qualification key (§2.2, §2.3).
- **"None fit" inside a softmax is not enough.** Without an explicit escape, Jev flagged 0 of 30 out-of-scope messages, at 0.99
  confidence [V-author]. The vendor's own fix is a separate yes/no asking whether the document answers at all [V]. Proposal: keep `X`
  and `Q`, and add an independent **existence gate** outside the menu's distribution for lookups, routing and near-fit menus (§2.4).
- **Many questions per item, never many items per state.** Questions scored independently over one shared state were 12.2× cheaper
  [V-author, vendor cookbook]; packing 40 rows into one state raised ranking inversions 4.5-fold, 0.038 to 0.171 [V-author]. Proposal: a state-first
  layout with one tail per question on llama-server's prefix cache, an independence test, and a "one item per state" rule (§2.5).
- **Probabilities belong to a question form, a menu and a wording.** Calibration direction flips by question type and domain, and
  one temperature per subset, fitted on 50 labels, largely fixed it for a plain Gemma [V-author]. Proposal: key doc 53's temperatures and thresholds by (harness preset, DecisionKind, question form,
  wording hash, menu size, language), floor probabilities at ε, and report held-out ECE against a noise floor (§2.6).
- **Combine by the weakest link; back off when unsure.** A multi-part answer is as good as its least certain part [V]. Proposal: a
  Fill record's routing confidence is its minimum field confidence, and a facet chain stops at the last confident facet (§2.7).
- **Thresholds are policy.** "A confidence threshold is not one number" [V]. Proposal: split doc 55's thresholds into per-preset
  routing values and product-owned **stakes floors** per DecisionKind that no preset can lower; confidence still never admits (§2.8).
- **Code proposes, the model selects, code copies**, plus a "stated?" gate per optional field and date parts picked, never computed
  by the model [V]. These are direct vendor precedents for doc 53 §4.4, doc 55 H-Q3/H-R3 and the `size` failures (§2.9, §2.10).
- **Explain by decomposition; publish rough edges.** Jev returns no rationale; transparency comes from atomic sub-answers combined by
  visible code [V]. Each version ships a list of known weaknesses with mitigations [V]. Proposal: a "why" built from recorded
  sub-answers, and a "known rough edges" list per harness preset, derived from our failures (§2.11, §2.12).
- **Twenty proposals, eleven design-gap candidates** (§3, §4). An optional shadow run of hosted Jev through the `Selector` seam is
  listed, but it needs its own paid key, a data-egress decision and a reading of TypeSafe's usage policy under D047: owner decisions
  that this doc does not assume.

## 1. What TypeSafe AI's design is

### 1.1 The product in one paragraph

TypeSafe AI sells "System One" models: models that take a text *state* plus typed *questions* and return a probability for every
allowed answer, and never write text. Jev (`jev-1.13.0`; aliases `jev-latest` and `jev-preview`) is the one public model. It is a
hosted API only; "The same weights serve every account", with no fine-tuning [V: models page]. The design advice throughout the docs
is: "Design AI-powered software by keeping code in control and giving System One narrow, structured decisions" [V: how-to-build].

### 1.2 Request, answer and limits

| Aspect | TypeSafe's design | Source |
| --- | --- | --- |
| Endpoint | `POST /v1/systemone` with `{state, model, questions}`; `state` is a string, a JSON object (recommended) or an array; text only | [V: api, models] |
| Question ids | Chosen by the caller; "Question IDs are for your code. They are not sent to the model" (the API page: "The key is not sent to the underlying model and is not used in inference") | [V: primitives, api] |
| Choice | Up to 255 options; each option is a label plus an optional description or a structured object; the vendor's examples use `what`, `not_for` and `examples`, but the field names are the caller's (the SDK types criteria as free-form) | [V: choice, advanced, SDK reference] |
| Score | 2–10 ordered levels, each described by a string or an object (the examples use `what` / `examples`, or `summary` / `signals`); "Every level is evaluated separately" | [V: score, advanced] |
| Noul | Optional `criteria.true` / `criteria.false`; answer is one probability | [V: noul] |
| Answers | Choice: `choice`, `probabilities` (sum 1), `confidence`. Score: `score` (the expected level), `probabilities`, `legend`, `confidence`. Noul: one probability, no confidence field | [V: primitives, api] |
| Independence | Every question "is evaluated independently", and all of a request's questions are evaluated "in parallel"; each is "scored on its own against the document" | [V: primitives; parallel-questions cookbook] |
| Limits | "64k tokens per request; 32k tokens for `state` plus the longest question"; English best, other languages need testing | [V: models] |
| Identity | The response names the resolved version; "An alias moves when a new release ships" | [V: models, api] |
| Price | $0.042 per million input tokens; "Output tokens are free"; rate limits listed with dynamic adjustment | [V: models] |
| Errors | 401, 422, 429, 529; SDK retries 408, 429 and 5xx with capped jittered backoff, exposes a request id and a `field_path` on response-validation errors | [V: api, SDK reference] |

The primitives are meant to map onto code. The CEO in an interview (transcript, fillers cut): "choice maps into … a switch statement
on an enum. Noulli's mapped to if statements. And scores map to sorting or thresholding" [V: Latent Space interview]. Confidence is a derived concentration statistic,
and "you are never locked into our definition" because the full distribution is returned [V: confidence].

### 1.3 Ecosystem

Python and JavaScript SDKs with typed answers (the JavaScript `ResultFor<T>` maps each question type to its answer type, and a
Choice answer is typed as the literal union of its option keys) [V: SDK reference]; a coding-agent skill [V]; an MIT
`system-one-adapter-python` that serves the same interface from OpenAI-compatible, Anthropic or Gemini backends [V: GitHub org];
integrations in pi-ai (doc 11), rig (`rig-typesafeai`, a 0.0.0 placeholder on crates.io; doc 12 §1.9), Pydantic AI, LiteLLM, OpenRouter and Cloudflare
Workers AI [V]. Eighteen cookbooks show end-to-end recipes (function calling, date extraction, semantic find, skill suggestion,
hierarchical classification, guardrails, cascades) [V: cookbooks].

### 1.4 How much to trust each kind of source

| Source | What it gives | Weight [I] |
| --- | --- | --- |
| TypeSafe docs and cookbooks | Design rules and recipes; many cookbooks use a handful to a few dozen items (4 hierarchies, 60 filings, 15 guardrail messages; a few use hundreds), and thresholds are offered as starting points (the Noul consistency cookbook: "The band is illustrative") | Good for design ideas, weak as evidence |
| Vendor workflow evals | Headline gains; no case counts, run counts or variance published (per an independent review) | Marketing-grade [V-author] |
| Pre-registered third-party studies (PriorBench, the Gemma-vs-Jev comparison, the option-name paper) | Measured failure modes | The strongest evidence here, still small or synthetic |
| Single-author GitHub benchmarks and reviews | Specific effects (batching, calibration, bias) | Directional; not reproduced |

No number in this doc comes from Plotroom measurements, and no study measured editor tasks.

## 2. Design principles and what Plotroom takes from each

Each subsection gives what TypeSafe does, why it works, what Plotroom already does, what to adopt or adapt, and what to reject.

### 2.1 Code owns the workflow; answer types are programming constructs

- **What they do** [V]: three primitives, each mapped to a control-flow construct; questions are atomic ("Ask two Nouls and combine
  them in code"); every fact, sum and date is computed in code; "Avoid … asking the model something code can compute exactly".
- **Why it works** [I on V]: a narrow judgement has one right reading; code owns everything that can be checked, so the model's
  errors stay judgement errors that a margin or a question card can catch.
- **Plotroom today** [V per docs]: the who-decides ladder (doc 16 §3.1, doc 21 §2), "code owns facts, structure and limits" (doc 25
  §3 principle 2), and `PickAnswer { Option, NoneFit, AskMe }` (agent-runtime §6). Plotroom has one choice answer type, the Pick's
  `PickAnswer`; yes/no checks and ordinal bands would today be ordinary Picks or Fill fields [I].
- **Adopt** [I]: make yes/no and ordinal first-class *forms* of the PICK step kind, each with its own answer type and calibration key
  (P-03, P-10). No new step kind: doc 38's closed set of twelve stays.
- **Reject** [I]: nothing; this is the doctrine TypeSafe and Plotroom share.

### 2.2 The question text is the program

- **What they do** [V]: "jev-1.13 answers the question you wrote, not the one you meant" (jaggedness page). The coding-agent skill says
  "Agents aren't great at writing questions, so expect to edit collaboratively with them", "Put the constants (questions and
  thresholds) in a single place so they're easy to review", and "The most important thing for humans to review is the questions and
  any threshold constants used in your TypeSafe code".
- **Why it works** [V-author; I]: measured wording effects are large. PriorBench: wrong criteria descriptions gave 16.7%, below the
  25% chance floor, while missing descriptions cost 0.8 points. Asking "are these lines part of the same paragraph?" (a topic) failed
  where "does this line pick up mid-sentence?" (the text itself) worked; the cookbook's rule is "the question should name the narrowest
  fact that decides it" (autoformat cookbook) [V]. A tool gate that asked whether data "cannot be recovered from version control"
  scored `rm -rf src && git push --force origin main` only 0.77, while asking whether the action is destructive scored it 0.99 against
  0.03–0.22 for ordinary requested edits (pi-jev) [V-author]. Pydantic AI: "Asked whether it *can* answer, rather than what the text
  calls for, Jev hands off nearly everything" [V].
- **Plotroom today** [V per docs]: doc 16 §1.3 already says "Question wording becomes part of the tested artifact"; doc 55 §1.4 puts
  wording in a versioned prompt pack addressed by ids, never in presets; DG012 lists the prompt pack among re-qualification triggers;
  doc 56 PK2 checks names in model-facing text against the registry.
- **Adopt** [I]:
  - A **question and menu style guide** (P-01): ask about observable content, never about topic, consequence or the model's own
    ability; one condition per yes/no; no clause that invites a chain of inference ("because it is in git"); state boundary cases in
    the option description; high probability means "flag this" (§2.3); describe ordinal levels as situations, not degrees (§2.10).
  - A **load-time lint** over the prompt pack that enforces the mechanical parts (P-01).
  - The **wording hash** (question text, option descriptions, criteria, exemplars) in the run record, the calibration key and the
    qualification key, so a one-word edit voids calibration exactly as a model-file change does (P-02).
  - Wording variants enter doc 55 §3's tuning split as candidates with a written hypothesis each; a stronger model may *propose*
    variants offline, frozen before any held-out run (the vendor's autoresearch cookbook keeps a change "only if the dev error goes
    down" and scores the test set once [V]).
- **Reject** [I]: runtime question writing by Wilco, and any model-proposed wording that ships without human review.

### 2.3 Option names carry meaning: neutral labels and one polarity

- **What they do** [V]: option names are sent to the model ("write descriptions that separate the options from each other"); per-option
  `what` / `not_for` / `examples` "sharpens the boundary between options"; "Phrase the question so that a high value means yes".
- **Why it matters** [V-author]: Sun et al. (arXiv 2609.26758, 2026-09-22) kept each rubric and swapped which name was bound to it:
  "renaming the two options from 0/1 to no/yes changes 70.4 more answers per hundred (95% CI: [67.6, 73.1])", the hosted model
  produced "24x as many answer flips as its test-retest floor", and random-string names "returns all model families to the
  neutral-control regime without reducing accuracy" while "the type-error rate remains 0%". The authors conclude the failure "depends on
  the semantic polarity of the option names". They tested Jev and two Jev-like models (Laya and an open DeBERTa-based model), not
  generative LLMs. The paper's body (read through a summarising fetcher) reports that on Laya's 3–16-option tasks "Even neutral letters
  change 52.4% of the decisions and lower accuracy from 56.4% to 27.8%", so how a model binds labels must be measured per model.
- **Plotroom today** [V per docs]: neutral letters mapped to ids by code, one-line option descriptions from facts only (doc 25 §6.2);
  doc 53 T2 and rule R5 plan to compare letters with option text per model (not built or run yet).
- **Adopt** [I]:
  - Never render a semantic answer label (yes/no, true/false, an option's name) as the token the model emits; never let mission
    text supply an option name.
  - Fix one polarity for every yes/no form: a high probability means "the thing to flag or act on".
  - A **name-reassignment flip rate** and a **polarity-swap replica** in qualification (P-11): cheap with one-pass scoring.
  - An authored `not_for` contrast line for known confusable pairs (TR UNLOAD vs UNLOAD, Countdown vs Timeout, PerCampaign vs
    PerTurn as in HV01, near-fit escapes such as HM04), rendered on or off per (model, DecisionKind) as a doc 55 option-rendering
    knob, because doc 55 §1.1 shows card effects change sign by model. The contrast text is reviewed data in the prompt pack, never
    preset prose.
- **Reject** [I]: TypeSafe's semantic option labels as the answer token.

### 2.4 Abstain, unknown and none-fit are different answers

- **What they do** [V]: "Add an `other` or `none of the above` option", and, because "Choice question probabilities always add up to
  1, so a line ranks first even when none answer the query", pair the Choice with a Noul: "Does any line of the document address or
  answer: [query]?" In the semantic-find example the top line scored 0.86 while that Noul was 0.14 (semantic-find cookbook).
- **Why it matters** [V-author]: PriorBench: "Without an explicit 'none of these' option, 0 of 30 out-of-scope messages were flagged —
  at 0.99 confidence"; a cake recipe went to a technical category at 0.94. On a label that depended on a policy absent from the text,
  Jev was 44.7% accurate at a mean probability of 0.74 (scienthoon). In a pre-registered bias audit, "With a third option, 'don't
  know', Jev chose it in 72 of 72 calls" [V-author]: an escape can also be too attractive.
- **Plotroom today** [V per docs]: every menu ends with `X none fit` and, where the user can answer, `Q ask me` (doc 21 §3.2); doc
  55's escape pre-check ("does any option fully cover this?", H-Q2) is a knob for Qwen3.5-4B's near-fit misses (HM04, 12 of 24), and
  doc 59 S7 includes a coverage check; doc 56 EQ4 scores the two escapes as separate instruments with always-escape controls. Neither
  doc fixes how the pre-check is read; on the direct path our `X` still competes inside the same distribution as the real options.
- **Adopt** [I]:
  - An **existence gate**: an absolute yes/no read, in the same pass as the menu, asking whether the request and state are answered by
    any option at all (P-04). It routes; it never admits. It is doc 55's escape pre-check made concrete: an independent yes/no
    probability outside the menu's softmax, with its own calibration and threshold.
  - Three outcomes kept apart in code: *none fit* (`X`: no option serves), *ask* (`Q`: the user can supply the missing fact), and
    *not stated* (the deciding fact is absent from the request and digest; code maps it to a question card when the field is
    required and to a visible default when it is optional, doc 21 §4.2). "Not stated" is a code-level outcome of gates, not a third
    menu letter, because a menu with two look-alike escapes is what doc 56 DS2 ("visibly distinct" lists) warns against.
  - **Unknowable items** in the suites, where the deciding fact is withheld from the digest, to measure overconfidence the way
    planted escapes measure `X` recall.
- **Reject** [I]: judging "none fit" from `X` mass alone on near-fit menus; a third escape letter on every menu before an arm shows
  it helps.

### 2.5 Independent questions over one shared state; one item per state

- **What they do** [V]: all questions of a request run over one state, independently; speculative questions are asked in the same
  call ("ignored when irrelevant and save a round trip when they are not"). Thirteen questions over a 53,777-character state were
  12.2× cheaper and 10.0× faster than thirteen calls (parallel-questions cookbook) [V-author]; the primitives page cites the same
  cookbook as "11.5x cheaper and 9.6x faster", so the vendor's own figure varies by page. "Every answer is independent. One question's
  answer is not hidden context for another" (primitives page) [V].
- **What breaks it** [V-author]: jev-orderby-bench (`jev-1.13.0`, 360 labelled rows): "1 row per request" gave a ranking inversion
  rate of 0.038, "40 rows per request" 0.171; rows in slots 0–7 moved by 0.049, slots 24–39 by about 0.42, and the model "stops
  discriminating for rows deep in a state of about 12,600 input tokens". The vendor: "Accuracy falls as the state grows with content
  unrelated to the decision" [V]. An independent review warns that batched questions "cannot see each other's answers", so one
  response can contradict itself [V-author].
- **Plotroom today** [V per docs]: one decision per fresh capsule (doc 25 §3 principle 3; doc 21 §8.1); the menu last so permuted
  re-asks reuse the prefix (doc 53 §4.2); one cache namespace per (stage, DecisionKind) (doc 40 R4); `map` fan-out seeded per item
  (agent-runtime §5). OpenJev read Qwen3.5-4B option logits over a shared prefix: 21 questions in 1.023 s against 5.332 s as generated
  JSON on an RTX 3090, and "BF16 execution changed 5–6 of 777 argmaxes relative to fresh scoring" on the prefix-reuse path [V-author].
- **Adopt** [I]:
  - A **state-shared layout** (P-06): frozen doctrine → quoted request → digest as the shared prefix; each question (its card, menu
    and schema) as its own tail sequence. On llama-server this is one prefill of the item plus a short tail per question. It is a
    named layout id beside doc 55's `static_first.v1`, because static-first per-DecisionKind prefixes cannot share an item's state
    across kinds (a design-gap candidate, §4 item 6).
  - **Independence is an invariant**: no answer enters another question's context unless a declared dispatch step puts it there;
    cross-answer consistency is a code check (for example, a "not stated" gate against a filled value).
  - **One item per state** for per-item questions: the play-tester (DP-10), lint batches and advisory ordering of K candidates never
    pack several items into one state and ask per-item questions.
- **Unknown** [U]: whether llama-server reuses one item's prefix across parallel slots, or only within one slot's cache; whether the
  prefix-cached path changes argmaxes on our quantised files (qualify it separately from fresh scoring).

### 2.6 Distributions, not a vendor "confidence"; calibration per question form

- **What they do** [V]: return full distributions; confidence is a concentration measure the caller may replace; the agent skill says
  "If you have a specific statistical algorithm in mind, you should probably be using probabilities instead of confidence". The vendor
  claims calibration from its training but publishes no reliability diagram or ECE (per an independent review) [V-author].
- **What independent tests found** [V-author]:
  - scienthoon (4,621 calls): ECE 0.107 on 900 unseen synthetic tickets against a noise floor of 0.024 ("Measured 0.107 is 4.4× the
    floor"); refit temperatures of 1.30 (Choice), 1.92 (Score) and 0.66 (boolean), so Choice and Score are over-confident and yes/no
    under-confident; probabilities are quantised to 0.01 with frequent exact 0 and 1; advice: calibrate per question type, and do not
    threshold on the `confidence` field: "On these sets it was never better than the max probability and sometimes much worse".
  - The vendor's own refund example: a Noul gave 0.22 while the equivalent Choice gave 0.01 / 0.99, and `refund` 0.72 plus
    `not_refund` 0.47 sums to 1.19 [V: jaggedness].
  - jev-wide: log-odds between a fixed pair moved by +0.31 to +0.50 as other options changed [V-author].
  - Plain Gemma 4 26B read by label probabilities: one temperature fitted on 50 labels took the median ECE over 13 subsets from 0.180
    to 0.074–0.080, against Jev's 0.071 as shipped (pre-registered; the test sets predate Gemma 4 and may be in its training data)
    [V-author].
- **Plotroom today** [V per docs]: doc 53 T3–T4 and §4.2 (prior division, fitted temperature, margin rules, R4's held-out ECE ≤ 0.10);
  doc 16 §4.2 logs probabilities with the menu hash; doc 16 §5 item 5 fits on development cases only.
- **Adopt** [I] (P-07):
  - Calibration and routing thresholds are keyed by (harness preset, DecisionKind, question form, wording hash, menu size, prompt
    language), not by model alone; Czech, Polish and Russian users need the language in the key (doc 16 open question 4). On Jev,
    Russian XNLI accuracy fell from 88.3% to 77.3% with ECE rising from 0.032 to 0.096, while intent and topic selection held
    (jev-cyrillic-audit); a Korean audit found accuracy 6.5 points lower on identical items with ECE unchanged (jev-calibration-audit)
    [V-author]. The effect depends on task and language, so it must be measured, not assumed.
  - Never derive P(not X) from a separately asked P(X); never compare probabilities across menus or chunks.
  - Floor probabilities at ε before log-loss and logging; pre-register the ECE binning, report it against a resampled noise floor, on
    the held-out split only.
  - About 50 labels per (preset, DecisionKind, form) as a first size for a temperature fit, to be checked on our suites.
  - The routing statistic (margin, normalised max, entropy, `X` mass) is a doc 55 knob, chosen on the tuning split.
- **Reject** [I]: TypeSafe's concentration "confidence" as a default routing statistic; any single temperature per model.

### 2.7 Combining judgements: weakest link, back-off, beams

- **What they do** [V]: "Confidence reports the least certain judgement in the call, rather than the product of all of them, since
  one wrong argument is enough to spoil the result" (function-calling cookbook); a date's confidence is its lowest part's. The SEC
  classification cookbook reports the parent division instead of one of 75 groups when confidence is under 0.9: forced groups were
  39 of 60 right, the back-off gave "48 of 60 useful answers", and below the threshold "naming a group was wrong more often than right,
  at 40%. Reporting those same answers as a division takes them to 70%" [V-author; 60 pre-filtered items, threshold at the in-sample
  median]. The hierarchical cookbook keeps a beam of 3 and scores paths by the geometric mean of edge probabilities: 4 of 4 against
  greedy's 2 of 4 [V-author; n = 4].
- **Plotroom today** [V per docs]: facet steps side → kind → role group → role (doc 25 §6.2); per-field Fill as a doc 55 knob (doc 53
  §4.4); no rule yet for how field or facet confidences combine.
- **Adopt** [I] (P-08): a Fill record's routing confidence is the minimum over its fields, and the confirm card highlights that field
  (glass box, D010); a facet chain whose leaf margin is low stops at the last confident facet and shows the children as a top-k card
  or `Q`; at a low-margin level a beam of 2 costs only extra one-pass reads on a cached prefix. All three are candidate arms for doc
  53 §5 and doc 59.
- **Reject** [I]: the product of confidences as a record score.

### 2.8 Thresholds are policy and scale with stakes

- **What they do** [V]: "A confidence threshold is not one number. Different actions within the same system should be gated at
  different levels depending on the consequences of getting it wrong"; the page's example routes a balance check on low stakes ("Showing
  the wrong screen is recoverable") and asks for more than 0.9, or a user confirmation, before approving a transfer (confidence page).
  The RAG cookbook keeps thresholds in one dictionary: "a change of policy is a constant edit under code review, not a reworded
  question". The Noul consistency cookbook routes 0.30–0.70 to review: "A review band absorbs fluctuation around 0.5 without issuing
  opposite automatic actions", and "The band is illustrative". Every cookbook threshold is a starting point, not a default. pi-jev: "The
  threshold sits mid-gap at 0.85, because the same state moved by ±0.05 between runs and either edge would have flipped" [V-author].
- **Plotroom today** [V per docs]: confidence routes presentation and never admits (doc 16 §4.2; doc 53 §4.1 item 3); doc 55 puts
  cascade thresholds in the harness preset; Confirm autonomy already waits for a click on deletes and large batches (doc 21 §7.3).
- **Adopt** [I] (P-09): two tables. (a) **Per-preset routing values** (accept margin, re-ask margin, top-2 margin, `X`/gate
  threshold), tuned and bound as D048 says. (b) **Product-owned stakes floors per DecisionKind**, set by what a wrong pick costs to
  notice and undo (a reversible single-entity edit against a campaign-branch or multi-entity change); the preset loader refuses a
  routing value below the floor. An explicit dead band maps to doc 53's one permuted re-ask. Thresholds are placed mid-gap on the tuning
  split after measuring run-to-run jitter.
- **Reject** [I]: any threshold that admits content, and any per-model setting that lowers a stakes floor.

### 2.9 Code proposes, the model selects, code copies

- **What they do** [V]:
  - Pre-parsed extraction: a regex over-finds spans, a Choice with `NONE` picks one, code copies it: "It cannot invent a value or
    transpose a digit". Autoformat: "every character of the output comes from the input".
  - Date extraction: seven Choices (mode, month, day, year, day anchor, weekday, week offset), each with `none`; "The model reads what
    the text says and never does the calendar math"; impossible dates become flags, and anything under 0.60 goes to review.
  - Citation check: a quote not found by normalised string match is fabricated, "and no model is needed to find that out".
  - Function calling: per optional argument, "a second yes/no question asking whether the command says anything about that argument
    at all. When the answer is no, the call leaves that argument out and the function's own default applies"; "Free text, numbers
    and dates work the same way: no question, and the function's default stands".
- **Plotroom today** [V per docs]: code-candidate span Picks and verbatim grammars (doc 53 §4.4; doc 55 H-Q3, H-R3); "exact copies are
  picked by index" (doc 56 DS2); `IntentFill` fields are `Option<Quoted<…>>` with quotes checked as substrings (doc 21 §4.1); doc 56
  DS1 proposes a named "nothing stated" value. Measured failures this targets: Granite 4.1 3B left named places empty (6 of 6), and
  the judgement field `size` was right 14–19 of 24 times across models (doc 55 §1.1).
- **Adopt** [I]:
  - A **"stated?" gate** per optional or judgement field (P-05): an absolute yes/no read before the value Pick, so an unstated field
    becomes a visible default or a question card instead of an invented value. Today the generative model must *choose* to leave a
    field empty; a gate asks it separately and is calibratable.
  - A **date and time recipe** for mission intel ("at dawn, two days after the landing"): the model picks components with `none`, code
    assembles, validates and flags impossible values, and confidence is the minimum over parts (P-15).
  - **String match first** for EXPLAIN quotes of card text: a quote not in the card is refused with no model call (P-15).
- **Reject** [I]: nothing; these match doctrine.

### 2.10 Decompose into atomic checks; combine in visible code; ordinal Scores

- **What they do** [V]: "Ask for a judgment a knowledgeable person makes in a second"; one dimension per Score; "Describe situations,
  not degrees"; "The model doesn't see a level's number or its neighbours, so 'worse than the previous level' means nothing to it"; use
  "as many levels as you can describe distinctly, up to 10"; composite scores are weighted in code. "Different distributions can
  produce the same score", so the expected level is a position, not a magnitude.
- **Evidence** [V-author]: anisselbd's phishing test: Jev asked once, 62.6%; five narrow signals combined by a logistic regression
  fitted on 1,000 emails, 95.0% on the other 1,000. But Haiku's best single signal (94.2%) beat its own five-signal composite (93.2%):
  the gain depends on the model. The vendor's own workflow evals show the weakest model gaining most (Haiku 4.5 from 18.1% to 53.6%),
  with no case counts published.
- **Plotroom today** [V per docs]: decomposition is doc 55's strongest knob; doc 53 DP-12 bins bounded ints into ≤ 7 bands; doc 59
  (draft) S7 is an arm of targeted sub-questions combined by code.
- **Adopt** [I]:
  - An **ordinal form** (P-10) for judgement and intensity fields (`size`, atmosphere intensity, the realism dial's bands): levels
    described as concrete situations, the expected level computed from letter probabilities; mass split across adjacent bands is
    benign (take the nearer), across distant bands it routes to a question card.
  - **Composite advisory checks** (P-18): plausibility lints, era checks and play-tester rubrics as several atomic yes/no checks with
    visible, editable weights. The realism dial (AGENTS.md: "an explicit, visible per-mission / per-campaign setting") changes weights,
    never which checks exist. Weights are fitted on the tuning split only.
- **Reject** [I]: weights learned from users' data, or any composite that becomes an error rather than advice.

### 2.11 Explanation by decomposition, not generated rationale

- **What they do** [V]: Jev returns no reasoning ("Jev does not produce reasoning traces, explanations, or free-form text"; "It returns
  probabilities", OpenRouter's guide); transparency comes from atomic questions combined by visible code; the composite-scoring page
  says the pattern "gives you visibility into how exactly the final score is being calculated".
- **Plotroom today** [V per docs]: the glass-box rule (AGENTS.md; D010) and the decision record (doc 53 §4.1 item 4; doc 55 §3.6);
  doctrine still asks for a bounded `why` before Pick and Fill answers (doc 25 §4.3, doc 38 §3.3), which doc 53 R7 tests.
- **Adopt** [I] (P-13): for PICK and gate steps, the inspector's "why" is the recorded sub-answers plus the code rule that combined
  them ("role group chosen; role left to the default: margin 0.08"; "not stated → default shown as a chip"). It is exact, costs no
  decode tokens and cannot contradict the answer. Doc 59 can use it as the baseline arm against short model-written rationales.
- **Reject** [I]: nothing; a model-written `why` stays an arm, not a requirement, until R7 decides.

### 2.12 Published limits per version: "known rough edges" per harness preset

- **What they do** [V]: a per-version jaggedness page lists nine weaknesses (literal reading, maths and numbers, dates, indirection,
  large irrelevant state, adversarial content, contradictory instructions and criteria, structural invariants, generation), each with
  a mitigation. Independent tests contradict parts of it: PriorBench measured "99.6 % across 13 designs" on number and date comparison
  and 100% on negation, and "18 of our 21 misses" were wrongly predicted failures [V-author]. The page is conservative guidance, not
  measured truth.
- **Plotroom today** [V per docs]: doc 55 §3.4 badges and §3.6's "what the harness preset changes" page; doc 51 §4.3 separates probed
  facts (the profile) from tuned choices (the preset); the model-independent "where a chooser must never decide" list (facts,
  arithmetic, counts, dates, identifiers, acceptance) is doc 16 §3.3.
- **Adopt** [I] (P-14): each harness preset carries structured **known rough edges**: failure class, evidence (suite hash, n), and
  the mitigation in use. Examples from doc 55 §1.1: Qwen3.5-4B, rule-bearing trigger menus (HT03, 0 of 24) → extract-then-dispatch;
  Granite 4.1 3B, empty named places → code span candidates; Gemma 4 E4B, an invented fix → code-chosen fix. The model's settings page
  shows them, and a Standing Orders entry explains the model-independent list (facts, maths, dates and counts stay in code).
- **Reject** [I]: listing a weakness without our own evidence or a labelled vendor source; a single star rating (doc 21 §12.3).

### 2.13 Stateless requests, minimal state, untrusted content

- **What they do** [V]: every request carries its own state; "Giving it more context in `state` than the question needs" is on the
  avoid list; the model "does not treat [state] as hostile by default"; in the RAG cookbook the injection check "is a filter, and only
  one", and conflicting passages go to a separate block.
- **Evidence** [V-author]: zkousama/jagged (pre-registered, 486 discussions): one planted sentence asserting a false fact and telling
  the model to ignore the rest took accuracy from 96.5% to 26.5%; the authors found Jev "mostly ignored the instruction and believed
  the fact". The study's other perturbations (literal reading, numbers, dates, indirection, padding, criteria) moved Jev's accuracy by
  at most 1.4 points. It ran no LLM baseline, so it says nothing about how Jev compares with generative models under attack.
- **Plotroom today** [V per docs]: the harness holds the state and each capsule is rebuilt from the document (doc 21 §8.1); digests
  are shrunk by relevance rank, never summarised; untrusted text is quoted and labelled (doc 21 §9.1); injection cases are a stress
  class (doc 21 §12.2).
- **Adopt** [I] (P-12): a **planted false fact** variant of the injection class ("this trigger already uses AND" in marker text):
  any decision that depends on a fact reads it from code-owned fields, so the planted claim must change nothing; EXPLAIN grounding keeps
  supporting and conflicting evidence in separate blocks.
- **Reject** [I]: nothing new; the design already matches.

### 2.14 Robustness by perturbation, not repetition

- **What they do** [V; V-author]: the consistency cookbooks vary irrelevant content per call ("Every query also gets a fresh uid, a
  throwaway unique value that changes each run while leaving the claim and rubric unchanged") and say "These percentages measure
  repeatability only"; the CEO describes putting UUIDs in prompts to test that similar inputs give similar outputs.
- **Plotroom today** [V per docs]: pass^k over repeated runs (doc 21 §12.3), permuted menus per sample (doc 25 §7.3), paraphrase and
  near-pair variants (doc 16 §5 item 1; doc 21 §12.2). With greedy one-pass scoring, identical-prompt pass^k equals accuracy (doc 53
  §5.4), so it measures nothing new.
- **Adopt** [I] (P-11): **perturbed replicas** in qualification: fresh entity ids, renamed markers and groups, shuffled irrelevant
  digest fields, padding with unrelated but valid state, permuted menus, polarity swaps and name reassignment. Report pass^k across
  perturbations as the stability measure for D037 badges and doc 55's held-out suite, apart from accuracy.

### 2.15 Versioning: aliases move, pins hold

- **What they do** [V]: "An alias moves when a new release ships, so the answers behind it can change without a change on your side";
  pin the version if you tuned thresholds; the response names the resolved version, and LiteLLM logs the versioned id even for an alias.
- **Plotroom today** [V per docs]: D048 item 5 binds presets to the exact file, runtime build and template; doc 16 §5 item 7 pins
  hosted Jev to `jev-1.13.0`; doc 56 MA4 cross-checks the served model on every reply; DG012 lists re-qualification triggers.
- **Adopt** [I] (P-16): run records store the **runtime-reported** identity, not the requested one; a cloud endpoint that exposes only
  a moving alias cannot hold a qualification badge.

### 2.16 Cost and latency transparency

- **What they do** [V; V-author]: input-only pricing with free output ("Output tokens are free", models page); the launch post claims
  "End-to-end response time is 70ms-500ms", and the Noul consistency cookbook measured 111 ms on average; PriorBench measured a ~430 ms
  fixed floor through OpenRouter ("Chaining two Jev calls wastes 430 ms for nothing").
- **Plotroom today** [V per docs]: doc 40's cost model and the plan card (D026); decision steps are prefill-bound (Pick prompt p50
  650–990 ms against 106–430 ms of decode on 4B Vulkan, doc 53 §3).
- **Adopt** [I] (P-17): record prefill tokens, cached tokens and decode tokens per decision and show them in the decision inspector;
  multi-stage flows (shortlist → inspect) reuse the item's prefix.

### 2.17 Typed client ergonomics

- **What they do** [V]: `ResultFor<T>` maps each question type to its answer type, and a Choice answer's `choice` is typed as the
  literal union of its option keys; Python validates into Pydantic models; errors carry status, body, request id and a `field_path`;
  an SDK release moved key validation earlier and kept the key out of logged exceptions; rig's client rejects missing or unexpected
  response ids and "does not silently renormalize".
- **Plotroom today** [V per docs]: `Selection { Candidate, NoMatch, Clarify }` (doc 16 §4.2), `Admitted<T>` (DG011), strict admission
  (doc 21 §8.2), newtypes and exhaustive `match` (AGENTS.md).
- **Adopt** [I] (P-03): `trait Question { type Answer; }` with `Pick<M: Menu>` returning a distribution keyed by the menu's own option
  newtype (`X` and `Q` as enum variants), `YesNo` returning a probability newtype with a fixed polarity, and `Ordinal<L>` returning the
  level distribution plus its expected level. Adapter errors carry the field path; the pre-renormalisation mass on valid letters is
  logged as a format-confusion signal.
- **Reject** [I]: SDK-style leniency for unknown answer types at admission (the journal keeps the raw reply as untrusted data; the
  workflow gets nothing).

### 2.18 Cookbooks: recipes with numbers and caveats

- **What they do** [V]: each cookbook is a runnable end-to-end pattern with its questions, thresholds, a small result table and its
  caveats ("Treat them as a starting point, not defaults").
- **Plotroom today** [V per docs]: doc 38 §8's three example workflow definitions; Standing Orders and Drill for users (doc 33).
- **Adopt** [I] (P-15): a **recipe set for contributors**: each recipe is one DecisionKind pattern (stated-gate Fill, date parts,
  lookup with an existence gate, two-stage shortlist then close inspection, facet back-off, composite advisory check, string-match-first
  quote check) with a synthetic fixture, a faux-model test and, once measured, its evidence and caveats.

## 3. Concrete proposals for Plotroom

Priority: **P1** cheap and on the path of doc 53/55 tooling or the first harness crates; **P2** valuable once the first crates exist;
**P3** later or owner-gated. Every proposal starts with the named failing test (AGENTS.md "Test-First / Proof-First"). Crate names
follow crate-map and are not final.

### 3.1 P1

- **P-01 Question and menu style guide, with a load-time lint.** Changes: a style section in doc 38 §6.2 (definition compiler) and
  doc 25 §6.2; the prompt-pack loader in `plotroom-workflow`. Rules the lint enforces: no self-ability wording ("can you", "are you
  able"); one condition per yes/no (refuse bare `and`/`or` joining two conditions unless marked as one concept); no semantic answer
  tokens; the declared polarity is "high = flag"; every option has a description; ordinal levels carry a situation description.
  Test first: fixture questions for each rule are refused with a finding naming the rule; a clean fixture passes.
- **P-02 Wording hash in the run record, calibration key and qualification key.** Changes: agent-runtime §5 (`ModelRequested`), doc
  55 §3.2 and §4.5, DG012 (extends doc 55 §7 item 1). Test first: changing one character in a question's description changes the
  hash, marks the affected badges `requalifying` and makes the calibration lookup return `Uncalibrated`.
- **P-04 Existence gate.** Changes: doc 55 §2.1 decomposition knob (`escape_precheck` asked as an independent yes/no), doc 53 §4.2
  step 5, doc 16 §4.2 and doc 21 §4.1–§4.2 for the `Selector`'s `NoMatch`. Test first: with a faux model giving low `X` mass but a gate below threshold, the
  step settles `NoMatch` (or `X`) and records both reads; the gate never admits an option. New suite items: unknowable cases with the
  deciding fact withheld. Arm for doc 53 §5 and doc 55 H-Q2.
- **P-05 "Stated?" gates for IntentFill and judgement fields.** Changes: doc 21 §4.1, doc 55 FILL decomposition (`judgement_fields`,
  spans), doc 56 DS1. Test first: a request with no size stated yields `size` unset plus an assumption chip even when the faux value
  Pick returns a confident band; a stated size passes through. Arm for doc 55 (Granite empty places, `size`) and doc 59.
- **P-07 Calibration key and hygiene.** Changes: doc 53 §5.3 item 4 and §4.2 step 4; doc 55 schema `scoring.calibration`. Test
  first: a calibration table lookup with any key part different (form, wording hash, menu size, language) returns `Uncalibrated`;
  log-loss stays finite on a probability of exactly 0 (ε floor); ECE uses the pre-registered binning and reports its noise floor.
- **P-09 Stakes floors separate from preset thresholds.** Changes: D048 item 2 would need a clarifying note (design-gap candidate,
  §4 item 2); doc 55 §1.4 and the preset loader; a floors table owned by each DecisionKind registration. Test first: the loader
  refuses a harness preset whose accept margin is below the DecisionKind's floor; a decision in the dead band is re-asked once.
- **P-11 Perturbed replicas in qualification.** Changes: `tools/local-qual` suite generator; doc 55 §4.1 held-out design; doc 21
  §12.2. Replicas: fresh ids, renamed markers and groups, shuffled irrelevant fields, unrelated padding, permuted menus, polarity swap,
  option-name reassignment. Test first: the replica generator is deterministic per seed and never changes the expected answer (a
  script re-derives each replica's answer); the report shows the flip rate per perturbation.

### 3.2 P2

- **P-03 Typed question forms in Rust.** Changes: `plotroom-decide`; agent-runtime §6 (`PickAnswer`), doc 16 §4.2. Test first:
  adapter tests reject unknown or duplicate option ids, non-finite or missing probabilities, and mass off the valid letters above a
  bound; a doctest shows an exhaustive `match` over `PickAnswer` for a two-option menu plus `X` and `Q`.
- **P-06 State-shared layout and the independence invariant.** Changes: doc 55 layout ids (a `state_shared.v1` beside
  `static_first.v1`), agent-runtime §6 capsule order, doc 40 R4 (namespace), DG019. Test first: a capsule golden shows the shared
  prefix byte-identical across the item's questions and each question after its own breakpoint; a batched-versus-single check on
  llama-server (spike) compares distributions per question; a capsule builder refuses two items in one state for a per-item
  DecisionKind.
- **P-08 Weakest-link record confidence and facet back-off.** Changes: doc 53 §4.4, doc 25 §6.2, doc 55 cascade knobs. Test first:
  a three-field record's routing confidence equals its minimum field confidence and the confirm card marks that field; a facet chain
  with a low leaf margin returns the parent facet and a top-k card.
- **P-10 Ordinal form.** Changes: doc 53 DP-12, doc 55 knob catalogue, doc 25 §4.3. Test first: expected level from a fixture
  distribution; adjacent-band split proceeds with the nearer band, distant-band split routes to a question card.
- **P-12 Planted-false-fact injection class.** Changes: doc 21 §12.2, doc 16 §5 item 1. Test first: a mission whose marker text
  asserts a false trigger property yields the same decision as the clean mission, and the digest carries the fact from the code-owned
  field.
- **P-13 "Why" from sub-answers.** Changes: doc 38 §5.3 inspector, doc 55 §3.6. Test first: the inspector renders every recorded
  sub-answer, its value and the rule id that combined them, with no model text.
- **P-14 Known rough edges per harness preset.** Changes: doc 55 §3.3 schema (`notes` becomes `rough_edges[{class, evidence,
  mitigation}]`), §3.6; a Standing Orders entry (doc 33). Test first: the loader refuses a rough-edge entry without an evidence
  reference; a UI golden lists them on the model's settings page.
- **P-15 Recipe set.** Changes: a recipes section in doc 38 (or a new docs page), built-in workflow fragments later. Test first: each
  recipe's synthetic fixture passes end to end with a faux model, including its `none` and flag paths (date recipe: 31 February is
  flagged, not guessed).
- **P-16 Resolved identity.** Changes: agent-runtime §5, doc 56 MA4, doc 48 cloud identity. Test first: a reply naming a different
  served model settles as an identity mismatch; an alias-only endpoint's badge stays "unqualified".

### 3.3 P3

- **P-17 Per-decision token and latency record** in the ledger and inspector (doc 40; D026). Test first: ledger entries sum to the
  run total and split prefill, cached and decode tokens.
- **P-18 Composite advisory checks with visible weights.** Changes: validation-and-lints (advisory tier), the realism dial, doc 59.
  Test first: the realism dial changes weights only; a weight fitted on the tuning split is frozen by hash before any held-out run;
  a composite never produces an error-level finding.
- **P-19 Optional shadow run of hosted Jev through the `Selector` seam** (owner decision; not assumed). What it would be: a
  `DecisionModelSelector` behind doc 16 §4.2's seam, run only in offline research on synthetic routing and clarification instruments,
  pinned to `jev-1.13.0`, answering beside the active selector with nothing shown or applied, compared with arms R, G and D (doc 16
  §5). Preconditions the owner must settle: (1) a separate paid key, owned and paid by the owner, never a product feature; (2) data
  egress to a second service (D008, doc 16 open question 5); (3) TypeSafe's Acceptable Use Policy (effective 2026-09-23) bars using
  the service to "engage in, promote, support, or facilitate … violent activities" and to "generate or promote violent threats" [V];
  whether that counts as a violent-content clause is D047's open part, and under D047 item 3 combat-flavoured items would never be
  sent. Test first, all offline: adapter robustness per doc 16 §5 item 8 against recorded fixtures (unknown and duplicate ids,
  non-finite values, oversize state refused, timeouts); a journal test shows the shadow record while the UI and the document are
  byte-identical to a run without it.
- **P-20 Letters against names, per model.** Changes: doc 53 T2 and R5. Folded into P-11's reassignment replica for generative
  models; for any future encoder or decision model (doc 58), measure label binding before any other quality work.

### 3.4 Arms handed to sibling experiments

| Arm | Hand to | From |
| --- | --- | --- |
| Existence gate against `X` mass | Doc 53 §5.4, doc 55 H-Q2 | §2.4 |
| "Stated?" gate per Fill field | Doc 55 H-Q3, H-R3; doc 59 | §2.9 |
| Weakest-link routing; facet back-off; beam of 2 | Doc 53 §5.4 (f); doc 59 | §2.7 |
| `not_for` contrast rendering on and off | Doc 55 layout knob | §2.3 |
| Ordinal band scoring for `size` | Doc 55 FILL; doc 59 | §2.10 |
| Batched against single questions over one state | Doc 53 §5.3 instrument check | §2.5 |
| "Why" from sub-answers against model rationale | Doc 53 R7; doc 59 | §2.11 |

## 4. Design-gap candidates (listed, not filed)

1. **Question text as a hashed, versioned artifact in every key** (run record, calibration, qualification). Extends DG012 and doc
   55 §7 item 1.
2. **Stakes floors per DecisionKind as product policy.** D048 item 2 lets a preset set cascade thresholds; nothing says a preset
   cannot route an expensive decision on a low margin.
3. **The existence gate as a registered decomposition alternative**, with its own qualification. Overlaps doc 55 §7 item 2.
4. **Yes/no and ordinal as forms of the PICK shape.** Agent-runtime §6's `PickAnswer` and DG015's letter schema cover only one form;
   the closed step-kind list (doc 38 §3.2) should not grow, so the forms belong under `ModelShape::Pick`.
5. **"Not stated" semantics.** How a gate's "not stated" maps to `Q`, a visible default or `NotSupported`, and whether any menu ever
   needs a third escape. Relates to doc 56 DS1's named "nothing stated" value.
6. **A state-shared layout across DecisionKinds.** Doc 40 R4 keeps one cache namespace per (stage, DecisionKind) and agent-runtime §6
   puts per-kind cards in the frozen prefix; several kinds asked over one item's state need a shared-state namespace. Relates to DG019.
7. **One item per state.** No rule yet forbids packing several items into one capsule for per-item questions (play-tester, lint
   batches, ordering).
8. **Known rough edges per harness preset**: structure, evidence rules and where they are shown. Overlaps doc 55 §7 item 7.
9. **Recipes as a documented artifact kind**: a docs page, built-in workflow fragments, or both.
10. **Language in the calibration binding.** Doc 16 open question 4 asks about languages; nothing keys calibration by prompt language.
11. **Rationale from sub-answers against the leading `why`.** Adds a third option to the doc 25 §4.3 / doc 38 §3.3 tension that doc 53
    R7 tests.

## Open questions

1. **Owner:** is a shadow run of hosted Jev (P-19) wanted at all, and if so, with whose key, on which items, and under which reading
   of TypeSafe's Acceptable Use Policy (D047)? [U]
2. **Owner or technical:** who sets stakes floors, and are they visible or editable in Settings? [I]
3. **Technical:** does llama-server share one item's prefix across parallel slots, and does the prefix-cached path change argmaxes on
   our Q4 and Q8 files? [U]
4. **Technical:** how many labels does a temperature fit need per (preset, DecisionKind, form) on our menus; is TypeSafe-style 50
   enough? [U]
5. **Design:** should "not stated" ever be a menu letter, given the bias audit's 72-of-72 "don't know" and doc 56 DS2's look-alike
   warning? [I]
6. **Design:** should composite advisory weights be user-editable beyond the realism dial? [I]
7. **Measurement:** does the existence gate improve near-fit `X` recall without raising false escapes on Qwen3.5-4B, where `X` inside
   the menu missed HM04 in 12 of 24 samples? [U]
8. **Naming:** `YesNo` and `Ordinal`, or "gate" and "band", in user-facing inspector text? Pending user-facing names go to the design round (D034 item 3) and
   clear doc 02 §9's naming checklist. [I]

## Findings for sibling docs (reported, not fixed)

- **Doc 16 §2.1:** the launch post page now shows "Sep 27, 2026, 10:27 PM UTC", likely a re-publish time; third parties date the
  launch to 2026-09-15. Rate limits are now described as adjusting dynamically [V].
- **Doc 16 §1.1 and §2.1 ("calibrated by the author"):** add the independent out-of-distribution result (ECE 0.107, about 4.4× the
  noise floor; direction differs by question type) and the Russian XNLI drop (88.3% → 77.3%, ECE 0.032 → 0.096; jev-cyrillic-audit)
  [V-author].
- **Doc 16 §5 and §6:** Jev itself shows position effects (the bias audit: "Whichever option is listed first gains 0.37" between two
  equally framed options; PriorBench: "Fix your option order for ambiguous tasks (up to 13 points of movement)") [V-author], so
  permutation debiasing stays even for decision models.
- **Doc 12 §1.9:** TypeSafe's models page now lists pricing ($0.042 per million input tokens, output free) [V].
- **Doc 11 §7.1 item 10 and doc 16 §4.2:** TypeSafe's MIT `system-one-adapter-python` serves the same typed interface from generative
  backends, outside support for one typed seam over pluggable selectors [V].
- **D047:** TypeSafe's Acceptable Use Policy (2026-09-23) has violence clauses (§1.7, §1.9) that may count as violent-content clauses
  [V; reading is ours].

## Sources

All read on 2026-09-28. Quotes were read on the page unless the verification notes say otherwise.

**TypeSafe AI (vendor pages)**

- Docs index: https://docs.typesafe.ai/llms.txt
- System One, state, how-to-build, use-case map: https://docs.typesafe.ai/concepts/system-one.md,
  https://docs.typesafe.ai/concepts/state.md, https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md,
  https://docs.typesafe.ai/concepts/use-case-map.md
- Primitives: https://docs.typesafe.ai/primitives.md, https://docs.typesafe.ai/primitives/choice.md,
  https://docs.typesafe.ai/primitives/score.md, https://docs.typesafe.ai/primitives/noul.md,
  https://docs.typesafe.ai/primitives/advanced.md
- Confidence: https://docs.typesafe.ai/confidence.md
- Patterns: https://docs.typesafe.ai/patterns.md (fan-out, confidence routing, composite scoring, intent routing)
- Cookbooks: https://docs.typesafe.ai/cookbooks.md, each at `https://docs.typesafe.ai/cookbooks/<slug>.md` with these slugs:
  `function_calling`, `parallel_questions`, `semantic_find`, `autoformat`, `date_extraction_cookbook`,
  `pre_parsed_value_extraction_cookbook`, `citation_check`, `classification_using_confidence`, `hierarchical_classification`,
  `skill_suggestion`, `consistency_choice_cookbook`, `consistency_noul_cookbook`, `classifying_rag_passages`, `llm_guardrails`,
  `entity_alignment`, `sde_cascade`, `autoresearch_feature_discovery`, `rerank_typesafe`
- Composite scoring pattern: https://docs.typesafe.ai/patterns/composite-scoring.md; fan-out: https://docs.typesafe.ai/patterns/fan-out.md
- Models: https://docs.typesafe.ai/models.md; API: https://docs.typesafe.ai/api.md
- Jev 1.13 jaggedness: https://docs.typesafe.ai/model-jaggedness/jev-1.13.md
- Agent skill: https://docs.typesafe.ai/agent-skill.md
- SDK references and changelogs: https://docs.typesafe.ai/sdk/python/changelog.md,
  https://docs.typesafe.ai/sdk/python/api/retries.md, https://docs.typesafe.ai/sdk/python/api/exceptions.md,
  https://docs.typesafe.ai/sdk/javascript/changelog.md, https://docs.typesafe.ai/sdk/javascript/api/type-aliases/ResultFor.md,
  https://docs.typesafe.ai/sdk/javascript/api/interfaces/ChoiceResponse.md,
  https://docs.typesafe.ai/sdk/javascript/api/type-aliases/ChoiceCriteria.md
- Launch post (page header now "Sep 27, 2026, 10:27 PM UTC"): https://typesafe.ai/blog/introducing-system-one-models-and-jev;
  manifesto: https://typesafe.ai/manifesto
- Acceptable Use Policy (effective 2026-09-23): https://typesafe.ai/legal/acceptable-use-policy
- Workflow evals: https://evals.typesafe.ai/
- GitHub org and adapter: https://github.com/typesafe-ai, https://github.com/typesafe-ai/system-one-adapter-python
- CEO interview: https://www.latent.space/p/jev (2026-09-21)

**Integrations**

- rig client: https://github.com/0xPlaygrounds/rig/tree/main/crates/rig-typesafeai
- Pydantic AI: https://pydantic.dev/docs/ai/models/typesafe/
- LiteLLM: https://docs.litellm.ai/docs/pass_through/typesafe
- OpenRouter: https://openrouter.ai/docs/guides/community/jev
- Cloudflare Workers AI: https://developers.cloudflare.com/ai/models/typesafe/jev/
- pi-jev: https://github.com/y0usaf/pi-jev

**Independent evaluations and reviews**

- Sun, Xu, Shi, Yang, "Type-Safe Is Not Error-Free: A Constrained Decision Head Follows the Option Name, Not the Rubric Bound to It",
  https://arxiv.org/abs/2609.26758 (2026-09-22)
- PriorBench (pre-registered): https://github.com/priorbench/jev
- Out-of-distribution calibration: https://github.com/scienthoon/jev-ood-calibration
- Batching and ranking: https://github.com/yodablocks/jev-orderby-bench
- Menu-relative probabilities: https://github.com/123Satyajeet123/jev-wide
- Calibration audit (Korean, KoBBQ and MMLU-ProX): https://github.com/jujumilk3/jev-calibration-audit
- Cyrillic audit (Russian XNLI, MASSIVE, SIB-200): https://github.com/AHTOOOXA/jev-cyrillic-audit
- Bias audit: https://github.com/pawarbi/jev-bias-audit
- Planted false facts: https://github.com/zkousama/jagged
- Phishing decomposition: https://github.com/anisselbd/jev-phishing-bench
- Plain Gemma 4 26B against Jev (pre-registered, 2026-09-24):
  https://dev.to/gde/plain-gemma-4-26b-vs-jev-on-one-ec2-l4-21-points-behind-overall-level-on-yesno-45-behind-on-15k6
- Eight days of independent tests (2026-09-24):
  https://dev.to/gde/jev-after-eight-days-of-independent-tests-level-with-mid-price-llms-behind-the-frontier-1kln
- Independent evidence review: https://github.com/xbill9/gemma4-dev/blob/main/jev/reports/Jev%20independent%20evidence%20review.md
- OpenJev (label logits on Qwen3.5-4B): https://github.com/thapecroth/openjev
- Reviews: https://www.beri.net/article/typesafe-jev-typed-decision-model-calibration-decomposition-shadow-eval,
  https://flaviocopes.com/jev/, https://www.truefoundry.com/blog/typesafe-ai-jev
- Ibrahim and Zaki, https://arxiv.org/abs/2609.24574; Li et al., https://arxiv.org/abs/2609.26550 (abstracts, via the review)

**This repository**

`AGENTS.md`; docs 11 (§3.4, §7.1 item 10), 12 (§1.9), 16 (§1.3, §3.1, §3.3, §4.2, §5, §6, open questions), 21 (§2, §3.2, §4.1–§4.2, §7.2–§7.3,
§8.1–§8.2, §9.1, §11.6, §12.1–§12.3), 25 (§3, §4.3–§4.4, §6.2, §7.3), 33, 38 (§3.2–§3.5, §5.3, §6.2, §8), 40 (R2–R5), 51 (§4.3), 53
(TL;DR, §1.2, §3, §4.1–§4.4, §5.3–§5.5), 55 (§1.1, §1.4, §2.1, §3.2–§3.6, §4.1–§4.5, §6.1–§6.3, §7), 56 (DS1, DS2, DS6, EQ4, EQ5,
MA4, PK2), 58 (status only), 59 (S3, S7), 02 (§9); `docs/architecture/agent-runtime.md` §3, §4, §5, §6, §7; D008, D010, D022,
D023, D026, D034, D037, D047, D048; DG006, DG011, DG012, DG015, DG019, DG021, DG022.

## Verification notes

### 2026-09-28, author checks at write-up

- **Re-read at the source by the author** (through a summarising fetcher, asked for verbatim quotes): the jaggedness page (nine
  sections, the literal-reading sentence, the refund numbers, the irrelevant-state and adversarial-content sentences, the avoid list);
  the confidence page ("never locked into our definition"; "A confidence threshold is not one number"); the models page (aliases,
  alias movement, pricing, limits, "The same weights serve every account"); the agent skill (the four quoted sentences); the Score page
  (level independence, "Describe situations, not degrees", up to 10 levels, "Different distributions can produce the same score");
  the function-calling, semantic-find and classification-using-confidence cookbooks (every quoted number); the arXiv 2609.26758
  abstract (70.4 per hundred, 24x, random strings, 0% type errors); PriorBench (0 of 30 at 0.99; 16.7%; 99.6%; 18 of 21; 430 ms);
  scienthoon (0.107, 0.024, temperatures 1.30 / 1.92 / 0.66, 44.7% at 0.74, the confidence-field advice); jev-orderby-bench (0.038,
  0.171, slot shifts, 12,600 tokens); the Gemma-versus-Jev post (75.3 / 77.3, 84.8 / 84.6, 78.3 / 82.8, median ECE 0.180 → 0.080,
  61 ms on an L4, the contamination caveat); TypeSafe's Acceptable Use Policy clauses.
- **Taken from research notes, not re-read by the author:** the parallel-questions (12.2×), autoformat, date, pre-parsed, citation,
  hierarchical, RAG, guardrail and autoresearch cookbooks; pi-jev; Pydantic AI; rig's client; the SDK details; OpenJev; the
  anisselbd, zkousama, jev-wide, jev-calibration-audit and jev-bias-audit figures; the evidence review; the CEO quotes; the Laya
  letters-versus-names detail in the arXiv paper's body. These are marked [V-author] or [V] as their source class, and should be
  re-read before any of them is used as a decision input.
- **Resolved conflicts:** one summary gave refit temperatures of 3.29 and 3.40; the study's own page gives 1.30 (Choice) and 1.92
  (Score), used here. One summary gave the arXiv effect as "32.5% of Jev's answers"; the abstract's pooled figure (70.4 per hundred)
  is quoted here, and the per-model figure is left out. Two URLs circulated for the "eight days" review; the one quoted is the one a
  search returned.
- **Not verified:** any claim about how Jev is built; any Plotroom effect of any proposal; llama-server's cross-slot prefix reuse.
- **Folding steps, not done here:** a row for this doc in `docs/README.md`; the sibling-doc findings above.

### 2026-09-28, review

A second reader re-opened every cited TypeSafe page and every third-party source on 2026-09-28, through a summarising fetcher asked
for verbatim text and yes/no phrase checks, and re-checked every Plotroom claim against the cited doc, decision or design-gap file.
No model or keyed API was called. Corrections made in place:

- **Quotes that were not on the cited page, replaced with what the page says:** "Reading account data might proceed at lower
  confidence than approving financial transfers" (confidence page; it gives the rule sentence and a code example instead, §2.8); "One
  primitive's result does not become hidden context…" (the primitives page says "One question's answer is not hidden context for
  another", §2.5); "transparency into final rankings" (the composite-scoring page says "visibility into how exactly the final score
  is being calculated", §2.11); "absorbs fluctuation near decision thresholds without requiring additional API calls" (this is the
  Noul consistency cookbook, not the RAG cookbook, and reads "absorbs fluctuation around 0.5 without issuing opposite automatic
  actions", §2.8); "fresh UIDs per call" (the cookbook's sentence is now quoted, §2.14); scienthoon's "approximately 4.4 times its
  noise floor" (the page says "4.4× the floor", §2.6).
- **Claims without a source, removed or re-sourced:** the CEO's "per-output pricing would reward verbosity" (no pricing passage in the
  Latent Space transcript; removed) and "a claimed ~100 ms per call" (replaced by the launch post's 70–500 ms and the Noul cookbook's
  111 ms mean, §2.16); the Russian XNLI drop (not in jev-calibration-audit; it comes from jev-cyrillic-audit, now cited with its ECE
  values and the Korean result, §2.6 and the sibling findings); "Other attacks moved Jev far less than LLMs" (zkousama/jagged runs no
  LLM baseline; replaced by its own per-perturbation deltas, §2.13); "ordering moved accuracy by up to 13 points" (from PriorBench's
  recommendations, not the bias audit; re-attributed).
- **Numbers corrected:** Gemma's median ECE after the fit is 0.074–0.080 (Jev 0.071), not 0.080 alone; the parallel cookbook's 10.0×,
  plus the primitives page's own 11.5× / 9.6× for the same cookbook; the ranking-inversion rise is 4.5-fold (0.038 → 0.171); the date
  cookbook's seven Choices renamed to the cookbook's fields; the arXiv CI punctuation and "test-retest floor" wording; OpenJev's
  timings to the repository's 1.023 s / 5.332 s and its BF16 caveat.
- **Plotroom claims corrected:** doc 58 now exists (draft, proposals only); doc 53 T2 and R5 *plan* the letters-versus-text
  comparison, nothing is measured yet; the look-alike warning is doc 56 DS2, not DS1; "PerMission" is not a roll scope, and HV01's
  confusable pair is PerCampaign vs PerTurn (doc 55 §1.1, doc 43); doc 16 §3.3 lists where any chooser must never decide, not what
  Wilco never decides; the Selector's `NoMatch` lives in doc 16 §4.2 and doc 21 §4.2, not only doc 21 §4.1; the existence gate is
  now described as a concrete reading of doc 55's escape pre-check (H-Q2) and doc 59 S7's coverage check; doc 59 is a draft, not
  "in progress"; the naming question now points at D034 item 3 as well as doc 02 §9.
- **Labels upgraded after reading the source:** the bias audit's 72 of 72 and 0.37, OpenJev, and the Laya letters result are now
  read at source ([V-author]); the Laya figure (56.4% → 27.8%) is quoted from the paper's HTML body.
- **Checked and correct as written:** models, API, primitives, Choice, Score, Noul and state pages; jaggedness headings and the refund
  table; agent-skill sentences; function-calling, semantic-find, classification-using-confidence, hierarchical, date, pre-parsed,
  autoformat, citation, RAG and autoresearch cookbooks; SDK retries (408, 429, 5xx; capped, jittered), exceptions (`request_id`,
  `field_path`), Python 0.7.1's key handling, `ChoiceResponse.choice: keyof T & string`, free-form `ChoiceCriteria`; the workflow
  evals (Haiku 4.5 18.1% → 53.6%; no case counts); the adapter repository (MIT; OpenAI-compatible, Anthropic, Gemini); the AUP
  (effective 2026-09-23; §1.7, §1.9; no fiction or game carve-out); the launch post header; pi-jev, Pydantic AI, LiteLLM, OpenRouter,
  rig and Cloudflare pages; PriorBench, jev-orderby-bench, anisselbd, jev-wide and the evidence review; every other Plotroom cross-
  reference (docs 11, 12, 16, 21, 25, 38, 40, 51, 53, 55, 56; agent-runtime; D023, D047, D048; DG012, DG015).
- **Scope and hygiene:** every proposal is marked [I] and changes no decision; P-19 stays owner-gated, offline, separately keyed and
  outside the product; no agent tool, network path or file access is proposed. No private or unpublished project is named, and no
  local path, username or key appears. Every URL in Sources resolved on 2026-09-28 (the `.md` doc URLs failed DNS once, then
  resolved). The bare-URL style of Sources follows the sibling docs.
