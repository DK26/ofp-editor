# DG029: Outreach to the mod-channel maintainers

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
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

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 42 §3.1, §4.2, §8.1, OQ1 and OQ2, re-read on 2026-09-27. No outreach was made in this pass. Not legal advice.
