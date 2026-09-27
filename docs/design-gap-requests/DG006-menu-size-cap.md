# DG006: Weak-model menu cap: 5 or 7 options

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
> **Decision by: technical** (bench E4 in doc 25 §11.1). Blocks: nothing hard (7 is the working default); the losing docs stay
> inconsistent until decided.

## Context

- **≤ 7 options plus escapes**: doc 25 §5.1 (Pick shape) and §6.2 step 5 ("Cap at k ≤ 7 and shuffle per sample"); doc 21 §3.1–§3.2;
  doc 38 §3.2 (`pick` step kind); doc 31 §9 (weak tier); doc 35 rc33; doc 37 §9; doc 42 MG5, §2.4 and MAT6 ("every menu ≤ 7 plus
  escapes").
- **≤ 5**: doc 26 TL;DR ("a ranked pick of at most 5 options"), §9.5 S5 row ("`Pick(u8)` archetype, `Pick(u8)` site | ≤ 5 each");
  doc 29 §6.2 (S3 "Pick ≤ 5 each", S5 "Pick ≤ 5").
- Doc 26 OQ6: "Are 3 or 5 options the right cap for the target local tiers (doc 14)? Doc 25 §5.1 allows ≤ 7; one number must win.
  This needs a small bench of pick-from-menu accuracy per step." Doc 25 OQ1: "is k ≤ 7 right for 3–4B models …? (E4)".
- Evidence that the cap already costs steps: 15 of 27 Side × Class unit lists exceed 7 (median 8, max 60), so unit menus are split
  into facets (doc 25 §6.2; doc 35 §2.2; `docs/research/data/catalog-sizes.csv`).

## The gap

Two numbers are in use for the same limit, and no doc says whether the cap is global or per decision kind and model tier.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | One global cap of 7 | Majority of docs; the menu algorithm, facets and MAT6 already assume it | May be too many for 3–4B models (unmeasured) |
| B | One global cap of 5 | Possibly easier for the weakest models | More facet steps (each a model call); more lists split; unmeasured too |
| C | Hard global maximum 7; each (DecisionKind, model setup) may qualify for a smaller cap (3–7), recorded like shape qualification (doc 25 §5.1, doc 21 §12.3) | Lets data pick per tier without changing the code path; code already computes menus | One more qualified parameter |

## Recommended resolution (proposal)

Option C. The hard maximum is 7 options plus the `X none_fit` and `Q ask_user` escapes (doc 25 §6.2); the menu builder takes a cap
per decision from the model setup's qualification record, default 7 until bench E4 says otherwise for a tier. Docs 26 and 29
replace "≤ 5" with "≤ the menu cap (default 7; doc 25 §5.1)". E4 reports pick accuracy at k = 3, 5 and 7 per tier, with permutation
debiasing on and off, and the added facet steps counted, as doc 25 OQ1 asks.

## What it would change

- Doc 26 TL;DR, §9.5 S5 row and OQ6 (answered by pointer); doc 29 §6.2 S3 and S5 rows.
- Doc 25 §5.1 and §6.2: "cap per qualified setup, maximum 7"; OQ1 points here; E4 gains the k sweep.
- Doc 21 §3.2 and doc 38 §3.2: unchanged wording ("≤ 7") stays correct as the maximum.

## Affected docs

Docs 21, 25, 26, 29, 38, 42 (MAT6 unchanged).

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 26 TL;DR, §9.5 and OQ6; doc 29 §6.2; doc 25 §5.1, §6.2 and OQ1; doc 21 §3.1–§3.2; doc 38 §3.2; doc 42 TL;DR, §2.4
  and MAT6; doc 35 rc33, re-read on 2026-09-27.
- *Docs 39, 41 and 43 step (2026-09-27).* The three final docs use ≤ 7 as well: doc 39 §7 step 2 and §8 (intent cards), doc 41 §7
  step 1 (mood family and preset), doc 43 §2.9 (`VariationAxis` options 2..=7) and §7 (variation recipes). Doc 39 §8, doc 41 §7
  and doc 43 §7 now point here; option C's maximum of 7 keeps all of them correct, and a smaller qualified cap would apply to them
  like any other Pick.
