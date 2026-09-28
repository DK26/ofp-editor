use mb::{Activation, Area, Degrees, Exported, Metres, Mission, Plan, Pos, Side, TriggerBuilder};
use mb_spec::t17::Input;
use mb_spec::{Point, Refusal};

fn pos(p: Point) -> Result<Pos, Refusal> {
    Pos::new(p.x, p.z).map_err(|_| Refusal::OutOfMap)
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::East, "Ambush").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, pos(u.pos)?, u.rank);
    }
    let plan = Plan::new().move_to(pos(input.ambush)?).move_to(pos(input.extraction)?);
    m.assign_plan(g, plan).map_err(|_| Refusal::EmptyGroup)?;
    let wait = m.waypoint(g, 0).ok_or(Refusal::UnknownGroup)?;
    let half = Metres::new(input.kill_zone_half_m);
    let zone = Area::new(pos(input.kill_zone)?, half, half, Degrees::new(0.0));
    let t = m.add_trigger(TriggerBuilder::new(zone).activation(Activation::present(Side::West)));
    m.sync_trigger(t, wait);
    let m = m.validate().map_err(|_| Refusal::InvalidSequence)?;
    Ok(m.export())
}
