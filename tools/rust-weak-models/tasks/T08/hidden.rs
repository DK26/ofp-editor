use mb_oracle::near;
use mb_spec::t08::Input;
use mb_spec::{Point, Rank::*, Refusal, UnitClass::*, UnitIn};

fn base(truck: &str) -> Input {
    Input {
        units: vec![
            UnitIn::new(Rifleman, "i1", 5000.0, 1000.0, Sergeant),
            UnitIn::new(Jeep, "jeep1", 5020.0, 1000.0, Private),
            UnitIn::new(AtSoldier, "i2", 5004.0, 1000.0, Private),
            UnitIn::new(Truck, "truck1", 5030.0, 1000.0, Private),
            UnitIn::new(Truck, "truck2", 5040.0, 1000.0, Private),
        ],
        truck: truck.to_string(),
        drop: Point::new(6000.0, 1500.0),
        target: Point::new(6300.0, 1800.0),
    }
}

/// GET_IN, MOVE to the drop, GET_OUT at the drop, SEEK_AND_DESTROY at the target.
#[test]
fn trap_seq_mount_board_move_dismount_attack() {
    let doc = mb_oracle::accept(&task::run(&base("truck1")).expect("valid input refused"));
    assert_eq!(doc.kinds("Assault"), ["GET_IN", "MOVE", "GET_OUT", "SEEK_AND_DESTROY"]);
    let out = doc.wp("Assault", 2).pos.unwrap();
    assert!(near(out.0, 6000.0) && near(out.1, 1500.0));
    let t = doc.wp("Assault", 3).pos.unwrap();
    assert!(near(t.0, 6300.0) && near(t.1, 1800.0));
}

/// The named truck is boarded, not the first vehicle of the roster.
#[test]
fn nominal_named_truck_boarded() {
    let doc = mb_oracle::accept(&task::run(&base("truck2")).expect("valid input refused"));
    assert_eq!(doc.boarded_label("Assault", 0), "truck2");
}

/// A truck label missing from the roster is refused with UnknownVehicle.
#[test]
fn trap_ref_vehicle_missing() {
    assert_eq!(task::run(&base("truck9")), Err(Refusal::UnknownVehicle));
}

/// A label that names a soldier is refused with UnknownVehicle.
#[test]
fn trap_ref_vehicle_soldier_label() {
    assert_eq!(task::run(&base("i2")), Err(Refusal::UnknownVehicle));
}

/// All five units are in the group.
#[test]
fn nominal_units() {
    let doc = mb_oracle::accept(&task::run(&base("truck1")).expect("valid input refused"));
    assert_eq!(doc.group("Assault").units.len(), 5);
}
