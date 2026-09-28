// SPDX-License-Identifier: GPL-3.0-or-later
//! Span patches: bytes outside the patched span never change, untouched subtrees are shared, and every request the
//! tree cannot honour is refused with an error that names the fix.

use crate::cst::green::GreenChild;
use crate::emit::WriterProfile;
use crate::error::Error;
use crate::text::{TextOffset, TextSpan, TextWidth};
use crate::{ElementValueLexeme, EntryValueLexeme, Limits, lint_syntax, parse, parse_with_limits};

/// Applies an entry-value patch and returns the new text, after checking the declared edit.
fn patch_entry(text: &[u8], path: &[&[u8]], lexeme: EntryValueLexeme) -> Vec<u8> {
    let cst = parse(text).unwrap();
    let target = cst.entry_value(path).unwrap();
    let (new_cst, edit) = cst
        .replace_entry_value(target, lexeme)
        .unwrap()
        .into_parts();
    let new_text = new_cst.render();
    edit.check_outside_unchanged(text, &new_text).unwrap();
    assert_eq!(parse(&new_text).unwrap().debug_tree(), new_cst.debug_tree());
    new_text
}

// ── Basic functionality ──────────────────────────────────────────────────────────────────────────────────────────

/// An int, a float, a bare token and a quoted string replace a value; nothing else changes.
///
/// Why: the SP-09 exit criterion: a patch leaves every byte outside its span unchanged.
#[test]
fn entry_values_are_replaced_in_place() {
    let text = b"class Mission\r\n{\r\n\tclass Item0\r\n\t{\r\n\t\tside=\"WEST\"; // player\r\n\t\tskill=0.6;\r\n\t};\r\n};\r\n";
    let new = patch_entry(
        text,
        &[b"Mission", b"Item0", b"skill"],
        EntryValueLexeme::float(0.75, WriterProfile::Legacy196Text).unwrap(),
    );
    assert_eq!(new, b"class Mission\r\n{\r\n\tclass Item0\r\n\t{\r\n\t\tside=\"WEST\"; // player\r\n\t\tskill=0.750000;\r\n\t};\r\n};\r\n");
    let new = patch_entry(
        text,
        &[b"mission", b"item0", b"SIDE"],
        EntryValueLexeme::quoted(b"EAST").unwrap(),
    );
    assert!(new.windows(13).any(|w| w == b"side=\"EAST\"; "));
    let new = patch_entry(b"n = 1;", &[b"n"], EntryValueLexeme::int(i32::MIN));
    assert_eq!(new, b"n = -2147483648;");
    let new = patch_entry(
        b"n = 1;",
        &[b"n"],
        EntryValueLexeme::bare(b"LIEUTENANT").unwrap(),
    );
    assert_eq!(new, b"n = LIEUTENANT;");
}

/// Array elements, including elements of sub-arrays, are replaced in place.
///
/// Why: positions and `addOns[]` entries are array elements; they must be editable without re-writing the array.
#[test]
fn array_elements_are_replaced_in_place() {
    let text = b"position[]={1.5, 0, 2.25};\r\nm[] = {{1,2},{3, 4}};\r\n";
    let cst = parse(text).unwrap();
    let target = cst.element_value(&[b"position"], &[1]).unwrap();
    let (cst2, edit) = cst
        .replace_element_value(target, ElementValueLexeme::int(42))
        .unwrap()
        .into_parts();
    let new = cst2.render();
    assert_eq!(
        new,
        b"position[]={1.5, 42, 2.25};\r\nm[] = {{1,2},{3, 4}};\r\n"
    );
    edit.check_outside_unchanged(text, &new).unwrap();
    let target = cst2.element_value(&[b"m"], &[1, 0]).unwrap();
    let (cst3, _) = cst2
        .replace_element_value(target, ElementValueLexeme::quoted(b"x,}").unwrap())
        .unwrap()
        .into_parts();
    assert_eq!(
        cst3.render(),
        b"position[]={1.5, 42, 2.25};\r\nm[] = {{1,2},{\"x,}\", 4}};\r\n"
    );
    assert!(lint_syntax(&cst3).is_empty());
}

/// A value split by a comment is replaced whole; the comment inside the value goes with it.
///
/// Why: the game reads `1 /*c*/ 2` as one value; replacing it must replace all of it.
#[test]
fn a_value_split_by_a_comment_is_replaced_whole() {
    let new = patch_entry(
        b"x = 1 /*c*/ 2; // keep\n",
        &[b"x"],
        EntryValueLexeme::int(7),
    );
    assert_eq!(new, b"x = 7; // keep\n");
}

