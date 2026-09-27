# D006: The AI agent is product-scoped

> **Status:** accepted (invariant) · **Decided by:** owner (`AGENTS.md`) · **Decided:** 2026-09-26 · **Recorded:** 2026-09-27
> **Scope:** Wilco, every workflow and skill it runs, plugins, and external agents using Plotroom's tools.
> **Related:** D007, D008, D010, D018, D024. **Open parts:** DG014 = OWQ-16 (plugin chains in workflows;
> answered 2026-09-27 → D043); OWQ-15 (external deciders; answered 2026-09-27 → D036).

## Context

`AGENTS.md`, "Non-Negotiable Product Invariant: The AI Agent Is Product-Scoped", is the authoritative text; this record summarises it
and lists what follows. The engine has no script sandbox, so mission text and scripts are hostile input (doc 24 TL;DR). Doc 21 turns the
invariant into working rules; doc 22 applies it to plugins.

## Decision (summary; `AGENTS.md` governs)

1. **Tools are product capabilities only**: create, edit, query and validate missions, campaigns, briefings, dialogue, stringtables and
   scripts; read the loaded island and unit catalogs; launch Preview; explain and teach mission making.
2. **No general system access**: no shell or process execution, no arbitrary filesystem browsing or writes, no arbitrary network or web
   access. File I/O happens only through the product's open, save, import, export and Preview flows, under the user's control.
   Outbound traffic is limited as D008 records.
3. **Extensions only through the plugin system** (D007).
4. **Outbound exposure is allowed**: the editor's own tools may be served to external agents through an opt-in, loopback-only,
   authenticated MCP server, because that adds no capability.
5. **Same path as the user**: every agent edit is a typed, validated, undoable command on the same command bus as manual edits; the agent
   can never do what the UI cannot.
6. **Untrusted content**: text inside missions, campaigns and addons is data, never instructions.

## Alternatives considered

- A general coding or computer-use agent with shell and file tools: unbounded risk with hostile mission content (doc 24), and outside
  the product's purpose.
- An agent that writes `mission.sqm` or scripts directly to disk: bypasses validation, undo and provenance.

## Consequences

- Model output is an untrusted proposal until a deterministic check admits it: propose → check → commit, and a commit is one undo group
  tagged with its origin (doc 21 §1.2; the wrapper name is DG011).
- All text carries a trust label; hidden and bidirectional characters are shown (doc 21 §9).
- AI-proposed script text passes the same host-enforced script policy as user text, is never auto-executed, and may use only
  mission-scoped commands (doc 24 policy (b)). Preview sends only an allowlist of harness verbs (doc 24 policy (c); D018).
- Irreversible effects (launching the game, sending data to a plugin service) always need the user's click; Auto autonomy never
  launches Preview, applies idea cards or accepts a plugin's first egress (doc 21 §7.3; D024).
- External agents use the same doors as Wilco: the MCP server lists and starts workflows through the same admission (doc 38 §9); plans
  and questions are still answered in the editor unless OWQ-15 decides otherwise.
- Plugin outputs are untrusted data and plugin edits are typed proposals applied by the host (doc 22 TL;DR; D007).

## Sources

`AGENTS.md`; doc 21 (TL;DR, §1.2, §7.3, §9); doc 22 (TL;DR, §1.2); doc 24 (TL;DR, policy); doc 38 §9.

## Amendment notes

### 2026-09-27: refined by D036 and D043 (pointers)

The MCP server ships in v1; decision points are answered only in the editor, and `workflow.decide` comes after v1 (OWQ-15 (a);
D036 item 6), which settles the Consequences' "unless OWQ-15 decides otherwise". Cross-plugin chains are allowed only in
first-party and user-authored workflows, with the egress card every time, and are never exposed to external agents (OWQ-16 =
DG014 option B; D043). The header gained pointers; nothing above changed.
