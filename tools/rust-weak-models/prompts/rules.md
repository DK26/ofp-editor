The map is 12,800 m by 12,800 m. `x` grows to the east and `z` to the north; both run
from 0 to 12,800 m.

Sides: West, East, Resistance, Civilian. Soldier classes: Rifleman, MachineGunner,
AtSoldier, Medic, Officer. Vehicle classes: Truck, Jeep, Apc. Ranks from lowest to
highest: Private, Corporal, Sergeant, Lieutenant, Captain, Major, Colonel.

A group has a side, a unique callsign, one or more units of that side, a leader (set
explicitly, otherwise the highest rank, the first listed on ties) and a waypoint plan.
Vehicles are units too and belong to a group.

Waypoints: MOVE, SEEK_AND_DESTROY (move and engage), HOLD (stay there), GET_IN (board
a vehicle), GET_OUT (dismount at a point) and CYCLE (repeat the plan from the first
waypoint). Waypoints are numbered from 0: "the second waypoint" of a brief is number 1.

Synchronisation: two waypoints can be synchronised (each waits for the other). A
trigger can be synchronised with a waypoint: the waypoint waits until the trigger
fires, and a trigger without activation fires when the group reaches the waypoint.

A trigger has a rectangular area (centre, half sizes a and b in metres, rotation in
degrees); an activation (none, a side present, a side not present, a side detected by
another side, or a radio call on a channel Alpha to Juliet); it fires once (the
default) or repeatedly; it may have a timer, either a countdown (fires between min and
max seconds after the condition became true, typically mid) or a timeout (the
condition must stay true between min and max seconds); and an effect: none, END with
ending 1 to 6, or LOSE.

Bearings are degrees clockwise from north: distance d at bearing b from (x, z) lands
at (x + d * sin b, z + d * cos b). Durations are stored in seconds and distances in
metres.

Rules:
R1 CYCLE must be the last waypoint and needs at least two earlier MOVE or SEEK_AND_DESTROY waypoints.
R2 HOLD is terminal: nothing may follow HOLD.
R3 GET_OUT is valid only after a GET_IN earlier in the same plan with no GET_OUT between them.
R4 GET_IN targets an existing vehicle unit of the same side.
R5 Every sync reference must name an existing group and waypoint.
R6 Timers: 0 <= min <= mid <= max, in seconds.
R7 A side cannot be detected by itself.
R8 An END or LOSE trigger must fire once, never repeatedly.
R9 Groups have at least one unit; callsigns are unique; all units share the group's side.
R10 Every position lies inside the map.
R11 Only a mission that passed validation, and was not changed after it, may be exported.

When the task names a `Refusal` for a situation, return that `Err(Refusal::...)`
instead of building the mission. Never panic.
