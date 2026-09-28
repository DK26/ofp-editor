//! T16: convoy.

use crate::{Point, Side, UnitIn};

/// An infantry squad and the label of the truck it boards.
#[derive(Debug, Clone, PartialEq)]
pub struct SquadIn {
    pub callsign: String,
    pub side: Side,
    pub units: Vec<UnitIn>,
    pub truck: String,
}

/// The motor pool (its callsign, side and vehicles), the squads and the destination.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub pool_callsign: String,
    pub pool_side: Side,
    pub vehicles: Vec<UnitIn>,
    pub squads: Vec<SquadIn>,
    pub destination: Point,
}
