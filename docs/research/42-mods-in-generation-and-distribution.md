# Mods in AI generation, and how mods and content packs are found

Research doc 42 for Plotroom (`ofp-editor`). Research date: 2026-09-27. Audience: contributors and LLM coding agents. This file is meant to be read on its own.
Question answered (owner): "What do we do if the user wants to involve a mod or addons when asking the LLM to generate content? Should we offer out-of-the-box access to some well-known community servers? Should we allow a custom market? Maybe include a good default? How should we handle this?"

**Status.** Proposal-only. Every type, name, code, threshold and UX in §2–§8 is **[I]** unless a line says otherwise.
**Epistemic legend.** **[V]** verified by static reading of the pinned engine source, a fetched page, a live API response or a count over the local corpus. Nothing was run against a game. Live counts were fetched on 2026-09-27 and will drift. **[V-search]** seen only in a search-result snippet, because the page refused the fetch. **[I]** our inference or proposal. **[U]** unknown; needs a probe or an answer from a maintainer.
**Citation aliases.** `BI:` = `BohemiaInteractive/CWR@ffc61838b7:` (Remastered 3.05 source). `CE:` = `ofpisnotdead-com/CWR-CE@b67bf3bd62:` (community continuation). Both are repo roots, as in doc 37; doc 27's `CE:` points one level deeper, at `engine/Poseidon/`. **PB** = PAPA BEAR, the master service at `https://papa-bear.cz`. **GS** = OFP Game Schedule (`https://ofp-faguss.com/schedule/`).
**Evidence bases.**

- **Source**: both pinned clones, including the `mserver/` Rust crates (the PB service and the `papa` CLI).
- **Live**: PB's JSON API and OpenAPI file, the GS API, feeds and docs, Nexus Mods' public GraphQL, Steam's public APIs, robots.txt files and host probes.
- **Case study**: an engine-style config loader run read-only over the owner's install on three catalogs (vanilla CWR 3.05, vanilla CWA 1.99, and Cold War Enhanced (CWE), a community "platform" mod with its own launcher for 1.96/1.99), plus the official and CWE missions. Only counts and class, addon and mod names appear here.
- **Prior art**: public documentation of other registries and marketplaces.

**Codes (provisional; the design round assigns final numbers).** Principles `MG1`–`MG8`, channels `CH1`–`CH8`, lints `D10`–`D12`, registry phases `RG0`–`RG3`, delivery phases `MS0`–`MS4`, acceptance tests `MAT1`–`MAT16`. The bare labels `D10`–`D12` also name doc 21 sections, the same clash doc 34 notes for `D9`. None collides with the codes listed in the headers of docs 36 and 37, and a grep of `docs/research/` finds none of these families elsewhere except doc 21's section labels.
**Relation to sibling docs.** Doc 27 owns mod sets, mount and merge rules, class provenance, dependency derivation and Preview mod lines. Doc 34 owns the lock family (`*.modset.toml`, drift report, `plotroom.lock`: mo01, mo03, mo16), the D9 redistribution guard (mo10) and the phase-0 registry idea (mo14). Doc 37 §5 owns the class-remap tool, doc 22 plugin tiers, trust and signing, doc 25 the S0 intake and Pick menus, doc 30 knowledge activation, and doc 24 the risky-command lints. This doc adds unit cards and the rules for mod-aware generation, the channel survey and its integration design, defaults, and registry governance. §8.3 lists what sibling docs should absorb.
**Hygiene.** All text is our own. No game or mod file content is quoted. Scratch scripts and their outputs stay outside the repo.

## TL;DR

- **Integrate; never host.** Plotroom builds no game-mod market and never downloads, installs, unpacks, mirrors or re-uploads mod files. It reads mods installed on disk, links to the channels that already serve them, and leaves installs to the game's own tools. The only curated, signed registry is for Plotroom's own content packs (§5).
- **The AI generates only from the active mod set's catalog** (doc 27 §4.8). An engine-parity loader reproduced the `addOnsAuto[]` lists the real editor wrote in 10/10 CWE mission sections and 170/178 official ones [V], so the catalog's provenance is good enough to drive menus and dependencies (§2.1).
- **Deterministic unit cards** turn config fields into typed facts and record a `basis` for every derived field. Infantry roles match an independent label on 96% of vanilla and 88% of CWE soldiers (92% with a convention rule) [V]. On a rebalanced mod, vehicle roles are measurably wrong, so they stay "derived, unvalidated" until graded against the set's own ammo (§2.2–§2.3).
- **Weak-model menus stay at ≤ 7 options** through side → kind → role group → role on both catalogs [V]. Variant collapse must get stricter (an M60 is not an M1A1), and `CfgGroups` presets become one-pick squads (§2.4).
- **"Use mod X" when X is not installed** produces a card that code computes, with three routes: get it (link and instructions), build now with vanilla stand-ins marked for remap, or record X as a declared requirement. The model never names a class of an absent mod. In CWE's own missions, 21% of entities are mod-only. Every mod-only *unit* has a same-role vanilla candidate; the 68 mines and logic modules have none [V] (§2.7).
- **Requirements travel as data**: a manifest keyed by engine ModId, carrying `(modId, packageRevision, sha256)` from the game's MODS storage, per-channel ids, and a platform mod's launcher state (§2.8).
- **Channels today [V].** PB is the game's built-in MODS storage: 13 admin-curated mods, an open read API, no published terms. GS with Fwatch covers only the legacy game: 123 records and installer scripts with no integrity checks. Nexus has 4 CWA mods and its API forbids rehosting. ModDB blocks automated access. CWA has **no Steam Workshop**. No channel exposes class data (§3.1).
- **A good default that works fully offline:** Vanilla plus auto-detected installed mods (from `mod.json` and `__gs_id`), the built-in vanilla overlay pack, and a built-in **Community mod directory** pack. The directory holds only ids, names, sizes, revisions and links (§4).
- **Live lookup is opt-in.** One first-party "Community catalog" connector, off by default, does GET-only metadata reads: PB for CWR/CE targets and GS for 1.96/1.99 targets. It sends the target game version (plus a channel mod id on detail routes), never brief text, and never calls a download or write route. It waits on a design gap (doc 22 makes MCP the only T2 transport) and on the channel maintainers' answer (§3.3–§3.4; the gap decided 2026-09-27 → [D008](../decisions/D008-outbound-network-sources.md); the outreach and non-objection rule answered 2026-09-27 → [D035](../decisions/D035-outreach-and-security-disclosure.md) item 4, the answers not yet in).
- **A "custom market" means another origin, not a Plotroom service.** The game already accepts any master service (`--master-server`), and PB is open source. The connector accepts any PB-v1-compatible origin the user types in (§3.5).
- **Security [V/I].** Mod content is hostile input, and Plotroom never runs mod executables, launchers or install scripts. A mod can silently redirect the game's master server from its `bin\remaster.cpp`. Preview should pass `--private`, and the scanner flags such mods (§6).
- **The pack registry is phased:** built-ins and sideloads (RG0); a Git-hosted curated index of per-version manifests with minisign signatures, immutable versions, yank lists and CI lints (RG1); throttled community submissions (RG2); TUF later (RG3). It costs reviewer hours, not servers (§5).

## 1. The question and the constraints

### 1.1 Four questions in one

| # | Sub-question | Short answer | Where |
| --- | --- | --- | --- |
| Q1 | How does the AI use a mod the user names? | Only through the installed, scanned, fingerprinted catalog. Anything else becomes a card with routes | §2 |
| Q2 | Out-of-the-box access to community servers? | An offline directory is built in. Live lookup is opt-in and metadata-only, and installs go to the channels' own installers | §3, §4 |
| Q3 | A custom market? | No Plotroom game-mod market. Users may type in any PB-compatible origin. Our registry holds only Plotroom packs | §3.5, §5 |
| Q4 | A good default? | Vanilla, detected mods, and the built-in overlay and directory packs; nothing online by default | §4 |

### 1.2 Constraints

| Kind | Constraint | Source | Consequence here |
| --- | --- | --- | --- |
| Product | Outbound network goes only to the user's model provider and to the declared endpoints of enabled plugins (widened 2026-09-27 → [D008](../decisions/D008-outbound-network-sources.md) item 1: `AGENTS.md` now also names download and feed sources the user explicitly enabled) | AGENTS.md | Channel access is a plugin the user enables. It is off by default |
| Product | Agent tools are product capabilities only: no shell, processes or arbitrary files | AGENTS.md; doc 22 §1.2 "Never allowed" | No installer, launcher or script runner. A URL opens only after a user click, through a non-shell OS API (doc 22 §2.3) |
| Product | Extensions only as T0/T1/T2 plugins | doc 22 §7.1 | The directory and overlays are T0. Live lookup is T2, with a gap (§3.4; decided 2026-09-27 → [D008](../decisions/D008-outbound-network-sources.md): a T2 `feed` connector) |
| Product | Content from missions and addons is untrusted | AGENTS.md | Catalog text, `mod.json` fields and display names reach the model fenced as quoted data |
| Product | Glass box | AGENTS.md | Every card, role, stand-in and requirement shows its basis and source |
| Weak models | Code owns facts; ≤ 7 options plus escapes; Pick and Fill steps | doc 25 §3, §6.2, §7 | Code computes cards, candidates and routes, and the model picks a letter |
| Engine | One mod set per launch; remount only from the main menu | doc 27 §2.6, §4.9 | One mod set per campaign; a mod cannot join mid-session |
| Engine | No URL scheme, protocol handler or CLI flag installs a mod | grep of `CE:` for `URL Protocol`, `x-scheme-handler`, `cwr://`, `papa://` finds nothing; mod options are only `--mod`, `--mods-dir`, `--workshop-dir` (`CE:engine/Poseidon/Foundation/Platform/AppConfig.cpp#L481-L496`) [V] | Hand-off means a web link plus instructions |
| Legal | Plotroom is GPL-3.0-or-later; BI game data is APL-SA (NonCommercial) | doc 02 | No paid tier; never redistribute BI data |
| Legal | Mod licences vary, are often absent, or say "ask first" | doc 27 §3 [U] | Mod content defaults to "licence unknown", so no mirroring |
| Legal | Channel terms: PB and GS publish none; the Nexus API policy forbids bulk rehosting; ModDB's robots.txt blocks automated access | §3.1 [V] | Metadata and links only; ask the maintainers before shipping a connector or the directory pack (§4.2) |

### 1.3 Principles

| # | Principle | Consequence |
| --- | --- | --- |
| MG1 | **Installed is the only truth for generation** | Class menus come from the fingerprinted catalog of the active mod set. Channel metadata never feeds a class menu |
| MG2 | **Link, never host** | No download, mirror, cache, proxy or re-upload of mod files or channel pages |
| MG3 | **Hand the job to its owner** | Installs happen in the game's MODS screen, `papa install`, Fwatch/GS or a platform's launcher; Plotroom rescans afterwards |
| MG4 | **Offline first** | Everything works with the network off. Live lookup only makes the directory fresher |
| MG5 | **Code computes, the model picks** | Code computes routes, candidates and matches; the model chooses among ≤ 7 |
| MG6 | **Provenance on every fact** | Channel data shows its source and fetch time, derived card fields their basis, and overlay hints their pack id |
| MG7 | **No silent substitution** | Stand-ins and remaps are visible, reversible proposals; human-edited entities are never swapped |
| MG8 | **Our registry is for our packs** | Game mods stay with the community's channels |

