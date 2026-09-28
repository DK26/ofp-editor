use mb::{AnyPlan, Exported, Mission, Order, Pos, Side};
use mb_spec::t18::{Input, OrderIn};
use mb_spec::{Point, Refusal};

fn pos(p: Point) -> Result<Pos, Refusal> {
    Pos::new(p.x, p.z).map_err(|_| Refusal::OutOfMap)
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Orders").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, pos(u.pos)?, u.rank);
    }
    let mut plan = AnyPlan::new();
    for order in &input.orders {
        // Sequence rules come before the vehicle label, so a closed plan is refused first.
        if plan.is_closed() {
            return Err(Refusal::InvalidSequence);
        }
        let next = match order {
            OrderIn::Move(p) => Order::Move(pos(*p)?),
            OrderIn::Hunt(p) => Order::SeekAndDestroy(pos(*p)?),
            OrderIn::Board(label) => Order::GetIn(m.vehicle(label).ok_or(Refusal::UnknownVehicle)?),
            OrderIn::Dismount(p) => Order::GetOut(pos(*p)?),
            OrderIn::Hold(p) => Order::Hold(pos(*p)?),
            OrderIn::Loop => Order::Cycle,
        };
        plan = plan.apply(next).map_err(|_| Refusal::InvalidSequence)?;
    }
    m.assign_plan(g, plan).map_err(|_| Refusal::WrongSide)?;
    let m = m.validate().map_err(|_| Refusal::InvalidSequence)?;
    Ok(m.export())
}
