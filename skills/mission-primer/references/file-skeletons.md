# File skeletons

Use these to read and explain files. The editor writes all three through typed actions, so do not hand-write them. Citations are in `sources.md` (facts R1–R4).

## mission.sqm (format version 11)

```text
version=11;
class Mission
{
    addOns[]={...};
    addOnsAuto[]={...};
    randomSeed=...;
    class Intel {...};
    class Groups {...};
    class Vehicles {...};
    class Markers {...};
    class Sensors {...};
};
class Intro {...};
class OutroWin {...};
class OutroLoose {...};
```

- The top level holds `version` and the four sections, in this order. The editor needs all four.
- Inside a section, the editor writes these entries in this order:
  1. `addOns[]` and `addOnsAuto[]`;
  2. the `show*` flags (format 8 and later);
  3. `randomSeed`;
  4. `Intel` (format 7 and later);
  5. `Groups`, `Vehicles` (empty vehicles), `Markers` and `Sensors` (triggers).
- The editor opens text files only, not binarised ones.
- Later titles' entries (`class EditorData`, `class Entities`, `binarizationWanted`, version 53 or 54) do not exist here.

## briefing.html

```html
<html><body>
<p><a name="Main"></a>Notes for the player.</p>
<hr>
<p><a name="Plan"></a>The plan.</p>
<hr>
<p><a name="OBJ_1"></a>Destroy the radar.</p>
<hr>
<p><a name="Debriefing:End1"></a>The radar is down.</p>
<hr>
</body></html>
```

**How the parser builds sections.**

- Everything before `<html>` is ignored, so a file without the wrapper shows an empty briefing.
- `<body>` opens the first section, and each `<hr>` opens the next.
- `<a name="...">` names a section only inside `<p>`, `<h1>`–`<h6>`, `<address>` or `<td>`. Text directly under `<body>` is ignored.

**Section names** match case-insensitively:

- `Main` is the notes page.
- `Plan` is the plan page; every `OBJ_<id>` section is listed under it with a status icon.
- `Debriefing:End1` to `Debriefing:End6` and `Debriefing:Loser` hold the debriefing text for each ending.
- Pages for one side or one unit: `Main.West`, `Plan.East`, `Main.<unit variable>`. The side names are `West`, `East`, `Guerrila` and `Civilian`.
- Objectives for one side only: `OBJ_WEST_`, `OBJ_EAST_`, `OBJ_GUER_` and `OBJ_CIVIL_`.

**Objectives.** `"<id>" objStatus "<status>"` sets `OBJ_<id>`. The statuses are `ACTIVE`, `DONE`, `FAILED` and `HIDDEN`. Hidden objectives are not listed, and an unknown word counts as `ACTIVE`.

**File name.** Plain `briefing.html` is the portable name. CWR and CE first try `briefing.<Language>.utf8.html`, then `briefing.<Language>.html`, then `briefing.utf8.html`. The UTF-8 names are Remastered additions; whether 1.99 reads the per-language `briefing.<Language>.html` is unconfirmed.

## description.ext

- **Two files.** The mission's own `description.ext` sits in the mission folder and is read when the mission is set up. The campaign's `description.ext` is a separate file.
- **Debriefing.** `debriefing = 0;` in the mission file skips the debriefing. Statistics update and the outro plays; in Preview, control returns to the editor. If the key is absent or reads as non-zero, the debriefing is shown.
- **How the value is read.** The engine reads the value as a number. On CWR and CE a word that is not a number is evaluated as a script expression, so `false`, and any unknown word, reads as 0 and also skips the debriefing. This comes from reading the source and has not been probed; 1.99 is unknown. Write `0` or `1`.
- **Campaign routing.** Each mission class in the campaign file holds:
  - `template`, the mission folder;
  - `end1`–`end6` and `lost`, the next mission for each outcome.
- **Empty keys.** An empty key falls back to the same key on the chapter class. That key names the next chapter, whose `firstMission` is played. If it is empty too, the campaign ends.
