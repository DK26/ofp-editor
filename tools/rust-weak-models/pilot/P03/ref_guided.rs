use mb::{Activation, Area, Degrees, Ending, Exported, Metres, Mission, Pos, Side, TriggerBuilder};
use mb_spec::Refusal;
use mb_spec::p03::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Base").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        let pos = Pos::new(u.pos.x, u.pos.z).map_err(|_| Refusal::OutOfMap)?;
        m.add_unit(g, u.class, &u.label, pos, u.rank);
    }
    let centre = Pos::new(input.base.x, input.base.z).map_err(|_| Refusal::OutOfMap)?;
    let half = Metres::new(input.half_size_m);
    let area = Area::new(centre, half, half, Degrees::new(0.0));
    let alarm = TriggerBuilder::new(area)
        .activation(Activation::present(Side::East))
        .ends_mission(Ending::One);
    m.add_trigger(alarm);
    let m = m.validate().map_err(|_| Refusal::RepeatingEnd)?;
    Ok(m.export())
}
