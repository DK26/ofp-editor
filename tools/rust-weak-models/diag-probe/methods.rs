//! Probe: which typestate method shapes let `#[diagnostic::on_unimplemented]`
//! reach the model? (a) bound in a method-level where clause, (b) inherent impl
//! only on the open state, (c) witness type required as an argument.
#![allow(dead_code)]

use std::marker::PhantomData;

pub struct Open;
pub struct Cycled;

#[diagnostic::on_unimplemented(
    message = "no waypoint can follow CYCLE: this plan was already closed by `.cycle()`",
    label = "this plan is `{Self}`, so it takes no more waypoints",
    note = "fix: add every waypoint first, then call `.cycle()` last"
)]
pub trait AcceptsWaypoints {}
impl AcceptsWaypoints for Open {}

pub struct PlanA<State> {
    n: u32,
    _s: PhantomData<State>,
}
impl<State> PlanA<State> {
    /// (a) Bound on the method, not on the impl block.
    pub fn move_to(self) -> Self
    where
        State: AcceptsWaypoints,
    {
        PlanA { n: self.n + 1, _s: PhantomData }
    }
}
impl PlanA<Open> {
    pub fn new() -> Self {
        PlanA { n: 0, _s: PhantomData }
    }
    pub fn cycle(self) -> PlanA<Cycled> {
        PlanA { n: self.n, _s: PhantomData }
    }
}

pub struct PlanB<State> {
    n: u32,
    _s: PhantomData<State>,
}
impl PlanB<Open> {
    pub fn new() -> Self {
        PlanB { n: 0, _s: PhantomData }
    }
    /// (b) Only the open state has `move_to`.
    pub fn move_to(self) -> Self {
        PlanB { n: self.n + 1, _s: PhantomData }
    }
    pub fn cycle(self) -> PlanB<Cycled> {
        PlanB { n: self.n, _s: PhantomData }
    }
}

// (c) Witness: a GroupRef can only come from Mission::group(id).
pub struct GroupId(u32);
pub struct GroupRef<'mission> {
    id: u32,
    _m: PhantomData<&'mission ()>,
}
pub struct Mission {
    groups: Vec<u32>,
}
impl Mission {
    /// Returns a proof that the group exists, or `None`.
    pub fn group(&self, id: GroupId) -> Option<GroupRef<'_>> {
        self.groups
            .iter()
            .find(|g| **g == id.0)
            .map(|g| GroupRef { id: *g, _m: PhantomData })
    }
}
pub struct Trigger;
impl Trigger {
    pub fn sync_to(self, _g: &GroupRef<'_>) -> Self {
        self
    }
}

pub fn misuse_a() {
    let _ = PlanA::new().move_to().move_to().cycle().move_to();
}
pub fn misuse_b() {
    let _ = PlanB::new().move_to().move_to().cycle().move_to();
}
pub fn misuse_c(m: &Mission) {
    // Model skips the existence check and passes the Option straight in.
    let g = m.group(GroupId(7));
    let _ = Trigger.sync_to(&g);
}
