use mb_spec::t28::Input;
use mb_spec::{Ending, Point, Radio, Rank::*, UnitClass::*, UnitIn};

/// The group has two waypoints and there are two triggers.
#[test]
fn visible_staged_shape() {
    let input = Input {
        callsign: "Alpha".into(),
        units: vec![UnitIn::new(Rifleman, "a1", 1000.0, 1000.0, Sergeant)],
        start: Point::new(1100.0, 1000.0),
        bridge: Point::new(2000.0, 1500.0),
        bridge_half_m: 60.0,
        release: Radio::Alpha,
        minutes: [2.0, 3.0, 4.0],
        ending: Ending::One,
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.group("Alpha").wps.len(), 2);
    assert_eq!(doc.triggers.len(), 2);
}
