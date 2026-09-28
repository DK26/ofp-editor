# Purpose-specific ML components: small brains that take work off the LLM

Research doc 58 for Plotroom (`ofp-editor`). Research date: 2026-09-28. Audience: contributors and LLM coding agents. This file is
meant to be read on its own.
Question answered (owner, 2026-09-28): "Would it make sense to put some small LM / deep-learning brains in different parts of our
harness or editor, to reduce the LLM's responsibilities and off-load to purpose-specific AI elements?"

**Status: draft — proposals only.** No model was loaded or run for this doc. Every verdict, tier, latency class and call estimate below
is a proposal [I] unless a source is cited. The machine-readable inventory of all 64 touchpoints is
`docs/research/data/ml-components.csv`.
**Epistemic legend** (doc 14's): **[V]** verified against the cited primary source; **[V-vendor]** / **[V-author]** the publisher's own
number about its own work; **[V per doc N]** taken from a sibling doc; **[I]** our inference or proposal; **[U]** unknown. Web sources
are cited as [S1]…[S45] and listed under §Sources.
**Relation to sibling docs.** Doc 16 sets the order of deciders, the `Selector` seam and the evidence bar; doc 53 (draft) the tiny-model
floors, one-pass scoring, cascades and the open encoder-runtime question (§4.9); doc 55 (draft) per-model presets; doc 47 the helper
models; doc 40 the token economy and its "what we will not do" list; doc 30 and D027 the knowledge stack; doc 22 the plugin tiers;
doc 57 (in progress) token efficiency and context rebuilding; doc 52 free-tier rate limits and UX. D008, D010, D011, D022, D023,
D024, D027, D037, D047 and D048 govern. This doc changes no decision.
**Names.** A **component** is any purpose-specific piece that is not the general generative model: a classical algorithm with fitted
tables, a non-generative model (embedder, reranker, extractor, checker, classifier) or a specialist generator (translation, speech).
**Session model** keeps doc 53's meaning (the one general model a setup keeps loaded). The **T0 path** is a feature with AI off (D023
decision 1). Touchpoint ids (A1…L4) are this doc's own and match the CSV.
**Hygiene.** Public sources only; no game content, no private projects, no local paths.

## TL;DR

- **Yes, but narrowly, and mostly not as new brains.** Of 64 touchpoints in the editor and the harness, plain code is the right owner
  for 40, classical statistics for 9 (BM25, n-gram language ID, Hunspell spelling, MinHash, Drain log templates, Bayesian tables), a
  small model for 10, a specialist generator for 3 (translation, speech synthesis, speech recognition) and the general LLM for 2
  (creative prose; Compose, Draft and scripts) [I]. The harness already moves work off the LLM by design (doc 16 §3.1, D027,
  agent-runtime §6): 14 of the 16 touchpoints where an LLM works today can move to code, statistics, a narrow Pick or a specialist.
- **The best small brain is the model already loaded.** Seven of the ten small-model rows are narrow Picks on the session model:
  one-pass letter scoring plus a per-model calibrator (doc 53 §4.2) replaces K = 3 voting and gives a real confidence, with no new
  artifact (priority P0). Beyond the three specialists, new model artifacts earn a place in three roles only: a span extractor, an
  EXPLAIN faithfulness checker and a tiny CPU Pick model for CPU-only machines, Preview time and free-tier users.
- **Biggest new offloads, ranked** [I on V]: (1) an AI-off **text-hygiene layer**: spelling (spellbook with Hunspell dictionaries),
  English grammar (Harper), language ID (lingua), all pure Rust and millisecond-fast; (2) **one BM25 index** as the shared retrieval
  baseline for Standing Orders, troubleshooting, mod search and mission search; (3) **offline draft translation** with Mozilla's
  Firefox Translations models (about 31M parameters and 32 MB per direction, all seven non-English engine languages, MPL-2.0) through
  `fxtranslate` (a Rust re-implementation whose native fast path is a vendored C++ int8 kernel, so it belongs in the helper process),
  which takes first-draft translation off the LLM entirely; (4) code span candidates, then a GLiNER-class extractor; (5) a code
  claim matcher, then a small checker, on EXPLAIN.
- **The contract for every component** (§1.2): typed input and output, one declared consumer, advisory or pre-filtering only (it never
  admits content or decides facts, ids or permissions), a code-owned fallback so the feature works with it off, qualification against
  the simple baseline on a frozen suite, a visible "answered by" record with a kill switch, an optional pinned download the user
  starts, and no agent-tool reach.
- **The evidence favours this order** [V]: learned routers rarely beat simple baselines and can be steered by their input text
  [S1–S4]; BM25 is the robust out-of-domain baseline, and rerankers can lower recall at large K [S10, S12]; guard classifiers over-flag
  security-flavoured benign text, which military briefings are [S13]; calibration drifts under shift and 4-bit quantization [S14]. The
  production successes (JetBrains full-line completion, IntelliCode, Smart Reply) all have ML re-rank or filter a complete deterministic
  list that survives the model's removal [S16–S18].
- **Runtime: three tiers behind one seam (proposal, §4).** (S) The llama-server sidecar already serves embedders, rerankers,
  BERT/XLM-R/ModernBERT classifier heads, fill-in-the-middle and generative translators; it is the default. (I) In the editor process,
  only pure-Rust code under an admission rule: lingua, spellbook, Harper and a BM25 index (each with its C-pulling or
  all-languages default features off), and, only if spike S-ENC admits it, an own static-embedding encoder. (H) A supervised helper
  process for native code: ONNX Runtime through `ort` (built without telemetry) for DeBERTa-family extractors and NLI models, HHEM,
  LettuceDetect, Piper and Kokoro voices, and `fxtranslate` with its C++ kernel. This proposes a shape for doc 53 §4.9's open
  encoder-runtime question; it decides nothing, and a neural encoder in tier I would depart from the architecture's "embedded
  inference always out of process" resolution, so both stay with the owner (OQ2, design-gap candidate 2).
- **What it changes for Wilco** [I]: with a local session model, a Pick costs about 1.2 calls instead of 3. With a tiny local stage
  plus free cloud, a 30-minute session needs about 4–6 cloud calls instead of doc 53's ~12 (about 60 today), so a free quota of 50 a
  day covers about 8–12 sessions. Draft translation needs no LLM call. Campaign text (~428 calls) is untouched, because authorship is
  the LLM's real job. For cloud-only users the saving is about 10%; their lever is code (adaptive K, DG021), not components.
- **Do not do** (mostly restating decisions, §2.4): learned routers or silent cascades; a reranker cutting catalog menus; embedders
  selecting cards; semantic response caches; code LMs as Teller's default completion; ML grading in Drill; neural safety or injection
  classifiers on user content; vision models where WRP objects exist; learned shot aesthetics; fine-tuned helpers in v1.
- **Experiments first (§6), pre-registered, CPU-first, after doc 49's run:** E1 card retrieval (BM25 vs embedder vs hybrid vs LLM
  choice); E2 a reranker pre-filter vs facet menus for large class catalogs (expected to confirm facets); E3 extractor vs LLM span
  Fill; E4 zero-shot and decision-model routing vs the letter-scored LLM Pick; E5 a radio-voice prototype with Piper and Kokoro. A
  runtime spike (S-ENC) runs beside them.
- **Training our own small task models would revise D027 item 6 and D048 decision 3.** §7 sets out costs, data sources, the licence of
  generated data and upkeep; Appendix A drafts the owner question. This doc does not decide it.

## 1. The principle: code first, then a small specialist, then the LLM

### 1.1 The ladder of deciders, extended to components

Doc 16 §3.1's rule stands: **use the cheapest decider that is always right.** This doc splits its "learned chooser" rung by what the
component is, and adds the specialists [I]:

| Rung | Decider | Examples in Plotroom | Typical cost | Runs in |
| --- | --- | --- | --- | --- |
| 0 | The user's gesture | Toolbar, context menu, palette, a click on a top-2 card | none | UI |
| 1 | Code and domain rules | Facts, geometry, validators, templates, facet menus, seeds, fingerprints | < 0.1 s (L0) | Editor |
| 2 | Classical statistics, no neural net | BM25, n-gram language ID, Hunspell, MinHash, Drain templates, Bayesian tables, calibration fits, kNN over typed metrics | milliseconds | Editor (pure Rust) |
| 3 | The session model, narrowly | One-pass letter scoring over a code-built menu; one Pick per closed field | 0.3–1.1 s on the reference GPU [V per doc 44/46] | Sidecar |
| 4 | A pinned, off-the-shelf non-generative model | Embedder, reranker, span extractor, faithfulness checker, NLI flag | about 0.05–0.5 s per item on CPU [I] | Sidecar or helper |
| 5 | A pinned specialist generator | Machine translation, speech synthesis, speech recognition | per sentence or line | Helper, sidecar or plugin (editor only for a qualified pure-Rust path, §4.4) |
| 6 | The general LLM | Creative prose, Compose, Draft, scripts, paraphrased explanations | seconds | Sidecar or cloud |
| 7 | Heads or adapters Plotroom trains itself | None in v1 (D027 item 6; §7) | — | — |

Rungs 0–2 need no model and work offline; some need data the user supplies, such as spelling dictionaries (§4.7). Rungs 3–6 are
optional and user-bound (D023 decision 1, D024). Doc 16's rule applies
to every rung above 2: **if removing the component would not change the accepted result, it does not ship.**

### 1.2 The component contract (proposal)

1. **Typed and single-purpose.** One input type, one output type, one declared consumer seam (`Selector`, `Retriever`, `Ranker`,
   `Extractor`, `Checker`, `Flagger`, `Translator`, `Voice`, `Transcriber`). No model consumes another model's raw output: a typed
   code validation always sits between them, which avoids the "correction cascade" debt Sculley et al. describe [S21].
2. **Advisory or pre-filtering only.** A component may order, shortlist, flag, draft or propose. It never admits content and never
   decides facts, ids, geometry, permissions or acceptance (doc 16 §3.3). A probability is never permission; a flag is dismissible as
   intentional (D011).
3. **Code-owned fallback.** The T0 path works with the component off, and removing it degrades gracefully. When Microsoft retired
   IntelliCode's ranking, its notice said "You will still get language-server powered completions" [S17]; that is the shape to copy.
4. **Qualified against the simple baseline.** Frozen suites with in-distribution, hard-benign (military vocabulary), shifted (mods,
   new islands, Czech/Polish/Russian phrasing) and adversarial (injected briefing text) splits. The component must beat BM25, kNN,
   `RuleSelector` or the code rule on paired cases (doc 16 §5; doc 21 §2.2). Per-kind bars are in §4.9.
5. **Visible.** Every call writes a journal record (§4.10); the UI shows "answered by" (component, artifact, score, threshold,
   outcome); each component has a kill switch; enabling one is a visible setting, never a silent swap (D010; D023 decision 3; D024).
6. **Optional and pinned.** Weights are downloads the user starts in the Model Manager, pinned by repository, revision, file and
   SHA-256 (D008, D022, D023 decision 1). D037's licence rule applies to components as to generative models; badges come from
   Plotroom's own instruments.
7. **Product-scoped.** Components are harness code steps or editor features, never agent tools, and add no network, file or process
   reach (AGENTS.md). Untrusted text reaches them only as quoted data, and never as an unquoted routing input (§1.3, router steering).
8. **Budgeted.** Each component states its latency class (doc 53 §1.1), its peak memory on the reference CPU, and whether it may run
   while Preview holds the GPU (D018).

### 1.3 What the evidence says about small brains

- **Routers: simple baselines win** [V]. LLMRouterBench (over 400K instances, 21 datasets, 33 models) finds several recent routers
  "fail to reliably outperform a simple baseline" [S1]; a tuned kNN router (k = 100) loses 2.63 points out of distribution against
  3.33–6.67 for the learned routers tested [S2]; as the cost budget grows, routers "systematically default to the most capable and most
  expensive model even when cheaper models already suffice" [S3]. "Confounder gadgets", query-independent token
  sequences, reroute almost every query, and perplexity filtering does not stop them [S4]. **Plotroom:** `RuleSelector` plus menu
  scoring (doc 16, D023 decision 5); a downloaded briefing must never be able to steer routing or force a paid escalation.
- **Silent routing fails in public** [V]. At the GPT-5 launch the autoswitcher broke "and the result was GPT-5 seemed way dumber";
  within days the manual picker returned. GitHub Copilot's Auto model selection shows the chosen model [S5]. **Plotroom:** external
  confirmation of D023 decision 3; an "answered by" chip on every decision card.
- **Small-first hybrids work, trained heads do not transfer** [V]. A SetFit hybrid that defers to an LLM on uncertainty stays within
  about 2% of LLM accuracy at about half the latency [S6]. But "a classifier trained on one app's intents scores 0% on a new app's
  intents while the schema-prompted LLM serves both at ~94%" [S7]. **Plotroom:** menus change with plugins, mod sets and target
  profiles (D003, D007, doc 42), so prompt-scored menus beat trained heads for routing.
- **Filter, then let the model choose among few** [V]. Letting an LLM rerank only the hard samples a small model flags gained 2.4 F1
  points [S8]; agreement-based cascades of existing models cut price per request 2–25× against earlier LLM cascades, with no trained
  router [S8]. **Plotroom:** code proposes, a model chooses among ≤ 7, never the reverse.
- **Specialists win with a data flywheel** [V]. Roblox built its PII classifier on manually reviewed and labelled production data,
  evaluates it on more than 47,000 real-world samples and feeds adversarial patterns back into training on an ongoing basis;
  Microsoft's 60M FLAME beat 175B Codex on Excel formulas in 10 of 14 settings with a domain corpus [S9]. The PCGML survey names
  small datasets as the recurring blocker [S9]. **Plotroom:** no telemetry and no fine-tuning in v1, so no flywheel; off-the-shelf
  components only.
- **Retrieval over parameters, lexical first** [V]. Retrieval-augmented small models beat much larger unaided ones on long-tail facts
  [S10]; in BEIR, BM25 is "a robust baseline" while dense retrievers often fall below it out of domain [S10]. Sourcegraph moved Cody
  Enterprise from embeddings to adapted BM25; Anthropic's failed retrievals fell from 5.7% to 2.9% with contextual embeddings plus
  contextual BM25 and to 1.9% with reranking added [S11]. **Plotroom:** engine knowledge is extreme long tail (0 of 24 without
  cards, doc 44); BM25 plus aliases first, embeddings only fused with it, because class names and ids are exact tokens.
- **Rerankers can hurt** [V]. Scoring more candidates with a pointwise cross-encoder first helps, then hurts: in 53.3% (academic) and
  44.4% (enterprise) of the cases where a small K helped, a larger K fell below retrieval alone [S12]. **Plotroom:** a fixed K ≤ 20.
- **Guard classifiers are brittle and over-defend** [V]. Prompt-Guard-86M was bypassed 449 of 450 times by spacing out characters;
  a detector with F1 0.98 in-split misclassified about a third of external security-adjacent benign prompts; NotInject shows
  over-defence near 60% accuracy [S13]. CaMeL instead fixes control flow from the trusted query [S13]. **Plotroom:** mission text is
  security-adjacent by nature ("attack", "destroy", "ignore orders"), so no guard classifier in any admission path.
- **Confidence drifts** [V]. Uncertainty quality degrades with shift and temperature scaling can worsen it [S14]; 4-bit GPTQ lowered
  the confidence models assign to true labels, with calibration error rising on several model–task pairs [S14]. **Plotroom:**
  calibrate per model file, quant and DecisionKind; report shifted splits; thresholds route, never admit.
