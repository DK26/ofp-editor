# D034: Descriptor placement, clearance and rename, and delegated names

> **Status:** accepted · **Decided by:** owner (OWQ-07 = DG002 option A; OWQ-08) · **Decided:** 2026-09-27 · **Recorded:** 2026-09-27
> **Scope:** where the descriptor appears; the clearance search and the repository rename; how pending user-facing names are chosen.
> **Refines:** D002 (settles its open parts and replaces the list of surfaces in its item 1), and D011, D019 and D029 (how their
> OWQ-08 naming route is settled). **Related:** D014, D028, D035.
> **Open parts:** the clearance search itself (doc 02 §9 item 2); the names table's content (design round), reviewed by the owner
> before the first release.

## Context

- D002 settled the names. DG002 asked where the descriptor "Mission & Campaign Editor for Arma: Cold War Assault / Operation
  Flashpoint" may appear: doc 02 §9 item 1 keeps marks out of the product, repository, crate, binary, window-title, installer and icon
  names; item 4 allows nominative use in body text.
- `AGENTS.md` first paired the name with the descriptor in the window title and installer as well, which contradicted DG002's table
  (consistency review, 2026-09-27; D002 note).
- Research left user-facing names as placeholders (OWQ-08): the realism setting's levels, "Styles", "Economy mode", "Surprise me",
  "Seed Atlas", "Remix", "Event pacing", campaign modifiers such as "Thin roster", difficulty rungs, the rename of
  `DifficultyPreset::Veteran` (which clashes with the game's own Veteran mode) and "Community catalog".

## Decision

1. **The product name is Plotroom; the descriptor is a descriptive tagline** (DG002 option A). `AGENTS.md` "Naming and Trademarks" was
   amended to match and governs; this table restates it:

   | Place | "Plotroom" | Descriptor |
   | --- | --- | --- |
   | Window title; installer product and file name; application icon; repository, crate and binary names; config and sidecar directories | Yes | **No** |
   | README heading and tagline, splash screen, About box, website, release notes, store and forum listings, documentation headers | Yes | Yes, as plain text (no stylised marks or logos), with the non-affiliation disclaimer in the same place or one click away |
   | In-app body text (Preview labels, compatibility notes, target-profile badges) | As needed | Game names only to identify the game |

2. **Before the first release**, the clearance search (doc 02 §9 item 2) for Plotroom, Wilco, Plotline, the Tote and Teller is recorded
   in doc 02, and the repository is renamed away from `ofp-editor` (GitHub keeps redirects). The disclaimer and SPDX `<Product>`
   placeholders read "Plotroom".
3. **Pending names are delegated to the design round** (OWQ-08 a), as the owner did for Standing Orders and Drill (D028): pick the best
   names, clear each through the doc 02 §9 checklist, record them in **one names table**, and refactor later if needed. The owner
   reviews the table before the first release.

## Alternatives considered

- DG002 option B (the long form everywhere): conflicts with doc 02 §9 item 1 and Bohemia's §7 term.
- DG002 option C (no descriptor anywhere): players searching for the game would not find the tool.
- Keeping `AGENTS.md`'s first wording: puts third-party marks into the program's most visible identifiers.
- The owner naming each term (OWQ-08 b): slower, with no gain over a cleared table the owner reviews.

## Consequences

- Window-title and About-box code follow the table; the About box also carries the legal notices (doc 02 §10.6).
- Doc 39 §5.1's realism levels (Cinematic, Grounded, Doctrinal) are the starting candidates; `DifficultyPreset::Veteran` is renamed
  (doc 36 OQ5; doc 43 §3.6). Names stay placeholders in research docs until the table records them.
- Never "official", "remastered" or "endorsed" (doc 02 §9 item 5). The first public release also waits for D035's letter and reports.
- DG002 is decided; its decision-record section and D002's placement note point here (folding step).

## Sources

DG002; `AGENTS.md` "Naming and Trademarks"; doc 02 (§9–§11); doc 36 OQ5; doc 39 §5.1; doc 43 §3.6; `OWNER-QUESTIONS.md` OWQ-07 and
OWQ-08; D002; D028.

## Notes

- 2026-09-27 (consistency review): **Refines:** now also names D019 and D029, which cite OWQ-08 as the naming route and now point
  here (citation fix; no decision changed). DG037 (the "Director" names, still open) falls under item 3: the design round decides it.
