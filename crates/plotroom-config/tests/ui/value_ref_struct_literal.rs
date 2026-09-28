// SPDX-License-Identifier: GPL-3.0-or-later
// Rule: a value reference is only made by ConfigCst::entry_value or ConfigCst::element_value.
// Why: the reference names a node path in one tree revision; a hand-made one could point anywhere.
use plotroom_config::{EntryValueRef, TextOffset, TextSpan, parse};

fn main() {
    let cst = parse(b"x = 1;").unwrap();
    let span = TextSpan::empty_at(TextOffset::from_raw(0));
    let _target = EntryValueRef { root: cst.green(), path: vec![0, 0], span };
}
