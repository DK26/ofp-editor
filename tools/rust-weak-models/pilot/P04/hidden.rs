use mb_oracle::near;
use mb_spec::p04::Input;
use mb_spec::{Point, Rank::*, Refusal, UnitClass::*, UnitIn};

fn base(ride: &str) -> Input {
    Input {
        units: vec![
            UnitIn::new(Rifleman, "r1", 6000.0, 6000.0, Sergeant),
            UnitIn::new(Truck, "truck1", 6010.0, 6000.0, Private),
            UnitIn::new(Rifleman, "r2", 6002.0, 6000.0, Private),
            UnitIn::new(Jeep, "jeep1", 6020.0, 6000.0, Private),
        ],
        ride: ride.to_string(),
        destination: Point::new(6800.0, 6400.0),
    }
}

/// GET_IN the named vehicle, MOVE to the destination, GET_OUT there.
#[test]
fn nominal_board_move_dismount() {
    let doc = mb_oracle::accept(&task::run(&base("jeep1")).expect("valid input refused"));
    assert_eq!(doc.kinds("Taxi"), ["GET_IN", "MOVE", "GET_OUT"]);
    assert_eq!(doc.boarded_label("Taxi", 0), "jeep1");
    let out = doc.wp("Taxi", 2).pos.expect("GET_OUT has a position");
    assert!(near(out.0, 6800.0) && near(out.1, 6400.0));
}

/// The first vehicle is boarded when it is the one named.
#[test]
fn nominal_first_vehicle() {
    let doc = mb_oracle::accept(&task::run(&base("truck1")).expect("valid input refused"));
    assert_eq!(doc.boarded_label("Taxi", 0), "truck1");
}

/// A label that is not in the roster is refused with UnknownVehicle.
#[test]
fn trap_ref_vehicle_missing_label() {
    assert_eq!(task::run(&base("apc7")), Err(Refusal::UnknownVehicle));
}

/// A label that names a soldier is refused with UnknownVehicle.
#[test]
fn trap_ref_vehicle_label_is_soldier() {
    assert_eq!(task::run(&base("r2")), Err(Refusal::UnknownVehicle));
}
