use mb::{Exported, Mission, Side, offset};
use mb_spec::Refusal;
use mb_spec::t22::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Ring").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        let pos = offset(input.anchor, u.bearing_deg, u.distance_km * 1000.0);
        m.add_unit(g, u.class, &u.label, pos, u.rank).map_err(|_| Refusal::OutOfMap)?;
    }
    m.validate().map_err(|_| Refusal::OutOfMap)?;
    Ok(m.export())
}
