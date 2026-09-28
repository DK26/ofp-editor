# D022: Local inference path and the Model Manager

> **Status:** accepted (Model Manager, owner) · baseline (runtime path, research) → accepted (runtime path, owner, 2026-09-27; see
> the amendment note) · **Decided by:** owner and research (doc 13)
> **Decided:** 2026-09-26 (runtime), 2026-09-27 (Model Manager) · **Recorded:** 2026-09-27
> **Scope:** running models on the user's machine; finding, qualifying and installing them. **Related:** D001, D008, D021, D023, D026.
> **Open parts:** OWQ-19 (which models the Manager may recommend; answered 2026-09-27 → D037); doc 21 OQ3 (badge wording); doc 13
> spikes (§11).

## Context

- Weights dominate size (a 4B Q4 GGUF is about 2.3 GiB); they must be optional downloads, never part of the installer (doc 13 TL;DR).
- A native crash inside the editor process would lose unsaved work, so out-of-process inference is safer by default (doc 13 TL;DR).
- The owner wants a **Model Manager** that recommends local models that fit the user's hardware, shows qualification badges, and
  downloads and installs them in the editor, including directly from Hugging Face.

## Decision

1. **One inference seam** (behind D021) with three backends: (1) a remote API; (2) a local OpenAI-compatible server (llama-server,
   Ollama, LM Studio and others), including a **managed llama-server sidecar** that Plotroom downloads, verifies and supervises; (3) an
   in-process engine built on `llama-cpp-2`, behind a cargo feature, added only after its safety spike passes (doc 13 §11, S3).
   Backends (1) and (2) ship first.
2. **Out-of-process by default.** Plotroom's own builds offer Vulkan, Metal or CPU; CUDA is reached only through a user-installed or
   upstream-downloaded server, never bundled with GPL builds (doc 13 TL;DR, NVIDIA EULA). NPU paths come later, through external servers.
3. **Typed output** comes from constrained decoding plus validation: JSON Schema from Rust types, `json_schema` on servers, a grammar
   engine in process; every result is parsed and admitted like any other proposal (doc 13 TL;DR; D009).
4. **The Model Manager** (owner decision):
   - detects the machine's memory, GPU and backend and recommends models that fit, by model tier (doc 14 §6);
   - shows a **qualification badge** per model setup and step shape, from Plotroom's own instruments (doc 21 §3.3, §12;
     `tools/local-qual/`), never from vendor claims alone;
   - downloads and installs in the editor, including from Hugging Face, through a pinned manifest (repository, revision, file, size,
     SHA-256, licence): resumable, hash-verified, atomically installed;
   - follows D008: the source is enabled by the user, blocked offline, and every download is started by the user, never by Wilco.

## Alternatives considered

- candle, mistral.rs, burn, ort or kalosm as the embedded engine: missing Vulkan or DirectX backends, constrained decoding or recent
  releases at research time (doc 13 TL;DR).
- Bundling weights or CUDA: installer size, licence conflicts and use-policy pass-through (doc 02 TL;DR; doc 13 TL;DR).
- "Bring your own server" only, with no Manager: leaves non-experts without a working local path.

## Consequences

- `hf-hub` is the candidate download client; resume and verify behaviour is confirmed by a spike before use (doc 13 TL;DR).
- A user-chosen Hugging Face file that is not in Plotroom's list installs with its licence shown and an "unqualified" badge until the
  user runs qualification (proposal; OWQ-19).
- Qualification is re-run when a setup changes (model, quantisation, chat template, sampler, runtime); what else voids it is DG012.
- The storage panel shows installed models and their disk use (doc 34 mo05, mo18).

## Sources

Doc 13 (TL;DR, §4, §11); doc 14 (§5–§7, §9); doc 21 (§3.3, §12, OQ3); doc 02 TL;DR; doc 34 (mo05, mo18); `tools/local-qual/README.md`;
DG012; DG028.

## Amendment notes

### 2026-09-27: the owner's local-runtime decision

A note under the lifecycle rules (`docs/decisions/README.md`): it narrows items 1–2 and the Consequences, reverses nothing, and makes
the runtime path an owner decision instead of a research baseline. Evidence: doc 46 (one 8 GB Pascal GPU, measured 2026-09-27).

