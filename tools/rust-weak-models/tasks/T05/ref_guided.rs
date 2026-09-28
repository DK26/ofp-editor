use mb::{Activation, Area, Exported, Mission, Pos, Side, TriggerBuilder};
use mb_spec::Refusal;
use mb_spec::t05::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "HQ").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        let pos = Pos::new(u.pos.x, u.pos.z).map_err(|_| Refusal::OutOfMap)?;
        m.add_unit(g, u.class, &u.label, pos, u.rank);
    }
    let t = TriggerBuilder::new(Area::whole_map())
        .activation(Activation::radio(input.channel))
        .ends_mission(input.ending);
    m.add_trigger(t);
    let m = m.validate().map_err(|_| Refusal::RepeatingEnd)?;
    Ok(m.export())
}
