use mb_spec::t27::{Input, RawGroup, RawRef, RawTrigger};
use mb_spec::{Point, Radio, Rank::*, Side, UnitClass::*, UnitIn};

/// A clean draft with one trigger and one sync.
#[test]
fn visible_clean_draft() {
    let input = Input {
        groups: vec![RawGroup {
            callsign: "Alpha".into(),
            side: Side::West,
            units: vec![UnitIn::new(Rifleman, "a1", 1000.0, 1000.0, Sergeant)],
            route: vec![Point::new(1100.0, 1000.0), Point::new(1200.0, 1000.0)],
        }],
        triggers: vec![RawTrigger { channel: Radio::Alpha, syncs: vec![RawRef { group: 0, waypoint: 1 }] }],
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.triggers.len(), 1);
}
