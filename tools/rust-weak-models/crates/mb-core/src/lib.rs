//! Shared mission model, rule checker (R1-R10) and `mbx` text writer.
//!
//! Both API variants (`mb-plain`, `mb-guided`) are thin layers over this crate, which
//! is what makes them functionally identical: the same model, the same rule
//! semantics and byte-identical exports for equivalent missions. The model never
//! sees this crate; its items are not part of either API listing.
//!
//! `mb-oracle` re-implements parsing and rule checking independently from the
//! exported text, so a bug here shows up as an oracle disagreement in the tests.
//!
//! No function here panics on any input: a library panic caused by model misuse would
//! be charged to the model and would differ between variants.

use std::fmt::Write as _;

pub use mb_spec::{Ending, Radio, Rank, Side, UnitClass};

/// Map edge length in metres; valid coordinates are `0.0..=MAP_SIZE` on both axes (R10).
pub const MAP_SIZE: f64 = 12_800.0;

/// True if the point lies on the map (R10). NaN is never on the map.
pub fn in_map(x: f64, z: f64) -> bool {
    (0.0..=MAP_SIZE).contains(&x) && (0.0..=MAP_SIZE).contains(&z)
}

/// Point at `bearing_deg` (clockwise from north, +z) and `distance_m` from (x, z).
pub fn offset(x: f64, z: f64, bearing_deg: f64, distance_m: f64) -> (f64, f64) {
    let rad = bearing_deg.to_radians();
    (x + distance_m * rad.sin(), z + distance_m * rad.cos())
}

/// One waypoint. Positions are metres; `GetIn` holds a unit index.
#[derive(Debug, Clone, PartialEq)]
pub enum Wp {
    Move(f64, f64),
    Sad(f64, f64),
    Hold(f64, f64),
    GetIn(usize),
    GetOut(f64, f64),
    Cycle,
}

/// Address of a waypoint: group index and 0-based waypoint index.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct WpAt {
    pub group: usize,
    pub index: usize,
}

/// Trigger activation.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Act {
    None,
    Present(Side),
    NotPresent(Side),
    DetectedBy { detector: Side, detected: Side },
    Radio(Radio),
}

/// Timer flavour of a trigger.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TimerKind {
    Countdown,
    Timeout,
}

/// Trigger timer in seconds.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Timer {
    pub kind: TimerKind,
    pub min: f64,
    pub mid: f64,
    pub max: f64,
}

/// What a trigger does when it fires.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Effect {
    None,
    End(Ending),
    Lose,
}

/// A unit; `group` is the owning group's index.
#[derive(Debug, Clone, PartialEq)]
pub struct Unit {
    pub group: usize,
    pub class: UnitClass,
    pub label: String,
    pub x: f64,
    pub z: f64,
    pub rank: Rank,
}

/// A group; `units` are unit indices in insertion order.
#[derive(Debug, Clone, PartialEq)]
pub struct Group {
    pub side: Side,
    pub callsign: String,
    pub units: Vec<usize>,
    pub leader: Option<usize>,
    pub plan: Vec<Wp>,
    /// Set once a whole plan was assigned (the guided variant assigns plans once).
    pub plan_assigned: bool,
}

/// A trigger with a rectangular area (centre, half sizes a and b, rotation angle).
#[derive(Debug, Clone, PartialEq)]
pub struct Trigger {
    pub cx: f64,
    pub cz: f64,
    pub a: f64,
    pub b: f64,
    pub angle: f64,
    pub act: Act,
    pub repeating: bool,
    pub timer: Option<Timer>,
    pub effect: Effect,
    pub syncs: Vec<WpAt>,
}

/// The whole mission.
#[derive(Debug, Clone, PartialEq, Default)]
pub struct Model {
    pub groups: Vec<Group>,
    pub units: Vec<Unit>,
    pub triggers: Vec<Trigger>,
    pub wp_syncs: Vec<(WpAt, WpAt)>,
    pub note: Option<String>,
    /// Uses of an id that belongs to a different mission value (guided variant only).
    pub foreign_ids: Vec<&'static str>,
}

