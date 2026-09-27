# local-qual: local-model qualification spike

A small, reusable harness that measures whether a **local** model can carry the Plotroom co-pilot's code-owned step
shapes. It answers questions such as "could our harness make a 4B model effective in the editor?" with numbers instead
of impressions. Two runtimes are supported: llama.cpp's `llama-server` (`--backend llamacpp`), which runs any GGUF
file, including one pulled straight from Hugging Face, and [Ollama](https://ollama.com) (`--backend ollama`, the
default, which doc 44 measured). llama-server is the runtime doc 13 plans as the editor's managed sidecar; doc 46
compares the two runtimes and a UD quant with a plain quant on it.

Research tool, not product code. Python 3.8+ standard library only (`urllib`, `json`, `argparse`, `random`, `csv`, …).
Licence: GPL-3.0-or-later, like the rest of the repository. Every suite item is our own text; engine facts are restated
from `skills/standing-orders` and the research docs cited per item, and no game content is copied.

## What it measures

The harness never asks a weak model to plan or write glue. It asks for one small, typed decision at a time (doc 21
§3.1, doc 25, doc 38) and validates everything. The suites mirror those shapes:

| Suite | Items | Shape | What the model returns | Scored by |
| --- | --- | --- | --- | --- |
| `pick` | 30 | **Pick** from a code-computed menu of 4–7 valid options plus the escape `X` (doc 21 §3.2 allows up to 7) | `{"choice": "<letter>"}` (grammar-constrained enum) | `score.py`: exact |
| `pick-hard` | 30 | **Pick**, harder: always 7 options plus `X`, near-miss distractors, longer requests, 3 planted escapes | as `pick` | `score.py`: exact |
| `fill` | 12 | **Fill** a small typed record: 8 IntentFill extractions (doc 21 §4.1) and 4 mission-concept cards | the item's JSON schema | `score.py`: schema, fields, quote check, validators |
| `explain` | 10 | Grounded explanation of a lint finding from a reference card | `{"explanation", "fix"}`, ≤ 2 sentences | LLM graders (rubric in the item); `score.py` flags only |
| `text` | 10 | Short templated flavour text (radio lines, titles, briefing and debrief lines) | `{"text"}` | `score.py`: code constraints; quality by LLM graders |
| `knowledge` | 12 | Doc 30's source-verified knowledge tasks, free text | plain text | LLM graders (ground truth + grading in the item) |

Pick categories: waypoint type (5), trigger activation, timer and type (5), no-code module from doc 31's catalogue
(5), cutscene archetype CA01–CA12 from doc 39 (4), mood preset AM01–AM12 from doc 41 (3), workflow routing (5, one
of which is an off-scope request whose only correct answer is the escape), and campaign-arc tags from doc 26 (3).

**`pick-hard`** is the harder Pick instrument that doc 44 §5.4 item 4 asks for, built to separate models and quants
that `pick` cannot tell apart. The item schema is the same, and the suite file declares `"shape": "pick"`, so
`run.py` sends it through the Pick prompt, schema and settings and `score.py` scores it as Pick, while its records and
output files carry the name `pick-hard`. Item ids (`HW01`…`HV02`) differ from `pick`'s, so seeds and permutations are
new. Every menu has exactly 7 real options plus `X`, so the random-valid control is 1/7 (0.143). Each distractor is a
near miss that differs from the answer in one decisive detail stated in the request, the option text or the card: JOIN
against JOIN AND LEAD, "Whole group" against "Any group member" with Not present, a CYCLE placed at four different
spots, Decision against Choice nodes. Requests are 2–4 sentences with one irrelevant detail, and a scripted check
finds no three-word run shared between a request and its answer's label or description (runs a distractor also
carries are allowed). Three items are planted escapes, whose only correct answer is `X`: a vehicle respawn (a wave-2
module), snow (which stock CWA cannot show) and an off-scope download. One routing request quotes a marker text that
tries to redirect the model; that text is data. Categories: waypoint type (5, Standing Orders), trigger activation,
timer, type and radio (5, Standing Orders), no-code module (4, doc 31), cutscene archetype (4, doc 39), mood preset (3,
doc 41), workflow routing (4, the workflow ids named in docs 21, 38 and 39), campaign structure (3: node type, doc 19;
structure pattern, doc 26; strategic-layer module, doc 29) and replayability (2: roll scope and one-of-N lowering, doc
43). Cards restate the rules of the cited entries, not the item's answer.

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
text (the harness samples K candidates and votes or validates); 0.2 for knowledge and explain. Context 8192 tokens.
Thinking is switched off: `think: false` on Ollama, `chat_template_kwargs: {"enable_thinking": false}` on
llama-server (either is retried without the field if a server rejects it). Other sampler settings (top_k, top_p,
min_p, penalties) come from the server or the build unless pinned with `--top-k`, `--top-p`, `--min-p`,
`--presence-penalty` and `--repeat-penalty`. Every call is independent: no chat history.

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

