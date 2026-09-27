# DG014: May one plugin's output feed another plugin's egress in a workflow

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
> **Decision by: owner** (it sets how far the plugin security boundary stretches). Blocks: the `requires` rule for pack workflows
> (doc 38 §3.1, §6.1–§6.2) and the install review for T0 workflows.

## Context

- **Doc 22 §3.2**, "No widening": "There are no cross-plugin calls; only the agent chains tools, and each call obeys the called
  plugin's grant." §4.2: a workflow step names a plugin tool and declares `requires`; the callable set is declared tools ∩ enabled
  plugins ∩ grants.
- **Doc 22 §3.1** runtime prompts: an egress card on the first network call per mission per plugin; **every time** for an
  agent-initiated call while untrusted text (a downloaded mission, a plugin output) is in context.
- **Doc 38 OQ13**: "May a pack workflow's `requires` name another publisher's plugin, so that one plugin's output feeds another
  plugin's egress? … Proposed: allow it only for first-party and user-authored definitions, with the egress card shown every time."
- Doc 38 §6.1: pack workflows cannot add step kinds, code steps, checks or wider tool sets; §9: workflows using T2 plugin tools are
  not exposed to external agents in v1.
- `AGENTS.md`: plugin outputs are untrusted data; no plugin gains shell or arbitrary file access.

## The gap

A workflow is a fixed chain, not the agent choosing tools one by one. If a pack workflow may `require` a plugin from another
publisher, plugin A's output (untrusted) can be sent by plugin B to B's service without a model or the user deciding each send.
Doc 22 allows chaining only by the agent; doc 38 has no rule for chains authored in a pack.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Forbid: a pack workflow may `require` only plugins from its own publisher | Simplest boundary; no cross-publisher data flow without the agent | Blocks useful pipelines (translate with one service, voice with another) |
| B | Allow for first-party and user-authored definitions only; pack workflows from third parties stay single-publisher; the egress card shows every time a step sends another plugin's output | Useful pipelines exist, but only from sources the user trusts or wrote; every send is visible | The user-authored route needs a way to author workflows (no Wilco tool writes definitions, doc 38 §2) |
| C | Allow for any pack, with an install-review line "sends output of X to Y" and per-send egress cards | Most flexible | A malicious pack can pair a scraping plugin with an exfiltrating one; review fatigue |

## Recommended resolution (proposal)

Option B, as doc 38 OQ13 proposes. Load-time validation refuses a third-party pack workflow whose `requires` names a plugin of
another publisher. First-party and user-authored workflows may chain plugins; any step that sends a value derived from another
plugin's output shows the egress card every time (the doc 22 §3.1 "untrusted text in context" row), naming both plugins and the
payload. Such workflows are never exposed over `ofp-mcp` (doc 38 §9 already excludes T2 workflows in v1).

## What it would change

- Doc 22 §3.2 "No widening": a sentence on workflow chains; §4.2: the publisher rule for `requires`.
- Doc 38 §6.1–§6.2: the load-time refusal and its fixture (AT-W1, AT-W14); OQ13 answered.
- `AGENTS.md` "Extensions only through the plugin system": no change needed if option B is taken.

## Affected docs

Docs 22, 38.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 22 §3.1, §3.2 and §4.2, doc 38 §2, §6.1–§6.2, §9 and OQ13, and `AGENTS.md`'s plugin rules, re-read on
  2026-09-27.
