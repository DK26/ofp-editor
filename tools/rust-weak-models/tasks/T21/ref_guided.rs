use mb::{Activation, Area, Exported, Mission, Pos, Side, TriggerBuilder};
use mb_spec::Refusal;
use mb_spec::t21::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Player").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        let pos = Pos::new(u.pos.x, u.pos.z).map_err(|_| Refusal::OutOfMap)?;
        m.add_unit(g, u.class, &u.label, pos, u.rank);
    }
    m.add_trigger(
        TriggerBuilder::new(Area::whole_map())
            .activation(Activation::not_present(Side::West))
            .loses_mission(),
    );
    m.add_trigger(
        TriggerBuilder::new(Area::whole_map())
            .activation(Activation::radio(input.win_channel))
            .ends_mission(input.win_ending),
    );
    let m = m.validate().map_err(|_| Refusal::RepeatingEnd)?;
    Ok(m.export())
}
