use mb::{Exported, Mission, Pos};
use mb_spec::Refusal;
use mb_spec::t11::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    for e in &input.roster {
        let g = m.add_group(input.side, &e.callsign).map_err(|_| Refusal::DuplicateCallsign)?;
        if e.units.is_empty() {
            return Err(Refusal::EmptyGroup);
        }
        for u in &e.units {
            let pos = Pos::new(u.pos.x, u.pos.z).map_err(|_| Refusal::OutOfMap)?;
            m.add_unit(g, u.class, &u.label, pos, u.rank);
        }
    }
    let m = m.validate().map_err(|_| Refusal::EmptyGroup)?;
    Ok(m.export())
}
