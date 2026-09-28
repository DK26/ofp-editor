Create one West group with the callsign "Holdout" that contains every unit of
`input.units` (in order, with class, label, position and rank).

Add a trigger over the square centred on `input.post` (half side
`input.post_half_m` metres, not rotated): once West units have been present there
continuously for between the shortest and the longest duration (typically the
typical one), the mission ends with ending 3. The three durations, in seconds, are in
`input.seconds` in the brief's order: longest, shortest, typical.

Return `Refusal::TimerOrder` if the durations are inconsistent: a negative value, or
the typical duration outside the range from the shortest to the longest.
