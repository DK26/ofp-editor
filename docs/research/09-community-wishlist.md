# Community Wishlist: What OFP/CWA Mission Makers Love, Miss and Want

Research date: 2026-09-26. Assignment: community wishlist for the standalone Rust re-implementation of
the *Arma: Cold War Assault* (CWA; originally *Operation Flashpoint: Cold War Crisis*, 2001) mission
editor, including how the community is likely to receive built-in AI features.

## TL;DR

- **The editor is loved for being simple, fast and versatile.** In the 800 most recent English Steam
  reviews of CWA (app 65790, now the Remastered listing; fetched 2026-09-26; the window reaches back to
  2021-07), 34 mention "editor"; 33 of those are positive reviews
  ("Map editor is simple to use", "extremely easy to use yet very versatile mission editor"). Keep the
  map-first F1-F6 workflow, the original dialogs and the Easy/Advanced split exactly as they are (§2, §3).
- **Top verified pain points:** no undo; opaque or blocking script-error handling (CWR-CE #234, #185);
  everything past unit placement lives in hand-edited external files (description.ext, briefing.html,
  scripts, sounds); stale or implicit addon dependencies; hidden objects need third-party "Editor Update"
  addons; no precise height placement; engine limits (63 groups per side, 12 units per group) found late;
  weak documentation and discoverability (§4).
- **The community's strongest tooling value is "no dependencies for players".** 3den Enhanced (398,738
  subscribers) is built around it, and in 2009 Arma 2 mission makers said they could not use an
  editor addon if players would then need it. Our output must be plain mission files that vanilla CWA
  can load (§3, M10).
- **The most-wanted additions are:** undo/redo, a non-blocking validation/lint panel, integrated script
  and briefing editing with a command reference that matches CWA exactly, an addon dependency manager,
  an entity list with search, multi-edit, compositions/layers/comments, preview variants, and
  direct-open/CLI with autosave (§8, "Should add").
