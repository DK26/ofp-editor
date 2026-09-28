// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Plotroom contributors
//! Known-value cross-validation against the engine source: what the game's reader keeps, drops and stops on.
//!
//! Each expected value is derived by hand from the cited lines of `BohemiaInteractive/CWR@ffc61838b7` (the
//! engine's config reader and preprocessor). Behaviour that cannot be confirmed for 1.99 without a probe is tagged
//! `unverified-1.99` in the test's doc comment.

use crate::cst::entries::{ArrayItem, Entry};
use crate::cst::issues::{EngineEffect, IssueKind};
use crate::cst::kinds::{StopReason, TokenKind};
use crate::scalar::Scalar;
use crate::{ConfigCst, lint_syntax, parse};

fn parsed(text: &[u8]) -> ConfigCst {
    let cst = parse(text).unwrap();
    assert_eq!(cst.render(), text);
    cst
}

fn names(cst: &ConfigCst) -> Vec<String> {
    cst.entries()
        .iter()
        .map(|entry| String::from_utf8_lossy(&entry.name()).into_owned())
        .collect()
}

fn value_text(cst: &ConfigCst, path: &[&[u8]]) -> Vec<u8> {
    let Some(Entry::Value(entry)) = cst.find(path) else {
        panic!("no value at {path:?}")
    };
    entry.value().unwrap().text()
}

fn issue_kinds(cst: &ConfigCst) -> Vec<(IssueKind, EngineEffect)> {
    lint_syntax(cst)
        .iter()
        .map(|issue| (issue.kind(), issue.effect()))
        .collect()
}

fn element_count(cst: &ConfigCst, path: &[&[u8]]) -> usize {
    let Some(Entry::Array(array)) = cst.find(path) else {
        panic!("no array at {path:?}")
    };
    array.items().len()
}

// ── Known-value cross-validation: values ─────────────────────────────────────────────────────────────────────────

/// After `=`, line breaks are skipped: `x =` followed by a line break takes the next line as the value.
///
/// Why: `ParamFile.cpp#L1790-L1795` skips all whitespace after `=`, so a value on the next line is legal.
#[test]
fn value_may_start_on_the_next_line() {
    let cst = parsed(b"x =\n  5;\ny = 6;\n");
    assert_eq!(value_text(&cst, &[b"x"]), b"5");
    assert_eq!(names(&cst), ["x", "y"]);
}

/// A lone CR is removed by the preprocessor, so the two lines it separates join into one value.
///
/// Why: `Preproc.cpp#L113-L116` drops every CR; the game reads `x = 1y = 2;`.
#[test]
fn a_lone_cr_joins_lines() {
    let cst = parsed(b"x = 1\ry = 2;");
    assert_eq!(names(&cst), ["x"]);
    assert_eq!(value_text(&cst, &[b"x"]), b"1y = 2");
    let dump = cst.debug_tree();
    assert!(dump.contains("CarriageReturn'\\r'"), "{dump}");
}

/// Bare values keep inner spaces, lose trailing spaces, and end at `;` or a line break (terminator kept in the
/// entry).
///
/// Why: `ParamFilePrivate.inc#L65-L104` reads bare text to a terminator and right-trims it.
#[test]
fn bare_values_keep_inner_spaces() {
    let cst = parsed(b"e = 2 + 2 ;\nf = last\n");
    assert_eq!(value_text(&cst, &[b"e"]), b"2 + 2");
    assert_eq!(value_text(&cst, &[b"f"]), b"last");
    assert!(
        cst.debug_tree()
            .contains("Value[BareText'last'] Newline'\\n'")
    );
}

/// Scalar typing follows the engine: `1.5e2` is 150, `12.34.56` is text, `db+10` a float, quoted always text.
///
/// Why: `ParamFile.cpp#L1818-L1843` types bare values in this order (ScanInt, ScanFloat, else string).
#[test]
fn values_are_typed_like_the_engine() {
    let cst = parsed(b"a=123;b=1.5e2;c=12.34.56;d=db+10;e=\"42\";f=0x1F;g=true;");
    let scalar = |name: &[u8]| {
        let Some(Entry::Value(entry)) = cst.find(&[name]) else {
            panic!("value")
        };
        entry.value().unwrap().scalar()
    };
    assert_eq!(scalar(b"a"), Scalar::Int(123));
    assert_eq!(scalar(b"b"), Scalar::Float(150.0));
    assert_eq!(scalar(b"c"), Scalar::Text);
    assert!(matches!(scalar(b"d"), Scalar::Float(v) if (v - 3.162_277_7).abs() < 1e-5));
    assert_eq!(scalar(b"e"), Scalar::Text);
    assert_eq!(scalar(b"f"), Scalar::Int(31));
    assert_eq!(scalar(b"g"), Scalar::Text);
}

