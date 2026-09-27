# DG030: Open decisions on mod install hand-off, directory freshness, CC-BY-SA and the registry operator

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
> **Decision by: owner** (all four items). Blocks: the "missing mod" card's install route (doc 42 §7.2), the directory update
> process (MS2), the registry licence allowlist and RG1 (MS4).

## Context

Doc 42's review pass ("Still open after this pass") and open questions 8–9, with doc 34 OQ6, leave four owner decisions.

## The gap

Four choices in the mod-discovery and registry design have no decision and no default: whether the editor may launch the game so
the user can install a mod, how the offline directory stays current, whether CC-BY-SA-4.0 content may reach missions, and who runs
the pack registry. Each item below gives its context, options (lettered) and a proposal.

## Item 1: a user-clicked "Launch the game to install"

- **Context:** installing a PB mod happens in the game's MODS screen (doc 42 §3.3 hand-off). Doc 42 proposes `--private` on
  every Preview launch (§6.3, MAT12, pending a probe, OQ10); `--private` blanks the master server, so the MODS screen could not reach
  PB from a Preview launch.
- **Options:** (a) text instruction only ("install from the in-game MODS screen, then come back"); (b) a button that reuses Preview's
  launcher to start the game vanilla, without `--private` and without staging a mission, only on a click.
- **Proposal:** (b) for CWR and CE targets, labelled "Launch the game to install mods", never automatic, never with a mission or
  mod set other than vanilla; Plotroom rescans on focus as doc 42 §3.3 describes.

## Item 2: keeping the directory fresh between releases

- **Context:** the directory pack is regenerated at each editor release (doc 42 §4.2). Updating it through the registry would put
  third-party metadata in Plotroom's registry, against MG8.
- **Options:** (a) release cadence only; (b) registry-delivered directory updates; (c) release cadence, plus a live refresh through the
  Community catalog connector for users who enable it (DG028).
- **Proposal:** (c). Every row shows its snapshot date; no third-party metadata in the registry.

## Item 3: CC-BY-SA-4.0 in the licence allowlist (doc 42 OQ8)

- **Context:** content that can reach a user's mission must be CC0-1.0, MIT, Apache-2.0 or CC-BY-4.0 so exported missions stay
  shareable; editor-only content may use any GPL-3.0-compatible licence (doc 42 §5.2).
- **Options:** (a) allow CC-BY-SA-4.0 for mission-reaching content; (b) allow it only for editor-only content.
- **Proposal:** (b). Share-alike would bind users' exported missions to CC-BY-SA terms, which conflicts with "exported missions stay
  shareable" and needs its own analysis next to the game data's APL-SA (doc 02 §3). CC-BY-SA-4.0 is one-way compatible with GPLv3,
  so editor-only use fits [I; not legal advice].

## Item 4: registry operator (doc 42 OQ9; doc 34 OQ6)

- **Context:** doc 42 §5.3 proposes two or three maintainers with FIDO 2FA, CODEOWNERS per namespace, a forkable index and a public
  succession plan; doc 22 OQ1 asks whether an OFP community site could run it.
- **Options:** (a) the project's own GitHub organisation; (b) a community site; (c) no registry until MS4 is scheduled.
- **Proposal:** (c) now, then (a) when RG1 starts, with the doc 42 §5.3 governance. Namespace verification through OFPEC tags and
  third-party registries added by URL stay open (doc 42 OQ9).

## Options

Listed per item above: item 1 (a)–(b), item 2 (a)–(c), item 3 (a)–(b), item 4 (a)–(c).

## Recommended resolution (proposal)

1. Offer "Launch the game to install mods" on a click, vanilla, without `--private`, CWR and CE targets only.
2. Release-cadence directory plus the opt-in connector's live refresh; no third-party metadata in the registry.
3. CC-BY-SA-4.0 allowed for editor-only content, not for content that reaches missions.
4. No registry operator until MS4 is scheduled; then the project's own organisation with doc 42 §5.3 governance.

## What it would change

- Doc 42 §3.3, §4.2, §5.2, §5.3, §7.2, §8.1, OQ8, OQ9 and the review pass's "Still open" list; doc 34 OQ6; doc 22 OQ1.

## Affected docs

Docs 22, 34, 42; DG028, DG029.

## Decision record

Open (per item).

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 42 §3.3, §4.2, §5.2–§5.3, §6.3, the review pass "Still open after this pass", OQ8 and OQ9; doc 34 OQ6; doc 22
  OQ1, re-read on 2026-09-27. Licence remarks are not legal advice; doc 02 governs.
