use mb_oracle::near;
use mb_spec::t20::{Input, LateTrigger};
use mb_spec::{Ending, Point, Radio, Rank::*, Refusal, UnitClass::*, UnitIn};

fn base(min_s: f64, mid_s: f64, max_s: f64) -> Input {
    Input {
        units: vec![
            UnitIn::new(Rifleman, "a1", 1500.0, 9000.0, Sergeant),
            UnitIn::new(Rifleman, "a2", 1504.0, 9000.0, Private),
        ],
        patrol: vec![Point::new(1600.0, 9000.0), Point::new(1600.0, 9100.0), Point::new(1500.0, 9100.0)],
        late: LateTrigger { channel: Radio::Golf, ending: Ending::Five, min_s, mid_s, max_s },
    }
}

/// The late trigger: radio Golf, countdown 30/45/60 s, ending 5, once.
#[test]
fn nominal_late_trigger() {
    let doc = mb_oracle::accept(&task::run(&base(30.0, 45.0, 60.0)).expect("valid input refused"));
    let t = doc.triggers_with_act(&["RADIO", "GOLF"]);
    assert_eq!(t.len(), 1);
    assert_eq!(t[0].effect, "END 5");
    let (kind, lo, md, hi) = t[0].timer.clone().expect("timer");
    assert_eq!(kind, "COUNTDOWN");
    assert!(near(lo, 30.0) && near(md, 45.0) && near(hi, 60.0));
}

/// The patrol loop is intact in the final export.
#[test]
fn nominal_patrol_loop() {
    let doc = mb_oracle::accept(&task::run(&base(30.0, 45.0, 60.0)).expect("valid input refused"));
    assert_eq!(doc.kinds("Alpha"), ["MOVE", "MOVE", "MOVE", "CYCLE"]);
}

/// An out-of-order late timer is refused, never exported: the late addition is
/// checked like the rest of the mission.
#[test]
fn trap_seq_export_late_timer_out_of_order() {
    assert_eq!(task::run(&base(90.0, 60.0, 120.0)), Err(Refusal::TimerOrder));
}

/// A negative late timer value is refused with TimerOrder.
#[test]
fn trap_timer_order_negative() {
    assert_eq!(task::run(&base(-1.0, 45.0, 60.0)), Err(Refusal::TimerOrder));
}

/// A zero-length countdown is consistent.
#[test]
fn edge_zero_countdown() {
    let doc = mb_oracle::accept(&task::run(&base(0.0, 0.0, 0.0)).expect("valid input refused"));
    assert_eq!(doc.triggers.len(), 1);
}
