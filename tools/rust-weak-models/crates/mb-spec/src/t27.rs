//! T27: repair a broken draft.

use crate::{Point, Radio, Side, UnitIn};

/// A raw group: callsign, side, units and route (one MOVE per point).
#[derive(Debug, Clone, PartialEq)]
pub struct RawGroup {
    pub callsign: String,
    pub side: Side,
    pub units: Vec<UnitIn>,
    pub route: Vec<Point>,
}

/// A numeric reference: group position in `Input::groups` and waypoint index,
/// both counted from 0. It may be broken.
#[derive(Debug, Clone, PartialEq)]
pub struct RawRef {
    pub group: usize,
    pub waypoint: usize,
}

/// A raw radio trigger and the waypoints it should be synchronised with.
#[derive(Debug, Clone, PartialEq)]
pub struct RawTrigger {
    pub channel: Radio,
    pub syncs: Vec<RawRef>,
}

/// The raw draft.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub groups: Vec<RawGroup>,
    pub triggers: Vec<RawTrigger>,
}
