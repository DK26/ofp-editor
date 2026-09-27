# DG003: One canonical vocabulary for attributes and presets

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass. Status: **open**.
> **Decision by: technical** (design round; the words are user-facing but generic, so no owner decision is needed unless one is
> contested). Blocks: attribute labels in doc 37 PT1–PT2, Standing Orders entries on attributes, Wilco menu labels.

## Context

- **Doc 31 §3** (rung 1): "An attribute is a typed field on an existing entity. A preset is a named bundle of attribute values
  (never code)." The Unit row lists "behaviour preset (posture, alertness, fleeing, hold fire); pose; character (cast entry);
  captive".
- **`skills/mission-primer/references/idioms.md`**, I11–I15 "No-code" column: "Behaviour preset attribute", "Loadout, Cargo
  contents", "Special 'In cargo'; start seat", "Health slider; Destroyed at start", "Timeline actors; Hostage", and in the I15 body
  "a hold-position behaviour preset".
- **Doc 37** §2 (WA16–WA25), §4.3, the §8 lift table and PT1: Stance, Start posture, Courage, Hold, Starts in, Starts destroyed, Cast member,
  Height, Seat.
- **Doc 37 §10**, design-gap candidate (g), asks for one canonical vocabulary, "with bundles always called presets, so users and
  Wilco see one word per idea".

## The gap

One idea has up to three names, and one word ("behaviour preset") is used both for a single attribute and for a bundle:

| Idea | Doc 31 §3 | idioms.md | Doc 37 |
| --- | --- | --- | --- |
| Group posture at start (`setBehaviour`, `setCombatMode`, `setSpeedMode`, `setFormation`) | behaviour preset (posture, alertness) | Behaviour preset attribute | Start posture |
| `allowFleeing` | behaviour preset (fleeing) | (inside Behaviour preset) | Courage |
| `setUnitPos` | (not named) | (inside Behaviour preset) | Stance |
| `stop` / hold fire | behaviour preset (hold fire) | hold-position behaviour preset | Hold |
| Start in a vehicle seat | (not named) | start seat; Special "In cargo" | Starts in |
| `setDammage` at start | (not named) | Health slider; Destroyed at start | Starts destroyed / damaged |
| `setIdentity` | character (cast entry) | — | Cast member |

A weak model picking from a menu, a Standing Orders entry and a lint message must all use the same word, or users and Wilco talk past
each other.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Doc 37's per-attribute names become canonical; "preset" only ever names a bundle | Doc 37 has the complete, engine-grounded list (lift table, lints PL01–PL14); one word per engine effect | Doc 31 and the primer need edits |
| B | Doc 31 §3's names become canonical | Doc 31 owns rung 1 | Its names are coarse: "behaviour preset" hides four separate attributes |
| C | Stock editor labels where one exists (Health, Special, Rank), doc 37 names for the rest | Keeps the original dialogs' words (doc 33 principle 9 and the faithful-editor goal) | Needs one mapping table anyway |

## Recommended resolution (proposal)

Option C, recorded as one table in doc 31 §3 (rung 1 owns the vocabulary) and linked from doc 37 and the primer:

- Where the stock dialog has a label, keep it (Health, Special, Rank, Probability of presence). A new attribute that sets the same
  engine value (for example destroyed at start) is named as a state of that label's idea ("Starts destroyed", shown beside Health).
- Otherwise use doc 37's names: **Stance**, **Start posture**, **Courage**, **Hold**, **Starts in** (vehicle, seat), **Starts
  destroyed**, **Height**, **Cast member**.
- **Preset** always means a named bundle of attribute values (doc 31 §3's definition). "Behaviour preset" names the bundle over
  Start posture, Courage, Stance and Hold (for example "sleepy sentry"), never a single attribute.
- Wilco menus, Standing Orders entries (doc 37 §10 asks for an entry on attributes themselves), lint messages and the lift table all
  read labels from this table; a docs lint flags the retired synonyms.

## What it would change

- Doc 31 §3: a vocabulary table; the Unit row names attributes individually and "behaviour preset" becomes a preset example.
- `skills/mission-primer/references/idioms.md` I11–I15 "No-code" column and I15 body: canonical names.
- Doc 37 §4.3, §8 and PT1–PT2: pointer to the doc 31 table; no renames expected.
- Standing Orders: the attribute entry doc 37 §10 requests uses the table.

## Affected docs

Doc 31 §3; doc 37 §2, §4.3, §8, §10, §11; `skills/mission-primer/references/idioms.md`; later Standing Orders entries.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 37 §10 (g), doc 31 §3 and idioms.md I11–I15 (table rows and the I14–I15 bodies), re-read on 2026-09-27. Doc 37
  names were taken from its WA16–WA25 rows and §8 lift table.
