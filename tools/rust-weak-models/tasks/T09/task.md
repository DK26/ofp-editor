Create one West group with the callsign "Defenders" that contains every unit of
`input.units` (in order, with class, label, position and rank).

Whenever East units enter the town (the square centred on `input.town`, half side
`input.town_half_m` metres, not rotated), the mission should end with ending 2.

`input.repeating` is true when the brief asked for this ending to repeat; return
`Refusal::RepeatingEnd` in that case.
