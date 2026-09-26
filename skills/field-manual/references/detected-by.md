---
id: detected-by
label: "Detected by West / East / Resistance / Civilians"
aliases: ["detected by", "detected by east", "detected by west", spotted, alarm, "not detected by", "side exists", "center", "centre"]
ui: "Trigger dialog > Presence: Detected by …"
---

# Detected by West / East / Resistance / Civilians

## In one sentence

"Detected by" fires on gossip, not on truth: it asks the watching side's shared intelligence whether it has fresh news of the activating side inside the area.

## What it really does

- The trigger looks through the **detecting side's** list of known targets. A target counts if the side the watchers believe it has matches the Activation side (dead targets count as Civilian; a contact not yet identified matches only Anybody), is not static, its position accuracy is at least 0.1, it was last seen within 100 seconds, and the spot where it was last seen is inside the area (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L923-L956`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L753-L774`).
- That "last seen" spot and time come from a sighting's aiming point; a newer sighting replaces them only if it is at least as precise as the stored one (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterImplPreview.cpp#L794-L801`).
- **The detecting side must exist.** In single-player and intros, a side's "brain" (its AI centre) is created only if the mission file has at least one group of that side. The check reads the file, before any presence roll. In multiplayer every side's centre always exists (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AICenterStats.cpp#L1328-L1349`). Without it the trigger stops before even evaluating its Condition, so it can never fire (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L923-L929`).
- There is no "not detected by" option (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/Path/ArcadeWaypoint.hpp#L232-L240`).

## When to use it

- Alarms: Activation West, Detected by East, over the base, with On Activation `alarm = true`.
- Stealth failures: the player's side detected by the enemy inside a no-go zone.

## Gotchas

- **"My Detected by East trigger never fires"** in a mission where East only arrives by script: East has no brain. Place one East unit, even at 0 % presence, to make the side exist ([probability-of-presence](probability-of-presence.md)).
- It works on beliefs: a unit last seen inside the area keeps counting for up to 100 seconds after the last sighting, even after it has left unseen.
- Fires late compared with "Present": someone has to spot the unit first.
- Dead bodies and wrecks count as Civilian, so a "Civilian, Detected by …" trigger can count them.
- An enemy set to Info age "Actual" counts for the player's side from the first second, for up to 100 seconds; every other age is too old to count (read from code, in-game probe pending; see [info-age](info-age.md)).

## Tiny example

```text
Trigger  Axis 200/200 over the East camp   Activation: West   Detected by East   Once
         On Activation: alarm = true
East     one squad in the camp (so East exists)
```

## Try it

1. Build the example; Preview and sneak close: note when it fires compared with when you enter.
2. Change it to Present and compare the timing.
3. Make it Detected by again, Repeatedly, with On Deactivation `hint "contact lost"`; get spotted, hide, and time how long the trigger stays on.

## Related

[trigger-activation](trigger-activation.md) · [sides-and-friendliness](sides-and-friendliness.md) · [info-age](info-age.md) · [probability-of-presence](probability-of-presence.md) · [bound-triggers](bound-triggers.md)

## Profiles

- **cwr:** as cited. `createCenter` (make a side's brain by script) exists in CWR and CE (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/Game/Commands/GameStateExt.cpp#L1180`; CE `#L1178`).
- **ce:** all other cited files are byte-identical.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified); `createCenter` there is unverified.
