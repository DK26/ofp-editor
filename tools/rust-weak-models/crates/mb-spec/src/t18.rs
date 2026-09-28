//! T18: orders from a list.

use crate::{Point, UnitIn};

/// One order of the brief.
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

/// The group's units (soldiers and vehicles) and its orders, in order.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub units: Vec<UnitIn>,
    pub orders: Vec<OrderIn>,
}
