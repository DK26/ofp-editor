use mb_oracle::near;
use mb_spec::t01::Input;
use mb_spec::{Rank::*, UnitClass::*, UnitIn};

fn squad() -> Input {
    Input {
        units: vec![
            UnitIn::new(Rifleman, "a1", 1200.0, 3400.0, Private),
            UnitIn::new(MachineGunner, "a2", 1210.0, 3400.0, Corporal),
            UnitIn::new(Rifleman, "a3", 1220.0, 3410.5, Sergeant),
            UnitIn::new(Medic, "a4", 1230.0, 3400.0, Private),
        ],
    }
}

/// Every unit keeps class, label, position and rank, in order, on side WEST.
#[test]
fn nominal_units_kept() {
    let doc = mb_oracle::accept(&task::run(&squad()).expect("valid input refused"));
    let g = doc.group("Alpha");
    assert_eq!(g.side, "WEST");
    let labels: Vec<&str> = g.units.iter().map(|u| u.label.as_str()).collect();
    assert_eq!(labels, ["a1", "a2", "a3", "a4"]);
    assert_eq!(g.units[1].class, "MACHINE_GUNNER");
    assert!(near(g.units[2].z, 3410.5));
    assert_eq!(g.units[2].rank, "SERGEANT");
}

/// The sergeant leads.
#[test]
fn nominal_sergeant_leads() {
    let doc = mb_oracle::accept(&task::run(&squad()).expect("valid input refused"));
    assert_eq!(doc.leader_label("Alpha"), "a3");
}

/// Only the Alpha group exists.
#[test]
fn nominal_one_group() {
    let doc = mb_oracle::accept(&task::run(&squad()).expect("valid input refused"));
    assert_eq!(doc.callsigns(), ["Alpha"]);
}

/// A squad of a single sergeant.
#[test]
fn edge_single_sergeant() {
    let input = Input { units: vec![UnitIn::new(Rifleman, "s", 500.0, 500.0, Sergeant)] };
    let doc = mb_oracle::accept(&task::run(&input).expect("valid input refused"));
    assert_eq!(doc.leader_label("Alpha"), "s");
}

/// The sergeant listed last still leads.
#[test]
fn edge_sergeant_last() {
    let mut input = squad();
    input.units.push(UnitIn::new(Rifleman, "boss", 1240.0, 3400.0, Sergeant));
    input.units[2].rank = Corporal;
    let doc = mb_oracle::accept(&task::run(&input).expect("valid input refused"));
    assert_eq!(doc.leader_label("Alpha"), "boss");
}
