# D020: Templating with minijinja

> **Status:** accepted · **Decided by:** owner, on docs 22 and 31 · **Decided:** 2026-09-27 · **Recorded:** 2026-09-27
> **Scope:** every text template: module lowerings, compositions, shot templates, prompt templates, briefing styles, local chat templates.
> **Related:** D007, D015, D019, D025. **Open parts:** DG003 (parameter vocabulary), DG007 (one definition format).

## Context

Modules, compositions, cinematic shot templates and prompts are data that must be shareable as T0 packs (doc 22 §2.1), render the same
way every time, and never let a pack author bypass the validators. Doc 22 compared `minijinja` and `tera`; doc 17 §5 named both.

## Decision

1. Templates use **`minijinja`** (Apache-2.0) with its **`fuel`** feature and **no file loader**.
2. Rendering is **pure** (a template and typed parameters in, a string out) and happens at compile or export time, never when the game
   loads a mission.
3. Rendered output is **parsed, linted and validated like a paste**; a template can never bypass a validator.
4. Templates are T0 data referenced by typed definitions; per-profile variants are separate templates (doc 31: a module's lowering maps
   a profile set to a template).
5. The dependency is pinned (3.0 alpha versions exist) and upgraded deliberately with a golden-render check.

## Alternatives considered

- `tera` (MIT): the alternative doc 22 §2.1 names; minijinja was preferred for its `fuel` feature against expensive templates and
  because it loads no files by default.
- Hand-written string building per module: blocks community modules as data packs.
- Load-time templating inside the game: not possible without an engine feature; export-time rendering is what the engine can run.

## Consequences

- Every render has fuel and output-size caps; pack text that fails under fuel is refused by a load-time lint (doc 38 §6).
- Golden tests render every built-in template for each profile from synthetic fixtures.
- Local models' chat templates are rendered with the same library and checked against the inference server's output (doc 13 spike S5).
- Template text copied into user output is original work and covered by the generated-content permission (D001, OWQ-01).

## Sources

Doc 13 (§11, spike S5); doc 17 §5–§6; doc 22 (§2.1, §7); doc 31 (§4.2, §4.8); doc 32 §5.1; doc 34 row "Platform extras" (export-time
templating); doc 38 §4, §6.
