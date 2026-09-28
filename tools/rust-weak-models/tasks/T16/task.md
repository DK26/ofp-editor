Create the motor-pool group first (callsign `input.pool_callsign`, side
`input.pool_side`, units `input.vehicles`), then one group per squad of
`input.squads`, in order, each with its callsign, side and units (every unit in
order, with class, label, position and rank).

The motor pool drives to `input.destination` (one MOVE waypoint). Each squad boards
its own truck (the vehicle labelled `squad.truck`), rides to `input.destination` and
dismounts there. The squads move in step with the convoy: synchronise each squad's
MOVE waypoint with the motor pool's MOVE waypoint.

Check the squads in order and refuse at the first problem: return
`Refusal::UnknownVehicle` if no vehicle has the squad's truck label, and
`Refusal::WrongSide` if that vehicle belongs to a different side than the squad.
