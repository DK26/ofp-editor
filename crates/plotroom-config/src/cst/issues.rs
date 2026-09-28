// SPDX-License-Identifier: GPL-3.0-or-later
//! Syntax issues derived from the tree: [`lint_syntax`], [`SyntaxIssue`], [`IssueKind`] and [`EngineEffect`].
//!
//! **What it owns.** A pure walk that reports what the game will do with text it does not read as intended: where
//! its parser stops, which bytes it drops, what it truncates, which file it rejects. Issues are derived from the tree
//! each time (never stored beside it), so they stay correct after a patch.
//!
//! **How messages are written.** Each message names the fix first and the game's reaction second, for the editor's
//! problem list and for Wilco (the product's agent), which receives [`IssueKind`] values, not these strings. Codes
//! map to the shared `DiagCode` registry once DG005 is decided (placeholder: the kinds are this crate's own for now).
//!
//! **Allocation profile.** One `Vec` of issues, plus the name lists used to find duplicates in each body.

use crate::ConfigCst;
use crate::cst::cursor::{CstElement, CstNode};
use crate::cst::entries::{added_statements, unquote};
use crate::cst::kinds::{DirectiveKind, NodeKind, StopReason, TokenKind};
use crate::text::{TextOffset, TextSpan, TextWidth};

/// The longest value the game keeps: `WordBuf` is 2048 bytes with a terminating NUL
/// (`CWR:engine/Poseidon/IO/ParamFile/ParamFilePrivate.inc#L10`, `#L52-L55`; engine request ER-050).
pub const MAX_ENGINE_VALUE_BYTES: usize = 2047;

/// The longest name the game keeps as written: names are read into the same 2048-byte `WordBuf`
/// (`ParamFilePrivate.inc#L10`, `#L109-L127`), so longer names are not kept intact.
pub const MAX_ENGINE_NAME_BYTES: usize = 2047;

/// What the game does because of an issue.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum EngineEffect {
    /// The game stops reading the file here; nothing after this point is defined.
    RootStops,
    /// The statement is dropped and the rest of its class is read as part of the parent class.
    ClassAbandoned,
    /// The array literal ends here; the entry survives only if a `;` follows.
    ArrayCutShort,
    /// This entry is dropped; the rest of the file is read normally.
    EntryDropped,
    /// Some bytes are silently thrown away.
    BytesDropped,
    /// The game refuses to load the whole file.
    FileRejected,
    /// The game keeps only the first part of the value or name.
    Truncated,
    /// The game logs an error but keeps reading as if nothing happened.
    ErrorMessageOnly,
    /// The game accepts it without any message.
    AcceptedSilently,
}

/// The kind of a syntax issue. Stop kinds refine a [`StopReason`] when the pattern is recognisable.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum IssueKind {
    /// The game's parser stopped (see [`StopReason`]).
    Stopped(StopReason),
    /// `class X;`: forward declarations do not exist in this format.
    ForwardClassDeclaration,
    /// `Class X {}`: keywords are case-sensitive.
    KeywordCase,
    /// `delete X;`: this format has no `delete` statement.
    DeleteStatement,
    /// `a [] = {}`: the `[` must follow the name directly.
    SpaceBeforeArrayBrackets,
    /// `a[][] = ...`: only one pair of brackets is allowed.
    MultiDimArrayName,
    /// `x = "a" ;`: whitespace between a quoted value and its terminator.
    TriviaAfterQuotedValue,
    /// A class whose closing `}` never comes (the input ends first).
    MissingCloseBraceAtEof,
    /// A `}` at the top level, which ends the file for the game.
    CloseBraceAtRoot,
    /// Text after the point where the game stopped reading the file.
    InputAfterRootEnd,
    /// A second entry with the same name (case-insensitive) in one class.
    DuplicateMember,
    /// A quoted string that never closes.
    UnterminatedString,
    /// A line break inside a quoted string.
    NewlineInQuotedString,
    /// A `/*` comment that never closes.
    UnterminatedBlockComment,
    /// A byte after a line break inside an array element, which the game drops.
    JunkAfterElement,
    /// A NUL byte, which the preprocessor drops.
    NulByte,
    /// A UTF-8 byte-order mark at the start, which the game reads as a stray byte.
    Utf8Bom,
    /// A `#` line the preprocessor does not know (for example `#if`).
    UnknownDirective,
    /// A value longer than [`MAX_ENGINE_VALUE_BYTES`].
    ValueTooLong,
    /// A name longer than [`MAX_ENGINE_NAME_BYTES`].
    NameTooLong,
}