## 2. Mod-aware generation

### 2.1 Catalog-only menus, and why the catalog can be trusted

Doc 27 §4.8 already decides that every class menu comes from the active mod set's catalog, and that V-catalog (doc 25 §7) rejects anything else. The case study checks that an engine-parity loader gets that catalog right. The loader mounts roots in search order (first-mounted stem wins), lets the highest-priority `bin\config` replace the base, prefers `config.cpp` over `config.bin`, drops configs without `CfgPatches`, filters by `requiredVersion`, orders preloaded addons first and then applies `requiredAddons` edges, merges field by field, and stamps the owner from the first `CfgPatches` entry, lower-cased and recursive (`BI:engine/Poseidon/Asset/Addon/AddonSystem.cpp#L131-L228`, `#L304-L379`; `BI:engine/Poseidon/IO/ParamFile/ParamFile.cpp#L1279-L1291`). It predicts `addOnsAuto[]` as the first `units[]` claimant plus the class owner (`BI:engine/Poseidon/AI/ArcadeTemplate.cpp#L321-L352`).

- **Parity [V].** CWE's own missions: 10/10 sections exact. Official missions against the 1.99 catalog: 170/178 exact. The 8 mismatching sections hold 9 name differences (7 extra `bis_resistance`, 1 extra `6g30`, 1 missing `bmp2`). The likeliest cause is saves made against an earlier catalog [I].
- **Where the Rust port must not copy the scratch loader.** None of these changed parity, but `ofp-config` must port the engine: access modes; clearing a class's base when the source class has none (`BI:engine/Poseidon/IO/ParamFile/ParamFile.cpp#L1934-L1950`); `enum` constants (`#L1682`); mod stringtables overlaying the base table (doc 27 §2.3 step 1).
- **Use.** "Predicted `addOnsAuto[]` equals the saved one" becomes the parity oracle for doc 27 M1/M2 (MAT2). It ships as synthetic fixtures plus an opt-in corpus test gated by an environment variable. On open, a mismatch is a drift signal (doc 34 mo03), not an error.
- **Stub owners [V]; resolves doc 35 open item 12.** A helper addon that declares an empty stub of a vanilla class becomes that class's owner. CWE's grenade pack declares an empty `Jeep` derived from `Car`, and CWE's version addon later fills it in. Both addons are preloaded, with no edge between them. The pack merges first (order 2 vs 4; same folder, and `b` sorts before `c`), so the engine stamps owner `bd_flashbang` on `Jeep`. The corpus confirms it: exactly the CWE mission sections that contain Jeeps carry `bd_flashbang` in `addOnsAuto[]`. The Bizon addon captures `SoldierESaboteurPipe` in the same way. Proposal: `ClassProvenance.owner_from_stub` and lint **D10** (§6.4). The dependency panel shows the chain, and "vanilla-portable save" and remap re-derive `addOns[]` from reasons, never from the saved list.

### 2.2 Deterministic unit cards

A **unit card** is the code-computed fact sheet for one public unit class of one fingerprinted catalog. The model sees cards only inside menus that code selects (doc 30 §4.6).

| Config field | Card field | Case-study reliability [V] | Rule |
| --- | --- | --- | --- |
| `side` | side | present on all 149 vanilla and 165 CWE cards | fact |
| `scope` | public (= 2) | CWE sets it through local macros, resolved to 2 (public) and 1 (hidden) | fact once macros resolve |
| `simulation`, `vehicleClass` | kind | 100%. `vehicleClass` is a category (Men, Armored, Car, Air, Support, Ships), never a faction | fact. No config field gives era or faction |
| `displayName` | label | a stringtable key on 100% of vanilla cards and 40.6% of CWE cards (the rest are literal). CWE's own main stringtable changes 18 of 165 names | resolve through the set's own main stringtable, including one a platform declares; keep the raw bytes |
| `armor`, `maxSpeed`, `transportSoldier`, `camouflage`, `accuracy` | stats | on every card | number evaluator (below) |
| `cost` | cost | > 0 on 96.4% of CWE cards; 6 unarmed medics and ambulance drivers cost 0 | `Option`; 0 is not "free" |
| `crew` | crew link | resolves to a public soldier for 100% of vanilla and 98.6% of CWE vehicles (JeepPolice names a hidden civilian) | an unresolved link is a diagnostic |
| `weapons[]`, `magazines[]` | loadout, weapon kinds | `magazines[]` is empty for unarmed and civilian men | weapon kind is graded per set (§2.3) |
| `picture` | role signal | the unit-bar picture (`BI:engine/Poseidon/AI/VehicleAI.cpp#L380-L385`), not the map `icon` (`BI:engine/Poseidon/AI/ArcadeTemplate.cpp#L394`) | fallback only |
| `type`, `weaponType` | kind, slot | bare constants (`type=VAir` in text configs), strings in binarized ones, and expression strings such as `"1 + 16"` | evaluator |

**Number evaluator.** The engine evaluates a string as an expression when it is read as a number (`BI:engine/Poseidon/IO/ParamFile/ParamFile.cpp#L815-L860`). Ours accepts digits, `+ - * /`, constants the loaded config defines (`enum` blocks, `#define`s), the engine's `VSoft`/`VArmor`/`VAir` and side names, and nothing else. An unresolved token becomes a per-field "unresolved" diagnostic, never a silent 0. CWE shows why: 61 of its weapon classes inherit `weaponType` from a macro defined in a launcher-generated header that is missing on disk [V].
**Labels.** Inside a side and kind, one display-name pair repeats per set (vanilla and CWE: `Rapid`/`RapidY`); CWE has a second pair with its own stringtable [V]. Whenever a label repeats inside one menu, the menu adds a disambiguator: weapon kind, variant, or class id.

| Catalog [V] | CfgVehicles | Public | Unit cards | CfgWeapons | PBOs, size |
| --- | --- | --- | --- | --- | --- |
| Vanilla CWR 3.05 | 502 | 263 | 149 (97 from the base config, 52 from 21 addons) | 155 | 28, 223.5 MiB |
| CWE | 1,270 | 788 (623 are not units) | 165 (10 from its replacement main config, 155 from 9 addons; 147 owned by `cwe_standard`) | 835 | 45, 899 MiB |

```rust
/// Code-computed facts for one public unit class of one fingerprinted catalog (proposal-only; fields private).
pub struct UnitCard {
    class: ClassName, side: Side, kind: UnitKind, role: Derived<Role>,
    label: DisplayLabel,                    // resolved via the set's own stringtable; raw bytes kept
    armor: Num, max_speed: Num, cargo_seats: Num, camouflage: Num, cost: Option<Num>,
    crew: Option<ClassName>, weapons: Vec<Derived<WeaponKind>>, provenance: ClassProvenance, // doc 27 §4.4
    hints: Vec<OverlayHint>,                // from T0 packs; never overwrite a fact (§2.5)
}
pub struct Derived<T> { value: T, basis: Basis }
pub enum Basis { Mechanics(Signal), CrewLink, InheritedCrewLink { ancestor: ClassName }, Picture, Side, Fallback,
                 Overlay { pack: PackId, rule: RuleId } }
pub enum UnitKind { Infantry, Car, Armor, Static, Air, Naval, Support }
pub enum Num { Value(f32), Unresolved { token: Box<str> } }
```

### 2.3 Role inference and its limits

**Soldier precedence, as implemented and to be test-pinned** [V: case-study script]:

1. medic from `attendant`;
2. pilot or crew from reverse `crew=` links of military air or tank vehicles, excluding static weapons and civilian vehicles;
3. AA from a secondary-slot launcher whose missile has `airLock`, AT from any other secondary-slot launcher;
4. spec-ops from `canDeactivateMines` with camouflage ≤ 0.7, otherwise engineer;
5. officer from the officer `picture`;
6. MG from ≥ 100 rounds per magazine or a primary with the secondary-slot bit;
7. sniper from `opticsZoomMin` ≤ 0.06;
8. grenadier from a later muzzle that fires `shotShell`;
9. an inherited crew link from a public ancestor;
10. a `picture` fallback for medic, sniper, spec-ops or sapper;
11. civilian from side;
12. otherwise unarmed, sidearm or rifleman.

Slot masks come from `BI:engine/Poseidon/World/Entities/Weapons/Weapons.hpp#L248-L254`.

- **Agreement with an independent display-name label [V]:** vanilla 52/54 infantry (96%). The misses: `OfficerENight` → grenadier, `SoldierGPilot` → rifleman. CWE: 44/50 (88%). CWE's basis histogram: mechanics 71, fallback 28, mechanics:weapon 20, side 17, picture 15, mechanics:mines 7, crew link 7.
- **Mods break vanilla signals, and a convention adapter can fix some of it [V].** CWE never sets `attendant` on a public soldier. Instead it marks roles with non-firing pseudo-weapons: 62 of its 94 soldiers carry them, under 11 names (`RoleMedic`, `RoleSniper`, `RoleOfficer`, `RoleSF`, five `SkillAim*`, `NonCombatant`, `IsFemale`). A 4-row rule "pseudo-weapon → role hint", applied only where the basis is fallback or picture, raises agreement to 46/50. Detection must key on the tag list, not on `weaponType`. The tags classify as "put" only because a launcher header is missing.
- **Vehicle roles are not validated, and on CWE they are wrong [V].** The weapon-kind thresholds were calibrated on vanilla ammo. CWE gives the AT-3 ATGM `airLock=1` (vanilla 0), so Bradley and BMP-2 grade as APCs, not IFVs. Its ZSU cannon (hit 9, vanilla 40) grades as an MG, so the ZSU drops out of SPAA. CWE also sets `attendant=0` on the M113 and BMP ambulances. The fix: grade weapons relative to the set's own ammo distribution (for example, a missile with `irLock` whose hit exceeds the set's MBT armour counts as AT); record kind and role with a basis; add a vehicle-role eval as an opt-in corpus test; and let convention adapters declare scripted mechanics ("this mod heals from ambulances by script"). Until then the UI labels vehicle roles "derived, unvalidated".
- **Public does not mean unit [V].** CWE exposes 15 public grenade-helper "vehicles" (simulation car, `maxSpeed` 0, horn only; 14 at armour 90,000). Unit menus take only `UnitKind`s. A land vehicle with `maxSpeed` ≤ 0 and no real weapon goes to the object and module pickers (doc 31), and placing one through Wilco raises a lint.

### 2.4 Menus a weak model can use

| Measure [V] | Vanilla | CWE |
| --- | --- | --- |
| Flat unit list per side (West / East / Resistance / Civilian) | 54 / 39 / 25 / 31 | 56 / 37 / 40 / 32 |
| Max role groups per side + kind | 7 | 6 |
| Max roles per group | 4 | 4 |
| `CfgGroups` presets (groups, unit slots) | West 4 (25), East 4 (25), Resistance none | West 12 (84), East 11 (70), Resistance 8 (46); West Infantry alone has 10 |

