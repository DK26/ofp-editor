Create the groups of `input.groups` in order, each with its callsign, side and units
(in order, with class, label, position and rank).

Each group's plan starts with its `prior` orders, converted order by order: `Move` is
a MOVE waypoint, `Hunt` a SEEK_AND_DESTROY, `Board(label)` a GET_IN into the vehicle
with that label, `Dismount` a GET_OUT, `Hold` a HOLD and `Loop` a CYCLE. The prior
orders are always a valid sequence and name existing vehicles.

Then append a clear-the-area sequence to every group: move to `entry`, seek and
destroy at `target`, move back to `entry`. Write this sequence once, as a reusable
helper, and use it for every group. Some groups are still aboard a vehicle when the
sequence starts; they stay aboard.

Return `Refusal::InvalidSequence` if a group's plan can no longer take waypoints
(its prior orders end with `Hold` or `Loop`).
