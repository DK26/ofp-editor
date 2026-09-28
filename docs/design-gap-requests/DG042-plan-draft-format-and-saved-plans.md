# DG042: Dynamic authoring, static execution: the `PlanDraft` format, its checks and where saved plans live

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-28 under the owner's go-ahead of 2026-09-28 ("Either way,
> except for GPG Signing, we can do everything else"), as one of three dynamic-workflow additions discussed with the owner (DG040,
> DG041, DG042); it covers doc 63 §13 items 9 and 10. Status: **open**.
> **Decision by: technical** (design round). The owner-level choice (plans exist, after v1, run only after a save) is
> [D051](../decisions/D051-capability-ladder-freedom-by-qualification.md) item 9. Blocks: the FR8 implementation after v1; doc 63
> §8.2–§8.3 stay `proposal-only` in their details.

## Context

- **D051 item 9** (adopted 2026-09-28 under the owner's go-ahead, doc 63 §8.7 option B, OQ1–OQ3): after v1, a `planner` role behind
  an FR8 grant may **propose** a workflow as data (`PlanDraft`) built only from registered units, reached only from
  `Dispatch::NotSupported`; the definition compiler checks it; it runs only after the user saves it as their own workflow with a
  click carrying `UserIntent`, in Auto too; no "run once, don't keep"; Wilco never saves a definition. D051's Consequences: a
  `PlanDraft` adds no step kind; its `when` may test only inputs, `ask` answers and trusted code outputs; about 12 units at most;
  nested steps keep their own grants. D025 carries a note that D051 refines decision 1.
- **Doc 63 §8.2–§8.5.** Planner capsule without any `Untrusted` segment; tools `workflow.search`, `workflow.describe` and `plan.check`,
  all `AgentEffect::None`; `plan.check` runs the definition compiler in dry-run mode plus §8.3's rules; the save writes "a
  user-authored TOML definition through the ordinary loader into the user's workflow folder (never a mission or campaign folder, doc
  38 §6.1), hash-pinned, with provenance: 'drafted by [setup] on [date], saved by you'". §8.3: a plan may not contain new kinds,
  types, checks, providers or tools, "loops other than a bounded `map`", or a model step without `verify` and `on_fail`.
- **Doc 63 §13 items 9–10.** Listed gaps: the `PlanDraft` format, `plan.check`, `workflow.search`/`describe`, the entry from
  `Dispatch::NotSupported`, a `ProposeOp` form for plans with `AgentEffect::None` (agent-runtime §2: "adding a variant is a design
  review"); and where saved user workflows live and how their provenance shows (doc 38 §6.1 covers packs and first-party only).
- **Doc 38.** §2 principle 1: "Wilco has no tool that creates or edits a definition". §6.1: first-party and pack workflows only;
  hash-pinned trust (Trusted, Modified, Untrusted); never loads workflows from mission or campaign folders. §5.2: "Always run without
  the card" only for built-in and installed pack workflows. §6.3: runs pin a definition snapshot.
- **D043.** User-authored workflows, like first-party ones, may chain plugins of different publishers, with the egress card each time.
- **DG007** (one definition format) and **DG040** (a `repeat` step) are open. **DG041** (a review stage in `sample`) was decided on
  2026-09-28 under the owner's delegation ([D054](../decisions/D054-review-stage-for-creative-steps.md)); whether a plan may use it
  is still gap 4 below.

## The gap

D051 settles that plans exist and when they may run, but not their mechanics:

1. **Format.** Is a `PlanDraft` the workflow TOML schema restricted by a "plan profile" of the compiler, or its own typed structure
   converted to TOML on save?
2. **Checks and tools.** What `plan.check` adds to the compiler; the `ProposeOp` variant and the three tools' typed inputs and outputs.
3. **Saved user workflows.** Where they live, their trust state after a save, what an edit outside the editor does, whether "Always
   run without the card" may ever apply to them, and how "drafted by … saved by you" shows in the palette and the run graph.
4. **Coordination.** Whether a plan may use what DG040 and DG041 would add.

## Options

| Gap | # | Option | For | Against |
| --- | --- | --- | --- | --- |
| Format | 1A | The TOML definition schema itself, checked with a plan profile (§8.3's stricter rules) | One format (DG007); the saved file is exactly what was checked | The model writes definition syntax, not a typed proposal |
| Format | 1B | A typed `PlanDraft` (doc 63 §8.2 step 4: "not a definition and cannot run"), converted by code to TOML on save and re-checked by the ordinary loader | The model fills a typed structure; conversion is code's | Two representations to keep in step |
| Saved workflows | 3A | A per-user workflow folder read by the ordinary loader, hash-pinned with provenance; Trusted when the user saved it in the editor, Modified after an outside edit until re-approved (doc 38 §6.1's rule); never "always run without the card" | Reuses pack trust; the glass box shows who drafted and who saved | A new folder the loader must scan |
| Saved workflows | 3B | Stored inside the project sidecar | Travels with the project | Doc 38 §6.1: workflows are never loaded from mission or campaign folders |
| Coordination | 4A | A plan may use only what doc 63 §8.3 allows today; DG040's `repeat` and DG041's review join only if those requests are adopted and §8.3 is amended with them | No hidden widening | Plans lag behind authored workflows |

## Recommended resolution (proposal)

- **Format: 1B**, as doc 63 §8.2 describes (a typed proposal that is "not a definition and cannot run", saved as a user-authored TOML
  definition through the ordinary loader); the saved file is re-checked by the same loader, so DG007's one on-disk format holds.
- **Checks and tools:** doc 63 §8.2–§8.3 as written, with T-L7 to T-L9 (doc 63 §11) as the first tests; the `ProposeOp` variant goes
  through the design review agent-runtime §2 requires.
- **Saved workflows: 3A**, per doc 63 §8.2 step 7 and doc 38 §6.1.
- **Coordination: 4A**; §8.3's "no loops other than a bounded `map`" stands until DG040 is decided.

## What it would change

- Doc 63 §8.2–§8.3 and §13 items 9–10 (from proposal to rules); doc 38 §6.1 (a user-workflow row), §5.2 (no "always" for saved
  plans), §6.2 (the plan profile of the compiler); agent-runtime §2 (`ProposeOp`); `CODE-INDEX.md` when the code lands.
- Tests first (proposal): doc 63 T-L7, T-L8 and T-L9; a saved plan edited outside the editor is Modified and does not run until
  re-approved; the saved file equals the checked `PlanDraft` after conversion (round-trip test).

## Affected docs

D051; D025; D043; doc 63 (§8, §11, §13); doc 38 (§2, §5.2, §6.1–§6.3); `docs/architecture/agent-runtime.md` §2; DG007; DG040; DG041.

## Decision record

Open. The owner-level part is decided in D051 item 9 (2026-09-28, under the owner's go-ahead; the owner may overrule on return).

## Verification notes

### Filing (2026-09-28)

- Filed from the owner's dynamic-workflow additions and doc 63 §13 items 9–10, re-reading D051, D025's 2026-09-28 note, D043, doc 63
  §8 and §11, and doc 38 §2, §5.2 and §6.1–§6.3 on 2026-09-28. Written after D051 appeared the same day; this request covers only
  what D051 lists as open (doc 63's design-gap candidates).

### Owner delegation, design-gap pass (2026-09-28)

- DG041 was decided the same day ([D054](../decisions/D054-review-stage-for-creative-steps.md)), so the Context bullet on DG040 and
  DG041 now says so. Option 4A is unchanged; under it a plan may use D054's review only once doc 63 §8.3 is amended with it. This
  request stays open.
