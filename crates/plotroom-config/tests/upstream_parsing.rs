// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: Bohemia Interactive a.s. (original C++)
// SPDX-FileCopyrightText: 2026 Plotroom contributors (Rust translation)
// Derived-From: ofpisnotdead-com/CWR-CE@b67bf3bd62:tests/unit/engine/Poseidon/IO/ParamFile/test_paramfile_parsing.cpp
// Derived-From: BohemiaInteractive/CWR@ffc61838b7:tests/unit/engine/Poseidon/IO/ParamFile/test_paramfile_parsing.cpp
// Modified: translated to Rust and changed, 2026-09-28. Subject to the Additional Terms
// (GPLv3 section 7) from Bohemia Interactive reproduced in NOTICE.
//! Port of the upstream config-grammar tests (`test_paramfile_parsing.cpp`, CE pin; identical to CWR's except for
//! one CE-only case about file paths longer than 512 bytes, which does not apply to a pure `&[u8]` parser).
//!
//! **How the port maps.** Upstream parses a raw stream with `ParamFile::Parse(QIStream&)` and checks the resolved
//! entry tree. Here each case keeps the same input and checks the same facts on the lossless tree: the entries the
//! game keeps ([`plotroom_config::ConfigCst::find`]), their values' text and lexical type
//! ([`plotroom_config::Scalar`]), and, for error cases, the syntax issue and what the game does
//! ([`plotroom_config::lint_syntax`]).
//!
//! **Adaptations (recorded in `docs/porting/upstream-test-map.csv`).**
//! - The comment cases are read as file loads: the game preprocesses every file, so comments are trivia and
//!   `value2` exists (upstream's raw-stream test documents the opposite as a "known limitation").
//! - Cases whose upstream assertion is `REQUIRE(true)` get goldens derived from the engine source, tagged
//!   `unverified-1.99` until a probe confirms them on 1.99.
//! - Inherited lookups (`derived->FindEntry("baseValue")`) need the resolved view, a later part of this crate: those
//!   assertions are not ported yet (CSV fragment `#inheritance-lookup`, status `todo`); the base-name syntax is.

use plotroom_config::{
    ArrayItem, ConfigCst, EngineEffect, Entry, IssueKind, Scalar, StopReason, TextOffset,
    ValueView, lint_syntax, parse,
};

#[cfg(test)]
mod support {
    use super::*;

    /// Parses `text`, asserting the byte-exact round trip every case also proves.
    pub fn parsed(text: &[u8]) -> ConfigCst {
        let cst = parse(text).unwrap();
        assert_eq!(cst.render(), text);
        cst
    }

    /// The value at `path`, which must exist.
    pub fn value<'cst>(cst: &'cst ConfigCst, path: &[&[u8]]) -> ValueView<'cst> {
        match cst.find(path) {
            Some(Entry::Value(entry)) => entry.value().unwrap(),
            other => panic!("no value at {path:?}: {other:?}"),
        }
    }

    /// The top-level items of the array at `path`.
    pub fn items<'cst>(cst: &'cst ConfigCst, path: &[&[u8]]) -> Vec<ArrayItem<'cst>> {
        match cst.find(path) {
            Some(Entry::Array(entry)) => entry.items(),
            other => panic!("no array at {path:?}: {other:?}"),
        }
    }

    /// The scalar of item `index` of an array.
    pub fn item_scalar(items: &[ArrayItem<'_>], index: usize) -> Scalar {
        match items[index] {
            ArrayItem::Value(value) => value.scalar(),
            ArrayItem::Array(_) => panic!("item {index} is a sub-array"),
        }
    }

    /// The text of item `index` of an array.
    pub fn item_text(items: &[ArrayItem<'_>], index: usize) -> Vec<u8> {
        match items[index] {
            ArrayItem::Value(value) => value.text(),
            ArrayItem::Array(_) => panic!("item {index} is a sub-array"),
        }
    }

    /// The class at `path`, which must exist.
    pub fn class<'cst>(cst: &'cst ConfigCst, path: &[&[u8]]) -> plotroom_config::ClassEntry<'cst> {
        match cst.find(path) {
            Some(Entry::Class(entry)) => entry,
            other => panic!("no class at {path:?}: {other:?}"),
        }
    }

    /// The issue kinds of a tree, in order.
    pub fn kinds(cst: &ConfigCst) -> Vec<IssueKind> {
        lint_syntax(cst).iter().map(|issue| issue.kind()).collect()
    }

    /// `f32` equality within the tolerance of Catch's `Approx` default (epsilon 100 * f32::EPSILON, relative).
    pub fn approx(actual: Scalar, expected: f32) -> bool {
        matches!(actual, Scalar::Float(v) if (v - expected).abs() <= f32::EPSILON * 100.0 * expected.abs().max(1.0))
    }
}

