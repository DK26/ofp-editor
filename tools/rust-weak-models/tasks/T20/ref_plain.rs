use mb::{Activation, Area, Effect, Exported, Mission, Side, Timer, TimerKind, Trigger, Waypoint};
use mb_spec::Refusal;
use mb_spec::t20::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Alpha").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    for p in &input.patrol {
        m.add_waypoint(g, Waypoint::Move(*p)).map_err(|_| Refusal::OutOfMap)?;
    }
    m.add_waypoint(g, Waypoint::Cycle).map_err(|_| Refusal::TooFewWaypoints)?;
    // Late addition.
    let late = &input.late;
    let timer = Timer::new(TimerKind::Countdown, late.min_s, late.mid_s, late.max_s).map_err(|_| Refusal::TimerOrder)?;
    let mut t = Trigger::new(Area::whole_map(), Activation::Radio(late.channel));
    t.timer = Some(timer);
    t.effect = Effect::End(late.ending);
    m.add_trigger(t).map_err(|_| Refusal::OutOfMap)?;
    // Validate the final mission, after every change.
    m.validate().map_err(|_| Refusal::TimerOrder)?;
    Ok(m.export())
}
