Combine the two drafts into one mission. Create the groups of `input.first` in
order, then the groups of `input.second` in order, each with its callsign, side and
units (in order, with class, label, position and rank). Each group moves through its
`route`: one MOVE waypoint per point, in order.

If a group of the second draft has a callsign that is already used, add "-2" to its
callsign (the inputs never need more than one rename).

Then add every synchronisation of both drafts. A synchronisation names two groups
by their position in their own draft's `groups` list and two waypoints by index,
all counted from 0. Keep each draft's synchronisations pointing at that draft's own
groups.
