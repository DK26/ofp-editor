# rust-weak-models: PLAIN vs GUIDED Rust APIs for small coding models

**Research instrument, not product code.** This folder holds the experiment behind
[research doc 64](../../docs/research/64-rust-and-weak-models.md): do small local models write more
correct Rust against an API that leads them into correct usage (typestate, witness and guard types,
unit newtypes, `#[diagnostic::on_unimplemented]` fix hints, doc comments written as instructions)
than against an idiomatic, runtime-checked API with identical functionality? `design.json` is the
pre-registration draft. Nothing here is built into, linked by or run by Plotroom, and the product never
executes model-written code. The harness evaluates how Plotroom is developed and how its agent
doctrine should be shaped; it is not a feature.

Standard library only (Rust and Python 3.11+; the pilot used rustc 1.98.1 and Python 3.12.4). The
Cargo workspace has no external dependencies, so `cargo --offline --locked` always works once the
task crates are generated. Results of any run stay local (`results/` is git-ignored); doc 64 holds
the numbers.

## Verify a fresh clone

From this folder:

```text
python -m unittest test_rwm                  # 53 harness tests; no cargo, no model, no scaffold needed
python runner.py scaffold                    # writes the 68 task crates and Cargo.lock (under 1 s; git-ignored)
python runner.py verify --tasks all          # 68/68 reference runs: visible and hidden tests, both variants
cargo test --workspace --offline --locked    # 406 Rust tests (crates, visible and hidden task tests)
```

`verify`, `mutants`, `conformance` and `run` stop with the command to run when the scaffold output
is missing. The first `verify` compiles everything (about 2.5 minutes); later runs reuse `target/`.

Model-free re-derivations of doc 64's other numbers (each writes under `results/`):

```text
python runner.py listing                     # API listings, system prompts, prompt-budget report
python runner.py run --dry-run --tasks all --samples 6   # every prompt, no model, no cargo
python runner.py conformance --tasks all     # PLAIN and GUIDED references export byte-identical text
python runner.py mutants --tasks scored      # static catch rate of the 13 trap mutants
python power_sim.py 500                      # the power simulation doc 64 quotes (about 20 s)
python -m rwm.hygiene                        # hidden characters, local paths, enclosing workspace
```

## How the repository's rules apply here

`AGENTS.md` governs Plotroom's product crates. This folder is research tooling, so:

- **Apply fully:** public-repository hygiene (no private project names, local paths, user names or
  keys; `python -m rwm.hygiene` and `test_rwm.Hygiene` check it), the naming rule (no third-party marks
  in crate, module or format names: the crates are `mb-*`, the export format is `mbx`), test-first
  changes to the harness (`test_rwm.py`), the friction review and the evidence rule.
- **Fast inner loop:** while changing Rust here, `cargo clippy -p <crate> --all-targets --offline`
  and that crate's tests (`cargo test -p <crate> --offline <filter>`); while changing the Python,
  `python -m unittest test_rwm -k <name>`. Finish with the four verification commands above. Clippy
  is not clean on the stimuli and they are left as they ran: on 2026-09-28 it reported 6
  `collapsible_if` warnings (mb-core 3, mb-oracle 2, mb-plain 1; mb-spec and mb-guided clean), so
  compare against that baseline instead of passing `-D warnings`. A clippy-feedback arm would need a
  clean baseline and its own `clippy.toml` here first.
- **Do not apply to the stimuli:** `crates/`, `tasks/`, `pilot/` and `prompts/` are the experiment's
  independent variable and its fixed inputs, not product code. PLAIN is deliberately idiomatic
  runtime-checked Rust and GUIDED deliberately typestate-driven; bringing either closer to the product
  rules (one `Error` enum per crate, no `unwrap`, the newtype table, file-size ceilings) would change
  what is measured. A change there is an experiment change: record it under "Deviations" (and in
  `design.json` before freezing) and re-run `verify`, `conformance`, `mutants` and `listing`.
  Model-written `src/solution.rs` files are data; every test crate carries `#![forbid(unsafe_code)]`
  and a static scan rejects process, file, network, environment and include escapes before compiling.
