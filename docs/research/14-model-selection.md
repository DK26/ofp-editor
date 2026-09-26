# Model Selection for the Editor's AI Harness

Research date: 2026-09-26. Scope: which language models ofp-editor should target for its built-in AI "harness agent",
and how to package them. This file is meant to stand alone.

### Epistemic tags used throughout

| Tag | Meaning |
| --- | --- |
| **[V]** | Verified: we checked a primary source (a live vendor page, a model card, the official leaderboard data, or source code at a pinned commit). The citation is given. |
| **[V-vendor]** | The vendor published this number about its own model. It is quoted correctly, but no one has checked it independently. |
| **[I]** | Inferred by us from verified facts. It could be wrong. |
| **[U]** | Unknown or unverified. We looked and could not confirm it. |

Terms used in this file:

- **Harness**: our agent loop. It sends the mission maker's request to a model, receives *typed tool calls* such as `place_group{...}`, and validates and applies them as an undoable change-set on the mission document. See docs 10–12.
- **SLM**: a small language model, here meaning about 0.5–4B parameters.
- **MoE**: mixture-of-experts. Only some of the weights ("active params") are used per token. RAM must still hold all of the weights.
- **GGUF / Q4_K_M**: the llama.cpp file format and its common ~4.5–5-bit quantization.
- **BFCL**: the Berkeley Function-Calling Leaderboard. **τ²-bench**: a benchmark for tool-using agents that also talk to a simulated user.
- **EQ-Bench Creative Writing v3**: a creative-writing leaderboard scored by an LLM judge.
- **BYOK**: bring your own API key.
- **CWA**: Arma: Cold War Assault (the renamed Operation Flashpoint), game version 1.99.
- **CWR**: the Remastered engine source.

## TL;DR

- **Ship no model weights in the installer.** Offer three paths:
  - **No-AI**, as a first-class mode;
  - a **one-click download** of a pinned, checksummed, Apache-2.0 local model pack;
  - **BYOK / BYO endpoint** for cloud APIs and for local servers such as Ollama, LM Studio or llama.cpp.

  This follows the precedent in iron-curtain D047: weights are "not bundled in the base install" [V]. [I]
- **The planner (multi-step typed actions) should default to a cloud frontier model.** Small models may be usable as single-step routers behind code, but the public data says they are weak at multi-turn tool use:
  - On the official BFCL table, multi-turn accuracy is 22% for Qwen3-4B against 68% for Claude Opus 4.5 [V].
  - We found no independent public evaluation of 2026 small models on short-menu routing, clarification, orchestration or coding (§4.1) [U]. Whether a 3–4B model can do single-step routing well enough is a hypothesis, to be measured with our own evaluation instruments (§9).
- **Default local pack (tier "local small"), candidate to be qualified by our own evals: Qwen3.5-4B at Q4 (2.7–2.9 GB, Apache-2.0, 201 languages).**
  - It has the strongest vendor tool-use numbers among the ~4B candidates (BFCL-V4 50.3, τ²-bench 79.9 [V-vendor]). It must pass our own evals (§9) before it becomes the default [I].
  - Fallback candidates: Gemma 4 E2B (3.1 GB file; τ² 24.5 [V-vendor]; 2.3B effective parameters [V]), and Granite 4.2-3B as a narrow router (2.2 GB; BFCL v4 52.4 [V-vendor]). Routing accuracy, false-accept rates and memory use for all three are unmeasured on our tasks [U]; our own evals (§9) decide.
- **Local medium tier (16–24 GB VRAM): Qwen3.8-27B (Apache-2.0, 16.5 GB Q4).** It is an all-rounder with EQ-Bench Elo 1671 [V].
  - Meta's **Muse-Glimmer-30B** (Apache-2.0) scores Elo 1798, the best local writer on EQ-Bench [V]. Its tool-use evidence is vendor-only (MCP Atlas 75.5, τ3-Banking 23.5 [V-vendor]); it has no independent tool-calling data [U]. Its repos also carry a separate Usage Policy that bans use "related to … Military, warfare … applications" [V]; check whether that covers a war-game editor before shipping it as a pack.
  - For 8–12 GB cards: Qwen3.5-9B (tools; BFCL-V4 66.1 [V-vendor]) or Gemma 4 12B (writing; Elo 1289) [V].
- **Cloud frontier: build adapters for any provider and choose the model with our own evals.** As of 2026-09-26:
  - Anthropic: `claude-opus-5-5` ($4/$20 per MTok), `claude-sonnet-5` ($2/$10), `claude-fable-5-1` ($10/$50).
  - OpenAI: `gpt-6-astra` ($10/$50), `gpt-6-sol` ($2/$10), `gpt-6-luna` ($0.10/$0.50).
  - Google: `gemini-3.8-flash` ($0.75/$3.75 until 2026-12-31) [V].
  - For CI we suggest the reference pair Sonnet 5 / Opus 5.5 [I]. They are pinned snapshots with published retirement floors in mid/late 2027 [V].
- **Creative text:** the top of EQ-Bench (judged in English by Claude Sonnet 4.6) is a cluster of GPT-6 Astra, Claude Fable 5.1, Claude Opus 5, GPT-6 Sol, Kimi K3 and GLM-5.3 [V].
  - **No benchmark measures Czech, Polish or Russian creative quality** [U]. We need native-speaker review.
  - Code, not the model, must enforce each language's legacy codepage: CP1250, CP1251 or CP1252 [V].
- **SQF/SQS: no public LLM benchmark exists** [U]. Models will drift toward Arma 3 idioms.
  - `compile`, `isNil`, `sleep`, `spawn`, `execVM`, `waitUntil`, `switch` and `params` are **not** registered commands in the CWR engine [V].
  - CWR adds Remastered-only commands such as `remoteExec` [V].
  - So SQF generation needs three things: a command whitelist extracted from the engine, the CWR `PoseidonEvaluator` checker [V], and a repair loop. The checker knows only its core operators plus about 70 mocked game commands, so it must be extended before it can gate real mission code (§2) [I]. It should run on frontier or ≥9B models only.
- **Routing: prefer the UI and deterministic matching first**, then a local SLM. TypeSafe **Jev** (hosted "System One" decision model, $0.042/M input tokens [V]) is worth an optional experiment.
  - Kev and Laya are open-weight decision models on Hugging Face [V]. They, Jev and CLM are compared in [16-decision-models.md](16-decision-models.md).
- **Map effort levels to four things:** model tier, reasoning setting, candidate count, and validation/repair passes. Examples: Quick = local/cheap with validators only; Max = top frontier model at `xhigh`/`max` with 2–3 candidates plus an automated `--test-mission` run. Details in §8.
- **Runtime constraint:** the pure-Rust `candle` model list has no Qwen3.5 module at all and no quantized Gemma 4 module [V]. llama.cpp runs both: its README quick start loads `ggml-org/Qwen3.5-0.8B-GGUF`, and the `ggml-org` HF account publishes `gemma-4-E2B-it-GGUF` [V]. Choosing candle would limit us to older architectures [I].

## 1. The four jobs and what each really needs

| Job | What the model does | What code must own | Hardest requirement | Minimum sensible tier [I] |
| --- | --- | --- | --- | --- |
| 1. Agentic editor harness | Turns "set up a BMP ambush on the road north of Morton" into a plan and a sequence of typed editor actions | Tool schemas, argument validation, engine limits (such as 63 groups per side, doc 09), the undoable change-set, user approval | Multi-turn tool calling, clarifying questions, spatial reasoning | Cloud frontier; local 27B+ experimental |
| 2. Creative text | Dialogue, `sideRadio`/`globalChat` lines, briefings, titles, stringtable entries in up to 8 languages | Length limits, stringtable keys, codepage transcoding, name consistency, anachronism lint | Tone (1985 Cold War military), non-English quality | Local medium for drafts; cloud for final text and translation |
| 3. Classification / routing | Maps a request to one editor operation, or asks "which group?" | Allowed-operation menu, argument admission, permissions | Low false-dispatch rate, a reliable "no match" answer | Deterministic first, then local small |
| 4. SQF/SQS generate and repair | Writes trigger `condition`/`onActivation` expressions, waypoint scripts and `.sqs` cutscenes; fixes them from error text | Command whitelist, syntax/type check, runtime check in the game | Very scarce training data in the *CWA dialect* | Cloud frontier, or local ≥9B plus validator |

