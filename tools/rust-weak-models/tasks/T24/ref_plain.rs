use mb::{Exported, Mission, Point, Side, Waypoint};
use mb_spec::Refusal;
use mb_spec::t24::{CloseIn, Input};

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let hq = m.add_group(Side::West, "HQ").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.hq {
        m.add_unit(hq, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    let mut ids = Vec::with_capacity(input.groups.len());
    for grp in &input.groups {
        let g = m.add_group(grp.side, &grp.callsign).map_err(|_| Refusal::DuplicateCallsign)?;
        for u in &grp.units {
            m.add_unit(g, u.class, &u.label, u.pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
        }
        ids.push(g);
    }
    // One plan (list of points) per group, filled in edit order.
    let mut plans: Vec<Vec<Point>> = vec![Vec::new(); input.groups.len()];
    for e in &input.edits {
        plans.get_mut(e.group).ok_or(Refusal::UnknownGroup)?.push(e.point);
    }
    for ((grp, g), points) in input.groups.iter().zip(&ids).zip(&plans) {
        for p in points {
            m.add_waypoint(*g, Waypoint::Move(*p)).map_err(|_| Refusal::OutOfMap)?;
        }
        match grp.close {
            CloseIn::Loop => {
                if points.len() < 2 {
                    return Err(Refusal::InvalidSequence);
                }
                m.add_waypoint(*g, Waypoint::Cycle).map_err(|_| Refusal::InvalidSequence)?;
            }
            CloseIn::Hold(p) => {
                m.add_waypoint(*g, Waypoint::Hold(p)).map_err(|_| Refusal::OutOfMap)?;
            }
            CloseIn::Open => {}
        }
    }
    m.validate().map_err(|_| Refusal::InvalidSequence)?;
    Ok(m.export())
}
