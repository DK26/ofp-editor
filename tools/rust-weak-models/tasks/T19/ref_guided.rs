use mb::{Exported, GroupId, Mission, Plan, Pos};
use mb_spec::t19::{DraftIn, Input};
use mb_spec::{Point, Refusal};

fn pos(p: Point) -> Result<Pos, Refusal> {
    Pos::new(p.x, p.z).map_err(|_| Refusal::OutOfMap)
}

fn add_draft(m: &mut Mission, draft: &DraftIn) -> Result<Vec<GroupId>, Refusal> {
    let mut ids = Vec::with_capacity(draft.groups.len());
    for grp in &draft.groups {
        let callsign = if m.group(&grp.callsign).is_some() {
            format!("{}-2", grp.callsign)
        } else {
            grp.callsign.clone()
        };
        let g = m.add_group(grp.side, &callsign).map_err(|_| Refusal::DuplicateCallsign)?;
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
    Ok(ids)
}

fn add_syncs(m: &mut Mission, draft: &DraftIn, ids: &[GroupId]) -> Result<(), Refusal> {
    for s in &draft.syncs {
        let a = *ids.get(s.group_a).ok_or(Refusal::UnknownGroup)?;
        let b = *ids.get(s.group_b).ok_or(Refusal::UnknownGroup)?;
        let wa = m.waypoint(a, s.wp_a).ok_or(Refusal::UnknownGroup)?;
        let wb = m.waypoint(b, s.wp_b).ok_or(Refusal::UnknownGroup)?;
        m.sync_waypoints(wa, wb);
    }
    Ok(())
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let first = add_draft(&mut m, &input.first)?;
    let second = add_draft(&mut m, &input.second)?;
    add_syncs(&mut m, &input.first, &first)?;
    add_syncs(&mut m, &input.second, &second)?;
    let m = m.validate().map_err(|_| Refusal::UnknownGroup)?;
    Ok(m.export())
}
