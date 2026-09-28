// SPDX-License-Identifier: GPL-3.0-or-later
//! Basic functionality and determinism of the tree: round trips, shapes, cursors and the game's view of entries.

use crate::cst::cursor::CstElement;
use crate::cst::entries::{ArrayItem, Entry};
use crate::cst::kinds::{NodeKind, TokenKind};
use crate::scalar::Scalar;
use crate::{ConfigCst, lint_syntax, parse};

/// Parses `text`, asserts the round trip, and returns the tree.
fn parsed(text: &[u8]) -> ConfigCst {
    let cst = parse(text).unwrap();
    assert_eq!(
        cst.render(),
        text,
        "round trip of {:?}",
        String::from_utf8_lossy(text)
    );
    cst
}

/// The names of the top-level entries.
fn names(cst: &ConfigCst) -> Vec<String> {
    cst.entries()
        .iter()
        .map(|entry| String::from_utf8_lossy(&entry.name()).into_owned())
        .collect()
}

/// The text of the value at `path`.
fn value_text(cst: &ConfigCst, path: &[&[u8]]) -> Vec<u8> {
    let Some(Entry::Value(entry)) = cst.find(path) else {
        panic!("no value at {path:?}")
    };
    entry.value().unwrap().text()
}

// ── Basic functionality ──────────────────────────────────────────────────────────────────────────────────────────

/// Empty input gives an empty file node and no entries.
///
/// Why: the smallest valid input; every other property builds on it.
#[test]
fn empty_input_is_an_empty_file() {
    let cst = parsed(b"");
    assert_eq!(cst.debug_tree(), "File[]");
    assert!(cst.entries().is_empty());
    assert!(lint_syntax(&cst).is_empty());
    assert_eq!(cst.width().to_raw(), 0);
}

/// Three assignments give three value entries with the whitespace kept as trivia outside the values.
///
/// Why: whitespace around `=` must stay outside the `Value` node, so a patch of the value never touches it.
#[test]
fn simple_assignments_have_the_expected_shape() {
    let cst = parsed(b"testInt = 42;\ntestFloat = 2.5;\ntestString = \"Hello\";\n");
    assert_eq!(names(&cst), ["testInt", "testFloat", "testString"]);
    let dump = cst.debug_tree();
    assert!(dump.starts_with(
        "File[ValueEntry[Name[Ident'testInt'] Whitespace' ' = Whitespace' ' Value[BareText'42'] ;] Newline'\\n' "
    ));
    assert!(dump.contains("Value[QuotedString'\"Hello\"']"));
    assert_eq!(value_text(&cst, &[b"testString"]), b"Hello");
}

/// CR LF line breaks and TAB indentation are single tokens, and the class layout of the game's writer parses.
///
/// Why: `mission.sqm` is written with CR LF and TABs (doc 04 §2.2); a CR LF split into two tokens would make
/// line-oriented edits and the trivia model awkward.
#[test]
fn crlf_and_tabs_are_kept_as_single_tokens() {
    let cst = parsed(b"class Intel\r\n{\r\n\tweather=0.2;\r\n};\r\n");
    let dump = cst.debug_tree();
    assert!(dump.contains("Newline'\\r\\n'"), "{dump}");
    assert!(dump.contains("Whitespace'\\t'"), "{dump}");
    assert!(!dump.contains("CarriageReturn"), "{dump}");
    let Some(Entry::Class(intel)) = cst.find(&[b"Intel"]) else {
        panic!("class Intel")
    };
    assert!(intel.is_closed());
    assert_eq!(value_text(&cst, &[b"intel", b"WEATHER"]), b"0.2");
}

