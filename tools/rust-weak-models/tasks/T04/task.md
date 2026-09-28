Create one West group with the callsign "Patrol" that contains every unit of
`input.units` (in order, with class, label, position and rank). The group patrols
`input.points` in a loop: it moves through the points in order and then starts over
from the first one, forever.

Return `Refusal::TooFewWaypoints` if fewer than two points are given.
