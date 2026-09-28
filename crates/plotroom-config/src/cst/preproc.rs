// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: Bohemia Interactive a.s. (original C++)
// SPDX-FileCopyrightText: 2026 Plotroom contributors (Rust translation)
// Derived-From: BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/IO/PreprocC/Preproc.cpp
// Modified: translated to Rust and changed, 2026-09-28. Subject to the Additional Terms
// (GPLv3 section 7) from Bohemia Interactive reproduced in NOTICE.
//! Which bytes the game's preprocessor removes before its config parser runs.
//!
//! **What it owns.** [`removed_spans`], a pure scan that marks every byte range the preprocessor drops: comments,
//! directive lines, CR and NUL bytes, and control bytes at the start of a line. The parser
//! ([`crate::cst::parser`]) then reads the text *around* these ranges, exactly as the game's parser reads the
//! preprocessor's output, and the tree keeps the removed bytes as trivia tokens.
//!
//! **Why this exists.** Every config file the game loads goes through its C-like preprocessor first
//! (`CWR:engine/Poseidon/IO/ParamFile/ParamFileParse.cpp#L279-L323`), so what the parser sees is not the file's
//! bytes. A comment inside a value splits it (`x = 1 /*c*/ 2;` reads as `1  2`), a lone CR joins two lines, and a
//! UTF-8 BOM survives as a stray byte. Reproducing the removal once, up front, lets the parser port the engine's
//! reading logic unchanged and keeps both faithful.
//!
//! **How the scan follows the engine** (`Preproc.cpp`, `GlobalScan` `#L290-L410`, `GetNext` `#L110-L166`):
//! - a `"` outside comments toggles "in quotes" (`#L300-L303`); inside quotes, nothing but CR and NUL is removed;
//! - CR bytes are skipped at the start of every item (`#L113-L116`, `#L140-L143`), so all of them are removed;
//!   NUL bytes produce an empty item (`#L135-L136`), so they are removed too;
//! - `//` runs to the line break and `/* ... */` to its end, the line break of `//` staying (`#L260-L288`);
//! - after a line break outside quotes, every byte below 33 other than LF is skipped (`SkipWhites`, `#L97-L108`),
//!   and a `#` then starts a directive line (`#L316-L372`); the first line counts as following a line break;
//! - `\` followed by a line break is one item that does not start a new line (`#L137-L158`; lexdef `"\\\n"`, `#L15-L33`).
//!
//! **Where it differs (documented simplifications).** A directive is taken to run to the end of its line (for
//! `#define`, across `\` continuations and block comments); text after a directive's operands on the same line is
//! passed on by the engine but is trivia here. Includes are not resolved, macros are not expanded, and both branches
//! of `#ifdef` are read as text: those need `plotroom-preproc` and the file's include set.
//!
//! **Allocation profile.** One `Vec` of spans, at most one entry per input byte; nothing borrows the input.
//!
//! **Arithmetic.** Indices step with `saturating_add` as a cursor within the input, whose length has already passed
//! the size cap (`Limits::max_input_bytes`, `MAX_CONFIG_TEXT_BYTES` by default, never above `u32::MAX`), so the
//! saturation cannot trigger; it only keeps the code panic-free.

use crate::cst::kinds::{DirectiveKind, TokenKind};

/// A byte range the preprocessor removes, and what it is.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) struct Removed {
    /// First removed byte.
    pub(crate) start: u32,
    /// First byte after the range.
    pub(crate) end: u32,
    /// The trivia kind the tree gives these bytes.
    pub(crate) kind: TokenKind,
}

/// Converts an index into the input to `u32`. The caller has checked the input against the size cap, which keeps
/// every index below `u32::MAX`; saturation is only a guard.
#[inline]
fn at(index: usize) -> u32 {
    u32::try_from(index).unwrap_or(u32::MAX)
}

