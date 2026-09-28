use mb_oracle::near;
use mb_spec::p02::Input;
use mb_spec::{Point, Rank::*, Refusal, UnitClass::*, UnitIn};

fn base() -> Input {
    Input {
        units: vec![
            UnitIn::new(Rifleman, "g1", 7000.0, 2000.0, Private),
            UnitIn::new(MachineGunner, "g2", 7005.0, 2000.0, Sergeant),
        ],
        gate: Point::new(7200.0, 2100.0),
        post: Point::new(7250.0, 2150.0),
    }
}

/// MOVE to the gate followed by HOLD at the post, with the right positions.
#[test]
fn nominal_move_then_hold() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    assert_eq!(doc.kinds("Guard"), ["MOVE", "HOLD"]);
    let hold = doc.wp("Guard", 1).pos.expect("HOLD has a position");
    assert!(near(hold.0, 7250.0) && near(hold.1, 2150.0));
}

/// A gate beyond the east edge is refused with OutOfMap.
#[test]
fn trap_bounds_gate_off_map() {
    let mut input = base();
    input.gate = Point::new(12_900.0, 2100.0);
    assert_eq!(task::run(&input), Err(Refusal::OutOfMap));
}

/// A unit below the south edge is refused with OutOfMap.
#[test]
fn trap_bounds_unit_off_map() {
    let mut input = base();
    input.units[1].pos = Point::new(7000.0, -1.0);
    assert_eq!(task::run(&input), Err(Refusal::OutOfMap));
}

/// A post exactly on the map corner is still on the map.
#[test]
fn edge_post_on_corner() {
    let mut input = base();
    input.post = Point::new(12_800.0, 0.0);
    let doc = mb_oracle::accept(&task::run(&input).expect("valid input refused"));
    assert_eq!(doc.kinds("Guard"), ["MOVE", "HOLD"]);
}
