# Local shortlist, measured: bigger, smaller and specialist models on an 8 GB GPU

Research doc 49 for Plotroom (`ofp-editor`). Run dates: 2026-09-27 and 2026-09-28. Audience: contributors and LLM coding agents. This
file is meant to be read on its own.
Question answered: which of doc 47's shortlisted local models do better than doc 46's defaults (Gemma 4 E4B QAT and Qwen3.5-4B), step
kind by step kind; what Mixture-of-Experts (MoE) expert offload delivers on a GTX 1070 with 32 GB of RAM; whether a CUDA build of
llama.cpp is worth offering on older NVIDIA cards; and what the Model Manager should recommend per hardware tier.

**Status.** Measurements are **[V]**. Verdicts, the tier table and the D022 and D023 notes are proposals **[I]**. Four of doc 47's
nine shortlist rows ran; the others were deliberately not run (§1.2).
**Epistemic legend.** **[V]** measured in this run (re-derived from the raw call records, `score.py` output, the grade files, the
server logs, `nvidia-smi` and process samples, or `llama-bench`). **[V per doc N]** taken from a sibling doc. **[I]** our inference
or proposal. **[U]** unknown.
**Data.** Every aggregate, flag, pin, memory and speed figure and every paired test is in
[`data/local-shortlist-results.csv`](data/local-shortlist-results.csv) (columns `model, file, quant, placement, backend, suite,
condition, metric, value, n, notes`). Comparison rows name both arms in `model` (`A vs B`) and their test family in `notes`; rows
that did not run have `suite` = `status`. The harness is [`tools/local-qual/`](../../tools/local-qual/README.md), unchanged. Raw
call records, grader files, the run driver and its logs stay local, as in docs 44 and 46.
**Relation to sibling docs.** Doc 44 measured four models through Ollama; doc 46 moved to llama.cpp's `llama-server`, found no UD-quant
gain and set the provisional 8 GB defaults; doc 47 §6 planned this run and its decision rules (§6.3); doc 48 defers its cloud round 1
until this run; doc 50 and [D044](../decisions/D044-cloud-first-model-screening.md) add the owner's cloud-first screening rule; doc 53
drafts the sub-4B plan and quotes this run's rows as preliminary. D022 and D023 carry the runtime and model decisions this doc informs.
**Hygiene.** Every suite item is our own text; model answers are only paraphrased. No local paths or user names appear here.

## TL;DR

- **What ran.** Four new models on llama.cpp b11146 Vulkan with thinking off, 484 calls each: Qwen3-4B-Instruct-2507 and
  Spark-X2.5-4B fully on the GPU; Qwen3-30B-A3B-Instruct-2507 and Gemma 4 26B-A4B QAT with their expert weights in system RAM. Also a
  CUDA 12.4 build of the same source (speed only, plus a 90-call Pick control) and a Vulkan re-run of doc 46's Qwen3.5-4B, which gave
  the same letter on 90 of 90 calls. 0 errors, 0 parse failures and 0 thinking characters in 2,116 calls. NuExtract3, MiniCPM5-2B,
  Gemma 4 E2B, Granite 4.2-3B, the CPU-only rows and the Bonsai 2 probe were not run (§1.2) [V].
- **No new model beats the doc 46 defaults with statistical support on any step kind.** None of the 64 pre-planned comparisons
  (pick, harder menus, Fill, and the graded suites) survives Holm. The only raw p < 0.05 go the other way: Qwen3-4B-2507 and
  Spark-X2.5-4B each lost 7 harder menus to 0 against Gemma 4 E4B QAT without cards (p = 0.016, Holm 0.50), and Qwen3-4B-2507 lost 7
  Fill records to 0 (p = 0.016, Holm 0.13). At 30 menus no comparison had enough discordant items (at most 8) to detect even a
  3:1 split (§4) [V].
- **MoE offload gives the first local whole-record Fill above doc 47's 0.8 bar.** Both offload models got 11 of 12 records right in all
  three samples (pass^3 0.917). Gemma 4 E4B QAT got 9 (0.75) and Qwen3.5-4B 7 (0.58). Against Qwen3.5-4B that is +0.28 per call
  (bootstrap interval +0.03 to +0.56, 4 records to 0, p = 0.125); against Gemma 4 E4B QAT there is no detectable difference. Gemma 4
  26B-A4B has the best or joint-best point estimates on most step kinds so far, none significant: Pick 30 of 30 menus in both
  conditions, harder menus 28 and 30 of 30, explanations 19 of 20 with no invented fixes, 12 of 24 knowledge answers with cards.
  Gemma 4 E4B QAT still leads it on harder menus without cards (30 against 28 by majority), and Qwen3-30B-A3B and Spark-X2.5-4B on
  explanations (20 of 20) [V].
- **What offload costs on 8 GB of VRAM and 32 GB of RAM** [V] (memory "GB" below means thousands of MiB, §3):
  - **Speed.** Every uncached prompt pays a fixed cost of about 4.5–5 s plus 3–7 ms per token (`llama-bench` and the server's own
    timings), so the battery's prompts, a median of 217–245 new tokens, ran at about 37 tokens/s. Generation runs at 4–8
    tokens/s, not the 16–25 of doc 47's community reports. Warm Pick takes 6.5–7.5 s, Fill 11–17 s (p90 16–20 s, missing doc 47's
    10 s bar) and an explanation 17–25 s.
  - **Memory.** At the tuned `--n-cpu-moe` only 366–490 MiB of the card stays free. llama-server's working set reaches 14.8–17.2 GB,
    and the machine's available RAM fell to 1.7 GB once.
  - **`--cpu-moe`** (every expert layer in RAM) benchmarks at the same speed with 1.6–2.9 GB less VRAM, so it is the better default.
- **The two 4B newcomers do not displace the defaults** (doc 47 §6.3 items 1–2) [V; I].
  - **Qwen3-4B-Instruct-2507** is the fastest 4B measured (warm Pick 820 ms, 58 tokens/s generation; a different session from the
    baselines, §3.1) and passed 9 of 10 explanations in both samples. But it reached pass^3 only 0.63 / 0.73 on the harder menus and
    got 3 of 12 Fill records right: it returned verb phrases or paraphrases where the `target` field wants the object as written (0
    of 4).
  - **Spark-X2.5-4B** over-escapes: it answered "none fit" on 25 of 90 harder-menu calls, 16 of them wrongly. It also fails the
    `target` span.
- **CUDA 12.4 vs Vulkan on this Pascal card (same b11146 source)** [V; I]:
  - **Prompt processing** is 1.7–1.9× faster on CUDA for the dense models and 2.4× for the MoE model.
  - **Generation:** no consistent winner on the dense models; 1.29× on the MoE model.
  - **Warm Pick p50:** 724 ms on CUDA against 1,220 ms on Vulkan in the same session; CUDA was faster on 89 of 90 calls.
  - **Answers:** the same letter on 87 of 90 calls, with no detectable quality difference (p = 1.0).
  - **Costs:** a 645 MB download instead of 32 MB, a one-time 38–105 s kernel compile per model on Pascal, and 70–90 MiB more VRAM.
  - **For the Model Manager:** offer the upstream CUDA 12.x build as an optional, user-started download on NVIDIA cards, pinned by
    tag and SHA-256 and never bundled, and treat the backend as part of the setup a badge belongs to.
- **Bonsai 2 27B is not usable as a managed local model here** [V per doc 47; I]. It was not run. It needs PrismML's fork, which D022
  refuses to manage (amendment item 4). Its smallest file is larger than the card's free memory, and the fork processed prompts at
  about 16 tokens/s on a GTX 1070. It stays bring-your-own, screened in the cloud first under D044.
- **CPU-only tier: no verdict** [V smoke; I]. No CPU row ran. A 2-call smoke test put Qwen3.5-4B at about 12–15 prompt tokens/s at
  `-dev none` (16–19 s for a first Pick, about 1.4 s with a cached prefix). Doc 47's default stands: No AI or bring-your-own for
  CPU-only machines until a CPU row passes §6.3 item 5.
- **Recommendation per tier (proposal, §5.2)** [I]:
  - **8 GB GPU:** the session model is unchanged, Gemma 4 E4B QAT once its licence tag is cleared, with Qwen3.5-4B as the equal
    alternative.
  - **8 GB GPU with 32 GB RAM:** add an opt-in "bigger local model for heavy steps" switch for whole-record Fill and card-backed
    explanations, never for Picks. Use Qwen3-30B-A3B-2507 at `--cpu-moe`, the only offload file licensed Apache-2.0 in both its
    card and its GGUF. Gemma 4 26B-A4B QAT scores higher on harder menus (level on Fill), but its GGUF says `gemma`, the E4B QAT's
    blocker again.
  - **NVIDIA cards:** offer the CUDA build.
- **A default to pin, and a scorer bug** [V; I]:
  - **`--cache-ram`.** llama-server's default 8 GiB host prompt cache grew its private memory to 8.5–11.9 GB over a battery with
    almost no reuse, and on an offload row it pushed free RAM to the stop line. The sidecar must set it (by analogy with D022 item 5,
    under which build defaults are never relied on for samplers).
  - **`score.py`** counts a possessive of an allowed name ("Dravec's") as a name outside the allowed list; a fix belongs in the
    pending `tools/local-qual` patch.

## 1. Setup and pins

### 1.1 Machine and runtime [V]

