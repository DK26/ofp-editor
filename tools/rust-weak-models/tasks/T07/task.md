Create one West group with the callsign "Rover" that contains every unit of
`input.units` (in order, with class, label, position and rank).

The group patrols the points `input.a`, `input.b` and `input.c` in a loop, in that
order. On every round the patrol should also stop by the fuel depot at `input.depot`
(a MOVE waypoint there).
