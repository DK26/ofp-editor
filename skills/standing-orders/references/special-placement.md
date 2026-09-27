---
id: special-placement
label: "Special: In formation, None, In cargo, Flying"
aliases: [special, "in formation", FORM, "in cargo", CARGO, flying, FLY, "none", "start in vehicle", "start in the air"]
ui: "Unit dialog > Special"
---

# Special: In formation, None, In cargo, Flying

## In one sentence

"Special" decides where a unit really starts: snapped into formation behind its leader (the default), exactly where you put it, sitting in the back of its own group's vehicle, or already in the air.

## What it really does

- **In formation** (default): after the group is built, every non-leader with this setting is moved to its formation slot around the leader and turned to face the leader's direction; aircraft keep their height above ground (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1924-L1927`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L2142-L2186`).
- **None:** the unit stays at its editor position, apart from its [placement radius](placement-radius.md).
- **In cargo:** soldiers are created in a second pass and seated as passengers in the first vehicle that a member of their **own group** is inside and that has a free cargo seat. Without such a vehicle they are not loaded (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1569-L1595`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1936-L1968`).
- An "In cargo" soldier is never registered as a sensor, even when no seat was found (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1572-L1600`). Whether an unseated one then stands around unable to see is unverified.
- **Flying:** only aircraft are made airborne; for anything else it acts like None (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1115-L1133`).

## When to use it

- In formation: normal squads, when you only care where the leader stands.
- None: sentries, snipers, men in a building, a hand-arranged ambush line.
- In cargo: troops that begin the mission riding in their own group's truck or helicopter.
- Flying: aircraft that should start airborne.

## Gotchas

- "I arranged my squad carefully and they teleported": that is In formation. Switch the members to None.
- The azimuth, placement radius and marker links of In-formation members are overridden; only the leader's count.
- In cargo ignores Empty vehicles and other groups' vehicles. For those, use an init line such as `this moveInCargo truck1`.
- Flying on a tank or a soldier does nothing special; it behaves like None.

## Tiny example

```text
Truck with driver (group Alpha leader)
Six riflemen in group Alpha      Special: In cargo     -> start seated in the truck
Sniper in group Bravo            Special: None         -> exactly where placed
```

## Try it

1. Place a crewed truck and, within 100 m of it, a soldier set to In cargo (he joins the truck's group). Preview: he starts inside.
2. Replace the truck with an Empty truck named `truck1` and Preview again: he is not loaded.
3. Give him the init `this moveInCargo truck1` and try once more.

## Related

[groups-and-leaders](groups-and-leaders.md) · [placement-radius](placement-radius.md) · [init-line](init-line.md) · [transport-waypoints](transport-waypoints.md) · [empty-vehicles](empty-vehicles.md)

## Profiles

- **cwr:** as cited.
- **ce:** `AICenterImpl.cpp` is byte-identical.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified).