- **Building and running:** the product rule "agents do not run `cargo build` or `cargo run`" is about
  Plotroom. Here the runner compiles task crates as its instrument, and agents may run the verification
  commands above. Live model runs take GPU hours and are started only when the owner asks.

## Standalone workspace

This folder is its own Cargo workspace (`Cargo.toml` is a virtual manifest). A repository-root
workspace does not exist yet. Probed with cargo 1.98.1 on a nested copy:

- a root `members` glob that matches this folder itself (`"tools/*"`) fails loudly: "multiple workspace
  roots found in the same workspace";
- a root `members` entry or glob that reaches a crate inside it (`"tools/*/*"`,
  `"tools/rust-weak-models/crates/mb-core"`) is adopted **silently**: the root builds it with the
  root's lock file, profiles and lints, while cargo run from inside this folder still uses this
  workspace;
- `exclude = ["tools/rust-weak-models"]` in the root filters globbed members, but an explicit member
  path still wins over `exclude`.

So the root `Cargo.toml`, when it is created, must carry `exclude = ["tools/rust-weak-models"]` in its
`[workspace]` table and must never name a path below this folder as a member (`CODE-INDEX.md` §3
records the rule). Configuration also leaks downward: a root `rust-toolchain.toml` or `.cargo/config.toml`
would change the compiler or flags the experiment uses (a toolchain pin can even trigger a rustup
download, which an offline run must never do), and clippy and rustfmt read the nearest `clippy.toml` or
`rustfmt.toml` above a crate, so a clippy-feedback arm must pin its own `clippy.toml` in this folder.
`test_rwm.EnclosingWorkspace` fails, naming the fix, if any `Cargo.toml` workspace, `rust-toolchain`
file or `.cargo/config` between this folder and the repository root would reach it.

## Layout

```text
crates/mb-spec     task inputs (one module per task), catalogs, Refusal/Problem   (shown to the model)
crates/mb-core     hidden shared model, rule checker R1-R10, mbx writer             (never shown)
crates/mb-plain    PLAIN API  -> presented to the model as crate `mb`
crates/mb-guided   GUIDED API -> presented to the model as crate `mb`
crates/mb-oracle   independent mbx parser + rule checker used only by the tests
pilot/P01..P04     pilot tasks (never scored)
tasks/T01..T30     scored tasks: task.json, task.md, visible.rs, hidden.rs, ref_plain.rs,
                   ref_guided.rs, optional mutants.json; plain/ and guided/ are generated test
                   crates (lib name `task`, git-ignored)
prompts/           system role text, domain rules sheet (R1-R11), export-format appendix
rwm/               harness package: listing generator, prompt/budget, cargo runner, static scan,
                   model clients (OpenAI-compatible + mock), scaffolding, hygiene checks
runner.py          CLI (scaffold, listing, verify, run, mutants, conformance, summary)
test_rwm.py        harness unit tests (python -m unittest test_rwm)
design.json        pre-registration draft
power_sim.py       Monte Carlo power check of the primary contrast
diag-probe/        rustc probes: which typestate shapes let on_unimplemented text reach a model
                   (guided.rs, methods.rs with their recorded rustc 1.98 output) and the E0618 probe
live/              the live pilot: drive_pilot.py (driver), start-server.ps1 (llama-server),
                   check_server.py (pre-run check), arms.json (models, pins, samplers)
analysis/          pilot analyses: analyze_pilot.py, transition_rates.py, fix_rates.py,
                   refusal_payload.py, time_split.py, peek.py
results/           everything a run writes (git-ignored)
```

