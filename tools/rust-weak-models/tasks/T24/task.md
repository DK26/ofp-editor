First create a West group with the callsign "HQ" that contains every unit of
`input.hq` (it gets no waypoints). Then create the groups of `input.groups` in
order, each with its callsign, side and units (in order, with class, label, position
and rank).

Keep one plan per group of `input.groups` in a list. Apply `input.edits` in input
order: each edit adds a MOVE waypoint at `point` to the plan of the group at position
`group` of `input.groups` (counted from 0). Then close each group's plan as its
`close` says: `Loop` adds a CYCLE, `Hold(p)` adds a HOLD at `p`, `Open` adds nothing.

Return `Refusal::InvalidSequence` if a group that should loop has fewer than two
waypoints.
