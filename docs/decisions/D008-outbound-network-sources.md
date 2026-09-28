# D008: Outbound network: provider, enabled plugins and user-enabled sources

> **Status:** accepted · **Decided by:** owner (DG028) · **Decided:** 2026-09-27 · **Recorded:** 2026-09-27
> **Scope:** every network request the product makes. **Related:** D006, D007, D022, D026, D030.
> **Open parts:** DG029 = OWQ-12 (channel maintainers' answers; the rule answered 2026-09-27 → D035, the answers not yet in);
> DG030 item 2 = OWQ-17 (directory freshness; answered 2026-09-27 → D038).

## Context

`AGENTS.md` first named only the configured model provider and the endpoints of enabled plugins as outbound destinations. DG028 found
three kinds of traffic with no place in that rule: read-only catalog lookups on community mod channels that are plain HTTPS JSON, not MCP
(doc 42 §3.3–§3.4); registry fetches by the pack manager (doc 42 §5.1); and model downloads for local inference (doc 13 TL;DR).

## Decision

1. The product's outbound traffic goes only to: the **model provider** the user configured; the **declared endpoints of plugins and
   connectors** the user enabled; and **download or feed sources the user explicitly enabled**, for example model downloads from
   Hugging Face, read-only community mod catalogs, and Plotroom's pack registry once it exists. `AGENTS.md` states this rule.
2. Every such source is **off by default**, **blocked in offline mode**, **integrity-checked** (pinned revisions and hashes), and every
   download is **started by the user, never by the agent**.
3. Catalog lookups use a narrow T2 connector kind, **`feed`** (DG028 option B): GET-only; a pinned or user-typed HTTPS origin; a fixed,
   host-owned response schema; enum filters only (no model-written parameters, no mission data); no secrets; no binary or download
   routes; doc 22's caps, egress card and egress log; the allowlist checked on the final request path; ids percent-encoded as one path
   segment; no redirects off the origin; response size, depth and time caps; schema validation.
4. The pack registry is a user-enabled source (DG028 option R1): its origin is shown and reviewed like a T2 origin; pack files are
   fetched only from origins the signed index allowlists and are checked against the pack hash before unpacking (doc 42 §5.1).
5. Unchanged: the editor never fetches web pages or pricing pages (doc 40 R1) and never downloads mod files (D030). A general
   host-mediated `net.fetch` for plugins (doc 22 OQ4) is not adopted.

## Alternatives considered

| Option (DG028) | Why not chosen |
| --- | --- |
| MCP only for catalogs | Neither channel runs an MCP server; a Plotroom-run shim adds a host and a service to operate |
| General `net.fetch` for plugins | Much wider surface than the use needs |
| No live lookups, offline directory only | The directory goes stale between releases |
| File-only pack installs | Loses discoverability and signed updates |

## Consequences

- Doc 22 (§2.3 transports, §3.2 network control) and doc 42 (§3.4, §5.1, MS3–MS4, OQ3) are unblocked by pointer when folded. The
  Community catalog connector still waits for the channel maintainers (DG029).
- The Model Manager's downloads (D022) and the pack manager follow rules 2 and 4. Showing each enabled source with its origin in one
  settings list is a proposal.
- Tests (proposal): a stub server per source (doc 42 MAT9), offline-mode refusal, hash-mismatch refusal, redirect-off-origin refusal,
  and a check that no agent tool can start a download.

## Sources

DG028; `AGENTS.md` ("No general system access"); doc 13 TL;DR; doc 22 (§2.3, §3.1–§3.2, OQ4); doc 40 R1; doc 42 (§3.3–§3.5, §5.1,
§8.3 row 22, OQ3).

## Amendment notes

### 2026-09-27: refined by D035 and D038 (pointers)

The owner or a named maintainer asks each channel, and non-objection is a written reply that does not object, or no objection 30
days after an acknowledging reply (OWQ-12 = DG029 option A; D035 item 4); the Community catalog connector still waits for those
answers. The directory is refreshed at each release, plus the opt-in connector's live refresh, and no third-party metadata enters
the registry (DG030 item 2; D038 item 2). The header gained pointers; nothing above changed.

### 2026-09-28: item 1 read for aggregators by D053 (pointer)

A note under lifecycle item 5; [D053](D053-aggregator-downstream-hosts.md) governs (DG039 option B), decided under the owner's
delegation; the owner may overrule it on return. For an aggregator, "the model provider the user configured" (item 1; `AGENTS.md`)
is read as the aggregator together with the hosts shown and accepted at setup: the hosts of the setup's pinned route and of the user's
per-key allow-list, named on the connect card before any call. A response from any other host, or with no served host reported, is
flagged, never admitted, and pauses the setup. `AGENTS.md` is unchanged (DG039 option C not adopted). The header has no open part to
mark; nothing above changed.
