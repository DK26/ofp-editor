//! Mission builder: create groups, units, waypoints and triggers, check the
//! mission against the domain rules and export it as `mbx` text.
//!
//! Typical use: `Mission::new()`, then `add_group` and `add_unit` for each group,
//! `add_waypoint` for each group's plan, `add_trigger` and the `sync_*` calls, then
//! `validate()` and, when it returns `Ok`, `export()`.
//!
//! Units, groups and triggers are addressed by `u32` ids returned by the `add_*`
//! methods; waypoints by `(group id, 0-based waypoint index)`. Positions are
//! [`Point`]s in metres, durations are `f64` seconds and angles are `f64` degrees.
//! Most methods return `Result<_, MissionError>`.

// Implementation notes (not part of the listing): every method maps onto the hidden
// `mb-core` model; local checks cover ids, map bounds and duplicate callsigns, and
// the sequence/trigger rules are checked by `validate`, as the design specifies.

use std::fmt;

use mb_core as core;

pub use mb_spec::{Ending, Point, Radio, Rank, Side, UnitClass};

/// Map edge length in metres; valid coordinates are `0.0..=MAP_SIZE` on both axes.
pub const MAP_SIZE: f64 = 12_800.0;

/// Returns the point at `bearing_deg` (degrees clockwise from north) and
/// `distance_m` (metres) from `from`.
pub fn offset(from: Point, bearing_deg: f64, distance_m: f64) -> Point {
    let (x, z) = core::offset(from.x, from.z, bearing_deg, distance_m);
    Point { x, z }
}

/// A waypoint of a group's plan.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Waypoint {
    /// Move to a point.
    Move(Point),
    /// Move to a point and engage enemies there.
    SeekAndDestroy(Point),
    /// Stay at a point.
    Hold(Point),
    /// Board the vehicle with this unit id.
    GetIn(u32),
    /// Leave the vehicle at a point.
    GetOut(Point),
    /// Repeat the plan from the first waypoint.
    Cycle,
}

/// Condition that activates a trigger.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Activation {
    /// No condition.
    None,
    /// Units of the side are in the area.
    Present(Side),
    /// No units of the side are in the area.
    NotPresent(Side),
    /// The detector side has detected the detected side in the area.
    DetectedBy { detector: Side, detected: Side },
    /// The player calls the radio channel.
    Radio(Radio),
}

/// Whether a trigger can fire again.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Repeat {
    Once,
    Repeatedly,
}

/// Timer flavour.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TimerKind {
    /// Fires after the delay once the condition became true.
    Countdown,
    /// Fires once the condition stayed true for the delay.
    Timeout,
}

/// Trigger timer; `min`, `mid` and `max` are seconds.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Timer {
    /// Countdown or timeout.
    pub kind: TimerKind,
    /// Shortest delay in seconds.
    pub min: f64,
    /// Typical delay in seconds.
    pub mid: f64,
    /// Longest delay in seconds.
    pub max: f64,
}

impl Timer {
    /// Creates a timer from seconds.
    ///
    /// # Errors
    /// `MissionError::TimerOrder` unless `0 <= min <= mid <= max`.
    pub fn new(kind: TimerKind, min: f64, mid: f64, max: f64) -> Result<Timer, MissionError> {
        let ordered = min <= mid && mid <= max;
        if ordered && min >= 0.0 {
            Ok(Timer { kind, min, mid, max })
        } else {
            Err(MissionError::TimerOrder { min, mid, max })
        }
    }
}

/// What a trigger does when it fires.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Effect {
    None,
    /// Ends the mission with this ending.
    End(Ending),
    /// The player loses.
    Lose,
}

/// Rectangular trigger area: centre, half sizes `a` (east-west) and `b`
/// (north-south) in metres, rotated by `angle` degrees.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Area {
    /// Centre of the rectangle.
    pub centre: Point,
    /// Half size along the east-west axis, in metres.
    pub a: f64,
    /// Half size along the north-south axis, in metres.
    pub b: f64,
    /// Rotation in degrees.
    pub angle: f64,
}

