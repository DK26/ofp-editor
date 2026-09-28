// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: Bohemia Interactive a.s. (original C++)
// SPDX-FileCopyrightText: 2026 Plotroom contributors (Rust translation)
// Derived-From: BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/IO/Streams/QStream.hpp
// Modified: translated to Rust and changed, 2026-09-28. Subject to the Additional Terms
// (GPLv3 section 7) from Bohemia Interactive reproduced in NOTICE.
//! The byte stream the parser reads: the input with the preprocessor's removed ranges skipped.
//!
//! **What it owns.** [`Stream`], a port of the game's `QIStream` reading interface (`get`, `unget`, end-of-input)
//! over the *preprocessed view* of the input. `get` jumps over removed ranges transparently, so the parser sees the
//! same byte sequence the game's parser sees, while every byte it returns still has its offset in the original text.
//!
//! **Engine semantics kept** (`CWR:engine/Poseidon/IO/Streams/QStream.hpp#L89-L112`): `get` returns bytes as
//! unsigned values and reports the end of input without moving; `unget` after an end-of-input `get` does nothing
//! (the CWR hardening that stops parser loops from re-reading the last byte forever). The engine never ungets twice
//! in a row on this path; a second `unget` here is a no-op.
//!
//! **Allocation profile.** None; the stream borrows the input and the removed ranges.
//!
//! **Arithmetic.** Positions step with `saturating_add` as a cursor within the input, whose length has already passed
//! the size cap (`Limits::max_input_bytes`, never above `u32::MAX`), so the saturation cannot trigger.

use crate::cst::preproc::Removed;

/// The preprocessed view of the input, read one byte at a time (see the module docs).
pub(crate) struct Stream<'input> {
    input: &'input [u8],
    removed: &'input [Removed],
    /// Offset of the next byte to consider (it may be the start of a removed range).
    pos: usize,
    /// Index of the first removed range that starts at or after `pos`.
    next_removed: usize,
    /// Offset and range index of the byte the last successful `get` returned, for `unget`.
    last: Option<(usize, usize)>,
    /// True after a `get` that reported the end of input (as `QIStream::_eof`).
    at_end: bool,
}

impl<'input> Stream<'input> {
    /// A stream at the start of `input`.
    pub(crate) fn new(input: &'input [u8], removed: &'input [Removed]) -> Self {
        Self {
            input,
            removed,
            pos: 0,
            next_removed: 0,
            last: None,
            at_end: false,
        }
    }

    /// Reads the next visible byte, or `None` at the end of input (the engine's `EOF`).
    pub(crate) fn get(&mut self) -> Option<u8> {
        // Jump over every removed range that starts where we are (ranges are sorted and do not overlap).
        while let Some(range) = self.removed.get(self.next_removed) {
            let start = to_index(range.start);
            if start > self.pos {
                break;
            }
            if start == self.pos {
                self.pos = to_index(range.end);
            }
            self.next_removed = self.next_removed.saturating_add(1);
        }
        match self.input.get(self.pos) {
            Some(&byte) => {
                self.last = Some((self.pos, self.next_removed));
                self.pos = self.pos.saturating_add(1);
                self.at_end = false;
                Some(byte)
            }
            None => {
                self.at_end = true;
                None
            }
        }
    }

    /// Puts the last byte back, unless the last `get` reported the end of input.
    pub(crate) fn unget(&mut self) {
        if self.at_end {
            return;
        }
        if let Some((pos, next_removed)) = self.last.take() {
            self.pos = pos;
            self.next_removed = next_removed;
        }
    }

    /// Offset of the byte the last successful `get` returned (or the current position if there was none).
    pub(crate) fn last_offset(&self) -> u32 {
        to_u32(self.last.map_or(self.pos, |(pos, _)| pos))
    }

    /// The current position: the offset of the next byte `get` would consider.
    pub(crate) fn offset(&self) -> u32 {
        to_u32(self.pos)
    }

    /// The input length as an offset.
    pub(crate) fn len(&self) -> u32 {
        to_u32(self.input.len())
    }
}

/// `u32` offset to index.
#[inline]
fn to_index(offset: u32) -> usize {
    usize::try_from(offset).unwrap_or(usize::MAX)
}

/// Index to `u32` offset; the size cap keeps it exact.
#[inline]
fn to_u32(index: usize) -> u32 {
    u32::try_from(index).unwrap_or(u32::MAX)
}
