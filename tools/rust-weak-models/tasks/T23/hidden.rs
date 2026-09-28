use mb_oracle::near;
use mb_spec::t23::{ClearIn, Input, OrderIn};
use mb_spec::{Point, Rank::*, Refusal, Side, UnitClass::*, UnitIn};

fn group(callsign: &str, x: f64, prior: Vec<OrderIn>) -> ClearIn {
    ClearIn {
        callsign: callsign.into(),
        side: Side::West,
        units: vec![
            UnitIn::new(Rifleman, &format!("{callsign}-1"), x, 2000.0, Sergeant),
            UnitIn::new(Truck, &format!("{callsign}-truck"), x + 10.0, 2000.0, Private),
        ],
        prior,
        entry: Point::new(x + 500.0, 2500.0),
        target: Point::new(x + 700.0, 2700.0),
    }
}

fn three() -> Input {
    Input {
        groups: vec![
            group("Alpha", 1000.0, vec![]),
            group("Bravo", 3000.0, vec![OrderIn::Move(Point::new(3100.0, 2000.0)), OrderIn::Board("Bravo-truck".into())]),
            group("Charlie", 5000.0, vec![OrderIn::Hunt(Point::new(5100.0, 2000.0))]),
        ],
    }
}

/// Every group ends with MOVE entry, SEEK_AND_DESTROY target, MOVE entry.
#[test]
fn nominal_sequence_appended() {
    let doc = mb_oracle::accept(&task::run(&three()).expect("valid input refused"));
    assert_eq!(doc.kinds("Alpha"), ["MOVE", "SEEK_AND_DESTROY", "MOVE"]);
    assert_eq!(doc.kinds("Charlie"), ["SEEK_AND_DESTROY", "MOVE", "SEEK_AND_DESTROY", "MOVE"]);
    let t = doc.wp("Alpha", 1).pos.unwrap();
    assert!(near(t.0, 1700.0) && near(t.1, 2700.0));
    let back = doc.wp("Alpha", 2).pos.unwrap();
    assert!(near(back.0, 1500.0) && near(back.1, 2500.0));
}

/// A mounted group stays aboard: no GET_OUT is added.
#[test]
fn nominal_mounted_group_stays_aboard() {
    let doc = mb_oracle::accept(&task::run(&three()).expect("valid input refused"));
    assert_eq!(doc.kinds("Bravo"), ["MOVE", "GET_IN", "MOVE", "SEEK_AND_DESTROY", "MOVE"]);
    assert_eq!(doc.boarded_label("Bravo", 1), "Bravo-truck");
}

/// A group whose prior orders end with Hold is refused with InvalidSequence.
#[test]
fn trap_seq_hold_prior_hold() {
    let mut input = three();
    input.groups[2].prior.push(OrderIn::Hold(Point::new(5200.0, 2000.0)));
    assert_eq!(task::run(&input), Err(Refusal::InvalidSequence));
}

/// A group whose prior orders end with Loop is refused with InvalidSequence.
#[test]
fn trap_seq_cycle_prior_loop() {
    let mut input = three();
    input.groups[0].prior = vec![OrderIn::Move(Point::new(1100.0, 2000.0)), OrderIn::Move(Point::new(1200.0, 2000.0)), OrderIn::Loop];
    assert_eq!(task::run(&input), Err(Refusal::InvalidSequence));
}

/// A group that boarded and dismounted again is on foot and gets the sequence.
#[test]
fn trap_err_handling_dismounted_group() {
    let mut input = three();
    input.groups[1].prior.push(OrderIn::Dismount(Point::new(3300.0, 2200.0)));
    let doc = mb_oracle::accept(&task::run(&input).expect("valid input refused"));
    assert_eq!(doc.kinds("Bravo"), ["MOVE", "GET_IN", "GET_OUT", "MOVE", "SEEK_AND_DESTROY", "MOVE"]);
}
