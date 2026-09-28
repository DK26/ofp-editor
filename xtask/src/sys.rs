// SPDX-License-Identifier: GPL-3.0-or-later
//! The only side effects in xtask: running `cargo metadata`, listing folders and reading `.rs` files.
//!
//! **Why a module of its own.** The workspace bans files, processes and environment reads outside the crates
//! crate-map §2.3 names (`clippy.toml`). xtask is repository tooling, so it may read the tree and run cargo, but
//! the exemption is kept to this one module with a module-level `#![expect(...)]`: every other xtask module stays
//! under the bans, and the expectation fails the lint run if these calls ever disappear.
//!
//! **Bounds.** The walk never follows symbolic links (no loops), skips `target` folders (build output), and stops
//! with [`Error::WalkLimit`] after [`MAX_WALK_ENTRIES`] entries instead of running away on a huge generated tree.

#![expect(
    clippy::disallowed_methods,
    clippy::disallowed_types,
    reason = "xtask is repository tooling (crate-map §12): it lists the source tree and runs cargo metadata; the \
              exemption is confined to this module"
)]

use std::path::{Component, Path, PathBuf};
use std::process::Command;

use crate::Error;
use crate::hygiene::{NameKind, NameSite, module_decls};

/// Most entries (files and folders) one hygiene walk visits before it gives up. The whole repository has a few
/// thousand; this leaves room for growth while stopping a walk into an unexpected generated tree.
pub const MAX_WALK_ENTRIES: usize = 50_000;

/// How much of cargo's standard error an [`Error::CargoMetadataFailed`] keeps (the end, where cargo puts the cause).
const STDERR_TAIL_CHARS: usize = 2_000;

/// Runs `cargo metadata --format-version 1 --no-deps` for the workspace at `workspace_root` and returns its output.
///
/// Uses the cargo that compiled xtask (`env!("CARGO")`, fixed at compile time), so no environment variable is read
/// at run time. `--no-deps` skips dependency resolution: the call is offline and fast.
///
/// # Errors
///
/// [`Error::Io`] when cargo cannot be started; [`Error::CargoMetadataFailed`] when it exits with a failure.
pub fn cargo_metadata(workspace_root: &Path) -> Result<Vec<u8>, Error> {
    let manifest = workspace_root.join("Cargo.toml");
    let output = Command::new(env!("CARGO"))
        .arg("metadata")
        .args(["--format-version", "1", "--no-deps", "--offline"])
        .arg("--manifest-path")
        .arg(&manifest)
        .output()
        .map_err(|source| Error::Io {
            context: "starting cargo metadata",
            path: manifest.clone(),
            source,
        })?;
    if output.status.success() {
        return Ok(output.stdout);
    }
    // Keep the end of stderr: cargo prints the failing manifest and the cause last.
    let stderr = String::from_utf8_lossy(&output.stderr);
    let skip = stderr.chars().count().saturating_sub(STDERR_TAIL_CHARS);
    Err(Error::CargoMetadataFailed {
        code: output.status.code(),
        stderr_tail: stderr.chars().skip(skip).collect(),
    })
}

/// Lists every file and folder name under each of `roots`, plus the inline `mod` declarations of every `.rs` file,
/// as [`NameSite`]s located relative to `workspace_root` (with `/` separators on every OS).
///
/// A root that does not exist is skipped (for example `fuzz/fuzz_targets/` in a trimmed checkout).
///
/// # Errors
///
/// [`Error::Io`] when a folder cannot be listed or a file cannot be read; [`Error::WalkLimit`] past
/// [`MAX_WALK_ENTRIES`].
pub fn walk_name_sites(workspace_root: &Path, roots: &[PathBuf]) -> Result<Vec<NameSite>, Error> {
    let mut sites = Vec::new();
    let mut pending: Vec<PathBuf> = roots.to_vec();
    let mut visited = 0_usize;
    while let Some(dir) = pending.pop() {
        let entries = match std::fs::read_dir(&dir) {
            Ok(entries) => entries,
            // A missing root is not an error: the folder is optional.
            Err(source) if source.kind() == std::io::ErrorKind::NotFound => continue,
            Err(source) => {
                return Err(Error::Io {
                    context: "listing a folder",
                    path: dir,
                    source,
                });
            }
        };
        for entry in entries {
            let entry = entry.map_err(|source| Error::Io {
                context: "listing a folder",
                path: dir.clone(),
                source,
            })?;
            visited = visited.saturating_add(1);
            if visited > MAX_WALK_ENTRIES {
                return Err(Error::WalkLimit {
                    limit: MAX_WALK_ENTRIES,
                    path: dir,
                });
            }
            let path = entry.path();
            // `file_type` does not follow symbolic links, so a link is never descended into.
            let file_type = entry.file_type().map_err(|source| Error::Io {
                context: "reading a file type",
                path: path.clone(),
                source,
            })?;
            let name = entry.file_name().to_string_lossy().into_owned();
            let location = relative_location(workspace_root, &path);
            if file_type.is_dir() && name == "target" {
                continue;
            }
            sites.push(NameSite::new(
                NameKind::Path,
                location.clone(),
                name.clone(),
            ));
            if file_type.is_dir() {
                pending.push(path);
            } else if file_type.is_file() && name.ends_with(".rs") {
                let bytes = std::fs::read(&path).map_err(|source| Error::Io {
                    context: "reading a Rust source file",
                    path: path.clone(),
                    source,
                })?;
                for (line, module) in module_decls(&String::from_utf8_lossy(&bytes)) {
                    sites.push(NameSite::new(
                        NameKind::Module,
                        format!("{location}:{line}"),
                        module,
                    ));
                }
            }
        }
    }
    Ok(sites)
}

/// `path` relative to `root`, joined with `/`, for stable locations on every OS; the full path if it is not
/// under `root`.
fn relative_location(root: &Path, path: &Path) -> String {
    let relative = path.strip_prefix(root).unwrap_or(path);
    relative
        .components()
        .filter_map(|c| match c {
            Component::Normal(part) => Some(part.to_string_lossy().into_owned()),
            Component::Prefix(_)
            | Component::RootDir
            | Component::CurDir
            | Component::ParentDir => None,
        })
        .collect::<Vec<_>>()
        .join("/")
}
