---
id: show-waypoint
label: Show waypoint (and the waypoint Description)
aliases: ["show waypoint", showWP, "waypoints not showing", "hidden waypoints", "cadet only", "waypoint description", "waypoint text"]
ui: "Waypoint dialog > Show waypoint; Waypoint dialog > Description"
---

# Show waypoint (and the waypoint Description)

## In one sentence

"Show waypoint" decides whether the player sees his group's route on the in-game map, and a brand-new waypoint starts at "Never", which is why so many first missions seem to have no waypoints.

## What it really does

- Three values: Never, Cadet only (the engine's "easy" setting), Always (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/Path/ArcadeWaypoint.hpp#L106-L111`).
- A waypoint created in the editor starts at **Never** (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.cpp#L1033-L1052`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapExt.cpp#L2585-L2587`). A hand-written `mission.sqm` (format version 10 or later) without the key loads as Cadet only; older files store a yes/no `show` flag instead (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.cpp#L1118-L1134`).
- The in-game map draws the player group's waypoints when the value is Always, or Cadet only while the game's easy mode is on (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapMain.cpp#L385-L459`). That is the same flag the `cadetMode` script command reports (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Game/Commands/GameStateExtGrp.cpp#L407-L410`).
- The floating in-world marker for the current waypoint shows the Description, or the type's name when there is none, or a "waiting" text while the group is held (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/InGame/InGameUIDrawCursor.cpp#L1468-L1515`). That code does not read "Show waypoint"; it is gated by the HUD difficulty option or compass view (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/InGame/InGameUIDrawCursor.cpp#L1328`). What players see in practice needs a probe (unverified).

## When to use it

- Always: the player's route on the map at every difficulty (tutorial-style missions).
- Cadet only: hand-holding for beginners, a clean map for veterans.
- Never: routes the player should work out from the briefing.

## Gotchas

- "My waypoints don't show": check Show waypoint first; the editor default is Never.
- The Description is only a label. Giving a waypoint a Description does not make it visible (folk myth).
- It matters only for the player's own group: this map code draws only that group's waypoints.
- The "waiting" label means the group is held by its Condition or a sync partner ([synchronisation](synchronisation.md)).

## Tiny example

```text
Player group  WP1 MOVE  Description: "Rally point"  Show waypoint: Always
              WP2 SAD   Description: "Clear the village"  Show waypoint: Cadet only
```

## Try it

1. Give the player's group two waypoints with the settings above.
2. Preview on Cadet, open the map, then switch to Veteran and compare.
3. Set WP1 to Never and check the map again.

## Related

[waypoint-lifecycle](waypoint-lifecycle.md) · [player-and-playable](player-and-playable.md) · [synchronisation](synchronisation.md)

## Profiles

- **cwr:** as cited.
- **ce:** `ArcadeTemplate.cpp` differs (+3 lines, e.g. the default at CE `#L1055`); `InGameUIDrawCursor.cpp` differs (+9 lines, CE `#L1337`, `#L1477-L1524`). `UIMapMain.cpp`, `UIMapExt.cpp`, `GameStateExtGrp.cpp` and `ArcadeWaypoint.hpp` are identical.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified).
