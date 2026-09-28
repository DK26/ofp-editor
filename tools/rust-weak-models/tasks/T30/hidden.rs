use mb_oracle::near;
use mb_spec::t30::{ActIn, EffectIn, GroupIn, Input, OrderIn, PlanIn, TriggerIn};
use mb_spec::{Ending, Point, Radio, Rank::*, Refusal, Side, UnitClass::*, UnitIn};

fn p(x: f64, z: f64) -> Point {
    Point::new(x, z)
}

fn trigger(centre: Point, half_m: f64, act: ActIn, effect: EffectIn, sync: Option<(&str, usize)>) -> TriggerIn {
    TriggerIn {
        centre,
        half_m,
        act,
        repeating: false,
        countdown_s: None,
        effect,
        sync: sync.map(|(c, n)| (c.to_string(), n)),
    }
}

/// The valid brief every hidden variant starts from.
fn brief() -> Input {
    Input {
        groups: vec![
            GroupIn {
                callsign: "Alpha".into(),
                side: Side::West,
                units: vec![
                    UnitIn::new(Rifleman, "a1", 2000.0, 2000.0, Sergeant),
                    UnitIn::new(Rifleman, "a2", 2004.0, 2000.0, Private),
                    UnitIn::new(Truck, "a-truck", 2010.0, 2000.0, Private),
                ],
            },
            GroupIn {
                callsign: "Bravo".into(),
                side: Side::West,
                units: vec![UnitIn::new(Rifleman, "b1", 3000.0, 2000.0, Sergeant), UnitIn::new(Medic, "b2", 3004.0, 2000.0, Private)],
            },
            GroupIn {
                callsign: "Viper".into(),
                side: Side::East,
                units: vec![UnitIn::new(Rifleman, "v1", 9000.0, 9000.0, Sergeant), UnitIn::new(Jeep, "v-jeep", 9010.0, 9000.0, Private)],
            },
        ],
        plans: vec![
            PlanIn {
                callsign: "Alpha".into(),
                orders: vec![
                    OrderIn::Board("a-truck".into()),
                    OrderIn::Move(p(2500.0, 2500.0)),
                    OrderIn::Dismount(p(2500.0, 2500.0)),
                    OrderIn::Hunt(p(2800.0, 2800.0)),
                ],
            },
            PlanIn { callsign: "Bravo".into(), orders: vec![OrderIn::Move(p(3100.0, 2000.0)), OrderIn::Move(p(3100.0, 2200.0)), OrderIn::Loop] },
            PlanIn { callsign: "Viper".into(), orders: vec![OrderIn::Move(p(8800.0, 8800.0)), OrderIn::Hold(p(8700.0, 8700.0))] },
        ],
        triggers: vec![
            TriggerIn { countdown_s: Some([30.0, 60.0, 90.0]), ..trigger(p(2800.0, 2800.0), 200.0, ActIn::Present(Side::West), EffectIn::End(Ending::One), None) },
            trigger(p(6400.0, 6400.0), 6400.0, ActIn::Radio(Radio::Alpha), EffectIn::None, Some(("Alpha", 1))),
            trigger(p(9000.0, 9000.0), 300.0, ActIn::DetectedBy { watcher: Side::East, watched: Side::West }, EffectIn::Lose, None),
            TriggerIn { repeating: true, ..trigger(p(3000.0, 2000.0), 100.0, ActIn::NotPresent(Side::East), EffectIn::None, Some(("Bravo", 2))) },
        ],
    }
}

/// The valid brief exports every element faithfully.
#[test]
fn nominal_valid_brief() {
    let doc = mb_oracle::accept(&task::run(&brief()).expect("valid input refused"));
    assert_eq!(doc.kinds("Alpha"), ["GET_IN", "MOVE", "GET_OUT", "SEEK_AND_DESTROY"]);
    assert_eq!(doc.kinds("Bravo"), ["MOVE", "MOVE", "CYCLE"]);
    assert_eq!(doc.kinds("Viper"), ["MOVE", "HOLD"]);
    assert_eq!(doc.triggers.len(), 4);
    let (kind, lo, md, hi) = doc.triggers[0].timer.clone().expect("timer");
    assert!(kind == "COUNTDOWN" && near(lo, 30.0) && near(md, 60.0) && near(hi, 90.0));
    assert_eq!(doc.triggers[0].effect, "END 1");
    assert_eq!(doc.trigger_syncs(1), vec![("Alpha".to_string(), 0)]);
    assert_eq!(doc.triggers[2].act, ["DETECTED_BY", "EAST", "WEST"]);
    assert_eq!(doc.triggers[2].effect, "LOSE");
    assert_eq!(doc.triggers[3].repeat, "REPEATEDLY");
    assert_eq!(doc.trigger_syncs(3), vec![("Bravo".to_string(), 1)]);
}