- **Exact reuse only** [V]. Static similarity thresholds in semantic caches "do not give formal correctness guarantees" [S15].
- **The production shape** [V]. Copilot's client gates calls with a small logistic filter, a silent gate whose only error is "nothing
  shown" [S16]; JetBrains ranks heuristic candidates with CatBoost, and its 100M local line-completion model is filtered by the IDE's
  own analysis (acceptance about 38% against 27%) [S17]; Smart Reply picks from a vetted response set with forced diversity [S18];
  Ghostwriter shows writers two drafts [S18]; Apple's small on-device model produced false news summaries and now shows a warning
  that summaries may change meaning [S19]. **Plotroom:** deterministic lists first, ML orders or filters, and small models never
  paraphrase untrusted text into authoritative-looking summaries.
- **Measure acceptance, count the debt** [V]. Acceptance of shown suggestions best predicted perceived productivity [S20]; every
  extra model adds entanglement and undeclared consumers [S21]; "Don't be afraid to launch a product without machine learning" [S21].
  NVIDIA's "40–70% of agent calls could go to SLMs" is an estimate whose recipe needs call logs and fine-tuning [S22]; Plotroom
  already has its decision points enumerated and typed (doc 53 DP-01 to DP-21).
- **Solvers and typed code dispose** [V]. Fast Downward solves Blocksworld at 100% in about 0.12 s per instance, where o1-preview
  reaches 23.63% on 20–40-step problems [S23]; ML-generated game levels need a deterministic repairer [S24]; LLM refactoring
  suggestions were up to 76.3% hallucinated until static analysis filtered them [S25]; explanations raised acceptance of AI advice
  regardless of its correctness [S26]. **Plotroom:** geometry, routes and plans stay code; confidence is shown as "unsure: choose
  between these two", not as a persuasive model-written reason.

## 2. Touchpoint map

### 2.1 Summary

| Recommended owner | Rows | Owned by an LLM today | By code today | Not built today |
| --- | --- | --- | --- | --- |
| Algorithm (code) | 40 | 2 (C4, C6) | 37 | 1 (B12) |
| Statistics (fitted tables, no neural net) | 9 | 1 (C2) | 4 | 4 (F3, G1, G2, K1) |
| Small model (7 of 10 are narrow Picks on the session model) | 10 | 10 | 0 | 0 |
| Specialist generator (translation, TTS, ASR) | 3 | 1 (G4) | 0 | 2 (H1, H2) |
| General LLM | 2 | 2 (B15, B16) | 0 | 0 |
| **Total** | **64** | **16** | **41** | **7** |

Among the small-model rows, only three new kinds of model artifact appear: the span extractor (B5, after code candidates), the
EXPLAIN checker (C3, after the claim matcher) and the tiny CPU model (A2, B3 and F4, on CPU-only machines). The three specialist rows
add translation, voice and speech-recognition models (G4, H1, H2). Embedders, rerankers and zero-shot flags appear only as optional
tiers behind BM25 or code signals.

### 2.2 The map

"Today" is the current design, not shipped code. Classes are doc 53 §1.1's latency classes. Priorities: **P0** now, no new artifact;
**P1** v1, no new runtime; **P2** after the runtime decision or in v1.x; **P3** later or as a plugin; **keep** the designed code path
stays; **shadow** research arms only. Full rows, candidates, risks and sources are in the CSV.

| Id | Touchpoint | Today | Verdict and method | Class | Priority |
| --- | --- | --- | --- | --- | --- |
| A1 | Slash commands, palette, context menus, toolbar | code | Algorithm: the gesture chose; fuzzy matching (nucleo or own) | L0 | keep |
| A2 | Intent Fill, closed fields (DP-01) | LLM | Small model: alias rules, then one Pick per field; judgement fields computed or asked | L1 | P1 |
| A3 | Workflow routing, `Selector` (DP-02) | LLM | Small model: `RuleSelector` + BM25, then letter scoring; learned arms in shadow | L1 | P1; shadow |
| A4 | Clarification choice (DP-03) | code | Algorithm: code knows the null fields | L1 | keep |
| A5 | Chat stagnation and loops | code | Algorithm: (tool, args, result, revision) fingerprints | L0 | keep |
| A6 | Free-chat context growth | code | Algorithm: rebuild from typed state (doc 57); validated summary only for free chat | L0 | keep |
| B1 | Large catalog menus | code | Algorithm: facet steps, no reranker | L0 | keep |
| B2 | Fact-bearing Picks (DP-08) | code | Algorithm: filter by the known fact; no model tier | L0 | keep |
| B3 | Pick confidence, re-ask, cascade | LLM | Small model: one-pass letter scoring + per-model calibrator | L1 | **P0** |
| B4 | Enum Fill (DP-12) | LLM | Small model: one Pick per field, ints in ≤ 7 bands | L1–L2 | P1 |
| B5 | Fill spans: place, target | LLM | Small model: code candidates + Pick; later GLiNER-class extractor | L1 | P1; P2 |
| B6 | Lint-fix choice (DP-09) | LLM | Small model: Pick among code-ranked FixIds | L1 | P1 |
| B7 | Ordering admitted candidates (DP-11) | code | Algorithm: code signals; rerankers and judges in shadow | L3 | keep |
| B8 | Exemplar retrieval | code | Algorithm: metadata match; embedder tier only after E1 | L0 | keep |
| B9 | Card, primer, skill selection | code | Algorithm: step-declared (D027 item 7); no embedder | L0 | keep |
| B10 | V-text checks | code | Algorithm: exact checks | L0 | keep |
| B11 | Anachronism, era voice | code | Algorithm: dated lexicon; optional zero-shot flag | L0 | keep; P3 |
| B12 | Dialogue voice consistency | none | Algorithm: stylometry vs the bible; embeddings order only | L3 | P2 |
| B13 | Duplicates, novelty | code | Statistics: n-gram, MinHash/SimHash, graph hashes, Vendi | L0–L4 | keep |
| B14 | Pick collapse | code | Algorithm: seeds and strata | L0 | keep |
| B15 | Creative text (DP-17/18) | LLM | **LLM**: 2–4B candidates, ≥ 12B or cloud for quality | L3–L4 | keep |
| B16 | Compose, Draft, scripts | LLM | **LLM**: ≥ 8B or cloud behind Teller | L3–L4 | keep |
| C1 | Standing Orders search, "What is this?" | code | Statistics: aliases + BM25; `NotInManual` without a model | L0 | P1 |
| C2 | Symptom → playbook (DP-04/05) | LLM | Statistics: BM25 over authored symptom lines, then a Pick of ≤ 7 | L1–L2 | P1 |
| C3 | EXPLAIN a finding (DP-14) | LLM | Small model: card; sentence Pick; ≥ 3B paraphrase; claim matcher then checker | L2 | P1; P2 |
| C4 | "Explain this mission" | LLM | Algorithm: MissionAnatomy view; optional cited walkthrough by ≥ 8B | L0 | keep |
| C5 | Drill checking and grading | code | Algorithm: validator predicates, multiple choice | L0 | keep |
| C6 | Drill tutor | LLM | Algorithm: authored hint ladder; optional rung Pick and one line | L1–L2 | keep |
| C7 | Readiness, Path Explorer, wizards, compile | code | Algorithm: model policy `Forbidden` | L0 | keep |
| D1 | Teller completion and hover | code | Algorithm: catalog + idiom-frequency prior; optional filtered FIM ghost text | L0 | keep; P3 |
| D2 | `did_you_mean` | code | Algorithm: edit distance over profile names | L0 | keep |
| D3 | Script error explanation | code | Algorithm: model-shaped diagnostics + card; optional phrasing as C3 | L0 | keep |
| D4 | Lift recognisers, pack detection | code | Algorithm: token fingerprints | L0 | keep |
| D5 | Command risk, Preview gate | code | Algorithm: risk rows, fail closed | L0 | keep |
| D6 | Injection text in missions | code | Algorithm: structural defence; no classifier | L0 | keep |
| E1 | Places, settlement clusters | code | Algorithm: density clustering over WRP objects | L0 | keep |
| E2 | Sites, cover, LOS, LZ, ambush spots | code | Algorithm: geometry; model Picks among sites | L0–L1 | keep |
| E3 | Routes, convoys, patrols | code | Algorithm: A*/Dijkstra, doctrine tables, seeds | L0 | keep |
| E4 | Populate town (DP-07) | LLM | Small model: code placement, composition Pick | L1 | P1 |
| E5 | Cutscene shot planning | code | Algorithm: toric candidates, hard checks | L0–L1 | keep |
| E6 | Atmosphere formulas | code | Algorithm: ported engine formulas | L0 | keep |
| E7 | Preview screenshot critique | code | Algorithm: pixel checks; optional local vision LM on opt-in | L4 | keep; P3 |
| F1 | Campaign taste Picks (DP-06) | LLM | Small model: one-pass Pick, show-top-2 | L1 | P1 |
| F2 | Balance lab, auto-tune | code | Algorithm: simulation and bounded search | L4 | keep |
| F3 | Outcome-table calibration | none | Statistics: Dirichlet-multinomial update with counts | L4 | P2 |
| F4 | Play-tester personas (DP-10) | LLM | Small model: scripted baseline; ≤ 1B CPU model for narrative QA | L4 | P2 |
| F5 | Surprise me, Seed Atlas | code | Algorithm: k-NN over typed metrics | L0 | keep |
| F6 | Content-policy advisories | code | Algorithm: typed vocabulary checks, host flags | L0 | keep |
| G1 | Spelling and grammar | none | Statistics: spellbook + Hunspell, Harper (EN), glossary | L0 | **P1** |
| G2 | Language ID | none | Statistics: lingua + Unicode-script check | L0 | **P1** |
| G3 | Code page, byte limits | code | Algorithm: `byte_len_in` | L0 | keep |
| G4 | Translation (translator role) | LLM | Specialist: Firefox models for drafts; Hy-MT2-1.8B for glossary lines | L4 | P2 |
| H1 | Radio voices (TTS) | none | Specialist: Piper allowlist, Kokoro (EN/FR/IT/ES) | L4 | P3 |
| H2 | Speech recognition | none | Specialist: Whisper-class | L4 | P3 |
| H3 | Audio post-processing | code | Algorithm: radio chain, LUFS, `.lip` | L0–L4 | keep |
| I1 | Class role inference | code | Algorithm: ordered rules and adapters | L0 | keep |
| I2 | Mod directory search | code | Statistics: BM25 and filters | L0 | P1 |
| I3 | Remap to installed mods | code | Algorithm: tiers and ratios | L0 | keep |
| J1 | Log and crash triage | code | Statistics: engine templates + Drain for unknown lines | L0 | P2 |
| K1 | Search across the user's missions | none | Statistics: facets + BM25; embedder only after it beats BM25 | L0–L1 | P2 |
| L1–L4 | Hardware fit, token counts, cost preview, plan estimates | code | Algorithm | L0 | keep |

### 2.3 Where plain algorithms win, and why

- **Facts, ids, geometry, permissions, acceptance** (B2, D5, E1–E6, F2, I1, I3): doc 16 §3.3 forbids a model there, and the code is
  exact.
- **Per keystroke and per commit** (A1, C1, D1, D2, G1–G3): the L0 budget of under 0.1 s rules out any model call, local or cloud.
- **Exact checks** (B10, D6, G3): a learned check adds no admission value and makes a pass non-reproducible.
- **Too little data** (F3): a handful of Preview runs per archetype supports a Bayesian table update, not a learned model.
- **The data already holds the answer** (E1): the WRP object list carries what a segmentation net would have to guess from the texture.
- **Reproducibility** (C5, C7): Drill and readiness verdicts must be the same for every learner and every rerun.
- **Planning** (E3, F2): solvers beat LLMs on long-horizon plans and paths [S23].

### 2.4 Do not do

| Item | Why | Source |
| --- | --- | --- |
| Learned routers; silent cascades | Rarely beat simple baselines; steerable; silent switches look like "the AI got dumber" | doc 40 §8; D023 decision 3; [S1–S5] |
| A reranker cutting a catalog menu to 7 | Contradicts facet menus; cannot resolve lexical near-misses (PW04) | doc 47 §4.4; E2 tests it |
| Embedders selecting cards | Activation is code's job | D027 item 7 |
| Semantic response caches; model summaries of facts | No correctness guarantee; lossy; breaks provenance | doc 40 §8; [S15] |
| Code LMs as Teller's default completion | Suggest later-Arma dialect; every 3–4B build scored 0 of 24 on free engine knowledge | doc 30 §1.1; doc 44 |
| ML grading in Drill or readiness | Pass/fail must be reproducible | doc 33 §5.1 |
| Neural safety or injection classifiers on user content | Over-flag military text; brittle; user content is never filtered | D011; D041; [S13] |
| Vision models for terrain perception | WRP objects already hold the facts | doc 25 §6.1 |
| Learned shot-aesthetics scorers | Checks are exact and explainable | doc 39 |
| Fine-tuned helpers in v1 | Decided against; revisited only as the §7 owner question | D027 item 6; D048 decision 3 |
| A small model summarising untrusted mission text as an authoritative digest | Public failure mode; verbatim card is the fallback | [S19]; doc 53 §4.5 |

## 3. Model candidates per task

### 3.1 How to read

Licences are read on the model card or the crate at the date shown (Hugging Face tags and crates.io entries re-checked on
2026-09-28 [S43, S44]) and still need the pinned-revision check of D037 before any recommendation. "Runs in" names the tier of §4.1.
Latency classes for one editor-sized item on a mid laptop CPU [I unless cited]: **A** < 50 ms, **B** 50–500 ms, **C** 0.5–5 s,
**D** > 5 s. No row here is qualified; every row is a candidate for §6.

### 3.2 Retrieval: BM25, embedders and rerankers

