// SPDX-License-Identifier: GPL-3.0-or-later
// Rule: the result of ByteEdit::check_outside_unchanged must be used.
// Why: the check is the proof that no byte outside the patch changed; ignoring its error defeats it.
#![deny(unused_must_use)]
use plotroom_config::{EntryValueLexeme, parse};

fn main() {
    let cst = parse(b"x = 1;").unwrap();
    let target = cst.entry_value(&[b"x"]).unwrap();
    let (new_cst, edit) = cst.replace_entry_value(target, EntryValueLexeme::int(2)).unwrap().into_parts();
    edit.check_outside_unchanged(b"x = 1;", &new_cst.render());
}
