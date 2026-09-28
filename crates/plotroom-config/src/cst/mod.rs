// SPDX-License-Identifier: GPL-3.0-or-later
//! The lossless concrete syntax tree of config text: [`ConfigCst`], [`parse`] and [`ConfigCst::render`].
//!
//! **What it owns.** Reading `mission.sqm`, `description.ext` and `config.cpp` text into a tree that keeps every
//! byte: statements, values, whitespace, line breaks (LF and CR LF), tabs, comments, directive lines, and even
//! input the game rejects. The one invariant everything else builds on is `render(parse(b)) == b` for every byte
//! string within the size cap (roadmap SP-09; `docs/architecture/core-document-model.md` §3.1, §12 R1).
//!
//! **Where it fits.** Layer L1 (crate-map §4). The typed mission lens (`plotroom-mission`, M1) reads keys through
//! [`ConfigCst::find`]; edits go through the span patches in [`patch`], which change only the bytes of one value.
//! The resolved view (inheritance, `>>` class paths), raP and the preprocessor proper come later.
//!
//! **How it is built.** Three passes over the input, all pure:
//! 1. [`preproc`] marks the bytes the game's preprocessor removes (comments, directives, CR, NUL);
//! 2. [`parser`] ports the game's statement reader over the remaining bytes ([`stream`], with the word readers of
//!    [`words`]) and reports what it recognises, including the zero-width [`kinds::TokenKind::Stop`] markers where the
//!    game gives up;
//! 3. [`builder`] turns those reports into the green tree ([`green`]) and fills every gap with trivia.
//!
//! **Parsing never fails on syntax.** Only the caps ([`crate::Limits`]) produce errors. Malformed text is kept and
//! described: [`crate::lint_syntax`] derives the issues from the tree, so they stay correct after a patch.

pub mod cursor;
pub mod entries;
pub mod green;
pub mod issues;
pub mod kinds;
pub mod lexeme;
pub mod patch;

mod builder;
mod parser;
mod preproc;
mod stream;
mod words;

use crate::error::Error;
use crate::limits::Limits;
use crate::text::{TextOffset, TextWidth};

use cursor::CstNode;
use green::GreenNode;

/// A parsed config text: the green tree and the limits it was parsed under.
///
/// Cloning is cheap (one `Arc` clone) and gives an immutable snapshot. There is no public constructor other than
/// [`parse`] and [`parse_with_limits`] (and the patch functions, which re-check their result), so a `ConfigCst` always
/// renders to text that parses back into the same tree under the same limits.
#[derive(Debug, Clone)]
pub struct ConfigCst {
    root: GreenNode,
    limits: Limits,
}

impl ConfigCst {
    /// Wraps a tree built by this crate.
    pub(crate) fn from_parts(root: GreenNode, limits: Limits) -> Self {
        Self { root, limits }
    }

    /// The root node of the tree (kind [`kinds::NodeKind::File`]).
    #[must_use]
    pub fn green(&self) -> &GreenNode {
        &self.root
    }

    /// A cursor on the root, at offset 0.
    #[must_use]
    pub fn root(&self) -> CstNode<'_> {
        CstNode::new(&self.root, TextOffset::from_raw(0))
    }

    /// The limits this tree was parsed under; patches keep the text within them.
    #[must_use]
    pub fn limits(&self) -> Limits {
        self.limits
    }

    /// The length of the text, in bytes.
    #[must_use]
    pub fn width(&self) -> TextWidth {
        self.root.width()
    }

    /// The text: every token's bytes, in order. For a tree from [`parse`], this is exactly the parsed input.
    #[must_use]
    pub fn render(&self) -> Vec<u8> {
        let capacity = usize::try_from(self.root.width().to_raw()).unwrap_or(0);
        let mut out = Vec::with_capacity(capacity);
        self.root.write_to(&mut out);
        out
    }
}

/// Parses config text under the default [`Limits`].
///
/// # Errors
///
/// [`Error::InputTooLarge`] above 64 MiB and [`Error::NestingTooDeep`] past 64 levels; nothing else. Malformed text
/// is kept in the tree and reported by [`crate::lint_syntax`].
///
/// ```
/// let text = b"class Mission\r\n{\r\n\tversion=11; // kept\r\n};\r\n";
/// let cst = plotroom_config::parse(text).unwrap();
/// assert_eq!(cst.render(), text);
/// assert!(cst.find(&[b"mission", b"VERSION"]).is_some()); // names are case-insensitive
/// ```
pub fn parse(input: &[u8]) -> Result<ConfigCst, Error> {
    parse_with_limits(input, Limits::DEFAULT)
}

/// Parses config text under the caller's [`Limits`].
///
/// # Errors
///
/// [`Error::InputTooLarge`] when the input is longer than `limits.max_input_bytes()`, and [`Error::NestingTooDeep`]
/// when classes and array literals nest deeper than `limits.max_depth()`.
pub fn parse_with_limits(input: &[u8], limits: Limits) -> Result<ConfigCst, Error> {
    let root = parser::parse_green(input, limits)?;
    Ok(ConfigCst::from_parts(root, limits))
}

#[cfg(test)]
mod tests;
#[cfg(test)]
mod tests_engine;
#[cfg(test)]
mod tests_limits;
#[cfg(test)]
mod tests_patch;
