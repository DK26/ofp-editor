use mb::{Activation, Area, Effect, Ending, Exported, Mission, Side, Timer, TimerKind, Trigger};
use mb_spec::Refusal;
use mb_spec::t06::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::East, "Garrison").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    let timer = Timer::new(
        TimerKind::Countdown,
        input.minutes_min * 60.0,
        input.minutes_typical * 60.0,
        input.minutes_max * 60.0,
    )
    .map_err(|_| Refusal::TimerOrder)?;
    let area = Area::new(input.zone, input.zone_half_m, input.zone_half_m, 0.0);
    let mut t = Trigger::new(area, Activation::Present(Side::West));
    t.timer = Some(timer);
    t.effect = Effect::End(Ending::Two);
    m.add_trigger(t).map_err(|_| Refusal::OutOfMap)?;
    m.validate().map_err(|_| Refusal::TimerOrder)?;
    Ok(m.export())
}
