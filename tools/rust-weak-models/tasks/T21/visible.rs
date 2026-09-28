use mb_spec::t21::Input;
use mb_spec::{Ending, Radio, Rank::*, UnitClass::*, UnitIn};

/// The export has the Player group and two triggers.
#[test]
fn visible_two_triggers() {
    let input = Input {
        units: vec![UnitIn::new(Rifleman, "p1", 6000.0, 6000.0, Lieutenant)],
        win_channel: Radio::Alpha,
        win_ending: Ending::One,
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.triggers.len(), 2);
}
