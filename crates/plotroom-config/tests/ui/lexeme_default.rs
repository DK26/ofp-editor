// SPDX-License-Identifier: GPL-3.0-or-later
// Rule: a lexeme has no Default value.
// Why: an "empty" lexeme would be a witness nobody checked; every lexeme comes from a checked constructor.
use plotroom_config::ElementValueLexeme;

fn main() {
    let _lexeme = ElementValueLexeme::default();
}
