use mb_spec::t09::Input;
use mb_spec::{Point, Rank::*, UnitClass::*, UnitIn};

/// The export has the Defenders group and one trigger.
#[test]
fn visible_town_trigger() {
    let input = Input {
        units: vec![UnitIn::new(Rifleman, "d1", 8000.0, 8000.0, Sergeant)],
        town: Point::new(8100.0, 8100.0),
        town_half_m: 250.0,
        repeating: false,
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.triggers.len(), 1);
}
