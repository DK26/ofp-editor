# Small-model landscape: candidates beyond the first spike

Research doc 47 for Plotroom (`ofp-editor`). Research date: 2026-09-27. Audience: contributors and LLM coding agents. This file is
meant to be read on its own.
Question answered: which small or locally runnable models, released or updated in 2025–2026 and not yet covered by docs 14 and 44, are
worth measuring next for Wilco's step kinds; which helper models (embedders, rerankers, speculative drafters) could sit beside them; and
what the next `tools/local-qual` run should contain.

**Status.** Research only. No model was loaded or run for this doc. Measurements quoted from doc 44 are Plotroom's own; every other
quality number is public and mostly vendor-reported. Verdicts, fit scores and the test plan are proposals [I]. No candidate here is
claimed to be better than a measured model: the most any row can say is "candidate to test".
**Epistemic legend** (doc 14's): **[V]** verified against the cited primary source; **[V-vendor]** the vendor's or author's own
number about its own model, quoted correctly but not independently checked; **[V per doc N]** taken from a sibling doc; **[I]** our
inference or proposal; **[U]** unknown. Web sources are cited as [S1]…[S85] and listed under §Sources.
**Data.** One row per model in [`data/slm-candidates.csv`](data/slm-candidates.csv) (53 rows; columns `name, vendor, hf_repo,
params_total, params_active, arch, release, license, license_ok_to_recommend, context, gguf_q4_size_gb, llamacpp_support, tool_calling,
thinking_toggle, tier, fit_pick, fit_fill, fit_draft, fit_explain, fit_multilingual, verdict, sources`). The four models doc 44 measured
are included as `baseline` rows so the table can be read on its own.
**Relation to sibling docs.** Doc 14 picks the model tiers and names the first candidates; doc 13 the runtime (llama-server sidecar);
doc 16 the decision models and the `Selector` seam; doc 21 and doc 25 the step shapes; doc 44 the first measurement on real hardware.
D022 accepts the Model Manager and D023 the tiers and the licence rule (decision 6). This doc widens the candidate list and plans the next
measurement; it does not change any decision.
**Hygiene.** Public sources only. No game content, no private projects.

**Step-kind names.** This doc uses the research brief's five step kinds: PICK, FILL, COMPOSE, DRAFT, EXPLAIN. **Naming clash:** here
DRAFT means creative text (briefings, radio lines, character lines, story beats, and their translation). In docs 21 §3.1, 25 §5.1 and 38
§3.2, "Draft" is a different shape, a multi-entity ChangeSet ("add a rescue branch"), and creative text is a Fill (one paragraph) or a
Compose (one radio exchange) bound to the `writer` or `translator` role. The CSV keeps the brief's column name `fit_draft` with the
creative-text meaning. Open question 1 asks for a single name.

## TL;DR

- **No new model is proven better than doc 44's four; a handful are better-shaped candidates.** The best new T1 candidate is
  **Qwen3-4B-Instruct-2507**: Apache-2.0, non-thinking by construction (so doc 44's "thinking on by default" trap cannot occur), 2.50 GB
  at Q4_K_M, and the highest-scoring Apache-2.0 non-thinking instruct model near 4B on the official BFCL V4 table (Live Simple 79.07,
  Live Multiple 76.16, irrelevance 84.93) [V S1, S14]. Run it as a control arm against Qwen3.5-4B and Gemma 4 E4B QAT [I].
- **The real opportunity on 8 GB VRAM + 32 GB RAM is MoE expert offload.** llama-server keeps expert weights in system RAM
  (`--cpu-moe`, `--n-cpu-moe N`) [V S8], so a 26–35B model with 3–4B active parameters needs only about 3–5 GiB of VRAM [I]. Community
  runs on Pascal 8 GB cards: Qwen3.6-35B-A3B generated 25.78 tokens/s on a GTX 1070 (UD-IQ2_M, upstream build) [V S18]; Gemma 4
  26B-A4B used 3,299 MiB of VRAM plus 14,747 MiB of RAM at about 16 tokens/s with `--n-cpu-moe 29`, and about 20 tokens/s at
  `--n-cpu-moe 20`, the lowest value that fit an empty 8 GB card at 128K, on a GTX 1080 (a fork) [V S19]. This is the path doc 44
  §5.4 item 6 asks for, for whole-record Fill, Compose and creative text. Candidates: **Qwen3-30B-A3B-Instruct-2507** (Apache,
  non-thinking, BFCL V4 41.39%) and **Gemma 4 26B-A4B QAT** (14.25–14.44 GB; the best creative-writing evidence among local candidates,
  and strong Czech and Polish scores) [V S1, S5, S7, S21]. The risk is prompt processing: the GTX 1080 runs printed 50–67 tokens/s,
  but on 29–52-token prompts, which says little about throughput; the GTX 1070 run measured pp512 at 367 tokens/s [V S18, S19; I].
- **A per-step-kind mix beats one model only in a narrow form [I].** An 8 GB card holds one 3–4 GB model next to the desktop, and a swap
  costs 6–18 s (doc 44). So the realistic mix is one session model on the GPU, plus sub-1-GB helpers on the CPU (an embedder, perhaps a
  decision model in shadow), plus cloud or a visible switch to an offloaded MoE model for heavy Fill, Compose and creative text. A
  separate "tiny router" for PICK adds nothing while the session model already qualifies on Pick.
- **Generic function-calling specialists do not help a grammar-constrained harness [I on V].** Format is already solved (0 parse
  failures in 1,216 calls, doc 44). BFCL V4's overall score is 40% agentic and 30% multi-turn [V S2], which the harness removes. On the
  single-call columns, 3B specialists trail Qwen3-4B-2507 on Live Multiple (xLAM-2-3b 60.68, Hammer2.1-3b 71.32, Arch-Agent-3B 72.27
  against 76.16) [V S1], and most carry non-commercial or research licences.
- **Format-matched specialists are different and worth a test [I]:** **NuExtract3** (Apache, 2.78 GB, trained for verbatim span
  extraction) for the Fill spans no 3–4B model qualified in doc 44, and **decider** (Apache, 0.53–2.71 GB, calibrated letter
  probabilities) for PICK in shadow mode, which D023 decision 5 requires. The decider's own held-out score on generated menus is only
  0.43–0.56 [V-vendor S49].
- **Translation is the one place a small specialist clearly fits the design [I].** **Hy-MT2-7B / 1.8B** (Tencent) cover all 8 engine
  languages and have terminology, delimiter and structured-data prompt modes that match glossary injection and stringtable placeholders
  [V S41]. They are Apache-2.0 only at revisions from 2026-05-26; the release files excluded the EU [V S42]. Bielik (SpeakLeash) leads
  EuroEval Czech below 12B [V S7]. No independent Czech, Polish or Russian translation or creative-writing evaluation exists [U].
- **English creative text: no new model of 14B or less beats doc 14's Gemma 4 picks on public boards.** EQ-Bench has no 2026 small
  model at all; Gemma 4 26B-A4B leads EQ-Bench Longform among local candidates (50.7) [V S4, S5]. The best open writer found,
  Hemmingway-1 (Elo 1906.4), is 27B and CC-BY-NC [V S4, S60].
- **Helpers:** multilingual embedders (granite-embedding-311m/97m-r2, Qwen3-Embedding-0.6B, harrier-oss-v1-0.6b) are CPU-cheap but
  belong only in doc 25 §4.6's optional semantic tier, after beating BM25. A reranker in front of Pick conflicts with doc 25 §6.2's facet
  menus and D023 decision 5. Speculative drafters speed up long text, do nothing for one-token Picks, and showed no speed-up for Gemma's
  MoE in upstream tests [V S22] [I].
- **Bonsai 2 27B (owner question, §2.7): watch, not test-now.** It is an Apache-2.0 ternary retrain of Qwen3.8-27B that only
  PrismML's llama.cpp fork runs: mainline rejects its tensor types, and PrismML says the two compact packings "might stay in fork only"
  [V S76, S80]. Its smallest file (5,671 MiB) plus an 8K cache exceeds the ~5,490 MiB free on the reference card, and on a GTX 1070
  the fork's Vulkan build processed prompts at about 16 tokens/s, about 94 s for a 1,500-token prompt [V S74, S79; I]. The
  98.2%-of-FP16 figure is the vendor's, in thinking mode only and served through vLLM rather than the released GGUFs; an independent
  KLD run shows a retrained sibling of the base, not a lossless copy [V-vendor S74, S76; V S81]. At most an optional paired probe
  against a mainline Qwen3.8-27B UD-IQ2_XXS; the fork stays bring-your-own until upstream support lands [I].
- **Licences are the main filter for the recommended list.** 41 of the CSV's 53 rows (the four baselines included; the Bonsai rows by
  licence only, §2.7) are OSI-licensed and eligible under D023 decision 6, some with conditions such as a pinned revision or the
  ungated GGUF. Others are bring-your-own at most: LFM Open License (revenue-gated), NVIDIA Nemotron (notice and indemnity), Gemma
  Terms (TranslateGemma), CC-BY-NC (xLAM-2, Tiny Aya), Katanemo (derivative naming). Licences change between revisions, so the Model
  Manager must read the LICENSE at the pinned revision [V S42, S51; I].
- **Next run (§6):** nine models through `tools/local-qual` on llama-server, re-running doc 44's Gemma and Qwen baselines on the same
  runtime first. Four answer doc 44's open items on the reference box (Qwen3-4B-2507, Qwen3-30B-A3B-2507, Gemma 4 26B-A4B QAT,
  NuExtract3). Four probe the CPU and 4–6 GB tiers (MiniCPM5-2B, Qwen3.5-2B, Granite-4.0-H-1B, Granite-4.0-H-Tiny). One, added in
  the critic pass, is the newest Apache-2.0 4B challenger (**Spark-X2.5-4B**: vendor BFCL-V4 65.1 and IFEval 93.0, thinking mode only
  [V-vendor S63]). Doc 14's two unmeasured T1 names (Gemma 4 E2B, Granite 4.2-3B) ride along as carry-overs. §6.3 states which
  results would change the default recommendation.

## 1. What a local model has to do, per step kind

### 1.1 Requirements

| Step kind | What the model returns (docs 21, 25, 38) | Already owned by code or the grammar | Left to the model | Doc 44 evidence (3–4B, thinking off) | Model properties that matter [I] |
| --- | --- | --- | --- | --- | --- |
| PICK | One letter from ≤ 7 code-built options plus `X` none fit and `Q` ask me | Valid letters only; the menu is filtered by facts (whose passengers, which side); the escapes always exist | Which valid option fits the request | Qualified for 3 of 4 models, pass^3 0.83–0.93; the fact-bearing menu PW04 was missed 23 of 24 times | Prompt-processing speed (the answer is one token); instruction following on short prompts; using the escape on off-scope requests; letter probabilities for confidence |
| FILL | A small flat record: enums, bounded numbers, 1–3 short spans | Schema, enum values, the quote check (a span must occur in the request) | Judgement fields (`size`, `task`) and choosing the right span | No model qualified a whole record (best: Gemma, pass^3 0.58); 2–5 fields qualified per model | Span copying, judgement, a larger model for the whole record |
| COMPOSE | One sub-structure: a mission concept, one radio exchange, one node's transitions | Schema, validators, split into Fill and Pick on failure (doc 21 §3.3) | Coherence across 5–20 fields | Not measured; doc 21 puts the floor at T2 or cloud | 8B-class quality or more, so MoE offload on small GPUs |
| DRAFT (creative text) | A briefing paragraph, a radio body, a character line, a story beat; a translation | Word caps, the names list, digits, era words, codepage, callsign framing | Wording, tone, period voice, language | Code constraints qualified for 3 models; graders passed only 15–35% of lines as ready text | Writing quality; coverage of the 8 engine languages (doc 14 §2); translation |
| EXPLAIN | A two-sentence explanation of one finding, plus a fix, from a card | Which card is shown (D027 item 7); invented-command patterns; the checker on the fix | A faithful paraphrase of the card | Qualified with cards for Qwen and Granite; free-text knowledge without cards 0 of 24 for every model | Faithfulness to the context; few hallucinations; short output |

Sources: doc 21 §3.1–§3.3, doc 25 §5.1 and §6.2, doc 38 §3.2, doc 44 §2 and §4, D027 [V per docs].

### 1.2 What grammar-constrained decoding already solves, and what it does not

- **Shape is solved.** Doc 44's 1,216 calls had 0 parse or schema failures, with the schema enforced during decoding [V per doc 44].
  JSONSchemaBench found constrained decoding scoring at or above unconstrained generation (GSM8K 80.1% → 82.4% with llama.cpp) [V S12].
  "Let Me Speak Freely" found format restrictions help classification "due to the restriction on answer space" but hurt reasoning
  [V S13], so any reasoning stays outside the constrained answer, as doc 21 §3.2's short `why` field does [I].
- **So the vendor's tool-call format matters little.** Locally the harness sends one `response_format: json_schema` envelope per step,
  not native tools (doc 21 §3.1; `tools/local-qual/README.md`), so Hermes-style JSON, XML (`<function>`), Pythonic calls or Harmony
  channels mostly do not reach our path [I]. BFCL-style tool scores are at best an indirect signal (§3.1).
- **Not solved by the grammar:** which valid option is right (PW04), judgement fields, a span that passes the quote check but is the
  wrong text (Gemma quoted the finding code "CF01" as a place), and engine knowledge [V per doc 44].
