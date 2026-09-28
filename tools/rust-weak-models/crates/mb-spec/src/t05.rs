//! T05: radio ending.

use crate::{Ending, Radio, UnitIn};

/// The headquarters team, the radio channel the player calls and the ending it gives.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub units: Vec<UnitIn>,
    pub channel: Radio,
    pub ending: Ending,
}
