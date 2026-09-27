# D039: Engagement ethics: fair play by design, and challenges without dailies

> **Status:** accepted · **Decided by:** owner (OWQ-20 a) · **Decided:** 2026-09-27 · **Recorded:** 2026-09-27
> **Scope:** everything Plotroom's modules, presets, generators, Wilco and Standing Orders produce for players; the challenge catalogue.
> A creator's own hand-written scripts are outside it, apart from informative lints. **Related:** D005, D009, D011, D028, D040, D042.
> **Open parts:** the strength of bad-luck protection (doc 36 OQ1; balance lab and playtests).

## Context

- Doc 36 cv43 gathered ten engagement rules from the Civilization V lessons and the review of doc 29's strategic layer; doc 33 already
  bans streaks and nagging in Drill (D028).
- Doc 43 §3.7 found that daily or weekly challenges conflict with cv43 item 2, and that server-bound challenge modes die with their
  servers. It proposed a numbered, never-expiring challenge catalogue instead.

## Decision

1. **Doc 36 cv43 is a product rule** for Plotroom's own output:
   1. clocks count deployments, never real time; nothing decays while the game is closed;
   2. no streaks, dailies, login rewards or appointment mechanics;
   3. no grind: payouts decay when an archetype repeats;
   4. no reroll or gacha loops for recruits or loot; candidates are shown before commitment;
   5. harsh modules are opt-in presets;
   6. no illusory ("endowed") progress used to lure play;
   7. every operation ends at a natural stopping point, with no "come back" nag;
   8. hidden help is disclosed in Standing Orders, the creator inspector and the preset description the player reads;
   9. no variable-ratio reward schedules: rolls vary situations, named rewards are deterministic, random bonuses are capped and tied to
      an action, and bad-luck protection only softens losses;
   10. staggered tracks stop at camps, act breaks and the finale, where threads may close together.
2. **Creators keep their freedom.** A creator's own hand-written scripts get informative lints only: never a block, a refusal or a nag
   (D011).
3. **The challenge catalogue is allowed** as T0 pack data: numbered, never-expiring entries with a baked play seed, playable at any
   time, with **no calendar, week index, streak, reward or reminder**. Communities may publish their own catalogues.

## Alternatives considered

- The catalogue with a "week" index (OWQ-20 b): an appointment mechanic in disguise.
- No challenges (OWQ-20 c): loses shareable, comparable runs that need no server.
- cv43 as guidance only: the loops it bans are exactly what a generator could produce at scale without anyone choosing them.

## Consequences

- Generator presets, Wilco's campaign suggestions and Standing Orders entries on Plotroom's own campaign rules (bad-luck protection,
  triage, a decided-state finale) follow the list; D042's triage disclosure applies item 8.
- Challenge entries pass the balance gates with tighter bands (doc 43 §4.5) and use the Fixed play seed (D040); Ironman stays
  honour-only (doc 29 E8).
- Engagement lints on a creator's own content have info severity.
- Doc 43 RV4's condition "after the owner decision" for the catalogue is met; doc 43 OQ1 is answered.

## Sources

Doc 36 (cv07, cv43, review notes, OQ1); doc 43 (§3.7, §4.5, RV4, OQ1); doc 33 §5.3; doc 29 (rules 4 and 11, E8, SL28, SL30);
`OWNER-QUESTIONS.md` OWQ-20.
