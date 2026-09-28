//! P03 (pilot): base alarm.

use crate::{Point, UnitIn};

/// The West base garrison and the base area (a square around `base`).
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub units: Vec<UnitIn>,
    pub base: Point,
    /// Half the side length of the square area, in metres.
    pub half_size_m: f64,
}
