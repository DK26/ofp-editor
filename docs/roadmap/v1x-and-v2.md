# Roadmap: v1.x and v2

> **Status:** proposal (roadmap baseline 2026-09-27). Part of the [roadmap](../roadmap.md). The order v1.1 → v1.4 is a proposal;
> the releases are independent except where "Depends on" says otherwise and may interleave. Every threshold quoted is the source
> doc's placeholder.

## v1.1 North star: the strategic layer and Operation Grey Heron

**Goal.** Someone can build an XCOM-like campaign that plays in real time, with named soldiers they can lose, resources, an expiring
ops board, a doom clock, camp visits and visible consequences, and "Operation Grey Heron" passes its acceptance criteria (D005; doc 29).
The owner answered OWQ-13 with (a) on 2026-09-27: this is the first milestone after v1.

**Scope.**

- **Strategic-layer kit** (doc 29 §3): the typed modules (among them Roster, Wounds, Recruitment, Loadout from the native weapon pool,
  Resources, Unlocks from research by capture, facilities and projects, Hangar, OpsBoard and DoomClock, with the playable camp) plus the
  optional Stress, Bonds and Nemesis; the fixed commit pipeline in the finisher; the Strategic complexity tier in Plotline and the Tote
  (doc 19 §6.8).
- **Doc 35 and doc 34 rows** (I35-29, I34-29): the Sortie op kind, roster and recruitment seeds, ops-board card types with the automatic
  resupply card, pressure- and progress-driven doom clock modes, the Reputation module; card-template fields, Programs, EnemyPosture,
  Mole, SupportRequests, Commendations, SectorDecl, PerkChoice, adaptive Nemesis, posture and enemy-policy steps, SL21–SL25, calibration
  from Preview battle reports, bundle-level endgame checks, the TeachingSchedule.
