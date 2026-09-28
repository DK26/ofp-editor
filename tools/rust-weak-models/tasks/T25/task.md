Create one group per entry of `input.roster`, in order, all on side `input.side`,
each with the entry's callsign and units (in order, with class, label, position and
rank), and export the mission.

The roster may have several problems. Find every one of them, not just the first:
- `Problem::DuplicateCallsign(callsign)` for each entry whose callsign an earlier
  entry already used;
- `Problem::EmptyGroup(callsign)` for each entry without units;
- `Problem::OutOfMap(label)` for each unit placed outside the map.

If there is at least one problem, return `Refusal::Many` with all of them sorted
ascending (the derived order of `Problem`) instead of exporting.
