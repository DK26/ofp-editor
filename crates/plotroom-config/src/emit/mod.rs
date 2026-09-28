// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: Bohemia Interactive a.s. (original C++)
// SPDX-FileCopyrightText: 2026 Plotroom contributors (Rust translation)
// Derived-From: BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/IO/ParamFile/ParamFileParse.cpp
// Modified: translated to Rust and changed, 2026-09-28. Subject to the Additional Terms
// (GPLv3 section 7) from Bohemia Interactive reproduced in NOTICE.
//! The canonical writer: config text exactly as the game's own writer lays it out.
//!
//! **What it owns.** [`write_entries`] and its small input model ([`EntryModel`], [`ClassModel`], [`ScalarModel`],
//! [`ItemModel`]), plus [`WriterProfile`]. It is used for *new* text: a fresh file, a new entry inserted into an
//! existing file (whose surrounding bytes the patch layer keeps), a lexeme built by [`crate::EntryValueLexeme`].
//! Existing text is never re-serialised: edits are span patches (doc 04 §12.3 item 2; core-document-model §4).
//!
//! **The engine's layout** (`ParamFile::Save` and the per-type `Save` functions, `ParamFileParse.cpp#L325-L697`,
//! `#L873-L891`; doc 04 §2.2): one TAB per nesting level; every line ends in CR LF; `class Name` [`: Base`] CRLF,
//! `{` CRLF, members, `};` CRLF; values `name=value;`; strings quoted with `"` doubled and nothing else escaped; ints
//! `%d`; floats per [`WriterProfile`]; bools through the int overload as `0`/`1`; arrays inline when every element
//! reads as a number (`IsNumerical` of its text, so `{"1"}` stays inline, quoted), otherwise one element per line,
//! and a sub-array inside a multi-line array written at its parent's indent; entries in insertion order.
//!
//! **Where it is stricter than the engine.** Names must be `[A-Za-z0-9_]*` and strings may not hold CR, LF or NUL:
//! the engine would write them, but the file would not read back to the same model (CR and NUL are dropped by its
//! preprocessor, LF is reported as an error). Nesting is capped like parsing.
//!
//! **Allocation profile.** One output `Vec<u8>`, plus a `String` per float.
//!
//! **Arithmetic.** Indent levels grow by one per class or array level and are checked against `MAX_NESTING_DEPTH`
//! before they are used, so `saturating_add` on levels, and on the output length in `indent`, cannot trigger.

pub mod float;

use crate::error::Error;
use crate::limits::MAX_NESTING_DEPTH;
use crate::scalar::is_numerical;

pub use float::format_float;

/// Which game version's float spelling to write (core-document-model §4 item 6).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum WriterProfile {
    /// Plain C `%f` (`0.600000`), as the 1.96/1.99-era writer is believed to write [I: CWR's comment says its
    /// fallback changes the older behaviour; real OFP-era files show `%f` values].
    Legacy196Text,
    /// CWR's writer: `%f` when it reads back to the same float, else `%.9g` with `.0` added if needed.
    RemasteredText,
}

/// A scalar value to write.
#[derive(Debug, Clone, PartialEq)]
pub enum ScalarModel {
    /// A string (raw bytes; any code page).
    Text(Vec<u8>),
    /// An integer.
    Int(i32),
    /// A float (must be finite).
    Float(f32),
    /// A boolean, written as `0` or `1` through the engine's int overload.
    Bool(bool),
}

/// One item of an array to write.
#[derive(Debug, Clone, PartialEq)]
pub enum ItemModel {
    /// A scalar element.
    Scalar(ScalarModel),
    /// A nested array.
    Array(Vec<ItemModel>),
}

/// A class to write.
#[derive(Debug, Clone, PartialEq)]
pub struct ClassModel {
    /// The class name.
    pub name: Vec<u8>,
    /// The base class, written as `: Base` (both profiles; [U] whether the 1.99 writer wrote bases at all).
    pub base: Option<Vec<u8>>,
    /// The members, in order.
    pub entries: Vec<EntryModel>,
}

