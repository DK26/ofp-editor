Create one East group with the callsign "Ambush" that contains every unit of
`input.units` (in order, with class, label, position and rank).

The group moves to `input.ambush` and waits there until West units are present in
the kill zone (the square centred on `input.kill_zone`, half side
`input.kill_zone_half_m` metres, not rotated); then it moves on to
`input.extraction`. The kill-zone trigger fires once and has no other effect.
