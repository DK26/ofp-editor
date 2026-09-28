use mb_oracle::near;
use mb_spec::t29::{Input, WaveIn};
use mb_spec::{Point, Radio, Rank::*, Refusal, UnitClass::*, UnitIn};

fn wave(callsign: &str, x: f64, vehicle_class: mb_spec::UnitClass, vehicle: &str) -> WaveIn {
    WaveIn {
        callsign: callsign.into(),
        units: vec![
            UnitIn::new(Rifleman, &format!("{callsign}-1"), x, 1000.0, Sergeant),
            UnitIn::new(vehicle_class, &format!("{callsign}-car"), x + 10.0, 1000.0, Private),
            UnitIn::new(Rifleman, &format!("{callsign}-2"), x + 4.0, 1000.0, Private),
        ],
        vehicle: vehicle.into(),
    }
}

fn base() -> Input {
    Input {
        first: wave("Red", 1000.0, Truck, "Red-car"),
        second: wave("Blue", 1100.0, Apc, "Blue-car"),
        route: vec![Point::new(3000.0, 3000.0), Point::new(4000.0, 3500.0)],
        release: Radio::Foxtrot,
        delay_s: 60.0,
    }
}

fn syncs_to(doc: &mb_oracle::Doc, callsign: &str) -> Vec<usize> {
    (0..doc.triggers.len()).filter(|i| doc.trigger_syncs(*i).iter().any(|(c, w)| c == callsign && *w == 0)).collect()
}

/// Each wave boards its own vehicle, then follows the route.
#[test]
fn trap_id_mix_own_vehicle() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    assert_eq!(doc.boarded_label("Red", 0), "Red-car");
    assert_eq!(doc.boarded_label("Blue", 0), "Blue-car");
    assert_eq!(doc.kinds("Blue"), ["GET_IN", "MOVE", "MOVE"]);
}

/// The first wave's trigger has no timer; the second's counts down exactly the delay.
#[test]
fn nominal_release_timers() {
    let doc = mb_oracle::accept(&task::run(&base()).expect("valid input refused"));
    let first = syncs_to(&doc, "Red");
    let second = syncs_to(&doc, "Blue");
    assert_eq!((first.len(), second.len()), (1, 1), "{:?}", doc.triggers);
    assert!(doc.triggers[first[0]].timer.is_none());
    let (kind, lo, md, hi) = doc.triggers[second[0]].timer.clone().expect("timer");
    assert_eq!(kind, "COUNTDOWN");
    assert!(near(lo, 60.0) && near(md, 60.0) && near(hi, 60.0));
    assert!(doc.triggers.iter().all(|t| t.act == ["RADIO", "FOXTROT"] && t.repeat == "ONCE"));
}

/// A missing second vehicle is refused with UnknownVehicle.
#[test]
fn trap_ref_vehicle_second_missing() {
    let mut input = base();
    input.second.vehicle = "Blue-bike".into();
    assert_eq!(task::run(&input), Err(Refusal::UnknownVehicle));
}

/// A vehicle label that names a soldier is refused with UnknownVehicle.
#[test]
fn trap_ref_vehicle_label_is_soldier() {
    let mut input = base();
    input.first.vehicle = "Red-2".into();
    assert_eq!(task::run(&input), Err(Refusal::UnknownVehicle));
}
