use mb_spec::t06::Input;
use mb_spec::{Point, Rank::*, UnitClass::*, UnitIn};

/// The export has the Garrison group and one timed trigger.
#[test]
fn visible_timed_trigger() {
    let input = Input {
        units: vec![UnitIn::new(Rifleman, "g1", 5000.0, 5000.0, Sergeant)],
        zone: Point::new(5000.0, 5100.0),
        zone_half_m: 200.0,
        minutes_min: 1.0,
        minutes_typical: 2.0,
        minutes_max: 3.0,
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.triggers.len(), 1);
    assert!(doc.triggers[0].timer.is_some());
}
