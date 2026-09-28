use mb::{Exported, Mission, Side, Waypoint};
use mb_spec::Refusal;
use mb_spec::t03::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::Resistance, "Sentry").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    let (last, rest) = input.points.split_last().ok_or(Refusal::TooFewWaypoints)?;
    for p in rest {
        m.add_waypoint(g, Waypoint::Move(*p)).map_err(|_| Refusal::OutOfMap)?;
    }
    m.add_waypoint(g, Waypoint::Hold(*last)).map_err(|_| Refusal::OutOfMap)?;
    m.validate().map_err(|_| Refusal::InvalidSequence)?;
    Ok(m.export())
}
