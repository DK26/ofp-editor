# Prior Art: AI Assistants for Game Content Creation and Mission Editors

> Research note for **ofp-editor**, a standalone Rust re-implementation of the *Arma: Cold War Assault* (CWA, formerly *Operation Flashpoint: Cold War Crisis*, 2001) Mission Editor with a built-in AI "harness agent".
> Researched 2026-09-26. Audience: contributors and LLM coding agents. This file is meant to stand alone.
> Sibling docs you may also want: `04-mission-data-model-and-formats.md` (mission files), `10-`/`11-`/`12-` (agent harness internals).

Epistemic tags used below:

- **[V]**: verified against the cited primary source on 2026-09-26.
- **[V2]**: verified only via a secondary source (press, aggregator, or search-result excerpt of the primary).
- **[I]**: inferred by the author from verified facts. It is reasoning, not a sourced fact.
- **[U]**: unknown or unverified. Treat it as a hypothesis.

**Method and limits.** Live web fetches plus reading the pinned local reference clones. Several pages returned 403, 402 or truncated bodies (PC Gamer, TechRadar, Nexus Mods news, Unreal news, Steam news). For those we cite secondary coverage and mark it [V2]. The web-search budget ran out partway through, so a few topics got less coverage: Arc Raiders and other TTS-voice controversies, Bohemia's own AI policy, and Godot's first-party stance. They are listed under Open questions. Quotes come from fetched pages. Star counts and download counts are snapshots.

---

## TL;DR

- **Recommendation:** build the harness as a **typed, undoable command layer** that the GUI and the LLM share, run in a **Plan → Preview diff → Apply** loop. Put a **deterministic mission generator** at the core and use the LLM for intent parsing, template filling and **flavor text** (briefings, barks, radio chatter). Keep every AI output as **structured data with provenance tags**. Make the whole feature **opt-in, local-first, bring-your-own-model, and never auto-publish**.
- Engine vendors have converged on this shape. Unity AI has **Ask / Plan / Agent** modes, permission prompts, undo, and metadata tags on AI assets [V]. Roblox Studio has a Planning Mode that produces a reviewable task manifest, a self-testing playtest agent, and a built-in MCP server [V]. Unreal 5.8 ships an **experimental** in-editor MCP server with typed toolsets [V].
- The riskiest pattern in the wild is letting the model **run arbitrary code** inside the editor. Blender MCP's `execute_blender_code` does this, and its own docs say "ALWAYS save your work" and warn that the socket has "no authentication" [V]. Our LLM must never emit raw SQF/SQS or `mission.sqm` text that we execute or save without parsing and validating it.
- The best-received writing tool is **Ubisoft Ghostwriter**. It narrows scope to **barks**, the incidental NPC one-liners. The tool offers **two candidates**, the writer accepts, edits or discards, and those choices feed back into the models. It explicitly excludes cinematics and lore [V]. It still drew writer backlash ("trojan horse", "editing is slower than writing") [V2; quotes unverified on re-check]. We should copy its scope discipline and its accept/edit/reject loop.
- **Deterministic generators are the closest domain prior art.** BriefingRoom for DCS (C#, GPL-3.0) runs a 9-stage, database-driven pipeline with retries and fallbacks, writes shareable template files, has a CLI, and puts all units into the mission file with no runtime spawning, so the result can be edited in the stock editor [V]. DCS Liberation and Retribution (Python, LGPL-3.0) generate whole campaigns [V]. None of their READMEs mentions an LLM [V]. The source trees were not exhaustively searched.
- **Arma-side LLM work is mostly runtime NPC or AI-commander mods, plus a few tiny hobby editor bridges.** Runtime examples: DCO GPT for Arma 3 (2023, ChatGPT NPC chat) [V2], and Reforger's "AI War - Core" (LLM game master, 20+ typed command types, 68% rating) and "StavkaTest" (LLM orchestrator over Reforger's commander systems, 15 downloads) [V]. **Correction (fact-check 2026-09-26):** LLM-assisted *editor* tools for Arma **do** exist as small MCP bridges: several drive the Arma 3 **Eden** editor (0–2★ each) and one drives the Reforger **Workbench** (`steffenbk/enfusion-mcp-BK`, 42★) [V, READMEs only] (§5.2). We found **none for OFP/CWA** and none that is a standalone editor with a built-in agent [U, negative result]. So our niche is "OFP/CWA + standalone editor + built-in harness", not "first LLM Arma editor".
- **Community reception is the main risk, more than the tech.** In late July 2026 Nexus Mods split its AI tag into *AI-Generated Content / AI Media / AI Assisted* and threatened moderation for mis-tagging [V2]. Steam's content survey separates *pre-generated* from *live-generated* AI content and requires guardrails for the latter [V]. The Indie Game Awards pulled *Clair Obscur*'s awards over leftover AI placeholder textures (Dec 2025) [V2]. Voice-cloning of Skyrim voice actors caused an outcry in 2023 [V2]. Provenance tags and an exportable disclosure summary protect our users from all of these.
- **Local and small models are viable for narrow, typed jobs.** NVIDIA ACE's PUBG Ally uses *Mistral-Nemo-Minitron-8B-128k-instruct* [V]. That it runs on-device is inferred: NVIDIA lists it among ACE SLMs sized for local VRAM but does not say so for Ally [I]. Skyrim mods Mantella and CHIM work with local backends [V]. Reforger mods on frontier APIs cost about $0.04–0.50/hr [V]. Our own design docs warn that local models need simpler schemas and staged decomposition [V].
- **Evaluation prior art:** hard validity checks (A* playability, physics stability), controllability, diversity, human acceptance rates (Ghostwriter-style telemetry), and LLM-as-judge used cautiously. The field lacks a consensus evaluation method [V]. A fine-tuned GPT-2 quest generator produced acceptable output only about **1 in 5** times [V]. That argues for validators and humans in the loop.
- **Do NOT ship:** runtime LLM calls inside exported missions, voice cloning, unauthenticated local control sockets, silent AI placeholders, or anything that uploads to the Workshop or Steam automatically.

---

## 1. Terms

| Term | Meaning here |
|---|---|
| LLM / SLM | Large / small language model. SLM roughly means ≤ ~8B parameters, runnable locally. |
| Harness agent | The loop around a model that exposes tools, runs them, feeds results back, and enforces approvals (see docs 10–12). |
| Typed action / tool | A named editor command with a schema-checked argument list (e.g. `place_unit{class, side, pos}`), as opposed to free-form code. |
| MCP | Model Context Protocol, a JSON-RPC protocol that lets an external agent list and call a program's tools. Spec: https://modelcontextprotocol.io/specification/2025-06-18/server/tools |
| Bark | A short, context-triggered NPC line ("Reloading!", "Contact left!"). |
| PCG | Procedural content generation. |
| Provenance | Machine-readable record of who or what produced a piece of content (model, prompt, time, human edits). |
| BYOM / BYOLLM | Bring-your-own-model: the user supplies an API key or a local endpoint. |
| Pre-/live-generated | Steam's terms: AI content made during development and shipped, versus AI content generated while the game runs. |

---

## 2. Landscape at a glance

