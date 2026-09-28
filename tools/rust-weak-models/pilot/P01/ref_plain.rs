use mb::{Exported, Mission, Side};
use mb_spec::Refusal;
use mb_spec::p01::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Fireteam").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    m.validate().map_err(|_| Refusal::EmptyGroup)?;
    Ok(m.export())
}
