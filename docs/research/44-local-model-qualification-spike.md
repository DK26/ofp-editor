# Local model qualification spike

Research doc 44 for Plotroom (`ofp-editor`). Research and run date: 2026-09-27. Audience: contributors and LLM coding agents. This file is
meant to be read on its own.
Question answered (owner, paraphrased): could our harness make Qwen 3.5 4B (the UD quant or the base one) effective in the editor? The
owner's follow-up: the editor could one day recommend local models that fit the user's machine and download and install them, perhaps
straight from Hugging Face.

**Status.** Measurements are **[V]**. Verdicts, recommendations and the Model Manager sketch are proposals **[I]**.
**Epistemic legend.** **[V]** measured in this spike (every number re-derived from the raw call records, the scorer output or the grade
files) or verified in the cited doc or tool. **[V per doc N]** taken from a sibling doc. **[I]** our inference or proposal. **[U]** unknown.
**Data.** Aggregates are in [`data/local-qualification.csv`](data/local-qualification.csv) (columns `model, suite, condition, metric, value,
n, notes`; 748 rows). The harness is [`tools/local-qual/`](../../tools/local-qual/README.md). Raw call records, grader notes and the run
driver stay local (`results/` is git-ignored), as in doc 30.
**Relation to sibling docs.** Doc 14 picks the model tiers and names the candidates; doc 13 the runtime and the download manager; doc 21
the step shapes (§3), when a model earns a role (§2.2) and qualification (§12.3); doc 25 the weak-model harness and its evaluation plan
(§11); doc 30 the twelve knowledge tasks and their cards. D022 accepts the Model Manager and D023 the model tiers. This doc adds the
first local measurement on real hardware.
**Hygiene.** Every suite item is our own text. Model answers are only paraphrased, and no game content is quoted.

## TL;DR

- **Yes, for the small steps the harness keeps small; no for free-text engine knowledge.** Qwen3.5-4B (Q4_K_M, thinking off) on a GTX 1070
  picked the right option in 90% of 90 menu calls without cards and 93% with them, against a 19% random-valid control. All three samples
  were right on 83% and 87% of the 30 menus. It explained lint findings from a reference card with 20 of 20 graded passes, and kept
  90% of flavour lines inside every code constraint [V].
