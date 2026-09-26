---
id: logic-gates
label: "Logic waypoints: AND and OR"
aliases: [AND waypoint, OR waypoint, logic gate, "game logic waypoints", "either trigger"]
ui: "Waypoint dialog > Type (Game Logic groups only): AND, OR"
---

# Logic waypoints: AND and OR

## In one sentence

Give a Game Logic a chain of AND/OR waypoints and you have built a circuit: sync lines are the wires, each waypoint is a gate, and "the logic reaching its next waypoint" is the output.

## What it really does

- Only Logic groups get these two types, and they get only these two (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcadeWaypoint.cpp#L74-L105`).
- When a gate becomes current, the logic teleports onto it and at once marks its own end of every sync on that waypoint as done (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L1774-L1793`).
- The gate then waits. First its Condition must be true; there `this` is the logic itself and `thisList` its group. With no syncs the gate then opens. **AND** stays shut while any sync still has an unfinished partner (another group with units that has not arrived, or a trigger that has not fired). **OR** opens as soon as one sync has no unfinished partner (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L309-L369`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L786-L807`).
- After it opens come the random timeout, then On Activation and effects, then the next waypoint (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L1795-L1810`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L863-L895`).
- Each sync drag creates its own link between exactly the two items you connected (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplateFind.cpp#L296-L331`).

## When to use it

- "When the alarm sounds **or** the convoy is spotted, send the tanks": an OR gate synced to two triggers.
- "Only when all three objectives are done": an AND gate synced to three triggers.
- A timed sequence (cutscene beats, a reinforcement schedule): a chain of unsynced gates, each with a timeout and an On Activation line.

## Gotchas

- **The output is the next waypoint.** A group synced to the gate itself is released when the logic *arrives* there, that is, as soon as the previous gate finished, not when this gate opens. Sync the group you want to hold to the logic's *next* waypoint (read from code; in-game probe pending).
- On an OR gate, a group synced to the gate is an input too: its arrival alone can open the gate.
- Ordinary group waypoints with several syncs always act as AND. OR exists only on logic waypoints.
- A gate with nothing synced still waits for its Condition and its timeout.
- Dragging a waypoint's sync line onto empty map removes **all** of that waypoint's syncs (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapExt.cpp#L2382-L2387`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplateFind.cpp#L337-L344`).

## Tiny example

```text
Trigger T1  Radio Alpha, Once        Trigger T2  Radio Bravo, Once
Logic   WP1 OR   synced to T1 and T2        On Activation: hint "gate open"
        WP2 AND  synced to the tanks' WP1   (the output)
Tanks   WP1 MOVE right beside the tanks, synced to logic WP2;  WP2 MOVE to the town
```

## Try it

1. Build the example, Preview and call only Radio Bravo: the tanks leave.
2. Change WP1 from OR to AND and Preview again: now both calls are needed.
3. Move the tanks' sync from logic WP2 to logic WP1 and watch them leave at once.

## Related

[game-logic](game-logic.md) · [synchronisation](synchronisation.md) · [radio-triggers](radio-triggers.md) · [waypoint-lifecycle](waypoint-lifecycle.md)

## Profiles

- **cwr:** as cited.
- **ce:** cited files are byte-identical except `UIArcadeWaypoint.cpp`, whose cited lines match.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified).
