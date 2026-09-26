---
id: bound-triggers
label: "Triggers linked to a unit, group or building"
aliases: ["whole group", "group leader", "any group member", vehicle, static, "linked trigger", "grouped trigger", "trigger on unit", "building destroyed", "group not present"]
ui: "Groups mode (F2): drag a trigger onto a unit or a building; Trigger dialog > Activation"
---

# Triggers linked to a unit, group or building

## In one sentence

Drag a trigger onto something and it stops watching "everyone" and starts watching just that thing, but read the labels like a lawyer: "Whole group, Not present" means "not **all** of them are inside".

## What it really does

- Linking a trigger to a unit in a group offers Vehicle, Whole group, Group leader and Any group member; a link to an empty vehicle offers only Vehicle, and a building link gives the Static activation (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcade.cpp#L1484-L1552`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplateFind.cpp#L650-L690`).
- Everything below is still tested against the trigger's **area**, and destroyed things never count as inside (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L816-L824`).

| Activation | Present fires when | Not present fires when | Source |
| --- | --- | --- | --- |
| Whole group | every member's vehicle is inside | **at least one** is outside (or destroyed while still listed), or the group is empty | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1047-L1095` |
| Group leader | the current leader's vehicle is inside | it is not | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1142-L1178` |
| Any group member | any member is inside | **no** member is inside | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1179-L1217` |
| Vehicle / Static | the object is inside and not destroyed | it is outside **or destroyed** | `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L957-L1046` |

- With a "Detected by" presence, Whole group fires only when every member is known to be inside (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1096-L1140`).
- At start, the link is resolved to the group commanding the linked unit, and the trigger keeps watching that group, even if the unit later changes group (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L626-L673`).

## When to use it

- "The convoy escaped": Whole group, Present, over the exit road.
- "The whole squad is dead or gone": **Any group member**, Not present, over the area.
- "The bridge is destroyed": Static (linked to the bridge), Not present, with the bridge inside the area.

## Gotchas

- Whole group + Not present fires as soon as **one** member steps outside; it does not mean "the group is gone".
- A linked object must sit inside the trigger area, or Not present is true from the first second.
- Linking to a plain map object that is not an AI-capable entity, such as a tree, probably never counts as present (unverified).
- If the linked unit is missing at start (probability or condition of presence), the trigger watches nothing: Present can never fire, and Not present is normally true from the first second. This holds for Vehicle and for all three group kinds, even when the rest of the group is there (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L639-L656`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1001-L1217`; read from code, in-game probe pending). Link to a unit that is always present, such as the leader at 100 %.

## Tiny example

```text
Trigger  linked to officer's squad   Activation: Any group member   Not present
         Axis 300/300 over the camp  Type: End #1
```

## Try it

1. Build the example with an enemy squad and Preview; kill them all to win.
2. Change "Any group member" to "Whole group" and see the mission end after the first kill or the first man to wander off.
3. Link a new trigger to a building (Static, Not present) and blow the building up.

## Related

[trigger-activation](trigger-activation.md) · [show-ids-and-object-ids](show-ids-and-object-ids.md) · [trigger-end-types](trigger-end-types.md) · [this-and-thislist](this-and-thislist.md)

## Profiles

- **cwr / ce:** all cited files are byte-identical. **cwa199:** same lineage, not checked against the 1.99 build (unverified).
