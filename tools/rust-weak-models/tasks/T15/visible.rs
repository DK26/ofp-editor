use mb_spec::t15::{Input, PatrolIn};
use mb_spec::{Point, Radio, Rank::*, Side, UnitClass::*, UnitIn};

fn patrol(callsign: &str, x: f64) -> PatrolIn {
    PatrolIn {
        callsign: callsign.into(),
        side: Side::West,
        units: vec![UnitIn::new(Rifleman, &format!("{callsign}-1"), x, 2000.0, Sergeant)],
        route: vec![Point::new(x + 100.0, 2000.0), Point::new(x + 200.0, 2000.0)],
    }
}

/// Two groups and one radio trigger.
#[test]
fn visible_release_trigger() {
    let input = Input {
        groups: vec![patrol("Alpha", 1000.0), patrol("Bravo", 3000.0)],
        waiting: "Bravo".into(),
        number: 2,
        channel: Radio::Bravo,
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.groups.len(), 2);
    assert_eq!(doc.triggers.len(), 1);
}
