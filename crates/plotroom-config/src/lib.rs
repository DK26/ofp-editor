// SPDX-License-Identifier: GPL-3.0-or-later
//! Config text for the game's mission and campaign files: a lossless tree, span patches and the canonical writer.
//!
//! **What it owns.** Layer L1 of the workspace (`docs/architecture/crate-map.md` §4): reading the game's config text
//! format (`mission.sqm`, `description.ext`, `config.cpp`) into a tree that keeps every byte, telling which entries the
//! game keeps and where it stops reading, changing one value without touching any other byte, and writing new text
//! exactly as the game's own writer lays it out. This is spike SP-09 of the M0 roadmap: `render(parse(b)) == b`, span
//! patches, a relative-length green tree, and one test per writer rule of doc 04 §2.2.
//!
//! **Map of the crate.**
//! - [`parse`] / [`ConfigCst`] ([`cst`]): the tree, its cursors ([`cst::cursor`]) and the game's view of it
//!   ([`cst::entries`]: [`ConfigCst::entries`], [`ConfigCst::find`]);
//! - [`lint_syntax`] ([`cst::issues`]): what the game will do with text it does not read as written;
//! - [`ConfigCst::replace_entry_value`] and [`ConfigCst::replace_element_value`] ([`cst::patch`]) with the checked
//!   lexemes of [`cst::lexeme`];
//! - [`write_entries`] ([`emit`]): new text in the engine's layout, with a [`WriterProfile`] for floats;
//! - [`classify_unquoted`] ([`scalar`]): how the game types a bare word;
//! - [`Limits`] ([`limits`]), [`Error`] ([`error`]), and the position newtypes of [`text`].
//!
//! **What depends on it.** `plotroom-mission` (the typed lens, M1) and every crate that reads or edits a config file.
//! Later milestones add the resolved view (inheritance, `>>` paths), raP reading and writing, and `ConfigOrigin`.
//!
//! **Porting.** Parts of this crate translate the game's released source (`BohemiaInteractive/CWR`, GPL-3.0-or-later
//! with Bohemia's section 7 terms); those files carry `Derived-From:` headers, and `NOTICE` reproduces the terms.
//!
//! ```
//! use plotroom_config::{EntryValueLexeme, lint_syntax, parse};
//!
//! let text = b"version=11;\r\nclass Mission\r\n{\r\n\tclass Intel\r\n\t{\r\n\t\tweather=0.2;\r\n\t};\r\n};\r\n";
//! let cst = parse(text).unwrap();
//! assert_eq!(cst.render(), text);               // every byte kept
//! assert!(lint_syntax(&cst).is_empty());         // the game reads it as written
//!
//! let target = cst.entry_value(&[b"Mission", b"Intel", b"weather"]).unwrap();
//! let patched = cst.replace_entry_value(target, EntryValueLexeme::bare(b"0.8").unwrap()).unwrap();
//! assert_eq!(patched.edit().removed().width().to_raw(), 3); // only "0.2" was replaced
//! ```

// Format crates deny arithmetic that can overflow or panic (crate-map §2.4; AGENTS.md "Integer Overflow Safety").
#![deny(clippy::arithmetic_side_effects)]

pub mod cst;
pub mod emit;
pub mod error;
pub mod limits;
pub mod scalar;
pub mod text;

pub use cst::entries::{
    ArrayEntry, ArrayItem, ArrayLiteralView, ClassEntry, Entry, ValueEntry, ValueView,
};
pub use cst::issues::{EngineEffect, IssueKind, SyntaxIssue, lint_syntax};
pub use cst::kinds::{DirectiveKind, NodeKind, StopReason, TokenKind};
pub use cst::lexeme::{ElementValueLexeme, EntryValueLexeme};
pub use cst::patch::{ByteEdit, ElementValueRef, EntryValueRef, Patched};
pub use cst::{ConfigCst, parse, parse_with_limits};
pub use emit::{
    ClassModel, EntryModel, ItemModel, ScalarModel, WriterProfile, format_float, write_entries,
};
pub use error::Error;
pub use limits::{Limits, MAX_CONFIG_TEXT_BYTES, MAX_NESTING_DEPTH};
pub use scalar::{Scalar, classify_unquoted};
pub use text::{TextOffset, TextSpan, TextWidth};
