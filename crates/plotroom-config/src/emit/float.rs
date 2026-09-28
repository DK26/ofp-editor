// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: Bohemia Interactive a.s. (original C++)
// SPDX-FileCopyrightText: 2026 Plotroom contributors (Rust translation)
// Derived-From: BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/IO/ParamFile/ParamFileParse.cpp
// Modified: translated to Rust and changed, 2026-09-28. Subject to the Additional Terms
// (GPLv3 section 7) from Bohemia Interactive reproduced in NOTICE.
//! Float spelling for the two writer profiles: C's `%f`, and CWR's `%f` with a `%.9g` fallback.
//!
//! **What it owns.** [`format_float`]. The engine writes a float with `snprintf("%f")`; CWR checks whether that text
//! reads back to the same 32-bit float and, if not, writes `%.9g` instead, adding `.0` when the result would read
//! back as an integer (`ParamFileParse.cpp#L371-L388`; its comment says this deliberately changes the older plain
//! `%f`). `Legacy196Text` therefore writes `%f` only.
//!
//! **How `%f` and `%.9g` are reproduced.** Both format `(double)value`, as C's varargs promotion does. Rust's
//! `{:.6}` and `{:.8e}` print the exact decimal expansion rounded half to even, like glibc; the old Microsoft C
//! runtime's rounding of exact ties is unverified ([U], tagged `unverified-1.99` in the writer tests). `%.9g` picks
//! fixed or exponent style from the exponent after rounding to 9 significant digits, strips trailing zeros, and writes
//! the exponent with a sign and at least two digits, as C does.
//!
//! **Allocation profile.** One `String` per call.

use crate::emit::WriterProfile;
use crate::error::Error;

/// Spells `value` as the given profile writes it.
///
/// # Errors
///
/// [`Error::NonFiniteFloat`] for NaN and infinities: the text format has no spelling the game reads back as them.
pub fn format_float(value: f32, profile: WriterProfile) -> Result<String, Error> {
    if !value.is_finite() {
        return Err(Error::NonFiniteFloat {
            bits: value.to_bits(),
        });
    }
    let fixed = c_percent_f(value);
    match profile {
        WriterProfile::Legacy196Text => Ok(fixed),
        WriterProfile::RemasteredText => {
            // Float narrowing that mirrors the engine: `(float)atof(buffer) != _value` (`ParamFileParse.cpp#L378`)
            // reads the %f text back as a double, narrows it and compares as floats.
            let reads_back = fixed.parse::<f64>().is_ok_and(|back| back as f32 == value);
            if reads_back {
                return Ok(fixed);
            }
            let mut general = c_percent_g9(value);
            if !general
                .bytes()
                .any(|byte| matches!(byte, b'.' | b'e' | b'E' | b'n' | b'N'))
            {
                general.push_str(".0");
            }
            Ok(general)
        }
    }
}

/// C `printf("%f", (double)value)`.
fn c_percent_f(value: f32) -> String {
    format!("{:.6}", f64::from(value))
}

/// C `printf("%.9g", (double)value)`.
fn c_percent_g9(value: f32) -> String {
    const PRECISION: i32 = 9;
    let wide = f64::from(value);
    if wide == 0.0 {
        return if wide.is_sign_negative() {
            "-0".to_owned()
        } else {
            "0".to_owned()
        };
    }
    // The exponent after rounding to 9 significant digits decides the style.
    let scientific = format!("{:.8e}", wide);
    let (mantissa, exponent) = scientific
        .split_once('e')
        .unwrap_or((scientific.as_str(), "0"));
    let exponent: i32 = exponent.parse().unwrap_or(0);
    if !(-4..PRECISION).contains(&exponent) {
        let mantissa = strip_fraction_zeros(mantissa);
        let sign = if exponent < 0 { '-' } else { '+' };
        return format!("{mantissa}e{sign}{:02}", exponent.unsigned_abs());
    }
    // Fixed style with PRECISION - 1 - exponent digits after the point, then trailing zeros removed.
    let decimals =
        usize::try_from(PRECISION.saturating_sub(1).saturating_sub(exponent)).unwrap_or(0);
    strip_fraction_zeros(&format!("{wide:.decimals$}")).to_owned()
}

/// Removes trailing zeros after a decimal point, and the point itself if nothing is left after it.
fn strip_fraction_zeros(text: &str) -> &str {
    if !text.contains('.') {
        return text;
    }
    text.trim_end_matches('0').trim_end_matches('.')
}

#[cfg(test)]
mod tests {
    use super::*;

    // ── Known-value cross-validation ─────────────────────────────────────────────────────────────────────────────

    /// `%.9g` goldens computed with Python's C-semantics `'%.9g' % x`, x = the f32 value widened to double via `struct` (see each value).
    ///
    /// Why: the fallback spelling must match C's exactly, or a re-saved file changes bytes the game would not.
    #[test]
    fn percent_g9_matches_c() {
        // CWR's own example in the source comment: 3.16228e-05f32 prints as 3.16227997e-05.
        assert_eq!(c_percent_g9(3.162_28e-5), "3.16227997e-05");
        assert_eq!(c_percent_g9(0.1), "0.100000001");
        assert_eq!(c_percent_g9(123_456_790.0), "123456792");
        assert_eq!(c_percent_g9(1.0e9), "1e+09");
        assert_eq!(c_percent_g9(0.0001), "9.99999975e-05");
        assert_eq!(c_percent_g9(-0.0), "-0");
        assert_eq!(c_percent_g9(1.5), "1.5");
    }
}
