// SPDX-License-Identifier: GPL-3.0-or-later
//! The two xtask commands, from command line to report.
//!
//! **What.** [`parse_args`] turns the arguments into a [`Command`]; [`run_layers`] and [`run_hygiene`] gather their
//! input through [`crate::sys`], run the pure checks and return an [`Outcome`]. `main.rs` prints the outcome and maps
//! it to an exit code (0 clean, 1 findings, 2 could not run), so everything above the printing is testable.

use std::path::{Path, PathBuf};

use crate::Error;
use crate::hygiene::{check_sites, metadata_sites};
use crate::layers::{LayerTable, check};
use crate::metadata::Metadata;
use crate::sys;

/// How to call xtask.
pub const USAGE: &str = "usage: cargo run -p xtask -- <command>\n\
    \n\
    commands:\n  \
    layers    check every workspace crate's dependencies against xtask/layers.toml (crate-map §2.1-§2.5)\n  \
    hygiene   refuse third-party marks and island names in crate, target, module, file and folder names\n  \
    help      print this text";

/// A parsed command line.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Command {
    /// `layers`
    Layers,
    /// `hygiene`
    Hygiene,
    /// `help`, `--help` or `-h`
    Help,
}

/// What a check found.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Outcome {
    /// Nothing to report; the summary says what was checked.
    Clean {
        /// One line: what was checked and how much.
        summary: String,
    },
    /// Findings, one message each, and a summary line.
    Findings {
        /// One message per finding, each with its next action.
        lines: Vec<String>,
        /// One line: how many findings.
        summary: String,
    },
}

/// Parses the arguments after the program name.
///
/// # Errors
///
/// [`Error::Usage`] for no command, an unknown command or extra arguments.
pub fn parse_args(args: &[String]) -> Result<Command, Error> {
    match args {
        [one] => match one.as_str() {
            "layers" => Ok(Command::Layers),
            "hygiene" => Ok(Command::Hygiene),
            "help" | "--help" | "-h" => Ok(Command::Help),
            _ => Err(Error::Usage { given: one.clone() }),
        },
        _ => Err(Error::Usage {
            given: args.join(" "),
        }),
    }
}

/// The workspace root: the parent of xtask's own manifest folder, fixed at compile time.
///
/// # Errors
///
/// [`Error::NoWorkspaceRoot`] if xtask's folder has no parent.
pub fn workspace_root() -> Result<PathBuf, Error> {
    const MANIFEST_DIR: &str = env!("CARGO_MANIFEST_DIR");
    Path::new(MANIFEST_DIR)
        .parent()
        .map(Path::to_path_buf)
        .ok_or(Error::NoWorkspaceRoot {
            manifest_dir: MANIFEST_DIR,
        })
}

/// Runs the layer check on the workspace at `root` with the committed table.
///
/// # Errors
///
/// When the table is invalid, or `cargo metadata` fails or prints something unreadable.
pub fn run_layers(root: &Path) -> Result<Outcome, Error> {
    let table = LayerTable::builtin()?;
    let metadata = Metadata::parse(&sys::cargo_metadata(root)?)?;
    let members = metadata.members().len();
    let violations = check(&table, &metadata);
    Ok(outcome(
        violations.iter().map(ToString::to_string).collect(),
        format!("layers: {members} workspace crates checked against xtask/layers.toml"),
        "layer violation(s)",
    ))
}