Our rule for all four jobs [I]:

- When the UI already determines which operation or workflow runs (a menu item, a dialog, a map click), no model is asked to choose it again.
- When code alone can compute the whole useful result (a lint, a count, a placement inside computed bounds), the product ships that code path and adds no model to it.
- A model is used only for the part that genuinely needs language: interpreting free text, choosing among code-computed options, or writing prose.

## 2. Engine facts that constrain model choice

**Languages.** The Remastered engine's built-in language set has 8 languages [V] (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Locale/LanguageRegistry.cpp#L22-L31`; identical in `ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/UI/Locale/LanguageRegistry.cpp#L23-L30`):

- English, French, Italian, Spanish, German (CP1252)
- Czech, Polish (CP1250)
- Russian (CP1251)

Only **English and Czech have voice-over** (`hasVoice`; the code comment says "the Remaster ships dubbing for English … and Czech only") [V]. We did not check vanilla 1.99's language set separately [U]. Generated dialogue in the other languages is text-only unless we add TTS, which is out of scope here.

**Codepages.**

- The legacy CSV codepage table also maps Dutch, Portuguese, the Nordic languages (Danish, Swedish, Norwegian, Finnish, Icelandic), Slovak, Hungarian, Slovenian, Croatian, Romanian, Ukrainian and Bulgarian [V] (`.../Stringtable/CodepageTranscode.cpp#L93-L101`).
- The Remastered engine prefers a `stringtable.utf8.csv` when one is present [V] (`.../Locale/MissionLanguageDetector.cpp#L285-L286`, `.../Stringtable/Stringtable.cpp#L285`).
- Vanilla 1.99 therefore needs the codepage `stringtable.csv` [I].
- Consequence: model output such as curly quotes, em-dashes or ellipsis characters must be normalized and transcoded by code. Characters that fall outside the target codepage must fail validation [I].

**Script vocabulary is enumerable.**

