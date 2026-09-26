# Plotroom

**Mission & Campaign Editor for Arma: Cold War Assault / Operation Flashpoint**

> **Status: early design.** There is no code yet. The research and design work lives in
> [`docs/`](docs/research/); contributor and coding-agent rules are in [`AGENTS.md`](AGENTS.md).

Plotroom is a standalone, open-source re-creation of the classic 2001 mission editor: the same
top-down map, the same F1–F6 editing modes, the same dialogs. It runs on its own, in a window or
full screen, and launches the real game when you press **Preview**. On top of that faithful core
it aims to make everything the community loves easy instead of hacky, and to make whole
campaigns a first-class thing you can design, not just a folder of missions.

## What it is meant to become

- **A faithful editor.** Visually and behaviourally true to the original, with modern safety nets
  underneath: undo, non-blocking validation, and integrated script and briefing editing.
- **Preview in the real game.** One click stages your mission and launches Arma: Cold War Assault
  (Remastered / CWR-CE), with an export-and-launch path for older installs.
- **Campaigns as a first-class citizen.** Persistent squad members who can die, resources, weapon
  pools, reputation and branching mission trees, compiled down to what the unmodified game can
  run. Our north star: someone builds an XCOM-like campaign (real-time, not turn-based) with it.
- **No-code first, scripting always available.** Attributes, ready-made modules for popular
  community patterns, a "when / if / do" rule builder, and a cinematics timeline for camera
  shots and cutscenes, all compiling to readable SQS/SQF that you can inspect and edit. For
  scripters: a mission-aware language service with completions, diagnostics and quick-fixes.
- **A Field Manual and live tutorials.** Every cryptic concept (Game Logic, synchronisation,
  "Guarded by", presence conditions, …) explained plainly, with small demos and learn-by-doing
  exercises checked by the editor itself.
- **Addons and mods handled properly.** Mod sets, catalogs that show which mod every unit comes
  from, and mission dependencies derived automatically.
- **Wilco, an optional AI co-pilot.** Off by default. Bring your own model, cloud or local. It can
  only do what you can do in the editor, through the same undoable commands; it has no shell,
  file or web access; and everything it makes is visible, inspectable and editable. You can
  describe a whole campaign and then refine any part of it. It is designed so that small local
  models can succeed, too.
- **Extensible.** Styles and knowledge as standard `SKILL.md` skills, and a sandboxed,
  product-scoped plugin system.

## What you need

Your own copy of the game (Steam or GOG). Plotroom reads game data from your installation at
runtime and never ships or redistributes it.

## License

Plotroom is free software under the **GNU General Public License v3.0 or later**; see
[`LICENSE`](LICENSE). Code derived from Bohemia Interactive's released Arma: Cold War Assault
source will carry Bohemia's GPLv3 section 7 additional terms, which will be reproduced in a
`NOTICE` file when such code is added. Missions and campaigns you make with Plotroom are meant to
be yours under terms of your choice; a GPLv3 section 7 permission to that effect is being drafted.

## Disclaimer

Plotroom is an independent, community-made tool. It is not affiliated with, endorsed by, or
authorized by Bohemia Interactive a.s. or Electronic Arts Inc. ARMA and Bohemia Interactive are
trademarks or registered trademarks of Bohemia Interactive a.s. OPERATION FLASHPOINT is a
registered trademark of Electronic Arts Inc. These names are used only to identify the game this
tool is designed to work with. Plotroom is being built with reference to, and will include code
derived from, the Arma: Cold War Assault source code that Bohemia Interactive released under
GPL-3.0-or-later with additional terms; such a modified version is not the original program.
Game data is not included and is licensed by Bohemia Interactive under the APL-SA.
