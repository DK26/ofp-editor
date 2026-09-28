# DG039: Downstream hosts behind an aggregator: what "the model provider the user configured" covers

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-28 with the owner's answer to OWQ-25 (D046). Status: **decided**
> (owner's delegation, 2026-09-28): option B → D053. The configured provider is the aggregator plus the hosts the user accepted; a
> response from any other host, or with no served host reported, is flagged, never admitted, and pauses the setup. Not yet folded.
> **Decision by: owner** (network boundary: which parties the user's content may reach, and possibly `AGENTS.md`'s wording). Blocks:
> the meaning of D046's per-key host allow-list and what the connect card and a setup must name beyond the pinned route's host, which
> every option below names (doc 50 §4 steps 1 and 5–7); these stay `proposal-only` until decided. D046's other safeguards (pinned
> route, privacy flags, host shown per call, re-probes) and D045's card naming the serving host are not blocked.

## Context

- **`AGENTS.md`, "No general system access"; D008 item 1.** The product's outbound traffic goes only to "the model provider the user
  configured", the declared endpoints of plugins the user enabled, and download or feed sources the user explicitly enabled.
- **Doc 48 §7.4 item 2** (its design-gap candidate 2): "With OpenRouter configured, requests reach hosts the user did not name.
  Proposed: ZDR and no-data-collection by default, the host shown per call, and a per-key allow-list of hosts." §7.1: an aggregator
  "forwards data beyond 'the model provider the user configured' (AGENTS.md)". §2.6: OpenRouter's default routing weights hosts by the
  inverse square of their price, so unpinned traffic mostly lands on the cheapest host, which may not be ZDR. OQ2: whether OpenRouter
  returns the served provider in the response body is undocumented; the runner marks records `provider_unverified` when it is missing.
