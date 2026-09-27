# DG014: May one plugin's output feed another plugin's egress in a workflow

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **decided** (owner,
> 2026-09-27, OWQ-16): option B. Only first-party and user-authored workflows may chain plugins of different publishers, with the
> egress card every time, and such workflows are never exposed to external agents. Not yet folded.
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

- **Decided:** 2026-09-27. **By:** the owner, answering OWQ-16 in
  [`docs/decisions/OWNER-QUESTIONS.md`](../decisions/OWNER-QUESTIONS.md). **Chosen:** option B, as recommended above.
  **Decision record:** [D043](../decisions/D043-cross-plugin-chaining-in-workflows.md) states items 1–4 below as the rule going
  forward and refines D007.
- **Rule.**
  1. **Third-party pack workflows stay single-publisher.** Load-time validation (doc 38 §6.2) refuses a third-party pack workflow
     whose `requires` names a plugin of another publisher, with a field-labelled error and a CI fixture (AT-W1; the hostile-pack test
     AT-W14 gains this case).
  2. **First-party and user-authored workflows may chain plugins** of different publishers.
  3. **The egress card shows every time** a step sends a value derived from another plugin's output, naming both plugins and the
     payload (the doc 22 §3.1 "untrusted text in context" row). "Every time" holds at every autonomy level, including Auto.
  4. **Never exposed to external agents.** Such workflows are not listed or startable over Plotroom's MCP server (`ofp-mcp` in doc 38
     §9), in v1 or later. Doc 38 §9's v1 exclusion of workflows using T2 plugin tools stays as it is.
- **Unchanged.** No plugin calls another plugin (D007 item 2; doc 22 §3.2 "No widening"): the host runs each step, and each call
  obeys the called plugin's grant. Plugin outputs remain untrusted data (`AGENTS.md`).
- **Reason.** Useful pipelines (translate with one service, voice with another) come only from sources the user trusts or wrote, and
  every cross-plugin send is visible. Option A blocks those pipelines; option C lets a malicious pack pair a scraping plugin with an
  exfiltrating one behind a single install review.
- **Open detail (not decided here).** How the host tells a user-authored definition from an installed third-party pack, and how users
  author workflows at all (no Wilco tool writes definitions, doc 38 §2), belong to doc 38 §6.1 when this decision is folded.
- **Folding (what moves this request to `folded`).** Doc 22 §3.2 (a sentence on workflow chains) and §4.2 (the publisher rule for
  `requires`); doc 38 §6.1–§6.2 (the refusal and its fixtures), §9 (item 4 above) and OQ13 (answered); D007's open part for DG014,
  under the decision-record rules (done 2026-09-27: D007's header and note point to D043). `AGENTS.md` needs no change.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 22 §3.1, §3.2 and §4.2, doc 38 §2, §6.1–§6.2, §9 and OQ13, and `AGENTS.md`'s plugin rules, re-read on
  2026-09-27.

### Owner answers (2026-09-27)

- Decision record written from the owner's dated answer to OWQ-16. Re-read for this step: OWQ-15 and OWQ-16, D007, D024 (safety
  waits), doc 38 §5.4, §6.1–§6.2, §9 and the AT-W1 and AT-W14 rows. Docs 22 and 38 were not edited; those edits are folding steps.

### Consistency review of the owner answers (2026-09-27)

- The decision record now links D043. D043 states rules 1–4 but not this file's "including Auto" reading of rule 3 or its open
  detail on telling user-authored definitions from third-party packs; both stay recorded here, and neither contradicts D043.
