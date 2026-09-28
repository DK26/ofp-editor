// SPDX-License-Identifier: GPL-3.0-or-later
//! Tests of the layer table: the committed `xtask/layers.toml` against crate-map §2, and the validation of
//! malformed tables.

use super::*;
use crate::Error;

/// The committed table.
fn table() -> LayerTable {
    LayerTable::builtin().unwrap()
}

/// A minimal valid table with two L0 crates, one L1 crate and one dev crate, to which a test appends one rule.
const BASE: &str = r#"
[crates]
a = "L0"
b = "L0"
c = "L1"
kit = "dev"
"#;

/// Parses `BASE` plus `extra` and returns the error.
fn table_error(extra: &str) -> Error {
    LayerTable::from_toml(&format!("{BASE}{extra}")).unwrap_err()
}

// ── Basic functionality ─────────────────────────────────────────────────────────────────────────────────────────

/// The committed table parses and places crates as crate-map §3-§12 does (one or two per layer).
#[test]
fn committed_table_matches_the_crate_map() {
    let table = table();
    let expect = [
        ("plotroom-bytes", Role::Layer(Layer::L0)),
        ("plotroom-profile", Role::Layer(Layer::L0)),
        ("plotroom-config", Role::Layer(Layer::L1)),
        ("plotroom-rsc", Role::Layer(Layer::L1)),
        ("plotroom-catalog", Role::Layer(Layer::L2)),
        ("plotroom-doc", Role::Layer(Layer::L3)),
        ("plotroom-mission", Role::Layer(Layer::L3)),
        ("plotroom-project", Role::Layer(Layer::L4)),
        ("plotroom-session", Role::Layer(Layer::L5)),
        ("plotroom-decide", Role::Layer(Layer::L6)),
        ("plotroom-evals", Role::Layer(Layer::L6)),
        ("plotroom-io", Role::Layer(Layer::L7)),
        ("plotroom-mcp", Role::Layer(Layer::L7)),
        ("plotroom-app", Role::Layer(Layer::L8)),
        ("plotroom-ui-classic", Role::Layer(Layer::L8)),
        ("plotroom-testkit", Role::Dev),
        ("plotroom-script-oracle", Role::Dev),
        ("xtask", Role::Tooling),
    ];
    for (name, role) in expect {
        assert_eq!(table.role(name), Some(role), "{name}");
    }
    assert_eq!(table.role("plotroom-core"), None, "not a planned crate");
    // Every layer of the order has planned crates.
    for layer in Layer::ALL {
        assert!(!table.crates_on(layer).is_empty(), "{layer} is empty");
    }
}

/// "plotroom-session -> every other L5 crate" (crate-map §2.2) stays true as L5 crates are added.
///
/// The table spells the rule out crate by crate; this test fails, naming the missing crate, when a new L5 crate
/// is added without its session edge.
#[test]
fn session_may_use_every_other_l5_crate() {
    let table = table();
    let mut others: Vec<&str> = table
        .crates_on(Layer::L5)
        .into_iter()
        .filter(|c| *c != "plotroom-session")
        .collect();
    others.sort_unstable();
    assert_eq!(table.same_layer_targets("plotroom-session"), others);
}

/// The document models (mission, modules, campaign, cine) and the sidecar may use `plotroom-doc`.
#[test]
fn document_models_may_use_the_kernel() {
    let table = table();
    for model in [
        "plotroom-mission",
        "plotroom-modules",
        "plotroom-campaign",
        "plotroom-cine",
        "plotroom-sidecar",
    ] {
        assert!(table.same_layer_allowed(model, "plotroom-doc"), "{model}");
    }
    assert!(!table.same_layer_allowed("plotroom-doc", "plotroom-mission"));
}

