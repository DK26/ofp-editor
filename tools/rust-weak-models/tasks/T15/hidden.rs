use mb_spec::t15::{Input, PatrolIn};
use mb_spec::{Point, Radio, Rank::*, Refusal, Side, UnitClass::*, UnitIn};

fn patrol(callsign: &str, x: f64, n: usize) -> PatrolIn {
    PatrolIn {
        callsign: callsign.into(),
        side: Side::East,
        units: vec![
            UnitIn::new(Rifleman, &format!("{callsign}-1"), x, 7000.0, Sergeant),
            UnitIn::new(Rifleman, &format!("{callsign}-2"), x + 4.0, 7000.0, Private),
        ],
        route: (0..n).map(|i| Point::new(x + 100.0 * (i + 1) as f64, 7000.0)).collect(),
    }
}

fn base(waiting: &str, number: usize, channel: Radio) -> Input {
    Input {
        groups: vec![patrol("Alpha", 1000.0, 3), patrol("Bravo", 3000.0, 3), patrol("Charlie", 5000.0, 2)],
        waiting: waiting.into(),
        number,
        channel,
    }
}

/// Bravo's second waypoint (index 1) waits for radio Bravo.
#[test]
fn trap_ref_sync_trigger_on_right_waypoint() {
    let doc = mb_oracle::accept(&task::run(&base("Bravo", 2, Radio::Bravo)).expect("valid input refused"));
    assert_eq!(doc.triggers.len(), 1);
    assert_eq!(doc.trigger_syncs(0), vec![("Bravo".to_string(), 1)]);
}

/// The waiting group is found by callsign (Charlie is the third group).
#[test]
fn trap_id_mix_group_by_callsign() {
    let doc = mb_oracle::accept(&task::run(&base("Charlie", 1, Radio::Delta)).expect("valid input refused"));
    assert_eq!(doc.trigger_syncs(0), vec![("Charlie".to_string(), 0)]);
}

/// The trigger is a once-only radio trigger on the given channel with no effect.
#[test]
fn nominal_radio_trigger() {
    let doc = mb_oracle::accept(&task::run(&base("Bravo", 2, Radio::Bravo)).expect("valid input refused"));
    let t = doc.triggers_with_act(&["RADIO", "BRAVO"]);
    assert_eq!(t.len(), 1);
    assert_eq!(t[0].effect, "NONE");
    assert_eq!(t[0].repeat, "ONCE");
}

/// A missing waiting group is refused with UnknownGroup.
#[test]
fn trap_ref_sync_missing_group() {
    assert_eq!(task::run(&base("Zulu", 1, Radio::Bravo)), Err(Refusal::UnknownGroup));
}

/// The routes stay plain MOVE waypoints.
#[test]
fn nominal_routes() {
    let doc = mb_oracle::accept(&task::run(&base("Bravo", 2, Radio::Bravo)).expect("valid input refused"));
    assert_eq!(doc.kinds("Bravo"), ["MOVE", "MOVE", "MOVE"]);
    assert_eq!(doc.kinds("Charlie"), ["MOVE", "MOVE"]);
}
