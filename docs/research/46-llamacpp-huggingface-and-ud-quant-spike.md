# Runtime and quant spike: llama.cpp straight from Hugging Face, UD vs Q4_K_M

Research doc 46 for Plotroom (`ofp-editor`). Research and run date: 2026-09-27. Audience: contributors and LLM coding agents. This file is
meant to be read on its own.
Question answered (owner, paraphrased): test the UD quant; and why use Ollama at all? Use whatever gives the most flexibility and gets
models directly from Hugging Face.

**Status.** Measurements are **[V]**. Verdicts, recommendations and the Model Manager and sidecar notes are proposals **[I]**.
**Epistemic legend.** **[V]** measured in this spike (re-derived from the raw call records, `score.py` output, the grade files, the GGUF
headers or the upstream source at the named tag). **[V per doc N]** taken from a sibling doc. **[I]** our inference or proposal.
**[U]** unknown.
**Data.** Aggregates, setup facts and every paired test are in
[`data/runtime-quant-comparison.csv`](data/runtime-quant-comparison.csv) (columns `model, runtime, quant, suite, condition, metric, value,
n, notes`; 2,814 rows). Comparison rows name both arms in `model` (`A vs B`) and their test family in `notes`. The harness is
[`tools/local-qual/`](../../tools/local-qual/README.md), now with a llama.cpp backend. Raw call records, grader notes and the run driver
stay local (`results/` is git-ignored), as in docs 30 and 44.
**Relation to sibling docs.** Doc 13 chose llama.cpp and planned the managed `llama-server` sidecar and the pinned download; doc 14 named
the candidate quants (§3.2 lists Qwen3.5-4B at 2.74 GB Q4_K_M and 2.91 GB UD-Q4_K_XL and says "qualify both"); doc 44 measured four
Ollama builds and left the UD comparison and a harder Pick instrument open (§5.4 items 3, 4 and 9); doc 47 widens the candidate list.
D022 accepts the Model Manager, D023 the model tiers and the licence rule (decision 6), D008 the user-enabled download sources.
**Hygiene.** Every suite item is our own text. Model answers are only paraphrased. No local paths or user names appear here: models
were stored outside the repository under a directory named by `LLAMA_CACHE`.

## TL;DR

- **The UD quant brings no detectable gain.** Qwen3.5-4B UD-Q4_K_XL against Q4_K_M, same repository commit, runtime, sampler, seeds and
  option order: per-call Pick accuracy 0.922 / 0.967 vs 0.933 / 0.967 (none / cards), harder menus 0.811 / 0.900 vs 0.822 / 0.867.
  0–2 menus per cell were right by majority in only one of the two builds; exact McNemar p = 1.0 in all four cells, and every
  paired bootstrap 95% interval includes 0 (−6.7 to +7.8 points). Gemma 4 E4B UD vs Q4_K_M: the same (p = 1.0 in all four cells).
  Fill and text show no difference either. UD costs +143–190 MiB of GPU memory, 7–8% generation speed and +0.15–0.17 GB of
  download [V].
- **No detectable Pick quality difference between llama.cpp and Ollama.** 16 paired Pick comparisons (three Qwen arms and one Gemma pair, on both menu suites and
  both conditions): none significant (p 0.25–1.0; Holm-adjusted 1.0) [V]. Fill leans towards llama.cpp (all fields right per call:
  Qwen 0.639 vs 0.472, Gemma 0.861 vs 0.639; bootstrap intervals exclude 0, but only 2–3 records differ by majority, p 0.25–0.5),
  cause unknown [V; U].
- **llama.cpp's Vulkan build is slower on this Pascal card, mostly in prompt processing.** Warm Pick p50: 1,046 ms (Qwen
  Q4_K_M) and 1,126 ms (Gemma QAT) on llama.cpp vs 700 and 590 ms on Ollama. Uncached prompt tokens are processed at 215–337
  tokens/s vs 620–710 (Pick and harder menus). That accounts for all of Qwen's gap and about 320 of Gemma's 536 ms; the rest of
  Gemma's is its pretty-printed JSON (16 output tokens per pick instead of 7, §2.6). Generation speed is equal or faster (Qwen 48.7
  vs 40.4 tokens/s, Gemma 45.0 vs 45.4). Long answers come out close (Qwen explain 2,530 vs 2,446 ms) [V]. The likely cause is
  Vulkan on Pascal against Ollama's (probably CUDA) backend [I].
- **llama.cpp uses less GPU memory:** +3,080–3,455 MiB at peak for the six text-only builds vs +4,052 (Qwen) and +4,361 MiB (Gemma)
  for the Ollama library builds, leaving 1,959–2,418 MiB of the 8,192 MiB card free instead of 1,052–1,361 [V]. The Ollama builds also
  carry vision and audio parts [I].
- **Straight from Hugging Face works, pinned.** Repository + commit + file + size + SHA-256 from the Hugging Face API, a resumable
  HTTPS download from `resolve/<commit>/<file>`, a hash check and an atomic rename: all five files matched, at 35–37 MB/s. The
  `-hf` shortcut also works but follows `main` and cannot be pinned. The file name is the only reliable quant label: UD-Q4_K_XL and
  Q4_K_M both report GGUF file type 15, and Unsloth's Gemma QAT "UD-Q4_K_XL" is 99.95% plain Q4_0 [V].
- **Hidden defaults can matter as much as the runtime.** Ollama's Qwen build sets `presence_penalty 1.5`. llama.cpp's server feeds
  every prompt token into the penalty history, so the penalty lands on the last menu letters. On llama.cpp, adding it cost 8 of 360
  Pick calls, which moved llama.cpp's Pick total from 7 calls above Ollama's to 1 below (315 vs 316); every harder-menu call it lost
  had its answer at G or X [V]. That is suggestive, not significant (item-level p ≥ 0.5; call-level sign test p ≈ 0.04 on clustered
  calls). Both chat templates also default to thinking **on** [V]. So the harness pins every sampler value and the thinking switch
  per step kind, with presence penalty 0 for Pick and Fill [I].
- **The harder menus (`pick-hard`) pull the model families apart, though not yet significantly; they do not separate quants.** They
  are harder in 16 of 16 build × condition cells (mean −7.6 points per call). Without cards Gemma QAT was ahead of either Qwen quant
  on 5 menus to 0 (p = 0.0625, short of significance; per-call intervals +3.3 to +24.4 points, not Holm-adjusted), while UD and
  Q4_K_M differed on 0–2 menus per cell [V]. Qwen's pass^3 without cards is 0.67–0.70 in every build and runtime, below doc
  44's 0.8 bar; Gemma's is 0.77–0.83 [V].
- **Explanations and knowledge: doc 44's picture holds on the new runtime.** Knowledge without cards: 0 passes in 24 for every build.
  With cards: 3–6 passes. Explanations: 13–19 passes in 20, 0 invented-command patterns. Gemma QAT gave the same hallucinated fix
  (E10) on both runtimes [V].
- **Recommended runtime:** the managed `llama-server` sidecar that doc 13 planned. Use the Vulkan build pinned by tag and SHA-256, and
  models downloaded straight from Hugging Face by commit and SHA-256. Ollama, LM Studio or a CUDA llama.cpp build that the user
  downloads stay available as bring-your-own endpoints for speed on NVIDIA cards [I on V].
