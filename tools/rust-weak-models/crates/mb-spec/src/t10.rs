//! T10: detected by.

use crate::{Point, Side, UnitIn};

/// The scouts (side `watched`), the side watching them and the watched area.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub units: Vec<UnitIn>,
    pub watcher: Side,
    pub watched: Side,
    pub area: Point,
    /// Half the side length of the square area, in metres.
    pub area_half_m: f64,
}
