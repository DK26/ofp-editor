// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: Bohemia Interactive a.s. (original C++)
// SPDX-FileCopyrightText: 2026 Plotroom contributors (Rust translation)
// Derived-From: BohemiaInteractive/CWR@ffc61838b7:tests/unit/engine/Poseidon/IO/ParamFile/test_paramfile_realworld.cpp
// Derived-From: ofpisnotdead-com/CWR-CE@b67bf3bd62:tests/unit/engine/Poseidon/IO/ParamFile/test_paramfile_realworld.cpp
// Modified: translated to Rust and changed, 2026-09-28. Subject to the Additional Terms
// (GPLv3 section 7) from Bohemia Interactive reproduced in NOTICE.
//! Port of the inline cases of `test_paramfile_realworld.cpp` (sections 10.1 to 10.4; the three fixture loads of
//! section 10.5 are in `tests/upstream_fixtures.rs`).
//!
//! **How the port maps.** Same inputs; the same checks on the lossless tree: classes and entries found by path
//! (`GetClass`/`FindEntry` on a class's own entries), values' text and type, array element counts. Every input also
//! round-trips byte for byte and has no syntax issue.
//!
//! **Not ported yet.** Assertions that read an entry through inheritance (for example `m16->FindEntry("type")`,
//! "from Rifle base") need the resolved view: CSV fragment `#inheritance-lookup`, status `todo`. Several inputs use
//! Arma-era `description.ext` schema that 1.99 does not read (doc 20); they are grammar tests only, never schema
//! oracles.

use plotroom_config::{ConfigCst, Entry, Scalar, lint_syntax, parse};

#[cfg(test)]
mod support {
    use super::*;

    /// Parses, and asserts the round trip and a clean lint.
    pub fn parsed(text: &[u8]) -> ConfigCst {
        let cst = parse(text).unwrap();
        assert_eq!(cst.render(), text);
        let issues = lint_syntax(&cst);
        assert!(issues.is_empty(), "{issues:?}");
        cst
    }

    pub fn has_class(cst: &ConfigCst, path: &[&[u8]]) -> bool {
        matches!(cst.find(path), Some(Entry::Class(_)))
    }

    pub fn scalar(cst: &ConfigCst, path: &[&[u8]]) -> Scalar {
        match cst.find(path) {
            Some(Entry::Value(entry)) => entry.value().unwrap().scalar(),
            other => panic!("no value at {path:?}: {other:?}"),
        }
    }

    pub fn text(cst: &ConfigCst, path: &[&[u8]]) -> Vec<u8> {
        match cst.find(path) {
            Some(Entry::Value(entry)) => entry.value().unwrap().text(),
            other => panic!("no value at {path:?}: {other:?}"),
        }
    }

    /// The element count of the array at `path` (`IsArray()` and `GetSize()` upstream).
    pub fn size(cst: &ConfigCst, path: &[&[u8]]) -> usize {
        match cst.find(path) {
            Some(Entry::Array(entry)) => entry.items().len(),
            other => panic!("no array at {path:?}: {other:?}"),
        }
    }
}

use support::*;

// ── Known-value cross-validation: section 10.1, mission configuration ───────────────────────────────────────────

/// Upstream `TEST_CASE("ParamFile - Simple mission description.ext")`, section "Basic mission settings".
///
/// Why: a real-world config shape must round-trip exactly and read as upstream expects (D013).
#[test]
fn simple_mission_description() {
    let cst = parsed(b"onLoadMission = \"Defend the base\";\nonLoadIntro = \"Synthetic Fixture Suite\";\nbriefingName = \"First Mission\";\noverviewText = \"Your first mission in Synthetic\";\ndebriefing = 1;\nrespawn = 3;\nrespawnDelay = 10;\n");
    assert!(cst.find(&[b"onLoadMission"]).is_some());
    assert_eq!(text(&cst, &[b"briefingName"]), b"First Mission");
    assert_eq!(scalar(&cst, &[b"respawn"]), Scalar::Int(3));
    assert_eq!(scalar(&cst, &[b"respawnDelay"]), Scalar::Int(10));
}