/// One rule violation found by [`check`]. Indices refer to the model's vectors.
#[derive(Debug, Clone, PartialEq)]
pub enum Violation {
    /// R1: CYCLE is not the last waypoint.
    CycleNotLast { group: usize, index: usize },
    /// R1: CYCLE with fewer than two earlier MOVE / SEEK_AND_DESTROY waypoints.
    TooFewMoves { group: usize, moves: usize },
    /// R2: a waypoint follows HOLD.
    AfterHold { group: usize, index: usize },
    /// R3: GET_OUT without an open GET_IN before it.
    GetOutWithoutGetIn { group: usize, index: usize },
    /// R4: GET_IN names a unit index that does not exist.
    UnknownVehicle { group: usize, index: usize, unit: usize },
    /// R4: GET_IN names a unit that is not a vehicle.
    NotAVehicle { group: usize, index: usize, unit: usize },
    /// R4: GET_IN names a vehicle of another side.
    WrongSide { group: usize, index: usize, unit: usize },
    /// R5: a sync names a group or waypoint that does not exist.
    DanglingSync { group: usize, index: usize },
    /// R6: timer values out of order or negative.
    TimerOrder { trigger: usize },
    /// R7: DETECTED_BY with detector == detected.
    SameSide { trigger: usize, side: Side },
    /// R8: an END or LOSE trigger that repeats.
    RepeatingEnd { trigger: usize },
    /// R9: a group without units.
    EmptyGroup { group: usize },
    /// R9: a callsign used by an earlier group.
    DuplicateCallsign { group: usize },
    /// R10: a position outside the map.
    OutOfMap { x: f64, z: f64 },
    /// The explicit leader is not a unit of the group.
    LeaderNotInGroup { group: usize },
    /// An id from another mission value was used.
    ForeignId { what: &'static str },
}

impl Model {
    /// Callsign of group `g`, or `"?"` for an unknown index.
    pub fn callsign(&self, g: usize) -> &str {
        self.groups.get(g).map(|grp| grp.callsign.as_str()).unwrap_or("?")
    }

    /// Index of the group with this callsign.
    pub fn group_index(&self, callsign: &str) -> Option<usize> {
        self.groups.iter().position(|g| g.callsign == callsign)
    }

    /// Index of the first unit with this label.
    pub fn unit_index(&self, label: &str) -> Option<usize> {
        self.units.iter().position(|u| u.label == label)
    }

    /// Index of the first vehicle unit with this label.
    pub fn vehicle_index(&self, label: &str) -> Option<usize> {
        self.units.iter().position(|u| u.label == label && u.class.is_vehicle())
    }

    /// Adds a unit to group `g`; returns the unit index or `None` for a bad group.
    pub fn push_unit(&mut self, g: usize, class: UnitClass, label: &str, x: f64, z: f64, rank: Rank) -> Option<usize> {
        let index = self.units.len();
        let group = self.groups.get_mut(g)?;
        group.units.push(index);
        self.units.push(Unit { group: g, class, label: label.to_string(), x, z, rank });
        Some(index)
    }

