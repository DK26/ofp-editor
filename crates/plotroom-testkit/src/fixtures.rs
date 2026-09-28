// SPDX-License-Identifier: GPL-3.0-or-later
//! Fixture roots: where committed synthetic fixtures live, and the opt-in local roots for real data.
//!
//! **Why.** Doc 20 §3 ("shared prerequisites", item 1) asks for a fixture root resolved from `CARGO_MANIFEST_DIR`
//! and an opt-in game-data root read from an environment variable. It mirrors the upstream test support's fixture
//! lookup (upstream-test-map row `tests/unit/engine/.../Support/*`, status `reference`), redesigned for Cargo: each
//! crate keeps its synthetic fixtures in `tests/fixtures/`, and tests that need an installed game or a local mission
//! corpus run only when the developer names one (testing-strategy §15). CI never sets these variables.
//!
//! **Capability.** Reading environment variables is confined to binaries and test code (crate-map §2.3). This crate
//! is test code, so [`OptInRoot::read`] is the one function in the workspace's libraries allowed to read one; it
//! carries the matching `#[expect(clippy::disallowed_methods, ...)]`.

use std::ffi::OsString;
use std::path::{Path, PathBuf};

/// The fixture folder of the crate that invokes the macro: `<its manifest dir>/tests/fixtures`.
///
/// A macro, not a function, because `env!("CARGO_MANIFEST_DIR")` must be expanded in the calling crate, not in
/// this one. The folder need not exist; most fixtures are built in code by [`crate::BlobBuilder`].
///
/// ```
/// let root = plotroom_testkit::fixture_root!();
/// assert!(root.ends_with("tests/fixtures"));
/// ```
#[macro_export]
macro_rules! fixture_root {
    () => {
        $crate::fixture_root_of(::std::path::Path::new(env!("CARGO_MANIFEST_DIR")))
    };
}

/// `<manifest_dir>/tests/fixtures`, the conventional folder for a crate's committed synthetic fixtures.
///
/// Prefer [`fixture_root!`], which supplies the calling crate's manifest directory.
pub fn fixture_root_of(manifest_dir: &Path) -> PathBuf {
    manifest_dir.join("tests").join("fixtures")
}

/// An opt-in local data root for tests that need real, non-redistributable data (testing-strategy §15).
///
/// An enum rather than a variable name, so a test cannot misspell the variable and silently skip forever. Tests
/// gated on a root print only hashes and counts and never commit what they read.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum OptInRoot {
    /// An installed game, for install-discovery and catalog tests (`PLOTROOM_GAME_DIR`).
    GameDir,
    /// A local mission corpus, for round-trip runs (`PLOTROOM_CORPUS_DIR`).
    CorpusDir,
}

impl OptInRoot {
    /// Every opt-in root, for listing them in a skip message.
    pub const ALL: [Self; 2] = [Self::GameDir, Self::CorpusDir];

    /// The environment variable that names this root.
    pub const fn var_name(self) -> &'static str {
        match self {
            Self::GameDir => "PLOTROOM_GAME_DIR",
            Self::CorpusDir => "PLOTROOM_CORPUS_DIR",
        }
    }

    /// Interprets a raw variable value: unset or empty means "not opted in".
    ///
    /// Split from [`OptInRoot::read`] so the rule is testable without touching the process environment (setting
    /// variables is `unsafe` in Rust 2024 and forbidden here).
    pub fn from_value(value: Option<OsString>) -> Option<PathBuf> {
        value.filter(|v| !v.is_empty()).map(PathBuf::from)
    }

    /// Reads this root from the environment; `None` means the test should skip and say which variable to set.
    #[must_use = "a test gated on an opt-in root must skip when this is None; match on it and print the variable name"]
    #[expect(
        clippy::disallowed_methods,
        reason = "crate-map §2.3 allows environment variables in test code; this crate is the tests' one reader"
    )]
    pub fn read(self) -> Option<PathBuf> {
        Self::from_value(std::env::var_os(self.var_name()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // ── Basic functionality ─────────────────────────────────────────────────────────────────────────────────────

    /// The macro resolves to this crate's `tests/fixtures` folder.
    #[test]
    fn fixture_root_is_under_the_calling_manifest() {
        let root = crate::fixture_root!();
        assert_eq!(
            root,
            Path::new(env!("CARGO_MANIFEST_DIR"))
                .join("tests")
                .join("fixtures")
        );
        assert_eq!(
            fixture_root_of(Path::new("crate")),
            Path::new("crate").join("tests").join("fixtures")
        );
    }

    /// The variable names are the ones testing-strategy §15 documents.
    ///
    /// Developers set these by name; a silent rename would turn every opt-in test into a permanent skip.
    #[test]
    fn variable_names_match_the_testing_strategy() {
        assert_eq!(OptInRoot::GameDir.var_name(), "PLOTROOM_GAME_DIR");
        assert_eq!(OptInRoot::CorpusDir.var_name(), "PLOTROOM_CORPUS_DIR");
        assert_eq!(OptInRoot::ALL.len(), 2);
    }

    /// A set, non-empty value opts in with that path.
    #[test]
    fn set_value_opts_in() {
        assert_eq!(
            OptInRoot::from_value(Some(OsString::from("/data/game"))),
            Some(PathBuf::from("/data/game"))
        );
    }

    // ── Boundary tests ──────────────────────────────────────────────────────────────────────────────────────────

    /// Unset and empty both mean "not opted in", so `PLOTROOM_GAME_DIR=` in a shell cannot point tests at the
    /// current directory.
    #[test]
    fn unset_or_empty_is_not_opted_in() {
        assert_eq!(OptInRoot::from_value(None), None);
        assert_eq!(OptInRoot::from_value(Some(OsString::new())), None);
    }

    /// Reading the real environment never panics; in CI the variables are unset.
    #[test]
    fn read_does_not_panic() {
        for root in OptInRoot::ALL {
            let _maybe: Option<PathBuf> = root.read();
        }
    }
}