use support::*;

// ── Basic functionality: Section 2.1, basic parsing ─────────────────────────────────────────────────────────────

/// Upstream `TEST_CASE("ParamFile - Parse simple assignments")`, `SECTION("Parse from memory stream")`.
///
/// Why: the three scalar kinds of the grammar (int, float, string) read as the engine types them.
#[test]
#[expect(
    clippy::approx_constant,
    reason = "3.14 is the upstream test's input value, not an approximation of pi"
)]
fn parse_simple_assignments() {
    let cst = parsed(b"testInt = 42;\ntestFloat = 3.14;\ntestString = \"Hello\";\n");
    assert_eq!(value(&cst, &[b"testInt"]).scalar(), Scalar::Int(42));
    assert!(approx(value(&cst, &[b"testFloat"]).scalar(), 3.14));
    assert_eq!(value(&cst, &[b"testString"]).text(), b"Hello");
}

/// Upstream `TEST_CASE("ParamFile - Parse quoted strings")`, sections "String with spaces" and "Empty string".
///
/// Why: quoted values keep inner spaces; an empty string is a value of length 0.
#[test]
fn parse_quoted_strings() {
    let cst = parsed(b"text = \"Hello World\";");
    assert_eq!(value(&cst, &[b"text"]).text(), b"Hello World");
    let cst = parsed(b"empty = \"\";");
    assert!(value(&cst, &[b"empty"]).text().is_empty());
}

/// Upstream `TEST_CASE("ParamFile - Parse string escapes")`, section "Escaped quotes" (vacuous upstream).
///
/// Why: backslash is not an escape; `\"` ends the string, the next byte is not a terminator, and the game drops the
/// entry (`ParamFilePrivate.inc#L39-L46`; `ParamFile.cpp#L1798-L1803`). Source-derived golden, unverified-1.99.
#[test]
fn parse_string_escapes_backslash_quote_ends_the_string() {
    let cst = parsed(b"text = \"He said \\\"Hello\\\"\";");
    assert!(cst.find(&[b"text"]).is_none());
    assert_eq!(
        kinds(&cst)[0],
        IssueKind::Stopped(StopReason::ExpectedTerminator)
    );
}

/// Upstream `TEST_CASE("ParamFile - Parse string escapes")`, section "Newline escape".
///
/// Why: `\n` inside quotes stays two literal bytes; the value is non-empty (the upstream assertion).
#[test]
fn parse_string_escapes_backslash_n_stays_literal() {
    let cst = parsed(b"text = \"Line1\\nLine2\";");
    let text = value(&cst, &[b"text"]).text();
    assert!(!text.is_empty());
    assert_eq!(text, b"Line1\\nLine2");
}

/// Upstream `TEST_CASE("ParamFile - Parse number formats")`, sections "Integer", "Float", "Negative number" and
/// "Scientific notation" (the last vacuous upstream).
///
/// Why: `strtod` reads `1.5e2` whole, so it is the float 150 (`ParamFile.cpp#L735-L741`); upstream's comment
/// calling it unsupported is contradicted by the source. Source-derived golden, unverified-1.99.
#[test]
#[expect(
    clippy::approx_constant,
    reason = "3.14 is the upstream test's input value, not an approximation of pi"
)]
fn parse_number_formats() {
    assert_eq!(
        value(&parsed(b"value = 123;"), &[b"value"]).scalar(),
        Scalar::Int(123)
    );
    assert!(approx(
        value(&parsed(b"value = 3.14;"), &[b"value"]).scalar(),
        3.14
    ));
    assert_eq!(
        value(&parsed(b"value = -42;"), &[b"value"]).scalar(),
        Scalar::Int(-42)
    );
    assert_eq!(
        value(&parsed(b"value = 1.5e2;"), &[b"value"]).scalar(),
        Scalar::Float(150.0)
    );
}

