use mb::{Exported, Mission, Side, Waypoint};
use mb_spec::Refusal;
use mb_spec::p02::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::East, "Guard").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    m.add_waypoint(g, Waypoint::Move(input.gate)).map_err(|_| Refusal::OutOfMap)?;
    m.add_waypoint(g, Waypoint::Hold(input.post)).map_err(|_| Refusal::OutOfMap)?;
    m.validate().map_err(|_| Refusal::InvalidSequence)?;
    Ok(m.export())
}
