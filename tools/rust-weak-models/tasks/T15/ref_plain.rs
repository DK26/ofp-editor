use mb::{Activation, Area, Exported, Mission, Trigger, Waypoint};
use mb_spec::Refusal;
use mb_spec::t15::Input;

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
    let waiting = m.group_by_callsign(&input.waiting).ok_or(Refusal::UnknownGroup)?;
    let t = m
        .add_trigger(Trigger::new(Area::whole_map(), Activation::Radio(input.channel)))
        .map_err(|_| Refusal::OutOfMap)?;
    m.sync_trigger(t, (waiting, input.number.saturating_sub(1))).map_err(|_| Refusal::UnknownGroup)?;
    m.validate().map_err(|_| Refusal::UnknownGroup)?;
    Ok(m.export())
}
