use mb_spec::t17::Input;
use mb_spec::{Point, Rank::*, UnitClass::*, UnitIn};

/// The export has the Ambush group and one trigger.
#[test]
fn visible_ambush() {
    let input = Input {
        units: vec![UnitIn::new(MachineGunner, "m1", 5000.0, 5000.0, Sergeant)],
        ambush: Point::new(5200.0, 5200.0),
        kill_zone: Point::new(5400.0, 5300.0),
        kill_zone_half_m: 120.0,
        extraction: Point::new(4800.0, 4800.0),
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.group("Ambush").units.len(), 1);
    assert_eq!(doc.triggers.len(), 1);
}
