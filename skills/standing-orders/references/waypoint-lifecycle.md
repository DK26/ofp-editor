---
id: waypoint-lifecycle
label: How every waypoint runs (the waypoint life cycle)
aliases: ["waypoint order", "when does On Activation run", "waypoint settings", "waypoint condition", "waypoint timeout", "turn, move, wait"]
ui: "Waypoint dialog: Condition, On Activation, Timeout min/mid/max, Combat mode, Formation, Speed, Behaviour"
translator-note: "'A little conveyor belt' is a picture, not a term. Rule it teaches: every waypoint runs in the same fixed order. Its settings apply on the way there, then the Condition and syncs are checked on arrival, then a random timeout, then On Activation on the way out. Replace it with a local image of a fixed sequence of stations; translate the rule literally."
---

# How every waypoint runs (the waypoint life cycle)

## In one sentence

Every waypoint is a little conveyor belt: orders on the way **there**, a check-in on arrival (Condition and syncs), a random pause, then On Activation on the way **out**.

## What it really does

1. **Becomes current:** its formation, combat mode, speed and behaviour are sent **now**, so they govern the trip *to* it. Player-led groups skip this step (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L270-L307`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L459-L466`). At mission start the first waypoint's settings are applied to every group, the player's included (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L2110-L2140`).
2. **Its job:** move, board, search, and so on ([waypoint-types](waypoint-types.md)). An AI group has arrived when the group reports done, or when its leader (as commander of his vehicle) is within one vehicle precision of the spot. A player-led group has arrived when **any** member is within the larger of 10 m and 5 × vehicle precision (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L569-L630`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L265-L266`).
3. **Check-in:** the group marks its own syncs done, then waits until its Condition is true and every synced partner is ready (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L811-L861`). In the Condition, `this` is the leader (the soldier, not his vehicle) and `thisList` the group's soldiers (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L309-L337`).
4. **Timeout:** one random delay from min/mid/max (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L863-L883`); see [countdown-vs-timeout](countdown-vs-timeout.md) for the shape.
5. **Out:** On Activation runs, then the effects (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L647-L685`).
6. **Next:** after any script lock on the group's waypoints is released, the next waypoint becomes current; with none left, the group is done (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L887-L909`).

A waypoint attached to a unit or building heads for where the group's side last knew that target to be (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L523-L549`).

## When to use it

- Plan settings one waypoint early: "Safe" on the approach waypoint, "Combat" on the assault waypoint that follows it.
- Put objective code in On Activation of a waypoint that will really finish.

## Gotchas

- "Combat" set on the objective waypoint applies for the whole walk there, not just on arrival.
- Safe or Aware is a floor, not a lock: once the group is disclosed, its units act at Combat anyway ([combat-mode](combat-mode.md)).
- The Condition is only checked on arrival; the group still walks there first.
- HOLD, GUARD and SUPPORT never finish, so their On Activation never runs (SENTRY never finishes for a player-led group).
- The player's own group gets no automatic moves or settings, yet its MOVE-style waypoints still complete and run On Activation when anyone in the group gets close.
- `this` in a waypoint is an object; in a trigger condition it is a Boolean ([this-and-thislist](this-and-thislist.md)).

## Tiny example

```text
WP1  MOVE   Behaviour: Safe,   Speed: Limited    (the walk to the tree line)
WP2  MOVE   Behaviour: Combat, Speed: Full       (the rush from the tree line to the farm)
            On Activation: farmTaken = true
```

## Try it

1. Build the example with an AI squad and watch where their behaviour and speed change.
2. Move "Combat" to WP1 and compare.
3. Give WP2 the Condition `false` and see the squad stop there forever.

## Related

[waypoint-types](waypoint-types.md) · [synchronisation](synchronisation.md) · [combat-mode](combat-mode.md) · [show-waypoint](show-waypoint.md) · [countdown-vs-timeout](countdown-vs-timeout.md)

## Profiles

- **cwr:** as cited.
- **ce:** all cited files are byte-identical.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified).

## Verification notes

### Consolidation pass (2026-09-27)

- 2026-09-27 (I33-SEED-C; doc 33 finding 11 and §7): added a `translator-note` front-matter key for the "conveyor belt" idiom, naming the rule it teaches. No engine facts or citations changed.