/// Names may start with a digit or be empty; keywords are case-sensitive.
///
/// Why: `GetAlphaWord` accepts `[A-Za-z0-9_]*` (`ParamFilePrivate.inc#L109-L127`); `class` is matched with `strcmp`
/// (`ParamFile.cpp#L1601`).
#[test]
fn names_are_alphanumeric_and_keywords_case_sensitive() {
    let cst = parsed(b"123invalid = 1;\n= 5;\n");
    assert_eq!(names(&cst), ["123invalid", ""]);
    let cst = parsed(b"Class X {};");
    assert!(cst.entries().is_empty());
    assert_eq!(
        issue_kinds(&cst),
        [(IssueKind::KeywordCase, EngineEffect::RootStops)]
    );
}

/// A comment inside a name joins the name, as the preprocessor removes it first.
///
/// Why: the parser reads the preprocessed text, where `na/*c*/me` is `name`.
#[test]
fn a_comment_inside_a_name_joins_it() {
    let cst = parsed(b"na/*c*/me = 1;");
    assert_eq!(names(&cst), ["name"]);
    assert!(
        cst.debug_tree()
            .contains("Name[Ident'na' BlockComment'/*c*/' Ident'me']")
    );
}

/// A `"` inside a bare value toggles the preprocessor's quote state, so a later `//` is not a comment.
///
/// Why: `Preproc.cpp#L300-L303` toggles on every `"` outside comments, whatever the parser thinks of it.
#[test]
fn a_quote_in_a_bare_value_disables_later_comments() {
    let cst = parsed(b"x = a\"b; // c\ny = 1;");
    assert_eq!(names(&cst), ["x"]);
    assert_eq!(value_text(&cst, &[b"x"]), b"a\"b");
    assert!(
        !cst.root()
            .tokens()
            .iter()
            .any(|token| token.kind() == TokenKind::LineComment)
    );
}

// ── Known-value cross-validation: stops and recovery ────────────────────────────────────────────────────────────

/// Whitespace between a quoted value and `;` drops the entry and stops the enclosing body.
///
/// Why: after a quoted value the next byte must be `;` or a line break (`ParamFile.cpp#L1798-L1803`).
#[test]
fn whitespace_after_a_quoted_value_stops() {
    let cst = parsed(b"x = \"a\" ;\ny = 1;");
    assert!(cst.entries().is_empty());
    assert_eq!(
        issue_kinds(&cst)[0],
        (IssueKind::TriviaAfterQuotedValue, EngineEffect::RootStops)
    );
    assert!(cst.debug_tree().contains("Unparsed["));
}

/// After an error inside a class, the rest of the class is read by the parent: later entries land in the parent.
///
/// Why: errors `return` from the current `ParamClass::Parse` only, and the parent carries on from the same stream
/// position (`ParamFile.cpp#L1643-L1644`, `#L1768-L1772`).
#[test]
fn an_error_inside_a_class_moves_later_text_to_the_parent() {
    let cst = parsed(b"class A { a[] = {1} b = 1; };\n");
    assert_eq!(names(&cst), ["A", ""]);
    let Some(Entry::Class(a)) = cst.find(&[b"A"]) else {
        panic!("A")
    };
    assert!(!a.is_closed());
    assert!(a.entries().is_empty());
    assert_eq!(value_text(&cst, &[b""]), b"1");
    let kinds = issue_kinds(&cst);
    assert!(kinds.contains(&(
        IssueKind::Stopped(StopReason::ExpectedSemicolonAfterArray),
        EngineEffect::ClassAbandoned
    )));
    assert!(kinds.contains(&(IssueKind::CloseBraceAtRoot, EngineEffect::RootStops)));
}

/// An enum item with a value ends the enum with an error; items without values are fine.
///
/// Why: after an item's value, `c` still holds the value's first byte, so the `while (c == ',')` loop ends and the
/// `}` check fails (`ParamFile.cpp#L1663-L1701`). unverified-1.99.
#[test]
fn enum_items_with_values_stop_the_enum() {
    let cst = parsed(b"enum {A, B}; x = 1;");
    assert_eq!(names(&cst), ["x"]);
    let cst = parsed(b"enum {A = 5}; x = 1;");
    assert!(cst.entries().is_empty());
    assert_eq!(
        issue_kinds(&cst)[0],
        (
            IssueKind::Stopped(StopReason::ExpectedEnumSeparator),
            EngineEffect::RootStops
        )
    );
}

