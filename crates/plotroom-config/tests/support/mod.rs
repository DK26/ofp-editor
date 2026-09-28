// SPDX-License-Identifier: GPL-3.0-or-later
//! Test-only statement model, renderer with injected trivia, and skeleton extraction for the property tests.
//!
//! **What it builds.** A random config text from a small statement model ([`Stmt`]) with random trivia (whitespace,
//! LF, CR LF, lone CR, `//` and `/* */` comments, directive lines) at every position where the game's reader accepts
//! it, following the engine rules the parser ports (`CWR:engine/Poseidon/IO/ParamFile/ParamFile.cpp#L1571-L1872`):
//! - two name-like tokens need visible whitespace between them (a removed comment would join them);
//! - between a name and `[` only bytes the preprocessor removes (comments, lone CR) may appear;
//! - a bare value may be followed by spaces and comments, but not by a line break, before `;`;
//! - a quoted value must be followed by `;` with only removed bytes in between;
//! - a bare array element may not be followed by a line break before its separator;
//! - a `//` comment ends with a line break, and directive lines sit alone on their line.
//!
//! **How randomness flows.** Proptest generates the model and a vector of seeds; [`Renderer`] consumes the seeds to
//! pick trivia, so a failing case shrinks and replays deterministically.
#![cfg(test)]
#![allow(
    dead_code,
    reason = "each property-test file uses a different part of this shared support module"
)]

use plotroom_config::{ConfigCst, NodeKind};
use proptest::prelude::*;

/// A statement of the model.
#[derive(Debug, Clone)]
pub enum Stmt {
    Class {
        name: String,
        base: Option<String>,
        body: Vec<Stmt>,
    },
    Value {
        name: String,
        lexeme: Vec<u8>,
    },
    Array {
        name: String,
        items: Vec<Item>,
    },
    Enum {
        name: String,
        items: Vec<String>,
    },
    Exec {
        text: Vec<u8>,
    },
}

/// An array item of the model.
#[derive(Debug, Clone)]
pub enum Item {
    Value(Vec<u8>),
    Array(Vec<Item>),
}

/// The skeleton the game reads: statement kinds, names and raw lexemes, without trivia.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Skel {
    Class(String, Option<String>, Vec<Skel>),
    Value(String, Vec<u8>),
    Array(String, Vec<SkelItem>),
    Enum(String, Vec<String>),
    Exec(Vec<u8>),
}

/// A skeleton array item.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SkelItem {
    Value(Vec<u8>),
    Array(Vec<SkelItem>),
}

// ── Strategies ───────────────────────────────────────────────────────────────────────────────────────────────────

/// A name stem; uniqueness is added by the renderer's suffix, so keywords can never be produced.
fn stem() -> impl Strategy<Value = String> {
    "[A-Za-z_][A-Za-z0-9_]{0,5}"
}

/// A bare lexeme: name characters, `.`, `+`, `-`, and single inner spaces; never empty, never space-edged.
fn bare_lexeme() -> impl Strategy<Value = Vec<u8>> {
    "[A-Za-z0-9_.+-]{1,6}( [A-Za-z0-9_.+-]{1,4}){0,2}".prop_map(String::into_bytes)
}

/// A quoted lexeme: printable bytes (including `;`, `/`, `{`), code-page bytes, and `""` escapes.
fn quoted_lexeme() -> impl Strategy<Value = Vec<u8>> {
    proptest::collection::vec(prop_oneof![Just(b'"'), 0x20u8..0x7F, 0x80u8..=0xFF], 0..8).prop_map(
        |content| {
            let mut out = vec![b'"'];
            for byte in content {
                if byte == b'"' {
                    out.extend_from_slice(b"\"\"");
                } else {
                    out.push(byte);
                }
            }
            out.push(b'"');
            out
        },
    )
}

fn lexeme() -> impl Strategy<Value = Vec<u8>> {
    prop_oneof![bare_lexeme(), quoted_lexeme()]
}

fn item() -> impl Strategy<Value = Item> {
    let leaf = lexeme().prop_map(Item::Value);
    leaf.prop_recursive(3, 12, 4, |inner| {
        proptest::collection::vec(inner, 0..4).prop_map(Item::Array)
    })
}

