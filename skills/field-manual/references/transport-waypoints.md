---
id: transport-waypoints
label: "Lifts: GET IN, LOAD, GET OUT, UNLOAD, TRANSPORT UNLOAD"
aliases: ["GET IN", LOAD, "GET OUT", UNLOAD, "TR UNLOAD", "transport unload", pickup, "helicopter pickup", "truck pickup", "drop off", insertion]
ui: "Waypoint dialog > Type; Synchronize mode (F5)"
---

# Lifts: GET IN, LOAD, GET OUT, UNLOAD, TRANSPORT UNLOAD

## In one sentence

A pickup is a handshake between two groups: the truck says "I'm here", the infantry say "we're aboard", and only then does the truck drive off.

## What it really does

- **GET IN target:** the vehicle the waypoint is attached to; otherwise, through a sync link that joins exactly two groups (triggers do not count), the first vehicle of the other group with a free passenger seat (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L1515-L1575`).
- GET IN checks its Condition and syncs **before** boarding, so the passengers wait for the transport to reach its synced waypoint. It marks its own syncs done only **after** boarding: every member with an assigned seat is inside (for a player-led group, the leader), or the vehicle is destroyed (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L1613-L1639`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L1717-L1787`). So the transport's synced waypoint holds until the passengers are aboard (read from code; in-game probe pending).
- A GET IN with neither an attached vehicle nor a two-group sync skips the walk entirely and boards the group's own vehicles (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L1577-L1586`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L1641-L1715`).
- **LOAD** orders the group's own units into its own vehicles and moves straight on, without waiting (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L105-L129`).
- **GET OUT:** the whole group, crew included, gets out; finished when the leader is on foot (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L73-L100`).
- **UNLOAD:** the group's own passengers get out, the crew stays; it does not wait (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L132-L181`).
- **TRANSPORT UNLOAD:** passengers from **other** groups are ordered out; finished when none remain (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L184-L256`).
- **MOVE** makes the group board its own vehicles first when the leader is more than 200 m away (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L913-L992`).

## When to use it

- Pickup: transport waypoint at the pickup point (LOAD by convention, or MOVE), synced to the infantry's GET IN.
- Drop-off: TRANSPORT UNLOAD on the transport where the passengers should get out.
- A group with its own trucks: GET OUT or UNLOAD at the destination.

## Gotchas

- LOAD by itself does not wait for anyone; the waiting comes from the sync to a GET IN.
- UNLOAD empties **my** passengers; TRANSPORT UNLOAD empties **other groups'** passengers.
- GET OUT dismounts the crew too, leaving the vehicle empty.
- Editor-made sync lines always join exactly two items; a hand-edited file whose link joins three or more groups disables GET IN's automatic target pick.
- Whether a helicopter lands by itself for a synced pickup was not traced (unverified); test it in Preview.

## Tiny example

```text
Truck   WP1 LOAD at the crossroads   (synced to Squad WP1)   WP2 MOVE to the village   WP3 TR UNLOAD
Squad   WP1 GET IN at the crossroads (synced to Truck WP1)   WP2 MOVE to the village
```

## Try it

1. Build the example with a crewed truck and a separate infantry squad; Preview.
2. Delete the sync line and Preview again: the truck no longer waits.
3. Change WP3 to UNLOAD and see who stays aboard.

## Related

[synchronisation](synchronisation.md) · [waypoint-types](waypoint-types.md) · [special-placement](special-placement.md) · [waypoint-lifecycle](waypoint-lifecycle.md)

## Profiles

- **cwr / ce:** both cited files are byte-identical. **cwa199:** same lineage, not checked against the 1.99 build (unverified).