- **Doc 50** §4: the disclosure card states the data route ("your mission text, briefings and names go to OpenRouter and then to
  ModelRun"); the free-only guard pins `provider.only` with `allow_fallbacks: false`; reading OpenRouter's catalogue is justified
  because, once chosen, OpenRouter "is 'the model provider the user configured' (D008 item 1)". §2.2: the only free zero-retention
  generalist is served by ModelRun, and whether its operator's use policy applies to that endpoint is unknown.
- **D046** (OWQ-25 a, 2026-09-28): aggregators are first-class providers with a pinned route, `zdr: true` and `data_collection:
  "deny"` by default for user content, the serving host shown per call, a per-key host allow-list and periodic re-probes. OWQ-25's
  recommendation read the aggregator as "the model provider the user configured" and asked for this request to settle how that
  wording covers the downstream host; the Answer line neither restates nor rejects that reading, and asks for this request.

## The gap

The product opens connections only to the aggregator's API origin, so on a network reading the rule already holds. But the user's
mission text also reaches a second party, the host that serves the model, which the user may never have named and which can change
between calls if fallbacks are allowed. The rule does not say whether "the model provider the user configured" means the aggregator
alone, the aggregator together with the hosts the user saw and accepted, or each host by name. Without an answer, D046's allow-list
has no defined meaning (a display filter, a consent record or an enforced boundary), and doc 50's card has no rule for what it must
name before the first call.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | The aggregator is the configured provider; downstream hosts are disclosed on the card and per call, with no separate consent | Matches the network reading; least friction when a free model's host changes | Content can reach a host the user had not seen before the call; the allow-list is only a display |
| B | The configured provider is the aggregator together with the hosts of the setup's pinned route and the user's allow-list: the card names them before any call; adding a host is a user action with a new card; a response served by any other host is flagged, never admitted, and pauses the setup until the user decides | The user names every host their content reaches (D010); gives D046's allow-list a meaning | Relies on the aggregator honouring the pin and reporting the served host (doc 48 OQ2); one more step when a host changes |
| C | As B, and `AGENTS.md`'s outbound sentence amended to name aggregators and the hosts the user allowed | No ambiguity left in the invariant | An `AGENTS.md` edit (owner) |
| D | Every downstream host must be configured as a provider of its own; aggregators only as plain endpoints | Strictest reading | Contradicts D046 (OWQ-25 a) |

## Recommended resolution (proposal)

B. It turns D046's allow-list into an enforced boundary, keeps the glass-box rule (D010), and fits `AGENTS.md`'s wording if the owner
reads "configured" as covering the hosts shown and accepted at setup; C writes that reading into `AGENTS.md` if the owner wants it
explicit. A call whose served host is not reported is marked "host unverified" in the run panel; whether such a call may carry user
content is part of the decision.

## What it would change

- D046 item 2: the allow-list's meaning; D008: a note on aggregators (or `AGENTS.md` under C).
- The aggregator adapter behind D021's seam: its rule for a response from an unlisted or unreported host. Tests (proposal): a stub
  aggregator that serves an unlisted host, reports no host, or falls back despite `allow_fallbacks: false`.
- Doc 50 §4 steps 1 and 5–7 (what the card and "Which models are free today" name); doc 48 §7.1 and §7.4 item 2 (pointer).
- D045's presets and the Hugging Face router, which also forwards to providers, follow the same rule.

## Affected docs

`AGENTS.md` (option C only); D008; D021; D045; D046; doc 48 (§2.6, §7.1, §7.4 item 2, OQ2); doc 50 (§2.2, §4).

## Decision record

- **Decided 2026-09-28 under the owner's delegation: option B → [D053](../decisions/D053-aggregator-downstream-hosts.md).** The
  configured provider is the aggregator together with the hosts of the setup's pinned route and the user's per-key allow-list, named
  on the connect card before any call; adding a host is a user action with a new card; a response served by any other host, or with
  no served host reported, is flagged in the run panel, never admitted, and pauses the setup until the user decides. The same rule
  covers D045's presets and the Hugging Face router. The owner may overrule it on return.
- **Reason.** B gives D046's allow-list a meaning and keeps the glass box (D010); doc 54's round 1 found every one of 3,494 answered
  OpenRouter calls served by the pinned host, so the strict rule costs little. C is not adopted now: B fits `AGENTS.md`'s wording read
  as covering the hosts shown and accepted at setup, which D008's note records; the owner may still choose C. D contradicts D046.
- **Folding (what moves this request to `folded`).** Doc 50 §4 steps 1 and 5–7; doc 48 §7.1, §7.4 item 2 and OQ2 (pointers). The
  notes on D008, D021, D045 and D046 and the pointers in D045's, D046's and D050's **Open parts** are done (2026-09-28).

## Verification notes

### Filing (2026-09-28)

- Filed from doc 48 §2.5, §2.6, §7.1, §7.4 item 2 and OQ2, doc 50 §2.2 and §4, D008, D046, `AGENTS.md` "No general system access"
  and OWQ-25's entry and Answer line, re-read on 2026-09-28. D046 does not decide this request. No provider was contacted and nothing
  here is legal advice.
- Verification (2026-09-28): the D046 bullet under Context said the owner's answer filed this request "without adopting" OWQ-25's
  reading; the Answer line is silent on that reading, so the bullet now says so. The header's "Blocks" now leaves out the serving
  host of the pinned route, which every option names and D045's card already shows. The quotes from docs 48 and 50 were checked
  against their sources; no option or recommendation changed.

### Owner delegation, design-gap pass (2026-09-28)

- Decided with the recommended option B under the owner's delegation of 2026-09-28 (quoted in D053). D053 was written from this
  request, D008, D021, D045, D046, doc 48 (§2.6, §7.1, §7.4, OQ2), doc 50 §4 and doc 54 (TL;DR, §2.6, verification notes "Calls"),
  re-read on 2026-09-28. The header, the decision record and the index row were updated; docs 48 and 50 were not edited.
