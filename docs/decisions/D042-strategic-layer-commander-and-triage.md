# D042: Strategic layer: the commander is a campaign setting, and triage is disclosed

> **Status:** accepted, to be confirmed after the first balance-lab runs and playtests · **Decided by:** owner (OWQ-23)
> **Decided:** 2026-09-27 · **Recorded:** 2026-09-27 · **Scope:** the player's role in the strategic layer (doc 29) on `Cwa199` and
> `Cwr`, and what the debrief tells the player about triage. **Refines:** D005 item 3. **Related:** D003, D012, D036, D039.
> **Open parts:** the owner's confirmation of both items after the first balance-lab runs and playtests; the strength of the triage
> table (doc 36 OQ1).

## Context

- Doc 29 names real-time permadeath as the central risk. On the shipped engine, player death is `EMKilled` → Retry and single-player
  respawn is off, so the player cannot die for good; a routable player death needs CWR-CE engine request E9 (a CE-only capability).
- Code-owned triage turns some deaths into grave wounds. Hidden help may favour only the player (doc 36 cv07), and D039 item 8 requires
  hidden help to be disclosed.
- Doc 29 OQ5 (plot armour or an embodied roster soldier with Retry) and OQ6 (should the debrief disclose triage) were product
  questions.

## Decision

1. **Commander design is a campaign setting** (OWQ-23 commander c), **plot armour by default**: the player is the commander, outside
   the roster's permadeath, and player death is Retry. The other value makes the player an **embodied roster soldier**; on `Cwa199`
   and `Cwr` that soldier's death is still Retry.
2. **Triage is disclosed** (triage a): the debrief says when triage saved a soldier, for example "survived: gravely wounded".
3. Both are confirmed again by the owner after the first balance-lab runs and playtests.

## Alternatives considered

- Plot armour only (commander a) or embodied only (b): which reads as fairer is unknown until playtests; a setting lets creators choose
  and the balance lab and playtests compare.
- Hidden triage (triage b): hidden help, which D039 item 8 forbids.

## Consequences

- Operation Grey Heron keeps the default: the player is the commander and never dies for good (D005 item 3).
- A permanent death for an embodied player is possible only as an opt-in capability of a CE profile once E9 ships (D003; D012); no
  campaign requires it.
- Doc 29 §3.2's `CommanderPolicy` sketch, which allows `EmbodiedSoldier` only on a CE profile with E9, gains an embodied value whose
  death is Retry on every profile (folding step).
- Retry after the commander's death replays the operation and so restores fallen squadmates; campaign text claims no stronger stakes
  than that (doc 29 product review notes).
- Standing Orders gets an entry on triage, and the preset description the player reads mentions it (D039 item 8).

## Sources

Doc 29 (TL;DR, §1.4 "Player-character permadeath" row, §3.2, §7 E9, OQ5–OQ6, product review notes); doc 36 (cv07, cv43, OQ1);
`OWNER-QUESTIONS.md` OWQ-23; D005; D039.
