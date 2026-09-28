// SPDX-License-Identifier: GPL-3.0-or-later
//! Checked replacement values: [`EntryValueLexeme`] and [`ElementValueLexeme`].
//!
//! **What it owns.** The only way to say "put these bytes where a value was". A lexeme is a *witness*
//! (`AGENTS.md`, "Witness and guard types"): its existence proves the bytes were checked to read back, in their
//! context, as exactly one value and nothing else, so a patch cannot open a comment, end a statement or start a new
//! line. The two types differ because the contexts do: an entry value ends at `;` or a line break, an array element
//! also at `,` and `}` (`CWR:engine/Poseidon/IO/ParamFile/ParamFile.cpp#L1797`, `ParamFileParse.cpp#L465`).
//!
//! **How the check works.** Each constructor applies explicit rules first (for a precise error), then proves
//! itself by running the real parser on the lexeme in a tiny synthetic statement (`v=<lexeme>;` or
//! `a[]={<lexeme>};`) and requiring one kept value whose bytes are exactly the lexeme.
//!
//! **Allocation profile.** One boxed byte slice per lexeme, plus the proof parse's small tree.

use crate::cst::entries::{ArrayItem, Entry};
use crate::emit::{WriterProfile, check_string, format_float};
use crate::error::Error;

/// The two contexts a value can be replaced in.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Context {
    Entry,
    Element,
}

impl Context {
    fn name(self, quoted: bool) -> &'static str {
        match (self, quoted) {
            (Context::Entry, true) => "quoted entry value",
            (Context::Entry, false) => "bare entry value",
            (Context::Element, true) => "quoted array element",
            (Context::Element, false) => "bare array element",
        }
    }
}

/// The checked bytes shared by both lexeme types.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct Lexeme {
    quoted: bool,
    bytes: Box<[u8]>,
}

impl Lexeme {
    pub(crate) fn is_quoted(&self) -> bool {
        self.quoted
    }

    pub(crate) fn bytes(&self) -> &[u8] {
        &self.bytes
    }

    /// `"content"` with `"` doubled; CR, LF and NUL refused.
    fn quoted(content: &[u8], context: Context) -> Result<Self, Error> {
        check_string(content)?;
        let mut bytes = Vec::with_capacity(content.len().saturating_add(2));
        bytes.push(b'"');
        for &byte in content {
            if byte == b'"' {
                bytes.extend_from_slice(b"\"\"");
            } else {
                bytes.push(byte);
            }
        }
        bytes.push(b'"');
        Self::proven(true, bytes, context)
    }

    /// Bare text, checked against the context's terminators and the preprocessor's special bytes.
    fn bare(text: &[u8], context: Context) -> Result<Self, Error> {
        let name = context.name(false);
        if text.is_empty() {
            return Err(Error::EmptyLexeme { context: name });
        }
        let invalid = |position: usize| Error::InvalidLexeme {
            context: name,
            offset_in_lexeme: u32::try_from(position).unwrap_or(u32::MAX),
            byte: text.get(position).copied().unwrap_or(0),
        };
        let is_space = |byte: u8| matches!(byte, b' ' | b'\t' | b'\n' | 0x0B | 0x0C | b'\r');
        // Leading or trailing whitespace would be skipped or trimmed by the game's reader.
        if text.first().is_some_and(|b| is_space(*b)) {
            return Err(invalid(0));
        }
        let last = text.len().saturating_sub(1);
        if text.last().is_some_and(|b| is_space(*b)) {
            return Err(invalid(last));
        }
        if context == Context::Element && text.first() == Some(&b'{') {
            return Err(invalid(0));
        }
        for (position, &byte) in text.iter().enumerate() {
            // `;` and line breaks end a value; `"` toggles the preprocessor's quote state for the rest of the file;
            // NUL and CR are dropped by the preprocessor; `,` and `}` end an element.
            let ends_value = matches!(byte, b';' | b'\n' | b'\r' | 0 | b'"');
            let ends_element = context == Context::Element && matches!(byte, b',' | b'}');
            // `//` and `/*` start comments, which the preprocessor removes.
            let starts_comment =
                byte == b'/' && matches!(text.get(position.saturating_add(1)), Some(b'/' | b'*'));
            if ends_value || ends_element || starts_comment {
                return Err(invalid(position));
            }
        }
        Self::proven(false, text.to_vec(), context)
    }

    /// Runs the real parser on the lexeme in a synthetic statement and accepts it only if the game would read back
    /// exactly one value made of exactly these bytes.
    fn proven(quoted: bool, bytes: Vec<u8>, context: Context) -> Result<Self, Error> {
        let (prefix, suffix): (&[u8], &[u8]) = match context {
            Context::Entry => (b"v=", b";"),
            Context::Element => (b"a[]={", b"};"),
        };
        let mut probe = Vec::with_capacity(bytes.len().saturating_add(8));
        probe.extend_from_slice(prefix);
        probe.extend_from_slice(&bytes);
        probe.extend_from_slice(suffix);
        let fail = || Error::InvalidLexeme {
            context: context.name(quoted),
            offset_in_lexeme: 0,
            byte: bytes.first().copied().unwrap_or(0),
        };
        let cst = crate::parse(&probe).map_err(|_| fail())?;
        let value = match (context, cst.entries().as_slice()) {
            (Context::Entry, [Entry::Value(entry)]) => entry.value(),
            (Context::Element, [Entry::Array(array)]) => match array.items().as_slice() {
                [ArrayItem::Value(value)] => Some(*value),
                _ => None,
            },
            _ => None,
        };
        let value = value.ok_or_else(fail)?;
        // The value node must hold exactly one token: the lexeme, with no trivia split into it.
        let tokens = value.node().tokens();
        let exact = tokens.len() == 1
            && tokens
                .first()
                .is_some_and(|token| token.bytes() == bytes.as_slice());
        // Any issue but the length note means the game would not read the lexeme back as written.
        let clean = crate::lint_syntax(&cst)
            .iter()
            .all(|issue| issue.kind() == crate::IssueKind::ValueTooLong);
        if !exact || !clean {
            return Err(fail());
        }
        Ok(Self {
            quoted,
            bytes: bytes.into_boxed_slice(),
        })
    }
}