| Item | Value |
| --- | --- |
| GPU | NVIDIA GeForce GTX 1070 (Pascal, compute capability 6.1), 8,192 MiB (`nvidia-smi` used + free = 8,061 MiB), driver 582.66. The desktop held 2,221–2,873 MiB during the runs (it drifted) |
| CPU | Intel Core i7-6820HK (Skylake laptop part), 4 cores / 8 threads, 2.7 GHz base, AVX2 and FMA, no AVX-512; llama.cpp loads its `haswell` CPU backend |
| RAM | 32 GB DDR4-2400 in dual channel (about 38.4 GB/s peak); about 18–20 GB available before each load, mostly standby cache |
| Disks | Models on a 7,200 rpm hard disk; the system SSD had too little space for them |
| OS | Windows 10 Pro 22H2 (19045) |
| Vulkan build (every quality record) | llama.cpp **b11146** (commit 7fe450e19), `llama-b11146-bin-win-vulkan-x64.zip`, SHA-256 `55a378aa…` (doc 46's build) |
| CUDA build (speed comparison and one Pick control) | Same tag, `llama-b11146-bin-win-cuda-12.4-x64.zip` (253,869,799 bytes, SHA-256 `3c806a6ceccc3dae1c743ceb1a1fb2cce5b76f40bfbd4c6b7b8afb6ef45a5807`) plus `cudart-llama-bin-win-cuda-12.4-x64.zip` (391,443,627 bytes, SHA-256 `8c79a9b226de4b3cacfd1f83d24f962d0773be79f1e7b75c6af4ded7e32ae1d6`), both equal to GitHub's listed digests. The only Windows CUDA 12.x x64 asset of this tag; about 1.17 GB unpacked. `--list-devices`: `CUDA0: NVIDIA GeForce GTX 1070 (8191 MiB, 7202 MiB free)` |
| Harness | `tools/local-qual/run.py --backend llamacpp` and `score.py`, both unchanged; suites as of doc 46 (every record carries its suite hash; 0 stale) |

**Contention.** Other processes kept the CPU busy during much of the run: antivirus scans, an editor, other jobs' tests. The system CPU
was 21–70% busy (median) during the dense benchmarks and 99–100% during the MoE ones. During the second half of the Gemma 26B battery
the laptop CPU also ran throttled, at a median 60% of nominal. Latencies from those periods are pessimistic; answers are unaffected
[V; I].

### 1.2 What ran and what did not [V]

| Doc 47 §6.1 row | Label here | Placement | Status |
| --- | --- | --- | --- |
| 1 Qwen3-4B-Instruct-2507 | `Qwen3-4B-Instruct-2507-Q4_K_M` | GPU | **Run**, 484 calls |
| 2 Qwen3-30B-A3B-Instruct-2507 | `Qwen3-30B-A3B-Instruct-2507-UD-Q4_K_XL` | MoE offload, `--n-cpu-moe 39` | **Run**, 484 calls |
| 3 Gemma 4 26B-A4B-it QAT | `gemma-4-26B-A4B-it-qat-UD-Q4_K_XL` | MoE offload, `--n-cpu-moe 26` | **Run**, 484 calls |
| 9 Spark-X2.5-4B | `Spark-X2.5-4B-Q4_K_M` | GPU | **Run**, 484 calls |
| 4 NuExtract3 | `NuExtract3-Q4_K_M` | GPU | Not run; also blocked on a template adapter that `run.py` lacks |
| 5 MiniCPM5-2B | `MiniCPM5-2B-Q4_K_M` (and `-cpu`) | GPU and CPU | Not run |
| 6 Qwen3.5-2B | `Qwen3.5-2B-Q4_K_M-cpu` | CPU | Not run |
| 7 Granite-4.0-H-1B, Granite-4.0-1B | `granite-4.0-h-1b-Q4_K_M-ibm-cpu`, `granite-4.0-1b-Q4_K_M-ibm-cpu` | CPU | Not run |
| 8 Granite-4.0-H-Tiny | `granite-4.0-h-tiny-UD-Q4_K_XL-cpu` | CPU | Not run |
| 9 (sibling) Spark-X2.5-1.7B | `Spark-X2.5-1.7B-Q4_K_M-cpu` | CPU | Not run |
| Carry-overs: Gemma 4 E2B QAT, Granite 4.2-3B | `gemma-4-E2B-it-qat-UD-Q4_K_XL`, `granite-4.2-3b-Q4_K_M-ibm` | GPU | Not run |
| Optional: Bonsai 2 27B paired probe | — | Fork runtime, partial offload | Not run, not downloaded |
| Controls | `Qwen3.5-4B-Q4_K_M-vk-ctl` (Vulkan), `Qwen3.5-4B-Q4_K_M-cuda12` (CUDA) | GPU | **Run**, `pick/none` only, 90 calls each |

- **Why rows were not run.** On 2026-09-27 the owner set the cloud-first rule, now recorded as D044. It says that any model that could
  run locally is screened on a cloud copy of the same weights first, and tried locally only if promising. The workflow therefore kept
  the four rows already under way and deferred the rest. The files of the nine deferred local rows are pinned (repository, commit,
  size, SHA-256) but were not downloaded; the CSV lists their pins and planned flags under `suite` = `status` [V].
- **A tension to settle, not settled here.** Doc 50 §5 and
  [`data/cloud-screening-candidates.csv`](data/cloud-screening-candidates.csv) found no same-weights cloud host for NuExtract3,
  MiniCPM5-2B, the three Granite 4.0 rows or Spark-X2.5 (so presumably not its 1.7B sibling either, which is not listed). Qwen3.5-2B
  and Gemma 4 E2B are hosted only on Featherless, and the owner bought no Featherless plan (D044 amendment). Granite 4.2-3B has only a
  no-schema cloud arm, and doc 50 marks it "local first". So under D044's P5 as written (a proposal: what cannot be cloud-screened goes
  local directly), and under doc 53's reading of it, most deferred rows would go local without a screen. Only the Bonsai 2 probe has a
  real screen path. How D044 applies to doc 49's remaining rows is an open part of D044 (Open question 1) [V per doc 50; I].
- **Baselines** are doc 46's llama.cpp records for Qwen3.5-4B Q4_K_M and Gemma 4 E4B QAT UD-Q4_K_XL, reused, not re-run. They come
  from the same build and server flags and were re-scored with the same `score.py`. The Vulkan control re-ran doc 46's Qwen3.5-4B
  `pick/none` job with identical flags and sampler, and chose the same letter on all 90 calls, so the setup reproduces [V].

### 1.3 Models, fetched straight from Hugging Face [V]

| Model | Repository @ commit | File | Bytes | SHA-256 | GGUF `general.license` |
| --- | --- | --- | --- | --- | --- |
| Qwen3-4B-Instruct-2507 | `unsloth/Qwen3-4B-Instruct-2507-GGUF` @ `a06e946bb6b655725eafa393f4a9745d460374c9` | `Qwen3-4B-Instruct-2507-Q4_K_M.gguf` | 2,497,281,120 | `3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597` | `apache-2.0` |
| Spark-X2.5-4B | `XHToken/Spark-X2.5-4B-GGUF` @ `9826e0be84e6e6e8b9668abc91421109a1df1e2d` | `Spark-X2.5-4B-Q4_K_M.gguf` | 2,600,224,352 | `adfcfa19a4ed6a5985da8bf565fe15f8e1a7e131d79bae2d19d48d1c40109428` | none (the key is absent) |
| Qwen3-30B-A3B-Instruct-2507 | `unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF` @ `eea7b2be5805a5f151f8847ede8e5f9a9284bf77` | `Qwen3-30B-A3B-Instruct-2507-UD-Q4_K_XL.gguf` | 17,690,497,440 | `535f831bf3034a7fcfdcc8f0277a57cbad3a36c650c6068bf1d0894f25fb4383` | `apache-2.0` |
| Gemma 4 26B-A4B-it QAT | `unsloth/gemma-4-26B-A4B-it-qat-GGUF` @ `7b92b5b28818151e8669af2e45e88d6086f490dd` | `gemma-4-26B-A4B-it-qat-UD-Q4_K_XL.gguf` | 14,249,047,104 | `a7c5bc715f5ff8e99a3e8901ce7d2b42b402c669bf24f7c5250747633d0f5891` | **`gemma`** (file type 2, uniform Q4_0, "smart Q4_0, QAT-lossless") |

- **Quant choice.** Dense models: Q4_K_M, since doc 46 found no UD gain. MoE models: the smaller of the two Q4 files, UD-Q4_K_XL for
  Qwen3-30B-A3B (17.69 GB against 18.56 GB for Q4_K_M). Gemma 26B-A4B QAT has no Q4_K_M; Unsloth's QAT file (14.25 GB) is smaller
  than Google's Q4_0 (14.44 GB) [V].
- **Download.** The pinned route of doc 46 §4.1: resolve the commit, read each file's LFS oid and size, download `resolve/<commit>/<file>`
  with resume, check the SHA-256, rename atomically, record a manifest entry. About 35–36 MB/s; all four hashes matched [V].
- **Licence fields.** Gemma 26B-A4B QAT's GGUF carries `gemma` where its model card says Apache-2.0, the same mismatch doc 46 found
  for the E4B QAT file. Spark's GGUF has no licence key and names itself `Hf_Format` [V]. Under D037 a mismatch blocks a recommendation
  until it is resolved [V per D023 amendment; I].

### 1.4 How they ran [V]

- **Server** (`llama-server`): `-m <file> --jinja -c 8192 --host 127.0.0.1 --port <free>`, plus the placement flags:
  - **GPU:** `-ngl 99`.
  - **MoE offload:** `-ngl 99 --n-cpu-moe N -t 4`; N was tuned per model (§3.2).
  - `-np` was left unset, as in doc 46: 4 slots, a unified KV cache and 8,192 tokens per slot. Doc 47 §6.2 had proposed `-np 1`;
    the default was kept for comparability with the baselines.
  - `--reasoning` stayed on auto and `--no-mmproj` was not needed (with `-m`, no projector is loaded).
  - `--cache-ram` stayed at its default except on the MoE rows, which switched to 0 (§3.4).
