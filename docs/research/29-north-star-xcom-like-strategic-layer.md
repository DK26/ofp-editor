# North star: an XCOM-like campaign

Research doc 29 for `ofp-editor`. Research date: 2026-09-27. Audience: contributors and LLM coding agents. This file is meant to be read on its own.
Question answered: can a user **describe, generate, refine and ship an XCOM-like campaign** (named soldiers who can die, scarce resources, a
base, a board of competing operations, a doom clock) that plays in real time on the OFP/CWA engine? And what must the campaign designer
provide to make this the product's flagship acceptance scenario?

**Status.** Proposal-only: §3–§8 are design **[I]** unless marked, and every number (cost, duration, cap, threshold) is a placeholder
that the simulator and playtests will tune.
**Epistemic legend.** **[V]** verified by reading pinned source (citation given) or a fetched primary page; **[V-search]** only a search
extract; **[I]** inferred or proposed; **[U]** unknown, needs a probe (§9) or a measurement. Engine facts come from the CWR source (the
Remastered engine); 1.99 parity is **[U]** unless stated (doc 18 caveat). A "wiki tag" is the BI wiki's first-introduction version of a
command (doc 23 §4); it shows availability, not runtime behaviour.
**Code citations.** `CWR:` = `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/`, `EVAL:` = `BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/`,
`CE:` = `ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/`.
**Siblings (semantics unchanged).** Doc 18 (engine campaign mechanics), doc 19 (`CampaignModel`, CXL, compiler, lints C01–C21,
simulator), doc 25 (workflow stages S0–S9), doc 26 (archetypes, patterns P1–P8, persistence modules, lints CF01–CF12), doc 23 §4
(dialects), doc 08 (Preview harness), doc 21 §11.6 (AI play-tester). This doc adds the **strategic tier**: a module kit, a camp design, a
balance lab and an acceptance scenario.
**Glossary.** *Turn*: one commit of the strategic layer; by default one deployment. *Op*: a playable operation mission. *Camp* (hub): the
playable base mission. *Card*: an offered op showing its reward, risk, expiry and "if ignored" consequence. *Commit*: the finisher's
`saveVar` pass (doc 19 §5.5). *Profiles* (doc 19 §4.2): `Cwa199` (legacy 1.99); `Cwr` (Remastered, CWR 3.05, and CWR-CE without
extensions); `CwrCe{…}` (opt-in engine extensions).

## TL;DR

- **Feasible on the engine as shipped** [V by reading CWR; I design]: named roster, permadeath, wounds counted in ops, recruiting, squad
  selection, pooled loadouts, currencies, research, a hangar, expiring offers, a doom clock and a walkable base all map onto vanilla
  commands plus the doc 19 compiler. **Remastered** can host it today; on **1.99** about 20 behaviours stay [U] until the §9 probes pass,
  with degraded fallbacks designed in (radio-menu camp, bucketed briefing lines).
- **Shape: one strategic turn = one deployment.** There is no real-time geoscape. Decisions happen at extraction through the radio menu,
  which costs no extra load. Every 3–4 ops the campaign stops at a playable camp. Pressure counts deployments, not days, as in FTL and Dawn
  of War II [V].
- **The XCOM feeling reduces to seven kernels** (§1): the turn structure, named soldiers you can lose, a looping reward economy, triage
  of competing offers, a visible doom clock, fatigue and wounds that force rotation, and visible memory. Everything else is an optional
  amplifier. Deliberately dropped: turn-based combat, player permadeath, a free-running world clock, base excavation, voiced banter.
- **The central risk is real-time permadeath.** Solomon: "Real-time would never work… if it's permadeath, it has to be turn-based" [V].
  Mitigations: the player is the commander and never dies for good (player death is Retry anyway [V]); code-owned triage turns some
  deaths into grave wounds; free reserves; a player-set casualty cushion; forgiving first ops. Rainbow Six, Ghost Recon and Hidden &
  Dangerous shipped real-time permanent loss [V]. Fairness must be playtested, not asserted.
- **Strategic Layer module kit** (§3). There are 13 typed modules (Roster, Wounds, Recruitment, SquadSelection, Loadout, Resources,
  Unlocks, Hangar, OpsBoard, DoomClock, BaseCamp, Memorial, SideOpGenerator) plus optional Stress, Bonds and Nemesis. Each lowers only to
  doc 19 constructs: flat `saveVar` scalars, finisher lines, presence conditions, generated camp UI and text slots. A fixed ten-step
  **commit pipeline** keeps engine and simulator in agreement.
- **The roster lives entirely in `saveVar`.** A spawn prologue uses `createUnit`, generated `CfgIdentities` and `setIdentity`, so
  campaign-book restarts revert the roster consistently. `objects.sav` is optional and uses versioned keys. Rolls come from a **stored
  LCG seed**, so a restart cannot re-roll a triage result [I].
- **Offers need no routers:** story ops are their own missions; side ops are layers of one per-island template selected by `cmp_op`,
  with consecutive side ops alternating between two classes that share it. The reference campaign has **0 routers**, ≤ 16 book rows [I].
- **The camp is a real mission** (chapter cutscenes lose campaign vars [V]): walkable stations, presence-gated facilities, a memorial and
  a command terminal using the best UI the profile has (`createDialog` on Remastered, 1.99 [U]; else `addAction`; else the radio menu).
- **Balance lab** (§5): 50–500 seeded simulated campaigns under strategic play-tester policies and an editable abstract combat-outcome
  model must show that the pessimistic policy still reaches a finale, ≥ 2 distinct strategies win, and permanent losses happen but
  rarely early.
- **"Make me an XCOM-like campaign"** (§6) runs pattern **P9 Strategic layer** in doc 25's flow: about 30 structural decisions plus
  ~40 one-slot text fills, all Pick or Fill; code owns every number, class, site and wire; a no-model run yields the same valid campaign
  with template text.
- **CWR-CE extensions** (§7) add polish and are never required: E13 strategic intermission screen (a geoscape with no load), E7 per-row
  `objects.sav`, E8 enforced Ironman, E9 routable player death, E10 state-driven book names, E11 numbers in briefings, E12 vars in outros,
  E14 camp row refresh.
- **Acceptance** (§8): "Operation Grey Heron": 12 missions per playthrough (9 deployments + 3 camp visits), 8 named soldiers, 3
  currencies, 6 unlocks, an expiring ops board, a doom clock, and 18 measurable pass criteria (CI on synthetic fixtures; engine runs on
  Remastered through Preview; a probe-gated 1.99 subset).

## 1. The XCOM feeling in a real-time sim

### 1.1 The strategic turn

```text
Op N (real time) ─► extraction: radio menu picks the next card, confirms the squad ─► finisher: 10-step commit ─► Op N+1
        └─ every 3–4 ops, or when "return to camp" is picked ─► Camp (playable: recruit, build, heal, remember, pick) ─► Op
```

Why this shape [V engine, I design]: the engine cannot show a meta-screen between missions, because chapter cutscenes, outros and award
cutscenes run without campaign vars (doc 18 §6.1). Every router or hub costs a `World::CleanUp` + `InitVehicles` and one book row, and a
different island adds a landscape load (doc 18 §8.2). Choices made at extraction are therefore free. The radio menu holds ≤ 10 items and
lists them only when the player leads the group (`CWR:UI/InGame/InGameUIMenu.cpp#L628-L689`); a node has ≤ 6 routable choices plus `lost`
(doc 18 §4).

**A calm decision, not a menu under fire [I].** The board for op N+1 is fixed by the previous commit (step 8), so op N's briefing and
status card already list its cards and the player plans while playing. The radio choice opens once the main objective is done; opening it
shows a `hint` with each card's reward, risk, expiry and if-ignored line, while radio labels carry only a letter, codename and expiry.
Squad picks made here are provisional: step 8 swaps a pick wounded in this op for the recommended fit soldier of the same role, and the
next briefing names the swap. If the op ends with no pick, the finisher takes code's recommended card (Critical first, then soonest to
expire) and the debrief says so.

### 1.2 The seven kernels (the minimal mechanic set)

| # | Kernel | Why it is fun (evidence) | Real-time translation | Modules |
| --- | --- | --- | --- | --- |
| K0 | Turn = deployment; camp every few ops | Solomon's "looping reward system" alternates tense combat with short strategy bursts [V PCGamesN 2017]. FTL: "each warp jump… causes the rebel fleet to advance" [V] | Clocks, wound timers and card expiry count deployments. Choices happen at extraction. The camp is a Relax node (doc 26 §5.3) | BaseCamp, OpsBoard |
| K1 | Named soldiers you can lose | Permadeath "makes you really get attached"; success comes "against real odds" [V PCGamesN] | The commander never dies for good. 8–16 named AI squadmates. Code-owned triage and reserves act as fairness cushions (§3.3) | Roster, Memorial |
| K2 | Looping reward economy | "tense combat which earns you something that you can turn into a new toy" [V] | ≤ 3 currencies plus the native weapon pool. Payouts come from outcomes and from physical acts: crates loaded, a BMP driven home, documents carried out | Resources, Loadout, Hangar |
| K3 | Triage: "you can't save everyone" | EU: an ignored abduction adds +2 panic in the country and +1 on the continent; 8 withdrawals lose the game [V UFOpaedia]. XCOM 2 Guerrilla Ops counter one Dark Event [V] | 2–3 cards per decision, each disclosing its "if ignored" effect. Ignored cards raise regional Pressure or the clock, and the effect surfaces ≤ 2 ops later (CF04) | OpsBoard, DoomClock |
| K4 | Visible strategic clock | XCOM 2's Avatar project "if completed is an automatic loss" and is delayed by sabotage [V]. Battle Brothers' crises show that "the world was changing around you" [V] | An "Enemy Offensive" counter 0..N: +1 per deployment, −1..2 per sabotage op. At max it triggers a playable last stand, never an instant game over | DoomClock |
| K5 | Rotation pressure | WotC fatigue: "You'll develop 12 heroes or more" [V GamesBeat]. Darkest Dungeon makes recovery "a bit of a board game" [V] | Wounded 1–3 ops, gravely wounded 3–5, tired after 2 consecutive ops. Code proposes a fit squad for each card's role needs | Wounds, SquadSelection |
| K6 | Visible memory | A memorial wall with bagpipes [V Kotaku]. The player's stories come from "building the stage and giving the player props" [V Kotaku] | Service records, KIA lines in the debrief, graves in the camp, a roll-call at the finale. The campaign book lists every op [V doc 18 §6.2] | Memorial |

### 1.3 Amplifiers and optional modules