/// A checked replacement for an entry's value (`name = <value>;`).
///
/// **When to use.** To change one value of a parsed file with [`crate::ConfigCst::replace_entry_value`]; build it with
/// [`EntryValueLexeme::quoted`], [`EntryValueLexeme::int`], [`EntryValueLexeme::float`] or [`EntryValueLexeme::bare`].
///
/// **When not to use.** For array elements use [`ElementValueLexeme`] (a different context: `,` and `}` end an
/// element). To write a whole new file use [`crate::write_entries`].
///
/// **Security.** The bytes are untrusted input (user or model text). The constructors refuse anything that would
/// read back as more or less than one value (a `;`, a line break, a comment opener, a stray quote), and prove it by
/// parsing. There is no other constructor, no `Default`, no `From<Vec<u8>>` and no public field.
#[doc(alias = "set_value")]
#[doc(alias = "value_edit")]
#[must_use = "a lexeme does nothing on its own: pass it to ConfigCst::replace_entry_value"]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EntryValueLexeme(Lexeme);

impl EntryValueLexeme {
    /// A quoted string holding `content` (raw bytes, any code page); `"` is doubled, as the game writes it.
    ///
    /// # Errors
    ///
    /// [`Error::NewlineInQuotedValue`] for CR or LF, [`Error::InvalidLexeme`] for NUL.
    pub fn quoted(content: &[u8]) -> Result<Self, Error> {
        Lexeme::quoted(content, Context::Entry).map(Self)
    }

    /// An integer, spelled `%d`.
    pub fn int(value: i32) -> Self {
        Self(Lexeme {
            quoted: false,
            bytes: value.to_string().into_bytes().into_boxed_slice(),
        })
    }

    /// A float, spelled as `profile` writes it.
    ///
    /// # Errors
    ///
    /// [`Error::NonFiniteFloat`] for NaN or infinity.
    pub fn float(value: f32, profile: WriterProfile) -> Result<Self, Error> {
        let text = format_float(value, profile)?;
        Ok(Self(Lexeme {
            quoted: false,
            bytes: text.into_bytes().into_boxed_slice(),
        }))
    }

    /// Bare text (an enum token such as `WEST`, a number in a chosen spelling, an expression).
    ///
    /// # Errors
    ///
    /// [`Error::EmptyLexeme`] when empty; [`Error::InvalidLexeme`] for leading or trailing whitespace, `;`, CR, LF,
    /// NUL, `"`, or a `//` or `/*` comment opener.
    pub fn bare(text: &[u8]) -> Result<Self, Error> {
        Lexeme::bare(text, Context::Entry).map(Self)
    }

    /// The lexeme's bytes, as they will appear in the file.
    #[must_use]
    pub fn as_bytes(&self) -> &[u8] {
        self.0.bytes()
    }

    pub(crate) fn lexeme(&self) -> &Lexeme {
        &self.0
    }
}

/// A checked replacement for one array element (`{..., <value>, ...}`).
///
/// **When to use.** With [`crate::ConfigCst::replace_element_value`].
///
/// **When not to use.** For entry values use [`EntryValueLexeme`]; to replace a whole sub-array, edit its elements one
/// by one (a sub-array replacement is not offered yet).
///
/// **Security.** As [`EntryValueLexeme`], with `,` and `}` refused as well and `{` refused as the first byte.
#[doc(alias = "set_element")]
#[must_use = "a lexeme does nothing on its own: pass it to ConfigCst::replace_element_value"]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ElementValueLexeme(Lexeme);

impl ElementValueLexeme {
    /// A quoted string holding `content`; `"` is doubled.
    ///
    /// # Errors
    ///
    /// [`Error::NewlineInQuotedValue`] for CR or LF, [`Error::InvalidLexeme`] for NUL.
    pub fn quoted(content: &[u8]) -> Result<Self, Error> {
        Lexeme::quoted(content, Context::Element).map(Self)
    }

    /// An integer, spelled `%d`.
    pub fn int(value: i32) -> Self {
        Self(Lexeme {
            quoted: false,
            bytes: value.to_string().into_bytes().into_boxed_slice(),
        })
    }

    /// A float, spelled as `profile` writes it.
    ///
    /// # Errors
    ///
    /// [`Error::NonFiniteFloat`] for NaN or infinity.
    pub fn float(value: f32, profile: WriterProfile) -> Result<Self, Error> {
        let text = format_float(value, profile)?;
        Ok(Self(Lexeme {
            quoted: false,
            bytes: text.into_bytes().into_boxed_slice(),
        }))
    }

    /// Bare text.
    ///
    /// # Errors
    ///
    /// As [`EntryValueLexeme::bare`], plus `,`, `}` anywhere and `{` first.
    pub fn bare(text: &[u8]) -> Result<Self, Error> {
        Lexeme::bare(text, Context::Element).map(Self)
    }

    /// The lexeme's bytes, as they will appear in the file.
    #[must_use]
    pub fn as_bytes(&self) -> &[u8] {
        self.0.bytes()
    }

    pub(crate) fn lexeme(&self) -> &Lexeme {
        &self.0
    }
}
