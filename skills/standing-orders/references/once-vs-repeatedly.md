---
id: once-vs-repeatedly
label: "Once vs Repeatedly (and On Deactivation)"
aliases: [once, repeatedly, repeating, "repeat", "on deactivation", "fires only once", "trigger won't fire again"]
ui: "Trigger dialog > Repeat: Once / Repeatedly; On Deactivation"
---

# Once vs Repeatedly (and On Deactivation)

## In one sentence

A Once trigger is a light switch that sticks in the "on" position forever; a Repeatedly trigger springs back to "off" when its condition goes false, and only then can it be flipped on again.

## What it really does

- **Once:** after it fires, the trigger stays active for the rest of the mission. It never switches off, so its On Deactivation never runs (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1280-L1296`).
- **Repeatedly:** when its condition becomes false while it is active, it switches off: On Deactivation runs (the trigger sets neither `this` nor `thisList` for it, so they hold leftover values), its looping trigger sound stops, and its synced waypoints are blocked again, except for a Switch trigger (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1512-L1529`).
- It fires again only after it has switched off and its condition becomes true again. It does not fire over and over while the condition stays true (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1267-L1278`).
- Each new firing starts a new countdown or timeout ([countdown-vs-timeout](countdown-vs-timeout.md)).
- New triggers default to Once (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/AI/ArcadeTemplate.cpp#L446-L473`).
- Radio triggers: Once disappears from the menu after use; Repeatedly can be called again ([radio-triggers](radio-triggers.md)).

## When to use it

- Once: story beats that happen one time (objective done, alarm raised, reinforcements sent).
- Repeatedly: states that come and go (a zone is occupied, a hint when entering or leaving an area).

## Gotchas

- "My On Deactivation never runs": the trigger is set to Once.
- "My Repeatedly trigger fires only once": its condition never went false in between.
- A Repeatedly trigger synced to a waypoint blocks that waypoint again when it switches off, which can stall a group that has not arrived yet.
- An END trigger set to Repeatedly can switch off again, which matters when several END triggers must all be on at once ([trigger-end-types](trigger-end-types.md)).

## Tiny example

```text
Trigger  Activation: West   Present   Repeatedly   (over the market square)
         On Activation:   hint "You are in the market"
         On Deactivation: hint "You left the market"
```

## Try it

1. Build the example and Preview; walk in and out twice.
2. Switch it to Once and repeat: one hint, then silence.
3. Add a Radio Alpha repeating trigger with a hint and call it several times.

## Related

[countdown-vs-timeout](countdown-vs-timeout.md) · [trigger-activation](trigger-activation.md) · [synchronisation](synchronisation.md) · [radio-triggers](radio-triggers.md) · [this-and-thislist](this-and-thislist.md)

## Profiles

- **cwr:** as cited.
- **ce:** `ArcadeTemplate.cpp` differs (defaults at CE `#L449-L476`, +3); `Detector.cpp` is byte-identical.
- **cwa199:** same lineage, not checked against the 1.99 build (unverified).
