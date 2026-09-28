// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: Bohemia Interactive a.s. (original C++)
// SPDX-FileCopyrightText: 2026 Plotroom contributors (Rust translation)
// Derived-From: BohemiaInteractive/CWR@ffc61838b7:tests/unit/engine/Poseidon/IO/ParamFile/test_paramfile.cpp
// Derived-From: ofpisnotdead-com/CWR-CE@b67bf3bd62:tests/unit/engine/Poseidon/IO/ParamFile/test_paramfile.cpp
// Derived-From: ofpisnotdead-com/CWR-CE@b67bf3bd62:tests/unit/engine/Poseidon/IO/ParamFile/test_paramfile_parsing.cpp
// Modified: translated to Rust and changed, 2026-09-28. Subject to the Additional Terms
// (GPLv3 section 7) from Bohemia Interactive reproduced in NOTICE.
//! Port of the text-save cases of `test_paramfile.cpp` (`L734-L1037`, and the "Edge cases" test `L633-L681`) and of
//! the save case in `test_paramfile_parsing.cpp` ("Fixture file I/O", `L983-L1023`).
//!
//! **How the port maps.** Upstream builds a `ParamFile` with `Add`/`AddClass`/`AddArray`, calls `Save`, and checks
//! with `strstr` that fragments appear. Here the same model is built with [`plotroom_config::EntryModel`], written
//! by [`plotroom_config::write_entries`] (the port of the engine's `Save`), and checked against the exact bytes the
//! engine's writer produces (strengthened from `strstr`); every output is also parsed back. The profile is
//! `RemasteredText`, the writer the upstream tests exercise. The tree-API cases of that file (add, find, delete,
//! update, compact) belong to the resolved view and are not ported yet.

use plotroom_config::{
    ClassModel, EntryModel, ItemModel, ScalarModel, WriterProfile, lint_syntax, parse,
    write_entries,
};

#[cfg(test)]
mod support {
    use super::*;

    pub fn text(content: &str) -> ScalarModel {
        ScalarModel::Text(content.as_bytes().to_vec())
    }

    pub fn value(name: &str, value: ScalarModel) -> EntryModel {
        EntryModel::Value {
            name: name.as_bytes().to_vec(),
            value,
        }
    }

    pub fn class(name: &str, entries: Vec<EntryModel>) -> EntryModel {
        EntryModel::Class(ClassModel {
            name: name.as_bytes().to_vec(),
            base: None,
            entries,
        })
    }

    pub fn array(name: &str, items: Vec<ItemModel>) -> EntryModel {
        EntryModel::Array {
            name: name.as_bytes().to_vec(),
            items,
        }
    }

    pub fn strings(items: &[&str]) -> Vec<ItemModel> {
        items
            .iter()
            .map(|item| ItemModel::Scalar(text(item)))
            .collect()
    }

    /// Saves with the remastered writer and checks the output reads back cleanly.
    pub fn save(entries: &[EntryModel]) -> Vec<u8> {
        let out = write_entries(entries, WriterProfile::RemasteredText).unwrap();
        let cst = parse(&out).unwrap();
        assert_eq!(cst.render(), out);
        assert!(
            lint_syntax(&cst).is_empty(),
            "{}",
            String::from_utf8_lossy(&out)
        );
        out
    }
}

use support::*;

// ── Known-value cross-validation ─────────────────────────────────────────────────────────────────────────────────

/// Upstream `TEST_CASE("ParamFile - Save to text format")`, section "Save simple values".
///
/// Why: values are `name=value;` CR LF, strings quoted, floats `%f` (3.14f round-trips, so no `%.9g`).
#[test]
#[expect(
    clippy::approx_constant,
    reason = "3.14 is the upstream test's input value, not an approximation of pi"
)]
fn save_simple_values() {
    let out = save(&[
        value("stringValue", text("Test String")),
        value("intValue", ScalarModel::Int(42)),
        value("floatValue", ScalarModel::Float(3.14)),
    ]);
    assert_eq!(
        out,
        b"stringValue=\"Test String\";\r\nintValue=42;\r\nfloatValue=3.140000;\r\n"
    );
}

/// Upstream `TEST_CASE("ParamFile - Save to text format")`, section "Save nested class structure".
///
/// Why: the writer must lay out text exactly as the engine's `Save` does (doc 04 §2.2).
#[test]
fn save_nested_class_structure() {
    let out = save(&[class(
        "Config",
        vec![
            value("option1", text("value1")),
            value("option2", ScalarModel::Int(123)),
            class("Nested", vec![value("nestedValue", text("deep"))]),
        ],
    )]);
    let expected: &[u8] = b"class Config\r\n{\r\n\toption1=\"value1\";\r\n\toption2=123;\r\n\
        \tclass Nested\r\n\t{\r\n\t\tnestedValue=\"deep\";\r\n\t};\r\n};\r\n";
    assert_eq!(out, expected);
}

