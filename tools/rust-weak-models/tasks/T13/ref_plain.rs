use mb::{Exported, Mission, Waypoint};
use mb_spec::Refusal;
use mb_spec::t13::{Input, WaypointNo};

fn locate(m: &Mission, w: &WaypointNo) -> Result<(u32, usize), Refusal> {
    let g = m.group_by_callsign(&w.callsign).ok_or(Refusal::UnknownGroup)?;
    Ok((g, w.number.saturating_sub(1)))
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    for grp in &input.groups {
        let g = m.add_group(grp.side, &grp.callsign).map_err(|_| Refusal::DuplicateCallsign)?;
        for u in &grp.units {
            m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
        }
        for p in &grp.route {
            m.add_waypoint(g, Waypoint::Move(*p)).map_err(|_| Refusal::OutOfMap)?;
        }
    }
    let a = locate(&m, &input.first)?;
    let b = locate(&m, &input.second)?;
    m.sync_waypoints(a, b).map_err(|_| Refusal::UnknownGroup)?;
    m.validate().map_err(|_| Refusal::UnknownGroup)?;
    Ok(m.export())
}
