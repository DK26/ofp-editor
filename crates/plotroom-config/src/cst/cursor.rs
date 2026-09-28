// SPDX-License-Identifier: GPL-3.0-or-later
//! Cursors over the green tree: [`CstNode`], [`CstToken`] and [`CstElement`], which add absolute offsets.
//!
//! **What it owns.** Walking the tree with positions. The green tree stores only widths ([`crate::cst::green`]);
//! a cursor carries the offset of the node it points at and computes each child's offset by adding up the widths of
//! the children before it, with checked arithmetic. Cursors borrow the tree (`'cst`), so they cannot outlive it.
//!
//! **Allocation profile.** Walking children allocates nothing; [`CstNode::tokens`], [`CstNode::text`] and
//! [`CstNode::visible_bytes`] collect into a `Vec` for convenience.

use std::slice;

use crate::cst::green::{GreenChild, GreenNode, GreenToken};
use crate::cst::kinds::{NodeKind, TokenKind};
use crate::text::{TextOffset, TextSpan, TextWidth};

/// A node and its absolute offset.
#[derive(Debug, Clone, Copy)]
pub struct CstNode<'cst> {
    green: &'cst GreenNode,
    offset: TextOffset,
}

/// A token and its absolute offset.
#[derive(Debug, Clone, Copy)]
pub struct CstToken<'cst> {
    green: &'cst GreenToken,
    offset: TextOffset,
}

/// A child of a node: a node or a token, with its offset.
#[derive(Debug, Clone, Copy)]
pub enum CstElement<'cst> {
    /// An inner node.
    Node(CstNode<'cst>),
    /// A token.
    Token(CstToken<'cst>),
}

/// The span `offset..offset+width`, or an empty span at `offset` if the end would overflow (impossible for a tree
/// built under the size cap).
fn span_of(offset: TextOffset, width: TextWidth) -> TextSpan {
    TextSpan::at(offset, width).unwrap_or(TextSpan::empty_at(offset))
}

impl<'cst> CstNode<'cst> {
    /// A cursor on `green` at `offset`.
    pub(crate) fn new(green: &'cst GreenNode, offset: TextOffset) -> Self {
        Self { green, offset }
    }

    /// The node's kind.
    #[must_use]
    pub fn kind(self) -> NodeKind {
        self.green.kind()
    }

    /// The underlying green node.
    #[must_use]
    pub fn green(self) -> &'cst GreenNode {
        self.green
    }

    /// The bytes this node covers.
    #[must_use]
    pub fn span(self) -> TextSpan {
        span_of(self.offset, self.green.width())
    }

    /// The node's children with their offsets.
    #[must_use]
    pub fn children(self) -> Children<'cst> {
        Children {
            iter: self.green.children().iter(),
            offset: Some(self.offset),
        }
    }

    /// The child nodes (tokens skipped).
    pub fn child_nodes(self) -> impl Iterator<Item = CstNode<'cst>> {
        self.children().filter_map(|child| match child {
            CstElement::Node(node) => Some(node),
            CstElement::Token(_) => None,
        })
    }

    /// The first child node of `kind`, if any.
    #[must_use]
    pub fn child_node(self, kind: NodeKind) -> Option<CstNode<'cst>> {
        self.child_nodes().find(|node| node.kind() == kind)
    }

    /// The direct child tokens (nodes skipped).
    pub fn child_tokens(self) -> impl Iterator<Item = CstToken<'cst>> {
        self.children().filter_map(|child| match child {
            CstElement::Token(token) => Some(token),
            CstElement::Node(_) => None,
        })
    }

    /// True when a direct child token has this kind.
    #[must_use]
    pub fn has_child_token(self, kind: TokenKind) -> bool {
        self.child_tokens().any(|token| token.kind() == kind)
    }

    /// Every token under this node, in text order.
    #[must_use]
    pub fn tokens(self) -> Vec<CstToken<'cst>> {
        let mut out = Vec::new();
        self.collect_tokens(&mut out);
        out
    }

    fn collect_tokens(self, out: &mut Vec<CstToken<'cst>>) {
        for child in self.children() {
            match child {
                CstElement::Node(node) => node.collect_tokens(out),
                CstElement::Token(token) => out.push(token),
            }
        }
    }

    /// The node's exact bytes.
    #[must_use]
    pub fn text(self) -> Vec<u8> {
        let mut out = Vec::new();
        self.green.write_to(&mut out);
        out
    }

    /// The bytes of the node's non-trivia tokens: what the game's parser reads for a name or a value, with
    /// comments, removed CRs and similar trivia left out.
    #[must_use]
    pub fn visible_bytes(self) -> Vec<u8> {
        let mut out = Vec::new();
        for token in self.tokens() {
            if !token.kind().is_trivia() {
                out.extend_from_slice(token.bytes());
            }
        }
        out
    }
}