Each test crate depends on its variant as `mb` (Cargo dependency renaming), on `mb-spec`, and (dev)
on `mb-oracle`. Its fixed `src/lib.rs` has `#![forbid(unsafe_code)]`, `pub mod solution;`, a
compile-time check of the entry signature `fn solve(&mb_spec::tNN::Input) -> Result<mb::Exported,
mb_spec::Refusal>`, and `task::run(&input)`, which the tests call. The model writes only
`src/solution.rs`. `tests/visible.rs` and `tests/hidden.rs` `include!` the task's shared test files,
so both variants run byte-identical tests.

## Run a pilot

The pilot ran three local models on llama.cpp's `llama-server` (release b11146) with an 8 GB GPU,
one model at a time; each arm (34 tasks x 2 variants, R0 to R3) took 2 to 3.5 hours.

1. **Weights.** `live/arms.json` names each GGUF by Hugging Face repo, revision, file, size and
   SHA-256 (the same pins as `tools/local-qual/presets/drafts`). Put the files under one folder as
   `<repo>/<file>` and set `RWM_MODELS_DIR` to it (or pass `--models-dir`). If they live elsewhere,
   copy `live/arms.json` to `live/arms.local.json` (git-ignored; the driver prefers it) and edit the
   `gguf` paths there. The driver checks each file's size, then its SHA-256, and skips an arm whose
   file does not match its pin.
2. **Server binary.** Put `llama-server` on `PATH`, or set `RWM_LLAMA_SERVER` (or pass
   `--llama-server`).
3. **Check.** `python live/drive_pilot.py --dry-run` reports each weight file and prints the exact
   runner command per arm.
4. **Run (Windows).** Start the driver detached so it outlives the terminal, for example
   `Start-Process python -ArgumentList 'live/drive_pilot.py' -WindowStyle Hidden`. It starts one
   server per arm, checks the chat template's thinking switch (`check_server.py`), runs
   `runner.py run`, always stops the server, and refreshes `results/pilot-live/pilot-summary.txt`.
   Progress: `results/pilot-live/drive-status.json` and `drive_pilot.log`; `python analysis/peek.py
   results/pilot-live/<tag>.jsonl` shows the latest rounds. Create `results/pilot-live/STOP` to end
   after the running arm.
5. **Run (other systems).** The driver uses `tasklist`, `taskkill` and PowerShell. Start the server
   yourself (`llama-server -m <file.gguf> --jinja -ngl 99 -c 24576 -np 1 --cache-ram 4096 --port 8080`)
   and run the command `--dry-run` printed, with the port you chose.
6. **Analyse.** With the arms' files in `results/pilot-live/` (the saved replies, code and feedback
   are read from `results/pilot-live/code/`):

   ```text
   python analysis/analyze_pilot.py    results/pilot-live/pilot-summary.json    results/pilot-live/<tag>.jsonl ...
   python analysis/transition_rates.py results/pilot-live/transition-rates.json results/pilot-live/<tag>.jsonl ...
   python analysis/fix_rates.py        results/pilot-live/fix-rates.json        results/pilot-live/<tag>.jsonl ...
   python analysis/refusal_payload.py  results/pilot-live/refusal-payload.json  results/pilot-live/<tag>.jsonl ...
   python analysis/time_split.py       results/pilot-live/<tag>.jsonl ...
   ```

A single run by hand, against any OpenAI-compatible endpoint:

```text
python runner.py run --base-url http://127.0.0.1:8080/v1 --model qwen3.5-4b-q4km \
    --tasks scored --samples 6 --rounds 3 --temperature 0.6 --top-p 0.8 --top-k 20 --min-p 0 \
    --server-tokens --out results/qwen35-4b.jsonl
python runner.py summary results/qwen35-4b.jsonl
python runner.py run --mock ref|fail-first|no-code-first|mutant --tasks pilot   # pipeline proofs, no model
```

`--resume` appends to an interrupted results file only when model, tasks, sampler, rounds, seed,
context, budget and system-prompt hashes match. `RWM_API_KEY` (or `OPENAI_API_KEY`) is sent as a
bearer token when set.

