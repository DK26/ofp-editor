use mb::{Activation, AnyPlan, Area, Degrees, Exported, Metres, Mission, Order, PlanError, Pos, Seconds, Timer, TriggerBuilder};
use mb_spec::t30::{ActIn, EffectIn, Input, OrderIn};
use mb_spec::{Point, Refusal};

fn pos(p: Point) -> Result<Pos, Refusal> {
    Pos::new(p.x, p.z).map_err(|_| Refusal::OutOfMap)
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    for grp in &input.groups {
        if grp.units.is_empty() {
            return Err(Refusal::EmptyGroup);
        }
        let g = m.add_group(grp.side, &grp.callsign).map_err(|_| Refusal::DuplicateCallsign)?;
        for u in &grp.units {
            m.add_unit(g, u.class, &u.label, pos(u.pos)?, u.rank);
        }
    }
    for plan in &input.plans {
        let g = m.group(&plan.callsign).ok_or(Refusal::UnknownGroup)?;
        let mut orders = AnyPlan::new();
        for order in &plan.orders {
            if orders.is_closed() {
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
            orders = orders.apply(next).map_err(|_| Refusal::InvalidSequence)?;
        }
        m.assign_plan(g, orders).map_err(|e| match e {
            PlanError::WrongSide { .. } => Refusal::WrongSide,
            PlanError::EmptyGroup { .. } => Refusal::EmptyGroup,
            PlanError::AlreadyAssigned { .. } | PlanError::ForeignId => Refusal::UnknownGroup,
        })?;
    }
    for t in &input.triggers {
        let act = match t.act {
            ActIn::Radio(r) => Activation::radio(r),
            ActIn::Present(s) => Activation::present(s),
            ActIn::NotPresent(s) => Activation::not_present(s),
            ActIn::DetectedBy { watcher, watched } => Activation::detected_by(watched, watcher).map_err(|_| Refusal::SameSide)?,
        };
        let half = Metres::new(t.half_m);
        let builder = TriggerBuilder::new(Area::new(pos(t.centre)?, half, half, Degrees::new(0.0))).activation(act);
        let builder = match t.countdown_s {
            Some([lo, md, hi]) => builder.timer(
                Timer::countdown(Seconds::new(lo), Seconds::new(md), Seconds::new(hi)).map_err(|_| Refusal::TimerOrder)?,
            ),
            None => builder,
        };
        // Repeat and effect are type states, so each combination is its own branch.
        let id = match (t.repeating, &t.effect) {
            (true, EffectIn::None) => m.add_trigger(builder.repeating()),
            (true, _) => return Err(Refusal::RepeatingEnd),
            (false, EffectIn::None) => m.add_trigger(builder),
            (false, EffectIn::End(e)) => m.add_trigger(builder.ends_mission(*e)),
            (false, EffectIn::Lose) => m.add_trigger(builder.loses_mission()),
        };
        if let Some((callsign, number)) = &t.sync {
            let g = m.group(callsign).ok_or(Refusal::UnknownGroup)?;
            let wp = m.waypoint(g, number.saturating_sub(1)).ok_or(Refusal::UnknownGroup)?;
            m.sync_trigger(id, wp);
        }
    }
    let m = m.validate().map_err(|_| Refusal::InvalidSequence)?;
    Ok(m.export())
}
