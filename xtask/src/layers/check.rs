// SPDX-License-Identifier: GPL-3.0-or-later
//! The layer check itself: every declared edge of every workspace member against the [`LayerTable`].
//!
//! **How.** For each member (sorted by name) and each declared dependency: an edge to another member is judged by
//! the two roles (layer order, `[same-layer]`, dev and tooling rules) and the `[[forbidden]]` rules; an edge to a
//! third-party crate is judged by the `[[confined]]` groups. Findings are collected in a `BTreeSet`, so the report
//! is sorted and a dependency listed twice (for example once per target) is reported once.

use std::collections::BTreeSet;
use std::fmt;

use crate::display_name;
use crate::layers::{Layer, LayerTable, Role};
use crate::metadata::{DepKind, Metadata};

/// One way the workspace breaks the declared layer table.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Violation {
    /// A workspace member that `[crates]` does not list.
    UndeclaredCrate {
        /// The member's package name.
        crate_name: String,
    },
    /// An edge to a higher layer.
    UpwardEdge {
        /// The depending crate.
        from: String,
        /// Its layer.
        from_layer: Layer,
        /// The dependency.
        to: String,
        /// Its (higher) layer.
        to_layer: Layer,
        /// The dependency table the edge comes from.
        kind: DepKind,
    },
    /// An edge inside one layer that `[same-layer]` does not list.
    SameLayerEdgeNotDeclared {
        /// The depending crate.
        from: String,
        /// The dependency.
        to: String,
        /// The layer both are on.
        layer: Layer,
        /// The dependency table the edge comes from.
        kind: DepKind,
    },
    /// An edge a `[[forbidden]]` rule refuses.
    ForbiddenEdge {
        /// The depending crate.
        from: String,
        /// The forbidden dependency.
        to: String,
        /// The dependency table the edge comes from.
        kind: DepKind,
        /// The rule's reason, with the sanctioned alternative.
        reason: String,
    },
    /// A layered crate that takes a dev crate outside `[dev-dependencies]`.
    DevCrateOutsideDevDependencies {
        /// The depending crate.
        from: String,
        /// The dev crate.
        to: String,
        /// The dependency table the edge comes from (normal or build).
        kind: DepKind,
    },
    /// A crate that depends on repository tooling.
    DependsOnTooling {
        /// The depending crate.
        from: String,
        /// The tooling crate.
        to: String,
        /// The dependency table the edge comes from.
        kind: DepKind,
    },
    /// A direct dependency on a confined third-party crate from a crate the group does not allow.
    ConfinedDependency {
        /// The depending workspace crate.
        from: String,
        /// The third-party crate.
        dependency: String,
        /// The group's short name.
        what: String,
        /// The crates the group allows, sorted.
        allowed: Vec<String>,
        /// The group's reason, with the sanctioned alternative.
        reason: String,
    },
}

/// The next action for an edge the table does not allow. It never suggests editing the table: a new edge is a
/// design change (`AGENTS.md`, "Never widen a guard").
const PROPOSE_EDGE: &str = "remove the dependency; if the design needs this edge, propose it in a design-gap request \
                            against crate-map §2.2, which then updates xtask/layers.toml";

impl fmt::Display for Violation {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::UndeclaredCrate { crate_name } => write!(
                f,
                "undeclared crate: workspace member `{}` is not in xtask/layers.toml; a new crate is recorded in \
                 crate-map.md, CODE-INDEX.md §4 and the layer table in the same change set, with the layer the crate \
                 map gives it",
                display_name(crate_name)
            ),
            Self::UpwardEdge {
                from,
                from_layer,
                to,
                to_layer,
                kind,
            } => write!(
                f,
                "upward edge: {} ({from_layer}) has a {kind} dependency on {} ({to_layer}); edges point downward \
                 only (crate-map §2.1): move the shared item down, or define a trait low and implement it high",
                display_name(from),
                display_name(to)
            ),
            Self::SameLayerEdgeNotDeclared {
                from,
                to,
                layer,
                kind,
            } => write!(
                f,
                "undeclared same-layer edge: {} has a {kind} dependency on {}, both on {layer}, and [same-layer] \
                 does not list it: {PROPOSE_EDGE}",
                display_name(from),
                display_name(to)
            ),
            Self::ForbiddenEdge {
                from,
                to,
                kind,
                reason,
            } => write!(
                f,
                "forbidden edge: {} has a {kind} dependency on {}: {}",
                display_name(from),
                display_name(to),
                display_name(reason)
            ),
            Self::DevCrateOutsideDevDependencies { from, to, kind } => write!(
                f,
                "dev crate in shipped code: {} has a {kind} dependency on the dev crate {}; test support is taken \
                 only under [dev-dependencies]: move it there",
                display_name(from),
                display_name(to)
            ),
            Self::DependsOnTooling { from, to, kind } => write!(
                f,
                "tooling dependency: {} has a {kind} dependency on {}, which is repository tooling: remove it; \
                 shared test helpers belong in plotroom-testkit",
                display_name(from),
                display_name(to)
            ),
            Self::ConfinedDependency {
                from,
                dependency,
                what,
                allowed,
                reason,
            } => {
                let allowed = if allowed.is_empty() {
                    "no workspace crate".to_owned()
                } else {
                    allowed
                        .iter()
                        .map(|name| display_name(name))
                        .collect::<Vec<_>>()
                        .join(", ")
                };
                write!(
                    f,
                    "confined dependency: {} depends on `{}` ({}), which only {allowed} may use: {}",
                    display_name(from),
                    display_name(dependency),
                    display_name(what),
                    display_name(reason)
                )
            }
        }
    }
}