impl IssueKind {
    /// A one-sentence message: the fix first, then what the game does.
    #[must_use]
    pub const fn message(self) -> &'static str {
        match self {
            IssueKind::Stopped(reason) => stop_message(reason),
            IssueKind::ForwardClassDeclaration => {
                "remove `class X;` or give it a body `class X {};`: forward declarations do not exist and the game stops reading this class here"
            }
            IssueKind::KeywordCase => {
                "write the keyword in lowercase (`class`, `enum`) or `__EXEC`: the game reads a differently cased keyword as a value name and stops"
            }
            IssueKind::DeleteStatement => {
                "remove `delete`: this format has no delete statement (override with an empty array instead); the game stops reading this class here"
            }
            IssueKind::SpaceBeforeArrayBrackets => {
                "remove the space before `[]`: the game needs `name[]` together and stops reading this class here"
            }
            IssueKind::MultiDimArrayName => {
                "use one pair of brackets, `name[] = {{1,2},{3,4}};`: the game stops reading this class at the second `[`"
            }
            IssueKind::TriviaAfterQuotedValue => {
                "remove the whitespace between the closing quote and `;`: the game drops this entry and ignores the rest of the class"
            }
            IssueKind::MissingCloseBraceAtEof => {
                "add the missing `}`: the game accepts the file but the class runs to the end"
            }
            IssueKind::CloseBraceAtRoot => {
                "remove the extra `}`: the game stops reading the file at it"
            }
            IssueKind::InputAfterRootEnd => {
                "fix the issue that ended the file earlier: the game never reads this text"
            }
            IssueKind::DuplicateMember => {
                "rename or remove the second entry: the game keeps the first one and drops this one"
            }
            IssueKind::UnterminatedString => {
                "close the string with `\"`: the game reads to the end of the file"
            }
            IssueKind::NewlineInQuotedString => {
                "remove the line break from the string: the game reports an error but keeps the line break"
            }
            IssueKind::UnterminatedBlockComment => {
                "close the comment with `*/`: everything after it is ignored"
            }
            IssueKind::JunkAfterElement => {
                "put a `,` between the elements: the game drops the byte after the line break"
            }
            IssueKind::NulByte => "remove the NUL byte: the game's preprocessor drops it",
            IssueKind::Utf8Bom => {
                "save the file without a byte-order mark: the game reads it as a stray byte and ignores the whole file"
            }
            IssueKind::UnknownDirective => {
                "remove or fix the `#` line (only include, define, ifdef, ifndef, else, endif and undef exist): the game refuses the whole file"
            }
            IssueKind::ValueTooLong => {
                "shorten the value to 2047 bytes or less: the game silently keeps only the first 2047"
            }
            IssueKind::NameTooLong => {
                "shorten the name to 2047 bytes or less: the game does not keep longer names intact"
            }
        }
    }
}