| Candidate | Licence | Size | Languages | Runs in | Evidence | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| tantivy 0.26.2 / bm25 2.3.2 (BM25) | MIT / MIT [V S43] | crates | any (tokeniser per language) | Editor | BEIR baseline [S10] | **Baseline (P1)** |
| granite-embedding-97m-multilingual-r2 | Apache-2.0 [V S33] | 97.4M; community Q8_0 GGUF ~0.12 GB | 200+, 52 "enhanced" incl. cs, pl, ru, de, fr, it, es | Sidecar (ModernBERT in mainline) | Vendor multilingual retrieval 60.3 vs 50.9 for multilingual-e5-small [V-vendor S33] | CPU default candidate for E1 (class A) |
| Qwen3-Embedding-0.6B | Apache-2.0 [V S33] | official Q8_0 0.64 GB | 100+ | Sidecar (append EOS by hand, doc 47) | Vendor MMTEB 64.33; BTZSC zero-shot 0.58 [V S27] | Quality tier candidate (class B) |
| bge-m3 | MIT [V S33] | ~568M | 100+; dense, sparse, ColBERT | Sidecar for dense [I]; sparse outputs via llama-server [U] | — | Watch |
| nomic-embed-text-v2-moe | Apache-2.0 [V S33] | 475M total, 305M active | ~100 | Sidecar (llama.cpp PR #12466) [V S28] | Vendor MIRACL 65.80, BEIR 52.86 | Watch; needs task prefixes |
| multilingual-e5-small | MIT [V S33] | ~118M | 90+ | Sidecar | — | Sanity arm |
| potion-base-8M (static Model2Vec) | MIT [V S33] | 7.56M; 30.2 MB safetensors | English | Editor, own encoder (§4.4) | — | Tier-I probe for keystroke-speed English search |
| EmbeddingGemma-300m; Bekko v1 | Gemma terms (gated); CC-BY-4.0 | 300M; 8–25M active | multilingual | — | Vendor/author claims [V-author S33] | Custom only (D037) |
| Qwen3-Reranker-0.6B | Apache-2.0 [V S34] | ggml-org Q8_0 0.64 GB | 100+ | Sidecar `--rerank` | MTEB-R 65.80, MMTEB-R 66.36; FollowIR only 5.41 [V-vendor S34] | Reranker candidate at K ≤ 20 (class B per pair) |
| bge-reranker-v2-m3 | Apache-2.0 [V S34] | 568M | multilingual | Sidecar (community GGUF) | MTEB-R 57.03 [V-vendor S34] | Second reranker arm |
| mxbai-rerank-base-v2 | Apache-2.0 | 0.5B | 100+ | no llama.cpp statement | BEIR 55.57, "multilingual" 28.56 [V-vendor S34] | Watch |
| gte-multilingual-reranker-base; jina rerankers | Apache-2.0 but custom code; CC-BY-NC-4.0 | — | — | trust_remote_code; — | — | Skip; excluded |

**Evidence caveat** [V]: the Slavic subset of MTEB rests on sparse, correlated datasets, so Czech, Polish and Russian rankings from
public leaderboards are weak evidence [S33]. E1 measures on Plotroom's own queries.
**BM25 caveats** [V S43]: tantivy's default features pull `zstd` (a C library) and `memmap2`, and its `MmapDirectory` writes index
files itself, so tier I takes it with `default-features = false`, an in-memory directory and bytes persisted through `plotroom-io`
(crate-map: the only file writer); the smaller `bm25` crate is in-memory by design. Neither ships a Czech or Polish stemmer (the
`rust-stemmers` list covers Russian, German, French, Italian and Spanish), so E1 adds a deterministic arm for the two inflected
languages without stemmers (character n-grams or prefix truncation) [I].
**Design** [I]: embed Plotroom's own authored corpora (Standing Orders, Drill, cards, exemplars, catalog aliases) at build time with the
pinned model revision and ship the vectors as hash-pinned data (an owner question, §4.7); at runtime only the query is embedded.
Fuse with BM25 by reciprocal-rank fusion. **Gotcha** [V]: `fastembed`'s built-in model list includes non-OSI models (EmbeddingGemma,
jina-reranker-v2), so the Model Manager admits models only from Plotroom's own manifest, never from a library default [S31].

### 3.3 Classification, zero-shot flags and decision models

| Candidate | Licence | Size | Languages | Runs in | Evidence | Role |
| --- | --- | --- | --- | --- | --- | --- |
| Session model letter probabilities | — | no extra artifact | as the model | Sidecar `n_probs` | doc 53 §3 | **First choice for every Pick** |
| Qwen3-Reranker-0.6B as a zero-shot scorer (hypothesis = query, item = document) | Apache-2.0 | 0.6B | 100+ | Sidecar | BTZSC 0.61 macro-F1 vs 0.65 for generative Qwen3-4B (English, 22 datasets) [V S27] | Advisory flags (B11) without a new artifact if the reranker is installed |
| bge-m3-zeroshot-v2.0-c | MIT [V S35] | 0.6B (XLM-R) | multilingual via XLM-R; Czech untested | Sidecar: a community GGUF of the non-"c" twin loads with two outputs under rank pooling [V-community S28] | Mean F1 0.59 vs 0.676 for English deberta-v3-large [V-author S35] | Multilingual NLI flag candidate |
| deberta-v3-base-zeroshot-v2.0-c | MIT | 0.2B | English | Helper (DeBERTa not in llama.cpp) | Mean F1 0.619 over 28 tasks [V-author S35] | Fast English flag |
| ModernBERT-large-zeroshot-v2.0 | Apache-2.0 | 0.4B | English | Sidecar plausible (ModernBERT sequence classification is registered) [I on V S28] | "Slightly worse than DeBERTa-v3", several times faster [V-author S35] | Watch |
| mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | MIT | 0.3B | 27 languages incl. de, fr, pl, ru; **no cs** | Helper | XNLI en 0.871, de 0.824, ru 0.803 [V-author S35] | Watch |
| GLiClass v3 (modern-base; x-base) | Apache-2.0 | 151M; 0.3B | English; multilingual (avg 0.418) | Python only; no Rust runtime found [U] | Avg F1 0.558 (modern-base) [V-author S35] | Skip |
| decider-0.8b; Kev-0.8B; Laya (mmBERT, 322M) | Apache-2.0 | 0.3–0.8B | English; —; multilingual | Sidecar; sidecar or ONNX; helper | decider-2b held-out 0.429, ECE 0.156; Laya near chance zero-shot (0.352) [V per doc 16/47] | Shadow research arms only (D023 decision 5) |

Independent evidence [V S27]: at small sizes, rerankers lead zero-shot classification, NLI cross-encoders plateau as they grow, and
embedders give the best accuracy per unit of latency; multilingual was not tested. Everything in this table is advisory (doc 16 §3.3).

### 3.4 Span extraction (free text to typed slots)

| Candidate | Licence | Size | Languages | Runs in | Evidence | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| **Code candidates + Pick** | — | — | all | Editor + sidecar | removes whole failure classes (doc 55 §1.1) | **P1 baseline** |
| GLiNER2-base-v1 | Apache-2.0 [V S36] | 205M (795 MB files) | English (multi-v1: EN, FR, ES, DE, IT, PT) | Helper (DeBERTa-v3 plus a count LSTM) | CrossNER F1 0.590 vs 0.599 GPT-4o; CPU 130–208 ms [V-vendor per doc 53] | English extractor candidate |
| gliner-x-base | Apache-2.0 [V S36] | 0.5B (mT5 encoder) | 20 incl. cs, pl, de, fr, it, es, uk; **no ru** | Helper (ONNX in the repo) | F1 de 0.760 vs 0.640 and en 0.678 vs 0.573 against gliner_multi-v2.1 [V-author S36] | Multilingual extractor candidate |
| gliner_multi-v2.1 | Apache-2.0 (the onnx-community export carries no licence tag) | mDeBERTa-v3-base; 1,102 MB; int8 ONNX 332.9 MB | multilingual | Helper; `gline-rs` pins ort rc.9 | — | Baseline arm |
| NuExtract3 | Apache-2.0 [V S36] | 4B, official GGUF | multilingual | Sidecar | doc 47 Fill-spans test | Generative alternative |
| NuExtract-2.0-2B | MIT | 2B (Qwen2-VL-2B base) | — | Sidecar (community GGUF) | vendor only | Watch |

Code snaps every extractor span to real data (substring of the request, island Names, catalog classes, counts), so the quote check holds
by construction. Russian falls back to code candidates plus the session model. Provenance flag: GLiNER2 used GPT-4o-annotated data
(doc 53), which D037's "unclear provenance" rule must rule on (Open question 8).

### 3.5 Faithfulness checkers for EXPLAIN

| Candidate | Licence | Size | Languages | Runs in | Notes |
| --- | --- | --- | --- | --- | --- |
| **Code claim matcher** | — | — | all | Editor | Named commands, classes and numbers in the paraphrase must appear in the card; **P1** |
| HHEM-2.1-Open | Apache-2.0 [V S37] | FLAN-T5-base, ~0.1B | English | Helper | Custom `HHEMv2ForSequenceClassification`; the reference path needs `trust_remote_code`, which the product never does [V S28]; ~1.5 s per 2K tokens on CPU [V-vendor per doc 53] |
| LettuceDetect | MIT (EN ModernBERT, 150M; EuroBERT 210M/610M variants) [V S37] | base encoder | English; EuroBERT variants for de, fr, it, es, pl, zh; `lettucedect-v2-mmbert-base` (Apache-2.0) tags en, de, fr, es, it, pl, zh; **no cs or ru** [V S37] | Helper (token classification is not registered in llama.cpp) [I on V S28] | Token-level spans of unsupported text |
| Granite 4.1 hallucination-detection / answerability adapters | Apache-2.0 | LoRA | English | Sidecar `--lora` on a Granite base only | doc 53 §2.4, stage S8 |

Bar: doc 53 R11 (AUROC ≥ 0.80 against graded hallucinations while flagging ≤ 10% of passes). On a failed check, show the card, not a
free retry.

### 3.6 Translation

Mozilla's Firefox Translations registry (generated 2026-09-27; re-fetched at review, regenerated 2026-09-28 with the same values) lists
released models for every direction Plotroom needs [V S38]. Metrics are the registry's own, on the general-domain `flores200-plus`
test set:

| Direction | Architecture, parameters | COMET22 | BLEU |
| --- | --- | --- | --- |
| en → cs / cs → en | base-memory, 31.2M | 0.8908 / 0.8748 | 32.71 / 37.37 |
| en → pl / pl → en | base-memory, 31.2M | 0.8683 / 0.8469 | 21.39 / 26.73 |
| en → ru / ru → en | base 42.7M ("Release Desktop") and base-memory 31.2M ("Release Android") / base-memory | 0.8764 and 0.8745 / 0.8497 | 31.25 / 31.88 |
| en → de, fr, it, es | base-memory | 0.867, 0.8653, 0.8655, 0.854 | 39.65, 48.85, 29.39, 27.52 |

- **Firefox models** [V S38]: code MPL-2.0, and "the model files are distributed under the MPL 2.0 license" (the `mozilla/translations`
  README); int8 model files of about 31.6 MB uncompressed per direction (43 MB for en → ru base); built for CPU and WASM. The registry
  gives a SHA-256 (`uncompressedHash`) for the model file only: the vocabulary and lexical-shortlist files carry a path and no hash,
  so the Model Manager computes and pins its own hashes for those two files at pin time [V S38; I]. The old models repository was
  archived (last push 2025-12-15) and work continues in `mozilla/translations`. Runtimes: `bergamot-translator` (C++, MPL-2.0),
  `slimt` (C++; GitHub reports GPL-2.0, so check for an "or later" grant before any use beside GPL-3.0-or-later), or
  **`fxtranslate` 0.4.2** (MPL-2.0, "validated against the reference C++ engine" [V-author]; first release July 2026, one owner,
  published from a fork of `mozilla/translations`). `fxtranslate` is Rust with its own SentencePiece reader, but its native fast
  path is the vendored gemmology int8 kernel (C++, MIT) through FFI and a `cc` build step (the default `gemmology` feature); the
  pure-Rust SIMD kernel exists only for wasm32, and without `gemmology` native builds fall back to a scalar path. Its default
  features also enable `mmap`, and `net` / `download` fetch models by themselves; all three stay off, so the Model Manager feeds
  pinned files (whether it offers a byte-slice loader is [U]) [V S43, S38]. Limits [I]: sentence-level; no glossary, terminology or tone control; code must mask placeholders
  (`%1`, `\n`, briefing HTML); military radio register untested. Class A–B per sentence with the SIMD kernel [I]; the scalar path is
  unmeasured [U].
- **Hy-MT2-1.8B** (Tencent): Apache-2.0 only at revisions from 2026-05-26 (commit `9a341cd1`, "Update license metadata"); the
  earlier revisions carry the Tencent Hy Community License, which excludes the European Union and is custom-only under D037, so pin
  the revision; official GGUF (Q4_K_M 1.13 GB); 36 languages including all eight engine languages; terminology, style, delimiter and
  structured-data prompt modes; no per-language Czech, Polish or Russian numbers [V/V-vendor S38]. Sidecar, class C. The **glossary
  tier**.
- **EuroLLM-1.7B-Instruct**: Apache-2.0; 35 languages; vendor FLORES-200 COMET 86.89 [V-vendor S38]; CPU bulk arm. EuroMoE-2.6B-A0.6B
  per doc 53 §4.7.
- **Skip:** OPUS-MT (Marian; superseded by the Firefox models for these pairs, en-cs last updated 2023-08) and madlad400-3b-mt (T5
  support in llama-server [U]). **Excluded** (D037): NLLB (CC-BY-NC), TranslateGemma (Gemma terms), Tiny Aya (CC-BY-NC), Seed-X.
- **No independent CZ/PL/RU evaluation exists** for any of these (doc 47), so the translation suite with native graders (doc 47 §6.4,
  E7 below) comes before any badge. Every output passes the code-page, length and placeholder lints and stays flagged
  "machine-translated" until native review (doc 33 §7).

### 3.7 Voice: speech synthesis and recognition

Out of v1 scope (docs 15, 17). Only English and Czech are voiced in the Remaster [V per doc 14]. Voice cloning is ruled out (doc 15;
doc 22 §1.2 "Never allowed").

| Candidate | Licence | Languages | Runs in | Notes | Verdict |
| --- | --- | --- | --- | --- | --- |
| Piper (engine `piper1-gpl`, embeds espeak-ng) | GPL-3.0 engine; **licence per voice** [V S39] | 43 languages, which the research pass found to include all eight engine languages; voice licences checked only for the voices named here | Helper (VITS `.onnx` + `.onnx.json`; `piper-rs` 0.2.0 MIT, which pins `ort` =2.0.0-rc.12 and compiles espeak-ng (C, GPL-3.0) through `espeak-rs-sys`, so a reference, not a dependency) [V S43] | cs_CZ jirka CC0, pl_PL gosia CC0, de_DE thorsten CC0, fr_FR siwis CC-BY-4.0; ru_RU irina lists its dataset licence as "Unknown" [V S39]. The voices doc says "Piper is intended for personal use and text to speech research only; we do not impose any additional restrictions on voice models" [V S39] | **First candidate**, per-voice allowlist (CC0, CC-BY), which needs an owner ruling because D037's rule names OSI licences and CC0 / CC-BY-4.0 are not OSI-approved (§3.10, OQ14) |
| Kokoro-82M | Apache-2.0 [V S39] | en-US, en-GB, es, fr, hi, it, ja, pt-BR, zh; **no cs, pl, ru, de** | Helper (onnx-community export; Rust ports) | Card says it trained partly on synthetic audio from closed TTS models (provenance) [V S39] | Second candidate for EN/FR/IT/ES |
| Kitten TTS; Pocket TTS; Chatterbox; Qwen3-TTS; OuteTTS-1.0-0.6B; Supertonic 2 | Apache-2.0; CC-BY-4.0 gated; MIT; Apache-2.0; Apache-2.0; OpenRAIL-M | English only; no cs/pl/ru; no cs; no cs/pl; no cs; — | — | Clone-capable or GPU-bound or English-only. llama.cpp's master now ships a `llama-tts` CLI (PR #26254, merged 2026-08-04) that runs Qwen3-TTS (zh, en, de, it, pt, es, ja, ko, fr, ru) and Pocket TTS, both driven by a speaker reference recording (cloning; Pocket TTS "produces almost no audio without it"); there is no llama-server speech endpoint, and OuteTTS 1.0 (PR #12794) is still an open draft [V S28] | Watch or custom only |
| openai/whisper-base (ASR) | Apache-2.0 [V S40] | covers cs, pl, ru, de | Helper; `whisper-rs` 0.16.0 (Unlicense, binds whisper.cpp) [V S43] | Draft subtitles and take checks | P3 |

What stays code: the radio filter (band-pass, saturation, limiter), loudness normalisation, `.lip` generation (CWR's algorithm with its
8 upstream tests), energy-threshold trimming (H3).

### 3.8 Text hygiene and classical statistics (no neural net)

