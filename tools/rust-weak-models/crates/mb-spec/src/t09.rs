//! T09: presence ending.

use crate::{Point, UnitIn};

/// The town's defenders, the town square and whether the brief asked the ending to repeat.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub units: Vec<UnitIn>,
    pub town: Point,
    /// Half the side length of the town square, in metres.
    pub town_half_m: f64,
    pub repeating: bool,
}
