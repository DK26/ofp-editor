---
id: not-in-this-engine
label: "Not in this engine: later-game editor terms"
aliases: [modules, "seized by", "not detected by", dismiss, "dismissed", loiter, "get in nearest", "skip waypoint", BLUFOR, OPFOR, INDFOR, "role description", "unit description", thisTrigger, "server only", "trigger owner", tasks, diary, Eden, 3DEN, layers, compositions]
ui: "(none; this entry answers questions that use later-game vocabulary)"
---

# Not in this engine: later-game editor terms

## In one sentence

Many tutorials online were written for this editor's grandchildren, so when a term below comes up, the honest answer is "not in this engine", followed by the nearest thing that is.

## What it really does

- Waypoint types are exactly MOVE, DESTROY, GET IN, SEEK AND DESTROY, JOIN, JOIN AND LEAD, GET OUT, CYCLE, LOAD, UNLOAD, TRANSPORT UNLOAD, HOLD, SENTRY, GUARD, TALK, SCRIPTED and SUPPORT, plus AND and OR for Game Logics (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/Path/ArcadeWaypoint.hpp#L61-L86`).
- Trigger activations are None, the sides, Anybody, Radio Alpha–Juliet and the linked kinds; presence is Present, Not present or Detected by one of four sides (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/Path/ArcadeWaypoint.hpp#L206-L240`).
- Trigger types are None, Guarded by East/West/Resistance, Switch, End #1–#6 and Lose (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/Path/ArcadeWaypoint.hpp#L242-L257`).
- A placed unit has no description field (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.hpp#L19-L61`).

## When to use it

| You heard… | In this engine… |
| --- | --- |
| Modules | two answers: the game engine has none (by hand, use a [Game Logic](game-logic.md) plus triggers and scripts); this editor's own modules, from its module palette, compile to ordinary triggers, waypoints, markers, Game Logics and scripts (docs/research/31-no-code-ladder-modules-rules-and-scripting.md §4, proposal-only) |
| "Seized by" trigger | none; combine "West Present" and "East Not present" (two triggers as End #n, or a [logic AND gate](logic-gates.md)) |
| "Not detected by" | none; use a Repeatedly "Detected by" trigger and its On Deactivation ([detected-by](detected-by.md)) |
| Dismiss, Loiter, Get in nearest waypoints | none; use HOLD, CYCLE patrols, or GET IN attached to a vehicle ([waypoint-types](waypoint-types.md)) |
| "Skip waypoint" trigger | Switch ([trigger-end-types](trigger-end-types.md)) |
| BLUFOR / OPFOR / INDFOR | WEST / EAST / GUER (Resistance) ([sides-and-friendliness](sides-and-friendliness.md)) |
| Unit role description | no such field |
| `thisTrigger`, tasks, diary records | not in this engine; objectives live in `briefing.html` (see the mission-primer skill) |
| 3D placement, layers, compositions | not in the original editor |

## Gotchas

- Several popular "OFP" tutorials were written for later games; their rules for CYCLE, Switch and triggers differ in details (see [cycle-waypoint](cycle-waypoint.md)).
- Never invent a replacement feature. If nothing in this table fits, say that Standing Orders has no entry and look the question up with the editor's reference tools.

## Tiny example

```text
User:   "How do I add a Seized by BLUFOR trigger?"
Answer: This engine has no "Seized by". For "West holds the town", combine
        two triggers over the town, West Present AND East Not present: give
        both the same End number, or sync both to a logic AND gate.
```

## Try it

1. Open the Trigger dialog and read the Type list: count the entries against the table above.
2. Open the Waypoint dialog for a Game Logic and see that only AND and OR are offered.
3. Search the Activation list for "Seized by": it is not there.

## Related

[game-logic](game-logic.md) · [waypoint-types](waypoint-types.md) · [trigger-end-types](trigger-end-types.md) · [detected-by](detected-by.md) · [sides-and-friendliness](sides-and-friendliness.md)

## Profiles

- **cwr:** as cited.
- **ce:** `ArcadeWaypoint.hpp` is byte-identical; `ArcadeTemplate.hpp` differs only by added addon-message declarations, and `ArcadeUnitInfo` is unchanged at the same lines.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified).

## Verification notes

### Consolidation pass (2026-09-27)

- 2026-09-27 (RN-03, owner rename decision): Gotchas now say "Standing Orders has no entry" instead of "the Field Manual has no entry"; the concept manual is now called Standing Orders. No engine facts or citations changed. This file moves with its folder to `skills/standing-orders/references/` in a later step.
- 2026-09-27 (I33-SEED-A; doc 33 pedagogy finding 9): the "Seized by" tiny example said either West Present or East Not present, while the table says to combine both; a model copies the example, so it now combines them (same End number, or a logic AND gate), matching the table. The "Modules" row now gives doc 33 §1.4's two-part answer: the game engine has none, and this editor's modules compile to ordinary triggers, waypoints, markers, Game Logics and scripts (doc 31 §4, proposal-only). No engine facts or citations changed.
- 2026-09-27 (RN-03, move done; supersedes "in a later step" above): this file now sits at `skills/standing-orders/references/not-in-this-engine.md` after the folder's `git mv`. Content unchanged.
