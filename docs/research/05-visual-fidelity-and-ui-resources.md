# Visual Fidelity and UI Resources for the Standalone CWA Mission Editor

Research date: 2026-09-26. Scope: how to make our standalone Rust editor *look* like the in-game
mission editor of Arma: Cold War Assault (CWA, originally Operation Flashpoint: Cold War Crisis,
2001), where every visual parameter is defined, and how we may obtain the assets legally.
Companion doc: `03-original-editor-code-map.md` (editor behaviour, data model, `mission.sqm`).

Epistemic tags used below: **[V]** verified in code or on a fetched web page (citation given);
**[I]** inferred from verified facts; **[U]** unknown / not verified; treat it as a hypothesis.

## TL;DR

- **Layout numbers are not in the source repos.** Neither `BohemiaInteractive/CWR` nor `ofpisnotdead-com/CWR-CE`
  contains any `RscDisplayArcade*` class body (positions, fonts, colors). The engine loads them by name
  from game data (`bin/resource.cpp` or `resource.bin`, plus `bin/config.bin`). **[V]**
- **Code does give us everything else.** It defines the resource *schema*: which keys each control reads,
  the IDD/IDC numbers (`resincl.hpp`), the `ST_*`/`CT_*` constants, and the exact drawing algorithm of every
  control and of the 2D map. We can reimplement the renderer 1:1 from GPL code. **[V]**
- **Classic look = vector lines and flat fills.** Buttons, list boxes, combos, edits, scroll bars, sliders and
  frames are drawn with line primitives laid out on a 1‑px grid, plus solid rectangles. Only a few textures are
  involved: the dialog background tile, the GroupBox2 tile, the HUD corner, cursors, map icons, fonts, and the
  remaster's `textureWhite`/`textureLine`. Note that the GL33 backend draws *every* 2D line as a 3‑px‑wide quad
  sampled from `textureLine`, so the on-screen line profile depends on that data texture. **[V]**
- **UI space is a 0..1 rectangle authored against an 800x600 (4:3) canvas.** Text height is `sizeEx` × UI
  height. The remaster's default "Modern" policy maps that rectangle to the full window from 4:3 up to 16:9 (+2%).
  Between that and the 21:9 clamp it uses a centred **4:3** band. Beyond 21:9 it uses a centred 21:9 band, and
  below 4:3 a letterboxed 4:3 band. "Legacy" mode stretches it over the whole window. **[V]**
- **The editor map is procedural, not a bitmap.** Its layers are sea gradient, optional texture colours,
  contour lines at a zoom-dependent interval, forests, roads, object icons, town names, spot heights and a grid,
  with the editor overlay on top. All colours and icons come from config. Rendering it needs our own parsers for
  WRP terrain, P3D `map` properties and `CfgWorlds`. **[V]**
- **Recommendation (assets): runtime-load from the user's install and never redistribute.** Probe for the Steam
  or GOG *Remastered* install, then the **free Steam demo** (app 4819000), then legacy CWA 1.99. Parse
  `resource`/`config`/fonts/PAA/WRP/P3D from there. **[I]**
- **The free demo appears sufficient for the editor visuals.** BI's own editor integration tests run the full
  game binary on `packages/Demo` data and open displays 26, 27 and 29. CWR-CE docs also say demo data plus the
  full binary unlocks the editor. The demo's island set is **[U]**; the only confirmed world is one with class
  name `Demo`. **[V/I]**
- **Game data is APL‑SA: NonCommercial, "ArmaOnly", ShareAlike.** **[V]** APL‑SA does allow sharing for
  NonCommercial + ArmaOnly purposes, with attribution and ShareAlike. A CWA editor is arguably "directed towards"
  CWA, so bundling is not flatly forbidden. We still choose **not** to commit or bundle data, because it would bring
  NonCommercial terms into our GPL releases, and because of the synthetic-fixtures rule. **[I]** Our own code and
  our fallback theme stay under our licence.
- **Recommendation (fallback): ship an original "Classic look-alike" theme.** Author the layout data in the same
  schema (our own numbers traced from screenshots), draw vector chrome, use OFL fonts and our own icon set, and
  take the map palette from GPL engine constants. Used when no install is found. **[I]**
- **Build a golden-image harness early.** Render each display with our renderer and with the CWR engine
  (Trident `triScreenshot` on local demo data), then diff them. This needs the full-game binary (`PoseidonGame`)
  built from source, because the demo exe has no editor. Screenshots stay local and are never committed. **[I]**

---

## 1. Context and glossary

| Term | Meaning |
|---|---|
| **Poseidon** | Codename of the CWA engine; GPL‑3.0‑or‑later source released June 2026 as `BohemiaInteractive/CWR`, continued by `ofpisnotdead-com/CWR-CE`. |
| **Display / dialog** | A full-screen or modal UI screen (`ControlsContainer` subclass). Identified by an **IDD** (int). |
| **Control** | Widget inside a display, identified by an **IDC** (int); `IDC_STATIC` (= -1) for decoration. |
| **Rsc class** | A config class (e.g. `class RscDisplayArcadeMap { idd=26; controls[]=…; }`) describing a display's controls and their `x,y,w,h,type,style,font,sizeEx,color*` values. |
| **resource.cpp / resource.bin** | The game's UI config file ("Res" ParamFile) holding all `Rsc*` classes. Text `.cpp` wins over binarized `.bin` if both exist. |
| **config.bin** | Main game config ("Pars") — `CfgVehicles`, `CfgWorlds`, `CfgMarkers`, `CfgWrapperUI`, `CfgInGameUI`, `CfgFonts`, … |
| **remaster.cpp** | Remaster-only config ("Remaster" ParamFile), e.g. `CfgPreloadTextures`. |
| **PBO** | BI archive format holding game data (`Dta\*.pbo`, `AddOns\*.pbo`). |
| **PAA / PAC** | BI texture formats (DXT1/3/5, ARGB4444/1555/8888, AI88). |
| **FXY** | Legacy bitmap-font glyph table; glyph pages are `<font>-NN.paa`. |
| **WRP** | Island (terrain) file: heightmap, per-cell textures, objects. |
| **P3D** | Model file; its named property `map` classifies an object for the 2D map (tree, house, forest square...). |
| **APL‑SA** | Arma Public License Share Alike — licence of BI game data. |

Code citations use `owner/repo@sha:path#Lx-Ly`. CWR = `BohemiaInteractive/CWR@ffc61838b7`, CE =
`ofpisnotdead-com/CWR-CE@b67bf3bd62`. Unless stated otherwise, the UI code is identical in both. CE differs in
cursor sizing, wheel-zoom binding and a `LayoutCanvas` refactor (see §4).

---

## 2. Where the editor's visual layout is defined

### 2.1 Result of the search

- `Grep "class Rsc(Display|Text|Button|Map|…)"` finds **no display or control-template class in CWR**. A broader
  `class\s+Rsc\w*` search finds only command-menu fixtures (`RscSubmenu`, `RscMainMenu`, `RscReply`, `RscUserRadio`)
  embedded as strings in `tests/unit/engine/Poseidon/UI/InGame/test_inGameUI.cpp#L83-L115`, which is present in both
  repos. In CE there is also a 4-line test fixture, `tests/fixtures/config-replace/bin/resource.cpp`
  (`class RscDisplayLoadMission { idd = 101; };`). The only embedded UI config data is a Tetris notebook
  snippet (`apps/tetris/Tetris/TetrisNotebookUI.cpp#L148-L187`, with `colorBackground[]`), which is unrelated to the
  editor. Every other `sizeEx`/`colorBackground`/`tahoma` hit is C++ code that *reads* those keys. The remaster's own
  resource overrides (e.g. `resources/menu/splashLogo.hpp`, named in `UI/OptionsUIApp.cpp#L186-L189`) are **not** in
  the repo; `resources/` holds only icons. **[V]**
