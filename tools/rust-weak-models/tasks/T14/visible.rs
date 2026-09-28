use mb_spec::t14::Input;
use mb_spec::{Point, Rank::*, UnitClass::*, UnitIn};

/// The export has the Holdout group and one timed trigger.
#[test]
fn visible_timed_hold() {
    let input = Input {
        units: vec![UnitIn::new(Rifleman, "h1", 6000.0, 6000.0, Sergeant)],
        post: Point::new(6000.0, 6100.0),
        post_half_m: 100.0,
        seconds: [90.0, 30.0, 60.0],
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.triggers.len(), 1);
}
