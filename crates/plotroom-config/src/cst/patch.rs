// SPDX-License-Identifier: GPL-3.0-or-later
//! Span patches: replace one value and change no other byte (`docs/architecture/core-document-model.md` §4, §12 R2).
//!
//! **What it owns.** Value references ([`EntryValueRef`], [`ElementValueRef`]), the replace operations on
//! [`ConfigCst`], their result [`Patched`], and [`ByteEdit`], the declared change with its check
//! [`ByteEdit::check_outside_unchanged`].
//!
//! **How a patch works.**
//! 1. The reference must come from this very tree (`Arc` identity of the root), else [`Error::StaleValueRef`].
//! 2. A new `Value` node holding the lexeme's single token replaces the old one; only the nodes on the path to the
//!    root are rebuilt, every other subtree is shared with the old tree (path copying, [`crate::cst::green`]).
//! 3. The result must stay within the tree's size cap ([`Error::PatchExceedsLimit`]).
//! 4. The patched text is parsed again and must give exactly the patched tree; otherwise the new bytes would change
//!    how something else is read ([`Error::PatchChangesStructure`]). This is O(file) per patch: a placeholder until
//!    SP-10 measures whether re-reading only the enclosing statement is enough.
//!
//! **Allocation profile.** One new node per level of the edited path; the verification parse allocates a second
//! tree, which is dropped.
//!
//! **Arithmetic.** New widths are summed with `checked_add` (path copying) and compared with the size cap; lengths in
//! [`ByteEdit::check_outside_unchanged`] use `checked_sub`/`checked_add` and map a failure to
//! [`Error::EditOutOfRange`]. The `saturating_add` calls left are for error reports (a position or a length that is
//! only shown) and for summing trivia widths inside one statement, which the size cap bounds.

use crate::ConfigCst;
use crate::cst::cursor::{CstElement, CstNode};
use crate::cst::entries::{Entry, added_statements};
use crate::cst::green::{GreenChild, GreenNode, GreenToken};
use crate::cst::kinds::{NodeKind, TokenKind};
use crate::cst::lexeme::{ElementValueLexeme, EntryValueLexeme, Lexeme};
use crate::cst::parser::parse_green;
use crate::error::Error;
use crate::text::{TextOffset, TextSpan, TextWidth};

/// A reference to one entry's value in one tree revision.
///
/// **When to use.** Get it from [`ConfigCst::entry_value`], then pass it to [`ConfigCst::replace_entry_value`] on the
/// same tree. **When not to use.** It cannot be kept across edits: after a patch, look the value up again on the new
/// tree. **Security.** It borrows the tree it came from and is checked against that tree's root when used, so it
/// can never point into another file or an older revision.
#[must_use = "a value reference does nothing on its own: pass it to ConfigCst::replace_entry_value"]
#[derive(Debug, Clone)]
pub struct EntryValueRef<'cst> {
    root: &'cst GreenNode,
    path: Vec<usize>,
    span: TextSpan,
}

impl EntryValueRef<'_> {
    /// The bytes the current value covers.
    #[must_use]
    pub fn span(&self) -> TextSpan {
        self.span
    }
}

/// A reference to one array element's value in one tree revision (see [`EntryValueRef`]).
#[must_use = "a value reference does nothing on its own: pass it to ConfigCst::replace_element_value"]
#[derive(Debug, Clone)]
pub struct ElementValueRef<'cst> {
    root: &'cst GreenNode,
    path: Vec<usize>,
    span: TextSpan,
}

impl ElementValueRef<'_> {
    /// The bytes the current element covers.
    #[must_use]
    pub fn span(&self) -> TextSpan {
        self.span
    }
}

/// The byte-level description of a patch: `removed` in the old text was replaced by `inserted` bytes.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ByteEdit {
    removed: TextSpan,
    inserted: TextWidth,
}

impl ByteEdit {
    /// The replaced range of the old text.
    #[must_use]
    pub fn removed(self) -> TextSpan {
        self.removed
    }

    /// The number of bytes inserted in its place.
    #[must_use]
    pub fn inserted(self) -> TextWidth {
        self.inserted
    }

