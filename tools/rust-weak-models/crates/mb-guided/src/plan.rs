//! Waypoint plans as a typestate (`Plan<Open | Mounted | Closed>`) plus the
//! runtime-checked `AnyPlan` for plans built from data.

use std::fmt;
use std::marker::PhantomData;

use crate::ids::VehicleId;
use crate::measure::Pos;
use crate::sealed::Sealed;

/// Plan state: accepts waypoints; the units are on foot.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Open;
/// Plan state: accepts waypoints; the units are aboard a vehicle (after `get_in`).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Mounted;
/// Plan state: closed by `hold` or `cycle`; takes no more waypoints.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Closed;

impl Sealed for Open {}
impl Sealed for Mounted {}
impl Sealed for Closed {}

/// Plan states that accept more waypoints: `Open` and `Mounted`.
#[diagnostic::on_unimplemented(
    message = "this plan is `{Self}`: no waypoint can be added after `hold()` or `cycle()`",
    label = "the plan was already closed here",
    note = "fix: add every waypoint first, then close the plan last with `.hold(pos)` or `.cycle()?`",
    note = "building a plan from runtime data? use `AnyPlan::apply`, which returns `Err(SequenceError)` instead"
)]
pub trait AcceptsWaypoints: Sealed {}
impl AcceptsWaypoints for Open {}
impl AcceptsWaypoints for Mounted {}

/// Plan states where the units are aboard a vehicle: `Mounted`.
#[diagnostic::on_unimplemented(
    message = "`get_out` needs a mounted plan, but this plan is `{Self}`",
    label = "no `get_in` before this `get_out`",
    note = "fix: call `.get_in(vehicle)` earlier in the same plan, then `.get_out(pos)`"
)]
pub trait IsMounted: Sealed {}
impl IsMounted for Mounted {}

/// One planned waypoint (internal form).
#[derive(Debug, Clone, Copy, PartialEq)]
pub(crate) enum Step {
    Move(Pos),
    Sad(Pos),
    Hold(Pos),
    GetIn(VehicleId),
    GetOut(Pos),
    Cycle,
}

/// Error: `cycle()` needs at least two earlier `move_to` / `seek_and_destroy`
/// waypoints in the plan (rule R1).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct TooFewWaypoints {
    pub moves: usize,
}

impl fmt::Display for TooFewWaypoints {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "CYCLE needs 2 moves before it, found {}", self.moves)
    }
}

impl std::error::Error for TooFewWaypoints {}

/// The waypoint plan of one group, built in order. Start with `Plan::new()`, chain
/// waypoints, optionally close it with `hold` or `cycle`, then pass it to
/// `Mission::assign_plan`. Each call consumes the plan and returns the next one.
#[derive(Debug, Clone, PartialEq)]
pub struct Plan<State = Open> {
    pub(crate) steps: Vec<Step>,
    moves: usize,
    _state: PhantomData<State>,
}

impl Plan<Open> {
    /// An empty plan; the units start on foot.
    pub fn new() -> Plan<Open> {
        Plan { steps: Vec::new(), moves: 0, _state: PhantomData }
    }
}

impl Default for Plan<Open> {
    fn default() -> Self {
        Plan::new()
    }
}

impl<State> Plan<State> {
    fn push<Next>(mut self, step: Step) -> Plan<Next> {
        if matches!(step, Step::Move(_) | Step::Sad(_)) {
            self.moves += 1;
        }
        self.steps.push(step);
        Plan { steps: self.steps, moves: self.moves, _state: PhantomData }
    }

    /// Adds a MOVE waypoint.
    pub fn move_to(self, pos: Pos) -> Plan<State>
    where
        State: AcceptsWaypoints,
    {
        self.push(Step::Move(pos))
    }

    /// Adds a SEEK_AND_DESTROY waypoint (move there and engage).
    pub fn seek_and_destroy(self, pos: Pos) -> Plan<State>
    where
        State: AcceptsWaypoints,
    {
        self.push(Step::Sad(pos))
    }

    /// Adds a GET_IN waypoint: the units board `vehicle`, which must belong to the
    /// same side. Returns a `Plan<Mounted>`; call `get_out` later to dismount.
    pub fn get_in(self, vehicle: VehicleId) -> Plan<Mounted>
    where
        State: AcceptsWaypoints,
    {
        self.push(Step::GetIn(vehicle))
    }

    /// Adds a GET_OUT waypoint at `pos`. Only a `Plan<Mounted>` (after `get_in`) has it.
    pub fn get_out(self, pos: Pos) -> Plan<Open>
    where
        State: IsMounted,
    {
        self.push(Step::GetOut(pos))
    }

    /// Adds a HOLD waypoint and closes the plan: HOLD must be the last waypoint.
    pub fn hold(self, pos: Pos) -> Plan<Closed>
    where
        State: AcceptsWaypoints,
    {
        self.push(Step::Hold(pos))
    }