The commands below use Ollama, the default backend; the llama.cpp route follows.

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
#    The harder Pick instrument (90 calls per condition at k = 3):
python tools/local-qual/run.py --model qwen3.5:4b-q4_K_M --suite pick-hard --condition none --k 3
python tools/local-qual/run.py --model qwen3.5:4b-q4_K_M --suite pick-hard --condition cards --k 3

# 3. Score everything under results/ (writes results/summary.csv and results/summary.json)
python tools/local-qual/score.py --grading-out tools/local-qual/results/grading.jsonl
```

Useful flags: `--limit N`, `--offset N` (skip the first N items, so `--offset 6 --limit 6` runs a chunk) and
`--items PW01,F03` select items; `--resume` skips calls already recorded without error
in the output file, so a long run can be split into chunks (for example under a 10-minute command limit) and resumed;
`--warmup` sends the first call once, unrecorded, before the run (use it on the first job after a model load);
`--dry-run` prints the first request and exits; `--base-url` names the server (`--host` still works for Ollama and
defaults to `OLLAMA_HOST`; a server bind address such as `0.0.0.0:11434` is mapped to loopback); `--num-predict`,
`--temperature`, the sampler pins above and `--think-mode omit` override defaults. `results/` is git-ignored.

### llama.cpp (`llama-server`) with a GGUF from Hugging Face

This is the most flexible route: any GGUF on Hugging Face, any quant (including Unsloth's "UD" dynamic quants), with
no model registry in between, and the same runtime the editor's sidecar would use (doc 13 §3).

**1. Get llama.cpp.** Download a release zip from <https://github.com/ggml-org/llama.cpp/releases> and check it
against the SHA-256 digest GitHub lists for the asset. The Vulkan build (`llama-<build>-bin-win-vulkan-x64.zip` on
Windows) runs on NVIDIA, AMD and Intel GPUs without CUDA libraries; macOS uses the Metal build. Binaries are published
on the numbered build tags (`bNNNNN`, marked pre-release); a versioned release such as `v0.5.0` carries only a
`nightly-tag.txt` that names its build (`b11146` for v0.5.0). `llama-server --list-devices` shows the GPU it will use.

**2. Get the model**, one of two ways:

- **Let llama-server download it.** `llama-server -hf <user>/<repo>:<quant>` fetches the GGUF from Hugging Face into
  `LLAMA_CACHE` (Hugging Face cache layout: `models--<user>--<repo>/snapshots/<commit>/<file>`) and loads it; later
  starts with `--offline` reuse the cache. Add `--no-mmproj` to skip a vision projector the suites do not need, and
  set `HF_TOKEN` for gated repositories (not tested here). This follows the repository's current `main`, so it is not
  pinned.
- **Pinned download.** Read the commit and the file's SHA-256 from the Hugging Face API
  (`https://huggingface.co/api/models/<user>/<repo>` gives `sha`; `.../tree/<sha>` gives each file's `lfs.oid`, which
  is its SHA-256, and `lfs.size`). Download `https://huggingface.co/<user>/<repo>/resolve/<sha>/<file>` (resumable,
  for example `curl -L -C - -o <file> <url>`), check the SHA-256, and start the server with `-m <file>`. Record repo,
  commit, file, size and SHA-256 next to the results: that is the artifact identity doc 14 §5 asks for.

**3. Start the server** (one model per server; stop it before loading another on a small GPU):