/// A statement tree of bounded depth and size.
pub fn statements() -> impl Strategy<Value = Vec<Stmt>> {
    let leaf = prop_oneof![
        (stem(), lexeme()).prop_map(|(name, lexeme)| Stmt::Value { name, lexeme }),
        (stem(), proptest::collection::vec(item(), 0..4))
            .prop_map(|(name, items)| Stmt::Array { name, items }),
        (stem(), proptest::collection::vec(stem(), 1..4))
            .prop_map(|(name, items)| Stmt::Enum { name, items }),
        "[A-Za-z0-9_ =+]{1,8}"
            .prop_map(|text| Stmt::Exec {
                text: text.trim().to_owned().into_bytes()
            })
            .prop_filter(
                "exec text must not be empty",
                |stmt| matches!(stmt, Stmt::Exec { text } if !text.is_empty())
            ),
    ];
    let tree = leaf.prop_recursive(3, 24, 5, |inner| {
        (
            stem(),
            proptest::option::of(stem()),
            proptest::collection::vec(inner, 0..5),
        )
            .prop_map(|(name, base, body)| Stmt::Class { name, base, body })
    });
    proptest::collection::vec(tree, 0..6)
}

// ── Rendering with trivia ────────────────────────────────────────────────────────────────────────────────────────

/// Where trivia is inserted, and which kinds that position allows.
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Slot {
    /// Anything, including line breaks, comments and directive lines.
    Any,
    /// Like `Any`, but at least one visible whitespace byte (separates two name-like tokens).
    Separating,
    /// Spaces, tabs, block comments and lone CRs: no line break.
    SameLine,
    /// Only bytes the preprocessor removes (block comments, lone CRs).
    RemovedOnly,
}

/// Renders a model, picking trivia from a seed list.
pub struct Renderer {
    seeds: Vec<u32>,
    next: usize,
    counter: usize,
    pub out: Vec<u8>,
    /// Final names (stem + unique suffix), in render order, for the skeleton.
    names: Vec<String>,
}

impl Renderer {
    pub fn new(seeds: Vec<u32>) -> Self {
        Self {
            seeds,
            next: 0,
            counter: 0,
            out: Vec::new(),
            names: Vec::new(),
        }
    }

    fn seed(&mut self) -> u32 {
        let value = self
            .seeds
            .get(self.next % self.seeds.len().max(1))
            .copied()
            .unwrap_or(0);
        self.next = self.next.wrapping_add(1);
        value.wrapping_add(
            u32::try_from(self.next)
                .unwrap_or(0)
                .wrapping_mul(2_654_435_761),
        )
    }

    /// A unique name: the stem plus a counter suffix (so no two entries collide, and no keyword appears).
    fn unique(&mut self, stem: &str) -> String {
        self.counter = self.counter.wrapping_add(1);
        format!("{stem}_{}", self.counter)
    }

    /// Emits trivia for one slot.
    pub fn trivia(&mut self, slot: Slot) {
        let pieces = self.seed() % 3;
        for _ in 0..pieces {
            let choice = self.seed() % 7;
            match (slot, choice) {
                (_, 0) if slot != Slot::RemovedOnly => {
                    let ws: &[u8] =
                        [&b" "[..], b"\t", b"  ", b"\x0B", b"\x0C"][(self.seed() % 5) as usize];
                    self.out.extend_from_slice(ws);
                }
                (Slot::Any | Slot::Separating, 1) => {
                    let newline: &[u8] = if self.seed().is_multiple_of(2) {
                        b"\n"
                    } else {
                        b"\r\n"
                    };
                    self.out.extend_from_slice(newline);
                }
                (Slot::Any | Slot::Separating, 2) => {
                    self.out.extend_from_slice(b"// note ; { \" */\n");
                }
                (Slot::Any | Slot::Separating, 3) => {
                    self.out
                        .extend_from_slice(b"\n#define MACRO_X 1 \\\n  + 2\n");
                }
                (_, 4) => self.out.extend_from_slice(b"/* c ; } \" // */"),
                (_, 5) => self.out.push(b'\r'),
                _ => {}
            }
        }
        if slot == Slot::Separating {
            self.out.push(b' ');
        }
        // A lone CR right before the next token is fine; a CR at the very end is fine too.
    }

