//! T01: single squad.

use crate::UnitIn;

/// The squad in brief order. Exactly one unit is a Sergeant; the others rank lower.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub units: Vec<UnitIn>,
}