- **Hierarchy.** side (≤ 4) → kind (≤ 7) → role group (≤ 7) → role (≤ 4) keeps every model step within doc 25's ≤ 7 options plus `X none_fit`, on both catalogs [V].
- **Variants.** The case-study collapse key (side, kind, role, weapon-kind set, flags) was too loose. It merged M1A1 with M60 (armour 900 vs 300), T-72A with T-80BV, AH-1 with AH-64 and CH-47 with UH-60. In 9 of 20 vanilla groups and 9 of 26 CWE groups the members differ by more than 20% in armour or speed, or in cargo [V]. Collapse only true equivalents: the same weapons list, armour and speed within a band, the same cargo. Where a role still has distinct variants (up to 6 in vanilla and 12 in CWE [V]), code either chooses from the brief's era chip or offers a variant Pick of ≤ 7, and shows the result as an editable chip. M60 against M1A1 is an era choice, not noise.
- **Squads.** `CfgGroups` presets are one-pick squads under a category step, paged when a category has more than 7 (CWE West Infantry has 10).

### 2.5 Knowledge overlays as T0 packs

Overlays **add knowledge; they never override facts**. They extend doc 17 §7.2's `llm:` notes and doc 34 mo04's `[activation] mods`.

- **Key:** (engine ModId, version range or catalog-fingerprint range, class).
- **Allowed fields** (a controlled vocabulary, in our own words): `summary`; `tactical_notes`; strengths, weaknesses and counters (doc 17 §7.2); `era` and `faction_label` (the config has neither); `aliases` for resolving brief text; `role_hint` (applied only where the card basis is fallback or picture); `equivalents` (tie-breakers only, §2.9); convention rules (pseudo-weapon or picture → role hint; declared scripted mechanics); and `expects = {side, kind, role}` guards.
- **Staleness.** A row whose `expects` contradicts the loaded card is disabled and reported as stale. Rows for classes that are not loaded stay inert.
- **Pack lint.** It rejects fact fields (side, weapons, crew, scope) and copied mod text; display names always come from the loaded config at runtime.
- **Location.** Packs use doc 22 §2.1's `catalog/*.toml`. Doc 17 §7.2's `data/llm/classes/*.toml` becomes the source folder of the built-in vanilla overlay pack (doc 34 mo22), so there is one format and one loader.
- **Demand in the case study [V].** 28 CWE and 10 vanilla cards have fallback basis; no card in any set has era or faction; 62 CWE soldiers use a decodable convention; CWE's vehicle roles need correction hints.

### 2.6 How S0 picks the mod set

Doc 27 §4.8 gives S0 a `mod_set` field, and §4.9 gives each campaign one mod set. The case study adds four requirements:

- **Resolve quoted brief phrases** (doc 25's quote check) against every installed set valid for the target. Sources: catalog labels (through the set's own stringtable), overlay aliases, ModIds, and the directory pack's names. Code scores which sides, eras and named hardware each set covers.
- **The menu (≤ 7)** lists the sets that satisfy the brief and always includes Vanilla. It marks platform sets valid only on their targets: CWE's launcher runs Fwatch and its changelog adds OFP 1.96 support, so CWE is `Cwa199`/1.96-only [V].
- **Unmatched mentions** become "not installed" chips (§2.7). They trigger a channel lookup only if the connector is on.
- **Eras and factions** are filled by code from pack defaults as visible assumption chips. Vanilla itself mixes eras (a WW1 Camel addon beside Cold War classes [V]), so an era is never inferred as a fact.

```rust
pub struct ModSetOption { id: ModSetId, kind: SetKind /* Mod | Platform */, fingerprint: Fingerprint, target_ok: bool,
                          covers: Coverage /* sides, roles, aliases hit */, missing_mentions: Vec<QuotedMention> }
```

After S0, V-catalog rejects any class outside the chosen set's fingerprinted catalog. Changing the mod set later runs the remap workflow (§2.9); it never edits classes silently.

### 2.7 "Use mod X" when X is missing

Channel metadata cannot make an absent mod usable for generation. Neither PB nor GS exposes `CfgPatches`, units, sides, weapons or dependencies, and Nexus and ModDB expose none either. PB's only `requiredAddons` string is a per-server registration field (`CE:mserver/MasterService/src/model.rs#L77-L78`, `#L127-L128`, against `ModCatalogEntry` at `#L281-L329`) [V].

When the brief (or the user in chat) names X and no valid installed set contains it, code builds one card with three routes. The choice is the user's, because it costs them a download or a compromise; the model may only mark one as recommended. In an unattended run, code takes route 2, which is reversible, and keeps X as a pinned requirement (route 3) [I]:

1. **Get it.** A "where to get" card from the directory pack or the live connector: channel, id, revision, size and target compatibility, an "Open page" button, and the install instruction for that channel (§3.3). After the user installs, Plotroom rescans, fingerprints and offers X as a set.
2. **Build now with vanilla stand-ins.** Units come from the remap tiers (§2.9) as candidates for the intended role. Each generated entity carries a `pending_remap { mod, intent }` badge on the map and in the state panel, and the brief keeps X as a pinned requirement. Mod mechanics (modules, mines, scripted systems) are never substituted; they are listed as "needs X". When a later scan finds X, the stored intents become the input of the remap workflow (§2.9), so "Swap stand-ins for X" is one reviewed step [I].
3. **Declare the requirement and continue.** X is recorded in the manifest (§2.8) with whatever identity is known. The mission stays buildable without X's classes.

The model never sees a class name of an absent mod, and code never generates ghost classes. Nothing installs automatically.

**Real content shows the size of the problem [V].** In CWE's 5 own missions, 270 of 1,274 `vehicle=` entities (21%) do not exist in vanilla CWR. 202 of them are units, and each has a same side, kind and role vanilla candidate (by the derived roles). The other 68 are mod mechanics with no equivalent: 28 logic modules and 40 mines. Opening such a mission follows doc 27 §4.11 (ghost entities, "Pick a mod set that has them") plus doc 35 rc84: "Remap to an installed set" (units through remap; modules and mines "drop" or "keep as ghost"; rc84 says "Retarget to mod set", but doc 37 §5 reserves "Retarget…" for changing the target profile); `addOns[]` re-derived from reasons; or keep the requirement. The reverse matters too. Re-saving CWE's 146 shipped vanilla-mission copies under CWE would change `addOnsAuto` in 59 of 168 sections (68 names added, mostly `cwe_standard`, plus `bizon` and `bd_flashbang`), so every re-saved section would then require CWE [V]. Before such a save, Plotroom warns that saving under a platform set captures vanilla classes.

### 2.8 Requirement manifests and the "Requires" badge

A requirement cannot always be expressed as a `-mod` line. CWE is a **platform**. Its launcher preprocesses and packs `ModConfig.cpp` files, writes headers that supplement the main config, switches the user profile through the registry, temporarily renames game folders, launches helper executables, and reverts everything on exit. The effective config therefore depends on launcher state: two generated headers are missing on disk, and a launcher-chosen PBO toggles the dynamic sound system, which guards 44 config lines [V: install listing, readme files, config includes]. The manifest extends doc 27 §4.5 and aligns with `mod.json` and PB's `ModCatalogEntry`. It is written next to the exported PBO, never into `mission.sqm`:

```toml
# <mission>.requires (proposal-only; placeholder values). Shown as TOML for readability: doc 27 §4.5 writes the
# manifest as JSON plus a README block, and the serialization stays doc 27's decision.
target = "Cwr"
[[requires]]
shape = "mod"                       # "mod" | "platform"
need = "required"                   # "required" | "recommended" (doc 34 mo08 calls this `kind`; doc 27 §4.9)
id = "examplemod"                   # engine ModId (basename, no leading '@', lower case)
folder = "@ExampleMod"; name = "Example Mod"; version = "1.2"
packageRevision = 3                 # mod.json / PB spelling, as in doc 34 §4.1; absent for GS and local installs
sha256 = "…"                        # catalog package hash, only if mod.json carries one (names the download, not the tree)
fingerprint = "…"                   # doc 27 §4.7 catalog part: the authoritative identity
patches = [{ name = "examplemod_units", reasons = 12 }]
channels = { papa_bear = "examplemod-1.2", game_schedule = "0123abcd", homepage = "https://…" }
[[requires]]
shape = "platform"
need = "required"
id = "exampleplatform"
targets = ["Cwa199"]
launcher_state = ["dss:on", "generated-headers", "stringtable:declared"]   # folded into the fingerprint
```

- **MP.** Servers advertise catalog modIds with revisions (`modPackages {modId, packageRevision}` on 4 of 13 live servers; `CE:engine/Poseidon/Network/NetworkServer.cpp#L594-L599`) [V], so the requirement carries `(modId, packageRevision)` too.
- **Badge.** Doc 27 §4.5's "Requires:" badge adds size (from the directory or `mod.json`) and "platform: runs only through its launcher". A mod set whose provenance is unverified (§6.4 D12) says so.
- **Upstream alignment.** CE issue #233 (open) asks for mission mod dependencies identified by a content hash, and #228 (open) asks to persist the active mod collection [V]. Plotroom should take part so that this manifest matches whatever lands.

### 2.9 Cross-mod equivalence for remap

Doc 27 §4.8's "vanilla-safe" swap, doc 35 rc84's "retarget to mod set" and doc 37 §5's class remap become one typed workflow. It is reliable only as a tiered candidate list that code builds, not by inheritance alone [V]:

| Direction | Classes | Same side + kind + role candidate | Other results |
| --- | --- | --- | --- |
| CWE → vanilla | 45 CWE-only units (42 infantry, 1 aircraft graded) | 42 (93%); 3 need the side + kind tier | The nearest vanilla ancestor has the same role in only 33/43 (77%). Top-1 is that ancestor in 26/43, and the top 3 contain it in 36/43. Top-1 matches the display-name role in 12/16 |
| Vanilla → CWE | 29 vanilla units hidden or absent in CWE | 26 | Top-1 matches the display-name role in 19/20 |

- **Tiers:** 1 = side + kind + role; 2 = kind + role on any side; 3 = side + kind. Ranking uses armour, speed, cargo and cost ratios plus weapon-kind and flag overlap. Code offers up to 3 candidates, each showing its tier and confidence; the model only ranks and the user confirms. Human-edited entities are never swapped silently. T0 `equivalents` may break ties only inside a tier.
- **A shared class name is not a shared unit.** Of 120 unit classes that CWE shares with vanilla, CWE changed weapons for 68, display names for 40 (58 with its own stringtable) and derived roles for 8 [V]. The drift report (doc 34 mo03) therefore diffs cards, not names.
- **Gate vehicle remaps** on the vehicle-role eval (§2.3); the graded set is infantry.

### 2.10 Caching per fingerprint

Measured on the owner's machine [V]: parse and merge took 0.19–0.24 s for vanilla and about 2.6 s for CWE (a 784 KB main config plus 45 PBO headers); building cards took 0.02–0.09 s; a stat-only revalidation took 1.3–4.9 ms; serialized cards take 0.17–0.50 MB per set. The inputs doc 27 §4.7 hashes for CWE come to about 1.1 MB, plus the 0.78 MB loose main config, out of 943 MB of PBOs. Full-content SHA-256 would take about 9–10 s. So doc 27 §4.7 stands: revalidate by stat, re-hash only the header, config and stringtable entries of changed PBOs, and never hash whole PBOs by default. Two additions: platform sets fold their launcher-state inputs (the chosen sound PBO, generated headers, the declared stringtable) into the fingerprint, and the cache also holds cards, menus and the overlay join. Stable menus per fingerprint keep prompt prefixes byte-stable, which helps provider prompt caching [I].

## 3. Discovery and acquisition

### 3.1 The channels, checked 2026-09-27

