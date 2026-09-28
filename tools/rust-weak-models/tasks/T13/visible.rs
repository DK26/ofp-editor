use mb_spec::t13::{Input, PatrolIn, WaypointNo};
use mb_spec::{Point, Rank::*, Side, UnitClass::*, UnitIn};

fn patrol(callsign: &str, x: f64, n: usize) -> PatrolIn {
    PatrolIn {
        callsign: callsign.into(),
        side: Side::West,
        units: vec![UnitIn::new(Rifleman, &format!("{callsign}-1"), x, 1000.0, Sergeant)],
        route: (0..n).map(|i| Point::new(x + 100.0 * (i + 1) as f64, 1000.0)).collect(),
    }
}

/// Two groups with their routes and one synchronisation.
#[test]
fn visible_two_groups_one_sync() {
    let input = Input {
        groups: vec![patrol("Alpha", 1000.0, 2), patrol("Bravo", 3000.0, 2)],
        first: WaypointNo { callsign: "Alpha".into(), number: 1 },
        second: WaypointNo { callsign: "Bravo".into(), number: 1 },
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.groups.len(), 2);
    assert_eq!(doc.syncs.len(), 1);
}