impl<'cst> CstToken<'cst> {
    /// The token's kind.
    #[must_use]
    pub fn kind(self) -> TokenKind {
        self.green.kind()
    }

    /// The token's exact bytes.
    #[must_use]
    pub fn bytes(self) -> &'cst [u8] {
        self.green.bytes()
    }

    /// The bytes this token covers.
    #[must_use]
    pub fn span(self) -> TextSpan {
        span_of(self.offset, self.green.width())
    }
}

impl crate::ConfigCst {
    /// A compact one-line dump of the tree, for tests and diagnostics (not a stable format).
    ///
    /// Nodes print as `Kind[children]`; punctuation tokens as their character; zero-width stops as
    /// `Stop(Reason)`; other tokens as `Kind'bytes'`, with bytes outside printable ASCII (and `'` and `\`) escaped
    /// as `\r`, `\n`, `\t` or `\xNN`. Example: `x=1;` dumps as `File[ValueEntry[Name[Ident'x'] = Value[BareText'1'] ;]]`.
    #[must_use]
    pub fn debug_tree(&self) -> String {
        let mut out = String::new();
        dump_node(self.root(), &mut out);
        out
    }
}

/// Appends the dump of `node` (see [`crate::ConfigCst::debug_tree`]).
fn dump_node(node: CstNode<'_>, out: &mut String) {
    out.push_str(&format!("{:?}[", node.kind()));
    for (index, child) in node.children().enumerate() {
        if index > 0 {
            out.push(' ');
        }
        match child {
            CstElement::Node(inner) => dump_node(inner, out),
            CstElement::Token(token) => dump_token(token, out),
        }
    }
    out.push(']');
}

/// Appends the dump of one token.
fn dump_token(token: CstToken<'_>, out: &mut String) {
    let punctuation = match token.kind() {
        TokenKind::LBrace => Some('{'),
        TokenKind::RBrace => Some('}'),
        TokenKind::LBracket => Some('['),
        TokenKind::RBracket => Some(']'),
        TokenKind::Colon => Some(':'),
        TokenKind::Eq => Some('='),
        TokenKind::Semi => Some(';'),
        TokenKind::Comma => Some(','),
        TokenKind::LParen => Some('('),
        TokenKind::RParen => Some(')'),
        _ => None,
    };
    if let (Some(character), [_]) = (punctuation, token.bytes()) {
        out.push(character);
        return;
    }
    out.push_str(&format!("{:?}", token.kind()));
    if token.bytes().is_empty() {
        return;
    }
    out.push('\'');
    for &byte in token.bytes() {
        match byte {
            b'\r' => out.push_str("\\r"),
            b'\n' => out.push_str("\\n"),
            b'\t' => out.push_str("\\t"),
            b'\'' | b'\\' => out.push_str(&format!("\\x{byte:02X}")),
            0x20..=0x7E => out.push(char::from(byte)),
            _ => out.push_str(&format!("\\x{byte:02X}")),
        }
    }
    out.push('\'');
}

/// Iterator over a node's children with offsets (see [`CstNode::children`]).
#[derive(Debug, Clone)]
pub struct Children<'cst> {
    iter: slice::Iter<'cst, GreenChild>,
    /// Offset of the next child; `None` after an (impossible) overflow, which ends the iteration.
    offset: Option<TextOffset>,
}

impl<'cst> Iterator for Children<'cst> {
    type Item = CstElement<'cst>;

    fn next(&mut self) -> Option<Self::Item> {
        let offset = self.offset?;
        let child = self.iter.next()?;
        self.offset = offset.checked_add(child.width());
        Some(match child {
            GreenChild::Node(node) => CstElement::Node(CstNode::new(node, offset)),
            GreenChild::Token(token) => CstElement::Token(CstToken {
                green: token,
                offset,
            }),
        })
    }
}
