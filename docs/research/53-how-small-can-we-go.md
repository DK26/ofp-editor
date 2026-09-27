# How small can we go? Tiny models and the harness built around them

Research doc 53 for Plotroom (`ofp-editor`). Research date: 2026-09-28. Audience: contributors and LLM coding agents. This file is
meant to be read on its own.
Question answered (owner, 2026-09-27): "How small can we get with SLMs while designing a harness around them that makes the best of
their advantages? Another interesting model is Granite 4.1."

**Status: draft — experiments pending.** No model was loaded or run for this doc. Plotroom's own measurements are quoted from docs
44 and 46, plus an offline re-analysis of their stored call records (no new calls). Rows from the doc 49 shortlist run are marked
**preliminary, doc 49 pending**. Every floor, speed class and design rule below is a hypothesis for §5 to test [I].
**Epistemic legend** (doc 14's): **[V]** verified against the cited primary source; **[V-vendor]** the vendor's or author's own number
about its own model; **[V per doc N]** taken from a sibling doc; **[I]** our inference or proposal; **[U]** unknown. Web sources are
cited as [S1]…[S75] and listed under §Sources.
**Relation to sibling docs.** Doc 14 sets the model tiers; doc 16 the decision models, the `Selector` seam and the evidence bar; docs
21, 25 and 38 the step shapes and workflows; doc 40 the token economy and decision counts; doc 44 the first local measurement; doc 46
the llama.cpp and quant spike; doc 47 the small-model landscape and the next shortlist; doc 48 cloud hosts; doc 49 (in progress) the
measured shortlist; doc 50 the free, legal default and the cloud-screening protocol; doc 51 (in progress) model-native conventions;
doc 52 (planned) free-tier rate limits. D022 (Model Manager), D023 (model strategy), D027 (knowledge stack) and D037 (recommended list)
govern. D044 (recorded 2026-09-28) makes the owner's cloud-first screening rule accepted and its protocol P1–P5 (doc 50 §5) a proposal;
D045 (free models offered only where qualified per step kind), D047 (models and services whose policies ban military uses) and D048
(per-model harness presets) also apply. This doc changes no decision.
**Hygiene.** Public sources only; no game content, no private projects, no local paths.

**Names.** "Creative text" means briefings, radio lines, names and story beats (doc 47's DRAFT). **Draft** keeps its doc 21/25/38
meaning: a multi-entity ChangeSet. "Tiny" means under about 2B parameters; "session model" means the one general model a user's
setup keeps loaded (3–4B on an 8 GB GPU, doc 44). The DP-nn labels in §1 are this doc's own.

## TL;DR

- **One general model: not below about 3B. One decision at a time: much lower, if code owns the decision.** Granite 4.1 3B
  (3.40B) is the smallest model Plotroom has measured, and it met the doc 44 spike bar (spike-checked, not qualified under doc 21
  §12.3) on Pick (pass^3 0.833 without cards, 0.867 with), on card-grounded explanations (18 of 20, at the bar) and on text
  constraints (10 of 10 slots), but on no whole Fill record [V per doc 44]. Nothing under 3B has run on our suites [U].
- **Proposed floors per step kind** [I, all unmeasured]:
  - PICK: about 1–2B for a generative model with no task training; about 0.6B with calibrated one-pass scoring on code-shrunk menus;
    0.35B only for 2–3-way facet steps.
  - FILL: closed fields as per-field Picks at 1–2B; spans by a ~0.2B extractor or code candidates plus a Pick; judgement fields
    (`size`, `task`) never by a small model (computed Picks or questions).
  - EXPLAIN: writing at 3B or more with the card; checking at 0.1–0.6B; card-sentence selection at 0.4–1B.
  - Creative text, Compose, Draft: 4B and up for candidates, 12B+/26B-A4B or cloud for quality. Free-text engine knowledge: no size.
  - At 150M or less: helpers only (checkers, embedders), never a Wilco generator.
- **Why there** [V; I]: on public single-call data the "choose among options" knee sits near 1.5–2B (BFCL V4 Live Multiple:
  Qwen3-0.6B 56.13, Qwen3-1.7B 74.26, Qwen3-4B-Instruct-2507 76.16) [V S31]. IBM's own ladder shows +16–22 IFEval points from 350M
  to 1B and only +4–6 from 1B to 3B [V-vendor S5, S6]. Non-generative 0.6B rerankers score 0.61 macro-F1 on zero-shot classification
  against 0.65 for generative Qwen3-4B [V S46].
- **The harness that plays to small models' strengths** [I on V]: code shrinks each decision to a closed, fact-filtered menu; the
  model returns a whole distribution in **one forward pass** (letter probabilities, llama-server `n_probs`); a per-model calibration
  (temperature, letter prior) turns it into a confidence; the confidence only **routes** (accept, re-ask once with a permuted menu,
  show the top 2, `Q`, or offer a bigger model) and never admits. In our records, K = 3 identical-prompt voting bought +1.6 points of
  accuracy on average for three times the calls [V, offline re-analysis].
- **Confidence cannot catch fact errors.** The waypoint menu PW04 was unanimous *and* wrong in 15 model × condition runs [V, offline
  re-analysis]. Code-filtered menus come before any tiny model.
- **Cascades work on our data, but doctrine forbids silent ones.** Escalating the menus whose three permuted samples disagree
  (13–33% of menus) to Gemma 4 E4B lifts majority accuracy for Granite 4.1 3B on `pick` from 0.933 to 0.967 and for Qwen3.5-4B on
  `pick-hard` from 0.833 to 0.967; Spark-X2.5-4B (a doc 49 row, preliminary) barely moves because it is confidently wrong [V,
  in-sample, n = 30]. D023 decision 3 rejects silent cross-model escalation, so a tiny → session → cloud cascade is proposed here
  only as a visible, user-bound role pair (a candidate design-gap request, §4.3).
- **Where tiny models matter.** CPU-only and 4–6 GB machines; Preview, when the game holds the GPU (D018); free-tier rate limits;
  high-volume batch steps (the play-tester). On an 8 GB GPU the 3–4B session model already picks in 0.3–1.1 s [V per doc 44/46],
  about as fast as the best CPU estimate for a model that could make the decision (0.7–1.3 s at 0.4–1B, §2.6 [I]), so there the gain
  is one-pass scoring on the session model, not a second model [I].
- **Granite 4.1 (owner question).** The family is 3B, 8B and 30B dense only; below 3B, Granite means the 4.0 Nano models of
  October 2025 [V S7]. The 3B is Granite 4.0 Micro's body with a new training run (same config and parameter count; official Q4_K_M
  within 1 KB), non-thinking by design, Apache-2.0 [V S1, S2]. It is the fastest and smallest model doc 44 measured, second on
  card-grounded explanations (18 of 20; Qwen3.5-4B 20 of 20) and first on knowledge with cards (8 of 24) [V per doc 44]. IBM ships
  task adapters for the 4.1 models and 4.0 Micro only, none for 4.2 or the Nano models (query clarification, answerability,
  hallucination detection, uncertainty, requirement check) [V S12, S13]. It is a GPU, Apple or iGPU session model, not a CPU default
  (an estimated 5.5–9 s per pick on the reference 4-core CPU) [I]. Granite 4.2-3B is the same base re-trained to think by default,
  which gives a clean controlled test of whether thinking is what Plotroom's direct-mode harness leaves on the table (§5, stage S7)
  [V S4; I].
- **Free default and rate limits.** A local CPU tier is the one AI path with no account, no rate limit and no cost. With Pick,
  intent Fill and enum Fill local, a 30-minute session drops from about 60 to about 12 cloud calls, which fits OpenRouter's free
  50 requests a day about four times; a campaign still needs about 428 text calls [I on V per doc 40, doc 48].
- **D044 (cloud-first screening): a proposed reading of its P5, for the owner to confirm.** D044's rule is accepted; its protocol,
  including P5 ("what cannot be cloud-screened goes local directly"), is a proposal. No ladder model in §5 is on OpenRouter or the HF
  router (2026-09-28); P5 already names Granite 4.1 3B and the 4.0 1B/H-1B, and D044's amendment sends Featherless-only models such
  as Qwen3.5-2B local, so the ladder is local under P5 as written. The proposal adds: encoders,
  rerankers, decision models and adapters are screened **locally on the CPU** (`-dev none`), and the letter-probability arms count as
  "local by nature", because hosted fp8/bf16 copies do not test the local Q8/Q4 file and most hosts return no log-probabilities.
  Cloud-first stays the rule wherever a same-weights host exists; the one hosted model in §5, Granite 4.2-3B (stage S7), is flagged
  in §4.10 [I on V S28].
- **Model Manager.** Weights stay optional, user-started downloads (D023 decision 1). The recommended list takes only OSI-licensed,
  qualified models (D037). Tiny models add artifact kinds (LoRA adapters pinned to one base file; encoders that llama.cpp cannot run),
  and the encoder runtime is a D022-level decision (candidate design-gap request). Q8_0 for anything of 1B or less.
- **Next (§5).** Build the scoring instruments first (letter and option-text scoring, calibration, cascade replay), then run a floor
  ladder from Granite 4.1 3B down to Granite 4.0 350M at `-dev none`, with pre-registered stop and decision rules: roughly 6–11 hours
  of CPU and 2–3 hours of GPU (estimates), after doc 49's run frees the machine.

## 1. What each step kind really needs

### 1.1 Latency classes (proposal)

Anchored on the classic 0.1 s / 1 s / 10 s response-time limits [V S74]:

| Class | Budget | Used for |
| --- | --- | --- |
| L0 | < 0.1 s | Code only: menus, validators, facet steps. No model step lives here. |
| L1 | ≤ 1 s (≤ 2 s including any resampling) | Picks the user waits on: routing, lint-fix choice, interactive taste Picks |
| L2 | ≤ 2–3 s, first token < 1 s, streamed | Small Fills, grounded explanations |
| L3 | ≤ 10 s for 2–3 candidates, streamed | Interactive creative slots, Compose |
| L4 | background, minutes | Campaign runs, batch text, translation, play-testing |

Measured on the reference box (GTX 1070) for dense 3–4B models on the GPU: Pick p50 0.31–0.75 s on Ollama and about 0.8–1.1 s on
llama.cpp Vulkan; Fill 1.0–1.5 s; explanations 1.7–2.5 s [V per doc 44/46]. MoE offload (Qwen3-30B-A3B-2507, `--n-cpu-moe 39`): Pick
p50 6.5 s, Fill 11.3 s, explain 17.2 s (preliminary, doc 49 pending), so offload is L4 only [I]. Doc 47 §6.3 already proposes a CPU
Pick badge at p50 ≤ 3 s and an offload Fill at p90 ≤ 10 s.

### 1.2 Decision points, their outputs and the smallest plausible tier

| # | Decision point (where) | Output | Non-generative option | Smallest plausible tier [I] | Latency | Volume (doc 40 §5.1) |
| --- | --- | --- | --- | --- | --- | --- |
| DP-01 | Intent fill from free text (chat entry; wizard prefill, doc 21 §11.3; doc 25 §9.2's refine shape). Skipped when a gesture, context menu or palette starts the workflow | Closed fields (task, side, size, posture, era) plus place and target spans, quote-checked; code resolves the place against the island's names | Alias and lexicon rules; a per-field classifier; a span extractor | Cue fields 0.15–1B (classifier or per-field Pick); spans ~0.2B extractor; judgement fields: none, they become computed Picks or questions; the whole record in one call only at 26–30B MoE or cloud | L1 | 12 of 35 decisions per 30-minute session; 1 per chat-started workflow |
| DP-02 | Workflow routing, the `Selector` (`Candidate` \| `NoMatch` \| `Clarify`; doc 16 §3.2, doc 21 §4.1) | One letter, `X` or `Q` over ≤ 7 code-written workflow descriptions | `RuleSelector` (aliases, BM25 shortlist; doc 38 §3.5) | 0.4–1B with letter scoring; a ≤ 0.4B trained classifier in shadow only (D023 decision 5) | L1 | ≤ 1 per free-text request |
| DP-03 | Clarification choice (doc 16 §3.2, doc 21 §4.2) | One authored question, or none | Rules; code already knows which fields are missing | 0.4–1B; low value | L1 | Rare (≤ 3 questions before the first artifact) |
| DP-04/05 | Lookups: symptom → playbook (doc 21 §11.2); concept, gotcha or tutor hint rung (doc 33 §6.2–§6.3) | One letter over ≤ 7 retrieved ids, or `none_fit` | BM25/FTS, then the menu for the user | 0.4–1B letter scoring; a reranker only after it beats BM25 (doc 30 OQ2) | L1–L2 | Part of 4 explain/teach requests per session |
| DP-06 | Campaign taste Picks: home town, graph shape, beat per node, consequence archetypes, concept picks; the strategic layer's spine, modules, op archetype and site (doc 25 §4.1, doc 29 §6.2) | One letter, optional bounded `why` | Code's soft score from menu step 3 (the AI-off default) | 1–2B; 0.4–1B with calibrated scoring and a show-top-2 rule. Every option is valid by construction, so a wrong pick is only suboptimal | ≤ 1–2 s each inside an L4 run | 66 of 273 decisions per 8-mission campaign (~198 of 650 calls at K = 3) |
| DP-07 | Interactive taste Picks: populate-town composition, cutscene template and shots, music mood, atmosphere preset and intensity, replayability recipe, no-code module, power-tool chains (docs 31, 37, 38, 39, 41, 43) | One letter | Code-ranked default | 0.4–2B: these categories sit at the ceiling for 3–4B (mood 1.00, cutscene 0.92–1.00, no-code 0.93–1.00, routing 0.80–1.00; doc 44) | L1 | 1–8 per run; 5 per session |
| DP-08 | Fact-bearing semantic Picks: waypoint type (TR UNLOAD vs UNLOAD), trigger timing (Countdown vs Timeout), end semantics | — | Code filters by the fact it knows (rung 1) | **No model tier: a harness fix.** PW04 was right in 1 of 24 samples (doc 44) and 1 of 36 (doc 46); pick-hard at 30B-A3B (0.70 without cards) matched the 4B class (preliminary, doc 49 pending) | — | — |
| DP-09 | Lint-fix and repair choice among code-computed fixes (doc 31 §9, doc 32 §5.3) | One letter | The top-ranked fix | 0.4–2B; a low margin goes to the user | L1 | 6 of 35 per session |
| DP-10 | Play-tester persona moves (doc 21 §11.6) | One legal option per node | Scripted persona policies (doc 26 §8.2) | ≤ 1B on CPU: cheap, parallel, legal moves only | L4 | Journeys × nodes; the largest call count, unquantified [U] |
| DP-11 | Advisory ordering or critique of admitted candidates (doc 25 §7.3, doc 16 §3.2) | An order | Deterministic signals (lints, length fit, novelty) | None established; a ≤ 0.6B reranker or decision model in shadow only; judges never admit | L3 | Per candidate set |
| DP-12 | Enum Fills over computed ranges: guard constants, concept enums, patrol parameters, `cine.fill` fields (doc 21 §6.4, doc 32) | Flat record of enums and bounded ints | One Pick per field, ints binned into ≤ 7 bands; code defaults shown as chips (doc 25 §10.1) | 1–2B per field; a whole record at 3–4B only as a pre-fill the user confirms (doc 44 §5.1) | L1–L2 | 12 per campaign, 4 per cutscene, 2 per session |
| DP-13 | Campaign intake brief (S0) | 5 quote-checked Fills | The wizard interview (same typed brief) | As DP-01, with more judgement fields | L2 | 5 per campaign |
| DP-14 | EXPLAIN a finding (`explain a finding`, `cine.critique`, `atmo.explain`, `script.explain`) | ≤ 2 sentences plus a fix, from one card | Card or diagnostic text verbatim (the AI-off path, doc 30 L2); card-sentence selection plus a templated fix | Writing ≥ 3B with the card; checking 0.1–0.6B; selection 0.4–1B | L2 | 10 of 35 per session |
| DP-15 | Longer grounded explanations: concept paraphrase, tutor hint line, "Explain this mission" (doc 33 §6.4) | ≤ 3 sentences, up to a 150-word cited walkthrough | The entry verbatim; the MissionAnatomy view | 3–4B for ≤ 3 sentences behind the claim matcher; ≥ 8B or cloud for the walkthrough | L2–L3 | Occasional |
| DP-16 | Free-text engine knowledge | An answer | Code shows the card | **Never local, at any size**: every 3–4B build scored 0 of 24 without cards (doc 44/46) | — | — |
| DP-17 | Short flavour lines: radio bodies ≤ 8 words, titles, names, barks, captions, event variants | Line candidates | Templates, era word lists, a seeded phrase bank with a model Pick among variants (doc 25 OQ5) | Generated candidates at 2–4B that the user picks; phrase-bank Picks ≤ 1B; final quality at ≥ 12B dense, 26B-A4B MoE or cloud | L3 (L4 in batch) | A large share of the 176 text slots per campaign |
| DP-18 | Paragraph and creative prose: briefings, debriefs, dialogue, bible rows, premises | Paragraphs | Template text with seeded archetypes (doc 25 §2.9, §10.1) | 3–4B rough drafts only; quality at ≥ 12B, 26B-A4B or cloud | L3 / L4 | 176 of 273 campaign decisions, ~70% of cloud campaign spend |
| DP-19 | Compose: a mission concept, one radio exchange, one node's transitions, a script snippet | One sub-structure | Split into authored Fill and Pick steps on failure (doc 21 §3.3) | ≥ 8B or cloud; scripts cloud or ≥ 9B behind the gates (doc 14 §4.4) | L3–L4 | Per cutscene or refine |
| DP-20 | Draft: a multi-entity ChangeSet (doc 19 §8) | A ChangeSet | Code's authored decomposition | Cloud; local 27B+ experimental | L4 | Rare |
| DP-21 | Translation (translator role) | Localised lines with codepage lints and native review | — | ≥ 7B specialist or cloud today; the 1.7–1.8B specialists are candidates to test | L4 | Lines × languages [U] |

Sources: docs 21, 25, 29–33, 37–41, 43, 44, 46; doc 40 §5.1 and its cost model's per-workflow counts [V per docs; tiers I].

### 1.3 Where the calls are

- **30-minute session:** 35 decisions, 60 calls. Intent fills (12), edit Picks (5), lint-fix Picks (6) and edit Fills (2) are
  tiny-candidate work: 25 decisions (71%), about 48 of 60 calls. Finding explanations (6) and explain or teach answers (4) need a
  3–4B model with a card, or the card verbatim [I on V per doc 40].
- **8-mission campaign:** 273 decisions, 650 calls. Picks (66, ~198 calls) and enum or extract Fills (17, ~19 calls) are
  tiny-candidate work, about 34% of calls; creative text is about 428 calls (66%) and must stay at 3–4B or above [I on V per doc 40].
- **Cost context:** moving Pick and Fill to a local model cuts a Sonnet 5 session from $0.544 to $0.160 and a campaign from $6.88 to
  $5.13 [V per doc 40 §5.4, model outputs]. The interactive session is where small local models pay most.

### 1.4 Where size helps and where it does not

- **Helps: whole-record Fill.** All fields right per call: 0.25–0.64 at 4B (Qwen3.5-4B 0.47–0.64; Gemma 4 E4B up to 0.86), 0.917 at
  Qwen3-30B-A3B-2507 (preliminary, doc 49 pending) [V per doc 44/46].
- **Does not help: fact-bearing menus.** `pick-hard` without cards: pass^3 0.67–0.70 for Qwen3.5-4B and 0.77–0.83 for Gemma 4 E4B
  [V per doc 46], 0.63–0.70 for the doc 49 4B rows, and 0.70 at 30B-A3B, whose ~3B active parameters match the 4B class (both
  preliminary, doc 49 pending) [V].
- **Already at the ceiling: easy taste menus.** `pick` pass^3 0.83–0.97 at 3–4B [V per doc 44].
- **Rule [I]:** split records into per-field Picks, move facts into code filters, and spend parameters only on text.

## 2. The tiny-model frontier

### 2.1 How to read this section

Vendor numbers at tiny sizes disagree sharply between sources: Gemma-3-270m-it IFEval is 51.2 on Google's card and 27.44 in TII's
comparison; Qwen3-1.7B non-thinking IFEval is 68.2 in Qwen's report and 74.0 in Hugging Face's SmolLM3 table [V S35, S38, S32, S37].
BFCL's CSV does not state the thinking mode of its Qwen3 rows [U]. No public benchmark covers code-built menus with escapes, Czech,
Polish or Russian creative text, or SQF. Only our suites decide (docs 44, 47) [I].

### 2.2 Public anchors for "choose among options"

| Model (licence) | BFCL V4 Live Simple | Live Multiple | Irrelevance | Note |
| --- | --- | --- | --- | --- |
| Qwen3-4B-Instruct-2507 (Apache-2.0) | 79.07 | 76.16 | 84.93 | Doc 47's non-thinking 4B control |
| Qwen3-1.7B (Apache-2.0) | 76.74 | 74.26 | 76.54 | Thinking mode of the row unknown; mean latency 5.12 s vs 0.68 s for the 0.6B hints that they differ [U] |
| Qwen3-0.6B (Apache-2.0) | 61.24 | 56.13 | 80.84 | High irrelevance: a good sign for the `X` escape [I] |
| Granite-4.0-350m (Apache-2.0) | 61.24 | 42.36 | 60.84 | Overall 18.98% |
| Llama-3.2-1B | — | 7.31 | — | Use policy bans military applications |
| Gemma-3-1b-it | — | 6.27 | — | Gemma terms |

Source [V S31]. Choosing among many options degrades much faster than filling one call: the 350M matches the 0.6B on Live Simple and
falls 14 points behind on Live Multiple [I].

Zero-shot classification (BTZSC, 22 datasets, macro-F1) [V S46]: generative Qwen3-8B 0.66 and Qwen3-4B 0.65; GTE-large 0.62;
Qwen3-Reranker-0.6B 0.61; the best NLI cross-encoder 0.60; Qwen3-Embedding-0.6B 0.58; Llama-3.2-3B 0.43; Gemma-3-1b-it 0.36;
Gemma-3-270m-it 0.28. Non-generative 0.6B models come within 4 points of a generative 4B. Caveat: BTZSC classifies by label name, not
by code-built menus carrying facts (doc 44 PW04), so transfer is untested [U].

### 2.3 Shortlist per tier

| Tier | Generative (licence) | Non-generative and specialists (licence) | Evidence highlights | Verdict [I] |
| --- | --- | --- | --- | --- |
| ≤ 150M | None fit. SmolLM2-135M (IFEval 29.9); Falcon-H1-Tiny-Tool-Calling-90M (BFCL 41.23%, irrelevance 94.44%; Falcon licence with use policy, not OSI; English); Needle 3 (121M; own engine, not llama.cpp) | **HHEM-2.1-Open** (Apache-2.0; FLAN-T5-base, ~0.1B): EXPLAIN faithfulness score 0–1; **granite-embedding-97m-multilingual-r2** (Apache-2.0): exemplar retrieval; **mmBERT-small** (MIT, ~140M): base for a future trained classifier | HHEM: RAGTruth-QA balanced accuracy 74.28 vs 74.11 for GPT-4; ~1.5 s for 2K tokens on an x86 CPU; English only (the multilingual HHEM-2.3 is commercial) [V-vendor S47] | Helpers only |
| 150–400M | **Granite-4.0-H-350M / 350M** (Apache-2.0; 12 languages incl. Czech; 32K): IFEval 61.63 / 55.4, BFCL v3 43.32 / 39.32; LFM2.5-350M (IFEval 76.96; LFM licence, revenue-gated; no CZ/PL/RU). Skip Gemma 3 270M and FunctionGemma (gated Gemma terms; FunctionGemma is "not intended for use as a direct dialogue model") | **GLiNER2** (Apache-2.0; 205M; English; `multi` covers EN, FR, ES, DE, IT, PT): entities, classification and structured extraction in one pass; **LettuceDetect** EuroBERT-210M (MIT; per-language models incl. PL): EXPLAIN check; **mDeBERTa-v3-base-xnli** (MIT, ~0.3B): multilingual NLI (no CZ/PL in its fine-tuning languages) | GLiNER2 zero-shot CrossNER F1 0.590 vs GPT-4o 0.599; CPU 130–208 ms for 5–50 labels; but zero-shot classification 0.72 vs 0.84 [V-vendor S44]; 118,636 of 254,334 training examples were GPT-4o-annotated [V S44] | Generative: floor probe only. Non-generative: real candidates |
| 0.4–1B | **Qwen3-0.6B** (Apache-2.0; non-thinking IFEval 54.5, BFCL v3 44.1); **Qwen3.5-0.8B** (Apache-2.0; 201 languages; non-thinking by default; non-thinking IFEval 52.1; card warns of thinking loops in thinking mode; its intended-use line is unclear under D037). Watch: K2-Horizon-0.9B, MiniCPM5-1B (EN/ZH) | **Qwen3-Reranker-0.6B** (Apache-2.0; `ggml-org` Q8_0 GGUF; llama-server `--rerank`): shadow Selector and escape detector; **bge-reranker-v2-m3** (Apache-2.0, 568M, multilingual); **LettuceDetect EuroBERT-610M**; **decider-0.8b** (Apache-2.0; fitted temperature 1.03) in shadow; **EuroMoE-2.6B-A0.6B** (Apache-2.0; 35 languages; 0.6B active) for CPU translation | LettuceDetect-610M F1 73–77% per language vs 59–62% for GPT-4.1-mini [V-vendor S48]; decider-0.8b config [V S43] | CPU Pick probe; best tier for non-generative classification |
| 1–2B | **Granite-4.0-1B / H-1B** (Apache-2.0; 12 languages; 128K): IFEval 77.38 / 78.53, BFCL v3 54.82 / 50.21; **Qwen3-1.7B** (Apache-2.0; 119 languages): the strongest public single-call evidence under 2B; missing from docs 14 and 47 | **EuroLLM-1.7B-Instruct** (Apache-2.0; 35 languages incl. CS, PL, RU; 4K) or Hy-MT2-1.8B (doc 47) for translation; Jev-Style-Qwen3.5-2B-Decision (Apache-2.0; LoRA; shadow) | EuroLLM FLORES-200 86.89 [V-vendor S40]. Not recommendable: LFM2.5-1.2B (LFM licence; no CZ/PL/RU), Llama-3.2-1B (military ban) | The CPU Pick badge candidates |
| 2–3.4B | **Granite 4.1 3B** (§2.4); **Qwen3.5-2B** (Apache-2.0; non-thinking by default; the same intended-use line as the 0.8B, so unclear under D037; best Czech/Polish evidence in the tier, EuroEval CZ 2.54, PL 2.86); MiniCPM5-2B or Gemma 4 E2B for 4–6 GB GPUs (doc 47) | — | Watch: SmolLM3-3B (thinking on by default), Granite 4.2-3B with thinking off. Skip: granite-swash (base models only), limite-1b (math only) | Session-model floor on GPU, Apple, iGPU |

Sources: [S5, S31–S51; V per doc 47]. Official GGUF sizes for the rows §5 runs are in Appendix A [V S2, S33, S51].

### 2.4 The Granite 4.x family (owner question)

**Family map** [V S1–S7, S9, S10, S15]:

| Model | Released | Params | Architecture | Thinking | Official Q4_K_M / Q8_0 (bytes) | KV at 8K, f16 [I] | Vendor IFEval / BFCL v3 | Hosted (2026-09-28) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4.0 H-350M | 2025-10-28 | 0.34B | 28 Mamba-2 + 4 attention layers | No | 222,662,560 / 366,195,616 | 32 MiB | 61.63 / 43.32 | No |
| 4.0 350M | 2025-10-28 | 0.35B | Dense | No | 236,985,760 / 378,138,016 | 224 MiB | 55.40 / 39.32 | No |
| 4.0 H-1B | 2025-10-28 | 1.46B | 36 Mamba-2 + 4 attention | No | 901,162,208 / 1,558,926,560 | 64 MiB | 78.53 / 50.21 | No |
| 4.0 1B | 2025-10-28 | 1.63B | Dense | No | 1,023,645,440 / 1,737,791,232 | 640 MiB | 77.38 / 54.82 | No |
| 4.0 Micro | 2025-10-02 | 3.40B | Dense | No | 2,099,502,528 / 3,619,691,968 | 640 MiB | 82.31 / 59.98 | No |
| 4.0 H-Micro | 2025-10-02 | 3.19B | Hybrid | No | 1,942,564,512 / 3,397,676,704 | ~64 MiB | 84.32 / 57.56 | Cloudflare Workers AI; OpenRouter via Cloudflare |
| 4.0 H-Tiny | 2025-10-02 | 6.94B, 1B active (MoE) | Hybrid MoE | No | 4,230,976,352 / 7,390,331,744 | 64 MiB | 81.44 / 57.65 | No |
| **4.1 3B** | 2026-04-29 | 3.40B | Dense (GQA 40 heads / 8 KV, head dim 64, 40 layers) | **No, by design** | 2,099,501,664 / 3,619,691,104 | 640 MiB | 82.30 / 60.80 | No |
| 4.1 8B | 2026-04-29 | 8.79B | Dense | No | 5,347,914,400 / 9,345,610,400 | 1,280 MiB | 87.06 / 68.27 | No |
| 4.2 3B | 2026-08-25 | 3.66B | Dense, untied embeddings; post-trained from Granite-4.1-3B-Base | **Yes, on by default** | 2,244,011,552 / 3,892,651,552 | 640 MiB | IFEval 93.7 (OpenBMB table, doc 47); IFBench 74.33, BFCL v4 52.41 (the card does not state the mode; thinking is the default) | DeepInfra via the HF router (no enforced schema) |
| 4.2 8B | 2026-08-25 | 8.79B | Dense | Yes | 5,347,917,952 / 9,345,613,952 | 1,280 MiB | — | DeepInfra; OpenRouter at CoreWeave (bf16, structured outputs and logprobs) |

Also in the family: Granite 4.2 30B (dense, thinking; DeepInfra via the HF router), Granite Guardian 4.1 8B (a yes/no judge), Switch
4.1 previews (a 4.1 base with 12 embedded aLoRA adapters), SWASH 2B / 3B-A600M (base models only, English, not instruction-tuned),
Vision 4.1 4B, Speech 4.1 2B and embedding R2 97M/311M [V S7, S10, S14, S15]. There is **no 4.1 or 4.2 model below 3B** [V S7].

**Granite 4.1 3B, what it is** [V S1, S2, S9; I]:

- The same body as 4.0 Micro: identical parameter count (3,402,836,480) and config (40 layers, hidden 2,560, RoPE theta 1e7); the
  official Q4_K_M files differ by 864 bytes. New: about 15T pretraining tokens in five phases, about 4.1M SFT samples, and four
  stages of on-policy reinforcement learning.
- Vendor deltas against 4.0 Micro are chat quality, not instruction following or tools: IFEval 82.30 vs 82.31, BFCL v3 60.80 vs
  59.98, MMLU 67.02 vs 65.98, but AlpacaEval 2.0 38.57 vs 29.49 and ArenaHard 37.80 vs 25.84. SimpleQA 3.68 predicts doc 44's 0 of 24
  on free recall.
- IBM chose non-thinking deliberately: "competitive instruction-following and tool-calling performance without relying on long
  chains of thought, offering predictable latency, stable token usage, and lower operational cost" [V S9]. That matches Plotroom's
  direct-mode harness exactly.
- 12 languages including Czech, Italian, German, French and Spanish; not Polish or Russian (6 of the 8 engine languages) [V S1].
- 131,072-token context; KV cache 81,920 B per token, 640 MiB at 8K (320 MiB with q8_0 K/V), against 1,152 MiB for
  Qwen3-4B-Instruct-2507 [I, arithmetic from config].
- The chat template injects **no** default system prompt (4.0's injects one; 4.2 always emits a system block) and has a trained
  `documents` path: "strictly aligning with the facts in the provided documents … inform the user that the question cannot be
  answered". Passing a Standing Orders card as a `documents` entry is a cheap EXPLAIN arm to test [V S1; I].
- No sampler ships in `generation_config`; Unsloth recommends temperature 0, top_p 1.0 [V S17]. At T = 0, K = 3 voting collapses to
  one answer, so confidence must come from letter probabilities or the uncertainty adapter [I].

**Granite 4.1 3B in doc 44** (Ollama `ibm/granite4.1:3b-q4_K_M`, GTX 1070, T 0.6) [V per doc 44]: Pick accuracy 0.911 / 0.889 and
pass^3 0.833 / 0.867 (none / cards); off-scope `X` 3 of 3, false `X` 0 of 87; cards changed nothing (82 of 90 calls chose the same
letter). Weak categories: campaign arc 0.67, trigger 0.73–0.87, waypoint 0.80. Fill: field accuracy 0.792, whole record 0.389 per call;
only archetype and time of day qualified. Explain with card: 18 pass, 2 partial, 0 fail, 0 hallucinations (pass^2 0.8, at the bar).
Text: code constraints 10 of 10, the tersest lines, quality pass^2 0.2. Knowledge with cards 8 of 24, the most of the four models.
Footprint: 2.1 GB on disk, +2,898 MiB on the GPU, Pick p50 310–330 ms at 56 tokens/s, the full 304-call battery in 3.9 minutes.

**How 4.0, 4.1 and 4.2 differ** [V S4, S9, S10, S23; I]:

- *Architecture:* 4.0 bet on Mamba-2 hybrids and MoE (4 attention layers, ~64 MiB of KV at 8K); 4.1 went back to dense only, and
  IBM says the 4.1 8B matches or beats the 4.0 32B MoE (IFEval 87.06 vs 87.55; BFCL v3 68.27 vs 64.69).
- *Thinking:* 4.1 has none. 4.2 is the 4.1 base re-post-trained for reasoning (CoT and agentic SFT, multi-environment GRPO, RLHF),
  thinking on by default; `enable_thinking=false` ends the prompt with an empty `<think></think>`; `low_effort=True` appends
  "{reasoning effort: low}". Card budgets: 8,192 new tokens with thinking, 2,048 without.
- *Template:* 4.0/4.1 use `<|start_of_role|>…<|end_of_role|>` role tokens; 4.2 switches to ChatML with `<think>` blocks and
  Qwen3-Coder-style XML tool calls, a new BOS id and GGUF pre-tokenizer `granite-docling`.
- *Sampler:* 4.2's card says temperature 1.0 and top_p 0.95 "across all tasks and serving backends", and the official 4.2 GGUF embeds
  those values; llama.cpp applies GGUF-embedded samplers unless the request overrides them (PR #17120, merged 2025-11-25). An
  unpinned run therefore differs for 4.2 rows only; doc 47 §6.2's pin-everything rule is essential.
- *Controlled test:* 4.1-3B and 4.2-3B are both post-trained from Granite-4.1-3B-Base (4.2 adds an untied output head) and share the
  100,352-token vocabulary, so comparing 4.1 direct with 4.2 direct,
  low-effort and full thinking isolates the effect of post-training and thinking far more cleanly than Qwen against Gemma (§5, S7).

**Harness assets unique to Granite 4.1: task adapters (granitelib, Apache-2.0)** [V S12, S13, S21; I]:

| Adapter | Library | Output | Vendor numbers on the 4.1 3B | GGUF LoRA at the pinned revision | Plotroom use (proposal) |
| --- | --- | --- | --- | --- | --- |
| Query clarification | rag | JSON `{"clarification": question \| "CLEAR"}` | 96.1% accuracy (LoRA) vs 79.4% for prompted GPT-4o and 64.8% for the prompted 4.1 3B itself | Yes, 124,556,768 B | Trigger for the Pick `Q` escape and the Selector's `Clarify` |
| Answerability | rag | Answerable or not | — | Yes, 62,297,568 B | EXPLAIN guard: "the card does not answer this" |
| Hallucination detection | rag | Per-sentence support | — | Yes, 62,297,568 B | EXPLAIN check beside the claim matcher |
| Uncertainty | core | Score 0–9 → confidence 0.1 × score + 0.05 | MMLU: ECE 0.288 → 0.100, AUROC 0.629 → 0.787, Brier 0.301 → 0.185 | **No** (safetensors only; convert with llama.cpp's LoRA converter) | Confidence for a visible escalation offer, against letter margins |
| Requirement check | core | Yes/no per requirement | Balanced accuracy on IFEval requirements 0.815 (LoRA) / 0.843 (aLoRA) vs 0.51 prompted (0.51–0.62 across 3B–30B); on HelpSteer3 and InfoBench 0.65–0.72 | **No** (safetensors only) | Advisory next to the creative-text lints; far below code checks |

- Bases: granite-4.1-3b/8b/30b and granite-4.0-micro only; none for 4.2 or the Nano models. All English only [V S12, S13].
- llama-server switches adapters per request (`lora: [{id, scale}]`, with `--lora-init-without-apply` at start-up) [V S26]; activated
  LoRA (aLoRA), which reuses the base model's KV cache up to the invocation point, was merged in PR #15327 on 2025-09-05; release
  tag b6396 is that merge commit [V S21]. One resident 3B base could therefore serve Pick plus clarify, answerability and
  hallucination checks with no model swap [I].
- These are published vendor adapters, not Plotroom fine-tuning, so D027 item 6 does not block measuring them; its "upkeep per base
  model" concern still applies (each adapter is tied to one exact base, and a quantised base may shift its calibration) [I]. D023
  decision 5 keeps any of them in shadow or advisory use until it beats our baselines.

**Other IBM pieces** [V S14–S16; I]: Guardian 4.1 8B's harm and violence criteria would flag ordinary war content in a military
editor, so it must never gate content (D011); at most it is an optional T2 or cloud judge. Switch 4.1 runs in llama.cpp only as a
CPU, single-sequence proof of concept (b10342) [V S22]: watch. granite-io was archived on 2026-06-30 and folded into Mellea, whose
patterns (typed generative functions, instruct-validate-repair) Plotroom already follows; the one new idea is intrinsics as calibrated
verifiers.

**Licence** [V S1, S2, S11; I]: every Granite 4.x language model is Apache-2.0 and ungated. The repositories contain no LICENSE
file, only README front-matter, so D037's "the LICENSE file wins" has no file to read: the manifest should hash the README at the
pinned revision. The GGUF `general.license` field reads `apache-2.0` in the official 4.1-3B, 4.2-3B and 4.0-H-1B files (header read
by HTTP range request), so there is no card/GGUF mismatch of the kind that blocks Gemma 4 E4B (D023 amendment). IBM's Responsible Use
Guide is guidance, with no military field-of-use ban. Community derivatives (abliterated variants, GGUFs distilled from proprietary
model outputs) are never candidates.

**Verdict for Granite [I]:** 4.1 3B is the best-shaped Granite for Plotroom: non-thinking by construction, the fastest and smallest
measured model, the cleanest licence evidence, and the only one with calibrated verifier adapters. Its role is the low-VRAM GPU,
Apple and iGPU session model, and the anchor for the first sub-3B comparison. It is not a CPU-only default (§2.6). Below 3B, the
candidates are the 4.0 Nano 1B/H-1B (Pick probes) and 350M/H-350M (floor probes). Hybrid "H" models must be measured against their
dense twins, since IBM shipped dense Nano variants for runtimes without optimised hybrid support, "e.g. Llama.cpp" [V S8], and H-Tiny
generated no faster than a 3×-larger-active MoE on Vulkan in one report (an AMD iGPU on build 6700; the issue was closed on
2025-10-17 after Vulkan SSM work, so it may not hold on b11146) [V S25]. Never use any Granite for free engine knowledge,
span-heavy Fill or Polish/Russian translation.

### 2.5 Licences at small sizes (D037)

| Treatment | Models |
| --- | --- |
| Eligible for the recommended list after qualification (OSI licence, no field-of-use limit) | Granite 4.0 Nano, 4.1, 4.2 and the granitelib adapters (Apache-2.0); Qwen3-0.6B/1.7B (Apache-2.0); SmolLM2/3 (Apache-2.0); MiniCPM5 (Apache-2.0); EuroLLM and EuroMoE (Apache-2.0); GLiNER2 and gliner_multi-v2.1 (Apache-2.0); HHEM-2.1-Open (Apache-2.0); LettuceDetect, mDeBERTa-xnli, mmBERT (MIT); EuroBERT (Apache-2.0); Qwen3-Reranker and Embedding (Apache-2.0); decider (Apache-2.0) |
| Unclear, blocks a recommendation until resolved | Qwen3.5-0.8B and Qwen3.5-2B: both cards say "In light of its parameter scale, the intended use cases are prototyping, task-specific fine-tuning, and other research or development purposes" [V S34] |
| Custom only | Gemma 3 270M, FunctionGemma, Gemma 3 1B (Gemma terms, gated); LFM2/2.5 (revenue-gated); Falcon-H1-Tiny (Falcon licence with a use policy, not OSI); xLAM-2-1b, Hammer2.1 (CC-BY-NC); Tev1 (licence "being finalized") |
| Never recommended | Llama 3.2 1B/3B: the use policy bans "Military, warfare, nuclear industries or applications" [V S42] |

Evaluating a custom-only model is allowed (it installs as custom under D037); recommending it is not [I]. For a model whose use
policy bans military uses (Llama 3.2 here), D047 allows tests with the synthetic suites only, and the results are labelled and never
become a recommendation or a preset.

### 2.6 CPU speed and memory classes on the reference box

The reference box has a 4-core, 8-thread AVX2 CPU without AVX-512 or VNNI and dual-channel DDR4-2400 (38.4 GB/s peak) [V per doc 47
§2.7]. Method [I]: prompt processing ≈ 2 FLOPs per non-embedding parameter per token at an assumed 150–250 GFLOP/s effective;
generation ≈ 25 GB/s effective ÷ bytes read per token. Cross-checks: TinyLlama 1.1B reached pp512 ≈ 507 tokens/s at Q6_K on a
12-core desktop and ≈ 197 tokens/s at Q4_K_M on a laptop, with llamafile's own kernels [V S75].

| Tier | Prompt (tokens/s) | Generation (tokens/s) | One-pass letter Pick, ~200 uncached tokens | K = 3 permuted generation per decision (~430 prompt tokens with prefix reuse + 21 output) |
| --- | --- | --- | --- | --- |
| ≤ 150M | ≥ 800 | ≥ 150 | < 0.3 s | < 0.7 s |
| 150–400M | 250–500 | 60–120 | 0.4–0.8 s | 1.0–2.1 s |
| 0.4–1B | 150–280 | 30–60 | 0.7–1.3 s | 1.9–3.6 s |
| 1–2B | 55–100 | 18–35 | 2.0–3.6 s | 4.9–9 s |
| 2–3.4B | 25–45 | 11–18 | 4.4–8 s | 11–19 s |

All [I], unmeasured; §5 stage S2 measures them with `llama-bench -dev none`. Encoders (GLiNER2, rerankers, HHEM) take tens to hundreds
of milliseconds per call [I]. Consequences:

- **On CPU, the per-decision prompt, not the model, sets latency down to about 1B.** A product Pick capsule is ~2.3K tokens, ~1.19K
  uncached (doc 40 §1.1); on a 1B CPU model that is 12–22 s. A CPU prompt profile (doc 14 §7's compact local profile) must keep the
  per-decision part to about 200–400 tokens behind a frozen, cached stage prefix [I].
- **Doc 47's CPU Pick badge (p50 ≤ 3 s at `-dev none`)** points at ≤ 1B models with one-pass scoring on 4-core CPUs; 1.5–2B is
  borderline; K = 3 generation at 1B misses it. Granite 4.1 3B is not a CPU-only option [I].
- **Memory (Q4_K_M weights plus 8K KV, rounded up for compute buffers)** [I, arithmetic]: H-350M 0.3 GiB; 350M 0.5 GiB; H-1B
  1.1–1.3 GiB; 1B 1.8–2.0 GiB; Granite 4.1 3B 2.9 GiB; H-Tiny 4.3 GiB. At Q8_0 (the rule for ≤ 1B, §4.8) add about 0.15–0.7 GiB.

## 3. Techniques and their evidence

| # | Technique | What it buys | Evidence | Caveat at tiny sizes | Plotroom status |
| --- | --- | --- | --- | --- | --- |
| T1 | One-pass letter scoring | The whole option distribution, a margin and a confidence in one call; no decode tokens | Soft Self-Consistency matches plain self-consistency with half the samples [V S70]; our K = 3 voting gained +1.6 points mean for 3× calls [V, offline] | Letter binding varies by model family (T2) | Not built: `run.py` has no scoring mode (doc 47 §6.4) |
| T2 | Option-text (cloze) scoring as a fallback | Works when a model binds letters poorly | OLMES scores both formats and keeps the better; Pythia/OLMo/TinyLlama ~1B are near chance in letter format [V S53]; "symbol binding varies greatly by model" [V S55]; Qwen3-0.6B-Base MMLU 52.81 vs Gemma-3-1B-Base 26.26 (chance) [V S32] | One forced-decode call per option through llama-server | Not built |
| T3 | Permutation debiasing | Removes the prior on option-ID tokens | Reordering options moves accuracy 13–75% [V S58]; PriDe estimates the prior on 5% of samples for ×1.15 cost, +2.6 points on MMLU over 20 models; smaller models are more biased [V S57] | Doc 44 saw no first-option bias in 3–4B generation, but a letter readout exposes the prior directly | Menus already permuted per sample in `run.py` |
| T4 | Calibration | A confidence that means something | Contextual calibration up to +30 points on GPT-2/3 [V S59]; post-training hurts calibration [V S60]; verbalized confidence is not a tiny-model tool (AUROC 0.522 vs 0.605 white-box) [V S60]; decider ships fitted temperatures (0.8b: 1.03) [V S43] | Needs per-model, per-quant fitting on development menus | Not built |
| T5 | Conformal answer sets | A set with a guaranteed error rate | Conformal uncertainty tracks accuracy on LLM multiple choice [V S61] | Exchangeability breaks for new menu families; calibrate per `DecisionKind` | Proposal |
| T6 | Confidence cascades | Most calls stay small; hard ones go up | FrugalGPT up to 98% cost cut at GPT-4 accuracy; RouteLLM 14–26% strong-model calls on MT-Bench but 54% on MMLU; margin sampling was a consistently good deferral rule [V S62] | Escalation need depends on difficulty; correlated errors defeat it (T7) | Doctrine rejects silent escalation (§4.3) |
| T7 | Code filters before models | Removes the errors confidence cannot see | PW04 unanimous and wrong in 15 runs [V, offline]; more LM calls can hurt hard queries [V S63] | — | Doctrine (doc 25 rung 1) |
| T8 | Decomposition | Smaller decisions per call | Pairwise ranking lets a 20B model match GPT-4 listwise but needs O(N²) calls; setwise keeps most of it in one pass [V S64]; closed Fill fields 0.9–1.0 per field vs whole records 0.39–0.64 [V per doc 44] | Yes/no has its own biases (a lean to "no" in EN, DE and PL) [V S65] | Facet steps (doc 25 §6.2); per-field Fill proposed |
| T9 | Grammar-constrained decoding | Valid output at any size | Constrained Llama-3.2-1B content accuracy 0.986 vs 0.777 unconstrained 3B; Qwen3-0.6B 0.943; semantic failures and "hollow rescue" remain [V S67] | Misaligned subword constraints hurt [V S67] | In place (0 parse failures in 1,216 calls, doc 44) |
| T10 | Letter-only answers (no leading `why`) | One-pass readout; 20–40 fewer decode tokens (seconds on CPU) | CoT gains concentrate in math and logic; on MMLU direct answers match CoT unless an "=" appears [V S68]; every measured Pick run used a bare `{"choice": …}` and reached 0.90–0.97 [V per doc 44/46] | — | Tension with doc 25 §4.3 and doc 38 (a bounded `why` first, H5 untested) |
| T11 | Few exemplars, fixed order; short cards | Format and label space | Demonstrations teach format and label space, not label correctness [V S69]; example order swings results from near-SOTA to chance [V S69]; one card lifted a weak model from 1 to 16 of 24 (doc 30) | Tight context budgets | Cards chosen by code (D027 item 7) |
| T12 | Extraction instead of generation | Spans at encoder cost | GLiNER2 ≈ GPT-4o on zero-shot NER at 130–208 ms on CPU, weaker on classification [V S44] | English (multi: 6 languages); needs a non-llama.cpp runtime | Not built |
| T13 | Small checkers for EXPLAIN | Cheap faithfulness scores | HHEM ≈ GPT-4 on RAGTruth-QA; LettuceDetect-610M beats GPT-4.1-mini in 6 languages [V-vendor S47, S48] | A probability is never acceptance (doc 16 §3.3) | Not built |
| T14 | Task adapters | Format-matched decisions on a small base | LoRA Land: 4-bit LoRA +34 points over base, +10 over GPT-4 on average [V S71]; fine-tuned classifiers beat zero-shot GPT-4 at 200–500 labels [V S71]; a 400M encoder beats a 1B decoder on MNLI [V S50]; decider's held-out menus only 0.43–0.56 [V per doc 47] | Transfer; per-base upkeep; teacher terms | D027 item 6: no fine-tuning now (§4.9) |
| T15 | Speculative and n-gram decoding | Speed on long, input-grounded text | Prompt-lookup/n-gram decoding gives 2–4× on input-grounded output with identical greedy results [V S73]; drafter latency matters more than quality [V S73] | Useless for 7–17-token Picks; all Granite 4.x share vocab 100,352, so a Nano model might draft for 4.1 8B [I, untested] | Doc 47 §4.5 |

**llama-server mechanics for T1** [V S26, S27; I]:

- `/completion` with `n_predict` 1 and `n_probs` returns, per generated token, the top-N of a plain softmax over the raw logits
  (before the sampler chain and before the grammar) unless `post_sampling_probs` is set.
- The grammar is applied lazily: the sampler draws a token, checks only that token, and resamples with the full grammar mask only if
  it is rejected (`common/sampling.cpp`, lines 634–669 at b11146). Post-sampling probabilities are therefore not guaranteed to be
  grammar-masked; use the raw ones.
- Build the prompt with `/apply-template` (keeping the template's empty thought block for Gemma and Qwen), append the JSON prefix up to
  the answer slot (`{"choice": "`), and read the next token. Sum every vocabulary token whose text starts with a valid letter and
  continues validly (`A`, `A"`, `A"}`, leading-space variants), then renormalise over the valid letters plus `X` and `Q`.
- `n_probs` ≥ 20 does not guarantee all nine letters appear; bound a missing letter's mass by the smallest listed probability, or
  raise `n_probs` (cheap).
- llama-server returns no prompt-token log-probabilities, so option-text scoring (T2) needs one forced-decode call per option (a
  grammar that allows exactly that option's text), reading each generated token's raw log-probability, or in-process llama.cpp
  (doc 13). A code reading at b11146 says the forced path works: with `n_probs` ≥ 1 and `post_sampling_probs` off, the server turns
  off backend sampling and reports the sampled token's probability from a softmax over the full raw logits, whatever the grammar
  forced (`tools/server/server-context.cpp`, `populate_token_probs`; `server-common.cpp`, `get_token_probabilities`) [V by code
  reading; not run, confirm in stage S1].
- Unconstrained first-token probabilities can disagree with the text answer [V S56]; the grammar's letter-first slot removes that
  mismatch for our schema [I].

**Our own records, re-analysed offline** (docs 44/46 and preliminary doc 49 rows; 51 model × suite × condition runs; k = 3, a
permuted menu per sample, T 0.6; n = 30 menus each; in-sample) [V]:

- Majority-of-3 beat single-call accuracy by a mean of +1.6 points (range −2.2 to +6.7; 16 runs unchanged, 4 worse).
- Pick latency is prefill-bound: 4B on Vulkan, prompt p50 650–990 ms against decode 106–430 ms for 7–17 JSON tokens.
- Unanimity as a confidence: pooled over four 4B-class models on `pick-hard`, 20% of menus were not unanimous; their majority
  accuracy was 0.52 against 0.93 for unanimous menus, and escalating them would catch 62% (23 of 37) of majority errors. On `pick`
  (doc 44's four models): 12% not unanimous, 0.77 vs 0.96, 47% of errors caught.
- Cascade pairs (escalate non-unanimous menus to Gemma 4 E4B QAT; majority accuracy): Granite 4.1 3B `pick` none 0.933 → 0.967 at
  13% escalation;
  Qwen3.5-4B `pick-hard` none 0.833 → 0.967 at 27%; Qwen3-4B-Instruct-2507 0.767 → 0.967 at 33%; Spark-X2.5-4B 0.767 → 0.833 at 17%
  (it is 0.80 accurate even when unanimous). Escalating to a weaker "big" model can hurt: Gemma 4 E4B QAT's 1.000 on `pick-hard`
  fell to 0.900 when its non-unanimous menus went to Qwen3-30B-A3B-2507. Gemma's 1.000 makes the gains above optimistic [V; I].

**Adapters and the no-fine-tuning rule** [I on V S71, S72]: D027 item 6's four objections read differently for a *format* adapter
(pick a letter, pick a span) on a ≤ 1B OSI base. Data licensing is solvable with Plotroom's own generators, labelled by code or an OSI
teacher and filtered by the validators; weaker, cheaper teachers can even give better training data at fixed compute [V S71]. Upkeep
per profile falls away because facts stay in code-built menus; per-base retraining remains. Transfer is the real risk (decider 0.43–0.56
on held-out menus), but Plotroom's decision kinds are enumerable per release. "No help for cloud" is true, and irrelevant for the tier
that runs without cloud. Teacher terms matter: OpenAI, Anthropic and Gemini API terms bar using outputs or services to build competing
models; Gemma terms make a model trained on Gemma outputs a "Model Derivative"; Llama 3.1 imposes naming; the safe teachers are
OSI-licensed open weights run locally (Qwen, Granite, Gemma 4 and gpt-oss under Apache-2.0 per doc 47) [V S72]. Recommendation: keep
"no fine-tuning" for v1; record a post-v1 spike (doc 30 §2.7 already allows the revisit).

## 4. A tiny-first harness design (proposal)

### 4.1 Principles

1. **Code shrinks the decision.** Facts filter the menu (rung 1); catalogs split into facet steps of ≤ 7, and of ≤ 3 for sub-1B models
   (DG006 option C: the cap may be qualified per setup). A small model is never asked what code knows.
2. **One pass, whole distribution.** Local models expose logits; use them. A Pick is one prompt, one token, a distribution.
3. **Confidence routes, validators admit.** Calibrated probability decides whether to accept, re-ask, show alternatives, ask the user
   or offer a bigger model. It never admits content (doc 16 §4.2); the validators and the checker still do.
4. **Glass box.** The decision record shows the menu, the distribution, the stage that answered and why it escalated (D010).
5. **Mode matches training.** Non-thinking models in direct mode; never pay for thinking on a one-token Pick.
6. **No silent upward moves** (D023 decision 3). Anything that reaches another model is a binding the user made and can see.
7. **Per-model knobs are preset settings** (D048). The scoring mode, letter prior, fitted temperature, routing thresholds, menu cap
   and the leading `why` below are the kind of settings D048 puts in a per-model preset: tuned and accepted on held-out suites, bound
   to the exact file, runtime build and template, and never changing what code owns.

### 4.2 PICK: one-pass scoring with permutation debiasing and calibration

1. Code builds the menu (facts filtered, ≤ 7 options, or ≤ 3 per facet step for sub-1B setups), with `X` and `Q` always present.
2. The prompt is the frozen stage prefix, then state and request, then the **menu last**, so permuted re-asks reuse the prefix cache.
3. One call returns raw next-token probabilities; code aggregates them per letter (§3 mechanics) in the model's qualified mode
   (letters or option text, recorded per model by the Model Manager).
4. Code divides out the model's letter prior (estimated offline per model and menu size, PriDe-style or content-free) and applies the
   model's fitted temperature.
5. Decision rule (thresholds fitted per model and quant on our suites): high margin → proceed with the top option; low margin → re-ask
   once with a cyclically permuted menu and accept only a stable answer; still unstable or a conformal set of 2–3 → doc 25 §7.3's
   top-2/3 card or `Q`; a larger set, or `X` mass above threshold → `X` path or the visible escalation offer (§4.3).
6. Endpoints without log-probabilities (most cloud hosts) keep today's K permuted samples, now with adaptive stopping (DG021).

This replaces identical-prompt K = 3 voting wherever log-probabilities exist: one prompt instead of three, plus a confidence [I].

### 4.3 The confidence cascade (tiny local → mid local → cloud)

- **Order that makes sense [I on V]:** a tiny model on CPU (0.5–3 s), then the 3–4B session model on the GPU (0.8–1.5 s per escalated
  Pick), then cloud (0.7–3 s to the first chunk, doc 48). Offloaded 26–30B MoE (6–9 s per Pick, prefill-bound) belongs to Fill,
  Compose and text, not to the Pick ladder.
- **What escalation can do today** (doctrine as written: doc 21 §1.4 and §6.2 rule 3, doc 25 §3 principle 5 and §10.2, D023 decision
  3, DG022): go to (a) the user (`Q`, top-2 card), (b) code's best-scored default, or (c) one visible same-model re-run (DG022, open).
- **What needs an owner decision:** escalation to another model. Proposal: a visible, user-authored **two-stage role binding**
  ("router: tiny local model; when unsure: the bound session model or cloud setup"), set up once in the role-binding UI (D024), priced
  on the plan card, and recorded per step in the run record ("answered by stage 2 after margin 0.08"). Doc 40's D, E and G cost rows
  already model a 15% router → bound-model escalation that doctrine currently reads as user re-runs. **Candidate design-gap request**
  (not filed here): "Two-stage role binding with confidence escalation".
- **Evidence bar before proposing it as a default:** §5 rule R6 (non-inferior to the session model alone, ≥ 50% fewer session-model
  calls, no loss of `X` recall).
- **Where it helps** [I]: CPU-only machines (tiny → cloud); Preview on a GPU machine (tiny CPU model while the game holds the GPU;
  whether a sub-1 GB CPU model coexists with the game is [U]); free-tier users (tiny local stage in front of a rate-limited cloud).
  On an 8 GB GPU with the session model resident, the first stage should be the session model itself with one-pass scoring.

### 4.4 FILL: per-field decisions and extraction

- **Closed fields** (side, era, posture, time of day, archetype): one Pick per field over code-computed values; bounded ints binned
  into ≤ 7 bands. Qualified at 3–4B already (time of day 0.94–1.00, archetype 1.00) [V per doc 44/46]; 1–2B plausible [I].
- **Span fields** (place, target): code proposes candidates (island names, catalog and gazetteer matches, request n-grams) and a small
  model Picks one; or an extractor (GLiNER2 in English, gliner_multi or the LM path for Czech, Polish and Russian); or a grammar that
  allows only substrings of the request, so the quote check holds by construction. None of these proves the span is the *right* one
  (doc 44: Gemma quoted the finding code "CF01" as a place) [I].
- **Judgement fields** (`size`, `task` on meta requests): computed Picks with code-described bands, or a question card. No model size
  fixed them in doc 44 [V].
- **Whole record in one call:** only as a pre-fill the user confirms at 3–4B, or at 26–30B MoE / cloud (doc 47 §6.3 item 3).

### 4.5 EXPLAIN: selection below 3B, a small checker above

- **Tiny tier:** Pick the card sentence(s) that answer the finding (a Pick over sentences) and add the fix from a code template.
  Always correct as far as the card is.
- **3–4B tier:** a two-sentence paraphrase from the card (Qwen3.5-4B 20/20, Granite 4.1 3B 18/20; Gemma 4 E4B 13/20 with a
  hallucinated fix twice) [V per doc 44/46], scored by a 0.1–0.6B checker (HHEM-2.1-Open in English; LettuceDetect EuroBERT for DE,
  FR, IT, ES, PL; Granite's hallucination-detection adapter on a 4.1 base). If the check fails, show the card's own text with the
  computed finding, not a free retry.
- **Granite 4.1 variant to test:** pass the card through the template's `documents` path instead of the user turn.
- The checker is advisory; the checker on the fix and D027 item 7 still decide admission.

### 4.6 Short text: templates plus small paraphrase

- **Tiny tier:** templates, era word lists and a seeded phrase bank; the model Picks among variants and fills slots (doc 25 OQ5).
- **2–4B:** generated candidates behind code constraints (callsigns, grids, names, word caps, codepage), 2–3 per slot, which the user
  picks. With 2 samples, 9–10 of 10 slots had a usable candidate [V per doc 44].
- **Speed:** n-gram lookup decoding (`--spec-type ngram-*`) for input-grounded text such as card paraphrases and placeholder-heavy
  stringtable lines; its default 12-token lookup will not fire on short spans; the interaction with `json_schema` is unmeasured [U].

### 4.7 Big models only for creative drafting

Paragraph prose, dialogue, premises, Compose, Draft and scripts stay with ≥ 12B dense, 26B-A4B MoE (offload, L4) or cloud (DP-17 to
DP-20). Translation stays with ≥ 7B specialists or cloud until the translation suite (doc 47 §6.4) measures Hy-MT2-1.8B, EuroLLM-1.7B
and EuroMoE-2.6B-A0.6B (0.6B active, so 0.6B-class speed on CPU for bulk stringtable passes) [I].

### 4.8 Machine layouts and hygiene

| Machine | Session model | Tiny pieces (all `-dev none`) | Heavy steps |
| --- | --- | --- | --- |
| CPU-only, 8–16 GB RAM | A ≤ 1–2B model for Pick and closed Fill fields, one-pass scoring (if §5 passes) | Encoders if the runtime is accepted (§4.9) | Cloud, templates or No-AI |
| 4–6 GB GPU | Qwen3.5-2B, MiniCPM5-2B or Gemma 4 E2B; Granite 4.1 3B if it fits | Same | Cloud |
| 8 GB GPU | 3–4B session model (doc 44/46 defaults, or Granite 4.1 3B as the low-VRAM option) with one-pass scoring | Optional CPU checker; a tiny CPU stage during Preview | Cloud or visible MoE offload |
| 12 GB+ GPU | 8B-class (Granite 4.1 8B is a T2a model: Q4_K_M 5.35 GB plus 1,280 MiB KV at 8K) | CPU checker | Same model or cloud |
| Apple 16 GB | E4B-class model (doc 47 §4.6) or Granite 4.1 3B | CPU checker | Cloud |

Hygiene rules for tiny models [I on V]:

- **Q8_0 for anything of about 1B or less**, including the Granite Nano "1B" models (1.46–1.63B; 0.37–1.74 GB files); do not add Q4
  error to the smallest models; measure the quant pair where cheap, as doc 46 did.
- **Thinking always off and checked**, plus a `max_tokens` cap and the grammar. Qwen3, Qwen3.5 from 4B up, SmolLM3 and Granite 4.2
  think by default; Qwen3.5-0.8B and 2B default to non-thinking, and their cards warn of thinking loops in thinking mode; MiniCPM5's
  template leaves the choice to the model unless `enable_thinking` is sent [V S34, S37, S39, S4].
- **Short, byte-stable prompts**: stable prefix, then cards, then request and menu last (already so in `tools/local-qual`); decisive
  facts go into option labels. Keep `--min-p 0` as pinned in doc 47.
- **Template check per row**: JSON Schema through `/v1/chat/completions` can fail on Granite and Qwen role tokens while an equivalent
  GBNF works (issue #29006, open) [V S24]; keep a GBNF fallback and a dry run per Granite row.

### 4.9 Runtime gap: encoders (candidate design-gap request)

The generative tiny models, the rerankers (Qwen3-Reranker, bge-reranker-v2-m3) and the embedders run in the pinned llama-server
sidecar (D022). GLiNER2, HHEM (T5), LettuceDetect (ModernBERT/EuroBERT token classification) and mDeBERTa NLI do not; they need ONNX
Runtime (the Rust `ort` crate; `gliner2-rs`) or candle (`candle-transformers` has bert, debertav2, modernbert, granitemoehybrid, lfm2,
mamba2 and quantized_qwen3; `gliner2-candle` is a pure-candle GLiNER2 port) [V S45, S52]. HHEM also loads with `trust_remote_code`
in its reference Python path [V S47], which the product would never do. Adding an in-process encoder runtime is a D022-level decision
(a second supply chain, pinning, a qualification key per runtime). **Candidate design-gap request** (not filed here): "Encoder
runtime for non-generative helpers", with the alternative of using only llama.cpp-served rerankers and embedders for the
non-generative tier. Until decided, encoder arms are offline research only.

### 4.10 Free default (doc 50), rate limits (doc 52) and cloud-first screening (D044)

- **The local tiny tier is the one AI path with no account, no rate limit, no data-use terms and no cost** [I]. A plausible free,
  legal default is a hybrid bound per role (D024) and shown to the user: local and small for Pick, closed Fill fields, spans, checkers
  and escape detection (the high-frequency calls); free cloud for Compose and creative text (the low-frequency, heavy calls).
- **Arithmetic for doc 52** [I on V per doc 48 §6.0]: OpenRouter `:free` allows 20 requests a minute and 50 a day until $10 of
  credits has been bought (1,000 a day after).
  - A 30-minute session (60 calls) exceeds 50 a day on its own. With Pick, intent Fill and enum Fill local, about 12 cloud calls
    remain (the explanations): about four sessions a day.
  - If a tiny stage handled Picks and escalated 13–33% of them to free cloud (§4.3, needs the owner decision), each daily quota
    covers 3–7.7× more Pick decisions (50 a day becomes about 150–385).
  - A Standard campaign's ~428 text calls take about 9 days at 50 a day, or about 22 minutes at 20 RPM with 1,000 a day: campaign
    text needs a local ≥ 4B writer, a paid cheap endpoint (doc 40: about $0.15 per campaign on the cheapest row) or template text.
- **Granite as a free default** [I on V]: Granite 4.1 3B has the cleanest licence evidence of the measured models (Apache-2.0,
  ungated, GGUF licence field equal to the card, no military-use ban) and the smallest footprint. While Gemma 4 E4B QAT stays blocked by
  its licence-field mismatch, it is the strongest recommendable local default candidate for low-VRAM machines, still "spike-checked",
  not qualified (doc 21 §12.3). The one free hosted Granite is 4.0-H-Micro on Cloudflare Workers AI (10,000 neurons a day; a doc 44
  battery costs about 208) [V S29]: a free smoke-test route, not a user default (account, terms, D008).
- **D044, stated plainly: a proposed reading of its P5, for the owner to confirm.** D044 (recorded 2026-09-28) accepts the owner's
  rule: a model that could run on the reference PC is first tested in the cloud on a hosted copy of the same weights, and tried
  locally only if the cloud results are promising; the stated aim is to save time. Its protocol P1–P5 is a proposal (doc 50 §5), and
  P5 already sends models with no host, and questions that are local by nature (CPU-tier latency, memory fit), straight to a local
  run. For tiny models the cloud route mostly does not exist, and a local screen costs little time:
  1. Tiny models are rarely hosted. Of doc 47's sub-2B OSI CPU candidates, none is on OpenRouter; hosted ≤ 3B models are Hy-MT2-1.8B,
     LFM 2.5 2.6B (free tier; revenue-gated licence; reasoning mandatory), Ministral 3 3B, Granite 4.0-H-Micro and Granite 4.2-3B,
     plus Llama 3.2 1B/3B on Cloudflare [V S28–S30; V per doc 48]. Granite 4.1 is hosted nowhere found (IBM's launch post named
     hosts, so listings are volatile).
  2. Hosted copies run fp8 or bf16, so a cloud screen does not test the local Q8 or Q4 file.
  3. The letter-probability arms need top-N log-probabilities; OpenRouter lists `top_logprobs` on 150 of 458 models, as a union across
     providers, so support must be probed per endpoint [V S28].
  4. A CPU screen of a 0.2–2 GB file costs $0 and minutes to an hour, never touches the GPU, and runs where the product would run it.

  **Proposal (a reading of P5, not an exception to the rule):** models of about 2B parameters or less (Q8_0 file ≤ ~2 GB) with no
  same-weights host, which P5 already covers, and all encoders, rerankers, decision models and adapters, are screened locally on the
  CPU (`-dev none`), never concurrently with a timed job; the letter-probability arms (c)–(e) count as local by nature (items 2–3).
  Cloud-first screening stays the rule wherever a same-weights host exists (for Granite: 4.2-8B at CoreWeave with battery S before
  any 5.3 GB download of its GGUF; the non-thinking 4.1 8B has no host and goes local under P5).

  **The one hosted model in §5 is Granite 4.2-3B** (stage S7; DeepInfra via the HF router, precision undisclosed, no enforced
  schema). Under the
  accepted rule it is cloud-screened first unless the owner rules otherwise. Two options: (a) run a DeepInfra no-schema screen first
  (cents, inside HF's free credits; doc 50 §5.3 lists it as "local first; cloud no-schema arms optional"); or (b) the owner confirms
  that S7 is local by nature under P5, because it compares thinking modes under the local grammar, template and sampler pin against
  4.1-3B, which has no host, and its file is probably on disk already from doc 47's pin at the same commit, so a cloud screen saves
  no download. Until the owner answers, S7 runs only after (a) or with the answer recorded.

### 4.11 What the Model Manager ships and recommends

| Artifact kind | Ships in the installer | Recommended list | Pin | Runtime |
| --- | --- | --- | --- | --- |
| Generative GGUF (session or tiny) | Never (D023 decision 1) | OSI licence, no field-of-use limit, qualified per step kind (D037) | Repo, commit, file, bytes, SHA-256, licence file or README hash, GGUF `general.license` | llama-server sidecar |
| Reranker / embedder GGUF | Never | Same rule; shadow or semantic tier only until it beats the baselines | Same | llama-server (one mode per server) |
| LoRA / aLoRA adapter GGUF (granitelib, or a future Plotroom adapter) | Never | Same rule, plus the base file's SHA-256; English-only adapters labelled | Adapter pin plus base pin | llama-server `--lora` |
| Encoder (safetensors/ONNX) | Never | Blocked until the runtime decision (§4.9) | Same | Undecided |

Presentation [I]: badges per step kind (doc 44 §5.3), including a **CPU Pick** badge (§5 rule R3) and the qualified **scoring mode**
(letters or option text); Q8_0 as the default file for ≤ 1B rows; Granite rows hash the README because no LICENSE file exists;
Qwen3.5-0.8B and 2B stay custom until their use statement is resolved. Downloads remain the user's action in Settings, never an agent tool
(D022).

## 5. The experiment plan

Not run. It runs only after doc 49's measurement job has finished and the CPU and GPU are idle. Tooling is built on a scratch copy of
`tools/local-qual`, never in the tree while doc 49 uses it. A machine-readable version (pins, arms, stop rules) is kept with the run
tooling and is to be committed next to the results.

### 5.1 Stages

| Stage | What | Hardware | Est. time [I] |
| --- | --- | --- | --- |
| S0 | Preconditions: doc 49 finished; suites frozen by hash; each file's SHA-256 checked; one dry run per template (json_schema vs GBNF, issue #29006); thinking off confirmed (`thinking_chars` = 0) | — | 30 min |
| S1 | Build instruments (§5.3); smoke-test each on one model with `--limit 3` | CPU | tooling time |
| S2 | Speed gate: `llama-bench -dev none -t 4 -p 512 -n 128` per CPU file; hybrids against dense twins | CPU, idle | 30–45 min |
| S3 | Floor ladder, generation arms (a) and (b): `pick`, `pick-hard`, `fill` at `none`; `pick-hard` at `cards` only for sizes that hold easy Picks. Descending order, stop rule R2. Reuse doc 49 CPU rows with the same pin and flags | CPU | 2.5–5 h |
| S4 | Scoring arms (c) letters, (d) letters + prior, (e) option text on every S3 model, plus GPU references (Gemma 4 E4B QAT, Qwen3-4B-Instruct-2507, Granite 4.1 3B on Vulkan) | CPU + GPU | 2.5–4 h CPU, 20 min GPU |
| S5 | Cascade replay (f), offline over S3/S4 records and stored session-model records; threshold sweep | none | minutes |
| S6 | Why-first vs letter-only (g): Granite 4.1 3B (GPU) and the best S3 CPU model, `pick-hard` both conditions | GPU + CPU | 30–45 min |
| S7 | Granite same-base thinking test: 4.1-3B direct vs 4.2-3B direct / low effort / full thinking (512-token cap); `pick-hard` plus the waypoint and trigger menus of `pick`; top_p pinned | GPU | 1–1.5 h |
| S8 | Granite intrinsics on 4.1-3B: uncertainty (converted) vs letter margin and unanimity; query clarification on planted `Q`/`X` and ambiguous items; answerability and the `documents` path on `explain` | GPU | 30–45 min + conversion |
| S9 | Non-generative shadow arms: Qwen3-Reranker-0.6B and bge-reranker-v2-m3 as Selectors on `pick`/`pick-hard`; decider-0.8b through arm (c) at T 1.03; GLiNER2 on Fill spans; HHEM and LettuceDetect re-scoring stored `explain` outputs against the grades (offline research tooling) | CPU | 30–60 min |

Total: roughly 6–11 hours of CPU (the sum of the stage ranges above) and 2–3 hours of GPU, mostly unattended, and about 20 GB of
downloads (30 GB with the optional files), less whatever doc 49 already holds at the same commits [I]. Stage S7 also waits on the
D044 point in §4.10 (Granite 4.2-3B is the one hosted model in the plan).

### 5.2 Models (pins in Appendix A)

| Rung | Model | Files | Placement | Why |
| --- | --- | --- | --- | --- |
| Ceiling | Granite 4.1 3B | Official Q4_K_M | GPU (Vulkan) and `-dev none` | The measured floor; CPU cost of a 3B |
| 1 | Qwen3.5-2B | Q4_K_M (doc 47 pin) | `-dev none` | Best CZ/PL in the tier; doc 44's family; recommendation blocked like the 0.8B (use statement) |
| 2 | Qwen3-1.7B | Official Q8_0 | `-dev none` | Strongest public single-call evidence under 2B |
| 3 | Granite 4.0 1B and H-1B | Official Q8_0 and Q4_K_M each | `-dev none` | Dense vs hybrid; quant pair |
| 4 | Qwen3.5-0.8B | Q8_0 (Unsloth) | `-dev none` | Evaluation only; recommendation blocked (use statement) |
| 5 | Qwen3-0.6B | Official Q8_0 | `-dev none` | High BFCL irrelevance |
| 6 | Granite 4.0 350M and H-350M | Official Q8_0 | `-dev none` | Floor probe |
| S7 | Granite 4.2-3B | Official Q4_K_M | GPU | Same base, thinking on; hosted on DeepInfra, so D044 applies (§4.10) |
| References | Gemma 4 E4B QAT; Qwen3-4B-Instruct-2507 | Doc 47 pins | GPU | Session models for the cascade |
| Helpers | Qwen3-Reranker-0.6B (ggml-org Q8_0); bge-reranker-v2-m3 (community Q8_0); decider-0.8b (community Q8_0); granitelib adapters; GLiNER2; HHEM-2.1-Open; LettuceDetect (EN ModernBERT; PL EuroBERT) | Appendix A | CPU | Shadow and checker arms |

### 5.3 Instruments to build first (scratch copy only)

1. **Letter mode** (`--score-mode letters`): `/apply-template` + JSON prefix + `/completion` with `n_predict` 1, `n_probs` 50,
   temperature 0; record the raw distribution, the per-letter aggregate, margin, entropy and the missing-mass bound.
2. **Option-text mode** (`--score-mode text`): one grammar-forced decode per option, summed and length-normalised log-probabilities;
   `n_probs` ≥ 1 is required for any per-token probability; a code reading says the forced token's raw probability is returned (§3),
   so a smoke run only has to confirm it.
3. **Priors:** content-free menus ("N/A" request) per model and menu size; PriDe-style cyclic permutations on 5 menus per suite.
4. **Calibration in `score.py`:** temperature fit by NLL on one suite, ECE (10 adaptive bins), Brier and AUROC on the other
   (cross-fit `pick` ↔ `pick-hard`); conformal set sizes at α = 0.1.
5. **Cascade replay:** margin, set-size and unanimity rules over stored records; report accuracy, pass^3, escalation rate, `X` recall
   and false `X`.
6. **Frozen new suites:** `pick-facet` (the same requests with menus split by code into ≤ 3-option facet steps) and `fill-fields`
   (each Fill record's closed fields as separate Picks, spans as single-field quote-constrained Fills).
7. **Think mode `low`** for Granite 4.2 (`enable_thinking` true, `low_effort` true) with the grammar starting after `</think>`.
8. **Adapter plumbing:** `--lora … --lora-init-without-apply` and per-request `lora`; granitelib-core adapters converted to GGUF LoRA
   against the exact base file.
9. **Offline encoder scorers** in a research virtual environment (GLiNER2, HHEM, LettuceDetect), with the HHEM repository's remote
   code read at the pinned commit before use.

### 5.4 Arms

| Arm | What | K | Notes |
| --- | --- | --- | --- |
| (a) | Generation, K = 1 | 1 | Read from arm (b)'s first sample per item: no extra calls |
| (b) | Generation, K = 3, permuted menus (current protocol) | 3 | T 0.6, sampler pinned as doc 47 |
| (c) | One-pass letter probabilities, plus one permuted re-ask when the margin is low | 1–2 | Greedy |
| (d) | (c) with the letter prior divided out and the fitted temperature | 1–2 | Cross-fit |
| (e) | Option-text scoring | 1 per option | Where the runtime allows |
| (f) | Cascade: tiny model → session model, sweep of margin / set-size thresholds | — | Offline replay |
| (g) | Why-first vs letter-only | 3 | `run.py --why` vs arm (c) |

Metrics: accuracy per call, majority, pass^3, per-category accuracy, `X` recall on planted escapes, false-`X` rate, `Q` rate, ECE,
Brier, AUROC, conformal set sizes, escalation rate, calls per decision, p50/p90 latency per decision at `-dev none` on an idle machine,
prompt and generation tokens/s, `cache_n`, resident memory. Fill: per-field accuracy and pass^3, quote check, validators. Controls on
every instrument: random-valid, always-first, always-ask, no-model. Note: a greedy one-pass answer is deterministic, so its pass^3
equals its accuracy; compare it with arm (b) on accuracy and on majority, and with the permuted re-ask for stability.

### 5.5 Decision rules (pre-registered)

- **R1 (floor per step kind):** a size *holds* PICK when `pick` and `pick-hard` pass^3 ≥ 0.8 (or arm-(c/d) accuracy ≥ 0.8 with a
  stable permuted re-ask) in both conditions, `X` is right on every planted escape and no legitimate request gets `X`. It holds *easy
  PICK* when the mood, cutscene, no-code and routing categories reach 0.8 with the same escape rules. The floor is the smallest size
  that holds, reported per arm.
- **R2 (stop descending):** after two consecutive sizes with `pick` pass^3 < 0.5 at `none`, or any size failing the `X` must-pass in
  every arm.
- **R3 (CPU Pick badge candidate):** R1 plus p50 ≤ 3 s per decision at `-dev none` on the idle reference box (doc 47 §6.3 item 5).
- **R4 (one-pass replaces K = 3 for a model):** arm (c/d) accuracy within doc 44's 10-point noise rule of arm (b) majority on
  `pick-hard` in both conditions, held-out ECE ≤ 0.10, and ≤ 50% of arm (b)'s per-decision latency.
- **R5 (scoring mode):** keep option text only if it beats letters by more than 3 points on `pick-hard`; otherwise letters (one call).
  Record the mode per model.
- **R6 (cascade proposal supported):** the tiny → session cascade is non-inferior to the session model alone on `pick-hard` pass^3
  (10-point rule, both conditions), cuts session-model calls by ≥ 50%, and never lowers `X` recall or raises false `X`. Otherwise
  the tiny stage is proposed only for CPU-only machines.
- **R7 (the leading `why`):** if letter-only is within 5 points of why-first on `pick-hard` accuracy in both conditions, the tiny
  tiers drop the `why` (a candidate design-gap request against doc 25 §4.3 / doc 38); if why-first wins by ≥ 10 points, keep it at
  ≥ 3B and retest at 1B.
- **R8 (thinking hypothesis):** supported if 4.2-3B low effort or full thinking beats 4.1-3B direct by ≥ 10 points `pick-hard`
  pass^3 in both conditions; the added latency is reported; refuted if within noise.
- **R9 (intrinsics):** the uncertainty adapter becomes a proposed routing signal only if its AUROC for `pick-hard` correctness beats
  both the letter margin and K = 3 unanimity by ≥ 0.05 on the same items (English only).
- **R10 (non-generative Selectors):** results are recorded only; an advisory slot needs doc 16 §5's bar and D023 decision 5.
- **R11 (EXPLAIN checker):** advisory candidate if AUROC ≥ 0.80 against the graders' hallucination and partial labels while flagging
  ≤ 10% of graded passes.
- **R12 (spans):** GLiNER2 is a candidate if it reaches ≥ 0.8 on both span fields where the session model does not, pending §4.9.
- **R13:** nothing here is doc 21 §12.3 qualification; results are spike verdicts, and public docs get aggregates only.

## Open questions

1. **D044 P5 reading (owner):** confirm that models of about 2B or less with no same-weights host, and all encoders, rerankers,
   decision models, adapters and letter-probability arms, are screened locally on the CPU; and say whether stage S7's Granite 4.2-3B
   run is local by nature or needs a DeepInfra no-schema screen first (§4.10).
2. **Cross-model escalation (owner):** may a user-authored two-stage role binding escalate from a tiny model to the session model or
   cloud, visibly and priced, or does escalation stay limited to the user, code's default and a same-model re-run (§4.3)?
3. **Encoder runtime (technical, D022-level):** ONNX Runtime or candle for GLiNER2, HHEM and LettuceDetect, or llama.cpp-served helpers
   only (§4.9)?
4. **The leading `why` (technical):** does doc 25 §4.3's bounded `why` stay for tiny tiers, given the one-pass readout (§5 rule R7)?
5. **Qwen3.5-0.8B and 2B use statement (owner, D037):** binding field-of-use limit or not? (The same line is on both cards.)
6. **Format adapters post-v1 (owner, D027 item 6; D048 decision 3):** D048 chose adapting the harness over training models; may a
   post-v1 spike still train a letter/span adapter on a ≤ 1B OSI base from Plotroom's own synthetic data, shipped only as a separate
   pinned download with provenance?
7. **Preview coexistence:** can a sub-1 GB CPU model stay resident while the game runs (D018), without hurting the game's frame
   rate? [U]
8. **Menu cap per setup (DG006):** should sub-1B setups qualify at ≤ 3 options per facet step?
9. **Granite adapters in the Model Manager:** is an English-only verifier adapter acceptable as an advisory helper in a multilingual
   product, and how is it badged?
10. **Hybrids on Vulkan:** are Granite H models faster or slower than their dense twins on the shipped build (§5 stage S2)? [U]

## Findings that affect sibling docs (reported, not fixed)

1. `docs/research/14-model-selection.md` line 308 says "LFM2.5 lists Polish and Russian but not Czech"; the current cards list none of
   the three (1.2B-Instruct: EN, AR, ZH, FR, DE, JA, KO, ES; the 350M adds PT; the 230M adds IT and PT) [V S36].
2. Doc 14 frames Granite 4.2-3B as the narrow router with thinking off and quotes BFCL v4 52.4; the 4.2 card describes a reasoning
   model with thinking on by default, and its agentic numbers are presumably in thinking mode. The non-thinking Granite is 4.1 3B
   [V S4; I].
3. `docs/research/data/slm-test-shortlist.json` describes Granite 4.2-3B as having no thinking mode. `run.py`'s default
   `--think-mode false` sends `enable_thinking=false`, which the 4.2 template honours, so direct-mode results stay valid; the records
   should still be checked for `thinking_chars` = 0 and the note fixed [V S4].
4. Doc 47 §5 lists "Apache-2.0 with a use statement → Eligible; show the statement" (Qwen3.5-2B, Olmo 3), which conflicts with D037's
   rule that an unclear use statement blocks a recommendation until resolved.
5. `docs/research/data/slm-candidates.csv`, Granite 4.1 3B row: context "unknown" (the config says 131,072), size from Ollama (the
   official Q4_K_M is 2,099,501,664 B), and the date is the repository's creation (2026-04-06), not the release (2026-04-29) [V S1, S2].
6. Qwen3-1.7B is absent from docs 14 and 47, although its public single-call evidence is the strongest of any Apache-2.0 model under
   2B [V S31].
7. Doc 47 line 123's remark that Granite 4.0 uses the same role tokens as Granite 3.1 holds for 4.0 and 4.1, not for 4.2 (ChatML)
   [V S4].
8. `docs/research/14-model-selection.md` line 193 says Qwen3.5 thinks by default; that holds from 4B up, while the 0.8B and 2B cards
   and templates default to non-thinking (doc 47's Qwen3.5-2B row already says so) [V S34].

## Sources

Repository docs: `docs/research/13`, `14` (§2–§9), `16` (§2–§5), `19` (§8), `21` (§1.4, §3, §4, §6, §11, §12.3), `25` (§2–§7, §9–§11),
`26` (§8.2), `29` (§6.2), `30` (§2.7, §4), `31` (§9), `32` (§5.3), `33` (§6–§7), `37` (§9), `38` (§3, §8), `39` (§8), `40` (§1, §4,
§5), `41` (§7), `43` (§7), `44`, `46`, `47`, `48` (§1, §6.0, §7); `docs/research/data/local-qualification.csv`,
`runtime-quant-comparison.csv`, `slm-candidates.csv`, `slm-test-shortlist.json`, `cloud-candidates.csv`; doc 50 (§5);
`docs/decisions/D008`, `D010`, `D011`, `D018`, `D022`, `D023`, `D024`, `D027`, `D037`, `D044`, `D045`, `D047`, `D048`;
`docs/design-gap-requests/DG006`, `DG015`, `DG021`, `DG022`; `tools/local-qual` (`run.py`, `prompts.py`, `score.py`). Offline
re-analysis: stored call records of docs 44 and 46 and the in-progress doc 49 run (git-ignored), re-scored without new model calls.

- **[S1]** Granite 4.1 3B card, config, chat template, generation config: <https://huggingface.co/ibm-granite/granite-4.1-3b>,
  <https://huggingface.co/ibm-granite/granite-4.1-3b/raw/main/config.json>
- **[S2]** Official Granite GGUF trees (commits and SHA-256 via the HF API, 2026-09-28):
  <https://huggingface.co/api/models/ibm-granite/granite-4.1-3b-GGUF/tree/main>, and the same path for `granite-4.1-8b-GGUF`,
  `granite-4.2-3b-GGUF`, `granite-4.0-h-350m-GGUF`, `granite-4.0-350m-GGUF`, `granite-4.0-1b-GGUF`, `granite-4.0-h-1b-GGUF`,
  `granite-4.0-h-micro-GGUF`; GGUF headers read by HTTP range request from the pinned `resolve/<commit>/` URLs
- **[S3]** Granite 4.1 8B and 30B: <https://huggingface.co/ibm-granite/granite-4.1-8b>, <https://huggingface.co/ibm-granite/granite-4.1-30b>
- **[S4]** Granite 4.2: <https://huggingface.co/ibm-granite/granite-4.2-3b> (README, chat template, config),
  <https://huggingface.co/ibm-granite/granite-4.2-8b>
- **[S5]** Granite 4.0 Nano: <https://huggingface.co/ibm-granite/granite-4.0-h-1b> (350M–H-1B benchmark table),
  <https://huggingface.co/ibm-granite/granite-4.0-h-350m>, <https://huggingface.co/ibm-granite/granite-4.0-350m>,
  <https://huggingface.co/ibm-granite/granite-4.0-1b>
- **[S6]** Granite 4.0 Micro family: <https://huggingface.co/ibm-granite/granite-4.0-h-micro>, <https://huggingface.co/ibm-granite/granite-4.0-micro>,
  <https://huggingface.co/ibm-granite/granite-4.0-h-tiny>
- **[S7]** IBM Granite organisation listing: <https://huggingface.co/api/models?author=ibm-granite&sort=createdAt&direction=-1&limit=120>
- **[S8]** Granite 4 Nano blog: <https://huggingface.co/blog/ibm-granite/granite-4-nano>
- **[S9]** Granite 4.1: <https://huggingface.co/blog/ibm-granite/granite-4-1>, <https://research.ibm.com/blog/granite-4-1-ai-foundation-models>
- **[S10]** Granite 4.2: <https://huggingface.co/blog/ibm-granite/granite-4-2>, <https://www.ibm.com/granite/docs/models/granite4-2>
- **[S11]** IBM Granite Responsible Use Guide: <https://www.ibm.com/granite/docs/resources/responsible-use-guide.pdf>
- **[S12]** granitelib-core-r1.0 (uncertainty, requirement-check): <https://huggingface.co/ibm-granite/granitelib-core-r1.0>,
  <https://huggingface.co/ibm-granite/granitelib-core-r1.0/blob/main/uncertainty/README.md>,
  <https://huggingface.co/ibm-granite/granitelib-core-r1.0/blob/main/requirement-check/README.md>
- **[S13]** granitelib-rag-r1.0: <https://huggingface.co/ibm-granite/granitelib-rag-r1.0>,
  <https://huggingface.co/ibm-granite/granitelib-rag-r1.0/blob/main/query_clarification/README.md>,
  <https://huggingface.co/api/models/ibm-granite/granitelib-rag-r1.0/tree/main?recursive=true>
- **[S14]** Granite Guardian 4.1 8B: <https://huggingface.co/ibm-granite/granite-guardian-4.1-8b>
- **[S15]** Granite Switch and SWASH: <https://huggingface.co/ibm-granite/granite-switch-4.1-3b-preview>,
  <https://huggingface.co/ibm-granite/granite-swash-2b>, <https://huggingface.co/ibm-granite/granite-swash-3b-a600m>
- **[S16]** Mellea and granite-io: <https://github.com/generative-computing/mellea>, <https://github.com/ibm-granite/granite-io>
- **[S17]** Unsloth Granite guides and GGUF: <https://unsloth.ai/docs/models/ibm-granite-4.1>,
  <https://unsloth.ai/docs/models/tutorials/ibm-granite-4.0>, <https://huggingface.co/api/models/unsloth/granite-4.1-3b-GGUF/tree/main>
- **[S18]** Ollama Granite tags: <https://ollama.com/ibm/granite4.1/tags>, <https://ollama.com/library/granite4/tags>, <https://ollama.com/ibm/granite4.2>
- **[S19]** Artificial Analysis: <https://artificialanalysis.ai/models/granite-4-1-3b>, <https://artificialanalysis.ai/models/granite-4-2-3b>
- **[S20]** llama.cpp "Granite Four" (granitehybrid): <https://github.com/ggml-org/llama.cpp/pull/13550>
- **[S21]** llama.cpp activated LoRA: <https://github.com/ggml-org/llama.cpp/issues/15212>, <https://github.com/ggml-org/llama.cpp/pull/15327>
- **[S22]** llama.cpp granite-switch: <https://github.com/ggml-org/llama.cpp/releases/tag/b10342>
- **[S23]** GGUF-embedded sampler defaults: <https://github.com/ggml-org/llama.cpp/pull/17120>
- **[S24]** json_schema with role tokens: <https://github.com/ggml-org/llama.cpp/issues/29006>
- **[S25]** Granite H-Tiny on Vulkan: <https://github.com/ggml-org/llama.cpp/issues/16454>
- **[S26]** llama-server README (`n_probs`, `post_sampling_probs`, `lora`, `--lora-init-without-apply`, `--rerank`, router mode,
  `--spec-type`): <https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md>
- **[S27]** Lazy grammar sampling: <https://github.com/ggml-org/llama.cpp/blob/b11146/common/sampling.cpp> (lines 634–669); token
  probabilities: <https://github.com/ggml-org/llama.cpp/blob/b11146/tools/server/server-context.cpp> (`populate_token_probs`),
  <https://github.com/ggml-org/llama.cpp/blob/b11146/tools/server/server-common.cpp> (`get_token_probabilities`)
- **[S28]** OpenRouter: <https://openrouter.ai/api/v1/models> (snapshot 2026-09-27: 458 models, 150 with `top_logprobs`),
  <https://openrouter.ai/api/v1/models/ibm-granite/granite-4.2-8b/endpoints>, <https://openrouter.ai/api/v1/models/ibm-granite/granite-4.0-h-micro/endpoints>,
  <https://openrouter.ai/docs/api-reference/parameters>, <https://openrouter.ai/docs/api-reference/limits>
- **[S29]** Cloudflare Workers AI: <https://developers.cloudflare.com/workers-ai/models/granite-4.0-h-micro/>,
  <https://developers.cloudflare.com/workers-ai/platform/pricing/>, <https://developers.cloudflare.com/workers-ai/platform/limits/>
- **[S30]** Hugging Face router model list: <https://router.huggingface.co/v1/models>
- **[S31]** BFCL V4 data: <https://gorilla.cs.berkeley.edu/data_overall.csv>
- **[S32]** Qwen3 technical report: <https://arxiv.org/abs/2505.09388>
- **[S33]** Qwen GGUFs: <https://huggingface.co/api/models/Qwen/Qwen3-0.6B-GGUF/tree/main>,
  <https://huggingface.co/api/models/Qwen/Qwen3-1.7B-GGUF/tree/main>, <https://huggingface.co/api/models/unsloth/Qwen3.5-0.8B-GGUF/tree/main>,
  <https://huggingface.co/api/models/unsloth/Qwen3.5-2B-GGUF/tree/main>
- **[S34]** Qwen3.5-0.8B and 2B cards and chat templates: <https://huggingface.co/Qwen/Qwen3.5-0.8B>,
  <https://huggingface.co/Qwen/Qwen3.5-2B>, <https://huggingface.co/Qwen/Qwen3.5-4B> (thinking default for comparison)
- **[S35]** Gemma 3 270M, FunctionGemma, Gemma terms: <https://huggingface.co/google/gemma-3-270m>,
  <https://huggingface.co/google/functiongemma-270m-it>, <https://ai.google.dev/gemma/prohibited_use_policy>, <https://ai.google.dev/gemma/terms>
- **[S36]** LFM2.5: <https://huggingface.co/LiquidAI/LFM2.5-350M>, <https://huggingface.co/LiquidAI/LFM2.5-230M>,
  <https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct>
- **[S37]** SmolLM: <https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct>, <https://huggingface.co/HuggingFaceTB/SmolLM3-3B>
- **[S38]** Falcon-H1-Tiny: <https://huggingface.co/tiiuae/Falcon-H1-Tiny-Tool-Calling-90M>, <https://huggingface.co/tiiuae/Falcon-H1-Tiny-90M-Instruct>,
  <https://tiiuae-tiny-h1-blogpost.hf.space/>, <https://falconllm.tii.ae/acceptable-use-policy.html>
- **[S39]** Watch list: <https://huggingface.co/openbmb/MiniCPM5-1B>, <https://huggingface.co/openbmb/MiniCPM5-2B>,
  <https://huggingface.co/IFM/K2-Horizon-0.9B>
- **[S40]** EuroLLM and EuroMoE: <https://huggingface.co/utter-project/EuroLLM-1.7B-Instruct>,
  <https://huggingface.co/utter-project/EuroMoE-2.6B-A0.6B-Instruct-2512>
- **[S41]** Decision-format fine-tunes: <https://huggingface.co/togethercomputer/Tev1-0.8B-experimental>,
  <https://huggingface.co/chaoliangUNSW/Jev-Style-Qwen3.5-2B-Decision-v2-GGUF>
- **[S42]** Llama 3.2 use policy: <https://github.com/meta-llama/llama-models/blob/main/models/llama3_2/USE_POLICY.md>
- **[S43]** decider-0.8b: <https://huggingface.co/Mapika/decider-0.8b> (`decider_config.json`: temperature 1.03),
  <https://huggingface.co/mradermacher/decider-0.8b-GGUF>
- **[S44]** GLiNER2: <https://arxiv.org/abs/2507.18546>, <https://huggingface.co/fastino/gliner2-base-v1>, <https://huggingface.co/fastino/gliner2-multi-v1>
- **[S45]** GLiNER and ports: <https://arxiv.org/abs/2311.08526>, <https://huggingface.co/urchade/gliner_multi-v2.1>,
  <https://github.com/codesoda/gliner2-rs>, <https://github.com/mrorigo/gliner2-candle>, <https://crates.io/crates/gline-rs/0.9.4>
- **[S46]** BTZSC zero-shot classification benchmark: <https://arxiv.org/abs/2603.11991>
- **[S47]** HHEM-2.1-Open: <https://huggingface.co/vectara/hallucination_evaluation_model>
- **[S48]** LettuceDetect: <https://github.com/krlabsorg/lettucedetect>, <https://huggingface.co/blog/adaamko/lettucedetect-multilingual>,
  <https://huggingface.co/EuroBERT/EuroBERT-210m>
- **[S49]** mDeBERTa-v3-base-xnli: <https://huggingface.co/MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7>
- **[S50]** Encoders vs decoders and mmBERT: <https://arxiv.org/abs/2507.11412>, <https://huggingface.co/api/models?search=mmBERT&author=jhu-clsp&limit=20>
- **[S51]** Rerankers: <https://huggingface.co/Qwen/Qwen3-Reranker-0.6B>, <https://huggingface.co/ggml-org/Qwen3-Reranker-0.6B-Q8_0-GGUF>,
  <https://huggingface.co/gpustack/bge-reranker-v2-m3-GGUF>
- **[S52]** candle-transformers models: <https://github.com/huggingface/candle/tree/main/candle-transformers/src/models>
- **[S53]** OLMES: <https://arxiv.org/abs/2406.08446>
- **[S54]** SmolLM2 paper: <https://arxiv.org/abs/2502.02737>
- **[S55]** Multiple-choice symbol binding: <https://arxiv.org/abs/2210.12353>
- **[S56]** First-token vs text answers: <https://arxiv.org/abs/2402.14499>, <https://arxiv.org/abs/2404.08382>
- **[S57]** PriDe: <https://arxiv.org/abs/2309.03882>
- **[S58]** Option-order sensitivity: <https://arxiv.org/abs/2308.11483>
- **[S59]** Calibration: <https://arxiv.org/abs/2102.09690>, <https://arxiv.org/abs/2309.17249>
- **[S60]** Confidence: <https://arxiv.org/abs/2305.14975>, <https://arxiv.org/abs/2306.13063>, <https://arxiv.org/abs/2303.08774>
- **[S61]** Conformal prediction for LLM multiple choice: <https://arxiv.org/abs/2305.18404>
- **[S62]** Cascades: <https://arxiv.org/abs/2305.05176>, <https://lmsys.org/blog/2024-07-01-routellm/>, <https://arxiv.org/abs/2406.18665>,
  <https://arxiv.org/abs/2404.14618>, <https://arxiv.org/abs/2310.12963>, <https://arxiv.org/abs/2310.03094>, <https://arxiv.org/abs/2402.04513>,
  <https://arxiv.org/abs/2407.18370>, <https://arxiv.org/abs/2310.13561>, <https://arxiv.org/abs/2404.10136>
- **[S63]** More calls and correlated errors: <https://arxiv.org/abs/2403.02419>, <https://arxiv.org/abs/2608.25761>
- **[S64]** Pairwise and setwise ranking: <https://arxiv.org/abs/2306.17563>, <https://arxiv.org/abs/2310.09497>
- **[S65]** Yes/no bias: <https://aclanthology.org/2025.findings-emnlp.607/>, <https://arxiv.org/html/2607.05552>
- **[S66]** Distilling decomposition: <https://arxiv.org/abs/2402.15000>
- **[S67]** Constrained decoding: <https://arxiv.org/html/2609.23742v1>, <https://arxiv.org/abs/2403.06988>
- **[S68]** When chain-of-thought helps: <https://arxiv.org/abs/2409.12183>
- **[S69]** In-context learning: <https://arxiv.org/abs/2202.12837>, <https://arxiv.org/abs/2104.08786>, <https://arxiv.org/abs/2303.13824>,
  <https://arxiv.org/abs/2401.11624>
- **[S70]** Soft Self-Consistency: <https://arxiv.org/abs/2402.13212>
- **[S71]** Adapters and distillation: <https://arxiv.org/abs/2405.00732>, <https://arxiv.org/abs/2305.02301>, <https://arxiv.org/abs/2406.08660>,
  <https://arxiv.org/abs/2304.09542>, <https://arxiv.org/abs/2408.16737>,
  <https://unsloth.ai/docs/get-started/fine-tuning-for-beginners/unsloth-requirements>
- **[S72]** Teacher-output terms (not legal advice): <https://www.anthropic.com/legal/commercial-terms>, <https://ai.google.dev/gemini-api/terms>,
  <https://ai.google.dev/gemma/terms>, <https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct/blob/main/LICENSE>;
  <https://openai.com/policies/services-agreement/> (returned 403; clause taken from search results)
- **[S73]** Speculative and lookup decoding: <https://arxiv.org/abs/2211.17192>, <https://arxiv.org/abs/2402.01528>,
  <https://github.com/apoorvumang/prompt-lookup-decoding>, <https://arxiv.org/abs/2304.04487>
- **[S74]** Response-time limits: <https://www.nngroup.com/articles/response-times-3-important-limits/> (confirmed from a search snippet)
- **[S75]** CPU prompt-processing cross-check: <https://github.com/mozilla-ai/llamafile/discussions/450>

## Appendix A: pinned files for §5

Repository commit and LFS SHA-256 as returned by the Hugging Face API on 2026-09-28 [V]. Download from
`https://huggingface.co/<repo>/resolve/<commit>/<file>` and check the SHA-256 before starting a server. Doc 47 Appendix A pins the
reference session models (Gemma 4 E4B QAT, Qwen3-4B-Instruct-2507) and Qwen3.5-2B Q4_K_M.

| Repo @ commit | File | Bytes | SHA-256 |
| --- | --- | --- | --- |
| `ibm-granite/granite-4.1-3b-GGUF` @ `ab47014810` | `granite-4.1-3b-Q4_K_M.gguf` | 2,099,501,664 | `662b0626cd58f443baea23559b469df6576a81d349649c59413b36a9fb32eb29` |
| same | `granite-4.1-3b-Q8_0.gguf` | 3,619,691,104 | `c31f09b9fd19bc51440f100f54fe5ac3d5deb26ef79ec93c38e4a14873c42a80` |
| `ibm-granite/granite-4.2-3b-GGUF` @ `c40945d71c` | `granite-4.2-3b-Q4_K_M.gguf` | 2,244,011,552 | `e0406663965846ae22a403456eb826ccce5f450840491f71952f18a7cb78e7d5` |
| `unsloth/Qwen3.5-2B-GGUF` @ `f6d5376be1` | `Qwen3.5-2B-Q4_K_M.gguf` | 1,280,835,840 | `aaf42c8b7c3cab2bf3d69c355048d4a0ee9973d48f16c731c0520ee914699223` |
| same | `Qwen3.5-2B-Q8_0.gguf` | 2,012,012,800 | `1b04acba824817554f4ce23639bc8495ff70453b8fcb047900c731521021f2c1` |
| `Qwen/Qwen3-1.7B-GGUF` @ `90862c4b9d` | `Qwen3-1.7B-Q8_0.gguf` | 1,834,426,016 | `061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a` |
| `ibm-granite/granite-4.0-1b-GGUF` @ `b27c2fe3f2` | `granite-4.0-1b-Q8_0.gguf` | 1,737,791,232 | `0660c20c3d3d3672b90f0468f62dc128a82a6e3ee2ec05d310d242969be06140` |
| same | `granite-4.0-1b-Q4_K_M.gguf` | 1,023,645,440 | `22ec0f9cc99a90185312de3c882c84e7bd6789bdd050389844380a01a831d7f1` |
| `ibm-granite/granite-4.0-h-1b-GGUF` @ `c2cb1972f5` | `granite-4.0-h-1b-Q8_0.gguf` | 1,558,926,560 | `f29248184ca766350e56e6d161c2a637ad302a6d595e15d4a62cd58327a0ac0e` |
| same | `granite-4.0-h-1b-Q4_K_M.gguf` | 901,162,208 | `da3d737121a96f3c9a316685212376257a7f167b74380855666dd488d6af3bcb` |
| `unsloth/Qwen3.5-0.8B-GGUF` @ `6ab461498e` | `Qwen3.5-0.8B-Q8_0.gguf` | 811,843,840 | `0ad885ffd4bb022fc4f0d33a3308fa108ef8613159d3b3a67e23abca056b7a6c` |
| `Qwen/Qwen3-0.6B-GGUF` @ `23749fefcc` | `Qwen3-0.6B-Q8_0.gguf` | 639,446,688 | `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031` |
| `ibm-granite/granite-4.0-h-350m-GGUF` @ `a864f823cc` | `granite-4.0-h-350m-Q8_0.gguf` | 366,195,616 | `c7d9873640dc303b6773dcc44e72e5bdf533e1c95ca8421e6191fbff5c94c942` |
| `ibm-granite/granite-4.0-350m-GGUF` @ `b8208a86a5` | `granite-4.0-350m-Q8_0.gguf` | 378,138,016 | `9595dafb4ed15aa02512c8ea26188744192a6f09530eae0a2747bd3ada96cd36` |
| Helper: `ggml-org/Qwen3-Reranker-0.6B-Q8_0-GGUF` @ `a02f48bb4f` | `qwen3-reranker-0.6b-q8_0.gguf` | 639,153,184 | `22c9979ce4fbcdc5acdc310c6641c32797eff1aa980b8f7a2db8a8ea23429a48` |
| Helper (community): `gpustack/bge-reranker-v2-m3-GGUF` @ `3093af03b1` | `bge-reranker-v2-m3-Q8_0.gguf` | 635,676,416 | `a43c7c9b11a4c1517e5bf95151960e1621d1b72f7a493364b01e386cf1aaa1d3` |
| Helper (community): `mradermacher/decider-0.8b-GGUF` @ `001df41ddc` | `decider-0.8b.Q8_0.gguf` | 811,844,032 | `2665d08c1052b4e01dabcb08771d25579f6776f7066355e4a0ccc5f74e32d4a2` |
| Adapter: `ibm-granite/granitelib-rag-r1.0` @ `2f0b2c79c6` | `query_clarification/granite4.1_3b/lora/Lora-bf16.gguf` | 124,556,768 | `58c0620e0868129281f8a711acc8a2fc22f404ceb3a05ac2f3687ea9580e1ce1` |
| same | `answerability/granite4.1_3b/lora/Lora-bf16.gguf` | 62,297,568 | `b05931f36a2ae6c515e317985ae073a9bdab024e338c485e5400680b7d06d17c` |
| same | `hallucination_detection/granite4.1_3b/lora/Lora-bf16.gguf` | 62,297,568 | `950e7a246564d9eaebc242ed5142b9c27d67b0e9f518f12d27182ee412d5a7b4` |
| Adapter (convert first): `ibm-granite/granitelib-core-r1.0` @ `d0a2a96a4c` | `uncertainty/granite-4.1-3b/lora/adapter_model.safetensors` | 83,929,080 | `e60d8b28441d8ac203baea8235716b0386501b127702d3855d12e13ed7ad148b` |
| same | `uncertainty/granite-4.1-3b/alora/adapter_model.safetensors` | 83,929,080 | `36f0309fcaba4c28e9deb0c5d49680dee1c9cbbec407abbb74e5760f64786a6c` |
| same | `requirement-check/granite-4.1-3b/lora/adapter_model.safetensors` | 83,929,368 | `10b87f10058af1423b06b83b4dd2358b45dc3d41ca3eeeae8649815e0c31acbb` |
| Encoder (offline): `fastino/gliner2-base-v1` @ `9585099e70` | `model.safetensors` | 833,938,108 | `845fc4bd93c525b86124c58ab4f56c9eacf8587953086b14c501fab25957c007` |
| Encoder (offline): `vectara/hallucination_evaluation_model` @ `8e4a2e6e96` | `model.safetensors` | 438,535,352 | `634de18a38cf1e991c1acd0f7a9e0d30f7ea187fba42bb4798f862d3edd31e72` |
| Encoder (offline): `KRLabsOrg/lettucedect-base-modernbert-en-v1` @ `bbd77832f5` | `model.safetensors` | 598,439,784 | `bbd64cc0ce5886bcb35a595622851f8b79bc2ece3284d254a7f08b32817a266e` |
| Encoder (offline, PL): `KRLabsOrg/lettucedect-210m-eurobert-pl-v1` @ `68a2e1b98a` | `model.safetensors` | 847,082,592 | `1ffaebc4e0d89d4935a453a899c8865f3686e8d4712320d0f983209bdfd7b47a` |
| Optional encoder: `fastino/gliner2-multi-v1` @ `330385515e` | `model.safetensors` | 1,228,421,964 | `7d982cda9e478d98933854a976f777e75732bce6d9fa54c3ee243562b804b627` |
| Optional encoder (PL): `KRLabsOrg/lettucedect-610m-eurobert-pl-v1` @ `5d3047afc7` | `model.safetensors` | 2,431,535,128 | `1f369e2cd75562e96565f2882e2a33d18cc7386c0878d71abfaf7fd640a07825` |
| Optional encoder: `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` @ `b5113eb38a` | `model.safetensors` | 557,652,046 | `7c8e29f1115986d032e92b0fbaa0bdef1062a46f658b08705f237c05014a8541` |

Pin the full 40-character commits in any download script; the short forms above are for reading.

## Verification notes

### 2026-09-28, author checks at write-up

- **Verified here:** every Appendix A commit, size and SHA-256 (HF API, 2026-09-28); that granitelib-core ships no GGUF at the pinned
  revision while granitelib-rag ships GGUF LoRA files for the 4.1 3B; that HHEM-2.1-Open is English only (the cross-lingual HHEM-2.3 is
  commercial) and loads with remote code; decider-0.8b's fitted temperature (1.03); the offline vote and cascade numbers in §3, re-run
  from the stored records; the `run.py` flags (`--why`, `--k`, `--think-mode`, no scoring mode) and suite sizes (`pick` 30,
  `pick-hard` 30, `fill` 12, `explain` 10, `text` 10).
- **Taken from sibling docs or the research inputs, not re-fetched:** vendor benchmark numbers, the Granite GGUF header readings, the
  OpenRouter and Cloudflare listings, and the paper numbers in §3.
- **Not verified:** any model run; every CPU speed and latency in §2.6 and §5; whether llama-server returns raw log-probabilities for
  grammar-forced tokens; aLoRA's first release (reported as b6396 from a search summary); whether Granite 4.2's `granite-docling`
  pre-tokenizer loads on b11146 (probably, since it predates that build).
- **Preliminary inputs:** the doc 49 rows (Qwen3-4B-Instruct-2507, Spark-X2.5-4B, Qwen3-30B-A3B-Instruct-2507, Gemma 4 26B-A4B) are
  from an unfinished run and may change.

### 2026-09-28, review

No model was run for the review; everything below is HTTP metadata, file headers, cards and source code.

- **Pins [V]:** all 32 pins in the machine-readable plan and all rows of Appendix A match the HF `paths-info` API at the pinned
  commit (LFS SHA-256 and size), and every `resolve/<commit>/` URL is well formed. Four plan pins that Appendix A lacked (the
  uncertainty aLoRA, GLiNER2 multi, LettuceDetect PL-610M, mDeBERTa) were added. The unpinned family-table sizes (4.0 Micro, H-Micro,
  H-Tiny, 4.1 8B, 4.2 3B and 8B) were read from the repositories' trees and filled in.
- **Licences [V]:** HF card metadata at the current revision: Apache-2.0 and ungated for every Granite 4.x model, GGUF and granitelib
  repository, the Qwen3 and Qwen3.5 rows, the rerankers, decider-0.8b, GLiNER2, HHEM, EuroBERT, EuroLLM, EuroMoE, SmolLM2/3, MiniCPM5
  and K2-Horizon; MIT for LettuceDetect and mDeBERTa; `other` for Falcon-H1-Tiny (falcon-llm-license) and LFM2.5 (lfm1.0); Gemma and
  Llama 3.2 gated; CC-BY-NC-4.0 for xLAM-2-1b and Hammer2.1; no licence field for Tev1. GGUF headers read by range request:
  `general.license = apache-2.0` in the official 4.1-3B, 4.2-3B, 4.0-H-1B, 4.0-1B, H-350M and 350M files.
- **Fixed, licence:** Qwen3.5-2B's card carries the same intended-use line as the 0.8B, so §2.5 now lists it as unclear under D037
  (it had been listed as eligible, contradicting the plan and finding 4).
- **Fixed, thinking modes:** Qwen3.5-0.8B and 2B default to non-thinking (card and template), unlike Qwen3.5-4B and up; MiniCPM5's
  template sends no think prefix unless `enable_thinking` is set. §2.3, §4.8 and a new sibling finding (8) say so.
- **Fixed, D044:** the draft said no D044 record existed; D044 was recorded on 2026-09-28 (rule accepted, protocol P1–P5 proposed,
  P5 already sending no-host models local). The exception is reframed as a proposed reading of P5, and stage S7's Granite 4.2-3B, the
  one hosted model in the plan, is flagged with two options for the owner. D045, D047 and D048 are now referenced.
- **Fixed, evidence wording:** "qualified in the doc 44 spike" → "met the spike bar"; Granite 4.1 3B is second on card-grounded
  explanations (18/20 against Qwen3.5-4B's 20/20), not the best; `pick-hard` pass^3 at 4B spans 0.67–0.83 in doc 46 (Gemma 4 E4B
  0.77–0.83), not 0.63–0.70; the cascade figures are majority accuracy; the 4.2 card does not state the mode of its benchmark table;
  the query-clarification baseline is now the prompted 4.1 3B itself (64.8%); the requirement-check figures are the IFEval column;
  IBM's adapters also cover 4.0 Micro; the 4.2 family has a 30B; the CPU total is 6–11 hours (the sum of the stage ranges), not 6–9.
- **Verified, llama.cpp [V]:** PR #17120 (model-embedded samplers) merged 2025-11-25, and the official 4.2-3B GGUF embeds
  `general.sampling.temp` 1.0 and `top_p` 0.95; PR #15327 (aLoRA) merged 2025-09-05, and tag b6396 is its merge commit; issue #29006
  is open (Granite 3.1 / Qwen3 role tokens); b10342's Granite Switch backend is a CPU proof of concept; issue #16454 is closed; at
  b11146 `granite-docling` is a known pre-tokenizer, `--reasoning on|off|auto`, `--reasoning-budget`, `--spec-type ngram-*`,
  `--lora-init-without-apply` and `--no-mmproj` exist, `common/sampling.cpp` lines 634–669 are the lazy grammar check, and the
  `n_probs` path without `post_sampling_probs` returns a softmax over the raw logits (code reading).
- **Verified, quotes and numbers [V]:** the IBM Research blog's non-thinking quote (verbatim; the HF blog words it differently); 15T
  tokens in five phases, 4.1M SFT samples, four sequential RL stages; the 4.1 3B and 4.0 Micro/Nano benchmark rows; the 4.1
  `documents` system text; 4.0's default system prompt and its absence in 4.1; 4.2's empty system block, thinking modes, budgets and
  sampler sentence; the granitelib numbers; the BFCL V4 rows (FC mode); the BTZSC figures; HHEM's RAGTruth-QA and CPU-speed lines;
  the Llama 3.2 military clause; the OpenRouter snapshot (458 models, 150 with `top_logprobs`; 4.2-8B at CoreWeave with structured
  outputs and log-probabilities); Granite 4.2 3B/8B/30B on DeepInfra via the HF router without structured output; every KV-cache
  figure against the configs.
- **Still not verified:** any model run or speed; the Falcon-H1-Tiny BFCL figures; the §3 paper numbers other than BTZSC; the
  doc 49 rows.
