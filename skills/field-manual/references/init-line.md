---
id: init-line
label: Initialization (init line)
aliases: [init, "init line", "init field", initialization, "this in init"]
ui: "Unit dialog > Initialization"
---

# Initialization (init line)

## In one sentence

The init line is a sticky note on an object that the engine reads aloud once, after the whole world has been built, with `this` pointing at the object the note is stuck to.

## What it really does

- Init lines are collected while objects are built and **all** run afterwards, in build order, once every object of the section exists (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/WorldInit.cpp#L622-L627`).
- `this` is the object you placed: for a soldier the man, for a crewed vehicle **the vehicle** (not its crew), for an "In cargo" soldier the man, for an empty object the object (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1929-L1934`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L2044-L2049`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1424-L1429`).
- In a single-player mission, `init.sqs` runs right after the init lines (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/WorldInit.cpp#L629-L632`). Intros run `initintro.sqs` instead (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/DisplayUIMenus.cpp#L1322-L1328`). In multiplayer, `init.sqs` is started from the network code; its timing was not traced (unverified).
- In multiplayer the server also sends every init line to the clients (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/WorldInit.cpp#L665-L671`), and a client runs a received line with `this` set (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Network/NetworkClientOnMessage.cpp#L1372-L1379`). So init lines probably run on every machine (inferred; unverified).
- The dialog checks the text with the real script evaluator in check-only mode (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcade.cpp#L1101-L1113`). It must be statements that return nothing: `alive player` on its own is an error.
- Sound sources and mines never run an init line, and an absent unit's init line never runs.

## When to use it

- One-off setup of this object: damage, lock, loadout, seating it in a vehicle.
- Setting global variables that triggers and scripts read later.

## Gotchas

- On a tank, `this` is the tank. Reach the crew through the vehicle, or through the crew names the engine creates for a named vehicle (name + `d`, `c`, `g`).
- A [condition of presence](condition-of-presence.md) runs **before** any init line, so it cannot see variables set here.
- In multiplayer, a line that adds weapons or items may run on every machine (unverified); guard it with a server check where available.
- Keep lines short; long logic belongs in a script file.

## Tiny example

```text
Empty jeep "jeep1"   init:  this lock true
Soldier              init:  this moveInCargo jeep1
Logic                init:  alarm = false
```

## Try it

1. Place an Empty jeep named `jeep1` and a soldier with the init `this moveInCargo jeep1`.
2. Preview: he starts in the jeep.
3. Give a second Empty jeep the init `this setDammage 1`: it starts as a wreck, which its Health slider cannot do ([empty-vehicles](empty-vehicles.md)).

## Related

[this-and-thislist](this-and-thislist.md) · [condition-of-presence](condition-of-presence.md) · [empty-vehicles](empty-vehicles.md) · [special-placement](special-placement.md)

## Profiles

- **cwr:** as cited.
- **ce:** all cited files are byte-identical.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified). The crew-name suffixes are verified in CWR and CE only (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1631-L1703`).
