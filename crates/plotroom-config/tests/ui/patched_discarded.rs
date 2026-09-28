// SPDX-License-Identifier: GPL-3.0-or-later
// Rule: a patch result must be used.
// Why: a patch builds a new tree and leaves the old one unchanged; dropping the result silently loses the edit.
#![deny(unused_must_use)]
use plotroom_config::{EntryValueLexeme, parse};

fn main() {
    let cst = parse(b"x = 1;").unwrap();
    let target = cst.entry_value(&[b"x"]).unwrap();
    cst.replace_entry_value(target, EntryValueLexeme::int(2)).unwrap();
}
