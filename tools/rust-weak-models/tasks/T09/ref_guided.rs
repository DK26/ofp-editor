use mb::{Activation, Area, Degrees, Ending, Exported, Metres, Mission, Pos, Side, TriggerBuilder};
use mb_spec::Refusal;
use mb_spec::t09::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    if input.repeating {
        return Err(Refusal::RepeatingEnd);
    }
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Defenders").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        let pos = Pos::new(u.pos.x, u.pos.z).map_err(|_| Refusal::OutOfMap)?;
        m.add_unit(g, u.class, &u.label, pos, u.rank);
    }
    let centre = Pos::new(input.town.x, input.town.z).map_err(|_| Refusal::OutOfMap)?;
    let half = Metres::new(input.town_half_m);
    let t = TriggerBuilder::new(Area::new(centre, half, half, Degrees::new(0.0)))
        .activation(Activation::present(Side::East))
        .ends_mission(Ending::Two);
    m.add_trigger(t);
    let m = m.validate().map_err(|_| Refusal::RepeatingEnd)?;
    Ok(m.export())
}