/// Upstream `TEST_CASE("ParamFile - Save to text format")`, section "Save arrays".
///
/// Why: the writer must lay out text exactly as the engine's `Save` does (doc 04 §2.2).
#[test]
fn save_arrays() {
    let items = [1, 2, 3]
        .into_iter()
        .map(|n| ItemModel::Scalar(ScalarModel::Int(n)))
        .collect();
    assert_eq!(
        save(&[array("testArray", items)]),
        b"testArray[]={1,2,3};\r\n"
    );
}

/// Upstream `TEST_CASE("ParamFile - Save to text format")`, section "Save complex game-like config".
///
/// Why: `%f` of 0.1f (`0.100000`) reads back as the same float, so CWR's writer keeps it and does not fall back
/// to `%.9g` (`ParamFileParse.cpp#L371-L388`); string arrays are written one element per line.
#[test]
fn save_complex_game_like_config() {
    let rifle = class(
        "SyntheticRifle",
        vec![
            value("displayName", text("SyntheticRifle Rifle")),
            value("reloadTime", ScalarModel::Float(0.1)),
            value("ammo", ScalarModel::Int(30)),
            array(
                "magazines",
                strings(&["SyntheticMagazine", "SyntheticMagazineTracer"]),
            ),
        ],
    );
    let out = save(&[class("CfgWeapons", vec![rifle])]);
    let expected: &[u8] = b"class CfgWeapons\r\n{\r\n\tclass SyntheticRifle\r\n\t{\r\n\
        \t\tdisplayName=\"SyntheticRifle Rifle\";\r\n\t\treloadTime=0.100000;\r\n\t\tammo=30;\r\n\
        \t\tmagazines[]=\r\n\t\t{\r\n\t\t\t\"SyntheticMagazine\",\r\n\t\t\t\"SyntheticMagazineTracer\"\r\n\t\t};\r\n\
        \t};\r\n};\r\n";
    assert_eq!(out, expected);
}

/// Upstream `TEST_CASE("ParamFile - Save and compare against expected")`, section "Build config matching game
/// settings format".
///
/// Why: numeric-looking strings stay quoted; 7.5 is exact in `%f`.
#[test]
fn save_game_settings_format() {
    let out = save(&[
        value("Product", text("CWACE")),
        value("Language", text("English")),
        value("Resolution_W", text("1920")),
        value("Resolution_H", text("1080")),
        value("LOD", ScalarModel::Float(7.5)),
        value("MaxObjects", ScalarModel::Int(256)),
    ]);
    assert_eq!(
        out,
        b"Product=\"CWACE\";\r\nLanguage=\"English\";\r\nResolution_W=\"1920\";\r\nResolution_H=\"1080\";\r\nLOD=7.500000;\r\nMaxObjects=256;\r\n"
    );
}

/// Upstream `TEST_CASE("ParamFile - Save and compare against expected")`, section "Build addon config structure".
///
/// Why: an empty array is `{}`, an empty class keeps its braces, backslashes are written raw, and 1.1f stays `%f`.
#[test]
fn save_addon_config_structure() {
    let patches = class(
        "CfgPatches",
        vec![class(
            "AH64",
            vec![
                value("requiredVersion", ScalarModel::Float(1.1)),
                array("units", strings(&["AH64"])),
                array("weapons", vec![]),
            ],
        )],
    );
    let ammo = class(
        "CfgAmmo",
        vec![
            class("Default", vec![]),
            class(
                "HellfireApach",
                vec![
                    value("model", text("\\Apac\\hellfire")),
                    value("hit", ScalarModel::Int(300)),
                    value("indirectHit", ScalarModel::Int(50)),
                ],
            ),
        ],
    );
    let out = save(&[patches, ammo]);
    let expected: &[u8] =
        b"class CfgPatches\r\n{\r\n\tclass AH64\r\n\t{\r\n\t\trequiredVersion=1.100000;\r\n\
        \t\tunits[]=\r\n\t\t{\r\n\t\t\t\"AH64\"\r\n\t\t};\r\n\t\tweapons[]={};\r\n\t};\r\n};\r\n\
        class CfgAmmo\r\n{\r\n\tclass Default\r\n\t{\r\n\t};\r\n\tclass HellfireApach\r\n\t{\r\n\
        \t\tmodel=\"\\Apac\\hellfire\";\r\n\t\thit=300;\r\n\t\tindirectHit=50;\r\n\t};\r\n};\r\n";
    assert_eq!(out, expected);
}

