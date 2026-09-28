use mb_oracle::near;
use mb_spec::p01::Input;
use mb_spec::{Rank::*, UnitClass::*, UnitIn};

fn four() -> Input {
    Input {
        units: vec![
            UnitIn::new(Rifleman, "r1", 2000.0, 3000.0, Private),
            UnitIn::new(MachineGunner, "mg", 2010.0, 3000.0, Corporal),
            UnitIn::new(Medic, "doc", 2020.0, 3005.5, Private),
            UnitIn::new(Rifleman, "sgt", 2030.0, 3000.0, Sergeant),
        ],
    }
}

/// Every unit keeps its class, label, position and rank, in order, on side WEST.
#[test]
fn nominal_all_fields_kept() {
    let doc = mb_oracle::accept(&task::run(&four()).expect("valid input refused"));
    let g = doc.group("Fireteam");
    assert_eq!(g.side, "WEST");
    let labels: Vec<&str> = g.units.iter().map(|u| u.label.as_str()).collect();
    assert_eq!(labels, ["r1", "mg", "doc", "sgt"]);
    assert_eq!(g.units[1].class, "MACHINE_GUNNER");
    assert!(near(g.units[2].z, 3005.5));
    assert_eq!(g.units[3].rank, "SERGEANT");
}

/// Only one group is created.
#[test]
fn nominal_single_group() {
    let doc = mb_oracle::accept(&task::run(&four()).expect("valid input refused"));
    assert_eq!(doc.callsigns(), ["Fireteam"]);
}

/// The highest rank leads when nothing else is said.
#[test]
fn nominal_default_leader() {
    let doc = mb_oracle::accept(&task::run(&four()).expect("valid input refused"));
    assert_eq!(doc.leader_label("Fireteam"), "sgt");
}
