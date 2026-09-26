# Rust UI and Rendering Stack for the Standalone CWA Mission Editor

Research date: 2026-09-26. Scope: which Rust windowing, GUI and 2D-rendering stack to use for a pixel-faithful
recreation of the Arma: Cold War Assault (CWA; originally Operation Flashpoint: Cold War Crisis, 2001) mission
editor. The same app must also host modern panels (AI agent chat, workflow progress, diffs) and a script editor.

Companion docs: `05-visual-fidelity-and-ui-resources.md` covers what the classic UI looks like, where the layout,
colour and font data live, and the asset licence (APL-SA). `07-file-formats-and-rust-crates.md` covers the parsers
this stack consumes (`ofp-config`, `ofp-paa`, `ofp-fxy`, `ofp-wrp`, `ofp-p3d`, `ofp-script`).
`03-original-editor-code-map.md` covers editor behaviour and `08-mission-preview-and-game-integration.md` covers
launching the game. This doc does not repeat them. It only covers the rendering, toolkit and test stack.

Epistemic tags: **[V]** verified in pinned code or on a fetched page (citation given); **[I]** inferred from
verified facts; **[U]** unknown or unverified, treat as a hypothesis. Code citations use
`owner/repo@sha:path#Lx-Ly`. `CWR` = `BohemiaInteractive/CWR@ffc61838b7`. The 2D renderer and UI code quoted
here is the same in `ofpisnotdead-com/CWR-CE@b67bf3bd62` (`EngineGL33_2D.cpp` is identical line for line, and
`UIMap.cpp` differs in 15 lines). Crate versions were read from the crates.io API on 2026-09-26.

## TL;DR

- **Recommendation [I]:** use **eframe/egui 0.36** (on winit 0.30, wgpu 30 and AccessKit) as the application shell
  and for all modern panels. Draw the classic editor with **our own small 2D renderer**: a GPU-free `DrawList` and
  batcher crate that mirrors Poseidon's primitives, executed by one **wgpu 30** pipeline into an offscreen texture.
  egui shows that texture as the central "classic view".
- **Poseidon's 2D layer is tiny [V]:** its whole 2D UI and editor map are built from textured quads with
  per-corner colours and UVs (`Draw2D`), convex polygons of up to 32 vertices (`DrawPoly`), lines drawn as
  3-px quads with a special 8x8 "line" texture (`DrawLine`), bitmap-glyph quads (`DrawText`) and CPU-side clip
  rectangles. The shader output is `vertex colour × texture`, sampled bilinearly, alpha-tested at ref 1 and
  blended with `SRC_ALPHA, ONE_MINUS_SRC_ALPHA` in gamma space. §2.
- **Generic toolkits cannot reproduce this as-is [V/I]:** it needs per-corner (gouraud) colours, per-draw
  clamp/repeat, *explicit* mip-level choice for terrain textures, and the line texture. egui-managed textures get
  no mipmaps on the wgpu backend (only `egui_glow`), and egui blends premultiplied alpha, while Poseidon blends
  straight alpha. Owning a small batcher and shader (our estimate: ~1,000 lines) is cheaper than bending a toolkit.
- **egui can host the classic view, but its own widgets cannot look authentic [V/I]:** egui text is TTF-only,
  and its styling is "not yet as powerful as say CSS". It does offer native-texture registration, wgpu paint
  callbacks and custom AccessKit nodes, which is all the hosting we need.
- **Modern panels [V]:** `egui_dock` 0.21 (docking), `egui_commonmark` 0.25 (Markdown chat), `similar` 3.2
  (diffs), and `TextEdit::code_editor()` with a custom `layouter` fed by the `ofp-script` tokenizer. The
  optional `egui_code_editor` 0.4.1 adds line numbers and completion.
- **Alternatives [V]:** iced 0.14 is the runner-up, but it calls itself "experimental software" and has no
  AccessKit. Slint 1.18 compiles its UI from a DSL at build time and is licensed "GPL-3.0-only OR royalty-free
  with attribution". Bevy 0.19 plus bevy_egui is a game engine with a ~3–5-month breaking cadence. Vizia needs C++
  Skia. Xilem/Masonry 0.4 is self-described experimental. Blitz is beta. macroquad has no IME or a11y. SDL3
  (sdl3-rs 0.20) is a C library we do not need. GPUI and Floem publish crates only rarely.
- **Vector libraries** (vello 0.10, femtovg 0.27, tiny-skia 0.12) draw anti-aliased paths well. They do not model
  gouraud quads, and anti-aliasing would change the classic look. We do not need them for the classic layer;
  egui's painter covers modern overlays. [I]
- **Test in three layers [V/I]:**
  1. Deterministic `DrawList` snapshots (`insta`).
  2. Headless wgpu golden images on software adapters: WARP on Windows and Mesa lavapipe on Linux. wgpu's own CI
     works this way.
  3. `egui_kittest` (AccessKit plus screenshots) for the egui panels.
- **Platform [V]:**
  - Window modes: borderless fullscreen and monitor choice via `ViewportCommand::Fullscreen` and `SetMonitor`.
  - Multi-window: deferred viewports.
  - Backends: DX12, Vulkan, Metal and GL 3.3+, plus a software adapter selected via `native_adapter_selector`.
  - OS floor: Windows 10 (Rust tier-1).
- **De-risk first (§7):** run a 3-week proof of concept with five spikes. The top risks are colour and gamma in the
  offscreen-to-egui composite, line and font fidelity, a ~50k-primitive map on an iGPU and on WARP, IME into a
  classic edit box, and AccessKit exposure of classic controls.

---

## 1. Context, terms and requirements

