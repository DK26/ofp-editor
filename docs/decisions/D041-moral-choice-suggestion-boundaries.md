# D041: Boundaries for generated moral choices

> **Status:** accepted · **Decided by:** owner (OWQ-22 a) · **Decided:** 2026-09-27 · **Recorded:** 2026-09-27
> **Scope:** the conscience and loyalty choices that Plotroom *suggests*: the archetype vocabulary, generator defaults, lens wording and
> Wilco's proposals. Never the user's own content. **Refines:** D011 (its open part OWQ-22). **Related:** D009, D010, D028, D039.
> **Open parts:** the list's full wording in Standing Orders (design round, in the project's own words); the doc 26 archetype
> vocabulary update (folding step).

## Context

- The original campaigns carry few, weighty choices of conscience with a real price (doc 28 §1.2–§1.3). Doc 28 FP48 proposes loyalty
  or conscience choice nodes with hinted consequences, an archetype vocabulary with no atrocity objective, and weight that comes from
  refusing or protecting.
- D011: the user's explicit creative intent always wins; the tool never refuses, silently corrects or nags. A content filter on user
  content would break that (OWQ-22 c).
- Doc 28 OQ8 asked for an owner decision, recorded in `docs/`, on which choices the vocabulary offers and how they are framed.

## Decision

1. A **short, documented boundary list** governs what Plotroom offers unprompted. It starts with:
   - dilemmas carry consequences and are never rewarded as atrocity;
   - civilians and prisoners are framed as dilemmas, not loot.
2. The list is **written in Standing Orders**, so anyone can read what the suggestions follow.
3. **The user's own content is never filtered.** When a user writes, or explicitly asks for, something outside the list, Plotroom
   builds it through the same commands as any other edit, without refusal, silent correction or nag (D011). The list shapes only what
   Plotroom suggests.

## Alternatives considered

- No boundaries (OWQ-22 b): generators could suggest atrocity as a rewarded objective by default, against the understated, humane
  register of the original campaigns (doc 28 §1, §5.2).
- A content filter on user content (OWQ-22 c): conflicts with D011 and with "the user stays the director" (D009).

## Consequences

- Doc 26 §2's archetype vocabulary has no atrocity objective; conscience choices appear as loyalty or conscience nodes with hinted
  consequences (doc 28 FP48).
- Checks against the list run on Plotroom's generators and in their tests; they never produce warnings on user content.
- Items join the list only through the design round and appear in Standing Orders the same day; the list stays short.
- Generated elements stay glass-box (D010): a suggested choice shows why it was offered, like any other generated element.

## Sources

Doc 28 (§1.2–§1.3, §5.2, §6.2 FP48, OQ8); doc 26 §2; D011; `OWNER-QUESTIONS.md` OWQ-22.
