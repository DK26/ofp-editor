Create one East group with the callsign "Team" that contains every unit of
`input.units` (in order, with class, label, position and rank). The team moves to
`input.first` and then on to `input.second`.

Return `Refusal::OutOfMap` if any unit or either point lies outside the map.