- **The pain is current:** CWR-CE issues filed June-August 2026 ask for direct editor launch (#35),
  save/autosave during preview (#166), editor loading as permissive as the MP loader (#185), a fix for
  the modal error lockup (#234) and higher group limits (#136).
- **3D and real-time editing are wanted, but as an add-on.** Faguss's Mission Editor 3D and
  Set-Pos-In-Game, Zeus Enhanced (739,089 subscribers) and MCC (243,521) show the demand. Arma 2's
  hidden 3D editor was called "very confusing". So 3D is a later Could, never a replacement for the 2D map (§5).
- **AI sentiment is mixed.** The community accepts AI as an assistant when a human stays the author:
  CWR-CE says "AI-assisted contributions are welcome" but bans AI boilerplate, AI bots run against the
  repo, and AI mentions in commit metadata. AI is also
  welcome as an idea generator. The community is hostile to undisclosed AI content, to voice cloning
  without consent, and to hallucinated SQF. DCO GPT, an in-game LLM mod whose hosts need an API key
  and a node.js setup, has only about 1.2k subscribers (§7).
- **Recommendation:** position AI as an optional, bring-your-own-model co-pilot. Every AI action should
  be an undoable diff that passes the same validator as a human edit. Dialogue should be text first,
  with no voice cloning and an optional disclosure sidecar. The editor must work 100% offline without
  any model (§7.3, WN1, WN2, WN6).
- **Backlog (§8):** 13 Must keep (M), 18 Should add (S), 14 Could add (CO), 8 Won't (WN). Each item
  cites its source.
- **Gaps:** Reddit, the OFP/CWA Discord and most Bohemia forum threads were not reachable from this
  environment (§1.2). Run a short community survey before locking priorities (Open questions).

## 1. Scope, method and terms

### 1.1 Terms (for readers of this file alone)

| Term | Meaning |
| --- | --- |
| OFP / CWC / CWA | Operation Flashpoint: Cold War Crisis (2001), renamed Arma: Cold War Assault (2011, v1.99). |
| CWR | "Arma: Cold War Assault Remastered". Bohemia published its engine source (codename Poseidon) as `BohemiaInteractive/CWR`, GPL-3.0-or-later. The remaster was released in July 2026: GamingOnLinux (article dated 2026-07-20) gives 16 July 2026 (fetch summary); an earlier search result gave 2026-07-17 and Bohemia's "Out Now" blog date (2026-07-29) could not be re-fetched (unverified). On Steam the remaster replaced CWA under the same app ID: app 65790 is now listed as "Arma: Cold War Assault Remastered" (store search API, 2026-09-26). |
| CWR-CE | `ofpisnotdead-com/CWR-CE`, the community continuation of CWR, with an active issue tracker. |
| 2D editor | The original in-game map editor (in the code: "Arcade" map, `DisplayArcadeMap`). ArmA 1 and Arma 2 used close descendants. |
| Eden (3DEN) | Arma 3's 3D scenario editor (2016). It replaced the 2D editor. |
| Zeus / Game Master | Real-time "game master" editing during play (Arma 3 / Arma Reforger). |
| mission.sqm | The mission file the editor saves (text or binarized config). |
| description.ext | Hand-written mission config: sounds, music, respawn, dialogs. |
| briefing.html / overview.html | Hand-written HTML briefing and mission-list overview. |
| SQS / SQF | OFP-era script syntaxes. Both appear in community tooling (e.g., the IGSE file list). |
| PBO | Bohemia archive format for missions and addons. |
| `addOns[]` / `addOnsAuto[]` | Lists in mission.sqm of the addons a mission requires. |
| BIKI | Bohemia Interactive Community Wiki. |

### 1.2 Sources and what was (not) reachable

- **Verified directly:**
  - CWR-CE issues, discussions and pull requests on GitHub.
  - Local pinned clones of CWR and CWR-CE.
  - BIKI pages, fetched through the MediaWiki API (see the note below on the main 2D-editor page).
  - OFPEC Editors Depot lists and tutorials.
  - Faguss's tool manuals (PDF).
  - Several Steam discussion threads.
  - The Steam reviews JSON API for CWA (app 65790).
  - Steam Workshop pages (subscriber counts).
  - Two Bohemia forum threads.
  - News articles on AI and modding.
- **Not reachable:**
  - Reddit: the fetch tool is blocked, and site searches returned nothing.
  - Discord: login required.
  - Most `forums.bohemia.net` threads: HTTP 403 after a few requests.
  - The main BIKI "2D Editor" page: consistently 403 through both the web page and the API. Its
    subpage "2D Editor: External" was reachable.
  - Web archives: blocked.
- **How quotes were obtained.** Quotes marked "(fetch summary)" passed through a summarizing fetch
  tool. Spot-check them before citing in public. Quotes from PDFs, BIKI wikitext, GitHub and the Steam
  reviews API are verbatim.
- **Epistemic tags:** **[V]** verified against a cited source; **[I]** inferred by this author;
  **[U]** unknown or unverified.

## 2. Baseline: the original editor as the community knows it

This section records the behaviour a faithful clone must reproduce. It was verified in the engine
source at `BohemiaInteractive/CWR@ffc61838b7`. That source is the 2026 remaster (SDL input, remaster
additions), so "the original editor" below means the remaster's editor code; that each behaviour was
identical in the CWA 1.99 binary is **[I]** unless a period source (FAQ, tutorial) is also cited.

| Behaviour | Evidence |
| --- | --- |
| **Modes:** F1 Units, F2 Groups, F3 Triggers ("Sensors"), F4 Waypoints, F5 Synchronize, F6 Markers. Keypad-5 animates the map to the player. **[V]** | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapExt.cpp#L1400-L1519` |
| **Clipboard:** Ctrl+X/C/V, Shift+Del (cut), Ctrl+Ins (copy), Shift+Ins (paste). Ctrl+Shift+V pastes at the original position ("paste absolute"). The clipboard is in-process and can hold units, groups, triggers, markers and empty vehicles. **[V]** | `...UIMapExt.cpp#L1520-L1645`; `...UIMapExt.cpp#L1073-L1268` |
| **Multi-select:** drag a rectangle on empty map; Ctrl+click toggles an item without clearing the selection (`InvertSelection`); Shift+click toggles a whole group. **[V]** | `...UIMapExt.cpp#L2527-L2556`; BIKI OFP FAQ ("drag a selection box ... press the DELETE key") |
| **Easy/Advanced toggle.** Advanced reveals Merge, the section combo (Mission / Intro / Outro-Win / Outro-Lose) and "Show IDs". OFPEC notes that Easy mode "simply hides aspects of the mission editor". **[V]** | `...UIMapExtDisplay.cpp#L429-L501`; OFPEC tutorial |
| **Load / Merge / Save / Intel / Clear / Preview / Continue buttons.** Preview is hidden until `ArcadeTemplate::IsConsistent` passes; in the MP editor it also stays hidden until the mission has a name, and MP Preview saves mission.sqm and exits the editor instead of playing. **[V]** | `...UIMapExtDisplay.cpp#L410-L427`, `#L503-L622` |
| **What `IsConsistent` checks, and when:** SP needs a player (only in builds without `_ENABLE_CHEATS`); a group's units are counted by their driver, commander and gunner positions (so one tank can count up to 3), with a cap of 12; groups per side are capped by `MaxGroups`. **[V]** The Preview button's visibility is refreshed with a silent check (`ShowButtons`), which runs after Delete, Load/Merge, Save, Clear, a section switch and on editor open, so on those paths an inconsistent mission simply loses its Preview button (clipboard paste does not refresh it at all). The explanatory modal boxes appear on four paths: OK in the unit dialog, OK in the group (F2) dialog, the Preview click, and leaving the editor with OK (`CanDestroy`). **[V]** from code; the resulting UX ("Preview vanished, no reason given" after a delete, load or merge) is **[I]**. | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.cpp#L1754-L1860`; `...UI/Map/UIMapExtDisplay.cpp#L410-L421`, `#L535`, `#L2072-L2073`, `#L2118-L2119`, `#L2373`; `...UIMapExt.cpp#L1580-L1585` |
| **`MaxGroups` is data-driven, not hard-coded:** it is the number of `CfgWorlds >> GroupNameList >> letters` times the number of `GroupColorList >> colors`. The FAQ's "63 groups per side" is therefore a property of the vanilla config. **[V]** | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Core/Config/Configuration.cpp#L339-L349` |
| **Shift+Preview** shows the briefing first, if the mission has a briefing file. **[V]** Preview also deletes `weapons.cfg`, and, for the Mission section once vehicles initialise, `continue.fps`, `autosave.fps` and `save.fps` from the save directory **[V]**, which bears on the save/autosave complaint in #166 **[I]**. | `...UIMapExtDisplay.cpp#L560-L592`; BIKI "2D Editor: External" |
| **"Show IDs"** of map objects and a **map textures** toggle. **[V]** | `...UIMapExtDisplay.cpp#L623-L666` |
| **Unit dialog fields:** side, class, vehicle, control, rank, azimuth, special, age, skill, health, fuel, ammo, probability of presence, condition of presence, placement radius, init, lock, name. **Trigger fields:** axes, angle, rectangle, activation, repeating, interruptible, min/mid/max timeouts, type, object, text, name, condition, on-activation, on-deactivation. **[V]** | `...UIArcade.cpp#L809-L1003`, `#L1434-L1669` |
| **Waypoints can attach to static map objects** (`idStatic`). **[V]** Logic-side groups get AND/OR waypoint types (`ACAND`, `ACOR`) **[V]**. Eden *discontinued* map-object interaction and AND/OR waypoints for logics **[V]**. A CWA clone must keep both **[I]**. | `...UIMapExt.cpp#L2506-L2526`; `...AI/Path/ArcadeWaypoint.hpp#L82-L85`; `...UI/Map/UIArcadeWaypoint.cpp#L79-L90`; BIKI "Eden Editor: Switching from 2D Editor" |
| **On save, required addons are rescanned** (`ScanRequiredAddons`), producing `addOns[]` and `addOnsAuto[]`. An `addOns[]` entry is dropped only if it was in the previous `addOnsAuto[]` and is no longer used; entries that were never auto-detected are kept. **[V]** | `...AI/ArcadeTemplate.cpp#L1910-L1941` |
| **Hard limit** `MAX_UNITS_PER_GROUP 12` (compile-time). **[V]** The FAQ documents the editor error "only 63 groups per side supported" **[V]**, which comes from the config-derived `MaxGroups` (row above). | `...AI/Path/AITypes.hpp#L31`; BIKI OFP FAQ |
| **Remaster additions:** `LooksLikeMod` treats `Missions`, `MPMissions`, `Templates` and `SPTemplates` folders as mod content roots, so mods can ship them **[V]** (that this is new in the remaster is **[I]**). Legacy-codepage (CP1252) world names are decoded in the editor (CWR-CE PR #151, merged 2026-07-24) **[V]**. | `...Core/ModCollection.cpp#L168-L174`; CWR-CE PR #151 |

**No undo exists.** A grep of `engine/Poseidon` for `undo` finds only an unrelated stream comment
**[V]**. BIKI lists undo as new in Eden ("you can now undo recent changes") **[V]**.

## 3. What the community loves (evidence for "Must keep")

| Signal | Evidence (verbatim unless marked) | Tag |
| --- | --- | --- |
| Simple and easy | "Map editor is simple to use and I spent countless hours on that" (review, 2026-07-22) [R1]. "an extremely easy to use yet very versatile mission editor" (2024-08-08) [R2]. "the mission editor once you get the hang of it can be a good time too" (2025-06-26) [R3]. | [V] |
| Depth through scripting | "What I could script was limited only by my proficiency with the editor and the scripting language." (2026-06-06) [R4] | [V] |
| Light and fast compared with newer Armas | "a solid scenario editor" ... "a lighter, more optimized experience" (2025-01-16) [R5] | [V] |
| Preview any time | "you can go into 'Preview' mode and test drive your mission at any point" (Combatsim, 2002-09-10) | [V] |
| Loved then, still loved | 34 of 800 recent English CWA reviews mention "editor"; 33 are positive. The one negative says it did not evaluate the editor. CWA's overall English score: "Very Positive", 2,398 of 2,978. The 800-review window runs 2021-07-07 to 2026-09; 97 of the 800 (8 of the 34 editor mentions) date from 2026-07-01 on, i.e. mostly the remaster. A review's thumbs-up is for the game, not specifically the editor. | [V] |
| Long-lived community tooling | Faguss's In-Game Script Editor v1.2 was released 2026-05-16; his Mission Editor 3D reached v0.25 in 2024-07 | [V] |
| "No dependencies for players" | 3den Enhanced: "adds new functionalities to the Eden Editor without creating any dependencies for players ... without making the life of the players harder by forcing them to download an additional modification." | [V] |
| Simplicity vs depth is a live debate | Arma 3 OP: Eden is "slow to use, so clunky and obtuse". Reply: "The Eden editor is widely regarded as one the very best mission editor in all of gaming" (Steam, 2025-07-26, fetch summary) [W37]. Reforger: "Zeus is far superior to the Game Master we've got now ... it just worked" (2023, fetch summary). | [V] |

**Takeaway [I].** OFP's own Easy/Advanced toggle already resolves the simplicity-vs-depth tension
through progressive disclosure. New power features belong behind "Advanced" or in side panels. They
must not clutter the classic screen.

## 4. Pain points, ranked

Ranking is by **[I]** frequency across sources and severity for mission makers.

| # | Pain point | Evidence | Tag |
| --- | --- | --- | --- |
| P1 | **No undo.** Mistakes are permanent until reload. | Absent from the code (§2); undo was advertised as new in Eden | [V] |
| P2 | **Script fields are blind and errors are hostile.** After a syntax error in an init field, a message box leaves the editor unable to accept input. A mission that loads in SP/MP "fails to open in the mission editor" with "no meaningful error message". | CWR-CE #234 (2026-08-16), #185 (2026-07-29) | [V] |
| P3 | **Most of mission-making happens outside the editor.** "Briefings, custom scripts, multiplayer settings or final packing are only handled by separate files programs." Custom sounds need description.ext plus OGG files (Steam 2018, fetch summary). IGSE exists to eliminate "frequent window switching between the game and an external text editor program". | BIKI "2D Editor: External"; Steam; IGSE manual | [V] |
| P4 | **Addon dependency hygiene.** Deleted addon units left stale `ADDONS/ADDONSAUTO` entries: "You'll have to edit the MISSION.SQM file with a text editor". For Mapfact's Arma 2 Editorupgrade (2009), a mission maker wrote "if people need the addon then I cant use it" (fetch summary; the earlier wording "would force players to download additional content" is unverified). Current ask: auto-check and download mission mod dependencies. | BIKI OFP FAQ; BI forums 2009 [W32] (fetch summary); CWR-CE #233 | [V] (CWR's `ScanRequiredAddons` prunes only entries it auto-detected earlier; `addOns[]` entries never auto-detected are kept, so they can still go stale [V from code]; whether the FAQ-era behaviour predates `addOnsAuto` is [U]) |
| P5 | **Many objects cannot be placed.** Four separate "editor update/upgrade" addons existed: Gunslinger's EU (~500 objects), Kegetys' Editor Addon 1.11, Mikero's Editor103 and General Barron's Editor Upgrade. The same demand recurred in Arma 2: Rübe (2009): "give us access to them. Directly without any 3rd party addon" (fetch summary). | BIKI OFP FAQ; OFPEC Editor Addon list; BI forums 2002 (OFP) / 2009 (Arma 2) | [V] |
| P6 | **No precise 3D placement.** "You cannot set Z axis in the mission.sqm". Static objects shift with `setPos`. Workarounds: ME3D and Set-Pos-In-Game scripts. | Faguss ME3D manual §5 | [V] |
| P7 | **Engine limits surface late or opaquely:** as a modal box after OK in the unit or group dialog, at Preview, or on exit, but only as a silently hidden Preview button after deletes, loads and merges (§2). "only 63 groups per side supported". Civilian-side objects consume group slots. A group's cap of 12 counts crew positions, not vehicles. Players ask for the limits to be raised. | BIKI OFP FAQ; `ArcadeTemplate.cpp#L1754-L1860`; `AITypes.hpp#L31`; CWR-CE #136; discussion #116 | [V] |
| P8 | **Documentation and discoverability.** "comes with really lousy documentation" (2002). "how on earth do you use this feature?" (Steam 2013, fetch summary). Zoom: "It took him three months of toying with OFP to discover this". Waypoint visibility depends on difficulty and "show" settings (Steam, fetch summary). | Combatsim; Steam; BIKI FAQ | [V] |
| P9 | **Workflow friction.** No documented way to launch straight into the editor with a mission from a shortcut (#35, open). The code does accept a positional `mission` argument ("Mission file to load (.pbo or .sqm)", basic help visibility) and opens a `.sqm` in the editor [C19], but there are no `-profile`/`-island`/`-editor` flags and whether this works for arbitrary paths is untested. Save/load and autosave do not work in Preview (#166). Saving failed because of folder permissions (Steam 2013, fetch summary). | CWR-CE #35, #166; Steam | [V] |
| P10 | **Packed and encrypted missions cannot be opened.** Official SP missions need a "PBO Decryptor" (Steam 2015, fetch summary). | Steam thread; BIKI FAQ lists UnPBO/DeSQM | [V] |
| P11 | **Mission name pitfall:** "Giving the mission a name is important, otherwise the briefing will display __cur_sp." | OFPEC tutorial | [V] |

## 5. Lessons from later editors, mods and historical tools

| Source | Feature or lesson | Community signal | Tag |
| --- | --- | --- | --- |
| Arma 3 Eden | Undo/redo (history resets on play or load) | Eden headline feature | [V] |
| Eden | Layers: hide, lock ("Enable Transformation"), group thematically | BIKI | [V] |
| Eden | Custom compositions keep attributes, layers and connections; shared via Workshop and to Zeus | BIKI | [V] |
| Eden | Comment entities that exist only in the editor | BIKI | [V] |
| Eden | Entity list plus search. Asset search supports `class`/`mod` prefixes, and since Arma 3 2.22 wildcards and regex (unverified: the Asset Browser page returned 403 on re-check) | BIKI Menu Bar / Asset Browser | [V] entity list; [U] search syntax |
| Eden | Multi-entity attribute editing (differing values are disabled until you tick them) | BIKI | [V] |
| Eden | Preview variants: SP, SP with briefing, at camera position, "Play from Here", "Play as the Character", MP | BIKI Preview / Menu Bar | [V] |
| Eden | Grids and snapping (translation, rotation, scale), surface snapping, vertical mode, status-bar X/Y/Z | BIKI Toolbar / Status Bar | [V] |
| Eden | Keys: Ctrl+Z/Y, Ctrl+C/X/V, Ctrl+Shift+V raw paste, Ctrl+M merge scenarios, Ctrl+Shift+F search entities, Enter preview | BIKI Controls | [V] |
| Eden | Scenario phases Intro / Scenario / Outro-Win / Outro-Lose. OFP already had these (§2). | BIKI | [V] |
| 3den Enhanced (398,738 subs, updated 2026-09-13) | Briefing Editor, CfgSentences (dialogue) browser, Garrison Buildings, Measure Distance, Selection Filter, align/space/orient tools, Name Objects, "Add to Favorites", log positions/classes, SQM backup, **Command Palette** (Alt+Space) with custom snippets | Most popular Eden extension | [V] |
| Zeus Enhanced (739,089 subs); MCC Sandbox 4 (243,521); ALiVE (208,272) | Live, real-time and generator-driven mission making. MCC: "create missions without any scripting knowledge and alter them in while in game" (search snippet). | Very high adoption | [V] counts; [V/snippet] MCC text |
| Arma 2 Alt+E 3D editor | Hidden 3D editor; users found it "very confusing" (Steam 2017, fetch summary); game crashes; 3D-to-2D converters needed (BI forums 2009, fetch summary) | Negative | [V] |
| Arma Reforger Workbench | Mission making called far more complex than Eden; "complete lack of any mission making tools" (2023, fetch summary) | Negative | [V] |
| Faguss Mission Editor 3D (OFP/CWA) | Real-time edit of mission.sqm while the mission runs; addon-config object list with search; F1 shortcut list | Niche but active | [V] |
| Faguss IGSE | In-game file manager and text editor: search/replace, bookmarks, PBO pack/unpack, image preview | Active 2011-2026 | [V] |
| Fwatch / OFP Game Schedule | Scripting extension; one-click server join with automatic mod install | Community infrastructure | [V] |
| OFPEC depot | Chris' OFP Script Editor (briefings, description.ext); OFP Dialog Maker; OfpCmaker and Campedit (campaigns); Mando_OFPClass (lists classes used); syntax highlighting for Vim, Crimson and UltraEdit; COMREF command reference | Long-standing demand for scripting aids | [V] |
| OFPEC tags | 2-8 letter author prefix for global variables to avoid clashes (search snippet) | Convention | [V/snippet] |
| Squint; VS Code SQF / SQFLint; HEMTT | SQF linting with syntax colouring (Squint, Arma 2 era); modern language servers; HEMTT lints (Arma 3) | Scripting aids are expected | [V/snippet] |

**Lessons [I]:**

1. Every popular editor extension adds convenience without adding runtime dependencies.
2. Live and real-time editing is loved when it "just works", and hated when hidden or crashy.
3. Eden's weaknesses, as perceived, are speed and clunkiness. Our USP should be *OFP speed plus modern
   safety nets*.

## 6. Scripting aids wanted

All items are **[I]**, derived from P2, P3 and P8 and from the tools in §5 unless tagged otherwise.

- **Integrated editors** for init, condition and activation fields, and for the files around the
  mission: description.ext, briefing.html, overview.html, `*.sqs`, `*.sqf`, stringtables.
  IGSE's reason to exist is proof of demand **[V]**.
- **A command reference that matches CWA exactly.** The engine registers most script commands in
  `engine/Poseidon/Game/Commands/GameStateExt.cpp`: 473 registration entries (482 lines match
  `GameFunction|GameOperator|GameNular`, 9 of them declarations) in CWR **[V]**. Core operators and
  nulars (`nil`, `true`, arithmetic and so on) are registered separately in
  `BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/express.cpp#L1100-L1212`, and three `diag_*`
  commands in `engine/Poseidon/World/Scene/SceneDraw.cpp#L541-L547` **[V]**; a generator must scan all three. Generate the reference from the pinned engine source instead of from Arma 3 docs.
  Link each command to its BIKI page. Command sets differ between releases: #166 reports `saveMission`
  as a new, undocumented remaster command **[V]**, and it is registered at
  `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Game/Commands/GameStateExt.cpp#L1043` **[V]**.
  The database must therefore be versioned per target: CWA 1.99, CWR or CWR-CE **[I]**.
- **Non-modal diagnostics** in a problems panel. Never block input (fixes P2). Reuse the engine grammar
  where feasible: CWR-CE ships `PoseidonEvaluator`, an "SQF expression evaluator" CLI
  (`ofpisnotdead-com/CWR-CE@b67bf3bd62:apps/README.md#L16`, `#L32`) **[V]**.
- **Name checks:**
  - unit, group, trigger and marker names that scripts or triggers reference but do not exist;
  - duplicate names;
  - marker names in `setMarkerPos` and similar calls;
  - globals without an OFPEC-style tag (optional).
- **Snippets and templates** for common OFP idioms: `addWeaponCargo`, respawn and description.ext
  blocks, cutscene cameras, `titleText` and `sideChat` dialogue.
- **Audio helpers:** OGG/WAV/WSS guidance (the FAQ recommends WSS) and `.lip` generation. CWR-CE's
  `PoseidonTools sound lip` generates a ".lip lip-sync file from a 16-bit mono audio file" **[V]**
  (`...apps/tools/Tools/commands/SoundCommand.cpp#L155-L172`).

## 7. Community sentiment on AI and LLM tools

### 7.1 Signals

| Signal | Source | Polarity | Tag |
| --- | --- | --- | --- |
| CWR-CE: "AI-assisted contributions are welcome". Rules: "you are the author, not the tooling"; "free of AI boilerplate"; do not run AI review bots against the repo directly ("their output tends to be noisy"; run them on your own fork). Note the norm is human accountability, not disclosure: commit metadata must credit only the human, with "no AI mention in the commit message". | `ofpisnotdead-com/CWR-CE@b67bf3bd62:CONTRIBUTING.md#L59-L72` | + (with conditions) | [V] |
| Zeus Mission Generator 2.0, a Discord mission-idea bot using "natural language completion AI" (2022-10-12; that it is an LLM is inferred): replies call it "a good last resort whenever I run out of quick improvised mission ideas" and "pretty good as inspiration" (fetch summary) | BI forums | + | [V] |
| DCO GPT, ChatGPT-driven NPC chat for Arma 3: the server owner or mission maker needs an OpenAI API key and a node.js install (players only subscribe). 1,233 subscribers; last updated 2023-05-18. For comparison, 3den Enhanced has 398,738. | Steam Workshop | neutral/low uptake | [V] numbers; causal reading [I] |
| ChatGPT "can spit out functions that don't exist or invalid syntax" for SQF; users without scripting knowledge cannot fix its output | BI forums thread "Chat GPT tried to script" (search snippet only; thread returned 403) | - (quality) | [V/snippet] |
| Nexus Mods split its AI tags after users said one tag "does not allow for nuance". The "AI Assisted" tag requires proof of human-led work (TheGamer, 2026-07-30). | TheGamer | disclosure demanded | [V] |
| Skyrim voice clones made without consent: "I don't agree to having my voice/s being turned into synthetic voice clones without my absolute, clear, specific and undeniable consent." (Ben Diskin, via Kotaku, 2023-07-05) | Kotaku | - - | [V] |
| The SAG-AFTRA video game strike (2024-07-26 to 2025-07-09) ended with consent and disclosure rules for digital replicas | Wikipedia | consent norm | [V] |
| Steam requires AI disclosure, distinguishing "pre-generated" from "live-generated" content (January 2024). A January 2026 narrowing to player-facing content is reported by secondary sources. | Steamworks post (title verified; body is rendered by JS); secondary reporting | disclosure norm | [V] title / [U] details |
| Indie Game Awards rescinded Clair Obscur's awards over generative AI use (December 2025) | multiple outlets (search results) | - - | [V/snippet] |
| No Bohemia- or Arma-specific AI controversy was found | searches | - | [U] |
| Iron Curtain design-docs precedent: "BYOLLM ... game fully functional without LLM" | `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D016-llm-missions.md#L1-L5` | design precedent | [V] |

### 7.2 Reading **[I]**

- **Accepted:** AI as an assistant to a human author, for ideas, boilerplate and explanations.
- **Resented:** undisclosed AI output ("slop"), AI that invents commands, and anything touching real
  people's voices.
- **Poorly adopted:** heavyweight setup (API keys, node.js, a runtime dependency in the mission).
- **OFP-specific risk:** the community is nostalgic about the original cast (reviews name "Dave
  Armstrong, Victor Troska, Guba"). Imitating those voices is off-limits.

### 7.3 Positioning principles (proposed)

1. **Opt-in and bring your own model; off by default.** Every editor feature works without a model
   (WN1).
2. **AI proposes, the human disposes.** Each AI action is one labelled transaction in the normal undo
   stack, shown as a diff before it applies. This depends on S1 undo.
3. **Validated against CWA reality.** Generated SQS/SQF and class names go through the same validator
   as human edits. Unknown commands and classes are rejected, not "fixed silently".
4. **Text-first dialogue.** Generate `sideChat` / `titleText` lines, briefing HTML and CfgSentences
   drafts. Voice only through user-supplied, licensed TTS voices. Never clone (WN2). Generate `.lip`
   files for any audio.
5. **Disclosure made easy.** Store an optional provenance sidecar (which fields were AI-drafted) and
   offer an "AI-assisted" line for the readme. Do not write this into mission.sqm until we know
   unknown fields are safe there (Open questions). Keep it optional: disclosure norms differ (Nexus
   Mods asks for AI tags, while CWR-CE forbids AI mentions in commit metadata).
6. **Target proven use cases:** idea generation, "explain this script", lint-fix suggestions,
   repetitive placement ("garrison this town"), briefing polish, and translation of stringtables.
   Avoid marketing "one-click missions".

## 8. Prioritized backlog (MoSCoW)

Backlog IDs are M (Must keep), S (Should add), CO (Could add) and WN (Won't). Bracketed keys such as
[C1] (code) and [W1] / [R1] (web) refer to §Sources. All priorities are **[I]**, based on the evidence
cited in each row.

### 8.1 Must keep (parity; losing these would alienate the core community)

| ID | Item | Why / sources |
| --- | --- | --- |
| M1 | Map-first 2D workflow with the F1-F6 modes; double-click to place or edit | §2 [C1]; "simple to use" [R1-R3] |
| M2 | Easy/Advanced progressive disclosure (Merge, Intro/Outro sections, IDs behind Advanced) | [C5][W29] |
| M3 | Full dialog-field parity for units, groups, triggers, waypoints (incl. Cycle, attach to map object), markers, effects | [C9][C2][W29] |
| M4 | Load / Merge / Save / Export (user SP mission, MP mission, PBO) / Clear; `name.world` folder convention | [C4][C6][W20][W31] |
| M5 | Intel dialog (name, description, date, time, weather), with a warning when the name is empty (`__cur_sp`) | [W29] |
| M6 | Four sections (Mission / Intro / Outro-Win / Outro-Lose), loaded permissively when a section is absent | [C4][W4][W19] |
| M7 | Keyboard and mouse flow: Delete, the clipboard keys incl. paste-absolute, rectangle / Ctrl / Shift selection, keypad-5, wheel and keypad +/- zoom | [C1][C2][C3][W21] |
| M8 | Preview that runs the real game; Shift+Preview shows the briefing; Preview gated on consistency | [C6][W20][W31] |
| M9 | OFP semantics that Eden dropped: Synchronize mode, waypoints attached to static map objects, logic waypoints | [W9][C2] |
| M10 | Output is vanilla-loadable mission files; no dependency on our tool or its addons | [W44][W32] |
| M11 | Lightweight and fast: starts without loading the game; runs windowed or fullscreen | [R5]; user goal |
| M12 | "Show IDs" and map-texture toggles | [C6] |
| M13 | Mod-aware class lists (mod configs and mod-shipped Templates); correct legacy-codepage names | [C10][W8] |

### 8.2 Should add (most-requested improvements)

| ID | Item | Why / sources |
| --- | --- | --- |
| S1 | Undo/redo with visible history that survives Preview (unlike Eden, which resets it) | P1; [W9][W11] |
| S2 | Non-modal problems panel. Parse errors name the file, line and section. The editor never locks input. | P2; [W3][W4] |
| S3 | Addon dependency manager: per-entity provenance, stale-entry cleanup, warnings for non-vanilla classes, exported dependency manifest / readme | P4; [W21][C7][W6][W32] |
| S4 | Live engine-limit lint as you place: `MaxGroups` = letters x colors from the loaded config (63 in vanilla), 12 crew seats per group, the civilian group-slot trap, SP needs a player. Limits are computed from data, per target engine. | P7; [W21][C8][C17][C18][W5] |
| S5 | Integrated editors for description.ext, briefing/overview HTML and scripts, with highlighting, hover docs, snippets and find/replace | P3; [W20][W24][W27] |
| S6 | Command reference generated from the pinned engine source, per target, with BIKI links | §6; [C11][C12] |
| S7 | Name and reference validation (undefined or duplicate names, markers used in scripts); optional tag-prefix rule | §6; [W30] |
| S8 | Entity list / outliner with search (class, name, type); asset search with class/mod prefixes | [W11][W17] |
| S9 | Multi-select attribute editing | [W9] |
| S10 | Preview variants (from camera, as selected unit) if the engine allows. CWR-CE dev flags exist: `--test-mission`, `--simulate`, `--harness`; the positional `mission` argument opens a `.sqm` in the in-game editor. | [W13][C13][C19][W2]; see 08-mission-preview-and-game-integration.md |
| S11 | Open a mission from CLI or file association, recent-files list, autosave, rotating mission.sqm backups | P9; [W1][W2][W45] |
| S12 | Open and unpack PBO missions; pack on export | P10; [W42][W24] |
| S13 | Precise placement: numeric position, azimuth and height (ME3D-style `setPos` pattern), grid snapping, align/space/orient | P6; [W23][W45] |
| S14 | Custom compositions (reusable prefabs) | [W15] |
| S15 | Editor-only comments / annotations | [W16] |
| S16 | Layers (hide / lock) | [W14] |
| S17 | Briefing editor and dialogue browser | [W45][W27] |
| S18 | Discoverability: F1 shortcut overlay, tooltips, contextual "why isn't X visible" hints, docs links; clear errors for save location and permissions | P8, P9; [W23][W24][W39][W41] |

### 8.3 Could add (valuable, later)

| ID | Item | Why / sources |
| --- | --- | --- |
| CO1 | Optional 3D view for placement and height, additive to the 2D map | [W23][W22]; caution [W34][W35] |
| CO2 | Live link to a running game (ME3D- and Zeus-style), e.g. through the CWR-CE harness | [W23][W46][W47][C13] |
| CO3 | Command palette, also the natural home for the AI prompt | [W45] |
| CO4 | Favorites in the asset browser | [W45] |
| CO5 | Garrison buildings, measure distance, selection filter, randomize direction | [W45] |
| CO6 | Campaign editor and description.ext wizards (respawn, sounds, music) | [W26][W40] |
| CO7 | `.lip` generation for dialogue audio | [C14][W21] |
| CO8 | Headless smoke test ("does it start without script errors?") | [C13] |
| CO9 | Dependency metadata usable by the remaster's mod manager, OFP Game Schedule and papa-bear.cz | [W6][W25][W61] |
| CO10 | Asset search with wildcards and regex | [W17] |
| CO11 | Status-bar coordinates and grid reference; copy positions and classes | [W18][W45] |
| CO12 | Opt-in AI co-pilot per §7.3: ideas, explain, lint-fix, placement macros, briefing and dialogue drafts, stringtable translation | §7 |
| CO13 | Multiplayer settings UI (respawn, players, parameters) | [W40] |
| CO14 | Gamepad / Steam Deck input (the remaster added controller UI to the editor) | [C4] (`ControllerUiScene`, `CycleControllerMode`) |

### 8.4 Won't (explicit non-goals)

| ID | Non-goal | Why / sources |
| --- | --- | --- |
| WN1 | AI required, on by default, or cloud-only | §7; [W49][C16][W12] |
| WN2 | Voice cloning of real people, including the original OFP cast | [W53][W54] |
| WN3 | Implicit non-vanilla dependencies written into missions | [W44][W32] |
| WN4 | Redistributing proprietary game data or official missions, or decrypting them for redistribution | Project rules; `ofpisnotdead-com/CWR-CE@b67bf3bd62:CONTRIBUTING.md#L54-L57` |
| WN5 | Replacing the 2D map-first flow with a 3D-first (Eden-style) design | [R1-R4][W35][W36] |
| WN6 | Auto-applying or auto-publishing AI output without review and labelling | [W52][W56][W12] |
| WN7 | In-game runtime LLM NPC chat (DCO GPT style); outside editor scope | [W49] |
| WN8 | "Fixing" engine limits inside the editor. We validate against the target engine's config and constants (`MaxGroups` comes from config, `MAX_UNITS_PER_GROUP` is compiled in), and CWR-CE may raise either (#136). | [W5][C8][C18] |

## Open questions

1. **Protected classes.** Does CWA accept `scope=1` (protected) classes in mission.sqm? If it does,
   S13/P5 could expose "hidden" vanilla objects without addons. **[U]**
2. **Interactive preview.** Can the CWR-CE dev flags (`--test-mission` "Run mission folder or
   mission.sqm directly and exit"; `--simulate`) support an interactive Preview? Does the existing
   positional `mission` argument (`.sqm` opens the in-game editor, [C19]) work for a mission outside
   the user's Missions folder, and will #35 (`-editor` / `-mission` / `-island` / `-profile`) land?
   **[U]** See 08-mission-preview-and-game-integration.md.
3. **Target engine.** Vanilla CWA 1.99, CWR or CWR-CE? This decides the command set, the limits and
   the preview mechanism. **[U]**
4. **Unknown fields.** Does the mission.sqm loader ignore unknown classes or fields safely? That decides
   whether provenance and comment metadata can live inside mission.sqm or must use sidecars. **[U]**
5. **Encrypted missions.** What is the legal and ethical line for opening a user's own
   encrypted official missions locally (P10)? **[U]**
6. **Unsampled channels.** Discord, Reddit and most Bohemia forum threads were not reachable. A short
   survey (ofpisnotdead Discord, CWR-CE Discussions) should validate the P- and S-rankings. **[U]**
7. **Multiplayer editing.** The engine has edit-rights logic (`HasFullRights`, `HasRight`) in the map
   editor. Is there community demand for collaborative or multiplayer mission editing? **[U]**

## Sources

**Code** (all paths repo-relative):

- [C1] `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapExt.cpp#L1400-L1645`
- [C2] `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapExt.cpp#L2506-L2556`
- [C3] `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapExt.cpp#L1073-L1268`
- [C4] `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMap.hpp#L705-L764`
- [C5] `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapExtDisplay.cpp#L410-L501`
- [C6] `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapExtDisplay.cpp#L503-L666`
- [C7] `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.cpp#L1910-L1941`
- [C8] `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/Path/AITypes.hpp#L31`
- [C9] `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcade.cpp#L809-L1003` and `#L1434-L1669`
- [C10] `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Core/ModCollection.cpp#L168-L174`
- [C11] `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Game/Commands/GameStateExt.cpp` (whole file; registration table)
- [C12] `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Game/Commands/GameStateExt.cpp#L1043`; `ofpisnotdead-com/CWR-CE@b67bf3bd62:apps/README.md#L9-L36`
- [C13] `ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/Foundation/Platform/AppConfig.cpp#L662-L688`
- [C14] `ofpisnotdead-com/CWR-CE@b67bf3bd62:apps/tools/Tools/commands/SoundCommand.cpp#L155-L172`
- [C16] `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09f/D016-llm-missions.md#L1-L5`
- [C17] `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.cpp#L1754-L1860` (`IsConsistent`)
- [C18] `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Core/Config/Configuration.cpp#L339-L349` (`MaxGroups`)
- [C19] `ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/Foundation/Platform/AppConfig.cpp#L761-L765` (positional `mission` arg) and `#L1133-L1136`; `...engine/Poseidon/World/WorldImpl.cpp#L2217-L2258` (`.sqm` → `OpenEditor()`); `...engine/Poseidon/UI/DisplayUIMenus.cpp#L1979-L1990`. The same positional arg and `.sqm` path exist in `BohemiaInteractive/CWR@ffc61838b7` (same files).
- [C20] `BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/express.cpp#L1100-L1212` (core operators); `...engine/Poseidon/AI/Path/ArcadeWaypoint.hpp#L82-L85` (`ACAND`/`ACOR`)
- [W12] `ofpisnotdead-com/CWR-CE@b67bf3bd62:CONTRIBUTING.md#L59-L72`

**CWR-CE tracker:**

- [W1] https://github.com/ofpisnotdead-com/CWR-CE/issues/166
- [W2] https://github.com/ofpisnotdead-com/CWR-CE/issues/35
- [W3] https://github.com/ofpisnotdead-com/CWR-CE/issues/234
- [W4] https://github.com/ofpisnotdead-com/CWR-CE/issues/185
- [W5] https://github.com/ofpisnotdead-com/CWR-CE/issues/136
- [W6] https://github.com/ofpisnotdead-com/CWR-CE/issues/233
- [W7] https://github.com/ofpisnotdead-com/CWR-CE/discussions/116
- [W8] https://github.com/ofpisnotdead-com/CWR-CE/pull/151

**BIKI** (fetched as wikitext via `https://community.bistudio.com/wikidata/api.php`):

- [W9] https://community.bistudio.com/wiki/Eden_Editor:_Switching_from_2D_Editor
- [W10] https://community.bistudio.com/wiki/Eden_Editor:_Controls
- [W11] https://community.bistudio.com/wiki/Eden_Editor:_Menu_Bar
- [W13] https://community.bistudio.com/wiki/Eden_Editor:_Preview
- [W14] https://community.bistudio.com/wiki/Eden_Editor:_Layer
- [W15] https://community.bistudio.com/wiki/Eden_Editor:_Custom_Composition
- [W16] https://community.bistudio.com/wiki/Eden_Editor:_Comment
- [W17] https://community.bistudio.com/wiki/Eden_Editor:_Asset_Browser
- [W18] https://community.bistudio.com/wiki/Eden_Editor:_Status_Bar
- [W19] https://community.bistudio.com/wiki/Eden_Editor:_Scenario_Phases
- [W20] https://community.bistudio.com/wiki/2D_Editor:_External
- [W21] https://community.bistudio.com/wiki/Operation_Flashpoint:_FAQ:_Mission_Editing
- [W22] https://community.bistudio.com/wiki/Eden_Editor:_Introduction
- Eden toolbar: https://community.bistudio.com/wiki/Eden_Editor:_Toolbar

**OFP community:**

- [W23] https://ofp-faguss.com/files/missioneditor3d.pdf
- [W24] https://ofp-faguss.com/files/in-game_script_editor.pdf
- [W25] https://ofp-faguss.com/schedule/
- [W26] https://www.ofpec.com/editors-depot/index.php?action=list&game=OFP&cat=to&type=me
- [W27] https://www.ofpec.com/editors-depot/index.php?action=list&game=OFP&cat=to&type=sc
- [W28] https://www.ofpec.com/editors-depot/index.php?action=list&game=OFP&cat=to&type=ea
- [W29] https://www.ofpec.com/tutorials/index.php?action=read&id=38
- [W30] https://community.bistudio.com/wiki/OFPEC_tags (search snippet)
- [W31] https://www.combatsim.com/memb123/htm/2002/09/opflash-me/
- Editor Update download: https://files.ofpisnotdead.com/files/editorupdate102/

**Bohemia forums:**

- [W32] https://forums.bohemia.net/forums/topic/76483-mapfactnet-releases-editorupgrade/
- [W33] https://forums.bohemia.net/forums/topic/15728-map-editor-update/
- [W34] https://forums.bohemia.net/forums/topic/83597-how-to-use-the-3d-editor-tutorial/
- [W50] https://forums.bohemia.net/forums/topic/240304-zeus-mission-generator-20-ai-mission-generator/
- [W51] https://forums.bohemia.net/forums/topic/242364-chat-gpt-tried-to-script/ (search snippet only)

**Steam discussions:**

- [W35] https://steamcommunity.com/app/33930/discussions/0/1471967615853542751/
- [W36] https://steamcommunity.com/app/107410/discussions/18/1694924244565886121
- [W37] https://steamcommunity.com/app/107410/discussions/0/591777615946438760/
- [W38] https://steamcommunity.com/app/1874880/discussions/0/3780246026247846134
- [W39] https://steamcommunity.com/app/65790/discussions/0/666825524923849797/
- [W40] https://steamcommunity.com/app/65790/discussions/0/1742227264188458372/
- [W41] https://steamcommunity.com/app/65790/discussions/0/1709564118764995008/
- [W42] https://steamcommunity.com/app/65790/discussions/0/618458030679357829/

**Steam reviews** (API: `https://store.steampowered.com/appreviews/65790?json=1&filter=recent&language=english`, fetched 2026-09-26):

- [R1] https://steamcommunity.com/profiles/76561197974925617/recommended/65790/
- [R2] https://steamcommunity.com/profiles/76561198116646340/recommended/65790/
- [R3] https://steamcommunity.com/profiles/76561199216624343/recommended/65790/
- [R4] https://steamcommunity.com/profiles/76561199063213336/recommended/65790/
- [R5] https://steamcommunity.com/profiles/76561198116484184/recommended/65790/

**Workshop and mods:**

- [W44] https://steamcommunity.com/sharedfiles/filedetails/?id=623475643 (3den Enhanced)
- [W45] https://github.com/R3voA3/3den-Enhanced/wiki/Menu-Strip, https://github.com/R3voA3/3den-Enhanced/wiki/Context-Menu, https://github.com/R3voA3/3den-Enhanced/wiki/3DEN-Command-Palette
- [W46] https://steamcommunity.com/sharedfiles/filedetails/?id=1779063631 (Zeus Enhanced)
- [W47] https://steamcommunity.com/sharedfiles/filedetails/?id=338988835 (MCC Sandbox 4)
- [W48] https://steamcommunity.com/sharedfiles/filedetails/?id=620260972 (ALiVE)
- [W49] https://steamcommunity.com/sharedfiles/filedetails/?id=2965142417 (DCO GPT)
- Squint, SQF linting (search snippets): https://forums.bohemia.net/forums/topic/101921-squint-the-sqf-editor-and-error-checker/, https://hemtt.dev/lints/sqf.html, https://github.com/SkaceKamen/vscode-sqflint

**AI and industry context:**

- [W52] https://www.thegamer.com/nexus-mods-generative-ai-guidelines-update/
- [W53] https://kotaku.com/skyrim-nexusmods-deepfake-porn-ai-voice-eleven-labs-1850607687
- [W54] https://en.wikipedia.org/wiki/2024%E2%80%932025_SAG-AFTRA_video_game_strike
- [W55] https://store.steampowered.com/news/group/4145017/view/3862463747997849618
- [W56] https://www.engadget.com/gaming/the-indie-game-awards-snatches-back-two-trophies-from-clair-obscur-over-its-use-of-generative-ai-164730842.html (search result)

**Remaster:**

- [W57] https://www.bohemia.net/en/blog/Arma-Cold-War-Assault-Remastered-Out-Now (DNS failure on re-check 2026-09-26)
- https://www.gamingonlinux.com/2026/07/arma-cold-war-assault-remastered-is-now-out-in-full-and-open-source/
- Steam store search API (app 65790 listing name): https://store.steampowered.com/api/storesearch/?term=Cold%20War%20Assault%20Remastered&l=english&cc=US
- [W61] papa-bear.cz as the mod host: via search snippet citing https://community.bistudio.com/wiki/Arma:_Cold_War_Assault_Remastered (page itself not fetched)

## Verification notes

Adversarial fact-check, 2026-09-26, against the pinned clones and live sources.

- **Confirmed in code:** no undo/redo in `engine/Poseidon` (only two `QBStream.cpp` comments) or in
  CWR-CE's UI; `MaxGroups` = letters x colors (Configuration.cpp#L339-L349, same in CWR-CE);
  `MAX_UNITS_PER_GROUP 12` (AITypes.hpp#L31, same in CWR-CE); crew-position counting in
  `IsConsistent`; clipboard keys incl. Ctrl+Shift+V; F1-F6 and keypad-5; Easy/Advanced hiding Merge,
  section combo and IDs; Shift+Preview and the four deleted save files; `idStatic` waypoints; unit
  and trigger dialog fields; `ScanRequiredAddons`; `saveMission` at GameStateExt.cpp#L1043;
  ModCollection.cpp#L168-L174; `sound lip`; CWR-CE AppConfig `--harness`, `--test-mission`,
  `--simulate` (#L662-L688); CONTRIBUTING.md#L54-L57, #L59-L72; Iron Curtain D016#L1-L5; CWR LICENSE
  (GPL-3.0-or-later + Section 7 terms).
- **Corrected:** (1) message boxes for limit violations are not Preview-only: they also appear after
  OK in the unit and group dialogs and on leaving the editor (§2, P7); (2) CWR and CWR-CE already
  accept a positional `mission` argument that opens a `.sqm` in the editor [C19], so "no user-facing
  flag" was too strong (P9, S10, Open question 2); (3) command registration also lives in
  `engine/Evaluator/express.cpp` and `SceneDraw.cpp`, and 473 is the count of table entries, not raw
  matches (482) (§6); (4) the 2009 Mapfact Editorupgrade thread is about Arma 2 and the quoted
  "would force players to download" wording was not found (TL;DR, P4, P5); (5) Ctrl+click toggles
  rather than adds; (6) Shift+Preview needs a briefing file; (7) MP Preview visibility and behaviour
  added; (8) PoseidonEvaluator line cite fixed; (9) remaster release date: GamingOnLinux says 16 July
  2026; (10) Steam app 65790 is now the Remastered listing, so the review window mixes both.
- **Confirmed live:** Steam reviews API (800 reviews, 34 mention "editor", 33 positive; 2,398/2,978
  "Very Positive"; R1-R5 quotes, authors and dates); Workshop counts via the Steam API (3den Enhanced
  398,753, Zeus Enhanced 739,093, MCC 243,520, ALiVE 208,271, DCO GPT 1,232: live counts drift by a
  few since the original fetch); DCO GPT API-key/node.js text; 3den Enhanced "no dependencies"
  text; CWR-CE issues #35, #136, #166, #185, #233, #234 (all open, dates as stated), discussion #116,
  PR #151; BIKI OFP FAQ, "2D Editor: External", "Eden Editor: Switching from 2D Editor", Controls,
  Menu Bar, Preview; IGSE v1.2 (16.05.2026) and ME3D v0.25 (2024.07.08) PDFs; OFPEC tutorial and
  Editor Addon list; Combatsim 2002; Steam threads W35 and W37; TheGamer, Kotaku, SAG-AFTRA
  (Wikipedia), Engadget; Zeus Mission Generator thread.
- **Still unverified:** Eden Asset Browser search syntax (2.22 wildcards/regex; page 403); Bohemia
  "Out Now" blog date; Steamworks AI-disclosure details; Reforger quotes (W38); W34 Arma 2 3D-editor
  crash reports; the OFPEC-tags and Squint snippets; whether each CWR editor behaviour matched the
  CWA 1.99 binary.
