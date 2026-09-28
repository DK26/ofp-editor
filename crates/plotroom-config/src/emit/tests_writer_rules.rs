// SPDX-License-Identifier: GPL-3.0-or-later
//! The writer-rule table: one test per rule of doc 04 §2.2 (roadmap SP-09 exit evidence).
//!
//! | Rule | What | Test |
//! | --- | --- | --- |
//! | W1 | One TAB per nesting level | `w1_one_tab_per_level` |
//! | W2 | Every line ends in CR LF | `w2_every_line_ends_in_crlf` |
//! | W3 | `class Name` CRLF `{` CRLF members `};` CRLF, also when empty | `w3_class_layout_including_empty` |
//! | W3b | A base is written `class D: B` (CWR form) | `w3b_base_class_form` |
//! | W4 | Values are `name=value;` | `w4_values_are_name_equals_value` |
//! | W5 | Strings: `"` doubled, nothing else escaped, bytes above 0x7F raw | `w5_strings_double_quotes_only` |
//! | W6 | Ints are `%d` | `w6_ints_are_percent_d` |
//! | W7 | `Legacy196Text` floats are `%f` | `w7_legacy_floats_are_percent_f` |
//! | W7b | `RemasteredText` floats: `%f` if it reads back, else `%.9g` | `w7b_remastered_float_fallback` |
//! | W7c | NaN and infinity are refused | `w7c_non_finite_floats_are_refused` |
//! | W7d | Exact ties round half to even (unverified-1.99) | `w7d_float_ties` |
//! | W8 | Bools go through the int overload: `0` / `1` | `w8_bools_are_zero_and_one` |
//! | W9 | All-numeric arrays are inline `{1,2,3}` | `w9_numeric_arrays_are_inline` |
//! | W9b | Other arrays: one element per line | `w9b_string_arrays_are_multi_line` |
//! | W9c | Numeric-looking strings stay inline, quoted | `w9c_numeric_looking_strings_stay_inline` |
//! | W9d | The empty array is `{}` | `w9d_empty_array` |
//! | W9e | A sub-array in a multi-line array uses the parent's indent | `w9e_nested_multi_line_sub_array` |
//! | W10 | Entries in insertion order | `w10_insertion_order` |
//!
//! Goldens are derived by hand from `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/IO/ParamFile/ParamFileParse.cpp`
//! (`#L325-L697`); float goldens come from C `printf` semantics (Python's `%` operator on the float widened to double).

use super::{ClassModel, EntryModel, ItemModel, ScalarModel, WriterProfile, write_entries};
use crate::error::Error;
use crate::{lint_syntax, parse};

fn value(name: &str, value: ScalarModel) -> EntryModel {
    EntryModel::Value {
        name: name.as_bytes().to_vec(),
        value,
    }
}

fn array(name: &str, items: Vec<ItemModel>) -> EntryModel {
    EntryModel::Array {
        name: name.as_bytes().to_vec(),
        items,
    }
}

fn class(name: &str, entries: Vec<EntryModel>) -> EntryModel {
    EntryModel::Class(ClassModel {
        name: name.as_bytes().to_vec(),
        base: None,
        entries,
    })
}

fn text(content: &str) -> ScalarModel {
    ScalarModel::Text(content.as_bytes().to_vec())
}

fn int(number: i32) -> ItemModel {
    ItemModel::Scalar(ScalarModel::Int(number))
}

/// Writes with the legacy profile and checks that the output reads back cleanly.
fn write(entries: &[EntryModel]) -> Vec<u8> {
    let out = write_entries(entries, WriterProfile::Legacy196Text).unwrap();
    let cst = parse(&out).unwrap();
    assert!(
        lint_syntax(&cst).is_empty(),
        "writer output must read back cleanly: {}",
        String::from_utf8_lossy(&out)
    );
    out
}

fn float(value: f32, profile: WriterProfile) -> String {
    super::format_float(value, profile).unwrap()
}

// ── Basic functionality: the rule table ──────────────────────────────────────────────────────────────────────────

