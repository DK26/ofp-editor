//! Unforgeable ids: each carries the creating mission's nonce and an index, and
//! has no public constructor, so the only way to hold one is to get it from the
//! mission (design note: deliberately no `from_raw`).

/// A group of this mission. Get it from `Mission::add_group` or `Mission::group(callsign)`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct GroupId {
    pub(crate) mission: u64,
    pub(crate) index: usize,
}

/// A unit of this mission. Get it from `Mission::add_unit` or `Mission::unit(label)`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct UnitId {
    pub(crate) mission: u64,
    pub(crate) index: usize,
}

/// A vehicle unit (truck, jeep, APC). Get it from `Mission::vehicle(label)`, which
/// returns `None` when no vehicle has that label: handle that case, do not unwrap.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct VehicleId {
    pub(crate) mission: u64,
    pub(crate) index: usize,
}

/// An existing waypoint. Get it from `Mission::waypoint(group, index)` after the
/// group's plan was assigned.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct WaypointRef {
    pub(crate) mission: u64,
    pub(crate) group: usize,
    pub(crate) index: usize,
}

/// A trigger of this mission. Get it from `Mission::add_trigger`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct TriggerId {
    pub(crate) mission: u64,
    pub(crate) index: usize,
}
