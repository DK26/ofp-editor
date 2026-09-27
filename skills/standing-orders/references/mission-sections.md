---
id: mission-sections
label: "Mission sections: Mission, Intro, Outro (win), Outro (lose)"
aliases: [intro, outro, "outro win", "outro lose", OutroWin, OutroLoose, cutscene, section, "section switcher", initintro.sqs, "Easy mode", "Advanced mode"]
ui: "Section selector (Advanced mode only): Mission / Intro / Outro - win / Outro - lose"
---

# Mission sections: Mission, Intro, Outro (win), Outro (lose)

## In one sentence

One mission file is really four little missions in a row: the Intro cutscene before, the Mission you play, and one of two ending cutscenes afterwards, picked by how things went.

## What it really does

- The file keeps four sections, `Mission`, `Intro`, `OutroWin` and `OutroLoose`, each with its own Intel, groups, empty objects, triggers and markers (see the mission-primer skill).
- **Intro** runs in cutscene mode: if the section has a Player unit, the camera follows it from outside, and the campaign variables are loaded after the units are built. Then `initintro.sqs` runs if it exists (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/DisplayUIMenus.cpp#L1268-L1329`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImpl.cpp#L2194-L2202`).
- The player's death ends only the playable Mission; in the Intro it does not (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/WorldImpl.cpp#L541-L557`).
- **Outro (win)** plays after End #1–#6. **Outro (lose)** plays after Lose and after the player's death; the code also sends an unfinished ending there, probably an abort (unverified) (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/DisplayUIMenus.cpp#L1331-L1357`).
- A section with no groups is skipped (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/DisplayUIMenus.cpp#L1275-L1280`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/DisplayUIMenus.cpp#L1359-L1364`).
- End triggers end cutscenes too (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/WorldImpl.cpp#L553-L556`).
- In the original editor the section selector appears only in Advanced mode. Switching to Easy mode returns you to the Mission section; CWR and CE start in Advanced mode (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapExtDisplay.cpp#L429-L501`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapExtDisplay.cpp#L63-L97`).

## When to use it

- Intro: a short establishing shot (a convoy on the road, a briefing at the HQ tent).
- Outro (win): a victory scene, such as a helicopter flying off at dawn.
- Outro (lose): a sombre ending that the campaign can follow up on.

## Gotchas

- Each section has its **own** units and Intel: the Intro's weather and time are set separately.
- Put at least one group in a cutscene section, or it is skipped silently.
- The end check runs in cutscene mode too, so a timed End trigger (Activation None, Condition `true`, a Countdown) is how a cutscene finishes by itself.
- Previewing Intro and Outros through an external launch path may not be possible; see docs/research/03-original-editor-code-map.md §4.12.

## Tiny example

```text
Intro     one jeep driving to the base; trigger: None, Condition true, Countdown 15 s, Type End #1
Mission   the actual fight
Outro win the squad standing by the flag; the same kind of timed End trigger
```

## Try it

1. Switch to the Intro section and place one group with a MOVE waypoint.
2. Add a timed End #1 trigger as in the example.
3. To watch the Intro play before the mission, save it and start it from the game's own mission menu. This editor has no path for that yet (docs/research/03-original-editor-code-map.md §4.12), so Drill does not check this step.

## Related

[trigger-end-types](trigger-end-types.md) · [player-and-playable](player-and-playable.md) · [sides-and-friendliness](sides-and-friendliness.md) · [condition-of-presence](condition-of-presence.md)

## Profiles

- **cwr:** as cited.
- **ce:** `UIMapExtDisplay.cpp` differs (Advanced-mode switch at CE `#L352-L424`, default and saved setting at CE `#L74-L108`); the other cited files are byte-identical.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified). Whether retail 1.99 starts in Easy mode is unverified.

## Verification notes

### Consolidation pass (2026-09-27)

- 2026-09-27 (I33-SEED-A; doc 33 pedagogy finding 6): Try it step 3 ("play the mission from the menu") has no path in this editor yet (doc 03 §4.12: the original editor's Preview runs only the selected section, and the external launch path never plays the outros). The step now sends the user to the game's own menu and is kept out of Drill checks. No engine facts or citations changed.