/// `class X;`, `delete X;` and `a [] = {}` stop with specific issues.
///
/// Why: none exists in this format (`ParamFile.cpp#L1632-L1641`, `#L1777-L1788`); the specific issue names the fix.
#[test]
fn unsupported_forms_get_specific_issues() {
    let cases: [(&[u8], IssueKind); 4] = [
        (b"class X;", IssueKind::ForwardClassDeclaration),
        (b"delete X;", IssueKind::DeleteStatement),
        (b"a [] = {};", IssueKind::SpaceBeforeArrayBrackets),
        (b"a[][] = {{1}};", IssueKind::MultiDimArrayName),
    ];
    for (text, kind) in cases {
        let cst = parsed(text);
        assert!(
            cst.entries().is_empty(),
            "{}",
            String::from_utf8_lossy(text)
        );
        assert_eq!(
            issue_kinds(&cst)[0].0,
            kind,
            "{}",
            String::from_utf8_lossy(text)
        );
    }
}

/// A missing `}` at the end is accepted silently; a `}` at the top ends the file.
///
/// Why: `ParamFile.cpp#L1582-L1585` returns at the end of input; a top-level `}` ends the root and the rest is
/// "input after EndOfFile" (`ParamFileParse.cpp#L904-L908`).
#[test]
fn braces_at_the_ends() {
    let cst = parsed(b"class A { x = 1;");
    assert_eq!(value_text(&cst, &[b"A", b"x"]), b"1");
    assert_eq!(
        issue_kinds(&cst),
        [(
            IssueKind::MissingCloseBraceAtEof,
            EngineEffect::AcceptedSilently
        )]
    );
    let cst = parsed(b"x = 1; }; y = 2;");
    assert_eq!(names(&cst), ["x"]);
    let kinds = issue_kinds(&cst);
    assert!(kinds.contains(&(IssueKind::CloseBraceAtRoot, EngineEffect::RootStops)));
    assert!(kinds.contains(&(IssueKind::InputAfterRootEnd, EngineEffect::BytesDropped)));
}

/// The first of two equal names (case-insensitive) wins.
///
/// Why: "Member already defined" (`ParamFile.cpp#L1849-L1866`); names compare with `strcmpi`.
#[test]
fn the_first_duplicate_wins() {
    let cst = parsed(b"x = 1; X = 2;");
    assert_eq!(names(&cst), ["x"]);
    assert_eq!(value_text(&cst, &[b"x"]), b"1");
    assert_eq!(
        issue_kinds(&cst),
        [(IssueKind::DuplicateMember, EngineEffect::EntryDropped)]
    );
}

/// A value at the end of input without a terminator is dropped.
///
/// Why: `ParamFile.cpp#L1798-L1803` requires `;` or a line break; end of input is neither.
#[test]
fn a_value_without_terminator_at_the_end_is_dropped() {
    let cst = parsed(b"value = 123");
    assert!(cst.entries().is_empty());
    assert_eq!(
        issue_kinds(&cst),
        [(
            IssueKind::Stopped(StopReason::MissingTerminatorAtEof),
            EngineEffect::EntryDropped
        )]
    );
}

// ── Known-value cross-validation: arrays ─────────────────────────────────────────────────────────────────────────

/// Array element counts: a trailing comma adds nothing, an empty element between commas is kept, `;` separates.
///
/// Why: `ParamFileParse.cpp#L462-L500` adds an element when the next byte is `,` or `;` or a word was read.
#[test]
fn array_element_counts_follow_the_engine() {
    let cst = parsed(b"a[] = {1, 2, 3,};\nb[] = {1,,2};\nc[] = {};\nd[] = {1; 2};\ne[] = {\"\"};\nm[] = {{1,2},{3,4}};\n");
    assert_eq!(element_count(&cst, &[b"a"]), 3);
    assert_eq!(element_count(&cst, &[b"b"]), 3);
    assert_eq!(element_count(&cst, &[b"c"]), 0);
    assert_eq!(element_count(&cst, &[b"d"]), 2);
    assert_eq!(element_count(&cst, &[b"e"]), 1);
    assert_eq!(element_count(&cst, &[b"m"]), 2);
    let Some(Entry::Array(b)) = cst.find(&[b"b"]) else {
        panic!("b")
    };
    let ArrayItem::Value(middle) = b.items()[1] else {
        panic!("value")
    };
    assert_eq!(middle.text(), b"");
    assert!(lint_syntax(&cst).is_empty());
}

