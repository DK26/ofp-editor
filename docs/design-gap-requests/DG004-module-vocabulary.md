# DG004: What "module" means: mission, persistence and strategic modules

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
> **Decision by: technical** (design round). Blocks: the type names in doc 31 §4.2 (`ofp-modules`), doc 26's `PersistenceModule`
> and doc 29 §3; UI labels and Standing Orders entries that say "module".

## Context

- **Doc 31 §4.1**: a module is "a typed, versioned definition (parameter schema, map footprint, singleton needs, profile
  requirements, lowering templates) plus placed instances" on the map; "'Module' here means a **mission** module. Doc 26 §5.2 uses
  'persistence module' for campaign-level bundles; the two share the parameter vocabulary but live in different editors (open
  question 9)." Doc 31 OQ9: "one concept with two scopes, or two names?"
- **Doc 26 §5.2** and the §9.1 type sketch: `enum PersistenceModule { Roster, Reputation, WeaponPool, VehiclePool, Intel, Supplies,
  DoomClock, Echoes }`, delivered as campaign consequences.
- **Doc 29 §3.1**: Strategic Layer modules are "data plus a deterministic lowering", live in the Strategic tier and "extend doc 26's
  `PersistenceModule`"; doc 26's Roster, Weapon pool, Vehicle pool, Supplies and Doom clock rows become Roster, Loadout, Hangar,
  Resources and DoomClock modules.
- **Doc 33 §1.4 and lesson C6**: "modules" is a later-game (Eden) term; "the engine has no modules; open one of the editor's modules
  and see the plain triggers, logics and script it compiles to".
- Doc 34 §5.2 (row for doc 26) lists more persistence modules (Fragments, alignment ladder, perk choice, commendations).

## The gap

"Module" names three things: a placed mission object (doc 31), a campaign-state bundle (doc 26) and a strategic-layer system that
extends the campaign bundle (doc 29). A fourth meaning, Eden modules, arrives with users from later games. Nothing says whether they
are one concept with scopes or different concepts, which decides the type hierarchy, the palette, the "Found by intent" search
(doc 31 §4.1) and how Wilco explains them.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | One concept with a scope: `Module { scope: Mission \| Campaign \| Strategic }`, one definition format and parameter vocabulary | One palette, one form engine, one "one-sentence summary" rule; matches doc 31's "share the parameter vocabulary" | Mission modules have map footprints and placed instances; campaign modules have state and commit steps; one type may hide real differences |
| B | Distinct names: "module" only for mission modules; campaign and strategic ones become another noun (for example "campaign system" or "persistence kit") | No ambiguity in UI and docs | Loses the shared vocabulary; users must learn two words |
| C | One family name, two kinds, shared definition machinery: **mission modules** and **campaign modules** (strategic modules are campaign modules in the Strategic tier) | Keeps shared forms, presets, versioning and the format (DG007) while typing the differences | Requires the qualifier in every UI label and doc |

## Recommended resolution (proposal)

Option C. "Module" is the family: a typed, versioned definition with presets, a one-sentence summary and a lowering. Two kinds:

- **Mission module** (doc 31): placed on the map in one mission, with footprint, events and verbs.
- **Campaign module** (doc 26's persistence modules and doc 29's strategic modules): declares campaign state (doc 19 `VarDecl`s),
  effects and commit steps; doc 29's Strategic tier is a set of campaign modules, not a third kind.

They share the definition format (DG007), preset and Shuffle machinery, versioning and profile badges (doc 31 §4.7). The Rust sketch
names `MissionModule` and `CampaignModule`; doc 26's enum becomes `CampaignModule`. UI labels always carry the qualifier. Standing
Orders keeps the "Coming from later editors?" answer: the engine has no modules, and Plotroom's modules compile to plain triggers,
logics and scripts.

## What it would change

- Doc 31 §4.1 note and OQ9: point to the decision; §4.2 sketch names `MissionModule`.
- Doc 26 §5.2 and §9.1: `PersistenceModule` → `CampaignModule` (text may keep "persistence" as the description).
- Doc 29 §3.1: "extend doc 26's campaign modules"; the kit is "Strategic Layer campaign modules".
- Doc 33 §1.4 and C6: wording aligned with the two kinds.
- Doc 34 §5.2 row for doc 26: "campaign modules".

## Affected docs

Docs 26, 29, 31, 33, 34; `ofp-modules` crate naming in CODE-INDEX.md when code lands.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 31 §4.1 and OQ9, doc 26 §5.2 and §9.1, doc 29 §3.1, doc 33 §1.4 and lesson C6, and doc 34 §5.2's row
  for doc 26, re-read on 2026-09-27.