/// The message for a stop without a more specific pattern.
const fn stop_message(reason: StopReason) -> &'static str {
    match reason {
        StopReason::ExpectedOpenBrace => {
            "add `{` after the class or enum header: the game stops reading here"
        }
        StopReason::ExpectedEnumSeparator => {
            "separate enum items with `,` and give no values (`enum {A, B}`): the game stops reading at an enum value"
        }
        StopReason::ExpectedOpenParen => {
            "write `__EXEC(...)` with its parentheses: the game stops reading here"
        }
        StopReason::ExpectedCloseParen => "close `__EXEC(` with `)`: the game stops reading here",
        StopReason::ExpectedCloseBracket => {
            "write `name[]` with nothing between the brackets: the game stops reading here"
        }
        StopReason::ExpectedEqualsAfterBrackets => {
            "put `=` after `name[]`: the game stops reading here"
        }
        StopReason::ExpectedSemicolonAfterArray => {
            "end the array with `;` (a line break is not enough): the game drops it and stops reading here"
        }
        StopReason::ExpectedEquals => {
            "put `=` after the name (or `[]=` for an array): the game stops reading here"
        }
        StopReason::ExpectedTerminator => {
            "end the value with `;`: the game drops it and stops reading here"
        }
        StopReason::MissingTerminatorAtEof => "end the last value with `;`: the game drops it",
        StopReason::ArrayExpectedOpenBrace => {
            "start the array value with `{`: the game drops the array"
        }
        StopReason::ArrayEndOfInput => {
            "close the array with `};`: the file ends inside it and the game drops it"
        }
        StopReason::ArrayExpectedSeparator => {
            "separate array elements with `,`: the game ends the array here and usually drops the entry"
        }
    }
}

/// One issue: its kind, where it is, and what the game does.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SyntaxIssue {
    kind: IssueKind,
    span: TextSpan,
    effect: EngineEffect,
}

impl SyntaxIssue {
    /// The issue's kind.
    #[must_use]
    pub fn kind(self) -> IssueKind {
        self.kind
    }

    /// The bytes the issue is about.
    #[must_use]
    pub fn span(self) -> TextSpan {
        self.span
    }

    /// What the game does because of it (the same kind can have a different effect in a class and at the top).
    #[must_use]
    pub fn effect(self) -> EngineEffect {
        self.effect
    }

    /// The fix and the game's reaction, in one sentence (for people; models get [`SyntaxIssue::kind`]).
    #[must_use]
    pub fn message(self) -> &'static str {
        self.kind.message()
    }
}

/// Lists the syntax issues of a tree, in text order of their statements.
///
/// Pure and deterministic; an empty list means the game reads every statement as written.
#[must_use]
pub fn lint_syntax(cst: &ConfigCst) -> Vec<SyntaxIssue> {
    let mut out = Vec::new();
    // The first three bytes of the text, which the parser may have split across tokens.
    let head: Vec<u8> = cst
        .root()
        .tokens()
        .iter()
        .flat_map(|token| token.bytes().iter().copied())
        .take(3)
        .collect();
    if head == [0xEF, 0xBB, 0xBF] {
        let span = TextSpan::at(TextOffset::from_raw(0), TextWidth::from_raw(3))
            .unwrap_or(TextSpan::empty_at(TextOffset::from_raw(0)));
        out.push(SyntaxIssue {
            kind: IssueKind::Utf8Bom,
            span,
            effect: EngineEffect::RootStops,
        });
    }
    walk(cst.root(), Context::Root, &mut out);
    out
}

/// Where a node sits, which decides the effect of a stop.
#[derive(Clone, Copy, PartialEq, Eq)]
enum Context {
    Root,
    Class,
}

/// Walks one node and its children.
fn walk(node: CstNode<'_>, context: Context, out: &mut Vec<SyntaxIssue>) {
    match node.kind() {
        NodeKind::File | NodeKind::ClassBody => body_issues(node, out),
        NodeKind::ClassDecl => class_issues(node, out),
        NodeKind::Value => value_issues(node, out),
        NodeKind::Name => name_issues(node, out),
        NodeKind::Unparsed => {
            push(
                out,
                IssueKind::InputAfterRootEnd,
                node.span(),
                EngineEffect::BytesDropped,
            );
        }
        _ => {}
    }
    let child_context = if node.kind() == NodeKind::ClassBody {
        Context::Class
    } else {
        context
    };
    for child in node.children() {
        match child {
            CstElement::Node(inner) => walk(inner, child_context, out),
            CstElement::Token(token) => token_issue(
                node,
                token.kind(),
                token.bytes(),
                token.span(),
                context,
                out,
            ),
        }
    }
}