/// Untouched subtrees are shared with the old tree, and later tokens move by the length change.
///
/// Why: this is the SP-09 evidence that offsets come from widths: the shared nodes are the same `Arc`s, yet their
/// tokens now report offsets shifted by the edit's delta.
#[test]
fn untouched_subtrees_are_shared_and_offsets_shift() {
    let text = b"class A { x = 1; };\nclass B { y = 2; };\n";
    let cst = parse(text).unwrap();
    let target = cst.entry_value(&[b"A", b"x"]).unwrap();
    let (new_cst, edit) = cst
        .replace_entry_value(target, EntryValueLexeme::int(1000))
        .unwrap()
        .into_parts();
    assert_eq!(
        edit.removed(),
        TextSpan::new(TextOffset::from_raw(14), TextOffset::from_raw(15)).unwrap()
    );
    assert_eq!(edit.inserted(), TextWidth::from_raw(4));
    let old_children = cst.green().children();
    let new_children = new_cst.green().children();
    let class_b = |children: &[GreenChild]| match children.get(2) {
        Some(GreenChild::Node(node)) => node.clone(),
        other => panic!("class B expected, got {other:?}"),
    };
    assert!(
        class_b(old_children).ptr_eq(&class_b(new_children)),
        "class B is shared"
    );
    let class_a = |children: &[GreenChild]| match children.first() {
        Some(GreenChild::Node(node)) => node.clone(),
        other => panic!("class A expected, got {other:?}"),
    };
    assert!(
        !class_a(old_children).ptr_eq(&class_a(new_children)),
        "class A is rebuilt"
    );
    let old_y = cst.entry_value(&[b"B", b"y"]).unwrap().span();
    let new_y = new_cst.entry_value(&[b"B", b"y"]).unwrap().span();
    assert_eq!(new_y.start().to_raw(), old_y.start().to_raw() + 3);
}

/// Patches chain: a reference taken on the patched tree patches it again.
///
/// Why: editing sessions apply many patches in a row, each on the latest revision.
#[test]
fn patches_chain() {
    let cst = parse(b"a = 1; b = 2;").unwrap();
    let (cst, _) = cst
        .replace_entry_value(cst.entry_value(&[b"a"]).unwrap(), EntryValueLexeme::int(10))
        .unwrap()
        .into_parts();
    let (cst, _) = cst
        .replace_entry_value(cst.entry_value(&[b"b"]).unwrap(), EntryValueLexeme::int(20))
        .unwrap()
        .into_parts();
    assert_eq!(cst.render(), b"a = 10; b = 20;");
}

// ── Error field & Display verification ───────────────────────────────────────────────────────────────────────────

/// A reference from another tree (even one with the same text) is refused.
///
/// Why: a reference is bound to one revision; applying it elsewhere could patch the wrong bytes.
#[test]
fn a_stale_reference_is_refused() {
    let first = parse(b"x = 1;").unwrap();
    let second = parse(b"x = 1;").unwrap();
    let target = first.entry_value(&[b"x"]).unwrap();
    let err = second
        .replace_entry_value(target, EntryValueLexeme::int(2))
        .unwrap_err();
    assert_eq!(
        err,
        Error::StaleValueRef {
            value_offset: TextOffset::from_raw(4)
        }
    );
    assert!(err.to_string().contains("ConfigCst::entry_value"));
}

/// A quoted value would be dropped by the game if whitespace separated it from `;`; the patch is refused.
///
/// Why: `x = "a" ;` drops the entry (`ParamFile.cpp#L1798-L1803`); a bare value there is fine.
#[test]
fn a_quoted_value_needs_its_terminator_adjacent() {
    let cst = parse(b"x = 5 ;").unwrap();
    let err = cst
        .replace_entry_value(
            cst.entry_value(&[b"x"]).unwrap(),
            EntryValueLexeme::quoted(b"a").unwrap(),
        )
        .unwrap_err();
    assert_eq!(
        err,
        Error::QuotedValueNeedsAdjacentTerminator {
            value_end: TextOffset::from_raw(5),
            trivia_len: 1
        }
    );
    assert!(err.to_string().contains("1 bytes of whitespace"));
    let patched = cst
        .replace_entry_value(cst.entry_value(&[b"x"]).unwrap(), EntryValueLexeme::int(6))
        .unwrap();
    assert_eq!(patched.cst().render(), b"x = 6 ;");
}