/// Upstream `TEST_CASE("ParamFile - Skip comments")`, sections "Single line comments" and "Multi-line comments".
///
/// Why: adapted to file-load semantics: the preprocessor removes comments, so both values exist.
#[test]
fn skip_comments() {
    let cst = parsed(b"value1 = 1; // Comment\n// Full line comment\nvalue2 = 2;\n");
    assert!(cst.find(&[b"value1"]).is_some());
    assert!(cst.find(&[b"value2"]).is_some());
    let cst = parsed(b"value1 = 1;\n/* Multi-line\n   comment */\nvalue2 = 2;\n");
    assert!(cst.find(&[b"value1"]).is_some());
    assert!(cst.find(&[b"value2"]).is_some());
}

/// Upstream `TEST_CASE("ParamFile - Parse array syntax")`, sections "Simple array" and "String array".
///
/// Why: arrays keep their element order and types.
#[test]
fn parse_array_syntax() {
    let cst = parsed(b"numbers[] = {1, 2, 3};");
    let numbers = items(&cst, &[b"numbers"]);
    assert_eq!(numbers.len(), 3);
    for (index, expected) in [1, 2, 3].into_iter().enumerate() {
        assert_eq!(item_scalar(&numbers, index), Scalar::Int(expected));
    }
    let cst = parsed(b"names[] = {\"alpha\", \"bravo\", \"charlie\"};");
    let names = items(&cst, &[b"names"]);
    assert_eq!(names.len(), 3);
    assert_eq!(item_text(&names, 0), b"alpha");
    assert_eq!(item_text(&names, 1), b"bravo");
    assert_eq!(item_text(&names, 2), b"charlie");
}

/// Upstream `TEST_CASE("ParamFile - Parse nested arrays")`, section "2D array" (vacuous upstream; its commented-out
/// assertions describe the nested literal).
///
/// Why: `matrix[][]` is refused at the second `[` (`ParamFile.cpp#L1757-L1761`); the nested literal itself works
/// with one pair of brackets and gives two sub-arrays of two items. Source-derived golden, unverified-1.99.
#[test]
fn parse_nested_arrays() {
    let cst = parsed(b"matrix[][] = {{1,2},{3,4}};");
    assert!(cst.find(&[b"matrix"]).is_none());
    assert_eq!(kinds(&cst)[0], IssueKind::MultiDimArrayName);
    let cst = parsed(b"matrix[] = {{1,2},{3,4}};");
    let rows = items(&cst, &[b"matrix"]);
    assert_eq!(rows.len(), 2);
    for (row, expected) in rows.iter().zip([[1, 2], [3, 4]]) {
        let ArrayItem::Array(row) = row else {
            panic!("row is a sub-array")
        };
        let cells = row.items();
        assert_eq!(cells.len(), 2);
        assert_eq!(item_scalar(&cells, 0), Scalar::Int(expected[0]));
        assert_eq!(item_scalar(&cells, 1), Scalar::Int(expected[1]));
    }
}

/// Upstream `TEST_CASE("ParamFile - Parse empty arrays")`, section "Empty array".
///
/// Why: upstream's known-value check with the same input (D013); the tree must give the game's reading of it.
#[test]
fn parse_empty_arrays() {
    assert!(items(&parsed(b"empty[] = {};"), &[b"empty"]).is_empty());
}

/// Upstream `TEST_CASE("ParamFile - Parse class blocks")`, section "Simple class".
///
/// Why: upstream's known-value check with the same input (D013); the tree must give the game's reading of it.
#[test]
fn parse_class_blocks() {
    let cst = parsed(b"class Test {\n    value = 42;\n};");
    assert_eq!(value(&cst, &[b"Test", b"value"]).scalar(), Scalar::Int(42));
}

/// Upstream `TEST_CASE("ParamFile - Parse nested classes")`, section "Nested class structure".
///
/// Why: upstream's known-value check with the same input (D013); the tree must give the game's reading of it.
#[test]
fn parse_nested_classes() {
    let cst = parsed(b"class Outer {\n    outerValue = 1;\n    class Inner {\n        innerValue = 2;\n    };\n};");
    assert_eq!(
        value(&cst, &[b"Outer", b"Inner", b"innerValue"]).scalar(),
        Scalar::Int(2)
    );
}

/// Upstream `TEST_CASE("ParamFile - Parse empty classes")`, section "Empty class block".
///
/// Why: upstream's known-value check with the same input (D013); the tree must give the game's reading of it.
#[test]
fn parse_empty_classes() {
    assert!(
        class(&parsed(b"class Empty {};"), &[b"Empty"])
            .entries()
            .is_empty()
    );
}

