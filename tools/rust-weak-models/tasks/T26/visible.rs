use mb_spec::t26::{ConvoyIn, Input, PatrolIn};
use mb_spec::{Point, Radio, Rank::*, UnitClass::*, UnitIn};

/// The scenario has three groups and three triggers.
#[test]
fn visible_scenario_shape() {
    let input = Input {
        patrol: PatrolIn {
            callsign: "Hawk".into(),
            units: vec![UnitIn::new(Rifleman, "h1", 2000.0, 2000.0, Sergeant)],
            route: vec![Point::new(2100.0, 2000.0), Point::new(2100.0, 2100.0)],
        },
        convoy: ConvoyIn {
            callsign: "Mule".into(),
            units: vec![UnitIn::new(Rifleman, "m1", 3000.0, 2000.0, Sergeant), UnitIn::new(Truck, "mt", 3010.0, 2000.0, Private)],
            truck: "mt".into(),
            destination: Point::new(3500.0, 2500.0),
        },
        enemy: PatrolIn {
            callsign: "Wolf".into(),
            units: vec![UnitIn::new(Rifleman, "w1", 8000.0, 8000.0, Sergeant)],
            route: vec![Point::new(7900.0, 7900.0)],
        },
        release: Radio::Alpha,
        release_callsign: "Mule".into(),
        objective: Point::new(5000.0, 5000.0),
        objective_half_m: 300.0,
        hold_minutes: [1.0, 2.0, 3.0],
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.groups.len(), 3);
    assert_eq!(doc.triggers.len(), 3);
}