/// Checks every declared edge of every workspace member in `metadata` against `table`.
///
/// Returns the violations sorted and without duplicates; an empty vector means the workspace follows the table.
#[must_use = "an unread report hides layer violations; print each one and fail when the vector is not empty"]
pub fn check(table: &LayerTable, metadata: &Metadata) -> Vec<Violation> {
    let members = metadata.members();
    let member_names: BTreeSet<&str> = members.iter().map(|p| p.name()).collect();
    let mut found = BTreeSet::new();
    for package in &members {
        let from = package.name();
        let Some(from_role) = table.role(from) else {
            found.insert(Violation::UndeclaredCrate {
                crate_name: from.to_owned(),
            });
            continue;
        };
        for dependency in package.dependencies() {
            let to = dependency.name();
            let kind = dependency.kind();
            if member_names.contains(to) {
                // An undeclared dependency is reported once, as a member of its own; nothing to judge here.
                if let Some(to_role) = table.role(to) {
                    let edge = MemberEdge {
                        from,
                        from_role,
                        to,
                        to_role,
                        kind,
                    };
                    judge_member_edge(table, &edge, &mut found);
                }
            } else {
                judge_external_edge(table, from, to, &mut found);
            }
        }
    }
    found.into_iter().collect()
}

/// One declared edge between two workspace crates the table lists, with both roles resolved.
struct MemberEdge<'names> {
    from: &'names str,
    from_role: Role,
    to: &'names str,
    to_role: Role,
    kind: DepKind,
}

/// Judges an edge between two declared workspace crates: roles first, then the forbidden rules.
fn judge_member_edge(table: &LayerTable, edge: &MemberEdge<'_>, found: &mut BTreeSet<Violation>) {
    let MemberEdge {
        from,
        from_role,
        to,
        to_role,
        kind,
    } = *edge;
    match (from_role, to_role) {
        // Nothing depends on tooling, whatever the depending crate is.
        (_, Role::Tooling) => {
            found.insert(Violation::DependsOnTooling {
                from: from.to_owned(),
                to: to.to_owned(),
                kind,
            });
        }
        // Dev and tooling crates sit outside the order and may depend on any non-tooling crate.
        (Role::Dev | Role::Tooling, Role::Layer(_) | Role::Dev) => {}
        (Role::Layer(_), Role::Dev) => {
            if kind != DepKind::Dev {
                found.insert(Violation::DevCrateOutsideDevDependencies {
                    from: from.to_owned(),
                    to: to.to_owned(),
                    kind,
                });
            }
        }
        (Role::Layer(from_layer), Role::Layer(to_layer)) => {
            if to_layer > from_layer {
                found.insert(Violation::UpwardEdge {
                    from: from.to_owned(),
                    from_layer,
                    to: to.to_owned(),
                    to_layer,
                    kind,
                });
            } else if to_layer == from_layer
                && !from_layer.same_layer_open()
                && !table.same_layer_allowed(from, to)
            {
                found.insert(Violation::SameLayerEdgeNotDeclared {
                    from: from.to_owned(),
                    to: to.to_owned(),
                    layer: from_layer,
                    kind,
                });
            }
        }
    }
    // Forbidden rules apply to every dependency table: a dev-dependency on the session would still let the
    // crate's tests mint consent, which the rule exists to prevent.
    for rule in table
        .forbidden()
        .iter()
        .filter(|rule| rule.to() == to && rule.covers(from, from_role))
    {
        found.insert(Violation::ForbiddenEdge {
            from: from.to_owned(),
            to: to.to_owned(),
            kind,
            reason: rule.reason().to_owned(),
        });
    }
}

/// Judges an edge to a third-party crate against the confined groups.
fn judge_external_edge(
    table: &LayerTable,
    from: &str,
    dependency: &str,
    found: &mut BTreeSet<Violation>,
) {
    for group in table
        .confined()
        .iter()
        .filter(|g| g.contains(dependency) && !g.allows(from))
    {
        found.insert(Violation::ConfinedDependency {
            from: from.to_owned(),
            dependency: dependency.to_owned(),
            what: group.what().to_owned(),
            allowed: group
                .allowed_crates()
                .into_iter()
                .map(str::to_owned)
                .collect(),
            reason: group.reason().to_owned(),
        });
    }
}
