Build the full scenario. Create three groups in this order, each with its callsign
and units (in order, with class, label, position and rank):
- `input.patrol` (West) patrols its `route` in a loop: it moves through the points in
  order and then starts over from the first (the route has at least two points);
- `input.convoy` (West) boards its truck (the vehicle labelled `convoy.truck`),
  drives to `convoy.destination` and dismounts there; its MOVE waypoint is
  synchronised with the patrol's second waypoint;
- `input.enemy` (East) moves through its `route` (one MOVE waypoint per point).

Add three triggers:
1. release: covers the whole map; when the player calls radio `input.release`, the
   group with the callsign `input.release_callsign` leaves its first waypoint (the
   trigger is synchronised with that waypoint);
2. win: when West units have been present in the objective (the square centred on
   `input.objective`, half side `input.objective_half_m` metres, not rotated)
   continuously for between `hold_minutes[0]` and `hold_minutes[2]` minutes
   (typically `hold_minutes[1]`), the mission ends with ending 1;
3. loss: covers the whole map; when no West units remain, the mission is lost.

No trigger repeats. Return `Refusal::UnknownGroup` if `input.release_callsign` is not
the callsign of one of the three groups.