- **Where it fails.** Answering engine questions freely gave 0 of 24 passes, all 24 with a hallucination; with doc 30's perfect cards, 6 of 24
  (doc 30's small cloud proxy: 16 of 24). A Fill got 83% of fields right but the whole record in only 47% of calls, and 3 of 12 records right
  in all samples. So a Fill is a pre-fill the user confirms, and only its closed fields qualify [V].
- **The harness carries the weight.** 1,216 calls gave 0 parse or schema failures (the output grammar is enforced during decoding), 0
  invented-command patterns in explanations, and the one off-scope request was answered with the escape `X` in every sample by every
  model [V].
- **The four models.** Gemma 4 E4B QAT led the code-scored steps: Pick 95.6% (pass^3 0.93), Fill fields 92% with 97% of records passing
  all validators, text constraints 100%. Qwen3.5-4B led the graded explanations. Granite 4.1 3B matched Qwen on Pick at half the latency
  and the least memory. Ministral 3 3B was weakest (Pick pass^3 0.67 without cards, text constraints 50%) [V]. On Pick, the top three
  are within noise of each other at n = 30 [I].
- **Spike verdicts** (doc 25's bar: beat the random-valid control and reach pass^k ≥ 0.8):
  - Pick qualifies for Qwen, Granite and Gemma, and for Ministral only with cards.
  - Explanations qualify with cards for Qwen and Granite.
  - Text qualifies only as code-checked candidates the user picks from (Qwen, Granite, Gemma).
  - Fill never qualifies as a whole record, only per field. Archetype and time of day qualify for all four models, side for three,
    the place span for two, task and size for one each, and the target span for none.
  - Knowledge qualifies for no model.

  These are spike verdicts, not doc 21 §12.3 qualification [I on V].
- **Cards.** On Pick they helped the weakest model most (Ministral pass^3 0.67 → 0.80) and changed little for the rest. On knowledge they
  lifted every model from 0 to 5–8 passes of 24. What remains is doc 30's residue, the right fact in the wrong form and whole files: T04,
  T06 and T12 failed for all four models in both samples. That is work for typed actions and the checker [V; I].
- **Facts belong to code.** On one menu, a helicopter dropping *another* group's infantry, the right answer is TR UNLOAD. The models
  missed it in 23 of 24 samples (22 times choosing UNLOAD), even with a card that spelled out the difference. When code knows the
  deciding fact, it filters the menu instead of asking [V; I].
- **Fit and speed on an 8 GB card.** Every model ran fully on the GPU at an 8K context. Each added 2,898–4,352 MiB (2.8–4.25 GiB) on
  top of the ≈2,700 MiB (2.6 GiB) the desktop already used, leaving 1,140–2,594 MiB (1.1–2.5 GiB) of the 8,192 MiB free. Median
  latency was 0.31–0.75 s for a pick and 1.0–1.5 s for a fill, at 37–61 tokens/s. The 304-call battery took 3.9–7.3 minutes per
  model [V].
- **UD versus base.** Only the standard 4-bit library builds were tested: three Q4_K_M and Gemma's QAT Q4_0. The UD comparison takes one
  `ollama pull hf.co/…:UD-Q4_K_XL` and a rerun of `tools/local-qual` with the sampler pinned. At 30 menus a small quant effect will not
  show, so it also needs a harder instrument (§1.6, §5.4) [V; I].
- **Recommendation.** The Model Manager the owner already accepted (D022) should recommend local models by *measured* fit on the
  user's GPU and show a badge per step kind, never one score.
  - Provisional default for 8 GB GPUs (measured with 32 GB of system RAM): Gemma 4 E4B QAT for Pick and Fill. Qwen3.5-4B Q4_K_M is
    the equal alternative, and Granite 4.1 3B the low-VRAM option. A confirmation run settles the default.
  - Knowledge answers, Compose and Draft steps, scripts and final prose stay with code, cards or a cloud model.
  - A download is always the user's action in Settings, never an agent tool (D022; §5.3) [I on D022].

## 1. Setup

### 1.1 Machine and runtime [V]

| Item | Value |
| --- | --- |
| GPU | NVIDIA GeForce GTX 1070, 8,192 MiB, driver 582.66; about 2,700 MiB already in use by the desktop and other processes with no model loaded |
| RAM, OS | 32 GB; Windows 10 Pro 22H2 (build 19045) |
| Runtime | Ollama 0.34.3 (`ollama --version`), native `/api/chat` with `stream: false`, on the NVIDIA GPU (the backend library was not logged); every model reported `100% GPU` at `CONTEXT 8192` |
| Harness | `tools/local-qual/run.py` and `score.py`, standard-library Python, suites as they stood in the working tree on 2026-09-27 (every record carries the suite file's hash; 0 stale records) |

### 1.2 Models [V]

All four are 4-bit instruct builds from the Ollama library. Parameter counts, quantisations, capabilities and licences are from
`ollama show`; disk sizes from `ollama list`.

| Ollama tag | Family (doc 14 row) | Params | Quant | Disk | Licence | Build notes |
| --- | --- | --- | --- | --- | --- | --- |
| `qwen3.5:4b-q4_K_M` | Qwen3.5-4B, doc 14's T1 candidate | 4.7B | Q4_K_M | 3.4 GB | Apache-2.0 | Hybrid thinking, **on by default** in this build; vision included; build defaults top_k 20, top_p 0.95, presence penalty 1.5 |
| `ibm/granite4.1:3b-q4_K_M` | Granite 4.1 3B (doc 14 lists Granite 4.2-3B as the router option) | 3.4B | Q4_K_M | 2.1 GB | Apache-2.0 | No thinking mode; no sampler defaults in the build |
| `ministral-3:3b-instruct-2512-q4_k_M` | Ministral 3 3B Instruct 2512 (doc 14 §3.2) | 3.8B | Q4_K_M | 3.0 GB | Apache-2.0 | Vision included; build default temperature 0.15 (overridden, §1.4) |
| `gemma4:e4b-it-qat` | Gemma 4 E4B (doc 14 §3.2; doc 14's low-memory fallback is E2B) | 7.5B with per-layer embeddings | **Q4_0, QAT** | 6.1 GB | Apache-2.0 | Hybrid thinking, **on by default**; vision and audio projector included; build defaults top_k 64, top_p 0.95 |

### 1.3 Procedure [V]

- One model at a time, in the order above. Before each model's first job, an empty warm-up call loaded it. After its last job it was
  unloaded with `ollama stop`, and `ollama ps` was empty before the next one loaded. Load time, job times and the `ollama ps` and
  `nvidia-smi` readings were logged per model.
- Every model got the same seven jobs, 304 calls each and 1,216 in total, with 0 HTTP errors, 0 timeouts and 0 parse failures:

| Suite | Shape (doc 21 §3.1) | Items | Condition(s) | k | Calls per model |
| --- | --- | --- | --- | --- | --- |
| `pick` | Pick one letter from a code-computed menu of 4–7 real options plus `X` | 30 | none, cards | 3 | 90 + 90 |
| `fill` | Fill a small typed record: 8 intent records, 4 mission-concept cards | 12 | none (Fill items carry no card) | 3 | 36 |
| `explain` | A grounded two-sentence explanation of one lint finding, plus a fix | 10 | cards (the product always sends the card) | 2 | 20 |
| `text` | One short flavour line: radio body, title, briefing or debrief line | 10 | none | 2 | 20 |
| `knowledge` | Doc 30's twelve free-text engine questions | 12 | none, cards | 2 | 24 + 24 |

- **Conditions.** `none` sends the request only; for Pick the menu carries a one-line description per option. `cards` also appends the
  item's reference card, the way the harness injects Standing Orders entries and catalog rows. The knowledge prompts and cards are
  byte-identical to doc 30's task file.
- **Pick menus.** The categories are waypoint type (5), trigger activation and timer (5), no-code module (5, doc 31), cutscene archetype
  (4, doc 39), mood preset (3, doc 41), workflow routing (5, one of them an off-scope request whose only right answer is `X`) and campaign
  arc (3). Options are shuffled per (item, sample) with a fixed seed, so the right answer moves between letters. `none` and `cards` see
  the same order, so the two conditions compare item by item.

### 1.4 Decoding and sampling [V]

- `think: false` on every call; the server accepted it, and no record contains thinking text. The hybrid models (Qwen, Gemma) were
  therefore measured in direct mode only. Both builds turn thinking **on** by default, so a harness must switch it off explicitly.
- Structured suites (pick, fill, explain, text) pass the item's JSON schema as Ollama's `format`, so decoding is constrained by a grammar,
  as a product harness would do (doc 13 §4). Knowledge answers are free text.
- Temperature 0.6 for pick, fill and text, where the harness samples K candidates and votes or validates, and 0.2 for knowledge and
  explain. Seed per (item, sample); `num_ctx` 8192; output caps of 64 / 320 / 120 / 700 / 320 tokens (pick / fill / text / knowledge /
  explain). Every call is independent, with no chat history.
- Not pinned: top_k, top_p and presence penalty came from each build's own defaults (§1.2), so the sampler is not identical across models
  (§6).

### 1.5 Scoring [V]

- **By code** (`score.py`): Pick exact match, pass^k (all k samples of an item right), majority vote (a tie counts as wrong), position
  bias, escapes, and two controls, random valid option and always `A`. Fill: schema validity, field accuracy, all fields right, a quote
  check (a quoted place or target must occur in the request) and all validators. Text: word caps, digits, banned era words, and names
  taken only from the allowed list. Explain: schema, the two-sentence cap and invented-command patterns.
- **By LLM graders:** knowledge (against doc 30's ground truth and rubric), explain (required facts and forbidden claims) and text
  quality. Each model's answers were graded in a separate single pass, with a pass / partial / fail verdict, a hallucination flag and a
  note per answer. The four grader passes were not calibrated against each other (§6).

### 1.6 "UD or base": what was and was not tested

- **Tested:** the standard library quant of each model. For Qwen that is `qwen3.5:4b-q4_K_M`, the "base" quant in the everyday sense
  [V].
- **UD** usually means Unsloth's "Dynamic" GGUF quants, such as `UD-Q4_K_XL`. As we understand the publisher's description, they choose
  the precision per tensor instead of applying one scheme to the whole model [I], and they are published as separate GGUF repositories.
  Doc 14 §3.2 lists Qwen3.5-4B at 2.74 GB for Q4_K_M and 2.91 GB for UD-Q4_K_XL, and doc 14 §6 already says to "qualify both" [V per
  doc 14]. Whether the dynamic quant scores better on *our* steps is unmeasured [U]. No UD build was installed on the test machine.
  The Ollama library build measured here is 3.4 GB on disk, probably because it also carries the vision parts [I].
- **"Base" as a pretrained-only checkpoint** (no instruction tuning) would be a different model, not a quant. It is not a harness
  candidate: every step here relies on instruction following, and the grammar can force a valid shape but not a sensible choice [I].
  Whether a pretrained-only Qwen3.5-4B checkpoint is published was not checked [U].
- **How to run the UD comparison with `tools/local-qual`** (the README documents the `hf.co/` pull; this run did not exercise it):

```text
ollama pull hf.co/<user>/<repo>:UD-Q4_K_XL
ollama show hf.co/<user>/<repo>:UD-Q4_K_XL     # compare template, parameters and thinking default with qwen3.5:4b-q4_K_M
# Pin the sampler to the library build's values, so only the weights differ (Modelfile:
#   FROM hf.co/<user>/<repo>:UD-Q4_K_XL / PARAMETER top_k 20 / PARAMETER top_p 0.95 / PARAMETER presence_penalty 1.5)
ollama create qwen3.5-4b-ud -f Modelfile
python tools/local-qual/run.py --model qwen3.5-4b-ud --suite pick --condition none --k 3
python tools/local-qual/run.py --model qwen3.5-4b-ud --suite pick --condition cards --k 3
python tools/local-qual/run.py --model qwen3.5-4b-ud --suite fill --k 3
python tools/local-qual/run.py --model qwen3.5-4b-ud --suite explain --condition cards --k 2
python tools/local-qual/run.py --model qwen3.5-4b-ud --suite text --condition none --k 2
python tools/local-qual/run.py --model qwen3.5-4b-ud --suite knowledge --condition none --k 2
python tools/local-qual/run.py --model qwen3.5-4b-ud --suite knowledge --condition cards --k 2
python tools/local-qual/score.py --grading-out tools/local-qual/results/grading.jsonl
```

  These are the same seven jobs (304 calls) as this run. The seeds depend only on (item, sample), so the UD run pairs item by item
  with this one, provided this run's raw files (kept outside the repository) are copied into `results/` next to it and the suite
  files are unchanged (otherwise `score.py` reports the old records as stale). Re-scoring is safe with the grading sheet inside
  `results/`: `score.py` skips rows that are not run records. Two checks come first: `ollama show` must report the same chat
  template family, and the records must show `thinking_chars` 0 with `think: false`. A GGUF whose template is wrong scores badly for
  reasons unrelated to the weights (README). Using `FROM` on a pulled `hf.co/` name inside a Modelfile is our reading
  of Ollama's model naming, not something tried here [I].

## 2. Results per suite

### 2.1 Pick [V]

Controls: a random valid option scores **0.191** and always answering `A` scores **0.156**. Invalid-output rate: **0%** in every run.

| Model | Condition | Accuracy (95% Wilson) | pass^3 (30 menus) | Majority of 3 | Off-scope `X` | False `X` | p50 / p90 ms | tokens/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen3.5-4B | none | 0.900 (0.82–0.95) | 0.833 | 0.900 | 3/3 | 0/87 | 650 / 724 | 39 |
| Qwen3.5-4B | cards | 0.933 (0.86–0.97) | 0.867 | 0.967 | 3/3 | 0/87 | 755 / 813 | 42 |
| Granite 4.1 3B | none | 0.911 (0.83–0.95) | 0.833 | 0.933 (1 tie) | 3/3 | 0/87 | 310 / 344 | 56 |
| Granite 4.1 3B | cards | 0.889 (0.81–0.94) | 0.867 | 0.900 | 3/3 | 0/87 | 330 / 428 | 55 |
| Ministral 3 3B | none | 0.833 (0.74–0.90) | 0.667 | 0.867 (2 ties) | 3/3 | 1/87 | 323 / 385 | 61 |
| Ministral 3 3B | cards | 0.911 (0.83–0.95) | 0.800 | 0.967 | 3/3 | 0/87 | 351 / 468 | 60 |
| Gemma 4 E4B QAT | none | 0.956 (0.89–0.98) | 0.933 | 0.967 | 3/3 | 1/87 | 510 / 536 | 45 |
| Gemma 4 E4B QAT | cards | 0.956 (0.89–0.98) | 0.933 | 0.967 | 3/3 | 0/87 | 628 / 703 | 45 |

The Wilson intervals treat the 90 calls as independent. The three samples of one menu are correlated, so the real uncertainty is wider
[I]. The two false escapes were the same legitimate request ("what does warning AL02 mean"), sent to `X` once each by Ministral and
Gemma without cards.

**Accuracy by category** (none / cards):

| Category (menus) | Qwen | Granite | Ministral | Gemma |
| --- | --- | --- | --- | --- |
| Waypoint type (5) | 0.53 / 0.67 | 0.80 / 0.80 | 0.67 / 0.73 | 0.80 / 0.80 |
| Trigger activation and timer (5) | 0.87 / 1.00 | 0.87 / 0.73 | 0.67 / 0.93 | 1.00 / 1.00 |
| No-code module (5) | 1.00 / 0.93 | 1.00 / 1.00 | 0.93 / 0.93 | 1.00 / 0.93 |
| Cutscene archetype (4) | 1.00 / 1.00 | 1.00 / 1.00 | 0.92 / 0.92 | 1.00 / 1.00 |
| Mood preset (3) | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| Workflow routing (5) | 1.00 / 1.00 | 1.00 / 1.00 | 0.80 / 0.93 | 0.93 / 1.00 |
| Campaign arc (3) | 1.00 / 1.00 | 0.67 / 0.67 | 1.00 / 1.00 | 1.00 / 1.00 |

- **Taste and routing are easy; engine semantics are hard.** Mood, cutscene, module and routing menus were near perfect, the lowest
  being Ministral's routing without cards (0.80). Granite got a third of its arc picks wrong in both conditions, mostly on one menu
  (PK03). The misses concentrate on menus where the engine's meaning differs from the everyday word: waypoint types and Countdown
  versus Timeout [V]. Across the 8 runs, the menus that failed pass^3 most often were PW04 (8 of 8 runs), PT03 and PW02 (4), and
  PW05, PT02, PT04 and PM05 (3 each) [V].
- **PW04 is a harness lesson, not a model score.** The request is a helicopter that drops *another* group's infantry. The right answer, TR
  UNLOAD, was chosen in 1 of 24 samples. The other 23 went to UNLOAD, which empties only the group's own passengers (22), or to MOVE
  (1), even when the card said so in capitals. Whose passengers they are is a fact code knows. By doc 21 §2.1–§2.2, code should drop
  UNLOAD from that menu (rung 1), not ask a model to overrule the word's plain meaning [I].
- **Cards on Pick.** Paired by menu at pass^3, cards fixed 2 menus and broke 1 for Qwen, the same for Granite, fixed 5 and broke 1
  for Ministral, and fixed 1 and broke 1 for Gemma [V]. The option descriptions already carry most of what the cards say, so cards
  matter mainly for the weakest model [I].
- **Voting helps.** A majority of 3 samples raised menu-level accuracy with cards to 0.967 for Qwen, Ministral and Gemma (per-call
  accuracy 0.933, 0.911 and 0.956). This is consistent with doc 25's K > 1 (H4) at the single-decision level, but it is not a test of
  H4, which compares K > 1 with verifiers against extra exemplars [V; I].
- **No first-option bias.** Models chose `A` when `A` was wrong in 0–5 of 76 calls (Qwen 3 → 1, Granite 1 → 1, Ministral 5 → 2, Gemma 0 →
  0, none → cards) [V]. Accuracy was *lower* when the right answer sat on `A`, in all eight runs, by 0.3–15 points. That is 14 calls
  per run, and the none and cards runs share the same shuffles, so it is not evidence of a bias either way [V; I].
- **Doc 25 H2 holds for single decisions.** Every model beats the random-valid control by 64–77 points, so doc 25's kill rule is not
  triggered at this level [V; I]. End-to-end fidelity (E3, E4, E10) remains unmeasured.

### 2.2 Fill [V]

Controls over the 56 expected fields: picking uniformly from each enum scores **0.158**; answering `unspecified` (or an empty span where
allowed) scores **0.393**. Schema-valid output: **100%** for every model.

| Model | Field accuracy | All fields right (per call) | All fields right, pass^3 | Quote check | All validators | Validators, pass^3 | p50 / p90 ms | tokens/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen3.5-4B | 0.833 | 0.472 | 3/12 | 0.861 | 0.750 | 8/12 | 1,541 / 2,732 | 37 |
| Granite 4.1 3B | 0.792 | 0.389 | 4/12 | 0.917 | 0.806 | 9/12 | 1,030 / 1,822 | 49 |
| Ministral 3 3B | 0.839 | 0.417 | 4/12 | 0.694 | 0.639 | 7/12 | 1,363 / 2,134 | 52 |
| Gemma 4 E4B QAT | **0.923** | **0.639** | **7/12** | **1.000** | **0.972** | **11/12** | 1,470 / 2,179 | 40 |

**Per field** (accuracy per call; in brackets, the items on which all 3 samples were right):

| Field (items) | Qwen | Granite | Ministral | Gemma |
| --- | --- | --- | --- | --- |
| `task` (8) | 0.71 (4/8) | 0.67 (4/8) | 0.67 (5/8) | 1.00 (8/8) |
| `place` span (8) | 0.96 (7/8) | 0.75 (6/8) | 0.92 (6/8) | 0.88 (7/8) |
| `side` (12) | 0.94 (10/12) | 0.81 (8/12) | 0.97 (11/12) | 1.00 (12/12) |
| `size` (8) | 0.54 (3/8) | 0.58 (3/8) | 0.88 (7/8) | 0.67 (5/8) |
| `time_of_day` (12) | 0.94 (10/12) | 0.97 (11/12) | 0.97 (11/12) | 1.00 (12/12) |
| `archetype` (4) | 1.00 (4/4) | 1.00 (4/4) | 1.00 (4/4) | 1.00 (4/4) |
| `target` span (4) | 0.58 (1/4) | 0.75 (3/4) | 0.00 (0/4) | 0.83 (3/4) |

- **Closed fields with a clear cue work; judgement fields do not.** Side, time of day and archetype were nearly always right. `size`
  (is a "squad" medium? is "dense" large?) and `task` on meta requests went wrong most often. Asked why the campaign graph shows CF01,
  Qwen chose `other` in all three samples, and Granite (once) and Ministral (twice) chose `campaign-from-brief`. Qwen and Granite read a
  "four-mission campaign" request as a populate task in 2 of 3 samples [V].
- **Spans.** Ministral copied whole clauses instead of the target (0 of 12 calls right). That fails the span expectation even where the
  clause passes the quote check [V]. Gemma quoted the finding code "CF01" as a place in all three samples: the quote check passes
  because the text is in the request, but the fact is wrong [V]. A quote check proves the text was not invented; it does not prove the
  text is the right thing [I].
- The `size` and `task` vocabularies are spike-local (README, Limitations), so part of the `size` error may be our wording [I].

### 2.3 Grounded explanation, with the card [V]

| Model | Schema valid | ≤ 2 sentences | Invented-command patterns | Graded pass / partial / fail | Hallucination | Pass in both samples | p50 / p90 ms | tokens/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen3.5-4B | 1.00 | 1.00 | 0 | 20 / 0 / 0 | 0 | 10/10 | 2,446 / 2,914 | 38 |
| Granite 4.1 3B | 1.00 | 0.90 | 0 | 18 / 2 / 0 | 0 | 8/10 | 1,737 / 2,127 | 49 |
| Ministral 3 3B | 1.00 | 1.00 | 0 | 16 / 4 / 0 | 0 | 6/10 | 2,038 / 2,660 | 53 |
| Gemma 4 E4B QAT | 1.00 | 1.00 | 0 | 13 / 7 / 0 | 2 | 5/10 | 2,310 / 2,615 | 40 |

- No explanation failed outright. Every model reached a pass on 8–10 of the 10 findings in at least one of its two samples [V].
- Gemma's seven partials split into three weak "why" sentences with a correct fix and four flawed fixes. Two of those are its two
  hallucinations: the same invented one-line syntax, proposed as the fix for the SQS early-exit finding (E10) in both samples. On the
  nil-global finding (E06), one sample moved the fix into `init.sqf`, a file that runs only on CWR and CE (doc 04), and on E02 one fix
  trailed off unusably [V].
- Grader strictness appears to differ. Qwen's grader passed answers with minor misquotes or overstatements, while Gemma's graded
  comparable gaps as partial (§6). The ranking inside the top three is not settled [I].

### 2.4 Flavour text [V]

| Model | All code checks | Word cap | Names allowed | No digits | Checks pass in both samples | Mean words | Graded pass / partial / fail | Quality pass in both samples | p50 / p90 ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen3.5-4B | 0.90 | 0.95 | 0.94 | 1.00 | 8/10 | 8.0 | 7 / 11 / 2 | 2/10 | 673 / 997 |
| Granite 4.1 3B | 1.00 | 1.00 | 1.00 | 1.00 | 10/10 | 6.4 | 6 / 14 / 0 | 2/10 | 408 / 554 |
| Ministral 3 3B | 0.50 | 0.60 | 0.69 | 0.90 | 3/10 | 13.4 | 3 / 10 / 7 | 0/10 | 648 / 837 |
| Gemma 4 E4B QAT | 1.00 | 1.00 | 1.00 | 1.00 | 10/10 | 8.6 | 5 / 15 / 0 | 2/10 | 651 / 783 |

- **Constraints are learnable; taste is not there yet.** Granite and Gemma kept every line inside the code checks and Qwen 90% of them,
  but graders passed only 15–35% of lines as ready to use. Most partials are fixable by the harness, not the model. This suite ran
  without cards, so the radio style card was not shown, and models put callsigns in the message body, which code framing then
  duplicates. A few lines were awkward titles or purple prose [V; I].
- **Candidates, not final text.** With two samples, Qwen, Granite and Gemma produced a pass or a usable partial on 9–10 of 10 slots [V].
  So the slot should offer the user 2–3 checked candidates (doc 21 §2.2 item 4) [I].
- Ministral ran long (mean 13.4 words) and broke the word cap and the names list most often [V].
- The "character trait" slot failed or was partial for every model, and no model wrote a specific human trait. Qwen and Ministral wrote
  action scenes; Granite and Gemma wrote stock adjectives [V].

### 2.5 Speed, memory and fit on an 8 GB card [V]

| Model | Disk (`ollama list`) | Loaded (`ollama ps`) | GPU memory in use (MiB of 8,192) | Added over ≈2,700 MiB desktop | Free after load | Warm load | tokens/s | 304-call battery |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen3.5-4B | 3.4 GB | 3.3 GB | 6,734–6,747 | ≈ 4,050 MiB | ≈ 1,445 MiB | 5.9 s | 36–42 | 7.3 min |
| Granite 4.1 3B | 2.1 GB | 2.9 GB | 5,586–5,598 | ≈ 2,900 MiB | ≈ 2,595 MiB | 7.8 s | 49–56 | 3.9 min |
| Ministral 3 3B | 3.0 GB | 3.2 GB | 6,677–6,692 | ≈ 3,990 MiB | ≈ 1,500 MiB | 18.1 s | 52–61 | 4.8 min |
| Gemma 4 E4B QAT | 6.1 GB | 3.1 GB | 6,934–7,052 | ≈ 4,350 MiB | ≈ 1,140 MiB | 13.2 s | 40–45 | 5.5 min |

- All readings were taken at `num_ctx` 8192 with the model reported as `100% GPU`, so no layers ran on the CPU. The load times are warm,
  with the files already in the OS cache. An earlier smoke test saw a cold first load of about 33 s for Qwen, so a first load in the
  editor will be slower.
- **Reported sizes are not fit.** For Gemma, `ollama ps` said 3.1 GB, but the card's total use rose by about 4,350 MiB (4.25 GiB). Its
  6.1 GB download also contains the vision and audio parts; how the bytes split was not checked [U]. A fit estimate must come from
  measured GPU memory for the exact build and context size, not from the file size or the runtime's size column [V; I].
- **Latency supports interactive use.** A pick's median wall time was 0.31–0.75 s and a fill's 1.0–1.5 s. Three sequential samples per
  decision would take about 1–2.3 s for a pick and 3–4.6 s for a fill on this GPU [V; I, arithmetic]. Free-text knowledge answers
  without cards were slow and long for Qwen (p90 10.9 s; 572 characters on average against 285–425 for the others), and one Ministral
  answer hit the 700-token cap [V].

## 3. Knowledge with and without cards, against doc 30

Same twelve tasks, same prompts, same cards (doc 30 §3.2), two samples each. Doc 30's models, sampler and grader differ, so compare the
rows as orders of magnitude, not exact figures [I].

| Model and condition | Pass | Partial | Fail | Pass rate (95% Wilson) | Score (partial = ½) | Hallucination |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen3.5-4B, none | 0 | 0 | 24 | 0% (0–14%) | 0% | 24 |
| Qwen3.5-4B, cards | 6 | 9 | 9 | 25% (12–45%) | 44% | 6 |
| Granite 4.1 3B, none | 0 | 0 | 24 | 0% (0–14%) | 0% | 20 |
| Granite 4.1 3B, cards | 8 | 6 | 10 | 33% (18–53%) | 46% | 6 |
| Ministral 3 3B, none | 0 | 1 | 23 | 0% (0–14%) | 2% | 24 |
| Ministral 3 3B, cards | 5 | 12 | 7 | 21% (9–40%) | 46% | 7 |
| Gemma 4 E4B QAT, none | 0 | 0 | 24 | 0% (0–14%) | 0% | 22 |
| Gemma 4 E4B QAT, cards | 6 | 8 | 10 | 25% (12–45%) | 42% | 10 |
| *Doc 30: small cloud proxy, none* | 1 | 3 | 20 | 4% (1–20%) | 10% | 10 |
| *Doc 30: small cloud proxy, cards* | 16 | 6 | 2 | 67% (47–82%) | 79% | 2 |
| *Doc 30: frontier, none* | 17 | 5 | 2 | 71% (51–85%) | 81% | 2 |

Per task with cards (`P` pass, `a` partial, `f` fail, `H` after a letter marks a hallucination; two samples; doc 30's
matrix carries no per-answer hallucination marks):

| Task | Qwen | Granite | Ministral | Gemma | Doc 30 proxy, cards |
| --- | --- | --- | --- | --- | --- |
| T01 SQS timing | P P | P P | a P | a a | P P |
| T02 conditional exit | fH fH | P P | fH a | a fH | P P |
| T03 comments | a aH | fH fH | a a | fH fH | P P |
| T04 spelling and existence | f fH | fH fH | fH fH | fH fH | a f |
| T05 trigger context | P P | P P | P a | P P | P P |
| T06 "group wiped out" condition | f f | f f | fH fH | fH fH | P a |
| T07 `mission.sqm` top level | P P | a P | a a | P P | P P |
| T08 `description.ext` | a a | a a | P P | a a | P P |
| T09 campaign endings | a a | P a | a a | a a | a P |
| T10 `saveVar` | a fH | f f | a a | fH a | a a |
| T11 editor group rules | aH a | a a | P a | P P | P P |
| T12 `briefing.html` and objectives | f f | fH fH | fH fH | fH fH | f a |

- **Without cards, local 3–4B models must not answer engine questions.** No model passed any of its 24 answers (Ministral got one
  partial; every other answer failed), and each hallucinated in 20–24 of them. They almost never declined, although the system prompt
  allowed "if unsure, say so". Gemma declined one task once and Granite part of one, while doc 30's proxy declined all twelve tasks in
  one sample. Typical failures, paraphrased: waits and exits borrowed
  from later titles, `object.member` access, C-style `if` blocks, and a `briefing.html` written as a web page with JavaScript [V].
- **Cards help a lot but not enough.** Passes rose from 0 to 5–8 of 24 and hallucinations fell to 6–10. That is still well below the
  small cloud proxy with the same cards (16 passes, 2 hallucinations). Only Granite's interval (up to 53%) overlaps the proxy's (from
  47%); the other three end at 40–45% [V].
- **The residue is doc 30's residue.** T04 (a binary command written as a prefix), T06 (a counting expression) and T12 (a whole briefing
  file) failed for every model in both samples. Doc 30 §3.4 already assigns these to code: typed actions write files and conditions (L1),
  and `script.check` catches the form errors (L3) [V; I].
- **Card format matters for small models.** With the card, Qwen still wrote member access on T02. Twice it copied the card's signature
  notation into its code: a stray `nular` on T02 and `objStatus | binary` on T12 [V]. Cards meant for weak models should show copyable
  usage lines, not signature tables [I].
- **Implication.** In the product, a local model never answers a free-text engine question. Code shows the card itself (doc 30 L2), and a
  local model may add at most a grounded two-sentence explanation in the §2.3 shape, which did work [I].

## 4. Qualification verdicts

**Rule applied** [I, from doc 25 §11.2 and its open question 2, doc 21 §2.2 and §12]:

1. Every output parses and is schema-valid (100%).
2. The model beats the step's control: random-valid for Pick (0.191) and Fill fields (0.158). There is no control yet for explain and
   text; code checks and graders stand in.
3. pass^k ≥ 0.8 over items: Pick pass^3 over 30 menus; Fill pass^3 per record and per field; explain and text quality as a graded pass in
   both samples; text constraints as all code checks passing in both samples; knowledge as a graded pass in both samples.
4. Must-pass safety: the off-scope request answered `X` in every sample (Pick); 0 invented-command patterns (explain).

**Labels.** **Qualified**: met in the `none` condition. Fill (whose items carry no card) and text (three of whose ten slots have a
radio style card that was not sent) ran only in that condition. **Qualified with cards**: met only with the reference card injected.
For explain the card is always part of the step, so this is its product configuration. **Not qualified**: not met.

**Scope.** These are *spike verdicts*. Doc 21 §12.3 grants qualification only after n consecutive all-pass trials on the product's own
instrument: 14 for 80% at 95% confidence, 29 for 90%. It also needs paired evidence against the next simpler decider (doc 21 §2.2 item
6). Neither is shown here, so a product badge built on this run must say "spike-checked", not "qualified" [I].

| Step kind (instrument) | Qwen3.5-4B Q4_K_M | Granite 4.1 3B Q4_K_M | Ministral 3 3B Q4_K_M | Gemma 4 E4B QAT |
| --- | --- | --- | --- | --- |
| Pick (30 menus, pass^3) | **Qualified** (0.83; 0.87 with cards) | **Qualified** (0.83; 0.87) | **Qualified with cards** (0.67 → 0.80, at the bar) | **Qualified** (0.93; 0.93) |
| Fill, whole record (12 records, pass^3) | Not qualified (0.25) | Not qualified (0.33) | Not qualified (0.33) | Not qualified (0.58) |
| Fill, per field (pass^3 ≥ 0.8) | **Qualified**: archetype, place, side, time of day. Not: task, size, target | **Qualified**: archetype, time of day. Not: side (0.67), place, task, size, target | **Qualified**: archetype, side, size, time of day. Not: place, task, target (0.00) | **Qualified**: archetype, side, task, time of day, place. Not: size (0.63), target (0.75) |
| Grounded explanation (10 findings, pass in both samples) | **Qualified with cards** (1.0) | **Qualified with cards** (0.8) | Not qualified (0.6) | Not qualified (0.5; 2 hallucinated fixes) |
| Flavour text, code constraints (10 slots, both samples) | **Qualified** (0.8, at the bar) | **Qualified** (1.0) | Not qualified (0.3) | **Qualified** (1.0) |
| Flavour text, quality as final text (both samples) | Not qualified (0.2) | Not qualified (0.2) | Not qualified (0.0) | Not qualified (0.2) |
| Free-text knowledge, no card | Not qualified (0 of 24) | Not qualified (0 of 24) | Not qualified (0 of 24) | Not qualified (0 of 24) |
| Free-text knowledge, with card (pass in both samples) | Not qualified (0.25) | Not qualified (0.25) | Not qualified (0.08) | Not qualified (0.25) |

The per-field Fill verdicts rest on 4–12 items each and are the least stable in this table. Several "qualified" cells sit exactly at the
bar (Ministral Pick with cards, Qwen text constraints, Granite explanations), and one more miss would flip them [I].

**Answer to the owner's question** [I on V]:

- The harness makes Qwen3.5-4B effective for Pick (menus of valid options), for grounded two-sentence explanations with a card, and for
  flavour-line *candidates* that code checks.
- It makes Qwen useful but not autonomous for Fill: closed fields qualify, and the record is a pre-fill the user confirms.
- It does not make Qwen, or any 3–4B model here, reliable for free-text engine knowledge, even with perfect cards.
- Whether the UD quant changes any of this is unmeasured.

## 5. Recommendations [I]

### 5.1 Default local model per step kind on 8 GB GPUs

| Step kind | Recommended build (Ollama tag) | Alternative | Notes |
| --- | --- | --- | --- |
| Pick | Gemma 4 E4B QAT (`gemma4:e4b-it-qat`) | Qwen3.5-4B Q4_K_M; Granite 4.1 3B Q4_K_M when VRAM is tight | K = 3 with a majority vote; cards on; code filters menus by known facts (PW04) |
| Fill | Gemma 4 E4B QAT | Qwen3.5-4B Q4_K_M | Admit only the qualified fields; the user confirms the pre-filled card; `size` and free spans become a Pick with computed options, or a question |
| Grounded explanation | Qwen3.5-4B Q4_K_M | Granite 4.1 3B Q4_K_M | Always shown next to the card and the computed finding; the fix is admitted only if it passes the checker |
| Flavour text | Granite 4.1 3B or Gemma 4 E4B QAT, as 2–3 candidates | Qwen3.5-4B Q4_K_M | Show the style card (radio: no callsigns in the body); code frames callsigns; the user picks |

- **One model per session on an 8 GB card.** Any two of these models (2.8–4.25 GiB each) do not fit next to a ≈2.6 GiB desktop, and
  swapping costs 6–18 s per warm load. So the 8 GB default is **one** model.
- **Provisional default: Gemma 4 E4B QAT.** It leads on Pick and Fill, the steps local models are meant to carry (doc 21 §13.4). Its
  explanations stay card-first until a single-grader rerun settles its 13 of 20.
- **Equal alternative: Qwen3.5-4B Q4_K_M.** The download is 3.4 GB instead of 6.1, it gives the best explanations, and it qualifies on
  Pick. Its UD quant is the next run.
- **Low-VRAM option: Granite 4.1 3B Q4_K_M.** It adds ≈2,900 MiB (2.8 GiB), is the fastest, and qualifies on Pick, explanations
  and text constraints. Its Fill is limited to two fields.
- **Not recommended:** Ministral 3 3B.
- **Build settings.** Whichever model is chosen, the harness sends thinking off explicitly (both hybrid builds default to on), pins the
  sampler, and records the exact artifact (doc 14 §5).
- **Gate for the default.** The confirmation run in §5.4 items 1–3 decides the final default; until then these are candidates.

### 5.2 What stays cloud or code

- **Code, at every tier:** facts and fact-bearing menu filters (whose passengers, which side, distances, counts), whole files
  (`mission.sqm`, `briefing.html`, `description.ext`), conditions and script lines (doc 30 L1), and the answer to any engine question
  (show the card, doc 30 L2).
- **Cloud or a stronger local tier (doc 14 T2 and T3):** free-text explanations beyond one finding, Compose and Draft steps (doc 21 §3.1),
  SQS authoring and repair, campaign premises and final briefing or dialogue prose, and translation (doc 14 §6).
- **Local, behind checks:** Pick, the qualified Fill fields, grounded explanations with a card, and flavour-line candidates.

### 5.3 How the Model Manager should present this

The owner's follow-up asks for recommended local models and an in-editor download, possibly straight from Hugging Face. The owner
has already accepted that feature as the Model Manager (D022 decision 4; D023 for the model tiers), and which models it may recommend
was then still open (OWQ-19; answered 2026-09-27: OSI licences with no field-of-use limit and qualified, everything else "custom",
D037). This spike gives it its first evidence. The sketch below builds on D022, doc 13 §6 (manifest and download) and
doc 14 §5 (packs, licences); all four measured builds are Apache-2.0, which fits D023 decision 6.

- **It is a user feature, not an agent tool.** The Model Manager lives in Settings. The user browses, downloads, deletes and selects
  models. Every download is started by the user, never by the agent (D022 decision 4, D008; AGENTS.md: no network or file access
  beyond the product's own user-driven flows; doc 21 §12.2's "download a mod" no-tool case). We propose that the agent also does not
  suggest downloads on its own [I].
- **Hardware first.** On open, read the GPU name, total and free VRAM, system RAM and the available backend: the user's server (Ollama,
  LM Studio), a managed llama.cpp sidecar (doc 13 Phase B), or CPU. Show free VRAM *as measured now*, since the desktop alone used
  2,700 MiB of 8,192 here.
- **Fit from measurements, never from file size.** Each recommended build's manifest row carries the measured GPU memory increase at a
  stated context size, per backend (2,898–4,352 MiB at 8K here), and tokens/s on named reference GPUs. Fit badges follow from those rows:
  - **Fits**: the increase plus a safety margin (proposed: 512 MiB) is at most the free VRAM.
  - **Tight**: under 1.5 GiB would remain; say so before a Preview.
  - **Partial offload**, slower and unmeasured.
  - **CPU only**, unmeasured.

  "Runs on 8 GB" always names what is 8 GB (GPU here, not system RAM; doc 13 §11).
- **Per-step badges, not a score.** Doc 21 §12.3 forbids one star rating. Each row shows one badge per step kind:
  - Pick: *Spike-checked* / *Qualified* / *With cards* / *No*;
  - Fill: *Fields: side, time, archetype* and similar;
  - Explanation: *With card*;
  - Text: *Candidates*;
  - Knowledge: *No; cards are shown instead*.

  Each badge links to its evidence: instrument version (suite hash), n, date, runtime version and sampler. A badge applies to that exact
  artifact only (weights hash, quant, template, sampler, thinking setting; doc 14 §5).
- **Recommended list = pinned manifest.** A small `models.toml`, updatable without a release (doc 14 §7), lists pinned builds with repo,
  revision, file, bytes, SHA-256, licence and chat template id (doc 13 §6), plus this doc's measurements and verdicts. The list is
  ordered by fit on *this* machine, then by the step kinds the user's chosen workflows need.
- **Download routes.**
  1. Through the user's own Ollama: `/api/pull`, including `hf.co/<user>/<repo>:<quant>` names. This route was not exercised in this run
     [U].
  2. Through the managed sidecar, which downloads the pinned GGUF from Hugging Face with Range resume, a size and SHA-256 check and an
     atomic install (doc 13 §6, spike S4).

  Show the licence and the download size before the user confirms. Gated repositories need the user's own token.
- **Any other Hugging Face GGUF is allowed, labelled "Unqualified".** Offer **"Check this model on my machine"**: the product's own port
  of these suites, about 300 calls, 4–8 minutes on a GTX 1070-class GPU at the speeds measured here. It records per-step results for that
  exact setup, labelled "local check, n = 30 menus". It widens doc 21 §12.3's smoke check but is not a guarantee.
- **Preview and the game.** The model is unloaded before Preview launches the game (doc 13 §6), since a 4 GB model and the game share the
  same 8 GB. Loading it again afterwards costs 6–18 s warm, or about 33 s cold.
- **Role binding stays visible.** The UI shows which step kinds run locally and which go to the cloud, with no silent switch (doc 21
  G5).

### 5.4 Next measurements

1. **Confirmation run for the default.** Gemma 4 E4B QAT, Qwen3.5-4B Q4_K_M and Granite 4.1 3B on a doc 25 E4-sized Pick instrument: 100
   menus, 20 with a planted "none fit", k = 3. Run it long enough to test doc 21 §12.3's 14 (or 29) consecutive all-pass trials per
   step.
2. **One grader for everything.** Re-grade explain, text and knowledge for all four models in one grader pass with a fixed rubric
   prompt. Add a blind human panel for text (doc 25 §11.2: LLM judges only as a pre-screen).
3. **UD versus Q4_K_M** for Qwen3.5-4B, with the sampler pinned (§1.6), paired by item.
4. **Harder menus.** Closer distractors, 7 options, menus generated by code from real filters and scores, more escapes (this run had
   one), and the `Q` "ask me" escape.
5. **Doc 25 H5.** The `--why` variant (a short reason before the letter), and thinking on versus off for the hybrid models, with the
   latency cost.
6. **Bigger local models.** Qwen3.5-9B and Gemma 4 12B QAT on this 8 GB card (a partial offload is expected) and on 12–16 GB cards: does
   Fill reach pass^3 ≥ 0.8 per record?
7. **Non-English.** Czech, Polish and Russian requests for Fill (quote check with diacritics) and text (codepage lints) (doc 25 open
   question 6; doc 14 §9 item 4).
8. **Realistic cards.** Cards selected by code instead of perfect ones (doc 30 open question 2), and one card per rule-bearing Fill field
   (doc 30 §4.2).
9. **Other machines and runtimes.** CPU-only with 16 GB RAM, an iGPU through Vulkan, a 6 GB GPU, and llama-server as the planned sidecar
   against Ollama for parity (doc 13 S1, S5). Include cold loads and model swaps.
10. **Text with the style card** and code-stripped callsigns, to confirm that most partials were harness-fixable.

## 6. Limitations

- **Small n.** The suites are small: 30 menus, 12 Fill records, 10 findings, 10 text slots and 12 knowledge tasks, at k = 2–3.
  Intervals are wide (Qwen Pick accuracy 0.82–0.95), and they are too narrow anyway, because samples of one item are correlated. Treat
  differences under about 10 points as noise unless they repeat across conditions.
- **One machine, one runtime.** The run used a GTX 1070 under Windows 10 with Ollama 0.34.3, 32 GB of system RAM, one context size
  and warm loads. That machine is in D023's T2a hardware class (8–12 GB VRAM or 32 GB RAM), while the models are T1 candidates. Doc 14
  §5 assumes about 16 GB of RAM for T1 and treats 8 GB-RAM machines as unqualified; nothing here measures a machine with less RAM, so
  "8 GB" in this doc always means the GPU.
  Another GPU, backend (Vulkan, CPU), runtime (llama-server, an in-process engine) or build may differ. Seeds make runs repeatable only on
  the same machine and version.
- **LLM graders.** Each model's answers were graded in a separate single pass, with no human adjudication and no calibration across the
  four passes. The explain ranking in particular may reflect grader strictness. The hallucination flag is a grader's judgement. Text
  quality needs people.
- **Synthetic tasks, written by us.** The menus use hand-picked distractors and one-line descriptions, and may be easier or harder than
  product menus. The Fill vocabulary is spike-local. There is one escape item. The knowledge cards are perfect, so they are an upper bound
  on retrieval (doc 30 §3.6). The same team wrote the items and the rubrics.
- **Sampling not like for like.** Temperatures were fixed per suite, but top_k, top_p and presence penalty came from each build's
  defaults. Only direct mode (`think: false`) was measured. Each call is one isolated decision: chaining, repair loops, K-candidate
  admission and whole-campaign effects are out of scope (README).
- **Builds.** These are Ollama library tags identified by their short digests. Gemma is QAT Q4_0, not Q4_K_M. Granite is 4.1, not doc
  14's 4.2. Gemma is E4B, not doc 14's low-memory E2B. Qwen, Ministral and Gemma ship vision (and, for Gemma, audio) parts that a
  text-only build would not load.
- **Uneven conditions.** Fill ran without cards only, explain with cards only, and text without cards only, so the style card's effect
  on text is inferred, not measured.
- **Memory figures.** GPU use is the card's total from `nvidia-smi` minus an approximate 2,700 MiB desktop baseline (the readings logged
  after each `ollama stop` were 2,701–2,704 MiB). The card was read twice per model, after the load and after the last job, so a
  transient peak between the two would not show. The runtime's own size column did not match it for Gemma.
- **Reproducibility.** The suites, runner and scorer live in `tools/local-qual/`, but raw records and grader notes are not in the
  repository (as in doc 30). The CSV holds every aggregate used here.

## Open questions

1. **The bar.** Is pass^3 ≥ 0.8 right for every step kind, and should product badges require doc 21 §12.3's 14 consecutive all-pass trials
   (doc 25 open question 2; doc 21 open question 3)? [U]
2. **Fill granularity.** Should qualification be per field, and should judgement fields such as `size` become computed Picks? [I]
3. **Quant effects.** Is a UD-versus-Q4_K_M difference visible at all without a harder instrument? [U]
4. **Gemma's footprint.** Would a text-only E4B GGUF keep these scores with a smaller download and less GPU memory? [U]
5. **One model or two.** On 8 GB cards, one model per session, or per-role binding with 6–18 s swaps? [I]
6. **Local checks.** How should a "check this model on my machine" result sit next to our reference results, and which suites can ship
   in the product without Python (a Rust port of the instrument with recorded cassettes, doc 25 §11.2)? [U]
7. **Hugging Face route.** Should the first release pull through the user's Ollama (`hf.co/` names) or through the managed sidecar (doc 13
   Phase B), and which licence and gating checks run before the download starts? [U]
8. **Card format.** Do usage-line cards beat signature-table cards for 3–4B models (the T02 copy error, §3)? [U]

## Sources

**Repository docs.**

- `docs/research/13-local-inference-in-rust.md`: §3 (Ollama), §4 (constrained decoding), §6 (download and model management), §9
  (phases), §11 (spikes S1–S5).
- `14-model-selection.md`: §3.2 (candidates and GGUF sizes, including UD-Q4_K_XL), §5 (hardware, pack policy, artifact identity), §6
  (tiers), §7, §9.
- `21-agent-doctrine.md`: §2.1–§2.2, §3.1–§3.3, §12.1–§12.4, §13.4, open question 3.
- `25-weak-model-friendly-campaign-harness.md`: §11.1–§11.3, open questions 2 and 6.
- `30-domain-knowledge-and-guidance.md`: §3.1–§3.6, §4.1–§4.2, open question 2.
- `31-no-code-ladder-modules-rules-and-scripting.md`, `39-cutscene-director.md`, `41-atmosphere-sound-and-music.md`: the source catalogs
  for the module, cutscene and mood menus.
- `38-harness-workflows.md`: the routing ids.
- `docs/decisions/D022-local-inference-and-model-manager.md` (decision 4, the Model Manager), `D023-model-strategy.md` (tiers,
  decision 6 on licences), `D008-outbound-network-sources.md`, and `OWNER-QUESTIONS.md` OWQ-19 (which models may be recommended).

**Tools and data.** `tools/local-qual/README.md`, `run.py`, `score.py`, and `suites/{pick,fill,explain,text,knowledge}.json`. The run
used the suites as they stood on 2026-09-27; the records carry each suite file's hash. The knowledge prompts and cards are identical to
doc 30's task file.
`docs/research/data/local-qualification.csv` holds this doc's aggregates.

**Runtime facts.** `ollama --version` (0.34.3); `ollama list` and `ollama show` for sizes, parameters, quantisations, capabilities,
thinking defaults, build sampler parameters and licences; `ollama ps` and `nvidia-smi` during the run (2026-09-27).

**Statistics.**

- Wilson score interval: E. B. Wilson, *JASA* 22 (1927) 209–212.
- pass^k: τ-bench, [arXiv 2406.12045](https://arxiv.org/abs/2406.12045) [V per doc 25].
- The rule of three and the n ≥ ln(1 − c) / ln(p) trial counts: Hanley & Lippman-Hand, *JAMA* 1983 [V per doc 21].

## Verification notes

### 2026-09-27, author checks at write-up

- **Scores.** `summary.csv` and `summary.json` came from `score.py` over the 28 raw files, one per model, suite and condition. Pass^3 per
  menu, false escapes, position-bias counts, per-field pass^3, validator pass^3 and text pass^2 were recomputed from the raw records with
  `score.py`'s own functions, and match its summary where the two overlap.
- **Grades.** Grade counts were recounted from the four grade files; three of them carry their own summary, and the recount matches it.
  The Gemma file has no summary block, so its counts come from the recount alone.
- **Controls.** The Fill controls were computed from the item schemas: uniform over each enum, with span fields counted as wrong unless
  an empty span is accepted.
- **Wilson intervals** use z = 1.96.
- **Runtime facts.** The Ollama version, the model metadata and the GPU driver were read on the test machine after the run.
- **Memory.** The desktop baseline (≈2,700 MiB) is the `nvidia-smi` total logged after each `ollama stop` (2,701–2,704 MiB); no
  reading was logged before the first load, and desktop use drifts, so the "added" column is approximate [I].
- **Not verified:** that `hf.co/` pulls and Modelfile `FROM` on them behave as §1.6 describes (not run); any UD build; any non-NVIDIA,
  CPU or llama-server path.

### 2026-09-27, independent review

A second pass re-derived the doc's numbers with its own script instead of the author's analysis helpers.

- **Raw records.** 1,216 records in 28 files: 0 HTTP errors, 0 parse failures, `think` sent on every call, 0 characters of thinking,
  and every record's suite hash equal to the current suite files. The first call per model reported a load time of about 5 ms, so the
  latencies exclude model loading, as the CSV notes say.
- **Re-scoring.** Re-running `score.py` on copies of the 28 raw files reproduced every value in the run's `summary.csv` (all 28
  rows). Every Pick, Fill and text figure in §2.1, §2.2, §2.4 and §4, including per-menu pass^3, the eight failing-menu lists, the
  fixed and broken menus, false escapes (PR04 twice), position-bias counts, the PW04 choices (22 UNLOAD, 1 MOVE, 1 TR UNLOAD), the
  per-field accuracies and pass^3 counts, and the Fill controls (0.1577 and 0.3929 over 56 fields), matches.
- **Grades.** Verdict and hallucination counts, pass^2 items and the any-pass items were recounted from the four grade files and match
  §2.3, §2.4, §3 and §4; the per-task knowledge matrix matches cell for cell. Doc 30's rows and its "weak, cards" column match doc 30
  §3.3. The knowledge prompts, cards, ground truths and rubrics are identical to doc 30's task file.
- **Runtime facts.** `ollama --version`, `ollama list`, `ollama show` and `nvidia-smi` were re-read on the test machine: version
  0.34.3, the sizes, parameter counts, quantisations, capabilities, thinking defaults, build sampler values and licences of §1.2, and
  driver 582.66 all match. Warm loads, battery times, `ollama ps` sizes and GPU totals match the run log.
- **Cross-references.** Doc 14 §3.2 (2.74 and 2.91 GB) and §6 ("qualify both"), doc 21 §2.1–§2.2, §3.3, §12.2–§12.4 and §13.4, doc 25
  §11.1–§11.3 and open questions 2 and 6, and doc 13 §6 and §11 say what this doc cites them for.
- **Corrected in this review.** Ministral's knowledge-with-cards Wilson upper bound is 40%, not 41% (so the other three intervals end
  at 40–45%). Without cards Ministral had one partial, so "all four failed all 24" was reworded. Gemma's `init.sqf` misplacement was on
  the nil-global finding (E06), not the SQS early-exit finding, and three of its seven explain partials, not most, were weak "why"
  sentences with a correct fix. Text slots X01, X06 and X08 do carry a style card, so the verdict labels no longer say text has none.
  Memory prose now gives MiB and GiB instead of treating 1,000 MiB as 1 GB, the 8 GB default names the GPU and the 32 GB of RAM, the
  memory baseline is attributed to the logged post-unload readings, the §1.6 rerun includes the knowledge `none` job, and the voting
  bullet no longer claims to test doc 25 H4. §5.3 now cites the already accepted Model Manager decision (D022), D023 and OWQ-19, uses
  D022's wording for who starts a download, and marks the stricter "no suggestions" rule as our proposal.
- **Tool fixes.** Re-scoring twice with the README's `--grading-out tools/local-qual/results/grading.jsonl` read the previous grading
  sheet back as records (the default input glob is `results/*.jsonl`): the second run doubled the knowledge, explain and text call
  counts and halved their parse rates. `score.py` now skips rows without `run_id` and `seed`; repeated re-scoring then reproduces the
  run's summary. Python bytecode caches are now git-ignored.
- **Public hygiene.** `tools/local-qual/` (excluding the git-ignored `results/`), this doc and the CSV contain no absolute local paths,
  user names or private-project references. Suite text is our own; the knowledge evidence fields cite upstream source by file and line
  range with short paraphrases, and no mission, campaign or stringtable text is copied.

### Owner answer folded (2026-09-27)

- §5.3 said which models the Model Manager may recommend was still open (OWQ-19). The owner answered (a) on 2026-09-27, recorded as
  D037; §5.3 now says so by pointer. No measurement or recommendation changed.
