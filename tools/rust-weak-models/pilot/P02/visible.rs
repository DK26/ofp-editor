use mb_spec::p02::Input;
use mb_spec::{Point, Rank::*, UnitClass::*, UnitIn};

/// The guard team walks to the gate, then stays at the post.
#[test]
fn visible_gate_then_post() {
    let input = Input {
        units: vec![UnitIn::new(Rifleman, "g1", 5000.0, 5000.0, Corporal)],
        gate: Point::new(5100.0, 5000.0),
        post: Point::new(5120.0, 5010.0),
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.group("Guard").side, "EAST");
    assert_eq!(doc.group("Guard").wps.len(), 2);
}
