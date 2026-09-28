use mb::{Degrees, Exported, Metres, Mission, Pos, Side};
use mb_spec::Refusal;
use mb_spec::t22::Input;

pub fn solve(input: &Input) -> Result<Exported, Refusal> {
    let anchor = Pos::new(input.anchor.x, input.anchor.z).map_err(|_| Refusal::OutOfMap)?;
    let mut m = Mission::new();
    let g = m.add_group(Side::West, "Ring").map_err(|_| Refusal::DuplicateCallsign)?;
    for u in &input.units {
        let pos = anchor
            .offset(Degrees::new(u.bearing_deg), Metres::from_km(u.distance_km))
            .map_err(|_| Refusal::OutOfMap)?;
        m.add_unit(g, u.class, &u.label, pos, u.rank);
    }
    let m = m.validate().map_err(|_| Refusal::OutOfMap)?;
    Ok(m.export())
}
