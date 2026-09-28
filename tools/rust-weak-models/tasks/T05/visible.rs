use mb_spec::t05::Input;
use mb_spec::{Ending, Radio, Rank::*, UnitClass::*, UnitIn};

/// The export has the HQ group and one trigger.
#[test]
fn visible_radio_trigger() {
    let input = Input {
        units: vec![UnitIn::new(Officer, "hq1", 1500.0, 1500.0, Major)],
        channel: Radio::Alpha,
        ending: Ending::One,
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.group("HQ").units.len(), 1);
    assert_eq!(doc.triggers.len(), 1);
}
