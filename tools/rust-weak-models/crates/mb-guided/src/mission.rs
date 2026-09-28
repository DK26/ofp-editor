//! The mission typestate (`Mission<Draft | Validated>`), its edit and lookup
//! methods, validation and export.

use std::fmt;
use std::marker::PhantomData;
use std::sync::atomic::{AtomicU64, Ordering};

use mb_core as core;
use mb_spec::{Rank, Side, UnitClass};

use crate::ids::{GroupId, TriggerId, UnitId, VehicleId, WaypointRef};
use crate::measure::Pos;
use crate::plan::{AnyPlan, Step};
use crate::sealed::Sealed;
use crate::trigger::{ActivationSet, TriggerBuilder};

/// Source of per-mission nonces that make ids from one mission unusable in another.
static NEXT_MISSION: AtomicU64 = AtomicU64::new(1);

/// Mission state: editable, not yet checked. `validate()` turns it into `Mission<Validated>`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Draft;
/// Mission state: checked and read-only; the only state that can be exported.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Validated;

impl Sealed for Draft {}
impl Sealed for Validated {}

/// Mission states that can be edited: `Draft`.
#[diagnostic::on_unimplemented(
    message = "a `Mission<{Self}>` is read-only: it cannot be edited after validation",
    label = "this mission was already validated",
    note = "fix: do every edit before `validate()`; to change a validated mission call `.into_draft()`, edit it, then `.validate()` again before `export()`"
)]
pub trait Editable: Sealed {}
impl Editable for Draft {}

/// Mission states that can be exported: `Validated`.
#[diagnostic::on_unimplemented(
    message = "`Mission<{Self}>` cannot be exported: only a validated mission can be exported",
    label = "this mission has not been validated",
    note = "fix: `let mission = mission.validate().map_err(...)?;` then call `.export()` on the `Mission<Validated>` it returns"
)]
pub trait Exportable: Sealed {}
impl Exportable for Validated {}

/// Error: the callsign is already used by another group (rule R9).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DuplicateCallsign {
    pub callsign: String,
}

impl fmt::Display for DuplicateCallsign {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "callsign {:?} already used", self.callsign)
    }
}

impl std::error::Error for DuplicateCallsign {}

/// Error: the unit does not belong to the group.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct NotInGroup;

impl fmt::Display for NotInGroup {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("the unit is not in this group")
    }
}

impl std::error::Error for NotInGroup {}

/// Error from [`Mission::assign_plan`].
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PlanError {
    /// The group has no units yet: add units before assigning its plan (rule R9).
    EmptyGroup { callsign: String },
    /// A `get_in` vehicle belongs to another side (rule R4).
    WrongSide { callsign: String },
    /// The group already has a plan; a plan is assigned once.
    AlreadyAssigned { callsign: String },
    /// An id from a different `Mission` value was used.
    ForeignId,
}

impl fmt::Display for PlanError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            PlanError::EmptyGroup { callsign } => write!(f, "group {callsign:?} has no units"),
            PlanError::WrongSide { callsign } => write!(f, "group {callsign:?} boards a vehicle of another side"),
            PlanError::AlreadyAssigned { callsign } => write!(f, "group {callsign:?} already has a plan"),
            PlanError::ForeignId => f.write_str("id from another mission"),
        }
    }
}

impl std::error::Error for PlanError {}

/// One problem found by [`Mission::validate`].
#[derive(Debug, Clone, PartialEq)]
pub enum Issue {
    /// A group without units (rule R9).
    EmptyGroup { callsign: String },
    /// An id from a different `Mission` value was used.
    ForeignId { what: &'static str },
    /// Any other rule violation.
    Rule { rule: &'static str, detail: String },
}

/// Error from [`Mission::validate`]: every problem found.
#[derive(Debug, Clone, PartialEq)]
pub struct ValidationReport {
    issues: Vec<Issue>,
}

impl ValidationReport {
    /// The problems, in a stable order.
    pub fn issues(&self) -> &[Issue] {
        &self.issues
    }
}

impl fmt::Display for ValidationReport {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{} validation issue(s): {:?}", self.issues.len(), self.issues)
    }
}

impl std::error::Error for ValidationReport {}

/// Exported mission text. Only `Mission<Validated>::export` creates one.
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

/// A mission. `Mission<Draft>` (the default) is editable; `Mission<Validated>` is
/// checked, read-only and exportable.
#[derive(Debug, Clone)]
pub struct Mission<State = Draft> {
    model: core::Model,
    nonce: u64,
    _state: PhantomData<State>,
}

impl Mission<Draft> {
    /// An empty draft mission.
    pub fn new() -> Mission<Draft> {
        let nonce = NEXT_MISSION.fetch_add(1, Ordering::Relaxed);
        Mission { model: core::Model::default(), nonce, _state: PhantomData }
    }

