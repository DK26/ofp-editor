# DG021: K candidates cost money on cloud setups: adaptive K

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass (doc 40 gap G3).
> Status: **open**. **Decision by: technical**. Blocks: the `sample` policy in doc 38 §3.3; doc 40 R7 stays `proposal-only`.

## Context

- **Doc 25 §5.2**: K per creative decision 1 / 2 / 3–5 / 5–8 and K for Pick 1 / 3 / 3–5 / 5 by effort; "Weak local models benefit
  *more* from larger K (§2.5), and K costs only local time, so 'Thorough on a 4B model' is a sensible preset."
- **Doc 21 §7.1** repeats the K rows.
- **Doc 40 R7**: "K is money on cloud setups." Pick K becomes a maximum: stop when two samples from differently permuted menus agree
  (and, where option probabilities exist, the margin is not low; threshold [U]); correctness-only Fills stop at the first admitted
  candidate; creative K stays fixed only where the user sees the alternatives; Economy and batch modes use K = 1; the plan card prices
  K. Doc 40 OQ3 leaves the stopping threshold and one-call-K-candidates open.

## The gap

Doc 25's statement is true only for local models. On cloud setups every candidate is a billed call, and the effort table fixes K
regardless of whether extra samples can change the outcome.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Keep fixed K per effort | Simple; predictable | Pays for samples that cannot change a decided vote or a correctness-only Fill |
| B | Adaptive K (doc 40 R7) on every setup | Saves cost on cloud and time locally | Early stopping may reduce position debiasing on Picks; threshold unmeasured |
| C | Adaptive K on cloud, fixed K locally | Keeps doc 25's local advice | Two behaviours to test |

## Recommended resolution (proposal)

Option B, with the effort table's K read as a **maximum**. Pick: stop at the first agreement of two samples from differently
permuted menus (plus a probability-margin check where the engine exposes it); correctness-only Fills: stop at the first admitted
candidate; creative steps: fixed K only in interactive modes that show the alternatives; Economy and batch: K = 1. The plan card
shows expected and maximum K per stage with its cost. The stopping threshold is set by E12 (doc 40 §7) and reported per
(DecisionKind, model setup). Unused reservation is released in key order (DG016).

## What it would change

- Doc 25 §5.2: "K costs only local time" → "K costs local time and, on cloud setups, money; K is a maximum (adaptive)"; the K rows
  become maxima.
- Doc 21 §7.1: K rows labelled maxima.
- Doc 38 §3.3 `sample`: `candidates` is a maximum; the stop rule by shape.
- Doc 40 R7 and OQ3: rule once E12 reports.

## Affected docs

Docs 21, 25, 38, 40; DG016, DG026.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 25 §5.2 and §7.3, doc 21 §7.1, doc 38 §3.3, and doc 40 R7, §4.3 G3, §7 and OQ3, re-read on 2026-09-27.
