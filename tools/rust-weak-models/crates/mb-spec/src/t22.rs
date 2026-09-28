//! T22: bearing and distance.

use crate::{Point, Rank, UnitClass};

/// A unit placed relative to the anchor.
#[derive(Debug, Clone, PartialEq)]
pub struct PlacedIn {
    pub class: UnitClass,
    pub label: String,
    pub rank: Rank,
    /// Degrees clockwise from north.
    pub bearing_deg: f64,
    /// Kilometres from the anchor.
    pub distance_km: f64,
}

/// The anchor point and the units around it.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub anchor: Point,
    pub units: Vec<PlacedIn>,
}