/// Upstream `TEST_CASE("ParamFile - Mission with class definitions")`, section "CfgRadio and CfgMusic classes".
///
/// Why: `db+0` and `db+10` are bare array elements typed as floats; the arrays keep their three elements.
#[test]
fn mission_with_class_definitions() {
    let cst = parsed(b"class CfgRadio {\n    class RadioMsg1 {\n        name = \"\";\n        sound[] = {\"radio1.ogg\", db+0, 1.0};\n        title = \"Radio message 1\";\n    };\n};\nclass CfgMusic {\n    tracks[] = {};\n    class MusicTrack1 {\n        name = \"Track 1\";\n        sound[] = {\"music\\track1.ogg\", db+10, 1.0};\n    };\n};\n");
    assert_eq!(size(&cst, &[b"CfgRadio", b"RadioMsg1", b"sound"]), 3);
    assert_eq!(size(&cst, &[b"CfgMusic", b"MusicTrack1", b"sound"]), 3);
}

/// Upstream `TEST_CASE("ParamFile - Mission respawn settings")`, section "Various respawn modes".
///
/// Why: a real-world config shape must round-trip exactly and read as upstream expects (D013).
#[test]
fn mission_respawn_settings() {
    let cst = parsed(b"respawn = \"BASE\";\nrespawnDelay = 5;\nrespawnDialog = 1;\nrespawnVehicleDelay = 10;\nclass RespawnTemplates {\n    class MenuPosition {};\n    class MenuInventory {};\n};\n");
    assert_eq!(text(&cst, &[b"respawn"]), b"BASE");
    assert!(has_class(&cst, &[b"RespawnTemplates", b"MenuPosition"]));
}

/// Upstream `TEST_CASE("ParamFile - Mission parameters")`, section "Mission-specific params".
///
/// Why: a real-world config shape must round-trip exactly and read as upstream expects (D013).
#[test]
fn mission_parameters() {
    let cst = parsed(b"class Params {\n    class TimeOfDay {\n        title = \"Time of Day\";\n        values[] = {6, 12, 18};\n        texts[] = {\"Morning\", \"Noon\", \"Evening\"};\n        default = 12;\n    };\n    class Weather {\n        title = \"Weather\";\n        values[] = {0, 1};\n        texts[] = {\"Clear\", \"Overcast\"};\n        default = 0;\n    };\n};\n");
    assert!(has_class(&cst, &[b"Params", b"Weather"]));
    assert_eq!(size(&cst, &[b"Params", b"TimeOfDay", b"values"]), 3);
    assert_eq!(size(&cst, &[b"Params", b"TimeOfDay", b"texts"]), 3);
}

/// Upstream `TEST_CASE("ParamFile - Mission header")`, section "Header with metadata".
///
/// Why: `gameType = Coop;` is a bare word the game keeps as a string.
#[test]
fn mission_header() {
    let cst = parsed(b"class Header {\n    gameType = Coop;\n    minPlayers = 1;\n    maxPlayers = 16;\n};\nauthor = \"Player Name\";\nonLoadName = \"Mission Name\";\nonLoadMission = \"Mission Description\";\n");
    assert_eq!(scalar(&cst, &[b"Header", b"gameType"]), Scalar::Text);
    assert_eq!(scalar(&cst, &[b"Header", b"minPlayers"]), Scalar::Int(1));
    assert_eq!(scalar(&cst, &[b"Header", b"maxPlayers"]), Scalar::Int(16));
}

/// Upstream `TEST_CASE("ParamFile - Mission difficulty settings")`, section "Difficulty modifiers".
///
/// Why: a real-world config shape must round-trip exactly and read as upstream expects (D013).
#[test]
fn mission_difficulty_settings() {
    let cst = parsed(b"class DifficultyPresets {\n    class Regular {\n        class Options {\n            reducedDamage = 0;\n            groupIndicators = 1;\n            friendlyTags = 1;\n            enemyTags = 0;\n        };\n    };\n};\n");
    assert_eq!(
        scalar(
            &cst,
            &[
                b"DifficultyPresets",
                b"Regular",
                b"Options",
                b"reducedDamage"
            ]
        ),
        Scalar::Int(0)
    );
    assert_eq!(
        scalar(
            &cst,
            &[
                b"DifficultyPresets",
                b"Regular",
                b"Options",
                b"groupIndicators"
            ]
        ),
        Scalar::Int(1)
    );
}

