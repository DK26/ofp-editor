// SPDX-License-Identifier: GPL-3.0-or-later
//! The game's view of a tree: which entries it keeps, and what their names and values are.
//!
//! **What it owns.** [`Entry`] and its three kinds ([`ClassEntry`], [`ValueEntry`], [`ArrayEntry`]), array items and
//! [`ValueView`], plus [`crate::ConfigCst::entries`] and [`crate::ConfigCst::find`]. These answer "what does the game
//! read here" without leaving the lossless tree: every view is a cursor on the nodes that hold the bytes.
//!
//! **The engine's rules applied** (`CWR:engine/Poseidon/IO/ParamFile/ParamFile.cpp`): a statement with a
//! [`TokenKind::Stop`] marker of its own is not added (`#L1849-L1866` runs only for `newEntry`); names compare
//! ASCII-case-insensitively and the first of two equal names wins (`FindIndex`, `#L1213-L1227`; "Member already
//! defined", `#L1862-L1865`). Enum and `__EXEC` statements are not entries. Lookups here are this class's own entries
//! only: inheritance (`class D : B`) belongs to the resolved view (later).
//!
//! **Allocation profile.** Entry lists and names are collected into `Vec`s on request; nothing is cached.

use crate::ConfigCst;
use crate::cst::cursor::{CstElement, CstNode};
use crate::cst::kinds::{NodeKind, TokenKind};
use crate::scalar::{Scalar, classify_unquoted};
use crate::text::TextSpan;

/// An entry the game keeps: a class, a value or an array.
#[derive(Debug, Clone, Copy)]
pub enum Entry<'cst> {
    /// `class Name { ... }`
    Class(ClassEntry<'cst>),
    /// `name = value;`
    Value(ValueEntry<'cst>),
    /// `name[] = { ... };`
    Array(ArrayEntry<'cst>),
}

impl<'cst> Entry<'cst> {
    /// The statement node.
    #[must_use]
    pub fn node(self) -> CstNode<'cst> {
        match self {
            Entry::Class(entry) => entry.node,
            Entry::Value(entry) => entry.node,
            Entry::Array(entry) => entry.node,
        }
    }

    /// The name the game reads (comments and removed bytes inside it left out).
    #[must_use]
    pub fn name(self) -> Vec<u8> {
        name_of(self.node())
    }
}

/// A class the game keeps.
#[derive(Debug, Clone, Copy)]
pub struct ClassEntry<'cst> {
    node: CstNode<'cst>,
}

impl<'cst> ClassEntry<'cst> {
    /// The class name.
    #[must_use]
    pub fn name(self) -> Vec<u8> {
        name_of(self.node)
    }

    /// The base class name after `:`, if any (not resolved: inheritance is the resolved view's job).
    #[must_use]
    pub fn base(self) -> Option<Vec<u8>> {
        let mut after_colon = false;
        for child in self.node.children() {
            match child {
                CstElement::Token(token) if token.kind() == TokenKind::Colon => after_colon = true,
                CstElement::Node(node) if after_colon && node.kind() == NodeKind::Name => {
                    return Some(node.visible_bytes());
                }
                _ => {}
            }
        }
        None
    }

    /// The class's own entries, in order (duplicates and stopped statements left out).
    #[must_use]
    pub fn entries(self) -> Vec<Entry<'cst>> {
        self.node
            .child_node(NodeKind::ClassBody)
            .map(body_entries)
            .unwrap_or_default()
    }

    /// True when the class has its closing `}` (false when the input ended first, or when a statement stopped the
    /// class and its remaining text was read by the parent).
    #[must_use]
    pub fn is_closed(self) -> bool {
        self.node.has_child_token(TokenKind::RBrace)
    }
}

/// A value entry the game keeps.
#[derive(Debug, Clone, Copy)]
pub struct ValueEntry<'cst> {
    node: CstNode<'cst>,
}

impl<'cst> ValueEntry<'cst> {
    /// The entry's name.
    #[must_use]
    pub fn name(self) -> Vec<u8> {
        name_of(self.node)
    }

    /// The entry's value.
    #[must_use]
    pub fn value(self) -> Option<ValueView<'cst>> {
        self.node
            .child_node(NodeKind::Value)
            .map(|node| ValueView { node })
    }
}

/// An array entry the game keeps.
#[derive(Debug, Clone, Copy)]
pub struct ArrayEntry<'cst> {
    node: CstNode<'cst>,
}

impl<'cst> ArrayEntry<'cst> {
    /// The entry's name.
    #[must_use]
    pub fn name(self) -> Vec<u8> {
        name_of(self.node)
    }

    /// The array literal.
    #[must_use]
    pub fn literal(self) -> Option<ArrayLiteralView<'cst>> {
        self.node
            .child_node(NodeKind::ArrayLiteral)
            .map(|node| ArrayLiteralView { node })
    }

    /// The top-level items (shorthand for `literal().items()`).
    #[must_use]
    pub fn items(self) -> Vec<ArrayItem<'cst>> {
        self.literal()
            .map(ArrayLiteralView::items)
            .unwrap_or_default()
    }
}

/// An array literal or sub-array.
#[derive(Debug, Clone, Copy)]
pub struct ArrayLiteralView<'cst> {
    node: CstNode<'cst>,
}

impl<'cst> ArrayLiteralView<'cst> {
    /// The node.
    #[must_use]
    pub fn node(self) -> CstNode<'cst> {
        self.node
    }

    /// The items the game adds, in order (`ParamFileParse.cpp#L453-L500`).
    #[must_use]
    pub fn items(self) -> Vec<ArrayItem<'cst>> {
        self.node
            .child_nodes()
            .filter_map(|node| match node.kind() {
                NodeKind::Element => node
                    .child_node(NodeKind::Value)
                    .map(|value| ArrayItem::Value(ValueView { node: value })),
                NodeKind::ArrayLiteral => Some(ArrayItem::Array(ArrayLiteralView { node })),
                _ => None,
            })
            .collect()
    }
}

