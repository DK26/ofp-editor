# Model-native harnesses: what each model was built to work with, and what Plotroom adopts

Research doc 51 for Plotroom (`ofp-editor`). Research date: 2026-09-27 and 2026-09-28 (UTC). Audience: the owner, contributors and
LLM coding agents; it is meant to be read alone.
Question answered (owner, 2026-09-27): "research what harness those models were reported to provide and give best results with, and
study those harness agents". Context: Plotroom will offer users free models that work well with its harness, each qualified per step
kind, and it screens candidates in the cloud before trying them locally ([D044](../decisions/D044-cloud-first-model-screening.md)).

**Status.** Research and proposals. **Nothing was run against a model**: no model was loaded, no keyed API was called and no money was
spent. Harness source code was read from public shallow clones at the commits pinned in §3. One throwaway local script fed hand-written
strings to Terminus 2's two pure-Python parser modules (§3.3); it calls no model. Model cards, vendor docs, leaderboards, papers and
issue trackers were read on 2026-09-27 and 2026-09-28; three facts were re-checked at the source during write-up (see Verification
notes). The adoption plan in §4, the test in §5 and the design-gap list in §6 are proposals; this doc changes no decision. The owner
decided on 2026-09-28, while this doc was being written, that the harness adapts to each model through per-model presets
([D048](../decisions/D048-per-model-harness-presets.md)); §4 and §5 are written as input to that decision and to
[doc 55](55-per-model-harness-presets.md) (draft, tuning runs pending; it reached the tree during review, see §4.1 and Verification
notes), which owns the knob catalogue, the preset file format and the tuning protocol.
**Epistemic legend** (doc 14's, as in docs 48, 50 and 53). **[V]** verified against the cited primary source (a model card, vendor
doc, code at the pinned commit, or a public leaderboard file). **[V-vendor]** the vendor's own number or claim about its own model.
**[V-3p]** a third-party report not confirmed at its source. **[V per doc N]** taken from a sibling doc. **[anecdote]** a single
community report. **[I]** our inference or proposal. **[U]** unknown. A CSV cell that mixes sources carries a combined label (for
example [V/anecdote] or [V/I]); a vendor-run test of other parties' serving (the K2 Vendor Verifier) is [V-vendor], not independent.
**Data.** [`data/model-profiles.csv`](data/model-profiles.csv): 44 rows, one per model row of §2 (`model, vendor_harness, tool_format,
reasoning_control, sampler, template_quirks, schema_mode_recommended, pitfalls, sources`). The harness, framework and synthesis rows
live in §3, not in the CSV.
**Relation to sibling docs.** Docs 10 and 11 studied Codex, OpenCode, pi, tinyagent and DeepSeek Harness, and doc 12 studied rig and
headroom; this doc does not re-study them. Docs 21, 25 and 38 define the step kinds and workflows served here; doc 40 the token
economy; docs 44 and 46 the local measurements and the bar; doc 47 the small-model candidates; doc 48 cloud providers and the 48-U
harness-uplift instrument; doc 50 free services and battery S; doc 53 tiny models; doc 55 (draft) presets and their tuning. Records:
D009, D021, D022, D023, D025, D026, D037, D044, and the four recorded on 2026-09-28: D045 (free-model offers on the user's own account,
only where qualified per step kind), D046 (aggregators with pinned routes), D047 (models and services whose policies ban military uses
or violent content: synthetic tests only, never a preset; the NVIDIA API trial and Z.ai not used) and D048 (per-model presets).
**Licences.** Every harness studied in code is Apache-2.0 or MIT, except the K2 Vendor Verifier, which has no licence file (all rights
reserved). Plotroom re-implements ideas in Rust and copies no code, prompt text or data from any of them; the few short phrases
quoted in this doc (repair or nudge wording, code comments) are quoted for commentary and are not adopted as Plotroom text. Where a
test case is re-authored as a known-value fixture, its doc comment cites the repository, commit, file and test name (AGENTS.md's porting rule,
applied here to third-party harnesses by analogy; see §6.1 item 7).
**Hygiene.** Public sources only. No private project, local path or user name appears here.
**Names.** *Native* means the model's trained conventions: chat template, tool dialect, reasoning switch, sampler and structured-output
wording. The *uniform capsule* is Plotroom's current single request shape: strict `response_format` (a grammar on `llama-server`), a
generic system line, thinking off and the tool's pinned sampler (`tools/local-qual/run.py`: T 0.6 for PICK, FILL and text; 0.2 for
EXPLAIN and knowledge); it is the natural first version of D048's general fallback preset. A *profile* (§4) holds the probed facts
about one model on one endpoint: what its template accepts, how its reasoning switches off, which schema features its host enforces.
A *preset* (D048) holds the tuned choices made within those facts: sampler values, answer format, schema mode, prompt layout. Step
kinds are PICK, FILL, COMPOSE, EXPLAIN and creative text (doc 47's DRAFT: briefings, radio lines, story beats).

## TL;DR

- **The harness behind a vendor's headline number is almost always a coding or computer-use agent** (Claude Code, Terminus 2,
  OpenHands, mini-SWE-agent, OpenCode, Qwen Code, Hermes Agent, OpenClaw), and the choice of harness alone moves the same weights a
  lot: Nemotron 3.5 Lightning scores 60.0 on SWE-bench Verified in OpenCode and 11.0 in Codex [V-vendor]. Those scores do not transfer
  to Plotroom's single bounded decisions, and the agent's general capabilities are out of product scope. What transfers is the **wire
  convention**: chat template, reasoning switch, sampler, output channel and host behaviour (§1).
- **Small models are very sensitive to those conventions.** On BFCL V4's 26 prompt formats the spread reaches 81.5 points (Phi-4),
  74.5 (Llama-3.1-8B) and 69.5 (Gemma-3-4B), against 14–18 for Qwen3 4B–32B. The safe cell for small models is a bare JSON answer with
  functions shown as JSON; asking for JSON inside a wrapper tag is lethal (Phi-4 falls to 1.5–11.0) [V]. A broken call path can zero
  a model: Ministral-8B-2410 scored 0.00% on every AST column with 100% "irrelevance" [V].
- **Fourteen incompatible native tool dialects** cover the 44 model rows (§2.6); parser bugs are the most common independent failure
  reported. PICK and FILL stay on `response_format` or a local grammar; a model's native tool channel becomes a qualification arm only
  for families whose trained syntax is not JSON [I].
- **Reasoning control is the largest adapter risk.** GLM-5.3, GLM-5.3-Flash, Kimi K3, gpt-oss, LFM2.5-2.6B and Muse-Glimmer cannot turn
  thinking off; defaults run up to `max`; Qwen3.8 answers `high` with HTTP 500; Gemini 3.7/3.8 Flash reject `minimal`; some knob pairs
  are rejected together (Moonshot's toggle plus effort, DashScope's effort plus budget) [V]. One explicit encoding per call, probed per
  endpoint, is the rule (§4.3).
- **Vendor samplers disagree by an order of magnitude**: T 1.0 (Gemma, NVIDIA, Granite 4.2, MiniCPM5, gpt-oss; Google says lowering it
  on Gemini 3 can cause loops), T 0.1–0.2 (Liquid, NuExtract3; Ministral "below 0.1"), and Qwen's presence penalty 1.5, which cost PICK
  calls in doc 46 [V]. The sampler is part of the qualified setup, pinned per (model, endpoint, step kind); server defaults are never
  inherited.
- **Structured-output quality belongs to the endpoint, not the model.** Z.ai's own harness trusts no first-party `json_schema` for GLM,
  DeepSeek, Kimi or MiniMax [V]; Moonshot's own verifier found tool-schema accuracy from 100% down to 71.96% across hosts serving the
  same weights [V-vendor]; some gpt-oss-120b endpoints score 22% on BFCL against a 37% reference [V]. Adopt the verifier's
  differential method as endpoint qualification for free hosts (§3.8, §4.8).
- **Eight harnesses were studied in code at pinned commits** (§3): Hermes Agent, the BFCL harness, Terminus 2, Mellea with BeeAI's
  RequirementAgent, Mistral Vibe's Rust harness core, ZCode with Kimi Code's provider layer, Qwen Code with Gemini CLI files, and the
  K2 Vendor Verifier: close to 200 cited lessons, condensed below and each marked adopt, adapt or reject. Their provider-adapter
  layers converge on the same ideas (§3.10); Mistral Vibe's sans-IO Rust reducer is the closest public analogue to Plotroom's workflow
  runtime.
- **Proposal for D048's presets (§4):** a *profile* of probed facts per model, wire and endpoint (tri-state capability fields,
  each unprobed, yes or no with evidence; one reasoning encoding; template rules; schema dialect; stop and intake rules; a typed error
  taxonomy in which upstream rate limits count against the endpoint's dependability), and the native-convention knobs D048's presets
  choose from, qualified per preset and step kind (D037, D044, D048). Profiles and presets shape requests to the provider the user
  configured and validate replies; they add no capability to Wilco.
- **A/B test (§5):** the general fallback preset (today's uniform capsule) against a native candidate preset on item-paired `pick-hard`
  and `fill` arms (k = 3, 252 calls per model and endpoint), then one factor at a time only if the bundle wins. A native knob enters a
  model's preset only if the bundle gains at least 4 of 90 PICK calls or 3 of 36 FILL calls (one-sided sign test, p ≤ 0.10) with no
  must-pass regression, and the gain holds on the held-out split (D048 item 4).
- **Corrections to earlier notes** (§6.4): BFCL's 50-point DeepSeek gap mixes call path with thinking; Qwen3-30B-2507's FC advantage
  comes from multi-turn and agentic columns, not single calls; Mistral's hosted API accepts consecutive user turns (its Hugging Face
  template does not); Gemini CLI does switch models silently under auto-routing; Hermes Agent's control-token neutraliser covers
  Harmony only; the K2 Vendor Verifier's headline F1 metric is not in its published code.

## 1. Why native conventions matter for weak models

### 1.1 The harness moves the score [V unless marked]

