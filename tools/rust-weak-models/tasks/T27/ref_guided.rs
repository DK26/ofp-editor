use mb::{Activation, Area, Exported, Mission, Plan, Pos, TriggerBuilder};
use mb_spec::t27::Input;
use mb_spec::{Point, Refusal};

fn pos(p: Point) -> Result<Pos, Refusal> {
    Pos::new(p.x, p.z).map_err(|_| Refusal::OutOfMap)
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let mut ids = Vec::with_capacity(input.groups.len());
    for grp in &input.groups {
        if grp.units.is_empty() {
            return Err(Refusal::EmptyGroup);
        }
        let g = m.add_group(grp.side, &grp.callsign).map_err(|_| Refusal::DuplicateCallsign)?;
        for u in &grp.units {
            m.add_unit(g, u.class, &u.label, pos(u.pos)?, u.rank);
        }
        let mut plan = Plan::new();
        for p in &grp.route {
            plan = plan.move_to(pos(*p)?);
        }
        m.assign_plan(g, plan).map_err(|_| Refusal::EmptyGroup)?;
        ids.push(g);
    }
    let mut dropped = Vec::new();
    for (ti, raw) in input.triggers.iter().enumerate() {
        let t = m.add_trigger(TriggerBuilder::new(Area::whole_map()).activation(Activation::radio(raw.channel)));
        for rf in &raw.syncs {
            let wp = ids.get(rf.group).and_then(|g| m.waypoint(*g, rf.waypoint));
            match wp {
                Some(wp) => m.sync_trigger(t, wp),
                None => dropped.push(format!("t{ti}:{}:{}", rf.group, rf.waypoint)),
            }
        }
    }
    if !dropped.is_empty() {
        m.set_note(&dropped.join(", "));
    }
    let m = m.validate().map_err(|_| Refusal::EmptyGroup)?;
    Ok(m.export())
}