/// The forbidden rule covers every L6 crate, the plugin host and the MCP server, and nothing else.
#[test]
fn forbidden_rule_covers_harness_plugins_and_mcp() {
    let table = table();
    let rule = table
        .forbidden()
        .iter()
        .find(|r| r.to() == "plotroom-session")
        .unwrap();
    for crate_name in table.crates_on(Layer::L6) {
        assert!(
            rule.covers(crate_name, Role::Layer(Layer::L6)),
            "{crate_name}"
        );
    }
    assert!(rule.covers("plotroom-plugin-host", Role::Layer(Layer::L7)));
    assert!(rule.covers("plotroom-mcp", Role::Layer(Layer::L7)));
    assert!(!rule.covers("plotroom-preview", Role::Layer(Layer::L7)));
    assert!(!rule.covers("plotroom-app", Role::Layer(Layer::L8)));
    assert!(!rule.covers("plotroom-testkit", Role::Dev));
}

/// egui is confined to the shell crates and HTTP clients to `plotroom-net` (crate-map §2.3).
#[test]
fn confined_groups_match_the_capability_table() {
    let table = table();
    let group = |dep: &str| table.confined().iter().find(|g| g.contains(dep)).unwrap();
    assert_eq!(
        group("egui").allowed_crates(),
        ["plotroom-app", "plotroom-ui"]
    );
    assert_eq!(
        group("eframe").allowed_crates(),
        ["plotroom-app", "plotroom-ui"]
    );
    assert_eq!(group("reqwest").allowed_crates(), ["plotroom-net"]);
    assert_eq!(group("wasmtime").allowed_crates(), ["plotroom-plugin-host"]);
    assert_eq!(
        group("rmcp").allowed_crates(),
        ["plotroom-mcp", "plotroom-plugin-host"]
    );
    assert_eq!(group("wgpu").allowed_crates(), ["plotroom-gpu"]);
}

// ── Error field & Display verification ──────────────────────────────────────────────────────────────────────────

/// Invalid TOML is a `TableToml` error that points at the line.
#[test]
fn invalid_toml_is_reported() {
    let err = LayerTable::from_toml("[crates\n").unwrap_err();
    assert!(matches!(err, Error::TableToml { .. }), "{err:?}");
    assert!(err.to_string().contains("line"), "{err}");
}

/// An unknown key is an error, so a misspelt rule section cannot be silently ignored.
#[test]
fn unknown_key_is_refused() {
    assert!(matches!(
        table_error("[same_layer]\na = [\"b\"]\n"),
        Error::TableToml { .. }
    ));
    assert!(matches!(
        table_error("[[forbidden]]\nto = \"a\"\nfrom-crate = [\"c\"]\nreason = \"r\"\n"),
        Error::TableToml { .. }
    ));
}

/// A role outside L0..L8, dev and tooling names the crate and the value.
#[test]
fn unknown_role_is_refused() {
    let err = LayerTable::from_toml("[crates]\nx = \"L9\"\n").unwrap_err();
    match &err {
        Error::TableUnknownRole { crate_name, value } => {
            assert_eq!((crate_name.as_str(), value.as_str()), ("x", "L9"))
        }
        other => panic!("{other:?}"),
    }
    assert!(err.to_string().contains("L0..L8, dev or tooling"), "{err}");
}

/// A forbidden rule's layer must be L0..L8.
#[test]
fn unknown_forbidden_layer_is_refused() {
    let err = table_error("[[forbidden]]\nto = \"a\"\nfrom-layers = [\"dev\"]\nreason = \"r\"\n");
    assert!(
        matches!(&err, Error::TableUnknownLayer { section: "forbidden", value } if value == "dev"),
        "{err:?}"
    );
}

