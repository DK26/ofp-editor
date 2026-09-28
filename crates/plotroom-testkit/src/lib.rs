// SPDX-License-Identifier: GPL-3.0-or-later
//! Shared test support for Plotroom crates (a dev-dependency, never shipped).
//!
//! **What it owns.** The M0 skeleton of the test kit named in `docs/architecture/crate-map.md` §12 and
//! `docs/roadmap/m0-m3-foundations-to-preview.md` (M0 "Crates"):
//!
//! - [`fixture_root!`] and [`OptInRoot`]: where a crate's committed synthetic fixtures live, and the opt-in local roots
//!   (`PLOTROOM_GAME_DIR`, `PLOTROOM_CORPUS_DIR`) that tests needing real data read (testing-strategy §15);
//! - [`BlobBuilder`]: a little-endian byte builder for synthetic binary fixtures, so format tests never commit game
//!   files (`AGENTS.md`, "Test Fixture Legality and CI Portability");
//! - [`VirtualClock`]: time that moves only when a test says so (no sleeps; testing-strategy §1 item 2);
//! - [`SeededIds`]: a deterministic source of 128-bit ids for tests (doc 45 §2.3: "tests: seeded counter").
//!
//! **Where it fits.** A dev-only crate outside the L0-L8 layer order (`xtask/layers.toml` gives it the role `dev`).
//! Product crates list it under `[dev-dependencies]` only; `cargo run -p xtask -- layers` fails on a normal or build
//! dependency on it. Later milestones add `EditorHarness`, `SqmBuilder`, synthetic PBO, WRP and raP builders, a
//! synthetic island and catalog, a faux model and cassettes (crate-map §12).
//!
//! **Placeholders.** The `Clock` and `IdSource` traits belong to `plotroom-ids` (M1), which does not exist yet; this
//! crate exposes the same operations as inherent methods ([`VirtualClock::now_ms`], [`SeededIds::mint`]) and gains
//! the trait impls when that crate lands. How production ids are minted is open (doc 45 open question 4); the seeded
//! source is for tests only.
//!
//! **Allocation profile.** [`BlobBuilder`] owns one growing `Vec<u8>`; everything else is allocation-free except the
//! `PathBuf`s the fixture helpers return.
//!
//! ```
//! use plotroom_testkit::{BlobBuilder, SeededIds, VirtualClock};
//!
//! // A tiny synthetic header: a zero-terminated name, then a little-endian length.
//! let blob = BlobBuilder::new().asciiz(b"demo").u32_le(7).into_bytes();
//! assert_eq!(blob, [b'd', b'e', b'm', b'o', 0, 7, 0, 0, 0]);
//!
//! // Same seed, same ids: a test can assert on them.
//! assert_eq!(SeededIds::new(42).mint(), SeededIds::new(42).mint());
//!
//! // Time moves only when the test moves it.
//! let mut clock = VirtualClock::starting_at_ms(1_000);
//! clock.advance_ms(250);
//! assert_eq!(clock.now_ms(), 1_250);
//! ```

pub mod blob;
pub mod clock;
pub mod error;
pub mod fixtures;
pub mod ids;

pub use blob::BlobBuilder;
pub use clock::VirtualClock;
pub use error::Error;
pub use fixtures::{OptInRoot, fixture_root_of};
pub use ids::SeededIds;
