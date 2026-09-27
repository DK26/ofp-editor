# DG007: One on-disk format for workflows, recipes, modules and rules

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
> **Decision by: technical** (design round). Blocks: all workflow runtime code (doc 38 phase W0: "no runtime code before the format
> decision"); the `ofp-workflow` loader; module and rule-set definitions (doc 31 §4.2, §5).

## Context

- **Doc 38 §3.1, §6.1, OQ1**: one TOML file per workflow (`format = "plotroom-workflow/1"`, ≤ 64 KiB, unknown keys refused).
  Built-ins "are written in the same TOML and compiled in by a build step that runs the same loader and fails the build on any error,
  so there is one format". OQ1 also proposes that doc 17 §10's recipes become exemplar libraries rather than workflows.
- **Doc 21 §6.1**: "Built-in workflows are Rust constants; T0 content packs may ship more in the same schema (TOML)". Doc 21 OQ7:
  should this schema, T0 plugin workflows (doc 22 §4.2) and the recipe library (doc 17 §10) be one format?
- **Doc 22 §4.2 and OQ9**: T0 workflow steps (`uses = "radio-voice/synthesize_lines"`, `requires = [...]`); OQ9 asks to reconcile
  them with doc 21's format and doc 16's Selector seam.
- **Doc 34 mo22** (adopted): first-party content ships as ordinary T0 packs with the same manifest, loader and validator as
  community packs, readable on disk, listed as built-in and disable-able (except the overlays Wilco's menus need).
- **Doc 17 §10**: a recipe library of verified accepted outputs, to be designed "together with this project's agent doctrine … so
  recipes, workflows and evaluation share one vocabulary".
- **Doc 31 OQ8**: should compositions (doc 17 §6), module definitions and rule sets share one on-disk format and schema language,
  and is it TOML?
- Knowledge prose is a separate case: Standing Orders entries and lessons are Markdown with YAML front matter (doc 33 §3.3, §5.5),
  because the concept registry is an Agent Skills skill.

## The gap

Three docs describe how built-in definitions exist (Rust constants, compiled-in TOML, on-disk packs), and three kinds of definition
(workflows, modules and rule sets, compositions) have no agreed format family. Recipes are both "workflows" (doc 21 OQ7) and
"exemplars" (doc 38 OQ1).

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Built-ins as Rust constants; packs as TOML (doc 21 §6.1) | Type-checked by rustc | Two formats; pack authors cannot read first-party examples; conflicts with mo22 |
| B | One TOML language for all definitions; built-ins compiled in after the build step validates them (doc 38 §6.1) | One loader, one validator, one set of refusals and fixtures | Built-ins are not visible on disk |
| C | B, and built-ins also ship as on-disk built-in packs (mo22) | Readable examples; disable-able; community packs use the same path | Built-in files could be edited on disk; needs a hash check against the compiled copy |
| D | A different language (RON, JSON, KDL) | RON maps to Rust types | TOML is already chosen by docs 22, 38, 42 and the manifests |

## Recommended resolution (proposal)

Option C:

- **One definition language:** UTF-8 TOML with `format = "plotroom-<kind>/<major>"` as the first key, unknown keys refused, size
  caps per kind, and one loader and validator family (pure parsers per `AGENTS.md`). Kinds: `workflow`, `module` (mission and
  campaign modules, see DG004), `rule-set`, `composition`, `preset`. Templates stay separate minijinja text files referenced by
  path (doc 22 §2.1).
- **Built-ins** are authored in the same TOML, validated by the build step (doc 38 §6.1) and also installed as built-in packs
  (mo22). The loader verifies built-in files against the compiled-in hash and falls back to the compiled copy if they differ.
- **Rust registers vocabularies, not definitions:** code steps, types, checks, gates, providers, roles and lenses (doc 38 §6.1).
  Doc 21 §6.1's "Rust constants" becomes "Rust-registered vocabularies; definitions in TOML".
- **Recipes are exemplar libraries** (doc 38 OQ1): verified accepted outputs keyed by `DecisionKind`, never executable workflows.
- **Knowledge prose stays Markdown with YAML front matter** (Standing Orders entries, lessons, skills); "one format" covers
  executable and declarative definitions, not prose.

## What it would change

- Doc 21 §6.1 and OQ7; doc 22 §4.2 and OQ9; doc 31 OQ8 and §4.2 (module definitions in TOML); doc 17 §10 (recipes = exemplars);
  doc 38 OQ1 and W0 (answered); doc 34 mo22 cross-reference.
- W1 can start: `ofp-workflow` and a shared definition-loader crate.

## Affected docs

Docs 17, 21, 22, 31, 34, 38; later CODE-INDEX.md.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 38 §3.1, §6.1, §10 (W0) and OQ1; doc 21 §6.1 and OQ7; doc 22 §4.2 and OQ9; doc 34 mo22; doc 17 §10; doc 31 OQ8;
  doc 33 §3.3 and §5.5, re-read on 2026-09-27.