    /// Checks that `old` and `new` are equal outside this edit: the same bytes before `removed`, and the same bytes
    /// after it (shifted by the change in length).
    ///
    /// # Errors
    ///
    /// [`Error::EditOutOfRange`] when the span or the lengths do not fit the texts, [`Error::OutsideSpanChanged`] with
    /// the first differing byte otherwise.
    #[must_use = "the check's result is the proof: handle the error"]
    pub fn check_outside_unchanged(self, old: &[u8], new: &[u8]) -> Result<(), Error> {
        let as_u64 = |n: usize| u64::try_from(n).unwrap_or(u64::MAX);
        let start = usize::try_from(self.removed.start().to_raw()).unwrap_or(usize::MAX);
        let end = usize::try_from(self.removed.end().to_raw()).unwrap_or(usize::MAX);
        let inserted = usize::try_from(self.inserted.to_raw()).unwrap_or(usize::MAX);
        let out_of_range = || Error::EditOutOfRange {
            span_end: as_u64(end),
            old_len: as_u64(old.len()),
            new_len: as_u64(new.len()),
        };
        let expected_len = old
            .len()
            .checked_sub(end.saturating_sub(start))
            .and_then(|kept| kept.checked_add(inserted))
            .ok_or_else(out_of_range)?;
        if end > old.len() || expected_len != new.len() {
            return Err(out_of_range());
        }
        let (old_before, new_before) = (
            old.get(..start).ok_or_else(out_of_range)?,
            new.get(..start).ok_or_else(out_of_range)?,
        );
        if let Some(diff) = old_before.iter().zip(new_before).position(|(a, b)| a != b) {
            return Err(Error::OutsideSpanChanged {
                first_diff: as_u64(diff),
            });
        }
        let new_after_start = start.checked_add(inserted).ok_or_else(out_of_range)?;
        let old_after = old.get(end..).ok_or_else(out_of_range)?;
        let new_after = new.get(new_after_start..).ok_or_else(out_of_range)?;
        if let Some(diff) = old_after.iter().zip(new_after).position(|(a, b)| a != b) {
            return Err(Error::OutsideSpanChanged {
                first_diff: as_u64(end.saturating_add(diff)),
            });
        }
        Ok(())
    }
}

/// The result of a patch: the new tree and the edit that produced it.
#[must_use = "a patch builds a new tree and leaves the old one unchanged: keep the result with Patched::into_parts"]
#[derive(Debug, Clone)]
pub struct Patched {
    cst: ConfigCst,
    edit: ByteEdit,
}

impl Patched {
    /// The new tree.
    #[must_use]
    pub fn cst(&self) -> &ConfigCst {
        &self.cst
    }

    /// The byte edit from the old text to the new one.
    #[must_use]
    pub fn edit(&self) -> ByteEdit {
        self.edit
    }

    /// The new tree and the edit.
    #[must_use]
    pub fn into_parts(self) -> (ConfigCst, ByteEdit) {
        (self.cst, self.edit)
    }
}

