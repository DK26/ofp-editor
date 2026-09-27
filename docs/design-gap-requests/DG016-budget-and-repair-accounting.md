# DG016: How turns, repairs, reservations and retries are counted

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
> **Decision by: technical** (design round). Blocks: the ledger, the plan card's estimate and cap, the key-order budget
> reservation (doc 38 §4.5) and the instruments' cost metrics.

## Context

- **Doc 38 §3.4**: definition numbers are ceilings; proposed [I]: `[budget].turns` is a **whole-run** ceiling that replaces only
  doc 21 §7.1's "model turns per request" row for the run; doc 21 §7.1 needs a matching note (W0). OQ7 asks whether long runs need
  their own effort table.
- **Doc 38 §4.3 item 4**: an intent without a settlement becomes `Interrupted`; its retry is a new, budget-counted turn.
  **§4.5**: each item reserves its worst case, "K candidates plus R repairs per decision, doc 21 §7.1", in key order. **§4.6**:
  "Transport retries are bounded, journaled apart from repairs and never switch models." **§7** "Done requested": a red completion
  gate "becomes one more repair turn with a code-written finding within budget".
- **Doc 21 §6.2 rule 6**: "a repair is a new, counted turn"; rule 2: "Repaired results are logged apart from first-pass ones";
  §12.1: repaired successes reported apart from first-pass ones.
- **Doc 25 §7.2**: "A repaired answer is recorded as repaired; metrics never count it as a first-pass success." §7.3 step 1: drop
  every candidate a verifier rejects "(after its repairs)", so repairs apply per candidate.
- **Doc 40 §6**: the plan card shows "the worst case the budget reserves (K candidates plus R repairs per decision, doc 38 §4.5)";
  caps per run, session and month; **§7**: "cost per *admitted* decision (repairs, escalations and defaults included)".

## The gap

- "K candidates plus R repairs" reads as **K + R** calls, but repairs run per candidate, so the worst case is **K × (1 + R)**.
- Whether each repair turn counts against `[budget].turns`, and whether the Pick `X` re-menu and the gate's extra repair turn are
  reserved, is unstated.
- Transport retries are "journaled apart", but whether they count as turns or money is not said.
- The whole-run semantics of `[budget].turns` are a proposal in doc 38 only.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Count only first-pass calls as turns; repairs are free | Simple estimates | Hides real cost; contradicts doc 21 rule 6 |
| B | Every model request that reaches a provider counts one turn; money is counted from reported usage for every request, including transport retries | Matches doc 21 rule 6 and doc 40's "cost per admitted decision"; caps are honest | Estimates must model repairs, re-menus and gate turns |

## Recommended resolution (proposal)

Option B, with one accounting rule used by the ledger, the plan card and the instruments:

- **Turn:** one provider request for a decision attempt: first pass, repair, `X` re-menu sample, gate repair, or a same-model effort
  re-run if DG022 is adopted. Each counts 1 against `[budget].turns`, which is a whole-run ceiling (doc 38 §3.4 proposal adopted;
  doc 21 §7.1 gets the note).
- **Transport retry:** re-sending a request that produced no complete reply (connection error, 5xx, timeout before the first token).
  Not a turn; journaled as its own record type; capped (placeholder: 2 per turn); any usage the provider reports still enters the
  money ledger and money caps. A retry never switches models (doc 38 §4.6).
- **Reservation per decision** (doc 38 §4.5): K × (1 + R); plus, for a Pick step with the `X` escape, one more round of K × (1 + R)
  for the single re-menu; plus 1 per completion gate for its repair turn. Adaptive K (DG021) and early stops release unused
  reservation in key order.
- **Plan card:** the expected cost (calibrated, doc 40 §6) and the reserved worst case, which is the default run cap.
- **Metrics:** first-pass admits, repaired admits and defaults reported separately (doc 21 §12.1, doc 25 §7.2); cost per admitted
  decision includes repairs, re-menus, gate repairs, effort re-runs and billed transport retries.

## What it would change

- Doc 38 §3.4 (proposal → rule), §4.5 (the formula), §4.6 (retry record), §7 (gate turn reserved); OQ7 narrowed to campaign-scale
  defaults.
- Doc 21 §6.2 rule 6 and §7.1: the whole-run note and the turn definition.
- Doc 25 §7.2–§7.3: repairs per candidate stated explicitly.
- Doc 40 §6: "K × (1 + R)" in the reservation sentence; §7: the metric definition.

## Affected docs

Docs 21, 25, 38, 40; DG021, DG022.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 38 §3.4, §4.3, §4.5, §4.6, §7 and OQ7; doc 21 §6.2, §7.1 and §12.1; doc 25 §7.2–§7.3; doc 40 §6 and §7, re-read on
  2026-09-27.