impl Area {
    /// Creates an area.
    pub fn new(centre: Point, a: f64, b: f64, angle: f64) -> Area {
        Area { centre, a, b, angle }
    }

    /// An area covering the whole map.
    pub fn whole_map() -> Area {
        let half = MAP_SIZE / 2.0;
        Area { centre: Point { x: half, z: half }, a: half, b: half, angle: 0.0 }
    }
}

/// A trigger definition, passed to [`Mission::add_trigger`].
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Trigger {
    /// Where the condition is evaluated.
    pub area: Area,
    /// The condition.
    pub activation: Activation,
    /// Once (default) or repeatedly.
    pub repeat: Repeat,
    /// Optional delay.
    pub timer: Option<Timer>,
    /// What happens when it fires.
    pub effect: Effect,
}

impl Trigger {
    /// Creates a trigger that fires once, without timer or effect.
    pub fn new(area: Area, activation: Activation) -> Trigger {
        Trigger { area, activation, repeat: Repeat::Once, timer: None, effect: Effect::None }
    }
}

/// Errors reported by [`Mission`] methods and by [`Mission::validate`].
#[derive(Debug, Clone, PartialEq)]
pub enum MissionError {
    /// No group has this id.
    UnknownGroup { group: u32 },
    /// No unit has this id.
    UnknownUnit { unit: u32 },
    /// No trigger has this id.
    UnknownTrigger { trigger: u32 },
    /// The group has no waypoint with this index.
    UnknownWaypoint { group: u32, index: usize },
    /// Another group already uses the callsign.
    DuplicateCallsign { callsign: String },
    /// A position lies outside the map.
    OutOfMap { x: f64, z: f64 },
    /// The unit is not a truck, jeep or APC.
    NotAVehicle { unit: u32 },
    /// The unit belongs to another group.
    NotInGroup { group: u32, unit: u32 },
    /// The group has no units.
    EmptyGroup { callsign: String },
    /// A CYCLE waypoint is not the last one.
    CycleNotLast { callsign: String },
    /// A CYCLE has fewer than two MOVE or SEEK_AND_DESTROY waypoints before it.
    TooFewWaypoints { callsign: String, moves: usize },
    /// A waypoint follows HOLD.
    AfterHold { callsign: String },
    /// A GET_OUT has no GET_IN before it.
    GetOutWithoutGetIn { callsign: String, index: usize },
    /// A GET_IN targets a vehicle of another side.
    WrongSide { callsign: String, vehicle: u32 },
    /// Timer values are not `0 <= min <= mid <= max`.
    TimerOrder { min: f64, mid: f64, max: f64 },
    /// A DETECTED_BY trigger uses the same side twice.
    SameSide { side: Side },
    /// An END or LOSE trigger repeats.
    RepeatingEnd { trigger: u32 },
}

impl fmt::Display for MissionError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            MissionError::UnknownGroup { group } => write!(f, "unknown group {group}"),
            MissionError::UnknownUnit { unit } => write!(f, "unknown unit {unit}"),
            MissionError::UnknownTrigger { trigger } => write!(f, "unknown trigger {trigger}"),
            MissionError::UnknownWaypoint { group, index } => {
                write!(f, "group {group} has no waypoint {index}")
            }
            MissionError::DuplicateCallsign { callsign } => write!(f, "callsign {callsign:?} already used"),
            MissionError::OutOfMap { x, z } => write!(f, "position ({x}, {z}) is outside the map"),
            MissionError::NotAVehicle { unit } => write!(f, "unit {unit} is not a vehicle"),
            MissionError::NotInGroup { group, unit } => write!(f, "unit {unit} is not in group {group}"),
            MissionError::EmptyGroup { callsign } => write!(f, "group {callsign:?} has no units"),
            MissionError::CycleNotLast { callsign } => write!(f, "group {callsign:?}: CYCLE is not last"),
            MissionError::TooFewWaypoints { callsign, moves } => {
                write!(f, "group {callsign:?}: CYCLE needs 2 moves before it, found {moves}")
            }
            MissionError::AfterHold { callsign } => write!(f, "group {callsign:?}: waypoint after HOLD"),
            MissionError::GetOutWithoutGetIn { callsign, index } => {
                write!(f, "group {callsign:?}: GET_OUT at {index} without GET_IN")
            }
            MissionError::WrongSide { callsign, vehicle } => {
                write!(f, "group {callsign:?}: vehicle {vehicle} belongs to another side")
            }
            MissionError::TimerOrder { min, mid, max } => {
                write!(f, "timer {min}/{mid}/{max} is not 0 <= min <= mid <= max")
            }
            MissionError::SameSide { side } => write!(f, "{side:?} cannot detect itself"),
            MissionError::RepeatingEnd { trigger } => write!(f, "trigger {trigger} ends the mission but repeats"),
        }
    }
}