/// Upstream `TEST_CASE("ParamFile - Mission briefing")`, section "Structured briefing".
///
/// Why: a real-world config shape must round-trip exactly and read as upstream expects (D013).
#[test]
fn mission_briefing() {
    let cst = parsed(b"class CfgBriefing {\n    class West {\n        title = \"USMC Forces\";\n        description = \"Mission briefing text\";\n    };\n    class East {\n        title = \"Soviet Forces\";\n        description = \"Enemy briefing\";\n    };\n};\n");
    assert_eq!(
        text(&cst, &[b"CfgBriefing", b"West", b"title"]),
        b"USMC Forces"
    );
    assert_eq!(
        text(&cst, &[b"CfgBriefing", b"East", b"title"]),
        b"Soviet Forces"
    );
}

/// Upstream `TEST_CASE("ParamFile - Complex mission config")`, section "Full-featured mission description.ext".
///
/// Why: a real-world config shape must round-trip exactly and read as upstream expects (D013).
#[test]
fn complex_mission_config() {
    let cst = parsed(b"respawn = 3;\nrespawnDelay = 10;\nonLoadName = \"Operation Thunder\";\nonLoadMission = \"Assault enemy positions\";\nauthor = \"Mission Designer\";\nclass Header {\n    gameType = Coop;\n    minPlayers = 4;\n    maxPlayers = 12;\n};\nclass Params {\n    class Difficulty {\n        title = \"AI Skill\";\n        values[] = {0, 1, 2};\n        texts[] = {\"Easy\", \"Normal\", \"Hard\"};\n        default = 1;\n    };\n};\nclass CfgRadio {\n    class BaseUnderAttack {\n        name = \"\";\n        sound[] = {\"radio\\baseattack.ogg\", db+5, 1.0};\n        title = \"Base under attack!\";\n    };\n};\n");
    assert!(cst.find(&[b"respawn"]).is_some() && cst.find(&[b"author"]).is_some());
    assert!(has_class(&cst, &[b"Header"]) && has_class(&cst, &[b"Params", b"Difficulty"]));
    assert!(has_class(&cst, &[b"CfgRadio", b"BaseUnderAttack"]));
}

// ── Known-value cross-validation: section 10.2, units and vehicles ──────────────────────────────────────────────

/// Upstream `TEST_CASE("ParamFile - Basic soldier config")`, section "Infantry unit definition" (own entries).
///
/// Why: a real-world config shape must round-trip exactly and read as upstream expects (D013).
#[test]
fn basic_soldier_config() {
    let cst = parsed(b"class CfgVehicles {\n    class All {};\n    class AllVehicles : All {};\n    class Land : AllVehicles {};\n    class Man : Land {\n        scope = 2;\n        vehicleClass = \"Men\";\n        displayName = \"Soldier\";\n        model = \"\\Synthetic\\soldiers\\soldierWB.p3d\";\n        weapons[] = {};\n        magazines[] = {};\n    };\n    class SyntheticSoldierWest : Man {\n        displayName = \"US Soldier\";\n        weapons[] = {\"SyntheticRifle\", \"Throw\", \"Put\"};\n        magazines[] = {\"SyntheticMagazine\", \"SyntheticMagazine\", \"SyntheticMagazine\", \"SyntheticMagazine\", \"HandGrenade\"};\n    };\n};\n");
    assert!(
        has_class(&cst, &[b"CfgVehicles", b"All"]) && has_class(&cst, &[b"CfgVehicles", b"Man"])
    );
    assert_eq!(
        size(&cst, &[b"CfgVehicles", b"SyntheticSoldierWest", b"weapons"]),
        3
    );
    assert_eq!(
        size(
            &cst,
            &[b"CfgVehicles", b"SyntheticSoldierWest", b"magazines"]
        ),
        5
    );
}

