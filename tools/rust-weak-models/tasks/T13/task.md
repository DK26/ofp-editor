Create the groups of `input.groups` in order, each with its callsign, side and units
(in order, with class, label, position and rank). Each group moves through its
`route`: one MOVE waypoint per point, in order.

Synchronise the waypoint named by `input.first` with the waypoint named by
`input.second`. Each names a group by callsign and a waypoint by its number in the
brief, where 1 is the group's first waypoint. The waypoint numbers always exist.

Return `Refusal::UnknownGroup` if either callsign is not one of the groups.
