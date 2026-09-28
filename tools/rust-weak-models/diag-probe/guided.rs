//! Minimal sketch of the GUIDED variant's three core mechanisms, used only to
//! capture the exact rustc diagnostics a model would receive in the feedback
//! loop. Not the experiment library itself.
#![allow(dead_code)]

use std::marker::PhantomData;

mod sealed {
    pub trait Sealed {}
}

/// Mission state: not yet checked. Call `validate()` to get a `Mission<Validated>`.
pub struct Draft;
/// Mission state: every cross-reference was checked. Only this state can be exported.
pub struct Validated;

pub struct Mission<State> {
    groups: Vec<u32>,
    _state: PhantomData<State>,
}

#[derive(Debug)]
pub struct ValidationReport;

impl Mission<Draft> {
    pub fn new() -> Self {
        Mission { groups: Vec::new(), _state: PhantomData }
    }
    /// Checks the mission. On success returns the only exportable form.
    pub fn validate(self) -> Result<Mission<Validated>, ValidationReport> {
        Ok(Mission { groups: self.groups, _state: PhantomData })
    }
}

impl sealed::Sealed for Mission<Validated> {}

#[diagnostic::on_unimplemented(
    message = "`{Self}` cannot be exported: only a validated mission can be exported",
    label = "this mission has not been validated yet",
    note = "fix: call `let mission = mission.validate()?;` and export the `Mission<Validated>` it returns"
)]
pub trait Exportable: sealed::Sealed {}
impl Exportable for Mission<Validated> {}

pub fn export<M: Exportable>(_mission: &M) -> String {
    String::new()
}

// ── Waypoint plan typestate ────────────────────────────────────────────
pub struct Open;
pub struct Cycled;

#[diagnostic::on_unimplemented(
    message = "no waypoint can follow CYCLE: this plan was already closed by `.cycle()`",
    label = "`{Self}` plan is closed",
    note = "fix: add every waypoint first, then call `.cycle()` last"
)]
pub trait AcceptsWaypoints {}
impl AcceptsWaypoints for Open {}

pub struct Pos {
    pub x: f32,
    pub z: f32,
}

pub struct WaypointPlan<State> {
    points: Vec<(f32, f32)>,
    _state: PhantomData<State>,
}

#[derive(Debug)]
pub struct TooFewWaypoints;

impl WaypointPlan<Open> {
    pub fn new() -> Self {
        WaypointPlan { points: Vec::new(), _state: PhantomData }
    }
    pub fn cycle(self) -> Result<WaypointPlan<Cycled>, TooFewWaypoints> {
        Ok(WaypointPlan { points: self.points, _state: PhantomData })
    }
}

impl<State: AcceptsWaypoints> WaypointPlan<State> {
    pub fn move_to(mut self, p: Pos) -> Self {
        self.points.push((p.x, p.z));
        self
    }
}

// ── Misuse 1: export before validate ──────────────────────────────────
pub fn misuse_export() -> String {
    let m = Mission::new();
    export(&m)
}

// ── Misuse 2: waypoint after CYCLE ────────────────────────────────────
pub fn misuse_cycle() -> Result<(), TooFewWaypoints> {
    let plan = WaypointPlan::new()
        .move_to(Pos { x: 1.0, z: 2.0 })
        .move_to(Pos { x: 3.0, z: 4.0 })
        .cycle()?;
    let _plan = plan.move_to(Pos { x: 5.0, z: 6.0 });
    Ok(())
}

// ── Misuse 3: id newtype confusion ─────────────────────────────────────
#[derive(Clone, Copy)]
pub struct UnitId(u32);
#[derive(Clone, Copy)]
pub struct GroupId(u32);
pub fn leader_of(_g: GroupId) -> UnitId {
    UnitId(0)
}
pub fn misuse_ids(u: UnitId) -> UnitId {
    leader_of(u)
}