- What the source **does** contain:
  - `engine/Poseidon/Core/resincl.hpp` (970 lines): all `CT_*` control types, `ST_*` styles, `IDD_*` display
    ids and `IDC_*` control ids. Examples: `CT_*` `CWR:engine/Poseidon/Core/resincl.hpp#L165-L191`, `ST_*`
    `#L193-L219`, IDDs `#L267-L342`, editor IDCs `#L678-L797`, template IDCs `#L807-L810`. **[V]**
  - The C++ display classes that `Load("Rsc…")` by name, then special-case some IDCs in `OnCreateCtrl` (table
    below). **[V]**
- The loader resolves names against **`Res`**:
  `ControlsContainer::Load(const char*)` → `Res >> clsName` (`CWR:engine/Poseidon/UI/Map/UIContainers.cpp#L438-L442`).
  `Res` is filled by `ParseResource`: `bin/resource.cpp`, else `bin/resource.bin`, then
  `bin/resource-extra.cpp` merged on top. A mod's `bin/` replaces the base
  (`CWR:engine/Poseidon/Asset/Addon/ConfigParsers.cpp#L233-L281`). `Pars` is loaded from
  `bin/config.cpp|config.bin` + `config-extra.cpp` (`#L179-L213`); `Remaster` from `bin/remaster.cpp|.bin`
  (`#L215-L231`). **[V]**
- Whether the remaster's UI resource is plain text is **unverified; the evidence conflicts**.
  - *For text:* two comments say that apps "that ship config.bin + resource.cpp + remaster.cpp (Game)"
    see every flag true (`CWR:tests/unit/engine/Poseidon/Core/test_config_system.cpp#L1-L3`,
    `engine/Poseidon/Core/Config/ConfigSystem.hpp#L10-L12`).
  - *For binary:* `.gitattributes#L42-L48` speaks of "Binary RESOURCE.BIN" in BI's staged `packages/**/BIN/`, next
    to text `.hpp` includes. `ConfigParsers.cpp#L261-L262` says that `resource-extra.cpp` adds displays "without
    rebuilding RESOURCE.BIN".
  - So our `rsc` crate must handle the rapified `resource.bin` as a first-class input, not as a fallback. **[V]** for
    the quotes; which format the retail and demo data actually ship is **[U]**.
- Legacy CWA 1.99: community guides say that `Resource.cpp` goes to `…\Arma Cold War Assault\BIN\` and that the
  shipped `resource.bin` is overridden by a `.cpp` there. For OFP 1.96 the path is `…\Res\Bin\`. Search results
  report this; the primary pages were not fetched (403/429). **[U]**

### 2.2 Display inventory (editor-relevant)

`[Simple]` marks the Easy-mode variant, loaded when the editor is not in Advanced mode. **[V]**

| Screen | Rsc class | IDD | C++ class / load site |
|---|---|---|---|
| Editor main map | `RscDisplayArcadeMap` | 26 | `DisplayArcadeMap` — `CWR:engine/Poseidon/UI/Map/UIMapExt.cpp#L2883-L2925` |
| Unit | `RscDisplayArcadeUnit[Simple]` | 27 | `UI/Map/UIMap.hpp#L886-L889` |
| Group | `RscDisplayArcadeGroup` | 40 | `UI/Map/UIArcade.cpp#L1260` |
| Waypoint | `RscDisplayArcadeWaypoint[Simple]` | 28 | `UI/Map/UIArcadeWaypoint.cpp#L45-L49` |
| Trigger ("sensor") | `RscDisplayArcadeSensor[Simple]` | 41 | `UI/Map/UIMap.hpp#L1005-L1008` |
| Marker | `RscDisplayArcadeMarker[Simple]` | 45 | `UI/Map/UIMap.hpp#L958-L961` |
| Effects | `RscDisplayArcadeEffects[Simple]` | 44 | `UI/Map/UIArcadeMarker.cpp#L358-L362` |
| Intel (name/date/weather) | `RscDisplayIntel[Simple]` | 32 | `UI/Map/UIMap.hpp#L1095-L1098` |
| Save / Load‑Merge | `RscDisplayTemplateSave` / `RscDisplayTemplateLoad` | 29 / 30 | `UI/Map/UIMap.hpp#L1051`, `#L1070` |
| Select island (editor entry) | `RscDisplaySelectIsland` | 51 | `UI/DisplayUI.hpp#L95` |
| User mission list | `RscDisplayCustomArcade` | 25 | `UI/DisplayUI.hpp#L113` |
| MP wizard | `RscDisplayWizardTemplate` / `RscDisplayWizardMap` | 67 / 68 | `UI/DisplayUIMultiplayerWizard.cpp#L85`, `#L616` |
| Confirm boxes | `RscMsgBox` (auto-layout) | 200–204 | `UI/Map/UIContainers.cpp#L1837-L1890` |

The IDD comes from the resource's `idd=` key (`UIContainers.cpp#L324`), not from C++. **[V]**
The integration test `arcade_map_language_switch.test.sqf` confirms the flow. Main menu IDC 115 (`IDC_MAIN_EDITOR`)
opens display 51; OK then opens display 26. The editor buttons are 101 Load, 102 Save, 103 Clear, 106 Merge,
107 Preview, 108 Continue, 112 "Show Textures" and 2 Exit. Exit opens message box 203
(`CWR:tests/integration/ui/editor/arcade_map_language_switch.test.sqf#L30-L58`, `#L95-L98`). **[V]**
Main-map IDCs: `IDC_MAP`=51, mode toolbox 104, Intel 105, section combo 109, Easy/Advanced 110, IDs 111,
Textures 112 (`resincl.hpp#L239`, `#L678-L689`). **[V]**

### 2.3 Display structure keys (schema, from the loader)

A display class has `idd`, `movingEnable`, and three control lists: `controlsBackground`, `objects` (3D models)
and `controls`. Each list is either a class of sub-classes or an array of names. A control class needs `type` and
`idc`, and may set `default=1` (at most one per display). Draw order is background, then objects, then foreground.
The focused control is drawn last within its layer. Hit-testing runs in reverse (foreground first).
(`UIContainers.cpp#L209-L238`, `#L271-L436`, `#L603-L682`) **[V]**
`idc`/`style`/`type` also accept the literal `IDC_STATIC` (`UIControlsBase.cpp#L48-L55`). **[V]**
Editor dialogs set `_enableSimulation=false; _enableDisplay=false`, so no 3D scene is drawn behind them
(e.g. `UIMap.hpp#L875-L876`, `UIMapExt.cpp#L2885-L2886`). **[V]** Our standalone editor therefore loses nothing by
having no 3D renderer.

---

## 3. Control rendering model

### 3.1 Common rules [V]

- **Coordinates:** `x,y,w,h` are floats in 0..1 of the *UI rectangle* (§4) (`UIControlsBase.cpp#L151-L163`).
  Pixel snapping: `xx = toInt(x*W)+0.5` where `W,H = Width2D(),Height2D()`. Width differs by control.
  `CStatic` uses `ww = toInt((x+w)*W) - toInt(x*W)` (`UIControls.cpp#L376-L387`). `CButton`, `CListBox` and
  `CCombo` use `ww = toInt(w*W)` (`UIControls.cpp#L2363-L2366`, `UIControlsImpl.cpp#L402-L405`).
- **Colors:** 4-float arrays `{r,g,b,a}` in 0..1, converted to 8-bit `PackedColor`. A malformed array (≠4 items)
  becomes opaque white (`CWR:engine/Poseidon/IO/ParamFileExt.cpp#L44-L59`). Display fade `alpha` multiplies
  each colour's alpha (`ModAlpha`).
- **Fonts:** `font="tahomaB24"` resolves via `GetFontID`. That strips any `fonts\` prefix, applies the
  per-language remap `CfgFonts >> <language> >> <name>`, and prefixes `fonts\` (`ParamFileExt.cpp#L20-L42`).
