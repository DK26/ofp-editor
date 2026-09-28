Create one group per entry of `input.roster`, in order, all on side `input.side`,
each with the entry's callsign and units (in order, with class, label, position and
rank). Export the mission.

Check the entries in order and refuse at the first problem: return
`Refusal::DuplicateCallsign` for an entry whose callsign an earlier entry already
used, and `Refusal::EmptyGroup` for an entry without units. For a single entry,
check the callsign before the units.
