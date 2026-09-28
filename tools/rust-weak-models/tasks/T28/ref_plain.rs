use mb::{Activation, Area, Effect, Exported, Mission, Side, Timer, TimerKind, Trigger, Waypoint};
use mb_spec::Refusal;
use mb_spec::t28::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::West, &input.callsign).map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    let start = m.add_waypoint(g, Waypoint::Move(input.start)).map_err(|_| Refusal::OutOfMap)?;
    let bridge = m.add_waypoint(g, Waypoint::Move(input.bridge)).map_err(|_| Refusal::OutOfMap)?;
    let release = m
        .add_trigger(Trigger::new(Area::whole_map(), Activation::Radio(input.release)))
        .map_err(|_| Refusal::OutOfMap)?;
    m.sync_trigger(release, (g, start)).map_err(|_| Refusal::UnknownGroup)?;
    let [lo, md, hi] = input.minutes;
    let timer = Timer::new(TimerKind::Countdown, lo * 60.0, md * 60.0, hi * 60.0).map_err(|_| Refusal::TimerOrder)?;
    let area = Area::new(input.bridge, input.bridge_half_m, input.bridge_half_m, 0.0);
    let mut end = Trigger::new(area, Activation::None);
    end.timer = Some(timer);
    end.effect = Effect::End(input.ending);
    let end = m.add_trigger(end).map_err(|_| Refusal::OutOfMap)?;
    m.sync_trigger(end, (g, bridge)).map_err(|_| Refusal::UnknownGroup)?;
    m.validate().map_err(|_| Refusal::TimerOrder)?;
    Ok(m.export())
}
