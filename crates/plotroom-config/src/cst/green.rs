// SPDX-License-Identifier: GPL-3.0-or-later
//! The green tree: immutable, `Arc`-shared nodes and tokens that store widths, not offsets.
//!
//! **What it owns.** [`GreenNode`], [`GreenToken`] and [`GreenChild`], the storage of a [`crate::ConfigCst`].
//!
//! **The model (for readers new to "green trees").** A green tree is the storage layer made popular by Roslyn and
//! used by rust-analyzer's `rowan`: every node knows its kind, its children and its total width in bytes, but not
//! where it sits in the file. Positions are computed on the way down by a cursor ([`crate::cst::cursor`]) that adds
//! up the widths of earlier siblings. Because nothing stores an absolute position, an edit rebuilds only the nodes
//! on the path from the edited leaf to the root; every other subtree is shared, unchanged, between the old and the
//! new tree (`Arc` clones), which keeps snapshots cheap (`docs/architecture/core-document-model.md` §3.1, §6).
//!
//! **Why in house.** `rowan` and `cstree` both store token text as UTF-8 `&str`. Config files carry raw code-page
//! bytes (CP1250/1251/1252) and must round-trip them unchanged (D017 item 5), so this crate stores token bytes as
//! `Box<[u8]>`. This answers the open question in core-document-model §3.1 and §13 item 4 for the CST spike (SP-09).
//!
//! **Allocation profile.** One `Arc` per node and per token, plus each token's exact bytes. Nothing is interned yet
//! (implementation placeholder: SP-10 measures whether a per-parse cache of common tokens such as `=`, `;` and line
//! breaks pays off).

use std::sync::Arc;

use crate::cst::kinds::{NodeKind, TokenKind};
use crate::text::TextWidth;

// ── Tokens ───────────────────────────────────────────────────────────────────────────────────────────────────────

/// A leaf: a kind and its exact bytes. Cloning is an `Arc` clone.
#[derive(Debug, Clone)]
pub struct GreenToken(Arc<GreenTokenData>);

#[derive(Debug)]
struct GreenTokenData {
    kind: TokenKind,
    width: TextWidth,
    bytes: Box<[u8]>,
}

impl GreenToken {
    /// Builds a token, or returns `None` if `bytes` is longer than `u32::MAX` (the size cap keeps parsed tokens far
    /// below that; lexemes built by callers are checked the same way).
    pub(crate) fn new(kind: TokenKind, bytes: &[u8]) -> Option<Self> {
        let width = TextWidth::of_len(bytes.len())?;
        Some(Self(Arc::new(GreenTokenData {
            kind,
            width,
            bytes: bytes.into(),
        })))
    }

    /// The token's kind.
    #[inline]
    #[must_use]
    pub fn kind(&self) -> TokenKind {
        self.0.kind
    }

    /// The token's exact bytes, as they appear in the file.
    #[inline]
    #[must_use]
    pub fn bytes(&self) -> &[u8] {
        &self.0.bytes
    }

    /// The token's width in bytes.
    #[inline]
    #[must_use]
    pub fn width(&self) -> TextWidth {
        self.0.width
    }
}

// ── Nodes ────────────────────────────────────────────────────────────────────────────────────────────────────────

/// An inner node: a kind, its children and the sum of their widths. Cloning is an `Arc` clone.
#[derive(Debug, Clone)]
pub struct GreenNode(Arc<GreenNodeData>);

#[derive(Debug)]
struct GreenNodeData {
    kind: NodeKind,
    width: TextWidth,
    children: Box<[GreenChild]>,
}

/// A child of a node: another node or a token.
#[derive(Debug, Clone)]
pub enum GreenChild {
    /// An inner node.
    Node(GreenNode),
    /// A leaf.
    Token(GreenToken),
}

impl GreenChild {
    /// The child's width in bytes.
    #[inline]
    #[must_use]
    pub fn width(&self) -> TextWidth {
        match self {
            GreenChild::Node(node) => node.width(),
            GreenChild::Token(token) => token.width(),
        }
    }
}

