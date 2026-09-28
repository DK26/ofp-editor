use mb::{Activation, Area, Exported, Mission, Plan, Pos, Seconds, Side, Timer, TriggerBuilder};
use mb_spec::t20::Input;
use mb_spec::{Point, Refusal};

fn pos(p: Point) -> Result<Pos, Refusal> {
    Pos::new(p.x, p.z).map_err(|_| Refusal::OutOfMap)
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Alpha").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, pos(u.pos)?, u.rank);
    }
    let mut plan = Plan::new();
    for p in &input.patrol {
        plan = plan.move_to(pos(*p)?);
    }
    let plan = plan.cycle().map_err(|_| Refusal::TooFewWaypoints)?;
    m.assign_plan(g, plan).map_err(|_| Refusal::EmptyGroup)?;
    // The brief's mission validates on its own; the late addition needs a draft again.
    let m = m.validate().map_err(|_| Refusal::TooFewWaypoints)?;
    let mut m = m.into_draft();
    let late = &input.late;
    let timer = Timer::countdown(Seconds::new(late.min_s), Seconds::new(late.mid_s), Seconds::new(late.max_s))
        .map_err(|_| Refusal::TimerOrder)?;
    let t = TriggerBuilder::new(Area::whole_map())
        .activation(Activation::radio(late.channel))
        .timer(timer)
        .ends_mission(late.ending);
    m.add_trigger(t);
    let m = m.validate().map_err(|_| Refusal::TimerOrder)?;
    Ok(m.export())
}