- **Sampler.** Each vendor's recommended non-thinking top_k / top_p / min_p. A value the vendor does not give is disabled (top_k 0,
  top_p 1.0, min_p 0). Presence penalty 0 and repeat penalty 1.0 everywhere. `run.py`'s per-suite temperature (0.6 for Pick, Fill and
  text; 0.2 for explanations and knowledge) and its seeds were unchanged; the vendor temperatures were recorded, not used.

  | Model | top_k / top_p / min_p | Source |
  | --- | --- | --- |
  | Qwen3-4B-2507, Qwen3-30B-A3B-2507 | 20 / 0.8 / 0 | Model cards ("Best Practices") and `generation_config.json` |
  | Gemma 4 26B-A4B QAT | 64 / 0.95 / 0 | Model card and `generation_config.json`; min_p not given |
  | Spark-X2.5-4B | 0 / 0.95 / 0 | The vendor publishes only thinking-mode values (top_k −1, top_p 0.95); −1 mapped to 0 |
  | Baselines (doc 46) | Qwen3.5-4B 20 / 0.95 / 0; Gemma 4 E4B QAT 64 / 0.95 / 0 | Doc 46 §1.4 |

  So the arms differ in sampler as well as model: each comparison is between product setups as the vendors recommend them. The
  optional Qwen3.5-4B arm with its own card's top_p 0.8 did not run [V].
- **Thinking off, checked.** `run.py` sends `chat_template_kwargs: {enable_thinking: false}`. Before each battery, the server's
  `/apply-template` rendered one prompt with the switch off and on:
  - **Spark-X2.5-4B:** off ends the prompt with an empty closed think block; on opens one.
  - **Gemma 4 26B-A4B:** off renders an empty, closed thought channel; on adds a think turn to the system message.
  - **The two Qwen3-2507 models** have no thinking mode, so their templates ignore the switch.
  - **All four:** every one of the 2,116 records has 0 thinking characters.
- **Jobs.** Per model: pick and pick-hard at k = 3 without and with cards (90 calls each), Fill at k = 3 (36), explain with cards
  and text without cards at k = 2 (20 each), knowledge without and with cards at k = 2 (24 each). That is 484 calls, the same list
  as doc 46. Long jobs ran in chunks with `--resume`. On the MoE rows `--timeout 900`; 7 and 10 chunks hit the driver's time budget
  and resumed. Each raw file holds exactly the expected records, with no duplicate (item, sample) keys [V].
- **Mid-row changes, recorded per call.**
  - **Qwen3-30B-A3B's host prompt cache.** The default cache grew the server's private memory while available RAM touched the 2,000
    MiB stop line, so the server was restarted with `--cache-ram 0` from `pick/cards` record 56 on.
  - **Gemma 26B's server stopped mid-job.** The first server ended during `pick-hard/none` when an earlier attempt of the step was
    interrupted. Its 11 records were kept and the job resumed on a new server with identical arguments.
  - **What they affect.** Both change latency only [I].
- **Scoring.** `score.py` (unchanged) over this run's raw files and doc 46's: 91 groups, 0 errors, 0 stale suites. Knowledge,
  explanations and text quality were graded by a strict LLM grader, one pass per model, using the rubric and verdict scale of doc
  46's grade files. The paired tests are §4's [V].

## 2. Results per step kind

Menus are paired across setups: the seeds and option shuffles depend only on (item, sample), and every pair was checked for equal
seeds and letter orders. "Majority" is right in at least 2 of 3 samples (a tie counts as wrong). Tests: exact McNemar on items
right by majority in one arm only, and a paired item bootstrap (10,000 resamples) for the per-call difference, with Holm adjustment
within each family (§4). Baselines are marked (b).

### 2.1 Pick and harder menus [V]

Per-call accuracy / pass^3 / majority. **Escapes**: the harder menus plant 3 items whose right answer is "none fit" (X), so 9 escape
calls per condition; "hit" counts those answered X, "false" counts X given where another option was right.

| Setup | `pick` none | `pick` cards | `pick-hard` none | `pick-hard` cards | Harder-menu escapes, none: hit / false | cards: hit / false |
| --- | --- | --- | --- | --- | --- | --- |
| Gemma 4 E4B QAT (b) | 0.967 / 0.967 / 0.967 | 0.967 / 0.967 / 0.967 | 0.944 / 0.833 / **1.000** | 0.922 / 0.867 / 0.900 | 8 / 0 | 9 / 0 |
| Qwen3.5-4B Q4_K_M (b) | 0.933 / 0.867 / 0.967 | 0.967 / 0.967 / 0.967 | 0.822 / 0.700 / 0.833 | 0.867 / 0.767 / 0.867 | 8 / 0 | 7 / 0 |
| Qwen3-4B-Instruct-2507 | 0.933 / 0.900 / 0.933 | 0.967 / 0.967 / 0.967 | 0.756 / 0.633 / 0.767 | 0.789 / 0.733 / 0.800 | 3 / 0 | 4 / 0 |
| Spark-X2.5-4B | 0.911 / 0.833 / 0.933 | 0.911 / 0.833 / 0.933 | 0.756 / 0.667 / 0.767 | 0.811 / 0.733 / 0.800 | 9 / **16** | 9 / **10** |
| Qwen3-30B-A3B-2507 (offload) | 0.967 / 0.967 / 0.967 | 0.978 / 0.967 / 0.967 | 0.822 / 0.700 / 0.867 | 0.889 / 0.800 / 0.933 | 5 / 0 | 6 / 0 |
| Gemma 4 26B-A4B QAT (offload) | 0.989 / 0.967 / **1.000** | **1.000 / 1.000 / 1.000** | 0.911 / 0.833 / 0.933 | 0.978 / 0.933 / **1.000** | 9 / 3 | 9 / 0 |

Random-valid controls: 0.191 (`pick`) and 0.143 (`pick-hard`); first-option controls 0.156 and 0.122. Every setup is far above them.

**Paired against the baselines** (menus right by majority in the new setup only : in the baseline only; exact McNemar p):

| New setup | vs Gemma E4B QAT: `pick-hard` none | cards | vs Qwen3.5-4B: `pick-hard` none | cards | `pick` (both baselines, both conditions) |
| --- | --- | --- | --- | --- | --- |
| Qwen3-4B-2507 | **0 : 7, p = 0.016** (Holm 0.50) | 1 : 4, p = 0.375 | 1 : 3, p = 0.625 | 1 : 3, p = 0.625 | 0–1 discordant, p = 1.0 |
| Spark-X2.5-4B | **0 : 7, p = 0.016** (Holm 0.50) | 0 : 3, p = 0.25 | 1 : 3, p = 0.625 | 1 : 3, p = 0.625 | 0–1 discordant, p = 1.0 |
| Qwen3-30B-A3B-2507 | 0 : 4, p = 0.125 | 2 : 1, p = 1.0 | 4 : 3, p = 1.0 | 2 : 0, p = 0.5 | 0 discordant |
| Gemma 4 26B-A4B | 0 : 2, p = 0.5 | 3 : 0, p = 0.25 | 4 : 1, p = 0.375 | 4 : 0, p = 0.125 | 1 : 0 (PW04), p = 1.0 |

- **Pick is saturated.** Every setup is at 0.93–1.00 by majority in both conditions, with 0–1 discordant menus per pair. No detectable
  difference [V].
- **PW04, the fact-bearing menu** (TR UNLOAD vs UNLOAD), was answered right in 5 of 6 samples by Gemma 4 26B-A4B, and in 1 of 6 by
  Qwen3-30B-A3B. Every dense setup here, the baselines included, got 0 of 6; doc 46's single hit in 36 samples came from its
  Ollama-sampler arm. One menu cannot carry a claim, and doc 53 treats such menus as a harness fix (code filters by the fact) rather
  than a model tier [V; I per doc 53].
- **Harder menus: the 4B newcomers trail Gemma 4 E4B QAT without cards.** Both lost 7 menus to 0 (raw p = 0.016), per-call −0.19
  (bootstrap intervals −0.31 to −0.09 and −0.32 to −0.07, unadjusted). Neither result survives Holm across the 32 Pick tests
  (0.50), so it is suggestive, not established [V].
  - **Qwen3-4B-2507** keeps missing the same items: HA03 0 of 3 in both conditions, where both baselines had 3 of 3, plus HM04,
    HT01, HT03, HV01 and HW04, all wrong by majority in both conditions. It escapes too little (3 and 4 of 9) and is weakest on
    replayability (0.33 / 0.50) and triggers (0.60 / 0.53) [V].
  - **Spark-X2.5-4B** escapes too much: X on 25 of 90 calls without cards and 19 with cards, of which 16 and 10 were wrong. It also
    under-picks A on the easy menus (0.64–0.71 accuracy when A is right, at least 0.875 for the other letters). It fails doc 47's
    must-pass ("no false escapes") in both suites, with 3 and 2 false escapes on the easy menus too [V].
- **The offload models show no detectable difference from the defaults on harder menus.** Qwen3-30B-A3B's pass^3 is 0.70 / 0.80,
  like Qwen3.5-4B's but 13 and 7 points below Gemma E4B QAT's; it under-escapes (5 and 6 of 9). Its 0 : 4 against Gemma E4B QAT
  without cards (per-call −0.12, interval −0.22 to −0.04 unadjusted) is not significant. Gemma 26B-A4B is the only setup with
  pass^3 ≥ 0.8 in both conditions besides Gemma E4B QAT. It over-escaped one menu, HT03, in all three samples without cards; with
  cards it passed the must-pass [V].
