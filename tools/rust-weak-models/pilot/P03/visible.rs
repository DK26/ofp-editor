use mb_spec::p03::Input;
use mb_spec::{Point, Rank::*, UnitClass::*, UnitIn};

/// The export holds the Base group and one trigger.
#[test]
fn visible_base_and_alarm() {
    let input = Input {
        units: vec![UnitIn::new(Officer, "cmd", 3000.0, 3000.0, Captain)],
        base: Point::new(3000.0, 3000.0),
        half_size_m: 150.0,
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.group("Base").units.len(), 1);
    assert_eq!(doc.triggers.len(), 1);
}