/// Regression (found by `tests/prop_patch.rs`): a comment between the value and the whitespace before `;` is
/// invisible to the game, so the quoted value is still refused with the specific error, not a structure change;
/// with no whitespace, or with a line break as terminator, the quoted value is accepted.
///
/// Why: the game sees `"a" ;` in `x = "a"/* c */ ;`; the error must name the fix, not a generic structure change.
#[test]
fn a_comment_before_the_whitespace_does_not_hide_it() {
    let cst = parse(b"x = 5/* c */\x0B;").unwrap();
    let err = cst
        .replace_entry_value(
            cst.entry_value(&[b"x"]).unwrap(),
            EntryValueLexeme::quoted(b"").unwrap(),
        )
        .unwrap_err();
    assert_eq!(
        err,
        Error::QuotedValueNeedsAdjacentTerminator {
            value_end: TextOffset::from_raw(5),
            trivia_len: 8
        }
    );
    for text in [&b"x = 5/* c */;"[..], b"x = 5/* c */\r\ny = 1;"] {
        let cst = parse(text).unwrap();
        let patched = cst.replace_entry_value(
            cst.entry_value(&[b"x"]).unwrap(),
            EntryValueLexeme::quoted(b"q").unwrap(),
        );
        assert!(patched.is_ok(), "{:?}", String::from_utf8_lossy(text));
    }
}

/// A lexeme that would change how the text around it is read is refused.
///
/// Why: a value on its own line after `=` that starts with `#` would become a directive.
#[test]
fn a_patch_that_changes_structure_is_refused() {
    let cst = parse(b"x =\n5;\ny = 1;").unwrap();
    let err = cst
        .replace_entry_value(
            cst.entry_value(&[b"x"]).unwrap(),
            EntryValueLexeme::bare(b"#define").unwrap(),
        )
        .unwrap_err();
    assert!(
        matches!(err, Error::PatchChangesStructure { .. }),
        "{err:?}"
    );
}

/// A patch that would push the text past the size cap is refused with both lengths.
///
/// Why: the patched tree must parse again under the same limits.
#[test]
fn a_patch_past_the_size_cap_is_refused() {
    let cst = parse_with_limits(b"x = 1;", Limits::new(10, 8)).unwrap();
    let err = cst
        .replace_entry_value(
            cst.entry_value(&[b"x"]).unwrap(),
            EntryValueLexeme::bare(b"123456").unwrap(),
        )
        .unwrap_err();
    assert_eq!(
        err,
        Error::PatchExceedsLimit {
            new_len: 11,
            cap: 10
        }
    );
    // Exactly at the cap is fine.
    let ok = cst.replace_entry_value(
        cst.entry_value(&[b"x"]).unwrap(),
        EntryValueLexeme::bare(b"12345").unwrap(),
    );
    assert_eq!(ok.unwrap().cst().render(), b"x = 12345;");
}

/// Bare lexemes refuse every byte that would end, split or hide the value, with its position.
///
/// Why: lexemes are witnesses: once built, a lexeme reads back as exactly one value in its context.
#[test]
fn bare_lexemes_refuse_structural_bytes() {
    let cases: [(&[u8], u32, u8); 10] = [
        (b"a;b", 1, b';'),
        (b"a\nb", 1, b'\n'),
        (b"a\rb", 1, b'\r'),
        (b"a\0b", 1, 0),
        (b"a\"b", 1, b'"'),
        (b"a//b", 1, b'/'),
        (b"a/*b", 1, b'/'),
        (b" a", 0, b' '),
        (b"a\t", 1, b'\t'),
        (b"\x0Ba", 0, 0x0B),
    ];
    for (text, offset, byte) in cases {
        let err = EntryValueLexeme::bare(text).unwrap_err();
        assert_eq!(
            err,
            Error::InvalidLexeme {
                context: "bare entry value",
                offset_in_lexeme: offset,
                byte
            },
            "{text:?}"
        );
    }
    assert_eq!(
        EntryValueLexeme::bare(b"").unwrap_err(),
        Error::EmptyLexeme {
            context: "bare entry value"
        }
    );
    for (text, offset, byte) in [(&b"a,b"[..], 1, b','), (b"a}b", 1, b'}'), (b"{a", 0, b'{')] {
        let err = ElementValueLexeme::bare(text).unwrap_err();
        assert_eq!(
            err,
            Error::InvalidLexeme {
                context: "bare array element",
                offset_in_lexeme: offset,
                byte
            }
        );
    }
    // Inner spaces, slashes and high bytes are fine.
    assert_eq!(
        EntryValueLexeme::bare(b"2 + 2 / 1 \xE8")
            .unwrap()
            .as_bytes(),
        b"2 + 2 / 1 \xE8"
    );
}

