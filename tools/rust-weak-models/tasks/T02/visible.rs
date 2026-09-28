use mb_spec::t02::Input;
use mb_spec::{Point, Rank::*, UnitClass::*, UnitIn};

/// The team gets two waypoints.
#[test]
fn visible_two_points() {
    let input = Input {
        units: vec![
            UnitIn::new(Rifleman, "e1", 9000.0, 9000.0, Corporal),
            UnitIn::new(Rifleman, "e2", 9005.0, 9000.0, Private),
        ],
        first: Point::new(9200.0, 9100.0),
        second: Point::new(9400.0, 9300.0),
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.group("Team").wps.len(), 2);
}