/// Upstream `TEST_CASE("ParamFile - Whitespace ignored")`, section "Extra whitespace".
///
/// Why: spaces and tabs around names, `=` and bare values are trivia (bare values are right-trimmed).
#[test]
fn whitespace_ignored() {
    let cst = parsed(b"  value1   =   123  ;  \n\tvalue2\t=\t456\t;\n    value3 = 789    ;");
    assert_eq!(value(&cst, &[b"value1"]).scalar(), Scalar::Int(123));
    assert_eq!(value(&cst, &[b"value2"]).scalar(), Scalar::Int(456));
    assert_eq!(value(&cst, &[b"value3"]).scalar(), Scalar::Int(789));
}

/// Upstream `TEST_CASE("ParamFile - Multi-line values")`, section "Array spanning multiple lines".
///
/// Why: upstream's known-value check with the same input (D013); the tree must give the game's reading of it.
#[test]
fn multi_line_values() {
    assert_eq!(
        items(
            &parsed(b"array[] = {\n    1,\n    2,\n    3\n};"),
            &[b"array"]
        )
        .len(),
        3
    );
}

/// Upstream `TEST_CASE("ParamFile - Optional trailing commas")` (vacuous upstream).
///
/// Why: a trailing comma adds no element (`ParamFileParse.cpp#L462-L468`). Source-derived golden, unverified-1.99.
#[test]
fn optional_trailing_commas() {
    let cst = parsed(b"array[] = {1, 2, 3,};");
    assert_eq!(items(&cst, &[b"array"]).len(), 3);
    assert!(lint_syntax(&cst).is_empty());
}

/// Upstream `TEST_CASE("ParamFile - Semicolon terminators")`, section "Statements with semicolons".
///
/// Why: upstream's known-value check with the same input (D013); the tree must give the game's reading of it.
#[test]
fn semicolon_terminators() {
    assert_eq!(
        parsed(b"value1 = 1;\nvalue2 = 2;\nvalue3 = 3;")
            .entries()
            .len(),
        3
    );
}

// ── Basic functionality: Section 2.2, inheritance syntax ────────────────────────────────────────────────────────

/// Upstream `TEST_CASE("ParamFile - Parse class inheritance")`, section "Simple inheritance" (syntax part).
///
/// Why: the base name is recorded and each class keeps its own entries; the inherited lookup is `#inheritance-lookup`.
#[test]
fn parse_class_inheritance_syntax() {
    let cst = parsed(b"class Base {\n    baseValue = 100;\n};\nclass Derived : Base {\n    derivedValue = 200;\n};");
    assert_eq!(class(&cst, &[b"Derived"]).base(), Some(b"Base".to_vec()));
    assert_eq!(
        value(&cst, &[b"Base", b"baseValue"]).scalar(),
        Scalar::Int(100)
    );
    assert_eq!(
        value(&cst, &[b"Derived", b"derivedValue"]).scalar(),
        Scalar::Int(200)
    );
}

/// Upstream `TEST_CASE("ParamFile - Multiple classes from same base")`, section "Multiple derived classes" (syntax).
///
/// Why: upstream's known-value check with the same input (D013); the tree must give the game's reading of it.
#[test]
fn multiple_classes_from_same_base_syntax() {
    let cst = parsed(
        b"class Base {\n    shared = 1;\n};\nclass Derived1 : Base {\n    value1 = 2;\n};\nclass Derived2 : Base {\n    value2 = 3;\n};",
    );
    for (name, own) in [(&b"Derived1"[..], &b"value1"[..]), (b"Derived2", b"value2")] {
        assert_eq!(class(&cst, &[name]).base(), Some(b"Base".to_vec()));
        assert!(cst.find(&[name, own]).is_some());
    }
}

/// Upstream `TEST_CASE("ParamFile - Base class defined later")`, `("... Error on undefined base")` and
/// `("... Detect self-inheritance")` (all vacuous upstream).
///
/// Why: the lossless tree keeps all three forms with their base names. The engine refuses a base it cannot find
/// yet (`ParamFile.cpp#L1613-L1623`: "Undefined base class", stopping the enclosing class); that verdict belongs to
/// the resolved view (`#inheritance-lookup`). unverified-1.99.
#[test]
fn forward_undefined_and_self_bases_keep_their_syntax() {
    let cst = parsed(b"class Derived : Base {\n    derivedValue = 200;\n};\nclass Base {\n    baseValue = 100;\n};");
    assert_eq!(class(&cst, &[b"Derived"]).base(), Some(b"Base".to_vec()));
    let cst = parsed(b"class Derived : NonExistentBase {\n    value = 1;\n};");
    assert_eq!(
        class(&cst, &[b"Derived"]).base(),
        Some(b"NonExistentBase".to_vec())
    );
    let cst = parsed(b"class SelfRef : SelfRef {\n    value = 1;\n};");
    assert_eq!(class(&cst, &[b"SelfRef"]).base(), Some(b"SelfRef".to_vec()));
}

