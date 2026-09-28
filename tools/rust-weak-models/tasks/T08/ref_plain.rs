use mb::{Exported, Mission, Side, Waypoint};
use mb_spec::Refusal;
use mb_spec::t08::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Assault").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    let truck = m.vehicle_by_label(&input.truck).ok_or(Refusal::UnknownVehicle)?;
    for wp in [
        Waypoint::GetIn(truck),
        Waypoint::Move(input.drop),
        Waypoint::GetOut(input.drop),
        Waypoint::SeekAndDestroy(input.target),
    ] {
        m.add_waypoint(g, wp).map_err(|_| Refusal::OutOfMap)?;
    }
    m.validate().map_err(|_| Refusal::InvalidSequence)?;
    Ok(m.export())
}
