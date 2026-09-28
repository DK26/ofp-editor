//! T06: countdown in minutes.

use crate::{Point, UnitIn};

/// The garrison, its zone (a square around `zone`) and the countdown, in minutes.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub units: Vec<UnitIn>,
    pub zone: Point,
    /// Half the side length of the square zone, in metres.
    pub zone_half_m: f64,
    pub minutes_min: f64,
    pub minutes_typical: f64,
    pub minutes_max: f64,
}
