// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: Bohemia Interactive a.s. (original C++)
// SPDX-FileCopyrightText: 2026 Plotroom contributors (Rust translation)
// Derived-From: BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/IO/ParamFile/ParamFilePrivate.inc
// Modified: translated to Rust and changed, 2026-09-28. Subject to the Additional Terms
// (GPLv3 section 7) from Bohemia Interactive reproduced in NOTICE.
//! The game's two word readers, `GetAlphaWord` and `GetWord` (`ParamFilePrivate.inc#L12-L127`), over the
//! preprocessed stream.
//!
//! **What it owns.** [`alpha_word`] (names and keywords) and [`value_word`] (values, array elements, enum values,
//! `__EXEC` text), and the C character classes they use. They return offsets rather than copies of the text, except
//! the name bytes the parser compares with the keywords; [`crate::cst::parser`] turns the results into tokens.
//!
//! **Differences from the engine.** Nothing is truncated: the engine keeps at most 2047 bytes of a value and 2048 of
//! a name (`WordBuf`, #L10); here the offsets cover every byte and the lint reports the cut.
//!
//! **Allocation profile.** `alpha_word` collects the name's bytes into a `Vec`; `value_word` allocates nothing.
//!
//! **Arithmetic.** Offsets and the content counter step with `saturating_add` as cursors within the input, whose
//! length has already passed the size cap (`Limits::max_input_bytes`, never above `u32::MAX`).

use crate::cst::stream::Stream;

/// A word read by `GetAlphaWord`: its visible range and its bytes.
pub(crate) struct Word {
    pub(crate) start: u32,
    pub(crate) end: u32,
    pub(crate) bytes: Vec<u8>,
}

/// A word read by `GetWord`: its visible range, whether it was quoted, the engine's return value, and the byte the
/// engine threw away after a line break, if any.
pub(crate) struct ValueWord {
    pub(crate) start: u32,
    pub(crate) end: u32,
    pub(crate) quoted: bool,
    pub(crate) some: bool,
    pub(crate) dropped: Option<u32>,
}

/// C `isspace` in the "C" locale (the engine never calls `setlocale`): space, TAB, LF, VT, FF, CR.
#[inline]
pub(crate) fn is_space(byte: Option<u8>) -> bool {
    matches!(byte, Some(b' ' | b'\t' | b'\n' | 0x0B | 0x0C | b'\r'))
}

/// C `isalnum` in the "C" locale, or `_`: the characters of a name (`ParamFilePrivate.inc#L117`).
#[inline]
fn is_name_byte(byte: u8) -> bool {
    byte.is_ascii_alphanumeric() || byte == b'_'
}

/// `GetAlphaWord` (#L109-L127): skip whitespace, then read `[A-Za-z0-9_]*` and put the next byte back.
pub(crate) fn alpha_word(stream: &mut Stream<'_>) -> Word {
    let mut c = stream.get();
    while is_space(c) {
        c = stream.get();
    }
    let start = if c.is_some() {
        stream.last_offset()
    } else {
        stream.offset()
    };
    let mut end = start;
    let mut bytes = Vec::new();
    while let Some(byte) = c {
        if !is_name_byte(byte) {
            break;
        }
        bytes.push(byte);
        end = stream.last_offset().saturating_add(1);
        c = stream.get();
    }
    stream.unget();
    Word { start, end, bytes }
}

/// `GetWord` (#L12-L107): skip whitespace, then read a quoted string (with `""` for `"`) or bare text up to a byte
/// in `terminators`, trimming trailing whitespace. In bare text, a line break ends the word; whitespace after it is
/// skipped and a byte that is not a terminator is consumed and thrown away (#L67-L87).
pub(crate) fn value_word(stream: &mut Stream<'_>, terminators: &[u8]) -> ValueWord {
    let mut c = stream.get();
    while is_space(c) {
        c = stream.get();
    }
    let Some(first) = c else {
        let at = stream.offset();
        return ValueWord {
            start: at,
            end: at,
            quoted: false,
            some: false,
            dropped: None,
        };
    };
    let start = stream.last_offset();
    if first == b'"' {
        return quoted_rest(stream, start);
    }
    // strchr(termin, c) also matches NUL; the preprocessor removes NULs, so this is only a guard.
    let is_terminator = |byte: u8| byte == 0 || terminators.contains(&byte);
    let mut end = start;
    let mut c = Some(first);
    while let Some(byte) = c {
        if is_terminator(byte) {
            stream.unget();
            break;
        }
        if byte == b'\n' || byte == b'\r' {
            let mut next = stream.get();
            while is_space(next) {
                next = stream.get();
            }
            let dropped = match next {
                Some(b) if is_terminator(b) => {
                    stream.unget();
                    None
                }
                Some(_) => Some(stream.last_offset()),
                None => None,
            };
            return ValueWord {
                start,
                end,
                quoted: false,
                some: end > start,
                dropped,
            };
        }
        // RTrim (#L100-L103): the word ends after its last non-space byte.
        if !is_space(Some(byte)) {
            end = stream.last_offset().saturating_add(1);
        }
        c = stream.get();
    }
    ValueWord {
        start,
        end,
        quoted: false,
        some: end > start,
        dropped: None,
    }
}

/// The rest of a quoted word after its opening `"` at `start` (#L23-L58).
fn quoted_rest(stream: &mut Stream<'_>, start: u32) -> ValueWord {
    let mut content_len: u32 = 0;
    let mut end = start.saturating_add(1);
    loop {
        let Some(byte) = stream.get() else {
            // #L32-L38: end of input inside the string; the word is kept only if it has content.
            return ValueWord {
                start,
                end,
                quoted: true,
                some: content_len > 0,
                dropped: None,
            };
        };
        end = stream.last_offset().saturating_add(1);
        if byte == b'"' {
            if stream.get() != Some(b'"') {
                // A lone quote closes the string; the byte after it is put back.
                stream.unget();
                return ValueWord {
                    start,
                    end,
                    quoted: true,
                    some: true,
                    dropped: None,
                };
            }
            // `""` is one quote character; the second quote is content.
            end = stream.last_offset().saturating_add(1);
        }
        // A line break inside quotes is kept; the engine only logs it (#L48-L51).
        content_len = content_len.saturating_add(1);
    }
}
