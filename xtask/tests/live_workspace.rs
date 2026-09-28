// SPDX-License-Identifier: GPL-3.0-or-later
//! Both checks on the real workspace, so `cargo test --workspace` enforces them without a `cargo run`.
//!
//! These tests run `cargo metadata --no-deps` (offline, no build) and walk the crate folders; they are the same
//! calls CI's `xtask` job makes, and the fastest feedback when a change adds a crate, an edge or a name.

use xtask::cli::{Outcome, run_hygiene, run_layers, workspace_root};

/// The first number in a summary line such as `layers: 2 workspace crates checked ...: clean`.
fn first_number(summary: &str) -> Option<usize> {
    summary
        .split_whitespace()
        .find_map(|word| word.parse().ok())
}

// ── Basic functionality ─────────────────────────────────────────────────────────────────────────────────────────

/// The workspace follows the committed layer table: every member is declared and every edge is allowed.
///
/// Fails with the violation list when a change adds an undeclared crate or a disallowed dependency. The member
/// count guards against a silent pass on an empty reading of `cargo metadata` (the workspace has at least xtask
/// and plotroom-testkit).
#[test]
fn the_workspace_passes_the_layer_check() {
    match run_layers(&workspace_root().unwrap()).unwrap() {
        Outcome::Clean { summary } => assert!(first_number(&summary).unwrap() >= 2, "{summary}"),
        findings @ Outcome::Findings { .. } => panic!("{findings:#?}"),
    }
}

/// No crate, target, module, file or folder name in the workspace carries a third-party mark or island name.
///
/// The name count guards against a silent pass on an empty walk.
#[test]
fn the_workspace_passes_the_naming_check() {
    match run_hygiene(&workspace_root().unwrap()).unwrap() {
        Outcome::Clean { summary } => assert!(first_number(&summary).unwrap() >= 20, "{summary}"),
        findings @ Outcome::Findings { .. } => panic!("{findings:#?}"),
    }
}
