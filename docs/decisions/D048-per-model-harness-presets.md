# D048: Per-model harness presets: adapt the harness to each model

> **Status:** accepted · **Decided by:** owner (direction of 2026-09-28) · **Decided:** 2026-09-28 · **Recorded:** 2026-09-28
> **Scope:** how Wilco asks each supported model for each step kind; not what code owns. **Refines:** D023 (per-model settings and
> the default), D037 (qualification is per preset and step kind). **Related:** D009, D021, D022, D027, D044, D045.
> **Open parts:** the knob catalogue, the preset file format and the tuning protocol (doc 55, draft); the expanded tuning and held-out
> suites; the first tuned presets (Qwen3.5-4B, Gemma 4 E4B, Granite 4.1 3B, the tiny tier of doc 53); how presets ship and update
> through the Model Manager under D008; re-qualification triggers (DG012).

## Context

- Measured rankings on Plotroom's steps differ from published benchmark rankings: in docs 44, 46 and 49, Gemma 4 E4B led Qwen3.5-4B
  on the harder menus and on whole-record Fill, while Qwen led on explanations, with thinking off for both.
- Models are trained for particular conventions: answer and tool-call formats, reasoning switches, sampler settings, prompt layouts.
  Model-native conventions are the subject of doc 51 (in progress).
- The owner's direction of 2026-09-28, in the owner's words: "Rather than having one general harness, and rather than train models for
  our harness, we adjust the harness towards what these models are already trained for", with pre-built presets that make the most of
  each small local model.

## Decision

1. **Presets per model, not one general harness.** Each supported model gets a preset: the harness settings that best fit it, per
   step kind (PICK, FILL, COMPOSE, creative text, EXPLAIN).
2. **Presets change how Wilco asks, never what code owns.** A preset may set the answer format, reasoning mode or budget, sampler,
   schema mode, prompt layout and exemplars, how a decision is split between the model and code, the scoring mode and cascade
   thresholds. It never changes the facts, the option computation, validation, repair limits or the product scope (D006, D009).
3. **Adapt the harness, do not train the model.** Presets are the chosen way to fit models; fine-tuning stays unchosen (D027).
4. **Measured, not guessed.** A preset is tuned on a tuning split and accepted only on a held-out split under decision rules written
   before the run.
5. **Bound and qualified.** A preset is bound to the exact model file (repository, revision, SHA-256), the runtime build and the chat
   template. Qualification badges belong to a preset and a step kind (D037), and a change to any binding voids them until
   re-qualified.
6. **Visible and overridable.** The editor shows the active preset, what it changes and its badges. The user can switch to the
   general fallback preset or edit settings (D010).
7. **A general fallback preset** serves models without a tuned preset.

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| One general harness for every model | Leaves measured per-model strengths unused, and weak spots unaddressed |
| Fine-tune models for Plotroom's harness | Training, data and maintenance cost for every model and release; the owner prefers adapting the harness (D027) |

## Consequences

- The provider layer (D021, D022) carries presets as versioned data beside the model manifest; the format and its shipping and update
  path are proposals (doc 55).
- `tools/local-qual` gains preset loading and the tuning tooling, and its suites gain tuning and held-out splits (doc 55, proposal).
- Cloud-first screening (D044) and model-native conventions (doc 51) feed the first candidate presets.

## Sources

Owner direction of 2026-09-28; docs 44, 46, 49 (in progress), 51 (in progress), 53 (draft), 55 (draft); D006; D009; D010; D021;
D022; D023; D027; D037; D044.
