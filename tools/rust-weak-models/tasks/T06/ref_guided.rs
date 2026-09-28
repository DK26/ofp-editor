use mb::{Activation, Area, Degrees, Ending, Exported, Metres, Mission, Pos, Seconds, Side, Timer, TriggerBuilder};
use mb_spec::Refusal;
use mb_spec::t06::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::East, "Garrison").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        let pos = Pos::new(u.pos.x, u.pos.z).map_err(|_| Refusal::OutOfMap)?;
        m.add_unit(g, u.class, &u.label, pos, u.rank);
    }
    let timer = Timer::countdown(
        Seconds::from_minutes(input.minutes_min),
        Seconds::from_minutes(input.minutes_typical),
        Seconds::from_minutes(input.minutes_max),
    )
    .map_err(|_| Refusal::TimerOrder)?;
    let centre = Pos::new(input.zone.x, input.zone.z).map_err(|_| Refusal::OutOfMap)?;
    let half = Metres::new(input.zone_half_m);
    let t = TriggerBuilder::new(Area::new(centre, half, half, Degrees::new(0.0)))
        .activation(Activation::present(Side::West))
        .timer(timer)
        .ends_mission(Ending::Two);
    m.add_trigger(t);
    let m = m.validate().map_err(|_| Refusal::TimerOrder)?;
    Ok(m.export())
}
