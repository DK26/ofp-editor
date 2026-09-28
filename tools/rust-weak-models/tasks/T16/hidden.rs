use mb_oracle::near;
use mb_spec::t16::{Input, SquadIn};
use mb_spec::{Point, Rank::*, Refusal, Side, UnitClass::*, UnitIn};

fn squad(callsign: &str, side: Side, x: f64, truck: &str) -> SquadIn {
    SquadIn {
        callsign: callsign.into(),
        side,
        units: vec![
            UnitIn::new(Rifleman, &format!("{callsign}-1"), x, 5000.0, Sergeant),
            UnitIn::new(Rifleman, &format!("{callsign}-2"), x + 4.0, 5000.0, Private),
        ],
        truck: truck.into(),
    }
}

/// Squads board trucks out of vehicle order (Red -> t3, Blue -> t1, Green -> t2).
fn base() -> Input {
    Input {
        pool_callsign: "Wheels".into(),
        pool_side: Side::West,
        vehicles: vec![
            UnitIn::new(Truck, "t1", 1000.0, 5100.0, Private),
            UnitIn::new(Truck, "t2", 1020.0, 5100.0, Private),
            UnitIn::new(Truck, "t3", 1040.0, 5100.0, Private),
            UnitIn::new(Jeep, "escort", 1060.0, 5100.0, Corporal),
        ],
        squads: vec![
            squad("Red", Side::West, 1000.0, "t3"),
            squad("Blue", Side::West, 1100.0, "t1"),
            squad("Green", Side::West, 1200.0, "t2"),
        ],
        destination: Point::new(4000.0, 6000.0),
    }
}

/// Each squad boards its own truck.
#[test]
fn trap_id_mix_each_squad_its_truck() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    assert_eq!(doc.boarded_label("Red", 0), "t3");
    assert_eq!(doc.boarded_label("Blue", 0), "t1");
    assert_eq!(doc.boarded_label("Green", 0), "t2");
}

/// Squads: GET_IN, MOVE, GET_OUT at the destination; the pool: one MOVE.
#[test]
fn trap_seq_mount_board_ride_dismount() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    for cs in ["Red", "Blue", "Green"] {
        assert_eq!(doc.kinds(cs), ["GET_IN", "MOVE", "GET_OUT"], "{cs}");
        let out = doc.wp(cs, 2).pos.unwrap();
        assert!(near(out.0, 4000.0) && near(out.1, 6000.0));
    }
    assert_eq!(doc.kinds("Wheels"), ["MOVE"]);
}

/// Every squad's MOVE is synchronised with the pool's MOVE.
#[test]
fn nominal_convoy_syncs() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    for cs in ["Red", "Blue", "Green"] {
        assert!(doc.synced((cs, 1), ("Wheels", 0)), "{cs} not in step: {:?}", doc.syncs);
    }
    assert_eq!(doc.syncs.len(), 3);
}

/// An unknown truck label is refused with UnknownVehicle.
#[test]
fn trap_ref_vehicle_unknown_truck() {
    let mut input = base();
    input.squads[1].truck = "t9".into();
    assert_eq!(task::run(&input), Err(Refusal::UnknownVehicle));
}

/// An East squad told to board a West truck is refused with WrongSide.
#[test]
fn trap_ref_vehicle_wrong_side() {
    let mut input = base();
    input.squads[2].side = Side::East;
    assert_eq!(task::run(&input), Err(Refusal::WrongSide));
}

/// The first problem in squad order wins.
#[test]
fn trap_ref_vehicle_first_problem_wins() {
    let mut input = base();
    input.squads[0].side = Side::East;
    input.squads[1].truck = "t9".into();
    assert_eq!(task::run(&input), Err(Refusal::WrongSide));
}

/// The motor pool is created first with its vehicles.
#[test]
fn nominal_pool_first() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    assert_eq!(doc.callsigns(), ["Wheels", "Red", "Blue", "Green"]);
    assert_eq!(doc.group("Wheels").units.len(), 4);
}
