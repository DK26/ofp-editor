# UI shell

> **Status:** proposal (architecture baseline 2026-09-27). Nothing here is decided unless it restates `AGENTS.md`, a decision
> record (`Dnnn`), a decided DG or an owner answer (`OWQ-nn`, all answered 2026-09-27). Type sketches are not compiled and names are
> not final.
> **Part of:** [architecture overview](README.md). **Main sources:** doc 03; doc 05; doc 06 §2, §4–§7; doc 09; doc 19 §6; doc 21 §5,
> §11; doc 33 §4–§7; doc 34 (ed, le, mo rows); doc 37 §3, §7; doc 38 §5; doc 45 §2.4–§2.5, §2.9, §3; D002, D016, D028, D029.

The shell is a thin client. It owns view state (selection, camera, folds, dock layout) and presentation caches (draw lists, layout);
it owns no document state, no validity logic and no fact computation. Every edit is a queued command; the same `Session::step` that
the app calls also drives the CLI and the headless tests ([commands-undo-history.md §11](commands-undo-history.md)).

## 1. Stack and crate split

| Crate | Layer | Owns | egui? | wgpu? |
| --- | --- | --- | --- | --- |
| `plotroom-draw2d` | L8 | GPU-free `DrawList` and batcher mirroring the engine's 2D primitives (doc 06 §2.2, §4.2–§4.3) | No | No |
| `plotroom-fonts` | L8 | FXY bitmap-glyph fonts from the install, OFL fallback fonts, TTF fallback for CJK (doc 06 §2.4; doc 34 mo23) | No | No |
| `plotroom-gpu` | L8 | The one wgpu pipeline that executes a `DrawList` into an offscreen `Rgba8Unorm` texture | No | **Only here** |
| `plotroom-ui-classic` | L8 | Retained control tree for the original dialogs, built from `plotroom-rsc` display specs | No | No |
| `plotroom-map2d` | L8 | The classic map as a pure function: (snapshot view, terrain, map style, camera, overlays) → `DrawList` layers | No | No |
| `plotroom-ui` | L8 | egui panels and widgets; no business logic; tested with `egui_kittest` | Yes | Via egui |
| `plotroom-app` | L8 | The `plotroom` binary: eframe `App`, input adapter, I/O and runtime wiring | Yes | Via egui |

- Stack (D016; doc 06): eframe/egui on winit, wgpu and AccessKit; `egui_dock` for docking, `egui_commonmark` for Markdown, `similar`
  for diffs; scripts use `TextEdit` with a layouter fed by Teller's tokenizer. One wgpu version, the one egui-wgpu uses.
- **No crate below `plotroom-ui` sees an egui type**, so rendering, dialogs, the map and the interaction state machine are testable
  headless (doc 06 §4.1).
- If the proof-of-concept spikes fail (composite colour, focus, IME, AccessKit, map stress), the documented fallbacks are the paint-
  callback route and raw winit plus egui-winit; crates below `plotroom-app` are unchanged (doc 06 §5; D016 "Revisit if").

## 2. The classic renderer

- The engine's 2D layer is small: textured quads with per-corner colours, convex polygons up to 32 vertices, 3-pixel lines drawn with
  a line texture, bitmap-glyph text and CPU clip rectangles, blended with straight alpha in gamma space (doc 06 §2). `plotroom-draw2d`
  reproduces exactly that; vector libraries would change the look (D016 alternatives).
- `plotroom-gpu` blends straight alpha, keeps target alpha at 1, uses explicit mip views and batches by (texture, mip, wrap)
  (doc 06 §4.3). Vertex bytes are packed with `to_le_bytes`, not a derive whose generated `unsafe impl` would conflict with the
  workspace's `forbid(unsafe_code)`.
- Static terrain layers are cached per (world, level of detail, style) and built on a worker; the overlay layer is rebuilt only on a
  revision, camera or hover change; idle CPU stays near zero (reactive repaint).
