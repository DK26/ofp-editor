# DG008: One condition language for campaign, mission and workflow scopes

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
> **Decision by: technical** (design round). Blocks: the rule builder's condition AST (doc 31 §5), the workflow `when` parser (doc
> 38 §3.1), lesson goal predicates (doc 33 §5.5).

## Context

- **Doc 19 §5** defines CXL: a small, pure, statically typed condition language for campaign transitions, with a visual condition
  builder as a second view of the same AST, a typechecker (lint C06) and a lowering table to SQS (§5.4).
- **Doc 31 §5.1**: "One condition language. The condition AST is doc 19's CXL, extended with mission references (`unit.x`,
  `group.g`, `marker.m`, `area.a`, `rule.r.fired`, `obj.n`) … The same projectional builder edits both." Doc 31 OQ10 still asks:
  "Extend CXL itself (one grammar, one checker) or define a sibling for mission scope?"
- **Doc 38 §3.1**: workflow `when` is "a closed predicate vocabulary over inputs and admitted values, never code" (`entry`, `set`,
  `eq`, `effort_at_least`, `all`, `any`, `not`); OQ6 asks whether CXL should replace it.
- **Doc 33 §5.5**: Drill lessons use a fourth predicate vocabulary for step goals (`holds`, `exists`, `field`, `is`).

## The gap

Up to four predicate vocabularies with overlapping operators (and, or, not, equality, membership) and no decision on whether they
share a grammar, a checker, a printer and a builder.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | One CXL grammar with **scopes**: each scope supplies its atom set and types; campaign and mission scopes lower to SQS, workflow and lesson scopes are evaluated in the editor | One parser, printer, typechecker and builder; users learn one notation; one fuzz target | The builder must show only the atoms of the active scope; scope errors need clear messages |
| B | CXL for campaign and mission scopes (doc 31's choice); keep doc 38 `when` and lesson goals as separate closed TOML/YAML vocabularies | Workflow and lesson authors write structured data, not expressions | Three evaluators and three sets of tests for the same logic |
| C | A sibling language for mission scope (doc 31 OQ10's alternative) | Mission-only atoms cannot leak into campaign code | Two grammars for one idea; contradicts doc 31 §5.1 |

## Recommended resolution (proposal)

Option A, staged:

1. **Now:** campaign and mission scopes are one CXL (doc 31 §5.1 already assumes it); answer doc 31 OQ10 with "extend CXL".
   Scope typing rejects a mission atom in a campaign guard and vice versa.
2. **Workflow scope:** atoms are workflow inputs, admitted values and `entry`; the TOML `when` may stay a structured table, but it
   is parsed into the CXL AST and checked by the same typechecker, so there is one evaluator. `effort_at_least` stays only if DG013
   keeps effort-driven gates.
3. **Lesson scope:** goal predicates (`holds`, `exists`, `field … is`) become CXL atoms over the sandbox mission, reusing the
   mission scope.
4. None of the scopes adds side effects; CXL stays pure (doc 19 §5).

## What it would change

- Doc 19 §5: a "Scopes" subsection (campaign, mission, workflow, lesson) and the rule that non-lowering scopes are evaluated in the
  editor.
- Doc 31 §5.1 and OQ10: answered by pointer.
- Doc 38 §3.1 and OQ6: `when` is CXL in workflow scope (surface syntax may stay TOML).
- Doc 33 §5.5: goal predicates as CXL lesson-scope atoms.

## Affected docs

Docs 19, 31, 33, 38.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 19 §5 (heading, grammar and lowering), doc 31 §5.1 and OQ10, doc 38 §3.1 and OQ6, and doc 33 §5.5, re-read on
  2026-09-27. The lesson-goal vocabulary was added by this pass; no research doc lists it as a gap yet.
