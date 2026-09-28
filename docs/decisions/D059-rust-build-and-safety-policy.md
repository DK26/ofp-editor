# D059: Rust build and safety policy

> **Status:** accepted · **Decided by:** owner (answers of 2026-09-28 to doc 68's open questions 1–4: OQ1 "On, whole workspace";
> OQ3 "cargo-deny + allowlists now"; OQ2 and OQ4 as items 3 and 4 state them; and the direction to fold the study into `AGENTS.md`:
> "when your Rust study is done, make sure AGENTS.md has updated instructions on how to code and use it") · **Decided:** 2026-09-28 ·
> **Recorded:** 2026-09-28
> **Scope:** how Plotroom's Rust code is written, built and checked: the release profile's overflow and panic settings, the
> supply-chain gate, the owner's build host, where the coding rules live, the toolchain pin and the warnings gate.
> **Related:** D001 (licence allowlist), D006, D007, D017 item 3 (caps on every count and size), D022 item 2, D032, D049, D058 item 2;
> docs 43 §3.2, 62, 64, 68. **Open parts:** doc 68's design-gap candidates 68-G1–68-G3, 68-G6, 68-G8–68-G13 (listed, not filed),
> among them the job-spawn wrapper and pool builder (68-G1, 68-G2) and the crate shape of an approved `unsafe` exception (68-G11);
> 68 OQ 5–7, 10, 12, 13 and 16–18.

## Context

- Doc 68 records where Rust's promises stop: panics and aborts on hostile input, silent wrap-around in release builds, build scripts
  and proc macros that run code at build time, unsafe emitted by a macro from any other crate (a sibling workspace crate included)
  that `forbid(unsafe_code)` accepts, no LTS toolchain, and lint and diagnostic changes on toolchain bumps. Its §4.4 proposes code
  rules for `AGENTS.md`, its §4.3 a configuration delta against the M0 skeleton, and its OQ1–OQ4 ask the owner four questions.
- D058 item 2 let doc 68 finish because its playbook updates `AGENTS.md`, which is already over its size budget (FR-C-010).
- The M0 workspace job was writing `Cargo.toml`, `deny.toml`, `clippy.toml` and CI when this record was written, so configuration
  changes are listed below as follow-ups, not applied.

## Decision

1. **Release overflow checks on, for the whole workspace (OQ1).** `[profile.release] overflow-checks = true` with no `package."*"`
   override, so our crates and every crate Cargo compiles (the prebuilt standard library keeps its own settings) panic on a wrap in
   shipped builds, as they already do in tests. It is a backstop: sizes and offsets from input still use checked arithmetic that
   returns structured errors, and a panic is contained only under a job boundary. `panic = "unwind"` is written out, since tests
   always unwind and `catch_unwind` boundaries need it.
2. **Supply chain: cargo-deny, allowlists and a person's review (OQ3).** cargo-deny keeps D001's licence allowlist and crates.io-only
   sources and gains `[bans.build] allow-build-scripts`, seeded from the current `Cargo.lock`; an `xtask` check keeps a proc-macro
   allowlist, which `allow-build-scripts` does not cover. Each list grows by one reviewed entry at a time and has a planted negative
   fixture. A person reviews every new dependency before merge; coding agents propose dependencies and never add them on their own
   initiative. cargo-vet is not adopted now; it is revisited before outside contributions are accepted, which the roadmap ties to the
   DCO check going live (D032). Unsafe emitted by a macro defined in any other crate, a dependency or one of our own workspace
   crates, is invisible to both lists and to `forbid`: no workspace crate defines a macro that emits `unsafe`, and a dependency's
   macros are part of its review.
3. **The owner's Windows 10 build host keeps Defender real-time scanning (OQ2):** no folder exclusions for `target/` or the Cargo
   home, and slower builds are accepted. Build speed comes from measured profile, linker and cache changes (doc 68's 68-P12, 68-P14
   items 1–2 and 68-P16), which stay proposals.
4. **The rules live in `AGENTS.md` as prose (OQ4),** merged into its existing sections, with lints and tests carrying whatever can be
   checked. No nested rule file under `crates/` (FR-C-010's removal option 2 is not taken).
5. **The `AGENTS.md` amendment of 2026-09-28** applies doc 68 §4.4 under the owner's direction, merged into existing sections (the
   file and its history carry the section changes). The arithmetic and cast rules are scoped so engine-faithful code stays valid:
   a bounded cursor may saturate, engine-defined wrap-around wraps, and float narrowing that mirrors the engine keeps `as`. Adopted
   with it beyond §4.4 and the owner's answers, as the study's proposals, which the owner may narrow:
   - **Jobs and concurrency:** the job's immutable snapshot and private draft, with a typed internal-error finding (68-P1, 68-G1);
     the global rayon pool's panic handler and no direct rayon spawn of any kind (68-P1); one owner per piece of state, state moving
     by message (68-P8); pools built in one place and parsing off the UI thread (68-P2; changes ui-shell §9–§10, 68-G2); the tokio
     runtime and its I/O confined to L7–L8 as crate-map §2.3 states.
   - **Toolchain:** one exact stable pinned in CI and equal to `rust-version` (MSRV = the pin); no root `rust-toolchain.toml` or
     `.cargo/config.toml` while `tools/rust-weak-models` sits below the root (FR-C-033); stable N adopted on its latest point release
     once N+1 ships; a security fix taken within a week by moving to the latest stable; each bump its own change set; final gates on
     the pin, trybuild re-blesses only for a bump or an intended guidance change.
   - **Warnings gate:** `-- -D warnings` stays in the gates and the inner loop. `CARGO_BUILD_WARNINGS=deny` (68-P13) waits until
     linker warnings are measured on all three CI legs (68 OQ 16), because it also fails on the linker warnings `-D warnings` ignores.