- Scaling modes: Native, Authentic low-res, Scaled chrome; the default is polled with the community (doc 06 OQ2).
- Classic UI resources (layouts, colours, fonts, textures, icons) are read from the user's install at runtime through the VFS, probing
  Remastered, then the free demo's data, then 1.99; nothing is bundled or committed (doc 05 §7; D016 item 3). An original look-alike
  fallback theme covers no-install use and CI.

## 3. The classic view

- **Faithful behaviour** (D004 item 1; doc 03): F1–F6 modes (units, groups, triggers, waypoints, synchronisation, markers), double-click
  insert, rubber band, Shift-drag rotate, drag to link, Del and Shift+Del, clipboard, the 100 m auto-join into groups, and the hit-test
  priorities of the original. The interaction state machine is headless in `plotroom-view` and emits `ViewCmd`s and `EditorCommand`s
  ([commands-undo-history.md §10](commands-undo-history.md)); map hotkeys apply only while the classic view has focus (doc 06 §4.5).
- **Drags** keep a `DragPreview` offset over a cached static layer and commit one `MoveEntities` on release; below a zoom threshold
  glyphs switch to a compact form with hysteresis (doc 45 §3).
- **Overlays**, drawn by the same code the validators use where they overlap:
  - Wilco ghosts and paste/template placement previews on one ghost layer (so AI proposals render through the path users already
    trust);
  - module footprints as handles (drag a ring to edit its radius parameter; doc 31 §4.3); attribute glyphs;
  - Standing Orders instance overlays: the CYCLE loop, the SWITCH jump, the 100 m auto-join ring, "who waits for whom" for syncs, the
    END-group counter (doc 33 §4.3); animated demos with scrubbing (doc 33 §4.6);
  - route and accessibility overlays (I34-05-06; doc 34 ed08, ed21); sight, earshot and sun helpers in v1.x (doc 41);
  - the Preview fire log glow after a trace run ([game-integration.md §9](game-integration.md)).
- **The Plotline flow view** is drawn with the same `draw2d` in the classic style, reusing fonts and chrome (doc 19 §6.7).

## 4. Dialogs

- Unit, Group, Waypoint, Trigger, Effects, Marker and Intel dialogs, and Save, Load and Merge, open modal inside the classic view as
  in the game. Layouts come from `DisplaySpec`s read from the install (`plotroom-rsc`) or from the fallback theme (doc 03 §3.2; doc 05).
- Each dialog is a `DialogSession` over a `Scratch` fork: the original copy-validate-write-back lifecycle, only changed fields written,
  admission hosting the original `CanDestroy` checks, one `Dialog` undo group ([commands-undo-history.md §10](commands-undo-history.md)).
- **Easy/Advanced** stays, as a view preset over the shared disclosure system, **default Advanced**; Easy uses the `…Simple` twins
  (D029; DG033 items 3–4 decided).
- **Original labels stay primary**, taken from the user's game stringtable; plain-language relabels sit beside them as a dim second
  line and on hover cards (D029). Both come from the descriptor tables' `label` and `relabel` fields
  ([core-document-model.md §3.3](core-document-model.md)).
- Greyed-out controls explain their reason with a Standing Orders link (doc 33 §4.4).
- **Modern forms** render the same `DisplaySpec` with egui widgets: the first-class keyboard and screen-reader path, and the default in
  accessibility mode if AccessKit on the classic tree proves inadequate (doc 06 §4.7).

## 5. Inspector

Descriptor-driven and engine-truthful (doc 37 §3; doc 45 §2.5):

- value-source badges ("engine default", "from template Ambush-2", "set by Wilco turn 12", "picked by you from Wilco's menu");
- "mixed" values over multi-select with a per-entity breakdown; one grouped `SetFields` for all targets;
- raw rows for unknown keys and for definitions the editor registry cannot render (doc 37 §3 raw-text row);
- live byte counters measured in the target encoding;
- "Reset to default" (keeps the key written), "Reset to template", "Detach";
- an ordered editor registry picks the widget per field type, falling back to raw text.

## 6. Modern panels

