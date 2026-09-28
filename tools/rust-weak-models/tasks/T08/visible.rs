use mb_spec::t08::Input;
use mb_spec::{Point, Rank::*, UnitClass::*, UnitIn};

/// The assault plan has four waypoints.
#[test]
fn visible_assault_plan() {
    let input = Input {
        units: vec![
            UnitIn::new(Rifleman, "i1", 3000.0, 3000.0, Sergeant),
            UnitIn::new(Truck, "truck1", 3010.0, 3000.0, Private),
        ],
        truck: "truck1".to_string(),
        drop: Point::new(4000.0, 3500.0),
        target: Point::new(4200.0, 3700.0),
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.group("Assault").wps.len(), 4);
}
