use mb::{Exported, Mission, Plan, Pos, Side};
use mb_spec::Refusal;
use mb_spec::p04::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Taxi").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        let pos = Pos::new(u.pos.x, u.pos.z).map_err(|_| Refusal::OutOfMap)?;
        m.add_unit(g, u.class, &u.label, pos, u.rank);
    }
    let ride = m.vehicle(&input.ride).ok_or(Refusal::UnknownVehicle)?;
    let dest = Pos::new(input.destination.x, input.destination.z).map_err(|_| Refusal::OutOfMap)?;
    let plan = Plan::new().get_in(ride).move_to(dest).get_out(dest);
    m.assign_plan(g, plan).map_err(|_| Refusal::WrongSide)?;
    let m = m.validate().map_err(|_| Refusal::InvalidSequence)?;
    Ok(m.export())
}