    /// Checks every rule. On success returns the `Mission<Validated>` to export;
    /// on failure a `ValidationReport` listing every problem. Consumes the draft:
    /// keep using the returned value, e.g. `let mission = mission.validate().map_err(...)?;`.
    pub fn validate(self) -> Result<Mission<Validated>, ValidationReport> {
        let issues: Vec<Issue> = core::check(&self.model).into_iter().map(|v| issue(&self.model, v)).collect();
        if issues.is_empty() {
            Ok(Mission { model: self.model, nonce: self.nonce, _state: PhantomData })
        } else {
            Err(ValidationReport { issues })
        }
    }
}

impl Default for Mission<Draft> {
    fn default() -> Self {
        Mission::new()
    }
}

impl Mission<Validated> {
    /// Turns a validated mission back into an editable draft. Validate it again
    /// before exporting.
    pub fn into_draft(self) -> Mission<Draft> {
        Mission { model: self.model, nonce: self.nonce, _state: PhantomData }
    }
}

impl<State> Mission<State> {
    /// Adds a group. Add at least one unit to it with `add_unit` before assigning
    /// its plan. Errors with `DuplicateCallsign` if the callsign is taken.
    pub fn add_group(&mut self, side: Side, callsign: &str) -> Result<GroupId, DuplicateCallsign>
    where
        State: Editable,
    {
        if self.model.group_index(callsign).is_some() {
            return Err(DuplicateCallsign { callsign: callsign.to_string() });
        }
        self.model.groups.push(core::Group {
            side,
            callsign: callsign.to_string(),
            units: Vec::new(),
            leader: None,
            plan: Vec::new(),
            plan_assigned: false,
        });
        Ok(GroupId { mission: self.nonce, index: self.model.groups.len() - 1 })
    }

    /// Adds a unit to `group`; it takes the group's side. `pos` is already checked,
    /// so this cannot fail. Keep the returned `UnitId` if you need it later (for
    /// `set_leader`).
    pub fn add_unit(&mut self, group: GroupId, class: UnitClass, label: &str, pos: Pos, rank: Rank) -> UnitId
    where
        State: Editable,
    {
        if group.mission != self.nonce {
            self.model.foreign_ids.push("GroupId");
            return UnitId { mission: self.nonce, index: usize::MAX };
        }
        match self.model.push_unit(group.index, class, label, pos.x(), pos.z(), rank) {
            Some(index) => UnitId { mission: self.nonce, index },
            None => {
                self.model.foreign_ids.push("GroupId");
                UnitId { mission: self.nonce, index: usize::MAX }
            }
        }
    }

    /// Makes `unit` the leader of `group`. Without this call the highest-ranked
    /// unit leads (the first listed on ties). Errors with `NotInGroup`.
    pub fn set_leader(&mut self, group: GroupId, unit: UnitId) -> Result<(), NotInGroup>
    where
        State: Editable,
    {
        if group.mission != self.nonce || unit.mission != self.nonce {
            return Err(NotInGroup);
        }
        let owner = self.model.units.get(unit.index).map(|u| u.group);
        let g = self.model.groups.get_mut(group.index).ok_or(NotInGroup)?;
        if owner != Some(group.index) {
            return Err(NotInGroup);
        }
        g.leader = Some(unit.index);
        Ok(())
    }

    /// Gives `group` its waypoint plan (a `Plan` in any state, or an `AnyPlan`).
    /// A plan is assigned once, after the group has units. Errors with
    /// `PlanError::EmptyGroup`, `WrongSide` (a `get_in` vehicle of another side)
    /// or `AlreadyAssigned`. Afterwards get waypoints with `Mission::waypoint`.
    pub fn assign_plan(&mut self, group: GroupId, plan: impl Into<AnyPlan>) -> Result<(), PlanError>
    where
        State: Editable,
    {
        let plan: AnyPlan = plan.into();
        if group.mission != self.nonce {
            return Err(PlanError::ForeignId);
        }
        let g = self.model.groups.get(group.index).ok_or(PlanError::ForeignId)?;
        let callsign = g.callsign.clone();
        if g.plan_assigned {
            return Err(PlanError::AlreadyAssigned { callsign });
        }
        if g.units.is_empty() {
            return Err(PlanError::EmptyGroup { callsign });
        }
        let mut wps = Vec::with_capacity(plan.len());
        for step in plan.steps() {
            let wp = match *step {
                Step::Move(p) => core::Wp::Move(p.x(), p.z()),
                Step::Sad(p) => core::Wp::Sad(p.x(), p.z()),
                Step::Hold(p) => core::Wp::Hold(p.x(), p.z()),
                Step::GetOut(p) => core::Wp::GetOut(p.x(), p.z()),
                Step::Cycle => core::Wp::Cycle,
                Step::GetIn(v) => {
                    if v.mission != self.nonce {
                        return Err(PlanError::ForeignId);
                    }
                    let vehicle_side = self
                        .model
                        .units
                        .get(v.index)
                        .and_then(|u| self.model.groups.get(u.group))
                        .map(|vg| vg.side);
                    if vehicle_side != Some(g.side) {
                        return Err(PlanError::WrongSide { callsign });
                    }
                    core::Wp::GetIn(v.index)
                }
            };
            wps.push(wp);
        }
        if let Some(g) = self.model.groups.get_mut(group.index) {
            g.plan = wps;
            g.plan_assigned = true;
        }
        Ok(())
    }

