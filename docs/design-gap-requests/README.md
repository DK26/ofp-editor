# Design-gap requests

A **design-gap request** (DG) records a place where Plotroom's own design is missing a detail, contradicts itself, or has no
workable path. `AGENTS.md` ("Design Authority") forbids inventing behaviour silently in that case: the gap is filed here, and
any local work that depends on it is marked `implementation placeholder`, `proposal-only` or `blocked on <decision>` until the
request is decided.

Design-gap requests are about **this project's design**. Gaps in the **game engine** are engine requests. They belong in the
engine-requests register under `docs/upstream/` (`AGENTS.md`, "Maximum Within the Engine; Gaps Become Engine Requests"). A DG
may point to engine requests, for example when a doc routed engine defects to the wrong place (DG034).

## Lifecycle

| State | Meaning | What changes |
| --- | --- | --- |
| `open` | Filed. Context, options and a recommendation marked *proposal* are recorded. Nothing is decided | Dependent work stays `proposal-only` or `blocked on DGnnn` |
| `decided` | The decider chose an option (or a variant of one). The file records the date, who decided, the choice and the reason | Affected docs are not yet updated |
| `folded` | Every affected doc now states the decision, points to the DG and carries a dated verification note | The DG file stays as the record; later readers follow its pointers |
| `withdrawn` / `superseded by DGnnn` | The gap turned out not to exist, or another DG absorbed it | Pointer to the reason or the successor |

- **Owner decisions** cover product scope, user-facing names, security and network boundaries, licensing and legal matters, and
  public outreach. Only the owner moves such a request to `decided`.
- **Technical decisions** are made in the design round from the evidence each request names (tests, benchmarks, probes) and are
  recorded in the same file.
- Never delete a DG file and never reuse a number. A decision that is later reversed gets a new DG that supersedes the old one.
- A recommendation in an `open` request is a proposal, not a decision. Docs may cite it only as "proposed in DGnnn".

## Naming

`DGnnn-short-slug.md`: `DG`, three digits, a hyphen, and a lowercase kebab-case slug of at most six words. Numbers are assigned
in filing order by this index, which is the source of truth. DG001 was filed before this index existed and keeps its file name
(`DG-preview-non-aborting-launch.md`) until the change that renames it also updates the references to it in doc 08 (§4.4 and its
verification notes).

## Template

```markdown
# DGnnn: <title>

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed <date> in <pass or change>. Status: **open**.
> **Decision by: owner | technical** (<who or which evidence>). Blocks: <what stays proposal-only or blocked until decided>.

## Context
<Source docs and sections, with a one-line summary of what each says.>

## The gap
<The contradiction or the missing "how", stated so a reader without the source docs understands it.>

## Options
| # | Option | For | Against |
| --- | --- | --- | --- |

## Recommended resolution (proposal)
<The option this request recommends and why. Always marked proposal until decided.>

## What it would change
<The concrete edits per affected doc, code area or test once decided.>

## Affected docs
<List.>

## Decision record
<Empty while open. Date, decider, chosen option, reason.>

## Verification notes

### <pass name> (<date>)
- <What was read to file this, and what was not re-checked.>
```

## Index