/// Every rule may name only crates listed in `[crates]`.
#[test]
fn rules_naming_unknown_crates_are_refused() {
    let cases = [
        ("[same-layer]\nzz = [\"a\"]\n", "same-layer"),
        ("[same-layer]\na = [\"zz\"]\n", "same-layer"),
        (
            "[[forbidden]]\nto = \"zz\"\nfrom-crates = [\"c\"]\nreason = \"r\"\n",
            "forbidden",
        ),
        (
            "[[forbidden]]\nto = \"a\"\nfrom-crates = [\"zz\"]\nreason = \"r\"\n",
            "forbidden",
        ),
        (
            "[[confined]]\nwhat = \"w\"\ndependencies = [\"d\"]\nallowed-crates = [\"zz\"]\nreason = \"r\"\n",
            "confined",
        ),
    ];
    for (extra, section) in cases {
        let err = table_error(extra);
        assert!(
            matches!(&err, Error::TableUnknownCrate { section: s, name } if *s == section && name == "zz"),
            "{extra}: {err:?}"
        );
        assert!(err.to_string().contains("[crates] does not list"), "{err}");
    }
}

/// A `[same-layer]` entry must join two crates of one layer; dev and tooling crates are not on a layer.
#[test]
fn same_layer_entry_across_layers_is_refused() {
    let err = table_error("[same-layer]\na = [\"c\"]\n");
    assert!(
        matches!(
            &err,
            Error::TableEdgeNotSameLayer {
                from_role: Role::Layer(Layer::L0),
                to_role: Role::Layer(Layer::L1),
                ..
            }
        ),
        "{err:?}"
    );
    assert!(err.to_string().contains("a` (L0) -> `c` (L1)"), "{err}");
    let dev = table_error("[same-layer]\na = [\"kit\"]\n");
    assert!(
        matches!(
            dev,
            Error::TableEdgeNotSameLayer {
                to_role: Role::Dev,
                ..
            }
        ),
        "{dev:?}"
    );
}

/// A forbidden rule with no source, or a confined group with no crates, matches nothing and is refused.
#[test]
fn empty_rules_are_refused() {
    let err = table_error("[[forbidden]]\nto = \"a\"\nreason = \"r\"\n");
    assert!(
        matches!(
            err,
            Error::TableEmptyRule {
                section: "forbidden",
                index: 0
            }
        ),
        "{err:?}"
    );
    assert!(err.to_string().contains("rule 0"), "{err}");
    let err = table_error("[[confined]]\nwhat = \"w\"\ndependencies = []\nreason = \"r\"\n");
    assert!(
        matches!(
            err,
            Error::TableEmptyRule {
                section: "confined",
                index: 0
            }
        ),
        "{err:?}"
    );
}

// ── Determinism ─────────────────────────────────────────────────────────────────────────────────────────────────

/// Parsing the committed table twice gives equal tables.
#[test]
fn parsing_is_deterministic() {
    assert_eq!(table(), table());
}

// ── Boundary tests ──────────────────────────────────────────────────────────────────────────────────────────────

/// L0 and L8 are the ends of the order; lowercase, `L9` and `L10` are not layers.
#[test]
fn layer_names_at_the_ends() {
    assert_eq!(Role::parse("L0"), Some(Role::Layer(Layer::L0)));
    assert_eq!(Role::parse("L8"), Some(Role::Layer(Layer::L8)));
    for bad in ["l0", "L9", "L10", "", " L1", "Dev"] {
        assert_eq!(Role::parse(bad), None, "{bad:?}");
    }
    assert!(Layer::L0 < Layer::L8);
    assert!(Layer::L8.same_layer_open());
    assert!(!Layer::L7.same_layer_open());
}

/// A table with crates and no rules is valid; one with no `[crates]` section is not.
#[test]
fn minimal_tables() {
    assert!(LayerTable::from_toml(BASE).is_ok());
    assert!(matches!(
        LayerTable::from_toml(""),
        Err(Error::TableToml { .. })
    ));
}

// ── Security edge-case tests ────────────────────────────────────────────────────────────────────────────────────

/// A role value with a hidden character is refused and shown escaped.
#[test]
fn hidden_character_in_role_is_escaped() {
    let err = LayerTable::from_toml("[crates]\nx = \"L\u{200B}1\"\n").unwrap_err();
    let text = err.to_string();
    assert!(text.contains("L\\u{200b}1"), "{text}");
    assert!(!text.contains('\u{200B}'), "{text}");
}