| Project | Category | What it does | Technical approach | Human-in-the-loop | Status / reception |
|---|---|---|---|---|---|
| Ubisoft Ghostwriter | Authoring (writing) | Drafts NPC barks | LLM + writer-defined character and bark type; 2 candidates per request; learns from choices; lives in Ubisoft's narrative tool "Omen" | Writer accepts, edits or discards | Internal tool. Announced at GDC 2023; public writer backlash [V]/[V2] |
| Xbox × Inworld | Authoring + runtime | "AI design copilot": prompts → scripts, dialogue trees, quests; plus a runtime character engine | Azure OpenAI + Inworld | Stated "responsible AI by design" | Announced Nov 2023. Shipping status **unknown** [V]/[U] |
| Inworld AI | Runtime NPC → infra | Character engine, now "Runtime" orchestration and realtime TTS | Cloud; "hybrid on-device or cloud" mention | n/a | Oct 2025 repositioning as infrastructure [V] |
| Convai | Runtime NPC | Voice NPCs that perform scene actions | Named action registry, scene "interactables", typed parameters | n/a | Unity and UE plugins [V]/[V2] |
| NVIDIA ACE | Runtime NPC | "Autonomous game characters" | On-device SLMs; perception → cognition → action | n/a | PUBG Ally, inZOI, NARAKA [V] |
| Ubisoft Neo NPC → Teammates | Runtime NPC | Voice-commanded squadmates | GenAI prototype | n/a | Closed test 2025; latency noted [V2] |
| Mantella (Skyrim/FO4) | Mod, runtime | Talk to any NPC; 20+ actions | STT → LLM → TTS; local or API backends; AGPL-3.0 | n/a | Very popular; many forks [V] |
| Herika → CHIM (Skyrim) | Mod, runtime | AI companion, then any NPC; narrator | SKSE plugin + HerikaServer bridge; function calling; GPL-3.0 / MIT | n/a | Active [V] |
| DCO GPT (Arma 3) | Mod, runtime | Chat with NPCs using ~1000 profiles | ChatGPT via extension | n/a | "Proof of concept", 2023 [V2] |
| AI War - Core (Reforger) | Mod, runtime | LLM game master | SITREP → FastAPI bridge → LLM → 20+ command types | none (autonomous) | 476 downloads, 68% rating [V] |
| StavkaTest (Reforger) | Mod, runtime | LLM strategic orchestrator | Drives Reforger's existing commander systems; pluggable REST/WebSocket | none | v1.0.2, 2026-04-01, 15 downloads, APL [V] |
| Arma 3 Eden / Reforger Workbench MCP bridges | Tool bridges (authoring) | Let Claude/Codex place and edit entities in the editor | Named-pipe / TCP / loopback-HTTP bridge to an SQF addon or Workbench NET API; typed tools, some also expose arbitrary SQF | Varies: none, to bearer token + confirm-destructive | Hobby scale: 0–2★ (Eden), 42★ (Workbench) [V, READMEs only] |
| Unity AI | Engine assistant | Ask / Plan / Agent; asset generators | Frontier models; `/run` generates C# and runs it after a compile check | Permission prompts, undo history, AI-asset metadata | Replaced Muse in Unity 6.2 (Aug 2025) [V] |
| Unreal 5.7 AI Assistant | Engine assistant | Docs Q&A, C++ snippets, F1 help | Cloud model (details undisclosed) | Advisory only | Nov 2025 [V2] |
| Unreal 5.8 MCP plugin | Engine tool API | External agents drive the editor | Typed toolsets (Scene/Actor/MaterialInstance/Object); localhost HTTP; no auth | Left to the client | **Experimental** [V] |
| Roblox Assistant | Engine assistant | Planning Mode, Playtest agent, mesh generation | Built-in MCP server; task manifest | Plan review (checkpoints unverified) | 44% of top-1000 creators use AI [V] |
| Blender / Unity / Unreal / Godot community MCP servers | Tool bridges | Let Claude, Cursor etc. drive the DCC or engine | Plugin/socket + MCP server; some expose arbitrary code execution | Varies; often none | Very popular (Blender MCP 29.4k★) [V] |
| Promethean AI | Asset mgmt / set dressing | Asset library search, world building in DCCs | Metadata around local assets; "don't … train on them" | Artist-driven | Commercial [V] |
| Ludo.ai / Scenario | Asset generation SaaS | Sprites, 3D, audio; style-trained models | Cloud; MCP + REST (Ludo) | n/a | Commercial [V] |
| Hidden Door | Narrative platform | Co-written stories in licensed worlds | Narrative engine over a hand-authored trope library + LLM narrator | Rights-holder built worlds | Public Aug 2025 [V2] |
| AI Dungeon | Narrative | Open-ended AI text adventure | Hosted LLMs + content filter | Moderation | 2021 moderation/privacy crisis [V] |
| BriefingRoom for DCS | Deterministic mission generator | Complete `.miz` missions from templates | 9-stage pipeline, DB of theaters and units, retries | Template UI; output editable in stock ME | GPL-3.0, 306★ [V] |
| DCS Liberation / Retribution | Deterministic campaign generator | Persistent dynamic campaigns | Python + pydcs; YAML data | Turn-based UI | LGPL-3.0; 800★ / 179★ [V] |

---

## 3. Authoring-time writing tools (closest analog to dialogue and briefing help)

### 3.1 Ubisoft Ghostwriter (2023)
- **What [V]:** An in-house La Forge tool that generates *first drafts of barks*. Writers specify a character and a bark type (combat, ambient, …) and optionally motivations or topics. The tool returns **two outputs**. The writer can "accept the line, edit it, or ditch it entirely". Selections feed back to improve the models. Ubisoft reported that paraphrasing "confident"/"excited" barks was often accepted, while "irritated"/"doubt" barks were rejected more often. It is integrated into the narrative tool **Omen**. It **excludes cinematics and lore**. A companion back-end, **Ernestine**, lets staff build their own ML models. Source: https://www.gamedeveloper.com/marketing/here-are-more-details-on-ubisoft-s-narrative-ai-tools-from-gdc-2023 , https://www.gamedeveloper.com/production/ubisoft-s-aims-to-support-its-scriptwriters-with-ai-ghostwriter-tool
- **Reception [V2]:** Some writers called it a "trojan horse" for broader AI use. Others worried about monotonous writing and argued that editing AI output takes longer than writing temp lines (Alanah Pearce). A former Watch Dogs: Legion developer (Liz England) called it the "gold standard" of integration. (These reception quotes are unverified on re-check: GamesHub returned 403, GamesRadar was truncated, and the AIAAIC page did not show them.) The Ernestine back-end and the "two choices" per request are confirmed by Ubisoft's own post, https://news.ubisoft.com/en-us/article/7Cm07zbBGy4Xml6WgYi25d/the-convergence-of-ai-and-creativity-introducing-ghostwriter (2023-03-21) [V]. Sources: https://www.gameshub.com/news/news/ubisoft-backlash-ai-dialogue-writing-tool-ghostwriter-2610382/ , https://www.gamesradar.com/former-watch-dogs-lead-defends-ubisofts-new-ai-assistant-writing-tool/ , https://www.aiaaic.org/aiaaic-repository/ai-algorithmic-and-automation-incidents/ubisoft-ghostwriter-seen-to-replace-scriptwriting-jobs
- **Lessons [I]:** Narrow scope (high-volume, low-stakes lines), several candidates side by side, one-click accept/edit/reject, structured inputs (character + event type), and acceptance telemetry as a quality signal. Even the gold-standard design attracts backlash, so framing and opt-in matter.

### 3.2 Xbox × Inworld "AI design copilot" (announced 2023-11-06)
- **What [V]:** "An AI design copilot that assists and empowers game designers … turning prompts into detailed scripts, dialogue trees, quests and more", plus "an AI character runtime engine". Source: https://developer.microsoft.com/en-us/games/articles/2023/11/xbox-and-inworld-ai-partnership-announcement/
- **Status [U]:** We found no public evidence of a shipped copilot. Inworld's Oct 2025 post repositions the company around its *Runtime* orchestration and realtime TTS, citing "Text-only stacks and one-off integrations were not built for real-time, multimodal workloads" (https://inworld.ai/blog/new-ai-infrastructure-scaling-games-media-characters) [V].
- **Lesson [I]:** "Prompt → dialogue tree/quest" is a recurring promise with little shipped, public evidence behind it. Our output should target the concrete data structures of the game: CWA dialogue is `stringtable.csv` keys plus `CfgRadio`/`CfgSounds` classes plus trigger and waypoint activations (§8.4).