/// Upstream `TEST_CASE("ParamFile - Weapon configuration")`, section "CfgWeapons with rifle definition" (own
/// entries; the inherited `type` lookup is `#inheritance-lookup`).
///
/// Why: a real-world config shape must round-trip exactly and read as upstream expects (D013).
#[test]
fn weapon_configuration() {
    let cst = parsed(b"class CfgWeapons {\n    class Default {};\n    class Rifle : Default {\n        scope = 0;\n        type = 1;\n        reloadTime = 0.1;\n        magazineReloadTime = 3.0;\n    };\n    class SyntheticRifle : Rifle {\n        scope = 2;\n        displayName = \"SyntheticRifle\";\n        model = \"\\Synthetic\\weapons\\SyntheticMagazine\\SyntheticRifle.p3d\";\n        picture = \"\\Synthetic\\weapons\\SyntheticMagazine\\equip_SyntheticRifle.paa\";\n        magazines[] = {\"SyntheticMagazine\"};\n        reloadTime = 0.1;\n        magazineReloadTime = 3.6;\n        recoil = \"SyntheticRifleRecoil\";\n        recoilProne = \"SyntheticRifleRecoilProne\";\n    };\n};\n");
    assert_eq!(
        scalar(&cst, &[b"CfgWeapons", b"SyntheticRifle", b"scope"]),
        Scalar::Int(2)
    );
    assert_eq!(
        text(&cst, &[b"CfgWeapons", b"SyntheticRifle", b"displayName"]),
        b"SyntheticRifle"
    );
    assert_eq!(
        size(&cst, &[b"CfgWeapons", b"SyntheticRifle", b"magazines"]),
        1
    );
    assert!(cst.find(&[b"CfgWeapons", b"Rifle", b"type"]).is_some());
}

/// Upstream `TEST_CASE("ParamFile - Vehicle configuration")`, section "Tank definition with complex properties".
///
/// Why: a real-world config shape must round-trip exactly and read as upstream expects (D013).
#[test]
fn vehicle_configuration() {
    let cst = parsed(b"class CfgVehicles {\n    class AllVehicles {};\n    class Land : AllVehicles {};\n    class LandVehicle : Land {};\n    class Tank : LandVehicle {\n        scope = 0;\n        accuracy = 0.3;\n        armor = 400;\n        cost = 500000;\n    };\n    class SyntheticTankAlpha : Tank {\n        scope = 2;\n        displayName = \"Synthetic Tank Alpha\";\n        model = \"\\Synthetic\\vehicles\\m1abrams.p3d\";\n        armor = 900;\n        class Turret {\n            gunnerAction = \"M1Gunner\";\n            gunnerInAction = \"M1GunnerIn\";\n            weapons[] = {\"M256\"};\n            magazines[] = {\"M256_SABOT\", \"M256_HEAT\"};\n        };\n    };\n};\n");
    assert_eq!(
        scalar(&cst, &[b"CfgVehicles", b"SyntheticTankAlpha", b"armor"]),
        Scalar::Int(900)
    );
    assert_eq!(
        size(
            &cst,
            &[b"CfgVehicles", b"SyntheticTankAlpha", b"Turret", b"weapons"]
        ),
        1
    );
    assert_eq!(
        size(
            &cst,
            &[
                b"CfgVehicles",
                b"SyntheticTankAlpha",
                b"Turret",
                b"magazines"
            ]
        ),
        2
    );
}

/// Upstream `TEST_CASE("ParamFile - Aircraft configuration")`, section "Helicopter with multiple crew positions".
///
/// Why: a real-world config shape must round-trip exactly and read as upstream expects (D013).
#[test]
fn aircraft_configuration() {
    let cst = parsed(b"class CfgVehicles {\n    class Air {};\n    class Helicopter : Air {\n        scope = 0;\n        vehicleClass = \"Air\";\n    };\n    class AH1Z : Helicopter {\n        scope = 2;\n        displayName = \"AH-1Z Viper\";\n        model = \"\\Synthetic\\air\\ah1z.p3d\";\n        crew = \"HelicopterPilot\";\n        class Library {\n            libTextDesc = \"Attack helicopter\";\n        };\n        class Turrets {\n            class MainTurret {\n                weapons[] = {\"M197\", \"FFARLauncher\"};\n                magazines[] = {\"M197_750Rnd\", \"FFAR_19Rnd\"};\n            };\n        };\n    };\n};\n");
    assert!(has_class(&cst, &[b"CfgVehicles", b"AH1Z", b"Library"]));
    assert!(has_class(
        &cst,
        &[b"CfgVehicles", b"AH1Z", b"Turrets", b"MainTurret"]
    ));
}

