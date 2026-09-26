# Local and Embedded LLM Inference from a Rust Desktop App

Research note 13 for the OFP/CWA standalone Mission Editor with the built-in AI harness agent.
Checked 2026-09-26. Scope: how the editor runs language models on the user's own machine
(Windows first, then Linux and macOS), and how that fits beside cloud APIs. Choosing *which*
model to ship, and how the agent loop works, are covered in other research notes. This note
covers only the runtime, packaging, constraint and licensing layer.

**Epistemic markers used below:** **[V]** verified against the cited source during this
research; **[I]** inferred by the author from verified facts (reasoning, not a measurement);
**[U]** unknown or unverified, so it must be measured or checked before we rely on it. There are
no tokens/s benchmarks in this note because none were measured. Every performance statement is
either a cited third-party claim or marked [U].

## TL;DR

- **Recommendation:** define one `InferenceProvider` trait with three backends: (1) **remote
  API**; (2) **local OpenAI-compatible server**, covering llama-server, Ollama, LM Studio,
  Lemonade, Foundry Local, vLLM and `mistralrs serve`, plus a **managed llama-server
  sidecar** that the editor downloads, verifies and supervises itself; (3) an **in-process
  embedded engine** behind the cargo feature `embedded-llama`, built on **`llama-cpp-2`**.
  Ship (1)+(2) first. Add (3) only after the spike exit criteria in §11 pass.
- **The embedded engine to adopt first is llama.cpp via `llama-cpp-2`** (0.1.157,
  2026-09-22, MIT OR Apache-2.0) [V]. It is the only candidate that combines a **Vulkan**
  GPU backend (vendor-neutral, so AMD, Intel and NVIDIA GPUs all work on Windows without
  CUDA), the GGUF model ecosystem, a GBNF grammar sampler, `json_schema_to_grammar`, and an
  optional **llguidance** sampler. It also uses the same engine as the managed sidecar, so a
  model we qualify behaves the same way in both modes [I].
- **Do not start with candle, mistral.rs, burn, ort or kalosm as the embedded engine.**
  candle 0.11 has no Vulkan or DirectX backend and no constrained decoding. mistral.rs documents
  no Vulkan backend, its Windows prebuilt binaries are CPU-only, and crates.io lags GitHub (0.8.1 vs
  v0.9.4). burn's LLM runtime (burn-lm) was archived on 2026-09-04. ort has no official
  generation/KV-cache layer in Rust. kalosm has not published a release since 2025-02 [V].
- **"Type-safe" actions come from constrained decoding plus validation, not from the model.**
  We define editor actions as Rust types, generate JSON Schema from them, and send it as
  `response_format: json_schema` to servers. On the embedded path we compile it with
  llguidance (MIT, Rust, JSON Schema, regex and Lark). The result is always parsed with
  serde and semantically validated before it becomes an undoable editor command. Constraints
  guarantee the *shape* of the output. They do not guarantee that it is *correct* [I].
- **Default to out-of-process native inference.** A C/C++ abort inside the editor process
  would lose unsaved mission work. So we qualify a supervised `llama-server` process first,
  and write an FFI adapter only after spike S3 (§11) shows the in-process path is safe [I].
- **Licensing:** every recommended runtime crate is MIT and/or Apache-2.0, and both are
  compatible with GPLv3 [V]. The NVIDIA CUDA EULA §1.2 says "You may not use the SDK in any
  manner that would cause it to become subject to an open source software license" [V]. **If the editor is GPL-3.0, do not
  bundle CUDA runtime DLLs.** Offer Vulkan, Metal or CPU in our own builds, and reach CUDA
  through a user-installed or upstream-downloaded server [I, not legal advice].
- **Binary weight:** upstream llama.cpp b11201 Windows zips are 18.3 MB (CPU) and 31.5 MB
  (Vulkan). The CUDA 13.4 zip is 145 MB plus a 404 MB cudart zip. The ONNX Runtime 1.30.0
  win-x64 CPU zip is 78.8 MB [V]. Model weights dominate: a 4B Q4_K_M GGUF is about 2.3 GiB
  [V]. Weights must be an optional download, never part of the installer.
- **Model management:** use a pinned manifest (repo, revision, file, size, SHA-256, license)
  with resumable download, hash verification and atomic install. `hf-hub` 1.0.0
  (Apache-2.0, 2026-07-10) is the candidate client [V]. Resume and verify behaviour is [U]
  until the spike confirms it.
- **NPU paths (WinML/QNN/OpenVINO/Ryzen AI) come later, as external servers only.** Reach them
  through Foundry Local, Lemonade or llama.cpp's OpenVINO build rather than embedding ONNX
  Runtime GenAI, which has no official Rust API [V].

## 1. Terms and context

| Term | Meaning in this note |
| --- | --- |
| SLM | Small language model, roughly ≤8B parameters, that fits on a consumer PC. |
| GGUF | llama.cpp's single-file model format: quantized weights plus metadata, including the chat template. |
| Quantization (e.g. Q4_K_M) | Storing weights in about 4–5 bits to cut RAM and disk use, at some quality cost. |
| Backend | The compute API the engine uses: CPU (SIMD), CUDA (NVIDIA only), Vulkan (cross-vendor GPU), Metal (Apple), DirectML/WinML (Windows DirectX 12 / ONNX), SYCL/OpenVINO (Intel), HIP/ROCm (AMD), QNN (Qualcomm NPU). |
| OpenAI-compatible server | A local HTTP server that exposes `/v1/chat/completions` (and often `/v1/models`) in OpenAI's JSON shape. Many runtimes do this. |
| Chat template | A Jinja template stored in the model that turns `[system, user, assistant, tool]` messages into the exact token text the model was trained on. |
| Tool calling | The model emits a structured "call function X with args Y". Each model family uses a different text syntax, which a parser converts to JSON. |
| Constrained decoding | At each generation step, tokens that would violate a grammar are masked out, so the output is guaranteed to parse. Grammars can be GBNF (llama.cpp), Lark or JSON Schema (llguidance), regex, and so on. |
| Sidecar | A separate helper process the editor starts, talks to over loopback HTTP, and kills when it exits. |

The editor's needs, from the project brief:

1. Runs standalone and offline, windowed or fullscreen.
2. Windows first. Many target users have AMD or Intel integrated GPUs, not NVIDIA.
3. The agent must emit editor actions (place unit, add waypoint or trigger, write a briefing
   or dialogue) that are valid by construction.
4. Bring-your-own model (cloud or local), with an optional first-party local model.
5. Streaming and cancellation, and the UI must never block.
6. The runtime must not crash the editor and lose mission work.
7. The license must be compatible with a possible GPL-3.0-or-later project license (the CWR
   engine source is GPL-3.0-or-later).
8. The project's coding rules forbid `unsafe` in our code, so FFI must live inside
   dependencies.

## 2. Embedded engines: landscape (as of 2026-09-26)