### 3.3 Hidden Door (narrative platform)
- **What:** Launched publicly in August 2025 with licensed worlds (e.g. *The Wizard of Oz*, *Pride and Prejudice*, *Call of Cthulhu*) and pays world creators when others play [V2] (https://www.forbes.com/sites/charliefink/2025/08/14/hidden-door-turns-fan-worlds-into-licensed-revenue-sharing-story-platforms/). An independent review describes a narrative engine that assembles stories "from a large library of human-written tropes", tracking characters, items and locations as cards. The result is more coherent, but "you can't create at will" [V2] (https://arcanumrpgs.com/blog/hidden-door-review/). Hidden Door's own site describes a "Narrator" and "Modifiers" but gives no technical detail [V].
- **Lesson [I]:** Coherence comes from **structured, human-authored scaffolding** (tropes, cards, state) with the LLM filling in surface text. For us that means mission templates and dialogue slots, with the LLM writing inside them.

### 3.4 AI Dungeon (Latitude) — cautionary tale
- **What happened [V]:** In 2021 users generated sexual content involving minors. Under pressure from OpenAI, Latitude shipped a rushed filter with many false positives and unjust bans, and used human review of private stories. That review was ended after backlash. Latitude's own retrospective says "we are accountable for choosing our tech partners". It now uses different providers, encrypts story data, uses opt-in data collection, and does no human review of unpublished content. Source: https://help.aidungeon.com/faq/openai-and-filters ; timeline https://www.aiaaic.org/aiaaic-repository/ai-algorithmic-and-automation-incidents/ai-dungeon-offensive-speech-filter
- **Lessons [I]:** (a) Depending on a single upstream model provider is a product risk, which is an argument for BYOM. (b) Never ship user prompts or content to a human or remote reviewer silently. (c) Our local-first design sidesteps most of this, because we host nothing.

---

## 4. Runtime NPC platforms (not our product, but their action layers are relevant)

- **Convai [V]/[V2]:** Characters perform **named actions** ("Move To", "Throw", …) on **registered scene interactables** (https://docs.convai.com/api-docs/plugins-and-integrations/unity-plugin/adding-actions-to-your-character). Convai's UE5 guide describes phases: Default actions (Move To/Follow/Stop/Wait), Custom actions wired to Blueprint logic, and **Parameterized actions** passing "typed data … actor references, numbers, strings, booleans, enum choices". Complex requests decompose into atomic action sequences, e.g. "fetch me a jetpack" → [Move, PickUp, Move, Drop] [V2] (https://convai.com/blog/how-to-make-ai-npcs-act-on-your-commands-in-unreal-engine-5-with-convai). **Lesson:** a typed action vocabulary plus an entity registry is the proven interface between an LLM and a game world.
- **NVIDIA ACE [V]:** "Autonomous game characters" with a perception → cognition → action loop. PUBG Ally uses **Mistral-Nemo-Minitron-8B-128k-instruct** (on-device is inferred, not stated for Ally [I]). The page lists 8B, 4B and 2B Minitron cognition SLMs, the 2B one "Fits in as little as 1.5GB of VRAM", but does not say which model inZOI uses (unverified). Source: https://www.nvidia.com/en-us/geforce/news/nvidia-ace-autonomous-ai-companions-pubg-naraka-bladepoint/ (2025-01-06). **Lesson:** vendors ship 2–8B local models for bounded, typed decisions, not for open-ended authoring.
- **Inworld [V]:** See 3.2. Its move from demos to infrastructure highlights **latency, consistency and telemetry** as the hard parts.
- **Ubisoft Neo NPC → Teammates (2025) [V2]:** Voice-commanded companions in a closed test. Reviewers noted **latency** throughout. https://news.ubisoft.com/en-us/article/3mWlITIuWuu0MoVuR6o8ps/ubisoft-reveals-teammates-an-ai-experiment-to-change-the-game , https://www.aiandgames.com/p/ubisofts-teammates-demo-and-their
- **Implication for us [I]:** Runtime LLM NPCs inside exported CWA missions would force every *player* to have a model, a key or a bridge, and would move the mission into Steam's "live-generated" category. Keep the AI at **authoring time**. Exported missions stay plain CWA content.

---

## 5. Modding-community LLM projects

### 5.1 Skyrim / Fallout 4
- **Mantella [V]:** STT (Moonshine/Whisper) → LLM → TTS (Piper/xVASynth/XTTS). "Works with local models (Llama, Gemma, etc) and APIs (OpenAI, OpenRouter, NanoGPT)". NPCs can "perform 20+ actions - follow, attack, trade, travel…". AGPL-3.0. https://github.com/art-from-the-machine/Mantella , https://art-from-the-machine.github.io/Mantella/ . The Nexus ecosystem includes a config "Omni Tool", a Player2 fork that removes the need for an OpenAI subscription, and community videos comparing "free Mantella LLMs" [V] (https://www.nexusmods.com/skyrimspecialedition/mods/98631, /mods/168163, /mods/179902). **Lesson:** setup friction and model choice are the main support burden. The community built one-click configurators and model-comparison guides.
- **Herika → CHIM [V]:** Herika began as "The ChatGPT Companion" (https://www.nexusmods.com/skyrimspecialedition/mods/89931). It grew into CHIM: an SKSE plugin plus **HerikaServer**, a bridge "between the SKSE plugin and various AI providers … ChatGPT, MeloTTS, koboldcpp, Openrouter, XTTS". It adds long-term memory, an AI narrator, and "function calling action commands". CHIM is GPL-3.0 (https://github.com/Dwemer-Dynamics/CHIM). The original HerikaServer is MIT and says "HerikaServer development has moved to Dwemer Dynamics" (https://github.com/abeiro/HerikaServer); no GitHub "archived" banner was seen, so "archived" is unverified. **Lesson:** a separate bridge process with pluggable backends plus function calling is the stable community architecture.

### 5.2 Arma
- **DCO GPT (Arma 3, 2023-05) [V2]:** Chat with NPCs driven by roughly 1,000 prebuilt profiles (rank, specialty, age, traits). NPCs know the current mission and injuries. The authors called it "more of a proof of concept". Speech lacked fluency. https://www.gamepressure.com/newsroom/arma-3-mod-with-chatgpt-npc-lack-eloquence/z5558c , Workshop https://steamcommunity.com/sharedfiles/filedetails/?id=2965142417 (page fetch rate-limited).
- **AI War - Core (Arma Reforger, v1.0.6, Mar 2026) [V]:** "A fully autonomous AI Game Master powered by LLM. No scripts, no admins". It collects a SITREP, sends it via a FastAPI middleware to Claude, GPT-4o or GLM, and executes "20+ command types: movement orders, spawns, weather control, sound, visual effects, objectives". Estimated cost "$0.04–$0.50/hr". 476 downloads, **68% rating**. https://reforger.armaplatform.com/workshop/68EB7BF2F5940DD9
- **Stavka (Workshop title "StavkaTest", Arma Reforger, v1.0.2, 2026-04-01, 15 downloads, Arma Public License) [V]:** An "LLM-powered strategic orchestrator" that "manipulates the game through Arma Reforger's existing commander systems, not by reimplementing them". An Enforce Script bridge "translates AI Commander decisions into native game commands". Pluggable transport: REST, with WebSocket as an upgrade. https://reforger.armaplatform.com/workshop/68B1A0F0C0DE0001
- **Others:** "LLM Commander" (Reforger) is a placeholder page, "LLMC test", 13 downloads [V]. There are ChatGPT custom GPTs for SQF scripting such as "Arma 3 Mission Architect" (https://chatgpt.com/g/g-sKOtixifR-arma-3-mission-architect) [V2, quality unknown]. A Reforger/Enfusion API-docs MCP server (`ViVi141/Arma_Reforger_Tools_MCP`, AGPL-3.0, docs lookup only, no editor control) is also listed on LobeHub [V]. Non-LLM runtime mission generators for Arma 3 exist, e.g. https://github.com/LISTINGS09/A3_Mission_Generator (runtime SQF: zones, tasks, population) [V].
- **Editor MCP bridges (added by fact-check, 2026-09-26) [V, from GitHub repo search and README reads only; code not inspected]:** these refute the original "no LLM-assisted Arma editor" result.
  - `diaverso/Arma3-Eden-Editor-MCP-Server` (MIT, 2★): Python MCP server → Windows named pipe → C++ DLL → SQF addon inside **Eden**. It creates, moves and deletes entities, edits attributes, queries terrain, and can save, clear and undo. It calls only pre-registered SQF functions, not arbitrary SQF. No authentication ("designed exclusively for local editor use").
  - `alexlef42/Arma3-Eden-Editor-MCP-Server` (MIT, 2★, Russian docs): 50+ tools over TCP → a Windows hub service → named pipe → DLL → SQF. It **also exposes `execute_sqf`**, i.e. arbitrary code.
  - `JTM-rootstorm/arma-mcp` ("ArmaMCP", 0★): TypeScript stdio sidecar → 127.0.0.1 HTTP bridge → native extension → SQF addon. It uses a bearer token, typed schemas, policy checks and explicit confirmation for destructive operations, and "no raw SQF execution MCP tool is exposed". This is the closest existing analog to principles 1 and 10 in §11.
  - Reforger **Workbench**: `steffenbk/enfusion-mcp-BK` (MIT, 42★) drives a running Workbench over its NET API on TCP 5775 (`wb_entity_create`, `wb_play`, …). Forks `Goldwep/enfusion-workbench-mcp` (112 tools, "author scenario elements live in Workbench") and `arma-reforger-competitive/arma-enfusion-mcp` build on it.
- **Negative result [U]:** We found no LLM-assisted editor for **OFP/CWA**. GitHub repo search for "operation flashpoint llm" and "sqm mission generator llm" returned 0 results. We also found no standalone mission editor with a built-in agent. Searches were limited, so treat this as "not found", not "does not exist".
- **Lessons [I]:** (1) Even the Arma LLM mods that work well **constrain the LLM to a command vocabulary** and **reuse the engine's existing systems** (Stavka). That is the same typed-action principle we want in the editor. (2) Ratings are mixed and downloads small, which suggests curiosity rather than a strong demand signal. (3) Cost per hour is published and users care about it, so our UI should show token and cost estimates per plan. (4) The Eden bridges split the same way Blender MCP does: typed-only (diaverso, ArmaMCP) versus arbitrary code (`execute_sqf`). ArmaMCP's loopback + token + confirm-destructive design is worth reading before we design our MCP surface.

---

## 6. Engine and editor assistants (the most direct analog)

### 6.1 Unity AI (replaced Muse in Unity 6.2, Aug 2025)
- **Components [V]:** Generators (sprites, textures, materials, animation, sound, partly via Scenario and Layer AI LoRAs), **Assistant**, and Inference Engine (formerly Sentis). Assistant "uses LLMs from OpenAI's GPT series, and Meta's Llama series". Actions consume "Unity Points". Unity's terms say "you are responsible for ensuring your use of Unity AI does not infringe on third-party rights". https://www.cgchannel.com/2025/08/unity-rolls-out-unity-ai-in-unity-6-2/
- **Modes [V]** (Unity blog, 2026-05-06, https://unity.com/blog/unity-ai-assistant-ask-plan-agent-mode-explained):
  - **Ask** is read-only.
  - **Plan** produces "a structured plan – a step-by-step breakdown" that needs approval.
  - **Agent** executes tasks end to end ("writing scripts, modifying scene components, creating prefabs"). It has three permission levels ("Read-only", "Write scripts only", and "Full autonomy", under which it "can write scripts, modify scenes, create assets, and run Editor actions"), and "A permission prompt appears before the Agent applies changes in a session".
  - Changes are undoable, and "all AI-generated assets are tagged with embedded metadata so they are identifiable in your project".
- **`/run` [V]:** Generates C# and "validates the generated code before it's run to ensure successful compilation". It shows a summary first, "Provides a log of changes … Lists the GameObjects that are modified or created", and offers an **Undo History** button. https://docs.unity3d.com/Packages/com.unity.ai.assistant@1.0/manual/run-overview.html
- **Lesson [I]:** Unity's Ask/Plan/Agent tiers plus permission levels are a ready-made answer to the "effort level" requirement. The embedded-metadata tag is the provenance precedent. Its C#-execution path is exactly what we avoid: CWA has no safe equivalent of compiling and sandboxing, and we don't need one if every capability is a typed command.

### 6.2 Unreal Engine
- **5.7 AI Assistant (Nov 2025) [V2]:** An in-editor assistant for questions, C++ snippets and step-by-step guidance. The "docked panel" and "F1 over UI" details are not in the cited article (unverified). It is advisory and "not intended to replace documentation or verified workflows". Epic "has not disclosed details about data handling". https://digitalproduction.com/2025/11/12/unreal-engine-5-7-foliage-pcg-and-in-editor-ai/
- **5.8 Unreal MCP plugin [V]:** "Experimental … use caution when shipping with it". Toolsets are `SceneTools`, `ActorTools`, `MaterialInstanceTools`, `ObjectTools` (GAS toolset off by default). It binds `http://127.0.0.1:8000/mcp`. "There is no authentication layer; the plugin is not safe to expose beyond the local machine". The docs say nothing about undo transactions or approvals. https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor ; coverage https://www.vp-land.com/p/unreal-engine-5-8-embeds-an-mcp-server-so-ai-agents-can-drive-the-editor
- **Community `chongdashu/unreal-mcp` [V]:** A C++ TCP plugin on port 55557 plus a Python FastMCP server, covering actors, Blueprints and node graphs. "EXPERIMENTAL … Production use is not recommended". MIT, about 2.1k★. https://github.com/chongdashu/unreal-mcp

### 6.3 Roblox Studio (2026-04-15) [V]
- **Planning Mode** "analyzes the game's code and data model", asks clarifying questions, and produces a plan that works as "a mini game design document". Agents can execute its tasks in parallel and check work against it.
- **Playtesting Agent (beta)** controls the player character to verify behaviour against the plan.
- **Built-in MCP server**, so creators can "seamlessly use Claude, Cursor, Codex, and other third-party tools with Studio". The name "Quick Connect" does not appear in the post (unverified).
- Checkpointing is not mentioned in the post or the TechCrunch coverage (unverified). The post only says that "Soon after launch" plan context will be stored "so it can be referenced across sessions".
- "44% of the top 1,000 creators on Roblox use Roblox Assistant or third-party AI tools via MCP".
- Source: https://about.roblox.com/newsroom/2026/04/roblox-studio-going-agentic
- **Lesson [I]:** The plan is an artifact the user edits before execution, and verification is automated. For us, the analog of the playtest agent is **static validation plus an optional "Preview in CWA" smoke test** (see doc 08).

### 6.4 Godot [V]/[U]
- We found no first-party AI assistant [U].
- Community MCP `Coding-Solo/godot-mcp` (MIT, about 5.8k★) launches the editor, runs projects, captures debug output, and creates scenes and nodes through one bundled `godot_operations.gd` run headless. https://github.com/Coding-Solo/godot-mcp . Other plugins exist (e.g. https://github.com/hi-godot/godot-ai) [V2].

### 6.5 DCC and engine MCP bridges
- **Blender MCP [V]:** An addon socket server plus an MCP server, about 29.4k★, MIT. `execute_blender_code` runs arbitrary Python: "ALWAYS save your work before using it". "The addon's socket server has no authentication or encryption, so anyone who can reach that port can run Python inside Blender". An opt-in `BLENDER_MCP_SAFE_MODE` validates scripts. https://github.com/ahujasid/blender-mcp
- **Unity MCP (CoplayDev) [V]:** "47 focused MCP tool entrypoints" for scenes, GameObjects, scripts, assets, tests and builds. MIT, about 14.5k★. The README mentions Roslyn script validation as an advanced option [V]. Undo integration and confirmations were not found in the README on re-check (unverified). None of this was verified in code. https://github.com/CoplayDev/unity-mcp
- **MCP spec guidance [V]:** "there **SHOULD** always be a human in the loop with the ability to deny tool invocations". Clients should "Present confirmation prompts", "Show tool inputs to the user before calling", and "Log tool usage for audit purposes". Clients "MUST consider tool annotations to be untrusted unless they come from trusted servers". Tools may declare `outputSchema` for validated structured results. https://modelcontextprotocol.io/specification/2025-06-18/server/tools
- **Lessons [I]:** (1) Every major engine now exposes an **external agent API**, so users expect to drive editors from their own agent (Claude Code, Codex, Cursor). (2) The bridges that ship arbitrary code execution and unauthenticated sockets are also the ones with the loudest warnings. (3) A typed toolset (Unreal's official plugin) is the direction the vendors took.

### 6.6 How this maps to the user's own prior design
Iron Curtain's design already specifies "LLM-callable editor tool bindings". They expose editor operations as a **structured tool-calling schema** routed "through the same validation and undo/redo pipeline as GUI actions — no special path, no privilege escalation". The manifest is auto-generated from the command registry. The mode is "Not autonomous by default. The LLM proposes actions; the editor shows a preview; the user confirms or edits". And "If the GUI can't do it, the LLM can't do it". Source: `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D016/D016-factions-editor-tools.md#L160-L192` [V]. The same docs note that "The word 'AI' in gaming contexts attracts immediate hostility" and recommend positioning LLM features as a quiet power-user capability (`…/D016/D016-overview-generation.md#L21`). They also note that local models need "simpler output schemas, and more staged task decomposition" (`…#L41-L47`) [V]. Everything in §§4–6 above **independently corroborates** that design.

---

## 7. Generative asset and design SaaS (low direct relevance)

- **Promethean AI [V]:** Asset management and AI world-building inside Unreal, Unity, Maya, Blender and 3ds Max. "We don't upload them, store them or train on them in any way shape or form". The company positions itself as an artists' technical advisor in the class action against text-to-image companies. https://www.prometheanai.com/
- **Ludo.ai [V]:** Sprites, 3D, audio and video generation, with "Generate assets from Claude, Cursor, or any MCP client" plus a REST API and a Unity plugin. https://ludo.ai/
- **Scenario [V]:** Style-trained models ("10 to 20 high-resolution images … 30 minutes to one hour"). https://www.scenario.com/features/train . Its LoRAs power some Unity Generators (6.1).
- **Relevance [I]:** CWA content is fixed (addons, models and textures come from the game). Asset generation is **out of scope** and would pull in the art-community backlash. What carries over: clear statements on training-data ethics, and exposing capabilities over MCP/REST.

---

## 8. Deterministic mission generators (highly relevant)

### 8.1 BriefingRoom for DCS World [V]
- C#, **GPL-3.0**, about 306★, GUI plus **CLI for batch generation**. "Save mission templates to small template files and share them". "No units spawned through runtime scripting. All units are [added] to the mission itself", so output is editable in the DCS Mission Editor. It also generates kneeboard images. https://github.com/DCS-BR-Tools/briefing-room-for-dcs
- **Pipeline** (from the repo's *Mission Generation Deep Dive*, which is itself labelled "AI Created", so read it as a secondary summary [V2]): 9 ordered stages: Situation → Airbase → WorldPreload → Objective → Carrier → PlayerFlightGroups → CAPResponse → AirDefense → MissionFeatures.
  - Inputs are an immutable `MissionTemplateRecord` plus a database of theaters, airbases, units (by family and era) and coalitions.
  - Retries are layered: "Initial Retries (5 attempts)" per failing stage, then stage-reverting fallbacks, then a top-level Polly wrapper that "Retries up to 3 times if generation fails".
  - Validation covers territory, water/terrain spawns, parking and distance.
  - It auto-generates the briefing (Situation / Mission / Execution, frequencies) and adds "Editor notes with generation parameters".
  - https://github.com/DCS-BR-Tools/briefing-room-for-dcs/blob/main/src/BriefingRoom/code_docs/Mission-Generation-Deep-Dive.md
- **No LLM is used by the generator** [V for the README and deep dive, which mention none; the source tree was not exhaustively searched]. The repo root contains `.cursorrules` and `.windsurfrules` for AI *coding* assistants.

### 8.2 DCS Liberation and DCS Retribution [V]
- Liberation: "DCS World turn based single-player or co-op dynamic campaign. It is an external program that generates full and complex DCS missions and manage a persistent combat environment". Python, **LGPL-3.0**, about 800★, uses `pydcs`. https://github.com/dcs-liberation/dcs_liberation
- Retribution: forked from Liberation in 2022 and no longer backward-compatible. LGPL-3.0, about 179★. Campaigns are `.yaml` descriptors paired with `.miz` template missions, and factions are `.json` files (`resources/campaigns/`, `resources/factions/` on the `dev` branch). https://github.com/dcs-retribution/dcs-retribution

### 8.3 Lessons for a CWA generator [I]
1. **Separate the template from the generator from the output.** A small, shareable template (side, era, terrain, objective types, difficulty) goes into a deterministic pipeline, which writes a plain `mission.sqm` that opens in any editor. That makes results reproducible (seeded), diffable and reviewable.
2. **Keep all objects static in the mission** and avoid runtime spawning scripts, so a human can keep editing. This matches BriefingRoom's explicit rule.
3. **Use stages with local validation and bounded retries.** The same shape suits LLM repair loops (Word2World's feedback rounds, §9).
4. **The LLM's job is narrow.** It turns free text into a template, i.e. structured intent. It writes flavor: briefing prose, callsigns, radio lines, bark variants. It explains validation failures. It does **not** choose coordinates or unit classes directly. It *requests* them through typed tools that the generator and validators check against the terrain and the unit config.
5. **Licensing note:** BriefingRoom is GPL-3.0 and Liberation/Retribution are LGPL-3.0. Reading them for ideas is fine. Copying code has licence implications that `02-licensing-and-trademarks.md` should settle.

### 8.4 Where generated text lands in a CWA mission (verified in engine source)
- Per-mission `stringtable.csv` is loaded on mission set-up, then `description.ext` is parsed: `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/OptionsUI.cpp#L863-L876` [V].
- The briefing is a localized HTML file found via `FindLocalizedMissionHtmlFile(GetMissionDirectory(), "briefing")`: `…/UI/OptionsUI.cpp#L202-L205` [V].
- `CfgSounds` and `CfgRadio` classes in the mission's `description.ext` are resolved to mission-relative sound files: `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Audio/SoundScene.cpp#L399-L439` [V]. These lines are in `SoundScene::PreloadMissionAudio`, the Remastered engine's preload path. It reads both classes from `ExtParsMission`, the parsed `description.ext`. The play path goes through `FindSound`.
- **Implication [I]:** "Generate dialogue" should produce **rows**: `{key: STR_…, speaker, channel(side/group/vehicle/global), text_by_language, optional sound class, trigger/waypoint link}`. These compile into `stringtable.csv` entries, `CfgRadio`/`CfgSounds` classes and editor trigger or waypoint activations. They should not compile into free prose or SQS script text. Structured rows can be validated (unique keys, referenced sounds exist, length limits), localized, diffed and tagged.

---

## 9. Academic work and evaluation methods

| Work | Venue / date | Approach | Finding relevant to us |
|---|---|---|---|
| MarioGPT (Sudhakaran et al.) | arXiv 2302.05981; NeurIPS 2023 (venue not shown on arXiv; unverified) | Fine-tuned GPT-2 on tile levels; text prompts ("many pipes…"); plus novelty search | "The first text-to-level model". Prompt-controllable, and diversity comes from search around the model, not the model alone [V] https://arxiv.org/abs/2302.05981 |
| Level Generation Through LLMs (Todd et al.) | FDG 2023 | LLMs generate Sokoban levels | "Performance scales dramatically with dataset size". Control via prompting and data augmentation [V2] https://arxiv.org/abs/2302.05817 |
| Word2World (Nasir, James, Togelius) | arXiv 2405.06686, May 2024 | Story → extract characters/tiles/goals → **two-step** world generation → feedback rounds | "Directly generating a level through a pre-trained LLM is still challenging". Ablations show that decomposition matters. Evaluated with A* playability, novelty, and LLM-judged story–world coherence; larger LLMs score better [V]/[V2] https://arxiv.org/abs/2405.06686 |
| ChatGPT4PCG 1 & 2 (Taveekitworachai et al.) | IEEE CoG 2023/2024 | Prompt-engineering competition for Science Birds levels | Scored on physics **stability** + **similarity** to target letters. Edition 2 added **diversity** and accepted Python *programs* (with control flow such as conditions and iterations) instead of single prompt files [V] https://arxiv.org/abs/2303.15662 , https://arxiv.org/abs/2403.02610 |
| Generating RPG Quests with GPT (Värtinen, Hämäläinen, Guckelsberger) | IEEE ToG 16(1), 2024 | Fine-tuned GPT-2 on 978 quests; GPT-3 case studies; 349-participant study | "One in five quest descriptions would be deemed acceptable by a human critic, yet the variation in quality … is large" [V] https://research.aalto.fi/en/publications/generating-role-playing-game-quests-with-gpt-language-models/ |
| PANGeA (Buongiorno et al.) | arXiv 2404.19721, 2024 | Designer-defined criteria + memory + **LLM-based validation** of responses; REST interface; local/private LLMs | A validation layer keeps output within narrative scope [V] https://arxiv.org/abs/2404.19721 |
| Symbolically Scaffolded Play (Figueiredo, Elumeze) | arXiv 2510.25820, Oct 2025 | High- vs low-constraint prompts for NPC dialogue (GPT-4o) | "Scaffolding effects were role-dependent": tighter constraints stabilized a quest-giver but made suspects less believable [V] https://arxiv.org/abs/2510.25820 |
| Player-Driven Emergence (Peng et al., Microsoft Research) | IEEE CoG 2024 | GPT-4 text-adventure study with 28 players; logs → node graphs | Emergent content came mostly from exploration-oriented players [V] https://arxiv.org/abs/2404.17027 |
| LLMs and Games: Survey & Roadmap (Gallotta et al.) | IEEE ToG 2024 | Survey | Taxonomy of LLM roles in games, including **design assistant** and game master [V] https://arxiv.org/abs/2402.18659 |
| On the Evaluation of PCG Systems (Withington, Cook, Tokarchuk) | FDG 2024 | Meta-survey | "Consensus on how to evaluate novel systems is currently limited". Proposes a taxonomy and reuse of frameworks [V] https://arxiv.org/abs/2404.18657 |

**Evaluation methods observed → proposed for ofp-editor [I]:**
1. **Hard validity** (A* playability, physics stability) becomes our **mission validators**:
   - unit and vehicle classes exist in the loaded config;
   - positions are on land or water as the class requires;
   - waypoints are reachable;
   - triggers and synchronizations reference existing IDs;
   - stringtable keys resolve;
   - the `mission.sqm` round-trips through our parser.
2. **Controllability** (does the output match the prompt) becomes golden prompts with checkable expectations, e.g. "3 BMPs patrol between A and B" must yield 3 BMP-class vehicles and a cycle waypoint.
3. **Diversity/novelty:** seed sweeps over the deterministic generator. The LLM should not be the diversity source.
4. **Human acceptance rate** (Ghostwriter, Värtinen): locally logged accept/edit/reject per suggestion. It is opt-in and never uploaded by default.
5. **LLM-as-judge** (Word2World coherence): only for soft qualities such as briefing tone, and never as a gate on validity.
6. **Engine smoke test:** "Preview in CWA" plus log scraping (doc 08) is our equivalent of Roblox's playtest agent.

---

## 10. Community reception and platform policy

| Event / policy | Date | What | Status |
|---|---|---|---|
| Nexus Mods initial stance | Jul 2023 | "AI-generated mod content is not against our rules, but may be removed if we receive a credible complaint from an affected creator/rights holder" (quoted by Kotaku) | [V2] https://kotaku.com/skyrim-nexusmods-deepfake-porn-ai-voice-eleven-labs-1850607687 |
| Skyrim voice-clone controversy | Jul 2023 | ElevenLabs clones of Skyrim voice actors used in explicit mods; voice actors (e.g. Ben Diskin) and NAVA objected; mods removed on complaint | [V2] same Kotaku article |
| SAG-AFTRA Interactive Media Agreement | ratified Jul 2025 | Ended the 2024–25 video-game strike. Requires consent and disclosure for digital replicas and lets performers suspend consent during strikes. Reported 95.04% approval; higher minimums reported for "real-time generation" (both figures unverified: the SAG-AFTRA page returned 403 and the Suffolk article states neither) | [V2] https://www.sagaftra.org/sag-aftra-members-approve-2025-video-game-agreement (403 on fetch) , https://sites.suffolk.edu/jhtl/2025/10/30/game-over-for-unauthorized-ai-performances-the-sag-aftra-video-game-strike-and-performer-protections-under-the-new-collective-bargaining-agreement/ |
| Steam content survey | current doc; form reworded Jan 2026 | **Pre-generated:** "content that ships with your game and is consumed by players that is created with the help of AI tools during development". **Live-generated:** "created … while the game is running", which requires describing "guardrails … to ensure it's not generating illegal content". "Efficiency gains through the use of these tools is not the focus" | [V] https://partner.steamgames.com/doc/gettingstarted/contentsurvey ; Jan-2026 change [V2] https://www.pcgamer.com/software/ai/steam-updates-ai-disclosure-form-to-specify-that-its-focused-on-ai-generated-content-that-is-consumed-by-players-not-efficiency-tools-used-behind-the-scenes/ ; "7,300+ games disclosed" [V2, secondary blog] |
| Ghostwriter backlash | Mar 2023 | Writers: job threat, monotony, editing overhead | [V2] §3.1 |
| Indie Game Awards vs *Clair Obscur* | Dec 2025 | GOTY and Debut awards rescinded under the rule "strictly ineligible" for games using gen-AI. AI **placeholder textures** "squeezed past the QA process" into the release and were later patched out (the "within days" timing is unverified) | [V2] https://www.engadget.com/gaming/the-indie-game-awards-snatches-back-two-trophies-from-clair-obscur-over-its-use-of-generative-ai-164730842.html |
| Nexus Mods tag split | late Jul 2026 (Shacknews: Jul 31; TheGamer: Jul 30) | One tag becomes **AI-Generated Content** (code, UI, voices, dialogue, translations, music, in-game assets), **AI Media** (promo art, thumbnails, descriptions) and **AI Assisted** (developer-led, limited AI, upscaling, concept art). "Failure to tag mods in correct fashion will result in moderation". Moderators may require proof of human-led work | [V2] https://www.shacknews.com/article/150216/nexus-mods-gen-ai-tagging-moderation , https://www.thegamer.com/nexus-mods-generative-ai-guidelines-update/ |
| AI Dungeon moderation crisis | 2021 | Rushed filter, false positives, human review of private stories | [V] §3.4 |

**What this means for us [I]:**
- CWA mission makers publish on Steam Workshop, community sites and possibly Nexus. They need to be able to **answer truthfully** what in their mission is AI-made. If the editor records provenance per object and per text line, it can produce a disclosure summary that maps onto Nexus's three tags and Steam's pre-generated category.
- The *Clair Obscur* case shows that **AI placeholders leak into releases**. The editor should (a) visibly mark AI-authored, human-unreviewed text in the UI, and (b) warn on export if any unreviewed AI content remains.
- **Voice is the most toxic area.** Do not ship voice cloning, and do not offer "sound like the original OFP voice actors". If TTS is ever added, it must use explicitly licensed voices and be tagged. Default to text-only radio subtitles, which CWA already supports via `CfgRadio` titles [I].
- **Positioning:** keep AI out of the headline, as in IC D016 L21. Lead with faithful editor recreation, and present the AI as an optional power tool.

---

## 11. Design principles for the ofp-editor harness (synthesis)

Each principle lists the evidence behind it and the concrete implication. All implications are [I].

1. **Typed command layer only; no model-authored code execution.** Evidence: Convai typed parameterized actions; the Unreal 5.8 typed toolsets; Stavka and AI War command vocabularies; IC D016 tool bindings; and Blender MCP's arbitrary-code warning as the counter-example. Implication: one `EditorCommand` enum (place unit or group, set waypoint, add trigger, set marker, edit intel/briefing, add dialogue row, …), with newtype IDs, serde schemas and a generated tool manifest. The LLM can only emit commands. SQS/SQF snippets such as trigger `condition`/`onActivation` strings are **text fields**. The model writes them only from vetted templates, or as proposals that are flagged, shown and never auto-executed.
2. **One pipeline for GUI and AI: validate → apply → undo.** Evidence: IC D016 "no special path, no privilege escalation"; Unity undo history. Implication: an AI turn produces a single **transaction** (one undo step), with a named checkpoint in the history panel, like Unity's /run Undo History (Roblox checkpoints: unverified, see §6.3). `diaverso/Arma3-Eden-Editor-MCP-Server` also exposes undo for Eden (§5.2).
3. **Plan → Preview diff → Apply as the default loop, with autonomy tiers as the "effort level".** Evidence: Unity Ask/Plan/Agent plus three permission levels; Roblox Planning Mode; the MCP "human in the loop SHOULD"; Codex's `AskForApproval {UnlessTrusted, OnRequest, Granular, Never}` (`openai/codex@e72da2b538:codex-rs/protocol/src/protocol.rs#L986-L1009`). Implication: expose **Ask** (read-only Q&A about the mission), **Plan** (editable step list, nothing applied), **Agent** (applies after a per-batch confirm) and **Auto** (opt-in, per-session). Show the preview as ghosted units and markers on the 2D map plus a textual diff.
4. **Deterministic core, LLM for intent and flavor.** Evidence: BriefingRoom, Liberation and Retribution succeed without LLMs; Word2World and Hidden Door gain coherence from structure; Värtinen's 1-in-5 acceptance rate. Implication: build a seeded generator crate first (templates → `mission.sqm`). The LLM fills templates and writes text slots, and the validators decide.
5. **Structured dialogue and briefing data, not raw prose.** Evidence: Ghostwriter's structured inputs; §8.4 engine data paths; role-dependent scaffolding (Figueiredo). Implication: dialogue rows compile to `stringtable.csv` plus `CfgRadio`/`CfgSounds` plus triggers. The briefing is edited as structured sections and rendered to `briefing.html`. Offer Ghostwriter-style **N candidates per line** with accept/edit/reject. Constraint strictness is per role: strict for objective and briefing text, looser for ambient barks.
6. **Provenance on everything the AI touches.** Evidence: Unity's embedded metadata; the Nexus and Steam taxonomies; *Clair Obscur*. Implication: every command and text row carries `{origin: human|ai|ai_edited, model_id, provider, prompt_hash, timestamp}`. Store it in an editor **sidecar file** next to the mission, because CWA must not choke on unknown `mission.sqm` classes [I, verify in doc 04]. Provide an "AI content report" export and an unreviewed-AI warning at export time. C2PA "Content Credentials" (https://c2pa.org/) is the media-industry provenance standard. Whether it fits text or config content like missions is unverified [U], so treat it as a later option rather than a dependency.
7. **Opt-in, local-first, BYOM, never auto-publish.** Evidence: AI Dungeon's provider dependency; community success of local backends (Mantella, CHIM); NVIDIA ACE on-device SLMs; IC BYOLLM. Implication: AI is off by default. Providers are local (OpenAI-compatible endpoint, llama.cpp/Ollama-style) or cloud with the user's key. No telemetry leaves the machine without opt-in. There is no Workshop-upload tool in the agent's manifest at all.
8. **Validators are ground truth; repair loops are bounded.** Evidence: BriefingRoom's retries and fallbacks; Word2World's feedback rounds; PANGeA's validation layer; MCP "validate tool results". Implication: tool results return structured `ValidationIssue`s to the model, with at most N repair rounds, then escalation to the user with an explanation.
9. **Design for small models too.** Evidence: IC D016 L41–47; ACE's 8B/4B/2B SLMs for bounded decisions; Reforger cost figures. Implication: keep tool schemas flat with enums over free strings. Offer a "fast/cheap" workflow that is mostly deterministic, and show estimated tokens and cost before running a plan.
10. **Expose the same tool manifest over MCP (optional, localhost, authenticated).** Evidence: Unreal, Roblox, Unity and Ludo all expose MCP; Unreal and Blender warn about missing auth; Arma 3 Eden already has hobby MCP bridges, one of which (ArmaMCP) uses a loopback bind, a bearer token and confirmation of destructive operations (§5.2). Implication: users can drive ofp-editor from Claude Code or Codex. Bind to loopback, require a per-session token, and apply the same confirmation tiers.
11. **Measure quality locally.** Evidence: §9. Implication: a golden-prompt suite in CI using synthetic terrain and config fixtures only (no proprietary data, per project rules), plus opt-in local accept/edit/reject counters.
12. **No runtime AI in exported missions.** Evidence: the Steam live-generated guardrail requirement; latency and cost in Teammates and Reforger mods. Implication: exported missions are plain CWA content that runs on stock game installs.

### Anti-patterns seen in prior art (avoid)
- Arbitrary code execution tools (`execute_*_code`, `execute_sqf`) and unauthenticated control sockets (Blender MCP, early Unreal MCP bridges, some Eden MCP bridges).
- Fully autonomous "no admins" loops as the default (AI War - Core). That is fine as a mode, bad as the default.
- Free-prose generation dumped into content files. It cannot be validated, localized or tagged.
- AI placeholders without markers (*Clair Obscur*).
- Voice cloning of real performers (Skyrim 2023).
- Single-provider lock-in (AI Dungeon 2021).
- Marketing AI as the headline feature (IC D016 L21; Ghostwriter backlash).

---

## Open questions

1. **Bohemia's position.** Does Bohemia Interactive have a policy on AI-generated content for CWA/Arma Workshop items or for derivative tools built on the CWR source? Not found [U]. Worth asking on the forums or of the CWR maintainers before launch.
2. **Where to store provenance.** Will CWA's `mission.sqm` loader tolerate an extra class or attribute, or must provenance live in a sidecar file only? Verify against the parser described in doc 04.
3. **CWA community appetite.** Which AI features does the CWA community actually want (dialogue and briefing help vs. full mission generation)? Doc 09 (community wishlist) should poll this. The low download counts of Reforger LLM mods suggest a niche.
4. **Nexus tag mapping.** How exactly would Nexus's "AI Assisted" tag apply to a mission where the AI proposed unit placements but a human reviewed each one? Needs a reading of the full Nexus guidelines (the page returned 403 to us).
5. **Unverified safety features.** Are CoplayDev Unity MCP's Roslyn validation and undo integration real and effective? Claimed in the README summary, not verified in code.
6. **Xbox × Inworld copilot.** Did it ship anywhere? If so, what did designers report? No public evidence found.
7. **Missing controversies.** The Arc Raiders and The Finals TTS-voice controversies, and Godot's official stance on AI contributions, were not researched because the search budget ran out.
8. **Model families outside our scope.** The user asked about decision models such as "Jev, Kev, CLM, Laya". We did not research these here and found no content-creation prior art that uses them. Model selection belongs in the harness and model research docs.
9. **Arma editor MCP bridges.** The Eden and Workbench bridges in §5.2 were checked from READMEs only. Before borrowing from their tool schemas, and from ArmaMCP's token, policy and confirm-destructive layer, read their code and check their licences.

---

## Sources

**Local code and docs (pinned)**
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/OptionsUI.cpp#L202-L205`, `#L863-L876`
- `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Audio/SoundScene.cpp#L399-L439`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D016/D016-factions-editor-tools.md#L160-L192`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D016/D016-overview-generation.md#L1-L47`
- `openai/codex@e72da2b538:codex-rs/protocol/src/protocol.rs#L986-L1009`

**Web (accessed 2026-09-26)**
- Ghostwriter: https://news.ubisoft.com/en-us/article/7Cm07zbBGy4Xml6WgYi25d/the-convergence-of-ai-and-creativity-introducing-ghostwriter ; https://www.gamedeveloper.com/marketing/here-are-more-details-on-ubisoft-s-narrative-ai-tools-from-gdc-2023 ; https://www.gamedeveloper.com/production/ubisoft-s-aims-to-support-its-scriptwriters-with-ai-ghostwriter-tool ; https://www.gameshub.com/news/news/ubisoft-backlash-ai-dialogue-writing-tool-ghostwriter-2610382/ ; https://www.gamesradar.com/former-watch-dogs-lead-defends-ubisofts-new-ai-assistant-writing-tool/ ; https://www.aiaaic.org/aiaaic-repository/ai-algorithmic-and-automation-incidents/ubisoft-ghostwriter-seen-to-replace-scriptwriting-jobs
- Ubisoft Teammates: https://news.ubisoft.com/en-us/article/3mWlITIuWuu0MoVuR6o8ps/ubisoft-reveals-teammates-an-ai-experiment-to-change-the-game ; https://www.aiandgames.com/p/ubisofts-teammates-demo-and-their
- Xbox × Inworld: https://developer.microsoft.com/en-us/games/articles/2023/11/xbox-and-inworld-ai-partnership-announcement/
- Inworld: https://inworld.ai/blog/new-ai-infrastructure-scaling-games-media-characters
- Convai: https://docs.convai.com/api-docs/plugins-and-integrations/unity-plugin/adding-actions-to-your-character ; https://convai.com/blog/how-to-make-ai-npcs-act-on-your-commands-in-unreal-engine-5-with-convai
- NVIDIA ACE: https://www.nvidia.com/en-us/geforce/news/nvidia-ace-autonomous-ai-companions-pubg-naraka-bladepoint/
- Mantella: https://github.com/art-from-the-machine/Mantella ; https://art-from-the-machine.github.io/Mantella/ ; https://www.nexusmods.com/skyrimspecialedition/mods/98631 ; https://www.nexusmods.com/skyrimspecialedition/mods/168163 ; https://www.nexusmods.com/skyrimspecialedition/mods/179902
- Herika/CHIM: https://www.nexusmods.com/skyrimspecialedition/mods/89931 ; https://github.com/Dwemer-Dynamics/CHIM ; https://github.com/abeiro/HerikaServer
- Arma: https://www.gamepressure.com/newsroom/arma-3-mod-with-chatgpt-npc-lack-eloquence/z5558c ; https://steamcommunity.com/sharedfiles/filedetails/?id=2965142417 ; https://reforger.armaplatform.com/workshop/68EB7BF2F5940DD9 ; https://reforger.armaplatform.com/workshop/68B1A0F0C0DE0001 ; https://reforger.armaplatform.com/workshop/6879160C94579E77 ; https://chatgpt.com/g/g-sKOtixifR-arma-3-mission-architect ; https://github.com/LISTINGS09/A3_Mission_Generator ; https://lobehub.com/mcp/vivi141-arma_reforger_tools_mcp ; https://github.com/ViVi141/Arma_Reforger_Tools_MCP
- Arma editor MCP bridges (added by fact-check): https://github.com/diaverso/Arma3-Eden-Editor-MCP-Server ; https://github.com/alexlef42/Arma3-Eden-Editor-MCP-Server ; https://github.com/JTM-rootstorm/arma-mcp ; https://github.com/steffenbk/enfusion-mcp-BK ; https://github.com/Goldwep/enfusion-workbench-mcp ; https://github.com/arma-reforger-competitive/arma-enfusion-mcp ; GitHub repo search: https://github.com/search?q=arma+mcp&type=repositories
- Unity: https://www.cgchannel.com/2025/08/unity-rolls-out-unity-ai-in-unity-6-2/ ; https://unity.com/blog/unity-ai-assistant-ask-plan-agent-mode-explained ; https://docs.unity3d.com/Packages/com.unity.ai.assistant@1.0/manual/run-overview.html
- Unreal: https://digitalproduction.com/2025/11/12/unreal-engine-5-7-foliage-pcg-and-in-editor-ai/ ; https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor ; https://www.vp-land.com/p/unreal-engine-5-8-embeds-an-mcp-server-so-ai-agents-can-drive-the-editor ; https://github.com/chongdashu/unreal-mcp
- Roblox: https://about.roblox.com/newsroom/2026/04/roblox-studio-going-agentic ; https://techcrunch.com/2026/04/16/robloxs-ai-assistant-gets-new-agentic-tools-to-plan-build-and-test-games/
- Godot / MCP bridges: https://github.com/Coding-Solo/godot-mcp ; https://github.com/hi-godot/godot-ai ; https://github.com/ahujasid/blender-mcp ; https://github.com/CoplayDev/unity-mcp ; https://modelcontextprotocol.io/specification/2025-06-18/server/tools
- Asset SaaS: https://www.prometheanai.com/ ; https://ludo.ai/ ; https://www.scenario.com/features/train
- Narrative: https://www.forbes.com/sites/charliefink/2025/08/14/hidden-door-turns-fan-worlds-into-licensed-revenue-sharing-story-platforms/ ; https://arcanumrpgs.com/blog/hidden-door-review/ ; https://www.hiddendoor.co/ ; https://help.aidungeon.com/faq/openai-and-filters ; https://www.aiaaic.org/aiaaic-repository/ai-algorithmic-and-automation-incidents/ai-dungeon-offensive-speech-filter
- DCS generators: https://github.com/DCS-BR-Tools/briefing-room-for-dcs ; https://github.com/DCS-BR-Tools/briefing-room-for-dcs/blob/main/src/BriefingRoom/code_docs/Mission-Generation-Deep-Dive.md ; https://github.com/dcs-liberation/dcs_liberation ; https://github.com/dcs-retribution/dcs-retribution ; https://github.com/dcs-retribution/dcs-retribution/tree/dev/resources/campaigns ; https://github.com/dcs-retribution/dcs-retribution/tree/dev/resources/factions
- Academic: https://arxiv.org/abs/2302.05981 ; https://arxiv.org/abs/2302.05817 ; https://arxiv.org/abs/2405.06686 ; https://arxiv.org/abs/2303.15662 ; https://arxiv.org/abs/2403.02610 ; https://research.aalto.fi/en/publications/generating-role-playing-game-quests-with-gpt-language-models/ ; https://arxiv.org/abs/2404.19721 ; https://arxiv.org/abs/2510.25820 ; https://arxiv.org/abs/2404.17027 ; https://arxiv.org/abs/2402.18659 ; https://arxiv.org/abs/2404.18657
- Policy and reception: https://partner.steamgames.com/doc/gettingstarted/contentsurvey ; https://www.pcgamer.com/software/ai/steam-updates-ai-disclosure-form-to-specify-that-its-focused-on-ai-generated-content-that-is-consumed-by-players-not-efficiency-tools-used-behind-the-scenes/ ; https://tech-insider.org/steam-ai-disclosure-2026/ ; https://kotaku.com/skyrim-nexusmods-deepfake-porn-ai-voice-eleven-labs-1850607687 ; https://www.shacknews.com/article/150216/nexus-mods-gen-ai-tagging-moderation ; https://www.thegamer.com/nexus-mods-generative-ai-guidelines-update/ ; https://www.pcgamer.com/gaming-industry/nexus-mods-finally-tightens-the-screws-on-ai-though-its-still-playing-softball-with-the-tide-of-slop/ ; https://www.sagaftra.org/sag-aftra-members-approve-2025-video-game-agreement ; https://sites.suffolk.edu/jhtl/2025/10/30/game-over-for-unauthorized-ai-performances-the-sag-aftra-video-game-strike-and-performer-protections-under-the-new-collective-bargaining-agreement/ ; https://www.engadget.com/gaming/the-indie-game-awards-snatches-back-two-trophies-from-clair-obscur-over-its-use-of-generative-ai-164730842.html ; https://c2pa.org/

---

## Verification notes

Adversarial fact-check on 2026-09-26. Web budget was limited: WebSearch was exhausted, and the GitHub API and some news sites returned 403. Checks were therefore WebFetch reads of primary pages, GitHub web repo-search, and the pinned local clones.

**Confirmed against primary sources:**
- CWR `OptionsUI.cpp` L202-205 and L863-876, and `SoundScene.cpp` L399-439.
- IC D016 editor-tools L160-192 and overview L21 and L41-47.
- Codex `AskForApproval` L986-1009.
- Unity blog: date, the three modes and three permission levels, the permission prompt, undo, and embedded metadata. Unity `/run` docs. CG Channel's Unity 6.2 article.
- Unreal 5.8 MCP docs: experimental status, the four toolsets, GASToolsets disabled by default, `127.0.0.1:8000/mcp`, no auth, and no mention of undo or approval.
- Roblox: Planning Mode, task manifest, playtest agent beta, built-in MCP, and the 44% figure with its footnote.
- Ghostwriter: two outputs, accept/edit/ditch, excludes cinematics and lore, Omen, Ernestine.
- BriefingRoom: GPL-3.0, 306★, static units, CLI, 9 stages, AI-labelled deep dive.
- Liberation and Retribution: LGPL-3.0, 800★ and 179★.
- Blender MCP: MIT, 29.4k★, and its quotes.
- Mantella: AGPL-3.0 and its quotes. CHIM: GPL-3.0. HerikaServer: MIT.
- AI War - Core: all figures. DCO GPT article. LLM Commander.
- MCP spec quotes. Steam survey quotes. Nexus tag split (Shacknews Jul 31, TheGamer Jul 30). Kotaku 2023. Engadget on *Clair Obscur* (Dec 22 2025).
- Värtinen et al. (ToG 16(1), 978 quests, 349 players, "one in five").
- NVIDIA ACE: PUBG Ally's model.
- arXiv entries for Todd, Word2World, ChatGPT4PCG 1 and 2, PANGeA, Figueiredo, Peng, Gallotta (roles include Design Assistant and Game Master), and Withington.
- chongdashu, godot-mcp, CoplayDev star counts and licences.

**Changed:**
1. **Refuted the "no LLM-assisted Arma editor" negative result.** Hobby MCP bridges for Arma 3 Eden and the Reforger Workbench exist. The TL;DR, the §2 table, §5.2, principles 2 and 10, the anti-patterns, and open question 9 were updated. OFP/CWA still has none that we found.
2. Stavka's Workshop title is "StavkaTest": 15 downloads, released 2026-04-01, APL.
3. The PUBG Ally "on-device" claim is now marked inferred. The "inZOI uses smaller Minitron variants" claim was removed, because the page does not say it.
4. HerikaServer "archived" is now unverified: no banner was seen, only a "development has moved" notice.
5. Roblox "Quick Connect" and "checkpoints" are marked unverified: they are absent from the newsroom post and the TechCrunch coverage.
6. The UE 5.7 "docked panel" and "F1" details are marked unverified.
7. Unity quotes were corrected: the model-family wording, and the "Full autonomy" attribution.
8. The BriefingRoom retry counts were made precise: 5 stage attempts plus 3 Polly retries. Its "no LLM" claim is now scoped to the README and deep dive.
9. Retribution: factions are JSON, not YAML; campaigns are YAML plus `.miz`.
10. CoplayDev: undo and confirmations were not found in the README.
11. Author name fixed: "Elumeze". ChatGPT4PCG 2 "programs" wording fixed. The MarioGPT venue is marked unverified.
12. SAG-AFTRA's 95.04% and its real-time-generation minimums are marked unverified. The *Clair Obscur* "within days" timing is marked unverified. The Ghostwriter reception quotes are marked unverified.
13. The SoundScene pointer is now labelled as the Remastered preload path.

**Not re-checked:** Hidden Door, Forbes, Arcanum, the Convai blog, Scenario, the Mantella Nexus pages (403), the DCO GPT Workshop page, Teammates, the PC Gamer Steam article (truncated), and the Arma 3 Mission Architect GPT.
