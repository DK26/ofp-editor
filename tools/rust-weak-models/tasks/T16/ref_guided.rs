use mb::{Exported, Mission, Plan, PlanError, Pos};
use mb_spec::t16::Input;
use mb_spec::{Point, Refusal};

fn pos(p: Point) -> Result<Pos, Refusal> {
    Pos::new(p.x, p.z).map_err(|_| Refusal::OutOfMap)
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let pool = m.add_group(input.pool_side, &input.pool_callsign).map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.vehicles {
        m.add_unit(pool, u.class, &u.label, pos(u.pos)?, u.rank);
    }
    let dest = pos(input.destination)?;
    m.assign_plan(pool, Plan::new().move_to(dest)).map_err(|_| Refusal::EmptyGroup)?;
    let pool_move = m.waypoint(pool, 0).ok_or(Refusal::UnknownGroup)?;
    for s in &input.squads {
        let truck = m.vehicle(&s.truck).ok_or(Refusal::UnknownVehicle)?;
        let g = m.add_group(s.side, &s.callsign).map_err(|_| Refusal::DuplicateCallsign)?;
        for u in &s.units {
            m.add_unit(g, u.class, &u.label, pos(u.pos)?, u.rank);
        }
        let plan = Plan::new().get_in(truck).move_to(dest).get_out(dest);
        m.assign_plan(g, plan).map_err(|e| match e {
            PlanError::WrongSide { .. } => Refusal::WrongSide,
            _ => Refusal::EmptyGroup,
        })?;
        let ride = m.waypoint(g, 1).ok_or(Refusal::UnknownGroup)?;
        m.sync_waypoints(ride, pool_move);
    }
    let m = m.validate().map_err(|_| Refusal::WrongSide)?;
    Ok(m.export())
}
