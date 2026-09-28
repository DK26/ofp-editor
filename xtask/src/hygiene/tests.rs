// SPDX-License-Identifier: GPL-3.0-or-later
//! Tests of the naming check. Planted names live in string literals only, never in file or module names, so the
//! live hygiene run over this repository stays clean.

use super::*;

/// Checks one name of `kind` and returns the findings.
fn check_one(kind: NameKind, name: &str) -> Vec<Finding> {
    check_sites(&[NameSite::new(kind, "fixture", name)])
}

/// The mark text found in `name`, if any.
fn mark_in(name: &str) -> Option<&'static str> {
    find_mark(name).map(|m| m.text())
}

// ── Basic functionality ─────────────────────────────────────────────────────────────────────────────────────────

/// Tokens come from separators, letter/digit boundaries and camel case, lowercased, from both splits.
#[test]
fn tokens_cover_both_splits() {
    assert_eq!(tokens("plotroom-testkit"), ["plotroom", "testkit"]);
    assert_eq!(tokens("SqmBuilder2"), ["2", "builder", "sqm", "sqmbuilder"]);
    assert_eq!(tokens("OFPEditor"), ["editor", "ofp", "ofpeditor"]);
    assert_eq!(tokens("ArmA"), ["a", "arm", "arma"]);
    assert_eq!(tokens("__"), Vec::<String>::new());
}

/// Every kind of spelling of a mark is found.
#[test]
fn marks_are_found_in_every_spelling() {
    let cases = [
        ("plotroom-arma", "arma"),
        ("ArmaTools", "arma"),
        ("ArmA", "arma"),
        ("arma3_import", "arma"),
        ("ofp-editor", "ofp"),
        ("ofpe_mission", "ofp"),
        ("OFPEditor", "ofp"),
        ("operation_flashpoint", "flashpoint"),
        ("flashpointtools", "flashpoint"),
        ("cold_war_assault", "coldwarassault"),
        ("ColdWarCrisis", "coldwarcrisis"),
        ("resistance_units", "resistance"),
        ("poseidon_bridge", "poseidon"),
        ("bohemian", "bohemia"),
        ("everon.sqm", "everon"),
        ("MaldenMap", "malden"),
        ("kolgujev_roads", "kolgujev"),
        ("nogova-v2", "nogova"),
        ("coop.Noe", "noe"),
        ("eden_test", "eden"),
        ("abel-places", "abel"),
        ("CainRoads", "cain"),
    ];
    for (name, mark) in cases {
        assert_eq!(mark_in(name), Some(mark), "{name}");
    }
}

/// Ordinary words that merely contain a short mark's letters are not flagged.
#[test]
fn ordinary_words_are_not_flagged() {
    for name in [
        "armadillo",
        "pharmacy",
        "karma",
        "sweden",
        "label",
        "canoe",
        "never_one",
        "cocaine",
        "bi_lzss",
        "intro",
        "demo",
        "profile_cwa199",
        "plotroom-testkit",
        "xtask",
        "layers.toml",
        "live_workspace.rs",
    ] {
        assert_eq!(mark_in(name), None, "{name}");
    }
}

/// `mod` declarations are found in all their forms, with line numbers; comments and other lines are not.
#[test]
fn module_declarations_are_found() {
    let source = "//! docs mention mod nothing\n\
                  mod alpha;\n\
                  pub mod beta {\n\
                  pub(crate) mod gamma;\n\
                  #[cfg(test)] mod delta;\n\
                  pub(in crate::x) mod r#epsilon;\n\
                  // mod commented;\n\
                  /// mod documented;\n\
                  let module = 1;\n\
                  modulo();\n    mod  indented ;\n";
    let decls = module_decls(source);
    let found: Vec<(usize, &str)> = decls.iter().map(|(l, n)| (*l, n.as_str())).collect();
    assert_eq!(
        found,
        [
            (2, "alpha"),
            (3, "beta"),
            (4, "gamma"),
            (5, "delta"),
            (6, "epsilon"),
            (11, "indented")
        ]
    );
}

/// Crate and target names come from the workspace members, located by manifest path relative to the root.
#[test]
fn metadata_sites_list_crates_and_targets() {
    let json = r#"{"packages":[{"name":"plotroom-demo","id":"d","manifest_path":"/ws/crates/plotroom-demo/Cargo.toml",
                   "targets":[{"name":"plotroom_demo"},{"name":"live_check"}]}],
                   "workspace_members":["d"],"workspace_root":"/ws"}"#;
    let md = Metadata::parse(json.as_bytes()).unwrap();
    assert_eq!(
        metadata_sites(&md),
        [
            NameSite::new(
                NameKind::Crate,
                "crates/plotroom-demo/Cargo.toml",
                "plotroom-demo"
            ),
            NameSite::new(
                NameKind::Target,
                "crates/plotroom-demo/Cargo.toml",
                "plotroom_demo"
            ),
            NameSite::new(
                NameKind::Target,
                "crates/plotroom-demo/Cargo.toml",
                "live_check"
            ),
        ]
    );
}

