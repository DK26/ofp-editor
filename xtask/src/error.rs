// SPDX-License-Identifier: GPL-3.0-or-later
//! The one error type of `xtask` (`AGENTS.md`, "Error Design").
//!
//! These are failures to *run* a check (a malformed layer table, unreadable `cargo metadata` output, a folder that
//! cannot be listed). What a check *finds* is not an error: layer violations and hygiene findings are reports
//! ([`crate::layers::Violation`], [`crate::hygiene::Finding`]) that the command prints before failing.
//!
//! `Display` is for developers and CI logs: it names the numbers and ends with the next action. Names quoted from
//! the table or from `cargo metadata` go through [`crate::display_name`], which makes control, bidi and zero-width
//! characters visible.

use std::fmt;
use std::path::PathBuf;

use crate::display_name;
use crate::layers::Role;

/// Everything that can stop an xtask command before it reports.
#[derive(Debug)]
pub enum Error {
    /// `xtask/layers.toml` is not valid TOML, or has a key the table format does not know.
    TableToml {
        /// The parser's error, with line and column.
        source: toml::de::Error,
    },
    /// A crate in `[crates]` has a role other than `L0`..`L8`, `dev` or `tooling`.
    TableUnknownRole {
        /// The crate whose role is wrong.
        crate_name: String,
        /// The value found.
        value: String,
    },
    /// A `[[forbidden]]` rule's `from-layers` holds something other than `L0`..`L8`.
    TableUnknownLayer {
        /// The table section holding the rule.
        section: &'static str,
        /// The value found.
        value: String,
    },
    /// A rule names a crate that `[crates]` does not list.
    TableUnknownCrate {
        /// The table section holding the rule (`same-layer`, `forbidden`, `confined`).
        section: &'static str,
        /// The unknown name.
        name: String,
    },
    /// A `[same-layer]` edge joins crates on different layers, or a crate outside the layer order.
    TableEdgeNotSameLayer {
        /// The depending crate.
        from: String,
        /// Its role.
        from_role: Role,
        /// The dependency.
        to: String,
        /// Its role.
        to_role: Role,
    },
    /// A `[[forbidden]]` or `[[confined]]` rule matches nothing (no source crates or no dependencies).
    TableEmptyRule {
        /// The table section holding the rule.
        section: &'static str,
        /// Zero-based position of the rule in that section.
        index: usize,
    },
    /// `cargo metadata` printed something that is not the JSON this tool reads.
    MetadataJson {
        /// The JSON parser's error, with line and column.
        source: serde_json::Error,
    },
    /// `cargo metadata` exited with a failure.
    CargoMetadataFailed {
        /// Its exit code, if it had one.
        code: Option<i32>,
        /// The last part of its standard error, as cargo printed it.
        stderr_tail: String,
    },
    /// Reading the file system or starting `cargo` failed.
    Io {
        /// What xtask was doing.
        context: &'static str,
        /// The path involved.
        path: PathBuf,
        /// The operating system's error.
        source: std::io::Error,
    },
    /// The hygiene walk met more entries than [`crate::sys::MAX_WALK_ENTRIES`].
    WalkLimit {
        /// The limit that was reached.
        limit: usize,
        /// The folder being listed when it was reached.
        path: PathBuf,
    },
    /// The command line names no known command.
    Usage {
        /// What was given (empty when nothing was).
        given: String,
    },
    /// xtask's manifest directory has no parent, so the workspace root is unknown.
    NoWorkspaceRoot {
        /// The manifest directory xtask was compiled in.
        manifest_dir: &'static str,
    },
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::TableToml { source } => {
                write!(
                    f,
                    "xtask/layers.toml is not a valid layer table: {source}; fix the line it names"
                )
            }
            Self::TableUnknownRole { crate_name, value } => write!(
                f,
                "xtask/layers.toml gives `{}` the role `{}`: use one of L0..L8, dev or tooling (crate-map §2.1)",
                display_name(crate_name),
                display_name(value)
            ),
            Self::TableUnknownLayer { section, value } => write!(
                f,
                "xtask/layers.toml [[{section}]] names the layer `{}`: use one of L0..L8 (crate-map §2.1)",
                display_name(value)
            ),
            Self::TableUnknownCrate { section, name } => write!(
                f,
                "xtask/layers.toml [{section}] names `{}`, which [crates] does not list: correct the name, or \
                 record the crate in crate-map.md and [crates] first",
                display_name(name)
            ),
            Self::TableEdgeNotSameLayer {
                from,
                from_role,
                to,
                to_role,
            } => write!(
                f,
                "xtask/layers.toml [same-layer] lists `{}` ({from_role}) -> `{}` ({to_role}), which is not a \
                 same-layer edge: remove it (lower-layer edges need no entry; edges to dev or tooling crates are \
                 not layer edges)",
                display_name(from),
                display_name(to)
            ),
            Self::TableEmptyRule { section, index } => write!(
                f,
                "xtask/layers.toml [[{section}]] rule {index} (zero-based) matches nothing: give it at least one \
                 source crate or layer and one target, or delete it"
            ),
            Self::MetadataJson { source } => write!(
                f,
                "cargo metadata output is not the expected JSON: {source}; run `cargo metadata --format-version 1 \
                 --no-deps` by hand to see what cargo printed"
            ),
            Self::CargoMetadataFailed { code, stderr_tail } => {
                let code =
                    code.map_or_else(|| "none (killed by a signal)".to_owned(), |c| c.to_string());
                write!(
                    f,
                    "cargo metadata failed (exit code {code}): {}; fix the manifest error it reports, then re-run",
                    display_name(stderr_tail)
                )
            }
            Self::Io {
                context,
                path,
                source,
            } => {
                write!(
                    f,
                    "{context} failed for {}: {source}; check that the path exists and is readable",
                    path.display()
                )
            }
            Self::WalkLimit { limit, path } => write!(
                f,
                "the hygiene walk stopped after {limit} entries at {}: remove build output or generated folders \
                 from the crate folders (target/ is already skipped)",
                path.display()
            ),
            Self::Usage { given } => write!(
                f,
                "unknown xtask command `{}`: run `cargo run -p xtask -- layers` or `cargo run -p xtask -- hygiene`",
                display_name(given)
            ),
            Self::NoWorkspaceRoot { manifest_dir } => write!(
                f,
                "xtask's manifest directory {manifest_dir} has no parent folder: keep xtask/ directly under the \
                 workspace root"
            ),
        }
    }
}

impl std::error::Error for Error {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::TableToml { source } => Some(source),
            Self::MetadataJson { source } => Some(source),
            Self::Io { source, .. } => Some(source),
            Self::TableUnknownRole { .. }
            | Self::TableUnknownLayer { .. }
            | Self::TableUnknownCrate { .. }
            | Self::TableEdgeNotSameLayer { .. }
            | Self::TableEmptyRule { .. }
            | Self::CargoMetadataFailed { .. }
            | Self::WalkLimit { .. }
            | Self::Usage { .. }
            | Self::NoWorkspaceRoot { .. } => None,
        }
    }
}
