use mb::{Activation, Area, Effect, Ending, Exported, Mission, Side, Trigger};
use mb_spec::Refusal;
use mb_spec::t09::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    if input.repeating {
        return Err(Refusal::RepeatingEnd);
    }
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Defenders").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    let area = Area::new(input.town, input.town_half_m, input.town_half_m, 0.0);
    let mut t = Trigger::new(area, Activation::Present(Side::East));
    t.effect = Effect::End(Ending::Two);
    m.add_trigger(t).map_err(|_| Refusal::OutOfMap)?;
    m.validate().map_err(|_| Refusal::RepeatingEnd)?;
    Ok(m.export())
}
