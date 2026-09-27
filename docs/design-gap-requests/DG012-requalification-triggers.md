# DG012: Which prompt, lens or exemplar changes void a qualification

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
> **Decision by: technical** (design round). Blocks: the qualification record format (doc 21 §12.3) and the "qualified for this
> model setup" UI (doc 21 OQ3).

## Context

- **Doc 21 §12.3**: a model setup is qualified for a step after n consecutive all-pass trials plus every must-pass safety case (14
  trials for 80% at 95% confidence). The model setup is "model, version, quantisation, chat template, sampler, reasoning" (§7.2).
  Nothing says what happens when the *prompt side* changes.
- **Doc 38 §3.5**: pack version and lens id go into every decision record; §4.3 puts lens and exemplar-pack hashes in the input
  digest, so a change marks decisions stale. OQ5: "Does a lens, prompt-template or exemplar-pack change void a setup's
  qualification (doc 21 §12.3)?"
- **`prompts/design-sensibility/README.md`**, "Versioning": a major version covers changes to lens ids, loading order, routing
  table, gate definitions or the layer model; the loader records pack version and lens id per decision.
- Doc 25 §4.6: exemplar count and order per tier are fixed by offline qualification ("compile-then-freeze").

## The gap

Qualification is recorded against the model setup only. Capsule inputs that change what the model sees (lens text, prompt
template, exemplar pack, answer schema, capsule order) can change pass rates, yet no rule says whether they void a qualification,
trigger a re-check, or change nothing.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Any change voids every affected qualification | Safest | Every typo fix forces 14+ trials per step and model |
| B | Nothing on the prompt side voids a qualification | No cost | A lens or exemplar change could silently break a weak model |
| C | Qualification is keyed by (model setup, `DecisionKind`, prompt-template version, lens pack version, exemplar pack version, schema id). A **major** change voids; a **minor or patch** change marks it "requalifying": the step runs, a quick re-check (the step's must-pass cases plus a small trial batch) runs offline, and full requalification follows only if that fails | Proportionate; reuses the prompt pack's semver rules | Needs discipline in version bumps; a mislabelled patch can hide a regression |

## Recommended resolution (proposal)

Option C. For **built-in packs**, the project runs the quick re-check before every release in which a pack version changes and
publishes qualification tables per version; a failed re-check blocks the release for that step or reverts the pack. For a **user's
own setup**, the UI shows "qualified on pack vX; now vY" and offers a re-check; the step keeps its smallest safe shape until then
(doc 25 §5.1). Capsule-order changes (DG019) count as major. The qualification record stores all six keys.

## What it would change

- Doc 21 §12.3: the keyed record and the major/minor rule; OQ3's UI wording.
- Doc 38 OQ5 answered; §3.5 unchanged (it already records pack version and lens id).
- `prompts/design-sensibility/README.md` "Versioning": one line linking version bumps to requalification.
- Doc 25 §4.6 and §11: the quick re-check as an instrument mode.

## Affected docs

Docs 21, 25, 38; `prompts/design-sensibility/README.md`.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 21 §7.2 and §12.3; doc 38 §3.5, §4.3 and OQ5; doc 25 §4.6; the prompt pack README's usage and versioning
  sections, re-read on 2026-09-27.