All panels read `DocCtx` and caches only, and dock around the classic view in the "Workbench" layout; the "Classic" layout hides them
for the authentic full-window look.

| Panel | Purpose | Sources |
| --- | --- | --- |
| Outliner | Search, filter, multi-select; egui ids keyed by `(PanelScope, ItemRef)` so expansion survives undo and `ItemN` renumbering | doc 45 §2.4 |
| Inspector | §5 | doc 37 §3 |
| Problems and readiness | Stale badge (never blanked), Show on map, Why?, fix and fix-all as one group, the readiness coach as one dominant control, snooze, audited "Preview anyway" | doc 45 §2.6; I36-21; [validation-and-lints.md §11](validation-and-lints.md) |
| History | Clickable, filterable by origin and document; rewind or replay; pan to and pulse the changed area | doc 45 §2.2 item 11 |
| Script editor | Teller diagnostics, completions, hover, rename with references, path hover | doc 23; doc 31 §7 |
| Briefing, stringtable, screenplay | Text views with per-language columns and per-field staleness; dialogue as screenplay; `VariantSet`s show which variant each what-if state picks | doc 33 §7; doc 25 §9 |
| **Plotline** | The campaign graph: an engine-styled Flow view and a Theatre view on the island map; per-node transition tables whose conditions edit as CXL text or in the visual condition builder, two views of one AST (doc 19 §5; `AGENTS.md` glass box); rewiring edges by drag; socket and router meter (doc 19 §7.2); protagonist and mode lanes (I35-26); thread lanes and hub-card disclosure fields (I34-19); readiness overlay (I36-19); a toggleable "reads or sets variable" layer; Classic and Strategic complexity tiers (doc 19 §6.8) | doc 19 §6; D002 |
| **The Tote** | The state board: declared variables with "set in / read in", roster and pools, Path Explorer witness paths and the "states from which the ending is decided" query (I36-19), the what-if Playthrough in campaign-book style; the balance lab in v1.x | doc 19 §4, §6.4; D002 |
| Cinematics | v1: the Cutscene-node recipe editor; the timeline and director in v1.x | doc 32 §3; doc 39 |
| **Standing Orders** | Non-modal pane that opens in front from the help action (hover card "More", `?`, "What is this?"; F1 only where F1 is not a mode key: in the default Classic keymap F1 stays the Units mode, doc 34 le06); entry for the focused element; "explain this instance"; expert density in v1 (I36-33; D028) | doc 33 §3–§4 |
| **Drill** | Lesson runner: a step completes only when its validator predicate holds, checked by code, not Wilco; hint ladder, skip, test-out, resume; payoff-first order (I34-21; I35-DRILL) | doc 33 §5; D028 |
| Wilco | Chat with `/` dispatch; typed tool-call cards with `ItemRef` links (raw JSON on expand; a failed card opens itself); one-tap question cards, never modals; turn report | doc 21 §5; doc 38 §5 |
| Plan card and run panel | Steps, roles, bound setups, K and R, effects, cost estimate with its price date and the $0 alternative, assumption chips, the per-run check-ins choice (D024 item 3), Run / Edit / Cancel; progress by phase, admitted/defaulted/repaired counts, live cost with "cache saved", pause, stop, re-run a step, "continue with N more turns" | doc 38 §5.2–§5.3; doc 40 §6 |
| Decision inspector and run graph | Per generated element: capsule as sent (untrusted segments marked), menu, seed and pick, the model's "why" as untrusted text, checks and repairs, lens and pack versions, setup and cost, dependents, rules that did not run; a read-only run graph | doc 25 §9.1; doc 38 §5.3 |
| Preview log and run report | The jsonl stream, exit meanings, click to jump to the element; debrief card; standalone outcome display | [game-integration.md §7](game-integration.md) |
| Model Manager, pack and plugin manager | [agent-runtime.md §13](agent-runtime.md); [extensibility.md §8](extensibility.md): grants, egress log, kill switch, safe mode | D022; D007 |
| Mod-set manager | Mod sets, lock, drift report, "who serves this file", handoff bundle | [game-integration.md §3](game-integration.md) |
| Settings | Roles, autonomy, effort, realism level per mission and campaign, cost caps, offline mode, user-enabled download and feed sources, keymap profiles, target profile and capabilities; the split between user preferences and project settings (I34-05-06; doc 34 le16) | D008; D024 |

