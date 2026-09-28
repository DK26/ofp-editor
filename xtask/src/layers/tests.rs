// SPDX-License-Identifier: GPL-3.0-or-later
//! Tests of [`check`] against the committed table, on fixture `cargo metadata` JSON.
//!
//! The fixtures use the real [`BUILTIN_TABLE`], so each negative test proves both that the check catches the edge
//! and that the committed table encodes the rule (M0 exit evidence item 2: a planted bad edge must fail).

use serde_json::json;

use super::*;
use crate::metadata::{DepKind, Metadata};

/// A declared dependency in a fixture workspace.
#[derive(Debug, Clone, Copy)]
struct Dep {
    name: &'static str,
    /// Cargo's `kind` field: `None` (normal), `Some("dev")` or `Some("build")`.
    kind: Option<&'static str>,
    /// Whether the dependency is another workspace member (a path dependency) or a crates.io crate.
    member: bool,
}

/// A normal dependency on another workspace member.
const fn on(name: &'static str) -> Dep {
    Dep {
        name,
        kind: None,
        member: true,
    }
}

/// A dependency on another workspace member from the given table (`"dev"` or `"build"`).
const fn on_as(name: &'static str, kind: &'static str) -> Dep {
    Dep {
        name,
        kind: Some(kind),
        member: true,
    }
}

/// A normal dependency on a crates.io crate.
const fn external(name: &'static str) -> Dep {
    Dep {
        name,
        kind: None,
        member: false,
    }
}

