# Testing strategy

> **Status:** proposal (architecture baseline 2026-09-27). Nothing here is decided unless it restates `AGENTS.md`, a decision
> record (`Dnnn`) or a decided DG. Names are not final.
> **Part of:** [architecture overview](README.md). **Main sources:** `AGENTS.md` (test-first, testing standards, porting, evidence);
> doc 04 §13; doc 06 §4.9; doc 07 §16; doc 19 §9; doc 20; doc 21 §12; doc 25 §11; doc 38 §6.4, §10; doc 40 §7; doc 44; doc 45 §2.10;
> D013, D016, D017; DG018.

Tests are the proof artifact, not cleanup: red → green → refactor, documented `#[test]`s with what/why/how doc comments, section headers
in the standard order, synthetic fixtures only, and ported upstream tests travelling with the code they cover (`AGENTS.md`; D013). A
feature is not "done" without named evidence (`AGENTS.md` "Evidence Rule").

## 1. Principles

1. **Everything below the shell runs headless.** The session, the store, dialogs, the map interaction state machine, the renderer's
   draw lists, the workflow runtime and Preview staging are libraries with no egui types ([crate-map.md](crate-map.md)).
2. **Determinism is injected.** `Clock`, `IdSource` and seeds are parameters; tests use a virtual clock and seeded ids; no sleeps, no
   environment mutation (doc 45 §2.10).
3. **No network, no game install, no proprietary data in CI.** Cassettes stand in for providers, fake processes and servers for the
   game and remote services, synthetic builders for game files (`AGENTS.md` fixture legality).
4. **Ported tests are the floor.** Our own boundary, overflow and adversarial tests go on top.
5. **Every fixed bug** gets a regression test plus adversarial tests in the same change set (`AGENTS.md`).

## 2. Test layers

| Layer | What | Where it runs |
| --- | --- | --- |
| Unit and ported upstream tests | Parsers, writers, lenses, rules, planners | Every push, 3 OSes |
| Property tests (proptest, seeded and bounded) | Round trips, undo/redo, plan == apply, CXL lowering | Every push |
| Kernel harness | `EditorHarness` driving the real `Session::step`, invariants after every step | Every push |
| Data-driven goldens | Lowering, staging, export, capsule prefixes, journals | Every push |
| UI | `DrawList` snapshots, headless wgpu golden images, `egui_kittest` | Per pull request |
| Edge fakes | Fake game binary, fake harness server, MCP and feed stub servers | Per pull request |
| Fuzzing | cargo-fuzz targets in a separate nightly workspace | Nightly |
| Evaluation instruments | E1–E12 on cassettes; qualification on local models | On demand, locally |
| In-game probes | Probe missions on real installs | Locally, opt-in; never in CI |

## 3. Formats and fuzzing

Every parser module has the `AGENTS.md` categories: happy path; each `Error` variant with its structured fields; `Display` containing
the numeric context; determinism; both sides of every boundary; `u32::MAX` and near-max overflow inputs; adversarial inputs for every
safety guard. In addition:

- **Golden fixtures** built in code (doc 04 §13): minimal missions, every key non-default, defaults explicit, legacy versions,
  aliases, unknown keys, comments and preprocessor lines, CRLF/LF/space variations, duplicate keys, item-count mismatch, triggers with
  group sensors, a 2,048-byte init field, legacy code-page bytes.
- **One test per writer rule** ([core-document-model.md §4](core-document-model.md)), including float formatting edge values.
- **Caps tests:** a varint longer than 32 bits, counts larger than the remaining bytes, pool gaps, BI LZSS output-ratio limits
  (doc 07 §16).
- **cargo-fuzz** targets mirror CWR's 16 libFuzzer harnesses, with header forcing, in a nightly `fuzz/` workspace (D017). Parsers of our
  own formats (sidecar DTOs, journal segments, pack manifests, TOML definitions, CXL, seed codes) get fuzz targets too, because shared
  projects and packs are untrusted input.

## 4. Porting upstream tests (D013)

`docs/porting/upstream-test-map.csv` tracks 636 upstream tests. By relevance (column `relevance`): 74 `port-now`, 68
`port-with-module`, 20 `adapt-as-probe`, 102 `reference`, 372 `not-applicable` (doc 20); by status: 142 `todo`, 20 `probe`, 102
`reference`, 372 `not-applicable`. Target areas map to crates:

