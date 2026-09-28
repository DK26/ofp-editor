// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: Bohemia Interactive a.s. (original C++ tests and fixtures)
// SPDX-FileCopyrightText: 2026 Plotroom contributors (Rust translation)
// Derived-From: ofpisnotdead-com/CWR-CE@b67bf3bd62:tests/fixtures/config/
// Derived-From: ofpisnotdead-com/CWR-CE@b67bf3bd62:tests/unit/engine/Poseidon/IO/ParamFile/test_paramfile_parsing.cpp
// Derived-From: ofpisnotdead-com/CWR-CE@b67bf3bd62:tests/unit/engine/Poseidon/IO/ParamFile/test_paramfile_realworld.cpp
// Modified: translated to Rust and changed, 2026-09-28. Subject to the Additional Terms
// (GPLv3 section 7) from Bohemia Interactive reproduced in NOTICE.
//! The upstream config fixtures: byte-exact round trips, plus the fixture-load cases of the parsing and real-world
//! test files.
//!
//! **Provenance.** `tests/fixtures/upstream-config/*.txt` are copied verbatim (LF line ends, no BOM) from
//! `ofpisnotdead-com/CWR-CE@b67bf3bd62:tests/fixtures/config/`; each file is byte-identical to
//! `BohemiaInteractive/CWR@ffc61838b7:tests/fixtures/config/`. They are authored synthetic text (upstream
//! `tests/fixtures/ASSET_SOURCES.md` requires fixtures to be authored, not copied from game data), redistributed under
//! GPL-3.0-or-later with Bohemia's section 7 terms (`NOTICE`). SHA-256 of each copy:
//!
//! | File | SHA-256 |
//! | --- | --- |
//! | addon_config.txt | 89CDAD4BD80BA8E70367CE9ADEF67FCCE73F3DED969858A85A389B9C37977A86 |
//! | arrays.txt | DE4FD95EDE5DBE1072D486F6CEF174C158649018117D86E6528177B8AD10E3B9 |
//! | comments.txt | E520597EEFEB8FBE1DD02CF8FF271F958F2EA38E77E6D76FC9766E5F2010D857 |
//! | config_strings.txt | 8FB97801D877F808960F46F16EDE3FACBB5BF71805E386019DF28F88087E819B |
//! | description_ext.txt | 132AFF682D9A4FCA41ACFF0B6CA8B9C6F3D412B89AE1698015DF0A1AE8F0661D |
//! | inheritance.txt | E6624D91AB7644EA5A0796F62A2EFFBE2B3934A7F93ACC6C3B89FE5163CB6DB7 |
//! | nested.txt | 94356B3CBA977680581ACDE0A4F13A9D96F3424BF049A9E709BD804996E9435C |
//! | simple.txt | DC000BA2CCFAE64A9E5596538EBADC2A6066BCF41F52BFEC5A22A82D7C5EE32A |
//! | vehicle_config.txt | D28F2D6CFC0B769E0D4462CE09148C2E2A8D823E35DE4C2363BFFDCB481B6D6E |
//! | weapon_config.txt | E730007E98909694C77AB6424EE2876FA8938FAF9103E30AF84A6019A11CCAD4 |
//!
//! The fixtures are embedded with `include_bytes!` at compile time, so the tests read no files at run time.

use plotroom_config::{ConfigCst, Entry, IssueKind, Scalar, lint_syntax, parse};

/// Every fixture, by file name.
const FIXTURES: [(&str, &[u8]); 10] = [
    (
        "addon_config.txt",
        include_bytes!("fixtures/upstream-config/addon_config.txt"),
    ),
    (
        "arrays.txt",
        include_bytes!("fixtures/upstream-config/arrays.txt"),
    ),
    (
        "comments.txt",
        include_bytes!("fixtures/upstream-config/comments.txt"),
    ),
    (
        "config_strings.txt",
        include_bytes!("fixtures/upstream-config/config_strings.txt"),
    ),
    (
        "description_ext.txt",
        include_bytes!("fixtures/upstream-config/description_ext.txt"),
    ),
    (
        "inheritance.txt",
        include_bytes!("fixtures/upstream-config/inheritance.txt"),
    ),
    (
        "nested.txt",
        include_bytes!("fixtures/upstream-config/nested.txt"),
    ),
    (
        "simple.txt",
        include_bytes!("fixtures/upstream-config/simple.txt"),
    ),
    (
        "vehicle_config.txt",
        include_bytes!("fixtures/upstream-config/vehicle_config.txt"),
    ),
    (
        "weapon_config.txt",
        include_bytes!("fixtures/upstream-config/weapon_config.txt"),
    ),
];

#[cfg(test)]
mod support {
    use super::*;

    pub fn fixture(name: &str) -> ConfigCst {
        let (_, bytes) = FIXTURES.iter().find(|(file, _)| *file == name).unwrap();
        let cst = parse(bytes).unwrap();
        assert_eq!(cst.render(), *bytes);
        cst
    }