```text
llama-server -m <file>.gguf --jinja -ngl 99 -c 8192 --host 127.0.0.1 --port 8080
#   or: llama-server -hf unsloth/Qwen3.5-4B-GGUF:UD-Q4_K_XL --no-mmproj --jinja -ngl 99 -c 8192 --port 8080
```

`--jinja` renders the chat template stored in the GGUF, `-ngl 99` puts every layer on the GPU and `-c 8192` matches
the Ollama runs' context. The context is fixed here, not per request.

**4. Run the suites** exactly as above, with `--backend llamacpp`:

```text
python tools/local-qual/run.py --backend llamacpp --base-url http://127.0.0.1:8080 --suite pick --condition none --k 3 --warmup
python tools/local-qual/run.py --backend llamacpp --base-url http://127.0.0.1:8080 --suite fill --k 3
python tools/local-qual/score.py
```

- **Label.** `--model` is optional here; the label defaults to the served file name without `.gguf` (for example
  `Qwen3.5-4B-UD-Q4_K_XL`), which also names the output files. In llama-server's router mode (`--models-dir`) pass
  `--model <name>`, since the request's `model` field then picks the model.
- **One output directory per runtime.** On a case-insensitive file system (Windows, and macOS by default) an Ollama
  tag and a GGUF label can name the same default file: the tag `qwen3.5:4b-q4_K_M` writes `qwen3.5-4b-q4_K_M__…` and
  the label `Qwen3.5-4B-Q4_K_M` writes `Qwen3.5-4B-Q4_K_M__…`, which such a file system treats as one name, so both
  runtimes append to one file. `--resume` and `score.py` key on each record's model label and keep them apart, but the
  file then holds two runtimes' records. Pass `--out` with a directory per runtime (for example
  `--out tools/local-qual/results/llamacpp/<label>__<suite>__<condition>.jsonl`) and score them together with
  `python tools/local-qual/score.py "tools/local-qual/results/*/*.jsonl"`.
