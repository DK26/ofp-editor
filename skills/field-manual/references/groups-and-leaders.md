---
id: groups-and-leaders
label: Groups, leaders and the 100 m auto-join
aliases: [group, squad, leader, "join group", "group link", rank, "Groups mode", F2, "12 units"]
ui: "Placing units; Groups mode (F2) drag links; Unit dialog > Rank"
---

# Groups, leaders and the 100 m auto-join

## In one sentence

Soldiers travel in groups that follow their highest-ranking member, and anything you drop within 100 m of a same-side leader quietly signs up for that group.

## What it really does

- A **new** unit (not Empty) joins the same-side group whose leader is nearest, if that leader is within 100 m horizontally; otherwise it starts a new group. Editing an existing unit never moves it to another group (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplateFind.cpp#L412-L471`). A squad placed through the Group dialog always becomes a new group of its own, wherever it lands (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplateFind.cpp#L841-L874`).
- After every edit the editor makes the highest-ranked unit the leader; on a tie the earlier unit in the list wins, and the group takes the leader's side (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.cpp#L1542-L1561`).
- At mission start the unit marked leader in the editor leads. If it is missing (probability of presence), the group picks a new leader by rank, then experience (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L2058-L2070`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImplPreview.cpp#L190-L198`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIGroup.cpp#L1015-L1047`).
- A crewed vehicle brings its crew as separate group members: driver at the placed rank, commander one or two ranks higher, gunner one lower or one higher, depending on the vehicle (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1628-L1722`).
- A group may hold at most 12 members (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/Path/AITypes.hpp#L31`). The editor's consistency check counts every crew seat and also caps the number of groups per side from the game config; the Preview button is hidden while it fails (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.cpp#L1754-L1860`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Core/Config/Configuration.cpp#L339-L348`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapExtDisplay.cpp#L410-L421`).
- Waypoints belong to the group. A hidden waypoint 0 is created at the leader's start position (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L2072-L2078`).

## When to use it

- One group for everything that should move, fight and take orders together.
- Separate groups for independent jobs: a sniper pair, a patrol, a transport truck.
- The Group dialog places ready-made squads from the game's group presets.

## Gotchas

- Units placed one at a time near a squad's leader pile into that squad. Past 12 crew seats the group fails the consistency check and the Preview button disappears. Squads placed with the Group dialog never merge this way.
- A lone sniper placed near a squad joins it and follows its waypoints.
- A tank placed as Private still gets a higher-ranked commander, who may take over the group if the editor's leader is missing at start or later dies.
- Changing a unit's rank can change the leader, and the leader's start spot is waypoint 0, which [CYCLE](cycle-waypoint.md) can loop back to.

## Tiny example

```text
Sergeant at A;  Private 50 m from A   -> one group, led by the Sergeant
Private 150 m from A                  -> a new group of one
```

## Try it

1. Place a Sergeant, then a Private 50 m away. Check in Groups mode (F2) that they share a group.
2. Place another Private 150 m away: a separate group.
3. In Groups mode, drag from the far Private to the Sergeant to join them.

## Related

[player-and-playable](player-and-playable.md) · [special-placement](special-placement.md) · [waypoint-lifecycle](waypoint-lifecycle.md) · [empty-vehicles](empty-vehicles.md)

## Profiles

- **cwr:** as cited.
- **ce:** `ArcadeTemplate.cpp` differs; cited lines are +3 in CE (`SelectLeader` at CE `#L1545`, the consistency check at CE `#L1757`). `UIMapExtDisplay.cpp` differs (the Preview button check is at CE `#L333-L344`). The other cited files are identical.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified).
