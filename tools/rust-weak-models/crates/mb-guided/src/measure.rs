//! Unit-carrying newtypes and the checked map position.

use std::fmt;

/// A duration. Build it from the unit the brief uses: `Seconds::new(90.0)` or
/// `Seconds::from_minutes(1.5)`.
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd)]
pub struct Seconds(f64);

impl Seconds {
    /// A duration given in seconds.
    pub fn new(seconds: f64) -> Seconds {
        Seconds(seconds)
    }

    /// A duration given in minutes (1 minute = 60 seconds).
    pub fn from_minutes(minutes: f64) -> Seconds {
        Seconds(minutes * 60.0)
    }

    /// The value in seconds.
    pub fn get(self) -> f64 {
        self.0
    }
}

/// A distance. Build it from the unit the brief uses: `Metres::new(250.0)` or
/// `Metres::from_km(1.2)`.
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd)]
pub struct Metres(f64);

impl Metres {
    /// A distance given in metres.
    pub fn new(metres: f64) -> Metres {
        Metres(metres)
    }

    /// A distance given in kilometres (1 km = 1000 m).
    pub fn from_km(km: f64) -> Metres {
        Metres(km * 1000.0)
    }

    /// The value in metres.
    pub fn get(self) -> f64 {
        self.0
    }
}

/// An angle in degrees (bearings are clockwise from north).
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd)]
pub struct Degrees(f64);

impl Degrees {
    /// An angle given in degrees.
    pub fn new(degrees: f64) -> Degrees {
        Degrees(degrees)
    }

    /// The value in degrees.
    pub fn get(self) -> f64 {
        self.0
    }
}

/// Error: the position is outside the map (`0..=12800` m on both axes, rule R10).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct OutOfMap {
    pub x: f64,
    pub z: f64,
}

impl fmt::Display for OutOfMap {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "position ({}, {}) is outside the map", self.x, self.z)
    }
}

impl std::error::Error for OutOfMap {}

/// A position on the map in metres. Only `Pos::new` and `Pos::offset` create one,
/// so every `Pos` is on the map.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Pos {
    x: f64,
    z: f64,
}

impl Pos {
    /// Checks that `(x, z)` metres lies on the map. Handle the error with `?` or
    /// `map_err` (the task says what to return); never unwrap it.
    pub fn new(x: f64, z: f64) -> Result<Pos, OutOfMap> {
        if mb_core::in_map(x, z) { Ok(Pos { x, z }) } else { Err(OutOfMap { x, z }) }
    }

    /// Crate-internal constructor for positions known to be on the map.
    pub(crate) fn on_map_unchecked(x: f64, z: f64) -> Pos {
        Pos { x, z }
    }

    /// East coordinate in metres.
    pub fn x(self) -> f64 {
        self.x
    }

    /// North coordinate in metres.
    pub fn z(self) -> f64 {
        self.z
    }

    /// The position `distance` away along `bearing` (clockwise from north). Build a
    /// distance given in km with `Metres::from_km`. Fails if the result is off the map.
    pub fn offset(self, bearing: Degrees, distance: Metres) -> Result<Pos, OutOfMap> {
        let (x, z) = mb_core::offset(self.x, self.z, bearing.get(), distance.get());
        Pos::new(x, z)
    }
}
