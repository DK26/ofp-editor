use mb_spec::p04::Input;
use mb_spec::{Point, Rank::*, UnitClass::*, UnitIn};

/// The team rides its jeep to the destination.
#[test]
fn visible_jeep_ride() {
    let input = Input {
        units: vec![
            UnitIn::new(Rifleman, "r1", 4000.0, 4000.0, Sergeant),
            UnitIn::new(Jeep, "jeep1", 4005.0, 4000.0, Private),
        ],
        ride: "jeep1".to_string(),
        destination: Point::new(4500.0, 4200.0),
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.group("Taxi").wps.len(), 3);
}
