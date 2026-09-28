// SPDX-License-Identifier: GPL-3.0-or-later
//! The layer table: its TOML form, its validated form, and the roles crates play in it.
//!
//! **How.** `xtask/layers.toml` is deserialised into private `Raw*` structs with `deny_unknown_fields` (a typo in a
//! key is an error, not a silently ignored rule), then validated into [`LayerTable`]: every role parses, every
//! crate a rule names is listed in `[crates]`, every `[same-layer]` edge really joins two crates of one layer, and
//! no rule is empty. Only [`LayerTable::from_toml`] builds a table, so a [`LayerTable`] value is always valid.

use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use serde::Deserialize;

use crate::Error;

/// The committed table, compiled into xtask so the check needs no file access.
pub const BUILTIN_TABLE: &str = include_str!("../../layers.toml");

/// A layer of crate-map §2.1, lowest first; the derived order is the layer order.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Layer {
    /// Foundation: ids, bytes, encodings, profiles, diagnostic codes.
    L0,
    /// Formats: pure `&[u8]` parsers and writers.
    L1,
    /// World facts: VFS, installs, catalogs, terrain.
    L2,
    /// Kernel and document models.
    L3,
    /// Core: project store, commands, validation, view state.
    L4,
    /// Domain engines and the session that assembles the core.
    L5,
    /// Harness, with no I/O.
    L6,
    /// Edge: the only crates with files, processes, network or sandboxes.
    L7,
    /// Presentation and binaries.
    L8,
}

impl Layer {
    /// Every layer, lowest first.
    pub const ALL: [Self; 9] = [
        Self::L0,
        Self::L1,
        Self::L2,
        Self::L3,
        Self::L4,
        Self::L5,
        Self::L6,
        Self::L7,
        Self::L8,
    ];

    /// Whether any edge inside this layer is allowed without a `[same-layer]` entry. Only L8, whose crate-map §2.1
    /// row reads "may use: everything".
    pub const fn same_layer_open(self) -> bool {
        matches!(self, Self::L8)
    }

    /// Parses `L0`..`L8`.
    pub fn parse(text: &str) -> Option<Self> {
        Self::ALL
            .into_iter()
            .find(|layer| layer.to_string() == text)
    }
}

impl fmt::Display for Layer {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::L0 => "L0",
            Self::L1 => "L1",
            Self::L2 => "L2",
            Self::L3 => "L3",
            Self::L4 => "L4",
            Self::L5 => "L5",
            Self::L6 => "L6",
            Self::L7 => "L7",
            Self::L8 => "L8",
        })
    }
}

/// The part a crate plays in the table.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Role {
    /// A product crate on a layer.
    Layer(Layer),
    /// Test support or a test oracle: outside the order, taken by layered crates as a dev-dependency only.
    Dev,
    /// Repository tooling (xtask): outside the order, never a dependency.
    Tooling,
}

impl Role {
    /// Parses `L0`..`L8`, `dev` or `tooling`.
    pub fn parse(text: &str) -> Option<Self> {
        match text {
            "dev" => Some(Self::Dev),
            "tooling" => Some(Self::Tooling),
            other => Layer::parse(other).map(Self::Layer),
        }
    }
}

impl fmt::Display for Role {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Layer(layer) => layer.fmt(f),
            Self::Dev => f.write_str("dev"),
            Self::Tooling => f.write_str("tooling"),
        }
    }
}

/// An edge refused even though it points downward (crate-map §2.1 L6 row, §2.5).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ForbiddenEdge {
    to: String,
    from_layers: BTreeSet<Layer>,
    from_crates: BTreeSet<String>,
    reason: String,
}

impl ForbiddenEdge {
    /// The crate that must not be depended on.
    pub fn to(&self) -> &str {
        &self.to
    }

