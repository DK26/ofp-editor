use mb_oracle::near;
use mb_spec::t03::Input;
use mb_spec::{Point, Rank::*, UnitClass::*, UnitIn};

fn with_points(points: Vec<Point>) -> Input {
    Input {
        units: vec![
            UnitIn::new(Rifleman, "s1", 2500.0, 7000.0, Private),
            UnitIn::new(MachineGunner, "s2", 2505.0, 7000.0, Corporal),
        ],
        points,
    }
}

/// Four points: three MOVE waypoints then HOLD at the last point.
#[test]
fn nominal_moves_then_hold() {
    let pts = vec![
        Point::new(2600.0, 7100.0),
        Point::new(2700.0, 7200.0),
        Point::new(2800.0, 7300.0),
        Point::new(2900.0, 7400.0),
    ];
    let doc = mb_oracle::accept(&task::run(&with_points(pts)).expect("valid input refused"));
    assert_eq!(doc.group("Sentry").side, "RESISTANCE");
    assert_eq!(doc.kinds("Sentry"), ["MOVE", "MOVE", "MOVE", "HOLD"]);
    let h = doc.wp("Sentry", 3).pos.unwrap();
    assert!(near(h.0, 2900.0) && near(h.1, 7400.0));
    let m = doc.wp("Sentry", 1).pos.unwrap();
    assert!(near(m.0, 2700.0) && near(m.1, 7200.0));
}

/// A single point: only HOLD.
#[test]
fn edge_single_point_is_hold() {
    let doc = mb_oracle::accept(&task::run(&with_points(vec![Point::new(100.0, 200.0)])).expect("valid input refused"));
    assert_eq!(doc.kinds("Sentry"), ["HOLD"]);
}

/// Units are kept in order.
#[test]
fn nominal_units_kept() {
    let doc = mb_oracle::accept(&task::run(&with_points(vec![Point::new(1.0, 2.0), Point::new(3.0, 4.0)])).expect("valid input refused"));
    let labels: Vec<&str> = doc.group("Sentry").units.iter().map(|u| u.label.as_str()).collect();
    assert_eq!(labels, ["s1", "s2"]);
}
