//! T23: reusable clear-the-area.

use crate::{Point, Side, UnitIn};

/// One order already given to a group.
#[derive(Debug, Clone, PartialEq)]
pub enum OrderIn {
    Move(Point),
    /// Seek and destroy at the point.
    Hunt(Point),
    /// Board the vehicle with this label.
    Board(String),
    /// Leave the vehicle at the point.
    Dismount(Point),
    Hold(Point),
    /// Repeat from the first waypoint.
    Loop,
}

/// A group, the orders it already has (always a valid sequence naming existing
/// vehicles) and the entry and target points of its clear-the-area sequence.
#[derive(Debug, Clone, PartialEq)]
pub struct ClearIn {
    pub callsign: String,
    pub side: Side,
    pub units: Vec<UnitIn>,
    pub prior: Vec<OrderIn>,
    pub entry: Point,
    pub target: Point,
}

/// The groups, in order.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub groups: Vec<ClearIn>,
}