    /// Adds CYCLE (repeat from the first waypoint) and closes the plan: call it
    /// after every other waypoint.
    ///
    /// Errors with `TooFewWaypoints` if fewer than two `move_to` /
    /// `seek_and_destroy` waypoints come before it; propagate it with `?` or map it.
    pub fn cycle(self) -> Result<Plan<Closed>, TooFewWaypoints>
    where
        State: AcceptsWaypoints,
    {
        if self.moves < 2 {
            return Err(TooFewWaypoints { moves: self.moves });
        }
        Ok(self.push(Step::Cycle))
    }

    /// Number of waypoints so far.
    pub fn len(&self) -> usize {
        self.steps.len()
    }

    /// True if the plan has no waypoints.
    pub fn is_empty(&self) -> bool {
        self.steps.is_empty()
    }
}

/// One waypoint order for [`AnyPlan::apply`].
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Order {
    Move(Pos),
    SeekAndDestroy(Pos),
    GetIn(VehicleId),
    GetOut(Pos),
    Hold(Pos),
    Cycle,
}

/// Error from [`AnyPlan::apply`]: the order breaks a waypoint sequence rule.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SequenceError {
    /// The plan was already closed by HOLD or CYCLE (rules R1, R2).
    Closed,
    /// GET_OUT without a GET_IN before it (rule R3).
    NotMounted,
    /// CYCLE with fewer than two moves before it (rule R1).
    TooFewWaypoints,
}

impl fmt::Display for SequenceError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let text = match self {
            SequenceError::Closed => "the plan is closed by HOLD or CYCLE",
            SequenceError::NotMounted => "GET_OUT without GET_IN",
            SequenceError::TooFewWaypoints => "CYCLE needs 2 moves before it",
        };
        f.write_str(text)
    }
}

impl std::error::Error for SequenceError {}

/// A plan in any state. Use it when the waypoints come from runtime data (a list
/// of orders) or when plans are kept in a collection; for fixed sequences written
/// in code prefer `Plan`. Every `Plan<S>` converts with `AnyPlan::from(plan)` or
/// `.into()`, and `Mission::assign_plan` accepts both.
#[derive(Debug, Clone, PartialEq)]
pub enum AnyPlan {
    Open(Plan<Open>),
    Mounted(Plan<Mounted>),
    Closed(Plan<Closed>),
}

impl Default for AnyPlan {
    fn default() -> Self {
        AnyPlan::new()
    }
}

impl AnyPlan {
    /// An empty open plan.
    pub fn new() -> AnyPlan {
        AnyPlan::Open(Plan::new())
    }

    /// Applies one order and returns the updated plan, or the `SequenceError` that
    /// the order would cause. The plan is consumed either way.
    pub fn apply(self, order: Order) -> Result<AnyPlan, SequenceError> {
        match self {
            AnyPlan::Closed(_) => Err(SequenceError::Closed),
            AnyPlan::Open(p) => match order {
                Order::Move(pos) => Ok(AnyPlan::Open(p.move_to(pos))),
                Order::SeekAndDestroy(pos) => Ok(AnyPlan::Open(p.seek_and_destroy(pos))),
                Order::GetIn(v) => Ok(AnyPlan::Mounted(p.get_in(v))),
                Order::GetOut(_) => Err(SequenceError::NotMounted),
                Order::Hold(pos) => Ok(AnyPlan::Closed(p.hold(pos))),
                Order::Cycle => p.cycle().map(AnyPlan::Closed).map_err(|_| SequenceError::TooFewWaypoints),
            },
            AnyPlan::Mounted(p) => match order {
                Order::Move(pos) => Ok(AnyPlan::Mounted(p.move_to(pos))),
                Order::SeekAndDestroy(pos) => Ok(AnyPlan::Mounted(p.seek_and_destroy(pos))),
                Order::GetIn(v) => Ok(AnyPlan::Mounted(p.get_in(v))),
                Order::GetOut(pos) => Ok(AnyPlan::Open(p.get_out(pos))),
                Order::Hold(pos) => Ok(AnyPlan::Closed(p.hold(pos))),
                Order::Cycle => p.cycle().map(AnyPlan::Closed).map_err(|_| SequenceError::TooFewWaypoints),
            },
        }
    }

    /// True once HOLD or CYCLE closed the plan.
    pub fn is_closed(&self) -> bool {
        matches!(self, AnyPlan::Closed(_))
    }

    /// Number of waypoints so far.
    pub fn len(&self) -> usize {
        self.steps().len()
    }

    /// True if the plan has no waypoints.
    pub fn is_empty(&self) -> bool {
        self.steps().is_empty()
    }

    pub(crate) fn steps(&self) -> &[Step] {
        match self {
            AnyPlan::Open(p) => &p.steps,
            AnyPlan::Mounted(p) => &p.steps,
            AnyPlan::Closed(p) => &p.steps,
        }
    }
}

impl From<Plan<Open>> for AnyPlan {
    fn from(plan: Plan<Open>) -> AnyPlan {
        AnyPlan::Open(plan)
    }
}

impl From<Plan<Mounted>> for AnyPlan {
    fn from(plan: Plan<Mounted>) -> AnyPlan {
        AnyPlan::Mounted(plan)
    }
}

impl From<Plan<Closed>> for AnyPlan {
    fn from(plan: Plan<Closed>) -> AnyPlan {
        AnyPlan::Closed(plan)
    }
}
