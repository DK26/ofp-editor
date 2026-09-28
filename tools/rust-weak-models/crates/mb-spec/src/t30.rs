//! T30: one bad element.

use crate::{Ending, Point, Radio, Side, UnitIn};

/// A group of the brief.
#[derive(Debug, Clone, PartialEq)]
pub struct GroupIn {
    pub callsign: String,
    pub side: Side,
    pub units: Vec<UnitIn>,
}

/// One order.
#[derive(Debug, Clone, PartialEq)]
pub enum OrderIn {
    Move(Point),
    /// Seek and destroy at the point.
    Hunt(Point),
    /// Board the vehicle with this label.
    Board(String),
    /// Leave the vehicle at the point.
    Dismount(Point),
    Hold(Point),
    /// Repeat from the first waypoint.
    Loop,
}

/// The orders of the group with this callsign.
#[derive(Debug, Clone, PartialEq)]
pub struct PlanIn {
    pub callsign: String,
    pub orders: Vec<OrderIn>,
}

/// Trigger condition.
#[derive(Debug, Clone, PartialEq)]
pub enum ActIn {
    Radio(Radio),
    Present(Side),
    NotPresent(Side),
    /// `watched` detected by `watcher`.
    DetectedBy { watcher: Side, watched: Side },
}

/// Trigger effect.
#[derive(Debug, Clone, PartialEq)]
pub enum EffectIn {
    None,
    End(Ending),
    Lose,
}

/// One trigger of the brief.
#[derive(Debug, Clone, PartialEq)]
pub struct TriggerIn {
    pub centre: Point,
    /// Half the side length of the square area, in metres.
    pub half_m: f64,
    pub act: ActIn,
    pub repeating: bool,
    /// Countdown in seconds: min, typical, max.
    pub countdown_s: Option<[f64; 3]>,
    pub effect: EffectIn,
    /// Callsign and waypoint number (1 is the first waypoint) to synchronise with.
    pub sync: Option<(String, usize)>,
}

/// The brief: groups, plans and triggers, each in order.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub groups: Vec<GroupIn>,
    pub plans: Vec<PlanIn>,
    pub triggers: Vec<TriggerIn>,
}
