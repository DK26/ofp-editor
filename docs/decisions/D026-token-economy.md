# D026: Saving users' API costs is a usability requirement

> **Status:** accepted (requirement, owner); rules baseline (doc 40) · **Decided by:** owner and research · **Decided:** 2026-09-27
> **Recorded:** 2026-09-27 · **Scope:** every model call Plotroom makes. **Related:** D021, D022, D023, D024, D025.
> **Open parts:** DG019 (capsule order), DG020 (effort table), DG021 (adaptive K), DG022 (same-model escalation), DG023 (fixed tool set
> per mode), DG024 (fixed cloud schemas), DG025 (cloud budget and cache minimums), DG026 (diversity without temperature), DG027
> (warm-first fan-out).

## Context

The owner: "In order to make it truly usable, we will have to do our best to save API costs for our users." A bring-your-own-key
co-pilot nobody can afford is not usable. Doc 40's cost model finds that typed capsules are already 3–13 times cheaper than a naive chat
agent for interactive work, but a whole campaign at today's Standard budgets can cost more than a naive agent; hidden thinking and
candidate counts dominate, not context (doc 40 TL;DR; `docs/research/data/cost-model.csv`).

## Decision

1. Cost is designed in, measured and shown, like correctness. The rules are doc 40 R1–R17; the load-bearing ones:
   - **Prices are data** (R1): a dated `[[price]]` table in `models.toml` with `as_of` and source; a "prices may be out of date" chip
     after 60 days; no price in code; the editor never fetches pricing pages.
   - **A cache-stable capsule** (R2–R5): frozen stage prefix, breakpoint, request, digest, breakpoint, permuted menu; nothing volatile
     above a breakpoint; one model, effort, schema and tool set per (stage, decision kind); Picks answer with a letter.
   - **Effort floors per step shape, one visible escalation on the same model** when a validator rejects (R6; DG020, DG022).
   - **K is money on cloud keys** (R7): stop sampling at decisive agreement; fixed K only where the user sees the alternatives.
   - **A cache policy per provider with wire tests** (R10); know each model's cache minimum and TTL (R11).
   - **Economy mode** for bulk text through batch APIs, always an explicit user choice with stated latency (R12).
   - **Exact memoisation from the journal** (R13); **local first for Pick and Fill** when a qualified local model exists (R14).
   - **No premium modifiers by default** (R15).
2. **Visible cost**: the plan card shows an estimate with the price date; the run panel shows a live meter and cache savings; per-run,
   session and monthly caps end in a resumable `BudgetLimited` state; the no-AI path is always offered at no cost.
3. **We will not** use semantic caching, token-dropping prompt compression, model-written summaries of facts, learned routers, a paid
   judge by default, or silent model switching (doc 40 §8).

## Alternatives considered

- A plain chat agent with provider automatic caching: on cost alone, the fully optimised harness only just beats it on some models,
  and today's Standard budgets cost more; the typed harness is justified by validity and editability, and the rules above keep it from
  costing more (doc 40 TL;DR).
- Hide costs and let users watch their provider dashboard: violates the owner's usability requirement.

## Consequences

- Cost per admitted decision is measured from provider-reported usage in a per-attempt ledger; CI replays recorded runs and fails on
  token-budget or prefix-stability regressions (doc 40 §7).
- A new instrument sweeps effort and K per workflow and preset on synthetic fixtures, reporting pass^k and cost per admitted decision
  (doc 40 §7; to be added to doc 25 §11.1).
- Doc 14 §7's `models.toml` gains the price table when folded.

## Sources

Doc 40 (TL;DR, §1, §4–§8); `docs/research/data/cost-model.csv`; `tools/cost-model/cost_model.py`; doc 12 §5; doc 14 §7; doc 21 §7;
doc 25 §5, §11; doc 38 §4.

## Notes

- 2026-09-27 (consistency review): the "one visible escalation on the same model" in decision item 1 restates doc 40 R6 as proposed.
  Whether it is allowed at all is DG022 (listed under Open parts, and in D024); this record does not decide it (decisions README,
  lifecycle item 2). Until DG022 is decided, the architecture offers a stronger model only as a visible button with its cost.

## Amendment notes

### 2026-09-28: D054 and D055 on the plan card (pointers)

A note under lifecycle item 5; both records were decided under the owner's delegation, and the owner may overrule them on return.
[D054](D054-review-stage-for-creative-steps.md)'s review stage is off by default and runs only when the user binds a reviewer and
picks Thorough or Max, with its calls and cost on the plan card, so decision 2's cost preview includes it and decision 3's "no paid
judge by default" holds. [D055](D055-visible-second-stage-when-unsure.md)'s bound second stage is priced on the plan card too; its
margin is computed by code from the first stage's own scores and calibrated (doc 53 §4.2), not a learned router (decision 3; doc 40
§8), and its moves are recorded and shown, so none is a silent switch. The header is unchanged; nothing above changed.
