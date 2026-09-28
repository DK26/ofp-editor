use mb_spec::t20::{Input, LateTrigger};
use mb_spec::{Ending, Point, Radio, Rank::*, UnitClass::*, UnitIn};

/// The patrol and the late trigger are both exported.
#[test]
fn visible_patrol_and_late_trigger() {
    let input = Input {
        units: vec![UnitIn::new(Rifleman, "a1", 1000.0, 8000.0, Sergeant)],
        patrol: vec![Point::new(1100.0, 8000.0), Point::new(1100.0, 8100.0)],
        late: LateTrigger { channel: Radio::Echo, ending: Ending::Four, min_s: 10.0, mid_s: 20.0, max_s: 30.0 },
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.group("Alpha").units.len(), 1);
    assert_eq!(doc.triggers.len(), 1);
}
