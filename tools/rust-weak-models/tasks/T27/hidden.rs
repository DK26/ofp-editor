use mb_spec::t27::{Input, RawGroup, RawRef, RawTrigger};
use mb_spec::{Point, Radio, Rank::*, Refusal, Side, UnitClass::*, UnitIn};

fn group(callsign: &str, x: f64, n_units: usize, n_route: usize) -> RawGroup {
    RawGroup {
        callsign: callsign.into(),
        side: Side::West,
        units: (0..n_units).map(|i| UnitIn::new(Rifleman, &format!("{callsign}{i}"), x + 4.0 * i as f64, 9000.0, Private)).collect(),
        route: (0..n_route).map(|i| Point::new(x + 100.0 * (i + 1) as f64, 9000.0)).collect(),
    }
}

fn r(group: usize, waypoint: usize) -> RawRef {
    RawRef { group, waypoint }
}

fn draft(t0: Vec<RawRef>, t1: Vec<RawRef>) -> Input {
    Input {
        groups: vec![group("Alpha", 1000.0, 2, 3), group("Bravo", 3000.0, 1, 2), group("Charlie", 5000.0, 2, 1)],
        triggers: vec![RawTrigger { channel: Radio::Alpha, syncs: t0 }, RawTrigger { channel: Radio::Bravo, syncs: t1 }],
    }
}

/// Valid references are kept on the right groups (by input position) and no note is set.
#[test]
fn nominal_clean_references() {
    let input = draft(vec![r(0, 2), r(2, 0)], vec![r(1, 1)]);
    let doc = mb_oracle::accept(&task::run(&input).expect("valid input refused"));
    assert_eq!(doc.trigger_syncs(0), vec![("Alpha".to_string(), 2), ("Charlie".to_string(), 0)]);
    assert_eq!(doc.trigger_syncs(1), vec![("Bravo".to_string(), 1)]);
    assert_eq!(doc.note, None);
}

/// Broken references are dropped and listed in the note, in input order.
#[test]
fn trap_ref_sync_broken_dropped_and_noted() {
    let input = draft(vec![r(5, 0), r(0, 1)], vec![r(1, 9), r(2, 0)]);
    let doc = mb_oracle::accept(&task::run(&input).expect("valid input refused"));
    assert_eq!(doc.trigger_syncs(0), vec![("Alpha".to_string(), 1)]);
    assert_eq!(doc.trigger_syncs(1), vec![("Charlie".to_string(), 0)]);
    assert_eq!(doc.note.as_deref(), Some("t0:5:0, t1:1:9"));
}

/// A waypoint index equal to the route length is broken (indices count from 0).
#[test]
fn trap_id_mix_index_equal_to_length_is_broken() {
    let input = draft(vec![r(1, 2)], vec![r(1, 1)]);
    let doc = mb_oracle::accept(&task::run(&input).expect("valid input refused"));
    assert!(doc.trigger_syncs(0).is_empty());
    assert_eq!(doc.note.as_deref(), Some("t0:1:2"));
}

/// Triggers are once-only radio triggers on their channels.
#[test]
fn nominal_triggers() {
    let doc = mb_oracle::accept(&task::run(&draft(vec![], vec![])).expect("valid input refused"));
    assert_eq!(doc.triggers[0].act, ["RADIO", "ALPHA"]);
    assert_eq!(doc.triggers[1].act, ["RADIO", "BRAVO"]);
    assert!(doc.triggers.iter().all(|t| t.repeat == "ONCE" && t.effect == "NONE"));
}

/// A group without units is refused with EmptyGroup.
#[test]
fn trap_empty_group() {
    let mut input = draft(vec![r(0, 0)], vec![]);
    input.groups[1].units.clear();
    assert_eq!(task::run(&input), Err(Refusal::EmptyGroup));
}
