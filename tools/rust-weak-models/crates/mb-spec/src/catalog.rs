//! Closed catalogs shared by every task and by both library variants.

/// A side (faction). All units of a group share the group's side.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Side {
    West,
    East,
    Resistance,
    Civilian,
}

/// Unit class. `Truck`, `Jeep` and `Apc` are vehicles; the rest are soldiers.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum UnitClass {
    Rifleman,
    MachineGunner,
    AtSoldier,
    Medic,
    Officer,
    Truck,
    Jeep,
    Apc,
}

impl UnitClass {
    /// True for `Truck`, `Jeep` and `Apc`.
    pub fn is_vehicle(self) -> bool {
        matches!(self, UnitClass::Truck | UnitClass::Jeep | UnitClass::Apc)
    }
}

/// Rank, lowest first: `Private < Corporal < Sergeant < ... < Colonel`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Rank {
    Private,
    Corporal,
    Sergeant,
    Lieutenant,
    Captain,
    Major,
    Colonel,
}

/// Radio channel of a radio-activated trigger.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Radio {
    Alpha,
    Bravo,
    Charlie,
    Delta,
    Echo,
    Foxtrot,
    Golf,
    Hotel,
    India,
    Juliet,
}

/// Mission ending number of an END trigger (ending 1 to ending 6).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Ending {
    One,
    Two,
    Three,
    Four,
    Five,
    Six,
}

/// A map point in metres. `x` grows to the east, `z` grows to the north.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Point {
    pub x: f64,
    pub z: f64,
}

impl Point {
    /// Builds a point from metres.
    pub fn new(x: f64, z: f64) -> Point {
        Point { x, z }
    }
}

/// One unit as described by a brief.
#[derive(Debug, Clone, PartialEq)]
pub struct UnitIn {
    pub class: UnitClass,
    pub label: String,
    pub pos: Point,
    pub rank: Rank,
}

impl UnitIn {
    /// Convenience constructor used by tests.
    pub fn new(class: UnitClass, label: &str, x: f64, z: f64, rank: Rank) -> UnitIn {
        UnitIn { class, label: label.to_string(), pos: Point { x, z }, rank }
    }
}
