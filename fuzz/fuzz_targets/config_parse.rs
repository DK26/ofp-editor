// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: Bohemia Interactive a.s. (original C++)
// SPDX-FileCopyrightText: 2026 Plotroom contributors (Rust translation)
// Derived-From: BohemiaInteractive/CWR@ffc61838b7:apps/fuzzers/Fuzzer/fuzz_paramfile.cpp
// Modified: translated to Rust and changed, 2026-09-28. Subject to the Additional Terms
// (GPLv3 section 7) from Bohemia Interactive reproduced in NOTICE.
//! Fuzz target for the lossless config parser (`plotroom-config`; roadmap SP-09, D017).
//!
//! **Upstream mirror.** CWR's `fuzz_paramfile.cpp` feeds arbitrary bytes to `ParamFile::Parse(QIStream&)`, the
//! engine's *text* config reader (its comment says raP, but the body calls the text parser); a crash or hang is a
//! finding. Text has no magic, so no header forcing is needed (unlike the raP and savegame targets).
//!
//! **What it checks, beyond "no panic".** For every input: parsing fails only on a cap (size or depth); the tree
//! renders back to the input byte for byte (`render(parse(b)) == b`, testing-strategy §5); linting does not panic;
//! and patching each of up to 16 top-level values with a fixed integer either succeeds with no byte outside the
//! patched span changed, or is refused for a documented reason.
//!
//! **How libFuzzer drives it.** `fuzz_target!` defines the entry point libFuzzer calls with each generated input;
//! a panic, an abort or a sanitizer report is a finding, saved under `fuzz/artifacts/config_parse/`.

#![no_main]

use libfuzzer_sys::fuzz_target;
use plotroom_config::{Entry, EntryValueLexeme, Error, lint_syntax, parse};

fuzz_target!(|data: &[u8]| {
    let cst = match parse(data) {
        Ok(cst) => cst,
        // The only refusals: the size and depth caps.
        Err(Error::InputTooLarge { .. } | Error::NestingTooDeep { .. }) => return,
        Err(other) => panic!("parse failed on something other than a cap: {other}"),
    };
    assert_eq!(cst.render(), data, "render(parse(b)) != b");
    let _ = lint_syntax(&cst);

    for entry in cst.entries().into_iter().take(16) {
        let Entry::Value(_) = entry else { continue };
        let name = entry.name();
        let Some(target) = cst.entry_value(&[name.as_slice()]) else {
            continue;
        };
        match cst.replace_entry_value(target, EntryValueLexeme::int(7)) {
            Ok(patched) => {
                let (new_cst, edit) = patched.into_parts();
                let new = new_cst.render();
                edit.check_outside_unchanged(data, &new)
                    .expect("a patch changed bytes outside its span");
                assert_eq!(parse(&new).expect("patched text parses").render(), new);
            }
            // Removing a `"` from a bare value can change the preprocessor's quote state for the rest of the file;
            // the patch is then refused, as designed.
            Err(Error::PatchChangesStructure { .. }) => {}
            Err(other) => panic!("unexpected patch refusal: {other}"),
        }
    }
});
