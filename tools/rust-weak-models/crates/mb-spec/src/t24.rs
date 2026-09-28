//! T24: plans in a collection.

use crate::{Point, Side, UnitIn};

/// How a group's plan ends.
#[derive(Debug, Clone, PartialEq)]
pub enum CloseIn {
    /// Repeat from the first waypoint.
    Loop,
    /// Stay at the point.
    Hold(Point),
    /// Add nothing.
    Open,
}

/// A group and how its plan ends.
#[derive(Debug, Clone, PartialEq)]
pub struct GroupIn {
    pub callsign: String,
    pub side: Side,
    pub units: Vec<UnitIn>,
    pub close: CloseIn,
}

/// One MOVE waypoint for the group at position `group` of `Input::groups` (from 0).
#[derive(Debug, Clone, PartialEq)]
pub struct EditIn {
    pub group: usize,
    pub point: Point,
}

/// The HQ units, the groups and the edits, each in order.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub hq: Vec<UnitIn>,
    pub groups: Vec<GroupIn>,
    pub edits: Vec<EditIn>,
}