/// W1: one TAB per nesting level.
///
/// Why: `Indent` writes `indent` TABs (`#L325-L331`); spaces would change every saved line.
#[test]
fn w1_one_tab_per_level() {
    let out = write(&[class(
        "A",
        vec![class("B", vec![value("v", ScalarModel::Int(1))])],
    )]);
    assert!(out.windows(6).any(|w| w == b"\tclass"), "level 1");
    assert!(out.windows(5).any(|w| w == b"\t\tv=1"), "level 2");
}

/// W2: every line ends in CR LF and there is no bare LF.
///
/// Why: the engine writes `\r\n` after every line (`#L653`, `#L688-L696`).
#[test]
fn w2_every_line_ends_in_crlf() {
    let out = write(&[class(
        "A",
        vec![
            value("v", text("x")),
            array("a", vec![ItemModel::Scalar(text("s"))]),
        ],
    )]);
    for (index, byte) in out.iter().enumerate() {
        if *byte == b'\n' {
            assert_eq!(out[index - 1], b'\r', "LF at {index} without CR");
        }
    }
    assert!(out.ends_with(b"\r\n"));
}

/// W3: the class layout, with an empty class written the same way.
///
/// Why: `ParamClass::Save` (#L678-L697).
#[test]
fn w3_class_layout_including_empty() {
    assert_eq!(write(&[class("X", vec![])]), b"class X\r\n{\r\n};\r\n");
    assert_eq!(
        write(&[class(
            "Mission",
            vec![value("version", ScalarModel::Int(11))]
        )]),
        b"class Mission\r\n{\r\n\tversion=11;\r\n};\r\n"
    );
}

/// W3b: a base class is written `class D: B` (CWR adds it for debinarised round trips, #L682-L687).
///
/// Why: the reader accepts any spacing, the writer has one form. unverified-1.99 (whether 1.99 wrote bases).
#[test]
fn w3b_base_class_form() {
    let model = EntryModel::Class(ClassModel {
        name: b"D".to_vec(),
        base: Some(b"B".to_vec()),
        entries: vec![],
    });
    let out = write_entries(&[class("B", vec![]), model], WriterProfile::Legacy196Text).unwrap();
    assert_eq!(out, b"class B\r\n{\r\n};\r\nclass D: B\r\n{\r\n};\r\n");
}

/// W4: values are `name=value;` with no spaces.
///
/// Why: `ParamValueSpec::Save` (#L647-L654).
#[test]
fn w4_values_are_name_equals_value() {
    assert_eq!(
        write(&[value("skill", ScalarModel::Int(1))]),
        b"skill=1;\r\n"
    );
}

/// W5: strings double `"` and write every other byte raw (backslashes and code-page bytes included).
///
/// Why: `ParamRawValue::Save` (#L344-L361); the game has no other escape.
#[test]
fn w5_strings_double_quotes_only() {
    let out = write(&[value("s", ScalarModel::Text(b"a\"b\\n\xE8".to_vec()))]);
    assert_eq!(out, b"s=\"a\"\"b\\n\xE8\";\r\n");
}

/// W6: ints are `%d`, including the extremes.
///
/// Why: `ParamRawValueInt::Save` (#L418-L423).
#[test]
fn w6_ints_are_percent_d() {
    assert_eq!(
        write(&[value("a", ScalarModel::Int(i32::MIN))]),
        b"a=-2147483648;\r\n"
    );
    assert_eq!(
        write(&[value("b", ScalarModel::Int(i32::MAX))]),
        b"b=2147483647;\r\n"
    );
}

/// W7: the legacy profile writes C `%f` of the float widened to double.
///
/// Why: OFP-era files show `skill=0.200000` (doc 04 §2.2); goldens from C printf semantics.
#[test]
fn w7_legacy_floats_are_percent_f() {
    let legacy = WriterProfile::Legacy196Text;
    assert_eq!(float(0.6, legacy), "0.600000");
    assert_eq!(float(2.5, legacy), "2.500000");
    assert_eq!(float(-0.0, legacy), "-0.000000");
    assert_eq!(float(16_777_217.0, legacy), "16777216.000000");
    assert_eq!(float(1e-5, legacy), "0.000010");
    assert_eq!(
        float(1e30, legacy),
        "1000000015047466219876688855040.000000"
    );
    assert_eq!(float(3.162_28e-5, legacy), "0.000032");
}

