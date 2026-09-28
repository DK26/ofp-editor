use mb_oracle::near;
use mb_spec::t17::Input;
use mb_spec::{Point, Rank::*, UnitClass::*, UnitIn};

fn base() -> Input {
    Input {
        units: vec![
            UnitIn::new(MachineGunner, "m1", 9000.0, 9000.0, Sergeant),
            UnitIn::new(AtSoldier, "m2", 9004.0, 9000.0, Private),
        ],
        ambush: Point::new(9300.0, 9200.0),
        kill_zone: Point::new(9500.0, 9400.0),
        kill_zone_half_m: 150.0,
        extraction: Point::new(8700.0, 8800.0),
    }
}

/// Waiting is a synchronised MOVE, not HOLD: nothing may follow HOLD.
#[test]
fn trap_seq_hold_wait_is_not_hold() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    let kinds = doc.kinds("Ambush");
    assert!(!kinds.iter().any(|k| k == "HOLD"), "{kinds:?}");
    assert_eq!(kinds, ["MOVE", "MOVE"]);
}

/// The kill-zone trigger is synchronised with the ambush waypoint.
#[test]
fn trap_ref_sync_trigger_on_ambush_waypoint() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    assert_eq!(doc.triggers.len(), 1);
    assert_eq!(doc.trigger_syncs(0), vec![("Ambush".to_string(), 0)]);
}

/// The trigger: West present in the kill zone, once, no effect.
#[test]
fn nominal_kill_zone_trigger() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    let t = doc.triggers_with_act(&["PRESENT", "WEST"]);
    assert_eq!(t.len(), 1);
    assert_eq!((t[0].repeat.as_str(), t[0].effect.as_str()), ("ONCE", "NONE"));
    assert!(near(t[0].area[0], 9500.0) && near(t[0].area[1], 9400.0) && near(t[0].area[2], 150.0));
}

/// Ambush point first, extraction second.
#[test]
fn nominal_positions() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    let a = doc.wp("Ambush", 0).pos.unwrap();
    let e = doc.wp("Ambush", 1).pos.unwrap();
    assert!(near(a.0, 9300.0) && near(a.1, 9200.0));
    assert!(near(e.0, 8700.0) && near(e.1, 8800.0));
}
