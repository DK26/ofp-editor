# DG056: One envelope, sanitiser and diagnostic contract for model-facing tool output

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-28 in the go-ahead pass (design-gap candidates of docs 51–63).
> Status: **open**.
> **Decision by: technical** (design round). Blocks: result shapes for Wilco's query tools, Teller's model-facing diagnostics and
> plugin tool results (doc 22); doc 57 TM1–TM3, doc 61 TG2 and doc 62 §10 item 4 stay `proposal-only`.

## Context

- **Doc 57 TE-G9, TM1–TM3.** A typed result envelope for every Wilco query tool and plugin result: shown and total counts, a cursor
  from rendered rows, the document revision, an evidence id (journal reference), the exact omitted count, a narrowing hint named by
  the tool, and "empty" distinct from "cut by budget"; result caps from the served window; cuts never split JSON or a row, with one
  counted, non-imitable marker. TE-G9: "Doc 22 does not define result shapes for token budgets"; the envelope goes in the plugin
  manifest.
- **Doc 61 TG2, §6 item 2.** A sanitiser for every echoed mission name in model-facing text ("doc 23 §13.4 states the rule without a
  mechanism"): which fields, which caps, which escaping, "shared with plugin results (doc 57 TE-G9)". Doc 61's findings: validation
  §9's "Model-shaped diagnostics" row has no delta, priority or sanitiser rule.
- **Doc 62 §6.9, §10 item 4.** Every finding ends with the next action; a diagnostic transport contract between Teller, Wilco,
  external agents and coding agents fixing which fields must survive (message, notes, code, location, next action, rendered).
- **Doc 21 §9.1.** Untrusted text inside tool results stays quoted and labelled. **D043; `AGENTS.md`**: plugin output is untrusted data.
- **Agent-runtime §8** lists the tool family; **DG032** (open) proposes one knowledge store and tool family.

## The gap

Product tools, Teller and plugins all send text to models and external agents, but no document defines one shape for it: how results
are capped and marked when cut, how untrusted names inside them are escaped, and which diagnostic fields survive each transport.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Each producer defines its own result shape | Local freedom | Caps, truncation and sanitising differ per tool; a plugin can return unbounded or instruction-shaped text |
| B | One typed envelope for every model-facing result (TM1's fields, TM3's cut marker), declared by plugins in their manifest; one sanitiser for every echoed untrusted string (TG2); one diagnostic field set that survives every transport (doc 62 §10 item 4) | One place to test caps, escaping and "empty versus cut" | Plugin authors fill the envelope; the manifest schema grows |

## Recommended resolution (proposal)

B (docs 57, 61 and 62 each propose one part of it).

## What it would change

- Doc 22 (the manifest declares result envelopes); agent-runtime §8; validation-and-lints §9 (the sanitiser and field set for
  model-shaped diagnostics); doc 23 §13.4 (the mechanism for its rule); DG032's tool family.
- Tests first (doc 57 TM1, TM3; doc 61 TG2): shown plus omitted equals total; the cursor resumes at the first unrendered row; empty and
  cut produce different statuses; a scripted model echoing the cut marker is refused; an echoed name carrying control or instruction
  text is escaped.

## Affected docs

Doc 22; doc 23 §13.4; doc 57 (§5.2, §6.1); doc 61 (§4.5, §6, findings); doc 62 (§6.9, §10); doc 21 §9.1;
`docs/architecture/agent-runtime.md` §8; `docs/architecture/validation-and-lints.md` §9; D043; DG032.

## Decision record

Open.

## Verification notes

### Filing (2026-09-28)

- Filed from doc 57 TE-G9, doc 61 §6 item 2 and doc 62 §10 item 4 (deduplicated), re-read on 2026-09-28 with doc 57's TM table and
  doc 61's TG table and findings.