/// W7b: the remastered profile keeps `%f` when it reads back to the same float and falls back to `%.9g` otherwise.
///
/// Why: `ParamRawValueFloat::Save` (#L371-L388); CWR's own example value 3.16228e-05 is in the source comment.
#[test]
fn w7b_remastered_float_fallback() {
    let remastered = WriterProfile::RemasteredText;
    assert_eq!(float(0.6, remastered), "0.600000");
    assert_eq!(float(1e-5, remastered), "0.000010");
    assert_eq!(float(3.162_28e-5, remastered), "3.16227997e-05");
    assert_eq!(float(1e-7, remastered), "1.00000001e-07");
    assert_eq!(float(16_777_217.0, remastered), "16777216.000000");
}

/// W7c: NaN and infinities are refused with their bit pattern.
///
/// Why: `%f` would write `nan`/`inf`, which the game reads back as text, not as the float.
#[test]
fn w7c_non_finite_floats_are_refused() {
    for bad in [f32::NAN, f32::INFINITY, f32::NEG_INFINITY] {
        let err = write_entries(
            &[value("f", ScalarModel::Float(bad))],
            WriterProfile::RemasteredText,
        )
        .unwrap_err();
        assert_eq!(
            err,
            Error::NonFiniteFloat {
                bits: bad.to_bits()
            }
        );
    }
}

/// W7d: an exact tie (0.0078125 is exactly representable) rounds half to even under `%f`; the remastered profile
/// then falls back to `%.9g`.
///
/// Why: glibc and Rust round exact ties to even; the legacy Microsoft runtime's tie rounding is unknown
/// (unverified-1.99; doc 04 §12.3 item 6).
#[test]
fn w7d_float_ties() {
    assert_eq!(float(0.007_812_5, WriterProfile::Legacy196Text), "0.007812");
    assert_eq!(
        float(0.007_812_5, WriterProfile::RemasteredText),
        "0.0078125"
    );
}

/// W8: bools are written through the int overload as `0` and `1`.
///
/// Why: `ParamEntry::Add` has no bool overload (`ParamFile.hpp#L120-L122`).
#[test]
fn w8_bools_are_zero_and_one() {
    assert_eq!(
        write(&[
            value("t", ScalarModel::Bool(true)),
            value("f", ScalarModel::Bool(false))
        ]),
        b"t=1;\r\nf=0;\r\n"
    );
}

/// W9: an array whose elements all read as numbers is written inline with no spaces.
///
/// Why: `ParamRawArray::Save` (#L563-L576).
#[test]
fn w9_numeric_arrays_are_inline() {
    let items = vec![
        ItemModel::Scalar(ScalarModel::Float(1.5)),
        int(0),
        ItemModel::Scalar(ScalarModel::Bool(true)),
    ];
    assert_eq!(
        write(&[array("position", items)]),
        b"position[]={1.500000,0,1};\r\n"
    );
}

/// W9b: an array with a non-numeric element is written one element per line, with `,` on all but the last.
///
/// Why: `ParamRawArray::Save` (#L544-L562).
#[test]
fn w9b_string_arrays_are_multi_line() {
    let items = vec![
        ItemModel::Scalar(text("pack_a")),
        ItemModel::Scalar(text("pack_b")),
    ];
    let out = write(&[class("Mission", vec![array("addOns", items)])]);
    assert_eq!(out, b"class Mission\r\n{\r\n\taddOns[]=\r\n\t{\r\n\t\t\"pack_a\",\r\n\t\t\"pack_b\"\r\n\t};\r\n};\r\n");
}

