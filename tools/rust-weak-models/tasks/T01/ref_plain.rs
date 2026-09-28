use mb::{Exported, Mission, Rank, Side};
use mb_spec::Refusal;
use mb_spec::t01::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Alpha").map_err(|_| Refusal::DuplicateCallsign)?;
    let mut leader = None;
    for u in &input.units {
        let id = m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
        if u.rank == Rank::Sergeant && leader.is_none() {
            leader = Some(id);
        }
    }
    if let Some(id) = leader {
        m.set_leader(g, id).map_err(|_| Refusal::EmptyGroup)?;
    }
    m.validate().map_err(|_| Refusal::EmptyGroup)?;
    Ok(m.export())
}
