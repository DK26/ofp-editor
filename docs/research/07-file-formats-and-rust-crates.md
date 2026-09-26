# File Formats and Rust Crates for the Standalone CWA Mission Editor

Research date: 2026-09-26. This document is for contributors and LLM coding agents, and it stands alone.

It overlaps with `04-mission-data-model-and-formats.md` only on `mission.sqm` and raP. Doc 04 owns the `mission.sqm` schema and the raP byte layout. This document covers every other format and the Rust crate plan.

## TL;DR

- **Formats.**
  - Read: PBO, BI-LZSS, text config + preprocessor, OFP raP (`config.bin`, `resource.bin`, binarized `mission.sqm`), WRP (`4WVR`, `OPRW` v2/v3), a small P3D subset, PAA/PAC, FXY fonts, `stringtable.csv`, SQS/SQF (lint only), WSS/OGG/WAV and JPG.
  - Write: text `mission.sqm`, `description.ext`, `stringtable.csv`, briefing HTML and mission PBOs. [§1]
- **No Rust crate handles OFP-era formats correctly.** HEMTT (v1.22.0, 2026-09-18) targets Arma 3 only:
  - its PBO reader requires a SHA-1 trailer that OFP PBOs lack;
  - its rapifier writes the Arma layout;
  - its PAA crate has no P8/PAC support;
  - its P3D crate reads MLOD only.

  HEMTT is licensed `GPL-2.0`, which SPDX defines as "v2.0 only". It therefore cannot ship in a GPL-3.0 or Apache-2.0 product. [V, §15]
- **CWR's Rust code is not a format library.**
  - `papa-bear-archive` is a ~565-line PBO reader, store-only packer and LZSS decoder. Treat it as a reference and oracle, not a dependency.
  - Trident (`tri`) is a binary-only test orchestrator. It talks JSON over TCP to CWR's `--harness`, so it matters for Preview, not for formats. [V, §14]
- **Recommendation: write our own `ofp-*` crates, spec-first.**
  - Pure `&[u8]` parsers, safe-read cursors, one `Error` enum per crate, and caps on every count and size.
  - Reuse only generic crates: `texpresso`, `zune-jpeg`, `lewton`/`symphonia`, `encoding_rs`, `rodio`. [§16-17]
- **Traps that break Arma-era tools.** [V, §2-4]
  - OFP PBOs have no checksum trailer.
  - The addon mount prefix is the PBO file name; there is no `prefix` property.
  - BI LZSS uses relative back-references, a space-filled 4 KiB window and a 4-byte additive checksum. PBO/OPRW data sums that checksum as unsigned bytes, but texture data sums it as *signed char*.
  - OFP raP is a string pool with varints (versions 2–4), not Arma's offset-table rapify.
- **P3D parsing is required.** The 2D map draws terrain objects from the model's `map` property (precomputed in ODOL), bounding box, average texture colour and `LB/PB/LE/PE` road points. We need a small map-info extractor for ODOL v7 and MLOD, not a renderer. [V, §7]
- **WRP.** Normalize both variants into one `Terrain`. [V, §6]
  - `4WVR`: `i16` heights, 512×32-byte texture names, and 128-byte object records holding a model path.
  - `OPRW` v2/v3: LZSS grids (geography flags, `f32` heights) plus an object-name table.
- **Licensing.** Format crates can be MIT OR Apache-2.0 only if written from specs rather than translated from Poseidon C++. Translated code must be GPL-3.0-or-later and carries Bohemia's Section 7 terms, including a trademark clause. [V/I, §15]
- **Testing.**
  - Mirror CWR's 16 libFuzzer harnesses (with header forcing) as `cargo-fuzz` targets.
  - Reproduce each CWR hardening fix as a synthetic adversarial test.
  - Use CWR's `PoseidonTools` CLI as an opt-in local differential oracle. [V, §16]

## 0. Terms, targets, legend

**Games.**

- **OFP:** *Operation Flashpoint: Cold War Crisis* (2001) plus *Resistance* (1.75–1.96).
- **CWA:** *Arma: Cold War Assault* (1.99).
- **CWR:** *Cold War Assault Remastered*. Its engine source (codename **Poseidon**) is published as BohemiaInteractive/CWR.
- **CWR-CE:** the community continuation of CWR.

**Formats.**

- **PBO:** archive.
- **raP:** binarized config.
- **WRP:** island.
- **P3D:** model, either binarized **ODOL** or editable **MLOD**.
- **PAA/PAC:** textures.
- **FXY:** bitmap-font glyph table.
- **WSS:** BI's wave container.

**Target rule.** Readers accept everything produced by OFP 1.96, CWA 1.99 and CWR. Writers default to OFP 1.96 / CWA 1.99 output. CWR-only features (UTF-8 CSV, TTF fonts, implicit config arithmetic) sit behind `Target::Cwr`.

**Legend.** [V] verified in pinned or fetched source. [I] inferred. [U] unknown.

**Citation aliases.**

- `CWR@ffc61838b7:` = `BohemiaInteractive/CWR@ffc61838b7:`
- `CE@b67bf3bd62:` = `ofpisnotdead-com/CWR-CE@b67bf3bd62:`
- `IC@7b7fac7fa5:` = `iron-curtain-engine/iron-curtain@7b7fac7fa5:`
- `…/` = `CWR@ffc61838b7:engine/Poseidon/`

**CWR vs CE.** In the format files checked, CE is identical to CWR or adds only hardening and logging. [V: hashes/diffs]

- `SsCompress.cpp`, `WrpReader.cpp`, `PAADecoder.cpp`, `PackFiles.cpp` and `ParamFile.cpp` are byte-identical.
- CE's `Pactext.cpp` makes the texture-LZSS `signed char` explicit (`CE@b67bf3bd62:engine/Poseidon/Graphics/Rendering/Font/Pactext.cpp#L404-L470`).
- CE's `QBStream.cpp` differs only in path resolution (`CollapseParentDirs`, mod-root aliases), and `ParamFileParse.cpp` only in a `realpath` buffer fix. Neither changes the on-disk format. [V: diff]

## 1. Inventory

