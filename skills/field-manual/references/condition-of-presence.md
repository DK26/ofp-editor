---
id: condition-of-presence
label: Condition of presence
aliases: ["condition of presence", presenceCondition, "only appear if", "conditional unit"]
ui: "Unit dialog > Condition of presence (default: true)"
---

# Condition of presence

## In one sentence

A yes/no question asked once, while the world is still being built: answer "no" and the unit or object is never created, but the question cannot see anything that has not been built yet.

## What it really does

- The dialog checks that it is a Boolean expression; the default is `true` (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcade.cpp#L1115-L1125`).
- It is evaluated once per Non-playable unit or empty object, right after the [probability roll](probability-of-presence.md) (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1528-L1538`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1402-L1410`). Player and Playable units skip it.
- Build order: East groups, then West, Resistance, Civilian and Logic groups, then empty objects, then ungrouped triggers and markers. Only after all of that do the init lines run, and then `init.sqs` (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/WorldInit.cpp#L563-L632`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1396-L1446`).
- So a condition can use names of things built **earlier** in that order and engine state such as the difficulty, but not names built later, nor variables set in init lines or `init.sqs`.
- In intros, the campaign variables are loaded after the units are built (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/DisplayUIMenus.cpp#L1282-L1320`), so intro conditions probably cannot rely on them (unverified). When campaign variables become visible in a normal mission was not traced (unverified).

## When to use it

- Difficulty-dependent help: an extra medic only on Cadet.
- Variants: a road block that exists only in some versions of the mission.
- Tying objects to earlier-built units: an empty object (built late) can test a group unit (built early).

## Gotchas

- An East unit whose condition mentions a West unit asks too early: West is built after East. Whether that raises an error or just reads as false is not traced (unverified); a lint should flag it.
- Variables you set in an init line or `init.sqs` do not exist yet.
- It is a one-time check. For "appear later", create or move units by script or use triggers.
- It does nothing for Player and Playable units.

## Tiny example

```text
Friendly medic      Condition of presence: cadetMode        -> only on Cadet difficulty
East patrol         Condition of presence: alive westTank   -> asks too early (West is built later)
```

## Try it

1. Place a friendly soldier with `cadetMode` as his condition.
2. Preview on Cadet, then on Veteran difficulty.
3. Change the condition to `false` and confirm he never appears.

## Related

[probability-of-presence](probability-of-presence.md) · [init-line](init-line.md) · [mission-sections](mission-sections.md) · [player-and-playable](player-and-playable.md)

## Profiles

- **cwr:** as cited. `cadetMode` is a command in CWR and CE (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Game/Commands/GameStateExt.cpp#L861`).
- **ce:** the cited files are byte-identical except `GameStateExt.cpp` (`cadetMode` at CE `#L860`).
- **cwa199:** same lineage, not checked against the 1.99 build (unverified).
