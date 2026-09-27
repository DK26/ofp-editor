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

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 42 §3.3, §3.4 (with its manifest sketch), §5.1, §8.1, §8.3 and OQ3, doc 22 §2.3, §3.2 and OQ4, and `AGENTS.md`
  "No general system access", re-read on 2026-09-27. The file name follows doc 42 §3.4's suggestion.