/// Builds `cargo metadata` JSON for a workspace and parses it with the real parser.
///
/// Every member dependency that is not itself listed becomes an extra member with no dependencies, so a fixture
/// states only the edges it tests. Member dependencies carry `source: null` and a `path`, third-party ones a
/// crates.io `source`, as cargo prints them.
fn workspace(members: &[(&'static str, &[Dep])]) -> Metadata {
    let mut all: Vec<(&str, Vec<Dep>)> = members
        .iter()
        .map(|(name, deps)| (*name, deps.to_vec()))
        .collect();
    for (_, deps) in members {
        for dep in deps.iter().filter(|d| d.member) {
            if !all.iter().any(|(name, _)| *name == dep.name) {
                all.push((dep.name, Vec::new()));
            }
        }
    }
    let id = |name: &str| format!("path+file:///ws/{name}#0.0.0");
    let packages: Vec<_> = all
        .iter()
        .map(|(name, deps)| {
            let deps: Vec<_> = deps
                .iter()
                .map(|d| {
                    if d.member {
                        json!({"name": d.name, "source": null, "kind": d.kind, "path": format!("/ws/{}", d.name)})
                    } else {
                        json!({"name": d.name, "kind": d.kind,
                               "source": "registry+https://github.com/rust-lang/crates.io-index"})
                    }
                })
                .collect();
            json!({"name": name, "id": id(name), "manifest_path": format!("/ws/{name}/Cargo.toml"),
                   "dependencies": deps, "targets": [{"name": name.replace('-', "_"), "kind": ["lib"]}]})
        })
        .collect();
    let members: Vec<_> = all.iter().map(|(name, _)| id(name)).collect();
    let text = json!({"packages": packages, "workspace_members": members, "workspace_root": "/ws"})
        .to_string();
    Metadata::parse(text.as_bytes()).unwrap()
}

/// The committed table.
fn table() -> LayerTable {
    LayerTable::builtin().unwrap()
}

// ── Basic functionality ─────────────────────────────────────────────────────────────────────────────────────────

/// A workspace that only uses allowed edges passes with no violations.
///
/// Covers each kind of allowed edge once: downward, a listed same-layer edge, session's fan-in, free edges inside
/// L8, confined crates in their allowed crates, and the dev crate as a dev-dependency (and depending freely).
#[test]
fn allowed_edges_pass() {
    let md = workspace(&[
        (
            "plotroom-pbo",
            &[on("plotroom-bytes"), on_as("plotroom-testkit", "dev")],
        ),
        (
            "plotroom-config",
            &[on("plotroom-preproc"), on("plotroom-bytes")],
        ),
        (
            "plotroom-session",
            &[on("plotroom-template"), on("plotroom-project")],
        ),
        (
            "plotroom-app",
            &[on("plotroom-ui"), on("plotroom-cli"), external("eframe")],
        ),
        ("plotroom-ui", &[external("egui")]),
        ("plotroom-net", &[external("reqwest")]),
        ("plotroom-gpu", &[external("wgpu")]),
        ("plotroom-testkit", &[on("plotroom-session")]),
        ("xtask", &[external("serde")]),
    ]);
    assert_eq!(check(&table(), &md), []);
}

/// An empty workspace has nothing to report.
#[test]
fn empty_workspace_has_no_violations() {
    assert_eq!(check(&table(), &workspace(&[])), []);
}

// ── Committed negative tests (M0 exit evidence item 2) ──────────────────────────────────────────────────────────

/// A planted L6 edge to `plotroom-session` fails.
///
/// The harness must never reach the session that mints `UserIntent` (crate-map §2.1, §2.3); this is the
/// milestone's named evidence that the layer check works.
#[test]
fn planted_l6_edge_to_session_fails() {
    let md = workspace(&[("plotroom-decide", &[on("plotroom-session")])]);
    let found = check(&table(), &md);
    assert_eq!(found.len(), 1, "{found:?}");
    assert!(
        matches!(&found[0], Violation::ForbiddenEdge { from, to, kind: DepKind::Normal, .. }
            if from == "plotroom-decide" && to == "plotroom-session"),
        "{found:?}"
    );
}

/// `plotroom-plugin-host` and `plotroom-mcp` (L7) may not depend on the session either, even as a dev-dependency.
#[test]
fn plugin_host_and_mcp_edges_to_session_fail() {
    let md = workspace(&[
        ("plotroom-plugin-host", &[on("plotroom-session")]),
        ("plotroom-mcp", &[on_as("plotroom-session", "dev")]),
        ("plotroom-preview", &[on("plotroom-session")]),
    ]);
    let found = check(&table(), &md);
    let forbidden: Vec<&str> = found
        .iter()
        .filter_map(|v| match v {
            Violation::ForbiddenEdge { from, .. } => Some(from.as_str()),
            _ => None,
        })
        .collect();
    assert_eq!(
        forbidden,
        ["plotroom-mcp", "plotroom-plugin-host"],
        "{found:?}"
    );
    assert_eq!(
        found.len(),
        2,
        "plotroom-preview -> plotroom-session is an ordinary downward edge: {found:?}"
    );
}

/// An edge to a higher layer fails, naming both layers.
#[test]
fn upward_edge_fails() {
    let md = workspace(&[("plotroom-bytes", &[on("plotroom-config")])]);
    assert_eq!(
        check(&table(), &md),
        [Violation::UpwardEdge {
            from: "plotroom-bytes".into(),
            from_layer: Layer::L0,
            to: "plotroom-config".into(),
            to_layer: Layer::L1,
            kind: DepKind::Normal,
        }]
    );
}

/// A same-layer edge not listed in `[same-layer]` fails; the listed edge in the other direction does not excuse it.
#[test]
fn undeclared_same_layer_edge_fails() {
    let md = workspace(&[("plotroom-ids", &[on("plotroom-profile")])]);
    assert_eq!(
        check(&table(), &md),
        [Violation::SameLayerEdgeNotDeclared {
            from: "plotroom-ids".into(),
            to: "plotroom-profile".into(),
            layer: Layer::L0,
            kind: DepKind::Normal,
        }]
    );
}

/// egui below the shell fails: in an L4 crate, and in an L8 crate the group does not allow.
#[test]
fn egui_outside_the_shell_fails() {
    let md = workspace(&[
        ("plotroom-view", &[external("egui")]),
        ("plotroom-draw2d", &[external("eframe")]),
    ]);
    let found = check(&table(), &md);
    let offenders: Vec<(&str, &str)> = found
        .iter()
        .filter_map(|v| match v {
            Violation::ConfinedDependency {
                from, dependency, ..
            } => Some((from.as_str(), dependency.as_str())),
            _ => None,
        })
        .collect();
    assert_eq!(
        offenders,
        [("plotroom-draw2d", "eframe"), ("plotroom-view", "egui")],
        "{found:?}"
    );
    assert_eq!(found.len(), 2);
}

/// HTTP clients outside `plotroom-net`, WebAssembly runtimes outside the plugin host and wgpu outside
/// `plotroom-gpu` fail.
#[test]
fn other_confined_crates_fail_outside_their_crates() {
    let md = workspace(&[
        ("plotroom-provider-http", &[external("reqwest")]),
        ("plotroom-packs", &[external("wasmtime")]),
        ("plotroom-map2d", &[external("wgpu")]),
        ("plotroom-wilco", &[external("rmcp")]),
    ]);
    assert_eq!(check(&table(), &md).len(), 4);
}

/// A workspace member the table does not list fails.
#[test]
fn undeclared_member_fails() {
    let md = workspace(&[("plotroom-mystery", &[])]);
    assert_eq!(
        check(&table(), &md),
        [Violation::UndeclaredCrate {
            crate_name: "plotroom-mystery".into()
        }]
    );
}

/// A layered crate may take a dev crate only under `[dev-dependencies]`.
#[test]
fn dev_crate_outside_dev_dependencies_fails() {
    let md = workspace(&[
        ("plotroom-bytes", &[on("plotroom-testkit")]),
        ("plotroom-pbo", &[on_as("plotroom-testkit", "build")]),
    ]);
    let found = check(&table(), &md);
    assert_eq!(
        found,
        [
            Violation::DevCrateOutsideDevDependencies {
                from: "plotroom-bytes".into(),
                to: "plotroom-testkit".into(),
                kind: DepKind::Normal
            },
            Violation::DevCrateOutsideDevDependencies {
                from: "plotroom-pbo".into(),
                to: "plotroom-testkit".into(),
                kind: DepKind::Build
            },
        ]
    );
}

/// Nothing depends on tooling, not even a dev crate or a dev-dependency.
#[test]
fn depending_on_tooling_fails() {
    let md = workspace(&[
        ("plotroom-bytes", &[on_as("xtask", "dev")]),
        ("plotroom-testkit", &[on("xtask")]),
    ]);
    let found = check(&table(), &md);
    assert_eq!(found.len(), 2, "{found:?}");
    assert!(
        found
            .iter()
            .all(|v| matches!(v, Violation::DependsOnTooling { to, .. } if to == "xtask"))
    );
}

// ── Error field & Display verification ──────────────────────────────────────────────────────────────────────────

/// Every violation's message names the crates, the layers or kind, and a next action that does not widen a guard.
#[test]
fn violation_display_names_facts_and_next_action() {
    let cases = [
        (
            Violation::UndeclaredCrate {
                crate_name: "plotroom-x".into(),
            },
            ["plotroom-x", "crate-map"],
        ),
        (
            Violation::UpwardEdge {
                from: "plotroom-bytes".into(),
                from_layer: Layer::L0,
                to: "plotroom-config".into(),
                to_layer: Layer::L1,
                kind: DepKind::Dev,
            },
            ["plotroom-bytes (L0)", "plotroom-config (L1)"],
        ),
        (
            Violation::SameLayerEdgeNotDeclared {
                from: "plotroom-ids".into(),
                to: "plotroom-profile".into(),
                layer: Layer::L0,
                kind: DepKind::Normal,
            },
            ["plotroom-ids", "design-gap request"],
        ),
        (
            Violation::ForbiddenEdge {
                from: "plotroom-decide".into(),
                to: "plotroom-session".into(),
                kind: DepKind::Normal,
                reason: "use the command API".into(),
            },
            ["plotroom-decide", "use the command API"],
        ),
        (
            Violation::DevCrateOutsideDevDependencies {
                from: "plotroom-bytes".into(),
                to: "plotroom-testkit".into(),
                kind: DepKind::Build,
            },
            ["build", "[dev-dependencies]"],
        ),
        (
            Violation::DependsOnTooling {
                from: "plotroom-bytes".into(),
                to: "xtask".into(),
                kind: DepKind::Dev,
            },
            ["xtask", "remove"],
        ),
        (
            Violation::ConfinedDependency {
                from: "plotroom-view".into(),
                dependency: "egui".into(),
                what: "egui and eframe".into(),
                allowed: vec!["plotroom-app".into(), "plotroom-ui".into()],
                reason: "stay headless".into(),
            },
            ["plotroom-app, plotroom-ui", "stay headless"],
        ),
    ];
    for (violation, needles) in cases {
        let text = violation.to_string();
        for needle in needles {
            assert!(text.contains(needle), "{text:?} lacks {needle:?}");
        }
        assert!(
            !text.contains("add it to xtask/layers.toml"),
            "guidance must not widen the table: {text}"
        );
    }
}

// ── Determinism ─────────────────────────────────────────────────────────────────────────────────────────────────

/// The same workspace gives the same report, sorted, whatever order the members were listed in.
#[test]
fn report_is_deterministic_and_sorted() {
    let forward = workspace(&[
        ("plotroom-view", &[external("egui")]),
        ("plotroom-bytes", &[on("plotroom-config")]),
        ("plotroom-decide", &[on("plotroom-session")]),
    ]);
    let backward = workspace(&[
        ("plotroom-decide", &[on("plotroom-session")]),
        ("plotroom-bytes", &[on("plotroom-config")]),
        ("plotroom-view", &[external("egui")]),
    ]);
    let first = check(&table(), &forward);
    assert_eq!(first.len(), 3);
    assert_eq!(first, check(&table(), &forward));
    assert_eq!(first, check(&table(), &backward));
    assert!(first.is_sorted());
}

// ── Boundary tests ──────────────────────────────────────────────────────────────────────────────────────────────

/// Any downward distance passes (L7 -> L0); edges inside L8 need no entry.
#[test]
fn any_downward_edge_passes_and_l8_is_open() {
    let md = workspace(&[
        ("plotroom-io", &[on("plotroom-bytes")]),
        ("plotroom-cli", &[on("plotroom-map2d"), on("plotroom-io")]),
    ]);
    assert_eq!(check(&table(), &md), []);
}

/// A dev-dependency that points upward is still an upward edge.
#[test]
fn upward_dev_dependency_still_fails() {
    let md = workspace(&[("plotroom-bytes", &[on_as("plotroom-session", "dev")])]);
    assert!(matches!(
        check(&table(), &md).as_slice(),
        [Violation::UpwardEdge {
            kind: DepKind::Dev,
            to_layer: Layer::L5,
            ..
        }]
    ));
}

// ── Security edge-case tests ────────────────────────────────────────────────────────────────────────────────────

/// A renamed dependency (`kit = { package = ... }`) is judged by its package name, so a rename cannot hide it.
#[test]
fn renamed_dependency_cannot_hide_an_edge() {
    let json = r#"{"packages":[
        {"name":"plotroom-decide","id":"d","dependencies":[
            {"name":"plotroom-session","rename":"harmless","source":null,"kind":null,"path":"/ws/s"}]},
        {"name":"plotroom-session","id":"s"}],
      "workspace_members":["d","s"],"workspace_root":"/ws"}"#;
    let md = Metadata::parse(json.as_bytes()).unwrap();
    assert!(matches!(
        check(&table(), &md).as_slice(),
        [Violation::ForbiddenEdge { .. }]
    ));
}

