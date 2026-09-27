---
id: combat-mode
label: "Combat mode colours, Behaviour and Speed"
aliases: ["combat mode", BLUE, GREEN, WHITE, YELLOW, RED, semaphore, "hold fire", "open fire", "fire at will", "engage at will", behaviour, behavior, CARELESS, SAFE, AWARE, COMBAT, STEALTH, speed, LIMITED, NORMAL, FULL]
ui: "Waypoint dialog > Combat mode, Behaviour, Speed, Formation"
---

# Combat mode colours, Behaviour and Speed

## In one sentence

The colours are two switches, "may we shoot?" and "may we break formation to chase?", and Blue is the one hold-fire colour that stays on even after the enemy has found you.

## What it really does

| Colour | Shooting | Formation | Once the group is disclosed |
| --- | --- | --- | --- |
| BLUE | hold fire | kept | stays BLUE |
| GREEN | hold fire | kept | becomes YELLOW |
| WHITE | hold fire | free to engage | becomes RED |
| YELLOW (default) | at will | kept | stays |
| RED | at will | free to engage | stays |

- "Hold fire" means firing only at a target the unit has been explicitly ordered to fire at; BLUE and GREEN are identical here. "Kept formation" means engaging only an assigned target (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIUnitImpl.cpp#L2108-L2143`). An AI leader never hands out targets on its own to hold-fire members (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIGroupImpl.cpp#L1053-L1056`).
- A DESTROY waypoint orders every member to fire at its target, so even a BLUE group shoots that target (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L1473-L1481`; read from code, in-game probe pending).
- When an AI group is disclosed, for example under fire, every mode except BLUE switches to open fire: GREEN becomes YELLOW and WHITE becomes RED. The player's own group is exempt (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIGroup.cpp#L759-L826`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIRadioImpl.cpp#L998-L1034`).
- New groups start YELLOW (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIGroup.cpp#L49-L55`). Each unit's own behaviour starts at AWARE (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIUnit.cpp#L406-L407`).
- **Behaviour** is a floor. A unit acts at whichever comes later in the list Careless, Safe, Aware, Combat, Stealth: its own behaviour or its group's alert level. The alert level starts at SAFE and jumps to COMBAT when the group is disclosed. CARELESS ignores the alert level (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIUnit.cpp#L1290-L1315`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIGroup.cpp#L785-L787`).
- A waypoint sends its colour to the group and to every member, and its behaviour separately, when the waypoint becomes current; "No change" keeps the old value. Player-led groups ignore these, except the first waypoint's values at mission start (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L270-L307`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L2110-L2140`).
- **Speed:** LIMITED caps the leader at 22 % of his top speed unless he is acting at COMBAT (which a disclosed group does); FULL lets him run up to 1.5 × top speed, so he does not wait for the formation (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AISubgroup.cpp#L2286-L2304`).
- What each Behaviour (Careless, Safe, Aware, Combat, Stealth) changes inside the AI was not traced (unverified).

## When to use it

- Stealthy approach: GREEN (or WHITE) so nobody fires first, knowing it opens up once the group is disclosed.
- Hunting: RED, so members leave formation to chase targets.
- Scripted "do not shoot" moments, such as a surrender: BLUE.

## Gotchas

- GREEN is not "never fire": it becomes YELLOW once the group is disclosed. Only BLUE keeps holding fire, and even BLUE shoots at the target of a DESTROY waypoint.
- A Safe waypoint does not keep a group relaxed under fire: disclosure lifts it to COMBAT behaviour and, with LIMITED speed, lifts the speed cap too.
- Settings take effect when the waypoint becomes current, so set them on the waypoint you are walking **to** ([waypoint-lifecycle](waypoint-lifecycle.md)).
- Members can end up with different colours: hold-fire and open-fire orders can target only some members (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIGroupCmd.cpp#L613-L636`).

## Tiny example

```text
WP1 MOVE  Combat mode: GREEN  Behaviour: STEALTH  Speed: LIMITED   (sneak up)
WP2 SAD   Combat mode: RED    Behaviour: COMBAT   Speed: FULL      (assault)
```

## Try it

1. Give an AI squad the example waypoints near an enemy post and Preview.
2. Change WP1 to BLUE and watch them walk in without firing, even when shot at.
3. Change it to WHITE and compare how they break formation once disclosed.

## Related

[waypoint-lifecycle](waypoint-lifecycle.md) · [waypoint-types](waypoint-types.md) · [seek-and-destroy](seek-and-destroy.md)

## Profiles

- **cwr / ce:** all cited files are byte-identical except `AIGroupImpl.cpp` (the hold-fire check is at CE `#L1067-L1070`). **cwa199:** same lineage, not checked against the 1.99 build (unverified).
