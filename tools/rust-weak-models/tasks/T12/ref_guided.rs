use mb::{Exported, Mission, Pos, Rank, UnitId};
use mb_spec::Refusal;
use mb_spec::t12::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    for grp in &input.groups {
        let g = m.add_group(grp.side, &grp.callsign).map_err(|_| Refusal::DuplicateCallsign)?;
        let mut best: Option<(UnitId, Rank)> = None;
        for u in &grp.units {
            let pos = Pos::new(u.pos.x, u.pos.z).map_err(|_| Refusal::OutOfMap)?;
            let id = m.add_unit(g, u.class, &u.label, pos, u.rank);
            let better = match best {
                None => true,
                Some((_, r)) => u.rank > r,
            };
            if !u.class.is_vehicle() && better {
                best = Some((id, u.rank));
            }
        }
        let (leader, _) = best.ok_or(Refusal::EmptyGroup)?;
        m.set_leader(g, leader).map_err(|_| Refusal::EmptyGroup)?;
    }
    let m = m.validate().map_err(|_| Refusal::EmptyGroup)?;
    Ok(m.export())
}