- **Default local model for 8 GB GPUs:** Gemma 4 E4B QAT, as Unsloth's `gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf` (a QAT Q4_0 file,
  4.22 GB, +2,894–3,080 MiB of GPU memory). It has the highest point estimates on Pick (tied), harder menus and Fill, none
  significantly above the other Gemma builds; it uses the least memory and is the fastest Gemma. It can be recommended only once
  its licence tag is cleared: the GGUF says `gemma`, the model card says Apache-2.0. The equal alternative is Qwen3.5-4B Q4_K_M
  (2.74 GB), which had the better explanation grades (19 vs 13 passes; 3 findings to 0 passed in both samples, p = 0.25, but Gemma
  QAT's E10 hallucination recurred on both runtimes). Do not recommend the 4-bit UD files for these two models: they showed no
  detectable gain and cost memory, speed and download [I on V].

## 1. Why llama.cpp, and exactly what ran

### 1.1 Why `llama-server` rather than Ollama

- **Any GGUF, any quant, from any Hugging Face repository.** That covers Unsloth's dynamic and plain quants, Google's and ggml-org's
  builds, and the user's own file. No registry sits in between. The run is tied to repository, commit, file, size and SHA-256, the
  artifact identity doc 14 §5 asks for [V].
- **The model's own chat template.** `--jinja` renders the Jinja template stored in the GGUF. `POST /apply-template` shows the rendered
  prompt, so the harness can check what `enable_thinking` does before any call [V].
- **Grammar-constrained output.** `response_format: {type: json_schema, json_schema: {name, schema, strict: true}}` is compiled into a
  grammar that constrains decoding, as Ollama's `format` does. Raw GBNF is available on `/completion` (doc 13 §3) [V; V per doc 13].
- **Sampler control and visibility.** `GET /props` reports the build, context, slot count and the server's default sampler. Every
  request can pin top_k, top_p, min_p and the penalties. `general.sampling.*` keys in a GGUF become the server defaults when present
  (all three Unsloth Gemma 4 E4B files set top_k 64, top_p 0.95, temperature 1.0; the Qwen3.5-4B files set none) [V].
- **Slots and a prefix cache.** Four slots with a unified KV cache by default. On Pick the prefix cache reused a median of 57–58
  prompt tokens per call [V].
- **Licence and builds.** MIT; prebuilt Vulkan (NVIDIA, AMD and Intel GPUs without CUDA libraries), Metal and CPU zips per build tag,
  each with a SHA-256 digest on GitHub. The Windows Vulkan zip is 32.1 MB [V]. CUDA builds exist upstream but are never bundled with
  our GPL builds (doc 13 §7) [V per doc 13].
- **It is the engine under Ollama anyway.** Ollama 0.34.3 serves every GGUF through a bundled upstream `llama-server` subprocess
  pinned to llama.cpp b10969 (`llm/server.go` L97–L100; `LLAMA_CPP_VERSION`). It forwards temperature, top_k, top_p, min_p, the
  penalties and the seed (`llm/llama_server.go` L1572–L1592, L2172–L2189), filling unset fields from `api/types.go` `DefaultOptions`
  (L1124–L1139) [V, source at tag v0.34.3]. What Ollama adds is a model registry, its own library builds (with vision and audio
  parts), a CUDA backend on NVIDIA, and build defaults that a caller cannot see in its own request (§2.2).
- **Ollama and LM Studio stay supported** as bring-your-own endpoints (D022 decision 1). In this spike Ollama is only the comparison
  baseline.

### 1.2 Machine and runtime [V]

| Item | Value |
| --- | --- |
| GPU | NVIDIA GeForce GTX 1070 (Pascal), 8,192 MiB, driver 582.66; 2,686–2,779 MiB already used by the desktop with no model loaded (it drifted during the day) |
| RAM, OS | 32 GB; Windows 10 Pro 22H2 (build 19045) |
| llama.cpp | Build **b11146** (commit 7fe450e19). Release v0.5.0, the latest non-pre-release, has a single asset, `nightly-tag.txt`, which contains `b11146`. The binaries are on the build tag: `llama-b11146-bin-win-vulkan-x64.zip`, 32,127,004 bytes, SHA-256 `55a378aa095b466979d85075234f66d7655c7a7483222af0c006c0e55b4d7bd6`, equal to GitHub's published digest. `llama-server --version`: `0.5.0-dev (build 11146, commit 7fe450e19)`. `--list-devices`: `Vulkan0: NVIDIA GeForce GTX 1070 (8274 MiB, 7505 MiB free)`. The newest pre-release, b11213, was not used |
| llama-bench | Vulkan, `-ngl 99`: Qwen3.5-4B UD-Q4_K_XL pp256 382 tokens/s, tg32 44.0; Q4_K_M pp256 389, tg32 47.1; all layers on the GPU |
| Ollama | 0.34.3 (doc 44's runs, plus the new harder-menu baselines); internally llama.cpp b10969; its GPU backend was not logged |
| Harness | `tools/local-qual/run.py` with the new `--backend llamacpp`; `score.py` unchanged; suites as of 2026-09-27, including the new `pick-hard` |

### 1.3 Models, fetched straight from Hugging Face [V]

| Build | Repository @ commit | File | Bytes | SHA-256 (matches the Hugging Face LFS oid) | Run |
| --- | --- | --- | --- | --- | --- |
| Qwen3.5-4B UD-Q4_K_XL | `unsloth/Qwen3.5-4B-GGUF` @ `e87f176479d0855a907a41277aca2f8ee7a09523` | `Qwen3.5-4B-UD-Q4_K_XL.gguf` | 2,912,109,728 | `b252c5610a42ca82d20fe2a12813e9d069eed89292907e26c783eeb0bc961bc7` | full |
| Qwen3.5-4B Q4_K_M | same | `Qwen3.5-4B-Q4_K_M.gguf` | 2,740,937,888 | `00fe7986ff5f6b463e62455821146049db6f9313603938a70800d1fb69ef11a4` | full, plus the Ollama-sampler arm |
| Gemma 4 E4B it QAT "UD-Q4_K_XL" | `unsloth/gemma-4-E4B-it-qat-GGUF` @ `8c5a9e4fd5482e2be20fe0bf013b4c262a8f4265` | `gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf` | 4,215,695,776 | `df0fd4ee07072c607c29a0a1cb4f98918426cca12f45a2776bdd6ee6d09a4de3` | full |
| Gemma 4 E4B it UD-Q4_K_XL | `unsloth/gemma-4-E4B-it-GGUF` @ `bfc15c382204943c3a8fff0c750b94ae2364d7a3` | `gemma-4-E4B-it-UD-Q4_K_XL.gguf` | 5,126,306,944 | `3cf61de12daa015ee0f7b68e7b7c541405bf220e1e942bad8b47cab827d7df80` | full |
| Gemma 4 E4B it Q4_K_M | same | `gemma-4-E4B-it-Q4_K_M.gguf` | 4,977,171,584 | `85a896a047553e842f25297ee5b031d64ff30147d9c4af17b1e4b394cd1fab87` | full |
| Gemma 4 E4B it QAT Q4_0 (Google) | `google/gemma-4-E4B-it-qat-q4_0-gguf` @ `4b4a2c1d584be7264f87aac328a1bc739ce81b6c` | `gemma-4-E4B_q4_0-it.gguf` | 5,154,941,280 | `676c35070db6dbe52f93e9c864ee0fba4eddea94b9c875d9cb10daff453fbaee` | resolved, not downloaded (disk space) |

- **What the repositories hold.** `unsloth/Qwen3.5-4B-GGUF` has UD-Q2_K_XL to UD-Q8_K_XL, Q4_K_M and other quants; its file sizes
  match doc 14 §3.2's figures. `unsloth/gemma-4-E4B-it-GGUF` has UD-Q4_K_XL (5.13 GB) and Q4_K_M (4.98 GB).
  `unsloth/gemma-4-E4B-it-qat-GGUF` has only UD-Q2_K_XL and UD-Q4_K_XL. Google's QAT repository has the Q4_0 file plus a 991,552,256-byte
  multimodal projector, and ggml-org publishes a 4.59 GB Q4_0. All are ungated, with Apache-2.0 model cards [V].
- **Google's file is 6.15 GB with its projector, the size of Ollama's `gemma4:e4b-it-qat` (6.1 GB).** So that file is probably the
  closest twin of Ollama's build; the hashes were not compared [I].
- **Doc 44 §1.6's open "base" question.** `Qwen/Qwen3.5-4B-Base` exists. It is a pretrained-only checkpoint, so, as doc 44 argued,
  it is not a harness candidate [V; I].
- **Pinned download.** The runner reads `sha` from `https://huggingface.co/api/models/<repo>`, then each file's `lfs.oid`
  (SHA-256) and `lfs.size` from the tree at that commit. It downloads `https://huggingface.co/<repo>/resolve/<commit>/<file>` to a
  `.part` file with HTTP Range resume, checks the size and SHA-256, and renames the file atomically. Throughput was 35–37 MB/s. A
  local manifest records repo, revision, file, size, SHA-256 and `verified` [V].
- **The `-hf` route** was checked with a 338 MB test model (`unsloth/Qwen3.5-0.8B-GGUF:UD-IQ2_XXS`, deleted afterwards).
  `llama-server -hf <user>/<repo>:<quant>` wrote `LLAMA_CACHE/models--<user>--<repo>/{refs/main, snapshots/<commit>/<file>}` in the
  Hugging Face cache layout. The file's SHA-256 matched, and an `--offline` restart reused it in 2.6 s. But `-hf` has no revision
  flag, so it follows `main`. With an empty cache, `-hf --offline` fails without naming the path it looked in [V].
- **Disk.** The five candidate files need about 20 GB. The system drive had 20.7 GB free, so the two non-QAT Gemma files went to a
  second drive, and Google's file was not fetched [V].

### 1.4 How they ran [V]

- **Server:** `llama-server -m <file> --jinja -ngl 99 -c 8192 --host 127.0.0.1 --port <free port>`, started hidden, with `/health`
  polled until ready. Defaults: 4 slots, a unified KV cache and the prefix cache. One model per server. Before each load, `ollama stop`
  unloaded any Ollama model; after the last job the server was stopped and the card returned to the desktop baseline.
- **Runner:** `python tools/local-qual/run.py --backend llamacpp --base-url http://127.0.0.1:<port> --suite <s> --condition <c>
  --k <k> --warmup` plus the sampler pins below. `--warmup` sends one unrecorded call first. Long jobs ran in chunks with `--resume`.
- **Request:** `/v1/chat/completions`, `stream: false`. Pick, Fill, explain and text send the item's schema as `response_format`
  json_schema (strict); knowledge is plain text. Temperature 0.6 (pick, fill, text) or 0.2 (explain, knowledge); seed per (item,
  sample); output caps as in doc 44; `chat_template_kwargs: {enable_thinking: false}`. Records keep `score.py`'s field names, so the
  scorer ran unchanged.
- **Sampler, per model family:** Qwen `--top-k 20 --top-p 0.95 --min-p 0` (the Ollama build's values without its presence
  penalty); Gemma `--top-k 64 --top-p 0.95 --min-p 0` (the Ollama build's values). The **Ollama-sampler arm** re-ran Qwen Q4_K_M on
  Pick and harder menus with `--presence-penalty 1.5 --repeat-penalty 1.0` added. That reproduces what Ollama's build sends: the other
  fields' server defaults equal Ollama's `DefaultOptions`, and Ollama passes no sampler order.
- **Thinking.** In `llama-server` both templates default to thinking on: Qwen3.5 opens a `<think>` block, and Gemma 4 adds a think
  turn. `enable_thinking: false` changes the rendered prompt for both, and every record came back with 0 thinking characters.
- **Jobs:** doc 44's seven jobs (304 calls) plus `pick-hard` none and cards at k = 3 (180 calls), so 484 calls per full build. The
  Ollama-sampler arm made 360 calls. The Ollama baselines are doc 44's 304-call records plus new `pick-hard` runs (180 calls each)
  on the same Ollama 0.34.3 with the build defaults, as in doc 44.
- **Totals:** `score.py` scored 81 raw files and 4,356 records: 3,140 new ones plus doc 44's 1,216. There were 0 HTTP errors, 0 parse
  failures, 0 stale suite hashes, 0 thinking characters and 0 duplicate (item, sample) records, and 0 truncations among the new
  records (the only one of the 4,356 is doc 44's Ministral knowledge answer at the 700-token cap). Three `pick-hard/cards`
  jobs hit the chunk time budget and were resumed; each raw file holds exactly the expected records.

### 1.5 What is inside each GGUF [V]

GGUF headers, bytes per tensor type (from the tensor offsets):

| File | Tensor data | Q4_K / Q4_0 | Q5_K | Q6_K | Q8_0 | Other | Metadata notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen3.5-4B Q4_K_M | 2,603.5 MiB | Q4_K 49.9% | 19.0% | 30.8% | 0.2% | F32 0.1% | file type 15; imatrix `unsloth_calibration_Qwen3.5-4B.txt` (80 chunks); licence apache-2.0 |
| Qwen3.5-4B UD-Q4_K_XL | 2,766.7 MiB | Q4_K 29.5% | 28.0% | 28.6% | 9.2% | IQ4_XS 4.3%, F16 0.3%, F32 0.1% | file type **15** (same); the same imatrix |
| Gemma 4 E4B QAT "UD-Q4_K_XL" | 4,005.3 MiB | **Q4_0 99.95%** | — | — | — | F32 0.05% | file type 2 (Q4_0); name "smart Q4_0, QAT-lossless"; **licence `gemma`**; 666 tensors |
| Gemma 4 E4B Q4_K_M | 4,731.5 MiB | Q4_K 45.8% | 39.1% (one tensor) | 9.6% | — | F32 4.5%, BF16 1.1% | file type 15; imatrix (141 chunks); licence apache-2.0; 720 tensors |
| Gemma 4 E4B UD-Q4_K_XL | 4,873.7 MiB | Q4_K 31.9% | 52.7% | 10.1% | — | F32 4.4%, BF16 1.1% | file type 15; the same imatrix; licence apache-2.0 |

- **What "UD" changes here.** For Qwen, UD moves about 480 MiB of weights from Q4_K to Q5_K, Q8_0 and IQ4_XS: 6% more data. Both
  Unsloth files carry the same importance-matrix calibration, so the comparison isolates the per-tensor precision choice [V].
- **The QAT "UD" file is not a dynamic mix.** It is uniform Q4_0, consistent with a QAT checkpoint trained for Q4_0 [V; I].
- **Gemma's biggest tensor** is `per_layer_token_embd` (1,512 MiB as Q4_0 in the QAT file, 1,848 MiB as Q5_K in the others). The
  memory arithmetic in §2.6 suggests it stays in system RAM [I].
- **Chat templates.** The three Gemma files carry the same chat template (18,808 characters, identical by hash) [V].

## 2. Results

Pick menus are paired across builds: the seeds and option shuffles depend only on (item, sample), and every comparison checked that
both arms saw the same letter order. Tests: exact McNemar on menus right by majority in only one arm, and a paired item bootstrap
(10,000 resamples) for the per-call accuracy difference, Holm-adjusted within each family (§3).

### 2.1 Runtime: the same model on Ollama and llama.cpp [V]

The Qwen pair is the same model and quant name but **not the same file**. Ollama's library build is 3.4 GB with vision parts and
an unknown quantisation recipe [U]; Unsloth's Q4_K_M is 2.74 GB and imatrix-calibrated. The Gemma pair differs in quant, Ollama's
QAT Q4_0 against Unsloth's QAT "smart Q4_0", so it is the closest pair available, not a twin. Both runtimes produced **the same prompt
token counts** on every Pick and harder-menu call of both pairs (720 of 720) and on every Qwen Fill call (36 of 36), so the Jinja
template and Ollama's renderer agree.

| Suite / condition | Qwen: Ollama | Qwen: llama.cpp | Qwen: llama.cpp, Ollama's sampler | Gemma: Ollama QAT Q4_0 | Gemma: llama.cpp QAT UD |
| --- | --- | --- | --- | --- | --- |
| Pick none: acc / pass^3 | 0.900 / 0.833 | 0.933 / 0.867 | 0.933 / 0.833 | 0.956 / 0.933 | 0.967 / 0.967 |
| Pick cards | 0.933 / 0.867 | 0.967 / 0.967 | 0.944 / 0.900 | 0.956 / 0.933 | 0.967 / 0.967 |
| Harder none | 0.811 / 0.700 | 0.822 / 0.700 | 0.800 / 0.667 | 0.900 / 0.767 | 0.944 / 0.833 |
| Harder cards | 0.867 / 0.767 | 0.867 / 0.767 | 0.822 / 0.733 | 0.900 / 0.800 | 0.922 / 0.867 |
| Fill: fields / all fields per call / all fields pass^3 | 0.833 / 0.472 / 3 of 12 | 0.893 / 0.639 / 7 of 12 | — | 0.923 / 0.639 / 7 of 12 | 0.970 / 0.861 / 9 of 12 |
| Fill validators, all pass | 0.750 | 0.861 | — | 0.972 | 0.972 |
| Text code checks | 0.90 | 1.00 | — | 1.00 | 0.95 |

**Paired tests, llama.cpp minus Ollama** (menus right by majority only on llama.cpp : only on Ollama; McNemar p; per-call 95% interval):

| Pair | Pick none | Pick cards | Harder none | Harder cards |
| --- | --- | --- | --- | --- |
| Qwen, llama.cpp sampler | 2:0, p 0.5, −2.2 to +11.1 | 0:0, p 1.0, 0 to +7.8 | 2:1, p 1.0, −5.6 to +8.9 | 2:3, p 1.0, −6.7 to +7.8 |
| Qwen, Ollama's sampler | 2:0, p 0.5, 0 to +8.9 | 0:0, p 1.0, −2.2 to +4.4 | 3:1, p 0.625, −8.9 to +5.6 | 0:3, p 0.25, −10 to 0 |
| Gemma QAT | 0:0, p 1.0, 0 to +3.3 | 0:0, p 1.0, 0 to +3.3 | 2:0, p 0.5, +1.1 to +8.9 | 1:1, p 1.0, −2.2 to +6.7 |

- **No detectable accuracy difference on Pick at this n.** None of the 16 comparisons is significant (Holm-adjusted p = 1.0 for all);
  the four not shown, Qwen UD on llama.cpp against Ollama, give 0:0 to 3:2 menus and p = 1.0. The one interval that excludes 0
  (Gemma, harder none) rests on 2 menus to 0 and on a quant difference.
- **Letter-level agreement.** With the sampler matched, Qwen on llama.cpp chose the same letter as Ollama in 86 of 90 (none) and 87 of
  90 (cards) Pick calls; with llama.cpp's default sampler, 84 and 87. The remaining 7 of 180 differences come from the runtime (build
  b10969 vs b11146, GPU backend, slot layout, attention kernels) and the weight files [I].
- **Fill leans one way, cause unknown.** All fields right per call: llama.cpp minus Ollama +0.167 for Qwen (bootstrap +0.028 to
  +0.306) and +0.222 for Gemma QAT (+0.056 to +0.417). The non-QAT Gemma builds also beat Ollama's Gemma (+0.167 to +0.194). By
  majority only 2–3 of 12 records differ, all in llama.cpp's favour (McNemar p 0.25–0.5). This is suggestive, not significant [V].
  Possible causes: the weight files, Ollama's presence penalty for Qwen, and JSON whitespace under the grammar. Gemma pretty-prints on
  llama.cpp: 70.6 output tokens per fill vs 44.3 on Ollama. None of these is tested [U].
- **Explanations, text and knowledge** (graded, §2.5): the same verdicts as doc 44 on both runtimes. Gemma QAT's explain grades were
  13 pass / 7 partial / 0 fail with 2 hallucinated fixes on **both** runtimes, the same invented one-line syntax for E10.

### 2.2 Hidden sampler defaults: the presence-penalty effect [V; I]

Ollama's `qwen3.5:4b-q4_K_M` build sets `presence_penalty 1.5` (doc 44 §1.2). Adding exactly that on llama.cpp, with everything
else fixed:

| Qwen3.5-4B Q4_K_M, llama.cpp | Pick none | Pick cards | Harder none | Harder cards | Total |
| --- | --- | --- | --- | --- | --- |
| Default sampler (no penalty): right calls | 84 / 90 | 87 / 90 | 74 / 90 | 78 / 90 | 323 / 360 |
| Ollama's sampler (presence 1.5): right calls | 84 / 90 | 85 / 90 | 72 / 90 | 74 / 90 | 315 / 360 |
| Menus right by majority only with the penalty : only without | 0:0 | 0:0 | 1:0 | 0:2 (p 0.5) | — |

- **Size of the effect.** 12 calls were right under only one sampler: 2 favoured the penalty and 10 did not (exact sign test p ≈ 0.04).
  Calls on one menu are correlated, so the item-level tests (all p ≥ 0.5; Holm 1.0) are the honest ones: the effect is suggestive,
  not established at this n [V]. Against Ollama's 316 of 360, the default arm got 323 and the penalty arm 315, so on these point
  estimates the penalty alone is about as large as the whole runtime difference on Pick; neither difference is significant [V].
- **Mechanism, verified in the source.** At each request `llama-server` feeds every prompt token into the sampler chain
  (`tools/server/server-context.cpp` L409–L431, `init_sampler`, calling `common_sampler_accept`; `common/sampling.cpp` L496). So
  the penalty's 64-token window (`repeat_last_n`, Ollama's default) holds the **end of the prompt**: the last menu options, the `X)`
  line and the reply instruction. A presence penalty subtracts its value from the logit of every token in that window
  (`src/llama-sampler.cpp` L2976). The code is the same in b10969 (Ollama's) and b11146 [V].
- **The observed pattern fits.** On the harder menus, all 7 calls lost under the penalty had their answer at `G` or `X`, the last two
  letters of a 7-option menu. `G` was chosen 9 times vs 13 (none) and 12 vs 16 (cards) [V]. The causal link to accuracy is our
  reading [I]. **Doc 44's Ollama Qwen numbers may therefore carry a small bias against end-of-menu answers** [I].
- **Speed.** The penalty sampler is skipped only when every penalty is neutral (`src/llama-sampler.cpp` L2885–L2891, `is_disabled`);
  otherwise it runs over the whole vocabulary for each token. Generation fell from 48.7 to 45.2 tokens/s on Pick [V].
- **Rule for the harness** [I]: pin `presence_penalty 0`, `frequency_penalty 0` and `repeat_penalty 1` (or `repeat_last_n 0`) for
  Pick and Fill on every backend. Record the effective sampler from `/props` or the runtime, as doc 13 §3 already asks. Treat any
  build default as unknown until read.

### 2.3 Quant: UD-Q4_K_XL vs Q4_K_M on the same runtime [V]

Same repository commit, llama.cpp build, flags, sampler, seeds and option order; only the file differs.

| Suite / condition | Qwen UD | Qwen Q4_K_M | Menus UD-only : Q4-only, p; per-call 95% interval (UD − Q4) | Gemma UD | Gemma Q4_K_M | Menus, p; interval |
| --- | --- | --- | --- | --- | --- | --- |
| Pick none: acc / pass^3 / majority | 0.922 / 0.867 / 0.933 | 0.933 / 0.867 / 0.967 | 0:1 (PW05), p 1.0; −6.7 to +3.3 | 0.967 / 0.967 / 0.967 | 0.967 / 0.967 / 0.967 | 0:0, p 1.0; 0 to 0 |
| Pick cards | 0.967 / 0.967 / 0.967 | 0.967 / 0.967 / 0.967 | 0:0, p 1.0; 0 to 0 | 0.967 / 0.967 / 0.967 | 0.967 / 0.967 / 0.967 | 0:0, p 1.0; 0 to 0 |
| Harder none | 0.811 / 0.700 / 0.833 | 0.822 / 0.700 / 0.833 | 1:1, p 1.0; −6.7 to +4.4 | 0.911 / 0.833 / 0.933 | 0.900 / 0.800 / 0.933 | 0:0, p 1.0; 0 to +3.3 |
| Harder cards | 0.900 / 0.833 / 0.900 | 0.867 / 0.767 / 0.867 | 1:0 (HW04), p 1.0; 0 to +7.8 | 0.900 / 0.833 / 0.900 | 0.911 / 0.833 / 0.933 | 0:1 (HV02), p 1.0; −6.7 to +3.3 |
| Fill: fields / all fields per call / pass^3 | 0.899 / 0.583 / 5 of 12 | 0.893 / 0.639 / 7 of 12 | 0:0 records; all-fields interval −16.7 to +5.6 | 0.964 / 0.833 / 9 of 12 | 0.958 / 0.806 / 9 of 12 | 1:0 (F08), p 1.0; 0 to +8.3 |
| Text code checks | 1.00 | 1.00 | — | 1.00 | 0.95 | one miss, "East wind" read as a name (checker false positive [I]) |
| Explain graded pass / partial (pass both, of 10) | 15 / 5 (7) | 19 / 1 (9) | separate grader passes | 18 / 2 (9) | 17 / 3 (8) | separate grader passes |
| Knowledge with cards: pass / partial / fail | 6 / 2 / 16 | 3 / 7 / 14 | separate grader passes | 6 / 9 / 9 | 6 / 7 / 11 | separate grader passes |

| Cost of UD | Qwen UD vs Q4_K_M | Gemma UD vs Q4_K_M |
| --- | --- | --- |
| Download | 2.91 vs 2.74 GB (+171 MB, +6.2%) | 5.13 vs 4.98 GB (+149 MB, +3.0%) |
| GPU memory added at load / at peak | 3,331 vs 3,167 MiB (+164) / 3,383 vs 3,193 (+190) | 3,416 vs 3,273 (+143) / 3,455 vs 3,298 (+157) |
| Generation, Pick | 45.4 vs 48.7 tokens/s (−7%) | 39.0 vs 42.5 tokens/s (−8%) |
| Warm Pick p50 (pooled) | 1,079 vs 1,046 ms | 1,412 vs 1,341 ms |

- **Answer to "test the UD quant":** no detectable difference at this n on any code-scored suite, for either model. Graded suites
  cannot separate them either: each build was graded in its own pass, and the Qwen explain gap (7 vs 9 findings passed in both
  samples) is 2 findings, E01 and E04 (paired p = 0.5) [V].
- **What the data can and cannot show.** Every per-call interval lies within −6.7 to +7.8 points, which makes a quant effect larger
  than about 8 points per call unlikely on these instruments. Percentile intervals built from so few discordant menus are optimistic,
  so read that bound as indicative [V; I]. Smaller effects are out of reach: McNemar needs at least 6 discordant menus all going one
  way to reach p < 0.05, and UD vs Q4_K_M produced 0–2 per cell (4 of 120 menu-cells for Qwen, 1 of 120 for Gemma) [V]. Detecting a
  3:1 split of discordant menus with 80% power needs about 30 of them (exact binomial test; 29 by the normal approximation), which at
  those rates means roughly 900 (Qwen) to 3,600 (Gemma) menus per condition [I, arithmetic].
- **Verdicts at the bar are fragile.** Qwen's harder-menu pass^3 with cards is 0.833 for UD and 0.767 for Q4_K_M, either side of the
  0.8 bar, and the gap is one menu (HW04, a CYCLE waypoint). A badge must not rest on one menu (§4.1) [I].
- **Also compared:** Gemma QAT against non-QAT, both called "UD-Q4_K_XL". QAT was ahead on the harder menus without cards, by 2 menus
  to 0 (HT03, HV01; p = 0.5; per-call interval −3.3 to +12.2). On `pick` the two were identical; on the harder menus with cards they
  split 1:1 (HV02, HW04), and Fill split 1:1 by record. QAT is also smaller (4.22 vs 5.13 GB), leaner (−522 MiB at load) and faster
  (45.0 vs 39.0 tokens/s) [V].

### 2.4 The harder menu suite: does it separate them? [V]

`pick-hard` (30 menus, always 7 options plus `X`, near-miss distractors, 3 planted escapes; README) against `pick` (30 menus, 4–7
options):

| Build (runtime) | Pick-hard none: acc / pass^3 / majority | Cards | Escapes right (of 9), none / cards |
| --- | --- | --- | --- |
| Qwen3.5-4B Q4_K_M (Ollama) | 0.811 / 0.700 / 0.800 | 0.867 / 0.767 / 0.900 | 7 / 7 |
| Qwen3.5-4B Q4_K_M (llama.cpp) | 0.822 / 0.700 / 0.833 | 0.867 / 0.767 / 0.867 | 8 / 7 |
| Qwen3.5-4B Q4_K_M (llama.cpp, Ollama's sampler) | 0.800 / 0.667 / 0.867 | 0.822 / 0.733 / 0.800 | 8 / 6 |
| Qwen3.5-4B UD-Q4_K_XL (llama.cpp) | 0.811 / 0.700 / 0.833 | 0.900 / 0.833 / 0.900 | 8 / 7 |
| Gemma 4 E4B QAT Q4_0 (Ollama) | 0.900 / 0.767 / 0.933 | 0.900 / 0.800 / 0.900 | 8 / 9 |
| Gemma 4 E4B QAT UD-Q4_K_XL (llama.cpp) | 0.944 / 0.833 / 1.000 | 0.922 / 0.867 / 0.900 | 8 / 9 |
| Gemma 4 E4B UD-Q4_K_XL (llama.cpp) | 0.911 / 0.833 / 0.933 | 0.900 / 0.833 / 0.900 | 9 / 9 |
| Gemma 4 E4B Q4_K_M (llama.cpp) | 0.900 / 0.800 / 0.933 | 0.911 / 0.833 / 0.933 | 9 / 9 |

Random valid option: 0.143 (1/7), against 0.191 for `pick`. No build chose `X` on a menu that had a fitting option (0 false
escapes in 16 cells).

- **Harder, as intended.** Per-call accuracy is lower than on `pick` in 16 of 16 build × condition cells, by 7.6 points on average.
  The cells share models and items, so this is descriptive; no single cell is significant (Fisher exact on majority, p 0.10–1.0) [V].
- **It pulls model families apart, though not yet significantly.** Paired on the same menus:

  | Pair (same runtime) | Pick none | Pick-hard none | Pick-hard cards |
  | --- | --- | --- | --- |
  | Gemma QAT UD vs Qwen UD (llama.cpp) | 1:0, p 1.0 | **5:0, p 0.0625; +4.4 to +24.4** | 2:2, p 1.0 |
  | Gemma QAT UD vs Qwen Q4_K_M (llama.cpp) | 0:0 | **5:0, p 0.0625; +3.3 to +22.2** | 2:1, p 1.0 |
  | Gemma Q4_K_M vs Qwen Q4_K_M (llama.cpp) | 0:0 | 3:0, p 0.25 | 3:1, p 0.625 |
  | Gemma vs Qwen (Ollama) | 2:0, p 0.5 | 5:1, p 0.22 | 1:1, p 1.0 |

  Without cards, `pick-hard` produces about six times as many discordant menus between the families as `pick` (19 against 3), all
  but one in Gemma's favour. That is still short of significance at 30 menus: 5:0 gives p = 0.0625, and 6:0 would be the first
  one-way split under 0.05. The per-call intervals do exclude 0 (extra family, not Holm-adjusted) [V].
- **It does not separate quants** (§2.3: 0–2 discordant menus per cell) or runtimes (§2.1) [V].
- **Where builds fail.** HW04 (a CYCLE placed at the right waypoint), HT03 ("Both End #1") and HV01 (a per-turn roll) failed pass^3 in
  15 of 16 cells, HW03 (SENTRY) in 13 and HM04 (a planted escape, vehicle respawn) in 10. Replayability (2 menus) and trigger semantics
  are the weakest categories for Qwen; Gemma's weak spots are waypoints and replayability [V]. These are fact-bearing menus, so doc
  44's rule applies: code filters by the facts it knows, and the model picks among what remains [I].
- **Qwen misses the bar here.** Pass^3 without cards is 0.667–0.700 for every Qwen build on both runtimes, below doc 44's 0.8 bar.
  With cards it is 0.733–0.833. Gemma is at 0.767–0.833 without cards and 0.800–0.867 with them. Qwen also catches fewer planted
  escapes: 6–8 of 9, against 8–9 for Gemma [V].
- **PW04 still fails everywhere.** The TR UNLOAD menu from doc 44 was answered right in 1 of 36 samples across the llama.cpp builds;
  all 35 misses chose UNLOAD [V].

### 2.5 Fill, explanations, text and knowledge [V]

| Build (runtime) | Fill all fields: per call / pass^3 | Fill `size` | Explain pass / partial / fail (H) · pass both of 10 | Text quality pass / partial / fail · both of 10 | Knowledge none: pass (H of 24) | Knowledge cards: pass / partial / fail (H) · both of 12 |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen Q4_K_M (Ollama, doc 44) | 0.472 / 3 of 12 | 0.54 | 20 / 0 / 0 (0) · 10 | 7 / 11 / 2 · 2 | 0 (24) | 6 / 9 / 9 (6) · 3 |
| Qwen Q4_K_M (llama.cpp) | 0.639 / 7 of 12 | 0.67 | 19 / 1 / 0 (0) · 9 | 4 / 15 / 1 · 1 | 0 (24) | 3 / 7 / 14 (13) · 1 |
| Qwen UD-Q4_K_XL (llama.cpp) | 0.583 / 5 of 12 | 0.67 | 15 / 5 / 0 (0) · 7 | 6 / 12 / 2 · 2 | 0 (24) | 6 / 2 / 16 (9) · 2 |
| Gemma QAT Q4_0 (Ollama, doc 44) | 0.639 / 7 of 12 | 0.67 | 13 / 7 / 0 (2) · 5 | 5 / 15 / 0 · 2 | 0 (22) | 6 / 8 / 10 (10) · 3 |
| Gemma QAT UD (llama.cpp) | 0.861 / 9 of 12 | 0.79 | 13 / 7 / 0 (2) · 6 | 3 / 16 / 1 · 0 | 0 (23) | 6 / 8 / 10 (8) · 3 |
| Gemma UD-Q4_K_XL (llama.cpp) | 0.833 / 9 of 12 | 0.75 | 18 / 2 / 0 (0) · 9 | 4 / 15 / 1 · 2 | 0 (23) | 6 / 9 / 9 (9) · 3 |
| Gemma Q4_K_M (llama.cpp) | 0.806 / 9 of 12 | 0.71 | 17 / 3 / 0 (0) · 8 | 1 / 17 / 2 · 0 | 0 (21) | 6 / 7 / 11 (9) · 3 |

- **Fill.** Whole-record pass^3 stays below 0.8 for every build (best 9 of 12 = 0.75), so doc 44's verdict stands: the record is a
  pre-fill, and only closed fields qualify. `size` is still the weakest field everywhere (0.54–0.79). Every Gemma build on llama.cpp
  got `task`, `place`, `side`, `time_of_day`, `archetype` and `target` right in every call; for Qwen, `target` was 0.67–0.83 and
  `task` 0.75–0.79 [V].
- **Knowledge.** Without cards no build passed any of its 24 answers (one partial in total), with 21–24 hallucinations each. With
  cards: 3–6 passes. T04, T06 and T12 failed in every build, as in doc 44. Doc 44's rule is unchanged: a local model never answers a
  free-text engine question [V; I].
- **Explanations.** No explanation failed outright, and `score.py` found 0 invented-command patterns in any of the 100 llama.cpp
  answers. Gemma QAT's two hallucinations are the same E10 fix as on Ollama. The non-QAT Gemma builds did not produce it (18 and 17
  passes) [V].
- **Text.** Code constraints held in 95–100% of lines on llama.cpp. Graded quality stays low (1–6 passes of 20 on llama.cpp, 5–7 on
  Ollama), so lines remain candidates the user picks from (doc 44 §2.4) [V].
- **Grader caveat.** Each build was graded in its own single LLM pass, with no calibration across passes. The QAT build's grader was
  checked against doc 44's Gemma grades: identical answers got identical verdicts. Differences of a few grades between builds, such
  as Qwen Q4_K_M's 13 knowledge-card hallucinations against 6 on Ollama, are within grader variation and are not interpreted [V; I].

### 2.6 Latency, tokens/s, load and GPU memory [V]

**Warm latency** (every call after a warm-up call; no call reported a model load over 100 ms), p50 in ms, conditions pooled:

| Build (runtime) | Pick p50 / p90 | Pick-hard p50 / p90 | Fill | Explain | Text | Knowledge | Pick: prompt eval / generation p50 | Generation tokens/s (Pick) | Prompt tokens/s (Pick, uncached) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen Q4_K_M (Ollama) | 700 / 797 | 772 / 946 | 1,541 | 2,446 | 673 | 2,805 | 450 / 168 | 40.4 | 624 |
| Qwen Q4_K_M (llama.cpp) | 1,046 / 1,216 | 1,212 / 1,554 | 2,051 | 2,530 | 806 | 2,197 | 820 / 144 | 48.7 | 253 |
| Qwen Q4_K_M (llama.cpp, Ollama's sampler) | 1,074 / 1,228 | 1,259 / 1,751 | — | — | — | — | 827 / 152 | 45.2 | 250 |
| Qwen UD-Q4_K_XL (llama.cpp) | 1,079 / 1,252 | 1,248 / 1,592 | 2,089 | 2,625 | 776 | 2,375 | 835 / 153 | 45.4 | 247 |
| Gemma QAT Q4_0 (Ollama) | 590 / 689 | 690 / 855 | 1,470 | 2,310 | 651 | 1,739 | 404 / 154 | 45.4 | 687 |
| Gemma QAT UD (llama.cpp) | 1,126 / 1,320 | 1,310 / 1,576 | 2,223 | 2,555 | 891 | 1,969 | 727 / 352 | 45.0 | 276 |
| Gemma UD-Q4_K_XL (llama.cpp) | 1,412 / 1,642 | 1,648 / 1,999 | 2,496 | 2,980 | 1,085 | 2,375 | 941 / 431 | 39.0 | 215 |
| Gemma Q4_K_M (llama.cpp) | 1,341 / 1,563 | 1,557 / 1,918 | 2,383 | 2,762 | 1,001 | 2,119 | 908 / 399 | 42.5 | 225 |

- **The gap is mostly prompt processing.** A pick's wall time is mostly the uncached prompt: 215–337 tokens/s on llama.cpp's Vulkan
  build, with prefix-cache hits excluded, against 620–710 on Ollama (Pick and harder menus; the table's Pick column is 215–276 against
  624–687; summed tokens over summed time). `llama-bench` measured 382–389 tokens/s at pp256, so short, partly cached prompts run
  below the benchmark figure. Ollama's rate may count cached tokens too, so compare the end-to-end p50s, not the rates. For Qwen the
  prompt-eval gap (820 vs 450 ms) exceeds the whole p50 gap; for Gemma QAT it is about 320 of 536 ms, and the rest is generation
  (next bullets) [V; I].
- **Generation is not the problem.** llama.cpp generates as fast or faster: Qwen 48.7 vs 40.4 tokens/s, Gemma QAT 45.0 vs 45.4. On
  long outputs the runtimes converge (explain within 0.08–0.25 s) [V].
- **Gemma pretty-prints JSON under llama-server's grammar.** A pick comes back as `{`, newline, indented `"choice": "B"`, newline, `}`:
  16 output tokens against 7 on Ollama and 7 for Qwen on either runtime. Generation takes 352 vs 154 ms per pick; on Fill it is
  70.6 vs 44.3 tokens [V]. A whitespace-free grammar or a compact-JSON instruction should recover about 200 ms per Gemma pick
  (untested) [I].
- **Still interactive.** A Pick with k = 3 sequential samples takes about 3.1–3.4 s on llama.cpp against 1.8–2.1 s on Ollama here
  [I, arithmetic from the p50s]. One job, Qwen with Ollama's sampler on `pick-hard/cards`, briefly slowed to 35.2 tokens/s, probably
  because another process used the GPU; its scores are unaffected [V; I].
- **Battery wall time.** Doc 44's 304-call battery took 463–556 s per build on llama.cpp against 316 s (Gemma) and 430 s (Qwen) on
  Ollama. The full 484-call list took 688–860 s [V].

**Load and GPU memory** (whole-card `nvidia-smi` MiB, desktop included, context 8192; llama.cpp and the Ollama harder-menu sessions
sampled every 2 s):

| Build (runtime) | File | Baseline before load | After load (added) | Peak total (added) | Free at peak, of 8,192 | Start to `/health` | Warm-up call |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen UD-Q4_K_XL (llama.cpp) | 2.91 GB | 2,686 | 6,017 (+3,331) | 6,069 (+3,383) | 2,123 | 4.8 s | 1.29 / 1.45 s |
| Qwen Q4_K_M (llama.cpp) | 2.74 GB | 2,692 | 5,859 (+3,167) | 5,885 (+3,193) | 2,307 | 4.2 s | 1.22 s |
| Qwen Q4_K_M (llama.cpp, Ollama's sampler) | same | 2,702 | 5,859 (+3,157) | 5,911 (+3,209) | 2,281 | 4.7 s | 1.29 s |
| Gemma QAT UD (llama.cpp) | 4.22 GB | 2,694 | 5,588 (+2,894) | 5,774 (+3,080) | 2,418 | 8.8 s | 1.03 s |
| Gemma UD-Q4_K_XL (llama.cpp) | 5.13 GB | 2,778 | 6,194 (+3,416) | 6,233 (+3,455) | 1,959 | 7.3 s | 5.54 s |
| Gemma Q4_K_M (llama.cpp) | 4.98 GB | 2,779 | 6,052 (+3,273) | 6,077 (+3,298) | 2,115 | 5.8 s | 0.95 s |
| Qwen Q4_K_M (Ollama) | 3.4 GB | 2,779 | — | 6,831 (+4,052) | 1,361 | — | 12.2 s incl. load |
| Gemma QAT Q4_0 (Ollama) | 6.1 GB | 2,779 | — | 7,140 (+4,361) | 1,052 | — | 12.8 s incl. load |

- **llama.cpp saves 859 MiB on Qwen and 1,281 MiB on Gemma** at peak, against the Ollama library builds [V]. Those builds include
  vision (and, for Gemma, audio) parts that a text-only GGUF does not load [I].
- **GPU memory follows the tensor bytes that live on the GPU.** Between two quants of one model, the load-time difference equals the
  tensor-data difference to within about 11 MiB, once Gemma's per-layer embedding table is left out:
  - Qwen UD vs Q4_K_M: +163 MiB of data, +164 MiB of GPU memory.
  - Gemma UD vs Q4_K_M: +142 MiB of data, +143 MiB.
  - Gemma Q4_K_M vs QAT: +726 MiB of data, of which 336 MiB is the per-layer embedding table; the other +390 MiB compares with +379 MiB
    of GPU memory.

  So the per-layer table (1,512–1,848 MiB) most likely stays in system RAM, and a new quant's fit can be predicted from a measured sibling
  plus the tensor-byte difference. Host RAM was not measured [V arithmetic; I].
- **Start-up.** `llama-server` reached `/health` 4.2–8.8 s after start with the file already in the OS cache. The first call then took
  0.95–1.45 s, except 5.5 s for Gemma UD, probably while the GPU driver compiled pipelines for the Q4_K kernels [V; I]. The very first
  call with a new llama.cpp build spent 12.9 s on prompt processing, and later first calls 1.3–3.8 s, which suggests a shader cache
  (smoke test; not proven) [V; I]. Ollama's first call in the harder-menu sessions took 12.2 and 12.8 s including the load. Doc 44
  logged warm loads of 5.9 s (Qwen) and 13.2 s (Gemma). These are not controlled comparisons [V].

## 3. Significance and limits

- **Tests used.** Menus are the unit: majority of k = 3, a tie counts as wrong. Exact two-sided McNemar on discordant menus; a paired
  item bootstrap (10,000 resamples, seed fixed, percentile 95%) for the per-call difference; Holm adjustment within each family
  (quant 16 tests, runtime 16, sampler 4, cards vs none 18, pick vs pick-hard 16, Fill 9). Pick vs pick-hard uses different menus,
  so it is unpaired: Fisher exact on majority, bootstrap per suite. The Gemma-vs-Qwen family (16 tests) was added for this doc and is
  not adjusted. A percentile interval collapses to [0, 0] when no menu differs; read that as "no discordance", not as certainty [V].
- **Small n.** 30 menus per Pick suite and condition, 12 Fill records, 10 findings, 10 text slots and 12 knowledge tasks, at k = 2–3.
  At 30 menus, only effects of about 6 or more discordant menus in one direction can reach p < 0.05. "No detectable difference" here
  means that, not equivalence (§2.3). Cards vs none: all 18 comparisons have Holm p = 1.0; the largest is Qwen UD on the harder menus,
  +8.9 points per call (+1.1 to +18.9; McNemar 3:1, p = 0.625) [V].
- **One machine, one GPU backend per runtime.** One GTX 1070 (Pascal) on Windows 10; llama.cpp only through its Vulkan build; Ollama's
  backend not logged. The latency conclusions are about Vulkan on Pascal. A newer GPU, an AMD or Intel GPU, a CUDA build of llama.cpp,
  or another Vulkan driver can change them [I].
- **Not one variable at a time between runtimes.** Ollama vs llama.cpp also changes the llama.cpp build (b10969 vs b11146), the weight
  file (Ollama library build vs Unsloth), the slot and context layout and, unless matched, the sampler. §2.1 is a comparison of
  the product paths as a user would meet them, not of runtimes in isolation. The runtime-only Gemma twin (Google's QAT Q4_0 GGUF on
  llama.cpp) was not run [V; I].
- **Sampler parity.** The Qwen default arm leaves out Ollama's presence penalty on purpose; the matched arm covers only Pick and harder
  menus. Fill, explain, text and knowledge were not re-run with the penalty, so the Fill runtime gap is still confounded for Qwen [V].
- **Graders.** One LLM grader pass per build, with no human adjudication and no calibration across passes, except the QAT check
  against doc 44. Graded differences between builds are not interpreted [V].
- **Sessions and drift.** The Ollama harder-menu baselines ran in a later session than doc 44's Ollama records, on the same Ollama
  0.34.3. The desktop's GPU use drifted between 2,686 and 2,779 MiB, and "added" figures use each session's own pre-load reading.
  The Qwen UD run finished on a second server start whose pre-load reading was not saved, so the first start's baseline is used. One
  job ran slower, probably because another process used the GPU [V; I].
- **Prefix cache.** `llama-server` reuses shared prompt prefixes between calls. That saves time and may shift numerics slightly; the
  seeds make runs repeatable only on the same build, backend and machine [I].
- **Tooling caveat.** On a case-insensitive file system (Windows), `run.py`'s default output names for an Ollama tag
  (`qwen3.5-4b-q4_K_M`) and a llama.cpp file label (`Qwen3.5-4B-Q4_K_M`) are the same file, so both runtimes append to it.
  `run.py --resume` and `score.py` key on each record's exact model label, so they keep the two apart, but anything that counts
  records per file does not: this run's own driver counted that way, caught the collision before any data was mixed, and gave the
  Ollama runs their own file names. Use `--out` with a directory per runtime [V].
- **Synthetic instruments written by us.** `pick-hard` narrows the gap to product menus with near misses, but it is still hand-written,
  has 3 escapes, and was written by the same team as its answer key (README, Limitations) [V].

## 4. Implications

### 4.1 For the Model Manager (D022 decision 4)

- **Direct Hugging Face downloads, pinned: adopt the exact procedure measured here** [I on V]:
  1. Resolve the commit (`api/models/<repo>` → `sha`) and each file's `lfs.oid` and `lfs.size` from the tree at that commit.
  2. Download `resolve/<commit>/<file>` to `*.part` with Range resume.
  3. Verify the size and SHA-256.
  4. Rename atomically.
  5. Record the result in the manifest.

  Start `llama-server` with `-m <file>`, not `-hf`, because `-hf` follows `main`. Still open from doc 13's S4: resume after a forced
  kill (10 of 10), tamper rejection, gated repositories with the user's token, the low-disk pre-check (five candidates needed about
  20 GB, more than this machine's system drive had free) and progress events. As D022 and D008 require, the user enables the source
  and starts every download; Wilco never does.
- **Manifest fields this spike shows are needed** [I]: the quant label from the file name, since `general.file_type` is 15 for both UD
  and Q4_K_M; the measured tensor-type mix; **both** licence fields, the model card's and the GGUF's `general.license`, since they
  disagree for the QAT file and a mismatch blocks a recommendation until resolved (D023 decision 6, OWQ-19); `general.sampling.*`
  defaults; a chat-template hash; the thinking default and its switch; and whether a vision projector is needed. A sketch:

  ```toml
  [[model]]
  id           = "gemma-4-e4b-it-qat-q4_0-unsloth"
  repo         = "unsloth/gemma-4-E4B-it-qat-GGUF"
  revision     = "8c5a9e4fd5482e2be20fe0bf013b4c262a8f4265"
  file         = "gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf"
  bytes        = 4215695776
  sha256       = "df0fd4ee07072c607c29a0a1cb4f98918426cca12f45a2776bdd6ee6d09a4de3"
  quant_label  = "QAT UD-Q4_K_XL"          # the file says Q4_0; the name is Unsloth's
  tensor_types = { Q4_0 = 0.9995, F32 = 0.0005 }
  license_card = "apache-2.0"
  license_gguf = "gemma"                   # mismatch: not recommendable until resolved
  thinking     = { default = "on", switch = "chat_template_kwargs.enable_thinking" }
  sampler      = { top_k = 64, top_p = 0.95, min_p = 0.0, presence_penalty = 0.0 }   # pinned per step kind
  [model.fit."llamacpp-vulkan.ctx8192"]
  gpu_added_mib = { load = 2894, peak = 3080 }
  measured_on   = "GTX 1070 8 GB, llama.cpp b11146 Vulkan, 2026-09-27"
  ```

- **Hardware fit from measured GPU memory, per backend and context.** On this machine, with 5,400–5,500 MiB free after the desktop,
  doc 44's rule (the increase plus a 512 MiB margin must fit) gives **Fits** for all six llama.cpp builds, with 1,959–2,418 MiB
  (1.9–2.4 GiB) left at peak. The two Ollama builds are **Tight** (1.0–1.3 GiB left). For an unmeasured quant of a measured
  model, estimate from the sibling plus the difference in GPU-resident tensor bytes, which matched to within about 11 MiB here (§2.6),
  and label it "estimated" [I on V].
- **Qualification badges per step kind, per artifact and runtime.** Doc 44's spike verdicts carry over to llama.cpp on every code-scored
  suite within noise. The notable updates [V; I]:

  | Step kind | Gemma QAT UD (llama.cpp) | Qwen Q4_K_M (llama.cpp) |
  | --- | --- | --- |
  | Pick (`pick`, pass^3) | Spike-checked (0.967 / 0.967) | Spike-checked (0.867 / 0.967) |
  | Harder menus (`pick-hard`, pass^3) | Spike-checked (0.833 / 0.867) | **Not met** (0.700 / 0.767) |
  | Fill, whole record | Not met (0.75) | Not met (0.58) |
  | Explanation, pass in both samples | Not met (0.6) | Spike-checked with card (0.9) |
  | Text code checks, both samples | 0.9 | 1.0 |
  | Knowledge | No: cards are shown instead | No |

  Two lessons for the badge design [I]:
  - A badge names its instrument. `pick` and `pick-hard` disagree for Qwen, so "Pick: qualified" needs the suite, its version and n.
  - Verdicts at the bar (Qwen harder menus with cards: 0.833 UD vs 0.767 Q4_K_M, one menu apart) must be shown as such, not rounded
    into a badge. Doc 21 §12.3's 14 consecutive all-pass trials remain the product bar.

  Whether a badge carries over between runtimes for the same weights is DG012's question. This spike suggests "carried over after a
  spot check" for Pick, but not yet for Fill, where the runtimes may differ (§2.1: suggestive, not significant).
- **Default recommendation for 8 GB GPUs** [I on V]:
  - **First choice: Gemma 4 E4B QAT, the Unsloth QAT Q4_0 file**, once the licence mismatch is cleared. It has the highest Pick (tied),
    harder-menu and Fill point estimates, none significantly above the other Gemma builds, the smallest footprint (+3,080 MiB at
    peak) and the fastest Gemma generation.
  - **Equal alternative: Qwen3.5-4B Q4_K_M** from Unsloth. It is the smaller download and had the best explanation grades (not
    significant at 10 findings), but was behind on harder menus without cards (5 menus to 0, p = 0.0625).
  - **Not UD-Q4_K_XL** for either model at 4-bit, and not the non-QAT Gemma files: no detectable gain, and a measurable cost in memory,
    speed and download.
  - **Before Gemma becomes the default,** measure Google's official QAT Q4_0 file (5.15 GB), the closest alternative whose model card
    is Apache-2.0 (its GGUF licence field was not read).
  - **One model per session on 8 GB** still holds (doc 44 §5.1). The llama.cpp builds leave about 2 GB free, which is not enough for a
    second 3 GB model.

### 4.2 For doc 13's runtime plan (the `llama-server` sidecar, Phase B)

- **The sidecar path works end to end on Windows with a Vulkan build and no CUDA libraries**: download a pinned zip, check its
  SHA-256, start on loopback, poll `/health`, probe, generate with a grammar, stop. That covers part of doc 13's S2 and supports Phase
  B [V].
  - Still open in S2 [U]: 50 of 50 start → generate → stop cycles, Job Object clean-up after forced kills, port collisions, a random
    `--api-key` (supported by `run.py`, not exercised), firewall prompts, and AMD, Intel and CPU-only machines.
  - The S1 parse criterion is met on both servers: 0 parse failures in 4,356 constrained or plain calls. S1's own prompts, streaming
    and cancellation were not tested [V].
- **Pinning llama.cpp** [V; I]:
  - Versioned releases now exist (v0.5.0), but they carry only `nightly-tag.txt`; the binaries stay on the `bNNNNN` build tags, which
    GitHub marks pre-release.
  - Pin the build tag and the asset's SHA-256, as doc 13 §2.1 said. The versioned release can be used to *choose* which build to pin.
  - This spike used b11146, whose Windows Vulkan zip is 32.1 MB (doc 13 measured 31.5 MB for b11201).
- **Start-up and probe sequence** [I on V]:
  1. `--jinja -ngl 99 -c <ctx> --host 127.0.0.1 --port <random> --api-key <random>`.
  2. Wait for `/health`.
  3. Read the build, context, slot count and default sampler from `/props`.
  4. Check with `/apply-template` that the thinking switch changes the prompt.
  5. Send one warm-up call.
  6. Record the effective values next to every result (doc 13 §3, "unknown, never guessed").
- **Pin everything per step kind.** Send temperature, top_k, top_p, min_p and the penalties (presence 0 for Pick and Fill, §2.2), the
  seed and the thinking switch on every request. Never rely on GGUF, server or Ollama build defaults [I on V].
- **Privacy.** `/props` and `/v1/models` report the model's full local path, which includes the user name. The sidecar must record the
  file name only, and diagnostics exports must strip the path. `run.py` already records the file name only [V; I].
- **Speed on older GPUs.** Prompt processing dominates on Vulkan and Pascal. Four things help [I]:
  - Keep step prompts short and prefix-stable, so the cache hits more.
  - Offer a user-downloaded upstream CUDA build, or the user's own Ollama or LM Studio, as the "faster on NVIDIA" option. Do not bundle
    CUDA (doc 13 §7).
  - Test a compact JSON grammar for Gemma.
  - Measure the same suites on an AMD or Intel GPU through Vulkan before quoting any latency as typical.
- **Grammar route.** `response_format` json_schema worked for every schema in the suites, with 100% schema-valid output. The
  whitespace behaviour is the model's choice inside the grammar (Gemma pretty-prints, Qwen does not). If the sidecar converts the
  schema to GBNF itself, it can remove optional whitespace [V; I].
- **Where Ollama and LM Studio fit.** Ollama 0.34.3 is a llama-server wrapper, so the product's behaviour on it is a known quantity
  once its build defaults are overridden. Keep it, and LM Studio, as auto-detected bring-your-own endpoints (doc 13 Phase A). The
  sidecar remains the "built-in local AI" path, because only there does Plotroom control the exact file, template, sampler and
  build [I].

## Open questions

1. **Why is prompt processing 2–3× slower here?** Is it Vulkan on Pascal, this build, or batch sizing for short prompts? Run the same
   battery with an upstream CUDA build and a newer Vulkan build on this GPU, and on an AMD or Intel GPU (doc 13 S2) [U].
2. **Why does Fill do better on llama.cpp?** Candidates are the weight files, JSON whitespace and the presence penalty. Needed: a
   sampler-matched Fill arm for Qwen, and Google's QAT Q4_0 file on llama.cpp as the runtime-only Gemma twin [U].
3. **Which licence governs Unsloth's QAT GGUF,** the model card's Apache-2.0 or the file's `gemma` tag? Until that is answered the
   Model Manager cannot recommend it (D023 decision 6, OWQ-19) [U].
4. **How does Unsloth's 4.22 GB "smart Q4_0" differ from Google's 5.15 GB QAT Q4_0 and ggml-org's 4.59 GB Q4_0,** and does that matter
   on our instruments? [U]
5. **Would a compact JSON grammar save about 200 ms per Gemma pick,** and does it change accuracy? [U]
6. **Is the end-of-menu penalty effect real?** It needs a larger Pick instrument. And does a presence penalty over the prompt tail
   also hurt Fill span copying? [U]
7. **Do qualification badges transfer between runtimes for the same weights,** and what spot check is enough (DG012)? [U]
8. **Is a 900-menu instrument worth building** to resolve quant effects of a few points, or is "no detectable difference at 30
   menus, choose the smaller file" the right product rule? [I]
9. **Should the sidecar use router mode (`--models-dir`),** and should we ask upstream for a revision-pinned `-hf`? That would be a
   request to the llama.cpp project, not to the game engine [U].

## Sources

**Repository docs.**

- `docs/research/13-local-inference-in-rust.md`: §2.1 (upstream builds and tags), §3 (servers, quirks, managed sidecar), §4, §6
  (download and model management), §7 (licences), §9 (phases), §11 (spikes S1, S2 and S4).
- `14-model-selection.md`: §3.2 (candidate sizes, including UD-Q4_K_XL), §5 (artifact identity), §6.
- `21-agent-doctrine.md`: §3.2 (Pick), §12.3 (qualification trials).
- `25-weak-model-friendly-campaign-harness.md`: §11.
- `44-local-model-qualification-spike.md`: all sections; its Ollama records are this doc's baseline.
- `47-small-model-landscape.md`: the wider candidate list.
- `docs/decisions/D008-outbound-network-sources.md`, `D022-local-inference-and-model-manager.md`, `D023-model-strategy.md`
  (decision 6), `OWNER-QUESTIONS.md` (OWQ-19), `docs/design-gap-requests/` (DG012).

**Tools and data.** `tools/local-qual/README.md`, `run.py`, `backends.py`, `score.py`,
`suites/{pick,pick-hard,fill,explain,text,knowledge}.json` (every record carries its suite file's hash; 0 stale).
`docs/research/data/runtime-quant-comparison.csv` holds this doc's aggregates and tests; `data/local-qualification.csv` holds doc 44's.

**Upstream source** (read at the named tags):

- llama.cpp `b11146` and `b10969`:
  - `tools/server/server-context.cpp` L409–L431 (`init_sampler`);
  - `common/sampling.cpp` L496 (`common_sampler_accept`);
  - `src/llama-sampler.cpp` L2885–L2891 (penalties `is_disabled`) and L2976 (frequency and presence penalty applied to the logits).
- Ollama `v0.34.3`:
  - `llm/server.go` L97–L100 (every GGUF through `llama-server`);
  - `llm/llama_server.go` L1572–L1592 and L2172–L2189 (sampler fields forwarded);
  - `api/types.go` L1124–L1139 (`DefaultOptions`);
  - `LLAMA_CPP_VERSION` (b10969).

**Releases and model repositories** (read 2026-09-27):

- <https://github.com/ggml-org/llama.cpp/releases> (v0.5.0 and its `nightly-tag.txt`, b11146, b11213).
- <https://huggingface.co/unsloth/Qwen3.5-4B-GGUF>, <https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF>,
  <https://huggingface.co/unsloth/gemma-4-E4B-it-qat-GGUF>, <https://huggingface.co/google/gemma-4-E4B-it-qat-q4_0-gguf>,
  <https://huggingface.co/ggml-org/gemma-4-E4B-it-GGUF>, <https://huggingface.co/Qwen/Qwen3.5-4B-Base>; revisions and hashes in §1.3.
  The Hugging Face endpoints used are `api/models/<repo>`, the file tree at a commit and `resolve/<commit>/<file>`.

**Runtime facts.** `llama-server --version`, `--list-devices`, `GET /props`, `POST /apply-template`, `llama-bench`; `ollama --version`,
`ollama show --parameters`, `ollama ps`; `nvidia-smi`; GGUF headers read with a standard-library script (metadata keys and tensor
tables).

**Statistics.** Exact McNemar (binomial on discordant pairs); Fisher's exact test; S. Holm, *Scand. J. Statist.* 6 (1979) 65–70;
percentile bootstrap (B. Efron, *Ann. Statist.* 7 (1979) 1–26); pass^k as in doc 44.

## Verification notes

### 2026-09-27, author checks at write-up

- **Scores and tests.** Every accuracy, pass^k, majority, escape, Fill and text figure comes from `score.py`'s summary over the 81 raw
  files. Every paired test comes from the run's significance output, and the CSV was generated from those files by script. The Gemma
  vs Qwen comparisons (§2.4) were computed for this doc from the raw records, with the same majority rule, exact McNemar and a paired
  bootstrap with a fixed seed. All 16 pairs had identical option orders.
- **Grades.** Pass, partial, fail, hallucination and pass-in-both counts were recounted from the five grade files, and the recount
  matches each file's own summary. Doc 44's Ollama grades come from doc 44's CSV.
- **Source citations.** The llama.cpp lines were re-read in copies of both tags; the cited lines are identical in b10969 and b11146.
  The Ollama lines were re-read at v0.34.3. The sampler-loss letters (7 harder-menu calls, all at G or X; G chosen 9 vs 13 and 12 vs
  16) and PW04 (1 of 36; 35 UNLOAD) were recounted from the raw records.
- **GGUF facts.** File type, imatrix, licence and sampling keys, and the per-type tensor bytes (§1.5) were read from the five local
  files' headers. The memory arithmetic in §2.6 uses those bytes and the logged `nvidia-smi` readings.
- **Hygiene.** This doc and the CSV contain no absolute local paths, user names or private-project references; the model-path leak
  noted in §4.2 is described, not reproduced.
- **Not verified:** host RAM use; the GPU backend Ollama used; Google's QAT Q4_0 file on either runtime; `-hf` with a gated repository;
  `--api-key`; any machine other than this one.

### 2026-09-27, review

An independent pass recomputed a sample of the numbers from the raw records, the score summary and the grade files with its own
scripts (not the run's analysis scripts), then corrected the doc, the CSV and the tool README in place.

- **Recomputed and matched.**
  - Every per-call accuracy, pass^3 and majority figure in §2.1, §2.3 and §2.4.
  - All 16 quant, 16 runtime and 4 sampler McNemar splits, with their discordant menu ids and p values, and the 12 Gemma-vs-Qwen
    splits.
  - The Fill all-fields tests, and the Holm results.
  - The bootstrap intervals, which a different seed reproduced to within one step of the per-call grid (1.1 points on Pick, 2.8 on
    Fill).
  - The sampler-arm details: 12 discordant calls (2 : 10, sign test p = 0.039), 7 harder-menu losses all at G or X, and G chosen 9
    vs 13 and 12 vs 16.
  - PW04 (1 of 36, 35 UNLOAD); the pick-hard escapes and 0 false escapes in 16 cells.
  - The per-menu pass^3 failures (HW04, HT03, HV01 15 of 16; HW03 13; HM04 10), and the 16-of-16 drop from `pick` to `pick-hard`
    (mean −7.65 points).
  - Letter agreement (86 and 87 of 90 with the sampler matched, 84 and 87 without), prompt-token parity (720 of 720, and 36 of 36 on Fill), and 0 thinking characters in
    3,140 records.
  - The median of 57–58 cached prompt tokens, the pooled warm p50s and prompt-eval p50s, the generation rates, the Pick prompt
    rates (summed tokens over summed time), and all GPU-memory, download-size and tensor-byte arithmetic.
  - All grade counts in §2.3 and §2.5, the E01/E04 explain gap, and Gemma QAT's E10 hallucinations.
  - The four llama.cpp source citations (identical at b10969 and b11146).
- **Corrected.**
  - "0 truncations" held only for the new records (doc 44 has one).
  - The TL;DR said "all of the gap is prompt processing": true for Qwen, about 320 of 536 ms for Gemma, whose pretty-printed JSON
    accounts for the rest.
  - The prompt-rate ranges now say they span Pick and harder menus.
  - The power arithmetic now gives about 30 discordant menus with the exact test, which puts Gemma at about 3,600 menus.
  - The "can rule out" bullet now says the percentile bound is indicative.
  - The QAT-vs-non-QAT note now includes the 1:1 harder-menu split with cards.
  - The generation rate is now given as 48.7 everywhere.
  - The tooling caveat claimed that `--resume` would skip the other runtime's records. It does not: `run.py` keys on the exact model
    label. The shared file, which the run's driver counted per file, is the real hazard.
- **Wording tightened to what the tests show.** None of these is significant:
  - "separate models" is now "pull the model families apart, though not yet significantly" (5:0, p = 0.0625);
  - "matches Ollama" is now "no detectable Pick quality difference";
  - "matter more than the runtime" is now "can matter as much as", with the net 323 / 315 / 316 call totals added;
  - "best measured build" is now "highest point estimates, none significantly above the other Gemma builds";
  - "the better explainer" is now "better explanation grades", with p = 0.25 and the replicated E10 hallucination;
  - "therefore carry a bias" is now "may carry";
  - Fill "where the runtimes differed" is now "may differ".

  The recommendations stand, as proposals resting on measured cost and on no detectable gain.
- **CSV.**
  - 28 cards-vs-none rows for the two other doc 44 models carried internal arm keys (`ol:…`) and an empty runtime and quant; they now
    name the Ollama tag, `Ollama 0.34.3` and the build.
  - The Ollama-sampler arm's `battery_wall_s_304_calls` row (198.2 s) was the time of its Pick jobs, since that arm never ran doc
    44's battery; it is now `pick_wall_s`, with n = 180.
  - The row count is unchanged (2,814).
- **Tool README.** Its commands and flags were checked against `run.py`, `backends.py` and `score.py`, and it gained four notes:
  - one output directory per runtime (`--out`), with a working `score.py` glob;
  - llama-server's `prompt_eval_count` counts the whole prompt while `prompt_eval_duration` excludes cached tokens, so a rate
    from those two overstates prompt speed by about a quarter;
  - the sampler pins this doc used, and the presence-penalty finding;
  - `HF_TOKEN` with `-hf` is untested.

  Its speed note now gives the measured suite rates next to the `llama-bench` figure.
- **Hygiene.** The doc, the CSV, the README, `run.py`, `backends.py`, `score.py` and `suites/pick-hard.json` contain no drive
  paths, user names, scratch-directory names or private-project references (searched).
  - `pick-hard.json` checked: 30 items, 7 unique keys and labels each, 3 escapes, ids and requests disjoint from `pick`, and
    categories as the README lists.
- **Not re-verified by the review:** the GGUF headers themselves (§1.5; only the arithmetic built on them), the Ollama source line
  numbers, the Hugging Face hashes, and the p90 and battery wall-time figures beyond the CSV.
