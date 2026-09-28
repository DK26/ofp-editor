// SPDX-License-Identifier: GPL-3.0-or-later
// Rule: an EntryValueLexeme can only be built by its checked constructors (quoted, int, float, bare).
// Why: the lexeme is a witness that its bytes read back as exactly one value; building it directly would skip that
// proof and let a patch open a comment or end a statement.
use plotroom_config::EntryValueLexeme;

fn main() {
    let _lexeme = EntryValueLexeme(Default::default());
}
