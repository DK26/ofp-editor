// SPDX-License-Identifier: GPL-3.0-or-later
//! [`SeededIds`]: a deterministic source of 128-bit ids for tests.
//!
//! **Why.** Plotroom's identity types (`EntityId`, `ElementId`, `LineId`; core-document-model §7.1) are `u128` values
//! from an injected `IdSource`. Production minting is time-ordered plus random (doc 45 §2.3; its exact scheme is doc
//! 45 open question 4), which a test cannot predict. Tests inject this source instead ("tests: seeded counter"), so
//! golden files, journals and snapshots that contain ids are byte-identical on every run.
//!
//! **How.** SplitMix64 (Steele, Lea and Flood, OOPSLA 2014; public-domain reference code by S. Vigna):
//! - the **low 64 bits** of each id are the next output of a SplitMix64 stream seeded with the seed. The stream
//!   adds an odd constant to its state and passes it through a bijective finaliser, so one source never repeats a
//!   low half within 2^64 draws;
//! - the **high 64 bits** are the finaliser applied to `seed ^ SEED_DOMAIN`, the same for every id of one source.
//!   The finaliser is a bijection, so sources with different seeds never share a high half, and ids from two
//!   differently seeded sources never collide.
//!
//! **Placeholder.** The `IdSource` trait belongs to `plotroom-ids` (M1); [`SeededIds::mint`] has the trait's
//! signature (doc 45 §2.3: `fn mint(&mut self) -> u128`) and gains the trait impl when that crate lands.

/// SplitMix64's increment: 2^64 divided by the golden ratio, rounded to odd (from the reference implementation).
const GOLDEN_GAMMA: u64 = 0x9E37_79B9_7F4A_7C15;

/// Arbitrary odd constant that separates the high half's input from the stream's states. Any fixed value works;
/// changing it changes every seeded id, so it is frozen.
const SEED_DOMAIN: u64 = 0xD1B5_4A32_D192_ED03;

/// A deterministic id source: the same seed gives the same ids in the same order.
///
/// For tests only; never use it to mint ids that reach a saved file outside a test.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SeededIds {
    high: u64,
    state: u64,
    minted: u64,
}

impl SeededIds {
    /// A source seeded with `seed`.
    pub const fn new(seed: u64) -> Self {
        Self {
            high: mix64(seed ^ SEED_DOMAIN),
            state: seed,
            minted: 0,
        }
    }

    /// The next id: this source's high half, then the next SplitMix64 output as the low half.
    pub fn mint(&mut self) -> u128 {
        // Wrapping is the algorithm, not an overflow: the state walks the full u64 cycle by an odd step.
        self.state = self.state.wrapping_add(GOLDEN_GAMMA);
        let low = mix64(self.state);
        self.minted = self.minted.saturating_add(1);
        (u128::from(self.high) << 64) | u128::from(low)
    }

    /// How many ids this source has minted (saturating at `u64::MAX`).
    pub const fn minted(&self) -> u64 {
        self.minted
    }
}

/// SplitMix64's finaliser (the reference code's two multiply-xorshift rounds): a bijection on `u64`, so distinct
/// inputs always give distinct outputs. The shifts and multipliers are the reference constants.
const fn mix64(value: u64) -> u64 {
    let mut z = value;
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^ (z >> 31)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;

    /// Low 64 bits of an id.
    fn low(id: u128) -> u64 {
        u64::try_from(id & u128::from(u64::MAX)).unwrap()
    }

    /// High 64 bits of an id.
    fn high(id: u128) -> u64 {
        u64::try_from(id >> 64).unwrap()
    }

    // ── Basic functionality ─────────────────────────────────────────────────────────────────────────────────────

    /// Minting counts the ids handed out and keeps one high half per source.
    #[test]
    fn mint_counts_and_keeps_the_source_high_half() {
        let mut ids = SeededIds::new(9);
        let first = ids.mint();
        let second = ids.mint();
        assert_ne!(first, second);
        assert_eq!(high(first), high(second));
        assert_eq!(ids.minted(), 2);
    }

    // ── Known-value cross-validation ────────────────────────────────────────────────────────────────────────────

    /// The low halves for seed 0 are SplitMix64's published first outputs.
    ///
    /// Checks the implementation against the reference algorithm rather than against itself: the reference code
    /// seeded with 0 yields 0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4 and 0x06C45D188009454F.
    #[test]
    fn seed_zero_matches_splitmix64_reference_outputs() {
        let mut ids = SeededIds::new(0);
        assert_eq!(low(ids.mint()), 0xE220_A839_7B1D_CDAF);
        assert_eq!(low(ids.mint()), 0x6E78_9E6A_A1B9_65F4);
        assert_eq!(low(ids.mint()), 0x06C4_5D18_8009_454F);
    }

    // ── Determinism ─────────────────────────────────────────────────────────────────────────────────────────────

    /// The same seed gives the same sequence; a different seed gives a different one.
    #[test]
    fn same_seed_same_sequence() {
        let take = |seed| {
            let mut ids = SeededIds::new(seed);
            (0..5).map(|_| ids.mint()).collect::<Vec<_>>()
        };
        assert_eq!(take(1), take(1));
        assert_ne!(take(1), take(2));
    }

    // ── Boundary tests ──────────────────────────────────────────────────────────────────────────────────────────

    /// Ten thousand ids from one source are all distinct, and never collide with another seed's ids.
    ///
    /// Tests put many seeded entities into one document; a duplicate id would corrupt the identity map.
    #[test]
    fn ids_are_unique_within_and_across_sources() {
        let mut seen = HashSet::new();
        for seed in [0, 1, u64::MAX] {
            let mut ids = SeededIds::new(seed);
            for _ in 0..10_000 {
                assert!(seen.insert(ids.mint()), "duplicate id for seed {seed}");
            }
        }
    }

    // ── Integer overflow safety ─────────────────────────────────────────────────────────────────────────────────

    /// Extreme seeds mint without panicking (the stream's arithmetic wraps by design; the counter saturates).
    #[test]
    fn extreme_seeds_do_not_panic() {
        for seed in [
            u64::MAX,
            u64::MAX - GOLDEN_GAMMA,
            GOLDEN_GAMMA.wrapping_neg(),
        ] {
            let mut ids = SeededIds::new(seed);
            assert_ne!(ids.mint(), ids.mint());
        }
        let mut worn = SeededIds {
            high: 0,
            state: 0,
            minted: u64::MAX,
        };
        let _id = worn.mint();
        assert_eq!(worn.minted(), u64::MAX);
    }
}
