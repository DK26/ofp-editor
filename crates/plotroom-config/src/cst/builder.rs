// SPDX-License-Identifier: GPL-3.0-or-later
//! Builds the green tree while the parser reads, guaranteeing that every input byte lands in exactly one token.
//!
//! **What it owns.** [`Builder`]: a stack of open nodes plus an "emitted up to" offset. The parser only reports
//! the syntax it recognised (`token(kind, start, end)`) and the nodes around it; the builder fills every gap between
//! two reported tokens with trivia tokens, and splits a reported token wherever the preprocessor removed bytes inside
//! it (a comment inside a value, a CR inside a string). That is what makes `render(parse(b)) == b` hold by
//! construction, even when the parser reports nothing for part of the input.
//!
//! **Robustness.** Reports that would go backwards (a start before the emitted offset) are clamped rather than
//! trusted, so a parser mistake can at worst misclassify bytes, never lose or duplicate them. The final
//! [`Builder::finish`] flushes whatever is left as trivia.
//!
//! **Allocation profile.** One `Vec<GreenChild>` per open node, then the tree itself (see [`crate::cst::green`]).
//!
//! **Arithmetic.** Offsets step with `saturating_add` as a cursor within the input, whose length passed the size cap
//! (`Limits::max_input_bytes`) before parsing started; node widths are summed with `checked_add` in
//! [`GreenNode::new`], and an overflow there becomes [`Error::InputTooLarge`].

use crate::cst::green::{GreenChild, GreenNode, GreenToken};
use crate::cst::kinds::{NodeKind, TokenKind};
use crate::cst::preproc::Removed;
use crate::error::Error;

/// One open node: its kind and the children collected so far.
struct Frame {
    kind: NodeKind,
    children: Vec<GreenChild>,
}

/// The tree builder (see the module docs).
pub(crate) struct Builder<'input> {
    input: &'input [u8],
    removed: &'input [Removed],
    /// Index of the first removed range not yet emitted.
    next_removed: usize,
    /// Every byte before this offset is already in the tree.
    emitted: u32,
    /// Open nodes; the bottom frame is the file and is closed only by [`Builder::finish`].
    stack: Vec<Frame>,
}

impl<'input> Builder<'input> {
    /// A builder for `input`, with the preprocessor's removed ranges for it.
    pub(crate) fn new(input: &'input [u8], removed: &'input [Removed]) -> Self {
        Self {
            input,
            removed,
            next_removed: 0,
            emitted: 0,
            stack: vec![Frame {
                kind: NodeKind::File,
                children: Vec::new(),
            }],
        }
    }

    /// The overflow error: only reachable if a width sum passes `u32::MAX`, which the size cap rules out.
    fn overflow(&self) -> Error {
        Error::InputTooLarge {
            len: u64::try_from(self.input.len()).unwrap_or(u64::MAX),
            cap: u32::MAX,
        }
    }

    /// Opens a node; tokens reported from now on go into it until [`Builder::finish_node`].
    pub(crate) fn start_node(&mut self, kind: NodeKind) {
        self.stack.push(Frame {
            kind,
            children: Vec::new(),
        });
    }

    /// Closes the innermost open node and adds it to its parent. The file frame is never closed here.
    pub(crate) fn finish_node(&mut self) -> Result<(), Error> {
        if self.stack.len() <= 1 {
            return Ok(());
        }
        let Some(frame) = self.stack.pop() else {
            return Ok(());
        };
        let node = GreenNode::new(frame.kind, frame.children).ok_or_else(|| self.overflow())?;
        self.push_child(GreenChild::Node(node));
        Ok(())
    }

    /// Adds a child to the innermost open node.
    fn push_child(&mut self, child: GreenChild) {
        if let Some(frame) = self.stack.last_mut() {
            frame.children.push(child);
        }
    }

    /// Adds a token for `input[start..end]` to the innermost open node.
    fn push_token(&mut self, kind: TokenKind, start: u32, end: u32) -> Result<(), Error> {
        let bytes = self
            .input
            .get(to_index(start)..to_index(end))
            .unwrap_or(&[]);
        let token = GreenToken::new(kind, bytes).ok_or_else(|| self.overflow())?;
        self.push_child(GreenChild::Token(token));
        Ok(())
    }

    /// Adds a zero-width marker token (a [`TokenKind::Stop`]).
    pub(crate) fn marker(&mut self, kind: TokenKind) -> Result<(), Error> {
        let token = GreenToken::new(kind, &[]).ok_or_else(|| self.overflow())?;
        self.push_child(GreenChild::Token(token));
        Ok(())
    }

    /// Reports a token of `kind` covering `start..end`. Bytes between the last emitted offset and `start` become
    /// trivia first; removed ranges inside `start..end` become their own trivia tokens, splitting the token.
    ///
    /// A [`TokenKind::Newline`] token absorbs a CR removed just before it, so CR LF stays one line-break token.
    pub(crate) fn token(&mut self, kind: TokenKind, start: u32, end: u32) -> Result<(), Error> {
        let start = start.max(self.emitted);
        if kind == TokenKind::Newline && start > self.emitted {
            // Flush the gap up to the byte before the LF, then check whether that byte is a removed CR.
            let before = start.saturating_sub(1);
            self.trivia_to(before)?;
            if self.emitted == before && self.pending_cr_at(before) {
                self.next_removed = self.next_removed.saturating_add(1);
                let lf_end = start.saturating_add(1);
                self.push_token(kind, before, lf_end)?;
                self.emitted = lf_end;
                return if end > lf_end {
                    self.emit_range(kind, lf_end, end)
                } else {
                    Ok(())
                };
            }
        }
        self.trivia_to(start)?;
        self.emit_range(kind, start, end.max(start))
    }

