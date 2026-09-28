use mb_spec::t22::{Input, PlacedIn};
use mb_spec::{Point, Rank::*, UnitClass::*};

/// Two units are placed around the anchor.
#[test]
fn visible_two_units() {
    let input = Input {
        anchor: Point::new(6400.0, 6400.0),
        units: vec![
            PlacedIn { class: Rifleman, label: "n".into(), rank: Sergeant, bearing_deg: 0.0, distance_km: 0.0 },
            PlacedIn { class: Rifleman, label: "m".into(), rank: Private, bearing_deg: 0.0, distance_km: 0.0 },
        ],
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.group("Ring").units.len(), 2);
}
