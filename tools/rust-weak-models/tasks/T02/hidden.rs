use mb_oracle::near;
use mb_spec::t02::Input;
use mb_spec::{Point, Rank::*, Refusal, UnitClass::*, UnitIn};

fn base() -> Input {
    Input {
        units: vec![
            UnitIn::new(AtSoldier, "e1", 4000.0, 11000.0, Sergeant),
            UnitIn::new(Rifleman, "e2", 4004.0, 11000.0, Private),
        ],
        first: Point::new(4300.0, 11200.0),
        second: Point::new(4700.0, 11600.0),
    }
}

/// Two MOVE waypoints in brief order, East side, both units kept.
#[test]
fn nominal_two_moves() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    assert_eq!(doc.group("Team").side, "EAST");
    assert_eq!(doc.group("Team").units.len(), 2);
    assert_eq!(doc.kinds("Team"), ["MOVE", "MOVE"]);
    let a = doc.wp("Team", 0).pos.unwrap();
    let b = doc.wp("Team", 1).pos.unwrap();
    assert!(near(a.0, 4300.0) && near(a.1, 11200.0));
    assert!(near(b.0, 4700.0) && near(b.1, 11600.0));
}

/// A second point beyond the north edge is refused with OutOfMap.
#[test]
fn trap_bounds_second_point_off_map() {
    let mut input = base();
    input.second = Point::new(4700.0, 12_800.5);
    assert_eq!(task::run(&input), Err(Refusal::OutOfMap));
}

/// A first point with a negative coordinate is refused with OutOfMap.
#[test]
fn trap_bounds_first_point_off_map() {
    let mut input = base();
    input.first = Point::new(-10.0, 11200.0);
    assert_eq!(task::run(&input), Err(Refusal::OutOfMap));
}

/// A unit off the map is refused with OutOfMap.
#[test]
fn trap_bounds_unit_off_map() {
    let mut input = base();
    input.units[0].pos = Point::new(13_000.0, 11000.0);
    assert_eq!(task::run(&input), Err(Refusal::OutOfMap));
}

/// Points exactly on the map edge are valid.
#[test]
fn edge_points_on_edge() {
    let mut input = base();
    input.first = Point::new(0.0, 12_800.0);
    input.second = Point::new(12_800.0, 0.0);
    let doc = mb_oracle::accept(&task::run(&input).expect("valid input refused"));
    assert_eq!(doc.kinds("Team"), ["MOVE", "MOVE"]);
}
