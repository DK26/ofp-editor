use mb::{Activation, Area, Effect, Exported, Mission, Side, Trigger};
use mb_spec::Refusal;
use mb_spec::t21::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Player").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    let mut lose = Trigger::new(Area::whole_map(), Activation::NotPresent(Side::West));
    lose.effect = Effect::Lose;
    m.add_trigger(lose).map_err(|_| Refusal::OutOfMap)?;
    let mut win = Trigger::new(Area::whole_map(), Activation::Radio(input.win_channel));
    win.effect = Effect::End(input.win_ending);
    m.add_trigger(win).map_err(|_| Refusal::OutOfMap)?;
    m.validate().map_err(|_| Refusal::RepeatingEnd)?;
    Ok(m.export())
}