    /// Synchronises two waypoints: each waits for the other.
    pub fn sync_waypoints(&mut self, a: WaypointRef, b: WaypointRef)
    where
        State: Editable,
    {
        if a.mission != self.nonce || b.mission != self.nonce {
            self.model.foreign_ids.push("WaypointRef");
            return;
        }
        let at = |w: WaypointRef| core::WpAt { group: w.group, index: w.index };
        self.model.wp_syncs.push((at(a), at(b)));
    }

    /// Adds a trigger built with `TriggerBuilder` (an activation is required) and
    /// returns its id.
    pub fn add_trigger<A, R>(&mut self, trigger: TriggerBuilder<A, R>) -> TriggerId
    where
        State: Editable,
        A: ActivationSet,
    {
        let area = trigger.area;
        self.model.triggers.push(core::Trigger {
            cx: area.centre.x(),
            cz: area.centre.z(),
            a: area.a.get(),
            b: area.b.get(),
            angle: area.angle.get(),
            act: trigger.act,
            repeating: trigger.repeating,
            timer: trigger.timer.map(|t| t.0),
            effect: trigger.effect,
            syncs: Vec::new(),
        });
        TriggerId { mission: self.nonce, index: self.model.triggers.len() - 1 }
    }

    /// Synchronises a trigger with a waypoint: the waypoint waits for the trigger
    /// (and a trigger with `Activation::none()` fires when the waypoint is reached).
    pub fn sync_trigger(&mut self, trigger: TriggerId, waypoint: WaypointRef)
    where
        State: Editable,
    {
        if trigger.mission != self.nonce || waypoint.mission != self.nonce {
            self.model.foreign_ids.push("TriggerId/WaypointRef");
            return;
        }
        let at = core::WpAt { group: waypoint.group, index: waypoint.index };
        match self.model.triggers.get_mut(trigger.index) {
            Some(t) => t.syncs.push(at),
            None => self.model.foreign_ids.push("TriggerId"),
        }
    }

    /// Sets the free-text note written into the export.
    pub fn set_note(&mut self, note: &str)
    where
        State: Editable,
    {
        self.model.note = Some(note.to_string());
    }

    /// The group with this callsign, or `None`: handle the `None` case (the task
    /// says what to return), do not unwrap.
    pub fn group(&self, callsign: &str) -> Option<GroupId> {
        self.model.group_index(callsign).map(|index| GroupId { mission: self.nonce, index })
    }

    /// The first unit with this label, or `None`.
    pub fn unit(&self, label: &str) -> Option<UnitId> {
        self.model.unit_index(label).map(|index| UnitId { mission: self.nonce, index })
    }

    /// The first vehicle with this label, or `None` (no such label, or not a vehicle).
    pub fn vehicle(&self, label: &str) -> Option<VehicleId> {
        self.model.vehicle_index(label).map(|index| VehicleId { mission: self.nonce, index })
    }

    /// Waypoint `index` (0-based: the first waypoint is 0) of `group`'s assigned
    /// plan, or `None` if there is no such waypoint.
    pub fn waypoint(&self, group: GroupId, index: usize) -> Option<WaypointRef> {
        if group.mission != self.nonce {
            return None;
        }
        let g = self.model.groups.get(group.index)?;
        (index < g.plan.len()).then_some(WaypointRef { mission: self.nonce, group: group.index, index })
    }

    /// Exports the mission as `mbx` text. Only a `Mission<Validated>` has this:
    /// call `validate()` first and export the value it returns.
    pub fn export(&self) -> Exported
    where
        State: Exportable,
    {
        Exported { text: core::write(&self.model) }
    }
}

/// Maps a core violation to the guided variant's `Issue`.
fn issue(m: &core::Model, v: core::Violation) -> Issue {
    match v {
        core::Violation::EmptyGroup { group } => Issue::EmptyGroup { callsign: m.callsign(group).to_string() },
        core::Violation::ForeignId { what } => Issue::ForeignId { what },
        other => {
            let rule = match other {
                core::Violation::CycleNotLast { .. } | core::Violation::TooFewMoves { .. } => "R1",
                core::Violation::AfterHold { .. } => "R2",
                core::Violation::GetOutWithoutGetIn { .. } => "R3",
                core::Violation::UnknownVehicle { .. }
                | core::Violation::NotAVehicle { .. }
                | core::Violation::WrongSide { .. } => "R4",
                core::Violation::DanglingSync { .. } => "R5",
                core::Violation::TimerOrder { .. } => "R6",
                core::Violation::SameSide { .. } => "R7",
                core::Violation::RepeatingEnd { .. } => "R8",
                core::Violation::DuplicateCallsign { .. } | core::Violation::LeaderNotInGroup { .. } => "R9",
                core::Violation::OutOfMap { .. } => "R10",
                core::Violation::EmptyGroup { .. } | core::Violation::ForeignId { .. } => "R9",
            };
            Issue::Rule { rule, detail: format!("{other:?}") }
        }
    }
}
