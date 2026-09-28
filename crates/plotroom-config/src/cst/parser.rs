// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: Bohemia Interactive a.s. (original C++)
// SPDX-FileCopyrightText: 2026 Plotroom contributors (Rust translation)
// Derived-From: BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/IO/ParamFile/ParamFile.cpp
// Derived-From: BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/IO/ParamFile/ParamFilePrivate.inc
// Derived-From: BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/IO/ParamFile/ParamFileParse.cpp
// Modified: translated to Rust and changed, 2026-09-28. Subject to the Additional Terms
// (GPLv3 section 7) from Bohemia Interactive reproduced in NOTICE.
//! The statement parser: a port of the game's config text reader that builds a lossless tree instead of entries.
//!
//! **What it owns.** [`parse_green`]. It reads the preprocessed view ([`crate::cst::stream`]) with the same
//! decisions, in the same order, as the engine's `ParamClass::Parse` (`ParamFile.cpp#L1571-L1872`),
//! `ParamRawArray::Parse` (`ParamFileParse.cpp#L432-L529`), `GetWord` and `GetAlphaWord`
//! (`ParamFilePrivate.inc#L12-L127`), and reports what it recognised to the [`Builder`], which keeps every byte.
//!
//! **Why a port and not a grammar.** The tree must say which statements the game keeps and where it stops. The
//! engine's reader has quirks no clean grammar reproduces: a value may continue on the next line after `=`, a quoted
//! value followed by a space before `;` is dropped, an error returns from the current class only and the parent
//! reads on from the same position (so later entries land in the parent), an enum item with a value ends the enum.
//! Porting the reading logic keeps all of these by construction.
//!
//! **Where it differs.** (1) Nothing is truncated: the engine cuts values at 2047 bytes and names at 2048
//! (`ParamFilePrivate.inc#L10`); the tree keeps every byte and `lint_syntax` reports the cut. (2) Base classes are
//! assumed to resolve: the engine stops the enclosing class when `class D : B` names an undefined base
//! (`ParamFile.cpp#L1613-L1629`), which needs the resolved view (later). (3) `enum` values and `__EXEC` text are not
//! evaluated, and `__EVAL`/`(...)` values are kept as text. (4) Nesting deeper than the cap is an error (a cap of
//! this crate's own, [`crate::Limits`]).
//!
//! **Arithmetic.** Token offsets (`at.saturating_add(1)`) are cursor steps within the input, whose length passed the
//! size cap (`Limits::max_input_bytes`) before parsing starts; the depth counter is checked against
//! `Limits::max_depth` before every level. Neither saturation can trigger.
//!
//! **Allocation profile.** Names read by `alpha_word` are copied into a small `Vec` to compare them with the
//! keywords; everything else is offsets. The tree itself is described in [`crate::cst::green`].

use crate::cst::builder::Builder;
use crate::cst::green::GreenNode;
use crate::cst::kinds::{NodeKind, StopReason, TokenKind};
use crate::cst::preproc::removed_spans;
use crate::cst::stream::Stream;
use crate::cst::words::{ValueWord, Word, alpha_word, is_space, value_word};
use crate::error::Error;
use crate::limits::Limits;
use crate::text::TextOffset;

/// Parses `input` into a green tree under `limits`.
///
/// Fails only on the caps: [`Error::InputTooLarge`] and [`Error::NestingTooDeep`]. Every other input, including
/// binary junk, gives a tree whose tokens concatenate back to `input`.
pub(crate) fn parse_green(input: &[u8], limits: Limits) -> Result<GreenNode, Error> {
    // ── Size cap ─────────────────────────────────────────────────────────────────────────────────────────────
    // Checked before anything else: offsets are u32, and the cap keeps every width sum exact.
    let too_large = || Error::InputTooLarge {
        len: u64::try_from(input.len()).unwrap_or(u64::MAX),
        cap: limits.max_input_bytes(),
    };
    let len = u32::try_from(input.len()).map_err(|_| too_large())?;
    if len > limits.max_input_bytes() {
        return Err(too_large());
    }

    // ── Preprocessor view, then the statement reader ─────────────────────────────────────────────────────────
    let removed = removed_spans(input);
    let mut parser = Parser {
        stream: Stream::new(input, &removed),
        builder: Builder::new(input, &removed),
        depth: 0,
        limits,
    };
    parser.file()?;
    parser.builder.finish()
}