impl std::error::Error for MissionError {}

/// Exported mission text.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Exported {
    text: String,
}

impl Exported {
    /// The `mbx` text.
    pub fn text(&self) -> &str {
        &self.text
    }
}

/// A mission under construction.
#[derive(Debug, Clone, Default)]
pub struct Mission {
    model: core::Model,
}

fn idx(id: u32) -> usize {
    usize::try_from(id).unwrap_or(usize::MAX)
}

fn id(index: usize) -> u32 {
    u32::try_from(index).unwrap_or(u32::MAX)
}

impl Mission {
    /// Creates an empty mission.
    pub fn new() -> Mission {
        Mission::default()
    }

    /// Adds a group and returns its id.
    ///
    /// # Errors
    /// `DuplicateCallsign` if another group uses `callsign`.
    pub fn add_group(&mut self, side: Side, callsign: &str) -> Result<u32, MissionError> {
        if self.model.group_index(callsign).is_some() {
            return Err(MissionError::DuplicateCallsign { callsign: callsign.to_string() });
        }
        self.model.groups.push(core::Group {
            side,
            callsign: callsign.to_string(),
            units: Vec::new(),
            leader: None,
            plan: Vec::new(),
            plan_assigned: false,
        });
        Ok(id(self.model.groups.len() - 1))
    }

    /// Adds a unit to a group and returns the unit id. The unit takes the group's side.
    ///
    /// # Errors
    /// `UnknownGroup`, or `OutOfMap` if `pos` is outside the map.
    pub fn add_unit(&mut self, group: u32, class: UnitClass, label: &str, pos: Point, rank: Rank) -> Result<u32, MissionError> {
        if self.model.groups.get(idx(group)).is_none() {
            return Err(MissionError::UnknownGroup { group });
        }
        if !core::in_map(pos.x, pos.z) {
            return Err(MissionError::OutOfMap { x: pos.x, z: pos.z });
        }
        self.model
            .push_unit(idx(group), class, label, pos.x, pos.z, rank)
            .map(id)
            .ok_or(MissionError::UnknownGroup { group })
    }

    /// Makes `unit` the group's leader. Without this call the highest-ranked unit
    /// leads (the first listed on ties).
    ///
    /// # Errors
    /// `UnknownGroup`, `UnknownUnit`, or `NotInGroup`.
    pub fn set_leader(&mut self, group: u32, unit: u32) -> Result<(), MissionError> {
        let owner = self.model.units.get(idx(unit)).map(|u| u.group).ok_or(MissionError::UnknownUnit { unit })?;
        let g = self.model.groups.get_mut(idx(group)).ok_or(MissionError::UnknownGroup { group })?;
        if owner != idx(group) {
            return Err(MissionError::NotInGroup { group, unit });
        }
        g.leader = Some(idx(unit));
        Ok(())
    }

