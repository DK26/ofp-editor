use mb::{Exported, Mission, Waypoint};
use mb_spec::Refusal;
use mb_spec::t16::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let pool = m.add_group(input.pool_side, &input.pool_callsign).map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.vehicles {
        m.add_unit(pool, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    let pool_move = m.add_waypoint(pool, Waypoint::Move(input.destination)).map_err(|_| Refusal::OutOfMap)?;
    for s in &input.squads {
        let truck = m.vehicle_by_label(&s.truck).ok_or(Refusal::UnknownVehicle)?;
        // Every vehicle belongs to the motor pool, so its side is the pool's side.
        if s.side != input.pool_side {
            return Err(Refusal::WrongSide);
        }
        let g = m.add_group(s.side, &s.callsign).map_err(|_| Refusal::DuplicateCallsign)?;
        for u in &s.units {
            m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
        }
        m.add_waypoint(g, Waypoint::GetIn(truck)).map_err(|_| Refusal::UnknownVehicle)?;
        let ride = m.add_waypoint(g, Waypoint::Move(input.destination)).map_err(|_| Refusal::OutOfMap)?;
        m.add_waypoint(g, Waypoint::GetOut(input.destination)).map_err(|_| Refusal::OutOfMap)?;
        m.sync_waypoints((g, ride), (pool, pool_move)).map_err(|_| Refusal::UnknownGroup)?;
    }
    m.validate().map_err(|_| Refusal::WrongSide)?;
    Ok(m.export())
}
