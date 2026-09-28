// SPDX-License-Identifier: GPL-3.0-or-later
//! Caps, boundaries, overflow and adversarial input for the parser (`AGENTS.md`, "Parser Security Testing").

use crate::cst::issues::IssueKind;
use crate::error::Error;
use crate::limits::{Limits, MAX_CONFIG_TEXT_BYTES, MAX_NESTING_DEPTH};
use crate::text::TextOffset;
use crate::{lint_syntax, parse, parse_with_limits};

/// Repeats `unit` `count` times.
fn repeat(unit: &[u8], count: usize) -> Vec<u8> {
    unit.repeat(count)
}

/// Nested classes `class a{` × `depth`, closed again.
fn nested_classes(depth: usize) -> Vec<u8> {
    let mut text = repeat(b"class a{", depth);
    text.extend(repeat(b"};", depth));
    text
}

// ── Boundary tests ───────────────────────────────────────────────────────────────────────────────────────────────

/// An input exactly at the size cap parses; one byte more is refused before any scanning.
///
/// Why: the size cap keeps every offset exact (`u32`) and bounds work on hostile input; both sides are checked.
#[test]
fn size_cap_both_sides() {
    let limits = Limits::new(16, MAX_NESTING_DEPTH);
    let at_cap = repeat(b" ", 16);
    assert_eq!(parse_with_limits(&at_cap, limits).unwrap().render(), at_cap);
    let over = repeat(b" ", 17);
    assert_eq!(
        parse_with_limits(&over, limits).unwrap_err(),
        Error::InputTooLarge { len: 17, cap: 16 }
    );
}

/// The default size cap is 64 MiB and applies to `parse`; one byte over it is refused cheaply.
///
/// Why: the default cap must hold for the ordinary entry point, and the refusal must not scan 64 MiB first.
#[test]
fn default_size_cap_is_64_mib() {
    assert_eq!(MAX_CONFIG_TEXT_BYTES, 64 * 1024 * 1024);
    let over = vec![b' '; MAX_CONFIG_TEXT_BYTES as usize + 1];
    assert_eq!(
        parse(&over).unwrap_err(),
        Error::InputTooLarge {
            len: u64::from(MAX_CONFIG_TEXT_BYTES) + 1,
            cap: MAX_CONFIG_TEXT_BYTES
        }
    );
}

/// Nesting exactly at the depth cap parses; one level more fails with the offset of the level that passed it.
///
/// Why: recursion depth is the parser's only stack risk; the error must say where the file became too deep.
#[test]
fn depth_cap_both_sides() {
    let limits = Limits::new(MAX_CONFIG_TEXT_BYTES, 3);
    assert!(parse_with_limits(&nested_classes(3), limits).is_ok());
    let err = parse_with_limits(&nested_classes(4), limits).unwrap_err();
    // The fourth `{` is at offset 3 * 8 + 7 = 31.
    assert_eq!(
        err,
        Error::NestingTooDeep {
            offset: TextOffset::from_raw(31),
            depth: 4,
            cap: 3
        }
    );
}

/// Array literals count towards the same depth cap as classes.
///
/// Why: `{{{...}}}` recurses in the engine's array parser just as classes do (`ParamFileParse.cpp#L453-L461`).
#[test]
fn arrays_and_classes_share_the_depth_cap() {
    let limits = Limits::new(MAX_CONFIG_TEXT_BYTES, 3);
    assert!(parse_with_limits(b"class c{a[]={{1}};};", limits).is_ok());
    let err = parse_with_limits(b"class c{a[]={{{1}}};};", limits).unwrap_err();
    assert!(
        matches!(
            err,
            Error::NestingTooDeep {
                depth: 4,
                cap: 3,
                ..
            }
        ),
        "{err:?}"
    );
}