    /// Appends a waypoint to the group's plan and returns its 0-based index.
    ///
    /// # Errors
    /// `UnknownGroup`, `OutOfMap`, `UnknownUnit` or `NotAVehicle` (for `GetIn`).
    pub fn add_waypoint(&mut self, group: u32, waypoint: Waypoint) -> Result<usize, MissionError> {
        let wp = match waypoint {
            Waypoint::Move(p) => core::Wp::Move(p.x, p.z),
            Waypoint::SeekAndDestroy(p) => core::Wp::Sad(p.x, p.z),
            Waypoint::Hold(p) => core::Wp::Hold(p.x, p.z),
            Waypoint::GetOut(p) => core::Wp::GetOut(p.x, p.z),
            Waypoint::GetIn(unit) => {
                let u = self.model.units.get(idx(unit)).ok_or(MissionError::UnknownUnit { unit })?;
                if !u.class.is_vehicle() {
                    return Err(MissionError::NotAVehicle { unit });
                }
                core::Wp::GetIn(idx(unit))
            }
            Waypoint::Cycle => core::Wp::Cycle,
        };
        if let core::Wp::Move(x, z) | core::Wp::Sad(x, z) | core::Wp::Hold(x, z) | core::Wp::GetOut(x, z) = wp {
            if !core::in_map(x, z) {
                return Err(MissionError::OutOfMap { x, z });
            }
        }
        let g = self.model.groups.get_mut(idx(group)).ok_or(MissionError::UnknownGroup { group })?;
        g.plan.push(wp);
        Ok(g.plan.len() - 1)
    }

    /// Synchronises two waypoints, each given as `(group id, waypoint index)`.
    ///
    /// # Errors
    /// `UnknownGroup` or `UnknownWaypoint`.
    pub fn sync_waypoints(&mut self, a: (u32, usize), b: (u32, usize)) -> Result<(), MissionError> {
        let a = self.wp_at(a)?;
        let b = self.wp_at(b)?;
        self.model.wp_syncs.push((a, b));
        Ok(())
    }

    /// Adds a trigger and returns its id.
    ///
    /// # Errors
    /// `OutOfMap` if the area centre is outside the map.
    pub fn add_trigger(&mut self, trigger: Trigger) -> Result<u32, MissionError> {
        let c = trigger.area.centre;
        if !core::in_map(c.x, c.z) {
            return Err(MissionError::OutOfMap { x: c.x, z: c.z });
        }
        let act = match trigger.activation {
            Activation::None => core::Act::None,
            Activation::Present(s) => core::Act::Present(s),
            Activation::NotPresent(s) => core::Act::NotPresent(s),
            Activation::DetectedBy { detector, detected } => core::Act::DetectedBy { detector, detected },
            Activation::Radio(r) => core::Act::Radio(r),
        };
        let timer = trigger.timer.map(|t| core::Timer {
            kind: match t.kind {
                TimerKind::Countdown => core::TimerKind::Countdown,
                TimerKind::Timeout => core::TimerKind::Timeout,
            },
            min: t.min,
            mid: t.mid,
            max: t.max,
        });
        let effect = match trigger.effect {
            Effect::None => core::Effect::None,
            Effect::End(e) => core::Effect::End(e),
            Effect::Lose => core::Effect::Lose,
        };
        self.model.triggers.push(core::Trigger {
            cx: c.x,
            cz: c.z,
            a: trigger.area.a,
            b: trigger.area.b,
            angle: trigger.area.angle,
            act,
            repeating: trigger.repeat == Repeat::Repeatedly,
            timer,
            effect,
            syncs: Vec::new(),
        });
        Ok(id(self.model.triggers.len() - 1))
    }

    /// Synchronises a trigger with a waypoint `(group id, waypoint index)`.
    ///
    /// # Errors
    /// `UnknownTrigger`, `UnknownGroup` or `UnknownWaypoint`.
    pub fn sync_trigger(&mut self, trigger: u32, waypoint: (u32, usize)) -> Result<(), MissionError> {
        let at = self.wp_at(waypoint)?;
        let t = self.model.triggers.get_mut(idx(trigger)).ok_or(MissionError::UnknownTrigger { trigger })?;
        t.syncs.push(at);
        Ok(())
    }

    /// Sets the free-text note written into the export.
    pub fn set_note(&mut self, note: &str) {
        self.model.note = Some(note.to_string());
    }

