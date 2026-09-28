//! T07: patrol with a stop.

use crate::{Point, UnitIn};

/// A patrol team, its three loop points and the fuel depot it also visits.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub units: Vec<UnitIn>,
    pub a: Point,
    pub b: Point,
    pub c: Point,
    pub depot: Point,
}
