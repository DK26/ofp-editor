//! T14: hold-true timer.

use crate::{Point, UnitIn};

/// The holdout team, its post (a square around `post`) and the three durations.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub units: Vec<UnitIn>,
    pub post: Point,
    /// Half the side length of the square, in metres.
    pub post_half_m: f64,
    /// Durations in seconds, in the brief's order: longest, shortest, typical.
    pub seconds: [f64; 3],
}
