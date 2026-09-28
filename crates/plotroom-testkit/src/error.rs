// SPDX-License-Identifier: GPL-3.0-or-later
//! The one error type of `plotroom-testkit` (`AGENTS.md`, "Error Design").
//!
//! Test support fails loudly but never panics in library code: a test that misuses a builder gets a structured
//! error it can `unwrap()` (tests may) with a message that says what to do instead.

use std::fmt;

/// Everything that can go wrong inside the test kit.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Error {
    /// [`crate::BlobBuilder::patch_u32_le`] was asked to overwrite bytes that do not exist yet.
    PatchOutOfBounds {
        /// Offset of the first byte the patch would overwrite.
        at: usize,
        /// Number of bytes the patch writes (4 for a `u32`).
        width: usize,
        /// Length of the blob at the time of the call.
        len: usize,
    },
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            // Two next actions: a blob shorter than the patch has no valid offset at all.
            Self::PatchOutOfBounds { at, width, len } if len < width => write!(
                f,
                "patch of {width} bytes at offset {at} does not fit a blob of {len} bytes: write a {width}-byte \
                 placeholder first (for example .u32_le(0)), then patch it"
            ),
            Self::PatchOutOfBounds { at, width, len } => write!(
                f,
                "patch of {width} bytes at offset {at} does not fit a blob of {len} bytes: patch an offset of at \
                 most {}, or write a placeholder there first (for example .u32_le(0))",
                len.saturating_sub(*width)
            ),
        }
    }
}

impl std::error::Error for Error {}
