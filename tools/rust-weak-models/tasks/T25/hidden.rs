use mb_spec::t25::{Entry, Input};
use mb_spec::{Problem, Rank::*, Refusal, Side, UnitClass::*, UnitIn};

fn entry(callsign: &str, units: &[(&str, f64, f64)]) -> Entry {
    Entry {
        callsign: callsign.into(),
        units: units.iter().map(|(l, x, z)| UnitIn::new(Rifleman, l, *x, *z, Private)).collect(),
    }
}

fn roster(entries: Vec<Entry>) -> Input {
    Input { side: Side::Resistance, roster: entries }
}

/// A clean roster exports every group.
#[test]
fn nominal_clean_roster() {
    let input = roster(vec![entry("Kilo", &[("k1", 1000.0, 1000.0)]), entry("Lima", &[("l1", 2000.0, 1000.0), ("l2", 2004.0, 1000.0)])]);
    let doc = mb_oracle::accept(&task::run(&input).expect("valid input refused"));
    assert_eq!(doc.callsigns(), ["Kilo", "Lima"]);
    assert!(doc.groups.iter().all(|g| g.side == "RESISTANCE"));
}

/// Every problem is reported, sorted, not just the first.
#[test]
fn trap_err_handling_all_problems_sorted() {
    let input = roster(vec![
        entry("Kilo", &[("k1", 1000.0, 1000.0), ("k2", 13_000.0, 1000.0)]),
        entry("Lima", &[]),
        entry("Kilo", &[("k3", 1100.0, 1000.0)]),
        entry("Mike", &[("m1", 1200.0, -3.0)]),
    ]);
    let expected = vec![
        Problem::DuplicateCallsign("Kilo".into()),
        Problem::EmptyGroup("Lima".into()),
        Problem::OutOfMap("k2".into()),
        Problem::OutOfMap("m1".into()),
    ];
    assert_eq!(task::run(&input), Err(Refusal::Many(expected)));
}

/// A single problem is still reported as `Many` with one item.
#[test]
fn trap_err_handling_single_problem() {
    let input = roster(vec![entry("Kilo", &[("k1", 1000.0, 1000.0)]), entry("Lima", &[])]);
    assert_eq!(task::run(&input), Err(Refusal::Many(vec![Problem::EmptyGroup("Lima".into())])));
}

/// An entry that is both a duplicate and empty gives both problems.
#[test]
fn trap_err_handling_duplicate_and_empty() {
    let input = roster(vec![entry("Kilo", &[("k1", 1000.0, 1000.0)]), entry("Kilo", &[])]);
    let expected = vec![Problem::DuplicateCallsign("Kilo".into()), Problem::EmptyGroup("Kilo".into())];
    assert_eq!(task::run(&input), Err(Refusal::Many(expected)));
}

/// Problems are sorted by the derived order, not by roster order.
#[test]
fn trap_seq_export_sorted_not_input_order() {
    let input = roster(vec![
        entry("Zulu", &[("z1", 20_000.0, 1.0)]),
        entry("Yankee", &[]),
        entry("Alpha", &[("a1", 1.0, 1.0)]),
        entry("Alpha", &[("a2", 2.0, 2.0)]),
    ]);
    let expected = vec![
        Problem::DuplicateCallsign("Alpha".into()),
        Problem::EmptyGroup("Yankee".into()),
        Problem::OutOfMap("z1".into()),
    ];
    assert_eq!(task::run(&input), Err(Refusal::Many(expected)));
}
