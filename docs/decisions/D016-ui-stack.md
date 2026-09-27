# D016: UI stack: an egui shell and our own classic 2D renderer

> **Status:** baseline · **Decided by:** research (doc 06 recommendation) · **Decided:** 2026-09-26 · **Recorded:** 2026-09-27
> **Scope:** windowing, GUI toolkit, the classic editor view and UI tests. **Related:** D004, D017.
> **Revisit if:** any of doc 06 §7's five proof-of-concept spikes fails.

## Context

The editor must look and behave like the original (map, dialogs, fonts, lines) and also host modern panels: Wilco chat, workflow runs,
diffs, inspectors, Plotline and the Tote. The engine's 2D layer is small: textured quads with per-corner colours, convex polygons of up
to 32 vertices, 3-pixel lines drawn with a special texture, bitmap-glyph text and CPU clip rectangles, blended with straight alpha in
gamma space (doc 06 §2). Generic toolkits cannot reproduce that as-is.

## Decision

1. **eframe/egui** (0.36 at research time, on winit, wgpu and AccessKit) is the application shell and hosts every modern panel.
2. The **classic view** is drawn by our own small 2D renderer: a GPU-free `DrawList` and batcher crate mirroring the engine's primitives,
   executed by one **wgpu** pipeline into an offscreen texture that egui displays.
3. Classic UI resources (layouts, colours, fonts, textures) are read from the user's install at runtime and never committed (doc 05;
   APL-SA).
4. Modern-panel crates: `egui_dock` (docking), `egui_commonmark` (Markdown), `similar` (diffs); the code editor is `TextEdit` with a
   layouter fed by the script tokenizer.
5. **Tests in three layers**: deterministic `DrawList` snapshots; headless wgpu golden images on software adapters (WARP on Windows,
   lavapipe on Linux); `egui_kittest` for panels.
6. **De-risk first**: a three-week proof of concept with five spikes: colour and gamma in the composite, line and font fidelity, a
   ~50k-primitive map on an integrated GPU and on WARP, IME into a classic edit box, and AccessKit exposure of classic controls.

## Alternatives considered

| Option | Why not chosen (doc 06 TL;DR) |
| --- | --- |
| iced | Calls itself experimental; no AccessKit |
| Slint | UI compiled from a DSL; licensed GPL-3.0-only or royalty-free with attribution |
| Bevy with bevy_egui | A game engine with a fast breaking cadence |
| Vizia, Xilem/Masonry, Blitz, macroquad, SDL3 | C++ Skia dependency; experimental or beta; no IME or accessibility; a C library we do not need |
| Vector libraries (vello, femtovg, tiny-skia) | Anti-aliasing and no gouraud quads would change the classic look |

## Consequences

- OS floor Windows 10; backends DX12, Vulkan, Metal and GL 3.3+. Support for GPUs without DX12 or Vulkan is open (doc 06 OQ8).
- The default classic scaling mode ("Native" or "Authentic low-res") is polled with the community (doc 06 OQ2).
- UI and rendering code carries onboarding comments that teach the framework concepts in use (`AGENTS.md`, comment rules).
- Accessibility of classic controls is a spike exit criterion, not an afterthought.

## Sources

Doc 06 (TL;DR, §2, §6, §7, open questions); doc 05; `AGENTS.md` (commenting rules).
