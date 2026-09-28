use mb_spec::t11::{Entry, Input};
use mb_spec::{Rank::*, Refusal, Side, UnitClass::*, UnitIn};

fn entry(callsign: &str, n: usize, x: f64) -> Entry {
    let units = (0..n).map(|i| UnitIn::new(Rifleman, &format!("{callsign}{i}"), x + i as f64 * 4.0, 5000.0, Private)).collect();
    Entry { callsign: callsign.to_string(), units }
}

fn roster(entries: Vec<Entry>) -> Input {
    Input { side: Side::East, roster: entries }
}

/// Three entries become three East groups in roster order with their units.
#[test]
fn nominal_three_groups() {
    let input = roster(vec![entry("Kilo", 2, 1000.0), entry("Lima", 1, 2000.0), entry("Mike", 3, 3000.0)]);
    let doc = mb_oracle::accept(&task::run(&input).expect("valid input refused"));
    assert_eq!(doc.callsigns(), ["Kilo", "Lima", "Mike"]);
    assert_eq!(doc.group("Mike").units.len(), 3);
    assert!(doc.groups.iter().all(|g| g.side == "EAST"));
}

/// An entry without units is refused with EmptyGroup (not exported as an empty group).
#[test]
fn trap_empty_group_middle_entry() {
    let input = roster(vec![entry("Kilo", 2, 1000.0), entry("Lima", 0, 2000.0), entry("Mike", 1, 3000.0)]);
    assert_eq!(task::run(&input), Err(Refusal::EmptyGroup));
}

/// A repeated callsign is refused with DuplicateCallsign.
#[test]
fn trap_err_handling_duplicate() {
    let input = roster(vec![entry("Kilo", 2, 1000.0), entry("Lima", 1, 2000.0), entry("Kilo", 1, 3000.0)]);
    assert_eq!(task::run(&input), Err(Refusal::DuplicateCallsign));
}

/// The first problem in roster order wins: an empty entry before a duplicate.
#[test]
fn trap_err_handling_first_problem_wins() {
    let input = roster(vec![entry("Kilo", 1, 1000.0), entry("Lima", 0, 2000.0), entry("Kilo", 1, 3000.0)]);
    assert_eq!(task::run(&input), Err(Refusal::EmptyGroup));
}

/// A duplicate before an empty entry: DuplicateCallsign wins.
#[test]
fn trap_err_handling_duplicate_first() {
    let input = roster(vec![entry("Kilo", 1, 1000.0), entry("Kilo", 1, 2000.0), entry("Lima", 0, 3000.0)]);
    assert_eq!(task::run(&input), Err(Refusal::DuplicateCallsign));
}

/// The last entry being empty is still refused.
#[test]
fn trap_empty_group_last_entry() {
    let input = roster(vec![entry("Kilo", 1, 1000.0), entry("Lima", 0, 2000.0)]);
    assert_eq!(task::run(&input), Err(Refusal::EmptyGroup));
}