/// How a class body (or the file) ended.
enum BodyEnd {
    /// The input ended (a missing `}` is accepted silently, `ParamFile.cpp#L1582-L1585`).
    EndOfInput,
    /// A `}` at this offset was read; the caller emits it and the `;`s after it.
    CloseBrace(u32),
    /// A statement stopped the body (a [`TokenKind::Stop`] marker is in the tree).
    Stopped,
}

/// Whether the statement just read lets the body continue.
#[derive(PartialEq, Eq)]
enum Flow {
    Continue,
    Stopped,
}

struct Parser<'input> {
    stream: Stream<'input>,
    builder: Builder<'input>,
    /// Current nesting depth (classes and array literals together).
    depth: u32,
    limits: Limits,
}

impl Parser<'_> {
    // ── File and class bodies (ParamFile.cpp#L1571-L1872; ParamFileParse.cpp#L893-L909) ──────────────────────

    /// The root: a class body; after a `}` or a stop, the rest of the input is never read by the engine.
    fn file(&mut self) -> Result<(), Error> {
        match self.body()? {
            BodyEnd::EndOfInput => Ok(()),
            BodyEnd::CloseBrace(at) => {
                self.builder
                    .token(TokenKind::RBrace, at, at.saturating_add(1))?;
                self.trailing_semicolons()?;
                self.unparsed_rest()
            }
            BodyEnd::Stopped => self.unparsed_rest(),
        }
    }

    /// Input after the root ended ("some input after EndOfFile", `ParamFileParse.cpp#L904-L908`).
    fn unparsed_rest(&mut self) -> Result<(), Error> {
        let start = self.stream.offset();
        let end = self.stream.len();
        if start < end {
            self.builder.start_node(NodeKind::Unparsed);
            self.builder.token(TokenKind::Opaque, start, end)?;
            self.builder.finish_node()?;
        }
        Ok(())
    }

    /// One class body (or the file): statements until `}`, the end of input, or a stop.
    fn body(&mut self) -> Result<BodyEnd, Error> {
        loop {
            // #L1577-L1585: skip whitespace; the end of input ends the body.
            let mut c = self.stream.get();
            while is_space(c) {
                c = self.stream.get();
            }
            let Some(first) = c else {
                return Ok(BodyEnd::EndOfInput);
            };
            let first_at = self.stream.last_offset();
            // Trivia between statements belongs to the body, not to the next statement.
            self.builder.trivia_to(first_at)?;
            if first == b'}' {
                return Ok(BodyEnd::CloseBrace(first_at));
            }
            self.stream.unget();
            // #L1597-L1601: the statement's first word decides its kind (keywords are case-sensitive, strcmp).
            let word = alpha_word(&mut self.stream);
            let flow = match word.bytes.as_slice() {
                b"class" => self.class_decl(&word)?,
                b"enum" => self.enum_decl(&word)?,
                b"__EXEC" => self.exec_stmt(&word)?,
                _ => self.entry(&word)?,
            };
            if flow == Flow::Stopped {
                return Ok(BodyEnd::Stopped);
            }
        }
    }

    /// After a closing brace: any mix of whitespace and `;` is consumed, then the next byte is put back
    /// (`ParamFile.cpp#L1588-L1593`, `#L1690-L1695`, `#L1720-L1725`).
    fn trailing_semicolons(&mut self) -> Result<(), Error> {
        loop {
            let c = self.stream.get();
            if c == Some(b';') {
                let at = self.stream.last_offset();
                self.builder
                    .token(TokenKind::Semi, at, at.saturating_add(1))?;
            } else if !is_space(c) {
                self.stream.unget();
                return Ok(());
            }
        }
    }

    // ── Tree helpers ─────────────────────────────────────────────────────────────────────────────────────────

    /// A `Name` node for `word` (empty when the word is empty). Trivia before the word stays outside the node.
    fn name_node(&mut self, word: &Word) -> Result<(), Error> {
        self.builder.trivia_to(word.start)?;
        self.builder.start_node(NodeKind::Name);
        if word.end > word.start {
            self.builder.token(TokenKind::Ident, word.start, word.end)?;
        }
        self.builder.finish_node()
    }

    /// A `Value` node for `word`. Trivia before the word stays outside the node, so a patch that replaces the
    /// value never touches the whitespace around it.
    fn value_node(&mut self, word: &ValueWord) -> Result<(), Error> {
        self.builder.trivia_to(word.start)?;
        self.builder.start_node(NodeKind::Value);
        if word.end > word.start {
            let kind = if word.quoted {
                TokenKind::QuotedString
            } else {
                TokenKind::BareText
            };
            self.builder.token(kind, word.start, word.end)?;
        }
        self.builder.finish_node()
    }

    /// A one-byte token at the offset of the byte just read.
    fn last_byte_token(&mut self, kind: TokenKind) -> Result<(), Error> {
        let at = self.stream.last_offset();
        self.builder.token(kind, at, at.saturating_add(1))
    }

    /// Ends the current statement node at a stop: the unexpected byte (if any), the marker, and the node.
    fn stop_statement(&mut self, c: Option<u8>, reason: StopReason) -> Result<Flow, Error> {
        if c.is_some() {
            self.last_byte_token(TokenKind::Unexpected)?;
        }
        self.builder.marker(TokenKind::Stop(reason))?;
        self.builder.finish_node()?;
        Ok(Flow::Stopped)
    }

    /// Enters one nesting level opened at `at`, or fails with [`Error::NestingTooDeep`].
    fn enter(&mut self, at: u32) -> Result<(), Error> {
        let depth = self.depth.saturating_add(1);
        if depth > self.limits.max_depth() {
            return Err(Error::NestingTooDeep {
                offset: TextOffset::from_raw(at),
                depth,
                cap: self.limits.max_depth(),
            });
        }
        self.depth = depth;
        Ok(())
    }

    /// Leaves one nesting level.
    fn leave(&mut self) {
        self.depth = self.depth.saturating_sub(1);
    }

    /// Reads whitespace from `c` on and returns the first byte that is not whitespace.
    fn skip_space_from(&mut self, mut c: Option<u8>) -> Option<u8> {
        while is_space(c) {
            c = self.stream.get();
        }
        c
    }

    // ── Statements ───────────────────────────────────────────────────────────────────────────────────────────

    /// `class Name [: Base] { ... }` (`ParamFile.cpp#L1601-L1645`).
    fn class_decl(&mut self, keyword: &Word) -> Result<Flow, Error> {
        self.builder.start_node(NodeKind::ClassDecl);
        self.builder
            .token(TokenKind::KwClass, keyword.start, keyword.end)?;
        let name = alpha_word(&mut self.stream);
        self.name_node(&name)?;
        let first = self.stream.get();
        let mut c = self.skip_space_from(first);
        if c == Some(b':') {
            self.last_byte_token(TokenKind::Colon)?;
            let base = alpha_word(&mut self.stream);
            self.name_node(&base)?;
            c = self.stream.get();
        }
        // #L1632-L1641: only whitespace may come before `{`.
        loop {
            match c {
                Some(b'{') => break,
                Some(_) if is_space(c) => c = self.stream.get(),
                _ => return self.stop_statement(c, StopReason::ExpectedOpenBrace),
            }
        }
        let open_at = self.stream.last_offset();
        self.builder
            .token(TokenKind::LBrace, open_at, open_at.saturating_add(1))?;
        self.enter(open_at)?;
        self.builder.start_node(NodeKind::ClassBody);
        let end = self.body()?;
        self.builder.finish_node()?;
        self.leave();
        // The class is added to its parent whatever ended its body (#L1643-L1644: no error check).
        if let BodyEnd::CloseBrace(at) = end {
            self.builder
                .token(TokenKind::RBrace, at, at.saturating_add(1))?;
            self.trailing_semicolons()?;
        }
        self.builder.finish_node()?;
        Ok(Flow::Continue)
    }

    /// `enum [Name] { A, B = value }` (`ParamFile.cpp#L1646-L1702`).
    fn enum_decl(&mut self, keyword: &Word) -> Result<Flow, Error> {
        self.builder.start_node(NodeKind::EnumDecl);
        self.builder
            .token(TokenKind::KwEnum, keyword.start, keyword.end)?;
        let name = alpha_word(&mut self.stream);
        self.name_node(&name)?;
        let mut c = self.stream.get();
        loop {
            match c {
                Some(b'{') => break,
                Some(_) if is_space(c) => c = self.stream.get(),
                _ => return self.stop_statement(c, StopReason::ExpectedOpenBrace),
            }
        }
        self.last_byte_token(TokenKind::LBrace)?;
        // `consumed` is true while the byte in `c` has been read and not yet put in the tree.
        let mut consumed;
        loop {
            self.builder.start_node(NodeKind::EnumItem);
            let item = alpha_word(&mut self.stream);
            self.name_node(&item)?;
            let first = self.stream.get();
            c = self.skip_space_from(first);
            consumed = c.is_some();
            if c == Some(b'=') {
                self.last_byte_token(TokenKind::Eq)?;
                // #L1675-L1682: the value's first byte is read, put back and read again by GetWord, and `c` keeps
                // that byte; so the loop goes on only if the value starts with `,` (an empty value).
                let first = self.stream.get();
                c = self.skip_space_from(first);
                self.stream.unget();
                let value = value_word(&mut self.stream, b",}");
                self.value_node(&value)?;
                consumed = false;
            }
            if consumed && c == Some(b',') {
                self.last_byte_token(TokenKind::Comma)?;
            }
            self.builder.finish_node()?;
            if c != Some(b',') {
                break;
            }
        }
        match (c, consumed) {
            (Some(b'}'), true) => {
                self.last_byte_token(TokenKind::RBrace)?;
                self.trailing_semicolons()?;
            }
            // The brace was put back by GetWord; the engine reads it again, finds no `;` and puts it back once more,
            // so it is left for the parent (#L1688-L1695).
            (Some(b'}'), false) => {}
            (_, true) => return self.stop_statement(c, StopReason::ExpectedEnumSeparator),
            (_, false) => return self.stop_statement(None, StopReason::ExpectedEnumSeparator),
        }
        self.builder.finish_node()?;
        Ok(Flow::Continue)
    }

    /// `__EXEC(text)` (`ParamFile.cpp#L1703-L1733`).
    fn exec_stmt(&mut self, keyword: &Word) -> Result<Flow, Error> {
        self.builder.start_node(NodeKind::ExecStmt);
        self.builder
            .token(TokenKind::KwExec, keyword.start, keyword.end)?;
        let mut c = self.stream.get();
        loop {
            match c {
                Some(b'(') => break,
                Some(_) if is_space(c) => c = self.stream.get(),
                _ => return self.stop_statement(c, StopReason::ExpectedOpenParen),
            }
        }
        self.last_byte_token(TokenKind::LParen)?;
        let text = value_word(&mut self.stream, b")");
        self.value_node(&text)?;
        if let Some(at) = text.dropped {
            self.builder
                .token(TokenKind::Dropped, at, at.saturating_add(1))?;
        }
        let c = self.stream.get();
        if c != Some(b')') {
            return self.stop_statement(c, StopReason::ExpectedCloseParen);
        }
        self.last_byte_token(TokenKind::RParen)?;
        self.trailing_semicolons()?;
        self.builder.finish_node()?;
        Ok(Flow::Continue)
    }

    /// `name = value;` or `name[] = {...};` (`ParamFile.cpp#L1734-L1848`).
    fn entry(&mut self, name: &Word) -> Result<Flow, Error> {
        let c = self.stream.get();
        if c == Some(b'[') {
            return self.array_entry(name);
        }
        self.builder.start_node(NodeKind::ValueEntry);
        self.name_node(name)?;
        let c = self.skip_space_from(c);
        if c != Some(b'=') {
            // #L1781-L1788: the engine reads the rest of the line into an error message, then stops.
            if c.is_some() {
                self.last_byte_token(TokenKind::Unexpected)?;
            }
            let context = value_word(&mut self.stream, b"\n");
            if context.end > context.start {
                self.builder
                    .token(TokenKind::Unexpected, context.start, context.end)?;
            }
            self.builder
                .marker(TokenKind::Stop(StopReason::ExpectedEquals))?;
            self.builder.finish_node()?;
            return Ok(Flow::Stopped);
        }
        self.last_byte_token(TokenKind::Eq)?;
        // #L1790-L1797: whitespace after `=`, line breaks included, is skipped before the value.
        let first = self.stream.get();
        self.skip_space_from(first);
        self.stream.unget();
        let value = value_word(&mut self.stream, b";\n\r");
        self.value_node(&value)?;
        // #L1798-L1803: the byte right after the value must be `;` or a line break.
        let c = self.stream.get();
        match c {
            Some(b';') => self.last_byte_token(TokenKind::Semi)?,
            Some(b'\n' | b'\r') => self.last_byte_token(TokenKind::Newline)?,
            None => return self.stop_statement(None, StopReason::MissingTerminatorAtEof),
            Some(_) => return self.stop_statement(c, StopReason::ExpectedTerminator),
        }
        self.builder.finish_node()?;
        Ok(Flow::Continue)
    }

    /// `name[] = {...};` after the `[` (`ParamFile.cpp#L1738-L1774`).
    fn array_entry(&mut self, name: &Word) -> Result<Flow, Error> {
        self.builder.start_node(NodeKind::ArrayEntry);
        self.name_node(name)?;
        self.last_byte_token(TokenKind::LBracket)?;
        let first = self.stream.get();
        let c = self.skip_space_from(first);
        if c != Some(b']') {
            return self.stop_statement(c, StopReason::ExpectedCloseBracket);
        }
        self.last_byte_token(TokenKind::RBracket)?;
        let first = self.stream.get();
        let c = self.skip_space_from(first);
        if c != Some(b'=') {
            return self.stop_statement(c, StopReason::ExpectedEqualsAfterBrackets);
        }
        self.last_byte_token(TokenKind::Eq)?;
        self.array_literal()?;
        // #L1763-L1772: a `;` must follow the literal (a line break is not enough).
        let first = self.stream.get();
        let c = self.skip_space_from(first);
        if c != Some(b';') {
            return self.stop_statement(c, StopReason::ExpectedSemicolonAfterArray);
        }
        self.last_byte_token(TokenKind::Semi)?;
        self.builder.finish_node()?;
        Ok(Flow::Continue)
    }

    /// An array literal or sub-array (`ParamRawArray::Parse`, `ParamFileParse.cpp#L432-L529`). Errors inside it
    /// stop the literal only; the caller carries on from the current position.
    fn array_literal(&mut self) -> Result<(), Error> {
        let first = self.stream.get();
        let c = self.skip_space_from(first);
        self.builder.start_node(NodeKind::ArrayLiteral);
        if c != Some(b'{') {
            self.array_stop(c, StopReason::ArrayExpectedOpenBrace)?;
            return self.builder.finish_node();
        }
        let open_at = self.stream.last_offset();
        self.builder
            .token(TokenKind::LBrace, open_at, open_at.saturating_add(1))?;
        self.enter(open_at)?;
        loop {
            // #L446-L453: look at the next non-space byte to tell a sub-array from an element.
            let first = self.stream.get();
            let peek = self.skip_space_from(first);
            self.stream.unget();
            let after = if peek == Some(b'{') {
                self.array_literal()?;
                self.stream.get()
            } else {
                self.element()?
            };
            // #L502-L506: the end of input right after an element stops the literal.
            if after.is_none() {
                self.array_stop(None, StopReason::ArrayEndOfInput)?;
                break;
            }
            let sep = self.skip_space_from(after);
            match sep {
                Some(b'}') => {
                    self.last_byte_token(TokenKind::RBrace)?;
                    // #L522-L527: whitespace after the literal is read and the next byte put back.
                    let next = self.stream.get();
                    self.skip_space_from(next);
                    self.stream.unget();
                    break;
                }
                Some(b',') => self.last_byte_token(TokenKind::Comma)?,
                Some(b';') => self.last_byte_token(TokenKind::Semi)?,
                _ => {
                    self.array_stop(sep, StopReason::ArrayExpectedSeparator)?;
                    break;
                }
            }
        }
        self.leave();
        self.builder.finish_node()
    }

    /// One element (#L462-L500). Returns the byte read right after it (the engine's `c`).
    fn element(&mut self) -> Result<Option<u8>, Error> {
        let word = value_word(&mut self.stream, b",;}");
        // The engine's `c = in.get()` right after GetWord. Its token is emitted by the caller, after the element's
        // tokens (the builder needs text order); emitting the element does not move the stream.
        let after = self.stream.get();
        let added = matches!(after, Some(b',' | b';')) || word.some;
        if added || word.end > word.start || word.dropped.is_some() {
            self.builder.trivia_to(word.start)?;
            self.builder.start_node(NodeKind::Element);
            self.value_node(&word)?;
            if let Some(at) = word.dropped {
                self.builder
                    .token(TokenKind::Dropped, at, at.saturating_add(1))?;
            }
            self.builder.finish_node()?;
        }
        Ok(after)
    }

    /// A stop inside an array literal: the unexpected byte (if any) and the marker; the literal node stays open for
    /// the caller to close.
    fn array_stop(&mut self, c: Option<u8>, reason: StopReason) -> Result<(), Error> {
        if c.is_some() {
            self.last_byte_token(TokenKind::Unexpected)?;
        }
        self.builder.marker(TokenKind::Stop(reason))
    }
}