/// Nested classes, a base name and arrays are read into the entry views.
///
/// Why: the typed lens reads everything through these views.
#[test]
fn classes_bases_and_arrays_are_read() {
    let cst = parsed(
        b"class Base { v = 1; };\nclass Outer : Base {\n  class Inner { deep[] = {1, \"two\", {3, 4}}; };\n};\n",
    );
    assert_eq!(names(&cst), ["Base", "Outer"]);
    let Some(Entry::Class(outer)) = cst.find(&[b"Outer"]) else {
        panic!("Outer")
    };
    assert_eq!(outer.base(), Some(b"Base".to_vec()));
    let Some(Entry::Array(deep)) = cst.find(&[b"Outer", b"Inner", b"deep"]) else {
        panic!("deep")
    };
    let items = deep.items();
    assert_eq!(items.len(), 3);
    let ArrayItem::Value(first) = items[0] else {
        panic!("first is a value")
    };
    assert_eq!(first.scalar(), Scalar::Int(1));
    let ArrayItem::Value(second) = items[1] else {
        panic!("second is a value")
    };
    assert_eq!(second.text(), b"two");
    assert_eq!(second.scalar(), Scalar::Text);
    let ArrayItem::Array(third) = items[2] else {
        panic!("third is a sub-array")
    };
    assert_eq!(third.items().len(), 2);
}

/// Comments in every trivia position are kept, and a comment inside a value splits it without changing what the
/// game reads.
///
/// Why: the game's preprocessor removes comments anywhere outside quotes; the tree must keep them and still report
/// the value the game reads (`x = 1 /*c*/ 2;` reads as `1  2`).
#[test]
fn comments_are_trivia_everywhere() {
    let text = b"// head\nclass /*a*/ A /*b*/ : /*c*/ B /*d*/ { /*e*/ x /*f*/ = /*g*/ 1 /*h*/ 2 /*i*/ ; };\n/* tail */";
    let cst = parsed(text);
    let Some(Entry::Class(a)) = cst.find(&[b"A"]) else {
        panic!("class A")
    };
    assert_eq!(a.base(), Some(b"B".to_vec()));
    let Some(Entry::Value(x)) = cst.find(&[b"A", b"x"]) else {
        panic!("A.x")
    };
    let value = x.value().unwrap();
    assert_eq!(value.lexeme(), b"1  2");
    assert!(
        value
            .node()
            .tokens()
            .iter()
            .any(|t| t.kind() == TokenKind::BlockComment)
    );
    assert!(lint_syntax(&cst).is_empty());
}

/// Directive lines are trivia (with `#define` continuations), and both `#ifdef` branches are read as text.
///
/// Why: `description.ext` and `config.cpp` use directives; the CST keeps them verbatim and leaves their meaning to
/// the preprocessor crate.
#[test]
fn directives_are_trivia() {
    let text = b"#include \"common.hpp\"\n#define LONG 1 \\\n  + 2\n#ifdef A\nx = 1;\n#else\ny = 2;\n#endif\n";
    let cst = parsed(text);
    assert_eq!(names(&cst), ["x", "y"]);
    let dump = cst.debug_tree();
    assert!(
        dump.contains("Directive(Include)'#include \"common.hpp\"'"),
        "{dump}"
    );
    assert!(
        dump.contains("Directive(Define)'#define LONG 1 \\x5C\\n  + 2'"),
        "{dump}"
    );
    assert!(
        dump.contains("Directive(IfDef)")
            && dump.contains("Directive(Else)")
            && dump.contains("Directive(EndIf)")
    );
    assert!(lint_syntax(&cst).is_empty());
}

