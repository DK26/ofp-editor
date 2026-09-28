// SPDX-License-Identifier: GPL-3.0-or-later
//! Property test of span patches: bytes outside the patched span never change (roadmap SP-09; core-document-model
//! §12 R2).
//!
//! **What it proves.** For a random config with injected trivia, a random value entry and a random valid lexeme,
//! the patch either succeeds with every byte outside its declared span unchanged, the skeleton unchanged except the
//! patched value, and `parse(render(p))` identical to the patched tree; or it is refused for the one documented
//! reason a valid lexeme can be refused (a quoted value would sit before whitespace and `;`).

mod support;

use plotroom_config::{EntryValueLexeme, Error, WriterProfile, lint_syntax, parse};
use proptest::prelude::*;
use proptest::test_runner::{Config, RngSeed};
use support::{Renderer, Skel, skeleton, statements, value_paths};

/// Replaces the value at `path` in a skeleton.
#[cfg(test)]
fn with_value(skel: &[Skel], path: &[String], lexeme: &[u8]) -> Vec<Skel> {
    skel.iter()
        .map(|statement| match (statement, path) {
            (Skel::Value(name, _), [last]) if name == last => {
                Skel::Value(name.clone(), lexeme.to_vec())
            }
            (Skel::Class(name, base, body), [first, rest @ ..])
                if name == first && !rest.is_empty() =>
            {
                Skel::Class(name.clone(), base.clone(), with_value(body, rest, lexeme))
            }
            _ => statement.clone(),
        })
        .collect()
}

/// A valid lexeme chosen by `choice` and `number`.
#[cfg(test)]
fn lexeme(choice: u8, number: i32, text: &str) -> EntryValueLexeme {
    match choice % 4 {
        0 => EntryValueLexeme::int(number),
        1 => EntryValueLexeme::float(
            f32::from(i16::try_from(number % 1000).unwrap_or(0)) / 8.0,
            WriterProfile::RemasteredText,
        )
        .unwrap(),
        2 => EntryValueLexeme::quoted(text.as_bytes()).unwrap(),
        _ => EntryValueLexeme::bare(b"WEST").unwrap(),
    }
}

proptest! {
    #![proptest_config(Config { cases: 256, rng_seed: RngSeed::Fixed(0x5909_0A7C), failure_persistence: None, ..Config::default() })]

    /// A patch changes only its span, keeps the rest of the skeleton, and re-reads as the patched tree.
    ///
    /// Why: the SP-09 exit criterion, over random files, targets and lexemes.
    #[test]
    fn patches_change_only_their_span(
        model in statements(),
        seeds in proptest::collection::vec(any::<u32>(), 1..64),
        pick in any::<usize>(),
        choice in any::<u8>(),
        number in any::<i32>(),
        text in "[ -~]{0,12}",
    ) {
        let mut renderer = Renderer::new(seeds);
        let skel = renderer.statements(&model);
        let old = renderer.out;
        let paths = value_paths(&skel);
        prop_assume!(!paths.is_empty());
        let path = &paths[pick % paths.len()];
        let names: Vec<&[u8]> = path.iter().map(|name| name.as_bytes()).collect();

        let cst = parse(&old).unwrap();
        let target = cst.entry_value(&names).unwrap();
        let lexeme = lexeme(choice, number, &text);
        let lexeme_bytes = lexeme.as_bytes().to_vec();
        match cst.replace_entry_value(target, lexeme) {
            Ok(patched) => {
                let (new_cst, edit) = patched.into_parts();
                let new = new_cst.render();
                prop_assert!(edit.check_outside_unchanged(&old, &new).is_ok());
                let reread = parse(&new).unwrap();
                prop_assert_eq!(reread.debug_tree(), new_cst.debug_tree());
                prop_assert_eq!(reread.render(), new.clone());
                prop_assert_eq!(skeleton(&reread), with_value(&skel, path, &lexeme_bytes));
                prop_assert!(lint_syntax(&reread).is_empty());
            }
            Err(Error::QuotedValueNeedsAdjacentTerminator { trivia_len, .. }) => {
                prop_assert!(lexeme_bytes.first() == Some(&b'"'));
                prop_assert!(trivia_len > 0);
            }
            Err(other) => prop_assert!(false, "unexpected refusal {:?} of {:?} at {:?} in {:?}", other, String::from_utf8_lossy(&lexeme_bytes), path, String::from_utf8_lossy(&old)),
        }
    }
}
