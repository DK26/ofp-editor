# D001: Licence: GPL-3.0-or-later everywhere

> **Status:** accepted · **Decided by:** owner · **Decided:** 2026-09-26 · **Recorded:** 2026-09-27
> **Scope:** every crate, tool, skill, prompt pack and data file this repository ships. **Related:** D002, D013, D014, D017, D022.
> **Open parts:** owner questions OWQ-01 (generated-content permission wording), OWQ-02 (docs licence), OWQ-03 (plugin SDK),
> OWQ-04 (GPL-3.0-only ports) (OWQ-01 to OWQ-04 answered 2026-09-27 → D031), OWQ-05 (contribution terms; answered 2026-09-27 →
> D032), OWQ-06 (sharing campaign extension overlays; answered 2026-09-27 → D033); DG018 (port records).

## Context

- Plotroom re-creates the original editor's behaviour. The fastest faithful route is translating Bohemia's released editor C++
  (`UIArcade*`, `ArcadeTemplate*`) into Rust, which only a GPLv3-family licence permits (doc 02 TL;DR, §6.1).
- CWR and CWR-CE are `GPL-3.0-or-later` with Bohemia's GPLv3 §7 Additional Terms, which must travel with every propagation of
  derived code (doc 02 TL;DR). One licence keeps code flowing both ways with CWR-CE.
- Research proposed three permissive exceptions: a generic harness crate under `MIT OR Apache-2.0` (doc 02 §6.3), clean-room format
  crates under `MIT OR Apache-2.0` (doc 07 §15) and a permissive plugin SDK, WIT and test kit (doc 22 TL;DR).
- Mission makers mix Plotroom output with APL-SA game content and must stay free to license their missions (doc 02 §6.2).

## Decision

1. The whole workspace is `GPL-3.0-or-later`: format, editor, preview, harness and knowledge crates, tools, skills and prompt packs.
   There is **no permissive lane**.
2. `LICENSE` holds the unmodified GPLv3 text (present at the repository root). The change set that adds the first file derived from
   CWR or CWR-CE also adds `NOTICE` with Bohemia's header and §7 Additional Terms verbatim, scoped to this program, and the trademark
   disclaimer (doc 02 §10.1; README "License").
3. Ported files carry SPDX headers and a `Derived-From:` tag naming the pinned upstream path (doc 02 §10.2). Game data is never
   committed, bundled or converted and shipped (doc 02 TL;DR; `AGENTS.md` fixture rules).
4. Plotroom adds its own GPLv3 §7 **additional permission** so that content the program writes for its users (missions, scripts,
   `description.ext`, briefings, stringtables, campaign files, and template text copied into them) is not GPL-bound. The wording is the
   doc 02 §6.2 draft, pending owner review (OWQ-01) and a legal review before 1.0. Until it is in `NOTICE`, the README's promise
   ("meant to be yours") states the intent.
5. Every template, snippet, module lowering and example that the program copies into user output is original work, never translated
   from CWR or CWR-CE, because Plotroom cannot grant permissions over Bohemia's code (doc 02 §6.2 constraints).

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| Permissive harness crate (doc 02 §6.3) | The owner chose one licence. Cost: other projects cannot reuse the harness under MIT |
| Permissive clean-room format crates (doc 07 §15) | Same choice; spec-first writing stays the method (D017), only the licence differs |
| Clean-room everything under a permissive licence | Loses the direct port of editor behaviour and the two-way flow with CWR-CE |
| An IC-style plugin exception | A §7 permission over part of the Program leaves the whole under the GPL, and it cannot cover Bohemia's code (doc 22 §5) |

## Consequences

- `[workspace.package] license = "GPL-3.0-or-later"`; a `cargo-deny` allow-list as in doc 02 §10.3. GPL-2.0-only crates (HEMTT) can
  never be linked; permissive crates, MPL-2.0 and GPL-2.0-or-later (armake2) can.
- REUSE 3.3 headers, `reuse lint`, and the provenance and game-data CI gates of doc 02 §10.4 from the first code commit (proposal until
  CI exists).
- Apache-2.0 code (for example from Codex, doc 38 §1.3) may be ported with its licence, NOTICE and a port record; where such records live
  is DG018.
- T1 plugins distributed through Plotroom's registry must be GPL-3.0-compatible (doc 22 §5; D007).
- Model weights are separate data, never inside the release archive (doc 02 TL;DR; D023). CUDA runtime DLLs are never bundled with GPL
  builds (doc 13 TL;DR; D022).

## Sources

Doc 02 (TL;DR, §6, §7.1, §10, §11, open questions); doc 07 §15; doc 13 TL;DR; doc 22 TL;DR and §5; doc 34 row mo21; doc 38 §1.3;
README "License"; `LICENSE`.

## Amendment notes

### 2026-09-27: refined by D031, D032 and D033 (pointers)

The owner answered OWQ-01 to OWQ-06 on 2026-09-27. D031 settles the §7 permission (item 4 here: the doc 02 §6.2 draft plus an
explicit coverage list, with the legal review before 1.0 still open), the docs licence, the plugin SDK licence and GPL-3.0-only
ports; D032 the contribution terms; D033 the sharing of extension overlays. Item 4's "pending owner review (OWQ-01)" is answered by
D031 item 1. The header's **Open parts** gained pointers; nothing else above changed.
