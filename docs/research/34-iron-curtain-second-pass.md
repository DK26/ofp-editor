# Iron Curtain design docs, second pass: campaign, editor, learning and mod ideas

Research doc 34 for Plotroom (`ofp-editor`). Research date: 2026-09-27. Audience: contributors and LLM coding agents. This file is meant to be read on its own.
Question answered: doc 17's first pass covered Iron Curtain's (IC's) LLM stack. Which of the remaining ideas in IC's public design docs are worth taking for campaigns, the editor, learning and mods? What does each become on the OFP/CWA engine as shipped, and which of our docs should absorb it?

**Status.** Proposal-only. Every Plotroom design here is **[I]** unless tagged. Every number (threshold, cap, count) is a placeholder for the simulator or for playtests to tune.
**Epistemic legend.** **[V]** means verified against the pinned source, or carried from a sibling doc that verified it (cited as "doc NN"). **[I]** means inferred or proposed. **[U]** means unknown and needs a probe. For IC, [V] only means "IC's docs say this". IC is still at the design stage, so its docs record intent, not proven practice (doc 17 TL;DR).
**Citations.** `ICD:` = `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:` (Markdown under `src/`). In rows and deep-dives, `…/` abbreviates a leading `ICD:src/` (plus directories where unambiguous); §8 gives every file's full path. `CWR:` = `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/`. `GSE` = `CWR:Game/Commands/GameStateExt.cpp`, the script-command registrations; availability on 1.99 is [U] unless stated. `F<n>` refers to doc 19's engine facts and `C<nn>` to doc 19's lints.
**Codes already in use (do not reuse):** doc 19 C01–C21; doc 26 CF01–CF12 and patterns P1–P8; doc 28 MC01–MC19, CF13–CF18 and TX01–TX06; doc 29 SL01–SL20, probes PR01–PR23, pattern P9 and CE extensions E7–E14; doc 27 D1–D8. The new lint codes in this doc (CF19–CF25, SL21–SL25, MC20–MC29, D9) are **provisional**; the design round assigns the final numbers (§5.1, which also lists doc 42's D10–D12). Two bare labels collide across docs and need a prefix in the design round: `D9` (doc 27's D-series lint) also names doc 21's section label D9, and pattern `P10` also names doc 09's pain point P10 (doc 26's P1–P8 already share that clash).
**Sibling docs 31–33.** Docs 31 (no-code ladder), 32 (cinematics and camera) and 33 (Standing Orders and Drill, the concept manual and live tutorials) now exist; they were written in the same round without this doc's rows, so rows aimed at them are reconciliation inputs, not new sections. Doc 31 §6 also fixes cinematic engine constraints and a compile contract, so the doc 32 rows reconcile against both.
**Row IDs.** `cw` = campaigns and world, `ed` = editor and creator UX, `le` = learning and engagement, `mo` = mods and content.

## TL;DR

- **Scope.** About 120 mined ideas in four clusters. After merging duplicates across clusters, 98 rows remain, plus 11 skip entries. The biggest gains are in the campaign tier (docs 26 and 29) and in the no-code, cinematics and Standing Orders/Drill docs (31, 32 and 33), not in the AI.
- **Card disclosure contract (cw01).** Each card keeps failure separate from expiry. Code renders the effect text from the typed effect, so it always has a number. Each card names the missions that consume it and can offer approach variants. The model writes only a blurb of 20 words or fewer. Target: doc 29 §3.2/§3.6.
- **Many small clocks instead of one (cw02, cw04, cw21).** Enemy capability programs have stages and timing windows. Enemy counter-intelligence tightens with the tempo of covert ops the player chooses to run (a cost shown on the card), not with their success, so doc 29's "scale by the clock, not by success" rule holds. Sectors carry features and war damage. A code-owned enemy strategic policy drives them. Everything lowers to flat `saveVar` ordinals and presence-gated variants [V F12 on CWR; 1.99 waits on probe PR04].
- **Narrative machinery the harness can prove (cw14–cw17).** A thread lifecycle with foreshadow counts, a twist-pattern catalogue with engine-feasibility tags, a Mole module (a traitor in the cast) and a Nemesis that adapts to the player's tactics. Code schedules every beat; the model fills one slot at a time.
- **Teaching compiled into campaigns (cw12, le22–le24).** Two new lints: a character must be met before a briefing references them, and a mechanic must be taught before it is used. The compiler places one in-character explainer at the first node on each path where a mechanic appears.
- **The spine of doc 31 (ed03, ed04).** A module catalog that lowers to vanilla triggers, logics, waypoints and SQS. It comes with a two-way ladder: *Show generated*, *Eject to script*, and *Lift* for recognised hand-written patterns. Unknown code stays verbatim, never dropped.
- **Sidecar objects that compile away (ed01, ed06, ed08).** Named zones, phases and named routes live in the sidecar. Each compiles to plain trigger geometry, `objStatus`/`setMarkerType` blocks and ordinary waypoints, so a vanilla re-save keeps working content.
- **Cinematics (ed09–ed12), the core of doc 32.** A typed step timeline compiles to one camera SQS with Preview-from-step. Alongside it: a radio message queue, music cues and ambient zones.
- **Learning (le01–le10), the core of doc 33.** Drill lessons deliver a payoff first. Live tours are validated by editor events. Smart Tips have mastery suppression and an attention budget. Standing Orders is built from one metadata source, and every lint code links to its page.
- **One validator behind three surfaces (ed14, ed15).** The same core serves Export Readiness, a headless `plotroom check` and Wilco. It adds per-object target badges and a retarget dry run with a fidelity report.
- **Mods (mo01–mo16).**
  - A shareable `*.modset.toml` locks exact revisions and exports launch lines.
  - A "who serves this file" resolver explains which mod provides a file.
  - A catalog-drift report flags changes after a mod update.
  - Every sound gets a text path.
  - Per-language voice uses the engine's own override [V `CWR:UI/OptionsUI.cpp#L434-L481`].
  - Export gains a redistribution guard (lint D9) and a project lockfile.
- **Skipped.** Everything that needs IC's deterministic replay simulation, a multiplayer campaign flow, a hosted Workshop or P2P delivery, or generated factions (§6).

## How to read this

- **Relation to doc 17.** Doc 17 mined IC's LLM features: D016 bring-your-own-LLM, D047 provider config, D057 skill library, D071 external agents, `llm-metadata`, Tera templating and validation. It also kept a short UX list (§15) and project-process ideas. This pass covers what doc 17 left out:
  - `modding/campaigns.md` and `modding/enhanced-campaign-plan.md` in depth; doc 19 took only D021/D038 basics from them;
  - D016's narrative modes;
  - D038's trigger, media, onboarding and game-master sub-files;
  - D065 (tutorials), D033, D036 and D058;
  - the package, profile and install decisions (D023, D026, D030, D049, D050, D051, D062, D066, D068 and D075);
  - IC's player-flow pages.

  Where doc 17 already has a one-line mention, the row says so.
- **Verdicts.** *Adopt*: take the idea in nearly the shape IC designed, renamed. *Adapt*: keep the goal but change the mechanism to fit the engine or our scope. *Skip*: it does not fit (§6).
- **Constraints every translation respects.**
  - The engine as shipped: 7 end codes, `saveVar` persistence and no generation at runtime.
  - No runtime creation on `Cwa199`: `createGroup`, `createTrigger`, `setTriggerStatements`, `addWaypoint`, `createMarker` and `setDate` appear only in `Cwr`/`Ce` output (doc 31 §4.6, §5.3). No target has `compile`, `spawn`, `isNil` or `params` [V doc 14 L98]. So on 1.99 every "disable", "add" or "spawn" below means a pre-placed object gated by a flag or by presence.
  - Presence gating rests on doc 19 F12, verified by reading CWR; on 1.99 it waits on probe PR04 (doc 29 §9). The engine has no vehicle pool and no unit roster [V doc 18 §6.4]; both are doc 29 modules built from `saveVar` scalars.
  - Glass box: every generated element is visible, inspectable and editable.
  - Code owns facts; the model picks or fills.
  - Wilco is product-scoped: no shell, no mod downloads, no arbitrary file I/O (AGENTS.md).
- **Merged rows.** Duplicates across clusters were merged into one home row, and the other cluster points to it.
- **Overlaps with doc 28** (whose lints are proposed but not adopted) are named so the design round can merge them instead of adding near-duplicates.

## 1. Campaigns and world (cw)

| ID | Idea (IC source) | Verdict | Plotroom translation | Target | Already covered? |
|---|---|---|---|---|---|
| cw01 | Operation-card disclosure contract: failure vs expiry, quantified effects, reveals, named consumers, approach variants (`ICD:src/modding/campaigns.md#L751-L897`; `…/enhanced-campaign-plan.md#L613-L650`) | adapt | Extend `CardTemplate` with `on_fail`, `reveals`, `chain`, `dispatch` and `approaches`. Code renders the effect text; the Path Explorer computes the consumers (§1.1). Lints SL23, SL24. | 29 §3.2/§3.6; 19 §6.1; 26 §10 | Partly. Doc 19 §2.3 has On Success / On Failure / If Skipped; doc 29 has `reward/risk/ttl/if_ignored` and SL05. |
| cw02 | Capability programs, asset ledger, timing windows (`…/enhanced-campaign-plan.md#L438-L509`; `…/campaigns.md#L1446-L1584`) | adopt | Module `Programs`. Each program has stage, timing and quality enums, stored as `saveVar` ordinals. Each op applies one verb (deny, delay, degrade, corrupt, capture or expose) to one stage. Consumer missions pick authored variants by presence [V F12] (§1.2). | 29 §1.3/§3.2/§3.5; 26 §5.2; 19 §4 | Partly: one `DoomClock` and regional Pressure. |
| cw03 | Intel chains, compound bonuses, exclusive branches (`…/campaigns.md#L861-L875, #L1111-L1199`) | adopt | Derived CXL variables (`full_intel = spy_net && radar_down`) and counters. Compound effects lower to presence sets or markers pre-revealed with `setMarkerType` from `"Empty"` [V GSE#L1248]. An exclusive node is a guarded edge and needs no router while sockets stay ≤ 7. The model names chains only. Lint SL25 (the head card expires before the tail is offered). | 29 §3.2; 19 §5; 26 §5.2 | Partly: `RuleChange::RevealCards`; doc 26 Intel module. |
| cw04 | Enemy counter-intelligence escalation and tempo (`…/campaigns.md#L1586-L1624, #L2218-L2256`) | adapt | Optional module `EnemyPosture` with `tempo` (+1 per side op launched, win or lose; −1 per story op or rest) and `opsec` (an enum stepped at commit when `tempo` crosses a threshold). IC steps OPSEC on *successful* covert ops; we key it to the player's chosen tempo instead, shown on every side-op card as a cost, because doc 29 §1.5 rule 2 scales enemies by the clock, not by success (cw20 rejects success scaling for the same reason). Consumers vary patrol density, QRF delay, skill and presence-gated extra patrols. A "mole hunt" op lowers `opsec` (§1.2). | 29 §1.3/§3.2/§3.3; 26 §9.3 | No. Doc 29's escalation is driven by neglect, not by success. |
| cw05 | Third-party actor alignment ladder with grants and blowback (`…/enhanced-campaign-plan.md#L511-L540`; `…/campaigns.md#L1024-L1042`) | adapt | An alignment enum derived from doc 26 Reputation by thresholds, plus a code-owned grant catalogue: staging (alternate start through presence-gated groups), manpower (a partisan squad), local knowledge (pre-revealed markers), sanctuary (an extra extraction trigger). Native lever: Intel `resistanceWest/East` [V doc 04 §3.2, file version ≥ 10], which is fixed per mission folder, so a shared side-op template needs the runtime `setFriend` [V GSE#L1393; 1.99 U]. Blowback = a presence-gated enemy patrol. | 26 §5.2; 29 §3.2; 04 §3.2 | Partly: Reputation module. |
| cw06 | Endurance battles that culminate rather than annihilate (`…/enhanced-campaign-plan.md#L542-L565`; `…/campaigns.md#L1044-L1109`) | adapt | Knobs on archetypes #6 Defend and #7 Delay: `hold_s = base + Σ ledger deltas`. On culmination a `culminated` flag gates the remaining wave triggers off (their conditions read it; there is no trigger-disable command, and runtime `setTriggerStatements` is `Cwr`/`Ce` only, doc 31 §5.3). Attackers get a `move` order to a withdrawal point, or reach a pre-placed withdrawal waypoint released by sync (`addWaypoint` is `Cwr`/`Ce` only). Campaign-level exhaustion removes crates through presence at load; mid-mission exhaustion gates the resupply triggers off. A soft timer is a briefing line and a hard timer a hint countdown; both honour SL16. Lint MC20. | 26 §9.3; 29 §3.2 | Partly: archetypes #6 and #7. |
| cw07 | Composable generated-op grammar (`…/campaigns.md#L433-L600`; `…/enhanced-campaign-plan.md#L567-L611`) | adapt | Typed slots: site, objective, ≥ 2 ingress routes, exfil, security tier, and exactly one complication. Choices are made at edit time from a recorded seed; at runtime the mission only selects compiled layers (§1.3). | 26 §2.2/§9.3; 29 §3.5 | Partly: doc 26 variation axes, doc 29 `SideOpGenerator`, doc 28 MC11/MC15. |
| cw08 | Dispatch tiers, elite detachments by promotion, per-op risk tiers (`…/campaigns.md#L2041-L2216`; `…/enhanced-campaign-plan.md#L239-L321`) | adapt | `CardTemplate.dispatch` (HeroRequired, HeroPreferred, TeamViable, CommanderVariant) plus `fallback_variant`. Promotion changes a roster member's class at camp (the `_cls` scalar, applied by `createUnit` at spawn; on `Cwa199`, until PR01–PR03 pass, doc 29's fallback of one pre-placed non-playable slot per class variant, chosen by presence [F12]) and uses up a line slot. The Commit risk tier is only a badge plus the detect-only restart ledger (PR19), because the campaign book allows restarts [V doc 18 §6.2]; a real lock needs CE extension E8. Lint SL21. | 29 §3.2/§3.5/§6; 19 §4 | Partly: `SquadSelection`, Ironman preset. |
| cw09 | Perk choice at debrief; presentation variants (`…/campaigns.md#L1744-L2010`) | adapt | `PerkChoice` offers 2 perks drawn from a catalogue limited to engine levers: a `setSkill` step, pool kit, a radio support item, a camp action, or a branch flag. Effects with no engine lever ("detection −20 %") are rejected. Presentation: `setIdentity`/`setFace` [V GSE#L1221-L1223]; civilian cover as a class variant plus `setCaptive` [V GSE#L1220]. Lint SL24 (a perk with no consumer). | 29 §1.3/§3.2; 26 §5.2 | Partly: doc 29 `PromotionTable` and perks. |
| cw10 | Strategic debrief from state diffs; in-game war diary (`…/campaigns.md#L2258-L2283`; `…/enhanced-campaign-plan.md#L1830-L1850`) | adapt | Each `Effect` variant has a template sentence. The compiler renders them as hidden `OBJ_` debrief lines that the finisher reveals (≤ 7 narratives per mission [V F10]). The diary is one hidden line per notable event in the camp briefing, revealed from state. No model is involved. The practical `OBJ_` cap is [U]. | 29 §4.3; 19 §7.3; 26 §7.1 | Partly: the journal exists in the simulator only. |
| cw11 | Collectible intel fragments with threshold payoffs (`…/enhanced-campaign-plan.md#L654-L767`) | adopt | Module `Fragments`. A prop with `addAction ["Read", script]` (exactly two elements [V doc 31 §4.5]; 1.99 [U] per F14), or a trigger zone as IC itself uses, sets `cmp_frag_k`. Thresholds (1, 3, 5) reveal a card, pre-mark a position or pick a briefing variant. The story thread is a doc 25 §8 row. The model writes 2–3 sentences per slot; code places the props. Lint CF19. | 26 §5.2; 25 §8.1 | No. |
| cw12 | Teaching order: meet characters in play first, explain each mechanic at first use, layered unlock (`…/enhanced-campaign-plan.md#L15-L57, #L407-L436`; `ICD:src/decisions/09d/D070-asymmetric-coop.md#L656-L745`; `…/09g/D065/D065-overview-commander-school.md#L137-L151`) | adopt | A compiler-computed `TeachingSchedule` (§1.5). Lints CF20 and CF21. Opener pattern: no camp or cards until a rescue op succeeds. Merges le "first-use explainers". | 26 §9.4/§10; 29 §8.2; 33 | Partly: doc 29 Op1 and §1.5 rule 3; doc 28 CF16. |
| cw13 | Campaign extension overlays with insertion modes (`…/campaigns.md#L264-L431, #L706-L722`) | adapt | An extension sidecar references its parent campaign by id and content hash. It adds only nodes and edges (`optional_branch`, `alternative`, `insert_before`, `post_campaign`). The build merges locally: in Preserve mode parent missions stay untouched, plus retrofit routers. Toggles are build options or a first-node "Classic / Enhanced" Choice. Checks: attach points exist, no two extensions use `insert_before` on one node, no cycles. Only the extension ships [U licensing, doc 02]. | 19 §7.6; 27; 02 | Partly: doc 19 §7.6 Preserve mode. |
| cw14 | Twist-pattern catalogue with prerequisites and feasibility (`ICD:src/decisions/09f/D016/D016-branching-world-campaigns.md#L79-L125`; `…/D016-extensions-factions-tools.md#L49-L63`) | adapt | A typed `TwistPattern` (about 20 IC patterns). Each declares the modules it needs, ≥ 2 foreshadow slots and a feasibility tag. Side flips inside a mission need `join` [V GSE#L1296] or `setFriend` (1.99 U, gated on a probe). Code lists up to 5 legal twists per act; the model ranks them (§1.4). Lint CF22. | 26 §3.2/§8.2/§9.1 | Partly: doc 26 twist cards; doc 28 MC17. |
| cw15 | Narrative thread lifecycle (`…/D016-characters-output.md#L172-L213, #L342-L360`) | adapt | The doc 25 §8 Thread row gains `foreshadow_nodes`, a `resolution_guard` (CXL), a `window`, and a status the explorer computes per path. Threads get a Flow-view lane (§1.4). Lint CF23. | 25 §8; 19 §6.3 | Partly: setup→payoff check (doc 25 §8.3). |
| cw16 | Mole: a traitor hidden in the named cast (`…/D016-extensions-factions-tools.md#L151-L175`) | adopt | Optional module. The bootstrap picks `mole` from the cast using the stored LCG. Leaks are presence variants; clue lines are written per (suspect, node) slot; the accusation is a radio or action Choice (≤ 10 radio items, and only while the player leads the group [V F11]) (§1.4). Lint SL22. | 29 §1.3/§3.2; 26 §9.4 | No (doc 29 has only Stress, Bonds and Nemesis). |
| cw17 | Nemesis that adapts to the player's observed tactics (`…/D016-extensions-factions-tools.md#L67-L84`; `…/09d/D043/commanders-and-puppet-masters.md#L14-L78`; `…/09d/D042-behavioral-profiles.md#L32-L65`) | adapt | Bounded tactic counters are committed after each mission (kill counts from `Killed` handlers, probe PR21). A code rule maps the dominant tactic to a counter-variant selected by presence. Code schedules 3–6 appearances, including one reversal. Taunts are intercepted radio lines. Nothing learns at runtime (§1.4). | 29 §1.3/§3.2; 26 §7.3; 25 §8 | Partly: doc 29 optional Nemesis. |
| cw18 | Moral-complexity knob, value-driven reactions, ensemble contrast (`…/D016-extensions-factions-tools.md#L88-L105`; `…/D016-characters-output.md#L1-L50`) | adapt | Intake chip `MoralComplexity` → 0, 1–2 or 3–4 dilemma Choices and an echo depth. Each cast member gets `values` ∈ {Duty, Principle, Loyalty, Pragmatism}. A code-owned reaction matrix turns options into bounded relationship deltas with threshold events. S2 check: ≥ 2 value tags and 1–2 friction pairs, which feed doc 29 Bonds. Dilemmas stay grounded (shell the church or flank it). | 25 §4/§8; 26 §5.2; 29 Bonds | Partly: doc 17 §9 cast sheets, CF05. |
| cw19 | Exodus ("Long March") pattern (`…/D016-extensions-factions-tools.md#L9-L25`) | adopt | Pattern **P10**: 6–12 mostly linear nodes on one island, shown as a route line in the Theatre view. Recruitment is off. The convoy is doc 29's Hangar (≤ 4 scalar slots; the engine has no vehicle pool) and never gates a leg's success (SL19): a leg that lost its vehicles plays a foot variant chosen by presence. A Supplies counter falls each leg. Each leg is a fight / sneak / negotiate Choice that selects an archetype. The finale is Exfiltration (#13), scaled by survivors. Sockets only, no routers. | 26 §9.4 | Partly: P1 Gauntlet. |
| cw20 | Open-ended campaigns: victory/defeat menus, finale readiness, stall breaker, relief (`…/D016-branching-world-campaigns.md#L127-L203`; `…/campaigns.md#L2871-L2898`) | adapt | Typed `VictoryCondition` and `DefeatCondition` become CXL guards on hub edges, and the explorer proves each is achievable. A recovery card comes before the finale if fit soldiers are low. A deterministic catalyst card fires after k turns without progress. After an alive-failure, a disclosed relief variant plays (doc 29 §1.5 rules 2, 3, 10). **Reject** "harder after a fast win": it contradicts clock-driven rather than success-driven scaling. | 29 §1.5/§3.2/§3.3/§5.2; 26 §9.4 | Partly: finale via Story4, replacement floor. |
| cw21 | Sectors: features, adjacency, war damage, posted soldiers, deterministic enemy strategic AI (`…/D016-branching-world-campaigns.md#L285-L361, #L423-L432`; `…/campaigns.md#L1626-L1648`) | adapt | `SectorDecl { features, adjacency, fortification, garrison, war_damage }`, bound to island names. Adjacency feeds op generation: an owned airfield gives a CAS radio item; radar pre-marks enemy positions. War damage = a prologue `(object <id>) setDammage 1` keyed by a sector counter [V `object` GSE#L1142; per-object destructibility U]. A soldier status `Posted`. An enemy policy persona picks targets at commit step 8 with the stored LCG, mirrored in the simulator. | 26 §9.4; 29 §3.2/§3.3/§5.2; 19 §6.7 | Partly: P5 sectors; doc 29 Regions. |
| cw22 | Battle report as Preview telemetry (`…/D016-characters-output.md#L99-L125, #L224-L240`; `…/D042-behavioral-profiles.md#L23-L30`) | adapt | A `PreviewBattleReport` built from committed vars plus harness reads (outcome, per-soldier alive/damage, duration, alarms, loot) [I; read-back per doc 08 §2.4–§2.5]. Kept local and used only with the user's permission, it calibrates the balance lab's per-archetype outcome distributions (doc 29 open question 1). Shares the run record with le12 and le19. | 29 §5.2/§5.3; 08; 21 §11.6 | Partly: outcome tables with no calibration. |
| cw23 | Mission "moments" as typed data (`…/D016-cinematics-media.md#L7-L231`) | adapt | Each archetype gets ≥ 1 `MomentSlot` (reinforcements arrive, a bridge blows, HQ changes the plan). Engine levers: trigger effect fields track/sound/voice/title [V doc 04]; `playMusic`/`fadeMusic` [V GSE#L1012, #L1338]; camera beats (ed09). In-mission choices share the campaign effect vocabulary: reveal a marker, reveal an `OBJ_` [V F9], start a timer, set a committed var. IC's frequency guide becomes generator defaults. Lint MC21. | 26 §2.2/§7; 31; 32; 19 §4 | Partly: doc 26 §7 radio templates. |
| cw24 | Campaign calendar and weather arc; weather-window cards (`…/09d/D022-dynamic-weather.md#L26-L157`) | adapt | Skip IC's surface simulation. A `Calendar` (one day per turn, a season) and a per-act `WeatherArc` compile into each node's Intel weather, fog and date fields [V doc 04 §3.2]. State-dependent overrides run in the prologue (`0 setOvercast x`, `skipTime` [V GSE#L1324, #L1054]); `setOvercast` and `setFog` go together, and rain appears only above overcast ≈ 0.67 [V doc 31 §4.6 row 15]. Card "wait a day for fog": doom +1, and the next op gets the Fog/Night modifiers. `setDate` [V GSE#L1178] is `Cwr`/`Ce` only (doc 31 TL;DR), so a shared side-op template, whose Intel date is fixed, advances the calendar with `skipTime` (24 h × days). | 26 §9.3; 29 §3.2; 04 §3.2 | Partly: a weather enum per mission. |
| cw25 | Support requests, extract-or-stay, three-horizon objectives (`…/D070-asymmetric-coop.md#L101-L326`; `…/campaigns.md#L2342-L2367`) | adapt | Single-player only. Module `SupportRequests`: radio items labelled with uses left via `setRadioMsg` [V F11; CWR] (radio needs the player to lead the group, so an action fallback is required), cooldowns, and `hint` denials that give a reason. Fire missions inherit doc 31 module 4's open point: how a vanilla script makes a real explosion on 1.99 is [U]. Budgets come from doc 29 currencies. "Stay for one more": a revealed optional `OBJ_` with a stated reward and a visible QRF timer, while extraction stays open. AI helicopter landing is [U], with a truck or boat fallback. Lint MC22. | 29 §3.2/§4.3; 26 §9.3; 31 | Partly: the "Fire mission" perk. |
| cw26 | Embedded task force inside a live AI-vs-AI battle (`…/campaigns.md#L2285-L2387, #L2535-L2603`) | adopt | Archetype modifier "Embedded in a live battle" plus a typed `BattleEffect` table mapping a player event to an AI group change: release a held waypoint by synchronisation, cancel a wave, change behaviour or combat mode, grant a support item. All native. A squadmate's death lowers friendly posture; player death is Retry [V doc 18 §5]. The model picks among ≤ 5 layouts. Lint MC23. | 26 §9.3; 31 | Partly: CWC combined-arms precedent (doc 26 §6). |
| cw27 | Diegetic limited rewind (`…/09d/D078-time-machine.md#L10-L23, #L252-L509`; IC marks it Draft) | adapt, low priority | The finisher commits shadow copies `cmp_ck<k>_<var>`. A camp Choice routes to the target mission as a new campaign-book row. It restores gameplay vars but never `tm_uses`, `tm_branch` or allowlisted intel. Butterfly variants are keyed on `tm_visits_<k>`. Engine limits: the target must be in the camp's chapter [V doc 18 L86] or be reached through a router (C11); each rewind target uses one of the camp's 7 sockets; `objects.sav` is never reverted [V doc 18 §6.3], so identity and gear blobs need versioned keys; the shadow copies double the checkpointed variables (C20). Worth building only as a designed puzzle, since the book already restarts rows [V doc 18 §6.2]. | 19 §4/§7; 29 §3.2 | No. |
| cw28 | Legacy veterans and cross-campaign echoes (`…/D016-world-assets-multiplayer.md#L343-L345`; `…/enhanced-campaign-plan.md#L1789-L1800`) | adapt | (a) Static echoes: always-true briefing lines that name events from the companion campaign. (b) An editor-time "Import veterans" reads the user's finished save, on explicit action only, and bakes the chosen survivors into the sequel's starting roster as a build option. Parsing the save is [U doc 18]; a mission cannot read another campaign's `.sqc` [I]. | 29 §3.2; 19 §7.6; 18 | No. |

### 1.1 The card disclosure contract (cw01)

IC requires every offered operation to show a role tag, criticality, urgency, a reward headline plus an exact effect sentence, a failure consequence kept separate from the if-ignored consequence, the reveals, and the downstream consumers. Anything that changes difficulty is quantified: "first wave delayed 180 s", not "better intel" [V `ICD:src/modding/campaigns.md#L751-L827, #L838-L897`].

```rust
// Proposal-only extension of doc 29's CardTemplate (crate ofp-campaign-strategic).
pub struct CardTemplate { /* doc 29 fields: archetype, sites, region, reward, risk, ttl, if_ignored, kind … */
    on_fail: Vec<Effect>,               // failure, distinct from if_ignored (expiry)
    reveals: Vec<CardId>,               // follow-ups offered on success (cw03 chains)
    chain: Option<ChainId>,             // chain-complete edge effect grants the compound bonus
    dispatch: DispatchTier,             // cw08; HeroRequired needs fallback_variant (SL21)
    fallback_variant: Option<VariantId>,
    approaches: Vec<ApproachVariant>,   // e.g. 4-man stealth insertion vs platoon assault
}
pub struct ApproachVariant { layer: VariantId, on_success: Vec<Effect>, label: TextSlot }
// Never stored: effect_detail (rendered by code from Effect) and consumers (computed by the Path Explorer).
```

- **Code renders the effect sentence** from the typed `Effect`, so a weak model cannot misstate a consequence. The model writes only a blurb of 20 words or fewer. Exact numbers go on hint and dialog surfaces (doc 29 §4.3). Radio labels set by `setRadioMsg` stay short [V CWR; 1.99 U].
- **Consumers** are every guard or presence condition that reads the card's variables, as found by the explorer. An empty list is an error (SL24, which extends SL05 and CF04). SL23 warns when effect text has no number or entity token, or when failure and expiry share text but have different effects.

### 1.2 Many small clocks: programs, posture and sectors (cw02, cw04, cw21)

Doc 29 has one doom counter plus Pressure per region. IC's plan tracks capabilities as programs moving through the stages *theory → materials → prototype → test → deployment → sustainment*. Each program has timing windows (early, on schedule, delayed) [V `…/enhanced-campaign-plan.md#L438-L509`], and a ledger entry records owner, state, quantity, quality and `consumed_by` [V `…/campaigns.md#L1461-L1489`]. OPSEC climbs baseline → heightened → active counter-ops → hardened as covert ops succeed [V `…/campaigns.md#L1586-L1615`], and a separate tempo counter rises with every SpecOps launch [V `…/campaigns.md#L2218-L2230`].

- **Storage.** Each program is stored as three ordinals, `pg_<k>_stage`, `pg_<k>_timing` and `pg_<k>_quality`: flat scalars, per doc 19 §4.3. One op shifts timing by at most one phase. The explorer lists the reachable (timing, quality) pairs per consumer, and the author writes variants only for those. SL25 is an error when a shift has no variant. "Corrupt" is an authored misfire variant [I].
- **Posture reacts to tempo, not to success.** We drop IC's success trigger and step `opsec` on the tempo the player chose, disclosed on each side-op card, because doc 29 §1.5 rule 2 scales enemies by the clock rather than by success and rule 10 forbids silent rule changes. At `active_counterops` a Critical counter-ops card appears. CF07 and SL01 guard against a tempo death spiral.
- **Enemy strategic policy** (aggressive, defensive or opportunistic) is code-owned, uses the stored LCG and runs identically in engine and simulator. The balance lab validates endgames by asset bundle, not by every permutation [V `…/enhanced-campaign-plan.md#L630-L638`], matching doc 19 §2.3.
- **Visibility.** Every program and posture appears on the status card and as a briefing bucket line (SL04).

### 1.3 Generated side ops from kits (cw07)

An IC op is assembled from a site kit, an objective module, at least 2 ingress routes plus 1 exfil, a security tier with patrol graphs, and exactly one complication. Validation checks that the objective is reachable, that a stealth route and a loud route exist, and that evac stays reachable after the alarm. The target is 10–15 minutes, 20 at most. The seed and choices are persisted when the card first appears; hand-made landmark ops are used once [V `…/campaigns.md#L433-L600`].

- **Slots.** `SiteRef` from the island feature index (doc 26 §2.2), `ObjectiveModule`, `IngressModule` ×≥ 2, `ExfilModule`, `SecurityTier`, and one `Complication` from: dawn deadline, QRF countdown, wounded VIP, fog front, moving convoy. Everything is chosen at edit time, so a failed validation is a compile error and no runtime fallback exists.
- **Validators** [I; they need the terrain index]:
  - route reachability on the island graph;
  - "stealth route exists": the route keeps its distance to every patrol graph above a detection band;
  - alarm-to-exfil feasibility against the QRF timer.

  The two-route rule reuses doc 28 **MC11/MC15** instead of adding a new lint. MC20 adds only "> 1 complication" and "estimated duration > 20 min".
- **The model** picks among ≤ 5 feasible combinations; code owns placement.

### 1.4 Narrative machinery the harness can prove (cw14–cw17)

The common rule is that code schedules and the model fills one slot.

- **Threads (cw15)** have statuses Foreshadowing → Rising → Active → Resolved or Abandoned [V `…/D016-characters-output.md#L342-L360`]. The explorer computes the status per path; the model never sets it. CF23 warns on three things: a payoff reached with fewer than k foreshadows, a thread still Rising at an ending (unless marked open), and an Abandoned thread whose setups still make promises. Digests include only the threads open at the current node (doc 25 §8.2).
- **Twists (cw14).** IC's catalogue includes backstab, defection offer, double agent, secret weapon, "the war was a lie", mentor's fall, rescue the captured, temporary alliance and others, with 2–3 missions of foreshadowing [V `…/D016-branching-world-campaigns.md#L79-L125`]. "Make the betrayer likeable first" comes from a different file [V `…/D016-characters-output.md#L83`], as does the traitor's trust-building first 30–40 % of a campaign [V `…/D016-extensions-factions-tools.md#L163`]. CF22: the betrayer needs ≥ N positive appearances before the reveal on every path. Doc 28 MC17 already covers foreshadowing inside a single mission.
- **Mole (cw16).** IC derives personality tells from MBTI types [V `…/D016-extensions-factions-tools.md#L161`]. We keep typologies optional (doc 17) and key tells on cw18 value tags instead.
  - Each clue line may mention only its own suspect, checked by CF11's scope rule.
  - Clue coverage must exist for every possible value of `mole` (C21).
  - SL22 also flags a suspect who can die before the first accusation point (C18).
  - A correct accusation leads to hunting the handlers. A wrong one sets roster statuses (Transferred or Arrested) and costs reputation.
- **Nemesis (cw17).** The arc runs introduction → first clash → escalation → reversal → obsession → reckoning [V `…/D016-extensions-factions-tools.md#L67-L84`].
  - Tactic counters are bounded Ints: vehicle vs infantry kills via `Killed` handlers (`addEventHandler` [V doc 31 §5.2]; payload and AI-squadmate kills are probe PR21), alarms raised, night ops chosen.
  - The dominant tactic selects AT teams and mines, an AA group or extra patrols.
  - All of this is authored variants, so it is deterministic and the simulator can test it.

### 1.5 Teaching inside campaigns (cw12, le22–le24)

IC's rules: every named character gets a gameplay or radio introduction before a briefing references them; each early mission introduces one mechanic [V `…/enhanced-campaign-plan.md#L15-L57`], explained at the moment of encounter, once, in the briefing officer's voice, and then trusted to the player [V `…/enhanced-campaign-plan.md#L427-L434`]. Every non-classic feature is taught or hinted at first need [V `…/D065-overview-commander-school.md#L137-L151`].

- **TeachingSchedule.** Covered mechanics: Wounds, Cards, Doom, Recruitment, the Pool, radio choices and roster permadeath. For each, the compiler finds the first node on every path where it becomes visible. It emits an in-character `sideChat` or briefing Notes paragraph plus one hint there, gated by `cmp_taught_<m>` so it fires once per run. The text is a pinnable slot (doc 25). Doc 29's Op1 ("teaches extraction choices") becomes one instance of this schedule.
- **Lints.** CF20 (warn): a character is referenced before their first in-play appearance on some path. CF21 (info): a mechanic is used before its teaching slot. The pacing lints are in le22.

## 2. Editor and creator UX (ed)

| ID | Idea (IC source) | Verdict | Plotroom translation | Target | Already covered? |
|---|---|---|---|---|---|
| ed01 | Named zones shared by triggers, modules and scripts (`ICD:src/decisions/09f/D038/D038-core-architecture.md#L139-L159`; `…/D038-triggers-waypoints.md#L5-L17`) | adapt | A sidecar `Zone` (name, rect or ellipse, angle, colour, tags). The compiler copies its geometry into every trigger that references it (`a`, `b`, `angle`, `rectangular` [V doc 04 L311-L313]). For scripts it emits one detector trigger `zone_<name>`, so a script can test `unit in list zone_<name>` [I]. How `list` refreshes and whether `in` exists on 1.99 are [U doc 19 F4] (§2.2). | 31; 04; 03; 05 | One bullet in doc 17 §15. |
| ed02 | Logic outliner, typed mission variables with no-code operations, read-only flow graph (`…/D038-core-architecture.md#L223-L271`; `…/D038-campaign-editor.md#L181-L190`) | adopt | Mission-scope Bool, Int (±2^24 [V C17]), Float, Text and Timer (stamped from `time` [V GSE#L859]). Initial values go into the generated `init.sqs`. Set / Add / Toggle / Start-timer rows compile into `expActiv` [V doc 04 L298, L326]. Folders and colours are sidecar metadata. The doc 23 checker derives "Set in / Read in" statically. The flow graph covers triggers, `synchronizations[]` [V doc 03 L65], waypoints and variables. Globals used only in hand-written scripts appear as Opaque. | 31; 19; 23; 09 | Campaign scope only (doc 19 §6.3); doc 09 S8. |
| ed03 | Module catalog compiled to vanilla content (`…/D038-triggers-waypoints.md#L102-L153, #L257-L266`; `…/D038-media-validation.md#L519-L563`) | adapt | CWA has no engine modules [I]. A Plotroom module is an editor object with a typed schema and a deterministic lowering to triggers, logics, waypoints, markers, `description.ext` classes and namespaced SQS. Module definitions are T0 data: a schema plus a minijinja template (doc 22 §7). Each module is tagged Easy or Advanced (§2.1). | 31; 22; 17; 26 | Now largely in doc 31 §4 (20-module wave 1, native-first lowering, compiler-owned singletons); reconcile §2.1 against it. |
| ed04 | Two-way ladder: Show generated, Eject, Lift (`…/D038-core-architecture.md#L161-L221`; `ICD:src/decisions/09c/D066-cross-engine-export.md#L135-L157`) | adapt | Show = a read-only view with a source map. Eject = explicit, undoable and one-way; the output becomes hand-owned and pinned. Lift = a finite pattern table with golden tests proving that lowering then lifting returns the original. Unmatched code stays verbatim with an Opaque badge. Merges the mo row "pattern-based lowering and lifting" (§2.1). | 31; 32; 19 §7.6; 23; 25 | Doc 19 §7.6 (campaign level); doc 31 §8 (recognisers, "replace" only when re-emission reproduces the original, else "wrap"; ejecting). |
| ed05 | Difficulty chip, Checkpoint, Mission Timer (`…/D038-triggers-waypoints.md#L127-L130`; `…/D038-core-architecture.md#L132-L137`) | adopt | **Difficulty chip** (All, Cadet, Veteran): compiles to `presenceCondition` `cadetMode` or `!cadetMode`, ANDed with any existing condition [V GSE#L861; 1.99 I]. The engine evaluates presence only for non-playable units, empty vehicles and objects [V F12], so playable units cannot carry the chip; triggers have no presence field and get `cadetMode` ANDed into their condition instead. **Checkpoint**: `saveGame` [V CWR; 1.99 "likely", risk CSV L17], which overwrites the campaign's single save slot (doc 18). **Timer**: a generated SQS countdown within the SQS limits [V F6/F7]. Lint MC29: a checkpoint in a loop, in MP, or more than once per phase. | 31; 24; 26 | Knobs only. |
| ed06 | Phase-transition presets, the OFP form of IC's Map Segment Unlock (`…/D038-triggers-waypoints.md#L307-L404`) | adapt | A sidecar `Phase` with an activation, members and on-enter actions. A one-click scaffold chains: objective done → radio line → reveal markers (1.99 timing U, PR09) → release a group through a synced waypoint (or `createGroup` [V GSE#L1182] on CWR) → a new `OBJ_` [V doc 04 L520]. No destructive layer deactivation. Lint MC24 (§2.2). | 31; 26; 19 | No. |
| ed07 | Outcome priority, standalone preview, outcome lints; detour-and-return for IC's sub-scenario portal (`…/D038-triggers-waypoints.md#L37-L100, #L354-L386`; `…/D038-media-validation.md#L267-L286`) | adapt | **Priority column** showing vanilla's implicit order: player death, then any LOOSE, then END1..6, where `END<n>` fires only when all its triggers are active [V doc 18 L181-L183]. The finisher breaks same-tick ties. **Standalone Preview** shows "Outcome fired: X → would commit {…}" instead of routing. **Lints** extending C13: no outcome (error), outcome not in the graph (error), single outcome (advice), duplicate at equal priority (error). **Detour**: the parent ends with an outcome, a child mission plays, and "part 2" rebuilds state from a typed payload (`saveVar`, `saveStatus`, destroyed objects). Positions travel as `saveVar` arrays, because `saveStatus` stores no transform [V doc 18 §6.3], and `objects.sav` is never reverted by a book restart. The UI shows the cost of 2 extra loads and 2 extra book rows. | 19; 18; 26 | Doc 19 §6.6, C13. |
| ed08 | Route overlay and shared named routes (`…/D038-triggers-waypoints.md#L155-L266`; `ICD:src/architecture/sdk-editor.md#L113-L130`) | adapt | The faithful drawing stays the default (doc 05 §5.3). An optional overlay encodes type by dash and shape, and draws the selected route bright with arrows. A sidecar `NamedRoute` can be assigned to a group: it is copied into ordinary waypoints, and later edits propagate after a diff. This also gives Wilco a vocabulary ("patrol along north_road") (§2.2). | 05; 31; 03 | Native semantics only. |
| ed09 | Cinematic timeline compiled to one camera SQS (`…/D038-media-validation.md#L7-L174, #L256-L265`) | adopt | Typed steps compiled with `#step_N` labels, Preview-from-step, a skip flag and end-holding rules (§2.3). Lint MC26. | 32; 31; 08; 18 | Doc 31 §6 (engine facts, timeline model, compile contract); only the step-label and Preview-from-step parts are new here. |
| ed10 | Trigger camera-scene presets (`…/D038-media-validation.md#L91-L132`) | adopt | Simple shots use the trigger's native `cameraEffect`/`cameraPosition` [V doc 04 L336-L337]; richer ones generate an ed09 Cinematic. The interrupt policy compiles to `alive` guards with a text fallback. Camera scripts run locally while triggers fire on every machine [I], so "local player only" adds a guard. Lint MC25: an MP camera scene with no declared audience. | 32; 31; 04 | No. |
| ed11 | Radio Message module with portrait and delivery queue (`…/D038-triggers-waypoints.md#L140-L141`; `…/D038-media-validation.md#L44-L46, #L239-L254`) | adapt | Speaker, channel, stringtable key, optional sound and portrait compile to `CfgRadio` (sound plus `titles[]` [V doc 04 L485]), played with `sideRadio`/`groupRadio`/`vehicleRadio` [V GSE#L1269-L1271]. The portrait is `RscTitles` shown via `cutRsc` [V GSE#L1003]. A generated queue orders lines by priority, spacing and cooldown, because triggers that fire together overwrite each other's titles [I]. Outside MP all radio needs a living player, and in Intro/Outro sections group and vehicle radio are inaudible [V doc 31 §6.1], so lines there lower to `say`. | 32; 26; 15; 22 | Doc 15 §8.4 (dialogue rows → CfgRadio); doc 31 module 19 Conversation. |
| ed12 | Music cues, mood playlist, ambient sound zones (`…/D038-media-validation.md#L185-L237`) | adapt | A cue is the trigger's `track`, or `playMusic` with a `fadeMusic` crossfade [V doc 04 L342; GSE#L1012, #L1338]. The optional mood playlist (off by default) switches on the leader's `behaviour` [V GSE#L995; heuristic I] with hysteresis. An ambient zone is an ed01 zone plus `soundEnv`/`soundDet` [V doc 04 L340-L341; looping U]. | 32; 04 | No. |
| ed13 | Localization and text-fit workbench (`…/D038-media-validation.md#L288-L306, #L500-L517`; `ICD:src/architecture/ui-theme.md#L10-L50`; `…/09c/D068-selective-install.md#L163-L215`) | adapt | Key-usage lookup across sqm, briefing, `description.ext` and SQS. Coverage per language × branch from the Path Explorer. Pseudolocalization (+30–40 % length, glyphs within the legacy codepages). A text-fit preview of hint, titleText, subtitles and briefing at 4:3 and widescreen with the game fonts (doc 05 §6). A per-cell `translation_source` (human, machine, machine-reviewed) kept in the sidecar, never in the CSV. The preview applies the engine's fallback rules [V doc 04 §7]. Merges the mo "language matrix" row. RTL is skipped [U]. | 04; 05; 23; 22 #2; 33 | Doc 22 #2 translator plugin. |
| ed14 | Export Readiness screen, validation presets, headless CLI, budget meter (`…/D038-media-validation.md#L344-L456`; `…/09f/D020-mod-sdk.md#L52-L67`; `…/D066-cross-engine-export.md#L317-L341`) | adopt | §2.4. Merges the mo row "one validation engine". | 17; 09; 23; 08; 27 | Doc 17 L275, §17 #3; doc 09 S2/S4; doc 28 MC06. |
| ed15 | Retarget workbench: per-object badges, palette gating, fidelity report, import report (`…/D038-onboarding-platform-export.md#L82-L91, #L407-L516`; `…/D066-cross-engine-export.md#L27-L37, #L305-L315`) | adopt | §2.4. Merges the mo row "target-aware authoring". | 23; 24 §5.5; 27; 19 | Mission-level Requires badge. |
| ed16 | Stable IDs re-associated after external re-saves; git merge driver; per-source views (`…/D038-core-architecture.md#L283-L366`) | adapt | Object `id`s in `mission.sqm` are renumbered on save [V doc 04 L29], so ULIDs live in the sidecar. After an in-game editor re-save, objects are re-associated by class, position within a tolerance, name and group, with a confidence report and manual fix-up. Output follows the canonical Serialize order (doc 04 L248). `plotroom merge-sqm` is a semantic three-way merge driver; `plotroom diff` supports reviews. View toggles: by source (doc 27 provenance) and "changed since import". | 04; 17; 25; 27 | Doc 17 L201-L202; doc 25 L56. |
| ed17 | Test range and Preview quality of life (`…/D038-media-validation.md#L359-L362`; `…/D038-onboarding-platform-export.md#L383-L405`) | adapt | One click stages a mission with the player at the cursor, a chosen class beside them and no logic; it works on every target through staging (doc 08 §4). Speed ×2 and ×4 via SP-only `setAccTime` [V GSE#L1071; allowed values U]. Restart means relaunch [V doc 08 L468]. A banner shows the resolved mod set. | 08; 09; 27 | Doc 17 §15. |
| ed18 | Director panel, capture back, route recording (`…/D038-game-master-replay-multiplayer.md#L1-L127`) | adapt | Remastered and CE only; the harness does not exist on 1.99. Typed, ephemeral Director templates (doc 24 §5.4 [V doc 24 L488]). **Capture back** turns in-game positions into undoable EditorCommands (doc 09 S13, CO2). **Route recording** samples `getPos vehicle player` at 1–2 Hz, simplifies the path (Douglas–Peucker, road snapping) and emits MOVE waypoints into an ed08 route. Loopback only, because the harness has no authentication [V doc 08 L471-L473]. | 08; 24; 09; 31 | Doc 08 §4.4; doc 09 CO2. |
| ed19 | Multiplayer authoring: slots panel, per-side objectives, templates, multi-client preview (`…/D038-game-master-replay-multiplayer.md#L181-L354`) | adapt | Slots per side with `respawn`, `respawnDelay`, `disabledAI` and `aiKills` [V doc 04 L476-L478]. Per-side briefings are [U probe]. Coop, CTF, C&H and DM compositions. Preview runs a local dedicated server plus N clients (doc 08 P4). Locality lints. Asymmetric roles and live-GM co-op are skipped. | 08; 09; 31; 04 | Doc 08 §4.5; doc 09 CO13. |
| ed20 | Mission media bin with import normalisation (`…/D040-asset-studio.md#L80-L172`; `…/09c/D075-remastered-format-compat.md#L64-L70, #L241-L249`; `…/09e/D049-workshop-assets.md#L48-L103`) | adapt | Covers only the mission's own media. Trim, normalise and convert once to what the target reads: `.ogg` dispatches to Vorbis [V doc 07 §12]; OGG on 1.99 is [U], so WAV is the fallback; which picture fields take JPG is [U]; there is no PAA encoder. The original stays in the project. Adds `.lip` (doc 09 CO7), auto-registration of CfgSounds/CfgMusic/CfgRadio, where-used, and provenance shown at Export Readiness. Imports are decoded with widely fuzzed crates; our own decoders stay capped (doc 27 §4.10). | 04; 07 §12; 22; 17; 09 | Doc 17 §11; doc 09 CO7. |
| ed21 | Accessibility overlay (`…/D038-onboarding-platform-export.md#L437-L459`) | adapt | The classic palette stays the default. The overlay adds outline glyphs per side (colours from `colorFriendly` and similar [V doc 05 L320, L340]), dash patterns for sync vs waypoint links, hatching per trigger type, high contrast, UI scale, keyboard reach and sticky modes. Screen readers work through AccessKit (doc 06 §4.7). | 06; 05 | AccessKit only. |
| ed22 | Per-origin undo lanes (`…/D038-game-master-replay-multiplayer.md#L22`) | adapt | "Undo last Wilco change" (and one per plugin) reverts that origin's latest group when its semantic diff commutes with later edits; otherwise it offers "revert as a new change" with a conflict view [I]. Director actions get an ephemeral lane. | 21; 22; 17 | Origin-tagged undo groups (doc 22 L367). |

**Merged into other rows:** veteran onboarding → le02, le08, le09; live tours → le05; embedded manual → le10; training-mission kit → le21; credits block → mo13. The skipped rows (D056 replay import, measured playtest, platform extras) are in §6.

### 2.1 Modules and the two-way ladder (ed03, ed04)

| Module | Lowers to | Evidence |
|---|---|---|
| Guard position | GUARD waypoint plus a `WestGuarded`/`EastGuarded`/`GuerGuarded` trigger | [V doc 04 L725] |
| Patrol | CYCLE waypoints, optionally from an ed08 route | [V doc 04] |
| Probability group | Per-unit `presence` / `presenceCondition` | [V F12] |
| Reinforcements | A group held by a waypoint synchronised to a trigger. In the code a sync member's `active` flag means "still blocking": members start blocking (`CWR:AI/AICenterImpl.cpp#L748-L760`), a trigger clears its flag on activation and sets it again on deactivation (`CWR:World/Detection/Detector.cpp#L1384-L1389`, `#L1512-L1523`), and an AI group at a synced waypoint waits while any other member still blocks (`CWR:AI/AIArcade.cpp#L309-L369`, `#L815-L855`; `AICenterImpl.cpp#L786-L807`). Player-led groups are not auto-held (`AIArcade.cpp#L832`), and a trigger that deactivates re-arms the hold. `createUnit` on CWR. | [V by reading; runtime and 1.99 U] |
| Objective (destroy, defend, escort) | Trigger plus `objStatus` plus a briefing `OBJ_` line | [V doc 04 L520] |
| Timer, checkpoint, difficulty; radio, music, camera; training; support | ed05; ed11, ed12, ed10; le21; cw25 | see rows |

- **Children are generated artefacts.** They carry a badge and stay read-only until ejected; the Compiled overlay lists them. Wilco only fills parameters, which suits weak models. Plugins add modules as T0 data, with no code (doc 22 §7).
- **Lift runs only on import or on request**, and shows a semantic diff before applying. First patterns: countdown hint loops, `objStatus` + `setMarkerType` phase blocks, `camCreate … camCommit` scripts, and Guarded-by setups. Lift is the mission-level twin of doc 19 §7.6 Adopt.

### 2.2 Sidecar objects that compile away (ed01, ed06, ed08)

Zones, phases and named routes follow one contract [I]:
1. They live only in the `.ofpeditor/` sidecar, and `mission.sqm` receives plain triggers, waypoints and markers.
2. An edit reaches every dependent in one undo group.
3. "Where used" and the Compiled overlay explain each object, for example "zone bridge_xing → 3 triggers + 1 detector".
4. After a vanilla re-save the dependents survive as plain content, and ed16 re-association either restores the links or reports them as detached.
5. Target badges (ed15) judge what the object compiles to.

Phase lint MC24 (error) fires when, after some phase, the player has no active objective or no reachable outcome. It also fires when a member is referenced before its phase, or a released group is synced to a trigger that can never fire.

### 2.3 Cinematic timeline (ed09)

- **Steps:**
  - camera shot (position, target, FOV, duration);
  - wait;
  - text line (stringtable key, title or cut layer);
  - radio line (lowered to `say` inside Intro/Outro sections, where group and vehicle radio are inaudible [V doc 31 §6.1]);
  - sound (`say` [V GSE#L1266]);
  - music (`playMusic`/`fadeMusic`);
  - weather (`setOvercast`);
  - letterbox (`showCinemaBorder` [V GSE#L1037]);
  - input lock (`disableUserInput`, an unclamped nesting counter, so the compiler emits balanced pairs on every exit path [V doc 31 §6.1]);
  - set variable;
  - raw SQS as the escape hatch.
- **Compilation:** one SQS script with a `#step_N` label per step: `camCreate` [V GSE#L1342] → `cameraEffect` → `camSetTarget`/`camSetPos` → `camCommit` [V GSE#L1351] → `@camCommitted _cam` [V GSE#L1065]. It must stay within the SQS limits [V F6/F7] and follow doc 31 §6.3's compile contract (no `camSetDir`/`camSetBank`/`camSetDive`/`camSetFovRange`; one FOV per commit; terminate the effect before `camDestroy`). Starting at step N skips the setup of earlier steps, so each step records the camera, border and input state it assumes and the staged copy restores it first [I]. "Preview from step N" stages a copy whose init starts the script at that label (doc 08 staging).
- **Skip and end rules.** No native in-mission skip is known [U]; an optional radio Skip item sets a flag checked between steps. Camera and title-layer effects hold the mission end unless `forceEnd` is called [V doc 18 L185-L189], so text defaults to the cut layer. MC26 flags an outcome that can fire during a cinematic. Doc 28 MC19 already covers scene caps, skippability and music under fire; reuse it. FMV is skipped [U].

### 2.4 One validator, three surfaces, per-object targets (ed14, ed15)

- **Export Readiness** runs before PBO, MPMissions or campaign export. It aggregates:
  - validation results and the Requires badge;
  - the dependency manifest;
  - missing metadata (`briefingName`, `overview.html`);
  - provenance and AI disclosure;
  - the licence audit (mo13) and the D9 guard (mo10).

  Errors block export but never Save.
- **Presets.** Quick: static checks in under 2 s. Export: adds a `--check --test-mission` smoke run on Remastered or CE [V doc 08 L52]. Campaign: adds the Path Explorer.
- **CLI.** `plotroom check <mission|campaign|project>` prints JSON, and `plotroom export --dry-run` checks an export without writing it. This is a product binary for humans and CI, not a Wilco tool: Wilco has no shell and calls the same validator in-process (AGENTS.md).
- **Budget meter** from target data: groups per side vs MaxGroups [V doc 04 L411], 12 units per group, triggers, generated script lines, `.sqc` growth (C20). This is a single implementation shared with doc 28 MC06.
- **Per-object badges.** Green: runs on the target. Yellow: a fallback is substituted. Red: impossible, for example a CE-only verb, or `createGroup` on `Cwa199` (a `Cwr`/`Ce`-only command in doc 31 §4.6). Red items are greyed out in the palette.
  - "Retarget…" does a dry run, shows a fidelity report and takes a rollback snapshot.
  - Importers end with an honest report, for example "312 objects; 4 classes missing, kept as placeholders".
  - Unlike IC, retargeting never flattens state lossily: every target has `saveVar` and `objects.sav` (docs 18, 19).

## 3. Learning and engagement (le)

| ID | Idea (IC source) | Verdict | Plotroom translation | Target | Already covered? |
|---|---|---|---|---|---|
| le01 | Payoff-first lesson order; skip by demonstration (`ICD:src/decisions/09g/D065/D065-overview-commander-school.md#L51-L178`; `ICD:src/player-flow/tutorial.md#L11-L28`) | adapt | §3.1. | 33; 21 §11.4 | Doc 21 §11.4 Drill, ordered bottom-up; doc 33 §5 Drill (sandbox, test-out, curriculum). |
| le02 | "Coming From" gate and two-register wording (`…/09f/D038/D038-onboarding-platform-export.md#L22-L52`; `…/D065-new-player-pacing.md#L9-L34`; `…/player-flow/first-launch.md#L193-L211`) | adapt | One non-blocking first-run question on doc 33's single dismissible welcome card (doc 33 §2 principle 5: no start-up tour): New / OFP-CWA 2001 editor / Arma 3 Eden / Scripter / Skip. It sets the Easy or Advanced default (doc 09 M2), the keymap (le06), tip categories, the first tour, Rosetta tooltips and Wilco's verbosity. Stored in user prefs only. Each tip has a newcomer and a veteran register. Target: an OFP veteran is productive within 30 min [U until measured]. | 33; 09 | No. |
| le03 | Smart Tips engine (`…/D065-hints-schema.md#L1-L274`; `…/D065-hints-tips-triggers.md#L1-L136, #L338-L392`) | adopt | §3.2. | 33; 22 | Doc 09 S18 asks for hints; doc 33 §4.8 has contextual tips, a tips inbox and "never repeat once dismissed". |
| le04 | Attention budget and mastery-based cadence (`…/D065-postgame-api-integration.md#L86`; `…/D065-hints-tips-triggers.md#L394-L410`; `…/D065-new-player-pacing.md#L322-L368`) | adopt | §3.2. | 33 | No. |
| le05 | Live guided tours validated by editor events (`…/D038-onboarding-platform-export.md#L95-L339`; `…/player-flow/sdk.md#L28, #L83`) | adopt | §3.1. Merges the ed tours row. | 33; 21 §11.4; 22 | Doc 17 L152, as an analogy only. |
| le06 | Semantic action catalog and keymap profiles (`…/D065-new-player-pacing.md#L51-L80`; `…/D038-onboarding-platform-export.md#L40-L52`; `…/player-flow/sdk.md#L73`) | adapt | Stable action IDs (`mode.units`, `mode.sync`, `preview.run`) shared by the command registry, palette, tips, tours and manual. Profiles: "OFP 2001 Classic" (F1–F6; keypad 5 centres on the player [V doc 09 L103, doc 03 L39]), "Eden-like" and "Plotroom default"; a user profile is stored as a diff. Teaching text uses `{action:mode.sync}` tokens, so it names the user's real key. Conflict: IC uses F1 for context help, but F1 is Units mode in the original editor, so the Classic profile uses hover or `?` for help. | 33; 09; 06 | Doc 09 M1; doc 03 L39. |
| le07 | Shortcut reference and "What changed" cards (`…/D065-new-player-pacing.md#L231-L272`; `…/player-flow/tutorial.md#L67-L69`) | adopt | The overlay is generated from le06, so it always matches the active profile. An optional pinned strip of mode keys unpins after N uses. After an update, one-time "What changed" cards are built from a versioned changelog file; they can be replayed from Help. | 33; 09 | Doc 09 S18. |
| le08 | Terminology Rosetta Stone and a "coming from the original editor" page (`…/D038-onboarding-platform-export.md#L54-L70`; `ICD:src/architecture/install-layout.md#L182-L203`) | adopt | §3.3. | 33; 31; 32; 03 | Partly: doc 33 §4.5 and curriculum C6 "Coming from later editors". |
| le09 | Migration cheat sheets triggered by lint findings (`…/D038-onboarding-platform-export.md#L72-L80`) | adapt | The first `remoteExec` or `private _x = …` in a Cwa199 script raises a one-time tip ("not in CWA 1.99; the CWA way is …") that links to an "Arma 3 → CWA" page. `params`, `compile`, `spawn`, `execVM` and `isNil` get "not in this engine" on every target, since no CWR build registers them [V doc 14 L98]. `remoteExec` raises Requires to CWR [V doc 24 L495]. The first SQS file raises "SQS vs SQF". One toggle turns all such tips off. This follows doc 21 §10.2's warning about drift toward Arma 3 idioms. | 33; 23 | Agent-side only (doc 21 §10.2). |
| le10 | Single-source Standing Orders with context help and lint anchors (`…/D038-onboarding-platform-export.md#L341-L381, #L455`; `…/player-flow/sdk.md#L32-L36`) | adopt | §3.3. Merges the ed "embedded manual" row. | 33; 21 §10; 23; 09 | Mostly: doc 33 §3 concept registry (one source for tooltip, F1, manual, lint links, tutorials and agent); doc 21 §10.1; doc 09 S6/S18. |
| le11 | Armoury pages built from the user's install (`…/player-flow/encyclopedia.md#L1-L37`) | adapt | Generated at import from the loaded config: class, side, crew seats, weapons and magazines, armour and addon provenance, plus our descriptive overlay (doc 17 §7.2). Right-click → "Open in Standing Orders". Built locally, never redistributed, and follows the active mod set (doc 27). | 33; 27; 21 §10 | Agent catalog pack only. |
| le12 | Post-Preview debrief card (`…/D065-postgame-api-integration.md#L5-L43`; `…/player-flow/post-game.md#L36-L47`) | adapt | Code builds it from the Preview log and harness state: END code and time, script errors ("Script error at" [V risk CSV L27]), objectives completed, and harness reads on CWR/CE [V doc 08 L24-L25]. It shows one positive tip and at most one improvement, for example "END1 fired at 00:42: the win rule may fire before the player acts". Each tip links to a manual page. It works with AI off; the numbers always come from code. | 33; 21 §11.1; 08 | The readiness coach runs only before Preview. |
| le13 | Preview postcards (`…/09d/D077-replay-highlights.md#L10-L20, #L114-L126`; `…/player-flow/post-game.md#L122-L147`) | adapt | OFP has no replays. On CWR/CE the harness `screenshot` [V doc 08 L24-L27] fires when generated flags show an objective done or an END fired; the flags are polled through a read-only eval template (doc 24 L488). Screenshots go to the sidecar, never the PBO, and appear as thumbnails on graph nodes and behind "Continue". There are none on 1.99. | 33; 08; 19 | No. |
| le14 | Creator ribbons computed by validators (`…/09e/D036-achievements.md#L13-L79`; `…/D065-postgame-api-integration.md#L271-L287`) | adapt | Local only and can be switched off. One ribbon per Drill lesson, plus "First Preview", "First branch", "Ending proved reachable" (a Path Explorer witness) and "Lint-clean on all targets". A few are hidden. Raw counts are never rewarded, and only clean runs count (le19). | 33; 21 §11.4 | Doc 21 §11.4 (checks double as achievements). |
| le15 | Player-facing commendations compiled into campaigns (`…/D036-achievements.md#L47-L79`; `…/player-flow/post-game.md#L55-L120`) | adapt | CWR never selects the native Awards cutscenes; only penalties play [V doc 18 L578; 1.99 U]. So a `Commendations` module: the finisher evaluates data-defined medals from counters (alive, `getDammage`, kills), stores them as `saveVar` scalars and reveals them as hidden `OBJ_` debrief lines [V F10]. A final service-record Cutscene node or router intro summarises them; chapter cutscenes see no vars [V doc 18 L37]. | 29; 26; 19; 31 | No. |
| le16 | Editor feel presets; preference vs project split (`…/09d/D033-qol-presets.md#L3-L86, #L188-L220`; `ICD:src/architecture/qol-toggles.md#L1-L20`) | adapt | Presets: "OFP 2001 Classic", "Plotroom Modern" and "Eden-like", with every overlay individually toggleable. Preferences never change mission output. Choices that do (target profile, min-version badge, mod set) live in the project and show on its badge. Presets are shared via mo17 packs. | 09; 33; 06 | Doc 09 M1/M2; doc 17 §15. |
| le17 | No dead-end buttons, extended to every refusal and gap (`…/D033-qol-presets.md#L232-L257`; `ICD:src/17-PLAYER-FLOW.md#L42-L50`; `…/D068-selective-install.md#L251-L276, #L350-L360`) | adopt | Any greyed-out or refused action opens an inline panel explaining what is missing, why, and what it costs, with a minimal fix and a full fix. Cases: no game detected → [Locate game]; a 13th crew seat → [Split group]; mods missing → a list with sizes and deep links to CWR's MODS manager, Game Schedule or Fwatch (Plotroom never downloads mods, doc 27 OQ6); island not in the mod set (D7); a CWR-only feature on a Cwa199 target → [Switch target] or [Show alternative]; Wilco off → the template path. Merges the mo gaps row. | 33; 17; 21; 27; 08 | Partly: doc 33 §4.4 "Why is this greyed out or invalid?"; AI case in doc 17 §15, doc 21 §6.3. |
| le18 | Command palette as a teaching surface (`…/09g/D058/D058-overview-architecture.md#L64-L219`; `…/D058-commands-catalog.md#L86-L88`) | adapt | Typed autocomplete from catalogs (classes, groups, markers, islands). Each entry shows its key binding. Only commands valid for the current mode, selection and target appear. In Wilco chat, a leading `/` routes to the same deterministic dispatcher with no model call (extends doc 14 L319). | 09; 17; 21; 14 | Doc 09 CO3; doc 17 #1. |
| le19 | Assisted-run flag for Preview debug actions (`…/D058-commands-catalog.md#L355-L365`; `…/D058-cheats-config.md#L15-L22`) | adapt | Each run record carries `assisted_gameplay` and `assisted_cosmetic` flags. Any debug template that changes state (setPos, skipTime, setDate, weather [V doc 24 L488]) sets the gameplay flag. Only clean runs count as "playtested end-to-end", as witness replays or toward ribbons. | 08; 24; 21 §11 | No. |
| le20 | Cosmetic easter eggs (`…/D058-cheats-config.md#L1-L26`; `ICD:src/13-PHILOSOPHY.md#L344`) | adapt, low priority | A few era phrases typed into the palette trigger editor-only gags: radio static, a "1985 paper map" theme, a Wilco persona line. They never touch mission data, and one setting turns them off. | 21 §11.7; 33 | No. |
| le21 | Training kit: Step, Hint, Gate and Skill Check modules (`…/D065-postgame-api-integration.md#L90-L222`; `…/D038-triggers-waypoints.md#L146-L149`; `…/D065-overview-commander-school.md#L335-L406`) | adapt | §3.4. Merges the ed "training-mission kit" row. | 31; 32; 26; 33 | No. |
| le22 | Pedagogical pacing lints (`…/D065-postgame-api-integration.md#L411-L421`; `…/D065-overview-commander-school.md#L59-L65`) | adapt | (a) A new mechanic first appears in a Peak or Finale node: extend doc 28 CF16 to radio choices, permadeath and pool gear. (b) More than one new mechanic in one node on some path: **CF24**. (c) One of the first two nodes routes `lost` to the campaign end: merge into CF14 unless the campaign is tagged hardcore. (d) An intensity jump of ≥ 2 bands with no remedial route from `lost`: **CF25**. (e) Time to first action above N min: info only, since long walks belong to the genre (doc 28 MC03). | 26; 19; 28 | Partly: CF01–CF03, CF14, CF16. |
| le23 | "Second chance" remedial branch (`…/D065-overview-commander-school.md#L75-L126, #L246-L250, #L311-L324`) | adapt | `lost` routes to a node that reuses the same template, with extra units gated on `cmp_retry_<node>` (F12), denser hints and a "regroup" briefing. An optional struggle exit (a timer plus a no-progress flag) costs a spare end code; the UI shows that cost. `lives = -1` keeps the native retry [V doc 18 L87]. | 26; 19; 29 | Partly: failure-forward (doc 26 §6). |
| le24 | First-encounter intel callouts (`…/D065-new-player-pacing.md#L343`; `…/D065-hints-tips-triggers.md#L347`) | adapt | When the player's group first detects a unit of class X, a radio or titleText line plays and `cmp_seen_<class>` is committed, so it fires once per run. Condition: something like `player knowsAbout _u > 1`, with the threshold [U, 1.99 probe]. The line is an era-styled slot. | 31; 26 | No. |
| le25 | Start screen and first run built around a fast first Preview (`…/player-flow/sdk.md#L5-L36`; `…/17-PLAYER-FLOW.md#L7-L74`; `…/player-flow/first-launch.md#L27-L53`; `…/13-PHILOSOPHY.md#L178-L189`) | adapt | First run: detect installs with visible defaults, then one dismissible welcome card holding the le02 question and [Drill] / [Sample mission] / [Just let me edit]; nothing starts a tour by itself (doc 33 §2 principle 5). Start screen: Continue (1 click), New Mission, New Campaign (wizard, doc 21 §11.3), Open, Recent, Tours with completion ticks, Standing Orders. Targets to measure [U]: time from launch to first Preview, and ≤ 1 s from action to feedback. | 33; 08; 09 | Partly: doc 09 S11; doc 21 §11.3. |

**Merged:** the "first-use explainers" row went into cw12. The skipped rows (annotated replay, skill assessment, feedback prompts, cvars) are in §6.

### 3.1 Drill order and live tours (le01, le05)

IC's rule is that every lesson "must have a dopamine moment in the first 60 seconds" [V `…/D065-overview-commander-school.md#L61`]. Exciting and foundational lessons alternate, and each tool is introduced as relief from friction the player has already felt. Doc 21 §11.4's order today is bottom-up: units → groups → triggers → sync → markers → briefing → scripts → campaigns [V doc 21 §11.4].

- **Proposed order:**
  1. L1 "Ambush in a minute": Easy mode; a player squad and an enemy patrol with one waypoint; press Preview, and the user's own mission runs in the real game.
  2. L2 "Make it a mission": one objective plus an END rule.
  3. L3 Groups and waypoints, framed as relief ("you moved 6 units by hand").
  4. L4 Rules and sync.
  5. L5 Markers and briefing.
  6. L6 First campaign: two missions and a branch, previewed.
  7. L7 Scripts.
  8. L8 Roster and persistence (doc 29).

  Non-goal: lessons teach tools and engine limits, not mission-design craft; craft lives in manual pages drawn from doc 28.
- **Test-out.** Mastery counters from real edits mark topics done. A validator-computed capstone (a synced two-group attack plus an END rule) unlocks everything. Lessons run in a scratch mission by default.
- **Tours are data**: a new T0 content type `tour` (doc 22 §7). Each step has a stable logical UI anchor, shared with tips and with Wilco's "show me where"; a spotlight; text; a required action; and a validator over the EditorCommand event stream (`units_placed(side)`, `rule.condition_set`, `sync_exists`, `mission_saved`, `preview_started`).
  - A Preview step completes on the harness `display` event for IDD_MISSION 46 [V doc 08 L257-L259]. On 1.99 Preview is export-and-open, with the user choosing Editor → Load → Preview in the game (doc 08 L362, Option 1), so Plotroom cannot observe it; the step completes when the user confirms [I].
  - Skip advances without validating.
  - Code decides when a step is done, never Wilco. Wilco explains but does not act unless asked.
  - Plugins may ship tours only for their own tools.

### 3.2 Smart Tips with an attention budget (le03, le04)

IC runs every tip through a trigger → filter → render pipeline. Each hint carries its trigger, suppression rules (mastery action with a threshold, cooldown, maximum shows), audience profiles, priority, anchor and dismiss mode. A history table keeps `show_count`, `dismissed` and `mastery_count` [V `…/D065-hints-schema.md#L1-L274`].

```toml
# Proposal-only T0 "tip" item; the triggers are typed editor-state queries, never scripts.
[tip.sync_lines]
trigger  = { ungrouped_units_gte = 8, without_action = "group.create" }
mastery  = { action = "sync.create", threshold = 3 }   # stop after 3 real syncs
limits   = { cooldown_min = 30, max_shows = 3 }
category = "Controls"                                  # Controls, Engine limits, Campaign, Scripting, Wilco, What's new
anchor   = "ui.map.toolbar.sync"                       # the logical UI ID shared with tours
text     = { newcomer = "tip.sync.new", veteran = "tip.sync.vet" }   # stringtable keys
```

- **Editor-state triggers:**
  - `action_refused(crew_seats)` at a 13th seat (doc 09 S4);
  - `rule_without_condition` for 30 s;
  - the first switch to MP (a locality primer);
  - `feature_unused(campaign_graph, sessions: 5)`.

  History stays in the local profile; there is no telemetry.
- **Budget.** At most 1 discovery tip per session. Three dismissals switch a category off; Settings shows this and offers a reset. No tip appears during a drag, a placement, text entry or a Preview launch. The cadence depends only on local mastery counts and dismiss rate. "Quiet mode" silences everything except blocking engine-limit refusals.

### 3.3 One Standing Orders source, many surfaces (le08, le09, le10, le11)

- **One metadata record** per dialog field, module parameter, trigger enum, lint and script command. It holds a summary, type and range, default, an engine note with its citation, an example ("Probability 50 = coin-flip ambush"), target availability, and since/deprecated.
- **Generated from the same schema** the editor and compiler use: hover tooltips, F1 to the exact anchor, "Why? / How to fix" on every lint code (C, CF, SL, MC, TX, D), command pages per dialect (doc 23 §14) and engine limits (doc 21 §10.1). Wilco cites the same entries (doc 21 §10.2).
- **Two views of one content set:** in-app and exported HTML. Both are version-correct for the project's target profile, with a min-version badge, and ship as an offline snapshot versioned with the app. The manual is never modal.
- **Rosetta rows (le08).** Terms map Plotroom ↔ OFP 2001 ↔ Eden ↔ script:
  - Rule ↔ Trigger (F3 "Sensor");
  - Link ↔ Synchronize (F5);
  - Roster slot ↔ non-playable unit with a presence condition;
  - End socket ↔ END1–6/LOOSE plus `end1..end6/lost`;
  - Module ↔ "CWA has none; Plotroom modules compile to triggers and scripts".

  Tooltips fade after 3 views. The aliases feed manual search and palette fuzzy matching (doc 14 L319). One page maps the original editor's modes, dialogs and Mission/Intro/Outro templates (doc 03) to Plotroom panels. The table never implies that an Eden-only feature exists in CWA.

### 3.4 In-game training kit and remedial routes (le21, le23, le24)

- **Step** is a rule `tutStep == n && <condition>`. On activation it shows hint or titleText text from `stringtable.csv`, marks an `OBJ_` done via `objStatus`, and advances `tutStep`. Camera focus uses an ed09 shot. A struggle timer re-shows a simpler hint after N s. A "Training opponent" preset has low skill and waits on a waypoint synced to the step rule.
- **Gate** uses `enableRadio false` [V GSE#L1035], vehicle `lock` [I] or weapon removal, never `disableUserInput`. **Skill Check**: N targets within T s. UI highlighting has no engine equivalent and is not offered. `hint` is a real command [V doc 23 L143]; how the generated chain behaves on 1.99 needs a probe [U].
- **Drill's live tutorials** (doc 33) generate a small training mission and launch Preview. le23 and le24 reuse the same building blocks at campaign scale.

## 4. Mods and content (mo)

| ID | Idea (IC source) | Verdict | Plotroom translation | Target | Already covered? |
|---|---|---|---|---|---|
| mo01 | Mod set as a shareable lock-style file (`ICD:src/decisions/09c/D062-mod-profiles.md#L19-L91, #L227-L231`) | adapt | §4.1. | 27 §4.2/§4.7/§4.11; 08 | Mostly: ModSet, importers, diff and fingerprint in doc 27. |
| mo02 | "Who serves this file" path resolver (`…/D062-mod-profiles.md#L95-L145, #L217-L223`) | adapt | §4.2. | 27 §4.3/§4.4; 23 | Class provenance only. |
| mo03 | Authoring fingerprint and catalog-drift report (`…/D062-mod-profiles.md#L203-L215`; `…/09e/D049/D049-content-channels-integration.md#L39-L59`) | adapt | §4.1. | 27 §4.5/§4.7/§4.11; 19 | Missing-mod banner, ghost entities. |
| mo04 | Knowledge packs bound to the active mod set (`…/D066-cross-engine-export.md#L296`; `…/D062-mod-profiles.md#L217-L223`) | adopt | A manifest field `[activation] mods = ["csla"]`, matched on the engine-normalised ModId [V doc 27 §2.6]. The pack's templates and menu entries appear only when the project's mod set includes that mod, which keeps weak-model menus truthful. Plugins still never mount or install mods (doc 27 §4.8). | 22 §7.2; 27 §4.8; 25 | Stated in doc 27 §4.8; no manifest field yet. |
| mo05 | Selective install of Plotroom's own components; first-run inventory (`…/D068-selective-install.md#L32-L74, #L278-L289, #L336-L348`; `…/D075-remastered-format-compat.md#L186-L226`) | adapt | Separate "installed components" (Settings → Data: model weights, tutorial content, packs, caches, tiles) from "active in this project". The first-run probe lists installs and mod folders with their sizes and indexes the chosen sets in the background. Presets: "Editor only", "Editor + local model", "Everything". Every choice can be undone, and no download starts without showing its size. | 13; 27 §4.2/§4.7; 08; 33 | Mechanics only (doc 13; doc 27 §4.2). |
| mo06 | Optional media never breaks a campaign (`…/D068-selective-install.md#L101-L112, #L217-L249, #L384-L394`) | adapt | §4.3. Lint MC28. | 26 §7; 19 §6.5; 25; 04 §5; 22 #1 | Text-only default (doc 15 L260). |
| mo07 | Per-language voice through the engine's `<base>.<voiceLang>.<ext>` override (`…/D068-selective-install.md#L134-L161, #L229-L236`) | adapt | §4.3. | 04 §5; 26 §7; 22 #1; 24 §5.5 | One clause in doc 04 L485. |
| mo08 | Required vs recommended dependencies; split fingerprint (`…/D068-selective-install.md#L76-L112, #L308-L324`) | adapt | Manifest and badge fields: size (Game Schedule [V doc 27 §3]), where to get the mod (MODS `modId`, a Game Schedule id or Fwatch `__gs_id`), and `need` (required or recommended-cosmetic; this row first called it `kind`, but doc 42 §2.8 names it `need` and uses `shape` for mod or platform, and doc 42 §5.2 already uses `kind` for pack kinds, so `need` is proposed to win, pending the design round). The cache fingerprint splits in two: **catalog** (configs, stringtables) and **asset** (icons, tiles), so a texture-only revision leaves the catalog caches valid. The game still gates only on `addOns[]` and server mod ids [V doc 27 §2.4]. | 27 §4.5/§4.7/§4.9 | Required/recommended split (D3, §4.9). |
| mo09 | Generated variants never replace originals (`…/D068-selective-install.md#L114-L132, #L392`) | adopt | AI-voiced or rewritten lines are variants stored next to the human version (group = line id). The project selects one, and export writes only that one plus an optional "AI-assisted" credit (doc 17 OQ9). The compiler proves that switching variants changes no condition, timer or objective. | 22 §3.2; 19; 26 §7 | AGENTS.md; doc 22 §3.2. |
| mo10 | Redistribution guard at export, lint D9 (`…/D068-selective-install.md#L291-L306`; `…/D075-remastered-format-compat.md#L161-L174`; `…/09e/D049/D049-p2p-policy-admin.md#L200-L214`; `…/09e/D030/D030-deployment-operations.md#L250-L252`) | adapt | §4.4. | 27 §4.5; 02 §3.4; 09 WN4; 08 | Covers the editor's own behaviour only. |
| mo11 | Script libraries vendored into the mission; resolvable-path lint (`…/D030-deployment-operations.md#L13-L48`) | adapt | A T0 script-library pack is copied at export into `scripts/lib/<pack>@<version>/`, with a header naming pack, version, licence and hash, and recorded in the project lock (mo16). Lint **MC27**: every `exec`, `preprocessFile` or `loadFile` path (including `call loadFile …` and `call preprocessFile …`; there is no `compile` command in any target [V doc 14 L98]) must resolve inside the mission, the campaign or a declared addon prefix (doc 27 AddonPath; doc 24 rule L2). Upgrades re-vendor and show a diff. | 22 §2.1; 23; 24; 27 §4.5 | Snippet library (doc 14); path safety (doc 24 L2). |
| mo12 | `ai_usage` consent, separate from the licence (`…/D030-deployment-operations.md#L71-L99`) | adapt | `allow`: the model may pick the item from its options. `metadata_only` (default): shown only as suggestions the user must click. `deny`: invisible to the agent but browsable by the user. The model never sees an item it may not use. Revisit now that doc 22 #3 plans a community-library connector. | 22 §1.2 #3/§7.2; 17 §7.2; 21 | Deferred in doc 17 §7.2. |
| mo13 | Licence metadata, licence audit, credits block (`…/D030-deployment-operations.md#L50-L69`; `…/09c/D051-gpl-license.md#L125-L127`; `…/09e/D035-creator-attribution.md#L1-L82`; `…/D038-campaign-editor.md#L207, #L221`) | adapt | §4.4. Merges the ed credits row. | 22 §7.2; 02 §6.2; 27 §4.5; 04 | Per-plugin licence only (doc 22 §5). |
| mo14 | Phase-0 registry for packs and connectors (`…/D049-p2p-policy-admin.md#L63-L198`; `…/09e/D030-workshop-registry.md#L158-L218`; `…/D049-package-profiles.md#L1-L51`; `…/09c/D050-workshop-library.md#L61-L130`) | adapt | Start doc 22 step 4 in IC's zero-infrastructure form: a public git repo of per-version TOML manifests, with no binaries. CI checks schema, SPDX licence, per-file SHA-256, `manifest_hash` and capability hash. It rejects game-format files by format detection (PBO, raP, WRP, P3D, PAA) and files matching user-contributed hash lists; CI holds no BI data to hash against, so "known BI data" is not a workable check (doc 42 §5.2). PRs are path-scoped (CODEOWNERS); CI builds the index and signs it with minisign. Versions are immutable; yanking is not deletion. Stable and beta channels; a name-similarity check against typosquatting; an OFP tag vocabulary. | 22 §3.2/§7.1/§7.2 | Signing, channels and revocation (doc 22 §3.2). |
| mo15 | Offline project handoff bundle (`…/D030-workshop-registry.md#L220-L227`) | adapt | "Share project" writes one archive: the typed project, sidecar and lock; the mod-set file; the dependency manifest; and redistributable packs (the others are listed by id). Game data, addons, caches and keys are excluded by construction, and D9 runs first. Opening a bundle validates every file and shows gaps (le17). | 19; 27 §4.5; 22 | None. |
| mo16 | Project lockfile (`…/D030-workshop-registry.md#L127-L135, #L166-L172, #L229-L240`) | adapt | §4.1. | 22 §3.2; 25; 21; 19 | Per-command plugin id and version only. |
| mo17 | Preference packs with hard safety boundaries (`…/D049-package-profiles.md#L80-L216`) | adapt | A T0 `settings` subtype for keymaps, layout, theme, contrast, UI scale, effort defaults and provider routing (no keys). No secrets, paths or code. Installing never applies a pack; applying shows a per-scope diff, can be partial and keeps a rollback snapshot. A pack never enters a mission, mod set or lock. | 22 §2.1; 17 §15; 06 | Config export only (doc 17 §17). |
| mo18 | Storage panel: pinned vs transient caches under a budget (`…/D030-workshop-registry.md#L264-L416`; `…/D049-package-profiles.md#L55-L78`) | adapt | Settings → Storage groups per-fingerprint caches, Preview staging copies, autosaves, model weights and packs, with sizes and last use. Caches for open and recent projects are pinned; the rest are cleaned least-recently-used-first under a budget, with a dry run. No content-addressed store is needed, because everything can be rebuilt from the user's install. | 27 §4.7; 13; 08 | LRU caches (doc 27 §4.7), no UI. |
| mo19 | Open foreign content in place; "import into project" for migration (`…/09c/D026-mod-manifest.md#L12-L66`) | adopt | Open a folder or PBO in place with a byte-stable round trip (doc 04), showing unknown classes as ghosts. Or import it into the project: typed model plus sidecar, ed04 Lift, and TODO notes for anything left raw. Mod lists import from `-mod=` lines, server lists, Game Schedule and Fwatch. Unknown entries give a warning and never fail the load. | 27 §4.2/§4.11; 04; 19 | Mostly (docs 27, 04). |
| mo20 | Permanent aliases for renamed classes and our own schema keys (`…/09c/D023-vocabulary-compat.md#L11-L72`) | adapt | The engine has no class aliasing [V doc 27 §2.4]. T0 rename tables `old → new`, keyed by ModId and revision, drive a one-click rename lint, and the exporter always writes canonical names. Our own sidecar, schema and node keys keep permanent aliases with a deprecation note, so old projects always open. | 27 §4.8; 19; 04 | Vanilla-safe swaps (doc 27 §4.8). |
| mo21 | Licensing: keep doc 02's model rather than IC's broad modding exception (`…/D051-gpl-license.md#L3-L127`) | adapt (confirm) | Doc 02 already decides GPL-3.0-or-later, Bohemia's §7 terms, our Generated Content Exception (§6.2, which cites D051 as precedent), a narrow permissive lane (§6.3) and cargo-deny (§10.3). Doc 22 §5.3 rejects an IC-style plugin exception. Borrow only the `spdx` crate (mo13). | 02 §6; 22 §5 | Fully. |
| mo22 | First-party content ships as ordinary packs (`…/install-layout.md#L5-L15, #L59-L64`) | adopt | Vanilla `llm:` overlays, templates, lint sets, script libraries, tutorials and settings presets are T0 packs with the same manifest, loader and validator as community packs, readable on disk. They are listed as "built-in" and can be disabled, except the overlays Wilco's menus need. | 22 §2.1/§7.1; 17 §7.2; 33 | Implied (doc 27 §4.8). |
| mo23 | Open-licensed fallback fonts and icons (`…/install-layout.md#L298-L324`) | adapt | OFL fonts with Noto Sans as the coverage fallback, because stringtables span CP1250 and CP1251 languages (doc 04 §7). An ISC/MIT icon set fills only gaps in our own icons. All are listed in the third-party notices. | 05; 06 | Doc 05 L45. |

**Merged:** no dead-end buttons → le17; language matrix → ed13; target badges → ed15; pattern lowering/lifting → ed04; one validation engine → ed14; import normalisation → ed20; onboarding map page → le08.

### 4.1 The lock family: mod-set file, drift report, project lock (mo01, mo03, mo16)

```toml
# csla-1985.modset.toml: shareable, never inside a mission (proposal-only)
target = "Cwr"
order  = ["csla", "wgl5"]                           # engine ModIds, first = highest priority
[mod.csla]
folder = "@CSLA"; version = "2.1"; packageRevision = 7; sha256 = "…"   # lock fields from mod.json
fingerprint = "…"                                   # catalog part (mo08 split)
# launcher_state = ["…"]                            # platform entries only (doc 42 §2.8, lint D12); folded into the fingerprint
[mod.csla.channels]                                 # same keys as doc 42 §2.8's manifest; links only, never an install
papa_bear = "…"; game_schedule = "…"; homepage = "https://…"
[preview]
difficulty = "veteran"; nosplash = true
```

- **The mod-set file** ([V doc 27 §2.6] for the `mod.json` fields) offers "Copy as launch line" and imports from a launch line, a server mod list or a Game Schedule id. Opening a mission with no set proposes one from the mission's derived needs.
  - There are no per-profile conflict overrides: the engine picks the winners through reversed bank shadowing and merge order [V doc 27 §2.1/§2.3]. Plotroom can only reorder and explain.
  - Revisions are locked exactly, not by semver; the UI shows "newer revision installed".
  - Each mod carries a `[mod.<id>.channels]` table, and a platform entry also carries `launcher_state` (doc 42 §2.8, §7.4). Importing a file never installs anything: unresolved mods appear as "missing" rows with their channel links.
- **The drift digest** lives in `.ofpeditor/`, never in `mission.sqm`. It records the fingerprint at the last save plus each used class's owner, parent, side, weapons and magazines.
  - On reopen, a non-blocking report lists removed classes (now ghosts), changed owners (so `addOns[]` will change on save), side changes and loadout changes.
  - Each row focuses the entity and offers swap or pin. Nothing is edited automatically.
- **`.ofpeditor/plotroom.lock`** records the version, SHA-256 and source of every pack, template, overlay, script library and plugin tool definition, plus the mod-set fingerprint and the target.
  - "Regenerate this step" uses the locked template unless the user chooses Update.
  - Glass-box inspection can say "made by workflow W, step S, template T@1.3.0".
  - The lock is stripped on export.

### 4.2 Path resolver (mo02)

- **How it resolves.** It runs the engine's lookup chain exactly as doc 27 §2.1 describes [V]: mounted bank by prefix, then a loose file relative to the game directory, then the mod-root alias, then the anims/addons normalisation. Fonts are the only thing a mod overrides by relative path. The resolver is a pure function of `MountPlan`, surfaced as a hover on every path literal through the doc 23 language service.
- **What it reports:** the winner, the shadowed candidates and the deciding rule, for example "first-mounted stem wins" or "loose files are not overlaid".
- **Sounds** resolve against the mission directory (or `dtaExt\` for a campaign), then the voice-language override [V `CWR:UI/OptionsUI.cpp#L434-L481`]; the global-config branch applies no override (`#L483-L489`).

### 4.3 Every sound has a text path; voice languages come for free (mo06, mo07)

- **Text paths.** The engine already provides `titles[]` in CfgSounds and CfgRadio, plus `sideChat` and `titleText` [V doc 04 L485, citing `CWR:Audio/DynSound.cpp#L146`].
  - Compiler rule: every custom `say`, `playSound` or radio item has a text rendering; no trigger or objective depends on a sound having played or on its length; music is decorative.
  - MC28 fires when a line lacks a text path or when a `sound[]` file is missing from the mission or campaign folder. What the engine does with a missing file is [U probe].
  - Export offers "campaign core" (text only) and "full" (with the voice pack).
- **Voice languages.** CWR's `PreferExistingVoiceLanguageOverride` plays `<base>.<voiceLang>.<ext>` if that file exists, resolved at play time, for mission and campaign `CfgSounds` [V `CWR:UI/OptionsUI.cpp#L434-L481`], `CfgRadio` (`FindRadio`, `#L542-L570`) and `CfgSFX` (`#L355-L405`), never for global-config entries. A voice pack is therefore just sibling files (`radio/hq01.ogg` plus `radio/hq01.Czech.ogg`).
  - The audio panel shows a line × language matrix.
  - The suffix is the selected voice-language name inserted before the extension, `s02v01.ogg` + `Czech` → `s02v01.Czech.ogg`; a path without an extension gets no override [V `CWR:Audio/VoiceLangPath.hpp#L12-L54`]. Lip files pair with either form: a missing `<base>.<lang>.lip` falls back to `<base>.lip` and the reverse (`CWR:World/Entities/Infantry/Head.cpp#L45-L75`), so one `.lip` can serve every language only when the timing matches [I]. Case sensitivity of the lookup on non-Windows hosts is [U].
  - The Requires badge marks the feature as CWR/CE (1.99 is [U]).
  - The base file must always exist, so every target and language falls back cleanly.

### 4.4 Export hygiene: redistribution guard, licence audit, credits (mo10, mo13)

- **D9 (warn, never blocks private use).** At export, every file is hashed and compared with a local index of files served by the base game and the mounted mods. The index is built during catalog indexing and lives only in the user cache. Example findings:
  - "`sound/alarm.ogg` is byte-identical to a file in the base game's sound bank (BI data, APL-SA): reference it by path instead";
  - "copied from @CSLA (licence unknown)".

  Plotroom treats install and mod folders as read-only and writes only to project directories, the user's mission folders and Preview staging (doc 08).
- **Licence audit.** An SPDX `license` and an `author` are required on every T0 item that can reach user output, and on plugin-generated assets. At export, the items actually incorporated (doc 22 §3.2 provenance) are collected:
  - NC and ShareAlike obligations get a warning;
  - referenced BI data is noted as APL-SA and not included (doc 02 §3);
  - licence expressions are parsed with the `spdx` crate.

  Our built-in items fall under the Generated Content Exception (doc 02 §6.2).
- **Credits block** (authors, roles, licence, links, an AI-assistance note). It compiles into:
  - `overview.html` and `onLoadMission` [V doc 04 L96, L474];
  - an optional Outro-Win roll of cut-layer `cutText` pages, which cannot hold the mission end [V doc 18 L187-L189];
  - the exported readme and manifest (doc 27).

  Tipping and monetisation are skipped.

## 5. Integration list for the design round

### 5.1 Provisional lint codes

| Code | Severity | Rule | Row |
|---|---|---|---|
| CF19 | error | A payoff needs a fragment or flag obtainable only on a branch the path skipped (make it a variant, not a requirement) | cw11 |
| CF20 | warn | A character is referenced in a briefing before their first in-play appearance on some path | cw12 |
| CF21 | info | A mechanic is used on a path before its teaching slot | cw12 |
| CF22 | warn | A betrayer has fewer than N positive appearances before the reveal on some path | cw14 |
| CF23 | warn | A payoff is reached with fewer than k foreshadows; a thread is still Rising at an ending unless open; an Abandoned thread's setups still promise | cw15 |
| CF24 | warn | More than one new mechanic in one node on some path | le22 |
| CF25 | warn | An intensity jump of ≥ 2 bands with no remedial route from `lost` | le22 |
| SL21 | error | A `HeroRequired` card on a path where the hero may be KIA or captured, with no `fallback_variant` (extends C18/SL01) | cw08 |
| SL22 | error | Mole: a suspect can die before the first accuse point, or clue coverage is missing for some `mole` value | cw16 |
| SL23 | warn | Effect text has no number or entity token; failure and expiry share text while their effects differ | cw01 |
| SL24 | error | A card, ledger entry or perk has no consumer (extends SL05, SL07, CF04) | cw01, cw02, cw09 |
| SL25 | error | A program timing shifts > 1 phase without an authored variant; a chain head can expire before its tail is offered | cw02, cw03 |
| MC20 | warn | A generated op has > 1 complication or estimated duration > 20 min; an endurance mission's win requires killing every enemy | cw07, cw06 |
| MC21 | info | A mission has no moment slot | cw23 |
| MC22 | warn | A support item has no budget source; a "stay" objective has no visible risk statement | cw25 |
| MC23 | error | A battle effect targets a group that is absent on some path | cw26 |
| MC24 | error | After a phase, no active objective or reachable outcome; a phase member is referenced before its phase | ed06 |
| MC25 | warn | A camera scene in an MP mission with no declared audience | ed10 |
| MC26 | warn | An outcome can fire while a cinematic is running | ed09 |
| MC27 | error | A script path does not resolve inside the mission, the campaign or a declared addon prefix | mo11 |
| MC28 | warn | A custom sound has no text path, or a `sound[]` file is missing | mo06 |
| MC29 | warn | `saveGame` checkpoint inside a loop, in MP, or more than once per phase | ed05 |
| D9 | warn | An exported file is byte-identical to a file served by the base game or a mounted mod | mo10 |
| D10 | warn | A class's owner comes from an empty stub declaration in another addon; the chain is shown (defined in doc 42 §6.4) | doc 42 §2.1 |
| D11 | warn | A mod in the set redirects the game's master server through `CfgNetwork.masterServer` (defined in doc 42 §6.4) | doc 42 §6.3 |
| D12 | info | A platform mod set's effective config depends on launcher state; its provenance is unverified until the parity test passes (defined in doc 42 §6.4) | doc 42 §2.8 |

The outcome lints in ed07 extend C13 and take no new code. D10–D12 are doc 42's provisional codes, listed here so the D series stays in one table; like `D9`, their bare labels also name doc 21 section labels.

### 5.2 Actions per target doc

| Doc | Actions to fold in |
|---|---|
| 02 Licensing | Record D9 as the enforcement of §3.4 for user-supplied files (mo10). Add SPDX per item and the licence audit (mo13). Decide whether extension overlays that reference a BI or third-party campaign may be shared (cw13). Confirm the D051 comparison as is (mo21). |
| 04 Formats | List Intel `resistanceWest/East` as a campaign lever (cw05) and the Intel weather and date fields as calendar targets (cw24). Specify the voice-language sibling-file rule (mo07). List the sidecar-only objects: zones, phases, named routes, the ULID map (ed01, ed06, ed08, ed16). |
| 05, 06 Visuals, UI stack | Route overlay (ed08); accessibility overlay (ed21); fallback fonts (mo23); semantic action IDs and keymap profiles (le06); the preference-versus-project split (le16). |
| 08 Preview | Run record with assisted flags (le19) and a `PreviewBattleReport` (cw22). Post-Preview debrief card (le12) and postcards (le13). Test range and speed control (ed17). Director, capture back and route recording (ed18). Standalone outcome display (ed07); tour completion events (le05). |
| 09 Wishlist | Map S18 → le03, le07, le10; CO3 → le18; S4 → the ed14 meter; M1/M2 → le06, le16; S13/CO2 → ed18. |
| 13 Local inference | Component presets and the storage panel (mo05, mo18). |
| 17 First IC pass | Add a pointer to this doc. Mark as designed the §15 bullets for named regions (ed01), the outliner (ed02), the complexity meter (ed14) and play from cursor (ed17). |
| 18 Engine campaigns | Note the detour-and-return cost (ed07) and the open question of reading another campaign's save (cw28). |
| 19 Campaign designer | §4/§5: derived variables and counters (cw03), `VictoryCondition`/`DefeatCondition` (cw20), a template sentence per `Effect` (cw10). §6.1: hub-card disclosure fields (cw01). §6.3: thread lanes (cw15). §6.4: the explorer computes consumers and teaching nodes (cw01, cw12). §6.6: priority column, standalone preview, outcome lints (ed07). §7.6: extension overlays (cw13), the veteran-import build option (cw28). |
| 21 Agent doctrine | Reorder the §11.4 Drill payoff-first, with test-out (le01). A tour runner in which code, not Wilco, validates steps (le05). Ribbons (le14); `/` dispatch in chat (le18); per-origin undo (ed22). |
| 22 Plugins | Manifest fields `[activation] mods` (mo04), `ai_usage` (mo12), SPDX per item (mo13). T0 content types `tour`, `tip`, `module`, `settings`, `script-library` (le05, le03, ed03, mo17, mo11). Phase-0 registry (mo14); the built-in-packs rule (mo22). Plugins may ship tips and tours only for their own tools. |
| 23, 24 Language service, risk audit | Migration tips triggered by findings (le09). Path-resolution hover (mo02) and MC27. Risk rows for the `saveGame` checkpoint (ed05) and `setAccTime` (ed17). |
| 25 Weak-model harness | Thread lifecycle fields (cw15). The `MoralComplexity` chip, value tags and ensemble check (cw18). One-slot fill rules for Mole clues, Nemesis taunts and fragments (cw16, cw17, cw11). Lock-based regeneration (mo16). |
| 26 Campaign content | Persistence modules: Fragments (cw11), alignment ladder (cw05), perk choice (cw09), commendations (le15). §9.3 knobs: culmination (cw06), embedded battles (cw26), support requests (cw25), weather windows (cw24), `MomentSlot` (cw23), op grammar (cw07). §9.4 patterns: P10 Exodus (cw19), open-ended conditions (cw20), sectors (cw21), second chance (le23), the layered-unlock opener (cw12). §8.2: the `TwistPattern` catalogue (cw14). §10: CF19–CF25. |
| 27 Addons and mods | mo01, mo02, mo03, mo08, mo15, mo19, mo20; lint D9. Doc 42 §8.3 already carries the doc 27 amendments for the mod-set file and manifest (`shape`, `need`, channel ids, `launcher_state`). |
| 28 Fun (merge, do not duplicate) | MC11 and MC15 carry cw07's two-route rule. MC19 carries the cinematic caps and skip rules (ed09). MC06 is the ed14 meter. CF14 and CF16 absorb le22 (a) and (c). MC17 pairs with CF22 and CF23. |
| 29 Strategic layer | §3.2: `CardTemplate` fields (cw01, cw03, cw08); modules Programs, EnemyPosture, Mole, SupportRequests, Commendations; adaptive Nemesis (cw17); `SectorDecl` (cw21); `PerkChoice` (cw09). §3.3: posture and enemy-policy steps (cw04, cw21). §3.6: SL21–SL25. §4.3: debrief lines and the war diary (cw10). §5.2: calibration from battle reports (cw22), bundle-level endgame checks (cw02). §8.2: `TeachingSchedule` (cw12). |
| 31 No-code ladder (exists; reconcile, do not append) | ed01–ed08, ed10–ed12 (their module side), ed19; cw23, cw25, cw26, le21, le24; the §2.1 lowering table and the Show/Eject/Lift contract. |
| 32 Cinematics and camera (exists; reconcile, do not append) | ed09–ed12; cw23 moments; MC25/MC26. |
| 33 Standing Orders and Drill (exists; reconcile, do not append) | le01–le11, le17, le21 (live tutorials), le25, cw12; the tutorial content in mo05 and mo22. |

## 6. Skipped and why

| Skipped (IC source) | Why | What survives |
|---|---|---|
| Co-op, async and competitive generative campaigns; bridges from solo to multiplayer (`ICD:src/decisions/09f/D016/D016-world-assets-multiplayer.md#L145-L305`; `…/D016-extensions-factions-tools.md#L179-L191`; `…/09d/D070-asymmetric-coop.md#L1-L100`) | The engine has no MP campaign flow: a dedicated server runs a flat mission rotation [V doc 18 §6.5], and doc 19 §7.4 puts MP campaigns out of scope. Leaderboards and shared front lines need services beyond the product. | Single MP missions (ed19); the request economy (cw25); seeded generation (doc 29). |
| RTS-only features: replay takeover, ghost armies, dual-state maps, generated factions, campaign menu scenes (`…/09d/D078-time-machine.md#L126-L248, #L947-L1045`; `…/D016-factions-editor-tools.md#L1-L158`; `…/modding/campaigns.md#L2605-L2704`) | OFP has no replay or snapshot branching and no terrain layers. Factions need addon configs and models, which the agent must not fabricate (doc 27). The main menu is not campaign-controlled, and chapter cutscenes see no vars [V doc 18 §6.1; C16]. | Designer-side what-if (doc 19 §6.4); cutscenes that do not depend on state. |
| Foreign replay import, divergence tracking, replay corpora (`…/09f/D056-replay-import.md#L33-L235`; `…/D038-game-master-replay-multiplayer.md#L59-L71`) | There is no order-stream replay format, and Plotroom owns no simulation. LLM narrative from event logs is out of scope. | Route recording (ed18); honest import reports (ed15). |
| Measured profile playtest (`…/D038-media-validation.md#L458-L498`) | 1.99 exposes no timing data; CWR compiles `diag_*` out (doc 24 L495-L496); the harness has no frame-time query [V doc 08 §2.5]. | The static meter (ed14); an MP soak with `PoseidonServer --duration N --stats 10` [V doc 08 L490-L491]. Revisit if CE adds a timing query. |
| Platform extras (`…/D038-onboarding-platform-export.md#L1-L20, #L425-L435`; `…/D038-game-master-replay-multiplayer.md#L26-L34, #L213-L275`; `…/D038-media-validation.md#L23-L46`; `…/architecture/ui-theme.md#L78-L84`; `…/09c/D014-tera-templating.md#L1-L10`) | Workshop and tipping: we run no hub. Controller editing: stays doc 09 CO14 "Could". Spectator bookmarks: RTS only. Asymmetric and live-GM co-op: not planned. FMV and RTL: [U]. Shellmaps: game configuration, not missions. Load-time Tera: we already chose export-time minijinja [V doc 22 L124-L125]. | Credits without monetisation (mo13); the doc 22 plugin tiers. |
| Annotated replay, Play-of-the-Game scoring, highlight library (`…/09g/D065/D065-postgame-api-integration.md#L45-L68`; `…/09d/D077-replay-highlights.md#L43-L140`) | OFP records no deterministic replays. | Postcards (le13); the debrief card (le12). |
| Skill assessment, APM, tempo advisor, gamepad/Deck/touch input (`…/D065-new-player-pacing.md#L112-L202, #L274-L320, #L370-L391`) | Plotroom is a desktop editor, and testing a creator's dexterity is intrusive. | Mastery counters (le04); keyboard reach (le06, ed21). |
| Post-play feedback prompts, community benchmarks, MVP awards (`ICD:src/player-flow/post-game.md#L55-L178`; `…/player-flow/single-player.md#L179-L184`) | They need a content hub and an in-game UI we do not control (doc 17 L493). | A personal line in commendations (le15). |
| Cvars, autoexec, chat channels, mod console commands, Lua console (`…/09g/D058/D058-overview-architecture.md#L221-L311`; `…/D058-cheats-config.md#L212-L240`; `…/D058-commands-catalog.md#L309-L353`) | These serve an MP game runtime. Plugin capabilities go through the manifest (doc 22). | The Preview console under doc 24's templates [V doc 24 L488]. |
| Hosted Workshop, P2P, lobby auto-download, content channels, reputation, DMCA, export to other engines (`…/09e/D030/D030-deployment-operations.md#L168-L271`; `…/09e/D049/D049-p2p-policy-admin.md#L249-L285`; `…/09c/D050-workshop-library.md#L12-L59`; `…/09c/D066-cross-engine-export.md#L9-L45`) | Plotroom neither hosts nor installs content. CWR's MODS manager already downloads at server join with SHA-256 checks [V doc 27 §2.6]. There is no lockstep sim to pin. APL-SA "ArmaOnly" bars exporting BI assets (doc 02 §3.4). | Client-side manifest rules (mo12–mo14). |
| D022 surface simulation (snow depth, mud) (`…/09d/D022-dynamic-weather.md`) | The engine has no such system. | The calendar and weather arc (cw24). |

## 7. Open questions

1. **Engine probes** (add them to doc 29 §9 and doc 19): `in` and `list` refresh on 1.99 (ed01); `setMarkerType` timing on 1.99 (ed06, cw03); the practical `OBJ_` cap per briefing (cw10, le15); `setFriend` and `join` on 1.99 (cw05, cw14); the `knowsAbout` threshold (le24); OGG on 1.99 and JPG picture fields (ed20); whether 1.99 has any voice-language override (mo07; the CWR suffix rule is now [V], §4.3); `Killed` handler payload (PR21; cw17, le15); a real explosion from a vanilla script on 1.99 (cw25, doc 31 module 4); what the engine does with a missing sound file (mo06); per-side MP briefings (ed19); AI helicopter landing (cw25); an in-mission cinematic skip (ed09); allowed `setAccTime` values (ed17); prisoner `join` (cw23); per-object destructibility via `object` (cw21).
2. Does a waypoint synced to a trigger that has not fired hold its group at runtime, and on 1.99? The CWR code says yes for AI-led groups (§2.1, [V by reading]); a probe must confirm it, including the 600 s `Wait` timeout (`CWR:AI/AIArcade.cpp#L265`, `#L834-L837`), which ends the wait command but not the waypoint state [I].
3. Can a finished campaign's save be parsed for "Import veterans" (cw28, doc 18 [U])?
4. What position tolerance keeps false matches rare when objects are re-associated after a vanilla re-save (ed16)? This needs a corpus of real re-saved missions.
5. Does the "stealth route exists" detection-band heuristic predict playtest reality (cw07)? This needs the terrain index (doc 26 §2.2) and the doc 21 §11.6 play-testers.
6. **Scope (owner decisions).** Which modules are in doc 31 v1? Which strategic modules (Programs, EnemyPosture, Mole, SupportRequests) join the reference XCOM-like campaign, within the SL03 budget? Is the headless `plotroom` CLI in v1 (v1 = editor + Preview + AI co-pilot + the campaign flow, describe → generate → edit; owner decision)? Who operates the phase-0 registry repo (mo14)?
7. Where does local learning history (tips, tours, ribbons) live: a settings file or SQLite? The answer must survive app updates.

## 8. Sources

**Iron Curtain design docs**, all under `iron-curtain-engine/iron-curtain-design-docs@2fda63f5a9:src/` (line ranges are in the rows above):
- `modding/`: `campaigns.md`, `enhanced-campaign-plan.md`.
- `decisions/09c/`: `D014-tera-templating.md`, `D023-vocabulary-compat.md`, `D026-mod-manifest.md`, `D050-workshop-library.md`, `D051-gpl-license.md`, `D062-mod-profiles.md`, `D066-cross-engine-export.md`, `D068-selective-install.md`, `D075-remastered-format-compat.md`.
- `decisions/09d/`: `D021-branching-campaigns.md`, `D022-dynamic-weather.md`, `D033-qol-presets.md`, `D042-behavioral-profiles.md`, `D043/commanders-and-puppet-masters.md`, `D070-asymmetric-coop.md`, `D077-replay-highlights.md`, `D078-time-machine.md`.
- `decisions/09e/`: `D030-workshop-registry.md`, `D030/D030-deployment-operations.md`, `D035-creator-attribution.md`, `D036-achievements.md`, `D049-workshop-assets.md`, `D049/D049-content-channels-integration.md`, `D049/D049-package-profiles.md`, `D049/D049-p2p-policy-admin.md`.
- `decisions/09f/`: `D016/D016-{branching-world-campaigns, characters-output, cinematics-media, extensions-factions-tools, factions-editor-tools, overview-generation, world-assets-multiplayer}.md`, `D020-mod-sdk.md`, `D038/D038-{campaign-editor, core-architecture, game-master-replay-multiplayer, media-validation, onboarding-platform-export, triggers-waypoints}.md`, `D040-asset-studio.md`, `D056-replay-import.md`.
- `decisions/09g/`: `D058/D058-{cheats-config, commands-catalog, overview-architecture}.md`, `D065/D065-{hints-schema, hints-tips-triggers, new-player-pacing, overview-commander-school, postgame-api-integration}.md`.
- `architecture/`: `install-layout.md`, `qol-toggles.md`, `sdk-editor.md`, `ui-theme.md`.
- `player-flow/`: `encyclopedia.md`, `first-launch.md`, `post-game.md`, `sdk.md`, `settings.md`, `single-player.md`, `tutorial.md`.
- Top level: `13-PHILOSOPHY.md`, `17-PLAYER-FLOW.md`.

**Engine source** (`BohemiaInteractive/CWR@ffc61838b7`):
- `engine/Poseidon/Game/Commands/GameStateExt.cpp`, registrations at #L859, #L861, #L995, #L1002–L1003, #L1012, #L1035, #L1037, #L1054, #L1065, #L1071, #L1142, #L1178, #L1182, #L1220–L1221, #L1248, #L1266, #L1269, #L1296, #L1324, #L1338, #L1342, #L1351, #L1393;
- `engine/Poseidon/UI/OptionsUI.cpp#L355-L405`, `#L434-L489`, `#L542-L570` (CfgSFX, FindSound, FindRadio and the voice-language override);
- `engine/Poseidon/Audio/VoiceLangPath.hpp#L12-L54` (`WithLangSuffix`); `engine/Poseidon/World/Entities/Infantry/Head.cpp#L45-L75` (lip pairing);
- `engine/Poseidon/AI/AICenterImpl.cpp#L748-L807`, `engine/Poseidon/AI/AIArcade.cpp#L265`, `#L309-L369`, `#L815-L855`, `engine/Poseidon/World/Detection/Detector.cpp#L1336-L1389`, `#L1512-L1523` (sync items and held waypoints; re-read in the fact-check).

**Sibling docs:** 02, 03, 04, 05, 06, 07, 08, 09, 13, 14, 15, 17, 18, 19, 21, 22, 23, 24 (and `data/script-command-risk.csv`), 25, 26, 27, 28, 29, 31, 32, 33, 42 (32 and 42 cited from the consolidation pass).

**Mining-pass checks.** In this pass I confirmed that all 64 cited IC files exist at the pin and that every cited line range lies inside its file. I spot-read these passages against the cited text: dispatch tiers (`campaigns.md#L2059-L2062`), OPSEC levels (`#L1597-L1615`), Named Regions (`D038-core-architecture.md#L139-L146`), the Coming From profiles including "OFP Classic" (`D038-onboarding-platform-export.md#L24-L52`), the Long March and traitor modes (`D016-extensions-factions-tools.md#L9-L11, #L155-L167`), dopamine-first design (`D065-overview-commander-school.md#L51-L75`), no dead-end buttons (`D033-qol-presets.md#L232`) and `ai_usage` (`D030-deployment-operations.md#L80-L90`). Every `GSE` line listed above was read and matches the named command, and the voice-language override code was read in full. The remaining IC line ranges come from the mining pass and were not all re-read; their content claims are [V] as reported, with some residual risk.

## Verification notes

Adversarial fact-check, 2026-09-27. Scope: IC citation accuracy, engine feasibility of every *adopt*/*adapt* translation against docs 18, 19, 23, 24, 27, 29 and the now-existing 31 and 33, and the public-repository rule. Sources were read at the pins named in the header; the CWR source was re-read where noted. Nothing was run in the game, so every [V] here means "verified by reading".

**Citation sample (62 IC passages opened).** Accurate as paraphrased:

- `campaigns.md`: #L751-L760, #L821-L875, #L879-L897, #L1111-L1199, #L1461-L1489, #L1491-L1584, #L1586-L1615, #L433-L600 (generation order #L532-L546, 10–15 min band #L578, seed persisted #L560), #L2041-L2062, #L2168-L2185, #L2218-L2256.
- `enhanced-campaign-plan.md`: #L15-L57, #L239-L260, #L407-L436, #L438-L509, #L613-L650, #L730-L767 (fragments, thresholds 1/3/5, trigger zones), #L1789-L1800, #L1830-L1850.
- D016: `branching-world-campaigns.md#L79-L125`, `#L127-L140`, `#L285-L300`, `#L423-L432`; `extensions-factions-tools.md#L9-L25`, `#L49-L63`, `#L67-L105`, `#L151-L175`; `characters-output.md#L1-L50`, `#L172-L213`, `#L342-L360`; `world-assets-multiplayer.md#L338-L348`; `cinematics-media.md` (moment frequency table).
- D038: `core-architecture.md#L132-L159`, `#L223-L232`, `#L283-L366`; `triggers-waypoints.md#L102-L153`; `media-validation.md#L239-L266`, `#L344-L457`.
- D065: `overview-commander-school.md#L51-L75`, `#L137-L151`; `postgame-api-integration.md#L84-L88`, `#L411-L421`; `new-player-pacing.md#L322-L368`; `hints-schema.md` fields; `hints-tips-triggers.md#L394-L410`.
- Others: D070 `#L230-L309`, `#L656-L745`; D078 `#L1-L23` (Draft); D062 `#L19-L30`, `#L95-L105`, `#L203-L231`; D068 `#L134-L161`; D030 `deployment-operations.md#L71-L99`; D051 `#L120-L127`; D023 `#L11-L20`; D033 `#L232-L240`; D042 `#L23-L34`; D022 `#L26-L40`; `13-PHILOSOPHY.md#L342-L346`; `install-layout.md#L182-L190`; `player-flow/sdk.md#L26-L36`; `encyclopedia.md#L1-L12`.

**Misattributions fixed.**

1. §1.2 credited the ledger fields (owner, state, quality, `consumed_by`) to `enhanced-campaign-plan.md#L438-L509`; they are in `campaigns.md#L1461-L1489`.
2. §1.4 credited "make the betrayer likeable first" to `D016-branching-world-campaigns.md`; it is `D016-characters-output.md#L83` (trust-building: `D016-extensions-factions-tools.md#L163`).
3. §1.5 credited "explain once, in character, then trust" to `#L15-L57`; that is Rule 7, `#L427-L434`.
4. §3.1 cited doc 08 L44 (a Remastered launch line) for 1.99 Preview. On 1.99 Preview is manual export-and-open (doc 08 L362).
5. §2.1 read `SynchronizedItem::IsActive` backwards. In the code `active` means "still blocking"; the conclusion (the waypoint holds) now rests on the re-read activation and wait code and is [V by reading].

The GSE lines listed in §8 were re-read at the pin and all match.

**Engine-feasibility changes.**

- *cw04 downgraded adopt → adapt.* IC escalates OPSEC on success. That contradicts doc 29 §1.5 rule 2 and this doc's own cw20 rejection, so `opsec` now steps on the tempo the player chooses, disclosed on the card (TL;DR, §1.2).
- *cw06.* There is no trigger-disable command, and `addWaypoint` and `setTriggerStatements` are `Cwr`/`Ce` only (doc 31). Culmination now uses flag-gated conditions and a `move` order or a sync-held waypoint.
- *cw19.* The convoy was "Hangar rows"; the engine has no vehicle pool, doc 29 caps the Hangar at 4 slots, and SL19 forbids a hangar vehicle on the critical path. Legs now fall back to foot variants.
- *cw27.* Added the engine limits: same-chapter edges (doc 18 L86) or a router (C11), one camp socket per target, `objects.sav` never reverted, and C20 growth.
- *cw24.* Rain above overcast ≈ 0.67 is now [V] from doc 31. `setDate` is `Cwr`/`Ce` only, so shared templates advance days with `skipTime`.
- *Other rows.*
  - cw05: static Intel on shared templates.
  - cw08: slot-unit fallback on `Cwa199`.
  - cw11: `addAction` arity; 1.99 [U].
  - cw16, cw25: radio needs a group-leading player; fire missions carry doc 31's 1.99 explosion probe.
  - cw17: `Killed` handlers are probe PR21.
  - ed05: presence skips playable units (F12).
  - ed07: positions travel through `saveVar` because `saveStatus` stores no transform.
  - ed09/ed11/§2.3: radio is inaudible in intro mode; `disableUserInput` is a nesting counter; doc 31 §6.3 compile contract.
  - le09 and mo11: `params` and `compile` exist on no target (doc 14 L98); MC27 no longer names `call compile`.
  - le02 and le25: doc 33's "no start-up tour" rule now governs first run.
- *mo07 upgraded.* The suffix token is now [V] (`VoiceLangPath.hpp`), and the override also covers `CfgRadio` and `CfgSFX`.

**Stale-context fixes.**

- Docs 31 and 33 now exist, so "Already covered?" cells now point to them: ed03, ed04, ed09, ed11, le01, le03, le08, le10, le17.
- The §5.2 rows for docs 31 and 33 now say "reconcile, do not append".
- The code-collision note now names `D9` (doc 21) and `P10` (doc 09).

**Public rule.** No private or unpublished project, path or coined term appears in the doc (searched for local paths, user names and private project names). IC's design docs are the owner's public repository.

**Residual concerns.**

- Roughly 40 % of the IC line ranges were re-read. The rest are in range and plausible but unverified at sentence level.
- Several "adopt" rows (cw02, cw03, cw11, cw16, cw26) depend on F12 presence gating and on `setMarkerType`, whose 1.99 behaviour is still a probe (PR04, PR09).
- Doc 33 labels a curriculum item "C6", which collides with doc 19's lint C06. That is outside this doc and belongs to the design round.
- The overlap with docs 31 and 33 was mapped at row level only. A merge pass should retire rows that those docs already cover (for example ed05 against doc 31 module 18) rather than carry both.

### Consolidation pass (2026-09-27)

- **Feature renames (owner decision).** Our concept manual "Field Manual" is now **Standing Orders** and our live tutorials ("Academy" in doc 21, "boot camp" in doc 33) are now **Drill**: header sibling note, TL;DR, le01, le10, le11, le14, le25, the §3.1 and §3.3 headings, §3.4, and the §5.2 rows for docs 21 and 33. IC's own names (Commander School, IC file names) are unchanged. This doc had no links to doc 33's file or to the skill folder to update.
- **Doc 32 exists.** The header, TL;DR and §5.2 no longer call it planned; its §5.2 row now says "exists; reconcile, do not append", like the rows for docs 31 and 33 (doc 33's residual note that doc 34 still called its siblings missing).
- **Doc 42 reconciliation (doc 42 §5.2, §8.3 row 34).** mo14: CI rejects game formats by detection plus user-contributed hash lists, not "known BI data". §4.1: the mod-set file gains `[mod.<id>.channels]` and, for platforms, `launcher_state` (doc 42 §2.8, §7.4). §5.1: D10–D12 listed, attributed to doc 42 §6.4. mo08: the required/recommended field is renamed `kind` → `need` to match doc 42 §2.8 (`shape` = mod or platform; `kind` already names pack kinds in doc 42 §5.2). This choice is flagged as proposed until the design round confirms it.
- **v1 scope (owner decision).** Open question 6 now reads v1 = editor + Preview + AI co-pilot + the campaign flow. The CLI, doc 31 v1 modules, strategic modules and registry operator questions stay open.
- **Stable anchors.** Doc 21 was edited in this same pass and its lines moved, so citations of doc 21 L274, L426, L456 and L457 now cite §6.3, §10.2 and §11.4 instead. The sources list adds docs 32 and 42.
