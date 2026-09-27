# DG029: Outreach to the mod-channel maintainers

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **decided** (owner,
> 2026-09-27, OWQ-12): option A, with the owner's non-objection rule. Outreach not yet sent; not yet folded.
> **Decision by: owner** (who speaks for the project in public, and when). Blocks: the Community mod directory pack (doc 42 MS2,
> "maintainer courtesy notice") and the Community catalog connector (MS3, "maintainer answers").

## Context

- **Doc 42 OQ1**: outreach to the PB maintainers through a post in the CWR-CE `papa-bear-cz` Discussions category: who operates
  papa-bear.cz; whether third-party read-only clients are welcome; which User-Agent and request rate they want; the inclusion policy;
  the licence status of the 13 re-hosted archives; MIT or GPL for the MasterService code; whether a directory pack of ids, sizes and
  links is welcome. Also take part in CE issues #233 and #228 so the requirement manifest matches upstream.
- **Doc 42 OQ2**: outreach to the GS maintainer: API terms, attribution and rate for a read-only client.
- **Doc 42 §4.2**: the directory pack ships only after the PB and GS maintainers "have been asked and have not objected, not on a
  bare notice": copying a substantial part of a curated catalog can touch the EU sui generis database right even when each row is a
  fact [I; not legal advice].
- **Doc 42 §3.1**: PB has no terms, API policy or robots.txt (404); its OpenAPI file declares MIT; whether third-party clients are
  welcome is [U]. GS publishes no terms.

## The gap

The directory and the connector depend on answers only the channel maintainers can give, and nothing says who asks, where, or what
counts as non-objection.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | The owner (or a maintainer the owner names) posts one discussion in CWR-CE's `papa-bear-cz` category and contacts the GS maintainer, with the questions above | Public, on the channels' own forum; aligns with CE (the project's alignment target) | Answers may take weeks |
| B | Ship the directory with a notice and wait for objections | Faster | Doc 42 §4.2 rejects a bare notice because of the database-right caveat |
| C | Skip both until the channels publish terms | No outreach effort | MS2 and MS3 wait indefinitely |

## Recommended resolution (proposal)

Option A. One message per channel, drafted from doc 42 OQ1–OQ2, sent by the owner or a named maintainer. Non-objection is recorded
here as: a written reply that does not object, or no objection 30 days after a reply acknowledging the request [I: placeholder,
owner to set]. Answers go into doc 42 (§3.1 rows, OQ1–OQ2) and the connector's `[network] user_agent` and rate limits. Participation
in CE #233 and #228 is part of the same outreach. The directory pack (MS2) ships after the recorded non-objection; the connector (MS3)
also needs DG028.

## What it would change

- Doc 42 OQ1–OQ2, §4.2 and §8.1 (MS2/MS3 dependencies): answered or dated.
- A dated outreach log in this file's decision record.

## Affected docs

Doc 42; DG028, DG030.

## Decision record

- **Decided:** 2026-09-27. **By:** the owner, answering OWQ-12 in
  [`docs/decisions/OWNER-QUESTIONS.md`](../decisions/OWNER-QUESTIONS.md). **Chosen:** option A, as recommended above.
  **Decision record:** [D035](../decisions/D035-outreach-and-security-disclosure.md) item 4 states the rule going forward, beside the
  owner's other outreach answers (OWQ-09 to OWQ-11), and refines D030.
- **Who and where.** The owner, or a maintainer the owner names, sends one message per channel, drafted from doc 42 OQ1–OQ2: for PB,
  one discussion in CWR-CE's `papa-bear-cz` Discussions category; for GS, a message to its maintainer. Taking part in CE issues #233
  and #228 (requirement manifest) is part of the same outreach.
- **Non-objection rule (owner-set; replaces the placeholder above).** A channel counts as not objecting when either:
  1. its maintainer sends a written reply that does not object; or
  2. no objection arrives within 30 days after a reply that acknowledges the request.

  The 30 days start only from an acknowledging reply, so silence with no reply never counts, and a bare notice never counts (doc 42
  §4.2).
- **What waits for it.** The Community mod directory pack (doc 42 MS2) ships only after the PB and GS maintainers have been asked and
  their non-objection is recorded in the log below (doc 42 §4.2). The Community catalog connector (MS3) also needs the maintainers'
  answers on User-Agent and request rate; its connector kind is settled by DG028 (D008).
- **Reason.** Public, on the channels' own forum, and aligned with CWR-CE, the project's alignment target (D003). Option B is the bare
  notice doc 42 §4.2 rejects because of the EU database-right caveat [I; not legal advice]; option C leaves MS2 and MS3 waiting
  indefinitely.
- **Outreach log.** Answers also go into doc 42 (§3.1 rows, OQ1–OQ2) and into the connector's `[network] user_agent` and rate limits.

  | Channel | Where | Sent | Acknowledged | Outcome |
  | --- | --- | --- | --- | --- |
  | PB (MODS storage) | CWR-CE Discussions, `papa-bear-cz` category | not yet | — | — |
  | GS (Game Schedule) | Its maintainer | not yet | — | — |

- **Folding (what moves this request to `folded`).** Doc 42 OQ1–OQ2, §4.2 and §8.1 (MS2 and MS3 dependencies) state the rule and point
  here; D008's and D030's open parts for DG029 are updated under the decision-record rules (done 2026-09-27: both headers and notes
  point to D035). The outreach itself is logged above as it happens; folding does not wait for the answers.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 42 §3.1, §4.2, §8.1, OQ1 and OQ2, re-read on 2026-09-27. No outreach was made in this pass. Not legal advice.

### Owner answers (2026-09-27)

- Decision record written from the owner's dated answer to OWQ-12, which adopts the placeholder rule unchanged. Re-read for this
  step: OWQ-12, D008, D030 and doc 42 §4.2 and the MS2 row. No outreach was made; doc 42 was not edited.

### Consistency review of the owner answers (2026-09-27)

- The decision record now links D035, whose item 4 states the same non-objection rule. D008 and D030 point to D035; doc 42 is still
  to be folded, so the request stays `decided`.
