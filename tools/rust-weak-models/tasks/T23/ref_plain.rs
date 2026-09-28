use mb::{Exported, Mission, Point, Waypoint};
use mb_spec::Refusal;
use mb_spec::t23::{Input, OrderIn};

/// Appends MOVE entry, SEEK_AND_DESTROY target, MOVE entry to the group's plan.
fn clear_the_area(m: &mut Mission, group: u32, entry: Point, target: Point) -> Result<(), Refusal> {
    for wp in [Waypoint::Move(entry), Waypoint::SeekAndDestroy(target), Waypoint::Move(entry)] {
        m.add_waypoint(group, wp).map_err(|_| Refusal::OutOfMap)?;
    }
    Ok(())
}

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    for grp in &input.groups {
        let g = m.add_group(grp.side, &grp.callsign).map_err(|_| Refusal::DuplicateCallsign)?;
        for u in &grp.units {
            m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
        }
        let mut closed = false;
        for order in &grp.prior {
            let wp = match order {
                OrderIn::Move(p) => Waypoint::Move(*p),
                OrderIn::Hunt(p) => Waypoint::SeekAndDestroy(*p),
                OrderIn::Board(label) => Waypoint::GetIn(m.vehicle_by_label(label).ok_or(Refusal::UnknownVehicle)?),
                OrderIn::Dismount(p) => Waypoint::GetOut(*p),
                OrderIn::Hold(p) => {
                    closed = true;
                    Waypoint::Hold(*p)
                }
                OrderIn::Loop => {
                    closed = true;
                    Waypoint::Cycle
                }
            };
            m.add_waypoint(g, wp).map_err(|_| Refusal::OutOfMap)?;
        }
        if closed {
            return Err(Refusal::InvalidSequence);
        }
        clear_the_area(&mut m, g, grp.entry, grp.target)?;
    }
    m.validate().map_err(|_| Refusal::InvalidSequence)?;
    Ok(m.export())
}
