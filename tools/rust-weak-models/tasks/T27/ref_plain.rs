use mb::{Activation, Area, Exported, Mission, Trigger, Waypoint};
use mb_spec::Refusal;
use mb_spec::t27::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    if input.groups.iter().any(|g| g.units.is_empty()) {
        return Err(Refusal::EmptyGroup);
    }
    let mut m = Mission::new();
    let mut ids = Vec::with_capacity(input.groups.len());
    for grp in &input.groups {
        let g = m.add_group(grp.side, &grp.callsign).map_err(|_| Refusal::DuplicateCallsign)?;
        for u in &grp.units {
            m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
        }
        for p in &grp.route {
            m.add_waypoint(g, Waypoint::Move(*p)).map_err(|_| Refusal::OutOfMap)?;
        }
        ids.push(g);
    }
    let mut dropped = Vec::new();
    for (ti, raw) in input.triggers.iter().enumerate() {
        let t = m.add_trigger(Trigger::new(Area::whole_map(), Activation::Radio(raw.channel))).map_err(|_| Refusal::OutOfMap)?;
        for rf in &raw.syncs {
            let target = ids.get(rf.group).copied();
            let ok = match target {
                Some(g) => m.sync_trigger(t, (g, rf.waypoint)).is_ok(),
                None => false,
            };
            if !ok {
                dropped.push(format!("t{ti}:{}:{}", rf.group, rf.waypoint));
            }
        }
    }
    if !dropped.is_empty() {
        m.set_note(&dropped.join(", "));
    }
    m.validate().map_err(|_| Refusal::EmptyGroup)?;
    Ok(m.export())
}
