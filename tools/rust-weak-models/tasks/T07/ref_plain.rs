use mb::{Exported, Mission, Side, Waypoint};
use mb_spec::Refusal;
use mb_spec::t07::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Rover").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    for p in [input.a, input.b, input.c, input.depot] {
        m.add_waypoint(g, Waypoint::Move(p)).map_err(|_| Refusal::OutOfMap)?;
    }
    m.add_waypoint(g, Waypoint::Cycle).map_err(|_| Refusal::InvalidSequence)?;
    m.validate().map_err(|_| Refusal::InvalidSequence)?;
    Ok(m.export())
}
