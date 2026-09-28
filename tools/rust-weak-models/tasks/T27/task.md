The input is a raw draft with numeric references, some of them broken. Rebuild it.

Create the groups of `input.groups` in order, each with its callsign, side and units
(in order, with class, label, position and rank); each group moves through its
`route` (one MOVE waypoint per point).

Add one trigger per raw trigger, in order: a radio trigger on `channel` that covers
the whole map, fires once, has no other effect, and is synchronised with every
waypoint in its `syncs`. A reference is broken if its `group` is not a position in
`input.groups` or its `waypoint` is not an index of that group's route (both count
from 0). Drop broken references and list them in the export note: in input order,
separated by ", ", each written as `t<trigger>:<group>:<waypoint>` with the numbers
from the input (triggers counted from 0), for example `t0:5:0, t1:1:9`. Set no note
if nothing was dropped.

Return `Refusal::EmptyGroup` if any group has no units.
