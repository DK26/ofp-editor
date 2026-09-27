# D033: Sharing campaign extension overlays

> **Status:** accepted · **Decided by:** owner (OWQ-06) · **Decided:** 2026-09-27 · **Recorded:** 2026-09-27
> **Scope:** extension overlays (doc 34 cw13; doc 19 §7.6) that attach new nodes, branches and missions to a campaign the user did not
> make, and the export guard's rules for sharing them. **Refines:** D001 and D030 (their open part OWQ-06).
> **Related:** D003, D017, D035. **Open parts:** Bohemia's answer to the overlay question in the OWQ-10 letter (D035 item 2); how
> the share flow records a third-party parent's licence or permission (design detail).

## Context

- Doc 34 cw13: an extension sidecar references its parent campaign by id and content hash and adds only nodes and edges
  (`optional_branch`, `alternative`, `insert_before`, `post_campaign`). The build merges locally; in Preserve mode the parent's missions
  stay untouched (doc 19 §7.6). Whether "only the extension ships" is enough was marked unknown pending licensing.
- Bohemia's campaigns are game data under the APL-SA (doc 02 §3). Third-party campaigns carry their authors' terms, which are often
  unstated.
- Doc 34 mo10 (§4.4): at export, lint D9 compares every file with the files served by the base game and the mounted mods; for private
  use it warns and never blocks.

## Decision

1. **Bohemia's campaigns: yes, extension-only.** A user may share an extension overlay for a Bohemia campaign when only the extension
   sidecar and the user's own new missions ship. The recipient's build merges locally from the parent they have installed, matched by
   id and hash. For a shared overlay, the export guard **blocks** parent content from the package. The question is also put to Bohemia
   in the OWQ-10 letter.
2. **Third-party campaigns: only with permission.** An overlay for someone else's campaign may be shared only when the parent's licence
   allows derivative works, or when the parent author's permission is recorded with the overlay.
3. These rules govern only what is shared; making and playing an overlay on one's own machine is not restricted by this record.

## Alternatives considered

- Extension-only sharing for every parent (option a for all): community authors' wishes about derivative work vary and are rarely
  written down; a recorded permission respects them.
- Licence or permission for Bohemia's campaigns too (option b for all): the extension ships no Bohemia content and merges only with
  the player's own install, and the OWQ-10 letter asks Bohemia directly (not legal advice; doc 02 governs).
- Never (option c): blocks the natural way to extend classic campaigns while shipping nobody else's content.

## Consequences

- The overlay manifest records the parent's id and hash and, for a third-party parent, its licence or the permission record; the share
  flow does not package a third-party overlay without one (design detail: proposal).
- Lint D9 stays a warning for private use (doc 34 §4.4); only a shared overlay's package is blocked from carrying parent files.
- A recipient without the parent sees a card naming the required campaign, and the "Requires" badge lists the parent (D003; design
  detail: proposal).
- Doc 19 §7.6 and doc 34 cw13 drop the open licensing mark in the folding step (doc 34 §5.2 row 02).

## Sources

Doc 34 (cw13, mo10, §4.4, §5.2 row 02); doc 19 §7.6; doc 02 §3; `OWNER-QUESTIONS.md` OWQ-06 and OWQ-10; D001.
