use mb_spec::t29::{Input, WaveIn};
use mb_spec::{Point, Radio, Rank::*, UnitClass::*, UnitIn};

/// Two waves and two triggers.
#[test]
fn visible_two_waves() {
    let input = Input {
        first: WaveIn {
            callsign: "One".into(),
            units: vec![UnitIn::new(Rifleman, "o1", 1000.0, 1000.0, Sergeant), UnitIn::new(Truck, "ot", 1010.0, 1000.0, Private)],
            vehicle: "ot".into(),
        },
        second: WaveIn {
            callsign: "Two".into(),
            units: vec![UnitIn::new(Rifleman, "t1", 1100.0, 1000.0, Sergeant), UnitIn::new(Truck, "tt", 1110.0, 1000.0, Private)],
            vehicle: "tt".into(),
        },
        route: vec![Point::new(2000.0, 2000.0)],
        release: Radio::Alpha,
        delay_s: 60.0,
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.groups.len(), 2);
    assert_eq!(doc.triggers.len(), 2);
}