/// A bare element ends at a line break; a non-separator byte after it is dropped.
///
/// Why: `ParamFilePrivate.inc#L67-L87` consumes and discards that byte (with only a log message).
#[test]
fn a_byte_after_a_line_break_in_an_element_is_dropped() {
    let cst = parsed(b"a[] = {1\n2, 3};");
    assert_eq!(element_count(&cst, &[b"a"]), 2);
    assert!(cst.debug_tree().contains("Dropped'2'"));
    assert_eq!(
        issue_kinds(&cst),
        [(IssueKind::JunkAfterElement, EngineEffect::BytesDropped)]
    );
}

/// An array needs `;` after its literal; a line break is not enough.
///
/// Why: `ParamFile.cpp#L1763-L1772`.
#[test]
fn an_array_needs_a_semicolon() {
    let cst = parsed(b"a[] = {1}\nb = 2;");
    assert!(cst.entries().is_empty());
    assert_eq!(
        issue_kinds(&cst)[0].0,
        IssueKind::Stopped(StopReason::ExpectedSemicolonAfterArray)
    );
}

// ── Known-value cross-validation: preprocessor bytes ────────────────────────────────────────────────────────────

/// NUL bytes are removed; a UTF-8 BOM makes the game read nothing.
///
/// Why: the preprocessor drops NUL (`Preproc.cpp#L135-L136`) but passes 0xEF through, and `GetAlphaWord` then reads
/// an empty name followed by a stray byte, which stops the root. unverified-1.99 (runtime effect).
#[test]
fn nul_and_bom() {
    let cst = parsed(b"x = 1\x00;");
    assert_eq!(value_text(&cst, &[b"x"]), b"1");
    assert_eq!(
        issue_kinds(&cst),
        [(IssueKind::NulByte, EngineEffect::BytesDropped)]
    );
    let cst = parsed(b"\xEF\xBB\xBFx = 1;");
    assert!(cst.entries().is_empty());
    let kinds = issue_kinds(&cst);
    assert_eq!(kinds[0], (IssueKind::Utf8Bom, EngineEffect::RootStops));
    assert!(kinds.contains(&(
        IssueKind::Stopped(StopReason::ExpectedEquals),
        EngineEffect::RootStops
    )));
}

/// Unknown directives make the game refuse the file; `#` in the middle of a line is not a directive.
///
/// Why: `Preproc.cpp#L363-L367` (`prInvalidPreprocessorCommand`); directives start only after a line break.
#[test]
fn directive_rules() {
    let cst = parsed(b"#if 0\nx = 1;\n");
    assert_eq!(
        issue_kinds(&cst),
        [(IssueKind::UnknownDirective, EngineEffect::FileRejected)]
    );
    let cst = parsed(b"x = 1; #define A\n");
    assert_eq!(names(&cst), ["x"]);
    assert!(
        !cst.root()
            .tokens()
            .iter()
            .any(|token| matches!(token.kind(), TokenKind::Directive(_)))
    );
    let cst = parsed(b"  \t#define A 1\r\nx = A;\r\n");
    assert_eq!(value_text(&cst, &[b"x"]), b"A");
    assert!(
        cst.debug_tree()
            .contains("Directive(Define)'#define A 1' Newline'\\r\\n'")
    );
}

/// Strings and comments that never close, and line breaks inside strings, are reported.
///
/// Why: the game logs them (`ParamFilePrivate.inc#L32-L51`); a never-closed comment hides the rest of the file.
#[test]
fn unterminated_strings_and_comments() {
    let cst = parsed(b"text = \"abc");
    let kinds: Vec<IssueKind> = issue_kinds(&cst)
        .into_iter()
        .map(|(kind, _)| kind)
        .collect();
    assert!(kinds.contains(&IssueKind::UnterminatedString));
    assert!(kinds.contains(&IssueKind::Stopped(StopReason::MissingTerminatorAtEof)));
    let cst = parsed(b"x = 1; /* open");
    assert_eq!(names(&cst), ["x"]);
    assert_eq!(
        issue_kinds(&cst),
        [(
            IssueKind::UnterminatedBlockComment,
            EngineEffect::BytesDropped
        )]
    );
    let cst = parsed(b"t = \"a\nb\";");
    assert_eq!(value_text(&cst, &[b"t"]), b"a\nb");
    assert_eq!(
        issue_kinds(&cst),
        [(
            IssueKind::NewlineInQuotedString,
            EngineEffect::ErrorMessageOnly
        )]
    );
}

/// `__EXEC` and `enum` statements are read but are not entries; the class after them is.
///
/// Why: `ParamFile.cpp#L1646-L1733` handles them without adding an entry.
#[test]
fn exec_and_enum_are_not_entries() {
    let cst = parsed(b"__EXEC(_x = 1);\nenum {E1, E2};\nclass C {};");
    assert_eq!(names(&cst), ["C"]);
    assert!(lint_syntax(&cst).is_empty());
}