| ID | Title | Decision by | Status | Main sources |
| --- | --- | --- | --- | --- |
| [DG001](DG-preview-non-aborting-launch.md) | A non-aborting Preview launch for the debug console | technical + probe | open | 31 §7.4, 08 §4.4 |
| [DG002](DG002-product-name-and-subtitle.md) | Where the product name and its descriptive subtitle may appear | **owner** | open | 02 §9, §11 |
| [DG003](DG003-attribute-vocabulary.md) | One canonical vocabulary for attributes and presets | technical | open | 37 §10 (g), 31 §3, mission-primer idioms |
| [DG004](DG004-module-vocabulary.md) | What "module" means: mission, persistence and strategic modules | technical | open | 31 §4.1, OQ9; 26 §5.2; 29 §3.1 |
| [DG005](DG005-code-registry.md) | One registry for lint, pattern and other codes | technical | open | 34, 36, 42 headers; 21; 29; 33; 37; 40 |
| [DG006](DG006-menu-size-cap.md) | Weak-model menu cap: 5 or 7 options | technical (bench E4) | open | 25 §5.1, OQ1; 26 OQ6; 29 §6.2 |
| [DG007](DG007-one-definition-format.md) | One on-disk format for workflows, recipes, modules and rules | technical | open | 38 OQ1, §6.1; 21 §6.1, OQ7; 22 OQ9; 31 OQ8; 17 §10; 34 mo22 |
| [DG008](DG008-condition-language.md) | One condition language for campaign, mission and workflow scopes | technical | open | 19 §5; 31 OQ10; 38 §3.1, OQ6 |
| [DG009](DG009-rung-4-engine-facts-owner.md) | Which doc owns the cinematic engine facts: 31 §6 or 32 §2 | technical | open | 31 verification "Open" (1); 32 reviews |
| [DG010](DG010-resume-and-replay-wording.md) | Resume reuses settled entries; one meaning for "replay" | technical | open | 38 §4.3, OQ3; 21 §6.2, §8.2; 25 §4.2 |
| [DG011](DG011-admission-wrapper-name.md) | `Admitted<T>` or `Checked<T>`, and what a changed read does | technical | open | 21 §1.2, OQ1; 25 §4.2; 38 OQ4 |
| [DG012](DG012-requalification-triggers.md) | Which prompt, lens or exemplar changes void a qualification | technical | open | 38 OQ5, §3.5; 21 §12.3 |
| [DG013](DG013-user-gates-effort-or-autonomy.md) | User gates: set by effort or by autonomy | **owner** | decided 2026-09-27 | 38 OQ12, §5.4, §8.1; 25 §5.2; 21 §7; 14 §8 |
| [DG014](DG014-cross-plugin-chaining.md) | May one plugin's output feed another plugin's egress in a workflow | **owner** | open | 38 OQ13; 22 §3.1–§3.2 |
| [DG015](DG015-pick-answer-schema.md) | `DecisionSpec.schema` must not be declarable for Pick | technical | open | 38 §3.3, §4.7; 40 R4–R5, §4.1 |
| [DG016](DG016-budget-and-repair-accounting.md) | How turns, repairs, reservations and retries are counted | technical | open | 38 §3.4, §4.3, §4.5–§4.6, §7; 40 §6–§7; 25 §7.2; 21 §6.2 |
| [DG017](DG017-journal-storage-and-retention.md) | Journal storage, atomic save, retention and export stripping | technical | open | 38 §4.2, OQ2, OQ10; 25 OQ10 |
| [DG018](DG018-third-party-port-records.md) | Where records of ported permissive-licence code live | technical | open | 38 §1.2, OQ9; 02 §10.4 |
| [DG019](DG019-static-first-capsule-order.md) | Capsule order: static first, or exemplars next to the question | technical (measure) | open | 40 G1, §4.1, R2–R3; 25 §4.4, §4.6; 21 §8.1; 38 §3.3 |
| [DG020](DG020-reasoning-effort-table.md) | One measured reasoning-effort table per shape and provider | technical (measure) | open | 40 G2, R6; 21 §7.1; 25 §4.4; 14 §8; 12 §3.3 |
| [DG021](DG021-adaptive-candidates-k.md) | K candidates cost money on cloud setups: adaptive K | technical | open | 40 G3, R7; 25 §5.2 |
| [DG022](DG022-same-model-effort-escalation.md) | Same-model effort re-run versus "never upward" | technical (doctrine wording) | open | 40 G4, R6; 25 §3, §10.2; 21 §1.4, §6.2; 12 §5.7 |
| [DG023](DG023-fixed-tool-set-per-mode.md) | A fixed tool set per mode instead of per-turn `active_tools` | technical | open | 40 G5, R5; 12 §3.1; 21 §6.2 |
| [DG024](DG024-fixed-cloud-schemas.md) | No per-request dynamic enums in cloud schemas | technical | open | 40 G6, R5; 30 §4.5 |
| [DG025](DG025-cloud-prompt-budget-and-cache-minimum.md) | The cloud (T3) capsule budget and provider cache minimums | technical | open | 40 G7, R11, §2.3; 25 §4.4 |
| [DG026](DG026-candidate-diversity-without-temperature.md) | Candidate diversity when `temperature` is rejected | technical | open | 40 G8, R7; 21 §7.1; 25 §7.3; 38 §3.3 |
| [DG027](DG027-warm-first-fan-out.md) | Warm-first fan-out and llama.cpp slots | technical | open | 40 G9, R9, R14; 38 §4.5 |
| [DG028](DG028-t2-read-only-catalog-feeds.md) | Read-only catalog feeds and registry traffic | **owner** | decided 2026-09-27 | 42 §3.4, §5.1, OQ3; 22 §2.3, OQ4; AGENTS.md |
| [DG029](DG029-mod-channel-outreach.md) | Outreach to the mod-channel maintainers | **owner** | open | 42 OQ1–OQ2, §4.2, §8.1 |
| [DG030](DG030-mod-distribution-open-decisions.md) | Open decisions on mod install hand-off, directory freshness, CC-BY-SA and the registry operator | **owner** | open | 42 review "Still open", OQ8–OQ9; 34 OQ6 |
| [DG031](DG031-concept-id-scheme.md) | Flat or dotted ids for Standing Orders entries and cards | technical | open | 33 OQ11, finding 10, §3.1–§3.4; 30 §4.6; 38 §3.5 |
| [DG032](DG032-reference-tool-family.md) | One knowledge store and one tool family | technical | open | 30 OQ7, §4.4; 33 §6.1, OQ10; 21 §10.2; 23 |
| [DG033](DG033-standing-orders-phase-0.md) | Standing Orders phase-0 decisions (schema, demos, Easy/Advanced, relabels) | technical; **owner** for items 3–4 | items 3–4 decided 2026-09-27; 1–2 open | 33 §9 phase 0, OQ2–OQ3 |
| [DG034](DG034-camera-engine-defects-routing.md) | Camera and effects engine defects: route to the engine-requests register | technical | open | 32 §2.9, §3.7; 31 §10; AGENTS.md |

