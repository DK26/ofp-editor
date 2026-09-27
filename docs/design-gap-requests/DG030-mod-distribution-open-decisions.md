# DG030: Open decisions on mod install hand-off, directory freshness, CC-BY-SA and the registry operator

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **decided** (owner,
> 2026-09-27, OWQ-17): all four proposals as written (items 1 (b), 2 (c), 3 (b), 4 (c) then (a)). Not yet folded.
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

- **Decided:** 2026-09-27. **By:** the owner, answering OWQ-17 in
  [`docs/decisions/OWNER-QUESTIONS.md`](../decisions/OWNER-QUESTIONS.md): "All four DG030 proposals as written." **Chosen:** the
  proposal of each item. **Decision record:** [D038](../decisions/D038-mod-handling-owner-additions.md) items 1–4 state the rule
  going forward (item 5 adds OWQ-18) and refine D030, D007 and D008.

| Item | Chosen | Decision |
| --- | --- | --- |
| 1. Install hand-off | (b) | A button labelled "Launch the game to install mods" reuses Preview's launcher to start the game **vanilla**, **without `--private`** and **without staging a mission**, only when the user clicks it, for CWR and CE targets only. It is never automatic and never uses a mod set other than vanilla. Plotroom rescans on root changes or window focus (doc 42 §3.3) |
| 2. Directory freshness | (c) | The directory pack is regenerated at each editor release; users who enable the Community catalog connector (D008) also get its live refresh. Every row shows its snapshot date. No third-party metadata enters Plotroom's registry (MG8) |
| 3. CC-BY-SA-4.0 | (b) | Allowed only for editor-only content. Content that can reach a user's mission stays CC0-1.0, MIT, Apache-2.0 or CC-BY-4.0 (doc 42 §5.2) |
| 4. Registry operator | (c), then (a) | No registry operator until the registry (doc 42 MS4, RG1) is scheduled; then the project's own GitHub organisation with doc 42 §5.3's governance (two or three maintainers with FIDO 2FA, CODEOWNERS per namespace, a forkable index, a public succession plan) |

- **Reason.** Item 1 shortens the trip to the game's MODS screen (the "missing mod" card's install route, doc 42 §7.2) while Plotroom
  never installs mods itself (D030 item 5) and never launches the game on its own. Item 2 keeps the offline default current while honouring MG8. Item 3 keeps exported missions shareable instead
  of binding them to share-alike terms next to the game data's APL-SA (doc 02 §3) [I; not legal advice]. Item 4 avoids running an
  operator before there is anything to operate.
- **Still open.** Item 1's launch uses the Preview launcher, whose `--private` default still waits for its probe (doc 42 §6.3, MAT12,
  OQ10); the install launch omits `--private` either way. Item 2's live refresh also waits for the channel maintainers (DG029). Item 4:
  namespace verification through OFPEC tags and third-party registries added by URL stay open (doc 42 OQ9).
- **Folding (what moves this request to `folded`).** Doc 42 §3.3, §4.2, §5.2, §5.3, §7.2, §8.1, OQ8, OQ9 and the review pass's
  "Still open" list; doc 34 OQ6 (registry operator); doc 22 OQ1; D030's open part for DG030 (and its CC-BY-SA consequence line) under
  the decision-record rules (done 2026-09-27: D030's, D007's and D008's headers and notes point to D038).

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 42 §3.3, §4.2, §5.2–§5.3, §6.3, the review pass "Still open after this pass", OQ8 and OQ9; doc 34 OQ6; doc 22
  OQ1, re-read on 2026-09-27. Licence remarks are not legal advice; doc 02 governs.

### Owner answers (2026-09-27)

- Decision record written from the owner's dated answer to OWQ-17. Re-read for this step: OWQ-17, D008, D030 and doc 42's review pass
  "Still open after this pass". Docs 22, 34 and 42 were not edited; those edits are folding steps.

### Consistency review of the owner answers (2026-09-27)

- The decision record now links D038, which states the same four items (and OWQ-18 as its item 5). The decision records point to
  D038; docs 22, 34 and 42 are still to be folded, so the request stays `decided`.