- **Other per-call intervals that exclude 0** (unadjusted, listed for completeness; none has item-level support): Spark-X2.5-4B −0.06
  on `pick` against Gemma E4B QAT in both conditions and against Qwen3.5-4B with cards (one menu, PM05); Qwen3-4B-2507 −0.13 and
  Spark −0.11 against Gemma E4B QAT on harder menus with cards; Gemma 26B-A4B +0.06 on `pick` without cards (PW04) and +0.11 on
  harder menus with cards, both against Qwen3.5-4B [V].
- **Must-pass on the harder menus (doc 47 §6.3 item 6: X on every planted escape and no false escapes) is met only with cards**, by
  Gemma 4 E4B QAT and Gemma 4 26B-A4B. Without cards every setup either misses an escape or escapes falsely. On the easy menus every
  setup but Spark-X2.5-4B passes it [V].

### 2.2 Fill [V]

Twelve request → record items, k = 3. "All fields" is the whole record right in one call; pass^3 counts records right in all three
samples. The `target` span is scored on 4 items (F09–F12).

| Setup | All fields per call | pass^3 (records of 12) | Field accuracy | `size` | `target` | `task` | `place` | Quote check | Validators all pass (per call) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemma 4 E4B QAT (b) | 0.861 | 0.750 (9) | 0.970 | 0.79 | 1.00 | 1.00 | 1.00 | 1.000 | 0.972 |
| Qwen3.5-4B (b) | 0.639 | 0.583 (7) | 0.893 | 0.67 | 0.83 | 0.75 | 0.92 | 0.944 | 0.861 |
| Qwen3-4B-2507 | 0.250 | 0.250 (3) | 0.786 | 0.50 | **0.00** | 0.75 | 0.75 | 0.667 | 0.667 |
| Spark-X2.5-4B | 0.444 | 0.250 (3) | 0.881 | 0.71 | **0.00** | 0.96 | 1.00 | 0.833 | 0.750 |
| Qwen3-30B-A3B-2507 | **0.917** | **0.917 (11)** | 0.982 | 0.88 | 1.00 | 1.00 | 1.00 | 1.000 | 0.917 |
| Gemma 4 26B-A4B | **0.917** | **0.917 (11)** | 0.982 | 0.88 | 1.00 | 1.00 | 1.00 | 1.000 | **1.000** |

Every setup returned schema-valid JSON on every call. `archetype`, `side` and `time_of_day` were right on every call for every setup.

**Paired, all fields right by majority** (new : baseline; exact McNemar p; per-call difference with its unadjusted bootstrap interval):

| New setup | vs Gemma 4 E4B QAT | vs Qwen3.5-4B |
| --- | --- | --- |
| Qwen3-30B-A3B-2507 | 1 : 0, p = 1.0; +0.06 (−0.06 to +0.19) | 4 : 0, p = 0.125 (Holm 0.88); **+0.28 (+0.03 to +0.56)** |
| Gemma 4 26B-A4B | 1 : 0, p = 1.0; +0.06 (−0.06 to +0.19) | 4 : 0, p = 0.125 (Holm 0.88); **+0.28 (+0.03 to +0.56)** |
| Qwen3-4B-2507 | **0 : 7, p = 0.016** (Holm 0.13); −0.61 (−0.83 to −0.36) | 0 : 4, p = 0.125; −0.39 (−0.64 to −0.14) |
| Spark-X2.5-4B | 2 : 6, p = 0.29; −0.42 (−0.69 to −0.14) | 2 : 3, p = 1.0; −0.19 (−0.50 to +0.11) |

- **Both offload models miss only F05**, on `size`: a squad, where the gold answer is "medium". They are the first local setups at or
  above doc 47 §6.3 item 3's whole-record bar (pass^3 ≥ 0.8, 10 of 12). Against Gemma 4 E4B QAT (9 of 12 in all samples, 10 by
  majority) the paired gain is one record (F08), so there is no detectable difference. Against Qwen3.5-4B the per-call interval
  excludes 0, but the item-level test does not reach significance [V].
- **The two 4B newcomers fail on span copying, not on format.** Every record was schema-valid, yet `target` was 0 of 4 for both
  [V].
  - **Qwen3-4B-2507** returned verb phrases or paraphrases such as "destroy the radar at Hill 214 near Dravec", where the span is the
    object. That also fails the verbatim quote check. It guessed `size` "small" when the request gives none, and reordered a place
    span. Its three samples were identical on 10 of 12 items (F11 and F12 differed in wording, F12 also in its `target`): top_k 20
    with top_p 0.8 at temperature 0.6 is very peaked.
  - **Spark-X2.5-4B** returned the whole task clause (for example "destroy the radar and slip away before dawn").
- **Doc 44's rule still holds for the 8 GB session models:** a Fill record is a pre-fill the user confirms, and only closed fields
  qualify (doc 44 §5.1). The offload models change this for users who switch to them, at the latency of §3.2 [I].

### 2.3 Explanations, text and knowledge (graded) [V]

Strict LLM grader, one pass per model; baselines from doc 46's grade files. "Both" counts items passed in both samples. H =
answers that present a non-existent command, key or behaviour.

| Setup | Explain (cards): pass / partial / fail (H) · both of 10 | Text quality: pass / partial / fail · both of 10 | Text code constraints (per call) | Knowledge none: pass (H of 24) | Knowledge cards: pass / partial / fail (H) · both of 12 |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 E4B QAT (b) | 13 / 7 / 0 (2) · 6 | 3 / 16 / 1 · 0 | 0.95 | 0 (23) | 6 / 8 / 10 (8) · 3 |
| Qwen3.5-4B (b) | 19 / 1 / 0 (0) · 9 | 4 / 15 / 1 · 1 | 1.00 | 0 (24) | 3 / 7 / 14 (13) · 1 |
| Qwen3-4B-2507 | 18 / 2 / 0 (0) · 9 | 6 / 14 / 0 · 2 | 1.00 | 0 (22) | 3 / 10 / 11 (7) · 1 |
| Spark-X2.5-4B | 20 / 0 / 0 (0) · **10** | 3 / 17 / 0 · 1 | 0.90 (0.95 without the scorer bug) | 0 (23) | 6 / 7 / 11 (6) · 3 |
| Qwen3-30B-A3B-2507 | 20 / 0 / 0 (0) · **10** | 7 / 13 / 0 · 3 | 1.00 | 0 (23) | 11 / 5 / 8 (5) · 5 |
| Gemma 4 26B-A4B | 19 / 1 / 0 (0) · 9 | 7 / 13 / 0 · 3 | 1.00 | 1 (23) | **12** / 6 / 6 (8) · **6** |

Paired on items passed in both samples (24 tests: 4 new models × 2 baselines × explain, text and knowledge with cards), no test
survives Holm (all adjusted p = 1.0). The largest splits are on explanations, where Qwen3-30B-A3B and Spark-X2.5-4B each lead Gemma
4 E4B QAT 4 : 0 (p = 0.125), and on knowledge with cards, where Gemma 4 26B-A4B and Qwen3-30B-A3B lead Qwen3.5-4B 5 : 0 and 4 : 0
(p = 0.0625 and 0.125).