- **Structured output.** The item's schema goes in `response_format` as `{"type": "json_schema", "json_schema":
  {"name", "schema", "strict": true}}`; llama-server compiles it into a grammar that constrains decoding, as Ollama's
  `format` does. Knowledge answers are plain text.
- **Thinking.** Before the run, `run.py` renders a test prompt through `POST /apply-template` with `enable_thinking`
  false and true and records whether the template reacts (`thinking_kwarg_changes_prompt`). Each record also counts
  any thinking text that came back (`thinking_chars`). The Qwen3.5 and Gemma 4 templates both default to thinking
  **on**, so the field must be sent.
- **What the records add.** `backend`, `runtime_version` (the llama-server build, from `GET /props`), `model_file`
  (file name only, never a local path), `quant` (from the file name, or `--quant`: the GGUF's own file-type field
  reads "Q4_K - Medium" for both a Q4_K_M and a UD-Q4_K_XL file), the effective `num_ctx`, `server_sampler_defaults`,
  `sampler_sent`, `usage`, `timings` (including `cache_n`, the prompt tokens reused from the server's prefix cache) and
  `system_fingerprint`. Durations are converted to Ollama's field names and nanoseconds, so `score.py` is unchanged.
  One asymmetry: `prompt_eval_count` is the whole prompt (as on Ollama), but `prompt_eval_duration` covers only the
  part not served from the prefix cache, so compute a llama-server prompt rate as `timings.prompt_n / prompt_ms`, not
  as `prompt_eval_count / prompt_eval_duration` (that overstates it by roughly a quarter on Pick).
- **Sampler.** The per-suite temperature is always sent. For the rest, llama-server's defaults (top_k 40, top_p 0.95,
  min_p 0.05) apply unless the GGUF carries `general.sampling.*` metadata or you pin them: the three Unsloth Gemma 4
  E4B files tested set top_k 64, top_p 0.95 and temperature 1.0 (the temperature is overridden per suite), the
  Qwen3.5-4B files set none. The records keep the server's defaults (`server_sampler_defaults`). Two quants of one
  model on the same server build get the same sampler; to compare with an Ollama run, pin the values that Ollama build
  uses (`ollama show --parameters <model>`). Doc 46 pinned `--top-k 20 --top-p 0.95 --min-p 0` for Qwen3.5 and
  `--top-k 64 --top-p 0.95 --min-p 0` for Gemma 4, and left out the Qwen build's `presence_penalty 1.5`: on
  llama-server the penalty window covers the end of the prompt, so it penalises the last menu letters (doc 46 §2.2).
- **First call.** The first request after a server start can be slow while the GPU backend builds its compute
  pipelines. On the test GPU, the very first call with a new llama.cpp build spent 12.9 s processing a 239-token
  prompt (0.8 s warm); first calls after later server starts took 1.3–3.8 s, probably because the GPU driver had cached
  the compiled shaders. Pass `--warmup` on the first job after each start so none of this reaches the latency figures.
- `--api-key` (default `LLAMA_API_KEY`) is sent as a bearer token when the server was started with `--api-key`, and
  `--wait` (default 180 s) waits for `/health` while the server is still loading.

**Comparing a UD quant with the plain quant** is one server start per file with the same flags, the same suite
commands, and one `score.py` over both: the seeds depend only on (item, sample), so the runs pair item by item.

### Ollama, including Hugging Face GGUFs

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
  `pick-hard` narrows the gap with near misses and 7 options per menu, but its menus are still hand-written, not
  computed by code, and its items were written by the same team as its rubric.
- **Runtimes differ.** Grammar-constrained decoding, chat-template rendering, default sampler settings and GPU
  numerics differ between Ollama, llama-server builds and GPU backends (CUDA, Vulkan, Metal, CPU), so a result belongs
  to the exact runtime, build and model file in its records. Seeds make runs repeatable on one machine and version,
  not across GPUs or builds. llama-server's prefix cache reuses the shared start of prompts between calls; that saves
  time but may shift numerics slightly. On the GTX 1070 used so far, the Vulkan build processed prompts at about 385
  tokens/s in `llama-bench` (pp256) but 215–337 tokens/s on the Pick suites' uncached prompt parts, so a warm pick took
  1.0–1.4 s there (0.6–0.7 s on Ollama), most of it prompt processing (doc 46 §2.6).
- **`think: false`.** Hybrid reasoning models are measured in their direct mode only; a thinking run is a separate
  experiment (use `--think-mode omit` and a larger `--num-predict`).
- **Spike-local vocabulary.** The IntentFill `task`, `size` and `time_of_day` values, the concept-card `archetype`
  list (a simplified subset of doc 26 §9.3), the routing ids `explain-finding`, `cutscene-director` and
  `atmosphere-director` (doc 38 defines only `campaign-from-brief`, `populate-town` and `write-briefing`), and the
  explain labels `trigger-cannot-fire`, `detected-by-missing-side`, `global-read-before-init` and `sqs-exitwith` are
  local to this spike; the docs name the concepts but have not fixed these ids yet. `pick-hard` routes only to
  workflow ids the docs name (`campaign-from-brief`, `campaign-refine`, `populate-town`, `write-briefing`: doc 38;
  `give-patrol`, `validate-and-fix`: docs 21 and 38; `make-cutscene`: doc 39), but the one-line descriptions are ours.
- **Code checks are heuristic.** The names check exempts ordinary sentence-initial words (it still checks all-caps
  tokens and a sentence-initial name used as an address before a comma), so an invented name that opens a sentence can
  slip through. The two-sentence counter splits on `.`, `!` or `?` followed by a capital letter. The era list is short.
- **LLM grading comes later.** Knowledge, explain and text quality need graders; `score.py` leaves them `ungraded`.
- **Not a workflow test.** Each call is one isolated decision; chaining, repair loops, voting across K candidates and
  the effect on a whole campaign run are out of scope here.

## Files

| Path | Role |
| --- | --- |
| `run.py` | Runner: builds prompts, schemas and seeds per suite, sends each call through the chosen backend, writes JSONL records |
| `backends.py` | The two HTTP clients: Ollama `/api/chat` and llama-server `/v1/chat/completions` (both `stream: false`), plus the per-run server probe (version, model file, quant, context, template thinking check) |
| `score.py` | Scorer: summary CSV and JSON, console table, optional grading sheet |
| `suites/knowledge.json` | Doc 30's 12 knowledge tasks: prompt, ground truth, grading, card, evidence |
| `suites/pick.json` | 30 Pick menus: request, options (key, label, one-line description), escape, answer key, card, rationale, sources |
| `suites/pick-hard.json` | 30 harder Pick menus, same schema, 7 options each, 3 planted escapes; declares `"shape": "pick"` |
| `suites/fill.json` | 12 Fill items: request, instructions, schema, expected values, validators; banned era words |
| `suites/explain.json` | 10 findings: code, message, mission facts, card, schema, rubric (required facts, forbidden claims and patterns) |
| `suites/text.json` | 10 flavour-text slots: context, constraints (word cap, allowed names, digits, era, tone), schema; name allowlist |

Each JSONL record holds the item id, model, suite, condition, variant, sample, seed, the raw content, `parse_ok`,
`parsed`, latency, `prompt_eval_count`, `eval_count`, `eval_duration` and the other timings (in Ollama's field names
and units for both backends), and `backend`, `runtime_version`, `model_file`, `quant` and `sampler_sent`;
llama-server records add the fields listed in the llama.cpp section. Pick records also hold the permutation, the
correct letter and position, and the chosen letter and key.

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
- 2026-09-27, llama.cpp backend smoke test on the same machine (GTX 1070 8 GB, Windows 10). llama.cpp build b11146
  (the build named by release v0.5.0), Vulkan x64 zip checked against GitHub's SHA-256 digest; `--list-devices` showed
  the GTX 1070 as `Vulkan0`. Model: `Qwen3.5-4B-UD-Q4_K_XL.gguf` from `unsloth/Qwen3.5-4B-GGUF` at commit `e87f1764`,
  downloaded from the pinned `resolve/<commit>` URL and matching the Hugging Face LFS SHA-256. Server flags as in step 3.
  Pick `PW01` answered `D` = `hold` (correct) and fill `F01` returned all five fields right; both records show
  `think_sent` true, 0 thinking characters and `thinking_kwarg_changes_prompt` true. The first call took 15.6 s (12.9 s
  of it prompt processing on first use; first calls after later server starts took 1.3–3.8 s); warm picks took about
  1.0 s and fills 0.9–2.8 s, generating 38–41 tokens/s.
  GPU memory rose from 2,703 to 6,017 MiB at `-c 8192`. One explain, text and knowledge call each also parsed, and
  `score.py` scored the records unchanged. The `-hf` route was checked with a small GGUF: it downloaded into
  `LLAMA_CACHE` in the Hugging Face cache layout, the file matched the LFS SHA-256, and an `--offline` restart reused it.
  The Ollama backend was re-run on `PW01` and `F01` after the refactor, with the same results as before.
- 2026-09-27, `pick-hard` added (30 items, no model run yet). A scripted check confirmed 7 options and unique keys and
  labels per item, answers among the options or `none_fit` on exactly three items, the standard escape, 2–4 sentences
  per request, no id or request shared with `pick`, and no three-word run shared between a request and its answer's
  label or description alone; the same check finds none in `pick` either. An offline run through `run.py` and
  `score.py` with a stub backend that answers right on samples 0 and 1 and wrong on sample 2 scored 0.667 accuracy,
  pass^3 0, majority 1.0, random-valid control 0.143, and 0 stale records; the right answers fell on all seven letters
  and on `X` for the escapes. `pick` still ran and scored through the same path.
- 2026-09-27, full llama.cpp run (doc 46): five GGUF builds pulled from Hugging Face by commit and SHA-256, plus a
  Qwen arm with the Ollama build's sampler, on llama-server b11146 (Vulkan), and `pick-hard` on the two Ollama
  builds: 3,140 new records, 0 errors, 0 parse failures, 0 stale. Review: the paired tests, grade counts, pick-hard
  escapes and failures, sampler losses, latency and prompt rates were recomputed from the raw records with separate
  scripts and matched (bootstrap bounds within one resampling step); the README commands and flags were checked
  against `run.py` and `score.py`. The file-name collision note above now says what actually happens (records stay
  apart by label, the file is shared), and the sampler note gives the pins doc 46 used.
