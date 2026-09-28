use mb_oracle::{Doc, near};
use mb_spec::t22::{Input, PlacedIn};
use mb_spec::{Point, Rank::*, Refusal, UnitClass::*};

fn placed(label: &str, bearing_deg: f64, distance_km: f64) -> PlacedIn {
    PlacedIn { class: Rifleman, label: label.into(), rank: Private, bearing_deg, distance_km }
}

fn ring(units: Vec<PlacedIn>) -> Input {
    Input { anchor: Point::new(5000.0, 7000.0), units }
}

fn pos_of(doc: &Doc, label: &str) -> (f64, f64) {
    let (_, u) = doc.unit_by_label(label).unwrap_or_else(|| panic!("no unit {label}"));
    (u.x, u.z)
}

/// Bearing 0 is north (+z) and 90 is east (+x); distances in km become metres.
#[test]
fn trap_unit_measure_km_and_compass() {
    let doc = mb_oracle::accept(&task::run(&ring(vec![placed("n", 0.0, 1.0), placed("e", 90.0, 0.5)])).expect("valid input refused"));
    let n = pos_of(&doc, "n");
    let e = pos_of(&doc, "e");
    assert!(near(n.0, 5000.0) && near(n.1, 8000.0), "north unit at {n:?}");
    assert!(near(e.0, 5500.0) && near(e.1, 7000.0), "east unit at {e:?}");
}

/// Bearing 225 and 2 km: south-west by 1414.2 m on each axis (degrees, not radians).
#[test]
fn trap_unit_measure_degrees_southwest() {
    let doc = mb_oracle::accept(&task::run(&ring(vec![placed("sw", 225.0, 2.0)])).expect("valid input refused"));
    let sw = pos_of(&doc, "sw");
    assert!((sw.0 - 3585.8).abs() < 0.2 && (sw.1 - 5585.8).abs() < 0.2, "south-west unit at {sw:?}");
}

/// A unit that lands beyond the east edge is refused with OutOfMap.
#[test]
fn trap_bounds_off_map() {
    let input = ring(vec![placed("n", 0.0, 1.0), placed("far", 90.0, 8.0)]);
    assert_eq!(task::run(&input), Err(Refusal::OutOfMap));
}

/// Distance zero puts the unit on the anchor; class, rank and order are kept.
#[test]
fn edge_zero_distance() {
    let mut units = vec![placed("c", 45.0, 0.0), placed("s", 180.0, 0.25)];
    units[0].class = Officer;
    units[0].rank = Captain;
    let doc = mb_oracle::accept(&task::run(&ring(units)).expect("valid input refused"));
    let c = pos_of(&doc, "c");
    assert!(near(c.0, 5000.0) && near(c.1, 7000.0));
    let s = pos_of(&doc, "s");
    assert!(near(s.0, 5000.0) && near(s.1, 6750.0), "south unit at {s:?}");
    let g = doc.group("Ring");
    assert_eq!((g.units[0].class.as_str(), g.units[0].rank.as_str()), ("OFFICER", "CAPTAIN"));
}
