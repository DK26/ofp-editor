---
id: cycle-waypoint
label: CYCLE waypoint
aliases: [CYCLE, cycle, loop, "patrol loop", "repeat waypoints"]
ui: "Waypoint dialog > Type: CYCLE"
translator-note: "'Magnet' is a picture, not a term. Rule it teaches: CYCLE sends the group to the earlier waypoint, or the start position, nearest to where the CYCLE is placed; there is no target field. Replace it with a local image of pulling toward the nearest thing, never one of returning to where something started (such as a boomerang), which teaches the false 'loops to the start' rule; translate the rule literally."
---

# CYCLE waypoint

## In one sentence

CYCLE is a magnet with no target field: it pulls the group back to whichever earlier waypoint (or the start) lies closest to where you dropped the CYCLE marker, and the group carries on from there, forever.

## What it really does

- When CYCLE becomes current, the engine measures the flat (2D) distance from the CYCLE's position to **every** earlier waypoint, including the hidden waypoint 0 at the leader's start position and the waypoint just before the CYCLE. The nearest one wins; on a tie, the earliest wins (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L400-L433`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L2072-L2078`).
- It re-arms the syncs of every waypoint from that target up to the CYCLE, then continues at the target (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L419-L432`).
- Distances use the waypoint positions after [placement radius](placement-radius.md) was rolled at start, so the loop target is the same on every lap (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L2096-L2100`).
- A CYCLE as a group's only waypoint can only pick waypoint 0, so the group shuttles back to its start.
- Game Logic groups cannot use CYCLE; they only get AND/OR (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcadeWaypoint.cpp#L74-L105`).

## When to use it

- Endless patrols: a guard walking the perimeter, a boat circling the bay.
- A loop that only covers the second half of a route: put the CYCLE near waypoint 2 and waypoint 1 becomes a one-time "approach".

## Gotchas

- **Placement is the only setting.** Drag the CYCLE right next to the waypoint you want to restart from.
- **Folk myths:** "it never jumps to the previous waypoint" and "it must be very close" do not match this engine. Here the previous waypoint and the start position are candidates too, and the nearest candidate simply wins, however far away it is.
- A once-only trigger that has already fired stays fired, so on later laps it no longer holds a synced waypoint.
- To stop a loop, sync a Switch trigger to a waypoint inside it ([trigger-end-types](trigger-end-types.md)).

## Tiny example

```text
WP1 MOVE (north gate)  WP2 MOVE (east tower)  WP3 MOVE (south gate)
WP4 CYCLE placed on top of WP1                -> loops 1 -> 2 -> 3 -> 1 ...
WP4 CYCLE placed next to the group's start    -> loops back to the start (waypoint 0)
```

## Try it

1. Build the three-waypoint patrol and put the CYCLE on WP1. Preview.
2. Drag the CYCLE close to the group's start position and Preview again.
3. Drag it next to WP3 and watch the group stop moving: it keeps "returning" to WP3, and WP3's On Activation runs again on every pass (read from code; in-game probe pending).

## Related

[waypoint-types](waypoint-types.md) · [waypoint-lifecycle](waypoint-lifecycle.md) · [synchronisation](synchronisation.md) · [trigger-end-types](trigger-end-types.md)

## Profiles

- **cwr:** as cited.
- **ce:** `AIArcade.cpp` and `AICenterImpl.cpp` are byte-identical; `UIArcadeWaypoint.cpp` differs but its cited lines match.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified). Later games may behave differently.

## Verification notes

### Consolidation pass (2026-09-27)

- 2026-09-27 (I33-SEED-C; doc 33 pedagogy findings 2 and 11): "In one sentence" used a boomerang, which returns to its thrower and so encodes the "loops to the start" myth. It now uses a magnet pulling the group to the nearest earlier waypoint (or the start). Added a `translator-note` front-matter key naming the rule and warning against "return to origin" images. No engine facts or citations changed.
