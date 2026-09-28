use mb_spec::t07::Input;
use mb_spec::{Point, Rank::*, UnitClass::*, UnitIn};

/// The patrol has five waypoints (four stops and the loop).
#[test]
fn visible_patrol_with_depot() {
    let input = Input {
        units: vec![UnitIn::new(Rifleman, "r1", 2000.0, 2000.0, Sergeant)],
        a: Point::new(2100.0, 2000.0),
        b: Point::new(2100.0, 2100.0),
        c: Point::new(2000.0, 2100.0),
        depot: Point::new(1900.0, 2050.0),
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.group("Rover").wps.len(), 5);
}