impl GreenNode {
    /// Builds a node, summing its children's widths with checked arithmetic; `None` if the sum passes `u32::MAX`.
    pub(crate) fn new(kind: NodeKind, children: Vec<GreenChild>) -> Option<Self> {
        let width = children
            .iter()
            .try_fold(TextWidth::from_raw(0), |sum, child| {
                sum.checked_add(child.width())
            })?;
        Some(Self(Arc::new(GreenNodeData {
            kind,
            width,
            children: children.into_boxed_slice(),
        })))
    }

    /// The node's kind.
    #[inline]
    #[must_use]
    pub fn kind(&self) -> NodeKind {
        self.0.kind
    }

    /// The node's width in bytes (the sum of its children's widths).
    #[inline]
    #[must_use]
    pub fn width(&self) -> TextWidth {
        self.0.width
    }

    /// The node's children, in text order.
    #[inline]
    #[must_use]
    pub fn children(&self) -> &[GreenChild] {
        &self.0.children
    }

    /// True when both handles point at the same shared node (not merely equal content).
    ///
    /// Why it exists: patches must share every untouched subtree with the old tree; tests prove it with this, and
    /// value references use it to check that they belong to the tree they are applied to.
    #[inline]
    #[must_use]
    pub fn ptr_eq(&self, other: &GreenNode) -> bool {
        Arc::ptr_eq(&self.0, &other.0)
    }

    /// A copy of this node with child `index` replaced; `None` if `index` is out of range or the width overflows.
    ///
    /// Only this node is new: the other children are `Arc` clones of the originals (path copying).
    pub(crate) fn with_child_replaced(&self, index: usize, child: GreenChild) -> Option<GreenNode> {
        let mut children: Vec<GreenChild> = self.children().to_vec();
        let slot = children.get_mut(index)?;
        *slot = child;
        GreenNode::new(self.kind(), children)
    }

    /// Appends the node's bytes (every token in order) to `out`.
    ///
    /// Recursion depth equals tree depth, which the nesting cap bounds.
    pub(crate) fn write_to(&self, out: &mut Vec<u8>) {
        for child in self.children() {
            match child {
                GreenChild::Node(node) => node.write_to(out),
                GreenChild::Token(token) => out.extend_from_slice(token.bytes()),
            }
        }
    }

    /// Compares two trees by shape, kinds and bytes. Returns `Ok(())` when they are identical, or the offset of the
    /// first token (or node) where they differ.
    ///
    /// Why it exists: a patch is accepted only if re-parsing its rendered text gives back exactly the patched tree
    /// ([`crate::cst::patch`]); the offset tells the caller where the text started to read differently.
    pub(crate) fn first_difference(&self, other: &GreenNode) -> Result<(), u32> {
        let mut offset: u32 = 0;
        diff_nodes(self, other, &mut offset)
    }
}

/// Walks two nodes in parallel; `offset` tracks the position of the current child in the first tree.
///
/// `offset` is a cursor within the first tree's width, which the size cap bounds, so its `saturating_add` cannot
/// trigger. Recursion depth is the tree depth, which the nesting cap bounds.
fn diff_nodes(left: &GreenNode, right: &GreenNode, offset: &mut u32) -> Result<(), u32> {
    if left.ptr_eq(right) {
        // Shared subtree: identical by construction; skip it.
        *offset = offset.saturating_add(left.width().to_raw());
        return Ok(());
    }
    if left.kind() != right.kind() || left.children().len() != right.children().len() {
        return Err(*offset);
    }
    for (l, r) in left.children().iter().zip(right.children()) {
        match (l, r) {
            (GreenChild::Node(ln), GreenChild::Node(rn)) => diff_nodes(ln, rn, offset)?,
            (GreenChild::Token(lt), GreenChild::Token(rt)) => {
                if lt.kind() != rt.kind() || lt.bytes() != rt.bytes() {
                    return Err(*offset);
                }
                *offset = offset.saturating_add(lt.width().to_raw());
            }
            _ => return Err(*offset),
        }
    }
    Ok(())
}