## 7. The glass-box contract

Every element the AI or a generator made is easy to **see**, **inspect** and **edit** with the same native editors as hand-made
content (`AGENTS.md`; D010):

- Any `ItemRef` opens one inspector card with provenance, its decision record, dependents, diagnostics and, for compiled content, the
  generated text side by side with the form that produced it (doc 31 §8.3).
- AI-made elements stay highlighted until the user has seen them ("new since you looked" is view state, never document state).
- One `NodeSummary` per element feeds Plotline cards, the Tote, the screenplay outline and Wilco's scope header (doc 45 §4.6).
- Pending proposals show as ghosts plus a semantic diff; nothing lands without its undo group.

## 8. Palette, action ids and keymaps

- The command palette uses pluggable locator sources: commands, catalog classes of the active mod set, entities by name or callsign,
  markers, Standing Orders entries, open diagnostics and goal aliases; an enum hit comes back with that value pre-set; unavailable
  entries are greyed with a one-click fix; recents are per user.
- Every shortcut is a `CommandSpec` binding with a **semantic action id** and per-OS keys; keymap profiles ship with "Classic" as the
  default; a shortcut-clash test runs per OS (I34-05-06; doc 34 le06).
- Availability is checked before a shortcut is consumed (doc 45 §2.8).

## 9. Frame discipline

1. **Logic** (`eframe::App::logic`): `Session::step` drains the command bus, plans, admits and commits, publishes the snapshot, drains
   background results and coalesces rebuilds ([commands-undo-history.md §11](commands-undo-history.md); doc 45 §2.9).
2. **UI** (`App::ui`): reads `DocCtx` and caches only; never validates, never plans, never mutates. Every edit is a queued command,
   traced with `Location::caller()` in debug builds.
3. Long lists allocate rows but paint and query only visible rows; aligned columns use layout statistics from the previous frame.
4. egui ids come from `(PanelScope, ItemRef)`, with a separate scope while a filter is active.
5. Forbidden: validation during `ui()`; locks around the document; the take-and-`expect` borrow trick (state is split into disjoint
   structs instead; doc 45 §2.9 item 5).

## 10. Threading and data flow

| Thread or pool | Owns or runs | Talks to the document by |
| --- | --- | --- |
| UI/logic thread (eframe) | The only `&mut ProjectStore`, history, view state, the bus receiver | Committing admitted batches |
| Worker pool (rayon, N−1 threads) | Validation shards, static map layers and draw lists, catalog and terrain indexing, Path Explorer and simulator, generator and lowering dry runs on a `Scratch`, heavy command plans, diffs | Returning revision-stamped results |
| Async runtime (one tokio runtime, 2–4 workers, on a background thread) | Workflow runtime tasks, provider streams, Wilco sessions, Preview supervision, the game link, T2 connectors and feeds, the MCP server, downloads, file watchers | Sending `Proposal<CommandBatch>` to the bus |
| Blocking pool | Saves and autosaves from a snapshot, journal flushes, model and pack installs, T1 WASM calls under fuel and epoch limits (v1.x) | Posting `Saved { doc, rev }` and similar completions |
| Child processes | The game (Preview) and the managed inference server; `kill_on_drop` and Windows Job Objects | Never; results arrive as events |

- **Single writer, many readers.** Snapshots are published as `Arc<Snapshot>` through an atomic swap; the document has no locks.
- **Channels:** the command bus is a bounded multi-producer channel (back-pressure on runtime commits); event channels (`RunEvent`,
  `AgentEvent`, `PreviewEvent`, job results, download progress) are drained every step, coalesced, and call `request_repaint`;
  replies are one-shot channels. Streamed text deltas are coalesced before the UI sees them.