    pub fn statements(&mut self, statements: &[Stmt]) -> Vec<Skel> {
        let mut skel = Vec::new();
        for statement in statements {
            self.trivia(Slot::Any);
            skel.push(self.statement(statement));
        }
        self.trivia(Slot::Any);
        skel
    }

    fn statement(&mut self, statement: &Stmt) -> Skel {
        match statement {
            Stmt::Class { name, base, body } => {
                let name = self.unique(name);
                self.out.extend_from_slice(b"class");
                self.trivia(Slot::Separating);
                self.out.extend_from_slice(name.as_bytes());
                let base = base.as_ref().map(|base| {
                    let base = self.unique(base);
                    self.trivia(Slot::Any);
                    self.out.push(b':');
                    self.trivia(Slot::Any);
                    self.out.extend_from_slice(base.as_bytes());
                    base
                });
                self.trivia(Slot::Any);
                self.out.push(b'{');
                let body = self.statements(body);
                self.out.push(b'}');
                self.trivia(Slot::Any);
                self.out.push(b';');
                Skel::Class(name, base, body)
            }
            Stmt::Value { name, lexeme } => {
                let name = self.unique(name);
                self.out.extend_from_slice(name.as_bytes());
                self.trivia(Slot::Any);
                self.out.push(b'=');
                self.trivia(Slot::Any);
                self.out.extend_from_slice(lexeme);
                let quoted = lexeme.first() == Some(&b'"');
                self.trivia(if quoted {
                    Slot::RemovedOnly
                } else {
                    Slot::SameLine
                });
                self.out.push(b';');
                Skel::Value(name, lexeme.clone())
            }
            Stmt::Array { name, items } => {
                let name = self.unique(name);
                self.out.extend_from_slice(name.as_bytes());
                self.trivia(Slot::RemovedOnly);
                self.out.push(b'[');
                self.trivia(Slot::Any);
                self.out.push(b']');
                self.trivia(Slot::Any);
                self.out.push(b'=');
                let items = self.literal(items);
                self.trivia(Slot::Any);
                self.out.push(b';');
                Skel::Array(name, items)
            }
            Stmt::Enum { name, items } => {
                let name = self.unique(name);
                self.out.extend_from_slice(b"enum");
                self.trivia(Slot::Separating);
                self.out.extend_from_slice(name.as_bytes());
                self.trivia(Slot::Any);
                self.out.push(b'{');
                let mut names = Vec::new();
                for (index, item) in items.iter().enumerate() {
                    if index > 0 {
                        self.trivia(Slot::Any);
                        self.out.push(b',');
                    }
                    self.trivia(Slot::Any);
                    let item = self.unique(item);
                    self.out.extend_from_slice(item.as_bytes());
                    names.push(item);
                }
                self.trivia(Slot::Any);
                self.out.push(b'}');
                self.trivia(Slot::Any);
                self.out.push(b';');
                Skel::Enum(name, names)
            }
            Stmt::Exec { text } => {
                self.out.extend_from_slice(b"__EXEC");
                self.trivia(Slot::Any);
                self.out.push(b'(');
                self.out.extend_from_slice(text);
                self.out.push(b')');
                self.trivia(Slot::Any);
                self.out.push(b';');
                Skel::Exec(text.clone())
            }
        }
    }

    fn literal(&mut self, items: &[Item]) -> Vec<SkelItem> {
        self.trivia(Slot::Any);
        self.out.push(b'{');
        let mut skel = Vec::new();
        for (index, item) in items.iter().enumerate() {
            if index > 0 {
                let separator = if self.seed().is_multiple_of(4) {
                    b';'
                } else {
                    b','
                };
                self.out.push(separator);
            }
            self.trivia(Slot::Any);
            match item {
                Item::Value(lexeme) => {
                    self.out.extend_from_slice(lexeme);
                    let quoted = lexeme.first() == Some(&b'"');
                    self.trivia(if quoted { Slot::Any } else { Slot::SameLine });
                    skel.push(SkelItem::Value(lexeme.clone()));
                }
                Item::Array(inner) => {
                    skel.push(SkelItem::Array(self.literal(inner)));
                    self.trivia(Slot::Any);
                }
            }
        }
        self.out.push(b'}');
        skel
    }