/// Upstream `TEST_CASE("ParamFile - Ammunition configuration")`, section "CfgAmmo with bullet and explosive types".
///
/// Why: `airFriction = -0.001;` is a negative float.
#[test]
fn ammunition_configuration() {
    let cst = parsed(b"class CfgAmmo {\n    class Default {};\n    class BulletCore : Default {\n        simulation = \"shotBullet\";\n        hit = 10;\n        indirectHit = 0;\n        indirectHitRange = 0;\n    };\n    class B_556x45_Ball : BulletCore {\n        hit = 8;\n        typicalSpeed = 920;\n        airFriction = -0.001;\n        caliber = 1.0;\n    };\n    class GrenadeCore : Default {\n        simulation = \"shotShell\";\n        explosionEffects = \"GrenadeExplosion\";\n    };\n    class HandGrenade : GrenadeCore {\n        hit = 20;\n        indirectHit = 10;\n        indirectHitRange = 7;\n        explosive = 1;\n    };\n};\n");
    assert_eq!(
        scalar(&cst, &[b"CfgAmmo", b"B_556x45_Ball", b"hit"]),
        Scalar::Int(8)
    );
    assert_eq!(
        scalar(&cst, &[b"CfgAmmo", b"B_556x45_Ball", b"airFriction"]),
        Scalar::Float(-0.001)
    );
    assert_eq!(
        scalar(&cst, &[b"CfgAmmo", b"HandGrenade", b"explosive"]),
        Scalar::Int(1)
    );
}

/// Upstream `TEST_CASE("ParamFile - Magazine configuration")`, section "CfgMagazines with different ammo types".
///
/// Why: a real-world config shape must round-trip exactly and read as upstream expects (D013).
#[test]
fn magazine_configuration() {
    let cst = parsed(b"class CfgMagazines {\n    class Default {};\n    class CA_Magazine : Default {\n        scope = 0;\n        value = 1;\n        mass = 1;\n    };\n    class SyntheticMagazine : CA_Magazine {\n        scope = 2;\n        displayName = \"30Rnd STANAG\";\n        ammo = \"B_556x45_Ball\";\n        count = 30;\n        initSpeed = 920;\n        picture = \"\\Synthetic\\weapons\\data\\equip\\m_stanag.paa\";\n        model = \"\\Synthetic\\weapons\\mag_stanag.p3d\";\n    };\n};\n");
    assert_eq!(
        scalar(&cst, &[b"CfgMagazines", b"SyntheticMagazine", b"count"]),
        Scalar::Int(30)
    );
    assert_eq!(
        text(&cst, &[b"CfgMagazines", b"SyntheticMagazine", b"ammo"]),
        b"B_556x45_Ball"
    );
}

/// Upstream `TEST_CASE("ParamFile - Sound configuration")`, section "CfgSounds with weapon sounds".
///
/// Why: `sound[]` has four elements, `db+5` bare among them.
#[test]
fn sound_configuration() {
    let cst = parsed(b"class CfgSounds {\n    class SyntheticMagazineSingle {\n        name = \"SyntheticMagazine_single\";\n        sound[] = {\"\\Synthetic\\sounds\\m16single.wss\", db+5, 1.0, 900};\n        titles[] = {};\n    };\n    class SyntheticMagazineBurst {\n        name = \"SyntheticMagazine_burst\";\n        sound[] = {\"\\Synthetic\\sounds\\m16burst.wss\", db+5, 1.0, 900};\n        titles[] = {};\n    };\n};\n");
    assert_eq!(
        size(&cst, &[b"CfgSounds", b"SyntheticMagazineSingle", b"sound"]),
        4
    );
    assert_eq!(
        size(&cst, &[b"CfgSounds", b"SyntheticMagazineBurst", b"sound"]),
        4
    );
}

/// Upstream `TEST_CASE("ParamFile - Model configuration")`, section "CfgModels with LOD definitions".
///
/// Why: a real-world config shape must round-trip exactly and read as upstream expects (D013).
#[test]
fn model_configuration() {
    let cst = parsed(b"class CfgModels {\n    class Default {\n        sectionsInherit = \"\";\n        sections[] = {};\n    };\n    class soldierWB : Default {\n        sections[] = {\"head\", \"body\", \"weapon\"};\n        class Animations {\n            class head {\n                type = \"rotationY\";\n                source = \"aimY\";\n                selection = \"head\";\n                axis = \"axis_head\";\n            };\n        };\n    };\n};\n");
    assert_eq!(size(&cst, &[b"CfgModels", b"soldierWB", b"sections"]), 3);
    assert!(has_class(
        &cst,
        &[b"CfgModels", b"soldierWB", b"Animations", b"head"]
    ));
}

// ── Known-value cross-validation: section 10.3, addon patterns ──────────────────────────────────────────────────

