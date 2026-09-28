//! T15: trigger releases a group.

use crate::{Point, Radio, Side, UnitIn};

/// A group and the route it moves through (one MOVE waypoint per point).
#[derive(Debug, Clone, PartialEq)]
pub struct PatrolIn {
    pub callsign: String,
    pub side: Side,
    pub units: Vec<UnitIn>,
    pub route: Vec<Point>,
}

/// The groups, the callsign of the group that waits, the number of the waypoint where
/// it waits (counted from 1) and the radio channel that releases it.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub groups: Vec<PatrolIn>,
    pub waiting: String,
    pub number: usize,
    pub channel: Radio,
}
