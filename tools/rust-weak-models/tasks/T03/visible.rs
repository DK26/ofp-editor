use mb_spec::t03::Input;
use mb_spec::{Point, Rank::*, UnitClass::*, UnitIn};

/// Two points give two waypoints.
#[test]
fn visible_two_points() {
    let input = Input {
        units: vec![UnitIn::new(Rifleman, "s1", 3000.0, 6000.0, Corporal)],
        points: vec![Point::new(3100.0, 6000.0), Point::new(3200.0, 6100.0)],
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.group("Sentry").wps.len(), 2);
}