    /// Whether the rule covers a crate named `from` with role `role`.
    pub fn covers(&self, from: &str, role: Role) -> bool {
        let by_layer = match role {
            Role::Layer(layer) => self.from_layers.contains(&layer),
            Role::Dev | Role::Tooling => false,
        };
        by_layer || self.from_crates.contains(from)
    }

    /// Why the edge is refused, with the sanctioned alternative.
    pub fn reason(&self) -> &str {
        &self.reason
    }
}

/// Third-party crates that only some workspace crates may depend on directly (crate-map §2.3).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Confined {
    what: String,
    dependencies: BTreeSet<String>,
    allowed_crates: BTreeSet<String>,
    reason: String,
}

impl Confined {
    /// A short name for the group, for messages.
    pub fn what(&self) -> &str {
        &self.what
    }

    /// Whether `dependency` belongs to this group.
    pub fn contains(&self, dependency: &str) -> bool {
        self.dependencies.contains(dependency)
    }

    /// Whether the workspace crate `from` may depend on this group directly.
    pub fn allows(&self, from: &str) -> bool {
        self.allowed_crates.contains(from)
    }

    /// The crates allowed to depend on this group, sorted.
    pub fn allowed_crates(&self) -> Vec<&str> {
        self.allowed_crates.iter().map(String::as_str).collect()
    }

    /// Why the group is confined, with the sanctioned alternative.
    pub fn reason(&self) -> &str {
        &self.reason
    }
}

/// The validated layer table. Built only by [`LayerTable::from_toml`] (or [`LayerTable::builtin`]).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LayerTable {
    roles: BTreeMap<String, Role>,
    same_layer: BTreeSet<(String, String)>,
    forbidden: Vec<ForbiddenEdge>,
    confined: Vec<Confined>,
}

/// `xtask/layers.toml` as written; validated into [`LayerTable`].
#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields, rename_all = "kebab-case")]
struct RawTable {
    crates: BTreeMap<String, String>,
    #[serde(default)]
    same_layer: BTreeMap<String, Vec<String>>,
    #[serde(default)]
    forbidden: Vec<RawForbidden>,
    #[serde(default)]
    confined: Vec<RawConfined>,
}

/// One `[[forbidden]]` entry as written.
#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields, rename_all = "kebab-case")]
struct RawForbidden {
    to: String,
    #[serde(default)]
    from_layers: Vec<String>,
    #[serde(default)]
    from_crates: Vec<String>,
    reason: String,
}

/// One `[[confined]]` entry as written.
#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields, rename_all = "kebab-case")]
struct RawConfined {
    what: String,
    dependencies: Vec<String>,
    #[serde(default)]
    allowed_crates: Vec<String>,
    reason: String,
}

impl LayerTable {
    /// Parses and validates a layer table.
    ///
    /// # Errors
    ///
    /// [`Error::TableToml`] for invalid TOML or an unknown key; [`Error::TableUnknownRole`],
    /// [`Error::TableUnknownLayer`], [`Error::TableUnknownCrate`], [`Error::TableEdgeNotSameLayer`] and
    /// [`Error::TableEmptyRule`] for a table that parses but says something impossible.
    #[must_use = "a layer table is only useful for checking; pass it to xtask::layers::check"]
    pub fn from_toml(text: &str) -> Result<Self, Error> {
        let raw: RawTable = toml::from_str(text).map_err(|source| Error::TableToml { source })?;

        // ── Roles ──
        let mut roles = BTreeMap::new();
        for (crate_name, value) in raw.crates {
            let role = Role::parse(&value).ok_or_else(|| Error::TableUnknownRole {
                crate_name: crate_name.clone(),
                value,
            })?;
            roles.insert(crate_name, role);
        }
        // Every later rule may name only crates listed above.
        let role_of = |section: &'static str, name: &str| {
            roles
                .get(name)
                .copied()
                .ok_or_else(|| Error::TableUnknownCrate {
                    section,
                    name: name.to_owned(),
                })
        };

