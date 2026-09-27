# DG028: Read-only catalog feeds and registry traffic

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **decided** (owner, 2026-09-27): user-enabled download and feed sources are allowed (model downloads such as Hugging Face; read-only community mod catalogs): off by default, blocked offline, integrity-checked, every download user-started. `AGENTS.md` amended accordingly.
> **Decision by: owner** (it changes which outbound destinations the product may contact, and `AGENTS.md`'s wording). Blocks: the
> Community catalog connector (doc 42 MS3) and registry phases RG1–RG2 (doc 42 MS4), which stay `proposal-only` until decided.

## Context

- **Doc 42 §3.3–§3.4**: the recommended mod discovery is an offline directory pack plus one opt-in, first-party, read-only
  "Community catalog" connector over the two community channels: PB (the game's MODS storage for CWR 3.05 and CE) and GS (the legacy
  Game Schedule). Both are plain HTTPS JSON; PB publishes an OpenAPI 3.1 file.
- **Doc 22 §2.3** makes Streamable-HTTP MCP "the only T2 transport"; **doc 22 OQ4** asks whether REST-only services get a
  host-mediated `net.fetch` or must use MCP.
- **Doc 42 §3.4**: a Plotroom-run MCP shim would add a Plotroom-operated host to the outbound path and a service to run. Proposal
  [I]: a narrow connector kind `feed`. "Blocked on an owner decision."
- **Doc 42 §5.1**, "Network rule gap": `AGENTS.md` names only the model provider and enabled plugins as outbound destinations;
  registry traffic from the pack manager is neither. Proposed gate: the registry is a source the user enables (origin shown and
  reviewed like a T2 origin, off until enabled, blocked in offline mode); pack files are fetched only from forge origins allowlisted
  by the signed index and checked against `pack_hash` before unpacking. "The §3.4 design-gap request should cover this too."
- **Doc 42 OQ3**: "Feed connector kind or MCP only? An owner decision."

## The gap

Two kinds of outbound traffic have no place in the current rules: a read-only catalog lookup that is not MCP, and the pack
manager's registry fetches, which are neither model-provider nor plugin traffic.

## Options

**Catalog lookups**

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | MCP only; the channels or someone else must run an MCP server | No new connector kind | Neither channel offers one; a Plotroom-run shim adds a host and a service to operate |
| B | A narrow `feed` connector kind: GET-only; pinned or user-typed HTTPS origin; fixed host-owned response schema (`papa-bear-v1`, `game-schedule-api-1`); enum filters only (no model-written parameters, no mission data); no secrets; no binary or download routes; doc 22's caps, egress card and egress log | Minimal surface; testable against a stub (doc 42 MAT9) | A second T2 transport to maintain |
| C | A general host-mediated `net.fetch` for plugins (doc 22 OQ4) | Covers REST-only TTS or translation too | Much wider surface; not needed for this use |
| D | No live lookup; the offline directory only | No network at all | Directory goes stale between releases (DG030) |

**Registry traffic**

| # | Option | For | Against |
| --- | --- | --- | --- |
| R1 | Registry as a user-enabled, reviewed source (doc 42 §5.1 gate) and `AGENTS.md` amended to name it | Explicit, off by default, blocked offline | An `AGENTS.md` change |
| R2 | File-only pack installs; no registry networking | No new destination | Loses discoverability and signed updates |

## Recommended resolution (proposal)

Option B plus R1. Add the `feed` kind to doc 22 as a T2 variant with the limits listed in option B and doc 42 §3.3 (allowlist checked
on the final request path, ids percent-encoded as one path segment, no redirects off the origin, response size and depth caps,
timeouts, schema validation). Treat the pack registry as a user-enabled source with the doc 42 §5.1 gate. Amend `AGENTS.md`'s
outbound sentence to: "…to the model provider the user configured, to the services of plugins and connectors the user has enabled,
and to package sources the user has enabled in the pack manager." The agent itself still never initiates registry traffic.

## What it would change

- `AGENTS.md` "No general system access" outbound sentence (owner edit).
- Doc 22 §2.3 (transports), §3.2 (network control), OQ4 (answered for feeds; `net.fetch` stays open).
- Doc 42 §3.4, §5.1, MS3–MS4 and OQ3: unblocked by pointer.

## Affected docs

`AGENTS.md`; docs 22, 42.

## Decision record

- **Decided:** 2026-09-27. **By:** the owner. **Chosen:** option B (the `feed` connector kind) plus R1 (the registry as a user-enabled,
  reviewed source), with a broader outbound rule than the proposal's wording. The durable rule is recorded as
  [D008](../decisions/D008-outbound-network-sources.md), which this section summarises.
- **Rule.**
  1. Outbound traffic goes only to the model provider the user configured, the declared endpoints of plugins and connectors the user
     enabled, and **download or feed sources the user explicitly enabled**: for example model downloads from Hugging Face, read-only
     community mod catalogs, and Plotroom's pack registry once it exists.
  2. Every such source is **off by default**, **blocked in offline mode**, **integrity-checked** (pinned revisions and hashes), and
     every download is **started by the user, never by the agent**.
  3. Catalog lookups use the narrow T2 **`feed`** kind with the limits of option B and doc 42 §3.3 (GET-only; pinned or user-typed
     HTTPS origin; fixed host-owned response schema; enum filters only; no secrets; no binary or download routes; allowlist checked on
     the final request path; ids percent-encoded as one path segment; no redirects off the origin; size, depth and time caps; schema
     validation; doc 22's caps, egress card and egress log).
  4. The pack registry's origin is shown and reviewed like a T2 origin; pack files come only from origins the signed index allowlists
     and are checked against the pack hash before unpacking (doc 42 §5.1).
  5. Not adopted: a general host-mediated `net.fetch` for plugins (option C; doc 22 OQ4). Unchanged: the editor never fetches web or
     pricing pages (doc 40 R1) and never downloads mod files (D030).
- **`AGENTS.md`.** "No general system access" was amended by the owner to state rules 1 and 2. Its wording is the owner's, not the
  sentence proposed above: it names download and feed sources in general rather than only package sources in the pack manager.
- **Reason.** Neither channel runs an MCP server, and a Plotroom-run shim would add a host and a service to operate (option A); a
  general `net.fetch` is a much wider surface than the use needs (option C); an offline-only directory goes stale between releases
  (option D, DG030 item 2); file-only pack installs lose discoverability and signed updates (R2).
- **Still open.** The Community catalog connector also waits for the channel maintainers' non-objection and answers (DG029).
- **Folding (what moves this request to `folded`).** Doc 22 §2.3 (transports), §3.2 (network control) and OQ4 (answered for feeds;
  `net.fetch` not adopted); doc 42 §3.4, §5.1, MS3–MS4 and OQ3, unblocked by pointer. `AGENTS.md` is already amended.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 42 §3.3, §3.4 (with its manifest sketch), §5.1, §8.1, §8.3 and OQ3, doc 22 §2.3, §3.2 and OQ4, and `AGENTS.md`
  "No general system access", re-read on 2026-09-27. The file name follows doc 42 §3.4's suggestion.

### Owner answers (2026-09-27)

- The header said **decided** while the decision record still read "Open" (found by the consistency review). The record is now
  filled from D008 and `AGENTS.md` "No general system access", both re-read for this step; no decision changed. Docs 22 and 42 were
  not edited.
- The owner's local-runtime decision of the same day (llama.cpp's `llama-server` as a managed sidecar, with GGUF files pulled from
  Hugging Face at a pinned revision and checked by SHA-256; doc 46) is a user-enabled download source under rules 1–2 above and needs
  no change here.
