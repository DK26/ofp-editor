//! P01 (pilot): fire team.

use crate::UnitIn;

/// The soldiers of one West fire team, in brief order.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub units: Vec<UnitIn>,
}
