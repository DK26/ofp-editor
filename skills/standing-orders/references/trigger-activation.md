---
id: trigger-activation
label: "Trigger activation: who, Present / Not present, and the area"
aliases: [activation, "activated by", present, "not present", anybody, "trigger area", "trigger size", "axis a", "axis b", "trigger doesn't fire", "trigger never fires"]
ui: "Trigger dialog > Activation, Presence, Axis a/b, Angle, Shape"
---

# Trigger activation: who, Present / Not present, and the area

## In one sentence

A trigger is a tripwire drawn on the map: Activation says whose boots count, Present or Not present says whether you want boots in the zone or an empty zone, and a fresh trigger is watching nobody yet.

## What it really does

- A new trigger is an ellipse with both axes 50 m, that is a circle 100 m across, with Activation **None**, Present, Once, not interruptable (the Countdown behaviour), no delay and the Condition `this` (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.cpp#L446-L473`).
- Axis a and b are **half**-widths in metres. The inside test is flat (2D): height is ignored (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L478-L492`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L792-L814`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L839-L852`).
- **None:** no area test; `this` is false, so the default Condition `this` never fires. Only a custom Condition can fire it (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L865-L868`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1259-L1265`).
- **East / West / Resistance / Civilian / Game Logic / Anybody:** each check walks the world's list of moving objects, skips destroyed ones, non-AI objects and static ones, keeps those of the chosen side (Anybody keeps all) and lists those inside the area. Present fires when the list is not empty, Not present when it is empty (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L880-L922`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L731-L751`).
- Side comes from the object's current side. A renegade is "enemy to all", so only Anybody counts him. An intact vehicle with no living driver, commander or gunner counts as **Civilian**, whatever its class ([sides-and-friendliness](sides-and-friendliness.md), `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Entities/Vehicles/TransportCore.cpp#L227-L254`).
- Crew created inside vehicles at start are kept in a separate list that this scan does not walk, so the list holds the vehicle, not the men in it (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1510-L1514`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/World.hpp#L460-L487`). The same probably holds for anyone who boards later (unverified).
- Other activations: [radio-triggers](radio-triggers.md), [detected-by](detected-by.md), and triggers linked to a unit or building ([bound-triggers](bound-triggers.md)).

## When to use it

- "Player reaches the village": West, Present, over the village.
- "Village cleared": East, Not present, over the village.
- A global event with no area: None plus a custom Condition such as `!alive officer1`.

## Gotchas

- **The number-one "broken trigger":** Activation left at None with Condition `this`. It can never fire.
- Not present fires immediately at mission start if the area is already empty of that side.
- A helicopter flying over the area counts: the test ignores height.
- `player in thisList` is false while the player sits in a vehicle; test `vehicle player in thisList`.
- Parked empty vehicles count for Civilian and Anybody, not for the side of their class; Game Logics count for Game Logic and Anybody (read from code; in-game probe pending).
- Dead soldiers and wrecks are skipped entirely, so they never count for Present or keep a Not present from firing.

## Tiny example

```text
Trigger  Axis a/b: 100/100   Activation: West   Present   Once
         On Activation: hint "Contact at the village!"
```

## Try it

1. Place a player on foot outside the trigger above and Preview; walk in.
2. Set Activation back to None and Preview again: it never fires.
3. Keep None and change the Condition to `true`: now it fires at once, wherever the player is.

## Related

[this-and-thislist](this-and-thislist.md) · [once-vs-repeatedly](once-vs-repeatedly.md) · [countdown-vs-timeout](countdown-vs-timeout.md) · [bound-triggers](bound-triggers.md) · [detected-by](detected-by.md) · [trigger-end-types](trigger-end-types.md)

## Profiles

- **cwr:** as cited.
- **ce:** `ArcadeTemplate.cpp` differs (defaults at CE `#L449-L476`, +3); the other cited files are byte-identical.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified).

## Verification notes

### Consolidation pass (2026-09-27)

- 2026-09-27 (I33-SEED-C; doc 33 pedagogy finding 2): "In one sentence" said a fresh trigger "is not wired to anything yet", which invites syncing it; it now says "is watching nobody yet", which matches the real cause (Activation None). No engine facts or citations changed.
