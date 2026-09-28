use mb::{Exported, MAP_SIZE, Mission};
use mb_spec::t25::Input;
use mb_spec::{Problem, Refusal};

fn on_map(x: f64, z: f64) -> bool {
    (0.0..=MAP_SIZE).contains(&x) && (0.0..=MAP_SIZE).contains(&z)
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    // Collect every problem first.
    let mut problems = Vec::new();
    let mut seen: Vec<&str> = Vec::new();
    for e in &input.roster {
        if seen.contains(&e.callsign.as_str()) {
            problems.push(Problem::DuplicateCallsign(e.callsign.clone()));
        }
        seen.push(&e.callsign);
        if e.units.is_empty() {
            problems.push(Problem::EmptyGroup(e.callsign.clone()));
        }
        for u in &e.units {
            if !on_map(u.pos.x, u.pos.z) {
                problems.push(Problem::OutOfMap(u.label.clone()));
            }
        }
    }
    if !problems.is_empty() {
        problems.sort();
        return Err(Refusal::Many(problems));
    }
    let mut m = Mission::new();
    for e in &input.roster {
        let g = m.add_group(input.side, &e.callsign).map_err(|_| Refusal::DuplicateCallsign)?;
        for u in &e.units {
            m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
        }
    }
    m.validate().map_err(|_| Refusal::EmptyGroup)?;
    Ok(m.export())
}