- **Staleness:** a result whose read set is unchanged is applied; a validation result for an older revision is shown as stale; a
  proposal whose reads changed is re-verified (DG011).
- **Determinism:** `Clock`, `IdSource` and seeds are injected; fan-out joins in key order; concurrency 1 and 8 produce byte-identical
  documents and canonical journals (doc 38 AT-W9). Tests never sleep.
- **Fallback:** if snapshot publishing stalls frames on large missions, the store moves to a dedicated document thread behind the same
  `Session` API (doc 45 §2.9 item 4).

## 11. Performance budgets

Targets to validate in the proof of concept and the M2 benchmark, not measurements (doc 06 §4.10): a typical commit plus snapshot
publish under 2 ms on a 5,000-entity synthetic mission; overlay draw-list build under 4 ms at 1080p; GPU submit under 2 ms on an
integrated GPU for up to about 100k quads; at least 60 fps on an integrated GPU and 10 fps on WARP for the map stress spike; idle
CPU near zero.

## 12. Accessibility, locales, windows and branding

- **Accessibility:** AccessKit nodes for classic controls (a spike exit criterion, D016 item 6); Modern forms as the fallback path;
  keyboard entry everywhere; WCAG 1.4.13-style hover cards; reduced motion; text alternatives for every demo (doc 33 §7).
- **Locales:** the shell supports en, cs, pl, ru and de with per-field staleness (doc 33 §7). Standing Orders and Drill content ships
  in English first, and other locales are added as native reviewers join (owner, OWQ-14 (a)).
- **Windows:** windowed, borderless and monitor choice; the editor minimises when Preview launches; chat, script and diff panels can
  detach into deferred viewports (whether they share one wgpu device is [U]).
- **Branding (D002; decided by the owner in OWQ-07 as DG002 option A; `AGENTS.md` "Naming and Trademarks" amended to match).** The
  product name is **Plotroom**; "Mission & Campaign Editor for Arma: Cold War Assault / Operation Flashpoint" is a plain-text
  descriptor, not part of the name.

  | Surface | What it shows |
  | --- | --- |
  | Window title, installer product name and file name, application icon, binary, config and sidecar directory names | "Plotroom" alone, never the descriptor |
  | Splash screen, About box (and, outside the app, the README, website, release notes, store and forum listings) | "Plotroom" with the descriptor as plain text, no stylised marks or game logos, and the `README.md` non-affiliation disclaimer in the same place or one click away |
  | In-app body text (Preview labels, compatibility notes, target-profile badges) | Game names only to identify the game |

  The clearance search and the repository rename are release gates, not shell work (OWQ-07; roadmap §3 item 8).
- Preferences (theme, keymap, scaling, installs, providers, budgets, default autonomy) live in app data with versioned keys and tolerant
  decoding; project facts (target profile, mod set, realism) live in the sidecar (doc 34 le16).

## 13. Open questions

1. Default classic scaling mode (doc 06 OQ2) and support for GPUs without DX12 or Vulkan (doc 06 OQ8).
2. Whether AccessKit on the classic control tree is adequate, or Modern forms become the default in accessibility mode.
3. Whether deferred viewports can share one wgpu device.
4. *Decided 2026-09-27:* descriptor placement (OWQ-07; DG002 option A; §12).
5. *Decided 2026-09-27:* locales at first release: English content first (OWQ-14 (a); §12).
6. Names for Director features, realism levels and Economy mode: delegated to the design round's names table (DG037; OWQ-08 (a)), which
   the owner reviews before the first release.

## Verification notes

### Owner answers folded (2026-09-27)

- §12 now states OWQ-07's answer (DG002 option A, its placement table) and the amended `AGENTS.md` "Naming and Trademarks" section,
  re-read on 2026-09-27; it lists the splash with the About box among the descriptive surfaces, as DG002's decision record and
  `AGENTS.md` do. §12 and §13 state OWQ-14 (a) for locales and OWQ-08 (a) for names.
