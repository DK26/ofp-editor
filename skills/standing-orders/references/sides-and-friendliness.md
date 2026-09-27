---
id: sides-and-friendliness
label: Sides and who is friendly to whom
aliases: [side, West, East, Resistance, GUER, Civilian, CIV, "Resistance is friendly to", friendship, renegade]
ui: "Unit dialog > Side; Intel dialog > Resistance friendly to"
---

# Sides and who is friendly to whom

## In one sentence

West and East always fight; the only diplomacy you control is whom Resistance likes, and the civilians quietly copy Resistance.

## What it really does

- Intel stores two numbers: `resistanceWest` (default 1, friendly) and `resistanceEast` (default 0, hostile). On load, West and East are forced hostile to each other, every side is friendly to itself, and Resistance's view of a side mirrors that side's view of Resistance (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.cpp#L1474-L1526`).
- The Intel toolbox writes those numbers as pairs: Resistance friendly to nobody, West, East, or both (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcadeWaypoint.cpp#L779-L798`).
- At start, West, East and Resistance all treat Civilians as friends. The Civilian side is friendly to itself and to Resistance, and treats West and East the way Resistance does (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1745-L1768`).
- The Logic side rates everyone friendly (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1754-L1761`), and no side counts Logic as friend or enemy. "Friend" means a rating of at least 0.6, "enemy" below 0.6 (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterStats.cpp#L1371-L1410`).
- Dead objects report side Civilian. A unit whose commander's experience falls below the renegade limit reports "enemy", which every side treats as hostile; the engine's comment calls this shooting at friendlies (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/VehicleAIDiag.cpp#L1145-L1163`).
- An intact vehicle with no living driver, commander or gunner reports side Civilian, whatever its class (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Entities/Vehicles/TransportCore.cpp#L227-L254`).
- Each mission section (Mission, Intro, Outros) has its own Intel.

## When to use it

- Partisans helping NATO: keep the default (Resistance friendly to West).
- A pro-Soviet militia: Resistance friendly to East.
- A three-way war: Resistance friendly to nobody.

## Gotchas

- You cannot make West and East allies, and no Intel setting makes anyone hostile to Civilians.
- Armed Civilian-side units follow Resistance's attitude toward West and East, but West, East and Resistance always rate Civilians as friends, so they may not fire back at hostile armed civilians (read from code; in-game probe pending).
- A team-killer can drop out of his own side: "West present" triggers stop counting him, and everyone may shoot him.
- A dead soldier counts as Civilian where a side's knowledge is checked, as in "Civilian, Detected by …" triggers. Present and Not present scans skip dead and destroyed objects entirely ([trigger-activation](trigger-activation.md)).
- Side-based features need the side to exist in the mission; see [detected-by](detected-by.md).

## Tiny example

```text
Intel    Resistance friendly to: East
Result   GUER and EAST squads side by side ignore each other;
         a WEST patrol is attacked by both, and armed CIV units fire at it too.
```

## Try it

1. Place a WEST squad and a GUER squad 300 m apart, facing each other.
2. Preview with the default Intel: they ignore each other.
3. Set Resistance friendly to East only and Preview again.

## Related

[trigger-activation](trigger-activation.md) · [detected-by](detected-by.md) · [game-logic](game-logic.md) · [empty-vehicles](empty-vehicles.md)

## Profiles

- **cwr:** as cited. Mission files older than format version 10 store one `resistance` value instead of two (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.cpp#L1506-L1515`).
- **ce:** `ArcadeTemplate.cpp` differs; the cited block is at CE `#L1477-L1529` (+3). `UIArcadeWaypoint.cpp` differs, but its cited lines match. The other cited files are identical, including `TransportCore.cpp`.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified).