| Target area | Crate(s) | Rows needing work (status `todo`) |
| --- | --- | --- |
| formats-pbo | `plotroom-pbo`, `plotroom-bytes` | 11 |
| formats-config | `plotroom-config`, `plotroom-preproc`, `plotroom-stringtable` | 23 |
| script-lang | `plotroom-script`, `plotroom-script-catalog`, dev-only `plotroom-script-oracle` | 20 (plus 3 probes) |
| mission-model | `plotroom-mission` | 8 (plus 4 probes) |
| formats-paa, formats-font, formats-wrp, formats-p3d, formats-audio | `plotroom-paa`, `plotroom-fxy`/`plotroom-fonts`, `plotroom-wrp`, `plotroom-p3d`, `plotroom-audio` | 15, 4, 13, 10, 5 |
| editor-core, editor-ui | `plotroom-project`, `plotroom-commands`, `plotroom-view`, `plotroom-ui-classic`, `plotroom-rsc` | 6, 12 |
| map-render | `plotroom-map2d`, `plotroom-draw2d` | 1 |
| campaign | `plotroom-campaign`, `plotroom-campaign-compile`, `plotroom-campaign-sim` | 1 (plus 10 probes) |
| platform-paths | `plotroom-install`, `plotroom-vfs` | 5 (plus 1 probe) |
| preview-harness | `plotroom-preview`, `plotroom-gamelink` | 8 (plus 2 probes) |

- Order follows doc 20 §3: PBO first, then config, script, mission model, images and fonts, then editor modules with the code they cover.
- Each ported test keeps the upstream inputs and expected outputs (known-value cross-validation) and cites repo, commit, file and case
  in its doc comment. Tautological upstream assertions become source-derived goldens tagged `unverified-1.99`.
- A fixture that is not clearly redistributable is rebuilt synthetically; if that is impossible, the test is opt-in behind an
  environment variable (§15).
- The CSV row is updated in the same change set (status, target crate or module, reason). The CSV has a `target_area` column but no
  crate or module column, which `AGENTS.md` asks for; **proposal:** the first porting change set adds a `target_module` column
  (crate and module path), filled for every row it ports. Tests translated from third-party projects (for example TrenchBroom's
  command-processor tests, GPL-3.0-or-later) are recorded per DG018, not in this CSV.
- Upstream tests observable only in the running game become probes (§13).

## 5. Round-trip and property tests

| Property | Test |
| --- | --- |
| `render(parse(b)) == b` over random CSTs with injected trivia | proptest in `plotroom-config` |
| Random typed mission → canonical render → parse gives an equal model | proptest in `plotroom-mission` |
| Every writer: write → read round trip | proptest per writer (D017) |
| After every commit: bytes outside patched spans unchanged; lens equals re-derived lens | `verify_round_trip_each_commit`, always on in tests and CI |
| Random op sequences → undo all → byte-identical CST and sidecar; redo all → pre-undo state | kernel proptest |
| Applied diff equals planned diff | kernel proptest and a debug assertion |
| `interp(ast) == mini_sqs_interp(lower(ast))` for CXL | campaign proptest (doc 19 §9) |
| Preserve-mode campaign import re-saves byte-identical | campaign tests (doc 19 §7.6) |
| Sidecar DTO write → read and every `migrate_vN_to_vN1` on golden fixtures | sidecar tests |

An opt-in local corpus run (`PLOTROOM_CORPUS_DIR`) checks round trips on real missions and prints only hashes and counts.

## 6. Kernel tests

`EditorHarness` (in `plotroom-testkit`, a dev-dependency) drives the real `Session::step` with scripted gestures: `add_unit`,
`drag_waypoint`, `dialog_ok`, `paste`, `apply_template`, `wilco_turn(script)`, `undo`, `redo`, `save`.

- **`validate_invariants()` after every step:** the id map is complete and one-to-one; no sync or attachment dangles; `ItemN` is
  contiguous and agrees with `items=`; the incremental lens equals the re-derived lens; no group is open at rest (doc 45 §2.10).
