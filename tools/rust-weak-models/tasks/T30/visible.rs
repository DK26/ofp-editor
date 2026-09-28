use mb_spec::t30::{ActIn, EffectIn, GroupIn, Input, OrderIn, PlanIn, TriggerIn};
use mb_spec::{Point, Radio, Rank::*, Side, UnitClass::*, UnitIn};

/// A small valid brief: one group, one plan, one trigger.
#[test]
fn visible_small_brief() {
    let input = Input {
        groups: vec![GroupIn {
            callsign: "Alpha".into(),
            side: Side::West,
            units: vec![UnitIn::new(Rifleman, "a1", 2000.0, 2000.0, Sergeant)],
        }],
        plans: vec![PlanIn {
            callsign: "Alpha".into(),
            orders: vec![OrderIn::Move(Point::new(2100.0, 2000.0)), OrderIn::Hold(Point::new(2200.0, 2000.0))],
        }],
        triggers: vec![TriggerIn {
            centre: Point::new(6400.0, 6400.0),
            half_m: 6400.0,
            act: ActIn::Radio(Radio::Alpha),
            repeating: false,
            countdown_s: None,
            effect: EffectIn::None,
            sync: Some(("Alpha".into(), 1)),
        }],
    };
    let text = task::run(&input).expect("solve refused a valid input");
    let doc = mb_oracle::parse(&text).expect("export parses");
    assert_eq!(doc.group("Alpha").wps.len(), 2);
    assert_eq!(doc.triggers.len(), 1);
}
