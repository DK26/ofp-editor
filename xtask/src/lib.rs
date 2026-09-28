// SPDX-License-Identifier: GPL-3.0-or-later
//! Repository checks for the Plotroom workspace. Tooling: never shipped, never a dependency of a product crate.
//!
//! **What it owns** (docs/architecture/crate-map.md §2.5, §12, §15; testing-strategy §14):
//!
//! - [`layers`]: the declared layer table (`xtask/layers.toml`: crate → layer, allowed same-layer edges, forbidden
//!   edges, confined third-party crates) checked against `cargo metadata`;
//! - [`hygiene`]: refuses third-party marks and the game's island names in crate, target, module, file and folder
//!   names (`AGENTS.md`, "Naming and Trademarks"), from the one mark list [`hygiene::MARKS`].
//!
//! Later milestones add `codes`, `catalog`, `skills`, `provenance` and `defs` (crate-map §12).
//!
//! **How it is built.** Pure checks over parsed data ([`metadata`], [`layers`], [`hygiene`]) are unit-tested on
//! fixture JSON; the only side effects (running `cargo metadata`, listing folders, reading `.rs` files) live in
//! [`sys`], the one module that silences the workspace's capability lints. [`cli`] wires them into the two
//! commands; `src/main.rs` only maps the outcome to an exit code.
//!
//! **Running it.** `cargo run -p xtask -- layers` and `cargo run -p xtask -- hygiene` (CI's `xtask` job). There is
//! no `cargo xtask` alias: it would need a root `.cargo/config.toml`, which would also reach the standalone research
//! workspace under `tools/` (CODE-INDEX.md §3). `cargo test -p xtask` runs both checks on the real workspace too
//! (`tests/live_workspace.rs`), so the fast inner loop needs no `cargo run`.

pub mod cli;
pub mod error;
pub mod hygiene;
pub mod layers;
pub mod metadata;
pub mod sys;

pub use error::Error;

/// Makes a name from the layer table, `cargo metadata` or the file system safe to print in one log line.
///
/// Every character outside printable ASCII (controls, bidi overrides, zero-width and tag characters, and any other
/// non-ASCII character) is shown as `\u{…}`, and a backslash as `\\`, so a hidden character can neither hide a
/// mark from a reviewer nor reorder the text around it. A placeholder for the workspace's shared display sanitizer
/// (`plotroom-encoding`, M1; `AGENTS.md` "Error Design"), which replaces it once that crate lands.
///
/// ```
/// assert_eq!(xtask::display_name("o\u{200B}fp"), "o\\u{200b}fp");
/// assert_eq!(xtask::display_name("plotroom-io"), "plotroom-io");
/// ```
pub fn display_name(raw: &str) -> String {
    let mut shown = String::with_capacity(raw.len());
    for c in raw.chars() {
        match c {
            '\\' => shown.push_str("\\\\"),
            ' ' => shown.push(' '),
            c if c.is_ascii_graphic() => shown.push(c),
            // `escape_unicode` writes `\u{…}` with lowercase hex digits and no leading zeros.
            c => shown.extend(c.escape_unicode()),
        }
    }
    shown
}

#[cfg(test)]
mod tests {
    use super::display_name;

    // ── Basic functionality ─────────────────────────────────────────────────────────────────────────────────────

    /// Plain ASCII names print unchanged.
    #[test]
    fn ascii_names_are_unchanged() {
        assert_eq!(
            display_name("plotroom-testkit src/lib.rs"),
            "plotroom-testkit src/lib.rs"
        );
    }

    // ── Security edge-case tests ────────────────────────────────────────────────────────────────────────────────

    /// Zero-width, bidi-override, tag and control characters become visible escapes.
    ///
    /// A zero-width space inside a mark would otherwise print as the mark itself while evading a naive reviewer;
    /// a right-to-left override would reorder the rest of the log line.
    #[test]
    fn hidden_characters_become_visible() {
        assert_eq!(display_name("o\u{200B}fp"), "o\\u{200b}fp");
        assert_eq!(display_name("a\u{202E}b"), "a\\u{202e}b");
        assert_eq!(display_name("x\u{E0041}"), "x\\u{e0041}");
        assert_eq!(display_name("line\nbreak\t"), "line\\u{a}break\\u{9}");
        assert_eq!(display_name("caf\u{E9}"), "caf\\u{e9}");
    }

    /// A literal backslash is doubled, so it cannot impersonate an escape.
    #[test]
    fn backslash_is_escaped() {
        assert_eq!(display_name("a\\u{200b}"), "a\\\\u{200b}");
    }
}