    pub fn has_class(cst: &ConfigCst, path: &[&[u8]]) -> bool {
        matches!(cst.find(path), Some(Entry::Class(_)))
    }

    pub fn text(cst: &ConfigCst, path: &[&[u8]]) -> Vec<u8> {
        match cst.find(path) {
            Some(Entry::Value(entry)) => entry.value().unwrap().text(),
            other => panic!("no value at {path:?}: {other:?}"),
        }
    }

    pub fn scalar(cst: &ConfigCst, path: &[&[u8]]) -> Scalar {
        match cst.find(path) {
            Some(Entry::Value(entry)) => entry.value().unwrap().scalar(),
            other => panic!("no value at {path:?}: {other:?}"),
        }
    }
}

use support::*;

// ── Known-value cross-validation ─────────────────────────────────────────────────────────────────────────────────

/// Every upstream config fixture round-trips byte for byte, and parsing it twice gives the same tree.
///
/// Why: upstream's fixture loads only checked "no crash" (`REQUIRE(result == LSOK || result != LSOK)`); the
/// round trip is the stronger, checkable property (core-document-model §12 R1).
#[test]
fn every_upstream_fixture_round_trips() {
    for (name, bytes) in FIXTURES {
        let first = parse(bytes).unwrap();
        assert_eq!(first.render(), bytes, "{name}");
        assert_eq!(
            parse(bytes).unwrap().debug_tree(),
            first.debug_tree(),
            "{name}"
        );
    }
}

/// `test_paramfile_parsing.cpp` fixture loads (`L899-L981`): simple, arrays, nested, inheritance and comments.
///
/// Why: file loads are preprocessed, so the comments fixture defines both values (upstream expected failure for a
/// raw-stream parse); `testBool = true` stays a string (`true` is not a number to the engine).
#[test]
fn parsing_fixture_loads() {
    let simple = fixture("simple.txt");
    assert_eq!(text(&simple, &[b"testString"]), b"Hello World");
    assert_eq!(scalar(&simple, &[b"testInt"]), Scalar::Int(42));
    assert_eq!(scalar(&simple, &[b"testBool"]), Scalar::Text);
    let arrays = fixture("arrays.txt");
    let Some(Entry::Array(mixed)) = arrays.find(&[b"mixed"]) else {
        panic!("mixed")
    };
    assert_eq!(mixed.items().len(), 4);
    let nested = fixture("nested.txt");
    assert_eq!(
        text(&nested, &[b"Config", b"Video", b"resolution"]),
        b"1920x1080"
    );
    assert!(has_class(&nested, &[b"GameSettings"]));
    let inheritance = fixture("inheritance.txt");
    let Some(Entry::Class(more)) = inheritance.find(&[b"MoreDerived"]) else {
        panic!("MoreDerived")
    };
    assert_eq!(more.base(), Some(b"Derived".to_vec()));
    let comments = fixture("comments.txt");
    assert_eq!(scalar(&comments, &[b"value1"]), Scalar::Int(123));
    assert_eq!(scalar(&comments, &[b"value2"]), Scalar::Int(456));
    for cst in [simple, arrays, nested, inheritance, comments] {
        assert!(lint_syntax(&cst).is_empty());
    }
}

/// `test_paramfile_realworld.cpp` `TEST_CASE("ParamFile - Load description.ext fixture")`.
///
/// Why: the fixture load must give the upstream values (`respawn`, `onLoadName`, the `Params` classes) from the
/// lossless tree, with a clean lint.
#[test]
fn realworld_description_ext_fixture() {
    let cst = fixture("description_ext.txt");
    assert!(lint_syntax(&cst).is_empty());
    assert_eq!(scalar(&cst, &[b"respawn"]), Scalar::Int(3));
    assert_eq!(text(&cst, &[b"onLoadName"]), b"Defend Petrovice");
    assert_eq!(text(&cst, &[b"author"]), b"Synthetic Fixture Suite");
    assert_eq!(scalar(&cst, &[b"Header", b"maxPlayers"]), Scalar::Int(12));
    for name in [&b"TimeOfDay"[..], b"Weather", b"Difficulty"] {
        assert!(has_class(&cst, &[b"Params", name]));
    }
    assert!(has_class(&cst, &[b"CfgRadio"]));
}