/// Quoted lexemes double `"` and refuse line breaks and NUL; floats refuse NaN and infinity.
///
/// Why: the game reports a line break in a string, and its preprocessor drops CR and NUL (the value would change).
#[test]
fn quoted_and_float_lexemes_check_their_input() {
    assert_eq!(
        EntryValueLexeme::quoted(b"say \"hi\"").unwrap().as_bytes(),
        b"\"say \"\"hi\"\"\""
    );
    assert_eq!(
        EntryValueLexeme::quoted(b"a\nb").unwrap_err(),
        Error::NewlineInQuotedValue { offset_in_value: 1 }
    );
    assert_eq!(
        EntryValueLexeme::quoted(b"ab\r").unwrap_err(),
        Error::NewlineInQuotedValue { offset_in_value: 2 }
    );
    assert_eq!(
        EntryValueLexeme::quoted(b"\0").unwrap_err(),
        Error::InvalidLexeme {
            context: "quoted value",
            offset_in_lexeme: 0,
            byte: 0
        }
    );
    let nan = f32::NAN;
    assert_eq!(
        EntryValueLexeme::float(nan, WriterProfile::RemasteredText).unwrap_err(),
        Error::NonFiniteFloat {
            bits: nan.to_bits()
        }
    );
    assert!(ElementValueLexeme::float(f32::INFINITY, WriterProfile::Legacy196Text).is_err());
    assert_eq!(
        ElementValueLexeme::float(2.5, WriterProfile::Legacy196Text)
            .unwrap()
            .as_bytes(),
        b"2.500000"
    );
}

/// Lookups that do not name a value of the right kind return `None`.
///
/// Why: a wrong path must be a missing value, never a patch of something else.
#[test]
fn lookups_of_the_wrong_kind_are_none() {
    let cst = parse(b"class C { v = 1; a[] = {1, {2}}; };").unwrap();
    assert!(cst.entry_value(&[b"C"]).is_none());
    assert!(cst.entry_value(&[b"C", b"a"]).is_none());
    assert!(cst.entry_value(&[b"C", b"missing"]).is_none());
    assert!(cst.element_value(&[b"C", b"v"], &[0]).is_none());
    assert!(cst.element_value(&[b"C", b"a"], &[2]).is_none());
    assert!(
        cst.element_value(&[b"C", b"a"], &[1]).is_none(),
        "a sub-array is not an element value"
    );
    assert!(
        cst.element_value(&[b"C", b"a"], &[0, 0]).is_none(),
        "an element has no sub-items"
    );
    assert!(cst.element_value(&[b"C", b"a"], &[]).is_none());
    assert!(cst.element_value(&[b"C", b"a"], &[1, 0]).is_some());
}

/// The byte-edit check reports the first changed byte outside the span, and impossible lengths.
///
/// Why: `check_outside_unchanged` is the proof other layers rely on (`verify_round_trip_each_commit`).
#[test]
fn check_outside_unchanged_reports_violations() {
    let cst = parse(b"x = 1; y = 2;").unwrap();
    let (new_cst, edit) = cst
        .replace_entry_value(cst.entry_value(&[b"x"]).unwrap(), EntryValueLexeme::int(99))
        .unwrap()
        .into_parts();
    let new = new_cst.render();
    let mut tampered_before = new.clone();
    tampered_before[0] = b'X';
    assert_eq!(
        edit.check_outside_unchanged(b"x = 1; y = 2;", &tampered_before),
        Err(Error::OutsideSpanChanged { first_diff: 0 })
    );
    let mut tampered_after = new.clone();
    let last = tampered_after.len() - 1;
    tampered_after[last] = b',';
    assert_eq!(
        edit.check_outside_unchanged(b"x = 1; y = 2;", &tampered_after),
        Err(Error::OutsideSpanChanged { first_diff: 12 })
    );
    assert_eq!(
        edit.check_outside_unchanged(b"x = 1;", &new),
        Err(Error::EditOutOfRange {
            span_end: 5,
            old_len: 6,
            new_len: 14
        })
    );
}

// ── Integer overflow safety ──────────────────────────────────────────────────────────────────────────────────────

/// A byte edit whose span reaches `u32::MAX` is reported, not trusted.
///
/// Why: edits may come back from storage or another process and are checked again.
#[test]
fn a_huge_edit_span_is_out_of_range() {
    let cst = parse(b"x = 1;").unwrap();
    let (_, edit) = cst
        .replace_entry_value(cst.entry_value(&[b"x"]).unwrap(), EntryValueLexeme::int(2))
        .unwrap()
        .into_parts();
    let err = edit.check_outside_unchanged(b"", b"").unwrap_err();
    assert!(
        matches!(
            err,
            Error::EditOutOfRange {
                span_end: 5,
                old_len: 0,
                new_len: 0
            }
        ),
        "{err:?}"
    );
    let span = TextSpan::new(
        TextOffset::from_raw(u32::MAX - 1),
        TextOffset::from_raw(u32::MAX),
    )
    .unwrap();
    assert_eq!(span.width(), TextWidth::from_raw(1));
}
