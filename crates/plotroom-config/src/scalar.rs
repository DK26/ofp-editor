// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: Bohemia Interactive a.s. (original C++)
// SPDX-FileCopyrightText: 2026 Plotroom contributors (Rust translation)
// Derived-From: BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/IO/ParamFile/ParamFile.cpp
// Derived-From: BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/IO/ParamFile/ParamFileParse.cpp
// Modified: translated to Rust and changed, 2026-09-28. Subject to the Additional Terms
// (GPLv3 section 7) from Bohemia Interactive reproduced in NOTICE.
//! How the game types an unquoted value: [`classify_unquoted`] and the writer's "is it a number" test.
//!
//! **What it owns.** The lexical scalar class of a bare value or array element, reproducing the engine's order
//! (`ParamFile.cpp#L679-L789`, used at `#L1818-L1843` and `ParamFileParse.cpp#L481-L499`): try an integer
//! (`strtol` base 10 over the whole word, then `0x` hexadecimal), then a float (`strtod` over the whole word, then the
//! `db` decibel form), else the word stays a string. Quoted values are always strings.
//!
//! **Why it matters here.** The tree keeps raw lexemes; the class is what the game will make of them. The writer
//! needs the same `strtod` test to decide whether an array is written inline (`IsNumerical`,
//! `ParamFileParse.cpp#L333-L342`), and lints and the typed lens need to know that `1.5e2` is the float 150 while
//! `12.34.56` is text.
//!
//! **Platform choices (profile-dependent, [U] for 1.99).** `strtol` saturates at the 32-bit `long` range, as on
//! Windows, where the game runs (64-bit Linux builds truncate instead). `strtod` is read in its decimal form only: the
//! C99 extras (`inf`, `nan`, hexadecimal floats) depend on the C runtime, and the old Windows runtime did not accept
//! them, so they classify as text here.
//!
//! **Allocation profile.** None.

/// What the game makes of an unquoted word.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Scalar {
    /// An integer (decimal, or `0x` hexadecimal with any trailing junk ignored).
    Int(i32),
    /// A float (decimal, or the `db` form, which the engine converts from decibels: `db+10` is about 3.1623).
    Float(f32),
    /// Anything else stays a string.
    Text,
}

/// C `isspace` in the "C" locale.
#[inline]
fn is_c_space(byte: u8) -> bool {
    matches!(byte, b' ' | b'\t' | b'\n' | 0x0B | 0x0C | b'\r')
}

/// Classifies an unquoted word the way the engine does (see the module docs). An empty word is text.
#[must_use]
pub fn classify_unquoted(word: &[u8]) -> Scalar {
    if word.is_empty() {
        return Scalar::Text;
    }
    if let Some(value) = scan_int_plain(word).or_else(|| scan_hex(word)) {
        return Scalar::Int(value);
    }
    if let Some(value) = strtod_whole(word) {
        // Float narrowing that mirrors the engine: `float db = strtod(ptr, &end);` in `ScanFloatPlain`
        // (`ParamFile.cpp#L738`) stores the double in a float.
        return Scalar::Float(value as f32);
    }
    if let Some(value) = scan_db(word) {
        return Scalar::Float(value);
    }
    Scalar::Text
}

/// The writer's `IsNumerical` (`ParamFileParse.cpp#L333-L342`): non-empty and fully read by `strtod`.
#[must_use]
pub(crate) fn is_numerical(text: &[u8]) -> bool {
    !text.is_empty() && strtod_whole(text).is_some()
}

/// `ScanIntPlain` (`ParamFile.cpp#L743-L749`): `strtol(word, &end, 10)` must read the whole word.
fn scan_int_plain(word: &[u8]) -> Option<i32> {
    let rest = skip_c_space(word);
    let (negative, digits) = match rest.split_first() {
        Some((b'-', tail)) => (true, tail),
        Some((b'+', tail)) => (false, tail),
        _ => (false, rest),
    };
    if digits.is_empty() || !digits.iter().all(u8::is_ascii_digit) {
        return None;
    }
    // Intended clamp matching the engine: `strtol` saturates at LONG_MAX / LONG_MIN (a 32-bit `long` on Windows,
    // `ParamFile.cpp#L746`), and the `(int)` cast at `#L748` keeps that value.
    let magnitude = digits.iter().fold(0i64, |acc, digit| {
        acc.saturating_mul(10)
            .saturating_add(i64::from(digit.saturating_sub(b'0')))
    });
    let signed = if negative {
        magnitude.saturating_neg()
    } else {
        magnitude
    };
    Some(i32::try_from(signed).unwrap_or(if negative { i32::MIN } else { i32::MAX }))
}

