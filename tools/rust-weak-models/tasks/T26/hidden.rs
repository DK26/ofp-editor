use mb_oracle::near;
use mb_spec::t26::{ConvoyIn, Input, PatrolIn};
use mb_spec::{Point, Radio, Rank::*, Refusal, UnitClass::*, UnitIn};

fn base(release_callsign: &str) -> Input {
    Input {
        patrol: PatrolIn {
            callsign: "Hawk".into(),
            units: vec![
                UnitIn::new(Rifleman, "h1", 2000.0, 2000.0, Sergeant),
                UnitIn::new(Rifleman, "h2", 2004.0, 2000.0, Private),
            ],
            route: vec![Point::new(2100.0, 2000.0), Point::new(2100.0, 2200.0), Point::new(1900.0, 2200.0)],
        },
        convoy: ConvoyIn {
            callsign: "Mule".into(),
            units: vec![
                UnitIn::new(Rifleman, "m1", 3000.0, 2000.0, Sergeant),
                UnitIn::new(Jeep, "mj", 3020.0, 2000.0, Private),
                UnitIn::new(Truck, "mt", 3010.0, 2000.0, Private),
            ],
            truck: "mt".into(),
            destination: Point::new(3500.0, 2500.0),
        },
        enemy: PatrolIn {
            callsign: "Wolf".into(),
            units: vec![UnitIn::new(Rifleman, "w1", 8000.0, 8000.0, Sergeant)],
            route: vec![Point::new(7900.0, 7900.0), Point::new(7800.0, 7700.0)],
        },
        release: Radio::India,
        release_callsign: release_callsign.into(),
        objective: Point::new(5000.0, 5000.0),
        objective_half_m: 300.0,
        hold_minutes: [2.0, 3.0, 5.0],
    }
}

/// The patrol is a loop: moves, then CYCLE last.
#[test]
fn trap_seq_cycle_patrol_loop() {
    let doc = mb_oracle::accept(&task::run(&base("Mule")).expect("valid input refused"));
    assert_eq!(doc.kinds("Hawk"), ["MOVE", "MOVE", "MOVE", "CYCLE"]);
}

/// The convoy boards its truck (not the jeep), rides and dismounts; its MOVE is in
/// step with the patrol's second waypoint.
#[test]
fn nominal_convoy() {
    let doc = mb_oracle::accept(&task::run(&base("Mule")).expect("valid input refused"));
    assert_eq!(doc.kinds("Mule"), ["GET_IN", "MOVE", "GET_OUT"]);
    assert_eq!(doc.boarded_label("Mule", 0), "mt");
    assert!(doc.synced(("Mule", 1), ("Hawk", 1)), "{:?}", doc.syncs);
}

/// The hold time is stored in seconds (2/3/5 minutes -> 120/180/300 s) as a timeout.
#[test]
fn trap_unit_measure_hold_minutes() {
    let doc = mb_oracle::accept(&task::run(&base("Mule")).expect("valid input refused"));
    let win = doc.triggers_with_act(&["PRESENT", "WEST"]);
    assert_eq!(win.len(), 1);
    let (kind, lo, md, hi) = win[0].timer.clone().expect("timer");
    assert_eq!(kind, "TIMEOUT");
    assert!(near(lo, 120.0) && near(md, 180.0) && near(hi, 300.0), "{lo}/{md}/{hi}");
    assert_eq!(win[0].effect, "END 1");
}

/// The release trigger is synchronised with the named group's first waypoint.
#[test]
fn trap_ref_sync_release_group() {
    let doc = mb_oracle::accept(&task::run(&base("Wolf")).expect("valid input refused"));
    let idx = doc.triggers.iter().position(|t| t.act == ["RADIO", "INDIA"]).expect("release trigger");
    assert_eq!(doc.trigger_syncs(idx), vec![("Wolf".to_string(), 0)]);
}

/// An unknown release callsign is refused with UnknownGroup.
#[test]
fn trap_ref_sync_unknown_release() {
    assert_eq!(task::run(&base("Eagle")), Err(Refusal::UnknownGroup));
}

/// The loss and win fire once; nothing repeats.
#[test]
fn trap_act_rule_nothing_repeats() {
    let doc = mb_oracle::accept(&task::run(&base("Mule")).expect("valid input refused"));
    assert_eq!(doc.triggers.len(), 3);
    assert!(doc.triggers.iter().all(|t| t.repeat == "ONCE"));
    let loss = doc.triggers_with_act(&["NOT_PRESENT", "WEST"]);
    assert_eq!(loss.len(), 1);
    assert_eq!(loss[0].effect, "LOSE");
}

/// Groups in order, sides as briefed.
#[test]
fn nominal_groups() {
    let doc = mb_oracle::accept(&task::run(&base("Mule")).expect("valid input refused"));
    assert_eq!(doc.callsigns(), ["Hawk", "Mule", "Wolf"]);
    assert_eq!(doc.group("Wolf").side, "EAST");
    assert_eq!(doc.kinds("Wolf"), ["MOVE", "MOVE"]);
}
