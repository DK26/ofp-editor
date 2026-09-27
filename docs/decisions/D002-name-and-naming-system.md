# D002: Product name, descriptor and naming system

> **Status:** accepted (names); placement open → placement accepted (2026-09-27; see D034) · **Decided by:** owner
> **Decided:** 2026-09-27 · **Recorded:** 2026-09-27
> **Scope:** product, persona and feature names; identifiers in code and files. **Related:** D001, D028, D029.
> **Open parts:** DG002 (where the descriptor may appear, clearance search, repository rename) = OWQ-07 (answered 2026-09-27 → D034; the
> clearance search and the rename are still to be done); pending names = OWQ-08 (answered 2026-09-27 → D034).

## Context

- Doc 02 §9: the product name, crates, binary, window title, installer and icon must not contain "Arma", "OFP", "Flashpoint",
  "Cold War Assault", "Cold War Crisis", "Poseidon", "Bohemia" or island names; the game is named only nominatively in body text;
  Bohemia's §7 terms forbid distributing a modification "using" its marks.
- Players must still recognise the tool as the editor for this game, so the name needs a plain descriptive companion.
- Research docs used working names: the repository `ofp-editor`, `ofp-*` crates, `ofp-agent`, `ofp-mcp`, sidecar spellings such as
  `ofp-editor.meta.toml` and `.ofpeditor/` (doc 45 OQ1), and generic feature terms ("campaign graph", "state panel", "language service").

## Decision

1. The product is **Plotroom**. Its descriptor is "Mission & Campaign Editor for Arma: Cold War Assault / Operation Flashpoint".
   User-facing surfaces (README, window title, splash, About box, installer, listings) pair the name with the descriptor and show the
   non-affiliation disclaimer from `README.md` (`AGENTS.md`, "Naming and Trademarks").
2. Crates and binaries use the `plotroom` prefix (for example `plotroom-core`). Third-party marks (Arma, Operation Flashpoint, OFP,
   Cold War Assault/Crisis, Resistance, Poseidon, Bohemia) and the game's island names never appear in crate, binary, module,
   file-format, sidecar-file or generated-header names.
3. The naming system:

   | Name | What it names | Where it is designed |
   | --- | --- | --- |
   | **Wilco** | The optional AI co-pilot; default persona an era signals officer | doc 21 §11.7 |
   | **Plotline** | The campaign graph: Flow and Theatre views over the typed `CampaignModel` | doc 19 §6 |
   | **the Tote** | The state board: declared campaign variables, roster and pools, with "set in / read in" | doc 19 §4, §6 |
   | **Teller** | The language service: catalog, checker, diagnostics, completions and lookups | doc 23; doc 30 §4 (L2–L3) |
   | Standing Orders, Drill | Concept manual and live tutorials | D028 |

4. Working names in research docs are superseded when code lands: `ofp-*` crates become `plotroom-*`, `ofp-mcp` becomes Plotroom's MCP
   server, and sidecar files use `plotroom` spellings. The exact names are set in `CODE-INDEX.md` by the change set that creates them.

## Alternatives considered

- The long form as the product name everywhere (DG002 option B): conflicts with doc 02 §9 item 1 and Bohemia's §7 term.
- "Plotroom" with no descriptor (DG002 option C): players searching for the game would not find the tool.
- Doc 02 §9's example names (Sitrep, Fireteam Studio, Waypoint Studio) were illustrations only and were never checked.
- Generic feature terms only: harder to talk about, search and teach; the owner wanted a coherent system.

## Consequences

- The repository is still named `ofp-editor`. A rename before the first release is proposed in DG002 (open, OWQ-07).
- Which surfaces carry the descriptor (window title, installer, About box) is DG002's open placement rule; the README already follows its
  option A.
- Plotroom and each system name get a recorded clearance search (doc 02 §9 item 2) before the first release. Any further user-facing
  name clears the doc 02 §9 checklist before its UI string is written (doc 33 §2 item 9).
- Generic terms stay valid in prose ("Plotline, the campaign graph"); research docs adopt the names as they are revised.
- Never "official", "remastered" or "endorsed" (doc 02 §9 item 5).

## Sources

`AGENTS.md` "Naming and Trademarks"; README; doc 02 §9–§11; DG002; doc 07 OQ8; doc 19 TL;DR and §4–§6; doc 21 §11.7 and its
verification notes; doc 23 TL;DR; doc 30 TL;DR; doc 33 §2 item 9; doc 45 OQ1.

## Notes

- 2026-09-27 (consistency review): item 1 restates `AGENTS.md`, which names the window title, splash, About box and installer among
  the surfaces that carry the descriptor; the Consequences line calls that placement open because DG002's recommendation differs.
  This record does not decide between them; the conflict is recorded under OWQ-07, and `AGENTS.md` governs until the owner answers.
- 2026-09-27 (owner answers; pointers): OWQ-07 was answered with DG002 option A, and `AGENTS.md` "Naming and Trademarks" was
  amended to match. D034 now governs placement: item 1's list of surfaces is replaced by D034 item 1 (the window title and the
  installer carry "Plotroom" alone), and the Consequences lines that call the placement and the rename open are answered there; the
  clearance search and the rename remain actions before the first release. Pending names follow D034 item 3 (OWQ-08). The note
  above is resolved. The header gained pointers; nothing else above changed.
