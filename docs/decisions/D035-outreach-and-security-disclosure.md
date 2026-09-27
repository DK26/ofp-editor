# D035: Outreach and private disclosure

> **Status:** accepted · **Decided by:** owner (OWQ-09 to OWQ-12; OWQ-12 = DG029 option A) · **Decided:** 2026-09-27
> **Recorded:** 2026-09-27 · **Scope:** who speaks for the project to Bohemia Interactive, the CWR-CE maintainers and the mod-channel
> maintainers, in what order, and how engine security findings are disclosed. **Refines:** D030 and D008 (their open part DG029 =
> OWQ-12), D003 (OWQ-10, OWQ-11), D012 (OWQ-09, OWQ-11) and D018 (OWQ-11). **Related:** D033, D034, D038.
> **Open parts:** nothing has been sent yet. Dates and answers are logged where they are used: OWQ-09's entry (security reports), doc 02
> (Bohemia's answers), `docs/upstream/` (CE statuses), DG029 and doc 42 (channel answers).

## Context

- Doc 24's disclosure note: findings F1, F3, F4, F9 and H2–H4 can be used by a downloaded mission against players of the shipping
  game, not only against Preview; neither source snapshot has a `SECURITY.md`.
- Doc 02 §11 step 8 proposes one letter to Bohemia. Open points: loading APL-SA data (Remastered, demo and 1.99) in a GPL editor, the
  MIT metadata in CWR's Cargo manifests (doc 01 OQ3; doc 07 OQ5), and extension overlays for Bohemia's campaigns (D033).
- Doc 01 §9 (c): CWR-CE is the only upstream for patches; start with CE issue #35 and a small, well-tested PR. Engine requests are
  tracked in `docs/upstream/` (D012).
- Doc 42 §4.2: the community mod directory ships only after the channel maintainers are asked and do not object, because copying a
  curated catalog can touch database rights even when each row is a fact.

## Decision

1. **Security findings first, privately (OWQ-09 a).** The owner reports doc 24's findings privately to the CWR-CE maintainers and to
   Bohemia Interactive, through a private channel of each project, and records the dates in OWQ-09. Until the reports are
   acknowledged, no new public detail is added, and doc 24 §6's hardening patches enter the engine-requests register only after that.
2. **One letter to Bohemia (OWQ-10 a)**, from the owner, after the name clearance (D034 item 2) and before the first public release:
   the name, the disclaimer and the data policy, asking for comfort on nominative use, on loading APL-SA data (Remastered, demo and
   1.99) in a GPL editor, on the MIT metadata, and on extension overlays for Bohemia's campaigns. Answers are recorded in doc 02. The
   first public release waits for an answer or a documented decision to proceed.
3. **CWR-CE (OWQ-11 a).** The owner, or a maintainer the owner names, starts with CE #35 and a small tested PR, then opens one
   tracking discussion that links the engine-requests register. Security items go upstream only after item 1's private reports.
4. **Mod-channel maintainers (OWQ-12 = DG029 option A).** The owner or a named maintainer sends one message per channel: a discussion
   in CWR-CE's `papa-bear-cz` category for the game's MODS storage, and a message to the Game Schedule maintainer, with doc 42
   OQ1–OQ2's questions and participation in CE issues #233 and #228. **Non-objection** means a written reply that does not object, or
   no objection 30 days after a reply acknowledging the request.
5. Outreach is sent only by the owner or a maintainer the owner names.

## Alternatives considered

- Public issues for the findings (OWQ-09 b), or waiting until Plotroom ships (c): exposes players, or leaves them exposed longer.
- No letter to Bohemia (OWQ-10 b): the first release would rest on doc 02's reading alone.
- Filing every engine request at once (OWQ-11 b), or no outreach until v1 (c): floods a small team, or stalls Preview phase P3 and
  every "proposed" status in the register.
- DG029 B (ship the directory with a notice) or C (wait until the channels publish terms): doc 42 §4.2 rejects a bare notice; MS2 and
  MS3 would wait indefinitely.

## Consequences

- The first public release (roadmap M3) needs D034 item 2, item 1's reports and item 2's answer or a decision to proceed.
- The directory pack (doc 42 MS2) ships after a recorded non-objection; the catalog connector (MS3) also follows D008's feed rules.
  Channel answers set the connector's user agent and request rate (doc 42 §3.1, OQ1–OQ2).
- Every "proposed" status in `docs/upstream/` follows item 3's order.
- Not legal advice; doc 02 governs licensing and trademark readings.

## Sources

Doc 24 (disclosure note, §6); doc 02 (§11, open questions); doc 01 (§9, OQ3, OQ5); doc 07 OQ5; doc 08 P3; doc 18 §9; doc 29 OQ9;
doc 42 (§3.1, §4.2, §8.1, OQ1–OQ2); DG029; roadmap §4; `OWNER-QUESTIONS.md` OWQ-09 to OWQ-12.

## Notes

- 2026-09-27 (consistency review): **Refines:** now also names D008, D003, D012 and D018, whose headers listed OWQ-09 to OWQ-12 as
  open parts and now point here (citation fix; no decision changed).
