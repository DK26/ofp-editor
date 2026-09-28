// SPDX-License-Identifier: GPL-3.0-or-later
//! The one error type of `plotroom-config` (`AGENTS.md`, "Error Design").
//!
//! **What it owns.** [`Error`], shared by every module of the crate. Parsing never fails on syntax: malformed text
//! becomes part of the tree and is reported by [`crate::lint_syntax`]. Errors are reserved for the safety caps
//! (input size, nesting depth), for patch and lexeme requests the tree cannot honour, and for the writer.
//!
//! **Display.** Each message embeds its numbers and ends with the next action. It is for developers and logs: a
//! model- or plugin-facing layer maps the variant (not this text) to its own typed findings. Lexeme bytes are
//! untrusted, so no message quotes them; a message names a byte by its numeric value only.

use std::fmt;

use crate::text::TextOffset;

/// Everything that can go wrong in this crate. Every variant carries structured fields.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Error {
    /// The input is larger than the size cap (`Limits::max_input_bytes`).
    InputTooLarge {
        /// Length of the input, in bytes.
        len: u64,
        /// The cap, in bytes.
        cap: u32,
    },
    /// Classes and array literals nest deeper than the depth cap (`Limits::max_depth`).
    NestingTooDeep {
        /// Where the level that passed the cap opens.
        offset: TextOffset,
        /// The depth that level would have had.
        depth: u32,
        /// The cap.
        cap: u32,
    },
    /// The writer was given a model nested deeper than the depth cap.
    EmitTooDeep {
        /// The depth reached.
        depth: u32,
        /// The cap.
        cap: u32,
    },
    /// A value reference was taken from a different tree (an older revision, or another file).
    StaleValueRef {
        /// Where the referenced value started in the tree it came from.
        value_offset: TextOffset,
    },
    /// A lexeme or name contains a byte that its context cannot hold.
    InvalidLexeme {
        /// What was being built, for example `"bare entry value"` or `"class name"`.
        context: &'static str,
        /// Position of the offending byte inside the candidate.
        offset_in_lexeme: u32,
        /// The offending byte.
        byte: u8,
    },
    /// A lexeme that must not be empty was empty.
    EmptyLexeme {
        /// What was being built.
        context: &'static str,
    },
    /// A quoted value would contain a line break, which the game reports as an error on load.
    NewlineInQuotedValue {
        /// Position of the line-break byte inside the value's content.
        offset_in_value: u32,
    },
    /// A float value is NaN or infinite; the text format has no spelling the game reads back as that value.
    NonFiniteFloat {
        /// The float's bit pattern (`f32::to_bits`).
        bits: u32,
    },
    /// A quoted value would be followed by whitespace before its terminator, which makes the game drop the entry
    /// and ignore the rest of the class.
    QuotedValueNeedsAdjacentTerminator {
        /// Where the value ends.
        value_end: TextOffset,
        /// How many bytes of trivia sit between the value and its terminator.
        trivia_len: u32,
    },
    /// Applying the patch would change how the rest of the text is read (a new comment, statement or line).
    PatchChangesStructure {
        /// The first byte where the re-read text differs from the patched tree.
        offset: TextOffset,
    },
    /// The patched text would be larger than the size cap.
    PatchExceedsLimit {
        /// Length of the patched text, in bytes.
        new_len: u64,
        /// The cap, in bytes.
        cap: u32,
    },
    /// A byte outside an edit's declared span changed.
    OutsideSpanChanged {
        /// The first differing byte, counted in the old text.
        first_diff: u64,
    },
    /// An edit's declared span reaches past the end of the old text, or the lengths do not add up.
    EditOutOfRange {
        /// End of the declared removed span.
        span_end: u64,
        /// Length of the old text.
        old_len: u64,
        /// Length of the new text.
        new_len: u64,
    },
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::InputTooLarge { len, cap } => write!(
                f,
                "config text is {len} bytes, over the {cap}-byte cap: check that the file is a text config, or \
                 parse it with larger Limits"
            ),
            Error::NestingTooDeep { offset, depth, cap } => write!(
                f,
                "nesting depth {depth} at {offset} passes the cap of {cap} levels: the file is malformed or \
                 hostile; if it is genuine, parse it with larger Limits"
            ),
            Error::EmitTooDeep { depth, cap } => write!(
                f,
                "the model to write nests {depth} levels, over the cap of {cap}: flatten the model, or pass larger \
                 Limits to the writer"
            ),
            Error::StaleValueRef { value_offset } => write!(
                f,
                "the value reference (value at {value_offset}) belongs to another tree: look the value up again on \
                 the current tree with ConfigCst::entry_value or ConfigCst::element_value"
            ),
            Error::InvalidLexeme {
                context,
                offset_in_lexeme,
                byte,
            } => write!(
                f,
                "{context}: byte 0x{byte:02X} at position {offset_in_lexeme} cannot appear there: remove it, or use \
                 a quoted lexeme (EntryValueLexeme::quoted) for free text"
            ),
            Error::EmptyLexeme { context } => {
                write!(
                    f,
                    "{context} is empty (0 bytes): pass at least one byte, or use a quoted empty string"
                )
            }
            Error::NewlineInQuotedValue { offset_in_value } => write!(
                f,
                "a quoted value has a line break at position {offset_in_value}, which the game reports as an error: \
                 remove the CR or LF byte"
            ),
            Error::NonFiniteFloat { bits } => write!(
                f,
                "float with bits 0x{bits:08X} is NaN or infinite, which the text format cannot hold: pass a finite \
                 value"
            ),
            Error::QuotedValueNeedsAdjacentTerminator {
                value_end,
                trivia_len,
            } => write!(
                f,
                "a quoted value ending at {value_end} would be followed by {trivia_len} bytes of whitespace before \
                 its terminator, and the game drops such an entry and the rest of its class: use a bare lexeme \
                 (EntryValueLexeme::bare, int or float), or first remove the whitespace before the terminator"
            ),
            Error::PatchChangesStructure { offset } => write!(
                f,
                "the patch changes how the text is read from {offset} on (a new comment, statement or line): choose \
                 a lexeme that stays one value in its place"
            ),
            Error::PatchExceedsLimit { new_len, cap } => write!(
                f,
                "the patched text would be {new_len} bytes, over the {cap}-byte cap: use a shorter value"
            ),
            Error::OutsideSpanChanged { first_diff } => write!(
                f,
                "byte {first_diff} outside the edit's declared span changed: the edit is not a span patch; report \
                 this as a bug with the two texts"
            ),
            Error::EditOutOfRange {
                span_end,
                old_len,
                new_len,
            } => write!(
                f,
                "the edit's span ends at byte {span_end}, but the old text is {old_len} bytes and the new text \
                 {new_len} bytes: check the edit against the text it was made for"
            ),
        }
    }
}

