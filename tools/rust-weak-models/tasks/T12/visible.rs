use mb_spec::t12::{GroupIn, Input};
use mb_spec::{Rank::*, Side, UnitClass::*, UnitIn};

/// One group with a clear leader is exported.
#[test]
fn visible_one_group() {
    let input = Input {
        groups: vec![GroupIn {
            callsign: "Alpha".into(),
            side: Side::West,
            units: vec![
                UnitIn::new(Rifleman, "a1", 1000.0, 1000.0, Lieutenant),
                UnitIn::new(Rifleman, "a2", 1004.0, 1000.0, Private),
            ],
        }],
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.group("Alpha").units.len(), 2);
}