/// `ScanHex` (`ParamFile.cpp#L679-L716`): `0x`/`0X` and at least one hex digit; digits are read until the first
/// non-digit (trailing junk is ignored) and the value wraps like the engine's unsigned accumulator.
fn scan_hex(word: &[u8]) -> Option<i32> {
    let (prefix, digits) = word.split_at_checked(2)?;
    if !prefix.eq_ignore_ascii_case(b"0x") || !digits.first().is_some_and(u8::is_ascii_hexdigit) {
        return None;
    }
    let value = digits
        .iter()
        .take_while(|byte| byte.is_ascii_hexdigit())
        .fold(0u32, |acc, byte| {
            let digit = match byte {
                b'0'..=b'9' => byte.wrapping_sub(b'0'),
                b'a'..=b'f' => byte.wrapping_sub(b'a').wrapping_add(10),
                _ => byte.wrapping_sub(b'A').wrapping_add(10),
            };
            // Wrap-around the engine defines: its `unsigned iValue` accumulator (`ParamFile.cpp#L693-L709`).
            acc.wrapping_mul(16).wrapping_add(u32::from(digit))
        });
    Some(i32::from_ne_bytes(value.to_ne_bytes()))
}

/// `ScanDb` (`ParamFile.cpp#L718-L733`): a word starting with lowercase `db` is a float whatever follows; the rest
/// is read by `strtod` as far as it goes (0 if nothing), and the value is `10^(db / 20)`.
fn scan_db(word: &[u8]) -> Option<f32> {
    let rest = word.strip_prefix(b"db")?;
    // Float narrowing that mirrors the engine: `float db = strtod(ptr + 2, &end);` (`ParamFile.cpp#L727`).
    let db = strtod_prefix(rest).map_or(0.0, |(value, _)| value) as f32;
    // `return pow(10, db * (1.0f / 20));` (`ParamFile.cpp#L732`): a float product, a double power, a float result.
    // `powf` is not bit-exact across platforms (AGENTS.md "Determinism"); this engine-faithful value is used only
    // for the lexical type and display, never in a seeded or hashed path.
    let exponent = db * (1.0f32 / 20.0);
    let value = 10f64.powf(f64::from(exponent)) as f32;
    Some(value)
}

/// Skips leading C whitespace.
fn skip_c_space(bytes: &[u8]) -> &[u8] {
    let skip = bytes.iter().take_while(|byte| is_c_space(**byte)).count();
    bytes.get(skip..).unwrap_or(&[])
}

/// `strtod` over the whole input: the value if every byte was read.
fn strtod_whole(bytes: &[u8]) -> Option<f64> {
    let (value, used) = strtod_prefix(bytes)?;
    (used == bytes.len()).then_some(value)
}

/// `strtod` in its decimal form: optional whitespace, sign, digits with an optional `.`, and an optional exponent
/// (which is left unread if it has no digits). Returns the value and how many bytes were read, or `None` if no
/// number starts here.
fn strtod_prefix(bytes: &[u8]) -> Option<(f64, usize)> {
    let lead = bytes.iter().take_while(|byte| is_c_space(**byte)).count();
    let mut i = lead;
    if matches!(bytes.get(i), Some(b'+' | b'-')) {
        i = i.saturating_add(1);
    }
    let int_digits = count_digits(bytes, i);
    i = i.saturating_add(int_digits);
    let mut frac_digits = 0;
    if bytes.get(i) == Some(&b'.') {
        frac_digits = count_digits(bytes, i.saturating_add(1));
        if int_digits > 0 || frac_digits > 0 {
            i = i.saturating_add(1).saturating_add(frac_digits);
        }
    }
    if int_digits == 0 && frac_digits == 0 {
        return None;
    }
    if matches!(bytes.get(i), Some(b'e' | b'E')) {
        let mut j = i.saturating_add(1);
        if matches!(bytes.get(j), Some(b'+' | b'-')) {
            j = j.saturating_add(1);
        }
        let exp_digits = count_digits(bytes, j);
        if exp_digits > 0 {
            i = j.saturating_add(exp_digits);
        }
    }
    let text = std::str::from_utf8(bytes.get(lead..i)?).ok()?;
    // Rust's parser rounds correctly, like the C runtime; a leading '+' and a bare trailing '.' are both accepted.
    let value: f64 = text.parse().ok()?;
    Some((value, i))
}

