// SPDX-License-Identifier: GPL-3.0-or-later
//! Reading the output of `cargo metadata --format-version 1 --no-deps`.
//!
//! **What.** The subset both checks need: the workspace root, the workspace members, each member's manifest path,
//! targets and *declared* dependencies (name and kind: normal, build or dev). `--no-deps` makes cargo skip
//! dependency resolution, so the call is fast and offline, and the declared dependencies are exactly the edges
//! `layers` judges (direct edges; transitive paths are cargo-deny's job, crate-map §2.5).
//!
//! **Permissive.** Unknown JSON fields are ignored and missing optional ones default, because cargo adds fields
//! over time; an unknown dependency kind is read as `normal`, the strictest reading for the layer check.
//! The `name` of a dependency is the package name even when the manifest renames it (`rename` is ignored), so a
//! rename cannot hide an edge.
//!
//! **Allocation profile.** Parsing allocates the owned structs below; nothing borrows the input.

use std::collections::BTreeSet;
use std::fmt;

use serde::Deserialize;

use crate::Error;

/// The parts of `cargo metadata` output that the checks read.
#[derive(Debug, Clone, Deserialize)]
pub struct Metadata {
    #[serde(default)]
    packages: Vec<Package>,
    #[serde(default)]
    workspace_members: Vec<String>,
    #[serde(default)]
    workspace_root: String,
}

/// One package (with `--no-deps`, only workspace members appear).
#[derive(Debug, Clone, Deserialize)]
pub struct Package {
    name: String,
    id: String,
    #[serde(default)]
    manifest_path: String,
    #[serde(default)]
    dependencies: Vec<Dependency>,
    #[serde(default)]
    targets: Vec<Target>,
}

/// One declared dependency of a package, from any of its dependency tables (target-specific ones included).
#[derive(Debug, Clone, Deserialize)]
pub struct Dependency {
    name: String,
    #[serde(default)]
    kind: Option<String>,
}

/// One build target of a package (lib, bin, test, bench, example, build script).
#[derive(Debug, Clone, Deserialize)]
pub struct Target {
    name: String,
}

/// Which dependency table an edge comes from.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum DepKind {
    /// `[dependencies]`: part of the shipped crate.
    Normal,
    /// `[build-dependencies]`: runs at build time, still shipped code's concern.
    Build,
    /// `[dev-dependencies]`: tests, examples and benches only.
    Dev,
}

impl fmt::Display for DepKind {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::Normal => "normal",
            Self::Build => "build",
            Self::Dev => "dev",
        })
    }
}

impl Metadata {
    /// Parses `cargo metadata --format-version 1` JSON.
    ///
    /// # Errors
    ///
    /// [`Error::MetadataJson`] when the bytes are not JSON of that shape (including JSON nested deeper than
    /// serde_json's recursion limit, which it reports instead of overflowing the stack).
    pub fn parse(json: &[u8]) -> Result<Self, Error> {
        serde_json::from_slice(json).map_err(|source| Error::MetadataJson { source })
    }

    /// The workspace root folder as cargo printed it.
    pub fn workspace_root(&self) -> &str {
        &self.workspace_root
    }

    /// The workspace members, sorted by name (one entry per package id), so reports come out in a stable order.
    pub fn members(&self) -> Vec<&Package> {
        let member_ids: BTreeSet<&str> =
            self.workspace_members.iter().map(String::as_str).collect();
        let mut seen_ids = BTreeSet::new();
        let mut members: Vec<&Package> = self
            .packages
            .iter()
            .filter(|p| member_ids.contains(p.id.as_str()) && seen_ids.insert(p.id.as_str()))
            .collect();
        members.sort_by(|a, b| a.name.cmp(&b.name));
        members
    }
}

impl Package {
    /// The package name.
    pub fn name(&self) -> &str {
        &self.name
    }

    /// The path of its `Cargo.toml` as cargo printed it.
    pub fn manifest_path(&self) -> &str {
        &self.manifest_path
    }

    /// Its declared dependencies.
    pub fn dependencies(&self) -> &[Dependency] {
        &self.dependencies
    }

    /// Its build targets.
    pub fn targets(&self) -> &[Target] {
        &self.targets
    }
}

impl Dependency {
    /// The depended-on package's name (never the local rename).
    pub fn name(&self) -> &str {
        &self.name
    }

    /// The dependency table it comes from; an unknown kind reads as [`DepKind::Normal`].
    pub fn kind(&self) -> DepKind {
        match self.kind.as_deref() {
            Some("dev") => DepKind::Dev,
            Some("build") => DepKind::Build,
            // `null` is cargo's spelling of a normal dependency; an unknown kind is read the strictest way.
            None | Some(_) => DepKind::Normal,
        }
    }
}

