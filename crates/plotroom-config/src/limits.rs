// SPDX-License-Identifier: GPL-3.0-or-later
//! Parser-safety caps for config text: the input size and the nesting depth.
//!
//! **What it owns.** [`Limits`] and the two default caps. Every other module takes a `Limits` value rather than
//! reading the constants, so the boundary tests can check both sides of a cap without allocating 64 MiB.
//!
//! **Why these caps exist.** Plotroom reads config files downloaded from the internet, so parsing must be bounded in
//! memory and in recursion whatever the input: the parser recurses once per class or array level, and a hostile file
//! must not be able to exhaust the editor's stack. The engine's own reader is not the model here.
//!
//! **Implementation placeholder.** Both values are this crate's own choice, not engine facts. They are revisited
//! when the opt-in corpus run (testing-strategy §5, `PLOTROOM_CORPUS_DIR`) reports the largest real file and the
//! deepest real nesting.

/// Default cap on the size of one config text, in bytes: 64 MiB.
///
/// Why this value: offsets and widths are `u32` (see [`crate::text`]), so any cap below 4 GiB keeps them exact; 64 MiB
/// matches the PBO header cap in doc 07 and is far above the largest known `mission.sqm` or `config.cpp` (a few MiB).
pub const MAX_CONFIG_TEXT_BYTES: u32 = 64 * 1024 * 1024;

/// Default cap on nesting depth, counting classes and array literals together: 64 levels.
///
/// Why this value: real `mission.sqm` files nest about 7 levels and configs about 8-10 [I]; 64 leaves ample room and
/// keeps the parser's recursion (one frame per level) and the tree's `Drop` far from any stack limit.
pub const MAX_NESTING_DEPTH: u32 = 64;

/// The caps one parse runs under.
///
/// `Limits::default()` is [`MAX_CONFIG_TEXT_BYTES`] and [`MAX_NESTING_DEPTH`]. A parsed tree remembers its limits, and
/// a patch must keep the text within them (so the patched text parses again under the same caps).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Limits {
    max_input_bytes: u32,
    max_depth: u32,
}

impl Limits {
    /// The default caps.
    pub const DEFAULT: Limits = Limits {
        max_input_bytes: MAX_CONFIG_TEXT_BYTES,
        max_depth: MAX_NESTING_DEPTH,
    };

    /// Caps of the caller's choice (tests use small values to check both sides of each boundary cheaply).
    #[must_use]
    pub const fn new(max_input_bytes: u32, max_depth: u32) -> Self {
        Self {
            max_input_bytes,
            max_depth,
        }
    }

    /// The largest accepted input, in bytes (inclusive).
    #[must_use]
    pub const fn max_input_bytes(self) -> u32 {
        self.max_input_bytes
    }

    /// The deepest accepted nesting of classes and array literals (inclusive).
    #[must_use]
    pub const fn max_depth(self) -> u32 {
        self.max_depth
    }
}

impl Default for Limits {
    fn default() -> Self {
        Self::DEFAULT
    }
}
