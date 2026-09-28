use mb::{Exported, Mission, Plan, Pos, Side};
use mb_spec::t07::Input;
use mb_spec::{Point, Refusal};

fn pos(p: Point) -> Result<Pos, Refusal> {
    Pos::new(p.x, p.z).map_err(|_| Refusal::OutOfMap)
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Rover").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, pos(u.pos)?, u.rank);
    }
    let plan = Plan::new()
        .move_to(pos(input.a)?)
        .move_to(pos(input.b)?)
        .move_to(pos(input.c)?)
        .move_to(pos(input.depot)?)
        .cycle()
        .map_err(|_| Refusal::InvalidSequence)?;
    m.assign_plan(g, plan).map_err(|_| Refusal::EmptyGroup)?;
    let m = m.validate().map_err(|_| Refusal::InvalidSequence)?;
    Ok(m.export())
}
