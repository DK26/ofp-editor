use mb_spec::t10::Input;
use mb_spec::{Point, Rank::*, Refusal, Side, UnitClass::*, UnitIn};

fn base(watcher: Side, watched: Side) -> Input {
    Input {
        units: vec![
            UnitIn::new(Rifleman, "s1", 3000.0, 3000.0, Corporal),
            UnitIn::new(Rifleman, "s2", 3004.0, 3000.0, Private),
        ],
        watcher,
        watched,
        area: Point::new(3200.0, 3200.0),
        area_half_m: 600.0,
    }
}

/// DETECTED_BY names the detector (watcher) first and the detected (watched) side second.
#[test]
fn trap_act_rule_detector_order() {
    let doc = mb_oracle::accept(&task::run(&base(Side::East, Side::West)).expect("valid input refused"));
    assert_eq!(doc.triggers.len(), 1);
    assert_eq!(doc.triggers[0].act, ["DETECTED_BY", "EAST", "WEST"]);
}

/// Other sides: Resistance watches East.
#[test]
fn nominal_other_sides() {
    let doc = mb_oracle::accept(&task::run(&base(Side::Resistance, Side::East)).expect("valid input refused"));
    assert_eq!(doc.triggers[0].act, ["DETECTED_BY", "RESISTANCE", "EAST"]);
    assert_eq!(doc.group("Scouts").side, "EAST");
}

/// Detection loses the mission, once.
#[test]
fn nominal_lose_once() {
    let doc = mb_oracle::accept(&task::run(&base(Side::East, Side::West)).expect("valid input refused"));
    assert_eq!(doc.triggers[0].effect, "LOSE");
    assert_eq!(doc.triggers[0].repeat, "ONCE");
}

/// Equal sides are refused with SameSide.
#[test]
fn trap_act_rule_same_side() {
    assert_eq!(task::run(&base(Side::West, Side::West)), Err(Refusal::SameSide));
}