/// One entry to write.
#[derive(Debug, Clone, PartialEq)]
pub enum EntryModel {
    /// A class.
    Class(ClassModel),
    /// `name=value;`
    Value {
        /// The name.
        name: Vec<u8>,
        /// The value.
        value: ScalarModel,
    },
    /// `name[]={...};`
    Array {
        /// The name.
        name: Vec<u8>,
        /// The items, in order.
        items: Vec<ItemModel>,
    },
}

/// Writes `entries` as a top-level config text, laid out as the game writes it (see the module docs).
///
/// # Errors
///
/// [`Error::InvalidLexeme`] for a name outside `[A-Za-z0-9_]*` or a string holding NUL, [`Error::NewlineInQuotedValue`]
/// for a string holding CR or LF, [`Error::NonFiniteFloat`] for NaN or infinity, [`Error::EmitTooDeep`] past 64 levels.
///
/// ```
/// use plotroom_config::{EntryModel, ScalarModel, WriterProfile, write_entries};
///
/// let text = write_entries(
///     &[EntryModel::Value { name: b"skill".to_vec(), value: ScalarModel::Float(0.6) }],
///     WriterProfile::Legacy196Text,
/// )
/// .unwrap();
/// assert_eq!(text, b"skill=0.600000;\r\n");
/// ```
pub fn write_entries(entries: &[EntryModel], profile: WriterProfile) -> Result<Vec<u8>, Error> {
    let mut writer = Writer {
        out: Vec::new(),
        profile,
    };
    for entry in entries {
        writer.entry(entry, 0)?;
    }
    Ok(writer.out)
}

/// The writer's state: the output and the float profile.
struct Writer {
    out: Vec<u8>,
    profile: WriterProfile,
}

impl Writer {
    /// `Indent` (`ParamFileParse.cpp#L325-L331`): one TAB per level.
    fn indent(&mut self, level: u32) {
        self.out.resize(
            self.out
                .len()
                .saturating_add(usize::try_from(level).unwrap_or(0)),
            b'\t',
        );
    }

    /// Checks the nesting depth before a class body or an array literal.
    fn check_depth(level: u32) -> Result<(), Error> {
        if level > MAX_NESTING_DEPTH {
            return Err(Error::EmitTooDeep {
                depth: level,
                cap: MAX_NESTING_DEPTH,
            });
        }
        Ok(())
    }

    fn entry(&mut self, entry: &EntryModel, level: u32) -> Result<(), Error> {
        match entry {
            EntryModel::Class(class) => self.class(class, level),
            EntryModel::Value { name, value } => {
                // `ParamValueSpec::Save` (#L647-L654): indent, name, `=`, value, `;` CRLF.
                check_name(name, "value name")?;
                self.indent(level);
                self.out.extend_from_slice(name);
                self.out.push(b'=');
                self.scalar(value)?;
                self.out.extend_from_slice(b";\r\n");
                Ok(())
            }
            EntryModel::Array { name, items } => {
                // `ParamArray::Save` (#L619-L625): indent, `name[]=`, the literal, `;` CRLF.
                check_name(name, "array name")?;
                self.indent(level);
                self.out.extend_from_slice(name);
                self.out.extend_from_slice(b"[]=");
                self.array(items, level, level.saturating_add(1))?;
                self.out.extend_from_slice(b";\r\n");
                Ok(())
            }
        }
    }

    /// `ParamClass::Save` (#L678-L697).
    fn class(&mut self, class: &ClassModel, level: u32) -> Result<(), Error> {
        check_name(&class.name, "class name")?;
        Self::check_depth(level.saturating_add(1))?;
        self.indent(level);
        self.out.extend_from_slice(b"class ");
        self.out.extend_from_slice(&class.name);
        if let Some(base) = &class.base {
            check_name(base, "base class name")?;
            self.out.extend_from_slice(b": ");
            self.out.extend_from_slice(base);
        }
        self.out.extend_from_slice(b"\r\n");
        self.indent(level);
        self.out.extend_from_slice(b"{\r\n");
        for entry in &class.entries {
            self.entry(entry, level.saturating_add(1))?;
        }
        self.indent(level);
        self.out.extend_from_slice(b"};\r\n");
        Ok(())
    }

