Create one East group with the callsign "Guard" that contains every unit of
`input.units` (in order, with class, label, position and rank). The group walks to
`input.gate` and then stays at `input.post` for the rest of the mission.

Return `Refusal::OutOfMap` if any unit or either point lies outside the map.