| Crate or method | Licence [V S43] | Use | Notes |
| --- | --- | --- | --- |
| `lingua` 1.8.0 | Apache-2.0 | G2 language ID | 75 languages incl. cs, pl, ru, de; rule-based alphabet step plus 1–5-gram models; "pretty accurate results on both long and short text, even on single words and phrases"; "a few dozen megabytes" of memory [V-author S42]. The default features compile all 75 language models ("approximately 300 MB" of model crates); the eight engine languages alone are about 26 MB of model crates, selected with `default-features = false` [V S42, S43] |
| `harper-core` 2.11.0 | Apache-2.0 | G1 English grammar | Offline, "milliseconds to lint a document" [V-author S42]; rules need curating for radio register [I] |
| `spellbook` 0.4.2 | MPL-2.0 | G1 spelling, all languages | Hunspell-compatible, pure Rust (Helix); dictionaries' licences vary: cs_CZ GPL (the pack also holds GFDL-licensed parts), pl_PL offered under GPL, LGPL, MPL, Apache-2.0 or CC-SA 1.0, ru_RU a BSD-style licence with no advertising clause but a "modified versions must be clearly marked" condition [V S42] |
| LanguageTool | LGPL-2.1 (Java server) | optional | pl, ru, de, fr, it, es, **not Czech** [V S42]; bring-your-own local endpoint only |
| `tantivy` 0.26.2; `bm25` 2.3.2 | MIT; MIT | C1, C2, I2, K1 | BM25 indexes; tantivy with default features off (§3.2 BM25 caveats); no Czech or Polish stemmer |
| `nucleo` 0.5.0 | MPL-2.0 | A1 | Fuzzy matching |
| `gaoya` 0.2.2; `probminhash` 0.1.12 | MIT; MIT or Apache-2.0 | B13 | MinHash/SimHash LSH |
| `smartcore` 0.6.15; `linfa` 0.8.1 | Apache-2.0; MIT or Apache-2.0 | B3 offline calibration fits | A few hundred lines of our own code may be enough |
| Drain (He et al., ICWS 2017; Drain3 reference) | port the algorithm | J1 unknown log lines | LLM log parsers beat Drain on LogHub-2.0 [V S43] but only matter for unknown sources; Plotroom has the engine's own format strings |
| Dirichlet-multinomial update | closed form | F3 | Counts and credible bands per cell |

No small, OSI-licensed, Czech-capable neural grammar corrector was found [I]. All text-hygiene findings are advisory lints,
dismissible as intentional (D011).

### 3.9 Code completion (SQS/SQF)

No SQS- or SQF-specific model exists [I; none found]. A 2026 study on a low-resource language got its gains only from continued
pre-training and fine-tuning on that language's corpus [V-author S41], which D027 item 6 rules out, and public SQF is mostly the later
dialect (doc 30). Candidates for **optional, off-by-default** ghost text through llama-server `/infill`: Qwen2.5-Coder-0.5B and 1.5B
(Apache-2.0 [V S41]); Mellum-4b-base (Apache-2.0; official GGUF in `JetBrains/Mellum-4b-base-gguf` [V S41]). Excluded:
Qwen2.5-Coder-3B (qwen-research licence) and StarCoder2 (OpenRAIL-M). Teller's parser and dialect lint filter every suggestion first
(the JetBrains shape [S17]).

### 3.10 Licence screen and provenance flags

- **Eligible after qualification** (OSI, no field-of-use limit): the Apache-2.0, MIT and MPL-2.0 rows above. MPL-2.0 is compatible
  with GPL-3.0-or-later unless a file is marked "Incompatible With Secondary Licenses" [S45], so each MPL file is checked at pin
  time [I].
- **Custom only** (D037): EmbeddingGemma (Gemma terms), jina rerankers (CC-BY-NC), Pocket TTS (CC-BY-4.0, gated, clone-capable),
  Supertonic (OpenRAIL-M), Bekko (CC-BY-4.0), Qwen2.5-Coder-3B, NLLB, TranslateGemma, StarCoder2; Prompt Guard (Llama terms);
  Hy-MT2 revisions before 2026-05-26 (territory-restricted community licence).
- **Needs an owner ruling** (OQ14): D037's recommended list requires an **OSI-approved** licence, and CC0 and CC-BY-4.0 are not
  OSI-approved (they are content licences). Read literally, the Piper voices of §3.7 (CC0, CC-BY-4.0) would be custom-only, as Bekko
  (CC-BY-4.0) is above; the per-voice allowlist of §3.7 and §4.7 is therefore a proposal to extend D037 to data-derived artifacts,
  not an application of it [I]. The same question touches Hunspell dictionaries under GFDL or CC-SA terms.
- **Provenance questions** for D037's "unclear provenance" rule: Kokoro (synthetic audio from closed TTS models), GLiNER2 (GPT-4o
  annotations), Piper voice ru_RU irina (dataset licence "Unknown"), and the onnx-community GLiNER export with no licence tag, where
  the check must fall back to the base repository or refuse.

## 4. Runtime and architecture

### 4.1 Three tiers (proposal)

| Tier | What runs | Examples | Supply chain | Crash isolation | Platforms |
| --- | --- | --- | --- | --- | --- |
| **S: sidecar** (default) | GGUF generative models, embedders, rerankers, BERT/XLM-R/ModernBERT classifier heads, FIM | Session model, granite-embedding r2, Qwen3-Reranker, bge-m3-zeroshot, Hy-MT2 | Already managed (D022: pinned by build tag and asset SHA-256; docs 55 and 59 cite b11146); the upstream b11223 CPU, Vulkan and macOS archives (latest release, 2026-09-27) are 10.8–31.5 MB [V S28] | Separate process | Windows CPU/Vulkan, macOS arm64 and x64, Linux CPU/Vulkan |
| **I: in-process, pure Rust** | Deterministic statistics and tiny pinned models under §4.4's rule | lingua, spellbook, Harper, tantivy or `bm25` (default features off); after S-ENC only: an own static-embedding encoder, tract or rten for small ONNX heads | Rust crates (tract adds assembly kernels) | Editor process, guarded by §4.4 | Every Rust target |
| **H: helper process** | Native runtimes and anything not admitted to tier I | ONNX Runtime via `ort` (load-dynamic): GLiNER2, gliner-x, mDeBERTa NLI, HHEM, LettuceDetect, Piper, Kokoro; whisper.cpp; `fxtranslate` with its C++ gemmology kernel | A second native supply chain (`onnxruntime.dll` 16.46 MB in the official v1.30.0 win-x64 zip) [V S29]; official ORT builds carry telemetry (§4.5) | Separate process supervised by `plotroom-model-manager` | ORT: no x86_64 macOS build from pyke or Microsoft; pyke builds need x86-64-v3 (AVX2) and pyke's Windows builds all include DirectML [V S29] |

Crate-map §2.3 already lets `plotroom-model-manager` spawn "managed inference server and helper" processes, and its §10 row reserves "a
helper process for any embedded engine"; agent-runtime §3 resolves that any embedded engine runs out of process. Tier H is that helper,
widened from generative engines to components [I]. Tier I is the new part: running neural model code (a static-embedding encoder,
tract, rten) inside the editor departs from that resolution (architecture README §7 row 13, §8 item 7), so it needs the owner's or
D022's revisit, not only a spike; the deterministic crates of tier I (lingua, spellbook, Harper, BM25) load no downloaded model
files, run no neural network and are ordinary editor code [I].

### 4.2 What the sidecar already runs, and its caveats

- **Coverage** [V S28]: `--embedding`, `--pooling {none,mean,cls,last,rank}`, `--rerank`, `/v1/embeddings`, `/rerank`, `/infill`,
  `/tokenize`, router mode with per-model presets, and `-dev none` to keep a helper off the GPU. The converter registers BERT,
  DistilBERT, RoBERTa, XLM-RoBERTa, NomicBERT, NeoBERT, EuroBERT, JinaBERT v2/v3, Jina embeddings v5, ModernBERT (including sequence
  classification) and T5 (read on `master`; the pinned build must be re-checked). One mode per server, so each helper is its own
  router entry (doc 47 §4.1).
- **Caveats** [V S28]: an encoder input must fit one micro-batch; the default `-ub` is 512, and longer inputs return HTTP 500 "input is
  too large to process" (third-party report), so presets set `ubatch-size` = `batch-size` ≥ the longest input. Logits "are not
  guaranteed to be bit-for-bit identical for different batch sizes", and parallel slots add rounding noise, so encoder entries pin
  `-np 1`, a fixed `-ub` and a fixed thread count. A reranker GGUF converted without its `cls.output.weight` tensor returns scores near
  zero (third-party gist), so D022 amendment item 4's refusal check should also read the encoder metadata (pooling type,
  `cls.output` tensors, classifier labels) before admitting a file [I].
