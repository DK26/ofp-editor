use mb_spec::t18::{Input, OrderIn};
use mb_spec::{Point, Rank::*, UnitClass::*, UnitIn};

/// Three simple orders give three waypoints.
#[test]
fn visible_three_orders() {
    let input = Input {
        units: vec![UnitIn::new(Rifleman, "o1", 2000.0, 2000.0, Sergeant)],
        orders: vec![
            OrderIn::Move(Point::new(2100.0, 2000.0)),
            OrderIn::Hunt(Point::new(2200.0, 2100.0)),
            OrderIn::Hold(Point::new(2300.0, 2200.0)),
        ],
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.group("Orders").wps.len(), 3);
}
