use mb::{AnyPlan, Exported, Mission, Order, Pos, Side};
use mb_spec::t24::{CloseIn, Input};
use mb_spec::{Point, Refusal};

fn pos(p: Point) -> Result<Pos, Refusal> {
    Pos::new(p.x, p.z).map_err(|_| Refusal::OutOfMap)
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let hq = m.add_group(Side::West, "HQ").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.hq {
        m.add_unit(hq, u.class, &u.label, pos(u.pos)?, u.rank);
    }
    let mut ids = Vec::with_capacity(input.groups.len());
    for grp in &input.groups {
        let g = m.add_group(grp.side, &grp.callsign).map_err(|_| Refusal::DuplicateCallsign)?;
        for u in &grp.units {
            m.add_unit(g, u.class, &u.label, pos(u.pos)?, u.rank);
        }
        ids.push(g);
    }
    // Plans of different states live together as AnyPlan.
    let mut plans: Vec<AnyPlan> = input.groups.iter().map(|_| AnyPlan::new()).collect();
    for e in &input.edits {
        let slot = plans.get_mut(e.group).ok_or(Refusal::UnknownGroup)?;
        let plan = std::mem::take(slot);
        *slot = plan.apply(Order::Move(pos(e.point)?)).map_err(|_| Refusal::InvalidSequence)?;
    }
    for ((grp, g), plan) in input.groups.iter().zip(ids).zip(plans) {
        let plan = match grp.close {
            CloseIn::Loop => plan.apply(Order::Cycle),
            CloseIn::Hold(p) => plan.apply(Order::Hold(pos(p)?)),
            CloseIn::Open => Ok(plan),
        }
        .map_err(|_| Refusal::InvalidSequence)?;
        m.assign_plan(g, plan).map_err(|_| Refusal::EmptyGroup)?;
    }
    let m = m.validate().map_err(|_| Refusal::InvalidSequence)?;
    Ok(m.export())
}
