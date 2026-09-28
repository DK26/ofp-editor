//! T19: merge two drafts.

use crate::{Point, Side, UnitIn};

/// A group and the route it moves through (one MOVE waypoint per point).
#[derive(Debug, Clone, PartialEq)]
pub struct PatrolIn {
    pub callsign: String,
    pub side: Side,
    pub units: Vec<UnitIn>,
    pub route: Vec<Point>,
}

/// A synchronisation inside one draft: two groups by their position in that draft's
/// `groups` list and two waypoint indices, all counted from 0.
#[derive(Debug, Clone, PartialEq)]
pub struct SyncIn {
    pub group_a: usize,
    pub wp_a: usize,
    pub group_b: usize,
    pub wp_b: usize,
}

/// One draft: its groups and its synchronisations.
#[derive(Debug, Clone, PartialEq)]
pub struct DraftIn {
    pub groups: Vec<PatrolIn>,
    pub syncs: Vec<SyncIn>,
}

/// The two drafts to merge.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub first: DraftIn,
    pub second: DraftIn,
}
