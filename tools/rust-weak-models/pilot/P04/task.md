Create one West group with the callsign "Taxi" that contains every unit of
`input.units` (soldiers and vehicles alike, in order). The group boards the vehicle
labelled `input.ride`, drives to `input.destination` and dismounts there.

Return `Refusal::UnknownVehicle` if no vehicle in the roster has the label
`input.ride`.
