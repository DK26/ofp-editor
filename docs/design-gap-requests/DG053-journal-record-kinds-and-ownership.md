# DG053: New journal record kinds, and one owner per journal

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-28 in the go-ahead pass (design-gap candidates of docs 51–63).
> Status: **open**.
> **Decision by: technical** (design round). Blocks: the journal schema (doc 38 §4.7; DG017), the inspector's record views (doc 38
> §5.3), and the records proposed in docs 51, 56, 57, 58, 59 and 63, which stay `proposal-only`.

## Context

- **Doc 38 §4.2, §4.7.** An append-only typed journal keyed `(run, step, item, attempt)`; model records hold the capsule hash, setup,
  admitted value, findings and the raw reply as untrusted data, "never reasoning text". **DG017** (open): storage, atomic save,
  retention (superseded attempts kept for the last three per key; capsule bytes until compaction) and export stripping.
- **Doc 51 §6.2.** `Discarded` and `Abandoned` records with typed causes; intake normalisations and admission flags logged; the raw
  failed reply kept as data; request-body and profile hashes per record.
- **Doc 56 §10 items 2 and 4.** Harness-authored records (repair notes, corrections, reminders), with only admitted answers re-entering
  history; a single-owner lock per journal with user-visible stale-lock handling.
- **Doc 57 TE-G4, TE-G5 (JL1–JL3, CL6).** Context receipts for every prune, mask, digest regeneration and window reset; capsule
  manifests (block ids, tokens, hashes, suppression reasons); ledger buckets with a cost source; a cache-miss classifier. Receipts
  never enter model context.
- **Doc 58 §4.11 item 4, §4.10.** Records for component outputs and the "answered by" display.
- **Doc 59 §7 item 4, §5.4.** Reasoning records: the thought id and hash, the reasoning token count and the `why` as an untrusted
  note, never the model's thinking text.
- **Doc 63 §13 item 6.** Pull-tool budgets and split-down events. **D051 item 7**: no stored reasoning text, no model-written memory.

## The gap

Six docs add records the journal would need; doc 38 §4.7's list names none of them, DG017 does not give them retention classes, and
nothing prevents two editor instances from appending to one journal.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Keep doc 38 §4.7's records and add fields as features land | No up-front work | Records drift per crate; replay tests and the inspector have no closed set to cover |
| B | One closed, versioned set of record kinds that adds the kinds above, each with a DG017 retention class and an inspector view; none ever sent to a model except through a code-rendered digest; reasoning text never stored; a single-owner lock per journal with a stale-lock prompt | One schema for replay (doc 38 §6.4), the inspector (D010) and retention | A larger schema to version and migrate |

## Recommended resolution (proposal)

B (each of docs 51, 56, 57, 58, 59 and 63 proposes its part; D051 item 7 fixes the reasoning-text rule).

## What it would change

- Doc 38 §4.2 and §4.7 (record list); DG017 (retention classes, lock); agent-runtime §5 (`ModelRequested` and friends); the
  inspector (doc 38 §5.3).
- Tests first (proposal): every record kind round-trips; a replay rebuilds the exact request bytes from receipts (doc 57 JL2); no
  record kind carries a thinking-text field; a second editor instance cannot append while the lock is held and sees the stale-lock
  prompt after a crash.

## Affected docs

Doc 38 (§4.2, §4.7, §5.3, §6.4); doc 51 §6.2; doc 56 §10; doc 57 (§5, §6.1); doc 58 (§4.10, §4.11); doc 59 (§5.4, §7); doc 63 §13;
`docs/architecture/agent-runtime.md` §5; D010; D051; DG017.

## Decision record

Open.

## Verification notes

### Filing (2026-09-28)

- Filed from doc 56 §10 items 2 and 4, doc 57 TE-G4 and TE-G5, doc 58 §4.11 item 4, doc 59 §7 item 4, doc 63 §13 item 6 and doc 51
  §6.2's journal fold (deduplicated), re-read on 2026-09-28 with doc 38 §4.2 and §4.7 and DG017.
