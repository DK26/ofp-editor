---
id: game-logic
label: Game Logic
aliases: [Logic, GameLogic, "invisible helper", module]
ui: "Unit dialog > Side: Game Logic (non-playable only)"
translator-note: "'Stagehand' is a picture, not a term: a theatre worker who does useful jobs unseen by the audience. Rule it teaches: a Game Logic is invisible, senses nothing and is never fought, yet it has a name, an init line and waypoints. The same goes for 'pin, notebook or switchboard' (named anchor, code holder, logic gate). Replace them with local images that teach the same rule; translate the rule literally."
---

# Game Logic

## In one sentence

A Game Logic is an invisible stagehand: it has a name, an init line and a to-do list, but no body, no eyes and no enemies, so it makes a perfect pin, notebook or switchboard.

## What it really does

- It is an invisible person-type object with its own AI brain, and its simulation step is empty: no physics, no animation (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Entities/Vehicles/InvisibleVeh.hpp#L20-L40`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Entities/Vehicles/InvisibleVeh.cpp#L31-L48`).
- It senses nothing: Logic-side units are never registered as sensors (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1596-L1600`).
- Nobody fights it: a side's friend and enemy checks both return false for side Logic, which lies outside the four real sides (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterStats.cpp#L1371-L1410`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Scene/Object.hpp#L19-L31`).
- A Logic group only runs its waypoint plan (no targeting, radio or fleeing), and only on the machine where the group is local (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIGroup.cpp#L1198-L1205`).
- Its waypoints can only be AND or OR, and it jumps to each one instead of walking (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcadeWaypoint.cpp#L74-L105`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L601-L605`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcadeActions.inc#L1774-L1781`).
- The editor offers side Logic only for Non-playable units and hides Rank (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcade.cpp#L176-L216`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcade.cpp#L899-L913`). The 100 m auto-join applies to logics too (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplateFind.cpp#L412-L471`).
- A trigger can use "Game Logic" as its activating side (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L731-L751`).
- That the stock "Logic" class is this invisible type on side Logic is game config, which is not in the source repo (unverified).

## When to use it

- **Named anchor:** a spot that scripts and conditions refer to by name (a landing zone, a camera target).
- **Code holder:** an init line that does not depend on a soldier who might be absent or killed.
- **Logic gate or timeline:** AND/OR waypoints that combine triggers and groups without scripts; see [logic-gates](logic-gates.md).

## Gotchas

- It has no hidden powers. Placing one does not "enable" anything; it only does what is listed above.
- Two logics placed within 100 m end up in one group with one shared waypoint list. Keep them apart or fix the links in Groups mode (F2).
- "Game Logic present" and "Anybody present" triggers count logics inside their area: the scan keeps every living, non-static object of the chosen side, and a placed logic is one (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L880-L922`; read from code, in-game probe pending).
- The multiplayer folk trick "name a logic `server`, test `local server`" is unverified. CWR and CE have `isServer` (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Game/Commands/GameStateExt.cpp#L909`).
- Later Bohemia editors grew "modules" from this idea. This game engine has no modules; this editor's own modules compile to ordinary triggers, waypoints, Game Logics and scripts ([not-in-this-engine](not-in-this-engine.md)).

## Tiny example

```text
Game Logic   Name: lz              (placed on the landing zone)
Trigger      Activation: None      Condition: player distance lz < 50
             On Activation: hint "You are at the LZ"
```

## Try it

1. Place a Game Logic on a clearing and name it `lz`.
2. Add the trigger above anywhere (with Activation None its area does not matter).
3. Preview and walk to the clearing.

## Related

[logic-gates](logic-gates.md) · [synchronisation](synchronisation.md) · [init-line](init-line.md) · [groups-and-leaders](groups-and-leaders.md) · [not-in-this-engine](not-in-this-engine.md)

## Profiles

- **cwr:** as cited.
- **ce:** cited lines match; `isServer` is at CE `GameStateExt.cpp#L907`. All other cited files are byte-identical or match at the cited lines.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified); `isServer` there is unverified.

## Verification notes

### Consolidation pass (2026-09-27)

- 2026-09-27 (I33-SEED-A; doc 33 §1.4 and pedagogy finding 9): the "modules" gotcha now gives both answers, because this entry lists `module` as an alias: the game engine has none, and this editor's own modules compile to ordinary triggers, waypoints, Game Logics and scripts. It points to [not-in-this-engine](not-in-this-engine.md), which carries the full answer. No engine facts or citations changed.
- 2026-09-27 (I33-SEED-C; doc 33 finding 11 and §7): added a `translator-note` front-matter key for the "stagehand" idiom, naming the rule it teaches.