- **Size:** `size` (relative) = `size × font.Height()`, where `Height() = _maxHeight / 600`
  (`Font.cpp#L362-L366`). `_maxHeight` is the FXY max glyph height in bitmap mode. In the remaster's TrueType mode it
  is the mapping row's fixed `bitmapMaxHeight`, one value per family regardless of the name's size suffix
  (`Font.cpp#L46-L60`, `#L307`). Otherwise `sizeEx` is absolute: glyph-box height as a fraction of UI height
  (`UIControls.cpp#L95-L109`). Draw scale: `sizeH = Height2D × sizeEx / 600 / font.Height()` px per font pixel.
  Width is scaled by aspect settings (`FontDraw.cpp#L75-L76`, `UI/Text/ScreenTextLayout.hpp#L28-L42`).
- **Text inset:** `textBorder = 0.005` from the left/right edge (`UIControls.cpp#L68`). Vertical centring:
  `top = y + (h - size)/2`.
- **Styles (`style` bits):** low nibble is alignment (`ST_LEFT 0, RIGHT 1, CENTER 2`; vertical text: `ST_UP 3,
  ST_VCENTER 5, ST_DOWN 4`). `0xF0` is the static type (`ST_SINGLE 0, MULTI 16, TITLE_BAR 32, PICTURE 48,
  FRAME 64, BACKGROUND 80, GROUP_BOX 96, GROUP_BOX2 112, HUD_BACKGROUND 128, TILE_PICTURE 144, WITH_RECT 160,
  LINE 176`). Flags: `ST_SHADOW 256`, `ST_NO_RECT 512` (`resincl.hpp#L193-L219`).
- **Shadow (`ST_SHADOW`):** black copy offset by `(0.075, 0.1) × size` by default. `shadowOffsetX/Y` keys
  override; an explicit Y without X gets aspect-corrected (`UIControls.cpp#L200-L236`, `#L669-L691`).
- **Tooltips:** any control may set `tooltip`. The font is fixed to `tahomaB24` at size 0.02. Colours default to
  white text, white 30% box and black 30% shade, and can be overridden by `tooltipColorText/Box/Shade`
  (`UIControlsBase.cpp#L91-L135`).
- **Sounds (feel, not look):** `soundPush`, `soundClick`, `soundEscape` (buttons); `soundEnter` (active text)
  (`UIControls.cpp#L2275-L2277`, `UIControlsSlider.cpp#L98-L101`).

### 3.2 Global chrome config `CfgWrapperUI` (in config.bin) [V]

| Key | Used for |
|---|---|
| `Colors >> color1..color5` | bevel ramp for `ST_BACKGROUND`, title bar, group boxes (`UIControls.cpp#L127-L153`) |
| `Background >> texture, alpha` | tiled dialog background (`ST_BACKGROUND`) (`TexturePreload.cpp#L59-L62`) |
| `TitleBar >> texture, alpha`, `GroupBox >> alpha`, `GroupBox2 >> texture, alpha` | title bars / group boxes. The `TitleBar` texture is preloaded (`TexturePreload.cpp#L61`) but never drawn: `ST_TITLE_BAR` fills with `textureWhite` × color3 (`UIControls.cpp#L549-L566`). |
| `Button >> color1..color5` | all `CT_BUTTON` bevels (`UIControls.cpp#L2288-L2296`) |
| `Cursors >> <Arrow|Move|Scroll|Track…> >> texture, hotspotX, hotspotY, width, height, color` | mouse cursors (`UIContainers.cpp#L240-L269`; names used `UIMapDisplayBriefing.cpp#L1650-L1675`) |

`CfgInGameUI >> imageCornerElement` supplies the corner texture for `ST_HUD_BACKGROUND` (`TexturePreload.cpp#L57`).
The white, black, default and **line** (`textureLine`, 8x8, 4x4 mip used) textures come from
`Remaster >> CfgPreloadTextures` (`TexturePreload.cpp#L29-L47`).

### 3.3 Per-control keys and drawing [V]

