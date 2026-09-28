use mb::{Activation, Area, Effect, Exported, Mission, Side, Trigger};
use mb_spec::Refusal;
use mb_spec::t05::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "HQ").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    let mut t = Trigger::new(Area::whole_map(), Activation::Radio(input.channel));
    t.effect = Effect::End(input.ending);
    m.add_trigger(t).map_err(|_| Refusal::OutOfMap)?;
    m.validate().map_err(|_| Refusal::RepeatingEnd)?;
    Ok(m.export())
}
