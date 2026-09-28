use mb::{Exported, Mission, Plan, Pos, Side};
use mb_spec::t03::Input;
use mb_spec::{Point, Refusal};

fn pos(p: Point) -> Result<Pos, Refusal> {
    Pos::new(p.x, p.z).map_err(|_| Refusal::OutOfMap)
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::Resistance, "Sentry").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, pos(u.pos)?, u.rank);
    }
    let (last, rest) = input.points.split_last().ok_or(Refusal::TooFewWaypoints)?;
    let mut plan = Plan::new();
    for p in rest {
        plan = plan.move_to(pos(*p)?);
    }
    let plan = plan.hold(pos(*last)?);
    m.assign_plan(g, plan).map_err(|_| Refusal::EmptyGroup)?;
    let m = m.validate().map_err(|_| Refusal::InvalidSequence)?;
    Ok(m.export())
}
