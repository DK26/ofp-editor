use mb::{Activation, Area, Exported, Mission, Side, Trigger, Waypoint};
use mb_spec::Refusal;
use mb_spec::t17::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::East, "Ambush").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    let wait = m.add_waypoint(g, Waypoint::Move(input.ambush)).map_err(|_| Refusal::OutOfMap)?;
    m.add_waypoint(g, Waypoint::Move(input.extraction)).map_err(|_| Refusal::OutOfMap)?;
    let zone = Area::new(input.kill_zone, input.kill_zone_half_m, input.kill_zone_half_m, 0.0);
    let t = m.add_trigger(Trigger::new(zone, Activation::Present(Side::West))).map_err(|_| Refusal::OutOfMap)?;
    m.sync_trigger(t, (g, wait)).map_err(|_| Refusal::UnknownGroup)?;
    m.validate().map_err(|_| Refusal::InvalidSequence)?;
    Ok(m.export())
}
