# DG032: One knowledge store and one tool family

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
> **Decision by: technical** (design round). Blocks: the agent's lookup tools (doc 21 §1.3 `Lookup` and `Check` variants), the
> Standing Orders tool set (doc 33 phase 1), tool names in `skills/*/SKILL.md`.

## Context

- **Doc 21 §10.2**: named, budgeted lookups `catalog.find`, `island.places`, `script.command`, `reference.search`.
- **Doc 23**: the `ofp-script` crate exposes `check_field(FieldKind, &str, Profile)` (a Rust function, §13.2) and the agent's
  `validate_script` tool (§15, phase P3).
- **Doc 30 §4.4** (names provisional): `script.command` (framing name lookup_command), `reference.search`, `reference.card`
  (schema_card), `diagnostic.explain`, `script.check` (validate_script, check_field), `script.complete`, `catalog.find`
  (list_classes), `island.places`, `next_step`. **OQ7**: consolidate these names across docs 21, 23 and 30.
- **Doc 33 §6.1**: `list_concepts`, `explain_concept(id, depth)`, `explain_instance(handle)`; "These overlap doc 30 §4.4's
  `reference.search` and `reference.card` … one family should survive." **OQ10**: do doc 30's cards and this registry merge into one
  store and one tool family? **Pedagogy finding 10**: the seed SKILL.md names doc 30's tools, not §6.1's.
- The seed Standing Orders SKILL.md tells the model to use `reference.search`, `reference.card`, `script.command`, `catalog.find`.

## The gap

Two stores (doc 30 reference cards; doc 33 concept registry) and three naming sets serve overlapping jobs. A small model choosing
between near-synonyms (`reference.card` versus `explain_concept`) is exactly what the weak-model doctrine avoids.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Doc 30's family survives; concept entries are served as cards through `reference.card` | Already in the skills; dotted namespacing fits doc 21 §10.2 | `explain_instance` has no doc 30 equivalent |
| B | Doc 33's three tools survive; doc 30 names become aliases | Clear teaching semantics (depth, instance) | Two naming styles remain; aliases still confuse models |
| C | **One store, one family**: the Standing Orders registry holds concept entries and doc 30's model-facing cards as entry kinds in one id namespace (DG031); tools `reference.search(text, kind?, anchor?)`, `reference.card(id, depth: card \| full)`, `reference.explain_instance(handle)`, `diagnostic.explain(code)`; language-service tools `script.command`, `script.check`, `script.complete`; data tools `catalog.find`, `island.places` | One place to author and verify facts (doc 33 principle 1: one source for human and model); one lookup path for weak models | Doc 30's card format (≤ 150 words, fact ids) and doc 33's entry format must merge |

## Recommended resolution (proposal)

Option C. Doc 30 cards become registry entries of a model-facing kind whose body is capped (≤ 150 words) and whose facts carry the
same grounding type as concept entries (doc 33 §3.2). Retired names: `list_concepts`, `explain_concept`, `explain_instance` (as bare
names), and the framing names `lookup_command`, `validate_script`, `schema_card`, `list_classes`, `explain_diagnostic`.
`check_field` stays the internal Rust function in `ofp-script`, not a tool. An unknown term still returns `NotInManual { term }` with
no model call (doc 33 §6.1). Tool names stay provisional until the doc 21 tool registry is implemented; SKILL.md files are updated
in the same change that lands the registry.

## What it would change

- Doc 21 §10.2: the family list.
- Doc 23 §15 (tool naming): `validate_script` → `script.check`.
- Doc 30 §4.4 table and OQ7 (answered); §4.6 knowledge activation reads the shared registry.
- Doc 33 §3.3 ("the primer stays small"), §6.1 table and OQ10: answered; pedagogy finding 10 closed.
- `skills/standing-orders/SKILL.md` and `skills/mission-primer/SKILL.md`: tool names.

## Affected docs

Docs 21, 23, 30, 33; both skills; DG031.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 21 §10.2, doc 23 §13.2 and §15, doc 30 §4.4, §4.6 and OQ7, doc 33 §3.3, §6.1, OQ10 and
  pedagogy finding 10, and the seed Standing Orders SKILL.md, re-read on 2026-09-27.