## Results

The pilot's outcomes, paired comparisons, diagnostic clearance and cost are in doc 64 §3.6 to §4.8.
Which script produced which table:

| Doc 64 | Source |
| --- | --- |
| §3.6 harness evidence, §3.7 static catch rate | `runner.py verify`, `conformance`, `mutants`; `cargo test` |
| §3.5 power | `power_sim.py 500` |
| §4.2 outcomes, §4.3 paired comparisons | `analysis/analyze_pilot.py` |
| §4.4 shared spec slip and stalls | `analysis/refusal_payload.py` |
| §4.5 clearance per transition (per-block rates for comparison) | `analysis/transition_rates.py` (`analysis/fix_rates.py`) |
| Time split and compile rate per round (owner input for the revision) | `analysis/time_split.py` |
| E0618 probe, typestate-shape probe | `diag-probe/` (commands below) |

The raw records (JSONL per round and episode, saved replies, code and feedback, server checks) are
not committed: they are run output and hold model text. The pilot's records stay with the machine
that ran them; a derived CSV under `docs/research/data/` (doc 64 §6 step 8) is the planned way to
publish the numbers.

Probe commands (from `diag-probe/`, output to a folder outside the repository):

```text
rustc --edition 2024 --crate-type lib --out-dir <tmp> guided.rs     # compare with guided.err.txt
rustc --edition 2024 --crate-type lib --out-dir <tmp> methods.rs    # compare with methods.err.txt
rustc --edition 2024 --crate-type lib --crate-name spec --out-dir <tmp> e0618_spec.rs
rustc --edition 2024 --crate-type lib --extern spec=<tmp>/libspec.rlib --out-dir <tmp> e0618_user.rs
rustc --edition 2024 --crate-type lib --out-dir <tmp> e0618_local.rs
```

## The two APIs (same operations, same semantics, same exports)

Both variants are thin layers over `mb-core`, so exports are byte-identical for equivalent missions
and the rule semantics cannot drift apart.

| Concern | PLAIN (`mb-plain`) | GUIDED (`mb-guided`) |
| --- | --- | --- |
| ids | `u32` unit/group/trigger ids, `(u32, usize)` waypoints | unforgeable `GroupId`, `UnitId`, `VehicleId`, `WaypointRef`, `TriggerId` (no numeric constructor; from `add_*` or `Option` lookups) |
| positions, units | `mb_spec::Point` (plain data), `f64` seconds/metres/degrees | `Pos::new(x, z) -> Result<Pos, OutOfMap>`, `Seconds::from_minutes`, `Metres::from_km`, `Degrees` |
| plans | `add_waypoint(group, Waypoint)`; sequence rules checked by `validate()` | `Plan<Open/Mounted/Closed>`: `move_to` needs `AcceptsWaypoints`, `get_out` needs `IsMounted`, `hold`/`cycle` close; `AnyPlan::apply(Order)` for data-driven plans |
| triggers | `Trigger` struct with public fields, `Timer::new -> Result` | `TriggerBuilder<NeedsActivation/Ready, Once/Repeating/Ends>`; `ends_mission` needs `FiresOnce`, `repeating` needs `MayRepeat`; `Activation::detected_by -> Result`; `Timer::countdown -> Result` |
| validation/export | `validate(&self) -> Result<(), Vec<MissionError>>`; `export()` does not re-validate (documented) | `Mission<Draft>::validate(self) -> Result<Mission<Validated>, ValidationReport>`; edits need `Editable` (Draft), `export` needs `Exportable` (Validated); `into_draft()` to edit again |
| docs | idiomatic rustdoc with `# Errors` sections and a one-sentence workflow | doc comments written as instructions (what comes before/after, what to do with the Result) |

