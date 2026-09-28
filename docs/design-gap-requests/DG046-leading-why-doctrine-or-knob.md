# DG046: The leading `why`: doctrine for every Pick and Fill, or a per-model knob

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-28 in the go-ahead pass (design-gap candidates of docs 51–63).
> Status: **open**.
> **Decision by: technical** (measurement: doc 53 §5 rule R7). Blocks: the Pick and Fill answer schemas (DG015, DG048) and the
> default preset (doc 55 §6.4); doc 25 §4.3 and doc 38 §3.3 keep their current wording until decided.

## Context

- **Doc 25 §2.4, §4.3; doc 38 §3.3.** Doctrine: "Pick and Fill lead with a bounded `why`" before the answer.
- **Doc 53 §5, R7.** Decision rule: if letter-only is within 5 points of why-first on `pick-hard` accuracy in both conditions, the
  tiny tiers drop the `why`; if why-first wins by ≥ 10 points, keep it at ≥ 3B and retest at 1B. It names this as a candidate
  request against doc 25 §4.3 and doc 38.
- **Doc 55 §6.4, §7 item 8.** The default preset leaves the leading `why` off until R7 decides; models may differ.
- **Doc 59 §7 items 5–6, finding 3.** Doc 25's evidence rests on math and letter tasks at 8B and up, so the `why` should be a
  per-(model, `DecisionKind`) knob; in the glass box it is labelled as a model's note, never as the cause, and dispatched decisions
  show code's rule.
- **Doc 60 §4 item 11** adds a third option: a rationale composed from sub-answers where the decision is decomposed.
- **D048 item 2** lets a preset set the answer format; **D051 item 7** forbids storing reasoning text (the `why` is an answer
  field, not reasoning).

## The gap

Docs 25 and 38 make the `why` part of every Pick and Fill; the default preset turns it off; docs 53, 55, 59 and 60 treat it as a
measured choice per model and `DecisionKind`. The glass box shows the `why` (doc 38 §5.3) without saying what it is presented as.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Doctrine stays: every Pick and Fill leads with a bounded `why` | One answer shape; a note per decision | The evidence is from larger models and other tasks (doc 59 finding 3); costs output tokens on tiny tiers |
| B | A per-(model, `DecisionKind`) preset knob, with the default set by doc 53 R7 | Evidence decides per model; D048 item 2 already allows it | The answer schema varies by preset (DG048) |
| C | Where a decision is decomposed (DG047), code composes the shown rationale from the sub-answers and no `why` is asked | The shown reason is code's | Only for decomposed decisions |

## Recommended resolution (proposal)

B, with C as an arm where DG047's decompositions apply (docs 53, 55, 59, 60). Whichever wins, doc 59 §7 item 5 applies: a `why` is
shown labelled as the model's note, never as the cause, and a dispatched decision shows code's rule.

## What it would change

- Doc 25 §2.4 and §4.3; doc 38 §3.3's model row; doc 55 §2.1 (a knob) and §6.4; DG015's letter schema gains an optional leading
  field per preset (DG048); the inspector wording (doc 38 §5.3).
- Tests first (proposal): a preset with the knob off produces a schema without the field; the inspector labels a `why` as the model's
  note; R7's arms in `tools/local-qual`.

## Affected docs

Doc 25 (§2.4, §4.3); doc 38 (§3.3, §5.3); doc 53 (§5, R7); doc 55 (§2.1, §6.4, §7); doc 59 (§7, findings); doc 60 §4; D048;
DG015; DG047; DG048.

## Decision record

Open.

## Verification notes

### Filing (2026-09-28)

- Filed from doc 53 R7, doc 55 §7 item 8, doc 59 §7 items 5–6 and doc 60 §4 item 11 (one candidate in four docs), re-read on
  2026-09-28 with doc 25 §4.3 and doc 38 §3.3. No measurement was run.