impl ConfigCst {
    /// A reference to the value of the entry at `path` (names compared case-insensitively, first match wins), or
    /// `None` if there is no such value entry.
    pub fn entry_value(&self, path: &[&[u8]]) -> Option<EntryValueRef<'_>> {
        let (mut index_path, statement) = self.locate(path)?;
        let Entry::Value(_) = statement else {
            return None;
        };
        let (value_index, value) = child_of_kind(statement.node(), NodeKind::Value)?;
        index_path.push(value_index);
        Some(EntryValueRef {
            root: self.green(),
            path: index_path,
            span: value.span(),
        })
    }

    /// A reference to one element of the array at `path`: `indices` selects the item at each nesting level
    /// (`[2]` is the third item, `[1, 0]` the first item of the second item's sub-array).
    pub fn element_value(&self, path: &[&[u8]], indices: &[usize]) -> Option<ElementValueRef<'_>> {
        let (mut index_path, statement) = self.locate(path)?;
        let Entry::Array(_) = statement else {
            return None;
        };
        let (literal_index, mut literal) = child_of_kind(statement.node(), NodeKind::ArrayLiteral)?;
        index_path.push(literal_index);
        let (last, parents) = indices.split_last()?;
        for item in parents {
            let (child_index, child) = nth_item(literal, *item)?;
            if child.kind() != NodeKind::ArrayLiteral {
                return None;
            }
            index_path.push(child_index);
            literal = child;
        }
        let (element_index, element) = nth_item(literal, *last)?;
        let (value_index, value) = child_of_kind(element, NodeKind::Value)?;
        index_path.extend([element_index, value_index]);
        Some(ElementValueRef {
            root: self.green(),
            path: index_path,
            span: value.span(),
        })
    }

    /// Replaces one entry value, leaving every other byte unchanged.
    ///
    /// # Errors
    ///
    /// [`Error::StaleValueRef`] for a reference from another tree, [`Error::QuotedValueNeedsAdjacentTerminator`] when a
    /// quoted lexeme would be followed by whitespace before `;`, [`Error::PatchExceedsLimit`] past the size cap and
    /// [`Error::PatchChangesStructure`] when the new text would read differently elsewhere.
    ///
    /// ```
    /// use plotroom_config::{EntryValueLexeme, parse};
    ///
    /// let old = b"class Intel\r\n{\r\n\tweather=0.2; // calm\r\n};\r\n";
    /// let cst = parse(old).unwrap();
    /// let target = cst.entry_value(&[b"Intel", b"weather"]).unwrap();
    /// let patched = cst.replace_entry_value(target, EntryValueLexeme::bare(b"0.75").unwrap()).unwrap();
    /// let (new_cst, edit) = patched.into_parts();
    /// let new = new_cst.render();
    /// assert_eq!(new, b"class Intel\r\n{\r\n\tweather=0.75; // calm\r\n};\r\n");
    /// edit.check_outside_unchanged(old, &new).unwrap();
    /// ```
    pub fn replace_entry_value(
        &self,
        target: EntryValueRef<'_>,
        lexeme: EntryValueLexeme,
    ) -> Result<Patched, Error> {
        self.replace_value(
            target.root,
            &target.path,
            target.span,
            lexeme.lexeme(),
            true,
        )
    }

    /// Replaces one array element, leaving every other byte unchanged.
    ///
    /// # Errors
    ///
    /// As [`ConfigCst::replace_entry_value`] (whitespace after a quoted element is fine for the game).
    pub fn replace_element_value(
        &self,
        target: ElementValueRef<'_>,
        lexeme: ElementValueLexeme,
    ) -> Result<Patched, Error> {
        self.replace_value(
            target.root,
            &target.path,
            target.span,
            lexeme.lexeme(),
            false,
        )
    }

    /// The added statement at `path` and the child-index path to it.
    fn locate(&self, path: &[&[u8]]) -> Option<(Vec<usize>, Entry<'_>)> {
        let (last, parents) = path.split_last()?;
        let mut index_path = Vec::with_capacity(path.len().saturating_mul(2));
        let mut body = self.root();
        for name in parents {
            let (index, entry) = find_named(body, name)?;
            let Entry::Class(_) = entry else { return None };
            let (body_index, class_body) = child_of_kind(entry.node(), NodeKind::ClassBody)?;
            index_path.extend([index, body_index]);
            body = class_body;
        }
        let (index, entry) = find_named(body, last)?;
        index_path.push(index);
        Some((index_path, entry))
    }

    fn replace_value(
        &self,
        root: &GreenNode,
        path: &[usize],
        span: TextSpan,
        lexeme: &Lexeme,
        is_entry: bool,
    ) -> Result<Patched, Error> {
        // ── 1. The reference belongs to this tree ─────────────────────────────────────────────────────────────
        if !root.ptr_eq(self.green()) {
            return Err(Error::StaleValueRef {
                value_offset: span.start(),
            });
        }
        // ── 2. A quoted entry value needs its terminator right after the closing quote ─────────────────────────
        if is_entry
            && lexeme.is_quoted()
            && let Some(trivia_len) = whitespace_after_value(self.root(), path)
        {
            return Err(Error::QuotedValueNeedsAdjacentTerminator {
                value_end: span.end(),
                trivia_len,
            });
        }
        // ── 3. Path copy with the new value node ──────────────────────────────────────────────────────────────
        let kind = if lexeme.is_quoted() {
            TokenKind::QuotedString
        } else {
            TokenKind::BareText
        };
        let cap = self.limits().max_input_bytes();
        let too_large = |extra: usize| Error::PatchExceedsLimit {
            new_len: u64::from(self.width().to_raw())
                .saturating_add(u64::try_from(extra).unwrap_or(u64::MAX)),
            cap,
        };
        let token =
            GreenToken::new(kind, lexeme.bytes()).ok_or_else(|| too_large(lexeme.bytes().len()))?;
        let inserted = token.width();
        let value = GreenNode::new(NodeKind::Value, vec![GreenChild::Token(token)])
            .ok_or_else(|| too_large(lexeme.bytes().len()))?;
        let new_root = replace_at(root, path, GreenChild::Node(value))
            .ok_or_else(|| too_large(lexeme.bytes().len()))?;
        // ── 4. Size cap ───────────────────────────────────────────────────────────────────────────────────────
        if new_root.width().to_raw() > cap {
            return Err(Error::PatchExceedsLimit {
                new_len: u64::from(new_root.width().to_raw()),
                cap,
            });
        }
        // ── 5. The new text must read back as exactly the patched tree ─────────────────────────────────────────
        let mut text = Vec::with_capacity(usize::try_from(new_root.width().to_raw()).unwrap_or(0));
        new_root.write_to(&mut text);
        let changed = |offset: u32| Error::PatchChangesStructure {
            offset: TextOffset::from_raw(offset),
        };
        let reread =
            parse_green(&text, self.limits()).map_err(|_| changed(span.start().to_raw()))?;
        new_root.first_difference(&reread).map_err(changed)?;
        Ok(Patched {
            cst: ConfigCst::from_parts(new_root, self.limits()),
            edit: ByteEdit {
                removed: span,
                inserted,
            },
        })
    }
}

