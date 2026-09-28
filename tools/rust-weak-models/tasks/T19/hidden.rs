use mb_spec::t19::{DraftIn, Input, PatrolIn, SyncIn};
use mb_spec::{Point, Rank::*, Side, UnitClass::*, UnitIn};

fn patrol(callsign: &str, x: f64, n: usize) -> PatrolIn {
    PatrolIn {
        callsign: callsign.into(),
        side: Side::West,
        units: vec![UnitIn::new(Rifleman, &format!("{callsign}{x}"), x, 6000.0, Sergeant)],
        route: (0..n).map(|i| Point::new(x + 100.0 * (i + 1) as f64, 6000.0)).collect(),
    }
}

fn sync(group_a: usize, wp_a: usize, group_b: usize, wp_b: usize) -> SyncIn {
    SyncIn { group_a, wp_a, group_b, wp_b }
}

fn no_clash() -> Input {
    Input {
        first: DraftIn { groups: vec![patrol("Alpha", 1000.0, 3), patrol("Bravo", 2000.0, 3)], syncs: vec![sync(0, 1, 1, 2)] },
        second: DraftIn { groups: vec![patrol("Charlie", 3000.0, 2), patrol("Delta", 4000.0, 3)], syncs: vec![sync(1, 2, 0, 1)] },
    }
}

fn clash() -> Input {
    Input {
        first: DraftIn { groups: vec![patrol("Alpha", 1000.0, 3), patrol("Bravo", 2000.0, 3)], syncs: vec![sync(0, 0, 1, 0)] },
        second: DraftIn { groups: vec![patrol("Alpha", 5000.0, 3), patrol("Echo", 6000.0, 3)], syncs: vec![sync(0, 2, 1, 1)] },
    }
}

/// Groups of both drafts, first draft first.
#[test]
fn nominal_groups_in_order() {
    let doc = mb_oracle::accept(&task::run(&no_clash()).expect("valid input refused"));
    assert_eq!(doc.callsigns(), ["Alpha", "Bravo", "Charlie", "Delta"]);
    assert_eq!(doc.kinds("Delta"), ["MOVE", "MOVE", "MOVE"]);
}

/// The first draft's sync connects Alpha:1 and Bravo:2.
#[test]
fn nominal_first_draft_sync() {
    let doc = mb_oracle::accept(&task::run(&no_clash()).expect("valid input refused"));
    assert!(doc.synced(("Alpha", 1), ("Bravo", 2)), "{:?}", doc.syncs);
}

/// The second draft's positions refer to its own groups (Delta:2 with Charlie:1),
/// not to the first draft's groups at the same positions.
#[test]
fn trap_id_mix_second_draft_positions() {
    let doc = mb_oracle::accept(&task::run(&no_clash()).expect("valid input refused"));
    assert!(doc.synced(("Delta", 2), ("Charlie", 1)), "{:?}", doc.syncs);
    assert_eq!(doc.syncs.len(), 2);
}

/// A clashing callsign of the second draft becomes "Alpha-2".
#[test]
fn nominal_rename_on_clash() {
    let doc = mb_oracle::accept(&task::run(&clash()).expect("valid input refused"));
    assert_eq!(doc.callsigns(), ["Alpha", "Bravo", "Alpha-2", "Echo"]);
}

/// The renamed group's sync points at "Alpha-2", not at the first draft's "Alpha".
#[test]
fn trap_ref_sync_renamed_group() {
    let doc = mb_oracle::accept(&task::run(&clash()).expect("valid input refused"));
    assert!(doc.synced(("Alpha-2", 2), ("Echo", 1)), "{:?}", doc.syncs);
    assert!(doc.synced(("Alpha", 0), ("Bravo", 0)), "{:?}", doc.syncs);
    assert_eq!(doc.syncs.len(), 2);
}