/// Upstream `TEST_CASE("ParamFile - Override base properties")`, section "Property override".
///
/// Why: upstream's known-value check with the same input (D013); the tree must give the game's reading of it.
#[test]
fn override_base_properties() {
    let cst =
        parsed(b"class Base {\n    value = 100;\n};\nclass Derived : Base {\n    value = 200;\n};");
    assert_eq!(
        value(&cst, &[b"Derived", b"value"]).scalar(),
        Scalar::Int(200)
    );
}

/// Upstream `TEST_CASE("ParamFile - Add new properties to derived")`, section "Extend base class" (own entries).
///
/// Why: upstream's known-value check with the same input (D013); the tree must give the game's reading of it.
#[test]
fn add_new_properties_to_derived() {
    let cst = parsed(
        b"class Base {\n    baseValue = 100;\n};\nclass Derived : Base {\n    newValue = 200;\n};",
    );
    assert!(cst.find(&[b"Base", b"newValue"]).is_none());
    assert!(cst.find(&[b"Derived", b"newValue"]).is_some());
}

/// Upstream `TEST_CASE("ParamFile - Inheritance in nested classes")`, section "Nested class inheritance" (syntax).
///
/// Why: upstream's known-value check with the same input (D013); the tree must give the game's reading of it.
#[test]
fn inheritance_in_nested_classes_syntax() {
    let cst = parsed(
        b"class Outer {\n    class Base {\n        value = 1;\n    };\n    class Derived : Base {\n        extra = 2;\n    };\n};",
    );
    assert_eq!(
        class(&cst, &[b"Outer", b"Derived"]).base(),
        Some(b"Base".to_vec())
    );
    assert!(cst.find(&[b"Outer", b"Derived", b"extra"]).is_some());
}

/// Upstream `TEST_CASE("ParamFile - Multi-level inheritance")` and `("... Handle diamond pattern")` (syntax).
///
/// Why: upstream's known-value check with the same input (D013); the tree must give the game's reading of it.
#[test]
fn multi_level_and_diamond_syntax() {
    let cst = parsed(b"class Level1 {\n    l1 = 1;\n};\nclass Level2 : Level1 {\n    l2 = 2;\n};\nclass Level3 : Level2 {\n    l3 = 3;\n};");
    assert_eq!(class(&cst, &[b"Level3"]).base(), Some(b"Level2".to_vec()));
    assert!(cst.find(&[b"Level3", b"l3"]).is_some());
    let cst = parsed(
        b"class Base {\n    value = 1;\n};\nclass Left : Base {\n    leftValue = 2;\n};\nclass Right : Base {\n    rightValue = 3;\n};\nclass Diamond : Left {\n    diamondValue = 4;\n};",
    );
    assert!(cst.find(&[b"Diamond"]).is_some());
}

// ── Error field & Display verification: Section 2.3, error handling ─────────────────────────────────────────────

/// Upstream `TEST_CASE("ParamFile - Error on missing semicolon")` (vacuous upstream).
///
/// Why: a value that reaches the end of input without `;` is dropped (`ParamFile.cpp#L1798-L1803`). unverified-1.99.
#[test]
fn error_on_missing_semicolon() {
    let cst = parsed(b"value = 123");
    assert!(cst.find(&[b"value"]).is_none());
    let issues = lint_syntax(&cst);
    assert_eq!(
        issues[0].kind(),
        IssueKind::Stopped(StopReason::MissingTerminatorAtEof)
    );
    assert_eq!(issues[0].effect(), EngineEffect::EntryDropped);
}

