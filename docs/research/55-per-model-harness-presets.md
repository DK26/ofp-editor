# Per-model harness presets: adapt the harness to the model

Research doc 55 for Plotroom (`ofp-editor`). Research date: 2026-09-28. Audience: contributors and LLM coding agents. This file is
meant to be read on its own.
Question answered (owner, 2026-09-28, lightly edited): "Figure out the best harness settings, configurations and parameters for each
small local model and ship pre-built presets that make the most of each, in the most optimised way. For Qwen3.5-4B a harness that
plays to its advantages; for Granite 4.1 a different or slightly different one. Rather than one general harness, and rather than
training models for our harness, adjust the harness towards what the models are already trained for."

**Status: draft — tuning runs pending.** No model was loaded or run for this doc. Measurements come from docs 44 and 46, from an
offline re-analysis of their stored call records made for this doc (no new calls), and from rows of the unfinished doc 49 run, marked
**preliminary, doc 49 pending**. Every preset value, knob range, decision rule and budget below is a proposal [I]. Staged with the
run tooling outside the tree, to land with the first tuning run (§3.3, §4): four draft harness presets at version 0.2.0 (the default,
Qwen3.5-4B, Gemma 4 E4B QAT, Granite 4.1 3B), each with a knob ledger; the draft JSON Schema (draft 2); a standard-library checker; a
split declaration; a tuning plan with per-stage call and time budgets; a six-item dispatch draft suite; and two new pools, 60 Pick
menus and 36 Fill records, each split half for tuning and half as an interim held-out check (§4.1).
**Epistemic legend** (doc 53's): **[V]** verified against the cited primary source, or re-derived from our own stored records;
**[V-vendor]** a vendor's statement about its own model; **[V per doc N]** taken from a sibling doc; **[I]** our inference or
proposal; **[U]** unknown.
**Relation to sibling docs.** Doc 21 sets the doctrine (step shapes, qualification, and §4's intent fill → dispatch); docs 25, 38 and
40 the capsule, workflows and token economy; docs 44 and 46 the measurements; doc 47 the candidates and the pin-everything protocol;
doc 48 the cloud controls and the uplift instrument; doc 50 cloud-first screening; doc 53 tiny models, one-pass scoring and cascades.
Doc 49 (the measured shortlist) is in progress. Doc 51 (model-native harnesses) reached the tree while this doc was drafted: it
supplies the *profile* of probed facts that every harness preset must respect and the native-convention knobs; §1.3 reads the
vendors' cards directly and is reconciled with doc 51 there. [D048](../decisions/D048-per-model-harness-presets.md) (owner, accepted
2026-09-28) records the owner's direction quoted above and leaves the knob catalogue, file format and tuning protocol to this doc;
D021, D022, D023, D024, D027, D037, D044, D045 and D048 govern, and this doc changes no decision.
**Names.** A **harness preset** is the data that says *how* Plotroom asks one exact model setup for each step kind. Always write the
full term: "preset" alone already means effort presets (doc 21 §13.3), free-model presets (D045), mood presets (doc 41) and
component presets (doc 34). Step kinds follow doc 53: PICK, FILL, COMPOSE, creative text (doc 47's DRAFT) and EXPLAIN. Draft keeps
its ChangeSet meaning and is out of scope for local harness presets. Doc 14 §7's "prompt profile" (`LocalCompact`, `CloudRich`),
chosen by a capability probe, is this idea's ancestor; a harness preset replaces it.
**Hygiene.** Public sources only; no game content; no local paths. Model answers appear only as short spans from our own synthetic
suites.

## TL;DR

- **One harness does not fit these models equally, and each misfit is specific** [V, offline re-analysis of docs 44/46 records]:
  - **Qwen3.5-4B** never applied the "same End number means AND" trigger rule: HT03, 0 of 24 samples across four builds and runtimes,
    with and without the card that states it. It missed the near-fit escape HM04 in 12 of 24 samples, and in Fill it paraphrased
    spans or mixed languages. It also wrote the best card-grounded explanations (20 of 20 and 19 of 20; docs 44, 46).
  - **Gemma 4 E4B** caught 22 of 24 near-fit escapes and every Fill span on llama.cpp, but chose PerCampaign for a roll that must
    depend on the previous mission (HV01, 7 of 24). Under llama-server's grammar it pads every JSON answer (16 output tokens per pick
    against 7), and it invented the same fix for one finding on both runtimes.
  - **Granite 4.1 3B** was the fastest (310 ms per pick on Ollama) and tersest. Cards changed almost nothing on Pick (82 of 90
    calls chose the same letter), and in Fill it left named places empty (6 of 6 samples on two requests).
- **A harness preset changes how we ask, never what code owns.** It may change answer format, reasoning, sampler, schema mode,
  prompt layout (by named ids only), decomposition among authored alternatives, scoring mode, K and repair *below* the effort
  ceiling, and cascade thresholds. It never changes facts, menus, escapes, validators, admission, tools, trust labels, role
  bindings, data destinations or shape grants, and it carries no prompt text (§1.4).
- **The same card helps one model and hurts another on the same menu.** With cards, Qwen went from 1 to 6 of 12 on HK01 but from 7
  to 5 on HM04 and from 10 to 5 on HW03; Gemma went from 5 to 8 on HT03 and from 5 to 2 on HV01 [V, descriptive; n = 12 per cell].
  So card policy is a knob per (model, decision kind), not a global rule.
- **Vendor conventions are candidates, not defaults.** Qwen's recommended non-thinking sampler includes presence penalty 1.5. On
  llama-server that penalty cost end-of-menu answers (41 → 34 of 50 on the same file), and the Ollama build that ships it put Chinese
  characters into 2 of 36 Fill records. That is the "language mixing" Qwen's own card warns about [V; V-vendor]. D022 already pins
  Pick and Fill penalties to neutral.
- **The preset file** is versioned, data-only JSON. It is bound to the model repo, commit, file, bytes and SHA-256, the runtime build
  and backend, the chat-template hash and the quant. It is written as a diff of the default preset, per step kind, with provenance
  (tuning runs, held-out scores) and per-step badges (D037). It ships with the Model Manager's manifest under D008, is shown in the
  editor, and can be overridden; an override is a "custom" preset, unqualified until checked (§3).
- **The tuning protocol** has five parts (§4):
  - Today's suites plus the tune halves of two new pools are the tuning split: every item has been read item by item, or written in
    the same pass as the analysis, so none of them is held-out evidence.
  - The pools' other halves (30 menus, 18 records) give one interim held-out look per model: an early warning, never a reason to
    call a harness preset tuned.
  - A fresh sealed held-out set (120 Pick menus, 48 Fill records, 24 dispatch items, 20 findings, 20 text slots) is written by
    someone else and frozen by hash first; prompt fragments, exemplar banks, thresholds and per-kind decision tables are frozen
    before it is opened.
  - Candidates come from vendor conventions and failure analysis, and are searched family by family, by sequential halving or one
    paired round, with item-level tests.
  - Rules PR1–PR9 are pre-registered, with minimum effects (+10 points Pick pass^3 at 120 menus).
- **Cost** (the staged plan's arithmetic from measured p50s): about 2.6 hours of GPU time for Qwen3.5-4B, 1.9 for Gemma 4 E4B and
  1.0 for Granite 4.1 3B on the reference card, 5.6 in all, unattended, plus grading. The three first targets have no cheap
  same-weights host, so they are tuned locally (D044 P5); for hosted models, only precision-insensitive knob families may be
  pre-screened in the cloud, for cents [I].
- **Not fine-tuning** (D027 item 6 stands), **not one harness either:** the default preset *is* the general harness and the fallback
  for every unknown or custom model. A knob that wins for all three first targets moves into the default (§5).
- **First targets** (§6), each with its hypotheses (the draft harness presets start from them; the measured controls stay arms):
  - Qwen3.5-4B: extract-then-dispatch for rule-bearing menus, an escape pre-check, verbatim span grammar, and the card's own
    `answer` field and non-thinking sampler without its presence penalty.
  - Gemma 4 E4B: a compact grammar, a code-chosen fix in EXPLAIN, dispatch for roll-scope and waypoint menus, and the vendor
    sampler for creative text (only an arm for Pick).
  - Granite 4.1 3B: a first llama.cpp baseline, greedy decoding with one-pass scoring, cards through its `documents` path (cards
    off on Pick as an efficiency arm), IBM's JSON system sentence under a compact grammar, span candidates from code, and style
    exemplars for creative text.
  - The tiny tier follows doc 53 (facet cap 3 at 1B or less, one-pass scoring, compact CPU layout).
- **Ten design-gap candidates** are listed, not filed (§7): chiefly, the harness preset must join the model-setup identity and the
  qualification key (DG012), and Pick needs authored alternative decompositions.

## 1. Why presets

### 1.1 What we measured: the same harness, different failures

All rows use the same suites, seeds, option permutations and schemas. Qwen and Gemma ran on llama.cpp b11146 (Vulkan) and on Ollama;
Granite ran on Ollama only (doc 44). "Arms" are builds × runtimes of one model family: Qwen3.5-4B Q4_K_M and UD-Q4_K_XL on llama.cpp,
Q4_K_M on llama.cpp with Ollama's sampler, and the Ollama library build; Gemma 4 E4B Q4_K_M, UD-Q4_K_XL and QAT on llama.cpp, and QAT
on Ollama. A count "of 24" pools four arms × two conditions × three samples. Arms of one family are near-copies of one model, so
their samples are not independent: the item counts below describe, they do not test [V; I].

| | Qwen3.5-4B | Gemma 4 E4B (QAT unless noted) | Granite 4.1 3B |
| --- | --- | --- | --- |
| `pick` pass^3, none / cards | 0.867 / 0.967 (llama.cpp) [V per doc 46] | 0.967 / 0.967 [V per doc 46] | 0.833 / 0.867 (Ollama) [V per doc 44] |
| `pick-hard` pass^3, none / cards | 0.700 / 0.767, below doc 44's 0.8 bar [V per doc 46] | 0.833 / 0.867 [V per doc 46] | Not run |
| Rule-bearing menus | HT03 (same End number = AND): 0 of 24, all conditions; HV01 (roll scope): 6 of 24 [V] | HT03: 13 of 24; HV01: 7 of 24, and 0 of 12 for the two non-QAT files, which chose PerCampaign every time [V] | PW04 (TR UNLOAD): 0 of 6, like nearly every 3–4B build [V per docs 44, 46] |
| Planted escapes | Near-fit HM04: 12 of 24; far HA03 and HR04: 46 of 48 [V] | HM04: 22 of 24; far: 48 of 48 [V] | 3 of 3 off-scope on `pick`, 0 false `X` in 87 [V per doc 44] |
| Lure-shaped wrong picks | 17–24% of wrong real-option picks share more request words with the pick than with the answer (base rate of such distractors: 15%); HK01's Cutscene ("content can vary by state") echoes "what happened decides" without sharing words: 1 of 12 without cards [V] | 35–47%, mostly HV01 and HW03 [V] | — |
| End-of-menu answers (letter G or `X`) on `pick-hard` | 41 of 50 without a presence penalty; 34 of 50 with 1.5, same file and runtime; 34 of 50 on Ollama [V] | 45–47 of 50 on every arm [V] | — |
| Fill, all fields right per call | 0.639 (llama.cpp) [V per doc 46] | 0.861 [V per doc 46] | 0.389 (Ollama) [V per doc 44] |
| Fill span errors (of 36 span answers per arm) | 4 on Q4_K_M: 2 reworded target spans ("enemy traffic on coast road near Saint Arel") and 2 finding codes filed as places; on Ollama, 2 of 36 records carried Chinese characters inside the target span [V] | 0 on each llama.cpp arm [V] | 6 empty places where the request named one (F02, F04, every sample); 3 reworded targets [V] |
| Judgement field `size` | 16 of 24 [V] | 19 of 24 [V] | 14 of 24 [V] |
| EXPLAIN with card | 20 of 20 (Ollama), 19 of 20 (llama.cpp) passes [V per docs 44, 46] | 13 of 20, the same invented fix for E10 on both runtimes [V per doc 46] | 18 of 20, 0 hallucinations [V per doc 44] |
| Creative text, code checks | 0.90 (Ollama), 1.00 (llama.cpp) [V per docs 44, 46] | 1.00 (Ollama), 0.95 (llama.cpp) [V per doc 46] | 1.00, tersest (6.4 words mean) [V per doc 44] |
| Output tokens per pick | 7.0 [V] | 16.3 under llama-server's grammar (pretty-printed JSON), 7.0 on Ollama [V] | 7.0 [V] |
| Pick p50 | 1,046 ms (llama.cpp), 650 ms (Ollama) [V per docs 44, 46] | 1,126 ms / 510 ms [V per docs 44, 46] | 310 ms (Ollama) [V per doc 44] |

**The card effect changes sign by model and item** (samples right out of 12 per family, pooled over the four arms, `pick-hard`) [V,
descriptive]:

| Item (what decides it) | Qwen3.5-4B none → cards | Gemma 4 E4B none → cards |
| --- | --- | --- |
| HT03 (End #1 on both triggers = AND) | 0 → 0 | 5 → 8 |
| HK01 (state decides → Decision node) | 1 → 6 | 12 → 12 |
| HM04 (vehicle respawn is not a wave-1 module → `X`) | 7 → 5 | 10 → 12 |
| HW03 (leave once an enemy is identified → SENTRY) | 10 → 5 | 7 → 4 |
| HV01 (drawn at the previous mission's end, kept on retry → PerTurn) | 1 → 5 | 5 → 2 |

**Preliminary doc 49 rows point the same way** [V, preliminary, doc 49 pending]. Spark-X2.5-4B answered `X` on 26 of the 162
`pick-hard` calls whose menu had a fitting option, while catching 18 of 18 planted escapes. Qwen3-4B-Instruct-2507 caught 7 of 18
planted escapes and wrote verb phrases instead of the target in Fill (0 of 12 target spans right). Qwen3-30B-A3B-2507 reached only
0.700 / 0.800 pass^3 on `pick-hard`, the 4B class (doc 53 §1.4). Only Gemma 4 26B-A4B solved PW04 (5 of 6).

**Reading** [I]: the three models do not differ in one "quality" dimension. Each has a failure *class*:

- **Qwen3.5-4B:** rules that contradict the everyday word, near-fit escapes, and span copying under a penalty.
- **Gemma 4 E4B:** option texts that echo the request, fix invention, and format overhead.
- **Granite 4.1 3B:** omission in extraction; rich context barely used on Pick.

A single general harness has to pick one fix for all three and gets the others wrong. Doc 21 §3.3 already adapts step *shapes* to a
model's qualification; a harness preset adapts the *way each shape is asked*.

### 1.2 Benchmark rank is not harness fit

- Gemma 4 E4B led doc 44's Pick and Fill, while OpenBMB's table gives it the lowest BFCL v4 (47.0) and IFEval (44.4) of the 4B-class
  models it lists, and Liquid's table gives it an IFEval of 87.74 [V-vendor per doc 47 §3.1]. Spark-X2.5-4B's vendor table puts it
  far above Qwen3.5-4B on BFCL-V4 (65.1 against 50.3, thinking mode) [V-vendor per doc 47]. In our direct-mode `pick-hard` it scored
  0.667 / 0.733 pass^3 with the false escapes above [V, preliminary].
- Prompt format alone can move accuracy by tens of points, and the best format does not transfer. Formatting moved LLaMA-2-13B by up
  to 76 accuracy points, and "format performance only weakly correlates between models" [V, arXiv 2310.11324]. "The best templates
  do not transfer between different setups and even between models of the same family", over 21 models from 770M to 70B [V, arXiv
  2401.06766]. GPT-3.5-turbo varied by up to 40% with the template while GPT-4 was more robust [V, arXiv 2411.10541].
- Per-model prompt compilation works for small models: DSPy programs compiled for T5-770M and llama2-13b-chat were "competitive with
  approaches that rely on expert-written prompt chains for proprietary GPT-3.5" [V, arXiv 2310.03714].
- **Consequence** [I]: a harness tuned on one model and frozen is tuned for that model. The gains are largest for the small models
  Plotroom runs locally, and they can be found only on our own instruments, per model.

### 1.3 What the vendors trained for

Read from the model cards and chat templates at the pinned revisions (copies fetched 2026-09-27; the Qwen3.5-4B and Gemma 4 E4B
cards re-read at review on 2026-09-28, see Verification notes) [V-vendor; I in the last column]:

| Model | Thinking | Vendor sampler | Answer and tool conventions | Model-native paths | What it suggests for a harness preset |
| --- | --- | --- | --- | --- | --- |
| Qwen3.5-4B | On by default; `enable_thinking=false` renders an empty `<think></think>` block | Non-thinking, general: temperature 0.7, top_p 0.8, top_k 20, min_p 0, presence 1.5; the card adds that a high presence penalty "may occasionally result in language mixing" | Multiple choice (Best Practices item 3): "show your choice in the `answer` field with only the choice letter"; tool calls as XML, `<tool_call><function=…><parameter=…>` | "No thinking content in history" (item 4) | The `answer` field costs nothing (the draft starts from it; `choice` stays the control arm); the penalty is off-limits (D022); the XML tool format matters only for native tool calls |
| Gemma 4 E4B | Switched by a `<\|think\|>` token at the start of the system prompt; E2B and E4B emit no empty thought block when it is off | Temperature 1.0, top_p 0.95, top_k 64 "across all use cases" (Unsloth's GGUFs embed these values) | Native `system` role; native function calling (Gemma tokens, not JSON, doc 51 §2.6.1) | — | The vendor sampler starts for creative text and is a Pick arm; Pick and Fill start at the measured 0.6 until a run says otherwise |
| Granite 4.1 3B | None, by design (IBM: "predictable latency, stable token usage", doc 53 §2.4) | None shipped (`generation_config.json` holds token ids only); the card's example passes no sampling arguments; Unsloth suggests temperature 0, top_p 1.0, top_k 0 "for deterministic, instruction-following responses" [V-3p, re-read at review] | Tool calls as JSON `{"name", "arguments"}` inside `<tool_call>` tags; no default system prompt injected | A `documents` path that tells the model to answer "strictly aligning with the facts in the provided documents", or say it cannot; vendor task adapters (granitelib) for clarification, answerability, hallucination, uncertainty [V per doc 53] | Greedy decoding plus one-pass letter scoring; IBM's JSON system sentence (README "JSON as Output"); cards through `documents` for EXPLAIN and Pick; adapters as advisory signals only |

**Rule** [I]: every vendor convention enters tuning as a *candidate arm*, never as a default. The clearest case is Qwen's own
presence penalty (§1.1). Vendor settings are tuned for chat and reasoning benchmarks, not for one-token Picks behind a grammar.
A draft harness preset may *start* from a convention that costs nothing and that no measurement contradicts; the measured control
stays an arm, and PR7 lets the control win a tie (§4.4).

**Reconciliation with doc 51** (added at review, 2026-09-28):

- **Agreement.** Doc 51 §2.1, §2.2, §2.4 and §2.6 and its `data/model-profiles.csv` give the same thinking switches, vendor
  samplers and tool formats for these three models, and the same `documents` channel for Granite. Doc 51 adds facts a harness
  preset must respect: Gemma 4's native tool format is Gemma tokens, not JSON; a JSON Schema request can fail with HTTP 400 on
  Granite's role tokens where GBNF works (llama.cpp #29006); the Qwen3.5 template raises on a system message that is not first or on
  a `developer` role [V per doc 51].
- **Profile and harness preset.** Doc 51 §4 keeps probed facts (template rules, reasoning switch, schema dialect) in a *profile* and
  the tuned choices in D048's preset. The draft default harness preset takes its reasoning switch `from_profile`; until profiles
  exist, the staged checker reads the pinned templates' facts (thinking switch, `documents` path) from the GGUF headers [I]. §7
  item 10 lists the gap.
- **Which test decides.** Doc 51 §5's A/B (the general fallback against a native bundle, adopted at +4 of 90 Pick calls with a
  one-sided sign test at p ≤ 0.10) is a cloud screen. For the pinned local files the sealed held-out rules of §4.4 decide; doc 51
  §5.6 item 7 agrees that a preset changes only after a held-out win and, for a local model, the local run.
- **One correction for doc 51, reported, not edited here.** Doc 51 §5.5 calls Qwen3.5-4B's second-wave native arm "the vendor
  preset without presence, which doc 46 already measured". Doc 46 ran T 0.6, top_p 0.95, top_k 20, min_p 0 (doc 46 §1.4 and
  `run.py`), which is the card's *thinking, precise coding* set. The card's non-thinking general set is T 0.7, top_p 0.8, top_k 20
  with presence 1.5 [V-vendor, card re-read 2026-09-28], and no run has used it. The Qwen draft starts from that set with the
  penalty dropped (H-Q4).

### 1.4 The invariant: how we ask, never what code owns

| A harness preset may change | A harness preset never changes |
| --- | --- |
| The answer's form (letter or option key, the field name, a bounded `why`) and transport (structured output; native tool calls only on cloud endpoints) | The facts: catalogs, places, ids, engine limits; which options a menu holds and their code-written descriptions (doc 21 §1.1) |
| Reasoning mode per step kind, inside what the model supports | The escapes: `X none fit` and `Q ask me` stay on every menu; with extract-then-dispatch, code decides `X` |
| Sampler values, inside ranges; Pick and Fill penalties stay neutral (D022 amendment item 5) | Validators, lints, quote checks and admission; a truncated reply is never executed (doc 21 §8.2) |
| Schema mode: strict schema, compact grammar, or, for a cloud endpoint without enforcement, JSON mode plus validation | Ceilings: K, R, turns and cost caps from the effort level and the user (doc 38 §3.4); a preset may only lower them |
| Prompt layout, by **named, runtime-owned ids** only: layout, instruction variant, option rendering, card channel and format, frozen exemplar set, and where the pack's system text goes (never whether it is sent) | Tools and effects (none for Pick and Fill), trust labels and quoting of untrusted text; untrusted mission text never enters the system text or a `documents` channel |
| Decomposition, choosing among the **alternatives the DecisionKind registers** (direct, facets, extract-then-dispatch, escape pre-check; whole record, per field, span method) | Shape grants: only qualification grants Compose or Draft (doc 21 §3.3) |
| Scoring mode (vote, one-pass letter probabilities, calibration, option text) | Role bindings, the model and the data destination: no preset names another model; escalation to another model stays a user-made binding (D023 decision 3, D024) |
| Voting stop rules, repair message form, cascade thresholds and route (same-model re-ask, user card, code default) | Product scope and reach: no network, file or process access (`AGENTS.md`); presets are data, never code |

**Why this holds by construction** [I]: the preset carries no prompt text, only ids that resolve into the versioned prompt pack the
release ships. Every value is range-checked by the loader. Every model output still passes the same checks. A preset can make a model
more or less accurate. It cannot make it able to do anything new. The staged checker (§3.3) enforces the rows of this table that a
schema cannot express, and refuses fourteen negative controls built to break them.

## 2. The knob catalogue

### 2.1 Knobs per step kind

Allowed values; the default preset's value is in **bold** [I]. COMPOSE applies only where qualification already grants it (cloud
setups, 26B-class offload); for local 3–4B setups it is split into authored Fill and Pick steps.

| Knob | PICK | FILL | COMPOSE | Creative text | EXPLAIN |
| --- | --- | --- | --- | --- | --- |
| Answer form | **letter** · option key; field **`choice`** · `answer`; `why` **off** · before (40–240 chars, with the output cap raised to 200); transport **structured output** · native tool call (cloud only) | **whole record as pre-fill** · closed fields as Picks · field by field | One sub-structure | **`{"text"}`** per slot (envelope **JSON object** · tagged plain text, doc 51 arm E) | **explanation + fix** · explanation + code-chosen fix · card-sentence Pick |
| Reasoning | **off** · budget N where measured; the switch comes from the model's profile (doc 51 §4) | **off** | **off** locally; provider floor per DG020 in the cloud | **off** · budget | **off** |
| Sampler | temperature **0.6** (0 with one-pass scoring), top_p **0.95**, top_k **40** (family value once known), min_p **0**; penalties fixed neutral | same; penalties fixed neutral | ranges | ranges, penalties 0–measured | temperature **0.2** |
| Schema mode | **strict json_schema** · compact GBNF (local only) · JSON mode + validator (cloud only) | same | same | same | same |
| Layout | layout id **`static_first.v1`** · menu-last · CPU compact; option rendering **letter+label+description** · letter+label · key+label+description · JSON array (doc 51 FS1); cards **declared** · off · `documents` channel; card format **prose** · usage lines; exemplars **0**–3, frozen by DecisionKind or nearest in kind; pack system text **system role** · folded into the first user turn | same, no options | same | style card on; exemplars 0–3 | card channel **user turn** · `documents` |
| Decomposition | **direct** · facets (cap 3–7) · extract-then-dispatch · escape pre-check | spans **free + quote check** · verbatim grammar (local only) · code-candidate Pick · extractor; judgement fields **in the record with code-written bands** (as measured) · computed Pick · ask | **authored split** on budget | — | **explanation + fix** · code-chosen fix |
| Scoring | **generate and vote** · letter probabilities · calibrated letters · option text; permutation **per sample** · cyclic re-ask | generate | generate | generate | generate |
| K and stop | **K ≤ effort**, stop **two agree** · margin · fixed | K ≤ effort, first admitted | K ≤ effort | K ≤ effort, user sees all | 1–2 |
| Repair | **R ≤ effort**; finding with recomputed allowed values · re-menu of valid options only | re-fill only the failed field | one finding per turn | one finding | one finding, else the card verbatim |
| Cascade | margins for accept, re-ask, top-2 card and `Q`; `X`-mass threshold; route **user card** · same-model re-ask · code default | — | — | — | — |
| Output cap | **64** (+ `why`) | **320** | table (doc 40 R8) | **120** | **320** |

### 2.2 Why each knob matters: the evidence

| Knob | Evidence | Status |
| --- | --- | --- |
| Answer form | Symbol binding "varies greatly by model"; 1B-class models are near chance in letter format, which is why OLMES also scores the option text (doc 53 T2, S53, S55) [V per doc 53]. Qwen's card names an `answer` field for multiple choice [V-vendor]. Every measured Pick used a bare `{"choice"}` and reached 0.90–0.97 [V per docs 44, 46] | Arms, not measured |
| Leading `why` | Doctrine asks for it (doc 25 §4.3, doc 38 §3.3); every measured run omitted it; chain-of-thought gains concentrate in math and logic (doc 53 T10) | Doc 53 R7 decides; a per-model knob if models differ |
| Reasoning | Every measured row ran with thinking off, 0 thinking characters in 4,356 records (doc 46); higher effort did not help in 21 of 36 runs (HAL, doc 48 §5.5); Granite 4.1 vs 4.2 (same base, thinking added) is the clean test (doc 53 S7) | Off by default; budgets only where measured |
| Sampler | A presence penalty over the prompt tail cost end-of-menu letters (doc 46 §2.2; §1.1 above); Qwen's card warns of language mixing; Gemma's vendor sampler is temperature 1.0 [V-vendor]; greedy K = 3 collapses to one answer (doc 53 §2.4) | Penalties fixed; temperature, top_p, top_k tuned per model |
| Schema mode | 0 parse failures in 4,356 local calls, constrained or plain (doc 46); Gemma pretty-prints under llama-server's grammar, +9 tokens and about 200 ms per pick (doc 46 §2.6); JSON Schema can fail on Granite role tokens where GBNF works (issue #29006, doc 53 §4.8); cloud schema support is per endpoint (doc 48 §2.3); llama-server has been reported to continue unconstrained after a grammar parse failure (doc 47 §1.2) | Compact GBNF is an efficiency arm; validation stays on every path |
| Prompt layout and cards | The card effect changes sign by model and item (§1.1); cards lifted the weakest model most and "changed little for the rest" (doc 44 §2.1); Qwen copied a card's signature notation into code (doc 44 §3); layouts must stay cache-stable (doc 40 R2–R3, DG019) | Per-decision-kind card policy; layouts from a small runtime-owned set |
| Exemplars | Similar exemplars help strongly, and their order moves results (doc 25 §2.7); best templates do not transfer between models (arXiv 2401.06766); no measured run used exemplars | Arm; frozen per pack version (DG019) |
| Decomposition | Whole-record Fill never qualified, closed fields did (doc 44 §4); rule-bearing menus fail by family (HT03, HV01, PW04; §1.1); doc 21 §4.1 already lets code decide `NotSupported` from filled fields | The strongest lever for failure classes; alternatives must be authored per DecisionKind |
| Scoring mode | One-pass letter probabilities give a full distribution in one call; K = 3 voting bought +1.6 points on average for three times the calls (doc 53 §3) | Exists only in a scratch copy of the tooling (letter readout, calibration, cascade replay); not in the tree; the token-boundary check per answer form is still missing (tuning plan TF5) |
| K and stop | Majority of 3 raised menu accuracy to 0.967 for Qwen with cards (doc 44 §2.1); K is money on cloud setups (DG021) | Ceilings from effort |
| Repair | Repairs quote one finding with the recomputed allowed values (doc 25 §7.2); no measured repair data yet (doc 48 rung F3 is planned) [U] | Message form is a knob; R never above effort |
| Cascade | Escalating non-unanimous menus lifted Qwen3.5-4B `pick-hard` from 0.833 to 0.967 in-sample, and hurt when the target was weaker (doc 53 §3) | Thresholds are per model; the route is never another model (D023 decision 3) |

### 2.3 Settings that are not knobs

Fixed by doctrine for every harness preset: facts and menu contents; the hard menu cap of 7 plus escapes (DG006: a setup may
qualify for a *smaller* cap); neutral Pick and Fill penalties; thinking switched explicitly and checked with `/apply-template`;
admission and every validator; the untrusted-text rules (doc 21 §9: quoted, labelled data fields, never instruction positions);
the pack's system text, which a harness preset may place (system role or first user turn) but never drop, since the text itself is
what the release ships; one frozen answer schema per (DecisionKind, harness preset) inside a cache namespace (doc 40 R4, DG015);
the effort ceilings; and "no silent upward move" (doc 25 §3 principle 5) [I on V]. Until the two-stage role binding is decided (§7
item 9), no cascade route leaves the model the user bound.

## 3. The preset file

### 3.1 Principles [I]

1. **Data only.** A JSON file, validated against a versioned schema; unknown keys are refused. It holds values and ids, never prompt
   text, templates or code.
2. **A diff of the default.** Every harness preset except the default names `extends: "default@x.y.z"` and states only what it
   changes, so the diff *is* the glass-box explanation (§3.6).
3. **Bound to one exact setup.** A preset applies only to the artifact it was tuned on; anything else gets the default preset.
4. **Evidence travels with it.** Provenance and badges are part of the file; a preset without held-out results is a draft.
5. **Never less safe than the default.** The loader checks the §1.4 invariant; the schema makes the fixed settings constants.

### 3.2 Binding and identity

A local harness preset binds to: the repository, the 40-character commit, the file name, bytes and SHA-256 (the D022 pin); the quant
label taken from the file name, because the GGUF file type reads the same for Q4_K_M and UD-Q4_K_XL (doc 46 §1.5), with the header's
file type added where the two disagree (Unsloth's Gemma 4 E4B QAT file is named UD-Q4_K_XL, while its header reads Q4_0 and "smart
Q4_0, QAT-lossless" [V, GGUF header read]); the SHA-256 of the chat template embedded in the GGUF; the llama.cpp build tag, the
backend (Vulkan, Metal, CPU or a user-downloaded CUDA build) and the asset's SHA-256; the context size; the KV-cache type; and the
placement (all layers on the GPU, MoE offload or CPU). A cloud harness preset binds to doc 48 §7.4 item 1's cloud identity:
provider, model, endpoint, precision, reasoning setting and read date (D045 item 5).

The model setup that doc 21 §7.2 records per step ("model, version, quantisation, chat template, sampler, reasoning") and the
`ModelSetupId` in the architecture's journal (agent-runtime §5) gain the harness preset's id, version and file hash. Qualification is
kept per (model setup incl. harness preset, DecisionKind), and per field for Fill (agent-runtime §7) [I].

### 3.3 Proposed schema

The full draft (JSON Schema 2020-12, draft 2) is staged with the run tooling. It is to be committed under `tools/local-qual/presets/`
with the first tuning run, together with draft harness presets (version 0.2.0) for the default, Qwen3.5-4B, Gemma 4 E4B QAT and
Granite 4.1 3B. A standard-library checker validates each file alone and merged onto its base, checks the pins against the GGUF
headers, and enforces the loader rules a schema cannot express: neutral Pick and Fill penalties; no shape grant; K and R ceilings; a
`documents` channel or an `enable_thinking` switch only on a pinned template that has one; verbatim spans only with a sidecar grammar;
sidecar grammars only locally; validator-only schema modes and native tool calls only on cloud endpoints; no route to an undecided
second stage. It refuses fourteen negative controls built to break those rules, among them a Pick presence penalty of 1.5, a step
granting itself Compose, a cascade route naming a model, dropping the pack's system text and an arm that sets one knob to two values.
The outline [I]:

```text
harness-preset/1
  format: "plotroom.harness-preset/1"   preset_id   version (semver)
  status: draft | candidate | tuned | qualified | withdrawn
  extends: "default@x.y.z"              (only the default omits it)
  prompt_pack: { id, version }          (the ids below resolve here; DG012's keys)
  binds_to: local-gguf { model{repo, revision, file, bytes, sha256}, quant_label, chat_template_sha256,
                         runtime{name, build, backend, asset_sha256}, context_tokens, kv_cache_type, placement }
          | cloud-endpoint { provider, model, endpoint, precision, reasoning_setting, read_on }
          | any                          (default preset only)
  step_kinds:
    pick:    answer{form, field, why{mode, max_chars}, transport}
             reasoning{mode, budget_tokens, switch (a template kwarg, a system token, none, or from_profile), value}
             sampler{temperature, top_p, top_k, min_p, presence=0, frequency=0, repeat=1}  schema_mode
             layout{id, instruction_variant, system_message: pack|fold_into_first_user, cards{mode, format},
                    option_rendering, exemplars{count, selection, bank, position}}
             decomposition{mode: direct|facets|extract_dispatch|escape_precheck, facet_cap 3..7}
             scoring{mode, permutation, rotations, calibration{temperature, prior_id}}  voting{k_max, stop}
             repair{r_max, message}  cascade{accept_margin, reask_margin, top2_margin, x_mass_threshold, route}
             output_cap_tokens
    fill:    reasoning, sampler (neutral penalties), schema_mode, layout,
             decomposition{record, spans, judgement_fields: in_record_bands|computed_pick|ask_user}, voting, repair,
             output_cap_tokens
    compose: reasoning, sampler, schema_mode, layout, repair, on_budget: authored_split   (no field grants a shape)
    text:    reasoning, sampler, schema_mode, envelope: json_object|tagged_plain_text, layout, voting, repair,
             output_cap_tokens
    explain: reasoning, sampler, schema_mode, layout, decomposition{mode}, checker, repair, output_cap_tokens
  decision_overrides: [ { decision_kind, step_kind, settings, evidence } ]   (only registered alternatives)
  provenance: { created, authors, tuning_runs[{run_id, suite, suite_sha, date}],
                held_out[{step_kind, suite, suite_sha, n, metric, default_value, preset_value, ci95, test, decision_rule}],
                vendor_sources[] }
  badges: [ { step_kind, field?, instrument, instrument_sha, n, value, state, date } ]
  knob_ledger: [ { step_kind, decision_kind?, knob, start, change: base|diff|inherit|fixed, hypothesis?, family,
                   evidence[], alternatives[{arm?, value, why, priority: grid|reserve|not_in_grid}], tune } ]
  notes: [ short strings ]
```

The **knob ledger** is the glass-box explanation of §3.6 in data form: one entry per knob and step kind (and per decision override),
giving the value the draft starts from, whether it is the preset's own change, the evidence with this doc's legend, and the
alternatives tuning must try. The checker recomputes every `start` from the merged file and substitutes every alternative to prove
it legal. An arm id may appear on several entries; those values move together (a leading `why` with a 200-token output cap, for
example), and the checker applies them together. Ids ending in 0 are the measured controls; an arm the tuning plan names but the
ledger does not list is the draft's own start value [I].

An excerpt of the Qwen3.5-4B draft (status `draft`, nothing tuned; the full file adds Fill's reasoning and sampler, the other step
kinds, two more overrides, provenance and the ledger) shows the shape of a diff:

```json
{
  "format": "plotroom.harness-preset/1", "preset_id": "qwen3.5-4b-q4_k_m", "version": "0.2.0",
  "status": "draft", "extends": "default@0.2.0", "prompt_pack": { "id": "wilco-core", "version": "0.2.0" },
  "binds_to": { "kind": "local-gguf",
    "model": { "repo": "unsloth/Qwen3.5-4B-GGUF", "revision": "e87f176479d0855a907a41277aca2f8ee7a09523",
               "file": "Qwen3.5-4B-Q4_K_M.gguf", "bytes": 2740937888,
               "sha256": "00fe7986ff5f6b463e62455821146049db6f9313603938a70800d1fb69ef11a4" },
    "quant_label": "Q4_K_M",
    "chat_template_sha256": "7f0e529032c25183bcd66c7f238da2d377f43be754a94e2725a58c4e16d2ed67",
    "runtime": { "name": "llama.cpp", "build": "b11146", "backend": "vulkan",
                 "asset_sha256": "55a378aa095b466979d85075234f66d7655c7a7483222af0c006c0e55b4d7bd6" },
    "context_tokens": 8192, "kv_cache_type": "f16", "placement": "gpu-all" },
  "step_kinds": {
    "pick": { "answer": { "form": "letter", "field": "answer", "why": { "mode": "off" }, "transport": "response_format" },
              "reasoning": { "mode": "off", "switch": "chat_template_kwargs.enable_thinking", "value": false },
              "sampler": { "temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0,
                           "presence_penalty": 0, "frequency_penalty": 0, "repeat_penalty": 1 },
              "layout": { "instruction_variant": "pick.answer_field.v1" } },
    "fill": { "schema_mode": "gbnf_compact",
              "decomposition": { "record": "whole_record_prefill", "spans": "verbatim_grammar",
                                 "judgement_fields": "in_record_bands" } } },
  "decision_overrides": [
    { "decision_kind": "trigger.end_type", "step_kind": "pick",
      "settings": { "decomposition": { "mode": "extract_dispatch" } },
      "evidence": "HT03 (same End number on both triggers means AND): 0 of 24 samples across four Qwen3.5-4B arms, with and without the card that states the rule." },
    { "decision_kind": "module.pick", "step_kind": "pick",
      "settings": { "decomposition": { "mode": "escape_precheck" } },
      "evidence": "HM04 near-fit escape: 12 of 24 (7 of 12 without cards, 5 of 12 with); far escapes 46 of 48." } ]
}
```

The `decision_kind` ids are spike-local until the DecisionKind registry exists (doc 38); `chat_template_sha256` may be null only in a
draft (every 0.2.0 draft carries the hash read from its GGUF header).

### 3.4 Provenance and badges

- **Provenance** names every tuning run (id, suite and suite hash, date, arms) and every held-out result: the step kind, suite hash,
  n, metric, the default preset's value, the harness preset's value, the 95% interval, the test and the decision rule applied (§4.4).
- **Badges** follow D022 item 4, D037 and doc 44 §5.3: one per step kind (per field for Fill), naming the instrument and its hash,
  n, the value, the date and the state (`spike-checked`, `qualified`, `not-met`, `requalifying`). A badge belongs to (model setup,
  harness preset version). Tuning makes a harness preset "tuned"; only doc 21 §12.3's consecutive all-pass trials make a badge
  "qualified". Recommending the model still needs D037's licence rule.

### 3.5 How harness presets ship, update and are overridden [I]

- **With the Model Manager's manifest.** A manifest row (doc 44 §5.3; agent-runtime §13) gains `harness_preset = { id, version,
  sha256 }`. The files ship with a release, or through the manifest's update channel, which is a D008 source: user-enabled, off by
  default, blocked offline, hash-checked, fetched only when the user asks. Wilco never fetches, suggests or edits a harness preset;
  there is no agent tool for it.
- **Updates are visible.** A new version appears as a change card (illustrative: "Qwen3.5-4B harness preset 1.2 → 1.3: Fill spans
  now copied verbatim; held-out Fill +16 points"), takes effect at the next session start, and keeps the old version for one-click
  rollback. Under DG012's option C, a major version voids the setup's badges until re-checked; a minor one marks them `requalifying`.
- **Overridable.** Settings → Models → *model* → Harness preset offers "Tuned for this model", "General" (the default preset) and
  "Custom…". A custom edit changes knob values inside the schema's ranges; the fixed settings (§2.3) are not offered. Saving creates
  a local custom harness preset whose badges read "custom: unqualified" until the user runs "Check this model on my machine" (doc 44
  §5.3) with it.
- **Unknown models get the default preset.** When the capability probe recognises a known template family on an unpinned file, the
  editor may *offer* the family's harness preset, labelled "untested on this file"; it never applies it silently.

### 3.6 The glass box in the editor (D010)

- The plan card shows the active harness preset and version for each bound role.
- The model's settings page lists, in plain words, **what the harness preset changes from the general harness**, per step kind, each
  line linked to its held-out evidence (illustrative: "Trigger-type questions are asked in your own terms and code applies the engine
  rule; held-out +18 points").
- The decision inspector shows, for each decision, the harness preset version and the knobs that applied: "Asked with Qwen3.5-4B
  harness preset 1.0: 'When should the mission end in victory?' → 'only once every listed objective is done' → code chose End #1 on
  both triggers (rule: trigger types)."
- The run record stores the harness preset's id, version and hash with every model call, so a decision can always be traced to the
  exact way it was asked (doc 21 §7.2 and its guarantee G5, §12.4).

## 4. The tuning protocol

### 4.1 Tuning and held-out split

- **Tuning split = today's suites plus the tune halves of two staged pools** [I]: `pick` 30, `pick-hard` 30, `fill` 12, `explain`
  10, `text` 10, the six-item dispatch draft, 30 of the 60 new Pick menus (`pick-pool`, seven real options plus `X` each, with five
  dispatch sketches) and 18 of the 36 new Fill records (`fill-pool`, matched pairs split by a SHA-256 coin). Every item has been
  inspected item by item in docs 44, 46, 53 and here, or written in the same pass as that analysis, so none of them is held-out
  evidence. Pick families are screened on the 60 hard menus (`pick-hard` plus the pool's tune half); the 30 easy menus serve only
  as a no-collapse guard in the final tune-split confirmation.
- **Interim held-out** [I]: the pools' other halves (30 menus including six dispatch sketches, 18 records), frozen by SHA-256, get one
  look per model after the tune-split confirmation, default against candidate. Their author had read the tuning analysis, so they
  are an early warning (PR1 guards, PR5's sign), never a reason to call a harness preset tuned; if their result changes the
  candidate, they become tuning material.
- **Held-out split, written first and sealed** [I]: `pick-hold` has 120 menus with 7 real options plus `X`: 24 planted escapes (12
  near-fit like HM04, 12 far) and at least 24 rule-bearing menus. `fill-hold` has 48 records with span decoys: finding codes, a second
  place name, a verb phrase around the target. `dispatch-hold` pairs 24 of the rule-bearing menus in dispatch form. `explain-hold`
  has 20 findings, at least 5 with an easily invented fix, and `text-hold` 20 slots with the style card sent. Items are written by
  someone who has not seen the tuning results (doc 21 OQ2; doc 14 §9 item 2: "keep held-out cases that were never used while tuning
  prompts"). They are our own synthetic text, frozen by SHA-256, with the hash recorded in the tuning plan before the first tuning
  call. The items stay outside this public repository until they are used, as doc 21 OQ2 suggests for paraphrase cases, so that
  neither the tuner nor future model training sees them first.
- **Frozen before it is opened** (added at review) [I]: the prompt-pack fragments and layouts, the exemplar banks, the fitted cascade
  thresholds and calibration, and one decision table per overridden DecisionKind are hashed into the tuning plan before the interim
  look and again before the sealed one. The draft dispatch suite writes one decision table per item, which is fine for tuning but
  would let an item's answer shape its own table; held-out dispatch items are therefore scored only with the frozen per-kind tables.
  The held-out author writes the requests, menus, DecisionKind tags, expected fields and answers; an item whose kind has no frozen
  table is scored in its direct form only.
- **Two looks only:** the sealed held-out set runs once for the default preset and once for the final candidate, same seeds, paired
  item by item, and only after all three models' candidates are frozen. A second candidate is a new pre-registration with a Holm
  step-down. Afterwards the held-out set becomes tuning material and a fresh one is written.
- **Power** [I on V per doc 48 §4.4]: a 10-point paired difference at 15% discordance needs about 115 items, so 120 Pick menus
  resolve 10 points; 48 Fill records resolve only large effects, about 20 points.

### 4.2 Candidates

Each candidate is a diff of the default preset in one knob family, with a written hypothesis, from three sources [I]:

1. **Vendor conventions** (§1.3): samplers, answer-field conventions, template paths (`documents`), thinking modes, vendor adapters.
2. **Failure analysis on the tuning split:** the §1.1 classes map to knob families. Rule-bearing menus map to extract-then-dispatch;
   near-fit escapes to an escape pre-check or a per-kind card policy; span paraphrase to a verbatim grammar; span omission to
   code-built span candidates; fix invention to a code-chosen fix; format overhead to a compact grammar; unused context to cards off.
3. **Doctrine and sibling proposals:** one-pass scoring, calibration and cascades (doc 53 R4–R6), the leading `why` (R7), adaptive K
   (DG021), a smaller menu cap (DG006).

**Extract-then-dispatch, concretely** [I]: the menu's decisive facts become one closed-field Fill phrased in the user's terms,
where every field allows "unspecified". A code-owned decision table restating the card's engine rule then picks the option. Code
answers `X` when no option serves the combination, and asks one computed question when a required field is unspecified. This is
doc 21 §4.1's IntentFill → Dispatch pattern applied inside one Pick. A draft suite does this for HT03, HV01, HM04, HK01, HW03 and
HW04, and the Pick pool carries eleven more sketches (five in its tune half); for example HT03 asks "When should the mission end in
victory?" with the options "only once every listed objective is done", "as soon as any one of them is done" and "each objective
ends the mission with its own ending". Each decision table reproduces its item's answer from the expected fields [V, checked by
script]. These tables are per item; the product needs one table per DecisionKind, which is what the held-out look uses (§4.1).

### 4.3 Search: sequential halving with paired tests

- **Coordinate ascent across knob families:** decomposition first (largest effects), then answer form and schema mode, layout and
  cards, sampler, scoring mode, and finally voting and cascade thresholds; then the Fill, EXPLAIN and text families. The incumbent
  starts as the default preset (the measured control) and each family's winner joins it before the next family is searched; arms
  are run against the incumbent, not against the draft's start values, and there is no full grid.
- **Within a family** (the staged plan's schedule): a family with three or four arms runs two rounds of Sequential Halving, first on
  30 hard menus (15 from `pick-hard`, 15 from the pool, stratified by category, with every planted escape, escape decoy and
  rule-bearing item forced in), then the better half on all 60, at k = 3 in both card conditions; a family with two arms runs one
  paired round on the 60; five to eight arms would take three rounds (15, 30, 60). Sequential Halving splits a fixed budget evenly
  across log₂ n rounds and drops the worst half each round [V, Karnin et al. 2013]; Hyperband (arXiv 1603.06560) applies the same
  budget-allocation idea to hyperparameter search [I]. Per-kind card policy, calibration and cascade thresholds are fitted offline
  from stored records, at no call cost.
- Rank by pass^3; break near-ties with exact McNemar on items right by majority, since with 30 items only splits of 6:0 or more reach
  p < 0.05 (doc 46 §3), then by PR7, so the control wins a tie. On the tune split an arm advances only if it beats the incumbent by
  at least 2 menus pass^3 (Pick) or 3 records all fields right (Fill), with no PR1 break; these are screening thresholds, not
  evidence. An arm that breaks a PR1 guard is dropped in any round, whatever its pass^3.
- Tooling runs on a scratch copy of `tools/local-qual` with a `--preset` flag that renders a harness preset into `run.py`'s request
  fields, plus the dispatch shape, verbatim-span grammar, per-field Fill and letter-probability scoring (doc 53 §5.3) [I].

### 4.4 Pre-registered decision rules

| Rule | Adopt a knob, or a harness preset, only if… |
| --- | --- |
| PR1 Must-pass | Schema-valid 100% locally; 0 thinking characters on thinking-off calls; planted escapes no fewer than the default's in each condition; false escapes no more than the default's; the injected marker-text routing item unaffected; no truncated reply executed |
| PR2 Quality | The held-out primary metric gains at least the minimum effect below **and** exact McNemar on items right by majority is significant (one-sided α = 0.05, Holm across the model's step kinds) **and** the paired bootstrap 95% lower bound of the per-call difference is above 0 |
| PR3 Efficiency | For speed or token knobs (compact grammar, cards off, one-pass scoring): the one-sided 95% lower bound of the paired per-call difference is above −0.03 (Pick) or −0.05 (other kinds), **and** p50 latency or prompt tokens fall by at least 15% |
| PR4 No collapse | No held-out category loses more than 2 menus by majority against the default |
| PR5 Replication | The held-out effect has the tuning effect's sign; if it is below half of it, both are reported as "optimistic tuning" |
| PR6 Latency | p50 per decision stays at most 1.25 × the default's, unless adopted under PR2 with the added time shown on the plan card |
| PR7 Parsimony | Ties within noise keep the arm changing fewer knobs; a knob without a held-out effect is removed |
| PR8 Promotion | A knob adopted under PR2 for all three first targets moves into the default preset after a check on a fourth model |
| PR9 Status | PR1–PR7 make a harness preset "tuned"; doc 21 §12.3's trials make its badges "qualified"; D037 still governs recommendation |

**Minimum held-out effects** [I]: Pick +10 points pass^3 on `pick-hold` (both conditions pooled, each reported); Fill +15 points all
fields right per call, with validators pass^3 not lower; dispatch +15 points against the same menus asked directly; EXPLAIN +3 of 20
findings passing both samples with no new invented fix; text +3 of 20 slots passing every code check in both samples.

**Dispatch overrides** (added at review, before any run) [I]: a harness preset's dispatch overrides are judged together on the
`dispatch-hold` items of the kinds it overrides, against the same menus asked directly, at the dispatch minimum effect above. PR4
then applies per DecisionKind: an overridden kind whose held-out menus lose more than 1 menu by majority against the direct form
goes back to direct.

### 4.5 Re-qualification triggers (DG012)

| Change | Effect on the harness preset and its badges [I] |
| --- | --- |
| Model file (SHA-256) | The harness preset no longer applies; the default preset runs until the preset is re-bound and quick-checked (must-pass items plus 30 held-out menus) or re-tuned |
| Chat-template hash (a GGUF re-issued with a template fix; doc 48 §4.1 lists several) | Major: full held-out re-run |
| llama.cpp build or backend | Minor: `requalifying`; quick re-check before the next release; the numerics differ across backends (docs 44, 46) |
| Context size or KV-cache type | Minor: quick re-check |
| Prompt pack | Major version: full re-run; minor: quick re-check (DG012 option C) |
| Harness preset version | Major (a knob family changed): full held-out; minor (thresholds): quick re-check |
| Cloud endpoint: provider, precision or reasoning setting | Full re-run for a cloud harness preset; a monthly 20-item canary catches drift (doc 48 §4.4) |
| GGUF-embedded sampler defaults | No effect, since every value is pinned per request (D022); recorded |

### 4.6 Cost and time budget

The staged tuning plan budgets every stage from measured warm p50s: doc 46's llama.cpp figures for Qwen and Gemma, and for Granite
doc 44's Ollama figures scaled by the other two models' llama.cpp-to-Ollama ratio (Granite is unmeasured on llama.cpp). It adds 15%
overhead and assumes the worst-case survivors of each halving; stored control records cost no calls [I]:

| Scope | Qwen3.5-4B | Gemma 4 E4B QAT | Granite 4.1 3B |
| --- | --- | --- | --- |
| Tuning (S0 preflight, control or baseline, families F1–F6, Fill, EXPLAIN, text, tune-split confirmation) | 3,659 calls, 92 min | 2,240 calls, 51 min | 2,658 calls, 33 min (its baseline B0 is new: no llama.cpp records exist) |
| Interim held-out (one look) | 468 calls, 13 min | 468 calls, 12 min | 407 calls, 5 min |
| Sealed held-out (two looks): `pick-hold` 120 × 3 × 2 conditions per arm; `fill-hold` 48 × 3; dispatch 24 × 3 for the candidate only, since the direct form is inside `pick-hold`; EXPLAIN and text 20 × 2 per arm | 1,960 calls, 51 min | 1,960 calls, 54 min | 1,662 calls, 23 min (a letter readout takes 1.3 passes per menu instead of 3 samples) |
| GPU time in all | 2.6 hours | 1.9 hours | 1.0 hour |
| Grading by LLM graders with one fixed rubric (doc 44 §5.4 item 2) | 200 EXPLAIN and text answers | 200 | 240 |

All three first targets: 8,557 tuning calls, 1,343 interim and 5,582 sealed, about 5.6 GPU hours. The tiny tier on CPU (Pick and
closed Fill only, four arms, one-pass scoring) would take about 2–4 hours per model at `-dev none` (doc 53 §2.6 classes, unmeasured).

- **Cloud-first (D044):** Qwen3.5-4B, Gemma 4 E4B and Granite 4.1 3B have no cheap same-weights host (Featherless only, or none), and
  the owner chose no Featherless top-up (D044 amendment, OWQ-27). So they are tuned locally, as P5 says. For hosted models (the
  offload class), the precision-insensitive knob families (decomposition, answer form, layout, cards) may be pre-screened on two ZDR
  strict-schema endpoints at k = 1: battery S costs $0.001–0.025 per endpoint run (doc 50 §5.2–§5.3), about $0.02–0.40 for eight
  arms on two hosts. Sampler, schema-mode and scoring-mode knobs depend on the runtime and are tuned only on the pinned local artifact.
- **Cloud harness presets** for D045's free setups are tuned entirely per endpoint, on the synthetic suites only (D047).
- **Order:** only after doc 49's run has freed the machine; one model at a time; never concurrent with a timed job.

## 5. Presets, fine-tuning and one general harness

- **Fine-tuning is not chosen** (D027 item 6: data licensing, per-profile and per-base upkeep, poor transfer, no help for cloud
  models). A harness preset needs no training data, no teacher terms (doc 53 §3) and no GPU training. It moves the harness toward the
  formats, modes and paths the vendor already trained, which is exactly the owner's direction. Vendor task adapters (granitelib) are
  model-native assets, not Plotroom training; a harness preset may enable them as advisory signals only (D023 decision 5). Doc 53's
  post-v1 format-adapter spike stays an open owner question.
- **The general harness survives as the default preset.** It is what docs 44 and 46 measured: letter answers, thinking off, neutral
  penalties, strict schema, declared cards, K = 3 permuted samples. Every unknown or custom model uses it, and every harness preset is
  a diff of it. PR8 moves any knob that wins for all first targets into the default, so the general harness improves too.
- **Costs to keep in check** [I]: a harness preset per artifact multiplies maintenance. Plotroom maintains them only for models on
  D037's recommended list and a few popular bring-your-own models, each tuned preset aiming at about ten changed knobs; everything
  else runs the default preset. The drafts start wider (17 to 24 changed ledger entries, five of them the per-step thinking switch a
  profile will hold), and PR7 removes every knob without a held-out effect.
- **Where the line sits:** a harness preset may change *how* a decision is asked, including the decomposition code authored for that
  DecisionKind. A problem that no way of asking fixes (PW04 for the 3–4B models; free-text engine knowledge, 0 of 24 for every model)
  stays with code: filter the menu by the known fact, or show the card (doc 21 §2; D027).

## 6. First targets

### 6.1 Qwen3.5-4B (Q4_K_M, the equal alternative to the default; D023 amendment)

Plays to: grounded explanation, closed-field Fill, easy menus. Needs help on: rule-bearing menus, near-fit escapes, span copying.
"Draft" says whether the 0.2.0 draft harness preset starts from the change or keeps it as an arm; the measured control is always an
arm, and the staged tuning plan names the arms.

| Id | Knob change | Draft | Evidence | Expected |
| --- | --- | --- | --- | --- |
| H-Q1 | Extract-then-dispatch on trigger-type, roll-scope and campaign-node-type menus | Start | HT03 0 of 24; HV01 6 of 24; HK01 1 of 12 without cards, every miss Cutscene | Largest single gain; tests whether a plain question beats a card |
| H-Q2 | Escape pre-check on module menus ("does one option do everything the request needs?"); code turns "no" into `X` | Start; cards off on module and waypoint menus is an offline arm | HM04 7 → 5 of 12 with cards; far escapes 46 of 48 | Near-fit `X` recall up, no false `X` |
| H-Q3 | Fill spans by verbatim grammar (word-aligned substrings of the request only), under a compact sidecar grammar | Start; spans as a Pick over code-built candidates and closed fields as per-field Picks (judgement fields as computed Picks) are arms | Reworded target spans; Chinese characters under penalty 1.5; `size` 16 of 24 | Span errors toward 0; quote check holds by construction; finding codes still need code's check |
| H-Q4 | Vendor non-thinking sampler (temperature 0.7, top_p 0.8, top_k 20), penalties still neutral, for Pick, Fill and text | Start | Qwen card (Best Practices item 1); never run: doc 46 ran the thinking-mode precise-coding set (§1.3) | Unknown; a cheap change |
| H-Q5 | Answer field `answer` and the card's multiple-choice sentence (restated in the pack) instead of `choice` | Start | Qwen card, Best Practices item 3 | Probably within noise; PR7 keeps `choice` on a tie |
| H-Q6 | One-pass letter scoring with a cyclic re-ask; calibration offline | Arm | Doc 53 R4; `"A`–`"G` are single tokens but `"X` and `"Q` are not, so a boundary check gates it | Same accuracy at about half the latency, plus a confidence |
| H-Q7 | Bounded `why` (160 characters) before the letter, with a 200-token cap | Arm | Doc 53 R7 | Unknown |
| H-Q8 | EXPLAIN unchanged (control) | Start (only top_k 20 pinned, as measured) | 20 of 20 and 19 of 20 | Keeps its lead |

### 6.2 Gemma 4 E4B QAT (the provisional default; not recommendable until its licence fields agree, D023 amendment)

Plays to: Pick and whole-record Fill, spans, escapes. Needs help on: echoing options, invented fixes, output overhead.

| Id | Knob change | Draft | Evidence | Expected |
| --- | --- | --- | --- | --- |
| H-G1 | Compact GBNF (no optional whitespace) for Pick, Fill, text and EXPLAIN; Pick output cap 32 | Start | 16.3 against 7 output tokens per pick; about 200 ms per pick; Fill 70.6 against 44.3 tokens | PR3 efficiency win if accuracy is non-inferior |
| H-G2 | EXPLAIN writes the explanation; the fix comes from code's fix list or the card | Start | The same invented E10 fix on both runtimes | Hallucinated fixes to 0 |
| H-G3 | Extract-then-dispatch on roll-scope and waypoint-type menus | Start; cards off on those two kinds is an offline arm | HV01 7 of 24 (non-QAT 0 of 12); HW03 SEEK AND DESTROY in 8 of 12 samples with cards | Lure-shaped errors down |
| H-G4 | Vendor sampler (temperature 1.0, top_k 64, top_p 0.95) | Start for creative text; an arm for Pick | Gemma card "across all use cases" | More varied candidates; checks still gate; T 1.0 is expected to cost pass^3 on Pick |
| H-G5 | One-pass letter scoring; calibration offline | Arm | Doc 53 R4; every letter is a single token with no quote merges | As H-Q6, for latency rather than accuracy |
| — | `size` as a separate computed Pick with "unspecified" | Arm | `size` 19 of 24, the only Fill errors on llama.cpp | Judgement errors down |

A Gemma harness preset must be re-bound (§4.5) if Google's official QAT Q4_0 file replaces Unsloth's, as doc 46 §4.1 asks before
Gemma becomes the default.

### 6.3 Granite 4.1 3B (Q4_K_M, the low-VRAM option; doc 53 §2.4)

Plays to: speed, terse constrained text, card-grounded explanation, predictable non-thinking decoding. Needs help on: span omission,
`side` (29 of 36), campaign-arc menus (0.67, doc 44), and a baseline on the product runtime.

| Id | Knob change | Draft | Evidence | Expected |
| --- | --- | --- | --- | --- |
| H-R0 | None: the first llama.cpp baseline (the default preset), including `pick-hard` | Control of every family | Only Ollama records exist | Places Granite beside the others |
| H-R1 | Temperature 0 (Pick, Fill, EXPLAIN) with one-pass letter scoring, one cyclic re-ask on a low margin, placeholder cascade thresholds | Start; IBM's recipe (one greedy sample) and calibration are arms | No vendor sampler; greedy in IBM's examples, BeeAI and Unsloth; Mellea reads first-token log-probabilities (doc 51 §3.4 M12, M25); greedy K = 3 collapses to one answer (doc 53 §2.4) | A confidence signal at the lowest latency measured |
| H-R2 | Cards off on Pick (efficiency, PR3) | Offline arm | 82 of 90 calls chose the same letter with and without cards | Fewer prompt tokens at equal accuracy |
| H-R3 | Closed Fill fields as per-field Picks; spans as a Pick among code-built candidates (request n-grams, finding codes excluded); judgement fields as computed Picks; K = 1 | Start; a native whole-record arm (IBM's JSON sentence plus two exemplars) is the alternative | Places left empty on F02 and F04, every sample; `side` 29 of 36; per-field Picks 0.9–1.0 (doc 53 T8) | Span and side errors down |
| H-R4 | Cards through the template's `documents` path, for EXPLAIN and for Pick | Start | Granite 4.1's trained grounding path; S0 must show that llama-server forwards `documents`, or the arm is refused, never hand-rendered | Equal or better; tests "use the native path" directly |
| H-R5 | Extract-then-dispatch on trigger-type, roll-scope and timer-type menus | Start, by analogy (no Granite `pick-hard` record yet) | HT03 and HV01 fail on every measured 3–4B model; Granite's own PT03 and PT04 misses on `pick` | Informs PR8 |
| H-R6 | granitelib query-clarification and answerability adapters, shadow only | Reserve | Doc 53 §2.4 (vendor numbers) | Recorded only (D023 decision 5) |
| H-R7 | IBM's JSON system sentence with the schema in `<schema>` tags, under a compact GBNF grammar | Start; the plain wording and `json_schema` are arms | Granite 4.1 README "JSON as Output"; llama.cpp #29006 (doc 51, doc 53 §4.8) | Equal accuracy without the HTTP 400 risk |
| H-R8 | Two frozen style exemplars for creative text | Start | 14 of 20 lines graded partial: flat or restating the context (doc 44 grades); IBM's Granite 4.0 prompt guide builds small-model prompts from examples | Livelier lines; an n-gram check against the bank catches copying |

### 6.4 The tiny tier and the default preset

- **Tiny tier (doc 53):** harness presets for models of 2B or less start from doc 53 §4: Q8_0 files and a facet cap of 3 at 1B or
  less; one-pass scoring in the model's qualified mode (letters or option text, doc 53 R5); no `why`; the CPU-compact layout with
  200–400 tokens per decision behind a cached prefix; thinking off and checked. Their tuning is Pick and closed Fill only, after doc
  53's floor ladder names the survivors.
- **The default preset** is drafted from docs 44 and 46 as measured, with four notes: `top_k` 40 (llama-server's default) for
  unknown families; the leading `why` left off until doc 53 R7 decides; judgement fields inside the record with code-written bands,
  as measured, with computed Picks as an arm; and the thinking switch taken from the model's profile (doc 51 §4), checked with
  `/apply-template` before the first call.

## 7. Design-gap candidates (listed, not filed)

1. **The harness preset in the model-setup identity and the qualification key.** Doc 21 §7.2 and DG012's six keys lack it, and so
   does agent-runtime §5's `ModelSetupId`. Proposal: add (preset id, version, hash); DG012's major/minor rule applies to its versions.
2. **Authored alternative decompositions for Pick and Fill.** Doc 38 §3.3 allows `split` only for Compose and Draft; extract-then-
   dispatch and the escape pre-check need a registered slot per DecisionKind, with the decision table as code.
3. **Answer schema per (DecisionKind, harness preset).** DG015 and doc 40 R4–R5 freeze one schema per DecisionKind. A per-model
   field name, option-key form or leading `why` needs the freeze to be per (DecisionKind, harness preset); the cache namespace
   already includes the model setup.
4. **Card policy per model and DecisionKind.** D027 item 7 makes each step declare its cards. A harness preset turning cards off, or
   moving them to a `documents` channel, needs a rule that keeps activation code-owned and measured.
5. **Named, runtime-owned capsule layouts.** Doc 38 §3.3 fixes one layout; DG019 is still open. Harness presets need a small,
   versioned set of layouts (static-first, menu-last, CPU-compact) to choose from.
6. **Verbatim span grammars locally, validators in the cloud.** Doc 40 R5 and its gap G6 keep per-request grammars local; a cloud
   harness preset needs an explicit validator-only form of the same knob.
7. **Harness preset distribution and override UX.** Covers the manifest channel under D008, change cards, rollback, and custom
   harness presets with their "unqualified" badge. D022 and agent-runtime §13 describe the manifest but not this.
8. **The leading `why` as a per-model knob.** Doc 53 R7 already lists the conflict with doc 25 §4.3 and doc 38 §3.3; this doc adds
   that models may differ.
9. **Cascade route to a second stage.** Doc 53 §4.3's two-stage role binding; until it is decided, a harness preset's route is
   limited to same-model re-ask, user card and code default (the staged checker refuses `bound_second_stage`).
10. **Profiles beside harness presets** (added at review; doc 51 §6.1 item 1). Doc 51 §4 proposes a profile of probed facts per model,
    wire and endpoint, with tri-state evidence; a harness preset chooses within it. The default's `from_profile` thinking switch and
    the checker's template facts (thinking switch, `documents` path) need one record of that split, its layering and where each fact
    lives, extending D021's adapter and D022's Model Manager.

## 8. Tuning run 0: cheap levers on Qwen3.5-4B and Gemma 4 E4B (2026-09-28)

A first, pre-registered run of cheap preset levers, before the full protocol of §4 [V]. Same files, runtime (llama.cpp b11146
Vulkan), seeds and option orders as doc 46, so every arm pairs item by item with doc 46's records; drift checks reproduced doc 46 on
90 of 90 calls for both models. Harder menus (`pick-hard`, none + cards pooled, 180 calls) and whole-record Fill (36):

| Arm | Qwen3.5-4B Q4_K_M | Gemma 4 E4B QAT |
| --- | --- | --- |
| Baseline (doc 46) | 152/180; Fill 23/36 | 168/180; Fill 31/36 |
| Vendor non-thinking sampler (T 0.7, top-p 0.8, top-k 20, no penalty) | 152 (±0); Fill 22 | — |
| T 0.3 | 158 (+6; 4 menus better, 1 worse; sign p 0.375) | 168 (±0); Fill 29 |
| Short reason before the answer (`--why`) | 155 (+3) | 163 (−5) |
| Thinking, 256-token budget | 157 (+5; p 0.73); Fill 25; p50 about 8.3 s | 167 (−1); Fill 31; p50 about 7.9–9.4 s |
| Thinking, 1,024-token budget, 8 of Qwen's hardest menus only | 39/48 vs 27/48 baseline (+12; p 0.0625, Holm 0.31); p50 about 27 s | — |

- **No pre-registered rule was met** (a gain of at least 9 of 180 calls with a Holm-adjusted per-menu sign test p ≤ 0.05), so no
  lever is adopted. Qwen does not close the gap to Gemma under any cheap lever (best 158 < 164; best Fill 25 < 29) [V].
- **Thinking always hit the cap**: every 256-token call used the whole budget (265–276 generated tokens), so 256 tokens truncates
  these models' reasoning; the 1,024-token gain is on menus chosen for being hard (regression to the mean possible) and is too slow
  for interactive steps — at most a rare, visible "think harder" escalation [V; I].
- **Gemma's current preset stays**: `--why` cost it 5 calls, T 0.3 and thinking changed nothing [V].
- **Next** (doc 59): harness-side reasoning — extract-then-dispatch where code applies the counter-intuitive rules that cause most
  misses — rather than longer model thinking [I].
- Caveats: latency is indicative only (the GPU was shared with desktop applications); two samples of thinking arms per smoke gate;
  the experiment design was prepared from our own failure analysis of doc 46's records.

## Open questions

1. **Naming (owner or technical):** "harness preset", "prompt profile" (doc 14 §7) or another word, given four existing uses of
   "preset"? Doc 51 now uses "profile" for probed facts, so "model profile" should not name the harness preset. [I]
2. **Who writes the held-out sets (owner):** a separate human author, a different model family under the owner's review, or both?
   Doc 21 OQ2 asks the same for paraphrase cases. [U]
3. **Transfer within a family:** does a harness preset tuned on Qwen3.5-4B help Qwen3.5-2B or the UD file enough to be offered as
   "untested on this file"? [U]
4. **Promotion into the default (PR8):** is "wins on all three first targets" the right bar, or should one model's gain with no loss
   elsewhere suffice? [I]
5. **Runtime transfer (DG012):** does a harness preset tuned on Vulkan keep its gains on a user-downloaded CUDA build or on Ollama?
   Doc 46 found no detectable Pick difference between runtimes but a Fill lean. [U]
6. **User overrides:** which knobs should Settings expose at all, given that most users should never see a sampler? [I]
7. **Native tool calls locally:** does llama-server constrain a template's native tool-call format (Qwen's XML, Granite's JSON in
   `<tool_call>`) well enough to test it as an answer transport? [U]
8. **Extract-then-dispatch for every model:** if it wins for all first targets, should rule-bearing DecisionKinds drop the direct
   Pick altogether (PR8), making it doctrine rather than a knob? [I]
9. **Grader drift:** can EXPLAIN and text decisions rest on LLM graders at all, or do they need doc 44 §5.4 item 2's single fixed
   grader plus a human sample? [U]

## Sources

**Repository docs.** `AGENTS.md`; `docs/research/14-model-selection.md` §7, §9; `21-agent-doctrine.md` §1.1, §1.4, §2, §3.3, §4.1,
§7.1–§7.2, §8.2, §9, §12.3, §13.3, OQ2; `25-weak-model-friendly-campaign-harness.md` §2.3–§2.7, §3, §4.3–§4.6, §5.1–§5.2, §7.2–§7.3;
`38-harness-workflows.md` §3.2–§3.5; `40-token-economy.md` §4.1–§4.2 (R2–R8, G6); `44-local-model-qualification-spike.md` §2–§5;
`46-llamacpp-huggingface-and-ud-quant-spike.md` §1.3–§1.5, §2.1–§2.6, §3, §4.1; `47-small-model-landscape.md` §1.2, §3.1–§3.3, §6.2;
`48-cloud-providers-and-harness-uplift.md` §1.2, §2.3, §4.1–§4.4, §5, §7.4; `50-free-llm-services-and-cloud-first-screening.md`
§5.2–§5.7; `51-model-native-harnesses.md` §1.2, §2.1, §2.2, §2.4, §2.6, §3.4 (M3, M12, M13, M25), §4, §5.2, §5.5–§5.6, §6.1 and
`data/model-profiles.csv`; `53-how-small-can-we-go.md` §1.4, §2.4, §3, §4, §5; `docs/architecture/agent-runtime.md` §3, §5, §7,
§13; decisions D008, D010, D021, D022 (amendment item 5), D023 (decision 3, 5; amendment), D024, D027 (items 6, 7), D037, D044 (P5;
amendment), D045, D047, D048; design-gap requests DG006, DG012, DG015, DG019, DG020, DG021, DG022; `tools/local-qual/README.md`,
`run.py`, `suites/pick.json`, `suites/pick-hard.json`, `suites/fill.json`.

**Our records, re-analysed offline for this doc.** The stored call records of docs 44 and 46 and of the unfinished doc 49 run
(git-ignored), re-scored without new model calls: per-item results for HT03, HV01, HM04, HA03, HR04, HK01, HW03, HW04 and PW04; a
wrong-pick taxonomy (escape miss, false escape, lure-shaped, other); card effects per item; Fill span errors by kind; output tokens
per call; end-of-menu accuracy; and a search for CJK characters in every answer.

**Vendor cards and templates** (copies fetched 2026-09-27, read 2026-09-28; the Qwen3.5-4B and Gemma 4 E4B cards re-read online at
review on 2026-09-28):

- Qwen3.5-4B card ("Best Practices" items 1, 3 and 4: sampling sets, the multiple-choice `answer` field, no thinking in history;
  non-thinking mode), <https://huggingface.co/Qwen/Qwen3.5-4B>, and its chat template.
- Qwen3-4B-Instruct-2507 card (the same multiple-choice `answer` convention), <https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507>.
- Gemma 4 E4B card ("Sampling Parameters", "Thinking Mode Configuration"), <https://huggingface.co/google/gemma-4-E4B-it>.
- Granite 4.1 3B README, `chat_template.jinja` and `generation_config.json`, <https://huggingface.co/ibm-granite/granite-4.1-3b>;
  the repository README's "JSON as Output" example, <https://github.com/ibm-granite/granite-4.1-language-models>.
- IBM's prompt engineering guide for Granite 4.0 (documents channel, JSON output with `<schema>`, few-shot examples; the 4.1
  template keeps the same documents wording),
  <https://github.com/ibm-granite/granite-4.0-language-models/blob/main/Granite%204.0%20Prompt%20engineering%20guide%20v2.md>.
- Unsloth's Granite 4.1 guide (temperature 0.0, top_p 1.0, top_k 0; minimum context 16,384) [V-3p],
  <https://unsloth.ai/docs/models/ibm-granite-4.1>.
- Pinned GGUF repositories: <https://huggingface.co/unsloth/Qwen3.5-4B-GGUF>, <https://huggingface.co/unsloth/gemma-4-E4B-it-qat-GGUF>,
  <https://huggingface.co/ibm-granite/granite-4.1-3b-GGUF> (commits and hashes as in docs 46 and 53).

**Papers** (abstracts read 2026-09-28):

- Sclar, Choi, Tsvetkov, Suhr, "Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design",
  [arXiv 2310.11324](https://arxiv.org/abs/2310.11324).
- Voronov, Wolf, Ryabinin, "Mind Your Format: Towards Consistent Evaluation of In-Context Learning Improvements",
  [arXiv 2401.06766](https://arxiv.org/abs/2401.06766).
- He, Rungta, Koleczek, Sekhon, Wang, Hasan, "Does Prompt Formatting Have Any Impact on LLM Performance?",
  [arXiv 2411.10541](https://arxiv.org/abs/2411.10541).
- Khattab et al., "DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines",
  [arXiv 2310.03714](https://arxiv.org/abs/2310.03714).
- Karnin, Koren, Somekh, "Almost Optimal Exploration in Multi-Armed Bandits", ICML 2013, PMLR 28(3):1238–1246,
  <https://proceedings.mlr.press/v28/karnin13.html> (Sequential Halving, §4 of the paper).
- Li, Jamieson, DeSalvo, Rostamizadeh, Talwalkar, "Hyperband: A Novel Bandit-Based Approach to Hyperparameter Optimization",
  [arXiv 1603.06560](https://arxiv.org/abs/1603.06560).

Papers cited through sibling docs keep those docs' verification: HAL and "When Thinking Fails" (doc 48 §5.5); OLMES, symbol binding
and PriDe (doc 53 S53, S55, S57); llama.cpp issue #29006 (doc 53 S24); Wilson, McNemar, Holm and bootstrap methods (docs 44, 46).

## Verification notes

### 2026-09-28, author checks at write-up

- **Re-derived from stored records** (no model calls), with a script kept with the run tooling:
  - every per-item count in §1.1 and §6: HT03, HV01, HM04, HK01 and HW03 per arm and condition; the far escapes HA03 and HR04;
  - the card-effect table;
  - the lure-shaped share, where a wrong real option counts as lure-shaped if it shares strictly more content words with the
    request than the answer does; 25 of 162 `pick-hard` distractors are like that;
  - the Fill span taxonomy and `size` counts;
  - output tokens per pick; end-of-menu accuracy with and without the presence penalty;
  - Chinese characters in 2 of 36 Ollama Qwen Fill records (F11) and in 0 of 72 llama.cpp Qwen Fill records;
  - the preliminary doc 49 rows.

  Suite-level figures quoted from docs 44 and 46 match the same records.
- **Checked by script:**
  - the draft harness presets validate against the draft schema, both alone and merged onto the default;
  - three negative controls are refused;
  - each draft decision table in the dispatch suite yields its item's `pick-hard` answer from the expected fields.
- **Read at the source:**
  - the four paper abstracts and the Hyperband abstract (2026-09-28);
  - Sequential Halving's definition in the Karnin et al. PDF (§4, "we split the given budget evenly across log2 n elimination rounds
    … we rule out the worst half of the arms");
  - the vendor sections quoted in §1.3, from copies of the cards fetched on 2026-09-27, not re-fetched;
  - the Qwen3.5 template's empty think block;
  - Granite's `documents` wording and its tool-call format;
  - Gemma's statement that E2B and E4B emit no empty thought block.
- **Not verified:**
  - any tuning arm, any latency or call count in §4.6 (arithmetic from doc 46's p50s);
  - whether llama-server constrains native tool calls;
  - any held-out result. No held-out set exists yet.
- **Limits:**
  - arms of one family are near-copies of one model, and n is 12 per family-item cell, so the §1.1 item tables describe and do
    not test;
  - the lure metric is a crude word-overlap count, and HK01 shows a semantic echo it cannot see;
  - the doc 49 rows may change.
- **Folding steps, not done here:** a row for this doc in `docs/README.md`; the pointers in D022's and agent-runtime's
  setup-identity text once candidate 1 in §7 is filed.

### 2026-09-28, independent review

Scope: this doc against the staged draft harness presets (0.2.0), their schema (draft 2), the checker and the tuning plan; the
invariant of §1.4; the sourcing of vendor claims; the overfitting controls; hygiene. No model was run.

- **Fixed in this doc:**
  - D048 (accepted the same day) and doc 51 (now in the tree) were described as absent; the header names both, and §1.3 gains a
    reconciliation with doc 51, including one correction reported for doc 51 §5.5: doc 46 ran Qwen's thinking-mode precise-coding
    sampler (T 0.6, top_p 0.95, top_k 20), not the card's non-thinking set.
  - §2.1 marked computed Picks as the default for judgement fields; the default preset and docs 44 and 46 use in-record bands. It
    now says so and adds the knobs the schema already had (text envelope, JSON-array menus, exemplar selection, placement of the
    pack's system text) and where compact grammars, validator-only modes and native tool calls may run.
  - §3.3's outline and excerpt showed draft 0.1.0 (null template hash, T 0.6, computed judgement fields); both now match the 0.2.0
    files, the knob ledger is described, and the checker's rules are listed.
  - §4.1, §4.3 and §4.6 described today's suites only, "up to eight arms" per step kind and 2,300–2,400 tuning calls per model; they
    now match the staged plan: the two pools' tune halves, the interim held-out look, families of two to four arms searched against
    the incumbent, and the plan's per-model budgets (2.6, 1.9 and 1.0 GPU hours; dispatch 72 held-out calls, not 144). The TL;DR
    follows.
  - §6's hypothesis tables lagged the drafts: Qwen's dispatch on `campaign.node_type`, Qwen's span-only start in Fill, Gemma's
    vendor sampler as a Pick arm, Granite's `documents` channel on Pick as well as EXPLAIN, and Granite's H-R7 and H-R8 were missing
    or different. Each row now says whether the draft starts from it or keeps it as an arm.
  - §5 promised "at most about ten knobs" per harness preset while the drafts change 17 to 24 ledger entries; it now states ten as
    the aim for tuned presets, with PR7 pruning.
  - §3.2 records the header's file type where the file name misleads (Gemma's QAT file); §1.3 and Sources cite the Qwen card's item
    numbers, the Granite README's "JSON as Output", IBM's Granite 4.0 prompt guide and Unsloth's Granite 4.1 page; §7 gains item 10.
- **Overfitting controls added before any run:** the prompt fragments, exemplar banks, fitted thresholds and calibration, and one
  decision table per overridden DecisionKind are hashed into the plan before each held-out look; held-out dispatch items are scored
  with those per-kind tables, never with tables written per item (the draft suite's tables are per item, so an item's answer could
  shape its own table); dispatch overrides are judged together, with PR4 per DecisionKind; an interim look that changes the
  candidate turns the interim half into tuning material.
- **Fixed in the staged files** (outside the tree; regenerated from their builders, never hand-edited):
  - Presets (short SHA-256: default `e0ef258ce646`, Qwen `80064c4526c0`, Gemma `77e783b05924`, Granite `ee1e40dccbbb`): Q-A2's leading
    `why` now carries the 200-token cap it needs (at 64 tokens PR1's truncation guard would fail the arm for a harness reason); R-C2
    (IBM's one-sample recipe) now sets voting K = 1 instead of only describing it, and no longer promises a "blind retry" that no
    repair value expresses; G-D2 and R-D2 were `grid` arms the plan never schedules and are now reserves; the Granite evidence names
    IBM's guide as the Granite 4.0 guide and lists its URL.
  - Schema (`0bd71264d6cd`): `layout.system_message` offered `none`, which would let a harness preset drop the pack's system text; it
    now offers only a placement (`pack`, `fold_into_first_user`). No draft used `none`.
  - Checker: new loader rules for what §1.4, §2.3 and §7 state in prose (no `bound_second_stage` route; native tool calls and
    validator-only schema modes on cloud endpoints only; sidecar grammars local only); every arm checked with all its coupled values
    applied together, refusing an arm that sets one knob to two values; the plan's arm lists and recorded preset hashes checked
    against the ledgers. Negative controls: 8 → 14, all refused.
  - Tuning plan (`0d4a63aaba75`): the freezing precondition, the dispatch rule, the interim-look rule, the arm-id convention and the
    corrected reserves; budgets unchanged and re-added by script (8,557 tuning, 1,343 interim and 5,582 sealed calls; 5.6 hours).
- **Checked by script:** all four drafts pass the checker alone, merged and per arm; all 14 negative controls are refused; the plan's
  stage call counts and minutes re-add to its totals; the recorded hashes of the five tree suites and three staged suites match the
  files; the builders reproduced the pre-review files byte for byte before any change.
- **Re-read at the source (2026-09-28):** the Qwen3.5-4B card's four sampling sets, the presence-penalty sentence ("may occasionally
  result in language mixing and a slight decrease in model performance"), the `answer` field sentence (Best Practices item 3) and
  thinking on by default; the Gemma 4 E4B card's sampler "across all use cases" and "For all models except for the E2B and E4B
  variants, if thinking is disabled, the model will still generate the tags but with an empty thought block"; from the stored
  copies, Granite 4.1's `generation_config.json` (token ids only), the template's `documents` wording and the absence of any thinking
  branch, the README's JSON system sentence with `<schema>` tags, and Unsloth's temperature 0.0, top_p 1.0, top_k 0.
- **Invariant:** no draft knob or alternative names a model, grants a shape, adds a tool, raises K above 5 or R above 3, or moves
  untrusted text; every prompt change is an id. The `documents` channel carries shipped cards only, which the checker cannot see;
  the loader must enforce it from the cards' trust labels (doc 21 §9.1).
- **Not verified:** whether llama-server forwards `chat_template_kwargs.documents` (stage S0 decides); the Granite timings, which are
  scaled from Ollama; the Qwen3-4B-Instruct-2507 card, not re-read.
- **Hygiene:** no local path, user name or private project in this doc, the drafts or the plan (searched by script).
- **Reported, not fixed here:** doc 51 §5.5 (above); the `docs/README.md` row for this doc is still missing.
