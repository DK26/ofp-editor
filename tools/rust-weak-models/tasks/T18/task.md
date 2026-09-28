Create one West group with the callsign "Orders" that contains every unit of
`input.units` (soldiers and vehicles alike, in order, with class, label, position and
rank).

Build its waypoint plan from `input.orders`, in order: `Move` is a MOVE waypoint,
`Hunt` a SEEK_AND_DESTROY, `Board(label)` a GET_IN into the vehicle with that label,
`Dismount` a GET_OUT, `Hold` a HOLD and `Loop` a CYCLE.

Process the orders in sequence and refuse at the first bad order:
- `Refusal::InvalidSequence` for any order after `Hold` or `Loop`, for a `Dismount`
  with no `Board` before it (since the last `Dismount`), and for a `Loop` with fewer
  than two `Move`/`Hunt` orders before it;
- `Refusal::UnknownVehicle` for a `Board` whose label is not a vehicle of the roster.

For a single order, check the sequence rules before the vehicle label.
