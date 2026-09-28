//! T04: patrol loop.

use crate::{Point, UnitIn};

/// A patrol team and the points of its loop, in order.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub units: Vec<UnitIn>,
    pub points: Vec<Point>,
}
