// SPDX-License-Identifier: GPL-3.0-or-later
// Rule: a value reference cannot outlive the tree it was taken from.
// Why: after the tree is gone (or replaced by a patch), the reference would describe bytes that no longer exist.
use plotroom_config::{EntryValueRef, parse};

fn main() {
    let target: EntryValueRef<'_> = {
        let cst = parse(b"x = 1;").unwrap();
        cst.entry_value(&[b"x"]).unwrap()
    };
    let _ = target.span();
}