- **"One action is one undo step" family:** `drag_waypoint_is_one_undo_step`, `dialog_ok_is_one_undo_step`,
  `paste_group_with_waypoints_is_one_undo_step`, `apply_template_is_one_undo_step`, `power_tool_apply_is_one_undo_step` (doc 37 G8),
  `fix_all_is_one_undo_step`, `migration_is_one_undo_step`, `module_drop_is_one_undo_step`,
  `confirm_mode_turn_with_many_tool_calls_is_one_undo_step`, `auto_mode_step_is_one_undo_step`.
- **Command-processor event-log tests**, written red-first with a recording log and a mock command: commit, rollback, nested, scopes,
  modification, collation.
- **Dirty state:** undo back to the save point is clean; a sidecar-only edit is dirty; saving with a pending proposal writes the
  pre-proposal bytes.
- **Identity:** reopen keeps ids; a simulated engine re-save (Compact) re-matches; merging two branches never collides; deleting a unit
  with a synced trigger from the middle of a group, then undoing, restores sync, selection and bytes; a `PreviewEntity` has no
  serializer; selection never reaches a saved file.
- **Admission:** a rejected batch never enters history; a non-user origin cannot write a human-owned or pinned field without
  `UserIntent`; `UserIntent` cannot be constructed outside `plotroom-session` (a layering test, §13).
- **Registry:** the per-OS shortcut-clash test; a schema snapshot of every `CommandSpec`; every agent-callable command belongs to a
  workflow or the read-only query set (doc 21 §6.4); every public mutator emits at least one op.
- **Classic dialogs and map:** syncing a changed value into every control type emits zero commands (doc 45 §2.5); ported map behaviours
  from doc 03 (100 m auto-join, Del versus Shift+Del, marker hit-testing outside the marker mode).
- **Undo-spam detector** test.

## 7. Validation and lowering tests

- **Every diagnostic code** carries a failing and a passing fixture; `xtask` generates one test per fixture from the registry data
  (DG005; [validation-and-lints.md §5](validation-and-lints.md)).
- Every rule runs twice on one snapshot with equal output; results are compared per profile; acknowledgement fingerprints invalidate
  when the read fields change; no finding lacks both a fix and a dismiss (I36-21); "not run" is reported apart from "pass".
- **Lowering goldens** are data-driven `{input.sqm, rule.ron, seed, expected.sqm}` triples per profile; every emitted SQS line passes
  `check_field` in the right mode; the "Requires" badge equals the maximum availability actually emitted.
- **Export contains no trace tokens and no agent leftovers** (doc 21 §12.4 G7; doc 45 §4.7).
- **Region states:** a hand edit to generated content becomes `Customized` and is never overwritten silently (doc 31 §8.3).
- **Lowering failure classes:** an invariant violation refuses only groups that touched the element's inputs; a compiler error keeps
  the last good output as Stale ([commands-undo-history.md §5](commands-undo-history.md)); a per-hook latency budget test.

## 8. Campaign tests

- CXL: parser fuzzing, scope typing, interval and coverage tests; the interpreter-versus-lowering property (§5).
- Compile goldens for sockets, routers and finishers; Path Explorer coverage; import in Preserve and Adopt modes.
- **"Operation Grey Heron" as a synthetic structural fixture** (doc 29 §8; D005): built early to stress the campaign model, compiler and
  runtime, long before the strategic layer ships.
- The balance lab across seeds, in v1.x.

## 9. Workflow runtime, model I/O and cost

Following doc 38 §6.4 and AT-W1 to AT-W15, doc 21 §12 and doc 40 §7:

- **Load-refusal fixtures** for the definition compiler (AT-W1), including a `schema` key on a Pick step (DG015) and effort predicates
  on `ask`/`approve` steps (DG013).
- **Golden journals** replayed in CI; **cassettes keyed by capsule hash**; a cassette miss fails CI; no test reaches a network.
- **Crash at every journal entry:** the resumed run reaches the same document with zero extra model calls for settled entries (AT-W3);
  the journal reader truncates a torn tail and survives adversarial segments.
- **Concurrency 1 and 8 give identical documents and canonical journals**, including under a budget that runs out mid-`map` (AT-W9).
- Cancelling any step leaves no half-applied edit; a commit the user undid is never re-applied.
- **Faux model as a state machine** (proptest-state-machine): walks every menu letter including `X` and `Q`, malformed, truncated and
  duplicate-key replies, timeouts and cancellations.
