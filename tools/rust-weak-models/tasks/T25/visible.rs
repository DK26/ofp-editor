use mb_spec::t25::{Entry, Input};
use mb_spec::{Rank::*, Side, UnitClass::*, UnitIn};

/// A clean roster is exported.
#[test]
fn visible_clean_roster() {
    let input = Input {
        side: Side::West,
        roster: vec![
            Entry { callsign: "Alpha".into(), units: vec![UnitIn::new(Rifleman, "a1", 1000.0, 1000.0, Sergeant)] },
            Entry { callsign: "Bravo".into(), units: vec![UnitIn::new(Rifleman, "b1", 1100.0, 1000.0, Sergeant)] },
        ],
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.groups.len(), 2);
}
