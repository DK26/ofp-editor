# DG060: The exact text of the generated-content permission in NOTICE

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-29 by the SP-09 change set, the first change set with code
> derived from CWR and CWR-CE, which added `NOTICE`. Status: **open**.
> **Decision by: owner** (licensing; D031 item 1 says the wording also passes a legal review before 1.0).
> Blocks: the "Content Plotroom writes for its users" section of `NOTICE`, which states that the permission is not there yet;
> README "License" keeps stating the intent (D001 item 4).

## Context

- **D001 item 4**: Plotroom adds its own GPLv3 section 7 additional permission for content the program writes for its users;
  "until it is in `NOTICE`, the README's promise states the intent".
- **D031 item 1 (OWQ-01 option b)**: `NOTICE` carries the doc 02 §6.2 draft "with 'Plotroom' filled in, plus an explicit list of
  covered output: compiler and module lowerings, generated scripts and glue, finishers, AI-written text, and first-party pack content
  copied into missions", keeping the exclusion of material derived from Bohemia's CWR source; legal review before 1.0.
- **Doc 02 §6.2**: the draft text of the permission. It speaks of "this program" and has no placeholder for the name.
- **Doc 02 §10.1**: `NOTICE` holds the project copyright, the SPDX line, the permission, Bohemia's notice and terms verbatim with a
  scope note, and the trademark disclaimer.

## The gap

The decision fixes what the permission covers but not its words. Two pieces of text are missing: where "Plotroom" goes in a draft
that says "this program", and the sentence that turns D031's coverage list into licence text. Writing either would be inventing
licence wording, which the owner decides (and a lawyer reviews).

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | The owner writes the final wording (draft plus coverage sentence) into D031 or doc 02 §6.2; the next change set copies it into `NOTICE` verbatim | Licence text comes from the owner | Waits for the owner |
| B | Put the doc 02 §6.2 draft into `NOTICE` unchanged now, and add the coverage list later | Some permission is published sooner | D031 chose the draft **plus** the list; the draft alone is option (a) of OWQ-01, which the owner did not pick |

## Recommended resolution (proposal)

Option A. Until then `NOTICE` says the permission is pending and points to README, as D001 item 4 allows.

## What it would change

`NOTICE` (the pending section becomes the permission), README "License", and the SPDX header line that doc 02 §10.2 adds to our own
files once our section 7 permission exists ("Additional permissions under GPLv3 section 7 apply; see NOTICE.").

## Affected docs

`NOTICE`; `README.md`; `docs/research/02-licensing-and-trademarks.md` §6.2, §10.1, §10.2; D031.

## Decision record

Open.

## Verification notes

### Filing (2026-09-29)

- D001, D031, OWNER-QUESTIONS OWQ-01 and doc 02 §6.2, §9, §10.1–§10.2 were read. None contains the combined wording.
