use mb_spec::t23::{ClearIn, Input};
use mb_spec::{Point, Rank::*, Side, UnitClass::*, UnitIn};

/// One group without prior orders gets the three-waypoint sequence.
#[test]
fn visible_one_group() {
    let input = Input {
        groups: vec![ClearIn {
            callsign: "Alpha".into(),
            side: Side::West,
            units: vec![UnitIn::new(Rifleman, "a1", 1000.0, 1000.0, Sergeant)],
            prior: vec![],
            entry: Point::new(1200.0, 1200.0),
            target: Point::new(1400.0, 1400.0),
        }],
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.group("Alpha").wps.len(), 3);
}