/// Upstream `TEST_CASE("ParamFile - Addon config header")`, section "Standard addon header structure".
///
/// Why: a real-world config shape must round-trip exactly and read as upstream expects (D013).
#[test]
fn addon_config_header() {
    let cst = parsed(b"class CfgPatches {\n    class MyAddon {\n        units[] = {\"MyUnit1\", \"MyUnit2\"};\n        weapons[] = {};\n        requiredVersion = 1.85;\n        requiredAddons[] = {\"CARescue\"};\n    };\n};\n");
    assert_eq!(size(&cst, &[b"CfgPatches", b"MyAddon", b"units"]), 2);
    assert_eq!(
        scalar(&cst, &[b"CfgPatches", b"MyAddon", b"requiredVersion"]),
        Scalar::Float(1.85)
    );
}

/// Upstream `TEST_CASE("ParamFile - Faction configuration")`, section "CfgFactionClasses defining custom faction".
///
/// Why: a real-world config shape must round-trip exactly and read as upstream expects (D013).
#[test]
fn faction_configuration() {
    let cst = parsed(b"class CfgFactionClasses {\n    class CustomFaction {\n        displayName = \"Custom Forces\";\n        priority = 10;\n        side = 1;\n        icon = \"\\MyAddon\\data\\faction_icon.paa\";\n    };\n};\n");
    assert_eq!(
        scalar(&cst, &[b"CfgFactionClasses", b"CustomFaction", b"side"]),
        Scalar::Int(1)
    );
}

/// Upstream `TEST_CASE("ParamFile - External class references")`, section "Extending external configs".
///
/// Why: `class Man {};` (a defined empty class) is the working form; upstream notes `class Man;` is not.
#[test]
fn external_class_references() {
    let cst = parsed(b"class CfgVehicles {\n    class Man {};\n    class SyntheticSoldierWest : Man {\n        displayName = \"US Rifleman\";\n    };\n    class CustomSoldier : SyntheticSoldierWest {\n        displayName = \"Custom Soldier\";\n        weapons[] = {\"SyntheticRifle\", \"Binocular\"};\n    };\n};\n");
    assert!(has_class(&cst, &[b"CfgVehicles", b"Man"]));
    assert_eq!(
        text(&cst, &[b"CfgVehicles", b"CustomSoldier", b"displayName"]),
        b"Custom Soldier"
    );
    assert_eq!(
        size(&cst, &[b"CfgVehicles", b"CustomSoldier", b"weapons"]),
        2
    );
}

/// Upstream `TEST_CASE("ParamFile - Property deletion pattern")`, section "Using empty arrays to delete inherited
/// properties".
///
/// Why: "deleting" is overriding with an empty array; there is no `delete` statement.
#[test]
fn property_deletion_pattern() {
    let cst = parsed(b"class CfgVehicles {\n    class SyntheticSoldierWest {\n        weapons[] = {\"SyntheticRifle\", \"HandGrenade\", \"Binocular\"};\n        magazines[] = {\"SyntheticMagazine\", \"SyntheticMagazine\", \"SyntheticMagazine\", \"HandGrenade\"};\n    };\n    class SyntheticUnarmed : SyntheticSoldierWest {\n        weapons[] = {};\n        magazines[] = {};\n    };\n};\n");
    assert_eq!(
        size(&cst, &[b"CfgVehicles", b"SyntheticUnarmed", b"weapons"]),
        0
    );
}

/// Upstream `TEST_CASE("ParamFile - Multiple inheritance levels")`, section "Deep inheritance hierarchy".
///
/// Why: a real-world config shape must round-trip exactly and read as upstream expects (D013).
#[test]
fn multiple_inheritance_levels() {
    let cst = parsed(b"class CfgVehicles {\n    class All {};\n    class AllVehicles : All {};\n    class Land : AllVehicles {};\n    class Man : Land {};\n    class Soldier : Man {};\n    class SyntheticSoldierWest : Soldier {};\n    class SyntheticSoldierRifle : SyntheticSoldierWest {\n        displayName = \"Rifleman\";\n        weapons[] = {\"SyntheticRifle\"};\n    };\n};\n");
    for name in [
        &b"All"[..],
        b"AllVehicles",
        b"Land",
        b"Man",
        b"Soldier",
        b"SyntheticSoldierWest",
    ] {
        assert!(has_class(&cst, &[b"CfgVehicles", name]));
    }
    assert!(
        cst.find(&[b"CfgVehicles", b"SyntheticSoldierRifle", b"weapons"])
            .is_some()
    );
}