        // ── Same-layer edges: both ends listed and on one layer ──
        let mut same_layer = BTreeSet::new();
        for (from, targets) in raw.same_layer {
            let from_role = role_of("same-layer", &from)?;
            for to in targets {
                let to_role = role_of("same-layer", &to)?;
                let one_layer =
                    matches!((from_role, to_role), (Role::Layer(a), Role::Layer(b)) if a == b);
                if !one_layer {
                    return Err(Error::TableEdgeNotSameLayer {
                        from,
                        from_role,
                        to,
                        to_role,
                    });
                }
                same_layer.insert((from.clone(), to));
            }
        }

        // ── Forbidden edges: a known target and at least one source ──
        let mut forbidden = Vec::with_capacity(raw.forbidden.len());
        for (index, rule) in raw.forbidden.into_iter().enumerate() {
            role_of("forbidden", &rule.to)?;
            let mut from_layers = BTreeSet::new();
            for value in rule.from_layers {
                let layer = Layer::parse(&value).ok_or(Error::TableUnknownLayer {
                    section: "forbidden",
                    value,
                })?;
                from_layers.insert(layer);
            }
            let mut from_crates = BTreeSet::new();
            for name in rule.from_crates {
                role_of("forbidden", &name)?;
                from_crates.insert(name);
            }
            if from_layers.is_empty() && from_crates.is_empty() {
                return Err(Error::TableEmptyRule {
                    section: "forbidden",
                    index,
                });
            }
            forbidden.push(ForbiddenEdge {
                to: rule.to,
                from_layers,
                from_crates,
                reason: rule.reason,
            });
        }

        // ── Confined groups: at least one crate, allowed crates known ──
        let mut confined = Vec::with_capacity(raw.confined.len());
        for (index, group) in raw.confined.into_iter().enumerate() {
            if group.dependencies.is_empty() {
                return Err(Error::TableEmptyRule {
                    section: "confined",
                    index,
                });
            }
            let mut allowed_crates = BTreeSet::new();
            for name in group.allowed_crates {
                role_of("confined", &name)?;
                allowed_crates.insert(name);
            }
            confined.push(Confined {
                what: group.what,
                dependencies: group.dependencies.into_iter().collect(),
                allowed_crates,
                reason: group.reason,
            });
        }

        Ok(Self {
            roles,
            same_layer,
            forbidden,
            confined,
        })
    }

    /// The committed table ([`BUILTIN_TABLE`]).
    ///
    /// # Errors
    ///
    /// As [`LayerTable::from_toml`]; the unit tests keep the committed table valid.
    #[must_use = "a layer table is only useful for checking; pass it to xtask::layers::check"]
    pub fn builtin() -> Result<Self, Error> {
        Self::from_toml(BUILTIN_TABLE)
    }

    /// The role of the crate named `name`, if the table lists it.
    pub fn role(&self, name: &str) -> Option<Role> {
        self.roles.get(name).copied()
    }

    /// Whether `[same-layer]` lists the edge `from` -> `to`.
    pub fn same_layer_allowed(&self, from: &str, to: &str) -> bool {
        self.same_layer.contains(&(from.to_owned(), to.to_owned()))
    }

    /// The crates on `layer`, sorted by name.
    pub fn crates_on(&self, layer: Layer) -> Vec<&str> {
        self.roles
            .iter()
            .filter(|(_, role)| **role == Role::Layer(layer))
            .map(|(name, _)| name.as_str())
            .collect()
    }

    /// The `[same-layer]` targets of `from`, sorted by name.
    pub fn same_layer_targets(&self, from: &str) -> Vec<&str> {
        self.same_layer
            .iter()
            .filter(|(f, _)| f == from)
            .map(|(_, to)| to.as_str())
            .collect()
    }

    /// The `[[forbidden]]` rules, in file order.
    pub fn forbidden(&self) -> &[ForbiddenEdge] {
        &self.forbidden
    }

    /// The `[[confined]]` groups, in file order.
    pub fn confined(&self) -> &[Confined] {
        &self.confined
    }
}
