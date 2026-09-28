Create two West groups, `input.first` and then `input.second`, each with its callsign
and units (in order, with class, label, position and rank; each wave's vehicle is
among its own units). Each group boards its own vehicle (the one labelled
`wave.vehicle`) and then moves through `input.route` (one MOVE waypoint per point).

When the player calls radio `input.release`, the first wave leaves at once and the
second wave `input.delay_s` seconds later. Add two radio triggers on that channel,
each covering the whole map and firing once: the first without a timer, synchronised
with the first wave's boarding waypoint; the second with a countdown of exactly
`input.delay_s` seconds (min, typical and max all equal to it), synchronised with the
second wave's boarding waypoint.

Return `Refusal::UnknownVehicle` if a wave's vehicle label is not a vehicle.
