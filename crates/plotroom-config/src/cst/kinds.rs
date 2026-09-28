// SPDX-License-Identifier: GPL-3.0-or-later
//! The vocabulary of the tree: [`NodeKind`], [`TokenKind`], [`DirectiveKind`] and [`StopReason`].
//!
//! **What it owns.** The kinds every node and token of a [`crate::ConfigCst`] carries. A node kind names a piece of
//! syntax (a class, an entry, a value); a token kind names what its bytes are to the game.
//!
//! **Three families of token.** *Syntax* tokens are bytes the game's parser reads as part of a statement. *Trivia*
//! tokens are bytes the game skips: whitespace and line breaks the parser skips itself, and bytes its preprocessor
//! removes before the parser runs (comments, directive lines, CR and NUL bytes). *Engine-consumed* tokens are bytes
//! the parser reads and then ignores or stops on ([`TokenKind::Dropped`], [`TokenKind::Unexpected`],
//! [`TokenKind::Opaque`]). Zero-width [`TokenKind::Stop`] markers record where the game's parser gave up on a
//! statement, so the tree states which statements the game keeps.

/// The kind of a node. Nodes group tokens and other nodes; a node's width is the sum of its children's widths.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum NodeKind {
    /// The whole file. Its children are statements and trivia, like a class body.
    File,
    /// `class Name [: Base] { ... }` with any `;` after the closing brace.
    ClassDecl,
    /// The statements between a class's braces.
    ClassBody,
    /// A name: an entry, class, base or enum item name. Its visible bytes are the name the game reads.
    Name,
    /// `name = value;` (the terminator is `;` or a line break).
    ValueEntry,
    /// A value's lexeme: a quoted string or bare text, possibly split by bytes the preprocessor removes.
    Value,
    /// `name[] = { ... };`
    ArrayEntry,
    /// `{ ... }`: an array literal or a nested sub-array.
    ArrayLiteral,
    /// One element of an array literal: a [`NodeKind::Value`] and any byte the game drops after it.
    Element,
    /// `enum [Name] { A, B = 5 }` (the game evaluates the values; the tree keeps their text).
    EnumDecl,
    /// One item of an enum, with the comma that follows it.
    EnumItem,
    /// `__EXEC(...)` (the game runs the text; the tree keeps it as a value).
    ExecStmt,
    /// Input the game never reads, because its parser ended the root before it.
    Unparsed,
}

/// The kind of a preprocessor directive line (`#include`, `#define`, ...).
///
/// Directives are trivia in this tree: `plotroom-preproc` (a later crate) resolves includes and macros. The kind
/// is recorded so lints can say what a line is; `Unknown` is a line the game's preprocessor rejects, which makes the
/// game refuse the whole file (`CWR:engine/Poseidon/IO/PreprocC/Preproc.cpp#L363-L367`).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum DirectiveKind {
    /// `#include "file"` or `#include <file>`.
    Include,
    /// `#define NAME text`, with backslash-newline continuations.
    Define,
    /// `#ifdef NAME`.
    IfDef,
    /// `#ifndef NAME`.
    IfNDef,
    /// `#else`.
    Else,
    /// `#endif`.
    EndIf,
    /// `#undef NAME`.
    Undef,
    /// Any other word after `#` at the start of a line (for example `#if`, which this preprocessor does not have).
    Unknown,
}

/// Why the game's parser stopped reading a statement.
///
/// A [`TokenKind::Stop`] marker with one of these reasons sits right after the bytes the parser consumed before
/// it gave up. The engine then returns from the class it was reading: the statement is not added, the rest of that
/// class is not read as part of it, and the parent class carries on from the same position (for the file itself,
/// reading ends). Array-literal reasons are the exception: the array parser stops, and the entry's own `;` check
/// decides whether the array is kept. Citations are to `BohemiaInteractive/CWR@ffc61838b7`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum StopReason {
    /// A class or enum header is followed by something other than `{` (`ParamFile.cpp#L1633-L1641`, `#L1654-L1662`).
    ExpectedOpenBrace,
    /// An enum item is followed by something other than `,` or `}` (`ParamFile.cpp#L1687-L1701`).
    ExpectedEnumSeparator,
    /// `__EXEC` is not followed by `(` (`ParamFile.cpp#L1707-L1715`).
    ExpectedOpenParen,
    /// `__EXEC(` text is not followed by `)` (`ParamFile.cpp#L1716-L1731`).
    ExpectedCloseParen,
    /// `name[` is followed by something other than `]` (`ParamFile.cpp#L1747-L1751`).
    ExpectedCloseBracket,
    /// `name[]` is followed by something other than `=` (`ParamFile.cpp#L1757-L1761`).
    ExpectedEqualsAfterBrackets,
    /// An array literal is followed by something other than `;` (`ParamFile.cpp#L1763-L1772`).
    ExpectedSemicolonAfterArray,
    /// A name is followed by something other than `=` or `[` (`ParamFile.cpp#L1777-L1788`).
    ExpectedEquals,
    /// A value is followed by a byte other than `;` or a line break (`ParamFile.cpp#L1797-L1803`).
    ExpectedTerminator,
    /// A value reaches the end of the input without a terminator (the same check, with end of input).
    MissingTerminatorAtEof,
    /// An array literal does not start with `{` (`ParamFileParse.cpp#L439-L443`).
    ArrayExpectedOpenBrace,
    /// The input ends inside an array literal (`ParamFileParse.cpp#L502-L506`).
    ArrayEndOfInput,
    /// An array element is followed by something other than `,`, `;` or `}` (`ParamFileParse.cpp#L515-L520`).
    ArrayExpectedSeparator,
}

