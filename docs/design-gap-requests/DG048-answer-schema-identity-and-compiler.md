# DG048: Answer schema identity per harness preset, and one schema compiler

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-28 in the go-ahead pass (design-gap candidates of docs 51–63).
> Status: **open**.
> **Decision by: technical** (design round; the creative-text envelope by doc 51 §5's E arm). Blocks: per-model answer conventions in
> presets (doc 55 §2.1); doc 51 §4.4's schema modes; the cloud form of local grammars.

## Context

- **DG015** (open): Pick uses one frozen letter schema; Fill, Compose and Draft carry a `SchemaId`, and the loader refuses a schema
  that differs from the one registered for the step's `DecisionKind`, so doc 40 R4's cache namespace stays stable.
- **DG024** (open): no per-request dynamic enums in cloud schemas; local engines keep per-request grammars.
- **Doc 55 §7 items 3 and 6.** A per-model field name, option-key form or leading `why` needs the freeze to be per (`DecisionKind`,
  harness preset), and "the cache namespace already includes the model setup". Verbatim span grammars run locally; a cloud preset
  needs "an explicit validator-only form of the same knob".
- **Doc 51 §4.3–§4.5, §6.1 items 8 and 14.** Schema dialect and keyword capabilities are profile facts (DG045); schema mode per step
  kind, envelope and compact whitespace are preset choices; the answer field name is a convention (Qwen's `answer`). The schema
  compiler produces the portable subset by construction (no `$ref`, explicit types, single-type enums, closed objects, all required,
  no `default`), per-dialect normalisers restating stripped constraints in descriptions, a lint and canonical serialisation;
  admission always validates "against the full original schema, including constraints the dialect normaliser stripped" (§4.5 step 7).
  Creative text is JSON-wrapped today; §5's E arm tests plain bounded or tagged text.
- **DG046** decides whether a leading `why` field exists per preset.

## The gap

Schemas are frozen per `DecisionKind`, while presets need per-model conventions and cloud endpoints need dialect-normalised forms.
No component is named as the source of every schema, grammar and validator, and no identity rule says when two of them are "the same
schema" for caching, qualification and journaling.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | One hand-written schema per `DecisionKind`; each adapter handles its dialect | Simplest identity | Per-model conventions impossible; each adapter re-derives constraints and can drop one silently |
| B | Schema identity per (`DecisionKind`, harness preset); one compiler generates every schema, grammar and cloud validator from the `DecisionKind`'s typed answer (doc 51's portable subset, normalisers, lint, canonical bytes); admission always against the full original schema; a local grammar and a cloud validator-only check are two renderings of one knob | One source of truth; the namespace stays stable per (`DecisionKind`, preset) | A compiler to build and test |

## Recommended resolution (proposal)

B (docs 51 and 55). DG015's rule for Pick (no `schema` key on a Pick step) and DG024's cloud rule stay, as outputs of the compiler.
The creative-text envelope (doc 51 §6.1 item 14) is decided by doc 51 §5's E arm.

## What it would change

- DG015 and DG024 (identity per preset; compiler as the producer); doc 40 R4–R5; doc 51 §4.4; doc 55 §2.1 and §3.3; the definition
  compiler (doc 38 §6.2: a schema-dialect lint).
- Tests first (proposal): every generated schema passes the lint; a normalised cloud schema plus its restated constraints admits
  exactly what the original admits on a fixture set; canonical bytes are identical across runs (prefix goldens, doc 57 CL2).

## Affected docs

DG015; DG024; DG046; doc 40 (R4–R5); doc 51 (§4.3–§4.5, §5, §6.1); doc 55 (§2.1, §3.3, §7); doc 38 §6.2; D048.

## Decision record

Open.

## Verification notes

### Filing (2026-09-28)

- Filed from doc 55 §7 items 3 and 6 and doc 51 §6.1 items 8 and 14 (deduplicated), re-read on 2026-09-28 with DG015, DG024 and doc
  51 §4.3–§4.5.