/// Upstream `TEST_CASE("ParamFile - Mixed property types")`, section "Config with all data types".
///
/// Why: a real-world config shape must round-trip exactly and read as upstream expects (D013).
#[test]
fn mixed_property_types() {
    let cst = parsed(b"class CfgVehicles {\n    class Tank {\n        displayName = \"Synthetic Tank Alpha\";\n        model = \"\\Synthetic\\m1.p3d\";\n        armor = 900;\n        cost = 500000;\n        maxSpeed = 65.5;\n        turnSpeed = 0.8;\n        weapons[] = {\"M256\"};\n        magazines[] = {\"M256_SABOT\", \"M256_HEAT\"};\n        transportSoldier = 0;\n        class Turret {\n            weapons[] = {\"M256\"};\n        };\n        class Damage {\n            tex[] = {};\n            mat[] = {};\n        };\n    };\n};\n");
    assert_eq!(
        scalar(&cst, &[b"CfgVehicles", b"Tank", b"maxSpeed"]),
        Scalar::Float(65.5)
    );
    assert!(
        has_class(&cst, &[b"CfgVehicles", b"Tank", b"Turret"])
            && has_class(&cst, &[b"CfgVehicles", b"Tank", b"Damage"])
    );
}

// ── Boundary tests: section 10.4, scale ─────────────────────────────────────────────────────────────────────────

/// Upstream `TEST_CASE("ParamFile - Large config with many classes")`, section "100+ classes in single config".
///
/// Why: a real-world config shape must round-trip exactly and read as upstream expects (D013).
#[test]
fn large_config_with_many_classes() {
    let mut config = String::from("class CfgVehicles {\n");
    for i in 0..100 {
        config.push_str(&format!("    class Unit{i} {{\n        displayName = \"Unit {i}\";\n        value = {};\n    }};\n", i * 100));
    }
    config.push_str("};\n");
    let cst = parsed(config.as_bytes());
    for name in [&b"Unit0"[..], b"Unit50", b"Unit99"] {
        assert!(has_class(&cst, &[b"CfgVehicles", name]));
    }
    assert_eq!(
        scalar(&cst, &[b"CfgVehicles", b"Unit99", b"value"]),
        Scalar::Int(9900)
    );
}

/// Upstream `TEST_CASE("ParamFile - Config with large arrays")`, section "Arrays with 100+ elements".
///
/// Why: a real-world config shape must round-trip exactly and read as upstream expects (D013).
#[test]
fn config_with_large_arrays() {
    let numbers: Vec<String> = (0..100).map(|i| i.to_string()).collect();
    let config = format!("bigArray[] = {{{}}};\n", numbers.join(", "));
    let cst = parsed(config.as_bytes());
    let Some(Entry::Array(array)) = cst.find(&[b"bigArray"]) else {
        panic!("bigArray")
    };
    let items = array.items();
    assert_eq!(items.len(), 100);
    for index in [0usize, 50, 99] {
        let plotroom_config::ArrayItem::Value(value) = items[index] else {
            panic!("value")
        };
        assert_eq!(value.scalar(), Scalar::Int(i32::try_from(index).unwrap()));
    }
}

/// Upstream `TEST_CASE("ParamFile - Deep class nesting")`, section "10 levels of nesting" (its final assertion was
/// vacuous; here Level10's value is reached).
///
/// Why: a real-world config shape must round-trip exactly and read as upstream expects (D013).
#[test]
fn deep_class_nesting() {
    let mut config = String::new();
    for level in 1..=10 {
        config.push_str(&format!(
            "{}class Level{level} {{\n",
            "    ".repeat(level - 1)
        ));
    }
    config.push_str(&format!("{}deepValue = 42;\n", "    ".repeat(10)));
    for level in (1..=10).rev() {
        config.push_str(&format!("{}}};\n", "    ".repeat(level - 1)));
    }
    let cst = parsed(config.as_bytes());
    let names: Vec<Vec<u8>> = (1..=10)
        .map(|level| format!("Level{level}").into_bytes())
        .chain([b"deepValue".to_vec()])
        .collect();
    let path: Vec<&[u8]> = names.iter().map(Vec::as_slice).collect();
    assert_eq!(scalar(&cst, &path), Scalar::Int(42));
}