impl StopReason {
    /// True for the reasons raised inside an array literal (they stop the array, not the class).
    #[must_use]
    pub const fn is_array_internal(self) -> bool {
        matches!(
            self,
            StopReason::ArrayExpectedOpenBrace
                | StopReason::ArrayEndOfInput
                | StopReason::ArrayExpectedSeparator
        )
    }
}

/// The kind of a token. A token owns its exact bytes; concatenating every token in order gives the input back.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum TokenKind {
    // ── Syntax ──
    /// The keyword `class` (matched case-sensitively, as the game does).
    KwClass,
    /// The keyword `enum`.
    KwEnum,
    /// The keyword `__EXEC`.
    KwExec,
    /// Name characters `[A-Za-z0-9_]` (inside a [`NodeKind::Name`]).
    Ident,
    /// `{`
    LBrace,
    /// `}`
    RBrace,
    /// `[`
    LBracket,
    /// `]`
    RBracket,
    /// `:`
    Colon,
    /// `=`
    Eq,
    /// `;` (a terminator or an array separator).
    Semi,
    /// `,`
    Comma,
    /// `(`
    LParen,
    /// `)`
    RParen,
    /// A quoted string, quotes included (inside a [`NodeKind::Value`]); `""` stands for one `"`.
    QuotedString,
    /// An unquoted value or element (inside a [`NodeKind::Value`]); may contain inner spaces.
    BareText,
    // ── Trivia the parser skips ──
    /// Spaces, tabs, vertical tabs and form feeds.
    Whitespace,
    /// A line break: LF, or CR LF (the game's preprocessor drops the CR).
    Newline,
    // ── Trivia the preprocessor removes ──
    /// `// ...` up to (not including) the line break.
    LineComment,
    /// `/* ... */` (or up to the end of the input when unterminated).
    BlockComment,
    /// A whole preprocessor directive line (with continuations for `#define`).
    Directive(DirectiveKind),
    /// A CR byte that is not part of a CR LF line break; the preprocessor drops it wherever it is.
    CarriageReturn,
    /// A NUL byte; the preprocessor drops it.
    Nul,
    /// A control byte (below 0x20, other than whitespace) at the start of a line, which the preprocessor drops.
    LineStartControl,
    // ── Engine-consumed ──
    /// A byte the game reads after a line break inside an array element and throws away
    /// (`CWR:engine/Poseidon/IO/ParamFile/ParamFilePrivate.inc#L67-L87`).
    Dropped,
    /// Bytes the parser read where syntax was expected, just before it stopped.
    Unexpected,
    /// Input after the end of the root, which the game never reads.
    Opaque,
    /// Zero width: the game's parser stopped here.
    Stop(StopReason),
}

impl TokenKind {
    /// True for tokens the game's parser never sees as part of a statement (whitespace, line breaks and every
    /// byte the preprocessor removes).
    #[must_use]
    pub const fn is_trivia(self) -> bool {
        matches!(
            self,
            TokenKind::Whitespace
                | TokenKind::Newline
                | TokenKind::LineComment
                | TokenKind::BlockComment
                | TokenKind::Directive(_)
                | TokenKind::CarriageReturn
                | TokenKind::Nul
                | TokenKind::LineStartControl
        )
    }

    /// True for trivia the preprocessor removes before the parser runs (so it is invisible even inside a lexeme).
    #[must_use]
    pub const fn is_removed_by_preprocessor(self) -> bool {
        matches!(
            self,
            TokenKind::LineComment
                | TokenKind::BlockComment
                | TokenKind::Directive(_)
                | TokenKind::CarriageReturn
                | TokenKind::Nul
                | TokenKind::LineStartControl
        )
    }
}
