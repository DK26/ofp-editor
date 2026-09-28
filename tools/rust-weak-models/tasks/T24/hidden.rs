use mb_oracle::near;
use mb_spec::t24::{CloseIn, EditIn, GroupIn, Input};
use mb_spec::{Point, Rank::*, Refusal, Side, UnitClass::*, UnitIn};

fn group(callsign: &str, x: f64, close: CloseIn) -> GroupIn {
    GroupIn {
        callsign: callsign.into(),
        side: Side::East,
        units: vec![UnitIn::new(Rifleman, &format!("{callsign}-1"), x, 4000.0, Sergeant)],
        close,
    }
}

fn edit(group: usize, x: f64, z: f64) -> EditIn {
    EditIn { group, point: Point::new(x, z) }
}

fn base() -> Input {
    Input {
        hq: vec![UnitIn::new(Officer, "hq", 500.0, 500.0, Major)],
        groups: vec![
            group("Alpha", 1000.0, CloseIn::Loop),
            group("Bravo", 2000.0, CloseIn::Hold(Point::new(2500.0, 4500.0))),
            group("Charlie", 3000.0, CloseIn::Open),
        ],
        edits: vec![
            edit(0, 1100.0, 4000.0),
            edit(2, 3100.0, 4000.0),
            edit(1, 2100.0, 4000.0),
            edit(0, 1200.0, 4100.0),
            edit(0, 1300.0, 4200.0),
        ],
    }
}

/// Edits land on the listed groups, never on HQ (group positions do not count HQ).
#[test]
fn trap_id_mix_positions_skip_hq() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    assert!(doc.group("HQ").wps.is_empty(), "HQ got waypoints: {:?}", doc.kinds("HQ"));
    assert_eq!(doc.kinds("Alpha"), ["MOVE", "MOVE", "MOVE", "CYCLE"]);
}

/// Each group's edits keep input order; closing follows `close`.
#[test]
fn nominal_edits_and_closing() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    let a2 = doc.wp("Alpha", 2).pos.unwrap();
    assert!(near(a2.0, 1300.0) && near(a2.1, 4200.0));
    assert_eq!(doc.kinds("Bravo"), ["MOVE", "HOLD"]);
    let h = doc.wp("Bravo", 1).pos.unwrap();
    assert!(near(h.0, 2500.0) && near(h.1, 4500.0));
    assert_eq!(doc.kinds("Charlie"), ["MOVE"]);
}

/// A looping group with a single waypoint is refused with InvalidSequence.
#[test]
fn trap_seq_cycle_loop_too_few() {
    let mut input = base();
    input.edits.retain(|e| !(e.group == 0 && e.point.x > 1150.0));
    assert_eq!(task::run(&input), Err(Refusal::InvalidSequence));
}

/// HQ comes first, then the groups in order.
#[test]
fn nominal_group_order() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    assert_eq!(doc.callsigns(), ["HQ", "Alpha", "Bravo", "Charlie"]);
    assert_eq!(doc.group("HQ").side, "WEST");
}
