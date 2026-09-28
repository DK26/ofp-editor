// SPDX-License-Identifier: GPL-3.0-or-later
//! `xtask layers`: the declared layer table checked against `cargo metadata` (crate-map §2.1-§2.5).
//!
//! **What.** [`LayerTable`] is the parsed and validated `xtask/layers.toml` (compiled in as [`BUILTIN_TABLE`]);
//! [`check`] compares it with the workspace's declared dependencies and returns every [`Violation`]:
//!
//! - a workspace member the table does not list;
//! - an edge that points upward, or sideways without a `[same-layer]` entry (crate-map §2.2);
//! - a `[[forbidden]]` edge (an L6 crate, `plotroom-plugin-host` or `plotroom-mcp` depending on `plotroom-session`);
//! - a layered crate taking a dev crate outside `[dev-dependencies]`, or anything depending on tooling;
//! - a direct dependency on a `[[confined]]` third-party crate (egui below the shell, HTTP clients, WebAssembly
//!   runtimes, rmcp, wgpu) from a crate the table does not allow.
//!
//! **Why a table and not Cargo alone.** Cargo only forbids cycles. The layer order is what keeps the core headless,
//! the harness free of I/O and consent unforgeable (crate-map §2.1, §2.3), so it is checked mechanically, and a
//! new edge becomes a reviewed change to the table instead of an incidental `Cargo.toml` edit (crate-map §2.2).
//!
//! **Where it runs.** CI's `xtask` job (`cargo run -p xtask -- layers`) and `tests/live_workspace.rs` on the real
//! workspace; the committed negative tests in `tests.rs` plant bad edges (M0 exit evidence item 2).

mod check;
mod table;

#[cfg(test)]
mod tests;
#[cfg(test)]
mod tests_table;

pub use check::{Violation, check};
pub use table::{BUILTIN_TABLE, Confined, ForbiddenEdge, Layer, LayerTable, Role};