## Alternatives considered

| Option | Why not chosen |
| --- | --- |
| Release builds wrap; rely on checked arithmetic and lints alone (OQ1) | The owner chose checks on: a missed wrap in a size can corrupt a saved file without any sign |
| Overflow checks for our crates only (`[profile.release.package."*"] overflow-checks = false`) | The owner chose the whole workspace: under this variant a dependency's non-generic code still wraps silently in release |
| cargo-vet now (OQ3) | Its audit load per new crate; revisited before outside contributions are accepted |
| Defender exclusions, or Windows 11 for Dev Drive (OQ2) | The owner keeps real-time scanning on the build host |
| Rules as lints and tests only, or a nested rule file (OQ4) | The owner wants the instructions in `AGENTS.md`; several rules (job boundaries, determinism, dependency review) have no lint |
| A root `rust-toolchain.toml` or `.cargo/config.toml` | Either would reach `tools/rust-weak-models`; a toolchain file also starts a download when the pin is not installed (FR-C-033) |

## Consequences

- `docs/architecture/crate-map.md` §2.3–§2.5 and `testing-strategy.md` §14 state the settings and gates, marked "D059" where this
  record decides them, "D059 follow-up" where the setting or check is not in the workspace yet, and "proposal" where doc 68 only
  proposes them (lint sets beyond the cast lints, the advisories split, SHA-pinned actions, the publish-age cooldown,
  `cargo auditable`, the beta canary, profile tuning).
- Config follow-ups, applied after the M0 job lands, each in one change with the test that proves it and the `AGENTS.md` words that
  name its check: the release profile (item 1); `clippy.toml` bans on `std::process::exit`, `std::thread::spawn`,
  `std::thread::Scope::spawn`, rayon's `spawn`, `spawn_fifo` and `spawn_broadcast` (free and on `ThreadPool`) and `tokio::spawn`
  and `tokio::task::spawn`; `deny.toml [bans.build]` seeded from the lockfile of that day (12 crates with build scripts on
  2026-09-28) and the `xtask` proc-macro allowlist (`serde_derive`, `zerocopy-derive`), each with a planted fixture; an `xtask` scan
  that fails on an `unsafe` token in workspace sources outside an approved list; the cast lints in L1 crates, landing with
  `#[expect]`s on `plotroom-config`'s engine-faithful float narrowings; the `xtask` lint-set and pin-consistency checks; `rust-src`
  in CI's UI-test job. Until each lands, `AGENTS.md` states its rule without naming the check.
- Tests to write first (doc 68 §8): depth and allocation caps, a contained job panic, the planted allowlist and `unsafe`-scan
  fixtures, the pin check, and the secret type's trybuild cases and redacting-`Debug` test.
- Friction (D049). Introduced for contributors and coding agents: more crate-level lints, allowlist entries to justify, `cargo +<pin>`
  for final gates, a longer `AGENTS.md` (817 → 895 lines, 47.5 → 55.8 KB; FR-C-010 stays open), and slower builds on the owner's
  host. Removed: a hostile file, a model reply or a crashed job costs an error card instead of the editor (68-P1–P3); a silent
  release wrap becomes a visible failure; a toolchain bump or a new build script no longer arrives unreviewed; agents get scoped
  gates, exact UI-test commands and a rule for a missing pin.
- Folding steps not done here: doc 68's status line, OQ1–OQ4 answers and §1.4's "no `unsafe` token written in our own crates"
  (macros from sibling workspace crates escape it too); `docs/README.md`'s row for doc 68; `CODE-INDEX.md` §2–§3 (the toolchain
  policy and gate commands); ui-shell §9–§10 (open and import parsing on the worker pool; named, sized pools); filing 68-G1, 68-G2
  and 68-G11 as design-gap requests before the first crate that spawns jobs or pools or needs an `unsafe` exception; roadmap M0
  scope's "per-crate `disallowed-methods`" wording; FR-C-030's removal text ("Pin the toolchain with rust-toolchain.toml"), which
  item 5 replaces with the CI pin plus `rust-version`.

## Sources

Doc 68 (§1.3–§1.5, §3, §4.2–§4.5, §8, §9, open questions 1–4, findings for sibling docs, verification notes); the owner's answers
and direction of 2026-09-28 quoted above; D058; `docs/friction/register.csv` FR-C-010, FR-C-030, FR-C-033; the M0 skeleton's
`Cargo.toml`, `Cargo.lock`, `clippy.toml`, `deny.toml` and `.github/workflows/ci.yml` as of 2026-09-28.
