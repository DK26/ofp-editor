use mb_spec::t19::{DraftIn, Input, PatrolIn, SyncIn};
use mb_spec::{Point, Rank::*, Side, UnitClass::*, UnitIn};

fn patrol(callsign: &str, x: f64) -> PatrolIn {
    PatrolIn {
        callsign: callsign.into(),
        side: Side::West,
        units: vec![UnitIn::new(Rifleman, &format!("{callsign}-1"), x, 3000.0, Sergeant)],
        route: vec![Point::new(x + 100.0, 3000.0), Point::new(x + 200.0, 3000.0)],
    }
}

/// Two one-group drafts merge into two groups.
#[test]
fn visible_two_small_drafts() {
    let input = Input {
        first: DraftIn { groups: vec![patrol("Alpha", 1000.0)], syncs: vec![] },
        second: DraftIn {
            groups: vec![patrol("Bravo", 2000.0), patrol("Charlie", 3000.0)],
            syncs: vec![SyncIn { group_a: 0, wp_a: 0, group_b: 1, wp_b: 0 }],
        },
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.groups.len(), 3);
    assert_eq!(doc.syncs.len(), 1);
}
