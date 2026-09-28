use mb::{Activation, Area, Degrees, Exported, Metres, Mission, Plan, Pos, Seconds, Side, Timer, TriggerBuilder};
use mb_spec::t28::Input;
use mb_spec::{Point, Refusal};

fn pos(p: Point) -> Result<Pos, Refusal> {
    Pos::new(p.x, p.z).map_err(|_| Refusal::OutOfMap)
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::West, &input.callsign).map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, pos(u.pos)?, u.rank);
    }
    let bridge = pos(input.bridge)?;
    m.assign_plan(g, Plan::new().move_to(pos(input.start)?).move_to(bridge)).map_err(|_| Refusal::EmptyGroup)?;
    let start_wp = m.waypoint(g, 0).ok_or(Refusal::UnknownGroup)?;
    let bridge_wp = m.waypoint(g, 1).ok_or(Refusal::UnknownGroup)?;
    let release = m.add_trigger(TriggerBuilder::new(Area::whole_map()).activation(Activation::radio(input.release)));
    m.sync_trigger(release, start_wp);
    let [lo, md, hi] = input.minutes;
    let timer = Timer::countdown(Seconds::from_minutes(lo), Seconds::from_minutes(md), Seconds::from_minutes(hi))
        .map_err(|_| Refusal::TimerOrder)?;
    let half = Metres::new(input.bridge_half_m);
    let end = m.add_trigger(
        TriggerBuilder::new(Area::new(bridge, half, half, Degrees::new(0.0)))
            .activation(Activation::none())
            .timer(timer)
            .ends_mission(input.ending),
    );
    m.sync_trigger(end, bridge_wp);
    let m = m.validate().map_err(|_| Refusal::TimerOrder)?;
    Ok(m.export())
}
