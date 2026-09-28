use mb_oracle::near;
use mb_spec::t06::Input;
use mb_spec::{Point, Rank::*, UnitClass::*, UnitIn};

fn input(min: f64, typical: f64, max: f64) -> Input {
    Input {
        units: vec![
            UnitIn::new(Rifleman, "g1", 10000.0, 4000.0, Sergeant),
            UnitIn::new(AtSoldier, "g2", 10004.0, 4000.0, Private),
        ],
        zone: Point::new(10100.0, 4050.0),
        zone_half_m: 300.0,
        minutes_min: min,
        minutes_typical: typical,
        minutes_max: max,
    }
}

/// The countdown is stored in seconds: 1/2/3 minutes -> 60/120/180 s.
#[test]
fn trap_unit_measure_minutes_to_seconds() {
    let doc = mb_oracle::accept(&task::run(&input(1.0, 2.0, 3.0)).expect("valid input refused"));
    let (kind, lo, md, hi) = doc.triggers[0].timer.clone().expect("timer");
    assert_eq!(kind, "COUNTDOWN");
    assert!(near(lo, 60.0) && near(md, 120.0) && near(hi, 180.0), "{lo}/{md}/{hi}");
}

/// Fractional minutes convert too: 0.5/1.5/4 -> 30/90/240 s.
#[test]
fn trap_unit_measure_fractional_minutes() {
    let doc = mb_oracle::accept(&task::run(&input(0.5, 1.5, 4.0)).expect("valid input refused"));
    let (_, lo, md, hi) = doc.triggers[0].timer.clone().expect("timer");
    assert!(near(lo, 30.0) && near(md, 90.0) && near(hi, 240.0), "{lo}/{md}/{hi}");
}

/// West presence ends the mission with ending 2, once.
#[test]
fn trap_act_rule_presence_ending_once() {
    let doc = mb_oracle::accept(&task::run(&input(1.0, 2.0, 3.0)).expect("valid input refused"));
    let t = doc.triggers_with_act(&["PRESENT", "WEST"]);
    assert_eq!(t.len(), 1);
    assert_eq!(t[0].effect, "END 2");
    assert_eq!(t[0].repeat, "ONCE");
}

/// The zone is the square around `zone`, unrotated.
#[test]
fn nominal_zone_area() {
    let doc = mb_oracle::accept(&task::run(&input(1.0, 2.0, 3.0)).expect("valid input refused"));
    let a = doc.triggers[0].area;
    assert!(near(a[0], 10100.0) && near(a[1], 4050.0) && near(a[2], 300.0) && near(a[3], 300.0) && near(a[4], 0.0));
    assert_eq!(doc.group("Garrison").side, "EAST");
}
