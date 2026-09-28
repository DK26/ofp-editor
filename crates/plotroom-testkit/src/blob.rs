// SPDX-License-Identifier: GPL-3.0-or-later
//! [`BlobBuilder`]: little-endian byte blobs for synthetic binary fixtures.
//!
//! **Why.** Format tests (PBO, raP, WRP, PAA, FXY; crate-map §4) need small binary inputs, including malformed ones,
//! and the repository may not hold game files (`AGENTS.md`, "Test Fixture Legality"). Doc 20 §3 ("shared
//! prerequisites", item 1) asks for a little-endian blob builder so each test states its bytes in code.
//!
//! **How.** A consuming builder over one `Vec<u8>`: each method appends and returns the builder, so a fixture reads
//! top to bottom like the format's layout. [`BlobBuilder::patch_u32_le`] back-fills a size or offset once it is
//! known. The builder never validates what it writes: adversarial tests build malformed input on purpose.

use crate::Error;

/// Builds a byte blob field by field, little-endian, for synthetic test fixtures.
///
/// Appending never fails. Only [`BlobBuilder::patch_u32_le`], which overwrites existing bytes, can return an error.
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct BlobBuilder {
    bytes: Vec<u8>,
}

impl BlobBuilder {
    /// An empty blob.
    pub fn new() -> Self {
        Self::default()
    }

    /// An empty blob with room for `capacity` bytes (`AGENTS.md` heap policy rule 4).
    pub fn with_capacity(capacity: usize) -> Self {
        Self {
            bytes: Vec::with_capacity(capacity),
        }
    }

    /// Appends one byte.
    pub fn u8(self, value: u8) -> Self {
        self.bytes(&[value])
    }

    /// Appends a `u16`, little-endian.
    pub fn u16_le(self, value: u16) -> Self {
        self.bytes(&value.to_le_bytes())
    }

    /// Appends a `u32`, little-endian.
    pub fn u32_le(self, value: u32) -> Self {
        self.bytes(&value.to_le_bytes())
    }

    /// Appends an `i32`, little-endian two's complement.
    pub fn i32_le(self, value: i32) -> Self {
        self.bytes(&value.to_le_bytes())
    }

    /// Appends an `f32` as its IEEE-754 bits, little-endian.
    pub fn f32_le(self, value: f32) -> Self {
        self.bytes(&value.to_le_bytes())
    }

    /// Appends raw bytes as they are.
    pub fn bytes(mut self, raw: &[u8]) -> Self {
        // One memcpy per field (`AGENTS.md` heap policy rule 5).
        self.bytes.extend_from_slice(raw);
        self
    }

    /// Appends `text` and a terminating zero byte (the engine's zero-terminated strings, for example PBO entry names).
    ///
    /// Takes bytes, not `&str`, so a fixture can hold legacy code-page names; an interior zero is written as given.
    pub fn asciiz(self, text: &[u8]) -> Self {
        self.bytes(text).u8(0)
    }

    /// Appends `count` copies of `byte` (padding, reserved fields, oversize inputs).
    pub fn fill(mut self, byte: u8, count: usize) -> Self {
        // `resize` is a memset, not `count` pushes (`AGENTS.md` heap policy rule 5). Saturating: a test asking for
        // more than `usize::MAX` bytes fails on allocation, which is the honest outcome, never on a wrapped length.
        let new_len = self.bytes.len().saturating_add(count);
        self.bytes.resize(new_len, byte);
        self
    }

    /// Overwrites four existing bytes at `at` with `value`, little-endian (a size or offset known only later).
    ///
    /// # Errors
    ///
    /// [`Error::PatchOutOfBounds`] when `at + 4` passes the end of the blob, including when `at + 4` overflows.
    pub fn patch_u32_le(&mut self, at: usize, value: u32) -> Result<(), Error> {
        const WIDTH: usize = 4;
        let len = self.bytes.len();
        let out_of_bounds = Error::PatchOutOfBounds {
            at,
            width: WIDTH,
            len,
        };
        // `checked_add` first: an offset near `usize::MAX` must fail, never wrap to a small index.
        let end = at.checked_add(WIDTH).ok_or(out_of_bounds.clone())?;
        let slot = self.bytes.get_mut(at..end).ok_or(out_of_bounds)?;
        // `zip` over the four bytes instead of `copy_from_slice`, which would panic on a length mismatch.
        for (dst, src) in slot.iter_mut().zip(value.to_le_bytes()) {
            *dst = src;
        }
        Ok(())
    }

    /// Number of bytes written so far; use it to record an offset before appending the field it points at.
    pub fn len(&self) -> usize {
        self.bytes.len()
    }

    /// Whether nothing has been written yet.
    pub fn is_empty(&self) -> bool {
        self.bytes.is_empty()
    }

    /// The bytes written so far.
    pub fn as_bytes(&self) -> &[u8] {
        &self.bytes
    }

