---
id: synchronisation
label: Synchronisation (F5)
aliases: [sync, synchronize, synchronise, "synchronization", "sync line", "Synchronize mode", F5, rendezvous, "wait for trigger"]
ui: "Synchronize mode (F5): drag from a waypoint to another waypoint or a trigger"
---

# Synchronisation (F5)

## In one sentence

A sync line is a rope tied between two waypoints, or a waypoint and a trigger: nobody on the rope may move past their knot until everyone tied to it is ready.

## What it really does

- Each drag creates a new link between exactly the two things you connected, and a waypoint can carry many links (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplateFind.cpp#L296-L331`). Dragging a waypoint's line onto empty map removes **all** its links (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplateFind.cpp#L337-L344`). The editor drops links left with only one end, and links with no waypoint end such as trigger-to-trigger links (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.cpp#L1582-L1752`).
- A group still **walks** to its synced waypoint. On arrival it marks its own ends ready, then waits while its Condition is false, any other linked group that still has units has not arrived, or any linked trigger has not fired (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L811-L861`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L309-L369`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L786-L807`).
- Several links on one normal waypoint mean AND: all must be ready.
- Trigger ends start "not ready", become ready when the trigger fires, and go back to "not ready" when a repeating trigger switches off. Triggers never wait for groups (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L755-L760`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1384-L1390`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1512-L1524`).
- The wait has no time limit in the waypoint plan. AI groups get a 600 s wait order, but the plan does not move on until the links clear (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L265`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L827-L839`). What the group does once that order lapses is unverified.
- Exceptions: GET IN is ready only after boarding ([transport-waypoints](transport-waypoints.md)); logic AND/OR are ready on arrival ([logic-gates](logic-gates.md)); a Switch trigger is never "ready", it jumps groups instead ([trigger-end-types](trigger-end-types.md)); CYCLE re-arms the links inside its loop ([cycle-waypoint](cycle-waypoint.md)).
- Links also change what some waypoints do: GET IN, JOIN and JOIN AND LEAD pick their target through a two-group link, and GUARD guards a linked trigger.

## When to use it

- "Wait here until the trigger fires": a waiting waypoint linked to the trigger, then the real destination.
- A coordinated attack: two groups' assault waypoints linked, so both wait for each other.
- Pickups: the transport's waypoint linked to the passengers' GET IN.

## Gotchas

- Linking a trigger to a group's first waypoint does not hold the group at its start: it walks to the waypoint and waits **there**. Put the waiting waypoint right on top of the group.
- Want OR? Use a Game Logic OR gate ([logic-gates](logic-gates.md)).
- Dragging between two waypoints of the **same** group creates no link at all (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplateFind.cpp#L298-L336`).
- A destroyed or emptied group no longer holds anyone.
- While a player-led group is held, its HUD waypoint label reads "waiting" ([show-waypoint](show-waypoint.md)).

## Tiny example

```text
Alpha    WP1 MOVE (on top of Alpha)  synced to trigger GO     WP2 MOVE (the village)
GO       Radio Alpha, Once
```

## Try it

1. Build the example and Preview: Alpha stays put.
2. Call Radio Alpha: Alpha heads for the village.
3. Move WP1 to the village gate and see Alpha walk there and wait.

## Related

[logic-gates](logic-gates.md) · [transport-waypoints](transport-waypoints.md) · [trigger-end-types](trigger-end-types.md) · [waypoint-lifecycle](waypoint-lifecycle.md) · [radio-triggers](radio-triggers.md)

## Profiles

- **cwr:** as cited.
- **ce:** `ArcadeTemplate.cpp` differs (the link cleanup starts at CE `#L1585`, +3); all other cited files are byte-identical.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified).