/// A group without units: EmptyGroup.
#[test]
fn trap_empty_group() {
    let mut b = brief();
    b.groups[1].units.clear();
    assert_eq!(task::run(&b), Err(Refusal::EmptyGroup));
}

/// An order point off the map: OutOfMap.
#[test]
fn trap_bounds_order_point() {
    let mut b = brief();
    b.plans[1].orders[1] = OrderIn::Move(p(3100.0, 13_000.0));
    assert_eq!(task::run(&b), Err(Refusal::OutOfMap));
}

/// A trigger centre off the map: OutOfMap.
#[test]
fn trap_bounds_trigger_centre() {
    let mut b = brief();
    b.triggers[2].centre = p(-50.0, 9000.0);
    assert_eq!(task::run(&b), Err(Refusal::OutOfMap));
}

/// A plan for a callsign that is not a group: UnknownGroup.
#[test]
fn trap_ref_sync_plan_unknown_group() {
    let mut b = brief();
    b.plans[2].callsign = "Cobra".into();
    assert_eq!(task::run(&b), Err(Refusal::UnknownGroup));
}

/// A sync to a callsign that is not a group: UnknownGroup.
#[test]
fn trap_ref_sync_unknown_callsign() {
    let mut b = brief();
    b.triggers[1].sync = Some(("Zulu".into(), 1));
    assert_eq!(task::run(&b), Err(Refusal::UnknownGroup));
}

/// A sync to a waypoint number the plan does not have: UnknownGroup.
#[test]
fn trap_ref_sync_missing_waypoint() {
    let mut b = brief();
    b.triggers[3].sync = Some(("Bravo".into(), 7));
    assert_eq!(task::run(&b), Err(Refusal::UnknownGroup));
}

/// Boarding a label that is not a vehicle: UnknownVehicle.
#[test]
fn trap_ref_vehicle_unknown_label() {
    let mut b = brief();
    b.plans[0].orders[0] = OrderIn::Board("a-tank".into());
    assert_eq!(task::run(&b), Err(Refusal::UnknownVehicle));
}

/// Boarding the enemy's jeep: WrongSide.
#[test]
fn trap_ref_vehicle_wrong_side() {
    let mut b = brief();
    b.plans[0].orders[0] = OrderIn::Board("v-jeep".into());
    assert_eq!(task::run(&b), Err(Refusal::WrongSide));
}

/// Dismount with no Board before it: InvalidSequence.
#[test]
fn trap_seq_mount_dismount_without_board() {
    let mut b = brief();
    b.plans[2].orders.insert(0, OrderIn::Dismount(p(8900.0, 8900.0)));
    assert_eq!(task::run(&b), Err(Refusal::InvalidSequence));
}

/// An order after Loop: InvalidSequence.
#[test]
fn trap_seq_cycle_order_after_loop() {
    let mut b = brief();
    b.plans[1].orders.push(OrderIn::Move(p(3200.0, 2000.0)));
    assert_eq!(task::run(&b), Err(Refusal::InvalidSequence));
}

/// An inconsistent countdown: TimerOrder.
#[test]
fn trap_timer_order_countdown() {
    let mut b = brief();
    b.triggers[0].countdown_s = Some([90.0, 60.0, 30.0]);
    assert_eq!(task::run(&b), Err(Refusal::TimerOrder));
}

/// A side detected by itself: SameSide.
#[test]
fn trap_act_rule_same_side() {
    let mut b = brief();
    b.triggers[2].act = ActIn::DetectedBy { watcher: Side::West, watched: Side::West };
    assert_eq!(task::run(&b), Err(Refusal::SameSide));
}

/// A repeating ending: RepeatingEnd.
#[test]
fn trap_act_rule_repeating_end() {
    let mut b = brief();
    b.triggers[0].repeating = true;
    assert_eq!(task::run(&b), Err(Refusal::RepeatingEnd));
}
