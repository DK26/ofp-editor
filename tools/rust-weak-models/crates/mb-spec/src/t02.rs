//! T02: two-point move.

use crate::{Point, UnitIn};

/// A two-man team and the two points it moves through, in order.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub units: Vec<UnitIn>,
    pub first: Point,
    pub second: Point,
}