/// The first added statement of `body` named `name`, with its child index.
fn find_named<'cst>(body: CstNode<'cst>, name: &[u8]) -> Option<(usize, Entry<'cst>)> {
    added_statements(body)
        .into_iter()
        .find(|(_, entry)| entry.name().eq_ignore_ascii_case(name))
}

/// The first child node of `kind`, with its index among all children.
fn child_of_kind(node: CstNode<'_>, kind: NodeKind) -> Option<(usize, CstNode<'_>)> {
    node.children()
        .enumerate()
        .find_map(|(index, child)| match child {
            CstElement::Node(inner) if inner.kind() == kind => Some((index, inner)),
            _ => None,
        })
}

/// The `n`th item (element or sub-array) of an array literal, with its child index.
fn nth_item(literal: CstNode<'_>, n: usize) -> Option<(usize, CstNode<'_>)> {
    literal
        .children()
        .enumerate()
        .filter_map(|(index, child)| match child {
            CstElement::Node(inner)
                if matches!(inner.kind(), NodeKind::Element | NodeKind::ArrayLiteral) =>
            {
                Some((index, inner))
            }
            _ => None,
        })
        .nth(n)
}

/// Rebuilds `node` with the child at the end of `path` replaced (path copying).
fn replace_at(node: &GreenNode, path: &[usize], replacement: GreenChild) -> Option<GreenNode> {
    let (first, rest) = path.split_first()?;
    if rest.is_empty() {
        return node.with_child_replaced(*first, replacement);
    }
    let GreenChild::Node(child) = node.children().get(*first)? else {
        return None;
    };
    let rebuilt = replace_at(child, rest, replacement)?;
    node.with_child_replaced(*first, GreenChild::Node(rebuilt))
}

/// When the first byte the game sees after an entry's value is whitespace (bytes the preprocessor removes, such as
/// comments, are invisible to it), the width of the trivia between the value and its terminator; otherwise `None`.
fn whitespace_after_value(root: CstNode<'_>, path: &[usize]) -> Option<u32> {
    let (value_index, statement_path) = path.split_last()?;
    let mut node = root;
    for index in statement_path {
        let CstElement::Node(child) = node.children().nth(*index)? else {
            return None;
        };
        node = child;
    }
    let mut width: u32 = 0;
    let mut visible_whitespace = false;
    for child in node.children().skip(value_index.saturating_add(1)) {
        let CstElement::Token(token) = child else {
            break;
        };
        let kind = token.kind();
        if !kind.is_trivia() {
            break;
        }
        // A line break is a terminator in its own right; whatever follows it does not matter here.
        if kind == TokenKind::Newline && !visible_whitespace {
            return None;
        }
        visible_whitespace |= kind == TokenKind::Whitespace;
        width = width.saturating_add(token.span().width().to_raw());
    }
    visible_whitespace.then_some(width)
}
