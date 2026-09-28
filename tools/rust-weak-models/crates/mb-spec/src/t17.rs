//! T17: ambush then extract.

use crate::{Point, UnitIn};

/// The ambush team, the ambush point, the kill zone (a square) and the extraction point.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub units: Vec<UnitIn>,
    pub ambush: Point,
    pub kill_zone: Point,
    /// Half the side length of the kill-zone square, in metres.
    pub kill_zone_half_m: f64,
    pub extraction: Point,
}
