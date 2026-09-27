# D005: North star: an XCOM-like real-time campaign ("Operation Grey Heron")

> **Status:** accepted (goal); design proposal-only · **Decided by:** owner (goal), research (acceptance scenario, doc 29)
> **Decided:** 2026-09-27 · **Recorded:** 2026-09-27 · **Related:** D004, D009, D012, D025.
> **Open parts:** OWQ-13 (v1 or first post-v1 milestone; answered 2026-09-27 → D036), OWQ-23 (commander design, triage transparency;
> answered 2026-09-27 → D042, to be confirmed again after the first balance-lab runs).

## Context

- The owner's success criterion: someone builds an XCOM-like campaign (characters, resources, choosing missions, consequences) that plays
  in real time, not turn by turn. It exercises everything distinctive about Plotroom: a persistent roster, resources, strategic mission
  choice, consequences, campaign-from-brief, compilation to vanilla engine content, and fun.
- Doc 29 finds it feasible on the shipped engine: named roster, permadeath, wounds, recruiting, pools, currencies, research, expiring
  offers, a doom clock and a walkable base all map onto vanilla commands plus doc 19's compiler. On 1.99 about 20 behaviours stay
  unverified until probes pass, with degraded fallbacks designed in.

## Decision

1. An XCOM-like campaign is the **flagship acceptance scenario** and the dogfood reference campaign of the campaign designer.
2. The scenario is doc 29 §8 **"Operation Grey Heron"**: 12 missions per playthrough (9 deployments + 3 camp visits), 8 named soldiers,
   3 currencies, 6 unlocks, an expiring ops board, a doom clock and 18 measurable pass criteria, checked in CI on synthetic fixtures, in
   engine runs on Remastered through Preview, and in a probe-gated 1.99 subset.
3. Its shape follows doc 29: one strategic turn is one deployment; no real-time geoscape; the player is the commander and never dies for
   good; a playable camp every 3–4 operations; seven kernels (turn structure, named soldiers you can lose, a looping reward economy,
   triage of competing offers, a visible doom clock, fatigue and wounds that force rotation, visible memory).
4. It must be buildable without any engine change (D012). CWR-CE extensions (doc 29 §7, E7–E14) add polish and are never required.

## Alternatives considered

- A generic "branching campaign works" criterion: too weak to force the roster, economy, strategic layer and balance tooling.
- A turn-based strategy screen between missions: impossible without an engine change; doc 29 records it as optional engine request E13.

## Consequences

- Doc 29's strategic-layer kit (13 typed modules plus optional Stress, Bonds and Nemesis; a fixed commit pipeline; the balance lab) and
  pattern P9 "Strategic layer" join doc 26's pattern list and doc 19's lint registry when those docs are next revised.
- "Make me an XCOM-like campaign" runs P9 through the campaign flow as about 30 structural decisions plus about 40 one-slot text fills,
  all Pick or Fill; a run with no model yields the same valid campaign with template text (doc 29 §6).
- Every number in doc 29 (costs, caps, thresholds) is a placeholder until the balance lab and playtests tune it.
- Player-facing rules for the scenario follow the engagement-ethics question (OWQ-20) and the doc 36 fairness rules once decided.
- Whether Grey Heron is part of v1 or the first milestone after it is OWQ-13.

## Sources

README ("north star"); doc 29 (TL;DR, §1, §3, §5–§8, open questions 5, 6, 9); doc 26 §9.4; doc 19 §6.8; doc 36 cv43.

## Amendment notes

### 2026-09-27: refined by D036, D039 and D042 (pointers)

Grey Heron is the first milestone after v1, v1.1 (OWQ-13 (a); D036 item 1). The engagement-ethics rule the Consequences name is
D039 (OWQ-20 (a)). Commander design is a campaign setting with plot armour by default, so item 3's "never dies for good" stays the
default and, on `Cwa199` and `Cwr`, holds for the embodied value as well; triage is disclosed in the debrief (OWQ-23; D042, to be
confirmed again after the first balance-lab runs and playtests). The header gained pointers; nothing above changed.