| Term | Meaning |
| --- | --- |
| **Poseidon** | Codename of the CWA engine released as GPL source (`BohemiaInteractive/CWR`), with an OpenGL 3.3 renderer (`engine/PoseidonGL33`) and SDL3 windowing. |
| **Display / control / Rsc class** | A UI screen and its widgets, declared in the game's `resource` config as `Rsc*` classes with normalised `x,y,w,h`, `type` (`CT_*`), `style` (`ST_*`), colours and fonts (doc 05 §2–3). |
| **2D viewport / UI rect** | The pixel rectangle into which normalised 0..1 UI coordinates map (`Width2D/Height2D`). |
| **FXY / PAA** | Legacy bitmap-font glyph table and BI texture format. Font pages are `<font>-NN.paa`. |
| **DrawList** | *Our* proposed ordered list of Poseidon-style 2D draw commands (painter's order). It is GPU-free and serialisable. |
| **Batcher** | Converts a DrawList into vertex/index buffers grouped by texture and sampler state, so the GPU gets a handful of draw calls. |
| **egui / eframe** | egui: immediate-mode Rust GUI (widgets are re-declared each frame). eframe: its app framework (window, event loop, renderer). |
| **wgpu / winit** | wgpu: safe Rust GPU API over DX12, Vulkan, Metal and GL. winit: Rust windowing and input library. |
| **AccessKit** | Cross-platform accessibility tree that exposes widgets to screen readers. |
| **IME** | Input Method Editor: OS text-composition UI for CJK and similar languages. It needs "composition" events and a caret rectangle. |
| **Golden image** | Reference screenshot; a test renders and compares within a tolerance. |
| **Software adapter** | CPU rasteriser exposed as a GPU: Microsoft WARP (Windows) or Mesa llvmpipe/lavapipe (Linux). |

Requirements this stack must meet:

| # | Requirement | Source |
| --- | --- | --- |
| R1 | Pixel-faithful classic chrome (dialogs, lists, combos, edits, sliders, buttons, bitmap fonts, tiled textures) | user brief; doc 05 |
| R2 | UI data-driven from the user's `resource` config at **runtime**, not compiled in | doc 05 §2 (layout numbers live only in game data) |
| R3 | 2D terrain map with sea gradient, textured cells, contours, forests, roads, icons, grid; smooth zoom and pan | §2.5 |
| R4 | Windowed, borderless fullscreen, monitor choice; resizable; DPI-aware | user brief |
| R5 | Cross-platform: Windows first, then Linux and macOS; CI matrix on all three | `AGENTS.md` (this repo) "Local Repo-Specific Rules" |
| R6 | Modern panels: agent chat, workflow progress, diffs, inspector; a decent SQS/SQF/init-line editor with IME | user brief |
| R7 | Headless rendering for golden tests in CI; no proprietary data in fixtures | `AGENTS.md` Evidence Rule and fixture-legality rules |
| R8 | Accessibility; multi-window (detachable panels) desirable | user brief |
| R9 | No `unsafe` in our crates; permissive or GPL-compatible dependencies; files ≤ ~600 lines | `AGENTS.md` |
| R10 | Runs on low-end GPUs; usable CPU fallback | user brief |

---

## 2. Ground truth: how Poseidon draws the editor

### 2.1 Coordinates and scaling [V]

- Screen and pixel coordinates use `Point2DAbs/Rect2DAbs` (absolute window px) and `Point2DPixel/Rect2DPixel`
  (px inside the 2D viewport). UI coordinates use `Point2DFloat/Rect2DFloat` (0..1 of the viewport)
  (`CWR:engine/Poseidon/Graphics/Core/Engine.hpp#L184-L277`). Controls store `_x,_y,_w,_h` as those floats
  (`CWR:engine/Poseidon/UI/Controls/UIControlsBase.hpp#L139-L177`).
- `Width2D/Height2D/Left2D/Top2D` come from the aspect settings' `uiTopLeft*/uiBottomRight*` fractions of the
  window (`CWR:engine/Poseidon/Graphics/Core/Engine.cpp#L113-L132`). The remaster can centre a UI band for wide
  windows (`CWR:engine/Poseidon/UI/Settings/AspectRatio.cpp#L85-L117`; policy details in doc 05 §4).
- Pixel snapping is explicit. Controls compute `xx = toInt(x*w) + 0.5` and `ww = toInt((w+x)*w) - xx`
  (`CWR:engine/Poseidon/UI/Controls/UIControls.cpp#L378-L387`). Text positions are also snapped to
  `toInt()+0.5` (`CWR:engine/Poseidon/Graphics/Rendering/Draw/FontDraw.cpp#L46-L49`). Our renderer must
  reproduce these roundings bit for bit, or 1-px bevels will blur or shift.

### 2.2 The primitive set [V]

The backend contract is `IGraphicsEngine` (`CWR:engine/Poseidon/Graphics/IGraphicsEngine.hpp#L95-L101`) plus
text helpers on `Engine` (`CWR:engine/Poseidon/Graphics/Core/Engine.hpp#L695-L715`). A tally of `GEngine->`/
`GLOB_ENGINE->` calls in `UI/Controls` and `UI/Map` shows that 2D UI code uses only `Draw2D`, `DrawLine`,
`DrawPoly`, `DrawText[F]`, `DrawTextVertical` and `GetTextWidth[F]`. `Draw3D`, `DrawLine3D` and `DrawText3D`
appear only in the 3D controls (`UIControls3D.cpp`, `UIControlsHTML.cpp`), which the editor map screen does not
use (doc 05 §2.3). Two caveats, checked 2026-09-26: (a) the generic `ControlsContainer::OnDraw` clears Z and
switches to a 3D camera whenever a display owns 3D objects
(`CWR:engine/Poseidon/UI/Map/UIContainers.cpp#L636-L669`). The in-game `DisplayMap` creates watch and compass
objects (`UIMapDisplay.cpp#L870-L894`), but `DisplayArcadeMap` has no `OnCreateObject` override
(`UIMap.hpp#L705-L764`). Whether its `RscDisplayArcadeMap` config declares any objects is **[U]**. (b) In CWR,
`DrawTextVertical` is an obsolete stub that only calls `Fail("Obsolete…")`
(`CWR:engine/Poseidon/Graphics/Rendering/Draw/FontDraw.cpp#L542-L546`), so it draws nothing.

| Primitive | Semantics (GL33 backend) | Citation |
| --- | --- | --- |
| `Draw2D(Draw2DPars, rect, clip)` | Axis-aligned quad. It has **4 corner colours** (`colorTL/TR/BL/BR`), **4 corner UVs**, texture + mip (`MipInfo`) and spec flags. The clip is done **on the CPU**: the rect is shrunk and the UVs are re-interpolated, and there is no scissor. | `Engine.hpp#L75-L86`; `CWR:engine/PoseidonGL33/EngineGL33_2D.cpp#L7-L110` |
| `DrawPoly(mip, verts, n, clip, spec)` | Convex polygon (triangle fan), **n ≤ 32**. Each vertex has its own colour and UV. It gets trivial rejection plus Sutherland–Hodgman clipping on the CPU against the clip rect. | `EngineGL33_2D.cpp#L169-L280` |
| `DrawLine(line, c0, c1, clip)` | Converted to a **3-px-wide quad** textured with the preloaded `textureLine` ("8x8" per a code comment; the file name comes from the remaster's `CfgPreloadTextures`). It is forced to mip level 1 (4x4). `v` spans 0.25→1 across the width and `u` spans 0→0.1 along the length, with clamp on both axes. Colours are interpolated c0→c1. It is **not** a hairline, so the visible profile comes from that texture. | `EngineGL33_2D.cpp#L112-L167`; `CWR:engine/Poseidon/Graphics/Textures/TexturePreload.cpp#L42-L47` |
| `DrawText(pos, sizeEx, clip, font, color, text)` | Bitmap path: one `Draw2D` per byte. `sizeH = Height2D·sizeEx/600/fontHeight`, width is aspect-corrected, advances are rounded with `toInt`, and chars ≤ 32 advance by the width of **'o'**. TTF path: `DrawTextFreeType`. | `FontDraw.cpp#L55-L139` |
| Clip rect | Every primitive takes a clip rect (map: `_clipRect`; default "infinite" `Rect2DClipPixel`). | `Engine.cpp#L131-L132`; `UIMap.cpp#L1369` |

Spec flags that matter for 2D: `DefSpecFlags2D = NoZBuf|IsAlpha|ClampU|ClampV|IsAlphaFog`
(`Engine.hpp#L136`). Tiled backgrounds switch to `NoClamp` (repeat) (`UIControls.cpp#L420-L426`). Textured
terrain cells use the per-texture `GLOB_LAND->ClampFlags(id)` plus `DetailTexture`
(`CWR:engine/Poseidon/UI/Map/UIMap.cpp#L1335`). The `NoClamp` at `UIMap.cpp#L1356` applies only to the
untextured merged-block path. Brush-filled ellipses and rectangles use `NoClamp2D`, with UVs of one texel per
screen pixel anchored to the map origin, so the pattern pans with the map
(`CWR:engine/Poseidon/UI/Map/UIMapExt.cpp#L176`, `#L212-L269`).

### 2.3 Batching and shading [V/I]

- Each 2D call goes through `SwitchRenderMode(RM2DTris)` and `QueuePrepareTriangle(mip, spec)`. The latter
  allocates or reuses a queue keyed by **texture, mip level and spec**. `Queue2DPoly` appends to it
  (`EngineGL33_2D.cpp#L102-L109`, `CWR:engine/PoseidonGL33/EngineGL33_Queue.cpp#L270-L276`). So the original
  already batches by texture state. [V]
- The pixel shader computes `vColor * texture(tex0, uv)` plus a specular term. The 2D vertices carry a black
  specular (`0xff000000`) (`CWR:engine/PoseidonGL33/EngineGL33_Shaders.cpp#L237-L239`, `EngineGL33_2D.cpp#L63-L81`).
  That this is the 2D pixel shader is inferred from the shared uniform layout and is **[I]**.
- Alpha blending is `glBlendFuncSeparate(SRC_ALPHA, ONE_MINUS_SRC_ALPHA, ONE, ZERO)`, i.e. straight alpha
  (`CWR:engine/Poseidon/Graphics/Core/GLBlendState.hpp#L24-L28`). A grep for `FRAMEBUFFER_SRGB|GL_SRGB` over
  `engine/` finds nothing. **[V]** The engine therefore blends in gamma space on non-sRGB targets. **[I]**
  Our pipeline must do the same: `Rgba8Unorm` textures and target, no sRGB views.
- Other 2D state, verified 2026-09-26 **[V]**:
  - Sampling is bilinear unless the `PointSampling` bit is set, and no UI code sets it
    (`CWR:engine/Poseidon/Graphics/Rendering/BuildRenderPassDescriptor.hpp#L50`).
  - Every 2D spec we checked carries `IsAlphaFog`: `DefSpecFlags2D`, `DrawLine`, the text path, `ST_BACKGROUND`,
    the map fields, sea and forests, and `NoClamp2D`. That flag selects `AlphaBlend` plus an alpha *test* with
    ref 1, so fully transparent fragments are discarded (`BuildRenderPassDescriptor.hpp#L124-L132`; shader
    discard at `EngineGL33_Shaders.cpp#L307`).
  - `BeginScreenPass` resets the `constColor` tint to white (`EngineGL33_Queue.cpp#L368-L373`).
  - The descriptor defaults to back-face culling with CW front faces
    (`CWR:engine/Poseidon/Graphics/Rendering/RenderPassDescriptor.hpp#L186-L187`). The 2D callers we sampled
    (`Draw2D`, forest triangles, ellipse wedges) all use one winding. So culling probably never drops a 2D
    primitive **[I]**. Our pipeline can disable culling, with a debug assertion on winding.
  - A full-frame gamma post-pass `pow(c, 1/gamma)` covers the game and HUD, but not the dev overlay. It is a
    no-op at the default gamma 1.0 (`EngineGL33_Shaders.cpp#L1622-L1659`,
    `EngineGL33_VertexBuffer.cpp#L577-L584`, `EngineGL33.cpp#L226`). An optional render-scale/SSAA target is
    also resolved into the default framebuffer at that point (render scale defaults to 1.0,
    `EngineGL33.hpp#L419`). Reference screenshots must therefore be taken with gamma 1.0 and render scale 1.0.

### 2.4 Text [V]

- FXY is a flat array of 6 LE `u16` per glyph: char, page, x, y, w, h. Pages are `<name>-NN.paa`
  (`CWR:engine/Poseidon/Graphics/Rendering/Draw/FontData.cpp#L34-L92`). The stored `w`/`h` are one larger than
  the glyph: the parser subtracts 1 and rounds the atlas cell up to the next power of two (`#L63-L73`). Glyphs start at char 32
  (`Font.hpp#L32`). The bitmap path reads **8-bit code-page bytes**, so Unicode needs a transcode step (code
  pages in doc 07 §10).
- CWR first maps legacy font names (`tahomab`, `garamond`, `couriernewb`, …) to `Fonts\cwr_*.ttf` via FreeType,
  with per-row metric tuning (`renderPx`, `widthScale`, `baselineOffset`, `letterSpacing`). It falls back to FXY
  otherwise (`CWR:engine/Poseidon/Graphics/Rendering/Draw/Font.cpp#L37-L60`, `#L277-L360`).
  Our text system therefore needs **both** a bitmap-atlas path and a TTF path with the same metric table.
- CWR itself uses Dear ImGui for developer overlays (`CWR:engine/Poseidon/Dev/Debug/DebugOverlay.cpp`). This
  separates authentic chrome from modern tooling UI, the same split we propose.

### 2.5 The map control [V]

The map layer order is in doc 05 §5.2. The facts that matter for rendering:

- **Level of detail is resolution-independent.** The code merges cells so each drawn block spans at least N
  "points" of an 800-point reference. N is `ptsPerSquareSea = 6`, `Txt = 8`, `CLn = 8`, `For = 6`,
  `ForBor = 6`, `Road = 2` and `Obj = 10`, with object LOD at 15 (`UIMap.cpp#L613-L630`, `#L743-L942`).
- **Terrain fields** are `Draw2D` quads with 4 per-corner colours and height-dependent alpha. A block's texture
  is drawn only when the block is a single cell (`iStep == 1`). It then uses an **explicitly chosen mip level**,
  `7 - floor(log2(max block px))` clamped to 0..8 (`UIMap.cpp#L816-L826`, `#L1318-L1336`, `#L1368`). Merged
  blocks are untextured, and each corner takes its texture's average colour ×0.75 (`#L1337-L1357`).
- **Sea** is a per-corner alpha gradient on untextured quads (`#L1374-L1443`). **Forests** are solid squares or
  3-vertex `DrawPoly` triangles (`#L1488-L1578`).
- **Ellipses and area markers** are fans of separate 3-vertex `DrawPoly` wedges, one call per wedge, with
  `nSteps = ceil(2π·a/5 px)` clamped to 6..720
  (`UIMapExt.cpp#L178-L279`). Icons are `Draw2D`, or a rotated 4-vertex `DrawPoly` when an azimuth is set
  (`UIMap.cpp#L495-L574`). **Grid** lines and labels are drawn on all four edges (`#L1971-L2045`). A cursor
  crosshair is drawn with 4 lines (`#L2158-L2199`).
- **Everything is redrawn every frame** in immediate mode (`CStaticMap::OnDraw`, `#L2047-L2201`).
- **Primitive budget [I]:** a full-window map yields at most about (800/6)×(600/6) ≈ 13k blocks per 6-point layer,
  and ≈ 7.5k per 8-point layer. Objects add more at close zoom. Expect **10^4–10^5 quads per frame** in the worst
  case. That is trivial for a batched GPU path and too heavy for per-frame CPU tessellation of anti-aliased paths.

### 2.6 Control recipes [V]

The controls use the same primitives with pixel offsets. `ST_BACKGROUND` is a tiled `DialogBackground` texture at
1 texel per pixel (`SetU(0, ww*invW)`) plus a 6-step bevel of `DrawLine`s. `ST_FRAME` cuts the text into the top
edge. `ST_TITLE_BAR` insets lines at 5–8 px. The code is in `UIControls.cpp#L376-L577`, and the bevel macros
`DrawLeft/DrawTop` are in `CWR:engine/Poseidon/UI/Controls/UIControlsExtShared.hpp#L24-L25`. Per-control keys
and looks are tabulated in doc 05 §3.3.

### 2.7 Fidelity requirements this imposes on our renderer [I]

1. Per-corner and per-vertex colours with textures (gouraud), not only solid fills or gradients.
2. Per-draw wrap mode (clamp or repeat) and **explicit mip-level selection** from the PAA mip chain. `ofp-paa`
   must therefore expose **all mip levels**, not just level 0 (a request to doc 07's plan).
3. Lines as 3-px quads sampling a 4x4 line texture. We need the real `textureLine` from the install, or an
   authored equivalent for the fallback theme.
4. CPU clipping identical to `Clip2D`: rect shrink with UV re-interpolation, and polygon clipping with ≤ 32
   vertices. This keeps fractional-edge behaviour identical, and avoids scissor state changes that would break
   batches.
5. Gamma-space straight-alpha blending with bilinear sampling and an alpha test at ref 1; `+0.5` snapping;
   `toInt` glyph advances; the 'o'-width space.
6. Text from FXY/PAA atlases (legacy) **and** TTF with CWR's metric table (remaster), plus a Unicode fallback
   for characters outside the 8-bit code page.

---

## 3. Candidates (versions as of 2026-09-26)

### 3.1 Versions and maintenance [V]

| Crate | Latest (date) | Licence | Notes |
| --- | --- | --- | --- |
| `egui` / `eframe` / `egui-wgpu` / `egui_kittest` | 0.36.2 (2026-09-08) | MIT OR Apache-2.0 | Breaking minors every ~2–3 months (0.34 Mar, 0.35 Jun, 0.36 Aug 2026). eframe default features include `accesskit`, `wgpu`, `winit`, `x11`, `wayland`. |
| `egui-winit` 0.36.2 → `winit` | `^0.30.13` | Apache-2.0 (winit) | winit 0.31 is in beta (0.31.0-beta.3, 2026-09-04). |
| `wgpu` | 30.0.1 (2026-08-22) | MIT OR Apache-2.0 | Majors in 2025-12 (28), 2026-03 (29) and 2026-07 (30). egui-wgpu 0.36 requires `wgpu ^30`. |
| `bevy` / `bevy_egui` | 0.19.1 (2026-08-13), 0.20.0-rc.1 (2026-09-15) / 0.42.0 | MIT OR Apache-2.0 / MIT | iron-curtain pins Bevy 0.18.1 (`iron-curtain-engine/iron-curtain@7b7fac7fa5:crates/ic-render/Cargo.toml#L15`). |
| `iced` | 0.14.0 (2025-12-07) | MIT | README: "Iced is currently experimental software". wgpu renderer plus tiny-skia software fallback. |
| `slint` | 1.18.1 (2026-09-21) | `GPL-3.0-only OR LicenseRef-Slint-Royalty-free-2.0 OR LicenseRef-Slint-Software-3.0` | 1.18.1 has `unstable-wgpu-29`/`unstable-wgpu-30` and `renderer-vello` features (crates.io). Which release added them, and how mature the Vello renderer is, are unverified. |
| `vizia` | 0.4.0 (2026-04-23) | MIT | Renders with Skia (C++) via rust-skia; CSS-like styling; AccessKit. |
| `xilem` / `masonry` | 0.4.0 (2025-10-29) | Apache-2.0 | README: "An experimental Rust architecture for reactive UI"; Vello + wgpu. |
| `blitz-dom` (Dioxus native) | 0.3.0-beta.2 (2026-08-24) | MIT OR Apache-2.0 | README: "currently in a beta state". |
| `macroquad` / `miniquad` | 0.4.16 (2026-07-30) / 0.4.11 (2026-06-03) | MIT OR Apache-2.0 | Game-oriented; own GL/Metal layer. |
| `sdl3` (sdl3-rs) | 0.20.0 (2026-09-07) | MIT | Bindings to the C SDL3 library (which CWR itself uses). |
| `gpui` / `floem` | 0.2.2 (2025-10-22) / 0.2.0 (2024-11-14) | Apache-2.0 / MIT | Sparse crates.io releases. |
| `vello` / `vello_cpu` / `vello_hybrid` | 0.10.0 (2026-08-14) / 0.2.0 / 0.2.0 (2026-08-07) | Apache-2.0 OR MIT | README: "Vello CPU is currently overall more mature". The hybrid renderer is being renamed `vello_gpu` (a 0.1.0 name-reservation crate exists). |
| `femtovg` | 0.27.0 (2026-08-31) | MIT OR Apache-2.0 | nanovg-style canvas; GL ES 3 and wgpu backends; "no custom shaders". |
| `tiny-skia` | 0.12.0 (2026-02-02) | BSD-3-Clause | CPU Skia subset. |
| `cosmic-text` / `glyphon` / `parley` | 0.19.0 / 0.12.0 / 0.11.1 | MIT/Apache (glyphon adds Zlib) | cosmic-text: HarfRust shaping, swash rasterisation. glyphon 0.12 requires `wgpu ^30` and `cosmic-text ^0.19`. |
| `accesskit` | 0.25.1 (2026-09-25) | MIT OR Apache-2.0 | |
| `egui_dock` / `egui_commonmark` / `egui_code_editor` | 0.21.1 / 0.25.0 / 0.4.1 | MIT / MIT OR Apache-2.0 / MIT | All released Aug 2026. |
| `similar` / `insta` | 3.2.0 / 1.48.0 | Apache-2.0 | Diffs / snapshot tests. |

### 3.2 Fit matrix [I, based on §2 and the facts above]

`+` good, `~` partial or needs work, `-` poor. "Classic 2D" means it can execute our DrawList with gouraud
colours, per-draw wrap and explicit mips at pixel precision.

| Option | Classic 2D | Dense tool panels | Text edit + IME | Code editor | A11y | Headless tests | Multi-window | Maturity/cadence | Licence/deps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **eframe/egui + own wgpu batcher** | + (own pipeline) | + | + | ~ (TextEdit + layouter; egui_code_editor) | + (AccessKit) | + (kittest + headless wgpu) | + (viewports) | ~ (breaking minors) | + |
| winit + wgpu + egui-winit/egui-wgpu, no eframe | + | + | + | ~ | + | + | ~ (manual) | ~ | + |
| iced 0.14 + `shader` widget | + (wgpu `Shader` widget) | ~ | + (IME in 0.14) | ~ (TextEditor + highlighter) | - (no AccessKit) | + (headless mode) | + | - (experimental; ~yearly releases) | + |
| Slint 1.18 | ~ (wgpu texture import) | ~ | + | - | + | + (software renderer) | ~ | + | ~ (GPL-3.0-only or attribution licence); - for runtime rsc (build-time DSL) |
| Bevy 0.19 + bevy_egui | ~ (ECS render graph) | + (via egui) | + (via egui) | ~ | ~ | ~ | ~ | - (breaking every ~3–5 months; heavy compile) | + |
| Vizia 0.4 | ~ | ~ | + | - | + | ? | ? | ~ | - (C++ Skia build) |
| Xilem/Masonry 0.4 | ~ (Vello) | ~ | ~ | - | + | ? | ? | - (experimental) | + |
| Blitz (Dioxus native) | - (HTML/CSS) | ~ | ~ | - | ? | ? | ? | - (beta) | + |
| macroquad/miniquad | + | - | - | - | - | ~ | - | ~ | + |
| SDL3 + own everything | + | - (build it) | ~ | - | - | ~ | + | + | ~ (C library) |

### 3.3 egui in depth: can it look retro, and can it host our widgets?

**Can egui's own widgets look authentic? No.** [V/I]

- Styling covers "colors, spacing, fonts and sizes"; the README says this "is not yet as powerful as say CSS"
  (<https://raw.githubusercontent.com/emilk/egui/main/README.md>). [V]
- Fonts are TTF/OTF, rasterised by Skrifa + vello_cpu since 0.34, which "enable font hinting". [V] FXY bitmap
  glyph pages cannot enter egui's text system. [I]
- egui's tessellator feathers edges for anti-aliasing. Poseidon's chrome is built from textured 3-px line quads
  and snapped 1-px geometry. [I]
- A "retro-ish" egui theme (square corners, olive and grey palette, an OFL Tahoma-like font) is possible and
  useful as a *modern* theme, but it is not the classic look. [I]

**Can egui host custom retro widgets? Yes, in three ways.** [V]

1. `Painter` with `Shape::Mesh` and user textures (`Context::load_texture(name, image, TextureOptions)`).
   `TextureOptions` offers `NEAREST`, `LINEAR` and `*_REPEAT`. However, its `mipmap_mode` "may not be available
   on all backends (currently only `egui_glow`)"
   (<https://docs.rs/epaint/latest/epaint/textures/struct.TextureOptions.html>, epaint 0.36.2). One workaround is
   to register each mip level as its own native texture view (option 3). But egui's pipeline blends
   premultiplied alpha (`One, OneMinusSrcAlpha`) and optionally dithers, so this path would still differ from
   Poseidon's straight-alpha blending. **[V/I]**
2. `egui_wgpu::Callback` (`CallbackTrait::prepare`, `finish_prepare`, `paint`) runs arbitrary wgpu commands inside
   egui's render pass (<https://docs.rs/egui-wgpu/latest/egui_wgpu/trait.CallbackTrait.html>).
3. `egui_wgpu::Renderer::register_native_texture(device, view, filter)` (or `…_with_sampler_options`) shows a
   texture we rendered ourselves as an ordinary egui image. The docs state that it requires an `Rgba8Unorm`
   texture (<https://docs.rs/egui-wgpu/latest/egui_wgpu/struct.Renderer.html>). The `…_with_sampler_options`
   variant takes a full `wgpu::SamplerDescriptor`. eframe exposes `RenderState {
   device, queue, target_format, renderer: Arc<RwLock<Renderer>>, … }`
   (<https://docs.rs/egui-wgpu/latest/egui_wgpu/struct.RenderState.html>).

**Recommended hosting: option 3, an offscreen texture.** [I] It decouples the classic renderer from egui's pass
format and MSAA settings. The same code path serves headless golden tests. It lets us cache the classic frame and
redraw it only when dirty. It also enables "authentic low-res" modes such as rendering at 800x600 and upscaling.
Option 2 is the fallback if the extra copy or a colour-space mismatch (§6) becomes a problem.

**Other egui facts that matter [V]:**

- `ViewportCommand::Fullscreen(bool)` "Turn borderless fullscreen on/off", `SetMonitor(usize)`, `IMERect`,
  `IMEAllowed`, `Screenshot` (egui 0.36.2 docs).
- Multiple native windows are supported "by the native `eframe` backend, but not the web one". Deferred viewports
  "are repainted independently".
- `Context::accesskit_node_builder(id, |node| …)` lets custom widgets publish AccessKit nodes.
- `TextEdit::code_editor()` and `TextEdit::layouter(&mut dyn FnMut(&Ui, &dyn TextBuffer, f32) -> Arc<Galley>)`
  exist in 0.36.
- The README says: "New releases will have breaking changes", and AccessKit "currently implements the native
  accessibility APIs on Windows and macOS". Linux coverage is **[U]**.
- `WgpuSetupCreateNew` has `instance_descriptor`, `power_preference`, `native_adapter_selector` and
  `device_descriptor`, which lets us choose the backend and a software adapter.

Precedent [V]: the Iron Curtain SDK design takes the same dual-UI route ("`ic-render` viewport + `egui` panels";
"egui provides all of these out of the box")
(`iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/architecture/sdk-editor.md#L43-L59`). Its
switchable-theme decision D032 (`…:src/decisions/09c/D032-ui-themes.md`) is the model for our Classic vs Modern
chrome.

### 3.4 Notes on the alternatives

- **Raw winit + wgpu + egui-winit/egui-wgpu (no eframe):** the same rendering story plus surface, event-loop and
  AccessKit boilerplate. It is the escape hatch in §5, so keep our crates free of `eframe` types. [I]
- **iced 0.14.** It has good architecture (Elm-style) and a wgpu `shader` widget
  (<https://docs.rs/iced/0.14.0/iced/widget/shader/index.html>). The 0.14 release notes list "Input method
  support" and "Headless mode testing". `TextEditor` is older: it arrived in 0.12. Against it: it calls itself
  experimental, and releases are infrequent (0.13 in 2024-09, 0.14 in 2025-12). There is no AccessKit
  dependency in `iced` 0.14.0 or `iced_winit` 0.14.0 (crates.io dependency lists). [V]
- **Slint 1.18.** It is mature, accessible, has a software renderer, and supports wgpu 30 texture import and
  underlay rendering. But UI is authored in `.slint` compiled at build time. Our classic UI must come from
  runtime rsc data, and the modern panels need an ecosystem (docking, Markdown, code editing) that egui has and
  Slint lacks. The licence is GPL-3.0-only, or royalty-free with an AboutSlint or attribution-badge requirement
  (<https://slint.dev/terms-and-conditions>). GPL-3.0-only would also pin the combined binary to GPLv3. [V/I]
- **Bevy 0.19 + bevy_egui.** Bevy 0.19 added text input and more Feathers "editor tooling" widgets (release
  coverage). But it is a game engine: an ECS schedule, a render graph and heavy compiles. It ships breaking
  releases roughly every 3–5 months: 0.18.0 on 2026-01-13, 0.19.0 on 2026-06-19 and 0.20.0-rc.1 on 2026-09-15. We would still use egui for
  panels. The only synergy, with iron-curtain, is conceptual. [V/I]
- **SDL3 (sdl3-rs 0.20)** would match CWR's platform layer (`IGraphicsEngine.hpp#L47-L84` mentions SDL3 displays
  and text input), but it adds a C library and no GUI. It is only a §5 fallback for winit IME/Wayland defects. [I]
- **macroquad**, **Vizia**, **Xilem/Masonry**, **Blitz**, **GPUI**, **Floem**: rejected for the reasons in §3.2.
  Revisit Xilem/Masonry when it drops the experimental label. [I]

### 3.5 2D vector and text libraries

- **vello / vello_cpu / vello_hybrid, femtovg, tiny-skia:** these are path renderers with anti-aliasing,
  gradients and image patterns. None exposes per-vertex-coloured textured triangles, which is the core of
  `Draw2D`/`DrawPoly`. Their anti-aliased strokes would *differ* from Poseidon's textured-quad lines. They are
  not needed for the classic layer. Possible later uses: SVG export of the map (a modern equivalent of the
  engine's WMF exporter, doc 05 §10), or CPU thumbnails. [I]
- **Text, classic view:** port `FontDraw.cpp` onto our own glyph atlas: FXY pages from PAA, or TTF glyphs
  rasterised with **cosmic-text 0.19** (swash) using CWR's metric table. Glyphs become ordinary textured quads in
  the same DrawList, so they interleave correctly with other primitives. glyphon 0.12 is a good wgpu text
  renderer, but it draws in its own pass. It would break painter's order unless text were always on top. We do
  not recommend it for the classic layer. [I]
- **Text, modern panels:** use egui's built-in text. [V]

### 3.6 Modern-panel and editor components [V/I]

| Need | Choice | Notes |
| --- | --- | --- |
| Docking and tabs | `egui_dock` 0.21.1 | Detachable to OS windows via egui viewports. [I] |
| Agent chat (Markdown, code blocks) | `egui_commonmark` 0.25.0 | Streaming text appends; code blocks can reuse our highlighter. [I] |
| Workflow progress | plain egui (progress bars, spinners, collapsing trees) | Reactive repaint only while running. [I] |
| Diffs (script text, `mission.sqm`) | `similar` 3.2.0 → egui rendering | A structured, per-entity mission diff can also be shown as ghost overlays on the classic map (§4.5). [I] |
| SQS/SQF/init-line editor | `TextEdit::code_editor()` + `layouter` fed by `ofp-script` tokens (doc 07 §11). Optional: `egui_code_editor` 0.4.1 (line numbers, completion; README: "Usage as lexer without egui") | Completions come from the per-target command table (doc 07). Add an "Open in external editor" button with a file watch. |
| Inspector and forms | egui + `egui_extras` tables (version not checked) | Also the "Modern forms" accessible alternative to classic dialogs (§4.7). |

HEMTT's SQF crates are GPL-2.0 according to GitHub (whether "-only" or "-or-later" is **[U]**). Do not link them
into a GPLv3 binary until that is checked; doc 07 already plans our own `ofp-script`.

---

## 4. Recommended architecture

### 4.1 Layers

```text
┌──────────────────────────── ofp-editor (bin, eframe App) ─────────────────────────────┐
│ Modern panels (egui): agent chat │ workflow │ diff │ inspector │ script editor (dock) │
│ Classic view widget: shows TextureId of offscreen target; maps pointer/keys/IME →     │
│   classic events; publishes AccessKit nodes for classic controls                      │
└───────────────┬───────────────────────────────────────────────┬──────────────────────┘
      edit commands (undo/redo)                           "frame dirty" / events
                ▼                                               ▼
   mission model + command bus            ofp-ui-classic  (retained control tree, focus,
   (docs 03/04; also used by the           CT_* behaviours, dialogs; normalised coords)
    AI agent — never simulated clicks)    ofp-map2d       (map layers, LOD, editor overlay)
                                                     │ emit Poseidon-style primitives
                                                     ▼
                                          ofp-draw2d  (DrawList → CPU clip → batches; no GPU)
                                                     ▼
                                          ofp-gpu     (wgpu pipeline, texture/mip cache,
                                                       offscreen target, headless readback)
   inputs: ofp-rsc (Rsc → DisplaySpec/ControlSpec), ofp-fonts (FXY/TTF metrics + atlas),
           ofp-config, ofp-paa (all mips), ofp-fxy, ofp-wrp, ofp-p3d, ofp-script (doc 07)
```

| Crate | Owns | Depends on | GPU? |
| --- | --- | --- | --- |
| `ofp-rsc` | Typed `DisplaySpec`/`ControlSpec` (`Idd`, `Idc` newtypes, `ControlType`, `Style` bits, colours, font refs); inheritance resolved; permissive on unknown keys | `ofp-config` | no |
| `ofp-fonts` | Font metrics (FXY table, CWR TTF metric rows), code-page mapping, glyph atlas packing (CPU images) | `ofp-fxy`, `ofp-paa`, `cosmic-text` | no |
| `ofp-ui-classic` | Control tree (arena + `ControlId`), per-type state machines (edit caret/selection, listbox, combo dropdown, slider, toolbox), focus, message boxes; `fn draw(&self, &mut DrawList)` ports each `OnDraw` | `ofp-rsc`, `ofp-fonts`, `ofp-draw2d` | no |
| `ofp-map2d` | Pure `(terrain, map metadata, style, camera) → DrawList` layers + editor overlay + hit-testing | `ofp-wrp`, `ofp-p3d`, `ofp-draw2d` | no |
| `ofp-draw2d` | `DrawList`, `Clip2D` port, line→quad and text→glyph expansion, batching, vertex packing | none (maybe `insta` in dev) | no |
| `ofp-gpu` | WGSL shader, pipelines (alpha blend; clamp/repeat samplers), texture cache with per-mip views, offscreen render, readback → RGBA8 | `wgpu` 30 | yes |
| `ofp-editor` | eframe app, panels, input routing, window modes, settings | `eframe`, `egui_*`, all above | yes |

All crates below `ofp-editor` avoid `eframe`/`egui` types, so they stay testable headless and portable to another
shell. [I]

### 4.2 Core types (sketch, not final API) [I]

```rust
/// Pixel rect inside the 2D viewport (Poseidon `Rect2DPixel`).
pub struct RectPx { pub x: f32, pub y: f32, pub w: f32, pub h: f32 }
/// Straight-alpha ARGB exactly as Poseidon's `PackedColor`.
pub struct PackedArgb(u32);
pub enum Wrap { Clamp, Repeat }                   // ClampU|ClampV vs NoClamp spec bits
pub struct TexRef { key: TextureKey, mip: MipLevel, wrap: Wrap } // newtypes per AGENTS.md
pub struct Vtx { pub pos: [f32; 2], pub uv: [f32; 2], pub color: PackedArgb }
pub enum DrawCmd {
    Quad { tex: Option<TexRef>, rect: RectPx, uv: [[f32; 2]; 4], color: [PackedArgb; 4], clip: RectPx },
    Poly { tex: Option<TexRef>, verts: PolyVerts /* fixed [Vtx; 32] + len */, clip: RectPx },
    Line { from: [f32; 2], to: [f32; 2], c0: PackedArgb, c1: PackedArgb, clip: RectPx },
    Text { font: FontKey, pos: [f32; 2], size_ex: f32, color: PackedArgb, clip: RectPx, run: TextRunId },
}
```

The `DrawList` keeps its `Vec`s across frames (`clear()` keeps capacity) and interns strings in a per-frame arena.
This satisfies the rule "hot paths must not heap-allocate". The primitive names and fields mirror
`IGraphicsEngine`, so each ported `OnDraw` reads almost line for line against its upstream source with a citation
comment.

### 4.3 Batcher and GPU pipeline [I]

- **Order:** keep painter's order and merge consecutive commands with the same `(texture, mip, wrap)`. This is
  the same key as Poseidon's queues. Expand `Line` into a quad with the line texture at mip 1, and `Text` into
  glyph quads. Clip on the CPU (port of `Clip2D`), so there are no scissor changes. Expected: tens of draw calls
  per frame, dominated by the number of distinct terrain textures visible.
- **Vertex:** 20 bytes (pos `f32x2`, uv `f32x2`, colour `unorm8x4`). Pack bytes with `to_le_bytes` rather than
  `bytemuck` derives. Derive macros expand to `unsafe impl`, which may conflict with `#![forbid(unsafe_code)]`.
  This interaction is **[U]**; check it in the PoC.
- **Shader:** one WGSL pipeline computing `out = color * textureSample(t, s, uv)`, with a 1x1 white texture for
  untextured draws. Discard fragments with alpha below 1/255, like the engine's alpha test (§2.3). Colour blend
  is `SrcAlpha / OneMinusSrcAlpha`, as in `GLBlendState.hpp`. **Do not copy the engine's `One / Zero` alpha
  component.** In the engine, framebuffer alpha is never shown. Our target's alpha, however, *is* used when egui
  composites it, and egui blends premultiplied (`One, OneMinusSrcAlpha`; see §6). Clear the target opaque and
  use an alpha component that keeps it at 1 (e.g. `One / OneMinusSrcAlpha`), or force alpha to 1 on output.
  **[V: egui blend state; I: remedy]** Textures are `Rgba8Unorm`. PAA DXT data can be decoded to RGBA8 at load (doc 07 plans
  `texpresso` or ~150 lines); using BC upload when `TEXTURE_COMPRESSION_BC` is available is an optimisation for
  later.
- **Explicit mip level:** create a texture view with `base_mip_level = m, mip_level_count = 1`, or a sampler with
  an LOD clamp, per `TexRef`. This mirrors `UseMipmap(tex, level, level)`.
- **Caching:** the editor is reactive. Rebuild the DrawList only on model, camera or hover change. Optionally
  cache static terrain layers as GPU buffers keyed by `(LOD step, camera)`. The original redraws every frame, but
  we do not have to.

### 4.4 Composition with egui, and scaling modes [I]

The classic view renders into an offscreen `Rgba8Unorm` texture, which is registered once per size with
`register_native_texture` and drawn by egui. The texture size and 2D-viewport math follow a user setting:

| Mode | Classic target size | Composite filter | Effect |
| --- | --- | --- | --- |
| **Native** (default) | panel size in physical px | nearest (1:1) | Same maths as CWR at that window size: 1-px bevels stay 1 px, and fonts scale with `Height2D/600`. |
| **Authentic low-res** | 800x600 / 1024x768 virtual | nearest-integer or bilinear upscale | The 2001 look on a modern screen. |
| **Scaled chrome** | panel size | nearest | Multiplies pixel constants (bevel widths, insets) by `Height2D/600`, as doc 05 §3 suggests. |

The map control fills the classic view at any aspect. Dialogs follow the UI-rect policy (doc 05 §4). Modern
panels dock around the classic view. Hiding them all gives the authentic full-window look.

### 4.5 Input, focus and IME [I]

- Pointer: the classic view widget converts egui pointer positions (points) → physical px within the image rect →
  normalised UI coordinates → `ofp-ui-classic` events (`OnLButtonDown/Up/Click/DblClick`, `OnMouseMove/Hold`,
  `OnMouseZChanged`, as in `UIControlsBase.hpp#L104-L126`).
- Keyboard: while the classic view has egui focus, forward key, text and IME events. Use egui's focus-lock event
  filter so Tab, arrows and Escape reach classic controls, which use them for their own focus and navigation. The
  exact egui API is **[U]**; verify it in the PoC. Map shortcuts (numpad pan, F1–F6 modes) apply only while the
  classic view is focused.
- IME: the classic `CEdit` has hooks `OnIMEChar/OnIMEComposition` (`UIControlsBase.hpp#L106-L108`). Feed them from
  egui IME events, and report the caret rectangle through egui's IME output or `ViewportCommand::IMERect`. The
  bitmap fonts cannot draw CJK, so composition text renders through the TTF fallback.
- Agent "proposed changes" render as a translucent ghost layer in `ofp-map2d`. They are just more DrawList
  commands with a modulated alpha, like the engine's `ModAlpha`.

### 4.6 Window modes, DPI, multi-window [V/I]

- Windowed, borderless fullscreen and monitor choice use `ViewportCommand::{Fullscreen, SetMonitor, Maximized}`.
  **[V]** Exclusive fullscreen is not needed for an editor. It would also fight the game window when "Preview"
  launches CWA (doc 08). Minimise the editor instead. **[I]**
- DPI: winit's scale factor becomes egui's `pixels_per_point`. The classic target is sized in *physical* px, so
  1-px lines stay crisp on 150% displays. Per-monitor DPI changes arrive as resize events. **[I]**
- Multi-window: detachable chat, script or diff panels use deferred viewports. Classic dialogs stay modal inside
  the main window, as in the game. Whether eframe shares one wgpu `Device` across viewports (needed to reuse our
  textures) is **[U]**.

### 4.7 Accessibility [V/I]

- Modern panels are accessible through egui + AccessKit (eframe default feature). **[V]**
- Classic controls: publish one AccessKit node per visible control via `Context::accesskit_node_builder`. Roles are
  button, list box, combo, text input or slider; the label is the control text or tooltip; bounds are in window
  coordinates. The API exists **[V]**; its fitness for a non-egui widget tree is **[I]** and is spike 5 below.
- Also offer "Modern forms": the same `DisplaySpec` rendered with egui widgets, following the D032 theme
  switching idea. This gives screen-reader and keyboard users a first-class path. It also reuses the inspector
  code. **[I]**

### 4.8 Backends, low-end GPUs, CPU fallback [V/I]

- wgpu 30 platform matrix: Vulkan and DX12 first-class on Windows; Metal on macOS; OpenGL "GL 3.3+"
  downlevel/best-effort on Windows and GL ES 3.0+ on Linux (wgpu README). **[V]** CWR itself targets GL 3.3, so any
  machine that runs the remaster should at least get wgpu's GL backend. **[I]**
- Adapter policy in settings: `auto | dx12 | vulkan | metal | gl | software`. This is loosely inspired by
  iron-curtain's GPU policy, which is *not* a backend list. It offers `gpu = auto|off|on|require` plus
  `fallback = classic|fail`, where `off` selects a CPU-only "classic" frontend
  (`iron-curtain-engine/iron-curtain@7b7fac7fa5:AGENTS.md#L701-L766`). `software` selects the CPU adapter
  (WARP / llvmpipe) via `native_adapter_selector`, or `force_fallback_adapter`. **[I]**
- Windows 10 is the floor: since Rust 1.78, "Windows 10 will now be the minimum supported version for the
  `*-pc-windows-*` targets" (<https://blog.rust-lang.org/2024/02/26/Windows-7/>). **[V]**
- Our own CPU rasteriser is not planned. WARP and llvmpipe run this workload (≤10^5 simple quads, reactive
  repaint), and a second renderer would double the fidelity surface. Revisit this if spike 3 shows WARP below
  ~10 fps on a full-window map. **[I]**

### 4.9 Testing and headless rendering [V/I]

| Layer | What | Tooling | Deterministic? |
| --- | --- | --- | --- |
| 1 | Each control recipe and map layer on **synthetic** data → DrawList → text snapshot | `insta` 1.48 | yes (pure Rust) |
| 2 | Batcher: clipping (UV re-interpolation, 32-vertex cap), batch splits, vertex bytes | unit tests | yes |
| 3 | Pixel goldens: headless wgpu device (no surface) → offscreen → `copy_texture_to_buffer` (256-byte row alignment) → PNG → tolerance diff | wgpu on **WARP** (Windows) and **Mesa lavapipe** (Linux). wgpu's own CI has "(Windows) Install WARP" and "(Linux) Install Mesa" steps. **[V]** | per-OS baselines + tolerance |
| 4 | egui panels: interaction via AccessKit queries, screenshots | `egui_kittest` 0.36.2 with `snapshot` + `wgpu` features. `kittest.toml` `threshold` (default 0.6) and `max_failed_pixels` (default 0); `UPDATE_SNAPSHOTS=true` (egui_kittest README) **[V]** | tolerance |
| 5 | Fidelity vs the real engine (local only, never committed) | CWR `triScreenshot` on the user's demo/full install (doc 05 §9), with gamma 1.0 and render scale 1.0 (§2.3) | manual/local |

Goldens in layers 3 and 4 are rendered from synthetic fixtures (our own procedural textures, glyph atlases and
terrain), so committing them is legal. Whether GitHub's macOS runners give wgpu a usable Metal adapter is
**[U]**. Until it is checked, run macOS golden tests as `#[ignore]` or local-only, and keep layer 1 and 2 on all
OSes. Per `AGENTS.md`, agents run `cargo test`/`clippy` only. Interactive runs of the app are for the user.

### 4.10 Performance budget (targets to validate, not measurements) [I]

- DrawList build for a full-window map at 1080p: < 4 ms CPU (release) on a 4-core laptop.
- GPU submit for ≤ 100k quads: < 2 ms on an Intel/AMD iGPU (DX12/Vulkan). WARP: < 100 ms, which is acceptable
  because repaint is reactive.
- Idle CPU ≈ 0: eframe repaints only on input, animation or streaming agent output.

---

## 5. Alternatives and switch triggers [I]

| If … | … then switch to |
| --- | --- |
| eframe blocks event pre-emption, frame pacing, or sharing the wgpu device across viewports | winit + wgpu + egui-winit/egui-wgpu directly. The crates below `ofp-editor` are unchanged. |
| The offscreen→egui composite cannot be made colour-exact | Draw the classic view inside egui's pass via `egui_wgpu::Callback`, with our own pipeline and blend. |
| egui's breaking minors become too costly | Pin one egui minor per release train, and upgrade egui and wgpu together, because egui-wgpu pins the wgpu major. |
| AccessKit for classic controls proves inadequate | Promote "Modern forms" (egui dialogs from the same `DisplaySpec`) to the default in accessibility mode. |
| A community wants a declarative, designer-friendly modern UI | Re-evaluate Slint for modern panels only, after checking licence compatibility with the project licence. |
| winit IME or Wayland defects | Use SDL3 windowing (sdl3-rs) with wgpu surfaces; egui input via a small SDL→egui adapter. |

---

## 6. Risks and mitigations

| Risk | Likelihood / impact | Mitigation |
| --- | --- | --- |
| **Colour space and composite:** egui-wgpu's shader (`egui.wgsl` on `emilk/egui` main, not pinned to 0.36.2) names the sampled value `tex_gamma`, multiplies it by the vertex colour, and converts gamma→linear only for an sRGB framebuffer. So gamma-space `Rgba8Unorm` bytes should round-trip **[I]**. Remaining hazards: the premultiplied blend `One, OneMinusSrcAlpha` needs our target alpha = 1 (§4.3) **[V]**. `RendererOptions.dithering` defaults to `true` and adds noise to values that are not whole 8-bit values, i.e. filtered upscales, but not 1:1 nearest sampling **[V]**. | Medium / High for fidelity | Spike 1: render known swatches and compare the pixel values from `ViewportCommand::Screenshot` with expected bytes. Test both 1:1 nearest and upscaled modes, with dithering on and off. Fallback: the paint-callback path. |
| wgpu/egui churn (wgpu majors 28→29→30 within 7 months; egui breaking minors every ~2–3 months) **[V]** | High / Medium | Keep one `wgpu` version in the workspace, taken from egui-wgpu. Isolate wgpu in `ofp-gpu`. Budget an upgrade day per quarter. |
| Line and font fidelity depends on install assets (`textureLine`, FXY pages, CWR TTFs) that we may not ship | High / Medium | Load them from the install (doc 05 §7). Author open equivalents for the fallback theme, and test with synthetic fixtures. |
| Software adapters differ per OS, so golden tests flake | Medium / Low | Put deterministic layers 1–2 first. Use per-OS baselines and a YIQ threshold like kittest's. Allow no pixel fuzz in DrawList snapshots. |
| Keyboard focus conflicts between egui and classic controls (Tab, Esc, F-keys) | Medium / Medium | A single focus owner and an explicit event filter (spike 4). |
| Accessibility of the custom tree is incomplete | Medium / Medium | Offer the Modern-forms path, and test with Accessibility Insights (Windows) and VoiceOver (macOS). |
| `bytemuck` derives vs `forbid(unsafe_code)` **[U]** | Low / Low | Manual byte packing. |
| Licence mismatch if the project picks a permissive licence while porting GPL code | Decided elsewhere | All recommended dependencies are MIT, Apache-2.0, BSD-3 or Zlib, so they are compatible with both GPLv3 and permissive licences. Avoid GPL-3.0-only (Slint) and GPL-2.0 (HEMTT) links. **[I]** |

---

## 7. Proof-of-concept plan (do this first; ~3 weeks, one developer)

Each spike ends with committed tests. Where a check needs a real install or a human, the evidence is a short
local verification note, per the repo's Evidence Rule. The user runs the app; agents only run tests and lints.

1. **Shell and composite (3 days).**
   - Build: eframe 0.36 app with a docked egui side panel (a mock chat using `egui_commonmark`, a `similar` diff,
     and a `TextEdit::code_editor` with a stub SQF highlighter). A central classic view shows an offscreen wgpu
     texture with colour swatches, gouraud quads, repeat-tiled textures and explicit mip levels.
   - Exit: swatch bytes match the expected values in a screenshot. Windowed ↔ borderless fullscreen ↔ monitor
     switch works. A DPI change (100% → 150%) keeps 1-px lines crisp.
2. **`ofp-draw2d` + glyphs (4 days).**
   - Build: DrawList, a `Clip2D` port, line→quad and batching, with insta snapshots. An FXY parser and atlas from
     a *synthetic* generated font and PAA-like pages. Port `FontDraw` (the 'o' space, `toInt` advances, aspect
     width). A TTF fallback via cosmic-text.
   - Exit: snapshots are stable, and headless goldens pass on WARP and lavapipe in CI.
3. **Map stress (4 days).**
   - Build: `ofp-map2d` on a procedural 256×256 heightmap covering sea gradient, fields with per-corner alpha,
     contours, forests, grid labels and 2,000 unit icons.
   - Exit: zoom and pan at ≥ 60 fps on an iGPU (DX12 and Vulkan) and ≥ 10 fps on WARP. DrawList build stays
     within the §4.10 budget. Record frame times as the evidence.
4. **Classic dialog + input (4 days).**
   - Build: port `CStatic` (`ST_BACKGROUND` bevel, `ST_FRAME`, `ST_TITLE_BAR`, `ST_PICTURE`), `CButton`,
     `CListBox`, `CCombo` and `CEdit` driven by a hand-written synthetic rsc snippet through `ofp-rsc`.
   - Exit: focus and Tab work inside the classic view without egui stealing them. A Japanese IME composes into
     the classic edit (manual Windows check). On a local install only, the result is compared side by side with a
     CWR `triScreenshot`.
5. **Accessibility + multi-window (2 days).**
   - Build: AccessKit nodes for the spike-4 dialog, and the chat panel detached as a deferred viewport.
   - Exit: Accessibility Insights (Windows) lists the classic controls with roles and names. The detached window
     keeps working while the classic view animates.

Go/no-go: if spike 1's colour check or spike 4's focus handling fails and cannot be fixed within 2 extra days,
switch to raw winit + egui-winit (§5) before building more.

---

## Open questions

1. **Colour pipeline:** does egui-wgpu 0.36 display an `Rgba8Unorm` native texture byte-exactly on an sRGB
   swapchain? Reading the shader suggests yes at 1:1 with alpha = 1 and no dithering (§6), but this is untested.
   (Spike 1.)
2. **Default scaling mode:** should "Native" or "Authentic low-res" be the default classic mode? This is a
   community preference, so poll it.
3. **Line texture:** what exactly does `textureLine` look like in CWR and CWA 1.99 data? Is `CfgPreloadTextures`
   (a remaster-only config) absent in 1.99, which would make the name hard-coded there?
4. **Multi-window resources:** does eframe share one wgpu device across native viewports?
5. **macOS CI:** do GitHub-hosted macOS runners expose a Metal adapter usable by wgpu for golden tests?
6. **Linux accessibility:** does eframe's AccessKit integration work under AT-SPI (Linux) today? The README
   names only Windows and macOS.
7. **HEMTT licence:** is HEMTT "GPL-2.0-only" or "-or-later"? This matters only if we ever want to reuse its SQF
   crates.
8. **Old GPUs:** do we support hardware without DX12 or Vulkan (the wgpu GL backend only)? Setting the floor at
   "GL 3.3 like CWR" needs a real low-end test machine.
9. **Editor-map 3D objects and culling:** does `RscDisplayArcadeMap` declare 3D objects? Does the GL33 screen
   pass ever back-face-cull a 2D primitive? (§2.2, §2.3.)

## Sources

Code (pinned; repo-relative paths):

- `BohemiaInteractive/CWR@ffc61838b7`:
  - Graphics core: `engine/Poseidon/Graphics/IGraphicsEngine.hpp#L47-L101`,
    `engine/Poseidon/Graphics/Core/Engine.hpp#L75-L86`, `#L136`, `#L184-L252`, `#L543-L591`, `#L695-L715`,
    `engine/Poseidon/Graphics/Core/Engine.cpp#L113-L132`, `engine/Poseidon/Graphics/Core/GLBlendState.hpp#L24-L28`.
  - GL33 backend: `engine/PoseidonGL33/EngineGL33_2D.cpp#L7-L280`,
    `engine/PoseidonGL33/EngineGL33_Queue.cpp#L270-L276`, `#L355-L388`,
    `engine/PoseidonGL33/EngineGL33_Shaders.cpp#L199-L239`.
  - Fonts: `engine/Poseidon/Graphics/Rendering/Draw/FontDraw.cpp#L27-L139`, `FontData.cpp#L34-L92`,
    `Font.cpp#L37-L60`, `#L277-L366`, `Font.hpp#L32`.
  - Textures: `engine/Poseidon/Graphics/Textures/TexturePreload.cpp#L29-L62`.
  - Controls: `engine/Poseidon/UI/Controls/UIControls.cpp#L95-L125`, `#L376-L577`, `UIControlsBase.hpp#L104-L177`,
    `UIControlsExtShared.hpp#L24-L25`.
  - Map: `engine/Poseidon/UI/Map/UIMap.cpp#L459-L574`, `#L613-L630`, `#L743-L942`, `#L1248-L1578`, `#L1971-L2201`,
    `UIMapExt.cpp#L176-L279`, `#L2883-L2895`, `UIMapExtDisplay.cpp#L478-L501`, `UIMapBase.hpp#L276-L373`.
  - Added in verification: `engine/Poseidon/Graphics/Rendering/BuildRenderPassDescriptor.hpp#L41-L196`,
    `engine/Poseidon/Graphics/Rendering/RenderPassDescriptor.hpp#L180-L197`,
    `engine/PoseidonGL33/EngineGL33_Queue.cpp#L241-L268`, `EngineGL33_Shaders.cpp#L300-L314`, `#L1611-L1674`,
    `engine/PoseidonGL33/EngineGL33_VertexBuffer.cpp#L575-L594`, `EngineGL33.cpp#L226`, `EngineGL33.hpp#L419`,
    `engine/Poseidon/UI/Map/UIContainers.cpp#L603-L669`, `UIMapDisplay.cpp#L870-L894`, `UIMap.hpp#L705-L764`,
    `FontDraw.cpp#L536-L546`, `UIMap.cpp#L1318-L1372`.
  - Other: `engine/Poseidon/Core/resincl.hpp#L165-L219`, `engine/Poseidon/UI/Settings/AspectRatio.cpp#L85-L117`,
    `engine/Poseidon/Dev/Debug/DebugOverlay.cpp`, `engine/Trident/Cargo.toml#L1-L7`.
- `ofpisnotdead-com/CWR-CE@b67bf3bd62`: `engine/PoseidonGL33/EngineGL33_2D.cpp` (identical to CWR), `engine/Poseidon/UI/Map/UIMap.cpp`.
- `iron-curtain-engine/iron-curtain@7b7fac7fa5`: `AGENTS.md#L701-L766`, `crates/ic-render/Cargo.toml#L15`.
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9`: `src/architecture/sdk-editor.md#L43-L59`, `src/decisions/09c/D032-ui-themes.md`.
- This repo: `AGENTS.md` (rules), `docs/research/05-visual-fidelity-and-ui-resources.md`, `docs/research/07-file-formats-and-rust-crates.md`.

Web (fetched 2026-09-26):

- crates.io API: <https://crates.io/api/v1/crates/egui> , /eframe , /egui_kittest , /egui-winit/0.36.2/dependencies , /wgpu , /winit , /bevy , /bevy_egui , /iced , /slint , /vizia , /xilem , /masonry , /blitz-dom , /macroquad , /miniquad , /sdl3 , /gpui , /floem , /vello , /vello_cpu , /vello_hybrid , /vello_gpu , /femtovg , /tiny-skia , /glyphon , /glyphon/0.12.0/dependencies , /cosmic-text , /parley , /accesskit , /egui_dock , /egui_commonmark , /egui_code_editor , /similar , /insta (all under <https://crates.io/api/v1/crates/>)
- egui CHANGELOG: <https://raw.githubusercontent.com/emilk/egui/main/CHANGELOG.md> ; README: <https://raw.githubusercontent.com/emilk/egui/main/README.md>
- egui_kittest README: <https://raw.githubusercontent.com/emilk/egui/main/crates/egui_kittest/README.md>
- egui docs: <https://docs.rs/egui/latest/egui/viewport/enum.ViewportCommand.html> , <https://docs.rs/egui/latest/egui/viewport/index.html> , <https://docs.rs/egui/latest/egui/struct.Context.html> , <https://docs.rs/egui/latest/egui/widgets/text_edit/struct.TextEdit.html> , <https://docs.rs/epaint/latest/epaint/textures/struct.TextureOptions.html>
- egui-wgpu shader and blend state (main branch): <https://raw.githubusercontent.com/emilk/egui/main/crates/egui-wgpu/src/egui.wgsl> , <https://raw.githubusercontent.com/emilk/egui/main/crates/egui-wgpu/src/renderer.rs> ; <https://docs.rs/egui-wgpu/latest/egui_wgpu/struct.RendererOptions.html>
- egui-wgpu docs: <https://docs.rs/egui-wgpu/latest/egui_wgpu/trait.CallbackTrait.html> , <https://docs.rs/egui-wgpu/latest/egui_wgpu/struct.Renderer.html> , <https://docs.rs/egui-wgpu/latest/egui_wgpu/struct.RenderState.html> , <https://docs.rs/egui-wgpu/latest/egui_wgpu/struct.WgpuSetupCreateNew.html>
- wgpu README: <https://raw.githubusercontent.com/gfx-rs/wgpu/trunk/README.md> ; CI workflow: <https://raw.githubusercontent.com/gfx-rs/wgpu/trunk/.github/workflows/ci.yml>
- WARP/lavapipe usage in other projects' CI: <https://github.com/francisdb/cuelight/pull/81> , <https://github.com/StruisICT/InSearch/pull/13> , <https://github.com/bhouston/jest-gpu/issues/31>
- iced: <https://github.com/iced-rs/iced/releases> , <https://raw.githubusercontent.com/iced-rs/iced/master/README.md> , <https://docs.rs/iced/0.14.0/iced/widget/shader/index.html> ; dependency lists <https://crates.io/api/v1/crates/iced/0.14.0/dependencies> , <https://crates.io/api/v1/crates/iced_winit/0.14.0/dependencies> (no accesskit)
- Slint: <https://slint.dev/terms-and-conditions> ; wgpu texture PR <https://github.com/slint-ui/slint/pull/8278> ; docs <https://docs.slint.dev/latest/docs/rust/slint/wgpu_28/>
- Bevy 0.19: <https://bevy.org/news/bevy-0-19/> , <https://alternativeto.net/news/2026/6/bevy-0-19-brings-next-gen-scenes-faster-rendering-contact-shadows-and-new-feathers-widgets/> , <https://gamefromscratch.com/bevy-0-19-released/>
- Vello: <https://raw.githubusercontent.com/linebender/vello/main/README.md> ; Xilem: <https://raw.githubusercontent.com/linebender/xilem/main/README.md> ; Blitz: <https://raw.githubusercontent.com/DioxusLabs/blitz/main/README.md> ; Vizia: <https://raw.githubusercontent.com/vizia/vizia/main/README.md> ; femtovg: <https://raw.githubusercontent.com/femtovg/femtovg/master/README.md> ; cosmic-text: <https://raw.githubusercontent.com/pop-os/cosmic-text/main/README.md>
- egui_code_editor: <https://raw.githubusercontent.com/p4ymak/egui_code_editor/main/README.md>
- HEMTT repo metadata: <https://api.github.com/repos/BrettMayson/HEMTT> , <https://raw.githubusercontent.com/BrettMayson/HEMTT/main/Cargo.toml>
- Rust Windows baseline: <https://blog.rust-lang.org/2024/02/26/Windows-7/>

## Verification notes

Adversarial fact-check, 2026-09-26. Code was re-read at the pinned SHAs; web claims were re-fetched live.

**Confirmed:**
- Primitive tally. Over `UI/Controls` and `UI/Map`, the only draw calls are `Draw2D`, `DrawLine`, `DrawPoly`,
  `DrawText[F]`, `DrawTextVertical` and `GetTextWidth[F]`. The 3D calls sit only in `UIControls3D.cpp` and
  `UIControlsHTML.cpp`.
- `Draw2DPars` and CPU clipping, including UV re-interpolation.
- `DrawLine`: a 3-px quad, `v` 0.25→1, `UseMipmap(tex,1,1)`, and `SetMipmapRange(1,1)`.
- `DrawPoly`: `maxN = 32`, with per-edge `Clip2D`.
- `AlphaBlend` is `(SRC_ALPHA, ONE_MINUS_SRC_ALPHA, ONE, ZERO)`, and there is no sRGB anywhere under `engine/`.
- The mip-level formula and all `ptsPerSquare*` constants.
- Text: the 'o'-width space and `toInt` advances; the FXY layout; the `Font.cpp` TTF mapping table.
- Other code pointers: controls, bevel macros, grid, crosshair, ellipse `nSteps`, and the IME hooks.
- CWR-CE matches CWR: `EngineGL33_2D.cpp` is identical, and `UIMap.cpp` differs in 15 lines.
- Crate versions and dates: egui/eframe 0.36.2, wgpu 28/29/30/30.0.1, winit 0.30.13 and 0.31.0-beta.3,
  Bevy 0.19.1 and 0.20.0-rc.1, iced 0.14.0, slint 1.18.1, and the others spot-checked.
- Dependency requirements: egui-wgpu needs `wgpu ^30.0`, egui-winit needs `winit ^0.30.13`, and glyphon 0.12
  needs `wgpu ^30.0.0` and `cosmic-text ^0.19`.
- eframe default features.
- egui docs: `register_native_texture` (`Rgba8Unorm`), `accesskit_node_builder`, `ViewportCommand` variants
  and payloads, and multi-viewport support.
- Project READMEs: wgpu's platform table, wgpu CI WARP/Mesa steps, the kittest defaults, and the
  iced/Xilem/Blitz status quotes.
- Licences and platform: Slint's licence string and royalty-free terms, egui 0.34's Skrifa/vello_cpu change,
  the Rust 1.78 Windows 10 floor, and HEMTT as `GPL-2.0` (only vs or-later still [U]).
- iron-curtain pins Bevy 0.18.1.

**Changed:**
- Blending: the alpha component of the recommended blend state (§4.3). egui composites premultiplied, so the
  engine's `One/Zero` alpha must not be copied.
- New 2D-state facts (§2.3): bilinear sampling, the alpha test at ref 1, the `constColor` reset, default culling,
  and the gamma/SSAA post-pass. The fidelity list (§2.7) and the layer-5 test setup were updated to match.
- Terrain (§2.5): textures apply only to single-cell blocks. The `UIMap.cpp#L1356` `NoClamp` citation was
  mis-attributed to textured cells; those use `ClampFlags(id)` (§2.2, §2.5).
- Ellipses are separate `DrawPoly` wedges, and their UVs are map-anchored.
- Citation fixes: `DrawTextVertical` is an obsolete no-op in CWR. The 3D-object caveat for
  `ControlsContainer` was added. `Engine.hpp` range widened to `#L184-L277`.
- Wording and dates:
  - epaint mipmap quote corrected to the verbatim text.
  - Native textures can take a custom sampler.
  - iced `TextEditor` dates from 0.12, not 0.14.
  - iced's lack of AccessKit is now verified via crates.io dependency lists.
  - Bevy cadence corrected to ~3–5 months, with dates.
  - Slint 1.18 feature claim softened.
  - iron-curtain's GPU policy described accurately.
  - `egui_code_editor` quote corrected.
- The colour-space risk (§6) was narrowed using egui-wgpu's shader, blend state and `dithering` default. Open
  questions 1 and 9 were updated.

**Unverifiable / not re-checked:**
- Whether `RscDisplayArcadeMap` declares 3D objects, and whether 2D polys are ever culled.
- Byte-exact composite, which needs spike 1.
- The Vello `vello_gpu` rename and the femtovg, gpui, floem, blitz-dom and macroquad version rows (not
  re-fetched).
- The WARP/lavapipe links from third-party CI.
- `bytemuck` vs `forbid(unsafe_code)`.