    /// True if waypoint `at` exists.
    pub fn wp_exists(&self, at: WpAt) -> bool {
        self.groups.get(at.group).is_some_and(|g| at.index < g.plan.len())
    }
}

/// Leader of group `g`: the explicit leader, else the highest rank (first listed on ties).
pub fn leader_of(m: &Model, g: usize) -> Option<usize> {
    let group = m.groups.get(g)?;
    if let Some(l) = group.leader {
        return Some(l);
    }
    let mut best: Option<(usize, Rank)> = None;
    for &u in &group.units {
        let Some(unit) = m.units.get(u) else { continue };
        // Strictly greater keeps the first listed unit on ties.
        if best.is_none_or(|(_, r)| unit.rank > r) {
            best = Some((u, unit.rank));
        }
    }
    best.map(|(u, _)| u)
}

/// Checks rules R1-R10 (plus leader membership and foreign ids) and returns every
/// violation in a deterministic order: groups, syncs, triggers.
pub fn check(m: &Model) -> Vec<Violation> {
    let mut out = Vec::new();
    for what in &m.foreign_ids {
        out.push(Violation::ForeignId { what });
    }
    for (gi, g) in m.groups.iter().enumerate() {
        // ── R9: units and unique callsigns ──
        if g.units.is_empty() {
            out.push(Violation::EmptyGroup { group: gi });
        }
        if m.groups.iter().take(gi).any(|e| e.callsign == g.callsign) {
            out.push(Violation::DuplicateCallsign { group: gi });
        }
        if let Some(l) = g.leader {
            if !g.units.contains(&l) {
                out.push(Violation::LeaderNotInGroup { group: gi });
            }
        }
        // ── R10: unit positions ──
        for &u in &g.units {
            if let Some(unit) = m.units.get(u) {
                if !in_map(unit.x, unit.z) {
                    out.push(Violation::OutOfMap { x: unit.x, z: unit.z });
                }
            }
        }
        check_plan(m, gi, g, &mut out);
    }
    // ── R5: waypoint syncs ──
    for (a, b) in &m.wp_syncs {
        for at in [a, b] {
            if !m.wp_exists(*at) {
                out.push(Violation::DanglingSync { group: at.group, index: at.index });
            }
        }
    }
    for (ti, t) in m.triggers.iter().enumerate() {
        if !in_map(t.cx, t.cz) {
            out.push(Violation::OutOfMap { x: t.cx, z: t.cz });
        }
        // ── R6: timer order ──
        if let Some(tm) = t.timer {
            let ordered = tm.min <= tm.mid && tm.mid <= tm.max;
            let non_negative = tm.min >= 0.0 && tm.mid >= 0.0 && tm.max >= 0.0;
            if !(ordered && non_negative) {
                out.push(Violation::TimerOrder { trigger: ti });
            }
        }
        // ── R7: detector differs from detected ──
        if let Act::DetectedBy { detector, detected } = t.act {
            if detector == detected {
                out.push(Violation::SameSide { trigger: ti, side: detector });
            }
        }
        // ── R8: END and LOSE fire once ──
        if t.repeating && !matches!(t.effect, Effect::None) {
            out.push(Violation::RepeatingEnd { trigger: ti });
        }
        // ── R5: trigger syncs ──
        for at in &t.syncs {
            if !m.wp_exists(*at) {
                out.push(Violation::DanglingSync { group: at.group, index: at.index });
            }
        }
    }
    out
}

/// R1-R4 and R10 for one group's plan.
fn check_plan(m: &Model, gi: usize, g: &Group, out: &mut Vec<Violation>) {
    let last = g.plan.len().saturating_sub(1);
    let mut moves = 0usize;
    let mut mounted = false;
    let mut closed_by_hold = false;
    for (i, wp) in g.plan.iter().enumerate() {
        if closed_by_hold {
            out.push(Violation::AfterHold { group: gi, index: i });
        }
        match wp {
            Wp::Move(x, z) | Wp::Sad(x, z) => {
                moves += 1;
                if !in_map(*x, *z) {
                    out.push(Violation::OutOfMap { x: *x, z: *z });
                }
            }
            Wp::Hold(x, z) => {
                closed_by_hold = true;
                if !in_map(*x, *z) {
                    out.push(Violation::OutOfMap { x: *x, z: *z });
                }
            }
            Wp::GetIn(u) => {
                mounted = true;
                match m.units.get(*u) {
                    None => out.push(Violation::UnknownVehicle { group: gi, index: i, unit: *u }),
                    Some(v) if !v.class.is_vehicle() => {
                        out.push(Violation::NotAVehicle { group: gi, index: i, unit: *u })
                    }
                    Some(v) => {
                        let side = m.groups.get(v.group).map(|vg| vg.side);
                        if side != Some(g.side) {
                            out.push(Violation::WrongSide { group: gi, index: i, unit: *u });
                        }
                    }
                }
            }
            Wp::GetOut(x, z) => {
                if !mounted {
                    out.push(Violation::GetOutWithoutGetIn { group: gi, index: i });
                }
                mounted = false;
                if !in_map(*x, *z) {
                    out.push(Violation::OutOfMap { x: *x, z: *z });
                }
            }
            Wp::Cycle => {
                if i != last {
                    out.push(Violation::CycleNotLast { group: gi, index: i });
                }
                if moves < 2 {
                    out.push(Violation::TooFewMoves { group: gi, moves });
                }
            }
        }
    }
}

// ── mbx writer ──────────────────────────────────────────────────────────────

fn quote(s: &str) -> String {
    let mut q = String::with_capacity(s.len() + 2);
    q.push('"');
    for c in s.chars() {
        match c {
            '"' => q.push_str("\\\""),
            '\\' => q.push_str("\\\\"),
            '\n' => q.push_str("\\n"),
            other => q.push(other),
        }
    }
    q.push('"');
    q
}

/// Formats metres/seconds with one decimal; adding 0.0 turns -0.0 into 0.0.
fn num(v: f64) -> String {
    format!("{:.1}", v + 0.0)
}

pub fn side_code(s: Side) -> &'static str {
    match s {
        Side::West => "WEST",
        Side::East => "EAST",
        Side::Resistance => "RESISTANCE",
        Side::Civilian => "CIVILIAN",
    }
}

fn class_code(c: UnitClass) -> &'static str {
    match c {
        UnitClass::Rifleman => "RIFLEMAN",
        UnitClass::MachineGunner => "MACHINE_GUNNER",
        UnitClass::AtSoldier => "AT_SOLDIER",
        UnitClass::Medic => "MEDIC",
        UnitClass::Officer => "OFFICER",
        UnitClass::Truck => "TRUCK",
        UnitClass::Jeep => "JEEP",
        UnitClass::Apc => "APC",
    }
}