    /// `ParamRawArray::Save` (#L531-L577). `indent` is the entry's level (sub-arrays reuse it); `depth` counts
    /// nesting for the cap.
    fn array(&mut self, items: &[ItemModel], indent: u32, depth: u32) -> Result<(), Error> {
        Self::check_depth(depth)?;
        let multi_line = items.iter().any(|item| match item {
            ItemModel::Array(_) => true,
            ItemModel::Scalar(ScalarModel::Text(text)) => !is_numerical(text),
            // Ints, floats (`%g`) and bools always read as numbers.
            ItemModel::Scalar(_) => false,
        });
        if !multi_line {
            self.out.push(b'{');
            for (index, item) in items.iter().enumerate() {
                if index > 0 {
                    self.out.push(b',');
                }
                self.item(item, indent, depth)?;
            }
            self.out.push(b'}');
            return Ok(());
        }
        self.out.extend_from_slice(b"\r\n");
        self.indent(indent);
        self.out.extend_from_slice(b"{\r\n");
        let last = items.len().saturating_sub(1);
        for (index, item) in items.iter().enumerate() {
            self.indent(indent.saturating_add(1));
            self.item(item, indent, depth)?;
            if index < last {
                self.out.push(b',');
            }
            self.out.extend_from_slice(b"\r\n");
        }
        self.indent(indent);
        self.out.push(b'}');
        Ok(())
    }

    /// One array item; a sub-array is saved with the parent's indent (`ParamArrayValueArray::Save`,
    /// `ParamFile.cpp#L1078-L1081`), which gives the engine's odd blank-ish line before a nested multi-line array.
    fn item(&mut self, item: &ItemModel, indent: u32, depth: u32) -> Result<(), Error> {
        match item {
            ItemModel::Scalar(value) => self.scalar(value),
            ItemModel::Array(items) => self.array(items, indent, depth.saturating_add(1)),
        }
    }

    /// A scalar: `ParamRawValue::Save` (#L344-L361), `ParamRawValueInt::Save` (#L418-L423), floats (#L371-L388).
    fn scalar(&mut self, value: &ScalarModel) -> Result<(), Error> {
        match value {
            ScalarModel::Text(text) => {
                check_string(text)?;
                self.out.push(b'"');
                for &byte in text {
                    if byte == b'"' {
                        self.out.extend_from_slice(b"\"\"");
                    } else {
                        self.out.push(byte);
                    }
                }
                self.out.push(b'"');
            }
            ScalarModel::Int(number) => self.out.extend_from_slice(number.to_string().as_bytes()),
            ScalarModel::Float(number) => self
                .out
                .extend_from_slice(format_float(*number, self.profile)?.as_bytes()),
            ScalarModel::Bool(flag) => self.out.push(if *flag { b'1' } else { b'0' }),
        }
        Ok(())
    }
}

/// Names are `[A-Za-z0-9_]*`, the characters the game's reader accepts in a name (an empty name reads back too).
fn check_name(name: &[u8], context: &'static str) -> Result<(), Error> {
    match name
        .iter()
        .position(|byte| !(byte.is_ascii_alphanumeric() || *byte == b'_'))
    {
        None => Ok(()),
        Some(position) => Err(Error::InvalidLexeme {
            context,
            offset_in_lexeme: u32::try_from(position).unwrap_or(u32::MAX),
            byte: name.get(position).copied().unwrap_or(0),
        }),
    }
}

/// Strings may not hold CR or LF (see [`Error::NewlineInQuotedValue`]) or NUL.
pub(crate) fn check_string(text: &[u8]) -> Result<(), Error> {
    for (position, &byte) in text.iter().enumerate() {
        let offset = u32::try_from(position).unwrap_or(u32::MAX);
        match byte {
            b'\r' | b'\n' => {
                return Err(Error::NewlineInQuotedValue {
                    offset_in_value: offset,
                });
            }
            0 => {
                return Err(Error::InvalidLexeme {
                    context: "quoted value",
                    offset_in_lexeme: offset,
                    byte,
                });
            }
            _ => {}
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests_writer_rules;
