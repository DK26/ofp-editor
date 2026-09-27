# Roadmap: spikes, probes and qualification runs

> **Status:** proposal (roadmap baseline 2026-09-27). Part of the [roadmap](../roadmap.md). Spike ids `SP-01`–`SP-16` are new and
> unused elsewhere in `docs/`; DG005 should register the family. Exit criteria are quoted from the source docs, where they are
> proposals and placeholders.

## 1. Conventions

- **A spike** is a time-boxed experiment that answers named questions with exit criteria and a go/no-go stated before it starts. A spike
  that fails reopens the baseline record it names ("Revisit if", `docs/decisions/README.md`) and is reported, never quietly absorbed.
- **Who runs what.** Agents write the spike code, fixtures and tests and run `cargo test`/`clippy`/`check`; anything that launches the
  app, the game or a local model is run by the owner or a contributor on their machine, and the result comes back as a manual
  verification note (`AGENTS.md`, build and run rule; Evidence Rule).
- **Reports (proposal).** One short file per spike, `docs/spikes/SP-nn-<slug>.md`, created with the first report: date, machine, OS,
  GPU, exact versions and artifact hashes, the questions, the measurements, the verdict, and which records, DGs or `ER-###` rows it
  changed. The source research doc gets a dated verification note pointing to it.
- **Hygiene.** No game data, screenshots of game assets, model outputs quoted at length, or private material is committed; corpus and
  install runs print hashes and counts only (`AGENTS.md`, fixture legality).

## 2. Spike register

