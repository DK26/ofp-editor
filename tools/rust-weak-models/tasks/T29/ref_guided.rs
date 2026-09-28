use mb::{Activation, Area, Exported, GroupId, Mission, Plan, Pos, Seconds, Side, Timer, TriggerBuilder};
use mb_spec::t29::{Input, WaveIn};
use mb_spec::{Point, Refusal};

fn pos(p: Point) -> Result<Pos, Refusal> {
    Pos::new(p.x, p.z).map_err(|_| Refusal::OutOfMap)
}

fn add_wave(m: &mut Mission, wave: &WaveIn, route: &[Point]) -> Result<GroupId, Refusal> {
    let g = m.add_group(Side::West, &wave.callsign).map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &wave.units {
        m.add_unit(g, u.class, &u.label, pos(u.pos)?, u.rank);
    }
    let vehicle = m.vehicle(&wave.vehicle).ok_or(Refusal::UnknownVehicle)?;
    let mut plan = Plan::new().get_in(vehicle);
    for p in route {
        plan = plan.move_to(pos(*p)?);
    }
    m.assign_plan(g, plan).map_err(|_| Refusal::WrongSide)?;
    Ok(g)
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let first = add_wave(&mut m, &input.first, &input.route)?;
    let second = add_wave(&mut m, &input.second, &input.route)?;
    let first_wp = m.waypoint(first, 0).ok_or(Refusal::UnknownGroup)?;
    let second_wp = m.waypoint(second, 0).ok_or(Refusal::UnknownGroup)?;
    let now = m.add_trigger(TriggerBuilder::new(Area::whole_map()).activation(Activation::radio(input.release)));
    m.sync_trigger(now, first_wp);
    let d = Seconds::new(input.delay_s);
    let timer = Timer::countdown(d, d, d).map_err(|_| Refusal::TimerOrder)?;
    let later = m.add_trigger(TriggerBuilder::new(Area::whole_map()).activation(Activation::radio(input.release)).timer(timer));
    m.sync_trigger(later, second_wp);
    let m = m.validate().map_err(|_| Refusal::UnknownVehicle)?;
    Ok(m.export())
}
