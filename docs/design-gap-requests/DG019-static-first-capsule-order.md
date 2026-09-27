# DG019: Capsule order: static first, or exemplars next to the question

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-27 in the consolidation pass (doc 40 gap G1).
> Status: **open**. **Decision by: technical** (measurement first). Blocks: the capsule builder's layout; doc 40 R2–R3 stay `proposal-only`.

## Context

- **Doc 25 §4.4**: "Order: task line → story digest → constraints → menu or slot spec → exemplars → answer schema"; **§4.6**:
  exemplar retrieval picks 1–3 by metadata match (beat, side, era, tone) per decision.
- **`prompts/design-sensibility/README.md`**, usage rule 2: task line, digest, **core then one lens**, menu, "1 to 3 rotated
  exemplars", schema; the core and lens may go in the system message instead.
- **Doc 21 §8.1** and **doc 38 §3.3**: system text and tool schemas → verbatim request → digest → menu or slot spec → exemplars →
  schema restated; doc 38 puts core, lens and knowledge in the system text.
- **Doc 40 §4.1, R2–R3, G1**: static first: tools; system text frozen per (stage × DecisionKind × pack version × model setup) with
  doctrine, core and lens, primer and cards, **frozen exemplars in a fixed order**, shape rules and schema text; breakpoint BP1;
  the request; digest; then per-sample menu permutation and variant note. "Rotating exemplars after the digest adds 6% to C on the
  campaign [I]." Proposal: "Measure first whether weak models need exemplars next to the question."

## The gap

Three orders are in force, and they disagree on where exemplars sit and whether they are fixed or retrieved per decision.
Per-decision retrieval (doc 25 §4.6) makes the prefix change every call, which defeats prompt caching on cloud providers and prefix
reuse in llama.cpp.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | Doc 25 order with retrieved exemplars after the menu | Doc 25 §2.7: similar, retrieved examples help strongly and their order moves results (Liu et al.; Lu et al.) | Every capsule differs early; no cache or prefix reuse |
| B | Doc 21/38 order: static system text, exemplars after the menu | Core and lens are cacheable | Exemplars below the breakpoint are re-sent uncached every call |
| C | Doc 40 static-first order: frozen exemplars in the system text above BP1; variety from menu permutations and variant notes below the breakpoints | Largest saving; one layout for cloud and local (llama.cpp reuses prefixes too) | Loses per-decision similarity retrieval, which doc 25 §2.7 cites as a strong effect; exemplars sit far from the question |

## Recommended resolution (proposal)

Option C as the default runtime-owned layout (authors never choose layout, doc 38 §3.3), gated by one measurement: an A/B run in the
doc 25 E-series (E4 and doc 40's E12) comparing frozen exemplars in the system text, frozen exemplars after the menu, and
retrieved exemplars after the menu, on T1 local models and one cloud model, per DecisionKind, reporting admit rate and pass^k. If T1 models lose accuracy beyond a threshold set
before the run, the layout becomes a per-tier parameter of the qualified setup (DG012 treats a layout change as major). Retrieved
exemplars are replaced by a frozen set per (DecisionKind, pack version); metadata matching chooses among a few frozen sets at the
stage level, not per decision.

## What it would change

- Doc 25 §4.4 order line and §4.6 retrieval rule.
- `prompts/design-sensibility/README.md` rule 2: the order list and "rotated" → "frozen per pack version".
- Doc 21 §8.1 and doc 38 §3.3: exemplars move above the request.
- Doc 40 R2–R3: from `proposal-only` to rules.

## Affected docs

Docs 21, 25, 38, 40; `prompts/design-sensibility/README.md`.

## Decision record

Open.

## Verification notes

### Consolidation pass (2026-09-27)

- Created from doc 40 §4.1, R2–R3 and §4.3 G1; doc 25 §4.4 and §4.6; doc 21 §8.1; doc 38 §3.3; the prompt pack README usage rule 2,
  re-read on 2026-09-27.