/// Upstream `TEST_CASE("ParamFile - Error on unmatched braces")` (disabled upstream: it hung before CWR's fixes).
///
/// Why: a missing `}` at the end of input is accepted silently (`ParamFile.cpp#L1582-L1585`). unverified-1.99.
#[test]
fn error_on_unmatched_braces() {
    let cst = parsed(b"class Test {\n    value = 1;\n");
    assert_eq!(value(&cst, &[b"Test", b"value"]).scalar(), Scalar::Int(1));
    assert_eq!(kinds(&cst), [IssueKind::MissingCloseBraceAtEof]);
}

/// Upstream `TEST_CASE("ParamFile - Error on invalid names")` (vacuous upstream).
///
/// Why: names may start with a digit (`GetAlphaWord`, `ParamFilePrivate.inc#L117`). unverified-1.99.
#[test]
fn error_on_invalid_names() {
    let cst = parsed(b"123invalid = 1;");
    assert_eq!(value(&cst, &[b"123invalid"]).scalar(), Scalar::Int(1));
    assert!(lint_syntax(&cst).is_empty());
}

/// Upstream `TEST_CASE("ParamFile - Error on premature EOF")` (disabled upstream).
///
/// Why: `class Test {` at the end of input gives an empty class, accepted silently. unverified-1.99.
#[test]
fn error_on_premature_eof() {
    let cst = parsed(b"class Test {");
    assert!(class(&cst, &[b"Test"]).entries().is_empty());
    assert_eq!(kinds(&cst), [IssueKind::MissingCloseBraceAtEof]);
}

/// Upstream `TEST_CASE("ParamFile - Error on malformed arrays")` (disabled upstream).
///
/// Why: the input ends inside the literal, then the array's `;` is missing: the entry is dropped
/// (`ParamFileParse.cpp#L502-L506`; `ParamFile.cpp#L1768-L1772`). unverified-1.99.
#[test]
fn error_on_malformed_arrays() {
    let cst = parsed(b"array[] = {1, 2, 3");
    assert!(cst.find(&[b"array"]).is_none());
    assert_eq!(
        kinds(&cst),
        [
            IssueKind::Stopped(StopReason::ArrayEndOfInput),
            IssueKind::Stopped(StopReason::ExpectedSemicolonAfterArray)
        ]
    );
}

/// Upstream `TEST_CASE("ParamFile - Reject binary data")` (disabled upstream: it crashed `GetWord`).
///
/// Why: binary junk is kept byte for byte, defines nothing, and does not panic.
#[test]
fn reject_binary_data() {
    let cst = parsed(&[0x00, 0x01, 0x02, 0xFF, 0xFE]);
    assert!(cst.entries().is_empty());
}

/// Upstream `TEST_CASE("ParamFile - Error on unterminated quotes")` (disabled upstream: it hung).
///
/// Why: the string runs to the end of input, then the terminator is missing: the entry is dropped
/// (`ParamFilePrivate.inc#L32-L38`). unverified-1.99.
#[test]
fn error_on_unterminated_quotes() {
    let cst = parsed(b"text = \"unterminated");
    assert!(cst.find(&[b"text"]).is_none());
    let found = kinds(&cst);
    assert!(found.contains(&IssueKind::UnterminatedString));
    assert!(found.contains(&IssueKind::Stopped(StopReason::MissingTerminatorAtEof)));
}

/// Upstream `TEST_CASE("ParamFile - Error on malformed numbers")` (vacuous upstream).
///
/// Why: `12.34.56` is not a whole number for `strtol` or `strtod`, so the game keeps it as a string. unverified-1.99.
#[test]
fn error_on_malformed_numbers() {
    let cst = parsed(b"value = 12.34.56;");
    assert_eq!(value(&cst, &[b"value"]).scalar(), Scalar::Text);
    assert_eq!(value(&cst, &[b"value"]).text(), b"12.34.56");
}

/// Upstream `TEST_CASE("ParamFile - Error position reporting")` (vacuous upstream).
///
/// Why: `invalid syntax here` stops the root at its statement (offset 12); `value2` is never read.
/// unverified-1.99.
#[test]
fn error_position_reporting() {
    let cst = parsed(b"value1 = 1;\ninvalid syntax here\nvalue2 = 2;\n");
    assert!(cst.find(&[b"value1"]).is_some());
    assert!(cst.find(&[b"value2"]).is_none());
    let issues = lint_syntax(&cst);
    assert_eq!(
        issues[0].kind(),
        IssueKind::Stopped(StopReason::ExpectedEquals)
    );
    assert_eq!(issues[0].effect(), EngineEffect::RootStops);
    assert_eq!(issues[0].span().start(), TextOffset::from_raw(12));
}
