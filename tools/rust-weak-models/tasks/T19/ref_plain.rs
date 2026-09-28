use mb::{Exported, Mission, Waypoint};
use mb_spec::Refusal;
use mb_spec::t19::{DraftIn, Input};

fn add_draft(m: &mut Mission, draft: &DraftIn) -> Result<Vec<u32>, Refusal> {
    let mut ids = Vec::with_capacity(draft.groups.len());
    for grp in &draft.groups {
        let callsign = if m.group_by_callsign(&grp.callsign).is_some() {
            format!("{}-2", grp.callsign)
        } else {
            grp.callsign.clone()
        };
        let g = m.add_group(grp.side, &callsign).map_err(|_| Refusal::DuplicateCallsign)?;
        for u in &grp.units {
            m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
        }
        for p in &grp.route {
            m.add_waypoint(g, Waypoint::Move(*p)).map_err(|_| Refusal::OutOfMap)?;
        }
        ids.push(g);
    }
    Ok(ids)
}

fn add_syncs(m: &mut Mission, draft: &DraftIn, ids: &[u32]) -> Result<(), Refusal> {
    for s in &draft.syncs {
        let a = *ids.get(s.group_a).ok_or(Refusal::UnknownGroup)?;
        let b = *ids.get(s.group_b).ok_or(Refusal::UnknownGroup)?;
        m.sync_waypoints((a, s.wp_a), (b, s.wp_b)).map_err(|_| Refusal::UnknownGroup)?;
    }
    Ok(())
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let first = add_draft(&mut m, &input.first)?;
    let second = add_draft(&mut m, &input.second)?;
    add_syncs(&mut m, &input.first, &first)?;
    add_syncs(&mut m, &input.second, &second)?;
    m.validate().map_err(|_| Refusal::UnknownGroup)?;
    Ok(m.export())
}