| Format | Where | Editor use | R/W | Engine reference (`…/`) | Plan |
| --- | --- | --- | --- | --- | --- |
| PBO | `Addons\`, `Res\Addons\`, `Missions\`, `MPMissions\`, mods | mount game data; export | R+W | `IO/Streams/QBStream.cpp`, `IO/PackFiles.cpp` | `ofp-pbo` |
| BI LZSS | PBO `Cprs`, OPRW grids, ODOL arrays, 16-bit PAA, PAC | all of the above | R (+W) | `IO/Streams/SsCompress.cpp`, `Graphics/Rendering/Font/Pactext.cpp` | `ofp-bytes::lzss` |
| Config text + preprocessor | `config.cpp`, `.hpp`, `description.ext`, text `.sqm` | catalogs, mission I/O | R+W | `IO/ParamFile/*`, `IO/PreprocC/*` | `ofp-preproc`, `ofp-config` |
| OFP raP | `bin\config.bin`, `bin\resource.bin`, addon `config.bin`, binary `.sqm` | catalogs, UI and map styles | R (W optional) | `IO/ParamFile/ParamFileParse.cpp` | `ofp-config` |
| `mission.sqm` | mission folder or PBO | the edited document | R+W | `AI/ArcadeTemplate.cpp` | `ofp-mission` (doc 04) |
| WRP `4WVR`/`OPRW` | `Worlds\*.wrp`, island addons | 2D map | R | `World/Terrain/WrpReader.cpp`, `LandSave.cpp` | `ofp-wrp` |
| P3D ODOL v7 / MLOD | model PBOs | map symbol, footprint, colour, roads | R (subset) | `Asset/Formats/P3D/*`, `Graphics/Rendering/Shape/ShapeLOD.cpp` | `ofp-p3d` |
| PAA / PAC | UI, map and marker icons, font pages, pictures | visual fidelity | R | `Pactext.cpp`, `Graphics/Textures/PAADecoder.cpp` | `ofp-paa` |
| FXY (+ PAA pages) | `fonts\` | original UI fonts | R | `Graphics/Rendering/Draw/FontData.cpp` | `ofp-fxy` |
| `stringtable.csv` | mission, campaign, game | localized dialogue | R+W | `UI/Locale/Stringtable/*`, `Asset/Formats/Common/CsvReader.cpp` | `ofp-stringtable` |
| SQS / SQF | scripts; trigger and waypoint code | highlighting, lint | R | `engine/Evaluator/express.cpp`, `Game/Scripting/Scripts.cpp`, `Game/Commands/GameStateExt*.cpp` | `ofp-script` |
| Briefing / overview HTML | mission | briefing editor | R+W | doc 04 §6 | `ofp-briefing` |
| WSS / OGG / WAV | sound PBOs, mission `sound\` | effect preview | R | `Audio/Streaming/WaveLoaders.cpp`, `WaveStream.cpp` | `ofp-audio` |
| JPG | overview pictures, CWR loose textures | preview | R | `Graphics/Textures/JpgImport.cpp` (stb_image) | `zune-jpeg` |
| Out of scope (for now) | RTM, `.lip`, `.fps` saves, `.bisign` | — | — | — | — |

## 2. Shared primitive: BI LZSS

Sources: `…/IO/Streams/SsCompress.cpp#L7-L89` (decode) and `#L231-L327` (encode). [V]

**Parameters.**

- `N=4096`, `F=18`, `THRESHOLD=2`.
- The window is pre-filled with spaces, and writing starts at `r=N-F`.

**Stream format.**

- Each flag byte governs 8 tokens.
- A 1-bit is a literal byte.
- A 0-bit is a reference `lo, hi`, where offset = `lo | (hi&0xF0)<<4` and length = `(hi&0x0F)+3`.
- The offset is **relative** to `r`: the encoder emits `(r - match_position) & (N-1)` (`#L280-L282`).
- Classic Okumura LZSS.C stores absolute ring positions [I]. The `lzss` 0.9.1 crate (MIT) uses absolute buffer indices and a bit-packed token stream rather than flag bytes [V: docs.rs source `src/dynamic/decompress.rs`]. So it does not fit as-is.
- A 4-byte LE additive checksum follows the stream.

**Two checksum flavours.**

- PBO entries and `SerializeBinStream` sum `unsigned char` (`#L42`, `#L68`).
- Texture LZSS (`DecodeLZW`, `…/Graphics/Rendering/Font/Pactext.cpp#L368-L482`) sums `(char)c`, i.e. **signed char** (`#L405`, `#L446`).
- HEMTT's decoder skips validation. Its comment says the mismatch "is expected right now with PAAs they store the checksum in a different format". [V: HEMTT `libs/lzo/src/lz77.rs`]

**When compression applies.** `SerializeBinStream` compresses only blocks of ≥1024 bytes; smaller blocks are stored raw (`…/IO/Streams/SerializeBin.cpp#L49-L81`). This rule governs OPRW grids and ODOL arrays. [V]

**Hardening.**

- The engine clamps the final match to the requested length (`SsCompress.cpp#L61-L64`). [V]
- The theoretical maximum expansion is 8 tokens × 18 bytes per 17 input bytes (≈8.47×). We therefore reject `declared_len > 9 × input_len` before allocating. [I: arithmetic]

**API.**

- `decode(input, out_len, ChecksumKind::{Unsigned, SignedChar, Ignore}) -> Result<(Vec<u8>, consumed), LzssError>`
- `encode(input) -> Vec<u8>`, needed only for optional compressed PBO export.

## 3. PBO

**Layout** [V] (`…/IO/Streams/QBStream.cpp#L293-L324`, `#L605-L735`; `…/IO/Streams/FileInfo.h#L10-L18`).

- **Header.** Each entry is a `cstring name`, then five LE `u32`: `packing`, `original_size`, `reserved`, `timestamp`, `data_size`.
- **Terminator.** An entry with an empty name ends the header.
- **Data.** Data blocks follow in header order. `reserved` is ignored. Offsets are the running sum of `data_size`, capped at `INT_MAX`.
- **Packing values.**

  | Value | Meaning |
  | --- | --- |
  | `0` | stored |
  | `0x43707273` `'Cprs'` | LZSS, expanding to `original_size` |
  | `0x56657273` `'Vers'` | properties |
  | `0x456E6372` `'Encr'` | encrypted |

  In `QFBank::Read`, any other value fails with "Unknown compression manager" (`QBStream.cpp#L1051-L1111`). The Win32 overlapped path (`ReadOverlapped`, `#L1137-L1143`) is more lenient: it treats every non-`Cprs` value as stored.

**Properties** [V].

- `Vers` is honoured only as the **first** entry, with an empty name, `data_size==0` and `time==0`. It is followed by `key\0value\0` pairs up to an empty key (`#L624-L720`).
- The engine reads `product`, `encryption` and `pboVersion` for addon acceptance (`…/Core/GameState.cpp#L93-L102`).
- If `encryption` is set, the header itself is encrypted (`#L654-L702`); we report such PBOs as unsupported.

**No `prefix` property** [V: grep].

- The bank prefix is the PBO file name (`#L1352-L1363`). Nothing reads a `"prefix"` property.
- This holds for `dta\` and `Addons\`, which mount with `emptyPrefix`. `Campaigns\` banks get `campaigns\<name>`, and CWR also remaps language-suffixed banks (`…/Core/GameState.cpp#L185-L215`, `#L272-L277`).
- So papa-bear-archive's comment that the property "mounts the addon correctly" (`CWR@ffc61838b7:mserver/Archive/src/pbo.rs#L167-L169`) is wrong for this engine.
- The PMC wiki describes Resistance's product entry as three strings. This parses identically if the last string is empty [I].

**No trailer.**

- OFP/CWA PBOs have no checksum trailer.
- After the header, the engine's only integrity check seeks to header+data (`#L754-L760`). It never reads past the data, so an Arma SHA-1 trailer is tolerated [V code / I runtime].
- The seek does not actually enforce a minimum file length. Win32 `SetFilePointer` and POSIX `lseek` (the `…/Foundation/platform.hpp#L121` shim) both succeed past EOF, so a truncated PBO fails only when an entry is read [I: API semantics]. Our reader should check the length explicitly.
- The PMC wiki reports 5 trailing bytes for Elite and 21 for Arma.

**Names.**

- The engine truncates names at 511 bytes and lowercases them (`#L296-L317`), then converts slashes with `ConvertDirSlash` (`#L621`).
- The packer converts `/` to `\` (`CanonicalBankEntryName`, `…/IO/PackFiles.cpp#L47-L58`) and writes names as given (`#L175-L202`).
- Names are raw ANSI bytes [I]: keep them as bytes and compare case-insensitively.

**BI packer quirks** [V] (`PackFiles.cpp#L484-L589`).

- Timestamps are `st_mtime`.
- `.pbo`, `.ogg`, `.wss` and `.jpg` files are never compressed (`#L467`).
- The terminator entry is appended before the compress loop, so it also gets `'Cprs'` (`#L315-L319`, `#L551-L571`). CWR's synthetic `tests/fixtures/pbo/mission_fixture.Intro.pbo` shows this.
- Therefore, never require packing `0` on the terminator.

**Writer defaults.**

- No `Vers` entry for missions.
- Stored (uncompressed) entries, with `Cprs` only as an opt-in.
- No trailer.
- Names ≤511 bytes, backslash-separated, with no `..` or drive components.
- Keep the original header bytes and order, so an unmodified PBO re-emits byte-identically.

### Existing crates

| Crate (checked 2026-09-26) | Version / date | License | OFP fit | Verdict |
| --- | --- | --- | --- | --- |
| `papa-bear-archive` (CWR `mserver/Archive`) | 0.1.0, in repo | Cargo says `MIT`; the repo is GPL-3.0-or-later + §7 (see §14) | stored + `Cprs` read, LZSS decode only, store-only pack | reference/oracle |
| `hemtt-pbo` | repo 1.22.0; crates.io 1.0.0 (2023-03-16) | `GPL-2.0` (= only) | `ReadablePbo::from` seeks past the data and then runs `Checksum::read_pbo(...)?`, so it fails without a trailer [V code] | ✗ |
| `pbo` (SynixeBrett/pbo-rs) | 0.1.3 (2019) | GPL-3.0-or-later | Arma; unmaintained | ✗ |
| `bi_fs_rs` | 1.0.1 (2026-07) | `GPL-3.0` (= only) | "A Rust library for working with Arma 3 related file formats, such as PBO and BISIGN files." | ✗ |
| `armake2` | 0.3.0 (2018) | GPL-2.0-or-later | Arma 3 | ✗ |
| `rust-pbo-wasm` (ofpisnotdead-com; GitHub only, not on crates.io) | pushed 2023 (unverified) | MIT | OFP reader, parses `Vers`, **no LZSS** | tiny reference |
| `cotillion/ofptools` (C) | 2012 (unverified) | GPL-2.0 | OFP PBO + bin2cpp | historical |

## 4. Configs: text, preprocessor, OFP raP

### 4.1 Text config

The engine's parser is `ParamClass::Parse` (`…/IO/ParamFile/ParamFile.cpp#L1571-L1850`). [V]

**Grammar:**

- `class N[: Base] { … };`
- `name[] = { … };` (arrays nest)
- `name = value;`
- `__EXEC(...)`

**Value typing.** An unquoted value is tried as decimal int, then `0x` hex, then float, then `db<n>` (converted to 10^(n/20)); if none match, it is a string (`#L679-L789`). Strings escape a quote as `""` (`…/IO/ParamFile/ParamFileParse.cpp#L344-L361`).

**Evaluated values.** `__EVAL(expr)` is evaluated at parse time (`ParamFile.cpp#L1805-L1808`). CWR also evaluates any unquoted value that starts with `(` ("implicit arithmetic", `#L1809-L1816`); this is CWR-only. Our syntax tree keeps both unevaluated. [V/I]

### 4.2 Preprocessor

**Supported syntax** (`…/IO/PreprocC/Preproc.cpp#L15-L33`) [V]:

- `#include`, `#define` (with arguments), `#ifdef`, `#ifndef`, `#else`, `#endif`, `#undef`;
- `#` (stringize) and `##` (token paste);
- `//` and `/* */` comments;
- backslash-newline continuation.

There is no `#if` [I: it is absent from the lexer table].

