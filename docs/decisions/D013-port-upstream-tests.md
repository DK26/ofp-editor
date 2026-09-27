# D013: Port upstream tests with the code

> **Status:** accepted (invariant) · **Decided by:** owner (`AGENTS.md`) · **Decided:** 2026-09-26 · **Recorded:** 2026-09-27
> **Scope:** every change set that ports or re-implements upstream behaviour. **Related:** D001, D003, D017, D018.
> **Open parts:** DG018 (where records of ported permissive-licence code live).

## Context

The released engine source ships unit, integration, smoke, stress, performance and Rust test suites. They are the best available
specification of original behaviour. Doc 20 inventoried them: 636 rows covering 4,659 upstream test cases, of which 74 rows (up to 821
cases) are "port now" and 68 rows "port with the module". Many upstream assertions are tautological (`REQUIRE(true)`), and there are no
behavioural tests of the Arcade editor, `ArcadeTemplate` serialisation, trigger semantics or map drawing upstream. The in-game runner
works against CE builds; nothing runs on 1.99.

## Decision (summary; `AGENTS.md` "Porting Upstream Code and Tests" governs)

1. A change set that ports or re-implements upstream behaviour also ports the upstream tests covering it, **in the same change set**:
   same inputs and expected outputs, adapted to this repository's conventions, plus our own boundary, overflow and adversarial tests.
2. Each ported test's doc comment cites the upstream repository, commit, test file path and test case name.
3. Fixtures that are not clearly redistributable are rebuilt as synthetic equivalents; if that is impossible, the test is opt-in and
   local, gated by an environment variable.
4. Tests of behaviour observable only inside the running game become entries of the in-game **probe suite** run through Preview.
5. `docs/porting/upstream-test-map.csv` tracks every upstream test (`todo`, `ported`, `adapted`, `probe`, `reference`,
   `not-applicable`) and is updated in the same change set.

## Alternatives considered

- Write only our own tests: throws away the best specification of original behaviour.
- Port upstream tests verbatim, tautologies included: gives a weak suite that proves little (doc 20 TL;DR).

## Consequences

- **Port order** (doc 20 TL;DR): PBO with LZSS vectors, config text, preprocessor, rapified config and stringtables, evaluator goldens,
  mission-folder and mission-text semantics, PAA, FXY fonts, WRP.
- Tautological upstream assertions become **source-derived goldens tagged `unverified-1.99`**, confirmed later in batched 1.99 probes.
- Editor-core, mission-model and map-render tests are written from the ported source, using a synthetic mission corpus as round-trip
  goldens.
- A separate 1.99 probe backend is needed, since the 1.99 executable has no harness (doc 20 §4.4).
- Fixtures doc 20 lists as unsafe to copy (save files, photographic textures, unprovenanced assets, anything game-derived) are never
  copied.
- Ported tests carry the upstream licence obligations (D001); upstream fuzz harnesses are mirrored as `cargo-fuzz` targets (doc 07 §16).

## Sources

`AGENTS.md`; doc 20 (TL;DR, §4); `docs/porting/upstream-test-map.csv`; doc 07 §16.
