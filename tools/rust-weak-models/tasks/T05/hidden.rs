use mb_oracle::near;
use mb_spec::t05::Input;
use mb_spec::{Ending, Radio, Rank::*, UnitClass::*, UnitIn};

fn input(channel: Radio, ending: Ending) -> Input {
    Input {
        units: vec![
            UnitIn::new(Officer, "hq1", 1500.0, 1500.0, Major),
            UnitIn::new(Rifleman, "hq2", 1505.0, 1500.0, Private),
        ],
        channel,
        ending,
    }
}

/// Radio Alpha ends the mission with ending 1.
#[test]
fn nominal_radio_alpha_ending_one() {
    let doc = mb_oracle::accept(&task::run(&input(Radio::Alpha, Ending::One)).expect("valid input refused"));
    let t = doc.triggers_with_act(&["RADIO", "ALPHA"]);
    assert_eq!(t.len(), 1);
    assert_eq!(t[0].effect, "END 1");
}

/// Channel and ending come from the input.
#[test]
fn nominal_other_channel_and_ending() {
    let doc = mb_oracle::accept(&task::run(&input(Radio::Charlie, Ending::Three)).expect("valid input refused"));
    let t = doc.triggers_with_act(&["RADIO", "CHARLIE"]);
    assert_eq!(t.len(), 1);
    assert_eq!(t[0].effect, "END 3");
}

/// "Whenever" does not make the ending repeat: it fires once.
#[test]
fn trap_act_rule_fires_once() {
    let doc = mb_oracle::accept(&task::run(&input(Radio::Alpha, Ending::One)).expect("valid input refused"));
    assert_eq!(doc.triggers.len(), 1);
    assert_eq!(doc.triggers[0].repeat, "ONCE");
}

/// The trigger covers the whole map (centred, half sizes 6400 m).
#[test]
fn nominal_whole_map_area() {
    let doc = mb_oracle::accept(&task::run(&input(Radio::Alpha, Ending::One)).expect("valid input refused"));
    let a = doc.triggers[0].area;
    assert!(near(a[0], 6400.0) && near(a[1], 6400.0) && a[2] >= 6399.9 && a[3] >= 6399.9, "area {a:?}");
}