/// Values of 2047 bytes pass; 2048 bytes are reported as too long. Names likewise.
///
/// Why: the game keeps 2047 bytes of a value and does not keep a name of 2048 bytes intact (`ParamFilePrivate.inc#L10`,
/// `#L52-L55`, `#L119-L126`); the tree keeps every byte and reports the cut.
#[test]
fn value_and_name_length_boundaries() {
    for (len, expect_issue) in [(2047usize, false), (2048, true)] {
        let mut text = b"v=\"".to_vec();
        text.extend(repeat(b"a", len));
        text.extend_from_slice(b"\";");
        let cst = parse(&text).unwrap();
        let has = lint_syntax(&cst)
            .iter()
            .any(|issue| issue.kind() == IssueKind::ValueTooLong);
        assert_eq!(has, expect_issue, "value of {len} bytes");
        let mut text = repeat(b"n", len);
        text.extend_from_slice(b"=1;");
        let cst = parse(&text).unwrap();
        let has = lint_syntax(&cst)
            .iter()
            .any(|issue| issue.kind() == IssueKind::NameTooLong);
        assert_eq!(has, expect_issue, "name of {len} bytes");
    }
}

/// Every single byte, and every pair of bytes, round-trips.
///
/// Why: the identity invariant must hold for any byte string, not only for text that looks like config.
#[test]
fn every_byte_and_byte_pair_round_trips() {
    for first in 0..=255u8 {
        assert_eq!(parse(&[first]).unwrap().render(), [first]);
        for second in 0..=255u8 {
            let text = [first, second];
            assert_eq!(parse(&text).unwrap().render(), text);
        }
    }
}

// ── Security edge cases ──────────────────────────────────────────────────────────────────────────────────────────

/// Ten thousand nested classes or array literals fail with `NestingTooDeep` instead of overflowing the stack.
///
/// Why: hostile files must not exhaust the editor's stack; the parser refuses before it recurses past the cap.
#[test]
fn deep_nesting_is_refused_without_stack_overflow() {
    let err = parse(&nested_classes(10_000)).unwrap_err();
    assert!(
        matches!(err, Error::NestingTooDeep { depth, cap, .. } if depth == MAX_NESTING_DEPTH + 1 && cap == MAX_NESTING_DEPTH)
    );
    let mut text = b"a[]=".to_vec();
    text.extend(repeat(b"{", 10_000));
    let err = parse(&text).unwrap_err();
    assert!(matches!(err, Error::NestingTooDeep { .. }), "{err:?}");
    // Unbalanced closing braces are not nesting at all.
    let text = repeat(b"}", 10_000);
    assert_eq!(parse(&text).unwrap().render(), text);
}

/// A one-megabyte bare value and a one-megabyte unterminated string parse and round-trip.
///
/// Why: long lexemes must not be truncated or cause quadratic work (the scan is a single pass).
#[test]
fn megabyte_lexemes_round_trip() {
    let mut text = b"v = ".to_vec();
    text.extend(repeat(b"x", 1 << 20));
    text.push(b';');
    let cst = parse(&text).unwrap();
    assert_eq!(cst.render(), text);
    let mut text = b"v = \"".to_vec();
    text.extend(repeat(b"y", 1 << 20));
    assert_eq!(parse(&text).unwrap().render(), text);
}

/// Hostile mixes of quotes, comment openers, directives and control bytes round-trip.
///
/// Why: downloaded missions are untrusted; no input may lose or duplicate a byte.
#[test]
fn hostile_mixes_round_trip() {
    let samples: [&[u8]; 10] = [
        b"\"/*\"*/\"//\n#define\r\r\n\\\n",
        b"/*/ x = 1; */ y = 2;",
        b"#\n##\n# include\n#include \"a\" /* c\n d */ x=1;",
        b"a[]={\"a\" \"b\"};b[]={,};c[]={;}",
        b"class{class:{};};}}}}",
        b"enum{A=,B};enum{=};__EXEC(;__EXEC)",
        b"x=\r\r\r\n\x00\x01\x02\x7F\xFF;",
        b"\x0B\x0C\t x = 1;\x0B",
        b"a[]={1\n\n\n2\n}",
        b"\"\"\"\"\"\x0B\"\"\"\xFE\x03\x00\n",
    ];
    for text in samples {
        let cst = parse(text).unwrap();
        assert_eq!(cst.render(), text, "{:?}", String::from_utf8_lossy(text));
        // Linting a hostile tree must not panic either; every issue lies inside the text.
        for issue in lint_syntax(&cst) {
            assert!(issue.span().end().to_raw() as usize <= text.len());
        }
    }
}