- Human edits during a run are never clobbered (E9; AT-W10); a no-model run gives 100% validity (E10; AT-W11); a hostile pack gains
  nothing (AT-W14); external runs wait for an editor click (AT-W15).
- **Effect table:** every `AgentTool` × `AgentEffect` pair (doc 21 §1.3); no agent tool can start a download (D008 tests).
- **Capsule prefixes:** a golden test renders every `DecisionKind` prefix from synthetic fixtures and asserts byte identity across
  decisions, runs and machines (doc 40 R2); nothing volatile sits above a breakpoint (R3); token-budget and prefix-stability
  regressions fail CI.
- **Wire tests per `CachePolicy`** assert that cache fields reach the wire (R10); price-table checks: no prices in Rust, and the
  staleness chip appears after 60 days (I40-14).
- **Injection fixtures:** mission text addressing the assistant changes nothing; hidden Unicode renders visibly.
- The full suite runs with no provider configured (doc 21 §12.4 G4).
- End-to-end acceptance: "put some guys near the town" (IntentFill → plan card → `map` over sockets → one commit group → provenance →
  one Ctrl+Z removes everything).

## 10. Evaluation instruments and qualification

- `plotroom-evals` holds doc 25's instruments E1–E11 and doc 40's **E12** (each workflow × preset on synthetic fixtures, sweeping effort
  none/low/medium and K fixed versus adaptive per shape; pass^k and dollars per admitted decision; settles R6 and R7; I40-25), with
  controls: no model, random-valid and always-ask (doc 21 §12).
- It ports `tools/local-qual`'s suites (Pick, the harder `pick-hard` menus, Fill, explain, text, knowledge) to Rust; `plotroom
  check`'s sibling `plotroom qualify` writes qualification records per (setup, `DecisionKind`, field), which drive shape grants and the
  Model Manager's badges ([agent-runtime.md §7](agent-runtime.md)). Doc 44's measurements (Ollama) and doc 46's (the managed
  `llama-server` runtime the owner chose on 2026-09-27) seed the first records as "spike-checked"; each badge names its suite, suite
  version and n, because `pick` and `pick-hard` disagree for some models (doc 46 §4.1).
- Doc 30's knowledge tasks and doc 33's trap benchmark become knowledge instruments.
- Instruments run locally on demand; CI runs them only against cassettes.

## 11. UI tests (D016)

- `insta` snapshots of `DrawList`s per control recipe and map layer, on synthetic data.
- Batcher unit tests: UV re-interpolation on clipping, the 32-vertex polygon cap, batch splits, vertex bytes.
- Headless wgpu golden images on WARP (Windows) and lavapipe (Linux), with per-OS baselines; macOS goldens stay ignored until a Metal
  runner is proven.
- `egui_kittest` per simulated OS with persistence off; the Wilco panel runs against a deterministic fake model with a fixed step count;
  **Drill lessons double as kittest scripts**, and each lesson's reference solution is replayed in CI (doc 33 §5.1).
- A local-only fidelity comparison against in-game screenshots, never committed.

## 12. Process, network and plugin edges

- **A fake game binary** built as a test helper: exit codes, jsonl output, a hang followed by a kill; `LaunchSpec` argument tests per
  executable flavour; `StagePlan` golden folders, including Intro/Outro through the intro fallback and the campaign prologue.
- **A fake loopback harness server** for `plotroom-gamelink`: the verb allowlist, malformed lines, oversize replies.
- **Stub servers** for T2 connectors and feeds: pin drift, SSRF including IPv4-mapped IPv6 and redirect chains, oversize output,
  non-https URLs, hostile asset names (doc 42 MAT9); offline-mode refusal; hash-mismatch refusal; redirect-off-origin refusal (D008).
- **Adversarial T1 components** (v1.x): infinite loops, memory bombs, invalid UTF-8, forbidden WASI imports that must fail to
  instantiate.
- VFS and `#include` path-confinement tests; model download resume, hash verification and atomic install tests.

## 13. In-game probes