impl Target {
    /// The target's name.
    pub fn name(&self) -> &str {
        &self.name
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A trimmed copy of real `cargo metadata --format-version 1 --no-deps` output (cargo 1.98.1), with the extra
    /// fields cargo prints kept so the permissive reading is exercised: one member with a registry dependency, a
    /// renamed path dependency and a target-specific build dependency, plus one package that is not a member.
    const REAL_SHAPE: &str = r#"{
      "packages": [
        {"name": "plotroom-demo", "version": "0.0.0", "id": "path+file:///ws/crates/plotroom-demo#0.0.0",
         "license": "GPL-3.0-or-later", "source": null, "manifest_path": "/ws/crates/plotroom-demo/Cargo.toml",
         "dependencies": [
           {"name": "serde", "source": "registry+https://github.com/rust-lang/crates.io-index", "req": "^1",
            "kind": null, "rename": null, "optional": false, "uses_default_features": true, "features": [],
            "target": null, "registry": null},
           {"name": "plotroom-testkit", "source": null, "req": "*", "kind": "dev", "rename": "kit",
            "optional": false, "uses_default_features": true, "features": [], "target": null,
            "registry": null, "path": "/ws/crates/plotroom-testkit"},
           {"name": "cc", "source": "registry+https://github.com/rust-lang/crates.io-index", "req": "^1",
            "kind": "build", "rename": null, "optional": false, "uses_default_features": true, "features": [],
            "target": "cfg(windows)", "registry": null},
           {"name": "future", "kind": "someday"}
         ],
         "targets": [{"kind": ["lib"], "crate_types": ["lib"], "name": "plotroom_demo",
                      "src_path": "/ws/crates/plotroom-demo/src/lib.rs", "edition": "2024", "doc": true,
                      "doctest": true, "test": true}],
         "features": {}, "metadata": null, "publish": [], "authors": [], "edition": "2024"},
        {"name": "outsider", "id": "path+file:///elsewhere#0.1.0", "manifest_path": "/elsewhere/Cargo.toml"}
      ],
      "workspace_members": ["path+file:///ws/crates/plotroom-demo#0.0.0"],
      "workspace_default_members": ["path+file:///ws/crates/plotroom-demo#0.0.0"],
      "resolve": null, "target_directory": "/ws/target", "version": 1, "workspace_root": "/ws", "metadata": null
    }"#;

    // ── Basic functionality ─────────────────────────────────────────────────────────────────────────────────────

    /// Real-shaped output parses; only workspace members are returned, with their manifest, targets and edges.
    #[test]
    fn real_shape_parses_members_and_edges() {
        let md = Metadata::parse(REAL_SHAPE.as_bytes()).unwrap();
        assert_eq!(md.workspace_root(), "/ws");
        let members = md.members();
        assert_eq!(members.len(), 1, "the non-member package must be skipped");
        let demo = members[0];
        assert_eq!(demo.name(), "plotroom-demo");
        assert_eq!(demo.manifest_path(), "/ws/crates/plotroom-demo/Cargo.toml");
        assert_eq!(demo.targets()[0].name(), "plotroom_demo");
        let edges: Vec<(&str, DepKind)> = demo
            .dependencies()
            .iter()
            .map(|d| (d.name(), d.kind()))
            .collect();
        assert_eq!(
            edges,
            [
                ("serde", DepKind::Normal),
                ("plotroom-testkit", DepKind::Dev),
                ("cc", DepKind::Build),
                ("future", DepKind::Normal),
            ]
        );
    }

    /// Members come back sorted by name whatever order cargo printed them in.
    #[test]
    fn members_are_sorted_by_name() {
        let json = r#"{"packages":[{"name":"b","id":"b"},{"name":"a","id":"a"},{"name":"c","id":"c"}],
                       "workspace_members":["c","a","b"],"workspace_root":"/"}"#;
        let md = Metadata::parse(json.as_bytes()).unwrap();
        let names: Vec<&str> = md.members().iter().map(|p| p.name()).collect();
        assert_eq!(names, ["a", "b", "c"]);
    }

    // ── Error field & Display verification ──────────────────────────────────────────────────────────────────────

    /// Text that is not metadata JSON is a `MetadataJson` error whose message has the position and the next step.
    #[test]
    fn malformed_json_is_reported_with_position() {
        let err = Metadata::parse(b"{\"packages\": [").unwrap_err();
        assert!(matches!(err, Error::MetadataJson { .. }), "{err:?}");
        let text = err.to_string();
        assert!(text.contains("line 1"), "{text}");
        assert!(text.contains("cargo metadata --format-version 1"), "{text}");
    }

    /// A package without the required `name` is refused rather than guessed.
    #[test]
    fn package_without_name_is_an_error() {
        let err =
            Metadata::parse(br#"{"packages":[{"id":"x"}],"workspace_members":["x"]}"#).unwrap_err();
        assert!(matches!(err, Error::MetadataJson { .. }), "{err:?}");
    }

    // ── Determinism ─────────────────────────────────────────────────────────────────────────────────────────────

    /// Parsing the same bytes twice gives the same members and edges.
    #[test]
    fn parse_is_deterministic() {
        let summary = || {
            let md = Metadata::parse(REAL_SHAPE.as_bytes()).unwrap();
            md.members()
                .iter()
                .flat_map(|p| {
                    p.dependencies()
                        .iter()
                        .map(|d| format!("{}>{}:{}", p.name(), d.name(), d.kind()))
                })
                .collect::<Vec<_>>()
        };
        assert_eq!(summary(), summary());
    }

    // ── Boundary tests ──────────────────────────────────────────────────────────────────────────────────────────

    /// An empty object is an empty workspace, not an error; duplicate member ids yield one member.
    #[test]
    fn empty_and_duplicate_members() {
        let md = Metadata::parse(b"{}").unwrap();
        assert!(md.members().is_empty());
        let dup = r#"{"packages":[{"name":"a","id":"a"},{"name":"a","id":"a"}],"workspace_members":["a","a"]}"#;
        assert_eq!(Metadata::parse(dup.as_bytes()).unwrap().members().len(), 1);
    }

    // ── Security edge-case tests ────────────────────────────────────────────────────────────────────────────────

    /// JSON nested far deeper than any real output is refused, not a stack overflow.
    ///
    /// serde_json stops at its recursion limit (128); this proves the limit is in force for our types.
    #[test]
    fn deeply_nested_json_is_refused() {
        let depth = 100_000;
        let mut hostile = String::from("{\"packages\":");
        hostile.push_str(&"[".repeat(depth));
        hostile.push_str(&"]".repeat(depth));
        hostile.push('}');
        assert!(matches!(
            Metadata::parse(hostile.as_bytes()),
            Err(Error::MetadataJson { .. })
        ));
    }
}
