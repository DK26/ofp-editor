use mb::{Exported, Mission, Plan, Pos, Side};
use mb_spec::t08::Input;
use mb_spec::{Point, Refusal};

fn pos(p: Point) -> Result<Pos, Refusal> {
    Pos::new(p.x, p.z).map_err(|_| Refusal::OutOfMap)
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Assault").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, pos(u.pos)?, u.rank);
    }
    let truck = m.vehicle(&input.truck).ok_or(Refusal::UnknownVehicle)?;
    let drop = pos(input.drop)?;
    let plan = Plan::new().get_in(truck).move_to(drop).get_out(drop).seek_and_destroy(pos(input.target)?);
    m.assign_plan(g, plan).map_err(|_| Refusal::WrongSide)?;
    let m = m.validate().map_err(|_| Refusal::InvalidSequence)?;
    Ok(m.export())
}
