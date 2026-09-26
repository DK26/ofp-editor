---
id: this-and-thislist
label: "What `this` and `thisList` mean in each box"
aliases: [this, thisList, "this in trigger", "this in waypoint", "this in init", "player in thisList", "vehicle player in thisList"]
ui: "Every Condition, On Activation, On Deactivation and Initialization field"
---

# What `this` and `thisList` mean in each box

## In one sentence

`this` is a pronoun whose meaning depends on which box you type it in: an object in init lines and waypoints, but a yes/no answer in a trigger's Condition.

## What it really does

| Where you type | `this` is | `thisList` is | Source |
| --- | --- | --- | --- |
| Unit or object init | the object (for a crewed vehicle, the vehicle) | not set | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/WorldInit.cpp#L622-L627` |
| Trigger Condition | true/false: did the area test pass? | the objects that passed it | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1259-L1265` |
| Trigger On Activation | **not set** (left over from elsewhere) | the objects that passed | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1331-L1337` |
| Trigger On Deactivation | not set | not set | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1512-L1517` |
| Radio trigger Condition | true | not refreshed | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1299-L1312` |
| Waypoint Condition and On Activation | the group leader (the soldier, not his vehicle) | the group's soldiers | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L309-L337`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L662-L684` |

- A trigger Condition that is exactly `this` (any letter case) is a shortcut and is not evaluated at all (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1259`).
- `this` and `thisList` are ordinary global variables that each box overwrites, so an unset one holds whatever the last trigger or waypoint left behind.
- A side trigger lists vehicles, not the men inside them ([trigger-activation](trigger-activation.md)).
- The effects Condition runs after On Activation. If it returns an object or an array, the effects play only when the player (or his vehicle) matches, so `thisList` there means "only if the player caused it" (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1392-L1439`).

## When to use it

- Trigger Condition: `this && alive officer1` ("area test passed and the officer lives").
- Waypoint Condition: `this distance tank1 < 50` ("the leader is near the tank").
- Init: `this setDammage 0.5`.

## Gotchas

- Do not use `this` in a trigger's On Activation; use `thisList` or a named object.
- `player in thisList` is false while the player is in a vehicle; write `vehicle player in thisList`.
- `this` in a waypoint is an object: `this` alone is not a valid Boolean Condition there.
- `==` cannot compare Booleans: write `this`, not `this == true`. It is registered only for numbers, strings, objects, groups and sides (`BohemiaInteractive/CWR@ffc61838b7:engine/Evaluator/express.cpp#L1113-L1116`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Game/Commands/GameStateExt.cpp#L1279-L1284`).

## Tiny example

```text
Trigger  West Present   Condition:     this && (vehicle player in thisList)
                        On Activation: hint format ["%1 units inside", count thisList]
```

## Try it

1. Build the trigger and Preview; enter on foot, then in a jeep.
2. Change the Condition to `player in thisList` and repeat in the jeep: it does not fire.
3. Put `hint format ["%1", this]` in a waypoint's On Activation and read who `this` is.

## Related

[trigger-activation](trigger-activation.md) · [init-line](init-line.md) · [waypoint-lifecycle](waypoint-lifecycle.md) · [radio-triggers](radio-triggers.md)

## Profiles

- **cwr / ce:** all cited files are byte-identical except `GameStateExt.cpp` (the `==` lines are at CE `#L1277-L1282`). CWR and CE also have `boolEq` and `boolNe` for comparing Booleans (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Game/Commands/GameStateExt.cpp#L1285-L1288`); whether 1.99 has them is unverified. **cwa199:** same lineage, not checked against the 1.99 build (unverified).
