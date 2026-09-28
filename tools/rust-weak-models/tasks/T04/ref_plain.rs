use mb::{Exported, Mission, Side, Waypoint};
use mb_spec::Refusal;
use mb_spec::t04::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    if input.points.len() < 2 {
        return Err(Refusal::TooFewWaypoints);
    }
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Patrol").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    for p in &input.points {
        m.add_waypoint(g, Waypoint::Move(*p)).map_err(|_| Refusal::OutOfMap)?;
    }
    m.add_waypoint(g, Waypoint::Cycle).map_err(|_| Refusal::TooFewWaypoints)?;
    m.validate().map_err(|_| Refusal::TooFewWaypoints)?;
    Ok(m.export())
}
