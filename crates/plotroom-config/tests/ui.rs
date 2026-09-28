// SPDX-License-Identifier: GPL-3.0-or-later
//! Negative compile tests for the witness and guard types (`AGENTS.md`, "Negative Compile Tests").
//!
//! Each `tests/ui/*.rs` case is a misuse that must not compile: building a lexeme, a value reference or a span
//! without its checked constructor, crossing the entry and element contexts, keeping a reference past its tree, or
//! discarding a patch or its check. The expected compiler output is committed next to each case as a `.stderr`
//! snapshot, so a change that weakens a guard, or changes its guidance text, fails here.
//!
//! **How trybuild works.** `TestCases::compile_fail` builds every case as a separate small crate that depends on
//! this one and compares the compiler's error output with the snapshot. Compiler messages change between releases,
//! so this target needs the `ui-tests` feature and runs in one CI job on the pinned toolchain
//! (`.github/workflows/ci.yml`, job `ui`). To refresh snapshots after a toolchain bump or a reviewed guidance change,
//! run `TRYBUILD=overwrite cargo test -p plotroom-config --features ui-tests --test ui` and review the diff.

/// Every case in `tests/ui/` fails to compile with exactly its committed compiler output.
///
/// Why: each case is a way around a guard (a witness built without its check, a reference kept past its tree, a
/// discarded proof); if one starts compiling, or its guidance text changes, the guard or its message changed.
#[test]
fn misuse_of_guard_types_does_not_compile() {
    let cases = trybuild::TestCases::new();
    cases.compile_fail("tests/ui/*.rs");
}
