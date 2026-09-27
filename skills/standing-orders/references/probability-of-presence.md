---
id: probability-of-presence
label: Probability of presence
aliases: [presence, "probability of presence", "chance to appear", "random units", "0% unit"]
ui: "Unit dialog > Probability of presence (slider)"
---

# Probability of presence

## In one sentence

A dice roll at mission start: at 50 % the unit or object exists in about half of all playthroughs, and when it loses the roll it is simply never built.

## What it really does

- It is rolled once, when the unit is created: if a random number is greater than the slider value, the unit is skipped (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1525-L1533`). Empty objects roll the same way (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1396-L1406`).
- It only applies to Non-playable units and empty objects. Player and Playable units always appear.
- A crewed vehicle is one unit in the editor, so the vehicle and its whole crew appear or vanish together.
- The roll comes before the [condition of presence](condition-of-presence.md).
- A group left with no units is removed (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L2052-L2056`). Its side still exists, because in single-player a side is created when the mission file contains any group of that side, checked before any roll (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterStats.cpp#L1328-L1349`).
- A unit that is not created never gets its Name variable (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1014-L1018`), and its init line never runs.

## When to use it

- Optional threats: a patrol that is there only sometimes.
- Surprises: a random extra tank or a lucky ammo crate.
- The "side switch" trick: one 0 % unit of a side makes that side exist in single-player, so its Detected-by and Guarded-by triggers work even when all its forces are spawned by script (see [detected-by](detected-by.md)).

## Gotchas

- Scripts, conditions and triggers that name a possibly absent unit will meet an undefined variable. What an expression does then is not traced here (unverified); test for it or avoid naming such units.
- Setting presence on a playable unit does nothing.
- In the editor there is no preview of the roll; each Preview is a new roll.

## Tiny example

```text
Ambush squad leader    Probability of presence: 50 %
Ambush riflemen        Probability of presence: 100 %
Result                 the riflemen always appear; in half the plays the group
                       picks a new leader from among them
```

Every unit rolls on its own, so a whole squad at 50 % turns up as a random handful, not all-or-nothing.

## Try it

1. Place five East soldiers at 30 % presence each.
2. Preview several times and count how many turn up.
3. Make one of them Playable: he is there every time.

## Related

[condition-of-presence](condition-of-presence.md) · [player-and-playable](player-and-playable.md) · [placement-radius](placement-radius.md) · [detected-by](detected-by.md)

## Profiles

- **cwr:** as cited.
- **ce:** `AICenterImpl.cpp` and `AICenterStats.cpp` are byte-identical.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified).
