---
id: show-ids-and-object-ids
label: "Show IDs and map-object IDs"
aliases: ["show ids", "object id", "building id", "object <id>", "house position", "bridge id", "static object", "map objects"]
ui: "Editor toolbar > Show IDs (Advanced mode only); Waypoints mode: double-click a building"
---

# Show IDs and map-object IDs

## In one sentence

Every house, bridge and tree that comes with the island wears a hidden number tag; "Show IDs" reveals them so you can point at a specific building from a trigger, a waypoint or a script.

## What it really does

- The Show IDs button exists only in Advanced mode; switching to Easy mode hides it and turns IDs off (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapExtDisplay.cpp#L455-L464`).
- The numbers are drawn only when you are zoomed in far enough (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMap.cpp#L1696-L1718`). They come from the island file, not from the mission.
- In scripts, `object 1234` returns that island object only if it is one of the engine's "primary" or "network" object kinds; otherwise it returns a null object (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Game/Commands/GameStateExtObj.cpp#L616-L629`).
- In Waypoints mode, double-clicking a building attaches the waypoint to it (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapExt.cpp#L2604-L2610`). For buildings with interior positions the waypoint dialog then offers a house position, and MOVE sends the group to that spot (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L959-L983`). DESTROY attacks the attached building.
- Linking a trigger to a building gives it the Static activation: Not present becomes true when the building is destroyed or outside the area ([bound-triggers](bound-triggers.md)).
- Unit `id` numbers inside `mission.sqm` are a different thing: internal, and renumbered by the editor.

## When to use it

- "Destroy the bridge" and "blow up the radar hut" objectives.
- Sending a squad into a specific building (house positions).
- Scripts that open, damage or check one particular map object.

## Gotchas

- "What are these numbers?" and "the button is missing": switch to Advanced mode and zoom in.
- Island updates and mods may renumber objects, which silently breaks missions that use raw IDs (unverified; test after island changes).
- A Static trigger counts only objects the engine models as AI entities, so plain objects such as trees probably never count as present ([bound-triggers](bound-triggers.md); which objects qualify is unverified).
- Prefer linking in the editor over typing numbers into scripts: the link is visible and checkable.

## Tiny example

```text
Trigger  linked to the bridge (Static)   Not present   Type: End #1
         area placed over the bridge
Script   _bridge = object 12345          (use the number shown on your island)
```

## Try it

1. Switch to Advanced mode, press Show IDs and zoom in on a village.
2. Link a trigger to a small house (Static, Not present) with a `hint` in On Activation.
3. Preview and destroy the house.

## Related

[bound-triggers](bound-triggers.md) · [waypoint-types](waypoint-types.md) · [empty-vehicles](empty-vehicles.md) · [mission-sections](mission-sections.md)

## Profiles

- **cwr:** as cited.
- **ce:** `UIMapExtDisplay.cpp` differs (CE `#L378-L387`); `UIMap.cpp` differs (CE `#L1698-L1720`); the other cited files are byte-identical.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified).