| # | Channel | Metadata | Deep link and hand-off | Versioning | Integrity | Terms, third-party clients | Scale | Plotroom use |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CH1 | **PB**, the game's MODS storage for CWR 3.05 and CE (default master service in both trees: `BI:`/`CE:engine/Poseidon/Network/NetworkConfig.cpp#L7`) | `modId`, `folderName`, `name`, `version`, `packageRevision`, `compatibleActvers`, `sha256`, `sizeBytes`, `homepageUrl`, `downloadUrl`, `authors`, `description`, `publishedUnixMs`. No licence, dependency or class fields (`CE:mserver/MasterService/src/model.rs#L281-L329`) | Page `https://papa-bear.cz/mods/{modId}`. Install happens in the in-game MODS screen, through `papa install` for servers, or on MP join, where a requirements dialog offers "download & join"; it is not automatic (`CE:engine/Poseidon/UI/DisplayUIMultiplayer.cpp#L1193-L1196`). The web page's "ADD" button only toggles an in-page selection | Immutable revisions, each with its own `compatibleActvers`. The newest compatible revision is served, and the client never downgrades (`CE:mserver/MasterService/src/mods.rs#L927-L940`; `CE:engine/Poseidon/Core/ModInstall.hpp#L29-L36`) | SHA-256 and size of the uploaded `.pbo.zst`, both skipped when the catalog gives none (`CE:engine/Poseidon/Core/ModInstall.cpp#L150-L153`). No publisher signature; writes are gated by one admin key when one is configured (`CE:mserver/MasterService/src/http.rs#L1334-L1356`) | No terms, API policy or robots.txt (`/robots.txt` and `/terms` return 404). The OpenAPI 3.1 file declares MIT and no `termsOfService`. Whether third-party clients are welcome is [U] | 13 mods, all for actver 305, 5.24 GiB total, 71 KB to 1.09 GB each, published 2026-08-17/18; 13 servers (10 verified), 0 players at fetch time | Primary for CWR/CE targets: directory rows plus opt-in lookup |
| CH2 | **GS + Fwatch** (legacy OFP 1.96, CWA 1.99, ArmA Resistance 2.01; "not compatible with the remaster") | 25 fields per record (name, version, size, website, `req_version`, type, admin, `updates[]` with install scripts). No hash or dependency field | `show.php?mod=<8hex>[&ver=]`; RSS at `rss?mod=all` and `rss?server=all` (40 items each). Installs only inside the legacy game, through Fwatch's MODS button (`wget.exe` plus `addonInstaller.exe`) | Version strings plus per-update scripts | None: 0 checksum commands in 176 scripts, 27 download hosts, 70 of 123 mods using mirror lists; several hosts fail DNS or TLS | None published; `/robots.txt` 404 | 123 records (120 names), `req_version` 1.96 for 115; 11 KB to 19.16 GB, about 58 GB total; 7 changed in the past year; one curator holds 89 | Legacy targets: ids and links only; never fetch or run scripts |
| CH3 | **ofpisnotdead.com** hub and `files.ofpisnotdead.com` file server | None structured; a plain index of about 50 entries, no checksums | Links only | — | — | The file server asks visitors not to download everything for mirroring, because bandwidth is limited | Homepage of 3 PB mods; a major GS script host | Link-out target only |
| CH4 | **Nexus Mods** (`armacoldwarassault`, game id 1729) | Name, version, uploader, size, counters (GraphQL) | Mod page URL (pages return 403 to automated fetches) | Per-file versions | Nexus scans uploads (its help centre) | The API acceptable-use policy tolerates personal keys for personal use, requires public apps to register, and forbids "fetching data en-masse with the intent to rehost" | 4 CWA mods; Operation Flashpoint 1 | Link-only, from pack- or user-supplied URLs |
| CH5 | **ModDB** | Unknown (403 to WebFetch and PowerShell) | Mod page URL | Unknown | Unknown | `robots.txt` blocks `/downloads/start/`, `/downloads/mirror/`, `/search` and every `?` query, blocks AI crawlers site-wide, and declares `ai-train=no`. No official API found [I]; the terms page is unreadable [U] | Hosts the CSLA page linked from BI's 3.05 notes and the RCWC page linked in CE discussion #114 [V] | Link-only; no connector, no scraping |
| CH6 | **Steam Workshop** | — | — | — | — | — | None: 0 Steamworks/UGC hits in either tree, no Workshop tab on the app 65790 hub, and none in the store's category list | Drop. If BI adds one, it becomes one more read-only source behind the same interface |
| CH7 | Legacy file hosts (OFPEC, the armaholic archive, lonebullet, mediafire, gamefront, g-g-c.de and others) | None | Direct links | None | None | Various | Some unreachable (gamefront 403, g-g-c.de TLS failure) | User-supplied links in a manual "where to get" note |
| CH8 | Author sites and platform launchers (for example csla.cz; CWE's own launcher) | Free text | Links; platform readmes | Per author | Per author | Per author | 4 PB records use GS pages and 1 uses csla.cz as `homepageUrl` | Link-out; "install and launch as its readme says"; never executed |

**No shared identifier [V].** PB uses modIds (mostly slug-version; two start with `@`) plus a verbatim `folderName`. GS uses 8-hex ids and `@` names. Local installs have only folder names. Under the engine's ModId normalisation (basename, leading `@` removed, lower case; `CE:engine/Poseidon/Core/ModId.hpp#L10-L38`), 8 of 13 PB `folderName`s equal a GS name exactly. `80+Islands` and `@xrofp_REM` match only loosely, and 3 have no match. Four PB records already point to their GS entry through `homepageUrl`. The CWE mod is in neither catalog.

**Popularity [V, trend I].** 16 concurrent Steam players in two snapshots on 2026-09-27; PB seeded with 13 mods in August 2026 and 4 open mod-request threads; 7 GS records changed in a year; 4 Nexus mods. The ecosystem is small and concentrated. With Remastered 3.05, the in-game MODS screen plus PB became the official path, and Fwatch/GS stays legacy-only.

### 3.2 Options compared

| Option | What it means | Value to users | Cost to us | Legal risk | Security risk | Fits the invariants? | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| O1 Nothing | Detected mods only; no links | "X not installed" is a dead end | None | None | None | Yes | Keep as the offline floor, not the answer |
| O2 **Integrate** | Offline directory pack, opt-in metadata connector, hand-off to the channels' installers | Where to get X, which revision, how big, whether it fits the target, which servers use it | A pack regenerated per release, one small connector, maintainer outreach | Low: facts and links; unknown terms → ask first | Low: GET-only JSON, no binaries | Yes, once the feed kind is decided (§3.4; decided 2026-09-27 → [D008](../decisions/D008-outbound-network-sources.md)) | **Adopt** |
| O3 Download in core | Core calls PB's download routes, unpacks and installs | Convenience | Staging, zstd and PBO unpacking, updates | Plotroom would distribute third-party archives of unknown licence | Multi-GB hostile archives, and an unpacking attack surface (PB's upload cap is 32 GiB; a code comment cites an 11 GB mod) | No: contradicts doc 27 open question 6 and the product scope | Reject |
| O4 Own game-mod market | Plotroom hosts or mirrors mods, with accounts and moderation | Splits a small community | Staff (Nexus reportedly had about 40 people at its 2025 sale [V-search]), DMCA, malware scanning, storage | Rehosting without consent has drawn public objections in the Arma scene [V-search]; APL-SA bars paid access to mods that adapt BI data (doc 02 §3), and §5.3 rules out money entirely | Account takeover is the common vector (fractureiser 2023, npm Shai-Hulud 2025) | No | Reject |

### 3.3 The recommendation: an offline directory plus an opt-in first-party connector