    /// Returns the id of the group with this callsign.
    pub fn group_by_callsign(&self, callsign: &str) -> Option<u32> {
        self.model.group_index(callsign).map(id)
    }

    /// Returns the id of the first unit with this label.
    pub fn unit_by_label(&self, label: &str) -> Option<u32> {
        self.model.unit_index(label).map(id)
    }

    /// Returns the id of the first vehicle with this label.
    pub fn vehicle_by_label(&self, label: &str) -> Option<u32> {
        self.model.vehicle_index(label).map(id)
    }

    /// Returns the number of waypoints in the group's plan.
    pub fn waypoint_count(&self, group: u32) -> Option<usize> {
        self.model.groups.get(idx(group)).map(|g| g.plan.len())
    }

    /// Checks the whole mission against the domain rules.
    ///
    /// # Errors
    /// Every problem found, in a stable order.
    pub fn validate(&self) -> Result<(), Vec<MissionError>> {
        let errors: Vec<MissionError> = core::check(&self.model).into_iter().map(|v| self.map_violation(v)).collect();
        if errors.is_empty() { Ok(()) } else { Err(errors) }
    }

    /// Exports the mission as `mbx` text. Call [`Mission::validate`] first: `export`
    /// does not check the rules.
    pub fn export(&self) -> Exported {
        Exported { text: core::write(&self.model) }
    }

    fn wp_at(&self, (group, index): (u32, usize)) -> Result<core::WpAt, MissionError> {
        let g = self.model.groups.get(idx(group)).ok_or(MissionError::UnknownGroup { group })?;
        if index >= g.plan.len() {
            return Err(MissionError::UnknownWaypoint { group, index });
        }
        Ok(core::WpAt { group: idx(group), index })
    }

    fn map_violation(&self, v: core::Violation) -> MissionError {
        let cs = |g: usize| self.model.callsign(g).to_string();
        match v {
            core::Violation::CycleNotLast { group, .. } => MissionError::CycleNotLast { callsign: cs(group) },
            core::Violation::TooFewMoves { group, moves } => MissionError::TooFewWaypoints { callsign: cs(group), moves },
            core::Violation::AfterHold { group, .. } => MissionError::AfterHold { callsign: cs(group) },
            core::Violation::GetOutWithoutGetIn { group, index } => {
                MissionError::GetOutWithoutGetIn { callsign: cs(group), index }
            }
            core::Violation::UnknownVehicle { unit, .. } => MissionError::UnknownUnit { unit: id(unit) },
            core::Violation::NotAVehicle { unit, .. } => MissionError::NotAVehicle { unit: id(unit) },
            core::Violation::WrongSide { group, unit, .. } => {
                MissionError::WrongSide { callsign: cs(group), vehicle: id(unit) }
            }
            core::Violation::DanglingSync { group, index } => MissionError::UnknownWaypoint { group: id(group), index },
            core::Violation::TimerOrder { trigger } => {
                let t = self.model.triggers.get(trigger).and_then(|t| t.timer);
                let (min, mid, max) = t.map(|t| (t.min, t.mid, t.max)).unwrap_or((0.0, 0.0, 0.0));
                MissionError::TimerOrder { min, mid, max }
            }
            core::Violation::SameSide { side, .. } => MissionError::SameSide { side },
            core::Violation::RepeatingEnd { trigger } => MissionError::RepeatingEnd { trigger: id(trigger) },
            core::Violation::EmptyGroup { group } => MissionError::EmptyGroup { callsign: cs(group) },
            core::Violation::DuplicateCallsign { group } => MissionError::DuplicateCallsign { callsign: cs(group) },
            core::Violation::OutOfMap { x, z } => MissionError::OutOfMap { x, z },
            core::Violation::LeaderNotInGroup { group } => {
                let unit = self.model.groups.get(group).and_then(|g| g.leader).map(id).unwrap_or(u32::MAX);
                MissionError::NotInGroup { group: id(group), unit }
            }
            core::Violation::ForeignId { .. } => MissionError::UnknownUnit { unit: u32::MAX },
        }
    }
}
