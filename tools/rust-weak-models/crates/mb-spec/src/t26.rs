//! T26: full scenario.

use crate::{Point, Radio, UnitIn};

/// A group and its route.
#[derive(Debug, Clone, PartialEq)]
pub struct PatrolIn {
    pub callsign: String,
    pub units: Vec<UnitIn>,
    pub route: Vec<Point>,
}

/// The convoy: its units (the truck is one of them), the truck's label and where it goes.
#[derive(Debug, Clone, PartialEq)]
pub struct ConvoyIn {
    pub callsign: String,
    pub units: Vec<UnitIn>,
    pub truck: String,
    pub destination: Point,
}

/// The whole scenario.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    /// West patrol; its route has at least two points.
    pub patrol: PatrolIn,
    /// West convoy.
    pub convoy: ConvoyIn,
    /// East group.
    pub enemy: PatrolIn,
    /// Radio channel that releases a group.
    pub release: Radio,
    /// Callsign of the group whose first waypoint waits for the radio call.
    pub release_callsign: String,
    pub objective: Point,
    /// Half the side length of the objective square, in metres.
    pub objective_half_m: f64,
    /// How long West must hold the objective, in minutes: min, typical, max.
    pub hold_minutes: [f64; 3],
}
