use mb::{AcceptsWaypoints, AnyPlan, Exported, Mission, Order, Plan, Pos};
use mb_spec::t23::{Input, OrderIn};
use mb_spec::{Point, Refusal};

fn pos(p: Point) -> Result<Pos, Refusal> {
    Pos::new(p.x, p.z).map_err(|_| Refusal::OutOfMap)
}

/// Appends MOVE entry, SEEK_AND_DESTROY target, MOVE entry to any plan that still
/// takes waypoints, on foot or mounted; the state is kept.
fn clear_the_area<S: AcceptsWaypoints>(plan: Plan<S>, entry: Pos, target: Pos) -> Plan<S> {
    plan.move_to(entry).seek_and_destroy(target).move_to(entry)
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    for grp in &input.groups {
        let g = m.add_group(grp.side, &grp.callsign).map_err(|_| Refusal::DuplicateCallsign)?;
        for u in &grp.units {
            m.add_unit(g, u.class, &u.label, pos(u.pos)?, u.rank);
        }
        let mut plan = AnyPlan::new();
        for order in &grp.prior {
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
        let (entry, target) = (pos(grp.entry)?, pos(grp.target)?);
        let plan = match plan {
            AnyPlan::Open(p) => AnyPlan::from(clear_the_area(p, entry, target)),
            AnyPlan::Mounted(p) => AnyPlan::from(clear_the_area(p, entry, target)),
            AnyPlan::Closed(_) => return Err(Refusal::InvalidSequence),
        };
        m.assign_plan(g, plan).map_err(|_| Refusal::WrongSide)?;
    }
    let m = m.validate().map_err(|_| Refusal::InvalidSequence)?;
    Ok(m.export())
}