Every GUIDED sequence restriction is a method-level `where State: Trait` bound on a trait carrying
`#[diagnostic::on_unimplemented]` (the construction rule from the diag-probe), so rustc 1.98 reports
E0277 with a `fix:` note. Rendered diagnostics fed back to the model are normalised so they never
reveal the variant name (`mb_guided::X` -> `mb::X`, `crates/mb-guided/src/` -> `mb/src/`).

## Episode loop, records and prompt budget

Episode loop (live and mock): system prompt (role, rules sheet, generated API listing,
export-format appendix, `mb_spec` catalog and `Refusal`; byte-stable per variant for prompt
caching) + user prompt (task module, task text, entry signature, visible tests; identical across
variants) -> extract the first ```rust block -> static scan (rejects `std::process/fs/net/env`,
`unsafe`, `extern`, `include!`, `#[path]`, out-of-file `mod`, entry-point macros) -> write
`src/solution.rs` -> `cargo test --no-run --offline --locked --message-format json` -> run the
visible and hidden test binaries directly (single-threaded, 20 s wall limit, process-tree kill) ->
feed back compiler diagnostics (errors first, 6,000-character cap on a message boundary) or
visible-test failures -> repeat up to `--rounds` (default 3). Hidden-test results are never fed
back. The reference solution is restored after every episode.

Records (JSONL): one `run` header (config, toolchain, token counts, system-prompt hashes), one
`round` record per generation (tokens incl. llama-server `cache_n`, latency, format/bypass/compile
status, diagnostic codes, visible/hidden/trap results with failed test names and trap categories,
`accepted_but_wrong`, `failure_mode`, solution panics, context estimate), and one `episode` record
(R0..R3 outcomes with carry-forward, rounds used, token totals, generation vs cargo wall time,
escape-hatch counts, per-round diagnostic fix record).

Prompt budget: the GUIDED listing is longer (more types). With `--budget equal` (default) the
shorter variant's appendix is padded with seeded, valid example exports (neutral: a solution can
never write export text) until both system prompts have the same token count (server tokenizer
with `--server-tokens`, local estimate otherwise); the run aborts if the ratio is off by more than
`--budget-tolerance` (2%). `--budget natural` turns padding off for the ablation.

## Evidence (re-run from this folder on 2026-09-28; rustc 1.98.1, cargo 1.98.1, Python 3.12.4)

