# local-qual: local-model qualification spike

A small, reusable harness that measures whether a **local** model served by [Ollama](https://ollama.com) can carry
the Plotroom co-pilot's code-owned step shapes. It answers questions such as "could our harness make a 4B model
effective in the editor?" with numbers instead of impressions.

Research tool, not product code. Python 3.8+ standard library only (`urllib`, `json`, `argparse`, `random`, `csv`, …).
Licence: GPL-3.0-or-later, like the rest of the repository. Every suite item is our own text; engine facts are restated
from `skills/standing-orders` and the research docs cited per item, and no game content is copied.

## What it measures

The harness never asks a weak model to plan or write glue. It asks for one small, typed decision at a time (doc 21
§3.1, doc 25, doc 38) and validates everything. The suites mirror those shapes:

| Suite | Items | Shape | What the model returns | Scored by |
| --- | --- | --- | --- | --- |
| `pick` | 30 | **Pick** from a code-computed menu of 4–7 valid options plus the escape `X` (doc 21 §3.2 allows up to 7) | `{"choice": "<letter>"}` (grammar-constrained enum) | `score.py`: exact |
| `fill` | 12 | **Fill** a small typed record: 8 IntentFill extractions (doc 21 §4.1) and 4 mission-concept cards | the item's JSON schema | `score.py`: schema, fields, quote check, validators |
| `explain` | 10 | Grounded explanation of a lint finding from a reference card | `{"explanation", "fix"}`, ≤ 2 sentences | LLM graders (rubric in the item); `score.py` flags only |
| `text` | 10 | Short templated flavour text (radio lines, titles, briefing and debrief lines) | `{"text"}` | `score.py`: code constraints; quality by LLM graders |
| `knowledge` | 12 | Doc 30's source-verified knowledge tasks, free text | plain text | LLM graders (ground truth + grading in the item) |

Pick categories: waypoint type (5), trigger activation, timer and type (5), no-code module from doc 31's catalogue
(5), cutscene archetype CA01–CA12 from doc 39 (4), mood preset AM01–AM12 from doc 41 (3), workflow routing (5, one
of which is an off-scope request whose only correct answer is the escape), and campaign-arc tags from doc 26 (3).

**Conditions.** `--condition none` sends the request (and, for Pick, the menu with one-line option descriptions) only.
`--condition cards` also appends the item's reference card as `[REFERENCE CARD]`, the way the harness injects Standing
Orders entries and catalog rows. Fill items carry no card (their field glossary is part of the instructions), so for
`fill` the two conditions are identical. Doc 30's earlier results on the knowledge tasks, for comparison: a small
cloud model scored 1/24 without cards and 16/24 with cards; a frontier model scored 17/24 without cards.

**Pick details.** Options have stable keys; letters are assigned at run time over a permutation seeded by (item id,
sample), so the right answer moves between letters across samples, while `none` and `cards` see the same order
(paired comparison). The escape is always last, as `X`. `--why` adds a short bounded `why` field before the choice
(doc 21 §3.2) as a separate variant.

**Sampling.** `--k` samples per item (default 3), with a per-(item, sample) seed. Temperature 0.6 for pick, fill and
text (the harness samples K candidates and votes or validates); 0.2 for knowledge and explain. `num_ctx` 8192,
`keep_alive` 10m, `think: false` (retried without the field if a server rejects it). Every call is independent: no
chat history.

## Metrics (`score.py`)

Per (model, suite, condition, variant):

- **pick:** accuracy per sample and overall; **pass^k** (all k samples of an item correct); **majority-vote
  accuracy** (ties count as wrong); accuracy by category; **position bias** (accuracy by the correct option's letter,
  and how often each letter was chosen); escape rate; two baselines: **random-valid** (mean of 1 / number of real
  options) and **first-option** (share of calls whose correct option landed on `A`, i.e. the score of always
  answering `A`).
- **fill:** schema-valid rate; exact-field accuracy (micro, and per field); all-fields-correct rate; **quote-check**
  pass rate (a quoted span must occur in the request, case-insensitively; empty allowed where the item says so); all
  validators passing (word and length caps, digits, era words, names taken only from the request).
- **text:** pass rate per check (word cap, digits, banned era words, names ⊆ allowed list) and all checks passing.
- **explain:** schema validity, the two-sentence cap, forbidden-pattern hits (invented commands). Grade: `ungraded`.
- **knowledge:** `ungraded` (answer length only).
- **all:** latency p50/p90 (wall clock, including model load on the first call), generation tokens/s
  (`eval_count / eval_duration`), mean prompt and output tokens, and outputs cut at the token cap.

`score.py --grading-out sheet.jsonl` writes one row per knowledge, explain and text answer with the reference material
(ground truth and grading, or rubric and card, or constraints) for the LLM graders. `score.py` scores only run records
(rows with `run_id` and `seed`), so a grading sheet left in `results/` is skipped when you score again.

## Running it

```text
# 1. The model must be in Ollama already:
ollama pull qwen3.5:4b-q4_K_M

# 2. One suite, one condition, k samples. Output: results/<model>__<suite>__<condition>.jsonl
#    (<model> with ':' and '/' replaced by '-'; --why adds a __why suffix)
python tools/local-qual/run.py --model qwen3.5:4b-q4_K_M --suite pick --condition none --k 3
python tools/local-qual/run.py --model qwen3.5:4b-q4_K_M --suite pick --condition cards --k 3
python tools/local-qual/run.py --model qwen3.5:4b-q4_K_M --suite pick --condition cards --k 3 --why
python tools/local-qual/run.py --model qwen3.5:4b-q4_K_M --suite fill --k 3
python tools/local-qual/run.py --model qwen3.5:4b-q4_K_M --suite knowledge --condition cards --k 2
#    The doc 44 battery (304 calls per model) is the four non-`--why` lines above plus:
python tools/local-qual/run.py --model qwen3.5:4b-q4_K_M --suite explain --condition cards --k 2
python tools/local-qual/run.py --model qwen3.5:4b-q4_K_M --suite text --condition none --k 2
python tools/local-qual/run.py --model qwen3.5:4b-q4_K_M --suite knowledge --condition none --k 2

# 3. Score everything under results/ (writes results/summary.csv and results/summary.json)
python tools/local-qual/score.py --grading-out tools/local-qual/results/grading.jsonl
```

Useful flags: `--limit N`, `--offset N` (skip the first N items, so `--offset 6 --limit 6` runs a chunk) and
`--items PW01,F03` select items; `--resume` skips calls already recorded without error
in the output file, so a long run can be split into chunks (for example under a 10-minute command limit) and resumed;
`--dry-run` prints the first request and exits; `--host` overrides `OLLAMA_HOST` (a server bind address such as
`0.0.0.0:11434` is mapped to loopback); `--num-predict`, `--temperature` and `--think-mode omit` override defaults.
`results/` is git-ignored.

### Any Ollama model, including Hugging Face GGUFs

Any model Ollama can run works, since the tool only talks to `/api/chat`. GGUF files hosted on Hugging Face can be
pulled directly by Ollama and then used under the same name:

```text
ollama pull hf.co/<user>/<repo>:<quant>          # for example a Q4_K_M or an Unsloth "UD" dynamic quant
python tools/local-qual/run.py --model hf.co/<user>/<repo>:<quant> --suite pick --condition cards
```

A local GGUF file can also be imported with a Modelfile (`FROM ./model.gguf`, then `ollama create <name> -f Modelfile`).
Ollama takes the chat template from the GGUF metadata; a model whose template is missing or wrong will score badly
for reasons unrelated to the model, so check one `--dry-run` and a couple of raw answers first. Comparing two quants
of one model (for example a base Q4_K_M and a UD quant) is just two runs with different `--model` names, scored
together.

Results like these are the kind of evidence a future in-editor list of recommended local models (and a guided
download from Hugging Face) would rest on: doc 21 §3.3 grants a model setup the largest step shape it qualified for.
That feature is not designed here; local inference and model choice are covered by docs 13 and 14.

## Limitations

- **Small n.** 30 picks × k samples gives wide confidence intervals; treat differences under ~10 points as noise
  unless they repeat across k and conditions. Items were written by us, not sampled from real users.
- **Menus are easier than the product's.** Options here are hand-picked distractors with one-line descriptions; real
  menus come from code filters and scores and may be closer calls. Conversely, a real capsule carries more context.
- **One runtime.** Ollama's grammar-constrained decoding, chat templates and default sampler settings shape the
  results; another runtime (llama.cpp server, a Rust in-process engine) may differ. Seeds make runs repeatable on one
  machine and version, not across GPUs or builds.
- **`think: false`.** Hybrid reasoning models are measured in their direct mode only; a thinking run is a separate
  experiment (use `--think-mode omit` and a larger `--num-predict`).
- **Spike-local vocabulary.** The IntentFill `task`, `size` and `time_of_day` values, the concept-card `archetype`
  list (a simplified subset of doc 26 §9.3), the routing ids `explain-finding`, `cutscene-director` and
  `atmosphere-director` (doc 38 defines only `campaign-from-brief`, `populate-town` and `write-briefing`), and the
  explain labels `trigger-cannot-fire`, `detected-by-missing-side`, `global-read-before-init` and `sqs-exitwith` are
  local to this spike; the docs name the concepts but have not fixed these ids yet.
- **Code checks are heuristic.** The names check exempts ordinary sentence-initial words (it still checks all-caps
  tokens and a sentence-initial name used as an address before a comma), so an invented name that opens a sentence can
  slip through. The two-sentence counter splits on `.`, `!` or `?` followed by a capital letter. The era list is short.
- **LLM grading comes later.** Knowledge, explain and text quality need graders; `score.py` leaves them `ungraded`.
- **Not a workflow test.** Each call is one isolated decision; chaining, repair loops, voting across K candidates and
  the effect on a whole campaign run are out of scope here.

## Files

| Path | Role |
| --- | --- |
| `run.py` | Runner: builds prompts per suite, calls Ollama `/api/chat` (`stream: false`), writes JSONL records |
| `score.py` | Scorer: summary CSV and JSON, console table, optional grading sheet |
| `suites/knowledge.json` | Doc 30's 12 knowledge tasks: prompt, ground truth, grading, card, evidence |
| `suites/pick.json` | 30 Pick menus: request, options (key, label, one-line description), escape, answer key, card, rationale, sources |
| `suites/fill.json` | 12 Fill items: request, instructions, schema, expected values, validators; banned era words |
| `suites/explain.json` | 10 findings: code, message, mission facts, card, schema, rubric (required facts, forbidden claims and patterns) |
| `suites/text.json` | 10 flavour-text slots: context, constraints (word cap, allowed names, digits, era, tone), schema; name allowlist |

Each JSONL record holds the item id, model, suite, condition, variant, sample, seed, the raw content, `parse_ok`,
`parsed`, latency, `prompt_eval_count`, `eval_count`, `eval_duration` and the other Ollama timings; Pick records also
hold the permutation, the correct letter and position, and the chosen letter and key.

## Verification notes

- 2026-09-27, smoke test on `qwen3.5:4b-q4_K_M` (Ollama 0.34.3, GTX 1070 8 GB), k = 1: pick `PW01` answered `D` =
  `hold` (correct; 39 s cold, of which 33 s was model load; 0.6 s warm), fill `F01` returned a schema-valid record
  with all five fields correct (1.5–2.2 s, about 39 tokens/s). `think: false` was accepted. `score.py` produced the
  summary for both. (The full spike ran later the same day; see the last note.)
- 2026-09-27, adversarial review of the pick, fill, explain and text suites (counts unchanged: 30/12/10/10). Requests
  that repeated the answer's description word for word were reworded (PC01–PC04, PA01–PA03, PK02), and a scripted check
  now finds no three-word run shared between any pick request and its answer's description. Other fixes: PT02 got its
  own Detected-by card and lost an answer-only parenthetical; PT03's non-timer distractor became a timer one; PC03
  gained the CA12 near miss; PM03 no longer promises "a different house each time"; E04's rain values now fit the rain
  band (maximum rain is 1.5 × overcast − 1); E02 states that a title-layer BLACK OUT never clears; E06 is a spike-local
  label; `isNil` and `terminate` left the automatic patterns (a correct answer may say them); the radio cards follow
  doc 26 §7.3 and doc 39 CA10 (code adds callsigns and prowords, the model writes the body); X10 dropped the names
  check (title-case cards); F07 accepts `island`. `score.py` reports records made with the earlier suite files as stale
  (their `suite_sha` differs), including the smoke-test records above.
- 2026-09-27, full spike on the same machine: `qwen3.5:4b-q4_K_M`, `ibm/granite4.1:3b-q4_K_M`,
  `ministral-3:3b-instruct-2512-q4_k_M` and `gemma4:e4b-it-qat`, one model at a time, 304 calls each (pick none/cards k = 3,
  fill k = 3, explain cards k = 2, text k = 2, knowledge none/cards k = 2), with 0 errors, 0 parse failures and 0 stale records.
  Knowledge, explain and text were graded by LLM graders from the `--grading-out` sheet. Results, verdicts and recommendations are
  in `docs/research/44-local-model-qualification-spike.md`, and the aggregates in `docs/research/data/local-qualification.csv`.
- 2026-09-27, review of the spike: re-scoring the 28 raw files reproduced every summary value. Scoring a second time with the
  grading sheet written to `results/grading.jsonl` (as in "Running it") read the sheet back through the default `results/*.jsonl`
  glob and doubled the knowledge, explain and text call counts; `score.py` now keeps only rows with `run_id` and `seed`, and two
  consecutive re-scores both reproduce the run's summary. The Pick row above now gives the suite's real menu size (4–7 options).