/// Upstream `TEST_CASE("ParamFile - Round-trip: Build, save, parse manually")`, sections "Simple config round-trip
/// verification" and "Complex nested config preserves structure".
///
/// Why: upstream could not parse its output back (no preprocessor in its test setup); here the output is parsed
/// and the nesting order checked through the tree.
#[test]
#[expect(
    clippy::approx_constant,
    reason = "3.14 is the upstream test's input value, not an approximation of pi"
)]
fn round_trip_build_save_parse() {
    let out = save(&[
        value("testKey", text("testValue")),
        value("number", ScalarModel::Int(42)),
    ]);
    assert_eq!(out, b"testKey=\"testValue\";\r\nnumber=42;\r\n");
    let out = save(&[class(
        "Level1",
        vec![
            value("L1_Value", text("First")),
            class(
                "Level2",
                vec![
                    value("L2_Value", ScalarModel::Int(123)),
                    class("Level3", vec![value("L3_Value", ScalarModel::Float(3.14))]),
                ],
            ),
        ],
    )]);
    let cst = parse(&out).unwrap();
    assert!(
        cst.find(&[b"Level1", b"Level2", b"Level3", b"L3_Value"])
            .is_some()
    );
    let find = |needle: &[u8]| out.windows(needle.len()).position(|w| w == needle).unwrap();
    assert!(
        find(b"class Level1") < find(b"class Level2")
            && find(b"class Level2") < find(b"class Level3")
    );
}

/// Upstream `TEST_CASE("ParamFile - Save formatting and indentation")`, sections "Nested classes are indented" and
/// "Arrays are formatted correctly".
///
/// Why: the writer must lay out text exactly as the engine's `Save` does (doc 04 §2.2).
#[test]
fn save_formatting_and_indentation() {
    let out = save(&[class(
        "Outer",
        vec![class("Inner", vec![value("value", text("test"))])],
    )]);
    assert_eq!(
        out,
        b"class Outer\r\n{\r\n\tclass Inner\r\n\t{\r\n\t\tvalue=\"test\";\r\n\t};\r\n};\r\n"
    );
    let numbers = [1, 2, 3]
        .into_iter()
        .map(|n| ItemModel::Scalar(ScalarModel::Int(n)))
        .collect();
    let out = save(&[
        array("numbers", numbers),
        array("names", strings(&["Alpha", "Bravo"])),
    ]);
    assert_eq!(
        out,
        b"numbers[]={1,2,3};\r\nnames[]=\r\n{\r\n\t\"Alpha\",\r\n\t\"Bravo\"\r\n};\r\n"
    );
}

/// Upstream `TEST_CASE("ParamFile - Edge cases")`, sections "Empty string name", "Very long names", "Special
/// characters in names" and "Null or empty values".
///
/// Why: an empty name and a 1023-byte name write and read back; empty strings and zeros are values.
#[test]
fn edge_cases() {
    let out = save(&[value("", text("value"))]);
    assert_eq!(out, b"=\"value\";\r\n");
    assert!(parse(&out).unwrap().find(&[b""]).is_some());
    let long = "A".repeat(1023);
    let out = save(&[value(&long, text("value"))]);
    assert!(parse(&out).unwrap().find(&[long.as_bytes()]).is_some());
    let out = save(&[
        value("name_with_underscores", text("test")),
        value("name123", text("test")),
    ]);
    let cst = parse(&out).unwrap();
    assert!(cst.find(&[b"name_with_underscores"]).is_some() && cst.find(&[b"name123"]).is_some());
    let out = save(&[
        value("emptyString", text("")),
        value("zeroInt", ScalarModel::Int(0)),
        value("zeroFloat", ScalarModel::Float(0.0)),
    ]);
    assert_eq!(
        out,
        b"emptyString=\"\";\r\nzeroInt=0;\r\nzeroFloat=0.000000;\r\n"
    );
}

/// Upstream `test_paramfile_parsing.cpp` `TEST_CASE("ParamFile - Fixture file I/O")`, section "Save to file and
/// verify" (upstream only checked that the file is non-empty).
///
/// Why: the writer must lay out text exactly as the engine's `Save` does (doc 04 §2.2).
#[test]
#[expect(
    clippy::approx_constant,
    reason = "3.14 is the upstream test's input value, not an approximation of pi"
)]
fn fixture_file_io_save() {
    let out = save(&[
        value("testValue", text("Hello World")),
        value("testInt", ScalarModel::Int(42)),
        value("testFloat", ScalarModel::Float(3.14)),
    ]);
    assert_eq!(
        out,
        b"testValue=\"Hello World\";\r\ntestInt=42;\r\ntestFloat=3.140000;\r\n"
    );
}
