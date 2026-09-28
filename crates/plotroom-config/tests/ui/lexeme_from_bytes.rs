// SPDX-License-Identifier: GPL-3.0-or-later
// Rule: raw bytes do not convert into a lexeme; there is no From<Vec<u8>> or From<&[u8]>.
// Why: a conversion would be an unchecked constructor, bypassing the witness check.
use plotroom_config::EntryValueLexeme;

fn main() {
    let _lexeme: EntryValueLexeme = b"1; injected = 2".to_vec().into();
}
