//! T29: second wave.

use crate::{Point, Radio, UnitIn};

/// One wave: callsign, units (its vehicle is one of them) and the vehicle's label.
#[derive(Debug, Clone, PartialEq)]
pub struct WaveIn {
    pub callsign: String,
    pub units: Vec<UnitIn>,
    pub vehicle: String,
}

/// The two waves, their shared route, the release channel and the second wave's delay.
#[derive(Debug, Clone, PartialEq)]
pub struct Input {
    pub first: WaveIn,
    pub second: WaveIn,
    pub route: Vec<Point>,
    pub release: Radio,
    pub delay_s: f64,
}
