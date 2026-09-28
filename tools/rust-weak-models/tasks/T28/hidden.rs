use mb_oracle::near;
use mb_spec::t28::Input;
use mb_spec::{Ending, Point, Radio, Rank::*, UnitClass::*, UnitIn};

fn base() -> Input {
    Input {
        callsign: "Lancer".into(),
        units: vec![
            UnitIn::new(Rifleman, "l1", 4000.0, 3000.0, Sergeant),
            UnitIn::new(AtSoldier, "l2", 4004.0, 3000.0, Private),
        ],
        start: Point::new(4100.0, 3100.0),
        bridge: Point::new(5200.0, 3600.0),
        bridge_half_m: 80.0,
        release: Radio::Juliet,
        minutes: [2.0, 3.0, 4.0],
        ending: Ending::Two,
    }
}

fn index_of(doc: &mb_oracle::Doc, act: &[&str]) -> usize {
    doc.triggers
        .iter()
        .position(|t| t.act.iter().map(String::as_str).eq(act.iter().copied()))
        .unwrap_or_else(|| panic!("no trigger {act:?}: {:?}", doc.triggers))
}

/// The radio trigger waits on the first waypoint.
#[test]
fn trap_ref_sync_release_on_first_waypoint() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    let i = index_of(&doc, &["RADIO", "JULIET"]);
    assert_eq!(doc.trigger_syncs(i), vec![("Lancer".to_string(), 0)]);
    assert_eq!(doc.triggers[i].effect, "NONE");
}

/// The bridge trigger (no activation) is synchronised with the second waypoint.
#[test]
fn trap_ref_sync_bridge_on_second_waypoint() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    let i = index_of(&doc, &["NONE"]);
    assert_eq!(doc.trigger_syncs(i), vec![("Lancer".to_string(), 1)]);
    let a = doc.triggers[i].area;
    assert!(near(a[0], 5200.0) && near(a[1], 3600.0) && near(a[2], 80.0));
}

/// 2/3/4 minutes are stored as a countdown of 120/180/240 seconds.
#[test]
fn trap_unit_measure_countdown_minutes() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    let i = index_of(&doc, &["NONE"]);
    let (kind, lo, md, hi) = doc.triggers[i].timer.clone().expect("timer");
    assert_eq!(kind, "COUNTDOWN");
    assert!(near(lo, 120.0) && near(md, 180.0) && near(hi, 240.0), "{lo}/{md}/{hi}");
}

/// The ending fires once with the given ending.
#[test]
fn trap_act_rule_ending_once() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    let i = index_of(&doc, &["NONE"]);
    assert_eq!(doc.triggers[i].effect, "END 2");
    assert!(doc.triggers.iter().all(|t| t.repeat == "ONCE"));
}

/// Two MOVE waypoints: start, then bridge.
#[test]
fn nominal_route() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    assert_eq!(doc.kinds("Lancer"), ["MOVE", "MOVE"]);
    let b = doc.wp("Lancer", 1).pos.unwrap();
    assert!(near(b.0, 5200.0) && near(b.1, 3600.0));
}
