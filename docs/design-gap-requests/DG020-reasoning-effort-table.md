# DG020: One measured reasoning-effort table per shape and provider

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass (doc 40 gap G2).
> Status: **open**. **Decision by: technical** (measurement, instrument E12). Blocks: the effort mapping in `ofp-agent-rig`; doc 40 R6 stays
> `proposal-only`.

## Context

Reasoning ("thinking") effort is stated four ways:

- **Doc 21 §7.1** "Provider reasoning" row: Quick "off / lowest", Standard "provider default", Thorough "on where measured to help
  that role", Max "highest measured setting".
- **Doc 25 §4.4**: provider thinking "only where measured to help that step and model".
- **Doc 14 §8**: Quick "off / `low`", Standard "`low`–`medium`", Thorough `high`, Max `xhigh`/`max`.
- **Doc 12 §3.3** "Off" row: OpenAI `ReasoningEffort::None`; Gemini `thinking_budget: Some(0)`; Anthropic "no off level: use `low`".
- **Doc 40 §2.5** [V, 2026-09-27]: Sonnet 5 **can** disable thinking; Opus 5.5 and Fable 5.1 cannot (lowest `low`); Gemini 3.x
  **cannot** turn thinking off (`minimal` lowest; 3.1 Pro `low`); GPT-6 Sol and Luna accept `none`, Astra does not; DeepSeek defaults
  to thinking mode. Provider defaults differ (Sonnet 5 `high`, Opus 5.5 `medium`).
- **Doc 40 R6**: a placeholder table of effort floors per shape (Pick/enum Fill/extraction; text slot; Compose; Draft) and provider.

## The gap

"Provider default" at Standard means `high` on Sonnet 5 and `medium` on Opus 5.5, so the same preset costs very different amounts;
doc 12 §3.3's "Off" row is wrong for Gemini 3.x and too coarse for Anthropic; no doc owns a per-shape table.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Keep per-effort-level rows (docs 14, 21) | Simple UI mapping | Ignores step shape, the largest lever (doc 40 OQ1) |
| B | One table per (shape × provider or model), as data beside prices in `models.toml` (doc 40 R1), filled from instrument E12 | Measured, per model, updatable without code | Needs E12 before it is final; placeholders until then |

## Recommended resolution (proposal)

Option B. The effort preset sets a **ceiling**; the table sets each shape's **floor** per model; the runtime uses the floor unless
a measured benefit justifies more, never above the preset's ceiling. Until E12 reports, doc 40 R6's placeholders apply. Doc 12
§3.3's "Off" row is refreshed per model: Sonnet 5 thinking off; Opus 5.5 and Fable 5.1 `low`; Haiku 4.5 none; Gemini 3.x `minimal`
(3.1 Pro `low`); GPT-6 Sol and Luna `none`, Astra `low`; DeepSeek non-thinking mode selected explicitly. The table records its
`as_of` date like the price table.

## What it would change

- Doc 21 §7.1 "Provider reasoning" row: "per shape, up to this ceiling (table: doc 12 §3.3 / `models.toml`)".
- Doc 14 §8 reasoning column: pointer.
- Doc 12 §3.3: per-model Off row and the shape-floor table (or a pointer to `models.toml`).
- Doc 25 §4.4: unchanged principle, pointer to the table.
- Doc 40 R6: from `proposal-only` to rule once E12 reports.

## Affected docs

Docs 12, 14, 21, 25, 40.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 40 §2.5, R1, R6, §4.3 G2 and OQ1; doc 21 §7.1; doc 25 §4.4; doc 14 §8; doc 12 §3.3, re-read on 2026-09-27.
  Provider facts are doc 40's, verified there on 2026-09-27; they were not re-fetched here.