1. **Primary local runtime: the managed `llama-server` sidecar** (item 1, backend 2). **Ollama and LM Studio stay optional
   bring-your-own endpoints**, reached through the same OpenAI-compatible seam (D021).
2. **Builds.** Plotroom's own sidecar builds are Vulkan, Metal or CPU (item 2), taken from upstream releases pinned by build tag and
   asset SHA-256 (doc 46 §4.2). CUDA never ships in a Plotroom artefact; the user may start an optional download of an upstream CUDA build for the sidecar
   (doc 13 §3), under D008. Whether it is offered on NVIDIA cards waits for a CUDA-versus-Vulkan measurement (doc 46 OQ1; doc 47
   §6.2 item 2 plans one for doc 49): Vulkan on the reference card processed prompts at 215–337 tokens/s against Ollama's 620–710,
   though Ollama's backend was not logged and its rate may count cached tokens, so doc 46 compares the end-to-end p50s below (§2.6).
3. **Pinned Hugging Face downloads through Plotroom's own downloader**: repository, commit, file, size and SHA-256 from the Hugging
   Face API; `resolve/<commit>/<file>` with range resume; hash check; atomic rename; the sidecar starts with `-m <file>`. Not
   `llama-server -hf`, which has no revision pin and follows `main` (doc 46 §1.3, §4.1).
4. **Refuse GGUFs the pinned runtime cannot run**: unknown tensor types or unsupported metadata are refused before loading, because a
   stock build can load such a file and generate nonsense (doc 47 §2.7, the fork-only ternary packings). Forks are never managed; a
   user may point Plotroom at one as a bring-your-own endpoint, badged "unqualified" (OWQ-19; D037).
5. **Pin samplers explicitly** on every request: temperature, top_k, top_p, min_p, the penalties (presence and frequency 0 and repeat
   1 for Pick and Fill), seed and the thinking switch; GGUF, server and Ollama build defaults are never relied on, and the effective
   values are recorded with each result (doc 46 §2.2: a hidden presence penalty of 1.5 in an Ollama build).

Evidence [V per doc 46; one 8 GB Pascal card, 30 menus per suite]: no detectable Pick quality difference between llama.cpp and
Ollama in 16 paired comparisons (not a proof of equivalence); 859–1,281 MiB less GPU memory at peak on llama.cpp than Ollama's library
builds, which also carry vision parts; slower warm Pick on the Vulkan build (p50 1,046–1,126 ms against 590–700 ms); all five pinned
downloads verified. **Open parts now:** OWQ-19 is answered (a) and has its own record,
[D037](D037-model-manager-recommended-list.md), which governs the recommended list; doc 21 OQ3; doc 13 S1,
S2 and S4 (doc 46 covered S1's parse criterion and part of S2); doc 49's CUDA bench. `hf-hub` becomes optional (SP-14 decides),
since the three plain endpoints above were enough; the sidecar records file names only, never local paths (doc 46 §4.2).

### 2026-09-27: pointer and citation fixes (consistency review)

The header's status and **Open parts** gained pointers (runtime path → this note; OWQ-19 → D037), the note above names D037 where it
had a placeholder, and its doc 46 figures now carry doc 46's own qualifiers. No decision changed. Consequences line 2 ("proposal;
OWQ-19") is settled by D037 decision 2.

### 2026-09-28: refined by D056 (encoders stay out of process)

A note under lifecycle item 5; [D056](D056-encoder-inference-out-of-process.md) governs (DG052), decided under the owner's delegation;
the owner may overrule it on return. Item 2's out-of-process rule, and the architecture's "embedded inference always out of process"
resolution, cover encoder components too: no encoder runs its model inside the editor process. For now, encoders are only the
rerankers and embedders the pinned sidecar serves; a helper process with a telemetry-free, reproducible ONNX Runtime build (doc 58
tier H) is admitted for other encoders only if spike S-ENC meets doc 58's evidence bar, recorded as a note on D056; until then encoder
arms are offline research only (doc 53 §4.9). The Alternatives' reasons against `ort` and candle were about generative engines (doc
58 finding 3); D056 states the encoder case. Item 1(3), the in-process generative backend, is not decided by D056. The header has no
open part to mark; nothing above changed.