| Evidence | What changed | Spread |
| --- | --- | --- |
| Nemotron 3.5 Lightning card chart, same weights, unmodified harness prompts [V-vendor; numbers read from the chart image, which the card text introduces as "harness-level coding-agent results"; re-read from the image at review] | Harness | SWE-bench Verified: OpenCode 60.0, Copilot CLI 58.4, Claude Code 57.4, Pi 54.5, mini-SWE-agent 50.7, OpenHands 48.7, Hermes 45.7, Codex 11.0. Terminal-Bench 2.1: mini-SWE-agent 29.7 down to Codex 2.9 |
| Qwen3-Coder-Next technical report, Table 5, Terminal-Bench 2.0 [V-vendor] | Harness and envelope | Qwen3-Coder-Next: Terminus2-json 36.2, Terminus2-xml 34.2, Claude Code 30.9, Qwen Code 25.8 (the vendor's own CLI is lowest). Kimi-K2.5: 49.4 / 38.8 / 9.0 / 27.5. GLM-4.7: XML 44.9 beats JSON 37.1 |
| Qwen3.6-35B-A3B card re-runs Qwen3.5-35B-A3B on SkillsBench through OpenCode [V-vendor] | Model generation in one harness | 4.4 against 28.7 |
| gpt-oss-20b, Mavrin (arXiv 2604.00362) | Native Harmony harness and in-distribution tools | Only the native setup reproduced OpenAI's numbers (SWE-bench Verified high 60.4 vs 60.7 published); declaring the tools in the system message raised the search-call rate from 3.8% to 58.8% |
| K2 Vendor Verifier, Kimi K2-0905, 4,000 requests [V-vendor: Moonshot's own test of other hosts] | Host (same weights) | Tool-schema accuracy 100% (Moonshot, Fireworks, DeepInfra, Novita, Groq), 84.47% Nebius, 76.00% vLLM, 73.13% SGLang, 71.96% Together; trigger F1 69.52% Groq, 50.60% Nebius |
| Artificial Analysis Endpoint Accuracy Index (2026-08-04) | Host | Some gpt-oss-120b endpoints score 22% on its BFCL-500 subset against 37% for the reference, because "providers parse and format tool calls differently" |
| BFCL V4 format sensitivity (26 configurations × 200 items) | Prompt rendering only | Max delta Phi-4 81.5, Llama-3.1-8B 74.5, Gemma-3-4B 69.5, MiniCPM3-4B 68.0, Qwen3-0.6B 60.5, Mistral-Small-2506 50.0; Qwen3 4B–32B 14–18; DeepSeek-V3.2 10 |
| BFCL V4, Ministral-8B-Instruct-2410 (FC) | Call path | 0.00% on every AST column and 100.00% irrelevance: an adapter failure scored as perfect restraint |
| Aider polyglot, Qwen2.5-Coder-32B (older generation) | Edit format | "diff" 8.0% (71.6% well-formed) against "whole" 16.4% (99.6% well-formed) |
| MiniMax-M3 on Terminal-Bench 2.1 [V-vendor against V] | Vendor versus independent harness | Vendor (Terminus 2) 66.0% against Vals AI's own harness 53.56% |
| DeepSeek V4 Pro, NIST CAISI (Inspect ReAct) | Independent agent scaffold | About eight months behind leading US models, against the vendor's parity claim; CAISI reproduced the vendor's GPQA number to rule out misconfiguration |

### 1.2 Where native conventions matter less [V]

- Moonshot's only published same-model pair: Kimi K3 on DeepSWE, 67.5 in Kimi Code against 67.3 in mini-SWE-agent [V-vendor].
- Frontier models are format-insensitive on Terminus 2: Claude Opus 4.5 58.4 (XML) against 57.3 (JSON); Sonnet 4.5 51.7 in both
  (measured by Qwen, Qwen3-Coder-Next report Table 5).
- Qwen3 4B–32B format deltas stay at 14–18 points; Qwen3-4B-2507 scores 35.68% in FC mode and 35.52% in prompt mode.
- Constrained decoding did not cost accuracy in JSONSchemaBench (Llama-3.1-8B GSM8K 80.1% unconstrained, 83.8% with Guidance, 82.4%
  with llama.cpp) and moved value accuracy only −0.007 to +0.033 in the Structured Output Benchmark (arXiv 2604.25359): grammars fix
  syntax, not semantics. Liquid's IFStruct excludes constrained decoding for the same reason.

Reading [I]: sensitivity falls with size and with multi-template training (Qwen3-Coder-Next was trained on 21 tool templates and
reports SWE-bench rising with their number, because "many existing models are trained with a single tool chat template, which often
leads to overfitting to specific output structures"). It stays large at 8B and below, which is Plotroom's local tier. A grammar
removes the syntax part of the risk; prompt layout, sampler, reasoning leakage and host defects remain.

### 1.3 What transfers to Plotroom's step kinds [I on V]

| Convention | Transfers? | Why |
| --- | --- | --- |
| A coding-agent benchmark score | Prior only | Multi-turn shell and file agents; Plotroom's steps are single bounded decisions, and its agent is product-scoped (AGENTS.md) |
| The trained tool-call dialect | Only on a tools channel | PICK and FILL use `response_format` or a grammar (doc 38 §3.3); the tools channel becomes a qualification arm (§5) |
| The reasoning switch and its levels | Yes, always | A wrong switch leaks reasoning, burns budget or returns HTTP errors |
| The vendor sampler | Yes, as a pinned, qualified value | Presets differ tenfold and server defaults differ per host |
| Template rules (system position, roles, alternation, default system text, BOS) | Yes | Templates raise errors or degrade silently |
| Trained structured-output wording (NVIDIA's "Response Formatting Schema", IBM's JSON system prompt, Harmony's "# Response Formats", NuExtract's template, Qwen's `answer` field) | Maybe | Tested by §5 |
| Host behaviour (parsers, schema engines, retention, rate limits) | Yes, per endpoint | K2 Vendor Verifier, AA Endpoint Accuracy, doc 48 §2.3 |

### 1.4 Vendors now train inside named third-party harnesses [V-vendor]

Liquid trained LFM2.5-2.6B "directly inside Hermes Agent, OpenClaw, and other harnesses"; Spark-X2.5 is "deeply integrated" with Codex,
Claude Code, OpenClaw and Hermes; NVIDIA's technical blog (not the card) says Lightning is "designed for harnesses like OpenClaw and
Hermes Agent", and NVIDIA lists Hermes,
OpenCode, Terminus and Droid data; IBM generated Granite 4.2 SFT trajectories with 12 scaffolds (OpenHands, OpenCode, Terminus-2,
SWE-agent, Gemini CLI, Hermes, Codex, Goose and others); Qwen scaled Qwen3.8 RL "across several popular harnesses" (QwenWork, Claude
Code, Codex, OpenClaw, Hermes; read through search snippets); Nemotron-Terminal is "trained using the Terminus 2 scaffolding". Plotroom's
harness is none of these, so expect a transfer gap and qualify per (model, profile), not per model [I]. The vendor's own claims need
measuring too: on NVIDIA's chart, Hermes, a harness Lightning was "designed for", ranks seventh of eight on SWE-bench Verified.

## 2. Per-model findings

Forty-four model rows, grouped by family. Each table keeps the facts that shape an adapter; the CSV holds the full cells with sources.
Cells are [V] or [V-vendor] unless marked; the last column is ours [I]. "Off" means how to switch thinking off.

### 2.1 Qwen and derivatives

| Model | Harness named by the vendor, and scaffolds behind its numbers | Native tool format | Reasoning control | Vendor sampler | Plotroom notes [I] |
| --- | --- | --- | --- | --- | --- |
| Qwen3.5-4B (2B, 9B) | Qwen-Agent (`use_raw_api`, server parses) and Qwen Code; vLLM/SGLang `qwen3` + `qwen3_coder`; BFCL-V4 50.3 in thinking mode, FC or prompt [U] | qwen3_coder XML | On by default (2B off); off = `enable_thinking=false`; no effort; Unsloth and doc 46 disagree on the GGUF default | Non-thinking T 0.7, top_p 0.8, top_k 20, presence 1.5 | Local GBNF, thinking off, presence pinned to 0 (doc 46); qualified for PICK and EXPLAIN with cards (doc 44) |
| Qwen3.5-27B, 35B-A3B | As above; SWE and Terminal scaffolds not footnoted [U]; harness-bench 55/80 | qwen3_coder XML | As above | As above | Cloud screen on fp8 hosts (doc 50); FILL schemas in reading order, required-but-nullable fields (#20164) |
| Qwen3.6-35B-A3B, 27B | Qwen-Agent with `preserve_thinking`; SWE in an internal bash-plus-edit scaffold; Terminal-Bench in Terminus-2; SkillsBench in OpenCode; NL2Repo in Claude Code | qwen3_coder XML (non-strings as JSON) | On by default; `preserve_thinking` kwarg, default off | Non-thinking as 3.5; `generation_config` holds only the thinking sampler | Pin every sampler key (vLLM applies `generation_config`); build after llama.cpp #24807's fix; f16 KV |
| Qwen3.8-27B (`:free`) | Card names no Qwen harness; Claude Code and Terminus for its numbers; RL "across several popular harnesses" | qwen3_coder XML (`qwen3_xml` or `qwen3_coder`) | On by default; effort `xhigh` (default), `medium`, `low` only, `high` → HTTP 500; `preserve_thinking` default ON | Thinking T 1.0, top_p 0.95, top_k 20, presence 0; non-thinking T 0.7, top_p 0.8, presence 1.5 | `:free`: reasoning off and `preserve_thinking` false sent explicitly; strict schema only if canary Z01 shows it enforced (doc 48) |
| Qwen3-4B-Instruct-2507 | Qwen-Agent's internal Hermes-style "nous" template; BFCL FC 35.68 vs prompt 35.52 | Hermes JSON `<tool_call>` | Non-thinking only | T 0.7, top_p 0.8, top_k 20; presence optional | Channel barely matters; JSON-rendered menus; candidate native factor: the `answer` field convention |
| Qwen3-30B-A3B-Instruct-2507 | As the 4B; BFCL FC 41.39 vs prompt 36.70 | Hermes JSON | Non-thinking only | As the 4B | The FC gain is multi-turn and agentic; single-call AST favours prompt mode (§3.2 B4) |
| Qwen3-Coder, Coder-Next | Qwen Code, Cline, Claude Code, Kilo and others; SWE-bench across SWE-Agent, mini-SWE-agent, OpenHands | qwen3_coder XML; Coder-Next trained on 21 templates | Non-thinking | 480B/30B T 0.7, top_p 0.8, top_k 20, rep 1.05; Next T 1.0, top_p 0.95, top_k 40 | Not a candidate; lesson: long text as plain bounded text, not escaped JSON strings |
| Ternary Bonsai 2 27B | Bonsai-demo scripts plus the PrismML llama.cpp fork (stock llama.cpp rejects its formats) | Qwen3.8 template | Default `xhigh`; `low` behaves like `xhigh`; `high` → 500; off via `none` with `--reasoning auto` or `enable_thinking=false` | As Qwen3.8; GGUF lacks `min_p`, so llama.cpp's 0.05 applies | Bring-your-own, unqualified; schema steps only after a canary proves the fork's grammar is enforced |
| NuExtract3 | NuMind vLLM recipe, API and `numind` SDK (JSON Schema → NuExtract template) | No tools; a typed JSON template via `chat_template_kwargs.template` | Default off | Non-thinking T 0.2 | A FILL-only template adapter (§4.4); local only |

### 2.2 Google

| Model | Harness named by the vendor | Native tool format | Reasoning control | Vendor sampler | Plotroom notes [I] |
| --- | --- | --- | --- | --- | --- |
| Gemma 4 E4B (QAT; the provisional default) | LiteRT-LM with llguidance plus AI Edge Gallery "Agent Skills"; vLLM `gemma4` parsers (`skip_special_tokens=False`); ADK uses the plain Gemini classes | Gemma 4 tokens, not JSON: `<\|tool_call>call:name{k:<\|"\|>v<\|"\|>}<tool_call\|>` | `<\|think\|>` in the system prompt; E4B emits no tags when off; llama-server and Ollama templates default ON (doc 46) | T 1.0, top_p 0.95, top_k 64 for all uses | Local GBNF, thinking off, whitespace-free grammar (it pretty-prints JSON under a grammar: 16 tokens per pick instead of 7); pin the GGUF revision and template hash |
| Gemma 4 26B-A4B | As E4B, plus the Gemini API and ADK; OpenRouter `:free` = AI Studio | Gemma 4 tokens | When off, still emits an empty thought block and sometimes leaks a thought channel; Gemini API `high` or `minimal` only | As E4B; `:free` rejects `top_k` | Cloud screen on bf16/fp8 hosts; `:free` (Google AI Studio) has no strict schema, keeps prompts 55 days and is never a preset (D045): no-schema arms on synthetic suites only; local grammar must allow the empty block |
| Gemma 4 31B | As 26B | Gemma 4 tokens | As 26B | As E4B | Cloud only; EXPLAIN card-bound (AA-Omniscience −45) |
| Gemini 3.1 Flash-Lite | ADK 2.x, Gemini CLI, Antigravity (closed), Interactions API or `generateContent`; vendor scores at high thinking | FunctionDeclaration; `responseJsonSchema` subset | `thinking_level` minimal (default, "does not guarantee that thinking is off"), low, medium, high; surfaces differ | Keep T 1.0; lower "may lead to … looping"; 3.5 guide: remove T, top_p, top_k | Strict schema on Vertex ZDR (doc 48 R18); K diversity from T 1.0 plus menu permutations |
| Gemini 3.5 Flash-Lite | As above | As above | As above | Remove sampler keys | Dominated by 3.1 Flash-Lite (doc 48) |
| Gemini 3.5–3.8 Flash | As above; 3.8 Flash's DeepSWE in mini-swe-agent, Terminal-Bench in Terminus 2 | As above | Default medium; 3.7 and 3.8 reject `minimal` with a 400 | Remove sampler keys | Lowest level is a profile value, never hard-coded |

### 2.3 Meta, Microsoft and Meta's Muse line

| Model | Harness | Native tool format | Reasoning | Vendor sampler | Plotroom notes [I] |
| --- | --- | --- | --- | --- | --- |
| Llama 4 Scout, Maverick | Llama Stack became OGX (model-agnostic server); in practice vLLM `llama4_pythonic` | Pythonic list or JSON `{name, parameters}`; results in `ipython` role; never text and calls together | None | T 0.6, top_p 0.9 | Not a default (licence; no Czech, Polish or Russian) |
| Llama 3.1 / 3.2 / 3.3 | OGX, llama-cookbook; vLLM `llama3_json`, `pythonic` | 3.1/3.3 JSON in the user prompt with `Environment: ipython`; 3.2 pythonic | None | T 0.6, top_p 0.9 | Format max delta 74.5 (3.1-8B): fixed JSON rendering if ever used |
| Phi-4-mini-instruct | Phi Cookbook, Foundry Local plus Agent Framework; vLLM `phi4_mini_json` | JSON inside `<\|tool\|>…<\|/tool\|>` in the system turn; emits `functools[...]` | None | Greedy in examples | Not in doc 47 yet; vLLM PR #58072 (empty call blanks the reply) |
| Phi-4, reasoning variants | Foundry, Agent Framework | None documented; reasoning variants cannot call functions | Reasoning variants always reason with a fixed system prompt | Reasoning-plus "must use" T 0.8, top_k 50, top_p 0.95 | Not a candidate; the most format-sensitive BFCL row (81.5) |
| Muse-Glimmer-30B, Muse Spark | Meta Model API; Muse Code; Glimmer cites OpenClaw and Hermes Agent | OpenAI-compatible; parser [U] | Glimmer mandatory, via "Reasoning strength: X" in the system prompt | T 1.0, top_p 0.95, top_k 64 | Its use policy bans military uses: synthetic tests only, never recommended or a preset (D047) |

### 2.4 NVIDIA, IBM, Liquid, OpenBMB, SparkLLM, dots

| Model | Harness | Native tool format | Reasoning | Vendor sampler | Plotroom notes [I] |
| --- | --- | --- | --- | --- | --- |
| Nemotron 3 Super (`:free`) | OpenCode, OpenClaw, Kilo Code, OpenHands; NeMo Agent Toolkit; scores from NeMo Evaluator/Skills | qwen3_coder XML in ChatML; `nemotron_v3` reasoning parser | Default on; `low_effort`; client `reasoning_budget`; fully off on `:free` [U] | T 1.0, top_p 0.95 everywhere | Always `response_format` (an anecdote: prompt-only JSON 2/12 valid, strict 12/12); its `:free` endpoint runs under the NVIDIA API trial terms, which D047 excludes from every test, so paid hosts only |
| Nemotron 3 Ultra (`:free`) | OpenCode; NeMo Gym, Skills, Harbor | As Super | `medium_effort` (not `low_effort`); with tools `force_nonempty_content` | As Super | `:free` has no schema support and runs under NVIDIA trial terms: not used (D047 drops doc 48's Z13) |
| Nemotron 3.5 Lightning (`:free`) | "Designed for" OpenClaw and Hermes (NVIDIA blog); NeMo Switchyard router; the harness chart in §1.1 | qwen3_coder XML with an `<IMPORTANT>` reminder | Default on; history thinking truncated; no effort knob [U] | T 1.0, top_p 0.95 (Unsloth: 0.6 thinking, 0.2 instruct) | Strict schema on paid ZDR bf16 copies; `:free` lacks `response_format` |
| Nemotron 3 Nano, Nano Omni | vLLM, SGLang, TRT-LLM, llama.cpp recipes; open evaluation recipe | qwen3_coder XML; `nano_v3` plugin | Default on | Reasoning T 1.0, top_p 1.0; **tool calling T 0.6, top_p 0.95** | Doc 47 skip; its trained "Response Formatting Schema" wording is a §5 factor |
| Granite 4.2 3B, 8B | Card configs for OpenCode, Pi, OpenHands; SFT from 12 scaffolds; the 3B had no agentic RL | Nemotron-style ChatML with qwen3_coder XML (a break from 4.0/4.1) | Default on; `low_effort` appends text to the user message | T 1.0, top_p 0.95 everywhere | Single-step steps only; thinking off; DeepInfra copy has no schema flag (no-schema arms) |
| Granite 4.1 3B (doc 44 baseline) | Plain chat template; BeeAI; IBM's guide | Granite role tokens with Hermes JSON; a trained `documents` grounding channel | None | None published (greedy examples) | IBM's JSON system wording and the `documents` channel are §5 factors; GBNF fallback for llama.cpp #29006 |
| Granite 4.0 H-Tiny, H-1B, 1B, Micro | BeeAI RequirementAgent; Mellea with Granite Libraries | As 4.1 | None | None | FILL must be grammar-constrained (IFStruct: H-Tiny 38.75% unconstrained) |
| LFM2.5-2.6B (`:free`) | Trained inside Hermes, OpenClaw and Pi; Hermes needs `tool_use_enforcement` | Pythonic `<\|tool_call_start\|>[f(a='v')]<\|tool_call_end\|>`; JSON on request | Always thinks (no off switch) | T 0.1, top_k 50, rep 1.1 | `:free` strict arms at effort low with reasoning headroom (8,192 output cap); avoid the tools path (#23838) |
| LFM2.5-1.2B, 8B-A1B | Fine-tuning recommended; vendor BFCL via "a custom Liquid handler" | Pythonic | 1.2B none; 8B-A1B always | 1.2B T 0.1; 8B-A1B T 0.2 | Doc 47 watch or skip |
| MiniCPM5-2B | SGLang recommended (`minicpm5` parser); deployment "Agent Skills" | XML `<function name><param name>` with CDATA | Hybrid; unset lets the model decide | T 1.0, top_p 0.95, **min_p 0** ("default min_p=0.05 can lead to repetitive output") | Local only; send `enable_thinking=false`; English and Chinese only |
| Spark-X2.5-4B | "Deeply integrated" with Codex, Claude Code, OpenClaw, Hermes; SGLang `spark25` | GLM-style `<arg_key>/<arg_value>`; `<\|Tool\|>` role | Default on; off emits a bare `</think>` | T 1.0, top_p 0.95, top_k −1 | Local only; check the reasoning parser on the unpaired tag |
| dots3-note preview (`:free`) | No harness on the card; Terminus-2 (JSON parser), live-swe-agent, OpenClaw-style, Claude Code in footnotes | `<dots_function_call><invoke>` | Default on; off appends `<no_think>` to every user turn | T 1.0, top_p 0.95 (footnotes vary) | Doc 48's strict fallback on `:free`; no seed |

### 2.5 Open frontier and other vendors

| Model | Harness | Native tool format | Reasoning | Vendor sampler | Plotroom notes [I] |
| --- | --- | --- | --- | --- | --- |
| gpt-oss-120b, 20b | Harmony only; `openai/gpt-oss` reference servers, `openai/harmony`, Codex | Harmony channels; structured output as "# Response Formats" in the developer message | Mandatory; `Reasoning: low\|medium\|high`; about 300 hidden tokens at low (doc 48) | T 1.0, top_p 1.0 | The host's strict output (Groq Free, fp4 and bf16 hosts); effort low; `finish_reason=length` is a failure |
| DeepSeek V4.1 Flash | Claude Code, OpenClaw, OpenCode; Codex via Responses; DeepSeek Harness; no Jinja template (`encoding_dsv4.py`) | DSML `<｜DSML｜invoke>`; first-party `json_object` only | `thinking` toggle on every request plus effort low/high/max | T 1.0, top_p 1.0; thinking mode ignores T | Thinking disabled; strict schema from a host; reasoning echo per host |
| GLM-5.3-Flash | ZCode; Coding Plan in Claude Code, Cline, OpenCode, Kilo, Codex | GLM `<arg_key>/<arg_value>`; first-party `json_object` only | **Cannot disable**; low/high/max, default max | T 1.0, top_p 0.95 | Batch COMPOSE and creative text only; always send low; never send a disable switch (vLLM PR #56994); third-party hosts only, since Z.ai's own service is not used (D047) |
| GLM-5.3 | ZCode; Claude Code for most numbers | As Flash | **Cannot disable** | T 1.0 | Writer candidate on a third-party host (not Z.ai, D047); pin the id |
| Kimi K2.6 | Kimi Code (kosong); K2 Vendor Verifier; Terminus-2 JSON for Terminal-Bench | Kimi special tokens, `functions.NAME:IDX` ids; `json_object` only | Toggle or effort, never both; self-hosted key is `thinking`, not `enable_thinking` | Locked: T 1.0 thinking, 0.6 instant | Instant mode; normalise schemas to Moonshot's subset |
| Kimi K3 | Kimi Code | K2 family [I] | **Cannot disable**; default max (about 3× medium through relays) | T 1.0 | Reference only |
| MiniMax-M3 | Claude Code, Terminus 2; MiniMax Code; Mini-Agent reference | `<minimax:tool_call><invoke>`; no first-party `response_format` | enabled, adaptive, disabled | T 1.0, top_p 0.95, top_k 40 | Disabled for PICK and FILL; CJK think tags (思考, 反思, 推理, 推敲) |
| Mistral Small 4 | Mistral API, Vibe, Agents API | `[TOOL_CALLS]` tokens; strict `json_schema` first-party | `none` or `high` only | none: T 0.0–0.7; high: T 0.7 | Send `none` explicitly; `prompt_cache_key`; repairs as fresh single-turn capsules. Mistral's hosted policy names military content: hosted results are synthetic-only and never a preset (D047) |
| Ministral 3 | None dedicated; vLLM `mistral` parser | Mistral tokens | None | **T below 0.1** | Calibration anchor (doc 50); test voting at T 0.6 against single-shot near 0 |
| Devstral 2 | Mistral Vibe CLI (primary) | Mistral tokens | None | T 0.15 | Out of scope |
| Hermes 4 / 4.3 | Hermes Agent | Hermes JSON `<tool_call>` | Hybrid; a system-prompt sentence can switch it on | T 0.6, top_p 0.95, top_k 20 | Not a candidate; the harness is the value (§3.1) |
| Ling 3.0 Flash | None; vLLM/SGLang `ling3` | [U] | Default on | T 0.6, top_p 0.95, top_k 20 | No enforcing host: open arms only |

### 2.6 Cross-family tables

#### 2.6.1 Native tool dialects [V]

| Dialect | Shape | Models | Parsers | Known parser defects (2026) |
| --- | --- | --- | --- | --- |
| qwen3_coder XML | `<tool_call><function=NAME><parameter=K>v</parameter></function></tool_call>` | Qwen3.5, 3.6, 3.8, Coder; Bonsai 2; Nemotron 3 Super, Ultra, Nano, 3.5 Lightning; Granite 4.2 (11 rows) | vLLM/SGLang `qwen3_coder`, `qwen3_xml`; llama.cpp peg-native | llama.cpp #20164, #20260, #24807; merged `<function=parameter=…>` tag on Nemotron Super |
| Hermes JSON | `<tool_call>{"name","arguments"}</tool_call>`, tools in `<tools>` | Qwen3-2507, Hermes 4, Granite 4.0/4.1 (with Granite role tokens) | `hermes`, `qwen25`; Qwen-Agent parses itself | llama.cpp #29006 (schema plus control tokens → 400) |
| Harmony | channels; `to=functions.NAME <\|constrain\|>json` | gpt-oss | `openai_gptoss`; openai/harmony | llama.cpp #19051 fail-open; vLLM #37359 |
| DSML | `<｜DSML｜invoke name><｜DSML｜parameter string=…>` | DeepSeek V4, V4.1 | `deepseek_v4`, `deepseek_v41` | vLLM #48931, #41240; the V4.1 spacing miss |
| Kimi tokens | `<\|tool_call_begin\|>functions.NAME:IDX<\|tool_call_argument_begin\|>{json}` | Kimi K2.x, K3 | vLLM, SGLang Kimi parsers | K2VV: dropped `add_generation_prompt`, strict id parser (vLLM) |
| GLM arg pairs | `<tool_call>NAME<arg_key>K</arg_key><arg_value>V</arg_value>` | GLM-5.x; Spark-X2.5 (GLM-like) | `glm47`; `spark25` | GLM-5.1 template ignored array tool content |
| MiniMax invoke | `<minimax:tool_call><invoke name><parameter name>` | MiniMax-M3 | SGLang MiniMax parser | — |
| dots invoke | `<dots_function_call><invoke name><parameter name>` | dots3 | `dots` (PRs open) | Preview |
| Mistral tokens | `[AVAILABLE_TOOLS]`, `[TOOL_CALLS]`, `[TOOL_RESULTS]` | Mistral Small 4, Ministral 3, Devstral 2 | `mistral` | BFCL's Ministral-8B zero |
| Llama pythonic / JSON | `[f(p=v)]` or `{name, parameters}` | Llama 3.x, 4 | `llama3_json`, `llama4_pythonic`, `pythonic` | Smaller Llamas "frequently fail to emit tool calls in the correct format" (vLLM) |
| LFM pythonic | `<\|tool_call_start\|>[f(a='v')]<\|tool_call_end\|>` | LFM2.5 | llama.cpp LFM2 parser | llama.cpp #23838 |
| MiniCPM5 XML | `<function name><param name>` with CDATA | MiniCPM5 | SGLang `minicpm5` | Malformed output on SGLang for some builds [anecdote] |
| Gemma 4 tokens | `<\|tool_call>call:name{k:<\|"\|>v<\|"\|>}<tool_call\|>` | Gemma 4 | vLLM `gemma4`; llama.cpp | llama.cpp PR #21326; Ollama #15241; the protocol-boundary loop report |
| Phi-4-mini | `functools[...]` | Phi-4-mini | `phi4_mini_json` | vLLM PR #58072 |

#### 2.6.2 Reasoning switches [V]

| Family | Off switch | Levels | Cannot turn off | Traps |
| --- | --- | --- | --- | --- |
| Qwen3.5, 3.6 | `chat_template_kwargs.enable_thinking=false` | none | — | GGUF template defaults disagree (Unsloth vs doc 46) |
| Qwen3.8 | `enable_thinking=false`; OpenRouter `reasoning.enabled=false` | `low`, `medium`, `xhigh` | Hosted Qwen3.8-Max-Preview (400 on false) | `high` → 500; effort with `thinking_budget` rejected; `preserve_thinking` default on |
| Gemma 4 | omit `<\|think\|>`; `enable_thinking=false` | Gemini API `high`/`minimal` | — | 26B/31B emit an empty block anyway; local templates default on |
| Gemini 3.x | none guaranteed | `minimal`…`high` | 3.7/3.8 Flash reject `minimal` | a gateway silently promoted `minimal` to `low` |
| Nemotron 3 | `enable_thinking=false` | `low_effort` (Super), `medium_effort` (Ultra) | — | vocabulary differs per model id |
| Granite 4.2 | `enable_thinking=false` | `low_effort` (edits the user text) | — | cache keys change |
| gpt-oss | — | `low`, `medium`, `high` | Yes | about 300 tokens at low |
| DeepSeek V4.x | `thinking:{type:disabled}` every request | `low`, `high`, `max` | — | echo rules with tools |
| GLM-5.3, 5.3-Flash | — | `low`, `high`, `max` (default max) | Yes | `enable_thinking=false` leaks the scratchpad into content |
| Kimi K2.6 | `thinking:{type:disabled}` (API) or `thinking:false` (self-hosted) | effort | — | toggle plus effort → 400 |
| Kimi K3 | — | `low`, `high`, `max` (default max) | Yes | relay default max |
| MiniMax-M3 | `thinking: disabled` | `adaptive` | — | byte-exact replay |
| Mistral Small 4 | `reasoning_effort: "none"` | `none`, `high` | — | omitting it leaves the server default [U] |
| LFM2.5-2.6B, 8B-A1B | — | effort (hosted) | Yes | 8,192 output cap on `:free` |
| MiniCPM5 | `enable_thinking=false` | — | — | unset lets the model decide |
| Spark-X2.5 | `enable_thinking=false` | — | — | bare `</think>` |
| dots3 | `enable_thinking=false` | — | — | `<no_think>` appended to every user turn |
| Muse-Glimmer | — | system-prompt strength | Yes | lives in the prompt prefix |

#### 2.6.3 First-party structured output [V]

JSON Schema enforced first-party: Mistral (strict) and Gemini (a subset). `json_object` only: DeepSeek (plus a strict function-calling
beta), Z.ai GLM, Moonshot Kimi. None: MiniMax first-party Chat. Open-weight models with no first-party API (gpt-oss, Gemma, Qwen, Granite
and the small models) depend entirely on the host: doc 48 §2.3 found capability flags wrong in at least six cases, Z.ai's own ZCode table
marks `supportsJsonSchemaOutput=false` for GLM, DeepSeek, Kimi and MiniMax first-party, and the same weights are flagged true on other
routes (for example DeepSeek V4.1 Flash on OpenRouter). On OpenRouter's free list, Qwen3.8-27B lists `structured_outputs` without
`response_format` [U until canary Z01], Gemma 4 lists `response_format` without `structured_outputs`, Nemotron Ultra and Lightning list
neither, and LFM2.5 and dots3 list both.

## 3. Harness code studies

### 3.0 How the eight harnesses were chosen [V counts; I choice]

Every model row names the harnesses its vendor recommends, trains in or evaluates in, or whose source encodes its adapter rules. Counted
over the 44 model rows (a row counts once per harness): BFCL 24; the τ-bench family 18; Hermes Agent 15; Terminus 2 in Harbor 15;
Claude Code 11; OpenClaw 9; mini-SWE-agent 8; OpenCode 8; pi 7; Codex 6; Qwen-Agent 6; Google ADK 6; Qwen Code 5; ZCode 5; NVIDIA's
NeMo Gym, Skills and Evaluator 5; OpenHands 5; IFStruct 5; the AA Endpoint Accuracy Index 5; Gemini CLI 4; Mistral Vibe 3; Kimi Code 3;
BeeAI and Mellea 2 each; the K2 Vendor Verifier 1–2. Removed: harnesses already studied (OpenCode and Codex in doc 10; pi and DeepSeek
Harness in doc 11), closed source (Claude Code, Antigravity, Copilot CLI, the AA index), general computer-use or coding agents with no
adapter layer worth reading (OpenClaw, OpenHands, mini-SWE-agent, Kilo Code, Cline) and multi-turn policy benchmarks far from PICK and
FILL (τ-bench). Kept: the harnesses whose model-facing layers teach something about formats, prompting, decoding, repair, context
handling or model adapters.

| # | Harness | Repository at commit (date) | Licence | Rows | Why studied |
| --- | --- | --- | --- | --- | --- |
| 3.1 | Hermes Agent | NousResearch/hermes-agent @04ea129 (2026-09-28) | MIT | 15 | The largest public catalogue of per-host and per-family adapter rules; the training harness of LFM2.5, Lightning, Spark-X2.5 and Granite 4.2 |
| 3.2 | BFCL harness | ShishirPatil/gorilla, `berkeley-function-call-leaderboard/` @6ea5797 (2026-03-23) | Apache-2.0 (code and data) | 24 | Hand-written handlers per family in native-FC and prompt mode; the format-sensitivity machinery |
| 3.3 | Terminus 2 | harbor-framework/harbor, `src/harbor/agents/terminus_2/` @3c82380 (2026-09-26) | Apache-2.0 | 15 | The only widely used scaffold shaped like Plotroom: one structured envelope per turn, no native tools, a tolerant parser and fed-back warnings |
| 3.4 | Mellea + BeeAI RequirementAgent | generative-computing/mellea @1276bf6 (2026-09-25); i-am-bee/beeai-framework @08c1edf (2026-09-25) | Apache-2.0 | 3 | IBM's reliability layer for small Granite models (granite-io was folded into Mellea and archived on 2026-06-30) |
| 3.5 | Mistral Vibe harness core | mistralai/mistral-vibe, `harness/core/` @7c19608 (v2.25.8, 2026-09-23) | Apache-2.0 | 3 | The only vendor harness core written in Rust (edition 2024): a sans-IO step reducer |
| 3.6 | ZCode + Kimi Code's kosong | zai-org/ZCode @29628c9 (v3.14.3, 2026-09-24); MoonshotAI/kimi-code @be7d5f5 (2026-09-24) | Apache-2.0; MIT | 7 | Per-model capability tables kept as data; reasoning-field dialects |
| 3.7 | Qwen Code + Gemini CLI | QwenLM/qwen-code @3f5ae3f (v0.24.6, 2026-09-27); google-gemini/gemini-cli @2fe7c2d (2026-09-25) | Apache-2.0 | 8 | Per-model thinking capabilities, few-shot in the model's notation, loop detectors, quota classification |
| 3.8 | K2 Vendor Verifier | MoonshotAI/K2-Vendor-Verifier @0bc5061 (2026-02-14); successor MoonshotAI/Kimi-Vendor-Verifier @66092cf (2026-09-17) | None (ideas only); successor MIT | 1–2 | A vendor-published differential test that qualifies hosts, not models |

Verdict words: **ADOPT** (take the idea as is), **ADAPT** (take it with the stated change), **REJECT** (do not take it). Evidence is
`path:lines` relative to the repository root at the pinned commit unless a prefix names another repository. Each lesson is re-stated in
this project's words; no code is copied.

### 3.1 Hermes Agent (Nous Research) @04ea129

Hermes Agent is a long, multi-turn general agent (terminal, files, browser, kanban). It refuses models under 64K context, and its
system prompt plus tool schemas take 4–8K tokens. Only its provider-adapter layer is in scope. Two corrections to earlier notes: its
control-token neutraliser covers **only** gpt-oss's Harmony tokens (a test asserts `<|im_start|>` is left untouched), and the tree
holds **no per-model tool-call parser table**, only server-flag prose in `website/docs/integrations/providers.md:858-895, 1118-1130`
[U: possibly in a separate Nous RL repository]. `agent/` has no LFM2.5, Granite 4.2 or Spark-X adapter code: what models trained in
Hermes inherit is its trajectory format (H2), not per-model adapters.

- **H1 · Scope (REJECT the loop; ADOPT the adapter layer).** Models RL-trained in Hermes are used to long tool-loop transcripts, while
  Plotroom sends small single-decision capsules; format fluency transfers, the context distribution does not.
  `agent/model_metadata.py:271-272` (`MINIMUM_CONTEXT_LENGTH = 64_000`). → The harness keeps state; capsules stay small (doc 21 §8,
  doc 40 §4.1); a Hermes-trained model's agent score says little about PICK or FILL.
- **H2 · The trajectory format trained models see (ADAPT).** Tools as JSON in `<tools>`, calls as `{name, arguments}` in `<tool_call>`,
  results in `<tool_response>`, a `<think>` block (possibly empty) opening every assistant turn. `agent/agent_runtime_helpers.py:91-191`.
  → A qualification arm (§5, "Ch"): the same PICK or FILL schema presented as the parameters of one forced function, only where the
  endpoint accepts a forced `tool_choice`.
- **H3 · The reasoning echo is a host table (ADAPT).** Kimi (matched by host: `api.kimi.com`, `moonshot.ai`, `moonshot.cn`), DeepSeek and
  MiMo require `reasoning_content` on every replayed assistant turn, padded with a single space because DeepSeek V4 rejects `""`;
  Mistral, Cerebras, Groq and SambaNova reject the key outright with 400/422. Aggregators re-exporting Kimi reject the echo.
  `agent/message_sanitization.py:573-701`; `tests/agent/test_message_sanitization_policy.py:140-265`. → Plotroom's PICK/FILL repair is a
  fresh user message quoting the failed answer as data, with no assistant replay; if a replay is ever kept, the profile carries
  `reasoning_echo: Require | Strip`, keyed by host.
- **H4 · Strict hosts reject unknown fields (ADOPT).** Responses-only fields are stripped for Chat Completions hosts; reasoning
  `extra_body` goes only to hosts known to accept it; `finish_reason` is normalised once at intake (Gemini's upper case, `MAX_TOKENS` →
  `length`). `agent/reasoning_params.py:88-121, 212-230`; `agent/message_sanitization.py:302-325`. → A typed serde request per wire
  dialect with no pass-through maps; a `FinishReason` enum with `Unknown(raw)` (AGENTS.md's permissive-parser rule).
- **H5 · Structured-output capability is per (host:port, model, format type) (ADAPT).** Rejections that name the capability are
  memoised and the field is dropped (not downgraded to `json_object`, which needs "JSON" in the prompt and returns empty content on some
  relays); invalid-schema 400s are retried once and never memoised. `agent/auxiliary_structured_output.py:1-111`;
  `agent/auxiliary_client.py:3362-3390`. → The qualification preflight sets the capability (doc 48 §2.3); a runtime rejection is a
  typed error that visibly moves that setup's FILL to the prompt-schema rung (F1), never a silent in-process memo.
- **H6 · Schema dialects (ADOPT, two layers).** Normalisers for Moonshot (every property typed, `anyOf` types on children, no null or
  `""` in enums, `required` everywhere), Gemini (key allowlist, stringified enums, inlined `$ref` with a 256-expansion budget), llama.cpp
  (no property-less objects, no type arrays), Anthropic (key regex), Fireworks (`default` beside `$ref`), Codex (no top-level
  combinators), xAI (no `/` in enum values). `agent/moonshot_schema.py:1-143`; `agent/gemini_schema.py`; `tools/schema_sanitizer.py`.
  → (a) Every shipped schema stays in the lowest common subset, checked in CI per dialect; (b) a pure per-dialect normaliser, with code
  validation re-checking whatever it stripped.
- **H7 · Grammar-compile failures are their own class (ADOPT the classification).** A 400 mentioning a grammar or a lookaround regex
  strips `pattern`/`format` and retries once; Qwen's "No user query found" means a poisoned transcript, not a grammar. `agent/
  error_classifier.py:857-868`. → For Plotroom's own schemas this should never fire; if it does, it is a qualification failure for that
  server build, logged with its version.
- **H8 · One effort ladder, per-wire vocabularies, a clamp that never escalates cost (ADOPT).** `none<minimal<low<medium<high<xhigh<
  max<ultra`; declared vendor overrides first (Kimi K3 `medium`→`high`); unset stays unset; Moonshot rejects toggle plus effort; DeepSeek
  needs the toggle on every request. `agent/reasoning_effort.py:18-150, 194-216`; `agent/reasoning_params.py:46-82`. → The level sent is
  recorded in the journal and the qualification record.
- **H9 · Mandatory-reasoning routes: step up, don't strip (ADOPT).** OpenRouter answers a disable request on such routes with 400;
  Hermes steps up to `low` and remembers the route, because dropping the field hands effort back to a higher provider default.
  `agent/auxiliary_reasoning_floor.py:1-30`. → Profile field `reasoning_off: Honoured | FloorAt(level)`; `max_tokens` then budgets
  thinking plus answer.
- **H10 · Where the answer lives (ADOPT).** Reasoning arrives as `reasoning`, `reasoning_content`, `reasoning_details[]`, typed
  `{type:thinking}` blocks, Mistral JSON arrays or inline tags (`think`, `thinking`, `reasoning`, `thought`, `REASONING_SCRATCHPAD`,
  MiniMax-M3's 思考/反思/推理/推敲). The stream scrubber strips closed pairs, holds partial tags across deltas and drops an unterminated
  block; `length` with only think content is "thinking budget exhausted". `agent/think_scrubber.py:18-187`; `tests/agent/
  test_think_scrubber.py` (19 cases). → A Rust response normaliser; `ThinkingExhausted` distinct from `Truncated`.
- **H11 · Reasoning-only stops (ADAPT narrowly).** When content is empty, `finish_reason=stop` and reasoning exists (vLLM's
  `nemotron_v3` parser files the whole answer as reasoning when the closing delimiter is missing), Hermes promotes it but never writes
  it into content. `agent/turn_final_response.py:87-115`. → One parse attempt of a schema-valid object from the reasoning tail, admitted
  only as `recovered_from_reasoning`, fully validated, counted and lowering the endpoint's rating.
- **H12 · The empty-response guard (ADOPT).** Two consecutive empties with usage proving zero output from the same (model, provider,
  finish_reason) are deterministic: stop retrying. `agent/empty_response_guard.py`; 35 test cases. → `EmptyDeterministic` is a counted
  outcome in the dependability rating; on a 50-a-day free tier every empty is a lost request.
- **H13 · A priority-ordered error classifier (ADOPT).** Upstream 429 (OpenRouter's "Provider returned error" with
  `metadata.provider_name`: the key is fine) versus account 429; free-tier gates ("not available on the free tier") versus capacity; Z.AI
  reuses 429 for overload; content-policy blocks are deterministic. `agent/error_classifier.py:34-172, 779-799, 1045-1069, 1474-1491`.
  → One provider `Error` enum with named fields (§4.7); upstream refusals do not count against the daily quota but do count against the
  endpoint's availability.
- **H14 · Rate-limit accounting (ADOPT).** Reads `x-ratelimit-*` and `Retry-After`; notes that one 429 fans out into up to 9 calls when
  SDK and harness both retry three times. `agent/rate_limit_tracker.py`; `agent/nous_rate_guard.py:1-7` (the fan-out note);
  `agent/retry_utils.py:20-27` (Z.AI's widening overload backoff). →
  SDK retries off; the harness owns every retry; per-account daily counters feed the quota preview (doc 48 §6.4).
- **H15 · A conservative repetition guard (ADOPT for creative text).** Runs only on 400+ characters; flags a repeated line covering half
  the text or a 60-character window recurring at least `max(5, ceil(n·0.5/60))` times; aborts a completed answer only at 16,000+
  characters with at most half the lines distinct. `agent/repetition_guard.py:15-156`; 8 tests. → A gate before admitting briefings and
  long FILL strings; short radio lines stay with doc 43's per-speaker lint.
- **H16 · Truncated structured output is refused (ADAPT).** Arguments not ending in `}` or `]` are truncated even when the router says
  `tool_calls`; retries with a boosted cap; a lossless repair ladder (control characters, trailing commas, misnested closers); `{}` when
  unrepairable. `agent/turn_tool_validation.py:143-189`; `agent/message_sanitization.py:157-284`. → One boosted retry; only lossless
  repairs, counted as `repaired_syntax`; **REJECT the `{}` fallback**, which would silently admit an empty FILL.
- **H17 · Unknown tool names (ADAPT).** Deterministic normalisation, a 0.7 fuzzy match, a terse catalogue-free error for blank or echoed
  names, three strikes. `agent/agent_runtime_helpers.py:2479-2526`; `agent/conversation_loop.py:931-1036`. → The normalisation maps an
  off-menu PICK answer for grading and telemetry only, never for admission; the terse, anti-priming error wording carries over to
  repair prompts.
- **H18 · Neutralising control tokens in untrusted text (ADOPT the technique, BUILD our own table).** Harmony tokens are rewritten with a
  fullwidth pipe after stripping Unicode Cf characters, idempotently; a token inside a JSON key is rejected, not rewritten.
  `agent/codex_responses_adapter.py:86-89, 164-200`; `tests/agent/test_codex_responses_adapter.py:191-243`. → Doc 21 §9.3 needs a
  multi-family table for mission text: ChatML, Hermes tags, DSML and DeepSeek sentence tokens (which already use `｜` and `▁`, so a
  fullwidth swap does not defang them [I]), Kimi, GLM, MiniMax, Mistral, Gemma. Applied only when rendering capsules; stored bytes stay
  unchanged.
- **H19 · Output leak scrub and leak assertions (ADOPT).** Leaked tool-call XML and GLM `<arg_key>` fragments are stripped; the live
  canary asserts that `LEAK_MARKERS` (`<think>`, DSML, `<|`, `<tool_call`, `"arguments"`, `<invoke`) never reach user-visible text; the
  vLLM `qwen3_xml` parser plus a reasoning parser leaks calls into text when streaming. `tests/e2e/core/live/_helpers.py:55-61`;
  `cli-config.yaml.example:99-108`. → A hard lint on creative text and a per-model leak rate; structured steps stay non-streaming.
- **H20 · Per-family prompt patches keyed on name substrings (ADAPT).** Tool-use enforcement and execution guidance blocks for gpt,
  gemini, gemma, glm, qwen, deepseek, kimi, minimax, mistral and others. `agent/prompt_builder.py:348-632`. → A D048 preset may select a
  preamble variant by id from the prompt pack the release ships (doc 55 §1.4: a harness preset carries no prompt text), only
  after it earns item-paired uplift (§5), keyed on exact model ids (the substring "gpt" also matches gpt-oss).
  Two FILL-relevant lines to test: "never repair identifiers" and "label assumptions".
- **H21 · Samplers deferred to the publisher (REJECT for PICK and FILL).** Temperature is sent only if set; local GGUF `general.sampling.*`
  keys become defaults; Kimi omits temperature. `agent/transports/chat_completions.py:344-357`; `hermes_cli/local_runtime/gguf.py:46-108`.
  → Doc 46 showed hidden defaults move results: preset samplers are tri-state `Pin(v) | Omit | ServerDefault`, and a GGUF whose sampling
  keys changed since qualification raises a warning.
- **H22 · Stale-stream timeout floors per family (ADAPT).** 600 s for Nemotron Ultra and Super on hosted NIM (60–180 s idle kills),
  DeepSeek R1/V4; 300 s for Lightning, Nano, MiniMax-M2; 180 s for qwen3; anchored slug matching. `agent/reasoning_timeouts.py:17-82`.
  → A qualified profile's timeout comes from its measured p90 latency; floors are defaults for unqualified models.
- **H23 · Cache-stable identity (ADOPT).** The builder declares the stable-prefix boundary; missing tool-call ids are derived by hash, never
  random; OpenRouter's top-level `session_id` keeps a session on one upstream. `agent/prompt_cache_boundary.py`;
  `plugins/model-providers/openrouter/__init__.py:39-43, 122-128`. → Send `session_id` = the run id (cache hits and screening
  reproducibility); every id in a prompt is deterministic.
- **H24 · Compaction and token estimates (REJECT compaction; ADOPT the estimator).** A byte-based estimate that counts CJK characters as
  about one token each and other text as UTF-8 bytes / 4, so Cyrillic is not undercounted. `agent/model_metadata.py:2320-2337`. → The
  budget ledger's pre-send check; workflows rebuild capsules instead of compacting (doc 21 §8.1).
- **H25 · A secrets-gated live canary and offline wire capture (ADOPT).** Nonce-valued synthetic tools, a per-test spend guard, slug
  resolution against the live catalogue, exact request-body capture, and a local server that always answers 418 to snapshot
  post-normalisation request bytes for free. `tests/e2e/core/live/_helpers.py`; `evals/gemini_type_array_probe.py`. → For
  `tools/local-qual` and a keyless CI test that snapshots each dialect's request for every shipped schema.
- **H26 · Free tiers (ADAPT).** Trusts the `:free` suffix; its default auxiliary model is `nvidia/nemotron-3-ultra-550b-a55b:free`; its
  fast tier excludes free models as "rate-limited and slowest". `agent/auxiliary_client.py:692-706, 956-959, 2271-2311`. → Verify a zero
  price from the catalogue (doc 48 §6.0 already does); offer free SKUs only for step kinds whose latency and availability qualified.
- **H27 · Strict role alternation (ADOPT as an invariant).** Adjacent same-role messages are merged and retried once for strict templates.
  `agent/message_sanitization.py:287-299`. → Every capsule is system (or developer) then strictly alternating turns ending on a user turn;
  a role-alternation error is a harness bug.
- **H28 · Porting its tests (ADAPT).** Suites with concrete known values: repetition guard (8), think scrubber (19), Moonshot schema (22),
  Gemini schema, schema sanitizer, structured-output rejection, echo policy, empty-response guard (35), effort clamp, timeout floors,
  argument repair, Harmony neutraliser, truncation boost. → Re-authored as Rust tests with the same inputs and Plotroom's expected
  outputs (for example `Err` where Hermes returns `{}`), citing file and test name; §6.1 item 7 asks where they are tracked.

Host and model quirks encoded in Hermes (condensed; each is a prior for the profile probe, not a fact about our endpoints):

| Family | Quirks (file:line at @04ea129) |
| --- | --- |
| DeepSeek | `json_schema` rejected first-party ("This response_format type is unavailable now"; `plugins/model-providers/deepseek/__init__.py:53`); toggle on every request plus `reasoning_effort` low/medium/high/max, `xhigh`→`max`; echo required, pad `" "`; V4 Pro returns typed thinking blocks; 600 s floor |
| Kimi / Moonshot | Omit temperature; toggle XOR effort; K3 levels low/high/max; relay default max; echo required by host; schema subset; `Accept-Encoding: gzip` (brotli SSE bug) (`plugins/model-providers/kimi-coding/__init__.py:12-67`) |
| GLM / Z.AI | 429 code 1305 is overload (widening backoff 30/60/90/120 s); tool calls sometimes arrive as plain text; `<arg_key>` leaks (`agent/error_classifier.py:153-164`) |
| MiniMax | Reasoning streams before content; CJK think tags; ignores the 1-hour cache tier on one route |
| Mistral, Cerebras, Groq, SambaNova | Strict: no `reasoning_content` key, no unknown tool-call fields (400/422); Mistral thinking may arrive as a JSON array |
| gpt-oss | Harmony tokens neutralised in untrusted text; leak pattern `to=functions.` |
| Nemotron | NIM idle kill; `nemotron_v3` files answers as reasoning without the closing delimiter; NIM payload cap 26,214,400 bytes |
| Qwen | 180 s floor; Alibaba routes cache 5 minutes only; streaming `qwen3_xml` leaks calls; "No user query found" is a transcript fault |
| Gemini, Gemma | Schema key allowlist; `thought_signature` kept for Gemini only; upper-case finish reasons via gateways |
| Local servers | llama.cpp needs `--jinja`; its schema converter rejects property-less objects, type arrays and lookaround; Ollama puts `<think>` in content and returns 400 on `reasoning_effort` for non-thinking pulls; LM Studio publishes allowed reasoning options per model |

### 3.2 BFCL harness (Berkeley Function Calling Leaderboard) @6ea5797

Paths are relative to `berkeley-function-call-leaderboard/`. Numbers come from the public files `data_overall.csv` and
`data_format_sensitivity.csv` (109 rows each, "Last Updated 2026-04-12", re-read 2026-09-28) and the prompt-variation post (2025-07-17).
On 2026-09-28, GitHub `main` had the same 29 files in `bfcl_eval/model_handler/local_inference/` (27 handler modules, the base
handler and `__init__.py`), so no local handler has been added since the pinned commit.

- **B1 · Format sensitivity is a small factorial (ADAPT as an "FS" arm).** Five axes: return format (Python list, fenced JSON list,
  verbose XML, concise XML), a `<TOOLCALL>` wrapper on or off, function docs as Python, XML or JSON, plaintext or markdown layout, and
  "classic" or paraphrased wording: 24 crossed cells plus 2 probes, each on 200 fixed items (a subset the post reports as strongly
  correlated with all 2,351). `bfcl_eval/constants/default_prompts.py:7-51`; `bfcl_eval/utils.py:881-964`; `bfcl_eval/eval_checker/
  eval_runner.py:395-498`. → Our own axes (§5.2): answer channel, answer wrapper, menu rendering, layout, paraphrased stem; one base
  cell plus one-change probes; max delta, SD and decode-failure share per cell.
- **B2 · One safe cell and one lethal cell for small models (ADOPT as a rendering rule).** A JSON answer with no wrapper tag and functions
  shown as JSON is best or within 3.5 points of best for 8 of 9 non-1B models checked (Gemma-3-4B 71.5, Gemma-3-12B 83.0, Phi-4 83.0,
  Qwen3-4B-2507 82.5 and MiniCPM3-4B 71.0 are best there). JSON inside `<TOOLCALL>` is lethal: Phi-4 1.5/4.0/11.0 against 79–83 untagged;
  Gemma-3-4B 6.0/16.0/9.5; Llama-3.1-8B 3.0/44.5/7.0. BFCL's default (a Python list) understates JSON-friendly small models (Phi-4 69.5
  against its best 83.0). Part of the tagged-JSON collapse may be parser strictness [I]. → PICK and FILL answers are one bare JSON
  object, never wrapped in custom tags or requested inside fences; menus and slot specs render as JSON by default; markdown layout is not
  assumed neutral below 8B (Gemma-3-4B falls from 62.0 to 41.5 with markdown).
- **B3 · A BFCL score is a score for model plus handler (ADOPT).** Each local model gets a hand-written adapter rendering its template as
  a raw string sent to the completions endpoint "for full control over the final formatted prompt". The renderings are near-native, not
  identical (the Qwen FC handler dumps raw BFCL docs with Gorilla types into `<tools>`); a Qwen3 template bug once affected the
  self-hosted Qwen3 rows (CHANGELOG #1068). `model_handler/local_inference/base_oss_handler.py:307-364`; `qwen_fc.py:143-151`. → The
  qualified artifact is the tuple (model file or endpoint, template id and hash, reasoning setting, stop set, sampler, channel), never a
  name. Golden-render tests compare our capsule with the model's own template output byte for byte.
- **B4 · FC versus prompt mode barely matters for Qwen3 on single calls (ADAPT).** Qwen3-30B-2507's 4.7-point FC advantage decomposes (V4
  weights 10/10/10/30/40) into multi-turn +1.95, agentic +2.59, irrelevance +0.51 and single-call AST −0.36: prompt mode wins non-live AST
  88.92 vs 85.77. MiniCPM3-4B with its native template gains +11.2 non-live and +22.1 live. `bfcl_eval/eval_checker/
  eval_runner_helper.py:436-519`. → A channel factor only for families whose trained call syntax is not JSON (MiniCPM, LFM2.5, Gemma 4,
  Mistral, Qwen3.5+ with `qwen3_coder`).
- **B5 · The DeepSeek "50 points" is confounded (ADOPT as an instrument rule).** `DeepSeek-V3.2-Exp-FC` maps to `deepseek-chat` with
  native tools and no thinking; `-thinking` maps to `deepseek-reasoner` in prompt mode with thinking. The 50.67-point non-live AST gap
  mixes call path and thinking; the FC row under-calls (parallel 15.0 vs 89.5; irrelevance 93.18 vs 67.0). `bfcl_eval/constants/
  model_config.py`; `model_handler/api_inference/deepseek.py:54-91`. → Every comparison changes one factor and records which; a
  two-factor comparison is labelled confounded (extends doc 48 §4.3). "No answer" is counted apart from "wrong answer".
- **B6 · Restraint scoring is lopsided, and a broken adapter looks perfectly restrained (ADOPT the mapping, REJECT the scoring).** An
  irrelevance item passes on a decode failure, empty output or truncation; irrelevance has 1,124 items, its complement (relevance) 16.
  Ministral-8B-2410 (FC) is the canary: 0% AST, 100% irrelevance. `eval_checker/eval_runner.py:263-316`. → PICK's X (none fits) and Q
  (ask) are explicit options; parse failures, empties and truncations are typed failures, never escapes; escape recall and false-escape
  rate are always reported as a pair; a 3–5 item canary with one planted escape halts a run on "all wrong plus all escape".
- **B7 · Off-domain restraint is easy (ADAPT).** BFCL's irrelevance items offer an unrelated function. Plotroom's failure mode is
  near-domain. → Stratify planted escapes (off-domain, near-miss option present, missing fact → Q) and grow the near-domain stratum first.
- **B8 · Published numbers are near-greedy single samples with a 4,096-token cap (ADAPT).** Temperature 0.001 for every model, no
  top_p/top_k/min_p; reasoning endpoints drop temperature; `ThinkAgentHandler` returns `""` when no `</think>` appears, so a truncated
  trace scores as restraint. `bfcl_eval/__main__.py:108-109`; `base_oss_handler.py:328-336`; `local_inference/think_agent.py:34-42`. The
  third-party Qwen-Agent no-think handler cannot be instantiated at this commit (constructor mismatch) [I from code]. → Qualify at the
  sampler we ship; one greedy arm only for comparison with BFCL; "truncated" (including an unclosed reasoning block) is its own error.
- **B9 · Reasoning handling is string surgery per family (ADOPT the fields).** Split at the last `</think>`; the local Qwen handlers never
  add the empty think block, so hybrid Qwen3 checkpoints ran with thinking on; DeepSeek's API rejects `reasoning_content` in history.
  `local_inference/qwen.py:106-197`; `api_inference/openai_completion.py:171-297`. → Profile fields `reasoning_disable`,
  `reasoning_strip`, `replay_in_history` (always never for our single-call steps). The thinking mode of individual Qwen3 rows stays [U]
  (latency is inconsistent: Qwen3-8B FC 51.36 s mean against Qwen3-14B FC 4.5 s).
- **B10 · System role and turn structure per family (ADOPT two flags).** Gemma 3 has no system role (folded into the first user turn);
  DeepSeek-R1 and Hammer turn system into user; `deepseek-reasoner` rejects consecutive user messages; Llama 3.1 wants tools in the first
  user turn; Mistral appends `[AVAILABLE_TOOLS]` before the last user message. `bfcl_eval/model_handler/utils.py:374-429`;
  `local_inference/gemma.py:29-69`. → `system_role: native | fold_into_first_user` and `alternation_required`; both in golden-render tests.
- **B11 · Schema lowering restates stripped keywords as prose (ADOPT).** For Gemini and Writer, `maximum`, `minItems`,
  `additionalProperties` and others are deleted and appended to the description ("Maximum value: 10."); dots in function names become
  underscores and are mapped back. `bfcl_eval/model_handler/utils.py:34-204`. → The per-provider normaliser (doc 48 §2.3) restates each
  stripped constraint in the field description; the code validator enforces the full original schema.
- **B12 · Parsers record how small models break their own formats (ADAPT; REJECT `eval`).** Missing close tags, unlisted parallel calls,
  schema echo instead of a call, `<|python_tag|>` prefixes, `;` separators, `parameters` for `arguments`, fences; several decoders call
  `eval()` on model text. `local_inference/phi_fc.py:161-227`; `llama_3_1.py:191-215`; `bfcl_eval/model_handler/utils.py:327-370`. → A
  closed normalisation list for no-schema channels (trim, one outer fence, text before the last reasoning tag), each application logged;
  everything else is a named finding, including a new "schema echo" finding; serde parsing only.
- **B13 · A typed AST error taxonomy with multi-answer ground truth (ADAPT).** `wrong_func_name`, `missing_required`, `type_error`,
  `value_error:string` and so on; each parameter's ground truth is a set of acceptable values. `eval_checker/ast_eval/ast_checker.py`. →
  FILL grading gets per-field acceptable sets and per-field error codes; REJECT BFCL's blanket punctuation and case folding, which would
  pass wrong catalogue ids.
- **B14 · No constrained decoding and no model repair (ADOPT the budget split).** No handler sets `response_format`, a grammar or
  `tool_choice=required`; only transport errors are retried. → Keep transport retries and model repair as separate budgets; BFCL's
  decoder-failure share is a floor our grammar mostly removes (doc 44: 0 parse failures in 1,216 constrained calls); the semantic
  value-error share is what transfers [I].
- **B15 · Special and stop tokens per model (ADAPT).** MiniCPM3 needs `skip_special_tokens=False` and stop ids `[2, 73440]`; GLM-4-9B its
  own stop set; the Mistral handler assumes the server stripped `[TOOL_CALLS]`. `local_inference/minicpm_fc.py:26-27`. → Profile fields
  `stop_tokens` and `keep_special_tokens`, used by the channel arm and any raw-completion path.
- **B16 · Most candidates' BFCL numbers come from harnesses outside the repo (ADOPT a provenance rule).** No handler exists for Qwen3.5,
  3.6, 3.8, Gemma 4, Granite 4.1/4.2, MiniCPM5, LFM2.5, Spark-X2.5, Ministral 3, gpt-oss or Nemotron 3; Liquid used "a custom Liquid
  handler"; several in-tree vendor handlers carry system prompts that coach restraint. → A BFCL figure enters a model table only with
  {handler, mode, thinking, sampler}; otherwise it is [V-vendor, method unknown] and never used to rank.
- **B17 · Evaluation hooks (ADOPT) and the agentic categories (REJECT).** Per-item prompt, tokens, latency and reasoning; re-run by id;
  a per-config CSV. The web-search, memory and executable multi-turn backends give the model capabilities Wilco must not have.
  `model_handler/base_handler.py:685-821`. → Records carry template id, capsule hash, error type and the factor changed; BFCL items are
  never imported (off-domain; the battery stays our own text).

Handler facts for the families that matter (all at T 0.001, raw completions, `max_tokens = min(4096, ctx − input − 2)`): Qwen3 FC uses
Hermes-style `<tools>` with raw BFCL docs and exact `<tool_call>\n…\n</tool_call>` extraction (malformed blocks silently dropped);
DashScope requires streaming and sets `enable_thinking=True`; Gemma 3 folds the system text into the first user turn; FunctionGemma has
its own escape DSL; Llama 3.2, 3.3 and 4 use the same pythonic prompt in "FC" and prompt mode; Phi-4-mini FC wants `<|tool|>` in the
system turn; MiniCPM3 renders tools as Python signatures; Ministral-8B-2410 runs through `MistralFCHandler` with `is_fc_model=False`
(the zeroed row); GLM-4.6 FC runs with thinking and no temperature; Kimi is plain OpenAI-compatible.

### 3.3 Terminus 2 (Harbor / Terminal-Bench) @3c82380

Terminus 2 never sends `response_format` or native tools: the envelope exists only in prose, and a tolerant parser reads the reply.
Vendors report their neutral agent scores in it (Qwen3.6, Qwen3.8, Qwen3-Coder-Next, three Gemini rows, three Nemotron rows, Granite
4.2, dots3, Kimi K2.6, GLM-5.3, MiniMax-M3). Probe cases J02–J20 (JSON parser), X02–X10 (XML parser) and S1/S3 (truncation) were
hand-written strings fed to `terminus_json_plain_parser.py` and `terminus_xml_plain_parser.py` by a local script; no model was run.

- **T1 · Two tiers of parse outcome (ADAPT).** `ParseResult` separates a blocking `error` from a non-blocking `warning` (text around the
  JSON, field order, a defaulted optional field, unknown keys). `terminus_json_plain_parser.py:13-20, 64-249`; `terminus_2.py:1479-1548`.
  → Admission returns `Admitted{value, deviations}` or `Rejected{finding, deviations}`; only a blocking finding spends repair budget. This
  matters only on the no-schema transport. It partly conflicts with doc 21 §8.2 ("schema violations are refused"), so §6.1 item 2 asks
  for the ignorable list; duplicate keys, non-finite numbers, out-of-range values and a second answer stay blocking.
- **T2 · Tolerating extra text is right; taking the first balanced object is wrong (ADAPT).** Prose or a fence around the envelope is
  admitted with warnings (J02, J03); with two envelopes the first runs with only an "extra text" warning (J07); an echoed format example
  before the real answer fails the turn (J15). `terminus_json_plain_parser.py:165-212`. → Scan all top-level JSON values, drop those
  failing the envelope shape, admit exactly one survivor; two or more is a blocking `AmbiguousAnswer`.
- **T3 · A short, brittle auto-fix ladder with one dead fix (ADAPT narrowly).** It appends `}` per unmatched `{` counted over raw text
  (strings included), then tries a two-level regex. A reply cut inside the commands array is not fixed (J05); a `{` inside a string
  overshoots (J06); single quotes and trailing commas are hard errors (J16, J17). The only XML fix waits for an error string no code path
  produces, so a missing `</response>` is accepted with no warning (X02). `terminus_json_plain_parser.py:29-348`;
  `terminus_xml_plain_parser.py:171-236`. → One string-aware, stack-driven closer, only on a stop-token end (never on a length stop),
  journalled as `auto_fixed` and never a first-pass success; every auto-fix ships with a test proving its trigger fires.
- **T4 · A generic repair turn with no cap (ADAPT the wording, REJECT the missing cap).** "Previous response had parsing errors: ERROR: …
  WARNINGS: … Please fix these issues" with a short content preview; `max_turns` defaults to 1,000,000. `terminus_2.py:424-440, 1479-1484`.
  → Plotroom keeps its one-finding repair (rule id, path, offending value, allowed values; doc 25 §7.2), adds a short excerpt around the
  JSON error position, never sends warnings in a repair turn, and keeps its R budget and repeat stops (a loop burns free quota).
- **T5 · Feedback after success (ADAPT for multi-turn only).** Warnings, including "AUTO-CORRECTED", are prefixed to the next
  observation. `terminus_2.py:1294-1300, 1540-1548`. → Only in chat, COMPOSE sessions and repair chains; for stateless steps the
  deviations feed the profile instead (per-run notes would break cache-stable prefixes).
- **T6 · Rules relax once the terminal action is chosen (ADAPT the relaxation, REJECT the self-confirmation).** With `task_complete` true,
  command errors become warnings (J11, X10); the model must confirm completion twice. `terminus_json_plain_parser.py:123-146`;
  `terminus_2.py:626-647`. → When an answer selects an escape (X, Q, keep default), the rest of the payload is ignored rather than
  validated; completion is decided by code (doc 21 §2, doc 38's completion gate).
- **T7 · Reasoning fields first, order checked but not enforced (ADOPT).** `analysis → plan → commands`; a wrong order only warns (J08).
  `terminus_json_plain_parser.py:357-398`. → Matches doc 25's `why` before `pick`; enforce it by marking every property required so the
  declared order survives constrained decoding; on the no-schema transport an answer-before-why reply is a recorded deviation.
- **T8 · Values Terminus handles silently (REJECT).** Duplicate keys: last wins, with no warning, so an injected second command list runs
  (J10); NaN accepted (J14); a duration of 1e9 clamped to 60 s without a record (J19); an unquoted XML attribute replaced by its default
  (X07). `terminus_json_plain_parser.py:90-92, 269-281`; `terminus_2.py:1305-1312`. → Refuse duplicates and non-finite numbers
  (serde_json rejects NaN by default); out-of-range numbers are findings with the allowed range, never clamps; J10, J14 and J19 become
  adversarial fixtures expecting refusal.
- **T9 · JSON versus XML is a per-model choice, and the gaps are large (ADAPT).** Qwen3-Coder-Next json 36.2 / xml 34.2; Kimi-K2.5 49.4 /
  38.8; DeepSeek-V3.2 39.3 / 34.8; GLM-4.7 37.1 / 44.9 (XML better); Claude Opus 4.5 57.3 / 58.4. Kimi K2.6 and dots3 report the JSON
  parser. The two parsers are not equally strict (a missing `<analysis>` warns in XML, X04; missing `analysis` errors in JSON, J09), so
  the gaps mix format and tolerance. → A preset field `envelope: json | tagged`, chosen per step kind on the no-schema rungs (doc 48 P2,
  F1); default JSON for PICK and FILL; measure a tagged raw-text body for creative text and SQF payloads, where JSON escaping stacks on
  SQF's doubled quotes; hold strictness equal across arms.
- **T10 · Terminus-2 scores are a prior for the no-schema path (ADOPT as a prior).** Nemotron-Terminal is trained in its JSON envelope
  and NVIDIA recommends evaluating it there; Granite 4.2 lists it among its training scaffolds. `terminus_2.py:1119-1136`. → Many free
  endpoints lack structured outputs (doc 48 §2.3), so the no-schema rung is live there; a "Terminus-shaped" prompt family (format block,
  filled example, field glossary, tolerance line) is one candidate on that rung. Never a qualification.
- **T11 · How the envelope is worded (ADAPT).** A filled example whose values are instructions, a required and optional field glossary
  with defaults, a tolerance line, an escaping reminder; the JSON example sets `"task_complete": true`, priming completion.
  `templates/terminus-json-plain.txt:1-54`. → The example must never contain a live option (a placeholder outside the menu, doc 25's
  position-bias rules); the format is restated at the end (doc 25 §4.4); tolerance is promised only for what we tolerate.
- **T12 · No system role (ADAPT).** The whole template goes in the first user message, which is always kept. `terminus_2.py:1728-1747`. →
  `system_role: native | fold_into_first_user`; the stable block leads, which is also the cacheable prefix.
- **T13 · Samplers: omitted since 2026-05-06 (ADAPT).** Harbor sends no temperature unless configured (Terminus 2 used 0.7 before);
  LiteLLM runs with `drop_params=True`, silently dropping unsupported parameters. `CHANGELOG.md:418-424`; `lite_llm.py:310-311`. →
  Always send an explicit sampler; the capability probe records dropped parameters. Terminus-2 rows from before May 2026 ran at T 0.7
  unless the vendor overrode it.
- **T14 · Reasoning carry-over and thinking switches are per model (ADAPT).** `interleaved_thinking` sends back the previous turn's
  reasoning; Kimi K2.6's score used "preserve thinking mode"; its instant mode needs `chat_template_kwargs {"thinking": false}`.
  `src/harbor/llms/chat.py:112-122`. → A profile fact `thinking_off` and a preset choice `carry_reasoning_in_repair` (in memory only,
  within one repair chain, for COMPOSE and creative text in thinking mode).
- **T15 · Context handling (REJECT model-written summaries and the 1M fallback; ADOPT the head-plus-tail cut).** Proactive compaction
  under 8,000 free tokens by three model calls; an unregistered model's context defaults to 1,000,000 tokens; tool output is cut to head
  plus tail at 10,000 bytes with an explicit omitted-bytes marker. `terminus_2.py:116-123, 655-1209`; `lite_llm.py:150-180`. → Digests are
  regenerated by code (doc 21 §8.1); an unknown window defaults to Plotroom's smallest supported window.
- **T16 · Truncated replies (REJECT salvage; ADOPT the wording).** The XML parser can execute a reply whose `</response>` closed before
  the cut, and cannot see a second complete block (S3); otherwise the next prompt says "NONE of the actions you just requested were
  performed because you exceeded {N} tokens". `terminus_xml_plain_parser.py:528-580`; `terminus_2.py:1211-1275`. → Never execute a reply
  that hit the length limit (doc 21 §8.2); `LengthLimit{cap}` for creative text; for PICK and FILL a length stop is counted in
  qualification; detect truncation from both `finish_reason` and a missing stop token.
- **T17 · Nested retries multiply calls (ADAPT).** LiteLLM retries three times, the agent three more: up to 9 calls per turn, 429s
  included. `lite_llm.py:257-404`; `terminus_2.py:1107-1118`. → One retry layer with typed classes (§4.7); a `Cancelled` user Stop is
  never retried.
- **T18 · Caching and sticky routing (ADAPT).** Cache breakpoints marked when the model name contains "anthropic" or "claude"; a session
  id sent as `extra_body` and `X-Session-ID`. `src/harbor/llms/utils.py:8-89`. → Breakpoints keyed by probed provider capability, not
  name substrings; a sticky key only where the provider documents affinity.
- **T19 · A scripted fake endpoint and golden trajectories (ADOPT).** Integration tests start a fake OpenAI-compatible server returning
  scripted replies (invalid, valid, complete) and compare id-normalised trajectories with golden files. `tests/integration/
  test_deterministic_terminus_2_invalid_json.py:33-322`. → Plotroom's harness tests use a scripted fake endpoint for repair, escapes,
  ambiguity, length stops and 429s, comparing canonical journals (doc 38 AT-W9); loopback only.
- **T20 · Fixtures to re-author (ADOPT).** The five trailing-newline cases generalise to "a per-item rule applies only to non-empty,
  non-final items"; the golden invalid-JSON case yields exactly one blocking finding plus two deviations; the probe set becomes adversarial
  fixtures with Plotroom's stricter expectations (J07, J10, J14, J19, S1, S3 refused). → Each cites harbor@3c82380, file and test.
- **T21 · Out of scope (REJECT).** The tmux keystroke tool, skills discovered with `find`/`cat`, MCP server listings in the prompt.
  `terminus_2.py:559-610, 1323-1353, 1713-1726`. → Wilco's generality comes from typed, undoable product commands.

### 3.4 Mellea (IBM Research) @1276bf6 with BeeAI RequirementAgent @08c1edf

IBM's recipe for small Granite models is "constrained decoding to guarantee schema correctness" plus instruct-validate-repair "via
rejection sampling strategies" plus task LoRA adapters (Granite Libraries blog, 2026-03-20). granite-io and granite-common were folded
into Mellea; granite-io was archived on 2026-06-30. The Granite 4.1 3B card itself names no harness and gives no sampler. `M:` is
Mellea, `B:` is `python/beeai_framework/` in BeeAI.

- **M1 · Budget definitions (ADOPT).** `loop_budget` counts generate-and-validate cycles per subsample (repairs = budget − 1);
  `concurrency_budget` counts parallel subsamples; no repair prompt is built on the last iteration; budgets are re-checked after a plugin
  changes them. `M:mellea/stdlib/sampling/base.py:113-156, 511-514`; `M:mellea/core/sampling.py:199-222`. → Plotroom's R maps to
  `loop_budget = R + 1`; the ledger reserves K × (R + 1) calls; a budget tightened to 0 goes to `on_fail`.
- **M2 · Parallel subsamples race; the first valid wins (REJECT the race).** The docstring admits the returned order "will no longer be
  deterministic". `M:mellea/stdlib/sampling/base.py:119-125, 267-355`. → K candidates may run concurrently but settle in index order;
  early stopping only by a deterministic rule (doc 40 R7).
- **M3 · Three repair strategies (ADAPT RepairTemplate as the default).** Rejection resends the same prompt; RepairTemplate rebuilds the
  instruction with the failed reasons in a tail block and does not show the failed answer, so the prefix stays identical; MultiTurn
  appends the answer and a user message. `M:mellea/stdlib/sampling/base.py:543-721`; `M:mellea/templates/prompts/default/
  Instruction.jinja2:40-44`. → For PICK and FILL: the same capsule, the repair at the tail after every cache breakpoint, replaced not
  accumulated, quoting only the offending value, one finding per turn; MultiTurn only for COMPOSE and creative text.
- **M4 · Repair wording (ADAPT).** ModelFriendly feedback turns each reason into `what failed + Try: <concrete fix>` ("Specific, Actionable,
  Concise"); a missing reason falls back to the requirement's description. `M:mellea/stdlib/sampling/feedback.py:11-110, 310-349`. → A
  typed `Finding {rule_id, field_path, offending_value, why, allowed_values}` rendered by one template per UI language, ending with a
  code-computed imperative ("Choose one of: B, D, F"); REJECT regex parsing of reason strings.
- **M5 · What is returned when every attempt fails (ADAPT).** Strategies return index 0 or the last attempt; SOFAI picks the attempt with
  most requirements passed; the failed output is `.value` with `success=False` beside it. `M:mellea/core/sampling.py:41-101`. → A
  deterministic "closest candidate" (fewest error findings, then warnings, then latest) offered only as a card under `on_fail`; REJECT
  returning a failed value as the result (a caller ignoring `.success` consumes it; doc 38's Binding has no raw-text variant).
- **M6 · Three validation outcomes (ADOPT).** Pass, fail with reason, or unparsable (always a failure; a judge's parse error never becomes
  repair text); `check_only` requirements stay out of the prompt. `M:mellea/core/requirement.py:34-123`. → `CheckOutcome {Pass,
  Fail(Finding), Unparsable, NotRun}`; a per-check `stated` flag (state length caps and allowed speakers; keep catalogue and geography
  checks check-only); the stated set is part of the capsule hash.
- **M7 · An LLM judge by default (REJECT as a gate).** A plain requirement without a validator goes to a judge, on Granite automatically
  to a requirement-check LoRA. `M:mellea/core/requirement.py:369-460`. → Every acceptance check is code (doc 21 §1.4); a judge may only
  order already-checked creative candidates.
- **M8 · Majority voting (ADAPT for PICK only).** MBRD over 8 concurrent samples with ROUGE-L for text; "weighted" voting is a stub
  (weights 1.0); `format` is not passed to inner samples and failed samples still vote.
  `M:mellea/stdlib/sampling/majority_voting.py:62-249`. → Admit before voting; identity of the chosen canonical option after un-permuting;
  weight by option probability where logprobs exist; stop at decisive agreement; show both options on a tie. REJECT ROUGE-L MBRD for
  creative text (it selects the blandest candidate); a regression test that the schema reaches every sample.
- **M9 · Budget forcing (ADAPT narrowly).** s1-style: cap the think block, optionally force more with "Wait", close `</think>`, then
  answer; Ollama-only, and the schema is passed during thinking too. `M:mellea/stdlib/sampling/budget_forcing.py`. → Only as an optional
  local feature if a thinking arm ever qualifies: a hard think cap and forced close with the grammar starting after the close token;
  REJECT "Wait" forcing.
- **M10 · SOFAI escalation (ADOPT the stop rule; REJECT automatic escalation).** A fast solver loops with feedback and stops early when the
  failure set equals the previous attempt's; a slow solver gets one attempt as fresh start, continued chat or best attempt.
  `M:mellea/stdlib/sampling/sofai.py:45-110, 745-859`. → "No improvement" by typed Finding equality (doc 25 §7.2); the best-attempt
  package becomes the payload of the visible "retry with another setup (cost shown)" button (doc 25 §10.2); no silent model switch.
- **M11 · Presets (ADOPT the shape).** Requirements, strategy and feedback bundled per use case. `M:mellea/stdlib/sampling/presets.py`. →
  Already Plotroom's per-DecisionKind binding (doc 38 §3.3); REJECT the code-executing presets.
- **M12 · Logprob soft scores (ADOPT for PICK).** Granite's TokenToFloat reads the first token of a categorical JSON value and its
  top_logprobs, maps alternatives to categories and normalises. `M:mellea/formatters/granite/intrinsics/output.py:294-432`. → A PICK
  margin from letter probabilities at the `pick` field; possibly replacing K = 3 with one calibrated call; record logprob support per
  endpoint and check that A–G are single tokens per tokenizer.
- **M13 · Sentence markers for grounded citation (ADAPT).** Sentences are numbered `<c0>`, `<c1>`… so the model cites ids instead of
  copying text. `M:mellea/formatters/granite/intrinsics/input.py:171-237`. → For S0 Describe (doc 25 §7.1): number the brief's sentences
  and let FILL cite them through an enum of valid ids; spans decoded by code; valid by construction.
- **M14 · Prompt layouts per model family (ADAPT).** Templates chosen by substring directory names; Granite's layout puts grounding facts
  before the task. `M:mellea/formatters/template_formatter.py:195-361`. → A qualified, versioned layout variant selected by an explicit
  preset key; REJECT substring matching; the static prefix stays byte-stable.
- **M15 · One thinking switch mapped per server (ADOPT).** `enable_thinking=false` for vLLM plus `reasoning_effort:"none"` for Ollama's
  `/v1` (not sent to api.openai.com, which rejects it); Granite 4.2 on Ollama thinks unless told `none`. `M:mellea/backends/
  model_options.py:55-89`. → `ReasoningControl` per endpoint; preflight asserts zero reasoning tokens when off.
- **M16 · Reasoning replay only after tool calls (ADOPT).** `M:mellea/helpers/openai_compatible_helpers.py:322-355`. → PICK and FILL
  repairs never replay reasoning.
- **M17 · Schema passing per backend (ADAPT).** Ollama `format=`, OpenAI-compatible strict always (root `additionalProperties` patched
  only for api.openai.com), vLLM `structured_outputs` or `guided_json` by version probe; LiteLLM's `drop_params=True` silently drops
  unsupported parameters. `M:mellea/backends/openai.py:1398-1428`; `M:mellea/backends/litellm.py:273-343`. → Schemas strict-compatible
  at every level; a per-endpoint `SchemaMode` learned by live preflight; REJECT silent drops and hostname sniffing.
- **M18 · Schema and tools never share a request (ADOPT).** Both backends drop tools when a format is given. → PICK and FILL are
  schema-only; tool rounds for COMPOSE come first, then one schema-constrained call.
- **M19 · Tool calling emulated through structured output (ADOPT).** BeeAI sends a union schema of allowed tools (`{name: const,
  parameters}`) when a provider lacks tool calling or the needed `tool_choice`; OpenAI and Bedrock need the union wrapped in an object.
  `B:backend/chat.py:453-502, 797-820`; `B:backend/utils.py:125-218`. → For COMPOSE tool selection: a code-built PICK over tool names then
  a FILL of arguments, with unions always wrapped.
- **M20 · Transport errors kept apart (ADOPT).** Typed errors for empty responses, wrong or unknown tools; Ollama's empty "done" during a
  model load; Ollama's default `num_ctx` of 2048 silently truncates. `B:backend/chat.py:625-626, 864-957`; `M:mellea/backends/
  context_lengths.py:48-55`. → §4.7's taxonomy; always send `num_ctx` to Ollama.
- **M21 · ConditionalRequirement (ADOPT the idea).** Per-tool rules (`force_at_step`, `only_before`, `max_invocations`,
  `consecutive_allowed`…), validated at construction; each step yields `{allowed, forced, hidden, prevent_stop}`.
  `B:agents/requirement/requirements/conditional.py:28-199`. → A declarative tool-constraint table in workflow TOML for COMPOSE steps,
  validated at load time; REJECT callable `custom_checks` in packs.
- **M22 · Rules combine as a conservative meet (ADOPT).** Any disallow wins; an empty allowed set is a hard error naming the rules.
  `B:agents/requirement/utils/_llm.py:64-168`. → Matches doc 38 §7's lattice; add the empty-set error and lattice unit tests.
- **M23 · Allow-lists and dates in the system prompt break caching (REJECT).** BeeAI lists every tool with "Allowed: True/False" plus
  today's date, and moves its cache breakpoint past the system message. `B:agents/requirement/prompts.py:42-95`;
  `B:agents/requirement/_runner.py:136-172`. → Byte-stable system prefix; the step's subset only in the tail.
- **M24 · Lenient recovery (REJECT).** BeeAI turns plain text into a final answer, "fixes" broken arguments and drops all requirements to
  force an answer; Mellea coerces tool argument types. `B:agents/requirement/_runner.py:174-306`. → Malformed replies are findings.
- **M25 · IBM's default harness for small Granite as a baseline arm (ADAPT).** Mellea defaults to Ollama with Granite 4.2 3B and
  `RejectionSamplingStrategy(loop_budget=2)` (one blind retry); BeeAI defaults to T 0; the backend pulls models automatically.
  `M:mellea/stdlib/session.py:271, 874`. → A vendor-recipe arm for the Granite rows (K = 1, one blind retry, T 0) that Plotroom's
  one-finding repair and K = 3 vote must beat; REJECT the automatic pull (downloads are user-started).

Further Mellea and BeeAI lessons (streaming validation cancelling generation at the first failed chunk for monotone code checks; typed
plugin hooks with allow-listed writable fields, where packs may only add findings or lower budgets; a cycle checker flagging the same
call repeated; a pinned-prefix chat window instead of model summaries; one registry of output contracts checked for exhaustiveness at
build time; a model catalogue whose routes each need their own qualification) are folded into §3.10 and §6.

### 3.5 Mistral Vibe harness core @7c19608

Crate `mistralai-unified-harness` (`harness/core/`, Rust edition 2024, `publish = false`, cdylib and rlib; 397 tests in `src/`), plus
the Mistral adapters in `vibe/core/llm/backend/mistral.py` and the Python runtime. Apache-2.0 ("Copyright 2025 Mistral AI"); no NOTICE
file at this commit. The harness spec, its docs and the checkpoint fixture JSON the code refers to are not in the public tree.

- **V1 · A sans-IO reducer with a transactional apply (ADOPT).** The Core is a pure function of (state, command, determinism) returning
  actions, typed observations and at most one turn completion; the session applies each command to a clone and swaps it in only on
  success, so a rejected command leaves no partial mutation. `harness/core/src/core/session.rs:61-72, 228-284`;
  `src/core/step_protocol/mod.rs:37-206`. → The workflow runtime of doc 38 §4.7 as a reducer: `apply(RunInput) -> Accepted{transition} |
  Rejected{rejection}`; model calls, card answers and command-bus commits become effects and results; the mission document still changes
  only through undoable commands.
- **V2 · Injected determinism, checked by contract tests (ADOPT).** Every input carries `{time_unix_ms, random_seed}`; the Core never reads
  a clock or an RNG; `contract.rs` tests properties (equal state plus equal input gives an equal transition; a terminal turn emits no
  actions). `src/core/step_protocol/determinism.rs:1-7`; `src/core/contract.rs:1-110`. → Contract tests for the workflow runtime, as
  proof artifacts under AGENTS.md's test-first rule.
- **V3 · Idempotent, ordered input delivery (ADAPT).** Same input id with identical canonical bytes replays the stored transition;
  different bytes is a conflict; lower ids are stale, gaps out of order; ids bounded to 2^53−1 for JSON round-trips; pending effects are
  Dispatch, Keep or Refresh. `src/core/session/delivery.rs:18, 82-141, 315-347`. → One-shot card tokens (doc 38 §4.1), plugin tool
  results and MCP `decide` calls use "same key, same bytes: replay; same key, different bytes: conflict".
- **V4 · Invalid states unrepresentable; pending work derived (ADOPT).** `TurnState` is `Idle | Compacting | Active | Terminal` with four
  `Awaiting*` phases (it replaced a phase enum beside five Options); a queued follow-up lives inside the active turn, so a failed turn
  discards it (a regression test covers the former wedge bug); `pending_actions()` is computed, never stored. `src/core/state.rs:187-652`;
  `src/core/turn.rs:1219-1258`. → Plotroom's `RunState` and `StepStatus` follow the same rules (AGENTS.md typestate).
- **V5 · State kept apart from what the model sees (ADAPT).** Stored messages carry a source and private metadata; a projection strips
  hidden fields and emits an append delta or a full replace; the model-input revision is disposable bookkeeping whose `PartialEq` is
  always true. `src/core/model_input_projection.rs:11-57`; `src/core/state.rs:60-72`. → A projection from typed run state to capsule
  segments carrying their trust labels (doc 21 §9); a stable-prefix revision counter lets the ledger predict cache breaks (doc 40 §4.1).
- **V6 · The cache-stable prefix is a tested property (ADOPT).** Generic rules, then product instructions, then per-user catalogues sorted
  and escaped; a test builds prompts for two users and asserts identical bytes up to the end of the product instructions; no wall clock
  in the prompt; prompt changes only at quiescent points. `src/core/prompt/system.rs:8-48, 240-279`. → For every step kind, a test
  rendering two capsules that differ only in per-run data and asserting a byte-identical prefix up to the declared breakpoint.
- **V7 · Schema lowering (ADOPT).** schemars draft-07 with inlined subschemas, then a normaliser (titles stripped, numeric formats
  dropped, closed objects given empty `properties`, harness markers for non-null and one-of). `src/core/tools/schema.rs:8-92`. → One
  canonical schemars schema lowered per provider dialect, with golden tests (doc 48 §2.3).
- **V8 · Argument validation fails into the model's context (ADAPT).** Arguments are validated before any effect; invalid calls become
  model-visible failures while valid calls in the batch still run, committed in call order; malformed JSON is kept as data with its raw
  bytes. Weakness: only the validator's first error, no JSON pointer, no allowed values, validator compiled per call.
  `src/core/tools/resolved/contracts.rs:154-168`; `src/core/wire/message.rs:12-17, 247-274`. → Keep validate-before-effect and raw bytes
  in the journal; improve feedback to doc 25 §7.2's standard; compile validators once at load.
- **V9 · Completion admission checks finish reasons and usage (ADOPT).** Rejects empty results, empty or duplicate tool-call ids, a
  `tool_call` finish without a call, and usage where total ≠ input + output or cached > input; repair is Retry (the draft is dropped, the
  feedback injected) or Reject, bounded and transactional. `src/core/turn/completion/candidate.rs:260-583`. → `Truncated` as a typed
  finding distinct from a JSON error; usage validated before the ledger trusts it.
- **V10 · Role alternation: a correction (ADAPT).** Vibe 2.10.0 (2026-05-19) dropped consecutive-user-message merging; the Core's retry
  and compaction emit adjacent user messages; the Mistral adapters send them unmerged. The hosted API therefore accepts consecutive user
  messages as Vibe uses it, while Mistral's Hugging Face template raises on them (discussion #13). `CHANGELOG.md:1101`;
  `src/core/features/compaction/context.rs:146-170`. → Every PICK and FILL repair is a fresh single-turn capsule (system, then one user
  message with the task, the offending value and one finding), safe under any template; `role_alternation` is a profile field checked
  against the GGUF's embedded template locally.
- **V11 · A conservative budget estimate corrected by measurement (ADOPT).** Serialised bytes / 4, raised to the provider-reported total of
  the last completion; infeasible configurations refused; a compaction call skipped when even a one-character summary cannot fit.
  `src/core/model_input_budget.rs:12-40`; `src/core/features/compaction/execution.rs:184-380`. → The ledger corrects byte estimates
  upward per model setup (Czech, Polish, Russian and SQF undercount at 4 bytes per token); the definition compiler rejects a step whose
  fixed capsule cannot fit the smallest context among its qualified models.
- **V12 · Compaction mechanics (ADAPT for chat and EXPLAIN only).** Oldest history dropped by binary search, tool call and result
  removed together, the latest user message protected, a `<summary>` reply with typed rejections and one retry, a cheap summariser at T 0.2
  with reasoning off. → Workflows never compact (doc 21 §8.1); a domain-specific summary prompt of our own.
- **V13 · An error taxonomy that separates caller errors from harness bugs (ADAPT).** `InvalidState`, `InvalidCorrelation`,
  `InvalidCommand`, `InvalidConfiguration{field}` and `Invariant` ("a Core bug … rather than blamed on the caller"); a Python store error
  for "requires newer reader". `src/core/error.rs:3-98`. → Keep the split inside each crate's single `Error` enum with structured fields
  (reject the stringly `code`/`details`); a `HarnessBug` class the UI reports as a bug, never as "model failed"; `NeedsNewerReader` for
  sidecars.
- **V14 · A versioned checkpoint with a strict semantic boundary (ADOPT).** Only semantic state is persisted (never configuration, the
  generated system prompt, derivable ids or transport caches); invariants validated on capture and restore; the version probed before
  parsing; owned leaves `deny_unknown_fields`, open payloads permissive. `src/core/checkpoint/v1/mod.rs:31-293`. → The run journal and
  campaign sidecar: persist decisions and admitted values, capsule hashes only; recompute derived keys on load and check them.
- **V15 · Checkpoint fixture families (ADOPT).** Schema, invariant and semantic tests; one golden JSON per reachable state regenerated by an
  environment variable, with an inventory check, byte-equal round trips and a `CONFIG_SECRET` sentinel proving configuration never leaks.
  `src/core/checkpoint/fixture_tests.rs:14-140`. → One committed fixture per `RunState`, `StepStatus` and campaign stage, plus a sentinel
  test (no key, rendered capsule or absolute path); unlike Vibe, commit the fixtures so CI works from a fresh clone.
- **V16 · A digest-chained recovery journal with divergence reports (ADOPT).** Canonical JSONL with per-record SHA-256 and the previous
  hash; a torn final line tolerated; replay compares transition digests and reports the first differing sequence number and a shape diff.
  `harness/runtimes/python/.../vibe/_storage.py:87-174, 3175-3204, 3763-3798`. → Doc 38's journal and its crash-at-every-entry test, with
  "Stale: step X" reports naming the first differing key and field.
- **V17 · Tests need no fake model: the model's answer is a command (ADOPT).** Helpers drive the shipped path; `advance_llm` turns a
  scripted message into `CompletionSucceeded`; 131 acceptance tests assert every observation and restart from checkpoints mid-scenario;
  one canonical snapshot of the first request. `src/core/testing.rs:1-483`; `tests/acceptance_scenarios/runtime_driver.rs:298-523`. →
  Scripted command sequences and cassettes feed the same admission path; one golden first capsule per step kind.
- **V18 · Deterministic, domain-separated ids (ADOPT).** UUIDv5 over a versioned domain, a kind and length-prefixed parts; a test proves
  `("a","b:c")` and `("a:b","c")` differ. `src/core/action_id.rs:1-82`. → Doc 38 §4.5's item seeds and journal keys length-prefix every
  part and carry a domain tag; add an aliasing property test.
- **V19 · Discarded work carries a typed cause (ADOPT).** `CandidateDiscarded{cause: Failure|Skipped|Retry|Rejected|Steer|Interrupt}` and
  `ActionAbandoned{cause}`. `src/core/step_protocol/observation.rs:113-245`. → `Discarded` and `Abandoned` journal records for the
  inspector's "why" panel and honest first-pass metrics.
- **V20 · Input admitted only at model-valid boundaries (ADAPT).** Steering waits until an assistant message or all tool results are
  committed, so a user message never lands between a call and its result. `src/core/state.rs:421-521`. → For COMPOSE tool steps and chat.
- **V21 · Mistral's own small-model classifier is a PICK template (ADOPT the pattern, REJECT the domain).** `mistral-small-latest` at T 0
  with thinking off regardless of the session (a 2.25.x fix: a thinking session had leaked into it); context stripped to the request;
  prompt-only JSON with fences stripped, **no `response_format`**; enums normalised, off-contract values become None; code re-derives the
  verdict; fail closed; the prompt version is `sha256(prompt)[:12]`. `harness/runtimes/python/.../vibe/_smart_approve.py`. → Pin sampler
  and reasoning per step kind, independent of the chat session's effort dial; a content-hash template version in the journal and
  cassette key. Mistral's own harness does not rely on constrained decoding here.
- **V22 · Mistral wire quirks (ADOPT in the Mistral profile).** Reasoning map low→`none`, medium/high/max→`high`, "off" omits the field;
  a reasoning reply streams list-form content mixing thinking and text chunks and can switch forms mid-stream; thinking replayed only
  when on; `parallel_tool_calls=true` whenever tools are sent; an empty streamed reply becomes `" "` while a non-streamed one raises;
  429/5xx backoff 0.5 s × 1.5 to 30 s. `vibe/core/llm/backend/mistral.py:76-490`; `CHANGELOG.md:603, 914, 1531`. → Send
  `reasoning_effort: "none"` explicitly; parse both content forms; parallel calls off for bounded steps; an empty reply is a typed
  `Empty` finding.
- **V23 · Prompt caching left off (ADAPT doc 40 R10).** Vibe sends `x-affinity: <session_id>` and reads `cached_tokens`, but never sends
  `prompt_cache_key`, which Mistral's docs make the switch for caching (a community request, discussion #680, had no reply).
  `harness/runtimes/python/.../vibe/_runtime_config.py:197-263`. → Always send `prompt_cache_key` on Mistral; log `cached_tokens` per
  call during screening.
- **V24 · Harness-overhead benchmarks kept apart from model evaluation (ADOPT small).** Feature-gated binaries report median and p95 of
  create, checkpoint, restore and tool ranking with an order-of-magnitude flag. `src/benchmark.rs:18-109`. → A bench for menu
  computation, capsule rendering, admission and journal replay per step kind, so "slow" is attributed correctly.
- **V25 · Progressive tool discovery (REJECT).** The model browses a tool catalogue. → Code computes menus (doc 21 §3.2); the plugin grant
  fixes the tool set (doc 22).
- **V26 · Defaults by role (ADAPT).** Main agent `mistral-medium-3.5` on the product endpoint `mistral-vibe-cli-latest` (T 1.0, thinking
  high; the `devstral-2` alias was migrated to it in 2.10.0); compaction and the classifier on `mistral-small-latest`. Cards: Ministral 3
  below T 0.1; Small 4 `none` at T 0.0–0.7; Devstral 2 T 0.15. `vibe/core/config/vibe_schema.py:128-151`;
  `vibe/core/config/_migration.py:114-198`. → Card values as starting points for qualification; "best in Vibe" means a coding agent on a
  vendor endpoint with thinking on, not our PICK or FILL.
- **V27 · Study it, never depend on it (REJECT as a dependency).** In the in-scope production files: 17 `.expect()`, 9 `.unwrap()`, 6
  `unreachable!` and direct slicing (`model_context.rs:112`, `compaction/context.rs:259, 368-446`); string errors; not a published
  crate. → Re-implement ideas; a ported snippet would carry the Apache-2.0 licence text, the copyright line and a change note (doc 02);
  no "Vibe" or "Mistral" in our names.

### 3.6 ZCode (Z.ai) @29628c9 with Kimi Code's kosong @be7d5f5

Read: ZCode's rules file (`config/provider/zcode-builtin.json`: 6,212 lines, 20 templates, 8 account providers, 84 model rules, 72
model-by-API rules, 52 site rules), `packages/model-option-map`, `packages/provider`, the CLI's model adapter layer; kosong's capability,
catalogue, error, provider and schema modules. The Electron app and the CLI tools were skipped. `K:` prefixes kosong paths
(`packages/kosong/src/`).

- **Z1 · Capabilities as a layered cascade of data rules (ADAPT).** Model regex → model × API type → model × API type × base URL →
  template → built-in provider → the user's exact rule; later layers win; `undefined` inherits, `null` clears; model patterns anchored and
  case-insensitive; base URLs normalised; users may add only exact rules. `config/provider/zcode-builtin.json:6, 865, 2484, 3287, 4316,
  6026`; `packages/provider/src/config/model-config.ts:379-559`. → The layering of Plotroom's profiles (§4.2): family defaults → model ×
  wire → model × wire × endpoint → qualification overrides → the user's exact override; TOML read with `deny_unknown_fields`.
- **Z2 · A model runs only when its config is complete (ADOPT).** Missing leaves list the model with typed issues but make it
  non-executable. `packages/provider/src/resolver.ts:256-324`. → A builder yields a `QualifiedAdapter` only when every field its step
  kind needs is present; the Model Manager lists the missing fields.
- **Z3 · "Unknown" is not "no" (ADOPT the tri-state).** kosong returns a detectable frozen `UNKNOWN_CAPABILITY`; ZCode puts safe defaults
  on its `.*` rule, which makes an unprobed false look like a measured false. `K:capability.ts:8-73`; `config/provider/
  zcode-builtin.json:866-900`. → `Unprobed | Yes{evidence} | No{evidence}` with the canary run id and date.
- **Z4 · An option-map DSL (ADAPT the principles, REJECT the string DSL).** A restricted expression language compiled once, pure, returning
  JSON merge patches applied at the final serialisation step with path-ownership conflict detection; non-JSON bodies fail closed; the
  patched body is captured. `packages/model-option-map/src/*`; `apps/zcode-cli/packages/adapters/src/model/model-option-map-fetch.ts`.
  → One owner per wire field, conflict detection, fail closed, body captured; in Rust a closed enum of encodings is enough.
- **Z5 · A counter-example (REJECT).** The generic Chat Completions map sends `thinking.type`, `enable_thinking`, `reasoning_effort` and
  `reasoning.effort` together; GLM-5.3 on Z.ai's standard OpenAI-compatible API falls through to it. `config/provider/
  zcode-builtin.json:2508-2520`. → Exactly one reasoning encoding per profile, chosen by the probe, which tries candidates one per request.
- **Z6 · Z.ai's own harness distrusts first-party `json_schema` (ADOPT as corroboration).** False by default and for GLM-5.x, Kimi,
  MiniMax and DeepSeek first-party; true for the same weights on other routes (DeepSeek V4.1 Flash on OpenRouter; GLM-5.3, Kimi K3 and
  DeepSeek at OpenCode Go; DeepSeek first-party on the Responses API). A request carrying a schema to an endpoint flagged false fails
  locally and non-retryably, with no silent fallback; the core agent loop never uses `responseJsonSchema`.
  `apps/zcode-cli/packages/adapters/src/model/model.ts:155-195`. → Per-endpoint canaries; where the canary says no, a visible and labelled
  fallback (json_object where offered, the schema in the prompt, the validator and repair loop).
- **Z7 · Several candidates cannot turn thinking off (ADOPT).** GLM-5.3 and 5.3-Flash low/high/max only; Kimi K3 low/high/max; K2.7-code
  `enabled` only; kosong derives `offEffort` and `alwaysThinking`; gpt-5-class models reject `none`; Gemini 3's floor still reasons.
  Another harness sent `disabled` to glm-5.3 and the reasoning leaked into content (earendil-works/pi #8706).
  `K:catalog.ts:73-95, 361-436`; ZCode's GLM-5.3 rule `config/provider/zcode-builtin.json:978-994`. → `thinking_off:
  Supported{encoding} | Unsupported{floor}`; on Unsupported endpoints PICK and FILL run
  at the floor with a reasoning-sized cap, reasoning tokens in the ledger and a leak check.
- **Z8 · Levels ordered weakest first (ADOPT).** The first value is the lowest public level; auxiliary calls take it with at most 5,000
  output tokens; ZCode refuses to infer behaviour from level names; out-of-spec levels and caps fail locally. `packages/shared/src/
  model-config.ts:21-35`; `apps/zcode-cli/packages/core/src/model/auxiliary-model-options.ts:3-14`. → A newtype index into the profile's
  ordered level list, validated at construction.
- **Z9 · Output caps and reasoning share one budget (ADOPT).** On Moonshot reasoning models `max_tokens` also covers reasoning, so a small
  cap returns HTTP 200 with no content; kosong prefers `max_completion_tokens` and raises a retryable empty-response error for think-only
  output; caps and field names vary by route (MiniMax-M3 32,000 first-party, 131,072 at OpenCode Go). `K:providers/kimi.ts:56-75,
  525-537, 613-626`; `K:generate.ts:215-245`. → Separate `EmptyOutput` (retry once), `ReasoningExhaustedCap` (larger cap or lower level,
  never the same request) and `Filtered` (no retry); the cap field name is a profile value.
- **Z10 · No standard field carries reasoning (ADOPT the scan, ADAPT the echo).** `reasoning_content` (DeepSeek, Moonshot, most gateways),
  `reasoning_details` (OpenRouter), `reasoning` (gpt-oss guidance, newer vLLM, whose request side accepts only it); kosong scans all
  three and echoes back the key each endpoint used. `K:providers/reasoning-key.ts:1-89`. → Scan all three on intake for thinking counts
  and leak checks; the outgoing key is pinned by qualification, not learned at run time.
- **Z11 · Merge consecutive user turns only at a strict provider's boundary (ADOPT).** Merged for Anthropic and Gemini, left alone
  elsewhere; structural 400s trigger one strict re-projection. `K:providers/merge-user-messages.ts:1-64`; `K:errors.ts:500-587`. → Profile
  flag `role_alternation: Strict | Lenient`; the inspector shows the real steps.
- **Z12 · One leading system message where templates require it (ADOPT).** Several system blocks kept internally for cache boundaries,
  concatenated in order for OpenAI-compatible providers, keeping the last block's cache marker; mid-conversation system only where
  flagged. `apps/zcode-cli/packages/adapters/src/model/system-message-compat.ts:6-36`. → Assemble the cache-stable prefix from blocks;
  emit one system message where the template needs it; byte order preserved.
- **Z13 · Schema normalisation per dialect, folding constraints into descriptions (ADOPT).** ZCode's strict converter drops unsupported
  keywords into the description and sends shapes it cannot express without `strict`; Kimi K3's Anthropic endpoint allows `$ref` only under
  `#/$defs/`; kosong inlines local refs, types enum-only properties and rejects mixed-type enums. `apps/zcode-cli/packages/adapters/src/
  model/strict-tool-schema.ts:1-132`; `K:providers/kimi-schema.ts:110-398`. → Generate the portable subset by construction (no refs,
  explicit types, single-type enums, closed objects, all required) and property-test every PICK and FILL schema through each dialect.
- **Z14 · Vendor extension fields off by default (ADOPT).** ZCode disables Anthropic's `eager_input_streaming` because "several
  Anthropic-compatible gateways reject that extra tool field"; strict schemas only for first-party ids; Kimi tool-call ids sanitised to
  64 characters. `apps/zcode-cli/packages/adapters/src/model/tool-transform.ts:225-243`; `K:providers/tool-call-id.ts:8-56`. → Every
  optional field gated by a profile flag, with golden wire tests per profile.
- **Z15 · An error taxonomy with vendor business codes (ADOPT).** Ordered classification ending in a vendor code table: Z.ai 1302/1303/1305
  retryable rate limits; 1304/1308/1310/1313 terminal; 1261 context exceeded; 1316–1321 terminal quota; business errors inside HTTP 200
  bodies or finish chunks; kosong keeps `QuotaExhausted` apart from `RateLimit` on purpose. `apps/zcode-cli/packages/adapters/src/model/
  failure-classifier.ts:39-633`; `failure-provider-business-codes.ts:20-326`. → Vendor code tables live in profiles as data; the upstream
  429s on the free Qwen endpoint are `RateLimited` for that endpoint, OpenRouter's daily cap is `QuotaExhausted` and not held against the
  model.
- **Z16 · Retry policy (ADAPT).** 10 retries, 2 s doubling to 60 s with jitter, Retry-After first, never after committed streamed output;
  kosong notes that retrying quota errors burns minutes. `apps/zcode-cli/packages/adapters/src/model/retry-policy.ts:13-30`. → An
  interactive step gets a small budget (for example 2 retries, Retry-After up to a cap shown to the user); switching endpoints is a
  visible, labelled choice.
- **Z17 · Output-token continuation (ADAPT for creative text only).** A fixed "Resume directly — no apology, no recap" prompt up to three
  times, entries tagged and filtered from history. `apps/zcode-cli/packages/core/src/runtime/methods/
  turn-output-token-continuation.ts:12-76`. → At most two tagged continuations for briefings and dialogue; never mid-JSON.
- **Z18 · Transport versus content failures (ADAPT).** Empty, `null` or unparsable tool input becomes `{}` and is left to schema
  validation; a BOM is stripped. `apps/zcode-cli/packages/adapters/src/model/tool-input-normalization.ts:9-48`. → A small deterministic
  cleanup (BOM, whitespace, one fence), then content failures go to the repair loop; `parse_ok` and `schema_ok` recorded apart from
  transport errors.
- **Z19 · Reasoning history when the model changes (ADAPT narrowly).** Signed reasoning from another model or provider group is dropped;
  thinking-only and whitespace-only assistant turns removed; placeholders exist only on the wire.
  `apps/zcode-cli/packages/adapters/src/model/reasoning-history-normalization.ts:12-261`. → Only EXPLAIN chat keeps a transcript; drop all
  reasoning when its model or endpoint changes.
- **Z20 · Evaluation hooks (ADOPT).** The patched request body captured; a recording proxy whose trajectory file derives full request
  snapshots in OpenAI and Anthropic shapes and checks prefix continuity ignoring cache-marker drift. `apps/zcode-cli/tools/
  prompt-trajectory/README.md:29-87`. → Records store the final body and the raw response; a prefix-continuity check across a workflow.
- **Z21 · Remote rule updates (ADAPT).** ZCode fetches newer rules over HTTPS with a 10 MB cap, forward-only revisions and "same revision,
  different content" refused, automatically and without a pinned hash. `packages/provider-node/src/zcode-builtin-download.ts:4-117`.
  → Profiles ship with releases; an optional feed only if the user enables it, off by default, offline-blocked, hash- or
  signature-pinned (AGENTS.md); REJECT automatic unpinned fetches.
- **Z22 · The wire is part of an endpoint's identity (ADAPT).** Z.ai's own templates reach GLM, Kimi, MiniMax, DeepSeek and Xiaomi through
  their Anthropic-compatible endpoints; capabilities differ by wire for the same weights. → `wire` is part of the profile key; D021's
  OpenAI-compatible seam stays the default; an Anthropic-Messages adapter only where a probe shows it helps a candidate that matters
  (MiniMax-M3 has no first-party `response_format`).
- **Z23 · Caching knobs belong in the profile (ADOPT).** `cache_control` on messages; kosong accepts `prompt_cache_key`.
  `apps/zcode-cli/packages/adapters/src/model/transform.ts:499-513`. → `cache: Automatic | PromptCacheKey | CacheControl | None`,
  surviving the system-message merge.
- **Z24 · No small-model accommodation (REJECT tool-driven PICK/FILL; ADAPT the catalogue idea).** Neither harness has grammar decoding or
  a schema repair loop; kosong imports models.dev-style metadata but refuses per-model protocol overrides it cannot represent.
  `K:catalog.ts:1-500`. → Catalogue metadata may seed Unprobed priors, shipped as a snapshot or fetched only from a pinned, user-enabled
  source.

### 3.7 Qwen Code @3f5ae3f with Gemini CLI @2fe7c2d

Qwen Code began from Gemini CLI v0.8.2 and stopped syncing at v0.1. Its "Qwen OAuth" free tier ended on 2026-04-15. `G:` prefixes Gemini
CLI paths (`packages/core/src/`); unprefixed paths are Qwen Code's `packages/core/src/`. Shell, file, web, sandbox, sub-agent and
MCP-client code were skipped.

- **Q1 · Copy the wire format, not the coding scaffold (ADAPT).** Qwen3.8's card reports SWE results in Claude Code and publishes the
  samplers; Qwen Code's DashScope provider sends no sampler defaults of its own. `core/openaiContentGenerator/provider/
  dashscope.ts:782-784`. → The vendor-card sampler becomes an explicit "vendor-default" arm sent on every call (§5), because free and
  aggregator endpoints may not apply card defaults.
- **Q2 · Few-shot examples in the model's own notation (ADAPT).** A regex on the model name picks qwen3_coder XML, Hermes JSON, Gemma 4
  tokens or a neutral bracket form for workflow examples; the real calls still use native tools. `core/prompts.ts:978-1371`. → Exemplars
  rendered in exactly the envelope parsed (the PICK letter object, the FILL record); notation is an explicit, qualified preset field,
  not a name regex.
- **Q3 · Never show an option that cannot be used (ADOPT).** Example blocks naming undeclared tools are removed; empty headings go; the
  match requires the `"arguments"` key so stray JSON does not trigger it (#12032). `core/prompts.ts:312-393`. → The capsule builder filters
  exemplars, hints and knowledge lines against the step's actual menu letters, fields and grants; a load-time lint flags exemplar packs
  referring to fields or options outside their schema.
- **Q4 · Leaked tool calls recovered only under strict gates (ADAPT for COMPOSE on unenforced endpoints).** Stream ended cleanly with no
  structured call; prose at most 80% of the text; fenced code skipped; five XML entities decoded; scalars never coerced; args in a
  prototype-free map; recovery runs after validation throws so a retry cannot run a call twice. `core/xml-tool-call-fallback.ts:9-210`;
  `core/llm-chat.ts:6325-6454`. → Pick and Fill under a grammar or strict schema have no leak path, and text extraction is refused there;
  a recovery parser per notation for COMPOSE, marked `recovered_from_text` and counted; relying on recovery disqualifies "native tool
  calls".
- **Q5 · Leaked protocol tags and upstream placeholders (ADOPT).** Answers starting with Qwen Code's own compaction tags become
  `PROTOCOL_TAG_LEAK` with a budget of 2; an answer that is exactly a gateway's "(request timeout)" placeholder is
  `UPSTREAM_DEGRADED_RESPONSE`. `core/llm-chat.ts:1493-1780`. → Every envelope tag our prompts define is registered and a leading tag
  is a typed finding; profiles list known placeholder strings, treated as transport failures.
- **Q6 · Truncation detected even when the finish reason lies (ADOPT the detector; REJECT the `{}` fallbacks).** Unbalanced JSON at the
  end of a stream becomes `length` although the provider said `stop`; one unclosed string auto-closed; otherwise `{}`.
  `core/openaiContentGenerator/streamingToolCallParser.ts:270-432`; `core/openaiContentGenerator/converter.ts:1854-1934`. → `Truncated`
  routes to the max-tokens path; an auto-closed candidate is marked repaired; unparsable is `Err`.
- **Q7 · The structured-output channel depends on the endpoint (ADAPT).** Side queries force one `respond_in_schema` tool
  (`tool_choice=required`); `response_format` is sent only to the official OpenAI host because DeepSeek, older vLLM and validating
  gateways reject it; schemas rewritten to the strict subset, with length and count limits dropped. `core/baseLlmClient.ts:229-321`;
  `core/openaiContentGenerator/pipeline.ts:72-239, 1393-1420`. → Each profile records which channels its endpoint enforces and each preset
  picks one; DecisionKind schemas are written in the strict subset; length and count limits live in our validator.
- **Q8 · A typed reasoning capability record (ADOPT; ADAPT the clamp; REJECT silent omission).** ToggleOnly or efforts with
  `defaultEffort`, `canDisable` and `disableField`; incomplete entries rejected; qwen3.8 presets expose low, medium and xhigh; on configured
  routes an unsupported effort is silently omitted, and only legacy routes clamp to the next stronger tier (sending `high` as a DashScope
  alias). `core/reasoning-effort.ts:22-345`; `providers/presets/alibaba-standard.ts:108-146`. → A Rust enum with a strict parser; the
  measured level per step shape; any clamp shown on the plan card ("xhigh requested, using medium").
- **Q9 · Thinking-mandatory models (ADOPT).** `thinkingMandatory` marks models answering 400 to any disable shape (qwen3.8-max-preview
  on some gateways, kimi-k3, kimi-k2.7-code); a runtime "enable_thinking must be true" 400 adds the model to a set and retries once
  with thinking on. `core/contentGenerator.ts:186-188`; `core/openaiContentGenerator/pipeline.ts:241-249, 1144-1161, 1328-1358,
  1631-1647`. → `can_disable: false` filled by the probe; a runtime discovery updates the endpoint profile visibly and journals it.
- **Q10 · Knob conflicts resolved before sending (ADOPT).** DashScope rejects `reasoning_effort` with `thinking_budget`; `enable_thinking:
  true` beside an effort is dropped; `tool_choice=required` is refused while thinking is on; Qwen-only fields gated on the wire model
  (GLM behind the same gateway rejects `metadata`). `core/openaiContentGenerator/provider/dashscope.ts:45-137, 404-768`. → A data-driven
  conflict table per endpoint, one deterministic resolver, table tests, each drop journaled. Consequence: on DashScope-served Qwen the
  forced-tool channel and thinking cannot be combined.
- **Q11 · The off switch differs by stack (ADOPT).** DashScope tiered family `reasoning_effort:"none"`; hybrids `enable_thinking:false`;
  vLLM, SGLang and llama-server `chat_template_kwargs.enable_thinking=false` (a top-level field is ignored); DeepSeek `thinking:{type:
  "disabled"}`; OpenRouter `reasoning:{enabled:false}`, only to that host, recognised by parsed hostname (`openrouter.ai.evil.com` is
  rejected). `core/openaiContentGenerator/pipeline.ts:96-123, 1201-1326`; `core/openaiContentGenerator/provider/openrouter.ts:21-36`.
  → A (host class, model family) table from parsed URLs.
- **Q12 · `<think>` inside content (ADOPT for unconstrained endpoints).** Parsed into the reasoning channel with a tail buffer for split
  tags; an unclosed thought logged. `core/openaiContentGenerator/taggedThinkingParser.ts:12-128`. → Stripped before the schema parse and
  never stored; an unclosed block at the end is `ThinkingOnly`.
- **Q13 · Invalid answers are typed and separate from transport errors (ADOPT).** Qwen Code: no finish reason, no text, no progress,
  protocol tag leak, malformed call, degraded response; Gemini CLI adds unexpected call, max tokens, safety and recitation blocks and
  thinking-only; empty-text detection strips zero-width characters first. `core/invalid-stream-error.ts:10-25`;
  `G:core/geminiChat.ts:104-339, 1548-1632`. → `InvalidAnswer` variants, each with its budget and route (§4.7).
- **Q14 · Retry nudges appended at the end so the prefix stays cached (ADOPT).** Gemini CLI appends one fixed "[System: … provide your
  final answer or call a tool now.]" sentence to the last user turn, deduplicated, never editing the system instruction ("This preserves
  the prefix cache"), inserting a neutral model turn first when the tail is a tool result. `G:core/geminiChat.ts:244-305, 964-988`. →
  Repair findings after the restated schema, the last capsule segment (doc 38 §3.3); continuation with overlap removal only for creative
  text.
- **Q15 · Samplers are data per call role (ADAPT).** Utility calls T 0 and top_p 1; chat T 1, top_p 0.95, top_k 64; thinking budgets 0–512
  for helpers; a retry override sets T 1 because a T 0 retry repeats the failure. `G:config/defaultModelConfigs.ts:21-342`. → A settings
  table keyed by (step kind, preset) with `extends` and a cycle check (D025); retries resample with a new seed (doc 38 §4.2); Gemini 3.x
  stays at T 1.0.
- **Q16 · Loop and degeneration detectors with tuned thresholds (ADAPT).** Five identical consecutive calls stop a turn, kept under
  DashScope's own 400 threshold (#5019, the only threshold tied to a server limit); "chanting" (10 repeats of a 50-character chunk); a
  periodic long-unit rule; repeated thoughts at 3; an adaptive per-turn cap; Gemini CLI adds an LLM judge after 30 turns.
  `services/loopDetectionService.ts:65-1468`; `G:services/loopDetectionService.ts:29-66`. → Chunk-hash and periodic detectors for streamed
  creative text and reasoning streams (a think loop burns free quota); the identical-call guard for COMPOSE lookups; REJECT the LLM judge.
- **Q17 · Two stream watchdogs (ADOPT).** Idle (240 s, reasoning deltas count) and lifetime (900 s of time spent waiting upstream,
  monotonic clock), because drip-fed gateway streams reset idle timers forever (a source comment reports 2.5–4.5 h lost to one).
  `core/stream-guards.ts:26-296`; defaults in `core/openaiContentGenerator/constants.ts:29-60`. → Typed `StreamIdle` and
  `StreamLifetime` with numbers, defaults per step kind [I: tune in round 0];
  each trip is a dependability event.
- **Q18 · Provider errors classified by kind and diagnosis (ADOPT).** Transport codes found through the cause chain; provider codes that
  can never succeed fail fast even inside a 200 SSE stream (`content_filter`, `insufficient_quota`, `context_length_exceeded`…);
  Retry-After honoured as a minimum. `utils/retryErrorClassification.ts:13-492`; `utils/rateLimit.ts:11-175`. → For OpenRouter, read
  `error.metadata.error_type` first, then the status; a unit table of real error bodies.
- **Q19 · Quota errors split into terminal and retryable (ADOPT; round 0 needs it now).** Gemini CLI's `TerminalQuotaError` covers daily
  limits, `QUOTA_EXHAUSTED`, capacity exhaustion, any suggested delay above 300 s and "limit: 0" (no allowance on this tier);
  `RetryableQuotaError` covers per-minute limits and delays of 300 s or less. `G:utils/googleQuotaErrors.ts:28-463`. → `RateLimited`,
  `QuotaExhausted{resets_at}` (parks until reset, 00:00 UTC for OpenRouter's free cap), `UpstreamRateLimited`, `NotInFreeTier`,
  `CapacityExhausted`; REJECT ten persistent retries (every attempt counts against a free allowance).
- **Q20 · A per-model health state machine (ADOPT).** Terminal (quota or capacity, the latter expiring after 30 s) or sticky-retry;
  transient failures never overwrite terminal ones. `G:availability/modelAvailabilityService.ts:9-160`. → `EndpointHealth` per (provider,
  model id, precision), shown in the run panel and gating dispatch; its history feeds the free-endpoint rating.
- **Q21 · Fallback is the user's choice, except where it is not (ADAPT; correction).** Gemini CLI's default policy prompts the user
  (retry once, always, later, stop, upgrade), but auto-routing makes transient failures silent and the Flash-Lite utility chain is silent
  throughout; Qwen Code runs a configured chain of up to three fallback models on 429/503/529 automatically. `G:fallback/handler.ts:26-196`;
  `G:availability/policyCatalog.ts:41-141`; `core/llm-chat.ts:4836-4870`. → On a quota park, an ask card (retry later, stop, switch this
  step to another qualified setup with its cost, an informational credits link); REJECT both silent paths (D023).
- **Q22 · Prompt-cache breakpoints on the last stable block (ADOPT).** DashScope `cache_control` on the system message, the last tool and
  the last stable block; stable tool order. `core/openaiContentGenerator/provider/dashscope.ts:289-970`. → A breakpoint before the
  per-candidate tail; snapshot tests that prefix bytes are identical across K candidates.
- **Q23 · Two model identities (ADAPT).** Loose normalisation (stripping prefixes and `:free` tags) for hints only; provider quirks keyed on
  parsed hostnames. `core/tokenLimits.ts:116-139`. → Qualification keys on the exact endpoint (model id including `:free`, served
  provider, precision): Qwen3.8-27B `:free` is fp4 on ModelRun while paid routes are bf16.
- **Q24 · Per-host quirks as flags with regression tests (ADOPT).** Cerebras rejects replayed `reasoning_content`; some qwen3 servers read
  replayed reasoning only from `reasoning`; old templates read tool results only as strings; Gemini wants OpenAPI 3.0 schemas (string
  enums, `nullable`, bounded depth). `core/openaiContentGenerator/provider/cerebras.ts:34-56`; `utils/schemaConverter.ts:13-80`. → Data
  flags with fixture tests; a schema-depth lint; capsules never replay reasoning.
- **Q25 · Evaluation hooks (ADOPT with a scope limit).** Typed events for content retries, loops and API retries; adversarial test files
  for fences, entities, `__proto__` and periodic chants. → Local journal records only, feeding qualification metrics; no telemetry export.

### 3.8 K2 Vendor Verifier (Moonshot AI) @0bc5061, read with Kimi-Vendor-Verifier @66092cf

K2VV has no licence file, so only ideas are used; its successor is MIT but its prompt-token cases derive from Moonshot-internal
repositories, so no data is reused either. `KVV:` prefixes successor paths. Moonshot's own numbers: 4,000 requests per model, half
published; K2-0905 official average F1 84% with an acceptance bar of 80%; K2-thinking bar 73% [V, re-checked 2026-09-28].

- **K1 · Qualify the endpoint, not only the model (ADOPT).** Replay the same requests against a reference serving and a candidate host;
  score the candidate's decisions against the reference's (trigger F1) and the format of what it returns (schema accuracy). `README.md:
  296-328`. → Reference: our qualified local run or a pinned paid endpoint of the same weights; candidate: the free host; metrics: PICK
  agreement with the reference arm (beside accuracy on gold) and FILL schema-pass. In `tools/local-qual` and the product's user-started
  "Check this endpoint".
- **K2 · The headline metric is not in the code (ADOPT the lesson in reverse).** `tool_calls_eval.py` writes per-run counts only; no F1 or
  join with reference results. `tool_calls_eval.py:816-879`. → Plotroom's comparator, both arms' raw outputs and the join key live in
  the same public tool.
- **K3 · The pass bar comes from the reference's own noise (ADAPT).** Bars sit about 3 points under the official API's worst run
  (K2-thinking min 75.81% → bar 73%; K2-0905 min 82.71% → 80%). `README.md:151, 294`. → The reference arm's agreement across its own k
  samples is the noise floor; a candidate passes if within the lower binomial bound (a fixed margin is meaningless at 30 menus).
- **K4 · A conditional schema rate hides abstention (ADOPT).** Schema accuracy is computed over responses that attempted a call; Groq
  scored 100% schema accuracy with 69.52% trigger F1 and 1,042 calls against Moonshot's 1,274. `README.md:175-320`. → FILL schema-pass
  uses every call as the denominator (text answers, empties, refusals, length stops and failed calls count as not passed).
- **K5 · Outcome categories lose information (ADOPT the detail, REJECT the lumping).** `others` folded into `stop` for F1; a missing
  stream `finish_reason` becomes `stop`. `tool_calls_eval.py:496, 548-553, 861-872`. → An exhaustive outcome enum (answered:
  conformant, non-conformant, degenerate; truncated; filtered; empty; missing or non-standard finish; rate-limited account or upstream;
  server error; rejected 4xx; transport; parse error); PICK's escape X as the "trigger" for a TP/FP/FN/TN table.
- **K6 · Validate by content, not by the finish flag (ADAPT).** Tool calls returned under `stop` (a known serving bug) are never checked.
  `tool_calls_eval.py:551-632`. → Validate any payload present; a disagreeing finish reason is a `finish_mismatch` defect; membership in
  the offered menu checked like K2VV's tool-name lookup.
- **K7 · Retries hide unavailability (ADAPT).** Infinite retries with jitter plus the SDK's own three; attempts only in logs; unlimited
  stream read timeout. `tool_calls_eval.py:38-75, 223-229, 383-402`. → One owned retry layer; every attempt a ledger row (status, account
  or upstream 429, Retry-After, latency, stream cut); 429s per 100 calls and time-to-success as rating data; never retry a format failure.
- **K8 · Resume semantics right, resume key incomplete (ADOPT the semantics; fix our key).** Only transport failures re-run; but the hash
  omits `extra_body` and the base URL, so a changed host or thinking switch silently reuses old results; the successor's `--reruns 3`
  keeps the last record (best of four). Plotroom's own `--resume` key (model, suite, item, condition, variant, sample;
  `tools/local-qual/run.py:264-280, 442`) has the same gap. → The key is a hash of the canonical full request: messages, schema, sampler,
  extras, provider pin, profile version, suite hash; REJECT quality reruns.
- **K9 · Streaming and non-streaming tested separately (ADAPT).** Three rules for rebuilding streamed names; usage in `choices[].usage` or
  top level; a server that ignores `stream=true`. `KVV:tests/k3_features/conftest.py:28-272`. → PICK and FILL are non-streamed; a
  streamed creative-text endpoint is qualified in both modes; Rust reassembler unit tests for each case.
- **K10 · Raw completions isolate template and parser from weights (ADAPT; REJECT `trust_remote_code`).** The client renders the template
  and parses native tokens itself; vLLM found three K2 bugs this way (218 → 971 successful calls); K2VV's own parser silently drops a call
  such as `search:2`. `tool_calls_eval.py:88-129, 236-314`. → The local `llama-server` run on the pinned GGUF is our isolation arm; parse
  failures are `ParseError` with raw text, never "no answer".
- **K11 · Check prompt tokens before generating (ADOPT).** Expected counts per fixed request; accept `usage.prompt_tokens` within
  [expected, expected + 3]; raw JSON bytes sent; one case shows the official server adds about 83 tokens for a one-field schema (36 →
  119). `KVV:tests/prompt_tokens/test_prompt_tokens.py:26-258`. → Preflight compares host counts, with and without `response_format`,
  against `/apply-template` plus `/tokenize` on the reference: template drift, dropped system messages and each host's real schema
  overhead (replacing doc 50's assumed τ) [U whether OpenRouter reports provider counts for `:free`].
- **K12 · Negative probes over raw HTTP (ADAPT).** Wrong locked sampler values must get 400; malformed `response_format` and `tool_choice`
  sent raw because SDKs "may normalize or reject these raw payloads before they reach the vendor endpoint"; "Run formal benchmarks only
  after all tests pass". `KVV:verify_params.py:1-122`; `KVV:tests/k3_features/test_response_format.py:153-256`. → A few negative
  schema probes; a host answering 200 to a malformed schema request is marked untrusted until the positive canary proves enforcement.
- **K13 · A per-keyword schema conformance matrix (ADOPT).** Each schema from a keyword-grouped corpus wrapped as one required `value`,
  strict, forced, validated locally (Draft 2020-12), reported by suite with `infra_error` apart. `KVV:tests/tool_call_json_schema/
  validator.py:179-706`. → A capability table per endpoint for exactly the keywords Plotroom's compiler emits, one or two synthetic calls
  each.
- **K14 · Schema features that destabilise decoders (ADOPT as a lint).** `default` removed everywhere ("observed on kimi-k2.5 where
  required properties are occasionally omitted"); exotic keys, unterminated recursion, huge `minLength` and non-finite numbers skipped.
  `KVV:tests/tool_call_json_schema/validator.py:108-366`. → Never emit `default` or `examples`; identifier keys; canonical serialisation
  so schema bytes stay stable for caching and resume hashes.
- **K15 · Constrained JSON should be compact (ADAPT).** Constrained output is asserted to contain no newline or tab. `KVV:tests/
  k3_features/test_response_format.py:322-358`. → Whitespace share and length-stop rate per host as FILL diagnostics; local grammars
  forbid free whitespace (Gemma pretty-prints, doc 46).
- **K16 · Valid is not substantive (ADOPT).** Empty objects or meaningless values rejected; tool-history integrity checked.
  `KVV:utils.py:236-401`. → FILL schema-pass split into conformant and substantive (non-empty spans, no placeholders, no echoed schema
  keywords, no values copied from the example).
- **K17 · The same weights need a different reasoning switch per host (ADOPT).** Official API `thinking:{type:"disabled"}`; vLLM, SGLang and
  KTransformers `chat_template_kwargs:{thinking:false}`. `README.md:389-401`. → Key the reasoning switch by (family, host kind); store the
  exact extras sent per record (`run.py` keeps sampler and pin only in the run header today).
- **K18 · Locked samplers and silently ignored options (ADOPT).** The Kimi API fixes temperature (1.0 thinking, 0.6 not), top_p 0.95 and
  penalties 0 and rejects other values; K2.6 rejects `tool_choice:"required"`; a named-function choice is silently ignored.
  `KVV:verify_params.py:1-36`. → Profiles declare locked parameters and supported forms; both arms run at locked values; the negative
  probes confirm options took effect.
- **K19 · Tool-call history is a bug source (ADOPT the principle).** Malformed ids in history make Kimi generate bad ids; thinking mode
  needs the full assistant message back. `README.md:343-346`. → PICK and FILL stay single-turn capsules; EXPLAIN follow-ups rewrite ids
  to the native form and never leave orphan tool messages.
- **K20 · A host's decision pattern is a fingerprint; re-verify on a schedule (ADAPT).** Trigger counts on one test set ranged from 644
  (Nebius) to 1,274 (Moonshot) on K2-0905, and up to 3,657 (Chutes) against 1,958 on K2-thinking. `README.md:39-341`. → Store per
  endpoint the PICK choice distribution (escape rate, chosen-position histogram, which exposes template or sampler defects) and the FILL
  outcome mix against the reference; badges carry "last verified"; a re-check canary runs only when the user starts it or has enabled
  it, with its call count shown first, because on a free tier every canary call spends the user's daily allowance (doc 40).
- **K21 · The replay unit is the complete request (ADOPT; ADAPT the private split).** Each line is a full request; each result stores the
  prepared request and the full response; half the set stays private so vendors cannot tune to it. → Records store the serialised
  request (or its canonical hash plus capsule inputs); Plotroom's repository is public, so seeded procedural variants generated at run
  time replace a private split.
- **K22 · Out of scope (REJECT).** The successor's coding-agent and long-context benchmarks and its vendor-internal routing header. →
  Qualification stays on Plotroom's own step-kind suites plus the endpoint checks above.

### 3.9 Vendor frameworks read from documentation, not studied in code [V unless marked]

| Framework (rows) | What it teaches | Verdict [I] |
| --- | --- | --- |
| Qwen-Agent v0.0.34 @31a4d36 (Qwen3–3.6 cards) | Lenient `json5` parse then strict `jsonschema` validation; never parse `<tool_call>` inside a thought; a per-run cap of 20 LLM calls; token-budgeted truncation keeping both ends; a random seed per call unless pinned; `use_raw_api` defers to the server's parser; `code_interpreter` "is not sandboxed" | ADOPT the parse-then-validate order and the seed warning; REJECT code execution, MCP and RAG over files |
| Google ADK 2.x (Gemma 4, Gemini) | 2.0 moved "from a hierarchical agent executor to a graph-based execution engine" because long prompt procedures became "less reliable"; typed node contracts; a Gemma 3 mixin that injects tools as text and parses the last JSON; LiteLLM path parses strict JSON, then Python literals, then unquoted keys; `output_schema` plus tools only on some models | Convergent evidence for docs 21, 25 and 38 (code-owned graphs); ADOPT "tolerant pre-parse, then strict validation, never the reverse" and "a step formats or acts, never both" |
| LiteRT-LM and AI Edge Gallery "Agent Skills" (Gemma 4 E2B/E4B) | Few generic tools, an explicit JSON schema in the instructions, skills chosen by the model from descriptions; llguidance constrained decoding on device | Plotroom stays stricter: code chooses skills (SKILL.md safe profile), grammars enforce schemas; LiteRT-LM is a possible later backend, llama.cpp stays the measured runtime (doc 46) |
| Llama Stack → OGX (Llama rows) | Meta no longer ships a Llama-specific harness; the model knowledge lives in the server's template and parser | Confirms that each model's profile must record template, parser and tool-result role; OGX is out of scope (server-side tools and state) |
| NVIDIA NeMo Agent Toolkit, Switchyard, Gym, Evaluator (Nemotron rows, Granite 4.2) | ReWOO keeps tool output out of the planner; a per-step router; published reproducibility recipes ("even small differences in these parameters can materially change results") | ADOPT publishing our qualification recipes (prompts, samplers, flags, pinned builds) so badges are reproducible; per-step routing is already doc 40 policy |
| Liquid LEAP SDK (LFM rows) | Deprecated in 2026-09 in favour of llama.cpp guides with JSON schema or GBNF; IFStruct excludes constrained decoding because "it cannot by itself make the model choose the right fields, values, or escaped content" | Supports grammar for syntax plus code validators for semantics; do not build on LEAP |
| MiniMax Mini-Agent (MIT) | Reference for interleaved thinking: replay the complete assistant response | Captured in the MiniMax profile; single-shot steps avoid replay |
| openai/harmony (Rust core) | The renderer and parser gpt-oss hosts need | Plotroom uses the host's structured output, not Harmony tools |

### 3.10 Convergent lessons across the studied harnesses [I on V]

| Lesson | Independently present in | Plotroom decision |
| --- | --- | --- |
| Per-model and per-endpoint capabilities kept as data, not code | ZCode (Z1), kosong (Z3), Qwen Code (Q8, Q24), Hermes (host tables), Gemini CLI (Q15), Mellea (model catalogue) | Profiles and D048 presets (§4) |
| Unknown capability is not "no"; probe behaviour, not flags | kosong, K2VV (K12, K13), Hermes (H5), doc 48 §2.3 | Tri-state fields with evidence |
| One reasoning encoding per request; mandatory-reasoning models stepped up, not stripped | ZCode (Z5 counter-example, Z7), Qwen Code (Q9–Q11), Hermes (H8, H9), Mellea (M15) | `reasoning_off: Honoured \| FloorAt` |
| Transport retries separate from content repair; typed errors; upstream versus account quota | Hermes (H13), Gemini CLI (Q19), Qwen Code (Q18), ZCode (Z15), BFCL (B14), Terminus (T17) | §4.7 |
| Empty, think-only and truncated answers are distinct typed outcomes | Hermes (H10, H12), kosong (Z9), Gemini CLI (Q13), Qwen Code (Q6), Vibe (V9) | `InvalidAnswer` variants |
| Repair feedback appended at the tail, so the prefix stays cached | Gemini CLI (Q14), Mellea RepairTemplate (M3) | Doc 38 §3.3 capsule order |
| Schemas lowered per dialect with stripped constraints restated | Hermes (H6), BFCL (B11), ZCode and kosong (Z13), Vibe (V7), Qwen Code (Q7), Mellea (M17) | Portable subset by construction plus normaliser |
| Deterministic loop and repetition guards | Hermes (H15), Qwen Code and Gemini CLI (Q16), BeeAI cycle checker | Creative text and reasoning streams |
| Think tags and control tokens scrubbed or neutralised | Hermes (H10, H18, H19), Qwen Code (Q12) | Intake normaliser; untrusted-text table |
| Silent fallbacks: failed values returned, `{}` substituted, requirements dropped, models switched | Mellea (M5), Hermes (H16), BeeAI (M24), Qwen Code (Q6), Gemini CLI auto-routing (Q21), Terminus (T8) | REJECT all of them |
| Deterministic, testable harness cores | Vibe (V1–V2, V15–V17), Terminus fake endpoint (T19), Hermes 418 capture (H25) | Reducer, contract tests, scripted fake endpoint |
| Endpoints qualified differentially against a reference | K2VV (K1–K4), AA Endpoint Accuracy | §4.8 and §5 |

## 4. What Plotroom adopts: model profiles under D048's presets (proposal) [I]

### 4.1 Position and scope

- **The decision it serves.** D048 (owner, 2026-09-28): "we adjust the harness towards what these models are already trained for",
  with a preset per model and step kind, measured on a tuning split and accepted on a held-out split, bound to the model file, runtime
  build and chat template, and a general fallback preset for untuned models. Doc 55 (draft) owns the knob catalogue, the preset file
  format and the tuning protocol. This section supplies two inputs: the **profile** (probed facts about a model on an endpoint, which
  every preset for it must respect) and the **native-convention knobs** this doc found (§2, §3).
- **Where it sits.** D021's provider layer ("own the seam, rent the wires") pins model ids in `models.toml` with dated prices and probes
  each endpoint; D046 makes aggregators first-class with pinned routes; D022's managed `llama-server` sidecar is the local runtime.
  Profiles and presets are the data the adapter reads between the workflow runtime's typed request (decision kind, capsule segments,
  schema, budget) and the bytes on the wire, on both paths.
- **What they may change.** How a request to the provider the user configured is shaped, and how its reply is parsed and validated;
  never the facts, option computation, validation or repair limits (D048 item 2). No tool, file access, network destination or code
  execution is added, so Wilco's scope cannot widen (AGENTS.md). Both are data, never code: no scripts and no expressions evaluated from
  downloaded files (§3.6 Z4, Z21).
- **Reconciliation with doc 55 (added at review, 2026-09-28).** Doc 55's draft reached the tree after this doc was written. Where they
  differ, doc 55 governs the preset side: it calls the object a *harness preset* and leaves the name open (its open question 1 lists
  "model profile" as this doc's working title); its preset file is versioned, data-only JSON (§4.10's TOML is illustrative only); a
  harness preset carries no prompt text, only ids into the release's prompt pack (applied to §4.3 and H20 here); and Pick and Fill
  penalties stay neutral under D022 item 5 (applied to §5 here). Doc 55 §1.3 read the vendor cards directly and says it must be
  reconciled with this doc; §2 and the CSV are the input for that.
- **The fallback preset is the reference.** Today's uniform capsule (doc 38 §3.3) is the natural first general fallback preset (D048
  item 7). A tuned preset differs from it only in knobs that won a measured comparison (§5; D048 item 4), so every deviation carries
  evidence and the fallback stays the reference arm for every new model.

### 4.2 Identity and layering

- **Key:** (model artifact, wire, endpoint route). Locally the artifact is the GGUF's repository, revision and SHA-256 plus the
  embedded template's hash and the runtime build (doc 46; D048 item 5); in the cloud it is the model id including any `:free` suffix,
  the served provider, the precision and the date (doc 48 §7.4 item 1; D045 item 5; D046).
- **Layers, lowest to highest** (after ZCode, Z1): family defaults (vendor-card priors, this doc's CSV) → model × wire → model × wire ×
  endpoint → values measured in probes and qualification → the user's exact override, which marks the setup "custom" (D037; D048 item
  6). Ids are exact or anchored; no substring matching (H20, M14, Q2). A setup is executable only when every field its step kind needs
  is present (Z2).
- **Distribution:** shipped with releases beside the model manifest (D048 Consequences); an optional update feed only if the user
  enables it, off by default, blocked offline, hash- or signature-pinned, forward-only revisions (Z21, AGENTS.md, D008).

### 4.3 Fields

"Fact" fields belong to the profile and are set by probes; "choice" fields belong to D048's preset and are set by tuning. A choice may
only select among what the facts allow (a preset cannot switch off reasoning that the profile records as mandatory).

| Group | Fields and values | Fact or choice | Filled by | Lessons |
| --- | --- | --- | --- | --- |
| Identity | `profile_id`; `artifact`; `template_sha`; `runtime_build`; `route` (provider pin, precision, `allow_fallbacks: false`, `require_parameters: true`, ZDR, per D046); `wire` (`openai-chat`, `openai-responses`, `anthropic-messages`, `llama-server`) | Fact | Release, probe | B3, Z22, Q23 |
| Template | `system_role` (native or fold into the first user turn); `single_leading_system`; `role_alternation` (strict or lenient); `developer_role`; `default_system_injected`; `mid_conversation_system` | Fact | Template render, probe | B10, T12, Z11, Z12, V10, H27 |
| Reasoning facts | `reasoning_control` (template kwarg, effort field, thinking type, OpenRouter object, system-prompt sentence, none); `reasoning_off` (`Honoured{body}` or `FloorAt(level)`); `levels` ordered weakest first; `forbidden_values` (for example `high` on Qwen3.8); `knob_conflicts`; `reasoning_key_in` (scan all) and `_out` (pinned) | Fact | Probe | H8–H10, Z5, Z7–Z10, Q8–Q11, M15, K17 |
| Reasoning choices | Level per step kind (off or the floor for PICK and FILL); `preserve_thinking` sent explicitly; `reasoning_echo` (never for PICK and FILL) | Choice | Tuning | Same |
| Sampler (per step kind) | Each key `Pin(v)`, `Omit` or `ServerDefault`; `locked` parameters and `seed_supported` are facts | Choice within facts | Vendor prior; tuning | H21, T13, K18, Q15 |
| Output | `cap_field` (`max_tokens`, `max_completion_tokens`, `max_output_tokens`); `context_window`; `max_input_tokens`; measured token ratio τ are facts; the cap per step kind, with reasoning headroom, is a choice | Both | Probe (K11), tuning | Z9, V11, K11 |
| Schema | `schema_dialect` (normaliser id) and `keyword_capabilities` are facts; `schema_mode` per step kind (`Grammar`, `JsonSchemaStrict`, `JsonSchemaNonStrict`, `JsonObjectPlusPrompt`, `PromptOnly`, `ForcedTool`), `envelope` (JSON or tagged, no-schema only) and compact whitespace are choices | Both | Canary, tuning | H5, H6, B11, M17, Q7, Z6, Z13, K13, T9 |
| Prompt conventions | `answer_field_name` (Qwen's `answer`); `schema_statement` (NVIDIA's "Response Formatting Schema", IBM's JSON system sentence, Harmony developer message); `layout_variant`; `exemplar_notation`; `preamble_variant`. Each is a named id resolving into the release's versioned prompt pack, never free text in the preset (doc 55 §1.4) | Choice (only after a §5 win) | Tuning | H20, M14, Q2 |
| Stops and intake | `stop_tokens`; `keep_special_tokens`; `think_forms` (fields and tags, CJK included); `finish_reason_map`; `leak_markers`; `placeholder_strings`; `salvage_reasoning` (counted, penalised) | Fact | Template, probe | B15, H10, H11, H19, Q5, Q12, K5 |
| Untrusted text | Control-token families to neutralise in mission text | Fact | Release | H18 |
| Transport | `cache` (automatic, `prompt_cache_key`, `cache_control`, none) and session affinity; vendor `error_codes`; measured latency are facts; retry budget and timeouts derived from measured p90 are choices; streaming never for PICK and FILL | Both | Probe | H13, H22, H23, Q17–Q19, Z15, Z23 |
| Evidence | Every fact `Unprobed`, `Yes{run_id, date}` or `No{run_id, date}`; `last_verified` | Fact | Canary | Z3, K20 |

### 4.4 Schema mode per step kind

| Step kind | Default | When the canary says no | Never |
| --- | --- | --- | --- |
| PICK | Local grammar; cloud strict `json_schema`; flat letter enum plus escapes X and Q; `why` before `pick` when asked | Prompt JSON (one bare object, JSON-rendered menu) plus validator and one repair, as a labelled arm; a forced single tool only where §5 shows it better for that family | Wrapper tags; requested fences; answers taken from reasoning without the `recovered_from_reasoning` flag |
| FILL | As PICK; schema in the portable subset (no `$ref`, explicit types, single-type enums, closed objects, all required, no `default`); stripped constraints restated in descriptions | `json_object` or prompt schema plus validator and repair; NuExtract3's template adapter for that model | `{}` fallbacks; silent defaults; type coercion |
| COMPOSE | Lookup and Check rounds first, then one schema-constrained call; tool choice as a PICK over constant tool names plus a FILL of arguments (M19) | Same, with prompt JSON | Schema and tools in one request |
| EXPLAIN | Bounded JSON with cards; Granite's `documents` channel only if qualified | — | EXPLAIN without cards for models that scored 0/24 without them (docs 44, 47) |
| Creative text | Today JSON-wrapped (`tools/local-qual` asks for "JSON only"); §5's E factor tests plain bounded text or a tagged envelope, since JSON escaping costs on quotes and newlines (T9; the Qwen3-Coder report) | — | Continuation in the middle of JSON |

### 4.5 Intake and admission, in order

1. **Transport classification**: HTTP status, error bodies inside HTTP 200, upstream versus account limits (`ProviderFailure`).
2. **Finish and truncation**: `finish_reason` normalised; truncation detected from it, from unbalanced JSON or from a missing stop token
   (`Truncated`, `ThinkingExhausted`).
3. **Reasoning split** from every channel and tag form; counted in the ledger; never stored in the journal.
4. **Deterministic cleanup**, a closed list: BOM, surrounding whitespace, one outer fence, text before the last closing reasoning tag;
   each application logged.
5. **No-schema channel only**: scan every top-level JSON value; exactly one envelope-shaped survivor, else `AmbiguousAnswer`.
6. **serde** with `deny_unknown_fields`; duplicate keys and non-finite numbers rejected.
7. **Schema validation** against the full original schema, including constraints the dialect normaliser stripped.
8. **Domain validators** (menu membership, quotes, catalogue, geography) producing typed findings.
9. **Settlement**: `Admitted{value, deviations, flags}` or `Rejected{finding}`. Flags (`repaired_syntax`, `auto_fixed`,
   `recovered_from_reasoning`, `recovered_from_text`) are counted separately in qualification and never count as first-pass successes.

Rejected outright: `eval` on model text, `{}` substitutes, fuzzy admission, silent clamping, best-of reruns and failed values returned as
results.

### 4.6 Repair, retry and budgets

- **Three budgets, never shared:** transport retries (typed, `Retry-After` honoured, no SDK-level retries), resamples after an
  `InvalidAnswer` (new seed), and model repair R (doc 25 §7.2). The ledger reserves K × (R + 1) calls per decision.
- **Repair capsule:** a fresh single-turn capsule with the same prefix; the finding at the tail after the restated schema; the offending
  value quoted as data; allowed values computed by code; no reasoning replay (M3, Q14, V10, H3).
- **Stops:** a recurring typed finding, a repeated answer digest, three strikes on echoed or blank answers (H17, M10).
- **Escalation is visible:** a "retry with another setup (cost shown)" card; never a silent model or endpoint switch (D023; Q21).
- **Free tiers:** a per-account daily counter; a quota park until the reset time instead of retries (Q19).

### 4.7 Error taxonomy

```rust
// Proposal-only; not compiled; names and fields illustrative. One enum per crate (AGENTS.md error design).
pub enum ProviderFailure {
    RateLimited { scope: RateScope, retry_after_ms: Option<u64> }, // RateScope: Account | Upstream
    QuotaExhausted { resets_at_unix_s: Option<u64> },              // daily caps: park until reset
    NotInFreeTier,                                                 // e.g. "limit: 0"
    CapacityExhausted { retry_after_ms: Option<u64> },
    Overloaded { provider_code: Option<u32> },                     // e.g. Z.ai 1305 on HTTP 429
    ContextExceeded { prompt_tokens: u32, limit: u32 },
    CapabilityRejected { capability: Capability },                 // e.g. json_schema unavailable
    BusinessErrorIn200 { provider_code: u32 },
    StreamIdle { idle_ms: u64, chunks: u32 },
    StreamLifetime { cap_ms: u64, chunks: u32 },
    InvalidRequest { status: u16 }, StructuralRequest { status: u16 }, Auth { status: u16 },
    Transport { kind: TransportKind }, Cancelled,
}
pub enum InvalidAnswer {
    Empty { deterministic: bool }, ThinkingOnly, Truncated { cap: u32 }, ThinkingExhausted { cap: u32 },
    ProtocolTagLeak, UpstreamPlaceholder, AmbiguousAnswer { candidates: u8 }, ParseError { offset: u32 },
    Filtered, FinishMismatch,
}
```

| Outcome | Counts against model accuracy | Counts against endpoint dependability | Counts against neither |
| --- | --- | --- | --- |
| Findings (wrong option, invented place, failed checks) | Yes | — | — |
| `InvalidAnswer` other than `Filtered` | Yes (per model and endpoint) | `Empty{deterministic}`, `UpstreamPlaceholder` also here | — |
| Upstream `RateLimited`, `CapacityExhausted`, `Overloaded`, stream watchdogs, `BusinessErrorIn200` | — | Yes: a free model that is rate-limited for hours is not dependable, whatever its accuracy (doc 48 §5.4's uptime rule; D045 item 5) | — |
| Account `RateLimited`, `QuotaExhausted`, `Auth`, `Cancelled` | — | — | Yes (they describe the user's account or choice) |
| `Filtered` | — | — | Reported separately (doc 50 §5.9) |

### 4.8 Qualification, badges and endpoint verification

- **Badges belong to a preset and a step kind** (D048 item 5; D037). A badge records the preset and profile hashes; a change to any
  field that reaches the wire voids it for the affected step kinds, exactly like a changed template hash (B3). PICK, FILL, EXPLAIN,
  COMPOSE and creative text qualify separately.
- **Cloud first** (D044): the cloud screen uses the same preset as the local run except precision; doc 50 §5.6's promotion rule applies;
  only the local run on the pinned runtime sets a badge.
- **Free models** (D045 item 4) are offered for a step kind only if the provider's terms allow it and the preset on that endpoint
  qualified; a model or service under D047 is tested with synthetic suites only and never becomes a preset.
- **Endpoint verification** (K1–K4, K11–K13, K20): reference = the local qualified run or a pinned paid endpoint of the same weights;
  candidate = the free host. Metrics: PICK agreement with the reference, FILL schema-pass over all calls, the keyword conformance matrix,
  the prompt-token check, and reliability (upstream 429s per 100 calls, empties, watchdog trips, time to success). Badges show "last
  verified"; re-checks (at session start or on a schedule) are opt-in, off by default, and show their call count and cost before the
  first call, since they spend the user's own quota (doc 40; D045).

### 4.9 What is not adopted

Shell, file, web and computer-use tools, MCP-client roles, code execution, sandboxes and sub-agents (every studied harness has some);
LLM judges as acceptance gates (M7) or loop detectors (Q16); model-written summaries of facts (T15; V12 outside chat); silent model or
endpoint fallback (Q21); automatic model downloads (M25); unpinned remote rule updates (Z21); `trust_remote_code` and `eval` on model
text (K10, B12); substring-keyed prompt patches (H20); per-step allow-lists and dates in the system prompt (M23).

### 4.10 A profile and preset sketch (proposal-only; field names and syntax not final; doc 55 owns the preset format, drafted there as JSON)

```toml
# A profile holds facts; "unprobed" values are priors from data/model-profiles.csv until a canary replaces them with evidence.
[[profile]]
id = "qwen3.8-27b.openrouter-free.modelrun-fp4"
artifact = { model = "qwen/qwen3.8-27b:free", provider = "modelrun", precision = "fp4" }
wire = "openai-chat"
route = { only = ["modelrun/fp4"], allow_fallbacks = false, require_parameters = true, zdr = true, data_collection = "deny" }
template = { system_role = "native", single_leading_system = true, role_alternation = "lenient", developer_role = false }
reasoning = { control = "openrouter-reasoning", off = "unprobed", off_body = { reasoning = { enabled = false } },
              levels = ["low", "medium", "xhigh"], forbidden = ["high"] }
schema = { dialect = "openai-strict", strict_enforced = "unprobed" }
sampler_accepted = { top_k = false, min_p = false, seed = false }   # endpoint catalogue, 2026-09-27
cache = { mode = "automatic", session_affinity = "session_id" }

# A preset holds choices (D048), made within the profile's facts.
[[preset]]
profile = "qwen3.8-27b.openrouter-free.modelrun-fp4"
id = "general-fallback"                       # today's uniform capsule; the reference arm of §5
[preset.pick]
schema_mode = "json-schema-strict"            # falls back to "prompt-json" if the canary says the schema is not enforced
reasoning = "off"
preserve_thinking = false
sampler = { temperature = 0.6, top_p = "server", presence_penalty = 0.0 }  # a number pins; "omit" sends nothing; "server" defers
# "server" is shown only to illustrate the tri-state; D022 item 5 pins every accepted key, so a shipped preset records a number here.

[[profile]]
id = "gemma-4-e4b-qat.llama-server"
artifact = { gguf_sha256 = "<pinned in models.toml>", template_sha256 = "<pinned>", runtime_build = "<pinned>" }
wire = "llama-server"
template = { system_role = "native", role_alternation = "strict" }
reasoning = { control = "template-kwarg", name = "enable_thinking", off = "yes" }
schema = { dialect = "gbnf", strict_enforced = "yes" }
```

## 5. A/B test: the general fallback preset against a native candidate preset (proposal) [I]

### 5.1 Question and hypotheses

For each (model, endpoint, step kind): does a preset built from the model's native conventions beat the general fallback preset
(today's uniform capsule), and if so, which single factor carries the gain? H1: yes for models of 8B and under on PICK and FILL, mostly
through the sampler and the trained prompt convention. H0 for hosted models of 27B and over: no difference beyond noise (§1.2). The test
runs inside cloud-first screening (D044, doc 50 §5) and reuses its battery, seeds and guards. It is one input to D048's tuning, whose
protocol and tuning and held-out splits doc 55 (draft) defines; until those splits exist, the existing suites act as the tuning split,
and a win changes a preset only after it holds on a held-out split (D048 item 4).

### 5.2 Arms

| Arm | What changes from U | Channel | Applies to |
| --- | --- | --- | --- |
| **U** (general fallback preset) | Nothing: today's capsule, strict schema or grammar, generic system line, thinking off (or the floor for mandatory models), the tool's sampler (T 0.6 for PICK and FILL) with other keys pinned as in the qualification record (presence 0) | As qualified | Every model; identical to battery S's arm, so records pair |
| **N** (native candidate preset) | The vendor's non-thinking or instruct sampler with every key pinned; the vendor's trained structured-output wording (Qwen's `answer` field and letter-only sentence, NVIDIA's "Response Formatting Schema" statement, IBM's JSON system sentence with the schema, instructions in gpt-oss's developer role); documented template rules (system placement, Gemma 26B/31B empty-thought prefill); same menus, schema, seeds and caps | As U | Every model with a documented convention |
| **S** | Sampler only | As U | After an N adoption |
| **C** | Prompt convention only | As U | After an N adoption |
| **Ch** | One forced tool whose parameters are our schema, in the model's native tool dialect | Tools | Families whose trained call syntax is not JSON, and only where the probe shows a forced `tool_choice` is honoured (not DashScope with thinking; not Kimi K2.6) |
| **E** | A tagged envelope instead of JSON | No-schema (P2, F1) and creative text | Creative text; models on endpoints without schema support. Creative-text items never go to hosts whose policies carry violent-content clauses (Groq, Cloudflare, ModelRun, Google; D047 item 3) |
| **FS1–FS6** | One change each from a base cell on the prompt-JSON channel: (1) menu as a JSON array instead of lettered lines, (2) markdown layout, (3) a paraphrased stem, (4) a requested `json` fence, (5) a custom answer tag, (6) system text folded into the first user turn | Prompt JSON | Every model; format robustness, reported only |
| **K** (endpoint check) | Arm U on the reference and on the candidate host | As U | Every free host before a free model is offered on it (D045) |

### 5.3 Controls

Same items and menu permutations (seeded by item and sample); cards off; same output caps except reasoning headroom for
mandatory-reasoning models, which both arms get; same grading (`score.py`); the endpoint pinned with fallbacks off and required
parameters on; a served-provider mismatch must be 0; parameters the endpoint drops are recorded, never silently removed from one arm
only; exact request bodies stored; the profile and preset hashes and a "factor changed" value on every record (B5).

### 5.4 Suites, k and calls

| Arm | Suites | k | Calls per model and endpoint |
| --- | --- | --- | --- |
| U | `pick-hard` without cards (30 menus); `fill` (12 items) | 3 | 90 + 36 = 126 (reused from battery S when seeds match) |
| N | Same | 3 | 126 |
| Preflight canary | 3 answerable menus plus 1 planted escape, U and N | 1 | 8 |
| FS1–FS6 | 20 stratified `pick-hard` items including at least 3 planted escapes | 1 | 120 |
| Decomposition (only after an N adoption) | S, C, and Ch or E where they apply | 3 | Up to 378 |

With U reused, a model and endpoint costs 254 new calls (380 without reuse; decomposition adds up to 378 more). At OpenRouter's 50 free
requests a day (the tool keeps to 45) that is about 6 days per model and endpoint; at 1,000 a day it is one day (doc 48 §6.0; the $10
credit decision in doc 50). On paid pinned endpoints it costs cents: battery S's 256 calls cost $0.001–0.025 per endpoint (doc 50 §5.2).

### 5.5 First-wave models

| Model | Endpoint(s) | N differs from U in | Notes |
| --- | --- | --- | --- |
| Qwen3.8-27B | OpenRouter `:free` (ModelRun fp4, ZDR, tier 0) and Groq Free (strict) | T 0.7, top_p 0.8, top_k 20, presence 1.5; the `answer` field convention; `preserve_thinking` false | `top_k` and `min_p` are not accepted on `:free` (recorded as dropped; tested on Groq); a clean test of presence 1.5 on a 27B; round 0's Z04–Z08 arms are U at k = 1 |
| Gemma 4 26B-A4B | coreweave/bf16 (strict) | T 1.0, top_p 0.95, top_k 64; empty-thought prefill | `:free` lacks `top_k` and a strict schema |
| gpt-oss-20b | Groq Free or akashml/fp4 (strict) | T 1.0, top_p 1.0; instructions in the developer role | Reasoning mandatory in both arms (effort low) |
| Nemotron 3.5 Lightning | coreweave/bf16 or deepinfra/bf16 (paid ZDR, strict; doc 48 O6) | T 1.0, top_p 0.95; the "Response Formatting Schema" statement in the user message | Thinking off in both arms. The Super and Ultra `:free` endpoints run under the NVIDIA API trial terms, which D047 item 2 excludes from every test |
| LFM2.5-2.6B | `:free` (tier 2: trains on and keeps prompts; synthetic suites only) | T 0.1, top_k 50, repetition 1.1 (where accepted) | Effort low and output headroom in both arms; the small-model floor |
| Qwen3-4B-Instruct-2507 | nscale via the HF router | T 0.7, top_p 0.8, top_k 20; the `answer` field | Doc 47's shortlist 1; enforcement at nscale [U] |
| Granite 4.2-3B | DeepInfra via the HF router (no schema flag: P2 and F1 only) | T 1.0, top_p 0.95; IBM's JSON system wording | Thinking off in both arms |
| Ministral 3 3B | `mistral/zdr` | T 0.05 (the card: below 0.1) | Calibration anchor with a local record; also tests K = 3 voting against near-greedy sampling. Mistral's hosted usage policy names military content, so under D047 these results are labelled and never make a preset; a preset for the local file comes from the local run |

Second wave, local, after doc 49: Gemma 4 E4B QAT (its N differs from U only in temperature, the vendor's 1.0 against the tool's 0.6,
because doc 44's top_k 64 and top_p 0.95 already came from the build defaults); Granite 4.1 3B (IBM JSON wording, and the `documents`
channel for EXPLAIN); MiniCPM5-2B (T 1.0, min_p 0; Ch with its XML dialect); Spark-X2.5-4B (T 1.0, top_k −1); Qwen3.5-4B (the vendor
preset without presence, which doc 46 already measured); NuExtract3 (FILL only: its template adapter against the uniform FILL); LFM2.5
locally (Ch with pythonic calls once llama.cpp #23838 is confirmed fixed).

### 5.6 Decision rule (pre-registered)

Per (model, endpoint, step kind); never pooled across step kinds or models.

1. **Guardrails for N, all required:** strict-schema conformance of at least 95% of calls on strict arms; no reasoning leak on
   thinking-off calls; planted escapes caught no fewer than in U; no false escapes; errors per 100 calls no more than U's plus 5.
2. **ADOPT N** if, for PICK, the net paired gain is at least +4 of 90 calls, an exact one-sided sign test on the discordant calls gives
   p ≤ 0.10, and `pick-hard` pass^3 is not lower than U's; for FILL, at least +3 of 36 all-fields-right calls, p ≤ 0.10, and
   whole-record pass^3 not lower. For example, 4 N-only wins and no U-only win give p = 0.0625 (adopt); 5 wins and 1 loss give p =
   0.109 (not adopted); 6 wins and 1 loss give p = 0.0625 (adopt).
3. **KEEP U** if the net difference is within ±2 calls (PICK) or ±1 (FILL), unless N uses at least 20% fewer tokens or less p90 latency
   at equal accuracy; then adopt only the saving factor, found by decomposition.
4. **REJECT N** if U wins by the adoption margin.
5. **Otherwise inconclusive:** park it and move the question to the 100-menu instrument (doc 44 §5.4) or the local run.
6. **After an adoption,** decompose and adopt the smallest factor set whose single-factor arm reproduces at least half of the bundle's
   net gain; otherwise adopt the bundle.
7. **Provenance:** an adoption on a single free host is provisional until a second host or the local run confirms it, and a preset
   changes only after the gain holds on the held-out split (D048 item 4) and, for a local model, on the local run (D044: the cloud
   screens, only the local run qualifies).
8. **FS arms are reported, not decided on:** a model whose maximum delta across FS cells is at least 20 points [provisional threshold]
   gets its rendering pinned and a warning in its CSV row.
9. **Penalties stay neutral for PICK and FILL (added at review).** D022 item 5 pins presence and frequency 0 and repeat 1 for Pick
   and Fill, and doc 55 §1.4 keeps that out of a harness preset's reach. N may carry a vendor's penalty (Qwen's presence 1.5, Liquid's
   repetition 1.1) as a measurement, but a win that the decomposition attributes to a penalty is reported, not adopted, unless the
   owner amends D022 item 5; if the penalty cannot be separated, N is re-run with neutral penalties before any adoption.

Resolution: 90 paired calls reveal effects of about 5 points or more. Doc 46's presence-penalty effect (8 of 360 calls, about 2%)
would be missed, so sampler micro-effects belong to the 100-menu instrument, not to this screen.

### 5.7 Tool changes needed (proposal-only)

- `--profile <id>` and `--preset <id>` reading the files of §4.10 (D048 Consequences: preset loading in `tools/local-qual`), and `--arm
  U|N|S|C|Ch|E|FS1…FS6` (or the pending `--variant` flag extended).
- Records carry `profile_id`, `profile_sha`, `preset_id`, `preset_sha`, `arm`, `factor_changed`, the exact extras sent, dropped
  parameters, the outcome enum and reasoning tokens.
- The `--resume` key gains backend, base URL, route pin, thinking mode, sampler, extras, profile and preset hashes and the suite hash
  (K8: today it is model, suite, item, condition, variant and sample).
- `score.py` gains the paired comparator (discordant counts, exact sign test), FS statistics (maximum delta, SD, decode-failure share),
  agreement with a reference arm, an all-calls schema-pass denominator and the conformant-versus-substantive split (K4, K16).
- The Ch arm refuses to run where the probe says a forced `tool_choice` is rejected or ignored.
- Doc 48 §6.0's free-only safety guards are unchanged.

### 5.8 What a result would change

- **N adopted for a model:** the winning native knobs enter that model's tuned preset for that step kind (D048), and the CSV's
  `schema_mode_recommended` and `sampler` cells record the measured values; doc 44 and 47's bars are unchanged.
- **No gain at 27B and above:** those models' presets keep the fallback's choices; only the profile's wire facts differ.
- **Ch wins for a non-JSON family:** a `ForcedTool` schema mode in that family's presets; COMPOSE tool rounds reuse it.
- **E wins for creative text:** the creative-text step returns tagged plain text (a doc 38 fold); FILL is unaffected.
- **A free host fails the endpoint check:** no free model is offered on it (D045), whatever the model's qualification elsewhere.

## 6. Design-gap candidates and folds

### 6.1 Design-gap candidates (listed, not filed in `docs/design-gap-requests/`) [I]

1. **Profiles beside D048's presets:** the split between probed facts (profile) and tuned choices (preset), the layering and the
   tri-state evidence; for doc 55 to settle with the preset format (D048's open parts), extending D021's adapter and D022's Model
   Manager.
2. **Admission tolerance on the no-schema transport:** which deviations are non-blocking (T1), against doc 21 §8.2's "schema violations
   are refused".
3. **Ambiguous answers:** two envelope-shaped JSON values in one reply is a blocking `AmbiguousAnswer` (T2).
4. **Error taxonomy:** `ProviderFailure`, `InvalidAnswer` and findings, and which outcomes count against model accuracy, endpoint
   dependability or neither (§4.7).
5. **Mandatory-reasoning endpoints:** PICK and FILL at the floor level with reasoning-sized caps and cost preview; plans that assume
   thinking off where it cannot be (§6.4).
6. **An untrusted-text control-token table** for mission content across model families (H18; doc 21 §9.3).
7. **Tracking re-authored third-party harness tests:** `docs/porting/upstream-test-map.csv` is scoped to engine tests; Hermes-, Terminus-,
   verifier- and Vibe-derived fixtures need a home (`reference` rows or a separate third-party fixture map).
8. **The schema compiler:** the portable subset by construction; per-dialect normalisers restating stripped constraints; a lint (no
   `default`, identifier keys, no `$ref`, bounded depth); canonical serialisation (H6, B11, Z13, K14).
9. **Repair capsule shape:** a fresh single-turn capsule, one finding at the tail, no reasoning replay; multi-turn only for COMPOSE and
   creative text (M3, V10, Q14).
10. **"Check this endpoint":** differential verification, a periodic canary and a "last verified" badge (K1–K4, K20; extends doc 48 §7.4
    item 4).
11. **Layout variants per profile** must keep the static prefix byte-stable and be qualified before shipping (M14).
12. **Resume and cassette keys** hash the full canonical request, including profile, endpoint pin, sampler and extras (K8).
13. **The workflow runtime as a sans-IO reducer** with determinism contract tests (V1, V2).
14. **The creative-text envelope:** plain bounded text or a tagged envelope versus a JSON-wrapped string (T9).
15. **PICK soft scores from logprobs,** with a per-tokenizer check that menu letters are single tokens (M12).
16. **Vendor penalties against D022 item 5** (added at review): whether a measured win from a vendor's presence or repetition penalty
    may ever enter a PICK or FILL preset (§5.6 rule 9); today it may not.

### 6.2 Doc 38 folds

- **§3.3 (capsule):** exemplars and hints filtered to the step's available options (Q3); the repair tail after the restated schema (Q14,
  M3); stated versus check-only constraints part of the capsule hash (M6); system role and alternation taken from the profile (B10, Z11).
- **§4.2 (journal):** `Discarded` and `Abandoned` records with typed causes (V19); intake normalisations and admission flags logged
  (§4.5); the raw failed reply kept as data; request-body and profile hashes per record (H25, K21).
- **§4.5 (fan-out):** K candidates settle in index order and stop early only by a deterministic rule (M2); length-prefixed,
  domain-tagged seed derivation (V18).
- **§4.6 (budgets and timeouts):** transport retries separate from repairs (B14, H14); idle and lifetime stream watchdogs (Q17);
  `Truncated` and `ThinkingExhausted` as typed outcomes (H10).
- **§4.7 (Rust sketch):** the reducer shape with derived pending work (V1, V4).
- **§6.2 (definition compiler):** reject steps whose fixed capsule cannot fit the smallest qualified window (V11); the schema dialect
  lint; an empty allowed-tool set is a load error (M22).
- **§6.4 (testing):** a scripted fake endpoint (T19) or scripted command sequences (V17); one golden first capsule per step kind;
  prefix-bytes tests (V6); fixtures per run state with a sentinel leak test (V15); golden-render tests against each model's own template
  (B3).
- **§9 (external agents):** idempotent `decide` inputs: identical bytes replay, different bytes conflict (V3).

### 6.3 Doc 25 folds

- **§4.4 (prompt contract):** one bare JSON object, no wrapper tags, no fence requests; menus and slot specs rendered as JSON by default;
  the format restated at the end; examples never contain a live option (B2, T11).
- **§7.2 (repair):** one typed finding with recomputed allowed values and a short excerpt around a JSON error position; stop on a
  recurring typed finding (M4, M10, T4).
- **§7.3 (choosing among candidates):** admit before voting; canonical option identity after un-permuting; logprob margins where
  available; no ROUGE-style consensus for creative text (M8, M12).
- **§10.2 (fallback ladder):** the closest candidate as a card; the best-attempt package as the payload of "retry with another setup"
  (M5, M10).
- **§11.2 (matrix):** the profile factor, the FS arm and a "factor changed" column on every comparison (B5; §5).

### 6.4 Findings for other sibling docs (reported, not fixed)

- **Doc 48 and anywhere BFCL's DeepSeek gap is quoted as a call-path effect:** it mixes call path and thinking (B5).
- **Docs 47 and 53:** quote BFCL figures only with handler, mode, thinking and sampler (B16); BFCL's prompt-mode rows understate
  JSON-friendly small models relative to a JSON harness (B2).
- **Docs 48 and 50:** GLM-5.3, GLM-5.3-Flash and Kimi K3 cannot switch thinking off; any arm planned at effort `none` for them must run
  at `low` with reasoning headroom (Z7). Doc 48 §7.1 already notes that mandatory models reject `none`.
- **Docs 46 and 47:** Qwen3.6's `generation_config.json` holds only the thinking sampler, so a vLLM host that applies it gives
  non-thinking requests the thinking sampler unless every key is pinned.
- **Doc 53:** its header says no D044 record exists; D044 is in the decisions index as of 2026-09-28.
- **`tools/local-qual/run.py`:** the `--resume` key omits backend, base URL, thinking mode, sampler and extras (K8).
- **Mistral rows:** the hosted API accepts consecutive user messages; the Hugging Face template raises on them (V10).

## Open questions

1. Does OpenRouter's Qwen3.8-27B `:free` endpoint enforce a strict `json_schema` (it lists `structured_outputs` but not
   `response_format`)? Doc 48's canary Z01 answers it.
2. Can Nemotron 3 Super's reasoning be fully switched off on its `:free` endpoint?
3. What reasoning effort does Mistral's hosted API apply when the field is omitted?
4. Do the local GGUF templates of Ministral 3 and Mistral Small 4 enforce role alternation?
5. Does `llama-server` forward Granite's `documents` kwarg through `chat_template_kwargs`, and does the trained grounding block beat
   plain cards for EXPLAIN?
6. Does OpenRouter report the upstream provider's own prompt-token counts on `:free` endpoints (needed for K11)?
7. Where, if anywhere, are Hermes Agent's per-model tool-call parsers (a separate Nous RL repository)?
8. Are A–G and X single tokens in every candidate tokenizer (needed for logprob margins)?
9. Is 20 points the right FS threshold for pinning a per-model rendering?
10. Where should re-authored third-party harness tests be tracked (§6.1 item 7)?
11. Should the E (tagged envelope) arm for creative text run before or after doc 49's local shortlist?
12. How often should a free endpoint be re-verified, and how much of its daily quota may the canary use?

## Sources

### Model cards and vendor documentation (read 2026-09-27 and 2026-09-28)

- Qwen: <https://huggingface.co/Qwen/Qwen3.5-4B> (and `/blob/main/chat_template.jinja`); <https://huggingface.co/Qwen/Qwen3.5-2B>;
  <https://huggingface.co/Qwen/Qwen3.5-27B>; <https://huggingface.co/Qwen/Qwen3.5-35B-A3B>; <https://huggingface.co/Qwen/Qwen3.6-35B-A3B>
  (and `/blob/main/generation_config.json`); <https://huggingface.co/Qwen/Qwen3.6-27B>; <https://huggingface.co/Qwen/Qwen3.8-27B> (and
  `chat_template.jinja`, `generation_config.json`); <https://huggingface.co/Qwen/Qwen3.8-Flash-Next>;
  <https://recipes.vllm.ai/Qwen/Qwen3.8-27B>; <https://qwen.ai/blog?id=qwen3.8>; <https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507>;
  <https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507>; <https://qwen.readthedocs.io/en/latest/framework/function_call.html>;
  <https://huggingface.co/Qwen/Qwen3-Coder-480B-A35B-Instruct>; <https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct>;
  <https://huggingface.co/Qwen/Qwen3-Coder-Next>; <https://unsloth.ai/docs/models/qwen3.5>; <https://unsloth.ai/docs/models/qwen3.6>;
  <https://unsloth.ai/docs/models/tutorials/qwen3-coder-how-to-run-locally>
- PrismML and NuMind: <https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf> (and `/blob/main/KNOWN_ISSUES.md`);
  <https://huggingface.co/numind/NuExtract3> (and `chat_template.jinja`); <https://huggingface.co/numind/NuExtract3-GGUF>
- Google: <https://huggingface.co/google/gemma-4-E4B-it>; <https://huggingface.co/google/gemma-4-26B-A4B-it>;
  <https://huggingface.co/google/gemma-4-31B-it>; <https://ai.google.dev/gemma/docs/core/prompt-formatting-gemma4>;
  <https://ai.google.dev/gemma/docs/capabilities/text/function-calling-gemma4>; <https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api>;
  <https://arxiv.org/html/2607.02770>; <https://developers.googleblog.com/bring-state-of-the-art-agentic-skills-to-the-edge-with-gemma-4/>;
  <https://ai.google.dev/gemini-api/docs/gemini-3>; <https://ai.google.dev/gemini-api/docs/structured-output>;
  <https://ai.google.dev/gemini-api/docs/function-calling>; <https://ai.google.dev/gemini-api/docs/thinking>;
  <https://ai.google.dev/gemini-api/docs/prompting-strategies>; <https://ai.google.dev/gemini-api/docs/whats-new-gemini-3.5>;
  <https://storage.googleapis.com/deepmind-media/gemini/gemini_3-1_flash-lite_model_evaluation.pdf>;
  <https://storage.googleapis.com/deepmind-media/gemini/gemini_3-5_flash-lite_model_evaluation.pdf>;
  <https://storage.googleapis.com/deepmind-media/gemini/gemini_3-8_flash_model_evaluation.pdf>; <https://adk.dev/2.0/>;
  <https://adk.dev/agents/models/google-gemma/>; <https://docs.vllm.ai/projects/recipes/en/stable/Google/Gemma4.html>
- Meta and Microsoft: <https://dev.meta.ai/llama/docs/model-cards-and-prompt-formats/llama4/>;
  <https://dev.meta.ai/llama/docs/model-cards-and-prompt-formats/llama3_1/>;
  <https://dev.meta.ai/llama/docs/model-cards-and-prompt-formats/llama3_2/>; <https://ogx-ai.github.io/blog/from-llama-stack-to-ogx>;
  <https://huggingface.co/meta-models/Muse-Glimmer-30B>; <https://dev.meta.ai/docs/models>;
  <https://huggingface.co/microsoft/Phi-4-mini-instruct>; <https://huggingface.co/microsoft/phi-4>;
  <https://huggingface.co/microsoft/Phi-4-reasoning-plus>
- NVIDIA: <https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8>;
  <https://docs.nvidia.com/nemotron/0.1.0/usage-cookbook/Nemotron-3-Super/OpenScaffoldingResources/README.html>;
  <https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16>;
  <https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16> (and `/blob/main/agentic_coding_benchmarks.png`);
  <https://developer.nvidia.com/blog/nvidia-nemotron-3-5-lightning-delivers-fast-accurate-specialized-task-execution-for-long-running-agents/>;
  <https://blogs.nvidia.com/blog/nemotron-lightning-switchyard-rtx-dgx/>;
  <https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16>;
  <https://huggingface.co/blog/nvidia/nemotron-3-nano-evaluation-recipe>;
  <https://docs.nvidia.com/nemo/datadesigner/dev-notes/structured-outputs-from-nemotron>;
  <https://huggingface.co/nvidia/Nemotron-Terminal-8B>
- IBM: <https://huggingface.co/ibm-granite/granite-4.2-3b>; <https://huggingface.co/ibm-granite/granite-4.2-8b>;
  <https://huggingface.co/blog/ibm-granite/granite-4-2>; <https://huggingface.co/ibm-granite/granite-4.1-3b>;
  <https://github.com/ibm-granite/granite-4.0-language-models/blob/main/Granite%204.0%20Prompt%20engineering%20guide%20v2.md>;
  <https://huggingface.co/ibm-granite/granite-4.0-h-tiny>; <https://huggingface.co/blog/ibm-granite/granite-libraries>;
  <https://framework.beeai.dev/modules/agents/requirement-agent>; <https://docs.mellea.ai/concepts/generative-programming>
- Liquid, OpenBMB, SparkLLM, dots: <https://huggingface.co/LiquidAI/LFM2.5-2.6B>; <https://www.liquid.ai/blog/lfm2-5-2-6b>;
  <https://docs.liquid.ai/examples/agent-harnesses>; <https://docs.liquid.ai/lfm/key-concepts/tool-use>;
  <https://docs.liquid.ai/deployment/on-device/llama-cpp>; <https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct>;
  <https://huggingface.co/LiquidAI/LFM2.5-8B-A1B>; <https://github.com/Liquid4All/docs/pull/126>;
  <https://huggingface.co/openbmb/MiniCPM5-2B>; <https://huggingface.co/XHToken/Spark-X2.5-4B>; <https://github.com/XHToken/Spark-X2.5>;
  <https://huggingface.co/dots-studio/dots3-note-prev>
- OpenAI, DeepSeek, Z.ai, Moonshot, MiniMax: <https://github.com/openai/gpt-oss>; <https://github.com/openai/harmony>;
  <https://developers.openai.com/cookbook/articles/openai-harmony>; <https://arxiv.org/html/2508.10925v1>;
  <https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash>;
  <https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blob/main/encoding/README.md>;
  <https://api-docs.deepseek.com/guides/thinking_mode/>; <https://api-docs.deepseek.com/guides/tool_calls/>;
  <https://api-docs.deepseek.com/news/news260424/>; <https://huggingface.co/zai-org/GLM-5.3-Flash>;
  <https://huggingface.co/zai-org/GLM-5.3>; <https://docs.z.ai/guides/capabilities/thinking-mode>; <https://docs.z.ai/devpack/overview>;
  <https://huggingface.co/moonshotai/Kimi-K2.6>; <https://huggingface.co/moonshotai/Kimi-K3>;
  <https://platform.kimi.ai/docs/guide/use-kimi-k2-thinking-model>;
  <https://platform.kimi.ai/docs/guide/use-json-mode-feature-of-kimi-api>;
  <https://huggingface.co/moonshotai/Kimi-K2-Instruct/blob/main/docs/tool_call_guidance.md>;
  <https://huggingface.co/MiniMaxAI/MiniMax-M3>; <https://platform.minimax.io/docs/guides/text-m3-function-call>;
  <https://www.minimax.io/news/why-is-interleaved-thinking-important-for-m2>
- Mistral, Nous, inclusionAI: <https://huggingface.co/mistralai/Mistral-Small-4-119B-2603>; <https://mistral.ai/news/mistral-small-4/>;
  <https://docs.mistral.ai/studio-api/conversations/structured-output/custom>;
  <https://docs.mistral.ai/studio-api/conversations/advanced/prompt-caching>;
  <https://huggingface.co/mistralai/Ministral-3-3B-Instruct-2512>; <https://mistral.ai/news/devstral-2-vibe-cli/>;
  <https://huggingface.co/mistralai/Devstral-2-123B-Instruct-2512>; <https://huggingface.co/NousResearch/Hermes-4.3-36B>;
  <https://huggingface.co/NousResearch/Hermes-4-14B>; <https://hermes-agent.nousresearch.com/docs/>;
  <https://huggingface.co/inclusionAI/Ling-3.0-flash>; <https://recipes.vllm.ai/inclusionAI/Ling-3.0-flash>

### Harness repositories at the studied commits

- <https://github.com/NousResearch/hermes-agent/tree/04ea129bbf84a7b8905eaab9ee575ff345a8f464> (MIT)
- <https://github.com/ShishirPatil/gorilla/tree/6ea57973c7a6097fd7c5915698c54c17c5b1b6c8/berkeley-function-call-leaderboard> (Apache-2.0)
- <https://github.com/harbor-framework/harbor/tree/3c82380859d187957cfd5cd64802b076d9779550> (Apache-2.0)
- <https://github.com/generative-computing/mellea/tree/1276bf6a5fb2e29b19e089776855217e6c073493> (Apache-2.0)
- <https://github.com/i-am-bee/beeai-framework/tree/08c1edf6c4a94eacf39f18a2e94a8a8c935e1c04> (Apache-2.0)
- <https://github.com/mistralai/mistral-vibe/tree/7c19608af06f6c61d63f8f7a5c3430da73fba2ab> (Apache-2.0)
- <https://github.com/zai-org/ZCode/tree/29628c9acdb81b703bbd4080c207a0e7ce5e276e> (Apache-2.0)
- <https://github.com/MoonshotAI/kimi-code/tree/be7d5f5fea7800778e4660cd5f36780ba783bddd> (MIT)
- <https://github.com/QwenLM/qwen-code/tree/3f5ae3ffeb7264f236038eef91256a3310361d3c> (Apache-2.0)
- <https://github.com/google-gemini/gemini-cli/tree/2fe7c2d3f065dc40ad573d50b2091116f8a4aa18> (Apache-2.0)
- <https://github.com/MoonshotAI/K2-Vendor-Verifier/tree/0bc5061be1a7b5667c2ec71a546a6b1c9ff5af9a> (no licence file)
- <https://github.com/MoonshotAI/Kimi-Vendor-Verifier/tree/66092cf444c97356c0e11c5078c67116390615d9> (MIT)

### Other harnesses and frameworks referenced

<https://github.com/QwenLM/Qwen-Agent> (@31a4d36); <https://github.com/google/adk-python>;
<https://github.com/google-ai-edge/LiteRT-LM>; <https://github.com/google-ai-edge/gallery>; <https://github.com/ogx-ai/ogx>;
<https://github.com/NVIDIA/NeMo-Agent-Toolkit>; <https://github.com/NVIDIA-NeMo/Evaluator>; <https://github.com/NVIDIA-NeMo/Gym>;
<https://github.com/NVIDIA-NeMo/Skills>; <https://github.com/MiniMax-AI/Mini-Agent>; <https://github.com/ibm-granite/granite-io>;
<https://github.com/openai/codex>; <https://github.com/SWE-agent/mini-swe-agent>; <https://github.com/OpenHands/OpenHands>;
<https://github.com/openclaw/openclaw>; <https://github.com/anomalyco/opencode>; <https://github.com/badlogic/pi-mono>;
<https://github.com/UKGovernmentBEIS/inspect_ai>; <https://github.com/PrismML-Eng/Bonsai-demo>; <https://github.com/numindai/nuextract>

### Benchmarks, leaderboards and evaluations

<https://gorilla.cs.berkeley.edu/data_overall.csv>; <https://gorilla.cs.berkeley.edu/data_format_sensitivity.csv>;
<https://gorilla.cs.berkeley.edu/blogs/17_bfcl_v4_prompt_variation.html>;
<https://artificialanalysis.ai/articles/endpoint-accuracy-index>; <https://artificialanalysis.ai/methodology/endpoint-accuracy-index>;
<https://artificialanalysis.ai/models/qwen3-8-27b>; <https://artificialanalysis.ai/articles/gemma-4-everything-you-need-to-know>;
<https://artificialanalysis.ai/articles/nemotron-3-5-lightning-launch>; <https://pinchbench.com/>;
<https://neuralnoise.com/2026/harness-bench-wip/>; <https://github.com/Vietnoirien/oaken-bench>;
<https://www.infralovers.com/blog/2026-07-14-local-model-ai-coding-tools-benchmark/>; <https://www.vals.ai/models/minimax_MiniMax-M3>;
<https://labs.scale.com/leaderboard/swe_bench_pro>;
<https://github.com/Aider-AI/aider/blob/main/aider/website/_data/polyglot_leaderboard.yml>;
<https://www.nist.gov/news-events/news/2026/05/caisi-evaluation-deepseek-v4-pro>; <https://www.liquid.ai/blog/ifstruct-v1.0>;
<https://github.com/Liquid4All/ifstruct>; <https://github.com/MikeVeerman/tool-calling-benchmark>;
<https://kgptalkie.com/tutorials/llm-benchmarking/granite-4-2-vs-gemma-4-vs-qwen-3-8-benchmark>;
<https://www.mindstudio.ai/blog/minicpm-5-2b-sub-agent-model>; <https://kaitchup.substack.com/p/boosting-agentic-coding-with-llm>
(paywalled); <https://regolo.ai/harness-engineering-for-qwen3-8-27b-a-technical-guide-to-pi-opencode-and-kilo-code/>

### Papers

- Qwen3-Coder-Next technical report: <https://arxiv.org/abs/2603.00729>
- Mavrin, "In harmony with gpt-oss": <https://arxiv.org/abs/2604.00362>
- JSONSchemaBench: <https://arxiv.org/abs/2501.10868>
- Structured Output Benchmark: <https://arxiv.org/abs/2604.25359>
- s1 (budget forcing): <https://arxiv.org/abs/2501.19393>
- DeepSeek V4: <https://arxiv.org/abs/2606.19348>
- MiniMax M2 series: <https://arxiv.org/abs/2605.26494>
- gpt-oss model card: <https://arxiv.org/abs/2508.10925>

### Issues, pull requests and discussions

- llama.cpp (<https://github.com/ggml-org/llama.cpp>): issues 19051, 20164, 20260, 20345 (fix commit 62b8143), 20668, 20703, 23838,
  24807, 28509, 29006; pull requests 20171, 21326, 26608, 27383, 27868, 28511.
- vLLM (<https://github.com/vllm-project/vllm>): issues 37359, 39103, 41240, 48931; pull requests 56994, 58072.
- Others: anomalyco/opencode issues 24316 and 24130; google/adk-python issue 5650; ollama/ollama issue 15241; googleapis/js-genai
  issue 1581; maximhq/bifrost issue 7287; BerriAI/litellm issue 22889; dograh-hq/dograh issue 689; microsoft/Foundry-Local issue 116;
  PrismML-Eng/Bonsai-demo issue 183; PrismML-Eng/llama.cpp issues 87, 247 and 283; pydantic/pydantic-ai issue 4762;
  earendil-works/pi issue 8706; QwenLM/Qwen3.8 issue 145; mistralai/mistral-vibe discussion 680.
- Hugging Face discussions: unsloth/Qwen3.6-35B-A3B-GGUF 5; nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8 6;
  nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16 3; zai-org/GLM-5.1 26; mistralai/Mistral-Small-4-119B-2603 13;
  <https://discuss.huggingface.co/t/gemma-4-bug-fixes-and-research-request/176979>.
- Third-party write-up: <https://www.orcarouter.ai/blog/deepseek-v4-1-tool-calling-vllm>.

### Sibling docs and records

Docs 02, 10, 11, 12, 14, 21, 22, 25, 38, 40, 43, 44, 46, 47, 48, 50, 53 and 55 (draft) in `docs/research/`; D008, D009, D021,
D022, D023, D025, D026, D037, D044, D045, D046, D047 and D048 in `docs/decisions/`; `tools/local-qual/run.py`.

## Verification notes

### 2026-09-28, author checks at write-up

- **Re-checked at the source:** the K2 Vendor Verifier README (K2-0905 schema accuracy 100% for Moonshot, Fireworks and Groq, 76.00%
  vLLM, 73.13% SGLang, 71.96% Together, 84.47% Nebius; Groq F1 69.52%, Nebius 50.60%; bars 80% and 73%; 4,000 requests, 50% published);
  BFCL's format-sensitivity file (Phi-4 81.5 and SD 23.34, Llama-3.1-8B 74.5 and 29.1, Gemma-3-4B 69.5 and 23.67, MiniCPM3-4B 68.0 and
  16.55, Qwen3-4B-2507 18.0 and 5.22); the Lightning card's text (SWE-bench Verified 51.56, Terminal-Bench 2.1 24.58, T 1.0 and top_p
  0.95). The card's per-harness numbers exist only in its chart image, which the fetch tool cannot read, so §1.1 keeps them as read in
  the study pass and marks them [V-vendor, chart].
- **Data file:** `data/model-profiles.csv` was generated by a script, parses with Python's `csv` module, and has 44 rows and 9 columns,
  all non-empty.
- **Decision records that landed during write-up:** D045, D046, D047 and D048 (all recorded 2026-09-28) were read before finishing. §4
  and §5 were aligned with D048 (profiles hold probed facts; D048's presets hold tuned choices; the uniform capsule is the general
  fallback preset; a held-out split confirms any win), and the model rows, the CSV and §5.5 with D045 and D047 (Google AI Studio's
  free tier is never a preset; the NVIDIA API trial and Z.ai's own service are not used; Mistral's hosted results and Muse-Glimmer are
  synthetic-only and never presets; creative-text items stay off hosts with violent-content clauses). Doc 55 is cited as a draft; it
  was not in the tree to read.
- **Not verified at the source:** the Qwen3.8-Max blog (rendered by JavaScript; read through search snippets); the dots3 benchmark page
  (search snippet); Kaitchup's harness comparison (paywalled); Regolo's DeepSWE figures (no primary data found); the BeeAI reliability
  blog (HTTP 502 at research time); whether Mistral's local GGUF templates enforce alternation.
- **Corrections relative to the study notes, applied in the text:** BFCL's DeepSeek gap is confounded with thinking (B5); Qwen3-30B-2507's
  FC gain is multi-turn and agentic (B4); Mistral's hosted API accepts consecutive user turns (V10); Gemini CLI switches silently under
  auto-routing (Q21); Hermes's neutraliser covers Harmony only and its tree has no parser table (§3.1); on configured qwen3.8 routes Qwen
  Code omits an unsupported effort silently and only legacy routes clamp (Q8); only the five-identical-calls threshold is tied to a
  server limit (Q16); the K2 Vendor Verifier's F1 is not in its code (K2).
- **Counts:** §3.0's per-harness tallies come from the study pass (a row counts once per harness); the lesson lists condense the
  studies (Hermes 28, BFCL 17, Terminus 21, Mellea and BeeAI 25 plus a folded paragraph, Vibe 27, ZCode 24, Qwen Code 25, verifier 22).
- **Hygiene:** searched this file and the CSV for local paths, user names and private project names before finishing; none found.

### 2026-09-28, independent review

- **Method.** The twelve harness repositories were re-read at the pinned commits (every clone's HEAD matched the commit in §3.0);
  vendor pages, papers and leaderboard files were re-fetched; the CSV was re-parsed; every URL in this file and the CSV (250 unique)
  was requested once (all resolved; two first answered HTTP 429 and resolved on retry). No model was run and no keyed API called.
- **Code claims confirmed at the pinned commits (19):** H1 (`MINIMUM_CONTEXT_LENGTH = 64_000`), H14 (the 9-call fan-out note), H15
  (400 characters, 60-character window, 5 repeats, 16,000 on the stop path), H18 (Harmony-only pattern; the test asserts
  `<|im_start|>` survives), H24 (CJK about one token, other text UTF-8 bytes / 4), H26 (default auxiliary model Nemotron 3 Ultra
  `:free`; the fast tier excludes `:free`); B6 (240 + 884 irrelevance items against 16 relevance), B8 (temperature 0.001), B15
  (MiniCPM3 stop ids); T4, T13, T15, T16 (repair and truncation wording, the 1,000,000-turn default, the 2026-05-06 sampler change,
  the 10,000-byte cut); M25 (Ollama, Granite 4.2 3B, `loop_budget=2`); V10 (Vibe 2.10.0, 2026-05-19), V11, V21, V22; Z6, Z7; Q11,
  Q16, Q17, Q19; K3, K4, K20 and the K2-0905 schema-accuracy table in §1.1; K2VV has no licence file, its successor and Hermes Agent
  and kosong are MIT, Vibe has no NOTICE file.
- **Vendor and third-party claims confirmed at the source (14):** the Qwen3.8-27B card (both samplers, efforts `xhigh`/`medium`/`low`,
  `preserve_thinking` on by default, Claude Code for SWE-bench Pro and NL2Repo); Qwen3.6 and Qwen3.8 `generation_config.json` (thinking
  sampler only); the Qwen3.6 card's SkillsBench row (4.4 against 28.7, OpenCode); Gemini's thinking page (3.7 and 3.8 Flash accept only
  low, medium, high) and Gemini 3 page ("`minimal` does not guarantee that thinking is off"; keep temperature 1.0); the LFM2.5-2.6B
  card; the MiniCPM5-2B card (`min_p` 0 and the llama.cpp warning); the Granite 4.2 card and blog (sampler, `low_effort` text, 12
  scaffolds, 3B without agentic RL); the Mistral Small 4 card (`none`/`high`, temperatures); the Lightning card, template and chart
  image (every per-harness bar in §1.1 matches); the AA Endpoint Accuracy article; Qwen3-Coder-Next Table 5 (column order xml, json,
  Claude Code, Qwen Code; every figure in §1.1 and T9 matches); Mavrin (60.4 against 60.7; 3.8% to 58.8% when tools moved to the
  system message); the gpt-oss card (tau-bench 67.8 to 49.4, SimpleQA 78.2% and 91.4%, 0.780); BFCL's format-sensitivity file (the
  §1.1 max deltas and every B2 cell, including Gemma-3-4B 62.0 to 41.5 with markdown); Aider's polyglot rows.
- **Corrections applied:** Qwen3-Coder-Next trained on 21 templates, not "about 20" (§1.2, §2.1, CSV); "designed for harnesses like
  OpenClaw and Hermes Agent" is NVIDIA's blog, not the Lightning card (§1.4, §2.4, CSV), and the card does not name an Ultra
  orchestrator (CSV reworded to the blog's Switchyard routing); `thinking_token_budget` is on neither the Lightning card nor its
  template (CSV marked [U]); AA's reference is "the reference", not "self-hosted"; the K2 Vendor Verifier is now labelled
  [V-vendor] as Moonshot's own test (TL;DR, §1.1), as are Moonshot's same-model pair and MiniMax's vendor figure (§1.1, §1.2);
  citations added or corrected for H14, Z7, Q11 and Q17; BFCL's "29 local handlers" restated as 29 files (27 handler modules);
  the gpt-oss "weak instruction hierarchy" wording made neutral (CSV); the legend now explains combined CSV labels.
- **Consistency with decisions and doc 55:** doc 55 reached the tree during review, so §4.1 records where it governs (name, JSON file
  format, no prompt text in a harness preset, neutral Pick and Fill penalties). §4.3 and H20 now select prompt variants by id, never as
  preset text; §4.10's syntax is marked illustrative; §5.6 rule 9 and §6.1 item 16 stop a vendor penalty (Qwen's presence 1.5,
  Liquid's repetition 1.1) from entering a PICK or FILL preset without an amendment to D022 item 5.
- **Product scope and token economy:** every ADOPT or ADAPT lesson stays inside formats, prompting, decoding, repair, context handling
  and model adapters; general tools, code execution, MCP-client roles, sub-agents and silent fallbacks remain rejected (§4.9). One
  change: the endpoint re-check canary (K20, §4.8) was automatic at session start; it is now opt-in with its call count shown, since
  it spends the user's own free allowance.
- **Not re-verified at review:** V27's exact `.expect()`/`.unwrap()` counts; §3.0's per-harness tallies; the GitHub `main` handler
  count for BFCL; the Qwen3.8 `high` → HTTP 500 report; Mistral's template raising on other effort values.
- **Hygiene:** both files re-searched for local paths, user names and private project names; none found. The CSV parses with
  Python's `csv` module: 44 data rows, 9 columns, no empty cell, and every cell from `vendor_harness` to `pitfalls` opens with an
  epistemic label.
