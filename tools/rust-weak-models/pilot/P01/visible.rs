use mb_spec::p01::Input;
use mb_spec::{Rank::*, UnitClass::*, UnitIn};

/// Two riflemen end up in the "Fireteam" group.
#[test]
fn visible_two_riflemen() {
    let input = Input {
        units: vec![
            UnitIn::new(Rifleman, "r1", 1000.0, 1000.0, Corporal),
            UnitIn::new(Rifleman, "r2", 1010.0, 1000.0, Private),
        ],
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.group("Fireteam").units.len(), 2);
}