/// Lists, in order and without overlap, every byte range the game's preprocessor removes from `input`.
///
/// Pure: the same input always gives the same spans. Precondition: `input.len()` fits in `u32` (the parser checks
/// the size cap first).
pub(crate) fn removed_spans(input: &[u8]) -> Vec<Removed> {
    let mut out: Vec<Removed> = Vec::new();
    let mut i: usize = 0;
    let mut in_quotes = false;
    // The engine starts in the "after a line break" state (`Preproc::Process`, `item = lxNewLine`, #L253).
    let mut line_start = true;

    while i < input.len() {
        // ── Start of a line, outside quotes: skip low bytes, then look for a directive ───────────────────────
        if line_start && !in_quotes {
            line_start = false;
            while let Some(&byte) = input.get(i) {
                if byte >= 33 || byte == b'\n' {
                    break;
                }
                push(&mut out, i, i.saturating_add(1), line_start_kind(byte));
                i = i.saturating_add(1);
            }
            // `#` starts a directive unless a second `#` follows at once (`##` is its own item, #L159-L166).
            if input.get(i) == Some(&b'#') && input.get(i.saturating_add(1)) != Some(&b'#') {
                let (end, kind) = directive_extent(input, i);
                push(&mut out, i, end, TokenKind::Directive(kind));
                i = end;
            }
            continue;
        }

        let Some(&byte) = input.get(i) else { break };
        match byte {
            b'\r' => {
                push(&mut out, i, i.saturating_add(1), TokenKind::CarriageReturn);
                i = i.saturating_add(1);
            }
            0 => {
                push(&mut out, i, i.saturating_add(1), TokenKind::Nul);
                i = i.saturating_add(1);
            }
            b'"' => {
                in_quotes = !in_quotes;
                i = i.saturating_add(1);
            }
            b'\n' => {
                i = i.saturating_add(1);
                if !in_quotes {
                    line_start = true;
                }
            }
            b'/' if !in_quotes => {
                // `GetNext` skips CRs between the two characters of `//` and `/*` (#L140-L143).
                let second = skip_crs(input, i.saturating_add(1));
                match input.get(second) {
                    Some(b'/') => {
                        let end = line_comment_end(input, second.saturating_add(1));
                        push(&mut out, i, end, TokenKind::LineComment);
                        i = end;
                    }
                    Some(b'*') => {
                        let end = block_comment_end(input, second.saturating_add(1));
                        push(&mut out, i, end, TokenKind::BlockComment);
                        i = end;
                    }
                    _ => i = i.saturating_add(1),
                }
            }
            b'\\' if !in_quotes => {
                // `\` + line break is one item (`lxLineBreak`): the break does not start a new line for directives.
                let after = skip_crs(input, i.saturating_add(1));
                if input.get(after) == Some(&b'\n') {
                    for cr in i.saturating_add(1)..after {
                        push(
                            &mut out,
                            cr,
                            cr.saturating_add(1),
                            TokenKind::CarriageReturn,
                        );
                    }
                    i = after.saturating_add(1);
                } else {
                    i = i.saturating_add(1);
                }
            }
            _ => i = i.saturating_add(1),
        }
    }
    out
}

/// Records a removed range, merging it with the previous one when both are line-start whitespace or control bytes
/// (so a run of indentation becomes one token). CR, NUL, comment and directive ranges stay separate.
fn push(out: &mut Vec<Removed>, start: usize, end: usize, kind: TokenKind) {
    let (start, end) = (at(start), at(end));
    if let Some(last) = out.last_mut() {
        let mergeable = matches!(kind, TokenKind::Whitespace | TokenKind::LineStartControl);
        if mergeable && last.kind == kind && last.end == start {
            last.end = end;
            return;
        }
    }
    out.push(Removed { start, end, kind });
}

/// The trivia kind of one byte below 33 skipped at the start of a line.
fn line_start_kind(byte: u8) -> TokenKind {
    match byte {
        b' ' | b'\t' | 0x0B | 0x0C => TokenKind::Whitespace,
        b'\r' => TokenKind::CarriageReturn,
        0 => TokenKind::Nul,
        _ => TokenKind::LineStartControl,
    }
}

/// The first index at or after `from` that is not a CR.
fn skip_crs(input: &[u8], from: usize) -> usize {
    let mut i = from;
    while input.get(i) == Some(&b'\r') {
        i = i.saturating_add(1);
    }
    i
}

/// Moves `end` back over CR bytes directly before it (but not before `floor`), so that a CR LF line break stays
/// whole instead of splitting its CR into the comment or directive before it.
fn trim_crs_before(input: &[u8], floor: usize, end: usize) -> usize {
    let mut e = end;
    while e > floor {
        let prev = e.saturating_sub(1);
        if input.get(prev) != Some(&b'\r') {
            break;
        }
        e = prev;
    }
    e
}

