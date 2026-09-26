---
id: waypoint-types
label: Waypoint types at a glance
aliases: [MOVE, DESTROY, "GET IN", SAD, JOIN, "JOIN AND LEAD", LEADER, "GET OUT", CYCLE, LOAD, UNLOAD, "TR UNLOAD", HOLD, SENTRY, GUARD, TALK, SCRIPTED, SUPPORT, AND, OR]
ui: "Waypoint dialog > Type"
---

# Waypoint types at a glance

## In one sentence

Each waypoint type is a different job card, and the column that matters most is "finishes when", because a job that never finishes needs someone to cancel it.

## What it really does

| Type | The group… | Finishes when | Source |
| --- | --- | --- | --- |
| MOVE | goes there; first boards its own vehicles if the leader is over 200 m away | it arrives | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L913-L992` |
| DESTROY | attacks the attached unit or object; if unattached, the nearest vehicle-type object within 100 m of the spot, **of any side** | target destroyed, 5 fruitless searches, or no target at all | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L1277-L1511` |
| GET IN | boards the attached vehicle, or the transport of the other group in a two-group sync | all with a seat are aboard, or the vehicle is destroyed | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L1515-L1787` |
| SEEK AND DESTROY | searches around the spot | 5 empty sweeps in a row (player-led: 15 s with no known enemy) | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L736-L962` |
| JOIN | merges **into** the target group (attached unit's group, or the other group of a two-group sync) | after the merge (skipped if there is no target) | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L1791-L1968`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L1-L32` |
| JOIN AND LEAD | makes the target group merge into **this** one | after the merge (skipped if there is no target) | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L1791-L1968`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L37-L68` |
| GET OUT | everybody gets out, crew included | the leader is on foot | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L73-L100` |
| CYCLE | jumps back to the nearest earlier waypoint | never; it redirects | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L400-L433` |
| LOAD | orders its own units into its own vehicles | at once, without waiting for boarding | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L105-L129` |
| UNLOAD | its own passengers get out; the crew stays | at once, without waiting | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L132-L181` |
| TR UNLOAD | passengers from **other** groups get out | no foreign passengers remain | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L184-L256` |
| HOLD | stays there | **never** (release it with a Switch trigger) | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L389-L508` |
| SENTRY | watches the area | an enemy is identified (**never** for a player-led group) | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L513-L731` |
| GUARD | becomes a quick-reaction force | **never** | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L967-L1668` |
| TALK | walks to about 3 m in front of the attached unit; says nothing | the leader is within 5 m (at once if there is no known target) | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L1072-L1273` |
| SCRIPTED | runs the Script field; moves only if the script moves it | the script ends | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L996-L1068` |
| SUPPORT | waits as repair, fuel, ammo or medical support | **never** | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L1673-L1769` |
| AND / OR | Game Logic gates only; see [logic-gates](logic-gates.md) | its gate opens | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L1774-L1810` |

After its job, every type still goes through Condition, syncs, timeout and On Activation ([waypoint-lifecycle](waypoint-lifecycle.md)).

## When to use it

Patrol: MOVE … CYCLE. Ambush: SENTRY, then SEEK AND DESTROY. Defence: HOLD or GUARD. Lifts: [transport-waypoints](transport-waypoints.md).

## Gotchas

- LOAD does not wait; use GET IN when someone must wait for boarding.
- An unattached DESTROY can pick a friendly or an empty vehicle. Attach it to the target.
- After HOLD, GUARD, SUPPORT (or SENTRY on the player's group), later waypoints are reached only when a Switch trigger fires.
- "Dismiss", "Loiter" and "Get in nearest" do not exist here ([not-in-this-engine](not-in-this-engine.md)).

## Tiny example

```text
Patrol:  WP1 MOVE (gate) -> WP2 MOVE (well) -> WP3 CYCLE (placed next to WP1)
```

## Try it

1. Build the patrol and Preview.
2. Change WP2 to HOLD: the loop stops at the well.
3. Add a Radio Alpha trigger of type Switch, sync it to WP2, and call it.

## Related

[waypoint-lifecycle](waypoint-lifecycle.md) · [cycle-waypoint](cycle-waypoint.md) · [seek-and-destroy](seek-and-destroy.md) · [guard-and-guarded-by](guard-and-guarded-by.md) · [transport-waypoints](transport-waypoints.md) · [trigger-end-types](trigger-end-types.md)

## Profiles

- **cwr / ce:** both cited files are byte-identical. **cwa199:** same lineage, not checked against the 1.99 build (unverified).
