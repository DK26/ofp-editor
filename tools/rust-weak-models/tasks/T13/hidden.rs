use mb_spec::t13::{Input, PatrolIn, WaypointNo};
use mb_spec::{Point, Rank::*, Refusal, Side, UnitClass::*, UnitIn};

fn patrol(callsign: &str, x: f64, n: usize) -> PatrolIn {
    PatrolIn {
        callsign: callsign.into(),
        side: Side::West,
        units: vec![
            UnitIn::new(Rifleman, &format!("{callsign}-1"), x, 4000.0, Sergeant),
            UnitIn::new(Rifleman, &format!("{callsign}-2"), x + 4.0, 4000.0, Private),
        ],
        route: (0..n).map(|i| Point::new(x + 100.0 * (i + 1) as f64, 4000.0 + 50.0 * i as f64)).collect(),
    }
}

fn wp(callsign: &str, number: usize) -> WaypointNo {
    WaypointNo { callsign: callsign.into(), number }
}

/// Groups are listed Charlie, Bravo, Alpha so input order and callsigns disagree.
fn base(first: WaypointNo, second: WaypointNo) -> Input {
    Input {
        groups: vec![patrol("Charlie", 5000.0, 2), patrol("Bravo", 3000.0, 4), patrol("Alpha", 1000.0, 3)],
        first,
        second,
    }
}

/// Alpha's second and Bravo's third waypoints (numbers from 1) are synchronised.
#[test]
fn trap_id_mix_numbers_counted_from_one() {
    let doc = mb_oracle::accept(&task::run(&base(wp("Alpha", 2), wp("Bravo", 3))).expect("valid input refused"));
    assert_eq!(doc.syncs.len(), 1, "exactly one synchronisation");
    assert!(doc.synced(("Alpha", 1), ("Bravo", 2)), "syncs: {:?}", doc.syncs);
}

/// The groups are found by callsign, not by input position.
#[test]
fn trap_id_mix_callsign_not_position() {
    let doc = mb_oracle::accept(&task::run(&base(wp("Charlie", 1), wp("Alpha", 3))).expect("valid input refused"));
    assert!(doc.synced(("Charlie", 0), ("Alpha", 2)), "syncs: {:?}", doc.syncs);
}

/// A missing first callsign is refused with UnknownGroup.
#[test]
fn trap_ref_sync_unknown_first() {
    assert_eq!(task::run(&base(wp("Delta", 1), wp("Bravo", 1))), Err(Refusal::UnknownGroup));
}

/// A missing second callsign is refused with UnknownGroup.
#[test]
fn trap_ref_sync_unknown_second() {
    assert_eq!(task::run(&base(wp("Alpha", 1), wp("Echo", 1))), Err(Refusal::UnknownGroup));
}

/// Every group moves through its route.
#[test]
fn nominal_routes() {
    let doc = mb_oracle::accept(&task::run(&base(wp("Alpha", 1), wp("Bravo", 1))).expect("valid input refused"));
    assert_eq!(doc.kinds("Bravo"), ["MOVE", "MOVE", "MOVE", "MOVE"]);
    assert_eq!(doc.kinds("Charlie"), ["MOVE", "MOVE"]);
    assert_eq!(doc.callsigns(), ["Charlie", "Bravo", "Alpha"]);
}
