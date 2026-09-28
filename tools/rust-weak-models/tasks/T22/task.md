Create one West group with the callsign "Ring" with one unit per entry of
`input.units`, in order, each with its class, label and rank. Place each unit at its
bearing (`bearing_deg`, degrees clockwise from north) and distance (`distance_km`,
kilometres) from `input.anchor`.

Return `Refusal::OutOfMap` if any unit would land outside the map.
