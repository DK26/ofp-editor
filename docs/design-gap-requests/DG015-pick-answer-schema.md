# DG015: `DecisionSpec.schema` must not be declarable for Pick

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
> **Decision by: technical** (type design). Blocks: the `ofp-workflow` definition types (doc 38 §4.7, phase W1).

## Context

- **Doc 38 §3.3**, `model` row: `{ role, decision, schema }` for every model step, and "Pick uses the menu's letter schema".
- **Doc 38 §4.7** sketch: `pub struct DecisionSpec { shape: ModelShape, role, decision: DecisionKind, schema: SchemaId, … }` with
  `ModelShape::Pick { menu: MenuSpec }`. `schema` is mandatory for every shape.
- **Doc 40 §4.1** (format line): "one frozen schema per DecisionKind (Pick: letters A-Z plus the X and Q escapes)"; **R4**: model,
  effort, schema and tool set stay fixed inside one cache namespace per (stage, DecisionKind); **R5**: "Picks answer with a letter;
  the menu text lives in the capsule; code maps letters and checks membership".
- `AGENTS.md` type-safety rule: make invalid states unrepresentable.

## The gap

A Pick step can declare any `schema` id, although its answer schema is fixed (the letter schema) and doc 40 needs it frozen per
`DecisionKind`. A definition with `kind = "pick"` and `schema = "premise@1"` would load, and the runtime would have to choose which
one wins.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | `schema: Option<SchemaId>`, required `None` for Pick (load-time check) | Small change | The invariant lives in a validator, not the type |
| B | Move the schema into the shape: `Pick { menu }` carries no schema (the letter schema is implied); `Fill { schema }`, `Compose { schema, split }`, `Draft { schema, split, tools }` | Invalid state unrepresentable; matches doc 38's pattern of putting `menu`, `split` and `tools` inside the shapes | TOML must still reject a `schema` key on Pick steps |
| C | The `DecisionKind` registry owns exactly one schema per kind (letters for Pick kinds); steps never name a schema, or name it only as an assertion that must match | Enforces doc 40's "one frozen schema per DecisionKind" for every shape | A schema migration needs a new `DecisionKind` version |

## Recommended resolution (proposal)

Option B for the types, plus C's registry check: `ModelShape::Pick { menu }` has no schema field and always uses the frozen letter
schema (A–Z plus `X` and `Q`); Fill, Compose and Draft carry a `SchemaId`, and the loader refuses a schema that differs from the
one registered for the step's `DecisionKind` (so R4's namespace stays stable). In TOML, a `schema` key on a Pick step is a load error
with a field-labelled message (a new AT-W1 fixture).

## What it would change

- Doc 38 §3.3 `model` row ("`schema` for Fill, Compose and Draft only") and the §4.7 sketch.
- Doc 38 §6.2: two new refusals (schema on Pick; schema not registered for the kind).
- Doc 25 §4.2 `DecisionPoint { schema }`: same treatment when doc 25's sketch is superseded by definitions (doc 38 §4.7).

## Affected docs

Docs 25, 38; DG024 (fixed cloud schemas).

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 38 §3.3, §4.7 and §6.2, doc 40 §4.1 and R4–R5, and doc 25 §4.2, re-read on 2026-09-27.