| ID | Spike | Source | Questions and exit criteria | Runs on | Blocks | When |
| --- | --- | --- | --- | --- | --- | --- |
| SP-01 | Shell and composite | doc 06 §7 spike 1 | eframe app with docked panels and a central offscreen wgpu texture; swatch bytes match in a screenshot; windowed ↔ borderless ↔ monitor switch; 1-px lines crisp from 100 % to 150 % DPI. **No-go** if the colour check fails and cannot be fixed in 2 extra days → raw winit + egui-winit | Dev machine; CI goldens | M1 renderer (D016) | M0 |
| SP-02 | `DrawList` and glyphs | doc 06 §7 spike 2 | `DrawList`, clip port, line → quad, batching with insta snapshots; FXY parser and atlas from a synthetic font; `FontDraw` port; TTF fallback. Snapshots stable; headless goldens pass on WARP and lavapipe in CI | CI | M1 fonts, map | M0 |
| SP-03 | Map stress | doc 06 §7 spike 3 | Procedural 256×256 heightmap, fields, contours, forests, grid labels, 2,000 unit icons; zoom and pan ≥ 60 fps on an iGPU (DX12 and Vulkan), ≥ 10 fps on WARP; draw-list build within budget; frame times recorded | iGPU laptop; WARP | M1 map | M0 |
| SP-04 | Classic dialog and input | doc 06 §7 spike 4 | `CStatic`, `CButton`, `CListBox`, `CCombo`, `CEdit` from a synthetic rsc snippet; focus and Tab stay in the classic view; a Japanese IME composes into a classic edit (manual Windows check). **No-go** as SP-01 | Windows dev machine | M2 dialogs | M0 |
| SP-05 | Accessibility and multi-window | doc 06 §7 spike 5 | AccessKit nodes for SP-04's dialog; Accessibility Insights lists roles and names; a detached chat viewport keeps working while the classic view animates; whether viewports share one wgpu device | Windows | M2 accessibility (D016 item 6) | M0 |
| SP-06 | P0 installs and data, including the free demo | doc 08 §5, §6 P0; doc 05 TL;DR, §7; game-integration §2, OQ2 | See §3.1 | Owner's real installs (Windows, Linux) | M1 discovery; M3 | M0 |
| SP-07 | Preview flags and harness | doc 08 §2.2–§2.5, §6 P0; doc 42 OQ10; doc 29 OQ2; DG001 | See §3.2 | Owner's Remastered and CE installs | M3 launch modes; DG001 option B; I42-08; I29-08 | M0 (flags); before M3 (harness) |
| SP-08 | The 1.99 probe suite (manual backend) | doc 20 §4.4; game-integration §10; doc 19 OQ1; doc 29 §9; doc 37 PP rows; doc 43 probes | Plotroom exports a probe mission; the owner plays it on 1.99; the result is recorded with the probe's source and hash. Recurring: see §4.2 for the order | Owner's 1.99 install | The `.plotroom/` spelling (M2); freezing `Cwa199` lowering (M5); AC17 (v1.1); RAT7 (v1.3) | Before M2, M3, M5, v1.1, v1.2, v1.3 |
| SP-09 | CST span patch and writer parity | architecture README §6 (M0); doc 04 §12; D017 | `render(parse(b)) == b` on synthetic configs with injected trivia; a patch leaves bytes outside its span unchanged; offsets from a relative-length green tree; one passing test per doc 04 writer rule | CI | M1 config crate; M2 kernel | M0 |
| SP-10 | Snapshot benchmark | doc 45 OQ5; ui-shell §11 | Commit plus snapshot publish on a 5,000-entity synthetic mission against the < 2 ms target; decides whether the document-thread fallback is needed | Dev machine | M2 kernel | M0; re-measured M2 |
| SP-11 | Local model confirmation run | doc 44 §5.4 item 1 | Gemma 4 E4B QAT, Qwen3.5-4B Q4_K_M and Granite 4.1 3B on a doc 25 E4-sized Pick instrument: 100 menus, 20 with a planted "none fit", k = 3, long enough to test doc 21 §12.3's consecutive all-pass trials; `tools/local-qual` with the sampler pinned | Owner's 8 GB GPU | DG006, DG012; M6 shape grants | M0 |
| SP-12 | Provider wires | D021 "Revisit if"; agent-runtime §3; doc 12 §3 | Structured output, cache breakpoints and per-message effort through an exact-pinned rig release versus thin clients of our own; cache fields reach the wire; decides `plotroom-provider-http`'s shape | Cassettes plus opt-in live calls | M6 | M0 |
| SP-13 | Local inference | doc 13 §11 S1, S2, S4, S5 | S1: ≥ 99.5 % of 200 constrained responses parse and validate on llama-server and Ollama; cancel returns control in ≤ 250 ms. S2: 50/50 start → generate → stop cycles; 0 orphans after 10 forced editor kills; port collisions handled. S4: resume after kill 10/10; tampered file rejected; atomic install; low-disk pre-check. S5: byte-identical chat templates. Phase B ships when S1, S2 and S4 pass. The managed sidecar is now the owner's primary runtime (D022 amendment note); doc 46 met S1's parse criterion (0 failures in 4,356 calls) and the sidecar start → probe → generate → stop path once, on one Windows machine with the Vulkan build | Doc 13's three reference machines | M6 Model Manager | Before M6 |
| SP-14 | Model downloads through `plotroom-net` | crate-map §2.3; D022 consequences | Can `hf-hub` route through `plotroom-net`'s verified, resumable download API; otherwise re-implement its URL scheme there. Doc 46 §1.3 already downloaded pinned files with three plain HTTPS calls (commit, file tree, `resolve/<commit>/<file>` with range resume), which is the fallback | CI stub server | M6 | Before M6 |
| SP-15 | rmcp over the guarded HTTP client | doc 22 step 2 | rmcp's Streamable HTTP client uses our `plotroom-net` client, so SSRF, redirect and egress checks apply on the final request path | CI stub servers | v1.4 T2 connectors | v1.4 |
| SP-16 | wasmtime LTS host | doc 22 step 3 | Fuel, epoch deadlines and `StoreLimits` bound CPU and memory; forbidden WASI imports fail to instantiate; a documented process for shipping wasmtime security releases | CI | v1.4 T1 | v1.4 |

Doc 13's S3 (embedded `llama-cpp-2`) and S6 (a pure-Rust comparison) are v2 items ([v1x-and-v2.md](v1x-and-v2.md#v2-and-later)).

## 3. The P0 questions

### 3.1 SP-06: installs and data, including the free demo

1. Discovery on real machines: Steam Remastered (app 65790), the free demo (app 4819000), GOG, user-chosen CE builds and legacy 1.99;
   library folders and app manifests parsed purely (doc 08 §5.1–§5.2). Discovery spawns nothing.
2. Does `PoseidonGame` start without Steam running? Does the Linux build run outside the Steam runtime? Boot-to-mission time on
   typical hardware (doc 08 §6 P0).
3. **The free demo.** Which worlds and UI resources does the demo data contain (doc 05 [U])? Is it enough to render the classic map and
   dialogs faithfully when no full install exists (game-integration OQ2)? Does a CE full-game `PoseidonGame` on demo data open the editor
   displays and run `--test-mission`, as the CE build docs and BI's editor tests suggest (doc 05 §7; doc 08 §5.3, "demo-only user")?
   `PoseidonGameDemo` has no editor module and is never used for Preview (doc 08 §2.1). Whether the demo's terms restrict use with
   third-party tools is a question for OWQ-10's letter, not for the spike.
4. Is `PoseidonServer` present in the Steam depot (needed later for Preview P4)?

