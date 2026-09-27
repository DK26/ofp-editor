# D028: Standing Orders and Drill

> **Status:** accepted · **Decided by:** owner (names chosen under the owner's delegation: "pick the best names, refactor later if
> needed") · **Decided:** 2026-09-27 · **Recorded:** 2026-09-27 · **Scope:** the concept manual and the live tutorials.
> **Related:** D002, D019, D027, D029. **Open parts:** DG031 (id scheme), DG032 (one store), DG033 items 1–2 (schema ownership, demo
> fidelity); OWQ-14 (v1 content and locales; answered 2026-09-27 → D036).

## Context

- Doc 33 designs a concept manual that explains every cryptic concept (Game Logic, synchronisation, Countdown vs Timeout, "Guarded
  by", Info age) in verified words shared by users and the AI, and live tutorials that teach by doing, with steps checked by validators.
- The working names were "Field Manual" and "boot camp"; doc 21 §11.4 called the tutorials "Academy". "Field Manual" and "Bootcamp" are
  Arma 3 feature names, and doc 02 §9 records Bohemia's rule to prefer original names (doc 33 §2 item 9).

## Decision

1. The concept manual is **Standing Orders**. The live tutorials are **Drill**. Doc 21's "Academy" and doc 33's tutorials are **one
   system**, Drill, with doc 21's ordered topics and validator-computed checks as its curriculum.
2. The skill folder is `skills/standing-orders/` and doc 33 is "Standing Orders and Drill"; mentions of Arma 3's own Field Manual stay
   only as prior art.
3. Any further new user-facing name clears the doc 02 §9 checklist before its UI string is written.

## Alternatives considered

- Keep "Field Manual" and "boot camp": both collide with Arma 3 features and invite confusion or a trademark complaint.
- Separate systems for the manual, the tutorials and Wilco's teaching mode: three sources of truth for the same facts.

## Consequences

- One registry of entries feeds every surface: hover cards, F1 pages, the manual, lint links, tutorial steps, Wilco's
  `explain_concept` replies and the skill's `references/` (doc 33 §3; proposal-only design).
- Every engine claim in an entry carries evidence; only verified facts are shown as rules (doc 33 TL;DR).
- The instructor voice never states a fact itself: code renders facts; no streaks, nagging or generic praise (doc 33 §5.3).
- The rename has been applied across the research docs and skills (see the verification notes of docs 21, 26, 33, 34, 35, 36, 37, 38
  and 40).

## Sources

Doc 33 (header, TL;DR, §2 item 9, §3, §5); doc 21 (§11.4, verification notes); doc 02 §9; `skills/standing-orders/SKILL.md`; README.

## Amendment notes

### 2026-09-27: refined by D036 (pointer)

The seed entries and Drill track A ship in English first; Czech, Polish, Russian and German follow as native reviewers join
(OWQ-14 (a); D036 item 4). The header gained the pointer; nothing above changed.