- `engine/Poseidon/Game/Commands/GameStateExt.cpp#L366-L1461` holds **473** `GameFunction`/`GameOperator`/`GameNular` registration lines [V: grep count]. Four of them sit inside the `TABLE_COMMAND` macros (#L365-L371), which expand to two commands per use, so the command count is somewhat higher.
- Other files register commands a whitelist must handle: `World/Scene/SceneDraw.cpp` (`diag_*` debug commands), `Game/Commands/GameStateExtTest*.cpp` (`tri*` Trident test verbs), and `engine/Evaluator/EvalState.cpp` (the stand-alone evaluator's mocks) [V: grep]. Exclude the debug and test verbs from generated code [I].
- `engine/Evaluator/express.cpp` holds 73 more, the core operators such as `forEach`, `call`, `private`, `if`, `while` and `for` (#L1133-L1195) [V].
- A search of the whole engine finds **no** script-command registration for `compile`, `isNil`, `sleep`, `spawn`, `execVM`, `waitUntil` or `switch` [V: grep]. `params` appears only as a JSON key in the dev harness protocol (`Dev/Harness/HarnessProtocol.hpp`) and the Trident schema, never as a command [V].
- These are exactly the idioms that Arma 2/3-trained models reach for [I].
- CWR **adds** `remoteExec`/`remoteExecCall` (`GameStateExt.cpp#L1228-L1229`) [V]. These are Remastered extensions that vanilla CWA 1.99 will not accept [I].
- So we need a **dialect profile** (vanilla-1.99 or CWR). Doc 09 says output must stay loadable by vanilla CWA.

**A ready-made script checker exists.**

- CWR ships `PoseidonEvaluator`, an "OFP SQF/SQS script evaluator" CLI with `--eval`, `--test`, `--flavor sqf|sqs`, `--validate-book` and `--validate-ref` [V] (`apps/tools/Evaluator/Cli/main.cpp#L24-L44`).
- Limitation: in `--validate-book`/`--validate-ref` mode its validator **skips** snippets that touch game objects (`addWaypoint`, `createTrigger`, `camCreate`, `doMove`, …). It also replaces non-ASCII bytes with spaces [V] (`engine/Evaluator/Validate.cpp#L122-L217`).
- Limitation for `--eval`/script mode: the evaluator's `EvalState` registers only about 72 commands (stubs such as `hint`, `sideChat`, and mocks such as `setPos`, `createUnit`, `getVariable`) on top of the 73 core ones [V: grep of `engine/Evaluator/EvalState.cpp`]. An unregistered binary command is an "unknown operator" error (`engine/Evaluator/express.hpp#L30`, `EvaluatorHost.cpp#L57`) [V]. So valid mission code that uses other game commands (for example `setBehaviour`) will probably be rejected until we register stubs for the whole dialect whitelist [I].
- It is therefore at best a syntax/type gate. It cannot check semantics [I].
- For runtime checks, the game's `--harness` loopback JSON server registers an `exec` command, "Execute SQF code (fire-and-forget)" [V] (`engine/Poseidon/Dev/Harness/HarnessBuiltins.cpp#L98`). It can run SQF inside a running preview (doc 08).

## 3. Landscape, September 2026

### 3.1 Frontier and hosted APIs (live-checked 2026-09-26)

| Provider | Current model IDs (text) | Price in/out per MTok | Context | Notes |
| --- | --- | --- | --- | --- |
| Anthropic [V] | `claude-fable-5-1` | $10 / $50 | 1M | "Demanding reasoning and long-horizon agentic work". Thinking always on. Default effort `high`. **Forced `tool_choice` is also rejected** ([Fable 5.1 page](https://platform.claude.com/docs/en/models/fable-5-1/overview)) |
| | `claude-opus-5-5` | $4 / $20 | 1M | Anthropic's suggested starting model. Default effort **`medium`**. Thinking cannot be disabled. **Forced `tool_choice` `any`/`tool` is rejected**: use `auto` plus strict schemas |
| | `claude-sonnet-5` | $2 / $10 | 1M | Speed/intelligence balance. Default effort `high` |
| | `claude-haiku-4-5` (`-20251001`) | $1 / $5 | 200K | Retirement "not sooner than **October 15, 2026**". Do not hard-code it |
| OpenAI [V] | `gpt-6-astra` | $10 / $50 | 1.05M | Flagship. Released 2026-09-03 |
| | `gpt-6-sol` | $2 / $10 | 1.05M | Coding/agentic. Released 2026-09-22 |
| | `gpt-6-luna` | $0.10 / $0.50 | 1.05M | High-volume. Released 2026-09-22. `gpt-5.6-*` is the previous generation |
| Google [V] | `gemini-3.8-flash` | $0.75 / $3.75 until 2026-12-31, then doubled | [U] | Agents/coding |
| | `gemini-3.5-flash-lite` | $0.30 / $2.50 | [U] | Cheapest |
| | `gemini-3.1-pro-preview` | $2 / $12 (prompts ≤200K; $4 / $18 above) | [U] | Preview |
| | | | | All three have a free tier, where "content used to improve our products" |
| xAI [V] | `grok-4.7` (code/chat) | $2 / $6 (<200K) | 500K | Pricing doubles above 200K |
| DeepSeek [V] | `deepseek-flash` (= V4.1-Flash) | $0.15–0.30 / $0.60–1.20 (peak-dependent) | 1M | Tool calls supported. Weights are MIT on HF |
| | `deepseek-v4-pro` (= V4-Pro-0813) | $0.66–1.32 / $1.98–3.96 | 1M | |
| Mistral | `mistral-medium-2604` (Medium 3.5) | [U] | [U] | Open weights, "Modified MIT" (unverified) |
| | `mistral-small-2603` (Small 4) | [U] | [U] | 119B, Apache-2.0 (unverified) |
| | `ministral-3b`/`-8b`/`-14b` | [U] | [U] | Apache-2.0 [V: HF API for Ministral-3-8B] |
| Qwen / Moonshot / Zhipu | Open-weight flagships: Qwen3.8-2.4T-A95B (license `qwen3.8-max`), Kimi-K3 (~2.78T params, license `kimi-k3`), GLM-5.3 (753B, license `glm-5.3`), GLM-5.3-Flash (321B, MIT) [V: HF API] | Provider-dependent | 262K for Qwen3.8 [V] | Too large to run locally. Reach them through their hosted APIs or OpenAI-compatible resellers |

Sources for the table:

- [Claude models overview](https://platform.claude.com/docs/en/about-claude/models/overview.md) and the [Opus 5.5 migration guide](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide).
- [OpenAI models](https://developers.openai.com/api/docs/models) and the [OpenAI changelog](https://developers.openai.com/api/docs/changelog).
- [Gemini models](https://ai.google.dev/gemini-api/docs/models) and [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing).
- [xAI models](https://docs.x.ai/docs/models), [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing) and [Mistral models](https://docs.mistral.ai/getting-started/models/models_overview/).

Anthropic tokenizer note: 1M tokens ≈ 555k English words on the current tokenizer [V, overview page].

### 3.2 Open-weight models you can run locally

Column notes:

- **Params**: `safetensors.total` from the HF API.
- **Q4 file**: the Q4_K_M GGUF size from the HF file tree (official or unsloth repos) [V]. RAM use is higher: file + KV cache + runtime.
- **Tool evidence** and **EQ Elo** are defined in §4.

| Model (HF id) | Params | Q4 file | License | Ctx | Our 8 langs? | Tool evidence | EQ Elo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen/Qwen3.5-0.8B | 0.87B | 0.53 GB | Apache-2.0 | 262K | 201 langs claimed | none found | – |
| Qwen/Qwen3.5-2B | 2.27B | 1.28 GB | Apache-2.0 | 262K | 201 | none found | – |
| **Qwen/Qwen3.5-4B** | 4.66B | 2.74 GB (UD-Q4_K_XL 2.91) | Apache-2.0 | 262K | 201 | BFCL-V4 50.3, τ² 79.9 [V-vendor] | – |
| Qwen/Qwen3.5-9B | 9.65B | 5.68 GB | Apache-2.0 | 262K | 201 | BFCL-V4 66.1, τ² 79.1 [V-vendor] | – |
| Qwen/Qwen3.6-35B-A3B | 35.95B (3B active) | 22.1 GB | Apache-2.0 | 262K | – | not on card | – |
| **Qwen/Qwen3.8-27B** | 27.8B | 16.5 GB | Apache-2.0 | 262K | [U] | not on card | **1671.3** |
| google/gemma-4-E2B-it | 5.12B (2.3B eff.) | 3.11 GB | Apache-2.0 | 128K | 35+ (140+ pretrain) | τ² 24.5 [V-vendor] | – |
| google/gemma-4-E4B-it | 8.0B (4.5B eff.) | 4.98 GB | Apache-2.0 | 128K | 35+ | τ² 42.2 [V-vendor] | – |
| google/gemma-4-12B-it | 11.96B | 6.98 GB (QAT q4_0) | Apache-2.0 | 256K | 35+ | τ² 69.0 [V-vendor] | 1288.9 |
| google/gemma-4-26B-A4B-it | 25.8B (3.8B active) | 16.95 GB | Apache-2.0 | 256K | 35+ | τ² 68.2 [V-vendor] | 1304.6 |
| google/gemma-4-31B-it | 31.3B | [U] | Apache-2.0 | 256K | 35+ | τ² 76.9 [V-vendor] | 1368.2 |
| ibm-granite/granite-4.2-3b / -8b / -30b | 3.66 / 8.79 / 29.3B | 2.24 / 5.35 / 17.7 GB | Apache-2.0 | 128K | 12 langs incl. **CZ**, no PL/RU | BFCL v4 52.4 / 52.4 / 61.4 [V-vendor] | – |
| mistralai/Ministral-3-3B / 8B / 14B-Instruct-2512 | 3.85 / 8.92 / 13.95B | 2.15 / 5.20 / 8.24 GB | Apache-2.0 | 256K | "dozens"; CZ/PL/RU not listed [U] | not checked [U] | – |
| LiquidAI/LFM2.5-1.2B / 2.6B / 8B-A1B | 1.17 / 2.70 / 8.47B | 0.73 / 1.67 GB / – | **LFM Open License v1.0** | 128K | 16 langs incl. PL, RU; no CZ | 2.6B: BFCLv4 56.9 [V-vendor] | – |
| HuggingFaceTB/SmolLM3-3B | 3.08B | 1.92 GB | Apache-2.0 | 64K (128K YaRN) | 6 native (EN/FR/ES/DE/IT/PT) | "BFCL 92.3" (older BFCL version, not comparable) [V-vendor] | – |
| nvidia/NVIDIA-Nemotron-3-Nano-4B | 3.97B | 2.84 GB | **NVIDIA Nemotron Open Model License** | 262K | "English" primarily | BFCL v3 61.1; τ² airline 28.0 with reasoning off, 33.3 on [V-vendor] | – |
| openai/gpt-oss-20b | 20.9B (3.6B active) | 11.6 GB | Apache-2.0 | – | – | "function calling with defined schemas" | **665.6** |
| zai-org/GLM-4.7-Flash | 31.2B (30B-A3B) | 18.3 GB | MIT | [U] | EN/ZH tags | τ² 79.5 [V-vendor] | 1124.7 |
| **meta-models/Muse-Glimmer-30B** (Meta Superintelligence Lab) | 29.8B dense | 16.8 GB (official `KQuant-17GB-Q4_K_M`; unsloth has no Q4_K_M, UD-Q4_K_XL 15.9 GB) | Apache-2.0, plus a separate Usage Policy | 131K+ | "more than 100 languages" | claims "Reliable Tool Use"; MCP Atlas 75.5, τ3-Banking 23.5, SWE-Bench Verified 76.0 [V-vendor]; no BFCL | **1798.3** |
| nvidia/Nemotron-3.5-Lightning-30B-A3B | 31.6B | 25.3 GB | OpenMDW-1.1 | – | – | – | 1280.3 |
| microsoft/phi-4, Phi-4-mini | 14.7B / 3.8B | – | MIT | – | – | BFCL (official): phi-4 28.79% | – |
| meta-llama/Llama-4-Scout-17B-16E | 109B MoE | – | Llama 4 Community (gated) | – | – | BFCL (official): 28.13% | 783.1 |
| google/functiongemma-270m-it | 0.27B | – | Gemma terms (gated) | – | – | Card: "not intended for use as a direct dialogue model"; "intended to be fine-tuned for your specific function-calling task" [V] | – |

Notes on the table:

- **Phi**: there is no Phi-5 on HF. The newest Phi is `Phi-4-reasoning-vision-15B` (2026-01) [V: HF API].
- **SmolLM**: `SmolLM3-3B` (2025-07) is still the newest; there is no SmolLM4 [V].
- **Llama**: Meta's newest `meta-llama` LLMs are still Llama 4 (2025-04) [V]. Its model card names "Meta Superintelligence Lab" as the publisher of Muse-Glimmer-30B (2026-08), which sits under a separate `meta-models` org [V]. We did not independently confirm who owns that org [U].
- **GLM "Air"**: the only one found is `GLM-4.5-Air` (110B, MIT, 2025-07) [V]. It is too large for our tiers.

Sources for the table:

- Model cards: [Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B), [Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B), [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B), [Gemma 4 E4B](https://huggingface.co/google/gemma-4-E4B-it), [Gemma 4 26B-A4B](https://huggingface.co/google/gemma-4-26B-A4B-it), [Granite 4.2-8B](https://huggingface.co/ibm-granite/granite-4.2-8b), [Ministral 3 8B](https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512), [LFM2.5-2.6B](https://huggingface.co/LiquidAI/LFM2.5-2.6B), [SmolLM3](https://huggingface.co/HuggingFaceTB/SmolLM3-3B), [Nemotron 3 Nano 4B](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16), [gpt-oss-20b](https://huggingface.co/openai/gpt-oss-20b), [GLM-4.7-Flash](https://huggingface.co/zai-org/GLM-4.7-Flash), [Muse-Glimmer-30B](https://huggingface.co/meta-models/Muse-Glimmer-30B), [Gemma 4 E2B](https://huggingface.co/google/gemma-4-E2B-it), [FunctionGemma](https://huggingface.co/google/functiongemma-270m-it).
- No independent routing, clarification or tool-calling measurement of these small models on editor-like tasks was found [U]. They are candidates for our own evals (§9), not qualified defaults.

Architecture caveats that matter for the runtime:

- Qwen3.5 is a hybrid of Gated DeltaNet and gated attention, with image input. Thinking is **on by default**; `enable_thinking: False` turns it off [V, model card].
- Gemma 4 E-models use Per-Layer Embeddings; "the 'E' in E2B and E4B stands for 'effective' parameters" (E2B: 2.3B effective, 5.1B with embeddings) [V: [Gemma 4 E2B card](https://huggingface.co/google/gemma-4-E2B-it)]. So "E2B" is not a RAM figure [I].
- The `candle-transformers` model directory lists `quantized_qwen3`, `quantized_gemma3` and `quantized_lfm2`. Its `models/mod.rs` has **no** Qwen3.5 module at all (neither `qwen3_5` nor `quantized_qwen3_5`), and its `gemma4/` module (audio, config, text, vision, …) has no quantized variant [V: [candle tree](https://github.com/huggingface/candle/tree/main/candle-transformers/src/models), `mod.rs` on `main`, re-checked 2026-09-26].
- The llama.cpp server supports GBNF `grammar`, `json_schema`-constrained sampling, and OpenAI-style tools with `--jinja` [V: [server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)].
- Inference: if doc 06/12 picks pure-Rust candle over llama.cpp, the local model list shrinks to Qwen3/Gemma 3/LFM2-era models [I]. This is a joint decision.

### 3.3 "Decision models" (Jev, Kev, Laya, CLM)

Full analysis, including the proposed `Selector` seam and the evidence bar a decision model must clear, is in [16-decision-models.md](16-decision-models.md). Summary:

- **Jev 1.13** (TypeSafe, "System One") [V]:
  - Hosted only. Text in; typed **Choice / Score / Noul (bool)** answers with calibrated probabilities out.
  - It "do[es] not write replies, produce code, or generate explanations".
  - 64k context. $0.042 per M input tokens; output is free.
  - Sources: [models](https://docs.typesafe.ai/models), [System One](https://docs.typesafe.ai/concepts/system-one).
  - pi-ai already has a `classify()` provider for it (doc 11) [V per doc 11].
- **CLM-v0.1-8B** (Contrastive-LM) ranks candidates that the caller supplies. Its Apache-2.0 projection heads sit on a frozen Qwen3-8B encoder, so it is 8B-class and needs a GPU-served encoder [V: [card](https://huggingface.co/Contrastive-LM/CLM-v0.1-8B), [repo](https://github.com/Contrastive-LM/CLM)].
- **Kev** (`jaredpalmer/kev-*`): open Apache-2.0 adapters and heads on Qwen bases with Jev's state-plus-typed-questions interface; the Kev-0.8B card lists 0.6B, 0.8B, 4B and 9B sizes, while the Hugging Face family listing also has 0.5B, 8B and 27B repos (7 in total; see `16-decision-models.md`) [V: [family listing](https://huggingface.co/api/models?search=jaredpalmer/kev&full=true), 2026-09-27]; the card says it "trails Jev everywhere it can be compared" on the author's development splits [V-author: [Kev-0.8B card](https://huggingface.co/jaredpalmer/kev-0.8b)].
- **Laya** (`convaiinnovations/laya`): an Apache-2.0, 421M-parameter ModernBERT-large encoder; small enough for CPU, but its base checkpoint is "near chance" zero-shot and needs fine-tuning [V-author, per doc 16 §2.3].
- Our position [I]: a decision model can at most be a small, bounded, advisory chooser behind code-computed menus. It cannot replace the generative model that plans and writes, and no one has measured any of these models on editor tasks [U]. Doc 16 recommends no decision model in front of the generative model for v1.

## 4. Evidence by task

### 4.1 Agentic tool calling (job 1)

**Independent data is stale for 2026 frontier models.**

- The official BFCL table was "Last Updated: 2026-04-12". It has 109 rows [V: [leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html) `data_overall.csv`].
- Its newest entries are late-2025 models. Its top score is **Claude-Opus-4-5-20251101 (FC) 77.47%**.
- None of Claude Opus 5.5, GPT-6 or Gemini 3.8 appears in it.
- Aggregator sites that claim September-2026 BFCL leaders could not be traced to official data [U]. We do not use them.

What the official table still shows well is the **size gap on multi-turn tool use**, the column that matters for an agent loop [V]:

| Model (official BFCL V4) | Overall | Multi-turn | Irrelevance detection |
| --- | --- | --- | --- |
| Claude-Opus-4-5 (FC) | 77.47% | 68.38% | 84.72% |
| GLM-4.6 (FC thinking), open MIT | 72.38% | 68.00% | 84.96% |
| Claude-Haiku-4-5 (FC) | 68.70% | 53.62% | 85.11% |
| GPT-5-mini (FC) | 55.46% | 27.50% | 91.01% |
| Qwen3-8B (FC) | 42.57% | 41.75% | 79.07% |
| Qwen3-4B-Instruct-2507 (FC) | 35.68% | 22.12% | 84.93% |
| Qwen3-1.7B (FC) | 28.41% | 11.00% | 76.54% |
| Gemma-3-12b-it (Prompt) | 30.43% | 5.75% | 70.29% |
| Llama-4-Scout (FC) | 28.13% | 9.00% | 44.92% |
| Qwen3-0.6B (FC) | 23.93% | 3.62% | 80.84% |
| Ministral-8B-2410 (FC) | 11.10% | 0.00% | 100.00% |

Takeaway [I]:

- Multi-turn accuracy collapses below about 8B parameters.
- A high "irrelevance detection" score can simply mean the model rarely calls tools (Ministral-8B: 100% irrelevance, 0% multi-turn).
- Newer small models (Qwen3.5, Gemma 4, Granite 4.2) report better numbers on their cards (§3.2), but those are vendor-reported and not on this table.

**Clarification under unclear instructions.** A public study of LLM agents given unclear tool-use instructions (for example, requests with a required argument missing) found that "LLMs tend to arbitrarily generate the missed argument, which may lead to hallucinations and risks" [V: Wang et al., "Learning to Ask: When LLM Agents Meet Unclear Instruction", [arXiv 2409.00557](https://arxiv.org/abs/2409.00557)]. We therefore do not expect a small model to ask a needed question on its own [I].

- Design consequence [I]: code detects missing or ambiguous slots (for example, "which group?" when several match) and asks the question itself, as a form field or a menu of code-computed options. The model at most picks among those options.
- Hypothesis, to be measured with our own evaluation instruments (§9, doc 25 §11): a 3–4B model can pick the right single action from a short, code-filtered menu often enough for a "suggest" UX, and can pick "no match" when nothing fits. No public evaluation of 2026 small models on this kind of menu task was found [U].
- The ~1B tier is weak on public data: Qwen3-0.6B and Qwen3-1.7B reach 3.62% and 11.00% multi-turn on BFCL (table above) [V]. FunctionGemma-270M's card says it is "intended to be fine-tuned for your specific function-calling task" and is "not intended for use as a direct dialogue model" [V: [card](https://huggingface.co/google/functiongemma-270m-it)]. We do not plan a stock ~1B default [I].

**Conclusion for job 1 [I]:**

- Local SLMs may **propose one action** from a short, code-filtered menu. Code validates the action and the user confirms it. Whether a given local model is good enough for this is decided by our own evals (§9).
- The **planner** that writes multi-step action lists and asks clarifying questions should be a frontier API by default, or a local ≥27B model as an explicitly "experimental" option.
- On Anthropic models, the harness must not rely on forced tool choice (rejected on Opus 5.5 and Fable 5.1 [V]). Use `tool_choice: auto` with strict schemas and a validator/repair turn.

### 4.2 Creative text (job 2)

**EQ-Bench Creative Writing v3.**

Method [V: [about](https://eqbench.com/about.html)]:

- 32 prompts × 3 iterations.
- Elo judged by **Claude Sonnet 4.6**; rubric scored by Claude Sonnet 4.
- **English only**. Outputs are truncated to 4,000 characters.
- Listed as *uncontrolled*: "Self-bias (judge preferring its own outputs)".

Data: [leaderboard](https://eqbench.com/creative_writing.html) data file `creative_writing.js?v=1.0.91`, fetched 2026-09-26, 141 entries. Some names on the site carry a `*` whose meaning we did not verify; we omit it below.

| Band | Models (Elo) |
| --- | --- |
| Top cluster | gpt-6-astra 2173.3 · claude-fable-5-1 2162.0 · claude-opus-5 2132.6 · gpt-6-sol 2124.7 · kimi-k3 2082.3 · GLM-5.3 2075.0 · claude-opus-5-5 2050.1 · grok-4.7 2006.7 |
| Strong / cheaper | Qwen3.8-2.4T-A95B 1842.5 · gpt-5.6-luna 1828.7 · **Muse-Glimmer-30B 1798.3** · claude-sonnet-5 1794.0 · gemini-3.8-flash 1747.9 · Kimi-K2.6 1724.5 · **Qwen3.8-27B 1671.3** |
| Budget API | DeepSeek-V4-Flash 1559.1 · gemini-3.5-flash-lite 1559.1 · DeepSeek-V4-Pro 1553.2 |
| Local mid | gemma-4-31B 1368.2 · gemma-4-26B-A4B 1304.6 · gemma-4-12B 1288.9 · Nemotron-3.5-Lightning-30B 1280.3 · Mistral-Small-3.2-24B 1255.4 · GLM-4.7-Flash 1124.7 |
| Local small / weak | gemma-3-4b 1068.0 · gpt-oss-120b 961.0 · Llama-4-Scout 783.1 · gpt-oss-20b 665.6 · llama-3.2-3b 595.3 |

Not on the board [V: absent]: any Qwen3.5 small model, Ministral 3, Granite 4.x, LFM2.5 (only the older `lfm-7b`, 751.7) and SmolLM3. So **4B-class creative quality is unmeasured**. The nearest proxy is gemma-3-4b at 1068 [I].

How well this transfers to our use [I]:

- We need short lines: radio chatter of 1–2 sentences, briefings of 100–400 words.
- They must fit a period voice: NATO/Warsaw Pact 1985, no anachronisms such as "GPS", "drone" or "cell phone".
- They must stay consistent with unit names and grid references taken from the mission.
- A long-story benchmark judged by a Claude model is only a coarse signal, and it may favor Claude outputs.
- Our pipeline should put facts in code and wording in the model:
  - code supplies the facts (names, callsigns, grid references from the mission document);
  - the model writes;
  - deterministic lints check length, codepage, placeholders, the anachronism list and name consistency.

**Multilingual.**

- Vendor multilingual numbers [V-vendor] (MMMLU and WMT24++ measure knowledge and translation, not creative quality):

  | Model | MMMLU | WMT24++ |
  | --- | --- | --- |
  | Qwen3.5-4B | 76.1 | 66.6 |
  | Qwen3.5-9B | 81.2 | 72.6 |
  | Gemma 4 E2B | 67.4 | – |
  | Gemma 4 E4B | 76.6 | – |
  | Gemma 4 12B | 83.4 | – |
  | Gemma 4 31B | 88.4 | – |

- Coverage gaps [V]:
  - Granite 4.2 lists Czech but not Polish or Russian.
  - LFM2.5 lists Polish and Russian but not Czech.
  - SmolLM3 has none of CZ/PL/RU natively.
  - Nemotron Nano 4B is English-primary.
- We found **no creative-writing evaluation in Czech, Polish or Russian** [U].
- Recommendation [I]:
  - Write in English first, then translate with a cloud or local-medium model.
  - Require native-speaker review before any shipped or official content.
  - Keep a per-language glossary for ranks, callsigns and radio procedure.

### 4.3 Cheap classification and routing (job 3)

- **Deterministic first.** The editor already has a closed command set (F1–F6 modes, dialogs). Fuzzy matching over command names and aliases handles most "do X" requests with no model [I].
- **Local router candidates** (public facts only; accuracy, false accepts, memory and latency on our tasks are unmeasured [U]):

  | Model | Q4 file [V] | Public tool evidence [V-vendor] | Languages [V] | Why it is a candidate [I] |
  | --- | --- | --- | --- | --- |
  | Qwen3.5-4B | 2.74 GB (UD-Q4_K_XL 2.91) | BFCL-V4 50.3, τ² 79.9 | 201 claimed | Strongest vendor tool numbers at ~4B |
  | Granite 4.2-3B | 2.24 GB | BFCL v4 52.4 | 12, incl. CZ | Smaller file; narrow menus |
  | Gemma 4 E2B | 3.11 GB | τ² 24.5 | 35+ | 2.3B effective parameters; low-memory option |

  - The file size is not the RAM requirement: KV cache, runtime buffers, the editor itself and the OS come on top [I]. Working set and per-request latency must be measured on reference machines (§9).
  - Design target [I]: local routing is a "suggest" UX (the user confirms), so multi-second latency is tolerable; per-keystroke use is not a goal.
- **Cloud cheap routers** [V prices]: `gpt-6-luna` ($0.10/$0.50), `gemini-3.5-flash-lite` ($0.30/$2.50), `deepseek-flash`, `claude-haiku-4-5` ($1/$5; retirement not before 2026-10-15).
- **Jev** is an optional experiment for "which of these N editor operations / is this ambiguous?" [I]. It must clear doc 16 §5's evidence bar: beat both the rule-based and the generative selector on the same cases, and be pinned to an exact version such as `jev-1.13.0`, never the `jev-latest` alias [I].

### 4.4 SQF/SQS generation and repair (job 4)

- **No public benchmark or study of LLMs on SQF or SQS was found** (web searches 2026-09-26) [U].
- General finding [V: [MultiPL-T, arXiv 2308.09895](https://arxiv.org/abs/2308.09895)]: code LLMs "struggle with low-resource languages that have limited training data available".
- **SQF** is a GitHub Linguist language (`.sqf`, `.hqf`); **SQS** is not [V: [languages.yml](https://raw.githubusercontent.com/github-linguist/linguist/main/lib/linguist/languages.yml)].
  - Public corpora therefore label SQF, and it is mostly Arma 2/3 code [I].
  - SQS, the main CWA-era scripting format, is barely identifiable [I].
- **Expected failure mode [I]:** confident Arma 3 code such as `params`, `spawn`, `sleep`, `waitUntil`, `isNil`, `switch` and `BIS_fnc_*`. None of these exist as CWA commands (§2).
- Community anecdote [U, low confidence]: a search snippet of the Arma 3 mod "Combat Copilot" (Gemini-backed) says "sometimes the neural network creates errors in the SQF code". The source page could not be fetched (HTTP 429/timeout).

**Recommended approach [I]:**

1. **Prefer typed actions over script.** Waypoint types, trigger activation, `END1..6` endings (doc 18) and `setBehaviour` presets should be tool arguments, not free code.
2. **Retrieval-grounded prompts.** Extract `{name, left type, right type, return type}` for every registration in `GameStateExt.cpp` and `express.cpp`. Filter by dialect (vanilla-1.99 or CWR). Inject only the relevant subset, plus 3–5 verified CWA-style examples. The CWR `tests/fixtures/evaluator` scripts are GPL, the same as our project (doc 02).
3. **Gates, in order:**
   - token-level whitelist lint (in Rust, no model);
   - `PoseidonEvaluator --eval/--flavor` for syntax and types, after we add stubs for every whitelisted game command (§2);
   - optional runtime `exec` through `--harness` in a preview (doc 08).
4. **Repair loop:** feed the exact error text back. Cap the loop at N attempts, where N depends on effort (§8).
5. **Model tier:** cloud frontier by default. Local ≥9B only for short expressions such as trigger conditions, and only behind the gates. No SLM authoring of scripts: SQF/SQS is a low-resource language (above) and small models already collapse on multi-turn tool use (§4.1), so we treat small-model script authoring as unqualified until our own SQF/SQS instrument (§9) says otherwise [I].

## 5. Hardware reality and whether to ship a model

**Steam Hardware Survey, August 2026** [V: [survey](https://store.steampowered.com/hwsurvey/)]:

| RAM | Share |
| --- | --- |
| 8 GB | 7.46% |
| 16 GB | 41.20% |
| 32 GB | 37.45% |
| 64 GB | 3.97% |

| VRAM | Share |
| --- | --- |
| 4 GB | 5.69% |
| 6 GB | 5.30% |
| 8 GB | 25.74% |
| 12 GB | 12.99% |
| 16 GB | 26.92% |
| 24 GB | 5.41% |

- Windows share is 93.95%.
- Summed over all survey buckets (including >64 GB RAM 0.59%, and 10/11/20/32 GB VRAM at 1.96/0.83/1.37/1.34%; VRAM "Other" 1.71% excluded): **83.2%** have 16 GB RAM or more, **76.6%** have 8 GB VRAM or more, and **35.0%** have 16 GB VRAM or more [V: arithmetic on the survey].
- Caveat: this survey covers all Steam users, not CWA players. A 2001-era game's audience may skew toward older machines [U].
- No candidate model has a minimum-hardware spec that we have verified on our own workload [U]. Each pack's `min_ram_gb` must come from our own measurements (§9), not from the file size.
- On 8 GB machines (7.46% of the survey), integrated GPUs share system RAM, so "shared GPU memory" adds no capacity: a ~3 GB model file plus KV cache competes with the OS, the editor and the game for the same 8 GB [I]. So T1's Qwen3.5-4B candidate assumes about 16 GB RAM (§6). On 8 GB machines we offer No-AI, BYOK cloud, or smaller local packs (for example Qwen3.5-2B or Granite 4.2-3B on CPU) only as explicitly unqualified experiments [I].

**Should we ship a default model? Recommendation: do not bundle weights. Provide one-click download plus BYO.** [I]

| Option | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| Bundle weights in the installer | Works offline immediately | Adds 1.3–3 GB to a small editor; forces a model on No-AI users; every model update needs a new release | ✘ |
| **One-click download of a pinned pack** | Opt-in; checksummed; updatable independently; D047 precedent ("downloaded on demand") [V] | Needs a hosting/mirror plan (HF is fine) | ✔ default local path |
| BYO local endpoint (Ollama / LM Studio / llama.cpp, OpenAI-compatible) | Zero hosting for us; power users pick their own models | Chat-template and tool-parser quirks per server | ✔ |
| BYOK cloud (Anthropic, OpenAI, Gemini, plus OpenAI-compatible for DeepSeek, xAI, Mistral, Qwen, Kimi, GLM, OpenRouter) | Best quality; no local hardware needed | Cost; privacy (the Gemini free tier trains on content [V]); key storage | ✔ |
| OAuth sign-in (D047 tier 2) | Easiest UX | Whether providers allow third-party apps to bill a subscriber's plan via OAuth is **[U]** | Defer |

**License policy for packs we pin or link** [V license facts; policy is I]:

- **First-party packs: Apache-2.0 or MIT only.** That covers Qwen3.5 and Qwen3.8-27B, Gemma 4 (Apache-2.0 since Gemma 4 [V]), Granite 4.x, Ministral 3, SmolLM3, gpt-oss, Muse-Glimmer-30B and GLM-4.7-Flash (MIT).
  - Caveat for Muse-Glimmer-30B: its `LICENSE` is plain Apache-2.0, but the repos also ship a `USAGE_POLICY.md` that prohibits activities risking death or bodily harm, "including use of Muse Glimmer related to … Military, warfare, … applications" [V: [policy](https://huggingface.co/meta-models/Muse-Glimmer-30B-GGUF/blob/main/USAGE_POLICY.md)]. The policy does not say how it relates to the license [V]. A fictional Cold War mission editor is probably not a "military application", but that is our inference, not legal advice [I]. Resolve this before making it a first-party pack.
- **Allowed as optional community packs, with their notices shown:**
  - the NVIDIA Nemotron Open Model License, which requires the notice "Licensed by NVIDIA Corporation under the NVIDIA Nemotron Model License" [V: [license](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-nemotron-open-model-license/)];
  - the LFM Open License v1.0, whose commercial use is conditioned on annual revenue under **$10M** [V: [LICENSE](https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct/blob/main/LICENSE)].
- **Avoid:**
  - **Llama 4**: it requires "prominently display 'Built with Llama'", "Llama" at the start of derivative model names, and a separate license above 700M MAU [V: [license](https://dev.meta.ai/llama/llama4/license/)]. It also scores weakly (§4).
  - FunctionGemma: Gemma terms, gated.
- Weights are downloaded data files, not linked code. We do not expect a GPL-3.0 conflict, but that is our inference, not legal advice [I].
- Pack manifest: follow D047's `model_pack.toml`, which records license, quantization, SHA-256, `min_ram_gb`, prompt profile and eval pass-rate [V] (`iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D047-llm-config.md#L73-L99`).
- Also record the exact artifact identity: weights hash, quantization, chat template, sampler, context length, thinking on/off and runtime version [I]. The same model name with a different quant, template or sampler can behave differently, so eval results apply only to the exact artifact that was measured (doc 25 §11 uses the same fields).

## 6. Recommended tiers

| Tier | Who | What installs | Default model(s) [I, from §3–4 evidence] |
| --- | --- | --- | --- |
| **T0 No-AI** | Everyone, always available | Nothing | Templates, fuzzy command search, snippet library, deterministic lints and validators (these also run in every other tier) |
| **T1 Local small** | About 16 GB RAM, any GPU or CPU-only (8 GB machines: no default local pack, see §5) | ~1.3–3.1 GB download | Candidates, each to be qualified by our own evals (§9): **Qwen3.5-4B Q4** (Q4_K_M or UD-Q4_K_XL; qualify both). Low-memory fallback: **Gemma 4 E2B**. Narrow-router option: **Granite 4.2-3B**. Thinking off for routing |
| **T2a Local medium-lite** | 8–12 GB VRAM or 32 GB RAM | 5.7–7 GB | **Qwen3.5-9B** for tools; **Gemma 4 12B QAT** for writing and translation drafts |
| **T2b Local medium** | ≥16 GB VRAM, or 32–64 GB RAM with MoE offload | 16–22 GB | **Qwen3.8-27B** as the all-rounder. **Muse-Glimmer-30B** for writing (tool use vendor-reported only; Usage Policy caveat in §5). **Gemma 4 26B-A4B** as the faster MoE option (3.8B active) |
| **T3 Cloud frontier** | Anyone with a key | Nothing | Planner: `claude-opus-5-5` / `gpt-6-sol` / `gemini-3.8-flash`. Writer: any top-cluster model. Router: `gpt-6-luna` / `gemini-3.5-flash-lite`. Max: `claude-fable-5-1` / `gpt-6-astra`. Budget: `deepseek-flash` |

Where each task runs:

| Task | T0 | T1 | T2 | T3 |
| --- | --- | --- | --- | --- |
| NL command → one editor action | fuzzy search | ✔ default | ✔ | ✔ |
| Multi-step plan (squads, waypoints, triggers) | wizards and templates | ✘ (offer T0 wizard) | experimental, Thorough only | ✔ default |
| Clarifying questions | form fields | ✘ (code asks; model may pick from code-computed options, §4.1) | experimental | ✔ |
| EN dialogue, radio, briefing | fill-in templates | draft only, flagged "rough" | ✔ | ✔ best |
| Translation to FR/IT/ES/DE/CZ/PL/RU | – | ✘ | draft + review | ✔ + review |
| Titles and names | word lists | ✔ | ✔ | ✔ |
| SQF/SQS authoring | snippet library | ✘ | short expressions + gates | ✔ + gates |
| SQF/SQS repair from an error | show error and docs | ✘ | ✔ small fixes + gates | ✔ |

## 7. Provider-neutral integration requirements that follow from model choice

- **Effort normalization.** Each provider exposes reasoning control differently. Map our `Effort` enum per provider. This follows pi-ai's `thinkingLevelMap` pattern (doc 11). The provider knobs:
  - **Anthropic** `output_config.effort` `low|medium|high|xhigh|max` [V]. On Opus 5.5 and Fable 5.1 thinking cannot be turned off [V].
  - **Qwen3.8**: `reasoning_effort` [V: [repo](https://github.com/QwenLM/Qwen3.8)].
  - **Qwen3.5 / Nemotron Nano**: `enable_thinking` on or off [V].
  - **gpt-oss**: low, medium or high [V].
  - **GPT-6**: the models page lists reasoning levels `low|medium|high|xhigh|max` for Astra and `none|low|medium|high|xhigh|max` for Sol and Luna [V]. We did not check the request parameter name [U].
- **No forced tool choice.** Design the loop with `auto` tool choice, strict JSON schemas and a validator/repair turn, because Opus 5.5 and Fable 5.1 reject forced tool choice [V].
- **Local structured output.** Use llama.cpp `json_schema`/GBNF constrained decoding for SLM routers so that the output is always a valid ID or `no_match` [V feature; I design].
- **Capability probe at setup**, as in D047: template, JSON reliability, tool calls, effective context and latency [V] (`D047-llm-config.md#L271-L287`).
  - Store the probe result per `(endpoint, model, version)`.
  - Choose a prompt profile such as `LocalCompact` or `CloudRich` (`#L245-L256`) [V].
- **Pin model IDs.** Anthropic's dateless IDs are pinned snapshots [V]. Keep a small `models.toml` that can be updated without a release. Some retirement dates are close (Haiku 4.5) [V].

## 8. Effort levels and workflows

**Effort** is one user-facing dial. Each level resolves to four settings: *(model tier, reasoning setting, candidates, verification and repair passes)*, plus budgets and human gates. Deterministic validators run at **every** level. Formal computation (counts, geometry, IDs, engine limits, legality checks) always belongs to code, never to the model, at any effort level [I].

| Effort | Default route | Reasoning | Candidates | Verification / repair | Human gate | Budget example [I] |
| --- | --- | --- | --- | --- | --- | --- |
| **Quick** | T1 local, or T3 cheap router model | off / `low` | 1 | Lints and schema only; 0 model repairs | Apply as a preview change-set | ≤2 tool calls, ≤4K output tokens |
| **Standard** | T2, or T3 mid (`claude-sonnet-5`, `gpt-6-sol`, `gemini-3.8-flash`) | `low`–`medium` | 1 | Lints, schema and `PoseidonEvaluator`; ≤1 repair | Change-set review | ≤10 tool calls |
| **Thorough** | T3 planner (`claude-opus-5-5` or equivalent) | `high` | Plan first (shown), then execute | Everything in Standard, ≤3 repairs, plus an optional automated `--test-mission` smoke run (doc 08; CWR's Trident launches it with `--window`, so it is not verified headless) | Approve the plan, then the change-set | ≤30 tool calls, with an explicit cost estimate |
| **Max** | T3 top (`claude-fable-5-1` or `gpt-6-astra`) | `xhigh` / `max` | 2–3 alternative plans or texts, ranked first by validators, then by a model judge | Everything in Thorough, plus a native-language checklist for translations | Same, with a side-by-side diff of alternatives | Hard spend cap shown before the run |

**Workflows** are code-defined pipelines whose steps declare a **role**. A step does not name a model. Roles are router, planner, writer, translator, scripter and judge. Settings map each role to a provider per effort level, like D047's task routing [V] (`D047-llm-config.md#L152`, `#L199-L210`).

Example briefing workflow:

1. Outline, facts pulled from the mission by code.
2. EN draft (writer).
3. Lints.
4. Translate (translator).
5. Codepage and length check (code).
6. Human review.

A user can then run "Standard, but use my local model for the writer role" [I].

## 9. What we must measure ourselves before committing

The public evidence cannot settle choices for *our* tools, so we need our own checks [I]:

1. **`ofp-evals` suite on synthetic fixtures only** (project rule):
   - 60 intent→action cases, including unsupported, ambiguous and missing-argument cases;
   - 20 multi-step plans;
   - 30 dialogue prompts across 8 languages;
   - 40 SQF/SQS tasks, graded by the §4.4 gates.
2. **Scoring rules** (our own; see also doc 25 §11) [I]:
   - Report the exact artifact (weights hash, template, sampler and runtime).
   - Report false accepts separately from refusals.
   - Report cost per *accepted* completion.
   - Never merge repeated runs, cases or models into one pooled score; report each run and a repeat-reliability figure such as pass^k.
   - Keep held-out cases that were never used while tuning prompts, so scores are not inflated by repetition on known cases.
   - Measure peak working set and per-request latency on named reference machines, and derive each pack's `min_ram_gb` from them (§5).
3. **Candidates to run:**
   - T1: Qwen3.5-4B (both quants), Gemma 4 E2B, Granite 4.2-3B.
   - T2: Qwen3.5-9B, Gemma 4 12B, Qwen3.8-27B, Muse-Glimmer-30B.
   - T3: Sonnet 5, Opus 5.5, GPT-6 Sol, Gemini 3.8 Flash, DeepSeek flash.
4. **Native-speaker rubric** for CZ, PL and RU (and FR/DE/IT/ES if volunteers exist): tone, military register, naturalness.

## Open questions

- **Decision models:** Jev, Kev, Laya and CLM are identified in doc 16; whether any of them earns an advisory slot is doc 16's open question, settled only by its §5 evidence bar.
- **Target dialect:** vanilla CWA 1.99 only, CWR Remastered, or selectable? This decides the command whitelist, including `remoteExec`, and the stringtable encoding (CSV codepage or `.utf8.csv`).
- **Inference runtime:** llama.cpp (bindings or sidecar) or pure-Rust candle? This decides whether Qwen3.5 and Gemma 4 are usable locally (docs 06 and 12).
- Do Anthropic, OpenAI or Google permit third-party desktop apps to use OAuth plan billing for API calls? [U]
- Does `PoseidonEvaluator` build standalone on all our CI targets, and can we ship it (GPL) as a helper binary or port its checks to Rust?
- Do CWA players' machines match the Steam average? A small opt-in survey on the community Discord or forums would tell us.
- Can we recruit Czech, Polish and Russian native reviewers? Czech matters most, because it is the only non-English voiced language.
- Is Muse-Glimmer-30B's tool calling usable through llama.cpp templates? Its card gives only vendor agentic scores (MCP Atlas, τ3-Banking), no BFCL. Does its Usage Policy's "military, warfare" clause bind Apache-2.0 users, and does it cover a war-game editor?
- Can `PoseidonEvaluator`'s `EvalState` be given stubs for the full dialect whitelist, so `--eval` stops rejecting valid game commands?
- Should the SQF gates also accept **Arma 3-style** output and auto-translate it (for example `sleep 5` → SQS `~5`), or reject it?

## Sources

### Code (pinned)

- `BohemiaInteractive/CWR@ffc61838b7`:
  - `engine/Poseidon/UI/Locale/LanguageRegistry.cpp#L14-L31`
  - `engine/Poseidon/UI/Locale/Stringtable/CodepageTranscode.cpp#L93-L101`
  - `engine/Poseidon/UI/Locale/MissionLanguageDetector.cpp#L285-L286`
  - `engine/Poseidon/UI/Locale/Stringtable/Stringtable.cpp#L285`
  - `engine/Poseidon/Game/Commands/GameStateExt.cpp#L366-L1461` and `#L1228-L1229`
  - `engine/Evaluator/express.cpp#L1133-L1195`
  - `engine/Evaluator/Validate.cpp#L122-L217`
  - `engine/Evaluator/EvalState.cpp` (grep of `NewFunction`/`NewOperator`/`NewNularOp`), `engine/Evaluator/express.hpp#L30`, `engine/Evaluator/EvaluatorHost.cpp#L57`
  - `engine/Poseidon/World/Scene/SceneDraw.cpp#L541-L546`, `engine/Poseidon/Game/Commands/GameStateExtTestAudio.cpp#L2966-L2996`
  - `engine/Poseidon/Dev/Harness/HarnessBuiltins.cpp#L98`
  - `apps/tools/Evaluator/Cli/main.cpp#L24-L44`
- `ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/UI/Locale/LanguageRegistry.cpp#L23-L30`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D047-llm-config.md#L24-L152`, `#L245-L287`

### Web (fetched 2026-09-26)

- Anthropic: <https://platform.claude.com/docs/en/about-claude/models/overview.md>, <https://platform.claude.com/docs/en/models/opus-5-5/migration-guide> and <https://platform.claude.com/docs/en/models/fable-5-1/overview>
- OpenAI: <https://developers.openai.com/api/docs/models> and <https://developers.openai.com/api/docs/changelog>
- Google: <https://ai.google.dev/gemini-api/docs/models> and <https://ai.google.dev/gemini-api/docs/pricing>
- xAI, DeepSeek, Mistral: <https://docs.x.ai/docs/models>, <https://api-docs.deepseek.com/quick_start/pricing>, <https://docs.mistral.ai/getting-started/models/models_overview/>
- BFCL: <https://gorilla.cs.berkeley.edu/leaderboard.html> (data file `data_overall.csv`, "Last Updated 2026-04-12")
- EQ-Bench: <https://eqbench.com/creative_writing.html> (data file `creative_writing.js?v=1.0.91`) and <https://eqbench.com/about.html>
- Hugging Face API (params, licenses, GGUF sizes): `https://huggingface.co/api/models/<id>` and `.../tree/main` for each model in §3.2
- Model cards:
  - Qwen: <https://huggingface.co/Qwen/Qwen3.5-4B>, <https://huggingface.co/Qwen/Qwen3.5-9B>, <https://huggingface.co/Qwen/Qwen3.6-35B-A3B>, <https://huggingface.co/Qwen/Qwen3.8-27B>, <https://github.com/QwenLM/Qwen3.8>
  - Google: <https://huggingface.co/google/gemma-4-E2B-it>, <https://huggingface.co/google/gemma-4-E4B-it>, <https://huggingface.co/google/gemma-4-26B-A4B-it>, <https://huggingface.co/google/functiongemma-270m-it>
  - IBM and Mistral: <https://huggingface.co/ibm-granite/granite-4.2-8b>, <https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512>
  - Others: <https://huggingface.co/LiquidAI/LFM2.5-2.6B>, <https://huggingface.co/HuggingFaceTB/SmolLM3-3B>, <https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16>, <https://huggingface.co/openai/gpt-oss-20b>, <https://huggingface.co/zai-org/GLM-4.7-Flash>, <https://huggingface.co/meta-models/Muse-Glimmer-30B>
- Licenses:
  - <https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct/blob/main/LICENSE>
  - <https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-nemotron-open-model-license/>
  - <https://dev.meta.ai/llama/llama4/license/>
  - Muse-Glimmer: <https://huggingface.co/meta-models/Muse-Glimmer-30B-GGUF> (`LICENSE`, `USAGE_POLICY.md`, file tree) and <https://huggingface.co/api/models/unsloth/Muse-Glimmer-30B-GGUF/tree/main>
- TypeSafe: <https://docs.typesafe.ai/models> and <https://docs.typesafe.ai/concepts/system-one>
- Other decision models (details in doc 16): <https://huggingface.co/jaredpalmer/kev-0.8b>, <https://huggingface.co/Contrastive-LM/CLM-v0.1-8B>, <https://github.com/Contrastive-LM/CLM>
- Runtimes:
  - <https://github.com/huggingface/candle/tree/main/candle-transformers/src/models>, <https://github.com/huggingface/candle/tree/main/candle-transformers/src/models/gemma4> and <https://raw.githubusercontent.com/huggingface/candle/main/candle-transformers/src/models/mod.rs>
  - <https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md>
- Research: <https://arxiv.org/abs/2308.09895> (MultiPL-T); <https://arxiv.org/abs/2409.00557> (Learning to Ask: When LLM Agents Meet Unclear Instruction); <https://raw.githubusercontent.com/github-linguist/linguist/main/lib/linguist/languages.yml>
- Hardware: <https://store.steampowered.com/hwsurvey/> (August 2026)

## Verification notes

Adversarial fact-check, 2026-09-26. We re-read every pinned code citation in the local clones and re-fetched the live sources.

**Confirmed as written:**

- Anthropic IDs, prices, contexts, default efforts and retirement floors; Haiku 4.5's "not sooner than October 15, 2026"; the Opus 5.5 migration guide's rejection of forced `tool_choice` and its always-on thinking.
- OpenAI GPT-6 prices, 1.05M context, and the 2026-09-22 Sol/Luna release.
- Gemini 3.8 Flash's price step on 2027-01-01, and free-tier data use.
- xAI and DeepSeek prices.
- The BFCL V4 date (2026-04-12), its 109 rows, and every number in the §4.1 table.
- All EQ-Bench Elo values quoted, plus the judge, the English-only scope and the self-bias caveat.
- Qwen3.5-4B/9B card numbers; GGUF sizes of 2.74 and 2.91 GB.
- Gemma 4's Apache-2.0 license (E2B, 12B, 26B-A4B, 31B checked).
- Muse-Glimmer-30B: Apache-2.0, 29.78B, official Q4_K_M 16.76 GB.
- Qwen3.8-27B: Apache-2.0, 27.8B, 16.5 GB.
- Licenses of the Qwen3.8/Kimi-K3/GLM-5.3-Flash flagships.
- The LFM, Nemotron and Llama 4 license clauses.
- Jev's price, context and answer types.
- The Steam percentages.
- The CWR language table (the same in CWR-CE); the 473 and 73 registration counts; no `compile`/`isNil`/`sleep`/`spawn`/`execVM`/`waitUntil`/`switch`/`params` command anywhere in the repo; `remoteExec` at #L1228-L1229.
- The PoseidonEvaluator CLI flags; `--test-mission` and `--harness`.
- D047's no-bundling rule and manifest.
- The Gemma 4 E2B card's "effective parameters" and Per-Layer Embeddings wording; FunctionGemma's intended-use wording; the Kev-0.8B card's size list and Jev comparison; the "Learning to Ask" abstract quote (re-checked 2026-09-27).

**Corrected:**

- Muse-Glimmer's card does report agentic scores (vendor-only), and its repos ship a Usage Policy with a "military, warfare" clause.
- Fable 5.1 also rejects forced `tool_choice`.
- The PoseidonEvaluator validator's skip list applies to book/ref validation. `--eval` knows only about 145 core and mocked commands.
- candle has no Qwen3.5 module at all.
- T1 now assumes about 16 GB RAM; 8 GB machines get no default local pack.
- Local small-model picks are now candidates only, to be qualified by our own evals (§9).
- Steam sums are now computed over all buckets.
- GPT-6 reasoning levels are now verified.
- `--test-mission` is not verified to run headless.
- Citations fixed: Validate.cpp range and the D047 task-routing lines. EQ-Bench entry count and ordering fixed.

**Not verified:**

- The absence of any public SQF/SQS LLM benchmark (web search budget exhausted).
- The Mistral Medium 3.5 and Small 4 license claims.
- The Qwen3.6-35B-A3B, Gemma 4 E2B/E4B, Granite 4.2 and LFM2.5 GGUF sizes.
- Vanilla CWA 1.99's language set.
- Cross-doc claims attributed to docs 08, 09, 11 and 18. We did check pi-ai's `classify()` for TypeSafe in `packages/ai/src/api/typesafe-system-one.lazy.ts`.