| Engine (Rust crate) | Latest | License | Language | GPU backends usable from Rust | Formats | Constrained decoding | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| llama.cpp via **`llama-cpp-2`** | 0.1.157, 2026-09-22 [V] | MIT OR Apache-2.0 [V] | C/C++ via bindgen FFI | cuda, vulkan, metal, rocm, opencl, mkl, `dynamic-backends` features [V] | GGUF (+ `mtmd` multimodal) | GBNF `grammar`, `grammar_lazy`, `json_schema_to_grammar`, `llguidance` feature [V] | **Adopt first (feature-gated)** |
| **mistral.rs** (`mistralrs`) | crates.io 0.8.1, 2026-04-02; GitHub v0.9.4, 2026-09-24 [V] | MIT [V] | Rust (candle-based) + CUDA kernels | CUDA, Metal, CPU. No Vulkan documented. Windows prebuilt is CPU-only [V] | HF safetensors, GGUF, GPTQ/AWQ/HQQ/FP8/BNB, ISQ [V] | llguidance (JSON Schema, regex, Lark) [V] | Use as an external server. Watch. |
| **candle** (`candle-core`) | 0.11.0, 2026-06-26 [V] | MIT OR Apache-2.0 [V] | Pure Rust | CUDA, Metal (+ MKL/Accelerate CPU). Vulkan/WGPU exist only in forks [V] | GGUF, safetensors | None built in [V]. Can add llguidance via `toktrie_hf_tokenizers` 1.8.0 [V] | Pure-Rust fallback, experimental |
| **burn** | 0.22.0-pre.4, 2026-09-22; 0.21.0 stable [V] | MIT OR Apache-2.0 [V] | Pure Rust (CubeCL) | CUDA, ROCm, Metal, Vulkan, WebGPU [V] | safetensors, PyTorch | None | No maintained LLM runtime (burn-lm archived). Reject for now. |
| **ort** (ONNX Runtime) | 2.0.0-rc.13, 2026-07-28, wraps ORT 1.28 [V] | MIT OR Apache-2.0; ORT MIT [V] | C++ runtime binary | CUDA, TensorRT, DirectML, OpenVINO, QNN, CoreML, ROCm, MIGraphX, Vitis AI, WebGPU, NVRTX … [V] | ONNX only | DIY (no generation loop) | Defer. It is the NPU path, but needs GenAI. |
| **kalosm** (floneum) | crates.io 0.4.0, 2025-02-09; repo active Sept 2026 [V] | MIT/Apache-2.0 [V] | Pure Rust (new "Fusor" WebGPU runtime, unpublished) | CUDA/Metal (0.4.0). WebGPU in repo [V] | GGUF | Derive-based `Parse` constraints [V] | Reject (no release). Watch. |
| `llama_cpp` (edgenai) | 0.3.2, 2024-04-29 [V] | MIT OR Apache-2.0 | FFI | — | GGUF | — | Stale. Reject. |

### 2.1 llama.cpp through `llama-cpp-2` (utilityai/llama-cpp-rs)

