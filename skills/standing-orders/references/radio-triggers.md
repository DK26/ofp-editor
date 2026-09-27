---
id: radio-triggers
label: "Radio triggers: Alpha to Juliet"
aliases: [radio, "radio alpha", "radio bravo", "0-0-1", "radio menu", "radio trigger", "call support", "radio null"]
ui: "Trigger dialog > Activation: Radio Alpha … Radio Juliet; Text"
---

# Radio triggers: Alpha to Juliet

## In one sentence

A radio trigger is a button you give the player: it adds an entry to his radio menu, and pressing it fires the trigger on the spot, with no area and no waiting.

## What it really does

- Radio triggers never scan their area (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L869-L879`).
- The menu entry shows the trigger's Text (localised), or the default channel name when the Text is empty. A Text of `null` (in any letter case) hides the entry **and** stops it from being called (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapDisplayBriefing.cpp#L509-L590`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapDisplayBriefing.cpp#L737-L767`).
- Calling a channel fires **every** callable trigger on that channel: each one evaluates its Condition once with `this` = true, then activates immediately. Countdown and timeout are skipped (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1299-L1312`).
- A Once radio trigger disappears from the menu after use; a Repeatedly one stays and can be called again. A radio trigger never switches off, so On Deactivation never runs (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapDisplayBriefing.cpp#L524-L527`, `BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/World/Detection/Detector.cpp#L1280-L1296`).
- `thisList` is empty for radio triggers.
- The menu works only while the real player is alive. In multiplayer, the activation is sent to the other machines (`BohemiaInteractive/CWR@ffc61838b7:engine/Poseidon/UI/Map/UIMapDisplayBriefing.cpp#L737-L767`).

## When to use it

- Player-called support: "Alpha: request artillery", "Bravo: call the extraction helicopter".
- Debug switches while testing a mission (remove them before release).
- Starting a scripted sequence when the player is ready.

## Gotchas

- Timeouts do nothing on radio triggers. For a delay, sync the radio trigger to a Game Logic gate with a timeout, or wait in a script.
- Two triggers on one channel both fire; the menu shows the label of the one created first that is still callable.
- A Condition such as `alive heli1` makes the call do nothing when false, but the entry stays in the menu.
- `null` is a switch, not a label: it hides the entry and blocks the call. Any other Text replaces the default channel name.

## Tiny example

```text
Trigger  Activation: Radio Alpha   Repeatedly   Text: "Request flare"
         On Activation: hint "Flare on the way"
```

## Try it

1. Place the trigger above and Preview; open the radio menu and call Alpha twice.
2. Switch it to Once and call it: the entry vanishes.
3. Give it a Countdown of 10 s and notice that nothing changes.

## Related

[once-vs-repeatedly](once-vs-repeatedly.md) · [countdown-vs-timeout](countdown-vs-timeout.md) · [logic-gates](logic-gates.md) · [synchronisation](synchronisation.md)

## Profiles

- **cwr / ce:** both cited files are byte-identical. **cwa199:** same lineage, not checked against the 1.99 build (unverified).
