use mb_oracle::near;
use mb_spec::p03::Input;
use mb_spec::{Point, Rank::*, UnitClass::*, UnitIn};

fn base() -> Input {
    Input {
        units: vec![
            UnitIn::new(Rifleman, "b1", 8000.0, 8000.0, Private),
            UnitIn::new(Officer, "b2", 8010.0, 8000.0, Lieutenant),
        ],
        base: Point::new(8020.0, 7990.0),
        half_size_m: 250.0,
    }
}

/// The alarm fires on East presence and ends the mission with ending 1.
#[test]
fn nominal_alarm_semantics() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    let alarms = doc.triggers_with_act(&["PRESENT", "EAST"]);
    assert_eq!(alarms.len(), 1, "one East-presence trigger");
    assert_eq!(alarms[0].effect, "END 1");
}

/// The trigger fires once (an ending trigger must not repeat).
#[test]
fn trap_act_rule_fires_once() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    assert_eq!(doc.triggers[0].repeat, "ONCE");
}

/// The area is the square around the base, unrotated.
#[test]
fn nominal_area() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    let a = doc.triggers[0].area;
    assert!(near(a[0], 8020.0) && near(a[1], 7990.0), "centre {a:?}");
    assert!(near(a[2], 250.0) && near(a[3], 250.0) && near(a[4], 0.0), "size {a:?}");
}
