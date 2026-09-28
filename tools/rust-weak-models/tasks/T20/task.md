First build the mission of the brief: one West group with the callsign "Alpha" that
contains every unit of `input.units` (in order, with class, label, position and
rank), patrolling `input.patrol` in a loop (it moves through the points in order and
then starts over from the first; there are always at least two points).

Then, as a late addition, add the trigger described in `input.late`: when the player
calls radio `late.channel`, a countdown between `late.min_s` and `late.max_s` seconds
(typically `late.mid_s`) runs, and then the mission ends with `late.ending`. The
trigger covers the whole map. Export the final mission.

Return `Refusal::TimerOrder` if the late trigger's timer is inconsistent (a negative
value, or not min <= mid <= max).
