use mb::{Activation, Area, Effect, Ending, Exported, Mission, Side, Trigger};
use mb_spec::Refusal;
use mb_spec::p03::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Base").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    let area = Area::new(input.base, input.half_size_m, input.half_size_m, 0.0);
    let mut alarm = Trigger::new(area, Activation::Present(Side::East));
    alarm.effect = Effect::End(Ending::One);
    m.add_trigger(alarm).map_err(|_| Refusal::OutOfMap)?;
    m.validate().map_err(|_| Refusal::RepeatingEnd)?;
    Ok(m.export())
}