impl std::error::Error for Error {}

#[cfg(test)]
mod tests {
    use super::*;

    // ── Error field & Display verification ───────────────────────────────────────────────────────────────────────

    /// Every variant's message embeds its numbers and ends with a next action.
    ///
    /// Why: `AGENTS.md` "Error Design": a developer reading a log must see the values and what to do, without a
    /// debugger. The pairs below list, for each variant, the fragments its message must contain.
    #[test]
    fn every_display_embeds_numbers_and_a_next_action() {
        let cases: Vec<(Error, &[&str])> = vec![
            (
                Error::InputTooLarge { len: 70, cap: 64 },
                &["70 bytes", "64-byte cap", "Limits"],
            ),
            (
                Error::NestingTooDeep {
                    offset: TextOffset::from_raw(31),
                    depth: 65,
                    cap: 64,
                },
                &["depth 65", "byte 31", "64 levels", "larger Limits"],
            ),
            (
                Error::EmitTooDeep { depth: 65, cap: 64 },
                &["65 levels", "cap of 64", "flatten"],
            ),
            (
                Error::StaleValueRef {
                    value_offset: TextOffset::from_raw(9),
                },
                &["byte 9", "ConfigCst::entry_value"],
            ),
            (
                Error::InvalidLexeme {
                    context: "bare entry value",
                    offset_in_lexeme: 3,
                    byte: b';',
                },
                &[
                    "bare entry value",
                    "0x3B",
                    "position 3",
                    "EntryValueLexeme::quoted",
                ],
            ),
            (
                Error::EmptyLexeme {
                    context: "bare entry value",
                },
                &["bare entry value", "0 bytes", "pass at least one byte"],
            ),
            (
                Error::NewlineInQuotedValue { offset_in_value: 4 },
                &["position 4", "remove the CR or LF"],
            ),
            (
                Error::NonFiniteFloat { bits: 0x7FC0_0000 },
                &["0x7FC00000", "finite value"],
            ),
            (
                Error::QuotedValueNeedsAdjacentTerminator {
                    value_end: TextOffset::from_raw(12),
                    trivia_len: 2,
                },
                &["byte 12", "2 bytes of whitespace", "EntryValueLexeme::bare"],
            ),
            (
                Error::PatchChangesStructure {
                    offset: TextOffset::from_raw(40),
                },
                &["byte 40", "choose a lexeme"],
            ),
            (
                Error::PatchExceedsLimit {
                    new_len: 11,
                    cap: 10,
                },
                &["11 bytes", "10-byte cap", "shorter value"],
            ),
            (
                Error::OutsideSpanChanged { first_diff: 17 },
                &["byte 17", "report this as a bug"],
            ),
            (
                Error::EditOutOfRange {
                    span_end: 5,
                    old_len: 3,
                    new_len: 4,
                },
                &["byte 5", "3 bytes", "4 bytes", "check the edit"],
            ),
        ];
        for (error, fragments) in cases {
            let message = error.to_string();
            for fragment in fragments {
                assert!(message.contains(fragment), "{message:?} lacks {fragment:?}");
            }
        }
    }

    /// Errors are comparable and cloneable with their fields, so tests and callers can match on them.
    ///
    /// Why: structured fields are the contract (`AGENTS.md`); a variant's fields must survive a clone.
    #[test]
    fn errors_keep_their_fields() {
        let error = Error::InputTooLarge {
            len: u64::MAX,
            cap: u32::MAX,
        };
        assert_eq!(error.clone(), error);
        assert!(error.to_string().contains(&u64::MAX.to_string()));
    }
}
