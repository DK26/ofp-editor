// SPDX-License-Identifier: GPL-3.0-or-later
//! `cargo run -p xtask -- <layers|hygiene|help>`: prints the report and sets the exit code.
//!
//! Exit codes: 0 when the check is clean (or for `help`), 1 when it found something, 2 when it could not run
//! (bad arguments, invalid layer table, `cargo metadata` failure). All logic lives in the library (`xtask::cli`),
//! where it is unit-tested; this file only prints.

use std::process::ExitCode;

use xtask::cli::{Command, Outcome, USAGE, parse_args, run_hygiene, run_layers, workspace_root};

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    match run(&args) {
        Ok(Some(Outcome::Clean { summary })) => {
            println!("{summary}");
            ExitCode::SUCCESS
        }
        Ok(Some(Outcome::Findings { lines, summary })) => {
            for line in lines {
                eprintln!("{line}");
            }
            eprintln!("{summary}");
            ExitCode::from(1)
        }
        Ok(None) => {
            println!("{USAGE}");
            ExitCode::SUCCESS
        }
        Err(err) => {
            eprintln!("xtask: {err}");
            eprintln!("{USAGE}");
            ExitCode::from(2)
        }
    }
}

/// Parses the arguments and runs the command; `None` means help was printed on request.
fn run(args: &[String]) -> Result<Option<Outcome>, xtask::Error> {
    match parse_args(args)? {
        Command::Help => Ok(None),
        Command::Layers => run_layers(&workspace_root()?).map(Some),
        Command::Hygiene => run_hygiene(&workspace_root()?).map(Some),
    }
}