/// A `mission.sqm`-shaped file built in code (CR LF, TABs, the four sections) round-trips and is read correctly.
///
/// Why: the main file the editor edits; the fixture is synthetic (no game data, `AGENTS.md` fixture rules).
#[test]
fn mission_shaped_text_is_read() {
    let mut text = b"version=11;\r\n".to_vec();
    for section in ["Mission", "Intro", "OutroWin", "OutroLoose"] {
        text.extend_from_slice(
            format!("class {section}\r\n{{\r\n\taddOns[]=\r\n\t{{\r\n\t\t\"pack_a\"\r\n\t}};\r\n")
                .as_bytes(),
        );
        text.extend_from_slice(
            b"\tclass Intel\r\n\t{\r\n\t\tresistanceWest=0.000000;\r\n\t};\r\n};\r\n",
        );
    }
    let cst = parsed(&text);
    assert_eq!(
        names(&cst),
        ["version", "Mission", "Intro", "OutroWin", "OutroLoose"]
    );
    assert_eq!(value_text(&cst, &[b"version"]), b"11");
    let Some(Entry::Array(addons)) = cst.find(&[b"OutroLoose", b"addOns"]) else {
        panic!("addOns")
    };
    assert_eq!(addons.items().len(), 1);
    assert!(lint_syntax(&cst).is_empty());
}

/// Quoted values unescape `""` and keep every other byte, including raw code-page bytes.
///
/// Why: strings are raw bytes (D017 item 5); `""` is the only escape the game knows (`ParamFilePrivate.inc#L39-L46`).
#[test]
fn quoted_values_unescape_doubled_quotes_only() {
    let cst =
        parsed(b"a = \"He said \"\"hi\"\"\";\nb = \"\\n stays\";\nc = \"\xE8\xE9\";\nd = \"\";\n");
    assert_eq!(value_text(&cst, &[b"a"]), b"He said \"hi\"");
    assert_eq!(value_text(&cst, &[b"b"]), b"\\n stays");
    assert_eq!(value_text(&cst, &[b"c"]), b"\xE8\xE9");
    assert_eq!(value_text(&cst, &[b"d"]), b"");
}

/// Token spans are contiguous, start at 0 and end at the input length, and node spans match their tokens.
///
/// Why: offsets are derived from widths (core-document-model §3.1); a gap or overlap would misplace every patch.
#[test]
fn token_spans_tile_the_input() {
    let text = b"class A { x[] = {1, \"a\"}; /* c */ };\r\ny = 2;";
    let cst = parsed(text);
    let tokens = cst.root().tokens();
    let mut expected_start = 0;
    for token in &tokens {
        assert_eq!(token.span().start().to_raw(), expected_start);
        assert_eq!(token.span().slice(text), Some(token.bytes()));
        expected_start = token.span().end().to_raw();
    }
    assert_eq!(expected_start as usize, text.len());
    for child in cst.root().children() {
        if let CstElement::Node(node) = child {
            assert_eq!(
                node.span().slice(text).map(<[u8]>::to_vec),
                Some(node.text())
            );
        }
    }
}

/// Every statement kind has its node kind.
///
/// Why: lints and the lens dispatch on node kinds.
#[test]
fn statement_kinds_are_recorded() {
    let cst = parsed(b"class C {}; v = 1; a[] = {}; enum {E1, E2}; __EXEC(x = 1);");
    let kinds: Vec<NodeKind> = cst.root().child_nodes().map(|node| node.kind()).collect();
    assert_eq!(
        kinds,
        [
            NodeKind::ClassDecl,
            NodeKind::ValueEntry,
            NodeKind::ArrayEntry,
            NodeKind::EnumDecl,
            NodeKind::ExecStmt
        ]
    );
    // Enum and __EXEC statements are not entries.
    assert_eq!(names(&cst), ["C", "v", "a"]);
}

// ── Determinism ──────────────────────────────────────────────────────────────────────────────────────────────────

/// Parsing the same input twice gives the same tree dump, render and issues.
///
/// Why: parsers are pure functions of their input (`AGENTS.md`, "Parser Design Philosophy").
#[test]
fn parsing_is_deterministic() {
    let text = b"class A { x = \"a\" ; };\n}\n#if 0\n\x00\xEF\xBB\xBF";
    let first = parse(text).unwrap();
    let second = parse(text).unwrap();
    assert_eq!(first.debug_tree(), second.debug_tree());
    assert_eq!(first.render(), second.render());
    assert_eq!(lint_syntax(&first), lint_syntax(&second));
}
