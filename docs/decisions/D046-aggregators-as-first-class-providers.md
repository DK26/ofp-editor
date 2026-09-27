# D046: Aggregators as first-class providers, with safeguards

> **Status:** accepted · **Decided by:** owner (OWQ-25 a) · **Decided:** 2026-09-28 · **Recorded:** 2026-09-28
> **Scope:** model providers that forward a request to a host the user did not name, today OpenRouter and the Hugging Face router.
> **Refines:** D021 (its amendment note's aggregator proposals, and doc 48 OQ10, which that note called not yet filed).
> **Related:** D008, D010, D026, D044, D045, D047.
> **Open parts:** DG039 (what "the model provider the user configured" covers for the downstream host); whether the served host is
> reported in the response (doc 48 OQ2); the identity of a cloud setup and the re-probe cadence (doc 48 §7.4 item 1, OQ11).

## Context

- Through an aggregator a request reaches a host the user did not name. OpenRouter's default routing weights hosts by the inverse
  square of their price, so unpinned traffic mostly lands on the cheapest host, which may not be ZDR (doc 48 §2.6).
- OpenRouter can pin one endpoint per request (`provider.only`, `allow_fallbacks: false`, `require_parameters: true`), demand zero data
  retention (`zdr: true`) and exclude data-collecting hosts (`data_collection: "deny"`); request flags only tighten account settings
  (doc 48 TL;DR, §2.5; doc 50 §2.2).
- OpenRouter is the only one-click, no-registration route to a free model with zero-data-retention pinning, and D044's screening
  relies on it (OWQ-25).
- `AGENTS.md` and D008 item 1 allow outbound traffic to "the model provider the user configured".

## Decision

1. **Aggregators are first-class providers** in the provider layer (D021), not only a generic endpoint the user types in.
2. **Safeguards, on by default:**
   - a **pinned provider route** per setup: endpoint, precision, `allow_fallbacks: false`, `require_parameters: true`;
   - for user content, **`zdr: true` and `data_collection: "deny"`**;
   - the **host that served each call** recorded and shown in the run panel and the decision inspector (D010);
   - a **per-key allow-list of hosts**;
   - **periodic re-probes** of each setup.
3. **DG039 is filed** on how "the model provider the user configured" covers the downstream host. This record does not decide it
   (lifecycle item 2); the allow-list's exact meaning waits for it.

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| A generic OpenAI-compatible endpoint that the user types in, with no route pinning or host display (OWQ-25 b) | Hides the downstream host that the safeguards make visible |
| Not supported (OWQ-25 c) | Loses the only one-click free route with ZDR pinning, and D044's screening route |

## Consequences

- The aggregator adapter behind D021's seam carries the pinned route (item 2). Keying prices and qualifications by (aggregator, model,
  endpoint, precision, reasoning setting, date) is D021's amendment-note proposal and stays open (doc 48 §7.4 item 1).
- What the capability probe and its re-probes check (one real strict-schema request, a reasoning-off check and the served host per
  setup) is a proposal (D021's amendment note; doc 48 §7.1, §7.4 item 3). A call whose served host is not reported is marked as such,
  never assumed (doc 48 OQ2); whether it may carry user content is part of DG039.
- D045's disclosure card names the host that will serve the model, and the run panel names the host that did.
- Account-wide privacy settings may add a guard beside the per-request flags, never loosen one.
- The Hugging Face router, which also forwards to providers, follows the same rules.

## Sources

`OWNER-QUESTIONS.md` OWQ-25 (Answer of 2026-09-28); doc 48 (TL;DR, §2.5, §2.6, §7.1, §7.4 items 1–3, OQ2, OQ10, OQ11); doc 50 (§2.2,
§4); D008; D010; D021 (amendment note of 2026-09-27); DG039.
