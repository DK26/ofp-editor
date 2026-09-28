//! Mission builder: create groups, units, waypoint plans and triggers, validate
//! the mission and export it as `mbx` text.
//!
//! Workflow: `Mission::new()` -> `add_group` -> `add_unit` (every group needs at
//! least one unit) -> build a `Plan` and `assign_plan` -> `add_trigger` and syncs ->
//! `validate()` -> `export()` on the `Mission<Validated>` that `validate` returned.
//! Ids (`GroupId`, `UnitId`, `VehicleId`, `WaypointRef`, `TriggerId`) come only
//! from `add_*` calls or `Option`-returning lookups; there is no numeric
//! constructor. Positions are `Pos`, durations `Seconds`, distances `Metres`,
//! angles `Degrees`.

// Implementation notes (not part of the listing): every type is a thin typed layer
// over the hidden `mb-core` model shared with the PLAIN variant. Each sequence rule
// that has a fix to teach is a method-level `where State: Trait` bound on a trait
// carrying `#[diagnostic::on_unimplemented]`; rustc 1.98 then reports E0277 with the
// custom text (an impl-block bound or an inherent impl on one state would give E0599
// and drop the text; see the diag-probe notes in design.json).

mod ids;
mod measure;
mod mission;
mod plan;
mod trigger;

pub use ids::{GroupId, TriggerId, UnitId, VehicleId, WaypointRef};
pub use mb_spec::{Ending, Radio, Rank, Side, UnitClass};
pub use measure::{Degrees, Metres, OutOfMap, Pos, Seconds};
pub use mission::{
    Draft, DuplicateCallsign, Editable, Exportable, Exported, Issue, Mission, NotInGroup, PlanError, Validated,
    ValidationReport,
};
pub use plan::{AcceptsWaypoints, AnyPlan, Closed, IsMounted, Mounted, Open, Order, Plan, SequenceError, TooFewWaypoints};
pub use trigger::{
    Activation, ActivationSet, Area, Ends, FiresOnce, MayRepeat, NeedsActivation, Once, Ready, Repeating, SameSide, Timer,
    TimerOrder, TriggerBuilder,
};

/// Map edge length in metres; valid coordinates are `0.0..=MAP_SIZE` on both axes.
pub const MAP_SIZE: f64 = 12_800.0;

/// Seals the state traits so only this crate can implement them.
mod sealed {
    pub trait Sealed {}
}
