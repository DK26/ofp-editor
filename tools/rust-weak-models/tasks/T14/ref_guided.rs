use mb::{Activation, Area, Degrees, Ending, Exported, Metres, Mission, Pos, Seconds, Side, Timer, TriggerBuilder};
use mb_spec::Refusal;
use mb_spec::t14::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let [longest, shortest, typical] = input.seconds;
    let timer = Timer::timeout(Seconds::new(shortest), Seconds::new(typical), Seconds::new(longest))
        .map_err(|_| Refusal::TimerOrder)?;
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Holdout").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        let pos = Pos::new(u.pos.x, u.pos.z).map_err(|_| Refusal::OutOfMap)?;
        m.add_unit(g, u.class, &u.label, pos, u.rank);
    }
    let centre = Pos::new(input.post.x, input.post.z).map_err(|_| Refusal::OutOfMap)?;
    let half = Metres::new(input.post_half_m);
    let t = TriggerBuilder::new(Area::new(centre, half, half, Degrees::new(0.0)))
        .activation(Activation::present(Side::West))
        .timer(timer)
        .ends_mission(Ending::Three);
    m.add_trigger(t);
    let m = m.validate().map_err(|_| Refusal::TimerOrder)?;
    Ok(m.export())
}
