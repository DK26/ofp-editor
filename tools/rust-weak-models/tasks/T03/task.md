Create one Resistance group with the callsign "Sentry" that contains every unit of
`input.units` (in order, with class, label, position and rank). The group walks
through `input.points` in order and stays at the last point for the rest of the
mission: one MOVE waypoint for each point except the last, then a HOLD waypoint at
the last point. `input.points` always has at least one point.
