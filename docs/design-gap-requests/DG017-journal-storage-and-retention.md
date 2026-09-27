# DG017: Journal storage, atomic save, retention and export stripping

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
> **Decision by: technical** (design round, with a load-time and size measurement). Blocks: the journal in `ofp-workflow-runtime`
> (doc 38 phase W2, AT-W3 crash-at-every-entry test).

## Context

- **Doc 38 §4.2**: the journal is "an append-only typed log in the mission or campaign sidecar, excluded from export (doc 21 §9.3)";
  keys `(run, step, item, attempt)`; model records hold the capsule hash, setup, admitted value, findings and the raw reply as
  untrusted data, never reasoning text. **OQ2**: "JSONL or SQLite in the sidecar, and can journal and document be saved atomically
  with autosave?" **OQ10**: how many superseded attempts, candidates and capsules the sidecar keeps, and what export strips.
- **Doc 38 §8.1 commentary**: each stage is a child run; code may compact a finished stage into admitted results plus the records
  the inspector needs; retention limits are [U].
- **Doc 25 OQ10**: the decision log, alternatives and provenance for 300 decisions: prune policy and export exclusion (doc 19 §7.1).
- **Doc 21 §12.4 G7**: exports carry no agent leftovers (sidecar split; export scan test).
- **Doc 34 mo15**: "Share project" writes one archive containing "the typed project, sidecar and lock", so the sidecar can leave the
  machine through the handoff bundle.
- Doc 38 §4.7 names duroxide (MIT, SQLite provider) as the reference design.

## The gap

Storage format, the consistency rule between journal and document on save or crash, how much history is kept, and what leaves the
machine in a shared project are all undecided.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | JSONL segments, one per (child) run; each record length-prefixed and checksummed; a torn tail is truncated on load | Human-inspectable (glass box); trivial append; canonical journals compare easily (AT-W9); pure, size-capped parser per `AGENTS.md` | Queries need an in-memory index built at load; many small files |
| B | One SQLite file in the sidecar (WAL mode) | Transactions; indexed queries for the inspector; duroxide precedent | Opaque to users; a C dependency (SQLite is public domain); harder to diff |
| C | A (JSONL) now, with an optional SQLite index cache rebuilt from the JSONL | Keeps the source of truth readable; fast lookups when needed | Two artefacts |

## Recommended resolution (proposal)

- **Storage:** option A, revisited only if a measured load of the largest supported run (doc 38 §4.5 cap: 2,000 decisions) exceeds
  the load-time target; then option C.
- **Consistency:** the journal is appended and flushed before a commit is applied; the document is saved by write-then-rename.
  On load, `CommitApplied` records are reconciled with the document's undo history by idempotency key (doc 38 §4.3 item 5), so a
  crash between the two writes never applies a commit twice or loses one. Autosave uses the same order.
- **Retention:** admitted results and every record the inspector needs for an element are kept while the element exists.
  Superseded attempts and non-chosen candidates: the last 3 per journal key [I: placeholder]. Capsule bytes: kept until the run's
  stage is compacted, then only their hashes. A "Compact AI history" command and a per-project size warning.
- **Export:** mission and campaign export strips the whole sidecar (doc 21 §12.4 G7). The "Share project" bundle (mo15) includes the
  journal only if the user ticks "Include AI history", and even then without capsules or raw replies unless ticked separately,
  because they may contain the user's brief and untrusted third-party text.

## What it would change

- Doc 38 §4.2, OQ2 and OQ10 answered; §8.1 commentary gets the retention numbers.
- Doc 25 OQ10 answered by pointer.
- Doc 34 mo15: the "Include AI history" option.
- Doc 21 §9.3 / §12.4 G7: unchanged; the export scan test covers the bundle option.

## Affected docs

Docs 21, 25, 34, 38; doc 43 (added 2026-09-27, see the verification notes).

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 38 §4.2, §4.3, §4.5, §4.7, §8.1, OQ2 and OQ10; doc 25 OQ10; doc 21 §12.4; doc 34 mo15, re-read on 2026-09-27.
  The mo15 interaction was found while filing and is not recorded elsewhere.
- *Docs 39, 41 and 43 step (2026-09-27).* Doc 43 §3.4 and open question 5 add a second case of journal data leaving the machine:
  the **replay record** (the seed code, the journal's settled answers with Pick letters mapped to stable ids, admitted Fill text and
  human edits as ops; never raw replies or reasoning), shared from the Share dialog so another user can reproduce a model-assisted
  campaign with no model call. Doc 43 calls it an exception to "journal excluded from export" (doc 21 §9.3). The export rule above
  should say whether the replay record is its own opt-in item, separate from "Include AI history", and which size caps apply on
  import (doc 43 §3.4 already requires caps, verifier re-runs and untrusted-text handling). Doc 43 is added to the affected docs.