/// One item of an array: a value or a sub-array.
#[derive(Debug, Clone, Copy)]
pub enum ArrayItem<'cst> {
    /// A scalar element.
    Value(ValueView<'cst>),
    /// A nested `{ ... }`.
    Array(ArrayLiteralView<'cst>),
}

/// A value: an entry's value, an array element, an enum value or `__EXEC` text.
#[derive(Debug, Clone, Copy)]
pub struct ValueView<'cst> {
    node: CstNode<'cst>,
}

impl<'cst> ValueView<'cst> {
    /// The `Value` node.
    #[must_use]
    pub fn node(self) -> CstNode<'cst> {
        self.node
    }

    /// The bytes the value's node covers (removed trivia inside it included).
    #[must_use]
    pub fn span(self) -> TextSpan {
        self.node.span()
    }

    /// The lexeme the game reads: quotes included, removed trivia (comments, CR bytes) left out.
    #[must_use]
    pub fn lexeme(self) -> Vec<u8> {
        self.node.visible_bytes()
    }

    /// True for a quoted string.
    #[must_use]
    pub fn is_quoted(self) -> bool {
        self.node
            .child_tokens()
            .any(|token| token.kind() == TokenKind::QuotedString)
    }

    /// The value as the game stores it: for a quoted string, the content with `""` read as `"`; otherwise the
    /// bare text (the game keeps at most 2047 bytes; this keeps all of them).
    #[must_use]
    pub fn text(self) -> Vec<u8> {
        let lexeme = self.lexeme();
        if !self.is_quoted() {
            return lexeme;
        }
        unquote(&lexeme)
    }

    /// What the game makes of the value: quoted strings are text; bare words are typed as the engine types them.
    #[must_use]
    pub fn scalar(self) -> Scalar {
        if self.is_quoted() {
            Scalar::Text
        } else {
            classify_unquoted(&self.lexeme())
        }
    }
}

/// The content of a quoted lexeme: after the opening quote, `""` stands for `"` and a lone `"` ends it
/// (`ParamFilePrivate.inc#L23-L58`); an unterminated string runs to the end.
pub(crate) fn unquote(lexeme: &[u8]) -> Vec<u8> {
    let mut out = Vec::with_capacity(lexeme.len());
    let mut bytes = lexeme.iter().skip(1).peekable();
    while let Some(&byte) = bytes.next() {
        if byte == b'"' {
            if bytes.peek() == Some(&&b'"') {
                bytes.next();
            } else {
                break;
            }
        }
        out.push(byte);
    }
    out
}

/// The visible name of a statement: its first `Name` child.
fn name_of(node: CstNode<'_>) -> Vec<u8> {
    node.child_node(NodeKind::Name)
        .map(CstNode::visible_bytes)
        .unwrap_or_default()
}

/// The statements of a body (the file or a class body) that the game adds, with their child index.
pub(crate) fn added_statements(body: CstNode<'_>) -> Vec<(usize, Entry<'_>)> {
    let mut seen: Vec<Vec<u8>> = Vec::new();
    let mut out = Vec::new();
    for (index, child) in body.children().enumerate() {
        let CstElement::Node(node) = child else {
            continue;
        };
        let entry = match node.kind() {
            NodeKind::ClassDecl => Entry::Class(ClassEntry { node }),
            NodeKind::ValueEntry => Entry::Value(ValueEntry { node }),
            NodeKind::ArrayEntry => Entry::Array(ArrayEntry { node }),
            _ => continue,
        };
        // A statement with its own stop marker is never added.
        if node
            .child_tokens()
            .any(|token| matches!(token.kind(), TokenKind::Stop(_)))
        {
            continue;
        }
        let name = entry.name();
        if seen
            .iter()
            .any(|earlier| earlier.eq_ignore_ascii_case(&name))
        {
            continue;
        }
        seen.push(name);
        out.push((index, entry));
    }
    out
}

/// The entries of a body, without indices.
fn body_entries(body: CstNode<'_>) -> Vec<Entry<'_>> {
    added_statements(body)
        .into_iter()
        .map(|(_, entry)| entry)
        .collect()
}

impl ConfigCst {
    /// The file's top-level entries, as the game keeps them.
    #[must_use]
    pub fn entries(&self) -> Vec<Entry<'_>> {
        body_entries(self.root())
    }

    /// Finds an entry by its path of names (for example `[b"Mission", b"Intel", b"weather"]`), comparing names
    /// ASCII-case-insensitively; the first of two equal names wins, as in the game. Only a class's own entries are
    /// searched (no inheritance).
    #[must_use]
    pub fn find(&self, path: &[&[u8]]) -> Option<Entry<'_>> {
        let (last, parents) = path.split_last()?;
        let mut body = self.root();
        for name in parents {
            let Entry::Class(class) = find_in(body, name)? else {
                return None;
            };
            body = class.node.child_node(NodeKind::ClassBody)?;
        }
        find_in(body, last)
    }
}

/// The first added entry of `body` named `name` (case-insensitive).
fn find_in<'cst>(body: CstNode<'cst>, name: &[u8]) -> Option<Entry<'cst>> {
    added_statements(body)
        .into_iter()
        .map(|(_, entry)| entry)
        .find(|entry| entry.name().eq_ignore_ascii_case(name))
}
