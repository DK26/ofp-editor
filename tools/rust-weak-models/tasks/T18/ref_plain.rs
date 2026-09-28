use mb::{Exported, Mission, Side, Waypoint};
use mb_spec::Refusal;
use mb_spec::t18::{Input, OrderIn};

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Orders").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    let mut closed = false;
    let mut mounted = false;
    let mut moves = 0;
    for order in &input.orders {
        if closed {
            return Err(Refusal::InvalidSequence);
        }
        let wp = match order {
            OrderIn::Move(p) => {
                moves += 1;
                Waypoint::Move(*p)
            }
            OrderIn::Hunt(p) => {
                moves += 1;
                Waypoint::SeekAndDestroy(*p)
            }
            OrderIn::Board(label) => {
                let v = m.vehicle_by_label(label).ok_or(Refusal::UnknownVehicle)?;
                mounted = true;
                Waypoint::GetIn(v)
            }
            OrderIn::Dismount(p) => {
                if !mounted {
                    return Err(Refusal::InvalidSequence);
                }
                mounted = false;
                Waypoint::GetOut(*p)
            }
            OrderIn::Hold(p) => {
                closed = true;
                Waypoint::Hold(*p)
            }
            OrderIn::Loop => {
                if moves < 2 {
                    return Err(Refusal::InvalidSequence);
                }
                closed = true;
                Waypoint::Cycle
            }
        };
        m.add_waypoint(g, wp).map_err(|_| Refusal::OutOfMap)?;
    }
    m.validate().map_err(|_| Refusal::InvalidSequence)?;
    Ok(m.export())
}
