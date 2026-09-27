# D029: Keep the Easy/Advanced switch and the original labels

> **Status:** accepted · **Decided by:** owner (DG033 items 3–4) · **Decided:** 2026-09-27 · **Recorded:** 2026-09-27
> **Scope:** the faithful dialogs, their disclosure levels and their labels. **Related:** D002, D004, D015, D028.
> **Open parts:** DG033 items 1–2 (entry schema ownership, demo fidelity; technical); OWQ-08 (names of any new UI terms;
> answered 2026-09-27 → D034).

## Context

- The original editor has an Easy/Advanced switch; "Easy only hides things", and CWR defaults to Advanced (doc 33 §1.2 row 19). Doc 31
  §4.1 uses short forms with "Advanced" folds; doc 33 §4.1 uses two disclosure levels (hover card, manual page).
- The original dialog labels are terse and sometimes misleading ("Countdown" vs "Timeout"), but two decades of community tutorials use
  them. Doc 33 proposed plain-language lines such as "Countdown: fires after the delay no matter what" (doc 33 OQ2).
- The README promises "the same dialogs" as the original editor.

## Decision

1. **Easy/Advanced stays** as a view preset over Plotroom's shared disclosure system (DG033 item 3, option (c)): Easy hides what the
   original hides, Advanced shows everything, and the **default is Advanced**, as in CWR.
2. **Original labels stay primary** on every control, resolved from the user's game locale. A **plain-language relabel sits beside
   them**: as the hover card's "what" line, and as a dim secondary line in dialogs where space allows (DG033 item 4, option (b)).

## Alternatives considered

| Option (DG033) | Why not chosen |
| --- | --- |
| Keep the original switch exactly, with no shared disclosure system | Two mechanisms for the same job (short forms and folds exist anyway) |
| Replace the switch with progressive disclosure only | Breaks fidelity with the original and with community tutorials |
| Replace the original labels with plain language | Community tutorials would no longer match the screen |
| A setting to switch label styles | More UI; the side-by-side form serves both audiences at once |

## Consequences

- Doc 33 lesson C7 teaches the Easy/Advanced preset rather than a replacement; doc 33 OQ2 is answered (folding step).
- Standing Orders entries store the original label (from game data at runtime) plus the plain name (doc 33 §3.1 `labels`); plain
  lines are our own words and are localised with the rest of Standing Orders.
- Where the switch's exact behaviour needs recording, docs 03 and 05 carry it (dialog fidelity).
- Proposal: tests check which fields each preset shows against the original's behaviour as recorded in doc 03.

## Sources

DG033 (items 3–4); doc 33 (§1.2 row 19, §3.1, §4.1, §5.4 lesson C7, OQ2); doc 31 §4.1; doc 03; doc 05; README.

## Amendment notes

### 2026-09-27: refined by D034 (pointer)

New UI terms are named by the design round in one names table, each cleared through doc 02 §9, and the owner reviews the table
before the first release (OWQ-08 (a); D034 item 3). The header gained the pointer; nothing above changed.
