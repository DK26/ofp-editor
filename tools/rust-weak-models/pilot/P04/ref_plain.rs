use mb::{Exported, Mission, Side, Waypoint};
use mb_spec::Refusal;
use mb_spec::p04::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Taxi").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    let ride = m.vehicle_by_label(&input.ride).ok_or(Refusal::UnknownVehicle)?;
    m.add_waypoint(g, Waypoint::GetIn(ride)).map_err(|_| Refusal::UnknownVehicle)?;
    m.add_waypoint(g, Waypoint::Move(input.destination)).map_err(|_| Refusal::OutOfMap)?;
    m.add_waypoint(g, Waypoint::GetOut(input.destination)).map_err(|_| Refusal::OutOfMap)?;
    m.validate().map_err(|_| Refusal::InvalidSequence)?;
    Ok(m.export())
}
