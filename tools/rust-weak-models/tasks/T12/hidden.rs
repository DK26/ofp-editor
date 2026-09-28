use mb_spec::t12::{GroupIn, Input};
use mb_spec::{Rank::*, Side, UnitClass::*, UnitIn};

fn three_groups() -> Input {
    Input {
        groups: vec![
            GroupIn {
                callsign: "Alpha".into(),
                side: Side::West,
                units: vec![
                    UnitIn::new(Rifleman, "a1", 1000.0, 1000.0, Private),
                    UnitIn::new(Rifleman, "a2", 1004.0, 1000.0, Sergeant),
                    UnitIn::new(Medic, "a3", 1008.0, 1000.0, Corporal),
                ],
            },
            GroupIn {
                callsign: "Bravo".into(),
                side: Side::West,
                units: vec![
                    UnitIn::new(Truck, "b-truck", 2000.0, 1000.0, Captain),
                    UnitIn::new(Rifleman, "b1", 2004.0, 1000.0, Corporal),
                    UnitIn::new(Officer, "b2", 2008.0, 1000.0, Lieutenant),
                    UnitIn::new(Rifleman, "b3", 2012.0, 1000.0, Private),
                ],
            },
            GroupIn {
                callsign: "Charlie".into(),
                side: Side::East,
                units: vec![
                    UnitIn::new(Rifleman, "c1", 3000.0, 1000.0, Private),
                    UnitIn::new(Rifleman, "c2", 3004.0, 1000.0, Sergeant),
                    UnitIn::new(Apc, "c-apc", 3008.0, 1000.0, Major),
                    UnitIn::new(MachineGunner, "c3", 3012.0, 1000.0, Sergeant),
                ],
            },
        ],
    }
}

/// The highest-ranked soldier leads the first group.
#[test]
fn nominal_first_group_leader() {
    let doc = mb_oracle::accept(&task::run(&three_groups()).expect("valid input refused"));
    assert_eq!(doc.leader_label("Alpha"), "a2");
}

/// A higher-ranked vehicle never leads; in a later group the right unit is chosen
/// (unit numbering continues across groups).
#[test]
fn trap_id_mix_vehicle_skipped_in_second_group() {
    let doc = mb_oracle::accept(&task::run(&three_groups()).expect("valid input refused"));
    assert_eq!(doc.leader_label("Bravo"), "b2");
}

/// On a tie the soldier listed first leads (and the APC is skipped).
#[test]
fn trap_id_mix_tie_goes_to_first_listed() {
    let doc = mb_oracle::accept(&task::run(&three_groups()).expect("valid input refused"));
    assert_eq!(doc.leader_label("Charlie"), "c2");
}

/// Groups keep callsigns, sides and units.
#[test]
fn nominal_groups_kept() {
    let doc = mb_oracle::accept(&task::run(&three_groups()).expect("valid input refused"));
    assert_eq!(doc.callsigns(), ["Alpha", "Bravo", "Charlie"]);
    assert_eq!(doc.group("Charlie").side, "EAST");
    assert_eq!(doc.unit_count(), 11);
}
