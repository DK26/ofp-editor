use mb_spec::t16::{Input, SquadIn};
use mb_spec::{Point, Rank::*, Side, UnitClass::*, UnitIn};

/// One squad and its truck form a two-group convoy.
#[test]
fn visible_one_squad_convoy() {
    let input = Input {
        pool_callsign: "Wheels".into(),
        pool_side: Side::West,
        vehicles: vec![UnitIn::new(Truck, "t1", 1000.0, 5000.0, Private)],
        squads: vec![SquadIn {
            callsign: "Red".into(),
            side: Side::West,
            units: vec![UnitIn::new(Rifleman, "r1", 1010.0, 5000.0, Sergeant)],
            truck: "t1".into(),
        }],
        destination: Point::new(3000.0, 5000.0),
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.groups.len(), 2);
}
