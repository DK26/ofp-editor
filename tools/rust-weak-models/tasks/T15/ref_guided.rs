use mb::{Activation, Area, Exported, Mission, Plan, Pos, TriggerBuilder};
use mb_spec::t15::Input;
use mb_spec::{Point, Refusal};

fn pos(p: Point) -> Result<Pos, Refusal> {
    Pos::new(p.x, p.z).map_err(|_| Refusal::OutOfMap)
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
    let waiting = m.group(&input.waiting).ok_or(Refusal::UnknownGroup)?;
    let wp = m.waypoint(waiting, input.number.saturating_sub(1)).ok_or(Refusal::UnknownGroup)?;
    let t = m.add_trigger(TriggerBuilder::new(Area::whole_map()).activation(Activation::radio(input.channel)));
    m.sync_trigger(t, wp);
    let m = m.validate().map_err(|_| Refusal::UnknownGroup)?;
    Ok(m.export())
}
