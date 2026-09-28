use mb::{
    Activation, Area, Degrees, Ending, Exported, GroupId, Metres, Mission, Plan, Pos, Seconds, Side, Timer, TriggerBuilder,
};
use mb_spec::t26::Input;
use mb_spec::{Point, Refusal, UnitIn};

fn pos(p: Point) -> Result<Pos, Refusal> {
    Pos::new(p.x, p.z).map_err(|_| Refusal::OutOfMap)
}

fn add_group(m: &mut Mission, side: Side, callsign: &str, units: &[UnitIn]) -> Result<GroupId, Refusal> {
    let g = m.add_group(side, callsign).map_err(|_| Refusal::DuplicateCallsign)?;
    for u in units {
        m.add_unit(g, u.class, &u.label, pos(u.pos)?, u.rank);
    }
    Ok(g)
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    // Patrol loop.
    let patrol = add_group(&mut m, Side::West, &input.patrol.callsign, &input.patrol.units)?;
    let mut plan = Plan::new();
    for p in &input.patrol.route {
        plan = plan.move_to(pos(*p)?);
    }
    m.assign_plan(patrol, plan.cycle().map_err(|_| Refusal::TooFewWaypoints)?).map_err(|_| Refusal::EmptyGroup)?;
    // Convoy.
    let c = &input.convoy;
    let convoy = add_group(&mut m, Side::West, &c.callsign, &c.units)?;
    let truck = m.vehicle(&c.truck).ok_or(Refusal::UnknownVehicle)?;
    let dest = pos(c.destination)?;
    m.assign_plan(convoy, Plan::new().get_in(truck).move_to(dest).get_out(dest)).map_err(|_| Refusal::WrongSide)?;
    let ride = m.waypoint(convoy, 1).ok_or(Refusal::UnknownGroup)?;
    let patrol_second = m.waypoint(patrol, 1).ok_or(Refusal::UnknownGroup)?;
    m.sync_waypoints(ride, patrol_second);
    // Enemy.
    let enemy = add_group(&mut m, Side::East, &input.enemy.callsign, &input.enemy.units)?;
    let mut plan = Plan::new();
    for p in &input.enemy.route {
        plan = plan.move_to(pos(*p)?);
    }
    m.assign_plan(enemy, plan).map_err(|_| Refusal::EmptyGroup)?;
    // Release.
    let released = m.group(&input.release_callsign).ok_or(Refusal::UnknownGroup)?;
    let first = m.waypoint(released, 0).ok_or(Refusal::UnknownGroup)?;
    let release = m.add_trigger(TriggerBuilder::new(Area::whole_map()).activation(Activation::radio(input.release)));
    m.sync_trigger(release, first);
    // Win: timeout given in minutes.
    let [lo, md, hi] = input.hold_minutes;
    let timer = Timer::timeout(Seconds::from_minutes(lo), Seconds::from_minutes(md), Seconds::from_minutes(hi))
        .map_err(|_| Refusal::TimerOrder)?;
    let half = Metres::new(input.objective_half_m);
    let objective = Area::new(pos(input.objective)?, half, half, Degrees::new(0.0));
    m.add_trigger(
        TriggerBuilder::new(objective)
            .activation(Activation::present(Side::West))
            .timer(timer)
            .ends_mission(Ending::One),
    );
    // Loss.
    m.add_trigger(TriggerBuilder::new(Area::whole_map()).activation(Activation::not_present(Side::West)).loses_mission());
    let m = m.validate().map_err(|_| Refusal::InvalidSequence)?;
    Ok(m.export())
}
