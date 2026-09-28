use mb::{Activation, Area, Effect, Exported, Mission, Trigger};
use mb_spec::Refusal;
use mb_spec::t10::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    if input.watcher == input.watched {
        return Err(Refusal::SameSide);
    }
    let mut m = Mission::new();
    let g = m.add_group(input.watched, "Scouts").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    let area = Area::new(input.area, input.area_half_m, input.area_half_m, 0.0);
    let act = Activation::DetectedBy { detector: input.watcher, detected: input.watched };
    let mut t = Trigger::new(area, act);
    t.effect = Effect::Lose;
    m.add_trigger(t).map_err(|_| Refusal::OutOfMap)?;
    m.validate().map_err(|_| Refusal::SameSide)?;
    Ok(m.export())
}
