Create the groups of `input.groups` in order, each with its callsign, side and units
(in order, with class, label, position and rank). Each group moves through its
`route`: one MOVE waypoint per point, in order.

The group with the callsign `input.waiting` waits at its waypoint number
`input.number` (1 is its first waypoint) until the player calls radio
`input.channel`. The radio trigger covers the whole map, fires once and has no other
effect. The waypoint number always exists.

Return `Refusal::UnknownGroup` if no group has the callsign `input.waiting`.
