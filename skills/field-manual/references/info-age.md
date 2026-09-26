---
id: info-age
label: Info age
aliases: ["info age", age, "intel age", "known position", "Actual", "Unknown"]
ui: "Unit dialog > Info age; Trigger dialog > Info age"
---

# Info age

## In one sentence

Info age is how stale the player side's recon report on this unit is when the mission starts: "Actual" means "we know where it is right now", and "Unknown" is the same as a two-hour-old rumour, so old that the side forgets it at once.

## What it really does

- It only matters for objects whose side is not the player's side. That includes allies and every empty object. For each such object, the player side's knowledge is seeded with a report of the chosen age: 0, 5, 10, 15, 30, 60 or 120 minutes, or "Unknown" (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1163-L1199`).
- "Unknown" uses the engine's longest age, 7200 s, the same as 120 minutes (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L87`).
- The report is back-dated by that age, and it also records the unit's facing when the age is 5 minutes or less (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImplPreview.cpp#L686-L722`).
- Position accuracy of a report fades linearly to zero over 7200 s (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterStats.cpp#L702-L712`): at 60 minutes it is about half.
- Each time a side's AI updates, it deletes reports older than 7200 s. A 120-minute or Unknown report is already that old, so it is gone as soon as the mission clock moves; a 60-minute report lasts another hour (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImplPreview.cpp#L538-L556`; read from code, in-game probe pending).
- New units default to Unknown (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.cpp#L265`).
- On **triggers**, the start-up code computes the age and then throws it away (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1344-L1375`). No other use was found, so treat it as doing nothing (unverified).

## When to use it

- "Recon spotted T-72s at the crossroads this morning": set those tanks to 60 or 120 minutes.
- "The partisans just radioed their position": set the allied squad to Actual.

## Gotchas

- Unknown and 120 minutes behave the same: the seeded report is dropped at once, so the side starts with no knowledge of the unit.
- What the AI and the map do with the seeded knowledge that survives was not traced (unverified).
- An enemy set to Actual inside a "Detected by (the player's side)" trigger fires that trigger at mission start: such triggers count reports less than 100 s old with good accuracy, and Actual is 0 s old. Any other age is too old to count (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L923-L956`; read from code, in-game probe pending).
- In the original editor's map, Unknown also hides such units from viewers with limited rights (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapExt.cpp#L705-L708`).

## Tiny example

```text
Player side: WEST
East BMP at the bridge     Info age: 30 min    -> WEST starts with a half-hour-old report
Allied GUER squad          Info age: Actual    -> WEST knows exactly where they are
```

## Try it

1. Place an East tank with Info age Actual inside a trigger "East, Detected by West".
2. Preview and note whether it fires at start (the code says it should; the probe confirms it).
3. Set the tank to 5 minutes and compare: now it fires only once West really spots it.

## Related

[detected-by](detected-by.md) · [sides-and-friendliness](sides-and-friendliness.md) · [empty-vehicles](empty-vehicles.md)

## Profiles

- **cwr:** as cited.
- **ce:** `ArcadeTemplate.cpp` differs (+3 lines, default at CE `#L268`); the other cited files, including `Detector.cpp`, are byte-identical.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified).
