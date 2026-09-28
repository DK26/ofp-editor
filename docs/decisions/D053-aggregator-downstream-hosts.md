# D053: Aggregator downstream hosts: the configured provider is the aggregator plus the hosts the user accepted

> **Status:** accepted · **Decided by:** owner delegation (2026-09-28, lightly edited: "Go ahead without the GPG passphrase. I will not
> be near the PC for hours. We are working remote"; "Tiny models with no cloud availability should be tested directly on PC. Either
> way, except for GPG signing, we can do everything else"; for a choice between design options, "Figure out the best option for this
> use case"); decided under the owner's delegation; the owner may overrule it on return · **Decided:** 2026-09-28 · **Recorded:**
> 2026-09-28
> **Scope:** which hosts behind an aggregator may receive the user's content, and what happens when a response comes from any other
> host (DG039 option B). **Refines:** D046 item 2 (the per-key host allow-list is an enforced boundary); D008 item 1 (a note on its
> reading for aggregators); D045's and D050's open part DG039 (header pointers). **Related:** D010, D021, D049; DG039; docs 48, 50
> and 54.
> **Open parts:** the wording of the connect card and of the pause card; option C (writing this reading into `AGENTS.md`), which the
> owner may still choose; D046's other open parts (doc 48 OQ2 as documentation, §7.4 item 1, OQ11); whether D050's router may
> continue on the next route-list entry while an aggregator setup is paused (a pause is not a limit outcome, D050 item 3).

## Context

- `AGENTS.md` ("No general system access") and D008 item 1 allow outbound traffic to "the model provider the user configured". The
  product connects only to the aggregator's API origin, but the user's mission text also reaches the host that serves the model,
  which the user may never have named and which can change between calls if fallbacks are allowed (DG039).
- D046 (OWQ-25 a) made aggregators first-class providers with a pinned route, `zdr: true` and `data_collection: "deny"`, the serving
  host shown per call, a per-key host allow-list and re-probes, and left the allow-list's meaning to DG039.
- The strict rule costs little in practice: doc 54's verification notes ("Calls") checked the served host on every one of the 3,494
  answered OpenRouter calls of screening round 1, and every one was served by the pinned host with the requested model (doc 54 TL;DR).
- DG039 recommends B. Decided under the owner's delegation, as the decisions README's "owner delegation" kind (the practice that
  follows from D049) asks when one option is sound; the owner may overrule it on return.

## Decision

1. **Option B of DG039.** For an aggregator, the configured provider is the aggregator together with the hosts of the setup's pinned
   route and the hosts on the user's per-key allow-list. This is how Plotroom reads "the model provider the user configured"
   (`AGENTS.md`; D008 item 1): the hosts shown and accepted at setup are part of what the user configured.
2. **Named before any call.** The connect card (D045 item 3; doc 50 §4) names the aggregator and every host the setup may reach before
   the first call carries user content.
3. **Adding a host is a user action**, with a new card that names it. Wilco, the router (D050) and a re-probe never add one.
4. **Any other host is flagged, never admitted.** A response served by a host outside the accepted set, or one with no served host
   reported, is flagged in the run panel, never admitted, and pauses the setup until the user decides (for an unlisted host: accept
   it through item 3; for an unreported host: retry; in either case the user may choose another setup instead).
5. **One rule for every aggregator path:** D045's presets, the Hugging Face router, and route-list entries that go through an
   aggregator.
6. **Tests first** (DG039): a stub aggregator that serves an unlisted host, reports no host, or falls back despite
   `allow_fallbacks: false`; each response is flagged, not admitted, and pauses the setup; the connect card lists every host before
   the first call; no code path adds a host without the card.

## Alternatives considered

| Option (DG039) | Why not chosen |
| --- | --- |
| A: the aggregator alone; hosts disclosed, no consent | Content can reach a host the user had not seen; the allow-list would only be a display |
| C: B, and `AGENTS.md`'s outbound sentence amended to name aggregators | Not adopted now: B fits `AGENTS.md`'s wording as item 1 reads it, and D008 carries that reading as a dated note; an `AGENTS.md` edit stays the owner's choice |
| D: every downstream host configured as a provider of its own | Contradicts D046 (OWQ-25 a) |

## Consequences

- D046 item 2's allow-list is an enforced boundary: the aggregator adapter behind D021's seam checks each response's served host
  against the accepted set before admission.
- A response is known only after the host has seen the request, so item 4 cannot recall content already sent: the pinned route and
  the privacy flags prevent, and the flag and pause make any breach visible and stop it from recurring on that setup.
- Friction (D049): one card when the user adds a host, and a pause that none of doc 54's 3,494 answered calls would have triggered;
  in return, no host the user never saw keeps receiving content unnoticed.
- Folding steps, not done here: doc 50 §4 steps 1 and 5–7; doc 48 §7.1, §7.4 item 2 and OQ2 (pointers). D008, D021, D045, D046 and
  D050 carry dated notes.

## Sources

DG039; `AGENTS.md` ("No general system access"); D008; D045; D046; D050; doc 48 (§2.5, §2.6, §7.1, §7.4 item 2, OQ2); doc 50
(§2.2, §4); doc 54 (TL;DR, §2.6, verification notes "Calls"); the owner's delegation of 2026-09-28.