// ── Committed negative tests (M0 exit evidence item 2) ──────────────────────────────────────────────────────────

/// A planted mark in a crate name is refused.
///
/// The milestone's named evidence for the hygiene check: `plotroom-ofp-import` must never be a crate.
#[test]
fn planted_mark_in_crate_name_fails() {
    let found = check_one(NameKind::Crate, "plotroom-ofp-import");
    assert_eq!(found.len(), 1, "{found:?}");
    assert!(
        matches!(&found[0], Finding::Mark { mark, .. } if mark.text() == "ofp"),
        "{found:?}"
    );
}

/// Planted marks in a module, a file and a target name are refused too.
#[test]
fn planted_marks_in_other_names_fail() {
    assert_eq!(check_one(NameKind::Module, "everon_roads").len(), 1);
    assert_eq!(
        check_one(NameKind::Path, "cold-war-assault.sidecar").len(),
        1
    );
    assert_eq!(check_one(NameKind::Target, "arma_bridge").len(), 1);
}

// ── Error field & Display verification ──────────────────────────────────────────────────────────────────────────

/// A finding names the location, the kind of name, the mark and the fix.
#[test]
fn finding_display_names_location_mark_and_fix() {
    let text = check_one(NameKind::Module, "malden_map")[0].to_string();
    for needle in [
        "fixture",
        "module name",
        "`malden_map`",
        "island name `malden`",
        "rename it",
    ] {
        assert!(text.contains(needle), "{text:?} lacks {needle:?}");
    }
    let text = check_one(NameKind::Crate, "plotroom-bohemia")[0].to_string();
    assert!(text.contains("third-party mark `bohemia`"), "{text}");
}

// ── Determinism ─────────────────────────────────────────────────────────────────────────────────────────────────

/// Findings come out sorted and without duplicates, whatever the input order.
#[test]
fn findings_are_sorted_and_deduplicated() {
    let a = NameSite::new(NameKind::Path, "b/everon", "everon");
    let b = NameSite::new(NameKind::Crate, "a/Cargo.toml", "plotroom-arma");
    let forward = check_sites(&[a.clone(), b.clone(), a.clone()]);
    let backward = check_sites(&[b, a]);
    assert_eq!(forward.len(), 2);
    assert_eq!(forward, backward);
    assert!(forward.is_sorted());
}

// ── Boundary tests ──────────────────────────────────────────────────────────────────────────────────────────────

/// A mark that is the whole name, or sits at either end, is found; one letter short is not.
#[test]
fn marks_at_the_edges_of_a_name() {
    assert_eq!(mark_in("ofp"), Some("ofp"));
    assert_eq!(mark_in("OF"), None);
    assert_eq!(mark_in("x_noe"), Some("noe"));
    assert_eq!(mark_in("noe_x"), Some("noe"));
    assert_eq!(mark_in("no"), None);
    assert_eq!(mark_in("kolgujev"), Some("kolgujev"));
    assert_eq!(mark_in("kolguje"), None);
    assert_eq!(mark_in(""), None);
}

/// Printable ASCII with spaces and punctuation passes the character rule.
#[test]
fn printable_ascii_passes_the_character_rule() {
    assert!(check_one(NameKind::Path, "a file (copy) #2.txt").is_empty());
}

// ── Security edge-case tests ────────────────────────────────────────────────────────────────────────────────────

/// Zero-width, bidi, look-alike and control characters make a finding of their own, shown escaped.
///
/// `o\u{200B}fp` reads as `ofp` but tokenises differently; a full-width `ＯＦＰ` escapes the ASCII match; both
/// must be refused, not silently passed.
#[test]
fn hidden_characters_are_refused_and_escaped() {
    for name in [
        "o\u{200B}fp",
        "\u{FF2F}\u{FF26}\u{FF30}",
        "safe\u{202E}name",
        "tab\tname",
        "caf\u{E9}",
    ] {
        let found = check_one(NameKind::Path, name);
        assert!(
            matches!(found.as_slice(), [Finding::HiddenCharacters { .. }]),
            "{name:?}: {found:?}"
        );
        let text = found[0].to_string();
        assert!(text.is_ascii(), "{text:?}");
        assert!(text.contains("\\u{"), "{text}");
    }
}

/// A very long name is handled without panicking or slowing down noticeably.
#[test]
fn very_long_names_are_handled() {
    let long = "a_".repeat(100_000);
    assert!(check_one(NameKind::Path, &long).is_empty());
    let planted = format!("{long}ofp");
    assert_eq!(check_one(NameKind::Path, &planted).len(), 1);
}