**Default, offline.** The built-in Community mod directory pack (§4.2) answers "where to get X" with no network at all.
**Optional, live.** One first-party connector, "Community catalog", is off by default and suggested once, in context (§7.2). It is read-only and has one query-effect tool that returns `CatalogHint` rows. (Its `feed` connector kind: decided 2026-09-27 → [D008](../decisions/D008-outbound-network-sources.md); its wait for the channel maintainers' non-objection: answered 2026-09-27 → [D035](../decisions/D035-outreach-and-security-disclosure.md) item 4.)

- **Which channels, in order.** First PB, the default for `Cwr`/`Ce` targets. Then GS, for `Cwa199` and 1.96 targets. Nexus, ModDB and the file hosts stay link-only.
- **Metadata only.** Allowed PB routes: `GET /v1/meta/service`, `/v1/mods` (filters `app`, `actver`), `/v1/mods/{id}`, `/v1/mods/{id}/revisions`, `/v1/mods/{id}/servers` and `/v1/servers/versions` (route table: `CE:mserver/MasterService/src/http.rs#L169-L218`). GS: `GET /schedule/api?mod=all`; the `password` parameter is never sent or stored. Both `/download` routes and every write route (POST, PUT, DELETE) are outside the allowlist. The client never sends `x-api-key`.
- **What is sent.** The target game version (for example `actver=305`) and, on the per-mod routes, a channel mod id that code took from the fetched list, which tells the service which mod the user looked at. The catalogs are small (13 and 123 records), so the connector fetches the list and code searches it locally; brief text never leaves the machine. Ids from the feed are untrusted: each is percent-encoded as exactly one path segment, and the allowlist is checked on the final request path, so an id such as `x/revisions/1/download` cannot reach an excluded route. Responses are cached with their fetch time, with one refresh per session plus a manual refresh.
- **Guards** (doc 22 §3.2): a pinned origin, HTTPS only, no redirect off the origin (PB answers `/download` with a 307, one more reason that route is excluded), caps on response size and depth, timeouts, schema validation, an egress card on first use, and an egress log.
- **Hand-off.** A user-clicked "Open on papa-bear.cz" opens `https://<origin>/mods/{modId}` in the system browser (doc 22 §2.3 URL rule), next to the instruction "Install from the in-game MODS screen, then come back; Plotroom rescans." The rescan runs by itself when the known mod roots change or the window regains focus, so the user never hunts for a button [I]. Links that are not `https:` (common among legacy hosts) are shown as copyable text and never opened (doc 22 §3.2). For a legacy target the card shows the GS `show.php` link and "install with Fwatch (legacy game only)". For MP missions, the exported set's launch line lets hosts run the right set, and joining CWR clients are then offered the download by the game [I]. (A user-clicked "Launch the game to install mods" for CWR and CE targets, which starts the game vanilla without `--private` or a mission: answered 2026-09-27 → [D038](../decisions/D038-mod-handling-owner-additions.md) item 1.)
- **Integrity labels.** Plotroom downloads nothing, so it verifies nothing. It shows the catalog hash as "catalog hash (PB)", never as a Plotroom "verified" badge. The local fingerprint (doc 27 §4.7) stays the truth for drift. "Matches PB rev N" is a separate provenance badge (§4.1).
- **Never done.** Downloading, installing, unpacking; caching, proxying or mirroring artifacts or pages; calling write routes; scraping HTML; running GS scripts, Fwatch, `papa` or a platform launcher; auto-updating mods; opening URLs without a click; sending brief or mission text.

```rust
/// One read-only row from a community channel (proposal-only). Never feeds class menus (MG1).
pub struct CatalogHint {
    channel: Channel,                       // PapaBear { origin } | GameSchedule { origin } | Directory { pack: PackId }
    channel_id: ChannelModId,               // e.g. a PB modId or an 8-hex GS id
    mod_id: ModId,                          // engine-normalised folder name (doc 27 §4.2)
    name: Untrusted<String>, version: Untrusted<String>,
    package_revision: Option<u32>, sha256: Option<Sha256>, size_bytes: Option<u64>,
    targets: Vec<TargetProfile>, page: Option<HttpsUrl>, fetched_at: Timestamp,
}
```

### 3.4 The design gap: the channels speak REST, not MCP

Doc 22 makes Streamable-HTTP MCP "the only T2 transport" (§2.3), and its open question 4 asks whether REST-only services get a host-mediated `net.fetch` or must use MCP. Both catalogs are plain HTTPS JSON (PB has a live OpenAPI 3.1 file). A Plotroom-run MCP shim would add a Plotroom-operated host to the outbound path, contrary to the "model provider plus enabled plugins" rule unless that host were itself a declared endpoint, and it would give us a service to run. **Proposal [I]:** a narrow connector kind `feed`. It is GET-only, has a pinned or user-typed HTTPS origin and a fixed host-owned schema (`papa-bear-v1`, `game-schedule-api-1`), takes enum filters only (no model-written parameters, no mission data), has no secrets and no binary or download routes, and gets the doc 22 caps, egress card and log. **Blocked on an owner decision.** A request should be filed in `docs/design-gap-requests/` (the folder does not exist yet; suggested name `DGxxx-t2-read-only-catalog-feeds.md`, following doc 17's `DGxxx-*.md` pattern), and the connector stays proposal-only until then. (Filed as DG028 and decided 2026-09-27 → [D008](../decisions/D008-outbound-network-sources.md) item 3: the `feed` kind is adopted; the connector still waits for the channel maintainers, answered 2026-09-27 → [D035](../decisions/D035-outreach-and-security-disclosure.md) item 4.)

```toml
# community-catalog/plugin.toml (proposal-only; kind "feed" does not exist yet)
[plugin]
id = "community-catalog"; kind = "feed"; license = "GPL-3.0-or-later"
[provides]
tools = ["catalog_lookup"]                     # effect = "query"; output schema "catalog-hint@1"
[feed.papa_bear]
origin = "https://papa-bear.cz"; schema = "papa-bear-v1"
allow = ["GET /v1/meta/service", "GET /v1/mods", "GET /v1/mods/{id}", "GET /v1/mods/{id}/revisions",
         "GET /v1/mods/{id}/servers", "GET /v1/servers/versions"]
query = { app = "from-target", actver = "from-target" }
[feed.game_schedule]
origin = "https://ofp-faguss.com"; schema = "game-schedule-api-1"; allow = ["GET /schedule/api?mod=all"]
[limits]
max_response_bytes = 4194304; timeout_ms = 15000; cache_ttl_hours = 24   # placeholders
[network]
user_agent = "Plotroom/<version> (+<repository url>)"                     # final form per the maintainers
reasoning = "Fetches public mod lists; sends the target game version and, for a detail view, that mod's catalog id"
```

### 3.5 "Custom market": any compatible origin, not a Plotroom service

The engine already supports alternative catalogs [V]. The game takes `--master-server <host>` (`CE:engine/Poseidon/Foundation/Platform/AppConfig.cpp#L410-L413`; one override switches both the server browser and the MODS screen, `CE:engine/Poseidon/UI/OptionsUIApp.cpp#L1927-L1945`). The CLI takes `--master`/`PAPA_MASTER` (`CE:mserver/CLI/src/main.rs#L50-L52`), and the downloaded-mods root is configurable (`--workshop-dir`). PB's crates declare MIT and ship a Dockerfile (`CE:docker/papa-bear-master-service/Dockerfile#L1-L21`). Upstream integration tests even start a local master service seeded with fixture mods (`CE:tests/integration/mods/workshop_live_download.test/test.toml#L5-L25`). So a community that wants its own catalog can run one today, and the game can use it.

- The connector's origin field accepts any HTTPS origin the user types in, and it is reviewed like a T2 origin. Registry manifests may pin only the default origins; loopback follows doc 22 §2.3's typed-in-only rule.
- A third party's own connector is just another user-installed plugin under the same manifest rules (doc 22). Plotroom runs no market of its own.
- Connector tests run against a synthetic stub of the OpenAPI subset, as the upstream harness does, and never against recorded live catalog text (MAT9).

## 4. Good defaults

### 4.1 Vanilla plus auto-detected installed mods

The first scan covers doc 27 §4.2's roots: the game directory, `<UserContent>/Mods`, `<UserContent>/Workshop` (`Documents/Cold War Assault` on Windows; `CE:engine/Poseidon/Foundation/Common/GamePaths.hpp#L95-L106`) and folders the user adds. Identity comes from the folder name (ModId), `mod.json` (read by the engine as `catalogId`, `CE:engine/Poseidon/Core/ModCollection.cpp#L318-L324`) and a GS `__gs_id` file, which CWR's source never reads. Provenance has four levels, and every field is treated as untrusted data:

| Level | Condition | Badge |
| --- | --- | --- |
| 1 | Folder under `Workshop`, and `mod.json` has `sha256` or a `downloadUrl` on the pinned PB origin (the engine writes these on install, `CE:engine/Poseidon/Core/ModInstall.cpp#L469-L497`) | "PB `<modId>` rev N" |
| 2 | `mod.json` names a `modId` | "claims catalog id `<modId>`". It proves nothing, because BI's own custom-mods guide tells authors to hand-write `mod.json` with a `modId`, and the engine reads it from local folders too [V] |
| 3 | A `__gs_id` file | "GS id `<8hex>`" |
| 4 | None of these | "source unknown; add a link" |

On the owner's machine, `Mods` and `Workshop` are empty, and the CWE and Fwatch folders carry no `mod.json` or `__gs_id` within three levels [V]. Level 4 will be common, so matching needs help: code proposes candidates (ModId equality first, then a `homepageUrl` → GS id link, then loose matches the user confirms), and a human-curated T0 **mod alias table** keyed by ModId records the confirmed ones. The AI never guesses identity.

**Game-folder addons [I].** Third-party PBOs dropped straight into the game's own addon folders (a long-standing habit on 1.96/1.99) are not a mod folder: they load with every launch, so a set named "Vanilla" would silently include them. The scan compares the base roots' PBO stems with the stock list for the detected executable (names only: a list of facts, not BI data) and shows extras as "Game-folder addons" with their own provenance chip. Vanilla-labelled AI menus leave their classes out unless the user opts in, which keeps doc 27 §4.1's "vanilla-loadable by default" true.

### 4.2 Built-in packs and "known mod set" presets

- **Vanilla overlay pack** (doc 34 mo22): our own notes on vanilla classes. The rows Wilco's menus need cannot be disabled.
- **Community mod directory** (T0, metadata only): one row per PB mod plus its GS cross-walk. Each row has the ModId, channel ids, name, version, `packageRevision`, `sha256`, size, `compatibleActvers`, and channel links labelled by channel (PB's `homepageUrl` is heterogeneous: GS pages, file-server paths including a direct archive link, an author site, or nothing). It copies no descriptions; author names appear only as the channel's author field, for credit (§6.5). Maintainers regenerate it at each editor release with a script outside the editor, from the public APIs, and review the diff. Every row carries its snapshot date. (Freshness: answered 2026-09-27 → [D038](../decisions/D038-mod-handling-owner-additions.md) item 2: regenerated at each release, plus the opt-in connector's live refresh; no third-party metadata in Plotroom's registry.) It ships only after the PB and GS maintainers have been asked and have not objected, not on a bare notice: copying a substantial part of a curated catalog can touch the EU sui generis database right even when each row is a plain fact, and PB at least sits on a `.cz` domain (where each operator is based is [U]) [I; not legal advice] (Open questions 1–2, 4; who asks and what counts as non-objection, a written reply that does not object or no objection 30 days after an acknowledging reply: answered 2026-09-27 → [D035](../decisions/D035-outreach-and-security-disclosure.md) item 4).
- **Presets.** A directory row becomes a one-mod preset ("Example Mod, CWR 3.05, rev 3") that resolves only once the mod is installed and scanned. Multi-mod presets come from users (`*.modset.toml`, §7.4) or from importing a server's advertised mod list (doc 34 mo19). Plotroom invents no combinations, because no channel publishes dependencies.

### 4.3 First run

1. The install probe (doc 27 §4.2) lists the executables and target profiles it found.
2. The mod scan lists detected mods with size, provenance level and target validity, and indexes them in the background (doc 34 mo05).
3. The project starts on **Vanilla**. Each detected, valid mod is offered as a one-click mod set; nothing is enabled by guesswork.
4. The "Find mods" panel (§7.3) works offline from the directory. A single quiet line says "Online lookup is off", with a toggle that opens the connector's install review. No first-run dialog asks for network access.

## 5. The Plotroom content-pack registry

### 5.1 Scope and phases

The registry distributes **Plotroom packs only**: T0 overlays, convention adapters, alias and equivalence tables, templates, skills, workflows, lint sets, and later T1/T2 plugin manifests (doc 22 §7.1 step 4; doc 34 mo14). It never lists or hosts game mods. Only the pack manager, at the user's request, contacts the registry; the agent never does. Packs can always be installed from a file.

**Network rule gap [I].** AGENTS.md names only the model provider and enabled plugins as outbound destinations. Registry traffic is neither, so it needs the same treatment as a connector: the registry is a source the user enables in the pack manager (its origin shown and reviewed like a T2 origin, off until enabled, blocked in offline mode), and pack files are fetched only from the forge origins that the signed index allowlists, then checked against `pack_hash` before anything is unpacked. The §3.4 design-gap request should cover this too. (Covered by DG028 and decided 2026-09-27 → [D008](../decisions/D008-outbound-network-sources.md) item 4: the registry is a user-enabled source.)

| Phase | Shape | Exit evidence |
| --- | --- | --- |
| RG0 | Built-in packs plus sideloading from a folder or zip (unsigned sideloads get a badge and need a developer toggle, doc 22 §3.2) | Pack loader, validator and hash pinning tests |
| RG1 | A curated index: one public Git repo of per-version TOML manifests, PR-based and CI-gated, with a minisign-signed `index.json`. It hosts no binaries: a manifest names a source repo and commit SHA, and CI recomputes the pack hash | MAT14, MAT15 |
| RG2 | Community submissions with throttles (below) and namespaces | Review-time log; first external publishers |
| RG3 | TUF via tuf-on-ci with 2-of-3 hardware-key roots, verified client-side with `tough`, which adds rollback and freeze protection | Signature and rollback tests |

### 5.2 Manifests, CI and review

- **Manifest fields:** `id` (namespace = a GitHub organisation or a verified OFPEC tag), `version`, `kind`, SPDX `license` from the allowlist, `ai` (`generated` | `media` | `assisted`, Nexus Mods' three-tag vocabulary), `source` (git URL plus commit SHA), `pack_hash`, publisher key id, capability hash, `[activation] mods` (mo04), `ai_usage` (mo12).
- **Pack identity** is a dirhash-style hash over sorted per-file SHA-256 lines, as Go's `dirhash` Hash1 does, so zip ordering and timestamps do not matter. Relative paths are normalised; CI rejects `..`, absolute and drive paths, newlines in names and case collisions. `plotroom.lock` (mo16) records the hash.
- **CI checks:** schema; licence; hash recomputed from the pinned commit; size caps; game-format rejection (our own PBO, raP, WRP, P3D and PAA detectors, doc 07); name similarity against existing ids and OFPEC tags. It also rejects bidi controls, zero-width characters, Variation Selectors (U+FE00–FE0F, U+E0100–E01EF), Tag characters (U+E0000–E007F) and Private Use Area code points in every text file. Those characters hid code from reviewers in the 2025 GlassWorm campaign and double as prompt-injection carriers. CI renders every template with fixture parameters and runs the doc 23/24 linter on the output, rejecting doc 24 L1 deny-listed commands and MC27 path escapes (doc 34). It also runs the doc 22 §4.4 conformance kit, and it re-checks **every** version, not only the first. Obsidian had to add per-version scanning after reviewing only first submissions, and account takeover is how fractureiser, Shai-Hulud and the BeamNG incident spread [V].
- **Humans review** new publishers, T2 endpoints, elevated capabilities, templates whose output touches `exec` fields, and flagged diffs.
- **Throttles** (after Zed): one pack per PR, at most 3 open PRs per author, and PRs closed after 3 weeks without a reply.
- **AI disclosure:** mandatory, with a named accountable human maintainer. This combines Luanti ContentDB's disclosure rule with GNOME's rule that authors must be able to explain what they submit; an outright ban would contradict the product.
- **Licence allowlist [I]:** content that can reach a user's mission (templates, compositions, script libraries, briefing styles) must be CC0-1.0, MIT, Apache-2.0 or CC-BY-4.0 (CC-BY-SA-4.0 is an owner decision; answered 2026-09-27 → [D038](../decisions/D038-mod-handling-owner-additions.md) item 3: allowed for editor-only content, never for content that reaches missions), so exported missions stay shareable. Editor-only content (skills, workflows, lints, overlays) may use any GPL-3.0-compatible licence. T1 stays GPL-3.0-compatible (doc 22 §5.2). The mo13 licence audit enforces this at export.
- **Reconcile doc 34 mo14:** CI cannot hash against "known BI data" it does not have. The practical form is format detection plus hash lists that users contribute.

### 5.3 Governance, signing and takedowns

- **Maintainers:** two or three, with FIDO 2FA and no long-lived tokens (GitHub's post-Shai-Hulud npm plan points the same way), CODEOWNERS per namespace, and a public succession plan: the index is forkable, clients can move to a new root through a signed key-rotation record, and yank lists survive the move. (Operator: answered 2026-09-27 → [D038](../decisions/D038-mod-handling-owner-additions.md) item 4: none until the registry is scheduled, then the project's own GitHub organisation with this governance.)
- **Signing:** publishers sign manifests with minisign. The index is signed with an offline registry key (RG1), later TUF (RG3). The client pins a publisher key at first install and treats a key change as a re-review, like doc 22 §3.1's capability-hash rule. A signed revocation list covers incidents. Auto-update is off for third-party sources (doc 22 §3.2).
- **Takedowns:** versions are yanked, not deleted. DMCA goes through the forge's process (GitHub publishes redacted notices and restores content after a counter-notice unless a suit is filed within 10–14 days). Policy removals go through an abuse contact, modelled on OpenTTD's. A written rule, following BI's Reforger licensing FAQ, says we do not arbitrate licence disputes between authors.
- **No money:** no paid tier, tipping or revenue share. APL-SA is NonCommercial, and paid-mod experiments (Skyrim 2015) went badly.
- **Steam Workshop for our packs: rejected.** It needs a Steam app, grants Valve a worldwide non-exclusive licence to uploads (SSA §6.A), and would link the proprietary Steamworks SDK into a GPL binary that contains BI code (Valve itself calls copyleft "problematic" there). mod.io remains a fallback if non-Git authors ever need uploads. 0 A.D., a GPL game, pairs mod.io with minisign signatures [V-search].
- **Cost:** GitHub Pages and Actions are free for a public repo at text-pack scale (Pages: 1 GB, soft 100 GB per month). The real cost is 1–3 maintainer hours a week at tens of publishers, if automation carries T0 [I], plus incident response.

## 6. Security and legal

### 6.1 Untrusted PBOs and parsers

Doc 27 §4.10 stands: pure `&[u8]` parsers, caps, fuzzing, per-addon isolation, no execution of config expressions or scripts. The case study adds cases that `ofp-config` must mirror from the engine or diagnose [V]:

- a scalar ends at `;` or at the end of the line;
- braces inside an unquoted value are ordinary characters (the engine does not balance them; `BI:engine/Poseidon/IO/ParamFile/ParamFile.cpp#L81-L103`, `#L1797-L1803`);
- `enum` constants;
- function-like macros with `##` and `#`, multi-line bodies, `#undef`/`#ifdef`/`#else`, and a mid-line `#include` inside arrays;
- top-level classes outside `Cfg*`.

Without the first two rules, CWE's `CfgVehicles` parse stopped at 13 public classes instead of 788. Includes resolve through **bank prefixes**: CWE's version addon includes its own files by prefix and another, launcher-selected PBO. **Amend doc 27 §4.10:** an include may resolve only inside the owning PBO or another bank mounted in the same mod set, never through `..`, absolute paths or unmounted files. A missing include is a per-addon diagnostic ("supplied by the platform launcher?"), not a failure. Each case becomes a synthetic fixture with parser-security tests, including caps on macro passes, include depth and line joins.

### 6.2 Never running mod code

On the owner's install, the CWE and Fwatch toolchains add 21 executables and DLLs, all unsigned. They include a launcher that edits the registry and renames game folders, and a bundled `wget.exe` [V]. Several official binaries are unsigned too, so the risk signal is behaviour, not the missing signature. Plotroom runs none of them, never emulates GS install scripts, and never repacks mod files. It treats install and mod folders as read-only (doc 34 §4.4). Platform mod sets are scanned with the user's launcher settings applied where known, and tagged by D12.

### 6.3 The game's own network paths

- **A mod can redirect the master server [V].** Unless the command line set the host, a `bin\remaster.cpp`/`.bin` in any loaded root with `CfgNetwork >> masterServer` re-points the game's server list, MODS catalog and MP-join downloads (`CE:engine/Poseidon/Core/Config/Configuration.cpp#L355-L374`, `CE:engine/Poseidon/Asset/Addon/ConfigParsers.cpp#L220-L228`; identical lines in `BI:`).
- **`--private` blocks both [V code, I runtime].** It sets the host to empty with source "CLI" (`CE:engine/Poseidon/Core/Config/Configuration.cpp#L220-L221`), which also disables the mod override, and the catalog-URL builder then returns an empty URL. Doc 08 §2.6 already requires it for preview servers. **Proposal:** every Preview launch passes it, clients included, subject to a probe that it has no side effects in single-player Preview. The scanner raises D11 on any mod that sets `CfgNetwork.masterServer`.
- **Missions can still reach the network** through `triHttpGet` and the gated `tri*` verbs, including the MODS-catalog verbs (doc 24 L1 deny, unchanged). "Workshop" in CWR/CE means the PB catalog, never Steam; the UI says "MODS storage (PB)".

### 6.4 Lints added by this doc

| Code | Severity | Fires when | Section |
| --- | --- | --- | --- |
| D10 | warn | A class's owner comes from an empty stub declaration in another addon. The text reads: "every mission using this class will require `<addon>`", and the chain is shown | §2.1 |
| D11 | warn | A mod in the set redirects the game's master server through `CfgNetwork.masterServer` | §6.3 |
| D12 | info | A platform mod set's effective config depends on launcher state (missing generated includes, launcher-selected PBOs, a declared stringtable). Its provenance model is unverified until the parity test passes on the user's install | §2.8 |

### 6.5 Licences and terms

- **Mods:** licence unknown by default. D9 (doc 34 mo10) flags exported files that are byte-identical to mod files, and the handoff bundle (mo15) excludes mod content by construction.
- **Overlays and directory rows:** our own words; facts, identifiers and links only. No catalog descriptions, and no author text beyond what the channel labels as the author field.
- **Channel terms:** PB and GS publish none, so ask before shipping a default connector. Nexus: link-only unless Plotroom registers as an app, which is not worth it for 4 mods. ModDB: `robots.txt` rules it out even before the product-scope rule. BI's own 3.05 notes link out to Nexus and ModDB, which supports "link out, never re-host".
- **PB's licence is inconsistent:** its `Cargo.toml` and the OpenAPI file say MIT, while the CE repo's `LICENSE` is GPL-3.0-or-later with §7 terms. This matters only if we port PB code (for example the OpenAPI subset for test stubs); ask upstream first.

## 7. UX flows

### 7.1 The mod-set picker in the brief (S0)

The brief view shows the chosen set as a chip ("Mod set: Vanilla (CWR 3.05)"). When quoted phrases match other installed sets, S0 shows the ≤ 7 option menu from §2.6. Each option lists what it covers ("West armour ✓, Soviet helicopters ✓, 'Spetsnaz' matched by alias"), its target validity, and its Requires cost. The user or the model picks; code then fills eras and factions as assumption chips.

### 7.2 The "missing mod" card

```text
Not installed: "Example Mod"                          [matched: directory alias · quote "example mod"]
  1  Get it      Example Mod 1.2 · rev 3 · 310 MB · CWR 3.05 ✓      [Open page ↗]  then: in-game MODS screen → rescan
  2  Build now   with vanilla stand-ins (12 units marked "pending remap"; 2 mines listed as "needs mod")
  3  Declare     keep "Example Mod" as a requirement and continue
  X  Not a mod   treat the phrase as plain text
Source: Community mod directory (built-in, snapshot 2026-09-27) · online lookup: off [turn on…]
```

Every number on the card comes from code. Choosing 2 shows the stand-ins on the map with their badge; choosing 1 changes nothing until a rescan finds the mod. (Route 1's install step for CWR and CE targets, a user-clicked "Launch the game to install mods": answered 2026-09-27 → [D038](../decisions/D038-mod-handling-owner-additions.md) item 1.)

### 7.3 The "Find mods" panel

A search box over the directory (and the live cache when the connector is on). Filters: target, channel, installed or not. Each row shows its channel badge, id, revision, size, compatibility, "installed here" (with the §4.1 level) and the fetch time. Actions: open the page, copy the id, "add to requirements", "import server list". There is no "install" button anywhere.

### 7.4 Sharing presets with `*.modset.toml`

Doc 34 §4.1's file gains a `[mod.<id>.channels]` table (the same keys as the manifest in §2.8) and, for platforms, `launcher_state`. "Copy as launch line" writes `--mods-dir … --mod …` for CWR/CE, the shape `papa install` prints (`CE:mserver/CLI/src/main.rs#L880-L925`), and `-mod=` names for 1.99 (doc 27 §4.6). Importing a file never installs anything: unresolved mods appear as "missing" rows with their channel links.

## 8. Phased plan and acceptance tests

### 8.1 Phases

| Phase | Deliverable | Depends on | Evidence |
| --- | --- | --- | --- |
| MS0 | `UnitCard` with bases, the number evaluator, the helper filter, infantry role rules, provenance levels (`mod.json`, `__gs_id`), D10–D12, Preview `--private` | doc 27 M0–M1 | MAT2–MAT6, MAT11, MAT12, MAT16 |
| MS1 | Mod-aware generation: S0 `ModSetOption`, menus, the missing-mod card (offline routes), the infantry remap workflow, the T0 overlay format with the vanilla pack and convention adapters, the requirement manifest and badge | doc 27 M4; doc 25; doc 37 PT3 | MAT1, MAT7, MAT8, MAT13 |
| MS2 | The built-in Community mod directory and the alias table; the offline "Find mods" panel; the vehicle-role eval | Maintainer courtesy notice (superseded by [D035](../decisions/D035-outreach-and-security-disclosure.md) item 4, 2026-09-27: a recorded non-objection, as §4.2 already asks; see also [D038](../decisions/D038-mod-handling-owner-additions.md)) | MAT6 on vehicles; eval report |
| MS3 | The opt-in Community catalog connector | Design gap (§3.4; decided 2026-09-27 → [D008](../decisions/D008-outbound-network-sources.md)); maintainer answers (Open questions 1–2; the outreach rule answered 2026-09-27 → [D035](../decisions/D035-outreach-and-security-disclosure.md) item 4) | MAT9, MAT10 |
| MS4 | Registry RG1, then RG2; RG3 later | doc 22 steps 1 and 4; Open question 9 (the operator answered 2026-09-27 → [D038](../decisions/D038-mod-handling-owner-additions.md) item 4) | MAT14, MAT15 |

### 8.2 Acceptance tests

| # | Test | Pass condition |
| --- | --- | --- |
| MAT1 | Prompts that name absent mods, run through every generation step with a mod set active | Zero admitted classes outside the fingerprinted catalog |
| MAT2 | `addOnsAuto[]` parity: synthetic fixtures, plus an opt-in corpus test gated by an environment variable | Fixtures exact; the corpus lists every mismatch, with the case-study baseline (10/10, 170/178) as the floor |
| MAT3 | A stub-owner fixture: an empty stub in addon A merged before the real definition | Owner = A; D10 fires; the panel shows the chain |
| MAT4 | Card determinism and bases | Same input twice → identical cards; every derived field has a basis; an unresolved macro gives a diagnostic, never 0 |
| MAT5 | Role eval (opt-in corpus) | Infantry agreement ≥ baseline; vehicle roles stay labelled "unvalidated" until their eval passes |
| MAT6 | Menu bounds over synthetic and corpus catalogs | Every menu ≤ 7 plus escapes; no duplicate label inside a menu |
| MAT7 | Missing-mod flow with the connector off | The three-route card appears; zero network requests (mock HTTP client); no class of the absent mod admitted |
| MAT8 | Remap on a fixture with units, script literals, cargo and loadouts | Tiered candidates with tier shown; human-edited entities untouched; one undo restores identical bytes (doc 37 PAT5) |
| MAT9 | Connector against a stub server | Only the pinned origin and allowlisted GET paths; download and write routes never called, including when the feed returns hostile ids containing `/`, `..`, `?`, `#` or `%`; off-origin redirect refused; oversize and malformed responses rejected; no `x-api-key`; no brief text in any request; a non-`https` link is never opened |
| MAT10 | Full generation with the connector disabled | The only network traffic goes to the model provider |
| MAT11 | Provenance levels over crafted `mod.json` and `__gs_id` fixtures, including hostile ones (huge, non-UTF-8, path-like) | Correct level; a hand-written `modId` gives "claims" only; no panic |
| MAT12 | A synthetic mod with `bin\remaster.cpp` setting `CfgNetwork.masterServer` | D11 fires; every Preview launch line contains `--private` |
| MAT13 | `*.modset.toml` and manifest round trip | Export → import → export is byte-stable; launch lines match; unknown keys rejected |
| MAT14 | Registry CI fixtures | Rejects bidi, VS, Tag and PUA characters, a PBO or raP payload, an L1 command in rendered template output, and path escapes; `pack_hash` identical across zip orderings |
| MAT15 | Signing | Bad index signature refused; publisher key change → re-review; yanked version refused for new installs; revocation disables |
| MAT16 | Fingerprint cache | Stat-only revalidation; one changed PBO config re-hashes only that PBO; a platform launcher-state change changes the fingerprint |

### 8.3 What sibling docs should absorb (reconciliation inputs, not edits made here)

| Doc | Change |
| --- | --- |
| 27 | Correct the GS scale (L262–L263: 123 records, 11 KB–19.16 GB, not 77 and 155 KB–3 GB); answer open question 6 ("never install") with §3; amend §4.10 (mounted-bank includes, missing include = diagnostic); add launcher-state inputs to §4.7; add `owner_from_stub` to §4.4; add the §2.8 fields (`shape`, `need`, channel ids, `launcher_state`) to the §4.5 JSON manifest; add game-folder addons (§4.1) to §4.2 |
| 22 | Decide the `feed` connector kind (open question 4; decided 2026-09-27 → [D008](../decisions/D008-outbound-network-sources.md)); add manifest fields `ai`, `ai_usage`, `[activation] mods`; add the RG phases, the licence split and the Unicode and template lints to §7.1 step 4 |
| 34 | mo14's "known BI data" → format detection plus user-contributed hash lists; add `channels` and `launcher_state` to the §4.1 mod-set file; add D10–D12 to §5.1; mo08's `kind` (required or recommended) is `need` in §2.8, where `shape` holds mod or platform, so one name must win |
| 25 | S0 `ModSetOption` and the four-level unit menu; variant chips |
| 17 / 30 | The overlay path (§2.5); overlay text appears only inside code-selected cards |
| 37 | Remap tiers and the vehicle gate (§2.9) |
| 08 | `--private` on every Preview launch, clients included, after its probe |
| 35 | Open item 12 resolved (§2.1); rc84's "Retarget to mod set" label becomes "Remap to an installed set", since doc 37 §5 reserves "Retarget…" (§2.7) |
| `docs/README.md` | Add this doc's index row. The file does not exist yet, although AGENTS.md names it as the entry point; creating it is a separate change |
| `docs/design-gap-requests/` | Create the folder and file the T2 feed request, including registry traffic (§3.4, §5.1) |

## Open questions

1. **Outreach to the PB maintainers** (a post in the CWR-CE `papa-bear-cz` Discussions category): who operates papa-bear.cz; whether third-party read-only clients are welcome; which User-Agent and request rate they want; the inclusion policy; the licence status of the 13 re-hosted archives; MIT or GPL for the MasterService code; whether a directory pack of ids, sizes and links is welcome. Also take part in CE #233 and #228 so the requirement manifest matches upstream [U]. (Who asks and what counts as non-objection: answered 2026-09-27 → [D035](../decisions/D035-outreach-and-security-disclosure.md) item 4; nothing sent yet, and the answers are logged here and in DG029.)
2. **Outreach to the GS maintainer**: API terms, attribution and rate for a read-only client [U]. (answered 2026-09-27 → [D035](../decisions/D035-outreach-and-security-disclosure.md) item 4; not yet sent.)
3. **Feed connector kind or MCP only?** An owner decision (§3.4; doc 22 open question 4). (decided 2026-09-27 through DG028 → [D008](../decisions/D008-outbound-network-sources.md) item 3: the `feed` kind.)
4. **Directory scope:** all 123 GS records, or only rows cross-walked to PB and rows users request?
5. **Platform mods:** what CWE's launcher writes into its generated headers, whether it swaps the main stringtable, and how the scanned (sound-system-off) catalog differs from the user's launched state (sound system on). These are 1.99 probe items [U].
6. **1.99 parity:** whether 1.99 applies owner stamping and preload exactly as the CWR source does. The 170/178 parity supports it; doc 27's probes remain [U].
7. **Vehicle-role grading:** which set-relative thresholds, and which labels serve as the eval's ground truth.
8. **Licence allowlist:** is CC-BY-SA-4.0 allowed for content that reaches missions? (answered 2026-09-27 → [D038](../decisions/D038-mod-handling-owner-additions.md) item 3: no; it is allowed for editor-only content only.)
9. **Registry operator** (doc 34 open question 6), namespace verification through OFPEC tags (does registration need an OFPEC account? [U]), and whether third-party registries may be added by URL. (The operator: answered 2026-09-27 → [D038](../decisions/D038-mod-handling-owner-additions.md) item 4; namespace verification and third-party registries stay open.)
10. **`--private` in single-player Preview:** any side effects? A probe [U].
11. **Nexus:** is link-only enough, or should Plotroom register as an app if the CWA catalog grows?
12. **Pages that returned 403** (ModDB terms, several BIKI pages, Nexus pages): re-check them in a browser before citing them further.

## Sources

**Engine source (pinned).** `BohemiaInteractive/CWR@ffc61838b7` and `ofpisnotdead-com/CWR-CE@b67bf3bd62`; all `BI:`/`CE:` citations are inline. Key files:

- Master service and CLI: `mserver/MasterService/src/{main.rs,http.rs,model.rs,mods.rs}`, `mserver/MasterService/Cargo.toml`, `mserver/MasterService/web/assets/papa-bear.js`, `mserver/CLI/src/main.rs`, `docker/papa-bear-master-service/Dockerfile`.
- Network: `engine/Poseidon/Network/{NetworkConfig.cpp,MasterServerServiceClient.cpp,MasterServerProtocol.hpp,NetworkServer.cpp}`.
- Mods and config: `engine/Poseidon/Core/{ModInstall.hpp,ModInstall.cpp,ModCollection.hpp,ModCollection.cpp,ModId.hpp,ServerModResolve.hpp,Config/Configuration.cpp}`, `engine/Poseidon/Asset/Addon/{AddonSystem.cpp,ConfigParsers.cpp}`, `engine/Poseidon/IO/ParamFile/{ParamFile.cpp,ParamFile.hpp,ParamFileParse.cpp}`.
- Editor and UI: `engine/Poseidon/AI/{ArcadeTemplate.cpp,VehicleAI.cpp}`, `engine/Poseidon/World/Entities/Weapons/Weapons.hpp`, `engine/Poseidon/UI/{OptionsUIApp.cpp,DisplayUIMultiplayer.cpp}`.
- Platform, paths and tests: `engine/Poseidon/Foundation/{Platform/AppConfig.cpp,Common/GamePaths.hpp}`, `engine/Poseidon/Game/Commands/GameStateExtTest.cpp`, `tests/fixtures/workshop/@wsfixture/mod.json`, `tests/integration/mods/workshop_live_download.test/test.toml`.

**Live channel sources (fetched 2026-09-27).**

- PAPA BEAR: <https://papa-bear.cz/v1/meta/service>, `/v1/meta/summary`, `/v1/mods`, `/v1/mods?app=CWR&actver=303`, `/v1/mods/{id}/revisions`, `/v1/servers`, `/v1/servers/versions`, `/openapi/v1.yaml`, `/mods/{id}`, `/assets/papa-bear.js`; `/robots.txt` and `/terms` return 404.
- CWR-CE on GitHub: Discussions category <https://github.com/ofpisnotdead-com/CWR-CE/discussions/categories/papa-bear-cz> (#114, #118); issues #228 and #233; PRs #240 and #57.
- Steam: `ISteamNews/GetNewsForApp` for app 65790 (the Update 3.05 notes and SITREP, 2026-08-17); `ISteamUserStats/GetNumberOfCurrentPlayers` for apps 65790 and 4819000; <https://steamcommunity.com/app/65790/workshop/>; `store.steampowered.com/api/appdetails?appids=65790`.
- BI's custom-mods guide: <https://gist.github.com/simi/11703283038bb6b3a57a2d0d4c374087>.
- OFP Game Schedule: <https://ofp-faguss.com/schedule/>, `/schedule/api?mod=all`, `/schedule/api_documentation`, `/schedule/install_scripts`, `/schedule/show.php?mod=<id>`, `/schedule/rss?mod=all`, `/schedule/mod_updates`; the Fwatch mod manager <http://ofp-faguss.com/fwatch/modmanager/details>; the repo <https://github.com/Faguss/OFP-Game-Schedule>.
- ofpisnotdead.com: <https://ofpisnotdead.com/>, <https://files.ofpisnotdead.com/files/>, <https://master.ofpisnotdead.com/servers.txt>.
- Nexus Mods: <https://api.nexusmods.com/v2/graphql>; API policy <https://help.nexusmods.com/article/114-api-acceptable-use-policy>; scanning <https://help.nexusmods.com/article/128-anti-virus-false-positives>.
- ModDB: <https://www.moddb.com/robots.txt>; the game pages and terms returned 403.
- OFPEC tags: <https://www.ofpec.com/tags/>.

**Registry and marketplace prior art.**

- Steam: <https://partner.steamgames.com/doc/features/workshop/implementation>, `/doc/sdk/uploading/distributing_opensource`, `/doc/gettingstarted/appfee`, <https://store.steampowered.com/subscriber_agreement/english/>.
- Arma Reforger Workshop: <https://reforger.armaplatform.com/news/workshop-licenses-and-ip-faq>, <https://reforger.armaplatform.com/workshop-terms>.
- mod.io: <https://docs.mod.io/moderation/automated-scanning>, <https://docs.mod.io/monetization/how-it-works>.
- Thunderstore: <https://wiki.thunderstore.io/mods/creating-a-package>.
- Incidents: <https://github.com/trigram-mrp/fractureiser>, <https://unit42.paloaltonetworks.com/npm-supply-chain-attack/>, <https://github.blog/security/supply-chain-security/our-plan-for-a-more-secure-npm-supply-chain/>, <https://www.truesec.com/hub/blog/glassworm-self-propagating-vscode-extension>, <https://securelist.com/dozens-of-malicious-wallpapers-found-on-steam-workshop/120186/>, <https://lemonyte.com/blog/beamng-malware>.
- Review practice: <https://obsidian.md/blog/future-of-plugins/>, <https://blogs.gnome.org/jrahmatzadeh/2025/12/06/ai-and-gnome-shell-extensions/>, <https://zed.dev/docs/extensions/publishing/publishing-guide>, <https://content.luanti.org/policy_and_guidance/>, <https://developer.blender.org/docs/features/extensions/moderation/guidelines/>, <https://bananas.openttd.org/manager/tos/1.4>.
- Signing and identity: <https://github.com/theupdateframework/tuf-on-ci>, <https://pkg.go.dev/golang.org/x/mod/sumdb/dirhash>.
- GitHub: <https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits>, <https://docs.github.com/en/site-policy/content-removal-policies/dmca-takedown-policy>.
- Paid mods: <https://en.uesp.net/wiki/Skyrim_Mod:Paid_Mods>.
- Rehosting objections: withSIX/ModDB news and the reply on X, [V-search] only.

**Repo docs.** `docs/research/02`, `07`, `08` (§2.6), `17` (§7.2), `22` (§1.2, §2.1, §2.3, §3.1–§3.2, §5, §7, open question 4), `24` (L1, workshop verbs), `25` (S0, §7), `27` (§2.3–§2.6, §3, §4.2–§4.12, open questions 1 and 6), `30` (§4.6–§4.7), `34` (mo01–mo22, §4.1, §4.4), `35` (rc66, rc84, open item 12), `36`, `37` (§5, PAT5).

**Local analysis (not in the repo; aggregates only).** An engine-style config loader and card builder over the owner's install (vanilla CWR 3.05, vanilla 1.99, CWE), plus four fact-check probes (cards, stringtable, missions, sizes); all re-run clean on 2026-09-27. Saved channel responses were used for counts only. Scripts and outputs stay in the session scratch area and contain no mod or mission text.

## Verification notes

An adversarial pass on 2026-09-27 re-read every source citation in the local clones and re-fetched every live count.

- **Corrections carried into this doc:**
  - BI's 3.05 notes never name PB as the MODS backend; "MODS storage = papa-bear.cz" rests on the source default and the live catalog.
  - An MP join shows a requirements dialog; it does not download automatically.
  - `vertag` is absent from all 13 live PB records, one record lacks `compatibleActvers`, and two modIds start with `@`.
  - GS has 123 records with 11 KB–19.16 GB sizes (doc 27 said 77 and 155 KB–3 GB).
  - A `mod.json` `modId` is self-asserted.
  - The soldier role precedence is the implemented order, not the summary order first reported.
  - Display-name repeats are one pair per set.
  - `CfgGroups` counts are groups, not slots.
  - "Owned" and "claimed" CWE cards were conflated at first.
  - The Steam Subscriber Agreement licence is not "irrevocable".
  - fractureiser began by 2023-05-20.
  - mod.io's studio share is 20–61%.
  - GlassWorm used Variation Selectors.
- **Removed as unverifiable:** a Steam Workshop search claim (HTTP 429), a ModDB mod-count snippet, and a "Valve will reach out" DMCA quote.
- **Still [I] or [U]:**
  - The `--private` runtime effect.
  - Who operates PB and whether it welcomes third-party clients.
  - Game Schedule's terms.
  - CWE's launcher-generated state.
  - 1.99 parity beyond the corpus.
  - The ModDB terms.
  - One re-check of PB's `/v1/meta/summary` hit a DNS failure; the other reproduced it (13 mods, 10 verified servers).

### Review pass, 2026-09-27: invariants, legal, sibling docs, public rule, user-friendliness

Re-read against AGENTS.md and docs 02, 17, 22, 24, 25, 27, 34, 35 and 37. Spot-checked in the pinned CE clone [V]: `--master-server` and the `--mod`/`--mods-dir`/`--workshop-dir` options (`AppConfig.cpp`), `--private` blanking the master server and the `remaster.cpp` override (`Configuration.cpp`), the PB route table and admin-key gate (`http.rs`), the join-requirements dialog, the skipped hash check, the `mod.json` read, the MODS-screen fetch, the server `modPackages` and newest-compatible-revision selection. All match the cited lines. The 13 saved PB records all have `https:` or absent `homepageUrl`s.

- **Fixed in this pass:**
  - *Route choice (§2.7).* The model no longer picks between "get it", "stand-ins" and "declare": that choice costs the user a download or a compromise, so it is the user's. Unattended runs default to the reversible route. Stand-in intents now feed the remap once X is installed.
  - *Egress accuracy (TL;DR, §3.3, §3.4 manifest).* Per-mod routes send a channel mod id, not only the target version. Feed ids are percent-encoded as one path segment, and the allowlist is checked on the final path, so a hostile id cannot reach `/download`. MAT9 now tests this, and non-`https` links are never opened (doc 22 §3.2).
  - *Hand-off (§3.3).* The rescan runs automatically on root changes or window focus.
  - *Manifest (§2.8).* `kind` clashed with doc 34 mo08's required/recommended `kind`. It is now `shape`, with a separate `need` field. `package_revision` now uses doc 34's `packageRevision`, and a note records that doc 27 §4.5 serializes the manifest as JSON.
  - *Naming (§2.7).* "Retarget to installed set" is now "Remap to an installed set", because doc 37 §5 reserves "Retarget…". The phrase was also attributed to doc 27 §4.11, which says "Pick a mod set that has them".
  - *Legal.* The directory pack now needs the maintainers' non-objection, not a bare notice, with an EU database-right caveat (§4.2, §1.2). O4's "APL-SA forbids paid tiers" was narrowed to what doc 02 supports. The Nexus staff figure is now tagged [V-search]. Author names are allowed only as the channel's author field, which reconciles §4.2 with §6.5.
  - *Network invariant (§5.1).* Registry fetches are neither model-provider nor plugin traffic, so they are now gated as a user-enabled, reviewed source and are part of the design-gap request.
  - *Game-folder addons (§4.1).* Loose third-party PBOs in the game's own addon folders would silently enter "Vanilla". The scan now flags them, and Vanilla-labelled menus exclude them unless the user opts in.
  - *Housekeeping (§3.4, §8.3, header).* `docs/README.md` and `docs/design-gap-requests/` do not exist yet. The gap file follows doc 17's `DGxxx-*.md` pattern. A grep of the code families found no collisions beyond doc 21.
- **Public rule.** A grep for private project names, local paths and personal identifiers found none. Corpus facts are counts plus class, addon and mod names only.
- **Judgement on the recommendation.** "Integrate, never host" plus an offline directory and an opt-in connector is the friendliest option the invariants allow. A connector that is on by default would need network access the user never enabled. A Plotroom market or in-core downloads would add hosting, licence and security burdens for a 13-mod official catalog. The remaining friction is the trip to the game's MODS screen (see the open items below).
- **Still open after this pass:**
  - Whether the editor may offer a user-clicked "Launch the game to install" that reuses Preview's launcher. It would run vanilla and without `--private`, so the MODS screen can reach PB. This is an owner decision [I]. (answered 2026-09-27 → [D038](../decisions/D038-mod-handling-owner-additions.md) item 1.)
  - How the directory stays fresh between releases without a live connector. One option is updating the directory pack through the registry, but that would put third-party metadata into our registry (MG8). (answered 2026-09-27 → [D038](../decisions/D038-mod-handling-owner-additions.md) item 2.)
  - The stock PBO-stem lists per executable that §4.1 needs [U].

### Consolidation pass (2026-09-27)

- **Filing pointers (verification step).** `docs/design-gap-requests/` now exists, so the §8.3 row for that folder and the
  housekeeping note above are done: the T2 feed request with registry traffic (§3.4, §5.1, open question 3) is DG028; outreach to
  the PB and GS maintainers (open questions 1–2) is DG029; the "Still open after this pass" items on launching the game to install
  and on directory freshness, plus open questions 8 (CC-BY-SA-4.0) and 9 (registry operator), are DG030. All are open owner
  decisions, so this doc's text is unchanged. The PBO-stem lists stay [U] and are not a design gap. (All three decided 2026-09-27:
  DG028 → [D008](../decisions/D008-outbound-network-sources.md), DG029 → [D035](../decisions/D035-outreach-and-security-disclosure.md),
  DG030 → [D038](../decisions/D038-mod-handling-owner-additions.md).)
- **Still missing.** `docs/README.md` (the §8.3 index row) does not exist yet, so this doc has no index row; creating it belongs
  to the consolidation pass's docs-index step.
- **Rename check.** This doc has no mention of the concept manual, the live tutorials, doc 33's file or the skill folder.

### Owner answers folded (2026-09-27)

- 2026-09-27: folded by pointer, original words kept: D008 (DG028; the `feed` kind and the registry as a user-enabled source) in
  the TL;DR, §1.2, §3.2 O2, §3.3, §3.4, §5.1, MS3, §8.3 row 22 and OQ3; D035 item 4 (OWQ-12 = DG029 A, the non-objection rule) in
  the TL;DR, §3.3, §3.4, §4.2, MS3 and OQ1–OQ2; D038 (OWQ-17 = DG030) items 1–4 in §3.3, §4.2, §5.2, §5.3, §7.2, MS4, OQ8, OQ9 and
  the review pass's "Still open" items. One contradiction is marked, not deleted: MS2's "Maintainer courtesy notice" is superseded
  by D035 item 4's recorded non-objection. OQ4, OQ9's namespace and third-party-registry parts and OQ10 (`--private`) stay open.
- 2026-09-27 (verifier pass): §1.2's first Product row, which restates the older outbound-network rule, gained the D008 item 1
  pointer that the fold above had missed; its words are kept.
