# DG018: Where records of ported permissive-licence code live

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
> **Decision by: technical** (compliance mechanics; the licence itself is settled as GPL-3.0-or-later, doc 02 governs). Blocks: the
> first port of any Apache-2.0 or MIT code (doc 38 §1.2 candidates).

## Context

- **Doc 38 §1.2**: Codex is Apache-2.0; its `NOTICE` credits OpenAI and Ratatui (MIT). A port "ships the license and NOTICE contents
  in our third-party notices, marks modified files, keeps copyright lines, cites the `CX:` path in a comment and is recorded in a
  provenance list (Open question 9)". duroxide code (MIT) needs attribution if taken. Candidates: the `restrict_to` meet, the
  role-authority test, the catalog budget algorithm, a BM25 selector.
- **Doc 38 OQ9**: "Where do Apache-2.0 port records live (for example a `docs/porting/` file beside `upstream-test-map.csv`)?"
- **Doc 02 §10.4**: a `Derived-From:` header for code translated from CWR or CWR-CE, a PR checkbox, CI checks on permissive crates,
  and `reuse lint` plus `cargo deny`.
- **`AGENTS.md`** "Porting Upstream Code and Tests": upstream tests are tracked in `docs/porting/upstream-test-map.csv`.

## The gap

There is a rule for engine-derived code (`Derived-From:` headers) and a tracker for upstream tests, but no agreed place or format
for records of other ported code (Apache-2.0, MIT), which carry their own notice obligations.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | A hand-kept `docs/porting/third-party-ports.csv` | Easy to read | Drifts from the code |
| B | Per-file headers only | Next to the code | No overview for the release's third-party notices |
| C | Per-file `Derived-From:` headers are the source of truth (extending doc 02 §10.4 to every upstream licence); CI generates and checks `docs/porting/provenance.csv` and the third-party notices file from them | One rule for all ports; the list cannot drift; notices are complete by construction | A small CI script |

## Recommended resolution (proposal)

Option C. Header form: `Derived-From: <repo>@<commit>:<path>#L<a>-L<b> (<SPDX licence>)`, one line per source, plus `Modified:
<yes|no>`. CI refuses a file whose header names a licence missing from the allowlist, regenerates `docs/porting/provenance.csv`
(columns: our path, upstream repo and commit, upstream path and lines, licence, modified, notice entry) and fails when the committed
copy differs. The third-party notices file for binary releases (doc 02 §10.6) is generated from the same data, including each
upstream `NOTICE` text.

## What it would change

- Doc 02 §10.4: the header covers every upstream licence, not only CWR/CWR-CE.
- Doc 38 §1.2 and OQ9 answered by pointer.
- `docs/porting/`: gains `provenance.csv` (generated) beside `upstream-test-map.csv`.
- `CONTRIBUTING.md` (when written): the header rule.

## Affected docs

Doc 02, doc 38, `docs/porting/`, `AGENTS.md` (no change needed).

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 38 §1.2 and OQ9, doc 02 §10.4 and §10.6, and `AGENTS.md` "Porting Upstream Code and Tests", re-read on
  2026-09-27. `docs/porting/` currently holds only `upstream-test-map.csv`. Not legal advice.
