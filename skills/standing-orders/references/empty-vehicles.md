---
id: empty-vehicles
label: "Empty: vehicles and objects with nobody inside"
aliases: [empty, EMPTY, "empty vehicle", props, objects, "ammo crate", "sound source", mines, lock, locked, health, fuel, ammo]
ui: "Unit dialog > Side: Empty"
---

# Empty: vehicles and objects with nobody inside

## In one sentence

"Empty" does not mean an empty slot: it means a thing with no crew and no group, such as a car to steal, a crate, a sandbag wall, an ambient sound or a live mine.

## What it really does

- Empty units go to their own list and never join a group; the class list leaves out Game Logic and anything derived from a soldier (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplateFind.cpp#L419-L426`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcade.cpp#L269-L280`).
- They are built after every side's groups. Each rolls presence and its condition. A class in vehicle class "Sounds" becomes an ambient sound source; "Mines" becomes a live mine placed evenly in the placement circle; anything else becomes a normal object (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1396-L1431`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L855-L939`).
- Sound sources and mines get no Name variable and no init line. Normal objects get Name, init, lock, health, fuel, ammo, azimuth, placement radius, start markers and info age.
- **Health** sets damage to 1 − max(0.03, health), so Health 0 leaves the object alive at 97 % damage, not destroyed (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L853`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1020-L1086`).
- **Lock** affects the player and the player's group only. Locked: the player gets no get-in action, and members of his group do not board. Default: he gets the action only as group leader, in multiplayer, or when the vehicle is assigned to him. Unlocked: always. AI groups not led by the player ignore locks (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Entities/Vehicles/TransportCrew.cpp#L386-L396`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIUnitImpl.cpp#L223-L300`).
- **Side:** an intact vehicle with no living driver, commander or gunner reports side **Civilian**, whatever its class, so a parked West jeep counts for "Civilian present" and "Anybody present", not "West present" (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Entities/Vehicles/TransportCore.cpp#L227-L254`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L731-L751`; read from code, in-game probe pending). Other empty objects start with the side in their class config (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/VehicleAI.cpp#L1154`), and static ones never count for side triggers.

## When to use it

- Vehicles the player or AI can take, supply crates, props and fortifications.
- Ambience: sound sources for birds, dogs or a generator.
- Minefields that are really there at start.

## Gotchas

- Health 0 is not a wreck. For a wreck put `this setDammage 1` in the init line.
- A low Health on a crewed (non-Empty) vehicle damages the vehicle only; its crew start unhurt.
- Locked does not stop AI groups the player does not lead, friend or enemy, from using the vehicle.
- Parked empty vehicles inside a "Civilian" or "Anybody" Present trigger trip it, and keep a matching Not present trigger from firing (read from code; in-game probe pending).
- In cargo soldiers never board an Empty vehicle; use `moveInCargo` ([special-placement](special-placement.md)).

## Tiny example

```text
Empty jeep    Name: jeep1   Lock: Locked      init: this setFuel 0.2
Empty crate   (from the Empty class list)     Health 100 %
Empty tank    init: this setDammage 1         -> a burnt-out wreck at start
```

## Try it

1. Place an Empty jeep with Health 0 and Preview: it is still alive.
2. Replace the Health trick with `this setDammage 1` in its init and Preview again.
3. Set Lock to Locked and try to get in as the player.

## Related

[init-line](init-line.md) · [special-placement](special-placement.md) · [trigger-activation](trigger-activation.md) · [show-ids-and-object-ids](show-ids-and-object-ids.md)

## Profiles

- **cwr:** as cited.
- **ce:** all cited files are byte-identical except `VehicleAI.cpp` (the side line is at CE `#L1159`).
- **cwa199:** same lineage, not checked against the 1.99 build (unverified).