/// Runs the naming check on the workspace at `root`: member crate and target names, and every file, folder and
/// inline module name under the member folders and `fuzz/fuzz_targets/` (not all of `fuzz/`, whose local corpus can
/// hold tens of thousands of generated file names).
///
/// # Errors
///
/// When `cargo metadata` fails, or a folder or file cannot be read.
pub fn run_hygiene(root: &Path) -> Result<Outcome, Error> {
    let metadata = Metadata::parse(&sys::cargo_metadata(root)?)?;
    let mut sites = metadata_sites(&metadata);
    let mut roots: Vec<PathBuf> = metadata
        .members()
        .iter()
        .filter_map(|member| {
            Path::new(member.manifest_path())
                .parent()
                .map(Path::to_path_buf)
        })
        .collect();
    roots.push(root.join("fuzz").join("fuzz_targets"));
    sites.extend(sys::walk_name_sites(root, &roots)?);
    let findings = check_sites(&sites);
    Ok(outcome(
        findings.iter().map(ToString::to_string).collect(),
        format!(
            "hygiene: {} names checked against {} marks",
            sites.len(),
            crate::hygiene::MARKS.len()
        ),
        "naming finding(s)",
    ))
}

/// Builds the outcome: clean when there are no lines, otherwise findings with a count.
fn outcome(lines: Vec<String>, checked: String, noun: &str) -> Outcome {
    if lines.is_empty() {
        Outcome::Clean {
            summary: format!("{checked}: clean"),
        }
    } else {
        let summary = format!("{checked}: {} {noun}", lines.len());
        Outcome::Findings { lines, summary }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Owned argument list from string slices.
    fn args(list: &[&str]) -> Vec<String> {
        list.iter().map(|s| (*s).to_owned()).collect()
    }

    // ── Basic functionality ─────────────────────────────────────────────────────────────────────────────────────

    /// The two commands and the help spellings parse.
    #[test]
    fn known_commands_parse() {
        assert_eq!(parse_args(&args(&["layers"])).unwrap(), Command::Layers);
        assert_eq!(parse_args(&args(&["hygiene"])).unwrap(), Command::Hygiene);
        for help in ["help", "--help", "-h"] {
            assert_eq!(parse_args(&args(&[help])).unwrap(), Command::Help);
        }
        assert!(USAGE.contains("layers") && USAGE.contains("hygiene"));
    }

    /// The workspace root is the folder above xtask's manifest.
    #[test]
    fn workspace_root_is_above_xtask() {
        let root = workspace_root().unwrap();
        assert_eq!(root.join("xtask"), Path::new(env!("CARGO_MANIFEST_DIR")));
    }

    /// An outcome with lines counts them; one without is clean.
    #[test]
    fn outcome_counts_findings() {
        assert_eq!(
            outcome(Vec::new(), "x".into(), "n"),
            Outcome::Clean {
                summary: "x: clean".into()
            }
        );
        assert_eq!(
            outcome(vec!["a".into(), "b".into()], "x".into(), "things"),
            Outcome::Findings {
                lines: vec!["a".into(), "b".into()],
                summary: "x: 2 things".into()
            }
        );
    }

    // ── Error field & Display verification ──────────────────────────────────────────────────────────────────────

    /// No command, an unknown one, or extra arguments are usage errors that name what was given and the fix.
    #[test]
    fn bad_command_lines_are_usage_errors() {
        for (given, shown) in [
            (vec![], ""),
            (vec!["lint"], "lint"),
            (vec!["layers", "extra"], "layers extra"),
        ] {
            let err = parse_args(&args(&given)).unwrap_err();
            assert!(
                matches!(&err, Error::Usage { given } if given == shown),
                "{err:?}"
            );
            assert!(
                err.to_string().contains("cargo run -p xtask -- layers"),
                "{err}"
            );
        }
    }

    // ── Security edge-case tests ────────────────────────────────────────────────────────────────────────────────

    /// A hostile argument is echoed escaped, so it cannot rewrite the terminal line.
    #[test]
    fn hostile_argument_is_escaped() {
        let text = parse_args(&args(&["lay\u{202E}ers\u{1B}[2J"]))
            .unwrap_err()
            .to_string();
        assert!(text.is_ascii(), "{text:?}");
        assert!(
            text.contains("\\u{202e}") && text.contains("\\u{1b}"),
            "{text}"
        );
    }
}
