# DG026: Candidate diversity when `temperature` is rejected

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass (doc 40 gap G8).
> Status: **open**. **Decision by: technical**. Blocks: the `sample` key semantics in doc 38 §3.3 and the candidate generator.

## Context

- **Doc 21 §7.1** ("Candidates K per creative slot") and **doc 25 §7.3** assume K sampled candidates differ. Doc 25 §7.3: Pick steps
  vote across samples that saw differently permuted menus; creative steps order candidates by deterministic signals and show the
  top 2–3 in interactive modes.
- **Doc 38 §3.3** `sample`: `{ candidates, select }` with `vote`, `rank` or `user`; §4.5 seeds per item.
- **Doc 40 §2.5** [V, 2026-09-27]: `temperature`, `top_p` and `top_k` return 400 on Opus 5.5, Opus 5, Opus 4.8/4.7, Sonnet 5 and
  Fable 5/5.1 (allowed on Haiku 4.5, Sonnet 4.6, Opus 4.6). **R7**: sample diversity comes from permutations and variant notes below
  BP3. **OQ3**: does asking for K candidates in one call (array schema) reduce diversity compared with K separate samples?
- Doc 21 §13.1: variety comes from code seeds and archetype menus because models converge on similar ideas.

## The gap

On current Claude models, K identical capsules can return near-identical candidates, because sampling parameters are refused.
Picks still differ by menu permutation; creative Fills and text slots have no specified source of diversity.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Rely on the provider's default sampling | No work | Near-duplicates on providers that fix sampling; K wasted |
| B | Code-authored diversity below the last breakpoint: menu permutation (Pick); a seeded **variant note** per candidate drawn from a code-owned list of angles (for example opening device, tone chip, focal character) for creative steps | Works on every provider; seeds are journaled, so reproducible; fits doc 21 §13.1 | Angle lists must be written per DecisionKind; notes cost a few tokens |
| C | K candidates in one call with an array schema | One call instead of K | Unmeasured diversity loss (doc 40 OQ3); `minItems` must be enforced in code; one failure fails all |

## Recommended resolution (proposal)

Option B as the default on every provider, with sampler settings used additionally where the provider accepts them. Variant notes
come from a code-owned angle list per DecisionKind, chosen by the item seed, and never from earlier candidates' text, so the K calls
stay parallel and warm-first fan-out still works (DG027). Option C is measured in E12 (doc 40 §7) before any use. In doc 38 §3.3,
diversity is runtime-owned (authors do not choose it), like capsule order.

## What it would change

- Doc 21 §7.1 and doc 25 §7.3: "candidates differ by permutation or seeded variant note; sampler settings only where accepted".
- Doc 38 §3.3 `sample`: note on runtime-owned diversity; §4.5 seed use.
- Doc 40 R7 and OQ3: rule; G8 closed.

## Affected docs

Docs 21, 25, 38, 40; DG021, DG027.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 21 §7.1 and §13.1, doc 25 §7.3, doc 38 §3.3 and §4.5, and doc 40 §2.5, R7, OQ3 and §4.3 G8, re-read on 2026-09-27.
  Provider facts are doc 40's and were not re-fetched here.