- **What it is.** Thin, fast-tracking bindings. The project says it aims to stay "as up to date
  as possible with llama.cpp" and "does not follow semver meaningfully"
  (<https://github.com/utilityai/llama-cpp-rs>) [V]. Releases come every one to four weeks
  (0.1.150 on 2026-06-16 through 0.1.157 on 2026-09-22) [V]. **Pin exact versions.**
- **Features** [V] (<https://docs.rs/crate/llama-cpp-2/latest/features>): the defaults are
  `common` and `openmp` (plus an Android-only stdcxx flag). The optional features are
  `cuda`, `cuda-no-vmm`, `vulkan`, `metal`, `rocm`, `opencl`, `mkl`, `dynamic-backends`,
  `dynamic-link`, `system-ggml`, `mtmd` and `llguidance` (the last pulls `llguidance ^1.7.5`
  and `toktrie ^1.7.5`). The `-sys` crate's manifest comment says `common` builds "the
  JSON-schema-to-grammar helper backed by llama.cpp's `common/` static library"; disabling it
  drops `libcommon.a` (~14 MB) [V]
  (<https://raw.githubusercontent.com/utilityai/llama-cpp-rs/main/llama-cpp-sys-2/Cargo.toml>).
- **Sampling API** [V] (<https://docs.rs/llama-cpp-2/latest/llama_cpp_2/sampling/struct.LlamaSampler.html>):
  - `grammar(model, grammar_str, root)`, `grammar_lazy(...)` (grammar enforced only after
    trigger words or tokens), `grammar_lazy_patterns(...)`;
  - `temp`, `top_k`, `top_p`, `min_p`, `typical`, `xtc`, `dry`, `penalties`, `mirostat`,
    `logit_bias`, `greedy`, `dist(seed)` and `chain`.
  - `json_schema_to_grammar` is a top-level function [V].
  - The `llguidance_sampler.rs` module adapts an `llguidance::Matcher` into a llama.cpp sampler
    through a C vtable. Its docs warn that building the token environment takes "on the order
    of hundreds of milliseconds for large vocabularies", so we should build it once per model
    [V] (<https://raw.githubusercontent.com/utilityai/llama-cpp-rs/main/llama-cpp-2/src/llguidance_sampler.rs>).
- **Chat templates and tools: a gap.** The binding exposes `chat_template()` and
  `apply_chat_template()`, which wrap llama.cpp's built-in heuristic template renderer, not its
  Jinja engine. It has no tool-call rendering or parsing [V]. Issue #1150, opened 2026-09-21,
  proposes Jinja bindings and is still open, with no maintainer reply at fetch time [V]
  (<https://github.com/utilityai/llama-cpp-rs/issues/1150>). A fork
  (`kapsl-llama-cpp-sys-2` 0.1.146-kapsl.1) carries OpenAI-compatible chat and tool wrappers,
  but it is a niche "shared-KV fork" [V] and we should not depend on it.
- **Windows build friction** [V] (build.rs and llama.cpp `docs/build.md`):
  - The build script runs **CMake** on vendored llama.cpp sources and runs **bindgen at build
    time**, so it needs libclang. It reads `LLAMA_STATIC_CRT`, `CMAKE_*`,
    `LLAMA_BUILD_SHARED_LIBS` and related variables.
  - `cuda` needs the CUDA toolkit (`CUDA_PATH`, `find_cuda_helper`).
  - `vulkan` needs the **Vulkan SDK** (`VULKAN_SDK`, `VULKAN_GLSLC`).
  - llama.cpp's Windows guide asks for Visual Studio 2022 with the "Desktop development with
    C++" workload, CMake tools and the Clang compiler.
  - `dynamic-backends` sets `GGML_BACKEND_DL=ON`, so GPU backends become runtime-loadable
    libraries [V].
  - Compile time and binary-size delta are [U]; see spike S3.
- **Upstream prebuilt sizes** (release b11201, 2026-09-26) are a proxy for the native payload
  [V] (<https://github.com/ggml-org/llama.cpp/releases/expanded_assets/b11201>):

  | Asset | Size |
  | --- | --- |
  | win-cpu-x64 | 18.3 MB |
  | win-vulkan-x64 | 31.5 MB |
  | win-cuda-13.4-x64 | 145 MB, plus cudart 404 MB |
  | win-cuda-12.4-x64 | 251 MB, plus cudart 373 MB |
  | win-openvino-2026.4-x64 | 84.2 MB |
  | win-sycl-x64 | 115 MB |
  | win-rocm-10.0-x64 | 245 MB |
  | macos-arm64 | 11.2 MB |
  | ubuntu-vulkan-x64 | 29.9 MB |

  These zips contain all the CLI tools, not just the library. Note that recent `bNNNNN` tags,
  b11201 included, are labelled **"Pre-release"** on GitHub [V], so pin an exact tag and asset
  hash rather than resolving "latest release".
- **Upstream backends** listed in the README: BLAS, CUDA, HIP, Metal, Vulkan, SYCL, WebGPU and
  OpenVINO ("Intel CPUs, GPUs, and NPUs", marked "[In Progress]"). License: MIT [V]
  (<https://github.com/ggml-org/llama.cpp>).
- **Our own evidence: none yet.** We have not yet run llama.cpp on Vulkan on an Intel or AMD
  iGPU ourselves. Whether it works, how fast it is, and how much memory it takes on our
  reference machines are [U], to be measured with our own evaluation instruments in spike S2
  (§11).

### 2.2 mistral.rs

- Feature-rich Rust engine. From the README [V] (<https://github.com/EricLBuehler/mistral.rs>):
  - OpenAI-compatible `/v1` and Anthropic Messages endpoints (`mistralrs serve`);
  - "Integrated tool calling with grammar enforcement and strict schema mode";
  - MCP client;
  - ISQ (in-situ quantization) and GGUF support.
- llguidance replaced the older constraint engine for regex, JSON Schema and Lark CFGs [V]
  (<https://github.com/EricLBuehler/mistral.rs/pull/899>).
- **Blockers for us:**
  - The quickstart lists Windows x86_64 prebuilt binaries as **CPU** acceleration only [V]
    (<https://ericlbuehler.github.io/mistral.rs/quickstart/>).
  - No Vulkan backend is documented [U]. Windows GPU users would need CUDA, and CUDA
    compiles on Windows are historically WSL-centric (community reports only [U]).
  - crates.io's newest `mistralrs` is 0.8.1 (2026-04-02), while GitHub tags reach v0.9.4
    (2026-09-24) [V]. Embedding it means a git dependency or accepting a lag of about six
    months.
- Development is very active (commits through 2026-09-25) [V]. It is a good
  **"bring your own server"** target (backend 2) and worth revisiting if a Vulkan/wgpu path
  appears.

### 2.3 candle (and rig-candle)

- `candle-core` 0.11.0 (2026-06-26) has the features `cuda`, `cudnn`, `metal`, `mkl`,
  `accelerate`, `nccl` and `ug`. There is **no Vulkan/wgpu/DirectML** [V]
  (<https://crates.io/crates/candle-core>). An upstream Vulkan backend (issue #3985) was
  proposed on 2026-09-16 and was still open with no maintainer reply at fetch time [V]
  (<https://github.com/huggingface/candle/issues/3985>). Forks (FerrisMind, rexlunae) add Vulkan
  and WGPU [V]. Depending on them is a maintenance risk [I].
- Real-world Rust integration: `rig-candle` (rig 0.42.0, candle 0.11)
  (`0xPlaygrounds/rig@42f4e060ef:Cargo.toml#L193-L195`) validates exactly three profiles,
  including the official Qwen3-4B Q4_K_M GGUF (2,497,280,256 bytes). Its README states [V]:
  - "The effective GGUF context limit is currently 4096 tokens because that is Candle 0.11's
    quantized cache capacity" (`crates/rig-candle/README.md#L48-L52`);
  - `output_schema` is rejected because "decoding is not grammar constrained" (`#L88-L92`);
  - cancellation is cooperative between forwards, inference runs in `spawn_blocking`, and
    concurrency defaults to one (`#L162-L166`);
  - "CPU only; no CUDA/Metal selection" (`#L171-L172`).

  A 4k window is tight for a mission-editing agent. It must fit the system prompt, the action
  schema, a mission-state summary and the reply [I]. The rig-candle README is the source of
  the 4096 limit; whether it applies to candle in general is [U].
- The Iron Curtain design docs chose candle for a **CPU-only** built-in tier because it is pure
  Rust, WASM-capable, and has no FFI
  (`iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D047-llm-config.md#L28-L39`,
  `#L101-L102`) [V]. Two things about that analysis matter here:
  - It notes "Candle does not ship a grammar constraint system"
    (`research/pure-rust-inference-feasibility.md#L483`) [V].
  - Its claim that candle reaches "~80–90% of llama.cpp throughput" (`#L705`) has **no
    citation**. Treat it as [U].

  For this editor, the lack of Vulkan and grammar support outweighs pure-Rust purity. Keep an
  `embedded-candle` experiment only for a future WASM/web build.

### 2.4 burn

- burn 0.22 prereleases have CUDA, ROCm, Metal, **Vulkan** and **WebGPU** backends [V].
  Architecturally, this is the most attractive pure-Rust GPU story.
- However, `tracel-ai/burn-lm` was **archived on 2026-09-04**: "Burn-LM is making way for a new
  Burn powered AI engine that can be embedded directly into applications or deployed as a
  standalone server" [V] (<https://github.com/tracel-ai/burn-lm>).
- No GGUF loader, quantized LLM runtime or constraint engine was found [U]. **Watch** for the
  announced successor, but do not build on burn now.

### 2.5 ort / ONNX Runtime / onnxruntime-genai / Windows ML

- `ort` 2.0.0-rc.13 (2026-07-28) targets ONNX Runtime 1.28, while ORT itself is at v1.30.0 [V].
  It lists execution providers (EPs) for CUDA, TensorRT, DirectML, OpenVINO, QNN, CoreML,
  ROCm, MIGraphX, Vitis AI, WebGPU, NVRTX and others [V] (<https://docs.rs/ort/latest/ort/ep/index.html>).
- ORT runs a graph. The LLM loop (KV cache, sampling, chat templates, constraints) lives in
  **onnxruntime-genai**:
  - v0.16.0 was released on 2026-09-22 with "tool calling and constrained decoding" [V]
    (<https://github.com/microsoft/onnxruntime-genai/releases>).
  - It offers **Python, C#, C/C++ and Java APIs, not Rust** [V]. Only unofficial experimental
    Rust wrappers exist [V].
  - Models must be converted or optimized to ONNX. GGUF is not supported.
- **DirectML is in maintenance mode.** Microsoft points Windows 11 24H2+ users to **Windows ML**
  [V] (<https://github.com/microsoft/DirectML>). Windows ML is "powered by ONNX Runtime" and can
  fetch vendor EPs through Windows Update. NPU and IHV-specific EPs require Windows 11 24H2
  (build 26100) or newer; CPU and DirectML GPU work on all supported versions [V]
  (<https://learn.microsoft.com/en-us/windows/ai/new-windows-ml/overview>).
- ORT win-x64 zips are 78.8 MB (CPU), 281 MB (CUDA 13) and 362 MB (CUDA 12) [V]
  (<https://github.com/microsoft/onnxruntime/releases/expanded_assets/v1.30.0>).
- **Verdict:** too much glue for a first release. Revisit only if NPU inference proves valuable,
  and prefer reaching NPUs through an external server (§3).

### 2.6 kalosm / floneum

- The ergonomics are attractive: `#[derive(Parse, Schema)]` for structured generation [V]
  (<https://github.com/floneum/floneum>).
- It has not published to crates.io since 0.4.0 (2025-02-09) [V]. The repo moved to an
  unpublished "Fusor" CPU/WebGPU runtime, with commits through 2026-09-08 [V]. The `fusor`
  name on crates.io is an unrelated 2020 placeholder [V].
- **Reject** for now. It could not be pinned to a released version.

### 2.7 WebGPU and NPU paths in brief

- **WebGPU:**
  - llama.cpp has an upstream WebGPU backend and can build natively via Dawn
    (<https://github.com/ggml-org/llama.cpp>; paper: <https://arxiv.org/html/2605.20706v1>) [V].
  - ort has a WebGPU EP [V], and candle forks add WGPU [V]. huggingface/ratchet is a
    "web-first" WebGPU toolkit whose README still says "active development", but its last code
    commit is dated 2024-11-23; 2026 commits only pin CI actions [V]. Treat it as dormant.
  - On a native desktop, Vulkan, Metal or DirectX already reach the same GPUs. WebGPU matters
    only for a future browser build [I].
- **NPUs:**
  - Intel NPU: OpenVINO. llama.cpp publishes `win-openvino` builds [V]; `openvino` crate 0.11.0
    (Apache-2.0) [V].
  - Qualcomm: QNN via ort/onnxruntime-genai [V].
  - AMD Ryzen AI: ONNX Runtime GenAI inside Lemonade [V].
  - Windows ML auto-EPs [V].
  - Whether an NPU beats a Vulkan iGPU for a 3–4B model on our target laptops is [U].

## 3. External OpenAI-compatible servers (backend 2)

| Server | License | Windows acceleration | API surface | Structured output | Tool calls | Model management | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **llama-server** (llama.cpp) | MIT [V] | CPU, CUDA, Vulkan, SYCL, ROCm, OpenVINO prebuilt [V] | `/v1/chat/completions` (sync + stream), `/completion` [V] | `response_format` `json_schema`; `grammar` and `json_schema` on `/completion` [V] | With `--jinja` (the flag table now lists it as "default: enabled"; `--no-jinja` turns it off); native formats for Llama 3.x, Qwen, Hermes, Mistral Nemo, …; "Generic" fallback; parallel calls opt-in [V] | Router mode: `--models-dir`, `--models-preset`, `--models-max`, autoload [V]; HF download by the server [V] | `--api-key` supported [V] |
| **Ollama** | MIT [V] | CUDA, ROCm, **Vulkan** ("enabled by default when the backend is installed") [V] | Native `/api/*` on :11434 plus OpenAI-compatible [V] | `format` = JSON Schema; also `response_format` via the OpenAI API [V] | Yes. codex requires ≥0.13.4 for the Responses API [V] | `/api/pull` with progress [V] | v0.34.4 (2026-09-23); 0.40.0 pre-release [V]. Default context length depends on VRAM [V] (see below) |
| **LM Studio** | Proprietary. Free for personal and work use; no redistribution [V] | Its own llama.cpp builds | OpenAI-compatible | JSON Schema: llama.cpp grammar for GGUF, Outlines for MLX; docs warn models "below 7B" may fail [V] | [U] | `lms get`, load/unload [V] | User-installed only |
| **Lemonade** (AMD) | Apache-2.0 [V] | llama.cpp Vulkan/ROCm; ORT GenAI for **Ryzen AI NPU** [V] | OpenAI-compatible; README example base URL `http://localhost:13305/api/v1` [V] | [U] | [U] | Built-in | Windows 11, Linux, macOS [V] |
| **Foundry Local** (Microsoft) | SDK MIT; CLI under the Microsoft Software License Terms [V]. The license terms of the native core library the SDK loads are not stated in the repo LICENSE (unverified) | Windows ML (GPU/NPU) on Windows [V]; macOS Apple silicon and Linux also supported [V] | Optional OpenAI-compatible web server; Rust SDK `foundry-local-sdk` 2.0.1 loads the core through `libloading` [V] | "structured response formatting" [V, shallow] | Yes (SDK) [V] | Catalog plus download builder [V] | GA 2026-04-09 per the Microsoft blog [V], though the README still points to a `cli-preview-0.10.0` CLI release [V]. Redistribution terms of the core are [U] |
| **vLLM** | Apache-2.0 [I] | **No native Windows**: "use WSL … or community-maintained forks" [V] | OpenAI-compatible | xgrammar / guidance backends, `structured_outputs` [V] | Yes [I] | — | For LAN GPU boxes |
| **`mistralrs serve`** | MIT [V] | CPU prebuilt on Windows [V] | OpenAI and Anthropic-compatible [V] | llguidance [V] | Yes [V] | HF | See §2.2 |

Sources for the table: llama.cpp server README and function-calling docs, docs.ollama.com,
lmstudio.ai docs, lemonade and Foundry-Local repos, docs.vllm.ai (full URLs in Sources).

**Important quirks for our client.**

- The same "OpenAI-compatible" label hides different constraint keywords (`format` vs
  `response_format` vs `structured_outputs`), different tool-call support, and different
  default context lengths.
- Defaults can change underneath us. Ollama's docs, for example, set the default context by
  VRAM: "< 24 GiB VRAM: 4k context", "24-48 GiB VRAM: 32k context", ">= 48 GiB VRAM: 256k
  context", overridable with `OLLAMA_CONTEXT_LENGTH`
  (<https://docs.ollama.com/context-length>) [V]. So the same model can get a different
  window on a different machine.
- Our client should therefore probe capabilities and **send explicit `n_ctx`, sampler and
  constraint settings**, recording what the server reports back [I].

**Managed llama-server sidecar (backend 2, "built-in" mode).** The editor would:

1. Download a pinned upstream release zip (Vulkan build on Windows/Linux, Metal build on macOS,
   CPU fallback) by exact tag (upstream builds are labelled "Pre-release", see §2.1) and verify
   its SHA-256.
2. Start `llama-server` bound to `127.0.0.1` on a random port with a random `--api-key`.
3. Wait for `/health`, then talk to it through the same client as any external server.
4. Kill it with the editor (on Windows, a Job Object with kill-on-close).

Prior art:

- pi drives llama-server's **router mode** for load, unload and HF download, with
  cancellation from the UI
  (`earendil-works/pi@2b0a123de9:packages/coding-agent/docs/llama-cpp.md#L9-L28`, `#L76-L83`)
  [V].
- codex auto-pulls models with progress events for `--oss` through Ollama
  (`openai/codex@e72da2b538:codex-rs/ollama/src/lib.rs#L15-L44`) and through LM Studio's
  `lms get` (`codex-rs/lmstudio/src/client.rs#L173-L184`) [V].

Advantages of this mode:

- no C++ toolchain in our CI;
- crash isolation;
- identical wire behaviour to BYO servers;
- the user can switch to a CUDA build that **they** download from upstream, so we never
  redistribute CUDA [I].

Costs of this mode:

- process supervision, port and firewall prompts, and antivirus false positives [U];
- binding to loopback is not authentication: any local process can reach the port, which is
  why step 2 still sets a random `--api-key` [I];
- upstream prebuilt binaries almost certainly do **not** include llguidance.
  `LLAMA_LLGUIDANCE` is a build-time option that needs a Rust toolchain (llama.cpp
  `docs/llguidance.md`), its CMake default is `OFF`, and the upstream `release.yml` workflow
  never sets it [V: checked 2026-09-26]. Whether a given binary has it is still confirmed at
  runtime in S1/S2 [I]. So the sidecar path uses the built-in GBNF converter, with its
  weaker JSON Schema handling (§4).

## 4. Constrained decoding: the "type-safe" layer

The user asked for actions that a small model (SLM), a large model (LLM) or a decision model
cannot get syntactically wrong. The mechanism is to mask the logits with a grammar compiled
from the action schema.

| Library | Version / date | License | Language | Inputs | Where it already runs | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| llama.cpp GBNF + `json_schema_to_grammar` | in-tree | MIT | C++ | GBNF, JSON Schema subset | llama.cpp, llama-server, Ollama, LM Studio (GGUF) [V] | Per the llguidance comparison, the built-in converter puts required properties first and silently ignores unsupported keywords; llguidance errors instead [V] (llama.cpp `docs/llguidance.md`) |
| **llguidance** | 1.8.0, 2026-08-11 [V] | MIT [V] | **Rust** | JSON Schema (large subset), regex, Lark-like CFG with inline `%json{}` [V] | README claims OpenAI, llama.cpp (opt-in), vLLM, SGLang, Chromium, mistral.rs, onnxruntime-genai [V: claim] | README claims ~50 µs CPU per token for a 128k tokenizer and negligible startup [V: claim]. The llama-cpp-2 wrapper notes TokEnv build costs of hundreds of ms [V] |
| outlines-core | 0.2.14, 2026-01-09 [V] | Apache-2.0 [V] | Rust | regex, JSON Schema | Outlines (Python); LM Studio MLX path [V] | Slower release cadence |
| xgrammar | XGrammar-2, 2026-05 [V] | Apache-2.0 [V] | C++ | EBNF, JSON Schema, regex, structural tags | vLLM, SGLang, TensorRT-LLM, MLC [V] | Official Python/C++/JS/Swift APIs. Rust bindings are community-made (`xgrammar-rs`, listed under third-party bindings in the xgrammar README) [V]. Their maturity is [U] |

**Design (all [I]):**

1. Editor actions are Rust enums and structs, for example `EditorAction::PlaceUnit { side,
   class: UnitClass, pos: Pos2, … }`. `schemars` 1.2.2 (MIT) [V] derives the JSON Schema.
2. Dynamic enums restrict fields such as `class` to classes that exist in the loaded addon
   config, and `group` to IDs present in the mission. The schema is therefore rebuilt per
   request from editor state.
3. Every provider receives the same schema:
   - servers get `response_format: {type: "json_schema", ...}` (llama-server, LM Studio,
     vLLM) or `format` (Ollama);
   - the embedded engine compiles the schema with llguidance;
   - remote frontier APIs use their native structured-output modes (see the provider research
     note).
4. If a provider reports no constraint support, fall back to "JSON mode, then validate, then a
   bounded repair retry". Surface that the output was unconstrained.
5. The output is always deserialized with serde and validated against editor rules (map
   bounds, side and class compatibility, waypoint ownership) before it becomes an undoable
   command. **A constraint proves syntax. It does not prove intent.** Validators therefore stay
   mandatory whatever the backend; this is a standing rule of our agent doctrine
   ([21-agent-doctrine.md](21-agent-doctrine.md)).
6. **Local "decision model" emulation.** Constrain the output to one of N enum labels. With
   in-process llama.cpp, read the per-option probabilities from the logits. This gives a local
   analogue of hosted choice/score judges such as TypeSafe Jev. Rig's public integration reaches
   Jev as a hosted service, reading `JEV_TOKEN` with a default model id of `jev-latest`
   (`0xPlaygrounds/rig@42f4e060ef:crates/rig-typesafeai/README.md#L87-L88`) [V], and its README
   warns that "Confidence measures concentration, not correctness" (`#L92`) [V]. The public
   decision models and the evidence we require of them are compared in
   [16-decision-models.md](16-decision-models.md). This is a key reason to keep an in-process
   engine on the roadmap. Its quality is [U].
7. For small local models, prefer **one constrained "action envelope" per step**
   (`{"action": <union>, "say": "..."}`) over model-native tool calling. It works on every
   constraint-capable backend and does not depend on per-family tool-call parsers. Native tool
   calling remains the default for remote frontier models [I].

## 5. Chat templates, tool calling, streaming and cancellation

**Chat templates.**

- GGUF files embed a Jinja template. llama-server renders it with its Jinja engine (`--jinja`,
  which the current server README lists as "default: enabled") [V]. The sidecar should still
  pass `--jinja` explicitly so the setting does not depend on the build's default.
- `llama-cpp-2` exposes only llama.cpp's heuristic renderer (issue #1150) [V]. For the embedded
  path, render templates ourselves with `minijinja` (Apache-2.0; newest 3.0.0-alpha.2, so pin
  the stable 2.x line) [V/I]. Add golden tests comparing our output with llama-server's for
  each qualified model.
- Whether minijinja reproduces every HF template byte-for-byte is [U]. kalosm recently had to
  "Fix chat template rendering to match transformers" [V], which shows the risk is real.

**Tool calling.**

- Through servers, the OpenAI `tools` field works when the server supports the model family.
  llama.cpp warns that "extreme KV quantizations (e.g. `-ctk q4_0`) … can substantially degrade
  the model's tool calling performance" [V]
  (<https://github.com/ggml-org/llama.cpp/blob/master/docs/function-calling.md>).
- rig-candle shows the manual work required for local tool calling. It has to:
  - buffer a whole turn, because Qwen tool syntax crosses token boundaries;
  - reject reserved template delimiters in user text to prevent prompt-structure injection;
  - route unknown tool names to a typed error.

  (`0xPlaygrounds/rig@42f4e060ef:crates/rig-candle/README.md#L54-L86`) [V]. Adopt the same
  safeguards in our embedded path.

**Streaming.**

- Servers stream over SSE [V].
- In-process: run the decode loop on a dedicated OS thread (not the UI thread) and push
  `GenerateEvent`s over a bounded channel. rig-candle uses capacity 8 and `spawn_blocking`
  (`#L162-L166`) [V].
- Do not display an unvalidated action as applied. Stream prose, but apply actions only after
  validation [I].

**Cancellation.**

- In-process: check an atomic cancel flag between `decode` calls, so latency is at most one
  token step [I].
- HTTP: drop the request. Whether llama-server or Ollama stop computing when the client
  disconnects is [U]. The llama-server README fetched for this note does not state it. If they
  do not, the managed sidecar can be restarted as a last resort.

## 6. Model download and management UX

- **Pinned manifest per first-party model:** `repo`, `revision` (commit SHA), `file`, `bytes`,
  `sha256`, `license`, `chat_template_id`, `n_ctx`, recommended sampler, and a
  RAM/VRAM note. This is the same shape as the IC `model_pack.toml` (`D047-llm-config.md#L73-L99`)
  [V]. At run time we record both the values we requested and the effective values the
  backend reports, because they can differ (§3) [I].
- **Download:**
  1. Stream to `*.part` with HTTP Range resume.
  2. Verify size and SHA-256.
  3. Rename atomically into the model directory.
  4. Check free disk space first: the `.part` file plus any version it replaces must fit
     [I]. Check **RAM** separately at load time. rig-candle notes that loading "temporarily also
     holds the 2.33-GiB input byte buffer" and advises planning "for more than twice the
     checkpoint size during loading" (`#L127-L132`) [V]. That is a memory figure for an
     in-process loader that reads the whole file into a buffer. It is not a disk-space figure.

  rig-candle's download script follows exactly this pattern: "immutable revisions, retries
  resumable temporary downloads, checks size and SHA-256, then atomically installs"
  (`#L105-L107`) [V].
- **Client:**
  - `hf-hub` 1.0.0 is async and has an optional `blocking` feature. Downloads are
    "content-addressed under `HF_HUB_CACHE`" (`HF_HOME` defaults to `~/.cache/huggingface`)
    with on-disk locking. It supports Xet transfers and `HF_TOKEN`
    (<https://docs.rs/hf-hub/latest/hf_hub/>) [V]. The docs do not say the layout is
    byte-compatible with Python `huggingface_hub`'s cache (unverified).
  - That its resume and checksum behaviour meets our needs is [U]. If it does not, use plain
    `reqwest` with Range plus `sha2`.
  - Gated repos need a user token, and pi warns before gated downloads (`llama-cpp.md#L81`) [V].
- **BYO model:**
  - The user can pick any local `.gguf`. We read its metadata (architecture, context length,
    template) without loading weights, via `llama_cpp_2::gguf` or a small pure-Rust header
    parser written under our parser rules.
  - Label the model "unqualified", meaning no eval pass has been recorded for it.
- **External servers:** list models (`/v1/models`, Ollama `/api/tags`) and offer pull or
  download where the server supports it (Ollama `/api/pull`, `lms get`, llama-server router).
  Never silently unload another client's model, following pi (`llama-cpp.md#L83`) [V].
- **Memory reality check.** Peak memory for each candidate model on CPU and on an iGPU
  through Vulkan is [U]. We will measure it with our own evaluation instruments (peak
  working set per backend, recorded as an observation, **not** a minimum requirement) on
  the §11 reference machines. Whatever the peak is, it comes on top of the editor. The model
  should also be unloaded before **Preview** launches the game [I].

## 7. Licenses and GPL-3.0 compatibility

| Component | License | Compatible with a GPL-3.0 editor? |
| --- | --- | --- |
| llama.cpp / ggml; llama-cpp-2 | MIT; MIT OR Apache-2.0 [V] | Yes |
| candle, burn, ort, hf-hub, llguidance, toktrie_hf_tokenizers, outlines-core, xgrammar, schemars, minijinja | MIT and/or Apache-2.0 [V] | Yes. "Apache 2 software can therefore be included in GPLv3 projects" (<https://www.apache.org/licenses/GPL-compatibility.html>) [V] |
| ONNX Runtime, onnxruntime-genai | MIT [V] | Yes |
| **CUDA runtime / cuBLAS DLLs** | NVIDIA EULA. Redistributable per Attachment A, but §1.2 says "You may not use the SDK in any manner that would cause it to become subject to an open source software license" [V] (<https://docs.nvidia.com/cuda/eula/index.html>) | **Conflict if bundled** with a GPL binary. They are not "System Libraries" [I, not legal advice] |
| Vulkan loader + GPU driver | Loader permissively licensed [U]; the driver is an OS/vendor component | Low risk [I] |
| Metal (macOS) | System framework | Low risk [I] |
| DirectML redistributable / Windows ML | Microsoft terms. WinML can be a shared system component [V] | Review before bundling [U] |
| LM Studio app | Proprietary, no redistribution [V] | Only as a user-installed external server |
| Foundry Local core | Not covered by the repo LICENSE, which has only an MIT SDK part and a Microsoft-terms CLI part [V]. The core's own terms are unverified | External server only until reviewed [U] |
| Model weights | Per model. For example, Qwen3.5-4B and Granite 4.1 3B are tagged `apache-2.0` on their Hugging Face model cards [V]. Re-check the license at the pinned revision | Separate data. Ship as an optional download with the license shown |

**Consequences:**

- If the project is GPL-3.0, our release builds should enable only `vulkan`, `metal` or CPU.
  CUDA stays reachable through the sidecar mode, where the **user** downloads upstream CUDA
  builds (separate programs talking over HTTP), or through their own Ollama or LM Studio [I].
- If the project chooses a permissive license instead, bundling CUDA is permitted under the
  EULA's conditions. It still costs 145–400+ MB per variant [V] and is not worth it for
  version 1 [I].

## 8. What prior art does

| Project | Local-model approach | Lesson for us |
| --- | --- | --- |
| openai/codex | `--oss` flag. Ensures Ollama or LM Studio is reachable, pulls or downloads the default model (`gpt-oss:20b`), and version-gates Ollama ≥0.13.4 for the Responses API (`codex-rs/ollama/src/lib.rs#L15-L70`; `codex-rs/lmstudio/src/lib.rs#L7-L45`) [V] | Detect servers, gate on versions, and give pull progress UX. No embedded engine. |
| earendil-works/pi | llama-server router: `/llama` load, unload and download; `--jinja`; Escape cancels loads (`docs/llama-cpp.md#L3-L87`) [V] | The router mode makes a managed sidecar cheap. |
| 0xPlaygrounds/rig | HTTP providers (`ollama`, `llamacpp` with server `timings`) plus `rig-candle` in-process (CPU, 4k context, no grammar) (`crates/rig-core/src/providers/llamacpp/completion.rs#L17-L48`) [V] | A trait over HTTP and in-process engines is proven. rig-candle's safety checks are worth copying. |
| iron-curtain design docs | Four provider tiers. Tier 1 is in-process candle, CPU-only, "not a sidecar". Tier 4 auto-detects Ollama :11434 and LM Studio :1234 (`D047-llm-config.md#L28-L39`, `#L101-L102`, `#L133-L141`) [V] | Reuse the tier UX and model-pack manifest. Our editor diverges on the engine choice for the reasons in §2.3. |

## 9. Recommended architecture

**Crate split** (each crate has one `Error` enum and no `unsafe`, per project rules):

```text
ofp-ai-core        types + trait; no HTTP, no native deps (pure, unit-testable)
ofp-ai-http        OpenAI-compatible + provider-specific HTTP/SSE clients (remote & local)
ofp-ai-sidecar     download/verify/spawn/supervise llama-server; yields an http endpoint
ofp-ai-llamacpp    in-process engine; only built with --features embedded-llama
```

**Trait sketch** (illustrative, not final API) [I]:

```rust
/// One way of running a model. Remote API, local server and in-process engine all implement it.
pub trait InferenceProvider: Send + Sync {
    fn capabilities(&self) -> &Capabilities; // streaming, tools, constraint kinds, logprobs, n_ctx
    fn generate(&self, req: GenerateRequest, cancel: CancelToken)
        -> Result<EventStream, InferenceError>; // bounded channel of GenerateEvent
}
pub enum OutputConstraint { None, JsonSchema(serde_json::Value), Lark(String), Gbnf(String), Choice(Vec<String>) }
pub enum GenerateEvent { TextDelta(String), ReasoningDelta(String), ToolCall(ToolCall), Usage(Usage), Done(StopReason) }
pub enum Backend { RemoteApi(RemoteCfg), LocalServer(ServerCfg), ManagedSidecar(SidecarCfg), Embedded(EmbeddedCfg) }
```

- The harness never learns which backend is in use. It asks `capabilities()`, picks the
  strongest constraint available (in order: `JsonSchema` or `Lark`, then JSON mode plus
  validation, then prompt plus validation), and records the effective settings in the session
  log.
- Effort levels map to provider-agnostic knobs:
  - `max_tokens`;
  - thinking on or off, via chat-template kwargs where supported (see issue #1150's
    `enable_thinking`);
  - best-of-N with validator selection;
  - escalation from local to remote. This last step needs explicit user consent, since it
    sends mission content off the machine [I].

**Phasing:**

1. **Phase A:** `ofp-ai-core` plus `ofp-ai-http`. Remote APIs plus BYO local servers
   (llama-server, Ollama, LM Studio, Lemonade, Foundry Local web server, vLLM,
   `mistralrs serve`). Auto-detect the default ports. Use JSON Schema constraints. Zero native
   dependencies, zero license risk.
2. **Phase B:** `ofp-ai-sidecar` becomes the "built-in local AI" button. It downloads a pinned
   llama.cpp release (Vulkan/Metal/CPU) plus one pinned, qualified GGUF, and runs it in router
   mode.
3. **Phase C:** `embedded-llama` feature using `llama-cpp-2` with `vulkan` or `metal`,
   `llguidance` and `dynamic-backends`. Use it for:
   - single-binary builds;
   - exact logit access (choice scoring and decision emulation);
   - lower-latency constrained steps.

   Enable it by default only if spike S3 shows abort-safety or we run it in our own worker
   process (`ofp-infer`, the same crate compiled as a separate binary).
4. **Deferred:** candle or burn pure-Rust engines (for WASM/web); ORT GenAI/WinML NPU
   embedding; CUDA in our own builds.

**Why `llama-cpp-2` first rather than candle (the Iron Curtain choice)** [I, from the verified
facts above]:

- **GPU coverage on Windows:** candle has CUDA only, while llama.cpp has Vulkan for all vendors.
- **Constraints:** candle has none. llama.cpp has GBNF plus an llguidance sampler.
- **Context:** rig-candle reports a 4096-token quantized-cache limit.
- **Behavioural parity** with the sidecar and with llama.cpp-based external servers
  (llama-server, Ollama, LM Studio for GGUF), so a model qualified on one path behaves the same
  on the others.
- **Maintenance cadence:** there is a llama-cpp-2 release every one to four weeks.
- **Costs accepted:** C++ build friction, FFI (the `unsafe` stays inside the dependency), no
  Jinja templates or tool parser in the binding, and in-process crash risk.

## 10. Risks

| Risk | Likelihood / impact | Mitigation |
| --- | --- | --- |
| ggml aborts on malformed input or out-of-memory, killing the editor | [U] / high (lost work) | Sidecar or worker process by default. Autosave before inference. Spike S3 fuzz test. |
| `llama-cpp-2` breaking changes (no semver) | High / medium [V] | Pin exact versions and wrap the binding in `ofp-ai-llamacpp` only. |
| Vulkan driver bugs on old iGPUs | [U] / medium | Automatic CPU fallback. Per-device allow/deny list from telemetry-free, user-submitted reports. |
| Small models produce schema-valid but wrong actions | High [I] / medium | Semantic validators, previews and diffs, undo, a "confirm before apply" mode, and eval sets. |
| Server constraint dialects diverge | High [V] / low | Per-server adapter tests against recorded, synthetic cassettes. |
| GPU contention with the game during Preview | [U] / medium | Unload the model or stop the sidecar on Preview; reload lazily. |
| CUDA licensing under GPL | [I] / high if ignored | No CUDA in our artifacts (§7). |

## 11. De-risking spike plan with measurable exit criteria

All spikes use synthetic fixtures only, with no game data. Record for each run:

- the exact artifact hashes, llama.cpp tag or crate version, backend, `n_ctx`, sampler, and
  hardware;
- the reference machines: one NVIDIA desktop, one AMD or Intel iGPU laptop, and one CPU-only 8
  GB VM, all on Windows 11 (plus Windows 10 where possible).

Unknown effective values are logged as `unknown`, never guessed or filled in from defaults.

| # | Spike | Exit criteria (all must pass) |
| --- | --- | --- |
| S1 | **HTTP provider + constraints.** `ofp-ai-http` against llama-server b11201, Ollama ≥0.34 and LM Studio, with one 3–4B Q4_K_M model. 200 prompts asking for `EditorAction` JSON with dynamic `UnitClass` enums | ≥99.5% responses parse **and** validate against the schema on llama-server and Ollama with constraints on. Streaming first-delta and total latency are recorded (no target yet). Cancelling a stream returns control to the UI in ≤250 ms. Whether the server stops computing afterwards is recorded (answers an open question). Mock-server tests cover SSE framing, errors and truncated streams. |
| S2 | **Managed sidecar lifecycle.** Download the pinned `win-vulkan-x64` zip, verify SHA-256, spawn on loopback with `--api-key`, health-check, load the model, generate, shut down | 50/50 start→generate→stop cycles succeed. 0 orphan processes after 10 forced editor kills (Job Object). Port collisions handled. Cold start to first token measured on each reference machine. Correct backend reported (Vulkan device name or CPU fallback) on NVIDIA, AMD or Intel and CPU-only. No Windows Firewall prompt when bound to 127.0.0.1 [U]. |
| S3 | **Embedded `llama-cpp-2`.** `cargo build --features embedded-llama` with `vulkan` + `llguidance` (+ `dynamic-backends`) on a clean Windows 11 VM from documented prerequisites only | A new contributor can build from the documented steps. Clean build time and release-binary size delta are recorded. Greedy output is token-identical to llama-server of the same llama.cpp commit on 20 prompts. llguidance-constrained output is 100% schema-valid on 200 prompts. Cancel latency is ≤1 decode step. Corrupted or truncated synthetic GGUF files **and** OOM-sized contexts either return an error or are proven to abort. If they abort, in-process mode is disallowed and the worker-process design is used. |
| S4 | **Model download manager.** hf-hub 1.0.0 vs reqwest + Range, pinned revision + SHA-256 | Resume after a mid-download kill works 10/10. A tampered file is rejected. Install is atomic (no partial model visible). The low-disk pre-check triggers. HF token handling works for a gated repo. Progress events reach the UI at ≥2 Hz. |
| S5 | **Chat-template fidelity.** Render each candidate model's GGUF template with minijinja and compare against llama-server `--jinja` output | Byte-identical prompts for system, user and assistant turns, tool turns, and thinking on/off for every model we plan to qualify. Mismatches are either fixed or the model is marked sidecar-only. |
| S6 (optional) | **Pure-Rust comparison.** candle 0.11 CPU + `toktrie_hf_tokenizers`/llguidance on the same GGUF | Report tokens/s against llama.cpp CPU on the same machine, the actual context limit, and constraint validity. Pursue it only if within an agreed factor (to be set by maintainers) **and** ≥8k usable context. |

**Go/no-go:**

- Phase B ships when S1, S2 and S4 pass.
- Phase C (`embedded-llama`) merges only when S3 and S5 pass.
- Nothing is advertised as "runs on 8 GB" until the harness's own workload passes on the
  8 GB VM. No minimum hardware has been established for any candidate model yet [U].

## Open questions

- **Project license.** GPL-3.0-or-later (if CWR code is reused) or permissive? This decides
  whether CUDA can ever be bundled (§7). Legal review is needed for the CUDA/GPL
  interpretation and for Foundry Local core and DirectML redistribution terms.
- Does llama-server stop generation when a client disconnects? This is [U] and is answered by
  S1/S2. (Upstream prebuilts are built without llguidance, per §3. Confirm this at runtime.)
- Does ggml abort the process on malformed GGUF or allocation failure in current builds? This
  decides whether in-process mode is safe (S3).
- Is the 4096-token limit a candle 0.11 limitation or specific to rig-candle? Check the candle
  source if S6 runs.
- Target minimum hardware: 8 GB RAM with an iGPU, or 16 GB? It is unestablished for every
  candidate model.
- Do NPUs (Intel via OpenVINO, AMD Ryzen AI via Lemonade, Qualcomm via QNN/WinML) give a
  better experience than Vulkan iGPU for 3–4B models on Windows laptops? Unmeasured.
- Should the "built-in" model run whenever the editor is open, or only on demand? What
  unload policy should apply around Preview (game launch)?
- Will `mistralrs` resume crates.io releases, or add Vulkan? Either would make it a
  pure-Rust embedded contender.
- What will burn's announced burn-lm successor provide, and when?

## Sources

Local reference clones (pinned):

- `0xPlaygrounds/rig@42f4e060ef:crates/rig-candle/README.md#L3-L5`, `#L29-L36`, `#L48-L52`, `#L54-L86`, `#L88-L92`, `#L105-L113`, `#L127-L132`, `#L162-L166`, `#L171-L172`
- `0xPlaygrounds/rig@42f4e060ef:Cargo.toml#L152`, `#L193-L195`
- `0xPlaygrounds/rig@42f4e060ef:crates/rig-core/src/providers/llamacpp/completion.rs#L17-L48`
- `0xPlaygrounds/rig@42f4e060ef:crates/rig-typesafeai/README.md#L87-L88`
- `openai/codex@e72da2b538:codex-rs/ollama/src/lib.rs#L15-L70`
- `openai/codex@e72da2b538:codex-rs/lmstudio/src/lib.rs#L7-L45`
- `openai/codex@e72da2b538:codex-rs/lmstudio/src/client.rs#L69-L97`, `#L173-L184`
- `earendil-works/pi@2b0a123de9:packages/coding-agent/docs/llama-cpp.md#L3-L87`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D047-llm-config.md#L28-L39`, `#L73-L102`, `#L133-L141`
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:research/pure-rust-inference-feasibility.md#L483`, `#L701-L705`

Web (fetched 2026-09-26):

- <https://crates.io/crates/llama-cpp-2> ; <https://docs.rs/crate/llama-cpp-2/latest/features> ; <https://docs.rs/llama-cpp-2/latest/llama_cpp_2/> ; <https://docs.rs/llama-cpp-2/latest/llama_cpp_2/sampling/struct.LlamaSampler.html> ; <https://docs.rs/llama-cpp-2/latest/llama_cpp_2/model/struct.LlamaModel.html>
- <https://github.com/utilityai/llama-cpp-rs> ; <https://raw.githubusercontent.com/utilityai/llama-cpp-rs/main/llama-cpp-sys-2/Cargo.toml> ; <https://raw.githubusercontent.com/utilityai/llama-cpp-rs/main/llama-cpp-sys-2/build.rs> ; <https://raw.githubusercontent.com/utilityai/llama-cpp-rs/main/llama-cpp-2/src/llguidance_sampler.rs> ; <https://github.com/utilityai/llama-cpp-rs/issues/1150> ; <https://docs.rs/kapsl-llama-cpp-sys-2/latest/llama_cpp_sys_2/>
- <https://github.com/ggml-org/llama.cpp> ; <https://github.com/ggml-org/llama.cpp/releases/tag/b11201> ; <https://github.com/ggml-org/llama.cpp/releases/expanded_assets/b11201> ; <https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md> ; <https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md> ; <https://github.com/ggml-org/llama.cpp/blob/master/docs/llguidance.md> ; <https://github.com/ggml-org/llama.cpp/blob/master/docs/function-calling.md> ; <https://arxiv.org/html/2605.20706v1>
- <https://crates.io/crates/mistralrs> ; <https://github.com/EricLBuehler/mistral.rs> ; <https://github.com/EricLBuehler/mistral.rs/releases> ; <https://github.com/EricLBuehler/mistral.rs/pull/899> ; <https://ericlbuehler.github.io/mistral.rs/quickstart/>
- <https://crates.io/crates/candle-core> ; <https://github.com/huggingface/candle/issues/3985> ; <https://github.com/FerrisMind/candle>
- <https://crates.io/crates/burn> ; <https://github.com/tracel-ai/burn-lm>
- <https://crates.io/crates/ort> ; <https://docs.rs/ort/latest/ort/ep/index.html> ; <https://github.com/microsoft/onnxruntime> ; <https://github.com/microsoft/onnxruntime/releases/expanded_assets/v1.30.0> ; <https://github.com/microsoft/onnxruntime-genai> ; <https://github.com/microsoft/onnxruntime-genai/releases>
- <https://github.com/microsoft/DirectML> ; <https://learn.microsoft.com/en-us/windows/ai/new-windows-ml/overview>
- <https://crates.io/crates/kalosm> ; <https://github.com/floneum/floneum> ; <https://github.com/floneum/floneum/commits/main> ; <https://github.com/huggingface/ratchet>
- <https://crates.io/crates/llama_cpp> ; <https://crates.io/crates/openvino>
- <https://crates.io/crates/llguidance> ; <https://github.com/guidance-ai/llguidance> ; <https://crates.io/crates/toktrie_hf_tokenizers> ; <https://crates.io/crates/outlines-core> ; <https://github.com/mlc-ai/xgrammar>
- <https://crates.io/crates/hf-hub> ; <https://docs.rs/hf-hub/latest/hf_hub/> ; <https://crates.io/crates/minijinja> ; <https://crates.io/crates/schemars>
- <https://github.com/ollama/ollama> ; <https://github.com/ollama/ollama/releases> ; <https://docs.ollama.com/gpu> ; <https://docs.ollama.com/capabilities/structured-outputs>
- <https://lmstudio.ai/docs/developer/openai-compat/structured-output> ; <https://lmstudio.ai/blog/free-for-work> ; <https://lmstudio.ai/app-terms>
- <https://github.com/lemonade-sdk/lemonade>
- <https://github.com/microsoft/Foundry-Local> ; <https://docs.rs/foundry-local-sdk/latest/foundry_local_sdk/> ; <https://devblogs.microsoft.com/foundry/foundry-local-ga/>
- <https://docs.vllm.ai/en/stable/getting_started/installation/gpu/> ; <https://docs.vllm.ai/en/latest/features/structured_outputs.html>
- <https://www.apache.org/licenses/GPL-compatibility.html> ; <https://docs.nvidia.com/cuda/eula/index.html>
- Added during verification: <https://raw.githubusercontent.com/ggml-org/llama.cpp/master/.github/workflows/release.yml> ; <https://raw.githubusercontent.com/ggml-org/llama.cpp/master/CMakeLists.txt> ; <https://github.com/ggml-org/llama.cpp/releases> ; <https://github.com/huggingface/ratchet/commits/master> ; <https://github.com/microsoft/Foundry-Local/blob/main/LICENSE> ; <https://docs.rs/llama-cpp-sys-2/latest/llama_cpp_sys_2/all.html> ; <https://github.com/EricLBuehler/mistral.rs/commits/master>

## Verification notes (2026-09-26)

An adversarial fact-check re-opened every local code citation in the pinned clones and
re-fetched the primary web sources.

**Confirmed as written:**

- `llama-cpp-2` 0.1.157 (2026-09-22, MIT OR Apache-2.0), its feature list and llguidance
  ^1.7.5, and its sampler methods.
- Issue #1150 is open with no replies. llama-cpp-sys-2 0.1.157 has no OAI-chat or tool items.
- `build.rs` uses bindgen and cmake and reads `VULKAN_SDK`, `VULKAN_GLSLC` and `CUDA_PATH`.
  `dynamic-backends` sets `GGML_BACKEND_DL`.
- candle-core 0.11.0 features, and candle issue #3985.
- All rig-candle, codex, pi and Iron Curtain (D047 and the feasibility note) line citations.
- The mistral.rs quickstart (Windows is CPU), crates.io 0.8.1 vs v0.9.4, and PR #899.
- The burn-lm archive, the onnxruntime-genai APIs and v0.16.0, the DirectML maintenance note
  and the Windows ML 24H2 requirement.
- CUDA EULA §1.2 and the ASF GPLv3 statement.
- All b11201 and ORT 1.30.0 asset sizes.
- The llama-server flags (`--api-key`, `--models-dir`, `--models-preset`, `--models-max`,
  autoload) and `response_format` json_schema.
- The function-calling doc quotes, `docs/llguidance.md`, llguidance 1.8.0 and its README claims.
- The Ollama Vulkan quote, the `format` field, MIT, and v0.34.4 / v0.40.0 pre-release.
- kalosm 0.4.0 and the `fusor` placeholder, hf-hub 1.0.0, the LM Studio terms and the
  <7B warning.
- vLLM on Windows, and the minijinja, schemars, outlines-core, burn, ort, openvino, llama_cpp
  and toktrie_hf_tokenizers versions.
- XGrammar-2 (2026/5) and the xgrammar-rs "Third-Party Bindings" listing.

**Changed:**

- The "~14 MB library" text was rewritten as the manifest's actual wording.
- The CUDA EULA quote now uses its exact words.
- "mistral.rs has no Vulkan" is now "documents no Vulkan".
- `--jinja` is now documented as default-enabled.
- Upstream llama.cpp tags are labelled "Pre-release", so the plan pins exact tags.
- llama.cpp's OpenVINO backend is marked "[In Progress]".
- The question of llguidance in prebuilts is resolved as "not included" (CMake default `OFF`,
  and release.yml never sets it).
- ratchet was marked dormant (last code commit 2024-11-23).
- Lemonade's base URL is now `/api/v1`.
- Foundry Local: the core's license terms are now marked unverified, "Metal" was replaced by
  the stated platforms, and a note says the CLI is still a preview.
- vLLM on Windows is now "WSL or community forks", not "Docker".
- The Jev quote was completed.
- The disk-space step no longer misuses rig-candle's RAM-during-load note.
- The hf-hub "HF-cache-compatible" wording was softened.
- A missing `#L184-L189` citation was added.

**Not independently verified:** that the 4096-token limit applies to candle generally (it is
still [U]), and whether unofficial onnxruntime-genai Rust wrappers exist. A crates.io search
found only `onnx-genai-genai-config` 0.1.0-dev.6.