- **Explanations with cards qualify for every new model** on doc 44's bar (pass in both samples ≥ 0.8 of 10 findings): 0.9–1.0,
  with no hallucinated fix. Gemma 4 E4B QAT (0.6, two invented one-line fixes on E10) remains the only tested setup below it. Gemma
  26B-A4B did not repeat its smaller sibling's E10 fix. Each model was graded in its own pass, so these differences stay descriptive
  (doc 46 §2.5's grader caveat) [V; I].
- **Structured-output debris the schema did not catch** [V]:
  - **Qwen3-4B-2507** closed a JSON string where an escaped quote belonged (E02, both samples) and left a stray brace in one fix.
  - **Spark-X2.5-4B** wrote a raw carriage return where a file path's backslash belonged (E03), and one answer ended in `}{`.

  Code should insert paths itself and reject control characters and brace debris in code-bearing fields [I].
- **Knowledge without cards: doc 44's rule stands.** 0–1 passes in 24 and 22–23 hallucinations for every new model, the 30B-class
  ones included; Qwen3-4B-2507 even misnamed the game. With cards the offload models pass 11–12 of 24 against 3–6 for the 4B
  setups, but cards still leave 5–8 hallucinations [V].
- **Text: constraints are code's job, quality stays low.**
  - **Code checks:** held on 90–100% of lines. Spark's two failures are one real overrun (5 words against a cap of 4) and one scorer
    false positive (§4, tooling).
  - **Graded quality:** 3–7 passes of 20 for every setup, so lines stay candidates the user picks from (doc 44 §2.4).
  - **Spark:** leaked tone labels into lines ("with restrained pride", "sombre") and wrote radio slots as third-person narration
    [V].

### 2.4 Qualification view, per step kind [V; I]

Spike checks in doc 44's and doc 46's sense (pass^3 ≥ 0.8 or pass in both samples ≥ 0.8), not product badges. Doc 21 §12.3's 14
consecutive all-pass trials remain the product bar.

| Step kind (instrument) | Gemma E4B QAT (b) | Qwen3.5-4B (b) | Qwen3-4B-2507 | Spark-X2.5-4B | Qwen3-30B-A3B (offload) | Gemma 26B-A4B (offload) |
| --- | --- | --- | --- | --- | --- | --- |
| Pick (`pick`, pass^3 none / cards) | Met (0.967 / 0.967) | Met (0.867 / 0.967) | Met (0.900 / 0.967) | Met (0.833 / 0.833) | Met (0.967 / 0.967) | Met (0.967 / 1.000) |
| Harder menus (`pick-hard`, pass^3) | Met (0.833 / 0.867) | Not met (0.700 / 0.767) | Not met (0.633 / 0.733) | Not met (0.667 / 0.733) | Not met (0.700 / 0.800) | Met (0.833 / 0.933) |
| Must-pass escapes, harder menus | With cards only | No | No | No (false escapes) | No | With cards only |
| Fill, whole record (pass^3) | Not met (0.75) | Not met (0.58) | Not met (0.25) | Not met (0.25) | **Met (0.92)** | **Met (0.92)** |
| Explanation with card (both samples) | Not met (0.6) | Met (0.9) | Met (0.9) | Met (1.0) | Met (1.0) | Met (0.9) |
| Text, code constraints (per call) | 0.95 | 1.0 | 1.0 | 0.9 | 1.0 | 1.0 |
| Knowledge without cards | No | No | No | No | No | No |
| Warm latency class (Pick p50) | ~1.1 s | ~1.0 s | ~0.8 s | ~1.0 s | ~6.5 s | ~7.1 s |

## 3. Speed and memory per placement

**Units.** Memory is read in MiB (`nvidia-smi`, Windows counters). Where this doc gives a memory reading in GB, it means thousands of
MiB: 1 GB here is 1.049 × 10⁹ bytes (0.98 GiB). File sizes in GB (§1.3) are decimal.

### 3.1 Dense models on the GPU [V]

GPU figures are whole-card `nvidia-smi` readings (desktop included), sampled every 2 s. Host figures are the `llama-server` process's
working set and private bytes; doc 46 did not sample them. Latency is warm (after one warm-up call), p50 per suite without cards.

| Setup | GPU added: after load / peak | Free at peak (of 8,192) | Host working set after load; private after first job → max | Start to `/health` | Pick p50 / p90 | Harder menus p50 | Fill p50 / p90 | Explain p50 | Generation tokens/s | Prompt tokens/s (uncached) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemma 4 E4B QAT (b) | +2,894 / +3,080 | 2,418 | not sampled | 8.8 s | 1,088 / 1,284 | 1,161 | 2,223 / 2,901 | 2,555 | 44.1 | 305 |
| Qwen3.5-4B (b) | +3,167 / +3,193 | 2,307 | not sampled | 4.2 s | 1,019 / 1,050 | 1,073 | 2,051 / 2,832 | 2,530 | 43.9 | 277 |
| Qwen3-4B-2507 | +3,641 / +3,681 | 1,692 | 2,844; 4,472 → 9,396 MiB | 4.2 s | **820** / 891 | 906 | 1,494 / 2,193 | 1,709 | **58.0** | 266 |
| Spark-X2.5-4B | +3,143 / +3,256 | 2,155 | 2,887; 4,165 → 11,900 MiB | 3.7 s | 962 / 1,001 | 1,011 | 1,940 / 2,768 | 1,964 | 50.7 | 288 |

- **These rows ran in different sessions.** The same-session Vulkan control of Qwen3.5-4B took 1,220 ms for Pick against 1,019 ms in
  doc 46, with identical answers, so session drift of about 20% is within noise here. Qwen3-4B-2507's generation lead (58 against
  44 tokens/s, +32%) is larger than that drift; its Pick lead (820 against 1,019 ms, −20%) is about the size of it. Neither was
  measured in the same session as the baselines [V; I].
- **KV cache.** Qwen3-4B-2507 keeps KV in all 36 layers, against 8 full-attention layers for Qwen3.5-4B. At 8K that cost about 470
  MiB more GPU memory after load, although its file is 0.24 GB smaller. It still leaves 1.7 GB free [V; I per doc 47 §1.3].
- **Output length.** Gemma 4 26B-A4B returned 12 tokens per pick, against 16 for Gemma 4 E4B QAT (pretty-printed JSON, doc 46 §2.6)
  and 7 for the Qwen and Spark models [V].

### 3.2 MoE expert offload [V]

**Tuning.** `llama-fit-params` gave a projection, then each candidate N was loaded in a real server and measured with `nvidia-smi`
after a warm call. N is the number of layers whose expert weights stay in RAM. The rule was the smallest N leaving at least 400 MiB of
VRAM free at the highest desktop reading seen (2,873 MiB).

| VRAM the server adds after a warm call (MiB) | `--cpu-moe` (all expert layers in RAM) | Chosen N | One layer fewer |
| --- | --- | --- | --- |
| Qwen3-30B-A3B-2507 (48 layers) | +1,813 | +4,678 at N = 39 (510 MiB spare at the worst desktop reading) | +5,018 at N = 38 (about 170 MiB spare) |
| Gemma 4 26B-A4B (30 layers) | +2,889 | +4,523 at N = 26 (665 MiB spare) | +4,933 at N = 25 (255 MiB spare) |

The projections were off in both directions: `llama-fit-params` under-read Gemma's real delta by about 580 MiB and over-read Qwen's
by 65–310 MiB (170–310 at N = 38–40). So a fit estimate needs a measured margin [V; I].

**Speed at the chosen N** (Vulkan):

| Measure | Qwen3-30B-A3B-2507 (N = 39) | Gemma 4 26B-A4B (N = 26) |
| --- | --- | --- |
| `llama-bench` pp512 / tg128, chosen N | 63–70 / 4.1–5.2 tokens/s (several runs under varying CPU load) | 86–88 / 7.2 |
| `llama-bench` pp512 / tg128, `--cpu-moe` | 68.0 / 6.7 | 82.8 / 7.8 |
| Prompt tokens/s with op-offload on vs off (pp128 / pp256 / pp512) | 23 / 43 / 70 vs 15 / 12 / 12 | 27 / 50 / 88 vs 12 / 13 / 13 |
| Server, real prompts: prompt tokens/s (weighted), generation tokens/s | 37, 7.9 | 37, 4.9 (6.6 on answers of 16+ tokens) |
| Warm p50: Pick none / cards | 6.5 / 6.6 s | 7.1 / 7.5 s |
| Warm p50: harder menus none / cards (p90) | 6.6 / 7.5 s (7.0 / 9.0) | 9.2 / 11.1 s (15.6 / 23.6) |
| Warm p50: Fill (p90) | 11.3 s (**16.1**) | 16.6 s (**20.1**) |
| Warm p50: explain, text, knowledge none / cards | 17.2, 8.6, 13.5 / 16.1 s | 24.7, 10.3, 18.2 / 23.1 s |
| First call after load, start to `/health` | 11.7–11.9 s; 6.7–7.8 s (file in the OS cache) | 12.4–13.2 s; 8.8–9.3 s |
| Battery (484 calls) | 72 min | 105 min (partly throttled, §1.1) |

- **A fixed cost per prompt dominates.** Prompt time is about 4.5–5 s plus 3–4.5 ms per token in `llama-bench` (pp128 to pp512),
  and 5–7 ms per token in the server's own timings (a robust line fit over each battery's 484 calls: about 5.0 s + 5.1 ms per token
  for Qwen3-30B-A3B, 4.5 s + 7.2 ms for Gemma 26B-A4B). With op-offload the per-token cost is low (pp512 at 70–88 tokens/s), but
  short prompts gain little: pp128 runs at only 23–27 tokens/s. That pattern fits llama.cpp copying
  the RAM-resident expert weights to the GPU for each prompt batch [V; I].
  - Without op-offload the CPU does the work at 12–13 tokens/s, so leaving op-offload on (the default) is right [V].
  - A Qwen3-30B-A3B Pick (7 output tokens) spends 5.7–6.0 s (p50) of its 6.5–6.6 s in prompt processing (Gemma 26B-A4B: 5.6–6.1
    of 7.1–7.5 s), so offload suits few, long calls (one Fill per
    record, one explanation) far better than k = 3 Picks, as doc 47 §2.5 suspected [V; I].
- **Generation is 4–8 tokens/s, not 16–25.** Doc 47's community reports ran on desktop CPUs, with a CUDA build and a 2-bit file on
  the GTX 1070 and a fork on the GTX 1080 [V per doc 47]. Here the laptop CPU with dual-channel DDR4-2400, under contention, is the
  likely limit: CUDA raised MoE generation only 1.29× (§3.3) [I].
