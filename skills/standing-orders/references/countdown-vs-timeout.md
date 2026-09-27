---
id: countdown-vs-timeout
label: "Countdown vs Timeout (and min / mid / max)"
aliases: [countdown, timeout, "timeout min", "timeout mid", "timeout max", delay, interruptable, "trigger delay", "waypoint timeout"]
ui: "Trigger dialog > Countdown / Timeout toggle, Timeout min / mid / max; Waypoint dialog > Timeout min / mid / max"
translator-note: "'A lit fuse' and 'a held breath' are pictures, not terms. Rule they teach: Countdown fires when its delay ends even if the condition turned false meanwhile; Timeout fires only if the condition stays true for the whole delay, otherwise the clock resets. Replace either picture with a local image that teaches the same rule; translate the rule literally."
---

# Countdown vs Timeout (and min / mid / max)

## In one sentence

Countdown is a lit fuse: once it starts, it goes off even if you change your mind. Timeout is a held breath: the condition has to stay true for the whole wait, or the clock resets.

## What it really does

- When a trigger's condition becomes true: if **max is below 0.1 s** it fires at once; otherwise it picks one delay and starts the clock (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1267-L1278`).
- If the condition goes false before the clock runs out, an "interruptable" trigger (Timeout) cancels the clock; a non-interruptable one (Countdown) fires anyway when time is up (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1289-L1295`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L696-L705`).
- **The three boxes are one random delay, not three timers.** The engine averages four random numbers and maps the result so that half the draws land between min and mid and half between mid and max, bunched toward mid (`BohemiaInteractive/CWR@ffc61838b7:engine/Random/randomGen.cpp#L156-L171`). The result stays within min..max only if min ≤ mid ≤ max.
- The dialog toggle stores index 1 as interruptable; new triggers use index 0 (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIArcade.cpp#L1572-L1584`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.cpp#L446-L473`). That index 0 is labelled "Countdown" and index 1 "Timeout" comes from game data and community guides (unverified).
- Waypoints use the same min/mid/max draw, without the "max below 0.1 s" shortcut and without any Countdown/Timeout choice (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/AIArcade.cpp#L863-L883`).
- Radio triggers ignore both ([radio-triggers](radio-triggers.md)).

## When to use it

- Countdown: "reinforcements arrive 60–120 s after the alarm", whatever happens meanwhile.
- Timeout: "the zone counts as held only if we stay in it for 30 s".

## Gotchas

- Filling min and mid but leaving max at 0 means **no delay at all** on a trigger.
- Mixed-up order (for example min 30, mid 10) can give delays outside the range you meant.
- With Timeout, a flickering condition (a unit pacing along the edge of the area) keeps resetting the clock.
- The two words sound alike. Read them as "fires after the delay no matter what" and "must hold true for the delay".

## Tiny example

```text
Trigger A  West Present   Countdown   min 10  mid 15  max 20   -> fires ~15 s after entry, even if you leave
Trigger B  West Present   Timeout     min 10  mid 10  max 10   -> fires only after 10 s inside without leaving
```

## Try it

1. Build both triggers with a `hint` each and Preview.
2. Step into each area for 3 seconds, step out again, then wait 20 s: only A fires.
3. Set A's max to 0 and see it fire the instant you enter.

## Related

[once-vs-repeatedly](once-vs-repeatedly.md) · [trigger-activation](trigger-activation.md) · [waypoint-lifecycle](waypoint-lifecycle.md) · [radio-triggers](radio-triggers.md)

## Profiles

- **cwr:** as cited.
- **ce:** `ArcadeTemplate.cpp` differs (defaults at CE `#L449-L476`, +3); the other cited files are byte-identical.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified). Later games changed the default for new triggers; this engine defaults to index 0.

## Verification notes

### Consolidation pass (2026-09-27)

- 2026-09-27 (I33-SEED-A; doc 33 pedagogy finding 6): Try it step 2 now says "then wait 20 s". Trigger A is a Countdown of up to 20 s, so without the wait it looks broken. No engine facts or citations changed.
- 2026-09-27 (I33-SEED-C; doc 33 finding 11 and §7): added a `translator-note` front-matter key for the "lit fuse" and "held breath" idioms, naming the rule they teach.