/// `test_paramfile_realworld.cpp` `TEST_CASE("ParamFile - Load weapon config fixture")`.
///
/// Why, and one source-derived correction: upstream asserts `m16->GetClass("Burst") != nullptr`, which cannot fail,
/// because `GetClass` returns an error sentinel, never null (`ParamFile.cpp#L1320-L1330`). In the fixture,
/// `class Burst` follows `burst = 3;` in the same class, names compare case-insensitively (`strcmpi`,
/// `#L1213-L1227`), so the game drops the class as "Member already defined" (`#L1849-L1866`) and `Burst` finds the
/// value. unverified-1.99.
#[test]
fn realworld_weapon_config_fixture() {
    let cst = fixture("weapon_config.txt");
    let issues = lint_syntax(&cst);
    assert_eq!(
        issues.iter().map(|issue| issue.kind()).collect::<Vec<_>>(),
        [IssueKind::DuplicateMember]
    );
    assert!(
        has_class(&cst, &[b"CfgWeapons", b"Default"])
            && has_class(&cst, &[b"CfgWeapons", b"Rifle"])
    );
    assert_eq!(
        text(&cst, &[b"CfgWeapons", b"SyntheticRifle", b"displayName"]),
        b"SyntheticRifle"
    );
    for mode in [&b"Single"[..], b"FullAuto"] {
        assert!(has_class(&cst, &[b"CfgWeapons", b"SyntheticRifle", mode]));
    }
    assert_eq!(
        scalar(&cst, &[b"CfgWeapons", b"SyntheticRifle", b"Burst"]),
        Scalar::Int(3)
    );
    assert_eq!(
        text(&cst, &[b"CfgWeapons", b"SyntheticSupport", b"displayName"]),
        b"SyntheticSupport"
    );
    assert_eq!(
        text(&cst, &[b"CfgWeapons", b"SyntheticLauncher", b"displayName"]),
        b"Synthetic Launcher"
    );
    for name in [&b"Binocular"[..], b"Throw", b"Put"] {
        assert!(has_class(&cst, &[b"CfgWeapons", name]));
    }
}

/// `test_paramfile_realworld.cpp` `TEST_CASE("ParamFile - Load vehicle config fixture")`.
///
/// Why: the largest fixture's nested classes and values must read as upstream expects, with a clean lint.
#[test]
fn realworld_vehicle_config_fixture() {
    let cst = fixture("vehicle_config.txt");
    assert!(lint_syntax(&cst).is_empty());
    for name in [&b"All"[..], b"AllVehicles", b"Land", b"Man"] {
        assert!(has_class(&cst, &[b"CfgVehicles", name]));
    }
    assert_eq!(
        text(
            &cst,
            &[b"CfgVehicles", b"SyntheticTankAlpha", b"displayName"]
        ),
        b"Synthetic Tank Alpha"
    );
    assert_eq!(
        scalar(&cst, &[b"CfgVehicles", b"SyntheticTankAlpha", b"armor"]),
        Scalar::Int(900)
    );
    assert!(matches!(
        cst.find(&[b"CfgVehicles", b"SyntheticTankAlpha", b"Turret", b"weapons"]),
        Some(Entry::Array(_))
    ));
    assert!(has_class(
        &cst,
        &[b"CfgVehicles", b"SyntheticTankAlpha", b"Damage"]
    ));
    assert_eq!(
        text(
            &cst,
            &[b"CfgVehicles", b"SyntheticTankBeta", b"displayName"]
        ),
        b"T-72"
    );
    assert_eq!(
        text(&cst, &[b"CfgVehicles", b"AH1Z", b"displayName"]),
        b"AH-1Z Viper"
    );
    assert!(
        has_class(&cst, &[b"CfgVehicles", b"AH1Z", b"Library"])
            && has_class(&cst, &[b"CfgVehicles", b"AH1Z", b"Turrets"])
    );
    assert_eq!(
        text(&cst, &[b"CfgVehicles", b"SyntheticHeli", b"displayName"]),
        b"Synthetic Utility Helicopter"
    );
    assert!(has_class(
        &cst,
        &[b"CfgVehicles", b"SyntheticHeli", b"Turrets", b"LeftDoorGun"]
    ));
    assert!(has_class(
        &cst,
        &[
            b"CfgVehicles",
            b"SyntheticHeli",
            b"Turrets",
            b"RightDoorGun"
        ]
    ));
}

/// The two fixtures no upstream test reads: `config_strings.txt` is clean (its `$STR_` values stay raw), and
/// `addon_config.txt` uses `class X;` forward declarations, which the game refuses.
///
/// Why: the CST keeps `$STR_` keys verbatim (D017 item 5), and the lint names the forward declarations that make the
/// game abandon the enclosing class (`ParamFile.cpp#L1632-L1641`).
#[test]
fn orphan_fixtures() {
    let strings = fixture("config_strings.txt");
    assert!(lint_syntax(&strings).is_empty());
    assert_eq!(
        text(&strings, &[b"CfgVehicles", b"Man", b"displayName"]),
        b"$STR_DN_MAN"
    );
    let addon = fixture("addon_config.txt");
    let kinds: Vec<IssueKind> = lint_syntax(&addon)
        .iter()
        .map(|issue| issue.kind())
        .collect();
    assert!(
        kinds.contains(&IssueKind::ForwardClassDeclaration),
        "{kinds:?}"
    );
}