**Include resolution.** A path is tried as given first, then relative to the including file (CWR, `…/IO/PreprocC/PreprocC.cpp#L28-L49`). Whether 1.96 performs the second step is [U].

**Planned API.** `preprocess(src, &dyn IncludeResolver) -> Result<(Vec<u8>, SourceMap), Error>`, with caps on include depth, output size and macro expansions.

### 4.3 OFP raP (full layout: doc 04 §4)

Reader: `ParamFileParse.cpp#L43-L180`, `#L579-L670`, `#L752-L951`. [V]

**Header and encoding.**

- **Magic and version.** Magic `00 72 61 50`, then an `i32` version. The writer emits 4; the reader rejects anything below 2.
- **Pool indices** are 7-bit varints from version 3 (`i32` before that). **Counts** are varints from version 4.
- **Pool order.** A new string must take the next index (`#L108-L117`).

**Entries.**

- **Kind byte:** 0 = class, 1 = value, 2 = array.
- **Value type:** 0 = string, 1 = float, 2 = int. Type 3 (nested array) appears only inside arrays (`ParamFile.cpp#L185-L191`, `#L630-L648`, `#L1054-L1071`).
- **Base names:** a class base name is a plain cstring, not a pool reference (`ParamFileParse.cpp#L762-L769`).
- **Trailer:** an `i32` variables count, which is 0 in plain configs (`ParamFile.cpp#L2208-L2220`; the pair form is in `…/IO/ParamFile/ParamFileEval.cpp#L70-L105`).

**Arma raP is different.** HEMTT writes `"\0raP"`, then `00000000 08000000`, then an enum offset. Its derapifier "skips 8 bytes" after the magic [V: HEMTT `libs/config/src/rapify/config.rs`]. To distinguish the formats, look after the magic: OFP has a version of 2–4, while Arma has `0` then `8`. Report Arma raP as `Error::ArmaRapNotSupported`. [I]

**Load order.** The engine tries binary before text [V]:

- in the mission loader `ParseCutscene`, which `ParseMission`/`ParseIntro` call (`…/UI/Map/UIArcadeWaypoint.cpp#L920-L929`, `#L980-L988`);
- in the mission-list title lookup inside PBOs (`…/UI/OptionsUIImpl.cpp#L280-L294`);
- in `ParseBinOrTxt` (`ParamFileParse.cpp#L1037-L1044`).

**Why raP matters for fidelity.** Map colours come from the map control's resource class and from `cfgMap` (`…/UI/Map/UIMap.cpp#L258-L267`, `#L339-L356`). Map-symbol icons, `CfgWorlds` names and every catalog also come from config. [V]

**Existing crates.** `hemtt-config` and `hemtt-preprocessor` (GPL-2.0, chumsky/pest, Arma semantics) and `armake2` (GPL-2.0-or-later, 2018) do not fit. We build a lossless CST (doc 04 §12) plus a resolved view with case-insensitive inheritance lookup for catalogs.

## 5. `mission.sqm`

**Structure.** A `mission.sqm` is a config file; text is canonical and binary is read-only. [V/I]

