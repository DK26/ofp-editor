//! T20: late addition.

use crate::{Ending, Point, Radio, UnitIn};

/// The trigger added late: radio channel, ending and countdown in seconds.
#[derive(Debug, Clone, PartialEq)]
pub struct LateTrigger {
    pub channel: Radio,
    pub ending: Ending,
    pub min_s: f64,
    pub mid_s: f64,
    pub max_s: f64,
}

/// The patrol team, its loop points (at least two) and the late trigger.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub units: Vec<UnitIn>,
    pub patrol: Vec<Point>,
    pub late: LateTrigger,
}