/// A dependency declared only for one target (`[target.'cfg(windows)'.dependencies]`) is checked like any other.
#[test]
fn target_specific_dependency_is_checked() {
    let json = r#"{"packages":[
        {"name":"plotroom-view","id":"v","dependencies":[
            {"name":"egui","source":"registry+https://github.com/rust-lang/crates.io-index","kind":null,
             "target":"cfg(windows)"}]}],
      "workspace_members":["v"],"workspace_root":"/ws"}"#;
    let md = Metadata::parse(json.as_bytes()).unwrap();
    assert!(matches!(
        check(&table(), &md).as_slice(),
        [Violation::ConfinedDependency { .. }]
    ));
}

/// The same bad edge declared twice (normal and per target) is reported once.
#[test]
fn duplicate_edges_are_reported_once() {
    let md = workspace(&[(
        "plotroom-bytes",
        &[on("plotroom-config"), on("plotroom-config")],
    )]);
    assert_eq!(check(&table(), &md).len(), 1);
}

/// Hidden characters in a member name are shown escaped in the report, never raw.
#[test]
fn hidden_characters_in_names_are_escaped() {
    let json = "{\"packages\":[{\"name\":\"plotroom-\u{202E}x\",\"id\":\"h\"}],\"workspace_members\":[\"h\"]}";
    let md = Metadata::parse(json.as_bytes()).unwrap();
    let text = check(&table(), &md)
        .iter()
        .map(ToString::to_string)
        .collect::<String>();
    assert!(text.contains("plotroom-\\u{202e}x"), "{text}");
    assert!(!text.contains('\u{202E}'), "{text}");
}
