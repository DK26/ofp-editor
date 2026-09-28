use mb::{Activation, Area, Effect, Ending, Exported, Mission, Side, Timer, TimerKind, Trigger};
use mb_spec::Refusal;
use mb_spec::t14::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let [longest, shortest, typical] = input.seconds;
    let timer = Timer::new(TimerKind::Timeout, shortest, typical, longest).map_err(|_| Refusal::TimerOrder)?;
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Holdout").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    let area = Area::new(input.post, input.post_half_m, input.post_half_m, 0.0);
    let mut t = Trigger::new(area, Activation::Present(Side::West));
    t.timer = Some(timer);
    t.effect = Effect::End(Ending::Three);
    m.add_trigger(t).map_err(|_| Refusal::OutOfMap)?;
    m.validate().map_err(|_| Refusal::TimerOrder)?;
    Ok(m.export())
}
