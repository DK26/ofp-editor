---
id: guard-and-guarded-by
label: GUARD waypoints and "Guarded by" triggers
aliases: [GUARD, "guarded by", "guarded by east", "guarded by west", "guarded by resistance", "quick reaction force", QRF, "seized by"]
ui: "Waypoint dialog > Type: GUARD; Trigger dialog > Type: Guarded by East/West/Resistance"
translator-note: "'Fire brigade on permanent call' and 'a pin on the side's duty map' are pictures, not terms. Rule they teach: unsynced GUARD groups form the side's reserve that is sent to known threats; a Guarded by trigger only marks a spot where idle reserves wait, and runs no code. Replace them with local images that teach the same rule; translate the rule literally."
---

# GUARD waypoints and "Guarded by" triggers

## In one sentence

GUARD turns a group into a fire brigade on permanent call, and a "Guarded by" trigger is just a pin on the side's duty map saying "if nobody is busy, sit here".

## What it really does

- **A "Guarded by" trigger is not a trigger at start.** No trigger object is created; its condition, activation, size, On Activation, effects, name and syncs are all ignored. It only adds a guard point for that side, at the trigger's position, or at the position of the group leader, building or vehicle it is linked to, taken once at start. It does nothing if that side has no AI centre, which in single-player means no group of that side in the mission file (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1246-L1303`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterStats.cpp#L1328-L1349`).
- **Unsynced GUARD groups form the side's pool.** Every 25–35 s, the side lists its targets: known enemies before unidentified contacts, and costlier targets first. Each target gets the nearest free guard group, one group per target. Only groups left over go to the guard points, in point order, nearest free group first (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L295-L509`).
- **A GUARD synced to a real trigger** guards that trigger instead: it attacks enemies and checks out unknown contacts among the objects the trigger currently lists (its `thisList`), using the side's knowledge (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L967-L1233`).
- "Guarded by" pins never take part in syncs, so a GUARD synced only to a pin counts as unsynced and joins the pool (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L967-L984`).
- A GUARD waypoint never finishes (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L1116-L1668`). Only a Switch trigger moves the group on.

## When to use it

- A town garrison with one or two mobile reserve squads that rush to wherever the enemy shows up.
- A strongpoint that reserves drift back to while things are quiet: a "Guarded by" pin.
- A reserve for one specific zone: GUARD synced to a trigger covering that zone.

## Gotchas

- Code, conditions and names on a "Guarded by" trigger are silently ignored.
- If the side knows of as many threats (enemies or unidentified contacts) as it has guard groups, no guard point is held at all.
- A GUARD synced to a trigger dismounts from its vehicles while idle (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L1231-L1232`).
- A GUARD synced to a trigger with Activation None never reacts: that trigger never lists anything.
- The guard point does not follow a moving unit; it is taken once at start.
- "Seized by" is a later-game option; this engine does not have it ([not-in-this-engine](not-in-this-engine.md)).

## Tiny example

```text
Trigger   Type: Guarded by East    (placed on the crossroads; size and code do not matter)
Squad A   WP1 GUARD                Squad B   WP1 GUARD     (both East, not synced)
Result    with no contacts, the nearest squad holds the crossroads; West contacts pull squads away
```

## Try it

1. Build the example and Preview: watch one squad settle at the crossroads.
2. Add a West patrol driving toward the town and watch a squad move to meet it.
3. Give Squad A a WP2 MOVE to a hill, add a Radio Alpha trigger of type Switch synced to its GUARD, and call it.

## Related

[waypoint-types](waypoint-types.md) · [trigger-end-types](trigger-end-types.md) · [synchronisation](synchronisation.md) · [detected-by](detected-by.md)

## Profiles

- **cwr / ce:** `AICenterImpl.cpp`, `AICenterStats.cpp` and `AIArcadeActions.inc` are byte-identical. **cwa199:** same lineage, not checked against the 1.99 build (unverified).

## Verification notes

### Consolidation pass (2026-09-27)

- 2026-09-27 (I33-SEED-C; doc 33 finding 11 and §7): added a `translator-note` front-matter key for the "fire brigade" idiom (and the duty-map pin), naming the rule they teach. No engine facts or citations changed.