| Control (`type`) | Keys read | How it is drawn |
|---|---|---|
| **Static** `CT_STATIC`=0 (`UIControls.cpp#L95-L692`) | `text, font, size/sizeEx, colorText, colorBackground, style, lineSpacing (MULTI)` | Default: solid `colorBackground` rect + text. `ST_BACKGROUND`: tiled `CfgWrapperUI` texture tinted by `colorBackground`, then a **6‑px bevel** (left/top color5→1, bottom/right color1→5). `ST_FRAME`: 1‑px rect in `colorText`, text "cut" into the top edge. `ST_TITLE_BAR`: color3 fill with inset lines at 5–8 px. `ST_GROUP_BOX(2)`: color3 fill (or GroupBox2 texture) + 1‑px light/dark edges. `ST_PICTURE`: `text` is a texture path (`FindPicture`: mission dir → `dtaExt\` → `data\*.paa`), drawn tinted by `colorText`. `ST_MULTI`: word-wrapped, scrollable (↑/↓), focus frame unless `ST_NO_RECT`. |
| **Button** `CT_BUTTON`=1 (`#L2258-L2438`) | `text, font, size/sizeEx, colorText, style, default, action, sound*` | **2‑px bevel** from `CfgWrapperUI>>Button` color1..5 (reversed when pressed), color3 fill inset 2 px, focus/default = 1‑px rectangle inset **6 px** in text colour; pressed text shifts by (0.003, 0.004). |
| **Edit** `CT_EDIT`=2 (`#L1144-L1161`, `#L1752-L2035`) | `text, font, size/sizeEx, colorText, colorSelection, style (MULTI), autocomplete` | 1‑px frame in `colorText`; selection block filled `colorSelection`; caret line blinking at 1 Hz (0.5 s on); optional autocomplete tooltip. |
| **Listbox** `CT_LISTBOX`=5 (`UIControlsImpl.cpp#L84-L94`, `#L196-L479`) | `font, size/sizeEx, colorText, colorSelect, rowHeight` | 1‑px frame; rows of `rowHeight`; **selected row = inverse video** (filled with `colorText`, text in `colorSelect`); optional per-row picture; vertical scrollbar width **0.02** at right. |
| **Combo** `CT_COMBO`=4 (`#L483-L516`, `#L800-L928`) | `font, size/sizeEx, colorText, colorSelect, colorBackground, wholeHeight` | 1‑px frame; focused = inverse fill; drop-down panel below, height `min(wholeHeight-h, n×size)`, filled `colorBackground`, hovered row inverse. |
| **Active text** `CT_ACTIVETEXT`=11 (`UIControlsSlider.cpp#L72-L295`) | `text, font, size/sizeEx, color, colorActive, colorFocusBg (remaster), action, sound*` | Plain text; `colorActive` on hover; disabled = 25% alpha; focus/default = underline (default at 50% alpha). |
| **Toolbox** `CT_TOOLBOX`=6 / checkboxes 7 (`#L297-L500`) | `strings[], rows, columns, colorText, colorTextSelect, color, colorSelect, colorTextDisable, colorDisable, font, size/sizeEx` | Grid of text cells; the selected cell gets a 1‑px outline inset 0.005 (outline colour = `colorSelect` when focused, `colorDisable` when disabled, else `color`); selected text in `colorTextSelect`. The editor mode bar (Units/Groups/Triggers/Waypoints/Synchronize/Markers) is this control, IDC 104. |
| **Slider** `CT_SLIDER`=3 (`#L502-L851`) | `color`, style `SL_HORZ/SL_VERT` | Pure line art: spin triangles at the ends, a ruler with power-of-two tick marks, and a triangular thumb. |
| **Scrollbar** (inside list/combo) (`#L853-L985`) | inherits list colour | Frame, chevron spins of 0.8×width, rectangular thumb. |
| **Progress** `CT_PROGRESS`=8 (`#L987-L1012`) | `colorFrame, colorBar` | frame + bar. |
| **HTML** `CT_HTML`=9 (`UIControlsExt.cpp#L66-L106`) | `colorBackground, colorText, colorBold, colorLink, colorLinkActive, H1..H6/P >> font, fontBold, size/sizeEx` | Briefing renderer (not used on the editor map screen). |
| **Map** `CT_MAP`=100 | see §5 | Procedural. |
| **Azimuth picker** (C++ subclass `CStaticAzimut` on IDC 114 / group IDC 105) (`UIArcade.cpp#L43-L107`) | static keys | Static picture + a dark (0.08,0.08,0.12) triangle needle; click snaps to 5°. |

**Consequence:** a pixel-faithful classic skin needs very little art: line primitives, solid fills, one tiled
background texture, cursors, fonts and map icons.

Caveat **[V]**: the remaster's only renderer (`engine/PoseidonGL33`) turns every 2D `DrawLine` into a **3‑px‑wide
quad** textured with `textureLine`, using v = 0.25..1 across its width (`EngineGL33_2D.cpp#L112-L167`). The visible
width and softness of "1‑px" frames therefore depend on that data texture. Our renderer should emulate this, or
offer it as an option. The exact look is **[U]** until measured against a real install.

Several constants are in **physical pixels**
(6‑px bevel, 6‑px focus inset, 1‑px lines). At 4K they look thinner than at 800x600. We should offer a
"pixel-exact" mode (as the engine does) and a "scaled" mode that multiplies these by `Height2D/600`. **[I]**

---

## 4. Resolution, aspect ratio, UI scaling [V]

- The UI is authored on an **800x600 canvas** (CE makes this explicit in `LayoutCanvas::kWidth/kHeight`,
  `CE:engine/Poseidon/UI/LayoutCanvas.hpp#L7-L17`; CWR hard-codes `/600`, `4/3`, `16/800`).
- `Width2D/Height2D` = the UI rectangle `(uiTopLeft .. uiBottomRight) × window px`
  (`CWR:engine/Poseidon/Graphics/Core/Engine.cpp#L113-L129`).
- Remaster policy (`CWR:engine/Poseidon/UI/Settings/AspectRatio.cpp#L12-L22`, `#L85-L221`):
  - **Modern** (default, with `Clamp21x9`, `Presentation.cpp#L14-L15`, `#L43-L46`):
    - From 4:3 up to 16:9 (+2% tolerance), the UI rect is the **full window**, so 4:3-authored dialogs stretch
      horizontally.
    - Between 16:9 +2% (≈1.81) and the clamp ratio (21:9 ≈ 2.33, inclusive), nothing overrides
      `BuildSettingsForRatio`, so the UI is a **centred 4:3 pillarbox band**.
    - Wider than the clamp, the UI is a centred band of the clamp ratio (`ApplyCenteredUiBand`).
    - Narrower than 4:3 (e.g. 5:4), it is a **letterboxed** 4:3 band: full width, reduced height.
    - `ClampOff` means the full window at every ratio.
  - **Legacy**: always the full window (classic OFP stretch).
  - A dev "live override" (`ResolveLive`, `AspectRatio.cpp#L333-L432`) follows different rules. It is only used when
    `Live().overrideEnabled` is set (`Presentation.cpp#L62-L66`).
- Text width compensates via `leftFOV/topFOV`, so glyphs keep their proportions even when boxes stretch
  (`FontDraw.cpp#L76`).
- The map keeps world proportions: `_scaleY = (H/W) × _scaleX` (`UIMap.cpp#L2426-L2441`).
- Legacy CWA 1.99 exposed the same idea through user-config keys (`uiTopLeftX` etc. are still written and read from
  the user cfg, `Engine.cpp#L275-L296`). Widescreen fixes of the old game edit these; see the Faguss "OFP Aspect Ratio" PDF
  (not parsed here). **[U]** for 1.99 defaults.

**Recommendation [I]:** implement a `UiRect` policy enum {`Stretch4x3` (legacy), `Modern` (default), `Pillarbox4x3`}.
Make the map control **fill the window at any aspect** — the editor's biggest win in a standalone window — while
dialogs follow the policy. Because x/w are fractions, resizing the window is free.

---

## 5. The 2D map control (how the editor map is drawn)

Class chain: `CStaticMap` → `CStaticMapArcadeViewer` → `CStaticMapArcade`. The editor creates it with
**scaleMin 0.001, scaleMax 1.0, default 0.1**, hard-coded rather than taken from config
(`CWR:engine/Poseidon/UI/Map/UIMapExtDisplay.cpp#L478-L487`). **[V]**

### 5.1 Coordinates and zoom [V]

- `scale` = fraction of the island that spans one unit of UI width. `WorldToScreen`:
  `x = X/LandSize/scale + mapX + ctrl.x`, `y = (1 - Z/LandSize)/scaleY + mapY + ctrl.y`
  (`UIMap.cpp#L459-L474`). North is up.
- Reference density `ptsLand = 800 / scale / LandRange` = "pixels per terrain cell at 800 px width". It drives
  every level-of-detail decision, independent of the real resolution (`UIMap.cpp#L743-L751`).
- The wheel zooms by `exp(0.1·dz)` around the mouse cursor (`SetScale`, `UIMap.cpp#L2496-L2523`). Numpad keys pan.
  CE routes the wheel through bindable actions (§ CE diff).
- The initial centre is `CfgWorlds >> <world> >> centerPosition`, or the player unit if there is one
  (`UIMap.cpp#L250-L256`, `UIMapExt.cpp#L1060-L1069`).

### 5.2 Background layers, in draw order (`CStaticMap::DrawBackground`, `UIMap.cpp#L743-L1104`) [V]

| # | Layer | Algorithm / LOD | Colour source |
|---|---|---|---|
| 0 | Paper | tiles the control's own picture every 0.5/scale if the control has a texture (`style` `ST_PICTURE` + `text`) | control `colorBackground` × texture — **whether CWA's map class uses a paper texture is [U]** |
| 1 | Sea | per block of `ceil(6/ptsLand)` cells; depth ≤ −5 m is solid sea; −5..+5 m fades alpha from sea to 0 (shoreline gradient) (`#L1374-L1443`) | `colorSea` |
| 2 | Textures ("Show Textures" button, `_showScale=false`) | per-cell ground texture average colour ×0.75, or at full zoom the texture itself ×1.5 random tint; alpha `0.5 + 0.1·height` (`#L1248-L1372`) | terrain textures from WRP |
| 3 | Contours | marching triangles per terrain cell; interval = `50·scale` rounded up to 2/5/10 × 10ⁿ (**5 m at the default zoom**); below-sea lines use a separate colour (`#L850-L895`, `#L1876-L1969`) | `colorCountlines`, `colorCountlinesWater` |
| 4 | Forests | fill "FOREST SQUARE" cells, or a half-cell triangle for "FOREST TRIANGLE" oriented by object heading; only if `ptsLand ≥ 6` (`#L1488-L1578`) | `colorForest` |
| 5 | Forest borders | outline edges without a forest neighbour (`#L1724-L1797`) | `colorForestBorder` |
| 6 | Roads | two edge lines per road segment between memory points `LB/PB` and `LE/PE` (bounding-box fallback); only if `ptsLand ≥ 2` (`#L1799-L1874`) | `CfgInGameUI>>IslandMap>>colorRoads` |
| 7 | Objects | buildings/houses/fences/walls as rotated bounding-box quads in the **model's own colour**; other types as icons (Tree, SmallTree, Bush, Church, Chapel, Cross, Rock, Bunker, Fortress, Fountain, ViewTower, Lighthouse, Quay, Fuelstation, Hospital, BusStop). Only if `ptsLand ≥ 10`; thinned with a world-anchored stride below 15 pts (`#L613-L630`, `#L963-L996`, `#L1580-L1722`) | map-class sub-classes `<Type> >> icon, color, size` (`#L230-L235`, `#L312-L327`) |
| 8 | Town names | `CfgWorlds>>world>>Names>>*>>{name, position}`; decluttered within `1000·scale` m; size `sizeNames × 0.05/scale`, clamped to 0.5–2 × font height (`#L1000-L1036`, `#L1169-L1204`) | `colorNames`, `fontNames` |
| 9 | Spot heights | local maxima of the heightmap (`Geography.cpp#L512-L543`; OPRW also stores a mountain list, `WrpReader.hpp#L59`), decluttered within 1000·scale m; tiny rectangle outline (px x..x+1, y−1..y+1) + `"%.0f"` label at size 0.02 (`#L1038-L1083`, `#L1206-L1242`) | `colorCountlines` / `colorNames` |
| 10 | Grid | lines + labels on **all four edges**; step/format chosen by zoom from `CfgWorlds>>world>>Grid>>*{zoomMax, format, formatX, formatY, stepX, stepY}` + `offsetX/Y` (`#L1971-L2045`, `WorldInit.cpp#L940-L992`) | `colorGridMap` (lines), `colorGrid` + `fontGrid` (labels) |

An object's map class comes from its **P3D named property `map`** (`"TREE"`, `"HOUSE"`, `"FOREST SQUARE"`, …)
(`CWR:engine/Poseidon/Graphics/Rendering/Shape/ShapeLOD.cpp#L1009-L1118`; missing or unknown values → `MapHide`).
Faithful map rendering therefore needs
per-model metadata: the `map` property, the bounding box, the memory points for roads and the average colour.
We can precompute this once per install into a cache. **[V/I]**
`DrawLegend` (scale bar, contour note) runs only on the in-game map, **not** in the editor (`UIMapMain.cpp#L1641`). **[V]**
The legacy parameters `colorLevels`, `colorRocks`, `colorPowerLines`, `maxSatelliteAlpha` are **not read by
Poseidon** (0 grep hits in the whole CWR repo) **[V]**. That they belong to later Arma engines is (unverified).

### 5.3 Editor overlay (`CStaticMapArcadeViewer::DrawExt`, `UIMapExt.cpp#L426-L937`) [V]

| Element | Drawing | Colour / icon source |
|---|---|---|
| Sync lines | straight lines between all members of a sync group; full colour if either end is selected, else "inactive" (colour × `colorInactive`) (`#L458-L542`) | `IslandMap>>colorSync`, map `colorInactive` |
| Waypoint route | leader → wp1 → wp2 … lines, each with a 12‑px arrowhead; the active group is full colour (`#L585-L613`) | `colorActiveMission` |
| Waypoint marks | icon + optional placement circle + camera icon at +0.02 if it has effects (`#L614-L630`) | map `Waypoint>>icon,color,size`; `IslandMap>>iconCamera`, `colorCamera` |
| Group links | leader → member lines, leader → group-trigger lines (`#L633-L699`) | `colorGroups` / `colorActiveGroup` |
| Triggers | ellipse (line segments ≈ every 5 px, 6–720 segments) or rotated rectangle outline + 16‑px icon; unselected at half alpha (`#L60-L167`, `#L661-L680`, `#L839-L893`) | `colorSensor`, `iconSensor` |
| Units / vehicles | `CfgVehicles>>class>>icon` rotated by azimuth; size = `mapSize/LandSize/scale × 640` px@640, min 16; colour by side relation: friendly/enemy (via `friends ≥ 0.5`), civilian/logic, empty = unknown; **unselected = half alpha**; placement-radius circle; player/playable marker (`#L701-L837`, `ArcadeTemplate.cpp#L394-L396`) | `colorFriendly, colorEnemy, colorCivilian, colorUnknown, colorMe, colorPlayable, iconPlayer` |
| Unit→marker links | lines | `colorGroups` / `colorActiveGroup` |
| Markers | **only drawn in Markers mode** in the editor. Icon markers: `CfgMarkers>>type>>icon,size,color` (or `CfgMarkerColors`), text label beside. Area markers: rectangle/ellipse filled with the `CfgMarkerBrushes>>texture` in screen space, or 50% alpha solid (`#L895-L934`, `#L178-L359`, `ArcadeTemplate.cpp#L762-L798`) | marker colour |
| Hover label | name/type + up to 6 detail lines (presence %, condition, init, waypoint type/behaviour…), placed below the object if y<0.7, else above (`#L1708-L1940`) | `colorLabelBackground` (details at 75% alpha), `fontLabel`/`sizeLabel`, text in `colorInfoMove` |
| Drag line | object → cursor while dragging in Groups/Synchronize mode (`#L939-L1041`) | `colorDragging` |
| Rubber-band select | 1‑px rectangle, **hard-coded green (0,1,0,1)** (`#L1042-L1055`) | — |
| Crosshair | full-length cursor lines to the map edges, gap 16/800 × 16/600, half alpha, drawn when the cursor is not `Arrow` (`UIMap.cpp#L2158-L2200`) | cursor colour |

`DrawSign` sizes are expressed in **pixels of a 640x480 reference** and then normalised
(`w/=640; h/=480`, `UIMap.cpp#L495-L500`). We must keep this to match icon sizes. **[V]**

### 5.4 Map config keys (checklist) [V]

- On the **map control class** in `resource` (`UIMap.cpp#L245-L330`): `colorSea, colorForest, colorCountlines,
  colorCountlinesWater, colorForestBorder, colorNames, colorInactive`,
  `fontLabel/sizeLabel|sizeExLabel`, `fontGrid/…Grid`, `fontUnits/…Units`, `fontNames/…Names`,
  `scaleMin/scaleMax/scaleDefault` (overridden in the editor), sub-classes `Tree … BusStop, Waypoint,
  WaypointCompleted` each `{icon, color, size}`, plus the `CStatic` keys (`text, style, font, sizeEx,
  colorText, colorBackground`).
- In **config.bin `CfgInGameUI >> IslandMap`** (`#L334-L364`): `iconPlayer, iconSelect, iconCamera, iconSensor`,
  `colorFriendly, colorEnemy, colorCivilian, colorNeutral, colorUnknown, colorMe, colorPlayable, colorSelect,
  colorSensor, colorDragging, colorExposureEnemy, colorExposureUnknown, colorRoads, colorGrid, colorGridMap,
  colorCheckpoints, colorCamera, colorMissions, colorActiveMission, colorPath, colorInfoMove, colorGroups,
  colorActiveGroup, colorSync, colorLabelBackground`.
- **Per world** in `CfgWorlds`: `centerPosition, Names, Grid`. **Per vehicle**: `icon, mapSize, displayName`.
  **Markers**: `CfgMarkers`, `CfgMarkerColors`, `CfgMarkerBrushes`.

---

## 6. Fonts [V]

- Legacy engine fonts are **FXY + PAA pages**. An `.fxy` file is a flat array of 12-byte records of 6 LE `u16`:
  `char, page, x, y, w, h`. Pages are `<fontname>-NN.paa`. Glyph size is `(w-1, h-1)`, the font height is the
  max glyph height, and the parser sets glyph 0's width to 3/4 of the max width (`CWR:engine/Poseidon/Graphics/Rendering/Draw/FontData.cpp#L34-L92`).
  The bitmap draw path reads bytes as 8-bit codepage characters (`FontDraw.cpp#L86-L137`). It advances spaces,
  control characters and out-of-range characters by the width of glyph `'o'` (`FontDraw.cpp#L77-L99`).
- The **remaster replaces fonts with FreeType TTFs** through a prefix table (`Font.cpp#L37-L60`):
  `tahomab*`/`fontmaincz*` → `Fonts\cwr_body.ttf`, `couriernewb*` → `cwr_mono.ttf`, `garamond*` → `cwr_serif.ttf`,
  `steelfishb*`/`impact*` → `cwr_title.ttf`, `audreyshand*` → `cwr_hand.ttf`. `cz_`/`ru_`/`pl_` prefixes are
  stripped. A header comment says the trailing digits are parsed for pixel size (`FontMapping.hpp#L5-L7`).
  However, `ParseTrailingSize` (`Font.cpp#L160-L165`) has no caller in this snapshot. `Height()` uses the row's
  fixed `bitmapMaxHeight` (§3.1). Each row also carries `bitmapMaxHeight`, `renderPx`, `widthScale`,
  `syntheticOblique`, `baselineOffset`, `syntheticBold` and `letterSpacing` to match the old metrics
  (`FontMapping.hpp#L17-L34`). Load order: TTF mapping first (when the TTF exists), `.fxy` fallback (`#L277-L360`).
  The source calls this "the default OFL set under fonts/" and says "Hand = Caveat" (`FontMapping.hpp#L9-L10`,
  `Font.cpp#L37-L41`). The TTFs are **not** in the repo; they ship with game data (only
  `tests/fixtures/font/dummy.ttf` and a synthetic `legacy.fxy` are present). **[V]**
- **Family names (from test comments, [V] as quotes, not checked against the TTFs):**
  `CWR:tests/unit/engine/Poseidon/Graphics/Rendering/test_font_mapping.cpp#L29-L75` labels the families as follows.

  | File | Family (per test comment) |
  |---|---|
  | `cwr_title` | "Oswald 700" |
  | `cwr_body` | "Roboto 700" |
  | `cwr_mono` | "Unuaranga Kuriero Bold" (family not identified) |
  | `cwr_serif` | "Vollkorn 700" |
  | `cwr_hand` | "Caveat" |

  Confirm them from the TTF `name` tables of an install. Our fallback theme can take the same upstream families
  from their original publishers. Check each one's licence first; for example, Roboto releases have shipped under
  Apache‑2.0 and under OFL (unverified which).
- **Recommendation [I]:** support both paths (FXY+PAA for legacy installs, TTF for remaster). Copy the
  per-prefix metric-matching table so that `sizeEx` produces identical line heights.

---

## 7. Asset strategy (legal + practical)

### 7.1 Licences [V]

- Engine code: GPL‑3.0‑or‑later + §7 terms. Names and logos are not licensed; a fork must not present itself as
  "Arma" (`CWR:README.md#L6-L18`). Porting the algorithms above into our Rust code makes our project a derivative
  of GPL code, so our licence must be GPL-compatible (decided in the licensing doc).
- Game data: **APL‑SA**. It allows share/adapt only for **NonCommercial** and **ArmaOnly** purposes (the text
  says: "You may not convert or adapt this material to be used in other games than Arma"), with **ShareAlike**
  (https://www.bohemia.net/community/licenses/arma-public-license-share-alike). The remastered demo is marketed
  as an "official asset pack" under APL‑SA (GamingOnLinux, 2026‑06; Steam demo description). The full game's Steam
  description also says "Game assets remain under Arma Public License Share Alike" (Steam `appdetails` for 65790).
- The §2a grant *does* permit "reproduce and Share the Licensed Material … for NonCommercial and ArmaOnly purposes
  only", with attribution (§3a) and ShareAlike. "ArmaOnly" is defined as "primarily intended for or directed
  towards the use in any of existing and future Arma games, including … Arma: Cold War Assault".
- **Implications [I]:**
  - (a) Reading the user's installed files at runtime is ordinary use and needs no redistribution.
  - (b) Never commit or ship extracted configs, icons, fonts or layout numbers. This is a **project policy**, not a
    flat legal ban. APL‑SA might allow non-commercial redistribution of CWA-directed material, but bundling would
    tie NonCommercial terms to our GPL releases, and it would break the project rule of synthetic fixtures only.
    Not legal advice.
  - (c) A generated cache on the user's machine (decoded PAA → PNG, map metadata) is fine but must stay local.
  - (d) The IDD/IDC/`ST_*`/`CT_*` numbers are GPL code, not APL‑SA data, and may be reused under GPL terms.

### 7.2 Where to find the data (probe order) [V/I]

| Source | Location | Notes |
|---|---|---|
| Steam *Arma: Cold War Assault Remastered* (app 65790) | `…/steamapps/common/<game>/Remastered/` | CWR-CE: copy binaries "into the `Remastered` folder" (`CE:docs/build/win.md#L79`). Original owners got the remaster free, and old and new **install side by side** (vgtimes, 2026-07). **[V]** |
| GOG *ARMA: Cold War Assault Remastered* | install dir; Remastered layout **[U]** | listed as supported data in CE docs. |
| Steam **demo** (app 4819000, free) | top level of the demo download | full-game binary + demo data "unlock[s] … the editor" (`CE:docs/build/win.md#L11-L12`). BI tests open editor displays 26/27/29 on `data_dir = "packages/Demo"` (`CWR:tests/integration/ui/editor/editor_mission_save_unicode_name.test.toml`, `.sqf#L9-L22`). The official demo exe does **not** register the editor module (`CWR:apps/cwr/GameDemo/GameDemoApplication.cpp#L5-L13`), but that restricts the exe, not the data. **[V]** |
| Legacy CWA 1.99 (Steam/GOG, pre-remaster) | root with `bin\`, `Dta\`, `AddOns\` | FXY fonts, `resource.bin` **[U]**; useful for "original 2009 look". |
| Manual folder | user picks it | also covers old OFP 1.96 (`Res\bin\`) **[U]**. |

Mount rules to replicate: `dta\*.pbo` and `addons\*.pbo` (addon configs merged), `Campaigns\` (only for
missions). Mod directories are searched first (`CWR:engine/Poseidon/Core/GameState.cpp#L262-L281`). Loose `bin\`
files: `config.*`, `config-extra.cpp`, `resource.*`, `resource-extra.cpp`, `remaster.*`, `stringtable.csv`
(`ConfigParsers.cpp`). Picture lookup: mission dir, then `dtaExt\`, then `data\<name>.paa` (default ext `.paa`)
(`UI/OptionsUI.cpp#L697-L743`, `ParamFileExt.cpp#L124-L177`).

### 7.3 Files the editor needs (runtime checklist)

| Need | Where (engine key) | Format |
|---|---|---|
| Dialog layouts | `Res >> RscDisplayArcade*`, `RscDisplayIntel*`, `RscDisplayTemplate*`, `RscDisplaySelectIsland`, `RscMsgBox`, base `Rsc*` templates | `bin/resource.cpp` (text) / `.bin` (rapified) |
| Chrome & cursors | `CfgWrapperUI` | config.bin |
| Map colours, icons | map control class (Res) + `CfgInGameUI>>IslandMap` | config + PAA |
| Unit/vehicle icons | `CfgVehicles>>*>>icon, mapSize` | config + PAA |
| Markers | `CfgMarkers`, `CfgMarkerColors`, `CfgMarkerBrushes` | config + PAA |
| World | `CfgWorlds>>world>>{centerPosition, Names, Grid}` + `worlds\*.wrp` | config + WRP (OPRW v2/v3 or RVW `2WVR`/`3WVR`/`4WVR`, `WrpReader.hpp#L27-L35`, `LandFile.hpp#L16-L45`) |
| Map object classes | P3D `map` property, bbox, memory points `LB/PB/LE/PE` | ODOL P3D inside PBOs |
| Fonts | `fonts\<name>.fxy` + pages, or `Fonts\cwr_*.ttf` | FXY/PAA or TTF |
| Strings | `stringtable.csv` (+ remaster `STRINGTABLE_MAP.utf8.csv`, `UIMap.cpp#L1146-L1149`) | CSV |
| Textures | PAA magics `0xFF01/02/03/04/05` DXT1–5, `0x4444`, `0x1555`, `0x8888`, `0x8080` AI88 (`PAADecoder.cpp#L80-L131`) | PAA |

Whether the demo data contains every one of these is **[U]**. The BI tests only show that the editor displays
open and work. The first engineering task is a `probe` CLI that prints which items resolve on a given install.

### 7.4 Fallback "Classic look-alike" theme (no install found) [I]

The pattern follows Iron Curtain D032, which ships original themes that capture the aesthetic without copying
assets (`iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/decisions/09c/D032-ui-themes.md`). Content
detection with Steam/GOG/manual probing is `…:src/architecture/first-runnable.md#L164-L180`.

1. **Same schema, our numbers.** Store the theme as our own config file using the Rsc key names from §3.3, with
   positions re-measured from public screenshots and our own judgement. Layout arrangements are not
   copyrightable expression (D032 reasoning; not legal advice).
2. **Vector chrome** is already procedural: the bevel/frame algorithms come from GPL code. Pick our own
   `color1..5` ramp (military olive/grey) and our own background tile.
3. **Map palette**: GPL-licensed constants in the engine's WMF map exporter can seed the defaults: sea
   RGB(200,230,253), land white, forest (205,230,154), forest border (102,205,0), roads (123,92,72), contours
   (211,186,163), water contours (128,196,255), grid (112,112,83)
   (`CWR:engine/Poseidon/UI/Map/UIMapExport.cpp#L31-L47`). Whether they match the in-game `config.bin` values is **[U]**.
4. **Fonts**: bundle OFL families only, e.g. Caveat for "hand". The first candidates are the families named in
   the CWR tests (Roboto, Oswald, Vollkorn, Caveat; §6). Each licence still needs confirming, and a mono face is
   still to be picked.
5. **Icons**: author an original SVG set (NATO-ish unit symbols, waypoint circle, trigger flag, marker shapes).
   Without an install there is also **no island**: offer a synthetic demo terrain (procedural heightmap) so the
   editor stays usable for UI and agent development.

---

## 8. Visual element checklist

| Element | Defined in (code, verified) | Values from (data) | Fallback |
|---|---|---|---|
| Top toolbar buttons (Load/Save/Clear/Merge/Preview/Continue/Exit) | `CButton::OnDraw` UIControls.cpp#L2358-L2438; IDCs resincl#L678-L689 | Res `RscDisplayArcadeMap` + `CfgWrapperUI>>Button` | theme file |
| Mode toolbox (Units F1 … Markers F6) | `CToolBox::OnDraw` UIControlsSlider.cpp#L383-L461; keys UIMapExt.cpp#L1436-L1519 | Res `strings[]` (`$STR_DISP_ARCMAP_*`) | theme + our strings |
| Easy/Advanced toggle, IDs, Textures buttons | UIMapExtDisplay.cpp#L429-L474, #L623-L673 | Res + stringtable | theme |
| Mission/Intro/Outro combo | UIMapExtDisplay.cpp#L488-L497; `CCombo::OnDraw` | Res | theme |
| Dialog background + bevel | `ST_BACKGROUND` UIControls.cpp#L404-L462 | `CfgWrapperUI>>Background/Colors` | our tile + ramp |
| Titles, group boxes, frames | UIControls.cpp#L463-L566 | `CfgWrapperUI` | theme |
| Lists, combos, edits, sliders, scrollbars | §3.3 | Res colours/fonts | theme |
| Azimuth needle | UIArcade.cpp#L43-L82 | Res picture | our dial SVG |
| Message boxes | UIContainers.cpp#L1837-L1890 | `RscMsgBox` | theme |
| Cursors | UIContainers.cpp#L240-L269, #L1446-L1469 | `CfgWrapperUI>>Cursors` | OS/our cursors |
| Tooltips | UIControlsBase.cpp#L91-L135, #L288 | per-control keys | theme |
| Map sea/contours/forests/roads/objects/names/heights/grid | §5.2 | map class + `IslandMap` + WRP/P3D + `CfgWorlds` | GPL export palette + synthetic terrain |
| Units/waypoints/triggers/markers/sync/labels | §5.3 | `IslandMap`, `CfgVehicles`, `CfgMarkers*` | our SVG icons |
| Fonts and text metrics | §3.1, §6 | FXY/PAA or TTF | OFL fonts |

---

## 9. Reference screenshots of the original editor

Useful for building the fallback theme and for eyeballing fidelity. Only the pages were fetched; image URLs
reported by the fetch tool were not individually verified.

- OFPEC, *Mission Editor Interface (OFP)*: Easy vs Advanced, Intel, Unit, Group, Trigger, Waypoint and Marker
  dialogs — https://www.ofpec.com/tutorials/index.php?action=read&id=38
- COMBATSIM, *Mission Editing in Operation Flashpoint* (2002): editor map, Intel, insert group, waypoint effects,
  save — https://www.combatsim.com/memb123/htm/2002/09/opflash-me/
- aligrant.com OFP editing intro (text walkthrough of the same layout) — https://www.aligrant.com/web/games/ofp/editing/intro
- BI Community Wiki, *Operation Flashpoint: Elite: Mission Editor* and *2D Editor* (returned HTTP 403 to our fetcher; open them in a browser):
  https://community.bistudio.com/wiki/Operation_Flashpoint:_Elite:_Mission_Editor , https://community.bistudio.com/wiki/2D_Editor
- **Best reference:** generate our own screenshots locally from the GPL engine with the free demo, using the
  existing Trident scripts (`triScreenshot "00_editor_english"` in `arcade_map_language_switch.test.sqf#L48`) at
  several resolutions. Do not commit the images.

---

## 10. Recommendations for implementation

1. **`rsc` crate:** parse text `resource.cpp`/`resource-extra.cpp` and the rapified `.bin` (both first-class, see
   §2.1) into a typed `DisplaySpec`/`ControlSpec`
   (newtypes `Idd`, `Idc`). Be permissive about unknown keys and strict about structure, following the project
   parser rules. Resolve class inheritance and `IDC_STATIC`.
2. **`ui-classic` renderer:** a small immediate-mode layer offering `line`, `rect_fill`, `tiled_texture`,
   `text(font,sizeEx,clip)` and `poly`. Port each `OnDraw` from §3.3 literally, then verify with golden images.
   The choice of GUI toolkit is covered elsewhere; whatever it is, it must allow custom painting at pixel
   precision.
3. **`map2d` crate:** pure functions from (heightmap, cell textures, object list with map metadata, `MapStyle`)
   to a list of draw primitives, with the LOD thresholds from §5.2 as named constants. The primitives can then be
   rasterised, exported to SVG (an equivalent of the engine's `ExportWMF`, `UIMapExport.cpp#L927`) or snapshot
   tested.
4. **`assets` probe:** implement install detection (§7.2) and a report of available items (§7.3). Missing items
   degrade per element to the fallback theme, never to a crash.
5. **Community-requested extras** (toggleable, off in "classic" mode): markers visible in all modes (the original
   shows them only in Markers mode), scalable chrome, a dark theme, a full-window map, and a map legend in the
   editor (the engine draws it only in-game).

---

## Open questions

1. Exact contents of the free demo: which world(s), and whether all `CfgVehicles` icons, `CfgMarkers` and fonts
   are present. Only `Demo` is confirmed by tests. The Steam `appdetails` description of 4819000 mentions "playable
   combat across Everon, Malden, and Kolguyev islands", but that may describe the game rather than the demo data.
   Install app 4819000 and run the probe.
2. Does the remaster ship `bin/resource.cpp` (text) or a rapified `RESOURCE.BIN` plus text `resource-extra.cpp`?
   Code comments conflict (§2.1). Does it still use the OFP-era class names (`RscText`, `RscMapControl`, …) as base
   templates?
3. Does the editor's map class use a paper texture (`ST_PICTURE` + `text`), or a flat `colorBackground`?
4. Font families behind `Fonts\cwr_*.ttf`: the CWR tests name Oswald, Roboto, "Unuaranga Kuriero", Vollkorn and
   Caveat (§6). Confirm this against the TTF `name` tables, identify "Unuaranga Kuriero", and check each licence.
5. Legacy CWA 1.99 layout and defaults (`bin\resource.bin`, `uiTopLeftX…` in the user cfg): verify on a real install.
6. Do Steam/GOG remaster installs keep data in loose `Dta/`/`AddOns/` PBOs identical to the demo? Is the GOG
   layout also `Remastered/`?
7. Does APL‑SA "ArmaOnly" cover a *local cache* our tool derives from the data (e.g. PNGs of icons)? We believe
   yes, as non-distributed private use, but it has not been confirmed with BI.

## Sources

Code (pinned):
- `BohemiaInteractive/CWR@ffc61838b7`: `engine/Poseidon/Core/resincl.hpp`; `engine/Poseidon/UI/Map/{UIContainers,UIMap,UIMapExt,UIMapExtDisplay,UIArcade,UIArcadeWaypoint,UIArcadeMarker,UIMapMain,UIMapExport,UIMapDisplayBriefing}.cpp`, `UIMap.hpp`; `engine/Poseidon/UI/Controls/{UIControls,UIControlsBase,UIControlsImpl,UIControlsSlider,UIControlsExt,UIControlsHTML}.cpp`; `engine/Poseidon/UI/{DisplayUI.hpp,DisplayUIMultiplayerWizard.cpp,OptionsUI.cpp}`; `engine/Poseidon/UI/Settings/AspectRatio.cpp`; `engine/Poseidon/UI/Text/ScreenTextLayout.hpp`; `engine/Poseidon/Graphics/Core/Engine.cpp`; `engine/Poseidon/Graphics/Rendering/Draw/{Font.cpp,FontData.cpp,FontDraw.cpp,FontMapping.hpp}`; `engine/Poseidon/Graphics/Textures/{TexturePreload.cpp,PAADecoder.cpp,PixelFormat.cpp}`; `engine/Poseidon/Graphics/Rendering/Shape/ShapeLOD.cpp`; `engine/Poseidon/World/{WorldInit.cpp,Terrain/Geography.cpp,Terrain/WrpReader.hpp}`; `engine/Poseidon/IO/ParamFileExt.cpp`; `engine/Poseidon/Asset/Addon/ConfigParsers.cpp`; `engine/Poseidon/Core/GameState.cpp`; `engine/Poseidon/AI/ArcadeTemplate.cpp`; `apps/cwr/GameDemo/{CMakeLists.txt,GameDemoApplication.cpp}`; `tests/integration/ui/editor/*.test.{sqf,toml}`; `tests/unit/engine/Poseidon/Core/test_config_system.cpp`; `tests/README.md`; `.trident.env.example`; `README.md`; added in verification: `engine/PoseidonGL33/EngineGL33_2D.cpp`, `engine/Poseidon/UI/Settings/Presentation.cpp`, `engine/Poseidon/Core/Config/ConfigSystem.hpp`, `engine/Poseidon/UI/OptionsUIApp.cpp`, `engine/Poseidon/World/Terrain/LandFile.hpp`, `tests/unit/engine/Poseidon/Graphics/Rendering/test_font_mapping.cpp`, `tests/unit/engine/Poseidon/UI/InGame/test_inGameUI.cpp`, `apps/tetris/Tetris/TetrisNotebookUI.cpp`, `.gitattributes`.
- `ofpisnotdead-com/CWR-CE@b67bf3bd62`: `engine/Poseidon/UI/LayoutCanvas.hpp`; `engine/Poseidon/UI/Map/UIMap.cpp` (diff vs CWR); `docs/build/win.md`; `README.md`; `tests/fixtures/config-replace/bin/resource.cpp`.
- `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9`: `src/decisions/09c/D032-ui-themes.md`, `src/architecture/first-runnable.md`.

Web:
- APL‑SA text: https://www.bohemia.net/community/licenses/arma-public-license-share-alike
- Demo store page (age-gated to our fetcher): https://store.steampowered.com/app/4819000/Arma_Cold_War_Assault_Remastered_Demo/
- Full game store page: https://store.steampowered.com/app/65790/Arma_Cold_War_Assault_Remastered/ ; GOG: https://www.gog.com/en/game/arma_cold_war_assault
- GamingOnLinux, demo + source (2026‑06): https://www.gamingonlinux.com/2026/06/arma-cold-war-assault-remastered-out-with-a-demo-and-its-open-source/
- GamingOnLinux, full release (2026‑07): https://www.gamingonlinux.com/2026/07/arma-cold-war-assault-remastered-is-now-out-in-full-and-open-source/
- VGTimes, free for owners, side-by-side install: https://vgtimes.com/gaming-news/161442-arma-cold-war-assault-remastered-launches-on-steam-with-free-copies-for-original-owners.html
- Steam `appdetails` API (demo type, full game 65790, "official asset pack", APL‑SA): https://store.steampowered.com/api/appdetails?appids=4819000 , https://store.steampowered.com/api/appdetails?appids=65790
- COMBATSIM demo news (mentions Everon/Malden/Kolguyev as game setting; not proof of demo content; unreachable (DNS error) on re-check 2026-09-26): https://www.combatsim.com/2026/06/arma-cold-war-assault-remastered-demo-now-available.htm/
- OFPEC editor interface tutorial: https://www.ofpec.com/tutorials/index.php?action=read&id=38
- COMBATSIM 2002 editor article: https://www.combatsim.com/memb123/htm/2002/09/opflash-me/
- aligrant OFP editing: https://www.aligrant.com/web/games/ofp/editing/intro
- BI wiki (403 to fetcher): https://community.bistudio.com/wiki/Resource.cpp/bin , https://community.bistudio.com/wiki/2D_Editor
- Faguss, OFP Aspect Ratio Configuration (PDF, not parsed): https://ofp-faguss.com/files/ofp_aspect_ratio.pdf

## Verification notes

Adversarial fact-check, 2026-09-26, against the pinned clones and live web pages.

**Checked and confirmed:**
- **Source contents.** No editor `Rsc*` layout data is in either repo. The `Res >> clsName` loader and the
  `ParseResource` order hold. All IDD/IDC/`CT_*`/`ST_*` values quoted hold.
- **Control drawing.** The Static/Button/List/Combo/Toolbox/ActiveText drawing code matches §3.3, including the
  6‑px bevel, 2‑px button bevel, 6‑px focus inset and 0.003/0.004 press shift. Sizes (`sizeEx`, `size × Height()`)
  and `FontDraw.cpp#L75-L76` hold.
- **Editor map.** Hard-coded zoom 0.001/1.0/0.1 (`UIMapExtDisplay.cpp#L484`) holds. So do all map layers and LOD
  constants, the contour step (5 m at 0.1), the sea ±5 m gradient, the P3D `map` property parse, and markers drawn
  only in `IMMarkers`. `DrawLegend` has a single call site. The four legacy map params get 0 grep hits.
- **Fonts.** The TTF prefix table, "OFL set" and "Hand = Caveat" comments hold, and the TTFs are absent from the repo.
- **Assets and licences.**
  - The demo exe does not register the editor (`GameDemoApplication.cpp#L5-L13`).
  - Integration tests use `PoseidonGame` with `data_dir = "packages/Demo"` and open displays 26/27/29.
  - The CE `win.md#L11-L12` and `#L79` quotes hold.
  - The APL‑SA element texts were re-fetched and match.
  - The VGTimes side-by-side quote holds, as do the GamingOnLinux "asset pack" quote and the WMF palette values.
- **CE differences.** A file-by-file hash comparison of the UI and render sources found them identical to CWR
  except for the cursor, LayoutCanvas and wheel-zoom changes, plus non-visual edits.

**Corrected:**
- **Aspect policy** (claim 6). Modern shows a centred **4:3** band between 16:9 +2% and 21:9. It letterboxes below
  4:3. The 21:9 band applies only above the clamp.
- **Chrome textures** (claim 4). The TitleBar texture is preloaded but never drawn. All 2D lines are 3‑px
  `textureLine` quads in GL33.
- **`resource.cpp` plain text** (claim 3). Downgraded to "conflicting evidence": `.gitattributes` and
  `ConfigParsers.cpp` refer to a binary `RESOURCE.BIN`. The `rsc` crate must treat `.bin` as first-class.
- **APL‑SA** (claim 12). "Redistribution not permitted" was too strong. The licence grants NonCommercial + ArmaOnly
  sharing. Not bundling is kept as a project policy.
- **Grep result wording.** Command-menu `Rsc*` test fixtures and a Tetris config snippet exist. The CE fixture has 4
  lines, not 3.
- **Line counts and citations.** `resincl.hpp` is 970 lines, not 870. Fixed citations: ShapeLOD `#L1009-L1118`,
  `Engine.cpp#L275-L296`, the language-switch test `#L95-L98`.
- **Pixel snapping** differs between `CStatic` and the other controls.
- **TrueType `Height()`** uses the per-family `bitmapMaxHeight`. `ParseTrailingSize` has no caller.
- **Space advance.** The bitmap path advances spaces by the width of `'o'`.
- **WRP magics** now list 2WVR/3WVR/4WVR.
- **Spot-height marker** shape corrected.
- **Font family names** added from `test_font_mapping.cpp`.

**Not verified:**
- The demo island list.
- Whether retail data ships text or binary resource.
- The real TTF families and licences.
- Legacy 1.99 paths.
- "Later Arma engines" provenance of the unused map params.
- The COMBATSIM 2026 page (DNS failure).