/// Bidirectional-control and zero-width characters inside strings and comments are kept byte for byte.
///
/// Why: such characters can hide text from a reviewer; the tree must neither drop nor normalise them.
///
/// How: U+202E (RIGHT-TO-LEFT OVERRIDE) is E2 80 AE in UTF-8 and U+200B (ZERO WIDTH SPACE) is E2 80 8B; both are
/// written as escapes and compared as bytes.
#[test]
fn hidden_characters_are_kept_exactly() {
    let text = b"s = \"a\xE2\x80\xAEb\xE2\x80\x8Bc\"; // \xE2\x80\xAE\n/* \xE2\x80\x8B */";
    let cst = parse(text).unwrap();
    assert_eq!(cst.render(), text);
    let Some(crate::Entry::Value(s)) = cst.find(&[b"s"]) else {
        panic!("s")
    };
    assert_eq!(s.value().unwrap().text(), b"a\xE2\x80\xAEb\xE2\x80\x8Bc");
}

/// Stack size of the thread the walker test runs on: 512 KiB, half of the 1 MiB main-thread stack the Windows MSVC
/// linker gives by default, which is the smallest stack a caller of this crate is expected to parse on
/// (AGENTS.md "Threads are named and sized").
const WALKER_TEST_STACK: usize = 512 * 1024;

/// At the depth cap, parsing and every tree walker (render, dump, lint, lookup, patch with its verification parse,
/// derived `Debug`, drop) run on a 512 KiB stack; one level more is refused with `NestingTooDeep`.
///
/// Why: AGENTS.md "Bounded recursion": a depth limit is sized against the smallest stack any walker of the tree runs
/// on, derived `Debug` and drop glue included, and both sides are tested on a thread with a named stack size.
///
/// How: 63 nested classes plus an array literal inside the innermost one make exactly 64 levels (the cap); 64 classes
/// plus the array make 65.
#[test]
fn walkers_fit_a_small_stack_at_the_depth_cap() {
    let worker = std::thread::Builder::new()
        .name("depth-cap-walkers".to_owned())
        .stack_size(WALKER_TEST_STACK)
        .spawn(|| {
            let levels = MAX_NESTING_DEPTH as usize - 1;
            let mut text = repeat(b"class a{", levels);
            text.extend_from_slice(b"v=1;w[]={1};");
            text.extend(repeat(b"};", levels));
            let cst = parse(&text).unwrap();
            assert_eq!(cst.render(), text);
            assert!(cst.debug_tree().starts_with("File[ClassDecl["));
            assert!(lint_syntax(&cst).is_empty());
            assert!(!format!("{:?}", cst.green()).is_empty());
            let mut path: Vec<&[u8]> = vec![b"a"; levels];
            path.push(b"v");
            let target = cst.entry_value(&path).unwrap();
            let (patched, _) = cst
                .replace_entry_value(target, crate::EntryValueLexeme::int(2))
                .unwrap()
                .into_parts();
            assert_eq!(patched.width().to_raw() as usize, text.len());
            drop(patched);
            drop(cst);
            let mut deeper = repeat(b"class a{", levels + 1);
            deeper.extend_from_slice(b"w[]={1};");
            let err = parse(&deeper).unwrap_err();
            assert!(
                matches!(err, Error::NestingTooDeep { depth, .. } if depth == MAX_NESTING_DEPTH + 1)
            );
        })
        .unwrap();
    worker.join().unwrap();
}
