---
id: seek-and-destroy
label: SEEK AND DESTROY (SAD) waypoint
aliases: [SAD, "seek and destroy", "search and destroy", "clear area", "hunt"]
ui: "Waypoint dialog > Type: SEEK AND DESTROY"
---

# SEEK AND DESTROY (SAD) waypoint

## In one sentence

SAD tells a group to go to an area and poke around until it gets bored: five empty sweeps in a row and it moves on, but every enemy it spots, and every contact it walks over to check, resets the boredom counter.

## What it really does

- The group first moves to the waypoint like a MOVE (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L736-L739`).
- **AI group:** while it knows of a valid enemy target, its "empty sweep" counter resets to 0 and its normal combat AI does the fighting. Unidentified contacts are walked over to and checked when they are close enough to the waypoint; the allowed distance scales between 400 and 1600 m with a group threshold. After such a check the group walks back to the waypoint and the counter starts again at 0 (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L741-L911`).
- With nothing to chase, the group makes a random search move around the waypoint, at most 6 seconds' travel at its leader's top speed along each axis. Each completed empty move adds one to the counter; at 5 the waypoint finishes (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L913-L962`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L783-L791`).
- **Player-led group:** it finishes once 15 seconds pass with no known enemy; each enemy sighting restarts the 15 seconds (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L741-L778`).
- Then comes the usual Condition, syncs, timeout and On Activation ([waypoint-lifecycle](waypoint-lifecycle.md)).

## When to use it

- Sweeping a village or a wood line after a fight.
- The second half of an ambush: SENTRY (wait until enemies are identified), then SAD.
- A final assault on an objective area where you do not know exactly where the defenders are.

## Gotchas

- It is **not** "search until everyone is dead". Hidden enemies can be left behind once five empty sweeps have passed.
- If enemies keep turning up, it may never finish, so waypoints after it may be reached late or not at all.
- The sweep size depends on the leader's vehicle: a tank searches a much wider area than infantry.
- Use DESTROY attached to a target when you mean one specific target ([waypoint-types](waypoint-types.md)).

## Tiny example

```text
Squad  WP1 SENTRY (hill overlooking the road)
       WP2 SEEK AND DESTROY (the road bend)
       WP3 MOVE (back to camp)
```

## Try it

1. Place an East squad with the example waypoints and a West patrol driving past the bend.
2. Preview: the squad waits, then pounces when it identifies the patrol.
3. Remove the patrol: the squad stays on the hill forever (SENTRY needs an enemy).

## Related

[waypoint-types](waypoint-types.md) · [waypoint-lifecycle](waypoint-lifecycle.md) · [guard-and-guarded-by](guard-and-guarded-by.md) · [combat-mode](combat-mode.md)

## Profiles

- **cwr:** as cited.
- **ce:** `AIArcadeActions.inc` is byte-identical.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified).
