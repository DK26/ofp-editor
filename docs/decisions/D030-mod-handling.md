# D030: Mods: first-class mod sets; integrate, never host

> **Status:** baseline (docs 27 and 42), with the owner's network rule (D008) · **Decided by:** research and owner (DG028)
> **Decided:** 2026-09-27 · **Recorded:** 2026-09-27 · **Scope:** game addons and mods in catalogs, generation, Preview and discovery;
> Plotroom's own pack registry. **Related:** D003, D007, D008, D017, D018, D027.
> **Open parts:** DG029 = OWQ-12 (channel maintainers; answered 2026-09-27 → D035); DG030 = OWQ-17 (install hand-off, directory
> freshness, CC-BY-SA, registry operator; answered 2026-09-27 → D038); OWQ-18 (extended addon set default; answered 2026-09-27 → D038);
> OWQ-06 (sharing extension overlays; answered 2026-09-27 → D033).

## Context

- Big mods are still installed and updated through four channels (the game's MODS manager, the legacy Game Schedule, hand-made `-mod=`
  lines, mission packs inside mod folders); some are launcher platforms (doc 27 TL;DR).
- The engine's own dependency scan counts only unit and empty-vehicle classes, yet a missing addon fails the whole mission load (doc 27).
- Users will ask Wilco to "use mod X", installed or not (doc 42 question).

## Decision

1. **A mod set is a first-class, fingerprinted object**: ordered, named and tied to a target profile. Plotroom mirrors the engine's mount
   and merge rules exactly in pure crates (D017), with owner and access tracking, and records provenance for every class.
2. **Dependencies are derived, never hand-edited**: `addOnsAuto[]` with exact engine parity; `addOns[]` as the engine set plus
   pinned entries (whether the extended set is written by default is OWQ-18); an exported requirement manifest; mod needs fold into the
   "Requires" badge (D003).
3. **Preview uses the mission's resolved mod set**, and also offers clean-room and vanilla previews (D018).
4. **The AI generates only from the active mod set's catalog.** Menus are computed from it, so the model can never name an unloaded
   class. "Use mod X" when X is absent produces a code-computed card with three routes: get it (link and instructions), build now with
   vanilla stand-ins marked for remap, or record X as a declared requirement (doc 42 §2.7).
5. **Integrate, never host**: Plotroom never downloads, installs, unpacks, mirrors or re-uploads mod files, and never runs mod
   executables, launchers or install scripts. Installs stay with the game's own tools.
6. **Offline default**: vanilla, auto-detected installed mods, a built-in vanilla overlay pack and a built-in community mod directory
   pack (ids, names, sizes, revisions and links only; it ships after the channel maintainers are asked, DG029).
7. **Live lookup is opt-in**: one first-party, read-only Community catalog `feed` connector, off by default (D008).
8. **Plotroom's own pack registry** holds only Plotroom packs and is phased: built-ins and sideloads, then a Git-hosted signed index,
   then throttled community submissions, then stronger update security (doc 42 §5, RG0–RG3).

## Alternatives considered

- A Plotroom game-mod market or mirror: the channels already serve mods, and a "custom market" is just another origin the user can
  type into the connector (doc 42 §1.1 Q3, §3.5); hosting would add licence and operating burdens.
- Hand-edited `addOns[]` lists: error-prone, because the engine's own scan misses weapons, magazines, markers, effects and
  script-created objects while a listed but missing addon fails the whole load (doc 27 TL;DR).
- Letting the model name classes from memory: it would name classes of mods that are not loaded.

## Consequences

- Every PBO is hostile input: parse caps, `#include` confined to banks of the same set, no execution of config expressions, failures
  isolated per addon, derived caches local only (doc 27 TL;DR).
- Unit cards derive roles deterministically with a recorded basis; vehicle roles stay "derived, unvalidated" until graded (doc 42 §2.2).
- A campaign has exactly one mod set (doc 27 TL;DR).
- Content that can reach a user's mission from a pack is under an allowlisted licence (doc 42 §5.2; CC-BY-SA is OWQ-17).

## Sources

Doc 27 (TL;DR, §2, §4, open questions); doc 42 (TL;DR, §1–§8, open questions); doc 34 (mo01–mo16 rows); DG028; DG029; DG030.

## Amendment notes

### 2026-09-27: the owner's answers to this record's open parts

All four open parts are answered in `OWNER-QUESTIONS.md`; the decisions above are unchanged and the answers fill them in. The DG
decision records (DG029, DG030) hold the detail.

- **Channel maintainers (OWQ-12 = DG029 option A).** One message per channel from the owner or a maintainer the owner names.
  Non-objection means a written reply that does not object, or no objection 30 days after an acknowledging reply. The built-in
  community mod directory pack (decision 6) and the Community catalog feed (decision 7) wait for it.
- **DG030 (OWQ-17, all four proposals).** (1) A user-clicked "Launch the game to install mods" starts the game vanilla, without
  `--private` and without a mission, for `Cwr` and `Ce` targets; installing stays in the game's own tools (decision 5). (2) The
  directory is refreshed at each release, plus the opt-in connector's live refresh; no third-party metadata in Plotroom's registry.
  (3) CC-BY-SA-4.0 is allowed only for editor-only content, never for content that reaches missions. (4) No registry operator until
  the registry is scheduled; then the project's own organisation with doc 42 §5.3's governance.
- **Extended addon set (OWQ-18 (a)).** `addOns[]` is written from the engine set plus the extended set plus user pins by default, with
  an engine-parity-only mode (decision 2).
- **Extension overlays (OWQ-06).** For Bohemia's campaigns, only the extension sidecar and the user's own new missions ship, merged
  locally from the user's installed parent by id and hash, with the export guard blocking parent content (the question also goes into
  the OWQ-10 letter); for third-party campaigns, only when the parent's licence allows derivatives or the author's permission is
  recorded.

### 2026-09-27: pointers to D033, D035 and D038

The answers in the note above are also stated as records, which govern: D033 (OWQ-06), D035 item 4 (DG029 = OWQ-12) and D038
(DG030 = OWQ-17, and OWQ-18). The header gained pointers; nothing else above changed.
