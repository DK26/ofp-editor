---
id: player-and-playable
label: Player vs Playable (the Control field)
aliases: [player, playable, "Control", "player as commander", "player as driver", "multiplayer slots", "MP roles", "disable AI"]
ui: "Unit dialog > Control"
---

# Player vs Playable (the Control field)

## In one sentence

"Player" is the one body you wear in single-player; "Playable" marks the seats humans can grab in multiplayer, and in single-player it does nothing.

## What it really does

- Control lists Non-playable, Player (as commander, driver or pilot, or gunner, depending on the vehicle's seats) and Playable seat combinations (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcade.cpp#L455-L803`). Only the four real sides can be playable; Logic and Empty are always non-playable (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcade.cpp#L176-L216`).
- There is exactly one Player: making a unit the Player clears the previous one (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplateFind.cpp#L491-L510`). A single-player mission with no Player fails the consistency check, so the Preview button is hidden (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.cpp#L1835-L1845`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapExtDisplay.cpp#L410-L421`).
- Probability and condition of presence are skipped for Player and Playable units: they always appear (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1525-L1538`).
- In single-player the Player unit takes the profile's name, face and voice (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1795-L1918`). The Player's death ends the mission as "killed", and the end check tests this before any END or Lose trigger (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/WorldImpl.cpp#L541-L585`).
- In multiplayer each playable seat becomes a lobby role. A soldier seat that no human took while AI is disabled is not created at all (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1003-L1007`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L1946-L1962`).
- Merging another mission in strips Player and Playable from the merged units (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplateFind.cpp#L1086-L1310`).

## When to use it

- Single-player: set exactly one unit to Player; leave everyone else Non-playable.
- Multiplayer: mark every seat a human may take as Playable, on any of the four real sides.

## Gotchas

- In single-player, Playable gives no team-switching; apart from skipping the presence checks, the flag does nothing there.
- A 0 % presence on a playable unit is ignored: presence never removes a player's seat.
- With AI disabled in the lobby, empty playable soldier seats simply do not exist, so scripts naming them see nothing.
- The Player's death always ends a single-player mission as "killed"; it cannot pick an ending. Route failures that should lead somewhere through a Lose trigger while the player lives (see [trigger-end-types](trigger-end-types.md)).
- Multiplayer-only behaviour such as respawn is set in `description.ext`, and a single-player Preview does not exercise it (community guidance; unverified here).

## Tiny example

```text
Leader      Control: Player (commander)      Probability 100 %
Rifleman 2  Control: Playable                Probability 0 %   -> still appears
Rifleman 3  Control: Non-playable            Probability 0 %   -> never appears
```

## Try it

1. Place a squad, make the leader Player and one rifleman Playable.
2. Give both riflemen 0 % Probability of presence and Preview: only the playable one is there.
3. Remove the Player flag and look for the Preview button: it is gone until a Player exists again.

## Related

[probability-of-presence](probability-of-presence.md) · [groups-and-leaders](groups-and-leaders.md) · [mission-sections](mission-sections.md) · [trigger-end-types](trigger-end-types.md)

## Profiles

- **cwr:** as cited. The "no player" refusal is compiled out of builds with cheats enabled (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.cpp#L1836`).
- **ce:** `ArcadeTemplate.cpp` differs; cited lines are +3 in CE. `UIMapExtDisplay.cpp` differs (CE `#L333-L344`). The other cited files are identical.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified).
