use mb::{Activation, Area, Effect, Exported, Mission, MissionError, Repeat, Timer, TimerKind, Trigger, Waypoint};
use mb_spec::Refusal;
use mb_spec::t30::{ActIn, EffectIn, Input, OrderIn};

/// The refusal the task names for each library error.
fn refusal(e: &MissionError) -> Refusal {
    match e {
        MissionError::UnknownGroup { .. } | MissionError::UnknownWaypoint { .. } | MissionError::UnknownTrigger { .. } => {
            Refusal::UnknownGroup
        }
        MissionError::UnknownUnit { .. } | MissionError::NotAVehicle { .. } => Refusal::UnknownVehicle,
        MissionError::DuplicateCallsign { .. } => Refusal::DuplicateCallsign,
        MissionError::OutOfMap { .. } => Refusal::OutOfMap,
        MissionError::NotInGroup { .. } | MissionError::EmptyGroup { .. } => Refusal::EmptyGroup,
        MissionError::CycleNotLast { .. }
        | MissionError::TooFewWaypoints { .. }
        | MissionError::AfterHold { .. }
        | MissionError::GetOutWithoutGetIn { .. } => Refusal::InvalidSequence,
        MissionError::WrongSide { .. } => Refusal::WrongSide,
        MissionError::TimerOrder { .. } => Refusal::TimerOrder,
        MissionError::SameSide { .. } => Refusal::SameSide,
        MissionError::RepeatingEnd { .. } => Refusal::RepeatingEnd,
    }
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    for grp in &input.groups {
        let g = m.add_group(grp.side, &grp.callsign).map_err(|e| refusal(&e))?;
        for u in &grp.units {
            m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|e| refusal(&e))?;
        }
    }
    for plan in &input.plans {
        let g = m.group_by_callsign(&plan.callsign).ok_or(Refusal::UnknownGroup)?;
        for order in &plan.orders {
            let wp = match order {
                OrderIn::Move(p) => Waypoint::Move(*p),
                OrderIn::Hunt(p) => Waypoint::SeekAndDestroy(*p),
                OrderIn::Board(label) => Waypoint::GetIn(m.vehicle_by_label(label).ok_or(Refusal::UnknownVehicle)?),
                OrderIn::Dismount(p) => Waypoint::GetOut(*p),
                OrderIn::Hold(p) => Waypoint::Hold(*p),
                OrderIn::Loop => Waypoint::Cycle,
            };
            m.add_waypoint(g, wp).map_err(|e| refusal(&e))?;
        }
    }
    for t in &input.triggers {
        let act = match t.act {
            ActIn::Radio(r) => Activation::Radio(r),
            ActIn::Present(s) => Activation::Present(s),
            ActIn::NotPresent(s) => Activation::NotPresent(s),
            ActIn::DetectedBy { watcher, watched } => Activation::DetectedBy { detector: watcher, detected: watched },
        };
        let mut trig = Trigger::new(Area::new(t.centre, t.half_m, t.half_m, 0.0), act);
        if t.repeating {
            trig.repeat = Repeat::Repeatedly;
        }
        if let Some([lo, md, hi]) = t.countdown_s {
            trig.timer = Some(Timer::new(TimerKind::Countdown, lo, md, hi).map_err(|e| refusal(&e))?);
        }
        trig.effect = match t.effect {
            EffectIn::None => Effect::None,
            EffectIn::End(e) => Effect::End(e),
            EffectIn::Lose => Effect::Lose,
        };
        let id = m.add_trigger(trig).map_err(|e| refusal(&e))?;
        if let Some((callsign, number)) = &t.sync {
            let g = m.group_by_callsign(callsign).ok_or(Refusal::UnknownGroup)?;
            m.sync_trigger(id, (g, number.saturating_sub(1))).map_err(|e| refusal(&e))?;
        }
    }
    // Rules checked only on the whole mission (sequence, sides, R7, R8, empty groups).
    m.validate().map_err(|errors| errors.first().map(refusal).unwrap_or(Refusal::InvalidSequence))?;
    Ok(m.export())
}
