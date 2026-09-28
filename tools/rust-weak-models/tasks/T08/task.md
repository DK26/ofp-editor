Create one West group with the callsign "Assault" that contains every unit of
`input.units` (soldiers and vehicles alike, in order, with class, label, position and
rank).

The infantry boards the truck labelled `input.truck`, drives to `input.drop`,
dismounts there and then seeks and destroys at `input.target`.

Return `Refusal::UnknownVehicle` if no vehicle in the roster has the label
`input.truck`.
