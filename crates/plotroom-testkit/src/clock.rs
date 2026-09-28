// SPDX-License-Identifier: GPL-3.0-or-later
//! [`VirtualClock`]: test time that moves only when the test moves it.
//!
//! **Why.** Determinism is injected (testing-strategy §1 item 2; doc 45 §2.10): code that needs the time takes a
//! clock, and tests pass one they control, so timeouts, staleness chips and journal timestamps are tested without
//! sleeping and give the same result on every run and every CI machine.
//!
//! **Placeholder.** The production `Clock` trait belongs to `plotroom-ids` (M1). Until it exists this type offers
//! the same reading as an inherent method, [`VirtualClock::now_ms`]; the trait impl is added when that crate lands.
//! Milliseconds since an arbitrary test epoch are the unit because journals and ledgers store integers, never floats.

use std::time::Duration;

/// A clock whose time is set and advanced only by the test.
///
/// Advancing saturates at `u64::MAX` milliseconds instead of wrapping, so a test that pushes time "to the end"
/// cannot make it run backwards.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct VirtualClock {
    now_ms: u64,
}

impl VirtualClock {
    /// A clock reading `start_ms` milliseconds after the test epoch.
    pub const fn starting_at_ms(start_ms: u64) -> Self {
        Self { now_ms: start_ms }
    }

    /// The current reading, in milliseconds after the test epoch.
    pub const fn now_ms(&self) -> u64 {
        self.now_ms
    }

    /// Moves time forward by `delta_ms` milliseconds (saturating) and returns the new reading.
    pub fn advance_ms(&mut self, delta_ms: u64) -> u64 {
        self.now_ms = self.now_ms.saturating_add(delta_ms);
        self.now_ms
    }

    /// Moves time forward by `delta` (whole milliseconds, saturating) and returns the new reading.
    ///
    /// Sub-millisecond parts are dropped, the same truncation `Duration::as_millis` applies.
    pub fn advance(&mut self, delta: Duration) -> u64 {
        // `as_millis` is a u128; anything past u64::MAX milliseconds saturates like the addition does.
        let delta_ms = u64::try_from(delta.as_millis()).unwrap_or(u64::MAX);
        self.advance_ms(delta_ms)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // ── Basic functionality ─────────────────────────────────────────────────────────────────────────────────────

    /// A clock starts where the test says and moves only by the amounts the test gives.
    #[test]
    fn starts_where_told_and_moves_only_when_told() {
        let mut clock = VirtualClock::starting_at_ms(500);
        assert_eq!(clock.now_ms(), 500);
        assert_eq!(clock.now_ms(), 500, "reading the clock must not move it");
        assert_eq!(clock.advance_ms(20), 520);
        assert_eq!(clock.advance(Duration::from_millis(1_480)), 2_000);
        assert_eq!(clock.now_ms(), 2_000);
        assert_eq!(VirtualClock::default().now_ms(), 0);
    }

    // ── Determinism ─────────────────────────────────────────────────────────────────────────────────────────────

    /// The same advances from the same start give the same reading.
    #[test]
    fn same_steps_same_reading() {
        let run = || {
            let mut clock = VirtualClock::starting_at_ms(7);
            for step in [1, 10, 100] {
                clock.advance_ms(step);
            }
            clock.now_ms()
        };
        assert_eq!(run(), 118);
        assert_eq!(run(), run());
    }

    // ── Boundary tests ──────────────────────────────────────────────────────────────────────────────────────────

    /// Sub-millisecond parts of a `Duration` are dropped; a zero advance changes nothing.
    #[test]
    fn sub_millisecond_parts_truncate() {
        let mut clock = VirtualClock::starting_at_ms(10);
        assert_eq!(clock.advance(Duration::from_micros(999)), 10);
        assert_eq!(clock.advance(Duration::from_micros(1_999)), 11);
        assert_eq!(clock.advance_ms(0), 11);
    }

    // ── Integer overflow safety ─────────────────────────────────────────────────────────────────────────────────

    /// Advancing past `u64::MAX` milliseconds saturates instead of wrapping to an earlier time.
    ///
    /// A wrapped clock would make "later" events sort before earlier ones and break staleness checks.
    #[test]
    fn advance_saturates_at_max() {
        let mut clock = VirtualClock::starting_at_ms(u64::MAX - 5);
        assert_eq!(clock.advance_ms(10), u64::MAX);
        assert_eq!(clock.advance_ms(u64::MAX), u64::MAX);
        let mut other = VirtualClock::starting_at_ms(1);
        // Duration::MAX is about 1.8e22 ms, far past u64::MAX ms: the conversion must saturate too.
        assert_eq!(other.advance(Duration::MAX), u64::MAX);
    }
}
