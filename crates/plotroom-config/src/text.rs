// SPDX-License-Identifier: GPL-3.0-or-later
//! Byte positions and lengths in a config text: [`TextOffset`], [`TextWidth`] and [`TextSpan`].
//!
//! **What it owns.** The three small types every other module uses to talk about "where in the file". They are
//! newtypes over `u32` (`AGENTS.md`, "Newtypes for domain identifiers"): an offset and a width are both byte counts,
//! and mixing them up (adding two offsets, or treating a width as a position) silently corrupts a patch.
//!
//! **Why `u32`.** The green tree stores widths, not offsets (`docs/architecture/core-document-model.md` §3.1), one per
//! node and token, so their size matters. [`crate::limits::MAX_CONFIG_TEXT_BYTES`] keeps every input far below
//! `u32::MAX`, and every sum goes through `checked_add`, so a width can never wrap even on crafted input.
//!
//! **Allocation profile.** None; all three types are `Copy`.

use std::fmt;

// ── TextOffset ───────────────────────────────────────────────────────────────────────────────────────────────────

/// A byte offset into the original config text, counted from the first byte (0).
///
/// Offsets are never stored in the tree: a cursor computes them on demand by summing the widths of earlier siblings,
/// which is what lets an edit rebuild only the path from the edited leaf to the root (core-document-model §3.1).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct TextOffset(u32);

impl TextOffset {
    /// Wraps a raw byte offset.
    #[inline]
    #[must_use]
    pub const fn from_raw(raw: u32) -> Self {
        Self(raw)
    }

    /// Returns the raw byte offset.
    #[inline]
    #[must_use]
    pub const fn to_raw(self) -> u32 {
        self.0
    }

    /// Moves the offset forward by `width` bytes, or returns `None` if the result would pass `u32::MAX`.
    ///
    /// Why checked: offsets are sums of widths taken from untrusted input; the size cap makes an overflow
    /// impossible on parsed input, but the check keeps that true for any caller (`AGENTS.md`, "Integer Overflow
    /// Safety").
    #[inline]
    #[must_use]
    pub const fn checked_add(self, width: TextWidth) -> Option<Self> {
        match self.0.checked_add(width.0) {
            Some(raw) => Some(Self(raw)),
            None => None,
        }
    }
}

impl fmt::Display for TextOffset {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "byte {}", self.0)
    }
}

// ── TextWidth ────────────────────────────────────────────────────────────────────────────────────────────────────

/// A length in bytes: the width of a token, a node or a patch's inserted text.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct TextWidth(u32);

impl TextWidth {
    /// Wraps a raw byte count.
    #[inline]
    #[must_use]
    pub const fn from_raw(raw: u32) -> Self {
        Self(raw)
    }

    /// Returns the raw byte count.
    #[inline]
    #[must_use]
    pub const fn to_raw(self) -> u32 {
        self.0
    }

    /// Adds two widths, or returns `None` if the sum would pass `u32::MAX`.
    #[inline]
    #[must_use]
    pub const fn checked_add(self, other: TextWidth) -> Option<Self> {
        match self.0.checked_add(other.0) {
            Some(raw) => Some(Self(raw)),
            None => None,
        }
    }

    /// The width of a byte slice of `len` bytes, or `None` if `len` does not fit in a `u32`.
    #[inline]
    #[must_use]
    pub fn of_len(len: usize) -> Option<Self> {
        u32::try_from(len).ok().map(Self)
    }
}

impl fmt::Display for TextWidth {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{} bytes", self.0)
    }
}

// ── TextSpan ─────────────────────────────────────────────────────────────────────────────────────────────────────

/// A half-open byte range `start..end` of the original text.
///
/// Invariant: `start <= end`. The fields are private and the only constructor, [`TextSpan::new`], refuses a reversed
/// range, so a span can always be sliced and its width computed without underflow.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct TextSpan {
    start: TextOffset,
    end: TextOffset,
}

impl TextSpan {
    /// Builds the span `start..end`, or returns `None` when `end` lies before `start`.
    #[inline]
    #[must_use]
    pub const fn new(start: TextOffset, end: TextOffset) -> Option<Self> {
        if start.0 <= end.0 {
            Some(Self { start, end })
        } else {
            None
        }
    }

    /// The empty span at `offset` (always valid).
    #[inline]
    #[must_use]
    pub const fn empty_at(offset: TextOffset) -> Self {
        Self {
            start: offset,
            end: offset,
        }
    }