- **Sections.** The top level has `Mission`, `Intro`, `OutroWin` and `OutroLoose` (BI's spelling; `…/UI/Map/UIMapExtDisplay.cpp#L106-L121`).
- **Section contents.** Each holds `addOns[]`, `addOnsAuto[]`, `show*`, `randomSeed`, `Intel`, `Groups`, `Vehicles`, `Markers` and `Sensors` (`…/AI/ArcadeTemplate.cpp#L1934-L1981`).

**Addon check.** Loading fails with `LSNoAddOn` if `addOns[]` names a missing `CfgPatches` (`#L1946-L1955`).

- The check compares against `CfgPatches` class names (`CheckPatch`, `#L1875-L1900`).
- The loader then shows the missing names and rejects the mission, because no groups were loaded (`…/UI/Map/UIArcadeWaypoint.cpp#L933-L970`).
- `addOns[]` is computed from each patch's `units[]` (`ArcadeUnitInfo::RequiredAddons`, `ArcadeTemplate.cpp#L321-L340`). So the editor must index `CfgPatches` class names and `units[]` across every mounted addon config before saving.

**Details.** See doc 04 for the schema, IDs and round-trip rules. `sqm_parser` 1.0.1 (MIT, 2019) targets Arma 3. ✗

## 6. WRP (islands)

**Formats.** The first 4 bytes select the reader (`…/World/Terrain/WrpReader.cpp#L51-L73`) [V]:

- `2WVR`, `3WVR` and `4WVR` are the legacy editable format;
- `OPRW` is the binarized format.

The PMC wiki calls OPRW "BI's official format for all wrp files in the game" and 4WVR the "unpacked" community format (WrpTool, Visitor). We need both.

**4WVR** (`WrpReader.cpp#L75-L204`; structs in `…/World/Terrain/LandFile.hpp#L13-L53`; generator `CWR@ffc61838b7:tests/fixtures/wrp/generate_test_world.py#L1-L24`) [V]:

| Field | Type |
| --- | --- |
| magic | `"4WVR"` |
| grid | `i32 x, i32 z`; CWR's `WrpReader` caps each at 2048 (`#L81-L87`). The runtime 4WVR loader (`Landscape::LoadData`, `LandSave.cpp#L58-L150`) does not use `WrpReader`. |
| heights | `i16[x*z]`; metres = raw × 0.045 (`LANDDATA_SCALE`, `#L119-L133`) |
| texture index grid | `u16[x*z]` |
| texture names | 512 × 32-byte NUL-padded strings (`landtext\…pac`) |
| objects, until EOF | 128 bytes each: `f32[12]` (aside, up, dir, position), `i32 id`, `char[76]` model path (`data3d\….p3d`). v2/v3 differ only in this record (`LandFile.hpp#L21-L40`). |

**OPRW v2/v3** (`WrpReader.cpp#L208-L389`; writer `…/World/Terrain/LandSave.cpp#L1278-L1384`) [V]:

1. `"OPRW"`, then an `i32` version (2 or 3). v3 adds `i32 landX, landZ, terrainX, terrainZ`; v2 is always 256².
2. Grids, each LZSS-compressed if ≥1024 bytes:
   - `geography u32[cells]` — bits `waterDepth:2, full:1, forestInner:1, forestOuter:1, road:1, track:1, slow:1, …` (`…/AI/Path/AITypes.hpp#L39-L57`);
   - `soundMap u8[cells]`;
   - `mountains` — `i32` count plus `f32×3` each, uncompressed;
   - `tex u16[cells]`;
   - `random u32[cells]`;
   - `heights f32[cells]`, in metres.
3. `i32 textureCount` (capped at 65536), then per texture a `cstring` and a `bool` byte.
4. An object-name table: `i32` count, then cstrings.
5. Objects `{i32 id; i32 nameIndex; f32[12]}` until `id < 0` or EOF. The engine had to add an EOF guard here (`#L363-L368`).

**Height-grid caveat [U].** `WrpReader` sizes heights by the land grid, but `LandSave` transfers `_data.RawSize()` (the terrain grid). For v3 files where `terrainX != landX`, the right size is unclear; test with a synthetic file.

**What the 2D map draws** (`…/UI/Map/UIMap.cpp`) [V]:

- **Heights:** shading, sea and contour lines (`DrawField` `#L1248`, `DrawSea` `#L1374`, `DrawCountlines` `#L1948`).
- **Forests:** forest-typed objects, plus the `forestInner/Outer` flags for borders (`#L1488-L1578`, `#L1724-L1797`).
- **Buildings, fences and walls:** the model's bounding box in the model's colour (`#L1580-L1645`).
- **Icons:** trees, churches and similar objects (`#L1646-L1694`).
- **Roads:** lines between `LB/PB/LE/PE` memory points of `Network` objects (`#L1799-L1874`).
- **Mountain labels:** `DrawMount` `#L1206`.
- **`CfgWorlds` names:** `DrawName` `#L1169`.

4WVR has no geography or mountains (the engine derives them at load), so we compute `forestInner/Outer` ourselves [I].

**Existing crates.** None on crates.io. HEMTT's workspace (`common, config, lzo, p3d, paa, pbo, preprocessor, signing, sqf, stringtable, workspace, wss`) has no WRP crate. [V]

## 7. P3D: needed, but only a "map info" subset

**Why we need it** [V]:

- A model's `MapType` comes from its `map` named property: `TREE`, `SMALL TREE`, `BUSH`, `BUILDING`, `HOUSE`, `FOREST BORDER/TRIANGLE/SQUARE`, `CHURCH`, …, `FENCE`, `WALL`, `HIDE`, `BUSSTOP`. If the property is missing or unknown, the type is `MapHide` (`…/Graphics/Rendering/Shape/ShapeLOD.cpp#L1009-L1118`, `…/World/MapTypes.hpp#L7-L21`).
- Building colour is the average of the model's texture colours, weighted by face area and texture alpha (`…/Graphics/Rendering/Shape/Shape.cpp#L62-L93`).
- So the map cannot be drawn from the WRP alone.

**ODOL v7 (official models)** [V]. The model trailer follows all LODs and already holds `color`, `colorTop`, `minMax` (the bounding box) and `mapType` (`…/Asset/Formats/P3D/P3DStructures.hpp#L463-L524`). We must still walk the LODs, both to reach the trailer and to read the memory-LOD named points that roads use.

**Version mismatch** [U]. `FormatDetector` accepts ODOL v7/v8 and MLOD 1.0/1.1 (`…/Asset/Formats/Common/FormatDetector.cpp#L84-L96`), but `P3DStructures::readHeader` accepts only v7 (`#L27-L49`). Parse v8 with v7 rules and report failures.

**MLOD (community addons)** [I]. Read the LOD named properties (`map`, `class`), the vertex bounding box, the texture names and the memory-LOD selections. Colour comes from the PAA `AVGC` tags (§8).

**Existing crates.** `hemtt-p3d` is MLOD-only (it rejects non-`MLOD` files) and GPL-2.0 [V]. `p3dtxt` 0.2.0 is Arma 3-era (2018) and licensed GPL-2.0-or-later [V: crates.io API].

**Output.** `ofp-p3d` returns `MapInfo { map_type, bbox: [Vec3; 2], color: Option<Rgba>, road_points: Option<[Vec3; 4]>, textures, class }`.

- No rendering and no animation.
- Results are cached per island (model path → `MapInfo`) at import time.
- On a parse failure, record `MapHide` plus a diagnostic.

## 8. PAA / PAC textures

Sources: `…/Graphics/Rendering/Font/Pactext.cpp#L139-L353,L484-L600,L875-L960,L1102-L1247,L1364-L1433`; `…/Graphics/Textures/PAADecoder.cpp#L80-L132,L403-L546` [V]. The file sections, in order:

1. **Format tag.** An optional `u16`. If it is unrecognized, rewind and default to ARGB4444 (`.paa`) or P8 (`.pac`) (`PAADecoder.cpp#L408-L415`).
2. **TAGGs.** Each is `"GGAT"`, a 4-byte name, a `u32` size and the data: `AVGC` is the average colour; `FLAG` holds alpha/transparency bits; `OFFS` has up to 16 mip offsets. Unknown tags are skipped.
3. **Palette.** A `u16` count (≤256), then 3 bytes per entry. Transparent colours are replaced by `AVGC`.
4. **Mips.**
   - Each mip is `u16 w`, `u16 h`, `u24 size`, then data. `w=h=0` ends the list.
   - `w=1234, h=8765` (PAC) means LZSS data follows, with the real `w, h` next.
   - The engine accepts sizes 2..4096 (`Pactext.cpp#L1411`); the tools decoder caps at 8192.

| Tag | Format | Storage in OFP/CWA |
| --- | --- | --- |
| `0xFF01`..`0xFF05` | DXT1–5 | raw blocks (no LZO; that is Arma's `w & 0x8000` flag) |
| `0x4444`, `0x1555`, `0x8080` | ARGB4444, ARGB1555, AI88 | LZSS with a signed-char checksum |
| `0x8888` | ARGB8888 | raw in the CWR decoder; support in retail 1.99 is [U] |
| none (`.pac`) | P8 palette | RLE: if `c & 0x80`, repeat the next byte `(c&0x7F)+1` times; otherwise copy `c+1` literals. Or LZSS behind 1234×8765. |

**Existing crates.**

- **`hemtt-paa`** (GPL-2.0) decodes DXT1/3/5 via `texpresso`, plus ARGB4/1555/8888 and AI88. DXT2/4 hit `unimplemented!()`, which panics. It has no P8/PAC support and no headerless default. [V: fetched summaries of `libs/paa/src/pax.rs` and `mipmap.rs`; re-check the details]
- **`texpresso`** 2.0.2 (MIT, 2025-05) decodes BCn.

**Plan.** Our own `ofp-paa`, returning RGBA8 plus `avg_color`, flags and mip selection. It uses `texpresso`, or ~150 hand-written lines for DXT1/3/5. No encoder is needed.

## 9. Fonts: `.fxy` + PAA pages

**FXY layout** [V]. A flat array of 12-byte records: `u16 char, page, x, y, w, h`. The glyph size is `w-1`×`h-1`, pages are `<font>-NN.paa`, and the space width is `maxW*3/4` (`…/Graphics/Rendering/Draw/FontData.cpp#L34-L92`).

**CWR fonts** [V]. CWR maps legacy names (`tahomab`, `garamond`, `couriernewb`, `audreyshand`, `steelfishb`, …) to `Fonts\cwr_*.ttf` via FreeType, and uses `.fxy` only when a name has no mapping (`…/Graphics/Rendering/Draw/Font.cpp#L47-L59`, `#L296-L347`).

**Plan.** For fidelity, render FXY and its PAA pages from the user's own install. Ship an open-licensed fallback font. Never ship BI fonts or CWR's TTFs; their license is [U].

## 10. `stringtable.csv`

**Format** [V].

- **CSV rules.** Cells may be `"`-quoted, with `""` as an escaped quote. Rows end with CR, LF or CRLF (`…/Asset/Formats/Common/CsvReader.cpp#L9-L97`). The first row starting with `LANGUAGE` defines the columns.
- **Code pages.** Legacy files use one code page per language column (`…/UI/Locale/Stringtable/Stringtable.cpp#L281-L339`, `…/UI/Locale/Stringtable/CodepageTranscode.cpp#L74-L110`):
  - CP1252 by default;
  - CP1250 for Czech, Polish, Slovak, Hungarian and others;
  - CP1251 for Russian, Ukrainian and Bulgarian.
- **CWR additions.** CWR adds `*.utf8.csv` shards. It also merges stray cells into the French column when old files contain unquoted commas (`MergeSurplusLegacyCsvCells`).

**Plan.**

- Keep raw rows for lossless round-trips.
- Transcode with `encoding_rs` 0.8.42, licensed "(Apache-2.0 OR MIT) AND BSD-3-Clause".
- Write legacy code pages for OFP/CWA targets, and UTF-8 only for `Target::Cwr`.
- Check AI-generated dialogue for characters the column's code page cannot encode. [I]

**Existing crates.** `hemtt-stringtable` targets Arma's XML format, so it does not apply.

## 11. SQS / SQF (highlighting and validation only)

**Engine sources.**

- The evaluator is `CWR@ffc61838b7:engine/Evaluator/express.cpp`.
- The SQS runner is `…/Game/Scripting/Scripts.cpp`.
- Commands are registered in `…/Game/Commands/GameStateExt*.cpp`.
- CWR adds test/harness commands in `GameStateExtTest*.cpp`, so command tables must be per target. [V: the files exist; I: they are absent from retail builds]

**Oracles.** CWR builds a standalone `PoseidonEvaluator` (`CWR@ffc61838b7:apps/tools/Evaluator/CMakeLists.txt#L9`) and `PoseidonTools lint mission` (`CWR@ffc61838b7:apps/tools/Tools/commands/LintCommand.cpp#L162-L165`). Both are useful as local oracles.

**Plan: `ofp-script`.**

- A tokenizer.
- SQS line and label structure.
- SQF bracket and semicolon structure.
- A per-target command table generated as data (name, arity, argument types).
- No execution.

**Existing crates.** `hemtt-sqf` targets Arma 3 (it depends on `arma3-wiki`) and is GPL-2.0. ✗

## 12. Audio: WSS / OGG / WAV

**Dispatch** [V]. The engine picks a decoder by extension: `.wav` → RIFF, `.ogg` → Vorbis, anything else → WSS (`…/Audio/Streaming/WaveStream.cpp#L146-L164`).

**WSS layout** [V].

- **Optional header.** 8 bytes: `"WSS0"`, a `u8 deltaPack` (0, 4 or 8), and 3 reserved bytes.
- **Format block.** A `WAVEFORMATEX` follows. The reader forces `cbSize=0`, which suggests an 18-byte struct [I].
- **Samples.** Delta packing is 4-bit (4:1) or 8-bit (2:1) (`…/Audio/Streaming/WaveLoaders.cpp#L14-L66`, `WaveStream.cpp#L191-L226`, `…/Audio/Core/Format/WaveBuffer.cpp#L46-L77`).
- **Sniff the content.** CWR's own `click.wss` fixture is actually a RIFF WAV. [V: hex]

**Plan.**

- Our own WSS decoder to `i16` PCM (~150 lines).
- Vorbis via `lewton` 0.10.2 (MIT OR Apache-2.0; last release 2021) or `symphonia` 0.6.1 (MPL-2.0).
- Playback via `rodio` 0.22.2 (MIT OR Apache-2.0).
- `hemtt-wss` is GPL-2.0. ✗

**Later.** CWR also generates `.lip` lip-sync files (`…/Asset/Probes/WaveToLip.cpp`, `PoseidonTools sound lip`). This matters later for AI-voiced dialogue.

## 13. JPG and other images

- CWR decodes JPG with stb_image (`…/Graphics/Textures/JpgImport.cpp#L7`). [V]
- We plan to use `zune-jpeg` (MIT OR Apache-2.0 OR Zlib) or the `image` crate. Its latest stable release is 0.5.15; 0.5.16-rc2 is a pre-release.
- PNG and BMP appear only as CWR tool inputs/outputs. [I]

## 14. CWR's Rust code: Trident and papa-bear-archive

The workspace members are `engine/Trident` and `mserver/{Archive,Client,CLI,MasterService}` (`CWR@ffc61838b7:Cargo.toml#L1-L9`). CE's members are identical. [V]

### Trident [V]

**Package.**

- Crate `tri` 0.1.0, described as a "Playwright-style test orchestrator for CWR game instances".
- `license = "MIT"`, and it denies `unsafe_code` (`CWR@ffc61838b7:engine/Trident/Cargo.toml#L1-L7`, `#L34-L35`).
- It is binary-only: `src/main.rs` with `#![allow(dead_code)]` (`#L8`) and no `lib.rs`.

**Protocol.**

- It spawns the game with `--harness <port>` (`src/client/instance.rs#L70`) and speaks newline-delimited JSON over TCP, protocol v1 (`protocol/harness.schema.json#L1-L141`).
- Commands: `ping`, `describe`, `key`, `key_up`, `click`, `query`, `screenshot`, `wait_display`, `eval`, `exec`, `http_fixture`, `exit`.
- Events include `ready`, `display`, `log` and `mission_state`.

**Scenarios.** About 7,500 lines of scenario code (`src/scenarios/{integration,multi,stress,mod}.rs`) drive SQF tests. `multi.rs` packs seed mods with `papa_bear_archive::Pbo::pack_dir` plus zstd (`src/scenarios/multi.rs#L15`, `#L417-L425`).

**Relevance.**

- It contains no format code.
- It could serve Preview by driving a `--harness` CWR build through `eval`, `exec` and `screenshot`. The flag is defined in `…/Foundation/Platform/AppConfig.cpp#L663-L664`; whether retail builds enable it is [U].
- If we adopt it, copy the protocol types (`src/protocol/types.rs`, 372 lines) rather than depending on the unpublished 0.1.0 binary.

### papa-bear-archive [V: whole crate read]

**API.** `Pbo::{read_path, read_bytes, property, entry_data, read, pack_dir, write, write_path, unpack_to_dir}`.

- LZSS is decode-only, with the unsigned checksum (`CWR@ffc61838b7:mserver/Archive/src/lzss.rs#L1-L79`).
- Tests cover round-trip, a `Cprs` fixture and path traversal.

**Gaps against our rules.**

- `anyhow` errors;
- direct indexing (`buf[*cur]`, `buf[header_size..data_end]`);
- an unchecked `offset += data_size as usize`;
- a full `.to_vec()` copy;
- no encoder;
- the wrong `prefix` comment (§3).

### License ambiguity [V facts / I conclusion]

Both crates declare `MIT` in their `Cargo.toml`. However, the repo `LICENSE` and README place the whole source under GPL-3.0-or-later plus Section 7 terms, excluding only `thirdparty/` (`CWR@ffc61838b7:README.md#L49-L60`, `LICENSE#L1-L3`). Treat them as GPL-3.0-or-later + §7 until Bohemia clarifies.

### Other CWR tooling (C++, GPL) [V]

**`PoseidonFormats`** is a C API/DLL over the engine's P3D, PAA, PBO, VFS and RTM loaders. It links the whole engine (`CWR@ffc61838b7:engine/PoseidonFormats/PoseidonFormats.h#L25-L118`).

**`PoseidonTools`** (`CWR@ffc61838b7:apps/tools/Tools/CMakeLists.txt#L13`; e.g. `…/apps/tools/Tools/commands/PboCommand.cpp#L233-L255`, `ConfigCommand.cpp#L204-L271`, `TerrainCommand.cpp#L29-L181`) offers:

- `pbo`: list, show, extract, pack;
- `config`: debin, bin, tojson, dump, search;
- `image`: inspect, convert, compare;
- `font`: inspect, render;
- `model`: inspect, convert;
- `terrain`: inspect, textures, objects, render;
- `sound`: inspect, lip;
- `stringtable`: validate, inspect, lookup;
- `lint mission`.

**Use as an oracle.** Build these tools locally and never vendor them. Use them as an opt-in differential oracle, for example `ofp-wrp` vs `terrain objects`, and `ofp-config` vs `config debin`.

## 15. Ecosystem and license compatibility

### Facts [V]

**HEMTT.**

- Every lib crate checked (`pbo`, `paa`, `config`, `preprocessor`, `sqf`, `wss`, `p3d`) declares `license = "GPL-2.0"`.
- SPDX marks that identifier deprecated, with the name "GNU General Public License v2.0 only".
- The repo has 157 stars, and its GitHub page describes it as "The modern build system for Arma 3 mods". The last-push date was not re-verified, because the GitHub API returned 403.
- Its PBO code says it is partly "derivative work of the code from the armake2 project by KoffeinFlummi, which is licensed GPLv2" (`libs/pbo/src/lib.rs`).

**Other licensing facts.**

- crates.io lists armake2 as `GPL-2.0-or-later`.
- Apache-2.0 is compatible with GPLv3 but not with GPLv2 (Apache Software Foundation).
- GPLv2-only code cannot be combined with GPLv3 code [I: standard FSF position; the fetch failed].

**CWR's Section 7 terms** (`CWR@ffc61838b7:LICENSE#L682-L721`) must accompany any propagation:

- no "ARMA" or "OPERATION FLASHPOINT" trademarks on distributed modifications;
- no claim of affiliation;
- modified versions must be marked;
- indemnification if you assume liability.

### Compatibility

| Source | In a GPL-3.0-or-later app? | In MIT/Apache format crates? |
| --- | --- | --- |
| HEMTT crates (GPL-2.0-only) | no | no |
| armake2 (GPL-2.0-or-later) | yes, as GPL-3 | no |
| `pbo`, `bi_fs_rs` (GPL-3.0*) | yes | no |
| CWR/CE C++ and Rust (GPL-3.0-or-later + §7) | yes, with §7 notices | no (facts and specs only, never translated code) |
| `rust-pbo-wasm`, `sqm_parser`, `lzss` (MIT) | yes | yes |
| `texpresso`, `zune-jpeg`, `lewton`, `rodio`, `encoding_rs` | yes | yes |
| `symphonia` (MPL-2.0) | yes | yes, as a dependency [I] |

### Recommendation [I]

- **License the format crates MIT OR Apache-2.0,** whatever the app's own license is.
- **Write them from our own spec docs.** Ground the specs in BI/PMC/Mikero documentation and black-box tests against CWR's tools, not in translated Poseidon code. Format facts are not copyrightable; translated code is.
- **Permissive licensing helps the community.** Other tools can adopt these crates, including HEMTT, which is GPL-2.0-only.
- **Isolate ported code.** If something must be ported (for example UI layout constants), keep it in a separate GPL-3.0-or-later crate.
- **The `ofp-` crate prefix is still an open question.**

## 16. Proposed workspace layout for format crates

**Rules** (from `IC@7b7fac7fa5:AGENTS.md`):

- no direct indexing (`#L276-L333`);
- no `unwrap`/`expect` (`#L335-L342`);
- pure `&[u8]` parsers, permissive on values and strict on structure (`#L399-L416`);
- synthetic fixtures only (`#L583-L597`);
- files of at most ~600 lines, plus a `CODE-INDEX.md`.

| Crate | Contents | Deps |
| --- | --- | --- |
| `ofp-bytes` | `Cursor<'input>` (checked LE `u8/u16/u24/u32/i32/f32`, `cstr`, `fixed_str<N>`), OFP varint, `lzss::{decode, encode}` + `ChecksumKind`, `Caps` | none |
| `ofp-pbo` | `Pbo<'input>` borrowing entries; `PackingMethod(u32)` (permissive); `Properties`; `PboWriter` (stored / `Cprs`); lazy `Read+Seek` reader | `ofp-bytes` |
| `ofp-vfs` | the only IO crate: mount order game → `Res` → mods; prefix = PBO stem; case-insensitive lookup; `..` collapsing like CE's `CollapseParentDirs` | `ofp-pbo` |
| `ofp-preproc` | §4.2 directives, `IncludeResolver`, `SourceMap`, caps | `ofp-bytes` |
| `ofp-config` | CST + resolved view; value typing; raw `__EVAL`/`__EXEC`; raP read (v2–4) and write (v4, pending OQ1); Arma-raP detection | `ofp-bytes`, `ofp-preproc` |
| `ofp-mission` | typed `mission.sqm` lens and validator (doc 04) | `ofp-config` |
| `ofp-wrp` | `4WVR`/`OPRW` → `Terrain { grid, heights: Vec<f32>, tex_idx, textures, objects: Vec<WrpObject{WrpObjectId, model, transform}>, geography: Option<_>, mountains }` | `ofp-bytes` |
| `ofp-p3d` | ODOL v7 walk + MLOD → `MapInfo` (§7) | `ofp-bytes` |
| `ofp-paa` | PAA/PAC → RGBA8; TAGGs, palette, RLE, signed-checksum LZSS | `ofp-bytes`, `texpresso` |
| `ofp-fxy` | glyph table | `ofp-bytes` |
| `ofp-stringtable` | raw + decoded rows, per-column code page | `encoding_rs` |
| `ofp-script` | SQS/SQF tokenizer, structure lint, per-target command tables | none |
| `ofp-audio` | WSS decode (+ delta), Vorbis/WAV adapters → PCM | `lewton` or `symphonia` |
| `ofp-briefing` | HTML subset (doc 04) | none |

**Newtypes.** Each has `from_raw`, `to_raw` and `Display`:

- `PackingMethod`
- `StringPoolIndex`
- `WrpObjectId`
- `TextureIndex`
- `LodIndex`
- `PaaFormatTag`
- `GlyphCode`

**Example error variants.**

- `UnexpectedEof { offset, needed, available }`
- `BadMagic { found }`
- `CountExceedsCap { what, count, cap }`
- `LzssChecksum { stored, computed }`
- `UnsupportedPacking(PackingMethod)`
- `ArmaRapNotSupported`
- `EncryptedPbo`

**Caps.** We reuse the engine's own hardened limits:

| Limit | Value | Source |
| --- | --- | --- |
| WRP grid side | ≤2048 | `WrpReader.cpp#L81-L87`, `#L239-L246` |
| OPRW texture count | ≤65536 | `#L336-L342` |
| array count | ≤ remaining bytes | `SerializeBin.hpp#L132-L157` |
| binary array | ≤256 MiB | `#L111-L121` |
| raP pool index | must be the next index | `ParamFileParse.cpp#L108-L117` |
| raP varint | ≤5 groups; stop at EOF | `#L136-L145` |
| PAA side | 2..4096 | `Pactext.cpp#L1411` |
| PBO name | ≤511 bytes | — |
| PBO header block | ≤64 MiB (the engine applies this to encrypted headers; we apply it to all) | `QBStream.cpp#L662-L672` |
| LZSS output | ≤9× input | §2 |

**CWR's fuzzing** [V].

- CWR has 16 libFuzzer harnesses in `apps/fuzzers/Fuzzer/`: `pbo`, `paramfile`, `wrp`, `paa`, `p3d`, `shape`, `stringtable`, `sqs`, `sqf`, `sqf_exec`, `wss`, `wav`, `lip`, `rtm`, `savegame` and `decode_msg`.
- They use header forcing: the first bytes are overwritten with a valid magic, so mutations reach the body (`CWR@ffc61838b7:apps/fuzzers/Fuzzer/fuzz_structure.hpp#L1-L32`).

**Our fuzzing.**

- **Targets.** Mirror CWR's harnesses as `cargo-fuzz` targets, each with a header-forcing wrapper:
  - `fuzz_pbo`, `fuzz_lzss_{unsigned,signed}`;
  - `fuzz_rap`, `fuzz_config_text`, `fuzz_preproc`;
  - `fuzz_wrp_{4wvr,oprw}`, `fuzz_p3d`;
  - `fuzz_paa`, `fuzz_pac`, `fuzz_fxy`;
  - `fuzz_stringtable`, `fuzz_wss`, `fuzz_sqs`.
- **Round-trips.** Add `proptest` write→read round-trips for every writer.
- **Known bug classes.** CWR's crash regressions name the classes to pre-empt: `tests/fixtures/paa/fuzz_lzw_overflow.paa`, `fuzz_dxt_oob.paa`, `fuzz_argb8888_oob.paa`, `tests/fixtures/mlod/fuzz_tagg_oob.p3d`, `fuzz_shape_lod_oob.p3d`. Re-create them synthetically; never copy the files.
- **Nightly toolchain.** `cargo-fuzz` needs nightly Rust, so it lives in a separate `fuzz/` workspace. [I]

**Other practices** [I].

- **No `memmap2`.** Mapping requires `unsafe`, so stream big PBOs via `Read+Seek` from a bounded header prefix instead.
- **Synthetic fixtures from test helpers.** Build them with helpers such as `build_pbo(&[...])` and `build_4wvr(grid, objects)`. CWR's generator shows how small a valid WRP is: a 4×4 grid with 3 objects is 16,844 bytes.
- **Real-install corpora.** These are opt-in, local only, and gated by an environment variable.

## 17. Per-format decision

| Format | Decision | Why |
| --- | --- | --- |
| BI LZSS | clean-room in `ofp-bytes` (~200 lines including the encoder) | two checksum flavours; no crate fits |
| PBO | clean-room; oracles: papa-bear-archive and `PoseidonTools pbo` | existing crates are Arma-only or license-incompatible |
| Text config + preprocessor | clean-room | HEMTT is GPL-2.0-only with Arma semantics; we need a lossless CST |
| OFP raP | clean-room from doc 04 §4 and the BI wiki; oracle: `PoseidonTools config bin/debin` | no Rust implementation of the OFP layout exists [V: searches] |
| `mission.sqm` | clean-room on top of `ofp-config` (doc 04) | fidelity, IDs, validation |
| WRP | clean-room; oracle: `PoseidonTools terrain` | no crate exists |
| P3D (subset) | clean-room, map info only | needed for the map; HEMTT is MLOD-only and GPL-2.0 |
| PAA/PAC | clean-room + `texpresso` | HEMTT lacks P8/PAC and panics on DXT2/4 |
| FXY | clean-room (trivial) | — |
| stringtable | clean-room + `encoding_rs` | legacy code pages; raw rows |
| SQS/SQF | clean-room tokenizer + generated per-target command table | HEMTT is Arma 3-only and GPL-2.0 |
| WSS / OGG | clean-room WSS; `lewton` or `symphonia` for OGG | small |
| JPG | reuse `zune-jpeg` | standard format |

## Open questions

1. **raP versions.** Which raP versions do OFP 1.96 and CWA 1.99 accept? If 1.96 rejects v4, the writer must emit v2 or v3. Test on a local install.
2. **ODOL v8.** Does v8 occur in CWA or CWR data, and how does it differ from v7? CWR's detector and reader disagree.
3. **OPRW v3 heights.** Is the height grid terrain-sized when `terrainX != landX`? `WrpReader` and `LandSave` disagree.
4. **Product entry.** Is Resistance's product entry really "three strings"? Is an Elite-style `prefix` property harmless in 1.96?
5. **CWR Cargo licenses.** Is `license = "MIT"` in CWR's Cargo manifests intended? This needs a statement from Bohemia.
6. **Retail harness.** Is `--harness` enabled in retail CWR builds? This decides whether Trident's protocol can serve Preview.
7. **ARGB8888.** Can retail 1.99 read `0x8888` PAAs?
8. **Crate prefix.** Should we keep the `ofp-` crate prefix, given the §7 trademark clause and trademark law generally? CWR's README names "OPERATION FLASHPOINT" as a registered trademark of Electronic Arts Inc. (`CWR@ffc61838b7:README.md#L62`).
9. **BI wiki.** The BI wiki pages for raP-OFP, OPRW2&3, ODOLV7 and PAA returned HTTP 403. A human should cross-check §3–§8 against them.

## Sources

Pinned code, using the aliases defined in §0:

- **CWR I/O and PBO:** `…/IO/Streams/SsCompress.cpp#L7-L327`; `…/IO/Streams/QBStream.cpp#L293-L324,L605-L764,L1051-L1111,L1352-L1363`; `…/IO/Streams/FileInfo.h#L10-L18`; `…/IO/Streams/QBStream.cpp#L621,L1137-L1143`; `…/Foundation/platform.hpp#L121`; `…/IO/PackFiles.cpp#L47-L58,L175-L202,L315-L319,L423-L467,L484-L589`; `…/IO/Streams/SerializeBin.cpp#L49-L81`; `…/IO/Streams/SerializeBin.hpp#L105-L157`; `…/Core/GameState.cpp#L93-L102`.
- **CWR config and preprocessor:** `…/IO/ParamFile/ParamFileParse.cpp#L43-L180,L344-L361,L579-L670,L752-L951,L1037-L1044`; `…/IO/ParamFile/ParamFile.cpp#L185-L191,L630-L648,L679-L789,L1054-L1071,L1571-L1850,L2208-L2220`; `…/IO/ParamFile/ParamFileEval.cpp#L70-L105`; `…/IO/PreprocC/Preproc.cpp#L15-L33`; `…/IO/PreprocC/PreprocC.cpp#L28-L49`.
- **CWR missions:** `…/UI/OptionsUIImpl.cpp#L280-L294`; `…/UI/Map/UIArcadeWaypoint.cpp#L920-L988`; `…/AI/ArcadeTemplate.cpp#L321-L340,L1875-L1900,L1934-L1981`; `…/UI/Map/UIMapExtDisplay.cpp#L106-L121`.
- **CWR terrain and map:** `…/World/Terrain/WrpReader.cpp#L51-L389`; `…/World/Terrain/LandFile.hpp#L13-L53`; `…/World/Terrain/LandSave.cpp#L58-L150,L1278-L1384`; `…/AI/Path/AITypes.hpp#L39-L57`; `…/UI/Map/UIMap.cpp#L258-L267,L339-L356,L1169,L1206,L1248,L1374,L1488-L1874,L1948`.
- **CWR models:** `…/Graphics/Rendering/Shape/ShapeLOD.cpp#L1009-L1118`; `…/Graphics/Rendering/Shape/Shape.cpp#L62-L93`; `…/World/MapTypes.hpp#L7-L21`; `…/Asset/Formats/P3D/P3DStructures.hpp#L27-L49,L463-L524`; `…/Asset/Formats/Common/FormatDetector.cpp#L84-L96`.
- **CWR textures, fonts and text:** `…/Graphics/Rendering/Font/Pactext.cpp#L139-L353,L368-L600,L875-L960,L1102-L1247,L1364-L1433`; `…/Graphics/Textures/PAADecoder.cpp#L80-L132,L403-L546`; `…/Graphics/Rendering/Draw/FontData.cpp#L34-L92`; `…/Graphics/Rendering/Draw/Font.cpp#L47-L59,L296-L347`; `…/UI/Locale/Stringtable/Stringtable.cpp#L281-L339`; `…/UI/Locale/Stringtable/CodepageTranscode.cpp#L74-L110`; `…/Asset/Formats/Common/CsvReader.cpp#L9-L97`.
- **CWR audio, images and platform:** `…/Audio/Streaming/WaveLoaders.cpp#L14-L66`; `…/Audio/Streaming/WaveStream.cpp#L146-L226`; `…/Audio/Core/Format/WaveBuffer.cpp#L46-L77`; `…/Graphics/Textures/JpgImport.cpp#L7`; `…/Foundation/Platform/AppConfig.cpp#L663-L664`.
- **CWR Rust:** `CWR@ffc61838b7:Cargo.toml#L1-L9`; `CWR@ffc61838b7:engine/Trident/{Cargo.toml#L1-L45, src/main.rs#L1-L8, src/client/instance.rs#L1-L70, protocol/harness.schema.json#L1-L141, src/scenarios/multi.rs#L15,L417-L425}`; `CWR@ffc61838b7:mserver/Archive/{Cargo.toml#L1-L7, src/lib.rs#L1-L13, src/pbo.rs#L1-L473, src/lzss.rs#L1-L79}`.
- **CWR tools, fuzzers and license:** `CWR@ffc61838b7:engine/PoseidonFormats/PoseidonFormats.h#L25-L118`; `CWR@ffc61838b7:apps/tools/Tools/CMakeLists.txt#L13`; `CWR@ffc61838b7:apps/tools/Tools/commands/{PboCommand.cpp#L233-L255, ConfigCommand.cpp#L204-L271, TerrainCommand.cpp#L29-L181, LintCommand.cpp#L162-L165}`; `CWR@ffc61838b7:apps/tools/Evaluator/CMakeLists.txt#L9`; `CWR@ffc61838b7:apps/fuzzers/Fuzzer/{fuzz_structure.hpp#L1-L32, fuzz_pbo.cpp#L18-L69}`; `CWR@ffc61838b7:tests/fixtures/wrp/generate_test_world.py#L1-L24`; `CWR@ffc61838b7:LICENSE#L1-L3,L682-L721`; `CWR@ffc61838b7:README.md#L7-L18,L49-L62`.
- **Other repositories:** `CE@b67bf3bd62:engine/Poseidon/Graphics/Rendering/Font/Pactext.cpp#L404-L470`; `IC@7b7fac7fa5:AGENTS.md#L276-L342,L399-L416,L583-L597`.

Web sources, fetched 2026-09-26 unless noted:

- **HEMTT (main branch).** Release v1.22.0 per <https://api.github.com/repos/BrettMayson/HEMTT/releases/latest>. Repository <https://github.com/BrettMayson/HEMTT>. Manifests: <https://raw.githubusercontent.com/BrettMayson/HEMTT/main/Cargo.toml> and `libs/{pbo,paa,config,preprocessor,sqf,wss,p3d,stringtable}/Cargo.toml`. Source files: `libs/pbo/src/{lib.rs,read.rs}`, `libs/pbo/src/model/mime.rs`, `libs/config/src/rapify/config.rs`, `libs/paa/src/{pax.rs,mipmap.rs}`, `libs/lzo/src/lz77.rs`, `libs/p3d/src/lib.rs`.
- **Licensing.** SPDX: <https://raw.githubusercontent.com/spdx/license-list-data/main/json/details/GPL-2.0.json>. Apache: <https://www.apache.org/licenses/GPL-compatibility.html>. FSF: <https://www.gnu.org/licenses/license-list.html> (from search results; the fetch failed).
- **crates.io.** API at <https://crates.io/api/v1/crates>. Searches: `hemtt`, `pbo`, `arma`, `paa`, `rapify`, `wrp`, `sqf`, `p3d`, `bohemia`, `lzss`, `sqm`. Crate pages: `armake2`, `pbo`, `bi_fs_rs`, `sqm_parser`, `lzss`, `texpresso`, `lewton`, `symphonia`, `rodio`, `encoding_rs`, `zune-jpeg`, `p3dtxt`. `lzss` 0.9.1 source: <https://docs.rs/crate/lzss/0.9.1/source/src/dynamic/decompress.rs>.
- **GitHub.** <https://api.github.com/repos/KoffeinFlummi/armake2>, <https://api.github.com/repos/cotillion/ofptools>, <https://api.github.com/orgs/ofpisnotdead-com/repos>, <https://raw.githubusercontent.com/ofpisnotdead-com/rust-pbo-wasm/master/src/lib-original.rs>, <https://github.com/ofpisnotdead-com/rust-pbo-wasm>, <https://github.com/cotillion/ofptools>.
- **PMC Editing Wiki.** <https://pmc.editing.wiki/doku.php?id=ofp:file_formats:pbo>, <https://pmc.editing.wiki/doku.php?id=ofp:file_formats:wrp>.
- **BI Community Wiki.** Found via search; every page fetch returned HTTP 403. <https://community.bistudio.com/wiki/PBO_File_Format>, <https://community.bistudio.com/wiki/Compressed_LZSS_File_Format>, <https://community.bistudio.com/wiki/raP_File_Format_-_OFP>, <https://community.bistudio.com/wiki/raP_File_Format_-_Elite>, <https://community.bistudio.com/wiki/Wrp_File_Format_-_4WVR>, <https://community.bistudio.com/wiki/Wrp_File_Format_-_OPRW2_&_3>, <https://community.bistudio.com/wiki/P3D_File_Format_-_ODOLV7>, <https://community.bistudio.com/wiki/PAA_File_Format>, <https://community.bistudio.com/wiki/Category:BIS_File_Formats>.
- **Mikero's tools.** Closed source; used as a behaviour reference. <https://mikero.bytex.digital/>, <https://wiki.mikero.tools/tools>.

## Verification notes

Adversarial fact-check, 2026-09-26. The checker re-read the pinned CWR/CE/IC clones, hex-dumped CWR's PBO/WRP/WSS fixtures, and re-fetched the HEMTT, crates.io, SPDX, Apache, PMC and GitHub sources.

**Confirmed.**

- PBO: no trailer (`mission_fixture.Intro.pbo` is exactly 123 header bytes plus 278 data bytes = 401), the `Vers` condition, 0/`Cprs`/`Encr` only, prefix = bank name, a `Cprs` terminator, and the no-compress list.
- LZSS: relative offsets, a space-filled window, unsigned vs signed checksums, and the ≥1024-byte rule.
- raP: layout, varints, cstring base names, the `\0raP` magic and the "version ≥ 2" check.
- HEMTT: checksum-required `from()` (it also rejects bytes after the checksum), the Arma rapify header, MLOD-only P3D, no P8 and `unimplemented!()` for DXT2/4, `GPL-2.0` on all checked crates, v1.22.0 on 2026-09-18 and crates.io 1.0.0 on 2023-03-16.
- CWR Rust: MIT Cargo licenses vs GPL-3.0+§7 in LICENSE/README (the same in CE), binary-only `tri`, `--harness`, and NDJSON protocol v1.
- Map: `map` property, bounding box, colour, `LB/PB/LE/PE`, ODOL trailer.
- WRP: 4WVR/OPRW layouts; the synthetic `test_world.wrp` generator gives 16,844 bytes.
- Missions: `LSNoAddOn`; 16 fuzzers; the FXY, WSS and code-page tables.
- Crate versions and licenses (texpresso, lewton, symphonia, rodio, encoding_rs, pbo, bi_fs_rs, armake2, sqm_parser, lzss) and the Apache GPLv3/GPLv2 statement.

**Changed.**

- The PBO length check does not enforce a minimum length, because seeking past EOF succeeds.
- Added that `ReadOverlapped` is lenient about packing values.
- Scoped "prefix = file name" to `dta\` and `Addons\`; `Campaigns\` banks get a directory prefix.
- Fixed citations:
  - slash conversion (`#L621`) and the packer's backslash code (`PackFiles.cpp#L47-L58`);
  - the `MapType` table (`ShapeLOD.cpp#L1009-L1118`);
  - the mission loader (`UIArcadeWaypoint.cpp#L920-L988`); `OptionsUIImpl.cpp` is only the mission-list title lookup;
  - `fuzz_structure.hpp` is 32 lines.
- The 2048 grid cap belongs to `WrpReader`, not the runtime 4WVR loader.
- Trident: `types.rs` is 372 lines, not 325; the scenario code is ~7,500 lines, not ~6,900; added `key_up`; `multi.rs` packs seed mods, not missions.
- Quotes: HEMTT's lz77 comment and the `bi_fs_rs` description now match the source verbatim.
- `p3dtxt` is GPL-2.0-or-later, not unknown.
- `zune-jpeg` 0.5.16-rc2 is a pre-release; the latest stable is 0.5.15.
- The `lzss` crate is now verified to use absolute indices and a bit-packed stream.
- Added CE diff details, the EA trademark note (OQ8) and the colour weighting.

**Unverified.** HEMTT's last-push date, the `rust-pbo-wasm` push date and the `ofptools` date (the GitHub API returned 403). The retail (1.96/1.99) runtime behaviour remains inferred from CWR code.
