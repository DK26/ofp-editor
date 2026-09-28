use mb_spec::t01::Input;
use mb_spec::{Rank::*, UnitClass::*, UnitIn};

/// Three riflemen end up in the "Alpha" group.
#[test]
fn visible_three_riflemen() {
    let input = Input {
        units: vec![
            UnitIn::new(Rifleman, "a1", 1000.0, 2000.0, Private),
            UnitIn::new(Rifleman, "a2", 1010.0, 2000.0, Sergeant),
            UnitIn::new(Rifleman, "a3", 1020.0, 2000.0, Private),
        ],
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.group("Alpha").units.len(), 3);
}