    /// True when the next removed range not yet emitted is a single CR at `offset`.
    fn pending_cr_at(&self, offset: u32) -> bool {
        self.removed.get(self.next_removed).is_some_and(|r| {
            r.kind == TokenKind::CarriageReturn
                && r.start == offset
                && r.end == offset.saturating_add(1)
        })
    }

    /// Emits `start..end` as `kind`, split at removed ranges (which become trivia tokens).
    fn emit_range(&mut self, kind: TokenKind, start: u32, end: u32) -> Result<(), Error> {
        let mut pos = start;
        while pos < end {
            match self.removed.get(self.next_removed).copied() {
                Some(r) if r.start <= pos => {
                    self.next_removed = self.next_removed.saturating_add(1);
                    if r.end > pos {
                        self.push_token(r.kind, pos, r.end)?;
                        pos = r.end;
                    }
                }
                next => {
                    let stop = next.map_or(end, |r| r.start.min(end));
                    self.push_token(kind, pos, stop)?;
                    pos = stop;
                }
            }
        }
        self.emitted = self.emitted.max(pos);
        Ok(())
    }

    /// Emits everything from the last emitted offset up to `end` as trivia tokens into the innermost open node.
    ///
    /// Visible bytes are classified by value: runs of space, tab, VT and FF are [`TokenKind::Whitespace`], LF is a
    /// [`TokenKind::Newline`] (merged with a CR removed just before it), and anything else, which the parser should
    /// have reported, is kept as [`TokenKind::Unexpected`] so that no byte is ever lost.
    pub(crate) fn trivia_to(&mut self, end: u32) -> Result<(), Error> {
        let end = end.min(to_u32(self.input.len()));
        while self.emitted < end {
            let pos = self.emitted;
            match self.removed.get(self.next_removed).copied() {
                Some(r) if r.start <= pos => {
                    self.next_removed = self.next_removed.saturating_add(1);
                    if r.end <= pos {
                        continue;
                    }
                    // CR removed right before a visible LF inside this gap: one line-break token.
                    let lf = r.end;
                    let is_crlf = r.kind == TokenKind::CarriageReturn
                        && lf < end
                        && self.byte(lf) == Some(b'\n')
                        && !self.removed_starts_at(lf);
                    if is_crlf {
                        self.push_token(TokenKind::Newline, pos, lf.saturating_add(1))?;
                        self.emitted = lf.saturating_add(1);
                    } else {
                        self.push_token(r.kind, pos, r.end)?;
                        self.emitted = r.end;
                    }
                }
                next => {
                    let limit = next.map_or(end, |r| r.start.min(end));
                    let run_end = self.visible_run_end(pos, limit);
                    let kind = match self.byte(pos) {
                        Some(b'\n') => TokenKind::Newline,
                        Some(b' ' | b'\t' | 0x0B | 0x0C) => TokenKind::Whitespace,
                        _ => TokenKind::Unexpected,
                    };
                    self.push_token(kind, pos, run_end)?;
                    self.emitted = run_end;
                }
            }
        }
        Ok(())
    }

    /// The end of the run of same-class visible bytes starting at `pos` (stopping at `limit`). Line breaks are one
    /// byte each; whitespace and "other" bytes form runs.
    fn visible_run_end(&self, pos: u32, limit: u32) -> u32 {
        let class = |b: Option<u8>| match b {
            Some(b'\n') => 0u8,
            Some(b' ' | b'\t' | 0x0B | 0x0C) => 1,
            _ => 2,
        };
        let first = class(self.byte(pos));
        let mut end = pos.saturating_add(1);
        if first == 0 {
            return end.min(limit);
        }
        while end < limit && class(self.byte(end)) == first {
            end = end.saturating_add(1);
        }
        end.min(limit)
    }

    /// True when a removed range starts exactly at `offset`.
    fn removed_starts_at(&self, offset: u32) -> bool {
        self.removed
            .get(self.next_removed)
            .is_some_and(|r| r.start == offset)
    }

    /// The input byte at `offset`, if any.
    fn byte(&self, offset: u32) -> Option<u8> {
        self.input.get(to_index(offset)).copied()
    }

    /// Flushes the rest of the input as trivia, closes any node left open and returns the file node.
    pub(crate) fn finish(mut self) -> Result<GreenNode, Error> {
        self.trivia_to(to_u32(self.input.len()))?;
        while self.stack.len() > 1 {
            self.finish_node()?;
        }
        let frame = self.stack.pop().unwrap_or(Frame {
            kind: NodeKind::File,
            children: Vec::new(),
        });
        GreenNode::new(frame.kind, frame.children).ok_or_else(|| self.overflow())
    }
}

/// `u32` offset to slice index (always exact on the 32- and 64-bit targets this crate supports).
#[inline]
fn to_index(offset: u32) -> usize {
    usize::try_from(offset).unwrap_or(usize::MAX)
}

/// Slice length to `u32` offset; the size cap keeps it exact.
#[inline]
fn to_u32(len: usize) -> u32 {
    u32::try_from(len).unwrap_or(u32::MAX)
}
