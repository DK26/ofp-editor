use mb_spec::t24::{CloseIn, EditIn, GroupIn, Input};
use mb_spec::{Point, Rank::*, Side, UnitClass::*, UnitIn};

/// HQ plus one open group with one edit.
#[test]
fn visible_one_group_one_edit() {
    let input = Input {
        hq: vec![UnitIn::new(Officer, "hq", 500.0, 500.0, Major)],
        groups: vec![GroupIn {
            callsign: "Alpha".into(),
            side: Side::West,
            units: vec![UnitIn::new(Rifleman, "a1", 1000.0, 1000.0, Sergeant)],
            close: CloseIn::Open,
        }],
        edits: vec![EditIn { group: 0, point: Point::new(1100.0, 1000.0) }],
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.groups.len(), 2);
}
