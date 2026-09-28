use mb_oracle::near;
use mb_spec::t04::Input;
use mb_spec::{Point, Rank::*, Refusal, UnitClass::*, UnitIn};

fn with_points(points: Vec<Point>) -> Input {
    Input {
        units: vec![
            UnitIn::new(Rifleman, "p1", 8000.0, 3000.0, Sergeant),
            UnitIn::new(Medic, "p2", 8004.0, 3000.0, Private),
        ],
        points,
    }
}

/// Three points: MOVE x3 then CYCLE, positions in order.
#[test]
fn nominal_loop_of_three() {
    let pts = vec![Point::new(8100.0, 3000.0), Point::new(8100.0, 3100.0), Point::new(8000.0, 3100.0)];
    let doc = mb_oracle::accept(&task::run(&with_points(pts)).expect("valid input refused"));
    assert_eq!(doc.kinds("Patrol"), ["MOVE", "MOVE", "MOVE", "CYCLE"]);
    let p = doc.wp("Patrol", 2).pos.unwrap();
    assert!(near(p.0, 8000.0) && near(p.1, 3100.0));
}

/// Exactly two points is the smallest valid loop.
#[test]
fn trap_seq_cycle_two_points_is_valid() {
    let pts = vec![Point::new(8100.0, 3000.0), Point::new(8200.0, 3000.0)];
    let doc = mb_oracle::accept(&task::run(&with_points(pts)).expect("valid input refused"));
    assert_eq!(doc.kinds("Patrol"), ["MOVE", "MOVE", "CYCLE"]);
}

/// One point is refused with TooFewWaypoints.
#[test]
fn trap_err_handling_one_point() {
    assert_eq!(task::run(&with_points(vec![Point::new(1.0, 1.0)])), Err(Refusal::TooFewWaypoints));
}

/// No points is refused with TooFewWaypoints.
#[test]
fn trap_err_handling_no_points() {
    assert_eq!(task::run(&with_points(vec![])), Err(Refusal::TooFewWaypoints));
}
