use mb_spec::t10::Input;
use mb_spec::{Point, Rank::*, Side, UnitClass::*, UnitIn};

/// The export has the Scouts group and one trigger.
#[test]
fn visible_detection_trigger() {
    let input = Input {
        units: vec![UnitIn::new(Rifleman, "s1", 4000.0, 9000.0, Corporal)],
        watcher: Side::East,
        watched: Side::West,
        area: Point::new(4100.0, 9100.0),
        area_half_m: 500.0,
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.group("Scouts").units.len(), 1);
    assert_eq!(doc.triggers.len(), 1);
}