/// W9c: strings that read as numbers keep the array inline, still quoted.
///
/// Why: the test is `IsNumerical(GetValue())`, not the element type (#L333-L342, #L536-L543).
#[test]
fn w9c_numeric_looking_strings_stay_inline() {
    assert_eq!(
        write(&[array("markers", vec![ItemModel::Scalar(text("1"))])]),
        b"markers[]={\"1\"};\r\n"
    );
}

/// W9d: the empty array is `{}`.
///
/// Why: no element is a string, so the inline branch writes just the braces.
#[test]
fn w9d_empty_array() {
    assert_eq!(write(&[array("addOns", vec![])]), b"addOns[]={};\r\n");
}

/// W9e: a sub-array inside a multi-line array is saved at its parent's indent, which gives the engine's odd line.
///
/// Why: `ParamArrayValueArray::Save` passes the parent's `indent` (`ParamFile.cpp#L1078-L1081`).
#[test]
fn w9e_nested_multi_line_sub_array() {
    let items = vec![
        ItemModel::Scalar(text("a")),
        ItemModel::Array(vec![int(1), int(2)]),
        ItemModel::Array(vec![ItemModel::Scalar(text("b"))]),
    ];
    let out = write(&[class("C", vec![array("arr", items)])]);
    let expected: &[u8] = b"class C\r\n{\r\n\
        \tarr[]=\r\n\t{\r\n\t\t\"a\",\r\n\t\t{1,2},\r\n\t\t\r\n\t{\r\n\t\t\"b\"\r\n\t}\r\n\t};\r\n};\r\n";
    assert_eq!(out, expected);
}

/// W10: entries are written in insertion order.
///
/// Why: the engine iterates its entry list in order (`ParamFile::Save`, #L873-L879); `version` first in missions.
#[test]
fn w10_insertion_order() {
    let out = write(&[
        value("zeta", ScalarModel::Int(1)),
        value("alpha", ScalarModel::Int(2)),
    ]);
    assert_eq!(out, b"zeta=1;\r\nalpha=2;\r\n");
}

// ── Error field & Display verification ───────────────────────────────────────────────────────────────────────────

/// Names outside `[A-Za-z0-9_]*`, strings with line breaks and NUL, and over-deep models are refused.
///
/// Why: the writer is stricter than the engine so its output always reads back to the same model.
#[test]
fn writer_refuses_unreadable_output() {
    let err = write_entries(
        &[value("bad name", ScalarModel::Int(1))],
        WriterProfile::Legacy196Text,
    )
    .unwrap_err();
    assert_eq!(
        err,
        Error::InvalidLexeme {
            context: "value name",
            offset_in_lexeme: 3,
            byte: b' '
        }
    );
    let err = write_entries(&[value("s", text("a\nb"))], WriterProfile::Legacy196Text).unwrap_err();
    assert_eq!(err, Error::NewlineInQuotedValue { offset_in_value: 1 });
    let mut deep = value("v", ScalarModel::Int(1));
    for _ in 0..65 {
        deep = class("c", vec![deep]);
    }
    let err = write_entries(&[deep], WriterProfile::Legacy196Text).unwrap_err();
    assert_eq!(err, Error::EmitTooDeep { depth: 65, cap: 64 });
    // An empty name is allowed: the game reads `=1;` back as an entry named "".
    assert_eq!(write(&[value("", ScalarModel::Int(1))]), b"=1;\r\n");
}

// ── Determinism ──────────────────────────────────────────────────────────────────────────────────────────────────

/// Writing the same model twice gives the same bytes.
///
/// Why: saves must be reproducible (diffs, content hashes).
#[test]
fn writing_is_deterministic() {
    let model = [class(
        "A",
        vec![
            value("f", ScalarModel::Float(0.1)),
            array("a", vec![int(1), ItemModel::Scalar(text("x"))]),
        ],
    )];
    let first = write_entries(&model, WriterProfile::RemasteredText).unwrap();
    let second = write_entries(&model, WriterProfile::RemasteredText).unwrap();
    assert_eq!(first, second);
}
