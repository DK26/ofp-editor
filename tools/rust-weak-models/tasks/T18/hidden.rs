use mb_spec::t18::{Input, OrderIn};
use mb_spec::{Point, Rank::*, Refusal, UnitClass::*, UnitIn};

fn p(x: f64, z: f64) -> Point {
    Point::new(x, z)
}

fn with_orders(orders: Vec<OrderIn>) -> Input {
    Input {
        units: vec![
            UnitIn::new(Rifleman, "o1", 3000.0, 3000.0, Sergeant),
            UnitIn::new(Rifleman, "o2", 3004.0, 3000.0, Private),
            UnitIn::new(Truck, "truck1", 3010.0, 3000.0, Private),
        ],
        orders,
    }
}

fn board(label: &str) -> OrderIn {
    OrderIn::Board(label.into())
}

/// A full valid sequence maps order by order onto waypoints.
#[test]
fn nominal_full_sequence() {
    let input = with_orders(vec![
        OrderIn::Move(p(3100.0, 3000.0)),
        board("truck1"),
        OrderIn::Move(p(3500.0, 3300.0)),
        OrderIn::Dismount(p(3500.0, 3300.0)),
        OrderIn::Hunt(p(3600.0, 3400.0)),
        OrderIn::Loop,
    ]);
    let doc = mb_oracle::accept(&task::run(&input).expect("valid input refused"));
    assert_eq!(doc.kinds("Orders"), ["MOVE", "GET_IN", "MOVE", "GET_OUT", "SEEK_AND_DESTROY", "CYCLE"]);
    assert_eq!(doc.boarded_label("Orders", 1), "truck1");
}

/// An order after Hold is refused with InvalidSequence.
#[test]
fn trap_seq_hold_order_after_hold() {
    let input = with_orders(vec![OrderIn::Move(p(3100.0, 3000.0)), OrderIn::Hold(p(3200.0, 3000.0)), OrderIn::Move(p(3300.0, 3000.0))]);
    assert_eq!(task::run(&input), Err(Refusal::InvalidSequence));
}

/// An order after Loop is refused with InvalidSequence.
#[test]
fn trap_seq_cycle_order_after_loop() {
    let input = with_orders(vec![OrderIn::Move(p(3100.0, 3000.0)), OrderIn::Hunt(p(3200.0, 3000.0)), OrderIn::Loop, OrderIn::Move(p(3300.0, 3000.0))]);
    assert_eq!(task::run(&input), Err(Refusal::InvalidSequence));
}

/// A Loop after a single move is refused with InvalidSequence.
#[test]
fn trap_seq_cycle_loop_after_one_move() {
    let input = with_orders(vec![OrderIn::Move(p(3100.0, 3000.0)), OrderIn::Loop]);
    assert_eq!(task::run(&input), Err(Refusal::InvalidSequence));
}

/// Dismount without Board is refused with InvalidSequence.
#[test]
fn trap_seq_mount_dismount_without_board() {
    let input = with_orders(vec![OrderIn::Move(p(3100.0, 3000.0)), OrderIn::Dismount(p(3200.0, 3000.0))]);
    assert_eq!(task::run(&input), Err(Refusal::InvalidSequence));
}

/// A second Dismount after one Board is refused with InvalidSequence.
#[test]
fn trap_seq_mount_second_dismount() {
    let input = with_orders(vec![board("truck1"), OrderIn::Dismount(p(3200.0, 3000.0)), OrderIn::Dismount(p(3300.0, 3000.0))]);
    assert_eq!(task::run(&input), Err(Refusal::InvalidSequence));
}

/// Boarding a label that is not a vehicle is refused with UnknownVehicle.
#[test]
fn trap_err_handling_unknown_vehicle() {
    let input = with_orders(vec![OrderIn::Move(p(3100.0, 3000.0)), board("o2")]);
    assert_eq!(task::run(&input), Err(Refusal::UnknownVehicle));
}

/// The first bad order wins: an unknown vehicle before a sequence error.
#[test]
fn trap_err_handling_first_bad_order_wins() {
    let input = with_orders(vec![board("apc9"), OrderIn::Dismount(p(1.0, 1.0)), OrderIn::Dismount(p(1.0, 1.0))]);
    assert_eq!(task::run(&input), Err(Refusal::UnknownVehicle));
}

/// Within one order the sequence rule is checked before the label.
#[test]
fn trap_err_handling_sequence_before_label() {
    let input = with_orders(vec![OrderIn::Hold(p(3100.0, 3000.0)), board("apc9")]);
    assert_eq!(task::run(&input), Err(Refusal::InvalidSequence));
}
