Create one group with the callsign "Scouts" on side `input.watched` that contains
every unit of `input.units` (in order, with class, label, position and rank).

Add a trigger over the square area centred on `input.area` (half side
`input.area_half_m` metres, not rotated). It fires when the `input.watched` side is
detected by the `input.watcher` side, and when it fires the mission is lost.

Return `Refusal::SameSide` if `input.watcher` and `input.watched` are the same side.
