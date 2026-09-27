# D017: Format crates, a lossless CST and raw-byte strings

> **Status:** baseline · **Decided by:** research (docs 04, 07), with the owner's licence (D001) and naming (D002) rules
> **Decided:** 2026-09-26 · **Recorded:** 2026-09-27 · **Related:** D001, D002, D003, D013, D030.
> **Open parts:** doc 07 OQ1–OQ7 and doc 04's open questions (format facts to probe); doc 45 OQ4 (id minting).

## Context

- No Rust crate handles the game's era formats correctly: HEMTT targets Arma 3 (PBO checksum trailer, Arma raP layout, no P8/PAC) and is
  GPL-2.0-only, so it cannot be linked (doc 07 TL;DR). CWR's own Rust code is a small PBO reader and a test orchestrator, not a library.
- Existing missions must round-trip byte-exactly: the engine omits default-valued keys, renumbers ids on every save and drops dangling
  synchronisations; the Remastered editor decodes legacy code pages on load, so a naive re-save silently changes bytes (doc 04 TL;DR).

## Decision

1. **Our own crates** for every format Plotroom reads or writes: PBO, BI LZSS, config text and preprocessor, raP, `mission.sqm`, WRP, a
   P3D map-info subset, PAA/PAC, FXY, stringtable, SQS/SQF tokenizer, WSS, briefing HTML. Only generic crates are reused (`texpresso`,
   `zune-jpeg`, `lewton` or `symphonia`, `encoding_rs`).
2. **Spec-first**: written from our own format specs (docs 04, 07), black-box checks against CWR's tools and ported upstream tests (D013).
   Under D001 translating engine parser code is allowed when it is the faster faithful route; such files carry `Derived-From:` headers.
3. **Pure `&[u8]` parsers**: safe-read cursors, one `Error` enum per crate, caps on every count and size taken from the engine's own
   hardened limits, permissive on unknown values and strict on structure (`AGENTS.md`; doc 07 §16).
4. **Three layers for configs and missions** (doc 04 TL;DR): a lossless CST where `render(parse(bytes)) == bytes`; a typed lens with
   newtype ids and `Other(RawToken)` arms that keep the original spelling; an engine-strict validator plus an optional "normalise like
   the engine" writer profile.
5. **Strings are raw bytes**; code-page decoding happens at the edges, and `$STR_` references are never expanded on read.
6. **File ids are not identity**: Plotroom keeps its own stable ids in the sidecar and re-associates objects after an external save.
7. Crates are `GPL-3.0-or-later` (D001, overriding doc 07 §15's permissive proposal) and use the `plotroom-` prefix (D002, replacing
   doc 07's `ofp-*` working names and answering doc 07 OQ8). Writers default to output every profile accepts (D003).

## Alternatives considered

- Depend on HEMTT or armake2: wrong semantics for this engine, and HEMTT's licence is incompatible.
- A lossy parse-and-reprint model: breaks byte-identical round trips and silently rewrites users' files.
- Memory-mapped archives (`memmap2`): needs `unsafe`; large PBOs are streamed through `Read + Seek` instead.

## Consequences

- `cargo-fuzz` targets mirror CWR's 16 fuzz harnesses (with header forcing) in a separate nightly `fuzz/` workspace; every writer gets
  `proptest` write → read round trips; fixtures are synthetic builders (doc 07 §16).
- One IO crate owns the mount order (game → `res` → mods) and case-insensitive lookup; the mod-set pipeline builds on it (D030).
- A format feature counts as done only with round-trip evidence (load → save → byte-compare), per `AGENTS.md`'s evidence rule.
- Newtypes (`PackingMethod`, `StringPoolIndex`, `WrpObjectId`, …) are listed in `CODE-INDEX.md` when they land.

## Sources

Doc 04 (TL;DR, §3, §12); doc 07 (TL;DR, §0, §15–§17, open questions); doc 20 TL;DR; doc 45 OQ4; `AGENTS.md` (parser, indexing,
allocation and evidence rules).
