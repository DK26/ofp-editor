use mb_oracle::near;
use mb_spec::t09::Input;
use mb_spec::{Point, Rank::*, Refusal, UnitClass::*, UnitIn};

fn base(repeating: bool) -> Input {
    Input {
        units: vec![
            UnitIn::new(Rifleman, "d1", 9000.0, 2000.0, Sergeant),
            UnitIn::new(MachineGunner, "d2", 9004.0, 2000.0, Private),
        ],
        town: Point::new(9100.0, 2200.0),
        town_half_m: 400.0,
        repeating,
    }
}

/// "Whenever" does not make an ending repeat: the trigger fires once.
#[test]
fn trap_act_rule_ending_fires_once() {
    let doc = mb_oracle::accept(&task::run(&base(false)).expect("valid input refused"));
    assert_eq!(doc.triggers.len(), 1);
    assert_eq!(doc.triggers[0].repeat, "ONCE");
}

/// East presence in the town ends the mission with ending 2.
#[test]
fn nominal_presence_ending_two() {
    let doc = mb_oracle::accept(&task::run(&base(false)).expect("valid input refused"));
    let t = doc.triggers_with_act(&["PRESENT", "EAST"]);
    assert_eq!(t.len(), 1);
    assert_eq!(t[0].effect, "END 2");
    let a = t[0].area;
    assert!(near(a[0], 9100.0) && near(a[1], 2200.0) && near(a[2], 400.0) && near(a[3], 400.0));
}

/// A brief asking for a repeating ending is refused with RepeatingEnd.
#[test]
fn trap_err_handling_repeating_flag() {
    assert_eq!(task::run(&base(true)), Err(Refusal::RepeatingEnd));
}