## Candidates noticed but not filed in this pass

- **Cutscene-section staging** (doc 32 §7 phase 0; doc 08 verification notes): the staged-Intro refinement is listed as a design
  gap, but no request exists yet.
- **Workflow definitions replace doc 25's `Stage` enum** (doc 38 §4.7 and W0): needs a doc 25 note and a request.
- **Generated file names built from labels** (doc 31 verification notes, "Open" item 7): rename-follows-references or freeze at
  first export.
- **Doc 39 §1.2 sibling changes**: doc 39 files them "through `docs/design-gap-requests/`"; file them once doc 39 is final.
- **A trimmed T1 core prompt** (`prompts/design-sensibility/README.md`, "Token budget"): needs an owner decision here if and when
  such a variant is proposed.
- Doc 37 §10's candidates other than (g) are factual corrections for the cross-doc correction step (docs 03 and 31 already carry
  (b), (c) and (f)). They are filed here only if a correction turns out to need a decision.

## Verification notes

### Consolidation pass (2026-09-27)

- Created this folder index, the template and DG002–DG034 from the design-gap list of the consolidation pass. Each request cites
  the sections it was built from; those sections were re-read on 2026-09-27. Docs 39, 41 and 43 were still being written and were
  only read, never edited. No research doc was edited by this step.
- DG001 was filed earlier in the same pass under an unnumbered name; this index assigns it DG001.
- `docs/upstream/` (the engine-requests register named in `AGENTS.md`) does not exist yet; DG034 records what goes there.
