use mb::{Exported, Mission, Pos};
use mb_spec::t25::Input;
use mb_spec::{Problem, Refusal};

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    // Build what can be built and collect every problem on the way.
    let mut problems = Vec::new();
    let mut m = Mission::new();
    for e in &input.roster {
        let group = match m.add_group(input.side, &e.callsign) {
            Ok(g) => Some(g),
            Err(_) => {
                problems.push(Problem::DuplicateCallsign(e.callsign.clone()));
                None
            }
        };
        if e.units.is_empty() {
            problems.push(Problem::EmptyGroup(e.callsign.clone()));
        }
        for u in &e.units {
            match Pos::new(u.pos.x, u.pos.z) {
                Ok(pos) => {
                    if let Some(g) = group {
                        m.add_unit(g, u.class, &u.label, pos, u.rank);
                    }
                }
                Err(_) => problems.push(Problem::OutOfMap(u.label.clone())),
            }
        }
    }
    if !problems.is_empty() {
        problems.sort();
        return Err(Refusal::Many(problems));
    }
    let m = m.validate().map_err(|_| Refusal::EmptyGroup)?;
    Ok(m.export())
}
