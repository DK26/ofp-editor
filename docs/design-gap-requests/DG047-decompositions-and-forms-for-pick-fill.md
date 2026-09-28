# DG047: Authored decompositions and question forms for Pick and Fill

> Design-gap request (`AGENTS.md`, "Design Authority"). Filed 2026-09-28 in the go-ahead pass (design-gap candidates of docs 51–63).
> Status: **open**.
> **Decision by: technical** (design round). Blocks: doc 55 §2.1's decomposition knob, doc 59's registered scaffolds and doc 60's
> gates and forms (P-03, P-04, P-05, P-10); they stay `proposal-only`.

## Context

- **Doc 38 §3.3.** `split` (authored smaller decisions) exists only for Compose and Draft. **§3.2; D025 decision 2**: a closed set
  of twelve step kinds.
- **D048 item 2.** A preset may set "how a decision is split between the model and code". **D051 items 2–3**: levels FR1–FR3
  (one-pass Pick, guided Pick, field Fill) and product ceilings per `DecisionKind`.
- **Doc 55 §2.1, §7 item 2, OQ8.** Extract-then-dispatch and the escape pre-check need "a registered slot per DecisionKind, with the
  decision table as code"; OQ8 asks whether dispatch should become doctrine for rule-bearing kinds.
- **Doc 59 §7 items 1 and 7, §5.3.** Registered reasoning scaffolds per `DecisionKind` (facet schemas, decision tables, annotation
  generators, card-sentence selectors), authored and tested as code, with scaffold-leakage tests as part of the kind's contract.
- **Doc 60 P-03, P-04, P-05, P-10; §4 items 3–5.** Typed question forms; the existence gate as a registered decomposition
  alternative with its own qualification; "stated?" gates for optional and judgement fields; an ordinal form. "Yes/no and ordinal
  [are] forms of the PICK shape … the closed step-kind list (doc 38 §3.2) should not grow, so the forms belong under
  `ModelShape::Pick`." Item 5 and OQ5: how a gate's "not stated" maps to `Q`, a visible default or `NotSupported`, and whether a
  menu ever needs a third escape.
- **DG015** (open) proposes one frozen letter schema for every Pick; **agent-runtime §6** has one `PickAnswer` form; **doc 56 DS1**
  names a "nothing stated" value; **doc 53 §4.4** asks for per-field Picks.

## The gap

Presets may split a decision (D048 item 2), and three docs propose concrete splits and forms, but the format has nowhere to register
them for Pick and Fill, DG015 knows only the letter form, and no rule says how a gate's "not stated" settles.

## Options

| # | Option | For | Against |
| --- | --- | --- | --- |
| A | One fixed form per `DecisionKind`; any split is an authored workflow edit | No new registry | Per-model choice impossible (D048 item 2); every split changes a definition |
| B | A registry of authored decomposition alternatives per `DecisionKind`, written and tested as code (decision tables, facet schemas, gates, selectors, with doc 59 §5.3's leakage tests); each alternative qualified on its own; a preset selects among the registered ones; yes/no and ordinal are forms of `ModelShape::Pick`, not new step kinds | Presets choose, code owns every split; the closed step-kind list stays | Each alternative needs its own qualification runs |
| C | New step kinds for gates and ordinal questions | Visible in the definition | The closed list should not grow (doc 60 §4 item 4; D025 decision 2) |

## Recommended resolution (proposal)

B (docs 55, 59 and 60 converge on it). The "not stated" mapping (doc 60 §4 item 5, OQ5; doc 56 DS1) is a sub-question for the
design round; doc 60 OQ5 doubts that it should ever be a menu letter. Whether dispatch becomes doctrine (doc 55 OQ8; doc 59 OQ2)
follows the measurements.

## What it would change

- Doc 38 §3.3 (`split` or a registered-alternative key for Pick and Fill); DG015 (letter, yes/no and ordinal forms under
  `ModelShape::Pick`); agent-runtime §6 (`PickAnswer`); doc 55 §2.1; the `DecisionKind` registry.
- Tests first (doc 60 P-03, P-04, P-05; doc 59 §5.3): adapters reject unknown or duplicate option ids; the existence gate never admits
  an option; an unstated field stays unset with an assumption chip; each scaffold's leakage test.

## Affected docs

Doc 38 (§3.2–§3.3); doc 55 (§2.1, §7, OQ8); doc 59 (§5.3, §7, OQ2); doc 60 (§2, §3, §4, OQ5, OQ7); doc 53 §4.4; doc 56 DS1;
`docs/architecture/agent-runtime.md` §6; D025; D048; D051; DG015.

## Decision record

Open.

## Verification notes

### Filing (2026-09-28)

- Filed from doc 55 §7 item 2, doc 59 §7 items 1 and 7, and doc 60 §4 items 3–5 (deduplicated), re-read on 2026-09-28 with doc 38
  §3.2–§3.3, DG015 and D048.
