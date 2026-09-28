//! P04 (pilot): taxi ride.

use crate::{Point, UnitIn};

/// A West team whose roster includes its vehicles, the label of the vehicle to
/// ride, and the destination.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub units: Vec<UnitIn>,
    pub ride: String,
    pub destination: Point,
}
