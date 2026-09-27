# D023: Model strategy: no bundled weights, bring your own model, qualified local tiers

> **Status:** accepted · **Decided by:** owner (bring your own model, AI optional) and research (docs 14, 16) · **Decided:** 2026-09-26
> **Recorded:** 2026-09-27 · **Scope:** which models Plotroom supports and how it chooses among them.
> **Related:** D004, D009, D021, D022, D024, D026. **Open parts:** OWQ-19 (recommended-model policy; answered 2026-09-27 → D037);
> doc 14 §9 measurements.

## Context

- Wilco is optional and the user brings the model, cloud or local (README). Users pay for their own calls or hardware (doc 40).
- Public data shows small models are weak at multi-turn tool use; no public benchmark covers SQF/SQS or Czech, Polish and Russian
  creative text (doc 14 TL;DR). Doc 25 shows that a harness of small typed decisions lets weak models contribute safely.
- Decision models (Jev, Kev, Laya, CLM) choose among options but cannot write; none has been measured on editor tasks (doc 16 TL;DR).

## Decision

1. **No model weights in the installer.** Three paths, all first-class:
   - **No AI**: every core feature works; templates, wizards, lints and deterministic tools (model tier T0);
   - **local models**, installed through the Model Manager (D022);
   - **bring your own key or endpoint**: cloud APIs and local servers such as Ollama, LM Studio or llama.cpp.
2. **Model tiers** (doc 14 §6): T0 no AI; T1 local small (about 16 GB RAM); T2 local medium (T2a: 8–12 GB VRAM or 32 GB RAM; T2b:
   16 GB VRAM and up, or MoE offload); T3 cloud frontier. Named models in doc 14 are **candidates**, not defaults, until Plotroom's
   own evaluations qualify them per step shape.
3. **No workflow requires a strong model** (D009). Stronger setups may take larger steps once qualified; a failed step is split into
   smaller ones, never silently moved to another model; switching models is a visible user choice with its cost (doc 25 §10.2).
4. **Roles, not models, in workflows**: steps declare a role; the user binds roles to models (D024).
5. **No decision model in front of the generative model in v1.** A `Selector` seam returns `Candidate | NoMatch | Clarify`; the
   deterministic and generative selectors ship first; a decision model earns an advisory slot only by beating both on our instruments
   (doc 16 §4–§5).
6. Default local downloads are **OSI-licensed weights**; models with pass-through use restrictions are bring-your-own, with the licence
   shown (doc 02 TL;DR; OWQ-19).

## Alternatives considered

- Bundle a default model: installer size, licences, and a model that ages quickly.
- Cloud-only AI: excludes offline users and costs every user money.
- Require a frontier model for the campaign flow: contradicts the weak-model invariant and the cost requirement (D026).

## Consequences

- Model ids are pinned and kept in an editable `models.toml` with dated prices (D021, D026).
- A capability probe per endpoint and model chooses a prompt profile (doc 14 §7).
- Creative text in non-English locales needs native-speaker review; code enforces each language's legacy code page (doc 14 TL;DR).
- Label clash with plugin tiers: write "model tier T1" (D007).

## Sources

README; doc 02 TL;DR; doc 14 (TL;DR, §1, §6–§9); doc 16 (TL;DR, §4–§5); doc 25 (TL;DR, §10.2); doc 40 TL;DR.

## Amendment notes

### 2026-09-27: owner answer to OWQ-19 and provisional local defaults

- **Recommended-model policy (owner, OWQ-19 (a)).** The Model Manager's recommended list holds only models under OSI licences with no
  field-of-use limits that passed Plotroom's qualification; everything else installs as "custom", with its licence and use policy
  shown, an explicit acceptance and an "unqualified" badge until qualified. The rule is stated in
  [D037](D037-model-manager-recommended-list.md), which governs decision 6 from now on; this note only points to it.
- **Provisional local defaults (research, doc 46; proposal, not an owner decision).** On the managed llama.cpp sidecar (D022,
  amendment of 2026-09-27), for 8 GB GPUs: **Gemma 4 E4B QAT** (Unsloth's QAT Q4_0 file) as first choice, recommendable only once its
  licence-tag mismatch is resolved (GGUF `general.license` says `gemma`, the model card Apache-2.0), and, as doc 46 §4.1 asks, after
  Google's official QAT Q4_0 file is measured; **Qwen3.5-4B Q4_K_M** as the equal alternative; **not the 4-bit UD dynamic files**
  for these two models (nor the non-QAT Gemma files), which showed no detectable gain for more memory, less speed and a larger
  download. Unsloth's QAT file carries "UD-Q4_K_XL" in its name but is uniform Q4_0, so the exclusion does not cover it. One model
  per session on 8 GB. Both stay candidates under decision 2 until qualified: doc 46's spike checks passed on Pick for both and on
  `pick-hard` for Gemma only, and neither passed whole-record Fill (doc 46 §4.1); doc 49 (the measured local shortlist from doc 47)
  may replace them. The manifest records both licence fields, and a mismatch blocks a recommendation (doc 46 §4.1; doc 47 TL;DR:
  licences are read at the pinned revision; D037).
- **Cloud (proposal, doc 48 §7.2).** Cloud recommendations should name endpoints, not only models, because precision, schema support,
  retention and price differ by host; the round-1 measurements are deferred by the owner until doc 49 exists (owner decision,
  2026-09-27). See D021's amendment note.

### 2026-09-27: pointer and citation fixes (consistency review)

The header's **Open parts** points OWQ-19 to D037, the note above names D037 where it had a placeholder, and the provisional defaults
now state doc 46's per-step results and its Google-file condition instead of a blanket "spike-checked". No decision changed.
