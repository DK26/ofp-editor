//! T12: leader by rank.

use crate::{Side, UnitIn};

/// One group of the brief. It always has at least one soldier.
#[derive(Debug, Clone, PartialEq)]
pub struct GroupIn {
    pub callsign: String,
    pub side: Side,
    pub units: Vec<UnitIn>,
}

/// The groups, in order.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub groups: Vec<GroupIn>,
}
