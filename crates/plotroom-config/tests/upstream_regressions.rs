// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: Bohemia Interactive a.s. (original C++)
// SPDX-FileCopyrightText: 2026 Plotroom contributors (Rust translation)
// Derived-From: BohemiaInteractive/CWR@ffc61838b7:tests/unit/engine/Poseidon/IO/test_paramFile_defaults.cpp
// Derived-From: ofpisnotdead-com/CWR-CE@b67bf3bd62:tests/unit/engine/Poseidon/IO/test_paramFile_defaults.cpp
// Modified: translated to Rust and changed, 2026-09-28. Subject to the Additional Terms
// (GPLv3 section 7) from Bohemia Interactive reproduced in NOTICE.
//! Port of the two parser-robustness regressions in `test_paramFile_defaults.cpp` (found upstream by the
//! `fuzz_paramfile` libFuzzer target). The file's six other cases check C++ dependency-injection wiring and do not
//! apply (CSV status `not-applicable` for that part).
//!
//! Upstream passes if `Parse` returns at all (it used to spin forever). Here each case also proves the byte-exact
//! round trip and the issue the game would report.

use plotroom_config::{IssueKind, StopReason, lint_syntax, parse};

/// Upstream `TEST_CASE("ParamFile: unterminated quoted string terminates at EOF")`: the fuzz reproducer
/// `22 0b 22 22 22 fe 03 00 0a`.
///
/// Why: a quoted string opened and never closed must end at the end of input, not loop forever
/// (`ParamFilePrivate.inc#L32-L38`, the CWR fix).
///
/// How: the bytes are `"` VT `"` `""` 0xFE 0x03 NUL LF. The first `"` opens a value-less name slot: the first word
/// is empty, so the statement stops at once; everything is kept.
#[test]
fn unterminated_quoted_string_terminates_at_eof() {
    let repro: [u8; 9] = [0x22, 0x0b, 0x22, 0x22, 0x22, 0xfe, 0x03, 0x00, 0x0a];
    let cst = parse(&repro).unwrap();
    assert_eq!(cst.render(), repro);
    assert!(cst.entries().is_empty());
    let kinds: Vec<IssueKind> = lint_syntax(&cst).iter().map(|issue| issue.kind()).collect();
    assert!(
        kinds.contains(&IssueKind::Stopped(StopReason::ExpectedEquals)),
        "{kinds:?}"
    );
}

/// Upstream `TEST_CASE("ParamFile: unterminated string inside an array does not hang")`: `x[]={"abc`.
///
/// Why: the array element reader had the same end-of-input spin; the literal must stop at the end of input and the
/// entry be dropped (`ParamFileParse.cpp#L502-L506`).
#[test]
fn unterminated_string_inside_an_array_does_not_hang() {
    let config = b"x[]={\"abc";
    let cst = parse(config).unwrap();
    assert_eq!(cst.render(), config);
    assert!(cst.find(&[b"x"]).is_none());
    let kinds: Vec<IssueKind> = lint_syntax(&cst).iter().map(|issue| issue.kind()).collect();
    assert!(kinds.contains(&IssueKind::UnterminatedString), "{kinds:?}");
    assert!(
        kinds.contains(&IssueKind::Stopped(StopReason::ArrayEndOfInput)),
        "{kinds:?}"
    );
}
