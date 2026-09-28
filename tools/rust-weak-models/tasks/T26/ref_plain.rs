use mb::{Activation, Area, Effect, Ending, Exported, Mission, Side, Timer, TimerKind, Trigger, Waypoint};
use mb_spec::t26::Input;
use mb_spec::{Refusal, UnitIn};

fn add_group(m: &mut Mission, side: Side, callsign: &str, units: &[UnitIn]) -> Result<u32, Refusal> {
    let g = m.add_group(side, callsign).map_err(|_| Refusal::DuplicateCallsign)?;
    for u in units {
        m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    Ok(g)
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    // Patrol loop.
    let patrol = add_group(&mut m, Side::West, &input.patrol.callsign, &input.patrol.units)?;
    for p in &input.patrol.route {
        m.add_waypoint(patrol, Waypoint::Move(*p)).map_err(|_| Refusal::OutOfMap)?;
    }
    m.add_waypoint(patrol, Waypoint::Cycle).map_err(|_| Refusal::TooFewWaypoints)?;
    // Convoy.
    let c = &input.convoy;
    let convoy = add_group(&mut m, Side::West, &c.callsign, &c.units)?;
    let truck = m.vehicle_by_label(&c.truck).ok_or(Refusal::UnknownVehicle)?;
    m.add_waypoint(convoy, Waypoint::GetIn(truck)).map_err(|_| Refusal::UnknownVehicle)?;
    let ride = m.add_waypoint(convoy, Waypoint::Move(c.destination)).map_err(|_| Refusal::OutOfMap)?;
    m.add_waypoint(convoy, Waypoint::GetOut(c.destination)).map_err(|_| Refusal::OutOfMap)?;
    m.sync_waypoints((convoy, ride), (patrol, 1)).map_err(|_| Refusal::UnknownGroup)?;
    // Enemy.
    let enemy = add_group(&mut m, Side::East, &input.enemy.callsign, &input.enemy.units)?;
    for p in &input.enemy.route {
        m.add_waypoint(enemy, Waypoint::Move(*p)).map_err(|_| Refusal::OutOfMap)?;
    }
    // Release.
    let released = m.group_by_callsign(&input.release_callsign).ok_or(Refusal::UnknownGroup)?;
    let release = m
        .add_trigger(Trigger::new(Area::whole_map(), Activation::Radio(input.release)))
        .map_err(|_| Refusal::OutOfMap)?;
    m.sync_trigger(release, (released, 0)).map_err(|_| Refusal::UnknownGroup)?;
    // Win: timeout in seconds.
    let [lo, md, hi] = input.hold_minutes;
    let timer = Timer::new(TimerKind::Timeout, lo * 60.0, md * 60.0, hi * 60.0).map_err(|_| Refusal::TimerOrder)?;
    let area = Area::new(input.objective, input.objective_half_m, input.objective_half_m, 0.0);
    let mut win = Trigger::new(area, Activation::Present(Side::West));
    win.timer = Some(timer);
    win.effect = Effect::End(Ending::One);
    m.add_trigger(win).map_err(|_| Refusal::OutOfMap)?;
    // Loss.
    let mut loss = Trigger::new(Area::whole_map(), Activation::NotPresent(Side::West));
    loss.effect = Effect::Lose;
    m.add_trigger(loss).map_err(|_| Refusal::OutOfMap)?;
    m.validate().map_err(|_| Refusal::InvalidSequence)?;
    Ok(m.export())
}
