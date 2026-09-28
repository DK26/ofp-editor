//! What `solve` returns when the task text says to refuse.

/// Why `solve` declined to build a mission. Return exactly the variant the task
/// text names for the situation; never panic instead.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Refusal {
    OutOfMap,
    TooFewWaypoints,
    UnknownVehicle,
    UnknownGroup,
    RepeatingEnd,
    SameSide,
    EmptyGroup,
    DuplicateCallsign,
    TimerOrder,
    WrongSide,
    InvalidSequence,
    /// Every problem found, sorted ascending (only where a task asks for it).
    Many(Vec<Problem>),
}

/// One problem inside `Refusal::Many`. The derived order sorts by variant in the
/// order declared here, then by the text.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub enum Problem {
    /// A callsign used again; carries the repeated callsign.
    DuplicateCallsign(String),
    /// A group with no units; carries its callsign.
    EmptyGroup(String),
    /// A unit placed outside the map; carries the unit's label.
    OutOfMap(String),
}
