# D043: Cross-plugin chaining in workflows

> **Status:** accepted · **Decided by:** owner (OWQ-16 = DG014 option B) · **Decided:** 2026-09-27 · **Recorded:** 2026-09-27
> **Scope:** workflows whose steps use tools of plugins from more than one publisher: third-party pack workflows, first-party
> workflows and user-authored workflows. **Refines:** D007, D006 and D025 (their open part DG014 = OWQ-16). **Related:** D008,
> D036.
> **Open parts:** how users author workflow definitions (no Wilco tool writes definitions, doc 38 §2).

## Context

- Doc 22 §3.2, "No widening": only the agent chains tools, and each call obeys the called plugin's grant. A workflow is a fixed chain,
  so a pack could route plugin A's untrusted output to plugin B's service without the user or a model deciding each send (DG014).
- The egress card appears the first time a plugin sends mission data, and every time for an agent-initiated send while untrusted text
  is in context (doc 22 §3.1; D007 item 3). Plugin outputs are untrusted data (`AGENTS.md`).

## Decision

1. **Third-party pack workflows stay single-publisher.** Load-time validation refuses a third-party pack workflow whose `requires`
   names a plugin of another publisher.
2. **First-party and user-authored workflows may chain plugins** from different publishers.
3. **The egress card shows every time** a step sends a value derived from another plugin's output, naming both plugins and the
   payload.
4. **Such chains are never exposed to external agents** over Plotroom's MCP server.

## Alternatives considered

- Forbid every cross-publisher chain (DG014 A): blocks useful pipelines, such as translating with one service and voicing with
  another.
- Allow any pack, with an install-review line and per-send cards (DG014 C): a malicious pack could pair a scraping plugin with an
  exfiltrating one, and review fatigue sets in.

## Consequences

- Doc 22 §3.2 and §4.2 gain the publisher rule for `requires`; doc 38 §6.1–§6.2 gain the load-time refusal and its fixtures (AT-W1,
  AT-W14); doc 38 OQ13 is answered (folding step).
- A chain adds no capability that either plugin lacks: each call still obeys its own plugin's grant (D007).
- `AGENTS.md`'s plugin rules need no change (DG014).
- The MCP server in v1 (D036 item 6) already leaves out workflows that use T2 plugin tools (doc 38 §9).

## Sources

DG014; doc 22 (§3.1–§3.2, §4.2); doc 38 (§2, §6.1–§6.2, §9, OQ13); `OWNER-QUESTIONS.md` OWQ-16; D007; `AGENTS.md`.

## Notes

- 2026-09-27 (consistency review): **Refines:** now also names D006 and D025, whose headers listed DG014 = OWQ-16 as an open part
  and now point here (citation fix; no decision changed). DG014's decision record adds two readings this record leaves implicit: the
  egress card shows every time at every autonomy level, including Auto, and how the host tells a user-authored definition from an
  installed third-party pack is still open (doc 38 §6.1).