    pub fn names(&self) -> &[String] {
        &self.names
    }
}

// ── Skeleton of a parsed tree ────────────────────────────────────────────────────────────────────────────────────

/// The skeleton of a parsed tree: every statement node of the file, as the game reads it.
pub fn skeleton(cst: &ConfigCst) -> Vec<Skel> {
    body_skeleton(cst.root())
}

fn text(bytes: Vec<u8>) -> String {
    String::from_utf8_lossy(&bytes).into_owned()
}

fn body_skeleton(body: plotroom_config::cst::cursor::CstNode<'_>) -> Vec<Skel> {
    let mut out = Vec::new();
    for node in body.child_nodes() {
        let name = || {
            node.child_node(NodeKind::Name)
                .map(|n| text(n.visible_bytes()))
                .unwrap_or_default()
        };
        match node.kind() {
            NodeKind::ClassDecl => {
                let names: Vec<String> = node
                    .child_nodes()
                    .filter(|n| n.kind() == NodeKind::Name)
                    .map(|n| text(n.visible_bytes()))
                    .collect();
                let base = names.get(1).cloned();
                let body = node
                    .child_node(NodeKind::ClassBody)
                    .map(body_skeleton)
                    .unwrap_or_default();
                out.push(Skel::Class(name(), base, body));
            }
            NodeKind::ValueEntry => {
                let lexeme = node
                    .child_node(NodeKind::Value)
                    .map(|v| v.visible_bytes())
                    .unwrap_or_default();
                out.push(Skel::Value(name(), lexeme));
            }
            NodeKind::ArrayEntry => {
                let items = node
                    .child_node(NodeKind::ArrayLiteral)
                    .map(literal_skeleton)
                    .unwrap_or_default();
                out.push(Skel::Array(name(), items));
            }
            NodeKind::EnumDecl => {
                let items = node
                    .child_nodes()
                    .filter(|n| n.kind() == NodeKind::EnumItem)
                    .filter_map(|item| {
                        item.child_node(NodeKind::Name)
                            .map(|n| text(n.visible_bytes()))
                    })
                    .collect();
                out.push(Skel::Enum(name(), items));
            }
            NodeKind::ExecStmt => {
                out.push(Skel::Exec(
                    node.child_node(NodeKind::Value)
                        .map(|v| v.visible_bytes())
                        .unwrap_or_default(),
                ));
            }
            _ => {}
        }
    }
    out
}

fn literal_skeleton(literal: plotroom_config::cst::cursor::CstNode<'_>) -> Vec<SkelItem> {
    literal
        .child_nodes()
        .filter_map(|node| match node.kind() {
            NodeKind::Element => Some(SkelItem::Value(
                node.child_node(NodeKind::Value)
                    .map(|v| v.visible_bytes())
                    .unwrap_or_default(),
            )),
            NodeKind::ArrayLiteral => Some(SkelItem::Array(literal_skeleton(node))),
            _ => None,
        })
        .collect()
}

/// Paths (class names, then the value name) of every value entry in a skeleton.
pub fn value_paths(skel: &[Skel]) -> Vec<Vec<String>> {
    let mut out = Vec::new();
    collect_value_paths(skel, &mut Vec::new(), &mut out);
    out
}

fn collect_value_paths(skel: &[Skel], prefix: &mut Vec<String>, out: &mut Vec<Vec<String>>) {
    for statement in skel {
        match statement {
            Skel::Value(name, _) => {
                let mut path = prefix.clone();
                path.push(name.clone());
                out.push(path);
            }
            Skel::Class(name, _, body) => {
                prefix.push(name.clone());
                collect_value_paths(body, prefix, out);
                prefix.pop();
            }
            _ => {}
        }
    }
}