fn push(out: &mut Vec<SyntaxIssue>, kind: IssueKind, span: TextSpan, effect: EngineEffect) {
    out.push(SyntaxIssue { kind, span, effect });
}

/// Issues carried by single tokens: stops, dropped bytes, NULs, directives, comments, stray root braces.
fn token_issue(
    parent: CstNode<'_>,
    kind: TokenKind,
    bytes: &[u8],
    span: TextSpan,
    context: Context,
    out: &mut Vec<SyntaxIssue>,
) {
    match kind {
        TokenKind::Stop(reason) => {
            let effect = if reason.is_array_internal() {
                EngineEffect::ArrayCutShort
            } else if reason == StopReason::MissingTerminatorAtEof {
                EngineEffect::EntryDropped
            } else if context == Context::Root {
                EngineEffect::RootStops
            } else {
                EngineEffect::ClassAbandoned
            };
            let statement_span =
                TextSpan::new(parent.span().start(), span.end()).unwrap_or(parent.span());
            push(out, refine(parent, reason), statement_span, effect);
        }
        TokenKind::Dropped => push(
            out,
            IssueKind::JunkAfterElement,
            span,
            EngineEffect::BytesDropped,
        ),
        TokenKind::Nul => push(out, IssueKind::NulByte, span, EngineEffect::BytesDropped),
        TokenKind::Directive(DirectiveKind::Unknown) => {
            push(
                out,
                IssueKind::UnknownDirective,
                span,
                EngineEffect::FileRejected,
            );
        }
        TokenKind::BlockComment if !(bytes.len() >= 4 && bytes.ends_with(b"*/")) => {
            push(
                out,
                IssueKind::UnterminatedBlockComment,
                span,
                EngineEffect::BytesDropped,
            );
        }
        TokenKind::RBrace if parent.kind() == NodeKind::File => {
            push(
                out,
                IssueKind::CloseBraceAtRoot,
                span,
                EngineEffect::RootStops,
            );
        }
        _ => {}
    }
}

/// Picks a more specific kind for a stop when its pattern is recognisable.
fn refine(statement: CstNode<'_>, reason: StopReason) -> IssueKind {
    let unexpected: Vec<u8> = statement
        .child_tokens()
        .filter(|token| token.kind() == TokenKind::Unexpected)
        .flat_map(|token| token.bytes().iter().copied())
        .collect();
    let name = statement
        .child_node(NodeKind::Name)
        .map(CstNode::visible_bytes)
        .unwrap_or_default();
    match reason {
        StopReason::ExpectedOpenBrace
            if statement.kind() == NodeKind::ClassDecl && unexpected.first() == Some(&b';') =>
        {
            IssueKind::ForwardClassDeclaration
        }
        StopReason::ExpectedEquals => {
            if [&b"class"[..], b"enum", b"__EXEC"]
                .iter()
                .any(|keyword| keyword.eq_ignore_ascii_case(&name))
            {
                IssueKind::KeywordCase
            } else if name == b"delete" {
                IssueKind::DeleteStatement
            } else if unexpected.first() == Some(&b'[') {
                IssueKind::SpaceBeforeArrayBrackets
            } else {
                IssueKind::Stopped(reason)
            }
        }
        StopReason::ExpectedEqualsAfterBrackets if unexpected.first() == Some(&b'[') => {
            IssueKind::MultiDimArrayName
        }
        StopReason::ExpectedTerminator => {
            let quoted = statement.child_node(NodeKind::Value).is_some_and(|value| {
                value
                    .child_tokens()
                    .any(|token| token.kind() == TokenKind::QuotedString)
            });
            if quoted && matches!(unexpected.first(), Some(b' ' | b'\t' | 0x0B | 0x0C)) {
                IssueKind::TriviaAfterQuotedValue
            } else {
                IssueKind::Stopped(reason)
            }
        }
        _ => IssueKind::Stopped(reason),
    }
}

