---
id: placement-radius
label: Placement radius and random start markers
aliases: [placement, "placement radius", "random position", "random start", "start markers", "link unit to marker"]
ui: "Unit dialog > Placement radius; Waypoint dialog > Placement radius; Groups mode (F2): drag unit to marker"
---

# Placement radius and random start markers

## In one sentence

Placement radius rolls a new start spot inside a circle every time the mission starts, and linking a unit to markers adds whole alternative start points; it is not an even scatter, because the engine prefers easy ground.

## What it really does

- **Markers first:** if a unit is linked to n markers, it starts at its own spot or at one of the markers, each with equal odds of 1/(n+1). Markers are matched by name (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L965-L984`).
- **Then the radius:** the engine tries up to 100 random points inside the circle, throws away any whose surrounding terrain cells are impassable for a reference vehicle, and keeps the one with the **lowest terrain cost**. If none is valid, the unit stays at the centre. A radius of 0.1 m or less means no search at all (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L628-L691`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/WorldInit.cpp#L550-L553`).
- With a radius above 0, the engine also shifts the unit to a nearby collision-free spot (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1090-L1094`).
- **Waypoints:** a waypoint's radius takes the first random point that passes the same terrain check and has free space (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L694-L739`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L2096-L2100`).
- Sound sources and mines are scattered evenly in their circle instead (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L855-L939`).
- Everything is rolled once, at mission start, and stays fixed for the whole mission.

## When to use it

- Replay value: the enemy officer is somewhere in the village, not always in the same house.
- Patrol routes that differ between plays (waypoint radius).
- Two or three hand-picked hideouts: link the unit to markers.

## Gotchas

- Not uniform: with some road or open ground in the circle, units probably end up there more often (inferred from the lowest-cost rule; unverified in play).
- In-formation members are snapped back behind their leader, so only the **leader's** radius and markers matter ([special-placement](special-placement.md)).
- A looping patrol does not re-roll its waypoint spots on each lap.
- Scripts that expect a unit at an exact spot break once a radius is set.

## Tiny example

```text
East officer  Placement radius: 0   linked to markers hideout1, hideout2
Result        starts at his own spot, hideout1 or hideout2 (1/3 each)
```

## Try it

1. Place a leader with a 150 m radius on mixed terrain; Preview five times and note where he appears.
2. Place two markers, then in Groups mode (F2) drag from the leader to each marker.
3. Preview again and watch him start at the markers too.

## Related

[special-placement](special-placement.md) · [probability-of-presence](probability-of-presence.md) · [condition-of-presence](condition-of-presence.md) · [cycle-waypoint](cycle-waypoint.md)

## Profiles

- **cwr:** as cited.
- **ce:** `AICenterImpl.cpp` and `WorldInit.cpp` are byte-identical.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified).