    /// Finishes the blob.
    pub fn into_bytes(self) -> Vec<u8> {
        self.bytes
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // ── Basic functionality ─────────────────────────────────────────────────────────────────────────────────────

    /// Every appender writes its value little-endian, in call order.
    ///
    /// Format tests rely on the exact layout; a byte-order slip here would make every synthetic fixture wrong in
    /// the same way as the parser under test, hiding the bug.
    #[test]
    fn appenders_write_little_endian_in_call_order() {
        let blob = BlobBuilder::new()
            .u8(0xAB)
            .u16_le(0x1234)
            .u32_le(0xDEAD_BEEF)
            .i32_le(-2)
            .f32_le(1.0)
            .bytes(&[9, 8])
            .into_bytes();
        assert_eq!(
            blob,
            [
                0xAB, 0x34, 0x12, 0xEF, 0xBE, 0xAD, 0xDE, 0xFE, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x80,
                0x3F, 9, 8
            ]
        );
    }

    /// `asciiz` appends the text and one zero byte; `fill` repeats a byte.
    ///
    /// Zero-terminated names and padding are the most common fields in the engine's binary formats.
    #[test]
    fn asciiz_terminates_and_fill_repeats() {
        let blob = BlobBuilder::new()
            .asciiz(b"ab")
            .fill(0xFF, 3)
            .asciiz(b"")
            .into_bytes();
        assert_eq!(blob, [b'a', b'b', 0, 0xFF, 0xFF, 0xFF, 0]);
    }

    /// `len` tracks the bytes written, so a test can record an offset before writing the field it points at.
    #[test]
    fn len_tracks_written_bytes() {
        let builder = BlobBuilder::with_capacity(16).u32_le(1).u8(2);
        assert_eq!(builder.len(), 5);
        assert!(!builder.is_empty());
        assert!(BlobBuilder::new().is_empty());
        assert_eq!(builder.as_bytes(), [1, 0, 0, 0, 2]);
    }

    /// A placeholder patched later holds the new value and leaves every other byte alone.
    ///
    /// Headers that store a total size or a table offset are written with a placeholder and back-filled.
    #[test]
    fn patch_overwrites_only_its_four_bytes() {
        let mut builder = BlobBuilder::new().u8(7).u32_le(0).u8(9);
        builder.patch_u32_le(1, 0x0102_0304).unwrap();
        assert_eq!(builder.into_bytes(), [7, 4, 3, 2, 1, 9]);
    }

    // ── Error field & Display verification ──────────────────────────────────────────────────────────────────────

    /// A patch past the end reports the offset, the width and the blob length.
    #[test]
    fn patch_past_end_reports_structured_fields() {
        let mut builder = BlobBuilder::new().u32_le(0).u8(0);
        let err = builder.patch_u32_le(2, 1).unwrap_err();
        assert_eq!(
            err,
            Error::PatchOutOfBounds {
                at: 2,
                width: 4,
                len: 5
            }
        );
        // The failed patch changed nothing.
        assert_eq!(builder.as_bytes(), [0, 0, 0, 0, 0]);
    }

    /// The message carries the numbers and the next action.
    #[test]
    fn patch_error_display_names_numbers_and_fix() {
        let fits_nowhere = Error::PatchOutOfBounds {
            at: 0,
            width: 4,
            len: 2,
        }
        .to_string();
        assert!(
            fits_nowhere.contains("4 bytes at offset 0"),
            "{fits_nowhere}"
        );
        assert!(fits_nowhere.contains("blob of 2 bytes"), "{fits_nowhere}");
        assert!(fits_nowhere.contains("placeholder"), "{fits_nowhere}");
        let too_far = Error::PatchOutOfBounds {
            at: 9,
            width: 4,
            len: 10,
        }
        .to_string();
        assert!(too_far.contains("at most 6"), "{too_far}");
    }

    // ── Determinism ─────────────────────────────────────────────────────────────────────────────────────────────

    /// The same calls give the same bytes.
    #[test]
    fn same_calls_same_bytes() {
        let build = || {
            BlobBuilder::new()
                .asciiz(b"x")
                .f32_le(-0.5)
                .fill(1, 2)
                .into_bytes()
        };
        assert_eq!(build(), build());
    }

    // ── Boundary tests ──────────────────────────────────────────────────────────────────────────────────────────

    /// A patch ending exactly at the end succeeds; one byte further fails.
    #[test]
    fn patch_boundary_at_end() {
        let mut builder = BlobBuilder::new().fill(0, 8);
        assert!(builder.patch_u32_le(4, u32::MAX).is_ok());
        assert_eq!(
            builder.patch_u32_le(5, 1),
            Err(Error::PatchOutOfBounds {
                at: 5,
                width: 4,
                len: 8
            })
        );
    }

    /// Patching an empty blob fails instead of growing it.
    #[test]
    fn patch_on_empty_blob_fails() {
        let mut builder = BlobBuilder::new();
        assert_eq!(
            builder.patch_u32_le(0, 1),
            Err(Error::PatchOutOfBounds {
                at: 0,
                width: 4,
                len: 0
            })
        );
        assert!(builder.is_empty());
    }

    // ── Integer overflow safety ─────────────────────────────────────────────────────────────────────────────────

    /// An offset near `usize::MAX` whose end overflows returns an error, never a panic or a wrapped write.
    #[test]
    fn patch_offset_overflow_is_an_error() {
        let mut builder = BlobBuilder::new().fill(0, 4);
        for at in [usize::MAX, usize::MAX - 3, usize::MAX - 2] {
            assert_eq!(
                builder.patch_u32_le(at, 1),
                Err(Error::PatchOutOfBounds {
                    at,
                    width: 4,
                    len: 4
                })
            );
        }
        assert_eq!(builder.as_bytes(), [0, 0, 0, 0]);
    }
}
