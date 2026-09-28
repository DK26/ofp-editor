use mb_oracle::near;
use mb_spec::t14::Input;
use mb_spec::{Point, Rank::*, Refusal, UnitClass::*, UnitIn};

fn base(seconds: [f64; 3]) -> Input {
    Input {
        units: vec![
            UnitIn::new(Rifleman, "h1", 2000.0, 9000.0, Sergeant),
            UnitIn::new(Medic, "h2", 2004.0, 9000.0, Private),
        ],
        post: Point::new(2100.0, 9100.0),
        post_half_m: 150.0,
        seconds,
    }
}

/// Longest/shortest/typical 90/30/60 becomes a TIMEOUT of 30/60/90 s.
#[test]
fn nominal_reordered_timeout() {
    let doc = mb_oracle::accept(&task::run(&base([90.0, 30.0, 60.0])).expect("valid input refused"));
    let (kind, lo, md, hi) = doc.triggers[0].timer.clone().expect("timer");
    assert_eq!(kind, "TIMEOUT");
    assert!(near(lo, 30.0) && near(md, 60.0) && near(hi, 90.0), "{lo}/{md}/{hi}");
}

/// West presence at the post ends the mission with ending 3, once.
#[test]
fn nominal_presence_end_three() {
    let doc = mb_oracle::accept(&task::run(&base([90.0, 30.0, 60.0])).expect("valid input refused"));
    let t = doc.triggers_with_act(&["PRESENT", "WEST"]);
    assert_eq!(t.len(), 1);
    assert_eq!(t[0].effect, "END 3");
    assert_eq!(t[0].repeat, "ONCE");
}

/// A negative duration is refused with TimerOrder.
#[test]
fn trap_timer_order_negative() {
    assert_eq!(task::run(&base([90.0, -5.0, 60.0])), Err(Refusal::TimerOrder));
}

/// A typical duration above the longest is refused with TimerOrder.
#[test]
fn trap_timer_order_typical_above_longest() {
    assert_eq!(task::run(&base([90.0, 30.0, 120.0])), Err(Refusal::TimerOrder));
}

/// A shortest duration above the longest is refused with TimerOrder.
#[test]
fn trap_timer_order_shortest_above_longest() {
    assert_eq!(task::run(&base([30.0, 90.0, 60.0])), Err(Refusal::TimerOrder));
}

/// Three equal durations are consistent.
#[test]
fn edge_equal_durations() {
    let doc = mb_oracle::accept(&task::run(&base([45.0, 45.0, 45.0])).expect("valid input refused"));
    let (_, lo, md, hi) = doc.triggers[0].timer.clone().expect("timer");
    assert!(near(lo, 45.0) && near(md, 45.0) && near(hi, 45.0));
}