/// End of a `//` comment whose body starts at `from`: the line break (excluded, with any CRs before it) or the
/// end of the input (`SkipLineComment`, #L277-L288).
fn line_comment_end(input: &[u8], from: usize) -> usize {
    let mut i = from;
    while let Some(&byte) = input.get(i) {
        if byte == b'\n' {
            return trim_crs_before(input, from, i);
        }
        i = i.saturating_add(1);
    }
    input.len()
}

/// End of a `/* ... */` comment whose body starts at `from`: just after `*/`, or the end of the input when it never
/// closes (`SkipBlockComment`, #L260-L275; `last` starts at 0, so `/*/` does not close).
fn block_comment_end(input: &[u8], from: usize) -> usize {
    let mut last: u8 = 0;
    let mut i = from;
    while let Some(&byte) = input.get(i) {
        if last == b'*' && byte == b'/' {
            return i.saturating_add(1);
        }
        last = byte;
        i = i.saturating_add(1);
    }
    input.len()
}

/// The extent and kind of a directive line starting at the `#` at `hash`.
///
/// The directive word follows `#` directly (CRs aside): `# include` is an unknown directive, as in the engine
/// (`#L325-L327`: `ReadNext` reads the item right after `#`).
fn directive_extent(input: &[u8], hash: usize) -> (usize, DirectiveKind) {
    let word_start = skip_crs(input, hash.saturating_add(1));
    let mut word_end = word_start;
    // `validIdChar`: a letter or `_` first, then letters, digits and `_` (#L47-L57).
    while let Some(&byte) = input.get(word_end) {
        let first = word_end == word_start;
        let ok = byte.is_ascii_alphabetic() || byte == b'_' || (!first && byte.is_ascii_digit());
        if !ok {
            break;
        }
        word_end = word_end.saturating_add(1);
    }
    let word = input.get(word_start..word_end).unwrap_or(&[]);
    let kind = match word {
        b"include" => DirectiveKind::Include,
        b"define" => DirectiveKind::Define,
        b"ifdef" => DirectiveKind::IfDef,
        b"ifndef" => DirectiveKind::IfNDef,
        b"else" => DirectiveKind::Else,
        b"endif" => DirectiveKind::EndIf,
        b"undef" => DirectiveKind::Undef,
        _ => DirectiveKind::Unknown,
    };
    let end = if kind == DirectiveKind::Define {
        define_end(input, word_end)
    } else {
        simple_directive_end(input, word_end)
    };
    (end, kind)
}

/// End of a `#define`: the first line break not escaped by `\` and not inside a block comment
/// (`ReadDefineText`, #L597-L618).
fn define_end(input: &[u8], from: usize) -> usize {
    let mut i = from;
    while let Some(&byte) = input.get(i) {
        match byte {
            b'\n' => return trim_crs_before(input, from, i),
            b'\\' => {
                let after = skip_crs(input, i.saturating_add(1));
                i = if input.get(after) == Some(&b'\n') {
                    after.saturating_add(1)
                } else {
                    i.saturating_add(1)
                };
            }
            b'/' => {
                let second = skip_crs(input, i.saturating_add(1));
                i = match input.get(second) {
                    Some(b'*') => block_comment_end(input, second.saturating_add(1)),
                    Some(b'/') => line_comment_end(input, second.saturating_add(1)),
                    _ => i.saturating_add(1),
                };
            }
            _ => i = i.saturating_add(1),
        }
    }
    input.len()
}

/// End of any other directive: the line break, or the start of a comment that follows the directive (the comment
/// is then its own removed range, as the engine removes it separately).
fn simple_directive_end(input: &[u8], from: usize) -> usize {
    let mut i = from;
    while let Some(&byte) = input.get(i) {
        if byte == b'\n' {
            return trim_crs_before(input, from, i);
        }
        if byte == b'/' {
            let second = skip_crs(input, i.saturating_add(1));
            if matches!(input.get(second), Some(b'/' | b'*')) {
                return i;
            }
        }
        i = i.saturating_add(1);
    }
    input.len()
}