/// Duplicate names among the statements the game adds to one body.
fn body_issues(body: CstNode<'_>, out: &mut Vec<SyntaxIssue>) {
    let kept: Vec<usize> = added_statements(body)
        .into_iter()
        .map(|(index, _)| index)
        .collect();
    let mut names: Vec<Vec<u8>> = Vec::new();
    for (index, child) in body.children().enumerate() {
        let CstElement::Node(node) = child else {
            continue;
        };
        if !matches!(
            node.kind(),
            NodeKind::ClassDecl | NodeKind::ValueEntry | NodeKind::ArrayEntry
        ) {
            continue;
        }
        if node
            .child_tokens()
            .any(|token| matches!(token.kind(), TokenKind::Stop(_)))
        {
            continue;
        }
        let name = node
            .child_node(NodeKind::Name)
            .map(CstNode::visible_bytes)
            .unwrap_or_default();
        if kept.contains(&index) {
            names.push(name);
        } else if names
            .iter()
            .any(|earlier| earlier.eq_ignore_ascii_case(&name))
        {
            push(
                out,
                IssueKind::DuplicateMember,
                node.span(),
                EngineEffect::EntryDropped,
            );
        }
    }
}

/// A class whose body ended without `}` and without a stop: the input ended first.
fn class_issues(class: CstNode<'_>, out: &mut Vec<SyntaxIssue>) {
    if class.has_child_token(TokenKind::RBrace)
        || class
            .child_tokens()
            .any(|t| matches!(t.kind(), TokenKind::Stop(_)))
    {
        return;
    }
    let Some(body) = class.child_node(NodeKind::ClassBody) else {
        return;
    };
    let body_stopped = body.child_nodes().any(|statement| {
        statement.child_tokens().any(
            |token| matches!(token.kind(), TokenKind::Stop(reason) if !reason.is_array_internal()),
        )
    });
    if !body_stopped {
        let end = class.span().end();
        push(
            out,
            IssueKind::MissingCloseBraceAtEof,
            TextSpan::empty_at(end),
            EngineEffect::AcceptedSilently,
        );
    }
}

/// String issues and the length cap of one value.
fn value_issues(value: CstNode<'_>, out: &mut Vec<SyntaxIssue>) {
    let lexeme = value.visible_bytes();
    let quoted = value
        .child_tokens()
        .any(|token| token.kind() == TokenKind::QuotedString);
    let text = if quoted {
        unquote(&lexeme)
    } else {
        lexeme.clone()
    };
    if quoted {
        let quotes = lexeme.iter().filter(|byte| **byte == b'"').count();
        let terminated = lexeme.len() >= 2 && lexeme.ends_with(b"\"") && quotes.is_multiple_of(2);
        if !terminated {
            push(
                out,
                IssueKind::UnterminatedString,
                value.span(),
                EngineEffect::ErrorMessageOnly,
            );
        }
        if text.contains(&b'\n') {
            push(
                out,
                IssueKind::NewlineInQuotedString,
                value.span(),
                EngineEffect::ErrorMessageOnly,
            );
        }
    }
    if text.len() > MAX_ENGINE_VALUE_BYTES {
        push(
            out,
            IssueKind::ValueTooLong,
            value.span(),
            EngineEffect::Truncated,
        );
    }
}

/// The length cap of one name.
fn name_issues(name: CstNode<'_>, out: &mut Vec<SyntaxIssue>) {
    if name.visible_bytes().len() > MAX_ENGINE_NAME_BYTES {
        push(
            out,
            IssueKind::NameTooLong,
            name.span(),
            EngineEffect::Truncated,
        );
    }
}
