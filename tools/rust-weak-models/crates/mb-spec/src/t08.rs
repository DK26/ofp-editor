//! T08: mounted assault.

use crate::{Point, UnitIn};

/// The assault team (soldiers and its vehicles), the label of the truck to board,
/// the drop point and the target.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub units: Vec<UnitIn>,
    pub truck: String,
    pub drop: Point,
    pub target: Point,
}