    /// Builds the span that starts at `start` and is `width` bytes long, or `None` if its end passes `u32::MAX`.
    #[inline]
    #[must_use]
    pub const fn at(start: TextOffset, width: TextWidth) -> Option<Self> {
        match start.checked_add(width) {
            Some(end) => Some(Self { start, end }),
            None => None,
        }
    }

    /// The first byte of the span.
    #[inline]
    #[must_use]
    pub const fn start(self) -> TextOffset {
        self.start
    }

    /// The first byte after the span.
    #[inline]
    #[must_use]
    pub const fn end(self) -> TextOffset {
        self.end
    }

    /// The number of bytes in the span (never negative: `start <= end` is an invariant).
    #[inline]
    #[must_use]
    pub const fn width(self) -> TextWidth {
        TextWidth(self.end.0.saturating_sub(self.start.0))
    }

    /// The bytes of `input` the span covers, or `None` if the span reaches past the end of `input`.
    #[must_use]
    pub fn slice(self, input: &[u8]) -> Option<&[u8]> {
        let start = usize::try_from(self.start.0).ok()?;
        let end = usize::try_from(self.end.0).ok()?;
        input.get(start..end)
    }
}

impl fmt::Display for TextSpan {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "bytes {}..{}", self.start.0, self.end.0)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // ── Basic functionality ──────────────────────────────────────────────────────────────────────────────────────

    /// A span built from ordered offsets reports its ends, width and slice.
    ///
    /// Why: every patch and issue position is a span; its accessors are the base of all offset arithmetic.
    #[test]
    fn span_reports_ends_width_and_slice() {
        let span = TextSpan::new(TextOffset::from_raw(2), TextOffset::from_raw(5)).unwrap();
        assert_eq!(span.start().to_raw(), 2);
        assert_eq!(span.end().to_raw(), 5);
        assert_eq!(span.width().to_raw(), 3);
        assert_eq!(span.slice(b"abcdefg"), Some(&b"cde"[..]));
        assert_eq!(span.to_string(), "bytes 2..5");
        assert_eq!(TextOffset::from_raw(7).to_string(), "byte 7");
        assert_eq!(TextWidth::from_raw(3).to_string(), "3 bytes");
    }

    // ── Boundary tests ───────────────────────────────────────────────────────────────────────────────────────────

    /// A reversed span cannot be built; an empty one can.
    ///
    /// Why: `start <= end` is the invariant that makes `width` and `slice` panic-free.
    #[test]
    fn reversed_span_is_refused_and_empty_span_is_accepted() {
        assert!(TextSpan::new(TextOffset::from_raw(5), TextOffset::from_raw(4)).is_none());
        let empty = TextSpan::new(TextOffset::from_raw(4), TextOffset::from_raw(4)).unwrap();
        assert_eq!(empty.width().to_raw(), 0);
        assert_eq!(empty.slice(b"abcd"), Some(&b""[..]));
    }

    /// Slicing past the end of the input returns `None` instead of panicking.
    ///
    /// Why: spans can outlive the text they were computed on (a stale span after an edit).
    #[test]
    fn slice_past_the_end_is_none() {
        let span = TextSpan::new(TextOffset::from_raw(2), TextOffset::from_raw(9)).unwrap();
        assert_eq!(span.slice(b"abc"), None);
    }

    // ── Integer overflow safety ──────────────────────────────────────────────────────────────────────────────────

    /// Adding near `u32::MAX` returns `None` for offsets, widths and spans.
    ///
    /// Why: widths come from untrusted input; a wrapped offset would point a patch at the wrong bytes.
    #[test]
    fn additions_near_u32_max_are_checked() {
        let near = TextOffset::from_raw(u32::MAX - 1);
        assert_eq!(
            near.checked_add(TextWidth::from_raw(1)),
            Some(TextOffset::from_raw(u32::MAX))
        );
        assert_eq!(near.checked_add(TextWidth::from_raw(2)), None);
        assert_eq!(
            TextWidth::from_raw(u32::MAX).checked_add(TextWidth::from_raw(1)),
            None
        );
        assert!(TextSpan::at(near, TextWidth::from_raw(2)).is_none());
        assert_eq!(
            TextWidth::of_len(usize::try_from(u32::MAX).unwrap()),
            Some(TextWidth::from_raw(u32::MAX))
        );
    }
}