Probe missions with declared outcomes (END1–6, LOSE, script-asserted pass or fail, timeout), negative probes and a strict mode run
through the Preview harness on Remastered and CE, plus the manual 1.99 backend
([game-integration.md §10](game-integration.md)). Probes are local and opt-in, never in CI; their results update evidence tiers and
`probe` rows in the upstream-test map.

## 14. CI matrix and gates

| Gate | Runs |
| --- | --- |
| `cargo fmt --all --check`; `cargo clippy --workspace --all-targets --locked -- -D warnings`; `cargo test --workspace --locked`, doctests included (never `no_run` or `ignore`) | Windows, Ubuntu, macOS |
| Workspace lints: `unsafe_code = "forbid"`; `unused_must_use` and `deprecated` at deny; clippy `indexing_slicing`, `string_slice`, `unwrap_used`, `expect_used`, `panic`, `unreachable`, `todo`, `unimplemented`, `let_underscore_must_use` and `allow_attributes_without_reason` at deny in production code; `arithmetic_side_effects` in format crates ([crate-map.md §2.4](crate-map.md)) | With clippy |
| Map-indexing check: a small custom check for `Index` on maps, which `indexing_slicing` misses ([crate-map.md §2.4](crate-map.md); doc 62 §3.2) | With clippy, once it exists |
| Negative compile tests: `trybuild` UI tests in `tests/ui/` for every witness, guard, typestate and sealed-trait misuse, with committed `.stderr` snapshots (`AGENTS.md` "Negative Compile Tests") | One job on a pinned toolchain, because compiler text changes between releases (which OS: doc 62 OQ5); snapshots change only with a toolchain bump or a reviewed guidance change |
| `xtask layers`: the declared layer table against `cargo metadata`; the evidence test is that a deliberately bad edge fails | Every push |
| `cargo-deny`: licence allowlist (GPL-3.0-compatible; bans GPL-2.0-only crates), advisories, banned crates and features per layer | Every push |
| Per-crate clippy `disallowed-methods`/`disallowed-types` for `std::fs`, `std::process`, `std::net`, `std::env::var` outside the edge crates; each `reason` names the sanctioned API, with no `replacement` unless the call shape is identical ([crate-map.md §2.4](crate-map.md)) | With clippy |
| REUSE/SPDX check; `Derived-From:` headers on ported files; DG018 records for third-party ports | Every push |
| Public-hygiene grep: third-party marks and island names in crate, module, format, sidecar and generated-header names; private project names | Every push |
| `xtask` drift checks: generated code registry, script catalog against its pinned inputs, Standing Orders index, skill index, provenance records | Every push |
| Fuzzing | Nightly |

Tiering keeps three-OS CI fast: unit, property and kernel tests on every push; golden images and kittest per pull request; fuzzing
nightly. Property tests use seeded, bounded configurations.

## 15. Fixtures, environment variables and determinism

- Fixtures are built in code by `plotroom-testkit` builders (`SqmBuilder`, synthetic PBO, WRP and raP builders, a synthetic island and
  catalog); no island names or game marks in fixture names.
- Opt-in local variables: `PLOTROOM_GAME_DIR` (an installed game, for install and catalog tests) and `PLOTROOM_CORPUS_DIR` (a local
  mission corpus, for round-trip runs). Such tests print only hashes and counts and never commit output.
- Every milestone in the roadmap lists the named tests or artifacts that prove it.

## 16. Open questions

1. *Answered (2026-09-28, doc 62 §3.2):* clippy's `indexing_slicing` does not cover `Index` on maps (`map[&key]`), so a small custom
   check enforces `AGENTS.md`'s "any type" rule ([crate-map.md §2.4](crate-map.md)). Still open: an `xtask` check or a dylint lint.
2. Which clippy configuration keys exempt test code for each lint, and where `cfg_attr(test, allow(...))` is needed instead.
3. A Metal runner for macOS golden images.
4. The corpus size and composition for re-match threshold measurements (doc 45 OQ9).
5. How long CI may run on three OSes before tiers are rebalanced.

## Verification notes

### Type-driven guidance folded (2026-09-28)

- §14 follows `AGENTS.md`'s amendment of 2026-09-28 (doc 62 §8, applied under the owner's go-ahead): the lint row lists the four
  guidance lints; new rows for the map-indexing check and the pinned trybuild UI-test job; §16 item 1 is answered by doc 62 §3.2's probe.
