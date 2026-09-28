// SPDX-License-Identifier: GPL-3.0-or-later
//! Property tests of the identity invariant `render(parse(b)) == b` (roadmap SP-09; core-document-model §12 R1).
//!
//! **What they prove.** (a) Any byte string within the size cap renders back unchanged. (b) A random config built
//! from a statement model, with random trivia at every position the game accepts it, renders back unchanged, parses
//! to exactly the model's skeleton (kinds, names, raw lexemes) and has no syntax issue. (c) Injecting one pattern the
//! game rejects keeps the round trip and reports the matching issue.
//!
//! **Proptest in brief.** `proptest!` turns each `fn` into a `#[test]` that runs the body on generated inputs and,
//! on failure, shrinks the input to a minimal case. The config below pins the random seed and the case count, and
//! turns off regression files, so runs are deterministic and write nothing into the source tree.

mod support;

use plotroom_config::{IssueKind, lint_syntax, parse};
use proptest::prelude::*;
use proptest::test_runner::{Config, RngSeed};
use support::{Renderer, skeleton, statements};

/// Seeded, bounded, file-free proptest configuration shared by the properties in this file.
fn config(cases: u32) -> Config {
    Config {
        cases,
        rng_seed: RngSeed::Fixed(0x5909_C0F1),
        failure_persistence: None,
        ..Config::default()
    }
}

proptest! {
    #![proptest_config(config(512))]

    /// (a) Arbitrary bytes round-trip.
    ///
    /// Why: the invariant holds for every byte string, not only for config-like text (untrusted downloads).
    #[test]
    fn arbitrary_bytes_round_trip(bytes in proptest::collection::vec(any::<u8>(), 0..512)) {
        let cst = parse(&bytes).unwrap();
        prop_assert_eq!(cst.render(), bytes);
    }

    /// (a') Config-flavoured byte soup (structural bytes over-represented) round-trips.
    ///
    /// Why: uniform random bytes rarely form `class`, `/*` or `"`; this soup reaches the parser's deeper states.
    #[test]
    fn structural_byte_soup_round_trips(
        pieces in proptest::collection::vec(
            prop_oneof![
                Just(&b"class "[..]), Just(&b"enum"[..]), Just(&b"__EXEC"[..]), Just(&b"{"[..]), Just(&b"}"[..]),
                Just(&b"["[..]), Just(&b"]"[..]), Just(&b"="[..]), Just(&b";"[..]), Just(&b","[..]),
                Just(&b"\""[..]), Just(&b"//"[..]), Just(&b"/*"[..]), Just(&b"*/"[..]), Just(&b"\n"[..]),
                Just(&b"\r"[..]), Just(&b"\r\n"[..]), Just(&b"#define A 1"[..]), Just(&b"#if"[..]), Just(&b" "[..]),
                Just(&b"\\"[..]), Just(&b"x"[..]), Just(&b"12"[..]), Just(&b":"[..]), Just(&b"("[..]), Just(&b")"[..]),
                Just(&b"\x00"[..]), Just(&b"\xEF\xBB\xBF"[..]),
            ],
            0..64,
        )
    ) {
        let bytes: Vec<u8> = pieces.concat();
        let cst = parse(&bytes).unwrap();
        prop_assert_eq!(cst.render(), bytes);
    }
}

proptest! {
    #![proptest_config(config(256))]

    /// (b) A generated config with injected trivia round-trips, parses to the model's skeleton, and is clean.
    ///
    /// Why: this is the SP-09 exit property: trivia anywhere the game accepts it changes neither the bytes nor
    /// what the game reads.
    #[test]
    fn generated_configs_with_trivia_round_trip(model in statements(), seeds in proptest::collection::vec(any::<u32>(), 1..64)) {
        let mut renderer = Renderer::new(seeds);
        let expected = renderer.statements(&model);
        let text = renderer.out;
        let cst = parse(&text).unwrap();
        prop_assert_eq!(cst.render(), text.clone());
        prop_assert_eq!(skeleton(&cst), expected, "text: {:?}", String::from_utf8_lossy(&text));
        let issues = lint_syntax(&cst);
        prop_assert!(issues.is_empty(), "issues {:?} in {:?}", issues, String::from_utf8_lossy(&text));
    }

    /// (c) One engine-illegal pattern appended to a generated config round-trips and is reported.
    ///
    /// Why: the tree must keep text the game rejects, and the lint must name what the game does with it.
    #[test]
    fn illegal_patterns_are_kept_and_reported(
        model in statements(),
        seeds in proptest::collection::vec(any::<u32>(), 1..64),
        pattern in 0usize..4,
    ) {
        let (suffix, kind): (&[u8], IssueKind) = [
            (&b"\nbad [] = {};"[..], IssueKind::SpaceBeforeArrayBrackets),
            (b"\nbad = \"q\" ;", IssueKind::TriviaAfterQuotedValue),
            (b"\nclass Bad;", IssueKind::ForwardClassDeclaration),
            (b"\nbad[][] = {};", IssueKind::MultiDimArrayName),
        ][pattern];
        let mut renderer = Renderer::new(seeds);
        renderer.statements(&model);
        let mut text = renderer.out;
        text.extend_from_slice(suffix);
        let cst = parse(&text).unwrap();
        prop_assert_eq!(cst.render(), text.clone());
        let kinds: Vec<IssueKind> = lint_syntax(&cst).iter().map(|issue| issue.kind()).collect();
        prop_assert!(kinds.contains(&kind), "{:?} not in {:?} for {:?}", kind, kinds, String::from_utf8_lossy(&text));
    }
}
