//! T21: win and lose.

use crate::{Ending, Radio, UnitIn};

/// The player's team, the radio channel that wins and the ending it gives.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub units: Vec<UnitIn>,
    pub win_channel: Radio,
    pub win_ending: Ending,
}