- **New risks when choosing models:**
  - *Reasoning-only models.* LFM2.5-8B-A1B has no thinking switch and "assistant turns contain an explicit chain of thought before
    the final answer" [V S31]; Nanbeige4.1-3B's template has no `enable_thinking` [V S33]. A grammar that forbids the trace puts them
    off-distribution; one that allows it makes every Pick pay for it [I].
  - *Fixed blocks the grammar must allow.* With thinking off, Gemma 4 26B-A4B still emits an empty thought block [V S21]. gpt-oss uses
    Harmony channels, and grammars were reported to apply before llama.cpp strips the channel tags (August 2025; current state [U]) [S23].
  - *Fail-open.* llama-server was reported to log a grammar parse failure and continue **unconstrained** with HTTP 200 (issue #19051,
    closed 2026-03-09 by the stale bot as "not planned", so no fix is recorded there) [V S11]. Every output must still be validated
    (D009), and the sidecar supervisor should treat that log line as an error [I].
  - *Template quirks.* JSON Schema through `/v1/chat/completions` failed for Granite 3.1's role tokens while an equivalent GBNF worked
    (issue #29006, open since 2026-09-17) [V S28]; Granite 4.0 uses the same role tokens, so the Granite rows need a schema check [I].
    TranslateGemma's template needs its language codes passed as `chat_template_kwargs` (`source_lang_code`, `target_lang_code`;
    PR #19052, merged 2026-01-24, after which #19295 was closed as completed); a separate Jinja parser failure on the 27B (#20305)
    was closed as stale without a fix, with `--no-jinja` reported to work [V S45].
- **What matters when choosing** [I]: a thinking switch that works (or no thinking at all); a chat template that renders in llama-server
  `--jinja`; memory including the KV cache; instruction following on short prompts; coverage of the 8 engine languages; the licence.

### 1.3 Memory budgets

- **Reference box:** GTX 1070 with 8,192 MiB, of which the desktop already used about 2,700 MiB, leaving about 5,490 MiB; 32 GB of RAM
  [V per doc 44]. On llama-server's Vulkan build, Qwen3.5-4B UD-Q4_K_XL raised GPU use from 2,703 to 6,017 MiB at `-c 8192`
  (+3,314 MiB) [V per `tools/local-qual/README.md`].
- **File size is not fit; the KV cache decides a lot.** f16 KV bytes = (layers that keep KV) × (KV heads) × (head dim) × 2 × 2 B ×
  context. At 8K [I, arithmetic from each model's config, cited in the CSV rows]:

  | Model | Layers with KV × KV heads × head dim | KV at 8K, f16 |
  | --- | --- | --- |
  | Qwen3-4B-Instruct-2507 | 36 × 8 × 128 | 1,152 MiB |
  | Qwen3.5-4B / NuExtract3 (8 full-attention layers) | 8 × 4 × 256 | 256 MiB |
  | Spark-X2.5-4B (9 full-attention layers; 27 sliding-window 512) | 9 × 4 × 256, plus the windows | about 290 MiB, plus about 100 MiB |
  | Bielik-Minitron-7B | 40 × 8 × 128 | 1,280 MiB |
  | Olmo 3 7B (MHA, sliding window on 24 layers) | 32 KV heads | about 2.5 GiB |
  | Qwen3-30B-A3B (stays on the GPU under offload) | 48 × 4 × 128 | 768 MiB |
  | Granite 4.0 H models (4 attention layers) | 4 × 4 × 128 | 64 MiB |
  | Jamba2 3B (2 attention layers, 1 KV head) | 2 × 1 × 128 | about 8 MiB |

  Hybrid models (linear attention, Mamba, sliding windows) are cheap in KV, which matters on 8 GB cards and on CPU [I]. `-ctk q8_0`
  halves the K cache (llama-server accepts q8_0, q4_0 and others) [V S8].
- **llama-server fits by default.** `--fit` is on and adjusts unset arguments to fit device memory with a 1,024 MiB margin per device
  [V S8]. Measurements should set `-ngl`, `--n-cpu-moe` and `-c` explicitly and record the effective values [I].
- **Pascal:** CUDA 13 dropped compute capability below 7.5, so GTX 10xx cards need a CUDA 12.x build or Vulkan [V S24]. Plotroom's own
  builds are Vulkan, Metal or CPU (D022 decision 2).
- **Other machines [I]:** on Apple 16 GB unified memory, Gemma 4 26B-A4B QAT (14.4 GB) and the 35B-A3B models (22 GB) do not fit
  comfortably, while E4B-class models, LFM2.5-8B-A1B (5.2 GB) and Granite-4.0-H-Tiny do; 12–16 GB GPUs run Gemma 4 12B or the 26B-A4B
  QAT mostly on the GPU; 4–6 GB laptops get the 1–2B rows or a small MoE with offload; CPU-only machines get the 1–2B rows.

## 2. Candidates by tier

### 2.1 How to read the tables

- **Tiers** follow D023: T1 local small (about 16 GB of RAM; here split into *T1-cpu* for CPU-only or 4–6 GB VRAM and *T1* for an
  8 GB GPU), T2a (8–12 GB VRAM, dense 7–11B), T2b (16 GB VRAM and up, or MoE offload with 32 GB of RAM).
- **Fit scores** (P F D E M = PICK, FILL, DRAFT, EXPLAIN, multilingual; COMPOSE follows FILL and DRAFT) are 0–3 and are all [I]:
  0 not suitable or not a general model; 1 weak, unknown or mismatched evidence; 2 a plausible candidate with some evidence; 3 the
  strongest available evidence or a purpose-built design. For `baseline` rows the scores are read from doc 44's verdicts. Multilingual:
  0 = no Czech, Polish or Russian; 1 = claimed coverage without independent evidence, or weak evidence; 2 = covered with moderate
  independent evidence; 3 = the strongest independent evidence or purpose-built for translation.
- **Q4 file** is the Q4_K_M GGUF unless named otherwise; "UD" is Unsloth's dynamic UD-Q4_K_XL. Sizes are decimal GB from the Hugging
  Face tree API.

### 2.2 T1 on an 8 GB GPU

| Model (licence) | Q4 file | Params (active) | Thinking | Public evidence | P F D E M | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| **Qwen3-4B-Instruct-2507** (Apache-2.0) | 2.50; UD 2.55 | 4.02B | none (non-thinking only) | BFCL V4 FC overall 35.68%, Live Simple 79.07, Live Multiple 76.16, Non-Live Simple 75.50, irrelevance 84.93, multi-turn 22.12, mean latency 7.61 s [V S1]; IFEval 83.4, Creative Writing v3 83.5, WritingBench 83.4 [V-vendor S14]; two rival vendors' tables place it at or above their own models (AI21: average 0.53 against Jamba2's 0.52; Sber: 58.8 against GigaChat's 51.2) [V-vendor S32, S36]; not on EQ-Bench [V S4] | 2 2 2 2 1 | **Test now** (control arm) |
| **NuExtract3** (Apache-2.0) | 2.78 (official) | 4.33B text (Qwen3.5-4B base) | template default off | Built for verbatim span extraction; vendor table in reasoning mode only (§3.3) [V-vendor S47] | 1 3 0 0 1 | **Test now** (Fill only) |
| **Spark-X2.5-4B** (Apache-2.0; also 1.7B, 1.11 GB) | 2.60 (official; no UD) | 4.11B (hybrid: 1 full-attention layer per 3 sliding-window layers) | switch, default on (send false) | Created 2026-08-24; mainline since PR #27868 (merged 2026-09-06; card: build b10828 or later) [V S63]. Vendor table, all in thinking mode: BFCL-V4 65.1 against Qwen3.5-4B's 50.3 and Gemma 4 E4B's 36.9, IFEval 93.0 against 89.8 and 45.3 [V-vendor S63]; "more than 200 languages" claimed, not on EuroEval [V-vendor S63; V S7] | 2 2 1 1 1 | **Test** (priority B, row 9) |
| Nanbeige4.1-3B (Apache-2.0) | 2.44 (community) | 3.93B | always reasons (no switch) | Sibling Nanbeige4-3B-Thinking-2511 is the best ≤ 8B open model on BFCL V4 (51.40%), at 13.46 s mean latency against 7.61 s for Qwen3-4B-2507 [V S1] | 2 2 1 1 0 | Watch |
| Nanbeige4.2-3B (Apache-2.0) | 2.68 (community) | 4.17B (22 blocks looped twice) | switch, default on | Mainline llama.cpp since build b10153 (PR #25994, merged 2026-07-27) [V S33]; vendor numbers in thinking mode only; about twice the compute and KV of a 22-layer model [I] | 2 2 1 1 0 | Watch |
| Olmo 3 7B Instruct (Apache-2.0, research-and-education intent statement) | 4.47; UD 4.57 | 7.30B | none | Vendor BFCL 49.8 against Qwen3-8B's 60.2 [V-vendor S34]; full MHA, so about 2.5 GiB of KV at 8K [I]; English only | 1 1 1 1 0 | Skip |
| GigaChat 3.1 10B-A1.8B (MIT) | 6.47 (official) | 10B (1.8B) | none | Its own card's arena table puts Qwen3-4B-Instruct-2507 ahead (58.8 against 51.2) [V-vendor S36]; Russian and English only | 1 1 1 1 1 | Skip |
| LFM2.5-8B-A1B (LFM Open License) | 5.16; UD 5.35 | 8.47B (1.5B) | reasoning only | Vendor IFEval 91.84, BFCLv4 49.73 [V-vendor S31]; EuroEval Czech 3.80, near the bottom [V S7]; 10 languages, no CZ, PL or RU [V S31] | 1 1 0 1 0 | Skip (bring-your-own at most) |

### 2.3 T1-cpu: CPU-only, 8–16 GB of RAM, or 4–6 GB of VRAM

| Model (licence) | Q4 file | Params (active) | Thinking | Public evidence | P F D E M | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| **Granite-4.0-H-1B** (Apache-2.0) | 0.90; UD 0.91 | 1.46B (Mamba2 hybrid) | none | Vendor IFEval 78.53, BFCL v3 50.21 [V-vendor S27]; about 1.3 GiB with KV [I] | 1 1 0 0 1 | **Test** (CPU floor) |
| Granite-4.0-1B (Apache-2.0) | 1.02; UD 1.04 | 1.63B | none | Vendor IFEval 77.38, BFCL v3 54.82 [V-vendor S27]; Liquid's own table puts it above LFM2.5-1.2B on BFCLv3 (52.43 against 49.12) [V-vendor S30] | 1 1 0 0 1 | Test (paired with H-1B) |
| **Qwen3.5-2B** (Apache-2.0) | 1.28; UD 1.34 | 2.27B | switch; the card says non-thinking by default | Non-thinking IFEval 61.2 (78.6 thinking); BFCL-V4 43.6 in thinking mode only [V-vendor S29]; same family as doc 44's Qwen | 1 1 1 1 2 | **Test** (CPU) |
| **MiniCPM5-2B** (Apache-2.0) | 1.56 (official; no UD) | 2.52B | switch; unset lets the model decide | Vendor BFCL v4 66.6 against Qwen3.5-4B's 56.8, but IFEval 86.7 against 90.2, mode unstated [V-vendor S25]; English and Chinese only | 1 1 0 1 0 | **Test** (4–6 GB tier) |
| MiniCPM5-1B (Apache-2.0) | 0.69 | 1.08B | switch | EuroEval Czech 4.43, rank 41 [V S7] | 1 1 0 0 0 | Watch |
| **Granite-4.0-H-Tiny** (Apache-2.0) | 4.23; UD 4.07 | 6.94B (1B) | none | Vendor IFEval 81.44, BFCL v3 57.65 [V-vendor S26]; Liquid reports BFCLv4 28.52 and IFBench 21.28 for it [V-vendor S31]; 64 MiB of KV at 8K [I] | 2 1 1 1 1 | **Test** (CPU, 16 GB RAM) |
| Ling-3.0-tiny (MIT) | 4.82 (official) | 7.89B (1.3B; KDA + MLA hybrid, 128 experts) | switch, default on | Created 2026-08-10; mainline since PR #26608 (merged 2026-08-17) plus a dedicated chat parser (PR #28682); open issues: repeating slashes (#27876) and a tool-call terminator bug (#27462) [V S64]; benchmarks only as an image on the card; languages unstated | 1 1 0 1 0 | Watch (a 1B-active peer of H-Tiny once the bugs close) |
| AI21 Jamba2 3B (Apache-2.0) | 1.93 (community) | 3.03B (Mamba hybrid) | none | Vendor chart: average 0.52 against Qwen3-4B-2507's 0.53, FACTS tied at 0.54 [V-vendor S32]; languages unstated | 1 2 1 2 0 | Watch |
| LFM2.5-1.2B-Instruct (LFM Open License) | 0.73 | 1.17B | none | Vendor IFEval 86.23, BFCLv3 49.12; 719 MB on a phone CPU [V-vendor S30]; of the game languages only EN, FR, DE, ES; the card says 32K context [V S30] | 1 1 0 1 1 | Watch (bring-your-own) |

### 2.4 T2a: dense 7–11B (tight on 8 GB, comfortable on 12 GB)

| Model (licence) | Q4 file | Params | Public evidence | P F D E M | Verdict |
| --- | --- | --- | --- | --- | --- |
| Bielik-Minitron-7B-v3.0 (Apache-2.0; GGUF ungated) | 4.50 | 7.48B | EuroEval Czech 1.89 (Gemma 4 E4B 2.15, Qwen3.5-9B 2.23), Polish 2.33 (Qwen3.5-9B 2.26 is better) [V S7]; about 5,970 MiB at 8K f16, over the 5,490 MiB free on the reference card [I] | 1 1 2 2 3 | Test in the non-English suite |
| Bielik-11B-v3.0 (Apache-2.0) | 6.72 | 11.17B | EuroEval Czech 1.76 (Gemma 4 12B-it 1.84 ± 0.07), Polish 2.17 (Gemma 4 12B 2.07) [V S7]; Polish EQ-Bench 71.20 [V-vendor S39]; needs partial offload on 8 GB [I] | 1 1 2 1 3 | Test in the non-English suite (12 GB+) |
| EuroLLM-9B-Instruct-2512 (Apache-2.0) | 5.58 (community only) | 9.15B | EuroEval Czech 2.04, Polish 2.64 [V S7]; the card says it "has not been aligned to human preferences" [V S37]; 32K context | 1 1 1 1 2 | Watch |

Translation-only 7B models (Hy-MT2-7B, TranslateGemma, Seed-X) are in §3.5.

### 2.5 T2b by MoE expert offload (8 GB VRAM + 32 GB RAM) or 16 GB VRAM

**How offload works.** `-cmoe, --cpu-moe` keeps all Mixture-of-Experts weights in CPU memory; `-ncmoe, --n-cpu-moe N` does so for the
first N layers; `-ot` overrides the buffer type per tensor pattern [V S8]. Attention, shared weights and the KV cache stay on the GPU,
and each token touches only the routed experts, so a 3–4B-active model generates at a useful speed from RAM [I]. For Qwen3-30B-A3B the
experts are about 29.0B of the 30.5B parameters (48 layers × 128 experts × 3 × 2048 × 768), so with `--cpu-moe` the GPU holds about
1 GiB of weights plus 768 MiB of KV at 8K plus buffers, roughly 2.5–3.5 GiB, and RAM holds about 16–17 GiB [I, arithmetic on the
config in S15].

**Measured on Pascal 8 GB cards (community, not Plotroom):**

| Setup | Model and file | Result |
| --- | --- | --- |
| GTX 1070 8 GB, i7-4790, 16 GiB RAM, upstream master of 2026-05-26, CUDA 12.8, 64K context, q4_0 KV, MTP drafting; no `--n-cpu-moe` (llama.cpp's own fitting) | Qwen3.6-35B-A3B UD-IQ2_M (11.5 GB) | pp512 366.93 tokens/s, tg128 25.78 tokens/s; about 15 tokens/s at full context [V S18] |
| GTX 1080 8 GB, i7-6700, 32 GiB RAM, a fork with fork-only KV types, 128K context, `--n-cpu-moe 30` (29 ran out of memory) | Qwen3.6-35B-A3B Q4_K_M (40 layers) | 24.11 tokens/s; prompt 54.69 tokens/s on a 29-token prompt [V S19] |
| Same machine and fork, 128K context, `--n-cpu-moe 29` | Gemma 4 26B-A4B (non-QAT Q4_K_M, 30 layers) | GPU 3,299 MiB (model 2,103, context 664, compute 532), host 14,747 MiB, 15.64 tokens/s, prompt 52.74 tokens/s on a 52-token prompt [V S19] |
| Same, `--n-cpu-moe 20` (19 ran out of memory) | Same | 19.78 tokens/s, prompt 49.64 tokens/s on a 29-token prompt; memory not printed. With the MTP assistant at `--n-cpu-moe 20–21`, about 21–24.5 tokens/s and prompt 65–67 tokens/s; the target's GPU model buffer was 6,504 MiB [V S19] |

**Risk: prompt processing [I].** A Pick or Fill prompt with a card runs to hundreds or a few thousand tokens. If offload really
processed prompts at the GTX 1080 runs' 50–67 tokens/s, a 1,500-token prompt would take about 25 s before the first output token,
against about 385 tokens/s for the dense 4B on Vulkan (`tools/local-qual/README.md`). Those runs timed 29–52-token prompts, though,
where fixed per-call overhead dominates, so they are not throughput figures; the GTX 1070 run measured pp512 at 367 tokens/s and pp512
at 4K depth at 380 tokens/s [V S18, S19]. The setup matters and must be measured with prompts of our real length. llama-server
reuses the shared prompt prefix between calls (`cache_n`), so stable system prompts and cards (doc 40) cut the cost. Offload suits one
call per Fill record or text slot better than K = 3 Picks.

**Placement on the reference card [I].** The GTX 1080 figures bound Gemma 4 26B-A4B's layer cost: moving from `--n-cpu-moe 29` to 21
added about 4.4 GiB of model buffer on the GPU (2,103 to 6,504 MiB), roughly 550 MiB per expert layer for the 16.9 GB non-QAT file
[V S19; I]. With about 5,490 MiB free and the desktop running (doc 44), `--n-cpu-moe 20` cannot fit; start at `--cpu-moe` and lower
`--n-cpu-moe` from about 28 while GPU use stays below the free memory. For Qwen3-30B-A3B each expert layer is about 0.33 GiB at
UD-Q4_K_XL (29.0B expert parameters over 48 layers at about 4.6 bits per weight), so `--n-cpu-moe 40` (8 layers on the GPU) is near
the limit.

| Model (licence) | Q4 file | Params (active) | Thinking | Public evidence | P F D E M | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| **Qwen3-30B-A3B-Instruct-2507** (Apache-2.0) | 18.56; UD 17.69 | 30.5B (3.3B) | none (non-thinking only) | BFCL V4 FC 41.39%, Live 77.94, multi-turn 30.00, irrelevance 79.90 [V S1]; IFEval 84.7, Creative Writing v3 86.0, WritingBench 85.5, INCLUDE 71.9 [V-vendor S15]; not on EQ-Bench, though the original April 2025 qwen3-30b-a3b scores 35.6 on EQ-Bench Longform [V S4, S5] | 2 3 2 3 2 | **Test now** |
| **Gemma 4 26B-A4B-it QAT** (Apache-2.0) | Q4_0 14.44 (Google); UD 14.25 (Unsloth; no Q4_K_M) | 25.8B (3.8B) | switch; empty thought block when off | EQ-Bench Creative v3 1304.6 (doc 14), Longform 50.7, the best local candidate [V S5]; UGI Writing 41.62 without thinking [V S6]; EuroEval Czech 1.71, Polish 2.05 [V S7]; offload measured above [V S19] | 2 2 3 2 3 | **Test now** |
| Qwen3.5-35B-A3B (Apache-2.0) | 22.02; UD 22.24; UD-IQ4_XS 17.49 | 35.95B (3B) | switch, default on | Vendor (thinking mode) IFEval 91.9, BFCL-V4 67.3, TAU2 81.2 [V-vendor S16]; EuroEval Czech 1.68, Polish 1.75, the best instruct checkpoint with 4B or fewer active parameters (FP8; the Base scores 1.65 in Czech) [V S7]; UGI Writing 37.0 without thinking [V S6] | 2 2 2 2 3 | Alternate (if RAM allows) |
| Qwen3.6-35B-A3B (Apache-2.0) | UD-Q4_K_M 22.13; UD-IQ2_M 11.52 | 35.95B (3B) | switch, default on | The GTX 1070 measurement above [V S18]; a coding and agent card that ties 3.5 on shared rows (MMLU-Pro 85.2 against 85.3) [V-vendor S17]; UGI Writing 35.83 without thinking [V S6] | 2 2 2 2 2 | Alternate |
| gpt-oss-20b (Apache-2.0) | MXFP4 12.11 | 20.9B (3.6B) | reasoning low / medium / high | RTX 4060 Laptop 8 GB, `--n-cpu-moe 14`: 42.32 tokens/s [V S23]; EQ-Bench Longform 21.2 [V S5]; EuroEval Czech 1.96 [V S7]; needs Harmony-aware grammars (§1.2) | 2 2 0 2 2 | Watch |
| Nemotron 3 Nano 30B-A3B (NVIDIA licence) | 24.57; UD 22.83 | 31.6B (3.5B) | switch, default on | Vendor numbers come from a reasoning-mode table (BFCL v4 53.8) [V-vendor S35]; no CZ, PL or RU | 1 2 2 2 1 | Skip |

### 2.6 Considered and left out

- **Too large or not an assistant:** Qwen3.8-Flash-Next (created 2026-08-24) has 180B parameters and licence "other" [V S61].
- **Licence:** Tencent Hunyuan 0.5–7B Instruct and Hunyuan-MT / HY-MT1.5, whose licence "DOES NOT APPLY IN THE EUROPEAN UNION, UNITED
  KINGDOM AND SOUTH KOREA" [V S42]; xLAM-2 (CC-BY-NC-4.0) and the other tool specialists in §3.1 [V S54]; Tiny Aya (CC-BY-NC-4.0)
  [V S40].
- **Already covered in doc 14 with nothing new found:** Gemma 4 E2B/E4B/12B/31B, Qwen3.5-0.8B/9B, Qwen3.8-27B, Granite 4.2,
  Ministral 3, SmolLM3, Nemotron 3 Nano 4B, GLM-4.7-Flash, Muse-Glimmer-30B, FunctionGemma. Granite 4.2-30b is a dense 29.3B model
  (`GraniteForCausalLM`), not an offload candidate [V S70]. Gemma 4 E2B and Granite 4.2-3B are still unmeasured, so §6.1 carries them.
- **Added by the critic pass and left out (sweep of Hugging Face trending and 45 vendor organisations, 2026-09-27) [V S66–S72]:**
  - *No mainline llama.cpp support:* Ternary-Bonsai-2-27B (Apache-2.0, a ternary retrain of Qwen3.8-27B; "Stock llama.cpp will
    not run these files", only PrismML's fork; the 5.95 GB PTQ1_0 file fits an empty 8 GB card but not the ~5.5 GB free on the
    reference card; reasoning effort `xhigh` by default; examined in §2.7) and Xing4.0-29B-A4B (Apache-2.0, China Telecom; support
    PRs #29012 and #29141 still open).
  - *Licence bucket (owner ruling):* Arcee Trinity-Mini (26.1B MoE) and Trinity-Nano-Preview (6.1B MoE) are tagged OpenMDW-1.1 at
    their current revisions, the Seed-X bucket (§5); Kakao kanana-2 (custom `kanana-license`); Falcon-H1R-7B (Falcon LLM licence, English, reasoning).
  - *Multilingual, weaker on EuroEval than what we have:* EuroLLM-22B-Instruct-2512 (Apache-2.0; Czech 2.08, Polish 2.48, no
    better than the 9B's 2.04 at 2.5 times the size), Apertus-v1.1-4B-Instruct (Apache-2.0; Czech 2.60, Polish 3.19), EuroMoE-2.6B-A0.6B
    (Apache-2.0; only the Preview is on the board, Czech 3.57, Polish 3.65), Salamandra-7b-instruct (Czech 3.24) [V S7].
  - *Popular Qwen3.5-9B derivatives:* Ornith-1.5-9B (MIT; a reasoning model that opens every turn with `<think>`), MiMo-V2.6-Distill-
    Qwen-9B (MIT, 2026-09-21), NeoHorse-1-9B (Apache-2.0). Doc 14's Qwen3.5-9B covers the base; none has independent writing or
    locale evidence.
  - *Too large:* GLM-5.3-Flash (321B), Motif-3 (315B), Hy4-preview (780B), North-Small-Translate-1.0 (218B, CC-BY-NC-4.0).
  - *Helpers with non-OSI terms:* EmbeddingGemma-300m (Gemma terms, gated), jina-reranker-v3.5 (CC-BY-NC-4.0).

### 2.7 Ternary and very-low-bit 27B: Bonsai 2 27B (owner question)

Added after the critic pass to answer "What about Bonsai 2 27B?". Nothing was downloaded or run. The pins, releases, issue states and
vendor files below were re-read on 2026-09-27 (Verification notes: the Bonsai addendum and its fact-check).

**What it is.** PrismML's `Ternary-Bonsai-2-27B` (announced 2026-09-17, repository created 2026-09-16, Apache-2.0) is derived from
Qwen3.8-27B (Apache-2.0, 2026-08-05) with the architecture unchanged: GGUF architecture `qwen35`, 64 layers (48 Gated DeltaNet layers
and 16 gated-attention layers with 4 KV heads × 256), a 262,144-token context, and vision through an mmproj file [V S74, S77]. Every
matrix weight, the embedding and the LM head included, is ternary {−1, 0, +1} with an FP16 scale per 128 weights (26.2M parameters,
the recurrent-state path and the norms, stay in higher precision), stored in a blockwise Walsh–Hadamard-rotated basis (block 1024,
fixed sign flips) that the runtime undoes on the activations [V-vendor S74, S76]. Two packings are published: PTQ1_0 (1.75 bits per
weight, 5,946,648,928 B) and PQ2_0 (2.13 bits per weight, 7,206,168,928 B) [V S74]. It is a retrained sibling of the base, not a
rounding of it: rotate-and-round reproduces about 92% of the trits, swapping in the rest collapses perplexity (HF discussion #44), and
the training recipe is unpublished [V S76, S81]. No smaller Bonsai 2 exists; the 8B, 4B and 1.7B ternary models are first-generation,
on Qwen3 bases [V S75].

**Vendor claims against the evidence.**

| Claim (vendor or research brief) | Finding | Evidence |
| --- | --- | --- |
| "98.2% of FP16" | [V-vendor], thinking mode only | 84.78 against 86.32 on 14 benchmarks (card) and 83.9 against 85.4 on 20 (whitepaper), at `xhigh` effort with EvalScope and vLLM on H100 [V-vendor S74, S76]. At `medium` effort 96.0% (79.3 against 82.6); long-horizon agent tasks keep about 75% (Terminal-Bench 2.1 52.8 against 69.7, SWE-bench Verified 60.8 against 80.6) [V-vendor S76]. No non-thinking result is published, and Plotroom runs every step with thinking off. The scores come from vLLM serving, not from the GGUF files on llama.cpp, and no unpacked Bonsai 2 checkpoint is published (the first generation had `-unpacked` repositories), so the scored artefact cannot be re-run as released [V S75, S76; I]. The vendor's own 2-bit comparator is not stable: the card's IQ2_XXS scores 56.40 on LiveCodeBench and 57.50 on AIME26 (average 72.59 on 14), the whitepaper's 70.05 and 78.6 (average 75.2 on 20), while the FP16 and Bonsai values match in both [V-vendor S74, S76]. |
| Near-lossless, so it behaves like the base | Contradicted for the output distribution | Against Unsloth's BF16 (V100, fork build 10728, wikitext-2, 50 chunks): PQ2_0 mean KLD 0.340, same top token 77.8%, perplexity 8.04 against 6.13 (×1.31); Unsloth UD-Q4_K_XL 0.0087 and 96.9%. Over all 145 chunks: 8.35 against Q4_K_XL's 6.34 [V S81]. For scale, bartowski's mainline IQ2_XXS of the same base: mean KLD 0.283, 78.0% (a different run: b10896, 100 chunks) [V S81]. |
| Better than conventional 2-bit | One independent task result, with thinking on | LiveCodeBench v6, 50 problems, temperature 0.2, 8,192-token cap, Bonsai at `reasoning_effort: medium`: PTQ1_0 32/50 against Unsloth UD-IQ2_XXS 16/50 on the same fork build (paired, p = 3.1e-05; fork issue #283) [V S79]. Both arms reasoned; IQ2_XXS hit the token cap on 34 of 50 problems against 18, so part of the gap is reasoning that did not finish [V S79; I]. Vendor table: IQ2_XXS 72.59 against 84.78 (whitepaper: 75.2 against 83.9) [V-vendor S74, S76]. |
| "Stock llama.cpp will not run these files" | [V] | PQ2_0 and PTQ1_0 are types 142 and 143 in the fork's `ggml.h`; mainline stops at 42 (Q2_0) [V S78]. The F16 file loads in stock builds and "produces garbled output" [V-vendor S74]. |
| Needs the fork at `prism-b10658+` | Vendor sources disagree; use `prism-b10743` | The docs site does say "prism-b10658 or newer" for both GGUF packings [V-vendor S76], but that release (2026-08-28) predates Bonsai 2 by three weeks and is also the Bonsai 1 README's minimum [V S76, S78]. KNOWN_ISSUES names `prism-b10709` or newer (the launch tag `prism-b10687` carries only CUDA runtime zips, no llama.cpp binaries), and the demo pins `prism-b10743-adfffbe` of 2026-09-25 [V S74, S76, S78]. Whether b10658 runs Bonsai 2 correctly is untested [U]; the Vulkan and x86 fixes this doc relies on are only in b10743. |
| CUDA and Metal; CPU unoptimised | Partly right | The card lists CUDA, Metal and CPU [V S74]; the fork's releases also ship Vulkan and HIP (ROCm) builds, but no SYCL build, and KNOWN_ISSUES says the SYCL backend cannot run PQ2_0 or PTQ1_0 yet (#235 in review) [V S74, S78]. Three fixes KNOWN_ISSUES marks "fixed in source" on 2026-09-23 (PQ2_0 silently on the CPU under Vulkan, #238, which carries #188's Vulkan PQ2_0 support and PTQ1_0 integer-dot decode kernel; x86 PQ2_0 AVX2 kernels, #206; the AVX-512 load crash, #245) are all in `prism-b10743` [V S78, S79]. For PTQ1_0 on x86 that release has only SSE2/SSSE3 kernels (#248); the AVX2 kernel (#250) is in review [V S79]. |
| Thinking off via `thinking_budget_tokens` 0 or `BONSAI_THINKING=0` | Contradicted by the vendor's own files | The docs site says so [V S76], but the model repository's KNOWN_ISSUES says a budget in `chat_template_kwargs` is ignored and "A budget of `0` does not turn reasoning off"; its off switch is `reasoning_effort: "none"` with the server at `--reasoning auto` [V S74]. `BONSAI_THINKING` is in neither the demo's launcher nor its list of variables at `9ef3205` [V S76]. |
| Apache-2.0 | [V] | Plain Apache-2.0 LICENSE; the NOTICE asks, without requiring it, for "Created using Bonsai by Prism ML" and credits Qwen3.8-27B [V S74]. The fork is MIT [V S78]. The licence key inside the GGUF was not read (that needs a ranged download) [U]. |

**Runtime.**

- **Mainline:** feature request #29058 (types 142 and 143) is open. PR #29077, which added both types, was closed unmerged on
  2026-09-22 after a maintainer asked PrismML to submit support itself [V S80]. PrismML is so far upstreaming only the fast
  Walsh–Hadamard transform (CPU #27779, Metal #29094 and #29095, CUDA #29096 and SYCL #29243 merged; CUDA #29100 and Vulkan #29101
  open drafts) [V S80]. It aims upstream support at the official Q2_0 with the rotation and sign flips; its engineer wrote on PR #29077
  that "PTQ1_0 and PQ2_0 might stay in fork only", and the demo README calls them fork-specific packings with no promise of upstream
  support [V S76, S80]. That upstream-shaped file is 7,626,008,928 B (the `-gguf-dev` repository), too large for the free VRAM too
  [V S75].
- **Precedent:** PrismML's 1-bit Q1_0 reached mainline CPU, Vulkan and CUDA within about 3–4 weeks of its repositories' creation
  (2026-03-18; merged 2026-04-06, 04-10 and 04-15); ternary Q2_0 took about 11–15 weeks (GGUF repositories 2026-04-18; CPU merged
  2026-07-07, CUDA 2026-07-30) and was changed to group 64, about 6% larger [V S75, S80; I for the durations].
- **The fork:** MIT, default branch `prism`, 127 commits ahead of mainline master and 605 behind (merge base 2026-08-25); three
  releases between 2026-09-18 and 2026-09-25, and thirteen from `prism-b10658` (2026-08-28) to `prism-b10743` [V S78]. Its
  llama-server is late-August mainline code and documents `--json-schema`, `response_format`, `chat_template_kwargs` and `--fit` (on
  by default, 1,024 MiB margin, adjusting only unset arguments) [V S78]. Open fork issue #87 (filed in July against a first-generation file) reports tool-call grammars that fail
  to compile being logged and skipped, so generation runs unconstrained: the fail-open class of §1.2, in code the fork shares with
  mainline [V S79].
- **Pascal and CUDA:** the fork's Windows CUDA 12.4 build carries `61-virtual` code that the driver compiles on first run; its CUDA
  13.x builds have no Pascal target [V S78]. On Pascal, PTQ1_0's batched kernel (Turing and newer) is replaced by dequantise plus
  cuBLAS, while PQ2_0 has a Pascal tile configuration [V S78]. No Bonsai 2 CUDA measurement on Pascal exists [U]; the first-generation
  ternary 27B ran pp512 278 and tg128 20.5 tokens/s on a GTX 1080 Ti [V S83], but that was a Q2_0 file with no Hadamard rotation,
  wholly on a larger 11 GB Pascal card, so it bounds a 1070 with partial offload from above [V S74, S76, S83; I].
- **Vulkan on the reference GPU** (fork issue #247: GTX 1070, Windows 10, driver 535.98, the fork's code of 2026-09-23, PTQ1_0 wholly
  on the GPU): generation 14.7 tokens/s in llama-bench and about 11 in llama-server, but prompt processing flat at about 16 tokens/s
  from pp512 to pp2048. A 2,839-token prompt prefilled at 15.25 tokens/s, plus about 3 s of fixed cost per request. The card reports
  `fp16: 0`, so the batched path runs in f32; the issue is open with no reply [V S79]. The release before the decode fix (b10709)
  generated 0.81 tokens/s; b10743 was cut two days after the measured code [V S79; I].

**Fit on the reference box [I].** 5,490 MiB of free VRAM (doc 44); a 4-core, 8-thread CPU with AVX2 and no AVX-512 or VNNI; 4 × 8 GB
of DDR4-2400 in two channels, 38.4 GB/s peak at the configured 2,400 MT/s (Intel rates the CPU for DDR4-2133, 34.1 GB/s) [V S85;
hardware read locally].

- **Full GPU: no.** The PTQ1_0 file is 5,671 MiB. llama.cpp keeps the token embedding on the CPU (fork and b11146
  `src/llama-model.cpp`, "always keep it on the CPU"), about 265 MiB here, which leaves about 5,400 MiB of weights for the GPU
  [V S78; I]. The KV cache is 64 KiB per token at f16 (16 attention layers × 2 × 4 heads × 256 × 2 B), 512 MiB at 8K, plus about
  150 MiB of Gated DeltaNet state (48 layers × 48 heads × 128 × 128 × 4 B, plus the convolution state) [arithmetic on S77]. An RTX
  3080 running the fork peaked at 6,571 MiB at 16K and 7,195 MiB at 32K with q8_0 KV [V S79]: about 6.1 GiB at 8K by
  extrapolation, about 6.35 GiB with f16 KV, so roughly 0.8–1.0 GiB of weights (about 10–13 of 64 blocks) must stay in RAM.
- **Partial offload:** keep `-ngl 99` and move whole blocks to the CPU with `-ot`, so the blocks that leave are named explicitly and
  every layer's KV cache and recurrent state stays on the GPU. (A lower `-ngl` would also work: llama.cpp offloads the output layer
  first and then the last blocks, and leaves the first blocks on the CPU [V S78, `src/llama-model.cpp`].) Generation: the GPU share
  at #247's effective rate (5.95 GB × 14.7 tokens/s ≈ 87 GB/s, a third of the card's 256 GB/s [S85], which suggests unpacking rather
  than memory binds) costs about 55–60 ms per token. The CPU share runs on the SSSE3 PTQ1_0 kernel, which an AVX2 build also picks,
  and which moved the whole model at about 12.5 GB/s on a 6P+4E i5-12600K (#248: 2.1 tokens/s at 8 threads, AVX disabled at compile
  time) [V S79], so a 4-core Skylake needs roughly 120–220 ms for ~1 GB. That is **about 3–6 tokens/s** in llama-bench, less in the
  server. Prompt processing cannot beat the ~16 tokens/s ceiling: **at least 60 s per 1,000 uncached prompt tokens.** A Pick sends
  about 200 uncached tokens (doc 46 §2.6: 820 ms at 253 tokens/s), so one Pick takes about 15–20 s instead of about 1 s.
- **CPU only:** use PQ2_0, which has AVX2 kernels in b10743 (#206) [V S79]. Reading 7.21 GB per token at 38.4 GB/s caps generation at
  5.3 tokens/s, and compute binds first: **about 1–3 tokens/s**. For scale, #206 measured 3.9–4.2 tokens/s and 16 tokens/s of prompt
  processing on a 10-core i7-13620H with AVX-VNNI, which this CPU lacks [V S79]. A data point, not a harness option.
- **The fork's CUDA 12.4 build:** the only configuration that might be much faster and the one nobody has measured [U]; the 1080 Ti
  run above is an upper bound, not a forecast. It is also a CUDA build, which Plotroom's own builds never bundle (D022 decision 2).

**Against the mainline alternatives [I].**

| Option (all Apache-2.0) | Runtime | File | On ~5.5 GB free | Generation on the reference box | Prompt processing | Evidence for our steps |
| --- | --- | --- | --- | --- | --- | --- |
| Bonsai 2 27B PTQ1_0 | fork only | 5.95 GB | partial offload, ≈ 1 GiB in RAM | ≈ 3–6 tokens/s [I] | ≈ 16 tokens/s on this card [V S79] | thinking-mode vendor tables; one code benchmark [V S79] |
| Qwen3.8-27B UD-IQ2_XXS (Unsloth) | mainline b11146 | 7.27 GB | partial offload, ≈ 2.5–3 GiB in RAM | ≈ 5–8 tokens/s [I] | unmeasured; ≈ 30–60 tokens/s by scaling the 4B [I] | same-base IQ2_XXS KLD 0.283 [V S81]; half Bonsai's LiveCodeBench score, thinking on [V S79] |
| Qwen3-30B-A3B-2507 or Gemma 4 26B-A4B QAT (§6.1 rows 2–3) | mainline | 14.25–17.69 GB | `--cpu-moe`, 2–5 GiB of VRAM | 16–26 tokens/s measured on Pascal 8 GB cards (Gemma 4 26B-A4B, Qwen3.6-35B-A3B) [V S18, S19] | pp512 367 tokens/s (Qwen3.6-35B-A3B, CUDA 12.8, GTX 1070) [V S18] | non-thinking by design (Qwen) or by switch; Gemma's writing and locale evidence (§3.4, §3.5) |
| Bonsai-27B Q1_0 (first generation, Qwen3.6-27B base) | mainline (Q1_0 on Vulkan since #21539) | 3.80 GB | full GPU at 4–8K by the vendor's peak memory (5.2 GB at 4K) [V-vendor S83] | unmeasured | unmeasured | vendor 89.5% of FP16 in thinking mode [V-vendor S83]; one hands-on report of a false answer with thinking off [V S83] |

The comparator's estimate puts about 4.5 GB on the GPU at the ~128 GB/s implied by doc 46's Qwen3.5-4B Vulkan run (tg32 44.0 on
2.91 GB) and about 2 GB on the CPU at 15–25 GB/s [I].

- **By step kind [I].** MoE offload reads about 1 GB of expert weights per token from system RAM, against 6–7 GB in all for a dense
  27B near 2 bits, so it generates 3–5 times faster; the only Pascal MoE prompt measurement at a realistic length is 367 tokens/s
  (CUDA), against Bonsai's 16 (Vulkan). **PICK** is prompt-bound (one answer token), so Bonsai is out for Pick on Pascal whatever its
  quality. **FILL, COMPOSE and creative text** are
  where a 27B could matter, but only with thinking off, where there is no evidence at all. **EXPLAIN** is short and card-grounded, so
  a larger model is unlikely to repay a minute of prompt processing.

**Thinking.** The template is Qwen3.8-27B's: it thinks unless `enable_thinking` is false, in which case it emits an empty think block,
and that is what `run.py` sends [V S75]. `reasoning_effort` takes only `xhigh` (the default), `medium` and `low`; `high` returns HTTP
500, and `low` thinks about as long as `xhigh` [V S74, S75]. The template needs exactly one system message, first (`run.py` sends one),
and by default re-renders earlier reasoning into later turns, which defeats prompt-cache reuse in multi-turn loops [V S74, S75]. The
GGUF carries only the thinking-mode sampler (`top_k`, `top_p`, `temperature`), not the card's non-thinking values (temperature 0.7,
top_p 0.80, presence penalty 1.5) [V S74]. Every published evaluation keeps thinking on; one user reports 2–3 times the tokens of a
4-bit build (HF #47), and the vendor lists malformed or looping tool calls as open [V S74, S81]. With thinking on at ~11 tokens/s, one
step would take minutes [I].

**Product implications [I].**

- **One pinned runtime.** Doc 46 recommends one managed llama-server, the upstream Vulkan build pinned by tag and SHA-256, with CUDA
  builds as bring-your-own endpoints; D022 decision 2 keeps CUDA out of Plotroom's builds. Managing the fork would add a second supply
  chain for one model: 605 commits behind upstream, three releases in eight days, and CUDA 13.3 builds that exit silently on Windows
  (open) [V S74, S78].
- **So: bring-your-own until upstream.** A user can already point Plotroom at the fork's llama-server as D022's "local
  OpenAI-compatible server" (decision 1). D022 had no badge rule for such a server; by analogy with its rule for unlisted Hugging Face
  files (an "unqualified" badge until the user qualifies it; a proposal under OWQ-19 when written), the model would stay unqualified
  until `tools/local-qual` passes on that runtime. Since 2026-09-27 this is decided: D022's amendment note (item 4) and D037 badge a
  model behind a fork's bring-your-own server "unqualified" until qualification passes on that endpoint. Plotroom should not download or supervise the fork. (Doc 13 §3 lets the managed
  sidecar run a CUDA build the user downloads from upstream; whether that should extend to a user-downloaded fork binary is the
  middle option of open question 9.)
- **If the owner wants a managed "advanced runtime" anyway,** the D022 manifest needs a runtime pin per model entry (runtime, release
  tag, asset, SHA-256, backend), qualification keyed by runtime (D022 already voids it when the runtime changes), and a supervisor that
  can run two binaries. The fork's releases publish a SHA-256 digest for every asset [V S78].
- **A Model Manager guard is needed regardless.** Stock llama.cpp loads the Bonsai 2 F16 file, and ordinary models quantised to these
  types, without a warning and generates nonsense [V-vendor S74]. The manager should refuse a GGUF with an unknown tensor type or
  `prism.hadamard.*` metadata unless the pinned runtime declares support, rather than trusting a successful load.
- **Pin the revision, never `main`.** Open HF PR #59 rewrites the metadata of all five GGUFs (weights unchanged), which changes every
  SHA-256; pin `b072e1d` (the files' own commit is `6ed5e12`) [V S74].
- **Hosted:** OpenRouter lists one provider for it, labelled int4, with structured outputs [V S84]; whether that endpoint serves the
  ternary weights is unknown [U]. Cloud providers are outside this doc.

**Verdict: Watch, not Priority A.** An optional paired probe (the owner's call) can follow the Priority A rows: PTQ1_0 on the fork's
Vulkan release with about 12 blocks in RAM, against Qwen3.8-27B UD-IQ2_XXS on the mainline build, both with thinking off and the common
sampler pin (§6.1; Appendix A; the shortlist JSON's `bonsai` block). It answers one question: does ternary retraining buy quality over
a mainline 2-bit build of the same base on Plotroom's steps with thinking off? At about 16 tokens/s of prompt processing it takes
roughly 1.5–2.5 hours per arm [I].

What would change the verdict [I]:

1. **Up to "test now":** mainline merges the Q2_0 rotation and sign-flip support, and a Pascal Vulkan run meets §6.3 item 3's offload
   bar (whole-record Fill pass^3 ≥ 0.8 with p90 Fill latency ≤ 10 s warm), which ~16 tokens/s of prompt processing cannot. Or the owner
   accepts a bring-your-own badge for newer GPUs, where the fork generates 32 tokens/s on an 8 GB RTX 3060 and 52 on an RTX 3080
   [V S79, S81].
2. **Up to a recommended writer on 12 GB and larger:** the paired probe, or an independent non-thinking evaluation, puts Bonsai clearly
   ahead of UD-IQ2_XXS (doc 44 §6's noise rule) and at least level with the offload rows on Fill and text.
3. **Down to "skip":** with thinking off it loops, breaks the JSON schema, or is no better than UD-IQ2_XXS.

## 3. Specialists

### 3.1 Tool-calling and structured-output specialists

BFCL V4's overall score weights agentic tasks at 40% and multi-turn at 30% [V S2]; the "simple" and "multiple" AST categories (choose
one of 2–4 functions and fill its arguments) and irrelevance detection are the part closest to a Pick or Fill [V S3]. On those columns
[V S1]:

| Model (licence) | Live Simple | Live Multiple | Non-Live Simple | Irrelevance | Overall |
| --- | --- | --- | --- | --- | --- |
| Qwen3-4B-Instruct-2507, FC (Apache-2.0) | 79.07 | 76.16 | 75.50 | 84.93 | 35.68% |
| xLAM-2-3b-fc-r (CC-BY-NC-4.0) | 73.26 | 60.68 | 75.33 | 63.45 | 41.22% |
| Hammer2.1-3b (qwen-research) | 68.22 | 71.32 | 79.33 | 86.12 | 29.71% |
| Arch-Agent-3B (katanemo-research) | 75.58 | 72.27 | 78.67 | 74.67 | 35.36% |
| Nanbeige4-3B-Thinking-2511 (Apache-2.0) | 86.05 | 78.06 | 63.83 | 83.09 | 51.40% |

- The specialists lead on multi-turn, which the harness does not use. On the single-call columns, Qwen3-4B-2507 leads the
  non-reasoning rows on the Live categories (the reasoning Nanbeige row beats it there, at 13.46 s mean latency); Hammer2.1-3b beats it
  on Non-Live Simple and irrelevance, and Arch-Agent-3B on Non-Live Simple [V S1].
- xLAM-2's 63.45% irrelevance means more false calls, which is bad for the `X` escape [I on V S1].
- BitAgent-Bounty-8B tops the small single-call columns (Live Multiple 94.02, irrelevance 97.48) but has an empty card, 0% web search
  and 1.51% memory on the board, which suggests benchmark-targeted tuning with undocumented data [V S54; I].
- Nemotron-Orchestrator-8B is for "research and development only" [V S54]. Osmosis-Structure-0.6B structures free-form output after
  the fact, which decode-time grammars make unnecessary [V S54; I].

**Public ranks did not predict our instrument.** Gemma 4 E4B was best on doc 44's Pick and Fill, yet OpenBMB's table gives it the
lowest BFCL v4 (47.0) and IFEval (44.4) of the 4B-class models it lists, while Liquid's table gives Gemma 4 E4B an IFEval of 87.74
[V-vendor S25, S31]. Vendor tables also disagree about Qwen3.5-4B (IFBench 41.4 in Nanbeige's table, 59.0 in OpenBMB's) [V-vendor S33,
S25]. Only our own suites should decide [I].

### 3.2 Decision-format models (PICK)

- **decider** (0.8b / 2b / 4b; Apache-2.0; English only). Qwen3.5 bases fine-tuned so that the hidden state at an answer slot, projected
  on the option-letter rows of the LM head, gives a calibrated distribution; `abstain_below` returns no answer [V S49]. Author numbers:
  the 2b (v11) scores 0.802 in-task and **0.429** on held-out generated families (ECE 0.156); the 4b (v2.1) 0.831 and **0.556**
  (ECE 0.147) [V-vendor S49]. Held-out generated menus are the closest thing to our code-built menus, where doc 44's general 3–4B
  models scored 90–95% on a different instrument [I]. GGUFs are community-only (0.8b Q4_K_M 0.53 GB; 2b IQ4_NL 1.24 GB; 4b Q4_K_M
  2.71 GB) [V S49]. The official runtime is PyTorch; a llama-server port would send a raw prompt to `/completion` with `n_predict` 1 and
  `n_probs` ≥ 20, renormalise over the valid letters and apply the fitted temperature (choice T = 1.164 on the 2b) [I, untested; S8].
  Only single-question requests port. **Verdict:** test in shadow through D023's `Selector` seam after the readout mode exists (§6.4).
- **Intern-Decision-4B** (Apache-2.0): a standard Qwen3.5-4B checkpoint whose engine reads next-token logits at placeholders; vendor
  average 90.02 (Brier 0.347, ECE 0.065) on its own suite, whose origin the card does not document [V-vendor S50]. Only a community
  Q8_0 GGUF exists. **Watch** (doc 16 candidate list).
- **Arch-Router-1.5B** reports 93.17% on its paper's routing set against 20.69% for its untuned Qwen2.5-1.5B base [V-vendor S51], but
  its licence requires "Built with DigitalOcean" and a commercial licence, and doc 44 already measured workflow routing at 0.93–1.00
  for Qwen, Granite and Gemma [V S51; V per doc 44]. **Skip.**
- **Needle 3** (121M, Apache-2.0) runs in its own engine (C API, CLI, WASI component), not llama.cpp, has a 256-token KV window and only
  vendor claims [V S52]. **Watch.**
- D023 decision 5 keeps every decision model out of v1 unless it beats both the deterministic and the generative selector on our
  instruments (doc 16 §5).

### 3.3 Extraction models (FILL spans)

- **NuExtract3** (NuMind; Apache-2.0; official GGUF). A Qwen3.5-4B fine-tune that fills a JSON template whose leaf types include
  `verbatim-string`, enums and multi-enums; absent fields become null [V S47]. Vendor table, run with reasoning on at temperature 0.25
  and up to 65,000 output tokens: NuExtract3 0.651 with 27 failed runs, Gemma-4-E4B-it 0.538 / 31, Qwen3.5-4B 0.417 / 229,
  Ministral-3-3B 0.240 / 344, over about 600 documents [V-vendor S47]. Most of the general models' losses are failed runs (repetition
  loops), and our harness runs them with thinking off, so the gap does not transfer [I]. It targets exactly doc 44's weak fields: the
  target span (Ministral 0 of 12, Gemma 0.83) and the place span [V per doc 44]. The GGUF's template reads a `template` variable and
  defaults `enable_thinking` to false, and llama-server accepts per-request `chat_template_kwargs` [V S47, S8], so the harness can pass
  the template per call [I, untested]. At about 3.3 GiB it cannot sit beside Gemma 4 E4B on an 8 GB card; it would be a swap [I].
  **Verdict:** test on the Fill suite, thinking off, against Gemma 4 E4B and Qwen3.5-4B run the same way.
- **LFM2-1.2B-Extract / 350M-Extract** (LFM Open License): 0.73 / 0.23 GB, no published numbers, no Czech, Polish, Russian or Italian
  [V S48]. **Watch** (bring-your-own).
- **Task-distilled adapters.** A public exemplar fine-tuned Qwen3.5-4B on 4,156 synthetic examples and scored 98 of 100 against its
  teacher's 96, in thinking mode, on one narrow task [V-vendor S53]; Arch-Router shows the same pattern for routing [V-vendor S51].
  Format-specific training works [I]. A Plotroom adapter is a post-v1 spike: one LoRA on doc 44's weak Fill fields, measured against
  the untuned base, trained only on Plotroom's own synthetic data [I].

### 3.4 English creative text

- **EQ-Bench Creative Writing v3:** among models of 14B or less the best is gemma-4-12B-it at 1288.9; the only small entries are older
  models such as gemma-3-4b-it (1068.0) and Nanbeige4-3B-Thinking-2511 (841.2); no 2026 small model is on the board [V S4].
- **EQ-Bench Longform:** Gemma 4 26B-A4B 50.7, Gemma 4 12B 48.7, Qwen3.5-35B-A3B 44.5, qwen3-30b-a3b (the April 2025 original, not
  the 2507 Instruct) 35.6, gemma-3-4b-it 34.4, Ministral-3-14B 31.9, Nanbeige4-3B-Thinking-2511 31.5, gpt-oss-20b 21.2, qwen3-4b 17.0
  [V S5].
- **UGI Writing** (no thinking / thinking prefill): Qwen3.6-35B-A3B 35.83 / 45.36; Gemma 4 26B-A4B 41.62 / 43.8; Qwen3.5-9B
  33.52 / 39.5; Gemma 4 12B 31.6 / 36.32; Qwen3.5-4B 29.68 / 30.82; Gemma 4 E4B 20.23 / 21.59 [V S6]. UGI rates Qwen3.5-4B well above
  Gemma 4 E4B for English writing; doc 44's graders passed 7 of Qwen's and 5 of Gemma's 20 lines, the same direction within noise [I].
- **Best open writer found:** Hemmingway-1, a 26.9B Qwen3.8-27B fine-tune under CC-BY-NC-4.0, Elo 1906.4 and Longform 74.2, above
  Muse-Glimmer-30B's 1798.3 [V S4, S5, S60]. Bring-your-own only, and T2b hardware.
- **Conclusion [I]:** for English creative text keep doc 14's Gemma 4 12B and 26B-A4B as the local writers, and test the 26B-A4B
  through offload. Qwen3-30B-A3B-2507's writing numbers are Qwen's own benchmark runs, not EQ-Bench Elo.

### 3.5 Multilingual text and translation

**EuroEval rank scores** (lower is better; they aggregate sentiment, named entities, acceptability, reading comprehension,
summarisation, knowledge and common sense, not creative writing or translation; there is no Russian board) [V S7]:

| Model | Czech | Polish | Hungarian | European |
| --- | --- | --- | --- | --- |
| Qwen3.5-35B-A3B (FP8 checkpoint) | 1.68 | 1.75 | 1.78 | 1.75 |
| Gemma 4 26B-A4B-it | 1.71 | 2.05 | 2.04 | 1.88 |
| Bielik-11B-v3.0-Instruct | 1.76 | 2.17 | 2.04 | 2.07 |
| Gemma 4 12B-it | 1.84 | 2.07 | 1.93 | 1.93 |
| Bielik-Minitron-7B-v3.0 | 1.89 | 2.33 | 2.18 | 2.23 |
| gpt-oss-20b (reasoning medium) | 1.96 | 2.17 | 2.15 | – |
| EuroLLM-9B-Instruct-2512 | 2.04 | 2.64 | 2.49 | – |
| EuroLLM-22B-Instruct-2512 (critic pass) | 2.08 | 2.48 | – | – |
| Gemma 4 E4B-it | 2.15 | 2.39 | 2.44 | 2.27 |
| Qwen3.5-9B | 2.23 | 2.26 | 2.30 | 2.17 |
| Ministral-3-3B | 2.27 | – | – | – |
| Qwen3.5-2B (critic pass) | 2.54 | 2.86 | – | – |
| Qwen3.5-4B | 2.58 | 2.71 | 2.76 | 2.53 |
| Apertus-v1.1-4B-Instruct (critic pass) | 2.60 | 3.19 | – | – |
| Gemma 4 E2B-it (critic pass) | 2.61 | 2.71 | – | – |
| LFM2.5-8B-A1B | 3.80 | 4.00 | 3.98 | – |
| MiniCPM5-1B | 4.43 | – | 4.35 | – |

- Hungarian is not one of the engine's 8 languages (doc 14 §2). Some rows carry ± 0.07–0.08, and the Bielik rows ± 0.00, which
  suggests a single run; gaps under about 0.1 are noise [V S7; I].
- For locales, Gemma 4 E4B clearly beats Qwen3.5-4B, which supports doc 44's provisional Gemma default [I].

**Translation specialists:**

| Model (licence) | Q4 file | Languages | Evidence | llama.cpp | Verdict |
| --- | --- | --- | --- | --- | --- |
| **Hy-MT2-7B / 1.8B** (Apache-2.0 at revisions from 2026-05-26) | 4.62 (UD 4.78) / 1.13 | 33, including all 8 engine languages [V S41] | Vendor paper claims the 7B and 30B-A3B beat large open models "in fast-thinking mode"; no per-language CZ/PL/RU numbers [V-vendor S41] | `hunyuan-dense` in mainline; the card points to an unmerged PR (#22836) that covers only the 1.25-bit STQ files, so the Q4_K_M should load without it [V S43; I, unverified] | **Test** in a translation suite |
| Hy-MT2-30B-A3B (same licence) | 18.24 | same | same | `hy_v3` since PR #25395 (merged 2026-07-13) [V S43] | Watch |
| TranslateGemma 4B / 12B (Gemma Terms, gated) | 2.49 / 7.30 (community) | 55 | WMT24++ MetricX 5.32 / 3.60 against Gemma 3's 6.97 / 4.86 [V-vendor S44]; input capped at 2K tokens | Chat endpoint works with `chat_template_kwargs` `source_lang_code` / `target_lang_code` (PR #19052); a Jinja parser failure on the 27B (#20305) closed as stale, `--no-jinja` reported to work [V S45] | Watch (bring-your-own) |
| Seed-X-PPO-7B (OpenMDW-1.0, not yet OSI-approved) | 4.56 (community) | 28 | Vendor claims only; the vendor advises against unofficial quantised versions, and every GGUF is unofficial [V S46] | No chat template; recommends beam search [V S46] | Skip |
| Tiny Aya Global (CC-BY-NC-4.0) | 2.14 (official) | 70+ | WMT24++ ChrF 46.0 against Gemma3-4B's 41.9 [V-vendor S40]; scores 0.00 on EuroEval's Czech and Hungarian grammar tasks [V S7] | `cohere2` in mainline | Watch (bring-your-own) |

The Hy-MT2 prompt modes (terminology pairs, delimiters kept, structured data with keys and placeholders kept) map onto doc 14 §4.2's
per-language glossary and the stringtable placeholder checks; output still goes through the codepage and length lints and native review
[I; V S41].

### 3.6 Do specialists beat generalists? [I]

- **Generic function-calling models: no** for this harness (§3.1).
- **Format-matched models: plausibly**, for two narrow steps: verbatim Fill spans (NuExtract3) and calibrated Pick confidence (decider).
  Both need a small harness adapter (§6.4), and neither can sit beside the session model on an 8 GB GPU except the 0.8b decider on CPU.
- **Translation: plausibly**, Hy-MT2 for the translate step of creative text, pending native review.
- **English writing: no small specialist exists**; the gain comes from larger generalists through offload or cloud.

## 4. Helper models

### 4.1 One sidecar, several models

- llama-server's router mode serves several models from one process (`--models-dir`, `--models-max`, default 4, with presets per
  model) [V S8]. `--embedding` restricts a server to embeddings, and reranking needs `--rerank` with `--embedding --pooling rank`
  [V S8], so helpers need their own router entries or processes.
- `-dev none` keeps a model entirely off the GPU [V S8]. Helpers belong on the CPU so they cost no VRAM next to the session model; each
  costs about 0.2–1 GB of RAM [I].

### 4.2 Letter probabilities from the session model: no extra model

- llama-server returns the top-N token probabilities per generated token (`n_probs`), optionally after the sampler chain
  (`post_sampling_probs`) [V S8]. With the answer constrained to the menu letters, one call can return the whole distribution over the
  options [I, untested].
- Uses: a confidence threshold that triggers `Q` ask me, a cheaper alternative to K = 3 voting, and paired evidence for doc 16 §5. The
  probabilities need per-model calibration, as decider applies fitted temperatures [I; S49].
- This is doc 13 §4 item 6's "local decision model emulation", which doc 13 tied to in-process llama.cpp; the sidecar can do it too [I].

### 4.3 Embeddings

| Model (licence) | Size | Languages | llama.cpp notes | Evidence | Verdict |
| --- | --- | --- | --- | --- | --- |
| granite-embedding-311m / 97m-multilingual-r2 (Apache-2.0) | Q8_0 0.35 / 0.12 GB (community) | 52 "enhanced", including CS, PL, RU, IT, DE, FR, ES [V S57] | `modern-bert` in mainline (PRs #15641, #18330); a community GGUF matches the reference at cosine 0.99996 [V S57] | Vendor multilingual retrieval 65.2 / 60.3 [V-vendor S57] | Watch (first to measure) |
| Qwen3-Embedding-0.6B (Apache-2.0) | Q8_0 0.64 GB (official) | 100+ | The official GGUF predates EOS fixes; append the end-of-text token by hand or re-convert [V S55]; turning on `--embedding` and `--reranking` together returned all zeros (#20085, Metal; closed as a misconfiguration, so run one mode per server) [V S55] | Vendor MMTEB mean 64.33 [V-vendor S55] | Watch |
| harrier-oss-v1-0.6b / 270m (MIT) | Q4_K_M 0.40 / 0.25 GB (community) | Lists CS, PL, RU, IT, DE, FR, ES [V S58] | The 270m config matches Gemma 3 270M, so its terms are unclear [V S58; I] | Vendor "MTEB v2" 69.0 / 66.5 [V-vendor S58] | Watch (0.6b only) |

**Role [I]:** only doc 25 §4.6's optional semantic tier for exemplar retrieval ("metadata alone must work") and a shadow shortlist next
to doc 38's BM25. Cards for EXPLAIN are declared per step (D027 item 7), so no embedder selects them. Any embedder must beat BM25/FTS
on Plotroom's own retrieval instrument first (doc 30 open question 2).

### 4.4 Rerankers

- Qwen3-Reranker-0.6B (Apache-2.0, maintainer Q8_0 GGUF 0.64 GB) scores MTEB-R 65.80 against bge-reranker-v2-m3's 57.03, but only 5.41
  on FollowIR, a weak sign for instruction-following in ranking [V-vendor S56]. The wrong-score issue #16407 was closed on 2025-10-09
  and blamed on bad conversions [V S56]; query and document must fit one physical batch until PR #28876 lands [V S56].
- **Verdict: skip for v1 [I].** Cutting a catalog to 7 options with a learned ranker contradicts doc 25 §6.2, where catalog menus are
  split into code-owned facet steps, and a ranker in front of Pick is a selector gated by D023 decision 5. Doc 44's PW04 (UNLOAD against
  TR UNLOAD) is exactly the lexical near-miss a relevance ranker cannot resolve.

### 4.5 Speculative-decoding drafters

- llama-server supports `--spec-type` draft-simple, draft-eagle3, draft-mtp, draft-dflash, draft-dspark and several n-gram types that
  need no model [V S8].
- MTP: Qwen3.6-27B Q6_K on an RTX 3090 went from 22.97 to 42.45 tokens/s at 76% acceptance, for about 2.49 GiB of extra VRAM
  [V S20]. For Gemma 4 26B-A4B the MTP PR's author saw no speed-up on the MoE [V S22], yet the GTX 1080 fork run went from 19.78 tokens/s
  (no drafter, `--n-cpu-moe 20`) to 24.48 tokens/s (MTP assistant, `--n-cpu-moe 21`) under expert offload, with fork-only flags and
  one run each [V S19]. On Metal, MTP was slower at every setting
  (issue #23752, closed) [V S59].
- The Gemma 4 E4B QAT drafter is 0.06 GB, but Unsloth advises "~2 GB additional RAM/VRAM headroom" and doc 44 left 1.14 GiB free
  [V S59; V per doc 44], so it may not fit the reference card [I].
- DSpark (LFM2.5) is merged, but llama.cpp's docs still say only Qwen3-backbone drafts are supported [V S31, S9].
- **Verdict [I]:** drafters help long creative text only, not one-token Picks; test after a default exists, with `json_schema` on,
  because the interaction with constrained sampling is unmeasured [U].

### 4.6 One model or a mix? [I]

| Machine | Session model | Helpers | Heavy steps (Fill record, Compose, creative text) |
| --- | --- | --- | --- |
| 8 GB GPU, 16–32 GB RAM | One 3–4 GB model on the GPU (doc 44's default or a §6 winner) | CPU embedder if the semantic tier is on; decider-0.8b in shadow | Cloud, or a visible session switch to an offloaded MoE model (32 GB RAM) |
| CPU-only, 16 GB RAM | One 1–2B model for Pick and closed Fill fields | None | Cloud or No-AI |
| 12–16 GB GPU | Gemma 4 12B or the 26B-A4B QAT mostly on the GPU | CPU embedder | Same model |
| Apple 16 GB | E4B-class model | CPU embedder | Cloud |

A dedicated tiny PICK router would add a load and a second artifact to qualify without a measured gain, since the session model already
qualifies on Pick (doc 44) [I].

## 5. Licensing for recommending and downloading

Plotroom never ships weights. The Model Manager downloads a pinned file (repository, revision, file, size, SHA-256, licence) when the
user starts it (D022 decision 4), and D023 decision 6 limits default downloads to OSI-licensed weights. Proposed treatment [I]. Since
2026-09-27 the owner's rule (OWQ-19 (a), D037) governs this table: the recommended list takes only qualified models under OSI licences
with no field-of-use limit; every other model, including the "Bring-your-own" and "Not offered" rows, installs only as "custom" with
its licence and use policy shown and accepted; and a use statement whose force is unclear blocks a recommendation until resolved.

| Licence family | Examples in this doc | Model Manager treatment |
| --- | --- | --- |
| Apache-2.0 or MIT, ungated | Qwen3 / 3.5 / 3.6, Gemma 4, Granite 4.0, MiniCPM5, NuExtract3, decider, Nanbeige, Jamba2, EuroLLM, gpt-oss, GigaChat (MIT), Bielik GGUFs, Hy-MT2 at current revisions, Spark-X2.5, Ling-3.0-tiny (MIT); Bonsai 2 27B and Bonsai-27B by licence only (the runtime is the blocker, §2.7) | Eligible for the recommended list; licence and size shown before download |
| Apache-2.0 with a use statement | Olmo 3 ("intended for research and educational use") [V S34]; Qwen3.5-2B's intended-use note [V S29] | Eligible; show the statement |
| Licence tag with unclear provenance | harrier-oss-v1-270m (MIT tag; config identical to Gemma 3 270M) [V S58] | Not first-party until provenance is confirmed |
| Not yet OSI-approved | OpenMDW (Seed-X), submitted to OSI in August 2026 [V S46]; OpenMDW-1.1 (Arcee Trinity-Mini, Trinity-Nano-Preview) [V S68] | Custom only until OSI approves the licence (OWQ-19 answered, D037) |
| Custom, revenue-gated | LFM Open License v1.0: commercial use excluded at $10,000,000 annual revenue or more [V S30, S31] | Bring-your-own; licence shown and accepted |
| Custom with notice and indemnity | NVIDIA Nemotron Open Model License (§7 indemnity) [V S35] | Bring-your-own |
| Pass-through use terms, gated | Gemma Terms of Use (TranslateGemma, Gemma 3-based) [V S44] | Bring-your-own; the user's own token |
| Non-commercial | CC-BY-NC-4.0: xLAM-2, Tiny Aya, Hemmingway-1 [V S54, S40, S60] | Bring-your-own, labelled non-commercial |
| Attribution and derivative naming | Katanemo Community License (Arch-Router): "Built with DigitalOcean", derivative names must start "DigitalOcean" [V S51] | Not offered |
| Territory exclusion | Tencent HY Community License (Hunyuan, Hunyuan-MT, HY-MT1.5; Hy-MT2 files before 2026-05-26) [V S42] | Never offered: it excludes EU users, including Czech and Polish ones |

Rules [I]:

- **Read the licence at the pinned revision.** Hy-MT2's files moved from the EU-excluding licence to Apache-2.0 on 2026-05-26 [V S42],
  and Katanemo re-issued its licence on 2026-04-02 [V S51]. The manifest should store the LICENSE file's hash next to the weights.
- **Metadata can disagree with the licence text.** Unsloth's Nemotron repository carries a different licence tag from NVIDIA's [V S35];
  Liquid's blog says "without restrictions" while the licence is revenue-gated [V S30]. The LICENSE file wins.
- **Teacher outputs carry terms.** Models trained on Arch-Router outputs must be named "DigitalOcean…" [V S51], so such models are
  never teachers for a Plotroom adapter.
- Gated repositories need the user's own Hugging Face token (doc 44 §5.3). None of this is legal advice.

## 6. Test plan

**See also (2026-09-28):** [D044](../decisions/D044-cloud-first-model-screening.md) (owner rule: a model that could run locally is
screened in the cloud first, and tried locally only if promising) and [doc 50](50-free-llm-services-and-cloud-first-screening.md) §5
(which rows have a same-weights host, and the proposed battery S, costs and promotion rule; the schedule is OWQ-27).

### 6.1 Shortlist for the next `tools/local-qual` run

Placement and memory figures are estimates [I] from file sizes, the KV arithmetic in §1.3 and doc 44's measured increases; the run
records the real values. Pinned files are in Appendix A.

| # | Model | File(s) | Placement and expected memory [I] | Suites | Why |
| --- | --- | --- | --- | --- | --- |
| 1 | Qwen3-4B-Instruct-2507 | Q4_K_M 2.50 GB and UD-Q4_K_XL 2.55 GB (Unsloth) | All layers on the GPU; +3.9–4.1 GiB at 8K f16, about +3.4 GiB with `-ctk q8_0 -ctv q8_0` | pick, pick-hard, fill, explain, text | Non-thinking control arm against Qwen3.5-4B; best independent single-call BFCL at 4B; also a quant pair |
| 2 | Qwen3-30B-A3B-Instruct-2507 | UD-Q4_K_XL 17.69 GB (Q4_K_M 18.56 GB as the pair) | `--cpu-moe`, then tune `--n-cpu-moe` down to about 40; 2–5 GiB VRAM, 14–17 GiB RAM | fill first; then explain, text, pick-hard | Whole-record Fill at 30B class with no thinking switch |
| 3 | Gemma 4 26B-A4B-it QAT | UD-Q4_K_XL 14.25 GB (Unsloth) and Q4_0 14.44 GB (Google); no Q4_K_M exists | `--cpu-moe` first, then `--n-cpu-moe` from about 28 downward (20 cannot fit the ~5.5 GiB free, §2.5); 2.5–5 GiB VRAM, 12–14 GiB RAM | fill, text, explain, pick-hard | Same family as the provisional default; the best creative-writing evidence among local candidates; smallest of the offload files |
| 4 | NuExtract3 | Q4_K_M 2.78 GB (official; no UD) | All on the GPU, `--no-mmproj`; about +3.2–3.5 GiB | fill only, through a template adapter | The span fields no 3–4B model qualified |
| 5 | MiniCPM5-2B | Q4_K_M 1.56 GB (official; no UD) | GPU, about +2.1 GiB (a 4 GB-class budget); then `-dev none` | pick, pick-hard, fill, text | Cheapest 2B with strong vendor tool numbers; thinking must be sent off |
| 6 | Qwen3.5-2B | Q4_K_M 1.28 GB and UD-Q4_K_XL 1.34 GB | `-dev none`; about 1.7–1.9 GiB of RAM | pick, pick-hard, fill | CPU floor from the family doc 44 measured |
| 7 | Granite-4.0-H-1B (and dense Granite-4.0-1B) | Q4_K_M 0.90 GB, UD 0.91 GB (1B: 1.02 / 1.04 GB) | `-dev none`; about 1.3 GiB (1B: about 2.0 GiB) | pick, pick-hard, fill (closed fields) | Smallest OSI option; the family qualified on Pick |
| 8 | Granite-4.0-H-Tiny | Q4_K_M 4.23 GB, UD 4.07 GB | `-dev none`; about 4.4–4.7 GiB of RAM | pick, pick-hard, fill | 1B-active MoE: CPU speed against the 1–2B dense rows |
| 9 | Spark-X2.5-4B (critic pass) | Q4_K_M 2.60 GB (official; no UD) | All on the GPU; about +3.1–3.4 GiB at 8K; needs a build with PR #27868 (the card says b10828 or later; b11146, used in `tools/local-qual`, should include it [I]) | pick, pick-hard, fill, explain, text | Newest Apache-2.0 4B with the strongest vendor tool and instruction numbers (thinking mode only); thinking must be sent off |

**Doc 14 carry-overs (unmeasured T1 names):** Gemma 4 E2B QAT (UD-Q4_K_XL 2.62 GB, Google Q4_0 3.35 GB; doc 14's low-memory
fallback; EuroEval Czech 2.61, Polish 2.71 [V S7, S65]) and Granite 4.2-3B (official Q4_K_M 2.24 GB; doc 14's narrow router; the
successor of doc 44's Granite 4.1 3B; vendor IFEval 93.7 and BFCL v4 52.2 in OpenBMB's table [V-vendor S25; V S65]). Both run pick,
pick-hard and fill on the GPU and at `-dev none`.

**Alternates:** Qwen3.5-35B-A3B (UD-IQ4_XS 17.49 GB if 22 GB is too much for 32 GB of RAM) and Qwen3.6-35B-A3B, for the offload slot
if rows 2 or 3 fail on quality rather than speed.

**Optional paired probe (owner question, §2.7; not one of the nine rows):** Ternary-Bonsai-2-27B PTQ1_0 on the PrismML fork's Vulkan
release `prism-b10743-adfffbe` with the last 12 blocks in RAM (`-ngl 99 -ot`), against Qwen3.8-27B UD-IQ2_XXS on the mainline build
with about 22 blocks in RAM. Suites in order: fill, text, explain, pick-hard; thinking off; the common sampler pin. It runs after the
Priority A rows, starts with a `llama-bench` speed gate and a `--limit` sample, and takes roughly 1.5–2.5 hours per arm at the measured
prompt speed (256 calls) [I]. The fork is unpacked into its own folder and never replaces the mainline build. Flags, pins and stop rules are in the
shortlist JSON's `bonsai` block; the files are in Appendix A.

### 6.2 Protocol

1. **Baselines on the same runtime first.** Doc 44 measured through Ollama, and results belong to the exact runtime and build
   (`tools/local-qual/README.md`, Limitations). Re-run Gemma 4 E4B QAT and Qwen3.5-4B (Q4_K_M and UD-Q4_K_XL) on the same llama-server
   build before comparing [I].
2. **One build, recorded.** Plotroom's own target is the Vulkan build (D022). For the offload rows also run the CUDA 12.x build as a
   comparison, since CUDA 13 does not support Pascal [V S24; I].
3. **Server flags.** `-m <file> --jinja -c 8192 -np 1 --no-mmproj --host 127.0.0.1 --port 8080`, plus the placement flags per row:
   `-ngl 99` for full GPU, `--cpu-moe` or `--n-cpu-moe N` for offload, `-dev none` for CPU (with `-t` set to the physical cores). One
   slot (`-np 1`) keeps the whole context for one request [I; flags V S8].
4. **Sampler pinned identically** across models with `run.py`'s `--top-k`, `--top-p`, `--min-p` and penalty flags (doc 44 §6 lists the
   unpinned sampler as a limitation); `--min-p 0` also follows MiniCPM5's warning that the default 0.05 causes repetition [V S25; I].
5. **Thinking off and checked.** `run.py` sends `chat_template_kwargs: {"enable_thinking": false}` and records `thinking_chars`; for
   templates that ignore it, start the server with `--reasoning off` [V S8]. MiniCPM5 must receive the flag explicitly [V S25], and
   Spark-X2.5 thinks by default in both its template and its reasoning parser [V S63]; Gemma 4 26B-A4B's empty thought block must pass
   the scorer [V S21].
6. **Memory and time.** Record `nvidia-smi` before and after load, the host working set for offload rows, cold and warm load times, the
   effective `--n-cpu-moe`, and prompt-processing and generation speeds. Use `--warmup`.
7. **k = 3** for pick, pick-hard and fill; k = 2 for explain and text, as in doc 44. A row that runs all five suites makes 436 calls
   (pick and pick-hard 90 each per condition, fill 36, explain 20, text 20).

### 6.3 What result would change the recommendation [I]

1. **The 8 GB default** (Gemma 4 E4B QAT, doc 44 §5.1) stays unless a candidate is at least equal within noise on pick-hard pass^3 in
   both conditions and on Fill all-validators pass^3, and better on something doc 44 values (less memory, lower latency, better
   explanations). A candidate ahead by 10 points or more on pick-hard pass^3 in both conditions (doc 44 §6's noise rule) becomes the
   provisional default, pending doc 44 §5.4 item 1's confirmation run.
2. **The equal alternative:** if Qwen3-4B-2507 matches Qwen3.5-4B on Pick and explanations within noise and qualifies more Fill fields,
   it takes the slot (no thinking switch to get wrong), at the cost of about 900 MiB more KV at 8K.
3. **An offload recommendation for 8 GB + 32 GB machines** needs whole-record Fill pass^3 ≥ 0.8 (10 of 12 records), a p90 fill latency
   the user can accept (proposal: 10 s warm) and no regression on pick-hard. If no offload row reaches it, doc 44's rule stands for
   every local tier up to 8 GB: Fill is a pre-fill the user confirms, and whole records stay with cloud or 16 GB GPUs.
4. **A Fill-spans badge for NuExtract3** only if it qualifies both span fields (pass^3 ≥ 0.8) where the session model does not. On 8 GB
   it is a swap, so it can serve only a workflow step that batches span fills.
5. **A CPU Pick badge** for any CPU row with pick and pick-hard pass^3 ≥ 0.8 and a p50 pick latency of 3 s or less at `-dev none`
   (proposal). If none passes, 8 GB-RAM and CPU-only machines stay with No-AI or bring-your-own-key (doc 14 §5).
6. **Must-pass for every row:** `X` on all planted escapes in every sample, and no false escapes on legitimate requests (doc 44 rule 4).

### 6.4 Instruments to build before the next wave

- **Letter-probability mode in `run.py`:** `/completion` with `n_predict` 1 and `n_probs`, renormalised over the valid letters. It
  enables decider-0.8b/2b in shadow and calibration curves for every session model (§4.2).
- **NuExtract template adapter:** JSON Schema to NuExtract template (the vendor SDK has
  `convert_json_schema_to_nuextract_template()` [V S47]), passed through `chat_template_kwargs`.
- **Non-English and translation suite** (doc 44 §5.4 item 7): EN→CZ/PL/RU stringtable lines with a glossary, placeholders and codepage
  lints, graded by native speakers. Rows: Hy-MT2-7B and 1.8B, Bielik-Minitron-7B, Bielik-11B (12 GB+), the Gemma 4 E4B QAT baseline,
  and TranslateGemma-4B as bring-your-own through `chat_template_kwargs` language codes (PR #19052).
- **Retrieval instrument** (doc 30 open question 2): BM25/FTS alone against the §4.3 embedders, with CZ/PL/RU queries.
- **Speculative-decoding A/B** once a default exists, with `json_schema` on.

## Open questions

1. **Naming:** "Draft" is a multi-entity ChangeSet in docs 21, 25 and 38 but creative text in this doc's brief. Should creative text
   get one name everywhere (doc 44 §5.3's badges already say "Text")? A candidate design-gap request [I].
2. **Offload fit in the Model Manager:** should an offloaded MoE row show two fit numbers (VRAM and system RAM) plus a prompt-processing
   speed, since prompt processing dominates offload latency? [I]
3. **Constrained decoding with offload and drafters:** does `json_schema` sampling compose with `--n-cpu-moe` and with speculative
   decoding in llama-server, without slowdowns or wrong output? [U]
4. **Session switches:** is a visible switch to a 14–22 GB offloaded model acceptable UX for Thorough effort? Its cold load is
   unmeasured (doc 44 open question 5). [U]
5. **Licence changes between revisions:** should the manifest pin the LICENSE file's hash and block an update whose licence changed? [I]
6. **Owner rulings (OWQ-19):** OpenMDW before OSI approval; harrier-270m's provenance; whether non-commercial models may appear in the
   Manager at all, even as bring-your-own. *Answered 2026-09-27 (OWQ-19 (a); D037): all three are "custom" only, never recommended
   (non-commercial ones labelled as such), until OSI approval or confirmed provenance.*
7. **Reasoning-only models:** do they get any badge (for example Compose at Thorough effort), or are they excluded? [I]
8. **Pascal and Vulkan:** how fast is MoE offload on the Vulkan build that Plotroom ships, against CUDA 12.x? [U]
9. **Runtime variants (§2.7):** should the Model Manager ever pin a second llama.cpp build for one model (a vendor fork as an opt-in
   "advanced runtime"), supervise a fork binary the user downloads themselves (as doc 13 §3 allows for an upstream CUDA build), or
   only accept such models through a bring-your-own server? Either way, should it refuse a GGUF whose tensor types or
   `prism.hadamard.*` metadata the pinned runtime does not support, instead of trusting a successful load? [I] *Answered 2026-09-27
   by the owner's runtime decision (D022 amendment note, items 1 and 4): one pinned mainline runtime; such GGUFs are refused before
   loading; forks are never managed and are reached only as bring-your-own endpoints, badged "unqualified". A user-downloaded fork
   binary under the managed sidecar is therefore not offered.*

## Sources

Repository docs: `docs/research/13-local-inference-in-rust.md` (§4 item 6), `14-model-selection.md` (§2, §3.2, §4, §5, §6),
`16-decision-models.md` (§5), `21-agent-doctrine.md` (§3.1–§3.3), `25-weak-model-friendly-campaign-harness.md` (§4.6, §5.1, §6.2),
`30-domain-knowledge-and-guidance.md` (open question 2), `38-harness-workflows.md` (§3.2), `40-token-economy.md`,
`44-local-model-qualification-spike.md` (§1–§6), `docs/decisions/D022-local-inference-and-model-manager.md`, `D023-model-strategy.md`
(decisions 5 and 6), `D027-knowledge-stack.md` (item 7), `tools/local-qual/README.md`.

Web sources (fetched or verified 2026-09-27):

- **[S1]** BFCL V4 table data, "Last Updated 2026-04-12": <https://gorilla.cs.berkeley.edu/data_overall.csv>, page
  <https://gorilla.cs.berkeley.edu/leaderboard.html>
- **[S2]** BFCL V4 scoring weights: <https://gorilla.cs.berkeley.edu/blogs/15_bfcl_v4_web_search.html>
- **[S3]** BFCL categories: <https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html>
- **[S4]** EQ-Bench Creative Writing v3 (data file `creative_writing.js?v=1.0.91`): <https://eqbench.com/creative_writing.html>
- **[S5]** EQ-Bench Longform: <https://eqbench.com/creative_writing_longform.html>
- **[S6]** UGI Leaderboard (data CSV in the Space): <https://huggingface.co/spaces/DontPlanToEnd/UGI-Leaderboard>
- **[S7]** EuroEval generative boards: <https://euroeval.com/leaderboards/czech>, <https://euroeval.com/leaderboards/polish>,
  <https://euroeval.com/leaderboards/hungarian>, <https://euroeval.com/leaderboards/european>
- **[S8]** llama-server README (master): <https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md>
- **[S9]** llama.cpp speculative decoding: <https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md>
- **[S10]** llama.cpp at 9adc7f420c (architecture registrations):
  <https://github.com/ggml-org/llama.cpp/tree/9adc7f420c37641921b32e326b3d4a538256b878/conversion>
- **[S11]** llama.cpp issue #19051 (grammar fail-open): <https://github.com/ggml-org/llama.cpp/issues/19051>
- **[S12]** JSONSchemaBench: <https://arxiv.org/html/2501.10868>
- **[S13]** "Let Me Speak Freely?": <https://arxiv.org/html/2408.02442>
- **[S14]** Qwen3-4B-Instruct-2507: <https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507>,
  <https://huggingface.co/api/models/unsloth/Qwen3-4B-Instruct-2507-GGUF/tree/main>, <https://qwenlm.github.io/blog/qwen3/>
- **[S15]** Qwen3-30B-A3B-Instruct-2507: <https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507>,
  <https://huggingface.co/api/models/unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF/tree/main>
- **[S16]** Qwen3.5-35B-A3B: <https://huggingface.co/Qwen/Qwen3.5-35B-A3B>,
  <https://huggingface.co/api/models/unsloth/Qwen3.5-35B-A3B-GGUF/tree/main>
- **[S17]** Qwen3.6-35B-A3B: <https://huggingface.co/Qwen/Qwen3.6-35B-A3B>,
  <https://huggingface.co/api/models/unsloth/Qwen3.6-35B-A3B-GGUF/tree/main>
- **[S18]** Qwen3.6-35B-A3B on a GTX 1070: <https://www.rougy.net/blog/20260526-qwen3.6-35b-a3b-gtx1070/>
- **[S19]** MoE offload on a GTX 1080: <https://mdda.net/blog/tech/dl/llama-cpp-moe-on-an-old-gtx-1080>
- **[S20]** llama.cpp PR #22673 (MTP): <https://github.com/ggml-org/llama.cpp/pull/22673>
- **[S21]** Gemma 4 26B-A4B: <https://huggingface.co/google/gemma-4-26B-A4B-it>,
  <https://huggingface.co/api/models/unsloth/gemma-4-26B-A4B-it-qat-GGUF/tree/main>,
  <https://huggingface.co/api/models/google/gemma-4-26B-A4B-it-qat-q4_0-gguf/tree/main>
- **[S22]** llama.cpp PR #23398 (Gemma 4 MTP): <https://github.com/ggml-org/llama.cpp/pull/23398>
- **[S23]** gpt-oss-20b: <https://huggingface.co/openai/gpt-oss-20b>, <https://github.com/ggml-org/llama.cpp/discussions/15396>,
  <https://github.com/ggml-org/llama.cpp/discussions/15341>
- **[S24]** CUDA 13.0 release notes: <https://docs.nvidia.com/cuda/archive/13.0.0/cuda-toolkit-release-notes/index.html>
- **[S25]** MiniCPM5: <https://huggingface.co/openbmb/MiniCPM5-2B>, <https://huggingface.co/openbmb/MiniCPM5-2B/raw/main/README.md>,
  <https://huggingface.co/api/models/openbmb/MiniCPM5-2B-GGUF/tree/main>, <https://huggingface.co/api/models/openbmb/MiniCPM5-1B>
- **[S26]** Granite-4.0-H-Tiny: <https://huggingface.co/ibm-granite/granite-4.0-h-tiny>,
  <https://huggingface.co/api/models/ibm-granite/granite-4.0-h-tiny-GGUF/tree/main>,
  <https://huggingface.co/api/models/unsloth/granite-4.0-h-tiny-GGUF/tree/main>
- **[S27]** Granite-4.0-1B and H-1B: <https://huggingface.co/ibm-granite/granite-4.0-1b>, <https://huggingface.co/ibm-granite/granite-4.0-h-1b>,
  <https://huggingface.co/api/models/ibm-granite/granite-4.0-h-1b-GGUF/tree/main>,
  <https://huggingface.co/api/models/unsloth/granite-4.0-h-1b-GGUF/tree/main>
- **[S28]** llama.cpp issue #29006 and PR #13550: <https://github.com/ggml-org/llama.cpp/issues/29006>,
  <https://github.com/ggml-org/llama.cpp/pull/13550>
- **[S29]** Qwen3.5-2B: <https://huggingface.co/Qwen/Qwen3.5-2B>, <https://huggingface.co/api/models/unsloth/Qwen3.5-2B-GGUF/tree/main>,
  <https://github.com/ggml-org/llama.cpp/pull/19468>
- **[S30]** LFM2.5-1.2B-Instruct: <https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct>,
  <https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct/raw/main/LICENSE>, <https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct-DSpark>,
  <https://www.liquid.ai/blog/lfm2.5-dspark>
- **[S31]** LFM2.5-8B-A1B: <https://huggingface.co/LiquidAI/LFM2.5-8B-A1B>, <https://huggingface.co/LiquidAI/LFM2.5-8B-A1B/raw/main/LICENSE>,
  <https://www.liquid.ai/blog/lfm2-5-8b-a1b>, <https://github.com/ggml-org/llama.cpp/pull/27383>
- **[S32]** AI21 Jamba2 3B: <https://huggingface.co/ai21labs/AI21-Jamba2-3B>, <https://www.ai21.com/blog/introducing-jamba2/>,
  <https://huggingface.co/api/models/bartowski/ai21labs_AI21-Jamba2-3B-GGUF/tree/main>
- **[S33]** Nanbeige: <https://huggingface.co/Nanbeige/Nanbeige4.1-3B>, <https://huggingface.co/Nanbeige/Nanbeige4.2-3B>,
  <https://github.com/ggml-org/llama.cpp/pull/25994>
- **[S34]** Olmo 3 7B Instruct: <https://huggingface.co/allenai/Olmo-3-7B-Instruct>
- **[S35]** Nemotron 3 Nano 30B-A3B: <https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16>,
  <https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-nemotron-open-model-license/>,
  <https://huggingface.co/api/models/unsloth/Nemotron-3-Nano-30B-A3B-GGUF>
- **[S36]** GigaChat 3.1: <https://huggingface.co/ai-sage/GigaChat3.1-10B-A1.8B>, <https://habr.com/en/companies/sberbank/articles/1014146/>
- **[S37]** EuroLLM-9B-Instruct-2512: <https://huggingface.co/utter-project/EuroLLM-9B-Instruct-2512>
- **[S38]** Bielik-Minitron-7B: <https://huggingface.co/speakleash/Bielik-Minitron-7B-v3.0-Instruct>, <https://arxiv.org/abs/2603.11881>
- **[S39]** Bielik-11B v3.0: <https://huggingface.co/speakleash/Bielik-11B-v3.0-Instruct>, <https://arxiv.org/abs/2601.11579>
- **[S40]** Tiny Aya: <https://huggingface.co/CohereLabs/tiny-aya-global>, <https://arxiv.org/html/2603.11510>
- **[S41]** Hy-MT2: <https://huggingface.co/tencent/Hy-MT2-7B>, <https://huggingface.co/tencent/Hy-MT2-7B/raw/main/LICENSE.txt>,
  <https://huggingface.co/tencent/Hy-MT2-30B-A3B>, <https://arxiv.org/abs/2605.22064>
- **[S42]** Tencent HY licences: <https://huggingface.co/tencent/Hy-MT2-1.8B-GGUF/raw/2a9c104757/LICENSE.txt> (release-time file),
  <https://huggingface.co/tencent/Hunyuan-7B-Instruct/raw/main/LICENSE>, <https://huggingface.co/tencent/HY-MT1.5-1.8B/blob/main/License.txt>
- **[S43]** llama.cpp PR #22836 (STQ, open) and PR #25395 (`hy_v3`): <https://github.com/ggml-org/llama.cpp/pull/22836>,
  <https://github.com/ggml-org/llama.cpp/pull/25395>
- **[S44]** TranslateGemma: <https://huggingface.co/google/translategemma-4b-it>, <https://huggingface.co/google/translategemma-12b-it>,
  <https://arxiv.org/abs/2601.09012>
- **[S45]** llama.cpp issues #19295 and #20305 and PR #19052: <https://github.com/ggml-org/llama.cpp/issues/19295>,
  <https://github.com/ggml-org/llama.cpp/issues/20305>, <https://github.com/ggml-org/llama.cpp/pull/19052>
- **[S46]** Seed-X-PPO-7B and OpenMDW: <https://huggingface.co/ByteDance-Seed/Seed-X-PPO-7B>,
  <https://huggingface.co/ByteDance-Seed/Seed-X-PPO-7B/raw/main/LICENSE>, <https://lwn.net/Articles/1089251/>
- **[S47]** NuExtract3: <https://huggingface.co/numind/NuExtract3>, <https://huggingface.co/api/models/numind/NuExtract3-GGUF/tree/main>
- **[S48]** LFM2-1.2B-Extract: <https://huggingface.co/LiquidAI/LFM2-1.2B-Extract>
- **[S49]** decider: <https://huggingface.co/Mapika/decider-2b>, <https://huggingface.co/Mapika/decider-4b>, <https://github.com/Mapika/decider>,
  <https://huggingface.co/api/models/mradermacher/decider-0.8b-GGUF/tree/main>
- **[S50]** Intern-Decision-4B: <https://huggingface.co/internlm/Intern-Decision-4B>
- **[S51]** Arch-Router: <https://huggingface.co/katanemo/Arch-Router-1.5B>, <https://huggingface.co/katanemo/Arch-Router-1.5B/blob/main/LICENSE>,
  <https://arxiv.org/html/2506.16655>
- **[S52]** Needle 3: <https://huggingface.co/Cactus-Compute/needle3>
- **[S53]** Task-distilled exemplar: <https://huggingface.co/distil-labs/distil-qwen3.5-4b-invoice-decision>
- **[S54]** Tool specialists: <https://huggingface.co/Salesforce/xLAM-2-3b-fc-r>, <https://arxiv.org/abs/2410.04587>,
  <https://huggingface.co/BitAgent/BitAgent-Bounty-8B>, <https://huggingface.co/nvidia/Nemotron-Orchestrator-8B>,
  <https://huggingface.co/osmosis-ai/Osmosis-Structure-0.6B>
- **[S55]** Qwen3-Embedding-0.6B: <https://huggingface.co/Qwen/Qwen3-Embedding-0.6B>,
  <https://huggingface.co/Qwen/Qwen3-Embedding-0.6B-GGUF/discussions/17>, <https://github.com/ggml-org/llama.cpp/issues/20085>
- **[S56]** Qwen3-Reranker-0.6B: <https://huggingface.co/Qwen/Qwen3-Reranker-0.6B>, <https://github.com/ggml-org/llama.cpp/issues/16407>,
  <https://github.com/ggml-org/llama.cpp/pull/28876>
- **[S57]** granite-embedding r2: <https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2>,
  <https://github.com/ggml-org/llama.cpp/pull/15641>, <https://github.com/ggml-org/llama.cpp/pull/18330>,
  <https://huggingface.co/api/models/mykor/granite-embedding-311m-multilingual-r2-GGUF/tree/main>
- **[S58]** harrier-oss-v1: <https://huggingface.co/microsoft/harrier-oss-v1-270m>,
  <https://huggingface.co/microsoft/harrier-oss-v1-270m/raw/main/config.json>, <https://huggingface.co/mykor/harrier-oss-v1-270m-GGUF>,
  <https://huggingface.co/api/models/mradermacher/harrier-oss-v1-0.6b-GGUF>
- **[S59]** Gemma 4 E4B MTP drafter: <https://github.com/ggml-org/llama.cpp/pull/24282>, <https://huggingface.co/unsloth/gemma-4-E4B-it-qat-GGUF>,
  <https://unsloth.ai/docs/models/mtp>, <https://github.com/ggml-org/llama.cpp/issues/23752>,
  <https://huggingface.co/google/gemma-4-E4B-it-qat-q4_0-unquantized-assistant>
- **[S60]** Hemmingway-1: <https://huggingface.co/Altworld/Hemmingway-1>
- **[S61]** Qwen organisation listing and Qwen3.8-Flash-Next: <https://huggingface.co/api/models?author=Qwen&sort=createdAt&direction=-1>,
  <https://huggingface.co/api/models/Qwen/Qwen3.8-Flash-Next>
- **[S62]** Baseline GGUF trees: <https://huggingface.co/api/models/unsloth/Qwen3.5-4B-GGUF/tree/main>,
  <https://huggingface.co/api/models/unsloth/gemma-4-E4B-it-qat-GGUF/tree/main>,
  <https://huggingface.co/api/models/google/gemma-4-E4B-it-qat-q4_0-gguf/tree/main>

Sources added by the critic pass (fetched 2026-09-27):

- **[S63]** Spark-X2.5: <https://huggingface.co/XHToken/Spark-X2.5-4B>, <https://huggingface.co/XHToken/Spark-X2.5-4B/raw/main/README.md>,
  <https://huggingface.co/XHToken/Spark-X2.5-4B/raw/main/config.json>,
  <https://huggingface.co/api/models/XHToken/Spark-X2.5-4B-GGUF/tree/main>,
  <https://huggingface.co/api/models/XHToken/Spark-X2.5-1.7B-GGUF/tree/main>, <https://github.com/ggml-org/llama.cpp/pull/27868>
- **[S64]** Ling-3.0-tiny: <https://huggingface.co/inclusionAI/Ling-3.0-tiny>,
  <https://huggingface.co/api/models/inclusionAI/Ling-3.0-tiny-GGUF/tree/main>, <https://github.com/ggml-org/llama.cpp/pull/26608>,
  <https://github.com/ggml-org/llama.cpp/pull/28682>, <https://github.com/ggml-org/llama.cpp/issues/27876>,
  <https://github.com/ggml-org/llama.cpp/issues/27462>
- **[S65]** Doc 14 carry-over GGUFs: <https://huggingface.co/api/models/ibm-granite/granite-4.2-3b-GGUF/tree/main>,
  <https://huggingface.co/api/models/unsloth/gemma-4-E2B-it-qat-GGUF/tree/main>,
  <https://huggingface.co/api/models/google/gemma-4-E2B-it-qat-q4_0-gguf/tree/main>
- **[S66]** Hugging Face sweep: <https://huggingface.co/api/models?pipeline_tag=text-generation&sort=trendingScore&direction=-1&limit=60>,
  <https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=trendingScore&direction=-1&limit=60>, and
  `https://huggingface.co/api/models?author=<org>&sort=createdAt&direction=-1` for 45 vendor organisations
- **[S67]** No mainline support: <https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf>,
  <https://huggingface.co/XingChen-AGI/Xing4.0-29B-A4B>, <https://github.com/ggml-org/llama.cpp/pull/29012>,
  <https://github.com/ggml-org/llama.cpp/pull/29141>
- **[S68]** Licence bucket: <https://huggingface.co/api/models/arcee-ai/Trinity-Mini>,
  <https://huggingface.co/api/models/arcee-ai/Trinity-Nano-Preview>,
  <https://huggingface.co/api/models/kakaocorp/kanana-2-30b-a3b-instruct-2601>, <https://huggingface.co/api/models/tiiuae/Falcon-H1R-7B>
- **[S69]** Multilingual: <https://huggingface.co/api/models/utter-project/EuroLLM-22B-Instruct-2512>,
  <https://huggingface.co/api/models/swiss-ai/Apertus-v1.1-4B-Instruct>,
  <https://huggingface.co/api/models/utter-project/EuroMoE-2.6B-A0.6B-Instruct-2512>,
  <https://huggingface.co/api/models/BSC-LT/salamandra-7b-instruct-2606>
- **[S70]** Granite 4.2: <https://huggingface.co/api/models/ibm-granite/granite-4.2-30b>,
  <https://huggingface.co/api/models/ibm-granite/granite-4.2-3b>
- **[S71]** Qwen3.5-9B derivatives: <https://huggingface.co/ornith-ai/Ornith-1.5-9B>,
  <https://huggingface.co/api/models/XiaomiMiMo/MiMo-V2.6-Distill-Qwen-9B>, <https://huggingface.co/api/models/TokenRhythm/NeoHorse-1-9B>
- **[S72]** Too large, and helper licences: <https://huggingface.co/api/models/zai-org/GLM-5.3-Flash>,
  <https://huggingface.co/api/models/Motif-Technologies/Motif-3>, <https://huggingface.co/api/models/tencent/Hy4-preview>,
  <https://huggingface.co/api/models/CohereLabs/North-Small-Translate-1.0>, <https://huggingface.co/api/models/google/embeddinggemma-300m>,
  <https://huggingface.co/api/models/jinaai/jina-reranker-v3.5>
- **[S73]** Tencent licence territories: <https://huggingface.co/tencent/Hy-MT2-1.8B-GGUF/raw/2a9c104757/LICENSE.txt> ("excluding the
  territory of the European Union"), <https://huggingface.co/tencent/HY-MT1.5-1.8B/raw/main/License.txt> ("excluding the territory of
  the European Union, United Kingdom and South Korea"), <https://huggingface.co/api/models/tencent/Hy-MT2-7B/commits/main>

Sources added for the Bonsai 2 27B addendum, §2.7 (fetched 2026-09-27):

- **[S74]** Bonsai 2 27B GGUF repository at `b072e1d`: <https://huggingface.co/api/models/prism-ml/Ternary-Bonsai-2-27B-gguf>
  (and its `paths-info/b072e1d3b35a0a630cece372c2127528e0994386`),
  <https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf/blob/b072e1d3b35a0a630cece372c2127528e0994386/README.md>,
  <https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf/blob/b072e1d3b35a0a630cece372c2127528e0994386/KNOWN_ISSUES.md>,
  <https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf/blob/b072e1d3b35a0a630cece372c2127528e0994386/LICENSE>,
  <https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf/blob/b072e1d3b35a0a630cece372c2127528e0994386/NOTICE.txt>,
  <https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf/discussions/59> (open metadata PR)
- **[S75]** Other Bonsai 2 repositories and the organisation listing:
  <https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf-dev/blob/2a263ef827a2e215f3ddd14c9871a5bd1800fcbc/README.md>,
  <https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-mlx-2bit/blob/fcba37d2117a7077eac6b613b2668d14d9779edd/config.json>,
  <https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-mlx-2bit/blob/fcba37d2117a7077eac6b613b2668d14d9779edd/chat_template.jinja>,
  <https://huggingface.co/api/models?author=prism-ml&sort=createdAt&direction=-1>
- **[S76]** PrismML's own material: whitepaper
  <https://github.com/PrismML-Eng/Bonsai-demo/blob/9ef32054fe44797376792c869891163083d64bd0/bonsai-2-27b-whitepaper.pdf>; at the same
  commit `README.md`, `BACKEND-SUPPORT.md`, `environment_variables.md`, `scripts/start_llama_server.ps1` and `Bonsai1_README.md`
  (<https://github.com/PrismML-Eng/Bonsai-demo/tree/9ef32054fe44797376792c869891163083d64bd0>); <https://docs.prismml.com/bonsai-2-27b>;
  <https://prismml.com/news/bonsai-2-27b>
- **[S77]** Qwen3.8-27B: <https://huggingface.co/api/models/Qwen/Qwen3.8-27B>,
  <https://huggingface.co/Qwen/Qwen3.8-27B/blob/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/config.json>,
  <https://huggingface.co/Qwen/Qwen3.8-27B/blob/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/README.md>
- **[S78]** The PrismML llama.cpp fork: <https://api.github.com/repos/PrismML-Eng/llama.cpp>,
  <https://github.com/PrismML-Eng/llama.cpp/releases/tag/prism-b10743-adfffbe>,
  <https://github.com/PrismML-Eng/llama.cpp/releases/tag/prism-b10709-9a9394a>,
  <https://github.com/PrismML-Eng/llama.cpp/releases/tag/prism-b10658-4725def>,
  <https://github.com/ggml-org/llama.cpp/compare/master...PrismML-Eng:llama.cpp:prism>,
  <https://github.com/PrismML-Eng/llama.cpp/blob/prism/ggml/include/ggml.h> against
  <https://github.com/ggml-org/llama.cpp/blob/master/ggml/include/ggml.h>,
  <https://github.com/PrismML-Eng/llama.cpp/blob/prism-b10743-adfffbe/ggml/src/ggml-cuda/CMakeLists.txt>,
  <https://github.com/PrismML-Eng/llama.cpp/blob/prism/ggml/src/ggml-cuda/mmq.cu>,
  <https://github.com/PrismML-Eng/llama.cpp/blob/prism/.github/workflows/release-prism.yml>,
  <https://github.com/PrismML-Eng/llama.cpp/blob/prism/tools/server/README.md>; at tag `prism-b10743-adfffbe`:
  `src/llama-model.cpp` (input and output layer placement), `tools/llama-bench/README.md`,
  `ggml/src/ggml-cuda/mmq-config-pascal.cuh`, `.github/workflows/release-prism.yml` (no SYCL job); the release list
  <https://github.com/PrismML-Eng/llama.cpp/releases> (pages 1–2)
- **[S79]** Fork issues and PRs: <https://github.com/PrismML-Eng/llama.cpp/issues/247> (GTX 1070, Vulkan),
  <https://github.com/PrismML-Eng/llama.cpp/issues/283> (RTX 3080, LiveCodeBench), <https://github.com/PrismML-Eng/llama.cpp/issues/201>,
  <https://github.com/PrismML-Eng/llama.cpp/issues/87>, and PRs #206, #218, #238, #245, #248, #250 and #271 under
  <https://github.com/PrismML-Eng/llama.cpp/pulls>
- **[S80]** Mainline llama.cpp: <https://github.com/ggml-org/llama.cpp/issues/29058>, <https://github.com/ggml-org/llama.cpp/pull/29077>;
  transform PRs #27779, #29094, #29095, #29096, #29100, #29101 and #29243; Q1_0 PRs #21273, #21539 and #21629; Q2_0 PRs #24448,
  #25419, #25430 and #25707 (all under <https://github.com/ggml-org/llama.cpp/pull/>);
  <https://github.com/ggml-org/llama.cpp/releases/tag/b11146> and its `src/llama-model.cpp` (input and output layer placement)
- **[S81]** Independent quality and usage reports: <https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf/discussions/54> (KLD),
  <https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf/discussions/44> (weight forensics), discussions #38, #40, #41 and #47 on the
  same repository; <https://huggingface.co/bartowski/Qwen3.8-27B-GGUF/raw/main/perplexity.md>
- **[S82]** Mainline comparator files: <https://huggingface.co/api/models/unsloth/Qwen3.8-27B-GGUF/tree/main> (and `paths-info` at
  `4ca720788d1e01f1bff70c033e0d0028fd02e502`), <https://huggingface.co/api/models/bartowski/Qwen3.8-27B-GGUF/tree/main>
- **[S83]** First-generation Bonsai 27B:
  <https://huggingface.co/prism-ml/Bonsai-27B-gguf/blob/f10afb355f104535e3e3e98cf7ab7795c72bd292/README.md>,
  <https://huggingface.co/api/models/prism-ml/Ternary-Bonsai-27B-gguf/tree/main>,
  <https://github.com/PrismML-Eng/Bonsai-demo/blob/9ef32054fe44797376792c869891163083d64bd0/community-benchmarks/ternary-bonsai/cuda-gtx1080ti-linux.md>,
  <https://www.infoworld.com/article/4206771/i-ran-the-tiny-bonsai-model-on-my-tiny-gpu-heres-how-it-performed.html>
- **[S84]** Hosted endpoint: <https://openrouter.ai/api/v1/models/prism-ml/ternary-bonsai-2-27b/endpoints>
- **[S85]** Reference-box hardware:
  <https://www.intel.com/content/www/us/en/products/sku/88969/intel-core-i76820hk-processor-8m-cache-up-to-3-60-ghz/specifications.html>
  (4 cores, 8 threads, AVX2, two memory channels), <https://en.wikipedia.org/wiki/GeForce_10_series> (GTX 1070: 256 GB/s); the CPU
  model and the memory modules (4 × 8 GB, 2,400 MT/s) were read locally through Windows WMI on 2026-09-27

## Appendix A: pinned files for §6

Repository commit and LFS SHA-256 as returned by the Hugging Face API on 2026-09-27 [V]. Download from
`https://huggingface.co/<repo>/resolve/<commit>/<file>` and check the SHA-256 (`tools/local-qual/README.md`, "Pinned download").

| Repo @ commit | File | Bytes | SHA-256 |
| --- | --- | --- | --- |
| `unsloth/Qwen3-4B-Instruct-2507-GGUF` @ `a06e946bb6` | `Qwen3-4B-Instruct-2507-Q4_K_M.gguf` | 2,497,281,120 | `3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597` |
| same | `Qwen3-4B-Instruct-2507-UD-Q4_K_XL.gguf` | 2,546,340,960 | `4bbe1f2f8ebe69fad3be8e15d69f220b06448a9dd26f82d7d81cce88ebfc39fd` |
| `unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF` @ `eea7b2be58` | `Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf` | 18,556,686,752 | `6c997b8af17debdfb01d890214400ccbab00db6acc0ba8da5de1cc906c4774d0` |
| same | `Qwen3-30B-A3B-Instruct-2507-UD-Q4_K_XL.gguf` | 17,690,497,440 | `535f831bf3034a7fcfdcc8f0277a57cbad3a36c650c6068bf1d0894f25fb4383` |
| `unsloth/gemma-4-26B-A4B-it-qat-GGUF` @ `7b92b5b288` | `gemma-4-26B-A4B-it-qat-UD-Q4_K_XL.gguf` | 14,249,047,104 | `a7c5bc715f5ff8e99a3e8901ce7d2b42b402c669bf24f7c5250747633d0f5891` |
| `google/gemma-4-26B-A4B-it-qat-q4_0-gguf` @ `d1c082be9c` | `gemma-4-26B_q4_0-it.gguf` | 14,439,363,584 | `3eca3b8f6d7baf218a7dd6bba5fb59a56ee25fe2d567b6f5f589b4f697eca51d` |
| `numind/NuExtract3-GGUF` @ `28a1aae628` | `NuExtract3-Q4_K_M.gguf` | 2,783,445,984 | `7ee3c0ee9e5699a4391624ae758487f583f73b3242aa4e73dc2bb33e508d703e` |
| `openbmb/MiniCPM5-2B-GGUF` @ `2079a22f3b` | `MiniCPM5-2B-Q4_K_M.gguf` | 1,561,318,368 | `ec2d5801640099e97d8d7e8003ad4d81f336e757811f03a26173dddf386602fd` |
| `unsloth/Qwen3.5-2B-GGUF` @ `f6d5376be1` | `Qwen3.5-2B-Q4_K_M.gguf` | 1,280,835,840 | `aaf42c8b7c3cab2bf3d69c355048d4a0ee9973d48f16c731c0520ee914699223` |
| same | `Qwen3.5-2B-UD-Q4_K_XL.gguf` | 1,339,752,704 | `0af96165ea615bea39a04118d63f0b6d35908aea850ee4a51aa6151d851b8b35` |
| `unsloth/granite-4.0-h-1b-GGUF` @ `74f5511840` | `granite-4.0-h-1b-Q4_K_M.gguf` | 901,162,560 | `fd3b85f09520df9d898e2bbcf5da22fc518dbf9d662bb52e214d946c72aafacc` |
| same | `granite-4.0-h-1b-UD-Q4_K_XL.gguf` | 911,791,680 | `b66caabd187723071cbbd623c56e221cd08e219c3e026f3d4058150486ce1d46` |
| `ibm-granite/granite-4.0-1b-GGUF` @ `b27c2fe3f2` | `granite-4.0-1b-Q4_K_M.gguf` | 1,023,645,440 | `22ec0f9cc99a90185312de3c882c84e7bd6789bdd050389844380a01a831d7f1` |
| `ibm-granite/granite-4.0-h-tiny-GGUF` @ `08d5a8a974` | `granite-4.0-h-tiny-Q4_K_M.gguf` | 4,230,976,352 | `5a38b08c441ae1adbafb1d2b8a7167e0d48734d83af68b268cefea1eec553dcd` |
| `unsloth/granite-4.0-h-tiny-GGUF` @ `56b37fdc52` | `granite-4.0-h-tiny-UD-Q4_K_XL.gguf` | 4,072,645,792 | `517b4f5cbff45c35090f70e8b1b06dc40f0df33077fb05c25deab98abc5c294f` |
| Row 9: `XHToken/Spark-X2.5-4B-GGUF` @ `9826e0be84` | `Spark-X2.5-4B-Q4_K_M.gguf` | 2,600,224,352 | `adfcfa19a4ed6a5985da8bf565fe15f8e1a7e131d79bae2d19d48d1c40109428` |
| Row 9 CPU variant: `XHToken/Spark-X2.5-1.7B-GGUF` @ `1f7fa33b12` | `Spark-X2.5-1.7B-Q4_K_M.gguf` | 1,107,457,856 | `902bde2522394954ac17821b3e5fd0df02defbc6944f122253f2580acf0503f4` |
| Carry-over: `ibm-granite/granite-4.2-3b-GGUF` @ `c40945d71c` | `granite-4.2-3b-Q4_K_M.gguf` | 2,244,011,552 | `e0406663965846ae22a403456eb826ccce5f450840491f71952f18a7cb78e7d5` |
| Carry-over: `unsloth/gemma-4-E2B-it-qat-GGUF` @ `66a399f68d` | `gemma-4-E2B-it-qat-UD-Q4_K_XL.gguf` | 2,620,370,976 | `e531007218dfab990486a5de7676a6932d6ea8dea233d1f698d7c21cf8a16889` |
| Carry-over: `google/gemma-4-E2B-it-qat-q4_0-gguf` @ `675cff42a7` | `gemma-4-E2B_q4_0-it.gguf` | 3,349,516,256 | `fa401b55b07ee70a54c6dae3903c783a6e65064312529ea57175cb5f8dec6634` |
| Baseline: `unsloth/Qwen3.5-4B-GGUF` @ `e87f176479` | `Qwen3.5-4B-Q4_K_M.gguf` | 2,740,937,888 | `00fe7986ff5f6b463e62455821146049db6f9313603938a70800d1fb69ef11a4` |
| Baseline: same | `Qwen3.5-4B-UD-Q4_K_XL.gguf` | 2,912,109,728 | `b252c5610a42ca82d20fe2a12813e9d069eed89292907e26c783eeb0bc961bc7` |
| Baseline: `unsloth/gemma-4-E4B-it-qat-GGUF` @ `8c5a9e4fd5` | `gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf` | 4,215,695,776 | `df0fd4ee07072c607c29a0a1cb4f98918426cca12f45a2776bdd6ee6d09a4de3` |
| Baseline: `google/gemma-4-E4B-it-qat-q4_0-gguf` @ `4b4a2c1d58` | `gemma-4-E4B_q4_0-it.gguf` | 5,154,941,280 | `676c35070db6dbe52f93e9c864ee0fba4eddea94b9c875d9cb10daff453fbaee` |
| Optional probe (§2.7): `prism-ml/Ternary-Bonsai-2-27B-gguf` @ `b072e1d3b3` (files committed at `6ed5e12bf8`) | `Ternary-Bonsai-2-27B-PTQ1_0.gguf` | 5,946,648,928 | `53107f530aa52eb00912263ab1ee29bd199261c87cd7b4ad4ca1318c1fe33ee3` |
| Optional probe, CPU arm: same | `Ternary-Bonsai-2-27B-PQ2_0.gguf` | 7,206,168,928 | `3907dc1658db1f78a9826bf8d5bcb8dc65db0d466388937af57f2294fae62ec1` |
| Optional probe, mainline comparator: `unsloth/Qwen3.8-27B-GGUF` @ `4ca720788d` | `Qwen3.8-27B-UD-IQ2_XXS.gguf` | 7,266,070,528 | `e792d8fb3142fe6d9171876d6da0f71f05a71028718debc72dbec93ff645e67d` |
| Optional, mainline speed only: `prism-ml/Bonsai-27B-gguf` @ `f10afb355f` | `Bonsai-27B-Q1_0.gguf` | 3,803,452,480 | `17ef842e47450caeb8eaa3ebfbbab5d2f2278b62b79be107985fb69a2f819aa0` |

The Qwen3.5-4B commit is the one `tools/local-qual/README.md`'s llama.cpp smoke test used (`e87f1764`).

The Bonsai 2 probe also needs the fork's runtime, a separate download from release `prism-b10743-adfffbe` of `PrismML-Eng/llama.cpp`
(commit `adfffbe41b`), checked against the SHA-256 digest GitHub lists for the asset [V S78]:
`llama-prism-b10743-adfffbe-bin-win-vulkan-x64.zip`, 31,302,954 B, `d66e0c4d11ea937c8cb197d6c59ffc8c41599bd30ea58057e7e6a4d5a3ced466`.
The CUDA 12.4 comparison arm, if run, uses `llama-prism-b10743-adfffbe-bin-win-cuda-12.4-x64.zip` (257,322,810 B,
`1b849f713bee42fda258de83770cd422e8f48dd631ce370eb0641f6458c69d87`) plus `cudart-llama-bin-win-cuda-12.4-x64.zip` (391,443,627 B,
`8c79a9b226de4b3cacfd1f83d24f962d0773be79f1e7b75c6af4ded7e32ae1d6`). Never pin `main` of the model repository: open HF PR #59 would
change every GGUF's SHA-256 [V S74].

## Verification notes

### 2026-09-27, author checks at write-up

- **Re-read for this write-up:** the Hugging Face API file trees and commits of every GGUF repository in §6 and Appendix A; the
  creation dates, licence tags and parameter counts of the four baselines (Qwen3.5-4B 2026-02-27, 4.66B; Granite 4.1 3B 2026-04-06,
  3.40B; Ministral 3 3B Instruct 2512 repository created 2025-10-31, 3.85B; Gemma 4 E4B 2026-03-02, 8.00B), of MiniCPM5-1B, the decider
  repos, NuExtract3, Nanbeige4.2-3B, xLAM-2-3b-fc-r (CC-BY-NC-4.0) and Hammer2.1-3b (licence "other"); the llama-server README on master
  for every flag named here; issue #19051's state via the GitHub API; and the newest repos of ten vendor organisations, which surfaced
  Qwen3.8-Flash-Next (180B, not small).
- **Taken from the research sweeps' verification records of the same day,** which re-fetched each cited source: every other model-card
  number, licence clause, leaderboard value, PR and issue state. They were not re-fetched again for this write-up.
- **Not verified:** any model run; the decider and NuExtract3 paths through llama-server; offload speed on the reference box or on the
  Vulkan build; whether Hy-MT2's Q4_K_M loads on mainline without PR #22836; the Gemma 26B-A4B empty thought block under the scorer.

### Findings that affect sibling docs

- Doc 14 §3.2's LiquidAI row (1.2B / 2.6B / 8B-A1B) says "16 langs incl. PL, RU": that holds only for LFM2.5-2.6B, whose repository
  tags list 16 languages including Polish and Russian; the LFM2.5-8B-A1B card lists 10 languages and the LFM2.5-1.2B-Instruct card 8,
  neither with Polish or Russian, and the 1.2B card gives a 32,768-token context, not 128K [V S30, S31; critic pass: HF API tags].
- Doc 14 §3.2's Qwen3.5-2B row says "tool evidence: none found": the card now reports BFCL-V4 43.6, in thinking mode only [V S29].
- Doc 14's Gemma 4 26B-A4B "Q4 file" of 16.95 GB is Unsloth's non-QAT UD-Q4_K_M; the QAT builds are 14.25–14.44 GB [V S21].
- None of these changes a decision; they belong in doc 14's next consolidation pass.

### 2026-09-27, critic pass (completeness and fact check)

**Re-checked against the sources, and found correct:**

- **Pinned files.** All 27 files in the shortlist, the baselines, the offload alternate and the new rows were re-queried through the
  Hugging Face `paths-info` API at their pinned commits. Bytes and LFS SHA-256 match, the `resolve/<commit>` URLs are well formed, and
  every repository is ungated and tagged Apache-2.0 [V].
- **CSV metadata.** For all 47 original rows, the creation date, parameter count, licence tag and gating were re-read through the
  Hugging Face API. Parameters and licences match. The `release` column mixes repository creation dates with announcement dates:
  Granite-4.0-H-Tiny (repository created 2025-09-16), H-1B and 1B (2025-10-07), Nemotron 3 Nano (2025-12-04) and Hy-MT2
  (2026-05-11) carry later announcement dates in the CSV. They are left as they are.
- **Leaderboards.**
  - BFCL V4: the live CSV was re-fetched, and every quoted value matches [S1].
  - EuroEval Czech and Polish: the site's data modules were re-fetched, and every quoted value matches [S7].
  - EQ-Bench Creative v3 and Longform: every quoted value matches [S4, S5].
- **Model cards and licences.**
  - Qwen3-4B-2507 and Qwen3-30B-A3B-2507: IFEval, Creative Writing v3, WritingBench and INCLUDE, and "supports only non-thinking
    mode" [S14, S15].
  - MiniCPM5-2B: BFCL v4 66.6 against 56.8, IFEval 86.7 against 90.2, and the `min_p` warning [S25].
  - Granite-4.0-H-1B and 1B: IFEval 78.53 and 77.38, BFCL v3 50.21 and 54.82 [S27].
  - LFM Open License: the $10,000,000 threshold [S30].
  - CUDA 13.0: Maxwell, Pascal and Volta support removed [S24].
  - Hy-MT2-7B: LICENSE at `main` is Apache-2.0, changed by the commit "Update license metadata" of 2026-05-26 [S73].
  - Gemma 4 26B-A4B config: 30 layers (25 sliding-window 1024 and 5 global), 128 experts, top-8 [S21].
- **Community runs and the server.**
  - The GTX 1070 blog: every quoted value matches [S18].
  - The llama.cpp PRs and issues cited here: 19 re-queried through the GitHub API.
  - Every llama-server flag in §6 exists in the README on master [S8].

**Errors fixed:**

1. **The GTX 1080 Gemma row joined two runs.** The 3,299 MiB of GPU and 14,747 MiB of host memory were measured at `--n-cpu-moe 29`
   (15.64 tokens/s). About 20 tokens/s was measured at `--n-cpu-moe 20`, the lowest value that fit an empty 8 GB card at 128K (19 ran
   out of memory). The 65–67 tokens/s prompt figures came only with the MTP assistant [S19]. Fixed in the TL;DR, §2.5 and §4.5.
2. **Shortlist row 3 started at `--n-cpu-moe 20`, which cannot fit** the ~5.5 GiB free on the reference card. The GTX 1080's model
   buffer went from 2,103 MiB at `--n-cpu-moe 29` to 6,504 MiB at 21 [S19]. The row now starts at `--cpu-moe` and lowers from about 28
   (§2.5, §6.1, and the shortlist JSON).
3. **The prompt-processing risk treated short prompts as throughput.** Its 50–67 tokens/s were timed on 29–52-token prompts, so the
   "25 s for 1,500 tokens" arithmetic is now conditional. The GTX 1070 measured pp512 at 367 tokens/s [S18, S19].
4. **TranslateGemma is not "broken" on llama-server's chat endpoint.** PR #19052 (merged 2026-01-24) takes the language codes through
   `chat_template_kwargs`, and #19295 was closed as completed. #20305 is a Jinja parser failure on the 27B, closed as stale, and
   `--no-jinja` was reported to work [S45]. Fixed in §1.2, §3.5, §6.4, the CSV and the JSON.
5. **Issue #19051 (grammar fail-open) was closed by the stale bot as "not planned"**, not fixed [S11].
6. **Issue #20085 was a misconfiguration** (`--embedding` and `--reranking` together), closed by its reporter [S55].
7. **The Hy-MT2 release-time licence excludes only the European Union.** It does not also exclude the UK and South Korea; that is
   HY-MT1.5's and Hunyuan's wording [S73]. Fixed in three CSV rows.
8. **LFM2.5-1.2B's DSpark drafting is merged** for LFM2 targets (PR #27383, 2026-08-20), not "unconfirmed". Fixed in the CSV.
9. **Qwen3-30B-A3B-2507's `fit_draft` goes from 3 to 2 [I].** Its writing evidence is the vendor's own run. The original April 2025
   Qwen3-30B-A3B scores 35.6 on EQ-Bench Longform, against 50.7 for Gemma 4 26B-A4B [S5]. §3.4 now lists that row.
10. **The doc 14 finding on LFM2.5 languages was too broad.** "16 langs incl. PL, RU" holds for LFM2.5-2.6B.
11. **The §3.1 BFCL table.** Nanbeige's Non-Live Simple (63.83) is filled in, and "Qwen3-4B-2507 leads on Live" is limited to the
    non-reasoning rows.
12. **Qwen3.5-35B-A3B's EuroEval lead holds among instruct checkpoints only.** Its Base checkpoint scores 1.65 in Czech, against 1.68
    for the FP8 instruct [S7]. Fixed in §2.5, the CSV and the JSON.

**Added:**

- **Spark-X2.5-4B and 1.7B** (Apache-2.0, created 2026-08-24, mainline since PR #27868). They get a CSV row, §2.2, shortlist row 9,
  and pinned files. The GGUF's template defaults `enable_thinking` to true and honours false [S63].
- **Ling-3.0-tiny** (MIT, 1.3B active; open llama.cpp bugs). It gets a CSV row and §2.3, as Watch [S64].
- **Doc 14 carry-overs** Gemma 4 E2B QAT and Granite 4.2-3B, with pinned files [S65].
- **EuroEval rows** for Qwen3.5-2B, Gemma 4 E2B, EuroLLM-22B and Apertus-v1.1-4B.
- **§2.6's list of models found and left out**, with reasons [S66–S72].

**Runnability on the GTX 1070 8 GB + 32 GB box with the Vulkan build [I]:**

- **Full GPU:** rows 1, 4, 5 and 9 and the carry-overs, each estimated at under 4.1 GiB added at 8K f16.
- **CPU only:** rows 6–8.
- **Offload:** rows 2 and 3 map 14–18 GB files into 32 GB of RAM. The Qwen3.5-35B alternates, at 22 GB, are tight next to Windows and
  the editor.
- **The q8_0 KV variant** needs flash attention. Its speed on Pascal through Vulkan, which has no cooperative-matrix path, is
  unmeasured [U].

**Hygiene:** a search of the doc, the CSV and the shortlist JSON found no private or unpublished project names, no local absolute
paths and no user names.

**Not re-checked by the critic:**

- UGI Writing values (S6).
- The decider, Intern-Decision, NuExtract3, Nanbeige4.2, Needle 3, Jamba2 and GigaChat vendor numbers.
- The embedder and reranker cards.
- Spark-X2.5's "more than 200 languages".
- Whether build b11146 contains PR #27868.

### 2026-09-27, Bonsai 2 27B addendum (owner question)

Added §2.7, a TL;DR bullet, four CSV rows, open question 9, the §6.1 optional probe, four Appendix A rows and S74–S85. Nothing was
downloaded or run, and the GPU was not used.

**Re-read directly for the addendum [V]:**

- **Files.** Hugging Face `paths-info` at the pinned commits for the Bonsai 2 PTQ1_0 and PQ2_0 files, the `-gguf-dev` Q2_0 file,
  Unsloth's Qwen3.8-27B UD-IQ1_S, UD-IQ2_XXS, UD-Q2_K_XL, UD-IQ3_XXS and UD-Q4_K_XL, and first-generation Bonsai-27B Q1_0. Bytes and
  LFS SHA-256 match the research sweeps. Also the repository metadata: licence, base model, creation date, GGUF parameter count and
  context.
- **Fork releases.** The GitHub API for release `prism-b10743-adfffbe`: Windows asset names, sizes and SHA-256 digests. Tags
  `prism-b10658-4725def` (2026-08-28) and `prism-b10709-9a9394a` (2026-09-18) exist. The compare API shows fork PRs #206, #238, #245,
  #248 and #271 are ancestors of b10743, and that #250 is unmerged.
- **Issue and PR states.** Fork #87, #201, #247, #248, #250 and #283; mainline #21539, #25430, #27779, #29058, #29077, #29096, #29100
  and #29101.
- **Vendor and community texts.** KNOWN_ISSUES.md and the model card at `b072e1d`; the chat template in the MLX repository; the
  docs-site paragraph on thinking; the demo's Windows launcher; the full text of fork issue #247 and the figures in #283; HF
  discussion #54; bartowski's `perplexity.md`.
- **Local hardware.** The reference box's CPU and memory modules, read through WMI.

**Corrections to the research brief and to the research sweeps:**

1. "prism-b10658+" is the Bonsai 1 README's minimum and also the docs site's stated minimum for Bonsai 2 (the second half added by
   the fact-check below). Two sweeps said the tag does not exist; it does, dated 2026-08-28, before Bonsai 2.
2. "`thinking_budget_tokens` 0 or `BONSAI_THINKING=0`" appears on the docs site, but the vendor's KNOWN_ISSUES and demo scripts
   contradict it.
3. "CUDA and Metal only": the fork also ships Vulkan and HIP builds (the SYCL build first listed here does not exist; corrected by
   the fact-check below).
4. "A ternary g128 packing of Qwen3.8-27B": PrismML says "derived from", and independent forensics show retraining.
5. §2.6 said the PTQ1_0 file "would fit 8 GB". That holds only for an empty card, not for the ~5.5 GB free on the reference card.
6. Fork PR #238's title names Intel Xe2 decode, but KNOWN_ISSUES credits it with the Vulkan PQ2_0 CPU-fallback fix as well; the doc
   follows KNOWN_ISSUES.
7. The sweeps quoted Bonsai perplexity as both 8.04 and 8.35. Both come from #54: the first from the 50-chunk KLD run against BF16
   (6.13), the second from all 145 chunks against Q4_K_XL (6.34).

**Not verified:**

- Any Bonsai run on this box.
- The licence key inside the GGUF.
- Whether the hosted int4 endpoint serves the ternary weights.
- Speed of the fork's CUDA build on Pascal.
- The comparator's speed on this box.
- Whether the fork has `--fit`.
- The starting `-ot` splits, which are estimates to tune.
- The whitepaper's medium-effort and long-horizon figures.
- The vendor's first-generation Bonsai-27B peak-memory and quality figures.
- The InfoWorld hands-on report.
- The RTX 3060 figure (HF #41).

These last items are taken from the research sweeps' records of the same day. The fact-check below has since verified `--fit`, the
whitepaper figures, the first-generation figures, the InfoWorld report and the RTX 3060 figure.

**Hygiene:** the addendum names no private project, local path or user name. The reference box's CPU model appears only in S85's URL.

### 2026-09-27, fact-check of the Bonsai 2 27B addendum

An adversarial re-check of every number and support claim in §2.7, its TL;DR bullet, the four CSV rows, the §6.1 probe, the Bonsai
rows of Appendix A and the shortlist JSON's `bonsai` block. Only text files and the whitepaper PDF were fetched; no model file or
binary was downloaded, and the GPU was not used.

**Re-checked and found correct [V]:**

- **Pins.** `paths-info` at `b072e1d` (PTQ1_0 5,946,648,928 B and PQ2_0 7,206,168,928 B, both last changed in `6ed5e12`), Unsloth's
  UD-IQ2_XXS at `4ca7207` (7,266,070,528 B, file commit `313447f`), Bonsai-27B Q1_0 at `f10afb3` and the `-gguf-dev` Q2_0
  (7,626,008,928 B): every size and SHA-256 matches Appendix A and the JSON. Repository metadata: created 2026-09-16, Apache-2.0,
  ungated, 26.90B GGUF parameters, 262,144-token context, five GGUFs.
- **The fork release** `prism-b10743-adfffbe` (published 2026-09-25, commit `adfffbe41b`, the merge of #248): the Vulkan, CUDA 12.4,
  cudart 12.4 and CPU zip digests and sizes match GitHub's listing. At the tag, `ggml.h` has PQ2_0 = 142 and PTQ1_0 = 143 (mainline
  ends at Q2_0 = 42); the CUDA CMake adds `61-virtual` only below CUDA 13; `mmq.cu` gates PTQ1_0's MMQ path on Turing, and
  `mmq-config-pascal.cuh` has PQ2_0 tiles. PRs #206, #238, #245, #248 and #271 merged between 2026-09-21 and 2026-09-25, before the
  tag; #250 and #218 are open. GitHub's branch comparison for `prism` reads 127 commits ahead of mainline master and 605 behind.
- **The chat template** (GGUF metadata through the HF API): `xhigh` by default, only `xhigh`, `medium` and `low` accepted, an empty
  think block when `enable_thinking` is false, one leading system message, earlier reasoning re-rendered unless `preserve_thinking`
  is false.
- **Vendor texts.** README, KNOWN_ISSUES (last checked 2026-09-23), NOTICE and LICENSE at `b072e1d`; the docs-site thinking paragraph;
  the demo README, BACKEND-SUPPORT.md and Windows launcher at `9ef3205`. The whitepaper: 83.9 against 85.4 on 20 benchmarks at
  `xhigh`, 79.3 against 82.6 at `medium`, Terminal-Bench 2.1 52.8 against 69.7, SWE-bench Verified 60.8 against 80.6, EvalScope with
  vLLM on H100.
- **Issues and PRs.** Fork #247 (every quoted figure), #283 (32/50 against 16/50, p = 3.1e-05; the RTX 3080 memory and speed
  figures), #248 (2.1 tokens/s), #201 and #87. Mainline #29058 open; #29077 closed on 2026-09-22 after "Please leave this for PrismML
  to submit themselves"; #27779, #29094, #29095, #29096 (2026-09-26) and #29243 (2026-09-27) merged; #29100 and #29101 open drafts;
  Q1_0 merged on 2026-04-06 (CPU), 04-10 (Vulkan) and 04-15 (CUDA); Q2_0 on 2026-07-07 (CPU) to 07-30 (CUDA), at group 64.
- **Community and third-party.** HF discussions #54 (every KLD and perplexity figure), #44 (92% of trits; perplexity 18.6 to 23,606
  after swapping the rest), #47 ("2-3x the tokens of a Q4 model"), #41 (32 tokens/s on an 8 GB RTX 3060 after `--no-mmproj`) and
  #59 (open; rewrites all five GGUFs' metadata). bartowski's IQ2_XXS (mean KLD 0.283, 78.0%, b10896, 100 chunks). Qwen3.8-27B's
  config (64 layers, 48 linear and 16 full attention, 4 KV heads × 256, vocabulary 248,320; created 2026-08-05). The first-generation
  card (89.5% on 15 thinking-mode benchmarks; peak 5.2 GB at 4K and 5.6 GB at 10K, decimal GB). The GTX 1080 Ti run (278 and 20.5).
  InfoWorld (1-bit Bonsai 27B in LM Studio; a false answer with thinking off). OpenRouter (one int4 provider, structured outputs).
- **Arithmetic.** 5,946,648,928 B = 5,671 MiB; KV 64 KiB per token; recurrent state about 150 MiB; 5.95 GB × 14.7 ≈ 87 GB/s;
  5.95 GB × 2.1 ≈ 12.5 GB/s; 1,500 / 16 ≈ 94 s; 7.21 GB at 38.4 GB/s caps at 5.3 tokens/s; 200 tokens at 16 tokens/s plus about 3 s
  ≈ 15.5 s. WMI reports the four modules at a configured 2,400 MT/s in two channels.

**Errors fixed:**

1. **No SYCL build.** No fork release from b10658 to b10743 has a SYCL asset, the release workflow has no SYCL job, and KNOWN_ISSUES
   says SYCL cannot run the two types (#235 in review). Fixed in §2.7, the correction list above and the JSON.
2. **Wrong reason for `-ngl 99 -ot`.** llama.cpp offloads the output layer whenever `-ngl` is at least 1 (first the output layer, then
   the last blocks; `src/llama-model.cpp` in the fork and in b11146). The recommendation stands, with the right reason (named blocks;
   every layer's KV cache and recurrent state on the GPU). Fixed in §2.7 and the JSON.
3. **"prism-b10658+" is also the docs site's minimum for Bonsai 2,** not only Bonsai 1's. The row now says the vendor's sources
   disagree and pins b10743; whether b10658 runs Bonsai 2 is untested.
4. **The "might stay in fork only" quote** is PrismML's comment on mainline PR #29077 (S80), not S76.
5. **#283 is a thinking-mode result too,** and the IQ2_XXS arm hit its 8,192-token cap on 34 of 50 problems. The vendor's own
   IQ2_XXS comparator differs between the card (72.59; LiveCodeBench 56.40, AIME26 57.50) and the whitepaper (75.2; 70.05 and 78.6).
   Both added to §2.7; the CSV comparator row notes the cap hits.
6. **The vendor scores come from vLLM,** and no unpacked Bonsai 2 checkpoint is published (the first generation had `-unpacked`
   repositories). Added to §2.7, the TL;DR and the CSV.
7. **The fit used a q8_0 figure for an f16 run.** About 6.1 GiB at 8K with q8_0 KV and about 6.35 GiB with f16, so 0.8–1.0 GiB of
   weights must move, not 0.8–1.1; the ~265 MiB token embedding stays on the CPU in any case. The JSON's placement estimates now
   follow the same numbers (about 80 MiB per block).
8. **The wall time did not add up.** 180 calls at 15–20 s is 45–60 min and 76 calls at 30–80 s is 38–101 min: now roughly 1.5–2.5
   hours per arm in §2.7, §6.1 and the JSON.
9. **#87 does not report "HTTP 200".** It reports a grammar that fails to compile being logged and skipped, with a later parse error
   on a tool call. The JSON's stop rule and §2.7 are reworded.
10. **D022 has no badge rule for a bring-your-own server.** The "unqualified" badge is now an analogy with D022's rule for unlisted
    Hugging Face files, which is itself a proposal under OWQ-19.
11. **Correction 6 above is now verified:** #238 carries #188's commits (Vulkan PQ2_0 support and the PTQ1_0 integer-dot decode
    kernel), so KNOWN_ISSUES credits it correctly.
12. **Precision.** The 38.4 GB/s peak is at the configured 2,400 MT/s (Intel rates the CPU for DDR4-2133, 34.1 GB/s). The 1080 Ti
    precedent was a Q2_0 file without the rotation, wholly on an 11 GB card, so it is an upper bound. #248's 2.1 tokens/s ran at 8
    threads with AVX disabled at compile time. The precedent durations now name their dates. The fork has had thirteen releases from
    b10658 to b10743, not only the three since 2026-09-18. The fork's `--fit` and its llama-bench `-ot` are documented at the tag.
13. **A middle option was missing.** Doc 13 §3 lets the managed sidecar run a CUDA build the user downloads from upstream; the same
    pattern for a user-downloaded fork binary is now named in §2.7 and open question 9. "Every weight is ternary" now excludes the
    26.2M higher-precision parameters the card lists.

**Still not verified:**

- Any Bonsai run on this box; the fork's CUDA build on Pascal; the comparator's speed here; the starting `-ot` splits.
- The licence key and tensor types inside the GGUF beyond #29058's report (a ranged download).
- Whether the hosted int4 endpoint serves the ternary weights.
- Whether `prism-b10658` runs Bonsai 2 at all.
- Whether the Bonsai template is byte-identical to Qwen3.8-27B's own (only the Bonsai template was read).
- The fork's merge-base date (2026-08-25); the GitHub API quota was exhausted during this check.

**Hygiene:** the doc, the CSV and the shortlist JSON were searched again for private project names, local absolute paths and user
names; none were found.

### Owner answers folded (consistency review, 2026-09-27)

- OWQ-19 was answered (a) on 2026-09-27 (D037), and the owner's runtime decision is D022's amendment note. §2.7's badge paragraph,
  §5's licence table (its lead-in and the OpenMDW row) and open questions 6 and 9 now state them by pointer. The recommendations and
  measurements are unchanged.
- The "shortlist JSON" that §2.7, §6.1 and the notes above cite (its `bonsai` block holds the probe's flags, pins and stop rules)
  is committed as [`data/slm-test-shortlist.json`](data/slm-test-shortlist.json) (2026-09-27, as used for the doc 49 run; searched
  for local paths and private names before committing). Appendix A and §6.1 carry the same pins.
