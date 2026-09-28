//! P02 (pilot): guard post.

use crate::{Point, UnitIn};

/// An East guard team, the gate it walks to and the post where it stays.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub units: Vec<UnitIn>,
    pub gate: Point,
    pub post: Point,
}
