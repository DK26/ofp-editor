use mb::{Activation, Area, Degrees, Exported, Metres, Mission, Pos, TriggerBuilder};
use mb_spec::Refusal;
use mb_spec::t10::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let act = Activation::detected_by(input.watched, input.watcher).map_err(|_| Refusal::SameSide)?;
    let mut m = Mission::new();
    let g = m.add_group(input.watched, "Scouts").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        let pos = Pos::new(u.pos.x, u.pos.z).map_err(|_| Refusal::OutOfMap)?;
        m.add_unit(g, u.class, &u.label, pos, u.rank);
    }
    let centre = Pos::new(input.area.x, input.area.z).map_err(|_| Refusal::OutOfMap)?;
    let half = Metres::new(input.area_half_m);
    let t = TriggerBuilder::new(Area::new(centre, half, half, Degrees::new(0.0))).activation(act).loses_mission();
    m.add_trigger(t);
    let m = m.validate().map_err(|_| Refusal::SameSide)?;
    Ok(m.export())
}
