use mb::{Exported, Mission, Plan, Pos, WaypointRef};
use mb_spec::t13::{Input, WaypointNo};
use mb_spec::{Point, Refusal};

fn pos(p: Point) -> Result<Pos, Refusal> {
    Pos::new(p.x, p.z).map_err(|_| Refusal::OutOfMap)
}

fn locate(m: &Mission, w: &WaypointNo) -> Result<WaypointRef, Refusal> {
    let g = m.group(&w.callsign).ok_or(Refusal::UnknownGroup)?;
    m.waypoint(g, w.number.saturating_sub(1)).ok_or(Refusal::UnknownGroup)
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    for grp in &input.groups {
        let g = m.add_group(grp.side, &grp.callsign).map_err(|_| Refusal::DuplicateCallsign)?;
        for u in &grp.units {
            m.add_unit(g, u.class, &u.label, pos(u.pos)?, u.rank);
        }
        let mut plan = Plan::new();
        for p in &grp.route {
            plan = plan.move_to(pos(*p)?);
        }
        m.assign_plan(g, plan).map_err(|_| Refusal::EmptyGroup)?;
    }
    let a = locate(&m, &input.first)?;
    let b = locate(&m, &input.second)?;
    m.sync_waypoints(a, b);
    let m = m.validate().map_err(|_| Refusal::UnknownGroup)?;
    Ok(m.export())
}
