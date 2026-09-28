use mb_oracle::{Doc, near};
use mb_spec::t07::Input;
use mb_spec::{Point, Rank::*, UnitClass::*, UnitIn};

fn base() -> Input {
    Input {
        units: vec![
            UnitIn::new(Rifleman, "r1", 7000.0, 7000.0, Sergeant),
            UnitIn::new(Rifleman, "r2", 7004.0, 7000.0, Private),
        ],
        a: Point::new(7200.0, 7000.0),
        b: Point::new(7200.0, 7300.0),
        c: Point::new(7000.0, 7300.0),
        depot: Point::new(6800.0, 7150.0),
    }
}

fn move_points(doc: &Doc) -> Vec<(f64, f64)> {
    doc.group("Rover").wps.iter().filter(|w| w.kind == "MOVE").map(|w| w.pos.unwrap()).collect()
}

fn index_of(points: &[(f64, f64)], p: Point) -> Option<usize> {
    points.iter().position(|q| near(q.0, p.x) && near(q.1, p.z))
}

/// The loop is valid: CYCLE is the last waypoint (nothing follows it).
#[test]
fn trap_seq_cycle_is_last() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    let kinds = doc.kinds("Rover");
    assert_eq!(kinds.last().map(String::as_str), Some("CYCLE"), "{kinds:?}");
    assert_eq!(kinds.iter().filter(|k| *k == "CYCLE").count(), 1);
}

/// The depot is one of the loop's MOVE waypoints.
#[test]
fn trap_seq_cycle_depot_inside_loop() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    let pts = move_points(&doc);
    assert_eq!(pts.len(), 4, "{pts:?}");
    assert!(index_of(&pts, base().depot).is_some(), "depot missing from the loop: {pts:?}");
}

/// A, B and C keep their order.
#[test]
fn nominal_abc_in_order() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    let pts = move_points(&doc);
    let (a, b, c) = (index_of(&pts, base().a), index_of(&pts, base().b), index_of(&pts, base().c));
    assert!(a.is_some() && b.is_some() && c.is_some(), "{pts:?}");
    assert!(a < b && b < c, "order {a:?} {b:?} {c:?}");
}

/// Units are kept, side West.
#[test]
fn nominal_units() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    assert_eq!(doc.group("Rover").side, "WEST");
    assert_eq!(doc.group("Rover").units.len(), 2);
}
