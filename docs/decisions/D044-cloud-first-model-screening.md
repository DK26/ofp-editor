# D044: Cloud-first screening of local model candidates

> **Status:** accepted (the rule) · **Decided by:** owner (direction of 2026-09-27) · **Decided:** 2026-09-27 · **Recorded:** 2026-09-28
> **Scope:** the order in which candidate models are evaluated before a local trial. Qualification and badges are unchanged (D022
> item 4, D037). **Related:** D008, D021, D022, D023, D026, D037.
> **Open parts:** the protocol below (proposal, doc 50 §5); how the rule applies to doc 49's rows already under way; OWQ-26 (models and
> services whose policies ban military uses; answered 2026-09-28 → D047); OWQ-27 (spend and schedule, including when the cloud backend
> of `tools/local-qual` lands; answered 2026-09-28 → the amendment note).

## Context

- Doc 47 §6 plans local runs first, and doc 48 defers its cloud round 1 until doc 49's local results are in (D021's amendment note).
- A local trial of an offload-class model costs a 12–22 GB download (about 84 GB for the five candidates), `--n-cpu-moe` tuning and
  4–31 minutes of prompt processing per run; PrismML's Bonsai fork needs 1.5–2.5 hours per arm (doc 50 §5.8).
- A cloud copy of the same weights runs a 256-call battery in minutes for cents, but at another precision and on another serving stack,
  so it screens and cannot qualify (doc 48 §4; doc 50 §5.5).

## Decision

**The owner's rule (accepted):**

In the owner's words (lightly edited): "Any model that could fit and run locally on our PC should first be tested in the cloud. Only
if it yields promising results in benchmarks do we try it locally as well. The idea is to save time." Restated:

1. Any model that could fit and run locally on the reference PC is **first tested in the cloud**, on a hosted copy of the same weights
   ("the same weights" is our reading of "tested in the cloud").
2. **Only if its cloud results are promising** is it tried locally as well.
3. The aim is to save time.

**The protocol (proposal, doc 50 §5; the owner did not decide these parts):**

- **P1 Battery S:** 256 calls (`pick-hard` with and without cards at k = 3, Fill at k = 3, Explain with cards and Text without card at
  k = 2), with the local records' seeds so that every call pairs item by item with a later local run.
- **P2 Endpoints:** paid, pinned, ZDR, strict-schema hosts, two per offload-class model; free tiers only for smoke tests, no-schema
  arms and round 0; only the repository's synthetic suites are ever sent.
- **P3 Promotion rule:** must-pass checks (schema conformance, no reasoning leak, planted escapes, no false escapes); promote when within
  one menu or two Fill calls of the default's local bar, or clearly better on a specialist axis; drop only on a clear miss confirmed on a
  second host; otherwise grey (doc 50 §5.6).
- **P4 Local Q4 confirmation:** a promoted model runs the same battery on the pinned `llama-server` build with the exact file the Model
  Manager would ship; only that local run, and full qualification after it, can set a badge (D022 item 4; D037).
- **P5 What cannot be cloud-screened goes local directly:** models with no host (Granite 4.1 3B, Spark-X2.5-4B, NuExtract3, MiniCPM5-2B,
  the Granite 4.0 1B, H-1B and H-Tiny rows, most watch rows); Featherless-only models unless the owner buys a $50 Developer top-up
  (OWQ-27); questions that are local by nature (CPU-tier latency, memory fit, fork-only runtimes, the exact QAT file); translation and
  non-English models until their suites exist.

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| Local first for every candidate (doc 47 §6.2) | The owner chose cloud first to save time |
| Qualify in the cloud and skip the local run | A hosted copy differs in precision, engine, template and grammar; badges belong to the local setup (D022, D037) |
| Free tiers only (a protocol choice, so part of the proposal) | Few same-weights free copies exist, most without an enforced schema or zero data retention (doc 50 §5.4) |

## Consequences

- Doc 47 §6 and doc 48 §6.0 point here. Doc 48's round 1 (the uplift ladder and frontier comparators) stays deferred; the screen is a
  separate, smaller step. This is our reading of how the rule sits beside the earlier deferral of round 1 (D021's amendment note), not
  something the owner said; OWQ-27 asks the owner to confirm the schedule.
- The screen needs the cloud backend of `tools/local-qual`, which doc 48 lands only after doc 49's local run; that schedule, and any
  spend (about $0.22 in tokens for 13 endpoints, plus OpenRouter's card fee), are OWQ-27.
- Records keep (aggregator, model, endpoint, precision, reasoning setting, date) for every cloud result (doc 48 §7.4 item 1). A cloud
  result is never shown to users as a badge.
- Interim practice until OWQ-26 is answered (a cautious default, not an owner decision): models or services whose policies ban
  military uses or violent content are screened only if OWQ-26 allows it, and the NVIDIA trial and Z.ai are not used as screening
  hosts (doc 50 §5.9).

## Sources

Owner direction of 2026-09-27; doc 50 (§5, §2.3); doc 47 (§6.1–§6.3); doc 48 (§1.2, §4, §6.0, §6.5, §6.6, §7.4); doc 46 (§2.4–§2.5);
D021 (amendment note of 2026-09-27); D022; D037.

## Amendment notes

### 2026-09-28: owner answers to OWQ-26 and OWQ-27

A note under lifecycle item 5 (`docs/decisions/README.md`): it fills in this record's open parts and reverses nothing; the text above
stays as written, and the header's **Open parts** gained pointers. OWQ-27 is a one-off spend and schedule decision, so it is recorded
here rather than as a record of its own.

- **OWQ-26 (a) → [D047](D047-military-use-policy-models-and-services.md).** The interim practice under Consequences is now the owner's
  rule: such models and services are tested with the synthetic suites only and never recommended or preset; the NVIDIA trial and Z.ai
  are not used at all; combat-flavoured items never go to hosts with violent-content clauses.
- **OWQ-27 (b), spend.** The owner buys 10 OpenRouter credits once (card fee $0.80, OpenRouter's minimum); a separate screening key is capped at $1
  (estimate: about $0.22 on 13 endpoints); the tool's hard cap applies on every run; round 0's free-only key keeps its $0 limit. No
  Featherless top-up (option (c) was not chosen), so P5's Featherless-only models go local directly. Purchase and key: not yet done
  (owner action); agents never create accounts or handle keys. The answer funds P2's paid, pinned endpoints; P1–P5 stay proposals.
- **OWQ-27, schedule.** The cloud backend lands in `tools/local-qual` "once the doc 49 run releases it" (the Answer line), that is
  after doc 49's run, not before its remaining rows as OWQ-27's recommendation proposed. Round 1 (the uplift ladder and the frontier
  comparators) stays deferred, which confirms the reading under Consequences. How the rule applies to doc 49's rows still under way
  stays open.
- **To reconcile, not decided here:** doc 48 §6.0 runs round 0 on a dedicated account with no payment method, while bought credits
  lift the free limit only on the account that buys them; which account the credits go on is for the runbook that lands with the tool
  patch (`tools/local-qual/cloud/README.md`).
- **Badges.** "A cloud result is never shown to users as a badge" covers screens. D045's per-step-kind qualification of a free cloud
  setup is that setup's own qualification (D022 item 4), not a screen of a local candidate.
