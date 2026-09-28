Create one West group with the callsign `input.callsign` that contains every unit of
`input.units` (in order, with class, label, position and rank). It moves to
`input.start` (its first waypoint) and then to `input.bridge` (its second).

Radio `input.release` releases the group: a radio trigger that covers the whole map,
fires once and has no other effect is synchronised with the first waypoint, so the
group waits there until the call.

When the group reaches the bridge, a second trigger synchronised with the bridge
waypoint (no activation condition; its area is the square centred on the bridge with
half side `input.bridge_half_m` metres, not rotated) counts down between
`input.minutes[0]` and `input.minutes[2]` minutes (typically `input.minutes[1]`) and
then ends the mission with `input.ending`.
