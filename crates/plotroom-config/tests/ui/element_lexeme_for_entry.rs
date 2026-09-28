// SPDX-License-Identifier: GPL-3.0-or-later
// Rule: an element lexeme cannot replace an entry value (and vice versa).
// Why: the contexts differ (`,` and `}` end an element but not an entry value); the types keep the proofs apart.
use plotroom_config::{ElementValueLexeme, parse};

fn main() {
    let cst = parse(b"x = 1;").unwrap();
    let target = cst.entry_value(&[b"x"]).unwrap();
    let _patched = cst.replace_entry_value(target, ElementValueLexeme::int(2));
}