/// The number of ASCII digits starting at `from`.
fn count_digits(bytes: &[u8], from: usize) -> usize {
    bytes
        .get(from..)
        .unwrap_or(&[])
        .iter()
        .take_while(|byte| byte.is_ascii_digit())
        .count()
}

#[cfg(test)]
mod tests {
    use super::*;

    // ── Known-value cross-validation ─────────────────────────────────────────────────────────────────────────────

    /// Integers, hexadecimal, floats, the `db` form and text classify as the engine types them.
    ///
    /// Why: these are the goldens from the engine source (`ParamFile.cpp#L679-L789`) that the ported parsing tests
    /// rely on (`1.5e2` is a float, `12.34.56` is text, `0x1F` is 31, `db+10` is 10^(10/20)).
    #[test]
    fn engine_typing_goldens() {
        assert_eq!(classify_unquoted(b"123"), Scalar::Int(123));
        assert_eq!(classify_unquoted(b"-42"), Scalar::Int(-42));
        assert_eq!(classify_unquoted(b"+7"), Scalar::Int(7));
        assert_eq!(classify_unquoted(b"0x1F"), Scalar::Int(31));
        assert_eq!(classify_unquoted(b"0x1Fzz"), Scalar::Int(31));
        assert_eq!(classify_unquoted(b"2.75"), Scalar::Float(2.75));
        assert_eq!(classify_unquoted(b"1.5e2"), Scalar::Float(150.0));
        assert_eq!(classify_unquoted(b"5."), Scalar::Float(5.0));
        assert_eq!(classify_unquoted(b".5"), Scalar::Float(0.5));
        assert_eq!(classify_unquoted(b"12.34.56"), Scalar::Text);
        assert_eq!(classify_unquoted(b"db+0"), Scalar::Float(1.0));
        let Scalar::Float(db10) = classify_unquoted(b"db+10") else {
            panic!("db+10 is a float")
        };
        assert!((db10 - 3.162_277_7).abs() < 1e-5);
        // Any word starting with lowercase `db` is a float (the engine sets ok before reading the number).
        assert_eq!(classify_unquoted(b"dbfoo"), Scalar::Float(1.0));
        assert_eq!(classify_unquoted(b"DB+0"), Scalar::Text);
        assert_eq!(classify_unquoted(b"true"), Scalar::Text);
        assert_eq!(classify_unquoted(b"2 + 2"), Scalar::Text);
        assert_eq!(classify_unquoted(b"1e"), Scalar::Text);
        assert_eq!(classify_unquoted(b"inf"), Scalar::Text);
        assert_eq!(classify_unquoted(b""), Scalar::Text);
    }

    /// The writer's numeric test accepts leading whitespace and rejects empty or partly numeric text.
    ///
    /// Why: it decides whether an array is written inline (`markers[]={"1"};`) or one element per line.
    #[test]
    fn is_numerical_follows_strtod() {
        assert!(is_numerical(b"1"));
        assert!(is_numerical(b" 2.5"));
        assert!(is_numerical(b"-1e3"));
        assert!(!is_numerical(b""));
        assert!(!is_numerical(b"1 "));
        assert!(!is_numerical(b"abc"));
        assert!(!is_numerical(b"0x10"));
    }

    // ── Integer overflow safety ──────────────────────────────────────────────────────────────────────────────────

    /// Decimal overflow saturates at the 32-bit range; hexadecimal overflow wraps.
    ///
    /// Why: both come from untrusted text; neither may panic, and each must match the engine on Windows.
    #[test]
    fn overflow_saturates_decimal_and_wraps_hex() {
        assert_eq!(classify_unquoted(b"2147483647"), Scalar::Int(i32::MAX));
        assert_eq!(classify_unquoted(b"2147483648"), Scalar::Int(i32::MAX));
        assert_eq!(classify_unquoted(b"-2147483649"), Scalar::Int(i32::MIN));
        assert_eq!(
            classify_unquoted(b"99999999999999999999999999"),
            Scalar::Int(i32::MAX)
        );
        assert_eq!(classify_unquoted(b"0xFFFFFFFF"), Scalar::Int(-1));
        assert_eq!(classify_unquoted(b"0x1FFFFFFFF"), Scalar::Int(-1));
        assert_eq!(classify_unquoted(b"1e999"), Scalar::Float(f32::INFINITY));
    }
}