- **Implication** [I]: with no new runtime, v1 can do embeddings, reranking, zero-shot scoring by reranker, XLM-R/ModernBERT
  classifier flags, FIM and generative translation through the sidecar, plus text hygiene in pure Rust. Firefox translation needs
  either the helper (for `fxtranslate`'s C++ kernel) or its unmeasured scalar path in process.

### 4.3 What needs another runtime

No DeBERTa-v2/v3 architecture appears in llama.cpp's converter [V S28], which rules out GLiNER multi-v2.1 (mDeBERTa-v3), GLiNER2-base
(DeBERTa-v3 plus an LSTM counting layer) and mDeBERTa-xnli. HHEM-2.1-Open is a custom class loaded through `auto_map`. Token
classification heads for ModernBERT or EuroBERT (LettuceDetect) are not registered [I on V S28]. llama.cpp is not a usable TTS path
for Plotroom: its `llama-tts` CLI (PR #26254) runs Qwen3-TTS and Pocket TTS only from a speaker reference recording, which is voice
cloning, llama-server has no speech endpoint, and OuteTTS 1.0 (PR #12794) is still an open draft [V S28]. These are exactly the
components doc 53 §4.9 flagged, and only they force the encoder-runtime decision.

### 4.4 In-process admission rule (proposal)

A component may run inside the editor process only when all of these hold [I]:

1. **Pure Rust.** No C or C++ in its build graph apart from assembly kernels. `tokenizers` with `default-features = false` and
   `fancy-regex` is pure Rust; its defaults pull Oniguruma (C) and a C++ suffix-array library, and its `http` feature pulls `hf-hub`
   [V S32].
2. **Pinned and qualified** by repository, commit and SHA-256, for that runtime and version.
3. **Small and capped:** weights at most about 150 MB; inputs capped (for example 512 tokens); p95 on the reference CPU within the
   stated class.
4. **Contained:** a worker thread with cancellation; byte-slice loaders only, fed by `plotroom-io` (rten `Model::load(Vec<u8>)`,
   candle `from_buffered_safetensors`, tract `model_for_read`; the mmap loaders are `unsafe`) [V S30].
5. **Robust:** a malformed-model fuzz run returns typed errors, never an abort; any abort moves the runtime to tier H.

Candidates today, each with the named default features off [V S43]: lingua (only the eight engine languages' model features, not
the default 75), spellbook, Harper, and tantivy (no `zstd`, no `mmap`, an in-memory directory persisted through `plotroom-io`) or
`bm25`. After S-ENC and an owner call on §4.1's exception: an own static-embedding encoder (tokenise → row lookup → mean →
normalise, over `safetensors` and `tokenizers`; cheaper than taking `model2vec-rs`, whose default features pull C and C++ through
`tokenizers`' Oniguruma and suffix-array code, plus `hf-hub` [V S31, S43]); tract 0.23.8 or rten 0.26.0 for small ONNX heads
[V S30]. Not a candidate as shipped: `fxtranslate` fails rule 1 on native targets while its `gemmology` kernel is C++; its scalar
path could qualify only if S-ENC shows it fits class B. Our crates keep `unsafe_code = "forbid"` under every option; the unsafe code
lives in dependencies.

### 4.5 The helper process (proposal)

- A small Plotroom binary (`plotroom-infer`, name provisional) supervised by `plotroom-model-manager` like the sidecar: loopback,
  random port and key, cancellation, restart on crash, and the same Preview rules as the sidecar (D018; whether CPU components may
  stay resident while the game runs is doc 53 OQ7).
- ONNX Runtime through `ort` 2.0.0-rc.13 with `load-dynamic`, loading a Model-Manager-pinned library; **CPU execution provider only**;
  `default-features = false` (the defaults download binaries at build time) [V S29].
- **No telemetry, by construction and proven by a test** [V S29]: `ort`'s `EnvironmentBuilder::new()` defaults to `telemetry: true`.
  Since ONNX Runtime 1.29, official builds collect trace events on every native platform: TraceLogging/ETW on Windows, and on Linux,
  macOS, Android and iOS a built-in 1DS client that sends them "to Microsoft's telemetry backend over HTTPS". The build driver turns
  telemetry on by default for native targets (only the Windows `build.bat` wrapper passes `--no_telemetry`), and even with the API
  switch "ONNX Runtime may already have emitted a minimal initialization event". An official Microsoft library would therefore add
  outbound traffic that AGENTS.md does not allow (directly on Linux and macOS; on Windows through the operating system's diagnostic
  pipeline, subject to its consent settings). Proposal [I]: the Model Manager pins an ONNX Runtime library built with
  `--no_telemetry` (Plotroom's own reproducible build, which also covers x86_64 macOS and pre-AVX2 CPUs, at a build and CI cost the
  owner weighs under OQ2), the supervisor starts the
  helper with `ORT_DISABLE_TELEMETRY=1` and the helper calls `with_telemetry(false)` as defence in depth, and a no-egress test runs
  the helper with networking denied. Whether pyke's prebuilt libraries include the 1DS client is [U].
- Never bundle DirectML or CUDA libraries (pyke's Windows builds all include the DirectML execution provider, so they are out);
  ONNX Runtime's third-party notices are permissive or MPL-2.0 for CPU builds [V S29].
- Only one `ort-sys` can exist in a build graph (`links = "onnxruntime"`), and `gline-rs` pins rc.9, `piper-rs` rc.12 and
  `fastembed` rc.13 (all exact pins) [V S29, S31, S43], so wrapper crates serve as references, not dependencies.
- Running untrusted model files in native code has a memory-safety record: ONNX Runtime 1.28.0 fixed out-of-bounds writes and reads
  in input binding and kernels, 1.30.0 fixed index overflows in CPU kernels, and the ONNX library's version converter had a heap
  over-read (GHSA-p893-rvq9-2xf9) [V S29]. That is why downloaded models are parsed and run here, not in the editor.
- `fxtranslate` (§3.6) also lives here while its fast path is C++; it needs no ONNX Runtime, so the helper hosts two independent
  engines behind one supervised process or two [I].

### 4.6 The component seam in the crate map (proposal)

Proposal-only sketch; names are not final (DG037's names table applies):

```rust
/// One purpose-specific component: a typed job, advisory, replaceable.
/// Nothing it returns is admitted without the calling step's own checks.
pub trait Component: Send + Sync {
    fn kind(&self) -> ComponentKind;
    /// Artifact, runtime build, threads and batch: the qualification key.
    fn pin(&self) -> &ComponentPin;
    fn run(&self, req: ComponentRequest<'_>, cancel: CancellationToken) -> Result<ComponentAnswer, Error>;
}

pub enum ComponentKind { Retrieve, Rerank, Flag, Extract, Check, Translate, Speak, Transcribe }

/// What the journal keeps for every call, used or not (D010).
pub struct ComponentVerdict {
    kind: ComponentKind,
    pin: ComponentPin,
    input: Digest,                  // digest of the typed input
    score: Score,                   // distribution, similarity or checker probability
    threshold: Option<Threshold>,
    outcome: ComponentOutcome,
}

pub enum ComponentOutcome { Used, ShownAsAdvice, Ignored, FellBack { reason: FallbackReason } }
```

| Piece | Crate (layer) | Why there |
| --- | --- | --- |
| The trait, kinds, typed requests and answers, `ComponentPin`, `ComponentBinding`, `ComponentVerdict` | `plotroom-provider` (L6) | Beside `InferenceProvider`; no I/O |
| Calls at the seams (`Selector`, retriever, ranker, extractor, checker) | `plotroom-decide` (L6) | The decision kernel owns menus and admission |
| BM25 index, aliases, hybrid fusion over Plotroom's corpora | `plotroom-knowledge` (L5) | The one knowledge store (DG032) |
| Spelling, grammar, language ID, script check, glossary | a new `plotroom-textcheck` (L5, name provisional) feeding `plotroom-validate` rules | AI-off advisory lints; dictionaries read through `ReadOnlySource` |
| Sidecar adapters: `/v1/embeddings`, `/rerank`, `/completion` with `n_probs`, `/infill` | `plotroom-provider-http` (L7) | The only wire adapters |
| In-process engines, only if S-ENC and the owner admit them (the static-embedding encoder, tract or rten) | a new `plotroom-components` (L7 proposed, name provisional; its layer is part of design-gap candidate 2) | Loads third-party model bytes and runs SIMD kernels; keeps L6 light |
| Pins, downloads, encoder router presets, the helper process (ONNX Runtime components, `fxtranslate`) | `plotroom-model-manager` (L7) | Already reserves the helper |
| Component suites; "Check this component on my machine" | `plotroom-evals` (L6); `tools/local-qual` | Qualification |

`xtask layers` and cargo-deny additions (proposal): ban `ort-sys` with `download-binaries`, `ort`'s `fetch-models`, `tch`/`torch-sys`
(libtorch), and `hf-hub`/`ureq` anywhere outside `plotroom-net` (which already catches `fastembed` and `gline-rs` defaults); optionally
ban `onig_sys`, `esaxx-rs` and, in tier I crates, `zstd-sys`; allow one `ort` version; the components crate reads no environment
variables (crate-map §2.3), which excludes `fastembed`-style `HF_*` lookups; `ORT_DISABLE_TELEMETRY` is set by the supervisor in the
helper's process environment, never read by a Plotroom library [I on V S31, S29].

### 4.7 Model delivery through the Model Manager

Extends doc 53 §4.11 [I]:

| Artifact kind | In the installer? | Recommended list | Pin | Runtime |
| --- | --- | --- | --- | --- |
| Encoder weights (ONNX, safetensors) | Never (D023 decision 1) | D037 rule plus qualification per component kind | Repository, revision, file, bytes, SHA-256, licence file hash | Tier I or H |
| Embedder or reranker GGUF | Never | Same | As generative GGUF | Tier S |
| Firefox translation models | Never | Same; **a new download source** (Mozilla's bucket, not Hugging Face) that the user enables under D008 | Registry path plus the registry's SHA-256 for the model file; Plotroom's own SHA-256 for the vocabulary and shortlist files, which the registry does not hash | Tier H (tier I only for a qualified scalar path) |
| TTS voices | Never | Proposed per-voice allowlist (CC0, CC-BY; "Unknown" refused), pending the owner's D037 ruling (OQ14) | Per voice file | Tier H or plugin |
| Hunspell dictionaries | Not by default (licences vary) | OS or user-supplied, or a pinned user-started download | Per file | Tier I |
| lingua's n-gram tables (compiled into the crate; about 26 MB of model crates for the eight engine languages) | **Owner question** (OQ6) | — | Crate version | Tier I |
| BM25 index over Plotroom's own corpora | Proposed yes: our own content (OQ6) | — | Build hash | Tier I |
| Vectors of Plotroom's corpora from a pinned embedder | **Owner question** (OQ6) | — | Model revision plus build hash | Tier I |
| Calibration files (letter priors, temperatures) | As preset data (D048) | With the preset | Preset hash | — |
| Plotroom-trained heads or adapters | Not in v1 (§7) | — | — | — |

Downloads remain the user's action in Settings, never an agent tool (D022). Proposal for the owner (OQ6): deterministic statistical data
under an OSI-compatible licence may ship pinned and versioned; neural weights never do.

### 4.8 Determinism and versioning

- **Pin everything that changes numbers** [V S28, S29]: model file, runtime build, threads, batch and micro-batch, `-np 1` for encoder
  entries; ONNX Runtime's `intra_op_num_threads` (one third-party report found bitwise-reproducible output at fixed threads on a quiet
  machine and drift up to 3e-4 under core contention) and `use_deterministic_compute`. tract, rten and candle document no guarantee
  [U]. All of it goes into the qualification key (D048 presets; DG012 voids).
- **Replay reads the journal, not the model** [I]: component outputs are recorded (§4.10), so a replay or golden-journal test on another
  machine never depends on float-identical recomputation.
- **Gates** [I]: a 20-run bitwise-repeat test at fixed threads, a cross-thread-count tolerance test, and parity against reference
  logits (max abs diff ≤ 1e-4, identical labels, spans and argmax) per runtime.
- **Versioning:** swapping the session model re-runs every dependent stage's qualification, because calibrations and adapters do not
  transfer (Apple's adapters "must be retrained with each new version of the base model" [S19]).

### 4.9 Per-component qualification suites

| Kind | Suite (synthetic, redistributable) | Metrics | Proposed bar | Baseline to beat |
| --- | --- | --- | --- | --- |
| Retriever / embedder | E1 retrieval instrument (doc 30 OQ2; doc 47 §6.4) | Recall@1/3/7, MRR, `NotInManual` accuracy, per language | Hybrid beats BM25 by ≥ 5 points Recall@3 held out; no language −2 points | Aliases + BM25 |
| Reranker | Same at fixed K ≤ 20, plus K = 50 | Recall@3 at both K | ≥ 3 points at K = 20, nothing lost at K = 50 | BM25 order |
| Extractor | E3 span suite | Snapped-entity accuracy, pass^3, null-when-absent, script leaks | doc 53 R12 | Code candidates + Pick |
| Checker | Graded EXPLAIN outputs (doc 44/46 labels) | AUROC, flag rate on passes | doc 53 R11 | Claim matcher |
| Selector / flag | doc 16 §5 instruments | Accuracy, `NoMatch` recall, `Clarify` precision, safety split | Beat `RuleSelector` and `GenerativeSelector` | Both |
| Calibrator | pick / pick-hard, shifted splits | ECE, Brier, risk-coverage | doc 53 R4 (held-out ECE ≤ 0.10) | K = 3 voting |
| Language ID | Short callsign-heavy lines in 8 languages | False-positive rate, wrong-language recall | FP ≤ 2%, recall ≥ 0.95 | Unicode-script check alone |
| Spelling / grammar | Synthetic briefings and radio lines | False flags per 1,000 words, glossary effect | ≤ 5 false flags per 1,000 words for default-on | None (new lint) |
| Translator | E7 with native graders | Adequacy and fluency 1–5; placeholders and code page 100% | Median ≥ 4 per language | Cloud reference |
| Voice | E5 listening panel | Intelligibility, plausibility, real-time factor | §6 E5 rule | — |

Common to every kind: CPU latency p50/p95 at `-dev none` on the reference machine (a pre-AVX2 CPU included for tier I), peak memory,
the determinism gates of §4.8, malformed-model robustness, and no network. Research tooling goes into a `components/` family of
`tools/local-qual` (proposal), later ported to `plotroom-evals`. Public docs carry aggregates only (doc 53 R13).

### 4.10 Glass box: the journal record and the answered-by chip

- **Record** [I]: `ComponentVerdict` (§4.6) per call, beside the decision's `JournalRecord` (DG017): artifact pin, input digest, score
  or distribution, threshold, outcome (used, shown as advice, ignored, fell back and why).
- **Display**: an "answered by: stage / component / margin" chip on every decision card, taken from the journal; a component panel in
  Settings listing each component, its badge, its binding and a kill switch; flags as advisory lints with their evidence (the matched
  word, the retrieved card, the checker's span).
- **Present confidence as routing, not persuasion**: "unsure: choose between these two" with the code facts behind each option, never
  a model-written reason on a low-margin pick [S26].
- **Local reliability report** (candidate DG): per DecisionKind and per component, the accept, edit and discard rates, how often `X`,
  `Q` or the top-2 card fired, fallbacks and validator rejects, computed from the user's own journal with no telemetry [S20].

### 4.11 Design-gap candidates (listed, not filed)

1. **Component bindings and visibility.** D024's roles (router, writer, scripter, explainer, play-tester, translator) have no slot for
   non-generative or specialist components, and doc 55's knob table (draft) keeps model choice out of presets ("no preset names
   another model", under D023 decision 3 and D024). A component needs its own visible binding, a badge per component kind (D037), a
   plan-card line and a kill switch.
2. **Encoder runtime for non-generative components** (doc 53 §4.9): tiers S, I and H of §4.1, the admission rule of §4.4 and the
   helper of §4.5, including a telemetry-free ONNX Runtime build; amends D022, whose Alternatives and Consequences name only
   generative engines, and would make tier I an exception to the architecture's "embedded inference always out of process"
   resolution (architecture README §8 item 7). Informed by spike S-ENC (§6); decided by the owner (OQ2).
3. **Weights versus data tables in the installer**: does D023 decision 1 cover lingua's n-gram tables, dictionaries, calibration files,
   a shipped BM25 index or precomputed vectors?
4. **Journal record for component outputs** (extends DG017) and the answered-by display.
5. **Qualification suites per component kind** (extends DG012 and doc 21 §12.3).
6. **Local reliability report** from the decision journal (§4.10).
7. **Mozilla's model bucket as a download source** under D008 (enabled by the user, blocked offline, hash-checked).

## 5. What this changes for Wilco's workflows

### 5.1 Per step

| Step (volume) | Today (design) | With components | Effect [I] |
| --- | --- | --- | --- |
| Pick (11 per session; 66 per campaign) | K = 3 permuted samples, adaptive K proposed (DG021) | One-pass letter scoring plus calibration; permuted re-ask on a low margin (~20% of menus) | ~3 → ~1.2 calls per Pick where log-probabilities exist (doc 53 §4.2) |
| Intent Fill (12 per session) | One Fill record | Alias rules; one Pick per remaining field; code span candidates | More but one-token calls; no free-text spans; quote check by construction |
| Enum Fill (17 per campaign) | Record Fill | One Pick per field | Record failures become per-field errors the user sees as chips |
| Explain a finding (6 per session) | ≥ 3B paraphrase with the card | Card-sentence Pick plus templated fix by default; paraphrase on request, checked | ~0.3–1 generative calls per finding instead of ~1.2 |
| Explain or teach (4 per session) | Model Pick over retrieved ids, then text | BM25 menu; Pick; paraphrase | Retrieval costs no model call |
| Routing (≤ 1 per free-text request) | `RuleSelector`, then generative selector | Same, with letter scoring | Share settled by rules [U]; the rest one pass |
| Translation (lines × languages) | Translator role, ≥ 7B or cloud | Firefox drafts; Hy-MT2 for glossary lines; cloud for review assistance only | Draft translation: 0 LLM calls |
| Spelling, grammar, language ID | Not built | Deterministic lints | New capability; no model calls |
| Text slots (176 per campaign) | 2–4B candidates or cloud | Unchanged; phrase-bank Picks for short flavour lines | Each 10% of slots moved to phrase-bank Picks moves ~43 of ~428 writer calls to one-token Picks [share unmeasured] |

### 5.2 Calls per session and per campaign [I]

Baselines are doc 40's strategy B and doc 53 §1.3: a 30-minute session has 35 decisions and about 60 calls (about 48 of them
tiny-candidate work); an 8-mission campaign has 273 decisions and about 650 calls (~198 Pick samples, ~19 enum/extract Fill calls,
~428 text calls).

| Setup | Session, cloud calls | Session, local calls | Campaign | What moved |
| --- | --- | --- | --- | --- |
| Cloud only, today | ~60 | 0 | ~650 cloud | — |
| Cloud only, with this doc | ~50–57 | 0 | ~650 cloud, minus all draft translation | Code span candidates cut extraction repairs; the card-verbatim default serves some findings; BM25 menus let the user pick lookups. The larger lever is code: adaptive K (DG021) |
| CPU-only + free cloud, doc 53 | ~12 | ~40–50 | Picks 9–22 escalated (13–33% of 66; needs doc 53 OQ2); text ~428 | Pick, intent Fill and enum Fill local |
| CPU-only + free cloud, with this doc | **~4–6** | ~45–60 (mostly one-token) | As doc 53, plus translation drafts local | The six finding explanations answered locally (sentence Pick plus template), cloud only when the user asks for a paraphrase |
| 8 GB GPU, local session model | 0 | ~60 today → ~13 Pick calls + ~30–40 one-token field Picks + ~10 paraphrases | Picks ~198 → ~80 local calls; text ~428 local or cloud | Multi-token generation shrinks to explanations and authorship |

For the free tier, 50 calls a day then covers about 8–12 sessions instead of about 4 (doc 53 §4.10) or less than one (today). For a
campaign, text remains the bulk (~428 calls, ~70% of cloud spend, doc 40 §5): components change what a free or CPU-only setup can do
per session, not the cost of authorship. Translation example: a three-language pass over 176 stringtable lines is 528 line
translations; batched at 20 lines per call that is about 27 cloud calls, against no LLM call for Firefox drafts plus native review.

### 5.3 Latency and rate limits

- **Pick**: one pass instead of three samples saves two calls of 0.8–1.1 s each on the reference GPU with llama.cpp Vulkan [V per
  doc 46], up to about 1.6–2.2 s per Pick when samples run one after another [I]; on CPU the per-decision part must stay at 200–400
  uncached tokens (doc 53 §1.1).
- **Spans**: GLiNER2 at 130–208 ms on CPU [V-vendor per doc 53] against 1.0–1.5 s for a session-model Fill on the GPU; code candidates
  in microseconds.
- **Retrieval**: BM25 in milliseconds; a class-A embedder query well under 50 ms [I]; a reranker at 20 pairs about 1–4 s on CPU unless
  batched [I], which is why it is optional.
- **Checkers**: HHEM needs about 1.5 s for 2K tokens on CPU [V-vendor per doc 53], so it only fits L2 on short paraphrases.
- **Rate limits**: OpenRouter's free tier allows 20 requests a minute and 50 a day until $10 of credits has been bought (1,000 a day
  after) [V per doc 48 §6.0]; doc 52 owns the full analysis, and doc 50 the free-default question. Every component call is a
  local call that no provider counts.
- **Token economy** (doc 40): non-LLM components cost nothing per call and send nothing; they do not change cache design, because they
  never sit inside a capsule's frozen prefix (exemplar retrieval stays frozen per model, DG019).

## 6. Experiments to run first

### 6.0 Preconditions and order

- Run only after doc 49's measurement job has finished and the machine is idle; no model runs in CI (doc 53 §5).
- Suites frozen by hash before any run; fixtures synthetic and redistributable, in our own words; a held-out split written by a
  different contributor where doc 16 §5 asks for one; CPU runs at `-dev none`; public docs get aggregates only.
- **E0 = doc 53 stage S4** (letter scoring and calibration) is a precondition, because E1, E2 and E4 use it.
- **S-ENC (runtime spike, beside E1):** tract vs rten vs the sidecar on potion-base-8M, bge-small-en-v1.5, gliner_multi-v2.1 int8,
  mDeBERTa-xnli and a LettuceDetect ModernBERT, plus the sidecar's Qwen3-Reranker-0.6B and bge-reranker-v2-m3. Record the release-binary
  size delta with LTO, cold load, p50/p95 at 128 and 512 tokens on the doc 13 reference machines (a pre-AVX2 CPU included), peak
  memory, parity with reference logits (≤ 1e-4), 20-run bitwise repeat, and typed errors on truncated or corrupt files. Confirm whether
  tract runs DeBERTa-v3 exports, including GLiNER2's LSTM layer [U: no public evidence found]. Add `fxtranslate` on one direction
  (en → cs) with and without `gemmology` (sentences per second, parity with its C++ oracle), and a no-egress check of the candidate
  ONNX Runtime library (built with `--no_telemetry`) with networking denied. Informs design-gap candidate 2; the owner decides it.
- **Order:** E1 (no new runtime) → E4 (reuses doc 16 instruments) → E3 (needs S-ENC for the encoder arms; offline research
  environment first) → E2 (expected negative; reuses E1's tooling) → E5 (plugin prototype, P3). E6 and E7 run whenever convenient.

### E1: Standing Orders card retrieval — BM25, embedder, hybrid, or LLM choice

- **Question:** what should find the right card or entry for a free-text question (C1, C2; doc 30 OQ2)?
- **Suite:** at least 200 queries over the Standing Orders seed set (doc 33 phase 0, DG033): English originals; Czech, Polish and
  Russian versions by native speakers; paraphrase twins; typos and stripped diacritics; later-Arma terms (expected: an alias hit or
  `NotInManual`); 20% unanswerable; 10% carrying injected text.
- **Arms:** R0 code-declared cards (workflow steps; reported separately); R1 aliases + BM25; R2 embedder alone (granite-embedding-97m-r2,
  Qwen3-Embedding-0.6B, multilingual-e5-small as a sanity arm); R3 hybrid R1 + R2 by reciprocal-rank fusion; R4 R3 plus a reranker at
  K = 20 and K = 50 (Qwen3-Reranker-0.6B, bge-reranker-v2-m3); R5 **LLM choice**: the session model letter-scores a menu of R1's (or
  R3's) top 7 plus `none_fit`; R6 LLM choice over all titles, a cost reference only.
- **Metrics:** Recall@1/3/7, MRR, `NotInManual` / `none_fit` accuracy, per language; p50/p95 per query at `-dev none`; index and model
  memory.
- **Decision rules (pre-registered):** (a) an embedder enters the optional tier only if R3 beats R1 by ≥ 5 points Recall@3 on the
  held-out split, no language loses more than 2 points, `NotInManual` accuracy does not fall, and query p95 ≤ 50 ms on the reference
  CPU; (b) a reranker only if R4 adds ≥ 3 points Recall@3 at K = 20 and loses nothing at K = 50; (c) R5 stays as the final step only if
  its top-1 accuracy beats R1's top-1 by ≥ 10 points with `none_fit` recall ≥ 0.9, otherwise the user sees the top 3; (d) if R1 is
  within 2 points of every arm, ship BM25 only.
- **Cost:** minutes of CPU; about 2 GB of downloads (three embedders and two rerankers at Q8_0).

### E2: Reranker pre-filter vs facet menus for large class catalogs

- **Question:** can a reranker, an embedder or BM25 cut a large catalog to 7 options better than code facets (B1)? Expected [I]: no,
  which would confirm doc 47 §4.4 with our own data.
- **Suite:** at least 150 requests for units, vehicles and squads by role or description ("an AT soldier", "something to carry a
  squad", "their medic") over the vanilla catalog and two synthetic mod catalogs from the test kit (odd display names, pseudo-weapons,
  convention adapters); English and Czech/Polish/Russian; near-miss pairs (AT/AA, crew/pilot, APC/IFV, a TR UNLOAD-style pair);
  requests whose class is absent (`X` expected).
- **Arms:** F facet steps (≤ 7; ≤ 3 for sub-1B) with one-pass session-model scoring (baseline); B BM25 top-7 then a Pick; Em embedder
  top-7 then a Pick; RR reranker top-7 of BM25's top 50 then a Pick; C code's best guess alone (control).
- **Metrics:** end-to-end accuracy, pre-filter recall@7, `X` recall, steps, calls and latency per decision.
- **Decision rule:** a pre-filter becomes an optional shortlist only if end-to-end accuracy ≥ F + 5 points held out, recall@7 ≥ 0.98,
  `X` recall no lower and p95 latency no higher than F; even then it runs in shadow first (D023 decision 5).

### E3: GLiNER-style extraction vs LLM Fill spans

- **Question:** what fills the place and target spans of an intent Fill (B5)?
- **Suite:** doc 53's `fill-fields` span subset, expanded to at least 150 requests: English plus native-written Czech, Polish and
  Russian; islands with and without named places (fallback clusters); finding codes such as "CF01" as distractors; typos, stripped
  diacritics; relative places ("the hill north of X").
- **Arms:** L session-model span Fill, quote-checked (today); C code candidates plus a session-model Pick; G GLiNER2-base (English) and
  gliner-x-base (cs, pl, de), snapped by code; N NuExtract3 in the sidecar; G→C (extractor proposes, code snaps, a Pick settles
  ambiguity).
- **Metrics:** exact span, snapped-entity accuracy, pass^3 for generative arms, null-when-absent, hallucinated spans (0 by construction
  for C and G), characters outside the request's script, p50/p95 on CPU.
- **Decision rules:** C is adopted if within 5 points of the best model arm (it is free); an extractor enters tier H only if it passes
  doc 53 R12, beats C by ≥ 10 points held out in at least two languages, and S-ENC admits its runtime; Russian stays on C until an
  extractor covers it.

### E4: Zero-shot and decision-model routing vs the LLM Pick

- **Question:** does anything beat `RuleSelector` plus the session model's letter-scored Pick for workflow routing (A3)?
- **Suite:** doc 16 §5's routing instrument (supported, ambiguous, unsupported, injected), plus a menu-shift split with plugin-added
  workflows, Czech/Polish/Russian phrasing, and hostile briefing text carrying confounder-style strings [S4]; a held-out split by a
  different contributor.
- **Arms:** R `RuleSelector`; G `GenerativeSelector` with K = 3 permuted samples (today); G1 one-pass letter scoring with calibration;
  K kNN over embeddings of qualified example requests [S2]; Z Qwen3-Reranker-0.6B as a zero-shot scorer and bge-m3-zeroshot-v2.0-c in
  the sidecar; D decider-0.8b. A trained SetFit-style head is excluded unless the §7 owner question allows it.
- **Metrics:** accuracy, `NoMatch` recall, `Clarify` precision, false `X`, per class; held-out ECE and risk-coverage; calls and
  latency.
- **Decision rules:** G1 replaces K = 3 under doc 53 R4; a learned arm gets an advisory slot only under all of doc 16 §5 (beat R and G1,
  paired sign test, no safety regression), otherwise it stays in shadow; any arm whose answer changes on the injected split fails
  outright.

### E5: A radio-voice prototype (TTS) for a plugin or helper

- **Question:** can fixed, licence-clean local voices produce usable radio lines in the engine languages (H1)?
- **Setup:** an offline research prototype, outside the product. Piper cs_CZ jirka, pl_PL gosia, de_DE thorsten and fr_FR siwis, plus
  one English Piper voice with an open dataset licence: en_GB alba (CC-BY-4.0) or en_US ljspeech (dataset "public domain"), not
  en_US lessac, whose dataset has its own licence page [V S39]; Kokoro-82M for English, French, Italian and Spanish. The
  product's radio chain (band-pass, saturation, limiter, loudness) applied in code; `.lip` files from the ported CWR algorithm.
- **Suite:** 60 lines per language, in our own words: callsigns, grid digits, unit names, orders of 8 words or fewer, 10 longer
  briefing sentences.
- **Metrics:** a listening panel of at least three native listeners per language: intelligibility (share of words transcribed
  correctly), radio plausibility 1–5, pronunciation errors on callsigns and digits; real-time factor on the reference CPU; voice file
  size; licence per voice; `.lip` timing check.
- **Decision rule:** proceed to a delivery design only if at least three engine languages, Czech included, reach median plausibility ≥ 4
  and intelligibility ≥ 95%, real-time factor ≤ 0.5, and every voice is CC0 or CC-BY with known dataset provenance. Delivery is an owner
  call (OQ5): a first-party helper (tier H) or a T2 plugin. Doc 22 §2.3 rejects stdio plugin servers that Plotroom spawns, so a local
  T2 voice means a loopback server the user runs and types in.

### Also: E6 text hygiene and E7 translation

- **E6** (no model): lingua, spellbook with the code glossary and Harper on synthetic briefings and radio lines in eight languages;
  ship as default-on advisory lints only at the §4.9 bars; otherwise off by default with a one-click enable.
- **E7**: doc 47 §6.4's translation suite gains Firefox, Hy-MT2-1.8B and EuroLLM-1.7B rows next to a cloud reference, with native
  graders, placeholder-heavy military lines, and the code-page and placeholder lints scored as hard failures.

## 7. Training small task models on Plotroom's own data (owner question)

D027 item 6 says "No fine-tuning now", and D048 decision 3 chose adapting the harness over training models. Doc 53 OQ6 already asks
about a post-v1 format-adapter spike. This section lays the question out; it decides nothing, and Appendix A drafts the entry.

- **What could be trained** [I]:
  1. letter or format adapters (LoRA) on a ≤ 1B OSI base, for one-token Picks (doc 53 OQ6);
  2. a span extractor fine-tuned for Czech, Polish and Russian (a GLiNER or mmBERT base), from code-labelled synthetic requests;
  3. a routing or intent head (SetFit style); weak, because menus change with plugins and mods and trained heads do not transfer
     [S7];
  4. an SQS/SQF completion model (FLAME-like, about 60M) [S9]; weak, because the redistributable corpus is small;
  5. calibration parameters: fitted statistics, not training, already allowed as preset data (D048).
- **Benefits** [V/I]: in-domain specialists can beat much larger general models (FLAME [S9]); a small first stage cuts calls where the
  domain is stable (SetFit hybrid [S6]); multilingual span extraction has no off-the-shelf Russian extractor (§3.4).
- **Costs** [I]: labelled data; compute (a 0.2B encoder fine-tune on a few thousand examples is minutes to hours on the reference GPU);
  re-training per base-model release and per target profile; re-qualification of every dependent stage (§4.8); a pinned download per
  artifact; the maintenance debt of every extra model [S21].
- **Data sources** [I]: Plotroom's own generators, which can emit typed decisions labelled by code and filtered by the validators; the
  public corpus of doc 35 is mostly proprietary game content and cannot train weights we distribute; community missions only with
  licences that allow it; the user's journal only through an opt-in, user-reviewed export (DG017), never telemetry.
- **Licence of generated data** [I; not legal advice]: generator output built from Plotroom's code and data is Plotroom's own; request
  paraphrases written by a cloud model may fall under that provider's terms on using outputs to train models [U, per provider]; D037's
  "unclear provenance" rule would apply to our own artifacts, so every training item needs a provenance record; whether shipping trained
  weights carries a GPL "preferred form for modification" obligation for the training data and scripts is [U], so publishing both is
  the safe default.
- **Alternatives that need no training**: per-model presets (D048), zero-shot scoring (§3.3), kNN over qualified examples [S2], and
  code-computed candidates.

## Open questions

1. **Text hygiene in v1 (owner):** should spelling, grammar and language ID ship in v1 as AI-off advisory lints (G1, G2)?
2. **Encoder runtime (owner and technical, D022-level):** sidecar only; plus in-process pure Rust under §4.4 (an exception to the
   architecture's "embedded inference always out of process" resolution); plus the helper process with a telemetry-free ONNX Runtime
   build and `fxtranslate` (§4.5)? Spike S-ENC informs it.
3. **Component bindings (owner):** do component kinds become bindable roles beside D024's six, with their own badges and kill switches
   (design-gap candidate 1)?
4. **Cross-model escalation (owner, doc 53 OQ2):** may a tiny CPU stage escalate visibly to the session model or cloud?
5. **Specialists' delivery (owner):** translation, TTS and ASR as first-party helpers (tier H) or strictly as T2 plugins (doc 22 places
   Radio Voice and the stringtable translator there; a local T2 server must be one the user runs)?
6. **Data versus weights (owner, D023 decision 1):** may deterministic statistical tables (lingua's n-grams), dictionaries, calibration
   files, a BM25 index and precomputed vectors of our own corpora ship in the installer?
7. **Firefox translation models (owner):** enable Mozilla's bucket as a download source under D008, and confirm MPL-2.0 files carry no
   "Incompatible With Secondary Licenses" notice.
8. **Provenance (owner, D037):** does training on closed-model outputs (Kokoro's synthetic audio, GLiNER2's GPT-4o annotations) count as
   "unclear provenance"?
9. **Training our own task models (owner):** Appendix A.
10. **Rank pooling for NLI (technical):** do XLM-R NLI classifiers (bge-m3-zeroshot) give stable, calibrated logits through
    llama-server's rank pooling on the pinned build?
11. **Piper's "personal use and research" wording (owner, legal):** binding on the voices, or advice? The same sentence goes on "we do
    not impose any additional restrictions on voice models", which reads as advice [I; not legal advice].
12. **Completion prior (owner, D014):** may idiom counts derived from official missions ship as Teller's ranking prior?
13. **Preview coexistence (technical, doc 53 OQ7):** can CPU components stay resident while the game runs without hurting its frame rate?
14. **Non-OSI open licences for data-derived artifacts (owner, D037):** may the recommended list admit TTS voices and dictionaries under
    CC0, CC-BY-4.0 or other open content licences with known dataset provenance, or do they stay custom-only as D037's "OSI-approved"
    wording implies (§3.10)? Bekko (CC-BY-4.0) should follow the same answer.

## Findings that affect sibling docs (reported, not fixed)

1. Doc 53 §4.7 and DP-21 keep translation with ≥ 7B specialists or cloud, and doc 47 §3.5 lists no non-LLM engine. Mozilla's released
   Firefox models (about 31M parameters, all seven non-English engine languages; registry generated 2026-09-27) offer a no-LLM draft
   tier that both docs could list [V S38].
2. Doc 22 §1.2 row 1 lists Radio Voice as T2 with "line text, voice id" leaving the machine; a local voice (Piper) would send nothing,
   and doc 22 §2.3 rejects stdio servers Plotroom spawns. Doc 22 should say whether a local voice path is a user-run loopback server or
   a first-party helper.
3. D022's Alternatives dismiss `ort` and candle for missing Vulkan or DirectX backends and constrained decoding; that reasoning is about
   generative engines and does not cover encoders. The encoder-runtime design-gap request should amend D022.
4. Doc 47 §4.3 lists embedder GGUFs for the sidecar; llama-server's default micro-batch of 512 rejects longer encoder inputs, so encoder
   presets must set `ubatch-size` [V S28].
5. D037's manifest rule should state that a library's built-in model list (for example `fastembed`'s, which includes non-OSI models)
   never defines what the Model Manager offers [V S31].
6. The architecture's "embedded inference always out of process" resolution (architecture README §7 row 13 and §8 item 7;
   agent-runtime §3) is written for generative engines. Tier I (§4.1, §4.4) would run small neural encoders in the editor process; the
   design-gap request for the encoder runtime should state whether the resolution covers them.
7. Doc 53 OQ3 weighs ONNX Runtime for GLiNER2, HHEM and LettuceDetect without mentioning telemetry. Official ONNX Runtime 1.29+
   libraries collect trace events on every native platform and upload them over HTTPS on Linux and macOS (§4.5) [V S29], so that
   option needs a `--no_telemetry` build to stay within AGENTS.md's outbound-traffic rule.

## Sources

Repository docs: `docs/architecture/agent-runtime.md` (§2, §3, §6–§9, §13, §14), `crate-map.md` (§2.3–§2.5, §9, §10), `ui-shell.md`
(§6, §8), `validation-and-lints.md` (§6), `game-integration.md` (§7, §9), `extensibility.md`; `docs/research/13`, `14`, `15`, `16`
(§3–§5), `21`, `22` (§1.2, §2.3, §7.1), `23` (§13), `24`, `25` (§4, §6, §7), `26` (§8.2), `29`, `30` (§1.1, §4, OQ2), `31` (§8.2),
`33`, `35`, `38`, `39`, `40` (§1, §2.6, §5, §6, §8), `41`, `42`, `43` (§3.8, §4.2, §4.6), `44`, `46`, `47` (§3–§6), `48` (§6.0), `50`,
`51`, `53` (draft), `55` (draft), `57` (in progress); `docs/research/data/corpus-script-idioms.csv`, `slm-candidates.csv`,
`model-profiles.csv`; `docs/decisions/D003`, `D007`, `D008`, `D010`, `D011`, `D014`, `D018`, `D022`, `D023`, `D024`, `D027`,
`D037`, `D041`, `D047`, `D048`; `docs/decisions/OWNER-QUESTIONS.md`; `docs/design-gap-requests/DG006`, `DG012`, `DG017`, `DG019`,
`DG021`, `DG032`, `DG033`, `DG037`; `tools/local-qual/`.

- **[S1]** LLMRouterBench: <https://arxiv.org/abs/2601.07206>
- **[S2]** kNN routers: <https://arxiv.org/abs/2505.12601>
- **[S3]** Router collapse: <https://arxiv.org/abs/2602.03478>
- **[S4]** Confounder gadgets against routers (COLM 2025): <https://arxiv.org/abs/2501.01818>
- **[S5]** GPT-5 autoswitcher and model picker: <https://techcrunch.com/2025/08/08/sam-altman-addresses-bumpy-gpt-5-rollout-bringing-4o-back-and-the-chart-crime/>,
  <https://techcrunch.com/2025/08/12/chatgpts-model-picker-is-back-and-its-complicated>; Copilot Auto model selection:
  <https://docs.github.com/copilot/concepts/auto-model-selection>,
  <https://github.blog/changelog/2025-12-10-auto-model-selection-is-generally-available-in-github-copilot-in-visual-studio-code/>
- **[S6]** SetFit and LLM hybrid (EMNLP 2024 industry): <https://arxiv.org/abs/2410.01627>
- **[S7]** Trained classifiers vs schema-prompted LLMs for intents: <https://arxiv.org/abs/2608.20371>
- **[S8]** Filter-then-rerank: <https://arxiv.org/abs/2303.08559>; agreement-based cascading: <https://arxiv.org/abs/2407.02348>
- **[S9]** Roblox PII classifier: <https://about.roblox.com/newsroom/2025/11/open-sourcing-roblox-pii-classifier-ai-pii-detection-chat>;
  FLAME: <https://arxiv.org/abs/2301.13779>; PCGML survey: <https://arxiv.org/abs/1702.00539>
- **[S10]** Atlas: <https://arxiv.org/abs/2208.03299>; PopQA: <https://arxiv.org/abs/2212.10511>; BEIR: <https://arxiv.org/abs/2104.08663>
- **[S11]** Sourcegraph: <https://sourcegraph.com/blog/how-cody-understands-your-codebase>; Anthropic contextual retrieval:
  <https://www.anthropic.com/engineering/contextual-retrieval>
- **[S12]** Rerankers at larger K: <https://arxiv.org/abs/2411.11767>; cross-encoders vs GPT-4 rerankers: <https://arxiv.org/abs/2403.10407>
- **[S13]** Prompt Guard bypass: <https://www.robustintelligence.com/blog-posts/bypassing-metas-llama-classifier-a-simple-jailbreak>
  (unreachable at review; mirror <https://blogs.cisco.com/security/bypassing-metas-llama-classifier-a-simple-jailbreak>),
  <https://github.com/meta-llama/llama-models/issues/50>; PIDS-Bench: <https://arxiv.org/abs/2609.15017>; InjecGuard:
  <https://arxiv.org/abs/2410.22770>; CaMeL: <https://arxiv.org/abs/2503.18813>; protectai model:
  <https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2>
- **[S14]** Uncertainty under shift: <https://arxiv.org/abs/1906.02530>; selective QA calibrator: <https://arxiv.org/abs/2006.09462>;
  quantization and calibration: <https://arxiv.org/abs/2405.00632>
- **[S15]** vCache: <https://arxiv.org/abs/2502.03771>
- **[S16]** Copilot client internals: <https://thakkarparth007.github.io/copilot-explorer/posts/copilot-internals.html>; invocation
  filter: <https://arxiv.org/abs/2405.14753>
- **[S17]** IntelliCode retirement: <https://github.com/MicrosoftDocs/intellicode/issues/614>,
  <https://learn.microsoft.com/en-us/visualstudio/ide/intellicode-visual-studio>; JetBrains completion ranking:
  <https://arxiv.org/abs/2205.10692>; Full Line Code Completion: <https://arxiv.org/abs/2405.08704>
- **[S18]** Smart Reply: <https://arxiv.org/abs/1606.04870>, <https://research.google/pubs/smart-reply-automated-response-suggestion-for-email/>,
  <https://blog.acolyer.org/2016/11/24/smart-reply-automated-response-suggestion-for-email/>, <https://arxiv.org/abs/1705.00652>;
  Smart Compose: <https://arxiv.org/abs/1906.00080>,
  <https://thenextweb.com/news/google-disables-some-gmail-smart-suggestions-because-it-cant-fix-ai-gender-bias>; Ghostwriter:
  <https://www.gamedeveloper.com/marketing/here-are-more-details-on-ubisoft-s-narrative-ai-tools-from-gdc-2023>
- **[S19]** Apple summaries and adapters: <https://www.cnbc.com/2025/01/16/apple-disables-ai-notifications-for-news-in-its-beta-iphone-software.html>,
  <https://appleinsider.com/articles/25/07/22/apple-brings-back-notification-summaries-for-news-in-ios-26>,
  <https://machinelearning.apple.com/research/apple-foundation-models-2025-updates>
- **[S20]** Acceptance and productivity: <https://arxiv.org/abs/2205.06537>; validating RAG in operation: <https://arxiv.org/abs/2401.05856>
- **[S21]** Hidden technical debt: <https://papers.neurips.cc/paper/5656-hidden-technical-debt-in-machine-learning-systems.pdf>; ML Test
  Score: <https://research.google/pubs/the-ml-test-score-a-rubric-for-ml-production-readiness-and-technical-debt-reduction/>; Rules of
  ML: <https://developers.google.com/machine-learning/guides/rules-of-ml>
- **[S22]** Small language models for agents (position paper): <https://arxiv.org/abs/2506.02153>
- **[S23]** Planning: <https://arxiv.org/abs/2410.02162>; path planning: <https://arxiv.org/abs/2310.03249>
- **[S24]** Level repair: <https://arxiv.org/abs/2010.06627>; MarioGPT: <https://arxiv.org/abs/2302.05981>; Sokoban:
  <https://arxiv.org/abs/2302.05817>; Morai Maker: <https://arxiv.org/abs/1901.06417>
- **[S25]** EM-Assist: <https://arxiv.org/abs/2401.15298>; schema-constrained intermediate: <https://arxiv.org/abs/2604.21746>; IRIS:
  <https://arxiv.org/abs/2405.17238>; GECToR: <https://arxiv.org/abs/2005.12592>
- **[S26]** Explanations and over-reliance (CHI 2021): <https://dl.acm.org/doi/10.1145/3411764.3445717>
- **[S27]** BTZSC zero-shot classification benchmark: <https://arxiv.org/abs/2603.11991>
- **[S28]** llama.cpp: <https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md>,
  <https://github.com/ggml-org/llama.cpp/blob/master/conversion/bert.py>, <https://github.com/ggml-org/llama.cpp/tree/master/src/models>,
  <https://github.com/ggml-org/llama.cpp/pull/12794>, <https://github.com/ggml-org/llama.cpp/pull/12466>,
  <https://github.com/ggml-org/llama.cpp/pull/26254>, <https://github.com/ggml-org/llama.cpp/blob/master/tools/tts/README.md>,
  <https://github.com/ggml-org/llama.cpp/releases/tag/b11223>, <https://github.com/ggml-org/llama.cpp/issues/28963>; micro-batch report:
  <https://github.com/openclaw/openclaw/issues/128923>; reranker conversion note:
  <https://gist.github.com/VooDisss/42bce4eb5c76d3c325633886c5e348ee>; NLI GGUF: <https://huggingface.co/votepurchase/bge-m3-zeroshot-v2.0-GGUF>;
  HHEM: <https://huggingface.co/vectara/hallucination_evaluation_model>
- **[S29]** `ort` and ONNX Runtime: <https://crates.io/crates/ort>, <https://crates.io/crates/ort-sys>,
  <https://github.com/pykeio/ort/blob/v2.0.0-rc.13/ort-sys/Cargo.toml>,
  <https://github.com/pykeio/ort/blob/v2.0.0-rc.13/ort-sys/build/download/dist.tsv>,
  <https://github.com/pykeio/ort/blob/v2.0.0-rc.13/docs/content/misc/prebuilt-binaries.mdx>,
  <https://github.com/pykeio/ort/blob/main/docs/content/setup/linking.mdx>,
  <https://github.com/pykeio/ort/blob/main/docs/content/backends/index.mdx>,
  <https://github.com/pykeio/ort/blob/v2.0.0-rc.13/src/environment.rs>, <https://crates.io/crates/ort-tract>,
  <https://crates.io/crates/ort-candle>, <https://github.com/microsoft/onnxruntime/releases/tag/v1.30.0>,
  <https://github.com/microsoft/onnxruntime/releases/tag/v1.28.0>,
  <https://github.com/microsoft/onnxruntime/blob/v1.30.0/ThirdPartyNotices.txt>,
  <https://github.com/microsoft/onnxruntime/blob/main/docs/Privacy.md>,
  <https://github.com/microsoft/onnxruntime/blob/v1.30.0/docs/Privacy.md> (1DS telemetry on non-Windows platforms; compare
  <https://github.com/microsoft/onnxruntime/blob/v1.28.2/docs/Privacy.md>, "only implemented for Windows builds"),
  <https://github.com/iossifovlab/gain/issues/1207>, <https://github.com/advisories/GHSA-p893-rvq9-2xf9>
- **[S30]** Pure-Rust engines: <https://github.com/sonos/tract>, <https://github.com/sonos/tract/blob/main/linalg/build.rs>,
  <https://crates.io/crates/tract-onnx>, <https://github.com/robertknight/rten>, <https://github.com/robertknight/rten/blob/main/src/model.rs>,
  <https://github.com/huggingface/candle>, <https://github.com/huggingface/candle/blob/main/candle-nn/src/var_builder.rs>,
  <https://github.com/tracel-ai/burn>, <https://github.com/tracel-ai/burn-onnx>
- **[S31]** Wrapper crates: <https://github.com/Anush008/fastembed-rs> (and `src/common.rs`), <https://crates.io/crates/gline-rs>,
  <https://crates.io/crates/orp>, <https://github.com/codesoda/gliner2-rs>, <https://github.com/mrorigo/gliner2-candle>,
  <https://crates.io/crates/gliner2>, <https://github.com/guillaume-be/rust-bert>, <https://github.com/MinishLab/model2vec-rs>,
  <https://github.com/huggingface/text-embeddings-inference/releases>
- **[S32]** Tokenizers: <https://github.com/huggingface/tokenizers/blob/v0.23.2/tokenizers/src/utils/mod.rs>,
  <https://crates.io/crates/tokenizers>, <https://crates.io/crates/tk-encode>, <https://crates.io/crates/safetensors>
- **[S33]** Embedders: <https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2>,
  <https://huggingface.co/Qwen/Qwen3-Embedding-0.6B>, <https://huggingface.co/BAAI/bge-m3>,
  <https://huggingface.co/api/models/intfloat/multilingual-e5-small>, <https://huggingface.co/nomic-ai/nomic-embed-text-v2-moe>,
  <https://huggingface.co/Snowflake/snowflake-arctic-embed-m-v2.0>, <https://huggingface.co/google/embeddinggemma-300m>,
  <https://huggingface.co/minishlab/potion-base-8M>, <https://huggingface.co/BAAI/bge-small-en-v1.5>; Bekko:
  <https://arxiv.org/abs/2607.25180>; Slavic MTEB subset: <https://arxiv.org/abs/2608.24477>
- **[S34]** Rerankers: <https://huggingface.co/Qwen/Qwen3-Reranker-0.6B>, <https://huggingface.co/BAAI/bge-reranker-v2-m3>,
  <https://huggingface.co/mixedbread-ai/mxbai-rerank-base-v2>, <https://huggingface.co/api/models/Alibaba-NLP/gte-multilingual-reranker-base>,
  <https://huggingface.co/api/models/jinaai/jina-reranker-v2-base-multilingual>
- **[S35]** Zero-shot and NLI: <https://huggingface.co/MoritzLaurer/deberta-v3-base-zeroshot-v2.0>,
  <https://huggingface.co/MoritzLaurer/ModernBERT-large-zeroshot-v2.0>, <https://huggingface.co/MoritzLaurer/bge-m3-zeroshot-v2.0-c>,
  <https://huggingface.co/MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7>,
  <https://huggingface.co/knowledgator/gliclass-modern-base-v3.0>, <https://huggingface.co/knowledgator/gliclass-x-base>,
  <https://huggingface.co/jhu-clsp/ettin-encoder-150m>, <https://huggingface.co/jhu-clsp/mmBERT-base>
- **[S36]** Span extraction: <https://huggingface.co/fastino/gliner2-base-v1>, <https://huggingface.co/fastino/gliner2-multi-v1>,
  <https://huggingface.co/knowledgator/gliner-x-base>, <https://huggingface.co/urchade/gliner_multi-v2.1>,
  <https://huggingface.co/onnx-community/gliner_multi-v2.1>, <https://huggingface.co/numind/NuExtract3>,
  <https://huggingface.co/numind/NuExtract-2.0-2B>
- **[S37]** Checkers: <https://huggingface.co/vectara/hallucination_evaluation_model>,
  <https://huggingface.co/KRLabsOrg/lettucedect-base-modernbert-en-v1>, <https://huggingface.co/KRLabsOrg/lettucedect-210m-eurobert-pl-v1>,
  <https://huggingface.co/KRLabsOrg/lettucedect-v2-mmbert-base>
- **[S38]** Translation: <https://github.com/mozilla/translations>, <https://github.com/mozilla/firefox-translations-models>,
  <https://storage.googleapis.com/moz-fx-translations-data--303e-prod-translations-data/db/models.json> (fetched 2026-09-28, generated
  2026-09-27; re-fetched at review, generated 2026-09-28), <https://docs.rs/fxtranslate/latest/fxtranslate/>,
  <https://github.com/gregtatum/translations> (fxtranslate's repository), <https://github.com/serge-sans-paille/gemmology>,
  <https://github.com/jerinphilip/slimt>, <https://github.com/browsermt/bergamot-translator>,
  <https://huggingface.co/tencent/Hy-MT2-1.8B> (licence change: commit `9a341cd1`), <https://huggingface.co/tencent/Hy-MT2-1.8B-GGUF>,
  <https://huggingface.co/utter-project/EuroLLM-1.7B-Instruct>, <https://huggingface.co/api/models/Helsinki-NLP/opus-mt-en-cs>,
  <https://huggingface.co/google/madlad400-3b-mt>
- **[S39]** Speech synthesis: <https://github.com/OHF-Voice/piper1-gpl>, <https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md>,
  <https://huggingface.co/rhasspy/piper-voices/blob/main/cs/cs_CZ/jirka/medium/MODEL_CARD>,
  <https://huggingface.co/rhasspy/piper-voices/blob/main/pl/pl_PL/gosia/medium/MODEL_CARD>,
  <https://huggingface.co/rhasspy/piper-voices/blob/main/ru/ru_RU/irina/medium/MODEL_CARD>,
  <https://huggingface.co/rhasspy/piper-voices/blob/main/fr/fr_FR/siwis/medium/MODEL_CARD>,
  <https://huggingface.co/rhasspy/piper-voices/blob/main/de/de_DE/thorsten/medium/MODEL_CARD>,
  <https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_GB/alba/medium/MODEL_CARD>,
  <https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_US/ljspeech/medium/MODEL_CARD>,
  <https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_US/lessac/medium/MODEL_CARD>, <https://github.com/thewh1teagle/piper-rs>,
  <https://huggingface.co/hexgrad/Kokoro-82M>, <https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md>,
  <https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX>, <https://github.com/lucasjinreal/Kokoros>,
  <https://huggingface.co/kyutai/pocket-tts>, <https://github.com/KittenML/KittenTTS>, <https://huggingface.co/ResembleAI/chatterbox>,
  <https://github.com/QwenLM/Qwen3-TTS>, <https://huggingface.co/OuteAI/OuteTTS-1.0-0.6B>, <https://huggingface.co/Supertone/supertonic-2>
- **[S40]** Speech recognition: <https://huggingface.co/api/models/openai/whisper-base>, <https://crates.io/crates/whisper-rs>
- **[S41]** Code completion: <https://arxiv.org/abs/2607.04939>, <https://huggingface.co/api/models/Qwen/Qwen2.5-Coder-0.5B>,
  <https://huggingface.co/api/models/Qwen/Qwen2.5-Coder-1.5B>, <https://huggingface.co/api/models/Qwen/Qwen2.5-Coder-3B>,
  <https://huggingface.co/api/models/JetBrains/Mellum-4b-base>, <https://huggingface.co/JetBrains/Mellum-4b-base-gguf>
- **[S42]** Text hygiene: <https://github.com/Automattic/harper>, <https://github.com/pemistahl/lingua-rs>,
  <https://raw.githubusercontent.com/LibreOffice/dictionaries/master/cs_CZ/README_en.txt>,
  <https://raw.githubusercontent.com/LibreOffice/dictionaries/master/ru_RU/README_ru_RU.txt>,
  <https://raw.githubusercontent.com/LibreOffice/dictionaries/master/pl_PL/README_en.txt>, <https://dev.languagetool.org/languages>,
  <https://raw.githubusercontent.com/pemistahl/lingua-rs/main/README.md>
- **[S43]** crates.io API, queried 2026-09-28 (version, licence, date): `fxtranslate` 0.4.2 MPL-2.0; `rten` 0.26.0; `tract-onnx` 0.23.8;
  `candle-core` 0.11.0; `ort` 2.0.0-rc.13 (MIT or Apache-2.0); `fastembed` 7.1.0; `gline-rs` 1.1.0; `lingua` 1.8.0; `harper-core`
  2.11.0; `spellbook` 0.4.2 MPL-2.0; `tantivy` 0.26.2 MIT; `bm25` 2.3.2 MIT; `nucleo` 0.5.0 MPL-2.0; `gaoya` 0.2.2 MIT; `smartcore`
  0.6.15; `linfa` 0.8.1; `whisper-rs` 0.16.0 Unlicense; `piper-rs` 0.2.0 MIT; `safetensors` 0.8.0; `tokenizers` (1.0.0-rc.2 latest);
  `probminhash` 0.1.12 [V per research pass; all re-read at review]. Default features and dependencies read at review for
  `fxtranslate` (default `fast` = `gemmology` + `mmap` + `lean-embed`; `cc` build dependency), `lingua` (all 75 language models by
  default), `tantivy` (default `mmap`, `lz4-compression`, `columnar-zstd-compression`, `stemmer`, `stopwords`), `piper-rs`
  (`ort` =2.0.0-rc.12, `espeak-rs`), `model2vec-rs` 0.3.0 (default `onig`, `hf-hub`), `gline-rs` and `orp` (`ort` =2.0.0-rc.9),
  `fastembed` (`ort` =2.0.0-rc.13) and `tokenizers` 0.23.2. Logs: Drain3 <https://github.com/logpai/Drain3>; LogHub-2.0
  <https://arxiv.org/abs/2408.01585>
- **[S44]** Hugging Face model API, queried 2026-09-28 (licence tag, commit): granite-embedding-97m-multilingual-r2, Qwen3-Reranker-0.6B,
  Qwen3-Embedding-0.6B, gliner2-base-v1, gliner-x-base, bge-m3-zeroshot-v2.0-c, HHEM, bge-reranker-v2-m3, Hy-MT2-1.8B,
  EuroLLM-1.7B-Instruct, Kokoro-82M, whisper-base, potion-base-8M, lettucedect-base-modernbert-en-v1, NuExtract3, Qwen2.5-Coder-0.5B
  (all OSI-tagged) and embeddinggemma-300m (`gemma`), at `https://huggingface.co/api/models/<repo>`
- **[S45]** GNU licence list (Apache-2.0, MPL-2.0 and GPLv3): <https://www.gnu.org/licenses/license-list.html>

## Verification notes

### 2026-09-28, author checks at write-up

- **Verified in this session:** 20 crates on the crates.io API (versions, licences and dates in [S43]); 17 model licence tags and
  commits on the Hugging Face API ([S44]); Mozilla's translation registry (generated 2026-09-27): released models for en ↔ cs, pl, ru and
  en → de, fr, it, es, metrics on `flores200-plus`, parameter counts and file sizes (§3.6). The registry check resolves an earlier
  research note that could not load it.
- **Inherited from this doc's research inputs** (checked on the cited pages by the research passes, not re-read here): the llama.cpp
  converter and server facts, the `ort` and ONNX Runtime facts, tract, rten and candle, the Piper voice cards, the literature numbers
  [S1]–[S27].
- **Not verified:** Bekko's and the Slavic-MTEB paper's claims beyond their abstracts; the LibreOffice pl_PL and other dictionary
  licences; `whatlang`'s licence (not used); any latency or accuracy of any component on Plotroom tasks. **No model was run.**
- **Counts:** the 64-row CSV is the source of every count in the TL;DR and §2.1 (40 algorithm, 9 statistics, 10 small-model, 3
  specialist, 2 LLM; 16 LLM-owned, 41 code-owned and 7 not built today).
- **Hygiene:** public sources only; no private projects; no local paths.

### 2026-09-28, review (licences, sizes, runtimes, numbers, scope, links)

- **Re-verified at the source [V]:** every crate in [S43] (versions, licences, dates; all matched; `whatlang` is MIT) plus the default
  features and dependencies listed there; licence tags, gating and parameter counts of about 50 Hugging Face repositories (all rows of
  §3.2–§3.9; all matched except the corrections below); Mozilla's registry, re-fetched (generated 2026-09-28T00:45Z): every §3.6 value
  matched, and ru → en COMET22 (0.8497) was filled in; `onnxruntime.dll` 16.46 MB, read from the v1.30.0 win-x64 zip's central
  directory; the b11223 asset sizes; llama.cpp's converter registrations, server flags and PR states; Hy-MT2's commit history and
  both licence texts; the Piper voice cards; the lingua, Harper, LanguageTool and LibreOffice dictionary texts; the literature
  numbers of [S1]–[S4], [S6]–[S8], [S12], [S13], [S15], [S17], [S19], [S22], [S23], [S25], [S27]; the model-card numbers of
  [S33]–[S36] and HHEM's card.
- **Corrected in place:**
  1. **`fxtranslate` is not pure Rust on native targets.** Its default `gemmology` feature is a vendored C++ kernel called through FFI
     (built with `cc`), and `mmap` is also a default. It moved from tier I to tier H (TL;DR, §3.6, §4.1, §4.2, §4.4–§4.7, S-ENC,
     CSV G4). The crate is new (July 2026) and published by one owner from a fork of `mozilla/translations`.
  2. **ONNX Runtime telemetry.** From 1.29, official builds collect trace events on every native platform, and on Linux and macOS
     they upload them over HTTPS; source builds default to telemetry on, except through the Windows `build.bat` wrapper. The earlier
     line "pyke and source builds do not" was wrong. §4.5 now proposes a `--no_telemetry` build, the environment switch, the API
     switch and a no-egress test (finding 7).
  3. **llama.cpp and TTS.** `llama-tts` with Qwen3-TTS and Pocket TTS merged on 2026-08-04; both need a speaker reference, which is
     cloning, so the verdict stands with a new reason (§3.7, §4.3).
  4. **D037 and non-OSI open licences.** CC0 and CC-BY-4.0 are not OSI-approved, so the Piper per-voice allowlist is a proposal
     to extend D037, not an application of it. Added OQ14 and marked §3.7, §3.10, §4.7 and CSV H1 and G1.
  5. **Owner scope.** "Settles the shape" became "proposes a shape". Tier I is flagged as an exception to the architecture's
     "embedded inference always out of process" resolution (§4.1, design-gap candidate 2, OQ2, finding 6). The §4.7 "Yes" for a
     shipped BM25 index became "proposed (OQ6)". "D048 decision 2 forbids a preset from naming another model" was really doc 55's
     knob table (draft), and the text now says so. D022 names no llama.cpp build: "already pinned: b11223" became "already
     managed", with b11146 as the build docs 55 and 59 cite.
  6. **Default features.** lingua compiles all 75 language models (about 300 MB of crates) unless `default-features = false`; the
     eight engine languages are about 26 MB. tantivy's defaults pull `zstd` (C) and write index files through `mmap`. Neither BM25
     crate stems Czech or Polish (§3.2, §3.8, §4.4, CSV C1 and G2).
  7. **Numbers and quotes.** kNN-router drift is 2.63 against 3.33–6.67 for the learned routers, not "5.30–6.67". The
     router-collapse claim is now quoted. Roblox's 47,000 samples are its evaluation set, not labelled training data. FLAME won 10 of
     14 settings. Anthropic's 2.9% is for contextual embeddings plus contextual BM25. The "about 10%" GPTQ calibration figure could
     not be found in [S14] and was softened to the abstract's claim. The ABC, Apple and lingua quotes are now exact.
  8. **Facts.** Mellum-4b-base has an official GGUF. Hy-MT2's earlier revisions carry the EU-excluding Tencent Hy Community License.
     The registry hashes only the model file, not the vocabulary or shortlist. The pl_PL dictionary is multi-licensed, and ru_RU's
     BSD-style licence has no advertising clause. Piper's "personal use" sentence is now quoted in full. The English voice for E5 is
     named. `piper-rs` pins `ort` rc.12 and builds espeak-ng. `slimt` is GPL-2.0 per GitHub. The LettuceDetect language coverage is
     now stated.
  9. **Links.** The Smart Reply PDF (404) was replaced with arXiv and the Google Research page. The unreachable Robust Intelligence
     post gained its Cisco mirror. The Hugging Face API template is no longer written as a link. Doc 52 is no longer "planned".
- **Link check:** every URL in this doc and the CSV was fetched. All returned 200 except these four. crates.io pages return 404 to
  non-browser clients and 200 with a browser `Accept` header, and the API confirmed every crate. dl.acm.org returns 403 to scripts.
  The Robust Intelligence post was unreachable, so its mirror was added. The Smart Reply PDF returned 404 and was replaced.
- **CSV:** it parses with Python's `csv` module into 64 data rows of 13 columns. Its counts are unchanged: 40 algorithm, 9
  statistics, 10 small-model, 3 specialist and 2 LLM rows; 16 LLM-owned, 41 code-owned and 7 not built. No verdict or priority
  changed.
- **Not re-verified at review:** [S5], [S9]'s PCGML claim, [S10], [S14]'s magnitudes, [S16], [S18], [S20], [S21], [S24] and [S26];
  GLiNER2's CPU latency and CrossNER numbers (from doc 53); Bekko; EuroLLM's COMET; ONNX Runtime's third-party notices; whether
  pyke's prebuilt libraries include the 1DS client; the loader APIs of tract, rten and candle; the GLiClass, decider and Laya rows.
  **No model was run.**
- **Left for others:** `docs/README.md` does not yet list this doc or `data/ml-components.csv`. D027 item 6 and D048 decision 3 are
  unchanged: Appendix A stays an unfiled proposal.

## Appendix A: proposed owner-question entry (not filed)

Text proposed for `docs/decisions/OWNER-QUESTIONS.md`; the number is assigned when it is filed.

### OWQ-28 (proposed): Training small task models on Plotroom's own data

- **Question.** D027 item 6 ("No fine-tuning now") and D048 decision 3 ("Adapt the harness, do not train the model") rule out training.
  Doc 58 finds that off-the-shelf components and the session model cover most touchpoints, but leaves gaps that a small trained model
  could close: Russian span extraction, one-token Picks on sub-1B CPU models, and possibly a format adapter. May Plotroom train small,
  non-generative task models or adapters on its own data after v1, and under which rules?
- **Source.** Doc 58 §7 and §3.4; doc 53 OQ6; D027 item 6; D048 decision 3; D037; DG017.
- **Options.**
  - (a) **No training** (status quo): presets (D048), zero-shot scoring, kNN over qualified examples and code-computed candidates only.
  - (b) **A post-v1 spike, narrowly:** non-generative heads, extractors or LoRA format adapters on an OSI base of about 1B parameters or
    less; trained only on data Plotroom's own generators produce and code labels, with a provenance record per item; training data and
    scripts published; shipped as separate pinned downloads, never in the installer; recommended only after qualification against the
    untrained baseline (doc 58 §4.9); re-trained and re-qualified per base-model release. Generative fine-tuning stays out.
  - (c) **Training allowed broadly,** including generative models such as an SQS/SQF completion model.
- **Recommended (proposal).** (a) for v1, and revisit (b) after experiments E3 and E4 show where the untrained components fall short.
  (c) is not recommended: the redistributable script corpus is small, the public dialect is mostly the later games', and every base
  release would need re-training.
- **Costs to weigh.** Data creation and labelling; per-base and per-profile re-training; re-qualifying every dependent stage; one more
  pinned artifact per component; the licence position of any cloud-generated training text [U, per provider]; whether trained weights
  bring GPL source obligations for data and scripts [U, legal review].
- **Blocks.** Nothing in v1. After v1: a Russian-capable extractor (doc 58 E3) and sub-1B Pick adapters (doc 53 OQ6).
