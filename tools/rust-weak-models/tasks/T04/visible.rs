use mb_spec::t04::Input;
use mb_spec::{Point, Rank::*, UnitClass::*, UnitIn};

/// A three-point patrol is exported.
#[test]
fn visible_three_point_patrol() {
    let input = Input {
        units: vec![UnitIn::new(Rifleman, "p1", 6000.0, 2000.0, Sergeant)],
        points: vec![Point::new(6100.0, 2000.0), Point::new(6100.0, 2100.0), Point::new(6000.0, 2100.0)],
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.group("Patrol").units.len(), 1);
}
