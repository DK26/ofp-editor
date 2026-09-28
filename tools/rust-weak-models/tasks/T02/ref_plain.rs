use mb::{Exported, Mission, Side, Waypoint};
use mb_spec::Refusal;
use mb_spec::t02::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::East, "Team").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    m.add_waypoint(g, Waypoint::Move(input.first)).map_err(|_| Refusal::OutOfMap)?;
    m.add_waypoint(g, Waypoint::Move(input.second)).map_err(|_| Refusal::OutOfMap)?;
    m.validate().map_err(|_| Refusal::OutOfMap)?;
    Ok(m.export())
}
