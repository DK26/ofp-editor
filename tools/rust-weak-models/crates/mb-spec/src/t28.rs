//! T28: staged objectives.

use crate::{Ending, Point, Radio, UnitIn};

/// The group, its two waypoints, the bridge area, the release channel, the
/// countdown in minutes (min, typical, max) and the ending.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub callsign: String,
    pub units: Vec<UnitIn>,
    pub start: Point,
    pub bridge: Point,
    /// Half the side length of the bridge square, in metres.
    pub bridge_half_m: f64,
    pub release: Radio,
    pub minutes: [f64; 3],
    pub ending: Ending,
}
