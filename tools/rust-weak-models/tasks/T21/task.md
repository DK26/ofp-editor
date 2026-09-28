Create one West group with the callsign "Player" that contains every unit of
`input.units` (in order, with class, label, position and rank).

Add two triggers, each covering the whole map: the mission is lost when no West
units remain anywhere on the map, and the mission is won with `input.win_ending` when
the player calls radio `input.win_channel`. Neither trigger may repeat.
