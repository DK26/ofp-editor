# local-qual: local-model qualification spike

A small, reusable harness that measures whether a **local** model can carry the Plotroom co-pilot's code-owned step
shapes. It answers questions such as "could our harness make a 4B model effective in the editor?" with numbers instead
of impressions. Three runtimes are supported: llama.cpp's `llama-server` (`--backend llamacpp`), which runs any GGUF
file, including one pulled straight from Hugging Face; [Ollama](https://ollama.com) (`--backend ollama`, the
default, which doc 44 measured); and any OpenAI-compatible endpoint (`--backend openai`), such as OpenRouter or a
provider's own API, for comparing cloud-hosted models under a hard spending cap (see
[Cloud endpoints](#openai-compatible-endpoints-cloud-under-a-hard-budget)), including OpenRouter's free models at zero
spend (see [Safe free-model testing](#safe-free-model-testing-on-openrouter)). llama-server is the runtime doc 13
plans as the editor's managed sidecar; doc 46 compares it with Ollama, and a UD quant with a plain quant, on it.

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

**Harness-uplift variants.** To measure how much the harness itself adds, `--variant` removes one harness mechanism
at a time while every other byte of the prompt, the seeds and the menu permutations stay the same, so the arms pair
item by item. The default, `plain`, is the request described above, byte for byte as before. The variant is part of
every record and of `score.py`'s group key, and it names the output file (`__<variant>` suffix).

| Suite | Variant | What changes | Rung |
| --- | --- | --- | --- |
| pick, pick-hard | `open` (also `--condition open`) | No menu: the request, a one-line stem ("Which waypoint type should this be?") and "Answer in at most eight words"; a system prompt that says to answer with an option name or "none"; no response schema; output cap 48 | P0 |
| pick, pick-hard | `labels` | As `open`, plus "Valid names:" with the option labels in the seeded order (no letters, no descriptions) | P1 |
| pick, pick-hard | `noschema` (also `--schema-mode none`) | The lettered menu and the reply line, but no response schema; a letter outside the menu counts as invalid | P2 |
| fill | `noschema` (also `--schema-mode none`) | The field glossary and "Answer with JSON only."; no schema text, no response schema | F0 |
| fill | `schematext` (also `--schema-mode text`) | The schema text stays in the prompt; no response schema | F1 |
| text | `bare` | Slot and context only; no constraint list | T0 |

`--repair` adds at most one repair call when a code check fails (pick `plain` or `noschema`: the reply must name a
menu letter; fill: the record must parse, match the item's schema and pass every validator of the item, the same
checks `score.py` applies). The repair call shows the model its own answer and one message naming the failed check
("place: quoted text not found in the request"), never the right answer. The record's variant becomes `repair` (or
`<variant>-repair`); it holds the final answer, the first answer under `first`, `repair_used`, `first_check_failed`,
and the summed tokens, latency and cost. The open arms' stems, escape phrases and synonyms are in
`suites/pick-open-aliases.json`; `grade_open.py` maps the free-form answers to option keys (see Metrics). The open
arms never take the reference card: the Pick cards name the answer's option in 43 of the 60 items, so `open` or
`labels` with `--condition cards` would be a menu by the back door and is refused. The bare
arms of explain and knowledge need no variant: they are `--condition none`, as before. The rung names (P0–P2, F0,
F1, T0) are those of the harness-uplift design: the full harness per step is the lettered menu with cards (voting
over its samples is computed offline), Fill with the strict schema and `--repair`, explain and knowledge with cards,
and Text with its constraints (and style card); the bare harness is P0, F0, `--condition none` and T0.

**Pick details.** Options have stable keys; letters are assigned at run time over a permutation seeded by (item id,
sample), so the right answer moves between letters across samples, while `none` and `cards` see the same order
(paired comparison). The escape is always last, as `X`. `--why` adds a short bounded `why` field before the choice
(doc 21 §3.2) as a separate variant. On llama-server, `--pick-mode logprob` reads the probability of every letter
instead of sampling one (see [Logprob Pick and cascades](#logprob-pick-and-cascades---pick-mode-logprob-cascadepy)).

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
- **added with the cloud backend and the variants:** `valid_choice_rate` (Pick calls that named a real option or the
  escape), `repair_rate` (decisions that needed the repair call), `cost_usd_total` and `cost_usd_per_call` (every
  record's `cost_usd`, failed calls included, because they may have been billed) and `reasoning_tokens_mean`. These
  columns come after the earlier ones in `summary.csv` and stay empty for older runs.

`score.py --grading-out sheet.jsonl` writes one row per knowledge, explain and text answer with the reference material
(ground truth and grading, or rubric and card, or constraints) for the LLM graders. `score.py` scores only run records
(rows with `run_id` and `seed`), so a grading sheet left in `results/` is skipped when you score again; the cloud
backend's budget rows (`budget_event`) are skipped too.

**Grading the open Pick arms.** The `open` and `labels` answers are names, so they are mapped to option keys in a
separate, auditable step before scoring:

```text
python tools/local-qual/grade_open.py --judge-sheet tools/local-qual/results/grades/judge-sheet.jsonl
#   writes results/grades/open-grades.jsonl (outside the results/*.jsonl glob)
python tools/local-qual/score.py --open-grades tools/local-qual/results/grades/open-grades.jsonl [judge rows ...]
```

`grade_open.py` builds aliases for each option from its label and key (the whole label; the key with `-` and `_` as
spaces; a leading code alone and the rest, as in "AM07" and "dark night raid"; the parts of a label split at " / ";
CamelCase split into words; timer labels without "min", "mid" and "max") plus the synonyms in the sidecar, and drops
any alias two options of one item would share. After normalising (casefold, `&` as "and", punctuation to spaces), an
answer equal to one option's alias maps to it (`exact`); an answer equal to an escape phrase maps to the escape; else
whole-word alias matches inside the answer, keeping the longest of overlapping matches ("TR UNLOAD" wins over the
"unload" inside it), map to a key when exactly one option matches and the answer does not start with an escape phrase
(`substring`), or to the escape when no option matches and it does; anything else is `unmapped` and counts as wrong.
Each grade row names the record (`grade_of`), carries the answer's SHA-256 prefix (a grade for a different answer is
ignored), the mapped key, the mode and the grader (`alias-v1`). The judge sheet holds only the unmapped answers, with
the option labels and descriptions and the escape, never the request, so a judge cannot solve the task; its verdicts
come back as grade rows with `map_mode: "judge"` and `grader: "judge:<model id>"`, and `score.py` reports them as
`judge_mapped_accuracy` next to the alias-only `accuracy`. An open group with any ungraded answer gets no accuracy at
all. Report open-versus-menu uplift separately for the engine-vocabulary categories (waypoint, trigger), which a
model may know from training, and the code-owned ones (module, cutscene, mood, routing, arc, campaign,
replayability), which no bare model can know.

**Comparing arms (`uplift.py`).** `score.py` summarises each arm alone; `uplift.py` compares them. Per arm it reports
per-call accuracy with a Wilson 95% interval, the unbiased pass^1 and pass^k (the mean over items of C(c, k) / C(n,
k), as in tau-bench, arXiv 2406.12045), and, per decision policy (`single`: sample 0; Pick `vote3`: the majority of
three samples, ties wrong; Pick `adaptive`: stop when samples 0 and 1 agree, else take sample 2; `first_admitted_2`:
sample 0 if the validators admit it, else sample 1), the decision accuracy, calls per decision, **CPCD** (billed USD of
every call the policy used, failed and repaired ones included, per correct decision), **CPAD** (per admitted
decision) and the **false-admit rate** (admitted but wrong, over admitted). Correct means: Pick, the answer key; Fill,
schema-valid, every validator passing and every field right; Text, every code check passing; Explain and Knowledge,
a graded pass from `--graded` rows (`{model, suite, item_id, condition, variant, sample, verdict}`), else ungraded.
An open arm with any answer that has no current grade gets no accuracy here either (as in `score.py`), so it enters
no pair or gap closure; scoring only the graded subset would bias them.
It pairs arms automatically (each variant against `plain`, `--repair` against its base, `cards` against `none`;
more with `--pair BARE FULL`, arms written `model|suite|condition|variant`) and reports the paired difference with an
item-cluster bootstrap interval (10,000 resamples, fixed seed), the exact McNemar p-value, the error reduction and
the prompt-token overhead, for all items and, for Pick, the engine-vocabulary and code-owned items apart. `--gap
CHEAP_BARE CHEAP_FULL FRONTIER_BARE` computes the gap closure H = (cheap_full - cheap_bare) / (frontier_bare -
cheap_bare) and a non-inferiority test of cheap_full against frontier_bare (the one-sided 95% lower bound of the
difference must exceed `--delta`, default 0.10), on engine-vocabulary Pick items unless `--gap-all-items`. The Pareto
table marks, per suite and never across suites, the (arm, policy) points not beaten on both CPCD and decision
accuracy. Output: `results/uplift.json`, `uplift_arms.csv` and `uplift_pairs.csv`.

```text
python tools/local-qual/uplift.py --open-grades tools/local-qual/results/grades/open-grades.jsonl ^
  --gap "<cheap>|pick-hard|none|open" "<cheap>|pick-hard|cards|plain" "<frontier>|pick-hard|none|open"
```

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
`--temperature`, the sampler pins above and `--think-mode omit` override defaults; `--variant`, `--schema-mode` and
`--repair` select the harness-uplift rungs above, and `--label` names the model in records and file names.
`results/` is git-ignored.

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

### Logprob Pick and cascades (`--pick-mode logprob`, `cascade.py`)

**Logprob Pick.** With `--backend llamacpp`, `--pick-mode logprob` answers a Pick from one forward pass: the model's
probability for every menu letter instead of one sampled letter. `run.py` renders the chat prompt with the model's own
template (`POST /apply-template`, sending the generate mode's own `messages`, `response_format`,
`enable_thinking: false` and `model`, so the server renders exactly the prompt a generate-mode call gets), appends
`{"choice": "` so that the letter is the next token, and sends it to `POST /completion` with `n_predict: 1`,
`n_probs: 32` and `temperature: 0`. llama-server returns the top 32 tokens of the next-token distribution before any
sampler (a softmax over all the logits it holds), in `completion_probabilities[0].top_logprobs`; older builds and the
OpenAI-style shapes are read too. One letter can arrive as several tokens ("A", " A", `A"`, a SentencePiece "▁A", the
same text under a second, byte-fallback id), whose probabilities add up; tokens that would continue into a longer
string ("AB", "A1", or "A" plus the first bytes of a multi-byte character, read from the token's `bytes` because the
server cuts its text there), a tab next to the letter (invalid inside a JSON string) and letters the menu does not have
are ignored. The probabilities are then renormalised over the menu's letters and `X`. A server that lists fewer than
`n_probs` tokens has computed them over a truncated candidate set (backend sampling, `-bs`, which at temperature 0 can
leave only the greedy token at probability 1): the preflight stops such a server (exit 3) and a decision that meets
one is an error.

```text
python tools/local-qual/run.py --backend llamacpp --suite pick-hard --condition cards --k 3 --pick-mode logprob
python tools/local-qual/run.py --backend llamacpp --suite pick-hard --condition cards --k 3 --pick-mode logprob --permute 7
```

- **Records.** The variant is `logprob` (`logprob-perm<N>` with `--permute N`), so these records group apart. The
  argmax fills `chosen_letter`, `chosen_key` and `correct` exactly as a sampled answer would, so `score.py` and
  `uplift.py` score the records unchanged. Added: `p_by_key` (probability per option key), `confidence` (the top
  one), `p_margin` (top minus second), `p_entropy`, `valid_mass_min` (how much of the model's probability the menu
  letters held) and, under `logprob.orders`, per option order: the listed tokens, the token variants behind each
  letter, the letters missing from the top N, `floor` (the smallest listed probability, an upper bound for a
  missing letter, which counts 0) and `missing_mass_max` (the most all missing letters together can hold), plus
  `logprob.completion_calls` (every `/completion` sent, a failed one included) and, from the run, `logprob_boundary`
  (below). `raw` is the one token the server generated. A reply with no menu letter among the listed tokens is a
  wrong answer (`parse_mode: no_valid_letter`), not an error.
- **Position bias.** `--permute N` repeats the read for N cyclic rotations of the sample's option order (`X` stays
  last) and averages per option key. With N equal to the number of options (7 on `pick-hard`) every option sits at
  every letter once, which cancels exactly a bias that adds the same probability to a letter whatever sits there,
  and dampens other position effects; rotations keep each option's neighbours, and `X` never moves, so neither a
  neighbour effect nor the escape's own position is varied. It costs N forward passes per decision; the
  rotations share the system prompt and the request, which the prefix cache serves. Samples still differ in their
  base order, so `--k 3` without `--permute` reads three orders too, one per sample.
- **Calibration.** `cascade.py calibrate` fits a temperature T on logprob records (it minimises the negative
  log-likelihood of the right option under p^(1/T)) and writes a small JSON file. `--calibration FILE` then records
  `p_by_key_cal` and uses it for `confidence` (`confidence_raw` keeps the raw value). The chosen option never changes.
  Fit it on one set of records and apply it to another. A file fitted on another model label is refused.
- **Refusals** (exit 2, nothing sent): another backend, a non-Pick suite, `--variant`, `--why`, `--repair`,
  `--schema-mode none|text`, `--temperature`, `--num-predict`, the sampler pins (only one greedy token is generated),
  `--permute` outside 1–7, `--n-probs` outside 20–200, and a malformed calibration file. Before the first item one
  tiny `/completion` checks that the build returns a full list of token probabilities (exit 3 if it does not).
- **Token boundary check.** The letter is read where the prefix ends, which is the model's own token boundary only
  if its tokenizer splits there. Once per run, `POST /tokenize` (no forward pass) tokenises the rendered prompt, the
  prompt plus the prefix, and the prompt plus the prefix plus each letter and `"}`. A letter whose tokens do not
  extend the prefix's (a vocabulary with one token for space, quote and `A`) is listed in
  `logprob_boundary.noncanonical` and warned about on the console; `junction_ok` says the prefix does not merge into
  the template's last token. A build without `/tokenize` is noted (`checked: false`). Read offline from the local
  GGUF vocabularies, Qwen3, Qwen3.5 and Gemma 4 all split there (space and quote as one token, then the letter);
  regex pre-tokenizers of the GPT-2 and Llama 3 family always separate punctuation from letters, while Gemma 4
  pre-tokenizes whole lines, so the check matters most for vocabularies like it.
- **Not the same measurement as the generate mode.** The distribution is read without the grammar, at the canonical
  reply prefix, with no thinking; the generate mode samples one letter under the grammar at temperature 0.6. Compare
  the two per item, not as one accuracy figure. Lower-case and space-led letter tokens count here (run.py's parser
  would accept them) although the grammar would not allow them; `variants` shows their share per letter.
  `valid_mass_min` shows how much probability the letters kept. With `cache_prompt` (on) llama-server does not
  guarantee bit-identical logits between runs, so a near-tie can flip; `p_margin` shows how near.

**Cascade simulator (`cascade.py simulate`).** It replays records that already exist for two or more models on the
same items and samples, and answers: if a small model answered first and a larger one only when the small one was
unsure, how accurate would the decisions be, how often would it escalate, and what would a decision cost and take? No
model runs. Seeds and option orders depend only on (item, sample), so records of different models pair exactly; a
unit whose seed, option order or answer key differs between arms (another suite version) is dropped and counted.

```text
python tools/local-qual/cascade.py simulate --chain "<small>|pick-hard|cards|logprob" "<large>|pick-hard|cards|plain"
python tools/local-qual/cascade.py simulate --signal vote --chain "<small>|pick-hard|cards|plain" "<large>|pick-hard|cards|plain" ^
  --price "<large>|pick-hard|cards|plain=0.07,0.40"
python tools/local-qual/cascade.py calibrate --arm "<small>|pick|cards|logprob" --out tools/local-qual/results/cal-small.json
```

- **Chain and threshold.** Arms are `model|suite|condition|variant`, cheapest first, one suite. A stage accepts its
  answer when it is valid and its confidence is at least the threshold; otherwise the next stage answers. The last
  stage always answers. A failed call, an unparsed answer or an unusable confidence always escalates.
- **Confidence.** `--signal logprob` (per (item, sample)) uses the record's `confidence`, or the raw `p_by_key`
  rescaled by `--calibration ARM=FILE` (a file fitted on another model is refused). `--min-valid-mass V` treats a
  decision whose letters held less than V of the model's probability in some order as unsure (it always escalates):
  a top probability renormalised from a sliver says little. `--signal vote` (per item) works on ordinary sampled
  records: the stage spends
  `--votes M` calls (default: all its samples), answers with the majority and takes the majority's share as its
  confidence; a tie always escalates. The last stage is one call, scored as the mean over its samples.
- **Cost and latency.** Cost per decision covers the calls actually made: a record's `cost_usd` when present,
  else `--price ARM=IN,OUT` (USD per million prompt and output tokens) on its token counts, else `--cost ARM=USD` per
  call, else unknown (listed under `unpriced`). A logprob decision counts every `/completion` it sent
  (`completion_calls`, the failed one included). Latency adds up along the chain, from each record's `latency_ms`.
- **Output.** `results/cascade.json` and `results/cascade_curve.csv`: per threshold, the accuracy, the escalation
  rate, the answer and call shares per stage, the cost and the mean and p90 latency. Next to them: each model alone,
  random escalation at the same rate (two-stage chains), the oracle (escalating exactly the first stage's errors),
  the first stage's AUROC, ECE and Brier score, and the operating point. The operating point is the threshold with
  the fewest escalations whose accuracy is within `--target-gap` (default 0) of the last stage alone, with an
  item-cluster bootstrap interval of the difference. A threshold chosen and scored on the same 30 items flatters the
  cascade, so a two-fold cross-fit also chooses it on one half of the items (split by a hash of the id) and scores
  it on the other.

### Reasoning scaffolds (`--scaffold`, `scaffold_stats.py`)

Doc 59's question is whether reasoning that the *harness* does can stand in for reasoning the model would otherwise
have to do. `--scaffold <arm>` adds one such scaffold to a Pick or Fill call. Every scaffold is computed by code from
the item's **answer-blind view** (`scaffolds.blind`: the request, the options' keys, labels and descriptions, the
escape, the card; never the answer, the rationale or the pools' metadata), so it can re-arrange what the prompt already
says but cannot know the answer. Thinking stays off in every arm.

| Arm | Step | Calls | What code adds (doc 59 id) |
| --- | --- | --- | --- |
| `why` | Pick | 1 | A reason of 40–160 characters before the letter; both bounds in the schema, `why` first (S3) |
| `diff` | Pick | 1 | Lines after the menu saying how each option differs in wording from its nearest option (S1) |
| `rule` | Pick, `--condition cards` | 1 | The one card sentence with the most IDF-weighted word overlap with the request, in place of the card (S2) |
| `eliminate` | Pick, llamacpp | 1 + 1 | Letter probabilities from one forward pass (the logprob mode's read); keep the top `--scaffold-keep` (2–3, default 3) options plus X (never masked); one sampled Pick over them in a fresh seeded order (S5) |
| `pairwise` | Pick, llamacpp | 1 + 6 | The same read picks the top 3 (or 2); each pair is asked as a two-option menu plus X in both orders; most wins, X only by majority, ties to the first read (S6) |
| `subq` | Pick | 1–2 | Each option clause (descriptions split at ";") becomes a yes / no / unclear statement, without the option names; a "no" eliminates the option; a unique top by "yes" count is chosen by code; a tie gets one final Pick over the tied options plus X; no survivor gives X (S7-like) |
| `prefill` | Pick, llamacpp | 1 | The diff lines as a code-written skeleton at the start of the assistant turn, between a head that announces them and a tail that restates the system prompt's rule ("the single best option; X if no option fits") and nothing more, so it differs from `diff` only in the channel; continued by a raw `/completion` under a grammar of the menu letters; `--prefill-channel think` puts it in the empty think block of a Qwen3-style template instead (S4) |
| `quote-first` | Fill | 1 | A `<field>_quote` property before every quote-checked field; code checks it is a verbatim, case-sensitive substring of the request (a blank quote never is) and uses it only when the item's own `quote_in_request` validator would reject the model's field (so a right span in another case or with a trailing full stop is kept); the `_quote` keys are removed before scoring (S8) |

```text
python tools/local-qual/run.py --backend llamacpp --suite pick-hard --condition cards --k 3 --scaffold diff
python tools/local-qual/run.py --backend llamacpp --suite pick-hard --k 3 --scaffold pairwise --scaffold-keep 2
python tools/local-qual/run.py --backend llamacpp --suite-file <pool>/pick-pool.json --split tune --k 3 --scaffold subq
python tools/local-qual/run.py --backend llamacpp --suite fill --k 3 --scaffold quote-first
python tools/local-qual/scaffold_stats.py --suite-file <pool>/pick-pool.json --suite-file <pool>/fill-pool.json
```

- **Records.** The variant is `scaffold-<arm>` (`-k2` for `--scaffold-keep 2`, `-think` for the think channel), so
  arms group apart and `uplift.py` pairs each with `plain` automatically. The Pick fields (`chosen_letter`,
  `chosen_key`, `correct`, the permutation) are those of the plain request of the same (item, sample): a multi-call
  arm's chosen key is written with its letter in that menu, so `score.py` reads every arm the same way. `scaffold`
  holds the arm, the scaffold version, the text and its hash (one-call arms), the arm's details (kept options, pair
  votes, statements and answers, the skeleton) and a **ledger** with one entry per request: phase, endpoint, prompt and
  output tokens, latency, server prompt and decode time, cache hits, finish reason and the call's own output cap
  (`cap`: the subq call's is not the record's `num_predict`). The record's token counts and durations are the ledger's
  sums, `n_calls` counts forward passes (a template render has none), and `truncated_calls` counts the calls that
  stopped at their cap (`length`, or `limit` on `/completion`): the record's `done_reason` is only the last call's.
- **Option objects.** The one-call arms receive the sample's order as the full item's option objects and replace each
  by the view's copy (key, label, description) before rendering, so no other field a suite puts on an option reaches a
  scaffold.
- **Template handling of `prefill`.** The prompt is rendered by `POST /apply-template` from the plain request's own
  chat body (as the logprob mode renders it), so it ends with the template's generation prefix for a thinking-off
  answer. `content` appends the skeleton and `{"choice": "` there; `think` needs the prompt to end with the empty think
  block `<think>\n\n</think>\n\n` (Qwen3 and Qwen3.5 render it with thinking off) and replaces it with the skeleton
  inside `<think>…</think>`; any other template stops the run before the first record (exit 3). The continuation is a
  raw `POST /completion` with `grammar: root ::= ("A" | … | "X") "\"}"`, the arm's temperature, seed and sampler
  pins, and no `response_format`: on `/v1/chat/completions` a trailing assistant message would be continued too, but
  the schema grammar would then demand a fresh `{` after a prefill that already opened the object.
- **Refusals** (exit 2, nothing sent): a Pick arm on Fill or the reverse; any other variant, `--why`, `--repair`,
  `--condition open`, `--schema-mode none|text` or `--pick-mode logprob` with a scaffold; the paid `openai` backend (its
  budget reserves one call per record); `eliminate`, `pairwise` and `prefill` off llama-server; `rule` without
  `--condition cards`; `--scaffold-keep` outside 2–3 or with another arm; `--prefill-channel` with another arm;
  `prefill` with `--think-mode omit`.
- **Suites outside `suites/`.** `--suite-file` runs a suite file that names itself (`"suite"`) and its step shape
  (`"shape"`; a copy of a built-in suite may omit the shape). A suite whose items carry `"split"` (the staged pools)
  needs `--split tune` or `--split heldout --confirm-heldout`; records add `suite_file` and `split`. `score.py`,
  `uplift.py` and `scaffold_stats.py` take `--suite-file` to score them.
- **Hint-only control.** `control_suite.py --suite pick-hard --mode swap --out <file>` writes the same menus, cards
  and answers with every request swapped for one from another category (or blanked, `--mode blank`), as suite
  `<suite>-hint-<mode>`. Run it through `--suite-file` for `plain` and a scaffold arm: a scaffold that still scores well
  above chance there chooses by itself (doc 59 T-L6). `scaffold_stats.py` recognises these records by the suite name
  and applies SR3 from them (below); no suite file is needed for that, since each record carries its answer key.
- **Analysis (`scaffold_stats.py`).** A decision (model, suite, item, condition, variant, sample) with several records
  (an error, then the retry `--resume` sent; or a rerun into the same file) counts once, as its last error-free record,
  like `uplift.py`, with every attempt's tokens and model calls in its cost. Unit = (suite, item, condition); unit
  score = mean correctness over its k samples (Fill: every field right, schema-valid, validators passing, as
  `uplift.py` counts it). Each `scaffold-*` arm (`--arm-prefix`; other variants in the input are listed, never
  compared) is compared with `plain` of the same model on the units both have with equal k by an exact paired
  sign-flip test (differences are multiples of 1/k, so the null distribution is computed exactly), one-sided both
  ways, Holm across the arms of one (model, step kind). Every side figure (false escapes, wrong-but-valid, latency,
  tokens, model calls, truncated and thinking decisions) is computed over those paired units, for both sides, so the
  cards-only `rule` arm meets plain's cards units, not its none-plus-cards pool. Records of a hint-only control suite
  (`<suite>-hint-<mode>`) are never units: they give SR3, which fails when an arm's hint-only accuracy exceeds chance
  (1 / menu size) + 0.10 or plain's hint-only accuracy on the same control units + 0.10 (`not_run` without control
  records). Verdicts: `winner` (Holm p < 0.05, mean gain ≥ 0.05, no fewer planted escapes right, no more false
  escapes, no category losing more than 2 units, SR3 not failed), `harmful` (Holm p < 0.05 for worse) or
  `no_effect`. Output `results/scaffold_stats.json`.

### Harness presets (`--preset`, `presets/`)

D048 fits the harness to each model with a **harness preset**: a data-only file that says how Wilco asks one model setup
for each step kind (doc 55 §3). `run.py --preset FILE` runs a suite with one; `presets/lint.py` checks preset files on
their own.

```text
python tools/local-qual/presets/lint.py                  # check every draft (or name files); exit 1 on any finding
python tools/local-qual/run.py --backend llamacpp --suite pick-hard --k 3 --dry-run --preset tools/local-qual/presets/drafts/qwen3.5-4b-q4_k_m.preset.json
python tools/local-qual/run.py --backend llamacpp --suite pick-hard --k 3 --preset tools/local-qual/presets/drafts/qwen3.5-4b-q4_k_m.preset.json
```

- **Files.** `presets/schema/harness-preset.schema.json` is the format (JSON Schema 2020-12, draft 2 of doc 55 §3.3).
  `presets/drafts/` holds the 0.1.0 drafts for the default, Qwen3.5-4B, Gemma 4 E4B QAT and Granite 4.1 3B. They are
  **untested hypotheses**: status `draft`, and their first note says so; no run has used them. Doc 55 §3.3's 0.2.0
  revision (knob ledgers, template hashes read from the GGUF headers) and the checks that go with it (the ledger and the
  tuning plan, the pins, the template-fact rules for a documents channel or an `enable_thinking` switch, and verbatim
  spans only with the compact grammar, which the 0.1.0 Qwen draft predates) land with the first tuning run.
- **Loading.** The file is read strictly: at most 256 KiB, UTF-8, one JSON object, no duplicate key and no NaN or
  Infinity (either would change a knob without showing it). It is checked against the schema, merged onto its base
  (`"extends": "<id>@<version>"`, looked up among the `*.json` files in the same folder; at most 8 levels; no cycles)
  and checked against the loader rules the schema cannot express: neutral Pick and Fill penalties (D022 amendment item
  5), no step-shape grant, `k_max` at most 5 and `r_max` at most 3, only the default binds to `any`, every other preset
  extends a base, a null template hash only in a draft, native tool calls and validator-only schema modes only on
  cloud endpoints, the compact grammar and verbatim spans only locally, no `bound_second_stage` route, a layout id
  after merging, and decision overrides valid as the step settings they become. A withdrawn preset is refused.
- **What it sets.** The settings of the suite's step kind (Pick for `pick`, `pick-hard` and Pick suite files; `fill`;
  `text`; `explain`) become the flags that send them, converted to the flags' types, so a preset run's requests are
  byte for byte those of the same flags typed out (p15–p17):

  | Knob | run.py flag |
  | --- | --- |
  | `sampler`: `temperature`, `top_p`, `top_k`, `min_p`, `presence_penalty`, `repeat_penalty` | `--temperature`, `--top-p`, `--top-k`, `--min-p`, `--presence-penalty`, `--repeat-penalty` |
  | `sampler.frequency_penalty` | not sent, so it must be 0 (every runtime's default) |
  | `output_cap_tokens` | `--num-predict` |
  | `schema_mode`: `json_schema_strict`, `none_validate` | `--schema-mode strict`, `none` (Pick and Fill only) |
  | `reasoning.mode` `off` | local: `--think-mode false` (switch `chat_template_kwargs.enable_thinking`, `from_profile` or none), `--think-mode omit` (`not_applicable`); openai: `--reasoning none` (`omit` for `not_applicable`) |
  | `reasoning.mode` `budget`, `on` | openai only: `--reasoning '{"max_tokens": B}'`, `--reasoning <effort>` |
  | `layout.cards.mode`: `declared`, `off` | `--condition` stays yours (both card conditions are runs of the preset); `--condition none` |
  | Pick `scoring.mode`: `generate_vote`, `letter_probs` (with `rotations`) | `--pick-mode generate`; `--pick-mode logprob` (with `--permute N`; llamacpp only) |
  | Pick `answer.why.mode` `before` | `--scaffold why`, the bounded why of 40–160 characters (local only) |
  | `binds_to.context_tokens` of a local file | `--num-ctx` |

  Every other request-shaping knob must hold the value run.py already runs (the measured harness of docs 44 and 46,
  which the default preset names): layout `static_first.v1`, run.py's own instruction variants, system text in the
  system role, prose cards, `A) label: description` menus, no exemplars, a letter in `choice` under a response schema,
  direct Pick and Explain, whole-record Fill with free-quoted spans and judgement fields in the record, text in a JSON
  object.
- **What it leaves out.** Voting, the repair ceiling, cascade thresholds and calibration shape no single request: each
  record lists them under `preset.not_applied` with the reason (score.py, uplift.py and cascade.py apply them offline).
  Decision overrides need a DecisionKind per item, which the suites do not carry: they are printed and listed under
  `preset.overrides_not_applied`, and those menus run the step setting.
- **Refusals** (exit 2, nothing sent), each naming the knob or flag and the fix: any knob value run.py cannot send (the
  compact GBNF grammar, verbatim spans, per-field Fill, extract-then-dispatch, exemplars, another layout or
  instruction variant, the documents channel, thinking on or a thinking budget locally, calibrated or option-text
  scoring, a non-zero frequency penalty), all of a preset's at once; the knowledge suite, which has no step kind; a
  flag that sets a knob the preset sets, to another value (the same value is accepted); `--variant`, `--why`,
  `--calibration` and `--condition open`; a `--scaffold` arm other than the preset's (the draft-2 format has no field
  for the other doc 59 arms: friction register FR-C-031); `--repair` when `repair.r_max` is 0; `--drop-params` naming
  a sampler value the preset sets. So of the drafts, the default, Qwen and Granite run Pick, text and explain; Gemma
  runs none as written (the compact grammar on every step); no draft runs Fill, because the 0.1.0 default asks for
  judgement fields as separate Picks (`computed_pick`; the 0.2.0 revision returns to `in_record_bands`, the measured
  form) and Qwen and Granite add verbatim spans or per-field Picks.
- **Records.** Every record carries `preset`: `id`, `version`, `status`, `file`, `sha256` (of the file's bytes),
  `extends`, `bases` (ref, file and SHA-256 of each base), `prompt_pack`, `step_kind`, `applied` (the flags),
  `adapted`, `not_applied`, `overrides_not_applied` and `binding` (whether the served model is the bound one:
  llama-server's model file or the requested cloud model; not checked on Ollama; a mismatch is also printed). The
  label gains `+<id>@<version>` unless `--label` is given, so preset runs never pool or resume with flag-only runs.
  Every `--resume`, with or without `--preset`, refuses a file whose records of that label were made with other preset
  bytes, with a preset when the run has none, or without one when it has one (one `--label` can name both kinds of
  run). `.gitattributes` keeps the preset files LF on every checkout, so their hashes do not change.

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

### OpenAI-compatible endpoints (cloud) under a hard budget

`--backend openai` sends the same suites to any OpenAI-compatible `POST <base-url>/chat/completions`: OpenRouter
(`https://openrouter.ai/api/v1`), a provider's own API, or a local vLLM or llama-server. It answers questions such as
"does this model do better on a cloud host at bf16 than as a local Q4?" and "which cheap model gains most from the
harness?". Every call costs money, so the backend is built around a cap it will not cross.

**What is sent.** Only the synthetic suites in `suites/` (our own text: no user data, no mission files, no game
content), the model id and the sampling parameters, plus whatever you put in `--extra-body`. The key travels only in
the `Authorization: Bearer` header, and redirects are never followed (Python's urllib would re-send the header to
whatever URL a 3xx names), so a redirecting endpoint stops the run (exit 5) and its final URL goes in `--base-url`.
No account id, user name or local path is sent or recorded; records keep only the endpoint's host name
(`base_host`). Plain `http` is refused unless the server is on this machine, and then no proxy is used. The key is
stripped of surrounding whitespace (a key file's trailing newline would otherwise make Python print the header, key
included, in a traceback); a key with inner spaces or control characters, shorter than 8 characters, holding a
double quote or a backslash (JSON writes those escaped, so the scrub of every record line could not find the key), or
found inside `--base-url` or `--extra-body` is refused, and so is any `--extra-body` field named like a credential
(`api_key`, `token`, `secret`, ...), because `--extra-body` is copied into every record.

**Before the first run (the account owner, never an agent):** create the account and an API key; on OpenRouter, set a
credit limit on the key itself (a second, independent cap: a key over its limit gets HTTP 402, which the runner treats
as out of budget and never retries); leave optional plugins such as Response Healing off (it repairs JSON on the
server and would blur the schema rungs; `--extra-body` refuses to enable it). The key reaches `run.py` only through
an environment variable, never typed into a command line (it would land in shell history and the process list).
On Windows, store it once with `cloud/set-openrouter-key.ps1` (DPAPI-encrypted for your Windows user, hidden input)
and start every run through `cloud/run-cloud.ps1`, which decrypts it into the environment of that one `run.py`
process only (paid rounds need its `-AllowPaid` switch; see [cloud/README.md](cloud/README.md)). Through the
launcher, name the output file with `--output` (the same option as `--out`): `powershell -File` reads `--out` as an
abbreviation of its own `-OutVariable`/`-OutBuffer` and stops before the launcher starts. Elsewhere, read it
with hidden input into the one command's environment (bash: `read -rs OPENROUTER_API_KEY; export
OPENROUTER_API_KEY`, then `unset` it after the run).

**A run.** The flags without defaults are all required: the runner refuses to start without `--max-usd`,
`--price-in`, `--price-out`, `--api-key-env` and `--reasoning`, and it never accepts a key on the command line. A
price or a cap of 0 is refused except with `--free-only` (a zero price makes every worst case 0; see
[Safe free-model testing](#safe-free-model-testing-on-openrouter)); so are a negative backoff, a timeout of 0,
`--num-predict 0` and `--est-tokens-per-byte` below 0.1.

```text
python tools/local-qual/run.py --backend openai --base-url https://openrouter.ai/api/v1 ^
  --api-key-env OPENROUTER_API_KEY --model google/gemma-4-26b-a4b-it ^
  --extra-body "{\"provider\": {\"only\": [\"<endpoint tag>\"], \"allow_fallbacks\": false, \"require_parameters\": true, \"data_collection\": \"deny\"}}" ^
  --reasoning none --price-in <USD/1M in> --price-out <USD/1M out> ^
  --price-as-of 2026-09-27 --price-source https://openrouter.ai/api/v1/models/<author>/<slug>/endpoints ^
  --max-usd 0.50 --ledger tools/local-qual/results/stage2-ledger.jsonl ^
  --suite pick-hard --condition cards --k 3
```

(`^` continues a line in Windows cmd; use `\` in bash, or put the provider block in a file and pass
`--extra-body @provider.json`.) Start every new endpoint with a one-item preflight (`--items HW01 --k 1`, then one
Fill and one knowledge item) and look at the record before running a battery.

- **Pinning an endpoint (OpenRouter).** A model is usually served by several providers at different precisions and
  prices, so pin one: `provider.only` (or `order`) with one endpoint, `allow_fallbacks: false` so it never falls back,
  `require_parameters: true` so it routes only to endpoints that support every parameter sent (structured outputs
  included), optionally `quantizations: ["bf16"]` and `max_price: {"prompt": <in>, "completion": <out>}` (USD per 1M,
  a third guard). Slugs with a variant suffix, such as `deepinfra/turbo`, address one endpoint
  ([provider routing](https://openrouter.ai/docs/features/provider-routing), read 2026-09-27); whether a
  precision-suffixed tag works in `only` should be confirmed in the preflight. The runner warns when an OpenRouter run
  is not pinned, and refuses a strict-schema run on OpenRouter without `require_parameters: true` (it could be routed
  to an endpoint that ignores `response_format`). `--extra-body` may not set the fields run.py owns, nor billing the
  cap cannot price: `models` and `route` (fallback to other models at other prices), `plugins` (response healing
  would blur the schema rungs; web search is billed per request), `web_search_options`, `prediction`, `prompt`,
  `input` and `max_output_tokens`, nor fields billed at a rate the price flags do not name: `service_tier` (a
  priority tier costs more per token) and `modalities` or `audio` (audio or image output). On an endpoint that
  reports no cost the ledger would count those calls at the flags' rate, below what was billed. A `:online` model id
  is refused for the same reason. Provider thinking switches
  (`reasoning_effort`, `thinking`, `chat_template_kwargs`, ...) are accepted only with `--reasoning omit`.
  `--expect-provider <tag or name>` stops the run if a response names another provider. It reads the
  response's top-level `provider` field, which OpenRouter's API reference does not document, so confirm it in the
  preflight; the record keeps it as `provider_served`, and `provider_unverified` is true when it is missing. The record label defaults to `<model>@<endpoint tag>`,
  so two precisions of one model score separately; `--label` overrides it.
- **Privacy flags.** OpenRouter says it does not log prompts or completions unless the account opts in
  ([FAQ](https://openrouter.ai/docs/faq), read 2026-09-27). `provider.data_collection: "deny"` routes only to
  providers that do not collect user data, and `provider.zdr: true` only to zero-data-retention endpoints (provider
  routing page, same date). The suites are synthetic, but the flags cost nothing to set.
- **Prices.** Take them from the pinned endpoint's row on the run day (`GET
  https://openrouter.ai/api/v1/models/<author>/<slug>/endpoints` needs no key), not from the model's list price, and
  record where and when (`--price-as-of`, `--price-source`). Reasoning tokens are billed as output
  ([reasoning tokens](https://openrouter.ai/docs/use-cases/reasoning-tokens), read 2026-09-27). Buying OpenRouter
  credits by card adds a 5.5% fee, minimum $0.80 (FAQ, same date), which the cap does not see.

**The budget cap** (`budget.py`). Before every attempt the runner reserves its worst case,
`(prompt estimate x price_in + output cap x price_out) / 1e6`, where the prompt estimate counts every UTF-8 byte of
every message, of the schema and of any body field that is not a known routing or sampling parameter as one token (a
byte-level tokenizer never produces more tokens than bytes; lower it with `--est-tokens-per-byte` only after a
preflight measured the tokenizer), plus 8 tokens per message, times 1.3, and the output cap is the request's
`max_tokens` (plus `reasoning.max_tokens` when sent). The attempt is sent only if `spent + reservation <= --max-usd`.
The reservation is written to the ledger before the request leaves; afterwards the attempt is charged the higher of
what the provider reported (`usage.cost`, which OpenRouter returns on every response, in credits that are US dollars,
[usage accounting](https://openrouter.ai/docs/use-cases/usage-accounting), read 2026-09-27) and what its usage costs
at your prices (`cost_source` `computed>provider` when the provider reported less), else whichever is known, else
its whole reservation. `usage.cost_details.upstream_inference_cost` is added to `usage.cost` only when `usage.is_byok`
is true (a request billed to your own provider key, where OpenRouter's fee and the provider's bill are both spent); on
any other request OpenRouter reports the same money in both fields, and counting both once booked every call twice
(doc 54 §4.2). Attempts rejected before a model ran (HTTP 400, 401, 402, 403, 404, 413, 422, 429, and a
refused redirect) cost nothing; any other failed attempt (5xx, timeout, dropped connection, a provider error inside
a 200) is charged its full reservation, because providers may bill prompt processing on failed requests
([errors](https://openrouter.ai/docs/api-reference/errors), read 2026-09-27). A reservation with no settled record
(the process died in between) keeps counting in full, so a crash can only over-count. The ledger is the output JSONL
itself unless `--ledger` names a shared file, so `--resume` (and any later run on the same file) keeps counting from
what was already spent; one `--ledger` can cap a whole stage of many runs. A run without `--ledger` prints a note
that its cap covers only its own output file. The ledger (and a separate output file) is locked for the whole run
with a `<file>.lock` file created atomically: a second process on the same ledger would read the total once and could
spend the cap again, so it refuses to start (exit 5). A lock left by a killed run blocks the next start until it is
deleted by hand. When the next attempt does not fit, the runner writes a `{"budget_event": "stop", "stop":
"BudgetLimited"}` row and exits with code 4; raise `--max-usd` and `--resume` to continue. If an attempt, answered or
failed, ever costs more than its own worst case (a wrong price flag, a per-request fee, or an endpoint ignoring
`max_tokens`), the call stops at once, before any retry, and the run stops as `CostAnomaly` (exit 4). For endpoints
that report no cost, the cap is only as good as the price flags: set a spending limit at the provider as well.
`--dry-run` with the budget flags prints the first request's worst case without sending anything. `--key-check` (OpenRouter) also reads
`GET <base>/key` before the run, refuses unless the key has a credit limit with at most `--max-usd` +
`--key-margin-usd` left ([limits](https://openrouter.ai/docs/api-reference/limits), read 2026-09-27), and reports the
key's usage change after it. `--key-status` reads the same record alone, with no run (next section).

**Reasoning.** `--reasoning` is required, so the effort is explicit and recorded on every call (`reasoning_sent`):
`none` switches reasoning off on hybrid models, another effort (`minimal`, `low`, `medium`, `high`, `xhigh`, `max`)
or a JSON object sets it, and `omit` sends no field (the provider's default applies). A JSON object's `max_tokens` (a
thinking budget, added to every worst case) must be a whole number above 0: `5000.0`, `"5000"` or `true` would reach
the provider as a budget the reservation never counted, so they are refused. Models whose reasoning is
mandatory reject `none`; use their lowest effort and give the output cap thinking headroom with `--num-predict`. A
call sent with `none` that still reports reasoning tokens, or returns non-blank thinking text (a `reasoning` field or
`<think>` tags in the content), stops the run (`ReasoningLeak`, exit 7); that record is an error, so it is neither
scored nor skipped by `--resume`. Every record keeps `reasoning_tokens` and `visible_tokens`. For every backend, a
`<think>` block in the content is removed before the answer is parsed (`think_stripped`; `raw` keeps the whole
reply), so a draft answer inside the block is never scored. For a provider's own API that names the field differently, use `omit`
and put its own field in `--extra-body` (for example `{"reasoning_effort": "none"}`).

**Schemas.** Schema steps send `response_format: {"type": "json_schema", "json_schema": {"name", "strict": true,
"schema"}}`. If the endpoint rejects it (a 4xx that names the schema), the run stops (`SchemaRejected`, exit 6) and is
never retried without the schema; pin an endpoint that lists structured outputs. `--schema-normalise` sends a strict-
mode copy (`additionalProperties: false` and every property required on every object) and `--schema-strip
maxLength,pattern` drops keywords an endpoint rejects (only validation limits and annotations may be stripped; `enum`,
`type`, `required` and the like would loosen the strict arm and are refused); answers are still validated against
the suite's own schema in `score.py`, so a stripped limit is still checked, in code. An endpoint can also accept the
schema and ignore it: each strict-schema record carries `schema_conformant` (the first answer was bare JSON whose
structure, types and enums match the schema sent; length limits are left to `score.py`), and the canary counts
non-conformant answers, so fenced or off-enum JSON from an unenforced schema stops the run even though it parses.

**Retries and stops.** 408, 429 and 5xx get up to `--max-attempts` (default 5) attempts with exponential backoff and
full jitter (`--retry-base-s` 2, capped at `--retry-cap-s` 60), honouring `Retry-After`. A provider error inside an
HTTP 200 is an error, never content; inside a 200, code 402 stops the run as out of budget and 401 or 403 as a
configuration fault, as the status codes would. Other 4xx stop the run as a configuration fault (exit 5), 402 as out
of budget (exit 4), a provider mismatch with exit 8. A 200 whose body is not a JSON completion (an event stream
despite `stream: false`, a portal page, a body over 8 MiB) is charged its reservation and stops the run (exit 5)
instead of being retried. The canary judges the first `--canary` calls (default 20): more than 20% non-conformant
answers in a strict-schema arm (above) or more than 10% errors stop the run (`CanaryAbort`, exit 7). `--warmup` is not
available (every call is paid and recorded; drop each schema's first call from latency figures instead). Parameters
a model rejects can be left out per endpoint with `--drop-params temperature,seed` (recorded as `params_dropped`);
seeds are best-effort on cloud endpoints. `--repeat-penalty` goes out under llama-server's name, `repeat_penalty`,
which OpenRouter lists as `repetition_penalty`; on OpenRouter the pin is most likely ignored, and the run warns at
the start: pass `{"repetition_penalty": <value>}` in `--extra-body` instead of the flag.

**What the records add.** `backend: "openai"`, `base_host`, `model_requested`, `model_served`, `provider_served`,
`endpoint_tag`, `quant` (from a single `provider.quantizations` entry, or `--quant`), `extra_body_sent`,
`reasoning_sent`, `reasoning_tokens`, `visible_tokens`, `cached_tokens`, `cache_write_tokens`, `usage`, `cost_usd`,
`cost_source` (`provider`, `computed`, `computed>provider`, `reserved`, or a `+` of several over retries),
`schema_conformant`, `think_stripped`, `attempt_costs_usd`,
`reserved_usd`, `spent_usd` (the ledger total after the call), `budget_usd`, `ledger` (file name only), `price_row`
(prices, date and source),
`params_sent`, `params_dropped`, `seed_sent`, `schema_normalised`, `schema_stripped`, `attempts`,
`http_status_history`, `retry_after_s`, `native_finish_reason`, `generation_id` and `call_id`. Token counts map to
`prompt_eval_count` and `eval_count`, counted by the endpoint's own tokenizer, so they are not comparable with local
counts one to one; `eval_duration` is empty, so tokens per second stay blank. The ledger rows (`budget_event`
reserve, settle and stop) sit in the same file and are skipped by `score.py` and `--resume`.

**Rate caps on paid runs.** `--rpm N` (attempts in any 60 s) and `--max-requests-per-day N` (attempts per UTC day
in the ledger) work on paid runs too (`rate_gate.py`); a run that reaches the day's cap stops with exit 10 and
continues with `--resume` the next UTC day.

### Safe free-model testing on OpenRouter

`--free-only` runs OpenRouter's free model variants (ids ending in `:free`) with no way to spend, inside the free
tier's limits. The owner runbook (account, privacy settings, key with a $0 credit limit, key storage, dry run, first
run, daily routine, revoking) is [cloud/README.md](cloud/README.md). What the tool enforces (`free_mode.py`,
`rate_gate.py`):

- **Free models only.** The id must be `<author>/<slug>:free` outside `openrouter/` (`openrouter/auto:free` can bill
  paid models). At every start and resume, the live public catalogue (read without the key) must list the exact id
  with every price present exactly 0 (Decimal equality: routers are priced `-1`), text output only, and zero-priced
  endpoints. No model has a `request` price key, so a missing key counts as no fee, and every key present must be 0.
  The cap and the prices are 0; any other value is refused.
- **Strict routing.** Every request carries `provider.require_parameters: true` (an endpoint without strict structured
  outputs is skipped, never answering unconstrained), `allow_fallbacks: false` and a pin to the endpoints read at
  start. A parameter the endpoint does not list is refused before sending, with the fix named (`--drop-params seed`,
  `--schema-mode none`).
- **Zero spend, checked on every response.** `usage.cost` must be exactly 0, with no BYOK upstream cost, and the
  served model must be the requested `:free` id (or its canonical slug with `:free`). Anything else stops the run at
  once with **exit 9**, before any retry. `GET /key` is read at start, every `--key-poll-every` attempts (at most
  10) and once more however a started run ends (done, a fatal stop, the canary, a quota stop); any rise in the key's
  usage is exit 9, whatever the other reason. Each reading goes into the ledger (a `key` row: usage figures and the
  daily counter only), and a start whose key spent more than the ledger's last reading refuses with exit 9, so a
  charge no response showed (a stream, a timeout, a killed run) is never taken as the next baseline. A ledger that
  ever recorded spending refuses to start.
- **A key that cannot spend.** Refused: a management key, a key with no credit limit, a key with more than
  `--max-key-headroom-usd` (default 0) left, an expired key, or a key record without the daily free counter
  (`--allow-key-headroom` accepts headroom knowingly). Only non-secret key fields are printed or recorded; the
  `label` (a partly masked key) and the account ids never are. Anything shaped like an OpenRouter key (`sk-or-...`)
  is redacted everywhere.
- **Rate limits.** One free run at a time per user, whatever its ledger (the limits are per account; a
  `free-run.lock` in `%LOCALAPPDATA%\plotroom-dev`, elsewhere `~/.local/state/plotroom-dev`, exit 5 while another
  run holds it). At most `--rpm` (default 18; OpenRouter allows 20) attempts in any 60 s, with the window carried
  across runs from the ledger. At most `--max-requests-per-day` (default 45, for the 50-a-day tier) attempts per UTC
  day in the shared `--ledger` (required), and never more than the account's remaining free requests less
  `--daily-reserve` (default 5); a wait that crosses 00:00 UTC books the attempt to the new day after reading the
  account's new counter. Every attempt counts, 429s and errors included. A 429 naming the daily quota is
  terminal: exit 10 with the resume time, from its `X-RateLimit-Reset`. The header is not trusted: a reset that is
  not after now, is not a number, or lies more than a day past the next 00:00 UTC resumes at the next 00:00 UTC
  (the daily counter resets then), so an absurd header cannot crash the run. A per-minute 429 waits for
  `X-RateLimit-Reset` (epoch milliseconds). An upstream 429 honours `Retry-After`. A 429 whose
  `error.metadata.limit_source` is `upstream_provider_shared_pool` is always upstream, whatever its text or headers
  say (a provider's own "per day" wording once read as the account's cap; doc 52's re-check of 2026-09-28); other
  `limit_source` values are not documented, keep the text and header rules, and are shown in the recorded error.
  `--max-consecutive-429` (default 3) 429s in a row, as HTTP 429 or reported inside an HTTP 200, end the run with
  exit 10; an answer or any other status resets the count. A 404 or 503 saying no endpoint may serve the request
  (privacy settings, ZDR, a guardrail) stops with exit 5 instead of spending more requests.

Free records add `free_only`, `canonical_slug`, `endpoint_tag`, `endpoint_name`, `provider_pin`, `endpoint_params`,
`key_start`, `free_daily_start` and `rate_gate` (`attempts_today`, `requests_left_today`, `rate_wait_s`). Exit codes
beyond the paid path's: **9** the free-only guard refused or stopped the run; **10** the day's allowance or the rate
limit ended it (resume later with `--resume`). With any key (paid runs too), `run.py` removes the `--api-key-env`
variable from its own environment once it has read it, so no process it starts inherits the key.

**Checking the key at no quota (`--key-status`, `key_status.py`).** A dry run sends nothing, not even the key check,
and a real free run spends one of the day's requests, so this command sends only `GET <base>/key` and prints the
key record's non-secret fields in plain words, then exits 0:

```text
powershell -NoProfile -ExecutionPolicy Bypass -File tools\local-qual\cloud\run-cloud.ps1 --key-status
python tools/local-qual/run.py --key-status --api-key-env OPENROUTER_API_KEY [--base-url <API base>]
```

- **What it prints.** Credit limit and what is left, usage in all and today (UTC), BYOK usage, free tier and
  management key (yes or no), the expiry, today's free-model requests (used, limit, left) with the reset at 00:00 UTC,
  the per-key rate limit (`-1` reads as none), and whether a `--free-only` run would accept the key (`accepted`, with
  how many requests the account still allows today after `--daily-reserve`, or `refused:` with `key_refusal`'s own
  reason and fix). The fields are `free_key.key_summary`'s and `rate_limit_summary`'s; the `label` and account ids
  are never read into the report. Two caveats are printed with the figures, from doc 52's re-check of 2026-09-28:
  the daily counter can lag (it read 0 before and after an answered free call), and the per-key `rate_limit` (-1 per
  10 s that day; the record marks it deprecated) is not what a free run meets, since the free-model limits count
  per account.
- **What it does not do.** No chat or completion request, no catalogue read, no ledger, record or other file, no
  lock (it runs while a free run holds the free-run lock). It skips every other flag and names them in one note, so
  `--key-status` can be added to any run line. `cloud/run-cloud.ps1` accepts it without `--free-only` (it cannot
  spend) and still refuses `sk-or-` and `--api-key` in the arguments.
- **Base URL and key.** `--base-url` defaults to `https://openrouter.ai/api/v1` only for an `sk-or-` key; another
  provider's key needs `--base-url`, so it is never sent to OpenRouter by default. The base-URL and key checks are the
  paid path's (`cloud_guard.py`): https, or plain http to this machine only; `--api-key` and `--dry-run` are refused.
- **Failures** are one line on stderr that names the next step: exit 5 for 401 or 403 (store a new key with
  `set-openrouter-key.ps1 -Force`), 404, a refused redirect or a body that is not a key record (check `--base-url`);
  exit 10 for 429 (wait); exit 3 for 5xx or no connection (try again later). A body is shown only after every
  `label` value, the key and anything shaped like an OpenRouter key are redacted, as one line of printable ASCII; a
  JSON body is decoded first, so a copy written with `\u` escapes is found too, and a redirect's target host is
  scrubbed the same way.

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
- **Not a workflow test.** Each call is one isolated decision (plus at most one repair call with `--repair`);
  chaining, longer repair loops and the effect on a whole campaign run are out of scope here, and voting across K
  candidates is computed offline from the samples.
- **Cloud endpoints are black boxes.** A cloud record belongs to the endpoint, the provider's serving stack and the
  day; server fp4 or fp8 is not a GGUF Q4_K_M, grammar engines differ, and seeds are best-effort, so a local-versus-
  cloud difference mixes runtime, precision and decoding effects. Prompts here are 87–535 tokens, below every prompt
  cache minimum, so the cost measured is uncached and per decision of a minimal harness, not the product's (doc 40).
- **Cascades are replays.** `cascade.py` combines records measured separately, possibly on different runtimes or
  days, and adds their latencies as if the calls ran one after another on one machine (a vote stage's calls could
  run in parallel on a server with several slots). Vote confidences take only a few values (thirds with three
  votes), so the curve is a step function. With 30 items a threshold is noisy; read the cross-fit next to the
  in-sample operating point.
- **Open-arm mapping is a heuristic.** Aliases and the longest-match rule cover common phrasings; everything else is
  `unmapped` and counts as wrong unless a judge maps it, so `accuracy` on the open arms is a lower bound and
  `judge_mapped_accuracy` depends on the judge.

## Files

| Path | Role |
| --- | --- |
| `run.py` | Runner: one loop over (sample, item) for every backend (with the optional repair call, a logprob decision or a multi-call scaffold decision), the server probe, JSONL records |
| `run_cli.py` | run.py's command line (`--out` and its alias `--output` included) and the refusals checked before anything is sent: variant and scaffold selection, `--suite-file`, `--split` |
| `run_records.py` | What a call becomes in the record: reply parsing, the repair call folded into its decision, the keys `--resume` skips, file-name slugs |
| `run_preset.py` | `--preset`: the knob plan (each supported knob to the run.py flag that sends it; fixed values; policies left to offline analysis; refusals), conflicts with command-line flags, the record's `preset` object and binding check, the `--resume` hash check |
| `presets/lint.py` | The harness-preset checker: the JSON Schema subset validator, strict file reading, base resolution and merging with file hashes, the loader rules the schema cannot express, and its command line |
| `presets/schema/harness-preset.schema.json` | The harness-preset format (JSON Schema 2020-12, draft 2 of doc 55 §3.3) |
| `presets/drafts/*.preset.json` | Draft presets 0.1.0 (default, Qwen3.5-4B, Gemma 4 E4B QAT, Granite 4.1 3B): untested hypotheses |
| `prompts.py` | What each call asks: suite shapes, temperatures, output caps, system prompts, seeds and menu permutations, one prompt builder per shape and variant, reasoning-block stripping and JSON extraction, repair checks and messages |
| `backends.py` | The two local HTTP clients: Ollama `/api/chat` and llama-server `/v1/chat/completions` (both `stream: false`), plus the per-run server probe (version, model file, quant, context, template thinking check) |
| `cloud_backend.py` | The OpenAI-compatible client (`stream: false`): strict `response_format`, retries with backoff, error classification, redaction of the key, usage and cost parsing, and the checks that stop a run |
| `cloud_guard.py` | What a paid request may carry and how it travels: base URL, key and `--extra-body` checks, the `--schema-strip` whitelist, schema normalising, an opener that never follows redirects (and uses no proxy for a loopback server), the response-size cap |
| `cloud_run.py` | The `openai` flags and their refusals, record fields for the endpoint and the start-of-run warnings (an unpinned OpenRouter run, `--repeat-penalty` on OpenRouter), and the per-run session: ledger and its lock (plus the per-user free-run lock), budget, key check, key readings written to the ledger, stop rows, canary (with the schema-conformance check), the key check on every stop of a free run, exit codes |
| `budget.py` | The hard cap for paid endpoints: worst-case reservation per attempt, write-ahead ledger, settled costs, resume |
| `free_mode.py` | `--free-only`: its flags, the free-model id rule, the live-catalogue check (exact-zero prices, text output, endpoint parameters), the per-response zero-spend check, the free-run lock's location, the start and end checks of a free run |
| `free_key.py` | The OpenRouter key record in free mode: its non-secret fields (and the per-key rate limit), the refusals (management key, headroom, expiry, no daily counter), the usage-rise test, and the `key` ledger rows compared at the next start |
| `key_status.py` | `--key-status`: one `GET <base>/key` and nothing else; the key record's non-secret fields in plain words with the free-only verdict, one next-step line per failure (401, 403, 404, 429, 5xx, a redirect, not a key record, no connection), bodies shown only redacted, the flags a run line carries but the command skips |
| `rate_gate.py` | Client-side rate caps: requests per rolling minute, attempts per UTC day from the ledger, the account's remaining free requests less a reserve, the key poll hook, the 429 streak (HTTP 429 and 429 inside a 200); the 429 classifier (daily, per minute, upstream) and the daily cap's sane resume time |
| `cloud/README.md` | Owner runbook for safe free-model testing on OpenRouter |
| `cloud/set-openrouter-key.ps1`, `cloud/run-cloud.ps1`, `cloud/remove-openrouter-key.ps1`, `cloud/secret-common.ps1` | Windows key handling: store the key DPAPI-encrypted per user with a user-only access list (hidden input, never in a git working tree), run `run.py` with the key in that one child process's environment only (free-only rounds and `--key-status`; paid rounds with `-AllowPaid`), delete it; the plaintext never is a cmdlet argument (module logging), tracing is switched off and parameter defaults ignored when run in-process, and only DPAPI blobs are written or read |
| `cloud/provider-zdr.json` | The tier-0 provider block for `--extra-body @...` (`zdr: true`, `data_collection: deny`) |
| `score.py` | Scorer: summary CSV and JSON, console table, optional grading sheet; consumes open-arm grade files; `--suite-file` for suites outside `suites/` |
| `score_checks.py` | The code checks shared by `score.py`, `uplift.py`, the repair check and the canary: the schema subset, quoted spans, Fill validators, Text constraints, names, words and sentences |
| `grade_open.py` | Maps the open Pick arms' free-form answers to option keys (grade file), writes the judge sheet for the unmapped ones, and applies grade files for `score.py` and `uplift.py` |
| `logprob_pick.py` | `--pick-mode logprob`: the prompt rendered by the model's template plus the reply prefix, the top-N next-token probabilities from llama-server's `/completion` (every response shape; truncated lists refused), token variants mapped to menu letters, renormalisation over the valid letters and `X`, rotations averaged per option key, the calibration temperature, the token-boundary check through `/tokenize`, and the flag refusals |
| `logprob_dist.py` | The pure parts of the logprob mode: every response shape parsed with each entry checked, token variants mapped to letters, the per-letter distribution and its missing-mass bound, truncated lists refused, rotations averaged per key, temperature scaling |
| `scaffolds.py` | The scaffold arms' pure parts (`--scaffold`): the answer-blind item views, the plain Pick prompt rebuilt from a view, the diff lines, the subq and prefill texts and rule table, the quote-first schema and verbatim check, the one-call arms' requests |
| `scaffold_algos.py` | The scaffold algorithms that need no menu: word stems, the diff arm's nearest pairs and phrases, the rule arm's card sentence, the eliminate and pairwise rankings and aggregation |
| `scaffold_run.py` | The multi-call scaffold arms (eliminate, pairwise, subq, prefill): their requests (the scoring pass through the logprob mode on the view, chat calls, the raw prefill `/completion`), the per-call ledger, preflights, dry runs, and the records |
| `scaffold_stats.py` | Pre-registered analysis of the scaffold arms: resumed decisions folded, exact paired sign-flip tests per unit, Holm per (model, step kind), escape and category vetoes and side figures on the paired units, the SR3 hint-only veto from the control records, verdicts |
| `control_suite.py` | Writes the hint-only control of a Pick suite (requests swapped across categories or blanked; menus and answers kept) |
| `cascade.py` | Offline cascade simulator over Pick records (logprob or vote confidence; accuracy, escalation, cost and latency per threshold; baselines, signal quality, operating point with bootstrap and cross-fit) and the temperature fit that `--calibration` reads |
| `cascade_numbers.py` | cascade.py's numeric building blocks: safe numbers from records and flags, AUROC, ECE and Brier, the temperature fit |
| `uplift.py` | Arm comparisons: decision accuracy under single, vote3, adaptive and first-admitted policies, pass^k, CPCD and CPAD, false-admit rate, paired deltas with McNemar (scaffold arms paired with `plain` automatically), gap closure and non-inferiority, Pareto per suite; `--suite-file` |
| `suites/pick-open-aliases.json` | Sidecar for the open arms: stems per category and item, escape phrases, synonyms; declares `"shape": "sidecar"`, so it is never run |
| `suites/knowledge.json` | Doc 30's 12 knowledge tasks: prompt, ground truth, grading, card, evidence |
| `suites/pick.json` | 30 Pick menus: request, options (key, label, one-line description), escape, answer key, card, rationale, sources |
| `suites/pick-hard.json` | 30 harder Pick menus, same schema, 7 options each, 3 planted escapes; declares `"shape": "pick"` |
| `suites/fill.json` | 12 Fill items: request, instructions, schema, expected values, validators; banned era words |
| `suites/explain.json` | 10 findings: code, message, mission facts, card, schema, rubric (required facts, forbidden claims and patterns) |
| `suites/text.json` | 10 flavour-text slots: context, constraints (word cap, allowed names, digits, era, tone), schema; name allowlist |
| `tests/` | The offline test suite (see [Tests](#tests)): `test_*.py`, their shared fixtures (`support.py`, `cloud_support.py`, `logprob_support.py`, `scaffold_support.py`), the mock servers (`mock_server.py`, `mock_llama.py`, `mock_reason.py`), the payload dumps and goldens (`dump_payloads.py`, `dump_bodies.py`, `make_goldens.py`, `golden/`), and the key-script checks (`dpapi_round_trip.ps1`, `dpapi_trace.ps1`, `probe_env.py`) |

Each JSONL record holds the item id, model, suite, condition, variant, sample, seed, the raw content, `parse_ok`,
`parsed`, latency, `prompt_eval_count`, `eval_count`, `eval_duration` and the other timings (in Ollama's field names
and units for both backends), and `backend`, `runtime_version`, `model_file`, `quant` and `sampler_sent`;
llama-server records add the fields listed in the llama.cpp section. Pick records also hold the permutation, the
correct letter and position, and the chosen letter and key.

## Tests

The checks run offline. Mock servers stand in for Ollama, llama-server and OpenAI-compatible endpoints (standard
library, in-process on 127.0.0.1); no model runs, no real endpoint is contacted, nothing is spent, and every key is a
random dummy. The runner is the standard library's `unittest` (Python 3.8+, nothing to install). From the repository
root:

```text
python -m unittest discover -s tools/local-qual/tests                          # everything, about 5 minutes
python -m unittest discover -s tools/local-qual/tests -p "test_free_mode*.py"  # one group
python -m unittest discover -s tools/local-qual/tests -k t59 -v                # one case, by name
```

| Module | Cases | What they cover |
| --- | --- | --- |
| `test_cloud.py` | t03–t13, t18–t21, t59–t62 | Paid path: start refusals, the cap and `--resume`, retries and their cost, stops, key hygiene, shared ledger, key check, schema normalising, canary; the upstream-cost double count (doc 54 §4.2) and `--output` |
| `test_cloud_grading.py` | t14–t17, t22, t23, t35, t39 | Open and labels arms and their grading, Fill schema modes, repair, `uplift.py` |
| `test_cloud_guards.py` | t24–t34, t36, t37, t74, t76 | Break-in attempts found in review: redirects (t74: one whose target cannot be parsed), smuggled keys and fields, a second process on the ledger, bodies that are not completions, errors inside a 200, cost 0 reports, ignored schemas, think blocks; t76: error bodies with an infinite `code` or nested past the JSON reader's depth, which crashed `chat()` |
| `test_cloud_review.py` | t63–t66 | Review of the merged tool: `--extra-body` fields billed at other rates, a thinking budget the worst case missed, a key JSON would escape, `--repeat-penalty` on OpenRouter |
| `test_cloud_regression.py` | t01, t02, t38 | The local backends' request bodies and scores against the tool before the cloud backend (goldens) |
| `test_free_mode.py` | t40–t50 | `--free-only`: refusals, catalogue traps, request shape, zero-spend guard, substitution, key rules, key poll, daily cap and day boundary, account quota, 429s, rate-gate units |
| `test_free_mode_review.py` | t51–t58, t75 | Second review of free mode, and the DPAPI key scripts through PowerShell (t53: 15 steps, `--key-status` through the launcher among them); t75: a label planted in the key record's date fields |
| `test_key_status.py` | t67–t73, t77 | `--key-status`: the report field by field, the key and label never shown (in bodies, record fields, redirect targets and `\u`-escaped copies), one next-step line per failure, refusals before sending, a run line with `--key-status` running only the key read, the limit that applies named; t77: a label holding a quote or a backslash scrubbed as written in a decoded error message, and a label nested below the record's own kept out of its date and period fields |
| `test_rate_limit_source.py` | r01–r08 | 429 classification by `limit_source` first: the observed shared-pool body, daily-looking text and far resets that stay upstream, unchanged behaviour without the field, undocumented and non-string values, escaped labels in the recorded error, back-off through `chat()` including 429s inside an HTTP 200 |
| `test_rate_limit_stops.py` | r09–r15 | Two 429 stops: a daily-cap 429 whose `X-RateLimit-Reset` is absurd (huge, past the year 3000, not a number, negative, in the past, over a day past midnight) resumes at the next 00:00 UTC, through `chat()` and as a free run (exit 10, unbilled, no traceback); 429s inside an HTTP 200 count toward the `--max-consecutive-429` streak (a free run stops as rate-limited after 3, an answer resets it, both forms share it) while paid gates retry as before; a daily-cap 429 that completes a streak still stops as the daily quota (r15) |
| `test_source_text.py` | h01 | No hidden characters in the tool's `.py` and `.ps1` sources: C0 controls, bidi overrides and isolates, zero-width and tag characters, line and paragraph separators (a leading BOM and CRLF are allowed) |
| `test_logprob_pick.py`, `test_logprob_failures.py` | l01–l19 | `--pick-mode logprob`: flags, request bodies, known distributions, response shapes, failures and hostile responses |
| `test_logprob_cascade.py` | c01–c08 | `cascade.py` against hand-computed values, calibration, an end-to-end run, refusals |
| `test_scaffolds.py`, `test_scaffolds_function.py`, `test_scaffolds_stats.py` | a01–a03, b01–b10, c01–c15, d01–d07 | Scaffold arms: regression, leakage and answer-blindness, what each arm computes and sends, `scaffold_stats.py` and `control_suite.py` |
| `test_presets.py`, `test_presets_plan.py`, `test_presets_run.py` | p01–p21 | Harness presets: the drafts and the checker's negative controls, strict loading and bases, the knob plan and its refusals, flag conflicts, preset runs byte-identical to their flags, the record, `--resume` with and without a preset |

- **Case names.** Each check is a function named after its group and number (`t04_budget_cap_...`, `l03_...`);
  the verification notes below cite them. `tests/support.py` turns each into a `unittest` method; `-v` shows the
  first line of its docstring.
- **Switches.** `LOCALQUAL_TEST_DETAIL=1` prints each passing case's one-line summary of what it verified.
  Work folders go to the system temp folder and are removed afterwards; `LOCALQUAL_KEEP_WORK=1` keeps them, and
  `LOCALQUAL_TEST_WORK=<dir>` puts them in `<dir>`. `LOCALQUAL_TOOL=<dir>` runs the suite against another copy of
  the tool (a deliberately broken one, for mutation checks).
- **Key sweep.** Each cloud and free-mode module ends by searching every file it wrote and every console transcript
  for the dummy keys and the masked key label; a leak fails the module.
- **Windows only.** t36 (a ledger path in another letter case), t53 and t58 (the key scripts under `powershell.exe`)
  are skipped on other systems.
- **Goldens.** t01, t02, t38 and a01 prove that later changes left earlier measurements alone, so they compare with
  files frozen from earlier tool versions in `tests/golden/` (per-command digests of every default request, record
  and dry run, and the pre-cloud scorer's summary). Regenerate them only deliberately, with `tests/make_goldens.py`,
  whose docs say when and from which baseline: a suite edit changes the requests (regenerate from the current tool),
  and a code change that is meant to change a default request must say so and regenerate from the tool before it.
  `.gitattributes` keeps the suites and goldens LF on every checkout, because `suite_sha` hashes the suite file's bytes.
- **Staged pools.** Set `LOCALQUAL_POOLS` to the folder holding `pick-pool.json` and `fill-pool.json` to include
  their tune halves in the leakage checks (b01, b02, b10) and in c12 and d07; without it, c12 and d07 use a
  pool-shaped copy of `pick-hard`.

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
- 2026-09-27, cloud backend, harness-uplift variants, `grade_open.py` and `uplift.py` added, and the runner split into
  `run.py`, `prompts.py`, `cloud_backend.py` and `cloud_run.py`. Tested offline only: no real endpoint was called, no
  account or key was used and nothing was spent. A mock OpenAI-compatible server (standard library; canned answers with
  usage, cost and a provider name; scripted 429, 5xx, 402, schema rejection and errors inside a 200) ran 24 checks, all
  passing: the refusals to start (no `--max-usd`, no prices, no key variable, a key on the command line, no
  `--reasoning`, plain http to a remote host, forbidden `--extra-body` fields, response healing, `--warmup`), with 0
  requests reaching the server; the cap stopping a run before an attempt could overspend (every sent call satisfied
  spent + worst case <= cap), a resume at the same cap sending nothing and a resume at a larger cap finishing without
  re-sending a call; 429s retried (Retry-After honoured) and not charged, 5xx retries charged their reservation;
  schema rejection stopping after one request, never retried without the schema; the key (echoed back by the mock in
  error bodies and in content) absent from every record, ledger and console line; 402, a provider error inside a 200,
  a provider mismatch, a cost above the worst case, reasoning tokens on an effort-none call and the canary each
  stopping as documented; a shared ledger capping a second run; the open arms' requests, grading, judge sheet and
  scoring; Fill without and with schema text; the repair call and its summed cost; the key check; schema normalising;
  and `uplift.py` against hand-computed values (Wilson 8/10 = 0.490–0.943, McNemar b = 8, c = 2: p = 0.109, pass^3
  with 4 of 5 = 0.4, a synthetic scenario's deltas, CPCD per policy and gap closure H = 5/3). The Ollama and
  llama-server request bodies were byte-identical to the previous version over 2,180 requests from 40 command lines
  (every suite, both conditions, `--why`, sampler pins and overrides, the bearer key from the environment and from
  the command line), and `score.py` reproduced every summary value of the previous version on those records. Seven
  deliberate faults (budget gate off, redaction off, retries off, schema rejection downgraded, 429 charged, resume
  ignoring the ledger, the longest-match rule removed) were each caught by at least one of these checks.
- 2026-09-27, adversarial review of the cloud backend, offline against the same mock (nothing sent to a real
  endpoint, nothing spent). Fifteen new attack checks each failed on the code as first written and pass after the
  fixes: a 302 from the endpoint (or from `GET /key`) made urllib re-send the bearer key to the redirect target; a
  key with a trailing newline crashed the run and printed the key in the traceback; a second process on the same
  ledger ran alongside the first and could spend the cap again; `--extra-body` accepted fallback `models`, the web
  plugin, `web_search_options`, a `prompt` field, a credential field or the key itself, and `--schema-strip enum`
  loosened the strict arm; zero prices, a negative backoff and `--num-predict 0` were accepted; a streamed or
  oversized 200 was retried five times per call; 402 or 401 inside a 200 did not stop the run; an attempt that cost
  5 USD against a 0.0016 USD worst case was retried because it had failed; a provider reporting `cost: 0` was
  believed; an unknown body field was left out of the worst case; an endpoint ignoring `response_format` (fenced or
  off-enum JSON) passed the canary; an OpenRouter strict arm could start without `require_parameters`; a
  `<think>{"choice": "B"}</think>{"choice": "A"}` reply was scored as B, and thinking text on an effort-none call went
  unnoticed; `uplift.py` scored a partly graded open arm on its graded subset; on Windows a `--ledger` differing
  from `--out` only in letter case was treated as a second ledger; nothing said that without `--ledger` the cap
  covers one output file only; and `--variant open --condition cards` was accepted although the Pick cards name the
  answer's option in 43 of 60 items (now refused). No open prompt without a card (request plus stem) contains an
  alias of its answer. With the 24 earlier checks, 40 checks pass, including the byte-identical Ollama and
  llama-server request bodies and a new check that the local records the changed runner writes score exactly like
  the previous runner's; 26 deliberate faults (the earlier 7 and one per new guard) are each caught. The request checks moved from `cloud_backend.py` into `cloud_guard.py`.
- 2026-09-27, free-only mode (`free_mode.py`, `rate_gate.py`) and the Windows key scripts (`cloud/`), tested offline
  against the extended mock (a public catalogue with a free model, a paid model and nine traps; the key record with
  a live daily counter; OpenRouter's daily-cap 429; model substitution). Nothing was sent to a real endpoint, no
  account or real key was used, and nothing was spent. Fourteen new checks pass. They cover: 21 offline refusals
  with 0 requests (paid ids, `openrouter/auto:free`, other suffixes, a non-OpenRouter host, any non-zero cap or
  price, no ledger, looser routing, out-of-range rate flags, `--free-only` on a local backend); the nine catalogue
  traps refused at start (exit 9) with the key never read and the catalogue fetched without it; missing strict
  schema or seed support refused with the fix named; a charged response, a response without usage, a BYOK cost, a
  cost on an error inside a 200, the paid sibling model and another provider each stopping after one call (exit 9);
  a charged ledger refusing to start again; the key rules (no limit, headroom over the threshold, a management key,
  an expired key, no daily counter); the key poll stopping on a usage rise; the daily cap, a same-day resume sending
  nothing, and a resume across a simulated day boundary finishing without repeats; the account's remaining count
  less the reserve, re-read mid-run; daily-cap, per-minute and upstream 429s; the per-minute window carried across
  runs from the ledger; `sk-or-` redaction; and a DPAPI round trip of the three scripts with a dummy key (no
  plaintext in the file, a user-only access list, the same value in the child's environment and nowhere in this
  session's, arguments quoted intact, nine refusals starting no child, an end-to-end `run.py --free-only` run, and
  removal). The paid path's earlier checks still pass, including the byte-identical local request bodies.
- 2026-09-27, adversarial review of the free-only layer, offline with dummy keys only (the only network reads were
  OpenRouter's keyless catalogue and documentation pages). Each of the following failed on the code as it was and
  passes now. A charge that no response showed was forgotten: a stream body while the key's usage rose ended as a
  plain configuration stop, and a start took the key's current usage as a fresh baseline. Every stop now reads the key
  once more, and each reading is written to the ledger and compared at the next start. Two free runs on two ledgers
  ran side by side, so each kept its own rate caps; there is now one free run per user at a time. A per-minute wait
  across 00:00 UTC booked the attempt to the old day. A whole-second ledger stamp left the minute window up to 1 s
  early. `run.py` kept the key variable in its environment. In the key scripts: `Set-PSDebug -Trace 2` printed 46 of
  the key's 64 secret characters; a trailing-space key went through `ConvertTo-SecureString -AsPlainText`, which
  module logging records verbatim (checked with a harmless marker); and a caller's `$PSDefaultParameterValues` turned
  the DPAPI blob into AES under a known key. The runbook now says where "Input & Output Logging" lives (Settings →
  Observability). All 58 tests and the final key sweep pass, and each of 66 deliberate faults (12 new) is caught.
- 2026-09-28, `--pick-mode logprob` (`logprob_pick.py`) and the cascade simulator (`cascade.py`), tested offline only:
  no model ran. A mock llama-server (standard library: `/apply-template` rendering like the Qwen3.5 template,
  `/completion` answering from a scripted next-token list in each of the five response shapes, `/v1/chat/completions`
  for the sampled arm) ran 19 checks, all passing. Logprob mode: the request bodies (the prompt is exactly the rendered
  template plus `{"choice": "`, `n_predict` 1, `n_probs` 32, temperature 0, no sampler or grammar fields); a known
  list renormalised by hand (hold 0.5, sentry 0.2, the rest 0.1, two letters missing); token variants adding up
  ("A", " A", `A"`, `A"}`, "▁B", "ĠC", lower case) while "AB", "A1", "Al" and a quote inside the string do not; all
  five response shapes giving the same distribution; letters cut from the top 20 recorded as missing with their
  floor; a reply with no menu letter scored wrong, not as an error; the escape read at `X` and letters beyond a
  5-option menu ignored; `--permute 7` sending 7 rotations with `X` fixed and averaging per key to the hand-computed
  values under a planted position bias that `--permute 1` falls for on 2 of 3 samples; calibration at T = 2 changing
  the confidence (0.5 to 0.336) but not the choice; 31 refusals with 0 requests; a build without `n_probs` stopping
  after one request (exit 3); a 500 recorded as an error and re-run by `--resume`; a template rejecting
  `chat_template_kwargs` retried without it; listed probabilities summing to 1.8 recorded as an error; malformed
  entries (NaN, strings, booleans, values outside [0, 1], positive logprobs, duplicate ids, bad bytes) ignored and a
  1,000-entry list cut to `n_probs`. Cascade simulator: a 10-unit logprob chain against hand-computed accuracy,
  escalation, cost, latency, random-escalation baseline, oracle, AUROC (0.84), Brier (0.1725), ECE (0.29) and the
  operating point; a vote chain with a tie and a failed sample; pairing (an unpaired unit and a changed option order
  dropped, a retried key costed twice); unusable confidences (NaN, a string, a boolean, 1.5) always escalating; the
  temperature fit matching its closed form (T = ln 9 / ln 1.5 = 5.419); an end-to-end run of `run.py` (logprob and
  sampled arms) into `cascade.py` and back through `--calibration`; and 19 refusals. Each of 33 deliberate faults
  (one per guard or rule above) is caught by these checks. The 59 earlier checks still pass, including byte-identical
  Ollama and llama-server request bodies in the default mode over the same 2,180 requests. `cascade.py --signal vote`
  also ran over existing `pick` and `pick-hard` records of 3–4B and 26–30B models and paired every unit.
- 2026-09-28, review of the logprob mode and the cascade simulator against llama.cpp's current server source
  (`populate_token_probs`, `process_token`, `probs_vector_to_json`, `get_token_probabilities`,
  `oaicompat_chat_params_parse`, and the BOS stripping in `common/chat.cpp`) and the tokenizer metadata of local GGUF
  files (header only; no model ran). Fixed, each with a check written first: a token whose text the server cut at a
  partial UTF-8 character was counted as its letter (now read from its bytes); tab variants counted although run.py
  cannot parse them; the byte cap (64) dropped real tokens (Qwen3 and Qwen3.5 have tokens of up to 128 bytes; now
  256); a truncated candidate list (backend sampling) would have read as certainty (now refused at the preflight and
  per decision), and so would a second generated token's list; the template render now gets the generate mode's
  `response_format` and `model` too; the token-boundary check through `/tokenize` is new (offline, the Qwen3, Qwen3.5
  and Gemma 4 vocabularies all split at the prefix end); NaN or Infinity in a response's counts crashed the run and a
  non-object template reply crashed it; a failed order's call went uncounted. `cascade.py` now pairs units on the
  answer key too, refuses a calibration file fitted on another model, splits `ARM=VALUE` at the first `=`, and has
  `--min-valid-mass`; its arithmetic was re-derived and found correct. 27 logprob and cascade checks pass (8 new, 5
  extended), each of 51 deliberate faults (18 new) is caught, and the 59 earlier checks still pass, including
  byte-identical default request bodies over the same 2,180 requests.
- 2026-09-28, reasoning scaffolds (`--scaffold`, `scaffolds.py`, `scaffold_run.py`), `--suite-file` and `--split`,
  `scaffold_stats.py` and `control_suite.py`, tested offline only: no model ran. A mock llama-server and Ollama
  (standard library; a prompt-only mock model whose replies depend on a hash of the prompt's menu lines, never on an
  answer) ran 29 checks, all passing. Regression: over 69 command lines (every suite and condition, `--why`, every
  variant, `--repair` with a failing first answer, sampler pins and overrides, both local backends, bearer keys, dry
  runs, `--pick-mode logprob`), 1,653 request bodies, 1,615 records (timing fields removed) and 3 dry-run prints are
  byte-identical between the previous tool, this one, and this one with `--scaffold none`; the plain Pick prompt
  rebuilt from the answer-blind view equals `build_pick_order`'s for all 90 tuning items (pick, pick-hard, the Pick
  pool's tune half) × 3 samples × 2 conditions. Leakage: with every answer moved to another key and every non-prompt
  field poisoned (rationale, sources, pool metadata; Fill expected values, lures, notes), 26 arm runs sent the same
  2,446 request bodies as on the original suites and no poisoned text; every word of 1,620 scaffold texts is a word of
  the plain cards prompt or of the arm's fixed template, and no key the prompt does not show appears; no scaffold states
  a verdict; permuting the options permutes the lines and changes nothing else; every option and clause is treated
  alike; an instruction injected into the request never enters the diff lines or the thought. Function: the diff and
  rule algorithms against hand-computed values (IDF 0.916 / 0.916 / 1.386; HM04's documented lure sentence); the why
  schema bounds; eliminate keeping the top 3 plus X even when X led, with letters mapped back; pairwise's six calls in
  both orders and its rule cases; subq's shared clauses, rule table and one- or two-call paths; prefill's exact
  prompts in both channels, its letter grammar, no schema on `/completion`, and exit 3 for a template without an empty
  think block; quote-first's schema, verbatim check and score; 19 refusals with 0 requests; ledgers whose sums are the
  record totals; `--resume`; a failed pair call recorded as an error and re-run; the one- and two-call arms on Ollama;
  `--suite-file` with split refusals, `score.py` and `uplift.py` (scaffold arms auto-paired with plain); exact
  sign-flip p-values (3/16, 1/1024) and Holm; the verdict rules including the escape veto; the hint-only control
  suite, where the prompt-only mock scores near chance in every arm. Each of 14 deliberate faults (reading the answer,
  the rationale or a Fill item's expected span, a verdict, order dependence, a skipped option or clause, a masked X, a
  changed default request) is caught by at least one check. The 27 logprob and cascade checks and the 59 cloud-backend
  checks also pass on the changed tool.
- 2026-09-28, adversarial review of the scaffold arms (offline; no model ran). Found and fixed: `scaffold_stats.py`
  counted a decision re-run by `--resume` after an error as an extra sample, so the unit left the paired test unseen
  (the plan chunks long runs with `--resume`); it computed the SR2 false-escape veto, latency, tokens and model calls
  over every record of each arm instead of the paired units, so the cards-only `rule` arm was held against plain's
  none-plus-cards pool (a synthetic arm with 3 false escapes in 33 passed against a pooled 0.5 and was called a
  winner; against plain's cards units, 0, it is vetoed); it let any other variant in its input glob join the Holm
  family and get a verdict; it did not apply SR3 at all (the plan's winner rule) and dropped records of a suite whose
  file was not passed without a word. Scaffolds: the prefill tail asked for the option that "fits every part of the
  request", a stricter, X-leaning test that the diff arm does not get (it now restates the system prompt); quote-first
  replaced any model field that was not a byte-exact substring, overwriting spans the item's own validator accepts
  (another case, a trailing full stop), and counted a blank quote as verbatim; the one-call arms received the full
  item's option objects (only key, label and description now reach them); the ledger had no per-call cap and no count
  of calls cut at their cap, which PR1 needs because a record's `done_reason` is only its last call's. Scaffold
  version 2. Checked and found sound: the answer-blind views, every request body of the existing command lines, the
  prefill template handling (the rendered prompt plus the skeleton, `limit` and `tokens_evaluated` as llama-server
  b11146's `server-task.cpp` reports them), the eliminate and pairwise rankings, the sign-flip and Holm arithmetic.
  Cue audit: no rule that reads only a scaffold's output (the option in most diff lines, the closest pair, the most or
  fewest "only" phrases, subq's most clauses under an all-yes model, the rule sentence under a foreign request) picks
  the answer above 0.172 on the 60 tuning menus (chance 0.125); in 34 of those menus one option appears in 3 to 5 of
  the diff lines (the answer among them in 5), a salience asymmetry kept as specified. 35 scaffold checks pass (6
  new, 3 extended, among them option-object poison in the answer-swap check); 25 of 25 deliberate faults are caught
  (11 new); the logprob, cascade and cloud-backend checks pass on the reviewed tool.
- 2026-09-28, the cloud backend (paid and free-only), the key scripts, `--pick-mode logprob`, `cascade.py` and the
  scaffold arms landed here from their tested patches, with their checks moved into `tests/` (see [Tests](#tests)).
  Tested offline only: no model ran, no real endpoint was called, every key was a random dummy. The checks that
  compared this tool with a copy of an earlier version now compare with goldens frozen from that version: 2,180
  request bodies over the 40 local command lines of the tool before the cloud backend (t01), its scorer's summary of
  38 groups (t02, t38), and 1,653 request bodies, 1,615 records and 3 dry runs over the 69-command grid of the tool
  before the scaffold arms (a01, without the flag and with `--scaffold none`). t02 scores the current runner's records
  cut down to the 46 fields the pre-cloud runner wrote; before freezing, that projection was checked to reproduce all
  2,180 pre-cloud records exactly (apart from run_id, ts and latency_ms). Fixed while landing, each test first: the
  budget added OpenRouter's `upstream_inference_cost` to `usage.cost` on every call, although outside a BYOK request
  both report the same money (doc 54 §4.2); t59–t61 failed on the patch as screened (every record's `cost_usd` twice
  its billed cost; a call billed at 60% of its worst case stopped as `CostAnomaly`) and pass now, and t20's BYOK case
  now says `is_byok`. `cloud/run-cloud.ps1` could not name the output file, because `powershell -File` reads `--out`
  as its own `-OutVariable`/`-OutBuffer` ("the parameter name 'out' is ambiguous", reproduced before the fix);
  `--output` is now an alias of `--out` (t62 failed with exit 2 before), and the key-script check passes it through
  the launcher (14 checks now). The five files over the ~600-line ceiling were split with every name re-exported
  (`run_cli.py`, `run_records.py`, `score_checks.py`, `logprob_dist.py`, `cascade_numbers.py`, `scaffold_algos.py`);
  the goldens above were unchanged by the split. All 124 checks pass, none skipped, in 312 s on Windows 10 with
  Python 3.12 (`python -m unittest discover -s tools/local-qual/tests`): the 120 moved here and t59–t62.
- 2026-09-28, harness presets (`--preset`, `presets/`; D048, doc 55 §3). The schema (draft 2) and the four 0.1.0 draft
  presets were copied from the staged tuning material; the drafts gained an "untested hypothesis" first note, and the
  schema's description now points at `presets/lint.py`. The staged draft checker was ported as `presets/lint.py`, its
  three negative controls (a Pick presence penalty of 1.5, a step granting itself Compose, a cascade route naming a
  model) became p02–p04, and the rules the schema's description names but cannot express became p05's twelve controls.
  Written test first: p01–p20 failed before the code existed (the checker did not import; `run.py` rejected
  `--preset`) and pass now. Mutation check: 15 safeguards broken one at a time in a copy of the tool (the second-stage
  rule, duplicate keys, NaN, the size cap, the override check, neutral penalties, the flag-type conversion, the
  compact grammar passed as strict, unknown knobs ignored, fixed knobs unchecked, the conflict check, the withdrawn
  check, the resume hash check, the label suffix, the flag ignored); each made at least one p-case fail. Without
  `--preset` nothing changed: a01, t01, t02 and t38 pass against their goldens. All 144 checks pass, none skipped, in
  247 s on Windows 10 with Python 3.12. Offline only: no model ran, no endpoint was called.
- 2026-09-28, adversarial review of the merged tool: paid and free-only cloud runs, logprob mode, scaffold arms and
  presets. Offline only: no model ran, no real endpoint was called, every key was a random dummy. Checked and found
  sound: the reservation, the write-ahead ledger and the settlement (the doc 54 double count stays fixed); refused
  redirects; the redaction of every string the client returns; the free-only guards; and the request bodies. The
  openai bodies are byte-identical to the tool before the merge over 34 command lines (253 bodies: every suite and
  condition, `--why`, the uplift variants, `--repair`, four reasoning forms, schema normalising and stripping, dropped
  parameters, sampler pins, a pinned provider block with rate caps, two free-only runs), and the local bodies match
  their goldens (t01, a01). No path falls back to an unconstrained answer: a schema rejection stops the run, and the
  local retries drop only the thinking switch. Every preset knob maps to an existing flag, and every later refusal
  still applies. Found and fixed, each with a check written first that failed on the merged code:
  - `--extra-body` accepted `service_tier`, `modalities` and `audio`, which bill at rates the price flags do not name
    (t63);
  - `--reasoning '{"max_tokens": 5000.0}'` (or `"5000"`, `true`) went out as a thinking budget while the worst case
    added nothing for it: an output cap of 64 instead of 5,064 (t64);
  - a key holding a double quote or a backslash passed the key check; echoed by the mock inside `usage`, it reached
    the record JSON-escaped, where the scrub could not find it (t65);
  - `--resume` without `--preset`, under a preset run's `--label`, finished the preset's decisions with the command
    line's own knobs (p21).

  `--repeat-penalty` goes out as `repeat_penalty`, which OpenRouter lists as `repetition_penalty`, so on OpenRouter
  the pin was most likely dropped while the records listed it. The body is unchanged (existing command lines keep
  their bytes); the run now warns at the start with the fix (t66; friction register FR-C-032). All 149 checks pass,
  none skipped, in 329 s on Windows 10 with Python 3.12.
- 2026-09-28, `--key-status` (`key_status.py`), offline only: the mock gained scripted `GET /key` replies, no real
  endpoint was called, and every key was a random dummy (the launcher step used a throwaway DPAPI blob in a temp
  folder). Written test first: t67–t71 failed before the code existed (`run.py` rejected `--key-status`; t70 could
  not import `key_status`), and t53 failed on its new step 15 (the launcher refused `--key-status` without
  `--free-only`); all pass now. t67 checks the report field by field and that one `GET /key` and nothing else was
  sent; t68 that neither the key nor the record's `label` (with or without `sk-or-`) reaches the console, on success
  or inside four hostile error bodies; t69 one next-step line per failure (401, 403, 404, 429, 500, 503, a non-JSON
  200, a 200 without a record, a 302, a closed port) with its exit code, and an escape sequence and a bidi override
  shown escaped; t70 ten refusals with 0 requests, and the default base URL in-process with the default pointed at the
  mock, so a regression cannot reach openrouter.ai; t71 a free-run and a paid-run line with `--key-status` added
  (no catalogue, chat, ledger, output file or lock; a held free-run lock untouched). Mutation check: 14 deliberate
  faults in a copy of the tool (the three body scrubs, the default base for any key, the `--dry-run` and `--api-key`
  refusals, 5xx as a key fault, no escaping, the label printed, the skipped-flags note, -1 read as a limit, the
  dispatch after the suite check, and two launcher faults) are each caught. Default requests and records are
  unchanged: a01, t01, t02 and t38 pass against their goldens. All 154 checks pass, none skipped, in 299 s on Windows
  10 with Python 3.12.
- 2026-09-28, adversarial review of `--key-status`, offline only (loopback mock, random dummy keys, no page or
  endpoint of OpenRouter opened). Found and fixed, each test first (red on the code as reviewed, green now): a
  redirect's Location host was printed unredacted, so a 302 to `<key>.example` showed the whole key (t72); a JSON
  body writing a label or the key with `\u` escapes, or a label with quotes in error metadata, escaped the scrub
  (t72); a 300 with an unparsable Location crashed `--key-status` (t73) and a paid or free run (t74, in `chat()`,
  older than `--key-status`; `cloud_guard.redirect_host` serves both now); a label planted in the key record's
  `limit_reset` or `expires_at` reached a free run's console and records (t75, `free_key.key_summary`, older too);
  the report presented the per-key `rate_limit` ("none") and the daily counter as the limits that apply, while doc
  52's re-check of 2026-09-28 found the counter lagging and the free-model limits count per account (t73 now wants
  both said). Guards the first tests did not pin, each now caught by t72 or t73 when removed in a copy of the tool:
  the record-field scrub, the verbatim key scrub of report lines (another provider's 40-character key passes the
  date filter), the body cap, the daily-against-minute 429 wording. The runbook's "read again 2026-09-28" source
  dates were removed: no page was re-read; the 429 texts and the two caveats now cite doc 52's observations. All
  158 checks pass, none skipped, in 384 s on Windows 10 with Python 3.12.
- 2026-09-28, two 429 stops and their adversarial review, offline only (loopback mocks, random dummy keys, nothing
  spent). A daily-cap 429 with an absurd `X-RateLimit-Reset` crashed `chat()` while it formatted the resume time
  (OverflowError for 1 followed by 30 zeros, OSError past the year 3000 on Windows): exit 1, the call's reservation
  left unsettled, no stop row. A reset in the past printed "resume after" the current time. `rate_gate.daily_wait`
  now keeps a reset only when it is above 0 and at most a day past the next 00:00 UTC, and uses the next 00:00 UTC
  otherwise; `daily_resume_time` formats it without raising (r09–r11). A 429 inside an HTTP 200 now counts toward
  `--max-consecutive-429` like an HTTP 429 (r12, r13), and paid gates still retry (r14). Written test first: r09–r13
  failed on the code before; r14 pins the unchanged paid path. The review then found two more faults, each written
  test first. A body with `"code": 1e999` or `Infinity` raised OverflowError in `_code_and_message`, and one nested
  a few thousand levels deep raised RecursionError in `_json_or_none`. Either crashed `chat()` on any status, with
  the reservation unsettled and exit 1 (t76; older than these fixes; `key_status.py` already caught the second).
  No test pinned that a daily-cap 429 completing a streak stops as the daily quota, not rate-limited, and moving
  the streak check first on either path passed the whole suite (r15). Mutation check in copies of the tool: 17
  faults are each caught. They are the classifier without `daily_wait`, no upper bound, no lower bound, the bound
  off by one, no slack, the bound as the fallback, no NaN guard and no bool guard (r09, with r10, r11 or r03–r06
  for some); the HTTP status alone in the streak, no stop inside a 200, an HTTP 429 resetting the streak, any
  embedded error counting and a paid gate stopping (r07, r12–r14, t49); the streak before the daily cap on either
  path (r15); and either `except` narrowed back (t76). Three changes are unobservable: formatting the resume time
  with `time.gmtime` again, and dropping the formatter's rounding or its exception handler, because `daily_wait`
  has already bounded the wait. All 175 checks pass, none skipped, in 289 s on Windows 10 with Python 3.12.
- **`--key-status` mutation check repeated in isolation (2026-09-28).** An earlier run shared a scratch folder with
  another agent, so it was repeated on a clean copy of the committed tool: all 16 listed faults are caught and every
  earlier "caught" claim reproduces. Two further faults survived the whole suite, both guards that work but that no
  test pinned: scrubbing a label in its exact written form when it holds a quote or a backslash inside a decoded
  error message, and keeping a label nested below the record's own out of the date and period fields. t77 was
  written for them; it fails on each of the two faulty copies and passes on the tool. All 176 checks pass, none
  skipped, in 273 s.
