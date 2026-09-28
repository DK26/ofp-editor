// SPDX-License-Identifier: GPL-3.0-or-later
// Rule: a TextSpan is built only by TextSpan::new, TextSpan::at or TextSpan::empty_at.
// Why: those keep start <= end; a reversed span built from fields would underflow widths and mis-slice text.
use plotroom_config::{TextOffset, TextSpan};

fn main() {
    let _span = TextSpan { start: TextOffset::from_raw(5), end: TextOffset::from_raw(1) };
}