**Exit.** Answers recorded in doc 08's verification notes and game-integration §14; synthetic discovery fixtures updated to match;
a go/no-go on "demo data is a supported editor-visuals source" for M1.

### 3.2 SP-07: Preview flags and the harness link

1. Do the Steam 3.0x Windows and Linux binaries honour `--test-mission`, `--harness 0`, `--check` and `--render dummy`?
2. What does a positional `…/name.Island/mission.sqm` do: open the in-game editor or play? If it plays without AutoTest and survives an
   `eval` error under `--harness 0 --no-strict`, it is DG001's option B for a tolerant console.
3. Does `--private` have side effects in single-player Preview (I42-08; doc 42 OQ10)? If none, every launch carries it.
4. The harness link: does a client that connects at once reach the loopback port (small listen backlog); what does `describe` list;
   does the port close on exit (doc 08 §2.5; doc 24 §4)?
5. Can a campaign start at a chosen row from the command line, and does `--test-mission` read a campaign `description.ext` (I29-08;
   ER-007)?
6. On 1.99, through SP-08: does it accept a positional `mission.sqm`, and does its exporter skip dot-directories (doc 45 OQ1; the
   `.plotroom/` spelling)?

**Exit.** Answers recorded in doc 08 and game-integration §14; register rows ER-004 to ER-007 updated with the evidence; DG001 gains
the positional-launch result; the `--private` rule confirmed or withdrawn in game-integration §6.

## 4. Probe suites

### 4.1 Remastered and CE (automated, local, opt-in)

Probes are generated synthetic missions with a declared outcome (END1–6, LOSE, a script-asserted pass or fail, or timeout), including
negative probes that must fail, run through `--test-mission --check` plus the harness by `plotroom-preview::probe` (game-integration
§10). They are never part of CI.

| Probe list | Source | Needed by |
| --- | --- | --- |
| Upstream tests observable only in game (20 `adapt-as-probe` rows) | doc 20 §4; `docs/porting/upstream-test-map.csv` | M3 (preview-harness, mission-model, script-lang, platform-paths), M5 (campaign) |
| SP-07's questions as repeatable probes | §3.2 | M3 |
| Mod behaviour probes | doc 27 phase M3, OQ1 | M3 |
| Doc 33 demos ("Show me in game") | doc 33 phase 3, 33-AT6 | M4 |
| Attribute probes PP1–PP12 | doc 37 §11 | M4 (Remastered), M5 (1.99 part) |
| No-code ladder probe entries | doc 31 §10 | M5 |
| Cutscene-node probes (title speed, `camDestroy` without terminate) | doc 32 §7 phase 0, OQ8 | M5 |
| Campaign probes (state across rows, prologue behaviour, reading another campaign's save) | doc 19 §9; doc 34 OQ3 (I34-18) | M5 |
| Strategic layer PR01–PR22 and doc 34 OQ1's list | doc 29 §9; I34-29 | v1.1 |
| Cinematics CP1–CP13 and doc 32 phase 0 | doc 39 §10; doc 32 §7 | v1.2 |
| Atmosphere AP1–AP18 | doc 41 §9 | v1.2 |
| Replayability P-R1–P-R12 | doc 43 §8.1 | v1.3 |

### 4.2 1.99 (manual, SP-08)

1.99 has no harness and no test verbs, so its backend is manual (doc 20 §4.4). Proposed order:

1. **Before M2** (by hand, with SP-07; no Plotroom code needed): the P0 1.99 questions (§3.2 item 6), because M2 freezes the
   `.plotroom/` spelling only once the 1.99 exporter's handling of dot-directories is known (m0-m3, M2 "Spikes and probes first";
   architecture README §8 item 1). Anything left over runs in M3.
2. **M5:** doc 19 OQ1's lowering whitelist, which gates freezing `Cwa199` lowering; doc 37 PP1–PP6 for attributes; doc 27 OQ1's mod
   behaviour on 1.99.
3. **v1.1:** doc 29 PR01–PR22 (AC17 needs PR01–PR18 and PR20, PR21 when kill credit is on, plus a manual three-op run).
4. **v1.2:** doc 32 OQ1, doc 39 CP8 and the doc 41 AP rows that concern 1.99.
5. **v1.3:** doc 43's P-R rows and PR20 (RAT7).

### 4.3 Recording results

- Results promote catalog entries between evidence tiers (doc 35 §8.3) and clear "unverified on …" badges (D003).
- Where a probe replaces an upstream test, its row in `docs/porting/upstream-test-map.csv` moves to `probe` with the result.
- Our own probes are not upstream tests (doc 43 §8.1 note). **Proposal:** record them in one tracked table,
  `docs/porting/probe-results.csv` (probe id, source doc, profile, build, date, result, probe hash), created with the first result.