- **Doc 36 rules** (I36-29): act breaks never wipe what was earned; every penalty has counterplay; randomness in situations, not
  payoffs; the status card with 3–5 horizons; risk and reward bands; bounded bad-luck protection for loss-side rolls; honest two-way
  difficulty rungs (names from the names table, OWQ-08 (a)); local factions; "Rested" framing; the finale epilogue replay; the
  engagement-ethics checklist (doc 36 cv43, a product rule for Plotroom's own output since OWQ-20 (a)).
- **P9 "Strategic layer"** in the campaign flow: "make me an XCOM-like campaign" as about 30 structural decisions plus about 40 one-slot
  text fills, all Pick or Fill; the same valid campaign with template text when no model is used (doc 29 §6).
- **Balance lab** (`plotroom-campaign-sim`): policies (Standard, Pessimistic, Builder-A/B, Exploiter), ×2/÷2 sweeps, dominance and
  decided-state detection, SL26–SL31, tuning proposals that move one knob ×2 or ÷2 with a simulator diff (doc 36 cv30; I36-21).
- **Probes:** doc 29 PR01–PR22 on Remastered through the harness and on 1.99 by hand (SP-08), plus doc 34 OQ1's list (I34-29).
- Standing Orders entries for Plotroom's own campaign rules (bad-luck protection, triage, decided-state finale; I36-33).

**Depends on.** v1.0 (M5's campaign model, compiler and simulator; M6's flow with models). RAT13 additionally needs v1.3's seeds.

**Gates.** Answered by the owner on 2026-09-27: OWQ-13 (a) (placement), OWQ-20 (a) (engagement ethics as a product rule), OWQ-23
(the commander is a campaign setting with plot armour by default; triage is disclosed in the debrief; both confirmed again after the
first balance-lab runs and playtests), OWQ-21 (a) (a fresh play seed by default, Fixed for challenge entries and "beat my run"
re-exports; memory across playthroughs opt-in with a visible reset; no re-roll exception, for SL11's wording). Still gating: DG004
decided for strategic modules; DG038, which OWQ-21's answer unblocks.

**Exit evidence.** Doc 29 §8: AC01 (intake), AC02 (model independence: no-model, T1, T2 and T3 runs all pass AC03–AC13), AC03
(structure and budget), AC04 (lint-clean in C, CF and SL families for `Cwr` and `Cwa199`), AC05 (totality), AC06 (500 seeded runs per
policy reach an ending), AC07 (stakes), AC08 (early fairness), AC09 (no dominant strategy), AC10 (visibility), AC11 (triage), AC12 (glass
box), AC13 (safe refines) in CI on synthetic fixtures; AC14 (engine agreement) and AC15 (roster round trip) as opt-in local runs on
Remastered; AC17 (the `Cwa199` build labelled "verified on 1.99" only after PR01–PR18 and PR20 pass and a manual 3-op run confirms AC15);
AC18 (time to play: Op1 and the Camp Preview-ready ≤ 5 min after S0; the full draft ≤ 30 min on a T1 local model). **AC16** (a human
panel of ≥ 5 players) gates the claim "north star achieved", not CI.

**Integration items.** I35-29, I34-29, I36-29, I34-26 (strategic rows), I34-25 (Mole and Nemesis), I29-26-19 (SL lints), I36-21
(tuning proposals), I36-33 (strategic-rule entries).

## v1.2 Cinematics and atmosphere

**Goal.** Easy, correct, tactical cutscenes and atmosphere: the cinematics timeline (doc 32), the cutscene director that turns an intent
and a few map picks into a checked, editable sequence (doc 39), and atmosphere, sound and music (doc 41).

**Scope.**

- **Timeline** (doc 32 phases 0–4): probes; the model, compiler and safety wrapper; shots, overlays, music and `say`; Intro, Outro and
  in-mission hosts; capture-block import; live shot preview, thumbnails and filmstrips over the live link; capture from the running game;
  the screenplay track with measured durations; templates, suggestions, follow shots, gameplay cameras; classic camera-script lifting;
  flow-back of edited literals; T0 template packs.
- **Director** (doc 39 DP0–DP4): exact `SurfaceY` in `plotroom-terrain` and the subdivision-cache reader; the offline planner (scale and
  lens solver, composition, candidates, DR01–DR14, pacing); staging with doctrinal recipes and the robustness contract; `core/make-cutscene`
  with Shuffle; round trip of captured and imported shots.
- **Atmosphere and audio** (doc 41 AD0–AD4): sun model and sight formula; the per-section atmosphere panel and AL lints; presets
  AM01–AM12, the weather timeline, lights and dressing kits; the cue planner, fades and ducking, soundscape painter, audio import with
  loudness and `.lip` generation, the language matrix and licence guard (`plotroom-audio`, formats-audio rows); the atmosphere workflow.
- **Remaining doc 34 items:** timeline rows ed09–ed12, postcards (le13), test range and speed control (ed17), director, capture-back and
  route recording (ed18) (I34-32, I34-08); music cue pairs per faction and the finale epilogue scene (I36-32); one music cue per mission
  (I35-MOMENT).

**Depends on.** M3 (live link), M5 (Cutscene node, `plotroom-cine`), M6 (workflows with models for `core/make-cutscene` and the
atmosphere workflow).

**Gates.** DG009, DG034 (camera and effects defects go to the engine-requests register), DG035, DG036, DG037 (names for the six
"Director" features, via the names table, OWQ-08 (a)). Probes CP1–CP13 (doc 39), AP1–AP18 (doc 41) and doc 32 §7 phase 0 first. The
release itself is decided: the owner placed the timeline and the director in v1.2 (OWQ-14 rung 4 (a)).

**Exit evidence.** 32-AT1–32-AT10 (32-AT6 headline: a newcomer authors a 30-second intro with four shots, a title card, music and radio
chatter without writing script, previews it live on Remastered and passes every lint on all three profiles); DAT1–DAT13 (DAT6 headline:
a 25–40 s intro from intent plus three map picks at 10 seeds with zero clearance, framing and doc 32 findings on all three profiles;
DAT6, DAT8 and DAT9 are opt-in local runs); AMT1–AMT14 (AMT12: the eight upstream `.lip` cases pass on synthetic fixtures; AMT13 and
AMT14: a 3–9B model yields valid, deterministic output); 31-AT6 (pasted camera captures are recognised as shots, and re-emission equals
the normalised original).

**Integration items.** I34-32 (timeline rows), I34-08 (postcards, test range, director recording), I36-32, I35-MOMENT (music cue),
I35-CUT (timeline form of the recipe).

## v1.3 Replayability and multiplayer

**Goal.** Missions and campaigns that play differently each time within designed bounds, and a multiplayer Preview that makes MP
content testable.

**Scope.**

- **Replayability** (doc 43 RV0–RV4): engine-truth probes P-R1–P-R12 and doc 29 PR17–PR20; the ported random-table model; mission
  variation axes with default variants, budgets and the Variety panel; build-time seeds, golden seeds, seed codes, remix levels and
  "Surprise me"; campaign-scale axes, shuffle-bag decks and campaign modifiers; the MP roll protocol and JIP on `Cwr`/`Ce`; the challenge
  catalogue as T0 data with a baked seed and no calendar, week index, streak, reward or reminder (OWQ-20 (a)).
- **Multiplayer Preview** (Preview P4; doc 08 §4.5): a local `PoseidonServer --private` with a sandboxed user directory plus N clients,
  slot presets per side.
- **MP authoring:** doc 31 L4 (wave-2 modules and MP modules, doc 35 rc23–rc26; MP settings lints rc65); doc 37 PT4 (locality-verified
  MP lowering) and PT3's SP ↔ MP wizard and island move; MP numbers as generator defaults (rc52); mode-family templates for CTI, Hub War,
  set-piece and co-op (I35-TPL rc37–rc39); the SP-campaign-to-co-op-pack workflow and MP series export as a rotation (I35-19 rc83); the
  "How classic MP modes work" Standing Orders page and the live CTF tutorial (I35-DRILL rc72); probe-backed MP primer facts (I35-PRIMER-MP).

**Depends on.** M5 (campaign scale); M3 (Preview infrastructure); v1.1 for RAT13.

**Gates.** DG038 (engine `random` and SL11; OWQ-21 (a) is answered). OWQ-20 (a) shapes the challenge catalogue (above).

**Exit evidence.** RAT1–RAT18 (RAT11 and RAT12 on a hosted server with two clients and on a dedicated server); PAT6 (island move dry
run), PAT10 (seats, loadouts and cargo correct in a two-client MP Preview); 31-AT1's MP behaviour re-run on MP Preview.

**Integration items.** I35-TPL (families), I35-19 (MP series export, co-op pack), I35-GEN (rc52), I35-MOD (MP modules), I35-DRILL (rc72),
I35-PRIMER-MP (probe-backed facts), I35-LINT (rc65).

## v1.4 Extensions and community

**Goal.** Extend Wilco and the editor only through the plugin system (`AGENTS.md`; D007), and connect to community sources the user
enables (D008), without hosting mods (D030).

**Scope.**

- **T2 service connectors** (doc 22 step 2): the rmcp Streamable HTTP client through `plotroom-net`, scope gate, egress card and log,
  keyring, OAuth, limits, offline state; a stringtable translator first, then radio voice. The **`feed` kind** (D008 item 3; DG028) for
  read-only catalogs.
- **T1 WASM generators** (doc 22 step 3): the wasmtime LTS host, WIT `plotroom:plugin@1`, the SDK and test kit (GPL-3.0-or-later for
  now, OWQ-03 (a)),
  reference plugins, declarative panels.
- **Mods and registry** (doc 42 MS2–MS4): the built-in Community mod directory and alias table, the offline "Find mods" panel, the
  vehicle-role evaluation (which unblocks vehicle remaps, I42-37, I35-84); the opt-in Community catalog feed (after the channel
  maintainers' non-objection: DG029 option A, OWQ-12); the signed registry index RG1 (extensibility §9), operated by the project's own
  organisation (OWQ-17 item 4).
- **External agents:** `workflow.decide` journaled with an `External` origin and excluded from qualification (OWQ-15 (a): after v1).
- **Cross-plugin chaining** in first-party and user-authored workflows, with the egress card every time and never exposed to external
  agents (DG014 option B, OWQ-16).
- **Knowledge community:** Drill tracks B and C, pack import of lessons, and locales `cs`, `pl`, `ru`, `de` as native reviewers join
  (doc 33 phase 6; OWQ-14 (a)).

**Depends on.** M4 (T0 packs), M6 (`plotroom-net`, egress grants).

**Gates.** Decided by the owner on 2026-09-27: DG014 option B (OWQ-16), DG029 option A (OWQ-12), DG030's four proposals (OWQ-17),
OWQ-03 (a), OWQ-15 (a). Still gating: the channel maintainers' non-objection before the directory pack and the Community catalog feed
ship; SP-15 and SP-16 first.

**Exit evidence.** Stub-server tests (pin drift, SSRF including IPv4-mapped IPv6 and redirect chains, oversize output, non-https URLs,
hostile asset names); MAT9 (connector against a stub server), MAT10 (with the connector enabled, traffic only to the provider and the
enabled origin), MAT14 (registry CI fixtures), MAT15 (signing, yanks, revocation); the adversarial T1 component suite (infinite loops,
memory bombs, invalid UTF-8, forbidden WASI imports fail to instantiate); determinism tests; 33-AT13 (every card renders in each locale).

**Integration items.** I42-22 (feed connectors, RG1), I42-37 and I35-84 (vehicle remaps), I34-22 (registry phase), I36-22-27 (sharing
through the registry).

## v2 and later

| Item | Why later | Reopen trigger |
| --- | --- | --- |
| Registry RG2 (community submissions with throttles) and RG3 (TUF metadata) (doc 42 §5.1) | RG1 first; needs reviewers beside the operator (the project's own organisation, OWQ-17 item 4) | RG1 in use by external publishers |
| In-process embedded inference (doc 13 phase C: S3 and S5) | Out-of-process is safer (D022 item 2); an in-process abort would lose work; the managed `llama-server` sidecar is the owner's primary local runtime (D022 amendment note) | S3 passes and the helper-process design (architecture README §8 item 7) is decided |
| Optional 3D placement view (doc 09 CO1) | The 2D map-first flow is the product (doc 09 WN5) | Community demand after v1 |
| Gamepad and Steam Deck input (doc 09 CO14) | Not needed by the core audience | Demand plus a test device |
| A decision model in front of the generator (D023 item 5; doc 16) | Must beat the deterministic and generative selectors on our instruments | Instrument results |
| Extension overlays for others' campaigns (doc 34 cw13) and veteran import (cw28) | OWQ-06 answered (extension-only for Bohemia's campaigns; third-party parents by licence or recorded permission); a probe on reading another campaign's save | Probe passed (may land in any v1.x) |
| Ribbons (doc 34 le14) and other engagement features that the engagement-ethics rule must clear | They must pass doc 36's cv43 rule, a product rule since OWQ-20 (a) | A design that passes cv43 (may land in any v1.x) |

## When the engine ships it

Community-engine features are adopted as opt-in `Ce` capabilities in whichever release is current when they ship and the capability
probe detects them (`docs/upstream/README.md`): tolerant Preview and the console (Preview P3; ER-001, ER-002; DG001), in-process restart
(ER-003), campaign test launch at a chosen row (ER-007), harness authentication (ER-010, after OWQ-09's private reports are
acknowledged), opt-in campaign keys (ER-027 first, then the filing plan's wave 5), and new commands only when a feature on the `Ce`
profile would use them. Filing follows the register's proposed filing plan, and nothing is filed without the owner (OWQ-11 (a): the
owner or a maintainer the owner names starts with CE #35 and a small tested PR, then opens one tracking discussion).

## Verification notes

### Roadmap baseline (2026-09-27)

- Built from docs 29 §3, §6, §8, §9; 32 §7; 39 §10; 41 §9; 43 §8; 08 §4.5, §6; 31 §10; 37 §11; 22 §7.1; 42 §5.1, §8; 33 §9; 13 §11;
  09 §8.3–§8.4; D005, D007, D008, D022, D023, D030; `docs/upstream/README.md` and the register's filing plan.
- The split of doc 34's strategic rows between M5 (classic tier) and v1.1 (strategic tier) is this roadmap's proposal; see
  integration-owners.md for the item-level assignment.

### Owner answers folded (2026-09-27)

- The owner's answers of 2026-09-27 now stand in v1.1 (OWQ-08, OWQ-13, OWQ-20, OWQ-21, OWQ-23), v1.2 (OWQ-08, OWQ-14 rung 4), v1.3
  (OWQ-20, OWQ-21), v1.4 (OWQ-03, OWQ-12, OWQ-14, OWQ-15, OWQ-16, OWQ-17), v2 (OWQ-06, OWQ-17, OWQ-20; the local-runtime decision)
  and "When the engine ships it" (OWQ-09, OWQ-11). v1.4 now lists cross-plugin chaining, which DG014 option B allows for first-party
  and user-authored workflows. Release order and contents are otherwise unchanged.
