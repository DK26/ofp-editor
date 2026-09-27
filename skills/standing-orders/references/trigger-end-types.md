---
id: trigger-end-types
label: "Trigger types: None, Switch, End #1–#6, Lose, Guarded by"
aliases: ["trigger type", switch, "skip waypoint", END1, END2, "end #1", ending, win, lose, LOOSE, "mission end", "end mission", "guarded by"]
ui: "Trigger dialog > Type"
---

# Trigger types: None, Switch, End #1–#6, Lose, Guarded by

## In one sentence

The Type is what the trigger does besides running its own code: nothing (None), shove groups past a waypoint (Switch), end the mission (End #n, Lose), or pin a spot for guards (Guarded by).

## What it really does

- **Switch:** when it fires, each group that has a waypoint synced to it jumps to the waypoint **after** its first synced waypoint and starts it fresh. This works out of HOLD, GUARD, SUPPORT or a CYCLE loop, jumps ahead if the group has not reached that waypoint yet, and jumps **back** if it has already passed it (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1339-L1383`).
- A Switch never counts as "ready" for syncs, so a normal waypoint synced to it simply holds its group until the switch fires (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1384-L1390`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L755-L760`).
- **End #n:** the mission ends with ending n only when **every** End #n trigger is active at the same moment. If several endings qualify at once, the lowest number wins (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/WorldImpl.cpp#L556-L656`).
- **Lose:** any active Lose trigger ends the mission as lost, ahead of every End trigger. In single-player, the player's death ends it as "killed" before either is checked (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/WorldImpl.cpp#L541-L585`). In `mission.sqm` the type is spelled `LOOSE` (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.cpp#L200`).
- **Guarded by East/West/Resistance:** no trigger is created at all; only a guard point is left for that side ([guard-and-guarded-by](guard-and-guarded-by.md)).
- These checks also run in intros and multiplayer (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/WorldImpl.cpp#L553-L556`).

## When to use it

- Switch: release a HOLD ("attack now"), break a patrol loop, or skip ahead in a route.
- End #1 plus a second End #1: "win when both objectives are done", no scripting needed.
- Different End numbers: different outcomes, which a campaign can route to different next missions.
- Lose: "the convoy was destroyed" while the player still lives.

## Gotchas

- Several triggers of the same End type act as AND, not OR. For "either objective wins", give them different numbers or combine them with a logic OR gate ([logic-gates](logic-gates.md)).
- An active Lose beats any End.
- A Switch synced to a waypoint the group already passed sends it **backwards**.
- Code and conditions on a Guarded by trigger are ignored.
- No script command picks an ending; to end from a script, set a variable that an End trigger's Condition reads (see the mission-primer skill).

## Tiny example

```text
Trigger 1  East Not present over the village   Type: End #1
Trigger 2  Activation None  Condition: !alive radarTruck   Type: End #1
Result     the mission is won only when the village is clear AND the radar truck is dead
```

## Try it

1. Build both End #1 triggers and Preview; destroy the truck first, then clear the village.
2. Change Trigger 2 to End #2: now whichever happens first ends the mission.
3. Set Trigger 2 back to End #1. Add a Radio Alpha trigger of type Lose and call it after only one of the two End #1 conditions is met: the mission is lost.

## Related

[guard-and-guarded-by](guard-and-guarded-by.md) · [synchronisation](synchronisation.md) · [once-vs-repeatedly](once-vs-repeatedly.md) · [mission-sections](mission-sections.md) · [cycle-waypoint](cycle-waypoint.md)

## Profiles

- **cwr / ce:** all cited files are byte-identical except `ArcadeTemplate.cpp` (`LOOSE` at CE `#L203`). **cwa199:** same lineage, not checked against the 1.99 build (unverified).

## Verification notes

### Consolidation pass (2026-09-27)

- 2026-09-27 (I33-SEED-A; doc 33 pedagogy finding 6): Try it step 3 now first sets Trigger 2 back to End #1, which step 2 had changed to End #2; without that, meeting either condition would already win the mission before Lose is called. No engine facts or citations changed.