fn rank_code(r: Rank) -> &'static str {
    match r {
        Rank::Private => "PRIVATE",
        Rank::Corporal => "CORPORAL",
        Rank::Sergeant => "SERGEANT",
        Rank::Lieutenant => "LIEUTENANT",
        Rank::Captain => "CAPTAIN",
        Rank::Major => "MAJOR",
        Rank::Colonel => "COLONEL",
    }
}

fn radio_code(r: Radio) -> &'static str {
    match r {
        Radio::Alpha => "ALPHA",
        Radio::Bravo => "BRAVO",
        Radio::Charlie => "CHARLIE",
        Radio::Delta => "DELTA",
        Radio::Echo => "ECHO",
        Radio::Foxtrot => "FOXTROT",
        Radio::Golf => "GOLF",
        Radio::Hotel => "HOTEL",
        Radio::India => "INDIA",
        Radio::Juliet => "JULIET",
    }
}

fn ending_number(e: Ending) -> u8 {
    match e {
        Ending::One => 1,
        Ending::Two => 2,
        Ending::Three => 3,
        Ending::Four => 4,
        Ending::Five => 5,
        Ending::Six => 6,
    }
}

/// Writes the canonical `mbx 1` text. Deterministic: same model, same bytes.
///
/// Layout: `mbx 1`, optional `note`, then per group a `group` line, its `unit` lines
/// and its `wp` lines; then `sync` lines, `trigger` lines each followed by its
/// `tsync` lines; then `end`.
pub fn write(m: &Model) -> String {
    let mut out = String::from("mbx 1\n");
    if let Some(note) = &m.note {
        let _ = writeln!(out, "note {}", quote(note));
    }
    for (gi, g) in m.groups.iter().enumerate() {
        let leader = leader_of(m, gi).map(|u| format!("u{u}")).unwrap_or_else(|| "-".to_string());
        let _ = writeln!(out, "group g{gi} {} {} leader {leader}", quote(&g.callsign), side_code(g.side));
        for &ui in &g.units {
            if let Some(u) = m.units.get(ui) {
                let _ = writeln!(
                    out,
                    "unit u{ui} g{gi} {} {} {} {} {}",
                    class_code(u.class),
                    quote(&u.label),
                    num(u.x),
                    num(u.z),
                    rank_code(u.rank)
                );
            }
        }
        for (i, wp) in g.plan.iter().enumerate() {
            let body = match wp {
                Wp::Move(x, z) => format!("MOVE {} {}", num(*x), num(*z)),
                Wp::Sad(x, z) => format!("SEEK_AND_DESTROY {} {}", num(*x), num(*z)),
                Wp::Hold(x, z) => format!("HOLD {} {}", num(*x), num(*z)),
                Wp::GetIn(u) => format!("GET_IN u{u}"),
                Wp::GetOut(x, z) => format!("GET_OUT {} {}", num(*x), num(*z)),
                Wp::Cycle => "CYCLE".to_string(),
            };
            let _ = writeln!(out, "wp g{gi} {i} {body}");
        }
    }
    for (a, b) in &m.wp_syncs {
        let _ = writeln!(out, "sync g{} {} g{} {}", a.group, a.index, b.group, b.index);
    }
    for (ti, t) in m.triggers.iter().enumerate() {
        let act = match t.act {
            Act::None => "NONE".to_string(),
            Act::Present(s) => format!("PRESENT {}", side_code(s)),
            Act::NotPresent(s) => format!("NOT_PRESENT {}", side_code(s)),
            Act::DetectedBy { detector, detected } => {
                format!("DETECTED_BY {} {}", side_code(detector), side_code(detected))
            }
            Act::Radio(r) => format!("RADIO {}", radio_code(r)),
        };
        let timer = match t.timer {
            None => "NONE".to_string(),
            Some(tm) => {
                let kind = match tm.kind {
                    TimerKind::Countdown => "COUNTDOWN",
                    TimerKind::Timeout => "TIMEOUT",
                };
                format!("{kind} {} {} {}", num(tm.min), num(tm.mid), num(tm.max))
            }
        };
        let effect = match t.effect {
            Effect::None => "NONE".to_string(),
            Effect::End(e) => format!("END {}", ending_number(e)),
            Effect::Lose => "LOSE".to_string(),
        };
        let repeat = if t.repeating { "REPEATEDLY" } else { "ONCE" };
        let _ = writeln!(
            out,
            "trigger t{ti} area {} {} {} {} {} act {act} repeat {repeat} timer {timer} effect {effect}",
            num(t.cx),
            num(t.cz),
            num(t.a),
            num(t.b),
            num(t.angle)
        );
        for s in &t.syncs {
            let _ = writeln!(out, "tsync t{ti} g{} {}", s.group, s.index);
        }
    }
    out.push_str("end\n");
    out
}
