//! T11: groups from a roster.

use crate::{Side, UnitIn};

/// One roster entry: a callsign and its units (possibly none).
#[derive(Debug, Clone, PartialEq)]
pub struct Entry {
    pub callsign: String,
    pub units: Vec<UnitIn>,
}

/// The side of every group and the roster, in order.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub side: Side,
    pub roster: Vec<Entry>,
}
