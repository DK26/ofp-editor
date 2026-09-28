Build the mission from a large brief.

- Create the groups of `input.groups` in order, each with its callsign, side and units
  (in order, with class, label, position and rank).
- For each entry of `input.plans`, build the waypoint plan of the group with that
  callsign from its orders: `Move` is a MOVE waypoint, `Hunt` a SEEK_AND_DESTROY,
  `Board(label)` a GET_IN into the vehicle with that label, `Dismount` a GET_OUT,
  `Hold` a HOLD and `Loop` a CYCLE.
- Then add the triggers of `input.triggers`, in order. The area is the square centred
  on `centre` with half side `half_m` metres, not rotated. The activation comes from
  `act` (`DetectedBy { watcher, watched }` fires when `watched` is detected by
  `watcher`). The trigger fires repeatedly if `repeating`, otherwise once. It has a
  countdown of `countdown_s` (min, typical, max seconds) if given, and the effect
  from `effect`. If `sync` is given, the trigger is synchronised with that waypoint
  (a callsign and a waypoint number, where 1 is the group's first waypoint).

The brief may contain one bad element. Return:
- `Refusal::EmptyGroup` for a group without units;
- `Refusal::OutOfMap` for a unit, an order point or a trigger centre outside the map;
- `Refusal::UnknownGroup` for a plan or a `sync` naming a callsign that is not a
  group, or a `sync` waypoint number that the group's plan does not have;
- `Refusal::UnknownVehicle` for a `Board` label that is not a vehicle;
- `Refusal::WrongSide` for a `Board` into a vehicle of another side;
- `Refusal::InvalidSequence` for an order after `Hold` or `Loop`, a `Dismount` with
  no `Board` before it, or a `Loop` with fewer than two `Move`/`Hunt` orders before it;
- `Refusal::TimerOrder` for an inconsistent countdown (a negative value, or not
  min <= typical <= max);
- `Refusal::SameSide` for a `DetectedBy` whose watcher and watched are the same side;
- `Refusal::RepeatingEnd` for a repeating trigger whose effect is `End` or `Lose`.

A brief without a bad element is exported.