- A probe that shows an engine limitation adds or updates an `ER-###` row in the same change set (D012).

## 5. Local model qualification track

| Doc 44 §5.4 item | Measurement | Milestone | Feeds |
| --- | --- | --- | --- |
| 1 | Confirmation run (SP-11) | M0 | DG006, DG012; M6 defaults |
| 2 | One grader for explain, text and knowledge; a blind human panel for text | Before M6 | Badges for explanation and text |
| 3 | UD versus Q4_K_M for Qwen3.5-4B, sampler pinned, paired by item | Before M6 | Model Manager manifest |
| 4 | Harder menus: closer distractors, 7 options, code-generated menus, more escapes including `Q` | Before M6 | DG006 (5 or 7) |
| 5 | The `--why` variant; thinking on versus off with its latency | M6 | DG020 (effort table) |
| 6 | Bigger local models (9B, 12B) on 8 GB with offload and on 12–16 GB cards: does Fill reach pass^3 ≥ 0.8 per record? | M6 | T2 tier grants |
| 7 | Czech, Polish and Russian requests for Fill and text | M6; v1.4 locales | Non-English support claims |
| 8 | Code-selected cards instead of perfect ones | M6 (cards from M4) | Card selection (doc 30 §4.2) |
| 9 | Other machines and runtimes; llama-server against Ollama parity; cold loads and swaps | With SP-13 | Model Manager fit rows |
| 10 | Text with the style card and code-stripped callsigns | M6 | Text qualification |

**Results so far (2026-09-27).** Doc 46 ran items 3 and 4 and part of 9 on one 8 GB Pascal machine: the UD quant showed no
detectable gain over Q4_K_M for Qwen3.5-4B or Gemma 4 E4B; the harder `pick-hard` menus (30 menus, 7 options plus `X`, 3 planted
escapes) pull model families apart, though not yet significantly, and do not separate quants; llama.cpp and Ollama showed no detectable
Pick difference, with slower prompt processing on llama.cpp's Vulkan build. Its data is in
`docs/research/data/runtime-quant-comparison.csv`. Doc 49 measures doc 47's local shortlist, including a CUDA-versus-Vulkan comparison
that decides whether the user-started CUDA build is offered (D022 amendment note). The owner deferred doc 48's cloud round 1 (about
$6.63, owner-run) until doc 49 exists (owner decision, 2026-09-27).

Results go into `docs/research/data/local-qualification.csv` until `plotroom qualify` writes qualification records (M6). Badges stay
"spike-checked" until doc 21 §12.3's product qualification exists for a setup; reaching it for the recommended default local setup is a
v1.0 stretch goal, not a gate (architecture agent-runtime §7).

## 6. Other measured evidence

| Evidence | Source | When |
| --- | --- | --- |
| Performance budgets (commit and publish, overlay build, GPU submit, frame rate, idle CPU) | ui-shell §11; doc 06 §4.10 | M0 (spikes), M2, v1.0 |
| Evaluation instruments E1–E12 with controls | doc 25 §11; doc 40 §7 | M6; re-run at v1.0 and for each new workflow |
| Cost model comparison: E12's measured cost per admitted decision against doc 40 §5's modelled figures | doc 40 §5, §7 | M6 |
| Moderated studies: 33-AT8, 33-AT9, PAT15, 31-AT1's newcomer session | docs 31, 33, 37 | First study after M4 to set targets; v1.0 |
| Delayed transfer study: 33-AT11 (a week later, tutor mode no worse than no AI) | doc 33 §9 phase 5 | After M6's tutor mode; reported in v1.x |
| Moderated studies: AC16 (fun panel), 32-AT6, DAT13 | docs 29, 32, 39 | v1.1, v1.2 |

## Verification notes

### Roadmap baseline (2026-09-27)

- Spike criteria re-read from doc 06 §7, doc 08 §6 (P0), doc 13 §11, doc 22 §7.1 and doc 44 §5.4; probe lists from doc 20 §4,
  game-integration §10, docs 19 §9, 27 §4.12, 29 §9, 31 §10, 32 §7, 33 §9, 37 §11, 39 §10, 41 §9 and 43 §8.

### Owner decisions and doc 46 folded (2026-09-27)

- SP-13 and SP-14 note what doc 46 already showed; §5 gains "Results so far" from doc 46's TL;DR, §2 and §4, and the owner's
  deferral of doc 48's round 1 until doc 49. No exit criterion changed: doc 46 ran on one machine, and doc 13's criteria ask for three.