- `python -m unittest test_rwm`: 53 tests pass (27 from the pilot's harness, 26 added with the move),
  before and after scaffold.
- `python runner.py scaffold`: 34 tasks, 68 crates, lock regenerated offline, in 0.7 s; everything it
  writes is git-ignored.
- `python runner.py verify --tasks all`: 68/68 reference runs pass (34 tasks x 2 variants; visible
  and hidden tests, incl. every trap test).
- `cargo test --workspace --offline --locked`: 406 tests pass in 146 test binaries, 0 fail, no warnings.
- `python runner.py conformance --tasks all`: 202 test outputs, PLAIN and GUIDED byte-identical.
- `python runner.py mutants --tasks scored`: PLAIN static 0/13, loop 4/13, silent 9/13; GUIDED static
  8/13, silent 5/13; the 26 records are identical to the pilot's.
- `python runner.py listing` and `run --dry-run --tasks all --samples 6`: listings 3,007 (PLAIN) and
  6,680 (GUIDED) estimated tokens, system prompts 8,976 vs 8,974 (ratio 0.9998), 408 episodes
  planned; both listings, both system prompts and all 34 user prompts are byte-identical to the
  pilot's, so the move changed nothing a model sees.
- `power_sim.py 500`: output identical to the pilot's record (72 configurations).
- The analysis scripts, run from here on the pilot's records, reproduce the pilot's
  `pilot-summary.json`, `transition-rates.json`, `fix-rates.json` and `refusal-payload.json` exactly.
- `diag-probe/`: rustc 1.98.1 output for `guided.rs` and `methods.rs` is identical to the recorded
  `.err.txt` files; the E0618 probe shows no fix hint and "defined here" only for the local enum.
- `run --mock fail-first --tasks pilot`: 8 episodes fail to compile at R0 and are repaired at R1.

Trap coverage (scored tasks, from hidden-test names; 167 hidden tests, 97 trap tests): ACT-RULE,
ID-MIX, REF-SYNC 8 tasks each; SEQ-CYCLE 7; ERR-HANDLING 6; REF-VEHICLE, SEQ-MOUNT, UNIT-MEASURE 4;
BOUNDS, EMPTY-GROUP, SEQ-HOLD, TIMER-ORDER 3; SEQ-EXPORT 2. T01 and T03 have no trap (controls).

## What is committed, what is not

Committed: the five crates, the 34 task folders' hand-written files, prompts, `design.json`, the
runner and its package, the tests, the power simulation, the probes, the live driver and its arms
file, and the analysis scripts. Not committed (`.gitignore`): `target/`; `results/` (run records,
saved replies and code, logs, listings, dry-run prompts, conformance dumps, simulation output); the
68 generated task crates and `Cargo.lock`, which `scaffold` regenerates deterministically; and
`live/arms.local.json`. Left out of the move: the one-off script that resolved the Granite pin (the
pin is in `arms.json`), the pilot's status, check and log files, and the probes' build output.

Changes made when the harness moved here from a scratch folder, none of which changes a prompt, a
crate, a task or a measured value (see Evidence): the scaffold guard in `runner.py`; the live driver
reads `live/arms.json` and `--models-dir` instead of paths in code, and `start-server.ps1` takes the
server binary and log folder as parameters; the analysis scripts read saved code next to the results
file they are given, and `time_split.py` takes its files as arguments; `power_sim.py` writes under
`results/`; `rwm/hygiene.py` and 26 tests were added.

## Deviations from design.json (to fold into the pre-registration before freezing)

1. Numbers are `f64`, not `f32`; PLAIN positions are the plain-data `mb_spec::Point` (not tuples).
   Unit `skill` is dropped (no task used it).
2. A shared hidden core (`mb-core`) makes the variants functionally identical by construction. The
   design's 20+-scenario byte-identity suite is replaced by `runner.py conformance`, which compares
   both references' outputs on every visible and hidden test input (202 inputs).
3. The toolchain is not pinned with `rust-toolchain.toml` (a pin can trigger a rustup download,
   which the offline harness must never do); `rust-version = "1.98"` plus the per-run
   `rustc --version` record replace it.
4. The listing generator is Python (`rwm/listing.py`), not an `mb-listing` crate; it drops
   `#[diagnostic::on_unimplemented]` text (rustdoc does not show it either), so that text reaches the
   model only through compiler errors.
5. Equal prompt budget by neutral padding (requested for this build); the design's "both capped at
   7,000 tokens, lengths recorded" is kept as `--budget natural`.
6. Default context 24,576 instead of 16,384: the balanced system prompt is about 9k estimated tokens,
   so 16k leaves no room for a repair round plus a 3,072-token reply. Each round records
   `context_est_tokens` and `context_overflow`.
7. GUIDED `Pos::new` takes `f64` metres (not `Metres`) to limit friction; `Metres` and `Degrees` are
   used for areas and offsets.
8. Mutants cover 13 traps in 11 tasks, not one per trap test.
9. Not built yet: the frozen `analyze.py` (sign-flip test, bootstrap, TOST), the `prereg.lock.json`
   freeze, the cloud comparator backend, and independent idiomaticity and neutrality reviews.
   `runner.py summary` and `analysis/` are descriptive only.
10. Trap categories listed in `task.json` without a dedicated trap test: SEQ-EXPORT in T02 and T26
    (PLAIN's local checks already reject those inputs), ERR-HANDLING in T27, SEQ-CYCLE in T29.
11. The harness lives in the repository (`tools/rust-weak-models`), not in a scratch workspace;
    `design.json`'s `integrity.hygiene` and `workspace_layout.root` still describe the scratch
    location and are left as drafted.
