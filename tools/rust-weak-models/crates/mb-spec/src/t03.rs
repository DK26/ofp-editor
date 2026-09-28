//! T03: move and hold.

use crate::{Point, UnitIn};

/// A sentry team and its route; `points` always has at least one point.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub units: Vec<UnitIn>,
    pub points: Vec<Point>,
}