| Amplifier | Translation [I] | Module | Default |
| --- | --- | --- | --- |
| Progression with caps | `setSkill` +0.05 per survived op, capped by rank. Rank rises at xp thresholds (there is no `setRank` [V doc 19 F13]). Perks are *mission capabilities*: FO → "Fire mission" radio item; Scout → pre-marked positions. At the next camp a promoted soldier picks 1 of 2 perks (XCOM's class tree reduced to one stored ordinal; code auto-picks if skipped) | Roster | On |
| Squad select + loadout | The squad is chosen before load, because spawn and presence are decided at load [V doc 19 F12]. Gear comes from the pool in the native briefing screen | SquadSelection, Loadout | On |
| Base facilities | 4–6 presence-gated objects, each changing one rule. None is mandatory (Solomon on EU satellites [V COGconnected]) | Unlocks, BaseCamp | On |
| Research by capture | ≤ 10 projects, started by what the squad brings back: launchers, documents, a prisoner held with `setCaptive`, an intact vehicle | Unlocks | On |
| Story spine + templated side ops | 3–10 authored ops that never expire. Side-op archetypes (doc 26 §9.3) become template layers | SideOpGenerator | On |
| Diegetic time pressure | QRF countdowns, dawn deadlines, extraction windows. Always behind a "Relaxed timers" switch (Solomon's regret [V player.one]) | per archetype | On, switchable |
| Recruitment + replacement floor | 3 candidates per camp visit. At least 1 free low-skill recruit. Nameless reserves fill empty slots | Recruitment | On |
| Stress / morale | Per-soldier stress 0..5, raised by deaths, civilian kills (`Killed` EH) and peak ops. Shaken soldiers rest 1 op; at max, the soldier transfers out | Stress | Off |
| Bonds, nemesis | Text barks (`sideChat`/`titleText`) and +0.05 skill when both partners deploy. A named enemy officer recurs until killed or captured | Bonds, Nemesis | Off |
| Ironman honour | Cannot be enforced on vanilla, because the campaign book allows restarts [V doc 18 §6.2]. It is a preset of cushion, fatigue, timers and clock speed | settings | Off |

### 1.4 What we deliberately drop

| XCOM feature | Why dropped | Replacement |
| --- | --- | --- |
| Turn-based tactical combat | The engine is a real-time sim; that is the point | Real-time ops with diegetic pressure |
| Player-character permadeath | Player death is `EMKilled` → Retry, and SP respawn is hard-wired off [V doc 18 §5] | A commander with plot armour. CE E9 is opt-in |
| Free-running geoscape clock, scanning, interception | There is no meta-screen between missions, and every screen costs a load | Discrete turns, radio choices, the camp every 3–4 ops. CE E13 |
| Several squads in the field | Phoenix Point: "Controlling any more than two [squads] is a nightmare" [V Dread Central] | One squad. The wider war stays abstract: clock, Pressure, background forces |
| Base excavation and adjacency | Management overhead with little real-time payoff | ≤ 6 facilities, one rule each |
| Voiced personalities | Custom speech needs sound assets | Text barks and identity voices only [I] |

### 1.5 Design rules taken from known pitfalls

1. **Fairness before stakes.** Losses the player could not influence feel unfair (Solomon [V]): every permanent loss needs a visible
   cause in the debrief, and the cushion is on by default [I].
2. **Stop the snowball** ("If you're finding the game easy, it gets easier", Tom Francis [V]): skill caps by rank, varying squad size,
   enemies scaled by the clock rather than player success, a replacement floor.
3. **No early death spiral** (EU: "better to restart", Bycer [V]): the first 3 deployments get the most generous triage and free
   replacements [I].
4. **No grind** (Long War "a 20-hour tutorial", Solomon [V]; Dawn of War II "same-y" [V]): 12–25 ops with a spine and a finale; cap
   archetype and site reuse (CF03). OFP load times amplify grind [I].
5. **Low overhead** (Phoenix Point's "cluttered morass" [V-search]): ≤ 3 offers, ≤ 3 currencies, ≤ 6 facilities, one squad; code proposes
   defaults and the player only overrides.
6. **No dominant strategy** (EU: "you focus on satellites" [V]): the simulator must show ≥ 2 winning policies (SL08).
7. **Nothing invisible:** every variable is read by a visible element within ≤ 2 ops (CF04); every card states its "if ignored" effect.
8. **Forced ops pay** (Phoenix Point ambushes served "exclusively to punish you" [V]): every forced or defensive op yields something.
9. **Model the meta layer first** (EU's strategy layer "stagnated", DeAngelis [V]): the typed model exists before missions (doc 19).
10. **Hidden bias only in the player's favour** ("That 85 percent isn't actually 85 percent", Solomon [V]); visible rules never change
    silently [I].
11. **Harsh modules are opt-in presets** (Darkest Dungeon made corpses and heart attacks optional after backlash [V]).

## 2. Feasibility matrix

Cells: **Yes** = registered commands and a mechanism verified by reading source; **Yes·probe** = relies on a §9 probe, with a fallback;
**Partial** = degraded presentation; **—** = nothing needed. "UX cost" counts only extra loads, book rows or screens.

| # | Mechanic | `Cwa199` | Remastered (`Cwr`) | CE extension adds | Mechanism (details §3) | UX cost |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Named roster (name, face, voice, rank, xp, skill) | Yes·probe PR01–PR03 (fallback: slot units) | Yes | E7 revertible identity blobs | Flat `cmp_r_<c>_*` scalars. The prologue calls `createUnit` (its 5-element form sets rank and skill, and its init string runs *before* identity, rank and skill are applied). It then applies `setIdentity` from a campaign-level `CfgIdentities` and `addRating` to restore xp (`CWR:Game/Commands/GameStateExtWorld.cpp#L155-L310`, `CWR:Game/Commands/GameStateExtUi.cpp#L184-L235`, `CWR:Game/Commands/GameStateExtObj.cpp#L444-L466`) | None. The squad appears on the briefing Group page with skill tiers (`CWR:UI/Map/UIMapDisplayBriefing.cpp#L138-L309`). Max 11 + player (`CWR:AI/Path/AITypes.hpp#L31`) |
| 2 | Permadeath + memorial | Yes·probe PR04, PR08 | Yes | E9 embodied player death; E12 roll-call outro | Finisher `alive` checks. KIA scalars. Hidden `OBJ_` lines revealed in the debrief [V doc 19 F10]. Presence-gated graves (empty objects honour `presenceCondition`, `CWR:AI/AICenterImpl.cpp#L1398-L1431`) | None |
| 3 | Wounds and recovery in ops | Yes·probe PR15 | Yes | E7 per-hitpoint wounds | `getDammage` → band → `cmp_r_<c>_out` (ops out), decremented at every commit. `setDammage` at spawn | None |
| 4 | Recruiting | Yes·probe PR01 | Yes | — | A build-time identity pool, so names are known offline and editable. Camp action, dialog or radio. Cost effects | Camp only |
| 5 | Squad selection | Partial until PR05–PR07 (radio paging) | Yes | E13 barracks screen | `setRadioMsg` paging (`CWR:Game/Commands/GameStateExtUi.cpp#L2213-L2268`), `addAction` per soldier, or `createDialog`. Selection flags are committed | The player must lead the group |
| 6 | Loadouts from a shared pool | Yes·probe PR10–PR11 | Yes | — | `weaponPool = 1` at the campaign top level (`CWR:UI/Map/UIMapDisplay.cpp#L468-L539`). The native gear screen. The finisher returns gear and runs `pickWeaponPool` on loot crates; the prologue strips class-default kit | None (native screen) |
| 7 | Currencies | Yes | Yes | E11 exact numbers in the briefing | Bounded `Int`s. `hint format` shows exact values up to 6 significant digits (`%g`, `EVAL:express.cpp#L1977-L1982`). Briefings show buckets | None |
| 8 | Research and unlocks | Yes·probe PR04 | Yes | — | Flags and counters. Pool adds at commit. Presence-gated objects | Camp only |
| 9 | Vehicle hangar | Yes·probe PR04, PR15 | Yes | E7 exact ammo/cargo | Scalar slots. Presence-gated empty vehicles, or `createVehicle` at park markers. A capture zone at extraction (the engine has no vehicle pool [V doc 18 §6.4]) | None |
| 10 | Offers with timers and triage | Yes (coarse) | Yes | E13 geoscape; E1+E3; E10 book names | TTL scalars. A multi-variant template. Marker type and colour set at init (`CWR:Game/Commands/GameStateExt.cpp#L1247-L1250`); dynamic marker text and `createMarker` are not OFP-tagged (doc 23 §4) | 1 load + 1 row per op |
| 11 | Ignored consequences, doom clock | Yes | Yes | — | Expiry effects. Doom as an `Int`. A last-stand socket | None |
| 12 | Base camp hub | Yes (radio UI until PR06–PR07) | Yes | E13 removes the camp load; E14 | A playable mission with stations and a terminal (§4) | +1 world init, +1 row per visit |
| 13 | Save and restart semantics | Partial: the campaign book allows save-scumming; Ironman is only *detectable* (PR19) | Same | E5, E6, E7, E8 | Commit only in the finisher. Stored-LCG rolls. Versioned keys. A debrief-restart guard: that restart re-inits with no campaign vars (`CWR:UI/Map/UIMapDialogs.cpp#L665-L695`), so `cmp_init` detects it, blocks commit and endings, and points to the book; it cannot restore state | — |
| 14 | Info displays | Partial: numbers only via hints and dialogs; briefing buckets; static marker text | Also `setMarkerText` and `createMarker` (`CWR:Game/Commands/GameStateExt.cpp#L1185`, `#L1395`) | E11 | Hint, `hintC`, `OBJ_` lines, radio labels, the Group and Gear pages, dialogs | Low |
| 15 | Procedural side ops | Yes (built at edit time) | Yes | — | Editor generators with recorded seeds. At runtime the game only *chooses* among compiled layers | None at runtime |

## 3. The Strategic Layer module kit

### 3.1 Contract (every module) [I]

- **What a module is.** Data plus a deterministic lowering. Modules are optional, live in the Strategic tier (doc 19 §6.8), and extend
  doc 26's `PersistenceModule`. Doc 26's Roster, Weapon pool, Vehicle pool, Supplies and Doom clock rows become the Roster, Loadout,
  Hangar, Resources and DoomClock modules.
- **State.** A module declares state only as doc 19 `VarDecl`s: flat scalars, bounded `Int`s within ±2^24 (displayed values ≤ 999,999,
  since `%g` prints `1e+06`) and ordinal enums. Roster data never uses arrays, because arrays alias (doc 18 §6.1).
- **Commit, surfaces, probes.** A module adds steps to the fixed commit pipeline (§3.3); it never calls `saveVar` itself and never emits
  END/LOOSE triggers (C13). It declares its **surfaces** (visible reads for CF04/SL04) and the **probes** it depends on (§9); a `Cwa199`
  build carries an "unverified on 1.99" badge until those probes pass.
- **What the model may touch.** Only flavour slots (names, bios, codenames, card blurbs, barks, memorial lines) and picks from computed
  menus. Numbers, classes, sites and wiring are code-owned (doc 26 §1).

### 3.2 Rust type sketches (crate `ofp-campaign-strategic`; proposal-only)

```rust
// Builds on doc 19 (`ofp-campaign-model`: CharacterId, NodeId, VarId, OutcomeId, Guard, Rank, DeathPolicy, IntRange) and doc 26
// (`ofp-campaign-content`: ArchetypeId, FlavorSlotId, SiteRef, Tracked<T>). Newtypes per AGENTS.md: derive Debug, Clone, Copy,
// PartialEq, Eq, PartialOrd, Ord, Hash; #[inline] from_raw/to_raw; Display ("card#2", "fac#1", "turn#7").
// ── Identifiers ─────────────────────────────────────────────────────────
pub struct CardId(u16);    pub struct FacilityId(u8);   pub struct ProjectId(u8); pub struct RegionId(u8);
pub struct ResourceId(u8); pub struct HangarSlotId(u8); pub struct PerkId(u8);    pub struct OfferSlot(u8);
pub struct TurnIndex(u16); /* absolute turn */          pub struct Turns(u8);     /* a duration in turns, never days */
pub struct Skill01(f32);   // validated 0.0..=1.0 by `Skill01::new`; no public from_raw

// ── The layer: one per campaign, stored in CampaignModel next to roster and pools ─
pub struct StrategicLayer {
    clock: TurnClock, preset: DifficultyPreset, rolls: RollSource,
    roster: RosterModule,                                    // required: the layer is pointless without named people
    wounds: Option<WoundsModule>, recruitment: Option<RecruitmentModule>, squad: Option<SquadSelectModule>,
    loadout: Option<LoadoutModule>, resources: Option<ResourcesModule>, unlocks: Option<UnlocksModule>,
    hangar: Option<HangarModule>, board: Option<OpsBoardModule>, doom: Option<DoomClockModule>,
    camp: Option<BaseCampModule>, memorial: Option<MemorialModule>, side_ops: Option<SideOpGeneratorModule>,
    optional: Vec<OptionalModule>,                           // Stress | Bonds | Nemesis (off by default)
}
pub struct TurnClock { hub_every: RangeInclusive<u8> /* 3..=4 deployments */, hub_turn: HubTurnPolicy }
pub enum HubTurnPolicy { NoRestDay, RestDay { doom: i8 } }   // "next day" handled inside the camp, no reload
pub enum DifficultyPreset { Recruit, Veteran, IronmanHonour, Custom(Knobs) }  pub enum CasualtyCushion { Off, Standard, Generous }
pub struct Knobs { cushion: CasualtyCushion, fatigue: FatigueRule, timers: TimerPolicy, doom_speed: u8 }
pub enum TimerPolicy { Diegetic, Relaxed }                   // Relaxed must still yield a completable op (SL16)
/// A saveVar-backed LCG reverts with the history row, so restart-from-row replays the same roll for the same outcome.
/// Engine `random` is allowed only for cosmetic variety (SL11).
pub enum RollSource { StoredLcg { seed: VarId }, CosmeticEngineRandom }

// ── Roster, wounds, recruitment ───────────────────────────────────────
pub struct RosterModule { commander: CommanderPolicy, soldiers: Vec<Tracked<SoldierDecl>> /* 3..=16 */,
                          reserves: ReservePolicy, lowering: RosterLowering, promotion: PromotionTable, triage: TriageTable }
/// `EmbodiedSoldier` compiles only for a CwrCe profile with E9; elsewhere player death stays Retry.
pub enum CommanderPolicy { PlotArmour, EmbodiedSoldier { on_death: OutcomeId } }
pub enum RosterLowering { SpawnPrologue /* A: createUnit + setIdentity */, SlotUnits /* B: pre-placed, per squad slot */ }
pub struct SoldierDecl { id: CharacterId, identity: IdentitySpec /* seeded name/face/glasses/speaker/pitch */,
    role: SquadRole, start_rank: Rank, start_skill: Skill01, background: Background, perks: Vec<PerkId>,
    bio: FlavorSlotId, nickname: Option<FlavorSlotId>, death: DeathPolicy }
/// Runtime ladder. Engine ordinals follow declaration order; payloads live in separate scalars (`_out`, `_kia`, ...).
pub enum SoldierStatus { Fit, Tired { rest: Turns }, Wounded { out: Turns }, GravelyWounded { out: Turns },
                         Shaken { rest: Turns }, Kia { at: NodeId, turn: TurnIndex }, Mia, Transferred, Unrecruited }
pub struct PromotionTable { xp_for_rank: Vec<(Rank, i32)>, skill_step: Skill01, skill_cap: Vec<(Rank, Skill01)> }
pub struct TriageTable { bands: Vec<DamageBand>, rank_save: Vec<(Rank, Percent)>, injury_instead_of_death: InjuryRule }
pub struct DamageBand { above: Damage01, out: RangeInclusive<Turns> }          // e.g. > 0.5 → 2..=3 ops
pub struct WoundsModule { fatigue: FatigueRule, hospital: Option<(FacilityId, Turns)>, walking_wounded: Option<Damage01> }
pub enum FatigueRule { Off, AfterConsecutive { ops: u8, rest: Turns } }
pub struct RecruitmentModule { pool: Vec<Tracked<SoldierDecl>>, candidates_per_visit: u8, cost: Cost,
                               free_floor: u8 /* ≥ 1 */, start_skill: Skill01 }
pub struct Cost(Vec<(ResourceId, u16)>);

// ── Squad, loadout, resources ─────────────────────────────────────────
pub struct SquadSelectModule { size: RangeInclusive<u8> /* ≤ 11 + player */, ui: SelectUi, points: Vec<SelectPoint> }
pub enum SelectUi { RadioPaged, ActionsOnSoldiers, Dialog(DialogRef), Intermission /* CE E13 */ }  pub enum SelectPoint { Extraction, Camp }
pub struct LoadoutModule { baseline: Vec<PoolItem>, kit: KitPolicy, returns: GearReturn, capture_unlock: Option<CaptureUnlock> }
pub enum KitPolicy { StripAndReissueFromRows, EmptyForBriefing }  /* both stop gear minting */  pub enum GearReturn { SurvivorsAndCrates, CratesOnly }
pub struct CaptureUnlock { threshold: u16, magazine_factor: u8 }             // Antistasi rule: 25 weapons, ×3 magazines [V]
pub struct ResourcesModule { currencies: Vec<Currency> /* ≤ 3 (SL03) */ }
pub struct Currency { id: ResourceId, key: Ident, range: IntRange /* ⊆ 0..=999_999 */, start: i32,
                      income: Vec<IncomeRule>, display: Buckets /* briefing lines on 1.99 */ }
pub enum IncomeRule { OnOutcome { outcome: OutcomeId, amount: i32 }, PerItemInZone { item: ItemRef, each: i32 }, PerTurn(i32) }

// ── Unlocks and hangar ────────────────────────────────────────────────
pub struct UnlocksModule { facilities: Vec<Facility> /* ≤ 6 */, projects: Vec<Project> /* ≤ 10 */ }
pub struct Facility { id: FacilityId, cost: Cost, build: Turns, rule: RuleChange, camp_objects: Vec<ObjectRef> }
pub struct Project { id: ProjectId, start: ProjectTrigger, duration: Turns, rule: RuleChange }
pub enum ProjectTrigger { Captured(ItemRef, u16), Documents(u16), Prisoner, VehicleRecovered(ClassRef) }
/// Exactly one visible rule per unlock (SL07).
pub enum RuleChange { WoundTime(i8), ExtraOffer, RevealCards, PoolItem(PoolItem), PoolCap(u16), RecruitSkill(Skill01),
                      Perk(PerkId), RepairPerTurn(u8), SupportAsset(SupportRef) }
pub enum UnlockState { Locked, InProgress { left: Turns }, Done }              // ordinals 0/1/2 + a `_left` scalar
pub struct HangarModule { slots: Vec<HangarSlotId> /* ≤ 4 */, classes: Vec<ClassRef>, show: Materialise,
                          capture_zone: ZoneRef, detail: VehicleDetail }
pub enum Materialise { PresenceSets, SpawnAtMarkers }  pub enum VehicleDetail { Scalars /* dmg, fuel */, StatusBlob /* versioned keys */ }

// ── Ops board, clock, camp, memorial, side ops ────────────────────────
pub struct OpsBoardModule { visible: u8 /* 2..=3 */, cards: Vec<Tracked<CardTemplate>>, lowering: OfferLowering }
pub struct CardTemplate { archetype: ArchetypeId, sites: Vec<SiteRef>, region: RegionId, reward: Vec<(ResourceId, i32)>,
    risk: RiskBand, ttl: RangeInclusive<Turns>, if_ignored: Vec<Consequence>, guard: Guard, kind: CardKind, blurb: FlavorSlotId }
pub enum CardKind { Story { order: u8 } /* never expires */, Side, Critical /* ignoring it advances the clock */ }
pub enum Consequence { Pressure(RegionId, i8), Doom(i8), Resource(ResourceId, i32), CaptureSoldier, LoseFacility(FacilityId) }
pub enum OfferLowering { Direct, VariantTemplate { alternating_classes: u8 }, HubRotation, RouterTree }
pub enum OfferState { Empty, Offered { card: CardId, ttl: Turns }, Taken, Expired }   // per OfferSlot
pub struct DoomClockModule { max: u8, per_turn: i8, sabotage: Vec<(ArchetypeId, i8)>, warn_at: Vec<u8>, at_max: AtMax, regions: Vec<Region> }
pub enum AtMax { LastStand(NodeId), SeasonEnd(NodeId) }  pub struct Region { id: RegionId, pressure: IntRange /* 0..=5 */, per_point: PressureEffect }
pub struct BaseCampModule { hub: NodeId, island: CampIsland, terminal: TerminalUi, stations: Vec<Station>, card: StatusCard }
pub enum CampIsland { SameAsOps, CopyPerIsland }  pub enum TerminalUi { RadioOnly, Actions, Dialog(DialogRef), Intermission /* CE E13 */ }
pub enum Station { OpsTable, Barracks, Quartermaster, Recruiter, MotorPool, Hospital, Workshop, Memorial }
pub struct MemorialModule { record: ServiceRecordFields, kills: KillCredit, surfaces: Vec<MemorialSurface> }
pub enum KillCredit { KilledEventHandler, Off }  pub enum MemorialSurface { DebriefLines, CampGraves, FallenBriefingBlock, FinaleRollCall }
pub struct SideOpGeneratorModule { archetypes: Vec<ArchetypeId> /* 4..=12 */, sites_per_archetype: u8, caps: VarietyCaps, seed: u64 }
```

The crate has one `Error` enum with structured fields, for example `SquadCapExceeded { node: NodeId, requested: u8, cap: u8 }` or
`CurrencyDisplayOverflow { currency: ResourceId, max: i64, display_cap: u32 }`.

### 3.3 The commit pipeline (one strategic turn)

Every op finisher (doc 19 §7.3) runs these steps **in this order**. The simulator runs the same order with engine-faithful `f32`
arithmetic (doc 19 §3, principle 1) [I].

| Step | What | Engine mechanism |
| --- | --- | --- |
| 1 Capture | For each deployed soldier: `alive`, `getDammage`, `rating` (= experience) and `skill`; both return 0 once destroyed, so a triage-saved soldier keeps his last committed xp and skill. Also: loot crates in the extraction zone, vehicles in the capture zone, kill counters | Commands registered in CWR (doc 19 F14). `rating`, `skill`: `CWR:Game/Commands/GameStateExtObj.cpp#L444-L489` [V] |
| 2 Select + effects | The doc 19 first-match edge, then its effects | Doc 19 §5.5 |
| 3 Triage | A dead soldier becomes KIA, unless a stored roll grants "evacuated, gravely wounded" (chance by rank and cushion; EU precedent [V-search]; raised when the squad's medic is alive at the end, lowered when the op is lost, so the player can influence it; the debrief names the reason [I]) or, if enabled, a permanent injury (skill −0.1; Battle Brothers [V]). Survivors are sorted into Wounded or Gravely wounded by damage band | Scalars only |
| 4 Progression | xp → rank by the table. skill += step, capped by rank | Rank is applied at the next spawn (`createUnit` rank argument) |
| 5 Timers | heal−−, tired/shaken rest−−, facility build−−, research++, card TTL−− | — |
| 6 Expiry | Expired cards apply their `if_ignored` consequences; Pressure changes | — |
| 7 Clock | doom += per_turn + ignored criticals − sabotage. At max, force the `AtMax` successor | Socket selection |
| 8 Offers | Refill empty slots from guarded card templates, using a stored roll and the variety caps; then resolve provisional squad picks (an unfit pick → the recommended fit soldier of its role, reserves last) | — |
| 9 Commit | Facts, seed advance, pool deltas (`addWeaponPool`/`addMagazinePool`, `pickWeaponPool`), then one `saveVar` per declared var | Pool changes only at mission end (doc 18 §6.4) |
| 10 Publish | Set `cmpEnd` last | An `exec` script runs ≤ 100 lines per step [V doc 19 F8] |

**Camp turns:** a "next day" runs steps 5–8 in-mission on shadow globals (no reload); leaving the camp runs 9–10. **Stored rolls [I]:**
`cmp_seed = (cmp_seed * 75 + 74) mod 65537`; the largest intermediate value, 4,915,274, is below 2^24, so it is exact in `f32` (doc 19
F2); `mod` is wiki-tagged ofp 1.00 and is `fmod` in CWR (`EVAL:express.cpp#L398`, `#L1105`), exact by reading; on 1.99 it is probe
PR20. Restart-from-row restores the seed (doc 18 §6.2), so replaying the same outcome gives the same triage; Retry never advances it,
because commits happen only at the end. **Anti-duplication [V by reading]:** a weapon swapped out on the briefing Gear page goes into the
pool (`CWR:UI/Map/UIMapDisplayBriefing.cpp#L1093-L1170`), and `fillWeaponsFromPool` first pushes every carried magazine into it
(`CWR:Game/Commands/GameStateExtWorld.cpp#L1227-L1234`), so class-default gear on *any* unit of the player group, the commander included,
mints items. The prologue therefore strips each unit and reissues its kit from the pool (or leaves it empty for the briefing). No engine
path returns carried gear at mission end, and `pickWeaponPool` reads only cargo (`CWR:UI/OptionsUI.cpp#L1500-L1556`), so every finisher,
the camp's included, returns survivors' gear with `addWeaponPool`/`addMagazinePool` over `weapons`/`magazines` (wiki tag ofp 1.75).
SL09's invariant: the pool count is constant across ops without loot.

### 3.4 Roster lowering (the load-bearing piece)

**Lowering A (default; fully revertible).** An `init.sqs` prologue, run before the briefing is built. In CWR, `init.sqs` runs inside
`InitVehicles` after the unit init lines (`CWR:World/WorldInit.cpp#L622-L632`), straight-line up to its first wait (one uncapped
`SimulateScripts` pass, `CWR:UI/DisplayUI.cpp#L121-L129`); the order on 1.99 is [U]. Retry without an autosave re-runs it (PR10).

```sqs
; GENERATED spawn prologue, Lowering A, char#3 "hale". Status Fit = 0. Ordinal tables are generated constants, not campaign vars.
? cmp_r_hale_st != 0 : goto "cmpSkip3"
? cmp_r_hale_sel != 1 : goto "cmpSkip3"
_rk = cmpRankNames select cmp_r_hale_rk
_cls = cmpClassNames select cmp_r_hale_cls
_cls createUnit [getMarkerPos "cmp_sp_3", group player, "cmpU_hale = this", cmp_r_hale_sk, _rk]
cmpU_hale setIdentity "cmpId_hale"
cmpU_hale addRating (cmp_r_hale_xp - (rating cmpU_hale))
cmpU_hale setDammage cmp_r_hale_dmg
; ... strip class-default gear, reissue the saved kit from the pool ...
#cmpSkip3
```

Why it looks like this [V]: `createUnit` runs its init string **before** it loads the next unused `CfgWorlds` identity (sequential, not
random: `CWR:AI/AICenterImpl.cpp#L1447-L1493`), applies rank and skill, and joins the group
(`CWR:Game/Commands/GameStateExtWorld.cpp#L193-L234`), so the identity is applied after the call. The call returns nothing
(`#L309`), so the init string captures the unit in a global. An unknown rank silently becomes PRIVATE (`#L256-L261`) and the engine
spells `LIEUTNANT` (`CWR:AI/AICenter.cpp#L178`), hence SL17. A full group of 12 makes the call a silent no-op (`#L157-L160`), hence
≤ 11 + player (SL02). `setIdentity` searches the mission, then the campaign (`CWR:Game/Commands/GameStateExtUi.cpp#L184-L235`), so each
soldier and recruit gets one `CfgIdentities` class in the **campaign** `description.ext`. It sets only name, face, glasses, speaker and
pitch (`#L218-L231`). `addRating` only adds to experience (`CWR:Game/Commands/GameStateExtObj.cpp#L680-L704`); saved xp is clamped to
≥ 0, because experience below the config `renegadeLimit` makes a unit an enemy of every side (`CWR:AI/VehicleAIDiag.cpp#L1145-L1163`).

**Lowering B (fallback if PR01 fails).** Pre-placed, non-playable **slot units** in the player group, one per squad position (not per
character: the 12-unit cap forbids that), each with `presenceCondition` `cmp_s<k>_c >= 0` [V doc 19 F12; 1.99 U]. Its init line applies
the assigned character's identity and skill inline (init lines run synchronously, before `init.sqs`: `CWR:World/WorldInit.cpp#L622-L627`).
Rank comes from a static `mission.sqm` rank or from `loadIdentity` of a versioned blob (PR03). Presence is evaluated before any
`init.sqs`, so Op1, whose bootstrap runs in `init.sqs`, cannot gate slots on campaign vars and places its squad statically [I].

### 3.5 What each module generates

| Module | Declares (flat `cmp_*` scalars) | Compiler generates | Lints | Probes |
| --- | --- | --- | --- | --- |
| Roster | `r_<c>_st/_rk/_xp/_sk/_dmg/_cls/_sel/_ops/_kills` | `CfgIdentities`; rank and class tables; spawn prologue or slot units; finisher capture, triage and promotion | SL02, SL10, SL12, SL17, C18, CF06 | PR01–PR03, PR14, PR22 |
| Wounds | `r_<c>_out`, `_rest` | Damage bands; decrement at every commit, camp turns included; `setDammage` for walking wounded | SL01 | PR15 |
| Recruitment | `r_<k>_*` for the pool; `nextRecruit` | Seeded identity pool ("unrecruited" in the roster panel); camp recruit UI; affordability guards | SL01 (replacement floor) | PR01 |
| SquadSelection | `r_<c>_sel`, `s<k>_c` | Recommended team per card (role coverage); paged radio, actions or dialog; cap check | SL02, SL15 | PR05–PR07 |
| Loadout | Native pool; optional per-soldier kit rows | `weaponPool = 1`; bootstrap pool fill from a delayed trigger (pool commands are no-ops before the first `AddMission`, doc 18 §6.4); strip and reissue; returns and loot | SL09, SL15 | PR10, PR11 |
| Resources | `supplies`, `intel`, `manpower` | Interval analysis and clamps (doc 19 §5.3); hint status card; bucketed `OBJ_` lines | SL03, SL18 | PR16 |
| Unlocks | `f<k>_st/_left`, `p<k>_st/_left` | Presence-gated camp objects and support assets; pool adds; recruit and card guards; research UI | SL07, SL20 | PR04 |
| Hangar | `h<k>_cls/_st/_dmg/_fuel` | Presence sets or park-marker spawns; capture trigger; crew check | SL19 (never on the critical path) | PR04, PR15 |
| OpsBoard | `o<k>_card/_ttl`, `pr_<region>` | Card generator; radio labels at extraction; camp ops table; markers hidden with `setMarkerType "Empty"` and coloured by urgency; socket allocation; budget meter | SL05, SL13, SL14, CF03, CF04 | PR05, PR09, PR13, PR17 |
| DoomClock | `doom` | Warnings; an `AtMax` socket in every finisher that can raise doom; clock marker; an `OBJ_` bucket line from turn 1 | SL04, SL06, CF07 | — |
| BaseCamp | `camp_day` | Camp mission from one design (a copy per island if chosen); stations; terminal; status card; camp finisher | SL13, SL14, SL15 | PR06–PR09, PR13, PR23 |
| Memorial | `r_<c>_kia/_kiaturn/_kills/_medals` | Hidden `OBJ_kia_*` debrief lines; presence-gated graves with a "Read inscription" action; "Fallen" block; finale roll-call | C18, C21 | PR04, PR08, PR21 |
| SideOpGenerator | `op` (selected layer) | Variant layers: presence-gated groups; triggers guarded by `cmp_op == k` (sensors are created unconditionally, `CWR:AI/AICenterImpl.cpp#L1432-L1438`); hidden markers; per-layer `OBJ_` briefing block | CF03, CF09, SL11 | PR17, PR18 |

### 3.6 Strategic-layer lints (proposed; complement C01–C21 and CF01–CF12) [I]

| ID | Sev. | Rule |
| --- | --- | --- |
| SL01 | error | Under the pessimistic policy, an op needs more fit soldiers plus reserves than exist (roster death spiral; a special case of CF07) |
| SL02 | error | The deployed squad is > 11, or the player group would exceed 12 (a silent `createUnit` no-op) |
| SL03 | warn | More than 3 currencies, 6 facilities, 10 projects or 3 visible cards (management overhead) |
| SL04 | error | A strategic variable (doom, a currency, Pressure, a soldier status) is not surfaced on turn 1, or not within 2 turns of a change |
| SL05 | error | A card lacks an "if ignored" disclosure, or its consequence never surfaces within 2 turns on some path |
| SL06 | error | Doom is below max on some path, but no doom-reducing card is reachable before max |
| SL07 | warn | An unlock changes no visible rule, or one unlock is built in > 90 % of winning simulator runs (it is effectively mandatory) |
| SL08 | warn | Fewer than 2 distinct policies win ≥ 30 % of their runs (a dominant strategy) |
| SL09 | error | A player-group unit (roster or commander) reaches the briefing with class-default gear while `weaponPool = 1` (duplication), or a finisher does not return survivors' gear (loss) |
| SL10 | error | Roster data sits in `objects.sav` without versioned keys and a run nonce (doc 18 §8.4) |
| SL11 | error | Engine `random` or a `presence` probability drives state that is committed or read by a guard |
| SL12 | warn | Expected permanent losses in the first 3 deployments (Standard policy) exceed the preset's target |
| SL13 | warn | More than 4 deployments without a camp visit, camps back to back, or a camp on a different island from its ops |
| SL14 | info | Over budget: too many book rows, world inits or landscape loads per playthrough |
| SL15 | error | The player does not lead the group where a radio choice or gear selection is needed (both are leader-only: `CWR:UI/InGame/InGameUIMenu.cpp#L628`, `CWR:UI/Map/UIMapDialogs.cpp#L355`) |
| SL16 | warn | A timed pressure mechanic ignores the "Relaxed timers" setting |
| SL17 | error | A rank string outside `PRIVATE`..`COLONEL` (unknown ranks silently become PRIVATE; `UNDEFINED` is accepted), or a restorable xp < 0 (renegade risk, §3.4) |
| SL18 | warn | A displayed number can exceed 999,999 (`%g` exponent form) |
| SL19 | error | A CE-only mechanic in a `Cwa199` or `Cwr` build without its fallback, or a hangar vehicle required on the critical path |
| SL20 | warn | A research project that completes after the last op, or unlocks nothing reachable |

## 4. The base camp hub mission

### 4.1 Layout

| Station | Physical form | Interaction | Changes |
| --- | --- | --- | --- |
| Ops table | Map table + officer NPC | Action "Operations…" → card list; map markers coloured by urgency; optional `onMapSingleClick` (PR09) | Next op, squad |
| Barracks | Selected, fit soldiers standing (presence-gated) | Per-soldier "Take along" / "Leave behind" via `addAction`, shown within 10 m in front of the player (`CWR:AI/VehicleAIPilot.cpp#L1279-L1298`) | `_sel` flags |
| Quartermaster | Crate + NPC | Pool summary via `hint`; the camp briefing's Gear page | Pool view |
| Recruiter | NPC + 3 presence-gated candidates | "Recruit (cost)" actions with affordability guards | Roster, currencies |
| Workshop | Tent with captured items on display | Start or inspect research projects | Unlocks |
| Motor pool, hospital, radio mast, training ground | Presence-gated objects that appear once built | Info actions | One rule each |
| Memorial | A presence-gated grave or board per KIA | "Read inscription" → `hint format` with name, op and turn | Memory |
| Command terminal | An action on the **player**, whose own actions always show [V] | Opens the best terminal UI for the profile (§4.2) | Everything above, in one screen |

**Walking is flavour, never a chore [I].** The player spawns at the Ops table with the terminal and "Leave camp" one action away. The
barracks opens with code's recommended squad for the chosen card already selected, so per-soldier actions only override it. The first
visit adds a skippable hint per station. A visit with nothing to change should take under a minute plus the load (AC16).

### 4.2 Terminal UI per profile

| Profile / probe state | Ops board and squad | Recruit, build, research | Status |
| --- | --- | --- | --- |
| `Cwa199` before probes | Radio `ALPHA..JULIET` with labels via `setRadioMsg format [...]`; one channel pages "More…"; activated non-repeating triggers drop out [V doc 19 F11] | Radio items | `hint` status card; bucketed `OBJ_` lines; marker colours |
| `Cwa199` after PR06–PR07 | Actions + a `createDialog` terminal (wiki tag 1.75) | Dialog | Adds dialog text and lists |
| Remastered (`Cwr`) | `createDialog` terminal. The class is defined once in the campaign `description.ext`; lookup order is mission → campaign → global (`CWR:Game/Commands/GameStateExtWorldDialog.cpp#L24-L49`, `#L136-L166`) | Dialog | Adds `setMarkerText` labels |
| `CwrCe` + E13 | Intermission screen between missions (no camp load), same dialog class | Same | Same |

The radio variant is always generated as the **floor**, so a failed probe degrades the UX but never blocks the campaign [I].

### 4.3 Status surfaces and cost

- **Status card.** A `hint format` (wiki tag 1.00) in the first seconds of each op and camp visit shows exact currencies, "Offensive 5/8",
  Fit and Wounded counts, expiring cards and, in ops, a roll-call such as "3 Pte. Hale (AT)". The group bar labels units by number only
  (`CWR:UI/InGame/InGameUIDraw.cpp#L1697-L1750`, `CWR:UI/InGame/InGameUIGroupUnitLabel.hpp#L18-L28`) [V], so names must reach the player as text: the roll-call, the Group page, and a
  `titleText` "Pte. Hale (3) is down" from the `killed` handler (PR21) [I].
- **Camp briefing.** The Plan shows state as `OBJ_` lines: number buckets, a "Fallen" block and card summaries [V doc 19 F9]. The Group
  page is a live roster with rank, name and skill tier [V]. The Gear page shows the armory.
- **Op briefings and debriefs.** Op briefings carry card facts, the risk band and the squad. Debriefs reveal KIA, wound and promotion lines
  [V doc 19 F10]. Exact numbers appear only in hints and dialogs, unless E11 is available.
- **Cost model.** Each transition costs one world init and one book row, plus a landscape load only when the island changes (doc 18
  §8.2): about `d + ⌈d / c⌉` rows and inits for `d` deployments with a camp every `c` ops (12 for `d = 9, c = 3`).
- **Rules [I].** Decide at extraction between camps (free). Keep the camp on its ops' island (`CopyPerIsland` generates identical camps
  from one design). No routers per turn (variant templates and alternating classes, §3.5). Never self-loop the camp for "next day": a
  consecutive same-name row is skipped (`CWR:UI/OptionsUI.cpp#L1122-L1127`), so its snapshot is never refreshed and a restart would
  rewind every camp turn; rest days run in-mission. The SL14 meter shows rows, inits and landscape loads per path, live. A camp must earn
  its load: when it falls due at the low end of `hub_every` but would offer no decision (nothing affordable to recruit, build or research,
  no promotion pick, no new fallen), the finisher defers it to the high end; "Return to camp" stays on every extraction menu.
- **Camp build keys.** `debriefing = 0` (which also removes the debriefing Restart that drops vars, doc 18 §6.1), empty
  `Intro`/`OutroWin`/`OutroLoose`, `noAward = 1`, `lives = -1`. **Real load times are [U]:** measure per island in Preview (PR23) before
  tuning the cadence.

## 5. Editor UX for designing it

### 5.1 The War Room (Strategic-tier views; retro chrome per doc 19 §6.7)

- **Roster table:** a spreadsheet of soldiers and recruits (identity preview, role, class from a catalog menu, rank, skill, perks,
  background, bio, death policy, simulated survival). Every flavour cell has a provenance chip (code seed / model and slot / human) and a
  pin; row actions regenerate a bio, swap a class or "kill in simulator".
- **Economy sheet:** currencies, income per outcome, costs and upkeep, each with p10/p50/p90 bands from the balance lab.
- **Ops-board designer:** card templates drawn as OFP-styled cards (region, archetype, reward, risk, TTL, if-ignored effect); the Theatre
  view (doc 19 §6.7) with a Pressure heat map; a lowering selector (Direct / VariantTemplate / HubRotation / RouterTree) beside the socket
  and budget meter.
- **Camp designer:** the camp opens in the normal mission editor with stations as typed objects; facilities and projects form a small
  tree, each node showing its one rule change. **Clock designer:** the doom curve per policy, with sabotage and ignored-critical effects.
- **Turn journal:** a campaign-book-styled log of one simulated run ("Turn 4: Pte. Hale gravely wounded at the depot raid; out 3 ops"),
  a designer aid ("war story"), never runtime state.

### 5.2 Balance lab (simulator and Path Explorer, doc 19 §6.4)

- **Combat-outcome model [I].** The simulator cannot play real-time combat. Instead, each archetype has an editable table that maps
  difficulty band × squad power (size, skill, role coverage, pooled AT/MG) to distributions over outcomes, per-soldier casualties, damage
  bands and loot. Code ships defaults for each archetype (doc 26 §9.3). How to calibrate them is open question 1.
- **Policies** (strategic play-testers that choose cards, squads, builds and recruits): Cautious, Greedy, Reckless, Random, Pessimistic
  (always the worst outcome), and Builder-A / Builder-B, two opposed build orders used by SL08. Narrated personas (doc 21 §11.6) are
  optional and sampled.
- **Runs:** 50 seeded runs by default, 500 for acceptance. Outputs: a chorus line of endings (doc 26 §8.2), per-soldier survival curves,
  currency bands, clock-reach rate, winning build orders, early-loss rate and book rows per path.
- **Auto-tune and gates [I].** Code (never the model) searches knob values (incomes, costs, TTLs, clock speed, triage chances) toward
  target bands, e.g. a 40–75 % Standard win rate, and shows the result as a diff to accept. Human-set or pinned numbers are constraints,
  never search variables (doc 25 §3 principle 6); if a band is unreachable without them, the lab names the blocking knob instead of
  moving it. SL01, SL06, SL08, SL12 and CF07/CF08 gate;
  entertaining commentary ("Command notes: the men are tired") comes from the same data and never gates (doc 26 §8.2).

### 5.3 Glass box and testing

- **Provenance.** Every generated element carries its origin (`Tracked<T>`, doc 26 §9.1) and opens an inspector: why it exists (module →
  rule → model element), which step and model produced it, what depends on it, and its lint and simulator status. The **Compiled**
  overlay source-maps every generated line (`CfgIdentities`, dialogs, prologues, finishers, presence conditions): clicking a grave's
  `presenceCondition` jumps to Memorial → soldier → KIA rule.
- **Testing.** "Start at turn N with state S" builds a debug campaign (doc 19 §6.4). On Remastered, each op runs as a `--test-mission`
  with a state-injected prologue, and harness `eval` reads the committed vars back for engine-versus-simulator comparison (doc 08 §2.4–§2.5)
  [I]. Launching a whole campaign from the CLI is open question 2. Outside a campaign there is no history row, so pool commands are no-ops
  (`CWR:UI/OptionsUI.cpp#L1397-L1407`) [V], and campaign-level `CfgIdentities` and dialog classes resolve only when a campaign
  `description.ext` is loaded (`CWR:UI/OptionsUI.cpp#L777-L794`); test builds inline those classes [I], and pool checks need a real chain.

## 6. Campaign-from-brief: "make me an XCOM-like campaign"

### 6.1 Intake and pattern

At S0, spans such as "XCOM-like", "squad that can die", "base", "choose missions" or "enemy offensive" raise a **P9 Strategic layer**
suggestion card. This is a code rule over quoted spans (doc 25 §4.3), not a model judgment.

Wishes the engine cannot meet get alternatives: "my character can die permanently" → commander plot armour, or E9 behind a CE-only
badge; "real-time world map" → turns per deployment, or E13; "voiced soldiers" → text barks. P9 combines P4 (hub + loop and grow), P8
(countdown offensive) and P6 (side-op pool) around a story spine of 3–5 ops (doc 26 §9.4).

| P9 parameter (chip; default) | Range | Owner |
| --- | --- | --- |
| Deployments per playthrough | 8–25 (9) | User; code checks the budget |
| Named soldiers / recruit pool | 6–16 / 0–12 (8 / 6) | User |
| Currencies | 1–3 (Supplies, Intel, Manpower) | User picks from a list; code owns the numbers |
| Facilities / projects | 0–6 / 0–10 (4 / 2) | User picks; code owns the costs |
| Visible cards; TTL | 2–3; 1–3 turns | Code |
| Camp cadence | every 3–4 deployments | Code (SL13) |
| Preset | Recruit / Veteran / Ironman honour | User |
| Optional modules | Stress, Bonds, Nemesis (off) | User |

### 6.2 Stages and model shapes (doc 25 §4.1; weak default shapes)

| Stage | Model decisions (shape) | ≈ count | Code owns |
| --- | --- | --- | --- |
| S0 Describe | Fill intake with quotes | 1 | Quote checks; the P9 suggestion; defaults as chips |
| S1 Premise | 3 premise cards (Fill); the user picks | 3 | Archetype menus by side and era |
| S2 Bible | Bio ≤ 25 words, nickname pick and speech style per soldier (Fill ×8); faction and nemesis names (Pick from era lists) | 10 | Identities (seeded names, faces, voices), classes, ranks, perks, backgrounds. The user may type names (friends', say); typed names are Human and pinned, and the model then writes bios around them |
| S3 Outline | Spine beats (Pick ≤ 5 each) | 4 | P9 skeleton, sockets, lowering, camp cadence |
| S4 Schema | Modules and preset (Pick) | 2 | Every var and rule, and **every number** (economy preset + auto-tune) |
| S5 Missions | Per story op: archetype and site (Pick ≤ 5); the side-op archetype set (Pick) | 8 | Feasibility, variety caps, variant layers |
| S6 Build | none | 0 | Generators, sockets, prologues, camp |
| S7 Text | Card blurbs, codenames, facility names, memorial lines, barks (Fill; one slot per call) | ~40 slots | Slot specs, fact scopes, C18/C21 coverage |
| S8 Verify | none | 0 | Lints, simulator gates, compile |
| S9 Refine | Request → typed `RefineRequest` (Fill) | per request | Scope, merge, no clobbering (doc 25 §9) |

The model never decides anything that could break the engine or the balance (every number, TTL, cost, class, site, variable, guard and
socket). Its text is checked against code-owned facts (named soldiers alive on the path, C18; the era forbid list) and shown to the user
before commit. A no-model run takes the same path with template text (AC02). Refines are single undoable transactions: "make the depot
raid a night op" → retemplate + Night; "add a nemesis officer" → enable Nemesis, presence across 3 ops, a capture/kill outcome; "fewer
resources" → drop Manpower and re-tune; "make it harder" → Veteran preset and auto-tune to the new band.

## 7. Proposed CWR-CE extensions (opt-in `CwrCe` profile)

Numbering continues doc 18 §9 (E1–E6); doc 25's E1–E11 are evaluation instruments, a separate series. CE's campaign code matches CWR at
the pinned SHAs (doc 18 §9), so the hooks cite CWR lines; CE's `NextMission` is at `CE:UI/OptionsUI.cpp#L1900`. Every extension keeps
vanilla behaviour when its key is absent, and `Cwa199`/`Cwr` output never depends on one (SL19).

| ID | Extension | Benefit | Hook points (pinned) | Fallback | Priority [I] |
| --- | --- | --- | --- | --- | --- |
| E13 | **Strategic intermission display**: a finished mission class with `strategicDisplay = "<Rsc>"` opens that dialog before `NextMission` | A real geoscape and barracks with no camp load and no book row. It reuses the camp's campaign-level dialog class | Open at `CWR:UI/OptionsUIApp.cpp#L1039-L1048`. Resources as in `CWR:Game/Commands/GameStateExtWorldDialog.cpp#L129-L166`. Vars via the `VarSet` loop at `CWR:UI/OptionsUIApp.cpp#L883-L892`. Commit into `CWR:AI/AICenterStats.cpp#L69-L80`. Pass the code to `CWR:UI/OptionsUI.cpp#L1894-L2022`. Running SQS without a simulating world needs a design check [I] | Camp mission | High |
| E7 | Per-row `objects.sav` snapshot | Identity and status blobs (per-hitpoint wounds, vehicle ammo and cargo) revert with the row. No versioned keys, no file growth | Copy at `CWR:UI/OptionsUI.cpp#L1693-L1712`, or embed in `CWR:UI/OptionsUICommon.hpp#L61-L105`. Restore at `CWR:UI/OptionsUIApp.cpp#L458-L501` and `#L525-L527`. Path at `CWR:Game/Commands/GameStateExtWorld.cpp#L837` | Scalars + versioned keys | High |
| E8 | Ironman (`ironman = 1`) | True stakes: the book offers only Continue and New, and debrief Restart is disabled | `CWR:UI/OptionsUIImpl.cpp#L1034-L1234`. Reject row restart and replay in `CWR:UI/OptionsUIApp.cpp#L458-L553`; refuse the debriefing Restart at `CWR:UI/Map/UIMapDialogs.cpp#L665-L676`, which already refuses when `lives == 0` | Detect-only ledger (PR19) | Medium |
| E9 | Routable player death (`killedEnd = "lost"` or `"endN"`) | "KIA: command passes to Sgt X" → camp with a memorial | `CWR:UI/DisplayUIMenus.cpp#L966-L981`; `CWR:World/WorldImpl.cpp#L541-L657`. `CWR:UI/OptionsUI.cpp#L1925-L1948` has no `EMKilled` case | Retry | Medium; CE-only badge |
| E10 | State-driven book row name (e.g. `cmp_bookName`) | "Op HAMMER (turn 12)" instead of the shared template name | `CWR:UI/DisplayUIMenus.cpp#L812-L821` and `CWR:UI/OptionsUIApp.cpp#L863-L871`. Stored at `CWR:UI/OptionsUI.cpp#L1104-L1136` | `briefingName` | Medium |
| E11 | Variable substitution in briefing and debriefing HTML | Exact numbers in the notebook | `CWR:UI/Map/UIMapDisplay.cpp#L614`; `CWR:UI/Map/UIMapDialogs.cpp#L910`. `Evaluate` is already used at `CWR:UI/Map/UIMapDisplayBriefing.cpp#L468-L470` | Bucketed `OBJ_` lines | Medium |
| E12 | Campaign vars in outros, awards and chapter cutscenes | State-aware roll-call and epilogues | Add the `VarSet` loop (`CWR:UI/OptionsUIApp.cpp#L883-L892`) to `CWR:UI/DisplayUIMenus.cpp#L1331-L1450` | Cutscene nodes / finale debrief | Low |
| E14 | Refresh the row snapshot on a camp self-loop | Restart returns to the latest camp day | `CWR:UI/OptionsUI.cpp#L1122-L1127` | In-mission rest days | Low |
| E1+E3 | (doc 18) Declarative router fast-path; hidden rows | Fan-out > 7 with no router load or row | Doc 18 §9 | Router missions | Low (P9 needs none) |
| E5, E6 | (doc 18) Re-inject vars on debrief Restart; reset `objects.sav` on Begin | Robustness | Doc 18 §9 | Guards; nonce keys | High (upstream early) |

## 8. The acceptance scenario: "Operation Grey Heron"

### 8.1 The brief (fixed test input)

> Make me an XCOM-like campaign. I command a resistance company on one island in 1985. Eight named fighters who can die for good,
> scarce supplies, a hidden camp we can build up, several missions to choose from that expire, and an enemy offensive coming.
> About ten missions, tense but fair.

### 8.2 Reference specification (what a correct result contains) [I]

One island (the local reference build uses any stock island; CI uses the synthetic test island and catalog, per AGENTS.md fixture
rules). The player is the commander with plot armour (death = Retry); the enemy is an occupying force resolved by role from the catalog.
One engine chapter, 0 routers:

| Class | Folder | Role | Sockets → successor |
| --- | --- | --- | --- |
| `Op1` | own | Story opener: forgiving, teaches extraction choices; the bootstrap runs in its prologue | end1 → `Camp` |
| `Camp` | own | BaseCamp | SideA, Story2, Story3, Story4, LastStand, Finale (6 sockets; `lost` unused) |
| `SideA`, `SideB` | **Shared** side-op template with 8 variant layers: Raid, Ambush, Sabotage, Recon, Rescue, Convoy interdiction, plus alternate sites for 2 of them | Side ops; the two classes alternate | Camp, the other side class, Story2, Story3, Story4, LastStand; `lost` → Camp (failure-forward) |
| `Story2`, `Story3` | own | Story spine; never expire | Camp, SideA, the next story op, LastStand; `lost` → Camp |
| `Story4` | own | Pre-finale; opens the finale card | Finale, Camp, LastStand (the clock's `AtMax` socket, §3.5); `lost` → LastStand |
| `LastStand` | own | Forced when the clock maxes out; pays out survivors and pool | Finale (harder variant); `lost` → Defeat ending |
| `Finale` | own | Finale | Victory, Pyrrhic victory; `lost` → Defeat |

A typical playthrough: Op1 → Camp → SideA → SideB → Story2 → Camp → SideA → Story3 → SideA → Camp → Story4 → Finale (story ops and
the camp route only to `SideA`; `SideB` exists only to follow `SideA`). That is 12 missions and 12 rows, 9 of them deployments, with 0
landscape loads after the first. Both side classes give every socket the same meaning (end2 = "the other side class"), because the shared
finisher cannot learn its own class: `missionName` returns the file name (`CWR:Game/Commands/GameStateExtWorldConfig.cpp#L854-L860`) [V]. It assumes at least one successful Sabotage: at
+1 per deployment the clock otherwise reaches 8 after Story4 and LastStand comes before the Finale, which is the intended pressure.

| Element | Specification (placeholders; code-owned) |
| --- | --- |
| Roster | 8 named soldiers: Sergeant, 2 Riflemen, MG, AT, Medic, Marksman, Saboteur. A recruit pool of 6 seeded identities. Nameless reserves fill empty slots. Perks: Marksman (scoped rifle in the pool), Saboteur (charges), Medic (class-native) |
| Wounds, fatigue | Damage > 0.25 → out 1 op; > 0.5 → out 2–3 ops; gravely wounded → out 3–5. Tired after 2 consecutive ops; rest 1 |
| Currencies | Supplies 0..9999 (start 120); Intel 0..99 (start 0); Manpower 0..30 (start 4) |
| Unlocks (6) | Facilities: Field Hospital (wounds −1 op); Motor Pool (deploy 1 hangar vehicle, repair 1 per turn); Radio Mast (+1 card; every card always shows reward, risk, expiry and if-ignored effect); Training Ground (recruits +0.1 skill). Projects: Captured AT (bring back N launchers → AT in the pool for good); Mortar Observer (Intel ≥ 10 → "Fire mission" radio item) |
| Hangar | 2 slots, filled only by capture at extraction |
| Ops board | 2 cards per decision (3 with the Radio Mast); side TTL 1–3. 3 regions with Pressure 0..5: +1 per ignored card in the region, −1 per successful op there (a reason to go where it burns; EU's successful abduction missions cut that country's panic by 3 [V UFOpaedia]), and each point adds a presence-gated patrol to that region's ops |
| Doom clock | "Enemy Offensive" 0..8: +1 per deployment, +1 per ignored Critical card, −2 per successful Sabotage. At 8 → LastStand. Shown from turn 1 |
| Memorial | Debrief KIA lines, camp graves, a "Fallen" block, a finale roll-call (hidden `OBJ_` lines) |
| Presets | Recruit / Veteran / Ironman honour; a Relaxed timers toggle |

### 8.3 Pass criteria

CI covers AC01–AC13 and AC18 on synthetic fixtures. AC14–AC17 are opt-in local engine runs, gated by an environment variable (AGENTS.md).

| ID | Criterion | Measure |
| --- | --- | --- |
| AC01 | Intake | P9 is selected by rule. At T1, ≥ 8 of 10 intake fields are filled with verified quotes, and ≤ 3 questions come before the first visible artifact (doc 26 §8.2) |
| AC02 | Model independence | The no-model run and the T1, T2 and T3 runs all pass AC03–AC13. They differ only in menu picks and flavour text |
| AC03 | Structure and budget | 8 folders, 9 classes, 0 routers, 1 chapter. Every simulated playthrough has 10–14 missions, ≤ 16 rows, and 0 landscape reloads after the first mission |
| AC04 | Lint-clean | 0 errors in C01–C21, CF01–CF12 and SL01–SL20 for both the `Cwr` and `Cwa199` builds. Every warning is listed with a rationale |
| AC05 | Totality | Path Explorer reaches Victory, Pyrrhic and Defeat with witness paths. No (node, trigger, state) is uncovered (C03) |
| AC06 | Robustness | 500 seeded runs for each §5.2 policy: 100 % reach an Ending. The Pessimistic policy reaches LastStand or Finale with a deployable team of ≥ 4 at every op |
| AC07 | Stakes exist | Under the Standard policy and cushion, ≥ 1 permanent loss in ≥ 60 % of runs; median permanent losses 1–4 |
| AC08 | Early fairness | A permanent loss within the first 3 deployments happens in ≤ 10 % of Standard runs |
| AC09 | No dominant strategy | Builder-A and Builder-B each win ≥ 30 % of their runs. No unlock is built in > 90 % of winning runs. The Standard win rate is 40–75 % |
| AC10 | Visibility | Doom and all 3 currencies are surfaced on turn 1. Every strategic var is surfaced within ≤ 2 turns on every path. Every card discloses its if-ignored effect |
| AC11 | Triage works | For each card template, some explored path ignores it, and its consequence surfaces within ≤ 2 turns |
| AC12 | Glass box | 100 % of generated lines are source-mapped. Every soldier, card, facility and project opens an inspector with its provenance |
| AC13 | Safe refines | The four §6.2 refines, plus "rename Hale and rewrite his bio", change only their scope. Clobbered human or pinned fields = 0 (doc 25 E9) |
| AC14 | Engine agreement (Remastered) | Every mission is started via `--test-mission` with ≥ 3 injected states and driven to every socket with 0 script errors (AutoTest aborts on errors [V doc 08]). Vars read back over the harness equal the simulator's commit for the same inputs |
| AC15 | Roster round-trip (Remastered) | In a scripted 3-op chain, names, faces, ranks, xp, skill, wounds and KIA persist and show on the Group page. Restart-from-row stays consistent. The pool count is invariant without loot (a real campaign chain: pool commands are no-ops in `--test-mission`, §5.3) |
| AC16 | Fun (human panel) [I] | ≥ 5 players play ≥ 4 ops including a camp visit. ≥ 4 of 5 name a soldier unprompted; the median "one more op" rating is ≥ 4/5; nobody reports a loss as unfair without a visible cause in the debrief; ≤ 1 of 5 calls the camp or the extraction choice a chore, and the median camp visit is ≤ 3 min excluding the load. This gates the "north star achieved" claim, not CI |
| AC17 | 1.99 | The `Cwa199` build (radio-menu camp) passes AC03–AC13. It is labelled "verified on 1.99" only after PR01–PR18 and PR20 (PR21 if kill credit is on) pass on a 1.99 install and a manual 3-op run confirms AC15 |
| AC18 | Time to play | The War Room shows a simulated turn journal of the chosen skeleton before any mission is built. `Op1` and the `Camp` (with injected state) are Preview-ready ≤ 5 min after S0, so the first play covers the strategic loop, not only a firefight. The full draft takes ≤ 30 min on a T1 local model at Standard effort [U hardware] |

### 8.4 Which parts run where

| Scenario part | Remastered | 1.99 once probes pass | 1.99 if a probe fails |
| --- | --- | --- | --- |
| Roster spawn, identities, promotion | Yes | Yes (PR01–PR03, PR14) | Lowering B slots |
| Camp terminal | Dialog | Dialog (PR07) | Radio menu, plus actions if PR06 passes |
| Ops-map markers | Dynamic text and colour | Static text, dynamic colour (PR09) | Static markers |
| Graves, facilities, hangar presence | Yes | Yes (PR04) | `deleteVehicle` pruning in init, after load |
| Numbers | Hint and dialog | Hint and dialog | Hint only |
| Ironman | Book restart allowed | Same | Same (needs E8) |

## 9. 1.99 probe list

All probes run as a local-only probe-mission suite on a legal 1.99 install (doc 19 Open question 1). Most also run on Remastered through
Preview (doc 08) to confirm our reading of the source.

| ID | Probe | Gates |
| --- | --- | --- |
| PR01 | `createUnit` 5-element form (wiki tag ofp 1.34): are rank and skill applied; does the init-string global capture work; does the unit appear on the briefing Group page and gear screen when created in `init.sqs`; is `LIEUTNANT` the spelling | Roster A, Recruitment |
| PR02 | `setIdentity`, after `createUnit` or on a pre-placed unit, keeps name, face and voice for the whole mission and leaves rank, xp and skill alone | Roster |
| PR03 | `saveIdentity`/`loadIdentity`/`saveStatus`/`loadStatus`: return values, `objects.sav` location, whether rank/xp/skill are restored, use in unit init and `init.sqs` | Roster B, Hangar detail |
| PR04 | `presenceCondition` reads `saveVar`-injected globals, both for non-playable units and for empty vehicles and objects | Roster B, Unlocks, Memorial, Hangar, variant layers |
| PR05 | `setRadioMsg` with `format` labels and `"NULL"` hiding; repeating radio triggers as a paged menu; leader-only listing | SquadSelection, extraction choices |
| PR06 | `addAction [title, script]` on the player and on NPCs: contents of `_this`, the 10 m range, how `removeAction` ids behave | Camp stations |
| PR07 | `createDialog` with a campaign-level class, opened from an action or a trigger; `lbAdd`/`lbSetValue`/`lbCurSel`/`buttonSetAction`/`ctrlSetText`/`lbSetPicture`; Esc; whether SP simulation continues | Terminal |
| PR08 | `objStatus "HIDDEN"` in `init.sqs` before the briefing; `OBJ_` lines revealed by the finisher show on the debriefing pane | Displays, Memorial |
| PR09 | `setMarkerType "Empty"` / `setMarkerColor` in `init.sqs` before the briefing map is built; the `onMapSingleClick` payload; whether `forceMap`/`mapAnimAdd` are usable | Ops map |
| PR10 | `weaponPool = 1` with a `createUnit`'d squad: decrement on Apply; `add*Pool`/`pickWeaponPool` in the finisher; `fillWeaponsFromPool`; duplication of class-default gear. Retry without an autosave re-runs `init.sqs`, then re-applies `weapons.cfg`, whose saved pool overwrites the row (`CWR:UI/DisplayUIMenus.cpp#L1054-L1084`): do its saved unit references reach the re-created units | Loadout |
| PR11 | Pool commands in a non-first mission's `init.sqs` apply once, and do not double after restart-from-row (safe by reading: `AddMission` re-reads rows from disk, `CWR:UI/OptionsUI.cpp#L1704-L1711`) | Loadout |
| PR12 | `debriefing = 0` skips the debriefing; the debriefing Restart exists and drops vars; `lives` semantics | Save semantics |
| PR13 | A camp self-loop adds no row and keeps the old snapshot; how rows are named when classes share a template (by reading: keyed by class, shown by the template's `briefingName`, `CWR:UI/DisplayUIMenus.cpp#L812-L821`) | Camp, offer lowering |
| PR14 | AI squadmates' `rating` grows with kills; `addRating` restores a saved delta; `skill`/`setSkill` round-trip | Progression |
| PR15 | Scalar `setDammage` on soldiers (hitpoint spread, mobility); vehicle `saveStatus` of fuel, ammo and cargo; `setFuel`/`fuel` | Wounds, Hangar |
| PR16 | `format`/`hint` output of large scalars (`%g`); integer exactness across `.sqc` save and load | Resources |
| PR17 | Multi-variant template: `mission.sqm` size, groups per side, load time with 8–20 layers; triggers guarded by `cmp_op` | SideOpGenerator |
| PR18 | `presence` probability and placement radius re-roll on Retry and on restart | Rolls (SL11) |
| PR19 | Ironman ledger: a dummy unit's experience saved via `saveIdentity` survives restart-from-row and reads back via `loadIdentity` + `rating` | Optional ledger |
| PR20 | `mod` on integer-valued scalars < 2^24 is exact (the stored LCG) | Rolls |
| PR21 | `addEventHandler ["killed", …]` (wiki tag 1.85): payload `[victim, killer]`; it fires for kills by AI squadmates | Service records, Stress |
| PR22 | Load hitch of 11 `createUnit` spawns in `init.sqs`, compared with pre-placed slots | Roster lowering choice |
| PR23 | Wall-clock time of op → camp → op, on one island and across islands | Camp cadence |

## Open questions

1. **Combat-outcome calibration [U].** Can Preview runs (AI-vs-AI, or scripted stand-ins over the harness) calibrate the outcome tables?
2. **Whole-campaign automation [U].** Doc 08 covers single-mission `--test-mission`; can a campaign start at a chosen row from the CLI?
3. **Load tolerance [U].** How many seconds per transition will players accept before a camp every 3 ops feels slow (PR23)?
4. **Per-soldier gear in the 1.99 briefing [U].** Can squadmates' gear be edited one soldier at a time? In CWR yes [V]: the Group page
   links `gear:<id>` (`CWR:UI/Map/UIMapDisplayBriefing.cpp#L216-L218`), which opens that soldier's Equipment page (`#L1062-L1083`), for
   a leading player only (`CWR:UI/Map/UIMapDialogs.cpp#L355`). If 1.99 differs, role kits come from the pool.
5. **Commander design (product).** Plot armour, or an embodied roster soldier with Retry, on `Cwa199` and `Cwr`: which reads as fairer?
6. **Triage transparency (product).** Should the debrief say "survived: gravely wounded (rank)"? Hidden bias may only favour the player,
   but disclosure may feel better.
7. **Card count (playtest).** Is 2–3 visible cards right, or can the radio menu comfortably carry up to 6?
8. **Localisation [U].** Can the `CfgIdentities` `name` be localised through the campaign stringtable? `setIdentity` reads `name` without
   a `Localize` call (`CWR:Game/Commands/GameStateExtUi.cpp#L220`), so only parse-time `$STR` resolution could do it.
9. **Upstream appetite.** Will CWR-CE accept E13, E7 and E8? E5 and E6 are the cheap first asks (doc 18 §9).

## Sources

**Engine source (pinned; exact lines cited inline).** `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/` — `Game/Commands/`
(`GameStateExt.cpp` registrations L860–L1395, `GameStateExtWorld.cpp`, `GameStateExtUi.cpp`, `GameStateExtObj.cpp`, `GameStateExtGrp.cpp`,
`GameStateExtWorldDialog.cpp`); `AI/` (`AICenter.cpp`, `AICenterImpl.cpp`, `AICenterStats.cpp`, `AIUnit.cpp`, `AIUnitImpl.cpp`,
`Path/AITypes.hpp`, `VehicleAIPilot.cpp`); `UI/` (`OptionsUI.cpp`, `OptionsUIApp.cpp`, `OptionsUIImpl.cpp`, `OptionsUICommon.hpp`,
`DisplayUIMenus.cpp`, `InGame/InGameUIMenu.cpp`, `Map/UIMapDisplay.cpp`, `Map/UIMapDisplayBriefing.cpp`, `Map/UIMapDialogs.cpp`); `World/`
(`WorldInit.cpp`, `WorldImpl.cpp`). Also `BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/express.cpp`,
`BohemiaInteractive/CWR@ffc61838b7:tests/unit/engine/Poseidon/AI/test_entity_event_handlers.cpp#L16-L29` (event-handler names) and
`ofpisnotdead-com/CWR-CE@b67bf3bd62:engine/Poseidon/UI/OptionsUI.cpp#L1900`.

**Repository docs.** Docs 08, 18, 19, 21 §11.6, 23 §4, 25 §4–§11, 26 §1, §5, §8–§10.

**Web** (accessed 2026-09-27; fetched unless marked "search").

- **Solomon interviews:** PCGamesN 2017-10-09 <https://www.pcgamesn.com/xcom-2/xcom-jake-solomon-interview>; Kotaku 2012-06-07
  <https://kotaku.com/remembering-the-fallen-and-the-decisions-for-which-the-5916627>; Game Developer 2012-06-20
  <https://www.gamedeveloper.com/design/-i-xcom-i-designer-consequences-make-success-so-much-sweeter> and 2016-03-01
  <https://www.gamedeveloper.com/design/jake-solomon-explains-the-careful-use-of-randomness-in-i-xcom-2-i->; player.one 2017-03-16
  <https://www.player.one/whats-next-xcom-jake-solomon-talks-xcom-5-dlcs-and-mission-timers-589331>; COGconnected 2015-12-10
  <https://cogconnected.com/preview/xcom-2-hands-on-preview-developer-interview-strategic-combat-intensified/>; GamesBeat 2017-06-17
  <https://gamesbeat.com/xcom-2-war-of-the-chosen-upgrades-design-enemies-and-cinematic-story/>; PSU 2024-05-14
  <https://www.psu.com/news/interview-with-jake-solomon-former-xcom-creative-director-midsummer-studios-co-founder/>
- **XCOM design:** DeAngelis <https://www.gamedeveloper.com/design/classic-postmortem-i-xcom-enemy-unknown-i-which-turns-5-today>; Tom
  Francis <https://www.pentadact.com/2016-02-25-solving-xcoms-snowball-problem/>; Bycer <https://www.gamedeveloper.com/design/a-deep-dive-into-xcom-and-xcom-2>;
  Gollop GDC 2013 (reference only) <https://www.gdcvault.com/play/1017808/Classic-Game-Postmortem-X-COM>
- **XCOM facts:** <https://en.wikipedia.org/wiki/XCOM:_Enemy_Unknown>, <https://en.wikipedia.org/wiki/XCOM_2>,
  <https://en.wikipedia.org/wiki/XCOM_2:_War_of_the_Chosen>, <https://en.wikipedia.org/wiki/UFO:_Enemy_Unknown>,
  <https://en.wikipedia.org/wiki/Long_War_(mod)>, <https://www.ufopaedia.org/index.php/Panic_(EU2012)>,
  <https://xcom2.wiki.fextralife.com/Guerrilla+Ops>; search only: <https://www.ufopaedia.org/index.php/Experience>,
  <https://steamcommunity.com/app/268500/discussions/0/1474221865194807318/>, <http://www.vigaroe.com/2020/05/xcom-2-analysis-war-of-chosens-fatigue.html>,
  <https://www.engadget.com/2012-12-10-xcom-memorial-wall-on-facebook-dedicated-to-fallen-soldiers-fri.html>
- **Darkest Dungeon, This War of Mine, FTL, Battle Brothers:**
  <https://www.gamedeveloper.com/design/game-design-deep-dive-i-darkest-dungeon-s-i-affliction-system>,
  <https://www.gamedeveloper.com/business/-i-darkest-dungeon-i-designing-for-despair-and-kicking-you-when-you-re-down>,
  <https://en.wikipedia.org/wiki/Darkest_Dungeon>, <https://en.wikipedia.org/wiki/This_War_of_Mine>,
  <https://www.gamedeveloper.com/design/road-to-the-igf-11bit-studios-i-this-war-of-mine-i->, <https://en.wikipedia.org/wiki/FTL:_Faster_Than_Light>,
  <https://www.gamedeveloper.com/design/designing-without-a-pitch---an-em-ftl-em-postmortem>, <https://en.wikipedia.org/wiki/Battle_Brothers>,
  <https://battlebrothersgame.com/dev-blog-79-progress-update-injury-mechanics/>, <http://battlebrothersgame.com/dev-blog-92-late-game-crises/>
- **Other games:** <https://en.wikipedia.org/wiki/Jagged_Alliance_2>, <https://en.wikipedia.org/wiki/Mount_%26_Blade:_Warband>,
  <https://www.dreadcentral.com/reviews/474381/phoenix-point-review-two-steps-forward-one-step-back/>,
  <https://en.wikipedia.org/wiki/Warhammer_40,000:_Dawn_of_War_II>,
  <https://www.pcgamesn.com/company-of-heroes-2-ardennes-assault/company-of-heroes-2-ardennes-assault-review>,
  <https://en.wikipedia.org/wiki/Close_Combat:_A_Bridge_Too_Far>, <https://en.wikipedia.org/wiki/Tom_Clancy's_Rainbow_Six_(video_game)>,
  <https://en.wikipedia.org/wiki/Tom_Clancy%27s_Ghost_Recon_(2001_video_game)>, <https://en.wikipedia.org/wiki/Hidden_%26_Dangerous>,
  <https://en.wikipedia.org/wiki/Ready_or_Not_(video_game)>; search only: <https://mountandblade.fandom.com/wiki/Recruitment>,
  <https://www.gamespot.com/reviews/phoenix-point-review-the-life-aquatic/1900-6417382/>,
  <https://support.feralinteractive.com/docs/en/dawnofwar2/latest/steam/manual/>,
  <https://steamcommunity.com/app/231430/discussions/0/527273789693112351/>,
  <https://itemlevel.net/ready-or-not-commander-mode-guide-in-1-0-roster-therapy-traits/>
- **Community strategic layers:** <https://github.com/dcs-liberation/dcs_liberation/wiki/Squadrons-and-pilots>,
  <https://github.com/dcs-liberation/dcs_liberation/wiki/First-operation>,
  <https://official-antistasi-community.github.io/A3-Antistasi-Docs/beginners_guide/raw_beginners_guide.html>,
  <https://github.com/KillahPotatoes/KP-Liberation/blob/master/README.md>

## Verification notes

Spot-checked against the pinned CWR source on 2026-09-27: `CreateUnit` runs the init string before `Load(NextSoldierIdentity)` and
before setting rank, experience and skill, and returns early at 12 units (`GameStateExtWorld.cpp#L155-L235`); the 5-element rank parse
falls back to PRIVATE and the command returns `NOTHING` (`#L237-L310`); skill tiers (`UIMapDisplayBriefing.cpp#L138-L162`); leader-only
radio listing and `null` hiding (`InGameUIMenu.cpp#L628-L689`); `%g` scalar text (`express.cpp#L1977-L1982`); `LIEUTNANT`
(`AICenter.cpp#L178`); the consecutive same-name row skip (`OptionsUI.cpp#L1122-L1127`); `rating` = experience, 0 when destroyed
(`GameStateExtObj.cpp#L444-L466`); registrations of the marker, dialog, action, identity and `setSkill` commands. Other engine citations
come from docs 18, 19 and 23 and their verification notes. Web claims come from the meta-loop survey this doc builds on; they were not
re-fetched here and keep their [V]/[V-search] marks. All 1.99 behaviour stays [U] until §9 runs.

### Product review notes

Product and fun review, 2026-09-27, against the AGENTS.md invariants, doc 25's flow and doc 26 §5 and §8. **Changed:** the extraction
choice is planned during the op, spelled out in a hint, gets a code default, and its squad picks become provisional (§1.1, step 8).
Triage now responds to what the player controls. A promotion gives a 1-of-2 perk pick. Walking in the camp is optional, and a camp with
nothing to decide is deferred (§4.1, §4.3). A roll-call puts names in the fight, because the group bar shows only numbers [V]. Auto-tune
treats pinned numbers as fixed. Users may type soldier names. `Story4` gains its missing `AtMax` socket. Pressure can now fall. The Radio
Mast no longer hides expiry. AC16 and AC18 now measure the loop, not just one firefight. No new model decision was added. **Open:**
(1) an attendant's heal zeroes every hitpoint (`CWR:World/Entities/Vehicles/Transport.cpp#L510-L517`, `CWR:AI/VehicleAICombat.cpp#L353-L363`)
[V]. That squad medics take this path is [I] (PR15). A heal before extraction can therefore erase wounds, so we must choose between end
damage (XCOM-like: field care shortens recovery) and peak damage. (2) If the commander dies, Retry replays the op and so un-kills
squadmates. That matches non-Ironman XCOM; claim no stronger stakes. (3) AI squadmates die from AI mistakes the player cannot order away,
which is the main fairness gap versus XCOM. Only AC16 can see it; the balance lab cannot. (4) Motor Pool carries two rules, while §3.2
says one per unlock and SL07 only flags zero. (5) One island with 8 side layers limits replay variety. (6) Whether a soldier keeps his
squad number across ops depends on spawn order [I]; spawn in roster order. (7) The file is now further over its ~650-line target.

### Engine review notes

Adversarial engine review, 2026-09-27, against the pinned clones and docs 18, 19 and 23. Every CWR file cited in §2–§4 hashes the same in
CE, except `GameStateExtWorld.cpp`, `OptionsUIApp.cpp` and `DisplayUI.cpp`, whose diffs are the `endGame` rename and download/input UI.
**Held [V by reading]:** the `createUnit` order and its 12-unit no-op; `init.sqs` runs synchronously in `InitVehicles`, after unit init
lines; presence applies to empty vehicles/objects and non-playable units only, while sensors and markers are always created
(`AICenterImpl.cpp#L1396-L1446`, `#L1525-L1538`); the `setIdentity` field set and mission → campaign lookup; dialog lookup mission →
campaign → global; leader-only radio with `null` hiding, and `setRadioMsg` relabels every trigger on a channel; user actions within 10 m
in front, the player's own always; `%g`; the same-name row skip; book restart loads the row's table (`OptionsUIApp.cpp#L458-L501`);
Retry re-injects the current table (`DisplayUIMenus.cpp#L1054-L1084`); the debriefing Restart restores its post-commit `GStats` copy and
re-inits without vars (`UIMapDialogs.cpp#L665-L695`, `#L898`); the group bar shows numbers only. In `Op1` the briefing pool is empty and
unsaved, as no row exists yet (`OptionsUI.cpp#L1214-L1221`, `#L1306-L1312`). **Corrected:** `createUnit` takes the next unused identity,
not a random one; `skill` also reads 0 once destroyed; negative xp risks the renegade rule (SL17); the gear hazard includes the commander
and `fillWeaponsFromPool`, and survivors' gear must be returned by script (SL09); the debrief-restart guard cannot restore state; the
Grey Heron playthrough used `Story3 → SideB`, which is not a socket; Lowering B cannot gate on campaign vars in `Op1`; E8 now hooks the
debriefing Restart button; the AC17 gate adds PR17, PR18 and PR20; `--test-mission` caveats (§5.3). **Wiki tags** (BI wiki API, fetched
2026-09-27; availability only): ofp 1.00 `hint`, `hintC`, `setRadioMsg`, `setIdentity`, `setMarkerType`, `objStatus`, `rating`,
`addRating`, `getDammage`, `setDammage`, `setCaptive`, `removeAllWeapons`, `addWeapon`; 1.10 `addAction`; 1.20 `removeAction`; 1.21
`setMarkerColor`; 1.27 `forceMap`, `mapAnimAdd`; 1.34 `createUnit` (the 5-element form), `createVehicle`, `deleteVehicle`; 1.75
`createDialog`, `closeDialog`, `lbAdd`, `lbCurSel`, `lbSetValue`, `lbSetPicture`, `buttonSetAction`, `ctrlSetText`, `skill`, `setSkill`,
`weapons`, `magazines`, `saveIdentity`/`loadIdentity`/`saveStatus`/`loadStatus`, the pool commands, `fillWeaponsFromPool`; 1.85
`onMapSingleClick`. `setMarkerText` is tagged only `ofpe 1.00`; `createMarker` first `arma1 1.00`. **Still open:** all 1.99 runtime
behaviour (§9); whether Retry's `weapons.cfg` references reach re-created `createUnit` units (PR10); the configured `renegadeLimit`
(unverified); how a `nil` compare evaluates in a presence condition (unverified); whether `--test-mission` loads a campaign
`description.ext` [I].
