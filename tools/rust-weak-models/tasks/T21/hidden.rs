use mb_oracle::near;
use mb_spec::t21::Input;
use mb_spec::{Ending, Radio, Rank::*, UnitClass::*, UnitIn};

fn base(win_channel: Radio, win_ending: Ending) -> Input {
    Input {
        units: vec![
            UnitIn::new(Rifleman, "p1", 6000.0, 6000.0, Lieutenant),
            UnitIn::new(Medic, "p2", 6004.0, 6000.0, Private),
        ],
        win_channel,
        win_ending,
    }
}

/// The loss fires when no West units are present (NOT_PRESENT, not PRESENT).
#[test]
fn trap_act_rule_loss_on_not_present() {
    let doc = mb_oracle::accept(&task::run(&base(Radio::Alpha, Ending::One)).expect("valid input refused"));
    let t = doc.triggers_with_act(&["NOT_PRESENT", "WEST"]);
    assert_eq!(t.len(), 1, "{:?}", doc.triggers);
    assert_eq!(t[0].effect, "LOSE");
}

/// The win: radio channel and ending from the input.
#[test]
fn nominal_win_on_radio() {
    let doc = mb_oracle::accept(&task::run(&base(Radio::Hotel, Ending::Six)).expect("valid input refused"));
    let t = doc.triggers_with_act(&["RADIO", "HOTEL"]);
    assert_eq!(t.len(), 1);
    assert_eq!(t[0].effect, "END 6");
}

/// Neither trigger repeats.
#[test]
fn trap_act_rule_neither_repeats() {
    let doc = mb_oracle::accept(&task::run(&base(Radio::Alpha, Ending::One)).expect("valid input refused"));
    assert_eq!(doc.triggers.len(), 2);
    assert!(doc.triggers.iter().all(|t| t.repeat == "ONCE"));
}

/// Both triggers cover the whole map.
#[test]
fn nominal_whole_map() {
    let doc = mb_oracle::accept(&task::run(&base(Radio::Alpha, Ending::One)).expect("valid input refused"));
    for t in &doc.triggers {
        assert!(near(t.area[0], 6400.0) && near(t.area[1], 6400.0) && t.area[2] >= 6399.9 && t.area[3] >= 6399.9, "{:?}", t.area);
    }
}