- **`--cpu-moe` is the better default on this card** [V; I]:
  - Speed: the same, within noise.
  - VRAM: 1.6 GB (Gemma) to 2.9 GB (Qwen) less.
  - Headroom: 2.3–3.4 GB of VRAM stays free at the worst desktop reading seen, against 0.5–0.7 GB at the tuned N (and 366–490 MiB
    at the batteries' peaks).
  - Not checked: the battery itself did not run at `--cpu-moe`. Placement should not change answers beyond numeric noise, but that is
    unverified (Open question 3).

**Memory during the batteries:**

| Measure | Qwen3-30B-A3B-2507 | Gemma 4 26B-A4B |
| --- | --- | --- |
| Whole-card GPU peak (free of 8,061) | 7,695 MiB (366) | 7,571 MiB (490) |
| Server working set: after load → peak | 5,838 → 17,227 MiB (mostly the memory-mapped experts) | 5,293 → 14,782 MiB |
| Server private bytes | 5,420–6,359 MiB (5,495–5,593 with `--cache-ram 0`) | 5,206–6,033 MiB |
| Machine's available RAM: minimum / median | 1,655 / 2,812 MiB | 3,391 / 5,254 MiB |
| Hard page reads (5 s samples): median / p90 / max | 1 / 76 / 3,431 per s | 3 / 95 / 1,689 per s (3,017 during tuning, before the battery) |

- **No RAM headroom next to a normal desktop.** One Qwen3-30B-A3B episode (about 4 minutes) came from another process's memory
  growth: the model's pages were paged back in from the hard disk at up to 3,430 reads/s, and that job's p50 rose from 6.6 to 7.5 s.
  Answers were unaffected [V].
- **Precondition missed.** The plan asked for at least 20,000 MiB available before loading Qwen3-30B-A3B; there were 19,193 and
  19,378 MiB before the two battery servers (18,533–19,604 across the tuning loads), the rest held by the user's own
  applications. The run proceeded under the 2,000 MiB stop rule [V].
- **For users:** a 30B-class offload model on a 32 GB machine wants the model file on an SSD and few other large applications
  open [I].

### 3.3 CUDA 12.4 vs Vulkan, same source [V]

`llama-bench` runs alternated between the builds, with no server running. The first CUDA run per model was discarded: the build
carries Pascal kernels only as PTX, which the driver compiles on first use. That took 105 s for Qwen3.5-4B, 38 s for Gemma 4 E4B QAT
and 97 s for Qwen3-30B-A3B, and left a 68.7 MB cache for the three models.

| Model (placement) | pp512 Vulkan → CUDA (×) | pp2048 (×) | tg128 (×) | GPU memory added, Vulkan / CUDA |
| --- | --- | --- | --- | --- |
| Qwen3.5-4B Q4_K_M (GPU) | 400 → 727 (1.82) | 376 → 705 (1.87) | 34.0 → 35.8 (1.05) | +3,229–3,307 / +3,339–3,389 MiB |
| Gemma 4 E4B QAT (GPU) | 466 → 777 (1.67) | 384 → 717 (1.87) | 43.6 → 36.7 (0.84) | +3,191–3,212 / +3,274–3,284 MiB |
| Qwen3-30B-A3B-2507 (`-ncmoe 39`, high priority) | 63.5 → 152.6 (2.40) | — | 4.12 → 5.31 (1.29) | +4,317–4,323 / +4,392–4,426 MiB |

**Server Pick control:** Qwen3.5-4B, `pick/none`, 90 paired calls, same flags and sampler, run back to back in one session.

| Build | Warm p50 / p90 | Prompt eval p50 | Uncached prompt tokens/s | Generation tokens/s | Right calls | Start to `/health` |
| --- | --- | --- | --- | --- | --- | --- |
| Vulkan | 1,220 / 1,550 ms | 866 ms | 183 | 37.3 | 84 of 90 | 9.8 s |
| CUDA 12.4 | **724** / 874 ms | 385 ms | 424 | 37.0 | 85 of 90 | 17.9 s (compile cache hit) |

- **Quality: no detectable difference.** The same letter on 87 of 90 calls; 2 calls right only on CUDA, 1 only on Vulkan; no menu
  differs by majority (McNemar p = 1.0). Only Pick was checked on CUDA [V].
- **Where the gain is.** CUDA was faster on 89 of 90 calls, with a median per-call ratio of 0.61. The gain is all prompt processing.
  That closes most of doc 46's gap to Ollama's 700 ms (doc 46 guessed Ollama used CUDA) [V; I].
- **Dense generation has no consistent winner.** The CUDA runs sat in the driver's P2 compute state at a 3,802 MHz memory clock,
  against P0 at 4,006 MHz for Vulkan, and CPU load made generation noisy (Vulkan Qwen 30.2–38.4 across runs) [V].
- **Contention.** One default-priority Vulkan MoE run at 98.5% system CPU fell to pp512 25.5 and tg128 1.25 tokens/s. It is kept only
  as a contention record [V].

### 3.4 The host prompt cache [V]

With the default `--cache-ram 8192`, `llama-server` keeps up to 8 GiB of past prompt states in RAM. The server log showed it making
room for new cache entries throughout the batteries.

| Setup | Private bytes: first job → end of battery |
| --- | --- |
| Qwen3-4B-2507 | 4.5 → 9.4 GB |
| Spark-X2.5-4B | 4.2 → 11.9 GB |
| Qwen3.5-4B, one 90-call job (both controls) | to 8.5–8.7 GB |

`run.py` reshuffles options per sample, so repeated menus reused only about 60–120 cached prompt tokens and the cache bought
almost nothing. On Qwen3-30B-A3B it grew private memory by 0.9 GB in 145 calls and pushed available RAM to the stop line. With
`--cache-ram 0` private memory stayed flat. Product prompts are more prefix-stable than this harness's, so a small cache may still
pay; that is untested (Open question 7) [V; I].

## 4. Significance and limits

- **Tests.** Menus and records are the unit: majority of k = 3 per item. Exact two-sided McNemar on discordant items; a paired item
  bootstrap (10,000 resamples, fixed seeds) for per-call differences; Holm within each family:
  - Pick family: 32 tests (4 new models × 2 baselines × `pick` / `pick-hard` × none / cards).
  - Fill family: 8 tests.
  - Graded family: 24 tests (pass in both samples, computed for this doc).
  - Secondary, not in the headline: pick and harder menus pooled per condition (60 items, 16 tests) and the two controls.

  Treating the Pick and Fill families as one family of 40 changes nothing [V].
- **Nothing survives Holm.** The smallest adjusted p is 0.125 (Qwen3-4B-2507 against Gemma E4B QAT on Fill). The pooled secondary
  family's smallest raw p is 0.0078 (0 : 8 against Gemma E4B QAT without cards, for both Qwen3-4B-2507 and Spark), still not Holm-
  significant [V].
- **The instruments cannot see moderate effects.**
  - The largest discordant count in any comparison was 8.
  - A 3:1 split reaches p < 0.05 only from 20 discordant items, 80% power at a true 3:1 ratio needs about 30, and surviving Holm's
    first step in the 32-test Pick family needs 44, which 30 menus can never supply. Every comparison is flagged for this in the CSV.
  - So "no detectable difference" here means exactly that, not equivalence. The bootstrap intervals quoted above are unadjusted
    (doc 46 §3, doc 46 OQ8) [V; I].
- **Samplers differ between arms.** Each arm uses its vendor's non-thinking values (§1.4), so a difference mixes model and sampler.
  Qwen3-4B-2507's near-identical Fill samples (10 of 12 items identical) point to how peaked its recommended sampler is [V; I].
- **Graders.** One LLM pass per model, with no calibration across passes; the baselines' grades come from doc 46's passes. The graded
  comparisons are descriptive [V].
- **One machine, a laptop CPU, a busy desktop.**
  - Offload speed depends on RAM bandwidth, CPU and disk; this machine has a 2016 laptop CPU, DDR4-2400 and a hard disk for models.
  - Contention and throttling inflated some latencies, recorded per run in the CSV notes.
  - Dense rows and baselines ran in different sessions (about 20% latency drift, §3.1) [V; I].
- **Flag differences on the offload rows.** `--n-cpu-moe`, `-t 4` and `--cache-ram 0` are placement and memory flags; they should
  change speed only. Their numeric effect on answers was not isolated [I].
- **Small n and our own instruments.** 30 menus per suite and condition, 12 Fill records, 10 findings, 10 text slots and 12
  knowledge tasks, all written by this project (doc 46 §3) [V].
- **Tooling caveats for the `tools/local-qual` patch** (not fixed here; the tool stayed unchanged):
  - **Possessive names.** `score.py`'s name check treats "Dravec's" as a name outside the allowed list, because its token pattern
    keeps the apostrophe. This cost Spark one text line. A fix should strip a trailing `'s` before comparing, with a regression test.
  - **Default output path.** `score.py` writes its CSV to `tools/local-qual/results/summary.csv` unless `--csv` is passed, so
    re-scoring elsewhere must pass both `--csv` and `--json`.
  - **No NuExtract adapter.** `run.py` has no template adapter for NuExtract (doc 47 §6.4) [V].

## 5. Implications

### 5.1 For D022: runtime variants and CUDA as a downloadable option [I on V]

- **Offer the upstream CUDA 12.x build on NVIDIA cards.** This is the measurement D022's amendment item 2 waits for. On this Pascal
  card CUDA cut warm Pick latency by about 40% and prompt time by 1.7–2.4×, with no detectable change in answers. Proposal:
  - **Shape.** An optional, user-started download (D008) of the upstream `llama-bNNNNN-bin-win-cuda-12.x-x64.zip` plus its `cudart`
    zip, pinned by build tag and both SHA-256 digests like the Vulkan build, and never bundled or redistributed by Plotroom (doc 13
    §7).
  - **Card generations.** Cards below compute capability 7.5 (Pascal, Volta) need the 12.x asset, because CUDA 13 dropped them
    (doc 47 §1.3) [V per doc 47].
  - **UI.** Show the cost: 645 MB against 32 MB, about 1.2 GB unpacked, and a one-time "preparing GPU kernels" wait of 40–105 s per
    model on older cards.
  - **Kernel cache.** Point the CUDA kernel cache (`CUDA_CACHE_PATH`, `CUDA_CACHE_MAXSIZE`) at Plotroom's own data folder so the
    compile happens once.
- **Make the runtime variant part of the setup identity.** A setup is (model file, quant, template, sampler, runtime build, backend)
  (D022 Consequences; DG012).
  - **Transfer rule.** A badge measured on Vulkan may carry over to CUDA for the same file after a spot check. This run's Pick control
    (87 of 90 same answers) is the template; Fill and explanations were not re-checked on CUDA, so DG012 should say which suites the
    spot check needs.
- **Pin `--cache-ram` explicitly** (by analogy with D022 amendment item 5, under which build defaults are never relied on for
  samplers). The default 8 GiB host prompt cache cost 5–8 GB
  of RAM with no gain in this harness and threatened the offload rows. Proposal: 0 for offload models, and a small measured value
  for dense ones.
- **Offload placement.**
  - **Default:** `--cpu-moe` on 8 GB cards. Tuning N bought no measurable speed here.
  - **Fit:** show two numbers, VRAM and host RAM (with the memory-mapped working set, 14.8–17.2 GB here), plus the prompt speed. This
    answers doc 47's open question 2.
  - **Margin:** the `llama-fit-params` projections missed by −310 to +580 MiB, so the Manager's fit check needs a measured margin, not
    the projection alone.
  - **Disk:** warn when the model file sits on a hard disk.
- **Forks stay out** (D022 amendment item 4): nothing here argues for managing the PrismML fork (§5.3).

### 5.2 For D023 and doc 14's tier table [I on V]

Proposed recommendations per hardware tier and step kind. All are candidates under D023 decision 2 until qualified; licences as D037
requires.

| Tier (machine) | Session model: Pick, harder menus, closed Fill fields, text | Heavy steps: whole-record Fill, card-backed explanations | Never local |
| --- | --- | --- | --- |
| **T1, 8 GB GPU** | Gemma 4 E4B QAT (once its licence tag is cleared) or Qwen3.5-4B, unchanged from doc 46; not Qwen3-4B-2507 or Spark-X2.5-4B (§2.1–§2.2) | The same model as a pre-fill the user confirms, or the cloud | Knowledge questions without cards |
| **T2b by offload: 8 GB GPU + 32 GB RAM (SSD advised)** | The same dense 4B model; an offload Pick takes 6.5–7.5 s against about 1 s, with no detectable gain | Opt-in **"bigger local model for heavy steps"**: Qwen3-30B-A3B-Instruct-2507 UD-Q4_K_XL at `--cpu-moe` (Apache-2.0 in card and GGUF; its answers were measured at `--n-cpu-moe 39`, Open question 3); Gemma 4 26B-A4B QAT scores higher on harder menus (level on Fill) but is blocked by the same licence-tag mismatch as E4B QAT | As above |
| **T1-cpu (no usable GPU)** | Unmeasured: No AI or bring-your-own (doc 47 §6.3 item 5) | Cloud | As above |
| **Any NVIDIA tier** | Optional CUDA 12.x build for speed (§5.1) | Same; it may bring offload Fill closer to the 10 s bar (untested) | — |

- **The switch is a visible role binding, not an automatic escalation.**
  - **Binding.** D023 item 3 forbids silently moving a step to another model. The switch binds the role that the heavy steps declare
    (D024) to the offload setup, with its latency and memory shown before the user accepts.
  - **Swap cost on 8 GB.** Only one model fits at a time as tuned here: loading the offload model takes 7–9 s from the OS cache, and
    its first call about 12 s.
  - **Open.** Whether a dense 4B model and a `--cpu-moe` offload model can stay resident together (about +4.7–6.6 GB of VRAM by the
    measured deltas, against 5.2–5.8 GB free after the desktop) is Open question 4.
- **Doc 47 §6.3 decision rules, applied:**
  - **Item 1 (the 8 GB default).** Unchanged. Both dense candidates sit 13–20 points of harder-menu pass^3 below Gemma E4B QAT,
    beyond doc 44's 10-point noise rule, and far below it on Fill validators (0.67 and 0.75 against 0.97). The offload models are
    not 8 GB-only candidates.
  - **Item 2 (the equal alternative).** Qwen3-4B-2507 matched Qwen3.5-4B on Pick and explanations within noise but qualified fewer
    Fill fields (`target` 0.00, `size` 0.50), so it does not take the slot.
  - **Item 3 (an offload recommendation).**
    - Fill pass^3 ≥ 0.8: met by both offload models.
    - No regression on harder menus: met by Gemma 26B-A4B. Qwen3-30B-A3B's pass^3 sits 13 and 7 points below Gemma E4B QAT's
      (level with Qwen3.5-4B). By the 10-point rule used for item 1 that is a regression without cards, although the paired test
      does not detect it (0 : 4, p = 0.125, §2.1). The opt-in switch below leaves Picks on the session model, so it would not reach
      users of the switch.
    - Warm Fill p90 ≤ 10 s: missed on Vulkan (16.1 and 20.1 s).
    - Outcome: under the pre-set rule, **no default offload recommendation yet**. The opt-in switch above is a proposal for the owner
      that relaxes the latency bar for users who choose it; a CUDA re-run may meet the bar (Open question 2).
  - **Items 4 and 5 (NuExtract3, CPU Pick).** Not run.
  - **Item 6 (must-pass escapes).** Met only with cards, by the two Gemma setups (§2.1).
- **Update to doc 14 §6** (for a later fold): the T2b row's "Gemma 4 26B-A4B as the faster MoE option" is now measured on the
  offload path of an 8 GB card, 6–25 s per call (warm p50) on Vulkan. Qwen3-30B-A3B-2507 joins it, and Qwen3.8-27B remains unmeasured.

### 5.3 Doc 47 shortlist status [V; I]

| Doc 47 row | Status after this run | Verdict (proposal) |
| --- | --- | --- |
| 1 Qwen3-4B-Instruct-2507 | Measured | Not adopted. Fastest 4B; explanations qualified; below the defaults on harder menus and Fill span copying |
| 2 Qwen3-30B-A3B-Instruct-2507 | Measured (offload) | Candidate for the heavy-step switch (licence clean); too slow for Picks; Fill p90 over the bar on Vulkan |
| 3 Gemma 4 26B-A4B QAT | Measured (offload) | Best or joint-best point estimates on most step kinds; licence tag blocks a recommendation; slowest per call |
| 4 NuExtract3 | Not run (pinned, not downloaded) | Needs the template adapter; no cloud host, so local under D044 P5 as written |
| 5 MiniCPM5-2B | Not run (pinned, not downloaded) | No cloud host; waits for the D044 ruling |
| 6 Qwen3.5-2B (CPU) | Not run (pinned, not downloaded) | Featherless-only host; CPU latency is local by nature |
| 7 Granite-4.0-H-1B, Granite-4.0-1B (CPU) | Not run (pinned, not downloaded) | No cloud host; the doc 53 ladder covers the same family |
| 8 Granite-4.0-H-Tiny (CPU) | Not run (pinned, not downloaded) | No cloud host |
| 9 Spark-X2.5-4B (1.7B sibling) | 4B measured; 1.7B not run | 4B not adopted: false escapes, `target` 0 |
| Carry-overs: Gemma 4 E2B QAT, Granite 4.2-3B | Not run (pinned, not downloaded) | E2B: Featherless-only; Granite 4.2-3B: no-schema cloud arm only |
| Optional: Bonsai 2 27B probe | Not run, not downloaded | Watch; bring-your-own only (fork); cloud screen first (D044) |

What this run unblocks: D044's amendment lands the `tools/local-qual` cloud backend after doc 49's run, and doc 48's round 1 waits for
these results. The Gemma 26B-A4B settings here are the local arm of doc 48's round-0 pairing Z09. Whether the deferred rows still
belong to "doc 49's run" before those steps go ahead is for the owner (Open question 1) [V per D044, doc 48; I].

## Open questions

1. **D044 and the deferred rows (owner).** Most deferred rows have no same-weights cloud host (§1.2). Do they go local directly under
   P5 as written and doc 53's reading, or wait? And does the cloud-backend patch wait for them?
2. **Does CUDA bring offload under the 10 s Fill p90 bar?** Re-run Fill and explanations for Qwen3-30B-A3B-2507 at `--cpu-moe` on the
   CUDA build. The 2.4× prompt speed-up suggests it may [I].
3. **Does `--cpu-moe` change answers?** A paired spot check (harder menus and Fill) against the tuned-N records.
4. **Can a dense session model and a `--cpu-moe` offload model stay resident together on 8 GB?** Measured deltas suggest +4.7–6.6 GB
   of VRAM against 5.2–5.8 GB free after the desktop. That would remove the swap, but host RAM would be tighter still.
5. **Which licence governs the Gemma QAT GGUFs** (26B-A4B as well as E4B): the card's Apache-2.0 or the file's `gemma`? Google's own
   26B-A4B QAT Q4_0 file was not read (D037; doc 46 OQ3).
6. **Can the fixed offload cost per prompt be amortised,** for example by batching several Picks into one prompt batch across the four
   slots, a larger `-ub`, or keeping short prompts under the op-offload threshold? [U]
7. **What `--cache-ram` should the sidecar pin,** and do prefix-stable product prompts get real reuse from a small cache?
8. **Would a field description fix span copying** (for example "the object only, as written") for Qwen3-4B-2507 and Spark? That is a
   harness fix to test before ruling a model out for Fill.
9. **Grader calibration.** The explanation gap to Gemma E4B QAT (3–4 findings) repeats across all four new models but comes from
   separate grader passes. A calibrated re-grade would settle whether it is real.
10. **A bigger instrument** (doc 46 OQ8): at 30 menus even a 7 : 0 split does not survive Holm across 32 tests.

## Sources

**Repository docs.**

- `docs/research/44-local-model-qualification-spike.md`: §2, §4, §5.1, §6 (bars and the noise rule).
- `46-llamacpp-huggingface-and-ud-quant-spike.md`: §1.4, §2.4–§2.6, §3, §4.1–§4.2; its llama.cpp records are this doc's baselines.
- `47-small-model-landscape.md`: §1.3, §2.5, §2.7, §6.1–§6.4, open questions 2 and 8;
  [`data/slm-test-shortlist.json`](data/slm-test-shortlist.json) (pins, flags and the `bonsai` block).
- `48-cloud-providers-and-harness-uplift.md` (round 0, Z09; the round-1 deferral).
- `50-free-llm-services-and-cloud-first-screening.md` §5 and [`data/cloud-screening-candidates.csv`](data/cloud-screening-candidates.csv).
- `53-how-small-can-we-go.md` (TL;DR: its reading of D044 P5).
- `13-local-inference-in-rust.md` §7.
- `14-model-selection.md` §6.
- `21-agent-doctrine.md` §12.3.
- [D008](../decisions/D008-outbound-network-sources.md), [D022](../decisions/D022-local-inference-and-model-manager.md) (amendment
  items 2, 4 and 5), [D023](../decisions/D023-model-strategy.md) (decisions 2–4 and the amendment),
  [D024](../decisions/D024-effort-autonomy-role-binding.md), [D037](../decisions/D037-model-manager-recommended-list.md),
  [D044](../decisions/D044-cloud-first-model-screening.md) (P1–P5 and the amendment),
  [DG012](../design-gap-requests/DG012-requalification-triggers.md).

**Tools and data.**

- `tools/local-qual/README.md`, `run.py`, `score.py` and `suites/{pick,pick-hard,fill,explain,text,knowledge}.json`, all unchanged.
- [`data/local-shortlist-results.csv`](data/local-shortlist-results.csv): this doc's aggregates, flags, pins, memory, speed and
  tests.
- `data/runtime-quant-comparison.csv`: doc 46's.

**Releases and model repositories** (read 2026-09-27):

- <https://github.com/ggml-org/llama.cpp/releases/tag/b11146>: the Vulkan and CUDA 12.4 assets and their listed SHA-256 digests.
- <https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF>, <https://huggingface.co/XHToken/Spark-X2.5-4B-GGUF>,
  <https://huggingface.co/unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF>, <https://huggingface.co/unsloth/gemma-4-26B-A4B-it-qat-GGUF>:
  revisions and hashes in §1.3; the files of the deferred rows are pinned in the CSV and doc 47 Appendix A.
- Model cards and `generation_config.json` for the samplers: `Qwen/Qwen3-4B-Instruct-2507`, `Qwen/Qwen3-30B-A3B-Instruct-2507`,
  `google/gemma-4-26B-A4B-it`, `XHToken/Spark-X2.5-4B`.

**Runtime facts.**

- `llama-server --version` and `--list-devices`; `GET /props`; `POST /apply-template`; the server's `print_timing` log lines.
- `llama-bench -o jsonl`; `llama-fit-params`.
- `nvidia-smi` (memory, clocks, P-states); Windows performance counters for process memory, page reads and CPU load.

**Statistics.**

- Exact McNemar (binomial on discordant pairs).
- Holm's step-down procedure: S. Holm, *Scand. J. Statist.* 6 (1979) 65–70.
- The percentile bootstrap: B. Efron, *Ann. Statist.* 7 (1979) 1–26.
- pass^k as in doc 44.

## Verification notes

### 2026-09-28, author checks at write-up

- **Scores and tests.** Every accuracy, pass^k, majority, escape, Fill, text and latency figure comes from `score.py`'s summary over
  this run's raw files and doc 46's (91 groups, 0 errors). Every code-scored paired test comes from the run's significance output,
  which checked equal seeds and option orders in every pair. The graded family (24 tests), the escape counts and the PW04 counts
  were recomputed from the grade files and raw records for this doc.
- **Grades.** Pass, partial, fail, hallucination and pass-in-both counts were recounted from the six grade files, four new and doc
  46's two. The baseline recount matches doc 46 §2.5's table.
- **The CSV** was generated by script from those outputs: 3,199 data rows, counted with Python's `csv` module. The script refuses to
  write if a local path or user name appears.
- **Pins.** The repository, revision, size and SHA-256 of the four run files were re-read from the fetch manifest (each entry
  `verified`, local hash equal to the pinned one) and match §1.3; the licence fields come from the GGUF headers. The CUDA zips were
  re-hashed during the run's preparation and equal GitHub's listed digests; GitHub's listed digest for the Vulkan zip equals doc 46's.
  A file listing of the model drive confirmed that the deferred rows' files were never fetched.
- **Hygiene.** This doc and the CSV were searched for local paths, user names and private project names; none were found. Server
  arguments appear with `-m <gguf>` or the file name only.
- **A local side effect, recorded.** One scoring call omitted `--csv` and overwrote the git-ignored
  `tools/local-qual/results/summary.csv` with the two baselines' rows. `summary.json` there is untouched and can regenerate it.
  Nothing tracked changed.
- **Not verified.**
  - Any battery at `--cpu-moe` or on the CUDA build beyond Pick.
  - Host RAM of doc 46's baseline runs.
  - A cold load of an offload file from disk.
  - Google's QAT files.
  - Any machine other than this one.
  - The deferred rows.

### 2026-09-28, independent review

- **Recomputed, not copied.** The reviewer's own scripts re-derived these from the raw call records (this run's and doc 46's) and
  the suite files rather than from the run's summaries, and all matched:
  - every cell of §2.1's accuracy, pass^3, majority and escape table;
  - all 32 Pick and 8 Fill paired tests: discordant items, exact McNemar, Holm, and equal seeds and option orders in every pair;
  - the Fill table, with a re-implemented scorer: all fields, pass^3, field and per-field accuracy, quote check;
  - PW04, HA03, the category and per-letter figures, and the random and first-option controls;
  - the two controls: 90 of 90 and 87 of 90 same letters, 89 of 90 calls faster, median ratio 0.61, latencies and speeds;
  - 2,116 records with 0 errors, 0 parse failures and 0 thinking characters.

  Bootstrap intervals re-drawn with other seeds agree within about 0.03.
- **Grades.** Every §2.3 cell and the 24 graded paired tests (smallest raw p 0.0625, every Holm value 1.0) were recounted from the six
  grade files and match.
- **Speed, memory, CUDA.** §3.1–§3.3 were checked against the per-call timings, the performance and backend-benchmark outputs, the
  server start records and the memory traces. §3.3's table, compile times and cache size match.
- **Fixed in this review.**
  - **Prompt fixed cost.** "5 s plus 3–4 ms per token" matched `llama-bench` only. The server's timings fit 4.5–5.0 s plus 5.1–7.2
    ms per token (a Theil–Sen line over 484 calls per model). The TL;DR and §3.2 now give both. The "7-token Pick" sentence now
    names its model and adds Gemma's figures.
  - **Gemma 26B-A4B memory row.** The trace statistics had included the tuning loads before the battery. Battery-only values are an
    available-RAM median of 5,254 MiB (was 5,313) and page reads of p90 95 and max 1,689 per s (was 90 and 3,017). The CSV's seven
    memory-trace rows for this model were corrected the same way.
  - **Qwen3-30B-A3B figures.**
    - Available RAM before load: 19,193 and 19,378 MiB for the battery servers (18,533–19,604 across tuning), not 18,527–19,378.
    - Private bytes with `--cache-ram 0` peaked at 5,593 MiB, not 5,537.
    - `llama-fit-params` over-read by 65–310 MiB, not 120–300; §5.1's margin now reads −310 to +580.
  - **Qwen3-4B-2507.**
    - Its Fill samples were identical on 10 of 12 items, not on every item (§2.2, §4).
    - The six harder menus it missed by majority in both conditions are now all named.
    - The TL;DR's `target` description now matches §2.2.
    - §3.1: its Pick lead (−20%) is about the size of the session drift; only its generation lead (+32%) exceeds it.
  - **Comparative wording.**
    - §2.1's offload bullet no longer says "level with the defaults": Qwen3-30B-A3B is 13 and 7 points below Gemma E4B QAT on
      harder-menu pass^3.
    - A new §2.1 bullet lists the other unadjusted per-call intervals that exclude 0, two of them in Gemma 26B-A4B's favour against
      Qwen3.5-4B.
    - §5.2 item 3 now applies item 1's 10-point rule consistently.
    - The TL;DR and §5.3 say Gemma 26B-A4B has the best or joint-best point estimates on most step kinds, not on all, and its
      "scores higher" than Qwen3-30B-A3B (TL;DR, §5.2) now says where: on harder menus, level on Fill.
  - **Citation.** D022 item 5 is about sampler defaults, so the `--cache-ram` proposal now cites it by analogy, not as a quote.
  - **Smaller figures.**
    - CPU smoke: 12–15 prompt tokens/s (was "about 13").
    - "6–25 s per call" is the warm p50.
    - The T2b cell gives offload Pick times instead of "adds 6–7 s" and notes that the answers were measured at N = 39.
    - §3 has a units note: memory "GB" figures are thousands of MiB.
  - **Hygiene.** One CSV note named a commercial endpoint-security product; it now says "a second endpoint-security agent".
- **Hygiene search.** No local paths, user names or private project names were found in this doc, the CSV, doc 47 or
  `docs/README.md` (URLs excluded from the drive-letter pattern).
- **Checked and unchanged.**
  - The pins and sizes, against the fetch manifest.
  - The deferred rows' files, absent from the model folder.
  - The mid-row server changes (record 56; 11 kept records).
  - The D044 and doc 50 cross-references.
  - §4's power figures: 20 discordant items, 80.3% power at 30, and 44 for Holm's first step.
  - The tier recommendations, which follow from the data once item 3's wording is fixed.
- **Not verified by the review.**
  - The grader's verdicts themselves (recounted, not re-graded).
  - The debris and "reordered place span" examples beyond the grade files' notes.
  - The vendor sampler sources.
