//! T13: two groups in step.

use crate::{Point, Side, UnitIn};

/// A group and the route it moves through (one MOVE waypoint per point).
#[derive(Debug, Clone, PartialEq)]
pub struct PatrolIn {
    pub callsign: String,
    pub side: Side,
    pub units: Vec<UnitIn>,
    pub route: Vec<Point>,
}

/// A waypoint as the brief names it: a group's callsign and the waypoint's number,
/// counted from 1 (1 is the group's first waypoint).
#[derive(Debug, Clone, PartialEq)]
pub struct WaypointNo {
    pub callsign: String,
    pub number: usize,
}

/// The groups, in order, and the two waypoints to synchronise.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub groups: Vec<PatrolIn>,
    pub first: WaypointNo,
    pub second: WaypointNo,
}
