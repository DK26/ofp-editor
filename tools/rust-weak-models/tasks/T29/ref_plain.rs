use mb::{Activation, Area, Exported, Mission, Side, Timer, TimerKind, Trigger, Waypoint};
use mb_spec::Refusal;
use mb_spec::t29::{Input, WaveIn};

fn add_wave(m: &mut Mission, wave: &WaveIn, route: &[mb::Point]) -> Result<u32, Refusal> {
    let g = m.add_group(Side::West, &wave.callsign).map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &wave.units {
        m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    let vehicle = m.vehicle_by_label(&wave.vehicle).ok_or(Refusal::UnknownVehicle)?;
    m.add_waypoint(g, Waypoint::GetIn(vehicle)).map_err(|_| Refusal::UnknownVehicle)?;
    for p in route {
        m.add_waypoint(g, Waypoint::Move(*p)).map_err(|_| Refusal::OutOfMap)?;
    }
    Ok(g)
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let first = add_wave(&mut m, &input.first, &input.route)?;
    let second = add_wave(&mut m, &input.second, &input.route)?;
    let now = m
        .add_trigger(Trigger::new(Area::whole_map(), Activation::Radio(input.release)))
        .map_err(|_| Refusal::OutOfMap)?;
    m.sync_trigger(now, (first, 0)).map_err(|_| Refusal::UnknownGroup)?;
    let mut later = Trigger::new(Area::whole_map(), Activation::Radio(input.release));
    let d = input.delay_s;
    later.timer = Some(Timer::new(TimerKind::Countdown, d, d, d).map_err(|_| Refusal::TimerOrder)?);
    let later = m.add_trigger(later).map_err(|_| Refusal::OutOfMap)?;
    m.sync_trigger(later, (second, 0)).map_err(|_| Refusal::UnknownGroup)?;
    m.validate().map_err(|_| Refusal::UnknownVehicle)?;
    Ok(m.export())
}
